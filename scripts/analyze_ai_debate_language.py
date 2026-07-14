"""
Language Analysis for AI Debate Dataset

Quantifies the extent of non-English character usage in AI debate data
to determine if cleaning is feasible or if regeneration is needed.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Define character ranges for different languages
LANGUAGE_RANGES = {
    'Chinese': [
        (0x4E00, 0x9FFF),   # CJK Unified Ideographs
        (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
        (0x20000, 0x2A6DF), # CJK Unified Ideographs Extension B
        (0x2A700, 0x2B73F), # CJK Unified Ideographs Extension C
        (0x2B740, 0x2B81F), # CJK Unified Ideographs Extension D
        (0x2B820, 0x2CEAF), # CJK Unified Ideographs Extension E
        (0x2CEB0, 0x2EBEF), # CJK Unified Ideographs Extension F
        (0x3000, 0x303F),   # CJK Symbols and Punctuation
        (0xFF00, 0xFFEF),   # Halfwidth and Fullwidth Forms
    ],
    'Japanese': [
        (0x3040, 0x309F),   # Hiragana
        (0x30A0, 0x30FF),   # Katakana
        (0x31F0, 0x31FF),   # Katakana Phonetic Extensions
    ],
    'Korean': [
        (0xAC00, 0xD7AF),   # Hangul Syllables
        (0x1100, 0x11FF),   # Hangul Jamo
        (0x3130, 0x318F),   # Hangul Compatibility Jamo
    ],
    'Arabic': [
        (0x0600, 0x06FF),   # Arabic
        (0x0750, 0x077F),   # Arabic Supplement
    ],
    'Cyrillic': [
        (0x0400, 0x04FF),   # Cyrillic
        (0x0500, 0x052F),   # Cyrillic Supplement
    ],
    'Greek': [
        (0x0370, 0x03FF),   # Greek and Coptic
    ],
    'Latin_Extended': [
        (0x0100, 0x017F),   # Latin Extended-A
        (0x0180, 0x024F),   # Latin Extended-B
    ],
}


def detect_language(char: str) -> str:
    """Detect which language a character belongs to."""
    code_point = ord(char)
    
    # Check each language range
    for language, ranges in LANGUAGE_RANGES.items():
        for start, end in ranges:
            if start <= code_point <= end:
                return language
    
    # Special cases for common symbols
    if char in '×÷≈−≠√→':
        return 'Math_Symbols'
    if char in '，。：；？！「」『（）【】':
        return 'Chinese_Punctuation'
    if char in '、':
        return 'Japanese_Punctuation'
    
    # ASCII
    if code_point < 128:
        return 'ASCII'
    
    return 'Other'


def analyze_ai_debate(filepath: Path) -> dict:
    """Analyze language distribution in AI debate dataset."""
    language_counter = Counter()
    row_language_stats = []
    total_chars = 0
    non_english_chars = 0
    row_count = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                text = data.get('full_text_no_labels', '')
                
                row_lang_counter = Counter()
                row_non_english = 0
                row_total = len(text)
                
                for char in text:
                    lang = detect_language(char)
                    language_counter[lang] += 1
                    row_lang_counter[lang] += 1
                    total_chars += 1
                    
                    if lang != 'ASCII' and lang != 'Math_Symbols':
                        non_english_chars += 1
                        row_non_english += 1
                
                row_count += 1
                
                # Calculate row statistics
                row_non_english_pct = (row_non_english / row_total * 100) if row_total > 0 else 0
                row_language_stats.append({
                    'row_index': row_count,
                    'total_chars': row_total,
                    'non_english_chars': row_non_english,
                    'non_english_percentage': row_non_english_pct,
                    'language_breakdown': dict(row_lang_counter)
                })
                
            except json.JSONDecodeError:
                continue
    
    return {
        'language_counter': language_counter,
        'row_language_stats': row_language_stats,
        'total_chars': total_chars,
        'non_english_chars': non_english_chars,
        'row_count': row_count,
        'non_english_percentage': (non_english_chars / total_chars * 100) if total_chars > 0 else 0
    }


def main():
    """Main analysis function."""
    print("=" * 80)
    print("Language Analysis for AI Debate Dataset")
    print("=" * 80)
    
    filepath = Path(r'C:\bachelor research\.1 recent approach\data\archive\ai_debate\original_chinese_ai_debate.jsonl')
    
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        return
    
    print(f"\nAnalyzing: {filepath.name}")
    
    results = analyze_ai_debate(filepath)
    
    print(f"\nOverall Statistics:")
    print(f"  Total rows: {results['row_count']}")
    print(f"  Total characters: {results['total_chars']:,}")
    print(f"  Non-English characters: {results['non_english_chars']:,}")
    print(f"  Non-English percentage: {results['non_english_percentage']:.2f}%")
    
    print(f"\nLanguage Breakdown:")
    for lang, count in results['language_counter'].most_common():
        percentage = (count / results['total_chars'] * 100) if results['total_chars'] > 0 else 0
        print(f"  {lang:20s}: {count:>10,} ({percentage:>6.2f}%)")
    
    # Row-level analysis
    print(f"\nRow-Level Analysis:")
    
    # Categorize rows by non-English percentage
    clean_rows = [r for r in results['row_language_stats'] if r['non_english_percentage'] == 0]
    minor_contamination = [r for r in results['row_language_stats'] if 0 < r['non_english_percentage'] < 1]
    moderate_contamination = [r for r in results['row_language_stats'] if 1 <= r['non_english_percentage'] < 5]
    heavy_contamination = [r for r in results['row_language_stats'] if r['non_english_percentage'] >= 5]
    
    print(f"  Clean rows (0% non-English): {len(clean_rows)} ({len(clean_rows)/results['row_count']*100:.1f}%)")
    print(f"  Minor contamination (<1%): {len(minor_contamination)} ({len(minor_contamination)/results['row_count']*100:.1f}%)")
    print(f"  Moderate contamination (1-5%): {len(moderate_contamination)} ({len(moderate_contamination)/results['row_count']*100:.1f}%)")
    print(f"  Heavy contamination (>=5%): {len(heavy_contamination)} ({len(heavy_contamination)/results['row_count']*100:.1f}%)")
    
    # Show most contaminated rows
    print(f"\nTop 20 Most Contaminated Rows:")
    sorted_rows = sorted(results['row_language_stats'], key=lambda x: x['non_english_percentage'], reverse=True)
    for i, row in enumerate(sorted_rows[:20], 1):
        print(f"  {i:2d}. Row {row['row_index']:3d}: {row['non_english_percentage']:5.2f}% non-English ({row['non_english_chars']}/{row['total_chars']} chars)")
        # Show language breakdown for contaminated rows
        if row['non_english_percentage'] > 0:
            print(f"      Languages: ", end="")
            for lang, count in sorted(row['language_breakdown'].items(), key=lambda x: x[1], reverse=True):
                if lang != 'ASCII' and count > 0:
                    print(f"{lang}({count}) ", end="")
            print()
    
    # Show sample of non-English characters found
    print(f"\nSample Non-English Characters Found:")
    non_english_chars = set()
    for row in results['row_language_stats']:
        for lang, count in row['language_breakdown'].items():
            if lang != 'ASCII' and lang != 'Math_Symbols':
                # We'd need to track actual characters, not just counts
                pass
    
    # Recommendation
    print(f"\n" + "=" * 80)
    print("ASSESSMENT AND RECOMMENDATION")
    print("=" * 80)
    
    if len(heavy_contamination) > 0:
        print(f"⚠️  ISSUE: {len(heavy_contamination)} rows ({len(heavy_contamination)/results['row_count']*100:.1f}%) have heavy non-English contamination (>=5%)")
        print(f"   These rows are likely corrupted and may need regeneration.")
    
    if len(moderate_contamination) > 0:
        print(f"⚠️  ISSUE: {len(moderate_contamination)} rows ({len(moderate_contamination)/results['row_count']*100:.1f}%) have moderate contamination (1-5%)")
        print(f"   These could potentially be cleaned, but regeneration might be safer.")
    
    if len(minor_contamination) > 0:
        print(f"✓ ACCEPTABLE: {len(minor_contamination)} rows ({len(minor_contamination)/results['row_count']*100:.1f}%) have minor contamination (<1%)")
        print(f"   These can likely be cleaned with character filtering.")
    
    if len(clean_rows) > 0:
        print(f"✓ GOOD: {len(clean_rows)} rows ({len(clean_rows)/results['row_count']*100:.1f}%) are completely clean")
    
    overall_assessment = results['non_english_percentage']
    if overall_assessment < 0.1:
        print(f"\n🟢 OVERALL: Low contamination ({overall_assessment:.2f}%) - Cleaning is feasible")
    elif overall_assessment < 1:
        print(f"\n🟡 OVERALL: Moderate contamination ({overall_assessment:.2f}%) - Cleaning possible but review needed")
    elif overall_assessment < 5:
        print(f"\n🟠 OVERALL: High contamination ({overall_assessment:.2f}%) - Consider partial regeneration")
    else:
        print(f"\n🔴 OVERALL: Severe contamination ({overall_assessment:.2f}%) - Regeneration recommended")


if __name__ == "__main__":
    main()