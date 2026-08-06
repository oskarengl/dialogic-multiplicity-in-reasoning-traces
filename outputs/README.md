# Outputs

Frozen results. The numbers in the paper are computed from these files.

| Path | Contents |
|---|---|
| `method1/` | Per-document author-count predictions for the four known cells (`calibration_predictions.jsonl`) and the traces (`cell5_predictions.jsonl`), plus a validation report |
| `method2/` | Per-document mean adjacent-pair style-switch probability and sentence-pair count, for the known cells and the traces |
| `method3/` | One `.jsonl` per document per cell, each line an utterance with its CAMS tag. `reliability/` holds the hand-labelling worksheet, the score report, and the disagreement review |
| `placement/` | Cell ⑤ relative to the two AI poles, under the pre-registered gates |

## `placement/` uses the pre-registered gates

`placement/cell5_placement.txt` reports:

```
M1 style-change (author count)        PASS   ...  monologue-leaning
M2 stylometric step-change            PASS   ...  dialogue-leaning
M3 dialogue-act tagging               FAIL   ...  excluded (kappa = 0.5425 < 0.70)
  SPLIT: M1 monologue-leaning, M2 dialogue-leaning
```

These files apply the per-method gates as pre-registered, under which Method 1 passed and
Method 3 was excluded. The paper applies a single validity check to all three methods
instead, under which Method 1 fails and Method 3 passes. See
[`../preregistration/METHOD_SELECTION.md`](../preregistration/METHOD_SELECTION.md) and the paper's §3.

The per-document measurements in `method1/`, `method2/` and `method3/` are the same under
either framing.

## Margin freeze

`placement/margins_frozen.txt` records that the no-clear-margin bands were fixed while no
cell-⑤ results existed on disk:

```
FIREWALL CHECK - cell 5 method outputs present on disk at freeze time:
  outputs/method1/cell5_predictions.jsonl : False
  outputs/method2/cell5_raw_scores.jsonl  : False
```

Frozen 2026-07-22T15:53:42Z, seed `20260722`, B = 1000 per pole. The placement was computed
at 18:00:23Z the same day.

## Regenerating

```bash
python paper/make_fig_grid.py     # Figure 1
python paper/make_fig_split.py    # Figure 2, from outputs/method2/*.jsonl
```

See the per-method `RUN_METHOD*.md` files for the full pipeline.
