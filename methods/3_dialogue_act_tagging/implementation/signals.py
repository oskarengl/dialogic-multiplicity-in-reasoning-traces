"""Method 3 - shared signal computation (methods.md sec. 3a/3b/3c).

Loads the already-tagged per-document JSONL files (outputs/method3/cellN_*/*.jsonl,
one line per sentence: {"text":..., "start":..., "end":..., "label":...}) and computes,
per document: the unigram tag distribution (3a), the bigram transition counts (3b, both
row- and joint-normalized), and the adjacency-pair completion rate (3c).

No LLM calls here - the tagging is already done (STATUS.md). This module only summarizes
existing labels; it never touches cell 5 (ai_reasoning)'s tags beyond what's needed to run
the identical, pre-registered computation later, at Step 2 - nothing in this file is
cell-5-aware.
"""
import json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTBASE = ROOT / "outputs" / "method3"

# 27 CAMS DA tags + none, exact order fixed here (index order used throughout).
TAGS = [
    "propositionalQuestion", "setQuestion", "choiceQuestion", "checkQuestion",
    "inform", "answer", "agreement", "disagreement", "correction", "confirm", "disconfirm",
    "offer", "conditionalAccept", "accept", "decline", "request", "suggest",
    "autoPositive", "autoNegative", "stalling", "retraction",
    "greeting", "goodbye", "thanking", "acceptThanking", "apology", "acceptApology",
    "none",
]
TAG_IDX = {t: i for i, t in enumerate(TAGS)}
N_TAGS = len(TAGS)  # 28

# Frozen FPP -> valid SPP table (methods.md sec. 3c), derived from CAMS category structure.
FPP_SPP = {
    "propositionalQuestion": {"answer", "confirm", "disconfirm"},
    "setQuestion": {"answer"},
    "choiceQuestion": {"answer"},
    "checkQuestion": {"confirm", "disconfirm"},
    "request": {"accept", "decline", "conditionalAccept"},
    "suggest": {"accept", "decline", "conditionalAccept"},
    "offer": {"accept", "decline", "conditionalAccept"},
    "inform": {"agreement", "disagreement", "correction", "autoPositive", "autoNegative"},
    "greeting": {"greeting"},
    "goodbye": {"goodbye"},
    "thanking": {"acceptThanking"},
    "apology": {"acceptApology"},
}

CELL_DIRS = {
    "1": "cell1_human_monologue", "2": "cell2_human_debate",
    "3": "cell3_ai_debate", "4": "cell4_ai_monologue", "5": "cell5_ai_reasoning",
}
CELL_LABEL = {
    "1": "human_monologue", "2": "human_debate",
    "3": "ai_debate", "4": "ai_monologue", "5": "ai_reasoning",
}


CACHE_DIR = OUTBASE / "_tag_cache"


def load_cell_tags(cell, limit=None, use_cache=True):
    """Returns a list of documents, each a list of tag strings (unknown labels dropped).
    Cached to outputs/method3/_tag_cache/cellN.json (keyed on file count + mtime sum) so
    repeated calls across scripts don't re-parse hundreds of files every time; the cache
    is just a summary of tags, never used to skip re-reading if the underlying labels
    change (a stale cache is detected via a lightweight fingerprint, see below)."""
    d = OUTBASE / CELL_DIRS[cell]
    files = sorted(d.glob("*.jsonl"))
    if limit:
        files = files[:limit]
    fingerprint = f"{len(files)}:{sum(fp.stat().st_mtime_ns for fp in files)}"
    cache_fp = CACHE_DIR / f"cell{cell}.json"
    if use_cache and limit is None and cache_fp.exists():
        cached = json.loads(cache_fp.read_text(encoding="utf-8"))
        if cached.get("fingerprint") == fingerprint:
            return cached["docs"], cached["n_bad"]

    docs = []
    n_bad = 0
    for fp in files:
        tags = []
        for line in open(fp, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                n_bad += 1; continue
            lab = rec.get("label")
            if lab not in TAG_IDX:
                n_bad += 1; continue
            tags.append(lab)
        docs.append({"doc_id": fp.stem, "tags": tags})

    if use_cache and limit is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_fp.write_text(json.dumps(
            {"fingerprint": fingerprint, "docs": docs, "n_bad": n_bad}), encoding="utf-8")
    return docs, n_bad


# ----------------------------- 3a: unigram -----------------------------
def unigram_dist(tags):
    v = np.zeros(N_TAGS)
    for t in tags:
        v[TAG_IDX[t]] += 1
    s = v.sum()
    return v / s if s > 0 else v


def cell_unigram(docs):
    """Sentence-count-weighted average unigram distribution for a cell."""
    total = np.zeros(N_TAGS)
    for d in docs:
        for t in d["tags"]:
            total[TAG_IDX[t]] += 1
    s = total.sum()
    return total / s if s > 0 else total


# ----------------------------- 3b: bigram -----------------------------
def doc_bigram_counts(tags):
    m = np.zeros((N_TAGS, N_TAGS))
    for a, b in zip(tags, tags[1:]):
        m[TAG_IDX[a], TAG_IDX[b]] += 1
    return m


def cell_bigram(docs):
    """Summed bigram counts across a cell's documents (per methods.md: counts formed
    per document, then summed within the cell). Returns (row_normalized, joint_normalized)."""
    total = np.zeros((N_TAGS, N_TAGS))
    for d in docs:
        total += doc_bigram_counts(d["tags"])
    row_sums = total.sum(axis=1, keepdims=True)
    row_norm = np.divide(total, row_sums, out=np.zeros_like(total), where=row_sums > 0)
    s = total.sum()
    joint_norm = total / s if s > 0 else total
    return row_norm, joint_norm, total


# ----------------------------- 3c: completion rate -----------------------------
def doc_completion_rate(tags):
    """Returns (rate or None, n_fpp). rate is None iff n_fpp == 0 (FPP-absent document)."""
    n_fpp = 0
    n_completed = 0
    for a, b in zip(tags, tags[1:]):
        if a in FPP_SPP:
            n_fpp += 1
            if b in FPP_SPP[a]:
                n_completed += 1
    if n_fpp == 0:
        return None, 0
    return n_completed / n_fpp, n_fpp


def cell_completion_rates(docs):
    """Returns (rates: list of defined per-doc rates, n_fpp_absent, n_docs)."""
    rates = []
    n_absent = 0
    for d in docs:
        r, _ = doc_completion_rate(d["tags"])
        if r is None:
            n_absent += 1
        else:
            rates.append(r)
    return rates, n_absent, len(docs)


# ----------------------------- distances -----------------------------
def jsd(p, q, base=2):
    """Jensen-Shannon divergence, base 2 (bounded [0,1]). p, q: probability vectors."""
    p = np.asarray(p, float); q = np.asarray(q, float)
    p = p / p.sum() if p.sum() > 0 else p
    q = q / q.sum() if q.sum() > 0 else q
    m = 0.5 * (p + q)

    def kl(x, y):
        mask = x > 0
        return float(np.sum(x[mask] * np.log(x[mask] / y[mask])))

    js_nats = 0.5 * kl(p, m) + 0.5 * kl(q, m)
    return js_nats / math.log(base)


def cliffs_delta(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    gt = int((a[:, None] > b[None, :]).sum())
    lt = int((a[:, None] < b[None, :]).sum())
    return (gt - lt) / (len(a) * len(b))
