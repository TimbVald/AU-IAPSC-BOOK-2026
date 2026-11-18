"""Extract AU-IAPSC monthly activity matrices (.docm) into structured JSON/CSV.

Each monthly .docm contains one Word table:
  row 0  : month title (e.g. "FEBRUARY 2026")
  row 1  : column headers (Dates, Venue, Staff concerned, Activity,
           Objectives/Expected Outcomes, Status of report)
  rows 2+: one activity per row (6 cells)
"""

import csv
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "input" / "documents"
OUT_RAW = ROOT / "data" / "raw"
OUT_RAW.mkdir(parents=True, exist_ok=True)

MONTHS = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5, "JUNE": 6,
    "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11,
    "DECEMBER": 12,
}


def cell_text(tc: ET.Element) -> str:
    """Join paragraph texts inside a cell with ' ; '."""
    parts = []
    for p in tc.findall(".//w:p", NS):
        t = "".join(x.text or "" for x in p.findall(".//w:t", NS)).strip()
        if t:
            parts.append(t)
    return " ; ".join(parts)


def parse_docm(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find("w:body", NS)
    tbl = body.find(".//w:tbl", NS)
    if tbl is None:
        return {"file": path.name, "error": "no table found"}

    rows = tbl.findall("w:tr", NS)
    if not rows:
        return {"file": path.name, "error": "empty table"}

    # row 0: month title (single merged cell)
    title_cells = rows[0].findall("w:tc", NS)
    title = cell_text(title_cells[0]) if title_cells else ""
    m = re.search(r"([A-Za-z]+)\s+(20\d\d)", title)
    month_name, year = (m.group(1).upper(), int(m.group(2))) if m else (None, None)
    month_num = MONTHS.get(month_name)

    # row 1: headers
    header_cells = rows[1].findall("w:tc", NS)
    headers = [cell_text(c) for c in header_cells]

    activities = []
    for row in rows[2:]:
        cells = row.findall("w:tc", NS)
        if not cells:
            continue
        values = [cell_text(c) for c in cells]
        values += [""] * (6 - len(values))
        values = values[:6]
        if not any(values):
            continue
        activities.append(dict(zip(
            ["date", "venue", "staff", "activity",
             "objectives_outcomes", "status"], values)))

    # paragraphs located after the table (notes / next-month previews)
    trailing = []
    seen_tbl = False
    for el in body:
        if el.tag.endswith("}tbl"):
            seen_tbl = True
            continue
        if seen_tbl and el.tag.endswith("}p"):
            t = "".join(x.text or "" for x in el.findall(".//w:t", NS)).strip()
            if t:
                trailing.append(t)

    return {
        "file": path.name,
        "month_title": title,
        "month": month_name,
        "month_num": month_num,
        "year": year,
        "period": f"{year}-{month_num:02d}" if month_num else None,
        "headers": headers,
        "activities": activities,
        "trailing_notes": trailing,
    }


def main() -> None:
    all_rows = []
    for docm in sorted(DOCS_DIR.glob("*.docm")):
        data = parse_docm(docm)
        period = data.get("period") or "unknown"
        out = OUT_RAW / f"{period}_{data['month'] or 'unknown'}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        n = len(data.get("activities", []))
        notes = len(data.get("trailing_notes", []))
        print(f"{docm.name:55s} -> {out.name:35s} {n:3d} act. {notes} notes")
        for i, a in enumerate(data.get("activities", []), 1):
            all_rows.append({
                "period": period, "month": data.get("month"),
                "idx": i, **a,
            })

    csv_path = OUT_RAW / "activities_all.csv"
    fields = ["period", "month", "idx", "date", "venue", "staff",
              "activity", "objectives_outcomes", "status"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nTotal: {len(all_rows)} activites -> {csv_path}")


if __name__ == "__main__":
    main()
