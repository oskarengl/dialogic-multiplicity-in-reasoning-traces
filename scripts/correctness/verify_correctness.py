import json
import re

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def extract_solutions_from_text(text):
    """Extract all boxed expressions from text."""
    # Pattern for \boxed{...}
    boxed_pattern = r'\\boxed\{([^}]+)\}'
    matches = re.findall(boxed_pattern, text)
    return matches

def evaluate_expression(expr, numbers):
    """Try to evaluate an expression to see if it equals 24."""
    try:
        # Remove any LaTeX formatting
        expr = expr.replace('\\frac', '').replace('{', '(').replace('}', ')')
        expr = expr.replace('\\times', '*').replace('\\div', '/')
        expr = expr.replace('\\cdot', '*')
        
        # Evaluate safely
        result = eval(expr)
        return abs(result - 24) < 0.001
    except:
        return False

def main():
    filepath = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    
    print("Loading debates...")
    debates = load_debates(filepath)
    print(f"Loaded {len(debates)} debates\n")
    
    # Sample first 10 debates
    print("="*80)
    print("INSPECTING FIRST 10 DEBATES")
    print("="*80)
    
    for i, debate in enumerate(debates[:10]):
        print(f"\n{'='*80}")
        print(f"Debate {i+1}: {debate['source_item_id']}")
        print(f"Numbers: {debate['puzzle']['numbers']}")
        print(f"Turns: {debate['n_turns']}")
        print(f"{'='*80}")
        
        full_text = debate['full_text_no_labels']
        
        # Current heuristic
        current_correct = bool(r'\boxed{24}' in full_text or 'boxed{24}' in full_text or ('= 24' in full_text and 'boxed' in full_text))
        
        # Extract all boxed expressions
        boxed_exprs = extract_solutions_from_text(full_text)
        
        print(f"\nCurrent heuristic says: {'CORRECT' if current_correct else 'INCORRECT'}")
        print(f"Found {len(boxed_exprs)} boxed expressions:")
        
        for expr in boxed_exprs:
            print(f"  - {expr}")
            is_24 = evaluate_expression(expr, debate['puzzle']['numbers'])
            print(f"    Evaluates to 24: {is_24}")
        
        # Show a snippet of the text
        print(f"\nText snippet (first 500 chars):")
        print(full_text[:500])
        print("...")
        
        # Show the last 500 chars (where solution likely is)
        print(f"\nText snippet (last 500 chars):")
        print(full_text[-500:])
    
    # Statistics
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)
    
    current_correct_count = 0
    has_boxed_24_count = 0
    has_any_boxed_count = 0
    
    for debate in debates:
        full_text = debate['full_text_no_labels']
        
        current_correct = bool(r'\boxed{24}' in full_text or 'boxed{24}' in full_text or ('= 24' in full_text and 'boxed' in full_text))
        if current_correct:
            current_correct_count += 1
        
        if r'\boxed{24}' in full_text:
            has_boxed_24_count += 1
        
        boxed_exprs = extract_solutions_from_text(full_text)
        if boxed_exprs:
            has_any_boxed_count += 1
    
    print(f"Current heuristic marks as correct: {current_correct_count}/{len(debates)} ({current_correct_count/len(debates)*100:.1f}%)")
    print(f"Has literal \\boxed{{24}}: {has_boxed_24_count}/{len(debates)} ({has_boxed_24_count/len(debates)*100:.1f}%)")
    print(f"Has any boxed expression: {has_any_boxed_count}/{len(debates)} ({has_any_boxed_count/len(debates)*100:.1f}%)")
    
    # Check a few debates that are marked correct
    print("\n" + "="*80)
    print("SAMPLE OF DEBATES MARKED CORRECT")
    print("="*80)
    
    correct_debates = [d for d in debates if r'\boxed{24}' in d['full_text_no_labels'] or 'boxed{24}' in d['full_text_no_labels'] or ('= 24' in d['full_text_no_labels'] and 'boxed' in d['full_text_no_labels'])]
    
    for i, debate in enumerate(correct_debates[:5]):
        print(f"\nCorrect debate {i+1}: {debate['source_item_id']}")
        print(f"Numbers: {debate['puzzle']['numbers']}")
        boxed_exprs = extract_solutions_from_text(debate['full_text_no_labels'])
        print(f"Boxed expressions: {boxed_exprs}")
        
        # Check if any actually evaluate to 24
        for expr in boxed_exprs:
            is_24 = evaluate_expression(expr, debate['puzzle']['numbers'])
            print(f"  {expr} -> 24: {is_24}")

if __name__ == '__main__':
    main()
