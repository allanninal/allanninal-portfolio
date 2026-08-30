#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch A.

All four notes share one spine: a request that succeeds, a response that is
short, and no error anywhere between them. So every problem chain ends in a
number somebody acted on rather than in a failure somebody saw, and every fix is
a branch, because each script sorts what the API says about its own completeness
instead of guessing at it. Drawn in GitHub blue.

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

V["github/link-header-not-followed"] = {
    "flow_intro": (
        "The script probes at one item per page, because at that page size the "
        "page number in rel=\"last\" is the exact size of the collection. It reads "
        "the header rather than the body, which is the same thing the broken "
        "client failed to do."
    ),
    "diagram_problem": D.chain(
        "ghlink-p",
        "A list read once, believed, and acted on",
        "Every step returns 200. The only statement about completeness is in a "
        "header, and the header is the part that was thrown away.",
        [
            ("Client asks for pulls", "no per_page set"),
            ("GitHub returns 30", "200 and valid JSON"),
            ("Link header ignored", "rel=next unread"),
            ("Report says 30 open", "340 exist"),
            ("Nobody sees an error", "nothing to log"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghlink-f",
        "Sorting endpoints by what their own Link header admits",
        "A rel=next with no rel=last is still a truncated list, so it gets its own "
        "state rather than being rounded to either neighbour.",
        ("Probe at per_page=1", "read the Link header"),
        [
            ("No rel=next at all", "one page really is the whole list", "good"),
            ("rel=last says 340", "and your report says 30", "bad"),
            ("rel=next, no rel=last", "truncated, and size unknown", "bad"),
            ("Counts already agree", "the loop is following next", "good"),
        ],
    ),
}

V["github/per-page-default-30"] = {
    "flow_intro": (
        "The script counts each collection exactly, in two requests, then does "
        "arithmetic you can check by hand. Nothing here is an estimate, because a "
        "projected saving is easy to argue with and a request count is not."
    ),
    "diagram_problem": D.chain(
        "ghpp-p",
        "A correct pagination loop paying three times over",
        "Nothing is broken. The data is right, the loop terminates, and the bill "
        "lands on whichever process shares the token.",
        [
            ("Loop follows rel=next", "correct and complete"),
            ("per_page unset", "30 items per request"),
            ("3,412 issues read", "114 requests, not 35"),
            ("Core quota drains", "5,000 an hour, shared"),
            ("403 at 09:14", "the other job is paged"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "ghpp-f",
        "Sorting endpoints by what a full page size would save",
        "Asking for 500 is its own finding: the API clamps it to 100 without "
        "complaint, so the saving looks real and the page arithmetic is not.",
        ("Exact count, two requests", "page one and rel=last"),
        [
            ("Fits in a single page", "nothing to save here", "good"),
            ("Already at per_page=100", "as cheap as the API gets", "good"),
            ("Left at the default 30", "114 requests instead of 35", "bad"),
            ("Asked for per_page=500", "clamped to 100 in silence", "bad"),
        ],
    ),
}

V["github/search-1000-result-cap"] = {
    "flow_intro": (
        "The script reads total_count with a one item page and compares it against "
        "the cap rather than against the page count. It also reports the search "
        "bucket from /rate_limit, which is a separate allowance and free to ask "
        "about."
    ),
    "diagram_problem": D.chain(
        "ghsrch-p",
        "A search that reports 24,831 matches and serves 1,000",
        "The count and the results disagree by design. Paging past the boundary "
        "is an error rather than an empty page, so retry logic makes it worse.",
        [
            ("Query matches 24,831", "total_count is honest"),
            ("Pages 1 to 10 work", "the first 1,000 results"),
            ("Page 11 returns 422", "only the first 1000"),
            ("Error swallowed", "logged, never read"),
            ("Report says 1,000", "a round, wrong number"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghsrch-f",
        "Sorting queries by how much of the match set is reachable",
        "The 900 to 1,000 band exists so the note arrives before the outage: that "
        "query is correct today and loses results the week it grows.",
        ("total_count at per_page=1", "one search request"),
        [
            ("No matches at all", "the query found nothing", "plain"),
            ("Under 900 results", "reachable in full, page away", "good"),
            ("900 to 1,000 results", "works now, not for long", "plain"),
            ("Above 1,000 results", "the tail cannot be paged to", "bad"),
        ],
    ),
}

V["github/compare-250-commit-cap"] = {
    "flow_intro": (
        "The script calls compare without page parameters on purpose, because that "
        "is the call the cap applies to, and reproducing it is the only way to "
        "measure what an unpaginated client is actually missing."
    ),
    "diagram_problem": D.chain(
        "ghcmp-p",
        "A changelog built from a commit list with a hole in it",
        "There is no truncation flag anywhere in the response. The only evidence "
        "is that two numbers in the same JSON body disagree.",
        [
            ("Job compares two tags", "no page parameters"),
            ("812 commits in range", "total_commits says so"),
            ("250 come back", "200, and no flag"),
            ("Notes built from 250", "entirely plausible"),
            ("562 never listed", "noticed weeks later"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ghcmp-f",
        "Sorting compare responses by total_commits against what arrived",
        "A missing total_commits is not a complete comparison. Defaulting it to "
        "zero would reproduce the bug inside the checker written to catch it.",
        ("total_commits vs commits", "one unpaginated GET"),
        [
            ("The two counts agree", "the comparison is whole", "good"),
            ("Exactly 250 of 812", "the unpaginated cap, exactly", "bad"),
            ("100 of 812", "mid walk, so keep paging", "plain"),
            ("No total_commits field", "cannot judge, do not assume", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
