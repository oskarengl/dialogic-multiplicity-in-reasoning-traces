"""Local hand-labeling UI for the Method 3 reliability worksheet (methods.md sec. 3e.1).

Serves a click-to-label interface at http://127.0.0.1:8765 backed by
outputs/method3/reliability/worksheet.csv. Every label is persisted the moment you click it:

  1. worksheet.csv          rewritten atomically (temp file + os.replace) after each label
  2. journal.jsonl          append-only log, one line per action, never rewritten
  3. backups/worksheet_*.csv timestamped snapshot every SNAPSHOT_EVERY labels

The journal is the real safety net: even if the CSV is somehow corrupted, every label you
ever entered can be replayed from it (`--rebuild-from-journal`).

TWO MODES
---------
Real labeling (/)          Blind. You never see the LLM's label. This is the measurement.
Practice   (/practice)     ALSO BLIND, same interaction as real labeling - drawn from a pool
                           guaranteed disjoint from the real worksheet, but otherwise no
                           different while you're working. You label it as you read it, with
                           no indication of whether you match the tagger, per item or in
                           aggregate. Comparison only happens afterward, out of the loop, via
                           `python label_server.py --practice-report` - not something you
                           watch tick up while you work. The reasoning: even per-item ✓/✗
                           feedback is a reinforcement signal - over 200 items you would start
                           predicting this specific model's habits rather than applying the
                           CAMS definitions, which defeats the point of an independent check.

GUARANTEES:

  1. Blindness (real labeling AND practice): neither mode's serving routes ever open or
     transmit hidden_llm_labels.json / practice_answers.json to the browser. No route can
     serve them, at any point during a session.
  2. Disjointness (practice): the practice set is drawn from utterances GUARANTEED DISJOINT
     from the real worksheet - enforced in code (`--make-practice` excludes every worksheet
     key and then asserts the intersection is empty), not by you remembering. Practicing on
     an item can therefore never contaminate an item you later label for real.
  3. No feedback during practice, live or per-item: nothing about correctness - not a running
     score, not a single ✓/✗ - is ever sent to the browser or rendered anywhere in the UI
     while you are labeling. It only exists in `--practice-report`, run manually, after the
     fact, reading straight from the two saved CSVs.

The /api/context route returns neighbouring sentences as TEXT ONLY; the source JSONL also
contains the LLM's label for those neighbours and it is stripped before sending.

Usage (from this directory):
    python label_server.py                       # start, opens browser
    python label_server.py --make-practice 200   # draw a fresh disjoint practice set
    python label_server.py --port 9000
    python label_server.py --no-browser
    python label_server.py --status              # print progress, don't serve
    python label_server.py --rebuild-from-journal  # restore CSV from the append-only log

Stdlib only - no pip install needed.
"""
import argparse, csv, json, os, random, shutil, sys, threading, time, webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
# labeling_tool/ -> 3_dialogue_act_tagging/ -> methods/ -> project root
ROOT = HERE.parent.parent.parent
OUTBASE = ROOT / "outputs" / "method3"
RELDIR = OUTBASE / "reliability"
WORKSHEET = RELDIR / "worksheet.csv"
JOURNAL = RELDIR / "journal.jsonl"
BACKUPDIR = RELDIR / "backups"
PRACTICE = RELDIR / "practice.csv"
PRACTICE_ANS = RELDIR / "practice_answers.json"
PRACTICE_LOG = RELDIR / "practice_journal.jsonl"
FIELDS = ["cell", "cell_name", "doc_id", "sentence_idx", "text", "human_label"]
SNAPSHOT_EVERY = 25

CELL_DIRS = {"1": "cell1_human_monologue", "2": "cell2_human_debate",
             "3": "cell3_ai_debate", "4": "cell4_ai_monologue"}
CELL_LABEL = {"1": "human_monologue", "2": "human_debate",
              "3": "ai_debate", "4": "ai_monologue"}

# Tag list must match signals.py TAGS exactly (27 CAMS tags + none).
TAGS = [
    "propositionalQuestion", "setQuestion", "choiceQuestion", "checkQuestion",
    "inform", "answer", "agreement", "disagreement", "correction", "confirm", "disconfirm",
    "offer", "conditionalAccept", "accept", "decline", "request", "suggest",
    "autoPositive", "autoNegative", "stalling", "retraction",
    "greeting", "goodbye", "thanking", "acceptThanking", "apology", "acceptApology",
    "none",
]
TAGSET = set(TAGS)

_lock = threading.Lock()
_rows = []
_practice = []
_since_snapshot = [0]     # mutable cell so _apply_label can increment it in place
_since_snapshot_p = [0]


# ----------------------------------------------------------------- worksheet I/O

def load_rows(path=WORKSHEET, required=True):
    if not path.exists():
        if not required:
            return []
        sys.exit(f"No worksheet at {path}\n"
                 f"Run:  python reliability_sample.py --sample   (in ../implementation/)")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["human_label"] = (r.get("human_label") or "").strip()
    return rows


def save_csv(rows, path):
    """Atomic rewrite: full write to a temp file, then os.replace (atomic on Windows + POSIX),
    so an interrupted save can never leave a half-written worksheet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    os.replace(tmp, path)


def journal(path, action, **kw):
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "action": action, **kw}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def snapshot(src_path, prefix):
    BACKUPDIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(src_path, BACKUPDIR / f"{prefix}_{stamp}.csv")
    for old in sorted(BACKUPDIR.glob(f"{prefix}_*.csv"))[:-20]:
        old.unlink()


def row_key(r):
    return f"{r['cell']}:{r['doc_id']}:{r['sentence_idx']}"


def _apply_label(rows, path, journal_path, snap_prefix, counter, idx, label):
    """Shared save path for both real and practice labeling. Deliberately returns nothing
    about correctness - callers (both /api/label and /api/practice/label) only ever get back
    {done, total}, never a truth value. That is what keeps practice blind: this function has
    no access to hidden_llm_labels.json / practice_answers.json in the first place."""
    with _lock:
        if not (0 <= idx < len(rows)):
            return False, f"index {idx} out of range"
        if label != "" and label not in TAGSET:
            return False, f"unknown tag {label!r}"
        prev = rows[idx]["human_label"]
        rows[idx]["human_label"] = label
        save_csv(rows, path)
        journal(journal_path, "label", idx=idx, key=row_key(rows[idx]), label=label, prev=prev)
        counter[0] += 1
        if counter[0] >= SNAPSHOT_EVERY:
            snapshot(path, snap_prefix)
            counter[0] = 0
        done = sum(1 for r in rows if r["human_label"])
    return True, {"done": done, "total": len(rows)}


def apply_label(idx, label):
    return _apply_label(_rows, WORKSHEET, JOURNAL, "worksheet", _since_snapshot, idx, label)


def apply_practice_label(idx, label):
    return _apply_label(_practice, PRACTICE, PRACTICE_LOG, "practice", _since_snapshot_p, idx, label)


# ----------------------------------------------------------------- context lookup

def doc_lines(cell, doc_id):
    """Raw lines of one source document. sentence_idx indexes raw lines (matches how
    reliability_sample.py enumerated them), so no re-indexing is needed."""
    d = CELL_DIRS.get(str(cell))
    if not d:
        return None
    fp = OUTBASE / d / f"{doc_id}.jsonl"
    if not fp.exists():
        return None
    return fp.read_text(encoding="utf-8").splitlines()


def get_context(cell, doc_id, idx, window=3):
    """Neighbouring sentences, TEXT ONLY. The source JSONL also holds the LLM's label for
    each neighbour - it is deliberately NOT included, or the worksheet would stop being blind."""
    lines = doc_lines(cell, doc_id)
    if lines is None:
        return {"error": "document not found", "before": [], "after": []}
    out = {"before": [], "after": [], "n_lines": len(lines)}
    for j in range(max(0, idx - window), min(len(lines), idx + window + 1)):
        raw = lines[j].strip()
        if not raw:
            continue
        try:
            text = json.loads(raw).get("text", "")   # .get("label") intentionally dropped
        except Exception:
            continue
        if j < idx:
            out["before"].append({"i": j, "text": text})
        elif j > idx:
            out["after"].append({"i": j, "text": text})
    return out


# ----------------------------------------------------------------- practice set

def scan_pool(exclude_keys):
    """All labeled utterances across cells 1-4, minus the excluded keys."""
    pool = []
    for cell, d in CELL_DIRS.items():
        cdir = OUTBASE / d
        if not cdir.exists():
            continue
        for fp in sorted(cdir.glob("*.jsonl")):
            doc_id = fp.stem
            try:
                lines = fp.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for idx, raw in enumerate(lines):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    continue
                lbl = rec.get("label")
                if lbl not in TAGSET:
                    continue
                key = f"{cell}:{doc_id}:{idx}"
                if key in exclude_keys:
                    continue
                pool.append({"cell": cell, "cell_name": CELL_LABEL[cell], "doc_id": doc_id,
                             "sentence_idx": str(idx), "text": rec.get("text", ""),
                             "label": lbl, "key": key})
    return pool


def make_practice(n, seed=None):
    """Draw a practice set GUARANTEED disjoint from the real worksheet, stratified by cell."""
    real = load_rows(WORKSHEET, required=True)
    exclude = {row_key(r) for r in real}
    print(f"worksheet holds {len(real)} items; excluding those keys from the practice pool...")
    print("scanning source documents (a few seconds)...")
    pool = scan_pool(exclude)
    print(f"pool after exclusion: {len(pool):,} utterances")
    if not pool:
        sys.exit("Empty pool - are the cell tag directories present under outputs/method3/?")

    rng = random.Random(seed)
    # stratify proportionally to the real worksheet's cell mix, so practice feels like the task
    mix = {}
    for r in real:
        mix[r["cell"]] = mix.get(r["cell"], 0) + 1
    by_cell = {}
    for p in pool:
        by_cell.setdefault(p["cell"], []).append(p)

    chosen = []
    for cell, cnt in sorted(mix.items()):
        want = max(1, round(n * cnt / len(real)))
        avail = by_cell.get(cell, [])
        chosen += rng.sample(avail, min(want, len(avail)))
    rng.shuffle(chosen)
    chosen = chosen[:n]

    # hard guarantee, asserted rather than assumed
    overlap = {c["key"] for c in chosen} & exclude
    assert not overlap, f"practice/worksheet overlap: {sorted(overlap)[:5]}"

    rows, answers = [], {}
    for c in chosen:
        rows.append({k: c[k] for k in ("cell", "cell_name", "doc_id", "sentence_idx", "text")}
                    | {"human_label": ""})
        answers[c["key"]] = c["label"]
    save_csv(rows, PRACTICE)
    PRACTICE_ANS.write_text(json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8")

    from collections import Counter
    print(f"\nwrote {len(rows)} practice items -> {PRACTICE}")
    print(f"answers (kept hidden until --practice-report) -> {PRACTICE_ANS}")
    print(f"disjoint from worksheet          -> VERIFIED (0 shared keys)")
    print("cell mix:", dict(Counter(r["cell_name"] for r in rows)))


def load_practice():
    """Only reads practice.csv (your blind guesses so far) - never touches
    practice_answers.json. The answer file is opened only by practice_report(), a separate
    CLI-only code path the HTTP server never calls."""
    return load_rows(PRACTICE, required=False)


# ----------------------------------------------------------------- misc commands

def progress():
    done = sum(1 for r in _rows if r["human_label"])
    per = {}
    for r in _rows:
        c = r["cell_name"]
        d, t = per.get(c, (0, 0))
        per[c] = (d + (1 if r["human_label"] else 0), t + 1)
    return done, len(_rows), per


def rebuild_from_journal():
    if not JOURNAL.exists():
        sys.exit(f"No journal at {JOURNAL}")
    by_key, n = {}, 0
    with open(JOURNAL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("action") == "label" and "key" in rec:
                by_key[rec["key"]] = rec.get("label", "")
                n += 1
    restored = 0
    for r in _rows:
        if row_key(r) in by_key:
            r["human_label"] = by_key[row_key(r)]
            restored += 1
    save_csv(_rows, WORKSHEET)
    print(f"Replayed {n} journal entries -> {restored} rows restored in {WORKSHEET}")


def practice_report(show_items=False):
    """Aggregate practice stats, CLI-only - deliberately no HTTP route serves this or
    practice_answers.json. The live UI is fully blind, same as real labeling: no per-item
    ✓/✗, no running score, nothing. This is the only place the comparison happens, and it
    only runs when you type the command yourself, after you've already committed your
    guesses - so it can inform your review/write-up without ever being able to bias the
    labeling itself."""
    if not PRACTICE.exists():
        sys.exit(f"No practice set at {PRACTICE} - run --make-practice first.")
    if not PRACTICE_ANS.exists():
        sys.exit(f"No answer key at {PRACTICE_ANS} - run --make-practice first.")
    rows = load_rows(PRACTICE, required=True)
    answers = json.loads(PRACTICE_ANS.read_text(encoding="utf-8"))

    answered = [r for r in rows if r["human_label"]]
    hits, misses, detail = 0, {}, []
    for r in answered:
        truth = answers.get(row_key(r), "")
        guess = r["human_label"]
        match = guess == truth
        hits += match
        if not match:
            misses[f"{guess} -> {truth}"] = misses.get(f"{guess} -> {truth}", 0) + 1
        detail.append((r["text"], guess, truth, match))

    n = len(answered)
    print(f"practice items answered: {n} / {len(rows)}")
    if n:
        print(f"raw agreement: {hits}/{n} = {100*hits/n:.0f}%  "
              f"(no chance-correction - this is not kappa, just a rough signal)")
    if misses:
        print("\nmost common your-tag -> tagger's-tag mismatches:")
        for k, v in sorted(misses.items(), key=lambda x: -x[1])[:12]:
            print(f"  {k:55s} x{v}")
    if show_items:
        print("\nper-item detail:")
        for text, guess, truth, match in detail:
            mark = "match" if match else "DIFF "
            print(f"  [{mark}] you={guess:22s} tagger={truth:22s} | {text[:70]}")


# ----------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    # Only these files are ever servable. hidden_llm_labels.json is deliberately unreachable.
    STATIC = {"/": "ui.html", "/ui.html": "ui.html", "/practice": "ui.html",
              "/cams_tags.js": "cams_tags.js", "/codebook.html": "codebook.html"}

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        path, qs = u.path, parse_qs(u.query)

        if path in self.STATIC:
            fp = HERE / self.STATIC[path]
            if not fp.exists():
                return self._send(404, f"missing {fp.name}", "text/plain; charset=utf-8")
            ctype = ("text/html; charset=utf-8" if fp.suffix == ".html"
                     else "application/javascript; charset=utf-8")
            return self._send(200, fp.read_text(encoding="utf-8"), ctype)

        if path == "/api/rows":
            with _lock:
                payload = [{"i": i, "cell": r["cell"],
                            "doc_id": r["doc_id"], "sentence_idx": int(r["sentence_idx"]),
                            "text": r["text"], "human_label": r["human_label"]}
                           for i, r in enumerate(_rows)]
            return self._send(200, {"rows": payload, "tags": TAGS, "mode": "real"})

        if path == "/api/practice/rows":
            # blind, same shape as /api/rows - answers are never loaded server-side during
            # serving at all (practice_answers.json is only opened by --practice-report)
            with _lock:
                payload = [{"i": i, "cell": r["cell"],
                            "doc_id": r["doc_id"], "sentence_idx": int(r["sentence_idx"]),
                            "text": r["text"], "human_label": r["human_label"]}
                           for i, r in enumerate(_practice)]
            return self._send(200, {"rows": payload, "tags": TAGS, "mode": "practice",
                                    "ready": bool(_practice)})

        if path == "/api/context":
            try:
                cell = qs["cell"][0]
                doc_id = qs["doc_id"][0]
                idx = int(qs["idx"][0])
                window = int(qs.get("window", ["3"])[0])
            except Exception as e:
                return self._send(400, {"error": f"bad params: {e}"})
            if ".." in doc_id or "/" in doc_id or "\\" in doc_id:
                return self._send(400, {"error": "bad doc_id"})
            return self._send(200, get_context(cell, doc_id, idx, max(0, min(window, 12))))

        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send(400, {"error": f"bad body: {e}"})

        if path == "/api/label":
            try:
                ok, res = apply_label(int(data["idx"]), str(data.get("label", "")))
            except Exception as e:
                return self._send(400, {"error": f"{type(e).__name__}: {e}"})
            return self._send(200 if ok else 400, res if ok else {"error": res})

        if path == "/api/practice/label":
            # mirrors /api/label exactly - saves the guess, returns only {done, total}.
            # apply_practice_label() has no access to practice_answers.json, so there is
            # no code path here that could return correctness even by mistake.
            try:
                ok, res = apply_practice_label(int(data["idx"]), str(data.get("label", "")))
            except Exception as e:
                return self._send(400, {"error": f"{type(e).__name__}: {e}"})
            return self._send(200 if ok else 400, res if ok else {"error": res})

        return self._send(404, {"error": "not found"})


def main():
    global _rows, _practice
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--status", action="store_true", help="print progress and exit")
    ap.add_argument("--make-practice", type=int, metavar="N",
                    help="draw N practice items, guaranteed disjoint from the worksheet")
    ap.add_argument("--seed", type=int, default=None,
                    help="seed for --make-practice (default: random each time)")
    ap.add_argument("--rebuild-from-journal", action="store_true",
                    help="restore worksheet.csv by replaying journal.jsonl")
    ap.add_argument("--practice-report", action="store_true",
                    help="print aggregate practice stats (CLI-only, check after a session, "
                         "never shown live in the UI - see practice_report() docstring)")
    ap.add_argument("--items", action="store_true",
                    help="with --practice-report, also print every item's guess vs. tagger label")
    a = ap.parse_args()

    if a.make_practice:
        return make_practice(a.make_practice, a.seed)
    if a.practice_report:
        return practice_report(show_items=a.items)

    _rows = load_rows()
    if a.rebuild_from_journal:
        return rebuild_from_journal()
    _practice = load_practice()

    done, total, per = progress()
    print(f"worksheet : {WORKSHEET}")
    print(f"progress  : {done}/{total} labeled")
    for c, (d, t) in sorted(per.items()):
        print(f"            {c:16s} {d:4d}/{t}")
    if a.status:
        if _practice:
            print(f"practice  : {len(_practice)} items ready")
        return

    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    url = f"http://127.0.0.1:{a.port}/"
    print(f"\nserving   : {url}   (Ctrl-C to stop)")
    if _practice:
        print(f"practice  : {url}practice   ({len(_practice)} items, disjoint from worksheet)")
    else:
        print(f"practice  : none yet - run  python label_server.py --make-practice 200")
    print(f"journal   : {JOURNAL}")
    print(f"backups   : {BACKUPDIR}  (every {SNAPSHOT_EVERY} labels)")
    if not a.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped. all labels already saved.")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
