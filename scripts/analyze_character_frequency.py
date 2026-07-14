"""
Character Frequency Analysis for Vocabulary Selection

Analyzes character distribution across all main datasets to inform
scientifically-grounded vocabulary selection using SentencePiece-style
character_coverage thresholds.
"""
import json
import sys
from collections import Counter
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Define datasets with their text fields
datasets = {
    '../archive/ai_debate/original_ai_debate.jsonl': 'full_text_no_labels',
    '../archive/ai_monologue/prompted_ai_monologue.jsonl': 'transcript',
    '../archive/ai_reasoning/native_reasoning_traces.jsonl': 'think_trace',
    '../archive/human_debate/human_debate_with_speaker_labels.jsonl': 'transcript',
    '../archive/human_monologue/human_think_aloud.jsonl': 'think_trace'
}

base_path = Path(r'C:\bachelor research\.1 recent approach\data\00_core-2x2')


def analyze_dataset(filepath: Path, text_field: str) -> dict:
    """Analyze character frequency for a single dataset."""
    if not filepath.exists():
        return None
    
    char_counter = Counter()
    total_chars = 0
    row_count = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                text = data.get(text_field, '')
                char_counter.update(text)
                total_chars += len(text)
                row_count += 1
            except json.JSONDecodeError:
                continue
    
    return {
        'char_counter': char_counter,
        'total_chars': total_chars,
        'row_count': row_count,
        'unique_chars': len(char_counter)
    }


def calculate_coverage_impact(char_counter: Counter, total_chars: int, coverage: float) -> dict:
    """
    Calculate what a given character_coverage threshold would mean.
    
    coverage: 0.9995 means 99.95% of characters should be covered
    (1 - coverage) * total_chars will be treated as UNK
    """
    # Sort characters by frequency (descending)
    sorted_chars = char_counter.most_common()
    
    # Calculate cumulative coverage
    cumulative_chars = 0
    coverage_chars = []
    removed_chars = []
    
    for char, count in sorted_chars:
        cumulative_chars += count
        current_coverage = cumulative_chars / total_chars
        
        if current_coverage <= coverage:
            coverage_chars.append((char, count))
        else:
            removed_chars.append((char, count))
    
    total_kept = sum(count for _, count in coverage_chars)
    total_removed = sum(count for _, count in removed_chars)
    
    return {
        'coverage_threshold': coverage,
        'chars_kept': len(coverage_chars),
        'chars_removed': len(removed_chars),
        'instances_kept': total_kept,
        'instances_removed': total_removed,
        'actual_coverage': total_kept / total_chars if total_chars > 0 else 0,
        'kept_chars': [char for char, _ in coverage_chars],
        'removed_chars': [(char, count) for char, count in removed_chars[:20]]  # First 20 for display
    }


def main():
    """Main analysis function."""
    print("=" * 80)
    print("Character Frequency Analysis for Vocabulary Selection")
    print("=" * 80)
    
    # Analyze each dataset
    dataset_results = {}
    combined_counter = Counter()
    combined_total = 0
    
    for filename, text_field in datasets.items():
        filepath = base_path / filename
        print(f"\nAnalyzing: {filename}")
        
        result = analyze_dataset(filepath, text_field)
        if result is None:
            print(f"  ERROR: File not found")
            continue
        
        dataset_results[filename] = result
        combined_counter.update(result['char_counter'])
        combined_total += result['total_chars']
        
        print(f"  Rows: {result['row_count']:,}")
        print(f"  Total characters: {result['total_chars']:,}")
        print(f"  Unique characters: {result['unique_chars']}")
    
    # Combined analysis
    print("\n" + "=" * 80)
    print("COMBINED ANALYSIS (All Datasets)")
    print("=" * 80)
    print(f"Total characters across all datasets: {combined_total:,}")
    print(f"Total unique characters: {len(combined_counter)}")
    
    # Show character distribution
    print("\nTop 50 most frequent characters:")
    for i, (char, count) in enumerate(combined_counter.most_common(50), 1):
        percentage = (count / combined_total) * 100
        print(f"  {i:2d}. '{char}' (ord={ord(char):3d}): {count:>10,} ({percentage:>5.2f}%)")
    
    # Show rare characters
    print("\nBottom 50 least frequent characters:")
    rare_chars = combined_counter.most_common()[:-51:-1]  # Last 50, reversed
    for i, (char, count) in enumerate(rare_chars, 1):
        percentage = (count / combined_total) * 100
        print(f"  {i:2d}. '{char}' (ord={ord(char):3d}): {count:>10,} ({percentage:>5.4f}%)")
    
    # Calculate impact of different coverage thresholds
    print("\n" + "=" * 80)
    print("COVERAGE THRESHOLD ANALYSIS")
    print("=" * 80)
    
    coverage_thresholds = [0.9990, 0.9995, 0.9998, 0.9999, 0.99995, 1.0]
    
    for coverage in coverage_thresholds:
        impact = calculate_coverage_impact(combined_counter, combined_total, coverage)
        
        print(f"\nCharacter Coverage: {coverage:.5f} ({coverage*100:.4f}%)")
        print(f"  Characters kept: {impact['chars_kept']}")
        print(f"  Characters removed: {impact['chars_removed']}")
        print(f"  Instances kept: {impact['instances_kept']:,} ({impact['actual_coverage']*100:.4f}%)")
        print(f"  Instances removed: {impact['instances_removed']:,} ({(1-impact['actual_coverage'])*100:.4f}%)")
        
        if impact['removed_chars']:
            print(f"  Sample removed characters (first 20):")
            for char, count in impact['removed_chars']:
                print(f"    '{char}' (ord={ord(char):3d}): {count} occurrences")
    
    # Character categories
    print("\n" + "=" * 80)
    print("CHARACTER CATEGORY ANALYSIS")
    print("=" * 80)
    
    categories = {
        'ASCII lowercase': set('abcdefghijklmnopqrstuvwxyz'),
        'ASCII uppercase': set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        'Digits': set('0123456789'),
        'Basic punctuation': set('.,!?;:\'"()[]{}'),
        'Math symbols': set('+-*/=<>&×÷^_'),
        'Whitespace': set(' \n\t'),
        'Other ASCII': set(chr(i) for i in range(32, 127)) - set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?;:\'"()[]{}+-*/=<>&×÷^_ \n\t'),
    }
    
    for category_name, char_set in categories.items():
        category_count = sum(combined_counter[char] for char in char_set)
        category_unique = len([char for char in char_set if combined_counter[char] > 0])
        percentage = (category_count / combined_total) * 100 if combined_total > 0 else 0
        
        print(f"{category_name:20s}: {category_unique:>3d} unique, {category_count:>10,} instances ({percentage:>5.2f}%)")
    
    # Non-ASCII characters
    non_ascii = {char: count for char, count in combined_counter.items() if ord(char) > 127}
    if non_ascii:
        print(f"\nNon-ASCII characters: {len(non_ascii)} unique, {sum(non_ascii.values()):,} instances")
        print("Non-ASCII character breakdown:")
        for char, count in sorted(non_ascii.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / combined_total) * 100
            print(f"  '{char}' (ord={ord(char):3d}): {count:>10,} ({percentage:>5.4f}%)")
    
    # Save detailed results
    output_file = base_path / 'character_frequency_analysis.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Character Frequency Analysis Results\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total characters: {combined_total:,}\n")
        f.write(f"Unique characters: {len(combined_counter)}\n\n")
        
        f.write("All characters sorted by frequency:\n")
        for i, (char, count) in enumerate(combined_counter.most_common(), 1):
            percentage = (count / combined_total) * 100
            f.write(f"{i:3d}. '{char}' (ord={ord(char):3d}): {count:>10,} ({percentage:>5.4f}%)\n")
    
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()