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

- Views: poster grid, timeline (2000–2026 bars), and **Jev colour** (the colour quilt: each tile is Jev's colour probabilities as horizontal bands; band edges soften as confidence drops; hover reveals the cover; swatches filter by Jev's top colour), and **Jev fans** (the constellation: a d3-force network, with d3 lazy-loaded from jsDelivr when the view first opens; edges are each show's top 3 symmetric fan links plus every link ≥78; hover shows the circle and tooltip, click opens the detail panel). The detail panel also lists "fans also love" (top 5 directed). Filters: genre chips, search, seen/want/unseen. Sorts: rank, year, cover colour (hue), lightness, A–Z. Includes a "Pick for me" random picker that prefers the want-list.
- **One status per show**: `seen` | `watch` (Watchlist) | `skip` (Won't watch), mutually exclusive. Clicking the active state clears it. Status lives in `localStorage` under `nyt100.status` (`{rank: status}`). The old `nyt100.marks` `{s, w}` data is migrated on load, with seen winning. Changes are announced through the `#sr` live region ("X moved from Watchlist to Seen"). Seen and skipped shows are excluded from For you.
- Other keys: `nyt100.visited` (return visits get the compact masthead), `nyt100.view`, `nyt100.milestones` (already-celebrated seen counts), `nyt100.savedNotice` (the one-time "saved in this browser only" toast).
- **Filtering is real filtering**: search, genre chips, the status select and Jev colour swatches hide non-matches (`.hide`) the same way in the Poster, Colour and Timeline views. The bar shows a live count ("1 show"), and there's an empty state with Clear search / Clear filters. The constellation is the one exception: it keeps its layout and dims instead ("N lit").
- **Masthead**: the full editorial hero with a "Start exploring" jump appears on the first visit only. After that it's a compact masthead ("About this project" expands it). The sticky bar holds views, search, sort, status filter, "N / 100 seen" and Pick for me. A mini wordmark appears in the bar once the hero scrolls away, and `--barh` is kept in sync for the sticky timeline axis.
- **Progression**: "You've seen N of 100". Milestone toasts fire at 10/25/50/75/100 seen, each once. The "Previously on… you" recap covers decade, genre, network, and the colour of your taste (from Jev's colours). Endings: "Series finale" (all 100 seen) and "Archive complete" (all 100 marked).
- **Design**: the Television Archive palette, light only (dark mode removed on purpose). Tokens are on `:root`: canvas #F4EFE3, panel #FFF9EE, ink #1E1A16, muted #6B6359, rule #D7C9B6, control #E9DECD, oxblood accent #8C3B2A, seen #287255, watchlist amber #8A5B13 (amber means Watchlist only). Fonts: Fraunces (`.disp`, plus `.soft` for brand and milestones; WONK stays 0) for display moments only, and Inter Tight for everything else. The constellation keeps its dark "sky" panel as artwork.
- Keys: `/` search, `←/→` browse in the dialog, `S` seen, `W` watchlist, `X` won't watch, `R` random.
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

- `jev_constellation.py`: **done**. One call per show A, with state = A's description and 99 `noul` questions ("would a devoted fan of this show also love B?"). That's 100 calls instead of 4,950 pairwise calls: ~1.17M input tokens, about $0.049. It has a `MAX_COST_USD` hard stop. `site/jev/fans.json` holds `rows[a]` = 100 ints (percent, self = -1), and it's **directed**: fan(A→B) ≠ fan(B→A). The site's `link()` averages both directions.

Running total spent on Jev: about $0.052 of the $5 credit.

Planned pieces (the user chose 3, 4 and 5):
3. **Colour quilt**: a `Choice` over a fixed ~12-colour palette per show. Paint each tile by its probability mix. Estimated ~100 calls, under $0.01.
4. **Fan constellation**: a `Noul` "would a fan of A love B?" for all 4,950 pairs, drawn as a network with covers as nodes. Estimated ~2M tokens, about $0.08.
5. **For you**: **done**. It needs no Jev calls, since it's computed in the browser from `fans.json` once the visitor has ticked ≥3 seen shows (`MIN_SEEN`). For each unseen show B: score = 0.6 × mean of the top-3 fan(seen → B) + 0.4 × mean over all seen shows. "Because you've seen…" names the top 2 contributors. It appears in four places:
   - the "Up next, according to Jev" row in the header (below 3 seen shows it shows a CTA instead)
   - "NN% for you" card badges, with the top 10 in accent colour
   - the "Jev · for you" sort
   - a "why" note in the dialog

   Other effects: "Pick for me" picks at random from the top 6 (want-list +6), and constellation nodes get `.pick` (top 5 glow) and `.seen` (dimmed).

Rules for Jev work:
- Jev judges only the text it's given. Pass a short description per show (the TVmaze `summary` in `shows.json` is a start) rather than bare titles.
- Always dry-run 3 shows first and read `usage` from the response before a full run. Cache every response to disk (`jev_cache/`) so re-renders never re-spend credit.
- Never commit or print the API key.
