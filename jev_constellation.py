"""Idea #4 (fan constellation): would a fan of show A love show B?

One call per show A: the state describes A, and there is one noul question per
other show B. The result is a directed 100x100 matrix of P(fan of A loves B).

    python3 jev_constellation.py --ranks 1        # dry run on one show
    python3 jev_constellation.py                  # all 100 (cached answers are reused)

Raw answers are cached in jev_cache/fans/NNN.json; export() writes site/jev/fans.json.
"""
import argparse, json, pathlib, re
from concurrent.futures import ThreadPoolExecutor, as_completed

from jev_colour import load_key, API, MODEL
import time, urllib.error, urllib.request

CACHE = pathlib.Path("jev_cache/fans")
MAX_COST_USD = 0.50  # hard stop for this script


def first_sentence(text, limit=160):
    s = re.split(r"(?<=[.!?])\s", (text or "").strip())[0]
    return s if len(s) <= limit else s[:limit].rsplit(" ", 1)[0] + "…"


def describe(s):
    end = "present" if s["end"] == "present" else s["end"]
    return f"{s['title']} ({s['start']}-{end}, {s.get('network')}; {', '.join(s.get('genres') or [])}): {first_sentence(s.get('summary'))}"


def post(key, body):
    req = urllib.request.Request(API, json.dumps(body).encode(), {
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:500]}")


def ask(key, a, others):
    questions = {
        f"r{int(b['rank']):03d}": {
            "type": "noul",
            "instructions": f"Would a devoted fan of this show also love: {describe(b)}",
            "criteria": {
                "true": "Yes: the same fans would very likely love it too (shared tone, humour, themes or craft)",
                "false": "No: it would not especially appeal to this show's fans",
            },
        }
        for b in others
    }
    body = {
        "model": MODEL,
        "state": {"show_the_fan_loves": describe(a), "full_summary": a.get("summary")},
        "questions": questions,
    }
    return post(key, body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ranks", type=int, nargs="*")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    key = load_key()
    CACHE.mkdir(parents=True, exist_ok=True)
    shows = json.load(open("shows.json"))
    todo = [s for s in shows if not args.ranks or int(s["rank"]) in args.ranks]
    todo = [s for s in todo if not (CACHE / f"{int(s['rank']):03d}.json").exists()]
    print(f"{len(todo)} shows to ask ({len(list(CACHE.glob('*.json')))} already cached)")

    spent = 0
    with ThreadPoolExecutor(args.workers) as pool:
        futs = {pool.submit(ask, key, a, [b for b in shows if b["rank"] != a["rank"]]): a for a in todo}
        for f in as_completed(futs):
            a, res = futs[f], f.result()
            json.dump(res, open(CACHE / f"{int(a['rank']):03d}.json", "w"))
            tin = res.get("usage", {}).get("input_tokens", 0)
            spent += tin * 0.042 / 1e6
            top = sorted(((k, v["noul"]) for k, v in res["answers"].items()), key=lambda kv: -kv[1])[:4]
            names = ", ".join(f"{shows[int(k[1:]) - 1]['title']} {p:.2f}" for k, p in top)
            print(f"{a['rank']:>3} {a['title'][:28]:28} {tin:>6} tok | {names}", flush=True)
            if spent > MAX_COST_USD:
                pool.shutdown(cancel_futures=True)
                raise SystemExit(f"cost cap ${MAX_COST_USD} reached; stopping")
    print(f"\nthis run: ~${spent:.4f}")
    export()


def export():
    """Write site/jev/fans.json: directed matrix m[a][b] = P(fan of a loves b), in percent."""
    m, total_in = {}, 0
    for path in sorted(CACHE.glob("*.json")):
        res = json.load(open(path))
        total_in += res.get("usage", {}).get("input_tokens", 0)
        m[int(path.stem)] = {int(k[1:]): round(v["noul"] * 100) for k, v in res["answers"].items()}
    out = pathlib.Path("site/jev/fans.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    # compact: row per show, 100 ints (self = -1), rank order
    rows = {a: [(-1 if b == a else row.get(b, 0)) for b in range(1, 101)] for a, row in m.items()}
    json.dump({"model": MODEL, "calls": len(m), "input_tokens": total_in,
               "cost_usd": round(total_in * 0.042 / 1e6, 4), "rows": rows},
              open(out, "w"), separators=(",", ":"))
    print(f"exported {len(m)} rows -> {out}")


if __name__ == "__main__":
    main()
