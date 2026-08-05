# RUN_CELL5 — the Step-2 target run, in order

Everything here is paste-ready PowerShell. **Do the steps in order**; step 0 must finish before
anything else is committed, and step 1 must finish before step 2.

Cell ⑤ is `ai_reasoning` — the pre-registered target. It is placed by **Methods 1 and 2 only**;
Method 3 failed its §3e reliability gate (κ = 0.5425 < 0.70) and takes no part. See `STATUS.md`,
entries dated 2026-07-22.

---

## 0. [YOU] Clear the git locks and commit

The sandbox cannot unlink files under `.git` (`Operation not permitted`), so stale `.lock` files
are blocking every ref update, and a diagnostic probe left a junk branch behind. **There are four
lock files, not the three the previous handover listed** — `refs/heads/main.lock` was missed.

```powershell
cd "C:\bachelor research\.1 recent approach"
del .git\HEAD.lock, .git\packed-refs.lock, .git\refs\heads\main.lock, .git\refs\heads\_probe_delete_me.lock
git branch -D _probe_delete_me
git add -A
git commit -m "Step 3 prep: two-method verdict rule, frozen placement margins, cell-5 wiring, figures"
git push origin main
```

Remote is `https://github.com/oskarengl/.1-recent-approach.git`. Last good commit is `aecfd6f`
(the 503 hand labels); everything since is on disk only.

If `git commit` complains about an identity, add `-c user.name=Oskar -c user.email=oskar.engl@gmx.de`.

---

## 1. [YOU] Run Methods 1 and 2 on cell ⑤

Both scripts resolve paths **relative to the current directory**, so you must `cd` into the
`implementation/` folder first — running them from anywhere else silently writes to the wrong
place.

Cell ⑤ results go to their own files (`outputs/method1/cell5_predictions.jsonl`,
`outputs/method2/cell5_raw_scores.jsonl`). The calibration files and both frozen gate numbers
are untouched by these commands, by construction.

### Method 1 — fast, well under a minute

```powershell
cd "C:\bachelor research\.1 recent approach\methods\1_style_change_detection\implementation"
.\venv\Scripts\python.exe run_calibration.py 5 0 600
```

Expect one line: `cell 5 (ai_reasoning) [0:600] n=600 (Ns)`. For reference, cell ③ took 44 s.

### Method 2 — the slow one

```powershell
cd "C:\bachelor research\.1 recent approach\methods\2_stylometric_step_change\implementation"
.\venv\Scripts\python.exe run_calibration.py 5 0 600
```

This prints `progress: n/600`. Cell ④ took 135 s, but **cell ⑤ documents are far longer**
(~10,700 chars median vs ~860 for cell ④), so budget considerably more — plan for tens of
minutes on CPU.

If it gets interrupted, it appends, so resume from where it stopped, e.g.
`.\venv\Scripts\python.exe run_calibration.py 5 240 600`.

**Do not run either script with no arguments.** That form re-runs all four calibration cells from
scratch into a fresh file and would overwrite the gate results.

---

## 2. [ME] Placement and figures

Once both files exist, tell me and I'll run these — or run them yourself:

```powershell
cd "C:\bachelor research\.1 recent approach"
python scripts\place_cell5.py
python scripts\make_placement_figures.py
```

`place_cell5.py` refuses to run unless the margins are already frozen, so the threshold can never
be chosen with the answer on screen. It writes `outputs/placement/cell5_placement.txt` (Table X:
methods × {passed Step 1?, verdict, margin}) and `.json`.

`make_placement_figures.py` writes Figs M1.1, M2.1, M2.2 and X.1 into `paper/figures/` as `.pdf`
and `.png`.

---

## What is already frozen, before any of this runs

| | |
|---|---|
| Verdict rule | §4 pattern-not-vote, applied unchanged at two methods (`methods.md` §4 clarification note) |
| M1 margin | `m = 0.3615` |
| M2 margin | `m = 0.1117` |
| Source | `outputs/placement/margins_frozen.json`, NULL-B, with a recorded check that neither cell-⑤ output file existed at freeze time |

Nothing in step 1 or 2 can change any of those. If you want to re-freeze the margins you have to
pass `--force` deliberately, and after step 1 that would no longer be blind.
