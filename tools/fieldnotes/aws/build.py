#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_section import build
from visuals import apply as apply_visuals
from guides_a import GUIDES as A
from guides_b import GUIDES as B

CFG = {
  "section": "aws",
  "date": "2026-08-28",
  "nav": [("/", "Portfolio"), ("/build/", "Build"), ("/email/", "Email &amp; SES"), ("/dns/", "DNS")],
  "footer_note": "Every script here defaults to reporting. Deleting AWS resources is "
                 "irreversible, so nothing is removed without an explicit id and a flag.",
  "index_title": "AWS Cost and Zombie Resource Fix Guides",
  "index_desc": "Resources that bill quietly for nothing. Each note gives the real monthly "
                "number and a Python or Node.js script to find and fix it.",
  "index_h1": "AWS cost fix guides",
  "index_lead": "Nine times out of ten a surprise AWS bill is not a traffic spike or a bug. "
                "It is a handful of resources that bill per hour whether or not anything uses "
                "them, sitting in states the console describes as healthy. Each note here takes "
                "one, gives the actual monthly figure, and hands you a script that finds every "
                "instance of it in your account.",
  "index_chips": ["Python and Node.js", "Real monthly figures", "Dry run by default",
                  "Tests included"],
  "scope_title": "Why these and not a cost tool",
  "scope_body": "<p>A cost dashboard tells you a number went up. These notes tell you which "
                "resource, why it charges when idle, what it costs, and how to remove it "
                "without breaking something. Every script reports first and needs an explicit "
                "resource id plus <code>--apply</code> before it deletes anything &mdash; these "
                "operations are irreversible, which is not true of anything in "
                "<a href=\"/email/\">/email/</a>.</p>",
  "group_heading": "Cost and zombie resources",
}
build(CFG, apply_visuals(CFG["section"], A + B))
