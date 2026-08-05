"""Run Method 3 (dialogue-act tagging) on all cells sequentially.

This wrapper calls label_dialogue_acts.py for each cell, one after the other.
It is designed to run unattended for hours. The rate limiter inside each
label_dialogue_acts.py run enforces the configured RPM. A small pause between
cells avoids any overlap at the boundary of the rolling rate-limit window.

Usage:
    set OPENAI_API_KEY=your-key
    set OPENAI_BASE_URL=https://openrouter.ai/api/v1
    python scripts/run_method3_all_cells.py

The cell mapping below can be edited if the dataset names change.
"""

import os
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

CELLS = [
    {
        "cell": "1",
        "input": PROJECT_ROOT / "data" / "00_core-2x2" / "human_monologue" / "all_samples" / "sample_600_human_think_aloud.jsonl",
        "output": PROJECT_ROOT / "outputs" / "method3" / "cell1_human_monologue",
        "text_field": "think_trace",
    },
    {
        "cell": "2",
        "input": PROJECT_ROOT / "data" / "00_core-2x2" / "human_debate" / "processed_human_debate.jsonl",
        "output": PROJECT_ROOT / "outputs" / "method3" / "cell2_human_debate",
        "text_field": "transcript",
    },
    {
        "cell": "3",
        "input": PROJECT_ROOT / "data" / "00_core-2x2" / "ai_debate" / "processed_ai_debate.jsonl",
        "output": PROJECT_ROOT / "outputs" / "method3" / "cell3_ai_debate",
        "text_field": "full_text_no_labels",
    },
    {
        "cell": "4",
        "input": PROJECT_ROOT / "data" / "00_core-2x2" / "ai_monologue" / "processed_prompted_ai_monologue.jsonl",
        "output": PROJECT_ROOT / "outputs" / "method3" / "cell4_ai_monologue",
        "text_field": "transcript",
    },
    {
        "cell": "5",
        "input": PROJECT_ROOT / "data" / "00_core-2x2" / "ai_reasoning" / "processed_native_reasoning_traces.jsonl",
        "output": PROJECT_ROOT / "outputs" / "method3" / "cell5_ai_reasoning",
        "text_field": "think_trace",
    },
]

# Model and settings
MODEL = "tencent/hy3:free"
PROMPT = PROJECT_ROOT / "methods" / "3_dialogue_act_tagging" / "implementation" / "CAMS_LLM_labeling_prompt.txt"
MAX_TOKENS = 32000
RATE_LIMIT_RPM = 19
MAX_WORKERS = 25

# Pause between cells to avoid rate-limit window overlap at the boundary.
PAUSE_BETWEEN_CELLS = 5  # seconds

# Optional test limit (e.g., 5 for a dry run). If None, process all samples.
LIMIT = None


def check_env() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    if not os.environ.get("OPENAI_BASE_URL"):
        print("WARNING: OPENAI_BASE_URL not set. Defaulting to OpenAI endpoint.", file=sys.stderr)


def run_cell(cell_config: dict) -> int:
    """Run one cell and return the subprocess exit code."""
    input_path = cell_config["input"]
    output_dir = cell_config["output"]
    cell = cell_config["cell"]
    text_field = cell_config["text_field"]

    print(f"\n=== Starting cell {cell}: {input_path} ===")
    print(f"Output: {output_dir}")

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "methods" / "3_dialogue_act_tagging" / "implementation" / "label_dialogue_acts.py"),
        "--input", str(input_path),
        "--output", str(output_dir),
        "--prompt", str(PROMPT),
        "--model", MODEL,
        "--max-tokens", str(MAX_TOKENS),
        "--rate-limit-rpm", str(RATE_LIMIT_RPM),
        "--max-workers", str(MAX_WORKERS),
        "--cell", cell,
        "--text-field", text_field,
    ]

    if LIMIT is not None:
        cmd.extend(["--limit", str(LIMIT)])

    result = subprocess.run(cmd)
    print(f"Cell {cell} finished with exit code {result.returncode}")
    return result.returncode


def main() -> None:
    check_env()

    total_cells = len(CELLS)
    for idx, cell_config in enumerate(CELLS, 1):
        returncode = run_cell(cell_config)

        if returncode != 0:
            print(f"WARNING: Cell {cell_config['cell']} failed. Continuing with next cell.", file=sys.stderr)

        # Pause between cells, except after the last one.
        if idx < total_cells:
            print(f"Pausing {PAUSE_BETWEEN_CELLS}s before next cell...")
            time.sleep(PAUSE_BETWEEN_CELLS)

    print("\nAll cells processed.")


if __name__ == "__main__":
    main()
