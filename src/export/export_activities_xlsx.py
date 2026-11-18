"""Export all AU-IAPSC activities (Feb-Nov 2026) to a formatted Excel file.

Sheets:
  1. Synthese  — KPIs and reading notes
  2. Activites — full table, one row per activity, autofilter + freeze panes

Status: November 2026 rows are flagged "En cours" (month still running).
"""

import datetime
import json
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from date_parser import parse_date_range, status_for

ROOT = Path(__file__).resolve().parents[2]
ENR = ROOT / "data" / "statistics" / "activities_enriched.json"
OUT = ROOT / "output" / "final" / "AU-IAPSC_Calendrier_Activites_2026.xlsx"
OUT.parent.mkdir(parents=True, exist_ok=True)

MONTHS_FR = {
    "2026-02": "Février", "2026-03": "Mars", "2026-04": "Avril",
    "2026-05": "Mai", "2026-06": "Juin", "2026-07": "Juillet",
    "2026-08": "Août", "2026-09": "Septembre", "2026-10": "Octobre",
    "2026-11": "Novembre",
}
MONTH_ORDER = list(MONTHS_FR)

# AU-IAPSC palette
GREEN = "1E7A44"
GREEN_LT = "3FAD49"
DEEP = "0B3D24"
CHAR = "263338"
BORDEAUX = "92203A"
YELLOW = "FFF200"
PALE = "F2F9F9"
LINE = "D8E2DC"

thin = Side(style="thin", color=LINE)
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD_FILL = PatternFill("solid", fgColor=GREEN)
ALT_FILL = PatternFill("solid", fgColor=PALE)
ONGOING_FILL = PatternFill("solid", fgColor="FDF6D8")

# Couleurs mensuelles — inspirées des logos UA (vert/or/rouge) et AU-IAPSC
# (vert #1E7A44, bordeaux #92203A, jaune #FFF200)
# period -> (couleur saturée cellule mois, teinte lignes, couleur texte mois)
MONTH_COLORS = {
    "2026-02": ("1E7A44", "EAF4EE", "FFFFFF"),   # vert IAPSC
    "2026-03": ("B07C00", "FDF2D0", "FFFFFF"),   # or UA
    "2026-04": ("92203A", "F9ECF0", "FFFFFF"),   # bordeaux IAPSC
    "2026-05": ("2E7D5B", "E8F4EF", "FFFFFF"),   # vert sapin
    "2026-06": ("9C8F00", "FAF6DC", "263338"),   # jaune doré UA
    "2026-07": ("B03A2E", "FBEAE8", "FFFFFF"),   # rouge brique UA
    "2026-08": ("5B7F2A", "EFF4E4", "FFFFFF"),   # olive
    "2026-09": ("0B3D24", "E4EEE8", "FFFFFF"),   # vert IAPSC
    "2026-10": ("7D122C", "F0E3E8", "FFFFFF"),   # bordeaux foncé
    "2026-11": ("8F6D00", "F8EFD2", "FFFFFF"),   # or foncé UA
}
TITLE_FONT = Font(name="Calibri", size=16, bold=True, color=DEEP)
SUB_FONT = Font(name="Calibri", size=10, color="8A9A94")
HEAD_FONT = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="Calibri", size=10, color=CHAR)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

TIME_RE = re.compile(
    r"\d{1,2}[:hH]\d{2}\s*(?:[AP]\.?[Mm]\.?)?"
    r"(?:\s*[-–]\s*\d{1,2}[:hH]?\d{2}\s*(?:[AP]\.?[Mm]\.?)?)?"
)


def extract_time(date_str: str) -> str:
    """Pull 'HH:MM' or 'HH:MM-HH:MM' out of free-text date fields."""
    m = TIME_RE.search(date_str or "")
    return m.group(0).replace("h", ":") if m else ""


DAY_RE = re.compile(r"(?<![\d:.])\d{1,2}(?![\d:.])")


def _days(date_str: str):
    return [int(m.group(0)) for m in DAY_RE.finditer(date_str or "")
            if 1 <= int(m.group(0)) <= 31]


def max_day(date_str: str):
    """Largest day-of-month mentioned in a free-text date (ignores times)."""
    days = _days(date_str)
    return max(days) if days else None


def first_day(date_str: str):
    """First plausible day-of-month in a free-text date (for sorting)."""
    days = _days(date_str)
    return days[0] if days else 99


def clean(s: str) -> str:
    return (s or "").replace("\xa0", " ").strip()


def main() -> None:
    rows = json.loads(ENR.read_text(encoding="utf-8"))
    rows.sort(key=lambda r: (MONTH_ORDER.index(r["period"])
                             if r["period"] in MONTH_ORDER else 99,
                             first_day(r["date"]), r["date"]))

    wb = Workbook()

    # ---------- Sheet 1: Synthèse ----------
    ws = wb.active
    ws.title = "Synthèse"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 46
    ws.column_dimensions["C"].width = 16

    ws["B2"] = "AU-IAPSC — Calendrier annuel des activités 2026"
    ws["B2"].font = TITLE_FONT
    ws["B3"] = "Inter-African Phytosanitary Council · Février à Novembre 2026"
    ws["B3"].font = SUB_FONT

    r = 5
    ws.cell(r, 2, "Indicateur").font = HEAD_FONT
    ws.cell(r, 2).fill = HEAD_FILL
    ws.cell(r, 3, "Valeur").font = HEAD_FONT
    ws.cell(r, 3).fill = HEAD_FILL
    for c in (2, 3):
        ws.cell(r, c).border = BORDER
        ws.cell(r, c).alignment = CENTER

    from collections import Counter
    sub = [x for x in rows if x["period"] != "2026-11"]
    kpis = [
        ("Activités réalisées (février–octobre 2026)", len(sub)),
        ("Mois documentés", 9),
        ("Pays / lieux distincts", len({x["country"] for x in sub if x["country"]})),
        ("En présentiel", sum(1 for x in sub if x["format"] == "Présentiel")),
        ("En ligne", sum(1 for x in sub if x["format"] == "En ligne")),
        ("Hybride", sum(1 for x in sub if x["format"] == "Hybride")),
        ("Activités novembre (en cours)", sum(1 for x in rows if x["period"] == "2026-11")),
        ("Total lignes du tableau", len(rows)),
    ]
    for i, (label, val) in enumerate(kpis):
        rr = r + 1 + i
        ws.cell(rr, 2, label).font = BODY_FONT
        ws.cell(rr, 2).border = BORDER
        ws.cell(rr, 2).alignment = WRAP
        v = ws.cell(rr, 3, val)
        v.font = Font(name="Calibri", size=11, bold=True, color=GREEN)
        v.border = BORDER
        v.alignment = CENTER
        if i % 2:
            for c in (2, 3):
                ws.cell(rr, c).fill = ALT_FILL

    r2 = r + len(kpis) + 3
    ws.cell(r2, 2, "Notes").font = Font(name="Calibri", size=11, bold=True, color=BORDEAUX)
    notes = [
        "• Toutes les activités de février à octobre 2026 ont eu lieu (confirmé).",
        "• Novembre 2026 : mois en cours — lignes signalées « En cours ».",
        "• DATE START / DATE END / TIME START / TIME END : valeurs parsées automatiquement depuis le champ Dates (format natif Excel, prêtes pour Power BI). DATES (SOURCE) conserve le texte original.",
        "• « Objectives » : reformulations éditoriales issues des matrices et documents de référence — à valider.",
        "• « Status of report » : Completed = réalisée (fév.–oct.) ; Ongoing = novembre ≤ 16 ; Not yet held = novembre après le 16 (au 16 novembre 2026).",
        "• Source : matrices mensuelles .docm AU-IAPSC.",
    ]
    for i, n in enumerate(notes):
        c = ws.cell(r2 + 1 + i, 2, n)
        c.font = Font(name="Calibri", size=9.5, color=CHAR)
        c.alignment = WRAP

    # ---------- Sheet 2: Activités (style « activites mensuelles ») ----------
    book = json.loads((ROOT / "data" / "processed" / "book_data.json")
                      .read_text(encoding="utf-8"))
    obj_map = {}
    for m in book["months"].values():
        for a in m["activities"]:
            obj_map[(m["period"], clean(a["activity"]))] = a["objectives"]

    wa = wb.create_sheet("Activités")
    wa.sheet_view.showGridLines = False
    wa.freeze_panes = "A3"

    # col A = mois (fusion verticale), cols B.. = données
    NCOL = 14  # A..N
    DATA_START = 2  # colonne B

    # row 1 : titre du rapport
    wa.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NCOL)
    t = wa.cell(1, 1,
                "RAPPORT DES ACTIVITÉS ANNUELLES DU CONSEIL PHYTOSANITAIRE "
                "INTER-AFRICAIN DE L'UNION AFRICAINE — 2026")
    t.font = Font(name="Calibri", size=13, bold=True, color=DEEP)
    t.alignment = Alignment(horizontal="center", vertical="center")
    wa.row_dimensions[1].height = 30

    headers = ["MONTH", "DATE START", "DATE END", "TIME START", "TIME END",
               "DATES (SOURCE)", "VENUE", "COUNTRY", "FORMAT", "TYPE",
               "STAFF CONCERNED", "ACTIVITY",
               "OBJECTIVES, EXPECTED OUTCOMES", "STATUS OF REPORT"]
    widths = [12, 12, 12, 10, 10, 26, 30, 14, 11, 18, 32, 48, 48, 17]
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        c = wa.cell(2, i, h)
        c.font = HEAD_FONT
        c.fill = HEAD_FILL
        c.alignment = CENTER
        c.border = BORDER
        wa.column_dimensions[get_column_letter(i)].width = w
    wa.row_dimensions[2].height = 34

    def est_height(vals, widths):
        """Estimate row height (pt) from wrapped text length."""
        lines = 1
        for v, w in zip(vals, widths):
            if not v:
                continue
            n = max(1, -(-len(str(v)) // max(int(w * 1.05), 8)))
            lines = max(lines, min(n, 12))
        return min(max(lines * 13 + 8, 26), 110)

    r = 3
    data_widths = widths[1:]
    for per in MONTH_ORDER:
        mrows = [x for x in rows if x["period"] == per]
        if not mrows:
            continue
        sat_hex, tint_hex, mc_text = MONTH_COLORS.get(per, (GREEN, PALE, "FFFFFF"))
        month_fill = PatternFill("solid", fgColor=sat_hex)
        tint_fill = PatternFill("solid", fgColor=tint_hex)
        start = r
        for k, x in enumerate(mrows):
            ds, de, ts, te = parse_date_range(x["date"], per)
            status = status_for(per, ds, de, x["date"])
            obj = obj_map.get((per, clean(x["activity"])), "")
            row_vals = [ds, de, ts, te, clean(x["date"]),
                        clean(x["venue"]), clean(x["country"]),
                        clean(x["format"]), clean(x["type"]),
                        clean(x["staff"]), clean(x["activity"]),
                        clean(obj), status]
            h = est_height([str(v) if v else "" for v in row_vals],
                           data_widths)
            wa.row_dimensions[r].height = h
            for col, val in enumerate(row_vals, DATA_START):
                c = wa.cell(r, col, val if val not in (None, "") else None)
                if col in (2, 3):
                    c.number_format = "yyyy-mm-dd"
                elif col in (4, 5):
                    c.number_format = "hh:mm"
                c.font = BODY_FONT
                c.border = BORDER
                c.alignment = Alignment(wrap_text=True, vertical="center")
                c.fill = tint_fill
            r += 1
        # mois fusionné verticalement dans la colonne A
        if r - start > 1:
            wa.merge_cells(start_row=start, start_column=1,
                           end_row=r - 1, end_column=1)
        for rr in range(start, r):
            cc = wa.cell(rr, 1)
            cc.fill = month_fill
            cc.border = BORDER
        mc = wa.cell(start, 1, f"{MONTHS_FR[per].upper()}\n2026")
        mc.font = Font(name="Calibri", size=11, bold=True, color=mc_text)
        mc.alignment = Alignment(horizontal="center", vertical="center",
                                 wrap_text=True)

    wb.save(OUT)
    print("xlsx ->", OUT)
    print("lignes:", len(rows))


if __name__ == "__main__":
    main()
