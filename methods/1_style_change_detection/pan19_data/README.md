# PAN 2019 corpus — fetch this yourself

This directory is intentionally empty. The PAN 2019 style change detection corpus is
access-restricted and is not redistributed here.

Request access at https://zenodo.org/records/5174825, then unpack the archives so this
directory contains:

```
pan19_data/
├── pan19-style-change-detection-training-dataset-2019-01-17/
├── pan19-style-change-detection-validation-dataset-2019-01-17/
└── test/
```

Each holds paired `problem-*.txt` (document) and `problem-*.truth` (ground truth) files.

Only `local_changes/reproduce_compare.py` and `local_changes/evaluate_benchmark.py` use
this data, to check the patched implementation against the published PAN 2019 accuracy.
No number reported in the paper depends on it.

The corpus contents are ignored by git — see the repository `.gitignore`.
