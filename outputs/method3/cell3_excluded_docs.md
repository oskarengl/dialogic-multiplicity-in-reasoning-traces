# Cell③ (ai_debate) re-tag: excluded documents

9 of 600 ai_debate documents could not be tagged by `tencent/hy3` and are excluded from the
cell③ re-tag (591/600 present). Not chunked — see RECLEAN_RUNBOOK.md and STATUS.md for why
chunking was rejected as an option (breaks CAMS's whole-document context requirement).

## Root cause (confirmed via direct API diagnostic)

These documents are debates about arithmetic "make 24" puzzles. `tencent/hy3` is a reasoning
model; on these specific docs its internal reasoning gets pulled into re-solving the embedded
math puzzle itself ("Let's try (12-9)x(10-3)=21, this isn't 24, let's try...") rather than doing
the tagging task, and never converges. Diagnostic on `g24_0130_p1`: `finish_reason: length`,
`reasoning_tokens: 32000` (full budget), `content: None` (never started the actual JSONL answer).

## Retry history (all full-document, temperature 0, no chunking)

1. Original run (--max-tokens 32000 default): 189/600 failed (including these 9).
2. Retry on the 189 (post a mid-run OpenRouter credit exhaustion, confirmed via `402` errors):
   162 succeeded, 27 still failed.
3. Retry on the 27 (--max-tokens 32000): 13 succeeded, 14 still failed.
4. Final retry on the 14, all in parallel, --max-tokens 65536 (2x): 5 succeeded (some of these
   were among the longest docs in the corpus, e.g. 810 tagged sentences), **9 still failed**.

4 real model attempts total for the final 9 (the credit-blocked round doesn't count — it never
reached the model). Per user decision (2026-07-21/22), stopping here and excluding these 9.

## Representativeness caveat

These 9 (and the 5 that eventually succeeded) skew toward the longest/most complex ai_debate
transcripts (12 of the original 14 stuck docs were above the corpus's 90th-percentile length).
The final 9 exclusions are NOT a random ~1.5% loss — they are the hardest, most reasoning-loop-
prone cases. This should be noted in the paper/STATUS.md as a limitation: cell③'s re-tagged
sample slightly under-represents the longest/most circuitous ai_debate transcripts.

Excluded debate_ids: g24_0021_p1, g24_0024_p1, g24_0024_p3, g24_0074_p1, g24_0121_p2,
g24_0130_p1, g24_0139_p3, g24_0148_p1, g24_0180_p2
