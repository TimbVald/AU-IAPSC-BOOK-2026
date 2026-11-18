"""Download free fonts (Google Fonts, OFL) for the book mockup."""
import re
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUT = Path("static/fonts")
OUT.mkdir(parents=True, exist_ok=True)

FAMILIES = {
    "Archivo": "ital,wght@0,500;0,600;0,700;0,800;0,900",
    "Source Serif 4": "opsz,wght@8..60,400;8..60,600;8..60,700",
    "Marcellus": "wght@400;700",
}

for family, axes in FAMILIES.items():
    css_url = ("https://fonts.googleapis.com/css2?family="
               + family.replace(" ", "+") + ":" + axes)
    req = urllib.request.Request(css_url, headers=UA)
    css = urllib.request.urlopen(req, timeout=60).read().decode()
    blocks = re.findall(
        r"font-family: '([^']+)';[^}]*?font-weight: (\d+)[^}]*?url\((https://[^)]+)\)",
        css, re.S)
    seen = set()
    for fam, weight, url in blocks:
        if url in seen:
            continue
        seen.add(url)
        fname = f"{fam.replace(' ', '_')}-{weight}.ttf"
        dest = OUT / fname
        if not dest.exists():
            urllib.request.urlretrieve(url, dest)
        print("OK", fname, dest.stat().st_size)
print("done ->", OUT)
