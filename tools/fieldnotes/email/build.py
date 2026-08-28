#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_section import build
from visuals import apply as apply_visuals
from guides_ses import GUIDES as A
from guides_ses2 import GUIDES as B
from guides_providers import GUIDES as C

CFG = {
  "section": "email",
  "date": "2026-08-28",
  "nav": [("/", "Portfolio"), ("/dns/", "DNS"), ("/aws/", "AWS cost"), ("/build/", "Build")],
  "footer_note": "Every script here is a starting point, not a substitute for reading your "
                 "own logs. Test against a non-production identity first.",
  "index_title": "Email Deliverability and Amazon SES Fix Guides",
  "index_desc": "Sending problems where the API says success and the mail never arrives. Each "
                "note gives a Python or Node.js script that finds and fixes it.",
  "index_h1": "Email deliverability fix guides",
  "index_lead": "Sending problems that look like nothing is wrong. The API returns a message "
                "ID, the logs say success, and the mail never arrives. Each note takes one of "
                "those, explains what is actually happening, and gives you a script in Python "
                "and Node.js that detects it &mdash; and repairs it where the API allows.",
  "index_chips": ["Python and Node.js", "SES v2 and provider APIs", "Detect, then repair",
                  "Tests included"],
  "scope_title": "Where this sits next to /dns/",
  "scope_body": "<p><a href=\"/dns/\">DNS &amp; domains</a> covers the record layer &mdash; SPF "
                "syntax, DKIM selectors, DMARC policy, MX targets. This section covers the layer "
                "above it, where the sending platform's own API is what finds and fixes the "
                "problem. If your records are wrong, start there. If your records are right and "
                "mail still is not arriving, start here.</p>",
  "group_heading": "Amazon SES and deliverability",
}
build(CFG, apply_visuals(CFG["section"], A + B + C))
