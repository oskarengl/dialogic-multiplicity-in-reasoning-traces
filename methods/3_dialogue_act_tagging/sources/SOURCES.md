# Method 3: Dialogue-Act Tagging Sources

## Overview
This folder contains sources for the dialogue-act tagging method. The method labels each sentence with one of the 27 Dialogue Acts from the Conversation Analysis Modelling Schema (CAMS) and counts adjacency pairs (e.g., question→answer, suggestion→accept/decline, inform→agreement/disagreement) as a supplementary structural signal. Tag definitions are taken verbatim from the CAMS website; the adjacency pair concept is grounded in Schegloff & Sacks (1973) and operationalised in CAMS.

---

## Status: **LOCAL SOURCES AVAILABLE**

This folder now contains local sources for dialogue-act tagging, including the CAMS labeling prompt (27 tags with verbatim definitions), the CAMS schema reference, the foundational Schegloff & Sacks (1973) paper on adjacency pairs, and DAMSL/Switchboard-DAMSL manuals.

---

## Literature Anchor (from research_plan.md)

### Primary sources cited:
1. **CAMS** (Duran & Battle 2018) — *Conversation Analysis Modelling Schema* — domain-agnostic schema combining Dialogue Acts and Adjacency Pairs, based on ISO 24617-2 (DiAML) and Conversation Analysis (primary source for tag set)
2. **DAMSL** (Allen & Core 1997) — *Draft of DAMSL: Dialog Act Markup in Several Layers* — foundational operational definitions
3. **Switchboard-DAMSL** (Jurafsky, Shriberg & Biasca, Stanford 1997 / *Computational Linguistics* 2000) — Switchboard implementation of DAMSL
4. **Act2P** (ACL Findings 2025, LLM-driven dialogue act classification)
5. **Schegloff & Sacks (1973)** - "Opening Up Closings" (*Semiotica* 8(4)) — foundational work on adjacency pairs in conversation analysis

### Local sources:
- `CAMS_LLM_labeling_prompt.txt` — Full CAMS definitions and annotation guidelines extracted verbatim from https://nathanduran.github.io/Conversation-Analysis-Modelling-Schema/ for use as the LLM prompt
- `CAMS_schema_full.html` — Full CAMS website saved as HTML for reference
- `Schegloff_Sacks_1973_Opening_Up_Closings.pdf` — Downloaded from Stanford University (https://web.stanford.edu/~eckert/Courses/l1562018/Readings/SchegloffSacks1973.pdf)
- `implementation/label_dialogue_acts.py` — Pipeline skeleton for sentence splitting, LLM labeling, and adjacency pair counting

### Pre-registered spec (from research_plan.md):
- **Judge model:** LLM (to be determined), temperature 0
- **Tag set:** Full CAMS 27 Dialogue Acts (see research_plan.md for full list)
- **Prompt:** `CAMS_LLM_labeling_prompt.txt` with appended instruction to output exactly one tag name per sentence
- **Validation:** Hand-label 50 random utterances from each of ①②③④ (200 total); compute Cohen's κ; if κ < 0.70, method is invalid

---

## Web Sources Found

### 1. CAMS (Conversation Analysis Modelling Schema) — Duran & Battle 2018
- **Main website:** https://nathanduran.github.io/Conversation-Analysis-Modelling-Schema/ (✅ **DOWNLOADED** locally as `CAMS_schema_full.html` and `CAMS_LLM_labeling_prompt.txt`)
- **GitHub repository:** https://github.com/NathanDuran/Conversation-Analysis-Modelling-Schema
- **Paper:** Duran, N. & Battle, S. (2018). "Conversation Analysis Structured Dialogue for Multi-Domain Dialogue Management" — https://www.researchgate.net/publication/329809503_Conversation_Analysis_Structured_Dialogue_for_Multi-Domain_Dialogue_Management

### 2. DAMSL (Dialog Act Markup in Several Layers) — Allen & Core 1997
- **Revised manual:** https://www.cs.rochester.edu/research/speech/damsl/RevisedManual/ (referenced only, not retained locally)

### 3. Switchboard-DAMSL
- **Stanford manual:** https://web.stanford.edu/~jurafsky/ws97/manual.august1.html (referenced only, not retained locally)
- **Colorado technical report (PDF):** https://www.colorado.edu/ics/sites/default/files/attached-files/97-02-part1.pdf
- **Project page:** http://web.stanford.edu/~jurafsky/ws97/
- **Citation:** Jurafsky, D., Shriberg, L., & Biasca, D. (1997). Switchboard Dialog Act Corpus. Institute of Cognitive Science Technical Report 97-02, University of Colorado.

### 4. Act2P
- **ACL Anthology page:** https://aclanthology.org/2025.findings-acl.1052/
- **Direct PDF:** https://aclanthology.org/2025.findings-acl.1052.pdf
- **DOI:** https://doi.org/10.18653/v1/2025.findings-acl.1052
- **Citation:** Zhang, W., & Wang, Y. (2025). Act2P: LLM-Driven Online Dialogue Act Classification for Power Analysis. In *Findings of the Association for Computational Linguistics: ACL 2025* (pp. 20494–20504).

---

## Next Steps
- ✅ **RESOLVED:** Schegloff & Sacks (1973) paper downloaded and available locally
- ✅ **RESOLVED:** Switchboard-DAMSL coders manual downloaded and available locally
- ✅ **RESOLVED:** CAMS definitions and annotation guidelines downloaded and saved as `CAMS_LLM_labeling_prompt.txt`
- **Optional:** Consider downloading Act2P paper for completeness
- **Implementation:** Proceed with dialogue act tagging using full CAMS 27-tag set and adjacency pair counting as specified in research_plan.md

---

## Notes
- The local paper `papers/speaker seperation/Identifying Speakers in Dialogue Transcripts...` is about speaker identification, NOT dialogue-act tagging — it was excluded as not directly relevant
- **Method 3 now has key local sources:** CAMS (primary source for 27-tag set and adjacency pair operationalisation); Schegloff & Sacks (1973) (foundational adjacency pair theory); DAMSL/Switchboard-DAMSL (foundational definitions, referenced via web links only)
- The method uses the full CAMS 27-tag set with definitions taken verbatim from the source. Adjacency pair counting is a simple comparative metric (e.g., question→answer, suggest/request/offer→accept/decline, inform→agreement/disagreement) rather than claiming literature-anchored classification thresholds