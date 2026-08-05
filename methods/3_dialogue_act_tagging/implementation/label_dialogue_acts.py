"""Dialogue-act tagging runner for Method 3.

Input: JSONL files where each line contains one sample.
Output: one JSONL file per sample. Each line is one sentence with fields:
  - text: the exact sentence text as returned by the LLM
  - start: character index where the sentence begins in the original sample
  - end: character index where the sentence ends in the original sample
  - label: the CAMS dialogue act tag as returned by the LLM

The LLM receives the full sample text and is responsible for sentence splitting.
The script only calls the LLM, parses the JSONL output, finds each returned
sentence in the original text, and writes the result.

Usage:
  python label_dialogue_acts.py \
      --input data/ai_debate/processed_ai_debate.jsonl \
      --output outputs/method3/ai_debate \
      --prompt ../CAMS_LLM_labeling_prompt.txt \
      --model tencent/hy3:free \
      --cell 3

The API key is read from OPENAI_API_KEY. OPENAI_BASE_URL should be set to the
OpenRouter endpoint (https://openrouter.ai/api/v1). The script uses the openai
Python SDK as the HTTP client, but OpenRouter is a separate service and you can
use any model ID available on OpenRouter via the --model argument.
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
import threading
import time
from pathlib import Path


class RateLimiter:
    """Sliding-window rate limiter.

    Ensures that no more than `max_requests` calls are made in any
    `window_seconds` interval. This is safer than a token bucket for APIs that
    enforce a strict rolling-window limit.
    """

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window = window_seconds
        self.timestamps = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def acquire(self, timeout: float | None = None) -> bool:
        """Block until a request slot is available within the window.

        Returns True if a slot was acquired, False if `timeout` expired.
        """
        with self.condition:
            deadline = None if timeout is None else time.time() + timeout
            while True:
                now = time.time()
                cutoff = now - self.window
                self.timestamps = [t for t in self.timestamps if t > cutoff]

                if len(self.timestamps) < self.max_requests:
                    self.timestamps.append(now)
                    return True

                if deadline is not None and time.time() >= deadline:
                    return False

                oldest = self.timestamps[0]
                wait_time = oldest + self.window - now
                if deadline is not None:
                    wait_time = min(wait_time, deadline - time.time())
                self.condition.wait(timeout=max(wait_time, 0.01))


def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def call_llm(
    prompt: str,
    user_message: str,
    model: str,
    max_tokens: int,
    temperature: float = 0.0,
) -> str:
    """Call the LLM via the OpenAI SDK client and return the raw text."""
    import openai

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=120, max_retries=3)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    message = response.choices[0].message
    content = message.content
    if content is None:
        # Fallback for reasoning models like Hy3 that return content in a separate field
        content = getattr(message, "reasoning", None) or getattr(message, "reasoning_content", None)
    if content is None:
        raise RuntimeError("Model returned empty content.")
    return content


def parse_llm_output(raw_output: str) -> list[dict]:
    """Parse the LLM's JSONL output into a list of text/label objects.

    The LLM is expected to return valid JSONL with one object per line. Labels
    are passed through as-is for post-processing.
    """
    labels = []
    for line in raw_output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        labels.append(
            {
                "text": obj.get("text", ""),
                "label": obj.get("label", ""),
            }
        )
    return labels


def _find_text_in_original(text: str, sent: str, search_from: int) -> tuple[int, int]:
    """Find sent in text starting at search_from.

    Returns (start, end) or (-1, -1) if not found. Tries exact match first,
    then whitespace-normalized match.
    """
    start = text.find(sent, search_from)
    if start != -1:
        return start, start + len(sent)

    # Fallback: exact match from the beginning (sentence may be out of order or
    # the cursor was advanced past a skipped sentence).
    start = text.find(sent)
    if start != -1:
        return start, start + len(sent)

    # Fallback: ignore whitespace differences.
    norm_text = re.sub(r"\s+", " ", text)
    norm_sent = re.sub(r"\s+", " ", sent)
    start = norm_text.find(norm_sent)
    if start != -1:
        # Cannot map back to exact original indices after whitespace collapse.
        return -1, -1

    return -1, -1


def attach_spans(text: str, labels: list[dict]) -> list[dict]:
    """Find each returned sentence in the original text and attach start/end.

    Uses a position cursor so repeated sentences are not all mapped to the first
    occurrence. If a sentence cannot be found, start/end are set to -1.
    """
    search_from = 0
    tagged = []
    for item in labels:
        sent = item["text"]
        start, end = _find_text_in_original(text, sent, search_from)
        if start != -1:
            search_from = end
        else:
            print(
                f"  Warning: could not find sentence in original text: {sent[:80]!r}",
                file=sys.stderr,
            )
        tagged.append(
            {"text": sent, "start": start, "end": end, "label": item["label"]}
        )
    return tagged


def _get_text(sample: dict, text_field: str | None) -> str:
    """Extract the text to classify from the sample."""
    if text_field:
        return sample.get(text_field, "")

    candidates = [
        "text",
        "full_text_no_labels",
        "transcript",
        "think_trace",
        "response_normalized",
        "response",
    ]
    for field in candidates:
        if field in sample and isinstance(sample[field], str):
            return sample[field]

    raise ValueError(
        f"No text field found in sample. Keys: {list(sample.keys())}. "
        "Use --text-field to specify one."
    )


def _get_sample_id(sample: dict, id_key: str | None, idx: int) -> str:
    """Extract a unique sample id from the sample."""
    if id_key:
        value = sample.get(id_key)
        if value is not None:
            return str(value)
        raise ValueError(f"Id key '{id_key}' not found in sample. Keys: {list(sample.keys())}")

    for field in ["debate_id", "source_item_id", "puzzle_id", "id", "sample_id"]:
        if field in sample and sample[field] is not None:
            return str(sample[field])

    if "pass" in sample and "seed" in sample:
        return f"pass{sample['pass']}_seed{sample['seed']}"

    return f"sample_{idx:04d}"


def _safe_filename(sample_id: str) -> str:
    """Replace characters that are unsafe in Windows filenames."""
    return re.sub(r'[<>:"/\\|?*]', "_", sample_id)


def label_sample(text: str, prompt: str, model: str, max_tokens: int) -> list[dict]:
    """Label one sample and return tagged sentences with start/end indices."""
    raw_output = call_llm(prompt, text, model, max_tokens)
    labels = parse_llm_output(raw_output)
    return attach_spans(text, labels)


def _process_one(
    idx: int,
    base_name: str,
    text: str,
    output_path: Path,
    prompt: str,
    model: str,
    max_tokens: int,
    rate_limiter: RateLimiter,
    semaphore: threading.Semaphore,
) -> None:
    """Process one sample inside a worker thread."""
    try:
        if not rate_limiter.acquire(timeout=None):
            raise RuntimeError("Rate limiter acquire timed out")
        tagged = label_sample(text, prompt, model, max_tokens)
        with open(output_path, "w", encoding="utf-8") as out_f:
            for item in tagged:
                out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  [{idx}] {base_name}: done ({len(tagged)} sentences)")
    except Exception as e:
        print(f"  [{idx}] {base_name}: error - {e}", file=sys.stderr)
    finally:
        semaphore.release()


def process_file(
    input_path: str,
    output_dir: str,
    prompt: str,
    model: str,
    max_tokens: int,
    rate_limit_rpm: int,
    max_workers: int,
    cell: str | None = None,
    id_key: str | None = None,
    text_field: str | None = None,
    limit: int | None = None,
) -> None:
    """Process all samples in one JSONL file with parallel workers."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cell_prefix = f"cell{cell}_" if cell else ""

    rate_limiter = RateLimiter(max_requests=rate_limit_rpm)
    # The semaphore bounds the number of tasks kept in memory at once.
    semaphore = threading.Semaphore(max_workers * 2)
    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        with open(input_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if limit is not None and idx >= limit:
                    break

                sample = json.loads(line)
                sample_id = _get_sample_id(sample, id_key, idx)
                text = _get_text(sample, text_field)

                safe_id = _safe_filename(sample_id)
                # Append the file index to the filename to guarantee uniqueness
                # when the same sample ID appears multiple times in the input.
                base_name = f"{cell_prefix}{safe_id}_{idx:04d}"
                output_path = out_dir / f"{base_name}.jsonl"

                # Resume: skip if a non-empty output file already exists.
                if output_path.exists() and output_path.stat().st_size > 0:
                    print(f"[{idx}] {base_name}: already exists, skipping")
                    continue

                print(f"[{idx}] {base_name}: {len(text)} chars")

                semaphore.acquire()
                future = executor.submit(
                    _process_one,
                    idx,
                    base_name,
                    text,
                    output_path,
                    prompt,
                    model,
                    max_tokens,
                    rate_limiter,
                    semaphore,
                )
                futures.append(future)

        # Wait for all submitted tasks to finish.
        concurrent.futures.wait(futures)


def main():
    parser = argparse.ArgumentParser(description="Label dialogue acts for Method 3")
    parser.add_argument("--input", required=True, help="Input JSONL file with samples")
    parser.add_argument("--output", required=True, help="Output directory for JSONL files")
    parser.add_argument("--prompt", default="../CAMS_LLM_labeling_prompt.txt", help="Path to LLM prompt")
    parser.add_argument("--model", default="gpt-4o", help="LLM model name")
    parser.add_argument("--max-tokens", type=int, default=32000, help="Max output tokens per LLM call (set high to allow long responses)")
    parser.add_argument("--rate-limit-rpm", type=int, default=19, help="Max requests per minute (default 19 to stay under OpenRouter free 20 RPM)")
    parser.add_argument("--max-workers", type=int, default=25, help="Max parallel worker threads")
    parser.add_argument("--cell", default=None, help="Cell number/label to include in output filenames")
    parser.add_argument("--id-key", default=None, help="JSON key to use as sample ID")
    parser.add_argument("--text-field", default=None, help="JSON key containing the text to classify")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N samples")
    args = parser.parse_args()

    prompt = load_prompt(args.prompt)
    process_file(
        args.input,
        args.output,
        prompt,
        args.model,
        args.max_tokens,
        rate_limit_rpm=args.rate_limit_rpm,
        max_workers=args.max_workers,
        cell=args.cell,
        id_key=args.id_key,
        text_field=args.text_field,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
