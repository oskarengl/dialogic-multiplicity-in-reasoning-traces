"""Validate the PAN 2025 SSPC implementation on local PAN 2025 data.

This script bypasses TIRA and loads the data directly from the local
pan25-data directory. It runs the Sequential Sentence Pair Classifier on
a subset of the data and reports macro-F1 scores.
"""

import json
import os
from pathlib import Path
from typing import List

import pandas as pd
import torch
from predict import StyleChangeSequential, StyleChangeSequentialDataset, collate_sequential_batch
from sklearn.metrics import f1_score
from transformers import AutoTokenizer


def load_pan2025_data(data_dir: str, split: str, task: str, max_files: int = None):
    """Load PAN 2025 data from local directory.
    
    Args:
        data_dir: Path to pan25-data
        split: 'train', 'validation', or 'test'
        task: 'easy', 'medium', or 'hard'
        max_files: Maximum number of files to load (for quick testing)
    
    Returns:
        DataFrame with columns: file, sentences, changes, num_sentences, task
    """
    data_dir = Path(data_dir)
    task_dir = data_dir / task / split
    
    rows = []
    txt_files = sorted(task_dir.glob("problem-*.txt"))
    if max_files:
        txt_files = txt_files[:max_files]
    
    for txt_file in txt_files:
        problem_id = txt_file.stem
        truth_file = txt_file.parent / f"truth-{problem_id}.json"
        
        # Read sentences
        with open(txt_file, "r", encoding="utf-8") as f:
            sentences = [line.strip() for line in f if line.strip()]
        
        # Read ground truth if available
        changes = None
        if truth_file.exists():
            with open(truth_file, "r", encoding="utf-8") as f:
                truth = json.load(f)
            changes = truth.get("changes")
            # Ensure length is num_sentences - 1
            if changes and len(changes) != len(sentences) - 1:
                changes = changes[:len(sentences) - 1]
        
        rows.append({
            "file": str(txt_file),
            "sentences": sentences,
            "changes": changes,
            "num_sentences": len(sentences),
            "task": task,
            "problem_id": problem_id,
        })
    
    return pd.DataFrame(rows)


def add_output_file(df: pd.DataFrame, output_dir: str):
    """Add output_file column as expected by shape_dataframe logic."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["output_file"] = df["problem_id"].apply(
        lambda x: str(output_dir / f"solution-{x}.json")
    )
    return df


def run_validation(model, tokenizer, df, device):
    """Run inference and compute macro-F1."""
    dataset = StyleChangeSequentialDataset(dataframe=df, tokenizer=tokenizer)
    
    all_preds = []
    all_labels = []
    
    model.eval()
    with torch.no_grad():
        for idx in range(len(dataset)):
            batch = collate_sequential_batch([dataset[idx]])
            logits = model.forward(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"]
            )
            
            # Get predictions and labels
            predictions, labels = model.get_predictions(
                logits=logits,
                labels=batch.get("labels"),
                num_sentences=batch["num_sentences"]
            )
            
            pred = predictions[0]
            if labels is not None:
                label = labels[0]
                all_preds.extend(pred)
                all_labels.extend(label)
    
    if all_labels:
        f1 = f1_score(
            y_true=all_labels,
            y_pred=all_preds,
            average='macro',
            labels=[0, 1],
            zero_division=0
        )
        return f1, all_preds, all_labels
    else:
        return None, all_preds, all_labels


def main():
    data_dir = Path(__file__).parent / "pan25-data"
    output_dir = Path(__file__).parent / "validation-output"
    model_path = Path(__file__).parent / "model.ckpt"
    encoder_path = Path(__file__).parent / "styledistance"
    
    device = torch.device('cpu')  # Use CPU; set to 'cuda' if available
    print(f"Using device: {device}")
    
    # Load model
    print(f"Loading model from {model_path}")
    checkpoint = torch.load(model_path, map_location=device)
    checkpoint['hyper_parameters']['model_name_or_path'] = str(encoder_path)
    
    model = StyleChangeSequential(**checkpoint['hyper_parameters'])
    model.load_state_dict(checkpoint['state_dict'])
    model.to(device)
    model.eval()
    
    tokenizer = AutoTokenizer.from_pretrained(str(encoder_path))
    
    # Run on each task
    for task in ["easy", "medium", "hard"]:
        print(f"\n=== Task: {task} ===")
        for split in ["train", "validation"]:
            split_dir = data_dir / task / split
            if not split_dir.exists():
                print(f"  {split}: not found, skipping")
                continue
            
            # For quick validation, limit to 10 files on CPU
            max_files = 10 if device.type == 'cpu' else None
            df = load_pan2025_data(data_dir, split, task, max_files=max_files)
            if df.empty:
                print(f"  {split}: no files")
                continue
            
            df = add_output_file(df, output_dir / task / split)
            
            f1, preds, labels = run_validation(model, tokenizer, df, device)
            if f1 is not None:
                print(f"  {split}: n={len(df)}, macro-F1={f1:.4f} (on {max_files if max_files else 'all'} files)")
            else:
                print(f"  {split}: n={len(df)}, no labels available")


if __name__ == "__main__":
    main()
