# nyt-jev: *Previously On…*

The site is branded **Previously On…** and deployed at https://previously-on-tv.vercel.app (Vercel project `previously-on-tv`, auto-deploys from GitHub `mridhularaghavan/previously-on` on push to `main`).

Visual artwork built from The New York Times' **100 Best TV Shows of the 21st Century** (Sept 2026), with TypeSafe's **Jev** model supplying data for the next pieces.

Note: the list covers all TV (drama, comedy, reality, docs), not just sitcoms. About 44 of the shows are tagged Comedy.

## Source of truth

- `nyt-print-list.jpeg`: the NYT printable checklist. This is the canonical ranking; nytimes.com can't be fetched from here.
- `shows.csv`: rank, title, start and end years transcribed from that image. `end` is `present` for ongoing shows. Check any list change against the image.

## Pipeline

```
shows.csv ──fetch_covers.py──▶ shows.json + covers/NNN.jpg      (TVmaze API, no key)
                    ├──make_poster.py──▶ poster_covers.png (24×40in @300dpi) + poster_covers_preview.jpg
                    └──build_site_data.py──▶ site/shows.json + site/covers/NNN.webp
```

```bash
python3 fetch_covers.py      # skips covers already downloaded; delete covers/NNN.jpg to refetch one
python3 make_poster.py
python3 build_site_data.py
```

Needs Python 3.10+ and Pillow. Fonts come from macOS system fonts (New York, Helvetica Neue).

### TVmaze matching gotchas (handled in `fetch_covers.py`)
- `QUERY` maps NYT titles to TVmaze search names (e.g. *The Bureau* → *Le Bureau des Légendes*).
- `COUNTRY` separates *The Office* US vs UK.
- `TVMAZE_ID` pins exact shows where search returns a spin-off (*Battlestar Galactica* → 166, the 2003 series).
- `SEASON_ART` uses a season poster when the NYT ranks one season (*True Detective* S1, *Beef* S1).
- *Twin Peaks: The Return* shares TVmaze's single *Twin Peaks* entry, so its cover isn't 2017-specific.

When adding a fix, put it in these tables rather than patching `shows.json` by hand.

## Site (`site/`)

Static, no build step: `index.html` (inline CSS/JS) + `shows.json` + `covers/*.webp`. Deployed to Vercel from the repo root: the root `vercel.json` sets `outputDirectory: "site"` plus cache headers, so the dashboard's Root Directory must stay blank (repo root).

- Views: poster grid, timeline (2000–2026 bars), and **Jev colour** (the colour quilt: each tile is Jev's colour probabilities as horizontal bands; band edges soften as confidence drops; hover reveals the cover; swatches filter by Jev's top colour). Filters: genre chips, search, seen/want/unseen. Sorts: rank, year, cover colour (hue), lightness, A–Z. Includes a "Pick for me" random picker that prefers the want-list.
- "I've seen it" / "I want to see it" mirror the NYT print checkboxes. They're stored in `localStorage` under `nyt100.marks`; theme and view use `nyt100.theme` and `nyt100.view`.
- Keys: `/` search, `←/→` browse in the detail panel, `S` seen, `W` want, `R` random.
- Colours are CSS tokens on `:root` with dark-mode overrides. Each card's `--c` is the cover's average colour from `build_site_data.py`.
- Local preview: `.claude/launch.json` → `python3 -m http.server 5173 --directory site`.

Deploy: commit, then push `main` (the user pushes via GitHub Desktop). Vercel redeploys automatically.

## Rights

Cover art belongs to the studios and networks, served via TVmaze; the ranking belongs to the NYT. The footer credits both. Keep it a non-commercial fan piece, and don't sell prints.

## Jev (next phase)

Jev is TypeSafe AI's "System One" decision model. It takes text in and returns typed answers with probabilities and confidence, not generated text or images.
- Official docs: https://docs.typesafe.ai (index at `/llms.txt`). Console and API keys: https://console.typesafe.ai. Use these, not the third-party jevmodel.org.
- API: `POST https://api.typesafe.ai/v1/systemone`, Bearer auth. Python: `pip install typesafe-sdk`; `TypeSafeClient()` reads `TYPESAFE_API_KEY` and defaults to model `jev-latest`.
- Primitives: `Choice` (pick from options), `Score` (2–10 ordered levels → weighted score, probabilities, confidence), `Noul` (yes/no probability).
- Price: about $0.042 per million input tokens, with output free. The user has **$5 credit**.

Jev data flow: `jev_*.py` scripts call the API and cache each raw response in `jev_cache/<piece>/NNN.json` (committed; no secrets in them). Each script then exports a compact `site/jev/<piece>.json` that the site loads. The site never calls TypeSafe, and it hides Jev features if the JSON is missing.

- `jev_colour.py`: **done**. 100 calls, ~77.5K input tokens, about $0.003. Choice over 13 colours (`PALETTE` holds each colour's hex and the description Jev sees). Re-export without API calls: `python3 -c "import jev_colour; jev_colour.export()"`.

Planned pieces (the user chose 3, 4 and 5):
3. **Colour quilt**: a `Choice` over a fixed ~12-colour palette per show. Paint each tile by its probability mix. Estimated ~100 calls, under $0.01.
4. **Fan constellation**: a `Noul` "would a fan of A love B?" for all 4,950 pairs, drawn as a network with covers as nodes. Estimated ~2M tokens, about $0.08.
5. **Watch-next map**: rank unseen shows against the user's seen and loved list. Estimated under $0.01.

Rules for Jev work:
- Jev judges only the text it's given. Pass a short description per show (the TVmaze `summary` in `shows.json` is a start) rather than bare titles.
- Always dry-run 3 shows first and read `usage` from the response before a full run. Cache every response to disk (`jev_cache/`) so re-renders never re-spend credit.
- Never commit or print the API key.
