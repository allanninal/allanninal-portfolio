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
  "section": "cloudflare",
  "date": "2026-08-28",
  "nav": [("/", "Portfolio"), ("/dns/", "DNS"), ("/ci/", "GitHub Actions"),
          ("/email/", "Email &amp; SES")],
  "footer_note": "These scripts read the Cloudflare API and report. The two that can change "
                 "a setting require --apply, because SSL mode and proxy status take effect "
                 "on every request to the zone the moment they are written.",
  "index_title": "Cloudflare Fix Guides: Rules That Never Fire",
  "index_desc": "Cloudflare problems where nothing errors: a rule that matches and is "
                "skipped, a purge that reports success, an SSL mode that loops.",
  "index_h1": "Cloudflare fix guides",
  "index_lead": "Cloudflare rarely tells you a rule did not run. It tells you the request "
                "succeeded. A Page Rule can be enabled, correct and permanently shadowed; a "
                "purge can return success having cleared nothing; a redirect loop can appear "
                "with no deploy at all. Each note takes one of those, explains why it is "
                "silent, and gives you a script that asks the API instead of guessing.",
  "index_chips": ["Cloudflare API", "Python and Node.js", "Tests included"],
  "scope_title": "Why Cloudflare problems are quiet",
  "scope_body": "<p>Every problem here comes from a component behaving exactly as designed. "
                "First-match-wins rule evaluation is a legitimate model. An idempotent purge "
                "API is correct. Flexible SSL exists for origins that genuinely cannot do "
                "TLS. Nothing is broken in isolation &mdash; the failure lives in the "
                "combination, which is why neither end reports it and why you have to look "
                "at the whole configuration rather than the piece that looks wrong.</p>",
  "group_heading": "Cloudflare",
}
build(CFG, apply_visuals(CFG["section"], GUIDES + GUIDES2))
