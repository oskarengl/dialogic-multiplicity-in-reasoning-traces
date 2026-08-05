"""Cell ④ — AI monologue dataset generator (single-agent think-aloud).

Produces Game-of-24 think-aloud transcripts from a single AI model,
mimicking the human think-aloud format for comparison.

Supports parallel processing with rate limiting and checkpointing,
similar to the AI debate dataset generator.

Usage:
  # Generate 5 monologues for testing:
  python cell4_build_ai_monologue.py --n-run 5

  # Generate full dataset in 4 parallel shards:
  python cell4_build_ai_monologue.py --start 1 --end 51 --shard-label "shard1" --rpm 5 &
  python cell4_build_ai_monologue.py --start 52 --end 101 --shard-label "shard2" --rpm 5 &
  python cell4_build_ai_monologue.py --start 102 --end 151 --shard-label "shard3" --rpm 5 &
  python cell4_build_ai_monologue.py --start 152 --end 200 --shard-label "shard4" --rpm 5 &
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import time
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

# --------------------------------------------------------------------------- #
# Paths & constants
# --------------------------------------------------------------------------- #
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR.parent.parent / "data"
PUZZLE_SELECTION = DATA_ROOT / "problem_sets" / "puzzle_selection_game24.csv"
DEFAULT_OUT = DATA_ROOT / "ai_monologue" / "unprocessed"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen-2.5-7b-instruct"
MODEL_SHORT = "qwen-2.5-7b-instruct"

TARGET = 24
NETWORK_RETRIES = 5

# --------------------------------------------------------------------------- #
# Game-of-24 solver & grader (reused from debate script)
# --------------------------------------------------------------------------- #
def solve_24(numbers, target=TARGET, max_solutions=5):
    """Return a list of solution expression strings (possibly empty)."""
    from fractions import Fraction
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
    """Normalise a model-written expression to a bare arithmetic string."""
    s = expr.replace("×", "*").replace("÷", "/").replace("`", "")
    s = s.replace("x", "*").replace("X", "*")
    # Remove LaTeX markers like \( ... \), \[ ... \], \frac{a}{b}
    s = re.sub(r'\\[()\[\]]', '', s)
    s = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', s)
    s = re.sub(r'\\[a-zA-Z]+', '', s)  # Remove other LaTeX commands
    if "=" in s:
        s = s.split("=")[0]
    # Keep parentheses for correct evaluation
    return s.strip().strip('"').strip("'").strip()


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
    """Return (answer_expr_normalized, valid, correct)."""
    norm = _normalize_expr(expr)
    # Allow parentheses in the expression
    if not re.fullmatch(r"^[0-9+\-*/(). ]+$", norm):
        return norm, False, False
    try:
        tree = ast.parse(norm, mode='eval')
    except:
        return norm, False, False
    literals = []
    _literals(tree, literals)
    if sorted(literals) != sorted(numbers):
        return norm, False, False
    try:
        result = _eval_fraction(tree)
    except:
        return norm, False, False
    correct = result == TARGET
    return norm, True, correct


# --------------------------------------------------------------------------- #
# Rate limiter (for parallel processing)
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


# --------------------------------------------------------------------------- #
# OpenRouter client
# --------------------------------------------------------------------------- #
class OpenRouter:
    def __init__(self, api_key, model=DEFAULT_MODEL, rpm_limit=5):
        self.api_key = api_key
        self.model = model
        self.rate_limiter = RateLimiter(rpm_limit)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "cell4-ai-monologue",
        })

    def complete(self, messages):
        self.rate_limiter.acquire()
        payload = {"model": self.model, "messages": messages, "usage": {"include": True}}
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
                }
            except Exception as exc:
                last_err = exc
                wait = 2 ** attempt
                time.sleep(wait)
        raise RuntimeError(f"OpenRouter call failed after {NETWORK_RETRIES} attempts: {last_err}")


# --------------------------------------------------------------------------- #
# Monologue generation
# --------------------------------------------------------------------------- #
def build_monologue_prompt(numbers):
    nums = ", ".join(str(n) for n in numbers)
    return f"""Target 24 with numbers [{nums}]. Use each number exactly once with +, -, *, /."""


def extract_final_expression(text):
    """Extract the final expression from the AI response."""
    # Look for "FINAL ANSWER:" pattern first
    final_match = re.search(r'FINAL ANSWER:\s*([^\n]+)', text, re.IGNORECASE)
    if final_match:
        expr = final_match.group(1).strip()
        expr = expr.replace("\\times", "*").replace("\\div", "/").replace("\\cdot", "*")
        expr = expr.replace("x", "*").replace("×", "*").replace("÷", "/")
        # Remove LaTeX markers
        expr = re.sub(r'\\[()\[\]]', '', expr)
        expr = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr)
        expr = re.sub(r'\\[a-zA-Z]+', '', expr)
        # Remove any trailing punctuation or equals
        expr = re.sub(r'[=\s]*$', '', expr)
        if re.search(r'[0-9].*[+\-*/]', expr):
            return expr.strip()
    
    # Look for LaTeX-style boxed expressions: \boxed{...}
    boxed_match = re.search(r'\\boxed\s*\{([^}]+)\}', text)
    if boxed_match:
        expr = boxed_match.group(1)
        expr = expr.replace("\\times", "*").replace("\\div", "/").replace("\\cdot", "*")
        expr = expr.replace("x", "*").replace("×", "*").replace("÷", "/")
        # Remove LaTeX markers
        expr = re.sub(r'\\[()\[\]]', '', expr)
        expr = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr)
        expr = re.sub(r'\\[a-zA-Z]+', '', expr)
        return expr.strip()
    
    # Look for patterns like "the solution is: 6x(2+1+1)" or "final answer: 6 * (2 + 1 + 1)"
    patterns = [
        r'(?:solution|answer|result|final)[^0-9]*([0-9+\-*/(). xX×÷\\]+)(?:\s*=\s*24)?',
        r'([0-9+\-*/(). xX×÷\\]+)(?:\s*=\s*24)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            expr = match.group(1)
            # Clean up
            expr = expr.replace("x", "*").replace("×", "*").replace("÷", "/")
            expr = expr.replace("\\times", "*").replace("\\div", "/").replace("\\cdot", "*")
            # Remove LaTeX markers
            expr = re.sub(r'\\[()\[\]]', '', expr)
            expr = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr)
            expr = re.sub(r'\\[a-zA-Z]+', '', expr)
            # Only return if it looks like a real expression (has numbers and operators)
            if re.search(r'[0-9].*[+\-*/]', expr):
                return expr.strip()
    
    # Fallback: look for the last line that looks like a mathematical expression
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in reversed(lines):
        # Skip lines that are just numbers or fragments
        if re.search(r'^[0-9]+\.?\s*$', line):
            continue
        if re.search(r'[0-9+\-*/()\\]{3,}', line):
            line = line.replace("x", "*").replace("×", "*").replace("÷", "/")
            line = line.replace("\\times", "*").replace("\\div", "/").replace("\\cdot", "*")
            # Remove LaTeX markers
            line = re.sub(r'\\[()\[\]]', '', line)
            line = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', line)
            line = re.sub(r'\\[a-zA-Z]+', '', line)
            if '=' in line:
                line = line.split('=')[0]
            if re.search(r'[0-9].*[+\-*/]', line):
                return line.strip()
    return None


def generate_monologue(client, numbers, base_puzzle_id, pass_num, seed):
    """Generate a single AI monologue for a puzzle."""
    prompt = build_monologue_prompt(numbers)
    messages = [{"role": "user", "content": prompt}]
    
    t0 = time.time()
    res = client.complete(messages)
    elapsed = time.time() - t0
    
    transcript = res["content"]
    response = extract_final_expression(transcript)
    
    # Grade the response
    if response:
        norm_expr, valid, correct = grade_expression(response, numbers)
    else:
        norm_expr, valid, correct = None, None, None
    
    return {
        "puzzle_id": base_puzzle_id,
        "pass": pass_num,
        "seed": seed,
        "numbers": numbers,
        "transcript": transcript,
        "response": response or "",
        "response_normalized": norm_expr or "",
        "valid": valid,
        "correct": correct,
        "rt_s": elapsed,
        "cost_usd": res["cost"],
        "model_version": res["model_version"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------- #
# IO
# --------------------------------------------------------------------------- #
def load_puzzle_selection(csv_path: Path):
    df = pd.read_csv(csv_path)
    # Parse the "numbers" column which contains JSON arrays
    df["numbers"] = df["numbers"].apply(lambda s: tuple(json.loads(s)))
    # Add a Rank column based on selection_rank for consistency
    df["Rank"] = df["selection_rank"]
    return df.sort_values("selection_rank").reset_index(drop=True)


def append_jsonl(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        fh.flush()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args():
    p = argparse.ArgumentParser(description="Cell ④ AI monologue dataset generator")
    p.add_argument("--puzzle-csv", type=Path, default=PUZZLE_SELECTION)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--n-run", type=int, default=0, help="monologues to generate (0 = all in range)")
    p.add_argument("--start", type=int, default=1, help="1-based rank to start from")
    p.add_argument("--end", type=int, default=0, help="1-based rank to end at (0 = last)")
    p.add_argument("--pass_", type=int, default=1, help="pass number (1, 2, or 3) for multi-pass generation")
    p.add_argument("--seed", type=int, default=12345, help="random seed for this pass")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL)
    p.add_argument("--api-key", type=str, default=None)
    p.add_argument("--rpm", type=int, default=5, help="max requests/minute for THIS process")
    p.add_argument("--shard-label", type=str, default="", help="short label shown in progress bar")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    monologues_path = out_dir / "cell4_monologues.jsonl"
    
    puzzles = load_puzzle_selection(args.puzzle_csv)
    print(f"[main] loaded {len(puzzles)} puzzles")
    
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("ERROR: set OPENROUTER_API_KEY env var or pass --api-key")
    client = OpenRouter(api_key, model=args.model, rpm_limit=args.rpm)
    
    # Load already done
    done = set()
    if monologues_path.exists():
        with open(monologues_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    done.add(json.loads(line)["puzzle_id"])
    
    # Load already done
    done = set()
    if monologues_path.exists():
        with open(monologues_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    record = json.loads(line)
                    # Use combined key: puzzle_id + pass
                    done.add((record["puzzle_id"], record["pass"]))
    
    # Filter by rank range and done set
    start = max(1, args.start)
    end = args.end if args.end > 0 else len(puzzles)
    puzzles_filtered = puzzles[(puzzles['selection_rank'] >= start) & (puzzles['selection_rank'] <= end)].copy()
    puzzles_filtered = puzzles_filtered[~puzzles_filtered['selection_rank'].apply(lambda r: (f"g24_{int(r):04d}", args.pass_)).isin(done)]
    
    if args.n_run > 0:
        puzzles_filtered = puzzles_filtered.head(args.n_run)
    
    print(f"[main] {len(done)} already done; generating {len(puzzles_filtered)} monologue(s) now (ranks {start}..{end}, pass {args.pass_})")
    
    total_cost = 0.0
    desc = f"Monologues[{args.shard_label}]" if args.shard_label else "Generating monologues"
    progress = tqdm(puzzles_filtered.iterrows(), total=len(puzzles_filtered), desc=desc, unit="mono")
    for _, row in progress:
        base_puzzle_id = f"g24_{int(row['selection_rank']):04d}"
        puzzle_id = f"{base_puzzle_id}_p{args.pass_}"
        numbers = list(row["numbers"])
        
        monologue = generate_monologue(client, numbers, base_puzzle_id, args.pass_, args.seed)
        monologue["debate_id"] = puzzle_id  # Add debate_id to match debate format
        append_jsonl(monologues_path, monologue)
        total_cost += monologue["cost_usd"]
        
        progress.set_postfix({
            "valid": monologue['valid'],
            "correct": monologue['correct'],
            "rt": f"{monologue['rt_s']:.1f}s",
            "cost": f"${monologue['cost_usd']:.5f}"
        })
    
    print(f"\n[main] done. monologues -> {monologues_path}")
    print(f"[main] total cost: ${total_cost:.5f}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
