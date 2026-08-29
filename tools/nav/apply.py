#!/usr/bin/env python3
"""Put the canonical header on every first-party page.

Run from the repo root. Idempotent: a page that already carries the bar has it
replaced, not duplicated, so this can run again after any section is rebuilt.

Deliberately NOT touched:
  templates/   — each template is the product; it previews in its own design
  redesign/    — Astro source and its dist
  index.html, 404.html — built from redesign/, which renders the same bar itself
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import header as H  # noqa: E402

ROOT = H.SITE_ROOT

# Sections that get the bar, and the header markup each currently carries.
SECTIONS = {
    d: r'<header class="site-header">.*?</header>'
    for d in [
        "woocommerce", "shopify", "bigcommerce", "medusa", "shopware", "saleor",
        "prestashop", "magento", "aws", "cloudflare", "ci", "email", "dns",
        "seo", "stripe", "twilio", "spreadsheets", "build",
    ]
}
# The two hand-written sections predate the generators and carry three
# different nav shapes between them; match all of them.
_LEGACY_NAV = r'<nav(?:\s+class="(?:nav|top-nav)")?\s*>.*?</nav>'
SECTIONS["blog"] = _LEGACY_NAV
SECTIONS["projects"] = _LEGACY_NAV

# Checked and inserted one at a time so a page the generators already emit
# these into is left byte-identical, rather than being handed a second copy.
CSS_LINKS = [
    '<link rel="stylesheet" href="/assets/site-nav.css">',
    '<link rel="stylesheet" href="/assets/site-mobile.css">',
]
JS_TAG = '<script defer src="/assets/site-nav.js"></script>'

# Matches the whole injected unit — bar, and the skip-link target that follows
# it on pages with no <main> — so a re-run replaces it exactly rather than
# accumulating stray newlines and duplicate anchors.
ANX_BLOCK = re.compile(
    r'\s*<div class="anx-root">.*?</header>\s*</div>'
    r'(?:<div id="main" tabindex="-1"></div>)?',
    re.S,
)


def process(path: str, section: str, pattern: str) -> str | None:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        src = fh.read()
    out = src

    # Re-runs replace the existing bar instead of stacking another one.
    out = ANX_BLOCK.sub("", out, count=1)

    # Drop the section's own header: the first match, and only if it sits near
    # the start of the *body*. Measuring from the start of the file would let a
    # large inline <style> block in <head> push a perfectly ordinary site nav
    # past the cutoff, which is exactly how the blog pages kept two bars.
    body_start = re.search(r"<body[^>]*>", out)
    if body_start:
        m = re.search(pattern, out[body_start.end():], re.S)
        if m and m.start() < 4000:
            a = body_start.end() + m.start()
            b = body_start.end() + m.end()
            out = out[:a] + out[b:]

    # The skip link needs somewhere to land.
    main_id = "main"
    mm = re.search(r"<main\b([^>]*)>", out)
    if mm:
        attrs = mm.group(1)
        found = re.search(r'id="([^"]+)"', attrs)
        if found:
            main_id = found.group(1)
        else:
            out = out[: mm.start()] + f"<main id=\"main\"{attrs}>" + out[mm.end():]
    anchor = "" if mm else '<div id="main" tabindex="-1"></div>'

    bm = re.search(r"<body[^>]*>", out)
    if not bm:
        return None
    out = out[: bm.end()] + "\n" + H.render(section, main_id) + anchor + out[bm.end():]

    for link in CSS_LINKS:
        if link not in out:
            out = out.replace("</head>", f"{link}\n</head>", 1)
    if JS_TAG not in out:
        out = out.replace("</body>", f"{JS_TAG}\n</body>", 1)

    return out if out != src else None


def main() -> None:
    dry = "--dry" in sys.argv
    changed = skipped = 0
    for section, pattern in SECTIONS.items():
        base = os.path.join(ROOT, section)
        if not os.path.isdir(base):
            print(f"  ! missing section {section}")
            continue
        n = 0
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ("assets", "downloads")]
            for fn in filenames:
                if not fn.endswith(".html"):
                    continue
                p = os.path.join(dirpath, fn)
                new = process(p, section, pattern)
                if new is None:
                    skipped += 1
                    continue
                if not dry:
                    with open(p, "w", encoding="utf-8") as fh:
                        fh.write(new)
                n += 1
                changed += 1
        print(f"  {section:14s} {n:5d} pages")
    print(f"\n{'would change' if dry else 'changed'}: {changed}   unchanged: {skipped}")


if __name__ == "__main__":
    main()
