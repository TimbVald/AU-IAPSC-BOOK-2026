"""Render the full AU-IAPSC book: Jinja2 template -> HTML -> WeasyPrint -> PDF."""
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "book_data.json"
TPL = ROOT / "templates" / "book"
OUT = ROOT / "output" / "final" / "AU-IAPSC_Livre_Activites_2026.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

book = json.loads(DATA.read_text(encoding="utf-8"))

env = Environment(
    loader=FileSystemLoader(str(TPL)),
    autoescape=select_autoescape(["html"]),
)
tpl = env.get_template("book.html")
html = tpl.render(book=book)

html_path = ROOT / "output" / "drafts" / "book_rendered.html"
html_path.parent.mkdir(parents=True, exist_ok=True)
html_path.write_text(html, encoding="utf-8")

HTML(filename=str(html_path), base_url=str(ROOT)).write_pdf(str(OUT))
print("PDF ->", OUT, OUT.stat().st_size, "octets")
