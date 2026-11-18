"""Compute book statistics from extracted activity JSON (raw counts only)."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "statistics"
OUT.mkdir(parents=True, exist_ok=True)

# country/venue normalisation (heuristic, documented limits)
COUNTRY_MAP = {
    "uganda": "Ouganda", "entebbe": "Ouganda", "nairobi": "Kenya", "kenya": "Kenya",
    "mombasa": "Kenya", "kephis": "Kenya", "addis": "Éthiopie", "ethiopia": "Éthiopie",
    "yaounde": "Cameroun", "yaoundé": "Cameroun", "douala": "Cameroun", "bafoussam": "Cameroun",
    "kribi": "Cameroun", "rome": "Italie", "italy": "Italie", "rome, italy": "Italie",
    "windhoek": "Namibie", "namibia": "Namibie", "libreville": "Gabon", "gabon": "Gabon",
    "cotonou": "Bénin", "benin": "Bénin", "abidjan": "Côte d'Ivoire", "cote d'ivoire": "Côte d'Ivoire",
    "kigali": "Rwanda", "rwanda": "Rwanda", "harare": "Zimbabwe", "zimbabwe": "Zimbabwe",
    "dar es salaam": "Tanzanie", "tanzania": "Tanzanie", "abuja": "Nigeria", "nigeria": "Nigeria",
    "geneva": "Suisse", "switzerland": "Suisse", "seoul": "Corée du Sud", "korea": "Corée du Sud",
    "brussels": "Belgique", "belgium": "Belgique", "malabo": "Guinée équatoriale",
    "mexico": "Mexique", "jamaica": "Jamaïque", "au-iapsc": "Cameroun (Siège)",
    "australia": "Australie", "auhq": "Cameroun (Siège)", "cpi": "Cameroun (Siège)",
    "minader": "Cameroun (Siège)", "hall": "Cameroun (Siège)", "conference hall": "Cameroun (Siège)",
}

TYPE_KEYWORDS = [
    ("Réunion / Gouvernance", ["meeting", "reunion", "réunion", "staff monthly", "all directors",
                                "head of missions", "steering", "general assembly", "assemblée",
                                "courtesy", "visite courtoisie", "preparation meeting", "prep"]),
    ("Atelier / Formation", ["workshop", "atelier", "training", "formation", "capacités", "capacite",
                             "write-shop", "writeshop", "seminar", "séminaire", "capacity-building",
                             "to-t", "tot", "train-the-trainer", "webinar"]),
    ("Mission / Voyage", ["mission", "visit", "travel", "deplacement"]),
    ("Webinaire / Visio", ["webinar", "virtual", "en ligne", "online", "zoom", "teams", "hybrid"]),
    ("Projet / Partenariat", ["project", "projet", "consortium", "partnership", "stdf", "app ",
                              "caadp", "contract", "consultancy", "call", "invitation"]),
]


def classify_type(activity: str, venue: str) -> str:
    text = (activity + " " + venue).lower()
    for label, kws in TYPE_KEYWORDS:
        if any(k in text for k in kws):
            return label
    return "Autre"


def detect_format(venue: str) -> str:
    v = venue.lower()
    if "online" in v or "zoom" in v or "teams" in v or "webinar" in v or "virtual" in v:
        if "hybrid" in v:
            return "Hybride"
        return "En ligne"
    if "hybrid" in v:
        return "Hybride"
    return "Présentiel"


def detect_country(venue: str) -> str | None:
    v = venue.lower()
    for key, country in COUNTRY_MAP.items():
        if key in v:
            return country
    return None


def main() -> None:
    rows = []
    for jf in sorted(RAW.glob("2026-*.json")):
        d = json.loads(jf.read_text(encoding="utf-8"))
        for a in d["activities"]:
            rows.append({
                "period": d["period"], "month": d["month"],
                "date": a["date"], "venue": a["venue"], "staff": a["staff"],
                "activity": a["activity"], "objectives": a["objectives_outcomes"],
                "status": a["status"],
                "country": detect_country(a["venue"]),
                "format": detect_format(a["venue"]),
                "type": classify_type(a["activity"], a["venue"]),
            })

    months = Counter(r["period"] for r in rows)
    countries = Counter(r["country"] for r in rows if r["country"])
    formats = Counter(r["format"] for r in rows)
    types = Counter(r["type"] for r in rows)

    stats = {
        "period": "2026-02 to 2026-11",
        "total_activities": len(rows),
        "months_documented": sorted(months),
        "months_missing": [f"2026-{m:02d}" for m in range(2, 12) if f"2026-{m:02d}" not in months],
        "activities_per_month": dict(sorted(months.items())),
        "distinct_countries": len(countries),
        "countries": dict(countries.most_common()),
        "format": dict(formats),
        "type": dict(types.most_common()),
        "unknown_country": sum(1 for r in rows if not r["country"]),
        "note": "Comptages réels issus des matrices .docm (octobre 2026 = version brouillon). "
                "Classification type/format/pays = heuristique à valider.",
    }
    (OUT / "stats_summary.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    # full enriched dataset for the book
    (OUT / "activities_enriched.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(stats, ensure_ascii=False, indent=2)[:2500])


if __name__ == "__main__":
    main()
