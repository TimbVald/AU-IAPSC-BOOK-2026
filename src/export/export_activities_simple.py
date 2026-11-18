"""Version simplifiee du calendrier : colonnes lisibles + couleurs par mois.

Colonnes : MONTH | DATES | Times | VENUE | COUNTRY | FORMAT | TYPE |
           STAFF CONCERNED | ACTIVITY | OBJECTIVES | STATUS OF REPORT
"""
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from date_parser import parse_date_range, status_for

ROOT = Path(__file__).resolve().parents[2]
ENR = ROOT / "data" / "statistics" / "activities_enriched.json"
BOOK = ROOT / "data" / "processed" / "book_data.json"
OUT = ROOT / "output" / "final" / "AU-IAPSC_Activites_Mensuelles_2026.xlsx"
OUT.parent.mkdir(parents=True, exist_ok=True)

MONTHS_FR = {
    "2026-02": "Février", "2026-03": "Mars", "2026-04": "Avril",
    "2026-05": "Mai", "2026-06": "Juin", "2026-07": "Juillet",
    "2026-08": "Août", "2026-09": "Septembre", "2026-10": "Octobre",
    "2026-11": "Novembre",
}
MONTH_ORDER = list(MONTHS_FR)

GREEN = "1E7A44"
DEEP = "0B3D24"
CHAR = "263338"
BORDEAUX = "92203A"
PALE = "F2F9F9"
LINE = "D8E2DC"

thin = Side(style="thin", color=LINE)
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD_FILL = PatternFill("solid", fgColor=GREEN)

# memes couleurs mensuelles que la version complete
MONTH_COLORS = {
    "2026-02": ("1E7A44", "EAF4EE", "FFFFFF"),
    "2026-03": ("B07C00", "FDF2D0", "FFFFFF"),
    "2026-04": ("92203A", "F9ECF0", "FFFFFF"),
    "2026-05": ("2E7D5B", "E8F4EF", "FFFFFF"),
    "2026-06": ("9C8F00", "FAF6DC", "263338"),
    "2026-07": ("B03A2E", "FBEAE8", "FFFFFF"),
    "2026-08": ("5B7F2A", "EFF4E4", "FFFFFF"),
    "2026-09": ("0B3D24", "E4EEE8", "FFFFFF"),
    "2026-10": ("7D122C", "F0E3E8", "FFFFFF"),
    "2026-11": ("8F6D00", "F8EFD2", "FFFFFF"),
}

HEAD_FONT = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="Calibri", size=9.5, color=CHAR)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

TIME_RE = __import__("re").compile(
    r"\d{1,2}[:hH]\d{2}\s*(?:[AP]\.?[Mm]\.?)?"
    r"(?:\s*[-–]\s*\d{1,2}[:hH]?\d{2}\s*(?:[AP]\.?[Mm]\.?)?)?")


def extract_time(date_str):
    m = TIME_RE.search(date_str or "")
    return m.group(0).replace("h", ":") if m else ""


def clean(s):
    return (s or "").replace("\xa0", " ").strip()


HEADERS = ["MONTH", "DATES", "Times", "VENUE", "COUNTRY", "FORMAT", "TYPE",
           "STAFF CONCERNED", "ACTIVITY", "OBJECTIVES, EXPECTED OUTCOMES",
           "STATUS OF REPORT"]
WIDTHS = [12, 34, 22, 36, 14, 13, 14, 32, 52, 52, 20]


def est_height(vals):
    lines = 1
    for v, w in zip(vals, WIDTHS):
        if not v:
            continue
        n = max(1, -(-len(str(v)) // max(int(w * 1.05), 8)))
        lines = max(lines, min(n, 12))
    return min(max(lines * 13 + 8, 26), 110)


def main():
    rows = json.loads(ENR.read_text(encoding="utf-8"))
    rows.sort(key=lambda r: (MONTH_ORDER.index(r["period"])
                             if r["period"] in MONTH_ORDER else 99,
                             r["date"]))

    book = json.loads(BOOK.read_text(encoding="utf-8"))
    obj_map = {}
    for m in book["months"].values():
        for a in m["activities"]:
            obj_map[(m["period"], clean(a["activity"]))] = a["objectives"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Activités"
    ws.sheet_view.showGridLines = False

    NCOL = len(HEADERS)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NCOL)
    t = ws.cell(1, 1,
                "RAPPORT DES ACTIVITÉS ANNUELLES DU CONSEIL PHYTOSANITAIRE "
                "INTER-AFRICAIN DE L'UNION AFRICAINE — 2026")
    t.font = Font(name="Calibri", size=13, bold=True, color=DEEP)
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    for i, (h, w) in enumerate(zip(HEADERS, WIDTHS), 1):
        c = ws.cell(2, i, h)
        c.font = HEAD_FONT
        c.fill = HEAD_FILL
        c.alignment = CENTER
        c.border = BORDER
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[2].height = 34

    r = 3
    for per in MONTH_ORDER:
        mrows = [x for x in rows if x["period"] == per]
        if not mrows:
            continue
        sat_hex, tint_hex, mc_text = MONTH_COLORS.get(per, (GREEN, PALE, "FFFFFF"))
        month_fill = PatternFill("solid", fgColor=sat_hex)
        tint_fill = PatternFill("solid", fgColor=tint_hex)
        start = r
        for x in mrows:
            ds, de, _, _ = parse_date_range(x["date"], per)
            status = status_for(per, ds, de, x["date"])
            obj = obj_map.get((per, clean(x["activity"])), "")
            vals = [extract_time(x["date"]), clean(x["date"]),
                    clean(x["venue"]), clean(x["country"]),
                    clean(x["format"]), clean(x["type"]),
                    clean(x["staff"]), clean(x["activity"]),
                    clean(obj), status]
            # ordre colonnes B..K : DATES, Times, VENUE, COUNTRY, FORMAT,
            # TYPE, STAFF, ACTIVITY, OBJECTIVES, STATUS
            vals = [clean(x["date"]), extract_time(x["date"])] + vals[2:]
            ws.row_dimensions[r].height = est_height(vals)
            for col, val in enumerate(vals, 2):
                c = ws.cell(r, col, val if val else None)
                c.font = BODY_FONT
                c.border = BORDER
                c.alignment = Alignment(wrap_text=True, vertical="center")
                c.fill = tint_fill
            r += 1
        if r - start > 1:
            ws.merge_cells(start_row=start, start_column=1,
                           end_row=r - 1, end_column=1)
        for rr in range(start, r):
            cc = ws.cell(rr, 1)
            cc.fill = month_fill
            cc.border = BORDER
        mc = ws.cell(start, 1, f"{MONTHS_FR[per].upper()}\n2026")
        mc.font = Font(name="Calibri", size=11, bold=True, color=mc_text)
        mc.alignment = CENTER

    ws.freeze_panes = "B3"
    ws.auto_filter.ref = f"A2:K{r - 1}"

    wb.save(OUT)
    print("xlsx ->", OUT)
    print("lignes:", len(rows))


if __name__ == "__main__":
    main()
