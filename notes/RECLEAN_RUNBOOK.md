# Re-clean speaker-label leak + re-run runbook (2026-07)

A condition leak was found in **both dialogue cells** of the 2×2: speaker identifiers survived
preprocessing and act as a shortcut for "this is a dialogue cell." Two data files are fixed and
the affected method outputs must be regenerated. Monologue cells (①④) and the cell⑤ target are
**not affected** — do not touch them (cell⑤ stays frozen).

## What leaked (verified)

| cell | leak | evidence |
|---|---|---|
| ② human_debate | 29 animal pseudonyms (`Guinea pig:` 100% intact; ~1,000 inline refs `@Cat`, `Thanks Bat`, `yes kiwi is right`) | names are the top-1/2/3 most-frequent tokens in every doc |
| ③ ai_debate | 4 role titles (`Critical Analyst` etc., 600+, cell③-only) + capital letter refs (`A's`, `great job, C!`) | role-words in top-50 MFT of 96/200 docs |

Field mapping that matters for the fix (verified in each method's `run_calibration.py`):
- **human_debate** — M1/M2/M3 all read `transcript`.
- **ai_debate** — M1/M2 read `turns[].text_clean`; M3 tagged `full_text_no_labels`. Both cleaned.
  (M1/M2 use `speaker` only for turn boundaries, never injected into the token stream — not a leak.)

## The two cleaners (already written, audited, non-destructive)

- `scripts/refix_human_debate_labels.py` — derives the 29-name set from the data (frequency
  floor = clean cliff), removes case-insensitively as whole words (turn-prefix + inline, trailing
  `:` and leading `@`). Audit: 28,771 removed, **residual 0**, zero content-word false positives.
- `scripts/refix_ai_debate_labels.py` — removes role titles (case-insensitive) + **surgical**
  case-sensitive letter refs (possessive `A's`, vocative `…, D!`, `B said`, `well done, C`);
  never touches bare/lowercase `a`–`d`. Audit: 3,141 removed, **residual 0**, zero article-`A`
  false positives. Cleans `full_text_no_labels` + `turns[].text_clean/raw` + `labeled_turns[].text`.

Run either without `--commit` to re-print its audit. Preview files
(`*.REFIX_PREVIEW.jsonl`) are already written for inspection.

---

## Runbook (run in order)

### Phase 0 — commit the data fixes  *(fast, no LLM; reversible via git)*
```bash
cd "C:/bachelor research/.1 recent approach"
python scripts/refix_human_debate_labels.py --commit    # -> processed_human_debate.jsonl
python scripts/refix_ai_debate_labels.py   --commit    # -> processed_ai_debate.jsonl
# each prints residual checks — confirm all are 0 before continuing
rm data/00_core-2x2/human_debate/processed_human_debate.REFIX_PREVIEW.jsonl
rm data/00_core-2x2/ai_debate/processed_ai_debate.REFIX_PREVIEW.jsonl
git add -A && git commit -m "Fix speaker-label leak in human_debate + ai_debate (see RECLEAN_RUNBOOK.md)"
```

### Phase 1 — Method 3 re-tag **cell② + cell③ only**  *(LLM calls)*
Use the **same model + prompt** as the original tagging run (temperature 0). The original
command is in `outputs/method3/run.log` if you need to confirm the model id.
```bash
cd methods/3_dialogue_act_tagging/implementation
# clear stale per-doc outputs so nothing lingers from the dirty run
rm -f ../../../outputs/method3/cell2_human_debate/*.jsonl
rm -f ../../../outputs/method3/cell3_ai_debate/*.jsonl

# cell② human_debate  (field: transcript)
python label_dialogue_acts_v2.py \
  --input ../../../data/00_core-2x2/human_debate/processed_human_debate.jsonl \
  --output ../../../outputs/method3/cell2_human_debate \
  --prompt ../CAMS_LLM_labeling_prompt.txt --model <SAME_MODEL> --cell 2 --text-field transcript

# cell③ ai_debate  (field: full_text_no_labels)
python label_dialogue_acts_v2.py \
  --input ../../../data/00_core-2x2/ai_debate/processed_ai_debate.jsonl \
  --output ../../../outputs/method3/cell3_ai_debate \
  --prompt ../CAMS_LLM_labeling_prompt.txt --model <SAME_MODEL> --cell 3 --text-field full_text_no_labels
```
**Do NOT re-tag cell①, cell④, or cell⑤.** cell⑤ is the frozen target; the others have no leak.

### Phase 2 — Method 3 downstream  *(no LLM)*
```bash
cd methods/3_dialogue_act_tagging/implementation
rm -rf ../../../outputs/method3/_tag_cache      # force signals to reparse the new tags
python run_calibration.py                        # recompute the §3c completion-rate gate
python reliability_sample.py --plan              # n re-solved from new cell②/③ marginals
python reliability_sample.py --sample            # fresh blind worksheet from clean tags
cd ../labeling_tool
python label_server.py --make-practice 200       # fresh practice set (disjoint from new worksheet)
```
The worksheet was **0/510 labeled**, so nothing hand-labeled is lost. **Watch:** if the
completion-rate δ (was 0.438) drops after re-tag, that means the dialogue signal was partly
leak-driven — a real finding, not a bug. It must still clear δ ≥ 0.33 to pass.

### Phase 3 — Method 1 re-run  *(no LLM)*
```bash
cd methods/1_style_change_detection/implementation
python run_calibration.py            # re-infer all 4 cells on cleaned data + gate
python run_calibration.py --report
```
The PAN19 source-reproduction step is unaffected — skip it. **Watch:** balanced accuracy may
move (human_debate/ai_debate features change); human_debate was already 0/500.

### Phase 4 — Method 2  *(first run; just run on clean data)*
```bash
cd methods/2_stylometric_step_change/implementation
./venv/Scripts/python.exe run_calibration.py
./venv/Scripts/python.exe run_calibration.py --report
```
Never ran before, so no rework — it simply reads the now-clean data.

### Phase 5 — log it
Add a dated entry to `STATUS.md` recording the leak, the fix, and the re-run results once the
gates re-report (template already stubbed there under the 2026-07 entry).

---

## Order & dependency summary
```
Phase 0 (data)  ──►  Phase 1 (M3 re-tag ②③, LLM)  ──►  Phase 2 (M3 gate + worksheet)
             └─────►  Phase 3 (M1 re-run)
             └─────►  Phase 4 (M2 first run)
```
Phases 3 and 4 depend only on Phase 0 and can run in parallel with Phase 1/2.
```
```
