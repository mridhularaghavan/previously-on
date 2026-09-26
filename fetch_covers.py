import csv, json, re, time, urllib.parse, urllib.request, pathlib

# Search-name overrides where the NYT title differs from TVmaze's
QUERY = {
    "The Office (U.S.)": "The Office", "The Office (U.K.)": "The Office",
    "True Detective (Season 1)": "True Detective", "Beef (Season 1)": "Beef",
    "Twin Peaks: The Return": "Twin Peaks", "The Bureau": "Le Bureau des Légendes",
    "Shogun": "Shōgun", "I Think You Should Leave": "I Think You Should Leave with Tim Robinson",
}
COUNTRY = {"The Office (U.S.)": "US", "The Office (U.K.)": "GB"}
# Pin exact TVmaze shows where search picks a spin-off
TVMAZE_ID = {"Battlestar Galactica": 166}
# Use a specific season's poster when the NYT ranks a single season
SEASON_ART = {"True Detective (Season 1)": 1, "Beef (Season 1)": 1}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "nyt-jev-art/1.0"})
    for _ in range(5):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(2); continue
            raise
    raise RuntimeError(url)

def country(s):
    n = s.get("network") or s.get("webChannel") or {}
    return ((n.get("country") or {}).get("code"))

out = []
for row in csv.DictReader(open("shows.csv")):
    t, start = row["title"], int(row["start"])
    q = QUERY.get(t, t)
    if t in TVMAZE_ID:
        res = [{"score": 99, "show": json.loads(get(f"https://api.tvmaze.com/shows/{TVMAZE_ID[t]}"))}]
    else:
        res = json.loads(get("https://api.tvmaze.com/search/shows?q=" + urllib.parse.quote(q)))
    def rank(r):
        s = r["show"]; yr = int((s.get("premiered") or "0")[:4] or 0)
        penalty = abs(yr - start) if yr else 50
        if t in COUNTRY and country(s) != COUNTRY[t]: penalty += 100
        if t == "Twin Peaks: The Return": penalty = abs(yr - 2017) if yr else 50
        if not s.get("image"): penalty += 20
        return penalty - r["score"]
    best = min(res, key=rank)["show"] if res else None
    rec = {**row, "tvmaze_id": None, "tvmaze_name": None, "premiered": None, "image": None, "file": None}
    if best:
        rec.update(tvmaze_id=best["id"], tvmaze_name=best["name"], premiered=best.get("premiered"),
                   genres=best.get("genres"), summary=re.sub("<[^>]+>", "", best.get("summary") or ""),
                   network=(best.get("network") or best.get("webChannel") or {}).get("name"))
        img = (best.get("image") or {}).get("original")
        if t in SEASON_ART:
            seasons = json.loads(get(f"https://api.tvmaze.com/shows/{best['id']}/seasons"))
            season = next((x for x in seasons if x["number"] == SEASON_ART[t]), None)
            img = ((season or {}).get("image") or {}).get("original") or img
        if img:
            fn = f"covers/{int(row['rank']):03d}.jpg"
            if not pathlib.Path(fn).exists():
                pathlib.Path(fn).write_bytes(get(img))
            rec.update(image=img, file=fn)
    out.append(rec)
    print(f"{row['rank']:>3} {t:40} -> {rec['tvmaze_name']} ({rec['premiered']}) {'IMG' if rec['file'] else 'NO IMG'}")
    time.sleep(0.3)
json.dump(out, open("shows.json", "w"), indent=1, ensure_ascii=False)
