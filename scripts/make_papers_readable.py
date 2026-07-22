import sys
import fitz
from pathlib import Path

ROOT = Path("papers")
OUT = ROOT / "readable"
OUT.mkdir(exist_ok=True)

pdfs = [p for p in ROOT.rglob("*") if p.suffix.lower() == ".pdf" and "readable" not in p.relative_to(ROOT).parts]

for pdf_path in pdfs:
    rel = pdf_path.relative_to(ROOT)
    out_path = OUT / rel.with_suffix(".md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        # skip if already up to date
        if out_path.stat().st_mtime >= pdf_path.stat().st_mtime:
            print(f"[skip] {rel}")
            continue
    try:
        doc = fitz.open(str(pdf_path))
        parts = [f"---", f"source: {rel.as_posix()}", f"pages: {len(doc)}", f"---", ""]
        for i, page in enumerate(doc, 1):
            txt = page.get_text("text", sort=True)
            if txt:
                parts.append(f"<!-- Page {i} -->")
                parts.append(txt)
                parts.append("")
        doc.close()
        out_path.write_text("\n".join(parts), encoding="utf-8")
        print(f"[ok] {rel} -> {out_path.relative_to(ROOT).as_posix()}")
    except Exception as e:
        print(f"[ERR] {rel}: {e}", file=sys.stderr)
