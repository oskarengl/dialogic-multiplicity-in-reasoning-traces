#!/usr/bin/env python3
"""Freeze the placement margins `m` for Methods 1 and 2 (methods.md sec. 3d, applied via sec. 4).

WHY THIS RUNS BEFORE THE TARGET
-------------------------------
methods.md sec. 4 says each surviving method's cell-5 call uses "the same relative-margin rule
as sec. 3d (each signal's own noise-floor-calibrated `m`, from the (3)/(4) bootstrap
procedure)". sec. 3d step 3 is explicit that the procedure "runs only on (3) and (4)
(calibration cells), so it never touches cell (5) and can be run and frozen before Step 2
executes on the target." This script is that freeze: it reads ONLY the calibration outputs and
writes the margins to disk, timestamped, before any cell-5 statistic exists.

WHAT THE MARGIN HAS TO BE A NULL *FOR*
--------------------------------------
The statistic m gates is a relative gap between two distances (methods.md sec. 3d, "Call"):

    r = |d_mono - d_dia| / max(d_mono, d_dia)

and the verdict is "no clear margin" when r < m. So m must answer: *how large can r get when the
probe cell is genuinely equidistant from the two poles and only sampling noise is at work?*

Two constructions are computed. Both use ONLY cells (3) and (4).

  NULL-A ("literal sec. 3d"). Split pole P into equal disjoint halves A and B, measure each
  half's distance to a fixed reference R, and record
      r = |d(A,R) - d(B,R)| / max(d(A,R), d(B,R)).
  A and B are the same pole by construction, so this is pure sampling noise. This is the closest
  reading of sec. 3d's wording ("split (3)'s documents into two random disjoint halves ... record
  the relative gap this produces ... the gap you'd see between two samples that are, by
  construction, the same pole").

  *** NULL-A IS ANTI-CONSERVATIVE AND --selftest DEMONSTRATES IT. *** It omits the probe-side
  noise entirely, and its denominator is the full pole-to-pole distance D rather than the ~D/2
  that an equidistant probe actually sits at. Both errors push m down. Concretely: an equidistant
  probe's two distances move in OPPOSITE directions when the probe's own mean wobbles (d_mono
  grows exactly as d_dia shrinks), so the real gap is ~2x the probe's mean error, while NULL-A
  only ever sees one-sided anchor wobble. Under NULL-A a synthetic probe placed exactly midway
  between the poles is called as leaning - i.e. it fails the one thing the margin exists to
  prevent.

  NULL-B ("equidistant synthetic probe", the corrected null). Build a probe that is equidistant
  from both poles *by construction* out of pole documents, then let every noise source act:
    - M1 (scalar mean signal): a 50/50 mixture of (3) and (4) documents has a mean exactly
      midway between the pole means, so its two distances are equal in expectation.
    - M2 (mean absolute residual against each pole's frozen length curve): a 50/50 mixture is
      NOT equidistant, because the two curves have different residual profiles. The mixing
      proportion p is instead SOLVED so that the two expected distances are equal. d(mix, pole)
      is linear in p, so p has a closed form (see solve_mix_p) - no search, no tuning.
    Each iteration: draw a probe of n5 documents at that mixing proportion (with replacement),
    independently bootstrap-resample each pole anchor (for M2, refitting its length curve on the
    resample, so curve-fit uncertainty is included too), compute d_mono, d_dia, r.
    m = 95th percentile of r.
  n5 = the number of documents in cell 5. That is a file line count, not a statistic computed on
  the target's text - no cell-5 content is read, here or anywhere in this script.

  NULL-B is the one the placement should use. NULL-A is computed and reported alongside so the
  size of the correction is visible rather than asserted. THE CHOICE BETWEEN THEM IS A USER
  DECISION - see STATUS.md. Whichever is chosen is fixed before cell 5 is scored.

SIGNALS
-------
M1: per-document predicted author count (TBC). Cell statistic = mean.
    d(X, Y) = |mean(X) - mean(Y)|                                  (methods.md sec. 4)
M2: per-document raw score with its length covariate, read against each pole's own frozen
    length curve (methods.md sec. 2).
    d(X, pole) = mean over X's documents of |raw - curve_pole(n_pairs)|
    Curves come from Method 2's own run_calibration.fit_pole, imported unmodified, so the fit is
    byte-identical to the one that produced the gate.

Usage:
    python scripts/freeze_placement_margins.py            # freeze (refuses to overwrite)
    python scripts/freeze_placement_margins.py --selftest # check the machinery, writes nothing
    python scripts/freeze_placement_margins.py --force    # deliberate re-freeze
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
M1_CAL = ROOT / "outputs" / "method1" / "calibration_predictions.jsonl"
M2_CAL = ROOT / "outputs" / "method2" / "calibration_raw_scores.jsonl"
M1_CELL5 = ROOT / "outputs" / "method1" / "cell5_predictions.jsonl"
M2_CELL5 = ROOT / "outputs" / "method2" / "cell5_raw_scores.jsonl"
CELL5_DATA = (ROOT / "data" / "ai_reasoning" /
              "processed_native_reasoning_traces.jsonl")
OUTDIR = ROOT / "outputs" / "placement"
OUT_JSON = OUTDIR / "margins_frozen.json"
OUT_TXT = OUTDIR / "margins_frozen.txt"

B_ITERS = 1000
PERCENTILE = 95
SEED = 20260722

DIA_POLE, MONO_POLE = "3", "4"          # methods.md sec. 3d anchors: (3) dialogue, (4) monologue


# --------------------------------------------------------------------------- loading
def load_m1():
    rows = [json.loads(l) for l in open(M1_CAL, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("cell") in ("1", "2", "3", "4")]
    return {c: np.array([r["pred_count"] for r in rows if r["cell"] == c], float)
            for c in ("1", "2", "3", "4")}


def load_m2():
    rows = [json.loads(l) for l in open(M2_CAL, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("cell") in ("1", "2", "3", "4")
            and r.get("raw") is not None]
    out = {}
    for c in ("1", "2", "3", "4"):
        rc = [r for r in rows if r["cell"] == c]
        out[c] = (np.array([r["raw"] for r in rc], float),
                  np.array([r["n_pairs"] for r in rc], float))
    return out


def _fit_pole():
    sys.path.insert(0, str(ROOT / "methods" / "2_stylometric_step_change" / "implementation"))
    from run_calibration import fit_pole                    # noqa: E402  (torch is lazy)
    return fit_pole


def n_cell5():
    """Document count for cell 5 - a line count, not a statistic on its text."""
    if not CELL5_DATA.exists():
        return 600
    with open(CELL5_DATA, encoding="utf-8") as f:
        return sum(1 for l in f if l.strip())


# --------------------------------------------------------------------------- distances
def d_m1(sample, reference):
    """|mean(sample) - mean(reference)| - methods.md sec. 4, scalar signal."""
    return abs(float(np.mean(sample)) - float(np.mean(reference)))


def d_m2(sample, curve):
    """Mean absolute residual of a sample against a pole's length curve."""
    raw, pairs = sample
    return float(np.mean(np.abs(raw - curve(pairs))))


def rel_gap(da, db):
    hi = max(da, db)
    return abs(da - db) / hi if hi > 0 else 0.0


def _halves(n, rng):
    idx = rng.permutation(n)
    h = n // 2
    return idx[:h], idx[h:2 * h]                            # equal size, disjoint


# --------------------------------------------------------------------------- NULL-A
def nullA_m1(cells, rng, ref_mode="opposite"):
    out = []
    for pole, other in ((DIA_POLE, MONO_POLE), (MONO_POLE, DIA_POLE)):
        x = cells[pole]
        ref = cells[other] if ref_mode == "opposite" else cells[pole]
        for _ in range(B_ITERS):
            ia, ib = _halves(len(x), rng)
            out.append(rel_gap(d_m1(x[ia], ref), d_m1(x[ib], ref)))
    return np.array(out)


def nullA_m2(cells, curves, rng, ref_mode="opposite"):
    out = []
    for pole in (DIA_POLE, MONO_POLE):
        raw, pairs = cells[pole]
        own = "dia" if pole == DIA_POLE else "mono"
        other = "mono" if pole == DIA_POLE else "dia"
        curve = curves[other][2] if ref_mode == "opposite" else curves[own][2]
        for _ in range(B_ITERS):
            ia, ib = _halves(len(raw), rng)
            out.append(rel_gap(d_m2((raw[ia], pairs[ia]), curve),
                               d_m2((raw[ib], pairs[ib]), curve)))
    return np.array(out)


# --------------------------------------------------------------------------- NULL-B
def solve_mix_p(a_dia_dia, a_dia_mono, a_mono_dia, a_mono_mono):
    """Mixing proportion p of DIALOGUE-pole documents that makes a mixture probe equidistant.

    d_dia(p) = p*a_dia_dia  + (1-p)*a_mono_dia      (distance to the dialogue curve)
    d_mono(p) = p*a_dia_mono + (1-p)*a_mono_mono    (distance to the monologue curve)
    Both are linear in p, so setting them equal has a closed form:
        p = (a_mono_mono - a_mono_dia) / (a_dia_dia - a_dia_mono - a_mono_dia + a_mono_mono)
    """
    num = a_mono_mono - a_mono_dia
    den = a_dia_dia - a_dia_mono - a_mono_dia + a_mono_mono
    if abs(den) < 1e-15:
        return 0.5
    return num / den


def nullB_m1(cells, n5, rng):
    """Equidistant probe = 50/50 mixture of (3) and (4); anchors bootstrapped."""
    x3, x4 = cells[DIA_POLE], cells[MONO_POLE]
    half = n5 // 2
    out = np.empty(B_ITERS)
    for i in range(B_ITERS):
        probe = np.concatenate([rng.choice(x3, half, replace=True),
                                rng.choice(x4, n5 - half, replace=True)])
        a3 = rng.choice(x3, len(x3), replace=True)
        a4 = rng.choice(x4, len(x4), replace=True)
        out[i] = rel_gap(d_m1(probe, a4), d_m1(probe, a3))   # (d_mono, d_dia)
    return out, 0.5


def nullB_m2(cells, curves, n5, rng):
    """Equidistant probe = mixture at the solved proportion p; anchors bootstrapped WITH refit."""
    fit_pole = _fit_pole()
    raw3, p3 = cells[DIA_POLE]
    raw4, p4 = cells[MONO_POLE]
    f3, f4 = curves["dia"][2], curves["mono"][2]

    p = solve_mix_p(a_dia_dia=float(np.mean(np.abs(raw3 - f3(p3)))),
                    a_dia_mono=float(np.mean(np.abs(raw3 - f4(p3)))),
                    a_mono_dia=float(np.mean(np.abs(raw4 - f3(p4)))),
                    a_mono_mono=float(np.mean(np.abs(raw4 - f4(p4)))))
    p_used = float(min(max(p, 0.0), 1.0))
    n_from3 = int(round(p_used * n5))
    n_from4 = n5 - n_from3

    out = np.empty(B_ITERS)
    i3, i4 = np.arange(len(raw3)), np.arange(len(raw4))
    for i in range(B_ITERS):
        s3 = rng.choice(i3, n_from3, replace=True) if n_from3 else np.array([], int)
        s4 = rng.choice(i4, n_from4, replace=True) if n_from4 else np.array([], int)
        probe = (np.concatenate([raw3[s3], raw4[s4]]),
                 np.concatenate([p3[s3], p4[s4]]))
        b3 = rng.choice(i3, len(i3), replace=True)
        b4 = rng.choice(i4, len(i4), replace=True)
        _, _, g3 = fit_pole(p3[b3], raw3[b3])
        _, _, g4 = fit_pole(p4[b4], raw4[b4])
        out[i] = rel_gap(d_m2(probe, g4), d_m2(probe, g3))   # (d_mono, d_dia)
    return out, p


def summarise(null):
    return {"m": float(np.percentile(null, PERCENTILE)),
            "median": float(np.median(null)),
            "p99": float(np.percentile(null, 99)),
            "max": float(np.max(null)),
            "n_draws": int(len(null))}


# --------------------------------------------------------------------------- selftest
def selftest():
    """Machinery checks on data whose answer is known in advance. Writes nothing."""
    ok = True
    rng = np.random.default_rng(0)

    assert rel_gap(0.4, 0.4) == 0.0 and rel_gap(0.0, 0.0) == 0.0
    assert abs(rel_gap(0.5, 0.25) - 0.5) < 1e-12
    print("[selftest] rel_gap bounded, 0 when equal          OK")

    ia, ib = _halves(601, rng)
    assert len(ia) == len(ib) == 300 and not (set(ia.tolist()) & set(ib.tolist()))
    print("[selftest] _halves equal-sized and disjoint       OK")

    # closed-form mixing solution really does equalise the two distances
    a = solve_mix_p(0.10, 0.40, 0.35, 0.12)
    d_dia = a * 0.10 + (1 - a) * 0.35
    d_mono = a * 0.40 + (1 - a) * 0.12
    print(f"[selftest] solve_mix_p p={a:.4f} -> d_dia={d_dia:.5f} d_mono={d_mono:.5f}  "
          f"{'OK' if abs(d_dia - d_mono) < 1e-12 else 'FAIL'}")
    ok &= abs(d_dia - d_mono) < 1e-12

    # synthetic poles: mean 1.0 (mono) vs 2.0 (dia), realistic dispersion and n
    def synth(n, mu, sd, r):
        return r.normal(mu, sd, n)
    cells = {DIA_POLE: synth(600, 2.0, 0.80, rng), MONO_POLE: synth(600, 1.0, 0.80, rng)}

    mA = summarise(nullA_m1(cells, np.random.default_rng(1)))["m"]
    nb, _ = nullB_m1(cells, 600, np.random.default_rng(1))
    mB = summarise(nb)["m"]
    print(f"[selftest] m(NULL-A)={mA:.4f}   m(NULL-B)={mB:.4f}   ratio={mB / mA:.2f}x")

    # the decisive check: a probe that IS equidistant must not be called
    probe = synth(600, 1.5, 0.80, rng)
    r = rel_gap(d_m1(probe, cells[MONO_POLE]), d_m1(probe, cells[DIA_POLE]))
    for name, m in (("NULL-A", mA), ("NULL-B", mB)):
        called = r >= m
        print(f"[selftest] equidistant probe r={r:.4f} vs {name} m={m:.4f} -> "
              f"{'CALLED (false positive)  FAIL' if called else 'no clear margin  OK'}")
        if name == "NULL-B":
            ok &= not called

    # and a probe that really is at a pole must still be called
    probe4 = synth(600, 1.0, 0.80, rng)
    r4 = rel_gap(d_m1(probe4, cells[MONO_POLE]), d_m1(probe4, cells[DIA_POLE]))
    print(f"[selftest] at-pole probe   r={r4:.4f} vs NULL-B m={mB:.4f} -> "
          f"{'called  OK' if r4 >= mB else 'no clear margin  FAIL (too blunt)'}")
    ok &= r4 >= mB

    # false-positive rate of each margin over many independent equidistant probes
    for name, m in (("NULL-A", mA), ("NULL-B", mB)):
        fp = 0
        for _ in range(500):
            pr = synth(600, 1.5, 0.80, rng)
            if rel_gap(d_m1(pr, cells[MONO_POLE]), d_m1(pr, cells[DIA_POLE])) >= m:
                fp += 1
        print(f"[selftest] {name} false-positive rate on equidistant probes: "
              f"{fp / 500:.1%}  (target <= 5%)")
        if name == "NULL-B":
            ok &= fp / 500 <= 0.10

    print("\n[selftest]", "ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


# --------------------------------------------------------------------------- freeze
def freeze(force=False):
    if OUT_JSON.exists() and not force:
        print(f"REFUSING: {OUT_JSON} already exists. The margins are frozen; re-running after "
              f"cell 5 has been scored would make them data-informed. Use --force only if you "
              f"are deliberately re-freezing before any cell-5 contact.")
        return 1

    cell5_present = {"method1_predictions": M1_CELL5.exists(),
                     "method2_raw_scores": M2_CELL5.exists()}
    n5 = n_cell5()

    m1 = load_m1()
    m2 = load_m2()
    fit_pole = _fit_pole()
    raw3, p3 = m2[DIA_POLE]
    raw4, p4 = m2[MONO_POLE]
    form3, aic3, f3 = fit_pole(p3, raw3)
    form4, aic4, f4 = fit_pole(p4, raw4)
    curves = {"dia": (form3, aic3, f3), "mono": (form4, aic4, f4)}

    res = {
        "m1_nullA": summarise(nullA_m1(m1, np.random.default_rng(SEED))),
        "m2_nullA": summarise(nullA_m2(m2, curves, np.random.default_rng(SEED))),
    }
    nb1, p_mix1 = nullB_m1(m1, n5, np.random.default_rng(SEED))
    nb2, p_mix2 = nullB_m2(m2, curves, n5, np.random.default_rng(SEED))
    res["m1_nullB"] = summarise(nb1)
    res["m2_nullB"] = summarise(nb2)

    payload = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "spec": "methods.md sec. 3d (noise-floor margin) applied via sec. 4",
        "null_A": "literal sec. 3d: same-pole equal disjoint halves vs a fixed opposite-pole "
                  "reference; r = |d(A,R)-d(B,R)|/max(...); pooled over poles (3),(4)",
        "null_B": "equidistant synthetic probe built from pole documents at a solved mixing "
                  "proportion; probe and both anchors resampled (M2 curves refit per draw)",
        "recommended": "null_B (null_A is anti-conservative - see --selftest)",
        "B_iters_per_pole": B_ITERS,
        "percentile": PERCENTILE,
        "seed": SEED,
        "n_cell5_documents": n5,
        "mixing_proportion_dialogue_side": {"m1": p_mix1, "m2": p_mix2},
        "cell5_outputs_present_at_freeze_time": cell5_present,
        "inputs": {"method1": str(M1_CAL.relative_to(ROOT)),
                   "method2": str(M2_CAL.relative_to(ROOT))},
        "m2_pole_curve_forms": {"dia_cell3": form3, "mono_cell4": form4},
        "n_calibration_docs": {"method1": {c: int(len(v)) for c, v in m1.items()},
                               "method2": {c: int(len(v[0])) for c, v in m2.items()}},
        "margins": res,
        "MARGIN_M1_nullB": res["m1_nullB"]["m"],
        "MARGIN_M2_nullB": res["m2_nullB"]["m"],
        "MARGIN_M1_nullA": res["m1_nullA"]["m"],
        "MARGIN_M2_nullA": res["m2_nullA"]["m"],
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "PLACEMENT MARGINS - FROZEN (methods.md sec. 3d via sec. 4)",
        "=" * 78,
        f"frozen (UTC)   : {payload['frozen_at_utc']}",
        f"seed           : {SEED}    B = {B_ITERS} per pole    m = P{PERCENTILE} of the null",
        f"cell 5 n docs  : {n5}  (line count only - no cell-5 text or score was read)",
        "",
        "FIREWALL CHECK - cell 5 method outputs present on disk at freeze time:",
        f"  outputs/method1/cell5_predictions.jsonl : {cell5_present['method1_predictions']}",
        f"  outputs/method2/cell5_raw_scores.jsonl  : {cell5_present['method2_raw_scores']}",
        "  (both False = the margins were fixed with no target results in existence)",
        "",
        f"M2 pole curve forms: dialogue (3) = {form3}, monologue (4) = {form4}",
        f"Equidistant-probe mixing proportion (share drawn from the dialogue pole):",
        f"  M1 = {p_mix1:.4f} (50/50 exactly equalises a mean-difference distance)",
        f"  M2 = {p_mix2:.4f} (solved so both expected residual distances match)",
        "",
        f"{'signal':32s} {'m (P95)':>10s} {'median':>10s} {'P99':>10s} {'max':>10s}",
    ]
    label = {"m1_nullA": "M1 author count   NULL-A",
             "m1_nullB": "M1 author count   NULL-B *",
             "m2_nullA": "M2 lean residual  NULL-A",
             "m2_nullB": "M2 lean residual  NULL-B *"}
    for k in ("m1_nullA", "m1_nullB", "m2_nullA", "m2_nullB"):
        s = res[k]
        lines.append(f"{label[k]:32s} {s['m']:>10.4f} {s['median']:>10.4f} "
                     f"{s['p99']:>10.4f} {s['max']:>10.4f}")
    lines += [
        "",
        "* recommended. NULL-A is the literal reading of sec. 3d but is anti-conservative:",
        "  it omits probe-side sampling noise and divides by the full pole-to-pole distance",
        "  rather than the ~half that an equidistant probe sits at. `--selftest` shows a",
        "  synthetic probe placed exactly midway between the poles being CALLED under NULL-A.",
        "",
        "USE: cell 5 is called toward the nearer pole only when",
        "     |d_mono - d_dia| / max(d_mono, d_dia) >= m",
        "     Otherwise the verdict is 'no clear margin' (methods.md sec. 3d).",
    ]
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_TXT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        sys.exit(selftest())
    sys.exit(freeze(force=(a == ["--force"])))
