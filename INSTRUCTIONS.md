# Lookahead: weekly research and build spec

This file is the authoritative guide for the weekly update. Follow it exactly. To add or remove a tracked game, edit the Tracked items and Sources sections here; the generator renders whatever games appear in `data.json`.

## Goal and window

- Run date: today. Window: today through today + 35 days (5 weeks).
- Include anything active now or starting on or before the window end. Exclude anything already ended.
- Also collect a short "just past the window" list: already-announced items landing in the 14 days after the window end, one line each.
- US region only. US dates.

## Tracked items

### WoW (Retail)
- In-game holidays and events, including micro-holidays.
- The weekly bonus event and PvP Brawl rotation, week by week.
- Timewalking events.
- Trading Post: notable items, monthly rollover, and claim or freeze deadlines.
- Twitch drops with claim deadlines.
- Notable limited-time shop items.
- Patches and content updates in the window: key items only (new zones, raids, major systems, big events). No routine hotfix or class-tuning lists.
- Season timing: last-chance-for-Season-N warnings. Label estimate vs confirmed clearly.

### Pokemon GO
- 5-star and Shadow raid rotations with dates and Raid Hour times.
- The weekly rhythm: Spotlight Hours with the bonus (note the season's day of week), Max Monday, GO Battle League rotation.
- Limited-time events with start and end.
- Community Days: date, time, featured Pokemon, evolve-for-move deadline.
- Paid tickets and Special or Masterwork Research, with prices.
- GO Pass details: free vs Deluxe, price, rank rewards, every claim-by deadline.
- Debuts and Shiny availability where officially stated.
- Skip region-locked non-US events; one line if major.

### Pokopia
- Events running now or officially confirmed.
- Active Mystery Gift distributions and codes: expiry date and region.
- Current game version (shown as the section tag pill).
- DLC and expansion roadmap items: price, on-sale status, early-purchase bonus deadlines.
- Confirmed and official only. No past, rumored, or datamined items.

### Aniimo
- Pre-launch (launch window Q3 2026): beta and test windows with start, end, and data-wipe notes; carry-forward events tied to a test (for example egg-sealing keepsakes) with their deadlines.
- Launch timing: track the announced window as an estimate until Pawprint publishes a date, then as confirmed.
- Pre-registration milestone rewards and any pre-order or early-purchase bonuses with deadlines.
- Once launched: version updates, limited-time events, paid passes and pricing, claim deadlines.
- Dates from official Pawprint or FunPlus posts only. Creator-program news only when it has a player-facing deadline.

## Sources

Research fresh every run. Verify dates; never guess. Prefer official sources; reputable trackers are OK; skip SEO and speculation sites unless corroborated.

Some sources are JS-heavy or block plain fetches (wowhead.com, pokemon.com, pokopia.pokemon.com). Fetch those through the Markdown Proxy MCP server (claude.ai Markdown Proxy), which renders a URL and returns its content as markdown. There is no browser in the update environment; do not assume one.

- WoW: wowhead.com/events (JS-heavy, use the proxy), cross-check darmory.com/events/calendar (plain HTML, US dates), news.blizzard.com/en-us/world-of-warcraft, Wowhead Blue Tracker.
- Pokemon GO: pokemongo.com/en/news is the priority source; when an item has an official news post, take dates, times, prices, and fine print from it. It requires no sign-in; if a fetch looks like a login wall or empty shell, retry through the Markdown Proxy (`fresh: true`) instead of skipping the source. Fall back to leekduck.com/events when an item has no official post yet (it is also the fastest way to enumerate the whole window), and cross-check Pokemon GO Hub's monthly page.
- Pokopia: pokopia.pokemon.com/en-us (news, /expansion/, /update/; use the proxy), serebii.net/pokemonpokopia (events and patch history), Bulbapedia current events.
- Aniimo: aniimo.com/newslist is the official news feed. The article list only renders in the proxy's browser mode (a plain fetch returns an empty shell); individual detail pages (aniimo.com/newslist/detail/NNNNNN) work with a plain fetch. Cross-check store.steampowered.com/app/4126040 and funplus.com news.
- Images: for each item with its own dedicated page, capture the exact `og:image` URL (or a relevant in-page hero image). Never construct or guess an image URL. Set `image_reliable` to false for signed or expiring URLs.

## Changelog rule

Before overwriting `data.json`, diff the new dataset against the previous committed `data.json`:

- Up to 4 lines. Verbs: `+` (new), `→` (changed), `−` (removed).
- Meaningful changes only: new events, date moves, endings. Never wording tweaks.
- If there is no previous `data.json`, omit the changelog (set it to `null`).

## "Needs you" rule

- Only items where inaction has a cost: claim-by deadlines, buy-or-freeze decisions, expiring rewards or currency, ticket-sale windows, season last-calls.
- Max 8 cards, sorted by date. Each has a source link.
- Must never contradict the timeline: same dates, same facts.

## Style rules

- US dates ("Aug 4-11", "Through Aug 11").
- Never use em-dashes or en-dashes anywhere. Use commas, colons, or simple hyphens.
- For times, only write "local" when the publisher defines the event per player's timezone (for example Pokemon GO Community Day). Otherwise give the source's timezone (for example "10:00 a.m. PDT").
- No filler, no intros, no sign-offs. Every `detail` is one short actionable sentence.

## Data shape

Write `data.json` at the repo root, matching the schema in README.md exactly. Key points:

- `run_date`, `window_start` (= run date), `window_end` (= run date + 35 days), plus `window_display` and `last_updated_display` strings.
- Every timeline item gets `start` and `end` (ISO dates) whenever known; they drive the live dots and countdowns in the viewer's browser. An item with neither stays a static estimate.
- `estimate: true` items must carry an `estimate_basis` (one mono line, for example "Based on last year's schedule").
- Game order inside the Gaming category: WoW (Retail), Pokemon GO, Pokopia, Aniimo.
- A game with nothing in the window keeps its object with empty lists; the page shows an empty-state callout using `typical_lead_time`.

## Build and publish

1. `pip install -r requirements.txt` (Pillow; needed for image downscaling).
2. Write the new `data.json`.
3. `python3 tools/generate.py` (downloads new event images, renders `docs/index.html`).
4. Check the generator summary for skipped images and sanity-check the output.
5. Commit `data.json`, `docs/index.html`, and any new `docs/assets/img/*`. Fonts are already committed; run `tools/build_fonts.py` only if `docs/assets/fonts/` is missing.
