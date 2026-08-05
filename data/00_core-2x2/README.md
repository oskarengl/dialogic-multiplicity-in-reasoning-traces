# Canonical 2×2+1 datasets

This folder is the minimal analysis-ready layer for the five research cells. It intentionally contains only the processed files used by the methods; raw sources, historical variants, generation runs, diagnostics, and documentation live elsewhere under `data/`.

## Research cells

| Cell | Folder | File the methods actually read | N | Meaning |
|---|---|---|---|---|
| ① | `human_monologue/` | `all_samples/sample_600_human_think_aloud.jsonl` | 600 | Game-of-24 think-aloud sample |
| ② | `human_debate/` | `processed_human_debate.jsonl` | 500 | Processed human Wason group dialogues |
| ③ | `ai_debate/` | `processed_ai_debate.jsonl` | 600 | Processed AI multi-agent debates |
| ④ | `ai_monologue/` | `processed_prompted_ai_monologue.jsonl` | 600 | Processed AI prompted-monologue condition |
| ⑤ | `ai_reasoning/` | `processed_native_reasoning_traces.jsonl` | 600 | Processed native DeepSeek-R1 reasoning traces |

## File naming

Cells ②–⑤ each read the `processed_*.jsonl` file at the top of their folder.

**Cell ① is the exception, and the name misleads.**
`human_monologue/processed_sample_600_human_think_aloud.jsonl` holds **5,143** documents
despite the `sample_600` in its name. It is the full processed think-aloud set. The
600-document sample the study actually uses is
`human_monologue/all_samples/sample_600_human_think_aloud.jsonl`.

Both runners point at the 600-document file (`scripts/run_method3_all_cells.py:28`, Method
2's `run_calibration.py:58`), and Method 2's calibration output contains exactly 600 cell-①
documents. The 5,143-row file is kept as the set the sample was drawn from, and is not read
by any analysis.

## Where the other files live

- `data/raw_datasets/`: upstream human corpora (submodules) and the Qwen/DeepSeek generation runs.
- `data/archive/`: pre-speaker-fix versions of the two dialogue cells.
- `data/problem_sets/`: Game of 24 selection and Wason items.
- `data/associated_files/`: vocabulary, character-frequency diagnostics, known data issues.

See [`../README.md`](../README.md) for provenance, licences, and the PAN 2019 fetch
instructions.
