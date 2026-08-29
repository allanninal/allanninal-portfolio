#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch O.

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

V["stripe/transfers-capability-inactive"] = {
    "flow_intro": (
        "The script reads the capability status off the account list, then fetches "
        "the capability itself for anything that is not active, because the status "
        "says what is wrong and only the capability object says why."
    ),
    "diagram_problem": D.chain(
        "stci-p",
        "An inactive transfers capability failing every attempt to move funds",
        "The account passes every check built around charges_enabled, because "
        "taking a payment and paying a seller are two separate permissions.",
        [
            ("Seller onboards", "charges_enabled true"),
            ("Transfers unverified", "capability inactive"),
            ("Payments succeed", "money reaches the platform"),
            ("Transfer rejected", "400 on every attempt"),
            ("Balance never moves", "seller asks where it is"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "stci-f",
        "Sorting the transfers capability by the status Stripe reports for it",
        "An absent capability key is a state of its own. Nothing is outstanding, "
        "so no onboarding link will ever change it.",
        ("GET /v1/accounts", "then the capability object"),
        [
            ("active", "funds can move", "good"),
            ("pending", "being verified, nothing to collect", "plain"),
            ("inactive with fields", "collect the union of currently_due", "bad"),
            ("key absent", "never requested, request it", "bad"),
        ],
    ),
}

V["stripe/payout-schedule-left-on-manual"] = {
    "flow_intro": (
        "The script reads the schedule off every account, then spends two extra "
        "GETs only where the interval is manual, because a balance and the age of "
        "the last payout are what separate a deliberate setting from stuck money."
    ),
    "diagram_problem": D.chain(
        "spsm-p",
        "A manual payout schedule leaving a connected account balance stranded",
        "Nothing here is a fault state, so no requirement, no event and no red "
        "field ever appears.",
        [
            ("Platform default set", "manual, during a hold phase"),
            ("Seller inherits it", "new account, same setting"),
            ("Payout job never written", "nothing creates payouts"),
            ("Balance climbs", "no failures to find"),
            ("Ticket months later", "where is my money"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "spsm-f",
        "Sorting connected accounts by payout schedule and by money actually held",
        "Manual on an empty account is a question. Manual on an account holding "
        "money with no recent payout is a support ticket.",
        ("settings.payouts.schedule", "plus balance and last payout"),
        [
            ("automatic interval", "scheduled, leave it", "good"),
            ("manual, nothing available", "no money is stuck yet", "plain"),
            ("manual, recent payout", "a job is running", "plain"),
            ("manual, money, no payout", "stranded, decide deliberately", "bad"),
            ("large delay_days", "working, and far out", "bad"),
        ],
    ),
}

V["stripe/onboarding-abandoned-details-not-submitted"] = {
    "flow_intro": (
        "The script pairs details_submitted with the age of the account, because "
        "an unsubmitted account is a normal signup for a week and a lost one "
        "afterwards."
    ),
    "diagram_problem": D.chain(
        "soad-p",
        "An expired account link leaving onboarding at details_submitted false",
        "The link is valid for minutes and can be used once, so the client that "
        "previews it spends it before the human clicks.",
        [
            ("Account link created", "single use, minutes long"),
            ("Link emailed", "client fetches a preview"),
            ("User clicks", "link already spent"),
            ("refresh_url is static", "error page, no new link"),
            ("Account never opens", "details_submitted false"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "soad-f",
        "Sorting unsubmitted accounts by age and by how many fields remain",
        "The length of currently_due is triage order, not a status. A short list "
        "is somebody who nearly finished.",
        ("details_submitted false", "plus created, plus currently_due"),
        [
            ("under 7 days old", "still signing up, do not chase", "plain"),
            ("aged, few fields left", "fresh link and an email", "bad"),
            ("aged, most fields left", "never worked through", "bad"),
            ("aged, nothing due", "no capability requested", "bad"),
        ],
    ),
}

V["stripe/verification-errors-unread"] = {
    "flow_intro": (
        "The script reads requirements.errors from every place it hides, then maps "
        "each code to one instruction, and reports an unrecognised code rather than "
        "swallowing it."
    ),
    "diagram_problem": D.chain(
        "svue-p",
        "An unread verification error code producing an endless upload loop",
        "The same file resubmitted fails automatically, so the natural response is "
        "guaranteed to fail again.",
        [
            ("Document uploaded", "request returns 200"),
            ("Stripe rejects it", "code in requirements.errors"),
            ("UI says pending", "the array is never read"),
            ("Seller resubmits", "the identical file"),
            ("Duplicate auto fails", "loop starts again"),
        ],
        fail_at=2,
        loop=(4, 3, "the same file cannot pass"),
    ),
    "diagram_fix": D.branch(
        "svue-f",
        "Mapping a verification error code to the one thing that resolves it",
        "A new photo fixes a greyscale scan and never fixes a keyed identity "
        "mismatch. An unknown code has to surface, not vanish.",
        ("requirements.errors", "account, person and capability"),
        [
            ("empty array", "clear", "good"),
            ("document code", "a different capture, in colour", "bad"),
            ("keyed identity", "correct the typed fields", "bad"),
            ("invalid_url_website_*", "fix the site, flip the url", "bad"),
            ("code not in the table", "unmapped, show the reason", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
