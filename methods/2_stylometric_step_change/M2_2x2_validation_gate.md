# Method 2 — 2×2 validation gate

**Date:** 2026-07-17  
**Pre-registration commit:** `fba456b`  
**Location:** `methods/2_stylometric_step_change/implementation/`  
**Script:** `run_calibration.py`

## Gate definition

From `methods.md` §2:

- For every calibration document, split the text into sentences with NLTK Punkt, run the SSPC checkpoint, and take the **mean raw `sigmoid(logit)` per adjacent sentence pair** (before the checkpoint's 0.5 threshold).
- Fit a length curve for each AI pole separately, using only that pole's own documents:
  - `ai_debate` (③) = dialogue pole
  - `ai_monologue` (④) = monologue pole
- Candidate forms: raw-linear (`probability ~ pairs`), semi-log (`probability ~ log(pairs)`), log-log (`log(probability + ε) ~ log(pairs)`, `ε = 0.001`).
- Select the form that minimizes AIC **on a common scale** (RSS in original probability units) so the three response transformations are comparable.
- Per document: `d_dia = raw − curve_dia(pairs)`, `d_mono = raw − curve_mono(pairs)`, and `lean = |d_mono| − |d_dia|` (positive = closer to the dialogue curve).
- **Gate:** mean `lean` for the dialogue cells (② human_debate, ③ ai_debate) must exceed mean `lean` for the monologue cells (① human_monologue, ④ ai_monologue), and Cliff's δ between the two groups must be ≥ 0.33.

## Command

```bash
cd methods/2_stylometric_step_change/implementation
./venv/Scripts/python.exe run_calibration.py
```

## Output

```
cell 1 (human_monologue) [0:None] n=600 (34s)
cell 2 (human_debate) [0:None] n=500 (93s)
cell 3 (ai_debate) [0:None] n=600 (655s)
cell 4 (ai_monologue) [0:None] n=600 (124s)

pole ai_debate  (3, dialogue)  form = semilog  AIC {'linear': -4670.2, 'semilog': -4744.8, 'loglog': -4739.3}
pole ai_monolog (4, monologue) form = semilog  AIC {'linear': -2743.8, 'semilog': -2762.9, 'loglog': -2657.8}

cell                 n  mean_raw  mean_lean
human_monologue    559    0.0269    -0.0133
human_debate       497    0.0746     0.0041
ai_debate          600    0.0394     0.0185
ai_monologue       559    0.0618    -0.0060

mean lean  dialogue (2,3) = 0.0120   monologue (1,4) = -0.0097
Cliff's delta (dialogue vs monologue) = 0.6300   (gate threshold >= 0.33)
direction (dia > mono): True
[85 documents had < 2 sentences and were excluded]
GATE (direction AND delta >= 0.33): PASS
```

## Interpretation

- **Gate: PASS.** The dialogue cells have a higher mean `lean` than the monologue cells (0.0120 vs. −0.0097), and the effect size is large (Cliff's δ = 0.6300), well above the 0.33 floor.
- The `lean` sign pattern is correct: both monologue cells are negative, both dialogue cells are positive.
- **Length confound is real.** Without the length curves, `ai_monologue` actually has a higher raw mean switch probability (0.0618) than `ai_debate` (0.0394) — because `ai_monologue` documents are longer and accumulate more pairs. The residual `lean` corrects this and places the monologue pole below the dialogue pole.
- Both AI poles selected the **semi-log** form (`probability ~ log(pairs)`), suggesting that per-pair switch probability declines with the logarithm of document length.
- 85 documents (41 in human_monologue, 3 in human_debate, 41 in ai_monologue) had fewer than two sentences after NLTK splitting and were excluded from the fit/gate. Inspection of every excluded document confirmed each has exactly one sentence; they are not failed runs, just cases where the per-pair score is undefined by construction.

## Implementation notes

- Long documents in `ai_debate` (up to ~800 sentences) caused CUDA OOM when processed in one forward pass. `run_calibration.py` was updated to process such documents in **overlapping 64-sentence chunks** (stride 63, so chunks share one sentence and all adjacent pairs remain covered). This is a memory-safety approximation, not a modeling change, and is only triggered when a document exceeds 64 sentences. The pre-registered per-document mean and gate logic are unchanged.
- AIC selection across linear / semi-log / log-log uses a common original-scale RSS because the response variable is transformed; this is the only valid way to compare AICs across the three forms.

## Artifacts

- Per-document raw scores: `outputs/method2/calibration_raw_scores.jsonl`
- Re-run the report without recomputing: `./venv/Scripts/python.exe run_calibration.py --report`
