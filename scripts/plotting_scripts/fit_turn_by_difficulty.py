import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import minimize
import pandas as pd

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def load_puzzle_difficulty(csv_path):
    """Load puzzle difficulty scores from CSV."""
    df = pd.read_csv(csv_path)
    # Create mapping from puzzle_id to difficulty_score
    difficulty_map = {}
    for _, row in df.iterrows():
        difficulty_map[row['source_item_id']] = row['difficulty_score']
    return difficulty_map

def extract_turn_counts_with_difficulty(debates, difficulty_map):
    """Extract turn counts and difficulty scores."""
    turn_counts = []
    difficulties = []
    
    for debate in debates:
        puzzle_id = debate.get('source_item_id')
        if puzzle_id in difficulty_map:
            turn_counts.append(debate['n_turns'])
            difficulties.append(difficulty_map[puzzle_id])
    
    return np.array(turn_counts), np.array(difficulties)

def fit_negative_binomial_mle(data):
    """Fit Negative Binomial using MLE."""
    def neg_log_likelihood(params):
        r, p = params
        if r <= 0 or p <= 0 or p >= 1:
            return np.inf
        nll = -np.sum(stats.nbinom.logpmf(data, r, p))
        return nll
    
    mean = np.mean(data)
    var = np.var(data)
    
    if var <= mean:
        return None, None, None
    
    r_init = mean**2 / (var - mean)
    p_init = mean / var
    
    result = minimize(neg_log_likelihood, [r_init, p_init], 
                     bounds=[(0.001, None), (0.001, 0.999)])
    
    if result.success:
        r_opt, p_opt = result.x
        return r_opt, p_opt, result.fun
    else:
        return None, None, None

def main():
    debate_file = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    csv_file = 'c:/bachelor research/.1 recent approach/data/00_core-2x2/ai_debate/puzzle_selection_game24.csv'
    
    print("Loading debates...")
    debates = load_debates(debate_file)
    print(f"Loaded {len(debates)} debates")
    
    print("\nLoading puzzle difficulties...")
    difficulty_map = load_puzzle_difficulty(csv_file)
    print(f"Loaded difficulties for {len(difficulty_map)} puzzles")
    
    print("\nExtracting turn counts with difficulties...")
    turn_counts, difficulties = extract_turn_counts_with_difficulty(debates, difficulty_map)
    print(f"Matched {len(turn_counts)} debates with difficulty scores")
    
    print(f"\nDifficulty range: {np.min(difficulties):.2f} to {np.max(difficulties):.2f}")
    print(f"Turn count range: {np.min(turn_counts)} to {np.max(turn_counts)}")
    
    # Stratify by difficulty quantiles
    print("\n" + "="*60)
    print("STRATIFIED ANALYSIS BY DIFFICULTY")
    print("="*60)
    
    # Create difficulty strata
    n_strata = 4
    quantiles = np.percentile(difficulties, np.linspace(0, 100, n_strata + 1))
    strata_labels = ['Easy', 'Medium-Easy', 'Medium-Hard', 'Hard']
    
    results = []
    
    for i in range(n_strata):
        lower = quantiles[i]
        upper = quantiles[i + 1]
        
        mask = (difficulties >= lower) & (difficulties < upper)
        if i == n_strata - 1:  # Include upper bound for last stratum
            mask = (difficulties >= lower) & (difficulties <= upper)
        
        stratum_turns = turn_counts[mask]
        stratum_diffs = difficulties[mask]
        
        if len(stratum_turns) < 10:
            print(f"\n{strata_labels[i]} (n={len(stratum_turns)}): Skipped (too few samples)")
            continue
        
        r, p, nll = fit_negative_binomial_mle(stratum_turns)
        
        print(f"\n{strata_labels[i]} (n={len(stratum_turns)}):")
        print(f"  Difficulty range: {lower:.2f} to {upper:.2f}")
        print(f"  Mean turns: {np.mean(stratum_turns):.2f}")
        print(f"  Variance: {np.var(stratum_turns):.2f}")
        print(f"  Dispersion: {np.var(stratum_turns)/np.mean(stratum_turns):.2f}")
        
        if r is not None:
            print(f"  Negative Binomial r: {r:.4f}")
            print(f"  Negative Binomial p: {p:.4f}")
            print(f"  Negative Log Likelihood: {nll:.4f}")
            results.append({
                'label': strata_labels[i],
                'turns': stratum_turns,
                'difficulties': stratum_diffs,
                'r': r,
                'p': p,
                'nll': nll
            })
        else:
            print(f"  Failed to fit distribution")
    
    # Plotting
    print("\nCreating visualization...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Turn count vs difficulty scatter
    ax = axes[0, 0]
    ax.scatter(difficulties, turn_counts, alpha=0.5, s=20)
    ax.set_xlabel('Difficulty Score')
    ax.set_ylabel('Turn Count')
    ax.set_title('Turn Count vs Difficulty')
    ax.grid(True, alpha=0.3)
    
    # Add trend line
    z = np.polyfit(difficulties, turn_counts, 1)
    p = np.poly1d(z)
    x_trend = np.linspace(np.min(difficulties), np.max(difficulties), 100)
    ax.plot(x_trend, p(x_trend), 'r-', linewidth=2, label=f'Trend: {z[0]:.2f}x + {z[1]:.2f}')
    ax.legend()
    
    # 2. Histograms by difficulty stratum
    ax = axes[0, 1]
    for res in results:
        ax.hist(res['turns'], bins=range(1, 41), alpha=0.5, label=res['label'], density=True)
    ax.set_xlabel('Turn Count')
    ax.set_ylabel('Density')
    ax.set_title('Turn Count Distribution by Difficulty Stratum')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Mean turns by difficulty stratum
    ax = axes[1, 0]
    means = [np.mean(res['turns']) for res in results]
    labels = [res['label'] for res in results]
    ax.bar(labels, means, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Mean Turn Count')
    ax.set_title('Mean Turn Count by Difficulty Stratum')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 4. Negative Binomial parameters by stratum
    ax = axes[1, 1]
    r_values = [res['r'] for res in results]
    p_values = [res['p'] for res in results]
    
    x = np.arange(len(labels))
    width = 0.35
    
    ax.bar(x - width/2, r_values, width, label='r (shape)', alpha=0.7)
    ax2 = ax.twinx()
    ax2.bar(x + width/2, p_values, width, label='p (prob)', alpha=0.7, color='orange')
    
    ax.set_xlabel('Difficulty Stratum')
    ax.set_ylabel('r parameter', color='blue')
    ax2.set_ylabel('p parameter', color='orange')
    ax.set_title('Negative Binomial Parameters by Difficulty')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('c:/bachelor research/.1 recent approach/data/archive/documentation/diagnostics/plots/turn_by_difficulty.png', dpi=150)
    print("Saved turn_by_difficulty.png")
    
    # Correlation analysis
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS")
    print("="*60)
    correlation = np.corrcoef(difficulties, turn_counts)[0, 1]
    print(f"Correlation between difficulty and turn count: {correlation:.4f}")
    
    if abs(correlation) > 0.3:
        print("  Moderate to strong correlation detected")
    elif abs(correlation) > 0.1:
        print("  Weak correlation detected")
    else:
        print("  Very weak or no correlation")

if __name__ == '__main__':
    main()
