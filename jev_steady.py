"""Steadiness experiment: re-ask Jev the colour question with one input changed, then compare with the original.

    python3 jev_steady.py --run 0 --ranks 1 61 21    # dry run
    python3 jev_steady.py --run 0                     # all 100 (cached answers are reused)

Run 0 = repeat, nothing changed.
Run 2 = new show descriptions (jev_inputs/run2_summaries.json, links and marks removed); only the summary changes.
Run 3 = the 13 colours in a new order, darkest to lightest (by perceived lightness of the swatch).
Run 4 = new colour descriptions (written by Mridhula) and neutral names colour_a..colour_m, original order.
Answers are cached in jev_cache/colour_run<N>/NNN.json.
The original answers in jev_cache/colour/ are never touched.
"""
import argparse, json, pathlib

import jev_colour

jev_colour.MODEL = "jev-1.13.0"  # the version that made the original answers
ORIGINAL = pathlib.Path("jev_cache/colour")

DARK_TO_LIGHT = ["black", "midnight_blue", "royal_purple", "blood_red", "steel_grey", "leafy_green",
                 "neon_pink", "sickly_green", "sunny_orange", "sky_blue", "desert_gold", "beige", "pastel"]

# Run 4: neutral name -> (original colour, Mridhula's category name, new description Jev sees)
RUN4 = {
    "colour_a": ("desert_gold", "dusty_ochre", "Faded yellows, ochres and dusty browns: heat, dryness, harsh sun, exposed landscapes, weathered worlds"),
    "colour_b": ("blood_red", "crimson_heat", "Dense reds, burgundy and blood tones: danger, violence, desire, rage, dominance"),
    "colour_c": ("neon_pink", "electric_magenta", "Hot pinks, fuchsias and neon magentas: glamour, camp, nightlife, spectacle, performance"),
    "colour_d": ("sunny_orange", "amber_glow", "Oranges, amber and glowing warm tones: friendliness, exuberance, generosity, easy cheer"),
    "colour_e": ("leafy_green", "meadow_green", "Lush greens and leafy natural tones: growth, community, countryside, sport, everyday calm"),
    "colour_f": ("sickly_green", "toxic_lime", "Acid greens, yellow-greens and murky chartreuse: sickness, contamination, menace, paranoia, unease"),
    "colour_g": ("sky_blue", "clear_sky", "Bright blues, cyan and open-sky tones: freedom, innocence, optimism, freshness, lightness"),
    "colour_h": ("midnight_blue", "blue_hour", "Inky blues and cold dark tones: night, solitude, restraint, melancholy, emotional distance"),
    "colour_i": ("royal_purple", "violet_haze", "Purples, violets and dreamlike tones: fantasy, eccentricity, mysticism, decadence, altered reality"),
    "colour_j": ("beige", "domestic_neutral", "Beige, cream, taupe and muted domestic neutrals: routine, suburbs, offices, domestic life, mundanity"),
    "colour_k": ("steel_grey", "concrete_grey", "Greys, slate and metallic tones: institutions, industry, bureaucracy, rain, austerity"),
    "colour_l": ("black", "void_black", "Blacks and near-black shadows: secrecy, death, crime, dread, absence"),
    "colour_m": ("pastel", "powder_pastel", "Soft pinks, mint, lilac and washed tones: tenderness, nostalgia, youth, sweetness, gentle awkwardness"),
}


def to_original(run, answer):
    """Translate an answer's colour names back to the original names, so runs can be compared."""
    if run != 4:
        return answer
    name = lambda k: RUN4[k][0]
    return {**answer, "choice": name(answer["choice"]),
            "probabilities": {name(k): p for k, p in answer["probabilities"].items()}}


def setup(run):
    """Change exactly one input for this run."""
    if run == 3:
        jev_colour.PALETTE = {k: jev_colour.PALETTE[k] for k in DARK_TO_LIGHT}
    if run == 4:
        jev_colour.PALETTE = {k: (jev_colour.PALETTE[orig][0], desc) for k, (orig, _, desc) in RUN4.items()}


def moved(a, b):
    """Share of probability that moved between two answers: 0 = same, 1 = completely different."""
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0) - b.get(k, 0)) for k in keys) / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, required=True, choices=[0, 2, 3, 4])
    ap.add_argument("--ranks", type=int, nargs="*", help="only these NYT ranks")
    args = ap.parse_args()

    setup(args.run)
    print("colour order:", ", ".join(jev_colour.PALETTE))
    key = jev_colour.load_key()
    cache = pathlib.Path(f"jev_cache/colour_run{args.run}")
    cache.mkdir(parents=True, exist_ok=True)
    shows = json.load(open("shows.json"))
    if args.ranks:
        shows = [s for s in shows if int(s["rank"]) in args.ranks]
    if args.run == 2:
        new = json.load(open("jev_inputs/run2_summaries.json"))
        shows = [{**s, "summary": new[str(int(s["rank"]))]["summary"]} for s in shows]

    tokens_in = calls = 0
    for s in shows:
        path = cache / f"{int(s['rank']):03d}.json"
        if path.exists():
            res = json.load(open(path))
        else:
            res = jev_colour.ask(key, s)
            json.dump(res, open(path, "w"), indent=1)
            calls += 1
            tokens_in += res.get("usage", {}).get("input_tokens", 0)
        old = json.load(open(ORIGINAL / path.name))["answers"]["colour"]
        new = to_original(args.run, res["answers"]["colour"])
        print(f"\n{s['rank']:>3} {s['title']}  (model {res.get('model')})")
        print(f"    old: {old['choice']:14} conf {old['confidence']:.2f}")
        print(f"    new: {new['choice']:14} conf {new['confidence']:.2f}")
        for k in sorted(set(old["probabilities"]) | set(new["probabilities"]),
                        key=lambda k: -old["probabilities"].get(k, 0)):
            o, n = old["probabilities"].get(k, 0), new["probabilities"].get(k, 0)
            if o or n:
                print(f"      {k:14} {o:5.0%} -> {n:5.0%}")
        line = (f"    same top colour: {old['choice'] == new['choice']} | moved: "
                f"{moved(old['probabilities'], new['probabilities']):.0%}")
        repeat = pathlib.Path("jev_cache/colour_run0") / path.name
        if args.run != 0 and repeat.exists():
            r0 = json.load(open(repeat))["answers"]["colour"]["probabilities"]
            line += f" | wobble in run 0: {moved(old['probabilities'], r0):.0%}"
        print(line)

    print(f"\nnew calls: {calls} | input tokens: {tokens_in} | est. cost: ${tokens_in * 0.042 / 1e6:.6f}")


if __name__ == "__main__":
    main()
