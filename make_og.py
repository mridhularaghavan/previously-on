"""Render the link-preview image (site/og.png, 1200x630) from Jev's colour data.

Builds a one-off HTML card (headline + the 20x5 colour quilt) and screenshots it
with headless Chrome, so the preview uses the site's real fonts and colours.

    python3 make_og.py
"""
import json, pathlib, subprocess, tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
jev = json.load(open("site/jev/colour.json"))
P, S = jev["palette"], jev["shows"]
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
cost_cents = round((jev["cost_usd"] + json.load(open("site/jev/fans.json"))["cost_usd"]) * 100)


def quilt(n):
    """Same banding as the site: bands sized by probability, softer edges when Jev was unsure."""
    j = S[str(n)]
    parts = [(k, p) for k, p in j["probs"].items() if p >= 0.02]
    tot, soft, at, stops = sum(p for _, p in parts), (1 - j["confidence"]) * 14, 0, []
    for i, (k, p) in enumerate(parts):
        a, b = at, at + p / tot * 100
        at = b
        lo = a + soft / 2 if i else 0
        hi = b - soft / 2 if i < len(parts) - 1 else 100
        stops.append(f"{P[k]['hex']} {lo:.1f}% {max(lo, hi):.1f}%")
    return f"linear-gradient(to bottom, {', '.join(stops)})" if len(stops) > 1 else P[parts[0][0]]["hex"]


bb = [P[k]["hex"] for k, _ in sorted(S["1"]["probs"].items(), key=lambda kv: -kv[1])[:2]]
tiles = "".join(f'<i style="background:{quilt(n)}"></i>' for n in range(1, 101))
html = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&family=Inter+Tight:wght@500;600&display=block" rel="stylesheet">
<style>
* {{ margin: 0; box-sizing: border-box; }}
body {{ width: 1200px; height: 630px; background: #fff; color: #171A1F; font-family: "Inter Tight", sans-serif; position: relative; overflow: hidden; }}
.top {{ padding: 52px 60px 0; }}
.row {{ display: flex; justify-content: space-between; align-items: center; }}
.kicker {{ font-size: 17px; letter-spacing: .16em; text-transform: uppercase; color: #5B5F66; font-weight: 600; }}
.brand {{ display: flex; align-items: center; gap: 10px; font: 600 22px "Bricolage Grotesque"; font-stretch: 88%; }}
.brand::before {{ content: ""; width: 10px; height: 10px; border-radius: 50%; background: #B65E45; box-shadow: 0 0 0 4px #B65E4540; }}
h1 {{ font: 700 92px/0.95 "Bricolage Grotesque"; letter-spacing: -.045em; margin-top: 26px; }}
.bb {{ background-image: linear-gradient(90deg, {bb[0]} 0 55%, {bb[1]} 55% 100%); background-size: 100% .11em; background-repeat: no-repeat; background-position: 0 92%; }}
.dek {{ font-size: 25px; color: #5B5F66; margin-top: 22px; }}
.dek b {{ color: #171A1F; font-weight: 600; }}
.quilt {{ position: absolute; left: 0; right: 0; bottom: 0; height: 170px; display: grid; grid-template-columns: repeat(20, 1fr); }}
.quilt i {{ display: block; }}
</style></head><body>
<div class="top">
  <div class="row"><span class="kicker">A {WORDS.get(cost_cents, cost_cents)}-cent experiment</span><span class="brand">Previously On…</span></div>
  <h1>What colour is<br><span class="bb">Breaking Bad</span>?</h1>
  <p class="dek">An AI colour-coded <b>the 100 best TV shows of the century</b>.</p>
</div>
<div class="quilt">{tiles}</div>
</body></html>"""

with tempfile.TemporaryDirectory() as tmp:
    card = pathlib.Path(tmp, "og.html")
    card.write_text(html)
    out = pathlib.Path("site/og.png").resolve()
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--window-size=1200,630", "--virtual-time-budget=5000", f"--screenshot={out}", card.as_uri()],
                   check=True, capture_output=True)
print("wrote", out)
