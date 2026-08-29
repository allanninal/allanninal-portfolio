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
  "section": "twilio",
  "date": "2026-08-30",
  "nav": [("/", "Portfolio"), ("/stripe/", "Stripe"), ("/email/", "Email & SES")],
  "footer_note": "Every script in this section is read only. They hold a credential to an "
                 "account that can send messages and spend money, so none of them writes: "
                 "they report what is wrong and print the repair for you to run. Use an "
                 "API Key with read access rather than the account auth token.",
  "index_title": "Twilio Fix Guides: Delivery, 10DLC and Webhooks",
  "index_desc": "Twilio problems a read-only script can find: messages filtered by "
                "carriers, unregistered 10DLC campaigns, numbers on demo TwiML and "
                "webhooks pointing nowhere.",
  "index_h1": "Twilio fix guides",
  "index_lead": "Most Twilio failures are a setting, not a bug. A number is still pointing "
                "at the demo TwiML URL, a campaign never finished registering, a webhook "
                "has no fallback. None of it raises an exception in your code &mdash; the "
                "message simply does not arrive. Each note here explains one such problem "
                "and gives you a script that finds it through the API.",
  "index_chips": ["Read-only key", "Python and Node.js", "Tests included"],
  "scope_title": "Why these scripts never write",
  "scope_body": "<p>A script here holds a credential to an account that can send messages "
                "and charge you for them. So these read, they tell you exactly what is "
                "wrong, and they print the repair: the resource, the field, the value. "
                "You run it.</p>"
                "<p>Give them a <strong>Twilio API Key with read access</strong> rather "
                "than the account auth token. If a read-only key leaks, somebody learns "
                "your phone numbers; if the auth token leaks, somebody sends from "
                "them.</p>",
  "group_heading": "Twilio",
}

build(CFG, apply_visuals(CFG["section"], GUIDES))
