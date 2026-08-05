#!/usr/bin/env python3
"""Method 2 - 2x2 validation gate (frozen spec, methods.md sec. 2).

Two phases:

(1) INFERENCE. For each calibration cell, split each document into sentences with
    NLTK Punkt, run the shipped SSPC checkpoint, take the RAW per-adjacent-pair
    probabilities sigmoid(logits) (before any 0.5 thresholding), and record the
    per-document MEAN raw score plus the number of sentence pairs (the length
    covariate). Writes outputs/method2/calibration_raw_scores.jsonl.

(2) --report. Fit each AI pole its OWN length curve of raw score vs sentence pairs
    - ai_debate (3) = dialogue pole, ai_monologue (4) = monologue pole - choosing
    among linear / semi-log / log-log by AIC, independently per pole. Then, per
    document, d_dia = raw - curve3(pairs), d_mono = raw - curve4(pairs), and
    lean = |d_mono| - |d_dia| (positive = closer to the dialogue curve). Gate:
    mean lean over dialogue cells (2,3) exceeds mean lean over monologue cells
    (1,4), AND Cliff's delta between the two groups >= 0.33.

Note on AIC across transforms: the three candidate forms use different response
scales (y vs log y), so AICs computed on each form's own scale are NOT comparable.
We therefore score every candidate by its residual sum of squares in the ORIGINAL
score units (back-transforming the log-log fit's predictions) and select on that
common scale. This is a precisification of methods.md's "minimizes AIC" wording;
worth a one-line STATUS.md note.

Torch is imported lazily, so --report and --selftest need only numpy.

Run from implementation/:
    python run_calibration.py                  # inference on all 4 cells, then report
    python run_calibration.py CELL START END   # inference on one index range (resumable)
    python run_calibration.py --report         # recompute fit + gate from saved scores
    python run_calibration.py --selftest       # check the fit/Cliff/gate math (no torch)
"""
import os, sys, json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
DATA = ROOT / "data"
OUTDIR = ROOT / "outputs" / "method2"; OUTDIR.mkdir(parents=True, exist_ok=True)
OUTFILE = OUTDIR / "calibration_raw_scores.jsonl"
LABEL = {"1": "human_monologue", "2": "human_debate", "3": "ai_debate", "4": "ai_monologue",
         "5": "ai_reasoning"}
CELL5FILE = OUTDIR / "cell5_raw_scores.jsonl"


def _prose(r, f): return r.get(f, "") or ""
def _turns(r, _=None):
    return " ".join(t.get("text_clean", "").strip()
                    for t in r.get("turns", []) if t.get("text_clean", "").strip())


# cell -> (file, text-builder, true_bin)   true_bin: 1 = single (mono), 0 = multi (dia)
CELLS = {
    "1": (DATA / "human_monologue" / "human_think_aloud_600.jsonl", lambda r: _prose(r, "think_trace"), 1),
    "2": (DATA / "human_debate" / "processed_human_debate.jsonl",
          lambda r: _prose(r, "transcript"), 0),
    "3": (DATA / "ai_debate" / "processed_ai_debate.jsonl", _turns, 0),
    "4": (DATA / "ai_monologue" / "processed_prompted_ai_monologue.jsonl",
          lambda r: _prose(r, "transcript"), 1),
    # --- Step 2 target, added 2026-07-22 after the gate passed (methods.md sec. 4). ---
    # Data path only: the builder is byte-identical to cell 1's (continuous prose in
    # "think_trace"). true_bin is None - the target has no ground-truth label, it is placed,
    # not scored. Cell 5 scores go to a SEPARATE file so calibration_raw_scores.jsonl, the
    # fitted pole curves, and the frozen gate (Cliff's delta 0.6211) cannot be altered by
    # running the target.
    "5": (DATA / "ai_reasoning" / "processed_native_reasoning_traces.jsonl",
          lambda r: _prose(r, "think_trace"), None),
}


# ----------------------------- phase 1: inference -----------------------------
def infer_range(cell, start, end, out):
    import time, nltk, pandas as pd, torch
    from transformers import AutoTokenizer
    from predict import (StyleChangeSequential, StyleChangeSequentialDataset,
                         collate_sequential_batch)
    for res in ("tokenizers/punkt", "tokenizers/punkt_tab"):
        try:
            nltk.data.find(res)
        except LookupError:
            nltk.download(res.split("/")[-1], quiet=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(HERE / "model.ckpt", map_location=device)
    ckpt["hyper_parameters"]["model_name_or_path"] = str(HERE / "styledistance")
    model = StyleChangeSequential(**ckpt["hyper_parameters"])
    model.load_state_dict(ckpt["state_dict"])
    model.to(device); model.eval()
    tok = AutoTokenizer.from_pretrained(str(HERE / "styledistance"))

    path, build, tb = CELLS[cell]
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()][start:end]
    t0 = time.time(); n = len(recs)
    with torch.no_grad():
        for i, rec in enumerate(recs):
            if i == 1 or (i + 1) % 10 == 0 or i == n - 1:
                print(f"  progress: {i+1}/{n}", flush=True)
            sents = [s for s in nltk.sent_tokenize(build(rec)) if s.strip()]
            n_pairs = len(sents) - 1
            raw = None
            if n_pairs >= 1:
                MAX_SENTS = 64  # chunk long docs to avoid GPU OOM
                all_probs = []
                for cstart in range(0, len(sents), MAX_SENTS - 1):
                    chunk = sents[cstart:cstart + MAX_SENTS]
                    if len(chunk) < 2:
                        break
                    df = pd.DataFrame([{"sentences": chunk, "changes": None,
                                        "num_sentences": len(chunk), "problem_id": "p-0"}])
                    ds = StyleChangeSequentialDataset(dataframe=df, tokenizer=tok)
                    b = collate_sequential_batch([ds[0]])
                    logits = model.forward(input_ids=b["input_ids"], attention_mask=b["attention_mask"])
                    probs = torch.sigmoid(logits.detach().cpu()).numpy().ravel()[:len(chunk) - 1]
                    all_probs.extend(probs.tolist())
                raw = float(np.mean(all_probs)) if all_probs else None
            out.write(json.dumps({"cell": cell, "idx": start + i, "true_bin": tb,
                                  "raw": raw, "n_pairs": n_pairs}) + "\n")
            out.flush()
    print(f"cell {cell} ({LABEL[cell]}) [{start}:{end}] n={len(recs)} ({time.time()-t0:.0f}s)")


# ----------------------------- phase 2: fit + gate -----------------------------
def fit_pole(pairs, scores):
    """Fit linear / semi-log / log-log; select by RSS in original score units (AIC,
    common scale). Returns (best_name, aic_dict, predict_fn)."""
    x = np.asarray(pairs, float); y = np.asarray(scores, float); eps = 1e-3
    lx = np.log(x)

    def ols(col, resp):
        A = np.vstack([np.ones_like(col), col]).T
        c, *_ = np.linalg.lstsq(A, resp, rcond=None)
        return c

    cands = {}
    c = ols(x, y);              cands["linear"]  = (c, lambda xx, c=c: c[0] + c[1] * xx)
    c = ols(lx, y);             cands["semilog"] = (c, lambda xx, c=c: c[0] + c[1] * np.log(xx))
    c = ols(lx, np.log(y + eps)); cands["loglog"] = (c, lambda xx, c=c: np.exp(c[0] + c[1] * np.log(xx)) - eps)

    n = len(y); aic = {}
    for name, (c, fn) in cands.items():
        rss = float(np.sum((y - fn(x)) ** 2))            # original-scale residuals
        aic[name] = n * math.log(rss / n + 1e-12) + 2 * 2
    best = min(aic, key=aic.get)
    return best, aic, cands[best][1]


def cliffs_delta(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    gt = int((a[:, None] > b[None, :]).sum())
    lt = int((a[:, None] < b[None, :]).sum())
    return (gt - lt) / (len(a) * len(b))


def report():
    rows = [json.loads(l) for l in open(OUTFILE, encoding="utf-8") if l.strip()]
    usable = [r for r in rows if r.get("raw") is not None]
    dropped = len(rows) - len(usable)
    if not usable:
        print("No usable scores yet."); return

    def arr(cell, key):
        return np.array([r[key] for r in usable if r["cell"] == cell], float)

    b3, aic3, f3 = fit_pole(arr("3", "n_pairs"), arr("3", "raw"))
    b4, aic4, f4 = fit_pole(arr("4", "n_pairs"), arr("4", "raw"))
    print(f"pole ai_debate  (3, dialogue)  form = {b3:8s} AIC "
          f"{ {k: round(v,1) for k,v in aic3.items()} }")
    print(f"pole ai_monolog (4, monologue) form = {b4:8s} AIC "
          f"{ {k: round(v,1) for k,v in aic4.items()} }")

    for r in usable:
        d_dia = r["raw"] - float(f3(r["n_pairs"]))
        d_mono = r["raw"] - float(f4(r["n_pairs"]))
        r["lean"] = abs(d_mono) - abs(d_dia)

    print(f"\n{'cell':16s} {'n':>5s} {'mean_raw':>9s} {'mean_lean':>10s}")
    for c in ("1", "2", "3", "4"):
        rc = [r for r in usable if r["cell"] == c]
        if not rc: continue
        mr = np.mean([r["raw"] for r in rc]); ml = np.mean([r["lean"] for r in rc])
        print(f"{LABEL[c]:16s} {len(rc):>5d} {mr:>9.4f} {ml:>10.4f}")

    dia = np.array([r["lean"] for r in usable if r["cell"] in ("2", "3")])
    mono = np.array([r["lean"] for r in usable if r["cell"] in ("1", "4")])
    md, mm = dia.mean(), mono.mean()
    delta = cliffs_delta(dia, mono)
    direction = md > mm
    print(f"\nmean lean  dialogue (2,3) = {md:.4f}   monologue (1,4) = {mm:.4f}")
    print(f"Cliff's delta (dialogue vs monologue) = {delta:.4f}   (gate threshold >= 0.33)")
    print(f"direction (dia > mono): {direction}")
    if dropped:
        print(f"[{dropped} documents had < 2 sentences and were excluded]")
    print(f"GATE (direction AND delta >= 0.33): "
          f"{'PASS' if (direction and delta >= 0.33) else 'FAIL'}")


# ----------------------------- selftest (no torch) -----------------------------
def selftest():
    rng = np.random.default_rng(0)
    # synthetic: dialogue docs sit above the dialogue curve, monologue below; both
    # decay with length. Gate should PASS with positive Cliff's delta.
    def make(n, base, slope, noise, cell, tb):
        pairs = rng.integers(5, 200, n)
        raw = np.clip(base + slope * np.log(pairs) + rng.normal(0, noise, n), 0, 1)
        return [{"cell": cell, "true_bin": tb, "raw": float(r), "n_pairs": int(p)}
                for r, p in zip(raw, pairs)]
    rows = (make(300, 0.55, -0.03, 0.03, "3", 0) + make(300, 0.10, -0.01, 0.03, "4", 1)
            + make(250, 0.50, -0.03, 0.05, "2", 0) + make(250, 0.12, -0.01, 0.03, "1", 1))
    with open(OUTFILE, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    print("[selftest] wrote synthetic scores; expect GATE PASS, delta > 0.33\n")
    report()


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        selftest(); return
    if args == ["--report"]:
        report(); return
    if len(args) == 3:                                   # single chunk (append)
        dest = CELL5FILE if args[0] == "5" else OUTFILE  # target never enters the gate file
        with open(dest, "a", encoding="utf-8") as out:
            infer_range(args[0], int(args[1]), int(args[2]), out)
        return
    # full run: fresh file, the four CALIBRATION cells, then report. Cell 5 is deliberately
    # not in this loop - the target is run explicitly (`run_calibration.py 5 0 600`) so it
    # can never be produced as a side effect of re-running the gate.
    with open(OUTFILE, "w", encoding="utf-8") as out:
        for c in ("1", "2", "3", "4"):
            infer_range(c, 0, None, out)
    report()


if __name__ == "__main__":
    main()
