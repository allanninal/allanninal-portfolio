"""Rebuild everything derived: thumbnails, /build/index.html, sitemap, feed, llms.txt.

Idempotent, and the single place that knows the shape of those four files, so
adding a series is: write the spec, run this, done.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from awsbuild import registry, thumbs  # noqa: E402
from awsbuild.diagrams import pick_icon  # noqa: E402
from awsbuild.pages import BASE, fmt_date  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"
STATIC = ["", "work-with-me/", "resources/"]


def esc(s):
    return html.escape(s, quote=True)


# --------------------------------------------------------------------------
def icons_for(entry):
    """Three service icons for a card, taken from the series' own words.

    "compute" and "external" are the picker's fallbacks, so they only earn a
    slot when nothing more specific turned up -- otherwise every card would be
    three orange chips.
    """
    sources = [entry["name"], entry["tagline"]]
    sources += [re.sub(r"^(How|What) (a|an|the) ", "", p["title"]) for p in entry["parts"]]
    strong, weak, seen = [], [], set()
    for src in sources:
        name = pick_icon(src, "", True)
        if name in seen:
            continue
        seen.add(name)
        (weak if name in ("compute", "external") else strong).append(name)
    picked = (strong + weak)[:3]
    for filler in ("queue", "database", "monitor", "person"):
        if len(picked) >= 3:
            break
        if filler not in picked:
            picked.append(filler)
    return picked[:3]


def build_thumbs(reg):
    for slug, e in reg.items():
        thumbs.write(slug, e["name"], icons_for(e))
    return len(reg)


# --------------------------------------------------------------------------
def build_index(reg):
    src = (BUILD / "index.html").read_text(encoding="utf-8")
    order = sorted(reg.values(), key=lambda e: (e["date"], e["slug"]), reverse=True)

    cards = []
    for e in order:
        cards.append(
            '          <li class="card">\n'
            f'            <a class="card__thumb" href="/build/series/{e["slug"]}/" '
            f'aria-label="{esc(e["name"])} series">\n'
            f'              <img src="/build/assets/thumbs/{e["slug"]}.svg" width="480" '
            f'height="270" loading="lazy" decoding="async" '
            f'alt="{esc(e["name"])} &mdash; series thumbnail">\n'
            "            </a>\n"
            '            <div class="card__body">\n'
            f'              <h2 class="card__title"><a href="/build/series/{e["slug"]}/">'
            f'{e["name"]}</a></h2>\n'
            f'              <p class="card__tagline">{e["tagline"]}</p>\n'
            f'              <p class="card__meta"><time datetime="{e["date"]}">'
            f'{fmt_date(e["date"])}</time> &middot; {len(e["parts"])} parts</p>\n'
            "            </div>\n"
            "          </li>")
    grid = '<ul class="card-grid">\n' + "\n".join(cards) + "\n        </ul>"
    out = re.sub(r'<ul class="card-grid">.*?</ul>', lambda _: grid, src, flags=re.S)

    # the ItemList in the head must match the grid
    items = [{"@type": "ListItem", "position": i + 1,
              "item": {"@type": "CreativeWorkSeries",
                       "name": f"{e['name']} series",
                       "url": f"{BASE}/series/{e['slug']}/"}}
             for i, e in enumerate(order)]
    out = re.sub(r'("itemListElement": )\[.*?\n        \]',
                 lambda _: json.dumps(items, indent=10, ensure_ascii=False)
                 .replace("\n", "\n  ").join(('"itemListElement": ', "")),
                 out, flags=re.S) if False else out
    blob = json.dumps(items, indent=2, ensure_ascii=False)
    blob = "\n".join("        " + ln for ln in blob.splitlines()).lstrip()
    out = re.sub(r'"itemListElement": \[.*?\n      \]',
                 lambda _: f'"itemListElement": {blob}', out, count=1, flags=re.S)
    (BUILD / "index.html").write_text(out, encoding="utf-8")
    return len(order)


# --------------------------------------------------------------------------
def build_sitemap(reg):
    today = dt.date.today().isoformat()
    urls = [("", today, "daily", "1.0"),
            ("work-with-me/", today, "monthly", "0.9"),
            ("resources/", today, "monthly", "0.7")]
    for e in sorted(reg.values(), key=lambda x: x["date"], reverse=True):
        urls.append((f"series/{e['slug']}/", e["date"], "monthly", "0.9"))
        for p in e["parts"]:
            urls.append((f"{p['slug']}/", e["date"], "monthly", "0.8"))
    body = "\n".join(
        f"  <url>\n    <loc>{BASE}/{loc}</loc>\n    <lastmod>{mod}</lastmod>\n"
        f"    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>"
        for loc, mod, freq, pri in urls)
    (BUILD / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + body + "\n</urlset>\n", encoding="utf-8")

    # root sitemap index points at us; keep its lastmod honest
    root = ROOT / "sitemap.xml"
    s = root.read_text(encoding="utf-8")
    s = re.sub(r"(<loc>https://www\.allanninal\.dev/build/sitemap\.xml</loc>\s*<lastmod>)"
               r"[\d-]+(</lastmod>)", rf"\g<1>{today}\g<2>", s)
    root.write_text(s, encoding="utf-8")
    return len(urls)


# --------------------------------------------------------------------------
def _summary(slug):
    f = BUILD / slug / "index.html"
    if not f.exists():
        return ""
    m = re.search(r'<meta name="description" content="([^"]*)"', f.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def build_feed(reg):
    entries = []
    order = sorted(reg.values(), key=lambda e: e["date"], reverse=True)
    for e in order[:30]:
        for i, p in enumerate(e["parts"]):
            entries.append(
                "  <entry>\n"
                f"    <title>{html.escape(p['title'])}</title>\n"
                f'    <link href="{BASE}/{p["slug"]}/" rel="alternate" type="text/html"/>\n'
                f"    <id>{BASE}/{p['slug']}/</id>\n"
                f"    <published>{e['date']}T09:00:00Z</published>\n"
                f"    <updated>{e['date']}T09:00:00Z</updated>\n"
                f'    <summary type="text">{html.escape(_summary(p["slug"]))} '
                f"Part {i + 1} of {len(e['parts'])} in the {html.escape(e['name'])} "
                "series.</summary>\n"
                "  </entry>")
    newest = order[0]["date"] if order else dt.date.today().isoformat()
    (BUILD / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        "  <title>allanninal.dev/build</title>\n"
        "  <subtitle>Diagram-first design walkthroughs of automations, DevOps, and cloud "
        "infrastructure by Allan Niñal. Open to builds, collabs, and design reviews.</subtitle>\n"
        f'  <link href="{BASE}/feed.xml" rel="self" type="application/atom+xml"/>\n'
        f'  <link href="{BASE}/" rel="alternate" type="text/html"/>\n'
        f"  <updated>{newest}T09:00:00Z</updated>\n"
        f"  <id>{BASE}/</id>\n"
        "  <author>\n    <name>Allan Niñal</name>\n  </author>\n"
        "  <rights>&#169; 2026 Allan Niñal</rights>\n\n"
        + "\n".join(entries) + "\n</feed>\n", encoding="utf-8")
    return len(entries)


# --------------------------------------------------------------------------
def build_llms(reg):
    order = sorted(reg.values(), key=lambda e: e["date"], reverse=True)
    lines = ["# allanninal.dev/build", "",
             "> Diagram-first design walkthroughs of small AWS systems for small businesses.",
             "> Every series is seven posts: the whole system, four mechanism posts, a cost",
             "> breakdown, and an engineering reference. Free to read, nothing paywalled.", "",
             f"{len(order)} series, {sum(len(e['parts']) for e in order)} posts. "
             f"Newest first.", ""]
    for e in order:
        lines.append(f"## {e['name']} ({e['date']})")
        lines.append(f"{e['tagline']}")
        lines.append(f"- Series index: {BASE}/series/{e['slug']}/")
        for i, p in enumerate(e["parts"]):
            lines.append(f"- Part {i + 1}: {p['title']} — {BASE}/{p['slug']}/")
        lines.append("")
    (BUILD / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    return len(order)


def main():
    reg = registry.load()
    print("thumbnails:", build_thumbs(reg))
    print("index cards:", build_index(reg))
    print("sitemap urls:", build_sitemap(reg))
    print("feed entries:", build_feed(reg))
    print("llms.txt series:", build_llms(reg))


if __name__ == "__main__":
    main()
