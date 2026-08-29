#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch Y.

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

V["stripe/inquiry-needs-response-ignored"] = {
    "flow_intro": (
        "The script pages the disputes list with no status filter at all, because "
        "a server side filter on needs_response is the exact mistake it exists to "
        "find, and then splits the results locally on the escalation line."
    ),
    "diagram_problem": D.chain(
        "sinqr-p",
        "An inquiry escalating into a chargeback while the alerting looks elsewhere",
        "Nothing failed. The event arrived, the handler ran, and the branch that "
        "would have paged someone was never written.",
        [
            ("Issuer asks", "status warning_needs_response"),
            ("Event delivered", "charge.dispute.created"),
            ("Handler ignores it", "matches needs_response only"),
            ("due_by passes", "no evidence sent"),
            ("Chargeback filed", "funds, fee and a ratio entry"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sinqr-f",
        "Sorting disputes by which side of the escalation line they sit on",
        "Staged evidence is not submitted evidence. Only submission_count says "
        "the response reached the issuer.",
        ("GET /v1/disputes", "unfiltered, split on the status prefix"),
        [
            ("warning_closed", "resolved before escalating", "good"),
            ("warning_under_review", "answered, waiting", "good"),
            ("warning_needs_response", "answer it, the window is open", "bad"),
            ("evidence staged, 0 sent", "the work is done, send it", "bad"),
            ("needs_response or later", "already a chargeback", "plain"),
        ],
    ),
}

V["stripe/dispute-rate-above-threshold"] = {
    "flow_intro": (
        "The script counts three lists over one calendar month and refuses to "
        "print a ratio it could not count in full, because a denominator that "
        "stopped paginating early reads high and would be believed."
    ),
    "diagram_problem": D.chain(
        "sdrat-p",
        "A dispute ratio crossing a network threshold with nobody computing it",
        "Each dispute is handled on its own terms and closed. The quotient "
        "between them belongs to no team.",
        [
            ("Disputes handled", "one at a time"),
            ("Nobody divides", "no monthly ratio"),
            ("Ratio drifts up", "past 0.5 percent"),
            ("Threshold crossed", "0.75 and then 1.5"),
            ("Programme letter", "fines and a remediation plan"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sdrat-f",
        "Sorting a month of dispute activity against the card network thresholds",
        "The count floors matter as much as the ratio. A high percentage on three "
        "events is a signal, not a breach.",
        ("Disputes plus warnings", "over successful captured charges"),
        [
            ("Under 0.5 percent", "clear for the month", "good"),
            ("Few countable events", "below the programme floors", "plain"),
            ("0.5 to 0.75 percent", "the month to act in", "bad"),
            ("Over 0.75 percent", "excessive by industry practice", "bad"),
            ("Over 1.5 percent", "VAMP excessive and ECM range", "bad"),
        ],
    ),
}

V["stripe/efw-actionable-not-refunded"] = {
    "flow_intro": (
        "The script trusts the actionable flag to narrow the set, then spends one "
        "request per warning on the charge itself, because the refund state that "
        "decides everything lives on the charge and not on the warning."
    ),
    "diagram_problem": D.chain(
        "sefwa-p",
        "An actionable early fraud warning aging out into a fraud dispute",
        "The one moment in payments with advance notice attached, and nothing "
        "moves when it arrives so nothing raises an alarm.",
        [
            ("Issuer reports fraud", "warning created, actionable true"),
            ("No subscription", "nobody is told"),
            ("Goods ship", "money still captured"),
            ("Window closes", "warning stops being actionable"),
            ("Dispute filed", "fee, funds and a second ratio entry"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sefwa-f",
        "Sorting early fraud warnings by the refund state of the charge they name",
        "A partial refund leaves the warning actionable. Comparing "
        "amount_refunded against zero rather than against amount reports a clean "
        "account that is not.",
        ("Actionable warnings", "joined to GET /v1/charges/{id}"),
        [
            ("Fully refunded", "closed before escalating", "good"),
            ("Already disputed", "past the window, count the fee", "plain"),
            ("Partly refunded", "still open, finish it", "bad"),
            ("Untouched", "refund now, oldest first", "bad"),
        ],
    ),
}

V["stripe/no-3ds-on-elevated-risk"] = {
    "flow_intro": (
        "The script reads the parent object before the result, because "
        "three_d_secure is absent rather than false when nothing authenticated, "
        "and the null guard added to stop the exception is what hides the finding."
    ),
    "diagram_problem": D.chain(
        "s3dse-p",
        "An elevated risk charge captured unauthenticated and disputed later",
        "Radar scored it and 3D Secure never ran, because risk scoring and "
        "authentication are separate systems with nothing joining them.",
        [
            ("Radar scores elevated", "outcome.risk_level set"),
            ("No request rule", "3DS never triggered"),
            ("Charge captured", "three_d_secure null"),
            ("Fraud dispute filed", "no liability shift to invoke"),
            ("Lost on response", "the loss stays with you"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "s3dse-f",
        "Sorting card charges by risk level against their authentication result",
        "Attempted is not authenticated. Counting any non null three_d_secure as "
        "covered overstates the share the card networks also compute.",
        ("GET /v1/charges", "card charges that succeeded"),
        [
            ("Authenticated", "liability sits with the issuer", "good"),
            ("Normal risk, no 3DS", "ordinary, counts in the share", "plain"),
            ("Attempt acknowledged", "looks covered and is not", "bad"),
            ("Elevated risk, no 3DS", "add the Radar request rule", "bad"),
            ("Share at or under 10 percent", "Mastercard monitoring range", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
