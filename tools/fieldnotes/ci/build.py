#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_section import build
from visuals import apply as apply_visuals
from guides import GUIDES

CFG = {
  "section": "ci",
  "date": "2026-08-28",
  "nav": [("/", "Portfolio"), ("/aws/", "AWS cost"), ("/email/", "Email &amp; SES"), ("/dns/", "DNS")],
  "footer_note": "These scripts read the GitHub API and report. None of them edits a workflow "
                 "file, because whether a workflow is safe to cancel is a judgement about your "
                 "deploys, not a rule.",
  "index_title": "GitHub Actions Fix Guides: Silent CI Failures",
  "index_desc": "CI problems that never show up as red. A secret resolves to an empty string, a "
                "rate limit reads as a cache miss, and the bill grows quietly.",
  "index_h1": "GitHub Actions fix guides",
  "index_lead": "The worst CI problems are not the ones that fail. They are the ones that carry "
                "on: a secret that resolves to an empty string instead of erroring, a rate limit "
                "reported as a cache miss, a job that goes green having skipped the deploy. Each "
                "note takes one of those, explains why it is silent, and gives you a script that "
                "finds it through the API.",
  "index_chips": ["GitHub REST API", "Python and Node.js", "Read-only", "Tests included"],
  "scope_title": "Why these are hard to spot",
  "scope_body": "<p>Every problem here degrades gracefully by design, which is correct behaviour "
                "and exactly what hides it. A missing cache should not break a build; an "
                "untrusted pull request should not receive your credentials. The cost is that "
                "the log line for the safe outcome and the log line for the broken one are the "
                "same, so you have to ask the API instead.</p>",
  "group_heading": "GitHub Actions",
}
build(CFG, apply_visuals(CFG["section"], GUIDES))
