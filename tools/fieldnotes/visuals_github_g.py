#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch G.

Four credential notes that sit next to each other, so the diagrams have to do
some of the work of keeping them apart. Each fix branch sorts on a different
signal on purpose: a pair of ceilings, two different 401 messages, two ladders
run side by side, and one response header on a credential that still works.

The problem chains differ in the same way. Two of them end at an error, one ends
at a number nobody costed, and the fourth ends at nothing at all, because it is
the note that runs before the outage rather than after it. Drawn in GitHub blue.

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

V["github/actions-token-repo-scoped-limit"] = {
    "flow_intro": (
        "Nothing in this check judges whether the credential is any good. It "
        "reads the ceilings the credential was handed, names the class from "
        "the shape of them, and then does arithmetic against a pool that "
        "belongs to the repository rather than to the job. The output is a job "
        "number, which is the only part anyone acts on."
    ),
    "diagram_problem": D.chain(
        "ghatb-p",
        "A matrix workflow draining one thousand requests shared by a repository",
        "The failing job moves between reruns, because the deciding factor is "
        "not that job. It is how much of the shared pool the others spent first.",
        [
            ("Works on a laptop", "5000 an hour"),
            ("Moved into Actions", "1000 an hour"),
            ("Matrix expands to 12", "120 calls each"),
            ("Pool empties at 1000", "one repository, one clock"),
            ("403 in a moving job", "reads as flaky"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghatb-f",
        "Naming the credential class from the ceilings it was handed",
        "The core number is a fingerprint, and the graphql row and a 403 from "
        "GET /user corroborate it from two other directions.",
        ("GET /rate_limit", "core and graphql rows"),
        [
            ("Core 1000, user 403", "Actions token, repo scoped", "bad"),
            ("Run costs more than that", "job N of M starves first", "bad"),
            ("Core 5000", "user or App at the floor, ambiguous", "plain"),
            ("Run fits the pool", "nothing to reclaim", "good"),
        ],
    ),
}

V["github/bad-credentials-401"] = {
    "flow_intro": (
        "Three requests, two of them to an endpoint that needs no credential "
        "at all. The pair with and without the header is what turns a guess "
        "into proof: GitHub only says Bad credentials about a value it "
        "actually received, and it says something else entirely about a value "
        "that never arrived."
    ),
    "diagram_problem": D.chain(
        "gh401-p",
        "One 401 message standing in for six unrelated causes",
        "Expired, revoked, truncated, quoted, empty, wrong account. The API "
        "will not say which, on purpose.",
        [
            ("401 on every call", "one message for all of it"),
            ("Public endpoint too", "needs no credential"),
            ("Token re-minted", "still 401"),
            ("Scopes reviewed", "wrong page entirely"),
            ("Two tokens, no answer", "back where it started"),
        ],
        fail_at=1,
        loop=(3, 0, "re-mint and try again"),
    ),
    "diagram_fix": D.branch(
        "gh401-f",
        "Sorting the 401 by which layer actually produced it",
        "Bad credentials means a value was received and refused. Requires "
        "authentication means nothing was received. Different repairs.",
        ("Root with and without", "the same request, twice"),
        [
            ("Bad credentials, 200 without", "the value is being refused", "bad"),
            ("Requires authentication", "the header is not arriving", "bad"),
            ("No GitHub request id", "an intermediary answered", "plain"),
            ("200 and the right login", "look at the other variable", "good"),
        ],
    ),
}

V["github/classic-pat-expired"] = {
    "flow_intro": (
        "The script never claims a token expired, because nothing observable "
        "can support that. It runs one ladder of resources under the suspect "
        "and the identical ladder under a control at the same instant, then "
        "reads the two shapes side by side. What it can prove is which of the "
        "credential and the world changed."
    ),
    "diagram_problem": D.chain(
        "ghdif-p",
        "An eleven month integration stopping at one instant with nothing deployed",
        "Total, instantaneous and silent is the signature of a credential. It "
        "looks exactly like an outage until you have seen it once.",
        [
            ("09:14 on a Tuesday", "every endpoint at once"),
            ("No deploy, no change", "nothing to roll back"),
            ("Status page green", "so the page is doubted"),
            ("Expiry unreadable", "header needs a live token"),
            ("Four theories, no test", "each one an hour"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "ghdif-f",
        "Reading two credential ladders side by side to isolate the variable",
        "Expiry is total, so a credential that answers 200 to anything has not "
        "expired. That single observation redirects the search.",
        ("Suspect and control", "same rungs, same second"),
        [
            ("401 everywhere against 200", "the credential is the variable", "bad"),
            ("Both dead on every rung", "the store, the network, the org", "bad"),
            ("Both fail the same rung", "the resource changed, not the token", "plain"),
            ("Suspect answers 200 somewhere", "access, not the calendar", "good"),
        ],
    ),
}

V["github/token-expiring-soon"] = {
    "flow_intro": (
        "One free request per credential and the answer is in a header that "
        "has been arriving for months. The interesting branch is the one where "
        "there is no header at all, because a credential that never expires "
        "and a class that does not report a date are different findings and a "
        "careless script prints them the same."
    ),
    "diagram_problem": D.chain(
        "ghexp-p",
        "A credential reaching its expiry with nobody reading the header",
        "Nothing is broken yet. That is the whole point: this is the only "
        "check here with no post mortem version of itself.",
        [
            ("Expiry set at mint", "366 days, then forgotten"),
            ("Header on every call", "nobody reads it"),
            ("Six days left", "no warning of any kind"),
            ("09:14, total refusal", "every endpoint at once"),
            ("Date now unreadable", "header needs a live token"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghexp-f",
        "Sorting each named credential by what its expiry header actually says",
        "Absence of the header is ambiguous, and an hour of life is usually "
        "good news. Both deserve their own row rather than a shrug.",
        ("One free GET each", "read the expiry header"),
        [
            ("Under three days", "rotate now, record the date", "bad"),
            ("Succeeded, no header", "never expires, or does not say", "bad"),
            ("About an hour left", "a minted App token, a non event", "plain"),
            ("Months of headroom", "watched, and nothing due", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
