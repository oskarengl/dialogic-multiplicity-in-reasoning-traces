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

---

## 2026-07-22 — Method 3 reliability gate (b): SCORED, FAILED

**Manual labeling completed.** All 503 worksheet items hand-labeled by the rater
(①122 / ②82 / ③131 / ④168, matching `sample_plan.json`). 0 blank, 0 invalid tags.
`journal.jsonl` (638 label events) reconciles with `worksheet.csv` with zero mismatches;
18 journal keys predate the 2026-07-22 worksheet regeneration and are inert. Labeling was
blind throughout — `hidden_llm_labels.json` was never surfaced in the UI, and practice mode
gave no per-item correctness feedback. Committed as `aecfd6f`.

**Self-test run before scoring** (`reliability_sample.py --selftest`): n-formula direction
check passed (skewed marginals require larger n than uniform: 104 vs 60); κ recovery on
simulated raters measured 0.824 against a ~0.75 target. Machinery verified sound *before*
the real number existed.

**GATE (b) RESULT — FAIL.** Pooled Cohen's κ = **0.5425**, bootstrap 95% CI
[0.4788, 0.6038], n = 503, 0 rows skipped. Pre-registered bar is κ ≥ 0.70 (methods.md §3e,
SOURCES.md). The CI upper bound sits well below the threshold — not a borderline call.
Per cell: ① 0.5456, ② 0.6048, ③ 0.5725, ④ 0.3874. Report: `outputs/method3/reliability/score_report.txt`.

Underlying agreement: 373/503 exact matches (74.2% raw), chance agreement p_e = 0.4350.
κ = 0.70 would have required 418/503 (83.1% raw) — a shortfall of 45 items.

**κ₀ = 0.70 was NOT moved and must not be.** Method 3 clears gate (a) (completion-rate
δ = 0.4649) but required both. **Method 3 is therefore not a validated method and does not
place cell ⑤.** Cell ⑤ is placed by Methods 1 and 2 only.

### Exploratory follow-ups (NOT gates, both chosen after seeing the failing number)

1. **Family-collapse κ** (`scripts/exploratory_family_kappa.py`) — collapsing both label
   sources to the 9 CAMS functional families gives κ = 0.6074 [0.5318, 0.6768]. Still below
   0.70. Disagreement decomposition: 74.2% exact, 8.9% same-family/wrong-tag, 16.9%
   different family. 50 of the 85 cross-family disagreements sit on the single
   `inform`↔`suggest` boundary (providing→directive 26, directive→providing 24).
   Output: `outputs/method3/reliability/exploratory_family_kappa.txt`.

2. **Weighted agreement per the CAMS authors** (`scripts/exploratory_weighted_agreement.py`)
   — Duran, Battle & Smith (2022) argue unweighted π/κ are not an acceptable measure for
   dialogue-act labeling because they give no credit for semantic near-misses, and instead
   use weighted coefficients over a distance matrix derived from the CAMS DA tree. Reproduced
   here: Krippendorff **α = 0.6188** [0.5531, 0.6864]; Artstein–Poesio α′ = 0.6184, β = 0.6185.
   Per cell: ① 0.6766, ② 0.6414, ③ 0.6724, ④ 0.4236. 14 items dropped (`none` has no node in
   the CAMS tree). Implementation validated to 4 d.p. against the Artstein & Poesio (2005)
   fixture that Duran et al. use for the same purpose (α 0.8156 / α′ 0.8146 / β 0.8163 — all
   reproduced exactly); the script refuses to score real data if that check fails.
   Swapping Duran's column-wise normalisation for a symmetric global-max one moves α by 0.002.
   Output: `outputs/method3/reliability/exploratory_weighted_agreement.txt`.
   Vendored inputs + provenance: `methods/3_dialogue_act_tagging/sources/duran_cams_agreement/`.

**Reading:** weighting is worth ≈ +0.076 over unweighted κ, and two independent coarsenings
(family collapse, tree-weighted α) converge on ≈ 0.61. So part of the shortfall was the
measure being unfair to near-misses — but the residual gap to 0.70 is genuine disagreement,
concentrated on `inform`/`suggest`, which the CAMS tree does *not* forgive (they sit under
different top-level branches). 0.619 is still below Carletta's (1996) 0.67 "tentative
conclusions" floor. Cell ④ is the weakest cell under every measure.

**Diagnostic viewer** (not an analysis): `outputs/method3/reliability/disagreements.html`,
built by `scripts/build_disagreement_review.py` — all 130 disagreements with ±3 sentences of
context, filterable. Note 11 of 130 are the tagger falling back to `none`, and 24 more are it
collapsing correction/answer/agreement/disagreement into generic `inform`.

---

## 2026-07-22 (later) — Step-3 preparation: verdict rule clarified, placement margins frozen

Everything in this entry happened **before** any §3/§4 statistic was computed on cell ⑤. The
firewall is still up as of the end of this entry; a repository-wide check for cell-⑤ placement
artifacts is recorded at the bottom.

### §4 verdict-combination rule with two surviving methods (clarification, not a change)

`methods.md` §4 was drafted assuming three methods would reach Step 3 ("the *pattern* of their
three verdicts"). M3 failed §3e, so two do. **The frozen §4 text was not edited**; a dated
clarification note was appended beneath it recording how it reads at n = 2. Decision, made by
the user before any cell-⑤ number existed:

- The rule applies unchanged. Agreement between M1 and M2 is the headline; a 1–1 split is
  reported as a split with both verdicts and both margins shown; no vote, no tie-break, no
  primary method.
- One substantive addition: where §4 says the strength of a concurrence "is exactly that three
  unrelated measures concur," a two-method concurrence must be stated as the weaker claim it is.
- Explicitly rejected: designating M1 or M2 as primary in case of a split. That choice would be
  made in full knowledge of which methods survived — a post-hoc selection of exactly the kind §4
  exists to prevent.

### Cell ⑤ wired into the M1/M2 run scripts (data path only)

Both `run_calibration.py` scripts gained a `"5"` entry in `CELLS` pointing at
`data/00_core-2x2/ai_reasoning/processed_native_reasoning_traces.jsonl` with `true_bin = None`.
The text builder is **byte-identical to cell ①'s** (continuous prose in `think_trace`), so no new
text handling is introduced — this is the "change the input data, not the method code" precedent.

Three guards were added so running the target cannot disturb the frozen gates:

- Cell ⑤ predictions/scores are written to **separate files** (`outputs/method1/cell5_predictions.jsonl`,
  `outputs/method2/cell5_raw_scores.jsonl`); the calibration artifacts are never appended to.
- Cell ⑤ is **not** in the default full-run loop, so it can never be produced as a side effect of
  re-running a gate.
- M1's `report()` now filters to cells ①–④ before computing anything. This is a no-op on a correct
  run (verified: the calibration file contains 600/500/600/600 rows and no cell-⑤ rows); it exists
  so a mis-routed target row cannot silently move balanced accuracy. M2's `report()` already
  selected cells explicitly and needed no change.

### Placement margins `m` for M1 and M2 — computed and frozen (`scripts/freeze_placement_margins.py`)

Ran **before any cell-⑤ statistic existed**; the output file records, as a machine-checked
provenance field, that neither cell-⑤ output file was on disk at freeze time. Inputs were the
existing calibration artifacts only. Cell ⑤'s document count (600) is read as a line count and is
the only cell-⑤ fact touched — no text, no score.

**A problem with the literal §3d procedure, found while implementing it.** §3d fixes `m` as the
95th percentile of a null built by splitting a pole into halves and recording "the relative gap
this produces." The statistic `m` actually gates is
`r = |d_mono − d_dia| / max(d_mono, d_dia)`, and the half-split null is **not** a valid null for
that statistic. It omits probe-side sampling noise — and probe-side noise is the dominant term,
because when the probe's own mean wobbles, `d_mono` grows exactly as `d_dia` shrinks, so the gap
moves by *twice* the probe's error — and it divides by the full pole-to-pole distance rather than
the ≈ half that an equidistant probe sits at. Both errors push `m` down.

Quantified on synthetic poles with realistic dispersion (`--selftest`): against probes constructed
to be *exactly equidistant*, the literal-§3d margin (NULL-A) has a **37.2% false-positive rate** —
it declares a lean where none exists more than a third of the time, against a nominal 5%.

**NULL-B, the corrected null.** Build a probe that is equidistant *by construction* out of pole
documents, then let every noise source act: probe and both anchors are resampled, and for M2 each
pole's length curve is refit on its bootstrap resample so curve-fit uncertainty is included. For
M1's mean-difference distance a 50/50 mixture of ③ and ④ is exactly equidistant; for M2's
residual distance it is not, so the mixing proportion is **solved** in closed form (`solve_mix_p`,
verified in `--selftest` to equalise the two distances to machine precision) — it came out to
0.2475. NULL-B's false-positive rate on equidistant probes is **1.4%**.

Both nulls were computed and are recorded; the verdicts:

| signal | NULL-A (literal §3d) | NULL-B (corrected) |
|---|---|---|
| M1 mean predicted author count | 0.1940 | **0.3615** |
| M2 lean residual | 0.1217 | **0.1117** |

Note the direction: adopting NULL-B makes M1's margin **substantially harder to clear** (0.19 →
0.36) and leaves M2's essentially unchanged. It is not a choice that buys an easier placement —
it makes a "no clear margin" verdict more likely, which is the conservative direction.

Character of the change, for the record: this is the same class as the 2026-07-17 Method 1
pooled→balanced-accuracy fix — a **metric-correctness fix derived from the structure of the
statistic**, decided with no cell-⑤ result in existence and demonstrated on synthetic data where
the right answer is known in advance. No pre-registered *threshold* moved; the 95th-percentile
rule, the ③/④-only data restriction, and the "no clear margin" reporting are all as written.
Output: `outputs/placement/margins_frozen.txt` / `.json`.

**DECISION (user, 2026-07-22, before any cell-⑤ run): the placement uses NULL-B.**
`m_M1 = 0.3615`, `m_M2 = 0.1117`. NULL-A's values remain in the frozen output file so the size of
the correction stays auditable, and the 37.2%-vs-1.4% false-positive comparison belongs in the
methods/limitations write-up rather than being left implicit. The decision was recorded here
before `run_calibration.py 5 ...` was executed for either method.

### Step-3 machinery written and self-tested (no target data touched)

- `scripts/place_cell5.py` — the §4 placement. Applies the §3d call to M1 and M2, reports the
  verdict *pattern* (never a vote), emits Table X and the ④ = 0 / ③ = 1 normalised axis with each
  method's no-clear-margin band. Refuses to run unless the margins are already frozen, so the
  threshold cannot be picked with the answer on screen. `--selftest` covers the three-verdict
  vocabulary, the exact `r = m` boundary (on binary-representable values), the degenerate
  zero-distance case, the open band interval, and the pole→0/1 rescaling. ALL PASS.
- `scripts/make_placement_figures.py` — §5 Figs M1.1, M2.1, M2.2, X.1 → `paper/figures/*.pdf|png`.
  Renders the calibration-only versions until cell ⑤ exists. Okabe–Ito colours (colour-blind
  safe); cells ①/② stay neutral grey so they cannot be misread as poles.
- `RUN_CELL5.md` (repo root) — the ordered runbook.

### Paper placeholders filled — validation-cell numbers only

`paper/main_v2.tex` went from **32** unfilled `\resultnum{}` to **8**. Everything filled is a
calibration-cell result with no cell-⑤ contact; every remaining placeholder is genuinely blocked.
Verified: the document still compiles (pdflatex, 19 pages, no errors), and both gate numbers
reproduce **after** the cell-⑤ wiring — M2's `--report` prints δ = 0.6211 unchanged, and M1's
balanced accuracy independently recomputes to 0.6088 from the prediction file.

Filled: M1 lead-in (0.6088, CI [0.5961, 0.6210], p = 0.0001, recalls 0.9867 / 0.2309) and the
per-cell Table M1 rows; M2 lead-in and Table M2 (δ = 0.6211, group means 0.0125 vs −0.0105,
per-cell leans, both AIC triples, semi-log selected for both poles); M3 lead-in written as a
**failed validation** (δ = 0.4649 passes gate (a), κ = 0.5425 [0.4788, 0.6038] fails gate (b))
and the Table M3 reliability row.

Two rows were changed from red placeholders to explicit "not computed" statements rather than
left as invitations to fill them in: Table M3's cell-⑤ completion-rate row, and its three
placement-signal rows. Computing a §3 statistic on cell ⑤ for a method that failed Step 1 would
be a firewall contact by an unvalidated method. Flagged as an open decision if a purely
descriptive figure is wanted later — it would have to be labelled as such and kept out of §4.

Still blocked: the two cell-⑤ rows in Tables M1/M2, the two cell-⑤ verdict cells in Table X, and
Table M3's per-cell completion rates for ①–④ (no saved artifact holds them; the δ was computed
without persisting the per-cell means).

## 2026-07-22 (later) — Step 2 executed on the target; cell ⑤ placed

The cell-⑤ target runs and the placement were finally executed. **The firewall held throughout:**
the margins were already frozen (15:53:42Z, recording `method1:false / method2:false`) before any
cell-⑤ method output existed, so no threshold could be tuned to the answer.

**Pre-flight verification (firewall-safe; no §3 statistic on cell ⑤ computed):**
- `margins_frozen.json` records both cell-⑤ outputs absent at freeze; its mtime (17:53 local) matches
  its recorded `frozen_at_utc` 15:53:42Z.
- Calibration files match the frozen record exactly (M1 {600,500,600,600}; M2 usable {559,497,600,559}).
  Zero stray cell-⑤ rows in either gate file.
- Cell-⑤ data integrity: `processed_native_reasoning_traces.jsonl`, 600 docs, `think_trace` present
  and non-empty in all 600 (0 empties). No content/distribution was inspected.
- `place_cell5.py --selftest` and `freeze_placement_margins.py --selftest` both ALL PASS (the latter
  reproduces NULL-A's 37.2% vs NULL-B's 1.4% false-positive rate on equidistant probes).

**Stray artifact found and archived (did not affect the freeze).** A partial, untracked
`outputs/method1/cell5_predictions.jsonl` (177/600 lines, mtime 16:29Z — i.e. created *after* the
15:53Z freeze, by an earlier interrupted attempt the prior handover omitted) was discovered. M1
appends, so it would have corrupted a fresh run into 777 overlapping rows. Moved to
`outputs/archive_stray_partial/method1_cell5_partial177_16-29Z.jsonl`. No placement verdict file
existed → the envelope had never been opened.

**Runs (exact original scripts, cell "5" argument only; data changed, method code not):**
- M1 `run_calibration.py 5 0 600` → 600 rows, 74 s. Structural check: idx 0–599 once, all fields
  present, `true_bin` null.
- M2 `run_calibration.py 5 0 600` → 600 rows, 1779 s (GPU), **0 docs dropped** (all ≥2 sentences).

**Placement (`place_cell5.py`, NULL-B margins), `outputs/placement/cell5_placement.{txt,json}`:**

| Method | d_mono | d_dia | r | m | verdict | bootstrap stability | axis (④=0,③=1) |
|---|---|---|---|---|---|---|---|
| M1 | 0.3167 | 0.5367 | 0.4099 | 0.3615 | monologue-leaning | 70.7% | 0.371 |
| M2 | 0.0588 | 0.0154 | 0.7372 | 0.1117 | dialogue-leaning | 100% | **1.447 (past ③)** |
| M3 | — | — | — | — | excluded (κ 0.5425 < 0.70) | — | — |

**Pattern: SPLIT** (reported, not voted, per §4). Read with two documented caveats, both already
pre-registered: M1 is a conservative detector (its monologue call ≈ "no document-level authorship
signal", not positive single-voice evidence); M2's monologue distance is an **extrapolation** —
median cell-⑤ length 232 sentence-pairs vs pole ④'s max 209, 63.7% of cell ⑤ beyond ④'s observed
range (only 1.7% beyond ③'s). Cell-⑤ descriptive numbers now on record: M1 mean author count 1.32,
share called multi-author 26.3%; M2 mean lean +0.0433.

**Figure display fix (visualization only — no frozen number touched).** `make_placement_figures.py`
`fig_x_1` clipped M2's target (s=1.447) off the x-axis and overlapped the legend/pattern text.
Rewrote the panel to auto-extend the x-range to include an out-of-pole target, flag "beyond ③/④",
and move the legend below the axis. All four figures regenerated.

**Paper (`main_v2.tex`) — placement results filled** (8 `\resultnum` → 4 remaining): Table M1 target
row (1.32, 26.3%), Table M2 target row (0.0433), Table X both verdict rows, all four figures wired
in with finalized captions, abstract verdict sentence, intro contribution (iii), the M1
conservative-detector paragraph, the M2 85-excluded-docs note, and the Discussion "interpretation
of the observed pattern" (the split, both caveats, the Kim et al. inside-vs-outside dissociation).
**Not yet compiled** — no LaTeX toolchain on this machine; the user should run pdflatex to confirm.

**Still open:** Table M3 per-cell completion rates for ①–④ (the last 4 `\resultnum`; need a recompute
from the M3 tag outputs); the non-result `\todo`s (citation requests, M3 failed-validation prose,
caption polish); and the git commit — locks still block it, nothing is committed since `aecfd6f`.

## 2026-07-23 — Method 3 reported as an EXPLORATORY analysis (does not touch the frozen verdict)

**Scope.** M3 failed its §3e gate (κ = 0.5425 < 0.70) and is still excluded from the confirmatory
placement. The 2026-07-22 M1/M2 SPLIT is unchanged; Table X (`tab:verdicts`) and Fig X.1
(`fig:placement`) are still M1/M2 only; `cell5_placement.{txt,json}` was not touched. This entry
sits *after* the gate result and is kept out of all gate logic. Everything below is exploratory.

**Table M3 completion rates ①–④ filled** (the last 4 `\resultnum` → 0 remaining in the paper).
Recomputed with `run_calibration.py` from the existing tags (numpy only, no LLM, no re-tag):
mean defined-rate / FPP-absent share = ① 0.0998 / 4.3%, ② 0.2350 / 0%, ③ 0.0248 / 0%, ④ 0.0030 / 0%.
Calibration-only, no cell-⑤ contact.

**M3 exploratory cell-⑤ placement — new script `scripts/place_cell5_method3_exploratory.py`.**
Applies the frozen §3a–§3d machinery to cell ⑤ (tags NOT re-tagged; existing counts
①600 ②500 ③591 ④597 ⑤597). Signals: c completion (primary, mean-difference distance),
a unigram JSD, b bigram JSD. Margins by the §3d same-pole bootstrap on ③/④, both nulls
(NULL-A literal, NULL-B corrected — NULL-B reported to match the M1/M2 placement). Outputs labelled
EXPLORATORY in-artifact: `outputs/placement/cell5_method3_exploratory.{txt,json}`.

- **The margins are POST-HOC and the writeup says so plainly.** M3 never reached placement, so no M3
  margin was ever frozen; these were computed 2026-07-23, after the M1/M2 answer was known
  (`margin_frozen_before_target: false` in the JSON). This is one of two stated reasons the M3
  placement is exploratory (the other being the failed gate). Seed 20260723; both nulls use ③/④ only.
- **Result.** Signal c: d_mono 0.0320, d_dia 0.0102, r 0.6809 > m 0.4404 → **dialogue-leaning**
  (⑤ mean rate 0.035, just above pole ③'s 0.025, well above pole ④'s 0.003), 100% bootstrap
  stability. Signals a/b: **no clear margin** — ⑤ sits ~equidistant (r 0.072 / 0.005) and the two AI
  poles are so close distributionally (pole-to-pole JSD 0.052 / 0.102) that the same-pole noise floor
  is wide (post-hoc m 0.94 / 0.91). The distributional signals cannot resolve a placement here.
- **Verification.** `--selftest` PASS: verdict vocabulary + exact r=m boundary + degenerate case;
  `solve_mix_p_jsd` equalises the two JSDs to ~1e-16; NULL-B equidistant-probe false-positive rate
  within tolerance and at-pole probe still called; vectorized `jsd_rows`/`draw_counts` match
  `signals.jsd`/`pooled` to machine precision; and the per-document count matrices reproduce
  `signals.cell_unigram`/`cell_bigram` exactly for all five cells (max diff 0.0). A verification stamp
  (`outputs/method3/_tag_cache/count_matrices_verified.json`, keyed on the tag fingerprints) records
  the check. Count matrices are cached to `_tag_cache/count_matrices.npz` (uint32, fingerprint-keyed;
  built once via `--build-cache`, which re-reads tags but never re-tags).

**Figures — `scripts/make_method3_figures.py`** (Okabe–Ito, mirrors `make_placement_figures.py`):
Fig M3.1 tag distribution (`fig_m3_1_tag_distribution`), M3.3 completion-rate box+strip
(`fig_m3_3_completion_rate`, headline), M3.4 JSD scatter (`fig_m3_4_jsd_scatter`). Every cell-⑤
element is the target colour and each figure carries an "exploratory / gate failed" footer. Fig M3.2
(transition heatmaps) was left as future work and its placeholder removed from the paper. All wired
into `main_v2.tex` with finalized captions.

**Prose (`main_v2.tex`).** (a) §Method 3 Results: the failed-validation writeup now filled — the
fine-grained-scheme + defensible-disagreement argument, the `inform`/`suggest` 50-of-85 concentration,
the exploratory reanalyses (family-collapse κ 0.6074, tree-weighted α 0.6188, both < 0.70 and <
Carletta's 0.67), ④ weakest (κ 0.387), and the FPP-absent deviation *reconciled* to the spec
(defined-rates-only; the old "scored 0" methods sentence and its `\todo` were corrected). (b) New
subsection **`sec:m3-exploratory`** "Exploratory: Method 3's reading of cell ⑤", placed after the
cross-method summary: states the two caveats (failed gate; post-hoc margins) up front, reports signal
c dialogue-leaning and a/b no-clear-margin, and explicitly does not resolve the split. Table M3's
cell-⑤ signal rows now show the exploratory distances/calls with a `†` post-hoc/exploratory footnote.
Writing follows the no-defensive-negation rule (positive statements; never implies validation).

**Bib.** Added `carletta1996assessing` and `artstein2008intercoder` to `references_v2.bib` for the
exploratory-reanalysis prose.

**Housekeeping.** Fixed three pre-existing dangling refs (`sec:methods-m2`/`sec:methods-m3` →
`sec:method2`/`sec:method3`) that would have rendered as "??". Verified: braces and environments
balanced, no dangling `\ref`, no undefined cite keys, all M3 `\todo`s cleared, all four figure PDFs
present. **Not compiled** — no LaTeX toolchain here; the user should run pdflatex to confirm.

**Still open (unchanged):** git commit (four `.lock` files still block it, nothing committed since
`aecfd6f`); the two non-result citation `\todo`s near the abstract/intro; pdflatex compile check.

## 2026-07-23 (later) — completion-rate metric: FPP-absent documents scored 0 (user decision)

Reverted the FPP-absent handling to the **score-0** convention (an earlier edit had switched it to
exclude-and-report-separately). User decision: the paper is ground truth and originally specified
score-0; it is the simpler, more intuitive convention (a document that opens no adjacency pairs
completes none of them → rate 0, folded into the mean). Aligned everywhere so spec = paper = code:

- `methods.md` §3c and `paper/main_v2.tex` Methods §3c prose rewritten to score 0.
- `signals.cell_completion_rates` now folds FPP-absent docs in as 0.0 (still counts `n_absent` for
  the descriptive share); `run_calibration.py` print relabelled `scored_n` / "(FPP-absent scored 0)".
- Only cell ① has FPP-absent docs (26/600), so only its number moves: completion mean
  **0.0998 → 0.0955**; validity-gate **Cliff's δ 0.4649 → 0.4717** (still ≫ 0.33 floor, gate still
  PASS). Cells ②③④⑤ unchanged; the cell-⑤ exploratory placement is unchanged (poles ③/④ and ⑤ have
  zero FPP-absent docs).
- Table M3 ① updated to 0.0955; Results δ updated to 0.4717; removed the now-moot "deviation
  reconciled" paragraph. Count-matrix cache rebuilt (cell ① rates changed). M3.3 figure + exploratory
  txt/json still show the old cell-① mean until regenerated (pending the figure/table redesign).
- κ reliability gate is unaffected (it does not use the completion rate).
