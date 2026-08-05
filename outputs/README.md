# Outputs

Frozen results. Every number in the paper is computed from the files here.

| Path | Contents |
|---|---|
| `method1/` | Per-document author-count predictions for the four known cells (`calibration_predictions.jsonl`) and the traces (`cell5_predictions.jsonl`), plus a validation report |
| `method2/` | Per-document mean adjacent-pair style-switch probability and sentence-pair count, for the known cells and the traces |
| `method3/` | One `.jsonl` per document per cell, each line an utterance with its CAMS tag. ~2,900 documents across five cells. `reliability/` holds the hand-labelling worksheet, the blind score report, and the disagreement review |
| `placement/` | Where cell ⑤ falls relative to the two AI poles, under the **pre-registered** gate framework — see the warning below |
| `archive_pre_speakerfix/` | Results computed before speaker labels were stripped from the dialogue cells, kept so the fix can be audited |

## `placement/` reports the superseded framework — read this before using it

`placement/cell5_placement.txt` says:

```
M1 style-change (author count)        PASS   ...  monologue-leaning
M2 stylometric step-change            PASS   ...  dialogue-leaning
M3 dialogue-act tagging               FAIL   ...  excluded (kappa = 0.5425 < 0.70)
  SPLIT: M1 monologue-leaning, M2 dialogue-leaning
```

**This is not what the paper reports, and it is not a contradiction.** These files apply the
per-method statistical gates as pre-registered, under which Method 1 passed and Method 3 was
excluded on its κ shortfall. The paper replaces those gates with a single validity check
applied identically to all three methods — sort the four known cells correctly — under which
Method 1 fails and Method 3 passes. The change and the reasons for it are documented in
[`../preregistration/DEVIATIONS.md`](../preregistration/DEVIATIONS.md) and in the paper's §3.

The underlying per-document measurements in `method1/`, `method2/` and `method3/` are the
same either way. Only the pass/fail framing around them differs.

## The margin freeze is worth checking

`placement/margins_frozen.txt` records that the no-clear-margin bands were fixed while no
cell-⑤ results existed on disk:

```
FIREWALL CHECK - cell 5 method outputs present on disk at freeze time:
  outputs/method1/cell5_predictions.jsonl : False
  outputs/method2/cell5_raw_scores.jsonl  : False
```

Frozen 2026-07-22T15:53:42Z, seed `20260722`, B = 1000 per pole. The placement was computed
afterwards, at 18:00:23Z the same day.

## Regenerating

The heavy stages need a GPU, API access, or both, and are not reproducible from this
repository alone — Method 2 needs the 719 MB SSPC checkpoint from upstream, and Method 3
needs API access to Tencent Hunyuan Hy3. The frozen outputs are committed precisely so the
analysis and figures can be re-derived without re-running them:

```bash
python paper/make_fig_grid.py     # Figure 1
python paper/make_fig_split.py    # Figure 2, from outputs/method2/*.jsonl
```

See the per-method `RUN_METHOD*.md` files for the full pipeline.
