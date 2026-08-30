#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch S.

The section's second four GraphQL notes. Batch R drew the response envelope
four ways; these four had to avoid drawing it a fifth, so not one of these
branches sorts on an errors array.

The first sorts a number by where it came from. Its chain is a value that is
not in the query text at all, and its branch has a literal and a variable
carrying the same 250 on two different rows, because the number is the same and
the file you have to open is not.

The second sorts connections, and it is the only branch in the batch whose rows
are about a single parent rather than a whole response. Its chain is an outer
loop that is entirely correct sitting on top of an inner one that never starts,
and its rows separate a connection that truncated from one that cannot even be
asked whether it did.

The third sorts three numbers against each other. Its chain is a query growing a
field at a time with no price attached to any of the diffs, and its branch has a
predicted cost, a measured cost and a recorded cost on the same axis, which is
the only diagram in the batch where the rows are comparisons rather than states.

The fourth sorts a call by time and by what it was charged. Its chain is a retry
loop paying three times for nothing, and its branch is the only one here with a
row that refuses to answer: a shared bucket cannot attribute a charge, and
saying so is better than printing a number that looks like proof.

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

V["github/graphql-first-over-100"] = {
    "flow_intro": (
        "The audit is pure text and the ceiling is a single number, so the "
        "interesting work is resolving what the number is being compared "
        "against. Every first and last in the document is collected with the "
        "field carrying it, then resolved through three sources in the order "
        "the server sees them: a literal, a value in the variables map, and a "
        "default in the operation's variable definitions. Only then is anything "
        "measured against 100. The optional probe sends the document once to "
        "show what a validation failure looks like, which is a body with an "
        "errors array and no data key at all, and it refuses to open a socket "
        "if the document turns out to contain a mutation."
    ),
    "diagram_problem": D.chain(
        "ghgqlfst-p",
        "An oversized page size arriving through a variable a text search cannot see",
        "Every number in the document is under the ceiling. The one that is "
        "not is a default nobody has read in a year.",
        [
            ("Ported from REST", "per_page was clamped"),
            ("first resolves to 250", "over a ceiling of 100"),
            ("Rejected, never runs", "no data key at all"),
            ("Grep finds nothing", "250 is not in the query"),
            ("Blamed on an outage", "it fails every time"),
        ],
        fail_at=1,
        loop=(4, 2, "and the same document is sent again"),
    ),
    "diagram_fix": D.branch(
        "ghgqlfst-f",
        "Sorting one slicing argument by the source its value came from",
        "The top two rows are the same value against the same ceiling. Only "
        "the source says which file has to change.",
        ("Each first and last", "resolved, then measured"),
        [
            ("Over, written down", "change the query text", "bad"),
            ("Over, via a variable", "change the caller", "bad"),
            ("Nobody can resolve it", "supply it or it is unchecked", "plain"),
            ("1 to 100, paginated", "now check the node count", "good"),
        ],
    ),
}

V["github/graphql-nested-pagination-ignored"] = {
    "flow_intro": (
        "Two halves, and the document half runs first because a connection "
        "that asked for neither totalCount nor pageInfo cannot be judged by "
        "anybody. Connections are found by shape rather than by their "
        "arguments, so one paginated through a variable is still found, and a "
        "pageInfo belonging to an inner connection is never credited to the "
        "connection that contains it. The response half then walks the returned "
        "tree, finds the same connections wherever they ended up, and reports "
        "the returned count against the true count once per parent, because a "
        "single total is exactly what hides this. The last line counts the "
        "follow-up queries a correct inner walk would cost."
    ),
    "diagram_problem": D.chain(
        "ghgqlnst-p",
        "A correct outer pagination loop sitting on top of inner ones that never run",
        "The loop is right and the repository count is right. Each parent "
        "quietly hands back its first page and nothing raises an error.",
        [
            ("Outer cursor followed", "every repo is visited"),
            ("Inner restarts each page", "first 100, then stops"),
            ("totalCount is not read", "nodes looks like a list"),
            ("Totals are a floor", "plausible and stable"),
            ("Busiest repos worst hit", "the ones being reported"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next outer page starts over"),
    ),
    "diagram_fix": D.branch(
        "ghgqlnst-f",
        "Sorting each connection in one response by what it can prove about itself",
        "The rows are per parent, not per response. Two of them need a query "
        "each before anything computed over this data is a total.",
        ("Each connection found", "totalCount against nodes"),
        [
            ("Inner, short of total", "one query per parent", "bad"),
            ("Inner, neither field", "unknowable, add them first", "bad"),
            ("Outer has more pages", "the one people do notice", "plain"),
            ("Returned all it holds", "the total is a total", "good"),
        ],
    ),
}

V["github/graphql-cost-not-measured"] = {
    "flow_intro": (
        "Three numbers for one query shape. The prediction is free and comes "
        "out of the text, using the documented approximation over the slices it "
        "can resolve; the measurement costs one point and comes from the server "
        "itself, after rateLimit is inserted into the document's top-level "
        "selection set and only there, which is why the comments and strings "
        "are blanked to spaces rather than removed and every index still lines "
        "up with the original. The third number is whatever was recorded last "
        "time. What the run reports is the disagreement between them, and the "
        "baseline file is printed for you to update rather than rewritten."
    ),
    "diagram_problem": D.chain(
        "ghgqlcst-p",
        "A query growing one field at a time with no price attached to any diff",
        "Each change is small, correct and reviewed. None of them mentions "
        "points, because the price was never written down to be changed.",
        [
            ("First version costs 1", "nothing to instrument"),
            ("One nested field added", "the price becomes 14"),
            ("No cost in the diff", "review sees two lines"),
            ("Budget gone at 2pm", "and fine again at 3"),
            ("Read as an incident", "status pages, networks"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next field is added too"),
    ),
    "diagram_fix": D.branch(
        "ghgqlcst-f",
        "Sorting one query shape by three costs measured against each other",
        "Every row is a comparison rather than a state. One number on its own "
        "cannot tell you which of these four you are looking at.",
        ("One shape, three costs", "predicted, measured, recorded"),
        [
            ("Dearer than last time", "a diff caused it, review it", "bad"),
            ("Dearer than its text", "something extra is traversed", "bad"),
            ("Rows few, points many", "lower first, not the filter", "plain"),
            ("Measured and recorded", "the next change is visible", "good"),
        ],
    ),
}

V["github/graphql-timeout-point-penalty"] = {
    "flow_intro": (
        "The instrument is a subtraction over a free endpoint, and most of the "
        "code exists to stop it lying. GET /rate_limit is read twice with "
        "nothing sent in between, so a bucket already draining under another "
        "process is caught before it can be mistaken for a penalty, and then "
        "again either side of one attempt. A reset timestamp that moves between "
        "readings voids the measurement rather than producing a negative "
        "number. The query is sent exactly once and never retried, because "
        "retrying is the behaviour the note exists to stop, and the cost of the "
        "retries somebody would have made is printed instead."
    ),
    "diagram_problem": D.chain(
        "ghgqltmo-p",
        "A retry loop paying the timeout penalty three more times for nothing",
        "A 502 is a gateway error and gateway errors get retried. This one "
        "was deliberate, deterministic, and charged on every attempt.",
        [
            ("Data grew, not the code", "4s becomes 10s"),
            ("Killed at the cutoff", "502, and charged extra"),
            ("Read as transient", "backoff, retry, retry"),
            ("Nothing returned", "budget several hundred down"),
            ("Blamed on the token", "the bucket is shared"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next retry is charged too"),
    ),
    "diagram_fix": D.branch(
        "ghgqltmo-f",
        "Sorting one attempt by its elapsed time and by what the bucket did",
        "One row here refuses to answer. A shared bucket cannot attribute a "
        "charge, and saying so beats printing a number that looks like proof.",
        ("One attempt, three reads", "used before, after, and idle"),
        [
            ("Killed, charged extra", "shrink it, never retry", "bad"),
            ("Killed, bucket noisy", "not attributable, re-run alone", "plain"),
            ("Returned at 8 seconds", "one busy repo from failing", "bad"),
            ("Well inside the cutoff", "log the time, watch it", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
