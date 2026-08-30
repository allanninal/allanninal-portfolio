#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch O.

Four webhook notes arriving into a section that already publishes ten of them,
so each of these had to be a different question rather than a different phrasing.

The first is about the encoding of the body rather than anything inside it. The
problem chain is a hook left on its default content type and a receiver that
answers 200 to a body it never understood, which is why the failure audit that
already exists here walks straight past it. The fix branch sorts the configured
encoding against the receiver the caller declares, because the API can see one
of those two and never the other.

The second is the only one in the section where the subject is not the hook.
The chain is a firewall rule that was correct the afternoon it was written, and
the branch sorts published ranges by how much of each one your own rules
actually permit, with one outcome for the list that was built from the wrong
array of /meta entirely.

The third is the opposite of the note about a hook with no secret. Nothing in
its chain fails; it is a value quietly accumulating readers for six years. The
branch has the reconciliation finding at the top, because a rotation your
records claim and the hook's timestamp predates is the one worth going to look
for.

The fourth has no failure in it either, for a different reason: nothing is
attempted. A blank or placeholder destination on the App produces no deliveries
and therefore no failed deliveries, and the branch is careful that a real URL
with an empty log is a question rather than a verdict.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/webhook-content-type-mismatch"] = {
    "flow_intro": (
        "Three kinds of GET and one judgement call. The hook list gives the "
        "configured encoding, and an absent field is resolved to form rather "
        "than to unknown, because that is the documented default and the most "
        "common way this happens. The delivery list gives the recent statuses, "
        "and the individual records give the only thing that settles it: the "
        "content-type header GitHub really sent, and a body recorded as one "
        "payload key holding a string. What the receiver does with any of that "
        "is declared by the caller and labelled as declared."
    ),
    "diagram_problem": D.chain(
        "ghctyp-p",
        "A hook left on the default content type feeding a receiver written for JSON",
        "The status codes are all fine, which is what sends the investigation "
        "everywhere except the one field that is wrong.",
        [
            ("Default content type", "nobody chose form"),
            ("Body arrives wrapped", "payload= not the event"),
            ("Handler returns 200", "having parsed nothing"),
            ("Delivery log is green", "so the audit finds none"),
            ("URL and events checked", "all of them correct"),
        ],
        fail_at=1,
        loop=(4, 2, "and the green log is read again"),
    ),
    "diagram_fix": D.branch(
        "ghctyp-f",
        "Sorting the configured encoding against the receiver the caller declares",
        "The top row is the finding whether or not anything has ever failed. "
        "The third is not a bug, and it still ends with advice about bytes.",
        ("Configured encoding", "against the declared receiver"),
        [
            ("Form hook, JSON receiver", "no key is where you look", "bad"),
            ("JSON hook, form parser", "the mirror of the same bug", "bad"),
            ("Form on both sides", "verify over the raw bytes", "plain"),
            ("JSON on both sides", "nothing in between them", "good"),
        ],
    ),
}

V["github/webhook-ip-allowlist-drift"] = {
    "flow_intro": (
        "One unauthenticated GET and then arithmetic that runs offline, which "
        "is the right split for a check whose owner is the firewall team "
        "rather than the GitHub one. Coverage is measured over address counts "
        "instead of over the text of the CIDRs, so an equivalent rewrite of a "
        "range passes and a subset is reported with the fraction it really "
        "permits. The same allow-list is scored against every other array in "
        "the response, which turns a list built from the wrong one into a "
        "sentence rather than eight unexplained blocked ranges."
    ),
    "diagram_problem": D.chain(
        "ghmeta-p",
        "A firewall allow-list going stale against GitHub's published hook ranges",
        "Nobody made a mistake here. The rule was right the afternoon it was "
        "written and nothing on your side subscribes to the list it copied.",
        [
            ("Ranges pasted once", "correct that afternoon"),
            ("Published set moves", "nothing is subscribed"),
            ("One range is blocked", "and most events land"),
            ("Read as flakiness", "and retried by hand"),
            ("Receiver is blamed", "and nothing changes"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next range is added"),
    ),
    "diagram_fix": D.branch(
        "ghmeta-f",
        "Sorting published hook ranges by how much of each one your rules permit",
        "The first row is the one that hides, because a partly covered range "
        "fails for some deliveries and works for the rest.",
        ("Published hook ranges", "against your exported rules"),
        [
            ("Covered in part", "fails for some deliveries", "bad"),
            ("Matches the api array", "the wrong half of /meta", "bad"),
            ("Default route present", "the control does nothing", "plain"),
            ("Every range covered", "now generate it on a timer", "good"),
        ],
    ),
}

V["github/webhook-secret-never-rotated"] = {
    "flow_intro": (
        "One GET per scope and no secret anywhere in the program. Presence is "
        "the only readable fact, the report is built from a config the value "
        "has already been stripped out of, and age comes from updated_at, "
        "which is a proxy the output names as one. The proxy is conclusive in "
        "a single direction: old proves no rotation, recent proves an edit and "
        "nothing more. Where the caller supplies a rotation date, one more "
        "comparison becomes possible, and it is the one that catches a "
        "rotation that only ever reached the receiver."
    ),
    "diagram_problem": D.chain(
        "ghstale-p",
        "A webhook secret quietly accumulating readers over six years",
        "There is no failure anywhere in this chain. That is the reason it "
        "runs for years without anybody being asked to stop it.",
        [
            ("Secret set at launch", "and never since"),
            ("Nothing expires it", "no prompt, no dashboard"),
            ("Readers accumulate", "configs, tickets, laptops"),
            ("An audit asks its age", "the API will not say"),
            ("Called probably fine", "on somebody's memory"),
        ],
        fail_at=1,
        loop=(4, 2, "and another year is added"),
    ),
    "diagram_fix": D.branch(
        "ghstale-f",
        "Sorting a hook by what its own timestamp can and cannot prove about the secret",
        "The third row is deliberately not a pass. A recent edit could have "
        "been the URL, and grading that as compliant is worse than no check.",
        ("Secret presence and age", "read from updated_at"),
        [
            ("Rotation on record only", "the hook predates the claim", "bad"),
            ("Untouched for years", "still the original secret", "bad"),
            ("Edited inside the window", "unknown, not compliant", "plain"),
            ("Rotated and reconciled", "the hook agrees with you", "good"),
        ],
    ),
}

V["github/app-webhook-url-unset"] = {
    "flow_intro": (
        "Three GETs against the App itself, authenticated with a JWT the "
        "script takes from the environment rather than signing, so the private "
        "key never enters the process. The classifier is the part that matters: "
        "it sorts unset, malformed, placeholder, tunnel, loopback and plain "
        "http before it will call anything a production destination, because "
        "every expensive version of this problem has a URL in the field. The "
        "delivery log corroborates and is only read next to the subscription "
        "list, never on its own."
    ),
    "diagram_problem": D.chain(
        "ghapphk-p",
        "A GitHub App shipped with the quickstart proxy still in its webhook field",
        "The delivery log is empty and empty reads as looking in the wrong "
        "place, so the search goes outward instead of to the destination.",
        [
            ("Tutorial URL kept", "works on a laptop"),
            ("The App ships", "the field looks filled in"),
            ("No event arrives", "and none fails either"),
            ("Installations checked", "all of them correct"),
            ("Permissions checked", "correct as well"),
        ],
        fail_at=1,
        loop=(4, 2, "and the empty log is read again"),
    ),
    "diagram_fix": D.branch(
        "ghapphk-f",
        "Sorting an App webhook destination against the events the App subscribes to",
        "The third row is a question rather than a verdict, because deliveries "
        "are retained for a window and quiet weeks exist.",
        ("App hook destination", "with its event subscriptions"),
        [
            ("Blank, and subscribed", "nowhere to deliver to", "bad"),
            ("A proxy or a loopback", "filled in and unreachable", "bad"),
            ("Real URL, empty log", "a question, not a verdict", "plain"),
            ("Real URL, events arriving", "and a secret is set", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
