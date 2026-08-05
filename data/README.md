# Data

Five corpora: four whose voice structure is known, and the reasoning traces whose structure
the study sets out to determine.

| Cell | Corpus | N | Producer | Task | Analysis input |
|---|---|---|---|---|---|
| ① | human monologue | 600 | human | Game of 24 | `00_core-2x2/human_monologue/all_samples/sample_600_human_think_aloud.jsonl` |
| ② | human debate | 500 | human | Wason card task | `00_core-2x2/human_debate/processed_human_debate.jsonl` |
| ③ | AI debate | 600 | 4× Qwen-2.5-7B | Game of 24 | `00_core-2x2/ai_debate/processed_ai_debate.jsonl` |
| ④ | AI monologue | 600 | Qwen-2.5-7B | Game of 24 | `00_core-2x2/ai_monologue/processed_prompted_ai_monologue.jsonl` |
| ⑤ | reasoning traces | 600 | DeepSeek-R1 | Game of 24 | `00_core-2x2/ai_reasoning/processed_native_reasoning_traces.jsonl` |

**A naming trap in cell ①.** `00_core-2x2/human_monologue/processed_sample_600_human_think_aloud.jsonl`
contains **5,143** documents, not 600 — it is the full processed think-aloud set and the
name is wrong. Every analysis in the paper reads the 600-document file listed in the table
above, under `all_samples/`. Both runners
(`scripts/run_method3_all_cells.py`, Method 2's `run_calibration.py`) point at that file,
and Method 2's calibration output contains exactly 600 cell-① documents. The 5,143-row file
is unused; it is kept because it is the input the 600 were sampled from.

## Provenance and licences

| Cell | Source | Licence | Redistributed here |
|---|---|---|---|
| ① | [think-aloud-llms](https://github.com/benpry/think-aloud-llms), Wurgaft et al. 2025 | MIT | yes, processed form |
| ② | [DeliData](https://huggingface.co/datasets/gkaradzhov/DeliData), Karadzhov et al. 2023 | CC-BY-4.0 | yes, processed form |
| ③④ | generated for this study with Qwen-2.5-7B | — | yes |
| ⑤ | generated for this study with DeepSeek-R1 | — | yes |

Cells ① and ② are redistributed in processed form under the terms above, with attribution
to their authors. The unmodified upstream sources are pinned as submodules under
`raw_datasets/` rather than copied:

```bash
git submodule update --init --recursive
```

## PAN 2019 — not included, and access-restricted

Method 1's benchmark reproduction needs the PAN 2019 style change detection corpus. It is
**not** in this repository, and it is not ours to redistribute: the dataset is
access-restricted on Zenodo and requires an approved request.

- PAN 2019 (needed for `reproduce_compare.py` / `evaluate_benchmark.py`):
  https://zenodo.org/records/5174825 — **restricted, request access**
- Task overview: Zangerle et al. 2019, https://downloads.webis.de/publications/papers/zangerle_2019.pdf

Once granted, unpack the training, validation and test archives into:

```
methods/1_style_change_detection/pan19_data/
├── pan19-style-change-detection-training-dataset-2019-01-17/
├── pan19-style-change-detection-validation-dataset-2019-01-17/
└── test/
```

Each directory holds paired `problem-*.txt` and `problem-*.truth` files. **Nothing in the
paper's reported results depends on this corpus** — it is used only to check the patched
Method 1 code against the published PAN 2019 accuracy. Method 1 failed the study's validity
check and does not judge the traces.

## Layout

| Path | Contents |
|---|---|
| `00_core-2x2/` | The analysis-ready cells. Each holds the processed file the methods read, and per-cell subfolders keep the raw generation output it came from. |
| `raw_datasets/` | Upstream human corpora as submodules, plus the Qwen and DeepSeek generation runs and their logs. |
| `problem_sets/` | The Game of 24 puzzle selection and the Wason items. |
| `associated_files/` | Vocabulary, character-frequency diagnostics, known data issues, sample listings. |
| `archive/` | Pre-speaker-fix versions of the two dialogue cells, kept so the fix can be audited. |
| `PREPROCESSING.md` | Every normalisation decision, why it was made, and what is still pending. Read this before comparing cells. |

## The speaker-label fix

Both dialogue cells originally carried speaker labels, which leak the number of voices
directly to a style-based method. They were removed, and all three methods were re-run on
the cleaned data (commit `77a29ae`, 2026-07-22). The pre-fix files are preserved in
`archive/` as `*.PRE_SPEAKERFIX_2026-07.jsonl` so the change can be checked.
