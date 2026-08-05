# Method 1: Style Change Detection — Sources

> The PDFs referenced below by filename are not included in this repository.
> Each entry carries a link or full citation.

## Papers

| File | What it is |
|---|---|
| `zangerle_2019.pdf` | PAN 2019 task overview, dataset description, results table |
| `nath_2019.pdf` | Nath's TBC/WMC method paper, algorithm details, per-split accuracy |

**zangerle_2019.pdf** — https://downloads.webis.de/publications/papers/zangerle_2019.pdf  
**nath_2019.pdf** — https://downloads.webis.de/pan/publications/papers/nath_2019.pdf

## Implementation

| Path | What it is |
|---|---|
| `implementation/` | Cloned from https://github.com/pan-webis-de/nath19 |
| `implementation/evaluate_benchmark.py` | Benchmark evaluator (PAN data only, not project cells) |
| `benchmark_data/` | External PAN benchmark data for validation |

## Key results (PAN 2019, binary single vs multi-author)

| Participant | Accuracy | OCI | Rank | Runtime |
|---|---|---|---|---|
| Nath | 0.848 | 0.865 | 0.491 | 00:02:23 |
| Zuo et al. | 0.604 | 0.809 | 0.398 | 00:25:50 |
| BASELINE-RND | 0.600 | 0.856 | 0.372 | - |
| BASELINE-C99 | 0.582 | 0.882 | 0.350 | 00:00:30 |

**Source:** https://downloads.webis.de/publications/papers/zangerle_2019.pdf (Table 3)

Nath TBC per-split (duplicate-sentence feature enabled):

| Split | TBC accuracy |
|---|---|
| Validation | 0.83 |
| Test (TIRA) | 0.85 |

**Source:** https://downloads.webis.de/pan/publications/papers/nath_2019.pdf (Table 5)

## Benchmark data

- **PAN 2019 (target):** https://zenodo.org/records/5174825 — restricted, request access
- **PAN 2018 (public smoke test):** https://doi.org/10.5281/zenodo.3746040 — downloaded to `benchmark_data/pan18/`

See `benchmark_data/README.md` for download and evaluation instructions.
