#!/usr/bin/env python3
"""Place cell (5) ai_reasoning on the monologue<->dialogue axis - methods.md sec. 4.

Runs AFTER `run_calibration.py 5 0 600` has been executed for Methods 1 and 2, and AFTER
`freeze_placement_margins.py` has fixed each method's margin. Refuses to run if the margins are
not frozen, so the threshold can never be chosen with the answer already on screen.

Method 3 does not appear here. It failed its sec. 3e reliability gate (kappa = 0.5425 < 0.70) and
sec. 4's first paragraph is explicit that a method which fails Step 1 "has shown it cannot measure
the thing, so its reading of cell (5) is discarded, not averaged in."

THE CALL (methods.md sec. 3d, "Call")
-------------------------------------
    d_mono = distance((5), (4))      d_dia = distance((5), (3))
    r      = |d_mono - d_dia| / max(d_mono, d_dia)
    verdict = "no clear margin"    if r < m
              "monologue-leaning"  if r >= m and d_mono < d_dia
              "dialogue-leaning"   if r >= m and d_dia < d_mono

with each method's own m from outputs/placement/margins_frozen.json (NULL-B; see STATUS.md
2026-07-22 for why NULL-B rather than the literal sec. 3d null).

    M1: distance = |mean predicted author count difference|          (methods.md sec. 4)
    M2: distance = mean |raw - curve_pole(n_pairs)| against each pole's frozen length curve

COMBINING (methods.md sec. 4 + the 2026-07-22 clarification)
-----------------------------------------------------------
Reported, never voted. Two methods survive, so the deliverable is the PATTERN of two verdicts
with both margins shown. If they agree that is the headline, stated as two concurring measures -
weaker than the three-method concurrence sec. 4 was drafted against. If they split it is reported
as a split. No tie-break, no primary method.

NORMALISED AXIS (for Fig X.1, methods.md sec. 5)
------------------------------------------------
s(X) = d_mono(X) / (d_mono(X) + d_dia(X)), then rescaled so pole (4) = 0 and pole (3) = 1. The
"no clear margin" band maps to s in [(1-m)/(2-m), 1/(2-m)] before rescaling. Cells (1) and (2) are
plotted for context only - sec. 3d restricts the anchors to the AI-only pair.

Usage:
    python scripts/place_cell5.py             # place cell 5 and write the report
    python scripts/place_cell5.py --selftest  # verify the call logic, reads/writes nothing
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
M1_CAL = ROOT / "outputs" / "method1" / "calibration_predictions.jsonl"
M2_CAL = ROOT / "outputs" / "method2" / "calibration_raw_scores.jsonl"
M1_C5 = ROOT / "outputs" / "method1" / "cell5_predictions.jsonl"
M2_C5 = ROOT / "outputs" / "method2" / "cell5_raw_scores.jsonl"
MARGINS = ROOT / "outputs" / "placement" / "margins_frozen.json"
OUT_TXT = ROOT / "outputs" / "placement" / "cell5_placement.txt"
OUT_JSON = ROOT / "outputs" / "placement" / "cell5_placement.json"

DIA, MONO, TARGET = "3", "4", "5"
BOOT = 2000
SEED = 20260722

MONO_LEAN, DIA_LEAN, NO_MARGIN = "monologue-leaning", "dialogue-leaning", "no clear margin"


# --------------------------------------------------------------------------- the call
def call_verdict(d_mono, d_dia, m):
    """methods.md sec. 3d. Returns (verdict, relative gap r)."""
    hi = max(d_mono, d_dia)
    r = abs(d_mono - d_dia) / hi if hi > 0 else 0.0
    if r < m:
        return NO_MARGIN, r
    return (MONO_LEAN if d_mono < d_dia else DIA_LEAN), r


def s_position(d_mono, d_dia):
    tot = d_mono + d_dia
    return d_mono / tot if tot > 0 else 0.5


def band_in_s(m):
    """The 'no clear margin' interval in un-rescaled s coordinates."""
    return (1 - m) / (2 - m), 1 / (2 - m)


def rescale(s, s_mono_pole, s_dia_pole):
    den = s_dia_pole - s_mono_pole
    return (s - s_mono_pole) / den if den != 0 else float("nan")


# --------------------------------------------------------------------------- loading
def _rows(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def load_m1():
    cal = [r for r in _rows(M1_CAL) if r.get("cell") in ("1", "2", "3", "4")]
    out = {c: np.array([r["pred_count"] for r in cal if r["cell"] == c], float)
           for c in ("1", "2", "3", "4")}
    out[TARGET] = np.array([r["pred_count"] for r in _rows(M1_C5)], float)
    return out


def load_m2():
    cal = [r for r in _rows(M2_CAL)
           if r.get("cell") in ("1", "2", "3", "4") and r.get("raw") is not None]
    c5 = [r for r in _rows(M2_C5) if r.get("raw") is not None]
    n5_total = len(_rows(M2_C5))
    out = {}
    for c in ("1", "2", "3", "4"):
        rc = [r for r in cal if r["cell"] == c]
        out[c] = (np.array([r["raw"] for r in rc], float),
                  np.array([r["n_pairs"] for r in rc], float))
    out[TARGET] = (np.array([r["raw"] for r in c5], float),
                   np.array([r["n_pairs"] for r in c5], float))
    return out, n5_total - len(c5)


def m2_curves(cells):
    sys.path.insert(0, str(ROOT / "methods" / "2_stylometric_step_change" / "implementation"))
    from run_calibration import fit_pole                    # noqa: E402  (torch is lazy)
    raw3, p3 = cells[DIA]
    raw4, p4 = cells[MONO]
    form3, _, f3 = fit_pole(p3, raw3)
    form4, _, f4 = fit_pole(p4, raw4)
    return (form3, f3), (form4, f4)


# --------------------------------------------------------------------------- per method
def place_m1(cells, m, rng):
    def dm(x, y):
        return abs(float(np.mean(x)) - float(np.mean(y)))

    d_mono = dm(cells[TARGET], cells[MONO])
    d_dia = dm(cells[TARGET], cells[DIA])
    verdict, r = call_verdict(d_mono, d_dia, m)

    flips = 0
    for _ in range(BOOT):
        b5 = rng.choice(cells[TARGET], len(cells[TARGET]), replace=True)
        b3 = rng.choice(cells[DIA], len(cells[DIA]), replace=True)
        b4 = rng.choice(cells[MONO], len(cells[MONO]), replace=True)
        v, _ = call_verdict(dm(b5, b4), dm(b5, b3), m)
        flips += (v != verdict)

    s_all = {}
    for c in ("1", "2", "3", "4", TARGET):
        s_all[c] = s_position(dm(cells[c], cells[MONO]), dm(cells[c], cells[DIA]))
    return {"d_mono": d_mono, "d_dia": d_dia, "r": r, "m": m, "verdict": verdict,
            "verdict_stability": 1 - flips / BOOT,
            "cell_means": {c: float(np.mean(v)) for c, v in cells.items()},
            "s_raw": s_all}


def place_m2(cells, curves, m, rng):
    (_, f3), (_, f4) = curves

    def dres(sample, curve):
        raw, pairs = sample
        return float(np.mean(np.abs(raw - curve(pairs))))

    d_mono = dres(cells[TARGET], f4)
    d_dia = dres(cells[TARGET], f3)
    verdict, r = call_verdict(d_mono, d_dia, m)

    raw5, p5 = cells[TARGET]
    n5 = len(raw5)
    idx = np.arange(n5)
    flips = 0
    for _ in range(BOOT):
        b = rng.choice(idx, n5, replace=True)
        v, _ = call_verdict(dres((raw5[b], p5[b]), f4), dres((raw5[b], p5[b]), f3), m)
        flips += (v != verdict)

    s_all = {}
    for c in ("1", "2", "3", "4", TARGET):
        s_all[c] = s_position(dres(cells[c], f4), dres(cells[c], f3))

    raw3, p3 = cells[DIA]
    raw4, p4 = cells[MONO]
    return {"d_mono": d_mono, "d_dia": d_dia, "r": r, "m": m, "verdict": verdict,
            "verdict_stability": 1 - flips / BOOT,
            "s_raw": s_all,
            "length_extrapolation": {
                "cell5_median_pairs": float(np.median(p5)),
                "cell5_max_pairs": float(np.max(p5)),
                "pole3_max_pairs": float(np.max(p3)),
                "pole4_max_pairs": float(np.max(p4)),
                "cell5_share_beyond_pole3_max": float(np.mean(p5 > np.max(p3))),
                "cell5_share_beyond_pole4_max": float(np.mean(p5 > np.max(p4)))}}


# --------------------------------------------------------------------------- selftest
def selftest():
    ok = True
    m = 0.20

    cases = [
        # (d_mono, d_dia, m, expected verdict, why)
        (0.10, 0.90, m, MONO_LEAN, "far closer to the monologue pole"),
        (0.90, 0.10, m, DIA_LEAN, "far closer to the dialogue pole"),
        (0.50, 0.50, m, NO_MARGIN, "exactly equidistant"),
        (0.45, 0.50, m, NO_MARGIN, "r = 0.10 < m, inside the band"),
        (0.30, 0.50, m, MONO_LEAN, "r = 0.40 > m, clearly outside the band"),
        (0.50, 0.30, m, DIA_LEAN, "mirror image, clearly outside"),
        # exact boundary, on binary-representable values so r == m to the bit:
        (0.50, 1.00, 0.50, MONO_LEAN, "r = m exactly -> called (sec. 3d says 'no margin' iff r < m)"),
        (0.00, 0.00, m, NO_MARGIN, "degenerate, both distances zero"),
    ]
    for d_mono, d_dia, mm, want, why in cases:
        got, r = call_verdict(d_mono, d_dia, mm)
        good = got == want
        ok &= good
        print(f"[selftest] d_mono={d_mono:.2f} d_dia={d_dia:.2f} m={mm:.2f} r={r:.3f} -> "
              f"{got:18s} {'OK ' if good else 'FAIL'}  ({why})")

    # the band in s-space is the OPEN interval of un-callable configurations
    lo, hi = band_in_s(m)
    inside = s_position(0.45, 0.50)
    outside = s_position(0.30, 0.50)
    good = lo < inside < hi and not (lo <= outside <= hi)
    ok &= good
    print(f"[selftest] s-band ({lo:.4f}, {hi:.4f}) contains {inside:.4f}, excludes "
          f"{outside:.4f}   {'OK ' if good else 'FAIL'}")

    # rescaling maps the poles to 0 and 1
    s4, s3 = s_position(0.0, 1.0), s_position(1.0, 0.0)
    good = abs(rescale(s4, s4, s3)) < 1e-12 and abs(rescale(s3, s4, s3) - 1) < 1e-12
    ok &= good
    print(f"[selftest] rescale maps pole (4)->0 and (3)->1                        "
          f"{'OK ' if good else 'FAIL'}")

    # a verdict must be one of exactly the three sec. 4 labels
    good = {c[3] for c in cases} <= {MONO_LEAN, DIA_LEAN, NO_MARGIN}
    ok &= good
    print(f"[selftest] verdict vocabulary is the three sec. 4 labels            "
          f"{'OK ' if good else 'FAIL'}")

    print("\n[selftest]", "ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


# --------------------------------------------------------------------------- main
def main():
    if not MARGINS.exists():
        print(f"REFUSING: {MARGINS} not found. Run scripts/freeze_placement_margins.py first - "
              f"the margin must be fixed before the placement is computed.")
        return 1
    missing = [str(p.relative_to(ROOT)) for p in (M1_C5, M2_C5) if not p.exists()]
    if missing:
        print("Cell 5 has not been scored yet. Missing:")
        for p in missing:
            print(f"  - {p}")
        print("\nRun, per RUN_CELL5.md in the repo root (cd into implementation/ first):")
        print("  M1:  .\\venv\\Scripts\\python.exe run_calibration.py 5 0 600")
        print("  M2:  .\\venv\\Scripts\\python.exe run_calibration.py 5 0 600")
        return 1

    mg = json.loads(MARGINS.read_text(encoding="utf-8"))
    m1_margin = mg["MARGIN_M1_nullB"]
    m2_margin = mg["MARGIN_M2_nullB"]

    rng = np.random.default_rng(SEED)
    c1 = load_m1()
    c2, m2_dropped = load_m2()
    curves = m2_curves(c2)

    r1 = place_m1(c1, m1_margin, rng)
    r2 = place_m2(c2, curves, m2_margin, rng)

    verdicts = [r1["verdict"], r2["verdict"]]
    called = [v for v in verdicts if v != NO_MARGIN]
    if len(set(verdicts)) == 1 and verdicts[0] != NO_MARGIN:
        pattern = f"BOTH METHODS AGREE: {verdicts[0]}"
        reading = ("Headline finding. Two unrelated measures concur. Per methods.md sec. 4 and "
                   "the 2026-07-22 clarification this is stated as a TWO-method concurrence, "
                   "weaker than the three-method concurrence sec. 4 was drafted against.")
    elif len(called) == 0:
        pattern = "BOTH METHODS: no clear margin"
        reading = ("Neither surviving method separates cell (5) from the two poles by more than "
                   "its own noise floor. This is a real result - cell (5) does not sit "
                   "distinguishably nearer either pole on either measure - not a failed analysis.")
    elif len(called) == 1:
        pattern = f"SPLIT: M1 {r1['verdict']}, M2 {r2['verdict']}"
        reading = ("One method calls a lean, the other cannot separate cell (5) from the poles. "
                   "Reported as the pattern, with both margins shown. Not resolved by a vote.")
    else:
        pattern = f"SPLIT: M1 {r1['verdict']}, M2 {r2['verdict']}"
        reading = ("The two methods point in opposite directions. Per sec. 4 this is read as "
                   "genuinely mixed evidence - cell (5) carrying some monologue-like and some "
                   "dialogue-like structure - and is a real result about reasoning traces, not a "
                   "failure of the study. No tie-break is applied.")

    s1, s2 = r1["s_raw"], r2["s_raw"]
    axis = {"method1": {c: rescale(s1[c], s1[MONO], s1[DIA]) for c in s1},
            "method2": {c: rescale(s2[c], s2[MONO], s2[DIA]) for c in s2}}
    band = {"method1": [rescale(b, s1[MONO], s1[DIA]) for b in band_in_s(m1_margin)],
            "method2": [rescale(b, s2[MONO], s2[DIA]) for b in band_in_s(m2_margin)]}

    payload = {"computed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "spec": "methods.md sec. 4 (placement) with sec. 3d margins, NULL-B",
               "margins_source": str(MARGINS.relative_to(ROOT)),
               "margins_frozen_at_utc": mg["frozen_at_utc"],
               "method1": r1, "method2": r2,
               "method3": {"verdict": "EXCLUDED - failed sec. 3e reliability gate "
                                      "(kappa = 0.5425 < 0.70); does not speak about cell (5)"},
               "pattern": pattern, "reading": reading,
               "normalised_axis_pole4_0_pole3_1": axis,
               "no_clear_margin_band_on_axis": band,
               "method2_docs_dropped_lt2_sentences": m2_dropped}

    L = [
        "CELL (5) ai_reasoning - PLACEMENT",
        "=" * 78,
        f"computed (UTC)   : {payload['computed_at_utc']}",
        f"margins frozen   : {mg['frozen_at_utc']}  (NULL-B, {MARGINS.name})",
        f"spec             : {payload['spec']}",
        "",
        "TABLE X - methods x {passed Step 1?, cell-(5) verdict, margin}",
        "-" * 78,
        f"{'method':34s} {'Step 1':>7s} {'d_mono':>8s} {'d_dia':>8s} {'r':>7s} {'m':>7s}",
        f"{'M1 style-change (author count)':34s} {'PASS':>7s} {r1['d_mono']:>8.4f} "
        f"{r1['d_dia']:>8.4f} {r1['r']:>7.4f} {r1['m']:>7.4f}",
        f"{'M2 stylometric step-change':34s} {'PASS':>7s} {r2['d_mono']:>8.4f} "
        f"{r2['d_dia']:>8.4f} {r2['r']:>7.4f} {r2['m']:>7.4f}",
        f"{'M3 dialogue-act tagging':34s} {'FAIL':>7s} {'-':>8s} {'-':>8s} {'-':>7s} {'-':>7s}",
        "",
        f"  M1 verdict : {r1['verdict']}   (bootstrap stability {r1['verdict_stability']:.1%})",
        f"  M2 verdict : {r2['verdict']}   (bootstrap stability {r2['verdict_stability']:.1%})",
        "  M3 verdict : excluded - failed the sec. 3e reliability gate (kappa = 0.5425 < 0.70)",
        "",
        "PATTERN (methods.md sec. 4 - reported, not voted)",
        "-" * 78,
        f"  {pattern}",
        "",
        f"  {reading}",
        "",
        "NORMALISED AXIS (pole (4) = 0, pole (3) = 1)  - Fig X.1",
        "-" * 78,
        f"{'cell':18s} {'M1':>10s} {'M2':>10s}",
    ]
    names = {"1": "(1) human_mono", "2": "(2) human_debate", "3": "(3) ai_debate [pole]",
             "4": "(4) ai_mono [pole]", "5": "(5) ai_reasoning *"}
    for c in ("4", "1", "2", "3", "5"):
        L.append(f"{names[c]:18s} {axis['method1'][c]:>10.4f} {axis['method2'][c]:>10.4f}")
    L += [
        "",
        f"  no-clear-margin band  M1: [{band['method1'][0]:.4f}, {band['method1'][1]:.4f}]",
        f"                        M2: [{band['method2'][0]:.4f}, {band['method2'][1]:.4f}]",
        "  cells (1) and (2) are context only - sec. 3d restricts the anchors to the AI pair.",
        "",
        "M2 LENGTH EXTRAPOLATION (descriptive - Fig M2.2)",
        "-" * 78,
    ]
    le = r2["length_extrapolation"]
    L += [f"  cell (5) median sentence pairs : {le['cell5_median_pairs']:.0f}",
          f"  cell (5) max sentence pairs    : {le['cell5_max_pairs']:.0f}",
          f"  pole (3) max / pole (4) max    : {le['pole3_max_pairs']:.0f} / "
          f"{le['pole4_max_pairs']:.0f}",
          f"  share of cell (5) beyond pole (3)'s observed max : "
          f"{le['cell5_share_beyond_pole3_max']:.1%}",
          f"  share of cell (5) beyond pole (4)'s observed max : "
          f"{le['cell5_share_beyond_pole4_max']:.1%}",
          "  Both pole curves are being extrapolated here; read the verdict with Fig M2.2.",
          ""]
    if m2_dropped:
        L.append(f"  [{m2_dropped} cell-(5) documents had < 2 sentences and were excluded]")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_TXT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {OUT_TXT.relative_to(ROOT)}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if sys.argv[1:] == ["--selftest"] else main())
