"""Extract embedded images from the reference newsletter PDF."""
import glob
import os
import pymupdf

path = glob.glob('input/reference/AU*NEWSLETTER*.pdf')[0]
doc = pymupdf.open(path)
out = 'input/images/newsletter'
os.makedirs(out, exist_ok=True)

seen = set()
n = 0
info = []
for pno in range(doc.page_count):
    for img in doc[pno].get_images(full=True):
        xref = img[0]
        if xref in seen:
            continue
        seen.add(xref)
        try:
            pix = pymupdf.Pixmap(doc, xref)
            if pix.n - pix.alpha > 3:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            fn = f"{out}/nl_p{pno+1:02d}_x{xref}.png"
            pix.save(fn)
            info.append((fn, pix.width, pix.height, pix.alpha))
            n += 1
        except Exception as e:
            print('skip xref', xref, e)

print(f"{n} images -> {out}")
for fn, w, h, a in sorted(info, key=lambda t: -t[1] * t[2])[:15]:
    print(f"  {w}x{h} a={a}  {os.path.basename(fn)}")
