"""Re-clean human_debate speaker-label leak (STATUS.md deviation, 2026-07).

The original standardize_datasets.py stripped only line-start `Name:` prefixes for a HARDCODED
animal list, which (a) missed the two-word name "Guinea pig:" entirely (444/444 left intact),
and (b) left ~1,000 inline references ("@Cat", "Thanks Bat", "I agree with Bee", lowercase
"yes kiwi is right") untouched. Animal pseudonyms are the top-1/2/3 most-frequent tokens per
human_debate document, so this is a hard condition leak: any method keying on tokens (Method 1
MFT clustering), sentence embeddings (Method 2), or dialogue structure (Method 3) can shortcut
"this is human_debate" from the names rather than genuine signal.

This script fixes it robustly and AUDITABLY:

  * Derives the speaker-name set from the data itself - every distinct line-start `Name:` turn
    prefix - and keeps only those above a frequency floor (the "cliff": real pseudonyms appear
    300+ times, incidental "Word:" appears once or twice). No hardcoded list.
  * Removes each name case-insensitively as a WHOLE WORD everywhere it occurs (turn-prefix OR
    inline), plus a trailing `:` and a leading `@`, then tidies the resulting whitespace.
  * Is NON-DESTRUCTIVE by default: writes a temp file + prints a full audit (derived name set,
    per-name removal counts, and every UNIQUE removal context deduped) so false positives can
    be caught before committing. Pass --commit to overwrite the real processed file.

Only human_debate is affected; ai_debate uses A-D labels (already clean), monologue cells and
ai_reasoning have no speakers. See STATUS.md.

Usage (from repo root):
    python scripts/refix_human_debate_labels.py            # audit only, writes temp
    python scripts/refix_human_debate_labels.py --commit   # overwrite processed_human_debate.jsonl
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/human_debate/unprocessed/human_debate_with_speaker_labels.jsonl"
PROCESSED = ROOT / "data/human_debate/processed_human_debate.jsonl"
TEMP = ROOT / "data/human_debate/processed_human_debate.REFIX_PREVIEW.jsonl"

FREQ_FLOOR = 20   # a turn-prefix must occur >= this many times corpus-wide to count as a speaker
                  # (real pseudonyms: 307-693; the cliff to incidental "Word:" is enormous)


def load(fp):
    return [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]


def derive_speaker_names(docs):
    """Every distinct line-start `Name:` (1-2 words) that clears the frequency floor."""
    pat = re.compile(r"(?m)^[ \t@]*([A-Za-z][A-Za-z]*(?:\s+[A-Za-z]+)?)\s*:")
    counts = Counter()
    for d in docs:
        for m in pat.findall(d["transcript"]):
            counts[m.strip()] += 1
    kept = {n: c for n, c in counts.items() if c >= FREQ_FLOOR}
    dropped = {n: c for n, c in counts.items() if c < FREQ_FLOOR}
    return kept, dropped


def build_remover(names):
    """Return (clean_fn, count_fn) for the given name set. Longest names first so 'Guinea pig'
    matches before 'pig'. Whole-word, case-insensitive."""
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    # turn prefix at line start: optional @, name, colon, trailing space
    turn_re = re.compile(rf"(?im)^[ \t]*@?\s*\b(?:{alt})\b[ \t]*:[ \t]*")
    # inline: optional leading @ (+ optional space), name as whole word, optional trailing colon
    inline_re = re.compile(rf"(?i)@[ \t]*\b(?:{alt})\b:?|\b(?:{alt})\b:?")

    def clean(text):
        t = turn_re.sub("", text)
        t = inline_re.sub("", t)
        # tidy: space before punctuation, collapsed spaces, empty-ish lines, leftover leading punct
        t = re.sub(r"[ \t]+([.,!?;:])", r"\1", t)
        t = re.sub(r"[ \t]{2,}", " ", t)
        t = re.sub(r"(?m)^[ \t]*[,:;]+[ \t]*", "", t)  # a line that now starts with stray punct
        t = "\n".join(line.strip() for line in t.split("\n"))
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()

    def count(text):
        return len(turn_re.findall(text)) + len(inline_re.findall(text))

    return clean, count, turn_re, inline_re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true",
                    help="overwrite the real processed_human_debate.jsonl (default: temp + audit only)")
    a = ap.parse_args()

    docs = load(RAW)
    kept, dropped = derive_speaker_names(docs)
    print(f"=== derived speaker-name set ({len(kept)} names, floor={FREQ_FLOOR}) ===")
    for n, c in sorted(kept.items(), key=lambda x: -x[1]):
        print(f"  {n:14s} {c}")
    if dropped:
        print(f"\n  dropped below floor (NOT treated as speakers): "
              f"{dict(sorted(dropped.items(), key=lambda x:-x[1])[:15])}")
    else:
        print("\n  (nothing sat below the floor - clean cliff, no ambiguous candidates)")

    clean, count, turn_re, inline_re = build_remover(set(kept))

    # audit: collect every UNIQUE removal context (what got deleted + a little surrounding text),
    # using the actual remover regexes so the audit matches exactly what will be deleted.
    def contexts(text):
        for rx in (turn_re, inline_re):
            for m in rx.finditer(text):
                pre = text[max(0, m.start() - 20):m.start()]
                post = text[m.end():m.end() + 20]
                yield f"...{pre}⟦{m.group().strip()}⟧{post}...".replace("\n", "⏎")

    unique_ctx = Counter()
    total_removed = 0
    per_name = Counter()
    out_rows = []
    for d in docs:
        raw_t = d["transcript"]
        total_removed += count(raw_t)
        for snip in contexts(raw_t):
            unique_ctx[snip] += 1
        low = raw_t.lower()
        for n in kept:
            per_name[n] += len(re.findall(rf"\b{re.escape(n.lower())}\b", low))
        nd = dict(d)
        cleaned = clean(raw_t)
        nd["transcript"] = cleaned
        info = dict(nd.get("processing_info", {}))
        info["refix_speaker_labels"] = {
            "removed_name_tokens": count(raw_t),
            "names_used": sorted(kept),
            "method": "derived-set, case-insensitive whole-word, turn+inline, floor%d" % FREQ_FLOOR,
        }
        nd["processing_info"] = info
        out_rows.append(nd)

    print(f"\n=== removal totals ===")
    print(f"  total name-tokens removed across 500 docs: {total_removed}")
    print(f"  per-name whole-word occurrences (turn+inline): "
          f"{dict(sorted(per_name.items(), key=lambda x:-x[1]))}")

    # residual leak check on the cleaned output
    residual = 0
    for nd in out_rows:
        low = nd["transcript"].lower()
        for n in kept:
            residual += len(re.findall(rf"\b{re.escape(n.lower())}\b", low))
    print(f"  residual name occurrences AFTER cleaning: {residual}  (must be 0)")

    print(f"\n=== every UNIQUE removal context ({len(unique_ctx)} distinct), "
          f"scan for any that is CONTENT not a speaker reference ===")
    for snip, c in unique_ctx.most_common():
        print(f"  x{c:<4d} {snip}")

    out = PROCESSED if a.commit else TEMP
    with open(out, "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n{'COMMITTED' if a.commit else 'PREVIEW (not committed)'}: wrote {len(out_rows)} rows -> {out.name}")
    if not a.commit:
        print("Re-run with --commit to overwrite the real processed_human_debate.jsonl once the audit looks clean.")


if __name__ == "__main__":
    main()
