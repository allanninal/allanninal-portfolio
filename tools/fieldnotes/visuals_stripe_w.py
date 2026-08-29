#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch W.

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

V["stripe/endpoint-api-version-drift"] = {
    "flow_intro": (
        "The script collapses both spellings of unpinned onto one sentinel before "
        "it deduplicates, because two endpoints that simply follow the account "
        "default are one shape and not two."
    ),
    "diagram_problem": D.chain(
        "seavd-p",
        "An endpoint upgrade that created a second endpoint and never retired the first",
        "Every step is the documented procedure. The failure is the last one never "
        "being taken, and nothing anywhere is counting down to it.",
        [
            ("Upgrade planned", "api_version is immutable"),
            ("Second endpoint", "same url, new pin"),
            ("Both deliver", "two shapes on the wire"),
            ("Cutover skipped", "ticket closed early"),
            ("One service breaks", "on a moved field"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "seavd-f",
        "Sorting webhook endpoints by the set of versions they render at",
        "A shared url under two versions is a migration to finish. Two urls under "
        "two versions is a decision nobody made.",
        ("GET /v1/webhook_endpoints", "enabled only, null and empty merged"),
        [
            ("One version in use", "consistent, leave it", "good"),
            ("No enabled endpoints", "nothing is delivered", "plain"),
            ("Two versions, one url", "unfinished migration", "bad"),
            ("Two versions, two urls", "services disagree", "bad"),
        ],
    ),
}

V["stripe/account-default-api-version-stale"] = {
    "flow_intro": (
        "The script reads one response twice: the newest event for the version in "
        "force when it fired, and the Stripe-Version header for the version in "
        "force right now. Disagreement between them is itself the finding."
    ),
    "diagram_problem": D.chain(
        "sadav-p",
        "An account default fixed by the first request years ago and never moved",
        "No object reports the account default, so the one field that decides how "
        "Stripe renders everything is the one field nobody can read.",
        [
            ("First API call", "version fixed in 2021"),
            ("No auto advance", "it never moves"),
            ("Releases stack up", "each one breaking"),
            ("Docs example fails", "no such parameter"),
            ("Renewals old shape", "Stripe bills for you"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sadav-f",
        "Sorting an account default read from an event and from a response header",
        "An SDK sends its own Stripe-Version and gets it echoed back, so this "
        "reading only works from a client that sends none.",
        ("GET /v1/events?limit=1", "body and response header"),
        [
            ("Both agree, current", "nothing to do", "good"),
            ("Under a year behind", "one changelog to read", "plain"),
            ("Header differs", "upgraded or rolled back", "plain"),
            ("Over a year behind", "several changelogs", "bad"),
        ],
    ),
}

V["stripe/mixed-event-api-versions"] = {
    "flow_intro": (
        "The script counts transitions rather than versions, because one change of "
        "shape is an upgrade you can date and three changes are an upgrade that was "
        "rolled back inside the 72 hour window."
    ),
    "diagram_problem": D.chain(
        "smeav-p",
        "A backfill walking through a version boundary inside the retained events",
        "Stored events are rendered once and never re-rendered, so the API hands "
        "back two payload shapes for one event type and both are correct.",
        [
            ("Account upgraded", "default moves"),
            ("Events split", "old shape stays old"),
            ("Handler fine", "new events only"),
            ("Backfill runs", "reads 30 days"),
            ("Throws mid loop", "at one timestamp"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "smeav-f",
        "Sorting the retained event stream by how many times its version changed",
        "Whether the boundary reached a handler depends on the endpoint pin, not "
        "on the events, so the two reads answer different questions.",
        ("GET /v1/events paginated", "plus the endpoint pins"),
        [
            ("One version", "no boundary", "good"),
            ("One transition", "branch for 30 days", "bad"),
            ("Several transitions", "upgrade then rollback", "bad"),
            ("Any endpoint unpinned", "it reached the handler", "bad"),
        ],
    ),
}

V["stripe/idempotency-key-reuse-conflict"] = {
    "flow_intro": (
        "The script groups events by idempotency key and measures the spread "
        "between the first and the last, because the same reused key is a 409 "
        "inside 24 hours and a silent duplicate outside it."
    ),
    "diagram_problem": D.chain(
        "sikrc-p",
        "A key derived from a customer id protecting a retry today and nothing tomorrow",
        "Stripe prunes saved results after about 24 hours, which is the one "
        "timescale nobody tests a retry across.",
        [
            ("Key from cus_ id", "looks unique enough"),
            ("Retry at 10:00", "correctly replayed"),
            ("Key pruned", "after 24 hours"),
            ("Same key next day", "treated as brand new"),
            ("Second real charge", "no error returned"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sikrc-f",
        "Sorting idempotency keys by request count and by the gap between them",
        "One key on one request id is the key working. Two request ids means "
        "nothing was deduplicated and both requests really ran.",
        ("GET /v1/events paginated", "grouped by idempotency_key"),
        [
            ("One request, a uuid", "unique per operation", "good"),
            ("One request, derived", "it will collide", "plain"),
            ("Two requests, minutes", "409 in_use under load", "bad"),
            ("Two requests, a day", "pruned, duplicate made", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
