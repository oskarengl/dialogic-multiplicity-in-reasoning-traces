# Findings — papers mined against `Methods.md`

**Purpose.** For every paper in `methods/papers/` (and subfolders), this document collects
concrete findings that are useful for one or more of the methods in `Methods.md`. Each finding
is tagged with the **exact method name(s)** it supports and a **verbatim quote + locator**
(section / PDF page) so it can be dropped straight into the thesis.

> **Locator note.** Quotes are taken from the PDF text layer (extracted with `pdftotext`).
> "p.N" = **PDF page N** (the Nth page of the file), which may differ from the printed page
> number; section titles are given where visible. Minor line-break/hyphenation artifacts from
> extraction have been silently cleaned; wording is otherwise verbatim. `[…]` marks elisions.

---

## Method reference (tag these names exactly)

**Hypotheses.** *H-mono*: one voice moving through phases, transiently adopting perspectives.
*H-soc*: several persistent, distinct, interacting agents.

**Probed properties.** P1 single- vs multi-authored · P2 distinct expertise / dialogicity ("each
persona has its own expertise") · P3 **persistence** (recurrence A…B…A) · P4 **interaction**
(turn-taking structure) · P5 **independence** · P6 **causal load** (does dialogic structure carry
performance / do answers flip-flop) · P7 **mechanistic separability**.

**Methods** (catalogue names used as tags below):

*Stylometric / authorship*
- `Single- vs multi-author classification (PAN style-change detection)`
- `Author diarisation + recurrence test`
- `Stylometric step-change & exchangeability`

*Discourse / dialogue-structure / conversation analysis*
- `Discourse-marker keyword analysis`
- `Dialogue-act tagging`
- `Coherence / cohesion breaks (Coh-Metrix)`

*Lexical / statistical / classic NLP*
- `Pronoun & function-word trajectories`
- `Graph-of-words / co-occurrence community detection`
- `Lexical burstiness / vocabulary-richness regime shifts`
- `Stance oscillation toward the current answer`
- `Answer-evolution across subthoughts (Beyond the Last Answer)`

*Dynamical-systems / time-series*
- `Recurrence Quantification Analysis (RQA)`

*Representational / mechanistic*
- `SAE persona/expertise feature activation`

*Causal / behavioural*
- `Forced-monologue counterfactual`

*Psychology-derived / clinical-linguistic*
- `Varieties-of-Inner-Speech (VISQ) coding`
- `Dialogical-Self / I-position coding (Hermans)`
- `Dissociation — clinical linguistic markers`
- `LIWC / Coh-Metrix psychological profiling per segment`

**Usefulness tags** (how a finding helps): `[METHOD]` provides/implements the technique ·
`[VALIDATION]` gives an anchor/dataset/calibration to validate against · `[CONFOUND]` warns of a
confound/limitation · `[THEORY]` conceptual/theoretical support · `[FRAMING]` useful framing or
related-work citation.

---

# Part A — Findings by paper

## P1 · Hammoud, Itani & Ghanem — *Beyond the Last Answer: Your Reasoning Trace Uncovers More than You Think* (arXiv:2504.20708, 2025)
**File:** `methods/papers/reasoning models/Beyond the Last Answer your Reasoning Trace Uncovers More than You Think.pdf`
**What it is:** Segments a reasoning trace into "subthoughts" at linguistic markers, regenerates a completion+answer from each cumulative prefix, and studies the answer sequence A₁…Aₙ (mode aggregation, entropy). **This is the namesake paper of method 11.**

- **[METHOD] `Answer-evolution across subthoughts (Beyond the Last Answer)`** — the full pipeline is spelled out and reusable verbatim. Abstract (p.1): *"Our approach involves segmenting a reasoning trace into sequential subthoughts based on linguistic cues. We start by prompting the model to generate continuations from the end-point of each intermediate subthought. We extract a potential answer from every completed continuation originating from different subthoughts."* Five formal steps in §3 (p.4): *"1) generating an initial trace, 2) segmenting it based on linguistic cues, 3) prompting completions from these intermediate points, 4) extracting the resulting answers, and 5) analyzing the distribution of these answers."* Code: `https://github.com/hammoudhasan/SubthoughtReasoner` (p.1).
- **[METHOD] `Discourse-marker keyword analysis`** + segmentation for other methods — the explicit marker set is directly usable as a contrast/correction-marker lexicon and as a subthought segmenter. §3.2 (p.4): *"We perform segmentation based on occurrences of words or phrases from a predefined set W, which we refer to as Subthought Transition Markers. These markers often signal reflection, correction, sequencing, or the exploration of alternatives."* The set W (p.4): *"Wait, Alternatively, Another angle, Another approach, But wait, Hold on, Hmm, Maybe, Looking back, Okay, Let me, First, Then, Alright, Compute, Correct, Good, Got it, I don't see any errors, I think, Let me double-check, Let's see, Now, Remember, Seems solid, Similarly, So, Starting, That's correct, That seems right, Therefore, Thus."* They split with regex, marker starting each new chunk (p.5).
- **[VALIDATION] `Answer-evolution across subthoughts` / `Stance oscillation toward the current answer`** — the converge-vs-flip-flop contrast and its link to correctness is exactly the P5/P6 signal both methods want. §4.2 (p.6): *"Consistent Correctness … the sequence of answers (A₁,…,Aₙ) often converges quickly to the correct answer A_true … indicating stable reasoning."* vs *"Fluctuating Incorrectness … the sequence of answers often exhibits high fluctuation. Many different incorrect answers are generated … This suggests unstable reasoning or exploration of incorrect paths."* And the asymmetry (p.7): *"Notably, we did not observe cases in our experiments where A_last was correct but A_mode was incorrect."*
- **[METHOD/VALIDATION] entropy as "internal disagreement" index** — operationalises the methods.md claim that "Entropy of the answer set indexes 'internal disagreement.'" §4.3 (p.8): *"the average entropy for correctly answered problems is significantly lower than for incorrectly answered problems. This quantitatively confirms … that successful reasoning paths tend to exhibit higher internal consistency across subthoughts, while unsuccessful paths are often characterized by high variability and exploration of diverse (incorrect) conclusions."* (Shannon entropy formula, p.7.)
- **[VALIDATION] data + models** — confirms the "math/QA traces (verifiable answers) + model generation access" requirement for methods 10/11. Datasets AIME2024, AIME2025; seven open-weight models incl. **DeepSeek-R1-Distill-Qwen-1.5B/14B, QwQ-32B** (§4.1, p.6) — the same family the `SAE persona/expertise feature activation` method needs.
- **[CONFOUND]** mode-aggregation/self-consistency interpretation: convergence may simply reflect a single dominant attractor, not "voices agreeing." Note when arguing oscillation = debate.

## P2 · Kambhampati, Stechly & Valmeekam — *(How) Do Reasoning Models Reason?* (Ann. NY Acad. Sci. 2025, 1547:33–40)
**File:** `methods/papers/reasoning models/(How) Do reasoning models reason.pdf`
**What it is:** A skeptical "perspective" on large reasoning models (o1, R1). **The single most important counter-framing for the whole thesis** — it argues the persona/thought reading is unwarranted anthropomorphism.

- **[CONFOUND/FRAMING] whole-thesis null hypothesis** — the strongest articulation of "surface dialogue ≠ real process," i.e. the H-mono (or even "no voices at all") null that every method must beat. "Are intermediate tokens actually traces of LLM reasoning?" (p.6): *"The fact that intermediate token sequences often reasonably look like better-formatted and spelled human scratch work—mumbling everything from 'hmm…,' 'aha!,' 'wait a minute' to 'interesting.' along the way—does not tell us much about whether they are used for anywhere near the same purposes that humans use them for … After all, LLMs already imitate the style of everything under the sun, so why would not they also imitate the style of any human musings present in the pretraining data?"* They coin *"large mumbling models."*
- **[CONFOUND] `Discourse-marker keyword analysis`, `Dialogue-act tagging`, `VISQ coding`, `Dialogical-Self / I-position coding`** — every method that reads cognitive meaning into surface markers is directly threatened: markers like "wait/hmm/aha" may be imitated style, not genuine objection/turn-taking moves. Use this to motivate topic-independent / mechanistic checks.
- **[CONFOUND] structure may be format, not function** — bears on segmentation and turn-taking claims. p.5: *"R1 is … trained to respond to all queries using a very specific format: first, a sequence of intermediate 'reasoning' tokens, then a reserved piece of text to mark the transition, and finally … 'answer' tokens. While this segmentation, when interpreted by us, is reminiscent of humans thinking before speaking, it does not carry any special execution-level semantics at inference time—every token is generated just like it would be in a standard LLM."*
- **[FRAMING] terminology** — they deliberately avoid "chain of thought"/"reasoning trace," using *"derivational traces"* as a *"neutral stand-in … rather than the more popular anthropomorphized phrases"* (p.2). Worth citing when you justify your own neutral framing.
- **[FRAMING] "monologue" language + self-consistency** — p.6 calls the traces *"monologues"* ("babble over 30 pages … it is far from clear how to check if these monologues constitute sound reasoning"); p.1 defines self-consistency (*"choose the most common answer"*), the backdrop for mode-based answer-evolution.
- **[CONFOUND] faithfulness** — footnote g (p.6): derivational traces vs *"post facto explanations or rationalizations"*; "such post facto exercises rarely shed any meaningful light on the thinking that went in" — supports treating apparent deliberation cautiously.

## P3 · Bao, Zhang, Wang, Yang & Zhang — *How Likely Do LLMs with CoT Mimic Human Reasoning?* (COLING 2025, pp. 7831–7850)
**File:** `methods/papers/reasoning models/How Likely Do LLMs with CoT Mimic Human Reasoning.pdf`
**What it is:** Causal analysis of CoT — treats instruction Z, CoT X, answer Y as variables, uses interventions + Average Treatment Effect (ATE) to classify each LLM-task into an SCM type (causal chain / common cause / full connection / isolation). **The intervention apparatus for the causal/behavioural methods.**

- **[METHOD] `Forced-monologue counterfactual`** (and causal methods generally) — gives a concrete, citable intervention toolkit transferable to "does removing/altering structure cost performance." §3.2–3.3 (p.4): cause-effect interventions, *"Average Treatment Effect … AT E = E(Y |do(X)) − E(Y )"*, significance via **McNemar's test**; interventions are **golden CoT, random CoT (inject mistakes), random instruction, random bias** (p.4–5). Code: `https://github.com/StevenZHB/CoT_Causal_Analysis` (p.1).
- **[CONFOUND] "reasoning" vs "explaining"** — the central distinction is a direct threat to answer-evolution/stance readings: if the answer-belief precedes the CoT, intermediate-state answers reflect a latent belief, not deliberation. Fig. 2 (p.3): Type II "Explaining, where beliefs of possible answers come before CoT X and an improvement in CoT X cannot improve the answer Y." Abstract/p.2: *"LLMs in these cases may not actually do reasoning (conclude the answer from the CoT) but do explaining (produce the CoT according to the latent belief of the answer)."*
- **[VALIDATION/CONFOUND] P6 causal-load test design** — Type I (causal chain) is detectable as "answers NOT significantly affected by interventions in instructions but … significantly affected by interventions in CoTs" (§4.2, p.5). This is a ready template for testing whether the dialogic structure is load-bearing.
- **[CONFOUND] training effects on causal structure** — Conclusion (p.8): *"ICL strengthening [causal structures] while SFT and RLHF weakening them"*; larger models don't necessarily help. Relevant to choosing models for the `Forced-monologue` fine-tune and interpreting structure.
- **[FRAMING] persona-as-instruction anchors** — uses role prompts ("Please act as a math teacher …", Table 1, p.1; roles Chef/Detective/Judge/Artist in the appendix) as instruction variations — a cheap way to build known-persona / known-expertise prompts for validating P2 methods.
- **Models/data anchors:** GPT-3.5/4, Llama2-7B/70B-Chat, Mistral-7B Base/SFT/DPO; tasks Addition, Multiplication, GSM8K, ProofWriter, FOLIO, LogiQA.

## P4 · Kim, Lai, Scherrer, Agüera y Arcas & Evans — *Reasoning Models Generate Societies of Thought* (arXiv:2601.10825, 15 Jan 2026) ⭐ THE TARGET PAPER
**File:** `methods/papers/Reasoning Models Generate Societies of Thought.pdf` (also in `analyzing emerging reasoning perspectives/…`, out of scope copies)
**What it is:** The paper whose central claim the whole thesis tests. Argues reasoning emerges from an implicit "society of thought" — multi-agent-like dialogue among perspectives with distinct **personalities (Big-5)** and **expertise** — evidenced by LLM-as-judge behavioural coding, **SAE** feature analysis, and **dialogue-vs-monologue RL fine-tuning**. **It is simultaneously the source of several methods' apparatus and the object to be triangulated against — note especially what it does NOT test.**

**Central claim (verbatim, Abstract p.1):** *"enhanced reasoning emerges not from extended computation alone, but from the implicit simulation of complex, multi-agent-like interactions—a society of thought—which enables the deliberate diversification and debate among internal cognitive perspectives characterized by distinct personality traits and domain expertise."* Discussion (p.17): reasoning traces *"evolve from isolated monologues into structured dialogues among differentiated internal perspectives."* → This is exactly the H-soc the thesis weighs against H-mono.

- **[METHOD] `SAE persona/expertise feature activation`** — full, replicable apparatus. Methods §SAE Feature Steering (p.21–23): SAE `15-llamascope-slimpj-res-32k` on **Layer 15 residual stream of DeepSeek-R1-Llama-8B**, dictionary 32,768 features, trained on SlimPajama. Feature descriptions from **Neuronpedia** (GPT-4o-mini); classified by Gemini-2.5-flash-lite into personality/expertise/other: *"Among the 32,768 features, 5,455 are labeled as personality-related (e.g., eagerness, expressions of frustration) and 15,436 as expertise-related (e.g., programming terminology, financial concepts)."* Diversity = **coverage** ("number of unique features within a category … that exhibit non-zero activation across all tokens") + **entropy** over per-feature token counts (formula p.23). Steering = activation addition `h'_t = h_t + s·d_30939`. Feature 30939 = *"a discourse marker for surprise, realization, or acknowledgment"*, conversation ratio **65.7% (99th pct)**, sparsity 0.016% (p.7).
- **[METHOD/VALIDATION] `SAE …` causal result + the EXTENSION GAP** — steering result (p.8–9): *"steering the conversational surprise feature with positive direction (+10) doubles accuracy from 27.1% to 54.8% in the Countdown task, while steering in the negative direction (−10) reduces accuracy to 23.8%"*; +10 raises coverage & entropy of personality- and expertise-features (p.13). **GAP to exploit:** the paper measures diversity (coverage/entropy/SD) but never tests **recurrence/persistence** — whether the same persona/expertise feature set returns later (A…B…A). Methods.md's `SAE …` note ("check recurrence the paper didn't") and `Recurrence Quantification Analysis (RQA)` and `Author diarisation + recurrence test` all target precisely this hole.
- **[METHOD/VALIDATION] `Author diarisation + recurrence test`** — the "Implicit Perspectives" protocol is LLM-as-judge diarisation (Methods p.23): *"(1) inferring the number of distinct perspectives present …, (2) characterizing each perspective's personality traits and domain expertise, and (3) segmenting the reasoning trace by attributing each portion to a specific perspective."* Token→speaker attribution validated with the **Hungarian algorithm**. Again, diversity ≠ recurrence: the paper does not test interleaving (A…B…A vs blocked A A B B), so the recurrence half of the method is novel relative to it.
- **[VALIDATION] the multi-party human anchor for diarisation / dialogue-act / single-vs-multi-author / RQA** — Methods §Validation (p.24): *"Intelligence Squared Debates Corpus—a dataset of human argumentative conversations (N = 1,196 conversations) among two to eight participants with known ground-truth speaker labels and biographical information. To ensure that the model cannot rely on superficial cues such as speaker tags or formatting, we remove all speaker labels and concatenate each dialogue into a single block of text, mimicking the format of LLM reasoning traces."* Token-level speaker accuracy: *"two speakers, accuracy is 82%; for three speakers, 76%; and for four speakers, 69%."* Expertise diversity vs ground-truth biographies Spearman ρ=0.55. **This is the genuine multi-author/turn-taking anchor your methods repeatedly call for.**
- **[METHOD/VALIDATION] `Dialogue-act tagging`** — two ready schemes with reliability. (a) Four **conversational behaviours** (Methods p.18): question–answering, perspective shift, *conflict of perspectives* (*"e.g., 'Wait, that can't be right…', 'No, actually…', and 'This contradicts…'"*), reconciliation. (b) **Bales' Interaction Process Analysis (IPA)** — *"classifies utterances into 12 interaction roles"* → 4 categories: information-giving (suggestion/opinion/orientation), information-asking, positive emotional (solidarity/tension-release/agree), negative emotional (antagonism/tension/disagree) (p.18–19). Reciprocity via **Jaccard index** (ask&give, positive&negative). LLM-judge (Gemini-2.5-Pro) reliability: vs human ICC(3,1) mean .756, vs GPT-5.2 .875 → justifies LLM-judge dialogue-act tagging.
- **[METHOD] `Forced-monologue counterfactual`** — the paper IS the mirror experiment methods.md names. §RL Experiments (p.13–16, Methods p.25–26): three conditions — Baseline (RL only), **Conversation fine-tuning** (SFT on multi-agent dialogue, personas in `<persona1>…`/`<think1>…` turn-taking), **Monologue fine-tuning** (SFT on single-voice `<think>…` traces) — on **Qwen-2.5-3B and Llama-3.2-3B**, identical problems/answers. Result (p.14): *"At step 40, conversation-fine-tuned Qwen-2.5-3B models reach approximately 38% accuracy while monologue-fine-tuned models remain at 28%"*; Llama by step 150 "40% … while monologue-fine-tuned models plateau around 18%." *"This indicates that conversational structure itself, not merely exposure to correct solutions or task-related knowledge, drives the improvement."* Full anchor monologue/dialogue text pairs in Supplementary Table 7.
- **[VALIDATION/THEORY] `Pronoun & function-word trajectories`** — direct evidence that **"we" marks the dialogic turn**. RL Fig.4c–d (p.13, 15): *"by step 120, two distinctive simulated personas have appeared, recognizing their collectivity with the pronoun 'we'"* / *"explicitly recognize their collectivity through the use of the pronoun 'we'."* Strong support that first-person-plural rate is a society marker.
- **[METHOD/VALIDATION] `Discourse-marker keyword analysis`** — markers carry the structure: intro (p.3) *"features … such as the frequent use of words like 'wait,' 'but,' and 'however'—are associated with these behaviours"*; conflict/Q&A marker lists (p.18); Feature 30939 fires on *"Oh!"*. Useful marker inventory + the claim that surprise/contrast markers are causally load-bearing.
- **[CONTRAST] `LIWC / Coh-Metrix psychological profiling per segment`** — the paper profiles each perspective with **BFI-10 Big Five** via LLM-as-judge (items listed p.23; diversity = SD per dimension). Methods.md frames method 18 as the *deterministic alternative to the paper's Big-5* — so this is the exact thing your LIWC/Coh-Metrix per-segment profiling replaces to avoid LLM-judge circularity. Note finding (p.11/16): diversity high in extraversion/neuroticism/agreeableness/openness but **low in conscientiousness** (*"Most R1 reasoning personas were surprisingly disciplined and hard-working!"*).
- **[THEORY/FRAMING] `Dialogical-Self / I-position coding (Hermans)` + `VISQ coding`** — the paper grounds its claim in Bakhtin's *"dialogic self"*, Cooley & Mead's *"looking glass self"*, and Minsky's *Society of Mind* (p.2, refs 28–31, 10), and names recurring I-positions ("critical verifier," "creative ideator," "semantic fidelity checker," "methodical problem-solver," "trial-and-error thinker"). Its dialogic-vs-monologic axis is exactly what VISQ operationalises. Note: the paper cites **Mercier & Sperber's *Enigma of Reason*** (ref 10) and **Minsky's *Society of Mind*** (ref 31) — both are in `psychology/`.
- **Reusable anchors/data:** benchmarks BBH, GPQA, MATH(Hard), MMLU-Pro, MUSR, IFEval (8,262 problems, temp 0.6); models DeepSeek-R1-0528 (671B)/QwQ-32B vs DeepSeek-V3/Qwen-2.5-32B-IT/Llama-3.3-70B-IT/Llama-3.1-8B-IT; DeepSeek-R1-Llama-8B for SAE; Countdown (1,024 problems) + PolitiFact misinformation (23,299 claims). Statistical design: linear probability model with **problem fixed effects + log(trace length) control** (p.20) — the template for "is it structure, not just length?"
- **[CONFOUND] LLM-as-judge circularity** — most behavioural claims rest on Gemini-2.5-Pro judging; your deterministic/classical methods (`Single- vs multi-author`, `Stylometric step-change`, `Graph-of-words`, `Pronoun…`, `Lexical burstiness`, `LIWC/Coh-Metrix`) and SAE/RQA are the independent cross-checks that make triangulation meaningful.

## P5 · Yeo, Tong, Niu, Neubig & Yue — *Demystifying Long Chain-of-Thought Reasoning in LLMs* (arXiv:2502.03373, 2025)
**File:** `methods/papers/reasoning models/Demystifying Long Chain-of-Thought Reasoning in LLMs.pdf`
**What it is:** Mechanics of how long-CoT (branching, backtracking, self-validation) emerges under RL. Mostly background, but contains a clean precedent for marker-counting.

- **[METHOD precedent] `Discourse-marker keyword analysis` / `Lexical burstiness`** — they quantify a reasoning behaviour by counting one keyword: §6.x (p., line ~331): *"We also noted a fall in the branching frequency of the model, which we estimated by counting the number of times the pivot keyword 'alternatively,' appeared in the CoT (Figure 10)."* Direct precedent that marker rate = behaviour proxy.
- **[THEORY] `Stance oscillation` / `Answer-evolution`** — branching/backtracking is the path-switching your stance methods track: *"Branching and Backtracking: The model systematically explores multiple paths (branching) and reverts to earlier points if a particular path proves wrong (backtracking)."* (intro contributions).
- **[CONFOUND] all "emergent dialogue" claims** — §6.1 (p., ~line 530): *"Self-validation behaviors are sometimes flagged as emergent behaviors or 'aha-moment' … However, we notice that sometimes self-validation behaviors already exist in the base model"* — self-correction can pre-exist RL, so apparent dialogic novelty may be baseline behaviour.
- **[METHOD] `Dialogue-act tagging`** — their Action Prompting primitives (§ setup, ~line 108) give a compact move taxonomy: *"clarify, decompose, solution step, reflection, and answer."*

## P6 · Chen et al. — *Towards Reasoning Era: A Survey of Long Chain-of-Thought for Reasoning Large Language Models* (2025)
**File:** `methods/papers/reasoning models/Towards Reasoning Era A Survey of Long Chain-of-Thought for Reasoning Large Language Models.pdf` (110 pp — used as a reference hub)
**What it is:** Large survey organising Long-CoT into **deep reasoning, feasible reflection, extensive exploration** (Fig. 2–3). Value here is framing + a citation hub.

- **[FRAMING/THEORY] `Recurrence Quantification Analysis (RQA)` / `Author diarisation + recurrence test`** — their formal model of reflection is literally "revisiting": §2.2.3 (p., line ~418): *"feasible reflection permits the reasoning path to return to a previously visited node"* (relaxes the acyclic constraint so n_j may equal an earlier n_i). A clean conceptual hook for "does the trace revisit earlier states?" (though about logical nodes, not personas).
- **[FRAMING] taxonomy of detectable behaviours** — deep reasoning / reflection (feedback + refinement, ORM/PRM) / exploration (Fig. 2, §5). Useful to position what `Dialogue-act tagging` and `Discourse-marker` methods are detecting, and as an entry point to the primary literature (extensive reference lists per behaviour).

## P7 · Wei, Wang, Schuurmans, Bosma, Ichter, Xia, Chi, Le & Zhou — *Chain-of-Thought Prompting Elicits Reasoning in LLMs* (NeurIPS 2022, arXiv:2201.11903)
**File:** `methods/papers/reasoning models/Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.pdf`
**What it is:** Foundational CoT paper. Background/definitional for the thesis.

- **[FRAMING] canonical definition** — Abstract (p.1): *"a chain of thought—a series of intermediate reasoning steps"* that improves complex reasoning, abilities that *"emerge naturally in sufficiently large language models."* The standard citation for "what a CoT is."
- **[CONFOUND] surface wording is not the locus of the benefit** — §3.4 Robustness (p.): CoT gains are *"robust to different annotators, exemplars, … and language models"* and to exemplar order/number. Implication for your style/marker methods: the *function* survives big changes in surface voice, so a given lexical/stylistic signature may be incidental rather than load-bearing — argue persona claims beyond mere wording.
- **[FRAMING] `Forced-monologue counterfactual`** — §3.3 Ablations (p.) ("equation only," "variable compute only," "reasoning after answer") establish the template for showing it's the reasoning *content/structure*, not extra compute, that matters — the logic your forced-monologue causal test reuses.

## P8 · Wei, Tay, Bommasani, Raffel, … & Fedus — *Emergent Abilities of Large Language Models* (TMLR 2022)
**File:** `methods/papers/reasoning models/Emergent Abilities of Large Language Models.pdf`
**What it is:** Defines "emergent ability." Purely framing for the thesis.

- **[THEORY/FRAMING] emergence framing for "society of thought"** — p.2: *"Emergence is when quantitative changes in a system result in qualitative changes in behavior"* (after Anderson, "More Is Different"); *"An ability is emergent if it is not present in smaller models but is present in larger models."* Directly supports framing the conversational/society structure as emergent — recall P4 (core paper) finds conversational behaviours absent in instruction-tuned models *regardless of size* (8B–671B) yet present in reasoning models, i.e. emergent with reasoning-training rather than scale.

## P9 · PAN @ CLEF — *Multi-Author Writing Style Analysis* (Webis/PAN shared-task page, 2026 edition) ⭐
**File:** `methods/papers/antonela/pan_webis.pdf` (the shared-task description page)
**What it is:** The PAN "style-change detection" task — **the literal namesake and data source for method 1** (and your `BERT Multiauthor classification/` folder is this task's data + a DistilBERT you trained on it).

- **[METHOD/VALIDATION] `Single- vs multi-author classification (PAN style-change detection)`** — task definition (Task Overview, p.1): *"Given a document, determine at which positions the author changes … for each pair of consecutive sentences, assess whether there was a style change."* Ground truth JSON has `"authors": NUMBER_OF_AUTHORS` and a binary `"changes"` array; evaluated by **macro F1**. Task lineage gives ready sub-tasks: 2018 single-vs-multi, 2019 number of authors, 2020–2022 paragraph-level change, 2022/2025 sentence-level.
- **[VALIDATION] the fix for method 1's headline confound** — methods.md warns a positive may reflect *topic/phase, not personas*; PAN built the cure: *"The previously used datasets exhibited high topic diversity, which allowed the participants to leverage topic information as a style change signal. In the 2023 and 2024 editions … special attention is paid to this issue."* Three difficulty levels (p.1): **Easy** (topic varies — topic usable), **Medium** (small topic variety), **Hard** (*"All sentences in a document are on the same topic"*). → Calibrate/validate your detector on the **Hard** (topic-controlled) split to prove it reads *style*, not topic.
- **[METHOD] `Author diarisation + recurrence test`** — PAN explicitly hosts *"Author Diarization"* (PAN@CLEF'16, Related Work, p.1), the multi-author clustering precedent for your diarisation step.
- **Anchor/data:** train/val/test with ground truth; TIRA deployment; committee Zangerle, Mayerl, Potthast, Stein. Cites Stamatatos's authorship survey (= P10/antonela) as the field reference.

## P10 · Nguyen, Dernoncourt, Yoon, Deilamsalehy, Tan, Rossi, Tran, Bui & Nguyen — *Identifying Speakers in Dialogue Transcripts: A Text-based Approach Using Pretrained Language Models* (Interspeech 2024)
**File:** `methods/papers/speaker seperation/Identifying Speakers in Dialogue Transcripts A Text-based Approach Using Pretrained Language Models.pdf`
**What it is:** Text-based SpeakerID — given a transcript with anonymized IDs + names, assign names — using RoBERTa sentence encoders (single-name + multi-name GCN). Tangential to detecting persona boundaries, but contributes a diarisation primitive.

- **[METHOD] `Author diarisation + recurrence test`** — the transferable idea is "embed each utterance with a PLM and treat the vector as the speaker". §2.3.1 (p.3): *"we posit that their vectors contain unique semantic signatures reflective of each speaker's communicative style or content. Thus, we treat these sentence vectors as proxies for the speakers themselves."* Uses a **prev / current / next** context window around each unit — a usable scheme for per-segment stylometric vectors before clustering. Multi-name variant builds a name-similarity **graph + GCN** so *"different names should be assigned to different speakers"* (§2.3.2, p.3).
- **[CONFOUND] limits** — this assigns *names to already-diarised speakers* (upstream diarization assumed, e.g. SOND); it does not segment style from raw text, and best precision is 80.3% / recall 50% (Table 3, p.4). Borrow the representation idea, not the task framing.
- **Anchor/data:** **MediaSum** corpus (463.6K NPR/CNN interview transcripts, §2.2, p.2) — a large real multi-speaker dialogue source; code `github.com/adobe-research/speaker-identification`.

## P11 · Mota, Furtado, Maia, Copelli & Ribeiro — *Graph Analysis of Dream Reports Is Especially Informative About Psychosis* (Scientific Reports 4:3691, 2014) ⭐
**File:** `methods/papers/antonela/srep03691.pdf`
**What it is:** "Speech Graph Attributes" (SGA) — represent text as a word-adjacency graph and read structural features — to separate schizophrenia/bipolar/control. **The methodological template for method 8, and it pre-implements the fixed-word-window control and graph-based recurrence that methods 3, 7 and 12 need.**

- **[METHOD] `Graph-of-words / co-occurrence community detection`** — exact construction. Results (p.1): *"every word represented a node, and every temporal connection between consecutive words represented an edge."* 14 SGA defined in Methods (p.6): nodes N, edges E, largest connected/strongly-connected components (LCC, LSC), ATD, density, diameter, ASP, clustering coefficient. Free software (custom Java) at `neuro.ufrn.br/softwares/speechgraphs`.
- **[METHOD] `Recurrence Quantification Analysis (RQA)` / `Author diarisation + recurrence test`** — the graph already contains *recurrence* primitives: Methods (p.6) *"recurrence attributes: repeated edges (RE …), parallel edges (PE …), cycles of one (L1 …), two (L2 …) or three (L3 …) nodes."* A graph-of-words recurrence measure (does the trace loop back?) complements time-series RQA on the role/style sequence.
- **[METHOD/VALIDATION] the fixed-word-window control methods.md mandates** — directly mirrors methods.md's "use fixed word-windows, not subthoughts, to avoid denominator artifacts." Results (p.2): *"To rule out the influence of verbosity, we analyzed the reports using a moving window of fixed word length (10, 20 and 30 words) with a step of 1 word. Each report yielded a population of graphs from which we calculated mean SGA."* Cite this as precedent for windowing `Stylometric step-change & exchangeability` and `Pronoun & function-word trajectories`.
- **[VALIDATION] topic/meaning-independence (beats the method-1 confound)** — structure separates groups even with shared vocabulary: Results (p.2) *"irrespective of meaning, clear contrasts emerged"*; and language-invariance (p.5, Fig. 7b) across English/German/French/Spanish/Portuguese — evidence that graph structure is a *topic-independent* signal. Classifier: Naïve Bayes on SGA, AUC up to 0.94.
- **[THEORY] `Dissociation — clinical linguistic markers` / `LIWC / Coh-Metrix profiling`** — a worked clinical-linguistic example that low connectivity ↔ negative/cognitive symptoms; bridges to the `psychology/` dream/dissociation paper (P-?). Note caveat: this is a clinical population, so transfer as analogy.

## P12 · Stamatatos — *A Survey of Modern Authorship Attribution Methods* (JASIST 60(3):538–556, 2009) ⭐ reference
**File:** `methods/papers/antonela/Journal of the American Society for Information Science and Technology - 2008 - Stamatatos - A survey of modern authorship.pdf`
**What it is:** The canonical survey of stylometric authorship attribution — features and classification. The reference text underpinning methods 1–3.

- **[METHOD] `Single- vs multi-author classification` / `Stylometric step-change & exchangeability` / `Author diarisation`** — the feature inventory your stylometry methods draw on: Introduction (p.1): early stylometry proposed *"sentence length, word length, word frequencies, character frequencies, and vocabulary richness functions"*; foundational work used *"frequencies of a small set of common words (e.g., 'and,' 'to,' etc.)"* (Mosteller & Wallace on the Federalist Papers) and Yule's K / vocabulary richness (Yule 1938/1944). Grounds `Lexical burstiness / vocabulary-richness regime shifts` too.
- **[VALIDATION] design checklist for your anchors** — the survey's list of *methodological limitations* (Introduction, p.1) is a ready validity checklist: data *"too long … and probably not stylistically homogeneous,"* *"number of candidate authors … too small,"* *"evaluation corpora were not controlled for topic,"* evaluation *"mainly intuitive,"* and *"comparison … difficult due to lack of suitable benchmark data."* Directly motivates topic-controlled anchors and quantitative nulls in your validation plans.
- **[CONFOUND] CUSUM/QSUM cautionary tale** — a stylometric method *"accepted in courts … however, the research community heavily criticized it and considered it generally unreliable"* (p.1): cite when warning that a plausible-looking style signal needs rigorous null testing (relevant to method 1's low–medium directness).

## P13 · Kestemont, Tschuggnall, Stamatatos, Daelemans, Specht, Stein & Potthast — *Overview of the Author Identification Task at PAN-2018: Cross-domain Authorship Attribution and Style Change Detection*
**File:** `methods/papers/really interesting/invited_paper_2.pdf`
**What it is:** PAN-2018 overview — defines style-change detection (single vs multi-author) and cross-domain attribution; spells out the topic-control rationale and the canonical "style not content" features. Core reference for methods 1–3.

- **[METHOD/VALIDATION] `Single- vs multi-author classification`** — the task in its simplest framing (Introduction, p.2): *"Given a document, are there any style changes or not? An alternative formulation would thus be to predict whether a document is written by a single author or by multiple collaborators."* Exactly method 1's question.
- **[VALIDATION] the topic-control requirement (again, central to beating method 1's confound)** — Introduction (p.2): *"a key requirement is that multi-author documents contain the same topic, as otherwise the task would be simplified (e.g., an author discussing about the first world war might be easily distinguished from a second one writing about programming languages by applying simple vocabulary analyses)."* Their fix: a same-topic Q&A corpus. Use as design rationale + data.
- **[METHOD] topic-independent feature set** — Previous Work (p.3): stylistic fingerprints use *"lexical features like character n-grams …, word frequencies …, average word/sentence lengths …, syntactic features like part-of-speech (POS) tag frequencies/structures … or structural features such as indentation usages."* And the field's guiding principle (p.2): *"features such as function words or common character-level n-grams are typically considered valuable … because they are less strongly tied to the specific content or genre."* This is the answer to methods.md's "beat with topic-independent features."
- **[CONFOUND] short-text limitation** — p.2: such features *"require relatively long documents to be successful and … result in sparse, less useful representations for short documents"* — relevant when segmenting a trace into short windows/subthoughts.

## P14 · Bevendorff et al. — *Overview of PAN 2025: Voight-Kampff Generative AI Detection, … Multi-Author Writing Style Analysis …*
**File:** `methods/papers/really interesting/bevendorff_2025c.pdf`
**What it is:** The current PAN-2025 overview — authoritative status of style-change detection and AI/mixed-authorship detection. Companion to P9 (the task page).

- **[VALIDATION] `Single- vs multi-author classification`** — confirms the continued **Multi-Author Writing Style Analysis** task *"aims to find positions of authorship change"* (Abstract, p.1) and the broader PAN resource base (Introduction, p.2): *"Since the workshop's inception in 2007, we organized 77 shared tasks … and assembled 60 evaluation datasets."* A deep well of calibration corpora for your detector.
- **[VALIDATION] genuine human–AI interleaving anchors** — the Voight-Kampff task targets *"detector sensitivity in the presence of obfuscation and mixed human-machine authorship"* and subtask 2 asks to *"distinguish between 6 different forms of human-AI collaboration … ranging from fully human-written to text with deep AI intervention"* (Introduction, p.2). Exactly the *"genuine multi-model interleavings"* your method 1 must flag as multi-author.

## P15 · Zamir, Ayub, Gul, Ahmad & Ahmad — *Stylometry Analysis of Multi-authored Documents for Authorship and Author Style Change Detection* (arXiv:2401.06752, 2024)
**File:** `methods/papers/antonela/2401.06752v1.pdf` (= `really interesting/2401.06752v1 1.pdf`)
**What it is:** Tackles the exact three sub-problems of methods 1–2 with a fusion of NLP models. Directly operational.

- **[METHOD] `Single- vs multi-author classification` + `Author diarisation`** — Abstract (p.1): *"three key tasks of style analysis: (i) classification of single and multi-authored documents, (ii) single change detection, which involves identifying the point where the author switches, and (iii) multiple author-switching detection in multi-authored documents."* They *"formulate all three tasks as classification problems and propose a merit-based fusion framework that integrates several state-of-the-art … NLP algorithms and weight optimization techniques."*
- **[METHOD] feature tip — keep special characters** — Abstract (p.1): they *"explore the potential of special characters, which are typically removed during pre-processing,"* finding raw (uncleaned) text helps. Useful, cheap, topic-independent signal for your stylometric step-change/diarisation on traces (punctuation is a classic stylometric marker).

## P16 · Rousseau & Vazirgiannis — *Graph-of-Word and TW-IDF: New Approach to Ad Hoc IR* (CIKM 2013, DOI 10.1145/2505515.2505671) ⭐
**File:** `methods/papers/antonela/2505515.2505671.pdf`
**What it is:** The origin of the **graph-of-word** representation — method 8's namesake construction.

- **[METHOD] `Graph-of-words / co-occurrence community detection`** — the canonical definition (Introduction, p.1): *"a novel document representation based on an unweighted directed graph whose vertices represent terms, whose edges represent co-occurrences between the terms within a fixed-size sliding window and whose edge direction represents term order."* It explicitly questions *"the term independence assumption behind the traditional bag-of-word model"* (Abstract). Use this construction per trace, then run community detection to test the paper's "each persona has its own expertise" claim (P2).
- **[METHOD] TW-IDF / term centrality** — they derive term weights from graph structure (*"counting the number of different contexts in which a term occurs"*, Abstract) — a principled way to weight nodes before community detection on a trace's word graph.

## P17 · Malik, Jiang & Chai — *An Empirical Analysis of the Writing Styles of Persona-Assigned LLMs* (EMNLP 2024, pp. 19369–19388) ⭐
**File:** `methods/papers/antonela/2024.emnlp-main.1079.pdf`
**What it is:** Directly tests whether **assigning a persona changes an LLM's measurable writing style** — the crux of whether "personas" in a trace are stylometrically real (P1/P2).

- **[VALIDATION] `Single- vs multi-author classification` / `Author diarisation`** — evidence that personas yield distinguishable styles: Abstract (p.1) *"We find significant style differences among personas."* But tempering method 1's hope (p.2): *"although LLMs' writing styles are not drastically different from those of humans from the same socio-demographic groups, some distinct differences can be observed"* — i.e. within-model persona style differences are real but subtle, matching methods.md's "within-model personas are below [PAN's] resolution." Strong calibration point.
- **[METHOD] tools — LISA + LDA + KL divergence** — Abstract/§1 (p.1): they use *"an interpretable style embedding model called LISA (Patel et al., 2023)"*, derive *"eight coarse-grained styles from the original 768 style attributes,"* and *"measure style differences using Kullback–Leibler divergence to compare LLM-generated and human-written texts."* LISA is a ready per-segment style-vector extractor for your diarisation/step-change/profiling; KL divergence is a clean inter-segment style-distance. Code: `github.com/ra-MANUJ-an/writing-style-persona`.
- **Anchor:** persona socio-demographic groups (age, profession, location, political affiliation) vs real Reddit comments — a human persona-style baseline.

## P18 · Zhang, Gao, Chen et al. — *LLM-as-a-Coauthor: Can Mixed Human-Written and Machine-Generated Text Be Detected?* (Findings of NAACL 2024, pp. 409–436)
**File:** `methods/papers/antonela/2024.findings-naacl.29.pdf`
**What it is:** Defines **"mixtext"** (interleaved human + AI authorship) and releases **MIXSET**. A direct interleaving anchor + cautionary result for method 1.

- **[VALIDATION] `Single- vs multi-author classification`** — MIXSET is the *"genuine multi-author interleaving"* your detector must flag. Abstract (p.1): *"we define mixtext, a form of mixed text involving both AI and human-generated content … MIXSET, the first dataset dedicated to studying these mixtext scenarios."* Includes AI-revised HWT and human-revised MGT, with token- and sentence-level polish/rewrite/adapt operations (Fig. 2, p.2) — graded interleaving for calibrating sensitivity.
- **[CONFOUND]** Abstract (p.1): *"existing detectors struggle to identify mixtext, particularly in dealing with subtle modifications and style adaptability."* Warns that detecting fine-grained authorship switches (your within-trace persona switches) is hard — set expectations and prefer fine-grained, sentence-level detectors.

## P19 · Zamaraeva, Flickinger, Bond & Gómez-Rodríguez — *Comparing LLM-generated and Human-authored News Text Using Formal Syntactic Theory* (ACL 2025, pp. 9041–…)
**File:** `methods/papers/antonela/2025.acl-long.443.pdf`
**What it is:** Uses **HPSG** grammar-type distributions (English Resource Grammar) to separate human vs LLM text — a topic-independent *syntactic* style signal.

- **[METHOD] `Stylometric step-change & exchangeability` / `Single- vs multi-author classification`** — Abstract (p.1): *"We use Head-driven Phrase Structure Grammar (HPSG) to analyze the grammatical structure of the texts … revealing systematic distinctions between human and LLM-generated writing."* Grammar-type frequency vectors are a deep, content-independent feature set for per-segment style comparison — beats the topic confound differently than function words.
- **[FRAMING] hub of human-vs-LLM style markers** — Related Work (p.1) compiles concrete, citable differences: humans show *"more variety of vocabulary, shorter constituents, and more optimized dependency distances"* (Muñoz-Ortiz 2024), greater verb-usage variety, the "delve" vocabulary shift (Juzek & Ward 2025), etc. Useful menu of cheap stylometric features and the argument that *"formal theory"* avoids NLP-tool bias.

## P20 · Wu, Zhan, Wong, Yang, Yang, Yuan & Chao — *DetectRL: Benchmarking LLM-Generated Text Detection in Real-World Scenarios* (NeurIPS 2024 Datasets & Benchmarks)
**File:** `methods/papers/antonela/1096_DetectRL_Benchmarking_LLM.pdf`
**What it is:** Stress-test benchmark for AI-text detection under adversarial/real-world conditions. Useful mainly for the *confounds* it isolates.

- **[CONFOUND] factors that move stylometric detectors** — Abstract (p.1): they *"analyzed the potential impact of writing styles, model types, attack methods, the text lengths, and real-world human writing factors on different types of detectors."* These are precisely the nuisance variables (especially **text length** and **writing style**) your trace-level detectors must control for; cite when arguing your fixed-window/topic-control design.
- **[VALIDATION] adversarial robustness anchor** — uses *"heuristic rules to create adversarial LLM-generated text, simulating various prompts usages, human revisions like word substitutions, and writing noises like spelling mistakes."* A template for null/robustness tests. Benchmark hub (TuringBench, MGTBench, MAGE, M4). Code: `github.com/NLP2CT/DetectRL`.

## P21 · Cutler & Condon — *Deep Lexical Hypothesis: Identifying Personality Structure in Natural Language* (preprint, 2022; arXiv 2203.02092)
**File:** `methods/papers/antonela/2203.02092v1.pdf`
**What it is:** Recovers Big-Five-like personality structure from language models via adjective co-occurrence — bears on the legitimacy of inferring personality from text (method 18) and on the core paper's Big-5 use.

- **[THEORY/METHOD] `LIWC / Coh-Metrix psychological profiling per segment`** — supports that personality structure is latent in language: Abstract (p.2) the LM-derived correlational structure is *"highly similar to that of self- and other-ratings,"* with the first three factors congruent (0.89, 0.79, 0.79). Backs profiling segments for recurring "personalities," and offers a language-based, survey-free route to a personality space.
- **[CONFOUND] which Big-5 dimensions are reliably recoverable** — Abstract (p.2): *"Neuroticism and Openness are only weakly and inconsistently recovered."* Note the tension: P4 (core paper) reports its *largest* persona diversity precisely in **neuroticism** (and high openness). If those dimensions are the least linguistically grounded, an LLM-as-judge Big-5 reading may be noisiest exactly where the society claim is strongest — a pointed cross-check for your deterministic alternative.

## P22 · Saloun, Ondrejka, Malčík & Zelinka — *Personality Disorders Identification in Written Texts* (AETA 2015, Springer LNEE 371, 2016)
**File:** `methods/papers/antonela/978-3-319-27247-4_13.pdf`
**What it is:** Classifies personality-disorder tendencies (fear, procrastination, intolerance of uncertainty) from self-essays via NLP features. Analogy-level support for the clinical-linguistic methods.

- **[METHOD/THEORY] `Dissociation — clinical linguistic markers` / `LIWC / Coh-Metrix profiling`** — Abstract (p.1): a pipeline of *"features extraction, sentiment analysis and classification by well-known classifiers: Naive Bayes, Multi-Class Support Vector Machine, k-Nearest Neighbors and Decision Tree."* A precedent that psychological tendencies leave classifiable lexical/sentiment traces — transfer as analogy (per methods.md's caveat) to per-segment profiling. Modest/older; cite for breadth, not as a primary method.

## P23 · Barrios, Gabay, Cafiero & Debbané — *Detecting Psychological Disorders with Stylometry: the Case of ADHD in Adolescent Autobiographical Narratives* (Computational Humanities Research 2023)
**File:** `methods/papers/antonela/CHR_2023_ADHD.pdf`
**What it is:** SVM on stylometric features detects ADHD from "Self-Defining Memories," then **interprets the model to surface the linguistic markers** — a clean interpretable-stylometry template.

- **[METHOD] `LIWC / Coh-Metrix profiling per segment` / `Dissociation — clinical linguistic markers`** — Abstract (p.2): *"(1) We train a Support Vector Machine (SVM) to predict ADHD diagnosis, (2) we attempt to explain its results by exploring lexical information (3) and unfolding the results of the SVM to identify and analyse the linguistic markers associated with each group"*, reaching 92% accuracy. The "train a classifier, then unfold it into interpretable markers" recipe is directly reusable for finding the markers that separate putative personas/segments.
- **[CONFOUND]** clinical population + autobiographical genre; *"several methodological improvements remain necessary"* — transfer as analogy only, not diagnosis (matches methods.md's dissociation caveat).

## P24 · Bob — *Dissociative Processes, Multiple Personality, and Dream Functions* (American Journal of Psychotherapy 58(2):139–149, 2004)
**File:** `methods/papers/psychology/Dissociative Processes, Multiple Personality, and Dream Functions.pdf`
**What it is:** A theoretical review of dissociation/MPD as a continuum of the normal psyche. The clinical grounding for methods 15–17 — and it supplies the "distinct, recurring, autonomous parts that take turns" template.

- **[THEORY] `Dissociation — clinical linguistic markers`** — the DSM-IV definition is almost a spec for "persistent, distinct, recurring personas" (p.3): *"The presence of two or more distinct identities or personality states (each with its own relatively enduring pattern of perceiving, relating to, and thinking about the environment and self)"* and *"At least two of these identities or personality states recurrently take control of the person's behavior."* Note *"recurrently take control"* = the persistence/recurrence (P3) idea, in clinical language.
- **[THEORY] `Dialogical-Self / I-position coding (Hermans)`** — Jung's psychic complexes as autonomous I-positions (p.2): *"A complex always has its own autonomy and behaves as a split part of the psyche."* And the integrative "Internal Self-helper"/"hidden observer" (p.5) — a meta/coordinator position analogous to a reconciliation role.
- **[THEORY] continuum → analogy licence (and its caveat)** — supports treating "parts" as a normal-psyche continuum, not just pathology: under hypnosis a multiple structure *"was not produced by the hypnosis, but preceded"* it (Bowers & Brecher, p.5), and the paper proposes *"the dreams of healthy persons also represent a reflection of interactions and order of dissociated components of the personality"* (p.9). Use exactly as methods.md instructs — **analogy, not diagnosis** (the whole frame is anthropomorphic/clinical).
- **[FRAMING] cross-link to P11 (graph-of-words)** — schizophrenia framed as *"loss of dissociative inhibitory connections … leading to serious defects in associative connections … 'word salad'"* (p.3) connects dissociation to the connectivity/graph signal Mota et al. quantify.

## P25 · Minsky — *The Society of Mind* (Simon & Schuster, 1986) ⭐ THEORY ANCHOR
**File:** `methods/papers/psychology/Society of Mind - Marvin Minski.pdf` (book — targeted extraction)
**What it is:** The origin of "society of mind," cited by P4 (ref 31) as a direct ancestor of "society of thought." Foundational framing for H-soc.

- **[THEORY/FRAMING] H-soc's intellectual ancestor** — the thesis statement (§1.1 "The Agents of the Mind"): *"you can build a mind from many little parts, each mindless by itself."* And: *"I'll call Society of Mind this scheme in which each mind is made of many smaller processes. These we'll call agents. Each mental agent by itself can only do some simple thing that needs no mind or thought at all. Yet when we join these agents in societies — in certain very special ways — this leads to true intelligence."* (§1.3 "The society of mind" develops it.) Cite to motivate the H-soc reading.
- **[CONFOUND/FRAMING] crucial distinction for your H-mono↔H-soc axis** — Minsky's agents are **mindless and sub-cognitive**, *not* personality-bearing personas. This is a sharper alternative to the core paper's "personas with Big-5 + expertise": a trace could be a society of *functional* agents (closer to the SAE-feature view, method 13) without being a society of *characters*. Flag that "society of mind" ≠ "society of personalities" — an important hypothesis to separate.
- **[THEORY] `SAE persona/expertise feature activation`** — the "polyneme" (an agent broadcasting to several agencies, setting independent property-states) is a concrete pre-image of distributed, reusable features — a conceptual bridge to reading SAE features as the real "agents."

## P26 · Mercier & Sperber — *The Enigma of Reason* (Harvard University Press, 2017) ⭐ THEORY ANCHOR
**File:** `methods/papers/psychology/The-Enigma-of-Reason.pdf` (book — targeted extraction)
**What it is:** The "interactionist / argumentative theory of reason," cited by P4 (ref 10) as the core motivation for why reasoning would be social. The single best theory cite for *why* a society-of-thought should help — and, read against the grain, a confound about post-hoc rationalization.

- **[THEORY/FRAMING] why H-soc is plausible** — the thesis (Introduction): *"reason … is first and foremost a social competence"* (p./line 249); *"Reason, we argue, has two main functions: that of producing reasons for justifying oneself, and that of producing arguments to convince others"* (Intro). Reason *"evolved as an adaptation to a very special ecological niche … intense social relationships, powerful languages, and rich culture"* (Ch. 7). This is the deep motivation behind simulating debate inside one model.
- **[THEORY] `Stance oscillation` / `Dialogue-act tagging` / `VISQ coding` / `Forced-monologue counterfactual`** — the advocate-vs-evaluator dynamic and the claim that *"solitary reasoning is biased and lazy, whereas argumentation is efficient"* (Intro, p./line 247) is the human prediction your debate-vs-monologue methods test: a true society should oscillate (advocate/critic) and outperform monologue (P4/P6).
- **[CONFOUND] reasoning vs rationalization (ties P2 Kambhampati + P3 Bao)** — Mercier & Sperber argue most reasons are *after-the-fact*: *"conscious reasoning … seemed to do was just provide a 'rationalization' for a choice that had been made prior to actual reasoning"* (Ch. 2, line 768); *"The main role of reasons is not to motivate or guide us … but to explain and justify after the fact the conclusions we have reached"* (Part III, line 1559). So apparent in-trace deliberation may be justification of an already-settled answer — exactly Bao et al.'s "explaining," and a caution for `Answer-evolution` / `Stance oscillation`.
- **[FRAMING] myside/confirmation bias as a feature** — their account that biases are *adaptations* of an argumentative mechanism supports the "diverse voices avoid the echo chamber" argument P4 makes about why diversity (not a single biased voice) improves accuracy.

## P27 · Lee & Kim — *Measuring Narrative Fluency by Analyzing Dynamic Interaction Networks in Textual Narratives* (Text2Story'20 Workshop)
**File:** `methods/papers/antonela/paper2.pdf`
**What it is:** Builds a **dynamic entity co-occurrence network** over a text (segmented by paragraph) and reads narrative fluency from how its structure (centrality, structural change) evolves. The temporal/graph-dynamics cousin to P11/P16.

- **[METHOD] `Graph-of-words / co-occurrence community detection`** — entity network construction (Abstract/Def. 1–2, p.1–2): *"a dynamic interaction network (called 'entity network'), which has entities as nodes and co-occurrences between the entities as edges"*; *"If a narrative consistently concentrates on a topic or subject, its entity network will have few entities with high node centrality."* Node-centrality concentration ≈ topical/expertise focus — usable to test P2 ("each persona has its own expertise") on a trace.
- **[METHOD] `Recurrence Quantification Analysis (RQA)` / `Stylometric step-change & exchangeability`** — the key extra over static graph-of-words is **tracking structural change across a sequence**: they segment by paragraph as a time window and measure *"structural changes in the entity network"* via graph embeddings to capture "rapidity." This is a template for a per-window graph-feature *sequence* you can then feed to step-change/recurrence/RQA analysis on a CoT trace.
- **[METHOD] `Coherence / cohesion breaks (Coh-Metrix)`** — three consistency criteria (Abstract, p.1): *"(i) consistency in each paragraph, (ii) consistency in the overall narrative, and (iii) consistency between the title and body"* — operational cohesion measures over a graph, complementary to lexical Coh-Metrix.
- **Anchor:** NYT editorials + human evaluators; uses sentence = interaction unit, paragraph = time window (segmentation choices to reuse or contrast with subthought segmentation).

---

# Part B — Method → findings index

*(Built after all papers are read — cross-references every finding above under each method.)*

Each method lists the papers that support it (⭐ = primary/most useful), with a one-line note. See Part A for the verbatim quotes + locators.

### Stylometric / authorship
**`Single- vs multi-author classification (PAN style-change detection)`**
- ⭐ P9 PAN task — the literal task/data; calibrate on the **Hard** (same-topic) split.
- ⭐ P13 PAN-2018 overview — definition + topic-control rationale + topic-independent features (function words, char n-grams, POS).
- P12 Stamatatos — feature taxonomy + evaluation-validity checklist.
- P14 PAN-2025 overview — current status; mixed human–AI authorship subtask.
- P15 Zamir — single/multi classification as a built system (merit-fusion; keep special characters).
- P18 MIXSET — interleaving anchor (and warning: detectors struggle on fine switches).
- P17 Malik — persona styles *are* separable but subtle (calibrates method-1's resolution limit).
- P19 HPSG · P11 srep03691 — topic-independent structural/syntactic signals.
- P20 DetectRL — nuisance variables to control (length, style). P4 — LLM-judge separates multi-persona vs single. P2 — CONFOUND (style imitation).

**`Author diarisation + recurrence test`**
- ⭐ P4 core — LLM-judge diarisation (perspective count, per-segment Big-5/expertise, token attribution, Hungarian) + Intelligence Squared anchor; **does NOT test recurrence — that half is your novelty.**
- P10 speaker separation — PLM sentence embedding as speaker proxy; prev/cur/next window.
- P11 srep03691 — graph recurrence attributes + fixed-word-window. P15 Zamir — multiple author-switch detection. P17 Malik (LISA vectors). P27 paper2 (structural change over sequence). P9 PAN — Author Diarization task.

**`Stylometric step-change & exchangeability`**
- ⭐ P11 srep03691 — the **fixed-word-window** verbosity control methods.md mandates.
- P17 Malik — KL divergence between segment style distributions. P19 HPSG / P12 Stamatatos / P13 PAN — topic-independent features. P15 Zamir — punctuation/special chars. P27 paper2 — per-window structural change.

### Discourse / dialogue-structure
**`Discourse-marker keyword analysis`**
- ⭐ P1 Beyond the Last Answer — explicit Subthought Transition Marker set W.
- ⭐ P5 Demystifying — precedent: count "alternatively" as a branching proxy.
- P4 core — wait/but/however; conflict-marker phrases; Feature 30939 (surprise). P2 — CONFOUND (markers may be imitated style, not real moves).

**`Dialogue-act tagging`**
- ⭐ P4 core — 4 conversational behaviours + **Bales IPA (12 roles → 4 categories)**; Jaccard reciprocity; LLM-judge ICC reliability.
- P5 Demystifying — action primitives (clarify/decompose/solution/reflection/answer). P26 Enigma — advocate vs evaluator acts. P2 — CONFOUND.

**`Coherence / cohesion breaks (Coh-Metrix)`**
- ⭐ P27 paper2 — three consistency criteria over an entity network. P11 srep03691 — connectivity as cohesion. P4 — perspective-segment boundaries.

### Lexical / statistical / classic NLP
**`Pronoun & function-word trajectories`**
- ⭐ P4 core — emergent personas mark collectivity with **"we"** (direct evidence). P12/P13 — function words as classic, topic-independent markers. P11 — fixed-word-window method.

**`Graph-of-words / co-occurrence community detection`**
- ⭐ P16 Rousseau — canonical graph-of-word construction (sliding-window co-occurrence, directed). ⭐ P11 srep03691 — speech-graph attributes (+ software). P27 paper2 — entity network, node centrality, dynamic.

**`Lexical burstiness / vocabulary-richness regime shifts`**
- P12 Stamatatos — Yule's K, vocabulary-richness functions. P5 Demystifying — marker-rate regime/branching frequency. P11 — windowed SGA.

**`Stance oscillation toward the current answer`** ⭐
- ⭐ P1 Beyond the Last Answer — converge (monologue) vs flip-flop (debate) + entropy.
- ⭐ P3 Bao — CONFOUND: "explaining" (answer precedes CoT) vs "reasoning". P5 — branching/backtracking. P26 Enigma — advocate vs critic. P4 — conflict of perspectives.

**`Answer-evolution across subthoughts (Beyond the Last Answer)`**
- ⭐ P1 — THE method (segmentation → completions → mode/entropy; code available). P3 Bao — explaining-vs-reasoning caveat. P2 — self-consistency framing.

### Dynamical-systems / time-series
**`Recurrence Quantification Analysis (RQA)`**
- ⭐ P4 core — the **gap to exploit** (diversity measured, recurrence not). ⭐ P11 srep03691 — graph recurrence attributes (L1/L2/L3, repeated/parallel edges). P27 paper2 — structural change over sequence. P6 survey — reflection = "return to a previously visited node". P24 — "recurrently take control".

### Representational / mechanistic
**`SAE persona/expertise feature activation`**
- ⭐ P4 core — THE apparatus to replicate & extend (SAE `15-llamascope-slimpj-res-32k`, DeepSeek-R1-Llama-8B L15, 32,768 feats → 5,455 personality / 15,436 expertise; coverage + entropy; Feature 30939 steering). **Extension = recurrence/persistence of feature sets, which the paper omits.**
- P25 Minsky — "polyneme"/mindless agents as a closer match to features than to personas. P1 — open models (R1-distill, QwQ) available.

### Causal / behavioural
**`Forced-monologue counterfactual`**
- ⭐ P4 core — THE mirror experiment (conversation-SFT vs monologue-SFT before RL on Qwen-2.5-3B, Llama-3.2-3B; identical problems; conversation wins).
- ⭐ P3 Bao — causal-intervention toolkit (ATE, McNemar, golden/random CoT). P7 Wei — ablation template. P26 Enigma — argumentation beats solitary reasoning.

### Psychology-derived / clinical-linguistic
**`Varieties-of-Inner-Speech (VISQ) coding`**
- ⭐ P26 Enigma — dialogic reasoning theory. P4 — dialogic↔monologic axis operationalised. P24 — "other people's voices". P25 Minsky — society framing.

**`Dialogical-Self / I-position coding (Hermans)`**
- ⭐ P4 core — named recurring I-positions (critical verifier, creative ideator…); cites Bakhtin/Cooley/Mead. ⭐ P24 — Jung complexes as autonomous positions; Internal Self-helper. P25 Minsky; P26 Enigma.

**`Dissociation — clinical linguistic markers`**
- ⭐ P24 — DSM-IV "distinct identities … recurrently take control" (+ analogy caveat). P11 srep03691 — connectivity / "word salad". P23 Barrios — ADHD stylometry + interpretable markers. P22 Saloun — disorder detection from text.

**`LIWC / Coh-Metrix psychological profiling per segment`**
- ⭐ P4 core — Big-5/BFI-10 per perspective (the thing this method replaces *deterministically*). P21 Deep Lexical Hypothesis — personality structure in language (Neuroticism/Openness weakly recovered → CONFOUND). P23 Barrios / P22 Saloun — clinical profiling. P17 Malik — LISA style attributes.

---

### Cross-cutting assets (reusable across methods)

**Validation anchors (genuine multi-author / debate / monologue):**
- ⭐ **Intelligence Squared Debates Corpus** (P4) — N=1,196 human debates, 2–8 speakers, labels + biographies; concatenated label-free to mimic a trace. The headline anchor for diarisation/dialogue-act/single-vs-multi/RQA.
- **PAN corpora** (P9, P13, P14) — single/multi-author, topic-controlled (Hard), Author Diarization; **MIXSET** (P18) human–AI interleavings; **MediaSum** (P10) 463.6K interviews.
- **Monologue vs dialogue text pairs** (P4, Suppl. Table 7) — ready H-mono/H-soc anchors.

**Datasets / tasks for trace generation:** BBH, GPQA, MATH(Hard), MMLU-Pro, MUSR, IFEval (P4); AIME2024/2025 (P1); Countdown + PolitiFact (P4); GSM8K/ProofWriter/FOLIO/LogiQA (P3).

**Models:** DeepSeek-R1 / QwQ-32B vs DeepSeek-V3 / Qwen-2.5-32B-IT / Llama-3.x-IT (P4); **DeepSeek-R1-Llama-8B + its SAE** for mechanistic work (P4); R1-distill family (P1); Qwen-2.5-3B / Llama-3.2-3B for RL (P4).

**Tools:** LISA interpretable style embeddings + KL divergence (P17); SpeechGraphs Java + SGA (P11); graph-of-word/TW-IDF (P16); SubthoughtReasoner code (P1); CoT_Causal_Analysis code (P3); LLM-as-judge with ICC reliability (P4); BFI-10 (P4), Bales IPA (P4).

**Two extension gaps the target paper leaves open (your contribution space):**
1. **Recurrence/persistence (P3 property).** P4 measures *diversity* (coverage, entropy, SD) but never tests whether voices/feature-sets *recur* (A…B…A). → methods `Author diarisation + recurrence test`, `RQA`, `SAE … (recurrence)`, `Stylometric step-change`.
2. **LLM-judge circularity.** Most of P4's behavioural evidence is Gemini-as-judge. → deterministic/classical cross-checks (`Single- vs multi-author`, `Stylometric step-change`, `Graph-of-words`, `Pronoun…`, `Lexical burstiness`, `LIWC/Coh-Metrix`) and mechanistic SAE/RQA make the triangulation independent.

**The standing null hypothesis to beat (cite throughout):** P2 Kambhampati ("derivational traces" are imitated style, not personas; structure may be format not function) + P3 Bao ("explaining" not "reasoning") + P26 Enigma (reasons as after-the-fact rationalization). Any society claim must survive these.
