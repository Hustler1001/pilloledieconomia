"""Crea una scheda grafica 1200x675 per X: titolo, numero grande, riga di dettaglio, fonte.
Uso: python3 make_card.py out.png "Titolo" "Numero grande" "Dettaglio" "Fonte"
Il titolo puo' andare su due righe con \\n."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
F7 = os.path.join(HERE, "fonts", "fredoka-latin-700-normal.woff")
F5 = os.path.join(HERE, "fonts", "fredoka-latin-500-normal.woff")
W, H = 1200, 675
NAVY, NAVY2, YEL, WHITE, GREY = (14, 22, 48), (28, 44, 92), (255, 204, 51), (255, 255, 255), (170, 182, 210)

def fit(draw, text, path, size, maxw):
    while size > 20:
        f = ImageFont.truetype(path, size)
        if draw.textlength(text, font=f) <= maxw:
            return f
        size -= 2
    return ImageFont.truetype(path, 20)

def card(out, title, big, detail, source):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):                                   # sfumatura verticale
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * t) for i in range(3)))
    d.rounded_rectangle([60, 48, 330, 98], 25, fill=YEL)
    d.text((195, 73), "Pillole di Economia", font=ImageFont.truetype(F7, 26), fill=NAVY, anchor="mm")
    title = title.replace("\\n", "\n")
    y = 150
    for line in title.split("\n"):
        d.text((60, y), line, font=fit(d, line, F7, 54, W - 120), fill=WHITE)
        y += 66
    d.text((60, 300), big, font=fit(d, big, F7, 150, W - 120), fill=YEL)
    d.text((60, 480), detail, font=fit(d, detail, F5, 46, W - 120), fill=WHITE)
    d.line([(60, 585), (W - 60, 585)], fill=(70, 88, 140), width=2)
    d.text((60, 600), source, font=fit(d, source, F5, 26, W - 120), fill=GREY)
    d.text((60, 636), "Informazione generale, non consulenza finanziaria", font=ImageFont.truetype(F5, 22), fill=(120, 136, 180))
    img.save(out, optimize=True)

if __name__ == "__main__":
    card(*sys.argv[1:6])
