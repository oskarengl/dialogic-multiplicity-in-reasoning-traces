# Correctness Scripts

These scripts were used to attempt automatic correctness extraction from AI data. They are archived here for future reference or improvement attempts.

## Problems

### 1. AI Debate Correctness

AI debates often don't produce valid Game of 24 solutions:
- 65.8% of debates have no extractable valid answer
- Many debates use fabricated numbers or wrong number multisets
- The strict `grade_expression()` validator (AST-parsed, exact number multiset, exact Fraction equality to 24) correctly rejects these

### 2. AI Monologue Correctness

AI monologues had extraction failures:
- `ai_mololouge.jsonl`: 0% valid (extraction completely failed)
  - The `extract_final_expression()` function extracted intermediate calculation steps instead of final answers
  - Example: extracted "45 - 21" from a transcript step "5 × 9 = 45 - 21 = 24" instead of the actual solution
- `ai_monolouge_reasoning.jsonl`: 69.8% valid (better due to structured prompting)
  - Still has ~30% failure rate
  - Some valid expressions may be incorrectly rejected

## Scripts

### Debate Scripts
- `analyze_debates.py` - Analyze turn counts and correctness patterns
- `difficulty_correctness.py` - Relate correctness to puzzle difficulty
- `fix_correctness.py` - Attempt to fix correctness scoring using boxed expressions
- `improved_correctness.py` - Improved correctness extraction
- `verify_correctness.py` - Verify correctness scoring
- `analyze_last_turns.py` - Analyze last turns
- `last_turns_sample.txt` - Sample data
- `manual_check.py` - Manual checking script

### Monologue/Reasoning Scripts
- `cell4_build_ai_monologue.py` - Generates AI monologue data (extraction logic flawed)
- `cell5_build_reasoning_traces.py` - Generates AI reasoning traces (partial extraction issues)

## Current Status

Correctness fields have been **removed** from the main datasets:
- `ai_debate.jsonl` - No correctness fields (never added)
- `ai_mololouge.jsonl` - Removed `valid`, `correct`, `response`, `response_normalized`
- `ai_monolouge_reasoning.jsonl` - Removed `valid`, `correct`, `response`, `response_normalized`
- `human_debate_delidata.jsonl` - Still has correctness (from original source)
- `human_reasoning_traces.jsonl` - Still has correctness (from original source)

The AI datasets are kept for qualitative analysis only (transcripts, think traces, etc.).

## Future Work

To improve correctness extraction, you would need to:
1. **Debates**: Design a more robust answer extraction that handles the messy nature of multi-speaker text
2. **Monologues**: Fix the `extract_final_expression()` logic to avoid extracting intermediate steps
3. Decide whether to accept "loose" answers (ignoring number multiset) for debates
4. Or accept that debates/monologues simply have lower correctness rates than expected
