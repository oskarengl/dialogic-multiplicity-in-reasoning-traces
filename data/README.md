# Data

Four corpora whose voice structure is known, and the reasoning traces.

| Cell | Corpus | N | Producer | Task | Analysis input |
|---|---|---|---|---|---|
| ① | human monologue | 600 | human | Game of 24 | `human_monologue/human_think_aloud_600.jsonl` |
| ② | human debate | 500 | human | Wason card task | `human_debate/processed_human_debate.jsonl` |
| ③ | AI debate | 600 | 4× Qwen-2.5-7B | Game of 24 | `ai_debate/processed_ai_debate.jsonl` |
| ④ | AI monologue | 600 | Qwen-2.5-7B | Game of 24 | `ai_monologue/processed_prompted_ai_monologue.jsonl` |
| ⑤ | reasoning traces | 600 | DeepSeek-R1 | Game of 24 | `ai_reasoning/processed_native_reasoning_traces.jsonl` |

## Cell ① files

`human_monologue/` holds the 600-document analysis input at its top level. Three larger
files sit in `unprocessed/`, each containing the full 5,143-document think-aloud set at a
different processing stage: `human_think_aloud_full.jsonl`,
`processed_human_think_aloud_full.jsonl`, and `processed_think_aloud_full_variant.jsonl`.

Both runners read the 600-document file (`scripts/run_method3_all_cells.py:28`, Method 2's
`run_calibration.py:58`), and Method 2's calibration output contains 600 cell-① documents.

## Provenance and licences

| Cell | Source | Licence | Redistributed here |
|---|---|---|---|
| ① | [think-aloud-llms](https://github.com/benpry/think-aloud-llms), Wurgaft et al. 2025 | MIT | yes, processed form |
| ② | [DeliData](https://huggingface.co/datasets/gkaradzhov/DeliData), Karadzhov et al. 2023 | CC-BY-4.0 | yes, processed form |
| ③④ | generated for this study with Qwen-2.5-7B | CC-BY-4.0 | yes |
| ⑤ | generated for this study with DeepSeek-R1 | CC-BY-4.0 | yes |

The unmodified upstream sources are pinned as submodules under each cell's `unprocessed/` folder:

```bash
git submodule update --init --recursive
```

## PAN 2019

Method 1's benchmark reproduction uses the PAN 2019 style change detection corpus. It is not
included here. The dataset is access-restricted on Zenodo and requires an approved request.

- PAN 2019: https://zenodo.org/records/5174825 (restricted, request access)
- Task overview: Zangerle et al. 2019, https://downloads.webis.de/publications/papers/zangerle_2019.pdf

Once granted, unpack into:

```
methods/1_style_change_detection/pan19_data/
├── pan19-style-change-detection-training-dataset-2019-01-17/
├── pan19-style-change-detection-validation-dataset-2019-01-17/
└── test/
```

Each directory holds paired `problem-*.txt` and `problem-*.truth` files. The corpus is used
only by `reproduce_compare.py` and `evaluate_benchmark.py`, which check the patched Method 1
code against the published PAN 2019 accuracy. No reported result depends on it.

## Layout

| Path | Contents |
|---|---|
| `ai_debate/`, `ai_monologue/`, `ai_reasoning/`, `human_debate/`, `human_monologue/` | One folder per cell. The processed file the methods read sits at the top; `unprocessed/` holds the generation output, upstream sources, and intermediate variants. |
| `problem_sets/` | Game of 24 puzzle selection and Wason items |
| `diagnostics/` | Vocabulary, character-frequency analysis, known data issues, sample listings |
| `PREPROCESSING.md` | Normalisation decisions, per-cell schemas, and standardization rules |

## Speaker-label fix

Speaker labels were removed from both dialogue cells and all three methods were re-run on
the cleaned data (commit `77a29ae`, 2026-07-22). To see exactly what changed:

```bash
git show 77a29ae
```

`human_debate/unprocessed/` keeps both the labelled and unlabelled DeliData conversions.
