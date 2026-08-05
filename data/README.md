# Data

Four corpora whose voice structure is known, and the reasoning traces.

| Cell | Corpus | N | Producer | Task | Analysis input |
|---|---|---|---|---|---|
| ① | human monologue | 600 | human | Game of 24 | `00_core-2x2/human_monologue/all_samples/sample_600_human_think_aloud.jsonl` |
| ② | human debate | 500 | human | Wason card task | `00_core-2x2/human_debate/processed_human_debate.jsonl` |
| ③ | AI debate | 600 | 4× Qwen-2.5-7B | Game of 24 | `00_core-2x2/ai_debate/processed_ai_debate.jsonl` |
| ④ | AI monologue | 600 | Qwen-2.5-7B | Game of 24 | `00_core-2x2/ai_monologue/processed_prompted_ai_monologue.jsonl` |
| ⑤ | reasoning traces | 600 | DeepSeek-R1 | Game of 24 | `00_core-2x2/ai_reasoning/processed_native_reasoning_traces.jsonl` |

## Cell ① file naming

`00_core-2x2/human_monologue/processed_sample_600_human_think_aloud.jsonl` contains 5,143
documents despite `sample_600` in its name. It is the full processed think-aloud set.

The 600-document file listed in the table above is the one the analyses read. Both runners
point at it (`scripts/run_method3_all_cells.py:28`, Method 2's `run_calibration.py:58`), and
Method 2's calibration output contains 600 cell-① documents.

## Provenance and licences

| Cell | Source | Licence | Redistributed here |
|---|---|---|---|
| ① | [think-aloud-llms](https://github.com/benpry/think-aloud-llms), Wurgaft et al. 2025 | MIT | yes, processed form |
| ② | [DeliData](https://huggingface.co/datasets/gkaradzhov/DeliData), Karadzhov et al. 2023 | CC-BY-4.0 | yes, processed form |
| ③④ | generated for this study with Qwen-2.5-7B | CC-BY-4.0 | yes |
| ⑤ | generated for this study with DeepSeek-R1 | CC-BY-4.0 | yes |

The unmodified upstream sources are pinned as submodules under `raw_datasets/`:

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
| `00_core-2x2/` | The analysis-ready cells, with per-cell subfolders holding the raw generation output |
| `raw_datasets/` | Upstream human corpora as submodules, plus the Qwen and DeepSeek generation runs and logs |
| `problem_sets/` | Game of 24 puzzle selection and Wason items |
| `associated_files/` | Vocabulary, character-frequency diagnostics, known data issues, sample listings |
| `archive/` | Pre-speaker-fix versions of the two dialogue cells |
| `PREPROCESSING.md` | Normalisation decisions, their reasons, and what is still pending |

## Speaker-label fix

Speaker labels were removed from both dialogue cells and all three methods were re-run on
the cleaned data (commit `77a29ae`, 2026-07-22). The pre-fix files are in `archive/` as
`*.PRE_SPEAKERFIX_2026-07.jsonl`.
