# Local changes to the nath19 implementation

Method 1 runs the PAN 2019 system by Nath, pinned as a submodule at `../implementation`
(upstream: https://github.com/pan-webis-de/nath19, commit `ede16f8`). The changes needed to
run it are kept here rather than in the submodule.

## Applying

```bash
git submodule update --init methods/1_style_change_detection/implementation
cd methods/1_style_change_detection/implementation
git apply ../local_changes/upstream_modifications.patch
cp ../local_changes/run_calibration.py ../local_changes/reproduce_compare.py ../local_changes/evaluate_benchmark.py .
```

## Algorithmic change

In six places the clustering thresholds are renormalised:

```python
-  add_node_threshold = add_node_threshold / (cluster_size * avg_dist)
+  add_node_threshold = add_node_threshold / cluster_size
```

The same substitution is applied to `merge_cluster_threshold` for both cluster graphs in
`check_cg_merge_criteria` and `check_cg_merge_criteria2`.

Method 1's reported result was produced by the patched code, not by the original system as
submitted to PAN 2019.

## Compatibility and bug fixes

| Change | Reason |
|---|---|
| `_entry_in_array()` helper replaces `entry not in array` | `in` on a 2-D numpy array raises a truth-value-ambiguous error on current numpy |
| `cg1.node` to `cg1.nodes` | networkx removed the `.node` alias in 2.4 |
| `np.asarray([])` to `.reshape(0, 3)` | the empty placeholder needs a 3-column shape to compare against entries |
| `prune_clusters(cg_list)` to `cg_list = prune_clusters(cg_list)` | the return value was discarded |
| `win_len_arr` kept as a list rather than `np.array` | downstream code indexes it in a way numpy arrays do not support |
| `inputFolder + "/" + file` to `os.path.join(...)` | path separators on Windows |
| bare `except:` to `except Exception` with `traceback.print_exc()` | the bare clause swallowed failures |

## Scripts

| File | Purpose |
|---|---|
| `run_calibration.py` | Runs the method over the four known cells and the traces, writing `outputs/method1/` |
| `reproduce_compare.py` | Reproduces the PAN 2019 benchmark figure against the published accuracy |
| `evaluate_benchmark.py` | Scores predictions against the PAN ground-truth `.truth` files |
| `AGENTS.md` | Working notes kept alongside the implementation |

`reproduce_compare.py` and `evaluate_benchmark.py` need the PAN 2019 corpus, which is not
included; see [`../../../data/README.md`](../../../data/README.md).
