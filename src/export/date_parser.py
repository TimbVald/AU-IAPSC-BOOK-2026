"""Heuristic parser for the free-text date fields of the AU-IAPSC monthly
activity matrices -> native date/time values for Excel / Power BI.

parse_date_range(date_str, period) -> (date_start, date_end,
                                        time_start, time_end)
Missing or unparseable parts are returned as None (empty cells).
"""

import datetime
import re

MONTH_NUM = {}
for _names, _n in [
    (["janvier", "january", "jan", "janv"], 1),
    (["février", "fevrier", "february", "feb", "févr", "fevr"], 2),
    (["mars", "march", "mar"], 3),
    (["avril", "april", "avr"], 4),
    (["mai", "may"], 5),
    (["juin", "june", "jun"], 6),
    (["juillet", "july", "jul", "juil"], 7),
    (["août", "aout", "august", "aug"], 8),
    (["septembre", "september", "sept", "sep"], 9),
    (["octobre", "october", "oct"], 10),
    (["novembre", "november", "nov"], 11),
    (["décembre", "decembre", "december", "dec", "déc"], 12),
]:
    for _w in _names:
        MONTH_NUM[_w] = _n

_MONTH_RE = re.compile(
    r"\b(" + "|".join(sorted(MONTH_NUM, key=len, reverse=True)) + r")\b",
    re.IGNORECASE)

# HH:MM am/pm | HH:MM / HHhMM | '16h' (heure seule)
_TIME_TOK_RE = re.compile(
    r"(\d{1,2})\s*[:hH]\s*(\d{2})\s*([apAP])\.?\s*[mM]\.?"
    r"|(\d{1,2})\s*[:hH]\s*(\d{2})"
    r"|(\d{1,2})\s*[hH](?![\d:])")

_SLASH_DATE_RE = re.compile(r"(\d{1,2})\s*[/\.]\s*(\d{1,2})"
                            r"(?:\s*[/\.]\s*(\d{2,4}))?")
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_DAY_NUM_RE = re.compile(r"(?<![\d])\d{1,2}(?![\d])")


def clean(s):
    return (s or "").replace("\xa0", " ").strip()


def _mask(text, spans):
    chars = list(text)
    for a, b in spans:
        for i in range(a, min(b, len(chars))):
            chars[i] = " "
    return "".join(chars)


def _to_time(h, m, ampm):
    h = int(h)
    if ampm:
        if ampm.lower() == "p" and h < 12:
            h += 12
        elif ampm.lower() == "a" and h == 12:
            h = 0
    try:
        return datetime.time(h % 24, int(m))
    except ValueError:
        return None


def parse_date_range(date_str, period):
    s = clean(date_str)
    if not s:
        return None, None, None, None
    pm = int(period[-2:]) if period else 1

    # 1) times -> mask them so their digits are not read as days
    times = []          # (pos, time, ampm_letter_or_None)
    spans = []
    for m in _TIME_TOK_RE.finditer(s):
        ampm = None
        if m.group(1):                        # HH:MM + am/pm
            t = _to_time(m.group(1), m.group(2), m.group(3))
            ampm = m.group(3)
        elif m.group(4):                      # HH:MM / HHhMM
            t = _to_time(m.group(4), m.group(5), None)
        else:                                 # '16h' -> 16:00
            t = _to_time(m.group(6), 0, None)
        if t:
            times.append((m.start(), t, (ampm or "").lower() or None))
            spans.append(m.span())
    work = _mask(s, spans)
    times.sort(key=lambda x: x[0])
    # plage 'X - Y PM' : le AM/PM final s'applique aussi au début si non précisé
    if len(times) >= 2 and times[-1][2] == "p" and not times[0][2] \
            and times[0][1].hour < 12:
        t0 = times[0][1]
        times[0] = (times[0][0],
                    datetime.time((t0.hour + 12) % 24, t0.minute), "p")
    t_start = times[0][1] if times else None
    t_end = times[1][1] if len(times) > 1 else None

    ym = _YEAR_RE.search(work)
    year_exp = int(ym.group(1)) if ym else None

    # 2) slash date '26/02' or '26/02/2026' -> single day
    sm = _SLASH_DATE_RE.search(work)
    if sm:
        try:
            d, mn = int(sm.group(1)), int(sm.group(2))
            y = sm.group(3)
            yr = int(y) if y else (year_exp or 2026)
            if y and len(y) == 2:
                yr = 2000 + yr
            dt = datetime.date(yr, mn, d)
            return dt, dt, t_start, t_end
        except ValueError:
            pass

    # 3) month names
    month_matches = list(_MONTH_RE.finditer(work))
    mts = [(m.start(), MONTH_NUM[m.group(0).lower()]) for m in month_matches]
    work2 = _mask(work, [m.span() for m in month_matches])

    # 4) remaining day numbers (1-31)
    days = [int(m.group(0)) for m in _DAY_NUM_RE.finditer(work2)
            if 1 <= int(m.group(0)) <= 31]

    if mts:
        m_start, m_end = mts[0][1], mts[-1][1]
    else:
        m_start = m_end = pm
    d_start = days[0] if days else None
    d_end = days[-1] if len(days) > 1 else d_start
    if d_start is None:
        return None, None, t_start, t_end

    y_start = year_exp or 2026
    y_end = (year_exp or 2026) + (1 if m_end < m_start else 0)
    try:
        ds = datetime.date(y_start, m_start, d_start)
    except ValueError:
        ds = None
        # 'Monday 31 - Friday 04 September' : le jour de début peut
        # appartenir au mois précédent quand il est invalide (ex. 31 sept.)
        if d_start and d_start > 28 and m_start == m_end:
            pm2 = m_start - 1 or 12
            py2 = y_start - 1 if m_start == 1 else y_start
            try:
                ds = datetime.date(py2, pm2, d_start)
            except ValueError:
                pass
    try:
        de = datetime.date(y_end, m_end, d_end) if d_end else ds
    except ValueError:
        de = ds
    if ds and de and de < ds:
        de = ds if m_end == m_start else None
    return ds, de, t_start, t_end


def status_for(period, ds, de, raw_date, cutoff_day=16):
    """Completed / Ongoing / Not yet held (November cutoff = 16 Nov 2026)."""
    if period != "2026-11":
        return "Completed"
    latest = None
    for d in (ds, de):
        if d and (latest is None or d > latest):
            latest = d
    if latest is None:
        # fallback on raw day numbers
        ds_raw = [int(m.group(0)) for m in _DAY_NUM_RE.finditer(clean(raw_date) or "")
                  if 1 <= int(m.group(0)) <= 31]
        latest_day = max(ds_raw) if ds_raw else 0
        return "Not yet held" if latest_day > cutoff_day else "Ongoing"
    return "Not yet held" if latest.day > cutoff_day else "Ongoing"


if __name__ == "__main__":
    tests = [
        ("Monday 02 – Wednesday 04", "2026-11"),
        ("26/02 ; 10:00-11:00", "2026-02"),
        ("24 February 2026, 2:00- 3:00 PM", "2026-02"),
        ("Friday, 27,  11:00 AM-12:30 PM.", "2026-03"),
        ("Sunday 29 Nov - Friday 04 Dec", "2026-11"),
        ("Monday 16 – Saturday 21", "2026-11"),
        ("Thursday 05 ; 13:00-15:00 (EAT)", "2026-11"),
        ("Friday 06 ; 16h (EAT)", "2026-11"),
        ("17-18 February", "2026-02"),
        ("Monday 30 11:00-12:00.", "2026-07"),
        ("Jeudi 5 ; 10:00-11:30", "2026-08"),
    ]
    for d, p in tests:
        print(f"{d!r:55} -> {parse_date_range(d, p)}")
