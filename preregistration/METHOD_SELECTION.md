# Method Selection

A method is carried forward only if it sorts the four known cells correctly into monologue
and dialogue. The same check is applied to all three methods.

Under it, Method 2 and Method 3 pass and Method 1 fails. Method 1 reads all 500 human
debates and a majority of the AI debates as single-author, placing both known dialogue cells
on the monologue side. Its reading of the traces appears in brackets in Table 1 of the paper
and carries no weight.

## This replaced a set of per-method gates

[`methods.md`](methods.md) is the frozen method specification. It gave each method its own
statistical gate:

| Method | Pre-registered gate |
|---|---|
| 1 | Balanced accuracy significantly above 0.50, against a label-permutation null |
| 2 | Mean `lean` for dialogue cells ②③ above monologue cells ①④, and Cliff's δ ≥ 0.33 |
| 3 | (a) Tagger to human Cohen's κ ≥ 0.70, and (b) completion rate separating dialogue from monologue within each producer |

Under those gates Method 1 passed, and Method 3 failed gate (a) with κ = 0.5425.
`methods.md` records in a clarification dated 2026-07-22 that Method 3 therefore gets no
call on cell ⑤.

The paper gives the reason for the change in §3, "Deviation from the pre-registered gates":
the gates admitted a method that reads most debates as the work of a single author, and
excluded a method that correctly separates all four known cells. The check was therefore
simplified: a method passes if it correctly separates the monologue from the dialogue
corpora for both the human and the AI datasets.

**The change was made after the gate results were known.** The check that replaced them is
defined only on the four known cells and does not refer to cell ⑤, but swapping which
methods qualify does change what the paper reports about cell ⑤.

Method 3's κ shortfall is reported. §4.1 reports 74.2% agreement on 503 utterances,
κ = 0.54, or 0.62 tree-weighted, records that 101 of 130 disagreements turn on the general
`inform` label against a more specific one, and names the labels as the weakest link in
Method 3's chain.

An earlier treatment reported Method 3's cell-⑤ reading as a separately sectioned
exploratory analysis. Artifacts from it remain at
`scripts/place_cell5_method3_exploratory.py` and
`outputs/placement/cell5_method3_exploratory.json`.

## When the specification was frozen

| Commit | Date | What it froze |
|---|---|---|
| `b7f40d0` | 2026-07-10 | `research_plan.md`, the design document, including a section pre-registering the three methods. Retrieve with `git show b7f40d0:research_plan.md` |
| `7747aef` | 2026-07-16 | `methods.md`, the operational specification that superseded that section, before cell ⑤ (`ai_reasoning`) was measured |
| `fba456b` | 2026-07-17 | The re-registered Method 1 gate: balanced accuracy with a label-permutation null |

Commit hashes changed when this repository was prepared for release. Dates, messages and
order are unchanged. See [History note](#history-note).

`outputs/placement/margins_frozen.txt` records that the no-clear-margin bands were fixed
while no cell-⑤ results existed on disk, at 2026-07-22T15:53:42Z with seed `20260722`. The
placement was computed at 18:00:23Z the same day.

## Smaller precisifications

**Method 2, model selection across transforms.** `methods.md` specifies AIC for choosing the
length curve per pole. The three candidate forms use different response scales, so their
AICs are not comparable. Selection uses residual sum of squares in the original score units,
back-transforming the log-log predictions. Documented in Method 2's `run_calibration.py`.

**Method 3, reliability sample precision.** The precision target around κ was revised during
pre-registration from a 95% CI half-width of ±0.05 to 90% and ±0.10, through an intermediate
±0.08 (2026-07-17). `methods.md` records that each revision changes how tightly κ is
estimated, not the 0.70 pass/fail bar.

**Method 1, gate replacement during pre-registration.** The imported 80% accuracy threshold
was replaced by balanced accuracy against a permutation null (commit `fba456b`, 2026-07-17).
`methods.md` §1 records the reason: pooled accuracy on an imbalanced set could be cleared by
a system that detected no dialogue at all.

## Corrections applied after freezing

**Speaker-label leak.** Speaker labels were removed from both dialogue cells and all three
methods were re-run on the cleaned data (commit `77a29ae`, 2026-07-22); `git show 77a29ae`
gives the change. The paper states in §2 that labels were removed from both dialogue
corpora.

**Method 1 implementation patches.** Method 1 was run on patched upstream code. One patch
changes the algorithm: clustering thresholds are divided by cluster size rather than by
cluster size times average intra-cluster distance. See
[`../methods/1_style_change_detection/local_changes/README.md`](../methods/1_style_change_detection/local_changes/README.md).

## History note

This repository was prepared for public release from the working repository. The PAN 2019
corpus, which is access-restricted, and literature PDFs under publisher copyright were
removed from every commit, so commit hashes differ from those in the working repository.
Commit dates, messages, authorship and order are preserved.

`methods.md` was also condensed for readability during release preparation. Its
specifications, thresholds and numbers are unchanged, and the text as frozen is retrievable
with `git show 7747aef:methods.md`.
