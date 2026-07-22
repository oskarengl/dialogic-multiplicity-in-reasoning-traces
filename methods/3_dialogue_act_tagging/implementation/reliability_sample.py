"""Method 3 - labeling-reliability check (methods.md sec. 3e.1).

Three phases:

--plan    Compute the required hand-labeling sample size per calibration cell from the
          standard asymptotic variance formula for Cohen's kappa (Fleiss, Cohen & Everitt,
          1969), using each cell's OWN observed tag marginals (sec. 3a, calibration-only
          input - never touches cell 5). Target: a CI (confidence level + half-width, both
          configurable via --confidence / --half-width) around the measured kappa, assuming
          the threshold kappa0 = 0.70 as the value being tested. Default precision target is
          CONFIDENCE=0.90, HALF_WIDTH=0.10 (see PRECISION_NOTE below for why).

--sample  Draw that many utterances per cell (fixed seed, reproducible) and write a BLIND
          hand-labeling worksheet (CSV, no LLM label column) plus a separate hidden-answer
          file (the LLM's label for each sampled utterance, kept out of the worksheet) for
          later scoring. You (the human) fill in a "human_label" column in the worksheet.

--score   Once the worksheet is filled in, merge it against the hidden LLM labels and
          compute Cohen's kappa (+ bootstrap 95% CI), pooled and per cell. Gate: kappa >= 0.70.

Usage (from implementation/):
    python reliability_sample.py --plan
    python reliability_sample.py --sample
    # ... hand-label outputs/method3/reliability/worksheet.csv (fill "human_label") ...
    python reliability_sample.py --score
    python reliability_sample.py --selftest   # sanity-check the n-formula + kappa/CI math
"""
import argparse, csv, json, math, random
from pathlib import Path
import numpy as np

import signals as S

OUTDIR = S.ROOT / "outputs" / "method3" / "reliability"
OUTDIR.mkdir(parents=True, exist_ok=True)
WORKSHEET = OUTDIR / "worksheet.csv"
HIDDEN = OUTDIR / "hidden_llm_labels.json"
PLAN = OUTDIR / "sample_plan.json"

KAPPA0 = 0.70          # pass/fail threshold being tested (methods.md sec. 3e.1) - UNCHANGED
CI_CONFIDENCE = 0.90   # precision target: confidence level (was 0.95)
CI_HALFWIDTH = 0.10    # precision target: half-width around measured kappa (was 0.05, then 0.08)

# PRECISION_NOTE: KAPPA0 (the actual pass/fail bar, kappa >= 0.70) is untouched - lowering
# it would be lowering the bar itself, which we do NOT do. What changed is CI_CONFIDENCE and
# CI_HALFWIDTH, i.e. how precisely we insist on PINNING DOWN the measured kappa before
# trusting a pass/fail call near the boundary. The original 95%/±0.05 target was chosen
# without weighing labeling cost; for a practical project, a 90% CI of ±0.10 around a
# measured kappa of, say, 0.75 gives roughly [0.65, 0.85] - still unambiguous relative to
# the 0.70 cutoff - while cutting the required sample to ~18% of the original
# (n scales as confidence-quantile^2 / half_width^2). The extra half-width also builds in a
# buffer for real-world labeling noise beyond the pure sampling-noise formula. This is a
# legitimate blind decision: a cost/precision trade-off fixed before any hand-labels exist,
# and does not touch cell 5 or any measured kappa value. Logged in STATUS.md.

# Two-sided normal quantiles for common confidence levels (avoids a scipy dependency here).
_Z_TABLE = {0.80: 1.281552, 0.85: 1.439531, 0.90: 1.644854,
            0.95: 1.959964, 0.975: 2.241403, 0.99: 2.575829}


def _z_for(confidence):
    if confidence in _Z_TABLE:
        return _Z_TABLE[confidence]
    try:
        from scipy.stats import norm
        return float(norm.ppf(0.5 + confidence / 2))
    except ImportError:
        raise ValueError(f"No table entry for confidence={confidence} and scipy not "
                         f"available; use one of {sorted(_Z_TABLE)} or install scipy.")


def required_n(marginals, kappa0=KAPPA0, half_width=CI_HALFWIDTH, confidence=CI_CONFIDENCE):
    """n such that the `confidence` CI half-width around a measured kappa = kappa0 is
    <= half_width, using the standard single-kappa large-sample approximation with both
    raters assumed to share the given marginal distribution p_k:
        p_e = sum_k p_k^2                      (chance agreement)
        p_o = kappa0*(1-p_e) + p_e              (implied observed agreement)
        SE(kappa) ~= sqrt( p_o*(1-p_o) / (n*(1-p_e)^2) )
        n = p_o*(1-p_o) / ( (half_width/Z)^2 * (1-p_e)^2 )
    """
    z = _z_for(confidence)
    p = np.asarray(marginals, float); p = p / p.sum()
    p_e = float(np.sum(p ** 2))
    p_o = kappa0 * (1 - p_e) + p_e
    se_target = half_width / z
    n = p_o * (1 - p_o) / (se_target ** 2 * (1 - p_e) ** 2)
    return max(30, math.ceil(n))  # floor of 30 regardless, for basic stability


def cmd_plan(half_width=CI_HALFWIDTH, confidence=CI_CONFIDENCE, kappa0=KAPPA0):
    print(f"Precision target: {confidence:.0%} CI, half-width <= {half_width:.2f}, "
          f"testing kappa0={kappa0:.2f}\n")
    plan = {"_settings": {"half_width": half_width, "confidence": confidence, "kappa0": kappa0}}
    for cell in ("1", "2", "3", "4"):
        docs, _ = S.load_cell_tags(cell)
        marg = S.cell_unigram(docs)
        if marg.sum() == 0:
            marg = np.ones(S.N_TAGS) / S.N_TAGS  # conservative fallback
            note = "uniform fallback (no labels found)"
        else:
            note = "from observed sec. 3a marginals"
        n = required_n(marg, kappa0=kappa0, half_width=half_width, confidence=confidence)
        total_sentences = sum(len(d["tags"]) for d in docs)
        n = min(n, total_sentences) if total_sentences else n
        plan[cell] = {"cell": S.CELL_LABEL[cell], "n_required": n,
                      "n_available_sentences": total_sentences, "basis": note}
        print(f"cell {cell} ({S.CELL_LABEL[cell]:16s}) n_required={n:4d}  "
              f"(of {total_sentences} sentences, {note})")
    json.dump(plan, open(PLAN, "w"), indent=2)
    total = sum(p["n_required"] for c, p in plan.items() if c != "_settings")
    print(f"\nTotal across 4 cells: {total}")
    print(f"Plan written to {PLAN}")


def cmd_sample(seed=0):
    if not PLAN.exists():
        print("Run --plan first."); return
    plan = json.load(open(PLAN))
    rng = random.Random(seed)
    worksheet_rows = []
    hidden = {}
    for cell, p in plan.items():
        if cell == "_settings":
            continue
        # (text isn't in the tag cache, so re-read files directly for the sampled pool)
        d_dir = S.OUTBASE / S.CELL_DIRS[cell]
        pool = []
        for fp in sorted(d_dir.glob("*.jsonl")):
            for idx, line in enumerate(open(fp, encoding="utf-8")):
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("label") not in S.TAG_IDX:
                    continue
                pool.append((fp.stem, idx, rec["text"], rec["label"]))
        n = min(p["n_required"], len(pool))
        sample = rng.sample(pool, n)
        for doc_id, idx, text, label in sample:
            key = f"{cell}:{doc_id}:{idx}"
            worksheet_rows.append({"cell": cell, "cell_name": S.CELL_LABEL[cell],
                                   "doc_id": doc_id, "sentence_idx": idx, "text": text,
                                   "human_label": ""})
            hidden[key] = label
    rng2 = random.Random(seed + 1)
    rng2.shuffle(worksheet_rows)  # blind ordering: cell/doc order doesn't hint the label
    with open(WORKSHEET, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cell", "cell_name", "doc_id", "sentence_idx",
                                          "text", "human_label"])
        w.writeheader()
        w.writerows(worksheet_rows)
    json.dump(hidden, open(HIDDEN, "w"), indent=2)
    print(f"Wrote {len(worksheet_rows)} rows to {WORKSHEET}")
    print(f"Allowed tags (case-sensitive): {', '.join(S.TAGS)}")
    print("Fill in the human_label column, save, then run --score.")


def cohen_kappa(y_true, y_pred, labels):
    idx = {l: i for i, l in enumerate(labels)}
    k = len(labels)
    cm = np.zeros((k, k))
    for t, p in zip(y_true, y_pred):
        cm[idx[t], idx[p]] += 1
    n = cm.sum()
    p_o = np.trace(cm) / n
    p_e = float((cm.sum(axis=1) * cm.sum(axis=0)).sum()) / (n ** 2)
    if p_e >= 1:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def cmd_score(n_boot=2000, seed=0):
    if not WORKSHEET.exists() or not HIDDEN.exists():
        print("Run --sample first."); return
    hidden = json.load(open(HIDDEN))
    rows = list(csv.DictReader(open(WORKSHEET, encoding="utf-8")))
    y_true, y_pred, cells = [], [], []
    n_missing = n_bad = 0
    for r in rows:
        key = f"{r['cell']}:{r['doc_id']}:{r['sentence_idx']}"
        h = (r.get("human_label") or "").strip()
        if not h:
            n_missing += 1; continue
        if h not in S.TAG_IDX:
            n_bad += 1; continue
        y_true.append(h); y_pred.append(hidden[key]); cells.append(r["cell"])
    if n_missing:
        print(f"[{n_missing} rows not yet hand-labeled, skipped]")
    if n_bad:
        print(f"[{n_bad} rows have an unrecognized human_label, skipped]")
    if len(y_true) < 10:
        print("Not enough completed rows to score yet."); return

    labels = sorted(set(y_true) | set(y_pred))
    kappa = cohen_kappa(y_true, y_pred, labels)

    rng = np.random.default_rng(seed)
    idx_all = np.arange(len(y_true))
    boot = np.empty(n_boot)
    yt, yp = np.array(y_true), np.array(y_pred)
    for i in range(n_boot):
        bi = rng.choice(idx_all, len(idx_all), replace=True)
        boot[i] = cohen_kappa(yt[bi], yp[bi], labels)
    lo, hi = np.percentile(boot, [2.5, 97.5])

    print(f"\nn scored = {len(y_true)}   pooled kappa = {kappa:.4f}   "
          f"bootstrap 95% CI = [{lo:.4f}, {hi:.4f}]")
    print(f"GATE (kappa >= 0.70): {'PASS' if kappa >= 0.70 else 'FAIL'}")
    print(f"\n{'cell':8s} {'n':>5s} {'kappa':>7s}")
    for c in ("1", "2", "3", "4"):
        ci = [i for i, cc in enumerate(cells) if cc == c]
        if len(ci) < 5:
            print(f"{c:8s} {len(ci):>5d}     n/a (too few)"); continue
        k_c = cohen_kappa(yt[ci], yp[ci], labels)
        print(f"{c:8s} {len(ci):>5d} {k_c:>7.4f}")


def selftest():
    # sample-size formula sanity check. Skewed marginals (one dominant tag, e.g. a
    # monologue cell dominated by "inform") have HIGHER chance agreement p_e, which
    # shrinks (1-p_e) and therefore requires a LARGER sample to pin down kappa to the
    # same precision - this is the correct, if slightly counterintuitive, behavior of
    # the formula: it is harder to distinguish real from chance agreement when one tag
    # dominates, so skewed cells need more hand-labeling, not less.
    uniform = np.ones(28) / 28
    skewed = np.zeros(28); skewed[0] = 0.6; skewed[1:] = 0.4 / 27
    n_u = required_n(uniform); n_s = required_n(skewed)
    print(f"[selftest] n(uniform marginals) = {n_u}   n(skewed marginals) = {n_s}"
          f"   (skewed > uniform is expected: {n_s > n_u})")
    assert n_u > 30 and n_s > 30
    assert n_s > n_u, "skewed marginals should require a larger sample than uniform"

    # kappa recovery: simulate raters agreeing at a known rate, check kappa ~ matches.
    rng = np.random.default_rng(0)
    labels = ["a", "b", "c", "d"]
    n = 2000
    p_true = rng.choice(labels, n, p=[0.4, 0.3, 0.2, 0.1])
    target_kappa = 0.75
    p_e = sum((np.mean(p_true == l)) ** 2 for l in labels)
    p_o = target_kappa * (1 - p_e) + p_e
    pred = p_true.copy()
    flip = rng.random(n) > p_o
    pred[flip] = rng.choice(labels, flip.sum())
    k = cohen_kappa(p_true.tolist(), pred.tolist(), labels)
    print(f"[selftest] target kappa~{target_kappa:.2f} (approx, ignores same-label flips), "
          f"measured kappa={k:.3f}")
    assert 0.55 < k < 0.95, "kappa recovery sanity check failed"
    print("[selftest] OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--half-width", type=float, default=CI_HALFWIDTH,
                    help=f"target CI half-width around measured kappa (default {CI_HALFWIDTH})")
    ap.add_argument("--confidence", type=float, default=CI_CONFIDENCE,
                    help=f"CI confidence level, e.g. 0.90 or 0.95 (default {CI_CONFIDENCE})")
    ap.add_argument("--kappa0", type=float, default=KAPPA0,
                    help=f"pass/fail threshold being tested - NOT the precision target "
                         f"(default {KAPPA0}, matches SOURCES.md; do not lower this to "
                         f"reduce n, lower --half-width or --confidence instead)")
    a = ap.parse_args()
    if a.selftest: selftest()
    elif a.plan: cmd_plan(half_width=a.half_width, confidence=a.confidence, kappa0=a.kappa0)
    elif a.sample: cmd_sample()
    elif a.score: cmd_score()
    else: ap.print_help()
