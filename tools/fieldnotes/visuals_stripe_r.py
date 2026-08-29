#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch R.

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

V["stripe/legacy-charges-api-no-payment-intent"] = {
    "flow_intro": (
        "The script sorts every charge by the API that made it, then splits the "
        "declines, because only one decline reason is caused by the API and the "
        "rest would have happened either way."
    ),
    "diagram_problem": D.chain(
        "slca-p",
        "A direct charge failing an issuer that asks for authentication",
        "Nothing in the request can present a 3D Secure challenge, so the only "
        "answer the legacy path has for an SCA issuer is a decline.",
        [
            ("Renewal job charges", "POST /v1/charges, a token"),
            ("No intent exists", "nothing can authenticate"),
            ("Issuer asks for SCA", "European card"),
            ("Declined", "authentication_required"),
            ("Retry declines too", "same API, same answer"),
        ],
        fail_at=1,
        loop=(4, 1, "each retry repeats the same call"),
    ),
    "diagram_fix": D.branch(
        "slca-f",
        "Sorting charges by whether a PaymentIntent created them",
        "An absent payment_intent key and an explicit null mean the same thing. "
        "A membership test reports a clean account.",
        ("GET /v1/charges", "paginated, 90 days"),
        [
            ("payment_intent set", "modern, can authenticate", "good"),
            ("null, succeeded", "legacy volume, no 3DS possible", "bad"),
            ("null, authentication_required", "caused by the API itself", "bad"),
            ("null, other decline", "would have failed anyway", "plain"),
        ],
    ),
}

V["stripe/legacy-card-sources-still-attached"] = {
    "flow_intro": (
        "The script reads both card stores for the same customer, and both "
        "defaults, because which default is populated decides what the next "
        "renewal will actually charge."
    ),
    "diagram_problem": D.chain(
        "slcs-p",
        "A card saved in the old store being invisible to the new billing code",
        "The Dashboard renders both stores on one page, so the card is plainly "
        "there while the API call that needs it returns nothing.",
        [
            ("Card saved years ago", "under customer.sources"),
            ("Billing code rewritten", "reads payment_methods"),
            ("List comes back empty", "the card is elsewhere"),
            ("Renewal fails", "no active card"),
            ("Support says re-enter", "customer churns instead"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "slcs-f",
        "Sorting customers by which store holds the card and which default is set",
        "Cards in both stores with no default_payment_method still renew on the "
        "legacy card, because Billing falls back to default_source.",
        ("sources plus payment_methods", "and both default fields"),
        [
            ("PaymentMethod and modern default", "migrated", "good"),
            ("legacy only, default_source set", "modern code sees no card", "bad"),
            ("both, no modern default", "renews on the old card", "bad"),
            ("both, modern default set", "residue, safe to remove", "plain"),
            ("neither store has a card", "ask, do not migrate", "bad"),
        ],
    ),
}

V["stripe/expired-manual-capture-holds"] = {
    "flow_intro": (
        "The script expands the charge, because the deadline lives there, and "
        "sorts by time remaining rather than by age: two holds authorized the "
        "same minute can expire days apart."
    ),
    "diagram_problem": D.chain(
        "smch-p",
        "An authorization expiring while the order waits to be dispatched",
        "No payment fails and no event fires, so the order table still reads "
        "authorized long after the hold has gone.",
        [
            ("Checkout authorizes", "capture_method manual"),
            ("Capture job waits", "fixed 7 day timer"),
            ("Window is shorter", "capture_before passes"),
            ("Stripe cancels", "reason automatic"),
            ("Capture returns 400", "charge_expired_for_capture"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "smch-f",
        "Sorting holds by the deadline the network gave them",
        "A missing capture_before is unknown, not safe. Defaulting it to seven "
        "days clears the card present holds whose window is two.",
        ("requires_capture intents", "latest_charge expanded"),
        [
            ("days left", "held, nothing to do yet", "good"),
            ("under 48 hours", "capture now, soonest first", "bad"),
            ("deadline passed", "hold gone, status may lag", "bad"),
            ("canceled, reason automatic", "already lost, count it", "bad"),
            ("no capture_before", "unknown, expand the charge", "plain"),
        ],
    ),
}

V["stripe/bank-debit-intents-stuck-processing"] = {
    "flow_intro": (
        "The script compares each processing intent against the settlement "
        "window of its own payment method, because one threshold flags healthy "
        "SEPA and misses stuck ACH at the same time."
    ),
    "diagram_problem": D.chain(
        "sbdp-p",
        "A bank debit parked in processing because nothing ever asks again",
        "Processing is where an ACH payment is supposed to sit, so there is no "
        "wrong looking value anywhere to alert on.",
        [
            ("Customer pays by ACH", "intent goes processing"),
            ("Checkout checks once", "not succeeded yet"),
            ("No endpoint subscribed", "result never arrives"),
            ("Bank settles days later", "nobody is listening"),
            ("Order never ships", "customer asks weeks on"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sbdp-f",
        "Sorting processing intents against their own settlement window",
        "Age is the only thing separating a slow debit from a dead one, so the "
        "check is arithmetic rather than a status read.",
        ("status processing", "plus payment_method_types and created"),
        [
            ("inside the window", "settling normally", "good"),
            ("past the window", "stuck, chase the mandate", "bad"),
            ("over 30 days", "cancelling no longer permitted", "bad"),
            ("card, over a day", "confirmation never finished", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
