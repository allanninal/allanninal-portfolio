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
  "section": "slack",
  "date": "2026-08-31",
  "nav": [("/", "Portfolio"), ("/github/", "GitHub API"), ("/twilio/", "Twilio")],
  "footer_note": "Every script in this section is read only. They hold a token that can post "
                 "into your workspace, so none of them writes: they report what is wrong and "
                 "print the repair for you to run. A read-scoped token is enough.",
  "index_title": "Slack API Fix Guides: Scopes, Channels and Events",
  "index_desc": "Slack app problems a read-only script can find: missing scopes, a bot outside "
                "the channel it posts to, rate limits, and event subscriptions Slack switched "
                "off.",
  "index_h1": "Slack API fix guides",
  "index_lead": "Slack answers almost everything with HTTP 200, and puts the failure in the "
                "body as <code>ok: false</code>. Code that checks the status code sees success "
                "and moves on, so a bot that is not in the channel, or a token missing one "
                "scope, looks exactly like a bot that worked. Each note here explains one such "
                "problem and gives you a script that finds it through the API.",
  "index_chips": ["Read-only token", "Python and Node.js", "Tests included"],
  "scope_title": "Why these scripts never write",
  "scope_body": "<p>A script here holds a token that can post into your workspace and read your "
                "conversations. So these read, they tell you exactly what is wrong, and they "
                "print the repair: the scope to add, the channel to join, the reinstall URL. "
                "You run it.</p>"
                "<p>Slack is unusually good at saying what is missing &mdash; a "
                "<code>missing_scope</code> error names both what was <code>needed</code> and "
                "what was <code>provided</code> &mdash; and most of these notes are about "
                "reading the answer it already gave you.</p>",
  "group_heading": "Slack",
}

build(CFG, apply_visuals(CFG["section"], GUIDES))
