"""Monitor Method 3 (dialogue-act tagging) progress.

Reads the same cell mapping as run_method3_all_cells.py and periodically reports:
- files completed per cell
- total progress and percent
- files per minute over the last interval
- estimated remaining time

Usage (one-shot):
    python scripts/monitor_method3.py

Usage (periodic, writes to log):
    python scripts/monitor_method3.py --interval 60 --log outputs/method3/monitor.log

The log is appended and only the latest report is kept if the file grows.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Reuse the cell mapping from the wrapper.
sys.path.insert(0, str(Path(__file__).parent))
from run_method3_all_cells import CELLS


def count_input_lines(input_path: Path) -> int:
    """Return number of lines in the input JSONL file."""
    if not input_path.exists():
        return 0
    with open(input_path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def count_output_files(output_dir: Path) -> int:
    """Return number of .jsonl files in the output directory."""
    if not output_dir.exists():
        return 0
    return len(list(output_dir.glob("*.jsonl")))


def format_seconds(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds < 0:
        return "?"
    td = timedelta(seconds=int(seconds))
    return str(td)


def earliest_output_mtime() -> float | None:
    """Return the earliest file modification time in the first cell directory.

    This is a good proxy for when the current run started. Cells that are
    skipped from a previous run may contain older files, so only the first
    cell is used.
    """
    out_dir = CELLS[0]["output"]
    if not out_dir.exists():
        return None
    earliest = None
    for f in out_dir.glob("*.jsonl"):
        t = f.stat().st_mtime
        if earliest is None or t < earliest:
            earliest = t
    return earliest


def build_report(start_time: float | None, prev_counts: dict | None) -> str:
    """Build a text progress report."""
    lines = []
    now = datetime.now()
    lines.append(f"=== Method 3 Monitor [{now.strftime('%Y-%m-%d %H:%M:%S')}] ===")
    if start_time is None:
        start_time = earliest_output_mtime()
    if start_time:
        elapsed = time.time() - start_time
        if elapsed > 0:
            lines.append(f"Elapsed: {format_seconds(elapsed)}")

    total_done = 0
    total_total = 0
    cell_counts = {}

    for cell in CELLS:
        name = cell["cell"]
        input_path = cell["input"]
        output_dir = cell["output"]
        total = count_input_lines(input_path)
        done = count_output_files(output_dir)
        total_done += done
        total_total += total
        cell_counts[name] = done
        pct = done / total * 100 if total else 0
        lines.append(f"Cell {name}: {done:>5} / {total:>5} files ({pct:5.1f}%)  -> {output_dir}")

    overall_pct = total_done / total_total * 100 if total_total else 0
    lines.append(f"Overall: {total_done:>5} / {total_total:>5} files ({overall_pct:5.1f}%)")

    # Rate over last interval
    if prev_counts and start_time:
        prev_total = prev_counts.get("total", 0)
        prev_time = prev_counts.get("time", start_time)
        interval = time.time() - prev_time
        delta = total_done - prev_total
        if interval > 0:
            fpm = delta / interval * 60
            lines.append(f"Recent rate: {fpm:.1f} files/min (last {delta} files in {format_seconds(interval)})")
            remaining = total_total - total_done
            eta_seconds = remaining / (fpm / 60) if fpm > 0 else float("inf")
            lines.append(f"ETA at current rate: {format_seconds(eta_seconds)}")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Monitor Method 3 progress")
    parser.add_argument("--interval", type=int, default=0, help="Seconds between updates. If 0, run once and exit.")
    parser.add_argument("--log", type=str, default=None, help="Log file to write updates to (append mode).")
    args = parser.parse_args()

    # If there are already output files, use the earliest file mtime as the
    # start time to give a realistic average rate. For a fresh run this will be
    # close to the current time.
    start_time = earliest_output_mtime() or time.time()
    prev_counts = None

    log_path = Path(args.log) if args.log else None
    if log_path and log_path.exists():
        log_path.touch()

    while True:
        report = build_report(start_time, prev_counts)
        print(report)

        if log_path:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(report)

        prev_counts = {
            "total": sum(count_output_files(cell["output"]) for cell in CELLS),
            "time": time.time(),
            **{cell["cell"]: count_output_files(cell["output"]) for cell in CELLS},
        }

        if args.interval <= 0:
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
