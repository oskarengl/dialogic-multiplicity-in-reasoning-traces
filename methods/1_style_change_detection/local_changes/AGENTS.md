# Agent Notes: Style-Change Detection (Method 1)

## Environment
- Python 3.11, virtual environment in `venv\`.
- Activate or use directly: `venv\Scripts\python.exe`.

## Running the PAN 2019 benchmark
From the `implementation` directory:

```powershell
& "venv\Scripts\python.exe" evaluate_benchmark.py -i "..\pan19_data\test" -a TBC
```

Replace `-a TBC` with `-a WMC` for the window-merge variant. `-n <N>` limits to the first N documents.

## Expected PAN 2019 TBC scores (after fixes)
| Split     | Binary Accuracy | Exact-Count Accuracy | Notes |
|-----------|----------------|----------------------|-------|
| Training  | ~0.835         | ~0.579               | 2,546 docs |
| Validation| ~0.835         | ~0.580               | 1,272 docs |
| Test      | ~0.850         | ~0.584               | 1,210 docs |

The ~0.850 binary accuracy on the official test set matches the ~84.8% reported by Nath et al. for PAN 2019.

## Key fixes applied
1. `src/algorithms/threshold_clustering/cluster_graph.py`:
   - Fixed NetworkX API usage (`cg1.nodes` instead of `cg1.node.keys()`).
   - Fixed NumPy 2D-array membership checks for traversed edge entries.
   - **Critical fix:** threshold adaptation now divides by cluster size only, not `cluster_size * avg_dist`. The extra `avg_dist` divisor made thresholds far too lenient on normalized frequency distances, causing over-merging.

2. `src/algorithms/threshold_clustering/executor.py`:
   - `prune_clusters(cg_list)` return value is now assigned back to `cg_list`.

3. `src/algorithms/window_merge_clustering/executor.py`:
   - `win_len_arr` is a plain Python list so `statistics.stdev` works with Python ints under Python 3.11.
   - Added traceback printing during WMC exceptions for debugging.
