#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch D.

Four rate-limit problems that share one awkward shape: the number everyone
checks is healthy while the thing that refused the request is not measured
anywhere. Three are secondary limits, which publish no bucket at all, so every
problem chain here ends at a 403 that arrives with the quota untouched. The
fourth runs the other way: nothing fails, a counter simply climbs for answers
that said nothing changed. Drawn in GitHub blue.

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

V["github/secondary-limit-concurrency"] = {
    "flow_intro": (
        "The script measures the overlap of its own request spans rather than "
        "trusting the pool size, because the pool size is a ceiling and the "
        "overlap is what actually happened. Then it classifies any refusal on "
        "the one field that separates the two limits."
    ),
    "diagram_problem": D.chain(
        "ghconc-p",
        "A fan-out that borrows its concurrency from the length of a list",
        "Nothing in the code changed between the run that worked and the run "
        "that did not. The input grew.",
        [
            ("Loop becomes parallel", "one call per repo"),
            ("List grows to 600", "600 in flight"),
            ("Past 100 concurrent", "secondary limit fires"),
            ("403 on most calls", "quota untouched"),
            ("Partial result written", "nothing marks it short"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghconc-f",
        "Telling a secondary limit apart from the hourly quota on one field",
        "A refusal with headroom left did not come from the bucket those "
        "headers describe, whatever the message wording happens to be.",
        ("403 or 429 received", "read body and headers"),
        [
            ("Body names a secondary limit", "burst, not volume", "bad"),
            ("Headroom left, no wording", "still a secondary limit", "bad"),
            ("Remaining is 0", "hourly quota, wait for reset", "plain"),
            ("No rate headers at all", "permissions, not throttling", "plain"),
        ],
    ),
}

V["github/secondary-limit-content-creation"] = {
    "flow_intro": (
        "There is no bucket to read here, so the script reads the residue "
        "instead: the density of created_at timestamps for one account. A "
        "sliding minute and a sliding hour, per login, because the limit is "
        "charged per account and not per repository."
    ),
    "diagram_problem": D.chain(
        "ghburst-p",
        "A migration that stops at eighty items with the quota barely touched",
        "The eighty issues it did create are real, so restarting the job from "
        "the top creates them a second time.",
        [
            ("Import 2,400 issues", "as fast as it can"),
            ("80 in the first minute", "content limit reached"),
            ("Every write 403s", "retry-after attached"),
            ("Quota still reads 4,900", "wrong number checked"),
            ("Half applied, not resumable", "no record of where"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghburst-f",
        "Sorting each author by the densest minute and the densest hour",
        "Forty in a minute from forty people is triage. Forty from one login "
        "is a script that will be throttled the next time it runs.",
        ("created_at grouped by login", "two sliding windows"),
        [
            ("80 or more in a minute", "already throttled", "bad"),
            ("500 or more in an hour", "paced, still over", "bad"),
            ("Inside 80 percent", "one label call from it", "plain"),
            ("Well under both", "nothing to pace", "good"),
        ],
    ),
}

V["github/retry-after-ignored"] = {
    "flow_intro": (
        "Every decision in this script is a function of five header values and "
        "the current time, so the whole calculation is pure and a response "
        "captured during an incident can be costed afterwards, offline."
    ),
    "diagram_problem": D.chain(
        "ghretry-p",
        "A generic retry that sends its next request inside the penalty window",
        "The requests made while waiting are themselves burst behaviour, which "
        "is what a secondary limit is throttling.",
        [
            ("403 with retry-after 120", "the wait is stated"),
            ("Client keeps the status", "discards the headers"),
            ("Sleeps one second", "retries immediately"),
            ("120 refused requests", "window re-arms"),
            ("Eleven minutes gone", "job never recovers"),
        ],
        fail_at=1,
        loop=(3, 2, "retry, refuse, repeat"),
    ),
    "diagram_fix": D.branch(
        "ghretry-f",
        "Branching on the two headers before falling back to a guess",
        "retry-after has to win, because a secondary limit fires while the "
        "hourly bucket is healthy and its reset time means nothing here.",
        ("Throttled response", "headers read in order"),
        [
            ("retry-after present", "sleep exactly that", "good"),
            ("Remaining 0 plus reset", "sleep until reset", "good"),
            ("Neither header", "60s floor, then backoff", "plain"),
            ("Sleep one call only", "other workers refill it", "bad"),
        ],
    ),
}

V["github/no-conditional-requests"] = {
    "flow_intro": (
        "This is the one note in the section where the fix can be measured "
        "rather than argued for. Two requests, three header values, one "
        "subtraction: if the second call came back 304 and x-ratelimit-used "
        "did not move, the saving is a fact."
    ),
    "diagram_problem": D.chain(
        "ghetag-p",
        "A poll that pays full price for an answer saying nothing changed",
        "There is no error anywhere in this chain. The wasteful version and "
        "the cheap version return identical data.",
        [
            ("Poll 8 endpoints", "every 30 seconds"),
            ("etag arrives, discarded", "no If-None-Match sent"),
            ("200 with a full body", "billed in full"),
            ("960 requests an hour", "on unchanged data"),
            ("Quota gone by noon", "read as a rate incident"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghetag-f",
        "Measuring the saving from x-ratelimit-used on two requests",
        "A 200 answer to a conditional request is not a saving that failed. It "
        "is a header that did not arrive.",
        ("Same GET sent twice", "second one conditional"),
        [
            ("304 and used unchanged", "free, saving is exact", "good"),
            ("200 despite the header", "proxy stripped it", "bad"),
            ("304 but used moved", "another process shares the token", "bad"),
            ("No etag at all", "try if-modified-since", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
