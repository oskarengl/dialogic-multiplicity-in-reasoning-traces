# CLAUDE.md — start here

Orientation for an AI agent (or person) who has no chat history with this project. Read this
file first, then [`docs/handoff/HANDOFF.md`](docs/handoff/HANDOFF.md) for current state and
next steps, and [`docs/handoff/SESSION_HISTORY.md`](docs/handoff/SESSION_HISTORY.md) if you need
to know how and why a decision was made.

## What this project is

A finished-but-still-polishable research paper by Oskar Engl (bachelor-level practical research,
JKU Linz):

**"Monologue or Dialogue? Measuring Conversational Structure in the Reasoning Traces of Large
Language Models."** Paper: [`paper/monologue_or_dialogue.tex`](paper/monologue_or_dialogue.tex)
(compiled PDF next to it).

Question: is a DeepSeek-R1 reasoning trace's textual shape closer to a monologue or to a
dialogue? (Motivated by Kim et al. 2026, "Reasoning models generate societies of thought".)

Design: a 2×2 grid of corpora with known voice structure, plus the target.

| Cell | Folder (`data/…`) | What | N |
|---|---|---|---|
| ① | `human_monologue` | human think-aloud, Game of 24 (Wurgaft et al. 2025) | 600 |
| ② | `human_debate` | human group deliberation, Wason task (DeliData) | 500 |
| ③ | `ai_debate` | 4 role-prompted Qwen-2.5-7B instances debating Game of 24 | 600 |
| ④ | `ai_monologue` | one Qwen-2.5-7B solving Game of 24 | 600 |
| ⑤ | `ai_reasoning` | **target**: DeepSeek-R1 native thinking traces, Game of 24 | 600 |

Three methods must first sort ①–④ correctly into monologue vs dialogue ("validity check");
only those that pass may judge ⑤.

| Method | Folder (`methods/…`) | Signal | Check | Reading of ⑤ |
|---|---|---|---|---|
| 1 | `1_style_change_detection` | author count (Nath 2019, PAN function-word clustering) | **fails** (calls all human debates single-author) | bracketed, no weight |
| 2 | `2_stylometric_step_change` | adjacent-sentence style-switch probability (SSPC, Schmidt et al. 2025), length-matched | passes | more switching than AI debate |
| 3 | `3_dialogue_act_tagging` | adjacency-pair completion rate from CAMS tags (tagger: Tencent Hunyuan Hy3) | passes (labels κ = 0.54 vs human, below the pre-registered 0.70) | more pairs than AI debate, far fewer than humans |

Headline: traces sit on the dialogue side of the AI comparison, but well short of human
conversation; the text alone cannot tell several voices from one voice writing conversationally.

## Two repositories exist — know which one you are in

1. **This repo** — the public release, `github.com/oskarengl/dialogic-multiplicity-in-reasoning-traces`.
   Prepared 2026-08-05/06. History was rewritten (PAN 2019 corpus and publisher PDFs purged), so
   commit hashes differ from the working repo. Working notes (`notes/`) and old drafts were
   deleted in commit `02f670e` but are recoverable:
   `git show dfe64c7:notes/STATUS.md` (the running decision log, 615 lines — the most useful
   historical document), `git show dfe64c7:notes/HANDOVER.md`, `git ls-tree -r --name-only dfe64c7 notes/`.
2. **The working repo** on the owner's Windows PC: `C:\bachelor research\.1 recent approach\`
   (per the old handover notes). It has the method virtualenvs (`venv\Scripts\python.exe`), the
   PAN corpora, and older paths like `data/00_core-2x2/` and `paper/main_v2.tex`. Paths in old
   notes and chats refer to that layout, not this one.

If you are unsure which one the user means, ask. Do not push the working repo's history to the
public remote (it contains material that must not be redistributed — see below).

## Repository map

| Path | Contents |
|---|---|
| `paper/` | The paper (`.tex`, `.pdf`), `figures/`, and `make_fig_grid.py` / `make_fig_split.py` |
| `preregistration/methods.md` | Frozen method spec (condensed edition; original: `git show 7747aef:methods.md`) |
| `preregistration/METHOD_SELECTION.md` | Why the per-method gates were replaced by one validity check, and every post-freeze change |
| `data/` | One folder per cell; processed file at top, `unprocessed/` below. `PREPROCESSING.md` has schemas |
| `methods/<n>_*/` | `RUN_METHOD<n>.md`, `M<n>_internal_verification.md`, `local_changes/` (patches to pinned upstream code), `sources/SOURCES.md` |
| `outputs/` | Frozen per-document results; `placement/` uses the **superseded** per-method gates (see `outputs/README.md`) |
| `scripts/` | Dataset construction (`cell3_…`, `cell4_…`, `cell5_…`), Method 3 runners, placement, figures |

Four directories are git submodules (`git submodule update --init --recursive`).

## Rules that carry over from earlier work (do not relitigate without the owner)

- **Frozen results stay frozen.** Do not re-run, re-tag, or overwrite anything in `outputs/`, and
  do not move pre-registered thresholds. New analyses go in new files, labelled exploratory.
- **Never chunk documents for Method 3** — CAMS tagging needs whole-document context.
- **Report deviations openly.** The gate swap happened after results were known; the repo says so
  (`METHOD_SELECTION.md`, paper §3). Keep that honesty in anything new.
- **Writing style the owner is firm about:** plain, positive statements of what was done. No
  defensive "not A but B" / "we are not cheating" constructions. No overclaiming: claims are
  about the *text surface*, not about minds inside the model. Short sentences, no filler.
- **Documentation must be verifiable** from the repo or the paper (commit `11ab820` tightened docs
  to exactly that). Don't write claims you can't point to.
- **Never commit:** the PAN 2019 corpus (access-restricted), literature PDFs, model checkpoints
  (`*.ckpt` — Method 2's `model.ckpt` is 719 MB, fetched from upstream). `.gitignore` covers these.
- Keep paths short (Windows path-length limits bit before — commit `fa5b862`).
- LaTeX: the owner compiles with pdflatex locally; match existing `\includegraphics` style.

## Quick commands

```bash
git submodule update --init --recursive
python paper/make_fig_grid.py     # Figure 1
python paper/make_fig_split.py    # Figure 2 (reads outputs/method2/*.jsonl)
```

Running the methods themselves needs: Method 2's SSPC checkpoint, API access to Tencent Hunyuan
Hy3 (Method 3), Qwen/DeepSeek access (cell generation). See `methods/*/RUN_METHOD*.md`.

## Known documentation gaps

- `RUN_METHOD2.md`, `RUN_METHOD3.md`, and two Method 2 scripts refer to `STATUS.md`; it was
  removed from the public repo. Read it with `git show dfe64c7:notes/STATUS.md`.
- Several `SOURCES.md` files refer to `research_plan.md`: `git show b7f40d0:research_plan.md`
  (or `git show dfe64c7:notes/research_plan.md` for the last version).
- `outputs/placement/cell5_placement.txt` reports the old SPLIT verdict (M1 monologue-leaning,
  M2 dialogue-leaning, M3 excluded). The paper supersedes it; that file is kept as a record.
