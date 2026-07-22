# Method 1 Validation Report: Reproducing the PAN 2019 Style-Change Detection Result

**Date:** 2026-07-15  
**Repository:** `C:\bachelor research\.1 recent approach\methods\1_style_change_detection\implementation`  
**Algorithm:** Threshold-Based Clustering (TBC) / Window-Merge Clustering (WMC) — Nath et al.  
**Dataset:** PAN 2019 Style Change Detection (training, validation, and official test splits)

## 1. Objective

The original published PAN 2019 result for Method 1 (TBC) reports an accuracy of **~84.8%** on the official PAN 2019 test set. Before using the method in the present study, the implementation was re-validated against the same known benchmark. The initial reproduction run obtained only **~70.4% binary accuracy**, so the implementation was debugged and corrected.

## 2. Data

All PAN 2019 splits are located under:

```
C:\bachelor research\.1 recent approach\methods\1_style_change_detection\pan19 data\
```

| Split | Documents | Single- / Multi-author distribution | Ground truth available |
|---|---|---|---|
| Training | 2,546 | 50% / 50% | Yes |
| Validation | 1,272 | 50% / 50% | Yes |
| Test | 1,210 | 50% / 50% | Yes (released after the competition) |

The official test set was used for the final validation, because the test split is the one on which the 84.8% score was reported.

## 3. Reference Result

The PAN 2019 task defines **accuracy** as the binary classification of single-author vs. multi-author documents. The number-of-authors prediction is scored separately with the Ordinal Classification Index (OCI). The combined ranking score is `(accuracy + (1 - OCI)) / 2`.

Source: PAN 2019 Style Change Detection task page and CLEF 2019 overview paper:  
- <https://pan.webis.de/clef19/pan19-web/style-change-detection.html>  
- <https://downloads.webis.de/pan/publications/papers/zangerle_2019.pdf>  
- <https://ceur-ws.org/Vol-2380/paper_243.pdf>

The Nath participant row in the PAN 2019 final table is:

| Participant | Accuracy | OCI | Rank |
|---|---|---|---|
| Nath (TBC) | 0.848 | 0.865 | 0.491 |

Thus the target for the present reproduction is **binary accuracy ≈ 0.85** on the official test set.

## 4. Bugs Found and Fixes Applied

### 4.1 TBC clustering threshold bug (critical)

**File:** `src/algorithms/threshold_clustering/cluster_graph.py`

The threshold used to decide whether a new window could be added to a cluster (and whether two clusters could merge) was computed as:

```python
add_node_threshold = add_node_threshold / (cluster_size * avg_dist)
```

The feature matrix stores **normalized** word frequencies, so `avg_dist` is usually < 1. Dividing by `cluster_size * avg_dist` therefore made the effective threshold far too large, causing almost every document to collapse into a single cluster and be predicted as one author.

**Fix:** remove the `avg_dist` term from the divisor:

```python
add_node_threshold = add_node_threshold / cluster_size
```

The same correction was applied to the merge threshold. This is the change that restores the reported accuracy.

### 4.2 `prune_clusters` return value ignored

**File:** `src/algorithms/threshold_clustering/executor.py`

The code called `prune_clusters(cg_list)` but did not capture the returned list, so pruning had no effect. The result is now assigned:

```python
if prune:
    cg_list = prune_clusters(cg_list)
```

### 4.3 NumPy / NetworkX compatibility issues

**File:** `src/algorithms/threshold_clustering/cluster_graph.py`

- `cg1.node.keys()` was replaced with `cg1.nodes` for NetworkX 3.x compatibility.
- 2-D NumPy array membership checks (`entry not in entries_already_traversed`) were replaced with an explicit row-wise equality test.

### 4.4 WMC `statistics.stdev` crash

**File:** `src/algorithms/window_merge_clustering/executor.py`

`get_number_of_authors` built `win_len_arr` as a NumPy array. Python 3.11's `statistics.stdev` raises an error on `numpy.int64` values. The array was changed to a plain Python list of `int`s.

WMC now runs without the previous "Something went wrong" fallback; it remains a fallback method, however, and is slower and less accurate than TBC on the test set.

## 5. Reproduction Command

From the `implementation` directory:

```powershell
& "venv\Scripts\python.exe" evaluate_benchmark.py -i "..\pan19 data\test" -a TBC
```

## 6. Results After Fixes

### 6.1 TBC

| PAN 2019 Split | Binary Accuracy | Exact-Count Accuracy | Runtime |
|---|---|---|---|
| Training | 0.8354 | 0.5786 | ~105 s |
| Validation | 0.8349 | 0.5802 | ~58 s |
| **Test** | **0.8496** | 0.5835 | ~52 s |

The **test binary accuracy of 0.8496** reproduces the reported ~84.8% score.

### 6.2 WMC (50-document subset, used for sanity check)

| Method | Binary Accuracy | Exact-Count Accuracy | Runtime |
|---|---|---|---|
| WMC | 0.7200 | 0.6200 | ~76 s |

WMC is computationally expensive and does not reach the TBC score; it is not the primary validated method.

## 7. Interpretation

- The official PAN 2019 **accuracy** is binary (single vs. multi-author). Method 1 now reaches the reported value on the official test set.
- The **exact-count accuracy** (~0.58) is a separate, harder metric. The low value is not inconsistent with the PAN 2019 table: the Nath submission had an OCI of 0.865, which is also far from perfect, giving a combined rank of 0.491.
- For the present study, Method 1 can therefore be treated as validated for the binary **monologue vs. dialogue** decision, which is the intended use case.

## 8. Files Changed

- `src/algorithms/threshold_clustering/cluster_graph.py` — threshold-adaptation fix and compatibility fixes.
- `src/algorithms/threshold_clustering/executor.py` — `prune_clusters` result assigned.
- `src/algorithms/window_merge_clustering/executor.py` — `win_len_arr` type fixed for Python 3.11 `statistics.stdev`.
- `AGENTS.md` — added run commands and expected scores for future agents.

## 9. Conclusion

The PAN 2019 TBC implementation is validated. After correcting the clustering threshold adaptation, the binary accuracy on the official test set is **0.8496**, matching the published ~84.8% score.
