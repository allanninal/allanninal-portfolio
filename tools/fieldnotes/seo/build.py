#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_section import build
from visuals import apply as apply_visuals
from guides import GUIDES
from guides2 import GUIDES2

CFG = {
  "section": "seo",
  "date": "2026-08-28",
  "nav": [("/", "Portfolio"), ("/cloudflare/", "Cloudflare"), ("/dns/", "DNS"),
          ("/ci/", "GitHub Actions")],
  "footer_note": "Two of these scripts rewrite files you own &mdash; your sitemap and your "
                 "built HTML &mdash; and both require --apply or an explicit --out. The other "
                 "two only read, because the fix lives in your server config and no script "
                 "should guess at that.",
  "index_title": "Technical SEO Fix Guides: Contradictory Signals",
  "index_desc": "Indexing problems where two correct settings cancel each other: a blocked "
                "noindex, a sitemap of 404s, a not-found page returning 200.",
  "index_h1": "Technical SEO fix guides",
  "index_lead": "These are not ranking tips. They are cases where your site tells a crawler "
                "two contradictory things and the contradiction is invisible from a browser: "
                "a sitemap recommending pages that say noindex, a robots.txt blocking the "
                "noindex it was meant to enforce, a missing page answering 200. Each note "
                "explains the mechanism and gives you a script that checks it.",
  "index_chips": ["No API key needed", "Python and Node.js", "Tests included"],
  "scope_title": "Why these stay hidden",
  "scope_body": "<p>Every problem here is invisible in a browser. Status codes are not "
                "displayed, canonical tags are not rendered, and robots.txt is a file nobody "
                "opens. A page can be excluded from indexing in one place and recommended in "
                "another for years, because the two sources are written by different systems "
                "and nothing joins them up. The only way to see it is to ask the way a "
                "crawler asks.</p>",
  "group_heading": "Technical SEO",
}
build(CFG, apply_visuals(CFG["section"], GUIDES + GUIDES2))
