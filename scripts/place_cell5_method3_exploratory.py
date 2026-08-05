#!/usr/bin/env python3
"""EXPLORATORY: Method 3's reading of cell (5) ai_reasoning.

STATUS OF THIS SCRIPT - READ FIRST
----------------------------------
Method 3 failed its methods.md sec. 3e reliability gate (pooled Cohen's kappa = 0.5425, 95% CI
[0.4788, 0.6038], against a pre-registered bar of 0.70). By the pre-registration it therefore
takes no part in placing cell (5): sec. 4's confirmatory placement is Methods 1 and 2 only, and
that result is frozen (outputs/placement/cell5_placement.{txt,json}, 2026-07-22).

Everything this script produces is EXPLORATORY and is labelled as such in every artifact it
writes. It is descriptive: it reports where Method 3's three signals put cell (5) if the method
is applied anyway. It is standalone - it was computed after the M1/M2 split was already known,
and it resolves nothing about that split.

Two further reasons the output is exploratory rather than confirmatory:

  1. The reliability gate failed, so the tagger's labels are not established as accurate.
  2. THE MARGIN IS POST-HOC. For Methods 1 and 2 the placement margin `m` was frozen on
     2026-07-22T15:53:42Z, before any cell-(5) statistic existed
     (outputs/placement/margins_frozen.json records both cell-(5) output files as absent at
     freeze time). Method 3 never reached placement, so no Method 3 margin was ever frozen. The
     margins here are computed now, on 2026-07-23, with the M1/M2 answer already on screen. The
     bootstrap procedure itself uses only cells (3) and (4) and its seed is fixed below, but the
     firewall property the M1/M2 margins have is one this script does not have.

WHAT IS COMPUTED (methods.md sec. 3a-3d, unchanged)
---------------------------------------------------
Three signals, each placed by the same nearest-anchor rule, anchors (4) = monologue pole and
(3) = dialogue pole:

  signal a  unigram DA-tag distribution (28 labels)       d(X, pole) = JSD(X, pole), base 2
  signal b  joint-normalized bigram distribution (28x28)  d(X, pole) = JSD(X, pole), base 2
  signal c  adjacency-pair completion rate  [PRIMARY]     d(X, pole) = |mean(X) - mean(pole)|

  r       = |d_mono - d_dia| / max(d_mono, d_dia)
  verdict = "no clear margin"    if r < m
            "monologue-leaning"  if r >= m and d_mono < d_dia
            "dialogue-leaning"   if r >= m and d_dia < d_mono

MARGINS (methods.md sec. 3d, same two nulls as scripts/freeze_placement_margins.py)
-----------------------------------------------------------------------------------
NULL-A (literal sec. 3d): split a pole into equal disjoint halves, measure each half's distance
to the opposite pole, record the relative gap. Pure anchor-side sampling noise.

NULL-B (the corrected null, and the one the frozen M1/M2 placement uses per STATUS.md
2026-07-22): build a probe that is equidistant from both poles by construction out of pole
documents, then let every noise source act - the probe and both anchors are resampled each
iteration. For signal c the distance is a mean difference, so a 50/50 document mixture is exactly
equidistant. For signals a and b the distance is a JSD, which is not linear in the mixing
proportion, so the proportion is solved numerically by bisection on the pooled pole
distributions (solve_mix_p_jsd); the two distances are equal at the returned p to ~1e-12.
m = 95th percentile of the null's r. NULL-B is reported as the margin; NULL-A is carried
alongside so the size of the correction stays visible.

Cell (5)'s tags already exist and are not re-tagged. Nothing here writes into the confirmatory
placement outputs, into Table X, or into Fig X.1.

Usage (from the repo root):
    python scripts/place_cell5_method3_exploratory.py
    python scripts/place_cell5_method3_exploratory.py --selftest
"""
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "methods" / "3_dialogue_act_tagging" / "implementation"))
import signals as S                                                       # noqa: E402

OUTDIR = ROOT / "outputs" / "placement"
OUT_TXT = OUTDIR / "cell5_method3_exploratory.txt"
OUT_JSON = OUTDIR / "cell5_method3_exploratory.json"
CACHE = ROOT / "outputs" / "method3" / "_tag_cache"
NPZ = CACHE / "count_matrices.npz"
STAMP = CACHE / "count_matrices_verified.json"

DIA, MONO, TARGET = "3", "4", "5"
CONTEXT = ("1", "2")
ALL_CELLS = ("1", "2", "3", "4", "5")

B_ITERS = 1000            # margin null draws, as in freeze_placement_margins.py
BOOT = 2000               # verdict-stability draws, as in place_cell5.py
PERCENTILE = 95
SEED = 20260723           # this run's seed; the M1/M2 freeze used 20260722

MONO_LEAN, DIA_LEAN, NO_MARGIN = "monologue-leaning", "dialogue-leaning", "no clear margin"

KAPPA = 0.5425
KAPPA_CI = (0.4788, 0.6038)
KAPPA_BAR = 0.70


# --------------------------------------------------------------------------- the call
def call_verdict(d_mono, d_dia, m):
    """methods.md sec. 3d 'Call'. Returns (verdict, relative gap r)."""
    hi = max(d_mono, d_dia)
    r = abs(d_mono - d_dia) / hi if hi > 0 else 0.0
    if r < m:
        return NO_MARGIN, r
    return (MONO_LEAN if d_mono < d_dia else DIA_LEAN), r


def rel_gap(da, db):
    hi = max(da, db)
    return abs(da - db) / hi if hi > 0 else 0.0


def s_position(d_mono, d_dia):
    tot = d_mono + d_dia
    return d_mono / tot if tot > 0 else 0.5


def rescale(s, s_mono_pole, s_dia_pole):
    den = s_dia_pole - s_mono_pole
    return (s - s_mono_pole) / den if den != 0 else float("nan")


def band_in_s(m):
    return (1 - m) / (2 - m), 1 / (2 - m)


def _halves(n, rng):
    idx = rng.permutation(n)
    h = n // 2
    return idx[:h], idx[h:2 * h]


# --------------------------------------------------------------------------- loading
def tag_fingerprint(cell):
    """The file-count + mtime fingerprint signals.load_cell_tags caches on (full re-stat)."""
    d = S.OUTBASE / S.CELL_DIRS[cell]
    files = sorted(d.glob("*.jsonl"))
    return f"{len(files)}:{sum(fp.stat().st_mtime_ns for fp in files)}"


def recorded_fingerprint(cell):
    """The fingerprint signals.load_cell_tags itself recorded when it last read this cell.

    Reading it costs one small file open, where re-stat-ing the ~2900 tag files takes tens of
    seconds. The recorded value is written by signals.load_cell_tags after a full re-stat, and
    a full re-stat happens again whenever the count matrices are rebuilt (--build-cache) or
    verified against signals.py (--selftest), so the cheap read is a key, not the check.
    """
    fp = S.CACHE_DIR / f"cell{cell}.json"
    if fp.exists():
        with open(fp, encoding="utf-8") as f:
            head = f.read(4096)
        i = head.find('"fingerprint"')
        if i >= 0:
            j = head.find('"', head.find(":", i) + 1)
            k = head.find('"', j + 1)
            return head[j + 1:k]
    return tag_fingerprint(cell)


def _build_cell(c):
    docs, n_bad = S.load_cell_tags(c)
    uni = np.zeros((len(docs), S.N_TAGS))
    big = np.zeros((len(docs), S.N_TAGS * S.N_TAGS))
    for i, d in enumerate(docs):
        for t in d["tags"]:
            uni[i, S.TAG_IDX[t]] += 1
        for a, b in zip(d["tags"], d["tags"][1:]):
            big[i, S.TAG_IDX[a] * S.N_TAGS + S.TAG_IDX[b]] += 1
    rates, n_absent, n_docs = S.cell_completion_rates(docs)
    return {"uni": uni, "big": big, "rates": np.array(rates, float),
            "n_docs": n_docs, "n_absent": n_absent, "n_bad": n_bad,
            "n_sentences": int(uni.sum())}


SCRATCH = Path(tempfile.gettempdir()) / "m3_count_matrices"


def build_cache():
    """Build the per-document count matrices and write the .npz cache.

    Resumable one cell at a time: each cell's matrices are staged in local scratch first, so a
    run that is interrupted can be repeated and will pick up where it stopped. Nothing here
    re-tags anything - it only re-reads tags that already exist.
    """
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for c in ALL_CELLS:
        fp_out = SCRATCH / f"cell{c}.npz"
        if fp_out.exists():
            print(f"  cell {c}: staged already")
            continue
        print(f"  cell {c}: building...", flush=True)
        d = _build_cell(c)
        np.savez_compressed(fp_out, uni=d["uni"].astype(np.uint32),
                            big=d["big"].astype(np.uint32), rates=d["rates"],
                            ndocs=d["n_docs"], nabs=d["n_absent"], nbad=d["n_bad"],
                            nsent=d["n_sentences"], fp=tag_fingerprint(c))
        print(f"  cell {c}: staged ({d['n_docs']} docs, {d['n_sentences']} sentences)")
        return False                       # one cell per invocation keeps each run short
    payload = {}
    for c in ALL_CELLS:
        z = np.load(SCRATCH / f"cell{c}.npz", allow_pickle=False)
        for k in ("uni", "big", "rates", "ndocs", "nabs", "nbad", "nsent", "fp"):
            payload[f"{k}_{c}"] = z[k]
    merged = Path(tempfile.gettempdir()) / "m3_count_matrices.npz"
    np.savez_compressed(merged, **payload)
    CACHE.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(merged, NPZ)
    print(f"  wrote {NPZ.relative_to(ROOT)}")
    return True


def load_counts():
    """Per-document count vectors for every cell.

    Returns dict cell -> {"uni": (n_docs, 28), "big": (n_docs, 784), "rates": (n_defined,),
                          "n_docs": int, "n_absent": int, ...}.

    Pooling a set of documents is then a plain row-sum, which reproduces signals.cell_unigram /
    signals.cell_bigram exactly (both sum raw counts across a cell's documents and normalize
    once at the end) and makes the bootstrap cheap. verify_against_signals() checks that
    equality on the real tags; --selftest runs it and records the result in the stamp file.
    """
    if not NPZ.exists():
        raise SystemExit(f"missing {NPZ.relative_to(ROOT)} - run with --build-cache first "
                         f"(repeat until it reports the cache is complete).")
    z = np.load(NPZ, allow_pickle=False)
    stale = [c for c in ALL_CELLS if str(z[f"fp_{c}"]) != recorded_fingerprint(c)]
    if stale:
        raise SystemExit(f"count-matrix cache is stale for cell(s) {stale} - delete "
                         f"{NPZ.relative_to(ROOT)} and rebuild with --build-cache.")
    return {c: {"uni": z[f"uni_{c}"].astype(float), "big": z[f"big_{c}"].astype(float),
                "rates": z[f"rates_{c}"], "n_docs": int(z[f"ndocs_{c}"]),
                "n_absent": int(z[f"nabs_{c}"]), "n_bad": int(z[f"nbad_{c}"]),
                "n_sentences": int(z[f"nsent_{c}"])} for c in ALL_CELLS}


def pooled(counts_matrix, idx=None):
    """Sum count rows and normalize to a probability vector."""
    v = counts_matrix.sum(axis=0) if idx is None else counts_matrix[idx].sum(axis=0)
    s = v.sum()
    return v / s if s > 0 else v


# ------------------------------------------------- vectorized bootstrap helpers
def draw_counts(mat, n_sample, n_draws, rng):
    """Unnormalized pooled counts for `n_draws` independent with-replacement samples of
    `n_sample` documents. Equivalent to summing the sampled rows one draw at a time; done as
    one matrix product so 1000-2000 draws over a 784-dimensional profile stay cheap."""
    n = mat.shape[0]
    idx = rng.integers(0, n, size=(n_draws, n_sample))
    w = np.zeros((n_draws, n))
    for i in range(n_draws):
        w[i] = np.bincount(idx[i], minlength=n)
    return w @ mat


def normalize_rows(counts):
    s = counts.sum(axis=1, keepdims=True)
    return np.divide(counts, s, out=np.zeros_like(counts), where=s > 0)


def jsd_rows(P, Q):
    """Row-wise Jensen-Shannon divergence, base 2 - the vectorized twin of signals.jsd.
    --selftest checks the two agree to machine precision on real cell profiles."""
    P = np.atleast_2d(P); Q = np.atleast_2d(Q)
    M = 0.5 * (P + Q)

    def kl(X):
        t = np.zeros_like(X)
        mask = X > 0
        t[mask] = X[mask] * np.log(X[mask] / M[mask])
        return t.sum(axis=1)

    return (0.5 * kl(P) + 0.5 * kl(Q)) / np.log(2)


def rel_gap_rows(da, db):
    hi = np.maximum(da, db)
    return np.divide(np.abs(da - db), hi, out=np.zeros_like(da), where=hi > 0)


# --------------------------------------------------------------------------- verification
def verify_against_signals(cells):
    """The count matrices must reproduce signals.py's own cell-level statistics exactly."""
    ok = True
    for c in ALL_CELLS:
        docs, _ = S.load_cell_tags(c)
        u_ref = S.cell_unigram(docs)
        b_ref = S.cell_bigram(docs)[1].flatten()
        du = float(np.max(np.abs(u_ref - pooled(cells[c]["uni"]))))
        db = float(np.max(np.abs(b_ref - pooled(cells[c]["big"]))))
        good = du < 1e-12 and db < 1e-12
        ok &= good
        print(f"  cell {c}: max|unigram diff| = {du:.2e}   max|bigram diff| = {db:.2e}   "
              f"{'OK' if good else 'MISMATCH'}")
    return bool(ok)


def write_stamp(ok):
    """Record that the count matrices were checked against signals.py, against the tag
    fingerprints they were checked at, so the check does not have to be repeated on every run
    and cannot silently carry over to different tags."""
    CACHE.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(json.dumps(
        {"verified_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "ok": bool(ok), "checked_by": "place_cell5_method3_exploratory.py --selftest",
         "fingerprints": {c: recorded_fingerprint(c) for c in ALL_CELLS}}, indent=2),
        encoding="utf-8")


def stamp_status():
    """(valid, message) - valid only if the stamp passed and the tags have not moved since."""
    if not STAMP.exists():
        return False, "no verification stamp on disk"
    d = json.loads(STAMP.read_text(encoding="utf-8"))
    if not d.get("ok"):
        return False, "stamp records a FAILED verification"
    for c in ALL_CELLS:
        if d.get("fingerprints", {}).get(c) != recorded_fingerprint(c):
            return False, f"tags for cell {c} changed since the stamp was written"
    return True, f"verified {d['verified_at_utc']} by {d['checked_by']}"


# --------------------------------------------------------------------------- margins
def solve_mix_p_jsd(mat_dia, mat_mono, tol=1e-14, iters=200):
    """Mixing proportion p of DIALOGUE-pole mass that makes a mixture equidistant under JSD.

    The mixture distribution is p * dist(3) + (1 - p) * dist(4). JSD is not linear in p, but
    f(p) = JSD(mix_p, dia) - JSD(mix_p, mono) is continuous, f(0) = D - 0 > 0 and f(1) = 0 - D < 0
    (with D = JSD(3, 4) > 0), so a bisection converges to the unique sign change. No tuning: the
    bracket is the whole interval [0, 1] and the tolerance is machine-level.
    """
    p_dia, p_mono = pooled(mat_dia), pooled(mat_mono)

    def f(p):
        mix = p * p_dia + (1 - p) * p_mono
        return S.jsd(mix, p_dia) - S.jsd(mix, p_mono)

    lo, hi = 0.0, 1.0
    if f(lo) * f(hi) > 0:
        return 0.5
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def nullA_jsd(mat_dia, mat_mono, rng):
    """Literal sec. 3d: same-pole halves, each measured against the opposite pole."""
    out = []
    for own, other in ((mat_dia, mat_mono), (mat_mono, mat_dia)):
        ref = pooled(other)
        A = np.empty((B_ITERS, own.shape[1]))
        Bm = np.empty((B_ITERS, own.shape[1]))
        for i in range(B_ITERS):
            ia, ib = _halves(len(own), rng)
            A[i] = own[ia].sum(axis=0)
            Bm[i] = own[ib].sum(axis=0)
        A, Bm = normalize_rows(A), normalize_rows(Bm)
        R = np.tile(ref, (B_ITERS, 1))
        out.append(rel_gap_rows(jsd_rows(A, R), jsd_rows(Bm, R)))
    return np.concatenate(out)


def nullB_jsd(mat_dia, mat_mono, n5, rng):
    """Equidistant-by-construction probe; probe and both anchors resampled every iteration."""
    p = solve_mix_p_jsd(mat_dia, mat_mono)
    n_from_dia = int(round(p * n5))
    n_from_mono = n5 - n_from_dia
    probe = normalize_rows(draw_counts(mat_dia, n_from_dia, B_ITERS, rng)
                           + draw_counts(mat_mono, n_from_mono, B_ITERS, rng))
    a_d = normalize_rows(draw_counts(mat_dia, len(mat_dia), B_ITERS, rng))
    a_m = normalize_rows(draw_counts(mat_mono, len(mat_mono), B_ITERS, rng))
    return rel_gap_rows(jsd_rows(probe, a_m), jsd_rows(probe, a_d)), p      # (d_mono, d_dia)


def nullA_scalar(x_dia, x_mono, rng):
    out = []
    for own, other in ((x_dia, x_mono), (x_mono, x_dia)):
        ref = float(np.mean(other))
        for _ in range(B_ITERS):
            ia, ib = _halves(len(own), rng)
            out.append(rel_gap(abs(float(np.mean(own[ia])) - ref),
                               abs(float(np.mean(own[ib])) - ref)))
    return np.array(out)


def nullB_scalar(x_dia, x_mono, n5, rng):
    """A 50/50 document mixture has a mean exactly midway between the pole means."""
    half = n5 // 2
    out = np.empty(B_ITERS)
    for i in range(B_ITERS):
        probe = np.concatenate([rng.choice(x_dia, half, replace=True),
                                rng.choice(x_mono, n5 - half, replace=True)])
        a_d = rng.choice(x_dia, len(x_dia), replace=True)
        a_m = rng.choice(x_mono, len(x_mono), replace=True)
        mp = float(np.mean(probe))
        out[i] = rel_gap(abs(mp - float(np.mean(a_m))), abs(mp - float(np.mean(a_d))))
    return out, 0.5


def summarise(null):
    return {"m": float(np.percentile(null, PERCENTILE)),
            "median": float(np.median(null)),
            "p99": float(np.percentile(null, 99)),
            "max": float(np.max(null)),
            "n_draws": int(len(null))}


# --------------------------------------------------------------------------- placement
def place_jsd(cells, key, m, rng):
    mat = {c: cells[c][key] for c in ALL_CELLS}
    p_dia, p_mono = pooled(mat[DIA]), pooled(mat[MONO])
    d_mono = S.jsd(pooled(mat[TARGET]), p_mono)
    d_dia = S.jsd(pooled(mat[TARGET]), p_dia)
    verdict, r = call_verdict(d_mono, d_dia, m)

    b5 = normalize_rows(draw_counts(mat[TARGET], len(mat[TARGET]), BOOT, rng))
    b_d = normalize_rows(draw_counts(mat[DIA], len(mat[DIA]), BOOT, rng))
    b_m = normalize_rows(draw_counts(mat[MONO], len(mat[MONO]), BOOT, rng))
    bm_dist, bd_dist = jsd_rows(b5, b_m), jsd_rows(b5, b_d)
    flips = sum(call_verdict(bm_dist[i], bd_dist[i], m)[0] != verdict for i in range(BOOT))

    per_cell = {c: {"d_mono": S.jsd(pooled(mat[c]), p_mono),
                    "d_dia": S.jsd(pooled(mat[c]), p_dia)} for c in ALL_CELLS}
    s_raw = {c: s_position(per_cell[c]["d_mono"], per_cell[c]["d_dia"]) for c in ALL_CELLS}
    return {"d_mono": d_mono, "d_dia": d_dia, "r": r, "m": m, "verdict": verdict,
            "verdict_stability": 1 - flips / BOOT,
            "pole_to_pole": S.jsd(p_dia, p_mono),
            "per_cell_distances": per_cell, "s_raw": s_raw}


def place_scalar(cells, m, rng):
    x = {c: cells[c]["rates"] for c in ALL_CELLS}
    mu = {c: float(np.mean(x[c])) for c in ALL_CELLS}
    d_mono = abs(mu[TARGET] - mu[MONO])
    d_dia = abs(mu[TARGET] - mu[DIA])
    verdict, r = call_verdict(d_mono, d_dia, m)

    flips = 0
    for _ in range(BOOT):
        b5 = rng.choice(x[TARGET], len(x[TARGET]), replace=True)
        b_d = rng.choice(x[DIA], len(x[DIA]), replace=True)
        b_m = rng.choice(x[MONO], len(x[MONO]), replace=True)
        mb = float(np.mean(b5))
        v, _ = call_verdict(abs(mb - float(np.mean(b_m))), abs(mb - float(np.mean(b_d))), m)
        flips += (v != verdict)

    per_cell = {c: {"d_mono": abs(mu[c] - mu[MONO]), "d_dia": abs(mu[c] - mu[DIA])}
                for c in ALL_CELLS}
    s_raw = {c: s_position(per_cell[c]["d_mono"], per_cell[c]["d_dia"]) for c in ALL_CELLS}
    return {"d_mono": d_mono, "d_dia": d_dia, "r": r, "m": m, "verdict": verdict,
            "verdict_stability": 1 - flips / BOOT,
            "cell_means": mu,
            "cell_fpp_absent_share": {c: cells[c]["n_absent"] / cells[c]["n_docs"]
                                      for c in ALL_CELLS},
            "cell_defined_n": {c: int(len(x[c])) for c in ALL_CELLS},
            "pole_to_pole": abs(mu[DIA] - mu[MONO]),
            "per_cell_distances": per_cell, "s_raw": s_raw}


# --------------------------------------------------------------------------- selftest
def selftest():
    """Machinery checks on inputs whose answer is known in advance. Writes nothing."""
    ok = True

    assert call_verdict(0.4, 0.4, 0.2)[0] == NO_MARGIN
    assert call_verdict(0.10, 0.90, 0.2)[0] == MONO_LEAN
    assert call_verdict(0.90, 0.10, 0.2)[0] == DIA_LEAN
    assert call_verdict(0.0, 0.0, 0.2)[0] == NO_MARGIN
    # exact r == m boundary, on binary-representable values: r = 0.5, m = 0.5 -> called
    assert call_verdict(0.25, 0.5, 0.5)[0] == MONO_LEAN
    assert call_verdict(0.25, 0.5, 0.5 + 1e-12)[0] == NO_MARGIN
    print("[selftest] verdict vocabulary, r == m boundary, degenerate case   OK")

    assert abs(rel_gap(0.5, 0.25) - 0.5) < 1e-12 and rel_gap(0.3, 0.3) == 0.0
    lo, hi = band_in_s(0.3615)
    assert lo < 0.5 < hi
    print("[selftest] rel_gap and no-clear-margin band                        OK")

    rng = np.random.default_rng(0)
    ia, ib = _halves(591, rng)
    assert len(ia) == len(ib) == 295 and not (set(ia.tolist()) & set(ib.tolist()))
    print("[selftest] _halves equal-sized and disjoint                        OK")

    # JSD: zero on identical inputs, symmetric, bounded by 1 for disjoint support
    p = np.array([0.5, 0.3, 0.2]); q = np.array([0.1, 0.1, 0.8])
    assert abs(S.jsd(p, p)) < 1e-12 and abs(S.jsd(p, q) - S.jsd(q, p)) < 1e-12
    assert abs(S.jsd(np.array([1.0, 0.0]), np.array([0.0, 1.0])) - 1.0) < 1e-12
    print("[selftest] jsd zero/symmetric/bounded                              OK")

    # solve_mix_p_jsd really does equalise the two distances
    d_mat = np.array([[80.0, 10.0, 10.0]])
    m_mat = np.array([[5.0, 5.0, 90.0]])
    p = solve_mix_p_jsd(d_mat, m_mat)
    mix = p * pooled(d_mat) + (1 - p) * pooled(m_mat)
    gap = abs(S.jsd(mix, pooled(d_mat)) - S.jsd(mix, pooled(m_mat)))
    print(f"[selftest] solve_mix_p_jsd p={p:.6f} -> |d_dia - d_mono| = {gap:.2e}   "
          f"{'OK' if gap < 1e-10 else 'FAIL'}")
    ok &= gap < 1e-10

    # synthetic scalar poles: an equidistant probe must not be called under NULL-B,
    # an at-pole probe must be.
    r0 = np.random.default_rng(1)
    x_d, x_m = r0.normal(2.0, 0.8, 600), r0.normal(1.0, 0.8, 600)
    mA = summarise(nullA_scalar(x_d, x_m, np.random.default_rng(2)))["m"]
    nb, _ = nullB_scalar(x_d, x_m, 600, np.random.default_rng(2))
    mB = summarise(nb)["m"]
    print(f"[selftest] scalar margins   m(NULL-A)={mA:.4f}  m(NULL-B)={mB:.4f}")
    fp = 0
    for _ in range(300):
        pr = float(np.mean(r0.normal(1.5, 0.8, 600)))
        if rel_gap(abs(pr - float(np.mean(x_m))), abs(pr - float(np.mean(x_d)))) >= mB:
            fp += 1
    print(f"[selftest] NULL-B false-positive rate on equidistant probes: {fp / 300:.1%}  "
          f"(target <= 5%)   {'OK' if fp / 300 <= 0.10 else 'FAIL'}")
    ok &= fp / 300 <= 0.10
    at_pole = float(np.mean(r0.normal(1.0, 0.8, 600)))
    called = rel_gap(abs(at_pole - float(np.mean(x_m))),
                     abs(at_pole - float(np.mean(x_d)))) >= mB
    print(f"[selftest] at-pole probe called under NULL-B: {called}   "
          f"{'OK' if called else 'FAIL (margin too blunt)'}")
    ok &= called

    # JSD null on synthetic profiles: a probe built at the solved proportion is not called
    r1 = np.random.default_rng(3)
    base_d = np.array([0.40, 0.25, 0.20, 0.15])
    base_m = np.array([0.10, 0.15, 0.30, 0.45])
    D = np.array([r1.multinomial(60, base_d) for _ in range(300)], float)
    M = np.array([r1.multinomial(60, base_m) for _ in range(300)], float)
    nbj, pj = nullB_jsd(D, M, 300, np.random.default_rng(4))
    mBj = summarise(nbj)["m"]
    probe_idx_d = r1.choice(len(D), int(round(pj * 300)), replace=True)
    probe_idx_m = r1.choice(len(M), 300 - int(round(pj * 300)), replace=True)
    pv = D[probe_idx_d].sum(axis=0) + M[probe_idx_m].sum(axis=0)
    pv = pv / pv.sum()
    rj = rel_gap(S.jsd(pv, pooled(M)), S.jsd(pv, pooled(D)))
    print(f"[selftest] jsd NULL-B p={pj:.4f}  m={mBj:.4f}  equidistant probe r={rj:.4f} -> "
          f"{'no clear margin  OK' if rj < mBj else 'CALLED (false positive)  FAIL'}")
    ok &= rj < mBj

    # count matrices reproduce signals.py on the real tags
    print("[selftest] count matrices vs signals.py:")
    cells = load_counts()
    v_ok = verify_against_signals(cells)
    ok &= v_ok
    write_stamp(v_ok)
    print(f"[selftest] verification stamp written to "
          f"{STAMP.relative_to(ROOT)}                   OK")

    # the vectorized helpers must agree with signals.jsd and with pooled() exactly
    p3, p4 = pooled(cells[DIA]["uni"]), pooled(cells[MONO]["uni"])
    dv = abs(float(jsd_rows(p3, p4)[0]) - S.jsd(p3, p4))
    q3, q4 = pooled(cells[DIA]["big"]), pooled(cells[MONO]["big"])
    dv = max(dv, abs(float(jsd_rows(q3, q4)[0]) - S.jsd(q3, q4)))
    print(f"[selftest] jsd_rows vs signals.jsd            max diff = {dv:.2e}   "
          f"{'OK' if dv < 1e-12 else 'FAIL'}")
    ok &= dv < 1e-12

    r2 = np.random.default_rng(7)
    mat = cells[MONO]["uni"]
    idx = r2.integers(0, len(mat), size=(3, len(mat)))
    w = np.zeros((3, len(mat)))
    for i in range(3):
        w[i] = np.bincount(idx[i], minlength=len(mat))
    dc = normalize_rows(w @ mat)
    ref = np.array([pooled(mat, idx[i]) for i in range(3)])
    dd = float(np.max(np.abs(dc - ref)))
    print(f"[selftest] draw_counts vs row-sum pooling     max diff = {dd:.2e}   "
          f"{'OK' if dd < 1e-12 else 'FAIL'}")
    ok &= dd < 1e-12

    print("\n[selftest]", "ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


# --------------------------------------------------------------------------- report
BANNER = (
    "EXPLORATORY - NOT A CONFIRMATORY RESULT\n"
    "Method 3 failed the methods.md sec. 3e reliability gate "
    f"(kappa = {KAPPA:.4f}, 95% CI [{KAPPA_CI[0]:.4f}, {KAPPA_CI[1]:.4f}], bar {KAPPA_BAR:.2f}).\n"
    "The confirmatory placement of cell (5) is Methods 1 and 2 only and is frozen in\n"
    "outputs/placement/cell5_placement.{txt,json}. Nothing below enters Table X or Fig X.1,\n"
    "and nothing below resolves the M1/M2 split.\n"
    "The margins here are POST-HOC: they were computed on 2026-07-23, after the M1/M2 result\n"
    "was known. The M1/M2 margins were frozen 2026-07-22T15:53:42Z, before cell (5) existed."
)


def main():
    rng = np.random.default_rng(SEED)
    print("Loading Method 3 tags (already tagged; nothing is re-tagged here)...")
    cells = load_counts()
    for c in ALL_CELLS:
        print(f"  cell {c} ({S.CELL_LABEL[c]:16s}) docs={cells[c]['n_docs']:4d}  "
              f"sentences={cells[c]['n_sentences']:6d}  "
              f"FPP-absent={cells[c]['n_absent']:3d}  "
              f"mean completion rate={np.mean(cells[c]['rates']):.4f}")

    valid, msg = stamp_status()
    if valid:
        print(f"\nCount matrices vs signals.py: {msg}")
    else:
        print(f"\nVerifying the count matrices against signals.py ({msg})...")
        v_ok = verify_against_signals(cells)
        write_stamp(v_ok)
        if not v_ok:
            print("ABORT: count matrices do not reproduce signals.py.")
            return 1

    n5_docs = cells[TARGET]["n_docs"]
    n5_rates = len(cells[TARGET]["rates"])

    print(f"\nComputing post-hoc margins ({B_ITERS} draws per null, cells (3)/(4) only)...")
    margins = {}
    nA = summarise(nullA_jsd(cells[DIA]["uni"], cells[MONO]["uni"], rng))
    nB, p_uni = nullB_jsd(cells[DIA]["uni"], cells[MONO]["uni"], n5_docs, rng)
    margins["a_unigram"] = {"nullA": nA, "nullB": summarise(nB), "mix_p": p_uni}
    print(f"  signal a (unigram)   NULL-A m={nA['m']:.4f}   "
          f"NULL-B m={margins['a_unigram']['nullB']['m']:.4f}  (mix p={p_uni:.4f})")

    nA = summarise(nullA_jsd(cells[DIA]["big"], cells[MONO]["big"], rng))
    nB, p_big = nullB_jsd(cells[DIA]["big"], cells[MONO]["big"], n5_docs, rng)
    margins["b_bigram"] = {"nullA": nA, "nullB": summarise(nB), "mix_p": p_big}
    print(f"  signal b (bigram)    NULL-A m={nA['m']:.4f}   "
          f"NULL-B m={margins['b_bigram']['nullB']['m']:.4f}  (mix p={p_big:.4f})")

    nA = summarise(nullA_scalar(cells[DIA]["rates"], cells[MONO]["rates"], rng))
    nB, p_com = nullB_scalar(cells[DIA]["rates"], cells[MONO]["rates"], n5_rates, rng)
    margins["c_completion"] = {"nullA": nA, "nullB": summarise(nB), "mix_p": p_com}
    print(f"  signal c (completion) NULL-A m={nA['m']:.4f}   "
          f"NULL-B m={margins['c_completion']['nullB']['m']:.4f}  (mix p={p_com:.4f})")

    print(f"\nPlacing cell (5) on each signal ({BOOT} bootstrap draws for stability)...")
    res = {
        "a_unigram": place_jsd(cells, "uni", margins["a_unigram"]["nullB"]["m"], rng),
        "b_bigram": place_jsd(cells, "big", margins["b_bigram"]["nullB"]["m"], rng),
        "c_completion": place_scalar(cells, margins["c_completion"]["nullB"]["m"], rng),
    }

    label = {"a_unigram": "signal a  unigram JSD",
             "b_bigram": "signal b  bigram JSD",
             "c_completion": "signal c  completion rate [primary]"}
    order = ["a_unigram", "b_bigram", "c_completion"]

    lines = []
    w = lines.append
    w("CELL (5) ai_reasoning - METHOD 3 READING")
    w("=" * 78)
    w(BANNER)
    w("=" * 78)
    w(f"computed (UTC)   : {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    w(f"seed             : {SEED}")
    w("spec             : methods.md sec. 3a-3c signals, sec. 3d comparison rule")
    w("margin null      : NULL-B (as used by the frozen M1/M2 placement); NULL-A shown alongside")
    w("")
    w("DOCUMENT COUNTS AND DESCRIPTIVE COMPLETION RATES (all five cells)")
    w("-" * 78)
    w(f"{'cell':22s} {'docs':>5s} {'sentences':>10s} {'FPP-absent':>11s} "
      f"{'defined n':>10s} {'mean rate':>10s}")
    for c in ALL_CELLS:
        cc = cells[c]
        w(f"({c}) {S.CELL_LABEL[c]:18s} {cc['n_docs']:5d} {cc['n_sentences']:10d} "
          f"{cc['n_absent']:5d} ({cc['n_absent'] / cc['n_docs']:5.1%}) "
          f"{len(cc['rates']):10d} {np.mean(cc['rates']):10.4f}")
    w("")
    w("EXPLORATORY PLACEMENT - three signals, anchors (4) = monologue, (3) = dialogue")
    w("-" * 78)
    w(f"{'signal':34s} {'d_mono':>8s} {'d_dia':>8s} {'r':>7s} {'m':>7s}  verdict")
    for k in order:
        v = res[k]
        w(f"{label[k]:34s} {v['d_mono']:8.4f} {v['d_dia']:8.4f} {v['r']:7.4f} "
          f"{v['m']:7.4f}  {v['verdict']} (exploratory)")
    w("")
    for k in order:
        v = res[k]
        w(f"  {label[k]:34s} bootstrap stability {v['verdict_stability']:6.1%}   "
          f"pole-to-pole distance {v['pole_to_pole']:.4f}")
    w("")
    w("MARGINS - POST-HOC (computed 2026-07-23, after the M1/M2 result was known)")
    w("-" * 78)
    w(f"{'signal':34s} {'NULL-A m':>9s} {'NULL-B m':>9s} {'mix p':>7s}  "
      f"{'NULL-B median':>13s}")
    for k in order:
        mm = margins[k]
        w(f"{label[k]:34s} {mm['nullA']['m']:9.4f} {mm['nullB']['m']:9.4f} "
          f"{mm['mix_p']:7.4f} {mm['nullB']['median']:13.4f}")
    w("  NULL-B is the reported margin, matching the frozen M1/M2 placement (STATUS.md")
    w("  2026-07-22). Both nulls use cells (3) and (4) only.")
    w("")
    w("NORMALISED AXIS (pole (4) = 0, pole (3) = 1)  - exploratory, for Fig M3.4/M3.3")
    w("-" * 78)
    w(f"{'cell':22s} " + " ".join(f"{label[k].split()[1]:>12s}" for k in order))
    for c in ALL_CELLS:
        row = []
        for k in order:
            s = res[k]["s_raw"]
            row.append(f"{rescale(s[c], s[MONO], s[DIA]):12.4f}")
        star = " *" if c == TARGET else ""
        w(f"({c}) {S.CELL_LABEL[c]:16s}{star:2s} " + " ".join(row))
    w("")
    for k in order:
        lo, hi = band_in_s(res[k]["m"])
        s = res[k]["s_raw"]
        lo_r, hi_r = rescale(lo, s[MONO], s[DIA]), rescale(hi, s[MONO], s[DIA])
        w(f"  no-clear-margin band  {label[k]:34s} [{lo_r:.4f}, {hi_r:.4f}]")
    w("  cells (1) and (2) are context only - sec. 3d restricts the anchors to the AI pair.")
    w("")
    w("READING THIS")
    w("-" * 78)
    w("  Method 3's labels are not established as accurate: the tagger/rater agreement is")
    w(f"  kappa = {KAPPA:.4f} against a pre-registered bar of {KAPPA_BAR:.2f}. The placement above")
    w("  inherits that uncertainty in full. It is reported as a description of what this")
    w("  method's signals say, and it stands beside the confirmatory M1/M2 result rather")
    w("  than adjudicating it.")
    w("")
    w("=" * 78)
    w("EXPLORATORY OUTPUT - see the banner at the top of this file.")

    text = "\n".join(lines)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT_TXT.write_text(text + "\n", encoding="utf-8")

    payload = {
        "status": "EXPLORATORY",
        "banner": BANNER,
        "confirmatory": False,
        "enters_table_x": False,
        "enters_fig_x1": False,
        "margin_frozen_before_target": False,
        "margin_computed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "b_iters": B_ITERS,
        "boot_stability_draws": BOOT,
        "kappa": KAPPA, "kappa_ci": list(KAPPA_CI), "kappa_bar": KAPPA_BAR,
        "cells": {c: {"n_docs": cells[c]["n_docs"], "n_sentences": cells[c]["n_sentences"],
                      "n_fpp_absent": cells[c]["n_absent"],
                      "fpp_absent_share": cells[c]["n_absent"] / cells[c]["n_docs"],
                      "n_defined_rates": int(len(cells[c]["rates"])),
                      "mean_completion_rate": float(np.mean(cells[c]["rates"])),
                      "n_bad_lines": cells[c]["n_bad"]} for c in ALL_CELLS},
        "margins_post_hoc": margins,
        "placement": res,
        "axis_normalised": {k: {c: rescale(res[k]["s_raw"][c], res[k]["s_raw"][MONO],
                                           res[k]["s_raw"][DIA]) for c in ALL_CELLS}
                            for k in order},
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\n" + text)
    print(f"\nwrote {OUT_TXT.relative_to(ROOT)}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(selftest())
    if sys.argv[1:] == ["--build-cache"]:
        done = build_cache()
        print("cache complete" if done else "cache incomplete - run --build-cache again")
        sys.exit(0 if done else 2)
    sys.exit(main())
