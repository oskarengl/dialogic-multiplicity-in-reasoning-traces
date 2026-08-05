# Handover — Method 3 exploratory placement + writeup (2026-07-23)

Paste-ready context for the next agent. Read `STATUS.md` (authoritative provenance log — the last
entry is dated 2026-07-22 "later" and covers the target run) and `methods.md` (frozen
pre-registration; §3e is the M3 gate, §3d the placement-margin procedure, §4 the two-method
verdict rule) alongside this.

## What this project is

Bachelor practical research. A **2×2 corpus** (human/AI × monologue/dialogue) *validates* three
text-analysis methods, which then place a fifth held-out target cell **⑤ `ai_reasoning`**
(DeepSeek-R1 traces on Game of 24) on a monologue↔dialogue axis.

| Cell | Name | Role |
|---|---|---|
| ① | human_monologue | validation |
| ② | human_debate | validation |
| ③ | ai_debate | **dialogue anchor** |
| ④ | ai_monologue | **monologue anchor** |
| ⑤ | ai_reasoning | **TARGET** |

## The confirmatory result is DONE and frozen — do not relitigate

The target run executed on 2026-07-22. Cell ⑤ is placed by **Methods 1 and 2**; **Method 3 failed
its §3e reliability gate (κ = 0.5425 < 0.70) and takes no part in the confirmatory placement.**

| Method | Gate | cell-⑤ verdict | detail |
|---|---|---|---|
| **M1** style-change | balanced acc 0.6088, PASS | **monologue-leaning** | r = 0.410, m = 0.3615, bootstrap stability 70.7%, axis 0.371 |
| **M2** stylometric step-change | δ = 0.6211, PASS | **dialogue-leaning** | r = 0.737, m = 0.1117, stability 100%, axis 1.447 (**past pole ③**) |
| **M3** dialogue-act | κ = 0.5425, **FAIL** | excluded (confirmatory) | — |

**Pattern: SPLIT** (reported, not voted, per §4). Two pre-registered caveats, both already written
into the paper: M1 is a conservative detector (its monologue call ≈ "no document-level authorship
signal"); M2's monologue distance is an **extrapolation** (64% of cell ⑤ is longer than pole ④'s
observed max — see `paper/figures/fig_m2_2_extrapolation.pdf`).

Already in `paper/main_v2.tex`: Table M1 target row (mean count 1.32, 26.3% multi), Table M2 target
row (mean lean 0.0433), Table X both verdicts, all four placement figures wired in with captions,
abstract verdict sentence, intro (iii), the M1 conservative-detector paragraph, the M2
85-excluded-docs note, and the Discussion "interpretation of the observed pattern". Outputs:
`outputs/placement/cell5_placement.{txt,json}`. The whole run is logged in `STATUS.md`.

---

## YOUR TASK — Method 3, as an explicitly exploratory analysis

The user wants M3 reported despite its failed validation, **clearly and honestly marked as not
validated**. Decisions already made with the user (do not relitigate):

- **M3's cell-⑤ reading is EXPLORATORY.** It failed Step 1, so by the pre-registration its reading
  is not confirmatory. Report it anyway, in a way that keeps its non-validated status unmissable.
- **STRUCTURE: a separate, clearly-titled exploratory section.** `§Method 3` in Results keeps the
  failed-validation report and the per-cell completion rates. M3's cell-⑤ *placement* lives in its
  own section (title it as exploratory, e.g. "Exploratory: Method 3's reading of cell ⑤"). **Table X
  and Fig X.1 stay M1/M2 only.**
- **It is standalone, not a tie-breaker.** We decided to compute M3's cell-⑤ reading after the
  M1/M2 split was known; the prose must present it as descriptive and must never resolve the split.
- **Writing style (the user is firm on this — see `[[user-writing-style-no-defensive-negation]]`):**
  state plainly what happened and what was done. Do **not** use "not A but B" / "we are not
  cheating" defensive-negation constructions. Do not claim or imply validation.

### Steps

**1. Fill Table M3 per-cell completion rates ①–④ (the last 4 red `\resultnum`, lines ~887–890).**
Calibration-only, no firewall question. M3's report already prints them:
```
cd "C:\bachelor research\.1 recent approach\methods\3_dialogue_act_tagging\implementation"
python run_calibration.py          # prints, per cell: mean_rate and FPP-absent share
```
`run_calibration.py` → `report()` is fixed to cells {1,2,3,4}. Uses `signals.py` (numpy only, no
LLM). Table columns are "Completion rate mean" and "FPP-absent share".

**2. Cell-⑤ M3 exploratory placement.** All tags already exist (do **not** re-tag): counts are
①600 ②500 ③591 ④597 ⑤597 (the 9 missing ai_debate docs are in
`outputs/method3/cell3_excluded_docs.md`). `signals.py` computes every needed signal for any cell
including ⑤ (`CELL_DIRS`/`CELL_LABEL` include "5"): `load_cell_tags`, `cell_completion_rates`,
`cell_unigram`, `cell_bigram`, `cliffs_delta`. There is **no** M3 placement script yet
(`scripts/place_cell5.py` is M1/M2 only) — write a small exploratory one, following `methods.md`
§3d/§3a-c:
   - **Signal c (completion, primary):** cell statistic = mean completion rate; `d(X,pole) =
     |mean(X) − mean(pole)|`; place by comparing `d_mono` (to ④) vs `d_dia` (to ③).
   - **Signals a/b (unigram, bigram JSD):** `d(X,pole) = JSD(dist_X, dist_pole)`; place by
     comparing JSD-to-④ vs JSD-to-③ (Fig M3.4 is exactly this scatter).
   - **Per-signal margin:** the §3d noise-floor procedure (bootstrap ③/④, 95th percentile of the
     same-pole relative gap) — runs on ③/④ only. **No M3 margin was ever frozen** (M3 never reached
     placement), so this margin is computed now, after the fact. Say so plainly in the writeup: for
     M1/M2 the margin was frozen before the target existed; for M3 it is post-hoc, which is one more
     reason the M3 placement is exploratory.
   - Label every cell-⑤ M3 output "exploratory" in the artifact itself.

**3. M3 figures.** `paper/main_v2.tex` still has placeholders for Fig M3.1 (28-tag distribution),
M3.2 (transition heatmaps), M3.3 (completion-rate violins, the headline), M3.4 (JSD scatter).
Render the ones you use for the exploratory section (M3.1/M3.3/M3.4 are the natural set) and mark
any cell-⑤ element exploratory. `scripts/make_placement_figures.py` is the pattern to follow
(Okabe–Ito palette, system `python` has matplotlib; the method venvs do not).

**4. Prose.** Two places: (a) `§Method 3` in Results — the failed-validation writeup (there is a
`\todo` around line ~804 listing exactly what to cover: the Duran et al. weighted-measure argument,
the exploratory reanalyses, the `inform`/`suggest` concentration, and the κ limitation); (b) the new
exploratory section — M3's cell-⑤ placement with the honest reasoning below.

**5. Log in `STATUS.md`**, dated 2026-07-23, labeled exploratory, entered after the gate result.
Keep it out of all gate logic.

### The honest reasoning to write (same in both prose places)

State positively, no defensive negations:
- M3 failed the reliability gate: κ = 0.5425, 95% CI [0.4788, 0.6038], against a pre-registered
  bar of 0.70. It is not a validated method here.
- With 28 fine-grained CAMS labels, many semantically adjacent, exact-match agreement is inherently
  limited, and κ charges a full penalty for near-misses. The `inform`/`suggest` boundary alone
  accounts for 50 of 85 cross-family disagreements.
- Disagreements divide between the rater and the tagger, and on review many are defensible on both
  readings — this is Duran, Battle & Smith's (2022) own argument for a near-miss-aware measure.
  Those measures land higher on this data: family-collapse κ = 0.6074, tree-weighted α = 0.6188,
  both still under 0.70 and under Carletta's 0.67 floor.
- An informal read of the tags suggests they are largely reasonable. Present this as a qualitative
  impression, explicitly a weaker check than the gate, with a rigorous re-check (adjudicated
  double-annotation) named as future work. cell ④ is weakest under every measure (κ 0.387).

---

## Standing constraints / precedents (do not relitigate)

- **Always edit files in the real repo folder** `C:\bachelor research\.1 recent approach\`.
- **Never re-tag or touch cell ①④⑤ tags.** All five cells are already tagged.
- **The confirmatory verdict (M1/M2 split) is frozen.** M3 exploratory does not change it, and does
  not enter Table X or Fig X.1.
- **No pre-registered threshold moves** (κ₀ = 0.70, the M1/M2 margins, etc.).
- **Chunking documents for M3 is forbidden** — CAMS needs whole-document context.
- **Writing style:** honest, positive statements of what was done; no "not A but B" defensive
  negations; never imply M3 validated. See `[[user-writing-style-no-defensive-negation]]`.
- **No LaTeX toolchain on this machine** — the user compiles pdflatex to verify. Match existing
  `\includegraphics[width=...]{figures/...pdf}` syntax.

## Also still open (independent of M3)

- **Git.** Four stale `.lock` files under `.git` still block every commit; nothing is committed
  since `aecfd6f`. Clear them and commit when the user is ready:
  ```powershell
  cd "C:\bachelor research\.1 recent approach"
  del .git\HEAD.lock, .git\packed-refs.lock, .git\refs\heads\main.lock, .git\refs\heads\_probe_delete_me.lock
  git branch -D _probe_delete_me
  git add -A
  git commit -m "..."   # add -c user.name=Oskar -c user.email=oskar.engl@gmx.de if it complains
  ```
- **Compile check** — run pdflatex on `paper/main_v2.tex` to confirm the placement edits render.
- Non-result `\todo`s: the two citation requests the user flagged (the "satisfactory→link" one near
  the abstract; the *Stop Anthropomorphizing Intermediate Tokens* cite in the intro), and caption
  polish on the M3 figures.

## Key files

- `STATUS.md` — full provenance (**authoritative**; last entry 2026-07-22 "later").
- `methods.md` — frozen pre-registration; §3a–c signals, §3d margin, §3e M3 gate, §4 verdict rule.
- `paper/main_v2.tex` — 4 remaining red `\resultnum` (Table M3 completion rates ①–④, lines ~887–890).
- `methods/3_dialogue_act_tagging/implementation/signals.py` — all M3 signal computations (cell-5
  aware); `run_calibration.py` — the calibration report (prints per-cell completion rates).
- `outputs/method3/cell{1..5}_*/` — the per-document tags; `cell3_excluded_docs.md` — the 9 excluded.
- `outputs/method3/reliability/score_report.txt` — the registered κ; `disagreements.html` — viewer.
- `scripts/place_cell5.py`, `scripts/make_placement_figures.py` — M1/M2 placement + figures (patterns
  to mirror for M3).
- `outputs/placement/cell5_placement.{txt,json}` — the confirmatory M1/M2 result.
