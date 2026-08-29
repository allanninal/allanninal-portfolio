#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch I.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Stripe indigo.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#635BFF"
D.set_theme(BRAND)

V = {}

V["stripe/checkout-expired-session-share"] = {
    "flow_intro": (
        "The script tallies status across a fixed window and counts the sessions "
        "that have already lapsed but are still marked open, because those are the "
        "ones a naive count reads as still in progress."
    ),
    "diagram_problem": D.chain(
        "sces-p",
        "A Checkout Session lapsing a full day after the customer left",
        "Every step in this sequence returned 200, which is why nothing alerts and "
        "the abandonment rate drifts unmeasured.",
        [
            ("Session created", "no expires_at set"),
            ("Customer leaves", "in the first minutes"),
            ("Status stays open", "for 24 hours"),
            ("expired fires", "a day too late"),
            ("Nobody subscribed", "no metric anywhere"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sces-f",
        "Sorting a window of Checkout Sessions by the share that expired unpaid",
        "The share only means something as a series. Keep the window fixed and "
        "count the lapsed sessions Stripe has not relabelled yet.",
        ("GET /v1/checkout/sessions", "created[gte], paginated, tallied"),
        [
            ("No sessions at all", "no data, not a clean score", "plain"),
            ("Under a quarter expired", "normal, keep the series", "good"),
            ("Open past expires_at", "lapsed and uncounted", "bad"),
            ("Over half expired", "shorten expires_at now", "bad"),
        ],
    ),
}

V["stripe/payment-link-inactive-still-published"] = {
    "flow_intro": (
        "The script lists every Payment Link and then asks each dead one whether "
        "customers are still arriving, because that count is what separates a lost "
        "sale from a tidy-up."
    ),
    "diagram_problem": D.chain(
        "splip-p",
        "A deactivated Payment Link still published on the site",
        "The URL keeps resolving forever. What changed is only what Stripe serves "
        "at the other end, and no request ever reaches your server.",
        [
            ("Link deactivated", "one click, good reason"),
            ("URL still published", "page, email, invoice PDF"),
            ("Customer clicks", "URL returns 200"),
            ("Deactivation page", "sale ends there"),
            ("Nothing logged", "found six weeks later"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "splip-f",
        "Sorting Payment Links by the active flag and by traffic still arriving",
        "A missing active flag is a thing you do not know, not a thing you know is "
        "false. Absent is not the same as deactivated.",
        ("GET /v1/payment_links", "plus sessions per link"),
        [
            ("active true", "live, leave it", "good"),
            ("Inactive, no traffic", "housekeeping", "plain"),
            ("Inactive with traffic", "sales lost right now", "bad"),
            ("No active flag", "unknown, check by hand", "bad"),
        ],
    ),
}

V["stripe/billing-portal-no-configuration"] = {
    "flow_intro": (
        "The script reads the configurations in whichever mode the key belongs to "
        "and counts who can press the button, because the same missing default is a "
        "ticket on one account and an outage on another."
    ),
    "diagram_problem": D.chain(
        "sbpnc-p",
        "A Billing Portal session failing on the first live click",
        "The default configuration is created by a Dashboard save, so nothing in "
        "the repository records that live mode never had one.",
        [
            ("Portal built", "tested in test mode"),
            ("Settings saved", "test mode only"),
            ("Live deploy", "no code difference"),
            ("Session create 400s", "no default configuration"),
            ("Generic 500 shown", "Stripe message swallowed"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sbpnc-f",
        "Sorting portal configurations by default status and by active status",
        "Both flags matter. A default that is inactive passes a check that counts "
        "the array and still fails every call.",
        ("GET billing_portal/configurations", "with the live key, plus subscriptions"),
        [
            ("Default and active", "sessions resolve", "good"),
            ("None, no subscribers", "waiting to break", "bad"),
            ("None, live subscribers", "every click 400s now", "bad"),
            ("Active but no default", "pass configuration=bpc_", "bad"),
        ],
    ),
}

V["stripe/checkout-complete-payment-unpaid"] = {
    "flow_intro": (
        "The script flags complete sessions whose payment_status is unpaid, then "
        "expands the PaymentIntent, because still processing and already failed "
        "look identical on the session itself."
    ),
    "diagram_problem": D.chain(
        "sccpu-p",
        "An order fulfilled on session completed before the payment settled",
        "status and payment_status are independent fields, and complete explicitly "
        "allows the payment to still be in progress.",
        [
            ("ACH enabled", "a Dashboard setting"),
            ("Session completes", "payment_status unpaid"),
            ("completed fires", "handler ships the order"),
            ("Debit fails", "days later"),
            ("No branch for it", "goods already gone"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sccpu-f",
        "Sorting complete Checkout Sessions by payment status and intent state",
        "Unpaid and processing is a normal bank debit. Unpaid with a dead intent is "
        "stock that has already left the warehouse.",
        ("Session plus expanded intent", "status, payment_status, intent status"),
        [
            ("paid", "fulfilment is safe", "good"),
            ("no_payment_required", "nothing to collect", "good"),
            ("unpaid, processing", "wait for the async event", "plain"),
            ("unpaid, intent dead", "unwind the fulfilment", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
