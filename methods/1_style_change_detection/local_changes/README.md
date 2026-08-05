# Local changes to the nath19 implementation

Method 1 runs the original PAN 2019 winning system by Nath, pinned as a submodule at
`../implementation` (upstream: https://github.com/pan-webis-de/nath19, commit `ede16f8`).

The code as published does not run on a current Python stack, and it needed changes
before it could be used. Those changes live here rather than in the submodule, because the
submodule tracks upstream.

## Applying

```bash
git submodule update --init methods/1_style_change_detection/implementation
cd methods/1_style_change_detection/implementation
git apply ../local_changes/upstream_modifications.patch
cp ../local_changes/run_calibration.py ../local_changes/reproduce_compare.py ../local_changes/evaluate_benchmark.py .
```

## What the patch changes

**One change alters the algorithm, and anyone reading the Method 1 result should know
about it.** In six places the clustering thresholds were renormalised:

```python
-  add_node_threshold = add_node_threshold / (cluster_size * avg_dist)
+  add_node_threshold = add_node_threshold / cluster_size
```

The same substitution is applied to `merge_cluster_threshold` for both cluster graphs in
`check_cg_merge_criteria` and `check_cg_merge_criteria2`. Dividing by the average
intra-cluster distance as well as the cluster size made the effective threshold collapse on
our documents. This is a deviation from the published method, and Method 1's reported
failure of the validity check is a result produced by the patched code, not by the original
system as it was submitted to PAN 2019.

The remaining changes are compatibility and bug fixes needed to run the 2019 code at all:

| Change | Reason |
|---|---|
| `_entry_in_array()` helper replaces `entry not in array` | `in` on a 2-D numpy array raises the truth-value-ambiguous error on modern numpy |
| `cg1.node` → `cg1.nodes` | networkx removed the `.node` alias in 2.4 |
| `np.asarray([])` → `.reshape(0, 3)` | empty placeholder needed a 3-column shape to compare against entries |
| `prune_clusters(cg_list)` → `cg_list = prune_clusters(cg_list)` | the return value was discarded, so pruning had no effect |
| `win_len_arr` kept as a list rather than `np.array` | downstream code indexes it in a way numpy arrays do not support |
| `inputFolder + "/" + file` → `os.path.join(...)` | path separators on Windows |
| bare `except:` → `except Exception` with `traceback.print_exc()` | the bare clause silently swallowed failures during debugging |

## Scripts added

| File | Purpose |
|---|---|
| `run_calibration.py` | Runs the method over the four known cells and the traces, writing `outputs/method1/` |
| `reproduce_compare.py` | Reproduces the PAN 2019 benchmark figure to check the patched code against the published accuracy |
| `evaluate_benchmark.py` | Scores predictions against the PAN ground-truth `.truth` files |
| `AGENTS.md` | Working notes kept alongside the implementation |

`reproduce_compare.py` and `evaluate_benchmark.py` need the PAN 2019 corpus, which is not
redistributed here — see `../../../data/README.md` for how to fetch it.
