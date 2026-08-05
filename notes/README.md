# Working notes

Process records from while the study was running. **None of this is part of the result.**
Where a note and the paper disagree, the paper is current and the note is a snapshot of
what was believed at the time.

They are kept because they show how decisions were reached, which is often what a reader
wants when a choice in the paper looks arbitrary.

| File | What it is |
|---|---|
| `STATUS.md` | The running log. Longest and most useful of these — decisions, dead ends, and why things were changed, in order. |
| `Findings.md` | Early exploratory findings, largely superseded. |
| `RECLEAN_RUNBOOK.md` | The procedure followed when the dialogue cells were re-cleaned after the speaker-label leak was found. |
| `RUN_CELL5.md` | Operational notes for generating the DeepSeek-R1 traces. |
| `HANDOVER.md`, `HANDOVER_plots.md` | Session handover notes; useful for the state of the plotting code. |
| `FEEDBACK_AND_FORWARD_PLAN.md` | Supervisor feedback and the plan that followed it. |
| `research_plan.md` | The original project plan, predating the frozen method specification. |
| `classification_methods_sources.md` | Literature survey done while choosing the three methods. |
| `add-to-paper-at-some-point.md` | Loose ends, some of which became Section 7. |
| `free-models.txt` | Which model APIs were free at the time, used when choosing generators. |
| `drafts/` | Superseded paper versions, `main_v2` through `final_v4`, plus the earlier `references.bib`. The current paper is `paper/monologue_or_dialogue.tex`. |

## Two notes are stale in a way worth naming

`STATUS.md` and `research_plan.md` both describe the per-method statistical gates as the
live framework, and `STATUS.md` records Method 3 as excluded on its κ shortfall. The paper
replaced that framework with a single validity check applied to all three methods; see
[`../preregistration/DEVIATIONS.md`](../preregistration/DEVIATIONS.md).

The frozen specification itself is not here — it is
[`../preregistration/methods.md`](../preregistration/methods.md), because it is a
commitment rather than a note.
