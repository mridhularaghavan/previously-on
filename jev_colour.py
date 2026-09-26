"""Idea #3 (colour quilt): ask Jev which colour best captures each show.

    python3 jev_colour.py --ranks 1 7 84     # dry run on a few shows
    python3 jev_colour.py                    # all 100 (cached answers are reused)

Answers are cached in jev_cache/colour/NNN.json so re-runs never re-spend credit.
"""
import argparse, json, os, pathlib, time, urllib.error, urllib.request

API = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
CACHE = pathlib.Path("jev_cache/colour")

# option -> (hex used when rendering, description Jev sees)
PALETTE = {
    "desert_gold":   ("#d9a441", "Sun-bleached yellows and ochres: heat, dust, deserts, harsh daylight"),
    "blood_red":     ("#9e1b24", "Deep reds: violence, danger, passion, power"),
    "neon_pink":     ("#e0457b", "Hot pinks and magentas: glamour, camp, nightlife, performance"),
    "sunny_orange":  ("#f08a3c", "Warm oranges: cheerful, sunny, upbeat, big-hearted"),
    "leafy_green":   ("#5b8c4a", "Natural greens: nature, small towns, sport fields, gentleness"),
    "sickly_green":  ("#7f8f3a", "Sickly greens: decay, menace, paranoia, the uncanny"),
    "sky_blue":      ("#7fb2d9", "Bright light blues: optimism, open skies, lightness, sweetness"),
    "midnight_blue": ("#1d2e4f", "Dark blues: night, melancholy, cold, loneliness"),
    "royal_purple":  ("#5d3a78", "Purples: royalty, the surreal, the mystical, the dreamlike"),
    "beige":         ("#cbb89d", "Beige and muted neutrals: offices, suburbs, the mundane everyday"),
    "steel_grey":    ("#77797c", "Greys: bureaucracy, rain, grit, bleak institutions"),
    "black":         ("#141414", "Blacks: darkness, crime, death, dread"),
    "pastel":        ("#e8c9d6", "Soft pastels: whimsy, nostalgia, awkward youth, tenderness"),
}


def load_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key and pathlib.Path(".env").exists():
        for line in open(".env"):
            name, _, val = line.strip().partition("=")
            if name == "TYPESAFE_API_KEY":
                key = val
    if not key:
        raise SystemExit("TYPESAFE_API_KEY not found in env or .env")
    return key


def ask(key, show):
    body = {
        "model": MODEL,
        "state": {
            "show": show["title"],
            "years": f"{show['start']}-{show['end']}",
            "network": show.get("network"),
            "genres": show.get("genres"),
            "summary": show.get("summary"),
        },
        "questions": {
            "colour": {
                "type": "choice",
                "instructions": "Which colour best captures this TV show's mood, tone and visual world?",
                "criteria": {k: d for k, (_, d) in PALETTE.items()},
            }
        },
    }
    req = urllib.request.Request(API, json.dumps(body).encode(), {
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ranks", type=int, nargs="*", help="only these NYT ranks")
    args = ap.parse_args()

    key = load_key()
    CACHE.mkdir(parents=True, exist_ok=True)
    shows = json.load(open("shows.json"))
    if args.ranks:
        shows = [s for s in shows if int(s["rank"]) in args.ranks]

    tokens_in = tokens_out = calls = 0
    for s in shows:
        path = CACHE / f"{int(s['rank']):03d}.json"
        if path.exists():
            res = json.load(open(path))
        else:
            res = ask(key, s)
            json.dump(res, open(path, "w"), indent=1)
            calls += 1
            tokens_in += res.get("usage", {}).get("input_tokens", 0)
            tokens_out += res.get("usage", {}).get("output_tokens", 0)
        a = res["answers"]["colour"]
        top = sorted(a["probabilities"].items(), key=lambda kv: -kv[1])[:3]
        mix = ", ".join(f"{k} {p:.0%}" for k, p in top)
        print(f"{s['rank']:>3} {s['title'][:32]:32} conf {a['confidence']:.2f} | {mix}")

    print(f"\nnew calls: {calls} | input tokens: {tokens_in} | output tokens: {tokens_out}"
          f" | est. cost: ${tokens_in * 0.042 / 1e6:.6f}  (at $0.042/M input, output free)")
    export()


def export():
    """Write site/jev/colour.json from every cached answer (no API calls)."""
    shows, total_in = {}, 0
    for path in sorted(CACHE.glob("*.json")):
        res = json.load(open(path))
        a = res["answers"]["colour"]
        total_in += res.get("usage", {}).get("input_tokens", 0)
        probs = {k: round(p, 3) for k, p in sorted(a["probabilities"].items(), key=lambda kv: -kv[1]) if p >= 0.01}
        shows[int(path.stem)] = {"choice": a["choice"], "confidence": round(a["confidence"], 3), "probs": probs}
    palette = {k: {"hex": h, "label": k.replace("_", " ").capitalize(), "desc": d} for k, (h, d) in PALETTE.items()}
    out = pathlib.Path("site/jev/colour.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"model": MODEL, "calls": len(shows), "input_tokens": total_in,
               "cost_usd": round(total_in * 0.042 / 1e6, 4), "palette": palette, "shows": shows},
              open(out, "w"), ensure_ascii=False)
    print(f"exported {len(shows)} answers -> {out}")


if __name__ == "__main__":
    main()
