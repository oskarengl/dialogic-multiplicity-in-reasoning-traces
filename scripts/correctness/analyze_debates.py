import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def extract_turn_count_and_correctness(debates):
    """Extract turn counts and determine correctness for each debate."""
    import re
    
    def extract_and_evaluate_solutions(text, numbers):
        """Extract all boxed expressions and check if any evaluate to 24."""
        boxed_pattern = r'\\boxed\{([^}]+)\}'
        matches = re.findall(boxed_pattern, text)
        
        for expr in matches:
            cleaned = expr.strip()
            cleaned = re.sub(r'\s*=\s*24\s*$', '', cleaned)
            cleaned = re.sub(r'\s*=\s*24\s*[,.!?]*$', '', cleaned)
            
            try:
                cleaned = cleaned.replace('\\frac', '').replace('{', '(').replace('}', ')')
                cleaned = cleaned.replace('\\times', '*').replace('\\div', '/')
                cleaned = cleaned.replace('\\cdot', '*')
                cleaned = cleaned.replace('\\left', '').replace('\\right', '')
                result = eval(cleaned)
                if abs(result - 24) < 0.001:
                    return True
            except:
                continue
        return False
    
    def check_final_answer(text):
        """Check if the final answer in the text equals 24."""
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
    
    turn_counts = []
    correctness = []
    
    for debate in debates:
        n_turns = debate['n_turns']
        turn_counts.append(n_turns)
        
        text = debate['full_text_no_labels']
        numbers = debate['puzzle']['numbers']
        
        has_boxed_24 = extract_and_evaluate_solutions(text, numbers)
        has_final_24 = check_final_answer(text)
        
        correct = has_boxed_24 or has_final_24
        correctness.append(correct)
    
    return turn_counts, correctness

def plot_turn_count_distribution(turn_counts, correctness):
    """Create stacked histogram of turn counts split by correctness."""
    # Separate by correctness
    correct_turns = [tc for tc, corr in zip(turn_counts, correctness) if corr]
    incorrect_turns = [tc for tc, corr in zip(turn_counts, correctness) if not corr]
    
    # Get unique turn counts and their frequencies
    max_turns = max(turn_counts)
    bins = range(1, max_turns + 2)
    
    correct_hist, _ = np.histogram(correct_turns, bins=bins)
    incorrect_hist, _ = np.histogram(incorrect_turns, bins=bins)
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(1, max_turns + 1)
    width = 0.8
    
    # Plot stacked bars
    ax.bar(x, correct_hist, width, label='Correct', color='green', alpha=0.7)
    ax.bar(x, incorrect_hist, width, bottom=correct_hist, label='Incorrect', color='red', alpha=0.7)
    
    ax.set_xlabel('Number of Turns')
    ax.set_ylabel('Number of Debates')
    ax.set_title('Turn Count Distribution by Correctness')
    ax.set_xticks(x)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('c:/bachelor research/.1 recent approach/data/archive/documentation/diagnostics/plots/turn_count_distribution.png', dpi=150)
    plt.close()
    print("Saved turn_count_distribution.png")

def extract_solution_emergence_relative(debates):
    """Extract the relative position where correct solution first appears.
    Returns (n-x)/n where n is total turns and x is turn index of solution."""
    emergence_data = []
    
    for debate in debates:
        turns = debate['turns']
        n_turns = debate['n_turns']
        emergence_turn = None
        
        for i, turn in enumerate(turns):
            text = turn['text_clean']
            # Check if this turn contains a correct solution
            if r'\boxed{24}' in text or ('boxed' in text and '= 24' in text):
                emergence_turn = i
                break
        
        if emergence_turn is not None:
            # Calculate relative position: (n - x) / n
            # This represents how far from the end the solution appears
            # 0 = appears at last turn, 1 = appears at first turn
            relative_pos = (n_turns - emergence_turn) / n_turns
            emergence_data.append(relative_pos)
    
    return emergence_data

def plot_solution_emergence_relative(emergence_data):
    """Plot distribution of relative solution emergence positions."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create histogram with 20 bins
    ax.hist(emergence_data, bins=20, edgecolor='black', alpha=0.7, color='steelblue')
    
    ax.set_xlabel('Relative Position (n-x)/n')
    ax.set_ylabel('Number of Debates')
    ax.set_title('Solution Emergence: Relative Position from End')
    ax.set_xlim(0, 1)
    
    # Add percentage labels
    ax.set_xticks([i/10 for i in range(11)])
    ax.set_xticklabels([f'{i*10}%' for i in range(11)])
    
    plt.tight_layout()
    plt.savefig('c:/bachelor research/.1 recent approach/data/archive/documentation/diagnostics/plots/solution_emergence_relative.png', dpi=150)
    plt.close()
    print("Saved solution_emergence_relative.png")

def main():
    filepath = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    
    print("Loading debates...")
    debates = load_debates(filepath)
    print(f"Loaded {len(debates)} debates")
    
    print("\nExtracting turn counts and correctness...")
    turn_counts, correctness = extract_turn_count_and_correctness(debates)
    print(f"Correct: {sum(correctness)}, Incorrect: {len(correctness) - sum(correctness)}")
    
    print("\nPlotting turn count distribution...")
    plot_turn_count_distribution(turn_counts, correctness)
    
    print("\nExtracting solution emergence (relative)...")
    emergence_data = extract_solution_emergence_relative(debates)
    print(f"Debates with solution: {len(emergence_data)}/{len(debates)}")
    
    print("\nPlotting solution emergence (relative)...")
    plot_solution_emergence_relative(emergence_data)
    
    print("\nDone!")

if __name__ == '__main__':
    main()
