# Running Method 2 (sentence-level style-change detection) yourself

Same two steps as Method 1: (1) internal validation — confirm the shipped SSPC
checkpoint reproduces its published PAN25 macro-F1 — then (2) run the frozen method on
the four calibration cells and apply the gate. Both are plain scripts in
`implementation/`; nothing runs in the background.

Run everything **from inside `implementation/`**, using the method's venv (which already
has torch / transformers / lightning / tira):

```bash
cd methods/2_stylometric_step_change/implementation
# (once) make sure NLTK Punkt is present in that venv:
./venv/Scripts/python.exe -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

## 1. Internal validation on PAN25 (`internal_validation.py`)

Confirms our copy of the checkpoint reproduces the published SSPC numbers before we trust
it on our own data.

```bash
./venv/Scripts/python.exe internal_validation.py               # full validation split
./venv/Scripts/python.exe internal_validation.py --max-files 50   # quick CPU-friendly sample
```

Expected (target: Schmidt et al. 2025, SSPC — macro-F1 per subtask):

| subtask | abstract | results table |
|---|---|---|
| easy   | 0.923 | 0.929 |
| medium | 0.828 | 0.815 |
| hard   | 0.724 | 0.731 |

The hard score differs between the paper's abstract and its results table (logged in
`STATUS.md`); a reproduction within a couple of points of these is a pass. On CPU the full
split is slow — use `--max-files` for a first check, or run on GPU for the full number.

## 2. Calibration cells + gate (`run_calibration.py`)

Two phases in one command:

```bash
./venv/Scripts/python.exe run_calibration.py         # infer on all 4 cells, then report the gate
```

**Phase 1 (inference):** each document is split into sentences with NLTK Punkt, run through
the SSPC checkpoint, and reduced to the **mean of the raw per-adjacent-pair probabilities**
`sigmoid(logits)` — the continuous score *before* the shipped 0.5 threshold, as methods.md §2
requires. Per-document `(raw_score, n_pairs)` are written to
`outputs/method2/calibration_raw_scores.jsonl`.

**Phase 2 (fit + gate):** each AI pole gets its own length curve of raw score vs. sentence
pairs — `ai_debate` (dialogue) and `ai_monologue` (monologue) — chosen among linear / semi-log
/ log-log by AIC, independently per pole. Then per document `d_dia = raw − curve3(pairs)`,
`d_mono = raw − curve4(pairs)`, and `lean = |d_mono| − |d_dia|`.

**Gate (methods.md §2):** mean `lean` over the dialogue cells (②③) exceeds mean `lean` over the
monologue cells (①④), **and** Cliff's δ between the two groups **≥ 0.33**. The report prints
the chosen curve form + AIC per pole, per-cell mean raw score and mean lean, the two group
means, Cliff's δ, and PASS/FAIL.

Re-print the gate without re-inferring:

```bash
./venv/Scripts/python.exe run_calibration.py --report
```

Inference is the slow part; if interrupted, resume by index range (scores append), e.g.
`./venv/Scripts/python.exe run_calibration.py 3 200 400`, then `--report`.

Check the fit/gate math on synthetic data without loading the model:

```bash
./venv/Scripts/python.exe run_calibration.py --selftest
```

## Decisions baked in (all per the frozen spec)

- **Raw sigmoid, not thresholded.** We read `sigmoid(logits)` per adjacent pair and average,
  rather than the shipped binary decision (methods.md §2).
- **Per-pole length curves.** Each pole is fit on its own documents only; the two poles may
  land on different functional forms. `lean = |d_mono| − |d_dia|` places a document by which
  pole's curve it sits closer to — the same nearest-pole idea as Method 3 §3d.
- **AIC on a common scale (refinement worth logging).** The three candidate forms use
  different response scales (`y` vs `log y`), so AICs on each form's own scale are not
  comparable. The script scores every candidate by residual sum of squares in the *original*
  score units (back-transforming the log-log prediction) and selects on that common scale.
  This precisifies methods.md's "minimizes AIC" wording — worth a one-line `STATUS.md` note.
- **Sentences:** NLTK Punkt, default parameters (methods.md §0). Debate cells are fed as their
  turns concatenated in order, then Punkt-split, so the model discovers changes without being
  told the turn boundaries. Documents with fewer than 2 sentences (0 pairs) have no defined
  score and are excluded from the fit and gate; their count is reported.

## Files

- `implementation/internal_validation.py` — PAN25 macro-F1 reproduction
- `implementation/run_calibration.py` — calibration-cell inference + length-adjusted gate
- `implementation/predict.py` — the shipped SSPC model (unchanged)
- outputs → `outputs/method2/calibration_raw_scores.jsonl`
