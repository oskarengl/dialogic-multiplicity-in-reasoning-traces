# Deviations from the pre-registration

[`methods.md`](methods.md) is the frozen method specification. It was committed **before**
the target cell was touched, and the commits are the record:

| Commit | Date | What it froze |
|---|---|---|
| `b7f40d0` | 2026-07-10 | Method specifications for all three methods, with every open decision filled in |
| `7747aef` | 2026-07-16 | Froze Methods 1–3 before running cell ⑤ (`ai_reasoning`) |
| `fba456b` | 2026-07-17 | Re-registered the Method 1 gate (balanced accuracy with a label-permutation null) |

Commit hashes changed when this repository was prepared for release; the dates, messages
and order are unchanged. See [the release note](#history-note) below.

---

## The one substantive deviation: the validity check replaced the per-method gates

**Pre-registered.** Each method had its own statistical gate, and only a method passing its
own gate could speak about cell ⑤:

| Method | Pre-registered gate |
|---|---|
| 1 | Balanced accuracy significantly above 0.50, tested against a label-permutation null |
| 2 | Mean `lean` for dialogue cells ②③ above monologue cells ①④, **and** Cliff's δ ≥ 0.33 |
| 3 | (a) Tagger–human Cohen's κ ≥ 0.70, **and** (b) completion rate separating dialogue from monologue within each producer |

**What happened.** Method 1 passed its gate. Method 3 failed gate (a): measured κ = 0.5425,
below the 0.70 floor. Under the pre-registration as written, Method 3 got no call on cell
⑤ — `methods.md` records this explicitly in the clarification dated 2026-07-22.

**The problem.** The gates admitted Method 1, which reads a majority of four-way debates as
single-author and *all 500* human debates as single-author — it places both known dialogue
cells on the monologue side. And they excluded Method 3, which sorts all four known cells
correctly. A gate that passes a method unable to recognise a dialogue, while failing one
that can, is not measuring the thing the study needs.

**What is reported instead.** A single check applied identically to all three methods: *a
method is carried forward only if it sorts the four known cells correctly into monologue
and dialogue.* Under it, Methods 2 and 3 pass and Method 1 fails. This is stated in the
paper (§3, "Deviation from the pre-registered gates") and Method 1's reading of the traces
is reported in brackets in Table 1 for completeness.

**How to read this.** The change was made after the gate results were known, which is
exactly the situation pre-registration exists to constrain. It is not defensible as a
blind choice, and the paper does not present it as one. What can be checked is that the
replacement rule is simpler than what it replaced, is applied identically to all three
methods, and is stated in advance of the cell-⑤ numbers rather than tuned to them. The
κ = 0.54 reliability shortfall is not waved away: it is reported in §4.1 and named as the
weakest link in Method 3's chain.

An earlier treatment reported Method 3's cell-⑤ reading as a separately sectioned
exploratory analysis that broke no ties. Artifacts from that treatment remain in the
repository — `scripts/place_cell5_method3_exploratory.py` and
`outputs/placement/cell5_method3_exploratory.json` — and the final paper supersedes it by
carrying Method 3 forward on the validity check.

---

## Smaller precisifications

**Method 2, model selection across transforms.** `methods.md` says the length curve per
pole is chosen by AIC. The three candidate forms (linear, semi-log, log-log) use different
response scales, so their AICs are not comparable. Selection is done instead by residual
sum of squares in the original score units, back-transforming the log-log predictions onto
the common scale. Noted in `local_changes/run_calibration.py` in Method 2.

**Method 3, reliability sample precision.** The precision target around κ was loosened
during pre-registration, from a 95% CI half-width of ±0.05 to a 90% CI half-width of ±0.10
(revised 2026-07-17 through an intermediate ±0.08). Each revision was made blind to any
measured κ and changes only how tightly κ is estimated, never the 0.70 pass/fail bar. The
bar itself was never moved — it was abandoned along with the rest of the per-method gates,
as above.

**Method 1, gate replacement during pre-registration.** The original imported 80% accuracy
threshold was replaced by balanced accuracy against a permutation null (commit `fba456b`,
2026-07-17) because pooled accuracy on an imbalanced set could be cleared by a system that
detected no dialogue at all. This tightened the gate and happened before any cell-⑤
statistic was computed.

---

## Corrections applied after freezing

**Speaker-label leak.** Both dialogue cells carried speaker labels, which hand a style-based
method the number of voices directly. They were removed and all three methods were re-run
on the cleaned data (commit `77a29ae`, 2026-07-22). Pre-fix files are preserved under
`data/archive/` as `*.PRE_SPEAKERFIX_2026-07.jsonl`.

**Method 1 implementation patches.** Method 1's reported failure comes from patched
upstream code, not from the PAN 2019 system as submitted. One patch alters the algorithm:
clustering thresholds are divided by cluster size alone rather than by cluster size times
average intra-cluster distance. See
[`../methods/1_style_change_detection/local_changes/README.md`](../methods/1_style_change_detection/local_changes/README.md).

---

## History note

This repository was prepared for public release from the working repository. Access-restricted
and copyrighted third-party material (the PAN 2019 corpus, literature PDFs) was removed from
every commit, so commit hashes differ from those in the private working repository. Commit
dates, messages, authorship and order are preserved, and the pre-registration commits above
still precede the commits that produced the cell-⑤ results.
