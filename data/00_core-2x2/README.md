# Canonical 2×2+1 datasets

This folder is the minimal analysis-ready layer for the five research cells. It intentionally contains only the processed files used by the methods; raw sources, historical variants, generation runs, diagnostics, and documentation live elsewhere under `data/`.

## Research cells

| Cell | Folder | Main file | Meaning |
|---|---|---|---|
| ① | `human_monologue/` | `processed_sample_600_human_think_aloud.jsonl` | Processed 600-row Game-of-24 think-aloud sample |
| ② | `human_debate/` | `processed_human_debate.jsonl` | Processed human Wason group dialogues |
| ③ | `ai_debate/` | `processed_ai_debate.jsonl` | Processed AI multi-agent debates |
| ④ | `ai_monologue/` | `processed_prompted_ai_monologue.jsonl` | Processed AI prompted-monologue condition |
| ⑤ | `ai_reasoning/` | `processed_native_reasoning_traces.jsonl` | Processed native DeepSeek-R1 reasoning traces |

## File naming

All files in this folder are `processed_...jsonl` analysis inputs. The 600-row human-monologue file is the development sample used by the current Method 3 runner.

## Where the other files went

- `data/raw/`: raw API outputs and original human-source repositories, grouped by research cell.
- `data/archive/`: regenerated/original variants, generation logs, historical samples, and diagnostics.
- `data/reference/`: unrelated benchmark datasets, puzzle sets, and the local IQ2 environment.

Nothing was deleted. The legacy empty folders left by the earlier layout are retained until explicitly approved for removal.
