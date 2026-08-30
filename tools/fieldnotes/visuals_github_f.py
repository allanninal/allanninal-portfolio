#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch F.

Four notes about spending less rather than about being broken, so none of these
problem chains ends at an error. They end at a number: an hour of wall clock, a
spike on the hour, 4,320 requests to notice something fifteen seconds late, 720
polls that return the page you already had. The failing step in each chain is
therefore the moment the cost is incurred, not the moment something breaks.

Each fix branch sorts on a different signal, which is the whole point of the
batch: a bucket row, a pair of status codes under two credentials, a hook
inventory, and one response header. Drawn in GitHub blue.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/code-search-bucket-exhausted"] = {
    "flow_intro": (
        "The script reads the whole resources table rather than the one row "
        "everybody checks, then costs the scan twice: once as the loop that is "
        "running and once as the qualified query that would replace it. The "
        "gap between those two numbers is the finding, and it is measured in "
        "minutes rather than in requests."
    ),
    "diagram_problem": D.chain(
        "ghcsb-p",
        "A per repository code search loop emptying a ten a minute bucket",
        "Nothing in this chain is an error. The scan finishes, with fewer hits "
        "than there are, and nobody sees the difference.",
        [
            ("Loop over 600 repos", "one search each"),
            ("Ten a minute gone", "spent in seconds"),
            ("403 on the eleventh", "core untouched"),
            ("Core row checked", "4,987 remaining"),
            ("Partial scan returned", "reads as fewer hits"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghcsb-f",
        "Reading every row of the rate limit table before blaming the quota",
        "code_search, search and core are independent rows. Spending one of "
        "them does not move the others, which is why the healthy number is so "
        "convincing and so useless.",
        ("GET /rate_limit", "every row, not just core"),
        [
            ("code_search at zero", "own bucket, own minute clock", "bad"),
            ("Loop dwarfs the query", "collapse into one org query", "bad"),
            ("Row not reported at all", "documented default applies", "plain"),
            ("Fits inside one minute", "nothing to change", "good"),
        ],
    ),
}

V["github/etag-invalidated-by-token-rotation"] = {
    "flow_intro": (
        "Three requests settle it. Fetch once and keep the etag, replay it with "
        "the credential that minted it as a control, then replay the same etag "
        "with a second credential. The third answer is the whole note, and it "
        "arrives in a second rather than in an hour."
    ),
    "diagram_problem": D.chain(
        "ghrot-p",
        "An hourly token rotation refetching an entire cache at full price",
        "The cache works. It works for fifty nine minutes, and the minute it "
        "does not is the one on the graph.",
        [
            ("Poll 2,000 urls", "etags keyed by url"),
            ("304 all the way", "quota near flat"),
            ("Token expires", "a new one is minted"),
            ("Every etag misses", "2,000 full bodies"),
            ("Read as an incident", "nothing had changed"),
        ],
        fail_at=2,
        loop=(4, 0, "every hour, on the hour"),
    ),
    "diagram_fix": D.branch(
        "ghrot-f",
        "Replaying one etag under two credentials to separate rotation from change",
        "A resource that genuinely changed answers 200 to both. Only a "
        "credential scoped validator answers 304 and 200 in the same second.",
        ("One etag, two tokens", "replayed back to back"),
        [
            ("304 then 200", "scoped to the credential", "bad"),
            ("200 to its own etag", "header stripped, or it changed", "bad"),
            ("304 then 304", "rotation is not the cause", "good"),
            ("No second credential", "a projection, not a measurement", "plain"),
        ],
    ),
}

V["github/polling-instead-of-webhooks"] = {
    "flow_intro": (
        "How often a client polls is invisible from the API, so the script "
        "checks the half that is readable: whether any active hook would push "
        "what the loop is reading. Then it costs the loop in latency as well "
        "as in requests, because the latency is the number that ends the "
        "argument."
    ),
    "diagram_problem": D.chain(
        "ghpush-p",
        "A polling loop paying for time rather than for activity",
        "A quiet repository costs exactly as much as a busy one, which is the "
        "part that never comes up when the interval is chosen.",
        [
            ("No hook configured", "nothing is pushed"),
            ("4,320 requests an hour", "six endpoints, 30 seconds"),
            ("Noticed 15s late", "half the interval"),
            ("Weekend costs the same", "no activity at all"),
            ("Label added and undone", "never seen at all"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "ghpush-f",
        "Sorting each polled concern by whether an active hook would push it",
        "A hook that exists is not a hook that delivers. Read events and "
        "active together, and treat anything else as absent.",
        ("Hook inventory", "events and active together"),
        [
            ("No hook for the event", "create one, name the events", "bad"),
            ("Hook there but inactive", "switch it on, do not duplicate", "bad"),
            ("Wildcard subscription", "delivers what you do not handle", "plain"),
            ("Active and specific", "poll becomes reconciliation", "good"),
        ],
    ),
}

V["github/poll-interval-header-ignored"] = {
    "flow_intro": (
        "One request, and the answer is in its headers. The script reports "
        "where the floor came from as well as what it is, because a number the "
        "server declared and a number the script assumed deserve different "
        "amounts of trust."
    ),
    "diagram_problem": D.chain(
        "ghpoll-p",
        "An events consumer polling under the floor the server declared",
        "Events do arrive. They simply arrive no sooner than they would have "
        "at a twelfth of the cost.",
        [
            ("x-poll-interval 60", "on every response"),
            ("720 polls an hour", "client sleeps 5s"),
            ("Same cached page", "feed not regenerated"),
            ("No If-None-Match", "each one billed in full"),
            ("Floor raised under load", "client speeds past it"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "ghpoll-f",
        "Comparing the configured interval against the declared floor",
        "Both directions are findings, and only one of them ever shows up on a "
        "quota graph.",
        ("Configured interval", "against the declared floor"),
        [
            ("Under the floor, no etag", "billable duplicates", "bad"),
            ("Far above the floor", "avoidable staleness", "bad"),
            ("Under it, with an etag", "free, and cannot help", "plain"),
            ("At the floor", "nothing to reclaim", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
