"""
Analyze Position of Chinese Characters in AI Debates

Tests the hypothesis that Chinese text appears at the end of debates
after conclusions have been reached, making truncation viable.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def is_chinese_char(char: str) -> bool:
    """Check if character is Chinese."""
    code_point = ord(char)
    # CJK Unified Ideographs
    if 0x4E00 <= code_point <= 0x9FFF:
        return True
    # CJK Unified Ideographs Extension A
    if 0x3400 <= code_point <= 0x4DBF:
        return True
    # Chinese punctuation
    if char in '，。：；？！「」『（）【】':
        return True
    return False


def analyze_chinese_position(text: str) -> dict:
    """Analyze where Chinese characters appear in text."""
    if not text:
        return {'has_chinese': False, 'positions': [], 'first_chinese_idx': None, 'last_chinese_idx': None}
    
    chinese_positions = []
    for i, char in enumerate(text):
        if is_chinese_char(char):
            chinese_positions.append(i)
    
    if not chinese_positions:
        return {
            'has_chinese': False,
            'positions': [],
            'first_chinese_idx': None,
            'last_chinese_idx': None,
            'chinese_percentage': 0
        }
    
    first_chinese = min(chinese_positions)
    last_chinese = max(chinese_positions)
    
    return {
        'has_chinese': True,
        'positions': chinese_positions,
        'first_chinese_idx': first_chinese,
        'last_chinese_idx': last_chinese,
        'first_chinese_percentage': (first_chinese / len(text)) * 100,
        'last_chinese_percentage': (last_chinese / len(text)) * 100,
        'chinese_count': len(chinese_positions),
        'chinese_percentage': (len(chinese_positions) / len(text)) * 100,
        'text_length': len(text)
    }


def check_conclusion_before_chinese(text: str, chinese_analysis: dict) -> dict:
    """Check if there's a valid conclusion before Chinese starts."""
    if not chinese_analysis['has_chinese']:
        return {'has_conclusion': False, 'reason': 'No Chinese text'}
    
    # Get text before Chinese starts
    if chinese_analysis['first_chinese_idx'] > 0:
        text_before_chinese = text[:chinese_analysis['first_chinese_idx']]
    else:
        return {'has_conclusion': False, 'reason': 'Chinese starts at beginning'}
    
    # Look for conclusion indicators in the English part
    conclusion_indicators = [
        'therefore', 'thus', 'so', 'consequently', 'as a result',
        'in conclusion', 'finally', 'ultimately', 'answer is',
        'solution is', 'result is', 'equals 24', ' = 24',
        'final answer', 'the answer', 'we get', 'gives us',
        'yields', 'results in', 'leads to'
    ]
    
    text_lower = text_before_chinese.lower()
    found_indicators = []
    
    for indicator in conclusion_indicators:
        if indicator in text_lower:
            # Find the position of this indicator
            idx = text_lower.find(indicator)
            found_indicators.append({
                'indicator': indicator,
                'position': idx,
                'percentage': (idx / len(text)) * 100
            })
    
    # Check if there are mathematical expressions suggesting solution
    import re
    math_patterns = [
        r'\d+\s*[\+\-\*\/]\s*\d+',  # Simple math like "3 + 4"
        r'\([^)]+\)\s*[\+\-\*\/]\s*\([^)]+\)',  # Parenthesized math
        r'\d+\s*=\s*24',  # Equals 24
        r'24\s*=',  # 24 equals something
    ]
    
    found_math = []
    for pattern in math_patterns:
        matches = list(re.finditer(pattern, text_before_chinese))
        for match in matches:
            found_math.append({
                'match': match.group(),
                'position': match.start(),
                'percentage': (match.start() / len(text)) * 100
            })
    
    # Get the last few sentences before Chinese
    sentences_before_chinese = text_before_chinese.split('.')[-5:]  # Last 5 sentences
    
    return {
        'has_conclusion': len(found_indicators) > 0 or len(found_math) > 0,
        'conclusion_indicators': found_indicators,
        'math_expressions': found_math,
        'sentences_before_chinese': sentences_before_chinese,
        'text_before_chinese_length': len(text_before_chinese),
        'text_before_chinese_percentage': (len(text_before_chinese) / len(text)) * 100
    }


def analyze_ai_debate_positions(filepath: Path) -> list:
    """Analyze Chinese character positions in all AI debates."""
    results = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                text = data.get('full_text_no_labels', '')
                debate_id = data.get('debate_id', f'row_{line_num}')
                
                chinese_analysis = analyze_chinese_position(text)
                conclusion_analysis = check_conclusion_before_chinese(text, chinese_analysis)
                
                if chinese_analysis['has_chinese']:
                    results.append({
                        'debate_id': debate_id,
                        'row_num': line_num,
                        'chinese_analysis': chinese_analysis,
                        'conclusion_analysis': conclusion_analysis,
                        'text_length': len(text),
                        'puzzle_id': data.get('puzzle_id', 'unknown')
                    })
                    
            except json.JSONDecodeError:
                continue
    
    return results


def main():
    """Main analysis function."""
    print("=" * 80)
    print("Chinese Character Position Analysis in AI Debates")
    print("=" * 80)
    
    filepath = Path(r'C:\bachelor research\.1 recent approach\data\archive\ai_debate\original_chinese_ai_debate.jsonl')
    
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        return
    
    print(f"\nAnalyzing: {filepath.name}")
    
    results = analyze_ai_debate_positions(filepath)
    
    print(f"\nFound {len(results)} debates with Chinese characters")
    
    # Categorize by Chinese position
    early_chinese = [r for r in results if r['chinese_analysis']['first_chinese_percentage'] < 20]
    middle_chinese = [r for r in results if 20 <= r['chinese_analysis']['first_chinese_percentage'] < 50]
    late_chinese = [r for r in results if r['chinese_analysis']['first_chinese_percentage'] >= 50]
    
    print(f"\nChinese Position Categories:")
    print(f"  Early (<20%): {len(early_chinese)} debates")
    print(f"  Middle (20-50%): {len(middle_chinese)} debates")
    print(f"  Late (>=50%): {len(late_chinese)} debates")
    
    # Analyze conclusion presence
    with_conclusion = [r for r in results if r['conclusion_analysis']['has_conclusion']]
    without_conclusion = [r for r in results if not r['conclusion_analysis']['has_conclusion']]
    
    print(f"\nConclusion Analysis:")
    print(f"  With conclusion indicators before Chinese: {len(with_conclusion)}")
    print(f"  Without clear conclusion: {len(without_conclusion)}")
    
    # Show detailed analysis for most contaminated debates
    print(f"\n" + "=" * 80)
    print("Detailed Analysis of Most Contaminated Debates (Top 15)")
    print("=" * 80)
    
    sorted_by_contamination = sorted(results, key=lambda x: x['chinese_analysis']['chinese_percentage'], reverse=True)
    
    for i, result in enumerate(sorted_by_contamination[:15], 1):
        chinese = result['chinese_analysis']
        conclusion = result['conclusion_analysis']
        
        print(f"\n{i}. Debate ID: {result['debate_id']}, Puzzle: {result['puzzle_id']}")
        print(f"   Chinese: {chinese['chinese_count']} chars ({chinese['chinese_percentage']:.2f}%)")
        print(f"   First Chinese at: {chinese['first_chinese_percentage']:.2f}% of text")
        print(f"   Last Chinese at: {chinese['last_chinese_percentage']:.2f}% of text")
        print(f"   Text before Chinese: {conclusion['text_before_chinese_percentage']:.2f}%")
        print(f"   Conclusion before Chinese: {conclusion['has_conclusion']}")
        
        if conclusion['has_conclusion']:
            print(f"   Conclusion indicators: {[c['indicator'] for c in conclusion['conclusion_indicators']]}")
            if conclusion['math_expressions']:
                print(f"   Math expressions: {[m['match'] for m in conclusion['math_expressions'][:3]]}")
        
        # Show sample of text before and after Chinese starts
        if chinese['first_chinese_idx'] > 0:
            before_sample = result['text_length'] > 0
            text_sample = "..."  # We'd need the full text here
            
    # Truncation viability assessment
    print(f"\n" + "=" * 80)
    print("TRUNCATION VIABILITY ASSESSMENT")
    print("=" * 80)
    
    truncation_candidates = [r for r in results if r['chinese_analysis']['first_chinese_percentage'] > 70]
    print(f"\nDebates where Chinese starts after 70% of text: {len(truncation_candidates)}")
    print(f"These are good candidates for simple truncation.")
    
    moderate_candidates = [r for r in results if 50 < r['chinese_analysis']['first_chinese_percentage'] <= 70]
    print(f"\nDebates where Chinese starts between 50-70% of text: {len(moderate_candidates)}")
    print(f"These might be truncatable but need review.")
    
    poor_candidates = [r for r in results if r['chinese_analysis']['first_chinese_percentage'] <= 50]
    print(f"\nDebates where Chinese starts early (<=50%): {len(poor_candidates)}")
    print(f"These are NOT good candidates for truncation - may need regeneration.")
    
    # Overall recommendation
    print(f"\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    total_with_chinese = len(results)
    truncation_viable = len(truncation_candidates) + len(moderate_candidates)
    
    if truncation_viable > 0:
        print(f"✅ GOOD NEWS: {truncation_viable}/{total_with_chinese} ({truncation_viable/total_with_chinese*100:.1f}%) of corrupted debates")
        print(f"   appear to have Chinese at the end, making truncation viable.")
        print(f"   Only {len(poor_candidates)} debates ({len(poor_candidates)/total_with_chinese*100:.1f}%) need regeneration.")
    
    if len(with_conclusion) > 0:
        print(f"\n✅ CONCLUSION EVIDENCE: {len(with_conclusion)}/{total_with_chinese} ({len(with_conclusion)/total_with_chinese*100:.1f}%)")
        print(f"   have conclusion indicators before Chinese starts, supporting your hypothesis.")


if __name__ == "__main__":
    main()