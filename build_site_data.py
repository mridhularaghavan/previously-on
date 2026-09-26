"""Build site/shows.json and site/covers/*.webp from shows.json + covers/."""
import json, pathlib
from PIL import Image, ImageOps

shows = json.load(open("shows.json"))
pathlib.Path("site/covers").mkdir(parents=True, exist_ok=True)
out = []
for s in shows:
    n = int(s["rank"])
    im = ImageOps.fit(Image.open(s["file"]).convert("RGB"), (480, 720), Image.LANCZOS, centering=(0.5, 0.35))
    im.save(f"site/covers/{n:03d}.webp", quality=80)
    c = im.resize((1, 1), Image.LANCZOS).getpixel((0, 0))  # average colour: glow + colour sort
    out.append({
        "rank": n, "title": s["title"], "start": int(s["start"]),
        "end": None if s["end"] == "present" else int(s["end"]),
        "network": s.get("network"), "genres": s.get("genres") or [],
        "summary": s.get("summary", "").strip(), "tvmaze": s.get("tvmaze_id"),
        "color": "#%02x%02x%02x" % c, "cover": f"covers/{n:03d}.webp",
    })
json.dump(out, open("site/shows.json", "w"), ensure_ascii=False)
print(len(out), "shows written")
