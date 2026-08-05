# Local additions to the SSPC implementation

Method 2 runs the PAN 2025 Sequential Sentence Pair Classifier by Schmidt et al., pinned as
a submodule at `../implementation` (upstream:
https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis, commit
`0f48051`).

Upstream is used **unmodified** — there is no patch to apply. What lives here are the two
driver scripts written for this study, which upstream does not provide.

## Applying

```bash
git submodule update --init methods/2_stylometric_step_change/implementation
cd methods/2_stylometric_step_change/implementation
cp ../local_changes/run_calibration.py ../local_changes/internal_validation.py .
```

Both scripts import upstream's `predict.py` and expect to be run from inside
`implementation/`.

## Scripts

| File | Purpose |
|---|---|
| `run_calibration.py` | Splits each document into sentences with NLTK Punkt, runs the SSPC checkpoint, and records the per-document mean raw adjacent-pair probability together with the sentence-pair count. Writes `outputs/method2/calibration_raw_scores.jsonl`. |
| `internal_validation.py` | Checks the shipped checkpoint against the published PAN 2025 macro-F1 before it is trusted on our own cells — the analogue of Method 1's PAN 2019 reproduction. |

## Two things to know

**The checkpoint is not in this repository.** `model.ckpt` is 719 MB and belongs to
upstream. Fetch it from the upstream repository's release before running either script.

**`run_calibration.py --report` implements the original pre-registered gate**, which
selected a length curve per AI pole and required Cliff's delta ≥ 0.33 between dialogue and
monologue cells. The paper does not use that gate; see
[`../../../preregistration/DEVIATIONS.md`](../../../preregistration/DEVIATIONS.md). The
inference phase, which produces the raw scores every reported Method 2 number is computed
from, is unaffected by that change.
