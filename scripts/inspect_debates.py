"""Pretty-print Cell ③ debate transcripts for human review.

Usage:
  python scripts/inspect_debates.py                 # summary of all debates
  python scripts/inspect_debates.py --id g24_0001   # full transcript of one
  python scripts/inspect_debates.py --full          # full transcript of all
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_JSONL = (
    Path(__file__).resolve().parents[2]
    / "data" / "00_core-2x2" / "ai_debate" / "regenerated_ai_debate.jsonl"
)


def load(path: Path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def summarize(d):
    speakers = Counter(t["speaker"] for t in d["turns"])
    lens = [len(t["text_clean"]) for t in d["turns"]]
    avg = sum(lens) / len(lens) if lens else 0
    print(f"\n{'=' * 78}")
    print(f"{d['debate_id']}  puzzle={d['puzzle']['numbers']} target={d['puzzle']['target']}")
    print(f"  model={d.get('model_version')}  seed={d.get('turn_order_seed')}  "
          f"ended_by={d.get('ended_by')}  cost=${d.get('cost_usd')}")
    print(f"  n_turns={d['n_turns']}  speaker_counts={dict(sorted(speakers.items()))}  "
          f"avg_turn_chars={avg:.0f}  max_turn_chars={max(lens) if lens else 0}")
    flagged = sum(1 for t in d["turns"] if t.get("flagged"))
    if flagged:
        print(f"  flagged_turns={flagged} (post-process retries exhausted)")
    print("  final_submissions:")
    for s in d["final_submissions"]:
        print(f"    {s['speaker']}: expr={s['answer_expr']!r}  valid={s['valid']}  correct={s['correct']}")
    print(f"  any_correct={d['any_correct']}")


def print_transcript(d, max_chars=600):
    summarize(d)
    print("  ---- transcript ----")
    for t in d["turns"]:
        txt = t["text_clean"].replace("\n", " ")
        if len(txt) > max_chars:
            txt = txt[:max_chars] + f" …[+{len(t['text_clean']) - max_chars} chars]"
        flag = " [FLAGGED]" if t.get("flagged") else ""
        print(f"  [{t['turn_index']:02d}] {t['speaker']}{flag}: {txt}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    ap.add_argument("--id", type=str, default=None)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--max-chars", type=int, default=600)
    args = ap.parse_args()

    rows = load(args.jsonl)
    print(f"Loaded {len(rows)} debate(s) from {args.jsonl}")
    total_cost = sum(r.get("cost_usd", 0) for r in rows)
    print(f"Total cost across file: ${total_cost:.5f}")

    if args.id:
        for d in rows:
            if d["debate_id"] == args.id:
                print_transcript(d, args.max_chars)
        return
    for d in rows:
        if args.full:
            print_transcript(d, args.max_chars)
        else:
            summarize(d)


if __name__ == "__main__":
    main()
