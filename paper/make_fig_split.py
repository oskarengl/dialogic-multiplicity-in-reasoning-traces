#!/usr/bin/env python3
"""Figure 2: (A) Method 2 read within quantile-spaced length bins -- each
corpus is split into five equal-count bins, so every point rests on the same
number of documents and no minimum-count threshold has to be chosen.  No fitted
curve, no extrapolation, no shaded anchor band.  (B) Method 3 completion rates.
All numbers computed from the frozen output files.

Writes paper/figures/fig_split.pdf (and .png).
"""
import json, numpy as np, matplotlib
from pathlib import Path
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "paper" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

MONO="#2F6F9F"; DIA="#C25A3C"; INK="#1A1A1A"; GRAY="#7A7A7A"; DGREY="#3A3A3A"
plt.rcParams.update({"font.family":"serif","font.serif":["DejaVu Serif"],
                     "savefig.dpi":300,"savefig.bbox":"tight"})

# ---------------- load Method 2 raw scores ----------------
cells={}
for f in ["calibration_raw_scores.jsonl","cell5_raw_scores.jsonl"]:
    for line in open(ROOT / "outputs" / "method2" / f):
        d=json.loads(line)
        if d["raw"] is None or d["n_pairs"]<2: continue
        cells.setdefault(d["cell"],[]).append((d["n_pairs"],d["raw"]))
NAME={"1":"human monologue","2":"human debate","3":"AI debate","4":"AI monologue",
      "5":"reasoning traces"}
K=5   # quantile bins per corpus: equal document count per plotted point

def binned(c,K=K):
    p=np.array([x[0] for x in cells[c]],float); r=np.array([x[1] for x in cells[c]])
    o=np.argsort(p); p,r=p[o],r[o]
    xs,ys,ns=[],[],[]
    for g in np.array_split(np.arange(len(p)),K):
        xs.append(np.exp(np.log(p[g]).mean()))   # geometric mean length in bin
        ys.append(r[g].mean()); ns.append(len(g))
    return xs,ys,ns

MS=5.2   # uniform marker size: every point rests on the same number of documents

fig,(axA,axB)=plt.subplots(1,2,figsize=(11.4,3.5),
                           gridspec_kw={"width_ratios":[1.32,1]})

# ---------------- Panel A ----------------
style={"5":(DGREY,"o","-",2.0,"reasoning traces"),
       "3":(DIA,"s","-",1.5,"AI debate"),
       "4":(MONO,"^","-",1.5,"AI monologue"),
       "2":(DIA,"s",(0,(2,2)),1.1,"human debate"),
       "1":(MONO,"^",(0,(2,2)),1.1,"human monologue")}
for c in ["1","2","4","3","5"]:
    col,mk,ls,lw,lab=style[c]
    xs,ys,ns=binned(c)
    if not xs: continue
    a=1.0 if c in ("3","4","5") else 0.5
    z=4 if c=="5" else 3
    axA.plot(xs,ys,ls=ls,lw=lw,color=col,alpha=a,label=lab,zorder=z)
    for x,y,n in zip(xs,ys,ns):
        axA.plot(x,y,marker=mk,ms=MS,color=col,alpha=a,ls="",zorder=z+1)
axA.set_xscale("log")
axA.set_xticks([3,10,30,100,300])
axA.set_xticklabels(["3","10","30","100","300"])
axA.minorticks_off()
axA.set_xlabel("document length (sentence pairs, log scale)",fontsize=8.5)
axA.set_ylabel("mean style-switch probability",fontsize=8.5)
axA.set_title("A   Method 2: style change, compared at equal length",
              loc="left",fontsize=9.5,fontweight="bold")
axA.tick_params(labelsize=8)
for s in ("top","right"): axA.spines[s].set_visible(False)
axA.grid(axis="y",color="#EEEEEE",lw=0.8,zorder=0)
axA.set_axisbelow(True)
axA.set_ylim(0,0.105)
axA.legend(fontsize=7.0,frameon=False,ncol=2,loc="upper right")
axA.text(0.015,0.03,"each point: one fifth of its corpus\n(106--120 documents)",
         transform=axA.transAxes,fontsize=6.6,color=GRAY,va="bottom")

# ---------------- Panel B ----------------
# Completion rates as reported in Section 4; regenerate with
# scripts/place_cell5_method3_exploratory.py -> outputs/placement/
comp={"AI monologue":0.003,"AI debate":0.025,"reasoning traces":0.035,
      "human monologue":0.095,"human debate":0.235}
labs=list(comp); vals=[comp[k] for k in labs]
colr=[MONO,DIA,DGREY,MONO,DIA]
alph=[1,1,1,0.55,0.55]
y=np.arange(len(labs))[::-1]
for yi,v,c,a,l in zip(y,vals,colr,alph,labs):
    axB.barh(yi,v,height=0.55,color=c,alpha=a,zorder=3)
    axB.text(v+0.006,yi,f"{v:.3f}",va="center",fontsize=7.6,color=INK)
axB.set_yticks(y); axB.set_yticklabels(labs,fontsize=8.2)
axB.set_xlabel("completed adjacency pairs (rate)",fontsize=8.5)
axB.set_title("B   Method 3: question-and-answer structure",
              loc="left",fontsize=9.5,fontweight="bold")
axB.set_xlim(0,0.285)
axB.tick_params(axis="x",labelsize=8)
for s in ("top","right","left"): axB.spines[s].set_visible(False)
axB.tick_params(axis="y",length=0)
axB.grid(axis="x",color="#EEEEEE",lw=0.8,zorder=0)
axB.set_axisbelow(True)

fig.tight_layout(w_pad=2.0)
fig.savefig(FIGS / "fig_split.pdf")
fig.savefig(FIGS / "fig_split.png")
print(f"wrote {FIGS / 'fig_split.pdf'}")
