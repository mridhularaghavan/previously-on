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

Static, no build step: `index.html` (inline CSS/JS) + `shows.json` + `jev/colour.json` + `jev/fans.json` + `covers/*.webp`. Deployed to Vercel from the repo root; the root `vercel.json` sets `outputDirectory: "site"` plus cache headers, so the dashboard's Root Directory must stay blank.

**The page is a scroll story with Jev at the front** (the owner felt the Jev experiment was getting buried under the 10x10 covers grid). A sticky top nav links the chapters and shows "N / 100 seen" plus the total Jev spend.
- **Hero**: "What colour is Breaking Bad?" (underlined in its Jev colours), a dek about the five-cent experiment, a "Why this exists" `<details>` with the owner's story (owner: **Mridhula**), and a **findings strip** computed from the data: most common colour, most certain, most torn, tightest fan pair, loneliest show. The cards link into the chapters (highlight the colour in the quilt, open a show, or `pinFan()` a node on the map).
- **Ch. 1, colour quilt**: 20x5 tiles on desktop, 10x10 at ≤1000px. Each tile is Jev's probabilities as bands, with edges that soften as confidence drops. Hover shows the cover. Also: a Breaking Bad callout, an order toggle (NYT rank / by colour), "Highlight a colour" swatches (these dim rather than filter, because the quilt is artwork), and a "How Jev answered" panel (question, palette, a real answer, cost).
- **Ch. 2, fan map**: a d3-force constellation, lazy-loaded (d3 from jsDelivr) when the section nears the viewport, with COMEDY/DRAMA continent labels from genre centroids. Hover/pin shows a show's circle. Plus a "How Jev answered" panel.
- **Ch. 3, your turn**: tap-to-mark-seen covers (20 per row), progress, the local-only note, "Up next, according to Jev" (after 3 seen), and the "Previously on… you" recap and finale states.
- **Ch. 4, archive**: a sticky toolbar under the nav (Covers/Timeline, search with a live count, sort, status filter, 🎲, genre chips ≥5). Covers carry a thin Jev-colour stripe; timeline bars use Jev's top colour. Filters **hide** non-matches, with an empty state + Clear.
- **One status per show**: `seen` | `watch` | `skip`, mutually exclusive, in `localStorage` `nyt100.status` (the old `nyt100.marks` is migrated). Changes are announced via `#sr`. Other keys: `nyt100.view` (archive view), `nyt100.milestones`, `nyt100.savedNotice`.
- **Detail dialog**: Jev's colour read and "fans also love" come *before* the TVmaze summary. There's no TVmaze link-out (attribution is in the footer). Prev/next follows the filtered archive order when the show is in it, and NYT rank order otherwise.
- **Design**: Cobalt + Clay on a **white base**, light only (no dark mode; no cream). Tokens: ink #171A1F, muted #5B5F66, rule #E2E4E8, chip #F1F2F4. **Cobalt #2447D8 = the only interactive colour.** Clay #B65E45 = editorial markers at ≥24px only; `--clay-ink` #8F432E for small text and fills. Status colours: seen #287255, watchlist #8A5B13, won't-watch #6B6359. Fonts: Bricolage Grotesque (`.disp`) for display only, Inter Tight for everything else. `.wrap` sets only `padding-inline`; `[hidden]` is forced to `display: none`.
- **Deliberately removed as low-value** (don't re-add without a reason): poster tilt/glare, pixel-colour sorts, corner status flags, "for you" badges beyond the top 10, genre chips under 5 shows, repeated storage notices, dark mode, the TVmaze link-out.
- Keys: `/` search (jumps to the archive), `←/→` browse in the dialog, `S` seen, `W` watchlist, `X` won't watch, `R` random.
- Local preview: `.claude/launch.json` → `python3 -m http.server 5173 --directory site`. The Browser pane can't screenshot while hidden. For visual checks use headless Chrome (`--headless=new --screenshot`); note it won't make windows narrower than ~500px, so check phone layouts with the pane's mobile emulation instead.

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
