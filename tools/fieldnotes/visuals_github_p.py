#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch P.

Four notes about pagination that answered 200 and was wrong anyway. The section
already publishes the obvious pagination bugs, so none of these four is about a
page that was never fetched: every client here paginates, and every one of them
paginates against an assumption the API never agreed to.

The first is a page size larger than the maximum. GitHub lowers it instead of
refusing it, so the chain is a loop that asked for five hundred, got a hundred,
and read the difference as the end of the list. The branch sorts one response by
the two questions that could have ended the loop, and the top two rows are both
short pages.

The second is a header field that is sometimes absent. The chain is a page count
computed from a rel that was not there; the branch sorts endpoints by whether
their Link header can be indexed or only walked, and the second row is a finding
even though nothing in it is missing.

The third is an endpoint that reads neither page nor per_page. The chain has no
terminating condition anywhere in it, which is why the loop symbol runs from the
last box rather than to it, and the branch sorts on what the endpoint's own next
link is built from rather than on what came back.

The fourth has a flag in the payload that says the answer is partial. The chain
is a query broad enough to run out of time, and the branch sorts repeated runs of
one query, because a single run cannot tell a timeout from a small result set.

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

V["github/per-page-over-100-clamped"] = {
    "flow_intro": (
        "One GET per probed path, and the request deliberately asks for a page "
        "size that cannot be served. What comes back is measured rather than "
        "assumed, because the effective page size is the smallest of three "
        "numbers and only one of them is yours. The whole finding is then a "
        "disagreement between two predicates evaluated over the same response: "
        "the one that asks whether the page was shorter than requested, and the "
        "one that asks whether the Link header still advertises a next page. "
        "Both are pure functions, so the rule can be tested without spending a "
        "request on it."
    ),
    "diagram_problem": D.chain(
        "ghclamp-p",
        "A page size of 500 quietly served as 100 and read as the end of the list",
        "Nothing in this chain returns an error. The only wrong number is the "
        "one the client compared against, and it was never GitHub's number.",
        [
            ("Asks for per_page=500", "to save round trips"),
            ("Served 100, no error", "the value was reduced"),
            ("100 is under 500", "so the loop calls it done"),
            ("Report looks complete", "and is short by four fifths"),
            ("Counts are queried", "the API is blamed"),
        ],
        fail_at=1,
        loop=(4, 2, "and the short page is trusted again"),
    ),
    "diagram_fix": D.branch(
        "ghclamp-f",
        "Sorting one list response by the two questions that could end a pagination loop",
        "The top two rows are both short pages and only one of them is losing "
        "data today. The second is losing data on the week the list grows.",
        ("One list response", "short-page check against the Link header"),
        [
            ("Short page, next present", "the loop stops mid list", "bad"),
            ("Exactly 100, no next", "true today, not next month", "bad"),
            ("Under 100, no next", "clamp real, unproven here", "plain"),
            ("Full page, next honoured", "the Link header ends it", "good"),
        ],
    ),
}

V["github/rel-last-absent"] = {
    "flow_intro": (
        "One GET per probed path at the smallest page size there is, because "
        "the finding lives entirely in a response header and none of the items "
        "are read. The rel names on that header are turned into a capability "
        "list rather than a boolean: an endpoint that can be indexed supports a "
        "page count, a progress bar, a fan-out over page numbers and a jump to "
        "the end, and an endpoint that can only be walked supports none of "
        "them. The script also models the bug directly, computing the page "
        "count the careless way beside the careful way so the two can be shown "
        "disagreeing."
    ),
    "diagram_problem": D.chain(
        "ghlast-p",
        "A pager that computes a page count from a rel=last that is not there",
        "The dangerous version of this does not throw. It defaults the missing "
        "page count to one and reports a single page as the whole collection.",
        [
            ("Reads rel=last", "to size the job up front"),
            ("Header has only next", "the count cannot be made"),
            ("Missing reads as one", "or the pager throws"),
            ("One page is returned", "and reported as all of it"),
            ("Endpoint called empty", "the loop was never run"),
        ],
        fail_at=1,
        loop=(4, 2, "and the page count is trusted again"),
    ),
    "diagram_fix": D.branch(
        "ghlast-f",
        "Sorting an endpoint by whether its Link header can be indexed or only walked",
        "The second row is the one worth arguing about. A page count that "
        "exists is still a number that moves while you are reading it.",
        ("Each list endpoint", "the rel names on one response"),
        [
            ("Next, no last", "walk it, never index it", "bad"),
            ("Last present, count cached", "it moves while you read", "bad"),
            ("No next at all", "one page really is all", "plain"),
            ("Driven off next alone", "absence is the terminator", "good"),
        ],
    ),
}

V["github/endpoint-ignores-page-param"] = {
    "flow_intro": (
        "Two GETs per probed path, both at the smallest page size, and the "
        "comparison is between the identifiers on page one and the identifiers "
        "on page two. Identical ids are suggestive rather than conclusive, "
        "because a feed sorted by recency can move between two requests, so the "
        "script reads a second and independent signal: the query parameters on "
        "the endpoint's own next link. An endpoint whose next link carries a "
        "cursor instead of a page number has told you what it supports, and "
        "that answer does not depend on timing at all."
    ),
    "diagram_problem": D.chain(
        "ghpgig-p",
        "A page counter incremented against an endpoint that never reads it",
        "There is no terminating condition anywhere in this chain. Every page "
        "is full, so the loop that stops on a short page never stops.",
        [
            ("page=2 is sent", "as it is everywhere else"),
            ("Page one comes back", "with a 200 and no hint"),
            ("Rows look new", "and are written again"),
            ("Duplicates pile up", "blamed on the writer"),
            ("Loop never ends", "there is no short page"),
        ],
        fail_at=1,
        loop=(4, 2, "and the same page is collected again"),
    ),
    "diagram_fix": D.branch(
        "ghpgig-f",
        "Sorting an endpoint by what its own next link is built from",
        "Two signals, and only their agreement is conclusive. The second row "
        "is the honest answer when the evidence is one busy feed.",
        ("Page one against page two", "ids compared, next link read"),
        [
            ("Same ids, cursor link", "page is ignored entirely", "bad"),
            ("Same ids, page link", "a feed that moved, re-run it", "plain"),
            ("Cursor link, ids differ", "it pages, not by number", "plain"),
            ("Different ids, page link", "offset paging is honoured", "good"),
        ],
    ),
}

V["github/search-incomplete-results"] = {
    "flow_intro": (
        "The same query sent a small number of times with a pause between, "
        "because one run cannot separate a partial answer from a small one. "
        "Three fields are kept from each response and the rest is discarded: "
        "the flag, the reported total and the number of items actually "
        "delivered. The verdict is built from the sequence rather than from any "
        "one response, which is what lets it say whether retrying is a repair "
        "or a waste, and the total is checked against the retrievable ceiling "
        "purely so the script can rule that explanation out by name."
    ),
    "diagram_problem": D.chain(
        "ghinc-p",
        "A search answered in part because the server ran out of time",
        "The status is 200 and the JSON is valid. The only thing that says "
        "the answer is partial is a boolean nobody wrote a branch for.",
        [
            ("Broad query is sent", "no repo or date bound"),
            ("200 with a flag set", "and fewer items than exist"),
            ("Flag is never read", "items are taken as the answer"),
            ("Cached as complete", "and the count changes daily"),
            ("Called index lag", "and waited out"),
        ],
        fail_at=1,
        loop=(4, 2, "and the partial answer is cached again"),
    ),
    "diagram_fix": D.branch(
        "ghinc-f",
        "Sorting a search response by its own flag rather than by its status code",
        "The top two rows carry the same flag and opposite repairs. One is "
        "retried and the other has to be made a smaller question.",
        ("Repeated identical queries", "incomplete_results and the counts"),
        [
            ("Flagged every round", "narrow it, retrying will not help", "bad"),
            ("Flagged some rounds", "retry, and never cache it", "bad"),
            ("Counts move, no flag", "still partial, treat as a retry", "plain"),
            ("Stable and unflagged", "the answer is the whole answer", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
