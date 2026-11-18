"""Generate book charts (matplotlib) in the AU-IAPSC palette -> static/charts/.

Scope: February-October 2026 (November is still in progress).
"""
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
CH = ROOT / "static" / "charts"
CH.mkdir(parents=True, exist_ok=True)

GREEN = "#1E7A44"
GREEN_LT = "#3FAD49"
CHARCOAL = "#263338"
BORDEAUX = "#92203A"
YELLOW = "#FFF200"
GRAY = "#8A9A94"

for f in (ROOT / "static" / "fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))
plt.rcParams["font.family"] = "Archivo"
plt.rcParams["text.color"] = CHARCOAL
plt.rcParams["axes.edgecolor"] = "#D8E2DC"

rows = json.loads((ROOT / "data" / "statistics" / "activities_enriched.json")
                  .read_text(encoding="utf-8"))
rows = [r for r in rows if r["period"] != "2026-11"]  # fev-oct seulement

MONTH_ORDER = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
               "2026-07", "2026-08", "2026-09", "2026-10"]
MONTH_LABELS = ["Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct"]
per_month = Counter(r["period"] for r in rows)
vals = [per_month[k] for k in MONTH_ORDER]

# --- monthly bar chart ---
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
colors = [GREEN if v < 15 else BORDEAUX for v in vals]
bars = ax.bar(MONTH_LABELS, vals, color=colors, width=0.62, zorder=3)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.4, str(v), ha="center",
            fontsize=12, fontweight="bold", color=CHARCOAL)
ax.set_ylim(0, max(vals) * 1.22)
ax.set_ylabel("Activités", fontsize=11, color=CHARCOAL)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left"]].set_visible(False)
ax.tick_params(axis="x", labelsize=11)
ax.tick_params(axis="y", labelsize=9)
ax.yaxis.grid(True, color="#E4ECE7", zorder=0)
ax.set_axisbelow(True)
ax.set_title("Activités documentées par mois — février à octobre 2026",
             fontsize=13, fontweight="bold", color=CHARCOAL, loc="left", pad=12)
fig.text(0.99, 0.01, "Novembre 2026 : mois en cours — non inclus",
         fontsize=8, color=GRAY, ha="right", style="italic")
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(CH / "activities_per_month.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close(fig)

# --- format donut ---
fmt = Counter(r["format"] for r in rows)
order = ["Présentiel", "En ligne", "Hybride"]
fracs = [fmt.get(k, 0) for k in order]
fig, ax = plt.subplots(figsize=(4.2, 3.6), dpi=200)
w, t, a = ax.pie(fracs, colors=[GREEN, YELLOW, BORDEAUX], startangle=90,
                 counterclock=False,
                 wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
                 autopct=lambda p: f"{p:.0f}%" if p > 4 else "")
ax.text(0, 0.06, str(sum(fracs)), ha="center", va="center",
        fontsize=26, fontweight="bold", color=CHARCOAL)
ax.text(0, -0.14, "activités", ha="center", va="center",
        fontsize=10, color=GRAY)
ax.legend(w, [f"{k} — {v}" for k, v in zip(order, fracs)],
          loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False,
          fontsize=10, labelcolor=CHARCOAL)
ax.set_title("Modalités de tenue", fontsize=12, fontweight="bold",
             color=CHARCOAL, loc="left")
fig.tight_layout()
fig.savefig(CH / "format_donut.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close(fig)

# --- top countries horizontal bars ---
countries = Counter(r["country"] for r in rows if r["country"])
top = countries.most_common(10)
names = [k.replace(" (Siège)", " (siège)") for k, _ in top]
vals2 = [v for _, v in top]
fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
y = range(len(names))[::-1]
ax.barh(y, vals2, color=GREEN_LT, height=0.62, zorder=3)
for yi, v in zip(y, vals2):
    ax.text(v + 0.15, yi, str(v), va="center", fontsize=11,
            fontweight="bold", color=CHARCOAL)
ax.set_yticks(list(y), names, fontsize=10.5, color=CHARCOAL)
ax.set_xlim(0, max(vals2) * 1.18)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True, color="#E4ECE7", zorder=0)
ax.set_axisbelow(True)
ax.set_title("Principaux pays / lieux d'activités (février–octobre 2026)",
             fontsize=12, fontweight="bold", color=CHARCOAL, loc="left", pad=10)
fig.tight_layout()
fig.savefig(CH / "top_countries.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close(fig)

# --- activity types horizontal bars (enrichissement dashboard) ---
types = Counter(r["type"] for r in rows)
top_t = types.most_common(8)
names_t = [k for k, _ in top_t]
vals_t = [v for _, v in top_t]
fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
y = range(len(names_t))[::-1]
ax.barh(y, vals_t, color=GREEN, height=0.62, zorder=3)
for yi, v in zip(y, vals_t):
    ax.text(v + 0.15, yi, str(v), va="center", fontsize=11,
            fontweight="bold", color=CHARCOAL)
ax.set_yticks(list(y), names_t, fontsize=10.5, color=CHARCOAL)
ax.set_xlim(0, max(vals_t) * 1.18)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True, color="#E4ECE7", zorder=0)
ax.set_axisbelow(True)
ax.set_title("Activités par type (février–octobre 2026)",
             fontsize=12, fontweight="bold", color=CHARCOAL, loc="left", pad=10)
fig.tight_layout()
fig.savefig(CH / "types_bars.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close(fig)

print("charts ->", CH)
for p in CH.glob("*.png"):
    print(" ", p.name, p.stat().st_size)
