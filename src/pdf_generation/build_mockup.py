"""Render the 5-page book mockup HTML -> PDF via WeasyPrint."""
from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "templates" / "mockup" / "book_mockup.html"
OUT = ROOT / "output" / "previews" / "book_mockup.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

HTML(filename=str(SRC), base_url=str(ROOT)).write_pdf(str(OUT))
print("PDF ->", OUT, OUT.stat().st_size, "octets")
