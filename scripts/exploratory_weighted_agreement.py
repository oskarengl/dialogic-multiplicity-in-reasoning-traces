"""
EXPLORATORY — NOT A PRE-REGISTERED GATE.

Weighted inter-annotator agreement for Method 3, following the measure that the
CAMS authors themselves specify.

BACKGROUND
----------
methods.md sec. 3e pre-registers *unweighted* Cohen's kappa on the 28-tag CAMS
scheme, bar 0.70. Scored 2026-07-22: kappa = 0.5425, 95% CI [0.4788, 0.6038] ->
FAIL. That verdict stands and is not affected by anything in this file.

However, Duran, Battle & Smith (2022) — the authors of CAMS, and the primary
source for this method — argue that unweighted pi/kappa are inappropriate for
dialogue-act labeling, because they give no credit for near-misses:
`choiceQuestion` and `checkQuestion` are semantically far closer than `request`
and `accept`, yet unweighted coefficients treat both disagreements identically.
They instead use weighted coefficients (Krippendorff's alpha, Artstein &
Poesio's alpha' and beta) with a distance matrix derived from the CAMS DA tree.

This script reproduces that approach on our 503 hand-labeled items.

WHY THIS CANNOT RESCUE THE GATE
-------------------------------
The choice to use a weighted coefficient was made AFTER seeing the failing
unweighted number. Whatever alpha comes out, Method 3 remains failed as
pre-registered, and cell (5) is placed by Methods 1 and 2 only. This is reported
as a limitation / exploratory reanalysis, not as a gate.

VALIDATION
----------
The alpha / alpha' / beta implementations are checked against the Artstein &
Poesio (2005) 100-item fixture that Duran et al. use for exactly this purpose.
Published expected values: alpha = 0.8156, alpha' = 0.8146, beta = 0.8163.
The script refuses to score real data if that check fails.

Distance matrix construction follows Duran et al.'s
`label_distance_utilities.generate_da_distance_matrix`: tree-walk distance
(steps up to the last common ancestor + steps back down), then min-max
normalised. Their pandas normalisation is column-wise, which is mildly
asymmetric; both that and a symmetric global-max variant are reported.

Usage:  python scripts/exploratory_weighted_agreement.py
"""
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "methods" / "3_dialogue_act_tagging" / "sources" / "duran_cams_agreement"
TREE_JSON = SRC / "da_labels_tree.json"
FIXTURE = SRC / "artstein_poesio_example.txt"
REL = ROOT / "outputs" / "method3" / "reliability"
WORKSHEET = REL / "worksheet.csv"
HIDDEN = REL / "hidden_llm_labels.json"

N_BOOT = 2000
SEED = 0

# Our tag inventory (cams_tags.js) vs the names used in Duran's DA tree.
TAG_ALIASES = {
    "propositionalQuestion": "propQuestion",
    "autoPositive": "feedbackPos",
    "autoNegative": "feedbackNeg",
}
# 'none' is our fallback tag; it has no node in the CAMS DA tree.
NO_NODE = {"none"}


# --------------------------------------------------------------------------
# distance matrix from the CAMS DA tree
# --------------------------------------------------------------------------
def tree_paths(node, prefix=()):
    """Yield (leaf_or_node_name, path_from_root_inclusive)."""
    path = prefix + (node["name"],)
    yield node["name"], path
    for child in node.get("children", []):
        yield from tree_paths(child, path)


def build_distance(tree, labels, normalise="column"):
    paths = dict(tree_paths(tree))
    missing = [l for l in labels if l not in paths]
    if missing:
        raise KeyError(f"labels absent from CAMS DA tree: {missing}")

    n = len(labels)
    d = np.zeros((n, n))
    for i, a in enumerate(labels):
        pa = paths[a]
        for j, b in enumerate(labels):
            pb = paths[b]
            common = 0
            for x, y in zip(pa, pb):
                if x == y:
                    common += 1
                else:
                    break
            # steps up from a to LCA + steps down from LCA to b
            d[i, j] = (len(pa) - common) + (len(pb) - common)

    if normalise == "column":
        # Duran et al.: (m - m.min()) / (m.max() - m.min()), pandas => per column
        col_min, col_max = d.min(axis=0), d.max(axis=0)
        rng = np.where(col_max - col_min == 0, 1, col_max - col_min)
        d = np.round((d - col_min) / rng, 3)
    elif normalise == "global":
        d = np.round(d / d.max(), 3)
    elif normalise == "none":
        pass
    else:
        raise ValueError(normalise)
    return d


# --------------------------------------------------------------------------
# weighted agreement coefficients (2 coders, 1 rating each per item)
# --------------------------------------------------------------------------
def _coeffs(a_idx, b_idx, D, n_labels):
    """Return (alpha, alpha_prime, beta) for paired ratings a_idx/b_idx."""
    a_idx = np.asarray(a_idx)
    b_idx = np.asarray(b_idx)
    N = len(a_idx)
    M = 2 * N  # total pairable ratings

    # observed disagreement — mirrors Duran's observed_disagreement() for 2 coders
    obs = (D[a_idx, b_idx].sum() + D[b_idx, a_idx].sum()) / M

    # counts over the pooled rating multiset
    n_all = np.bincount(np.concatenate([a_idx, b_idx]), minlength=n_labels).astype(float)
    num = float(n_all @ D @ n_all)          # sum over all ordered rating pairs

    exp_alpha = num / (M * (M - 1))
    exp_alpha_prime = num / (M * M)

    # beta uses a separate distribution per coder
    p_a = np.bincount(a_idx, minlength=n_labels).astype(float) / N
    p_b = np.bincount(b_idx, minlength=n_labels).astype(float) / N
    exp_beta = float(p_a @ D @ p_b)

    f = lambda e: 1.0 - obs / e if (obs and e) else 1.0
    return f(exp_alpha), f(exp_alpha_prime), f(exp_beta)


def validate_against_artstein_poesio():
    """Duran et al.'s own validation fixture. Must pass before real scoring."""
    rows = [ln.split() for ln in open(FIXTURE) if ln.strip()]
    per_item = {}
    for coder, idx, lbl in rows:
        per_item.setdefault(int(idx), {})[coder] = lbl
    labels = ["stat", "ireq", "chck"]
    li = {l: i for i, l in enumerate(labels)}

    D = np.zeros((3, 3))
    for x in labels:
        for y in labels:
            if x == y:
                D[li[x], li[y]] = 0.0
            elif {x, y} == {"ireq", "stat"}:
                D[li[x], li[y]] = 1.0
            else:
                D[li[x], li[y]] = 0.5

    a = [li[per_item[i]["a"]] for i in sorted(per_item)]
    b = [li[per_item[i]["b"]] for i in sorted(per_item)]
    got = _coeffs(a, b, D, 3)
    expected = (0.8156, 0.8146, 0.8163)
    ok = all(abs(g - e) < 5e-4 for g, e in zip(got, expected))
    print("[validation] Artstein & Poesio (2005) fixture, via Duran et al.")
    print(f"[validation]   alpha       got {got[0]:.4f}  expected {expected[0]:.4f}")
    print(f"[validation]   alpha_prime got {got[1]:.4f}  expected {expected[1]:.4f}")
    print(f"[validation]   beta        got {got[2]:.4f}  expected {expected[2]:.4f}")
    print(f"[validation]   {'PASS' if ok else 'FAIL'}\n")
    return ok


# --------------------------------------------------------------------------
def load_pairs():
    hidden = json.load(open(HIDDEN))
    rows = list(csv.DictReader(open(WORKSHEET, encoding="utf-8")))
    h, m, cells = [], [], []
    for r in rows:
        key = f"{r['cell']}:{r['doc_id']}:{r['sentence_idx']}"
        lab = (r.get("human_label") or "").strip()
        if not lab or key not in hidden:
            continue
        h.append(lab)
        m.append(hidden[key])
        cells.append(r["cell"])
    return h, m, cells


def main():
    if not validate_against_artstein_poesio():
        raise SystemExit("Validation failed — refusing to score real data.")

    tree = json.load(open(TREE_JSON))
    h_raw, m_raw, cells = load_pairs()

    dropped = sum(1 for a, b in zip(h_raw, m_raw) if a in NO_NODE or b in NO_NODE)
    keep = [i for i, (a, b) in enumerate(zip(h_raw, m_raw))
            if a not in NO_NODE and b not in NO_NODE]
    h = [TAG_ALIASES.get(h_raw[i], h_raw[i]) for i in keep]
    m = [TAG_ALIASES.get(m_raw[i], m_raw[i]) for i in keep]
    c = [cells[i] for i in keep]

    print(f"n pairs total        = {len(h_raw)}")
    print(f"dropped ('none' tag) = {dropped}   (no node in the CAMS DA tree)")
    print(f"n scored             = {len(h)}\n")

    labels = sorted(set(h) | set(m))
    li = {l: i for i, l in enumerate(labels)}
    a_idx = np.array([li[x] for x in h])
    b_idx = np.array([li[x] for x in m])

    for norm in ("column", "global"):
        D = build_distance(tree, labels, normalise=norm)
        al, ap, be = _coeffs(a_idx, b_idx, D, len(labels))
        tag = "Duran normalisation (column-wise)" if norm == "column" else "symmetric (global max)"
        print(f"--- {tag} ---")
        print(f"  Krippendorff alpha     = {al:.4f}")
        print(f"  Artstein-Poesio alpha' = {ap:.4f}")
        print(f"  Artstein-Poesio beta   = {be:.4f}")

        if norm == "column":
            rng = np.random.default_rng(SEED)
            boot = np.empty(N_BOOT)
            idx_all = np.arange(len(a_idx))
            for i in range(N_BOOT):
                bi = rng.choice(idx_all, size=len(idx_all), replace=True)
                boot[i] = _coeffs(a_idx[bi], b_idx[bi], D, len(labels))[0]
            lo, hi = np.percentile(boot, [2.5, 97.5])
            print(f"  alpha bootstrap 95% CI = [{lo:.4f}, {hi:.4f}]")

            print(f"\n  {'cell':6s} {'n':>5s} {'alpha':>8s}")
            c_arr = np.array(c)
            for cell in sorted(set(c)):
                ci = np.where(c_arr == cell)[0]
                print(f"  {cell:6s} {len(ci):>5d} "
                      f"{_coeffs(a_idx[ci], b_idx[ci], D, len(labels))[0]:>8.4f}")
        print()

    print("Reference points:")
    print("  unweighted Cohen's kappa, 28 tags (PRE-REGISTERED) = 0.5425  [0.4788, 0.6038]  FAIL vs 0.70")
    print("  unweighted Cohen's kappa, 9 families (exploratory) = 0.6074  [0.5318, 0.6768]")
    print("\nNOTE: no threshold applies to the numbers above. The pre-registered gate")
    print("was unweighted kappa >= 0.70 and it FAILED. This is exploratory context only.")


if __name__ == "__main__":
    main()
