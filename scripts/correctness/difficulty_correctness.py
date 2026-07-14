import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def load_puzzle_difficulty(csv_path):
    """Load puzzle difficulty scores from CSV."""
    df = pd.read_csv(csv_path)
    difficulty_map = {}
    for _, row in df.iterrows():
        difficulty_map[row['source_item_id']] = row['difficulty_score']
    return difficulty_map

def extract_correctness(debate):
    """Determine if debate contains a correct solution."""
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
    
    full_text = debate['full_text_no_labels']
    numbers = debate['puzzle']['numbers']
    
    has_boxed_24 = extract_and_evaluate_solutions(full_text, numbers)
    has_final_24 = check_final_answer(full_text)
    
    return has_boxed_24 or has_final_24

def extract_difficulty_and_correctness(debates, difficulty_map):
    """Extract difficulty scores and correctness for each debate."""
    difficulties = []
    correctness = []
    
    for debate in debates:
        puzzle_id = debate.get('source_item_id')
        if puzzle_id in difficulty_map:
            difficulties.append(difficulty_map[puzzle_id])
            correctness.append(extract_correctness(debate))
    
    return np.array(difficulties), np.array(correctness)

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
    difficulties, correctness = extract_difficulty_and_correctness(debates, difficulty_map)
    print(f"Matched {len(difficulties)} debates with difficulty scores")
    
    n_correct = np.sum(correctness)
    n_incorrect = len(correctness) - n_correct
    print(f"Correct: {n_correct} ({n_correct/len(correctness)*100:.1f}%)")
    print(f"Incorrect: {n_incorrect} ({n_incorrect/len(correctness)*100:.1f}%)")
    
    print(f"\nDifficulty range: {np.min(difficulties):.2f} to {np.max(difficulties):.2f}")
    
    # Correlation analysis
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS")
    print("="*60)
    
    # Point-biserial correlation (correlation between continuous variable and binary)
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
    
    results = []
    
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
        
        results.append({
            'label': strata_labels[i],
            'accuracy': accuracy,
            'n': len(stratum_correctness),
            'difficulty_range': (lower, upper)
        })
    
    # Plotting
    print("\nCreating visualization...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Scatter plot (jittered for binary correctness)
    ax = axes[0, 0]
    jitter = np.random.uniform(-0.05, 0.05, size=len(difficulties))
    ax.scatter(difficulties, correctness + jitter, alpha=0.3, s=20)
    ax.set_xlabel('Difficulty Score')
    ax.set_ylabel('Correctness (jittered)')
    ax.set_title('Correctness vs Difficulty')
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Incorrect', 'Correct'])
    ax.grid(True, alpha=0.3)
    
    # Add trend line (logistic regression approximation)
    from sklearn.linear_model import LogisticRegression
    X = difficulties.reshape(-1, 1)
    y = correctness
    logreg = LogisticRegression()
    logreg.fit(X, y)
    x_range = np.linspace(np.min(difficulties), np.max(difficulties), 100).reshape(-1, 1)
    y_prob = logreg.predict_proba(x_range)[:, 1]
    ax.plot(x_range, y_prob, 'r-', linewidth=2, label='Logistic fit')
    ax.legend()
    
    # 2. Accuracy by difficulty stratum
    ax = axes[0, 1]
    accuracies = [res['accuracy'] * 100 for res in results]
    labels = [res['label'] for res in results]
    ax.bar(labels, accuracies, alpha=0.7, edgecolor='black', color='steelblue')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Accuracy by Difficulty Stratum')
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add overall accuracy line
    overall_acc = np.sum(correctness) / len(correctness) * 100
    ax.axhline(y=overall_acc, color='r', linestyle='--', linewidth=2, label=f'Overall: {overall_acc:.1f}%')
    ax.legend()
    
    # 3. Difficulty distribution by correctness
    ax = axes[1, 0]
    correct_diffs = difficulties[correctness == 1]
    incorrect_diffs = difficulties[correctness == 0]
    ax.hist(correct_diffs, bins=20, alpha=0.5, label='Correct', color='green', density=True)
    ax.hist(incorrect_diffs, bins=20, alpha=0.5, label='Incorrect', color='red', density=True)
    ax.set_xlabel('Difficulty Score')
    ax.set_ylabel('Density')
    ax.set_title('Difficulty Distribution by Correctness')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Cumulative accuracy by difficulty
    ax = axes[1, 1]
    sorted_indices = np.argsort(difficulties)
    sorted_diffs = difficulties[sorted_indices]
    sorted_corr = correctness[sorted_indices]
    
    # Calculate rolling accuracy
    window_size = 50
    rolling_acc = []
    rolling_diffs = []
    
    for i in range(window_size, len(sorted_diffs)):
        window_corr = sorted_corr[i-window_size:i]
        acc = np.sum(window_corr) / len(window_corr)
        rolling_acc.append(acc)
        rolling_diffs.append(sorted_diffs[i])
    
    ax.plot(rolling_diffs, rolling_acc, linewidth=2, color='steelblue')
    ax.set_xlabel('Difficulty Score')
    ax.set_ylabel('Rolling Accuracy (50-debate window)')
    ax.set_title('Accuracy Trend by Difficulty')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('c:/bachelor research/.1 recent approach/data/archive/documentation/diagnostics/plots/difficulty_correctness.png', dpi=150)
    print("Saved difficulty_correctness.png")

if __name__ == '__main__':
    main()
