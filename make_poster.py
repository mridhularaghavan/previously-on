import json
from PIL import Image, ImageDraw, ImageFont, ImageOps

shows = json.load(open("shows.json"))
F = "/System/Library/Fonts/"
serif = lambda s: ImageFont.truetype(F + "NewYork.ttf", s)
sans = lambda s, i=0: ImageFont.truetype(F + "HelveticaNeue.ttc", s, index=i)  # 1 = bold

TW, TH = 600, 900          # tile (2:3 poster)
GAP, LABEL = 40, 130
SIDE, TOP, BOTTOM = 360, 940, 320
W = SIDE * 2 + TW * 10 + GAP * 9
H = TOP + (TH + LABEL) * 10 + GAP * 9 + BOTTOM
INK, PAPER, MUTED = (18, 18, 18), (250, 248, 243), (110, 108, 104)

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)
d.text((SIDE, 400), "The 100 Best TV Shows of the 21st Century", font=serif(300), fill=INK, anchor="ls")
d.text((SIDE, 540), "As ranked by The New York Times, 2026  ·  Cover art via TVmaze", font=sans(80), fill=MUTED, anchor="ls")
d.line((SIDE, 690, W - SIDE, 690), fill=INK, width=6)

def fit(text, max_w, size, idx):
    while size > 20 and d.textlength(text, font=sans(size, idx)) > max_w:
        size -= 2
    return sans(size, idx)

for i, s in enumerate(shows):
    r, c = divmod(i, 10)
    x = SIDE + c * (TW + GAP)
    y = TOP + r * (TH + LABEL + GAP)
    cover = ImageOps.fit(Image.open(s["file"]).convert("RGB"), (TW, TH), Image.LANCZOS, centering=(0.5, 0.35))
    img.paste(cover, (x, y))
    # rank badge
    n = s["rank"]
    bw = 120 if len(n) < 3 else 150
    d.rectangle((x, y, x + bw, y + 90), fill=INK)
    d.text((x + bw / 2, y + 47), n, font=sans(62, 1), fill=PAPER, anchor="mm")
    title = s["title"]
    d.text((x, y + TH + 50), title, font=fit(title, TW, 46, 1), fill=INK, anchor="ls")
    end = s["end"] if s["end"] != s["start"] else ""
    years = s["start"] + (f"–{end}" if end else "")
    d.text((x, y + TH + 105), years, font=sans(38), fill=MUTED, anchor="ls")

d.line((SIDE, H - 220, W - SIDE, H - 220), fill=INK, width=4)
d.text((SIDE, H - 120), "nyt-jev", font=sans(60, 1), fill=MUTED, anchor="ls")
img.save("poster_covers.png", optimize=True)
img.resize((W // 4, H // 4), Image.LANCZOS).save("poster_covers_preview.jpg", quality=88)
print(W, H, f"{W/300:.1f} x {H/300:.1f} in @300dpi")
