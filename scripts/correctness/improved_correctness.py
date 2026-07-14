import json
import re
import numpy as np
import pandas as pd
from scipy import stats

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def load_puzzle_difficulty(csv_path):
    df = pd.read_csv(csv_path)
    difficulty_map = {}
    for _, row in df.iterrows():
        difficulty_map[row['source_item_id']] = row['difficulty_score']
    return difficulty_map

def extract_and_evaluate_solutions(text, numbers):
    """Extract all boxed expressions and check if any evaluate to 24."""
    # Pattern for \boxed{...}
    boxed_pattern = r'\\boxed\{([^}]+)\}'
    matches = re.findall(boxed_pattern, text)
    
    for expr in matches:
        # Skip text-only boxed content
        if '\\text' in expr or 'No valid solution' in expr or 'not possible' in expr.lower():
            continue
            
        cleaned = expr.strip()
        # Remove trailing "= 24" or similar
        cleaned = re.sub(r'\s*=\s*24\s*$', '', cleaned)
        cleaned = re.sub(r'\s*=\s*24\s*[,.!?]*$', '', cleaned)
        
        try:
            # Convert LaTeX to Python
            cleaned = cleaned.replace('\\frac', '').replace('{', '(').replace('}', ')')
            cleaned = cleaned.replace('\\times', '*').replace('\\div', '/')
            cleaned = cleaned.replace('\\cdot', '*')
            cleaned = cleaned.replace('\\left', '').replace('\\right', '')
            result = eval(cleaned)
            if abs(result - 24) < 0.001:
                return True, cleaned
        except:
            continue
    return False, None

def check_final_answer_patterns(text, numbers):
    """Check for various patterns indicating a final answer of 24."""
    
    # Pattern 1: Expression followed by "= 24"
    pattern1 = r'[\(\[]?\d+[\s\+\-\*\/\d\(\)\[\]\{\}]+[\)\]]?\s*=\s*24'
    matches1 = re.findall(pattern1, text)
    
    for expr in matches1:
        try:
            # Extract the expression part (before = 24)
            expr_part = re.sub(r'\s*=\s*24\s*$', '', expr)
            # Convert to evaluable form
            expr_part = expr_part.replace('\\times', '*').replace('\\div', '/')
            expr_part = expr_part.replace('\\cdot', '*')
            # Only evaluate if it looks like a mathematical expression
            if any(op in expr_part for op in ['+', '-', '*', '/']):
                result = eval(expr_part)
                if abs(result - 24) < 0.001:
                    return True
        except:
            continue
    
    # Pattern 2: "solution is/answer is/final answer" followed by expression
    pattern2 = r'(?:solution|answer|final answer|final solution)\s*(?:is|:|=)\s*([^.,!?\n]+)'
    matches2 = re.findall(pattern2, text, re.IGNORECASE)
    
    for expr in matches2:
        if '24' in expr:
            try:
                # Try to evaluate the expression
                cleaned = expr.strip()
                cleaned = cleaned.replace('\\times', '*').replace('\\div', '/')
                cleaned = cleaned.replace('\\cdot', '*')
                cleaned = cleaned.replace('\\frac', '').replace('{', '(').replace('}', ')')
                cleaned = cleaned.replace('\\left', '').replace('\\right', '')
                # Remove trailing punctuation
                cleaned = re.sub(r'[.,!?]+$', '', cleaned)
                result = eval(cleaned)
                if abs(result - 24) < 0.001:
                    return True
            except:
                # If it contains "24" and claims to be the answer, mark as likely correct
                if '24' in expr and any(op in expr for op in ['+', '-', '*', '/']):
                    return True
    
    # Pattern 3: "equals 24" or "yields 24" or "results in 24"
    pattern3 = r'(?:equals|yields|results in|gives|produces)\s*24'
    if re.search(pattern3, text, re.IGNORECASE):
        return True
    
    # Pattern 4: Expression followed by "equals 24"
    pattern4 = r'[\(\[]?\d+[\s\+\-\*\/\d\(\)\[\]\{\}]+[\)\]]?\s*(?:equals|yields|results in)\s*24'
    if re.search(pattern4, text, re.IGNORECASE):
        return True
    
    return False

def check_no_solution(text):
    """Check if the debate concludes there is no solution."""
    no_solution_patterns = [
        r'no valid solution',
        r'not possible',
        r'cannot.*24',
        r'impossible.*24',
        r'does not have a solution',
        r'unattainable',
        r'no solution exists'
    ]
    
    for pattern in no_solution_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def comprehensive_correctness_check(debate):
    """Comprehensive check for correctness using multiple patterns."""
    text = debate['full_text_no_labels']
    numbers = debate['puzzle']['numbers']
    
    # Check for explicit "no solution" statements
    if check_no_solution(text):
        return False, {'method': 'no_solution_statement'}
    
    # Check boxed expressions
    has_boxed_24, boxed_expr = extract_and_evaluate_solutions(text, numbers)
    if has_boxed_24:
        return True, {'method': 'boxed_expression', 'expr': boxed_expr}
    
    # Check final answer patterns
    has_final_24 = check_final_answer_patterns(text, numbers)
    if has_final_24:
        return True, {'method': 'final_answer_pattern'}
    
    return False, {'method': 'no_pattern_match'}

def main():
    debate_file = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    csv_file = 'c:/bachelor research/.1 recent approach/data/00_core-2x2/ai_debate/puzzle_selection_game24.csv'
    
    print("Loading debates...")
    debates = load_debates(debate_file)
    print(f"Loaded {len(debates)} debates")
    
    print("\nLoading puzzle difficulties...")
    difficulty_map = load_puzzle_difficulty(csv_file)
    print(f"Loaded difficulties for {len(difficulty_map)} puzzles")
    
    print("\nExtracting difficulty and correctness...")
    difficulties = []
    correctness = []
    methods = []
    
    for debate in debates:
        puzzle_id = debate.get('source_item_id')
        if puzzle_id in difficulty_map:
            difficulties.append(difficulty_map[puzzle_id])
            is_correct, details = comprehensive_correctness_check(debate)
            correctness.append(is_correct)
            methods.append(details['method'])
    
    difficulties = np.array(difficulties)
    correctness = np.array(correctness)
    
    print(f"Matched {len(difficulties)} debates with difficulty scores")
    
    n_correct = np.sum(correctness)
    n_incorrect = len(correctness) - n_correct
    print(f"\nCorrect: {n_correct} ({n_correct/len(correctness)*100:.1f}%)")
    print(f"Incorrect: {n_incorrect} ({n_incorrect/len(correctness)*100:.1f}%)")
    
    # Breakdown by method
    from collections import Counter
    method_counts = Counter(methods)
    print("\nCorrectness methods breakdown:")
    for method, count in method_counts.items():
        print(f"  {method}: {count}")
    
    print(f"\nDifficulty range: {np.min(difficulties):.2f} to {np.max(difficulties):.2f}")
    
    # Correlation analysis
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS")
    print("="*60)
    
    correlation, p_value = stats.pointbiserialr(difficulties, correctness)
    print(f"Point-biserial correlation: {correlation:.4f}")
    print(f"P-value: {p_value:.4f}")
    
    if p_value < 0.05:
        print("  Statistically significant correlation")
    else:
        print("  Not statistically significant")
    
    if abs(correlation) > 0.3:
        print("  Moderate to strong correlation")
    elif abs(correlation) > 0.1:
        print("  Weak correlation")
    else:
        print("  Very weak or no correlation")
    
    # Stratified analysis
    print("\n" + "="*60)
    print("STRATIFIED ANALYSIS BY DIFFICULTY")
    print("="*60)
    
    n_strata = 4
    quantiles = np.percentile(difficulties, np.linspace(0, 100, n_strata + 1))
    strata_labels = ['Easy', 'Medium-Easy', 'Medium-Hard', 'Hard']
    
    for i in range(n_strata):
        lower = quantiles[i]
        upper = quantiles[i + 1]
        
        mask = (difficulties >= lower) & (difficulties < upper)
        if i == n_strata - 1:
            mask = (difficulties >= lower) & (difficulties <= upper)
        
        stratum_correctness = correctness[mask]
        stratum_diffs = difficulties[mask]
        
        if len(stratum_correctness) < 10:
            print(f"\n{strata_labels[i]} (n={len(stratum_correctness)}): Skipped")
            continue
        
        n_corr = np.sum(stratum_correctness)
        accuracy = n_corr / len(stratum_correctness)
        
        print(f"\n{strata_labels[i]} (n={len(stratum_correctness)}):")
        print(f"  Difficulty range: {lower:.2f} to {upper:.2f}")
        print(f"  Accuracy: {accuracy*100:.1f}% ({n_corr}/{len(stratum_correctness)})")

if __name__ == '__main__':
    main()
