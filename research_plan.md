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

| # | Cell | Folder | Status | Details |
|---|---|---|---|---|
| ① | Human Monologue | `human-monologue-think-aloud-llms/` | 🔒 **LOCKED** | 7,707 trials — Game-of-24 think-alouds |
| ② | Human Dialogue | `human-debate-delidata/` | 🔒 **LOCKED** | 500 Wason selection task group dialogues |
| ③ | AI Dialogue | `ai-debate/` | ✅ **GENERATED** | Simulated 4-agent debates on Game-of-24 (qwen-2.5-7b-instruct) |
| ④ | AI Prompted Monologue | `ai-monologue/` | ✅ **GENERATED** | Prompted CoT on Game-of-24 (qwen-2.5-7b-instruct) — intermediate anchor |
| ⑤ | Native Reasoning Traces (❓) | **To be collected** | 🔲 Pending — *the research question* | Native `-thinking` traces on Game-of-24, e.g. DeepSeek-R1, QwQ-32B |

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
Off-the-shelf intrinsic style-change detectors (function words, char n-grams, punctuation, or fine-tuned transformers) decide whether a document has one or several authors and locate switches.
- **Answers:** Is the trace stylometrically single- or multi-authored?
- **Validation:** must flag genuine multi-model interleavings (③) as multi-author and solo docs (①, ④) as single
- **Known weakness:** within-model personas share one authorial style, so a positive likely reflects topic/phase rather than personas. Mitigated by on-task false-positive check on ①.

### 2. Stylometric step-change & exchangeability 🍌
Measure |Δstyle| between consecutive fixed-word-window chunks; test whether the trace is exchangeable (order doesn't matter) or carries voice structure via lag autocorrelation and shuffle null.
- **Answers:** Is the trace exchangeable, or does order carry dialogue structure?
- **Validation:** debate anchors (③, ②) should be less exchangeable than solo anchors (①, ④); ⑤'s position on this axis is the finding
- **Note:** use fixed word-windows, not subthoughts, to avoid denominator artefacts

### 3. Dialogue-act tagging ⭐
Label each subthought with a speech act (assert / question / agree / disagree / propose / concede) using a tagger or LLM-judge; analyse the transition matrix for turn-taking structure (Q→A, propose→critique patterns).
- **Answers:** Does the sequence have conversational structure vs monotone assertion?
- **Validation:** transition structure must distinguish human debate (②) from human think-aloud (①) — this is the 2×2 check

---

## Method Pre-Registration (lock before running on real data)

**Why this section exists:** choosing a method *while* looking at how it performs on your data is the garden-of-forking-paths problem — every "let me just try X instead" after seeing a result is an undisclosed researcher degree of freedom. The antidote: pin the exact spec below, commit it to git as a frozen checkpoint, then run once. Any post-hoc deviation must be logged under "Deviations," not silently edited into the spec above.

### 1. Style-change detection
- **Literature anchor:** PAN Multi-Author Writing Style Analysis shared task (Zangerle et al., running 2016–2026; overview papers: PAN 2021, 2023, 2024). Established baselines: character n-gram / function-word frequency similarity (classical), fine-tuned DeBERTaV3 + contrastive learning (Ye et al., PAN 2023 — current strong baseline).
- **Exact spec:** Classical PAN baseline: character n-grams (n=3,4,5) + function-word frequency (top 100 function words from English POS tagger). Use cosine similarity between sliding windows (window size = 500 characters, step = 250 characters). Single/multi-author decision: if max similarity drop > 0.15 between any two consecutive windows, classify as multi-author (threshold from PAN 2018 baseline).
- **Decision rule for Step 1 pass/fail:** Classification accuracy ≥ 0.75 on single-author cells (①, ④) AND ≥ 0.70 on multi-author cells (②, ③). If either condition fails, method is invalid for this dataset.

### 2. Stylometric step-change & exchangeability
- **Literature anchor:** No single canonical paper — synthesis of stylometric distance (background: arXiv:2401.06752, "Stylometry Analysis of Multi-authored Documents for Authorship...") + statistical change-point/exchangeability testing. **This method has no external baseline to defer to, so it is the highest-risk one for undisclosed tuning and needs the tightest pre-registration.**
- **Exact spec:** Word-window size = 200 words (fixed, non-overlapping). Style feature vector = function-word frequencies (same top 100 words as Method 1). Distance metric = Jensen-Shannon divergence between consecutive windows. Autocorrelation test = Ljung-Box test on |Δstyle| series (lag=5, p<0.05 = significant structure). Shuffle-null procedure = 1000 permutations of window order; if original autocorrelation > 95th percentile of null distribution, reject exchangeability.
- **Calibration discipline:** Window size fixed at 200 words (no tuning). If Step 1 fails, record as failure — do not adjust window size post-hoc.

### 3. Dialogue-act tagging
- **Literature anchor:** Tag taxonomy traces to Switchboard-DAMSL (Jurafsky, Shriberg & Biasca, Stanford 1997 / *Computational Linguistics* 2000). LLM-judge implementation precedent: Act2P (ACL Findings 2025, LLM-driven dialogue act classification).
- **Exact spec:** Judge model = GPT-4o (temperature 0). Tag set = {assert, question, agree, disagree, propose, concede} (6 acts, simplified from SWBD-DAMSL core). Prompt: "Classify each utterance as one of: assert (statement of fact/opinion), question (request for information), agree (confirmation/assent), disagree (rejection/correction), propose (suggestion/new idea), concede (acknowledgment of validity). Output only the tag name." Frozen prompt — no adjustments after Step 1.
- **Validation before use:** Hand-label 50 random utterances from each of ①②③④ (200 total). Compute Cohen's κ between LLM-judge and human coder. If κ < 0.70, method is invalid — do not proceed to full corpus tagging.

### Process
1. Fill in the 🔲 open decisions above.
2. `git commit` the completed spec as a frozen checkpoint — this is the pre-registration record.
3. Run Step 1 validation exactly as specified, once.
4. Report the result, pass or fail, as written here — do not edit this section after seeing Step 1 results.
5. Any change after this point goes in a **Deviations** subsection (added below, never overwriting the original), with a stated reason.

---

## Key Strength of the Design
The inference about AI reasoning is **method-agnostic**: the conclusion is only as strong as the method's demonstrated performance on the known cells (①②③④), which is directly measurable and reportable. This makes the framework self-validating.

---

*Last updated: July 2026 — cells ①② locked in; cell ③ generated (Game-of-24, 4× qwen-2.5-7b-instruct); cell ④ generated (prompted CoT, qwen-2.5-7b-instruct) as intermediate anchor; cell ⑤ (native reasoning traces) pending — the research question; task-matching rationale and three classification methods added; framework expanded from 2×2 to 2×2+1 to include native reasoning traces as the true dependent variable.*

---

## Notes

### Difficulty scores
The `puzzle_selection.csv` includes `difficulty_score` (based on human RT and fail rate) ranging from approximately -3.1 (easiest) to +2.8 (hardest). These scores can be used for:
- **Difficulty-stratified analysis:** test whether the mono-/dialogic distinction varies with puzzle difficulty
- **Correlation with reasoning structure:** examine whether harder puzzles elicit more dialogic-like reasoning patterns
- **Balanced sampling:** ensure the 200-puzzle set covers the full difficulty range for generalizability
