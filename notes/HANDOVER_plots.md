# Handover — Method 3 & placement figures

Context for the next agent picking up plot work. This covers every figure we
touched recently, how they're generated, the design decisions and user
preferences behind them, and the still-open questions. Read the "Open questions"
and "Conventions" sections first.

---

## 1. Where everything lives

**Scripts** (edit these to change figures; nothing is hand-drawn):

- `scripts/make_method3_figures.py` → `fig_m3_1_tag_distribution`,
  `fig_m3_3_completion_rate`, `fig_m3_4_jsd_scatter`
- `scripts/make_placement_figures.py` → `fig_m1_1_author_count`,
  `fig_m2_1_switch_probability`, `fig_m2_2_extrapolation`,
  `fig_x_1_placement`, `fig_x_2_placement_m3`

**Outputs:** each figure is written as both `.pdf` (used by the paper) and
`.png` (for quick viewing) into `paper/figures/`.

**Data sources (nothing is re-tagged / re-scored by the figure scripts):**

- Method 3 distributions & completion rates: a count-matrix NPZ cache, loaded via
  `place_cell5_method3_exploratory.py` (`P.load_counts()`). Rebuild the cache
  with `python scripts/place_cell5_method3_exploratory.py --build-cache` if the
  underlying tags ever change.
- Method 3 exploratory placement numbers:
  `outputs/placement/cell5_method3_exploratory.json`
- Method 1/2 confirmatory placement: `outputs/placement/cell5_placement.json`

**Regenerate figures:**

```
python3 scripts/make_method3_figures.py
python3 scripts/make_placement_figures.py
```

**Compile the paper** (from `paper/`): `latexmk -pdf main_v2.tex`. A full TeX
Live toolchain is available in the sandbox. After each compile we copy the PDF
to `paper/build/main_v2.pdf` (a stable location). Current state: **25 pages,
compiles clean, no undefined refs or citations.**

**Paper ↔ figure labels:** `fig:m3-unigram` (M3.1), `fig:m3-completion` (M3.3),
`fig:m3-jsd` (M3.4), `fig:placement` (X.1), `fig:placement-m3` (X.2). All
captions were updated to match the current designs.

---

## 2. Colour palette (IMPORTANT — the two scripts differ)

`make_method3_figures.py` uses a **new per-cell distinct, colour-blind-safe
(Okabe-Ito)** palette — every cell has its own colour:

| Cell | Meaning | Hex |
|---|---|---|
| ① human monologue | context | `#56B4E9` sky blue |
| ② human debate | context | `#CC79A7` reddish purple |
| ③ AI debate | dialogue pole | `#009E73` bluish green |
| ④ AI monologue | monologue pole | `#0072B2` blue |
| ⑤ AI reasoning | target (exploratory) | `#D55E00` vermillion |

`make_placement_figures.py` still uses the **older** scheme: poles ③/④ and
target ⑤ carry the same three colours as above, **but context cells ①/② are
GREY (`#8c8c8c`)**. This is deliberate there (grey so context can't be mistaken
for a pole), but it means **cells ①/② are coloured in the M3 figures and grey in
the placement figures.** If the next task is visual consistency, this is the
first thing to reconcile — decide one palette and apply to both scripts.

The palette avoids relying on a red/green contrast (user explicitly asked to
keep red/green colour-blind readers in mind).

---

## 3. Figure-by-figure state & the decisions behind each

### Fig M3.1 — dialogue-act tag distribution (`fig:m3-unigram`)
- **Now:** five **stacked** panels, ① top → ⑤ bottom, each in its own colour.
  All share one x-axis; **the tag order is set by cell ⑤'s shares, descending**
  (so `inform` is leftmost). Panels are flat/wide.
- **The `inform` clip:** `inform` dwarfs everything, so the y-axis is zoomed to
  just above the tallest *non-inform* bar (`CAP = non_inform_max + 0.02`). Only
  the `inform` bar exceeds the axis; it's drawn to the cap with a **break mark
  (two white slashes) and its true value printed above** (0.66/0.45/0.66/0.74/
  0.84). **Only `inform` gets this treatment** — user was explicit that clipping
  multiple bars (an earlier version also clipped `suggest`) was confusing.
- **User preferences captured:** separate stacked distributions (not one grouped
  plot); distinct colours (no duplicate greys); cell ⑤ drives the x-order; only
  `inform` clipped; title parenthetical "(tags ordered by cell ⑤'s share)"
  **removed**; exploratory footer **removed**.

### Fig M3.3 — adjacency-pair completion rate (`fig:m3-completion`)
- Box + jittered strip per cell, cell mean as a diamond, mean value annotated.
- **Title:** "Adjacency-pair direct completion rate (e.g. question–answer), by
  cell". The old "signal c, primary" wording is gone.
- **FPP-absent share annotation removed** (user: not interesting). Mean kept.
- New palette; exploratory footer removed; "cell mean" legend moved to
  `bbox_to_anchor=(0.62, 0.72)` so it stops colliding with cell ⑤'s label.

### Fig M3.4 — distributional placement / JSD scatter (`fig:m3-jsd`)
- Two panels: **"Tag frequency (unigram)"** and **"Tag transition (bigram)"**
  (renamed from the opaque "signal a/b" — user didn't know what those meant).
- Each dot is **labelled with its cell name** ("① human mono", "⑤ AI reasoning",
  etc.), not just the number. `lab_off` dict nudges the ⑤ and ① labels apart
  because those two points nearly coincide.
- New palette; footer removed.
- **⚠ OPEN QUESTION (unresolved):** the user questioned whether we need *both*
  distributional signals, since unigram and bigram look very similar and both
  return "no clear margin". I (previous agent) **kept both** — reasoning: they're
  pre-registered in the frozen spec, and the fact that both independently come
  back inconclusive is a more robust statement than one alone. **If dropping
  one, the unigram is the redundant one** (its tag distribution is already shown
  in M3.1). This is still open — confirm with the user.

### Fig X.1 — cross-method placement, confirmatory (`fig:placement`)
- Lives in the confirmatory *Cross-method summary* section. **M1 and M2 only** —
  Method 3 is excluded because it failed its reliability gate.
- Two rows on a monologue↔dialogue axis normalised so ④ = 0, ③ = 1. Each method's
  cell-⑤ position (filled diamond), its no-clear-margin band (shaded), poles,
  and grey context cells.
- **Fixed the naming complaint:** the "Fig X.1" text was baked into the image
  title while LaTeX numbers it "Figure 9". I **removed the baked-in "Fig X.1 "
  prefix** so LaTeX's number is the only one. Title now reads "Cell ⑤ placement.
  SPLIT: …".

### Fig X.2 — placement INCLUDING Method 3, exploratory (`fig:placement-m3`) — NEW
- The figure the user just asked for. Same axis as X.1 with a **third row for
  Method 3** below a dashed confirmatory/exploratory divider.
- Method 3's placement uses its **primary completion signal**; cell ⑤ lands at
  **≈1.47 — past the dialogue pole ③, i.e. on the same side as Method 2.**
- Marked exploratory: **hollow diamond**, "(exploratory, post-hoc)" tag, italic
  row label, dashed divider, legend entry distinguishing filled (confirmatory)
  vs hollow (exploratory) markers.
- **Two modelling choices in this row (both noted in the caption):**
  1. Only the completion signal is plotted. The two distributional signals
     return "no clear margin", so they'd just be noise on this axis (they're
     covered in Table `tab:m3-exploratory` and Fig M3.4).
  2. The **human context cells ①/② are off-scale and omitted** from the M3 row:
     humans complete far more adjacency pairs than the AI poles, so on the
     AI-pole-normalised axis they'd sit at ~4 and ~11 and blow out the scale.
     There's a small note on the figure saying so.
  3. The M3 band is the **post-hoc relative-gap margin** mapped to the axis as
     `[1/(2+m), 1/(2-m)]` = `[0.410, 0.641]` (m = 0.440), **not** a frozen
     bootstrap band like M1/M2. Hatched to distinguish it. Flagged as a
     judgment call — the derivation is principled but not identical to how the
     confirmatory bands were computed.
- Placement kept **separate** from X.1 on purpose (X.1 stays confirmatory-only,
  matching the pre-registered split). If the user later wants M3 folded directly
  into X.1 as a third row instead, that's a small change.

---

## 4. Key numbers (so plots and text stay consistent)

- Completion-rate means per cell: ① 0.096, ② 0.235, ③ 0.025, ④ 0.003, ⑤ 0.035.
  (These reflect the **0-scoring** rule for FPP-absent documents — a doc with no
  first-pair-part scores 0, not "excluded". This was reversed back to 0-scoring
  in both the spec and the paper; only cell ① had any FPP-absent docs.)
- Reliability: unweighted Cohen's κ = **0.5425** (95% CI [0.4788, 0.6038]),
  n = 503, gate ≥ 0.70 → **FAIL** (the registered result). Raw agreement =
  **0.742** (373/503). Tree-weighted Krippendorff's α = **0.6188**. (The CAMS-9
  functional-family κ was dropped from the writeup; only α + raw agreement are
  reported now.)
- Method 3 exploratory placement (per signal): completion r = 0.681 vs m = 0.440
  → dialogue-leaning; unigram r = 0.072 → no clear margin; bigram r = 0.005 →
  no clear margin.
- Confirmatory split: M1 monologue-leaning (⑤ axis 0.371, r = 0.410, m = 0.361);
  M2 dialogue-leaning (⑤ axis 1.447, r = 0.737, m = 0.112).

---

## 5. Cross-cutting conventions

- **Exploratory footers removed** from all M3 figures (user: the "Method 3
  failed its gate" note belongs in the text, not stamped on each figure). The
  exploratory status is instead carried by markers/labels/captions.
- **Baked-in figure-number prefixes:** the M3 and M1/M2 figures **still have
  "Fig M3.1", "Fig M1.1", etc. baked into their image titles**, which conflicts
  with LaTeX's auto-numbering (same issue the user flagged on X.1). Only the two
  placement figures (X.1, X.2) have had the prefix removed. **A likely next task
  is to strip the baked-in "Fig N" prefixes from all figures** for consistency —
  the user dislikes the double-numbering.
- Every figure writes both `.pdf` and `.png`; the paper uses the `.pdf`.

---

## 6. Open items / housekeeping (not plot-specific)

- **M3.4 two-signal question** — unresolved (see §3). Highest-priority open call.
- **git `.lock` files** block commits: `.git/HEAD.lock`,
  `.git/packed-refs.lock`, `.git/refs/heads/main.lock`,
  `.git/refs/heads/_probe_delete_me.lock`. The sandbox mount can't delete them;
  the user must remove them manually.
- `.gitignore` was created (LaTeX aux/log clutter, `__pycache__`, `paper/build/`).
- Still-`\todo` in the paper: the Discussion section and a few deeper skeletons
  (methods pre-reg skeleton, appendix data-check notes) — untouched, out of the
  recent scope.

---

## 7. Judgment calls made by the previous agent (verify with user if unsure)

1. Kept **both** distributional signals in M3.4 (could drop unigram).
2. M3 band in X.2 derived as post-hoc relative-gap `[1/(2+m), 1/(2-m)]`.
3. Bib entry for the "Stop Anthropomorphizing Intermediate Tokens" paper uses
   "Kambhampati, Subbarao and others" (et al. shorthand; full 9-author list not
   filled in).
4. Abstract's validation cross-ref points to `Section~\ref{sec:grid}`.
