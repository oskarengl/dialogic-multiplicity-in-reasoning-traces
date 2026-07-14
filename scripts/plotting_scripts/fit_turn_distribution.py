import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import powerlaw

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def extract_turn_counts(debates):
    """Extract turn counts from debates."""
    return [debate['n_turns'] for debate in debates]

def fit_poisson(data):
    """Fit Poisson distribution and return goodness of fit."""
    lambda_param = np.mean(data)
    # Calculate expected frequencies
    max_val = max(data)
    observed = np.bincount(data, minlength=max_val+1)[1:]  # exclude 0
    expected = np.array([stats.poisson.pmf(k, lambda_param) for k in range(1, max_val+1)])
    expected = expected * len(data)
    
    # Combine bins with expected < 5
    # Start from the right and combine with left neighbor
    obs_adj = []
    exp_adj = []
    i = 0
    while i < len(expected):
        if expected[i] >= 5:
            obs_adj.append(observed[i])
            exp_adj.append(expected[i])
            i += 1
        else:
            # Combine with next bin
            if i < len(expected) - 1:
                obs_adj.append(observed[i] + observed[i+1])
                exp_adj.append(expected[i] + expected[i+1])
                i += 2
            else:
                # Last bin, combine with previous
                if len(obs_adj) > 0:
                    obs_adj[-1] += observed[i]
                    exp_adj[-1] += expected[i]
                i += 1
    
    obs_adj = np.array(obs_adj)
    exp_adj = np.array(exp_adj)
    
    # Normalize to ensure sums match
    total_obs = np.sum(obs_adj)
    total_exp = np.sum(exp_adj)
    if total_exp > 0:
        exp_adj = exp_adj * total_obs / total_exp
    
    if len(obs_adj) < 2:
        return None, None, None
    
    chi2, p_value = stats.chisquare(obs_adj, exp_adj)
    return lambda_param, chi2, p_value

def fit_geometric(data):
    """Fit geometric distribution and return goodness of fit."""
    # MLE for geometric p: p = 1 / (mean + 1)
    p_param = 1 / (np.mean(data) + 1)
    max_val = max(data)
    observed = np.bincount(data, minlength=max_val+1)[1:]  # exclude 0
    expected = np.array([stats.geom.pmf(k, p_param) for k in range(1, max_val+1)])
    expected = expected * len(data)
    
    # Combine bins with expected < 5
    obs_adj = []
    exp_adj = []
    i = 0
    while i < len(expected):
        if expected[i] >= 5:
            obs_adj.append(observed[i])
            exp_adj.append(expected[i])
            i += 1
        else:
            # Combine with next bin
            if i < len(expected) - 1:
                obs_adj.append(observed[i] + observed[i+1])
                exp_adj.append(expected[i] + expected[i+1])
                i += 2
            else:
                # Last bin, combine with previous
                if len(obs_adj) > 0:
                    obs_adj[-1] += observed[i]
                    exp_adj[-1] += expected[i]
                i += 1
    
    obs_adj = np.array(obs_adj)
    exp_adj = np.array(exp_adj)
    
    # Normalize to ensure sums match
    total_obs = np.sum(obs_adj)
    total_exp = np.sum(exp_adj)
    if total_exp > 0:
        exp_adj = exp_adj * total_obs / total_exp
    
    if len(obs_adj) < 2:
        return None, None, None
    
    chi2, p_value = stats.chisquare(obs_adj, exp_adj)
    return p_param, chi2, p_value

def fit_exponential(data):
    """Fit exponential distribution and return goodness of fit."""
    # MLE for exponential lambda: 1 / mean
    lambda_param = 1 / np.mean(data)
    
    # KS test
    D, p_value = stats.kstest(data, 'expon', args=(0, 1/lambda_param))
    return lambda_param, D, p_value

def fit_lognormal(data):
    """Fit lognormal distribution and return goodness of fit."""
    shape, loc, scale = stats.lognorm.fit(data, floc=0)
    
    # KS test
    D, p_value = stats.kstest(data, 'lognorm', args=(shape, loc, scale))
    return shape, scale, D, p_value

def fit_powerlaw(data):
    """Fit power law distribution using powerlaw package."""
    try:
        # Try with automatic xmin selection
        fit = powerlaw.Fit(data, discrete=True)
        alpha = fit.power_law.alpha
        sigma = fit.power_law.sigma
        xmin = fit.power_law.xmin
        
        # Compare with alternative distributions
        R, p = fit.distribution_compare('power_law', 'exponential')
        R2, p2 = fit.distribution_compare('power_law', 'lognormal')
        R3, p3 = fit.distribution_compare('power_law', 'poisson')
        
        return alpha, sigma, xmin, R, p, R2, p2, R3, p3
    except Exception as e:
        print(f"  Power law fit failed: {e}")
        return None, None, None, None, None, None, None, None

def fit_negative_binomial(data):
    """Fit negative binomial distribution (good for overdispersed count data)."""
    try:
        # Method of moments estimation
        mean = np.mean(data)
        var = np.var(data)
        
        if var <= mean:
            return None, None, None
        
        # Estimate parameters
        r = mean**2 / (var - mean)  # size parameter
        p = mean / var  # probability parameter
        
        max_val = max(data)
        observed = np.bincount(data, minlength=max_val+1)[1:]  # exclude 0
        expected = np.array([stats.nbinom.pmf(k, r, p) for k in range(1, max_val+1)])
        expected = expected * len(data)
        
        # Combine bins with expected < 5
        obs_adj = []
        exp_adj = []
        i = 0
        while i < len(expected):
            if expected[i] >= 5:
                obs_adj.append(observed[i])
                exp_adj.append(expected[i])
                i += 1
            else:
                if i < len(expected) - 1:
                    obs_adj.append(observed[i] + observed[i+1])
                    exp_adj.append(expected[i] + expected[i+1])
                    i += 2
                else:
                    if len(obs_adj) > 0:
                        obs_adj[-1] += observed[i]
                        exp_adj[-1] += expected[i]
                    i += 1
        
        obs_adj = np.array(obs_adj)
        exp_adj = np.array(exp_adj)
        
        # Normalize
        total_obs = np.sum(obs_adj)
        total_exp = np.sum(exp_adj)
        if total_exp > 0:
            exp_adj = exp_adj * total_obs / total_exp
        
        if len(obs_adj) < 2:
            return None, None, None
        
        chi2, p_value = stats.chisquare(obs_adj, exp_adj)
        return r, p, chi2, p_value
    except Exception as e:
        print(f"  Negative binomial fit failed: {e}")
        return None, None, None

def main():
    filepath = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    
    print("Loading debates...")
    debates = load_debates(filepath)
    print(f"Loaded {len(debates)} debates")
    
    print("\nExtracting turn counts...")
    turn_counts = extract_turn_counts(debates)
    print(f"Turn count range: {min(turn_counts)} to {max(turn_counts)}")
    print(f"Mean: {np.mean(turn_counts):.2f}, Std: {np.std(turn_counts):.2f}")
    print(f"Median: {np.median(turn_counts):.2f}")
    
    # Fit distributions
    print("\n" + "="*60)
    print("FITTING DISTRIBUTIONS")
    print("="*60)
    
    # Poisson
    print("\nPoisson Distribution:")
    lambda_param, chi2, p_value = fit_poisson(turn_counts)
    if lambda_param is not None:
        print(f"  Lambda (mean): {lambda_param:.2f}")
        print(f"  Chi-squared: {chi2:.2f}")
        print(f"  p-value: {p_value:.4f}")
        print(f"  {'✓ Good fit' if p_value > 0.05 else '✗ Poor fit'} (p > 0.05)")
    else:
        print("  Could not fit (insufficient data)")
    
    # Geometric
    print("\nGeometric Distribution:")
    p_param, chi2, p_value = fit_geometric(turn_counts)
    if p_param is not None:
        print(f"  p parameter: {p_param:.4f}")
        print(f"  Chi-squared: {chi2:.2f}")
        print(f"  p-value: {p_value:.4f}")
        print(f"  {'✓ Good fit' if p_value > 0.05 else '✗ Poor fit'} (p > 0.05)")
    else:
        print("  Could not fit (insufficient data)")
    
    # Exponential
    print("\nExponential Distribution:")
    lambda_param, D, p_value = fit_exponential(turn_counts)
    print(f"  Lambda (rate): {lambda_param:.4f}")
    print(f"  Kolmogorov-Smirnov D: {D:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  {'✓ Good fit' if p_value > 0.05 else '✗ Poor fit'} (p > 0.05)")
    
    # Lognormal
    print("\nLognormal Distribution:")
    shape, scale, D, p_value = fit_lognormal(turn_counts)
    print(f"  Shape parameter: {shape:.4f}")
    print(f"  Scale parameter: {scale:.4f}")
    print(f"  Kolmogorov-Smirnov D: {D:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  {'✓ Good fit' if p_value > 0.05 else '✗ Poor fit'} (p > 0.05)")
    
    # Negative Binomial
    print("\nNegative Binomial Distribution:")
    r, p, chi2, p_value = fit_negative_binomial(turn_counts)
    if r is not None:
        print(f"  r (size) parameter: {r:.4f}")
        print(f"  p parameter: {p:.4f}")
        print(f"  Chi-squared: {chi2:.2f}")
        print(f"  p-value: {p_value:.4f}")
        print(f"  {'✓ Good fit' if p_value > 0.05 else '✗ Poor fit'} (p > 0.05)")
    else:
        print("  Could not fit (variance <= mean)")
    
    # Power Law
    print("\nPower Law Distribution:")
    alpha = None
    result = fit_powerlaw(turn_counts)
    if result and result[0] is not None:
        alpha, sigma, xmin, R, p, R2, p2, R3, p3 = result
        print(f"  Alpha (exponent): {alpha:.4f}")
        print(f"  Sigma (std error): {sigma:.4f}")
        print(f"  xmin: {xmin}")
        print(f"\n  Comparison with Exponential:")
        print(f"    Log-likelihood ratio R: {R:.4f}")
        print(f"    p-value: {p:.4f}")
        print(f"    {'Power law preferred' if R > 0 and p < 0.05 else 'Exponential preferred or no significant difference'}")
        print(f"\n  Comparison with Lognormal:")
        print(f"    Log-likelihood ratio R: {R2:.4f}")
        print(f"    p-value: {p2:.4f}")
        print(f"    {'Power law preferred' if R2 > 0 and p2 < 0.05 else 'Lognormal preferred or no significant difference'}")
        print(f"\n  Comparison with Poisson:")
        print(f"    Log-likelihood ratio R: {R3:.4f}")
        print(f"    p-value: {p3:.4f}")
        print(f"    {'Power law preferred' if R3 > 0 and p3 < 0.05 else 'Poisson preferred or no significant difference'}")
    else:
        print("  Could not fit power law")
    
    # Create comparison plot
    print("\nCreating comparison plot...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Histogram with fitted distributions
    ax = axes[0, 0]
    counts, bins, _ = ax.hist(turn_counts, bins=range(1, max(turn_counts)+2), 
                              density=True, alpha=0.7, label='Observed', edgecolor='black')
    
    x = np.arange(1, max(turn_counts)+1)
    
    # Poisson
    if lambda_param is not None:
        poisson_pmf = stats.poisson.pmf(x, lambda_param)
        ax.plot(x, poisson_pmf, 'o-', label='Poisson', linewidth=2)
    
    # Geometric
    if p_param is not None:
        geom_pmf = stats.geom.pmf(x, p_param)
        ax.plot(x, geom_pmf, 's-', label='Geometric', linewidth=2)
    
    # Exponential (PDF)
    if lambda_param is not None:
        exp_pdf = stats.expon.pdf(x, scale=1/lambda_param)
        ax.plot(x, exp_pdf, '^-', label='Exponential', linewidth=2)
    
    # Negative Binomial
    if r is not None:
        nbinom_pmf = stats.nbinom.pmf(x, r, p)
        ax.plot(x, nbinom_pmf, 'd-', label='Negative Binomial', linewidth=2)
    
    ax.set_xlabel('Turn Count')
    ax.set_ylabel('Probability')
    ax.set_title('Turn Count Distribution with Fitted Models')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Log-log plot for power law check
    ax = axes[0, 1]
    hist, bin_edges = np.histogram(turn_counts, bins=range(1, max(turn_counts)+2))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    ax.loglog(bin_centers, hist, 'o', label='Observed', markersize=8)
    
    if alpha is not None:
        # Power law fit line
        x_fit = np.linspace(min(bin_centers), max(bin_centers), 100)
        y_fit = np.exp(-alpha * np.log(x_fit))  # Simplified power law visualization
        # Normalize to match data scale
        y_fit = y_fit * max(hist) / max(y_fit)
        ax.loglog(x_fit, y_fit, '--', label=f'Power law (α={alpha:.2f})', linewidth=2)
    
    ax.set_xlabel('Turn Count (log scale)')
    ax.set_ylabel('Frequency (log scale)')
    ax.set_title('Log-Log Plot (Power Law Check)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Q-Q plot for normality check
    ax = axes[1, 0]
    stats.probplot(turn_counts, dist="norm", plot=ax)
    ax.set_title('Q-Q Plot (Normal Distribution)')
    ax.grid(True, alpha=0.3)
    
    # CDF comparison
    ax = axes[1, 1]
    sorted_data = np.sort(turn_counts)
    empirical_cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax.plot(sorted_data, empirical_cdf, 'o-', label='Empirical CDF', markersize=4)
    
    if lambda_param is not None:
        poisson_cdf = stats.poisson.cdf(x, lambda_param)
        ax.plot(x, poisson_cdf, '--', label='Poisson CDF', linewidth=2)
    
    if p_param is not None:
        geom_cdf = stats.geom.cdf(x, p_param)
        ax.plot(x, geom_cdf, '--', label='Geometric CDF', linewidth=2)
    
    if r is not None:
        nbinom_cdf = stats.nbinom.cdf(x, r, p)
        ax.plot(x, nbinom_cdf, '--', label='Negative Binomial CDF', linewidth=2)
    
    ax.set_xlabel('Turn Count')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title('CDF Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('c:/bachelor research/.1 recent approach/data/archive/documentation/diagnostics/plots/distribution_fit.png', dpi=150)
    print("Saved distribution_fit.png")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("Based on statistical tests and visual inspection, the distribution")
    print("that best fits the turn count data is reported above.")
    print("Higher p-values indicate better fit for chi-squared and KS tests.")
    print("For power law comparisons, positive R with p < 0.05 indicates")
    print("the power law is preferred over the alternative.")

if __name__ == '__main__':
    main()
