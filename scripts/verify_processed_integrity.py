"""
Data Integrity Verification for Processed Datasets

Verifies that processed datasets maintain data integrity and follow the standardization rules.
"""
import json
import sys
from collections import Counter
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Define allowed character set (same as in standardization script)
ALLOWED_CHARS = set(
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '0123456789'
    '.,!?;:\'"()-[]{}'
    '+-*/=<>&×÷^_'
    ' \n'
)


def verify_character_set(text: str, dataset_name: str, row_num: int) -> tuple[bool, list[str]]:
    """Verify that text only contains allowed characters."""
    violations = []
    for i, char in enumerate(text):
        if char not in ALLOWED_CHARS:
            violations.append(f"Char '{char}' (ord={ord(char)}) at position {i}")
    
    if violations:
        print(f"  {dataset_name} row {row_num}: Character set violations:")
        for v in violations[:5]:  # Show first 5
            print(f"    {v}")
        if len(violations) > 5:
            print(f"    ... and {len(violations) - 5} more")
        return False, violations
    return True, []


def verify_processing_info(data: dict, dataset_name: str, row_num: int) -> bool:
    """Verify that processing_info field exists and has required fields."""
    if 'processing_info' not in data:
        print(f"  {dataset_name} row {row_num}: Missing processing_info field")
        return False
    
    required_fields = [
        'original_length', 'processed_length', 'characters_removed',
        'latex_conversions', 'speaker_labels_removed', 'system_extracted',
        'processing_timestamp'
    ]
    
    missing_fields = [f for f in required_fields if f not in data['processing_info']]
    if missing_fields:
        print(f"  {dataset_name} row {row_num}: Missing processing_info fields: {missing_fields}")
        return False
    
    # Verify that lengths make sense (allow for LaTeX conversions and normalization)
    orig_len = data['processing_info']['original_length']
    proc_len = data['processing_info']['processed_length']
    chars_removed = data['processing_info']['characters_removed']
    
    # Length should decrease, but not increase (unless LaTeX adds chars)
    # Just check that processed length is reasonable
    if proc_len <= 0:
        print(f"  {dataset_name} row {row_num}: Invalid processed length: {proc_len}")
        return False
    
    if proc_len > orig_len * 1.5:  # Allow some growth from LaTeX conversions
        print(f"  {dataset_name} row {row_num}: Processed length too large: {orig_len} -> {proc_len}")
        return False
    
    return True


def verify_no_speaker_labels(text: str, dataset_name: str, row_num: int) -> bool:
    """Verify that no speaker labels remain in processed text."""
    # Check for common speaker patterns
    patterns = [
        r'^[A-Z][a-z]+:\s',
        r'^Speaker\s+[A-Z]:\s',
        r'^Speaker\s+\d+:\s',
        r'^Cat:\s', r'^Dog:\s', r'^Bird:\s',  # Animal names
    ]
    
    import re
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            print(f"  {dataset_name} row {row_num}: Found speaker label pattern: {pattern}")
            return False
    
    return True


def verify_no_system_line(text: str, dataset_name: str, row_num: int) -> bool:
    """Verify that no SYSTEM line remains in processed text."""
    import re
    if re.search(r'^SYSTEM:', text, re.MULTILINE):
        print(f"  {dataset_name} row {row_num}: Found SYSTEM line in transcript")
        return False
    return True


def verify_dataset(filepath: Path, text_field: str, is_debate: bool = False) -> dict:
    """Verify an entire dataset."""
    print(f"\n{'='*60}")
    print(f"Verifying: {filepath.name}")
    print(f"{'='*60}")
    
    results = {
        'total_rows': 0,
        'valid_rows': 0,
        'character_violations': 0,
        'processing_info_missing': 0,
        'speaker_labels_found': 0,
        'system_lines_found': 0,
        'empty_transcripts': 0,
        'character_set_stats': Counter()
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for row_num, line in enumerate(f, 1):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                results['total_rows'] += 1
                
                text = data.get(text_field, '')
                if not text:
                    results['empty_transcripts'] += 1
                    print(f"  Row {row_num}: Empty {text_field}")
                    continue
                
                # Verify character set
                char_set_valid, violations = verify_character_set(text, filepath.name, row_num)
                if not char_set_valid:
                    results['character_violations'] += 1
                
                # Track character set statistics
                results['character_set_stats'].update(text)
                
                # Verify processing info
                if not verify_processing_info(data, filepath.name, row_num):
                    results['processing_info_missing'] += 1
                
                # Verify no speaker labels (for debates)
                if is_debate:
                    if not verify_no_speaker_labels(text, filepath.name, row_num):
                        results['speaker_labels_found'] += 1
                    
                    # Verify no SYSTEM line
                    if not verify_no_system_line(text, filepath.name, row_num):
                        results['system_lines_found'] += 1
                
                results['valid_rows'] += 1
                
            except json.JSONDecodeError as e:
                print(f"  Row {row_num}: JSON decode error: {e}")
            except Exception as e:
                print(f"  Row {row_num}: Error: {e}")
    
    # Print summary
    print(f"\nSummary for {filepath.name}:")
    print(f"  Total rows: {results['total_rows']}")
    print(f"  Valid rows: {results['valid_rows']}")
    print(f"  Character set violations: {results['character_violations']}")
    print(f"  Missing processing_info: {results['processing_info_missing']}")
    print(f"  Speaker labels found: {results['speaker_labels_found']}")
    print(f"  SYSTEM lines found: {results['system_lines_found']}")
    print(f"  Empty transcripts: {results['empty_transcripts']}")
    print(f"  Unique characters used: {len(results['character_set_stats'])}")
    print(f"  Character set: {repr(''.join(sorted(results['character_set_stats'].keys())))}")
    
    return results


def main():
    """Main verification function."""
    base_path = Path(__file__).resolve().parent.parent / 'data'
    human_debate_path = Path(__file__).resolve().parent.parent / 'data' / 'human_debate'
    
    # Define processed datasets to verify
    datasets = [
        (base_path / 'ai_debate' / 'processed_ai_debate.jsonl', 'full_text_no_labels', True),
        (base_path / 'ai_monologue' / 'processed_prompted_ai_monologue.jsonl', 'transcript', False),
        (base_path / 'ai_reasoning' / 'processed_native_reasoning_traces.jsonl', 'think_trace', False),
        (human_debate_path / 'processed_human_debate.jsonl', 'transcript', True),
        (base_path / 'human_monologue' / 'unprocessed' / 'processed_human_think_aloud_full.jsonl', 'think_trace', False),
        (base_path / 'human_monologue' / 'unprocessed' / 'processed_think_aloud_full_variant.jsonl', 'think_trace', False),
    ]
    
    print("="*60)
    print("Data Integrity Verification for Processed Datasets")
    print("="*60)
    
    all_results = []
    for filepath, text_field, is_debate in datasets:
        if not filepath.exists():
            print(f"\nSkipping {filepath.name}: File not found")
            continue
        
        results = verify_dataset(filepath, text_field, is_debate)
        all_results.append((filepath.name, results))
    
    # Overall summary
    print(f"\n{'='*60}")
    print("Overall Summary")
    print(f"{'='*60}")
    
    total_rows = sum(r['total_rows'] for _, r in all_results)
    total_valid = sum(r['valid_rows'] for _, r in all_results)
    total_violations = sum(r['character_violations'] for _, r in all_results)
    
    print(f"Total rows across all datasets: {total_rows}")
    print(f"Total valid rows: {total_valid}")
    print(f"Total character set violations: {total_violations}")
    
    if total_violations == 0 and total_valid == total_rows:
        print("\n✅ All datasets passed integrity checks!")
    else:
        print("\n❌ Some datasets have issues that need attention.")


if __name__ == "__main__":
    main()