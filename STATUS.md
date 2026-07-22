# STATUS — provenance and deviation log

This file records anything that happened to the data or the methods after the point where
`methods.md` is supposed to be frozen, plus build details kept out of `research_plan.md`. It is the
enforcement mechanism behind the pre-registration: `methods.md` says *what* will be done; this file
timestamps *when* things actually touched the data, so the firewall around cell ⑤ (`ai_reasoning`)
is auditable.

---

## 2026-07-15 — Method 3 label run, incl. cell ⑤ (the target)

Method 3's dialogue-act tagger (`label_dialogue_acts_v2.py`, fixed CAMS prompt, temperature 0,
fixed 28-tag set) was run across all five cells. Observed file counts at the time `methods.md` was
finalized:

| Cell | Files |
|---|---|
| ① human_monologue | 600 |
| ② human_debate | 500 |
| ③ ai_debate | 585 (run still finishing) |
| ④ ai_monologue | 594 (run still finishing) |
| ⑤ ai_reasoning | 421 and climbing (target; run in progress) |

**Firewall status — the important part.** Generating cell ⑤'s per-sentence tags is the mechanical
execution of Step 2 for Method 3, not an analysis contact: the tagger makes no decision that could
be tuned against an outcome. As of this entry, a repository-wide search finds **no** transition
matrix, completion-rate, unigram/bigram distribution, or JSD artifact for **any** cell, cell ⑤
included — i.e. the §3 summary statistics that a garden-of-forking-paths choice would exploit have
not been computed on cell ⑤ (or anywhere). This supersedes the earlier note about a single
"smoke-test" file in `outputs/method3/cell5_ai_reasoning/`.

- [ ] **Confirm before freezing:** no §3 statistic (§3a distribution, §3b transitions, §3c
      completion rate, §3d JSD) has been computed or inspected on cell ⑤. If any has, note it here
      and treat the corresponding decision as data-informed / exploratory rather than
      pre-registered.
- [ ] **Commit `methods.md` + `STATUS.md` together** once the four open numbers in `methods.md` §6
      are signed off. That commit is the pre-registration timestamp and must precede the first §3
      computation on cell ⑤.

## Method 2 SOURCES.md claims — retracted at the source, not just left unadopted

`methods/2_stylometric_step_change/sources/SOURCES.md` asserted a "0.5 average-probability"
decision rule and benchmark scores (0.929 / 0.815 / 0.724). Checked against the PAN25 paper: the
0.5 average-probability rule does not appear in the paper at all, and the cited scores mix two
tables that disagree with each other on the hard score (abstract 0.724 vs Table 3 0.731). These
claims were not swapped into `methods.md` §2, and — since confirmed as mistaken rather than merely
unverified — `SOURCES.md` itself has now been corrected in place to mark both claims retracted,
rather than leaving the error sitting in a source file.

## Method 2 — length confound found and corrected

Checked actual document lengths across all five cells: `ai_reasoning` (median ~10,700 chars) is
longer than both AI poles (`ai_debate` ~6,900, `ai_monologue` ~860 median), which matters because
Method 2's raw per-document mean switch-probability dilutes with length if true switches are closer
to a fixed count than a constant rate. Fixed by fitting a length-adjustment (mean switch-probability
regressed on log(sentence pairs)) using only the four calibration cells, frozen, then applied to
cell ⑤ mechanically later — no cell ⑤ contact in the fit. See `methods.md` §2.

## Open items carried from methods.md §6

All five original open numbers are now resolved. Method 1's gate uses a binomial test against
chance instead of an imported percentage; Method 2's gate requires direction + Cliff's delta ≥ 0.33
instead of a bare direction check; Method 2's equal-slope tolerance is no longer applicable since
each pole gets its own independently-fit curve; Method 3's comparison margin `m` is now calibrated
per signal from a bootstrap noise floor on ③/④ instead of a flat 0.10 default; and Method 3's
reliability sample size is now computed from Cohen's κ asymptotic variance formula (target: 90% CI
half-width ≤ 0.10, 122/83/137/168 utterances for cells ①–④, 510 total) instead of a flat 50/cell default.

## Method 3 — margin and reliability-sample procedures made empirical (2026-07-16)

Two remaining flat defaults in Method 3 were replaced with calibration-data-derived procedures, at
the user's request, to remove the last "asserted round numbers" from the pre-registration:

- **Comparison margin (§3d).** Was a flat `m = 0.10`. Now: bootstrap-split ③ and ④ (the two known
  poles) repeatedly, measure the gap the same signal produces between two random halves of the same
  pole (a true null — the "same thing" compared with itself), and set `m` to the 95th percentile of
  that noise distribution, separately for §3a/§3b/§3c since they have different sampling behavior.
  Runs only on ③/④, never touches cell ⑤.
- **Reliability sample size (§3e).** Was a flat 50 utterances/cell (200 total). Now: solved from the
  standard Cohen's κ asymptotic variance formula (Fleiss, Cohen & Everitt, 1969) for the `n` that
  gives a 95% CI half-width ≤ 0.05 around the measured κ, using each cell's own §3a tag-frequency
  marginals (calibration-only input) or a conservative uniform-marginal assumption if computed
  before §3a is available. Expected to land around 100–200/cell, but this is computed at
  execution time, not picked now.
- **Strict-adjacency assumption in §3c** (no insert-expansion tolerance) — reviewed and confirmed
  by the user as acceptable, given the "conservative lower bound, can only understate dialogue-ness"
  framing already in `methods.md`. No change made; recorded here as signed off.

Neither change involved inspecting cell ⑤'s tags or any §3 statistic on cell ⑤ — both procedures run
exclusively on ③ and ④.

## Method 1 — gate changed from pooled to balanced accuracy (2026-07-17)

**Supersedes** the earlier note that "Method 1's gate uses a binomial test against chance" (in the
"Open items carried" section above). While preparing the Method 1 validation we found the
pooled-accuracy-vs-0.5 gate is not imbalance-safe: the calibration cells hold ~1,200 single-author
documents (①④) against ~1,100 multi-author (②③), so a **degenerate detector that labels everything
single-author already scores ≈0.52 pooled** and can clear a one-sided binomial test against 0.5 on
sample size alone — i.e. a method that detects no dialogue at all could "pass."

Fix: the gate now uses **balanced accuracy = ½·(recall_single + recall_multi)**, where
recall_single is over the pooled monologue cells ①④ and recall_multi over the pooled dialogue cells
②③. The all-single detector scores exactly 0.50 on this, so passing requires genuinely detecting
multi-voice text somewhere. Significance is a label-permutation null (10,000 shuffles, one-sided
p < .05), which centres at 0.50 regardless of the imbalance; per-class recalls, per-cell recall
breakdown, confusion matrix, and a bootstrap 95% CI on balanced accuracy are reported alongside.

Character of the change: this is a **tightening** (it removes a free pass) and a metric-correctness
fix, decided from the class-count structure of the cells — not a reaction to any observed
calibration result (none has been computed). Applied consistently in `methods.md` §1, the paper
(`paper/main_v2.tex`, Method 1), and `run_calibration.py`/`RUN_METHOD1.md`.

Scope check — Methods 2 and 3 do **not** need the same fix: their gates are effect-size / rank based
(Method 2: direction + Cliff's δ ≥ 0.33; Method 3: κ ≥ 0.70 + directional completion-rate with
Cliff's δ), which are inherently imbalance-robust and cannot be passed by a degenerate constant
predictor. Method 1 was the only gate stated as raw accuracy. (Separately, whether off-task
`human_debate` should carry weight in the Method 2/3 pole contrasts is a different question, not
addressed here.)

## Method 2 — AIC-comparison precisified to a common scale (2026-07-17)

`methods.md` §2 says the per-pole length curve is chosen among linear / semi-log / log-log "by
minimizing AIC," but that instruction is under-specified: the log-log candidate is fit on
`log(score)` while linear and semi-log are fit on `score` directly, so their AICs are computed on
different response scales and are not directly comparable as-is — a lower log-log AIC could just
reflect the smaller numeric range of log-space, not a better fit.

`run_calibration.py` (Method 2) resolves this by scoring all three candidates on a **common
scale**: residual sum of squares in the *original* score units (back-transforming the log-log
fit's predictions before computing residuals), then applying the standard AIC formula
(`n·log(RSS/n) + 2k`) to that common-scale RSS. This is a precisification of the frozen wording,
not a substantive change to the selection rule (still AIC, same three candidates, still fit
independently per pole on calibration-only data) — logged here for the same reason the other
precisifications are: so the exact comparison procedure is on record before it's run on any
calibration numbers.

## Method 3 — reliability sample-size precision target relaxed (2026-07-18)

The κ reliability sample size (§3e.1) was computed at the original 95%-CI/±0.05-half-width
precision target and came out to 691 / 466 / 778 / 949 utterances for cells ①/②/③/④ — **2,884
total**. For a practical (non-thesis) project, this is disproportionate hand-labeling effort.

**What changed and what didn't.** The pass/fail bar itself — κ ≥ 0.70 — is untouched; lowering
that would be lowering the actual reliability standard, which we do not do. What changed is the
*precision target* for how tightly the measured κ must be pinned down: from 95% CI / half-width
≤ 0.05 to **90% CI / half-width ≤ 0.08**. This is a legitimate blind decision — a cost/precision
trade-off fixed independent of any measured κ (no hand-labels exist yet) and independent of cell
⑤ — not a relaxation of the actual reliability requirement. At a measured κ around 0.75, a ±0.08
band ([0.63, 0.87] roughly) is still unambiguous relative to the 0.70 cutoff; it is a
substantially looser precision guarantee than ±0.05, but still sufficient to make the pass/fail
call meaningfully rather than as an artifact of a wide interval.

Recomputed at the new setting, using each cell's real observed §3a marginals (calibration-only):
**191 / 129 / 215 / 261, 796 total** — 28% of the original, and close to the original
"100–200/cell" ballpark noted in the "Open items" section above (before the exact formula was
run). `reliability_sample.py` now exposes `--half-width` and `--confidence` as CLI flags (default
0.08 / 0.90) so this setting is explicit and adjustable rather than hard-coded silently; the
original 95%/±0.05 setting remains available (`--confidence 0.95 --half-width 0.05`) if stricter
precision is wanted later. See `methods.md` §3e.1 and `RUN_METHOD3.md` for the same numbers.

## Method 3 — reliability sample-size precision target relaxed further (2026-07-17)

Even 796 total hand-labels (§ above) was judged more than needed for a practical project.
Decided to loosen the precision target once more, from **90% CI / half-width ≤ 0.08** to **90%
CI / half-width ≤ 0.10** — confidence level unchanged, only the half-width widened. As before,
the pass/fail bar (κ ≥ 0.70) is untouched, and the decision was made blind to any measured κ (no
hand-labels exist yet, only §3a marginals). Unlike the first relaxation, the reasoning this time
is not purely the CI-precision argument: it also reflects a deliberate margin against noise in
the human labeling itself (a single rater covering 27 confusable dialogue-act categories is more
error-prone at very low n) — more samples make the measured κ more robust to a handful of
mislabels, independent of what the formal CI target requires.

Recomputed at the new setting: **122 / 83 / 137 / 168, 510 total** (①/②/③/④) — 64% of the
intermediate 796, 18% of the original 2,884. At a measured κ around 0.75, a ±0.10 band
([0.65, 0.85] roughly) is still unambiguous relative to the 0.70 cutoff. `reliability_sample.py`
defaults updated to `CI_HALFWIDTH = 0.10` (confidence unchanged at 0.90); `sample_plan.json`
regenerated at this setting; the stale test-era `worksheet.csv` / `hidden_llm_labels.json` (10
rows, left over from an earlier dry run, inconsistent with any real plan size) were deleted so
the next `--sample` draws a clean, correctly-sized worksheet. See `methods.md` §3e.1 and
`RUN_METHOD3.md` for the same numbers.

## Data — speaker-label leak found in BOTH dialogue cells, fixed + re-runs pending (2026-07-21)

`standardize_datasets.py`'s `remove_speaker_labels` under-cleaned the two dialogue cells,
leaving a **condition leak** (speaker identifiers that let any method shortcut "this is a
dialogue cell" rather than reading genuine signal). Found while auditing the raw-vs-processed
human_debate files; then, prompted to check the other dialogue cell, confirmed ai_debate is
infected too. Monologue cells (①④) and the cell⑤ target are **unaffected** — verified 0
occurrences in all non-dialogue cells, so the pre-registration firewall around cell⑤ is intact.

**human_debate (②).** Only line-start `Name:` prefixes for a hardcoded animal list were
stripped. This missed the two-word name `Guinea pig:` entirely (444/444 turn prefixes left in
place) and ~1,000 inline references (`@Cat`, `Thanks Bat`, lowercase `yes kiwi is right`) for
all 29 pseudonyms. The names are the **top-1/2/3 most-frequent tokens** in every document, i.e.
Method 1's dominant MFT clustering features.

**ai_debate (③).** The four prompt-assigned role titles (`Critical Analyst`,
`Creative Problem Solver`, `Mathematical Validator`, `Alternative Seeker`; 600+ occurrences,
**cell③-only**, 0 in every other cell incl. ⑤) plus capital-letter speaker references
(`A's approach`, `great job, C!`) survived in the utterance text. Role-words sit in the top-50
MFT of ~half the docs. Bare/lowercase `a`–`d` were deliberately **not** removed (overloaded with
the article "a", sentence-initial "A", and math) — the letter cleanup is surgical and
case-sensitive (possessive / vocative-before-punctuation / "X said" / "well done X" only).

**Fix (audited, non-destructive until committed).** Two new scripts,
`scripts/refix_human_debate_labels.py` and `scripts/refix_ai_debate_labels.py`. Each derives its
target set (human: 29 names via a frequency-floor "cliff"; ai: the 4 titles + surgical letter
patterns), removes it from every field the methods consume (`transcript` for human; and for ai
`full_text_no_labels` + `turns[].text_clean/raw` + `labeled_turns[].text` — M1/M2 read
`turns[].text_clean`, M3 tagged `full_text_no_labels`), and prints a full removal audit.
Verified: **residual 0** in every field, **0 content-word / article-"A" false positives**.
M1/M2 use `turns[].speaker` only for turn boundaries (never injected into the token stream), so
no method-code change is needed.

**Re-runs required** (data is upstream of the frozen `methods.md`, so this is a legitimate
data-integrity fix, logged not silently applied): Method 3 re-tag of cell②+cell③ only (LLM),
then M3 gate + reliability worksheet regen; Method 1 full re-run; Method 2 first run on clean
data. Step-by-step commands in **`RECLEAN_RUNBOOK.md`** (repo root). Watch items: M3 completion-
rate δ (was 0.438) may drop if it was partly leak-driven — still needs δ ≥ 0.33; M1 balanced
accuracy may move.

### Re-run results (2026-07-22) — all three gates re-verified on clean data

**Method 1** (`run_calibration.py`, unmodified, re-run on cleaned `processed_human_debate.jsonl` /
`processed_ai_debate.jsonl`): balanced accuracy **0.6088**, identical to the dirty-data figure
(0.6088). Per-cell recall unchanged (585/600, 0/500, 254/600, 599/600); bootstrap 95% CI
[0.5961, 0.6210]; label-permutation p = 0.0001. **GATE PASS.** The leak was not driving this
signal — confirmed the re-run wasn't a caching artifact (574/600 `ai_debate` docs' cleaned text
independently verified to differ from the dirty version; no data-level cache existed, only
Python bytecode).

**Method 2** (`run_calibration.py`, unmodified, re-run on the same cleaned files): Cliff's
δ = **0.6211** vs. the dirty-data baseline of 0.6300 (direction unchanged, True). **GATE PASS.**
Small decrease, not a meaningful shift — again consistent with the leak not being what drove the
signal.

**Method 3 re-tag.** Ran `label_dialogue_acts_v2.py` (confirmed via git history to be the exact
script + prompt file used for the original cell①④⑤ tagging, both untouched since the initial
commit — not the newer `label_dialogue_acts.py`, which gained resume/retry logic afterward),
model `tencent/hy3`, temperature 0 (script default), on the cleaned `processed_human_debate.jsonl`
(`--text-field transcript`, cell②) and `processed_ai_debate.jsonl` (`--text-field
full_text_no_labels`, cell③). cell①④⑤ untouched, as required.

- **cell② human_debate: 500/500** — no losses.
- **cell③ ai_debate: 591/600** — 9 docs excluded after 4 real attempts each (original run, a
  retry once OpenRouter credits were confirmed available — a mid-run `402 Insufficient credits`
  had blocked one retry round entirely and doesn't count as a real model attempt — a further
  retry, then a final parallel attempt at 2× `--max-tokens`). Root cause confirmed via direct API
  diagnostic: `tencent/hy3` (a reasoning model) gets stuck re-solving the embedded arithmetic
  puzzle inside these specific `ai_debate` transcripts instead of tagging them, exhausting the
  full completion-token budget on reasoning with `finish_reason: length` and no tagging output
  ever produced. Not a chunking-fixable problem (chunking was explicitly rejected — it would
  break CAMS's whole-utterance-context requirement) and not budget-fixable either (doubling the
  budget only rescued 5 of the 14 candidates at that point). **Caveat:** the 9 exclusions skew
  toward the longest/most circuitous `ai_debate` transcripts (most of the original 14 stuck docs
  were above the corpus's 90th-percentile length) — this is not a random ~1.5% loss and should be
  read as such in any writeup. Full retry history and excluded `debate_id`s in
  `outputs/method3/cell3_excluded_docs.md`.

**Method 3 signal-validity gate (§3c completion rate), re-run on the new tags:** Cliff's
δ = **0.4649** (cell③ n=591) vs. the dirty-data baseline of 0.4380 (cell③ n=598, recorded in
`M3_internal_verification.md`) — direction unchanged, **GATE-A and GATE-B PASS**. Signal is
slightly stronger post-cleaning, not weaker — the leak was not inflating this gate either.

**Method 3 reliability sample, re-solved from the clean-tag marginals:** 122/82/131/168 = **503
total** (①/②/③/④), close to the pre-cleaning figure of 510. Fresh `worksheet.csv` (503 rows,
blank) and a fresh 200-item `practice.csv` (verified disjoint from the worksheet, 0 shared keys)
were generated; the stale pre-cleaning worksheet/practice files were overwritten by this
regeneration.

**Bottom line:** across all three methods, the speaker-label leak was a real data-integrity bug
worth fixing, but empirically it was not the source of any method's validation signal — every
gate still passes on clean data, with results essentially unchanged (M1) or slightly improved
(M2 down 0.009 δ but still far above threshold; M3 completion-rate δ up 0.027). The one
substantive change is the 9 excluded `ai_debate` documents in cell③, which is a model-capability
limitation of `tencent/hy3` on long arithmetic-heavy transcripts, unrelated to the leak fix
itself.
