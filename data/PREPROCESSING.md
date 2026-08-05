# Preprocessing Documentation

This document contains all preprocessing decisions, schema definitions, standardization rules, and transformations applied to the datasets in `00_core-2x2/`. Last updated: 2026-07-14.

**Goal:** Ensure all datasets have consistent structure and formatting for fair comparison.

---

## Preprocessing Policy Decisions (2026-07-10, revised 2026-07-14)

These decisions govern all future preprocessing work and supersede any conflicting statements elsewhere in this document. They came out of a review of why we normalize, what counts as a nuisance artifact vs. a real structural signal, and how to verify the cleaning actually worked.

### 1. Replace, don't delete (CURRENT IMPLEMENTATION: DELETE)
**Problem:** Outright deleting disallowed characters (`filter_character_set` in `standardize_datasets.py`) can jam adjacent text together at the deletion site (e.g. a 500-character Chinese run removed from mid-sentence leaves a discontinuity/scar exactly where the contamination was). A step-change or exchangeability method could key on that scar instead of genuine authorial structure — reintroducing the exact problem the cleaning was meant to solve.

**Policy:** Wherever a disallowed character or run of characters is stripped, replace it with a single space (word-boundary-preserving placeholder) instead of deleting it outright. Collapse-multiple-spaces normalization (already applied) then absorbs the placeholder cleanly without leaving a jam. This applies to: foreign-script runs (Chinese/Japanese/Korean), emoji, decorative/special unicode, and special punctuation.

**Status:** 🟡 Decided, but not fully implemented. `scripts/standardize_datasets.py::filter_character_set` currently deletes disallowed characters. For the current processing run (2026-07-14), deletion was retained for non-essential symbols (special unicode math symbols like ≈, →, ≠, decorative symbols, emojis, Chinese characters). Curly quotes and backticks are remapped to semantically equivalent ASCII characters (`'` and `"`), so no scar risk there. The replace-with-space update is still pending for future refinement if deletion scars are detected in leakage probes.

**Current approach:** Delete all characters outside the `ALLOWED_CHARS` set, except for quote normalization and LaTeX conversions which happen before character filtering. Processed `*_processed.jsonl` files in `00_core-2x2/` were generated with this deletion policy.

### 2. Document length / turn count is NOT a nuisance variable — do not normalize it away
**Clarification:** AI/human debates will always run longer than solo monologues on the same task — that is a direct, expected consequence of the mono-/dialogue manipulation itself, not a pipeline artifact. Trying to equalize length across conditions in preprocessing would destroy real signal (turn-taking structure is partly *defined* by having more text to divide into turns).

**Policy:** Leave length/turn-count differences untouched in preprocessing. Handle them at the analysis stage instead — e.g. report length as a covariate, use fixed-word-window chunking (already planned for Method 2) so window count scales with document length rather than biasing per-window statistics, and interpret any leakage-probe result on length-derived features as expected, not as evidence of contamination.

### 3. Normalization intensity is comparison-specific, not global
- **① human monologue, ② human debate, ⑤ native reasoning** come from different collection pipelines (different formatting, different tasks in ①/②'s case) — heavy normalization (character set, LaTeX, speaker labels, quote/whitespace standardization) is earning its keep here and is necessary before these can be compared to anything else.
- **③ AI debate vs ④ AI monologue** are already matched on model family, task, and temperature; the only deliberate difference is the system-prompt framing (solo vs 4-participant). Heavy cross-pipeline normalization is not what makes this pair comparable — it already is. Over-cleaning within this trio risks washing out real signal, not removing confounds. Only apply normalization steps here that address an actual artifact (e.g. the Chinese contamination bug in ③, see below) — not blanket rules inherited from the ①/②/⑤ cleaning pass.

### 4. Root-cause fixes take priority over blanket filtering
The Chinese-character contamination in `ai_debate.jsonl` (46/600 rows) is a **generation bug** (model drifting into Chinese mid-debate), not a formatting-pipeline artifact. The correct fix is **regenerating those 46 debates** (see Phase 4 below), not blanket character-set filtering across the whole corpus. Blanket filtering should be treated as a stopgap for the *unregenerated* file, and revisited once regeneration completes — it should not become the permanent mechanism for handling this specific issue.

### 5. Mandatory leakage validation before Step 1 method validation
Before trusting any classification method's output on the known cells (①②③④), run a trivial surface-feature probe (doc length excluded/reported separately per point 2; LaTeX-token rate, non-ASCII rate, character-set-violation rate, avg sentence length) to predict condition label. If the probe still separates conditions near-perfectly on non-length features after cleaning, the corpus still leaks condition identity through a residual artifact, and the specific offending feature should be identified and addressed before proceeding. See Phase 5 in the Final Canonicalization Plan.

---

## Dataset Schema Definitions

### AI Debate Schema

**Files:** `ai_debate/raw_qwen_generation/regenerated_ai_debate.jsonl` → `ai_debate/processed_ai_debate.jsonl`

#### Core Fields
- `debate_id` - Unique debate identifier (string)
- `source_item_id` - Original puzzle identifier (string)
- `puzzle_id` - Standardized puzzle ID (g24_XXXX format) (string)
- `puzzle` - Nested object with target (integer) and numbers (array of integers)
- `numbers` - Flat copy of puzzle numbers (array of integers)
- `model` - Model name (string)
- `model_version` - Model version identifier (string)
- `temperature` - Sampling temperature (number or null)
- `max_tokens` - Maximum tokens per turn (integer or null)
- `turn_order_seed` - Random seed for turn ordering (integer)
- `turns` - Array of turn objects with turn_index, speaker, text_raw, text_clean, flagged
- `n_turns` - Number of turns in debate (integer)
- `ended_by` - How debate ended ("natural" or "cap")
- `started_at`, `finished_at` - Timestamps (ISO format)
- `cost_usd` - API cost in USD (number)
- `full_text_no_labels` - Complete transcript without speaker labels (string)
- `labeled_turns` - Transcript with speaker labels (array of objects)
- `pass` - Pass number (1-3) (integer)
- `seed` - Random seed (integer)

**Required fields:** debate_id, puzzle_id, numbers, model_version, turns, n_turns

#### Processed-Only Fields
- `processing_info` - Object with original_length, processed_length, characters_removed, latex_conversions, speaker_labels_removed, system_extracted, removed_char_types, processing_timestamp
- `system_info` - Extracted SYSTEM line if present (string)

---

### AI Monologue Schema

**Files:** `ai-monolouge/prompted_ai_monologue.jsonl` → `ai_monologue/processed_prompted_ai_monologue.jsonl`

#### Core Fields
- `puzzle_id` - Standardized puzzle ID (g24_XXXX format) (string)
- `numbers` - Available numbers (array of integers)
- `transcript` - AI-generated monologue transcript (string)
- `rt_s` - Response time in seconds (float)
- `cost_usd` - API cost in USD (number)
- `model_version` - Model version identifier (string)
- `timestamp` - ISO timestamp (string)
- `debate_id` - Associated debate ID (string)
- `pass` - Pass number (1-3) (integer)
- `seed` - Random seed (integer)

**Required fields:** puzzle_id, numbers, transcript, model_version

#### Processed-Only Fields
- `processing_info` - Same structure as AI debate

---

### AI Monologue Reasoning Schema

**Files:** `ai_reasoning/raw_deepseek_generation/native_reasoning_traces.jsonl` → `ai_reasoning/processed_native_reasoning_traces.jsonl`

#### Core Fields
- `puzzle_id` - Standardized puzzle ID (g24_XXXX format) (string)
- `numbers` - Available numbers (array of integers)
- `think_trace` - AI reasoning trace (string)
- `answer_text` - Formatted answer (string)
- `rt_s` - Response time in seconds (float)
- `cost_usd` - API cost in USD (number)
- `model_version` - Model version identifier (string)
- `timestamp` - ISO timestamp (string)
- `debug` - Debug metadata (object)
- `pass` - Pass number (1-3) (integer)
- `seed` - Random seed (integer)

**Required fields:** puzzle_id, numbers, think_trace, model_version

#### Processed-Only Fields
- `processing_info` - Same structure as AI debate

---

### Human Debate Schema

**Files:** `human_debate/json_formatted/human_debate_with_speaker_labels.jsonl` → `human_debate/processed_human_debate.jsonl`

#### Core Fields
- `puzzle_id` - Unique puzzle identifier (UUID format) (string)
- `numbers` - Available numbers (array of integers)
- `transcript` - Debate transcript (string)
- `response` - Final answer/expression (string)
- `response_normalized` - Normalized answer (string)
- `valid` - Whether response is syntactically valid (boolean)
- `correct` - Whether answer is correct (boolean)
- `rt_s` - Response time in seconds (float)
- `model_version` - Dataset identifier (string)
- `pass` - Pass number (artificial field) (integer)
- `seed` - Random seed (artificial field) (integer)
- `cost_usd` - API cost (artificial field) (number)
- `timestamp` - ISO timestamp (string)
- `debate_id` - Unique debate identifier (string)

**Required fields:** puzzle_id, numbers, transcript, model_version

#### Processed-Only Fields
- `processing_info` - Same structure as AI debate
- `system_info` - Extracted SYSTEM line (string)

---

### Human Monologue / Think-Aloud Schema

**Files:** `human_monologue/all_samples/human_think_aloud.jsonl` → `human_monologue/processed_sample_600_human_think_aloud.jsonl`

#### Core Fields
- `puzzle_id` - Standardized puzzle ID (g24_XXXX format) (string)
- `numbers` - Available numbers (array of integers)
- `think_trace` - Human reasoning trace (string)
- `response` - Final answer/expression (string)
- `response_normalized` - Normalized answer (string)
- `valid` - Whether response is syntactically valid (boolean)
- `correct` - Whether answer is correct (boolean)
- `rt_s` - Response time in seconds (float)
- `model_version` - Dataset identifier (string)

**Required fields:** puzzle_id, numbers, think_trace, model_version

#### Processed-Only Fields
- `processing_info` - Same structure as AI debate

---

### Human Reasoning Traces (Small) Schema (Archived / Not Currently Processed)

**Files:** `human_reasoning_traces_small.jsonl` / `human_reasoning_traces_small_processed.jsonl`

Same schema as human_reasoning_traces.jsonl. Note: The current `processed_sample_600_human_think_aloud.jsonl` is a sample of 600 rows drawn from the full 5,143-row human think-aloud dataset, not the small reasoning-traces sample.

---

## Text Standardization Rules

**Goal:** Create uniform character set and formatting across all datasets while preserving essential mathematical content.

### Common Character Set

#### Allowed Characters
- **Letters:** a-z, A-Z
- **Numbers:** 0-9
- **Basic punctuation:** . , ! ? ; : ' " ( ) [ ] -
- **Mathematical symbols:** + - * / = < > × ÷ ^ _
- **Whitespace:** space, newline
- **Special:** & (preserved as it appears in multiple datasets)
- **Note:** Curly braces `{ }` are removed during LaTeX standardization (they are not part of actual Game of 24 math notation and only appear as LaTeX formatting artifacts).

#### Replaced Characters
- Curly quotes (' ' " ") and backtick (`) → re-mapped to `'`/`"` (semantically equivalent characters, no scar risk)
- LaTeX commands:
  - `\frac{a}{b}` → `(a/b)`
  - `\times` → `×`
  - `\sqrt{x}` → `sqrt(x)`
  - `\[`, `\]`, `\(`, `\)` → removed
  - `^{n}` → `^n`, `_{n}` → `_n`
  - `boxed`, `left(`, `right)` → removed / replaced with `(` and `)`
  - `{ }` → removed

#### Deleted Characters (⚠ see "Preprocessing Policy Decisions" §1)
> Per the 2026-07-10 policy, these *should* be replaced with a single space. The current implementation deletes them. This was accepted for the 2026-07-14 processing run because the symbols are not part of the English/math vocabulary and are judged unlikely to leave meaningful scars, but it may be revisited if leakage probes detect condition-predictive artifacts.
- Chinese characters (上千个字符)
- Japanese characters (あいうえかがけしずせそっつてとなにねのはばまみめもょらるれわをん)
- Korean characters (솞치)
- Turkish characters (ä, ş)
- Special unicode (², ·, é, ʃ, –, —, ', ₁, ₂, ₃, ⅓, →, √, ≈, ≠, −, ')
- Emojis (😁)
- Special punctuation (¿, …, —, –, 、。)
- Other special symbols (@, #, `, ^, ~, $, etc.)

---

### LaTeX Standardization

#### Strategy: Simplify to Plain Text
Keep mathematical meaning but convert LaTeX to standardized plain text.

#### Conversion Rules
- `\frac{a}{b}` → `(a/b)`
- `\times` → `×` (already in character set)
- `\sqrt{x}` → `sqrt(x)`
- `\[` and `\]` → remove (display math delimiters)
- `\(` and `\)` → remove (inline math delimiters)
- `^{n}` → `^n` (keep exponent notation)
- `_{n}` → `_n` (keep subscript notation)
- `boxed{...}` → remove `boxed` and all `{ }` (LaTeX boxing artifacts)
- `left(` → `(` (LaTeX parenthesis sizing command)
- `right)` → `)` (LaTeX parenthesis sizing command)
- `{` and `}` → removed (curly braces are not part of Game of 24 math notation and are only used as LaTeX delimiters)
- Remove: Pure formatting LaTeX (e.g., `\textbf`, `\emph`)

#### Mathematical Symbol Preservation
- Keep: × ÷ + - * / = < > ( ) [ ] ^ _
- These are essential for mathematical reasoning content
- Curly braces `{ }` are NOT preserved; they are removed as LaTeX artifacts

---

### Text Normalization

#### Quote Standardization
- ' ' ' ' → '
- " " " " → "
- ` ` → ' (backtick to single quote)

#### Whitespace
- Collapse multiple spaces to single space
- Remove leading/trailing whitespace from each line
- Normalize newlines: ensure single newline between paragraphs

#### Speaker Label Removal
- Remove patterns: `SpeakerName: ` at start of lines
- Remove animal names from human debate: `Cat: `, `Dog: `, etc.
- Remove generic labels: `Speaker A: `, `Speaker 1: `, etc.
- Remove self-references: `I agree with SpeakerName`

#### SYSTEM Line Extraction
- Extract `SYSTEM: ...` content to `system_info` field
- Remove from transcript text
- Format: `system_info` contains the raw SYSTEM line content

#### Special Character Removal
- Delete (current implementation) or replace-with-space (planned policy) emojis: 😁, 🎉, etc.
- Delete special punctuation: ¿, …, —, –, etc.
- Delete decorative symbols: ◆, ●, etc.

---

### Field-Specific Transformations

#### Transcript Fields (ai_debate, human_debate)
1. Extract SYSTEM line to `system_info` field
2. Remove speaker labels
3. Apply LaTeX standardization
4. Apply character set filtering
5. Apply text normalization

#### Think Trace / Monologue Fields (ai_monologue, human_monologue)
1. Apply LaTeX standardization
2. Apply character set filtering
3. Apply text normalization
4. Remove leading/trailing whitespace

#### Metadata Fields
- Keep all metadata fields unchanged (puzzle_id, numbers, rt_s, etc.)
- Only transform text content fields

---

### Processing Order

1. **Extract metadata** (SYSTEM line, speaker info)
2. **Remove structural elements** (speaker labels, SYSTEM line from text)
3. **LaTeX standardization** (convert to plain text math; remove `boxed`, `left(`, `right)`, `{`, `}`)
4. **Character set filtering** (remove non-allowed characters)
5. **Text normalization** (quotes, whitespace, special chars)
6. **Quality check** (ensure no empty transcripts, reasonable length)

---

### Output Format

#### New Files
- Create `*_processed.jsonl` files alongside originals
- Preserve original files unchanged
- Add `processing_info` field to each row documenting transformations

#### Processing Info Field
```json
{
  "processing_info": {
    "original_length": 1234,
    "processed_length": 1200,
    "characters_removed": 34,
    "latex_conversions": 5,
    "normalization_changes": 12,
    "speaker_labels_removed": 10,
    "system_extracted": true,
    "removed_char_types": ["\\", "\\u2019", "\\u2248"],
    "processing_timestamp": "2026-07-10T15:30:00Z"
  }
}
```

---

## Transformations Applied (Chronological)

### 2026-07-08 15:35 UTC - Puzzle ID Standardization
**Files:** `ai_debate.jsonl`, `human_reasoning_traces.jsonl`

**Transformation:**
- Converted human reasoning traces from participant-based IDs to standardized `g24_XXXX` format
- Added `puzzle_id` field to AI debates (extracted from source_item_id using selection_rank mapping)
- Used `puzzle_selection.csv` to map number combinations to standardized puzzle IDs

**Status:** ✅ Complete

---

### 2026-07-08 15:45 UTC - Removed Artificial Fields from Human Data
**Files:** `human_reasoning_traces.jsonl`, `human_debate_delidata.jsonl`

**Fields Removed:**
- `pass` (artificial - humans don't have "passes")
- `seed` (artificial - humans aren't deterministic)
- `answer_text` (artificial - I created this)
- `cost_usd` (artificial - humans don't have API costs)
- `timestamp` (artificial - no timestamp available)
- `debug` (artificial - I created this)

**Rationale:** Keep data authentic to what was actually collected

**Status:** ✅ Complete

---

### 2026-07-08 15:50 UTC - Removed Correctness Fields from AI Datasets
**Files:** `ai_mololouge.jsonl`, `ai_monolouge_reasoning.jsonl`

**Fields Removed:**
- `valid` (extraction reliability issues)
- `correct` (extraction reliability issues)
- `response` (extraction reliability issues)
- `response_normalized` (extraction reliability issues)

**Reason:** AI monologue extraction had 0% valid rate, reasoning traces had 69.8% valid with potential issues

**Status:** ✅ Complete

**Scripts moved to `scripts/correctness/`:**
- `cell4_build_ai_monologue.py`
- `cell5_build_reasoning_traces.py`

---

### 2026-07-08 15:35 UTC - Added Flat `numbers` Field to AI Debates
**File:** `ai_debate.jsonl`

**Transformation:**
- Added top-level `numbers` field (copied from nested `puzzle.numbers`)
- Kept nested `puzzle` object for backward compatibility

**Rationale:** Enables consistent filtering/joining across datasets

**Status:** ✅ Complete

---

### 2026-07-08 15:44 UTC - Created Small Human Dataset
**Files:** Created `human_reasoning_traces_small.jsonl`

**Transformation:**
- Randomly sampled 3 trials per puzzle from full human reasoning traces
- Used random seed 42 for reproducibility
- Result: 600 rows (200 puzzles × 3 trials)

**Rationale:** Test dataset for computationally expensive methods; keep full dataset for final analysis

**Status:** ✅ Complete

---

### 2026-07-08 15:50 UTC - Removed Puzzle g24_0193 from AI Datasets
**Files:** `ai_debate.jsonl`, `ai_mololouge.jsonl`, `ai_monolouge_reasoning.jsonl`

**Transformation:**
- Removed all entries for puzzle `g24_0193` ([1, 1, 2, 8])
- AI datasets: 603 → 600 rows (removed 3 entries per dataset)
- Human study didn't include this puzzle

**Rationale:** Ensures puzzle-level comparison is possible (200 puzzles overlap between AI and human)

**Status:** ✅ Complete

---

### 2026-07-10 10:59 UTC - Text Standardization Phase (Initial)
**Files:** All datasets - created *_processed.jsonl versions

**Transformations Applied:**

1. **Character Set Standardization**
   - Defined common 89-character set: a-z, A-Z, 0-9, basic punctuation, mathematical symbols (+ - * / = < > × ÷), whitespace
   - Removed: Chinese characters (1000+), Japanese characters, Korean characters, Turkish characters
   - Removed: Emojis, special unicode (², ·, é, ʃ, –, —, ', ₁, ₂, ₃, ⅓, →, √, ≈, ≠)
   - Removed: Special punctuation (¿, …, 、。), curly quotes, decorative symbols
   - **Result:** All datasets now use identical character set

2. **LaTeX Standardization**
   - `\frac{a}{b}` → `(a/b)` (35,360 conversions in AI datasets)
   - `\times` → `×` (standardized multiplication symbol)
   - `\sqrt{x}` → `sqrt(x)` (preserved mathematical meaning)
   - Removed display/inline math delimiters (\[, \], \(, \))
   - Preserved mathematical content while standardizing format

3. **Text Normalization**
   - Standardized quotes: ' ' " " → ' "
   - Removed emojis and special unicode
   - Collapsed multiple spaces to single space
   - Removed leading/trailing whitespace from lines
   - Normalized newlines (max 2 consecutive)

4. **SYSTEM Line Extraction**
   - Extracted `SYSTEM: ...` lines to `system_info` field
   - Removed from transcript field
   - Applied to human debate data (500/500 successful)

5. **Speaker Label Removal**
   - Removed patterns: "Speaker: ", "Speaker A: ", "Speaker 1: "
   - Removed animal names: "Cat: ", "Dog: ", etc. (33 animals)
   - Removed self-references: "I agree with SpeakerName"
   - 13,578 labels removed from human debate, 803 from AI debate
   - **Note:** 39 edge cases remain (unusual formatting patterns)

6. **Processing Metadata**
   - Added `processing_info` field to all processed rows
   - Tracks: original_length, processed_length, characters_removed, latex_conversions, speaker_labels_removed, system_extracted, processing_timestamp
   - Enables reproducibility and quality tracking

**Results:**
- ✅ Character set violations: 0 across all 8,043 rows
- ✅ All datasets now use identical 89-character set
- ✅ Processing info present in 100% of rows
- ✅ SYSTEM lines extracted from 100% of human debate transcripts
- ⚠️ Speaker labels: 99.7% removal rate (13,578/13,617)

**Processed Files Created:**
- `ai_debate_processed.jsonl` (600 rows)
- `ai_mololouge_processed.jsonl` (600 rows)
- `ai_monolouge_reasoning_processed.jsonl` (600 rows)
- `human_debate_delidata_processed.jsonl` (500 rows)
- `human_reasoning_traces_processed.jsonl` (5,143 rows)
- `human_reasoning_traces_small_processed.jsonl` (600 rows)

**Scripts Created:**
- `scripts/standardize_datasets.py` - Main standardization script
- `scripts/verify_processed_integrity.py` - Verification script

**Status:** ✅ Superseded by 2026-07-14 reprocessing

---

### 2026-07-14 UTC - Reprocessing and LaTeX Artifact Cleanup
**Files:** All `processed_*.jsonl` files in `data/00_core-2x2/`

**Rationale:**
- Original raw sources were already in JSON Lines format (`.jsonl`); no JSON conversion was necessary.
- The `standardize_datasets.py` script reads `.jsonl` source files and writes `processed_*.jsonl` output files.
- Discovered orphaned LaTeX artifacts (`boxed`, `left(`, `right)`, `{`, `}`) in the processed AI debate and AI monologue files.
- Updated the script to clean these artifacts as part of the LaTeX standardization step.
- Re-ran the full pipeline on all 5 canonical datasets.

**Transformations Applied:**

1. **File format / JSONL handling**
   - Source files are `.jsonl` (JSON Lines), one JSON object per line
   - Output files are `.jsonl` with identical structure plus `processing_info` field
   - No JSON-to-JSON conversion; the script reads and writes `.jsonl` directly

2. **Dataset Source-to-Output Mapping**
   - `ai_debate/raw_qwen_generation/regenerated_ai_debate.jsonl` → `ai_debate/processed_ai_debate.jsonl` (600 rows)
   - `ai-monolouge/prompted_ai_monologue.jsonl` → `ai_monologue/processed_prompted_ai_monologue.jsonl` (600 rows)
   - `ai_reasoning/raw_deepseek_generation/native_reasoning_traces.jsonl` → `ai_reasoning/processed_native_reasoning_traces.jsonl` (600 rows)
   - `human_debate/json_formatted/human_debate_with_speaker_labels.jsonl` → `human_debate/processed_human_debate.jsonl` (500 rows)
   - `human_monologue/all_samples/human_think_aloud.jsonl` → `human_monologue/processed_sample_600_human_think_aloud.jsonl` (5,143 rows)

3. **LaTeX Standardization (updated)**
   - `\frac{a}{b}` → `(a/b)` (32,889 conversions in AI debate, 10,105 in AI monologue, 922 in AI reasoning)
   - `\times` → `×`
   - `\sqrt{x}` → `sqrt(x)`
   - Removed `\[`, `\]`, `\(`, `\)` (display/inline math delimiters)
   - `^{n}` → `^n`, `_{n}` → `_n`
   - **NEW:** `boxed` command removed
   - **NEW:** `left(` → `(` (LaTeX sizing command)
   - **NEW:** `right)` → `)` (LaTeX sizing command)
   - **NEW:** `{` and `}` removed (curly braces are LaTeX formatting artifacts, not Game of 24 math)

4. **Speaker Label Removal (human_debate, ai_debate)**
   - Removed `SpeakerName: ` patterns at start of lines
   - Removed animal names (Cat, Dog, Bird, etc.) as speaker labels
   - Removed generic labels (Speaker A, Speaker 1, etc.)
   - Removed self-references: "I agree with SpeakerName"
   - 13,578 labels removed from human debate, 884 from AI debate

5. **SYSTEM Line Extraction (human_debate)**
   - Extracted `SYSTEM: ...` lines to `system_info` field
   - Removed from transcript text

6. **Character Set Filtering**
   - Removed all characters outside the `ALLOWED_CHARS` set
   - Includes: Chinese/Japanese/Korean/Turkish characters, emojis, special unicode, special punctuation
   - **Note:** This currently *deletes* characters rather than replacing with spaces (see Policy §1)

7. **Text Normalization**
   - Curly quotes and backtick → straight `'` / `"`
   - Collapse multiple spaces to single space
   - Remove leading/trailing whitespace from lines
   - Normalize newlines (max 2 consecutive)

8. **Processing Metadata**
   - Added `processing_info` to each row
   - New fields include `normalization_changes` and `removed_char_types`

**Results:**
- ✅ Total 7,443 rows processed
- ✅ Character set violations: 0 across all processed text
- ✅ `boxed`, `left(`, `right)`, `{`, `}` artifacts: 0 in processed AI debate
- ✅ No Chinese characters in regenerated AI debate source
- ✅ Processing info present in 100% of rows
- ⚠️ Deletion-based character filtering (replace-with-space policy still pending)

**Processed Files Created/Updated:**
- `ai_debate/processed_ai_debate.jsonl` (600 rows)
- `ai_monologue/processed_prompted_ai_monologue.jsonl` (600 rows)
- `ai_reasoning/processed_native_reasoning_traces.jsonl` (600 rows)
- `human_debate/processed_human_debate.jsonl` (500 rows)
- `human_monologue/processed_sample_600_human_think_aloud.jsonl` (5,143 rows)

**Scripts Updated:**
- `scripts/standardize_datasets.py` - Updated file paths and integrated LaTeX artifact cleanup

**Status:** ✅ Complete

---

### 2026-07-10 13:00 UTC - AI Debate Chinese Character Analysis
**File:** `ai_debate.jsonl`

**Analysis:**
- Discovered 46/600 debates (7.67%) contain Chinese characters
- Total Chinese characters: 101,119 out of 4,830,270 (2.09% of corpus)
- Primary contaminant: Chinese characters (99,125 instances)
- Distribution: 260 rows clean (43.3%), 306 rows minor contamination (<1%), 34 rows significant contamination (≥1%)

**Position Analysis:**
- Tested hypothesis that Chinese appears at end after conclusions
- 93.5% of corrupted debates have conclusion indicators before Chinese
- 45.7% have Chinese starting at 50%+ of text position (truncation viable)
- 54.3% have Chinese starting early (≤50% of text position, regeneration needed)

**Decision:** Regenerate all 46 corrupted debates (simpler than hybrid truncation/regeneration approach)

**Analysis Scripts:**
- `scripts/analyze_ai_debate_language.py` - Language contamination analysis
- `scripts/analyze_chinese_position.py` - Chinese position analysis
- `scripts/extract_chinese_debate_parameters.py` - Parameter extraction for regeneration

**Status:** ✅ Analysis Complete

---

### 2026-07-10 13:30 UTC - AI Debate Regeneration
**Files:** `ai_debate.jsonl` → `ai_debate_chinese_original.jsonl` (backup) → `ai_debate_regenerated.jsonl`

**Regeneration:**
- Backup original: `ai_debate_chinese_original.jsonl` (preserves Chinese data)
- Regenerated 47 debates using exact same script and parameters as original
- Used original script: `cell3_build_dataset_random_discussion.py` (with minimal `--ranks` parameter addition)
- Same seeds: Pass 1 (12345), Pass 2 (22345), Pass 3 (32345)
- Regenerated specific ranks for each pass:
  - Pass 1: ranks 15, 31, 46, 63, 71, 85, 90, 99, 115, 121, 129, 171, 182 (13 debates)
  - Pass 2: ranks 10, 69, 101, 104, 109, 141, 144, 150, 171, 173, 189, 195 (12 debates)
  - Pass 3: ranks 1, 9, 23, 29, 43, 74, 80, 81, 87, 96, 103, 121, 126, 130, 143, 148, 158, 167, 171, 179, 184, 191 (22 debates)
- Note: 47 debates were regenerated (analysis initially counted 46, but one additional rank was found)
- Ran 3 passes in parallel (3 × 5 rpm = 15 rpm, within 20 rpm limit)
- Post-processed regenerated entries to add `pass`, `seed`, `puzzle_id` fields and `_pY` suffix to `debate_id`
- Replaced corrupted entries in backup
- Final output: `ai_debate_regenerated.jsonl` (600 rows, 0 Chinese characters)

**Verification:**
- ✅ All 600 debates in `ai_debate_regenerated.jsonl` are English-only
- ✅ No Chinese characters detected
- ✅ Original `ai_debate.jsonl` and `ai_debate_chinese_original.jsonl` preserved for traceability

**Commands Used:**
```bash
# Pass 1 (parallel)
python cell3_build_dataset_random_discussion.py --seed 12345 --ranks "15,31,46,63,71,85,90,99,115,121,129,171,182" --out-dir ai-debate-regenerated

# Pass 2 (parallel)
python cell3_build_dataset_random_discussion.py --seed 22345 --ranks "10,69,101,104,109,141,144,150,171,173,189,195" --out-dir ai-debate-regenerated/pass2

# Pass 3 (parallel)
python cell3_build_dataset_random_discussion.py --seed 32345 --ranks "1,9,23,29,43,74,80,81,87,96,103,121,126,130,143,148,158,167,171,179,184,191" --out-dir ai-debate-regenerated/pass3
```

**Rationale:** Ensures data quality (English-only) while preserving exact experimental conditions

**Status:** ✅ Complete

---

## Current Dataset State

### Raw / Source Files

| File | Rows | Unique puzzles | Correctness fields | Notes |
|---|---|---|---|---|
| `ai_debate/raw_qwen_generation/original_ai_debate (with chinese).jsonl` | 600 | 200 | No | Original with Chinese contamination; kept for traceability |
| `ai_debate/raw_qwen_generation/regenerated_ai_debate.jsonl` | 600 | 200 | No | Clean version: 47 corrupted debates regenerated, English-only, verified |
| `ai-monolouge/prompted_ai_monologue.jsonl` | 600 | 200 | No | Removed correctness (extraction failed), removed g24_0193 |
| `ai_reasoning/raw_deepseek_generation/native_reasoning_traces.jsonl` | 600 | 200 | No | Removed correctness (extraction issues), removed g24_0193 |
| `human_debate/json_formatted/human_debate_with_speaker_labels.jsonl` | 500 | 500 | Yes | Original includes speaker labels; Wason card selection task |
| `human_monologue/all_samples/human_think_aloud.jsonl` | 5,143 | 200 | Yes | Full dataset, original correctness kept |

### Processed Files

| File | Rows | Text field | Notes |
|---|---|---|---|
| `ai_debate/processed_ai_debate.jsonl` | 600 | `full_text_no_labels` | Speaker labels removed, LaTeX cleaned, character-set filtered |
| `ai_monologue/processed_prompted_ai_monologue.jsonl` | 600 | `transcript` | LaTeX cleaned, character-set filtered |
| `ai_reasoning/processed_native_reasoning_traces.jsonl` | 600 | `think_trace` | LaTeX cleaned, character-set filtered |
| `human_debate/processed_human_debate.jsonl` | 500 | `transcript` | Speaker labels removed, SYSTEM line extracted, character-set filtered |
| `human_monologue/processed_sample_600_human_think_aloud.jsonl` | 5,143 | `think_trace` | Character-set filtered, normalized |

---

## Final Canonicalization Plan

### Phase 1: Critical Fixes (COMPLETED)
- [x] Puzzle ID standardization
- [x] Remove artificial fields from human data
- [x] Remove unreliable correctness from AI data
- [x] Add flat numbers field to AI debates
- [x] Remove g24_0193 for puzzle overlap
- [x] Create small human test dataset

### Phase 2: Data Quality (COMPLETED 2026-07-14)
- [x] Text standardization (whitespace, special characters, LaTeX)
- [x] Character set standardization across all datasets
- [x] Transcript/think trace normalization (trailing whitespace, formatting)
- [x] System line extraction (human debate)
- [x] Speaker label removal (processed versions)
- [x] Created `processed_*.jsonl` files in `data/00_core-2x2/`
- [x] Added processing_info metadata to all processed rows
- [x] Integrated LaTeX artifact cleanup (`boxed`, `left(`, `right)`, `{`, `}`)
- [x] Re-ran standardization on 5 canonical datasets after artifact cleanup

### Phase 3: Schema Alignment (INTENTIONAL ASYMETRIES)
- [x] Keep AI-specific fields (pass, seed, cost_usd, timestamp)
- [x] Keep reasoning-specific fields (answer_text, debug)
- [x] Keep human correctness fields (source-validated)

### Phase 4: Data Quality Remediation (COMPLETED 2026-07-10)
- [x] Analyze AI debate dataset for language contamination
- [x] Identify 47/600 debates (7.83%) with Chinese characters
- [x] Analyze Chinese position to determine truncation vs regeneration
- [x] Create backup: ai_debate_chinese_original.jsonl
- [x] Extract exact parameters for regeneration (seeds, ranks)
- [x] Regenerate 47 corrupted debates using original script
- [x] Replace corrupted entries with regenerated ones
- [x] Create final clean version: ai_debate_regenerated.jsonl
- [x] Verify regenerated debates are English-only

### Phase 5: Policy Update & Leakage Validation (PARTIALLY COMPLETED — 2026-07-14)
- [x] Re-run standardization on all 5 canonical datasets after regeneration (Phase 4) and LaTeX cleanup, superseding earlier `*_processed.jsonl` files
- [x] Spot-check regenerated + re-cleaned `processed_ai_debate.jsonl` for residual `boxed`, `left(`, `right)`, `{`, `}` artifacts
- [ ] Update `filter_character_set` (and emoji/special-punct removal) in `standardize_datasets.py` to replace-with-space instead of delete (deferred; deletion accepted for current run)
- [ ] Build surface-feature leakage probe (LaTeX-token rate, non-ASCII rate, character-set-violation rate, avg sentence length — excluding length/turn-count, which are expected condition differences) and confirm condition label is not trivially recoverable on ①②③④
- [ ] Document probe results here before proceeding to Step 1 method validation in `research_plan.md`

---

## File Locations

**Original Sources (raw, in `data/00_core-2x2/`):**
- AI debate: `ai_debate/raw_qwen_generation/original_ai_debate (with chinese).jsonl`
- AI debate (clean): `ai_debate/raw_qwen_generation/regenerated_ai_debate.jsonl`
- AI monologue: `ai-monolouge/prompted_ai_monologue.jsonl`
- AI reasoning: `ai_reasoning/raw_deepseek_generation/native_reasoning_traces.jsonl`
- Human debate: `human_debate/json_formatted/human_debate_with_speaker_labels.jsonl`
- Human monologue: `human_monologue/all_samples/human_think_aloud.jsonl`

**Processed Working Files (in `data/00_core-2x2/`):**
- `ai_debate/processed_ai_debate.jsonl`
- `ai_monologue/processed_prompted_ai_monologue.jsonl`
- `ai_reasoning/processed_native_reasoning_traces.jsonl`
- `human_debate/processed_human_debate.jsonl`
- `human_monologue/processed_sample_600_human_think_aloud.jsonl`

**Scripts:**
- `scripts/correctness/` - Archived correctness extraction scripts
- `scripts/plotting_scripts/` - Analysis scripts (turn distribution, difficulty)
- `scripts/standardize_datasets.py` - Main standardization script
- `scripts/verify_processed_integrity.py` - Verification script
- `scripts/analyze_ai_debate_language.py` - Language contamination analysis
- `scripts/analyze_chinese_position.py` - Chinese position analysis
- `scripts/extract_chinese_debate_parameters.py` - Parameter extraction for regeneration

**Documentation:**
- `data/PREPROCESSING.md` - This consolidated documentation file
- `data/00_core-2x2/DATA_SAMPLES.md` - Samples of current canonicalized datasets
- `data/00_core-2x2/character_frequency_analysis.txt` - Character frequency analysis results