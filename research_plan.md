# Research Plan: Is AI Reasoning Monologue or Dialogue?

## Core Research Question
Does native AI reasoning (e.g. chain-of-thought / `<think>` traces) structurally resemble a **monologue** (single voice) or a **dialogue** (multiple voices)?

---

## 2×2 + 1 Validation Framework

|  | **Human** | **AI** |
|---|---|---|
| **Monologue** | ✅ Known — think-aloud protocols | ✅ Constructible — prompted CoT (single model, no reasoning training) |
| **Dialogue** | ✅ Known — group debates/discussions | ✅ Constructible — simulated multi-agent AI debate |

Plus a **5th data point**: native reasoning traces (e.g. DeepSeek-R1 `-thinking`, QwQ-32B) — the **true dependent variable**.

The four known cells serve as **ground-truth calibration** along a structural gradient. The native reasoning traces are the **unknown** — never assumed, always empirically derived.

### Structural gradient

**① human solo → ④ AI prompted solo → ⑤ native reasoning traces → ③ AI multi-agent → ② human debate**

If ⑤ clusters with ④, that's evidence for monologic. If ⑤ clusters with ③, that's evidence for dialogic. If it sits between, that's the spectrum answer.

---

## Experimental Design

### Step 1 — Validate the Method
Use the four known cells to confirm the classification method works:
- Human monologue (think-aloud) → should be classified as *single voice*
- AI prompted monologue (CoT from non-reasoning model) → should be classified as *single voice*
- Human dialogue (group debates) → should be classified as *multiple voices*
- AI simulated dialogue → should also be classified as *multiple voices*

A method that passes all four is considered valid for Step 2.

### Step 2 — Apply to the Native Reasoning Traces
Feed native AI reasoning traces (⑤) into the validated method and observe the output.

### Step 3 — Interpret
| Method Output for ⑤ | Interpretation |
|---|---|
| Clusters with ④ (single voice) | AI reasoning is monologic |
| Clusters with ③ (multiple voices) | AI reasoning structurally resembles dialogue |
| Spectrum / partial | Reasoning is neither purely mono- nor dialogic — requires nuanced reading |

---

## Comparability Layer (Key Design Choice)

All three AI/AI-adjacent cells (③, ④, and ⑤) use **Game-of-24** — the same task as the human monologue corpus ①.

### Rationale (style-based methods make this load-bearing)

The three planned classification methods (style-change detection, stylometric step-change, dialogue-act tagging) are all sensitive to **task content** — function-word rates, punctuation, and transition structure shift between arithmetic search (Game-of-24) and rule-checking (Wason) independently of how many authors wrote the text. This means:

1. **③, ④, and ⑤ must share a task.** The AI-group vs AI-solo vs AI-reasoning contrast is the only task-controlled monologue-vs-dialogue comparison in the design. If they run on different tasks, any stylometric difference is uninterpretable — task and structure are confounded.

2. **① (human think-aloud, Game-of-24) serves as the on-task single-author control.** If the style-change detector flags ① as single-author on Game-of-24, then a multi-author flag on ⑤ (same task, same phase structure) is trustworthy — phase artefacts are subtracted out. No such control exists on Wason.

3. **② (human debate, Wason) keeps a separate job:** it shows the methods detect multiple *human* voices, not only AI ones, and it anchors human dialogue-act transition patterns. It does not need to match ⑤'s task to do that job.

### Role of each cell in a style-based design

| Cell | Task | Role |
|---|---|---|
| ① human solo | Game-of-24 | On-task false-positive control — real single author on ⑤'s task |
| ④ AI prompted solo | Game-of-24 | Intermediate anchor — AI monologue without reasoning training; bridges ① and ⑤ |
| ③ AI group | Game-of-24 | On-task true-positive — genuine multi-author, task held constant with ⑤ |
| ⑤ native reasoning | Game-of-24 | **Unknown** — measured against ①, ④, and ③ with task controlled |
| ② human debate | Wason | Method generalization — shows detectors work on human multi-author text |

### Known limitation
The human ①–② pair is **task-confounded** (different tasks). It cannot by itself prove the methods detect *structure* rather than *task*. The AI ③–④–⑤ same-task trio is what supplies the task-controlled validation. This should be reported as a design limitation and addressed by reporting ③ vs ⑤ as the primary structural contrast, with ④ as the intermediate anchor.

---

## Data Sources

| # | Cell | Canonical file | Raw source | Status | Details |
|---|---|---|---|---|---|
| ① | Human Monologue | `data/00_core-2x2/human_monologue/processed_sample_600_human_think_aloud.jsonl` | `data/raw/human_monologue/think_aloud_source/` | LOCKED | 7,707 original trials; 600-row processed development sample — Game-of-24 think-alouds |
| ② | Human Dialogue | `data/00_core-2x2/human_debate/processed_human_debate.jsonl` | `data/raw/human_debate/delidata_source/` | LOCKED | 500 Wason selection task group dialogues |
| ③ | AI Dialogue | `data/00_core-2x2/ai_debate/processed_ai_debate.jsonl` | `data/raw/ai_debate/qwen_generation/` | GENERATED | Simulated 4-agent debates on Game-of-24. Actual model: `qwen/qwen-2.5-7b-instruct`. **Deviation:** locked protocol specified DeepSeek-V3 and no personas; see Current State & Deviations. |
| ④ | AI Prompted Monologue | `data/00_core-2x2/ai_monologue/processed_prompted_ai_monologue.jsonl` | `data/raw/ai_monologue/qwen_generation/` | GENERATED | Prompted CoT on Game-of-24 using `qwen/qwen-2.5-7b-instruct` — intermediate anchor |
| ⑤ | Native Reasoning Traces | `data/00_core-2x2/ai_reasoning/processed_native_reasoning_traces.jsonl` | `data/raw/ai_reasoning/deepseek_generation/` | GENERATED | Native `thinking` traces on Game-of-24 from `deepseek/deepseek-r1`, 600 rows — **the dependent variable** |

---

## AI Dialogue Construction (Cell ③) — 🔒 LOCKED Protocol

### Guiding principle
Match a structural variable only if leaving it unmatched would let it masquerade as the effect you're studying. Everything else: hold constant and keep simple. A constant is trivial to control for; a distribution is one more thing to model.

### What makes it ground truth
Multiplicity must come from **N genuinely separate model instances**, each with its **own context window**, sharing **only the public transcript** — never each other's internal state. This is the computational analog of N people who hear only what's said aloud.

> **Trap to avoid:** Do NOT prompt one model to write an N-persona script (`<persona1>…<persona2>…`). That is a single instance producing apparent-multi-voice text — precisely the phenomenon under study in Cell ⑤. Using it as ground truth begs the entire question.

### 🔒 Locked decisions

| Knob | Decision | Rationale |
|---|---|---|
| **Model** | DeepSeek-V3 (non-reasoning) | No hidden `<think>` traces; turn = only what is "said aloud"; clean multi-author signal |
| **Tasks** | **Game-of-24 items** (same as human monologue ①) | Task-controlled contrast with ④; enables on-task false-positive check via ① |
| **N speakers** | Fixed **4** per group | Keeps style-change detector conditions constant across corpus |
| **N debates** | **~200, hardest-first** | Start with hardest puzzles (highest human RT from ①); scale up later if needed |
| **Turn count** | Cap at **40 turns**; log actual length | Covers DeliData's ~28-utterance mean with headroom; control for length in analysis |
| **Turn order** | **Uniform random** draw from all 4 agents (including current speaker) | Simplest possible; self-repeats remain possible as in natural conversation |
| **Roles / personas** | None assigned | Assigning roles would be an arbitrary structural imposition |
| **System prompt** | One neutral structural line ("You are {X}, one of four participants (A, B, C, D). Share your thoughts briefly. This is a collaborative discussion."); task as bracketed header in user message; `stop=["\nA:","\nB:","\nC:","\nD:"]` enforces one turn | Structural facts (which slot) ≠ behavioural flavour; stop sequences mechanically prevent writing others' turns |
| **Ending mechanic** | All 4 must speak ≥1 turn; **40-turn hard cap**; then 4 independent final answers (1 extra call each) | No [DONE] signals, no consensus — simple cap is sufficient; final submissions add correctness data at minimal cost |
| **Sampling** | Temperature **0.8** | With no personas, sampling stochasticity + conversational position are the only sources of inter-agent difference; must be > 0 |

### Architecture
- N=4 **stateless** separate API calls per turn, each receiving only the shared public transcript
- Each instance identified only by a participant label (A/B/C/D) in the history
- No instance ever sees another's system prompt
- Output: full transcript with speaker labels → strip labels for the style/exchangeability methods; keep labels for dialogue-act tagging; ground truth = 4 authors

> **Full coder-facing build spec** (exact prompts, output schema, engineering practicalities, mandatory pilot gate): [`cell3_ai_debate_build_plan.md`](cell3_ai_debate_build_plan.md)

### Same-model ceiling — deliberate choice
Cell ③ uses **four instances of one model (V3)**, not four different models. ⑤ (the reasoning trace under study) is also a single model, so a same-model ceiling is the matched comparison. If style methods cannot detect multiplicity in same-model dialogue, that is a finding about method suitability — not masked by mixing models. Consequence: Method 1 (style-change) may read ③ as single-author; Methods 2 & 3 (which don't depend on distinct styles) carry the structural contrast.

### Risk: task may be too easy
Game-of-24 has verifiable answers a capable model may find fast, risking degenerate 1–2 turn "debates". Mitigated by (a) selecting the **hardest** puzzles (longest human think-aloud RT from ①) and (b) a **mandatory 20–30 debate pilot with a go/no-go gate** before generating all 500. If pilots collapse to trivial turns, escalate (possibly switch dialogue task / obtain harder think-aloud data).

⚠ **Task-matching note:** ③, ④, and ⑤ all use Game-of-24, making the ③ vs ⑤ contrast task-controlled (the primary structural comparison), with ④ as the intermediate anchor. Human monologue ① also uses Game-of-24, serving as the on-task single-author floor. Human dialogue ② uses Wason — the ②–③ task mismatch is acceptable because ② only needs to confirm the methods detect multi-author human text, not to serve as ⑤'s ceiling anchor.

---

## Classification Methods (Three Planned Experiments)

All three methods are applied across all five data points and validated against ground truth (①②③④) before being applied to ⑤.

### 1. Single- vs multi-author classification (PAN style-change detection) ⭐
Nath's clustering-based style-change detector (PAN 2019 winner): paragraph windows, 50 most frequent words, threshold-based clustering. Predicts author count; binary label = multi-author if count > 1.
- **Answers:** Is the trace stylometrically single- or multi-authored?
- **Validation:** must flag genuine multi-model interleavings (③) as multi-author and solo docs (①, ④) as single
- **Known weakness:** within-model personas share one authorial style, so a positive likely reflects topic/phase rather than personas. Mitigated by on-task false-positive check on ①.

### 2. Sentence-level style change detection (PAN 2025 SSPC) 🍌
Sequential Sentence Pair Classifier (SSPC) from PAN 2025: encode each sentence with a pre-trained language model (`StyleDistance/styledistance`), contextualize the sequence with a 5-layer BiLSTM, and classify each adjacent sentence pair as same-author or different-author. Binary label = multi-author if the average style-change probability (or number of detected changes) exceeds a document-level threshold.
- **Answers:** Does the trace contain sentence-level style switches indicative of multiple voices?
- **Validation:** must flag genuine multi-model interleavings (③) as multi-author and solo docs (①, ④) as single
- **Known weakness:** the model is trained to detect style-change points, not single-vs-multi-author documents; topic/phase shifts within a single author may trigger false positives. Mitigated by the same-task false-positive check on ① and by comparing average probabilities across cells.

### 3. Dialogue-act tagging ⭐
Label each subthought with a speech act (assert / question / agree / disagree / propose / concede) using a tagger or LLM-judge; analyse the transition matrix for turn-taking structure (Q→A, propose→critique patterns).
- **Answers:** Does the sequence have conversational structure vs monotone assertion?
- **Validation:** transition structure must distinguish human debate (②) from human think-aloud (①) — this is the 2×2 check

---

## Method Pre-Registration (lock before running on real data)

**Why this section exists:** choosing a method *while* looking at how it performs on your data is the garden-of-forking-paths problem — every "let me just try X instead" after seeing a result is an undisclosed researcher degree of freedom. The antidote: pin the exact spec below, commit it to git as a frozen checkpoint, then run once. Any post-hoc deviation must be logged under "Deviations," not silently edited into the spec above.

### 1. Style-change detection
- **Literature anchor:** PAN 2019 Style Change Detection (Zangerle et al., 2019). Winner: Nath (2019), clustering-based TBC algorithm.
- **Exact spec:** Nath's Threshold Based Clustering (TBC) from https://github.com/pan-webis-de/nath19 — 50 most frequent words per paragraph window, Matusita/Manhattan distance, merge_threshold=50, add_node_threshold=50, duplicate-sentence shortcut enabled. Predicted author count = number of clusters; binary label = multi-author if count > 1.
- **Decision rule for Step 1 pass/fail:** Qualitative cell-level expectations on known cells ①②③④ (no arbitrary accuracy thresholds):
  - ① human monologue, ④ AI prompted monologue → classified as **single-author**
  - ② human debate, ③ AI multi-agent debate → classified as **multi-author**
  - If the method fails on any of these four, record as failure — do not tune post-hoc.
- **Implementation:** `methods/1_style_change_detection/implementation/` (cloned from pan-webis-de/nath19)
- **Benchmark validation (before touching project data):** Reproduce PAN 2019 binary classification results on validation set to verify implementation correctness. Expected performance: ~84.8% accuracy (Nath's reported performance). PAN 2019 data: https://zenodo.org/records/5174825 (access requested). **PAN 2018 test results:** Tested on PAN 2018 validation set (1,492 files) - 58% accuracy on successful files (1,279/1,492), 14% failure rate due to implementation bug. Implementation shows bias toward single-author predictions. **Note:** PAN 2018 has different format/distribution; proper validation requires PAN 2019 data. **Procedure:** (1) Wait for PAN 2019 access approval, (2) Run implementation on PAN 2019 validation data, (3) Verify accuracy matches expected ~84.8%, (4) If accuracy is significantly lower, investigate implementation bug, (5) Only proceed to project data if validation succeeds.

#### Deviations
- **2026-07-11:** Replaced pre-registered classical baseline (char n-grams + cosine similarity + 0.15 threshold) with Nath TBC (PAN 2019 winner). **Reason:** Classical baseline expected ~60% (PAN random baseline); Nath achieves 84.8% on identical task with no GPU/fine-tuning. Removed arbitrary 75%/70% accuracy thresholds — no literature justification existed.

### 2. Sentence-level style change detection (PAN 2025 SSPC)
- **Literature anchor:** Schmidt et al. (2025), "Style Change Detection using a Sequential Sentence Pair Classifier," PAN Lab at CLEF 2025 (CEUR Workshop Proceedings, Vol. 4038). Open-source implementation: https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis
- **Exact spec:** Sentence-level style-change detection using the Sequential Sentence Pair Classifier (SSPC). Base encoder = `StyleDistance/styledistance` (frozen). Sentence representations obtained by mean-pooling token embeddings. Contextualization = 5-layer bidirectional LSTM (hidden dim 256, dropout 0.2). Adjacent sentence vectors are concatenated and passed through a 3-layer MLP with GELU activations and dropout 0.2, producing a logit for each sentence boundary. Classification threshold = 0.5 (sigmoid; default from the released code). Binary document-level label: multi-author if the average style-change probability across all sentence boundaries is > 0.5, otherwise single-author.
- **Decision rule for Step 1 pass/fail:** Qualitative cell-level expectations on known cells ①②③④:
  - ① human monologue, ④ AI prompted monologue → classified as **single-author**
  - ② human debate, ③ AI multi-agent debate → classified as **multi-author**
  - If the method fails on any of these four, record as failure — do not tune post-hoc.
- **Implementation:** `methods/2_stylometric_step_change/implementation/` (cloned from https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis)
- **Benchmark validation (before touching project data):** Reproduce PAN 2025 sentence-level style-change detection results on the official test data to verify implementation correctness. Expected performance: macro-F1 of 0.929 (EASY), 0.815 (MEDIUM), 0.724 (HARD) as reported by Schmidt et al. on the official test set. Procedure: (1) Download PAN 2025 multi-author style analysis data from https://pan.webis.de/clef25/pan25-web/style-change-detection.html, (2) Run the released `predict.py` on the test set, (3) Verify F1 scores are within reasonable range of reported values, (4) Only proceed to project data if validation succeeds.
- **Calibration discipline:** Document-level threshold fixed at 0.5 average style-change probability (no tuning). If Step 1 fails, record as failure — do not adjust the threshold post-hoc.

#### Deviations
- **2026-07-11:** Replaced the pre-registered custom exchangeability method (window + Jensen-Shannon divergence + Ljung-Box test + shuffle null) with the PAN 2025 Sequential Sentence Pair Classifier (SSPC). **Reason:** The custom method was a synthesis without a single canonical literature anchor, while SSPC is a recent, openly available, benchmarked PAN submission with sentence-level granularity and a reproducible implementation.

### 3. Dialogue-act tagging
- **Literature anchor:** The Conversation Analysis Modelling Schema (CAMS) — Duran & Battle (2018), based on ISO 24617-2 (DiAML) and Conversation Analysis (Schegloff & Sacks 1973; Liddicoat 2007; Sidnell 2010). CAMS explicitly combines Dialogue Acts (DA) and Adjacency Pairs (AP) into AP-types, making it directly applicable to our adjacency-pair counting approach. LLM-judge implementation precedent: Act2P (ACL Findings 2025, LLM-driven dialogue act classification).
- **Tag set:** The full CAMS set of 27 Dialogue Acts, grouped by function, plus an added `none` fallback for sentences that do not match any CAMS tag. The exact definitions are preserved in the local prompt file `methods/3_dialogue_act_tagging/CAMS_LLM_labeling_prompt.txt` and copied verbatim from the source. The 27 tags are:
  - **Information-seeking Functions:** propositionalQuestion, setQuestion, choiceQuestion, checkQuestion
  - **Information-providing Functions:** inform, answer, agreement, disagreement, correction, confirm, disconfirm
  - **Commissive Functions:** offer, conditionalAccept, accept, decline
  - **Directive Functions:** request, suggest
  - **Feedback Functions:** autoPositive, autoNegative
  - **Time Management Functions:** stalling
  - **Own and Partner Communication Management Functions:** retraction
  - **Social Obligations Management Functions:** greeting, goodbye, thanking, acceptThanking, apology, acceptApology
  - **Fallback tag:** `none` — use only if the sentence clearly does not match any of the 27 CAMS tags and does not form a speech act
- **Operational definitions:** Exact definitions are taken from the CAMS source (https://nathanduran.github.io/Conversation-Analysis-Modelling-Schema/) and stored in `methods/3_dialogue_act_tagging/CAMS_LLM_labeling_prompt.txt`. The LLM prompt is this file plus the instruction to classify each sentence with exactly one of the tags, outputting only the tag name.
- **Exact spec:**
  1. **Sentence segmentation:** Split text into sentences using standard sentence boundary detection
  2. **Dialogue act tagging:** Use LLM (model to be determined, temperature 0) to label each sentence with exactly one of the 27 CAMS tags or the `none` fallback. Frozen prompt: `CAMS_LLM_labeling_prompt.txt`. The prompt instructs the LLM: "If a sentence is part of the same speech act as the previous sentence, use the same tag. If a sentence introduces a new speech act, change the tag accordingly." Output format: one JSONL object per sentence with fields `text` (exact sentence text) and `label` (tag name), plus a full input/output example. The pipeline re-attaches `start` and `end` character indices and saves one JSONL file per sample, with filenames encoding the cell and sample ID (e.g., `cell3_ai_debate_sample_042.jsonl`). No explanations, no markdown code fences, only valid JSONL. One sample is processed per LLM call. Implementation skeleton: `methods/3_dialogue_act_tagging/implementation/label_dialogue_acts.py`.
  3. **Adjacency pair counting:** Count adjacency pairs in the sequence (first part followed by second part within 2 turns):
     - propositionalQuestion/setQuestion/choiceQuestion/checkQuestion → answer
     - suggest/request/offer → accept/decline/agreement/disagreement
     - inform → agreement/disagreement/correction
     - greeting → greeting
     - goodbye → goodbye
     - thanking → acceptThanking
     - apology → acceptApology
  4. **Comparison:** Apply to all cells ①②③④⑤, compute total and per-pair-type adjacency pair counts per cell, compare ⑤ to known cells.
- **Decision rule for Step 1 pass/fail:** Qualitative cell-level expectations: ② human debate and ③ AI multi-agent debate show higher adjacency pair counts than ① human monologue and ④ AI prompted monologue. If this pattern fails to emerge, record as failure — do not tune post-hoc.
- **Validation before use:** Hand-label 50 random utterances from each of ①②③④ (200 total). Compute Cohen's κ between LLM-judge and human coder. If κ < 0.70, method is invalid — do not proceed to full corpus tagging.

### Process
1. Fill in the 🔲 open decisions above.
2. `git commit` the completed spec as a frozen checkpoint — this is the pre-registration record.
3. **Implementation validation (for all methods):** Before touching project data, run each method on its original benchmark dataset to verify implementation correctness. Only proceed to project data if benchmark validation succeeds. This prevents "implementation bugs" from being mistaken for "method failures" on your data.
3. Run Step 1 validation exactly as specified, once.
4. Report the result, pass or fail, as written here — do not edit this section after seeing Step 1 results.
5. Any change after this point goes in a **Deviations** subsection (added below, never overwriting the original), with a stated reason.

---

## Key Strength of the Design
The inference about AI reasoning is **method-agnostic**: the conclusion is only as strong as the method's demonstrated performance on the known cells (①②③④), which is directly measurable and reportable. This makes the framework self-validating.

---

*Last updated: 2026-07-14 — cells ①② locked in; cell ③ generated (Game-of-24, 4× qwen-2.5-7b-instruct) with deviations from the locked protocol; cell ④ generated (prompted CoT, qwen-2.5-7b-instruct) as intermediate anchor; cell ⑤ generated (native `thinking` traces, DeepSeek-R1, Game-of-24) — the dependent variable; task-matching rationale and three classification methods added; framework expanded from 2×2 to 2×2+1; preprocessing and benchmark validation in progress.*

---

## Notes

### Difficulty scores
The `puzzle_selection.csv` includes `difficulty_score` (based on human RT and fail rate) ranging from approximately -3.1 (easiest) to +2.8 (hardest). These scores can be used for:
- **Difficulty-stratified analysis:** test whether the mono-/dialogic distinction varies with puzzle difficulty
- **Correlation with reasoning structure:** examine whether harder puzzles elicit more dialogic-like reasoning patterns
- **Balanced sampling:** ensure the 200-puzzle set covers the full difficulty range for generalizability

---

## Current State and Deviations (2026-07-14)

This section records the state of the project *after* the pre-registration checkpoint in commit `b7f40d0`. Per the pre-registration rules, nothing above this section is silently overwritten; deviations are appended with a reason.

### 1. Cell ⑤ (native reasoning traces) — generated, not pending
- **Status:** GENERATED.
- **Canonical file:** `data/00_core-2x2/ai_reasoning/processed_native_reasoning_traces.jsonl` (600 rows).
- **Raw source:** `data/raw/ai_reasoning/deepseek_generation/cell5_reasoning_traces.jsonl` (603 rows before `g24_0193` removal).
- **Model:** `deepseek/deepseek-r1`.
- **Task:** Game-of-24, matching cells ①, ③, and ④.
- **Reason for update:** The plan text above still listed cell ⑤ as pending. The data has been collected and canonicalized.

### 2. Cell ③ (AI multi-agent debate) — deviations from the locked protocol
- **Actual model used:** `qwen/qwen-2.5-7b-instruct` (OpenRouter) across 600 debates.
- **Locked protocol specified:** DeepSeek-V3 (non-reasoning).
- **Reason for deviation:** The generation script `scripts/cell3_build_dataset_random_discussion.py` defaults to `deepseek/deepseek-chat` but was run with `--model qwen/qwen-2.5-7b-instruct` (or the API route resolved to qwen). The `model` field in the JSON is hardcoded to `deepseek-chat`; `model_version` is the authoritative API-returned string.
- **Personas:** The script assigns four explicit roles (Creative Problem Solver, Critical Analyst, Mathematical Validator, Alternative Seeker). The locked protocol specified no roles/personas.
- **Final-answer round:** The locked protocol specified four independent final submissions. The current script is a "discussion-only" variant and does not collect explicit final answers.
- **Generation seeds:** Three passes were run with `seed` values 22345 / 32345 / 42345; per-debate `turn_order_seed` values are `seed - 10000 + rank` (e.g., 12346 for pass 1, rank 1).
- **Impact:** The same-model-ceiling reasoning in the locked protocol was written for DeepSeek-V3. A qwen-based ceiling is still a same-model ceiling, but the literature rationale about "no hidden `<think>` traces" is not cleanly satisfied because the model is not the one originally specified.

### 3. Data locations and file naming conventions
- **Canonical working directory:** `data/00_core-2x2/`.
- **Raw generation outputs:**
  - `data/raw/ai_debate/qwen_generation/cell3_debates.jsonl` (603 rows, includes `g24_0193`)
  - `data/raw/ai_monologue/qwen_generation/cell4_monologues.jsonl` (603 rows)
  - `data/raw/ai_reasoning/deepseek_generation/cell5_reasoning_traces.jsonl` (603 rows)
- **Canonicalized files in `data/00_core-2x2/`:** only the five processed analysis inputs remain, one per cell folder; the 600-row human-monologue sample is retained for method development.
- **Historical and diagnostic files:** `data/archive/` contains original/regenerated variants, generation runs, full human samples, and diagnostics. `data/reference/` contains unrelated corpora, puzzle sets, and environments.
- **Naming cleanup:** The former `ai_mololouge`, `ai_monolouge`, and `lables` typos were corrected in the canonical filenames; raw/source folders retain their original names for provenance.
- **Script paths:** Canonical-data consumers point to `data/00_core-2x2`; generation scripts write to `data/raw`; the former empty `data/core-2x2` path is no longer used.

### 4. Preprocessing Phase 5 — pending
- `scripts/standardize_datasets.py` currently **deletes** disallowed characters; the policy decision (2026-07-10) is to **replace-with-space** to avoid deletion scars.
- Current `*_processed.jsonl` files were generated under the old deletion policy and must be regenerated once the script is updated.
- A surface-feature leakage probe (LaTeX-token rate, non-ASCII rate, character-set-violation rate, average sentence length, excluding length/turn-count) must be run before Step 1 method validation is trusted.
- Chinese-character contamination in 47/600 debates was addressed by regenerating those debates (`ai_debate_regenerated.jsonl`); the original is backed up as `ai_debate_chinese_original.jsonl`.

### 5. Method implementation status
- **Method 1 (PAN 2019 TBC):** Code cloned from `pan-webis-de/nath19`. `evaluate_benchmark.py` exists. PAN 2019 data access was pending; as of 2026-07-14 the researcher has located the PAN 2019 data for Task 1 and benchmark validation can proceed. The `preprocess_NLP_pkg` path in `requirements.txt` still needs fixing.
- **Method 2 (PAN 2025 SSPC):** Code and `model.ckpt` present. The `styledistance` encoder folder is missing, so the checkpoint cannot load. The `predict.py` script expects TIRA format; a JSONL wrapper for project data is needed.
- **Method 3 (CAMS):** `label_dialogue_acts.py` is functional and accepts JSONL. The LLM judge model is not yet fixed; the current open files (`free models.txt`, `test_free_models.py`, `test_retry_models.py`, `test_hy3.py`) indicate active testing of free-tier OpenRouter models. Adjacency-pair counting is not yet implemented. Hand-label validation (200 utterances, Cohen's κ ≥ 0.70) is required before full corpus tagging.

### 6. Interpretation of the current 2×2+1 gradient
- **Cell ordering remains:** ① human solo → ④ AI prompted solo → ⑤ native reasoning traces → ③ AI multi-agent → ② human debate.
- Cells ①, ③, ④, and ⑤ share Game-of-24, so the ③ vs ⑤ contrast is the primary task-controlled structural comparison.
- Cell ② (Wason) remains the human-dialogue generalization check and is intentionally task-mismatched.
- Cell ⑤ is the dependent variable; it has not been run through any method yet.

### 7. Next steps (in order)
1. Update `scripts/standardize_datasets.py` to replace-with-space and regenerate all `*_processed.jsonl` files.
2. Run the surface-feature leakage probe on cells ①②③④.
3. Fix Method 1 dependency path and run PAN 2019 benchmark validation.
4. Obtain/download the `StyleDistance/styledistance` encoder for Method 2.
5. Complete Method 3 LLM-judge model selection, implement adjacency-pair counting, and run hand-label validation.
6. Run Step 1 validation on all three methods against cells ①②③④.
7. Run Step 2 on cell ⑤ and Step 3 interpretation.
