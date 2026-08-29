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
  "section": "stripe",
  "date": "2026-08-30",
  "nav": [("/", "Portfolio"), ("/woocommerce/", "WooCommerce"), ("/build/", "Build")],
  "footer_note": "Every script in this section is read only. They hold a credential to a "
                 "live payments account, so none of them writes: they report what is "
                 "wrong and print the repair for you to run. Use a restricted key with "
                 "read access only &mdash; if it leaks, it cannot move money.",
  "index_title": "Stripe Fix Guides: Webhooks, Billing and Connect",
  "index_desc": "Stripe integration problems a read-only script can find for you: "
                "disabled webhooks, undelivered events, stalled subscriptions and "
                "blocked payouts.",
  "index_h1": "Stripe fix guides",
  "index_lead": "Stripe fails quietly. A webhook endpoint stops delivering and the "
                "payments still succeed, so revenue looks normal while everything that "
                "should happen <em>after</em> a payment silently stops. Each note here "
                "explains one such problem and gives you a script that finds it through "
                "the API, in Python and in Node.js, with tests.",
  "index_chips": ["Read-only key", "Python and Node.js", "Tests included"],
  "scope_title": "Why these scripts never write",
  "scope_body": "<p>Every other section on this site ships scripts that can repair what "
                "they find. These do not, on purpose. A script here holds a credential "
                "to a live payments account, where a bug does not cost you a stale cache "
                "&mdash; it cancels a subscription, refunds a charge, or disables a "
                "connected account's payouts.</p>"
                "<p>So they read, they tell you exactly what is wrong, and they print the "
                "repair: the endpoint, the parameters, the object id. You run it. Give "
                "them a <strong>restricted key with read access only</strong> and the "
                "worst case if one leaks is that somebody learns your webhook URLs.</p>",
  "group_heading": "Stripe",
}

# Drawn in Stripe indigo rather than the /dns/ default; see visuals_stripe.py.
build(CFG, apply_visuals(CFG["section"], GUIDES))
