"""Cell ③ — AI group-debate dataset generator (random-puzzle, discussion-only variant).

Produces Game-of-24 group-debate transcripts among 4 independent, stateless
DeepSeek-V3 instances (OpenRouter), per `cell3_ai_debate_build_plan.md`.

This variant selects a random subset of solvable puzzles (rather than the
hardest ones) and records only the open discussion — no explicit final-answer
round is collected from each agent. If a final answer appears naturally in the
transcript, it is preserved as part of the dialogue.

Integrity rule: multiplicity comes only from 4 separately-prompted stateless
instances that share only the public transcript. No single model is ever asked
to write a 4-persona script.

Sampling: temperature omitted (provider default); no max_tokens limit (let them
talk); turn boundaries enforced purely by stop sequences.

Usage examples
--------------
  # Build/refresh puzzle_selection.csv only:
  python cell3_build_dataset_random_discussion.py --select-only --n-select 200

  # Test run: select then generate the 3 debates:
  python cell3_build_dataset_random_discussion.py --n-select 200 --n-run 3
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import pandas as pd
import requests
from tqdm import tqdm

# --------------------------------------------------------------------------- #
# Paths & constants
# --------------------------------------------------------------------------- #
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR.parent / "data"
CORE_ROOT = DATA_ROOT / "00_core-2x2"
DEFAULT_TRIALS = (
    DATA_ROOT
    / "raw" / "human_monologue" / "think_aloud_source"
    / "data" / "processed" / "full-experiment" / "full-experiment-trials.csv"
)
DEFAULT_PROBLEM_SET = (
    DATA_ROOT
    / "raw" / "human_monologue" / "think_aloud_source"
    / "data" / "problem-set" / "problem_set.csv"
)
DEFAULT_OUT = DATA_ROOT / "raw" / "ai_debate" / "qwen_generation"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat"
MODEL_SHORT = "deepseek-chat"

LABELS = ["A", "B", "C", "D"]
STOP_SEQUENCES = ["\nA:", "\nB:", "\nC:", "\nD:"]
SYSTEM_TEMPLATE = (
    "/no_think\n"
    "You are {X}, one of four participants in a mathematical problem-solving debate:\n"
    "- A: Creative Problem Solver - proposes novel approaches, thinks outside the box\n"
    "- B: Critical Analyst - challenges assumptions, questions logic, looks for flaws\n"
    "- C: Mathematical Validator - verifies calculations step-by-step, checks correctness\n"
    "- D: Alternative Seeker - looks for different solution paths, explores variations\n"
    "Share your thought briefly while staying in character. This is a collaborative but critical discussion."
)
TARGET = 24
MAX_TURNS = 40
CONTENT_RETRIES = 3          # regenerate a turn up to this many extra times
NETWORK_RETRIES = 5          # backoff retries on network/HTTP errors
GAME_TRIAL_TYPE = "GameOfN-audio-recording"

# --------------------------------------------------------------------------- #
# Natural stopping and semantic loop detection
# --------------------------------------------------------------------------- #
def detect_semantic_loop(turns, threshold=0.92, window=3):
    """Detect if recent turns are semantically repetitive using TF-IDF similarity."""
    if len(turns) < window + 1:
        return False
    
    # Get recent turn texts
    recent_texts = [t["text_clean"] for t in turns[-(window+1):]]
    
    try:
        # Calculate TF-IDF vectors
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(recent_texts)
        
        # Calculate cosine similarity between consecutive turns
        similarities = cosine_similarity(tfidf_matrix[:-1], tfidf_matrix[1:])
        
        # Check if any consecutive pair exceeds threshold
        max_similarity = similarities.diagonal().max()
        return max_similarity > threshold
    except:
        # Fallback: if vectorization fails, assume no loop
        return False

def should_stop_naturally(turns, spoken):
    """Determine if debate should end naturally based on consensus or loops."""
    # Minimum requirements
    if len(turns) < 4:  # At least one turn per participant
        return False
    if len(spoken) < 4:  # All participants must have spoken
        return False
    
    # Check for conclusion signals in the last 2 turns
    recent_text = " ".join(t["text_clean"].lower() for t in turns[-2:])
    conclusion_words = ["done", "finished", "complete", "agreed", "consensus", "locked in", "final"]
    if any(word in recent_text for word in conclusion_words):
        return True
    
    # Check for semantic loop
    if detect_semantic_loop(turns):
        return True
    
    return False

# --------------------------------------------------------------------------- #
# Game-of-24 solver & grader
# --------------------------------------------------------------------------- #
def solve_24(numbers, target=TARGET, max_solutions=5):
    """Return a list of solution expression strings (possibly empty)."""
    solutions = set()
    items0 = [(Fraction(n), str(n)) for n in numbers]

    def recurse(items):
        if len(items) == 1:
            if items[0][0] == target:
                solutions.add(items[0][1])
            return
        n = len(items)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                (av, ae), (bv, be) = items[i], items[j]
                rest = [items[k] for k in range(n) if k != i and k != j]
                cands = [
                    (av + bv, f"({ae}+{be})"),
                    (av - bv, f"({ae}-{be})"),
                    (av * bv, f"({ae}*{be})"),
                ]
                if bv != 0:
                    cands.append((av / bv, f"({ae}/{be})"))
                for cv, ce in cands:
                    recurse(rest + [(cv, ce)])

    recurse(items0)
    return sorted(solutions, key=len)[:max_solutions]


def _normalize_expr(expr: str) -> str:
    """Normalise a model-written expression to a bare arithmetic string.

    Handles the common ways models dress up an answer: unicode/x multiply signs,
    markdown bold/backticks, and a trailing ``= 24`` result annotation.
    """
    s = expr.replace("×", "*").replace("÷", "/").replace("`", "")
    s = s.replace("x", "*").replace("X", "*")
    if "=" in s:                       # drop a trailing "= 24" style result
        s = s.split("=")[0]
    return s.strip().strip("*").strip().strip('"').strip("'").strip()


def _eval_fraction(node):
    if isinstance(node, ast.Expression):
        return _eval_fraction(node.body)
    if isinstance(node, ast.BinOp):
        left, right = _eval_fraction(node.left), _eval_fraction(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError
            return left / right
        raise ValueError("unsupported operator")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        val = _eval_fraction(node.operand)
        return val if isinstance(node.op, ast.UAdd) else -val
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(node.value)
    raise ValueError("disallowed node")


def _literals(node, acc):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        acc.append(int(node.value))
    for child in ast.iter_child_nodes(node):
        _literals(child, acc)


def grade_expression(expr: str, numbers):
    """Return (answer_expr_normalized, valid, correct).

    valid  = parses, only + - * /, uses the four puzzle numbers each exactly once.
    correct = valid and evaluates to 24.
    On parse failure returns (cleaned_expr, None, None).
    """
    norm = _normalize_expr(expr)
    if not re.fullmatch(r"[0-9+\-*/().\s]+", norm or ""):
        return norm, None, None
    try:
        tree = ast.parse(norm, mode="eval")
        value = _eval_fraction(tree)
    except Exception:
        return norm, None, None
    used = []
    _literals(tree, used)
    valid = sorted(used) == sorted(numbers)
    correct = bool(valid and value == TARGET)
    return norm, bool(valid), correct


# --------------------------------------------------------------------------- #
# Puzzle selection
# --------------------------------------------------------------------------- #
def _parse_choices(raw):
    try:
        vals = [int(x) for x in ast.literal_eval(str(raw))]
        return tuple(sorted(vals)) if len(vals) == 4 else None
    except Exception:
        return None


def _zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def build_puzzle_selection(trials_csv: Path, n_select: int, out_csv: Path, seed: int = 12345) -> pd.DataFrame:
    df = pd.read_csv(trials_csv)
    game = df[df["trial_type"] == GAME_TRIAL_TYPE].copy()
    game["numbers"] = game["choices"].apply(_parse_choices)
    game = game[game["numbers"].notna()].copy()
    game["rt_s"] = pd.to_numeric(game["rt_s"], errors="coerce")
    game["correct"] = pd.to_numeric(game["correct"], errors="coerce")

    grouped = game.groupby("numbers").agg(
        human_rt_median=("rt_s", "median"),
        n_trials=("rt_s", "size"),
        mean_correct=("correct", "mean"),
    )
    grouped["human_fail_rate"] = 1.0 - grouped["mean_correct"].fillna(grouped["mean_correct"].mean())
    grouped["difficulty_score"] = (
        _zscore(grouped["human_rt_median"]) + _zscore(grouped["human_fail_rate"])
    )

    # Solvability + known solutions for every distinct puzzle (still required so
    # debates are run on solvable puzzles only).
    grouped["solutions"] = [solve_24(list(idx)) for idx in grouped.index]
    grouped["solvable"] = grouped["solutions"].apply(lambda s: len(s) > 0)

    n_distinct = len(grouped)
    n_game = len(game)
    n_solvable = int(grouped["solvable"].sum())
    print(f"[select] GameOfN trials: {n_game}  |  distinct puzzles (by multiset): {n_distinct}")
    print(f"[select] solvable puzzles: {n_solvable}")

    # Random selection from solvable puzzles (not hardest-first).
    solvable = grouped[grouped["solvable"]].copy().reset_index()
    selected = solvable.sample(n=min(n_select, len(solvable)), random_state=seed).reset_index(drop=True)
    selected["selection_rank"] = range(1, len(selected) + 1)
    selected["source_item_id"] = selected["numbers"].apply(
        lambda nums: "g24_" + "-".join(str(n) for n in nums)
    )

    out = selected[[
        "source_item_id", "numbers", "selection_rank", "human_rt_median",
        "human_fail_rate", "n_trials", "difficulty_score", "solvable", "solutions",
    ]].copy()
    out["numbers"] = out["numbers"].apply(lambda t: json.dumps(list(t)))
    out["solutions"] = out["solutions"].apply(json.dumps)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[select] wrote {len(out)} random solvable puzzles -> {out_csv}")
    return out


def load_puzzle_selection(out_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(out_csv)
    df["numbers"] = df["numbers"].apply(lambda s: tuple(json.loads(s)))
    df["solutions"] = df["solutions"].apply(json.loads)
    return df.sort_values("selection_rank").reset_index(drop=True)

# --------------------------------------------------------------------------- #
# Prompt construction (pure functions — covered by integrity test)
# --------------------------------------------------------------------------- #
def puzzle_header(numbers) -> str:
    nums = ", ".join(str(n) for n in numbers)
    return f"[Puzzle: make 24 using {nums} — each number once, + - * / only]"


def transcript_lines(numbers, turns):
    lines = [puzzle_header(numbers)]
    for t in turns:
        lines.append(f"{t['speaker']}: {t['text_clean']}")
    return lines


def build_turn_messages(numbers, turns, speaker):
    body = transcript_lines(numbers, turns) + [f"{speaker}:"]
    return [
        {"role": "system", "content": SYSTEM_TEMPLATE.format(X=speaker)},
        {"role": "user", "content": "\n".join(body)},
    ]


def assert_call_integrity(messages, expected_speaker):
    """Core ground-truth guard: a single call carries exactly ONE agent's system
    prompt (for `expected_speaker`) and never another agent's system prompt."""
    system_msgs = [m for m in messages if m["role"] == "system"]
    assert len(system_msgs) == 1, "a call must contain exactly one system prompt"
    assert system_msgs[0]["content"] == SYSTEM_TEMPLATE.format(X=expected_speaker)
    for other in [l for l in LABELS if l != expected_speaker]:
        assert SYSTEM_TEMPLATE.format(X=other) not in system_msgs[0]["content"]
    return True

# --------------------------------------------------------------------------- #
# Response post-processing
# --------------------------------------------------------------------------- #
_OTHER_LABEL_RE = re.compile(r"(?:^|\n)\s*(?:Person\s+)?([A-D])\s*:", re.IGNORECASE)


def _other_label_match(text, speaker):
    for m in _OTHER_LABEL_RE.finditer(text):
        if m.group(1).upper() != speaker:
            return m
    return None


def response_problem(text, speaker):
    if not text or not text.strip():
        return "empty"
    if _other_label_match(text, speaker) is not None:
        return "other_speaker_label"
    if re.match(rf"^\s*{speaker}\s*:", text):
        return "own_label_prefix"
    return None


def clean_turn_text(text, speaker):
    t = text.strip()
    t = re.sub(rf"^\s*{speaker}\s*:\s*", "", t)          # strip own leading label
    m = _other_label_match(t, speaker)                   # truncate at any leaked label
    if m is not None:
        t = t[: m.start()]
    t = t.strip().strip('"').strip()
    return t

# --------------------------------------------------------------------------- #
# OpenRouter client
# --------------------------------------------------------------------------- #
class RateLimiter:
    """Per-process rate limiter to stay under a global RPM budget.

    Each parallel worker instance should use the same max_per_minute so that
    N workers stay under N * max_per_minute total. For example, 4 workers at
    5 req/min each stays under 20 req/min.
    """
    def __init__(self, max_per_minute):
        self.max_per_minute = max_per_minute
        self.times = []

    def acquire(self):
        now = time.time()
        self.times = [t for t in self.times if now - t < 60]
        if len(self.times) >= self.max_per_minute:
            sleep_for = 60 - (now - self.times[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.time()
            self.times = [t for t in self.times if now - t < 60]
        self.times.append(now)


class OpenRouter:
    def __init__(self, api_key, model=DEFAULT_MODEL, rpm_limit=5):
        self.api_key = api_key
        self.model = model
        self.rate_limiter = RateLimiter(rpm_limit)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "cell3-ai-debate",
        })

    def complete(self, messages, stop=None, delay=None):
        self.rate_limiter.acquire()
        payload = {"model": self.model, "messages": messages, "usage": {"include": True}}
        if stop:
            payload["stop"] = stop
        # temperature & max_tokens deliberately omitted (provider defaults).
        if delay:
            time.sleep(delay)
        last_err = None
        for attempt in range(NETWORK_RETRIES):
            try:
                resp = self.session.post(OPENROUTER_URL, json=payload, timeout=180)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                resp.raise_for_status()
                data = resp.json()
                if "choices" not in data:
                    raise ValueError(f"no choices in response: {str(data)[:200]}")
                choice = data["choices"][0]
                content = choice["message"]["content"] or ""
                usage = data.get("usage", {}) or {}
                return {
                    "content": content,
                    "usage": usage,
                    "cost": float(usage.get("cost", 0.0) or 0.0),
                    "model_version": data.get("model", self.model),
                    "finish_reason": choice.get("finish_reason"),
                }
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                wait = 2 ** attempt
                print(f"  [api] attempt {attempt + 1}/{NETWORK_RETRIES} failed: {exc} (retry in {wait}s)")
                time.sleep(wait)
        raise RuntimeError(f"OpenRouter call failed after {NETWORK_RETRIES} attempts: {last_err}")

# --------------------------------------------------------------------------- #
# Debate engine
# --------------------------------------------------------------------------- #
def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def generate_turn(client, numbers, turns, speaker, log, debate_id, turn_index, delay=3.0):
    """One stateless turn with content-quality retries."""
    last = None
    for attempt in range(CONTENT_RETRIES + 1):
        messages = build_turn_messages(numbers, turns, speaker)
        assert_call_integrity(messages, speaker)
        res = client.complete(messages, stop=STOP_SEQUENCES, delay=delay)
        log.append({
            "ts": _now_iso(), "debate_id": debate_id, "kind": "turn",
            "turn_index": turn_index, "speaker": speaker, "attempt": attempt,
            "prompt_tokens": res["usage"].get("prompt_tokens"),
            "completion_tokens": res["usage"].get("completion_tokens"),
            "total_tokens": res["usage"].get("total_tokens"),
            "cost": res["cost"], "finish_reason": res["finish_reason"],
            "model_version": res["model_version"],
        })
        last = res
        problem = response_problem(res["content"], speaker)
        if problem is None:
            return res, clean_turn_text(res["content"], speaker), False, res["cost"]
    # retries exhausted -> accept best-effort, cleaned & flagged
    return last, clean_turn_text(last["content"], speaker), True, last["cost"]


def run_debate(client, puzzle_row, seed):
    numbers = list(puzzle_row["numbers"])
    debate_id = f"g24_{int(puzzle_row['selection_rank']):04d}"
    rng = random.Random(seed)
    started = _now_iso()
    turns, log = [], []
    spoken, cost = set(), 0.0
    model_version = client.model

    while True:
        missing = set(LABELS) - spoken
        if len(turns) >= MAX_TURNS and not missing:
            break
        # Check for natural stopping conditions
        if should_stop_naturally(turns, spoken):
            break
        speaker = rng.choice(sorted(missing)) if (len(turns) >= MAX_TURNS and missing) else rng.choice(LABELS)
        res, text_clean, flagged, turn_cost = generate_turn(
            client, numbers, turns, speaker, log, debate_id, len(turns)
        )
        cost += turn_cost
        model_version = res["model_version"]
        turns.append({
            "turn_index": len(turns), "speaker": speaker,
            "text_raw": res["content"], "text_clean": text_clean, "flagged": flagged,
        })
        spoken.add(speaker)

    # No explicit final-answer round: the discussion itself is the dataset.
    # If a final answer appears naturally in the transcript, it is preserved as-is.

    # Determine how the debate ended
    ended_by = "natural" if should_stop_naturally(turns, spoken) else "cap"

    debate = {
        "debate_id": debate_id,
        "source_item_id": puzzle_row["source_item_id"],
        "puzzle": {"target": TARGET, "numbers": numbers},
        "model": MODEL_SHORT,
        "model_version": model_version,
        "temperature": None,            # omitted -> provider default
        "max_tokens": None,             # omitted -> provider default
        "turn_order_seed": seed,
        "turns": turns,
        "n_turns": len(turns),
        "ended_by": ended_by,
        "started_at": started,
        "finished_at": _now_iso(),
        "cost_usd": round(cost, 6),
        "full_text_no_labels": "\n".join(t["text_clean"] for t in turns),
        "labeled_turns": [{"speaker": t["speaker"], "text": t["text_clean"]} for t in turns],
    }
    return debate, log

# --------------------------------------------------------------------------- #
# Resumable IO
# --------------------------------------------------------------------------- #
def load_done_ids(jsonl_path: Path):
    done = set()
    if jsonl_path.exists():
        with open(jsonl_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        done.add(json.loads(line)["debate_id"])
                    except Exception:
                        pass
    return done


def append_jsonl(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        fh.flush()

# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args():
    p = argparse.ArgumentParser(description="Cell ③ AI debate dataset generator (random puzzles, discussion only)")
    p.add_argument("--trials-csv", type=Path, default=DEFAULT_TRIALS)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--n-select", type=int, default=200, help="random solvable puzzles to select")
    p.add_argument("--n-run", type=int, default=0, help="debates to generate this run (0 = all not done)")
    p.add_argument("--start", type=int, default=1, help="1-based selection rank to start from (inclusive)")
    p.add_argument("--end", type=int, default=0, help="1-based selection rank to end at (inclusive, 0 = last)")
    p.add_argument("--seed", type=int, default=12345, help="base RNG seed (used for puzzle selection and per-debate turn order)")
    p.add_argument("--ranks", type=str, default="", help="comma-separated list of specific selection ranks to regenerate (e.g. '15,31,46')")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL)
    p.add_argument("--reselect", action="store_true", help="rebuild puzzle_selection.csv")
    p.add_argument("--select-only", action="store_true")
    p.add_argument("--api-key", type=str, default=None)
    p.add_argument("--rpm", type=int, default=5, help="max requests/minute for THIS process (run N shards at 20//N to stay under 20 total)")
    p.add_argument("--shard-label", type=str, default="", help="short label shown in the progress bar (e.g. shard rank range)")
    return p.parse_args()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    selection_csv = out_dir / "puzzle_selection.csv"
    debates_path = out_dir / "cell3_debates.jsonl"
    run_log_path = out_dir / "run_log.jsonl"

    if args.reselect or not selection_csv.exists():
        build_puzzle_selection(args.trials_csv, args.n_select, selection_csv, seed=args.seed)
    puzzles = load_puzzle_selection(selection_csv)
    print(f"[main] selection holds {len(puzzles)} puzzles (ranks 1..{len(puzzles)})")

    if args.select_only:
        return

    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("ERROR: set OPENROUTER_API_KEY env var or pass --api-key")
    client = OpenRouter(api_key, model=args.model, rpm_limit=args.rpm)

    done = load_done_ids(debates_path)
    start = max(1, args.start)
    end = args.end if args.end > 0 else args.n_select
    if args.ranks:
        target_ranks = {int(x) for x in args.ranks.split(",") if x.strip()}
        todo = [
            r for _, r in puzzles.iterrows()
            if int(r["selection_rank"]) in target_ranks
            and f"g24_{int(r['selection_rank']):04d}" not in done
        ]
        rank_str = args.ranks
    else:
        todo = [
            r for _, r in puzzles.iterrows()
            if start <= int(r["selection_rank"]) <= end
            and f"g24_{int(r['selection_rank']):04d}" not in done
        ]
        rank_str = f"{start}..{end}"
    if args.n_run > 0:
        todo = todo[: args.n_run]
    print(f"[main] {len(done)} already done; generating {len(todo)} debate(s) now (ranks {rank_str})")

    total_cost = 0.0
    desc = f"Debates[{args.shard_label}]" if args.shard_label else "Generating debates"
    progress = tqdm(todo, total=len(todo), desc=desc, unit="debate")
    for row in progress:
        rank = int(row["selection_rank"])
        seed = args.seed + rank
        debate_id = f"g24_{rank:04d}"
        t0 = time.time()
        debate, log = run_debate(client, row, seed)
        append_jsonl(debates_path, debate)
        for entry in log:
            append_jsonl(run_log_path, entry)
        total_cost += debate["cost_usd"]
        elapsed = time.time() - t0
        progress.set_postfix({
            "last": debate_id,
            "turns": debate["n_turns"],
            "cost": f"${debate['cost_usd']:.4f}",
            "time": f"{elapsed:.1f}s",
            "total": f"${total_cost:.3f}",
        })

    print(f"\n[main] done. debates -> {debates_path}")
    print(f"[main] run log -> {run_log_path}")
    print(f"[main] total cost this run: ${total_cost:.5f}")


if __name__ == "__main__":
    main()
