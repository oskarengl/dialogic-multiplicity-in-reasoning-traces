# Deviations from the pre-registration

[`methods.md`](methods.md) is the frozen method specification. The commits that froze it:

| Commit | Date | What it froze |
|---|---|---|
| `b7f40d0` | 2026-07-10 | Method specifications for all three methods, with open decisions filled in |
| `7747aef` | 2026-07-16 | Methods 1 to 3, before running cell ⑤ (`ai_reasoning`) |
| `fba456b` | 2026-07-17 | Re-registered the Method 1 gate (balanced accuracy with a label-permutation null) |

Commit hashes changed when this repository was prepared for release. Dates, messages and
order are unchanged. See [History note](#history-note).

## The validity check replaced the per-method gates

**Pre-registered.** Each method had its own gate, and only a method passing its own gate
could speak about cell ⑤:

| Method | Pre-registered gate |
|---|---|
| 1 | Balanced accuracy significantly above 0.50, against a label-permutation null |
| 2 | Mean `lean` for dialogue cells ②③ above monologue cells ①④, and Cliff's δ ≥ 0.33 |
| 3 | (a) Tagger to human Cohen's κ ≥ 0.70, and (b) completion rate separating dialogue from monologue within each producer |

**Results under those gates.** Method 1 passed. Method 3 failed gate (a) with κ = 0.5425.
`methods.md` records in a clarification dated 2026-07-22 that Method 3 therefore gets no
call on cell ⑤.

**What the paper reports instead.** A single check applied identically to all three methods:
a method is carried forward only if it sorts the four known cells correctly into monologue
and dialogue. Under it, Methods 2 and 3 pass and Method 1 fails.

The paper states the change and its reason in §3, "Deviation from the pre-registered gates":
the gates admitted a method that reads most debates as the work of a single author, and
excluded a method that correctly separates all four known cells. Method 1's reading of the
traces is reported in brackets in Table 1.

Method 3's κ shortfall is reported in §4.1, which records 74.2% agreement on 503 utterances,
κ = 0.54, or 0.62 tree-weighted, and states that 101 of 130 disagreements turn on the general
`inform` label against a more specific one.

An earlier treatment reported Method 3's cell-⑤ reading as a separately sectioned
exploratory analysis. Artifacts from it remain at
`scripts/place_cell5_method3_exploratory.py` and
`outputs/placement/cell5_method3_exploratory.json`.

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
methods were re-run on the cleaned data (commit `77a29ae`, 2026-07-22). Pre-fix files are at
`data/archive/*.PRE_SPEAKERFIX_2026-07.jsonl`. The paper states in §2 that labels were
removed from both dialogue corpora.

**Method 1 implementation patches.** Method 1 was run on patched upstream code. One patch
changes the algorithm: clustering thresholds are divided by cluster size rather than by
cluster size times average intra-cluster distance. See
[`../methods/1_style_change_detection/local_changes/README.md`](../methods/1_style_change_detection/local_changes/README.md).

## History note

This repository was prepared for public release from the working repository. The PAN 2019
corpus, which is access-restricted, and literature PDFs under publisher copyright were
removed from every commit, so commit hashes differ from those in the working repository.
Commit dates, messages, authorship and order are preserved.
