#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch L.

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

V["stripe/no-live-webhook-endpoints"] = {
    "flow_intro": (
        "The script counts the endpoints in this key's mode and the payment events "
        "in the same window, because an empty list is a non-event on an account "
        "with no traffic and an outage on one taking money."
    ),
    "diagram_problem": D.chain(
        "snlw-p",
        "A live account taking payments with no webhook endpoint registered",
        "The CLI listener was the only destination that ever existed, and it lives "
        "on a laptop rather than in the account.",
        [
            ("stripe listen", "ephemeral destination"),
            ("Handler verified", "against the CLI secret"),
            ("Shipped to live", "no endpoint created"),
            ("Payment succeeds", "nowhere to push"),
            ("Nothing runs", "no order, no email"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "snlw-f",
        "Sorting an account by whether a destination exists and whether it is needed",
        "The same empty list means different things on a quiet test account and on "
        "a live one with a month of payments behind it.",
        ("GET /v1/webhook_endpoints", "plus a count of payment events"),
        [
            ("Enabled and live", "covered", "good"),
            ("Enabled, test mode", "says nothing about live", "plain"),
            ("None, no traffic yet", "create before the first payment", "bad"),
            ("None, payments seen", "an outage already running", "bad"),
        ],
    ),
}

V["stripe/events-with-pending-webhooks"] = {
    "flow_intro": (
        "The script asks the API for events older than an hour, then counts the ones "
        "still waiting on a 2xx and tallies them by type, because the shape of the "
        "backlog is what names the cause."
    ),
    "diagram_problem": D.chain(
        "sepw-p",
        "A slow webhook handler losing a fraction of its events to timeouts",
        "The endpoint stays enabled the whole time, so nothing draws attention to "
        "the fraction that never lands.",
        [
            ("Event created", "pending_webhooks 1"),
            ("Handler works first", "answers after the job"),
            ("Timeout", "slow 200 is a failure"),
            ("Retry with backoff", "same slow path"),
            ("Order missing", "looks random"),
        ],
        fail_at=2,
        loop=(3, 1, "each retry repeats the slow work"),
    ),
    "diagram_fix": D.branch(
        "sepw-f",
        "Sorting a stuck event backlog by concentration and by share of the sample",
        "One type holding most of the backlog is a handler branch. An even spread "
        "across everything is the route itself.",
        ("GET /v1/events", "created[lt] now minus one hour"),
        [
            ("Nothing outstanding", "all delivered", "good"),
            ("One type dominates", "fix that branch", "bad"),
            ("Majority stuck", "timeout or a 3xx redirect", "bad"),
            ("Thin spread", "answer first, queue the work", "plain"),
        ],
    ),
}

V["stripe/missing-subscription-deleted"] = {
    "flow_intro": (
        "The script unions the subscribed types across every endpoint, then counts "
        "active and cancelled subscriptions, because the same missing type is noise "
        "on one account and a list of over entitled customers on another."
    ),
    "diagram_problem": D.chain(
        "smsd-p",
        "A cancelled subscription whose end is never delivered to the application",
        "The money side is entirely correct, which is why no report disagrees with "
        "the entitlement that is wrong.",
        [
            ("Customer cancels", "at period end"),
            ("Update delivered", "flag recorded"),
            ("Period ends", "subscription deleted"),
            ("Not subscribed", "event never sent"),
            ("Access continues", "found by a ticket"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "smsd-f",
        "Sorting entitlement coverage by subscription and by cancellations seen",
        "Cancellations already on the account turn a coverage gap into a backlog "
        "with names in it.",
        ("Union of enabled_events", "plus subscription counts"),
        [
            ("deleted and updated", "covered", "good"),
            ("deleted only", "no notice of scheduled ends", "plain"),
            ("missing, none ended", "a gap to close", "bad"),
            ("missing, cancellations", "accounts still entitled", "bad"),
        ],
    ),
}

V["stripe/missing-dispute-and-fraud-events"] = {
    "flow_intro": (
        "The script keeps the two signals apart rather than reporting one coverage "
        "flag, because a chargeback has a deadline and a fraud warning has a remedy, "
        "and only one of them is still cheap."
    ),
    "diagram_problem": D.chain(
        "smdf-p",
        "An early fraud warning arriving with no subscription to receive it",
        "The window in which a refund prevents the chargeback closes while the order "
        "is still being packed.",
        [
            ("Issuer flags card", "warning raised"),
            ("Not subscribed", "no event sent"),
            ("Order ships", "refund window gone"),
            ("Dispute filed", "deadline starts"),
            ("Found by email", "days already spent"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "smdf-f",
        "Sorting dispute and fraud coverage into two independent signals",
        "Hearing about chargebacks after they are filed is not the same as being "
        "covered, and collapsing the two hides the cheaper fix.",
        ("Union of enabled_events", "plus disputes and warnings"),
        [
            ("created, closed, warning", "covered", "good"),
            ("no closing event", "outcome never recorded", "plain"),
            ("disputes only", "no notice before filing", "bad"),
            ("neither subscribed", "deadlines found by email", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
