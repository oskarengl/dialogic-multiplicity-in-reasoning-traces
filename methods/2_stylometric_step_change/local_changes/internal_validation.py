#!/usr/bin/env python3
"""Method 2 - internal validation: reproduce the SSPC checkpoint's published
macro-F1 on the PAN 2025 multi-author (spot-check) data, per subtask.

This is the analogue of Method 1's PAN19 source reproduction: before trusting the
shipped checkpoint on our own cells, confirm it reproduces the published numbers on
the data it was built for.

Target (Schmidt et al. 2025, SSPC) macro-F1:
    EASY 0.923   MEDIUM 0.828   HARD 0.724     (abstract)
    EASY 0.929   MEDIUM 0.815   HARD 0.731     (results-table variant)
The hard score differs between the abstract and the results table; see STATUS.md.
A reproduction within a couple of points of these is a pass.

Run from implementation/ (imports predict.py; uses local model.ckpt + styledistance/):
    python internal_validation.py                 # full validation split, all subtasks
    python internal_validation.py --max-files 50  # quick sample per subtask (CPU-friendly)
    python internal_validation.py --split train   # use the train split instead
"""
import argparse, json
from pathlib import Path

import torch
import pandas as pd
from sklearn.metrics import f1_score
from transformers import AutoTokenizer
from predict import (StyleChangeSequential, StyleChangeSequentialDataset,
                     collate_sequential_batch)

HERE = Path(__file__).resolve().parent
TARGET = {"easy": (0.923, 0.929), "medium": (0.828, 0.815), "hard": (0.724, 0.731)}


def load_split(data_dir, task, split, max_files=None):
    d = Path(data_dir) / task / split
    rows = []
    for txt in sorted(d.glob("problem-*.txt"))[:max_files]:
        pid = txt.stem
        tf = txt.parent / f"truth-{pid}.json"
        sents = [l.strip() for l in open(txt, encoding="utf-8") if l.strip()]
        changes = None
        if tf.exists():
            changes = json.load(open(tf, encoding="utf-8")).get("changes")
            if changes and len(changes) != len(sents) - 1:
                changes = changes[:len(sents) - 1]
        rows.append({"sentences": sents, "changes": changes,
                     "num_sentences": len(sents), "problem_id": pid, "task": task})
    return pd.DataFrame(rows)


def macro_f1(model, tok, df, device):
    ds = StyleChangeSequentialDataset(dataframe=df, tokenizer=tok)
    P, Y = [], []
    with torch.no_grad():
        n = len(ds)
        for i in range(n):
            if i == 1 or (i + 1) % 10 == 0 or i == n - 1:
                print(f"  progress: {i+1}/{n}", flush=True)
            b = collate_sequential_batch([ds[i]])
            logits = model.forward(input_ids=b["input_ids"], attention_mask=b["attention_mask"])
            lbl = b.get("labels")
            if lbl is not None:
                lbl = lbl.detach().cpu()
            preds, labels = model.get_predictions(
                logits=logits, labels=lbl, num_sentences=b["num_sentences"])
            if labels is not None and labels[0]:
                P += preds[0]; Y += labels[0]
    return f1_score(Y, P, average="macro", labels=[0, 1], zero_division=0) if Y else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="validation")
    ap.add_argument("--max-files", type=int, default=None)
    a = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}  split={a.split}  max_files={a.max_files or 'all'}")
    ckpt = torch.load(HERE / "model.ckpt", map_location=device)
    ckpt["hyper_parameters"]["model_name_or_path"] = str(HERE / "styledistance")
    model = StyleChangeSequential(**ckpt["hyper_parameters"])
    model.load_state_dict(ckpt["state_dict"])
    model.to(device); model.eval()
    tok = AutoTokenizer.from_pretrained(str(HERE / "styledistance"))

    print(f"\n{'task':8s} {'n':>5s} {'macro-F1':>9s}   target (abstract / table)")
    for task in ["easy", "medium", "hard"]:
        df = load_split(HERE / "pan25-data", task, a.split, a.max_files)
        if df.empty:
            print(f"{task:8s}  (no data)"); continue
        f1 = macro_f1(model, tok, df, device)
        ta, tb = TARGET[task]
        print(f"{task:8s} {len(df):>5d} {f1:>9.4f}   {ta:.3f} / {tb:.3f}")


if __name__ == "__main__":
    main()
