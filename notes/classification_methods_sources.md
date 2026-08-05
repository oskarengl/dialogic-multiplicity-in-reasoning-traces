# Sources for Classification Methods

This document maps the three classification methods in `research_plan.md` to their literature anchors, with the actual local files in `papers/` that correspond to them.

**Note:** The `research_plan.md` already contains a "Method Pre-Registration" section with the exact literature anchors for each method. The first draft of this file was built from web search; this version is remapped to the anchors in `research_plan.md` and to the local `papers/` directory.

---

## Method 1: Single- vs Multi-Author Classification (PAN Style-Change Detection)

### Literature anchors from `research_plan.md`

- **PAN Multi-Author Writing Style Analysis shared task** (Zangerle et al., running 2016–2026; overview papers: PAN 2021, 2023, 2024).
- **Classical baselines:** character n-gram / function-word frequency similarity.
- **Strong baseline:** fine-tuned DeBERTaV3 + contrastive learning (Ye et al., PAN 2023).

### Local papers in `papers/`

**`papers/antonela/pan_webis.pdf`**
- Title: *Multi-Author Writing Style Analysis 2026* (PAN @ CLEF 2026)
- Relevance: Task description for the PAN style-change detection shared task; describes the exact single/multi-author classification problem and sentence-level change detection.

**`papers/really interesting/invited_paper_2.pdf`**
- Title: *Overview of the Author Identification Task at PAN-2018: Cross-domain Authorship Attribution and Style Change Detection*
- Authors: Kestemont, Tschuggnall, Stamatatos, Daelemans, Specht, Stein, Potthast
- Relevance: PAN-2018 overview covering style change detection and the classical function-word / character n-gram approach.

**`papers/antonela/2401.06752v1.pdf`** (duplicate: `papers/really interesting/2401.06752v1 1.pdf`)
- Title: *Stylometry Analysis of Multi-authored Documents for Authorship and Author Style Change Detection*
- Authors: Zamir, Ayub, Gul, Ahmad, Ahmad
- Relevance: Directly addresses single/multi-authored classification, single change detection, and multiple author-switching detection using stylometric features.

**`papers/antonela/Journal of the American Society for Information Science and Technology - 2008 - Stamatatos - A survey of modern authorship.pdf`**
- Title: *A Survey of Modern Authorship Attribution Methods*
- Author: Efstathios Stamatatos
- Relevance: Foundational survey of stylometric features and authorship attribution methods.

**`papers/really interesting/bevendorff_2025c.pdf`**
- Title: *Overview of PAN 2025*
- Authors: Bevendorff et al.
- Relevance: Recent PAN overview including the multi-author writing style analysis task at the sentence level.

---

## Method 2: Stylometric Step-Change & Exchangeability

### Literature anchors from `research_plan.md`

- **No single canonical paper** — synthesis of:
  - Stylometric distance (background: arXiv:2401.06752, *Stylometry Analysis of Multi-authored Documents for Authorship...*)
  - Statistical change-point / exchangeability testing
- The plan explicitly notes this method is the highest-risk because it has no external baseline to defer to.

### Local papers in `papers/`

**`papers/antonela/2401.06752v1.pdf`**
- Title: *Stylometry Analysis of Multi-authored Documents for Authorship and Author Style Change Detection*
- Relevance: Background for stylometric distance and author-change detection.

**`papers/antonela/Journal of the American Society for Information Science and Technology - 2008 - Stamatatos - A survey of modern authorship.pdf`**
- Title: *A Survey of Modern Authorship Attribution Methods*
- Relevance: General stylometric features (function words, character n-grams, etc.) used in the style distance vector.

**`papers/antonela/2024.emnlp-main.1079.pdf`**
- Title: *An Empirical Analysis of the Writing Styles of Persona-Assigned LLMs*
- Authors: Malik, Jiang, Chai
- Relevance: Uses style embedding + LDA to measure style differences between LLM and human text; relevant for |Δstyle| between windows.

**`papers/antonela/2025.acl-long.443.pdf`**
- Title: *Comparing LLM-generated and human-authored news text using formal syntactic theory*
- Authors: Zamaraeva, Flickinger, Bond, Gómez-Rodríguez
- Relevance: Grammatical comparison of LLM vs human text; relevant for syntactic stylometric features.

**`papers/antonela/paper2.pdf`**
- Title: *Measuring Narrative Fluency by Analyzing Dynamic Interaction Networks in Textual Narratives*
- Authors: Lee, Kim
- Relevance: Dynamic interaction networks / structural change in text; conceptually related to step-change measurement.

**`papers/antonela/srep03691.pdf`**
- Title: *Graph analysis of dream reports is especially informative about psychosis*
- Authors: Mota, Furtado, Maia, Copelli, Ribeiro
- Relevance: Uses speech graph attributes on fixed-word windows; relevant for fixed-window stylometric analysis.

### Missing local source

- **Exchangeability / shuffle-null / change-point testing** itself is not grounded in a local paper. The plan says it is a synthesis of the stylometric-distance paper plus statistical testing, not a method from a specific source.

---

## Method 3: Dialogue-Act Tagging

### Literature anchors from `research_plan.md`

- **Tag taxonomy:** Switchboard-DAMSL (Jurafsky, Shriberg & Biasca, Stanford 1997 / *Computational Linguistics* 2000).
- **LLM-judge implementation precedent:** Act2P (ACL Findings 2025, LLM-driven dialogue act classification).

### Local papers in `papers/`

**No direct local source found.** The local papers below are related but do not cover dialogue-act or speech-act tagging directly:

- `papers/speaker seperation/Identifying Speakers in Dialogue Transcripts A Text-based Approach Using Pretrained Language Models.pdf` — this is **speaker identification**, not dialogue-act tagging.
- `papers/Reasoning Models Generate Societies of Thought.pdf` — motivates the research question (dialogue-like reasoning) but is not a source for the tagging method.

### Missing local source

- **Switchboard-DAMSL paper** (Jurafsky et al., 1997/2000) is not in the `papers/` directory.
- **Act2P** (ACL Findings 2025) is not in the `papers/` directory.

---

## Broader Research Question (AI Reasoning as Monologue or Dialogue)

### Local papers

**`papers/Reasoning Models Generate Societies of Thought.pdf`**
- Title: *Reasoning Models Generate Societies of Thought*
- Authors: Kim, Lai, Scherrer, Agüera y Arcas, Evans
- Relevance: Directly argues that reasoning models simulate multi-agent-like interactions — a "society of thought".

**`papers/reasoning models/(How) Do reasoning models reason.pdf`**
- Title: *(How) Do Reasoning Models Reason?*
- Authors: Kambhampati, Stechly, Valmeekam
- Relevance: Discusses reasoning traces and test-time scaling.

**`papers/reasoning models/Beyond the Last Answer your Reasoning Trace Uncovers More than You Think.pdf`**
- Title: *Beyond the Last Answer: Your Reasoning Trace Uncovers More than You Think*
- Authors: Hammoud, Itani, Ghanem
- Relevance: Analyzes subthoughts in reasoning traces, relevant to segmentation.

**`papers/reasoning models/Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.pdf`**
- Title: *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*
- Authors: Wei et al.
- Relevance: Foundational paper on CoT prompting; supports Cell ④ (AI prompted monologue).

**`papers/reasoning models/How Likely Do LLMs with CoT Mimic Human Reasoning.pdf`**
- Title: *How Likely Do LLMs with CoT Mimic Human Reasoning?*
- Authors: Bao, Zhang, Wang, Yang, Zhang
- Relevance: Causal comparison of LLM CoT and human reasoning.

**`papers/reasoning models/Towards Reasoning Era A Survey of Long Chain-of-Thought for Reasoning Large Language Models.pdf`**
- Title: *Towards Reasoning Era: A Survey of Long Chain-of-Thought...*
- Authors: Chen, Qin, Liu, et al.
- Relevance: Survey of long CoT reasoning models (DeepSeek-R1, o1, etc.).

**`papers/psychology/Society of Mind - Marvin Minski.pdf`**
- Title: *Society of Mind*
- Author: Marvin Minsky
- Relevance: Theoretical basis for multi-agent / "society of mind" framing.

**`papers/psychology/The-Enigma-of-Reason.pdf`**
- Title: *The Enigma of Reason*
- Authors: Hugo Mercier, Dan Sperber
- Relevance: Argues human reasoning evolved as a social, adversarial process.

---

## Summary

| Method | Literature anchors from `research_plan.md` | Local `papers/` files | Missing sources |
|---|---|---|---|
| **Method 1** PAN style-change | PAN Multi-Author Writing Style Analysis (Zangerle et al., 2016–2026); Ye et al. PAN 2023; classical char n-gram / function-word baseline | `pan_webis.pdf`, `invited_paper_2.pdf`, `2401.06752v1.pdf`, `Stamatatos survey.pdf`, `bevendorff_2025c.pdf` | Ye et al. (PAN 2023) paper |
| **Method 2** Stylometric step-change / exchangeability | Synthesis of stylometric distance (arXiv:2401.06752) + change-point/exchangeability testing | `2401.06752v1.pdf`, `Stamatatos survey.pdf`, `2024.emnlp-main.1079.pdf`, `2025.acl-long.443.pdf`, `paper2.pdf`, `srep03691.pdf` | No canonical exchangeability-test paper; the plan states this is a synthesis |
| **Method 3** Dialogue-act tagging | Switchboard-DAMSL (Jurafsky, Shriberg & Biasca 1997/2000); Act2P (ACL Findings 2025) | None directly | Switchboard-DAMSL paper, Act2P paper |

---

*Last updated: July 2026 — remapped to the literature anchors in `research_plan.md` and to local `papers/` files.*
