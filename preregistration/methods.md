# Method specification

The operational specification for the three methods, fixed before the target cell was
measured.

> **On this edition.** This is a condensed and reordered version of the frozen document,
> written for readability. The specifications, thresholds and numbers are unchanged. The text
> as it stood when frozen is in the repository history:
>
> ```bash
> git show 7747aef:methods.md      # this specification, as frozen 2026-07-16
> git show b7f40d0:research_plan.md # the design document it grew out of, 2026-07-10
> ```
>
> What changed after freezing is recorded in [`METHOD_SELECTION.md`](METHOD_SELECTION.md).

## Scope and blindness

Cells ①–④ (`human_monologue`, `human_debate`, `ai_monologue`, `ai_debate`) have known ground
truth and are used to calibrate and gate every method. Decisions in this document may be
informed by them.

Cell ⑤ (`ai_reasoning`) is the target. What must stay blind is any summary statistic computed
on cell ⑤: the distributions, transition matrices, completion rates and JSD distances defined
in §3. Producing the per-sentence tags themselves is mechanical, a fixed prompt at
temperature 0 over a fixed 28-tag set, so generating cell ⑤'s labels is the execution of
Step 2 rather than a breach of the pre-registration.

## Segmentation

Each method segments text as its own source method did. There is no shared splitter.

| Method | Segmentation |
|---|---|
| 1 | Internal to Nath's code: paragraphs by blank line, with the fallbacks in §1 |
| 2 | NLTK Punkt sentence tokenizer, default parameters, applied to the raw text field |
| 3 | None. The tagger segments and labels in the same call |

Method 2 uses Punkt rather than Method 3's LLM segmentation for two reasons: the PAN 2025
data arrives pre-split, so the SSPC authors wrote no general-purpose splitter to reuse, and
routing Method 2 through Method 3's output would tie together two methods intended as
independent checks.

**Text field per cell**

| Cell | Field | Structure |
|---|---|---|
| ① human_monologue | `think_trace` | single blob |
| ② human_debate | `transcript` | newline-joined turns, speaker identity stripped |
| ③ ai_debate | `turns[].text_clean` | explicit `speaker` (A–D) per turn |
| ④ ai_monologue | `transcript` | single blob |
| ⑤ ai_reasoning | `think_trace` | single blob |

Cell ② has no recoverable speaker identity, and cells ①, ④ and ⑤ have no turns. No method
requires speaker identity to run.

## 1. Style-change detection (Nath 2019, PAN)

**Implementation.** `methods/1_style_change_detection/implementation`, Nath's own code.
Windows are paragraphs, described by the top 50 most frequent tokens per document, compared
by Matusita distance, and clustered into a predicted author count.

**Threshold-based clustering (TBC) only.** Nath reports TBC as the best of the three models,
and only TBC carries decision weight here, so window-merge clustering is not run.

**Configuration.** `merge_threshold=50`, `add_node_threshold=50`, `prune=True`,
`number_of_terms=50`, `use_duplication_feature=True`. The 50/50 thresholds are the optimum
Nath reports from a grid search over 5% to 100%. `number_of_terms=50` matches the top-50
most-frequent-tokens description. `use_duplication_feature=True` matches the configuration
that produced the paper's reported test-set accuracy.

**Distance measure.** `distance_measure=matusita_distance`, passed explicitly. The shipped
`main.py` defaults to Manhattan distance, but the paper's reported results used Matusita, and
the vendored package already provides it.

**Windowing**, as implemented in `src/algorithms/preprocessing.py`:

- Text is split on blank lines and the resulting chunks deduplicated, which also discards
  their original order. Order does not affect the result, because TBC consumes only a
  pairwise distance matrix and has no sequence-awareness.
- If the split yields one chunk, the code groups every 10 sentences into a window using
  NLTK's tokenizer.
- If blank lines are present, paragraphs longer than roughly one standard deviation above the
  mean are split into groups of 5 sentences.
- Paragraphs under 200 characters are merged into the previous entry, or the next if there is
  no previous one, repeating until none remain. The shipped code drops them instead, through
  a regex condition that is vacuously true. The paper states merging, and dropping would
  discard a large share of debate turns, which are frequently under 200 characters.
- Turn-structured cells are assembled with turns joined by `\n\n`, so that one turn becomes
  one paragraph.

**Per-document output.** Predicted author count.

**Step 1 gate.** Balanced accuracy, defined as ½·(recall_single + recall_multi), where
recall_single is pooled over cells ①④ and recall_multi over cells ②③. Balanced accuracy is
used rather than pooled accuracy because the cells are class-imbalanced: with roughly 1,200
single-author documents against 1,100 multi-author, a detector labelling everything
single-author scores about 0.52 pooled, which a binomial test against 0.5 can clear on sample
size alone. The same detector scores exactly 0.50 balanced.

The gate is that balanced accuracy significantly exceeds 0.50, tested against a
label-permutation null: shuffle the true labels across documents and recompute, 10,000 draws,
one-sided p < .05. Report both per-class recalls, the per-cell recall breakdown, the
confusion matrix, and a bootstrap 95% CI on balanced accuracy.

Nath's reported 0.85 is not imported as a threshold, being a five-class score on long
StackExchange threads rather than short Game of 24 transcripts.

## 2. Sentence-level style-change detection (PAN 2025 sequential pair classifier)

**Implementation.** `methods/2_stylometric_step_change/implementation/predict.py`. A
pretrained checkpoint over the `StyleDistance/styledistance` sentence encoder, mean-pooled
per sentence, contextualised by a bidirectional LSTM of hidden size 256, scored by an MLP
over concatenated adjacent-sentence representations, one logit per adjacent pair.

**Configuration.** The shipped checkpoint's weights, used without fine-tuning. This is
out-of-domain inference. `block_size=256`.

**Change from the shipped script.** `get_predictions` thresholds at 0.5 and returns only the
binary decision. The per-document metric needs the continuous values, so the raw
`sigmoid(logits)` per adjacent pair is read out of the forward pass before thresholding.

**Per-document output.** Mean of the raw per-adjacent-pair probabilities, a scalar in [0, 1].
Higher means more frequent style switching.

**Length dependence.** Document lengths differ substantially across cells: `ai_reasoning` has
a median of about 10,700 characters against about 6,900 for `ai_debate` and about 860 for
`ai_monologue`. A fixed number of true switch points spread over more sentence pairs produces
a smaller mean, so the raw score is not comparable across cells of different length. Taking
the sum instead fails in the opposite direction, since a constant per-pair false-positive rate
accumulates with pair count.

**Per-pole curves.** Rather than one corrected score, each pole is fitted its own curve on
its own data:

- `ai_debate` (③) is fitted on ③ documents only.
- `ai_monologue` (④) is fitted on ④ documents only, including a check of whether ④ supports a
  length slope at all or whether a flat mean is the better fit.

Every document then receives two distances: `d_dia`, its observed probability minus ③'s curve
at that document's length, and `d_mono`, the same against ④'s curve. This is the `d_mono` /
`d_dia` framework §3d defines for Method 3.

**Functional form.** For each pole separately, fit raw-linear (`probability ~ pairs`),
semi-log (`probability ~ log(pairs)`) and log-log (`log(probability + ε) ~ log(pairs)`, with
ε = 0.001), and keep whichever minimises AIC for that pole. The two poles may take different
forms. Report both comparisons.

**Step 1 gate.** For every calibration document compute `lean = |d_mono| − |d_dia|`, positive
meaning closer to the dialogue curve. The absolute values are required: the signed difference
`d_dia − d_mono` is negative for both genuine dialogue and genuine monologue documents and so
cannot separate them.

The gate is that mean `lean` for cells ②③ exceeds cells ①④, and that Cliff's delta between
the two groups is at least 0.33. Report both.

**Extrapolation.** Both `ai_monologue` and `ai_reasoning` sit past `ai_debate`'s observed
length range, and `ai_reasoning` sits further past `ai_monologue`'s. Figure M2.2 plots both
poles' documents and fitted curves extended to cover cell ⑤'s lengths, with each pole's
observed range shaded, alongside the number of characters by which cell ⑤ exceeds each pole's
observed maximum.

All fits use calibration data only and are frozen before cell ⑤ is scored.

## 3. Dialogue-act tagging (CAMS)

**Implementation.** `methods/3_dialogue_act_tagging/implementation/label_dialogue_acts_v2.py`
with `CAMS_LLM_labeling_prompt.txt`. Every sentence receives exactly one of the 27 CAMS
dialogue-act tags or `none`.

This uses the dialogue-act layer of CAMS only, not its formal adjacency-pair layer, which
requires speaker-turn structure that three of the five cells do not have. "Adjacency pair"
below means a sentence-sequence-level operationalisation.

The unit of analysis is the document. Each signal is computed per document and then summarised
per cell as a mean and a full across-document distribution, so every comparison is between
distributions rather than between two pooled numbers.

Three signals are defined. §3a and §3b are descriptive profile comparisons. §3c tests whether
first pair parts actually receive their answering second pair parts, which is what adjacency
pair theory treats as the hallmark of back-and-forth, and is the primary confirmatory signal.

### 3a. Tag distribution

Per document, the normalised frequency of each of the 28 labels, a probability vector summing
to 1. Averaged within each cell, weighted by sentence count.

### 3b. Tag transition structure

Per document, the empirical bigram transition count over consecutive tags, 28 × 28. Two
normalisations are kept, each with a fixed purpose:

- Row-normalised, for the heatmaps in §5.
- Joint-normalised, as the input to the JSD comparison in §3d, which needs a single
  probability distribution.

Averaged within each cell, weighted by sentence count.

### 3c. Adjacency-pair completion rate (primary signal)

The pair list is derived from CAMS's own category structure rather than from corpus
frequency. CAMS groups its 27 tags into eight functional categories and states that the
relationship between a first pair part and a second pair part is constrained by the type of
first pair part, with first pair parts drawn from the Information-seeking and Directive
categories and second pair parts from the Information-providing and Commissive categories.

| FPP tag | Valid SPP tag(s) | CAMS basis |
|---|---|---|
| `propositionalQuestion` | `answer`, `confirm`, `disconfirm` | yes/no question to answer or (dis)confirmation |
| `setQuestion` | `answer` | wh-question to answer |
| `choiceQuestion` | `answer` | alternative question to answer |
| `checkQuestion` | `confirm`, `disconfirm` | uncertain-belief check to (dis)confirmation |
| `request` | `accept`, `decline`, `conditionalAccept` | Directive to Commissive response |
| `suggest` | `accept`, `decline`, `conditionalAccept` | Directive to Commissive response |
| `offer` | `accept`, `decline`, `conditionalAccept` | Commissive offer to accept/decline |
| `inform` | `agreement`, `disagreement`, `correction`, `autoPositive`, `autoNegative` | statement to (dis)agreement or feedback |
| `greeting` | `greeting` | Social Obligation initiative-response pair |
| `goodbye` | `goodbye` | Social Obligation initiative-response pair |
| `thanking` | `acceptThanking` | Social Obligation pair |
| `apology` | `acceptApology` | Social Obligation pair |

This table is derived from CAMS's stated category mapping and worked examples, so it does not
change when the data is seen.

**Per-document metric.** Of all consecutive tag pairs where the first is a listed FPP, the
fraction where the second is in that FPP's valid-SPP set. A rate in [0, 1] rather than a
count, so it is comparable across documents regardless of how often FPP-type tags occur. A
document with no FPP occurrences completes no pairs and scores 0, and is included in the cell
mean. The FPP-absent share per cell may be reported as context.

The operationalisation is deliberately strict: an FPP counts as completed only when the valid
SPP is the very next tagged utterance, with no insert-expansion tolerated. CAMS's full theory
allows insert-expansions, but detecting them requires the speaker-turn layer three cells lack.
The metric is therefore a conservative lower bound, which can only understate dialogue-ness.

### 3d. Comparison rule

- **Anchors.** The monologue pole is AI monologue (④) and the dialogue pole is AI dialogue
  (③). The human cells are not used to place cell ⑤; they are the Step 1 validity check.
- **Distance.** For the distribution signals, Jensen-Shannon divergence, base 2 and so bounded
  in [0, 1]. It is symmetric, bounded, and defined when a distribution contains zeros. For the
  scalar signal, the absolute difference between cell means.
- **Call.** Compute `d_mono = distance(⑤, ④)` and `d_dia = distance(⑤, ③)`. Cell ⑤ is called
  toward the closer pole, and reported as **no clear margin** when
  `|d_mono − d_dia| / max(d_mono, d_dia) < m`.
- **Setting `m`.** Calibrated separately for each signal from the two poles, using calibration
  data only. Split ③'s documents into two random disjoint halves of equal size, recompute the
  signal's distance between halves, and record the relative gap; repeat for ④; B = 1000.
  Pooling both poles gives a null distribution of the gap produced by sampling noise alone.
  Set `m` to its 95th percentile. This runs on ③ and ④ only and is frozen before Step 2.

### 3e. Step 1 gates

**Labelling reliability.** Hand-label a sample of utterances from each of ①②③④ against the
tagger's output and compute Cohen's κ. If κ < 0.70, Method 3 is invalid and is dropped. The
threshold is the pre-registration in `sources/SOURCES.md` and is the conventional substantial
agreement floor. This is a property of the tagging step, independent of the
monologue/dialogue question.

Sample size per cell is solved from the asymptotic variance formula for Cohen's κ (Fleiss,
Cohen and Everitt, 1969), which takes the tag-frequency marginals as input, using each cell's
own §3a marginals from calibration data. The precision target is a 90% CI with half-width
≤ 0.10, revised 2026-07-17 from an initial 95% and ±0.05 through an intermediate 90% and
±0.08. The revision changes how tightly the measured κ is estimated, not the 0.70 pass/fail
bar, and was decided before any κ was measured. At this setting the required sample sizes are
122, 83, 137 and 168 for cells ①–④, 510 in total.

**Signal validity.** The primary signal §3c must separate the poles in the expected
direction: mean completion rate for cells ②③ must exceed cells ①④. Report Cliff's delta and
the direction. As a consistency check, within-class JSD should be smaller than between-class
JSD, but §3c is the binding gate and §3a/§3b agreement is reported rather than required.

If either gate fails, Method 3 is reported as failed at Step 1 and gets no call on cell ⑤.

## 4. Placing cell ⑤ and combining the methods

Only methods that pass their Step 1 gate get a call on cell ⑤. A method that cannot separate
monologue from dialogue on the four known cells has shown it cannot measure the quantity, so
its reading is discarded rather than averaged in.

Each surviving method places cell ⑤ on the monologue-dialogue axis against its own ④ and ③
anchors:

| Method | Quantity | Pole distance |
|---|---|---|
| 1 | Mean predicted author count | \|mean(⑤) − mean(pole)\| |
| 2 | `d_dia` and `d_mono` against each pole's length-fitted curve | distance to the closer pole |
| 3 | §3c completion rate, with §3a and §3b alongside | as in §3d |

Each method returns one of three verdicts, monologue-leaning, dialogue-leaning, or no clear
margin, using the relative-margin rule of §3d with each signal's own calibrated `m`.

**Combination.** The three methods are independent checks, so the result is the pattern of
their verdicts, reported in full rather than collapsed to a majority. Agreement among
surviving methods is the headline finding, and its strength is that unrelated measures concur.
A split is reported as a split, with each verdict and margin shown, and read as mixed
evidence. No method is weighted above the others and no tie-break is introduced.

> **Clarification added 2026-07-22, after the Method 3 gate result and before any cell-⑤
> statistic was computed.** Method 3 failed its §3e reliability gate with κ = 0.5425 and
> therefore gets no call on cell ⑤, as the first paragraph of this section requires. The
> combination rule does not depend on how many methods survive: the deliverable is still the
> pattern of the surviving verdicts. With two methods, agreement between Methods 1 and 2 is
> the headline finding, and the concurrence is weaker than the three-method version this
> section was drafted against and should be stated as such. A one-to-one split is reported as
> a split. No primary method is designated, no tie-break is introduced, and no threshold
> moves.

## 5. Outputs and figures

Every figure is faceted by cell unless stated, uses the ④ and ③ anchors as reference lines,
and marks cell ⑤ distinctly. Per-cell summaries report the full across-document distribution
rather than a bare mean.

**Method 1**

- Fig M1.1: per-document predicted author count per cell.
- Table M1: per-cell mean count, share called multi-author, per-cell and pooled accuracy,
  confusion matrix, and the test result against chance.

**Method 2**

- Fig M2.1: per-document raw switch probability per cell, and `lean` per cell.
- Fig M2.2: length against probability for ③ and ④ with each pole's fitted curve extended to
  cover cell ⑤'s lengths and each pole's observed range shaded, annotated with how far cell ⑤
  falls past each maximum. Two additions, both descriptive and used in neither the gate nor
  the placement: a context curve fitted on ② and marked as such, and cell ⑤'s own documents
  as a raw scatter.
- Table M2: per-cell mean `lean` and Cliff's delta for the gate, and the functional-form
  comparison per pole.

**Method 3**

- Fig M3.1: the 28-label distribution per cell.
- Fig M3.2: row-normalised transition matrices per cell, plus difference heatmaps (⑤ − ④) and
  (⑤ − ③).
- Fig M3.3: per-document completion rate per cell, annotated with the FPP-absent share.
- Fig M3.4: JSD-to-④ against JSD-to-③ for the unigram and bigram signals, with the diagonal
  marking equal distance.
- Table M3: per-cell mean completion rate and Cliff's delta, κ from the reliability check, and
  `d_mono` / `d_dia` with the resulting call per signal.

**Cross-method**

- Fig X.1: the monologue-dialogue axis normalised so ④ = 0 and ③ = 1, each surviving method's
  cell-⑤ position plotted with its no-clear-margin band.
- Table X: methods against passed Step 1, cell-⑤ verdict, and margin.

## 6. Free choices, and how each was fixed

Everything else in this document is taken from a source: Nath's 50/50 thresholds, Matusita
distance and TBC primacy; the PAN 2025 shipped checkpoint; CAMS's tag set and FPP to SPP
mapping; and the κ ≥ 0.70 floor from `SOURCES.md`. The following were the remaining free
choices, and fixing them is what makes the commit a pre-registration.

| Choice | Resolution |
|---|---|
| Method 1 gate | Balanced accuracy against a label-permutation null, replacing an imported 80% floor (§1) |
| Method 2 gate strength | Direction plus Cliff's delta ≥ 0.33 (§2) |
| Method 2 equal-slope tolerance | Not applicable. Each pole is fitted independently, so there is no shared slope to reconcile (§2) |
| Method 3 comparison margin | Per-signal margin from a bootstrap noise floor on ③ and ④, replacing a flat m = 0.10 (§3d) |
| Method 3 reliability sample size | Computed from Cohen's κ variance formula, replacing a flat 50 per cell (§3e) |
