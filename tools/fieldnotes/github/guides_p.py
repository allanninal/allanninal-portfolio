#!/usr/bin/env python3
"""/github/ field notes, batch P — the writing.

Four notes about pagination that returned 200 and was wrong anyway. The section
already carries the pagination bugs everybody knows about: the client that never
read the Link header, the page size left at its default, the Search ceiling at a
thousand results, the compare endpoint that stops at 250. None of these four is
one of those. Every client here paginates, and every one of them paginates
against an assumption GitHub never agreed to.

The first is a page size above the maximum. GitHub does not answer 422; it
lowers the number and serves the request. That is harmless until the client
decides it has reached the end of the list by noticing it got fewer items than
it asked for, at which point a request for 500 reads four fifths of a collection
and reports it as all of it.

The second is a field that is sometimes not in the Link header at all. Where
GitHub cannot compute a final page it omits rel="last", and a pager that needs
that value to size the job either throws or, much worse, defaults the missing
count to one. The existing Link header note is about a loop that was never
written; this one is about a loop that was written and requires something the
header does not always carry.

The third is an endpoint that reads neither page nor per_page. It does not
reject them, it ignores them, so page two is page one and a loop that stops on a
short page has no terminating condition anywhere in it. The evidence is two
requests and a second, independent signal from the endpoint's own next link,
because a busy feed can move between two calls and identical ids alone would be
a false positive waiting to happen.

The fourth is a boolean in a Search payload. When a query outruns the server's
timeout, GitHub returns what it found with incomplete_results set rather than
failing. This is not the note about the thousand-result ceiling, and the script
goes out of its way to rule that explanation out by name: the queries that get
flagged here are frequently nowhere near the cap.

Read only throughout, and deliberately cheap. Three of these four scripts could
give a sharper answer with more requests, and none of them is allowed to spend
them, because a section that publishes notes on quota exhaustion has no business
shipping a diagnostic that drains a bucket to prove a point. Every script prints
what it will spend before it spends it.
"""

CITE_PAGINATION = ("Using pagination in the REST API — GitHub Docs",
                   "https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api")
CITE_BEST_PRACTICES = ("Best practices for using the REST API — GitHub Docs",
                       "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_RATE_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_PAGINATE_PLUGIN = ("octokit/plugin-paginate-rest.js",
                        "https://github.com/octokit/plugin-paginate-rest.js")
CITE_ISSUES = ("Issues — GitHub REST API",
               "https://docs.github.com/en/rest/issues/issues")
CITE_REPOS = ("Repositories — GitHub REST API",
              "https://docs.github.com/en/rest/repos/repos")
CITE_COMMUNITY_PAGING = ("Pagination parameters ignored on some endpoints — GitHub Community",
                         "https://github.com/orgs/community/discussions/73014")
CITE_SEARCH = ("Search — GitHub REST API",
               "https://docs.github.com/en/rest/search/search")
CITE_SEARCH_SYNTAX = ("Understanding the search syntax — GitHub Docs",
                      "https://docs.github.com/en/search-github/searching-on-github/understanding-the-search-syntax")

GUIDES = [

{
"slug": "per-page-over-100-clamped",
"title": "per_page above 100 is clamped and never rejected",
"description": "A client asks for per_page=500, receives exactly 100, and reads the short page as the end of the list. GitHub lowers the value instead of refusing it.",
"h1": "per_page above 100 is clamped and never rejected",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api per_page 500 returns 100",
             "github per_page maximum 100 silently ignored",
             "github api per_page limit not rejected",
             "github pagination stops early short page",
             "github rest api per_page over 100"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody set <code>per_page=500</code> to cut the number of round trips, and the request came back with exactly one hundred items and a <code>200</code>. One hundred is fewer than five hundred, so the loop concluded it had reached the end and stopped. There was no <code>422</code>, no warning header and nothing in the logs. Four fifths of the collection was never read, and the report built on it looks entirely finished.",
"short_answer": """<p>GitHub caps <code>per_page</code> at 100 and enforces the cap by <em>reducing</em> the value rather than rejecting it. A request for 500 is served as a request for 100, with a success status and no indication anywhere in the response that anything was adjusted.</p>
<p>On its own that is harmless. It turns into data loss the moment the client decides whether it has reached the last page by comparing the number of items it received against the number it asked for &mdash; a predicate that is only correct if you know the effective page size, and you do not, because it is the smallest of your number, the endpoint's own maximum and what is left in the collection. Send <code>per_page=100</code> explicitly and terminate on the absence of <code>rel="next"</code> in the <code>Link</code> header. Never on a short page.</p>""",
"problem": """<p>The number gets written once, by somebody being sensible. Fewer requests is the right instinct, 500 is a round number, and nothing about the request fails, so nobody revisits it. It survives review for the same reason: a reviewer looking at <code>per_page=500</code> sees an intention rather than an error, and a reviewer looking at <code>if len(items) &lt; page_size: break</code> sees a pattern they have written themselves, because it is correct in plenty of other APIs and in most cursor-based ones.</p>
<p>Then it survives testing, because the fixture repository has eleven issues. The short-page predicate is right on eleven items, right on ninety-nine, and wrong from the hundred-and-first onwards. The bug does not exist until the collection crosses a boundary nobody is watching, and it appears first in the busiest repository, which is the one whose numbers people rely on.</p>
<p>What makes it hard to find afterwards is that the truncation is not ragged. It is exactly one hundred, every time, in a report that has no other reason to contain round numbers. That reads as a limit somebody configured on purpose, and the search goes looking for a hard-coded <code>100</code> in your own code, where there isn't one. The 100 came from GitHub, quietly, in response to being asked for five hundred.</p>""",
"why": """<p><strong>The cap is enforced by clamping, not by validation.</strong> The maximum page size on the REST API is 100. A larger value is not a client error; it is served as 100. There is no <code>Warning</code> header, no field in the body and no change to the status, so the only place the adjustment is visible is in the length of the array you got back &mdash; which is exactly the number the buggy predicate is reading.</p>
<p><strong>The short-page predicate has a premise you do not control.</strong> "Fewer items than I asked for means the end" is sound only when the server serves what you asked for. The effective page size is the minimum of your requested value, the endpoint's own maximum and the number of items remaining. Two of those three are GitHub's to change, and one of them changed the moment you typed a number above 100.</p>
<p><strong>Some endpoints enforce a smaller maximum than 100.</strong> The same clamping behaviour applies, at a lower number, so a client that has carefully hard-coded 100 as its page size can still receive a short full page and stop. This is why the check measures the effective page size against what came back rather than asserting a constant: a page that is shorter than requested <em>and</em> carries a <code>rel="next"</code> is the finding whatever the numbers happen to be.</p>
<p><strong>The <code>Link</code> header is the only authority on whether there is more.</strong> A response with <code>rel="next"</code> has more data behind it, at any page size, whether or not the page you are holding is full. A response without it does not. That predicate has no premise about page sizes in it at all, which is why it is the one to terminate on. Where <code>rel="last"</code> is missing from the header as well, <a href="/github/rel-last-absent/">that has its own consequences</a>.</p>
<p><strong>This is not the note about the default.</strong> Leaving <code>per_page</code> unset gets you 30 items a page and <a href="/github/per-page-default-30/">costs 3.3 times the requests</a>, which is a spending problem with a correct answer at the end of it. This one is a correctness problem: the answer is wrong and the job finished early and under budget. They are repaired by the same one-line change and they are not the same bug, and a team that has already set <code>per_page</code> has fixed the first while possibly introducing this one.</p>
<p><strong>The API cannot see your client, so the check proves the trap.</strong> Nothing GitHub returns says whether your loop terminates on a short page or on a missing <code>rel="next"</code>. What a read-only script can show is that the clamp happened on this endpoint, that the response is shorter than what was requested, and that there is more data on the far side of it. That is the trap being set, not you falling into it, and the script says so rather than accusing you of a bug it cannot see.</p>""",
"steps": [
 {"h": "Ask for more than the maximum on purpose",
  "body": """<p>Send the list request your integration sends, with <code>per_page=500</code>. One request. Count the items in the array that comes back: 100 is the clamp, plainly, in the one place it is ever visible. This is a deliberately abnormal request made once by a diagnostic, not something to leave in production code.</p>"""},
 {"h": "Read the Link header on that same response",
  "body": """<p>The clamp alone is not a finding. The clamp plus <code>rel="next"</code> is: it means the page you were served is shorter than the page you asked for <em>and</em> there is more behind it, which is precisely the state in which a short-page check stops early. If there is no <code>rel="next"</code>, this collection happens to end here and the trap is armed for whenever it grows.</p>"""},
 {"h": "Run both termination predicates side by side",
  "body": """<p>Evaluate "received fewer than requested" and "there is no <code>rel=&quot;next&quot;</code>" over the same response and print both. Where they disagree, the first one is the bug and the second one is the answer. Making the comparison explicit is worth more than the verdict, because it is the sentence that changes somebody's loop.</p>"""},
 {"h": "Set per_page to 100 and stop naming a bigger number",
  "body": """<p>100 is the maximum and asking for more buys nothing at all &mdash; not a bigger page, not fewer requests, not a warning that you asked. Writing 100 makes the effective page size and the requested page size the same number, which removes one of the two ways the short-page predicate can lie to you. It does not remove the other, which is why the next step exists.</p>"""},
 {"h": "Terminate on the header, then keep the check cheap",
  "body": """<p>Follow <code>rel="next"</code> until it is absent, and never construct the next URL yourself. The audit itself costs one request per path probed, three by default, against the hourly <code>core</code> quota &mdash; small enough to run on every deploy, and worth knowing before you point it at forty endpoints in a loop. <code>GET /rate_limit</code> will tell you what is left and does not itself consume any.</p>"""},
],
"verify": """<p>After the loop terminates on the header instead of on the page length, the same audit reports a full page with a next link and nothing to do.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_per_page_clamp.py --repo acme/monorepo
# read cost: 3 request(s) against the core hourly quota
# /repos/acme/monorepo/issues: asked for 500, received 100
# clamped-and-truncated: per_page=500 was reduced to 100 and rel="next" is
# present, so a client that stops on a short page stops here with more to read
# repair: send per_page=100 and terminate on the absence of rel="next"

# after the loop is changed to follow the header
GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_per_page_clamp.py --repo acme/monorepo --per-page 100
# within-cap-more-pages: asked for 100, received 100, rel="next" is present and
# the short-page check agrees with the header here</code></pre>""",
"code_intro": "One GET per probed path, asking on purpose for a page size that cannot be served. Everything that matters afterwards is two pure predicates evaluated over the same response: the one that asks whether the page was shorter than requested, and the one that asks whether the header still advertises a next page. The verdict is their disagreement, which means the entire rule can be tested offline and the network part is a thin shell around it. The cost of the run is computed and printed before any request is made, because a diagnostic in a section full of quota notes should say what it spends.",
"py_file": "github_per_page_clamp.py",
"py": '''"""Show that per_page above the maximum is reduced rather than refused.

Read only. One GET per probed path, plus one more per path with --confirm.
Nothing is written and the repair is printed rather than performed.

GitHub caps per_page at 100 and enforces the cap by silently lowering the value:
a request for 500 is served as a request for 100 with a success status and no
warning anywhere in the response. That is harmless on its own. It becomes data
loss in a client that decides it has reached the last page by noticing it got
fewer items than it asked for, because 100 is fewer than 500 and the loop stops
with four fifths of the collection unread.

What this can and cannot see: the API has no idea which predicate your client
terminates on. It can show that the clamp happened here and that there is more
data behind the shortened page. That is the trap, not the fall.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_per_page_clamp")

API = "https://api.github.com"
UA = "github-per-page-clamp/1.0"

# The documented ceiling on a page. Named rather than inlined because it turns up
# in the output and a reader comparing this against the documentation should find
# it in one place.
MAX_PER_PAGE = 100

# Anchored on the angle brackets rather than split on commas. A pagination URL
# can contain a comma of its own, labels=bug,ci being the everyday case, and
# splitting the header on commas turns one good link into two broken ones.
LINK = re.compile(r'<([^>]+)>\\s*;\\s*rel="([^"]+)"')

PROBES = ["issues", "pulls", "branches"]


def parse_link(header):
    """Parse a Link header into {rel: url}. Pure."""
    if not header:
        return {}
    return {rel: url for url, rel in LINK.findall(header)}


def clamped_to(requested):
    """The page size GitHub will actually use for this request. Pure.

    None for anything that is not a usable page size, so a bad argument is
    reported rather than silently treated as a finding.
    """
    try:
        n = int(requested)
    except (TypeError, ValueError):
        return None
    if n < 1:
        return None
    return min(n, MAX_PER_PAGE)


def is_over_maximum(requested):
    """Whether this value will be lowered before it is served. Pure."""
    try:
        return int(requested) > MAX_PER_PAGE
    except (TypeError, ValueError):
        return False


def stops_on_short_page(requested, received):
    """The buggy predicate: fewer items than asked for, so that was the end.

    Pure, and written out under its own name on purpose. It is the whole bug,
    and it is much easier to argue about when it is a function with a name than
    when it is an inequality inside somebody's while loop.
    """
    size = clamped_to(requested)
    try:
        got = int(received)
    except (TypeError, ValueError):
        return False
    if size is None:
        return False
    try:
        return got < int(requested)
    except (TypeError, ValueError):
        return False


def stops_on_missing_next(links):
    """The correct predicate: the header no longer advertises a next page. Pure."""
    return "next" not in (links or {})


def predicates_disagree(requested, received, links):
    """Whether the short-page check would stop while the header says otherwise."""
    return stops_on_short_page(requested, received) and not stops_on_missing_next(links)


def verdict(requested, received, links):
    """Classify one response. Pure. Returns (state, detail).

    The states keep two kinds of short page apart. One is losing data right now.
    The other is a collection that happens to end on the boundary, which is the
    same trap with the spring not yet released.
    """
    size = clamped_to(requested)
    if size is None or received is None:
        return ("unknown",
                "the request was not answered in a form this check can read.")
    try:
        got = int(received)
    except (TypeError, ValueError):
        return ("unknown",
                "the request was not answered in a form this check can read.")
    more = not stops_on_missing_next(links)
    over = is_over_maximum(requested)

    if predicates_disagree(requested, received, links):
        if over and got == MAX_PER_PAGE:
            return ("clamped-and-truncated",
                    'per_page=%s was reduced to %d and rel="next" is present, so '
                    "a client that stops on a short page stops here with more to "
                    "read." % (requested, MAX_PER_PAGE))
        return ("smaller-maximum",
                "per_page=%s was asked for and %d item(s) came back with "
                'rel="next" still present, so this endpoint serves a smaller '
                "page than you requested and a short-page check stops here too."
                % (requested, got))
    if over and got == MAX_PER_PAGE:
        return ("clamped-at-boundary",
                "per_page=%s was reduced to %d and there is no next page, so "
                "this collection happens to end exactly on the boundary. The "
                "clamp is real and the truncation starts on item %d."
                % (requested, MAX_PER_PAGE, MAX_PER_PAGE + 1))
    if over:
        return ("clamped-untested",
                "per_page=%s was reduced to %d, but only %d item(s) exist here, "
                "so the truncation cannot be shown on this path. The clamp still "
                "applies to every path that grows past %d."
                % (requested, MAX_PER_PAGE, got, MAX_PER_PAGE))
    if more:
        return ("within-cap-more-pages",
                'per_page=%s was served in full and rel="next" is present. The '
                "short-page check agrees with the header here, which is luck "
                "rather than correctness." % requested)
    return ("within-cap-complete",
            "per_page=%s was served in full and there is no next page. One "
            "request really is the whole list here." % requested)


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state in ("clamped-and-truncated", "clamped-at-boundary", "clamped-untested"):
        return ("send per_page=100 and terminate on the absence of rel=\\"next\\" "
                "in the Link header. Asking for more than 100 buys nothing: not "
                "a bigger page, not fewer requests, not an error telling you so.")
    if state == "smaller-maximum":
        return ("this endpoint serves a smaller page than 100, so hard-coding "
                "any page size as your terminating condition is unsafe here. "
                "Follow rel=\\"next\\" until it is absent.")
    if state == "within-cap-more-pages":
        return ("nothing on the page size. Check that the loop terminates on "
                "the missing rel=\\"next\\" rather than on the page length: the "
                "two agree on this response and will part company on a clamp.")
    if state == "within-cap-complete":
        return "nothing."
    return "point the check at a path this token can list."


def read_cost(paths, confirm=False):
    """Requests this run will spend against the core quota. Pure."""
    n = len(paths or [])
    return n * (2 if confirm else 1)


def get(session, path, params):
    """One GET. Returns (status, items-or-None, links)."""
    r = session.get(API + path, params=params, timeout=30)
    links = parse_link(r.headers.get("Link"))
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    if r.status_code != 200:
        log.info("%s returned %d; skipping it", path, r.status_code)
        return r.status_code, None, links
    try:
        body = r.json()
    except ValueError:
        return r.status_code, None, links
    return r.status_code, body if isinstance(body, list) else None, links


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--path", action="append",
                    help="probe this API path instead of the defaults, e.g. "
                         "/repos/o/n/releases. Repeatable.")
    ap.add_argument("--per-page", type=int, default=500,
                    help="the page size to ask for. The default is deliberately "
                         "above the maximum, which is the whole point.")
    ap.add_argument("--confirm", action="store_true",
                    help="spend a second request per path at per_page=100 to "
                         "show the honest page size beside the clamped one")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    paths = args.path or ["/repos/%s/%s" % (args.repo, name) for name in PROBES]
    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(paths, args.confirm))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for path in paths:
        status, items, links = get(session, path, {"per_page": args.per_page})
        if items is None:
            continue
        state, detail = verdict(args.per_page, len(items), links)
        log.info("%s: asked for %s, received %d", path, args.per_page, len(items))
        log.info("%s: %s", state, detail)
        log.info("repair: %s", repair(state))

        honest = None
        if args.confirm:
            _s, confirmed, _l = get(session, path, {"per_page": MAX_PER_PAGE})
            honest = len(confirmed) if confirmed is not None else None
            if honest is not None:
                log.info("%s: at per_page=%d the same call returns %d item(s)",
                         path, MAX_PER_PAGE, honest)

        findings.append({
            "path": path,
            "status": status,
            "requested": args.per_page,
            "effective_page_size": clamped_to(args.per_page),
            "received": len(items),
            "rels": sorted(links),
            "short_page_check_stops": stops_on_short_page(args.per_page, len(items)),
            "header_check_stops": stops_on_missing_next(links),
            "predicates_disagree": predicates_disagree(args.per_page, len(items), links),
            "at_per_page_100": honest,
            "state": state,
            "detail": detail,
        })

    print(json.dumps({"requests_spent": read_cost(paths, args.confirm),
                      "findings": findings}, indent=2, default=str))
    bad = {"clamped-and-truncated", "smaller-maximum", "clamped-at-boundary"}
    return 1 if any(f["state"] in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-per-page-clamp.mjs",
"js": '''/**
 * Show that per_page above the maximum is reduced rather than refused.
 *
 * Read only. One GET per probed path, plus one more per path when
 * GITHUB_CONFIRM is set. Nothing is written and the repair is printed rather
 * than performed.
 *
 * Environment:
 *   GITHUB_TOKEN     a token with read access to the repository
 *   GITHUB_REPO      owner/name
 *   GITHUB_PER_PAGE  the page size to ask for, default 500
 *   GITHUB_CONFIRM   set to spend a second request per path at per_page=100
 */
const API = 'https://api.github.com';
const UA = 'github-per-page-clamp/1.0';

/** The documented ceiling on a page. */
export const MAX_PER_PAGE = 100;

// Anchored on the angle brackets rather than split on commas: a pagination URL
// can contain a comma of its own, and splitting on it breaks the link.
const LINK = /<([^>]+)>\\s*;\\s*rel="([^"]+)"/g;

const PROBES = ['issues', 'pulls', 'branches'];

/** Parse a Link header into {rel: url}. Pure. */
export function parseLink(header) {
  const out = {};
  if (!header) return out;
  for (const m of String(header).matchAll(LINK)) out[m[2]] = m[1];
  return out;
}

/** The page size GitHub will actually use for this request. Pure. */
export function clampedTo(requested) {
  const n = Number(requested);
  if (!Number.isFinite(n) || Math.trunc(n) < 1) return null;
  return Math.min(Math.trunc(n), MAX_PER_PAGE);
}

/** Whether this value will be lowered before it is served. Pure. */
export function isOverMaximum(requested) {
  const n = Number(requested);
  return Number.isFinite(n) && n > MAX_PER_PAGE;
}

/** The buggy predicate: fewer items than asked for, so that was the end. Pure. */
export function stopsOnShortPage(requested, received) {
  const size = clampedTo(requested);
  const got = Number(received);
  if (size === null || !Number.isFinite(got)) return false;
  return got < Number(requested);
}

/** The correct predicate: the header no longer advertises a next page. Pure. */
export function stopsOnMissingNext(links) {
  return !(links && Object.prototype.hasOwnProperty.call(links, 'next'));
}

/** Whether the short-page check would stop while the header says otherwise. */
export function predicatesDisagree(requested, received, links) {
  return stopsOnShortPage(requested, received) && !stopsOnMissingNext(links);
}

/** Classify one response. Pure. Returns [state, detail]. */
export function verdict(requested, received, links) {
  const size = clampedTo(requested);
  const got = Number(received);
  if (size === null || received === null || received === undefined || !Number.isFinite(got)) {
    return ['unknown', 'the request was not answered in a form this check can read.'];
  }
  const more = !stopsOnMissingNext(links);
  const over = isOverMaximum(requested);

  if (predicatesDisagree(requested, received, links)) {
    if (over && got === MAX_PER_PAGE) {
      return ['clamped-and-truncated',
        `per_page=${requested} was reduced to ${MAX_PER_PAGE} and rel="next" is `
        + 'present, so a client that stops on a short page stops here with more '
        + 'to read.'];
    }
    return ['smaller-maximum',
      `per_page=${requested} was asked for and ${got} item(s) came back with `
      + 'rel="next" still present, so this endpoint serves a smaller page than '
      + 'you requested and a short-page check stops here too.'];
  }
  if (over && got === MAX_PER_PAGE) {
    return ['clamped-at-boundary',
      `per_page=${requested} was reduced to ${MAX_PER_PAGE} and there is no next `
      + 'page, so this collection happens to end exactly on the boundary. The '
      + `clamp is real and the truncation starts on item ${MAX_PER_PAGE + 1}.`];
  }
  if (over) {
    return ['clamped-untested',
      `per_page=${requested} was reduced to ${MAX_PER_PAGE}, but only ${got} `
      + 'item(s) exist here, so the truncation cannot be shown on this path. The '
      + `clamp still applies to every path that grows past ${MAX_PER_PAGE}.`];
  }
  if (more) {
    return ['within-cap-more-pages',
      `per_page=${requested} was served in full and rel="next" is present. The `
      + 'short-page check agrees with the header here, which is luck rather than '
      + 'correctness.'];
  }
  return ['within-cap-complete',
    `per_page=${requested} was served in full and there is no next page. One `
    + 'request really is the whole list here.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (['clamped-and-truncated', 'clamped-at-boundary', 'clamped-untested'].includes(state)) {
    return 'send per_page=100 and terminate on the absence of rel="next" in the '
      + 'Link header. Asking for more than 100 buys nothing: not a bigger page, '
      + 'not fewer requests, not an error telling you so.';
  }
  if (state === 'smaller-maximum') {
    return 'this endpoint serves a smaller page than 100, so hard-coding any '
      + 'page size as your terminating condition is unsafe here. Follow '
      + 'rel="next" until it is absent.';
  }
  if (state === 'within-cap-more-pages') {
    return 'nothing on the page size. Check that the loop terminates on the '
      + 'missing rel="next" rather than on the page length: the two agree on '
      + 'this response and will part company on a clamp.';
  }
  if (state === 'within-cap-complete') return 'nothing.';
  return 'point the check at a path this token can list.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(paths, confirm = false) {
  const n = Array.isArray(paths) ? paths.length : 0;
  return n * (confirm ? 2 : 1);
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const res = await fetch(url, { headers: headers(token) });
  const links = parseLink(res.headers.get('link'));
  if (!res.ok) return { status: res.status, items: null, links };
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, items: Array.isArray(body) ? body : null, links };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO=owner/name');
    process.exitCode = 2;
    return;
  }
  const perPage = Number(process.env.GITHUB_PER_PAGE || 500);
  const confirm = Boolean(process.env.GITHUB_CONFIRM);
  const paths = PROBES.map((name) => `/repos/${repo}/${name}`);
  console.log(`read cost: ${readCost(paths, confirm)} request(s) against the core hourly quota`);

  const findings = [];
  for (const path of paths) {
    const { status, items, links } = await get(token, path, { per_page: perPage });
    if (items === null) {
      console.log(`${path} returned ${status}; skipping it`);
      continue;
    }
    const [state, detail] = verdict(perPage, items.length, links);
    console.log(`${path}: asked for ${perPage}, received ${items.length}`);
    console.log(`${state}: ${detail}`);
    console.log(`repair: ${repair(state)}`);

    let honest = null;
    if (confirm) {
      const second = await get(token, path, { per_page: MAX_PER_PAGE });
      honest = second.items === null ? null : second.items.length;
      if (honest !== null) {
        console.log(`${path}: at per_page=${MAX_PER_PAGE} the same call returns ${honest} item(s)`);
      }
    }

    findings.push({
      path,
      status,
      requested: perPage,
      effective_page_size: clampedTo(perPage),
      received: items.length,
      rels: Object.keys(links).sort(),
      short_page_check_stops: stopsOnShortPage(perPage, items.length),
      header_check_stops: stopsOnMissingNext(links),
      predicates_disagree: predicatesDisagree(perPage, items.length, links),
      at_per_page_100: honest,
      state,
      detail,
    });
  }

  console.log(JSON.stringify({ requests_spent: readCost(paths, confirm), findings }, null, 2));
  const bad = ['clamped-and-truncated', 'smaller-maximum', 'clamped-at-boundary'];
  process.exitCode = findings.some((f) => bad.includes(f.state)) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two predicates get the most attention, because the note is entirely about the gap between them: the short-page check has to be wrong on a clamped response and right on a full one, the header check has to be indifferent to page sizes altogether, and their disagreement has to be exactly the finding. After that, the clamp arithmetic at and around the boundary, the distinction between a truncation happening now and one waiting for the collection to grow, an endpoint whose own maximum is below 100, and the read cost, which is asserted because a diagnostic that quietly doubles its request count is a bad citizen in a section full of quota notes.",
"test_py_file": "test_github_per_page_clamp.py",
"test_py": '''from github_per_page_clamp import (
    MAX_PER_PAGE, clamped_to, is_over_maximum, parse_link, predicates_disagree,
    read_cost, repair, stops_on_missing_next, stops_on_short_page, verdict,
)

MORE = {"next": "https://api.github.com/repositories/1/issues?page=2"}
END = {"prev": "https://api.github.com/repositories/1/issues?page=3"}


def test_the_clamp_is_a_minimum_not_a_rejection():
    assert clamped_to(500) == MAX_PER_PAGE
    assert clamped_to(101) == MAX_PER_PAGE
    assert clamped_to(100) == 100
    assert clamped_to(30) == 30
    assert clamped_to("50") == 50


def test_a_page_size_that_is_not_one_is_reported_rather_than_guessed():
    assert clamped_to(0) is None
    assert clamped_to(-5) is None
    assert clamped_to(None) is None
    assert clamped_to("many") is None


def test_only_values_above_the_maximum_are_lowered():
    assert is_over_maximum(500)
    assert is_over_maximum(101)
    assert not is_over_maximum(100)
    assert not is_over_maximum(None)


def test_the_short_page_check_is_wrong_on_a_clamped_response():
    assert stops_on_short_page(500, 100)
    assert not stops_on_short_page(100, 100)
    assert stops_on_short_page(100, 42)


def test_the_header_check_does_not_care_about_page_sizes():
    assert not stops_on_missing_next(MORE)
    assert stops_on_missing_next(END)
    assert stops_on_missing_next({})
    assert stops_on_missing_next(None)


def test_the_finding_is_exactly_the_disagreement():
    assert predicates_disagree(500, 100, MORE)
    assert not predicates_disagree(500, 100, END)
    assert not predicates_disagree(100, 100, MORE)


def test_a_clamped_page_with_more_behind_it_is_the_finding():
    state, detail = verdict(500, 100, MORE)
    assert state == "clamped-and-truncated"
    assert "reduced to 100" in detail
    assert "stops on a short page" in detail


def test_a_collection_that_ends_on_the_boundary_is_still_a_trap():
    state, detail = verdict(500, 100, END)
    assert state == "clamped-at-boundary"
    assert "item 101" in detail


def test_a_small_collection_cannot_prove_the_clamp():
    state, detail = verdict(500, 12, {})
    assert state == "clamped-untested"
    assert "cannot be shown on this path" in detail


def test_an_endpoint_with_a_smaller_maximum_is_named_separately():
    state, detail = verdict(100, 50, MORE)
    assert state == "smaller-maximum"
    assert "smaller page than you requested" in detail


def test_a_full_page_within_the_cap_is_not_a_finding():
    assert verdict(100, 100, MORE)[0] == "within-cap-more-pages"
    assert verdict(100, 100, END)[0] == "within-cap-complete"
    assert verdict(30, 11, {})[0] == "within-cap-complete"


def test_an_unreadable_response_is_not_reported_as_a_clamp():
    assert verdict(500, None, MORE)[0] == "unknown"
    assert verdict(None, 100, MORE)[0] == "unknown"


def test_the_link_header_survives_a_comma_inside_a_url():
    header = ('<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=2>; rel="next", '
              '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=9>; rel="last"')
    links = parse_link(header)
    assert set(links) == {"next", "last"}
    assert links["next"].endswith("page=2")
    assert parse_link(None) == {}


def test_the_repair_never_suggests_asking_for_more_than_the_maximum():
    for state in ("clamped-and-truncated", "clamped-at-boundary", "clamped-untested"):
        assert "per_page=100" in repair(state)
        assert "500" not in repair(state)
    assert "smaller page than 100" in repair("smaller-maximum")
    assert repair("within-cap-complete") == "nothing."


def test_the_run_says_what_it_will_spend():
    assert read_cost(["/a", "/b", "/c"]) == 3
    assert read_cost(["/a", "/b", "/c"], confirm=True) == 6
    assert read_cost([]) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-per-page-clamp.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  MAX_PER_PAGE, clampedTo, isOverMaximum, parseLink, predicatesDisagree,
  readCost, repair, stopsOnMissingNext, stopsOnShortPage, verdict,
} from './github-per-page-clamp.mjs';

const MORE = { next: 'https://api.github.com/repositories/1/issues?page=2' };
const END = { prev: 'https://api.github.com/repositories/1/issues?page=3' };

test('the clamp is a minimum, not a rejection', () => {
  assert.equal(clampedTo(500), MAX_PER_PAGE);
  assert.equal(clampedTo(101), MAX_PER_PAGE);
  assert.equal(clampedTo(100), 100);
  assert.equal(clampedTo(30), 30);
  assert.equal(clampedTo('50'), 50);
});

test('a page size that is not one is reported rather than guessed', () => {
  assert.equal(clampedTo(0), null);
  assert.equal(clampedTo(-5), null);
  assert.equal(clampedTo(null), null);
  assert.equal(clampedTo('many'), null);
});

test('only values above the maximum are lowered', () => {
  assert.ok(isOverMaximum(500));
  assert.ok(isOverMaximum(101));
  assert.ok(!isOverMaximum(100));
  assert.ok(!isOverMaximum(null));
});

test('the short-page check is wrong on a clamped response', () => {
  assert.ok(stopsOnShortPage(500, 100));
  assert.ok(!stopsOnShortPage(100, 100));
  assert.ok(stopsOnShortPage(100, 42));
});

test('the header check does not care about page sizes', () => {
  assert.ok(!stopsOnMissingNext(MORE));
  assert.ok(stopsOnMissingNext(END));
  assert.ok(stopsOnMissingNext({}));
  assert.ok(stopsOnMissingNext(null));
});

test('the finding is exactly the disagreement', () => {
  assert.ok(predicatesDisagree(500, 100, MORE));
  assert.ok(!predicatesDisagree(500, 100, END));
  assert.ok(!predicatesDisagree(100, 100, MORE));
});

test('a clamped page with more behind it is the finding', () => {
  const [state, detail] = verdict(500, 100, MORE);
  assert.equal(state, 'clamped-and-truncated');
  assert.match(detail, /reduced to 100/);
  assert.match(detail, /stops on a short page/);
});

test('a collection that ends on the boundary is still a trap', () => {
  const [state, detail] = verdict(500, 100, END);
  assert.equal(state, 'clamped-at-boundary');
  assert.match(detail, /item 101/);
});

test('a small collection cannot prove the clamp', () => {
  const [state, detail] = verdict(500, 12, {});
  assert.equal(state, 'clamped-untested');
  assert.match(detail, /cannot be shown on this path/);
});

test('an endpoint with a smaller maximum is named separately', () => {
  const [state, detail] = verdict(100, 50, MORE);
  assert.equal(state, 'smaller-maximum');
  assert.match(detail, /smaller page than you requested/);
});

test('a full page within the cap is not a finding', () => {
  assert.equal(verdict(100, 100, MORE)[0], 'within-cap-more-pages');
  assert.equal(verdict(100, 100, END)[0], 'within-cap-complete');
  assert.equal(verdict(30, 11, {})[0], 'within-cap-complete');
});

test('an unreadable response is not reported as a clamp', () => {
  assert.equal(verdict(500, null, MORE)[0], 'unknown');
  assert.equal(verdict(null, 100, MORE)[0], 'unknown');
});

test('the Link header survives a comma inside a URL', () => {
  const header = '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=2>; rel="next", '
    + '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=9>; rel="last"';
  const links = parseLink(header);
  assert.deepEqual(Object.keys(links).sort(), ['last', 'next']);
  assert.ok(links.next.endsWith('page=2'));
  assert.deepEqual(parseLink(null), {});
});

test('the repair never suggests asking for more than the maximum', () => {
  for (const state of ['clamped-and-truncated', 'clamped-at-boundary', 'clamped-untested']) {
    assert.match(repair(state), /per_page=100/);
    assert.ok(!repair(state).includes('500'));
  }
  assert.match(repair('smaller-maximum'), /smaller page than 100/);
  assert.equal(repair('within-cap-complete'), 'nothing.');
});

test('the run says what it will spend', () => {
  assert.equal(readCost(['/a', '/b', '/c']), 3);
  assert.equal(readCost(['/a', '/b', '/c'], true), 6);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("Why does GitHub not return a 422 for per_page=500?",
  "Because rejecting it would break clients that have been sending an oversized value harmlessly for years, and because the cap is a serving decision rather than a validation rule: the request is answerable, just not at the size asked for. Whatever the reasoning, the practical consequence for you is fixed. There is no signal in the response that the value was adjusted, so a client cannot detect the clamp except by counting items, which is exactly the operation the bug is hiding inside."),
 ("Is this the same problem as leaving per_page unset?",
  "No, and it is worth keeping them apart because the symptoms are opposite. An unset per_page gives you pages of 30 and costs 3.3 times the requests for a correct answer; that is a spending problem and it has its own note. This one costs you nothing extra and gives you a wrong answer, because the job stops early and under budget. The same one-line change repairs both, and a team that has already set per_page has fixed the first while possibly walking into this one."),
 ("Our loop stops on a short page and it has always worked. Why?",
  "Because your page size has always been at or below 100, so the effective page size and the requested page size were the same number and the predicate happened to be right. It is right by coincidence rather than by construction. It breaks in three ways: somebody raises the value above 100, an endpoint enforces its own lower maximum, or a future response is short for a reason nobody anticipated. Terminating on the missing rel=\"next\" has no premise about page sizes in it at all."),
 ("How much quota does the check itself cost?",
  "One request per path probed, three by default, against the hourly core bucket. With --confirm it is two per path, because the second request re-runs the same call at per_page=100 so the honest page size can be printed beside the clamped one. The script computes and prints that number before it makes any request, so pointing it at forty paths in a loop is a decision rather than an accident. GET /rate_limit will tell you what is left and does not itself consume any."),
 ("Can the script tell whether my client actually has this bug?",
  "No, and it does not claim to. Nothing GitHub returns says which predicate your loop terminates on, or whether it has a loop at all. What the script proves is that on this endpoint the value was clamped, that the page came back shorter than requested, and that there is more data behind it. That is the trap being set. Whether your client falls into it is a question about your code, and the printed comparison of the two predicates is there so you can answer it in a minute by reading your own loop."),
],
"related": [
 ("/github/per-page-default-30/", "per_page is unset and every list costs more"),
 ("/github/link-header-not-followed/", "Only the first page is ever read"),
 ("/github/rel-last-absent/", "The Link header has no rel=last"),
],
"citations": [CITE_PAGINATION, CITE_BEST_PRACTICES, CITE_ISSUES, CITE_PAGINATE_PLUGIN],
},

{
"slug": "rel-last-absent",
"title": "The Link header has no rel=last so the page count breaks",
"description": "GitHub only sends rel=last when it can compute a final page. Where it cannot, a pager that indexes pages or draws a progress bar reads one page and stops.",
"h1": "the Link header has no rel=last so the page count breaks",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github link header no rel last",
             "github api rel last missing pagination",
             "github api page count from link header",
             "github pagination progress bar total pages",
             "github link header rel next only"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The pager was written properly. It reads the <code>Link</code> header, it pulls the page number out of <code>rel=\"last\"</code>, and it uses that number to size the job before it starts: a progress bar, a worker pool over the page range, an estimate in the log line. On one endpoint the header comes back with a <code>rel=\"next\"</code> and no <code>rel=\"last\"</code> at all, and the job reports that it read one page of a one-page collection. It read one page of nine hundred.",
"short_answer": """<p>GitHub includes <code>rel="last"</code> in the <code>Link</code> header only when it can calculate the final page. On some endpoints it cannot, and the header comes back carrying <code>rel="next"</code> and nothing that tells you how far the list goes.</p>
<p>That is fine for a pager that walks the list, and fatal for one that indexes it. Any code that computes a page count, fans out over <code>range(1, last + 1)</code>, draws a progress bar or jumps to the final page for the oldest record depends on a field the API does not promise. The repair is to drive pagination off <code>rel="next"</code> alone and treat its absence as the terminating condition, and to treat a page count as a display nicety that is sometimes unavailable rather than as an input to the loop.</p>""",
"problem": """<p>This one hurts because the code is good. Reading the header is the correct instinct, and a developer who has got as far as parsing <code>Link</code> has already avoided the common bug. They then do the natural next thing, which is to use the richest field in the header, and build the whole shape of the job around a number that is usually there.</p>
<p>The two ways it fails are very different and only one of them is survivable. If the code does <code>int(links["last"])</code> it raises a <code>KeyError</code>, someone sees a stack trace, and it is fixed the same afternoon. If it does <code>last = page_of(links.get("last")) or 1</code> &mdash; and it usually does, because somebody hit the <code>KeyError</code> in staging and made it safe &mdash; then a missing page count silently becomes a page count of one. The job runs, reports success, and reads the first thirty items of a list that has no visible end.</p>
<p>It is endpoint-specific, so it survives every test you have. The pager works against issues, works against pull requests, works against branches, and is quietly wrong on the one endpoint in your set that cannot be indexed. Nobody suspects the pager, because the pager is the tested part. The suspicion lands on the endpoint, which gets described as returning nothing, and on the token, which gets rotated.</p>""",
"why": """<p><strong>A final page is a computation, not a fact.</strong> To say which page is last, GitHub has to know the total size of the result set at the moment of the request. Where that number is expensive, unbounded or genuinely unknown &mdash; high-volume feeds, cursor-based endpoints, anything counted lazily &mdash; it does not produce one, and the honest response is to omit the field rather than to invent it. So the presence of <code>rel="last"</code> is a property of the endpoint and the query, not a guarantee of the API.</p>
<p><strong>Walking and indexing are different capabilities.</strong> An endpoint that gives you <code>rel="last"</code> supports four things: a page count, a progress bar, a fan-out over page numbers, and a jump to the end for the oldest or newest record. An endpoint that gives you only <code>rel="next"</code> supports exactly one: walking it. Sorting your endpoints into those two groups is the whole of this check, and it is the thing to know <em>before</em> you design the job, not after it under-reports.</p>
<p><strong>Even where it exists, the number moves.</strong> <code>rel="last"</code> is computed per request. Between page one and page nine, issues get opened and closed, branches get deleted, and the final page number changes underneath a loop that captured it once. Caching it as the size of the job is a smaller version of the same mistake: it is a snapshot presented as a bound.</p>
<p><strong>The terminating condition never needed it.</strong> The absence of <code>rel="next"</code> is the end of the list, on every endpoint, at every page size, whether or not a final page can be computed. It is a strictly weaker requirement, it is always available, and a loop built on it does not need to know how long it is going to run.</p>
<p><strong>This is not the note about ignoring the header.</strong> The <a href="/github/link-header-not-followed/">first-page-only bug</a> is a client that never looked at <code>Link</code> at all, and it is the most common silent failure on this API. This one is a client that does look, does follow, and requires a field the header does not always carry. Both end with an under-count, and the code that produces them looks nothing alike.</p>
<p><strong>The check proves the endpoint's shape, not your loop's.</strong> A read-only script can say which of your endpoints hand back a final page and which do not. It cannot see whether your pager needs one. So it prints the capability list rather than a verdict about your code, and it computes the page count both the careful way and the careless way so you can see the two answers differ.</p>""",
"steps": [
 {"h": "Ask each endpoint for one item and read only the header",
  "body": """<p><code>per_page=1</code> is the cheapest possible probe, and none of the items are read. Where <code>rel="last"</code> is present, its <code>page</code> number at that page size is also the exact item count, which is a useful free byproduct. Where it is absent, that absence is the finding.</p>"""},
 {"h": "Sort the endpoints into indexable and walk-only",
  "body": """<p>Three states, not two. <code>rel="last"</code> present means the endpoint can be indexed. <code>rel="next"</code> present with no <code>rel="last"</code> means it can only be walked. Neither present means one page really is the whole list. The middle state is the one this note exists for and the one a boolean check would swallow.</p>"""},
 {"h": "Compute the page count twice on purpose",
  "body": """<p>Once carefully, returning nothing when the field is missing, and once the way tired code does it, defaulting a missing value to <code>1</code>. Printing both next to each other turns an abstract warning into a number: the careful answer is <code>unknown</code> and the careless answer is <code>1 page</code>, and only one of those will make somebody go and look at their loop.</p>"""},
 {"h": "Name the patterns that stop working",
  "body": """<p>A progress bar with no denominator, a worker pool with no range to divide, a jump to the last page for the oldest record, and any log line that says page 3 of 40. On a walk-only endpoint all four are unavailable, and knowing that before the job is written is much cheaper than discovering it from a report that says one page.</p>"""},
 {"h": "Drive the loop off rel=next and nothing else",
  "body": """<p>Follow the <code>next</code> URL exactly as given until there is no <code>next</code>, and never rebuild it by hand. In Octokit that is <code>octokit.paginate()</code>; in PyGithub it is iterating the <code>PaginatedList</code> rather than asking it for a length. The probe costs one request per path, five by default, against the hourly <code>core</code> quota.</p>"""},
],
"verify": """<p>Once the pager terminates on the missing <code>next</code>, the walk-only endpoint stops being a special case and the audit becomes a description of the endpoints rather than a warning about them.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_rel_last_absent.py --repo acme/monorepo
# read cost: 5 request(s) against the core hourly quota
# /repos/acme/monorepo/issues: rels next, last -> indexable, 912 page(s) at per_page=1
# /repos/acme/monorepo/events: rels next -> walk-only
# walk-only: rel="next" is present and rel="last" is not, so the size of this
# list is only knowable by walking it. A careful page count says unknown here;
# code that defaults a missing count to 1 reports 1 page
# unavailable here: page count, progress bar, parallel fan-out, jump to last
# repair: terminate on the absence of rel="next" and never require rel="last"</code></pre>""",
"code_intro": "One GET per probed path at the smallest page size there is, because the entire finding lives in a response header and not one item is read. The header is turned into a capability list rather than a boolean, since walk-only is a real and workable state and not an error. The script also models the bug directly: it computes the page count the careful way, which returns nothing when the field is absent, beside the careless way, which returns one, so the two can be printed disagreeing. Both are pure, so the rule is tested without a network.",
"py_file": "github_rel_last_absent.py",
"py": '''"""Sort GitHub list endpoints into the ones you can index and the ones you can only walk.

Read only. One GET per probed path at per_page=1, which is the cheapest request
that still produces a Link header. No items are read and nothing is written.

GitHub includes rel="last" only when it can calculate a final page. On some
endpoints it cannot, so the header carries rel="next" and no way to know how far
the list goes. A pager that walks the list is unaffected. A pager that indexes it
-- a progress bar, a fan-out over a page range, a jump to the last page -- either
raises on the missing key or, far more often, defaults the missing count to 1 and
reports a single page as the whole collection.

What this can and cannot see: the API cannot tell whether your pager needs a page
count. It can say which of your endpoints will give you one. That is why the
output is a capability list rather than an accusation.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import json
import logging
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_rel_last_absent")

API = "https://api.github.com"
UA = "github-rel-last-absent/1.0"

# Anchored on the angle brackets rather than split on commas, because a
# pagination URL can carry a comma of its own inside a query parameter.
LINK = re.compile(r'<([^>]+)>\\s*;\\s*rel="([^"]+)"')

PROBES = ["issues", "pulls", "branches", "events", "commits"]

# What each shape of header actually supports. Written as data rather than as a
# chain of ifs because the point of the script is the table, not the verdict.
CAPABILITIES = {
    "indexable": {"walk": True, "page_count": True, "progress_bar": True,
                  "parallel_fanout": True, "jump_to_last": True},
    "walk-only": {"walk": True, "page_count": False, "progress_bar": False,
                  "parallel_fanout": False, "jump_to_last": False},
    "single-page": {"walk": True, "page_count": True, "progress_bar": True,
                    "parallel_fanout": False, "jump_to_last": False},
}

PATTERN_NAMES = {
    "page_count": "page count",
    "progress_bar": "progress bar",
    "parallel_fanout": "parallel fan-out",
    "jump_to_last": "jump to last",
}


def parse_link(header):
    """Parse a Link header into {rel: url}. Pure."""
    if not header:
        return {}
    return {rel: url for url, rel in LINK.findall(header)}


def rels(links):
    """The rel names present, sorted. Pure, and the whole evidence base."""
    return sorted(links or {})


def page_param(url):
    """The page query parameter on a pagination URL, or None. Pure."""
    if not url:
        return None
    values = parse_qs(urlparse(url).query).get("page") or []
    try:
        return int(values[0])
    except (IndexError, TypeError, ValueError):
        return None


def pagination_style(links):
    """One of indexable, walk-only, single-page. Pure.

    Three states rather than two on purpose. A boolean check collapses walk-only
    into single-page, which is exactly the mistake this note is about.
    """
    links = links or {}
    if "last" in links:
        return "indexable"
    if "next" in links:
        return "walk-only"
    return "single-page"


def page_count(links):
    """The number of pages, or None where it cannot be known. Pure.

    None is the honest answer on a walk-only endpoint, and callers are expected
    to handle it rather than coerce it.
    """
    if pagination_style(links) == "single-page":
        return 1
    return page_param((links or {}).get("last"))


def naive_page_count(links):
    """The page count the careless way: a missing value becomes 1. Pure.

    This is not a helper. It is the bug, kept under its own name so the script
    can print it beside the careful answer and let the difference do the work.
    """
    return page_count(links) or 1


def item_count(links, per_page):
    """Total items, but only where the endpoint can be indexed. Pure."""
    pages = page_count(links)
    try:
        size = int(per_page)
    except (TypeError, ValueError):
        return None
    if pages is None or size != 1:
        return None
    return pages


def capabilities(style):
    """What a pager may rely on against an endpoint of this shape. Pure."""
    return dict(CAPABILITIES.get(style, CAPABILITIES["walk-only"]))


def unavailable(style):
    """The named patterns that do not work here, in a fixed order. Pure."""
    caps = capabilities(style)
    return [PATTERN_NAMES[k] for k in ("page_count", "progress_bar",
                                       "parallel_fanout", "jump_to_last")
            if not caps[k]]


def verdict(links, per_page=1):
    """Classify one endpoint's header. Pure. Returns (state, detail)."""
    style = pagination_style(links)
    if style == "walk-only":
        return (style,
                'rel="next" is present and rel="last" is not, so the size of '
                "this list is only knowable by walking it. A careful page count "
                "says unknown here; code that defaults a missing count to 1 "
                "reports %d page." % naive_page_count(links))
    if style == "indexable":
        total = item_count(links, per_page)
        return (style,
                'rel="last" is present, so this endpoint can be indexed: %s '
                "page(s) at per_page=%s%s. That number is computed per request "
                "and moves between calls, so it is a display value rather than "
                "a bound." % (page_count(links), per_page,
                              ", which is %d item(s)" % total if total else ""))
    return (style,
            'neither rel="next" nor rel="last" is present. One request is the '
            "whole list here, and nothing about paging applies.")


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "walk-only":
        return ('terminate on the absence of rel="next" and never require '
                'rel="last". Drop the progress bar or make it indeterminate, '
                "and replace any fan-out over a page range with a sequential "
                "walk that follows the next URL exactly as given.")
    if state == "indexable":
        return ('nothing, provided rel="last" is treated as a snapshot. Do not '
                "cache it as the size of the job, and do not let its absence on "
                "some other endpoint default to 1.")
    return "nothing."


def read_cost(paths):
    """Requests this run will spend against the core quota. Pure."""
    return len(paths or [])


def get(session, path, per_page):
    """One GET. Returns (status, links)."""
    r = session.get(API + path, params={"per_page": per_page}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    return r.status_code, parse_link(r.headers.get("Link"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--path", action="append",
                    help="probe this API path instead of the defaults. Repeatable.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    paths = args.path or ["/repos/%s/%s" % (args.repo, name) for name in PROBES]
    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(paths))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for path in paths:
        status, links = get(session, path, 1)
        if status != 200:
            log.info("%s returned %d; skipping it", path, status)
            continue
        state, detail = verdict(links, 1)
        log.info("%s: rels %s -> %s", path, ", ".join(rels(links)) or "none", state)
        log.info("%s: %s", state, detail)
        missing = unavailable(state)
        if missing:
            log.info("unavailable here: %s", ", ".join(missing))
        log.info("repair: %s", repair(state))
        findings.append({
            "path": path,
            "rels": rels(links),
            "style": state,
            "pages": page_count(links),
            "pages_if_missing_defaults_to_one": naive_page_count(links),
            "items": item_count(links, 1),
            "capabilities": capabilities(state),
            "unavailable": missing,
            "detail": detail,
        })

    print(json.dumps({"requests_spent": read_cost(paths),
                      "findings": findings}, indent=2, default=str))
    return 1 if any(f["style"] == "walk-only" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-rel-last-absent.mjs",
"js": '''/**
 * Sort GitHub list endpoints into the ones you can index and the ones you can
 * only walk.
 *
 * Read only. One GET per probed path at per_page=1, which is the cheapest
 * request that still produces a Link header. No items are read, nothing is
 * written, and the repair is printed rather than performed.
 *
 * Environment:
 *   GITHUB_TOKEN  a token with read access to the repository
 *   GITHUB_REPO   owner/name
 */
const API = 'https://api.github.com';
const UA = 'github-rel-last-absent/1.0';

const LINK = /<([^>]+)>\\s*;\\s*rel="([^"]+)"/g;

const PROBES = ['issues', 'pulls', 'branches', 'events', 'commits'];

/** What each shape of header actually supports. Data, not a chain of ifs. */
export const CAPABILITIES = {
  indexable: {
    walk: true, page_count: true, progress_bar: true, parallel_fanout: true, jump_to_last: true,
  },
  'walk-only': {
    walk: true, page_count: false, progress_bar: false, parallel_fanout: false, jump_to_last: false,
  },
  'single-page': {
    walk: true, page_count: true, progress_bar: true, parallel_fanout: false, jump_to_last: false,
  },
};

const PATTERN_NAMES = {
  page_count: 'page count',
  progress_bar: 'progress bar',
  parallel_fanout: 'parallel fan-out',
  jump_to_last: 'jump to last',
};

/** Parse a Link header into {rel: url}. Pure. */
export function parseLink(header) {
  const out = {};
  if (!header) return out;
  for (const m of String(header).matchAll(LINK)) out[m[2]] = m[1];
  return out;
}

/** The rel names present, sorted. Pure. */
export function rels(links) {
  return Object.keys(links || {}).sort();
}

/** The page query parameter on a pagination URL, or null. Pure. */
export function pageParam(url) {
  if (!url) return null;
  try {
    const raw = new URL(url, API).searchParams.get('page');
    const n = Number(raw);
    return Number.isFinite(n) && raw !== null ? Math.trunc(n) : null;
  } catch {
    return null;
  }
}

/** One of indexable, walk-only, single-page. Pure. */
export function paginationStyle(links) {
  const l = links || {};
  if (Object.prototype.hasOwnProperty.call(l, 'last')) return 'indexable';
  if (Object.prototype.hasOwnProperty.call(l, 'next')) return 'walk-only';
  return 'single-page';
}

/** The number of pages, or null where it cannot be known. Pure. */
export function pageCount(links) {
  if (paginationStyle(links) === 'single-page') return 1;
  return pageParam((links || {}).last);
}

/** The page count the careless way: a missing value becomes 1. Pure. */
export function naivePageCount(links) {
  return pageCount(links) || 1;
}

/** Total items, but only where the endpoint can be indexed. Pure. */
export function itemCount(links, perPage) {
  const pages = pageCount(links);
  const size = Number(perPage);
  if (pages === null || !Number.isFinite(size) || size !== 1) return null;
  return pages;
}

/** What a pager may rely on against an endpoint of this shape. Pure. */
export function capabilities(style) {
  return { ...(CAPABILITIES[style] || CAPABILITIES['walk-only']) };
}

/** The named patterns that do not work here, in a fixed order. Pure. */
export function unavailable(style) {
  const caps = capabilities(style);
  return ['page_count', 'progress_bar', 'parallel_fanout', 'jump_to_last']
    .filter((k) => !caps[k]).map((k) => PATTERN_NAMES[k]);
}

/** Classify one endpoint's header. Pure. Returns [state, detail]. */
export function verdict(links, perPage = 1) {
  const style = paginationStyle(links);
  if (style === 'walk-only') {
    return [style,
      'rel="next" is present and rel="last" is not, so the size of this list is '
      + 'only knowable by walking it. A careful page count says unknown here; '
      + `code that defaults a missing count to 1 reports ${naivePageCount(links)} page.`];
  }
  if (style === 'indexable') {
    const total = itemCount(links, perPage);
    return [style,
      `rel="last" is present, so this endpoint can be indexed: ${pageCount(links)} `
      + `page(s) at per_page=${perPage}${total ? `, which is ${total} item(s)` : ''}. `
      + 'That number is computed per request and moves between calls, so it is a '
      + 'display value rather than a bound.'];
  }
  return [style,
    'neither rel="next" nor rel="last" is present. One request is the whole list '
    + 'here, and nothing about paging applies.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'walk-only') {
    return 'terminate on the absence of rel="next" and never require rel="last". '
      + 'Drop the progress bar or make it indeterminate, and replace any fan-out '
      + 'over a page range with a sequential walk that follows the next URL '
      + 'exactly as given.';
  }
  if (state === 'indexable') {
    return 'nothing, provided rel="last" is treated as a snapshot. Do not cache '
      + 'it as the size of the job, and do not let its absence on some other '
      + 'endpoint default to 1.';
  }
  return 'nothing.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(paths) {
  return Array.isArray(paths) ? paths.length : 0;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO=owner/name');
    process.exitCode = 2;
    return;
  }
  const paths = PROBES.map((name) => `/repos/${repo}/${name}`);
  console.log(`read cost: ${readCost(paths)} request(s) against the core hourly quota`);

  const findings = [];
  for (const path of paths) {
    const url = new URL(API + path);
    url.searchParams.set('per_page', '1');
    const res = await fetch(url, { headers: headers(token) });
    if (res.status !== 200) {
      console.log(`${path} returned ${res.status}; skipping it`);
      continue;
    }
    const links = parseLink(res.headers.get('link'));
    const [state, detail] = verdict(links, 1);
    console.log(`${path}: rels ${rels(links).join(', ') || 'none'} -> ${state}`);
    console.log(`${state}: ${detail}`);
    const missing = unavailable(state);
    if (missing.length) console.log(`unavailable here: ${missing.join(', ')}`);
    console.log(`repair: ${repair(state)}`);
    findings.push({
      path,
      rels: rels(links),
      style: state,
      pages: pageCount(links),
      pages_if_missing_defaults_to_one: naivePageCount(links),
      items: itemCount(links, 1),
      capabilities: capabilities(state),
      unavailable: missing,
      detail,
    });
  }

  console.log(JSON.stringify({ requests_spent: readCost(paths), findings }, null, 2));
  process.exitCode = findings.some((f) => f.style === 'walk-only') ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The three-way classification is the thing under test, because collapsing it into a boolean is the mistake the note describes: walk-only has to be its own answer and must never be confused with a single-page list. Beside it, the careful page count and the careless one are asserted to differ on exactly the endpoint where it matters and to agree everywhere else, which is the sentence the script is built to print. The capability table is checked as data, so adding an endpoint shape later cannot quietly grant a pattern that does not work.",
"test_py_file": "test_github_rel_last_absent.py",
"test_py": '''from github_rel_last_absent import (
    capabilities, item_count, naive_page_count, page_count, page_param,
    pagination_style, parse_link, read_cost, rels, repair, unavailable, verdict,
)

BASE = "https://api.github.com/repositories/1/issues"
INDEXABLE = {"next": BASE + "?page=2", "last": BASE + "?page=912"}
WALK_ONLY = {"next": BASE + "?page=2"}
DEEP = {"first": BASE + "?page=1", "prev": BASE + "?page=4",
        "next": BASE + "?page=6", "last": BASE + "?page=40"}
SINGLE = {}


def test_the_classification_is_three_states_not_two():
    assert pagination_style(INDEXABLE) == "indexable"
    assert pagination_style(WALK_ONLY) == "walk-only"
    assert pagination_style(SINGLE) == "single-page"
    assert pagination_style(None) == "single-page"


def test_walk_only_is_never_mistaken_for_a_single_page():
    assert pagination_style(WALK_ONLY) != pagination_style(SINGLE)
    assert capabilities("walk-only") != capabilities("single-page")


def test_a_careful_page_count_refuses_to_answer_without_the_field():
    assert page_count(INDEXABLE) == 912
    assert page_count(DEEP) == 40
    assert page_count(SINGLE) == 1
    assert page_count(WALK_ONLY) is None


def test_the_careless_page_count_turns_the_gap_into_one():
    assert naive_page_count(WALK_ONLY) == 1
    assert naive_page_count(INDEXABLE) == 912
    assert naive_page_count(WALK_ONLY) != page_count(WALK_ONLY)
    assert naive_page_count(INDEXABLE) == page_count(INDEXABLE)


def test_the_item_count_is_only_offered_at_a_page_size_of_one():
    assert item_count(INDEXABLE, 1) == 912
    assert item_count(INDEXABLE, 100) is None
    assert item_count(WALK_ONLY, 1) is None


def test_the_capability_table_says_what_a_pager_may_rely_on():
    walk = capabilities("walk-only")
    assert walk["walk"] is True
    assert walk["page_count"] is False
    assert walk["progress_bar"] is False
    assert walk["parallel_fanout"] is False
    assert walk["jump_to_last"] is False
    assert capabilities("indexable")["parallel_fanout"] is True


def test_the_capability_table_is_a_copy_so_a_caller_cannot_edit_it():
    capabilities("indexable")["page_count"] = False
    assert capabilities("indexable")["page_count"] is True


def test_the_broken_patterns_are_named_in_a_fixed_order():
    assert unavailable("walk-only") == ["page count", "progress bar",
                                        "parallel fan-out", "jump to last"]
    assert unavailable("indexable") == []
    assert unavailable("single-page") == ["parallel fan-out", "jump to last"]


def test_the_walk_only_verdict_prints_the_number_that_moves_somebody():
    state, detail = verdict(WALK_ONLY)
    assert state == "walk-only"
    assert "only knowable by walking it" in detail
    assert "reports 1 page" in detail


def test_an_indexable_endpoint_is_reported_as_a_snapshot():
    state, detail = verdict(INDEXABLE, 1)
    assert state == "indexable"
    assert "912" in detail
    assert "moves between calls" in detail


def test_a_single_page_list_is_not_a_pagination_finding():
    state, detail = verdict(SINGLE)
    assert state == "single-page"
    assert "nothing about paging applies" in detail
    assert repair(state) == "nothing."


def test_the_page_parameter_is_read_out_of_the_url_defensively():
    assert page_param(BASE + "?page=7&per_page=1") == 7
    assert page_param(BASE + "?per_page=1") is None
    assert page_param("") is None
    assert page_param(None) is None


def test_the_header_is_parsed_around_commas_inside_urls():
    header = ('<%s?labels=bug,ci&page=2>; rel="next", '
              '<%s?labels=bug,ci&page=9>; rel="last"' % (BASE, BASE))
    assert rels(parse_link(header)) == ["last", "next"]
    assert parse_link("") == {}


def test_the_repair_for_walk_only_never_asks_for_a_page_count():
    fix = repair("walk-only")
    assert 'rel="next"' in fix
    assert "never require" in fix
    assert "cache it as the size of the job" in repair("indexable")


def test_the_run_says_what_it_will_spend():
    assert read_cost(["/a", "/b", "/c", "/d", "/e"]) == 5
    assert read_cost([]) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-rel-last-absent.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  capabilities, itemCount, naivePageCount, pageCount, pageParam,
  paginationStyle, parseLink, readCost, rels, repair, unavailable, verdict,
} from './github-rel-last-absent.mjs';

const BASE = 'https://api.github.com/repositories/1/issues';
const INDEXABLE = { next: `${BASE}?page=2`, last: `${BASE}?page=912` };
const WALK_ONLY = { next: `${BASE}?page=2` };
const DEEP = {
  first: `${BASE}?page=1`, prev: `${BASE}?page=4`, next: `${BASE}?page=6`, last: `${BASE}?page=40`,
};
const SINGLE = {};

test('the classification is three states, not two', () => {
  assert.equal(paginationStyle(INDEXABLE), 'indexable');
  assert.equal(paginationStyle(WALK_ONLY), 'walk-only');
  assert.equal(paginationStyle(SINGLE), 'single-page');
  assert.equal(paginationStyle(null), 'single-page');
});

test('walk-only is never mistaken for a single page', () => {
  assert.notEqual(paginationStyle(WALK_ONLY), paginationStyle(SINGLE));
  assert.notDeepEqual(capabilities('walk-only'), capabilities('single-page'));
});

test('a careful page count refuses to answer without the field', () => {
  assert.equal(pageCount(INDEXABLE), 912);
  assert.equal(pageCount(DEEP), 40);
  assert.equal(pageCount(SINGLE), 1);
  assert.equal(pageCount(WALK_ONLY), null);
});

test('the careless page count turns the gap into one', () => {
  assert.equal(naivePageCount(WALK_ONLY), 1);
  assert.equal(naivePageCount(INDEXABLE), 912);
  assert.notEqual(naivePageCount(WALK_ONLY), pageCount(WALK_ONLY));
  assert.equal(naivePageCount(INDEXABLE), pageCount(INDEXABLE));
});

test('the item count is only offered at a page size of one', () => {
  assert.equal(itemCount(INDEXABLE, 1), 912);
  assert.equal(itemCount(INDEXABLE, 100), null);
  assert.equal(itemCount(WALK_ONLY, 1), null);
});

test('the capability table says what a pager may rely on', () => {
  const walk = capabilities('walk-only');
  assert.equal(walk.walk, true);
  assert.equal(walk.page_count, false);
  assert.equal(walk.progress_bar, false);
  assert.equal(walk.parallel_fanout, false);
  assert.equal(walk.jump_to_last, false);
  assert.equal(capabilities('indexable').parallel_fanout, true);
});

test('the capability table is a copy so a caller cannot edit it', () => {
  capabilities('indexable').page_count = false;
  assert.equal(capabilities('indexable').page_count, true);
});

test('the broken patterns are named in a fixed order', () => {
  assert.deepEqual(unavailable('walk-only'),
    ['page count', 'progress bar', 'parallel fan-out', 'jump to last']);
  assert.deepEqual(unavailable('indexable'), []);
  assert.deepEqual(unavailable('single-page'), ['parallel fan-out', 'jump to last']);
});

test('the walk-only verdict prints the number that moves somebody', () => {
  const [state, detail] = verdict(WALK_ONLY);
  assert.equal(state, 'walk-only');
  assert.match(detail, /only knowable by walking it/);
  assert.match(detail, /reports 1 page/);
});

test('an indexable endpoint is reported as a snapshot', () => {
  const [state, detail] = verdict(INDEXABLE, 1);
  assert.equal(state, 'indexable');
  assert.match(detail, /912/);
  assert.match(detail, /moves between calls/);
});

test('a single-page list is not a pagination finding', () => {
  const [state, detail] = verdict(SINGLE);
  assert.equal(state, 'single-page');
  assert.match(detail, /nothing about paging applies/);
  assert.equal(repair(state), 'nothing.');
});

test('the page parameter is read out of the URL defensively', () => {
  assert.equal(pageParam(`${BASE}?page=7&per_page=1`), 7);
  assert.equal(pageParam(`${BASE}?per_page=1`), null);
  assert.equal(pageParam(''), null);
  assert.equal(pageParam(null), null);
});

test('the header is parsed around commas inside URLs', () => {
  const header = `<${BASE}?labels=bug,ci&page=2>; rel="next", `
    + `<${BASE}?labels=bug,ci&page=9>; rel="last"`;
  assert.deepEqual(rels(parseLink(header)), ['last', 'next']);
  assert.deepEqual(parseLink(''), {});
});

test('the repair for walk-only never asks for a page count', () => {
  const fix = repair('walk-only');
  assert.match(fix, /rel="next"/);
  assert.match(fix, /never require/);
  assert.match(repair('indexable'), /cache it as the size of the job/);
});

test('the run says what it will spend', () => {
  assert.equal(readCost(['/a', '/b', '/c', '/d', '/e']), 5);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("Which endpoints omit rel=last?",
  "It is not a fixed list, which is the practical reason to measure rather than memorise. GitHub includes the field when it can compute a final page for that request, and the calculation depends on the endpoint, the filters and how the underlying result set is counted. High-volume feeds and endpoints that page by cursor are the usual ones, but a list that is indexable with one set of query parameters can stop being indexable with another. Probe the exact calls your integration makes, which is one request each."),
 ("Is this not just the Link header note again?",
  "No. That note is about a client that never read the header and reported the first page as the whole list. This one is about a client that reads it, follows it correctly, and additionally requires a field the header does not always carry. The two produce a similar-looking under-count and the code that causes them looks nothing alike: one has no pagination at all, the other has pagination plus a dependency on a page count. If your pager already follows rel=\"next\" to the end, that note is closed for you and this one may not be."),
 ("What should a progress bar do on a walk-only endpoint?",
  "Be indeterminate, and say so. A spinner with a running item count is honest; a bar at 4% that was computed from a number defaulted to one is worse than no bar, because it will sit at 4% and then jump to done. If you truly need a denominator, the answer is usually a different endpoint or a search query with a total_count, and both of those come with caveats of their own about what that total actually describes."),
 ("Can I cache rel=last as the size of the job?",
  "Not safely, even on an endpoint that provides it. The final page number is computed per request, so it is a snapshot of a collection that other people are still writing to. Between page one and page nine issues get opened, branches get deleted, and the number you captured stops being the number. Use it for display, terminate on the absence of rel=\"next\", and let the loop discover the actual end."),
 ("How much quota does the check itself cost?",
  "One request per path probed, five by default, against the hourly core bucket. The probe uses per_page=1 because the finding is entirely in a response header and none of the items are needed, and that also makes the page number in rel=\"last\" equal to the exact item count wherever the field is present. The script prints the total before it spends anything, so widening the probe list is a decision you make with the number in front of you."),
],
"related": [
 ("/github/link-header-not-followed/", "Only the first page is ever read"),
 ("/github/endpoint-ignores-page-param/", "The endpoint ignores page entirely"),
 ("/github/per-page-over-100-clamped/", "per_page above 100 is clamped"),
],
"citations": [CITE_PAGINATION, CITE_PAGINATE_PLUGIN, CITE_REPOS, CITE_BEST_PRACTICES],
},

{
"slug": "endpoint-ignores-page-param",
"title": "The endpoint ignores page and returns page one forever",
"description": "Passing page=2 returns the same rows as page=1. A few endpoints ignore offset paging entirely and expect before/after cursors, so the loop never ends.",
"h1": "the endpoint ignores page and returns page one forever",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api page parameter ignored",
             "github api page 2 returns same results",
             "github rest api cursor pagination before after",
             "github repository activity pagination",
             "github api pagination infinite loop duplicates"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The collector increments a page counter, exactly as it does against a dozen other endpoints, and every request comes back <code>200</code> with a full page of rows. It never finishes. Either it runs until something kills it, or it stops at an arbitrary page cap and hands over a dataset that is the same thirty records repeated forty times. The endpoint has been returning page one to every request since the first one.",
"short_answer": """<p>A minority of GitHub list endpoints do not support offset pagination. They page with <code>before</code> and <code>after</code> cursors instead, or they do not page at all, and they <em>ignore</em> <code>page</code> and <code>per_page</code> rather than rejecting them. An unsupported parameter is not an error here; it is silence.</p>
<p>Two signals identify it, and you want both. Fetch <code>page=1</code> and <code>page=2</code> and compare the identifiers on each: identical rows are the symptom. Then read the endpoint's own <code>Link</code> header and look at what the <code>next</code> URL is built from &mdash; if it carries <code>after=</code> or <code>before=</code> rather than <code>page=</code>, the endpoint has told you plainly what it supports. The first signal alone can be a busy feed that reordered between two calls; the second does not depend on timing. The repair is to use the cursor parameters the endpoint's own next link uses, or the GraphQL equivalent with <code>after: $cursor</code> and <code>pageInfo { hasNextPage endCursor }</code>. Never synthesise page numbers.</p>""",
"problem": """<p>Every other pagination bug on this API is an under-count. This one is an over-count, and the difference matters because of where the damage lands. A job that reads too little produces a small number in a report. A job that reads the same page forever produces rows &mdash; thousands of them, all duplicates of thirty &mdash; and then writes them somewhere: a warehouse table, a search index, a spreadsheet somebody is about to make a decision from.</p>
<p>It also does not stop. The usual terminating condition for a hand-rolled pager is a short page, and there is never a short page, because page forty is page one and page one is full. So the loop runs until a timeout, an out-of-memory kill or a page cap somebody added for exactly this reason without ever finding out why it was needed. In the meantime it is spending quota at full speed on a single page of data.</p>
<p>The investigation goes to the wrong layer almost every time. Duplicate rows read as an upsert bug, so the first day goes into deduplication keys and idempotency. The fix &mdash; dedupe on ingest &mdash; even works, in the sense that the duplicates stop appearing. What remains is a job that spends forty requests to collect thirty records and reports the first page as the entire dataset, which is a data-loss bug now wearing the costume of a resolved ticket.</p>""",
"why": """<p><strong>An unsupported query parameter is ignored, not rejected.</strong> Sending <code>page=2</code> to an endpoint that does not implement offset paging produces a perfectly ordinary 200. There is no 422, no <code>Warning</code>, and nothing in the body to say the parameter was dropped. This is consistent behaviour across the API and it is the reason the bug is silent: the client's only evidence that its parameter did anything is that the results changed, and they did not.</p>
<p><strong>Cursor endpoints exist and are growing.</strong> Repository activity and several newer list endpoints page with <code>before</code> and <code>after</code> cursors, because an offset into a live feed is not a stable thing to hand out. Those endpoints advertise their cursors in the <code>Link</code> header exactly as the offset ones advertise page numbers, which means the header is a reliable, timing-independent statement of what the endpoint supports.</p>
<p><strong>Identical rows on two pages are evidence, not proof.</strong> A feed sorted by recency can genuinely return overlapping rows across two requests made a second apart, because items moved. That is why this check reads the <code>Link</code> header as well: identical ids plus a cursor-shaped next link is conclusive, identical ids plus a page-shaped next link is a re-run and a closer look. A diagnostic that reported the first case and the second case identically would be wrong often enough to be ignored, which is worse than not existing.</p>
<p><strong>The absence of a short page removes the terminating condition.</strong> Hand-rolled pagers usually stop when a page comes back shorter than the page size. Against an endpoint that ignores <code>page</code>, every page is the first page and every page is full, so that condition is never met. This is the one pagination bug in the section where the loop does not merely stop in the wrong place; it does not stop.</p>
<p><strong>The repair is to stop generating URLs.</strong> The next URL in the <code>Link</code> header already contains whatever the endpoint needs, cursor or page. Following it verbatim is correct on both kinds of endpoint and needs no knowledge of which kind you are on, which is why it is the pattern worth standardising: it makes the entire class of bug unreachable rather than fixing one instance of it.</p>
<p><strong>The check costs almost nothing and the script says so.</strong> Two requests per path at <code>per_page=1</code>, four by default. The irony of a diagnostic for a runaway loop being itself expensive is not lost, so the number is computed and printed before anything is fetched.</p>""",
"steps": [
 {"h": "Fetch page one and page two at the smallest page size",
  "body": """<p><code>per_page=1</code> on both, so the comparison is between two single rows and the whole check costs two requests per path. The small page size is not cosmetic: it also makes the two responses arrive close together, which narrows the window in which a live feed could legitimately reorder underneath you.</p>"""},
 {"h": "Compare identifiers rather than payloads",
  "body": """<p>Take <code>id</code>, falling back to <code>node_id</code>, <code>sha</code> or <code>url</code>, and compare the lists. Comparing whole objects produces false negatives, because timestamps and counters inside an item change between two requests while the item itself is the same row. An identifier is the only field that means what you want it to mean here.</p>"""},
 {"h": "Read what the endpoint's own next link is built from",
  "body": """<p>Parse the <code>Link</code> header and look at the query parameters on the <code>next</code> URL. <code>page=</code> means offset paging is what this endpoint speaks. <code>after=</code> or <code>before=</code> means it speaks cursors and your page numbers were never being read. This signal does not depend on timing at all, which is what makes it the one that settles the question.</p>"""},
 {"h": "Keep the ambiguous case ambiguous",
  "body": """<p>Identical rows with a page-shaped next link is a busy feed, a re-run, or a genuinely broken endpoint, in that order of likelihood. Reporting that as a definite finding is how a check gets switched off. The script gives it its own state, says what would settle it, and does not overclaim.</p>"""},
 {"h": "Follow the next URL instead of building one",
  "body": """<p>Take the <code>next</code> URL from the header verbatim, cursors and all, and stop when there is no <code>next</code>. That loop is correct on offset endpoints and cursor endpoints alike without knowing which it is on. Where you need the GraphQL equivalent, it is <code>after: $cursor</code> with <code>pageInfo { hasNextPage endCursor }</code>, and the same rule holds: the cursor is opaque and is not to be constructed.</p>"""},
],
"verify": """<p>After the collector follows the header instead of counting, the same probe reports the endpoint as a cursor endpoint that pages correctly, and the row count stops being a multiple of the page size.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_page_param_ignored.py --repo acme/monorepo
# read cost: 4 request(s) against the core hourly quota
# /repos/acme/monorepo/activity: page=1 and page=2 returned the same id(s)
# ignores-page: page=2 returned the same row(s) as page=1 and the next link is
# built from after=, so this endpoint does not read page at all. A loop that
# stops on a short page has no terminating condition here
# repair: follow the next URL from the Link header verbatim, using after=

# after the collector is changed
# cursor-pagination: the next link is built from after= and the rows differ,
# so this endpoint pages correctly and simply not by number</code></pre>""",
"code_intro": "Two GETs per probed path and one comparison, but the comparison is deliberately built from two independent signals because either one alone produces a diagnostic somebody would learn to ignore. Identifiers are extracted defensively, since not every list on this API keys its items the same way, and the endpoint's own next link is inspected for the parameter names it carries. Their agreement is the definitive state; their disagreement gets its own honest, weaker verdict. There is also a pure predicate that answers the question people actually care about, which is whether a page-counting loop against this endpoint would ever terminate.",
"py_file": "github_page_param_ignored.py",
"py": '''"""Find GitHub endpoints that ignore the page parameter instead of rejecting it.

Read only. Two GETs per probed path at per_page=1, and nothing is written.

A minority of endpoints do not implement offset pagination. They page with
before/after cursors, or they do not page at all, and they ignore page and
per_page rather than answering 422. So page=2 returns page one, a hand-rolled
loop that stops on a short page never stops, and the same rows are collected
until something kills the job.

Two independent signals are used, because either alone is unsafe. Identical
identifiers across page 1 and page 2 is the symptom, but a feed sorted by
recency can genuinely move between two requests. The parameter names on the
endpoint's own next link do not depend on timing at all: a next URL built from
after= or before= is the endpoint saying which kind of pagination it speaks.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import json
import logging
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_page_param_ignored")

API = "https://api.github.com"
UA = "github-page-param-ignored/1.0"

LINK = re.compile(r'<([^>]+)>\\s*;\\s*rel="([^"]+)"')

# The parameter names that mean each kind of pagination. Cursor names first
# because an endpoint that offers both is a cursor endpoint being polite.
CURSOR_PARAMS = ("after", "before", "cursor")
OFFSET_PARAMS = ("page",)

# Tried in order. Not every list on this API keys its items the same way, and
# comparing whole objects is useless because counters inside an item change
# between two requests while the item stays the same row.
ID_FIELDS = ("id", "node_id", "sha", "url")

PROBES = ["activity", "events"]


def parse_link(header):
    """Parse a Link header into {rel: url}. Pure."""
    if not header:
        return {}
    return {rel: url for url, rel in LINK.findall(header)}


def link_params(links):
    """The query parameter names on the next URL, sorted. Pure."""
    url = (links or {}).get("next")
    if not url:
        return []
    return sorted(parse_qs(urlparse(url).query))


def link_style(links):
    """What the endpoint's own next link is built from. Pure.

    Returns cursor, offset or none. This is the signal that does not depend on
    timing, which is why the definitive verdict requires it.
    """
    names = set(link_params(links))
    if names & set(CURSOR_PARAMS):
        return "cursor"
    if names & set(OFFSET_PARAMS):
        return "offset"
    return "none"


def cursor_hint(links):
    """The cursor parameter this endpoint actually uses, or None. Pure."""
    names = set(link_params(links))
    for name in CURSOR_PARAMS:
        if name in names:
            return name
    return None


def identity(item):
    """A stable identifier for one list item, or None. Pure."""
    if not isinstance(item, dict):
        return None
    for field in ID_FIELDS:
        value = item.get(field)
        if value not in (None, ""):
            return str(value)
    return None


def identities(items):
    """Identifiers for a page, dropping items that have none. Pure."""
    if not isinstance(items, list):
        return []
    return [i for i in (identity(x) for x in items) if i is not None]


def same_rows(first, second):
    """Whether page two is page one, exactly. Pure."""
    return bool(first) and bool(second) and list(first) == list(second)


def overlaps(first, second):
    """Whether the two pages share any row at all. Pure."""
    return bool(set(first or []) & set(second or []))


def verdict(style, first_ids, second_ids):
    """Classify one endpoint from both signals. Pure. Returns (state, detail).

    The two conclusive states require the signals to agree. Where they do not,
    the weaker verdict is returned deliberately: a check that cries wolf on a
    busy feed is a check somebody turns off.
    """
    if not first_ids:
        return ("inconclusive-empty",
                "page 1 returned nothing this check could identify, so there is "
                "no comparison to make. Point it at a path with rows in it.")
    if not second_ids:
        return ("offset-honoured",
                "page 2 came back empty, so the collection ends inside page 1 "
                "and the page parameter is being read.")
    if same_rows(first_ids, second_ids):
        if style in ("cursor", "none"):
            shape = ("built from a cursor" if style == "cursor"
                     else "absent, so there is no next page to follow")
            return ("ignores-page",
                    "page=2 returned the same row(s) as page=1 and the next "
                    "link is %s, so this endpoint does not read page at all. A "
                    "loop that stops on a short page has no terminating "
                    "condition here." % shape)
        return ("suspect-ignores-page",
                "page=2 returned the same row(s) as page=1, but the next link "
                "is still built from page=, so this may be a feed that moved "
                "between the two requests. Re-run it, or add a stable sort, "
                "before treating it as a finding.")
    if overlaps(first_ids, second_ids):
        return ("overlapping-pages",
                "page 1 and page 2 share rows without being identical, which is "
                "an unstable sort rather than an ignored parameter. Paging this "
                "endpoint will double-count and skip.")
    if style == "cursor":
        return ("cursor-pagination",
                "the rows differ and the next link is built from a cursor, so "
                "this endpoint pages correctly and simply not by number. Follow "
                "its next URL rather than incrementing anything.")
    return ("offset-honoured",
            "page 2 returned different rows and the next link is built from "
            "page=, so offset pagination works here.")


def loop_terminates(state):
    """Whether a page-counting loop against this endpoint would ever end. Pure."""
    return state not in ("ignores-page", "suspect-ignores-page")


def repair(state, links=None):
    """The sentence a reader has to act on. Pure."""
    if state == "ignores-page":
        cursor = cursor_hint(links)
        if cursor:
            return ("follow the next URL from the Link header verbatim, using "
                    "%s=. Do not construct it, and do not send page: the value "
                    "is opaque and incrementing anything here is meaningless."
                    % cursor)
        return ("stop paging this endpoint by number. It advertises no next "
                "page, so one request is what it offers, and the GraphQL "
                "equivalent with after: $cursor is the way to walk more.")
    if state == "suspect-ignores-page":
        return ("re-run the check, or add a deterministic sort, before changing "
                "any code. Identical rows on a recency-ordered feed can be two "
                "requests a second apart rather than an ignored parameter.")
    if state == "overlapping-pages":
        return ("sort deterministically before paging, or switch to the cursor "
                "form. Offset paging over a feed that reorders will double-count "
                "some rows and miss others whatever the page size.")
    if state == "cursor-pagination":
        return ("follow the next URL from the Link header verbatim. It already "
                "carries the cursor, and building it yourself is the only way "
                "to get this wrong.")
    if state == "inconclusive-empty":
        return "point the check at a path that has rows in it."
    return "nothing."


def read_cost(paths):
    """Requests this run will spend against the core quota. Pure."""
    return 2 * len(paths or [])


def get(session, path, params):
    """One GET. Returns (status, items-or-None, links)."""
    r = session.get(API + path, params=params, timeout=30)
    links = parse_link(r.headers.get("Link"))
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    if r.status_code != 200:
        return r.status_code, None, links
    try:
        body = r.json()
    except ValueError:
        return r.status_code, None, links
    return r.status_code, body if isinstance(body, list) else None, links


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--path", action="append",
                    help="probe this API path instead of the defaults. Repeatable.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    paths = args.path or ["/repos/%s/%s" % (args.repo, name) for name in PROBES]
    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(paths))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for path in paths:
        status1, first, links = get(session, path, {"per_page": 1, "page": 1})
        if first is None:
            log.info("%s returned %d; skipping it", path, status1)
            continue
        status2, second, _links2 = get(session, path, {"per_page": 1, "page": 2})
        first_ids, second_ids = identities(first), identities(second)
        style = link_style(links)
        state, detail = verdict(style, first_ids, second_ids)

        if same_rows(first_ids, second_ids):
            log.info("%s: page=1 and page=2 returned the same id(s)", path)
        log.info("%s: %s", state, detail)
        log.info("a page-counting loop here %s",
                 "terminates" if loop_terminates(state) else "never terminates")
        log.info("repair: %s", repair(state, links))

        findings.append({
            "path": path,
            "status": [status1, status2],
            "next_link_params": link_params(links),
            "link_style": style,
            "cursor_parameter": cursor_hint(links),
            "page_1_ids": first_ids,
            "page_2_ids": second_ids,
            "identical": same_rows(first_ids, second_ids),
            "loop_terminates": loop_terminates(state),
            "state": state,
            "detail": detail,
        })

    print(json.dumps({"requests_spent": read_cost(paths),
                      "findings": findings}, indent=2, default=str))
    bad = {"ignores-page", "suspect-ignores-page", "overlapping-pages"}
    return 1 if any(f["state"] in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-page-param-ignored.mjs",
"js": '''/**
 * Find GitHub endpoints that ignore the page parameter instead of rejecting it.
 *
 * Read only. Two GETs per probed path at per_page=1, and nothing is written.
 *
 * Two independent signals are used, because either alone is unsafe: identical
 * identifiers across page 1 and page 2, and the parameter names on the
 * endpoint's own next link. The second does not depend on timing.
 *
 * Environment:
 *   GITHUB_TOKEN  a token with read access to the repository
 *   GITHUB_REPO   owner/name
 */
const API = 'https://api.github.com';
const UA = 'github-page-param-ignored/1.0';

const LINK = /<([^>]+)>\\s*;\\s*rel="([^"]+)"/g;

/** Cursor names first: an endpoint offering both is a cursor endpoint. */
export const CURSOR_PARAMS = ['after', 'before', 'cursor'];
export const OFFSET_PARAMS = ['page'];

/** Tried in order. Not every list on this API keys its items the same way. */
export const ID_FIELDS = ['id', 'node_id', 'sha', 'url'];

const PROBES = ['activity', 'events'];

/** Parse a Link header into {rel: url}. Pure. */
export function parseLink(header) {
  const out = {};
  if (!header) return out;
  for (const m of String(header).matchAll(LINK)) out[m[2]] = m[1];
  return out;
}

/** The query parameter names on the next URL, sorted. Pure. */
export function linkParams(links) {
  const url = (links || {}).next;
  if (!url) return [];
  try {
    return [...new Set([...new URL(url, API).searchParams.keys()])].sort();
  } catch {
    return [];
  }
}

/** What the endpoint's own next link is built from: cursor, offset or none. */
export function linkStyle(links) {
  const names = new Set(linkParams(links));
  if (CURSOR_PARAMS.some((n) => names.has(n))) return 'cursor';
  if (OFFSET_PARAMS.some((n) => names.has(n))) return 'offset';
  return 'none';
}

/** The cursor parameter this endpoint actually uses, or null. Pure. */
export function cursorHint(links) {
  const names = new Set(linkParams(links));
  return CURSOR_PARAMS.find((n) => names.has(n)) ?? null;
}

/** A stable identifier for one list item, or null. Pure. */
export function identity(item) {
  if (!item || typeof item !== 'object' || Array.isArray(item)) return null;
  for (const field of ID_FIELDS) {
    const value = item[field];
    if (value !== null && value !== undefined && value !== '') return String(value);
  }
  return null;
}

/** Identifiers for a page, dropping items that have none. Pure. */
export function identities(items) {
  if (!Array.isArray(items)) return [];
  return items.map(identity).filter((v) => v !== null);
}

/** Whether page two is page one, exactly. Pure. */
export function sameRows(first, second) {
  if (!first || !second || !first.length || !second.length) return false;
  return first.length === second.length && first.every((v, i) => v === second[i]);
}

/** Whether the two pages share any row at all. Pure. */
export function overlaps(first, second) {
  const set = new Set(first || []);
  return (second || []).some((v) => set.has(v));
}

/** Classify one endpoint from both signals. Pure. Returns [state, detail]. */
export function verdict(style, firstIds, secondIds) {
  if (!firstIds || !firstIds.length) {
    return ['inconclusive-empty',
      'page 1 returned nothing this check could identify, so there is no '
      + 'comparison to make. Point it at a path with rows in it.'];
  }
  if (!secondIds || !secondIds.length) {
    return ['offset-honoured',
      'page 2 came back empty, so the collection ends inside page 1 and the '
      + 'page parameter is being read.'];
  }
  if (sameRows(firstIds, secondIds)) {
    if (style === 'cursor' || style === 'none') {
      const shape = style === 'cursor'
        ? 'built from a cursor'
        : 'absent, so there is no next page to follow';
      return ['ignores-page',
        `page=2 returned the same row(s) as page=1 and the next link is ${shape}, `
        + 'so this endpoint does not read page at all. A loop that stops on a '
        + 'short page has no terminating condition here.'];
    }
    return ['suspect-ignores-page',
      'page=2 returned the same row(s) as page=1, but the next link is still '
      + 'built from page=, so this may be a feed that moved between the two '
      + 'requests. Re-run it, or add a stable sort, before treating it as a finding.'];
  }
  if (overlaps(firstIds, secondIds)) {
    return ['overlapping-pages',
      'page 1 and page 2 share rows without being identical, which is an '
      + 'unstable sort rather than an ignored parameter. Paging this endpoint '
      + 'will double-count and skip.'];
  }
  if (style === 'cursor') {
    return ['cursor-pagination',
      'the rows differ and the next link is built from a cursor, so this '
      + 'endpoint pages correctly and simply not by number. Follow its next URL '
      + 'rather than incrementing anything.'];
  }
  return ['offset-honoured',
    'page 2 returned different rows and the next link is built from page=, so '
    + 'offset pagination works here.'];
}

/** Whether a page-counting loop against this endpoint would ever end. Pure. */
export function loopTerminates(state) {
  return !['ignores-page', 'suspect-ignores-page'].includes(state);
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, links = null) {
  if (state === 'ignores-page') {
    const cursor = cursorHint(links);
    if (cursor) {
      return 'follow the next URL from the Link header verbatim, using '
        + `${cursor}=. Do not construct it, and do not send page: the value is `
        + 'opaque and incrementing anything here is meaningless.';
    }
    return 'stop paging this endpoint by number. It advertises no next page, so '
      + 'one request is what it offers, and the GraphQL equivalent with '
      + 'after: $cursor is the way to walk more.';
  }
  if (state === 'suspect-ignores-page') {
    return 're-run the check, or add a deterministic sort, before changing any '
      + 'code. Identical rows on a recency-ordered feed can be two requests a '
      + 'second apart rather than an ignored parameter.';
  }
  if (state === 'overlapping-pages') {
    return 'sort deterministically before paging, or switch to the cursor form. '
      + 'Offset paging over a feed that reorders will double-count some rows and '
      + 'miss others whatever the page size.';
  }
  if (state === 'cursor-pagination') {
    return 'follow the next URL from the Link header verbatim. It already '
      + 'carries the cursor, and building it yourself is the only way to get '
      + 'this wrong.';
  }
  if (state === 'inconclusive-empty') return 'point the check at a path that has rows in it.';
  return 'nothing.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(paths) {
  return 2 * (Array.isArray(paths) ? paths.length : 0);
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const res = await fetch(url, { headers: headers(token) });
  const links = parseLink(res.headers.get('link'));
  if (res.status !== 200) return { status: res.status, items: null, links };
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, items: Array.isArray(body) ? body : null, links };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO=owner/name');
    process.exitCode = 2;
    return;
  }
  const paths = PROBES.map((name) => `/repos/${repo}/${name}`);
  console.log(`read cost: ${readCost(paths)} request(s) against the core hourly quota`);

  const findings = [];
  for (const path of paths) {
    const one = await get(token, path, { per_page: 1, page: 1 });
    if (one.items === null) {
      console.log(`${path} returned ${one.status}; skipping it`);
      continue;
    }
    const two = await get(token, path, { per_page: 1, page: 2 });
    const firstIds = identities(one.items);
    const secondIds = identities(two.items);
    const style = linkStyle(one.links);
    const [state, detail] = verdict(style, firstIds, secondIds);

    if (sameRows(firstIds, secondIds)) {
      console.log(`${path}: page=1 and page=2 returned the same id(s)`);
    }
    console.log(`${state}: ${detail}`);
    console.log(`a page-counting loop here ${loopTerminates(state) ? 'terminates' : 'never terminates'}`);
    console.log(`repair: ${repair(state, one.links)}`);

    findings.push({
      path,
      status: [one.status, two.status],
      next_link_params: linkParams(one.links),
      link_style: style,
      cursor_parameter: cursorHint(one.links),
      page_1_ids: firstIds,
      page_2_ids: secondIds,
      identical: sameRows(firstIds, secondIds),
      loop_terminates: loopTerminates(state),
      state,
      detail,
    });
  }

  console.log(JSON.stringify({ requests_spent: readCost(paths), findings }, null, 2));
  const bad = ['ignores-page', 'suspect-ignores-page', 'overlapping-pages'];
  process.exitCode = findings.some((f) => bad.includes(f.state)) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Most of these tests exist to stop the check overclaiming. Identical rows with a cursor-shaped next link must be the definite finding; identical rows with a page-shaped next link must be the softer one, because that is a busy feed as often as it is a bug, and a diagnostic that confuses the two gets switched off within a week. Beyond that: identifiers extracted from items that key themselves differently, partial overlap given its own state rather than being rounded to either neighbour, and the predicate that answers whether a page-counting loop here would ever terminate.",
"test_py_file": "test_github_page_param_ignored.py",
"test_py": '''from github_page_param_ignored import (
    cursor_hint, identities, identity, link_params, link_style, loop_terminates,
    overlaps, parse_link, read_cost, repair, same_rows, verdict,
)

BASE = "https://api.github.com/repos/o/n"
OFFSET_LINK = {"next": BASE + "/issues?per_page=1&page=2"}
CURSOR_LINK = {"next": BASE + "/activity?per_page=1&after=Y3Vyc29yOjE="}
BEFORE_LINK = {"next": BASE + "/activity?per_page=1&before=Y3Vyc29yOjk="}
NO_LINK = {}


def test_the_link_style_is_read_from_the_parameter_names():
    assert link_style(CURSOR_LINK) == "cursor"
    assert link_style(BEFORE_LINK) == "cursor"
    assert link_style(OFFSET_LINK) == "offset"
    assert link_style(NO_LINK) == "none"
    assert link_style(None) == "none"


def test_the_cursor_parameter_is_named_so_the_repair_can_be_concrete():
    assert cursor_hint(CURSOR_LINK) == "after"
    assert cursor_hint(BEFORE_LINK) == "before"
    assert cursor_hint(OFFSET_LINK) is None
    assert link_params(OFFSET_LINK) == ["page", "per_page"]


def test_identifiers_fall_back_through_the_fields_a_list_might_use():
    assert identity({"id": 41, "node_id": "MDQ6"}) == "41"
    assert identity({"node_id": "MDQ6"}) == "MDQ6"
    assert identity({"sha": "9f2c1ab"}) == "9f2c1ab"
    assert identity({"url": BASE + "/pulls/3"}) == BASE + "/pulls/3"
    assert identity({"title": "no identifier here"}) is None
    assert identity(None) is None


def test_a_page_of_unidentifiable_items_does_not_become_a_finding():
    assert identities([{"title": "a"}, {"title": "b"}]) == []
    assert identities([{"id": 1}, {"title": "b"}]) == ["1"]
    assert identities("not a list") == []


def test_identical_rows_with_a_cursor_link_is_the_definite_finding():
    state, detail = verdict("cursor", ["9"], ["9"])
    assert state == "ignores-page"
    assert "does not read page at all" in detail
    assert "no terminating condition" in detail
    assert not loop_terminates(state)


def test_identical_rows_with_a_page_link_is_only_a_suspicion():
    state, detail = verdict("offset", ["9"], ["9"])
    assert state == "suspect-ignores-page"
    assert "may be a feed that moved" in detail
    assert "Re-run it" in detail


def test_a_partial_overlap_is_its_own_answer():
    state, detail = verdict("offset", ["9", "8"], ["8", "7"])
    assert state == "overlapping-pages"
    assert "unstable sort" in detail
    assert loop_terminates(state)


def test_a_cursor_endpoint_that_pages_properly_is_not_a_finding():
    state, detail = verdict("cursor", ["9"], ["8"])
    assert state == "cursor-pagination"
    assert "not by number" in detail


def test_offset_pagination_that_works_is_reported_as_working():
    assert verdict("offset", ["9"], ["8"])[0] == "offset-honoured"
    assert verdict("offset", ["9"], [])[0] == "offset-honoured"


def test_an_empty_first_page_proves_nothing():
    state, detail = verdict("none", [], [])
    assert state == "inconclusive-empty"
    assert "no comparison to make" in detail


def test_the_row_comparisons_are_order_sensitive_and_set_based_in_turn():
    assert same_rows(["1", "2"], ["1", "2"])
    assert not same_rows(["1", "2"], ["2", "1"])
    assert not same_rows([], [])
    assert overlaps(["1", "2"], ["2", "3"])
    assert not overlaps(["1"], ["2"])


def test_the_repair_names_the_cursor_the_endpoint_actually_uses():
    assert "after=" in repair("ignores-page", CURSOR_LINK)
    assert "before=" in repair("ignores-page", BEFORE_LINK)
    assert "no next page" in repair("ignores-page", NO_LINK)
    assert "Re-run" not in repair("cursor-pagination")


def test_the_repair_for_a_suspicion_changes_no_code():
    fix = repair("suspect-ignores-page")
    assert "re-run the check" in fix
    assert "before changing any code" in fix


def test_the_header_is_parsed_around_commas_inside_urls():
    header = '<%s/issues?labels=bug,ci&page=2>; rel="next"' % BASE
    assert link_style(parse_link(header)) == "offset"


def test_the_run_says_what_it_will_spend():
    assert read_cost(["/a", "/b"]) == 4
    assert read_cost([]) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-page-param-ignored.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  cursorHint, identities, identity, linkParams, linkStyle, loopTerminates,
  overlaps, parseLink, readCost, repair, sameRows, verdict,
} from './github-page-param-ignored.mjs';

const BASE = 'https://api.github.com/repos/o/n';
const OFFSET_LINK = { next: `${BASE}/issues?per_page=1&page=2` };
const CURSOR_LINK = { next: `${BASE}/activity?per_page=1&after=Y3Vyc29yOjE=` };
const BEFORE_LINK = { next: `${BASE}/activity?per_page=1&before=Y3Vyc29yOjk=` };
const NO_LINK = {};

test('the link style is read from the parameter names', () => {
  assert.equal(linkStyle(CURSOR_LINK), 'cursor');
  assert.equal(linkStyle(BEFORE_LINK), 'cursor');
  assert.equal(linkStyle(OFFSET_LINK), 'offset');
  assert.equal(linkStyle(NO_LINK), 'none');
  assert.equal(linkStyle(null), 'none');
});

test('the cursor parameter is named so the repair can be concrete', () => {
  assert.equal(cursorHint(CURSOR_LINK), 'after');
  assert.equal(cursorHint(BEFORE_LINK), 'before');
  assert.equal(cursorHint(OFFSET_LINK), null);
  assert.deepEqual(linkParams(OFFSET_LINK), ['page', 'per_page']);
});

test('identifiers fall back through the fields a list might use', () => {
  assert.equal(identity({ id: 41, node_id: 'MDQ6' }), '41');
  assert.equal(identity({ node_id: 'MDQ6' }), 'MDQ6');
  assert.equal(identity({ sha: '9f2c1ab' }), '9f2c1ab');
  assert.equal(identity({ url: `${BASE}/pulls/3` }), `${BASE}/pulls/3`);
  assert.equal(identity({ title: 'no identifier here' }), null);
  assert.equal(identity(null), null);
});

test('a page of unidentifiable items does not become a finding', () => {
  assert.deepEqual(identities([{ title: 'a' }, { title: 'b' }]), []);
  assert.deepEqual(identities([{ id: 1 }, { title: 'b' }]), ['1']);
  assert.deepEqual(identities('not a list'), []);
});

test('identical rows with a cursor link is the definite finding', () => {
  const [state, detail] = verdict('cursor', ['9'], ['9']);
  assert.equal(state, 'ignores-page');
  assert.match(detail, /does not read page at all/);
  assert.match(detail, /no terminating condition/);
  assert.ok(!loopTerminates(state));
});

test('identical rows with a page link is only a suspicion', () => {
  const [state, detail] = verdict('offset', ['9'], ['9']);
  assert.equal(state, 'suspect-ignores-page');
  assert.match(detail, /may be a feed that moved/);
  assert.match(detail, /Re-run it/);
});

test('a partial overlap is its own answer', () => {
  const [state, detail] = verdict('offset', ['9', '8'], ['8', '7']);
  assert.equal(state, 'overlapping-pages');
  assert.match(detail, /unstable sort/);
  assert.ok(loopTerminates(state));
});

test('a cursor endpoint that pages properly is not a finding', () => {
  const [state, detail] = verdict('cursor', ['9'], ['8']);
  assert.equal(state, 'cursor-pagination');
  assert.match(detail, /not by number/);
});

test('offset pagination that works is reported as working', () => {
  assert.equal(verdict('offset', ['9'], ['8'])[0], 'offset-honoured');
  assert.equal(verdict('offset', ['9'], [])[0], 'offset-honoured');
});

test('an empty first page proves nothing', () => {
  const [state, detail] = verdict('none', [], []);
  assert.equal(state, 'inconclusive-empty');
  assert.match(detail, /no comparison to make/);
});

test('the row comparisons are order sensitive and set based in turn', () => {
  assert.ok(sameRows(['1', '2'], ['1', '2']));
  assert.ok(!sameRows(['1', '2'], ['2', '1']));
  assert.ok(!sameRows([], []));
  assert.ok(overlaps(['1', '2'], ['2', '3']));
  assert.ok(!overlaps(['1'], ['2']));
});

test('the repair names the cursor the endpoint actually uses', () => {
  assert.match(repair('ignores-page', CURSOR_LINK), /after=/);
  assert.match(repair('ignores-page', BEFORE_LINK), /before=/);
  assert.match(repair('ignores-page', NO_LINK), /no next page/);
  assert.ok(!repair('cursor-pagination').includes('Re-run'));
});

test('the repair for a suspicion changes no code', () => {
  const fix = repair('suspect-ignores-page');
  assert.match(fix, /re-run the check/);
  assert.match(fix, /before changing any code/);
});

test('the header is parsed around commas inside URLs', () => {
  const header = `<${BASE}/issues?labels=bug,ci&page=2>; rel="next"`;
  assert.equal(linkStyle(parseLink(header)), 'offset');
});

test('the run says what it will spend', () => {
  assert.equal(readCost(['/a', '/b']), 4);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("Which endpoints ignore page?",
  "There is no published list, and there does not need to be, because every endpoint tells you itself in its Link header. Repository activity is the well-known one and it pages with before and after cursors; several newer list endpoints do the same, on the reasonable grounds that an offset into a live feed is not a stable thing to hand out. Rather than memorising a set that changes, probe the exact calls your integration makes and read what their next links are built from. That is two requests per path."),
 ("Why compare identifiers instead of the whole response body?",
  "Because a list item is not stable between two requests even when it is the same row. Comment counts, updated timestamps, reaction totals and mergeability all change under you, so comparing whole objects reports two identical rows as different and hides the bug you are looking for. An identifier is the only field that means what you need it to mean, and the script falls back through id, node_id, sha and url because not every list on this API keys its items the same way."),
 ("The check says suspect-ignores-page. What does that mean?",
  "It means one signal fired and the other did not: page two returned the same rows as page one, but the endpoint's next link is still built from page=. A feed sorted by recency can legitimately return an overlapping row for two requests made a second apart, so the honest answer is that this needs a re-run or a deterministic sort before anybody changes code. The script keeps that state separate on purpose. A diagnostic that reports a busy feed as a definite bug is one that gets muted."),
 ("Why is this worse than a pager that stops too early?",
  "Because it does not stop, and because it produces data rather than withholding it. An under-count puts a small number in a report. This puts thousands of duplicate rows into whatever the job writes to, at full request rate, until a timeout or a page cap ends it. And it is usually misdiagnosed one layer down: duplicates read as an upsert problem, so the deduplication gets fixed and the job settles into quietly reporting page one as the entire dataset."),
 ("How much quota does the check itself cost?",
  "Two requests per path probed, four by default, against the hourly core bucket, and both are made at per_page=1 so nothing large is transferred. The script computes and prints the total before it fetches anything. Keeping it small matters here more than usual: the bug being diagnosed is a loop that spends quota at full speed on one page of data, and a diagnostic for it has no business doing the same."),
],
"related": [
 ("/github/link-header-not-followed/", "Only the first page is ever read"),
 ("/github/rel-last-absent/", "The Link header has no rel=last"),
 ("/github/compare-250-commit-cap/", "The compare endpoint stops at 250 commits"),
],
"citations": [CITE_PAGINATION, CITE_COMMUNITY_PAGING, CITE_REPOS, CITE_BEST_PRACTICES],
},

{
"slug": "search-incomplete-results",
"title": "incomplete_results is true and the search answer is partial",
"description": "A search can return 200 with incomplete_results true: the server timed out and sent what it had. The count moves between runs and nothing errors.",
"h1": "incomplete_results is true and the search answer is partial",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github search api incomplete_results true",
             "github search returns different results each time",
             "github search api timeout partial results",
             "github search missing results no error",
             "github search incomplete_results meaning"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The same search runs every morning and the number it reports moves: 412 on Monday, 380 on Tuesday, 412 again on Wednesday. Nothing failed. Every response was a <code>200</code> with well-formed JSON and a sensible-looking list of items. The field that says the answer was cut short is sitting at the top of every one of those payloads, and no code in the pipeline has ever read it.",
"short_answer": """<p>Search queries run against a server-side timeout. When a query outruns it, GitHub does not fail the request &mdash; it returns whatever it managed to find, with the top-level <code>incomplete_results</code> boolean set to <code>true</code>. The status is 200, the JSON is valid, and the only difference between a partial answer and a complete one is that flag.</p>
<p>So read it, on every <code>/search/*</code> response, and treat <code>true</code> as a retryable failure rather than as a result: do not count it, do not diff against it, and never cache it. If the flag keeps coming back on the same query, retrying is not the repair &mdash; narrow the query with <code>repo:</code>, <code>org:</code> or a <code>created:</code> range until it completes inside the timeout. This is not the thousand-result ceiling, which is a different, deterministic limit with its own note; a query well under a hundred matches can be flagged, and one with fifty thousand may not be.</p>""",
"problem": """<p>A flaky number is the hardest kind of wrong to act on, because the first response to it is disbelief and the second is a workaround. The count moved, so the data moved, so somebody explains it: issues were closed overnight, the index is catching up, search is eventually consistent, it settles down. Every one of those explanations is plausible, none of them is checkable, and all of them let the pipeline carry on treating a partial answer as an answer.</p>
<p>It is worse when the consumer is a comparison rather than a report. A job that diffs today's search results against yesterday's, and acts on the difference, will open tickets, page people or revoke access based on rows that did not disappear &mdash; they were simply not found this morning. The flag was true and the code read <code>items</code>.</p>
<p>And a cache turns an intermittent problem into a permanent one. A partial answer stored under a key that does not encode its own partiality gets served for the rest of its lifetime as though it were the whole set. The one run in ten that timed out becomes the answer everybody sees, and by the time somebody notices, the request that produced it is long gone and unreproducible.</p>""",
"why": """<p><strong>The timeout is served rather than raised.</strong> Search has a bounded amount of time to answer, and the design decision when it runs out is to return partial results with a flag rather than to return an error. That is defensible &mdash; a partial answer is usually more useful than a 504 &mdash; and it puts the entire burden on the client to read one boolean. There is no status code, no header and no error object to trip over.</p>
<p><strong>It is not the thousand-result cap.</strong> The Search API also refuses to page past 1,000 results per query, which is a hard, deterministic ceiling that announces itself with a <code>422</code> and <a href="/github/search-1000-result-cap/">has its own note</a>. This flag is a different animal: it is non-deterministic, it fires on the first page, and it fires on queries nowhere near the cap. The script reads <code>total_count</code> and says explicitly whether the ceiling could be an explanation, because being able to rule it out by name is what stops the two problems being conflated.</p>
<p><strong>It is a property of the query, not of the API's health.</strong> Broad queries time out: no <code>repo:</code> or <code>org:</code>, no date range, a full-text term that matches across everything, a regular expression or a long list of <code>OR</code>ed qualifiers. A narrow query with the same result count usually completes. That is why the durable repair is to make the question smaller rather than to ask it again, and why a query that is flagged on every attempt will not be fixed by any retry policy.</p>
<p><strong>One run cannot tell you what you need to know.</strong> A single flagged response says this attempt was partial. It does not say whether the query is occasionally unlucky, in which case retrying is a genuine repair, or reliably too broad, in which case retrying is a way of spending your search bucket on the same partial answer. The distinction is only visible across repeated runs of the same query, which is why the check makes a few and reasons about the sequence.</p>
<p><strong>An unflagged response can still be partial.</strong> If the item counts move between identical consecutive runs and no round was flagged, something is truncating or reordering underneath you regardless. The honest verdict there is the same as for a flagged round: treat it as a retry, do not cache it, and do not diff against it.</p>
<p><strong>Search has its own rate bucket, so the check has to be small.</strong> Search does not draw on the <code>core</code> quota; it has a separate and much tighter allowance, and <a href="/github/search-bucket-exhausted/">exhausting it</a> is its own failure. The check therefore defaults to one query and three rounds, three requests in total, prints that number before it spends anything, and refuses to run a plan that would not fit in the bucket.</p>""",
"steps": [
 {"h": "Read the flag on every search response",
  "body": """<p><code>incomplete_results</code> is a top-level boolean next to <code>total_count</code> and <code>items</code>. One branch. If it is <code>true</code>, the list you are holding is a subset of the matches and you do not know which subset. This is the entire fix for most integrations and it takes a line.</p>"""},
 {"h": "Run the same query a few times before concluding anything",
  "body": """<p>One flagged response tells you this attempt was cut short. Three tell you whether the query is occasionally unlucky or reliably too broad, and those two states have opposite repairs. The check defaults to three rounds with a short pause between them, which is three of your search requests.</p>"""},
 {"h": "Rule the thousand-result ceiling out by name",
  "body": """<p>Read <code>total_count</code> and say plainly whether it is above 1,000. If it is not, the ceiling cannot be the explanation and nobody needs to spend an afternoon on it. If it is, you have two separate problems that happen to look alike from the outside, and they need repairing separately.</p>"""},
 {"h": "Narrow the query rather than retrying it",
  "body": """<p>Where every round is flagged, no retry policy will help. Add a scope (<code>repo:</code> or <code>org:</code>), add a date range (<code>created:</code> or <code>updated:</code>), or split one broad query into several narrow ones and union the results yourself. The script reports which of those qualifiers your query does not already have.</p>"""},
 {"h": "Make a flagged response uncacheable and undiffable",
  "body": """<p>Anything with the flag set must not be written to a cache, compared against a previous run, or used to decide that something has disappeared. A partial answer stored without a note of its partiality becomes the permanent truth, and a diff against a partial answer manufactures deletions that never happened.</p>"""},
],
"verify": """<p>After the query is scoped to one organization and a date range, the same probe reports three clean rounds with a stable count and nothing to retry.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_search_incomplete.py \\
  --query 'is:issue is:open label:security'
# read cost: 3 search request(s) of the 30 per minute search bucket
# round 1: 412 item(s), total_count 412, incomplete_results=true
# round 2: 380 item(s), total_count 412, incomplete_results=true
# round 3: 412 item(s), total_count 412, incomplete_results=false
# timed-out-intermittent: 2 of 3 rounds came back partial. total_count is 412,
# well inside the 1000-result ceiling, so the ceiling is not the explanation
# missing from the query: repo: or org:, created: or updated: date range
# repair: treat a flagged response as a retry, never as a result, and never cache it

# after the query is scoped
GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_search_incomplete.py \\
  --query 'org:acme is:issue is:open label:security created:>2026-01-01'
# complete: 3 of 3 rounds were unflagged and the item count did not move</code></pre>""",
"code_intro": "The same query sent a small number of times with a pause between, because a single response cannot separate a partial answer from a small one. Three fields are kept from each round and the rest of the payload is discarded: the flag, the reported total and the number of items actually delivered. Everything after that is a pure function over the sequence, which is what lets the script say whether retrying is a repair or a waste. The reported total is checked against the retrievable ceiling for one reason only, which is so the script can rule that explanation out by name rather than leaving two similar-looking problems tangled together.",
"py_file": "github_search_incomplete.py",
"py": '''"""Say whether a GitHub search is being answered in part and nobody noticed.

Read only. One GET per round against /search/*, three rounds by default, with a
pause between them. Nothing is written.

Search runs against a server-side timeout. When a query outruns it GitHub does
not fail: it returns what it found with the top-level incomplete_results boolean
set to true. Status 200, valid JSON, fewer items, no error anywhere. A client
that reads items and ignores the flag treats a partial answer as a complete one,
and the count quietly moves between runs.

This is not the 1,000-result ceiling. That limit is deterministic, announces
itself with a 422 when you page past it, and applies to queries with more than a
thousand matches. This flag is non-deterministic, arrives on the first page, and
fires on queries nowhere near the cap. total_count is read here purely so the
ceiling can be ruled out by name.

Search has its own rate bucket, separate from and much tighter than core, so
this check is deliberately tiny and refuses a plan that would not fit in it.

Environment:

    GITHUB_TOKEN    any token with read access; search needs authentication to
                    get the larger of the two search buckets
"""
import argparse
import json
import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_search_incomplete")

API = "https://api.github.com"
UA = "github-search-incomplete/1.0"

# The other Search limit, read only so it can be excluded as an explanation.
RESULT_CAP = 1000
# Authenticated search requests per minute. The check is sized against this.
SEARCH_BUCKET = 30

QUALIFIER = re.compile(r"(?:^|\\s)-?([A-Za-z_]+):\\S")

SCOPES = ("repo", "org", "user")
RANGES = ("created", "updated", "merged", "closed")


def flagged(body):
    """Whether this response says it is partial. Pure."""
    return bool(isinstance(body, dict) and body.get("incomplete_results") is True)


def total_of(body):
    """The reported match count, or None. Pure."""
    if not isinstance(body, dict):
        return None
    try:
        return int(body.get("total_count"))
    except (TypeError, ValueError):
        return None


def item_count(body):
    """How many items were actually delivered. Pure."""
    if not isinstance(body, dict):
        return 0
    items = body.get("items")
    return len(items) if isinstance(items, list) else 0


def cacheable(body):
    """Whether this response may be stored. Pure.

    The rule the whole note comes down to: a partial answer written to a cache
    without a note of its partiality becomes the permanent truth.
    """
    return isinstance(body, dict) and not flagged(body)


def above_result_cap(total):
    """Whether the ceiling could also be in play here. Pure."""
    try:
        return int(total) > RESULT_CAP
    except (TypeError, ValueError):
        return False


def qualifiers(query):
    """The qualifier names used in a search query. Pure."""
    return set(QUALIFIER.findall(" " + str(query or "")))


def narrowing(query):
    """Which narrowing devices the query is not already using. Pure."""
    have = qualifiers(query)
    out = []
    if not have & set(SCOPES):
        out.append("repo: or org:")
    if not have & set(RANGES):
        out.append("created: or updated: date range")
    if "language" not in have:
        out.append("language:")
    return out


def observe(body):
    """The three fields worth keeping from one response. Pure."""
    return {"incomplete": flagged(body),
            "total": total_of(body),
            "items": item_count(body)}


def summarise(observations):
    """Counts over the sequence of rounds. Pure."""
    obs = list(observations or [])
    return {"rounds": len(obs),
            "flagged": sum(1 for o in obs if o.get("incomplete")),
            "item_counts": [o.get("items") for o in obs],
            "totals": [o.get("total") for o in obs]}


def counts_stable(observations):
    """Whether identical queries returned identical item counts. Pure."""
    counts = [o.get("items") for o in (observations or [])]
    return len(set(counts)) <= 1


def max_total(observations):
    """The largest reported match count across the rounds, or None. Pure."""
    totals = [o.get("total") for o in (observations or [])
              if o.get("total") is not None]
    return max(totals) if totals else None


def verdict(observations):
    """Classify the sequence. Pure. Returns (state, detail).

    Built from the sequence rather than from any one response, because a single
    flagged round cannot distinguish an unlucky query from a hopeless one, and
    those two have opposite repairs.
    """
    s = summarise(observations)
    if not s["rounds"]:
        return ("no-observations", "no round completed, so there is nothing to judge.")
    top = max_total(observations)
    ceiling = (" total_count is %s, well inside the %d-result ceiling, so the "
               "ceiling is not the explanation." % (top, RESULT_CAP)
               if top is not None and not above_result_cap(top) else "")
    if s["flagged"] and top is not None and above_result_cap(top):
        return ("timed-out-and-capped",
                "%d of %d round(s) came back partial and total_count is %s, "
                "which is also above the %d-result ceiling. These are two "
                "separate problems that look alike from outside and need "
                "repairing separately."
                % (s["flagged"], s["rounds"], top, RESULT_CAP))
    if s["flagged"] == s["rounds"]:
        return ("timed-out-always",
                "every one of %d round(s) came back partial, so this query does "
                "not finish inside the search timeout. No retry policy will fix "
                "that.%s" % (s["rounds"], ceiling))
    if s["flagged"]:
        return ("timed-out-intermittent",
                "%d of %d round(s) came back partial, so the query sometimes "
                "finishes and sometimes does not. A flagged response is a retry, "
                "not a result.%s" % (s["flagged"], s["rounds"], ceiling))
    if not counts_stable(observations):
        return ("unstable-counts",
                "no round was flagged, but identical queries returned %s "
                "item(s) across the rounds. Something is truncating or "
                "reordering underneath you, and the answer should be treated "
                "the same way as a flagged one."
                % " and ".join(str(c) for c in sorted(set(s["item_counts"]))))
    return ("complete",
            "%d of %d round(s) were unflagged and the item count did not move."
            % (s["rounds"], s["rounds"]))


def retry_or_narrow(observations):
    """What actually helps: retry, narrow, or nothing. Pure."""
    state = verdict(observations)[0]
    if state in ("timed-out-always", "timed-out-and-capped"):
        return "narrow"
    if state in ("timed-out-intermittent", "unstable-counts"):
        return "retry"
    return "nothing"


def repair(state, query=""):
    """The sentence a reader has to act on. Pure."""
    missing = ", ".join(narrowing(query)) or "nothing obvious"
    if state == "timed-out-always":
        return ("narrow the query until it finishes: add %s. Retrying will "
                "spend your search bucket on the same partial answer." % missing)
    if state == "timed-out-and-capped":
        return ("narrow the query until it finishes and until each slice reports "
                "under %d matches: add %s, then union the slices yourself."
                % (RESULT_CAP, missing))
    if state == "timed-out-intermittent":
        return ("treat a flagged response as a retry, never as a result, and "
                "never cache it. If the flag keeps coming back, add %s." % missing)
    if state == "unstable-counts":
        return ("treat this the same as a flagged response: do not cache it and "
                "do not diff against it. A moving count with no flag is still a "
                "moving count.")
    return "nothing."


def read_cost(queries, rounds):
    """Search requests this run will spend. Pure."""
    try:
        return max(0, len(queries or [])) * max(0, int(rounds))
    except (TypeError, ValueError):
        return 0


def within_search_bucket(cost):
    """Whether a plan of this size fits the per-minute search allowance. Pure."""
    try:
        return 0 < int(cost) <= SEARCH_BUCKET
    except (TypeError, ValueError):
        return False


def search(session, kind, query, per_page):
    """One search GET. Returns the decoded body or None."""
    r = session.get("%s/search/%s" % (API, kind),
                    params={"q": query, "per_page": per_page}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403:
        raise SystemExit("403 from search. The search bucket is separate from "
                         "core and much tighter; wait for the window to reset")
    if r.status_code == 422:
        raise SystemExit("422 from search: the query is invalid, or you paged "
                         "past the %d-result ceiling" % RESULT_CAP)
    if r.status_code != 200:
        log.info("search returned %d", r.status_code)
        return None
    try:
        return r.json()
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True, help="the search query, as sent")
    ap.add_argument("--kind", default="issues",
                    help="issues, repositories, code, users, commits")
    ap.add_argument("--rounds", type=int, default=3,
                    help="how many times to run the same query")
    ap.add_argument("--pause", type=float, default=2.0,
                    help="seconds between rounds")
    ap.add_argument("--per-page", type=int, default=100,
                    help="page size for each round")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN. Unauthenticated search gets a much smaller "
                  "bucket and this check would exhaust it")
        return 2

    cost = read_cost([args.query], args.rounds)
    if not within_search_bucket(cost):
        log.error("%d request(s) does not fit the %d per minute search bucket; "
                  "lower --rounds", cost, SEARCH_BUCKET)
        return 2
    log.info("read cost: %d search request(s) of the %d per minute search bucket",
             cost, SEARCH_BUCKET)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    observations = []
    for n in range(args.rounds):
        if n:
            time.sleep(args.pause)
        body = search(session, args.kind, args.query, args.per_page)
        if body is None:
            continue
        o = observe(body)
        observations.append(o)
        log.info("round %d: %d item(s), total_count %s, incomplete_results=%s",
                 n + 1, o["items"], o["total"], str(o["incomplete"]).lower())
        if not cacheable(body):
            log.info("round %d must not be cached or diffed against", n + 1)

    state, detail = verdict(observations)
    log.info("%s: %s", state, detail)
    missing = narrowing(args.query)
    if missing:
        log.info("missing from the query: %s", ", ".join(missing))
    log.info("what helps: %s", retry_or_narrow(observations))
    log.info("repair: %s", repair(state, args.query))

    print(json.dumps({"query": args.query,
                      "requests_spent": len(observations),
                      "summary": summarise(observations),
                      "counts_stable": counts_stable(observations),
                      "total_above_cap": above_result_cap(max_total(observations)),
                      "qualifiers_used": sorted(qualifiers(args.query)),
                      "narrowing_available": missing,
                      "action": retry_or_narrow(observations),
                      "state": state,
                      "detail": detail}, indent=2, default=str))
    return 1 if state not in ("complete", "no-observations") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-search-incomplete.mjs",
"js": '''/**
 * Say whether a GitHub search is being answered in part and nobody noticed.
 *
 * Read only. One GET per round against /search/*, three rounds by default,
 * with a pause between them. Nothing is written.
 *
 * Search runs against a server-side timeout. When a query outruns it, GitHub
 * returns what it found with incomplete_results set to true rather than
 * failing. This is not the 1,000-result ceiling: total_count is read here
 * purely so that ceiling can be ruled out by name.
 *
 * Environment:
 *   GITHUB_TOKEN   any token with read access
 *   GITHUB_QUERY   the search query, as sent
 *   GITHUB_KIND    issues, repositories, code, users, commits. Default issues
 *   GITHUB_ROUNDS  how many times to run the same query. Default 3
 */
const API = 'https://api.github.com';
const UA = 'github-search-incomplete/1.0';

/** The other Search limit, read only so it can be excluded as an explanation. */
export const RESULT_CAP = 1000;
/** Authenticated search requests per minute. The check is sized against this. */
export const SEARCH_BUCKET = 30;

const QUALIFIER = /(?:^|\\s)-?([A-Za-z_]+):\\S/g;

export const SCOPES = ['repo', 'org', 'user'];
export const RANGES = ['created', 'updated', 'merged', 'closed'];

/** Whether this response says it is partial. Pure. */
export function flagged(body) {
  return Boolean(body && typeof body === 'object' && body.incomplete_results === true);
}

/** The reported match count, or null. Pure. */
export function totalOf(body) {
  if (!body || typeof body !== 'object') return null;
  const raw = body.total_count;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

/** How many items were actually delivered. Pure. */
export function itemCount(body) {
  if (!body || typeof body !== 'object') return 0;
  return Array.isArray(body.items) ? body.items.length : 0;
}

/** Whether this response may be stored. Pure. */
export function cacheable(body) {
  return Boolean(body && typeof body === 'object') && !flagged(body);
}

/** Whether the ceiling could also be in play here. Pure. */
export function aboveResultCap(total) {
  const n = Number(total);
  return Number.isFinite(n) && n > RESULT_CAP;
}

/** The qualifier names used in a search query. Pure. */
export function qualifiers(query) {
  const out = new Set();
  for (const m of ` ${String(query ?? '')}`.matchAll(QUALIFIER)) out.add(m[1]);
  return out;
}

/** Which narrowing devices the query is not already using. Pure. */
export function narrowing(query) {
  const have = qualifiers(query);
  const out = [];
  if (!SCOPES.some((s) => have.has(s))) out.push('repo: or org:');
  if (!RANGES.some((s) => have.has(s))) out.push('created: or updated: date range');
  if (!have.has('language')) out.push('language:');
  return out;
}

/** The three fields worth keeping from one response. Pure. */
export function observe(body) {
  return { incomplete: flagged(body), total: totalOf(body), items: itemCount(body) };
}

/** Counts over the sequence of rounds. Pure. */
export function summarise(observations) {
  const obs = Array.isArray(observations) ? observations : [];
  return {
    rounds: obs.length,
    flagged: obs.filter((o) => o && o.incomplete).length,
    item_counts: obs.map((o) => (o || {}).items),
    totals: obs.map((o) => (o || {}).total),
  };
}

/** Whether identical queries returned identical item counts. Pure. */
export function countsStable(observations) {
  const counts = (Array.isArray(observations) ? observations : []).map((o) => (o || {}).items);
  return new Set(counts).size <= 1;
}

/** The largest reported match count across the rounds, or null. Pure. */
export function maxTotal(observations) {
  const totals = (Array.isArray(observations) ? observations : [])
    .map((o) => (o || {}).total).filter((t) => t !== null && t !== undefined);
  return totals.length ? Math.max(...totals) : null;
}

/** Classify the sequence. Pure. Returns [state, detail]. */
export function verdict(observations) {
  const s = summarise(observations);
  if (!s.rounds) return ['no-observations', 'no round completed, so there is nothing to judge.'];
  const top = maxTotal(observations);
  const ceiling = top !== null && !aboveResultCap(top)
    ? ` total_count is ${top}, well inside the ${RESULT_CAP}-result ceiling, so the ceiling is not the explanation.`
    : '';
  if (s.flagged && top !== null && aboveResultCap(top)) {
    return ['timed-out-and-capped',
      `${s.flagged} of ${s.rounds} round(s) came back partial and total_count is `
      + `${top}, which is also above the ${RESULT_CAP}-result ceiling. These are `
      + 'two separate problems that look alike from outside and need repairing separately.'];
  }
  if (s.flagged === s.rounds) {
    return ['timed-out-always',
      `every one of ${s.rounds} round(s) came back partial, so this query does not `
      + `finish inside the search timeout. No retry policy will fix that.${ceiling}`];
  }
  if (s.flagged) {
    return ['timed-out-intermittent',
      `${s.flagged} of ${s.rounds} round(s) came back partial, so the query `
      + 'sometimes finishes and sometimes does not. A flagged response is a '
      + `retry, not a result.${ceiling}`];
  }
  if (!countsStable(observations)) {
    const seen = [...new Set(s.item_counts)].sort((a, b) => a - b).join(' and ');
    return ['unstable-counts',
      `no round was flagged, but identical queries returned ${seen} item(s) across `
      + 'the rounds. Something is truncating or reordering underneath you, and the '
      + 'answer should be treated the same way as a flagged one.'];
  }
  return ['complete',
    `${s.rounds} of ${s.rounds} round(s) were unflagged and the item count did not move.`];
}

/** What actually helps: retry, narrow, or nothing. Pure. */
export function retryOrNarrow(observations) {
  const state = verdict(observations)[0];
  if (['timed-out-always', 'timed-out-and-capped'].includes(state)) return 'narrow';
  if (['timed-out-intermittent', 'unstable-counts'].includes(state)) return 'retry';
  return 'nothing';
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, query = '') {
  const missing = narrowing(query).join(', ') || 'nothing obvious';
  if (state === 'timed-out-always') {
    return `narrow the query until it finishes: add ${missing}. Retrying will `
      + 'spend your search bucket on the same partial answer.';
  }
  if (state === 'timed-out-and-capped') {
    return 'narrow the query until it finishes and until each slice reports under '
      + `${RESULT_CAP} matches: add ${missing}, then union the slices yourself.`;
  }
  if (state === 'timed-out-intermittent') {
    return 'treat a flagged response as a retry, never as a result, and never '
      + `cache it. If the flag keeps coming back, add ${missing}.`;
  }
  if (state === 'unstable-counts') {
    return 'treat this the same as a flagged response: do not cache it and do not '
      + 'diff against it. A moving count with no flag is still a moving count.';
  }
  return 'nothing.';
}

/** Search requests this run will spend. Pure. */
export function readCost(queries, rounds) {
  const q = Array.isArray(queries) ? queries.length : 0;
  const r = Number(rounds);
  return q * (Number.isFinite(r) && r > 0 ? Math.trunc(r) : 0);
}

/** Whether a plan of this size fits the per-minute search allowance. Pure. */
export function withinSearchBucket(cost) {
  const n = Number(cost);
  return Number.isFinite(n) && n > 0 && n <= SEARCH_BUCKET;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

const wait = (ms) => new Promise((resolve) => { setTimeout(resolve, ms); });

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const query = process.env.GITHUB_QUERY;
  if (!token || !query) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_QUERY');
    process.exitCode = 2;
    return;
  }
  const kind = process.env.GITHUB_KIND || 'issues';
  const rounds = Number(process.env.GITHUB_ROUNDS || 3);
  const cost = readCost([query], rounds);
  if (!withinSearchBucket(cost)) {
    console.error(`${cost} request(s) does not fit the ${SEARCH_BUCKET} per minute search bucket`);
    process.exitCode = 2;
    return;
  }
  console.log(`read cost: ${cost} search request(s) of the ${SEARCH_BUCKET} per minute search bucket`);

  const observations = [];
  for (let n = 0; n < rounds; n += 1) {
    if (n) await wait(2000);
    const url = new URL(`${API}/search/${kind}`);
    url.searchParams.set('q', query);
    url.searchParams.set('per_page', '100');
    const res = await fetch(url, { headers: headers(token) });
    if (res.status !== 200) {
      console.error(`search returned ${res.status}`);
      continue;
    }
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    if (body === null) continue;
    const o = observe(body);
    observations.push(o);
    console.log(`round ${n + 1}: ${o.items} item(s), total_count ${o.total}, `
      + `incomplete_results=${o.incomplete}`);
    if (!cacheable(body)) console.log(`round ${n + 1} must not be cached or diffed against`);
  }

  const [state, detail] = verdict(observations);
  console.log(`${state}: ${detail}`);
  const missing = narrowing(query);
  if (missing.length) console.log(`missing from the query: ${missing.join(', ')}`);
  console.log(`what helps: ${retryOrNarrow(observations)}`);
  console.log(`repair: ${repair(state, query)}`);

  console.log(JSON.stringify({
    query,
    requests_spent: observations.length,
    summary: summarise(observations),
    counts_stable: countsStable(observations),
    total_above_cap: aboveResultCap(maxTotal(observations)),
    qualifiers_used: [...qualifiers(query)].sort(),
    narrowing_available: missing,
    action: retryOrNarrow(observations),
    state,
    detail,
  }, null, 2));
  process.exitCode = ['complete', 'no-observations'].includes(state) ? 0 : 1;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The sequence logic carries the note, so it is what gets tested hardest: a query flagged on every round and one flagged on some of them have to reach different verdicts, because the first is narrowed and the second is retried and telling a reader to do the wrong one wastes a week. Beside that, the ceiling is asserted to be excluded by name on queries under a thousand matches and reported as a second, separate problem above it; a moving count with no flag has to be caught at all; the flag has to be strictly true rather than merely truthy; and the caching rule is asserted directly, since it is the sentence most likely to be skipped on the way to the code.",
"test_py_file": "test_github_search_incomplete.py",
"test_py": '''from github_search_incomplete import (
    RESULT_CAP, SEARCH_BUCKET, above_result_cap, cacheable, counts_stable,
    flagged, item_count, max_total, narrowing, observe, qualifiers, read_cost,
    repair, retry_or_narrow, summarise, total_of, verdict, within_search_bucket,
)

PARTIAL = {"total_count": 412, "incomplete_results": True,
           "items": [{"id": 1}, {"id": 2}]}
WHOLE = {"total_count": 412, "incomplete_results": False,
         "items": [{"id": 1}, {"id": 2}, {"id": 3}]}


def test_the_flag_is_read_strictly_rather_than_truthily():
    assert flagged(PARTIAL)
    assert not flagged(WHOLE)
    assert not flagged({"incomplete_results": "true"})
    assert not flagged({"incomplete_results": 1})
    assert not flagged({})
    assert not flagged(None)


def test_the_three_kept_fields_survive_a_malformed_payload():
    assert observe(PARTIAL) == {"incomplete": True, "total": 412, "items": 2}
    assert total_of({"total_count": "412"}) == 412
    assert total_of({"total_count": None}) is None
    assert total_of([]) is None
    assert item_count({"items": None}) == 0
    assert item_count(None) == 0


def test_a_flagged_response_may_never_be_cached():
    assert not cacheable(PARTIAL)
    assert cacheable(WHOLE)
    assert not cacheable(None)


def test_every_round_partial_is_narrowed_not_retried():
    obs = [observe(PARTIAL)] * 3
    state, detail = verdict(obs)
    assert state == "timed-out-always"
    assert "No retry policy will fix that" in detail
    assert retry_or_narrow(obs) == "narrow"


def test_some_rounds_partial_is_retried_not_narrowed():
    obs = [observe(PARTIAL), observe(WHOLE), observe(WHOLE)]
    state, detail = verdict(obs)
    assert state == "timed-out-intermittent"
    assert "1 of 3" in detail
    assert retry_or_narrow(obs) == "retry"


def test_the_thousand_result_ceiling_is_ruled_out_by_name():
    detail = verdict([observe(PARTIAL)] * 2)[1]
    assert "1000-result ceiling" in detail
    assert "not the explanation" in detail


def test_a_query_over_the_ceiling_is_reported_as_two_problems():
    big = dict(PARTIAL, total_count=24831)
    state, detail = verdict([observe(big)] * 2)
    assert state == "timed-out-and-capped"
    assert "two separate problems" in detail
    assert retry_or_narrow([observe(big)] * 2) == "narrow"


def test_a_moving_count_with_no_flag_is_still_caught():
    obs = [observe(WHOLE), observe(dict(WHOLE, items=[{"id": 1}]))]
    state, detail = verdict(obs)
    assert state == "unstable-counts"
    assert "no round was flagged" in detail
    assert retry_or_narrow(obs) == "retry"


def test_three_clean_stable_rounds_are_not_a_finding():
    obs = [observe(WHOLE)] * 3
    assert verdict(obs)[0] == "complete"
    assert retry_or_narrow(obs) == "nothing"
    assert counts_stable(obs)


def test_no_rounds_is_not_reported_as_a_clean_result():
    assert verdict([])[0] == "no-observations"
    assert summarise([]) == {"rounds": 0, "flagged": 0, "item_counts": [], "totals": []}
    assert max_total([]) is None


def test_the_ceiling_predicate_is_strictly_above_the_cap():
    assert above_result_cap(RESULT_CAP + 1)
    assert not above_result_cap(RESULT_CAP)
    assert not above_result_cap(None)


def test_the_query_is_read_for_the_qualifiers_it_already_has():
    assert qualifiers("is:issue repo:acme/api label:bug") == {"is", "repo", "label"}
    assert qualifiers("-org:acme is:open") == {"org", "is"}
    assert qualifiers("") == set()
    assert qualifiers(None) == set()


def test_narrowing_suggests_only_what_is_missing():
    assert narrowing("is:issue state:open") == [
        "repo: or org:", "created: or updated: date range", "language:"]
    assert narrowing("org:acme created:>2026-01-01 language:go") == []
    assert narrowing("repo:acme/api updated:>2026-01-01") == ["language:"]


def test_the_repair_tells_a_hopeless_query_not_to_retry():
    fix = repair("timed-out-always", "is:issue state:open")
    assert "narrow the query" in fix
    assert "repo: or org:" in fix
    assert "Retrying will" in fix
    assert "never cache it" in repair("timed-out-intermittent", "is:issue")


def test_the_check_refuses_a_plan_that_would_not_fit_the_search_bucket():
    assert read_cost(["q"], 3) == 3
    assert read_cost(["a", "b"], 4) == 8
    assert read_cost([], 3) == 0
    assert within_search_bucket(3)
    assert within_search_bucket(SEARCH_BUCKET)
    assert not within_search_bucket(SEARCH_BUCKET + 1)
    assert not within_search_bucket(0)
''',
"test_js_file": "github-search-incomplete.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  RESULT_CAP, SEARCH_BUCKET, aboveResultCap, cacheable, countsStable, flagged,
  itemCount, maxTotal, narrowing, observe, qualifiers, readCost, repair,
  retryOrNarrow, summarise, totalOf, verdict, withinSearchBucket,
} from './github-search-incomplete.mjs';

const PARTIAL = { total_count: 412, incomplete_results: true, items: [{ id: 1 }, { id: 2 }] };
const WHOLE = {
  total_count: 412, incomplete_results: false, items: [{ id: 1 }, { id: 2 }, { id: 3 }],
};

test('the flag is read strictly rather than truthily', () => {
  assert.ok(flagged(PARTIAL));
  assert.ok(!flagged(WHOLE));
  assert.ok(!flagged({ incomplete_results: 'true' }));
  assert.ok(!flagged({ incomplete_results: 1 }));
  assert.ok(!flagged({}));
  assert.ok(!flagged(null));
});

test('the three kept fields survive a malformed payload', () => {
  assert.deepEqual(observe(PARTIAL), { incomplete: true, total: 412, items: 2 });
  assert.equal(totalOf({ total_count: '412' }), 412);
  assert.equal(totalOf({ total_count: null }), null);
  assert.equal(itemCount({ items: null }), 0);
  assert.equal(itemCount(null), 0);
});

test('a flagged response may never be cached', () => {
  assert.ok(!cacheable(PARTIAL));
  assert.ok(cacheable(WHOLE));
  assert.ok(!cacheable(null));
});

test('every round partial is narrowed, not retried', () => {
  const obs = [observe(PARTIAL), observe(PARTIAL), observe(PARTIAL)];
  const [state, detail] = verdict(obs);
  assert.equal(state, 'timed-out-always');
  assert.match(detail, /No retry policy will fix that/);
  assert.equal(retryOrNarrow(obs), 'narrow');
});

test('some rounds partial is retried, not narrowed', () => {
  const obs = [observe(PARTIAL), observe(WHOLE), observe(WHOLE)];
  const [state, detail] = verdict(obs);
  assert.equal(state, 'timed-out-intermittent');
  assert.match(detail, /1 of 3/);
  assert.equal(retryOrNarrow(obs), 'retry');
});

test('the thousand-result ceiling is ruled out by name', () => {
  const detail = verdict([observe(PARTIAL), observe(PARTIAL)])[1];
  assert.match(detail, /1000-result ceiling/);
  assert.match(detail, /not the explanation/);
});

test('a query over the ceiling is reported as two problems', () => {
  const big = { ...PARTIAL, total_count: 24831 };
  const obs = [observe(big), observe(big)];
  const [state, detail] = verdict(obs);
  assert.equal(state, 'timed-out-and-capped');
  assert.match(detail, /two separate problems/);
  assert.equal(retryOrNarrow(obs), 'narrow');
});

test('a moving count with no flag is still caught', () => {
  const obs = [observe(WHOLE), observe({ ...WHOLE, items: [{ id: 1 }] })];
  const [state, detail] = verdict(obs);
  assert.equal(state, 'unstable-counts');
  assert.match(detail, /no round was flagged/);
  assert.equal(retryOrNarrow(obs), 'retry');
});

test('three clean stable rounds are not a finding', () => {
  const obs = [observe(WHOLE), observe(WHOLE), observe(WHOLE)];
  assert.equal(verdict(obs)[0], 'complete');
  assert.equal(retryOrNarrow(obs), 'nothing');
  assert.ok(countsStable(obs));
});

test('no rounds is not reported as a clean result', () => {
  assert.equal(verdict([])[0], 'no-observations');
  assert.deepEqual(summarise([]), {
    rounds: 0, flagged: 0, item_counts: [], totals: [],
  });
  assert.equal(maxTotal([]), null);
});

test('the ceiling predicate is strictly above the cap', () => {
  assert.ok(aboveResultCap(RESULT_CAP + 1));
  assert.ok(!aboveResultCap(RESULT_CAP));
  assert.ok(!aboveResultCap(null));
});

test('the query is read for the qualifiers it already has', () => {
  assert.deepEqual([...qualifiers('is:issue repo:acme/api label:bug')].sort(),
    ['is', 'label', 'repo']);
  assert.deepEqual([...qualifiers('-org:acme is:open')].sort(), ['is', 'org']);
  assert.equal(qualifiers('').size, 0);
  assert.equal(qualifiers(null).size, 0);
});

test('narrowing suggests only what is missing', () => {
  assert.deepEqual(narrowing('is:issue state:open'),
    ['repo: or org:', 'created: or updated: date range', 'language:']);
  assert.deepEqual(narrowing('org:acme created:>2026-01-01 language:go'), []);
  assert.deepEqual(narrowing('repo:acme/api updated:>2026-01-01'), ['language:']);
});

test('the repair tells a hopeless query not to retry', () => {
  const fix = repair('timed-out-always', 'is:issue state:open');
  assert.match(fix, /narrow the query/);
  assert.match(fix, /repo: or org:/);
  assert.match(fix, /Retrying will/);
  assert.match(repair('timed-out-intermittent', 'is:issue'), /never cache it/);
});

test('the check refuses a plan that would not fit the search bucket', () => {
  assert.equal(readCost(['q'], 3), 3);
  assert.equal(readCost(['a', 'b'], 4), 8);
  assert.equal(readCost([], 3), 0);
  assert.ok(withinSearchBucket(3));
  assert.ok(withinSearchBucket(SEARCH_BUCKET));
  assert.ok(!withinSearchBucket(SEARCH_BUCKET + 1));
  assert.ok(!withinSearchBucket(0));
});
''',
"faq": [
 ("Is this the same as the 1,000-result cap?",
  "No, and keeping them apart is most of the value of the note. The cap is deterministic: it applies to queries with more than a thousand matches, it announces itself with a 422 when you page past it, and the fix is to partition the query into slices that each report under a thousand. This flag is non-deterministic, arrives on the very first page, and fires on queries with a few hundred matches. The script reads total_count and says in the output whether the ceiling could be an explanation, so nobody spends an afternoon on the wrong limit."),
 ("Should I just retry until the flag is false?",
  "Only if it is sometimes false. A query that comes back flagged on every attempt is not unlucky, it is too broad to finish inside the timeout, and a retry loop against it will spend your search bucket producing the same partial answer more times. That is why the check runs the query more than once: the difference between sometimes and always is the difference between a retry policy and a rewritten query, and one run cannot tell you which you have."),
 ("Can I cache a response that had incomplete_results set?",
  "No. It is the single rule most worth taking from this note. A partial answer written to a cache under a key that does not encode its own partiality becomes the permanent answer for the lifetime of that entry, and the run that produced it is long gone by the time anyone questions it. The same applies to diffing: comparing today's partial results against yesterday's complete ones manufactures deletions that never happened, and if something acts on those deletions the damage is real."),
 ("The count moves but the flag is always false. What then?",
  "Treat it exactly like a flagged response. If two identical queries a few seconds apart return different item counts and nothing was flagged, something is truncating or reordering underneath you regardless of what the payload claims, and the answer is not stable enough to cache or to diff against. The check gives that its own state rather than reporting it as clean, because a clean verdict on a moving number is how a diagnostic loses somebody's trust."),
 ("How much of the search bucket does the check use?",
  "One request per round, three by default. Search does not draw on the core hourly quota; it has a separate and much tighter allowance, roughly thirty requests a minute authenticated, and exhausting it is a failure with its own note. The script computes the plan up front, prints it, and refuses to run at all if the number of rounds you asked for would not fit inside the bucket, because a diagnostic that causes the failure next door is not worth having."),
],
"related": [
 ("/github/search-1000-result-cap/", "Search returns at most 1,000 results"),
 ("/github/search-bucket-exhausted/", "The search rate bucket is exhausted"),
 ("/github/code-search-bucket-exhausted/", "Code search has its own tighter bucket"),
],
"citations": [CITE_SEARCH, CITE_SEARCH_SYNTAX, CITE_RATE_LIMITS, CITE_BEST_PRACTICES],
},

]
