# Handoff: current state and open threads

Written 2026-11-13, when the owner moved to a new Claude account without the old chat history.
Sources: this repository, the deleted working notes in git history (`git show dfe64c7:notes/...`),
and the transcripts of the Claude Code sessions listed in [`SESSION_HISTORY.md`](SESSION_HISTORY.md).

## State

The research is complete. The paper is final and public. The last work, on 2026-08-05 and
2026-08-06, was preparing this public repository and polishing its documentation. After
2026-08-06 there are no commits and no sessions on this project.

Final result, from the paper:

- Method 1 fails the validity check. It calls all 500 human debates and most AI debates single-author.
- Method 2 passes. The traces score +0.0109 above length-matched AI debates (95% CI
  [+0.0099, +0.0119]), and 85% of traces score above their matches.
- Method 3 passes. Completion rates are 0.235 and 0.095 for the human cells, 0.025 and 0.003
  for the AI cells, and 0.035 for the traces. Tagger vs human agreement is 74.2% on 503
  utterances, κ = 0.54 (0.62 tree-weighted), below the pre-registered 0.70.

## How the framing changed

Two framings of the result exist. Older files and chats use the first one.

1. **Pre-registered per-method gates** (computed 2026-07-22). Method 1 and Method 2 passed.
   Method 3 failed its κ ≥ 0.70 gate. The placement of cell ⑤ was a SPLIT: Method 1
   monologue-leaning, Method 2 dialogue-leaning. On 2026-07-23 Method 3's reading of ⑤ was
   added as a separate exploratory analysis with post-hoc margins. Files:
   `outputs/placement/cell5_placement.txt`, `outputs/placement/cell5_method3_exploratory.*`,
   `scripts/place_cell5_method3_exploratory.py`.
2. **One validity check for all three methods** (final paper). A method passes if it separates
   monologue from dialogue for both the human and the AI cells. Method 1 fails, Methods 2 and 3
   pass. This change was made after the gate results were known. The paper states this in §3,
   and `preregistration/METHOD_SELECTION.md` records it.

No available transcript covers the period from 2026-07-23 to 2026-08-05, when the second framing
and the final paper (`monologue_or_dialogue_final_v5`) were written. That work may have happened
in claude.ai chats or in sessions that are no longer listed. The drafts from that period are in
history: `git ls-tree -r --name-only dfe64c7 notes/drafts/`.

## Open threads

Each item says where it came from. None of them is required for the paper as published.

### Public repository

1. **Check that `oskarengl/.1-recent-approach` on GitHub is private.** It contains copyrighted
   PDFs and the access-restricted PAN 2019 corpus. A session on 2026-08-05 asked three times
   whether it was private and got no answer.
2. **The working repo may hold unpushed commits.** In the 2026-08-05 session, an M3 labelling
   commit had not been pushed to `.1-recent-approach`, and the session suggested
   `git push origin main` there. Stale `.git/*.lock` files had blocked commits in July
   (`git show dfe64c7:notes/HANDOVER.md` lists them).
3. **Compile check.** The 2026-08-05 session did not run pdflatex on
   `paper/monologue_or_dialogue.tex` after the figure paths changed. The committed PDF renders.
4. **Stale cell-① number in three files.** After the decision on 2026-07-23 to score documents
   without a first pair part as 0, the cell-① completion rate became 0.0955, and the paper uses
   0.095. These still print 0.0998:
   - `methods/3_dialogue_act_tagging/RUN_METHOD3.md:124`
   - `methods/3_dialogue_act_tagging/M3_internal_verification.md:38`
   - `outputs/placement/cell5_method3_exploratory.txt` (a frozen output, so leave it and add a note instead)
5. **References to deleted files.** `RUN_METHOD2.md`, `RUN_METHOD3.md` and two Method 2 scripts
   point to `STATUS.md`. Several `SOURCES.md` files point to `research_plan.md`. Both exist only
   in history (`git show dfe64c7:notes/STATUS.md`, `git show dfe64c7:notes/research_plan.md`).
6. **Character filtering.** `data/PREPROCESSING.md` §1 records a decision to replace disallowed
   characters with a space. The implementation deletes them, and the processed files were built
   that way. The item is marked pending in that file.

### Future work named in the paper (§7)

7. Add a cell in which one producer composes a whole exchange in a single pass, for example one
   model asked to write a four-way debate in one output.
8. Generate both AI anchors from the target model itself (a monologue condition and a
   role-prompted debate condition) to remove the change of base model.
9. A recurrence test for Method 2: stable voices taking turns should bring the same styles back
   across a document. Sentence-level style embeddings could replace Method 1's function-word
   clustering for this.
10. Re-tag Method 3 with a different model to measure label stability across taggers.
    Adjudicated double annotation was also named as a stronger check of the labels.

### Smaller items from earlier sessions

11. Optional Method 2 robustness rerun with a period-or-newline splitter for the 85 documents
    that Punkt reads as one sentence. It was offered on 2026-07-17 and declined; it would be post-hoc.
12. Fig M3.2 (transition heatmaps) was left as future work on 2026-07-23.
13. A request to rewrite `research_plan.md` from scratch in a minimal style (2026-07-15) was
    never carried out. The paper replaced the plan as the reference document.

### Early exploratory work outside this repo

These threads came before the final design and stopped. Their files are on the owner's PC.

14. A DistilBERT single-vs-multi-author classifier, replicated from a PAN-21 paper (validation
    accuracy 82.8%, macro F1 0.767). It never ran on traces, because 81% of traces exceed 512
    tokens. The open question was how to handle that: truncate, or chunk and then aggregate with
    an "any multi-author chunk" rule or a majority vote.
    Folder: `C:\bachelor research\BERT Multiauthor classification\`.
15. Speech-graph (graph-of-words) analysis after Mota et al. 2014, on one trace per difficulty
    bin. The full 14-attribute run over all 1,000 traces and a 30-word moving-window version
    were offered and not done. Folder: `C:\bachelor research\Graph of word analysis\`.
16. A pronoun trajectory plot ("we/us/our" vs "I"), to be redone with a 100-word sliding
    window. The earlier code was not found.
17. Literature mining: `C:\bachelor research\Findings.md` (27 papers, findings mapped to
    methods), `C:\bachelor research\Methods.md` (about 18 candidate methods),
    `C:\bachelor research\Datasets.md`, and a dataset dashboard in `C:\bachelor research\methods\`.

## Starting a new session

- Read `CLAUDE.md`, then this file. Ask the owner which thread to pick up.
- For background on a decision, search `git show dfe64c7:notes/STATUS.md` first, then
  `SESSION_HISTORY.md`.
- Claude Code keeps auto-memory files per project folder on the local machine, under
  `%USERPROFILE%\.claude\projects\`. Old sessions saved style rules there, for example a
  `user-writing-style-no-invented-commentary.md` memory in the folder for
  `C:\bachelor research\.1 recent approach`. If Claude Code runs on the same PC, those files may
  still be present. Their content is repeated in the rules section of `CLAUDE.md`.
