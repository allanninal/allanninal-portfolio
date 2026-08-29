#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch D: payments and intents.

Same two shapes as the rest of the site: the problem is a chain that breaks at one
step, the fix is a branch, because every script in this section classifies what it
finds rather than guessing. Drawn in Stripe indigo.

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

V["stripe/abandoned-requires-action-intents"] = {
    "flow_intro": (
        "The script reads every PaymentIntent in the window and asks one question of "
        "each: is it waiting on the customer's bank, and if so, for how long. The age "
        "separates a customer reading a prompt from a handoff that was never wired up."
    ),
    "diagram_problem": D.chain(
        "sara-p",
        "A PaymentIntent frozen at requires_action because the client never finished the handoff",
        "The authorization is never attempted, so there is no decline code and no "
        "failure event. The intent simply stops.",
        [
            ("Confirm called", "card needs 3DS"),
            ("requires_action", "next_action populated"),
            ("Client does nothing", "return_url is 404"),
            ("Customer leaves", "no error shown"),
            ("Intent frozen", "no money moves"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sara-f",
        "Sorting intents at the authentication step by age and next_action",
        "Only one of these three is a broken integration, and the other two would "
        "bury it if they were counted together.",
        ("GET /v1/payment_intents", "status and next_action, aged"),
        [
            ("Under 24 hours old", "in flight, leave it", "good"),
            ("Over 24 hours old", "handoff is broken", "bad"),
            ("Empty next_action", "client was never told", "bad"),
        ],
    ),
}

V["stripe/stale-requires-payment-method-intents"] = {
    "flow_intro": (
        "The script scans intents old enough to have a verdict and splits the open ones "
        "on a single field, last_payment_error, because that field is what separates a "
        "customer who never tried from a customer who tried and was turned down."
    ),
    "diagram_problem": D.chain(
        "ssrpm-p",
        "A PaymentIntent created on page load that nothing ever confirms",
        "Creating the intent before the customer acts makes the stale pile grow with "
        "traffic rather than with failures.",
        [
            ("Payment page loads", "intent created"),
            ("Visitor never pays", "no card entered"),
            ("requires_payment_method", "the birth status"),
            ("Nothing cancels it", "no expiry"),
            ("Stale forever", "reports drift"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "ssrpm-f",
        "Sorting open PaymentIntents into never attempted, declined, and unconfirmed",
        "Three buckets that share one status and need three different fixes.",
        ("GET /v1/payment_intents", "older than 7 days, open"),
        [
            ("No last_payment_error", "created on page load", "bad"),
            ("last_payment_error set", "no retry was offered", "bad"),
            ("requires_confirmation", "your server never confirmed", "bad"),
        ],
    ),
}

V["stripe/radar-blocked-payments-ignored"] = {
    "flow_intro": (
        "The script reads the outcome on every charge and keeps only the blocked ones, "
        "then groups them by reason and sums the amounts, because the cost of a rule is "
        "the number that settles what to do about it."
    ),
    "diagram_problem": D.chain(
        "srbp-p",
        "A charge stopped by a Radar rule before it ever reaches the issuer",
        "A block leaves no decline code anywhere, so the customer's bank has nothing "
        "to tell them when they call.",
        [
            ("Customer pays", "good card"),
            ("Radar evaluates", "an old rule matches"),
            ("Blocked", "not_sent_to_network"),
            ("Generic failure shown", "no reason given"),
            ("Revenue lost", "nobody reads outcome"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "srbp-f",
        "Sorting blocked charges by outcome.reason",
        "One of these three is Stripe working correctly, and treating it as fraud "
        "sends you to change rules that were never involved.",
        ("GET /v1/charges", "outcome.type is blocked"),
        [
            ("reason is rule", "narrow the rule you wrote", "bad"),
            ("highest_risk_level", "add a review threshold", "bad"),
            ("low probability of auth", "Adaptive Acceptance, leave it", "good"),
        ],
    ),
}

V["stripe/refunds-failed-or-stuck"] = {
    "flow_intro": (
        "The script reads 180 days of refunds and keeps the ones that never completed, "
        "grouped by failure reason and summed by amount, because that total is money "
        "debited from your balance that reached nobody."
    ),
    "diagram_problem": D.chain(
        "srfs-p",
        "A refund that fails days after it was created, with nothing listening",
        "The support ticket is closed and the ledger shows the debit, so only the "
        "customer knows the money never arrived.",
        [
            ("Refund created", "API returns 200"),
            ("Status goes failed", "card was closed"),
            ("No handler listening", "charge.refund.updated"),
            ("Customer waits", "told it was sent"),
            ("Dispute filed", "you pay twice"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "srfs-f",
        "Sorting refunds by status and age",
        "Failed and requires_action are not the same obligation: one is money you "
        "owe, the other is a message you owe.",
        ("GET /v1/refunds", "status, failure_reason, age"),
        [
            ("succeeded", "settled, nothing to do", "good"),
            ("failed", "open ticket, pay out of band", "bad"),
            ("pending over 10 days", "read pending_reason", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
