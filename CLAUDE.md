# CLAUDE.md: start here

Orientation for an agent that has no chat history with this project. Read this file first.
Then read [`docs/handoff/HANDOFF.md`](docs/handoff/HANDOFF.md) for the current state and the
open threads. [`docs/handoff/SESSION_HISTORY.md`](docs/handoff/SESSION_HISTORY.md) summarises
every earlier Claude session on the project, for when you need to know why something was decided.

## The project

Practical research by Oskar Engl (Johannes Kepler University Linz). The result is the paper
**"Monologue or Dialogue? Measuring Conversational Structure in the Reasoning Traces of Large
Language Models"**: [`paper/monologue_or_dialogue.tex`](paper/monologue_or_dialogue.tex), with
the compiled PDF next to it. The paper is the reference document. Where any note disagrees
with it, the paper is current.

Question: is a DeepSeek-R1 reasoning trace's textual shape closer to a monologue or to a
dialogue? It responds to Kim et al. 2026, "Reasoning models generate societies of thought".

Design: four corpora with known voice structure, plus the target.

| Cell | Folder in `data/` | Content | N |
|---|---|---|---|
| ① | `human_monologue` | human think-aloud, Game of 24 (Wurgaft et al. 2025) | 600 |
| ② | `human_debate` | human group deliberation, Wason task (DeliData) | 500 |
| ③ | `ai_debate` | four role-prompted Qwen-2.5-7B instances, Game of 24 | 600 |
| ④ | `ai_monologue` | one Qwen-2.5-7B, Game of 24 | 600 |
| ⑤ | `ai_reasoning` | target: DeepSeek-R1 native thinking traces, Game of 24 | 600 |

A method may judge cell ⑤ only if it first sorts ①-④ correctly into monologue and dialogue.

| Method | Folder in `methods/` | Signal | Validity check | Reading of ⑤ |
|---|---|---|---|---|
| 1 | `1_style_change_detection` | author count (Nath 2019, function-word clustering) | fails | bracketed, carries no weight |
| 2 | `2_stylometric_step_change` | adjacent-sentence style-switch probability (SSPC, Schmidt et al. 2025), length-matched | passes | more switches than AI debate |
| 3 | `3_dialogue_act_tagging` | adjacency-pair completion rate from CAMS tags (tagger: Tencent Hunyuan Hy3) | passes; tagger vs human κ = 0.54 | more pairs than AI debate, fewer than human |

## Where the files are

There are three copies of this work. Know which one you are in.

| Copy | Location | Notes |
|---|---|---|
| Public repo | `github.com/oskarengl/dialogic-multiplicity-in-reasoning-traces` | This repo. Built 2026-08-05 with rewritten history (PAN 2019 corpus and publisher PDFs removed), so hashes differ from the working repo. |
| Local clone of the public repo | `C:\bachelor research\dialogic-multiplicity-in-reasoning-traces\` | On the owner's Windows PC. |
| Working repo | `C:\bachelor research\.1 recent approach\` (GitHub `oskarengl/.1-recent-approach`, intended private) | Where all research ran. Holds the method virtualenvs (`venv\Scripts\python.exe`), the PAN corpora, the old layout (`data/00_core-2x2/`, `paper/main_v2.tex`, `STATUS.md`). |

A backup made before publication is at `C:\bachelor research\_publication_backup_2026-08-05\`.
Paths in old notes and chats refer to the working repo layout.

Never push working-repo history to the public remote: it contains the access-restricted PAN
2019 corpus and copyrighted PDFs.

The working notes were deleted from this repo in commit `02f670e` and can be read from history:

```bash
git show dfe64c7:notes/STATUS.md      # running decision log up to 2026-07-23, the most useful one
git show dfe64c7:notes/HANDOVER.md    # handover written 2026-07-23
git ls-tree -r --name-only dfe64c7 notes/
```

## Repository map

| Path | Contents |
|---|---|
| `paper/` | Paper `.tex` and `.pdf`, `figures/`, `make_fig_grid.py`, `make_fig_split.py` |
| `preregistration/methods.md` | Frozen method specification, condensed edition. Original: `git show 7747aef:methods.md` |
| `preregistration/METHOD_SELECTION.md` | Why the per-method gates were replaced by one validity check, and every post-freeze change |
| `data/` | One folder per cell, processed file on top, `unprocessed/` below. Schemas in `PREPROCESSING.md` |
| `methods/<n>_*/` | `RUN_METHOD<n>.md`, verification notes, `local_changes/` (patches to pinned upstream code), `sources/SOURCES.md` |
| `outputs/` | Frozen per-document results. `placement/` applies the superseded per-method gates (see `outputs/README.md`) |
| `scripts/` | Dataset construction, Method 3 runners, placement, figures |

Four directories are git submodules: `git submodule update --init --recursive`.

## Rules from earlier sessions

Keep these unless the owner changes them.

- Results in `outputs/` are frozen. Do not re-run, re-tag or overwrite them, and do not move
  pre-registered thresholds. Put new analyses in new files and label them exploratory.
- Method 3 tags whole documents. Do not chunk documents for it.
- Report every deviation openly, with its date and its reason.
- Ask before any compromise, method change, deletion, irreversible step, or push. The owner
  likes multiple-choice questions with a recommended option.
- Writing style for docs and paper:
  - plain, short, neutral sentences;
  - only facts that can be checked in the repo or the paper, with no added commentary or opinion;
  - no em dashes;
  - no "not A but B" constructions, and no defensive phrasing;
  - no arrows or symbols in running prose;
  - claims are about the text, not about minds inside the model.
- Edit files in the folder the owner looks at, not in a hidden worktree. Commit only when asked.
- Never commit the PAN 2019 corpus, literature PDFs, model checkpoints (`*.ckpt`) or API keys.
- Keep paths short, because of Windows path-length limits.
- The owner compiles LaTeX locally with pdflatex.
- The owner often dictates by voice, so messages can be long and contain transcription errors.
  Read for intent and answer briefly.

## Quick commands

```bash
git submodule update --init --recursive
python paper/make_fig_grid.py     # Figure 1
python paper/make_fig_split.py    # Figure 2, reads outputs/method2/*.jsonl
```

Running the methods needs Method 2's SSPC checkpoint (`model.ckpt`, 719 MB, from upstream),
API access to Tencent Hunyuan Hy3 for Method 3, and Qwen and DeepSeek access to generate cells
③④⑤. See `methods/*/RUN_METHOD*.md`.
