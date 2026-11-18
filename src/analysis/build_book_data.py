"""Build book_data.json for the Jinja2 book templates.

- Loads data/statistics/activities_enriched.json
- Marks every activity "Realisee - documentee" (user confirmed all took place)
- Drafts objectives/outcomes text by activity type (editorial, to validate)
- Selects the most important activities per month for full treatment
- Computes February-October 2026 stats (November still in progress)
- Assigns editorial photos (newsletter/annual archives) to feature slots
"""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENR = ROOT / "data" / "statistics" / "activities_enriched.json"
OUT = ROOT / "data" / "processed" / "book_data.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

MONTHS_FR = {
    "2026-02": ("Février", "février"), "2026-03": ("Mars", "mars"),
    "2026-04": ("Avril", "avril"), "2026-05": ("Mai", "mai"),
    "2026-06": ("Juin", "juin"), "2026-07": ("Juillet", "juillet"),
    "2026-08": ("Août", "août"), "2026-09": ("Septembre", "septembre"),
    "2026-10": ("Octobre", "octobre"), "2026-11": ("Novembre", "novembre"),
}

SCOPE_MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
                "2026-07", "2026-08", "2026-09", "2026-10"]
ONGOING_MONTH = "2026-11"

OBJECTIVES_BY_TYPE = {
    "Réunion / Gouvernance":
        "Renforcer la coordination et la gouvernance institutionnelle de l'AU-IAPSC.",
    "Atelier / Formation":
        "Renforcer les capacités phytosanitaires des organisations nationales et des experts africains.",
    "Mission / Voyage":
        "Contribuer à l'harmonisation phytosanitaire régionale et au partage d'expériences.",
    "Webinaire / Visio":
        "Diffuser les connaissances phytosanitaires et promouvoir les échanges techniques à distance.",
    "Projet / Partenariat":
        "Faire avancer les partenariats et projets de coopération phytosanitaire continentale.",
    "Autre":
        "Contribuer à la mise en œuvre du mandat phytosanitaire de l'AU-IAPSC.",
}

HIGHLIGHT_KEYWORDS = [
    "CPM 20", "IPPC Regional Workshop", "Africa Food Systems Forum",
    "International Day of Plant Health", "Banana Bunchy Top",
    "Phytosanitary Programme", "CAADP", "GreenPass", "STDF",
    "Trade and Development Forum", "NAPPO", "WAVE", "AfCFTA",
    "Steering Committee", "Semences", "Seed", "Barry Callebaut",
    "Team Building", "team building",
]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def draft_objectives(act: dict) -> str:
    base = OBJECTIVES_BY_TYPE.get(act["type"], OBJECTIVES_BY_TYPE["Autre"])
    t = act["activity"]
    if "CPM" in t or "Conference of Parties" in t or "Conférence" in t:
        return ("Porter la voix de l'Afrique à la Conférence des Parties de la CIPV "
                "et contribuer à l'agenda phytosanitaire mondial.")
    if "Banana Bunchy" in t or "BBTD" in t:
        return ("Renforcer la coordination africaine de la gestion du bunchy top "
                "de la bananier à travers le projet STDF.")
    if "IPPC" in t or "CIPV" in t or "Phytosanitary Convention" in t:
        return ("Contribuer aux travaux régionaux de la CIPV pour l'Afrique et "
                "à l'harmonisation des mesures phytosanitaires.")
    if "CAADP" in t or "La H" in t or "Kampala" in t or "Havane" in t:
        return ("Soutenir la domestisation et la mise en œuvre des lignes "
                "directrices du CAADP pour l'agriculture africaine.")
    if "Phytosanitary Programme" in t or "APP" in t or "ToT" in t or "Train-the-Trainer" in t:
        return ("Déployer la Phase 3 du Programme Phytosanitaire Africain et "
                "former les formateurs des pays membres.")
    if "Day of Plant Health" in t or "IDPH" in t:
        return ("Célébrer la Journée internationale de la santé des végétaux "
                "et sensibiliser au rôle de la phyto protection alimentaire.")
    if "GreenPass" in t or "Seed" in t or "Semence" in t:
        return ("Faciliter les échanges régionaux de semences et de matériel "
                "végétatif dans le respect des normes phytosanitaires.")
    if "STDF" in t:
        return ("Assurer la coordination du projet STDF sur la gestion du "
                "bunchy top de la bananier en Afrique.")
    if "Biopesticide" in t or "biopesticide" in t:
        return ("Contribuer à l'élaboration de directives continentales sur "
                "les biopesticides et les alternatives chimiques.")
    if "Steering Committee" in t:
        return ("Assurer la gouvernance et le pilotage stratégique de l'AU-IAPSC.")
    return base


def is_highlight(act: dict) -> bool:
    t = (act["activity"] + " " + act["venue"]).lower()
    return any(k.lower() in t for k in HIGHLIGHT_KEYWORDS)


def importance_score(a: dict) -> float:
    s = 0.0
    if a["highlight"]:
        s += 3.0
    if a["type"] == "Mission / Voyage":
        s += 1.0
    if a["type"] == "Atelier / Formation":
        s += 0.6
    if a["format"] == "Présentiel":
        s += 0.4
    if a["country"] and a["country"] != "International / En ligne":
        s += 0.3
    return s


def select_important(acts: list) -> list:
    """Return selected activities (chronological order), cap ~6 per month."""
    scored = sorted(enumerate(acts), key=lambda p: -importance_score(p[1]))
    sel_idx = {i for i, _ in scored[:6] if importance_score(_) > 0}
    # ensure at least 3 selected when possible
    for i, a in scored:
        if len(sel_idx) >= 3:
            break
        sel_idx.add(i)
    return [a for i, a in enumerate(acts) if i in sel_idx]


def main() -> None:
    rows = json.loads(ENR.read_text(encoding="utf-8"))

    months = {}
    for per in sorted({r["period"] for r in rows}):
        mrows = [r for r in rows if r["period"] == per]
        acts = []
        for i, r in enumerate(mrows, 1):
            acts.append({
                "id": f"{per}-{i:02d}",
                "date": r["date"], "venue": r["venue"], "staff": r["staff"],
                "activity": r["activity"], "country": r["country"],
                "format": r["format"], "type": r["type"],
                "objectives": draft_objectives(r),
                "status": "Réalisée — documentée",
                "source": "Matrice mensuelle .docm",
                "highlight": is_highlight(r),
            })
        name, name_lower = MONTHS_FR[per]
        ongoing = per == ONGOING_MONTH
        selected = select_important(acts) if not ongoing else []
        sel_ids = {a["id"] for a in selected}
        months[per] = {
            "period": per, "name": name, "name_lower": name_lower,
            "count": len(acts), "ongoing": ongoing,
            "activities": acts,
            "selected": selected,
            "others": [a for a in acts if a["id"] not in sel_ids],
            "highlights": [a for a in acts if a["highlight"]],
        }

    # duplicates across months (same event in two matrices)
    seen, dupes = {}, []
    for per, m in months.items():
        for a in m["activities"]:
            key = re.sub(r"[^a-z0-9]", "", a["activity"].lower())[:60]
            if key in seen:
                dupes.append({"activity": a["activity"], "months": [seen[key], per]})
            else:
                seen[key] = per

    # ---- stats for February-October scope ----
    sub = [r for r in rows if r["period"] in SCOPE_MONTHS]

    # staff mobilisation: normalise roles into groups (activity may count
    # in several groups — a meeting can involve coordinator + SSO-P + SSO-E)
    STAFF_GROUPS = [
        ("Coordinateur / coordination", ["coordinator", "coordonnateur", "coordination"]),
        ("SSO-P", ["sso-p", "ssop", "ssso-p", "sso p"]),
        ("SSO-E", ["sso-e", "ssoe", "sso e"]),
        ("Secrétariat & administration", ["admin", "secretary", "finance", "secrétaire", "secrétaire"]),
        ("Équipe complète / staff concerné", ["all staff", "all available", "staff concerned", "concerned staff", "toute l'équipe", "equipo"]),
    ]
    staff_counts = Counter()
    staff_named = 0
    staff_filled = 0
    for r in sub:
        s = r["staff"].replace("\xa0", " ").lower()
        if not s.strip():
            continue
        staff_filled += 1
        matched = False
        for label, keys in STAFF_GROUPS:
            if any(k in s for k in keys):
                staff_counts[label] += 1
                matched = True
        if not matched:
            staff_named += 1  # named individuals / partners / other roles
    staff_roles = [(k, v) for k, v in staff_counts.most_common()]

    stats = {
        "total": len(sub),
        "months": len(SCOPE_MONTHS),
        "per_month": {k: sum(1 for r in sub if r["period"] == k)
                      for k in SCOPE_MONTHS},
        "countries": len({r["country"] for r in sub if r["country"]}),
        "format": dict(Counter(r["format"] for r in sub)),
        "type": dict(Counter(r["type"] for r in sub).most_common()),
        "selected_total": sum(len(months[k]["selected"]) for k in SCOPE_MONTHS),
        "ongoing_count": sum(1 for r in rows if r["period"] == ONGOING_MONTH),
        "staff_filled": staff_filled,
        "staff_empty": len(sub) - staff_filled,
        "staff_roles": staff_roles,
        "staff_other": staff_named,
    }

    # photo pool (newsletter archives) — filenames in static/images/book/
    photos = sorted(p.name for p in (ROOT / "static" / "images" / "book").glob("*.png"))
    photos = [p for p in photos if p.startswith("nl_") or p.startswith("book_nl_")]

    book = {
        "title": "Livre des Activités",
        "subtitle": "AU-IAPSC — Calendrier annuel des activités",
        "period": "février — octobre 2026",
        "stats": stats,
        "months": months,
        "duplicates": dupes,
        "total": len(sub),
        "total_all": len(rows),
        "photos": photos,
    }
    OUT.write_text(json.dumps(book, ensure_ascii=False, indent=2), encoding="utf-8")
    print("book_data ->", OUT)
    print("total fev-oct:", len(sub), "| total incl. nov:", len(rows),
          "| mois:", len(months), "| doublons:", len(dupes))
    print("stats:", json.dumps(stats["per_month"]), "| photos:", len(photos))
    for d in dupes:
        print("  DUP:", d["months"], d["activity"][:70])


if __name__ == "__main__":
    main()
