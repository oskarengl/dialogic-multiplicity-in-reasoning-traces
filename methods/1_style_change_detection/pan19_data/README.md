# PAN 2019 corpus

The PAN 2019 style change detection corpus is access-restricted and is not included here.

Request access at https://zenodo.org/records/5174825, then unpack the archives so this
directory contains:

```
pan19_data/
├── pan19-style-change-detection-training-dataset-2019-01-17/
├── pan19-style-change-detection-validation-dataset-2019-01-17/
└── test/
```

Each holds paired `problem-*.txt` and `problem-*.truth` files.

The corpus is used by `local_changes/reproduce_compare.py` and
`local_changes/evaluate_benchmark.py`, which check the patched implementation against the
published PAN 2019 accuracy. No number reported in the paper depends on it.

Contents are ignored by git; see the repository `.gitignore`.
