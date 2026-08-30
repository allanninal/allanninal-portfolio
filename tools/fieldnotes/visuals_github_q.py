#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch Q.

Four notes about a request that was answered and should not have been trusted.
None of them is a loop bug, which the shapes are meant to carry: in three of the
four chains the client does everything the earlier notes in this section ask it
to do, and the failure is somewhere the loop cannot see.

The first is a pull request whose lists have ceilings the pull request object
knows about and the lists do not. The chain crosses a URL boundary halfway
through, because that is the whole mechanism, and the branch sorts one list
against the counter that describes it rather than against its own last page.

The second is a request the server gave up on. The chain is a retry loop that
buys the identical failure three times, so the loop symbol runs from the retry
back to the request rather than to any decision. The branch sorts one timed
response by elapsed time as much as by status, because the same 502 means two
opposite things at ten seconds and at three hundred milliseconds.

The third has a correct loop drawn in it on purpose. Nothing in that chain is
wrong except the ordering the pages were cut from, and the branch has three
rows above the healthy one because an immutable key descending repeats records
without ever hiding one, which is a different finding and a different repair.

The fourth is a resource that moved. The chain follows a redirect that works,
which is why it is drawn as a success that keeps costing, and the branch sorts a
single probe by what the status is telling you to do about it: rewrite the
config, follow it quietly, or go and read another note entirely.

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

V["github/pr-files-and-commits-caps"] = {
    "flow_intro": (
        "Three GETs per pull request, and they are three rather than one for "
        "the same reason the bug exists: the counter and the list it describes "
        "live at different URLs. One request reads changed_files and commits "
        "off the pull request object, and the other two ask each list endpoint "
        "how far it is prepared to go by reading its Link header at the "
        "maximum page size. Everything after that is arithmetic over two "
        "numbers from two responses, so the rule is pure and the tests never "
        "touch the network."
    ),
    "diagram_problem": D.chain(
        "ghprcap-p",
        "A review bot reading one list endpoint and never the counter that contradicts it",
        "The bot is not ignoring a warning. The response that is short does "
        "not carry the number it is short of, and the number lives one URL away.",
        [
            ("Bot lists PR files", "one endpoint, default page"),
            ("30 of 900 arrive", "200, no flag, no header"),
            ("Counter never read", "changed_files is elsewhere"),
            ("Summary is posted", "three files changed"),
            ("Nobody audits it", "the bot has been right"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next big pull request is truncated too"),
    ),
    "diagram_fix": D.branch(
        "ghprcap-f",
        "Sorting one list against the counter on the pull request rather than against its own last page",
        "The top row is the only one no page size can repair. The second is a "
        "list that stopped somewhere the header cannot explain.",
        ("PR counter and list", "declared count against page count"),
        [
            ("Above the endpoint cap", "unreachable at any page size", "bad"),
            ("Pages cannot hold it", "something truncated the list", "bad"),
            ("More than one page", "one page at 30 loses the rest", "plain"),
            ("Counter matches pages", "collected count can be asserted", "good"),
        ],
    ),
}

V["github/request-timeout-502"] = {
    "flow_intro": (
        "Two timed GETs against the path under test plus one free baseline "
        "against GET /rate_limit, which is the only endpoint that answers "
        "without consuming quota and therefore the only honest control here. "
        "Everything else is a classifier over three inputs: a status code, an "
        "elapsed time and the response headers. Rate-limit headers are checked "
        "first and hard, because a throttle misfiled as a timeout sends "
        "somebody off rewriting a query that was never the problem, and the "
        "two repairs have nothing in common."
    ),
    "diagram_problem": D.chain(
        "gh502-p",
        "A retry wrapper buying the same expensive failure three times over",
        "Every retry here is correct behaviour for a 5xx and wrong behaviour "
        "for this one. The request costs exactly as much the second time.",
        [
            ("Expensive call sent", "a diff of a huge merge"),
            ("502 at ten seconds", "no header, no interval"),
            ("Read as transient", "5xx means try again"),
            ("Same call resent", "same cost, same result"),
            ("Filed as flakiness", "backoff is made longer"),
        ],
        fail_at=1,
        loop=(4, 0, "and the identical query is sent again"),
    ),
    "diagram_fix": D.branch(
        "gh502-f",
        "Sorting one timed response by elapsed time as much as by status code",
        "The top two rows share a status code and have opposite repairs. The "
        "third is a success that is one busy afternoon from being the first.",
        ("One timed attempt", "status, elapsed, headers"),
        [
            ("Gateway at the cutoff", "too expensive, make it smaller", "bad"),
            ("Gateway in 0.3s", "an incident, retry is right", "plain"),
            ("200 just under the line", "narrow it while it works", "bad"),
            ("Throttled with a wait", "a rate limit, wait it out", "plain"),
            ("Answered well inside", "nothing to do here", "good"),
        ],
    ),
}

V["github/unstable-sort-duplicates"] = {
    "flow_intro": (
        "Two walks of the same window, back to back, and a diff of the id sets "
        "they collected. What counts as evidence depends on the ordering, "
        "which is why the interpretation is a function of its own: an id that "
        "shows up only in the second walk of an ascending immutable listing is "
        "the collection growing rather than the walk failing, and reporting "
        "that as a skip would be a false alarm shipped to a reader. The "
        "exposure is readable without any of that, straight off the sort key "
        "in your own request."
    ),
    "diagram_problem": D.chain(
        "ghusort-p",
        "A correct pagination loop over an ordering that moves between requests",
        "There is no mistake in this loop. The pages were cut from an order "
        "that changed between the moment page one was served and page two.",
        [
            ("Page 1 is read", "sorted on a field that moves"),
            ("A row is updated", "it jumps to the front"),
            ("Everything shifts", "by exactly one position"),
            ("Page 2 is read", "the boundary row is gone"),
            ("Counts never match", "and nobody can reproduce"),
        ],
        fail_at=1,
        loop=(4, 0, "and tomorrow night it is a different row"),
    ),
    "diagram_fix": D.branch(
        "ghusort-f",
        "Sorting a walk by what its ordering can lose rather than by whether the loop is right",
        "Three of these four are the same loop. Only the sort key differs, and "
        "only one of the three can hide a record from you for good.",
        ("Sort key and direction", "what a walk over this can lose"),
        [
            ("Mutable key, proven", "ids differ across two walks", "bad"),
            ("Mutable key, quiet hour", "exposed, just not caught yet", "bad"),
            ("Immutable, descending", "repeats rows, hides none", "plain"),
            ("Immutable, ascending", "grows past your position", "good"),
        ],
    ),
}

V["github/repo-renamed-301-redirect"] = {
    "flow_intro": (
        "One GET with automatic redirect following turned off, because that is "
        "the only way the 301 is visible at all, and one more to follow it "
        "where there is something to follow. The classification has more "
        "states than a two-branch problem needs: a permanent redirect and a "
        "temporary one carry opposite repairs, a difference of capitalisation "
        "is not a rename however much it looks like one, and a 404 is a "
        "different note with a different set of probes. Each of those is one "
        "wrong config edit that never gets made."
    ),
    "diagram_problem": D.chain(
        "ghrn301-p",
        "A renamed repository that keeps working and costs a round trip on every call",
        "Nothing fails anywhere in this chain, which is why it survives for "
        "months. The integration is paying twice for every call it makes.",
        [
            ("Repo is renamed", "in an org, on a Tuesday"),
            ("Old path answers 301", "with the canonical address"),
            ("Client follows it", "quietly, and succeeds"),
            ("Config is never fixed", "the stale name still works"),
            ("Every call costs two", "quota drains at double"),
        ],
        fail_at=1,
        loop=(4, 2, "and the redirect is paid for again"),
    ),
    "diagram_fix": D.branch(
        "ghrn301-f",
        "Sorting one probe of a configured name by what the status tells you to do about it",
        "Only the top two rows are anything to fix, and the bottom two exist "
        "so that nobody edits a configuration that was already correct.",
        ("One probe, no following", "status, Location and full_name"),
        [
            ("301 with a Location", "stale name, key on the id", "bad"),
            ("200 under another name", "followed silently, still stale", "bad"),
            ("302 or 307", "follow it, write nothing down", "plain"),
            ("Differs only in case", "the same repository", "plain"),
            ("Name matches, no hop", "nothing to do", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
