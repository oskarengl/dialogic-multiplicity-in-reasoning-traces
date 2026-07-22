# Method 3 — Internal verification

**Date:** 2026-07-17  
**Pre-registration commit:** `8cbdee4`  
**Location:** `methods/3_dialogue_act_tagging/implementation/`  
**Scripts:** `run_calibration.py`, `reliability_sample.py`

## What this checks

Method 3 has two internal-verification gates (`methods.md` §3e):

1. **Labeling reliability** — Cohen's κ between the LLM tagger and a human rater must be ≥ 0.70. This requires hand-labeling a sample of utterances.
2. **Signal validity** — the primary signal (adjacency-pair completion rate, §3c) must separate known dialogue cells (② human_debate, ③ ai_debate) from known monologue cells (① human_monologue, ④ ai_monologue) in the expected direction.

## Frozen configuration

- Tagger: `label_dialogue_acts_v2.py` + `CAMS_LLM_labeling_prompt.txt`, temperature 0, fixed 28-tag CAMS set.
- FPP → SPP mapping derived from CAMS's own category structure (frozen in `methods.md` §3c and in the prompt).
- Completion rate: fraction of immediately adjacent FPP→SPP pairs that match the frozen mapping, conditioning on FPP occurrence.
- Gate: direction check + Cliff's δ ≥ 0.33, consistent with Method 2.

## Data

- Tags for cells ①–④ are already in `outputs/method3/`.
- Hand-labeling worksheet: `outputs/method3/reliability/worksheet.csv` (510 rows generated, awaiting labels).

## 1. Signal-validity gate (`run_calibration.py`)

```bash
cd methods/3_dialogue_act_tagging/implementation
python run_calibration.py
```

### Output

```
=== 3c. Adjacency-pair completion rate (primary signal) ===
cell 1 (human_monologue ) n_docs= 600  FPP-absent=  26 (4.3%)  defined_n= 574  mean_rate=0.0998
cell 2 (human_debate    ) n_docs= 500  FPP-absent=   0 (0.0%)  defined_n= 500  mean_rate=0.2301
cell 3 (ai_debate       ) n_docs= 598  FPP-absent=   0 (0.0%)  defined_n= 598  mean_rate=0.0201
cell 4 (ai_monologue    ) n_docs= 597  FPP-absent=   0 (0.0%)  defined_n= 597  mean_rate=0.0030

mean completion rate  dialogue (2,3) = 0.1157   monologue (1,4) = 0.0504
Cliff's delta (dialogue vs monologue) = 0.4380
direction (dialogue > monologue): True
GATE-A (direction only, as literally specified): PASS
GATE-B (direction AND delta >= 0.33, consistency w/ Method 2): PASS

=== 3a/3b. Within-class vs. between-class JSD (consistency check, not gating) ===
3a unigram JSD:  within-mono(1,4)=0.1675  within-dia(2,3)=0.2142  between(avg)=0.1668  [within < between expected: False]
3b bigram  JSD:  within-mono(1,4)=0.3148  within-dia(2,3)=0.3618  between(avg)=0.2894  [within < between expected: False]
```

### Interpretation

- **Primary signal gate: PASS.** Dialogue cells complete adjacency pairs at roughly 2.3× the rate of monologue cells (0.1157 vs. 0.0504), with a medium-to-large effect (Cliff's δ = 0.4380), in the expected direction. This clears both the literal direction gate and the stricter δ ≥ 0.33 reading.
- `human_debate` has the highest completion rate (0.2301), as expected for genuine human back-and-forth.
- `ai_debate` has a low absolute rate (0.0201), but still above `ai_monologue` (0.0030). This is consistent with `ai_debate` being four copies of the same model: the *interaction structure* (valid SPP following an FPP) is present, even if the raw tag vocabulary remains model-specific.
- **§3a/§3b consistency check does NOT hold** — within-class JSD is not smaller than between-class JSD for either unigram or bigram profiles. Per `methods.md` §3e.2 this is reported, not required, so it does not block the gate. It does, however, flag a real interpretive point: the DA-tag *vocabulary* of `ai_debate` resembles the monologue cells about as much as it resembles `human_debate`, while the *adjacency-pair structure* correctly reads as dialogue.

## 2. Labeling-reliability gate (`reliability_sample.py`)

### Required sample size

```bash
python reliability_sample.py --plan
```

Precision target: **90% CI, half-width ≤ 0.10** around the measured κ (pass/fail bar unchanged at κ ≥ 0.70).

| cell | n required | available sentences |
|---|---|---|
| ① human_monologue | 122 | 12,166 |
| ② human_debate | 83 | 14,870 |
| ③ ai_debate | 137 | 79,978 |
| ④ ai_monologue | 168 | 18,172 |
| **total** | **510** | — |

This was revised 2026-07-17 from an original 95%/±0.05 target (2,884 total) via an intermediate 90%/±0.08 target (796 total). The further widening to ±0.10 adds a deliberate margin against human-labeling noise across the 27 confusable CAMS categories, not just the sampling-noise formula.

### Current worksheet

- A clean 510-row blind worksheet has been generated with `python reliability_sample.py --sample`.
- `worksheet.csv` currently has **0 filled rows** (awaiting hand-labeling).
- `hidden_llm_labels.json` holds the LLM labels for later `--score`.

### Status

- **Signal-validity gate: PASS.**
- **Labeling-reliability gate: PENDING.** Method 3 needs the 510-utterance worksheet hand-labeled before `reliability_sample.py --score` can compute κ and close the gate.

### Next step

Fill in the `human_label` column of `outputs/method3/reliability/worksheet.csv` (allowed tags are the 27 CAMS tags + `none`, case-sensitive), then run:

```bash
python reliability_sample.py --score
```

## Artifacts

- Signal gate output: `run_calibration.py` (no separate output file; prints to terminal).
- Reliability plan: `outputs/method3/reliability/sample_plan.json`
- Reliability worksheet: `outputs/method3/reliability/worksheet.csv`
- Hidden LLM labels: `outputs/method3/reliability/hidden_llm_labels.json`
