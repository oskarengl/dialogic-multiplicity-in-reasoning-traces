# Method 2: Sentence-Level Style Change Detection (PAN 2025 SSPC)

> The PDFs referenced below by filename are not included in this repository.
> Each entry carries a link or full citation.

## Overview
Method 2 is now the **Sequential Sentence Pair Classifier (SSPC)** from PAN 2025 (CLEF). It detects sentence-level style changes by encoding each sentence with a pre-trained language model, contextualizing the sequence with a BiLSTM, and classifying each adjacent sentence pair as same-author or different-author. The document-level binary label (single vs multi-author) is derived from the average style-change probability across all sentence boundaries.

---

## Sources

### 1. PAN 2025 SSPC Paper (Primary Literature Anchor)
**File:** `pan2025_sequential_sentence_pair_style_change.pdf`
- **Title:** Style Change Detection using a Sequential Sentence Pair Classifier
- **Authors:** Gleb Schmidt, Johannes Römisch, Mariia Halchynska, Svetlana Gorovaia, Ivan P. Yamshchikov
- **Venue:** PAN Lab at CLEF 2025, CEUR Workshop Proceedings, Vol. 4038
- **Open-source code:** https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis
- **Key relevance:** This is the main literature anchor for Method 2. It provides a sentence-level
  style change detection method. **Correction (checked directly against the PDF, the figures below
  had been misquoted):** the paper reports two different macro-F1 sets that don't agree with each
  other — the abstract states 0.923 / 0.828 / 0.724 (EASY/MEDIUM/HARD, "evaluated on the official
  PAN 2025 test datasets"), while Table 3 ("Performance of Claude and Sequential Sentence Pair
  Classifier on the official PAN 2025 test data") states 0.929 / 0.815 / 0.731. A prior version of
  this file quoted 0.929 / 0.815 / 0.724 — easy and medium from Table 3, hard from the abstract —
  which is neither number the paper actually reports. Not using either figure as a validation
  target; see the corrected Benchmark Validation section below.
- **Key concepts:**
  - Sentence-level style change detection
  - Pre-trained language model (`StyleDistance/styledistance`) for sentence encoding
  - 5-layer bidirectional LSTM for contextualization
  - 3-layer MLP classifier for adjacent sentence pairs
  - Binary classification threshold = 0.5 (sigmoid)

### 2. arXiv:2401.06752 (Background)
**File:** `2401.06752v1.pdf`
- **Title:** Stylometry Analysis of Multi-authored Documents for Authorship and Author Style Change Detection
- **Authors:** Zamir, Ayub, Gul, Ahmad, Ahmad
- **Key relevance:** General background on stylometry for multi-authored documents. Provides context for the broader task of style change detection.

### 3. Stamatatos Survey (Background)
**File:** `Journal of the American Society for Information Science and Technology - 2008 - Stamatatos - A survey of modern authorship.pdf`
- **Title:** A Survey of Modern Authorship Attribution Methods
- **Author:** Efstathios Stamatatos
- **Key relevance:** Foundational survey of stylometric features and authorship attribution methods. Provides background on the concept of writing style as a measurable feature.

---

## Key Points for Implementation (from research_plan.md)

### Literature anchor
- **Primary:** Schmidt et al. (2025), PAN 2025 Sequential Sentence Pair Classifier (SSPC)
- **Code:** https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis (cloned into `implementation/`)
- **Base encoder:** `StyleDistance/styledistance` (frozen)
- **Pooling:** Mean pooling of token embeddings
- **Contextualization:** 5-layer BiLSTM (hidden dim 256, dropout 0.2)
- **Classifier:** 3-layer MLP with GELU activations and dropout 0.2
- **Threshold:** 0.5 (sigmoid; default from released code)

### Pre-registered spec — corrected
- **Retracted claim:** an earlier version of this file asserted "multi-author if average
  style-change probability > 0.5, no tuning" as a paper-sourced rule. Searched the PDF directly for
  "threshold" and "0.5" — this document-level aggregation rule does not appear anywhere in the
  paper. It looks like something asserted in an earlier pass of this project, not a paper finding,
  and is not used. The 0.5 figure that *is* real and paper/code-sourced is the **per-adjacent-pair**
  sigmoid threshold inside `predict.py`'s `get_predictions` (`threshold = kwargs.get("threshold",
  0.5)`) — a different claim from a document-level decision rule. See `methods.md` §2 for the
  actual pre-registered document-level metric (mean raw per-pair probability, no threshold).

### Benchmark validation — corrected
- **Dataset:** PAN 2025 multi-author style analysis data (https://pan.webis.de/clef25/pan25-web/style-change-detection.html)
- **Retracted claim:** "expected macro-F1 of 0.929 / 0.815 / 0.724" — not a real citation, see the
  correction under Source 1 above. Not using either of the paper's two (mutually inconsistent)
  reported figures as a validation target.
- **Procedure, unchanged in spirit:** running the released `predict.py` on the official PAN 2025
  test set as a sanity check that the implementation works remains a reasonable idea; it's just no
  longer gated on matching a specific reported number, since there isn't one clean figure to match.

---

## Implementation
- **Location:** `implementation/` (cloned from https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis)
- **Status:** ✅ Cloned and ready for validation
- **Main file:** `predict.py`

## Notes
- The previous custom exchangeability method (window + Jensen-Shannon divergence + Ljung-Box test + shuffle null) was replaced because it lacked a single canonical literature anchor.
- The SSPC method is trained to detect style-change points, not single-vs-multi-author documents. Therefore, the document-level binary decision must be validated empirically on the known cells (①②③④).
- The model may detect style changes within single-author documents due to topic/phase shifts; this will be evaluated during Step 1 validation.
