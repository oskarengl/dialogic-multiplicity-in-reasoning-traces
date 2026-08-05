# Method 2 — Internal verification (PAN25 validation split)

**Date:** 2026-07-17  
**Pre-registration commit:** `fba456b`  
**Location:** `methods/2_stylometric_step_change/implementation/`  
**Script:** `internal_validation.py`

## What this checks

Before trusting the shipped SSPC checkpoint on our own 2×2 cells, we check that it behaves sensibly on the official PAN25 multi-author spot-check data (easy / medium / hard validation splits).

**Important:** the published macro-F1 numbers in Schmidt et al. 2025 were obtained on the official **test** split (via TIRA), and the test labels are not public. We only have train + validation locally. This run uses the **validation** split — the best local sanity check available — and compares against the published test numbers only as a rough reference, not as a strict reproduction target.

## Frozen configuration

- Model: SSPC `StyleChangeSequential` checkpoint (`model.ckpt`) over `styledistance` sentence encoder.
- `block_size = 256` (checkpoint default).
- Sentence splitter: **NLTK Punkt**, default parameters (`methods.md` §0).
- Inference output: **mean of raw `sigmoid(logits)` per adjacent sentence pair**, before the shipped 0.5 threshold (`methods.md` §2).
- For this verification we use the **0.5-thresholded binary predictions** to compute macro-F1, because the published score is a binary F1 metric.
- No fine-tuning on our data — out-of-domain checkpoint used as-is.
- Hardware: NVIDIA GeForce RTX 2070 Max-Q (`torch==2.13.0+cu126`).

## Data

- `methods/2_stylometric_step_change/implementation/pan25-data/{easy,medium,hard}/validation/`
- 900 problems per subtask (`.txt` + `truth-*.json`), 2,700 total.

## Command

```bash
cd methods/2_stylometric_step_change/implementation
./venv/Scripts/python.exe internal_validation.py
```

## Output

```
device=cuda  split=validation  max_files=all

Loading weights: 100%|##########| 199/199 [00:00<00:00, 2609.03it/s]

task         n  macro-F1   target (abstract / table)
easy       900    0.9203   0.923 / 0.929
medium     900    0.8275   0.828 / 0.815
hard       900    0.7232   0.724 / 0.731
```

## Interpretation

- **easy:** 0.9203 vs. paper abstract 0.923 / table 0.929 — essentially identical.
- **medium:** 0.8275 vs. paper abstract 0.828 / table 0.815 — right on.
- **hard:** 0.7232 vs. paper abstract 0.724 / table 0.731 — right on.

The checkpoint reproduces the published order (easy > medium > hard) and lands within a few points of the paper numbers on the validation split. This is a pass for internal verification.

## Notes

- The original `internal_validation.py` was written for CPU; a one-line device-handling fix was added so `labels` are moved to CPU before `predict.py`'s `get_predictions`, avoiding a CPU/GPU indexing error. The model code (`predict.py`) itself was not changed.
- CPU inference was ~1 minute per document, which would have made the full 2,700-document run ~45 hours. On the RTX 2070 the full run took a few minutes.
- Because the paper scores are from the test split, a perfect match on validation is neither expected nor required; the point is that the checkpoint is in the right ballpark.
