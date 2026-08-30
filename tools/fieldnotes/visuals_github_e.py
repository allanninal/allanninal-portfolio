#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch E.

Four rate-limit notes that sit next to each other in the index, so the diagrams
are the fastest way to show a reader they are not the same note. Each problem
chain fails at a different place for a different reason, and each fix branch
sorts on a different quantity: a drain against a window, a limit against a
control, a response time against two caps, and one bucket against another in
matching units. Drawn in GitHub blue.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built and restored at the bottom, because
# visuals.py imports every one of these modules in a single process and a theme
# left set would retint whichever section happened to be imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/rate-limit-core-exhausted"] = {
    "flow_intro": (
        "The script asks the one endpoint that does not charge for asking, then "
        "does arithmetic on three numbers. The window is a fixed hour, so reset "
        "minus 3,600 is when it opened, which turns a counter into a rate and a "
        "rate into a time of death."
    ),
    "diagram_problem": D.chain(
        "ghcore-p",
        "An hourly bucket spent in the first twelve minutes of the hour",
        "Nothing recovers until reset, and then everything does, which is how "
        "this gets closed as transient and recurs tomorrow.",
        [
            ("Window opens", "5,000 for the hour"),
            ("Backfill at 400 a minute", "no pacing anywhere"),
            ("Empty at minute 13", "remaining hits 0"),
            ("Every REST call 403s", "reads like an outage"),
            ("47 minutes of nothing", "then it fixes itself"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghcore-f",
        "Sorting a drain rate against the window that is left",
        "Two rates in the same units: what you are spending a minute, and what "
        "you can still afford a minute.",
        ("used, limit and reset", "one request, no charge"),
        [
            ("Drain over affordable", "names the minute it empties", "bad"),
            ("Now double the average", "a burst the average hides", "bad"),
            ("Past 80 percent used", "no room for a second consumer", "plain"),
            ("Drain fits the window", "nothing to change today", "good"),
        ],
    ),
}

V["github/rate-limit-unauthenticated"] = {
    "flow_intro": (
        "Nothing here is about quota. The script proves what GitHub thinks you "
        "are, by asking the same free endpoint twice, once with the header and "
        "once deliberately without it. Two numbers that agree are the proof "
        "that the header is not arriving."
    ),
    "diagram_problem": D.chain(
        "ghanon-p",
        "A token that never arrives and a server that serves you anyway",
        "An invalid token fails on request one. An absent token fails on "
        "request sixty-one, somewhere else entirely.",
        [
            ("Variable resolves empty", "set, but to nothing"),
            ("Header omitted", "client carries on"),
            ("Served anonymously", "200 with real data"),
            ("Request 61 refused", "403 names an IP"),
            ("Blamed on the runner", "shared egress address"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghanon-f",
        "Telling an absent token apart from a rejected one",
        "The control request carries no credentials on purpose. Without it you "
        "have one number and a theory.",
        ("Limit with and without the header", "plus GET /user"),
        [
            ("Both report 60", "the header is not arriving", "bad"),
            ("Variable unset or empty", "same symptom, different repair", "bad"),
            ("Sent, but /user says 401", "expired or stripped, not missing", "plain"),
            ("5,000 against a control of 60", "authenticated", "good"),
        ],
    ),
}

V["github/secondary-limit-points-per-minute"] = {
    "flow_intro": (
        "There is no bucket to read for a secondary limit, so the script builds "
        "the ceiling itself: time a few calls to one path, then divide 900 by "
        "the points per request and 90 by the mean seconds. The smaller answer "
        "is the rate that path will actually take."
    ),
    "diagram_problem": D.chain(
        "ghpts-p",
        "A slow endpoint throttled while the point counter looks healthy",
        "Only one path fails, which is why the search goes to permissions and "
        "repository size before it goes to cost.",
        [
            ("One expensive path", "0.6 s a call"),
            ("Loop runs flat out", "400 a minute"),
            ("CPU cap binds at 150", "points nowhere near 900"),
            ("403 on that path only", "everything else fine"),
            ("Retries refill the minute", "window re-arms"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghpts-f",
        "Two per-minute ceilings on one endpoint, and which of them binds",
        "The crossover sits at about a tenth of a second a call. Above it the "
        "ceiling keeps falling as the endpoint gets slower.",
        ("Mean response time on one path", "a few paced GETs"),
        [
            ("Under 0.1 s a call", "900 points a minute binds", "plain"),
            ("Over 0.1 s a call", "90s of CPU binds, and lower", "bad"),
            ("Configured rate above it", "surplus refused, not queued", "bad"),
            ("Rate under the ceiling", "spread across the minute", "good"),
        ],
    ),
}

V["github/search-bucket-exhausted"] = {
    "flow_intro": (
        "One free request returns every bucket at once, and the comparison only "
        "works after the windows are made to match: an hourly 5,000 is 83 a "
        "minute, against search at 30. Then the loop is costed and packed into "
        "the queries it should have been."
    ),
    "diagram_problem": D.chain(
        "ghsbkt-p",
        "A search per repository against a bucket that resets every minute",
        "The bucket refills in under a minute, so retrying by hand always "
        "works and the bug is filed as flaky.",
        [
            ("400 repositories", "one search in each"),
            ("30 in the first minute", "search bucket empty"),
            ("403 on searches only", "core barely touched"),
            ("Repo reads keep working", "looks like a query bug"),
            ("Manual retry succeeds", "closed as flaky"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghsbkt-f",
        "Comparing buckets in matching units and packing the loop away",
        "The allowance counts requests, not results, so a query naming twenty "
        "repositories costs exactly what a query naming one costs.",
        ("Every bucket, one free call", "normalised per minute"),
        [
            ("search is 30 a minute", "core is 83, so search binds", "bad"),
            ("code_search is 10", "tighter again, same document", "bad"),
            ("400 calls is 14 minutes", "370 refused in minute one", "bad"),
            ("19 packed queries", "256 characters each", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
