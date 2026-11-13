# Session history

Summaries of the earlier Claude Code sessions on this project, oldest first. They were written
on 2026-11-13 from the session transcripts, for an agent that cannot read those chats. All of
these sessions ran on the owner's Windows PC, and every path below is on that machine.
Sessions on unrelated topics are left out.

The decision log `git show dfe64c7:notes/STATUS.md` covers 2026-07-15 to 2026-07-23 in more
detail than this file.

## Phase 1: finding a method (2026-05-30 to 2026-06-09)

**2026-05-30. Replicate a PAN-21 multi-author classifier.**
- Goal: rebuild the single-vs-multi-author classifier from a PAN-21 style-change paper, then
  apply it to reasoning traces. The owner said: "Don't make any compromises without asking me before."
- Choices: single DistilBERT on raw text, with the paper's hyperparameters (lr 1e-5, 5 epochs,
  effective batch 32, 512 tokens).
  - The data came from a GitHub mirror, because Zenodo was gated.
  - Training used the train split and evaluation the validation split, since the test labels
    are not public.
- Result on validation: accuracy 82.8%, macro F1 0.767. Accuracy alone overstates the model,
  because 75% of documents are multi-author.
- Open: 81% of the 1,000 test traces exceed 512 tokens. The session ended on the question of how
  to handle that. Folder: `C:\bachelor research\BERT Multiauthor classification\`.

**2026-06-01. Graph-of-words visualisation.**
- Speech graphs after Mota et al. 2014: words are nodes and consecutive words form edges. One
  trace was drawn per difficulty bin.
- The owner dropped LCC and LSC ("everyone is gonna have connections somehow"), keeping N, E and ATD.
- Folder: `C:\bachelor research\Graph of word analysis\`.

**2026-06-02 to 06-03. How to detect multiple personas in traces.** This session set the design.
- The owner doubts the society-of-thought claim and suspects traces are closer to inner
  monologue with self-correction.
- The question was reframed as "closer to a human debate or to inner monologue?".
- The 2×2 anchor design (human/AI × single/multi) was proposed here.
- The AI debate anchor uses one model with different persona prompts, because different model
  brands would confound style with ability.
- Recurrence of voices (A, then B, then A again) was named as the key discriminator.
- The owner rejected a causal ablation test and asked for no timelines.

**2026-06-05. Pronoun rolling window.** The owner asked for a 100-word sliding window over a
"we/us/our" vs "I" plot. The earlier code was not found and nothing was produced.

**2026-06-09. Literature mining and dataset choice.**
- Mined 27 papers in `C:\bachelor research\methods\papers\` and mapped each finding, with a
  verbatim quote and its location, to the candidate methods in `C:\bachelor research\Methods.md`.
  Output: `C:\bachelor research\Findings.md`.
- The owner then chose the dataset plan, written to `C:\bachelor research\Datasets.md`:
  - a shared puzzle domain (Game of 24, Wason);
  - DeliData for human debate;
  - separate persona-prompted instances for the AI debate.
- The session hit a usage limit before finishing.

## Phase 2: data (2026-06-10 to 2026-06-16)

**2026-06-10. Human monologue data.**
- Cloned `benpry/think-aloud-llms` (Game of 24 think-aloud), which became cell ①.
- The owner widened the search to written step-by-step data. GSM8K, AQuA-RAT, MATH, ECQA and
  StrategyQA were added but not used in the final design.
- CMU DataShop think-aloud sets need an access request.

**2026-06-11. Dataset dashboard.** 14 candidate datasets were compared by domain, size and
length. Files: `dataset_dashboard.html` and the scripts that build it, in `C:\bachelor research\methods\`.

**2026-06-16. Model choice.**
- Tested free OpenRouter models to find non-reasoning ones, that is models with no intermediate
  tokens outside the final output.
- A question about using a non-reasoning model as the AI monologue was never answered in
  session. The final design does this: ④ is prompted Qwen-2.5-7B and ⑤ is native DeepSeek-R1.
- An API key was pasted in that chat and should be treated as exposed.

## Phase 3: specification and validation (2026-07-15 to 2026-07-22)

The working repo is now `C:\bachelor research\.1 recent approach\`. Commits from this phase
survive in this repo with new hashes: `b7f40d0` (07-10), `7747aef` (07-16), `fba456b` (07-17),
`77a29ae` and `a5dd52a` (07-22).

**2026-07-15. Codebase summary and research plan.**
- First, a fact-only summary of the project. Then a rewrite of `research_plan.md`, split from a
  new `STATUS.md`.
- The owner rejected the rewrite as too close to the AI-written original. Objections:
  - symbols, arrows and em dashes in prose;
  - "AI speak" phrases;
  - self-praising section titles;
  - too much detail.
- They asked for a from-scratch minimal version, which was never written.

**2026-07-17. Method 2 single-sentence documents.**
- 85 documents become one Punkt sentence, because they have no terminal periods. This is a
  property of the texts, and the splitter works correctly.
- Punkt was pre-registered, so the splitter was kept and the exclusion was reported as a limitation.
- Method 2 gate result: Cliff's δ = 0.63.

**2026-07-17. Method 3 labelling setup.**
- The human labeller must not see the model's labels on the real worksheet. A separate practice
  set is allowed.
- The owner chose about 500 hand labels: 510 in total, 122/83/137/168 for cells ①-④, at a 90% CI
  with half-width 0.10. The κ ≥ 0.70 bar was unchanged.
- A click-to-label tool and a cheat sheet were built (`methods/3_dialogue_act_tagging/labeling_tool/`).
- The owner asked that edits go into the real folder, not an uncommitted worktree.

**2026-07-20. Sample size.**
- The question was whether every cell should be 500, to match DeliData.
- Kept 600: the gates are robust to imbalance, and 600 had no principled anchor either. The owner
  wrote the sentence that discloses this.

**2026-07-22. Target run.**
- Before anything ran, the owner asked for a full pre-flight check of the firewall around cell ⑤.
- Checked that the margins had been frozen before any cell-⑤ output existed.
- Archived a stray partial `cell5_predictions.jsonl`; Method 1 appends to that file, so it would
  have corrupted the run.
- Method 1 has no length control, and this was disclosed.
- The placement script ran only after an explicit "go".
- Result under the per-method gates:
  - Method 1 monologue-leaning;
  - Method 2 dialogue-leaning;
  - Method 3 excluded (κ = 0.5425);
  - pattern: SPLIT.
- The owner then asked to report Method 3 anyway, in a separate exploratory section. They stated
  the rule against "not A but B" phrasing here.
- Speaker labels had leaked in both dialogue cells. They were removed on 2026-07-21 and 07-22, and
  all methods were re-verified (commit `77a29ae`).

**2026-07-23** (from `STATUS.md`; no transcript available).
- Method 3's exploratory placement was computed with post-hoc margins.
- Documents with no first pair part are scored as 0. The owner decided this, and it set
  cell ① to 0.0955 and δ to 0.4717.

## Gap: 2026-07-23 to 2026-08-05

No available session covers this period. In it, the per-method gates were replaced by the single
validity check and the paper reached its final version (`monologue_or_dialogue_final_v5`).

## Phase 4: publication (2026-08-05 to 2026-08-06)

**2026-08-05. Organise the repo for publication.**
- The working repo had problems:
  - the final paper was untracked;
  - four submodules had no `.gitmodules`;
  - it held 65 copyrighted PDFs;
  - it held the access-restricted PAN 2019 corpus.
- The owner's choices:
  - publish a separate public copy and keep the old repo private;
  - move notes to `notes/`;
  - untrack the PAN data;
  - rewrite history with git-filter-repo, keeping dates;
  - build locally, review, then push.
- Results:
  - backup at `C:\bachelor research\_publication_backup_2026-08-05\`;
  - the public repo, which was pushed and checked from a fresh clone (Figure 2 reproduces exactly);
  - Method 1's uncommitted upstream edits exported as patches.
- The owner corrected the docs: "too much of your opinion... Stay way more neutral... Don't
  invent any new large texts that are not 100 percent just facts... no M dashes." Commit `11ab820`
  applied this.
- The session ended while starting a restructure of `data/`.

**2026-08-05 and 2026-08-06** (from git; no transcript available).
- Commit `02f670e` did the `data/` restructure, deleted `notes/` and removed dead scripts.
- `be0243c` turned `DEVIATIONS.md` into `preregistration/METHOD_SELECTION.md`.
- The owner made three edits on the GitHub web interface.
- `0cb0423` condensed `methods.md`.
- `34631eb` fixed spellings. It is the last commit on `main`.
