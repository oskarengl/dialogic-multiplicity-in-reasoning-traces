#!/usr/bin/env python
"""Evaluate Nath TBC/WMC on PAN benchmark data (not project research cells).

Usage (from implementation/):
    python evaluate_benchmark.py -i ../benchmark_data/pan18/validation/... -a TBC
    python evaluate_benchmark.py -i ../benchmark_data/pan19/validation/... -a TBC

Reports binary accuracy (single vs multi-author), matching PAN 2019 evaluation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import preprocess_NLP_pkg
from src.algorithms.threshold_clustering.executor import execute_threshold_clustering
from src.algorithms.window_merge_clustering.executor import execute_window_merge_clustering


def load_ground_truth(folder: str, filename: str) -> int:
    truth_name = filename.replace(".txt", ".truth")
    truth_path = os.path.join(folder, truth_name)
    with open(truth_path, encoding="utf-8") as f:
        data = json.load(f)
    return int(data["authors"])


def predict(text: str, algorithm: str) -> int:
    if algorithm == "TBC":
        return execute_threshold_clustering(
            text,
            merge_threshold=50,
            add_node_threshold=50,
            prune=True,
            number_of_terms=50,
            distance_measure=preprocess_NLP_pkg.manhattan_distance,
            use_duplication_feature=True,
        )
    if algorithm == "WMC":
        return execute_window_merge_clustering(text, use_duplication_feature=True)
    raise ValueError(f"Unknown algorithm: {algorithm}")


def binary_label(author_count: int) -> int:
    return 1 if author_count == 1 else 0


def evaluate(folder: str, algorithm: str, limit: int | None = None) -> dict:
    files = preprocess_NLP_pkg.load_files_from_dir(folder, "*.txt")
    files.sort()
    if limit is not None:
        files = files[:limit]

    y_true_bin: list[int] = []
    y_pred_bin: list[int] = []
    y_true_count: list[int] = []
    y_pred_count: list[int] = []
    errors: list[dict] = []

    started = time.time()
    for i, filename in enumerate(files):
        text = preprocess_NLP_pkg.read_file(
            os.path.join(folder, filename),
            mode="rb",
            ignore_comments=False,
        ).decode("utf-8")
        true_authors = load_ground_truth(folder, filename)
        pred_authors = predict(text, algorithm)

        true_bin = binary_label(true_authors)
        pred_bin = binary_label(pred_authors)
        y_true_bin.append(true_bin)
        y_pred_bin.append(pred_bin)
        y_true_count.append(true_authors)
        y_pred_count.append(pred_authors)

        if true_bin != pred_bin:
            errors.append(
                {
                    "file": filename,
                    "true_authors": true_authors,
                    "pred_authors": pred_authors,
                }
            )

        if (i + 1) % 100 == 0:
            elapsed = time.time() - started
            print(f"  processed {i + 1}/{len(files)} ({elapsed:.0f}s)", flush=True)

    runtime = time.time() - started
    n = len(files)
    binary_accuracy = sum(t == p for t, p in zip(y_true_bin, y_pred_bin)) / n
    count_accuracy = sum(t == p for t, p in zip(y_true_count, y_pred_count)) / n

    return {
        "algorithm": algorithm,
        "documents": n,
        "binary_accuracy": binary_accuracy,
        "count_accuracy": count_accuracy,
        "runtime_seconds": runtime,
        "errors_sample": errors[:10],
        "error_count": len(errors),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Nath method on PAN benchmark data")
    parser.add_argument("-i", "--input", required=True, help="Folder with problem-*.txt and .truth files")
    parser.add_argument("-a", "--algorithm", default="TBC", choices=["TBC", "WMC"])
    parser.add_argument("-n", "--limit", type=int, default=None, help="Max documents (for quick smoke tests)")
    args = parser.parse_args()

    input_folder = os.path.abspath(args.input)
    if not os.path.isdir(input_folder):
        print(f"Input folder not found: {input_folder}", file=sys.stderr)
        sys.exit(1)

    print(f"Input: {input_folder}")
    print(f"Algorithm: {args.algorithm}")
    if args.limit:
        print(f"Limit: {args.limit} documents")

    results = evaluate(input_folder, args.algorithm, args.limit)

    print()
    print("=" * 50)
    print(f"Documents:       {results['documents']}")
    print(f"Binary accuracy: {results['binary_accuracy']:.4f}  (single vs multi-author)")
    print(f"Count accuracy:  {results['count_accuracy']:.4f}  (exact author count)")
    print(f"Runtime:         {results['runtime_seconds']:.0f}s")
    print(f"Binary errors:   {results['error_count']}")
    if results["errors_sample"]:
        print("\nFirst errors:")
        for err in results["errors_sample"][:5]:
            print(f"  {err['file']}: true={err['true_authors']}, pred={err['pred_authors']}")


if __name__ == "__main__":
    main()
