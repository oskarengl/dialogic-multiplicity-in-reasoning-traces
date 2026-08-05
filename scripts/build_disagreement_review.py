"""
Builds a standalone HTML review of every human/tagger disagreement in the
Method 3 reliability worksheet, with surrounding sentence context.

This is a DIAGNOSTIC VIEWER, not an analysis. It computes nothing that feeds any
gate. Its purpose is to let the rater read back the items where the two label
sources diverged, in context.

Note on framing: there is no ground truth here. The LLM tagger is not an answer
key — it is the second rater. A disagreement means the two raters diverged, not
that the human was wrong.

Output: outputs/method3/reliability/disagreements.html  (self-contained)
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / "outputs" / "method3" / "reliability"
OUTBASE = ROOT / "outputs" / "method3"
TAGS_JS = ROOT / "methods" / "3_dialogue_act_tagging" / "labeling_tool" / "cams_tags.js"
TREE_JSON = (ROOT / "methods" / "3_dialogue_act_tagging" / "sources"
             / "duran_cams_agreement" / "da_labels_tree.json")

CELL_DIRS = {
    "1": "cell1_human_monologue", "2": "cell2_human_debate",
    "3": "cell3_ai_debate", "4": "cell4_ai_monologue",
}
CELL_LABEL = {
    "1": "human_monologue", "2": "human_debate",
    "3": "ai_debate", "4": "ai_monologue",
}
ALIASES = {"propositionalQuestion": "propQuestion",
           "autoPositive": "feedbackPos", "autoNegative": "feedbackNeg"}
CONTEXT = 3


def family_map():
    src = TAGS_JS.read_text(encoding="utf-8")
    fams = [(m.start(), m.group(1)) for m in re.finditer(r'id:\s*"(\w+)"', src)]
    tags = [(m.start(), m.group(1)) for m in re.finditer(r'tag:\s*"(\w+)"', src)]
    starts = [p for p, _ in fams]
    out = {}
    for pos, t in tags:
        i = max([k for k, s in enumerate(starts) if s <= pos], default=-1)
        if i >= 0:
            out.setdefault(t, fams[i][1])
    return out


def tree_paths(node, prefix=()):
    path = prefix + (node["name"],)
    yield node["name"], path
    for ch in node.get("children", []):
        yield from tree_paths(ch, path)


def load_doc(cell, doc_id):
    fp = OUTBASE / CELL_DIRS[cell] / f"{doc_id}.jsonl"
    if not fp.exists():
        return []
    out = []
    for line in open(fp, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def main():
    fam = family_map()
    paths = dict(tree_paths(json.load(open(TREE_JSON))))
    hidden = json.load(open(REL / "hidden_llm_labels.json"))
    rows = list(csv.DictReader(open(REL / "worksheet.csv", encoding="utf-8")))

    def tree_dist(a, b):
        pa, pb = paths.get(ALIASES.get(a, a)), paths.get(ALIASES.get(b, b))
        if not pa or not pb:
            return None
        common = 0
        for x, y in zip(pa, pb):
            if x == y:
                common += 1
            else:
                break
        return (len(pa) - common) + (len(pb) - common)

    items = []
    doc_cache = {}
    for r in rows:
        key = f"{r['cell']}:{r['doc_id']}:{r['sentence_idx']}"
        h = (r.get("human_label") or "").strip()
        m = hidden.get(key)
        if not h or not m or h == m:
            continue
        ck = (r["cell"], r["doc_id"])
        if ck not in doc_cache:
            doc_cache[ck] = load_doc(*ck)
        doc = doc_cache[ck]
        i = int(r["sentence_idx"])
        lo, hi = max(0, i - CONTEXT), min(len(doc), i + CONTEXT + 1)
        before = [d["text"] for d in doc[lo:i]]
        after = [d["text"] for d in doc[i + 1:hi]]
        items.append({
            "cell": r["cell"], "cell_name": CELL_LABEL[r["cell"]],
            "doc_id": r["doc_id"], "idx": i, "text": r["text"],
            "human": h, "machine": m,
            "same_family": fam.get(h) == fam.get(m),
            "h_fam": fam.get(h, "?"), "m_fam": fam.get(m, "?"),
            "dist": tree_dist(h, m),
            "before": before, "after": after,
        })

    # most distant disagreements first
    items.sort(key=lambda x: (-(x["dist"] if x["dist"] is not None else 99),
                              x["cell"], x["doc_id"], x["idx"]))

    n_total = sum(1 for r in rows if (r.get("human_label") or "").strip())
    n_dis = len(items)
    n_near = sum(1 for i in items if i["same_family"])

    cards = []
    for n, it in enumerate(items, 1):
        ctx_b = "".join(f'<p class="ctx">{esc(t)}</p>' for t in it["before"])
        ctx_a = "".join(f'<p class="ctx">{esc(t)}</p>' for t in it["after"])
        badge = ("<span class='b near'>near miss · same family</span>"
                 if it["same_family"] else
                 f"<span class='b far'>{esc(it['h_fam'])} → {esc(it['m_fam'])}</span>")
        dist = f"tree distance {it['dist']}" if it["dist"] is not None else "off-tree"
        cards.append(f"""
<article class="card" data-fam="{'near' if it['same_family'] else 'far'}" data-cell="{it['cell']}">
  <header>
    <span class="num">#{n:03d}</span>
    <span class="meta">{esc(it['cell_name'])} · {esc(it['doc_id'])} · sentence {it['idx']}</span>
    {badge}
  </header>
  <div class="body">
    {ctx_b}
    <p class="focus">{esc(it['text'])}</p>
    {ctx_a}
  </div>
  <footer>
    <div class="verdict"><span class="lbl">you said</span><b class="you">{esc(it['human'])}</b></div>
    <div class="vs">vs</div>
    <div class="verdict"><span class="lbl">hy3 said</span><b class="them">{esc(it['machine'])}</b></div>
    <div class="dist">{dist}</div>
  </footer>
</article>""")

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Label Wall of Shame</title>
<style>
  :root {{ --bg:#0a0507; --ink:#e8d7d7; --dim:#7d6668; --blood:#8b0f1d;
           --blood2:#c41e2a; --card:#130a0d; --edge:#2a1418; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
          font:16px/1.65 Georgia,'Times New Roman',serif; }}
  .wrap {{ max-width:820px; margin:0 auto; padding:0 20px 120px; }}
  header.top {{ text-align:center; padding:80px 0 40px; position:relative; }}
  h1 {{ font-size:52px; margin:0 0 6px; letter-spacing:.06em; color:var(--blood2);
        text-shadow:0 0 28px rgba(196,30,42,.35); font-weight:400; }}
  .sub {{ color:var(--dim); font-style:italic; font-size:17px; margin:0; }}
  .drip {{ height:70px; background:
      radial-gradient(ellipse 5px 34px at 12% 0,var(--blood) 50%,transparent 51%),
      radial-gradient(ellipse 4px 52px at 27% 0,var(--blood) 50%,transparent 51%),
      radial-gradient(ellipse 6px 26px at 43% 0,var(--blood) 50%,transparent 51%),
      radial-gradient(ellipse 4px 62px at 58% 0,var(--blood) 50%,transparent 51%),
      radial-gradient(ellipse 5px 38px at 71% 0,var(--blood) 50%,transparent 51%),
      radial-gradient(ellipse 4px 48px at 86% 0,var(--blood) 50%,transparent 51%),
      linear-gradient(var(--blood),var(--blood)) top/100% 7px no-repeat;
      opacity:.75; margin-bottom:30px; }}
  .stats {{ display:flex; justify-content:center; gap:34px; flex-wrap:wrap;
            border-top:1px solid var(--edge); border-bottom:1px solid var(--edge);
            padding:22px 0; margin-bottom:14px; }}
  .stat {{ text-align:center; }}
  .stat b {{ display:block; font-size:30px; color:var(--blood2); font-weight:400; }}
  .stat span {{ font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--dim); }}
  .solace {{ border-left:2px solid var(--blood); background:#100709; padding:16px 20px;
             margin:28px 0 34px; color:#b9a3a5; font-size:15px; font-style:italic; }}
  .solace b {{ color:var(--ink); font-style:normal; }}
  .filters {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:26px; }}
  .filters button {{ background:#150b0e; color:var(--dim); border:1px solid var(--edge);
      padding:7px 14px; font:inherit; font-size:13px; cursor:pointer; letter-spacing:.04em; }}
  .filters button.on {{ color:var(--ink); border-color:var(--blood); background:#1d0d11; }}
  .card {{ background:var(--card); border:1px solid var(--edge); border-left:3px solid var(--blood);
           margin-bottom:22px; }}
  .card header {{ display:flex; align-items:center; gap:12px; flex-wrap:wrap;
                  padding:11px 18px; border-bottom:1px solid var(--edge); }}
  .num {{ color:var(--blood2); font-size:13px; letter-spacing:.1em; }}
  .meta {{ color:var(--dim); font-size:12px; font-family:ui-monospace,monospace; flex:1; }}
  .b {{ font-size:10.5px; letter-spacing:.11em; text-transform:uppercase; padding:3px 9px;
        border:1px solid; }}
  .b.near {{ color:#9a8a55; border-color:#4a3f24; }}
  .b.far {{ color:#d16b74; border-color:#4d1c22; }}
  .body {{ padding:18px 22px; }}
  .ctx {{ color:#4f4143; margin:5px 0; font-size:14.5px; }}
  .focus {{ color:var(--ink); background:linear-gradient(transparent 62%,rgba(139,15,29,.45) 62%);
            margin:11px 0; padding:2px 0; font-size:17px; }}
  .card footer {{ display:flex; align-items:center; gap:16px; flex-wrap:wrap;
                  padding:13px 22px; border-top:1px solid var(--edge); background:#0d0507; }}
  .verdict {{ display:flex; flex-direction:column; }}
  .lbl {{ font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim); }}
  .verdict b {{ font-family:ui-monospace,monospace; font-size:15px; font-weight:400; }}
  .you {{ color:#e0b3b7; }}
  .them {{ color:#8e9ec4; }}
  .vs {{ color:var(--dim); font-style:italic; font-size:13px; }}
  .dist {{ margin-left:auto; color:var(--dim); font-size:11.5px; font-family:ui-monospace,monospace; }}
  .end {{ text-align:center; color:var(--dim); font-style:italic; padding:50px 0 10px;
          border-top:1px solid var(--edge); margin-top:40px; }}
</style></head><body>
<header class="top">
  <h1>The Label Wall of Shame</h1>
  <p class="sub">{n_dis} disagreements, exhumed and laid out for inspection</p>
</header>
<div class="drip"></div>
<div class="wrap">
  <div class="stats">
    <div class="stat"><b>{n_total}</b><span>items labeled</span></div>
    <div class="stat"><b>{n_total - n_dis}</b><span>agreed</span></div>
    <div class="stat"><b>{n_dis}</b><span>disagreed</span></div>
    <div class="stat"><b>{n_near}</b><span>near misses</span></div>
    <div class="stat"><b>0.5425</b><span>cohen's &kappa;</span></div>
  </div>

  <p class="solace">A reliability study has <b>no answer key</b>. hy3 was the second rater,
  not the correct one — and it called 65% of everything <b>inform</b>, while you made
  finer distinctions. Every card below is a place two raters diverged. Not {n_dis} mistakes.
  You labeled {n_total} items and agreed on {n_total - n_dis} of them.</p>

  <div class="filters">
    <button class="on" data-f="all">all {n_dis}</button>
    <button data-f="far">different family ({n_dis - n_near})</button>
    <button data-f="near">near misses ({n_near})</button>
    <button data-f="1">① monologue</button>
    <button data-f="2">② human debate</button>
    <button data-f="3">③ ai debate</button>
    <button data-f="4">④ ai monologue</button>
  </div>
  {''.join(cards)}
  <p class="end">Here ends the wall.<br>The gate failed. The labeling did not.</p>
</div>
<script>
  const btns=[...document.querySelectorAll('.filters button')];
  const cards=[...document.querySelectorAll('.card')];
  btns.forEach(b=>b.addEventListener('click',()=>{{
    btns.forEach(x=>x.classList.toggle('on',x===b));
    const f=b.dataset.f;
    cards.forEach(c=>{{
      const show = f==='all' || c.dataset.fam===f || c.dataset.cell===f;
      c.style.display = show ? '' : 'none';
    }});
  }}));
</script>
</body></html>"""

    out = REL / "disagreements.html"
    out.write_text(html, encoding="utf-8")
    print(f"{n_dis} disagreements ({n_near} same-family) -> {out}")
    missing_ctx = sum(1 for i in items if not i["before"] and not i["after"])
    if missing_ctx:
        print(f"note: {missing_ctx} items had no retrievable context document")


if __name__ == "__main__":
    main()
