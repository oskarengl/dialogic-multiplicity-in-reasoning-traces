#!/usr/bin/env python3
"""Figures for Methods 1 and 2 and the cross-method placement panel - methods.md sec. 5.

Produces, into paper/figures/ as both .pdf (for the paper) and .png (for quick viewing):

  fig_m2_1  per-document raw switch probability per cell, and per-cell `lean`, side by side.
  fig_m2_2  the extrapolation check: length vs raw score for poles (3) and (4) with each pole's
            own fitted curve, each pole's observed length range shaded, both curves extended to
            cover cell (5)'s actual lengths, (2) as a context curve, and cell (5) as raw scatter.
  fig_x_1   the placement panel: monologue<->dialogue axis normalised so (4) = 0 and (3) = 1,
            each surviving method's cell-(5) position plotted with its no-clear-margin band.

Method 3 is absent by design - it failed its sec. 3e gate and gets no cell-(5) figure.

Run after scripts/place_cell5.py. Cells (1) and (2) appear for context only; sec. 3d restricts
the placement anchors to the AI-only pair (3)/(4).

Usage:
    python scripts/make_placement_figures.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                          # noqa: E402
import numpy as np                                                       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "paper" / "figures"
M2_CAL = ROOT / "outputs" / "method2" / "calibration_raw_scores.jsonl"
# Method 1's own predictions are no longer plotted (Table 3's per-cell mean/recall covers it),
# but cell5_predictions.jsonl existing is still the signal that M1 has scored the target.
M1_C5 = ROOT / "outputs" / "method1" / "cell5_predictions.jsonl"
M2_C5 = ROOT / "outputs" / "method2" / "cell5_raw_scores.jsonl"
PLACEMENT = ROOT / "outputs" / "placement" / "cell5_placement.json"

ORDER = ["1", "2", "3", "4", "5"]
NAME = {"1": "① human\nmonologue", "2": "② human\ndebate", "3": "③ ai\ndebate",
        "4": "④ ai\nmonologue", "5": "⑤ ai\nreasoning"}
# Okabe-Ito, colour-blind safe. Colour carries exactly one meaning here: the two placement
# anchors and the target. Context cells (1)/(2) stay neutral grey so they cannot be mistaken
# for poles - sec. 3d restricts the anchors to the AI-only pair.
GREY = "#8c8c8c"
ANCHOR_M = "#0072B2"      # (4) ai_monologue - monologue pole
ANCHOR_D = "#009E73"      # (3) ai_debate    - dialogue pole
TARGET_C = "#D55E00"      # (5) ai_reasoning - the target
FACE = {"1": GREY, "2": GREY, "3": ANCHOR_D, "4": ANCHOR_M, "5": TARGET_C}
SYM = {"1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤"}

plt.rcParams.update({
    "figure.dpi": 140, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "legend.frameon": False, "legend.fontsize": 8,
})


def save(fig, stem):
    FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{stem}.{ext}")
    plt.close(fig)
    print(f"  wrote paper/figures/{stem}.pdf + .png")


def rows(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def strip(ax, x, vals, rng, width=0.28, size=3, alpha=0.18):
    """Jittered raw points - dispersion and overlap must stay visible (sec. 5)."""
    jit = rng.uniform(-width, width, len(vals))
    ax.scatter(np.full(len(vals), x) + jit, vals, s=size, alpha=alpha,
               color="#2d3748", linewidths=0, zorder=2, rasterized=True)


def boxes(ax, data, cells):
    bp = ax.boxplot([data[c] for c in cells], positions=range(len(cells)), widths=0.5,
                    patch_artist=True, showfliers=False, zorder=3,
                    medianprops=dict(color="#1a202c", linewidth=1.4),
                    whiskerprops=dict(color="#4a5568", linewidth=1),
                    capprops=dict(color="#4a5568", linewidth=1),
                    boxprops=dict(linewidth=1, edgecolor="#4a5568"))
    for patch, c in zip(bp["boxes"], cells):
        patch.set_facecolor(FACE[c])
        patch.set_alpha(0.75 if c == "5" else 0.45)
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels([NAME[c] for c in cells])


def whisker_bounds(vals):
    """Tukey whisker extent (matches boxplot's default whis=1.5, the same rule
    showfliers=False uses to decide what counts as a flier), clipped to the data's
    own range. Used to set an axis range from the whiskers rather than the full
    outlier-inflated data range."""
    q1, q3 = np.percentile(vals, [25, 75])
    iqr = q3 - q1
    lo = max(float(np.min(vals)), q1 - 1.5 * iqr)
    hi = min(float(np.max(vals)), q3 + 1.5 * iqr)
    return lo, hi


# --------------------------------------------------------------------------- data
def load_m2(have5):
    r = [x for x in rows(M2_CAL)
         if x.get("cell") in ("1", "2", "3", "4") and x.get("raw") is not None]
    d = {}
    for c in ("1", "2", "3", "4"):
        rc = [x for x in r if x["cell"] == c]
        d[c] = (np.array([x["raw"] for x in rc], float),
                np.array([x["n_pairs"] for x in rc], float))
    if have5:
        rc = [x for x in rows(M2_C5) if x.get("raw") is not None]
        d["5"] = (np.array([x["raw"] for x in rc], float),
                  np.array([x["n_pairs"] for x in rc], float))
    return d


def curves(m2):
    sys.path.insert(0, str(ROOT / "methods" / "2_stylometric_step_change" / "implementation"))
    from run_calibration import fit_pole                    # noqa: E402
    out = {}
    for c in ("3", "4"):
        raw, pairs = m2[c]
        form, _, fn = fit_pole(pairs, raw)
        out[c] = (form, fn)
    return out


# --------------------------------------------------------------------------- figures
def fig_m2_1(m2, curv, cells, rng):
    f3, f4 = curv["3"][1], curv["4"][1]
    raw = {c: m2[c][0] for c in cells}
    lean = {c: np.abs(m2[c][0] - f4(m2[c][1])) - np.abs(m2[c][0] - f3(m2[c][1]))
            for c in cells}

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6))
    for i, c in enumerate(cells):
        strip(axes[0], i, raw[c], rng)
        strip(axes[1], i, lean[c], rng)
    boxes(axes[0], raw, cells)
    boxes(axes[1], lean, cells)
    axes[0].set_ylabel("mean raw switch probability")
    axes[0].set_title("Fig M2.1a  raw per-document score", loc="left")
    axes[1].axhline(0, color="#1a202c", lw=0.9, alpha=0.6, zorder=1)
    axes[1].set_ylabel(r"lean  $=|d_{mono}| - |d_{dia}|$")
    axes[1].set_title("Fig M2.1b  length-adjusted lean  (>0 = nearer the dialogue curve)",
                      loc="left")

    # Panel A only: a handful of high-outlier documents per cell were setting the y range,
    # squashing every box down into the bottom slice of the panel. Rescale to the whisker
    # extent (the same range showfliers=False already treats as "not a flier") so the boxes
    # - and the bulk of the jittered points above them - fill the panel instead.
    bounds = [whisker_bounds(raw[c]) for c in cells]
    lo = min(b[0] for b in bounds)
    hi = max(b[1] for b in bounds)
    pad = 0.08 * (hi - lo)
    axes[0].set_ylim(lo - pad, hi + pad)

    for a in axes:
        a.margins(x=0.06)
    save(fig, "fig_m2_1_switch_probability")


def fig_m2_2(m2, curv, have5):
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    xmax = max(float(np.max(m2[c][1])) for c in m2)
    xs = np.linspace(1, xmax * 1.05, 600)

    # y range is set by the OBSERVED scores; the fitted curves are allowed to run off the
    # panel when extrapolated, which is itself part of what this figure is for.
    obs = np.concatenate([m2[c][0] for c in m2])
    ylo, yhi = float(np.min(obs)), float(np.percentile(obs, 99.5))
    pad = 0.06 * (yhi - ylo)

    for c, lab, ls in (("4", "ai_monologue (monologue pole)", "-"),
                       ("3", "ai_debate (dialogue pole)", "--")):
        raw, pairs = m2[c]
        col = FACE[c]
        ax.scatter(pairs, raw, s=5, alpha=0.22, color=col, linewidths=0, rasterized=True,
                   label=f"{SYM[c]} {lab.split(' (')[0]} (raw scatter)")
        ax.plot(xs, curv[c][1](xs), color=col, lw=1.9, ls=ls,
                label=f"{SYM[c]} {lab} — {curv[c][0]} fit")

    if have5:
        raw5, p5 = m2["5"]
        ax.scatter(p5, raw5, s=8, alpha=0.40, color=TARGET_C, linewidths=0,
                   label="⑤ ai_reasoning (raw scatter)", rasterized=True)

    ax.set_xscale("log")
    ax.set_xlabel("sentence pairs per document (log scale)")
    ax.set_ylabel("mean raw switch probability")
    ax.legend(loc="upper right")
    ax.set_ylim(ylo - pad, yhi + pad)

    if have5:
        ax.set_title("Fig M2.2  Extrapolation check: both pole curves stretched to cell ⑤'s "
                     "lengths", loc="left")
    else:
        ax.set_title("Fig M2.2  Extrapolation check (cell ⑤ not yet scored)", loc="left")
    save(fig, "fig_m2_2_extrapolation")


def fig_x_1(pl):
    axis = pl["normalised_axis_pole4_0_pole3_1"]
    band = pl["no_clear_margin_band_on_axis"]
    methods = [("method1", "M1  style-change\n(author count)"),
               ("method2", "M2  stylometric\nstep-change")]

    # The x-range must always contain the target, even when it lands beyond a pole: M2 places
    # cell ⑤ at ~1.45, past the dialogue pole (1.0). Clipping it would hide the headline point.
    x5s = [axis[key]["5"] for key, _ in methods]
    ctx = [axis[key][c] for key, _ in methods for c in ("1", "2")]
    xr = max([1.0] + x5s)
    xl = min([0.0] + ctx)
    xlo, xhi = xl - 0.30, xr + 0.24
    lab_x = xlo + 0.02

    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    for i, (key, lab) in enumerate(methods):
        y = len(methods) - 1 - i
        ax.hlines(y, xl - 0.12, xhi - 0.04, color="#cbd5e0", lw=1.2, zorder=1)
        lo, hi = sorted(band[key])
        ax.add_patch(plt.Rectangle((lo, y - 0.17), hi - lo, 0.34, color="#a0aec0",
                                   alpha=0.28, zorder=2, linewidth=0))
        for c in ("4", "3"):
            ax.plot(axis[key][c], y, marker="|", ms=15, color=FACE[c], mew=2.4, zorder=3)
        for c in ("1", "2"):
            ax.plot(axis[key][c], y, marker="o", ms=4, color=GREY, alpha=0.6, zorder=3)
        x5 = axis[key]["5"]
        ax.plot(x5, y, marker="D", ms=10, color=TARGET_C, zorder=5)
        v = pl[key]["verdict"]
        beyond = "  · beyond ③" if x5 > 1.0 else ("  · beyond ④" if x5 < 0.0 else "")
        # keep the label from spilling off the right edge when the target sits far right
        ha = "right" if x5 > 0.75 * xhi else ("left" if x5 < xlo + 0.75 else "center")
        ax.annotate(f"⑤  {v}{beyond}\nr = {pl[key]['r']:.3f}   m = {pl[key]['m']:.3f}",
                    xy=(x5, y), xytext=(0, 15), textcoords="offset points",
                    ha=ha, fontsize=8, color=TARGET_C, zorder=6)
        ax.text(lab_x, y, lab, ha="left", va="center", fontsize=9)

    ax.set_yticks([])
    ax.set_ylim(-0.55, len(methods) - 0.15)
    ax.set_xlim(xlo, xhi)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels(["0\n④ ai_mono", "0.25", "0.5", "0.75", "1\n③ ai_debate"])
    ax.set_xlabel("monologue ←→ dialogue  (poles normalised to 0 and 1)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Cell ⑤ placement.  " + pl["pattern"], loc="left", fontsize=10)
    ax.plot([], [], marker="o", ms=4, color=GREY, ls="", label="① / ② context cells")
    ax.plot([], [], marker="|", ms=10, color=ANCHOR_M, ls="", mew=2, label="poles ③ / ④")
    ax.plot([], [], marker="D", ms=7, color=TARGET_C, ls="", label="⑤ ai_reasoning")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.26), ncol=3)
    save(fig, "fig_x_1_placement")


def fig_x_2(pl, ex):
    """Exploratory companion to Fig X.1: adds a Method 3 row (primary completion
    signal) below the two confirmatory methods. The M3 row is marked exploratory
    and post-hoc; its band is the post-hoc relative-gap margin, not a frozen
    bootstrap band, and its human context cells are off-scale (they complete far
    more adjacency pairs than the AI poles), so they are omitted from that row."""
    axis = pl["normalised_axis_pole4_0_pole3_1"]
    band = pl["no_clear_margin_band_on_axis"]

    cm = ex["placement"]["c_completion"]["cell_means"]
    denom = cm["3"] - cm["4"]
    m3_pos = (cm["5"] - cm["4"]) / denom
    m3_m = ex["placement"]["c_completion"]["m"]
    m3_r = ex["placement"]["c_completion"]["r"]
    m3_band = [1.0 / (2.0 + m3_m), 1.0 / (2.0 - m3_m)]

    rows = [("method1", "M1  style-change\n(author count)", False),
            ("method2", "M2  stylometric\nstep-change", False),
            ("method3", "M3  dialogue acts\n(completion) — exploratory", True)]

    x5s = [axis["method1"]["5"], axis["method2"]["5"], m3_pos]
    ctx = [axis[k][c] for k in ("method1", "method2") for c in ("1", "2")]
    xr = max([1.0] + x5s)
    xl = min([0.0] + ctx)
    xlo, xhi = xl - 0.30, xr + 0.28
    lab_x = xlo + 0.02

    fig, ax = plt.subplots(figsize=(8.6, 4.7))
    for i, (key, lab, is_expl) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.hlines(y, xl - 0.12, xhi - 0.04, color="#cbd5e0", lw=1.2, zorder=1)
        lo, hi = sorted(m3_band if is_expl else band[key])
        ax.add_patch(plt.Rectangle((lo, y - 0.17), hi - lo, 0.34,
                                   color="#a0aec0", alpha=0.20 if is_expl else 0.28,
                                   hatch="////" if is_expl else None,
                                   edgecolor="#a0aec0", zorder=2, linewidth=0))
        pole_x = {"3": 1.0, "4": 0.0} if is_expl else {c: axis[key][c] for c in ("3", "4")}
        for c in ("4", "3"):
            ax.plot(pole_x[c], y, marker="|", ms=15, color=FACE[c], mew=2.4, zorder=3)
        if not is_expl:
            for c in ("1", "2"):
                ax.plot(axis[key][c], y, marker="o", ms=4, color=GREY, alpha=0.6, zorder=3)
        x5 = m3_pos if is_expl else axis[key]["5"]
        if is_expl:
            ax.plot(x5, y, marker="D", ms=10, markerfacecolor="white",
                    markeredgecolor=TARGET_C, mew=2.0, zorder=5)
            verdict, r, m = ex["placement"]["c_completion"]["verdict"], m3_r, m3_m
        else:
            ax.plot(x5, y, marker="D", ms=10, color=TARGET_C, zorder=5)
            verdict, r, m = pl[key]["verdict"], pl[key]["r"], pl[key]["m"]
        beyond = "  · beyond ③" if x5 > 1.0 else ("  · beyond ④" if x5 < 0.0 else "")
        tag = "  (exploratory, post-hoc)" if is_expl else ""
        ha = "right" if x5 > 0.75 * xhi else ("left" if x5 < xlo + 0.75 else "center")
        ax.annotate(f"⑤  {verdict}{beyond}{tag}\nr = {r:.3f}   m = {m:.3f}",
                    xy=(x5, y), xytext=(0, 15), textcoords="offset points",
                    ha=ha, fontsize=8, color=TARGET_C, zorder=6)
        ax.text(lab_x, y, lab, ha="left", va="center", fontsize=9,
                style="italic" if is_expl else "normal")
        if is_expl:
            ax.text(xhi - 0.04, y - 0.30, "human cells ①②  off-scale to the right "
                    "(complete far more pairs)", ha="right", va="top",
                    fontsize=6.8, color=GREY, style="italic")

    # separator between the two confirmatory rows and the exploratory row
    ax.axhline(0.5, color="#e2a08a", lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.text(xlo + 0.02, 0.5, " confirmatory ↑   exploratory ↓ ", va="center",
            ha="left", fontsize=6.8, color="#c05621",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))

    ax.set_yticks([])
    ax.set_ylim(-0.75, len(rows) - 0.15)
    ax.set_xlim(xlo, xhi)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels(["0\n④ ai_mono", "0.25", "0.5", "0.75", "1\n③ ai_debate"])
    ax.set_xlabel("monologue ←→ dialogue  (poles normalised to 0 and 1)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Cell ⑤ placement including Method 3  (exploratory row)", loc="left",
                 fontsize=10)
    ax.plot([], [], marker="|", ms=10, color=ANCHOR_M, ls="", mew=2, label="poles ③ / ④")
    ax.plot([], [], marker="D", ms=7, color=TARGET_C, ls="", label="⑤ (confirmatory)")
    ax.plot([], [], marker="D", ms=7, markerfacecolor="white", markeredgecolor=TARGET_C,
            mew=1.6, ls="", label="⑤ (exploratory)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3)
    save(fig, "fig_x_2_placement_m3")


# --------------------------------------------------------------------------- main
def main():
    have5 = M1_C5.exists() and M2_C5.exists()
    cells = ORDER if have5 else ORDER[:-1]
    if not have5:
        print("NOTE: cell ⑤ has not been scored yet - rendering the calibration-only versions.\n"
              "      Re-run this script after scripts/place_cell5.py to get the final figures.")

    rng = np.random.default_rng(7)
    m2 = load_m2(have5)
    curv = curves(m2)

    fig_m2_1(m2, curv, cells, rng)
    fig_m2_2(m2, curv, have5)

    if PLACEMENT.exists():
        pl = json.loads(PLACEMENT.read_text(encoding="utf-8"))
        fig_x_1(pl)
        explor = ROOT / "outputs" / "placement" / "cell5_method3_exploratory.json"
        if explor.exists():
            fig_x_2(pl, json.loads(explor.read_text(encoding="utf-8")))
        else:
            print("  skipping Fig X.2 - exploratory JSON not found")
    else:
        print("  skipping Fig X.1 - outputs/placement/cell5_placement.json not found "
              "(run scripts/place_cell5.py first)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
