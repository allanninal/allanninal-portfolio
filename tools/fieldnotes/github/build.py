#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_section import build
from visuals import apply as apply_visuals

# Batches are discovered, not listed: this section is written a few notes at a
# time and each batch arrives as its own guides_<letter>.py. Sorted so the index
# order is stable between builds.
import importlib
GUIDES = []
for _m in sorted(q.stem for q in Path(__file__).resolve().parent.glob("guides*.py")):
    GUIDES.extend(importlib.import_module(_m).GUIDES)

CFG = {
  "section": "github",
  "date": "2026-08-31",
  "nav": [("/", "Portfolio"), ("/ci/", "GitHub Actions"), ("/slack/", "Slack")],
  "footer_note": "Every script in this section is read only. They hold a token that can reach "
                 "your repositories, so none of them writes: they report what is wrong and "
                 "print the repair for you to run. A read-only token is enough, and "
                 "GET /rate_limit does not consume quota.",
  "index_title": "GitHub API Fix Guides: Rate Limits, Apps and Webhooks",
  "index_desc": "GitHub API problems a read-only script can find: secondary rate limits, "
                "pagination that stops at 30, webhooks failing unnoticed, and App tokens that "
                "expired an hour ago.",
  "index_h1": "GitHub API fix guides",
  "index_lead": "The GitHub API is generous until it is not, and the ways it stops working are "
                "quiet ones: a list that returns thirty items because nobody followed the "
                "<code>Link</code> header, a webhook that has been failing for a month, a "
                "secondary rate limit that answers 403 with no <code>Retry-After</code>. Each "
                "note here explains one such problem and gives you a script that finds it "
                "through the API.",
  "index_chips": ["Read-only token", "Python and Node.js", "Tests included"],
  "scope_title": "Not GitHub Actions",
  "scope_body": "<p>This section is about the GitHub <strong>API</strong> as an integration "
                "surface: authentication, rate limits, pagination, webhooks, Apps and GraphQL. "
                "Workflow problems &mdash; empty secrets in fork pull requests, silent cache "
                "misses, redundant billed runs &mdash; live in "
                "<a href=\"/ci/\">GitHub Actions field notes</a> instead.</p>"
                "<p>Every script here is read only. They report what is wrong and print the "
                "repair; they never write.</p>",
  "group_heading": "GitHub API",
}

build(CFG, apply_visuals(CFG["section"], GUIDES))
