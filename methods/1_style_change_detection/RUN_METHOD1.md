# Running Method 1 (style-change detection) yourself

Two steps, matching the paper: (1) reproduce Nath's published PAN19 accuracy on the
source data, then (2) run the frozen method on the four calibration cells and apply the
gate. Both are plain scripts in `implementation/`; nothing runs in the background.

All commands are run **from inside `implementation/`**:

```bash
cd methods/1_style_change_detection/implementation
```

## 0. One-time environment setup

```bash
pip install scikit-learn nltk numpy inflect networkx          # deps
pip install personalLibrary/preprocess_NLP_pkg-0.0.1.tar.gz   # Nath's vendored package
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

(If you use the existing `venv/`, activate it first; the packages above may already be in it.)

## 1. Source reproduction on PAN19 (`reproduce_compare.py`)

Confirms our copy of the implementation reproduces the published number before we trust it
on our own data.

```bash
python reproduce_compare.py          # full validation split, both distance measures
```

Expected (target: Nath Table 5 = 0.83 validation / 0.85 test; Zangerle Table 3 = 0.848 official):

```
manhattan  n=1272 binary_acc=0.8349
matusita   n=1272 binary_acc~0.84
```

Already run here on the full split: **Manhattan 0.835, Matusita ~0.84** — reproduces the
paper. Manhattan is the shipped default and matches Nath's submitted 0.848 exactly; Matusita
is what the paper text describes, so that is what we use on our own cells (step 2). The full
run takes a couple of minutes; `python reproduce_compare.py 250` does a fast 250-problem check.

## 2. Calibration cells + gate (`run_calibration.py`)

Runs the frozen method on cells 1-4 and applies the gate in one command:

```bash
python run_calibration.py            # runs all four cells, then prints the gate report
```

This writes per-document predictions to `outputs/method1/calibration_predictions.jsonl`
and prints: per-cell recall, a confusion matrix, per-class recalls, balanced accuracy, a
bootstrap 95% CI, and a label-permutation p-value. **Gate (methods.md §1): balanced accuracy
= ½·(recall_single + recall_multi) significantly exceeds 0.50 (label-permutation null, one-sided
p < .05).** Balanced accuracy is used instead of pooled accuracy because the cells are
class-imbalanced (~1,200 single vs ~1,100 multi): an all-single detector scores ~0.52 pooled but
exactly 0.50 balanced, so the gate can't be passed without genuinely detecting multi-voice text.

Re-print the gate later without re-running:

```bash
python run_calibration.py --report
```

The debate cells are long, so a full run can take a while. If it gets interrupted you can
resume by index range (predictions append), e.g. `python run_calibration.py 3 200 400`,
then `python run_calibration.py --report`.

## What the script fixes, and why (all per the frozen spec)

- **Distance = Matusita.** The executor's default is already Matusita; the old
  `main.py`/`evaluate_benchmark.py` used Manhattan. We pass Matusita explicitly to match the
  method as Nath's paper describes it.
- **200-char merge fix.** The shipped `remove_empty_para()` has a regex bug (an empty
  alternative makes `re.match` always true) that **drops** every paragraph under 200
  characters instead of **merging** it into the previous window as the paper specifies. On
  PAN this was harmless (documents were long); on our data, debate turns are often < 200
  chars, so dropping them would erase the very turn structure we're testing for. The script
  monkeypatches the function with the merge behavior. TBC uses only a pairwise window-distance
  matrix (no ordering), so "merge into previous" is a well-defined deterministic rule.
- **Windowing.** Turn-structured cells (`ai_debate` turns, `human_debate` transcript lines)
  are assembled one turn per paragraph (blank-line separated) so each turn is treated as a
  PAN-style post; continuous-prose cells (`human_monologue`, `ai_monologue`) are passed raw
  and split by Nath's own tokenizer (10-sentence windows when there are no blank lines).

## Files

- `implementation/reproduce_compare.py` — source reproduction on PAN19
- `implementation/run_calibration.py` — calibration-cell run + gate
- `implementation/evaluate_benchmark.py` — pre-existing PAN benchmark evaluator (Manhattan)
- outputs → `outputs/method1/calibration_predictions.jsonl`
