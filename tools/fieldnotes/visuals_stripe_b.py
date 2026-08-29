#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch B.

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

V["stripe/undelivered-events-nearing-retention"] = {
    "flow_intro": (
        "The script pages every undelivered event to the very last page, because "
        "Stripe returns them newest first and the only number that matters is the "
        "age of the oldest one."
    ),
    "diagram_problem": D.chain(
        "sern-p",
        "Undelivered events aging out of the 30 day retention window",
        "The handler is fixed long before the replay is written, and the oldest "
        "events leave the API while the backfill is still being discussed.",
        [
            ("Delivery fails", "handler returns 500"),
            ("Retries stop", "after 3 days"),
            ("Outage found", "on day 21"),
            ("Replay written", "on day 27"),
            ("Oldest gone", "past 30 days"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sern-f",
        "Sorting an undelivered backlog by the age of its oldest event",
        "The count says how much work the replay is. The age of the oldest event "
        "says whether there is still time to do it properly.",
        ("GET /v1/events", "delivery_success=false, paginated"),
        [
            ("Nothing undelivered", "clear, no deadline", "good"),
            ("Oldest under 20 days", "replay carefully", "plain"),
            ("Oldest over 20 days", "schedule the replay now", "bad"),
            ("Oldest over 29 days", "gone tomorrow, replay first", "bad"),
        ],
    ),
}

V["stripe/wildcard-enabled-events"] = {
    "flow_intro": (
        "The script reads what each endpoint is subscribed to, then tallies what "
        "actually fires, so the traffic you are paying for and discarding becomes a "
        "number rather than a suspicion."
    ),
    "diagram_problem": D.chain(
        "swe-p",
        "A wildcard subscription flooding a handler that branches on four types",
        "Every event costs a request, a signature check and a parse before the "
        "handler can decide it does not care.",
        [
            ("enabled_events = *", "set once, never revisited"),
            ("Stripe delivers all", "every type generated"),
            ("Signature verified", "full cost per event"),
            ("No matching branch", "work discarded"),
            ("Timeout at renewals", "retries add load"),
        ],
        fail_at=3,
        loop=(4, 1, "retries multiply the flood"),
    ),
    "diagram_fix": D.branch(
        "swe-f",
        "Sorting webhook subscriptions by how closely they match the handler",
        "A hand typed list of sixty types is a wildcard that no check looking only "
        "for a star will ever find.",
        ("GET /v1/webhook_endpoints", "plus a tally of /v1/events"),
        [
            ("Matches the handler", "focused, leave it", "good"),
            ("Types that never fire", "trim to the branches", "bad"),
            ("Over 40 explicit types", "a wildcard typed out", "bad"),
            ("Contains a star", "subscribe explicitly", "bad"),
        ],
    ),
}

V["stripe/duplicate-endpoints-same-url"] = {
    "flow_intro": (
        "The script normalises every endpoint URL before grouping, because the query "
        "parameter Stripe tells you to add during a version upgrade is exactly what "
        "makes the duplicate look like a different destination."
    ),
    "diagram_problem": D.chain(
        "sdes-p",
        "Two enabled webhook endpoints on one URL delivering every event twice",
        "Both deliveries carry a valid signature, because each endpoint signs with "
        "its own secret.",
        [
            ("Version upgrade", "second endpoint created"),
            ("Old one left enabled", "retirement ticket skipped"),
            ("Both deliver", "same URL, two secrets"),
            ("Both verify", "no error anywhere"),
            ("Handler runs twice", "duplicate orders"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sdes-f",
        "Grouping webhook endpoints by normalised URL and delivery mode",
        "Only enabled endpoints in the same mode count. A disabled sibling is "
        "untidy, not a duplicate.",
        ("GET /v1/webhook_endpoints", "grouped by mode and stripped URL"),
        [
            ("One enabled endpoint", "unique, leave it", "good"),
            ("Enabled plus disabled", "residue, tidy later", "plain"),
            ("Two or more enabled", "disable one, add idempotency", "bad"),
        ],
    ),
}

V["stripe/missing-payout-failed"] = {
    "flow_intro": (
        "The script unions the subscribed event types across every endpoint, then "
        "asks whether any payout has already failed, because those two facts "
        "together separate a coverage gap from a live incident."
    ),
    "diagram_problem": D.chain(
        "smpf-p",
        "A failed payout going unnoticed because payout.failed is unsubscribed",
        "The external account is disabled by the first failure, so every later "
        "payout is blocked rather than merely late.",
        [
            ("Bank details go stale", "account closed"),
            ("Payout fails", "status failed"),
            ("No subscription", "event never delivered"),
            ("External account off", "further payouts blocked"),
            ("Found days later", "by the missing money"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "smpf-f",
        "Sorting payout failure coverage by subscription and by failures seen",
        "The same missing subscription is a ticket on a clean account and a page on "
        "one that has already lost a payout.",
        ("Union of enabled_events", "plus GET /v1/payouts?status=failed"),
        [
            ("paid and failed subscribed", "covered", "good"),
            ("only failed subscribed", "add payout.paid", "plain"),
            ("unsubscribed, no failures", "a gap to close", "bad"),
            ("unsubscribed, failures seen", "an incident already running", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
