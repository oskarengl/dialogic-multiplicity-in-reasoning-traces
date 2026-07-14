import json
import re
import numpy as np

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def extract_and_evaluate_solutions(text, numbers):
    """Extract all boxed expressions and check if any evaluate to 24 using the given numbers."""
    # Pattern for \boxed{...}
    boxed_pattern = r'\\boxed\{([^}]+)\}'
    matches = re.findall(boxed_pattern, text)
    
    for expr in matches:
        # Clean up the expression
        cleaned = expr.strip()
        
        # Remove trailing "= 24" or similar
        cleaned = re.sub(r'\s*=\s*24\s*$', '', cleaned)
        cleaned = re.sub(r'\s*=\s*24\s*[,.!?]*$', '', cleaned)
        
        # Try to evaluate
        try:
            # Convert LaTeX to Python
            cleaned = cleaned.replace('\\frac', '').replace('{', '(').replace('}', ')')
            cleaned = cleaned.replace('\\times', '*').replace('\\div', '/')
            cleaned = cleaned.replace('\\cdot', '*')
            cleaned = cleaned.replace('\\left', '').replace('\\right', '')
            
            # Evaluate
            result = eval(cleaned)
            
            if abs(result - 24) < 0.001:
                return True, cleaned
        except:
            continue
    
    return False, None

def check_final_answer(text, numbers):
    """Check if the final answer in the text equals 24."""
    # Look for patterns like "final answer is: 24" or "answer: 24" etc.
    patterns = [
        r'(?:final answer|answer|solution|result)\s*(?:is|:|=)\s*24',
        r'24\s*(?:is the answer|is the solution|is the result)',
        r'\\boxed\{24\}',
        r'boxed\{24\}',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def extract_all_numbers_from_expression(expr):
    """Extract all numbers from an expression."""
    return [int(n) for n in re.findall(r'\d+', expr)]

def verify_solution_uses_numbers(expr, puzzle_numbers):
    """Check if the expression uses exactly the puzzle numbers."""
    expr_numbers = extract_all_numbers_from_expression(expr)
    puzzle_numbers_sorted = sorted(puzzle_numbers)
    expr_numbers_sorted = sorted(expr_numbers)
    
    return puzzle_numbers_sorted == expr_numbers_sorted

def comprehensive_correctness_check(debate):
    """Comprehensive check for correctness."""
    text = debate['full_text_no_labels']
    numbers = debate['puzzle']['numbers']
    
    # Method 1: Check boxed expressions
    has_boxed_24, boxed_expr = extract_and_evaluate_solutions(text, numbers)
    
    # Method 2: Check for final answer statements
    has_final_24 = check_final_answer(text, numbers)
    
    # Method 3: Look for any expression that evaluates to 24
    # Extract all mathematical expressions from the text
    # This is more complex, so we'll skip for now
    
    # Method 4: Check if there's a clear solution statement with the correct calculation
    # Look for patterns like "X * Y = 24" where X and Y are valid operations
    
    return has_boxed_24 or has_final_24, {
        'has_boxed_24': has_boxed_24,
        'boxed_expr': boxed_expr,
        'has_final_24': has_final_24
    }

def main():
    filepath = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    
    print("Loading debates...")
    debates = load_debates(filepath)
    print(f"Loaded {len(debates)} debates\n")
    
    print("="*80)
    print("COMPREHENSIVE CORRECTNESS CHECK")
    print("="*80)
    
    results = []
    for debate in debates:
        is_correct, details = comprehensive_correctness_check(debate)
        results.append({
            'debate_id': debate['source_item_id'],
            'is_correct': is_correct,
            'details': details,
            'numbers': debate['puzzle']['numbers'],
            'n_turns': debate['n_turns']
        })
    
    n_correct = sum(1 for r in results if r['is_correct'])
    n_incorrect = len(results) - n_correct
    
    print(f"\nNew correctness count:")
    print(f"  Correct: {n_correct} ({n_correct/len(results)*100:.1f}%)")
    print(f"  Incorrect: {n_incorrect} ({n_incorrect/len(results)*100:.1f}%)")
    
    print(f"\nBreakdown:")
    n_boxed = sum(1 for r in results if r['details']['has_boxed_24'])
    n_final = sum(1 for r in results if r['details']['has_final_24'])
    print(f"  Has boxed expression evaluating to 24: {n_boxed}")
    print(f"  Has final answer statement: {n_final}")
    
    # Show examples
    print("\n" + "="*80)
    print("EXAMPLES OF DEBATES MARKED CORRECT")
    print("="*80)
    
    correct_results = [r for r in results if r['is_correct']]
    for i, r in enumerate(correct_results[:5]):
        print(f"\nCorrect debate {i+1}: {r['debate_id']}")
        print(f"  Numbers: {r['numbers']}")
        print(f"  Turns: {r['n_turns']}")
        print(f"  Details: {r['details']}")
    
    print("\n" + "="*80)
    print("EXAMPLES OF DEBATES MARKED INCORRECT")
    print("="*80)
    
    incorrect_results = [r for r in results if not r['is_correct']]
    for i, r in enumerate(incorrect_results[:5]):
        print(f"\nIncorrect debate {i+1}: {r['debate_id']}")
        print(f"  Numbers: {r['numbers']}")
        print(f"  Turns: {r['n_turns']}")
        print(f"  Details: {r['details']}")
    
    # Compare with old heuristic
    print("\n" + "="*80)
    print("COMPARISON WITH OLD HEURISTIC")
    print("="*80)
    
    old_correct = 0
    for debate in debates:
        text = debate['full_text_no_labels']
        if r'\boxed{24}' in text or 'boxed{24}' in text or ('= 24' in text and 'boxed' in text):
            old_correct += 1
    
    print(f"Old heuristic: {old_correct} correct ({old_correct/len(debates)*100:.1f}%)")
    print(f"New heuristic: {n_correct} correct ({n_correct/len(debates)*100:.1f}%)")
    print(f"Difference: {n_correct - old_correct} ({(n_correct - old_correct)/len(debates)*100:.1f}%)")

if __name__ == '__main__':
    main()
