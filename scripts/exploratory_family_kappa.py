"""
EXPLORATORY — NOT A PRE-REGISTERED GATE.

methods.md sec. 3e pre-registers Cohen's kappa on the full 28-tag CAMS scheme,
with a pass/fail bar of kappa >= 0.70. That gate was scored on 2026-07-22 and
FAILED (pooled kappa = 0.5425, 95% CI [0.4788, 0.6038]).

This script re-scores the SAME 503 hand-labeled items after collapsing both the
human labels and the tagger labels to CAMS's eight functional families (plus the
'fallback' family), to answer a diagnostic question: how much of the observed
disagreement is fine-grained (right family, wrong sibling tag) versus coarse
(wrong family entirely)?

This CANNOT rescue the gate. The collapse was not pre-registered, and it was
chosen AFTER seeing the failing number. It is reported as exploratory context
only. The 28-tag kappa remains the registered result.

Reuses cohen_kappa() from reliability_sample.py unmodified so the arithmetic is
identical to the registered run. Method code is not touched.
"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "methods" / "3_dialogue_act_tagging" / "implementation"
sys.path.insert(0, str(IMPL))

from reliability_sample import cohen_kappa  # noqa: E402  (exact registered function)

REL = ROOT / "outputs" / "method3" / "reliability"
WORKSHEET = REL / "worksheet.csv"
HIDDEN = REL / "hidden_llm_labels.json"
TAGS_JS = ROOT / "methods" / "3_dialogue_act_tagging" / "labeling_tool" / "cams_tags.js"

N_BOOT = 2000
SEED = 0


def build_family_map():
    """Derive tag -> family from the labeling tool's own taxonomy, not by hand."""
    src = TAGS_JS.read_text(encoding="utf-8")
    fam_pos = [(m.start(), m.group(1)) for m in re.finditer(r'id:\s*"(\w+)"', src)]
    tag_pos = [(m.start(), m.group(1)) for m in re.finditer(r'tag:\s*"(\w+)"', src)]
    starts = [p for p, _ in fam_pos]
    mapping = {}
    for pos, tag in tag_pos:
        i = np.searchsorted(starts, pos, side="right") - 1
        if i >= 0:
            mapping.setdefault(tag, fam_pos[i][1])
    return mapping


def boot_ci(yt, yp, labels, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    idx_all = np.arange(len(yt))
    boot = np.empty(n_boot)
    for i in range(n_boot):
        bi = rng.choice(idx_all, size=len(idx_all), replace=True)
        boot[i] = cohen_kappa(yt[bi].tolist(), yp[bi].tolist(), labels)
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def main():
    fam = build_family_map()
    hidden = json.load(open(HIDDEN))
    rows = list(csv.DictReader(open(WORKSHEET, encoding="utf-8")))

    h_tag, m_tag, cells = [], [], []
    for r in rows:
        key = f"{r['cell']}:{r['doc_id']}:{r['sentence_idx']}"
        h = (r.get("human_label") or "").strip()
        if not h or key not in hidden:
            continue
        h_tag.append(h)
        m_tag.append(hidden[key])
        cells.append(r["cell"])

    unmapped = sorted({t for t in set(h_tag) | set(m_tag) if t not in fam})
    if unmapped:
        print(f"WARNING: tags with no family mapping: {unmapped}")

    h_fam = [fam.get(t, t) for t in h_tag]
    m_fam = [fam.get(t, t) for t in m_tag]

    print(f"n scored = {len(h_tag)}   (families: {len(set(h_fam) | set(m_fam))})\n")

    # --- headline: family-level kappa ---
    labels = sorted(set(h_fam) | set(m_fam))
    k = cohen_kappa(h_fam, m_fam, labels)
    lo, hi = boot_ci(np.array(h_fam), np.array(m_fam), labels)
    print(f"FAMILY-LEVEL pooled kappa = {k:.4f}   bootstrap 95% CI = [{lo:.4f}, {hi:.4f}]")
    print("(exploratory — the registered 28-tag kappa was 0.5425 [0.4788, 0.6038], FAIL)\n")

    print(f"{'cell':6s} {'n':>5s} {'k_tag':>8s} {'k_family':>10s}")
    cells_arr = np.array(cells)
    for c in sorted(set(cells)):
        ci = np.where(cells_arr == c)[0]
        tl = sorted(set(np.array(h_tag)[ci]) | set(np.array(m_tag)[ci]))
        fl = sorted(set(np.array(h_fam)[ci]) | set(np.array(m_fam)[ci]))
        kt = cohen_kappa(np.array(h_tag)[ci].tolist(), np.array(m_tag)[ci].tolist(), tl)
        kf = cohen_kappa(np.array(h_fam)[ci].tolist(), np.array(m_fam)[ci].tolist(), fl)
        print(f"{c:6s} {len(ci):>5d} {kt:>8.4f} {kf:>10.4f}")

    # --- decomposition of disagreements ---
    exact = sum(1 for a, b in zip(h_tag, m_tag) if a == b)
    same_fam = sum(1 for a, b in zip(h_tag, m_tag)
                   if a != b and fam.get(a) == fam.get(b))
    diff_fam = len(h_tag) - exact - same_fam
    n = len(h_tag)
    print(f"\nAgreement decomposition (raw counts, not chance-corrected):")
    print(f"  exact tag match          {exact:4d}  ({exact / n:6.1%})")
    print(f"  same family, wrong tag   {same_fam:4d}  ({same_fam / n:6.1%})")
    print(f"  different family         {diff_fam:4d}  ({diff_fam / n:6.1%})")

    # --- where the cross-family disagreements actually go ---
    from collections import Counter
    cross = Counter((fam.get(a), fam.get(b))
                    for a, b in zip(h_tag, m_tag) if fam.get(a) != fam.get(b))
    print("\nTop cross-family confusions (human -> tagger):")
    for (a, b), cnt in cross.most_common(10):
        print(f"  {a:12s} -> {b:12s} {cnt:4d}")

    within = Counter((a, b) for a, b in zip(h_tag, m_tag)
                     if a != b and fam.get(a) == fam.get(b))
    print("\nTop within-family confusions (human -> tagger):")
    for (a, b), cnt in within.most_common(10):
        print(f"  {a:20s} -> {b:20s} {cnt:4d}")


if __name__ == "__main__":
    main()
