#!/usr/bin/env python3
"""Write a section's sitemap.xml, and register it in the root sitemap index.

Both files were hand-maintained: every section's sitemap.xml was typed out and
its <sitemap> entry added to the root index by hand. That works for a section
published once and never touched, and not at all for one written in batches —
adding four notes meant remembering to add four <url> blocks in the right file
with the right priority.

    python3 tools/fieldnotes/make_sitemap.py stripe --date 2026-08-30 --apply
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://www.allanninal.dev"


def build(section: str, date: str, apply: bool) -> int:
    sec = ROOT / section
    slugs = sorted(p.name for p in sec.iterdir()
                   if p.is_dir() and p.name not in ("assets", "downloads")
                   and (p / "index.html").exists())

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>{SITE}/{section}/</loc><lastmod>{date}</lastmod>'
             f'<changefreq>monthly</changefreq><priority>0.9</priority></url>']
    for slug in slugs:
        lines.append(f'  <url><loc>{SITE}/{section}/{slug}/</loc><lastmod>{date}</lastmod>'
                     f'<changefreq>monthly</changefreq><priority>0.8</priority></url>')
    lines.append('</urlset>')
    xml = "\n".join(lines) + "\n"

    index = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    entry = (f"  <sitemap>\n    <loc>{SITE}/{section}/sitemap.xml</loc>\n"
             f"    <lastmod>{date}</lastmod>\n  </sitemap>\n")
    if f"/{section}/sitemap.xml" in index:
        index = re.sub(
            rf"  <sitemap>\s*<loc>{re.escape(SITE)}/{section}/sitemap\.xml</loc>\s*"
            rf"<lastmod>[^<]*</lastmod>\s*</sitemap>\n",
            entry, index, count=1)
    else:
        index = index.replace("</sitemapindex>", entry + "</sitemapindex>")

    print(f"  {section}: {len(slugs)} note(s) + index, lastmod {date}")
    if apply:
        (sec / "sitemap.xml").write_text(xml, encoding="utf-8")
        (ROOT / "sitemap.xml").write_text(index, encoding="utf-8")
    print("APPLIED" if apply else "DRY RUN — pass --apply to write")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("section")
    ap.add_argument("--date", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    raise SystemExit(build(a.section, a.date, a.apply))
