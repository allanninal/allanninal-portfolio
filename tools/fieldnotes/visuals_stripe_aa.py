#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch AA.

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

V["stripe/uncaptured-charge-expiry-refunds"] = {
    "flow_intro": (
        "The script starts from the refunds rather than the charges, because the "
        "reason code that separates a returned payment from a released hold only "
        "exists on the refund, and then it goes to the charge for the proof."
    ),
    "diagram_problem": D.chain(
        "sucer-p",
        "An expired authorization becoming a refund inside a customer metric",
        "Nobody issued it and no money was ever collected, but it lands in the "
        "same table the refund rate is computed from.",
        [
            ("Hold authorized", "capture deferred"),
            ("Window closes", "no capture made"),
            ("Stripe writes refund", "reason set by Stripe"),
            ("Report sums it", "no grouping by reason"),
            ("Blamed on product", "refund rate up"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sucer-f",
        "Sorting refunds by reason and by what the charge says about capture",
        "The reason names the candidate. Only captured=false on the charge turns "
        "it into something you can put in a ticket.",
        ("GET /v1/refunds", "then GET /v1/charges/{id}"),
        [
            ("Customer reason", "a real refund, keep it", "good"),
            ("No reason recorded", "counts until proven otherwise", "plain"),
            ("Expired, charge unread", "a candidate, not evidence", "plain"),
            ("Expired, captured false", "confirmed, split it out", "bad"),
        ],
    ),
}

V["stripe/elevated-risk-charges-no-review"] = {
    "flow_intro": (
        "The script reads the risk score Radar wrote on every charge and asks what "
        "happened next, because the score and the outcome are on the same object "
        "and nothing in an order pipeline ever looks at either."
    ),
    "diagram_problem": D.chain(
        "selnr-p",
        "An elevated risk score captured with no review rule in front of it",
        "The default rules block the highest band and leave this one alone, so "
        "the absence of a review rule is the whole failure.",
        [
            ("Radar scores it", "risk_level elevated"),
            ("No review rule", "nothing to match"),
            ("Authorized", "review stays null"),
            ("Captured, shipped", "score never read"),
            ("Dispute arrives", "six weeks later"),
        ],
        fail_at=0,
        loop=(4, 0, "chargeback ratio climbs"),
    ),
    "diagram_fix": D.branch(
        "selnr-f",
        "Sorting elevated risk charges by what stopped them, if anything did",
        "An empty review queue looks the same whether the traffic is clean or "
        "the rule was never written.",
        ("GET /v1/charges", "risk_level, review, captured"),
        [
            ("Radar not_assessed", "no session, fix that first", "bad"),
            ("Stopped before capture", "a rule held", "good"),
            ("Placed in review", "a human saw it", "good"),
            ("Captured, review null", "write the review rule", "bad"),
        ],
    ),
}

V["stripe/incomplete-expired-signup-leak"] = {
    "flow_intro": (
        "The script counts two statuses over one identical window and divides, "
        "because the same number of expired signups is background noise on one "
        "account and a month long outage on another."
    ),
    "diagram_problem": D.chain(
        "siesl-p",
        "A signup expiring because the first invoice was never confirmed",
        "The create call returned 200 and the analytics event fired, so every "
        "signal except the money says this worked.",
        [
            ("Subscription created", "server side, 200 OK"),
            ("Client never confirms", "no payment attempted"),
            ("Invoice unpaid", "status incomplete"),
            ("Window closes", "incomplete_expired"),
            ("Invoice voided", "terminal, no revival"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "siesl-f",
        "Judging a window of signups by the share that never confirmed",
        "The count says nothing on its own. Only the ratio against activations "
        "separates abandonment from a broken checkout.",
        ("Two paginated counts", "expired against active"),
        [
            ("Nothing expired", "clean", "good"),
            ("Under 10 percent", "ordinary abandonment", "plain"),
            ("10 percent or more", "a slice cannot confirm", "bad"),
            ("No activations at all", "broken for everyone", "bad"),
        ],
    ),
}

V["stripe/sca-authentication-stuck-subscriptions"] = {
    "flow_intro": (
        "The script reads down to the PaymentIntent behind the first invoice and "
        "handles both field layouts, because a lookup that only knows one of them "
        "reports the whole account as unreadable and that reads like good news."
    ),
    "diagram_problem": D.chain(
        "sscas-p",
        "A bank challenge that was never shown freezing a subscription",
        "The issuer did not refuse the payment. It asked a question, and the "
        "customer was never given the screen to answer it on.",
        [
            ("First invoice", "payment attempted"),
            ("Issuer wants 3DS", "requires_action"),
            ("Client shows spinner", "no challenge rendered"),
            ("Invoice stays open", "subscription incomplete"),
            ("Retries do nothing", "hard decline"),
        ],
        fail_at=1,
        loop=(4, 3, "scheduled, never clears"),
    ),
    "diagram_fix": D.branch(
        "sscas-f",
        "Sorting incomplete subscriptions by the intent behind the first invoice",
        "Both a declined card and an unanswered challenge leave the subscription "
        "incomplete, and only one of them is still collectable.",
        ("GET /v1/subscriptions", "expanded to the intent"),
        [
            ("requires_action", "challenge never shown", "bad"),
            ("No next_action", "nothing to complete", "bad"),
            ("requires_payment_method", "a decline, send a card link", "plain"),
            ("Nothing expanded", "wrong shape for the version", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
