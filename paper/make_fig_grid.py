#!/usr/bin/env python3
"""Figure 1: the study design schematic -- four corpora of known voice structure,
the validity check, and the target cell.

This figure is schematic: it draws the design, and reads no data files.
Writes paper/figures/fig_grid.pdf (and .png).
"""
import matplotlib
from pathlib import Path
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "paper" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

MONO="#2F6F9F"; DIA="#C25A3C"; INK="#1A1A1A"; GRAY="#7A7A7A"
GREEN="#2E8B4F"; RED="#C0392B"; DGREY="#3A3A3A"
plt.rcParams.update({"font.family":"serif","font.serif":["DejaVu Serif"],
                     "savefig.dpi":300,"savefig.bbox":"tight"})


def make_grid():
    fig, ax = plt.subplots(figsize=(11.4, 3.4))
    ax.set_xlim(0, 104); ax.set_ylim(0, 42); ax.axis("off")

    def cell(x,y,w,h,title,sub,n,edge):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.4,rounding_size=1.2",
                     linewidth=1.3,edgecolor=edge,facecolor="white",zorder=2))
        ax.text(x+w/2,y+h-3.4,title,ha="center",va="top",fontsize=10.5,fontweight="bold",color=edge)
        ax.text(x+w/2,y+h-8.0,sub,ha="center",va="top",fontsize=8.2,color=INK)
        ax.text(x+w/2,y+3.0,n,ha="center",va="bottom",fontsize=8.0,color=GRAY)

    x0,cw,ch,gap=8,20,15,2.5
    cell(x0,24,cw,ch,"hum-mono","think-aloud","N = 600",MONO)
    cell(x0+cw+gap,24,cw,ch,"hum-dia","group debate","N = 500",DIA)
    cell(x0,6,cw,ch,"ai-mono","Qwen-2.5","N = 600",MONO)
    cell(x0+cw+gap,6,cw,ch,"ai-dia","4x Qwen-2.5","N = 600",DIA)

    ax.text(x0+cw/2,40.5,"monologue",ha="center",fontsize=9.5,color=MONO,fontweight="bold")
    ax.text(x0+cw+gap+cw/2,40.5,"dialogue",ha="center",fontsize=9.5,color=DIA,fontweight="bold")
    ax.text(x0-3.5,31.5,"human",ha="center",va="center",rotation=90,fontsize=9.5,color=INK)
    ax.text(x0-3.5,13.5,"AI",ha="center",va="center",rotation=90,fontsize=9.5,color=INK)
    ax.text(x0+cw+gap/2,1.2,"four corpora, structure known",
            ha="center",fontsize=8.4,color=GRAY,style="italic")

    vx=55.0
    ax.add_patch(FancyBboxPatch((vx,10),20.5,22,boxstyle="round,pad=0.5,rounding_size=1.4",
                 linewidth=1.3,edgecolor=INK,facecolor="white",zorder=2))
    ax.text(vx+10.25,29.6,"VALIDITY CHECK",ha="center",fontsize=9.0,fontweight="bold",color=INK)
    ax.text(vx+10.25,26.6,"classify all four\nknown cells correctly",ha="center",va="top",
            fontsize=7.7,color=INK)
    rows=[("M1  author count","fail",RED),("M2  style switch","pass",GREEN),
          ("M3  dialogue acts","pass",GREEN)]
    ry=19.0; word_x=vx+14.6
    for lbl,word,col in rows:
        ax.text(vx+2.2,ry,lbl,ha="left",va="center",fontsize=7.9,color=INK)
        ax.text(word_x,ry,word,ha="left",va="center",fontsize=8.0,color=col,fontweight="bold")
        ry-=3.6

    ax.add_patch(FancyArrowPatch((x0+2*cw+gap+1.5,21),(vx-0.5,21),
                 arrowstyle="-|>",mutation_scale=12,linewidth=1.1,color=GRAY))
    tx=87.5
    ax.add_patch(FancyArrowPatch((vx+20.5+0.7,21),(tx-0.7,21),
                 arrowstyle="-|>",mutation_scale=12,linewidth=1.1,color=GRAY))
    gm=(vx+20.5+tx)/2
    ax.text(gm,25.2,"passing",ha="center",va="center",fontsize=6.9,color=GRAY)
    ax.text(gm,22.9,"methods",ha="center",va="center",fontsize=6.9,color=GRAY)

    ax.add_patch(FancyBboxPatch((tx,12),15.5,18,boxstyle="round,pad=0.45,rounding_size=1.3",
                 linewidth=1.5,edgecolor=INK,facecolor="white",zorder=2,linestyle=(0,(4,2))))
    cx=tx+7.75
    ax.text(cx,27.2,"ai-reason",ha="center",va="center",fontsize=10.5,fontweight="bold",color=INK)
    ax.text(cx,23.6,"DeepSeek-R1",ha="center",va="center",fontsize=8.2,color=INK)
    ax.text(cx,20.4,"N = 600",ha="center",va="center",fontsize=8.0,color=GRAY)
    ax.text(cx,15.8,"monologue or\ndialogue?",ha="center",va="center",fontsize=8.2,
            color=INK,style="italic")

    fig.savefig(FIGS / "fig_grid.pdf")
    fig.savefig(FIGS / "fig_grid.png")
    plt.close(fig)
    print(f"wrote {FIGS / 'fig_grid.pdf'}")


if __name__ == "__main__":
    make_grid()
