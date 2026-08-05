"""Method 1 - source reproduction on PAN 2019 (validation split).

Runs Nath's TBC in the frozen configuration on the official PAN19 style-change
validation set and reports binary (single- vs multi-author) accuracy, to confirm
our copy of the implementation reproduces the published result:
    Nath (2019), Table 5: validation 0.83, test/TIRA 0.85
    Zangerle (2019), Table 3: official 0.848

It runs both distance measures so the paper-vs-code discrepancy is visible:
Nath's paper describes Matusita distance; the shipped main.py defaults to Manhattan.
On this benchmark both reproduce the reported number (Manhattan 0.835, Matusita ~0.84
on the full split), which is why either is defensible; for our own cells we use
Matusita to match the method as the paper describes it.

Usage:
    python reproduce_compare.py                 # full split, both distances
    python reproduce_compare.py 250             # first 250 problems, both distances
    python reproduce_compare.py 0 430 manhattan # index range, one distance (for chunking)
"""
import os, sys, time, json, contextlib
import preprocess_NLP_pkg
from src.algorithms.threshold_clustering.executor import execute_threshold_clustering

_NULL = open(os.devnull, "w")
FOLDER = os.path.abspath(
    "../pan19 data/pan19-style-change-detection-validation-dataset-2019-01-17")
DIST = {"manhattan": preprocess_NLP_pkg.manhattan_distance,
        "matusita": preprocess_NLP_pkg.matusita_distance}


def truth(fn):
    with open(os.path.join(FOLDER, fn.replace(".txt", ".truth")), encoding="utf-8") as f:
        return int(json.load(f)["authors"])


def run(distance, start=0, end=None):
    files = sorted(preprocess_NLP_pkg.load_files_from_dir(FOLDER, "*.txt"))[start:end]
    ok = n = 0
    for fn in files:
        text = preprocess_NLP_pkg.read_file(
            os.path.join(FOLDER, fn), mode="rb", ignore_comments=False).decode("utf-8")
        with contextlib.redirect_stdout(_NULL):
            pred = execute_threshold_clustering(
                text, merge_threshold=50, add_node_threshold=50, prune=True,
                number_of_terms=50, distance_measure=distance, use_duplication_feature=True)
        ok += (1 if truth(fn) == 1 else 0) == (1 if pred == 1 else 0)
        n += 1
    return ok, n


def main():
    args = sys.argv[1:]
    if len(args) == 3:                       # index-range chunk, one distance
        start, end, name = int(args[0]), int(args[1]), args[2]
        t0 = time.time(); ok, n = run(DIST[name], start, end)
        print(f"{name} [{start}:{end}] ok={ok} n={n} acc={ok/n:.4f} ({time.time()-t0:.0f}s)")
        return
    limit = int(args[0]) if args else None   # full split (both distances)
    for name in ("manhattan", "matusita"):
        t0 = time.time(); ok, n = run(DIST[name], 0, limit)
        print(f"{name:10s} n={n} binary_acc={ok/n:.4f} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
