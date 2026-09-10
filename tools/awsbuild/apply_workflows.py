"""Put the n8n and Make downloads on every page of a series that has them.

The offer block used to end "There is no download on this page and nothing is
paywalled." That was true until the workflow ports existed. This rewrites that
sentence wherever a series has files, and adds a downloads list above it, so the
page never contradicts itself.

Run after gen.py, for the same reason feature photos are replayed: gen.py
rewrites article HTML from the specs and drops anything injected afterwards.
"""
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"
WF = BUILD / "assets" / "workflows"

OLD_FOOT = ("Everything above is free to read, end to end &mdash; the architecture, the "
            "cost breakdown and the engineering reference. There is no download on this "
            "page and nothing is paywalled. ")
NEW_FOOT = ("Everything above is free to read, end to end &mdash; the architecture, the "
            "cost breakdown and the engineering reference. The two downloads are free "
            "as well, and nothing is paywalled. ")

BLOCK_RE = re.compile(r'<div class="offer__dl">.*?</div>', re.S)


def block(slug):
    rows = []
    for plat, label, what in (
            ("n8n", "n8n workflow",
             "importable JSON, validated against n8n&#x27;s own node database"),
            ("make", "Make scenario",
             "blueprint JSON for the free plan, plus what it costs in credits")):
        z = WF / f"{slug}-{plat}.zip"
        if not z.exists():
            continue
        kb = round(z.stat().st_size / 1024)
        rows.append(
            f'<li class="offer__item"><span class="offer__name">{label}</span>'
            f'<span class="offer__what">{what}</span>'
            f'<a class="offer__buy" href="/build/assets/workflows/{slug}-{plat}.zip" '
            f'download>Download ({kb} KB)</a></li>')
    if not rows:
        return ""
    return ('<div class="offer__dl"><p class="offer__label">Run it on n8n or Make '
            '<span class="offer__badge offer__badge--live">Free</span></p>'
            '<ul class="offer__list">' + "".join(rows) + "</ul>"
            '<p class="offer__foot">Each archive holds the workflow, a README and a '
            'diagram of the flow with the credentials it needs. These are ports, not '
            'equivalents &mdash; per-step IAM and the cost breakdown in part six do not '
            'survive the move, and the README says exactly how.</p></div>')


def main(slugs=None):
    reg = json.loads((ROOT / "tools" / "awsbuild" / "registry.json")
                     .read_text(encoding="utf-8"))
    changed = 0
    for slug, entry in reg.items():
        if slugs and slug not in slugs:
            continue
        b = block(slug)
        if not b:
            continue
        pages = [BUILD / "series" / slug / "index.html"]
        pages += [BUILD / p["slug"] / "index.html" for p in entry["parts"]]
        for f in pages:
            if not f.exists():
                continue
            s = f.read_text(encoding="utf-8")
            before = s
            s = BLOCK_RE.sub("", s)
            s = s.replace(OLD_FOOT, NEW_FOOT)
            s = s.replace('<p class="offer__foot">', b + '<p class="offer__foot">', 1)
            if s != before:
                f.write_text(s, encoding="utf-8")
                changed += 1
    print(f"workflow downloads: {changed} page(s) updated")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
