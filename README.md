# Lookahead

A self-updating gaming almanac: a five-week lookahead across tracked games (currently World of Warcraft Retail, Pokemon GO, and Pokopia), rendered as a dark, editorial web page and served by GitHub Pages.

Each week an agent researches what's coming up (per [INSTRUCTIONS.md](INSTRUCTIONS.md)), rewrites `data.json`, regenerates the page, and commits. Between rebuilds the page keeps itself current in the browser: countdowns tick, events flip to "active" when they start and grey out when they end. A sticky tab rail filters the feed to a single game (state lives in the URL hash, so filtered views are linkable); "Needs you" stays visible in every view.

## Repo layout

```
README.md            this file
INSTRUCTIONS.md      the weekly research + build spec (authoritative)
data.json            current dataset, rewritten each week
requirements.txt     Pillow (image downscaling)
tools/
  generate.py        data.json -> docs/index.html + docs/assets/*
  template.html      HTML skeleton with placeholders
  style.css          the "Ephemeris" design system (dark only)
  app.js             live countdowns, live state, scroll reveal
  build_fonts.py     one-time webfont fetch into docs/assets/fonts/
docs/                GitHub Pages root (main branch, /docs)
  index.html         GENERATED, never hand-edit
  .nojekyll          disables Jekyll processing
  CNAME              custom domain (see below)
  assets/            css, js, fonts, event images
```

## Build locally

```sh
pip install -r requirements.txt
python3 tools/generate.py
```

Then open `docs/index.html`. With [uv](https://docs.astral.sh/uv/), `uv run tools/generate.py` works with no setup (the script declares its own dependency).

Fonts are committed; re-run `python3 tools/build_fonts.py` only if `docs/assets/fonts/` is ever missing.

`docs/index.html` is generated output. To change the page, edit `data.json` or the files in `tools/` and re-run the generator.

## How the weekly update works

A separate scheduled agent (wired up outside this repo) follows `INSTRUCTIONS.md`: it researches the next five weeks from official sources and event trackers, writes a fresh `data.json`, runs `tools/generate.py`, and commits `data.json`, `docs/index.html`, and any new images. The client-side script (`tools/app.js`) keeps the published page accurate between runs using the viewer's clock.

## Adding or removing a tracked game

1. Edit the Tracked items and Sources sections of `INSTRUCTIONS.md`.
2. If it's a new game, add its accent color and calendar link to `GAME_META` in `tools/generate.py` (and a tag in `GAME_TAGS` if it should show a static pill).
3. The next weekly run picks it up; game sections render in the order they appear in `data.json`, and the game's filter tab (in its accent color) is generated automatically.

## GitHub Pages setup (one-time, manual)

1. Push this repo to GitHub.
2. In the repo: Settings, Pages, Build and deployment, Source: "Deploy from a branch", Branch: `main`, Folder: `/docs`. Save.
3. Custom domain (optional): replace the placeholder in `docs/CNAME` with your real domain and set the same domain in the Pages settings. If you'll use the default `<user>.github.io/lookahead` URL instead, delete `docs/CNAME`.

## data.json schema

```jsonc
{
  "run_date": "YYYY-MM-DD",
  "window_start": "YYYY-MM-DD",           // = run_date
  "window_end": "YYYY-MM-DD",             // run_date + 35 days
  "window_display": "Jul 24 - Aug 28, 2026",
  "last_updated_display": "Fri, Jul 24, 2026",
  "changelog": null,                       // or {"since":"Jul 17","lines":[{"verb":"+|→|−","text":"..."}]}
  "needs_you": [
    {"date":"YYYY-MM-DD","date_display":"Aug 1","game":"WoW|Pokemon GO|Pokopia",
     "action":"one action clause","urgent":false,"estimate":false,"link":"https://..."}
  ],
  "categories": [
    {"name":"Gaming","games":[ /* game objects; order: WoW (Retail), Pokemon GO, Pokopia */ ]}
  ]
}
```

Each game object:

```jsonc
{
  "game": "WoW (Retail)" | "Pokemon GO" | "Pokopia",
  "typical_lead_time": "string, used in the empty-state note",
  "current_version": "1.1.1",              // Pokopia only; shown as the tag pill
  "timeline": [
    {"state":"active|upcoming","start":"YYYY-MM-DD|null","end":"YYYY-MM-DD|null",
     "date_display":"Through Aug 11 | Aug 4-11 | August 2026",
     "title":"short name","detail":"one short actionable sentence",
     "paid":false,"price":"$4.99|null","estimate":false,"estimate_basis":"...|null",
     "link":"https://... primary source",
     "image_url":"https://... exact og:image or null","image_reliable":true}
  ],
  "weekly_rhythm": ["dense one-liners; no images"],
  "just_past_window": ["one line each"]
}
```

`start`/`end` drive the live dots and countdowns; emit both whenever known.
