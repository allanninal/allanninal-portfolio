#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch C.

Four webhook problems that share one shape: GitHub behaves exactly as
configured, the receiving side has no record of anything at all, and the only
witness is a resource nobody opens. So every problem chain ends in silence
rather than in an error, and every fix branch sorts what was found instead of
announcing a single verdict. Drawn in GitHub blue.

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

V["github/webhook-deliveries-failing"] = {
    "flow_intro": (
        "The script buckets deliveries by status code before it judges anything, "
        "because the code is the entire diagnosis: a timeout and a 502 and a "
        "silent connection failure are three different repairs wearing one "
        "number called failures."
    ),
    "diagram_problem": D.chain(
        "ghdlv-p",
        "An event delivered, refused by a proxy, and recorded only on GitHub's side",
        "Nothing in this chain reaches the code that writes your logs, so the "
        "integration looks idle rather than broken.",
        [
            ("Pull request opened", "event generated"),
            ("Hook delivers", "POST to your URL"),
            ("Proxy answers 502", "handler never runs"),
            ("GitHub logs it", "status_code 502"),
            ("Nobody opens the log", "no alert exists"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghdlv-f",
        "Sorting a hook's deliveries by what the response actually was",
        "Failures that all predate the last success are a backfill, not an "
        "outage, and they are the case a raw failure count gets wrong.",
        ("Deliveries paged per hook", "bucketed on status_code"),
        [
            ("Every attempt 2xx", "clean, nothing to do", "good"),
            ("Failures, then a 2xx", "fixed, replay the gap", "plain"),
            ("401 or 403 run", "your server refused it", "bad"),
            ("5xx or timed out", "handler raised or ran long", "bad"),
        ],
    ),
}

V["github/webhook-no-secret"] = {
    "flow_intro": (
        "The script tests for the absence of the config key rather than for a "
        "falsy value, because that absence is the one honest answer the API "
        "gives about a webhook secret."
    ),
    "diagram_problem": D.chain(
        "ghsec-p",
        "A signature check that skips itself because there is no header to check",
        "The receiver looks hardened in review. The branch it takes on every "
        "request is the one that verifies nothing.",
        [
            ("Hook has no secret", "key absent from config"),
            ("GitHub signs nothing", "no signature header"),
            ("Receiver checks if present", "header is never present"),
            ("Check skipped", "every request trusted"),
            ("URL is the only gate", "anyone holding it can post"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghsec-f",
        "Sorting hooks by what the config and the delivery log together prove",
        "A masked secret proves a secret exists and nothing more, so signed is "
        "the absence of evidence rather than a clean bill of health.",
        ("config.secret per hook", "plus recent delivery codes"),
        [
            ("Key absent", "unsigned, nothing to verify", "bad"),
            ("Masked, deliveries fine", "signed, value unknowable", "good"),
            ("Masked, 401s throughout", "the two secrets differ", "bad"),
            ("No config at all", "re-read the hook", "plain"),
        ],
    ),
}

V["github/webhook-event-not-subscribed"] = {
    "flow_intro": (
        "The script compares three lists rather than two: what your receiver "
        "implements, what the hook subscribes to, and what actually arrived. "
        "The third one is what separates never subscribed from a quiet week."
    ),
    "diagram_problem": D.chain(
        "ghevt-p",
        "A handler deployed for an event the hook was never subscribed to",
        "There is no rejected delivery here because there is no delivery. The "
        "only artefact is a gap, and gaps are not monitored.",
        [
            ("Handler written for release", "tested on a saved payload"),
            ("Hook lists push only", "created years earlier"),
            ("Release published", "event generated"),
            ("No delivery created", "not an error"),
            ("Handler never runs", "nothing to alert on"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghevt-f",
        "Sorting each handled event by subscription and by observed traffic",
        "Subscribed but unseen usually means the hook is on a fork or a "
        "similarly named repository, which is a different repair from adding "
        "the event.",
        ("Handlers, events array, log", "compared on canonical names"),
        [
            ("Subscribed and seen", "working as intended", "good"),
            ("Subscribed, never seen", "check which repo", "plain"),
            ("Not in the events array", "can never run", "bad"),
            ("Hook subscribes to *", "every future event too", "bad"),
        ],
    ),
}

V["github/duplicate-webhooks"] = {
    "flow_intro": (
        "The script normalises the URL before it groups, because two hooks "
        "created years apart differ by a trailing slash far more often than "
        "they differ by anything that matters."
    ),
    "diagram_problem": D.chain(
        "ghdup-p",
        "One URL registered in two scopes, so every event arrives twice",
        "Both copies are legitimate and both are correctly signed. Nothing "
        "about a single request marks it as the second one.",
        [
            ("Repo hook created", "by a setup script"),
            ("Org hook added later", "same URL, same events"),
            ("Event happens once", "two hooks subscribe"),
            ("Two deliveries sent", "one per hook"),
            ("Handler runs twice", "bot comments twice"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghdup-f",
        "Sorting endpoints by how many hooks reach them and what they share",
        "Two hooks on one URL with disjoint events are a deliberate split, and "
        "reporting that as a duplicate is how the report loses trust.",
        ("Hooks grouped by endpoint", "event sets intersected"),
        [
            ("One hook only", "unique, nothing to do", "good"),
            ("Shared URL, no shared events", "a deliberate split", "good"),
            ("Second hook inactive", "one toggle from doubling", "plain"),
            ("Overlapping events", "delivered twice, delete one", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
