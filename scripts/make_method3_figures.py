#!/usr/bin/env python3
"""EXPLORATORY Method 3 figures - methods.md sec. 5, Figs M3.1, M3.3, M3.4.

Method 3 failed its sec. 3e reliability gate (kappa = 0.5425 < 0.70) and takes no part in the
confirmatory placement of cell (5). Every figure here is EXPLORATORY: the cell-(5) element in
each is drawn in the target colour and annotated "exploratory", and the captions in the paper
say the same. These figures do not appear in the cross-method summary (Table X / Fig X.1),
which stays Methods 1 and 2 only.

  fig_m3_1  the 28-label dialogue-act tag distribution per cell (signal a). Grouped bars for the
            most frequent tags; cells (1)/(2) grey (context), (3)/(4) the anchors, (5) the target.
  fig_m3_3  per-document adjacency-pair completion rate per cell (signal c, the primary signal),
            box + jittered strip, with each cell's FPP-absent share annotated. Headline figure.
  fig_m3_4  scatter of JSD-to-(4) (x) against JSD-to-(3) (y) for the unigram and bigram signals;
            the diagonal is equal distance to the two poles. Points below the diagonal lean
            dialogue. Cell (5) is the exploratory target.

Reads the frozen exploratory result outputs/placement/cell5_method3_exploratory.json for the
JSD placement coordinates, and the count-matrix cache (built by
scripts/place_cell5_method3_exploratory.py --build-cache) for the distributions and per-document
completion rates. Nothing is re-tagged.

Palette matches scripts/make_placement_figures.py (Okabe-Ito, colour-blind safe): the two
placement anchors and the target carry colour; context cells (1)/(2) stay neutral grey.

Usage:
    python scripts/make_method3_figures.py
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
EXPLORATORY = ROOT / "outputs" / "placement" / "cell5_method3_exploratory.json"

sys.path.insert(0, str(ROOT / "scripts"))
import place_cell5_method3_exploratory as P                              # noqa: E402
sys.path.insert(0, str(ROOT / "methods" / "3_dialogue_act_tagging" / "implementation"))
import signals as S                                                      # noqa: E402

ORDER = ["1", "2", "3", "4", "5"]
NAME = {"1": "① human\nmonologue", "2": "② human\ndebate", "3": "③ ai\ndebate",
        "4": "④ ai\nmonologue", "5": "⑤ ai\nreasoning"}
# One distinct, colour-blind-safe colour per cell (Okabe-Ito). No two cells share
# a colour, and the palette avoids relying on a red/green contrast.
FACE = {
    "1": "#56B4E9",   # sky blue      - human monologue
    "2": "#CC79A7",   # reddish purple - human debate
    "3": "#009E73",   # bluish green  - ai debate    (dialogue pole)
    "4": "#0072B2",   # blue          - ai monologue (monologue pole)
    "5": "#D55E00",   # vermillion    - ai reasoning (target, exploratory)
}
ANCHOR_M = FACE["4"]      # (4) ai_monologue - monologue pole
ANCHOR_D = FACE["3"]      # (3) ai_debate    - dialogue pole
TARGET_C = FACE["5"]      # (5) ai_reasoning - the exploratory target
SYM = {"1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤"}
PANEL_NAME = {
    "1": "① human monologue",
    "2": "② human debate",
    "3": "③ AI debate  (dialogue pole)",
    "4": "④ AI monologue  (monologue pole)",
    "5": "⑤ AI reasoning  (target, exploratory)",
}

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


def exploratory_footer(fig):
    """A standing marker at the foot of the figure so it reads as exploratory on its own."""
    fig.text(0.5, 0.005,
             "Exploratory — Method 3 failed its reliability gate (κ = 0.5425 < 0.70); "
             "cell ⑤ takes no part in the confirmatory placement.",
             ha="center", va="bottom", fontsize=7.5, color=TARGET_C, style="italic")


# --------------------------------------------------------------------------- Fig M3.1
def fig_m3_1(cells):
    """Five stacked per-cell tag distributions, sharing one x-axis whose order is
    set by cell ⑤ (the target). Each cell has its own colour; cell ⑤ is at the
    bottom and drives the tag ordering (its share, descending)."""
    dists = {c: P.pooled(cells[c]["uni"]) for c in ORDER}
    peak = np.max([dists[c] for c in ORDER], axis=0)
    # tags that carry appreciable mass in at least one cell, ordered by cell ⑤'s
    # share (descending) so the target defines the left-to-right order.
    keep = [i for i in range(len(peak)) if peak[i] > 0.01]
    top = sorted(keep, key=lambda i: dists["5"][i], reverse=True)[:14]
    labels = [S.TAGS[i] for i in top]
    # `inform` alone is so dominant it flattens everything else. Set the axis just
    # above the tallest *non-inform* bar, so every other tag shows at true height
    # and only `inform` is clipped (its true share printed above a break marker).
    inform_k = next((k for k, i in enumerate(top) if S.TAGS[i] == "inform"), None)
    non_inform_max = max(dists[c][top[k]] for c in ORDER
                         for k in range(len(top)) if k != inform_k)
    CAP = non_inform_max + 0.02
    yticks = [t for t in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25) if t < CAP]

    fig, axes = plt.subplots(len(ORDER), 1, sharex=True, figsize=(8.6, 7.4))
    x = np.arange(len(top))
    for ax, c in zip(axes, ORDER):
        vals = np.array([dists[c][i] for i in top])
        shown = np.minimum(vals, CAP)
        ax.bar(x, shown, width=0.72, color=FACE[c],
               edgecolor="white", linewidth=0.3, zorder=3)
        if inform_k is not None and vals[inform_k] > CAP:
            xi, v = x[inform_k], vals[inform_k]
            ax.plot([xi - 0.36, xi + 0.36], [CAP * 0.965, CAP * 0.995],
                    color="white", lw=1.4, zorder=5, clip_on=False)
            ax.plot([xi - 0.36, xi + 0.36], [CAP * 0.93, CAP * 0.96],
                    color="white", lw=1.4, zorder=5, clip_on=False)
            ax.text(xi, CAP * 1.04, f"{v:.2f}", ha="center", va="bottom",
                    fontsize=7.5, color=FACE[c], fontweight="bold",
                    zorder=6, clip_on=False)
        ax.set_ylim(0, CAP)
        ax.set_yticks(yticks)
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(axis="x", visible=False)
        ax.text(0.992, 0.82, PANEL_NAME[c], transform=ax.transAxes,
                ha="right", va="top", fontsize=8.5, color=FACE[c], fontweight="bold")
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=40, ha="right", fontsize=7.5)
    axes[0].set_title(
        "Fig M3.1  Dialogue-act tag distribution by cell", loc="left",
        fontsize=10, pad=20)
    fig.supylabel("share of utterances", fontsize=9)
    fig.subplots_adjust(top=0.93, bottom=0.12, hspace=0.20, left=0.10)
    save(fig, "fig_m3_1_tag_distribution")


# --------------------------------------------------------------------------- Fig M3.3
def fig_m3_3(cells):
    """Box + jittered strip of per-document completion rate, cell mean marked."""
    rng = np.random.default_rng(7)
    rates = {c: cells[c]["rates"] for c in ORDER}

    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    bp = ax.boxplot([rates[c] for c in ORDER], positions=range(len(ORDER)), widths=0.5,
                    patch_artist=True, showfliers=False, zorder=3,
                    medianprops=dict(color="#1a202c", linewidth=1.4),
                    whiskerprops=dict(color="#4a5568", linewidth=1),
                    capprops=dict(color="#4a5568", linewidth=1),
                    boxprops=dict(linewidth=1, edgecolor="#4a5568"))
    for patch, c in zip(bp["boxes"], ORDER):
        patch.set_facecolor(FACE[c])
        patch.set_alpha(0.85 if c == "5" else 0.6)
    for j, c in enumerate(ORDER):
        v = rates[c]
        jit = rng.uniform(-0.2, 0.2, len(v))
        ax.scatter(np.full(len(v), j) + jit, v, s=4, alpha=0.16,
                   color="#2d3748", linewidths=0, zorder=2, rasterized=True)
        ax.plot(j, np.mean(v), marker="D", ms=7, color=FACE[c],
                markeredgecolor="white", mew=0.8, zorder=5)
        ax.annotate(f"mean {np.mean(v):.3f}",
                    xy=(j, 1.0), xytext=(0, 2), textcoords="offset points",
                    ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels([NAME[c] for c in ORDER])
    ax.set_ylabel("direct completion rate")
    ax.set_ylim(-0.03, 1.12)
    ax.set_title("Fig M3.3  Adjacency-pair direct completion rate (e.g. question–answer), by cell",
                 loc="left", fontsize=10)
    ax.plot([], [], marker="D", ms=7, color="#4a5568", ls="", label="cell mean")
    ax.legend(loc="center", bbox_to_anchor=(0.62, 0.72), fontsize=8)
    save(fig, "fig_m3_3_completion_rate")


# --------------------------------------------------------------------------- Fig M3.4
def fig_m3_4(res):
    """JSD-to-(4) vs JSD-to-(3) for the unigram and bigram signals; diagonal = equal distance."""
    dot_name = {"1": "① human mono", "2": "② human debate", "3": "③ AI debate",
                "4": "④ AI mono", "5": "⑤ AI reasoning"}
    # ⑤ (target) and ① sit almost on top of each other; push their labels apart.
    lab_off = {"1": (8, -12), "2": (8, 4), "3": (8, 4), "4": (8, 4), "5": (8, 9)}
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 5.0))
    panels = [("a_unigram", "Tag frequency (unigram)", axes[0]),
              ("b_bigram", "Tag transition (bigram)", axes[1])]
    for key, title, ax in panels:
        pc = res["placement"][key]["per_cell_distances"]
        hi = max(max(pc[c]["d_mono"], pc[c]["d_dia"]) for c in ORDER) * 1.18
        ax.plot([0, hi], [0, hi], color="#cbd5e0", lw=1.2, ls="--", zorder=1,
                label="equal distance")
        for c in ORDER:
            x, y = pc[c]["d_mono"], pc[c]["d_dia"]
            is5 = c == "5"
            ax.scatter(x, y, s=150 if is5 else 90,
                       marker="D" if is5 else "o",
                       color=FACE[c], edgecolor="white", linewidth=0.8,
                       zorder=5 if is5 else 4)
            ax.annotate(dot_name[c] + ("  (exploratory)" if is5 else ""),
                        xy=(x, y), xytext=lab_off[c], textcoords="offset points",
                        fontsize=7.8, color=FACE[c], fontweight="bold",
                        va="top" if c == "1" else "bottom")
        ax.set_xlabel("distance to AI monologue ④")
        ax.set_ylabel("distance to AI debate ③")
        ax.set_xlim(0, hi)
        ax.set_ylim(0, hi)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=9.5)
        ax.text(0.5 * hi, 0.05 * hi, "below diagonal → leans dialogue", fontsize=7,
                color="#4a5568", ha="center", style="italic")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Fig M3.4  Distributional placement — exploratory",
                 x=0.02, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "fig_m3_4_jsd_scatter")


# --------------------------------------------------------------------------- main
def main():
    if not EXPLORATORY.exists():
        print(f"missing {EXPLORATORY.relative_to(ROOT)} - run "
              f"scripts/place_cell5_method3_exploratory.py first.")
        return 1
    res = json.loads(EXPLORATORY.read_text(encoding="utf-8"))
    cells = P.load_counts()
    fig_m3_1(cells)
    fig_m3_3(cells)
    fig_m3_4(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
