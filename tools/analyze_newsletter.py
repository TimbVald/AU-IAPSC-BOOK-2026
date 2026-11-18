"""Analyze the reference newsletter PDF: fonts, colors, layout, images."""
import glob
import json
import collections
import pymupdf

path = glob.glob('input/reference/AU*NEWSLETTER*.pdf')[0]
doc = pymupdf.open(path)

# --- fonts & colors across document ---
font_counter = collections.Counter()
color_counter = collections.Counter()
size_counter = collections.Counter()

for pno in range(doc.page_count):
    d = doc[pno].get_text("dict")
    for block in d["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                font_counter[span["font"]] += len(text)
                size_counter[round(span["size"], 1)] += len(text)
                color_counter[span["color"]] += len(text)

print("=== FONTS (par volume de texte) ===")
for f, c in font_counter.most_common(15):
    print(f"  {f}: {c}")
print("\n=== TAILLES ===")
for s, c in sorted(size_counter.items()):
    print(f"  {s}pt: {c}")
print("\n=== COULEURS (hex) ===")
for col, c in color_counter.most_common(15):
    print(f"  #{col:06x}: {c}")

# --- per-page summary ---
print("\n=== RESUME PAR PAGE ===")
for pno in range(doc.page_count):
    page = doc[pno]
    text = page.get_text().strip()
    imgs = page.get_images(full=True)
    drawings = len(page.get_drawings())
    first = " ".join(text.split())[:90]
    print(f"p{pno+1:02d} | img:{len(imgs)} vec:{drawings} | {first}")

# --- extract embedded images ---
import os
out = 'input/images/newsletter'
os.makedirs(out, exist_ok=True)
seen = set()
n = 0
for pno in range(doc.page_count):
    for img in doc[pno].get_images(full=True):
        xref = img[0]
        if xref in seen:
            continue
        seen.add(xref)
        pix = pymupdf.Pixmap(doc, xref)
        if pix.n - pix.alpha > 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        fn = f"{out}/nl_p{pno+1:02d}_x{xref}.{pix.ext}"
        pix.save(fn)
        n += 1
print(f"\n{n} images extraites -> {out}")

# dump full text of a few key pages for structure reference
for pno in [0, 2, 5]:
    print(f"\n===== PAGE {pno+1} TEXT =====")
    print(doc[pno].get_text()[:1500])

json.dump({"fonts": dict(font_counter), "colors": {f"#{k:06x}": v for k, v in color_counter.items()},
           "sizes": {str(k): v for k, v in size_counter.items()}},
          open('data/processed/newsletter_style.json', 'w'), indent=2)
print("\nstyle -> data/processed/newsletter_style.json")
