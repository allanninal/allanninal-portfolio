#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch H.

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

V["stripe/endpoint-api-version-pinned-stale"] = {
    "flow_intro": (
        "The script reads one field per endpoint and trims it to its date prefix "
        "before comparing, because the two ways to get this wrong are both string "
        "handling: an empty version read as a pin, and a release name compared as "
        "though it were part of the date."
    ),
    "diagram_problem": D.chain(
        "seavp-p",
        "A webhook endpoint pinned to an old api_version deserializing to nothing",
        "Verification passes first, so every log line looks healthy right up to "
        "the point where the object turns out to be empty.",
        [
            ("Endpoint created", "api_version pinned"),
            ("Account upgraded", "the pin does not move"),
            ("Event delivered", "rendered at the old version"),
            ("Signature verifies", "raw bytes are valid"),
            ("Object empty", "no exception thrown"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "seavp-f",
        "Sorting webhook endpoints by the API version they render events at",
        "Unpinned is a different risk, not a smaller one. It follows the account "
        "default, so an upgrade changes these payloads too.",
        ("GET /v1/webhook_endpoints", "api_version, date prefix only"),
        [
            ("On the current line", "matches the SDK", "good"),
            ("Null or empty string", "unpinned, follows the account", "plain"),
            ("Behind the current line", "read the changelog", "bad"),
            ("Before 2024-09-30", "migrate to a new endpoint", "bad"),
        ],
    ),
}

V["stripe/missing-idempotency-keys-on-payments"] = {
    "flow_intro": (
        "The script reads the request that caused each event, and separates your "
        "API calls from the ones Stripe made on your behalf, because only the first "
        "group could ever have carried a key."
    ),
    "diagram_problem": D.chain(
        "smik-p",
        "A charge created twice because the request carried no idempotency key",
        "The charge succeeded the first time. Only the response was lost, and "
        "nothing in the retry can tell Stripe it is the same operation.",
        [
            ("Checkout submits", "no Idempotency-Key"),
            ("Stripe charges", "the card is debited"),
            ("Response lost", "mobile network drops"),
            ("Client retries", "same parameters"),
            ("Charged twice", "a refund and an apology"),
        ],
        fail_at=2,
        loop=(4, 1, "every retry is a new charge"),
    ),
    "diagram_fix": D.branch(
        "smik-f",
        "Sorting events by whether the request that caused them carried a key",
        "Stripe initiated events have a null request id, and on a billing account "
        "they outnumber everything else.",
        ("GET /v1/events", "request.id and request.idempotency_key"),
        [
            ("Null request id", "Stripe did it, not you", "plain"),
            ("Key present", "a retry replays the result", "good"),
            ("No key, customer created", "duplicate records", "bad"),
            ("No key, money moving", "duplicate charges", "bad"),
        ],
    ),
}

V["stripe/dead-or-rejected-enabled-events"] = {
    "flow_intro": (
        "The script tallies what actually fires before it judges any subscription, "
        "because silence proves decay only for the legacy families. Everywhere else "
        "silence is just low volume."
    ),
    "diagram_problem": D.chain(
        "sdret-p",
        "A subscribed event type that stopped firing and a handler branch gone dead",
        "Nothing errors at any point. A branch that never runs writes no logs, so "
        "the feature it drove disappears without a trace.",
        [
            ("Sources to PaymentMethods", "integration migrated"),
            ("Type stops firing", "still valid, never occurs"),
            ("Branch never runs", "no logs, no errors"),
            ("Reminders stop", "nobody notices"),
            ("Next update fails", "the array is re-sent whole"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sdret-f",
        "Sorting subscribed event types by whether they still fire and still exist",
        "Zero disputes in thirty days is a good month. Only the Sources families "
        "can be judged by an absence.",
        ("enabled_events", "diffed against a tally of /v1/events"),
        [
            ("Seen firing", "live, leave it", "good"),
            ("Quiet, current type", "low volume, not decay", "plain"),
            ("Sources type, silent", "dead branch, remove it", "bad"),
            ("Removed from the API", "poisons every update", "bad"),
        ],
    ),
}

V["stripe/expired-saved-cards-attached"] = {
    "flow_intro": (
        "The script compares the expiry month against today and asks separately "
        "whether the card is a billing default, because a stale card beside three "
        "working ones is untidy and the same card on a renewal is lost revenue."
    ),
    "diagram_problem": D.chain(
        "sesc-p",
        "A saved card expiring in place and taking the subscription with it",
        "The automatic card updater covers many US issuers and no field tells you "
        "which cards it will reach.",
        [
            ("Card saved", "exp_month and exp_year known"),
            ("Updater misses it", "coverage varies by issuer"),
            ("Expires in place", "still attached, still shown"),
            ("Renewal declines", "expired_card"),
            ("Dunning fails", "involuntary churn"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sesc-f",
        "Sorting saved cards by expiry against today and by billing default status",
        "A card is valid through the end of its expiry month, so the current month "
        "is a warning rather than a failure.",
        ("GET /v1/payment_methods", "type=card, exp_month and exp_year"),
        [
            ("Expires later", "nothing to do", "good"),
            ("Expires this month", "nudge now, it still works", "plain"),
            ("Expired, not default", "detach the dead card", "bad"),
            ("Expired and default", "the next renewal fails", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
