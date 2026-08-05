# Method 1 — Internal verification (PAN19 source reproduction)

**Date:** 2026-07-17  
**Pre-registration commit:** `fba456b`  
**Location:** `methods/1_style_change_detection/implementation/`  
**Script:** `reproduce_compare.py`

## What this checks

Before trusting Nath's implementation on our own 2×2 cells, we run the frozen TBC configuration on the official PAN19 style-change validation split and compare against the published number.

## Frozen configuration

- Algorithm: TBC (threshold-based clustering) only; WMC dropped per Nath §5.
- `merge_threshold = 50`
- `add_node_threshold = 50`
- `prune = True`
- `number_of_terms = 50`
- `use_duplication_feature = True`
- Distance: both Manhattan and Matusita are reported, to show the paper-vs-code discrepancy.

## Command

```bash
cd methods/1_style_change_detection/implementation
./venv/Scripts/python.exe reproduce_compare.py
```

## Output

```
manhattan  n=1272 binary_acc=0.8349 (41s)
matusita   n=1272 binary_acc=0.8223 (28s)
```

## Interpretation

- **Manhattan 0.8349** matches the expected ~0.835 validation score (Nath 2019, Table 5; Zangerle 2019, Table 3 official ~0.848). This confirms our copy of the code reproduces the published result.
- **Matusita 0.8223** is the distance measure the paper text evaluates; it is slightly lower on this split but still near 0.82.
- For the 2×2 validation gate we use **Matusita**, matching the method as the paper describes it rather than the shipped `main.py` default.
