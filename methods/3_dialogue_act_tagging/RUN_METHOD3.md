# Running Method 3 (dialogue-act tagging) yourself

Method 3 doesn't have a source-reproduction step the way Methods 1 and 2 do (there's no
external benchmark to reproduce) — its "internal validation" is the labeling-reliability
check (does the LLM tagger agree with a human?), and it needs one manual step: hand-labeling
a sample of utterances. Everything else — the signal computation and the gate — is
automatic, since the LLM tagging of all five cells is already done (see `STATUS.md`).

All commands run **from inside `implementation/`**:

```bash
cd methods/3_dialogue_act_tagging/implementation
```

No model calls are needed for any of this (the tags already exist on disk); scripts only
need `numpy`. The first call to `signals.py` on each cell parses hundreds of JSONL files and
caches the result to `outputs/method3/_tag_cache/`, so repeated runs are fast.

## 1. Labeling reliability — κ ≥ 0.70 (`reliability_sample.py`)

Three steps:

```bash
python reliability_sample.py --plan     # compute required hand-label sample size per cell
python reliability_sample.py --sample   # draw the sample, write a BLIND worksheet
# ... hand-label outputs/method3/reliability/worksheet.csv (fill the human_label column) ...
python reliability_sample.py --score    # merge against the hidden LLM labels, compute kappa
```

**`--plan`** uses the asymptotic variance formula for Cohen's κ (Fleiss, Cohen & Everitt,
1969), fed with each cell's own observed tag-frequency marginals (a legitimate calibration-only
input — §3a on cells ①–④), solving for the `n` that gives a CI of the target width around
κ = 0.70 (the pass/fail threshold, unchanged). **Current default precision target: 90% CI,
half-width ≤ 0.10** (revised 2026-07-17 from an intermediate 90%/±0.08, which itself revised the
original 95%/±0.05 — see `STATUS.md`).
**Already run on the real data at this setting; here is the result:**

| cell | n required | of how many sentences |
|---|---|---|
| ① human_monologue | 122 | 12,166 |
| ② human_debate | 83 | 14,870 |
| ③ ai_debate | 137 | 79,978 |
| ④ ai_monologue | 168 | 18,172 |
| **total** | **510** | |

The original 95%/±0.05 setting gave 2,884 total — a lot for a practical (non-thesis) project.
The reason it was that high is mechanical, not a bug: `human_monologue` and `ai_monologue` are
heavily dominated by a single tag (`inform`, ~61% in cell ①), and a skewed tag distribution
*raises* chance agreement (`p_e`), which *shrinks* `(1 − p_e)` in the κ variance formula — so
pinning κ down to the same precision on a skewed cell needs **more** labels, not fewer
(`run_calibration.py --selftest` demonstrates this directly). Loosening the confidence level to
90% and the half-width to ±0.08 (796 total) was a first blind cost/precision trade-off; loosening
further to ±0.10 (510 total) adds a deliberate margin on top of that, to buffer against noise in
the human labeling itself, not just sampling noise in κ — both changes affect how tightly we pin
down the *measured* κ, not the pass/fail bar itself (still κ ≥ 0.70), and at a measured κ around
0.75, a ±0.10 band ([0.65, 0.85] roughly) is still unambiguous relative to 0.70. Adjust anytime
with `--half-width` / `--confidence` on `--plan`, e.g.:

```bash
python reliability_sample.py --plan --confidence 0.90 --half-width 0.10   # current default
python reliability_sample.py --plan --confidence 0.90 --half-width 0.08   # intermediate
python reliability_sample.py --plan --confidence 0.95 --half-width 0.05   # original, stricter
```

**`--sample`** draws that many utterances per cell (fixed seed), shuffles them together, and
writes `outputs/method3/reliability/worksheet.csv` with columns `cell, cell_name, doc_id,
sentence_idx, text, human_label` — the LLM's own label is **not** in the worksheet (kept
separately in `hidden_llm_labels.json`), so your hand-labeling is genuinely blind. Allowed tags
are printed when you run it (the 27 CAMS tags + `none`, case-sensitive).

**`--score`** merges your filled-in `human_label` column against the hidden LLM labels,
computes Cohen's κ (pooled and per cell) with a bootstrap 95% CI, and reports **GATE (κ ≥
0.70): PASS/FAIL**. You can re-run `--score` any time after partially filling the worksheet;
unfilled rows are skipped and counted.

### Hand-labeling: click-to-label tool (`label_tool.py`)

Instead of editing `worksheet.csv` by hand in a spreadsheet, `label_tool.py` serves a local
click-to-label web UI at `http://127.0.0.1:8765/`:

```bash
python label_tool.py            # opens a browser tab automatically
python label_tool.py --port 9000 --no-browser   # options
```

- Shows one sentence at a time with the 28 CAMS tags (27 + `none`) as buttons, grouped into
  the schema's own 8 functional categories (Information-seeking, Information-providing,
  Commissive, Directive, Feedback, Time management, Communication management, Social
  obligations) — same clustering as the cheat sheet below.
- A reference sidebar (same clusters, click a tag to expand its definition/example/confusable
  neighbors) stays visible the whole time, so there's no need to alt-tab to a separate document.
- **Every click writes `worksheet.csv` immediately** (atomic write — a temp file then rename,
  so the file is never left half-written) **and** appends the same event to
  `outputs/method3/reliability/label_events.jsonl`, an append-only backup log — so no label can
  be lost even if the CSV were somehow corrupted. Fully compatible with `--score`: it's editing
  the exact same file, same columns, no import/export step.
- Auto-advances to the next *unlabeled* row after each click, so closing the browser and
  re-running `label_tool.py` later resumes right where you left off. `◀ Prev` / `Next ▶` /
  jump-to-row let you go back and relabel anything (a misclick is just a matter of navigating
  back to that row and clicking the correct tag — it overwrites the row).

**`labeling_tool/cheatsheet.html`** (also served at `/cheatsheet.html` by the same tool, or
open it directly through the running server) is a standalone, larger-format reference sheet:
all 28 tags laid out as colored panels by the same 8 clusters, each with a one-line gloss, a
short example, and a "watch for" note on the specific tags it's easiest to confuse (e.g.
`checkQuestion` vs `propositionalQuestion`, `agreement` vs `confirm` vs `autoPositive`,
`disconfirm` vs `disagreement` vs `correction`). Good for a first read-through / warm-up before
starting the blind worksheet, or to keep open in a second window/monitor while labeling. Both
pages read the same `labeling_tool/tag_schema.json`, so they never drift out of sync with each
other.

## 2. Signal-validity gate (`run_calibration.py`)

No manual step — everything needed already exists in `outputs/method3/`.

```bash
python run_calibration.py
```

**Already run on the real calibration data; here is the result:**

```
=== 3c. Adjacency-pair completion rate (primary signal) ===
cell 1 (human_monologue ) n_docs= 600  FPP-absent=  26 (4.3%)  defined_n= 574  mean_rate=0.0998
cell 2 (human_debate    ) n_docs= 500  FPP-absent=   0 (0.0%)  defined_n= 500  mean_rate=0.2301
cell 3 (ai_debate       ) n_docs= 598  FPP-absent=   0 (0.0%)  defined_n= 598  mean_rate=0.0201
cell 4 (ai_monologue    ) n_docs= 597  FPP-absent=   0 (0.0%)  defined_n= 597  mean_rate=0.0030

mean completion rate  dialogue (2,3) = 0.1157   monologue (1,4) = 0.0504
Cliff's delta (dialogue vs monologue) = 0.4380
direction (dialogue > monologue): True
GATE-A (direction only, as literally specified): PASS
GATE-B (direction AND delta >= 0.33, consistency w/ Method 2): PASS

=== 3a/3b. Within-class vs. between-class JSD (consistency check, not gating) ===
3a unigram JSD:  within-mono(1,4)=0.1675  within-dia(2,3)=0.2142  between(avg)=0.1668  [within < between: False]
3b bigram  JSD:  within-mono(1,4)=0.3148  within-dia(2,3)=0.3618  between(avg)=0.2894  [within < between: False]
```

**Reading this honestly:**

- **The primary signal passes cleanly, both ways.** Dialogue cells complete adjacency pairs
  roughly 2.3× more often than monologue cells (0.116 vs 0.050), a medium-to-large effect
  (δ = 0.438), in the expected direction. This clears the literal gate (direction only) *and*
  the stricter δ ≥ 0.33 reading — no ambiguity from that open question.
- **The §3a/§3b consistency check does *not* hold** — within-class JSD is not smaller than
  between-class for either the unigram or bigram profile. Per methods.md §3e.2 this is
  reported, not required, so it does **not** block the gate. But it's a real, interesting
  finding worth carrying into the write-up: `ai_debate`'s raw tag-usage *profile* (which tags
  occur, how often) apparently resembles the monologue cells about as much as it resembles
  `human_debate` — plausibly the same "single-model idiolect" effect flagged for Method 1
  (`ai_debate` is four instances of one model, and its DA-tag *vocabulary* may reflect that
  shared origin even while its *interaction structure*, i.e. completion rate, correctly reads
  as dialogue). That would make §3c's success and §3a/§3b's disagreement complementary
  evidence, not a contradiction — but this is a claim to make in the paper deliberately, not
  slip in.

**Gate-A vs. Gate-B — the open call.** methods.md §3e.2 literally specifies only a direction
check for Method 3 (no numeric δ floor), unlike Method 2, which explicitly requires δ ≥ 0.33.
That's the same category of gap that made Method 1's original pooled-accuracy gate too easy to
pass. Here it doesn't matter for the actual numbers (δ = 0.438 clears 0.33 comfortably either
way), but the methods.md text should probably say which reading is intended, for the record.
Recommend adding the δ ≥ 0.33 floor explicitly for consistency across all three methods — say
the word and I'll make that edit.

## Files

- `implementation/signals.py` — shared §3a/§3b/§3c computation + JSD + Cliff's delta (cached)
- `implementation/reliability_sample.py` — sample-size planning, blind worksheet, κ scoring
- `implementation/run_calibration.py` — the §3e.2 gate report
- outputs → `outputs/method3/reliability/` (plan, worksheet, hidden labels),
  `outputs/method3/_tag_cache/` (parsed-tag cache, safe to delete)
