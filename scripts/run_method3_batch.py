"""Batch runner for Method 3 dialogue-act tagging across all datasets.

The runner processes each dataset sequentially, resumes from where it left off,
and handles duplicate IDs by generating a unique `method3_id` for each sample.

Usage:
    python scripts/run_method3_batch.py \
        --model tencent/hy3:free \
        --max-tokens 32000 \
        --rate-limit-rpm 19 \
        --max-workers 5
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


DATASETS = [
    # (input path, output directory name, text field, cell label)
    (
        "data/00_core-2x2/human_monologue/processed_sample_600_human_think_aloud.jsonl",
        "outputs/method3/human_reasoning_traces_small",
        None,
        "3",
    ),
    (
        "data/00_core-2x2/ai_debate/processed_ai_debate.jsonl",
        "outputs/method3/ai_debate",
        None,
        "3",
    ),
    (
        "data/00_core-2x2/ai_monologue/processed_prompted_ai_monologue.jsonl",
        "outputs/method3/ai_monologue",
        None,
        "3",
    ),
    (
        "data/00_core-2x2/ai_reasoning/processed_native_reasoning_traces.jsonl",
        "outputs/method3/ai_monologue_reasoning",
        None,
        "3",
    ),
    (
        "data/00_core-2x2/human_debate/processed_human_debate.jsonl",
        "outputs/method3/human_debate_delidata",
        None,
        "3",
    ),
    (
        "data/00_core-2x2/human_monologue/processed_human_think_aloud.jsonl",
        "outputs/method3/human_reasoning_traces",
        None,
        "3",
    ),
]


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_sample_id(original: dict, idx: int, dataset_name: str) -> str:
    """Generate a unique method3_id for a sample."""
    return f"{dataset_name}_{idx:06d}"


def prepare_temp_input(
    input_path: Path,
    temp_dir: Path,
    dataset_name: str,
    cell: str | None,
    limit: int | None,
    resume: bool,
) -> tuple[Path, int, int]:
    """Prepare a temp JSONL with unprocessed samples and unique IDs.

    Returns (temp_input_path, total_samples, unprocessed_count).
    """
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_input = temp_dir / f"{dataset_name}.jsonl"

    with open(input_path, "r", encoding="utf-8") as f:
        lines = list(f)

    if limit is not None:
        lines = lines[:limit]

    total = len(lines)
    output_dir = Path("outputs/method3") / dataset_name
    cell_prefix = f"cell{cell}_" if cell else ""
    existing = set()
    if resume and output_dir.exists():
        existing = {p.stem for p in output_dir.glob("*.jsonl")}

    unprocessed_lines = []
    skipped = 0
    for idx, line in enumerate(lines):
        method3_id = get_sample_id({}, idx, dataset_name)
        expected_filename = f"{cell_prefix}{method3_id}"
        if resume and expected_filename in existing:
            skipped += 1
            continue
        sample = json.loads(line)
        sample["method3_id"] = method3_id
        sample["method3_original_index"] = idx
        unprocessed_lines.append(json.dumps(sample, ensure_ascii=False))

    with open(temp_input, "w", encoding="utf-8") as f:
        f.write("\n".join(unprocessed_lines) + ("\n" if unprocessed_lines else ""))

    return temp_input, total, len(unprocessed_lines)


def run_dataset(
    input_path: Path,
    output_dir: Path,
    model: str,
    max_tokens: int,
    rate_limit_rpm: int,
    max_workers: int,
    cell: str | None,
    text_field: str | None,
    temp_dir: Path,
    dataset_name: str,
    limit: int | None,
    resume: bool,
) -> tuple[int, int]:
    """Run label_dialogue_acts.py for one dataset."""
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset_name}")
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print(f"Time: {datetime.now().isoformat()}")

    temp_input, total, unprocessed = prepare_temp_input(
        input_path, temp_dir, dataset_name, cell, limit, resume
    )

    if unprocessed == 0:
        print(f"  Already complete ({total}/{total}). Skipping.")
        return total, 0

    print(f"  Total samples: {total}, unprocessed: {unprocessed}")

    output_dir.mkdir(parents=True, exist_ok=True)

    script = (
        Path(__file__).resolve().parent.parent
        / "methods"
        / "3_dialogue_act_tagging"
        / "implementation"
        / "label_dialogue_acts_v2.py"
    )
    prompt = (
        Path(__file__).resolve().parent.parent
        / "methods"
        / "3_dialogue_act_tagging"
        / "CAMS_LLM_labeling_prompt.txt"
    )

    cmd = [
        sys.executable,
        str(script),
        "--input", str(temp_input),
        "--output", str(output_dir),
        "--prompt", str(prompt),
        "--model", model,
        "--max-tokens", str(max_tokens),
        "--rate-limit-rpm", str(rate_limit_rpm),
        "--max-workers", str(max_workers),
        "--id-key", "method3_id",
    ]
    if cell:
        cmd.extend(["--cell", cell])
    if text_field:
        cmd.extend(["--text-field", text_field])

    start = time.time()
    log_path = output_dir / "label_dialogue_acts.log"
    with open(log_path, "a", encoding="utf-8") as log_f:
        try:
            subprocess.run(cmd, stdout=log_f, stderr=log_f, check=True, env={**os.environ, "PYTHONUNBUFFERED": "1"})
        except subprocess.CalledProcessError as e:
            print(f"  Dataset {dataset_name} failed: {e}", file=sys.stderr)
            raise
    elapsed = time.time() - start
    print(f"  Dataset {dataset_name} finished in {elapsed:.1f}s ({elapsed/unprocessed:.1f}s per sample)")
    print(f"  Log: {log_path}")

    return total, unprocessed


def main():
    parser = argparse.ArgumentParser(description="Batch runner for Method 3 dialogue-act tagging")
    parser.add_argument("--model", default="tencent/hy3:free", help="LLM model name")
    parser.add_argument("--max-tokens", type=int, default=32000, help="Max output tokens per LLM call")
    parser.add_argument("--rate-limit-rpm", type=int, default=19, help="Max requests per minute")
    parser.add_argument("--max-workers", type=int, default=5, help="Max parallel worker threads")
    parser.add_argument("--limit", type=int, default=None, help="Max samples per dataset (for testing)")
    parser.add_argument("--no-resume", action="store_true", help="Reprocess all samples, ignore existing output")
    args = parser.parse_args()

    repo_root = get_repo_root()
    os.chdir(repo_root)

    temp_dir = repo_root / "outputs" / "method3" / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    resume = not args.no_resume

    overall_start = time.time()
    for input_rel, output_rel, text_field, cell in DATASETS:
        input_path = repo_root / input_rel
        output_dir = repo_root / output_rel
        dataset_name = output_rel.split("/")[-1]

        if not input_path.exists():
            print(f"\nSkipping {dataset_name}: input not found at {input_path}")
            continue

        total, processed = run_dataset(
            input_path,
            output_dir,
            args.model,
            args.max_tokens,
            args.rate_limit_rpm,
            args.max_workers,
            cell,
            text_field,
            temp_dir,
            dataset_name,
            args.limit,
            resume,
        )

    overall_elapsed = time.time() - overall_start
    print(f"\n{'='*60}")
    print(f"All datasets finished in {overall_elapsed:.1f}s")


if __name__ == "__main__":
    main()
