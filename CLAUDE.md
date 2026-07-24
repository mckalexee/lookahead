# Lookahead

Five-week gaming almanac, published at https://look.mckenzie.app via GitHub Pages, which serves `docs/` on `main`. Committing to `docs/` IS deploying.

## Generated files: never hand-edit

`docs/index.html`, `docs/assets/style.css`, `docs/assets/app.js`, and `docs/assets/fonts.css` are build output. Edit the sources in `tools/` (or `data.json`) and rebuild:

```sh
python3 tools/generate.py     # needs Pillow: pip install -r requirements.txt
# or, zero-setup: uv run tools/generate.py
```

Always commit the regenerated `docs/` files in the same commit as a `tools/` change, or the live site falls behind the source. Fonts in `docs/assets/fonts/` are committed; run `tools/build_fonts.py` only if they are missing.

## Who changes what

- `INSTRUCTIONS.md` is the authoritative spec for the weekly data update (window, tracked items, sources, style rules, schema). Change tracked games or research rules there.
- `data.json` is rewritten every Monday by a cloud routine ("Lookahead weekly update") that commits straight to `main`. Pull before starting work, and don't be surprised by its commits. The routine has no browser; JS-heavy sources (wowhead.com, pokemon.com, pokopia.pokemon.com) are fetched via the Markdown Proxy MCP server (`fetch_page`) - same applies to research done from this repo locally.
- Adding a game: edit `INSTRUCTIONS.md` (tracked items + sources) and add accent/display/calendar to `GAME_META` in `tools/generate.py`. Sections and filter tabs render automatically from `data.json`.

## Hard style rules (enforced in content, not just preferred)

- No em-dashes or en-dashes anywhere in page content; hyphens/commas/colons only. `generate.py` normalizes as a safety net, but don't rely on it.
- US dates ("Aug 4-11", "Through Aug 11"). "local" time only when the publisher defines the event per player timezone (e.g. Pokemon GO); otherwise name the source's timezone.
- Dark theme only ("Ephemeris" design system in `tools/style.css`): single gold accent, per-game accent colors only on section headers/spines/tabs, mono for all data/labels. Don't add a light theme.
- Never guess dates or construct image URLs; unverified items are estimates with an `estimate_basis`.

## Verifying changes

Serve locally (`python3 -m http.server` in `docs/`) rather than file:// if you need the filter tabs' hash routing to behave like production. `tools/app.js` recomputes countdowns and active/upcoming/ended states from the viewer's clock, so a stale build can still look "correct" - check `data-start`/`data-end` attributes against `data.json` when validating.
