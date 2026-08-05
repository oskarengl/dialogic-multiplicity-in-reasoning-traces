"""Method 3 - signal-validity gate (methods.md sec. 3e.2).

Uses the tags already produced by label_dialogue_acts_v2.py (no LLM calls here). Computes,
for the four calibration cells only:

  - sec. 3c (primary signal): per-document adjacency-pair completion rate, the share of
    FPP-absent documents per cell, and whether the dialogue cells (2,3) show a higher mean
    completion rate than the monologue cells (1,4), with Cliff's delta as the effect size.
  - sec. 3a/3b (consistency check, not gating): within-class vs. between-class Jensen-
    Shannon divergence on the unigram and joint-bigram distributions - dialogue cells should
    resemble each other more than they resemble the monologue cells, and vice versa.

GATE (as literally specified in methods.md sec. 3e.2): completion rate separates the poles
in the expected direction (mean(2,3) > mean(1,4)). methods.md states this as a direction +
effect-size *report*, unlike Method 2's gate, which explicitly requires Cliff's delta >= 0.33.
This script reports BOTH readings - the bare-direction gate (as literally specified) and the
direction-plus-delta>=0.33 gate (for consistency with Method 2, and because Method 1's
pooled-accuracy gate turned out to admit a degenerate pass) - clearly labeled as two different
readings, rather than silently picking one. See RUN_METHOD3.md for the open question this
raises.

Never touches cell 5 (ai_reasoning): CELLS below is fixed to {1,2,3,4}.

Usage (from implementation/):
    python run_calibration.py            # compute and print the full report
    python run_calibration.py --selftest # verify signal math against synthetic tags
"""
import sys
import numpy as np
import signals as S

CALIBRATION_CELLS = ("1", "2", "3", "4")
DIALOGUE = ("2", "3")
MONOLOGUE = ("1", "4")


def report():
    docs = {c: S.load_cell_tags(c)[0] for c in CALIBRATION_CELLS}

    # --- 3c: completion rate (primary signal) ---
    print("=== 3c. Adjacency-pair completion rate (primary signal) ===")
    rates = {}
    for c in CALIBRATION_CELLS:
        r, n_absent, n_docs = S.cell_completion_rates(docs[c])
        rates[c] = r
        mean_r = np.mean(r) if r else float("nan")
        print(f"cell {c} ({S.CELL_LABEL[c]:16s}) n_docs={n_docs:4d}  "
              f"FPP-absent={n_absent:4d} ({n_absent/n_docs:.1%})  "
              f"scored_n={len(r):4d}  mean_rate={mean_r:.4f}  (FPP-absent scored 0)")

    dia = np.array(sum((rates[c] for c in DIALOGUE), []))
    mono = np.array(sum((rates[c] for c in MONOLOGUE), []))
    m_dia, m_mono = dia.mean(), mono.mean()
    delta = S.cliffs_delta(dia, mono)
    direction = m_dia > m_mono
    print(f"\nmean completion rate  dialogue (2,3) = {m_dia:.4f}   "
          f"monologue (1,4) = {m_mono:.4f}")
    print(f"Cliff's delta (dialogue vs monologue) = {delta:.4f}")
    print(f"direction (dialogue > monologue): {direction}")
    print(f"GATE-A (direction only, as literally specified): "
          f"{'PASS' if direction else 'FAIL'}")
    print(f"GATE-B (direction AND delta >= 0.33, consistency w/ Method 2): "
          f"{'PASS' if (direction and delta >= 0.33) else 'FAIL'}")

    # --- 3a/3b: consistency check (not gating) ---
    print("\n=== 3a/3b. Within-class vs. between-class JSD (consistency check, not gating) ===")
    uni = {c: S.cell_unigram(docs[c]) for c in CALIBRATION_CELLS}
    big = {c: S.cell_bigram(docs[c])[1] for c in CALIBRATION_CELLS}  # joint-normalized

    def flat(m):
        return m.flatten()

    within_mono_uni = S.jsd(uni["1"], uni["4"])
    within_dia_uni = S.jsd(uni["2"], uni["3"])
    between_uni = np.mean([S.jsd(uni[a], uni[b]) for a in MONOLOGUE for b in DIALOGUE])
    print(f"3a unigram JSD:  within-mono(1,4)={within_mono_uni:.4f}  "
          f"within-dia(2,3)={within_dia_uni:.4f}  between(avg)={between_uni:.4f}  "
          f"[within < between expected: "
          f"{within_mono_uni < between_uni and within_dia_uni < between_uni}]")

    within_mono_big = S.jsd(flat(big["1"]), flat(big["4"]))
    within_dia_big = S.jsd(flat(big["2"]), flat(big["3"]))
    between_big = np.mean([S.jsd(flat(big[a]), flat(big[b])) for a in MONOLOGUE for b in DIALOGUE])
    print(f"3b bigram  JSD:  within-mono(1,4)={within_mono_big:.4f}  "
          f"within-dia(2,3)={within_dia_big:.4f}  between(avg)={between_big:.4f}  "
          f"[within < between expected: "
          f"{within_mono_big < between_big and within_dia_big < between_big}]")

    print("\n(Run reliability_sample.py separately for the sec. 3e.1 kappa reliability gate; "
          "Method 3 needs BOTH gates to pass.)")


def selftest():
    """Synthetic tag sequences: dialogue-like docs alternate question/answer (high
    completion), monologue-like docs are mostly 'inform' (few FPPs, low completion).
    Confirms the direction comes out correctly and the JSD consistency check behaves."""
    import random
    rng = random.Random(0)

    def dia_doc(n=20):
        seq = []
        for _ in range(n // 2):
            seq += [rng.choice(["propositionalQuestion", "setQuestion"]),
                    rng.choice(["answer", "confirm"])]
        return seq

    def mono_doc(n=20):
        return [rng.choice(["inform", "stalling", "autoPositive"]) for _ in range(n)]

    fake = {
        "1": [{"doc_id": f"d{i}", "tags": mono_doc()} for i in range(80)],
        "4": [{"doc_id": f"d{i}", "tags": mono_doc()} for i in range(80)],
        "2": [{"doc_id": f"d{i}", "tags": dia_doc()} for i in range(80)],
        "3": [{"doc_id": f"d{i}", "tags": dia_doc()} for i in range(80)],
    }
    global report

    def fake_load(c, limit=None, use_cache=True):
        return fake[c], 0
    orig = S.load_cell_tags
    S.load_cell_tags = fake_load
    try:
        report()
    finally:
        S.load_cell_tags = orig


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        report()
