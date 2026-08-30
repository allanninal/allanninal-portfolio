#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch T.

Four faults that a probe of `GET /v1/models` can prove, which is the premise
and also the hazard: written carelessly these become one diagram of one curl
command drawn four times. So each chain is drawn around the thing that is
actually different, and in three of the four that thing is not the call, it is
the second reading the call is compared against.

`llmapiver` is a matrix, not a probe. One status code means nothing here: the
whole finding is that the absent-header probe and the current-header probe
disagree, and that the same pair disagrees again when it is repeated through a
gateway. Its fix branch is the only one in the batch whose outcomes are about
a host rather than about a value.

`llmbetav` is a loop with a second pass. The first pass sorts strings into 400
and 200; the second re-reads one endpoint with and without each accepted string
and diffs the JSON, because a beta that graduated still returns 200 and still
pins you to the shape it shipped with. Its problem chain ends in a response
that is correct, older, and quietly missing fields.

`llmverif` is the only chain here that never sees the error it is about. The
request that fails is on somebody else's code path, hours ago, and all that is
left of it is a row in an aggregate. So the chain is drawn as a route that
diverges rather than a call that breaks, and the fix branch spends two of its
five outcomes handing the reading to other notes, because the same row shape
belongs to them under different conditions.

`llmegress` is the only one whose variable is the machine. The call, the key
and the endpoint are all held fixed and the location moves, which is why its
problem chain has a deploy in the middle of it and its fix branch grades a
pair of observations rather than a response.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/anthropic-version-header-missing-or-ancient"] = {
    "flow_intro": (
        "One status code cannot tell you anything about a required header, "
        "because you have no way of knowing what your client, your SDK and "
        "whatever sits between them each contributed to it. The reading here "
        "is a matrix: the same endpoint called with no version header, with "
        "the current one and with the 2023 one, then the whole matrix repeated "
        "through the gateway your production traffic actually leaves by. The "
        "finding is in the disagreements, not in any single row."
    ),
    "diagram_problem": D.chain(
        "llmapiver-p",
        "How a missing version header survives every environment but one",
        "Nothing in the chain is wrong on its own. The client is broken the "
        "whole way along and only one of the two paths says so.",
        [
            ("Client hand rolls HTTP", "no SDK, no header"),
            ("Gateway adds a default", "helpfully, in staging"),
            ("Staging returns 200", "so it ships"),
            ("Prod calls the API direct", "no gateway in that path"),
            ("400 on every request", "before any model runs"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmapiver-f",
        "Sorting hosts by a three way version probe rather than one call",
        "Each outcome is a disagreement between two probes. A single status "
        "code appears in none of them, because on its own it says nothing.",
        ("Three probes, every host", "absent, current, 2023-01-01"),
        [
            ("Absent 400, current 200", "the header is enforced here", "good"),
            ("Absent returns 200 too", "something injects it in transit", "bad"),
            ("Gateway 400s the current one", "the header is stripped", "bad"),
            ("2023-01-01 still accepted", "deprecated, and pinned in code", "bad"),
            ("Current one is not 200", "credentials, not versioning", "plain"),
        ],
    ),
}

V["llm/invalid-beta-header-value"] = {
    "flow_intro": (
        "The models endpoint accepts and validates the beta header, so it is a "
        "free zero token validator for any string your code sends. That gets "
        "you the 400s. It does not get you the quieter half, which is a name "
        "that is still perfectly valid and no longer needed, so the script "
        "makes a second pass: the same GET twice, once with the header and "
        "once without, with the two JSON bodies diffed by key."
    ),
    "diagram_problem": D.chain(
        "llmbetav-p",
        "How a graduated beta header keeps returning the older response",
        "No error, no warning, and no line in any log. The client is reading "
        "a response shape that the platform stopped documenting.",
        [
            ("Header copied from a doc", "correct on the day"),
            ("Feature graduates to GA", "header becomes optional"),
            ("Code still sends it", "nothing revalidates it"),
            ("Older shape returned", "no expires_at, old cursors"),
            ("Client drifts per release", "silently, field by field"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmbetav-f",
        "Sorting every beta string by status code and then by response shape",
        "Two passes, because the two failures do not share a signal. One is "
        "a 400. The other is a 200 with fewer keys in it.",
        ("Every beta string you send", "probed, then diffed"),
        [
            ("400 with a near match", "a typo, and here is the name", "bad"),
            ("400 with no near match", "invalid or not entitled", "bad"),
            ("200, shape differs", "graduated, pinning you back", "bad"),
            ("Sent with a conflicting beta", "one replaces the other", "bad"),
            ("200, no visible difference", "unproven, not proven fine", "plain"),
        ],
    ),
}

V["llm/org-verification-required"] = {
    "flow_intro": (
        "Neither API reports whether an organization is verified, and no "
        "endpoint replays the 400 that a streaming call received yesterday. "
        "What survives is a row in the usage report, and the row on its own is "
        "ambiguous: requests billed with no tokens either side is also what a "
        "refused parameter looks like. The separation is the comparison. One "
        "model, one hour, two keys, and only one of them producing output."
    ),
    "diagram_problem": D.chain(
        "llmverif-p",
        "How one route fails while every other route on the same model works",
        "The batch job is fine, the tests are fine, and the only broken path "
        "is the one a person is waiting on.",
        [
            ("Model resolves, 200", "the id is real and yours"),
            ("Batch route buffers", "no stream, no problem"),
            ("UI route sets stream", "same model, same org"),
            ("400 before generation", "verification, not access"),
            ("Aggregate hides it", "one row among thousands"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmverif-f",
        "Comparing two keys on one model rather than grading the model",
        "The row shape belongs to more than one fault. Which fault it is "
        "depends entirely on whether a sibling key produced output.",
        ("One model, keys compared", "requests billed, no tokens"),
        [
            ("One key mute, one producing", "per key, so not the model", "bad"),
            ("Every key on it is mute", "a refused parameter instead", "plain"),
            ("Only one key uses it", "nothing to compare against", "plain"),
            ("Model does not resolve", "entitlement or retirement", "plain"),
            ("Output on every key", "the route is not blocked", "good"),
        ],
    ),
}

V["llm/unsupported-country-region"] = {
    "flow_intro": (
        "This is the one fault in the section where the interesting variable "
        "is the machine. The call is trivial and the key is the same one that "
        "works on your laptop, so a single run proves nothing at all: it has "
        "to be issued from the production egress path and compared against the "
        "identical run from a host you already trust. Two observations, one "
        "difference, and the difference is a place."
    ),
    "diagram_problem": D.chain(
        "llmegress-p",
        "How a working deployment moves itself into a blocked geography",
        "Nobody changed the code and nobody changed the key. The request "
        "started leaving from somewhere else.",
        [
            ("Works from the laptop", "and from CI, in a US runner"),
            ("Deployed to an edge runtime", "region chosen for latency"),
            ("Egress IP moves abroad", "silently, per invocation"),
            ("403 on every call", "not a rate limit, not a key"),
            ("Retries make it worse", "the block is total"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmegress-f",
        "Grading one probe from production against the same probe elsewhere",
        "A single 403 is ambiguous. The same key returning 200 from another "
        "host is what turns it into a statement about geography.",
        ("Same probe, two hosts", "production against known good"),
        [
            ("403 here, 200 there", "geography, proven by the pair", "bad"),
            ("403 on both hosts", "the account, not the location", "plain"),
            ("401 on both hosts", "the credential, not the place", "plain"),
            ("No baseline captured", "one status, no conclusion", "plain"),
            ("200 from production", "this egress path is allowed", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
