#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch R.

The section's first four GraphQL notes, and all four read the same response
envelope. Drawing them was mostly a matter of making sure no two branches sort
on the same thing, because four diagrams of one JSON object would be four
diagrams of nothing.

The first sorts on the status line against the body. Its chain is a client that
checked res.ok and got a null, and its branch has two rows carrying errors that
demand opposite handling, which is the whole reason the note exists.

The second sorts nulls, not responses. Its chain is an aggregation running over
a result set that is eight cells short, and its branch has withheld and absent
sitting next to each other because they look identical in the data and mean
opposite things.

The third sorts two buckets against each other. Its chain is a green health
check on a dead integration, and its branch is the only one in the batch whose
rows are pairs of readings rather than single facts, because one bucket on its
own explains nothing.

The fourth sorts a query document. Nothing in its branch touches a response at
all: the rows are shapes of query text, which is the point, since the rejection
happens before execution and the arithmetic can be done offline.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where nothing
downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/graphql-200-with-errors"] = {
    "flow_intro": (
        "One query per probe, deliberately aimed at something the endpoint will "
        "refuse, because the shape this note is about only exists on a response "
        "that failed. The document is parsed before anything is sent and a "
        "mutation or a subscription is refused outright, since the GraphQL "
        "endpoint is reached the same way for reads and writes. Everything "
        "after the request is two pure predicates over one body: the one a "
        "status-code client uses and the one a correct client uses. Where they "
        "disagree is the finding, and every response that carries errors "
        "alongside surviving data is named as a different problem rather than "
        "folded into this one."
    ),
    "diagram_problem": D.chain(
        "ghgqle-p",
        "A GraphQL failure carried in the body and walked past by a status check",
        "Every step here is a 200. The only thing that says the query failed is "
        "a key most clients never read.",
        [
            ("Query is sent", "one document, one point"),
            ("200 with errors", "data.repository is null"),
            ("res.ok passes", "the array is not read"),
            ("Null reaches the code", "or is counted as zero"),
            ("Blamed on the client", "the status said fine"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next 200 is trusted again"),
    ),
    "diagram_fix": D.branch(
        "ghgqle-f",
        "Sorting one GraphQL response by its body rather than by its status line",
        "The top two rows both carry errors and want opposite handling. "
        "Throwing on the second one discards data that arrived correctly.",
        ("One 200 response", "errors array read before data"),
        [
            ("Errors, no data", "the call failed, branch on type", "bad"),
            ("Errors beside data", "partial, a different repair", "bad"),
            ("Non-2xx status", "the check you already have", "plain"),
            ("Empty errors array", "now data can be touched", "good"),
        ],
    ),
}

V["github/graphql-partial-data-nulls"] = {
    "flow_intro": (
        "One query, sent in the shape your integration sends it, because the "
        "nulls follow the fields and a simplified probe comes back clean. What "
        "follows is a set difference done in both directions: every path in the "
        "data tree that resolved to null, every path named in errors, and the "
        "two compared so a field that was withheld can never be mistaken for a "
        "field that is empty. The path resolver walks list indices as well as "
        "object keys, since real GraphQL error paths contain them. The last "
        "step asks the only question that matters downstream, which is whether "
        "a total computed over this response is still a total."
    ),
    "diagram_problem": D.chain(
        "ghgqlp-p",
        "An aggregation summing across fields the token was never allowed to read",
        "Nothing throws and nothing is missing from the array. Eight cells out "
        "of fifty are unknown and every one of them is added as a zero.",
        [
            ("Fifty repos requested", "fifty objects come back"),
            ("Eight fields nulled", "errors names each path"),
            ("Nulls read as zero", "the array looks complete"),
            ("Total is 16% low", "and entirely plausible"),
            ("Moves every month", "blamed on real decline"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next total is published too"),
    ),
    "diagram_fix": D.branch(
        "ghgqlp-f",
        "Sorting each null in a response by whether an errors path explains it",
        "The top two rows are the same value in the same shape of response. "
        "One is unknown and one is none, and only the errors array knows which.",
        ("Each null in the data", "matched against errors[].path"),
        [
            ("Null, path explains it", "withheld: unknown, not zero", "bad"),
            ("Null, nothing explains it", "absent: a real answer", "plain"),
            ("Path with no null", "an element dropped, not nulled", "plain"),
            ("No nulls, no errors", "the total really is a total", "good"),
        ],
    ),
}

V["github/graphql-rate-limited"] = {
    "flow_intro": (
        "The default run spends nothing at all. GET /rate_limit reports the "
        "GraphQL bucket beside the REST one and is documented not to count "
        "against either, so the two can be printed side by side, which is what "
        "ends the argument about whether the token is broken. The observed "
        "limit is then read backwards to name the actor it belongs to, since a "
        "job that works on a laptop and dies in CI at a fifth of the volume is "
        "usually a 1,000-point budget rather than a code difference. Finally "
        "the points are divided by a measured query cost, because queries per "
        "hour is the only unit anybody can put in a scheduler."
    ),
    "diagram_problem": D.chain(
        "ghgqlr-p",
        "A REST health check reporting green while the GraphQL budget is empty",
        "The token is genuinely fine and can be proved fine in a terminal. The "
        "bucket that is empty is not the bucket anybody is watching.",
        [
            ("REST moved to GraphQL", "one query for a hundred calls"),
            ("Points bucket drains", "core is barely touched"),
            ("Health check stays green", "it reads core"),
            ("RATE_LIMITED on every call", "with a working token"),
            ("Hours spent in the client", "there is nothing there"),
        ],
        fail_at=1,
        loop=(4, 2, "and the green gauge is believed again"),
    ),
    "diagram_fix": D.branch(
        "ghgqlr-f",
        "Sorting a token by both rate-limit buckets read in the same free call",
        "Every row is a pair of readings. One bucket on its own cannot tell "
        "you which of these four you are in, which is why both are printed.",
        ("Both buckets, one free GET", "graphql beside core"),
        [
            ("GraphQL empty, core fine", "the green gauge is lying", "bad"),
            ("Core empty, GraphQL fine", "the REST quota, another note", "plain"),
            ("GraphQL under a fifth left", "slow down before zero", "bad"),
            ("Both healthy, cost measured", "budget stated in queries", "good"),
        ],
    ),
}

V["github/graphql-node-limit-exceeded"] = {
    "flow_intro": (
        "No token, no request, no points. The node count is a function of the "
        "query text, so the document is stripped of comments and strings, "
        "walked once with a stack of multipliers, and every connection carrying "
        "a first or a last contributes the product of its own value and every "
        "value above it. That total is the number the server computes, which is "
        "why the check can be run in CI over a directory of query files. The "
        "script then solves for the largest slice the deepest connection could "
        "take and still fit, so the repair is a specific number in a specific "
        "place rather than an instruction to make the query smaller."
    ),
    "diagram_problem": D.chain(
        "ghgqln-p",
        "A query rejected for its shape while the search goes looking at the data",
        "Every number in the document is 100 and the document is fifteen "
        "lines. The multiplication that makes it enormous is on no screen.",
        [
            ("first: 100 three deep", "the maximum, everywhere"),
            ("1,010,100 nodes", "over a cap of 500,000"),
            ("Rejected before running", "no partial result at all"),
            ("Read as too much data", "the org must be too big"),
            ("Filters narrowed", "and it fails identically"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next filter is tried"),
    ),
    "diagram_fix": D.branch(
        "ghgqln-f",
        "Sorting a query document by the node count computed from its own text",
        "Not one of these rows is about a response. The rejection happens "
        "before execution, so the whole verdict comes out of the text.",
        ("The query document", "first values multiplied down"),
        [
            ("Over the cap", "lower the deepest first", "bad"),
            ("Near the cap", "one schema change from failing", "bad"),
            ("Slice is a variable", "supply it or it is not counted", "plain"),
            ("Comfortably under", "and paginated per connection", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
