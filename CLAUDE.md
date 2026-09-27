# nyt-jev: *Previously On…*

## Read this first: intent and scope (from the owner)

**The whole project in one sentence:** *I asked Jev to associate one of 13 colours with each of 100 TV shows. These are the results.* Everything should serve that sentence.

- **Owner:** Mridhula, a design-strong PM. This is one of three or four small weekend projects she's building for a portfolio by the end of 2026. It is deliberately **one idea, executed well**, not a product.

### Scope guardrail

Before adding anything, test it against one question: **Does this help someone understand or explore Jev's 100 colour choices?** If the answer is no, it doesn't belong on this page.

The one sanctioned extension is **"Build your TV palette"** (see Site): visitors mark shows they've watched and see Jev's existing colour choices for those shows combined. It passes the test because it's another way to explore the same 100 answers. It makes no new Jev calls, and it must **never** produce personality claims ("you prefer dark, intellectual TV"). The output is a colour composition, not a psychological profile.

AI assistants tend to keep growing an idea; don't. Don't propose new features, chapters, modes or extra Jev runs unless asked. When asked for improvements, prefer cutting and clarifying over adding.

### Tone

The tone should feel like **a confident designer showing an experiment, not a startup explaining a feature set.** Narration is short: what I did, what came out of it, and perhaps one small observation.

Write in the first person singular, because Mridhula made this:
- "I asked Jev…"
- "I gave it…"
- "I wanted to see…"
- "I made this over a weekend…"

Avoid:
- "We asked…" (or any "we"/"our")
- "What Jev found" or anything that frames this as research
- "Fans overlap" or any other claim about real audience behaviour (Jev's outputs are its judgments, not data about people)
- "Your turn" and other product-onboarding language
- "More to come"
- "The owner of this page"

The model is **Jev**, from TypeSafe AI (not "Jeff").

### History (why the site is small)

By 2026-09-27 the site had grown into a four-chapter product: a fan-map constellation (a second Jev run), recommendations, Seen/Watchlist/Won't-watch tracking, a recap, milestones, and an archive with timeline and search. The owner cut it back to the one sentence on 2026-09-27. Don't reintroduce any of those. The fan-map data and script are kept in the repo only as an archive (see Jev below); the fan map could become a separate portfolio project with its own premise.

## Current state

The site is branded **Previously On…** and deployed at https://previously-on-tv.vercel.app (Vercel project `previously-on-tv`, auto-deploys from GitHub `mridhularaghavan/previously-on` on push to `main`).

One page: Jev's colour choice for each of The New York Times' **100 Best TV Shows of the 21st Century** (Sept 2026), shown as a quilt, plus a personal palette builder.

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

Static, no build step: `index.html` (inline CSS/JS) + `shows.json` + `jev/colour.json` + `covers/*.webp` + `og.png`. Deployed to Vercel from the repo root; the root `vercel.json` sets `outputDirectory: "site"` plus cache headers, so the dashboard's Root Directory must stay blank. Pushing `main` redeploys.

**Page, top to bottom:**
1. **Brand line** ("Previously On…") and **headline**: "What colour is Breaking Bad?", with "Breaking Bad" underlined in its own Jev colour split.
2. **Dek, one sentence:** "I asked Jev, an AI model from TypeSafe, to pick one of 13 colours for each of The New York Times' 100 best TV shows of the century. Here are the results."
3. **Three finding cards** (computed), above the quilt: most common colour (highlights it in the quilt), most certain and most torn (open the show panel).
4. **The quilt:** 20x5 tiles on desktop, 10x10 at ≤1000px. Each tile is Jev's probabilities as horizontal bands, with edges that soften as confidence drops. Hover shows the cover; click opens the show panel. Controls: order (NYT rank / by colour / by confidence, most certain first) and a colour key that **highlights** (dims the other tiles) rather than filtering, because the quilt is artwork.
5. **One observation** below the quilt (computed): "Breaking Bad was a split decision: 55% desert gold, 41% sickly green."
6. **"What colour is your television taste?"** The palette builder: 100 small covers to tap. The state copy (the owner's, keep it verbatim):
   - 0 selected: "Mark at least three shows to reveal your palette."
   - 1 selected: "One selected. Choose two more…"
   - 2 selected: "Two selected. Choose one more to reveal your palette."
   - 3 or more: "Your palette is ready."

   The result is the average of Jev's probabilities across the selected shows, drawn as a big banded tile, a colour list with percentages, and the selected shows' own tiles. No new AI calls and no personality claims. There's a "Clear selection" button, and the selection is stored in `localStorage` `nyt100.watched`, seeded once from the old `nyt100.status` "seen" marks.
7. **"How I did it"** (`<details>`): the question, the 13 colours with the descriptions Jev saw, "the palette and descriptions are mine", and the cost (100 calls, ~78K tokens, ~$0.0033, i.e. about a third of a cent).
8. **Footer credits:** by Mridhula; ranking by the NYT; covers and summaries from TVmaze; colours by Jev (TypeSafe AI).

**Show panel** (dialog): the cover, "No. N of 100", title, years and network, Jev's colour bar with the top 3 colours, "Jev was {certain/fairly sure/undecided/torn} (confidence x.xx)", "What Jev read" (the TVmaze summary it was given), an "I've watched this" toggle (feeds the palette), and prev/next in the current quilt order (←/→ keys).

**Design:** Cobalt + Clay on a **white base**, light only (no dark mode, no cream). Tokens: ink #171A1F, muted #5B5F66, rule #E2E4E8, chip #F1F2F4. **Cobalt #2447D8 = the only interactive colour.** Clay #B65E45 = editorial markers at ≥24px only; `--clay-ink` #8F432E for small text. Seen/selected green #287255. Fonts: Bricolage Grotesque (`.disp`) for display only, Inter Tight for everything else. `.wrap` sets only `padding-inline`; `[hidden]` is forced to `display: none`. Every control is ≥44px on phones and coarse pointers.

**Link previews:** Open Graph + `twitter:card=summary_large_image` tags point to the absolute `https://previously-on-tv.vercel.app/og.png`. Regenerate the 1200x630 image with `python3 make_og.py` (headless Chrome renders the headline plus the real 20x5 quilt). If the domain changes, update `og:url`, `og:image`, `twitter:image` and `canonical`.

**Local preview:** `.claude/launch.json` → `python3 -m http.server 5173 --directory site`. The Browser pane can't screenshot while hidden. For visual checks use headless Chrome (`--headless=new --screenshot`); it won't make windows narrower than ~500px, so check phone layouts with the pane's mobile emulation.

## Rights

Cover art belongs to the studios and networks, served via TVmaze; the ranking belongs to the NYT. The footer credits both. Keep it a non-commercial fan piece, and don't sell prints.

## Jev

Jev is TypeSafe AI's "System One" decision model. It takes text in and returns typed answers with probabilities and confidence, not generated text or images.
- Official docs: https://docs.typesafe.ai (index at `/llms.txt`). Console and API keys: https://console.typesafe.ai. Use these, not the third-party jevmodel.org.
- API: `POST https://api.typesafe.ai/v1/systemone`, Bearer auth. Python: `pip install typesafe-sdk`; `TypeSafeClient()` reads `TYPESAFE_API_KEY` and defaults to model `jev-latest`.
- Primitives: `Choice` (pick from options), `Score` (2–10 ordered levels → weighted score, probabilities, confidence), `Noul` (yes/no probability).
- Price: about $0.042 per million input tokens, with output free. The user has **$5 credit**.

Jev data flow: `jev_*.py` scripts call the API and cache each raw response in `jev_cache/<piece>/NNN.json` (committed; no secrets in them). Each script then exports a compact `site/jev/<piece>.json` that the site loads. The site never calls TypeSafe.

- `jev_colour.py`: **done**. 100 calls, ~77.5K input tokens, about $0.003. Choice over 13 colours (`PALETTE` holds each colour's hex and the description Jev sees). Re-export without API calls: `python3 -c "import jev_colour; jev_colour.export()"`.

- `jev_constellation.py`: **archived, not used by the site.** Kept only for a possible separate project. One call per show A, with state = A's description and 99 `noul` questions ("would a devoted fan of this show also love B?"). That's 100 calls instead of 4,950 pairwise calls: ~1.17M input tokens, about $0.049. It has a `MAX_COST_USD` hard stop. `site/jev/fans.json` holds `rows[a]` = 100 ints (percent, self = -1), and it's **directed**: fan(A→B) ≠ fan(B→A). These are Jev's judgments from show descriptions, never audience data.

Total spent on Jev: about $0.052 of the $5 credit (the colours alone: about $0.0033).

Rules for Jev work:
- Jev judges only the text it's given. Pass a short description per show (the TVmaze `summary` in `shows.json` is a start) rather than bare titles.
- Don't run Jev again for this site without the owner asking (scope guardrail).
- Always dry-run 3 shows first and read `usage` from the response before a full run. Cache every response to disk (`jev_cache/`) so re-renders never re-spend credit.
- Never commit or print the API key.
