# Feedback and forward plan
*Written 2026-07-15, based on `research_plan.md`, `methods.md`, `STATUS.md`, and the repo state.*

## Overall assessment

This is a well-designed project, and unusually so for practical work at bachelor level. Three things carry it:

1. **The 2×2+1 design.** Calibrating three methods on four ground-truth cells before letting any of them touch the target is the single best decision in the project. It converts "we ran some detectors on reasoning traces" into an actual argument.
2. **The pre-registration discipline.** Frozen methods spec, deviation log, an explicit firewall around cell ⑤'s summary statistics. Most published papers in this area don't do this.
3. **Honesty about confounds.** The task confound, the human-dialogue topic mismatch, the "no clear margin" verdict — all acknowledged in writing rather than papered over.

The main risk is no longer scientific, it's logistical: the design is done, the spec is done, and the remaining danger is spending more weeks polishing a plan that is already good enough to execute. **The correct move now is to stop specifying and start running.**

## What I'd flag (professor hat on)

**1. The pre-registration commit hasn't landed, and cell ⑤ tagging is 70%+ done.**
Your firewall argument (tagging is mechanical, only §3 summaries matter) is defensible, but it gets weaker every day the commit is delayed. Sign off the four §6 numbers *today* and commit. My recommendations below — take them and move on.

**2. Expect Method 1 to fail Step 1, and let it.**
Nath 2019 was built for StackExchange forum threads: long, natural-language paragraphs. Your documents are short, math-symbol-dense Game-of-24 transcripts. Top-50 function-word fingerprints may be degenerate on that text. If it fails the 80% gate, that is the design working — report the failure and move on. Do not retune it; the whole value of your setup is that you promised not to.

**3. One confound to write down, not fix: role prompts in AI dialogue.**
Your four debaters have distinct assigned roles (creative, critic, validator, alternative-seeker). If the methods separate ③ from ④, part of that could be role-induced style variation rather than multiplicity per se. Same-model debate mitigates model-level style, but not role-level. This belongs in the limitations section, one paragraph, done.

**4. Document length as a nuisance variable.**
Cells likely differ in document length, and Method 2's mean switch probability and Method 3's rates can drift with length. Report per-cell length distributions (one small table or figure). If lengths are wildly different, mention it; don't try to correct for it.

**5. Interpretation framing for the write-up.**
Whatever the verdict, the claim is about *textual surface structure*: "reasoning traces exhibit (or lack) the adjacency-pair and style-switching structure characteristic of multi-party dialogue." It is not a claim about the model literally containing multiple minds. Getting this framing right in the discussion is the difference between a strong thesis and an overclaiming one.

**6. Housekeeping (5 minutes, do it before it bites you).**
`data/00_core-2x2/` contains both `ai_monologue/` and a misspelled `ai-monolouge/` (which holds `prompted_ai_monologue.jsonl`). One canonical folder, delete or archive the other, and grep the scripts for which path they actually use. Also `outputs/method3/` has legacy folders (`ai_debate`, `ai_monologue_reasoning`, `human_reasoning_traces_small`) alongside the canonical `cellN_*` ones — archive the strays.

## Sign-off on the four open numbers (§6)

My recommendations, so you can commit today:

1. **Method 1 gate ≥ 80% per-cell TBC accuracy** — confirm as-is. Rationale is already written and sound.
2. **Comparison margin m = 0.10** — confirm as-is. 0.05 would over-call coin flips; 0.15 wastes signal.
3. **Reliability sample 50/cell, κ ≥ 0.70** — confirm as-is.
4. **Method 2 gate** — add a minimum effect size: **Cliff's delta ≥ 0.33** (conventional "medium") on ②③ vs ①④, in addition to direction. A directionally-correct-but-negligible separation shouldn't license a verdict on cell ⑤.

## Execution plan (target: results in ~1 week, draft in ~2)

**Day 0 (today)**
- Sign off §6, update `methods.md`, tick the STATUS.md checkboxes, commit `methods.md` + `STATUS.md` together. That commit is your timestamp.
- Fix the folder housekeeping.
- Let the Method 3 tagger finish (ETA is minutes).

**Days 1–2 — Step 1 (calibration cells only)**
- Run Method 1 (Nath, TBC+WMC, Matusita) on cells ①–④. Record per-cell accuracy vs the 80% gate.
- Run Method 2 (SSPC, raw sigmoid means) on cells ①–④. Compute direction + Cliff's delta.
- Hand-label the 200 utterances for κ. This is a few focused hours — do it before looking at any cell-⑤ summary.

**Day 3 — Step 1 verdicts, then Step 2**
- Write the Step-1 pass/fail table into STATUS.md. No rescues, no retuning.
- Run surviving methods on cell ⑤. Compute §3a–§3d for all five cells.

**Days 4–5 — Results**
- Produce exactly the figures in §5, nothing more. The figure list is already a complete results section — this is your biggest time-saver, don't expand it.
- Fill Table X. That table *is* the answer.

**Week 2 — Write-up**
- Methods section: `research_plan.md` + `methods.md` translate almost directly into thesis prose. Budget 2 days.
- Results: figures already exist; 1 day.
- Discussion: verdict pattern, the framing from point 6, limitations (role confound, length, human-dialogue task mismatch, out-of-domain inference for Method 2). 1–2 days.

**Do-not-do list (protects the timeline)**
- No new methods, no fourth signal, no fine-tuning Method 2 on your data.
- No fixing the human-monologue/human-dialogue task confound — it's documented, that's enough.
- No retuning any method that fails Step 1.
- No expanding the figure set beyond §5.
- No rewriting research_plan.md — it's done.

## Bottom line

The design is the thesis; the remaining work is execution and honest reporting. A split verdict or a failed method is a *result*, not a problem — your framework was built precisely so that every outcome is reportable. Commit the pre-registration today and run.
