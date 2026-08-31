"""Replace the free-text "Guides & starters" note with a structured offer block.

Nothing here is downloadable yet, so every line renders as Coming soon. The
moment a Gumroad product exists, put its URL in products.json under the series
slug and re-run: that line becomes a buy button everywhere the series appears.
No page ever links to a zip.
"""
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PRODUCTS = json.loads((ROOT / "products.json").read_text(encoding="utf-8"))["series"]

ITEMS = [
    ("guide", "Workflow guide", "the build step by step, with the decisions and the dead ends"),
    ("starter", "AWS CDK starter", "the same system as infrastructure-as-code you can deploy"),
    ("bundle", "Bundle", "both together"),
]

OLD_RE = re.compile(
    r'<aside class="support">\s*<p class="support__label">Guides &amp; starters</p>.*?</aside>',
    re.S)
NEW_RE = re.compile(r'<aside class="offer"[^>]*>.*?</aside>', re.S)
SERIES_RE = re.compile(r'/build/series/([a-z0-9-]+)/')


def block(slug):
    prod = PRODUCTS.get(slug, {})
    live = any(prod.get(k) for k, _, _ in ITEMS)
    badge = ('<span class="offer__badge offer__badge--live">Available</span>' if live
             else '<span class="offer__badge offer__badge--soon">Coming soon</span>')
    rows = []
    for key, name, what in ITEMS:
        url = prod.get(key)
        if url:
            action = (f'<a class="offer__buy" href="{html.escape(url)}" rel="noopener" '
                      f'target="_blank">Get it on Gumroad</a>')
        else:
            action = '<span class="offer__state">Coming soon</span>'
        rows.append(f'<li class="offer__item"><span class="offer__name">{name}</span>'
                    f'<span class="offer__what">{what}</span>{action}</li>')
    foot = ("Everything above is free to read, end to end &mdash; the architecture, the cost "
            "breakdown and the engineering reference. There is no download on this page and "
            "nothing is paywalled. "
            '<a href="/build/resources/">See what is coming</a>, or '
            '<a href="https://www.linkedin.com/in/allanninal/" rel="noopener">tell me on '
            "LinkedIn</a> which one you want first.")
    return ('<aside class="offer" aria-label="Guides and starters">'
            f'<p class="offer__label">Guides &amp; starters {badge}</p>'
            f'<ul class="offer__list">{"".join(rows)}</ul>'
            f'<p class="offer__foot">{foot}</p>'
            "</aside>")


def slug_for(page, path):
    m = SERIES_RE.search(page)
    if m:
        return m.group(1)
    return path.parent.name


def main(root="build"):
    n = 0
    for f in sorted(pathlib.Path(root).rglob("*.html")):
        s = f.read_text(encoding="utf-8")
        if 'support__label">Guides' not in s and '<aside class="offer"' not in s:
            continue
        new = block(slug_for(s, f))
        out = OLD_RE.sub(lambda _: new, s)
        out = NEW_RE.sub(lambda _: new, out)
        if out != s:
            f.write_text(out, encoding="utf-8")
            n += 1
    print("offer block written on", n, "pages")


if __name__ == "__main__":
    main(*sys.argv[1:])
