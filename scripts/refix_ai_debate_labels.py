"""Re-clean ai_debate role-title + letter-reference leak (STATUS.md deviation, 2026-07).

Companion to refix_human_debate_labels.py. Where human_debate leaked animal pseudonyms,
ai_debate leaks the four prompt-assigned ROLE TITLES and A/B/C/D speaker references. Both are
condition leaks specific to the dialogue cells (role titles: 600+ in cell3, ZERO in every other
cell incl. the cell5 target).

Two removable leaks, one trap:
  * ROLE TITLES (safe, case-insensitive phrase removal): "Creative Problem Solver",
    "Critical Analyst", "Mathematical Validator", "Alternative Seeker", plus the abbreviated
    role refs "the Analyst/Validator/Seeker/Solver" and "problem solver".
  * CAPITAL-LETTER SPEAKER REFS (SURGICAL, case-SENSITIVE, high-confidence patterns only):
    possessive  A's / B's / C's / D's
    vocative    "..., D!"  "..., A."  and line-initial "C, ..."
    explicit    "B said/suggested/proposed/notes/argues/thinks/mentioned/claimed"
    address     "well done/thanks/agree with/kudos to/building on/good point, X"
  * TRAP (never touched): bare or lowercase a-d - the article "a", sentence-initial "A ...",
    and any math/content letter. None of the patterns above match a bare standalone letter, so
    the article "A"/"a" is structurally safe.

NON-DESTRUCTIVE by default: writes a preview file + prints a full audit (every unique removal
context, residual check). Pass --commit to overwrite processed_ai_debate.jsonl.

Operates on the `full_text_no_labels` field (what the methods consume). Only ai_debate is
touched; see STATUS.md.

Usage (from repo root):
    python scripts/refix_ai_debate_labels.py            # audit only, writes preview
    python scripts/refix_ai_debate_labels.py --commit   # overwrite processed_ai_debate.jsonl
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data/ai_debate/processed_ai_debate.jsonl"
TEMP = ROOT / "data/ai_debate/processed_ai_debate.REFIX_PREVIEW.jsonl"
FIELD = "full_text_no_labels"

ROLE_TITLES = ["Creative Problem Solver", "Critical Analyst",
               "Mathematical Validator", "Alternative Seeker"]

# --- role-title removal (case-insensitive; also strips a leading article/"as a" wrapper) ---
_role_alt = "|".join(re.escape(r) for r in ROLE_TITLES)
ROLE_RE = re.compile(rf"(?i)\b(?:as\s+)?(?:a|the|our)?\s*(?:{_role_alt})(?:'?s)?\b")
ROLE_ABBR_RE = re.compile(r"(?i)\bthe\s+(Analyst|Validator|Seeker|Solver)\b|\bproblem solver\b")

# --- surgical capital-letter speaker refs (case-SENSITIVE) ---
POSSESSIVE_RE = re.compile(r"\b([A-D])'s\b")                         # A's approach
VOCATIVE_MID_RE = re.compile(r",\s*([A-D])(?=[!.?,])")               # ..., D!
VOCATIVE_INIT_RE = re.compile(r"(?m)^([A-D]),\s+")                   # D, let's ...
EXPLICIT_RE = re.compile(
    r"\b([A-D])\s+(said|suggested|proposed|notes?|argues?|thinks?|mentioned|claimed|claims)\b")
ADDRESS_RE = re.compile(
    r"(?i)\b(well done|thank you|thanks|agree with|kudos to|building on|good point|nice work)"
    r"([,!.]?\s+)([A-D])\b")


def clean(text):
    t = text
    t = ROLE_RE.sub("", t)
    t = ROLE_ABBR_RE.sub("", t)
    t = POSSESSIVE_RE.sub("", t)                       # "A's approach" -> " approach"
    t = VOCATIVE_MID_RE.sub("", t)                     # "start, D!" -> "start!"
    t = VOCATIVE_INIT_RE.sub("", t)                    # "D, let's" -> "let's"
    t = EXPLICIT_RE.sub(lambda m: m.group(2), t)       # "B said" -> "said"
    t = ADDRESS_RE.sub(lambda m: m.group(1), t)        # "well done, C" -> "well done"
    # tidy
    t = re.sub(r"\bas\s+a\s+,", "", t)                 # leftover "as a ," from role removal
    t = re.sub(r"[ \t]+([.,!?;:])", r"\1", t)
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"(?m)^[ \t]*[,:;]+[ \t]*", "", t)
    t = "\n".join(line.strip() for line in t.split("\n"))
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def all_matches(text):
    """(pattern_label, matched_string, start) for every removal, for auditing."""
    out = []
    for label, rx in [("role", ROLE_RE), ("role_abbr", ROLE_ABBR_RE), ("possessive", POSSESSIVE_RE),
                      ("vocative_mid", VOCATIVE_MID_RE), ("vocative_init", VOCATIVE_INIT_RE),
                      ("explicit", EXPLICIT_RE), ("address", ADDRESS_RE)]:
        for m in rx.finditer(text):
            out.append((label, m.group(), m.start()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    a = ap.parse_args()

    docs = [json.loads(l) for l in open(PROCESSED, encoding="utf-8") if l.strip()]
    per_label = Counter()
    unique_ctx = {}
    out_rows = []
    total = 0
    for d in docs:
        txt = d.get(FIELD, "")
        for label, hit, pos in all_matches(txt):
            per_label[label] += 1
            total += 1
            pre = txt[max(0, pos - 22):pos].split("\n")[-1]
            post = txt[pos + len(hit):pos + len(hit) + 22].split("\n")[0]
            key = (label, f"...{pre}⟦{hit.strip()}⟧{post}...")
            unique_ctx[key] = unique_ctx.get(key, 0) + 1
        nd = dict(d)
        # clean EVERY text-bearing field the methods consume:
        #   full_text_no_labels  -> Method 3 tagger input
        #   turns[].text_clean/text_raw, labeled_turns[].text -> Methods 1 & 2 (turns_to_paras/_turns)
        nd[FIELD] = clean(txt)
        if isinstance(nd.get("turns"), list):
            nd["turns"] = [{**t, **({"text_clean": clean(t["text_clean"])} if "text_clean" in t else {}),
                            **({"text_raw": clean(t["text_raw"])} if "text_raw" in t else {})}
                           for t in nd["turns"]]
        if isinstance(nd.get("labeled_turns"), list):
            nd["labeled_turns"] = [{**t, **({"text": clean(t["text"])} if "text" in t else {})}
                                   for t in nd["labeled_turns"]]
        info = dict(nd.get("processing_info", {}))
        info["refix_labels"] = {"removed_refs_full_text": len(all_matches(txt)),
                                "roles": ROLE_TITLES, "letter_refs": "surgical case-sensitive",
                                "fields_cleaned": ["full_text_no_labels", "turns[].text_clean/raw",
                                                   "labeled_turns[].text"]}
        nd["processing_info"] = info
        out_rows.append(nd)

    print("=== removals by pattern ===")
    for label, c in per_label.most_common():
        print(f"  {label:16s} {c}")
    print(f"  TOTAL removed: {total}")

    # residual leak checks on cleaned output
    role_res = sum(len(re.findall(r"(?i)"+_role_alt, r[FIELD])) for r in out_rows)
    poss_res = sum(len(POSSESSIVE_RE.findall(r[FIELD])) for r in out_rows)
    print(f"\n  residual role-titles after cleaning: {role_res}  (target 0)")
    print(f"  residual possessive X's after cleaning: {poss_res}  (target 0)")

    # false-positive sentinel: did we ever remove a sentence-initial article 'A'? (should be 0)
    art = 0
    for d in docs:
        for label, hit, pos in all_matches(d.get(FIELD, "")):
            if hit.strip() in ("A", "A,") and re.match(r"(?m)^A\s+[a-z]", d[FIELD][pos:pos+3] or ""):
                art += 1
    print(f"  article-'A' false positives caught: {art}  (must be 0)")

    print(f"\n=== unique removal contexts by pattern (scan for false positives) ===")
    for label in ("possessive", "vocative_mid", "vocative_init", "explicit", "address", "role_abbr"):
        rows = [(k[1], c) for k, c in unique_ctx.items() if k[0] == label]
        rows.sort(key=lambda x: -x[1])
        print(f"\n-- {label} ({len(rows)} distinct) --")
        for snip, c in rows[:18]:
            print(f"  x{c:<3d} {snip}".replace('\n', ' '))

    out = PROCESSED if a.commit else TEMP
    with open(out, "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n{'COMMITTED' if a.commit else 'PREVIEW (not committed)'}: {len(out_rows)} rows -> {out.name}")


if __name__ == "__main__":
    main()
