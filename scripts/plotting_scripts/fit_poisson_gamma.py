import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import minimize

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def extract_turn_counts(debates):
    """Extract turn counts from debates."""
    return [debate['n_turns'] for debate in debates]

def fit_negative_binomial_mle(data):
    """Fit Negative Binomial using MLE with multiple optimization strategies."""
    def neg_log_likelihood(params):
        r, p = params
        # Ensure valid parameter ranges
        if r <= 0 or p <= 0 or p >= 1:
            return np.inf
        # Negative log likelihood
        nll = -np.sum(stats.nbinom.logpmf(data, r, p))
        return nll
    
    mean = np.mean(data)
    var = np.var(data)
    
    if var <= mean:
        print("Variance <= mean, data may not be overdispersed")
        return None, None
    
    # Multiple initial guesses
    initial_guesses = []
    
    # Method of moments
    r_init = mean**2 / (var - mean)
    p_init = mean / var
    initial_guesses.append([r_init, p_init])
    
    # Alternative initial guesses
    initial_guesses.append([5.0, 0.5])
    initial_guesses.append([10.0, 0.5])
    initial_guesses.append([15.0, 0.6])
    initial_guesses.append([8.0, 0.4])
    
    best_result = None
    best_nll = np.inf
    
    # Try different optimization methods
    methods = ['L-BFGS-B', 'Nelder-Mead', 'Powell']
    
    for guess in initial_guesses:
        for method in methods:
            try:
                if method == 'L-BFGS-B':
                    result = minimize(neg_log_likelihood, guess, 
                                     method=method,
                                     bounds=[(0.001, None), (0.001, 0.999)])
                else:
                    result = minimize(neg_log_likelihood, guess, 
                                     method=method)
                
                if result.success and result.fun < best_nll:
                    best_nll = result.fun
                    best_result = result
            except:
                continue
    
    if best_result is not None:
        r_opt, p_opt = best_result.x
        return r_opt, p_opt, best_nll
    else:
        return None, None, None

def fit_poisson_gamma_parameters(data):
    """
    Fit Negative Binomial directly and report parameters.
    """
    r, p, nll = fit_negative_binomial_mle(data)
    
    if r is None:
        return None
    
    return {
        'negative_binomial_r': r,
        'negative_binomial_p': p,
        'negative_log_likelihood': nll,
        'data_mean': np.mean(data),
        'data_var': np.var(data)
    }

def main():
    filepath = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    
    print("Loading debates...")
    debates = load_debates(filepath)
    print(f"Loaded {len(debates)} debates")
    
    print("\nExtracting turn counts...")
    turn_counts = extract_turn_counts(debates)
    print(f"Turn count range: {min(turn_counts)} to {max(turn_counts)}")
    print(f"Mean: {np.mean(turn_counts):.4f}")
    print(f"Variance: {np.var(turn_counts):.4f}")
    print(f"Std: {np.std(turn_counts):.4f}")
    print(f"Dispersion index (variance/mean): {np.var(turn_counts)/np.mean(turn_counts):.4f}")
    
    print("\n" + "="*60)
    print("NEGATIVE BINOMIAL FIT (MLE)")
    print("="*60)
    
    params = fit_poisson_gamma_parameters(turn_counts)
    
    if params:
        print("\nNegative Binomial Parameters:")
        print(f"  r (size/shape): {params['negative_binomial_r']:.4f}")
        print(f"  p (probability): {params['negative_binomial_p']:.4f}")
        print(f"  Negative Log Likelihood: {params['negative_log_likelihood']:.4f}")
        
        print("\nModel Interpretation:")
        print(f"  The turn counts follow a Negative Binomial distribution:")
        print(f"  - Parameters: r={params['negative_binomial_r']:.4f}, p={params['negative_binomial_p']:.4f}")
        print(f"  - This accounts for overdispersion (variance > mean)")
        
        # Create visualization
        print("\nCreating visualization...")
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram with fitted distribution
        ax = axes[0]
        counts, bins, _ = ax.hist(turn_counts, bins=range(1, max(turn_counts)+2), 
                                  density=True, alpha=0.7, label='Observed', 
                                  edgecolor='black', color='steelblue')
        
        x = np.arange(1, max(turn_counts)+1)
        nbinom_pmf = stats.nbinom.pmf(x, params['negative_binomial_r'], 
                                       params['negative_binomial_p'])
        ax.plot(x, nbinom_pmf, 'ro-', label='Fitted Negative Binomial', 
                linewidth=2, markersize=6)
        
        ax.set_xlabel('Turn Count')
        ax.set_ylabel('Probability')
        ax.set_title('Turn Count Distribution: Negative Binomial')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Q-Q plot
        ax = axes[1]
        # Generate theoretical quantiles from fitted Negative Binomial
        n_samples = len(turn_counts)
        theoretical_quantiles = np.random.negative_binomial(
            params['negative_binomial_r'], 
            params['negative_binomial_p'], 
            size=10000)
        theoretical_quantiles.sort()
        
        # Get quantiles
        quantiles = np.linspace(0, 1, n_samples)
        observed_quantiles = np.quantile(turn_counts, quantiles)
        theoretical_q = np.quantile(theoretical_quantiles, quantiles)
        
        ax.scatter(theoretical_q, observed_quantiles, alpha=0.5, s=20)
        ax.plot([min(theoretical_q), max(theoretical_q)], 
                [min(theoretical_q), max(theoretical_q)], 
                'r--', linewidth=2)
        ax.set_xlabel('Theoretical Quantiles (Negative Binomial)')
        ax.set_ylabel('Observed Quantiles')
        ax.set_title('Q-Q Plot: Observed vs Fitted Distribution')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('c:/bachelor research/.1 recent approach/data/archive/documentation/diagnostics/plots/negative_binomial_fit.png', dpi=150)
        print("Saved negative_binomial_fit.png")
        
    else:
        print("Could not fit Negative Binomial")

if __name__ == '__main__':
    main()
