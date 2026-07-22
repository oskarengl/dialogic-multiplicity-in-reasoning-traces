"""Local labeling tool for the Method 3 reliability worksheet (methods.md sec. 3e.1).

Serves a click-to-label UI at http://127.0.0.1:<port>/ plus a standalone CAMS cheat
sheet at /cheatsheet.html. Reads and writes outputs/method3/reliability/worksheet.csv
directly - the exact file reliability_sample.py --score reads - so labeling here is
fully compatible with the existing --score step, no export/import needed.

Every click is saved twice: (1) the full worksheet.csv is rewritten atomically
(write to a .tmp file, then os.replace), so the file on disk is never left
half-written; (2) the same event is appended to label_events.jsonl, an append-only
log, so the complete label history survives even if worksheet.csv were ever lost
or corrupted.

Usage (from implementation/):
    python label_tool.py            # opens a browser tab automatically
    python label_tool.py --port 9000 --no-browser
"""
import argparse
import csv
import json
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
WORKSHEET = ROOT / "outputs" / "method3" / "reliability" / "worksheet.csv"
EVENTS_LOG = ROOT / "outputs" / "method3" / "reliability" / "label_events.jsonl"
STATIC_DIR = Path(__file__).resolve().parent / "labeling_tool"
FIELDNAMES = ["cell", "cell_name", "doc_id", "sentence_idx", "text", "human_label"]

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/cheatsheet": ("cheatsheet.html", "text/html; charset=utf-8"),
    "/cheatsheet.html": ("cheatsheet.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/tag_schema.json": ("tag_schema.json", "application/json; charset=utf-8"),
}

_lock = threading.Lock()


def read_rows():
    with open(WORKSHEET, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(rows):
    tmp = WORKSHEET.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(WORKSHEET)  # atomic on the same filesystem


def log_event(row):
    with open(EVENTS_LOG, "a", encoding="utf-8") as f:
        rec = {"ts": datetime.now(timezone.utc).isoformat()}
        rec.update(row)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename, ctype):
        path = STATIC_DIR / filename
        if not path.exists():
            self.send_error(404, f"{filename} not found")
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in STATIC_FILES:
            filename, ctype = STATIC_FILES[self.path]
            self._send_file(filename, ctype)
        elif self.path == "/api/rows":
            with _lock:
                rows = read_rows()
            labeled = sum(1 for r in rows if r["human_label"].strip())
            self._send_json({"rows": rows, "total": len(rows), "labeled": labeled})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/label":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
            idx = int(body["index"])
            label = str(body["label"])
        except (ValueError, KeyError, json.JSONDecodeError):
            self._send_json({"error": "bad request"}, 400)
            return
        with _lock:
            rows = read_rows()
            if not (0 <= idx < len(rows)):
                self._send_json({"error": "index out of range"}, 400)
                return
            rows[idx]["human_label"] = label
            write_rows(rows)
            log_event({"index": idx, **{k: rows[idx][k] for k in FIELDNAMES}})
            labeled = sum(1 for r in rows if r["human_label"].strip())
        self._send_json({"ok": True, "labeled": labeled, "total": len(rows)})

    def log_message(self, fmt, *args):
        pass  # keep the console quiet - progress is visible in the browser


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    if not WORKSHEET.exists():
        print(f"No worksheet found at {WORKSHEET}")
        print("Run `python reliability_sample.py --sample` first.")
        return

    rows = read_rows()
    labeled = sum(1 for r in rows if r["human_label"].strip())
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Labeling tool running at {url}")
    print(f"Cheat sheet at {url}cheatsheet.html")
    print(f"Worksheet: {WORKSHEET}  ({labeled}/{len(rows)} already labeled)")
    print(f"Backup log: {EVENTS_LOG}")
    print("Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
