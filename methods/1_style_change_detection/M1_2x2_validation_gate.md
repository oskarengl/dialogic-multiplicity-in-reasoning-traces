# Method 1 — 2×2 validation gate

**Date:** 2026-07-17  
**Pre-registration commit:** `8cbdee4`  
**Location:** `methods/1_style_change_detection/implementation/`  
**Script:** `run_calibration.py`

## Gate definition

From `methods.md` §1:

- Balanced accuracy = ½·(recall_single + recall_multi), where
  - `recall_single` is over the pooled monologue cells (① human_monologue, ④ ai_monologue), and
  - `recall_multi` is over the pooled dialogue cells (② human_debate, ③ ai_debate).
- The all-single detector scores exactly 0.50, so passing requires genuine multi-voice detection somewhere.
- Significance: label-permutation null, 10,000 shuffles, one-sided `p < .05`.
- Reported alongside: per-class recalls, per-cell recall breakdown, confusion matrix, and bootstrap 95% CI on balanced accuracy.

## Command

```bash
cd methods/1_style_change_detection/implementation
./venv/Scripts/python.exe run_calibration.py
```

## Output

```
cell 1 (human_monologue) [0:None] n=600 (2s)
cell 2 (human_debate) [0:None] n=500 (0s)
cell 3 (ai_debate) [0:None] n=600 (30s)
cell 4 (ai_monologue) [0:None] n=600 (1s)

cell                 n  correct  recall
human_monologue    600      585   0.975
human_debate       500        0   0.000
ai_debate          600      254   0.423
ai_monologue       600      599   0.998

Confusion (true \ pred):     pred_single  pred_multi
  true_single (mono, 1&4):         1184          16
  true_multi  (dia, 2&3):          846         254

recall_single (mono 1&4) = 0.9867   recall_multi (dia 2&3) = 0.2309
Balanced accuracy = 0.6088   (all-single baseline = 0.50)
Bootstrap 95% CI  = [0.5957, 0.6219]
Label-permutation p (one-sided vs 0.50) = 0.0001
GATE (balanced acc > 0.50, p < .05): PASS
```

## Interpretation

- **Gate: PASS.** Balanced accuracy (0.6088) is significantly above the 0.50 trivial baseline (permutation p = 0.0001), with a bootstrap 95% CI of [0.5957, 0.6219].
- Monologue cells are classified almost perfectly (human 0.975, AI 0.998).
- Multi-voice detection is driven almost entirely by `ai_debate` (recall 0.423).
- `human_debate` has **0/500 recall**: Method 1 labels every human debate transcript as single-author. This is a per-cell failure even though the pooled balanced-accuracy gate clears. It may reflect the human-debate material being short, task-focused, and speaker-identity-stripped, so the function-word window profile does not separate speakers.
- Per the current pre-registration, the method passes the gate and may proceed to the target. Whether a method that fails on one calibration cell should still report on `ai_reasoning` is a separate judgement call.

## Artifacts

- Per-document predictions: `outputs/method1/calibration_predictions.jsonl`
- Re-run the report without recomputing: `./venv/Scripts/python.exe run_calibration.py --report`
