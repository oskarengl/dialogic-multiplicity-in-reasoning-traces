# Local additions to the SSPC implementation

Method 2 runs the PAN 2025 Sequential Sentence Pair Classifier by Schmidt et al., pinned as
a submodule at `../implementation` (upstream:
https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis, commit
`0f48051`).

Upstream is used unmodified. There is no patch to apply. The two driver scripts here were
written for this study.

## Applying

```bash
git submodule update --init methods/2_stylometric_step_change/implementation
cd methods/2_stylometric_step_change/implementation
cp ../local_changes/run_calibration.py ../local_changes/internal_validation.py .
```

Both scripts import upstream's `predict.py` and are run from inside `implementation/`.

## Scripts

| File | Purpose |
|---|---|
| `run_calibration.py` | Splits each document into sentences with NLTK Punkt, runs the SSPC checkpoint, and records the per-document mean raw adjacent-pair probability with the sentence-pair count. Writes `outputs/method2/calibration_raw_scores.jsonl`. |
| `internal_validation.py` | Checks the shipped checkpoint against the published PAN 2025 macro-F1 before it is used on the study's own cells. |

## Notes

`model.ckpt` (719 MB) belongs to upstream and is not in this repository. Fetch it from the
upstream repository before running either script.

`run_calibration.py --report` implements the original pre-registered gate, which selected a
length curve per AI pole and required Cliff's δ ≥ 0.33 between dialogue and monologue cells.
The paper does not use that gate; see
[`../../../preregistration/DEVIATIONS.md`](../../../preregistration/DEVIATIONS.md). The
inference phase, which produces the raw scores the reported Method 2 numbers are computed
from, is unaffected.
