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
reliability sample size is now computed from Cohen's κ asymptotic variance formula (target: 95% CI
half-width ≤ 0.05) instead of a flat 50/cell default.

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
