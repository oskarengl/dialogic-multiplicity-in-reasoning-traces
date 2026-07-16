# Methods (frozen specification)

This document is the operational, run-it-as-written specification for the three methods in
`research_plan.md`. Nothing in here should change once it has been run against `ai_reasoning`
(cell ⑤, the target). If something has to change after that point, the change and its reason go
in `STATUS.md`, not here.

**What is allowed to inform decisions in this document, and what isn't.** Cells ①–④
(`human_monologue`, `human_debate`, `ai_monologue`, `ai_debate`) have known ground truth and are
used to calibrate and gate every method — it is legitimate for the numbers below to be shaped by
looking at those four. Cell ⑤ (`ai_reasoning`) is the target and must stay untouched by anything
in this document until Step 2 runs. The firewall to protect is a specific one, so state it
exactly: what must stay blind is any *summary statistic computed on cell ⑤'s labels* (the
distributions, transition matrices, completion rates and JSD distances defined in §3), because
those are what a forking-paths choice would quietly tune against. Producing the per-sentence tags
themselves is mechanical — a fixed prompt at temperature 0 with a fixed 28-tag set, no decision
that could look at an outcome — so generating cell ⑤'s labels is the execution of Step 2, not a
breach of pre-registration.

Current state (verified 2026-07-15): Method 3's tagger is mid-run across all cells — cells ①–④
complete or nearly so (600 / 500 / 585 / 594 files) and cell ⑤ actively tagging (≈347 / 600 and
climbing). A repository-wide search finds **no** transition-matrix, completion-rate, distribution
or JSD artifact for any cell, cell ⑤ included — i.e. the labels exist but nothing in §3 has been
computed on them yet. That is the state this pre-registration needs, and it supersedes the earlier
"one smoke-test file" note. Two things to do before treating this document as frozen: (1) create
`STATUS.md` and log that cell ⑤ was tagged as the mechanical Step-2 label pass, with the observed
file counts and an explicit line confirming no §3 summary has been computed on cell ⑤; (2) commit
this file — that commit is the pre-registration timestamp, and it must land before any §3 statistic
is first computed on cell ⑤.

---

## 0. Shared segmentation (Methods 1 and 2 only — Method 3 needs no separate step)

Revised after discussion: there is no single shared splitter used by all three methods. Each
method's segmentation is decided by what that method actually needs and what stays closest to how
it was originally validated, not by convenience of sharing one tool.

- **Method 3 has no dedicated sentence-splitting step, and never did.** `label_dialogue_acts_v2.py`
  sends the LLM the whole document once; the same call segments it into utterances and tags each
  one — per its own docstring, "the LLM ... is responsible for sentence splitting." There is no
  separate splitter here to point at or borrow; segmentation is a side effect of tagging, not a
  reusable module.
- **Method 2 gets its own independent, standard sentence splitter — not Method 3's LLM output.**
  Checked the actual PAN25 shared-task data (`pan25-multi-author-analysis.zip`, bundled in
  `implementation/`): it arrives pre-split one sentence per line by the task organizers, with a
  separate truth file marking which adjacent pairs are style changes. The SSPC authors never wrote
  a general-purpose sentence splitter — there was nothing to reuse from them for arbitrary new
  text. Relying on Method 3's LLM segmentation for this would make Method 2 depend on an LLM call
  100% of the time with no fallback, and would tie two methods together that are supposed to be
  independent checks on each other. Instead: **NLTK's Punkt sentence tokenizer, default parameters,
  unmodified** — deterministic, unsupervised, no thresholds to tune, and the standard choice in the
  authorship/stylometry literature this project already cites (Stamatatos 2008). Applied directly
  to each cell's raw text field (§ table below), independent of Methods 1 and 3.
- **Method 1 gets none of the above.** No LLM call, no dependency on Method 2 or 3 output — its
  windowing is fully independent and mechanical (see §1, revised). That independence is the point:
  Method 1's value partly rests on being close to Nath (2019) as actually run and reported, and
  routing its input through an LLM-based splitter neither paper used would be a bigger deviation
  than anything about window size.

**Per-dataset text field** (for the record, from `data/00_core-2x2/README.md` and the processed
files):

| Cell | Field | Structure |
|---|---|---|
| ① human_monologue | `think_trace` | single blob |
| ② human_debate | `transcript` | newline-joined turns, speaker identity stripped |
| ③ ai_debate | `turns[].text_clean` | explicit `speaker` (A–D) per turn |
| ④ ai_monologue | `transcript` | single blob |
| ⑤ ai_reasoning | `think_trace` | single blob |

Note cell ② has no recoverable speaker identity (`speaker_labels_removed` in `processing_info`)
and cell ① / ④ / ⑤ have no turns at all. None of the three methods below require speaker identity
to run — Method 3 in particular works on the DA-tag sequence only, not on the formal
FPP/SPP-by-different-speaker layer of CAMS (see §3) — so this is a property to report, not a
blocker.

---

## 1. Method 1 — Style-change detection (Nath 2019, PAN)

**Implementation**: `methods/1_style_change_detection/implementation` (Nath's own code). Confirmed
from `nath_2019.pdf`: windows = paragraphs, merged/split to reasonable length; top-50
most-frequent-tokens (MFT) per *document* (not corpus); Matusita distance between window feature
vectors; clustering to a predicted author count.

**TBC only — WMC dropped.** `nath_2019.pdf` §5 states plainly: "We found that, TBC performs the
best out of the three models under both the scenarios" (with and without the duplicate-sentence
feature). Since WMC carries no decision weight in this design (only TBC gates/verdicts), keeping it
around would just add a second number to explain without adding anything to what's actually
decided. TBC only, everywhere below.

**Fixed hyperparameters**, checked directly against `nath_2019.pdf` §4: the 50%/50%
add-window/merge-cluster thresholds are not arbitrary defaults — the paper reports a grid search
from 5% to 100% and reports 50% as the optimum for both ("We observed the optimum performance at
50% for both the thresholds"). `number_of_terms=50` matches "top 50 Most Frequent Tokens ... from
each document (and not the whole corpus)." `use_duplication_feature=True` matches the paper's
*Improved Results* configuration (Table 5), which is the one that reaches the reported test-set
(TIRA) accuracy below — not the weaker *Initial Results* (Table 4) baseline. Final config:
`merge_threshold=50`, `add_node_threshold=50`, `prune=True`, `number_of_terms=50`,
`use_duplication_feature=True`.

**Distance measure — corrected, not just flagged.** `src/main.py`'s own default argument is
`manhattan_distance`, but the paper's reported results (Tables 4 and 5, and the Matusita distance
description in §3.1) were obtained with Matusita distance. The vendored package already ships
`preprocess_NLP_pkg.matusita_distance` (confirmed by reading
`.../implementation/venv/Lib/site-packages/preprocess_NLP_pkg/distance_measures.py`), so this is a
one-argument fix, not new code: **pass `distance_measure=matusita_distance` explicitly**, rather
than keeping `main.py`'s leftover default. This is a case where matching the original method
*requires* overriding the shipped script's default, not preserving it — the default in the file
just isn't what was evaluated.

**Windowing — verified against the actual code** (`src/algorithms/preprocessing.py`, called by both
TBC and WMC), not just the paper's prose, since the two don't fully agree:

- The text is split on blank lines (`\n\n` or a newline-whitespace-newline pattern), and the
  resulting chunks are deduplicated via Python's `set()`, which also discards their original order.
  This is part of the shipped, validated algorithm, not something we introduced — order turns out
  not to matter downstream (see below), so this is kept exactly as-is.
- **If that split yields only one chunk** (no blank lines anywhere — most of `human_monologue`,
  since it's continuous transcribed speech), the code takes a distinct branch: it runs NLTK's
  sentence tokenizer and groups every **10 sentences** into one window. This is part of Nath's own
  shipped algorithm, not a splitter we added — it only applies inside Method 1's own code path and
  creates no dependency on Methods 2 or 3.
- **If there are blank lines** (`ai_monologue`, `ai_reasoning`): paragraphs longer than roughly one
  standard deviation above the mean get split into groups of 5 sentences (NLTK again) — also part
  of the shipped algorithm.
- **The one genuine bug, fixed rather than kept**: the paper states short paragraphs (under 200
  characters) get merged into the previous one; the actual shipped filter instead *drops* them
  outright, due to a regex condition that's vacuously always true. Faithfully reproducing this
  specific behavior isn't the same kind of "fidelity" as the rest of the list above — the paper
  never intended it, and unlike on PAN's data (minimum document length 339 tokens, so a document
  being entirely sub-200-char paragraphs was essentially impossible), it's a live risk here: turns
  in `ai_debate`/`human_debate` are frequently under 200 characters, and losing them would quietly
  undo the turn-as-paragraph fidelity fix above. **Fix**: implement the paper's own stated
  behavior — walk the (already-deduplicated) paragraph list, and any paragraph under 200 characters
  gets concatenated onto the prior list entry (`\n\n`-joined), or onto the next entry if it's first
  in the list with no prior one, repeated until nothing under 200 chars remains. This is well-defined
  without needing to reconstruct true document order, because TBC only ever consumes a pairwise
  distance matrix between windows — there is no sequence-awareness in the clustering step at all
  (unlike Method 2's BiLSTM), so "merge with previous" only needs to be a fixed, deterministic rule,
  not a claim about which paragraph truly preceded which.
- **Turn-structured cells** (`ai_debate`: each element of `turns[]`; `human_debate`: each
  newline-separated line in `transcript`) get one turn/line = one paragraph — the faithful analog of
  a PAN post. Concretely, this requires assembling the input text with turns joined by `\n\n` (not
  `\n`), since the tokenizer above only ever takes one raw string and finds paragraphs via blank-line
  splitting itself; it can't accept a pre-split list. This step wasn't specified before and is added
  here because otherwise "one turn = one paragraph" doesn't actually happen.
- No sentence-level information from Method 2 or Method 3 enters Method 1 at any point (§0) — the
  NLTK calls above are internal to Nath's own code, not shared with our other methods.

**Per-document output**: predicted author count (TBC).

**Step 1 pass/fail rule — significance against chance, not an imported round number.** Each
calibration cell has a uniform true label, so "accuracy" is only meaningful pooled across all four
cells (documents from ①④ truly single-author, ②③ truly multi-author). Rather than importing Nath's
own 0.85 test-set accuracy as a floor — a number measured on a 5-class task in a very different
domain (long StackExchange threads vs. short Game-of-24 transcripts), which isn't a fair transplant
either way — the gate is: **pooled binary accuracy across the four cells is significantly better
than chance** (binomial test against a 50% baseline, one-sided, p < .05). Report the pooled
accuracy, the per-cell breakdown, and a confusion matrix alongside, so the *size* of the effect is
visible even though the gate itself doesn't hinge on a specific percentage. This mirrors how
Methods 2 and 3's gates already work (direction + effect size, no invented floor) — Method 1 was the
only one still importing a point estimate from someone else's domain.

---

## 2. Method 2 — Sentence-level style-change detection (PAN 2025 sequential pair classifier)

**Implementation**: `methods/2_stylometric_step_change/implementation/predict.py` — a pretrained
checkpoint (`model.ckpt`) on top of the `StyleDistance/styledistance` sentence encoder, mean-pooled
per sentence, contextualized by a bidirectional LSTM (hidden size 256), scored by an MLP over
concatenated adjacent-sentence representations, one logit per adjacent sentence pair.

**Fixed hyperparameters**: the shipped checkpoint's own trained weights, used as-is (no
fine-tuning on our data — this is out-of-domain inference, which is itself worth stating plainly
in the write-up). `block_size=256`.

**Change from the shipped script, needed for our metric**: `predict.py`'s `get_predictions`
thresholds at 0.5 and only returns the binary decision. `research_plan.md` calls for "averaging
that probability across the whole text," which needs the raw `sigmoid(logits)` per adjacent pair,
not the post-threshold 0/1. Concretely: call `model.forward(...)`, apply `torch.sigmoid`, and keep
the continuous per-pair values before any thresholding — a one-line change to what's read out of
the forward pass, not a change to the model itself.

**Per-document output**: mean of the raw per-adjacent-pair probabilities across the whole document
— a single scalar in [0, 1] per document. Higher = more frequent/likely style switching. This is the
**raw** score; a length-adjusted version is defined below and is the one actually used for
comparisons.

**Length confound — verified, not hypothetical, and corrected.** Checked actual document lengths
across all five cells: `ai_reasoning` (the target) has a median of ~10,700 characters, longer than
*both* poles it gets compared against (`ai_debate` ~6,900, `ai_monologue` ~860 median) — over 10x
longer than the monologue pole. This matters because the raw mean is diluted by length: if genuine
style-switch points are closer to a roughly fixed number of discrete events than a constant
per-pair rate, the same number of true switches spread over more sentence pairs produces a smaller
mean, regardless of whether the model is working correctly — the identical dilution problem already
handled in Method 3 by conditioning the completion rate on FPP-occurrence (§3c). Simply switching
from mean to sum doesn't fix this cleanly either — a sum stops dividing by pair count, so it swings
to the opposite failure mode (even a small constant per-pair false-positive rate accumulates into a
large sum purely from having many pairs, biasing long documents toward looking dialogue-like
instead). Neither raw statistic is safe without checking what the length relationship actually looks
like in our data.

**No universal correction — each pole gets its own curve, and Method 2 places cell ⑤ the same way
every other method does.** An earlier draft of this section computed one "adjusted score"
(`observed − ai_debate's curve(length)`) and applied it to every document, including monologue-type
ones. That's wrong: `ai_debate`'s curve describes what dialogic switching looks like at a given
length, so subtracting it from a monologue document mostly measures the class gap, not a length
correction — and it does nothing to remove whatever length-drift might exist *within* monologue-type
documents specifically, which is exactly the risk that matters for a monologue-shaped target. The
fix is to not build a single corrected metric at all. Instead:

- **Fit `ai_debate` (③) its own curve**, on ③ data only, as before.
- **Fit `ai_monologue` (④) its own curve**, on ④ data only, completely independently — including
  checking, via the same model-comparison discipline, whether ④'s data even supports a length slope
  at all or whether a flat mean is the honest fit (expected, since ④'s true switch-count is ~0 by
  construction, but checked rather than assumed — if ④ does show a real slope, that's a reportable
  finding in its own right, not a modeling failure).
- **Every document then gets two distances, not one score**: `d_dia` = observed probability minus
  `ai_debate`'s curve evaluated at that document's own length, and `d_mono` = observed probability
  minus `ai_monologue`'s curve evaluated at that document's own length. This is the same `d_mono`/
  `d_dia` nearest-pole framework §3d already defines for Method 3 — Method 2 should use the identical
  concept instead of a bespoke one, evaluated at each document's actual length rather than at the
  pole's own average length, which is what makes it length-aware.

**Functional form — settled by model comparison on each pole's own data, not asserted.** A plausible
mechanism (fixed switch-count diluted by pairs) suggests log-log
(`log(probability) ≈ constant − slope × log(pairs)`) for a cell with genuine switching, but a
derivation being plausible isn't the same as it being correct. So, separately for ③ and for ④: fit
raw-linear (`probability ~ pairs`), semi-log (`probability ~ log(pairs)`), and log-log
(`log(probability + ε) ~ log(pairs)`, `ε = 0.001`), and keep whichever minimizes AIC for that pole.
The two poles are allowed to land on different functional forms — there's no reason to assume they
must match, and forcing them to would reintroduce the exact cross-class assumption just removed.
Report both comparisons.

**Step 1 pass/fail rule**: for every calibration document, compute `lean = |d_mono| − |d_dia|`
(positive = closer to the dialogue curve than the monologue curve, i.e. leans dialogue; negative =
leans monologue) — exactly the same quantity §4 will compute for cell ⑤. Using the signed difference
`d_dia − d_mono` instead would not work: a genuine dialogue document has small `d_dia` and large
positive `d_mono`, giving a *negative* signed difference, and a genuine monologue document has large
negative `d_dia` and small `d_mono`, which is *also* negative — the signed version can't tell the two
apart, only the absolute-value version can. **Gate: mean `lean` for ②③ (dialogue) must exceed ①④
(monologue) (direction), and Cliff's delta between the two groups must be ≥ 0.33.** Report both.

**Extrapolation risk — shown, not hidden behind a single number.** Both `ai_monologue` and
`ai_reasoning` sit at lengths past `ai_debate`'s observed range, and `ai_reasoning` sits past
`ai_monologue`'s observed range even more severely (checked directly: `ai_debate`'s own length range
actually reaches further into `ai_reasoning`'s territory than `ai_monologue`'s does). Rather than an
arbitrary cutoff for "too far," Fig M2.2 plots both poles' calibration documents and both fitted
curves extended out to cover cell ⑤'s length, with each pole's own observed range shaded — so exactly
how far each curve is being stretched is visible directly. Alongside it, one concrete number: how far
past each pole's own observed maximum length cell ⑤ falls.

Because every fit above uses only calibration data and is frozen before cell ⑤ is ever scored, none
of this reopens the blindness question — it's the same "decide the rule from calibration, apply
mechanically to the target" pattern used everywhere else in this document.

---

## 3. Method 3 — Dialogue-act tagging (CAMS)

**Implementation**: `methods/3_dialogue_act_tagging/implementation/label_dialogue_acts_v2.py` +
`CAMS_LLM_labeling_prompt.txt` (full label runs on all four calibration cells; exact per-cell file
counts are logged in `STATUS.md` rather than hard-coded here, since they drift as the run finishes).
Every sentence gets exactly one of the 27 CAMS DA tags (or `none`). This uses only the DA layer of
CAMS, not its formal AP layer (FPP/SPP-base/pre/insert/post) — CAMS's own AP layer requires
speaker-turn structure that three of our five cells don't have (§0), so "adjacency pair" below
means a fixed, sentence-sequence-level operationalization, not the full CAMS AP annotation.

This is the method with the most researcher degrees of freedom in the original plan, so it is split
into three descriptive signals (§3a–§3c) and one fixed comparison rule (§3d) that turns them into a
monologue/dialogue call. Every one of them is computed identically across all five cells, entirely
from the CAMS tag set — there is no per-cell judgment call and nothing in §3a–§3d is chosen by
looking at any cell's tags, calibration or target. **The unit of analysis is the document**: each
signal is computed per document, then summarised per cell (mean and full distribution across that
cell's documents), so every comparison is a comparison of distributions, never of two single
pooled numbers.

The three signals answer three progressively stronger questions, and it is worth being explicit
about which one carries the argument. §3a (what tags occur) and §3b (what follows what) are
descriptive profile comparisons — they show whether cell ⑤ *looks* like a monologue or a dialogue
in aggregate, but a monologue that happens to contain many questions could score "dialogue-ish" on
them. §3c (do question/request/offer FPPs actually get their answering SPP in the very next
utterance) is the one that tests the thing adjacency-pair theory says is the hallmark of genuine
back-and-forth, so **§3c is Method 3's primary confirmatory signal; §3a and §3b are supporting
descriptive context.**

### 3a. DA-tag distribution (unigram profile)

For every document, compute the normalized frequency of each of the 28 labels (27 CAMS tags +
`none`): a 28-dimensional probability vector summing to 1. Average within each cell (weighted by
sentence count) to get one 28-vector per cell. This is the "compare the distributions of labels"
analysis: it asks whether cell ⑤'s mix of conversational functions resembles the monologue cells or
the dialogue cells. Purely descriptive; the only input is the tag set, which is CAMS's.

### 3b. DA-tag transition structure (bigram profile)

For every document, build the empirical bigram transition count over consecutive DA tags
(28 × 28, including `none`): entry `(i,j)` = number of times tag `i` is immediately followed by tag
`j`. This is the "which tag is most often followed by which" / pattern analysis. Two normalized
forms are kept, each with a fixed purpose so there is no choice to make at analysis time:

- **Row-normalized transition matrix** (each row sums to 1) — the conditional "given tag `i`, what
  comes next" view, used for the interpretable heatmaps in §5.
- **Joint-normalized matrix** (whole matrix sums to 1) — the bigram distribution, used as the input
  to the JSD comparison in §3d, because JSD needs a single probability distribution.

Average the per-document matrices (weighted by sentence count) within each cell to get one 28×28
matrix per cell, in both normalizations. Purely descriptive; requires no researcher choice beyond
the CAMS tag set.

### 3c. Canonical adjacency-pair completion rate (primary signal)

This is the piece the discussion flagged as needing the data to decide ("which adjacency pairs to
use"). It does not, if the pair list is derived from CAMS's own category structure instead of from
corpus frequency. CAMS groups its 27 DA tags into eight functional categories and states the
governing regularity directly: "the relationship between FPP and SPP is constrained by the type of
FPP produced, i.e. a question followed by an answer", with FPPs drawn from the Information-seeking
and Directive categories and their SPPs from the Information-providing and Commissive categories
(verbatim from `CAMS_LLM_labeling_prompt.txt`). That yields a fixed FPP → {valid SPP} table,
decided now, from the source document, not from any of our five datasets:

| FPP tag | Valid SPP tag(s) | CAMS basis |
|---|---|---|
| `propositionalQuestion` | `answer`, `confirm`, `disconfirm` | yes/no question → answer or (dis)confirmation |
| `setQuestion` | `answer` | wh-question → answer |
| `choiceQuestion` | `answer` | alternative question → answer |
| `checkQuestion` | `confirm`, `disconfirm` | uncertain-belief check → (dis)confirmation |
| `request` | `accept`, `decline`, `conditionalAccept` | Directive → Commissive response |
| `suggest` | `accept`, `decline`, `conditionalAccept` | Directive → Commissive response |
| `offer` | `accept`, `decline`, `conditionalAccept` | Commissive offer → accept/decline |
| `inform` | `agreement`, `disagreement`, `correction`, `autoPositive`, `autoNegative` | statement → (dis)agreement / feedback |
| `greeting` | `greeting` | Social Obligation initiative-response pair |
| `goodbye` | `goodbye` | Social Obligation initiative-response pair |
| `thanking` | `acceptThanking` | Social Obligation pair |
| `apology` | `acceptApology` | Social Obligation pair |

This table is frozen. It is derived only from CAMS's stated category mapping and its worked
examples, so it does not change when the data is seen; if a future reader disputes an entry, that is
a dispute about CAMS, which is the right place for it to live.

**Per-document metric**: of all consecutive tag pairs `(tag_i, tag_{i+1})` where `tag_i` is a listed
FPP, the fraction where `tag_{i+1}` is in that FPP's valid-SPP set — a *completion rate* in [0, 1],
not a raw count, so it is comparable across documents and cells regardless of how often FPP-type
tags occur in the first place (monologues are expected to contain fewer FPPs; the rate controls for
that by conditioning on FPPs having occurred). Documents with zero FPP occurrences have an undefined
rate and are recorded separately as an FPP-absence count rather than folded in as 0 — reporting the
share of such documents per cell is itself informative (a monologue pole is expected to have many),
and averaging over defined rates keeps the metric from being dominated by the trivially-empty case.

Note this is a deliberately strict, immediate-adjacency operationalization: it counts an FPP as
"completed" only when the valid SPP is the *very next* tagged utterance, with no insert-expansion
tolerated. CAMS's full theory allows insert-expansions between an FPP and its SPP, but detecting
those requires the speaker-turn layer three of our five cells do not have (§0), so the strict
version is the one that is computable identically everywhere. This makes the metric a conservative
lower bound on "true" adjacency-pair completion — which is the safe direction: it can only
understate dialogue-ness, so a dialogue signal that survives it is real.

### 3d. Placing a cell: the comparison rule (threshold-free, fixed now)

Each signal above produces, per cell, either a distribution over labels (§3a: 28-vector; §3b:
784-vector = flattened joint bigram) or a per-document scalar (§3c: completion rate). The rule that
turns these into a monologue/dialogue call for cell ⑤ is the same nearest-neighbour logic used in
Methods 1 and 2, so no new threshold is invented:

- **Anchors.** The comparison that carries the argument is the same-task AI-only one
  (`research_plan.md`): the monologue pole is **AI monologue (④)** and the dialogue pole is **AI
  dialogue (③)**. The human cells (①②) are *not* used to place ⑤; they are the Step-1 validity
  check (§3e) that the signal separates known monologue from known dialogue at all.
- **Distance.** For the distribution signals (§3a, §3b), distance is the **Jensen–Shannon
  divergence** (base-2, so bounded in [0, 1]) between the two cells' averaged distributions — chosen
  because it is symmetric, bounded, defined even when one distribution has zeros (which raw KL is
  not), and standard for comparing categorical profiles. For the scalar signal (§3c), distance is
  the absolute difference between cell means.
- **Call.** Compute `d_mono = distance(⑤, ④)` and `d_dia = distance(⑤, ③)`. Cell ⑤ is called
  toward whichever pole is closer. To avoid over-reading a coin-flip, the call is reported as **"no
  clear margin"** when the two distances are within a relative margin of each other,
  `|d_mono − d_dia| / max(d_mono, d_dia) < m`. This directly implements `research_plan.md` Step 3's
  "if they land in between, we report that honestly instead of forcing a label."
- **Setting `m` from a noise floor, not a round number.** `m` is not asserted; it is calibrated
  separately for each signal (§3a, §3b, §3c each get their own `m`, since they have different
  sampling behaviour) from the two known poles, ③ and ④, using only calibration data:
  1. For a given signal, repeatedly (bootstrap, e.g. `B = 1000` iterations) split ③'s documents into
     two random disjoint halves of equal size, recompute the signal's distance between the two
     halves, and record the relative gap this produces. Do the same for ④. Pooling both poles' splits
     gives an empirical **null distribution of the gap size produced by sampling noise alone** — i.e.
     the size of gap you'd see between two samples that are, by construction, the *same* pole.
  2. Set that signal's `m` to the 95th percentile of this null distribution. A gap between ⑤ and a
     pole only counts as a real signal if it exceeds what 95% of pure-noise same-pole splits produce.
  3. This whole procedure runs only on ③ and ④ (calibration cells), so it never touches cell ⑤ and
     can be run and frozen before Step 2 executes on the target.
  This replaces the earlier flat default of `m = 0.10` (§6 item 2, now resolved) with a
  noise-floor-calibrated value per signal — the same fix pattern as Method 1's binomial gate and
  Method 2's Cliff's-delta gate: don't assert a threshold, derive it from what chance alone would
  produce on data we already have labels for.
- Each of the three signals gets its own call; §4 states how the three (and the three methods
  overall) are combined without a vote-counting fudge.

### 3e. Method 3 Step-1 gate and labeling-reliability check

Method 3 has to clear two gates on the four calibration cells before it is allowed to speak about
cell ⑤, and both are anchored, not invented:

1. **Labeling reliability (does the tagger tag correctly at all).** Pre-registered in
   `methods/3_dialogue_act_tagging/sources/SOURCES.md`: hand-label a sample of utterances from each
   of ①②③④ against the LLM tagger's output and compute Cohen's κ. **If κ < 0.70, Method 3 is
   invalid** and is dropped — this threshold is the SOURCES.md pre-registration, not a new choice,
   and 0.70 is the conventional "substantial agreement" floor. This is a property of the tagging step
   and is independent of the monologue/dialogue question.
   - **Sample size per cell is computed, not assumed.** Target: the 95% CI half-width around the
     measured κ must be ≤ 0.05, so a pass/fail call near the 0.70 cutoff is actually trustworthy
     rather than an artifact of a wide interval. Required `n` is solved from the standard asymptotic
     variance formula for Cohen's κ (Fleiss, Cohen & Everitt, 1969), which takes the tag-frequency
     marginals as an input. Procedure: once each cell's §3a unigram tag-distribution has been
     computed (calibration cells only — this is a legitimate pre-registration input, not a cell-⑤
     contact), use those observed marginals to solve for the `n` that hits the ±0.05 target for that
     cell; if computed before §3a is available, use the conservative worst-case assumption of all 28
     tags equally likely (which maximizes variance and therefore `n`), then this can only be revised
     downward once real marginals are in. The resulting `n` (expected to land somewhere around
     100–200 utterances per cell, i.e. 400–800 total, but this is computed rather than picked) is
     logged in `STATUS.md` before hand-labeling begins, replacing the earlier flat 50/cell default
     (§6 item 3, now resolved).
2. **Signal validity (does the structure separate known monologue from known dialogue).** The
   primary signal §3c must separate the poles in the expected direction: mean completion rate for
   the dialogue cells (②③) must exceed that for the monologue cells (①④). Report the effect size
   (Cliff's delta) and the direction, an ordinal check like Method 2's, not a fresh accuracy
   threshold. As a consistency check the distribution signals should agree structurally —
   within-class JSD (③↔② or ①↔④) smaller than between-class JSD (mono↔dialogue) — but §3c is the
   binding gate; §3a/§3b agreement is reported, not required.

If either gate fails, Method 3 is reported as failed at Step 1 and does not get a vote on cell ⑤
(§4), exactly as `research_plan.md` requires.

---

## 4. Step 3 — placing cell ⑤ and combining the three methods

Steps 1 and 2 are already specified per method above (each method's Step-1 gate, and "run on cell ⑤"
is mechanical). This section fixes Step 3 — how the surviving methods' calls are read together —
because leaving it open is itself a forking path.

**Only methods that pass their Step-1 gate get a call on cell ⑤.** A method that fails to separate
monologue from dialogue on the four known cells has shown it cannot measure the thing, so its
reading of cell ⑤ is discarded, not averaged in. This is stated in `research_plan.md` and is
repeated here so it cannot be quietly relaxed later.

**Each surviving method places cell ⑤ on the monologue↔dialogue axis using the same nearest-pole
logic**, against its own AI monologue (④) and AI dialogue (③) anchors:

- Method 1: mean predicted author count (TBC). Pole distance = |mean(⑤) − mean(pole)|.
- Method 2: `d_dia` and `d_mono` computed against each pole's own length-fitted curve (§2), not a
  single universal score — cell ⑤'s distance to whichever pole is closer, on the same footing as
  Method 3's §3d.
- Method 3: its primary signal §3c (completion rate), with §3a/§3b reported alongside. Distances as
  in §3d.

For each method the output is one of three verdicts — **monologue-leaning**, **dialogue-leaning**,
or **no clear margin** — using the same relative-margin rule as §3d (each signal's own
noise-floor-calibrated `m`, from the ③/④ bootstrap procedure) so the three methods are read on a
common footing.

**Combining the methods — reported, not voted.** The three methods are independent checks by
design, so the result is the *pattern* of their three verdicts, presented in full, not collapsed to
a majority label:

- If all surviving methods agree (all monologue-leaning, or all dialogue-leaning), that is the
  headline finding, and its strength is exactly that three unrelated measures concur.
- If they split, that is reported as a split, with each method's verdict and margin shown, and read
  as genuinely mixed evidence — cell ⑤ carrying some monologue-like and some dialogue-like
  structure — rather than forced to a single label by counting votes. A split is a real result about
  reasoning traces, not a failure of the study.

No method is weighted above the others and no tie-break is invented; the deliverable is the table of
three verdicts plus the placement figure (§5), which is what actually carries interpretable
information about the research question.

---

## 5. Exact outputs and figures to produce

Fixed now so the results section is written before the numbers exist. Every figure is faceted by
cell (①–⑤) unless stated, uses the AI monologue (④) and AI dialogue (③) anchors as reference lines,
and marks cell ⑤ distinctly. All per-cell summaries report the full across-document distribution
(box or violin), never a bare mean, so dispersion and overlap are visible.

**Method 1 — style-change author count**
- Fig M1.1: violin/box of per-document predicted author count per cell (TBC).
- Table M1: per-cell mean count, share called multi-author, per-cell and pooled accuracy, confusion
  matrix, and the binomial-test result against chance (§1).

**Method 2 — sentence-level switch probability**
- Fig M2.1: violin/box of per-document raw switch probability per cell, plus `lean = |d_mono| −
  |d_dia|` per cell side by side.
- Fig M2.2 (extrapolation check): scatter of length vs. probability for `ai_debate` (③) and
  `ai_monologue` (④) calibration documents, each with its own fitted curve (possibly different
  functional forms — §2), both extended out to cover cell ⑤'s actual length, and each pole's own
  observed length range shaded, so how far each curve is being stretched is visible directly, not
  asserted. Annotated with how far past each pole's own observed maximum length cell ⑤ falls.
  Two additions, both descriptive only, neither used in the gate or the placement decision: (a) a
  third curve fit on `human_debate` (②), clearly marked as context rather than a placement pole,
  since that restriction to the AI-only pair is deliberate (§2); (b) cell ⑤'s own documents plotted
  as a raw scatter (not a fitted curve — see §2 for why fitting one wasn't the right next step)
  alongside the two pole curves, so where the whole cloud actually sits is visible directly rather
  than reduced to a single averaged point.
- Table M2: per-cell mean `lean` and Cliff's delta (②③ vs. ①④, ≥ 0.33 floor) for the
  Step-1 gate; the functional-form comparison for each pole separately (AIC for raw-linear,
  semi-log, log-log).

**Method 3 — dialogue-act structure**
- Fig M3.1 (§3a): grouped/stacked bar of the 28-label distribution per cell (unigram profiles),
  cells side by side.
- Fig M3.2 (§3b): small-multiple heatmaps of the row-normalized 28×28 transition matrix per cell,
  plus two difference heatmaps, (⑤ − ④) and (⑤ − ③), to show which transitions pull cell ⑤ toward
  each pole.
- Fig M3.3 (§3c, headline): violin/box of per-document adjacency-pair completion rate per cell, with
  the per-cell share of FPP-absent documents annotated.
- Fig M3.4 (§3d): scatter of JSD-to-④ (x) vs JSD-to-③ (y) for the unigram and bigram signals, cells
  plotted as points, the diagonal marking equal distance, so cell ⑤'s lean is read off directly.
- Table M3: per-cell mean completion rate + Cliff's delta; κ from the reliability check;
  `d_mono`/`d_dia` and the resulting call for each of §3a/§3b/§3c.

**Cross-method summary**
- Fig X.1: a single placement panel — the monologue↔dialogue axis normalized so ④ = 0 and ③ = 1,
  with each surviving method's cell-⑤ position plotted as a point and its "no clear margin" band
  shaded, so the whole conclusion is legible in one view.
- Table X: methods × {passed Step 1?, cell-⑤ verdict, margin}. This table is the answer to the
  research question.

---

## 6. Numbers still to sign off

Everything else in this document is either taken from a source (Nath 2019's 50/50 thresholds and
Matusita distance and TBC-primacy; PAN25's shipped checkpoint; CAMS's tag set and FPP→SPP mapping;
SOURCES.md's κ ≥ 0.70) or a mechanical default. These are the only free choices left, and freezing
them is what makes the commit a real pre-registration:

1. ~~Method 1 gate~~ — **resolved, no longer an open number.** Replaced the imported 80%
   round-number floor with a binomial significance test against chance (§1); nothing left to sign
   off here.
2. ~~Method 3 comparison margin~~ — **resolved.** Replaced the flat `m = 0.10` default with a
   per-signal margin calibrated from a bootstrap noise floor on ③/④ (95th percentile of the
   same-pole random-split gap distribution) — §3d. Nothing left to sign off here.
3. ~~Method 3 reliability sample size~~ — **resolved.** Replaced the flat 50/cell default with a
   computed `n` solved from Cohen's κ asymptotic variance formula, targeting a 95% CI half-width of
   ≤ 0.05 around κ, using each cell's own calibration-only tag-frequency marginals (or a conservative
   uniform-marginal assumption if computed first) — §3e. The 0.70 gate itself remains the
   SOURCES.md pre-registration and was never in question.
4. ~~Method 2 gate strength~~ — **resolved.** Direction (②③ mean `lean` > ①④) plus Cliff's delta
   ≥ 0.33 (conventional "medium" floor). Nothing left to sign off here.
5. ~~Method 2 equal-slope tolerance~~ — **no longer applicable.** Each pole now gets its own
   independently-fit curve (§2) — `ai_debate` and `ai_monologue` are never combined into one shared
   slope, so there's nothing to reconcile between them. Nothing left to sign off here either.

Once these five are signed off, commit `methods.md` and `STATUS.md` together — that commit is the
pre-registration timestamp, and per §0 it must land before any §3 statistic is first computed on
cell ⑤.