#!/usr/bin/env python3
# /// script
# dependencies = ["Pillow"]
# ///
"""Static-site generator: renders data.json into docs/index.html.

Reads the dataset, downloads event images (skipping unreliable URLs),
copies static assets, and fills tools/template.html. Never hand-edit
docs/index.html; edit data.json or the tools and re-run this.
"""

import hashlib
import html
import io
import json
import re
import shutil
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

GAME_META = {
    "WoW (Retail)": {
        "accent": "#C8842B",
        "display": "World of Warcraft",
        "calendar": "https://www.wowhead.com/events",
    },
    "Pokemon GO": {
        "accent": "#3D9BE9",
        "display": "Pokémon GO",
        "calendar": "https://leekduck.com/events/",
    },
    "Pokopia": {
        "accent": "#6FB07A",
        "display": "Pokopia",
        "calendar": "https://pokopia.pokemon.com/en-us/",
    },
}

GAME_TAGS = {
    "WoW (Retail)": "Retail",
    "Pokemon GO": "Niantic",
}

# Signed or expiring URLs: the image would rot, so leave the item text-only.
UNRELIABLE_URL = re.compile(
    r"(Expires=|X-Amz-|X-Goog-Signature|Signature=|se=\d|token=|"
    r"cdn\.discordapp\.com/(ephemeral-)?attachments)", re.I)


def esc(s):
    return html.escape(str(s), quote=True)


def days_from_run(run_date, iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return (date(y, m, d) - run_date).days


def initial_countdown(run_date, item):
    """Server-side countdown text so the page reads right without JS.
    app.js recomputes the same wording from the viewer's clock."""
    start, end = item.get("start"), item.get("end")
    if start and days_from_run(run_date, start) > 0:
        return "in %dd" % days_from_run(run_date, start)
    if end:
        de = days_from_run(run_date, end)
        if de < 0:
            return "ended"
        return "ends today" if de == 0 else "%dd left" % de
    if start:
        return "now"
    return ""


def initial_state(run_date, item):
    start, end = item.get("start"), item.get("end")
    if start and days_from_run(run_date, start) > 0:
        return "upcoming"
    if end and days_from_run(run_date, end) < 0:
        return "ended"
    if start or end:
        return "active"
    return item.get("state", "upcoming")


def fetch_bytes(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def process_image(url, skipped):
    """Download, downscale, and save an event image. Returns the relative
    path for the HTML, or None (with a log line) if skipped. A failed image
    never fails the build."""
    if not url:
        return None
    if UNRELIABLE_URL.search(url):
        skipped.append("signed/expiring url: %s" % url)
        return None
    dest = ASSETS / "img" / (hashlib.sha1(url.encode()).hexdigest() + ".jpg")
    rel = "assets/img/" + dest.name
    if dest.exists():
        return rel
    try:
        data = fetch_bytes(url)
    except Exception as e:
        skipped.append("fetch failed (%s): %s" % (e, url))
        return None
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if im.width > 900:
            im = im.resize((900, round(im.height * 900 / im.width)),
                           Image.LANCZOS)
        im.save(dest, "JPEG", quality=80)
    except ImportError:
        dest.write_bytes(data)
        skipped.append("note: Pillow missing, saved %s unprocessed" % dest.name)
    except Exception as e:
        skipped.append("decode failed (%s): %s" % (e, url))
        return None
    return rel


def render_changelog(cl):
    if not cl or not cl.get("lines"):
        return ""
    verb_class = {"+": "verb-add", "→": "verb-chg", "->": "verb-chg",
                  "−": "verb-rem", "-": "verb-rem"}
    rows = []
    for line in cl["lines"][:4]:
        verb = line.get("verb", "+")
        cls = verb_class.get(verb, "verb-add")
        shown = {"->": "→", "-": "−"}.get(verb, verb)
        rows.append('      <li><span class="verb %s">%s</span>%s</li>'
                    % (cls, esc(shown), esc(line.get("text", ""))))
    return (
        '  <aside class="changelog reveal">\n'
        '    <p class="eyebrow">Since last update &middot; %s</p>\n'
        '    <ul>\n%s\n    </ul>\n'
        '  </aside>\n' % (esc(cl.get("since", "")), "\n".join(rows)))


def render_needs(run_date, items):
    if not items:
        return ""
    cards = []
    for it in sorted(items, key=lambda x: x["date"])[:8]:
        classes = ["needs-card"]
        if it.get("urgent"):
            classes.append("urgent")
        if it.get("estimate"):
            classes.append("est")
        d = days_from_run(run_date, it["date"])
        count = "past" if d < 0 else "today" if d == 0 else "%dd" % d
        cards.append(
            '      <a class="%s" href="%s" data-deadline="%s">\n'
            '        <span class="needs-arrow">&#8599;</span>\n'
            '        <div class="needs-count" data-countdown>%s</div>\n'
            '        <div class="needs-date">%s</div>\n'
            '        <div class="needs-game">%s</div>\n'
            '        <div class="needs-action">%s</div>\n'
            '      </a>'
            % (" ".join(classes), esc(it["link"]), esc(it["date"]),
               esc(count), esc(it["date_display"]), esc(it["game"]),
               esc(it["action"])))
    return (
        '  <section class="needs reveal">\n'
        '    <p class="eyebrow">Deadlines</p>\n'
        '    <h2 class="section-title">Needs you</h2>\n'
        '    <div class="needs-grid">\n%s\n    </div>\n'
        '  </section>\n' % "\n".join(cards))


def render_event(run_date, item, skipped):
    state = initial_state(run_date, item)
    classes = ["event", "state-" + state]
    if item.get("estimate"):
        classes.append("is-estimate")

    attrs = ""
    if item.get("start"):
        attrs += ' data-start="%s"' % esc(item["start"])
    if item.get("end"):
        attrs += ' data-end="%s"' % esc(item["end"])

    head = ['<span class="state-dot" aria-hidden="true"></span>']
    head.append('<a class="event-title" href="%s">%s</a>'
                % (esc(item["link"]), esc(item["title"])))
    if item.get("paid") and item.get("price"):
        head.append('<span class="pill pill-price">%s</span>' % esc(item["price"]))
    elif item.get("paid"):
        head.append('<span class="pill pill-price">paid</span>')
    if item.get("estimate"):
        head.append('<span class="pill pill-est">estimate</span>')

    body = ['        <div class="event-head">%s</div>' % "".join(head)]
    if item.get("detail"):
        body.append('        <p class="event-detail">%s</p>' % esc(item["detail"]))
    if item.get("estimate_basis"):
        body.append('        <p class="event-basis">%s</p>'
                    % esc(item["estimate_basis"]))

    if item.get("image_url") and item.get("image_reliable", False):
        rel = process_image(item["image_url"], skipped)
        if rel:
            body.append(
                '        <figure class="event-media">'
                '<img src="%s" alt="%s" loading="lazy" decoding="async">'
                '</figure>' % (esc(rel), esc(item["title"])))
    elif item.get("image_url"):
        skipped.append("marked unreliable: %s" % item["image_url"])

    count = initial_countdown(run_date, item)
    count_html = ('\n        <div class="event-count" data-countdown>%s</div>'
                  % esc(count)) if count else ""

    return (
        '    <article class="%s"%s>\n'
        '      <div class="event-when">\n'
        '        <div class="event-dates">%s</div>%s\n'
        '      </div>\n'
        '      <div class="event-body">\n%s\n      </div>\n'
        '    </article>'
        % (" ".join(classes), attrs, esc(item.get("date_display", "")),
           count_html, "\n".join(body)))


def render_game(run_date, game, skipped, counts):
    key = game["game"]
    meta = GAME_META.get(key, {"accent": "#E9B949", "display": key,
                               "calendar": ""})
    tag = game.get("current_version") or GAME_TAGS.get(key, "")
    if game.get("current_version"):
        tag = "v" + game["current_version"].lstrip("v")

    parts = [
        '  <section class="game reveal" style="--accent:%s">' % meta["accent"],
        '    <header class="game-head">',
        '      <h2 class="game-name">%s</h2>' % esc(meta["display"]),
    ]
    if tag:
        parts.append('      <span class="game-tag">%s</span>' % esc(tag))
    parts.append('    </header>')

    timeline = game.get("timeline") or []
    rhythm = game.get("weekly_rhythm") or []
    past = game.get("just_past_window") or []

    if not timeline and not rhythm and not past:
        parts.append(
            '    <div class="game-empty">Nothing in the next month. '
            'See the <a href="%s">events calendar</a>.'
            '<span class="as-of">as of %s; %s</span></div>'
            % (esc(meta["calendar"]),
               esc(run_date.strftime("%b %-d, %Y")),
               esc(game.get("typical_lead_time", ""))))
    else:
        if timeline:
            items = sorted(timeline, key=lambda x: (x.get("start") or
                                                    x.get("end") or "9999"))
            parts.append('    <p class="group-label">Timeline</p>')
            parts.append('    <div class="timeline">')
            for item in items:
                parts.append(render_event(run_date, item, skipped))
                counts["events"] += 1
            parts.append('    </div>')
        if rhythm:
            parts.append('    <p class="group-label">Weekly rhythm</p>')
            parts.append('    <ul class="rhythm">')
            for line in rhythm:
                parts.append('      <li>%s</li>' % esc(line))
            parts.append('    </ul>')
        if past:
            parts.append('    <p class="group-label">Just past the window</p>')
            parts.append('    <ul class="past-window">')
            for line in past:
                parts.append('      <li>%s</li>' % esc(line))
            parts.append('    </ul>')

    parts.append('  </section>')
    return "\n".join(parts)


def main():
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    y, m, d = (int(x) for x in data["run_date"].split("-"))
    run_date = date(y, m, d)

    (ASSETS / "img").mkdir(parents=True, exist_ok=True)
    (ASSETS / "fonts").mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").touch()
    shutil.copy(TOOLS / "style.css", ASSETS / "style.css")
    shutil.copy(TOOLS / "app.js", ASSETS / "app.js")

    skipped = []
    counts = {"events": 0}

    content = [render_changelog(data.get("changelog")),
               render_needs(run_date, data.get("needs_you") or [])]
    for cat in data.get("categories", []):
        for game in cat.get("games", []):
            content.append(render_game(run_date, game, skipped, counts))

    page = (TOOLS / "template.html").read_text(encoding="utf-8")
    page = (page
            .replace("{{WINDOW_DISPLAY}}", esc(data["window_display"]))
            .replace("{{UPDATED_DISPLAY}}", esc(data["last_updated_display"]))
            .replace("{{CONTENT}}", "\n".join(p for p in content if p)))
    (DOCS / "index.html").write_text(page, encoding="utf-8")

    print("Rendered %d timeline items, %d needs-you cards -> docs/index.html"
          % (counts["events"], min(len(data.get("needs_you") or []), 8)))
    if skipped:
        print("Images skipped or noted:")
        for line in skipped:
            print("  - " + line)
    else:
        print("No images skipped.")


if __name__ == "__main__":
    sys.exit(main())
