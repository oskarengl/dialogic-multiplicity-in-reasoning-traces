"""Method 1 (Nath TBC) on the four calibration cells - frozen spec, methods.md sec. 1.

Configuration (all fixed, matching the paper as described):
  - Matusita distance; merge_threshold=add_node_threshold=50; prune=True;
    number_of_terms=50; use_duplication_feature=True; TBC only.
  - 200-char merge fix: the shipped remove_empty_para() DROPS paragraphs < 200 chars
    (a regex bug - an empty alternative makes re.match always true). The paper specifies
    MERGING them into the previous window. We monkeypatch that function with the merge
    behavior. TBC consumes only a pairwise window-distance matrix (no sequence order),
    so "merge into previous" is a well-defined, deterministic rule.
  - Windowing (methods.md sec. 1): turn-structured cells are assembled one turn per
    paragraph (joined by blank lines) so each turn becomes a PAN-style "post"; continuous
    -prose cells are passed raw and handled by Nath's own splitter.

Ground truth: cells 1 & 4 are single-voice (monologue); cells 2 & 3 are multi-voice
(dialogue). Gate (methods.md sec. 1): BALANCED accuracy = mean(recall_single, recall_multi)
significantly exceeds 0.50 (label-permutation null, one-sided p < .05). Balanced accuracy is
used instead of pooled accuracy because the cells are class-imbalanced (~1200 single vs ~1100
multi): an all-single detector scores ~0.52 pooled but exactly 0.50 balanced, so passing
requires genuinely detecting multi-voice text.

Usage:
    python run_calibration.py                 # run all 4 cells fully, then report the gate
    python run_calibration.py CELL START END  # run one index range (for resuming/chunking)
    python run_calibration.py --report        # recompute the gate from existing predictions
"""
import os, sys, json, time, contextlib
import preprocess_NLP_pkg
import src.algorithms.preprocessing as prep

_NULL = open(os.devnull, "w")


# --- 200-char merge fix (replaces the shipped remove_empty_para drop-bug) ---
def merge_short_paragraphs(para_list, min_chars=200):
    paras = [p for p in para_list if p and p.strip()]
    if not paras:
        return paras
    changed = True
    while changed and len(paras) > 1:
        changed = False
        for i, p in enumerate(paras):
            if len(p) < min_chars:
                if i > 0:
                    paras[i - 1] = paras[i - 1] + "\n\n" + p
                else:
                    paras[i + 1] = p + "\n\n" + paras[i + 1]
                del paras[i]
                changed = True
                break
    return paras


prep.remove_empty_para = merge_short_paragraphs  # used by paragraph_tokenizer at call time
from src.algorithms.threshold_clustering.executor import execute_threshold_clustering

ROOT = os.path.abspath("../../..")
D = os.path.join(ROOT, "data")


def prose(rec, field):
    return rec.get(field, "") or ""


def lines_to_paras(rec, field):                      # one transcript line -> one paragraph
    txt = rec.get(field, "") or ""
    return "\n\n".join(s for s in (l.strip() for l in txt.split("\n")) if s)


def turns_to_paras(rec, _=None):                     # one debate turn -> one paragraph
    return "\n\n".join(t.get("text_clean", "").strip()
                       for t in rec.get("turns", []) if t.get("text_clean", "").strip())


# cell: (file, text-builder, true_bin)   true_bin: 1 = single (mono), 0 = multi (dia)
CELLS = {
    "1": (os.path.join(D, "human_monologue", "human_think_aloud_600.jsonl"),
          lambda r: prose(r, "think_trace"), 1),
    "2": (os.path.join(D, "human_debate", "processed_human_debate.jsonl"),
          lambda r: lines_to_paras(r, "transcript"), 0),
    "3": (os.path.join(D, "ai_debate", "processed_ai_debate.jsonl"),
          turns_to_paras, 0),
    "4": (os.path.join(D, "ai_monologue", "processed_prompted_ai_monologue.jsonl"),
          lambda r: prose(r, "transcript"), 1),
    # --- Step 2 target, added 2026-07-22 after the gate passed (methods.md sec. 4). ---
    # Data path only: the builder is byte-identical to cell 1's (continuous prose in
    # "think_trace"), so no new text handling is introduced. true_bin is None because the
    # target has no ground-truth label - it is placed, not scored. Cell 5 predictions are
    # written to a SEPARATE file so calibration_predictions.jsonl, and therefore the frozen
    # gate result (balanced accuracy 0.6088), cannot be altered by running the target.
    "5": (os.path.join(D, "ai_reasoning", "processed_native_reasoning_traces.jsonl"),
          lambda r: prose(r, "think_trace"), None),
}
LABEL = {"1": "human_monologue", "2": "human_debate", "3": "ai_debate", "4": "ai_monologue",
         "5": "ai_reasoning"}

OUTDIR = os.path.join(ROOT, "outputs", "method1")
os.makedirs(OUTDIR, exist_ok=True)
OUTFILE = os.path.join(OUTDIR, "calibration_predictions.jsonl")
CELL5FILE = os.path.join(OUTDIR, "cell5_predictions.jsonl")


def predict_text(text):
    if not text.strip():
        return 1
    with contextlib.redirect_stdout(_NULL):
        return execute_threshold_clustering(
            text, merge_threshold=50, add_node_threshold=50, prune=True, number_of_terms=50,
            distance_measure=preprocess_NLP_pkg.matusita_distance, use_duplication_feature=True)


def run_range(cell, start, end, out):
    path, build, true_bin = CELLS[cell]
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()][start:end]
    t0 = time.time()
    for i, rec in enumerate(recs):
        pred = predict_text(build(rec))
        out.write(json.dumps({"cell": cell, "idx": start + i, "true_bin": true_bin,
                              "pred_count": pred, "pred_bin": 1 if pred == 1 else 0}) + "\n")
        out.flush()
    print(f"cell {cell} ({LABEL[cell]}) [{start}:{end}] n={len(recs)} ({time.time()-t0:.0f}s)")


def report():
    import numpy as np
    rows = [json.loads(l) for l in open(OUTFILE, encoding="utf-8") if l.strip()]
    # Defensive: the gate is defined over the four calibration cells only. Cell 5 is written
    # to its own file, so this filter is a no-op on a correct run - it exists so that a
    # mis-routed target row can never silently move the gate number.
    rows = [r for r in rows if r.get("cell") in ("1", "2", "3", "4")]
    if not rows:
        print("No predictions yet."); return
    true = np.array([r["true_bin"] for r in rows])   # 1 = single (mono), 0 = multi (dia)
    pred = np.array([r["pred_bin"] for r in rows])
    correct = (true == pred).astype(float)

    print(f"\n{'cell':16s} {'n':>5s} {'correct':>8s} {'recall':>7s}")
    for c in ("1", "2", "3", "4"):
        r = [x for x in rows if x["cell"] == c]
        if not r:
            continue
        ok = sum(x["true_bin"] == x["pred_bin"] for x in r)
        print(f"{LABEL[c]:16s} {len(r):>5d} {ok:>8d} {ok/len(r):>7.3f}")

    recall_single = correct[true == 1].mean() if (true == 1).any() else 0.0
    recall_multi = correct[true == 0].mean() if (true == 0).any() else 0.0
    bacc = 0.5 * (recall_single + recall_multi)

    tp = {(t, p): int(((true == t) & (pred == p)).sum()) for t in (1, 0) for p in (1, 0)}
    print(f"\nConfusion (true \\ pred):     pred_single  pred_multi")
    print(f"  true_single (mono, 1&4):   {tp[(1,1)]:>10d}  {tp[(1,0)]:>10d}")
    print(f"  true_multi  (dia,  2&3):   {tp[(0,1)]:>10d}  {tp[(0,0)]:>10d}")

    rng = np.random.default_rng(0)
    # label-permutation null: shuffle truth, recompute balanced accuracy (centres at 0.50)
    perm = np.empty(10000)
    for i in range(10000):
        t = rng.permutation(true)
        c = (t == pred).astype(float)
        perm[i] = 0.5 * (c[t == 1].mean() + c[t == 0].mean())
    p_perm = (np.sum(perm >= bacc) + 1) / (len(perm) + 1)
    # bootstrap 95% CI on balanced accuracy (resample within each class)
    idx_s, idx_m = np.where(true == 1)[0], np.where(true == 0)[0]
    boot = np.empty(2000)
    for i in range(2000):
        bs, bm = rng.choice(idx_s, len(idx_s)), rng.choice(idx_m, len(idx_m))
        boot[i] = 0.5 * (correct[bs].mean() + correct[bm].mean())
    lo, hi = np.percentile(boot, [2.5, 97.5])

    print(f"\nrecall_single (mono 1&4) = {recall_single:.4f}"
          f"   recall_multi (dia 2&3) = {recall_multi:.4f}")
    print(f"Balanced accuracy = {bacc:.4f}   (all-single baseline = 0.50)")
    print(f"Bootstrap 95% CI  = [{lo:.4f}, {hi:.4f}]")
    print(f"Label-permutation p (one-sided vs 0.50) = {p_perm:.4f}")
    print(f"GATE (balanced acc > 0.50, p < .05): {'PASS' if p_perm < 0.05 else 'FAIL'}")


def main():
    args = sys.argv[1:]
    if args == ["--report"]:
        report(); return
    if len(args) == 3:                                   # single chunk (append)
        dest = CELL5FILE if args[0] == "5" else OUTFILE  # target never enters the gate file
        with open(dest, "a", encoding="utf-8") as out:
            run_range(args[0], int(args[1]), int(args[2]), out)
        return
    # full run: fresh file, the four CALIBRATION cells, then report. Cell 5 is deliberately
    # not in this loop - the target is run explicitly (`run_calibration.py 5 0 600`) so it
    # can never be produced as a side effect of re-running the gate.
    with open(OUTFILE, "w", encoding="utf-8") as out:
        for c in ("1", "2", "3", "4"):
            run_range(c, 0, None, out)
    report()


if __name__ == "__main__":
    main()
