# Method 2: Sentence-Level Style Change Detection (PAN 2025 SSPC)

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
- **Key relevance:** This is the main literature anchor for Method 2. It provides a sentence-level style change detection method with reported benchmark results (macro-F1: 0.929 EASY, 0.815 MEDIUM, 0.724 HARD on the official PAN 2025 test data).
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

### Pre-registered spec
- **Document-level decision:** Multi-author if the average style-change probability across all sentence boundaries is > 0.5, otherwise single-author.
- **Calibration discipline:** Document-level threshold fixed at 0.5 average probability (no tuning). If Step 1 fails, record as failure — do not adjust the threshold post-hoc.

### Benchmark validation
- **Dataset:** PAN 2025 multi-author style analysis data (https://pan.webis.de/clef25/pan25-web/style-change-detection.html)
- **Expected performance:** macro-F1 of 0.929 (EASY), 0.815 (MEDIUM), 0.724 (HARD) on the official test set
- **Procedure:**
  1. Download PAN 2025 data
  2. Run the released `predict.py` on the test set
  3. Verify F1 scores are within reasonable range of reported values
  4. Only proceed to project data if validation succeeds

---

## Implementation
- **Location:** `implementation/` (cloned from https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis)
- **Status:** ✅ Cloned and ready for validation
- **Main file:** `predict.py`

## Notes
- The previous custom exchangeability method (window + Jensen-Shannon divergence + Ljung-Box test + shuffle null) was replaced because it lacked a single canonical literature anchor.
- The SSPC method is trained to detect style-change points, not single-vs-multi-author documents. Therefore, the document-level binary decision must be validated empirically on the known cells (①②③④).
- The model may detect style changes within single-author documents due to topic/phase shifts; this will be evaluated during Step 1 validation.
