#!/usr/bin/env python3
"""/github/ field notes, batch Q — the writing.

Four notes about a request that was answered and should not have been trusted.
The section already carries the pagination bugs where the loop is the problem:
the client that never read the Link header, the page size left at the default,
the page size raised above the maximum, the endpoint that ignores `page`. None
of these four is a loop bug. Two of them are a client that paginated perfectly
and still holds a partial answer, one is a request the server refused to finish,
and one is a repository that is no longer where the config says it is.

The first is a pull request whose files and commits lists have ceilings of their
own: 3,000 and 250. The counters that would tell you so are on the pull request
object, at a different URL from the lists they describe, which is what makes
this different from the compare endpoint, where the true count arrives in the
same body as the truncated array. Here the ground truth has to be fetched.

The second is a request GitHub gives up on. About ten seconds in, an expensive
call comes back 502 or 504, which reads as transient, so the client retries the
identical expensive call and buys the identical failure. It is not a rate limit
and there is no header telling you how long to wait, which is the whole reason
it needs separating from the throttling notes: the repair is to make the request
smaller, and every second spent retrying is spent on the wrong idea.

The third is a walk whose ordering moves underneath it. The loop is correct, the
page size is correct, the Link header is followed to the end, and the job still
misses records and processes others twice, because the collection was sorted on
a field that changes while you read it. The subject is the sort key, not the
loop, and the two failure modes are not the same: an immutable key in descending
order can only ever repeat a record, while a mutable key can hide one for good.

The fourth is a repository that was renamed. The old path answers 301 forever.
A client that does not follow redirects sees an empty body and a falsy result; a
client that does follow them works, silently, and pays an extra round trip on
every call for the rest of the integration's life. This is not the 404 note: a
301 is the API telling you exactly where the resource went, and the failure is
in not writing it down.

Read only throughout. Every script prints what it will spend before it spends
it, and one of them makes its baseline measurement against GET /rate_limit
precisely because that call is free.
"""

CITE_PAGINATION = ("Using pagination in the REST API — GitHub Docs",
                   "https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api")
CITE_BEST_PRACTICES = ("Best practices for using the REST API — GitHub Docs",
                       "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_TROUBLESHOOTING = ("Troubleshooting the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_RESOURCE_LIMITS = ("Resource limitations — GitHub GraphQL API",
                        "https://docs.github.com/en/graphql/overview/resource-limitations")
CITE_RATE_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_PULLS = ("Pulls — GitHub REST API",
              "https://docs.github.com/en/rest/pulls/pulls")
CITE_COMMITS = ("Commits — GitHub REST API",
                "https://docs.github.com/en/rest/commits/commits")
CITE_ISSUES = ("Issues — GitHub REST API",
               "https://docs.github.com/en/rest/issues/issues")
CITE_REPOS = ("Repositories — GitHub REST API",
              "https://docs.github.com/en/rest/repos/repos")
CITE_MEDIA_TYPES = ("Getting started with the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api")
CITE_STATUS = ("GitHub Status",
               "https://www.githubstatus.com/")
CITE_RENAME = ("Renaming a repository — GitHub Docs",
               "https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository")

GUIDES = [

{
"slug": "pr-files-and-commits-caps",
"title": "A pull request's files and commits lists are both capped",
"description": "A review bot reports three files changed on a pull request that changed 900. The files list stops at 3,000 and the commits list at 250, with no error.",
"h1": "a pull request's files and commits lists are both capped",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api pull request files limit 3000",
             "github pr commits endpoint 250 limit",
             "github pulls files pagination truncated",
             "github changed_files does not match files endpoint",
             "github api large pull request missing files"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The review bot posts its summary on a nine-hundred-file pull request and says three files changed. Nobody reads past the first line, because a bot that has been right for a year is not a thing people audit. The pull request object knew the real number the whole time. It is just that <code>changed_files</code> lives on the pull request and the file list lives one URL further down, and nothing in either response mentions the other.",
"short_answer": """<p><code>GET /repos/{owner}/{repo}/pulls/{n}/files</code> returns at most 3,000 files, and <code>GET /repos/{owner}/{repo}/pulls/{n}/commits</code> at most 250. Both paginate at 30 an page by default, and both answer <code>200</code> with a shorter array rather than saying they stopped.</p>
<p>The counters that contradict them are on the pull request itself: <code>changed_files</code> and <code>commits</code> on <code>GET /repos/{owner}/{repo}/pulls/{n}</code>. Fetch those first, paginate the lists at <code>per_page=100</code>, and assert the collected count against the counter, failing loudly on a mismatch. Where <code>changed_files</code> exceeds 3,000 no amount of correct pagination will reach the end, and the diff has to come from the <code>application/vnd.github.diff</code> media type instead.</p>""",
"problem": """<p>Two numbers describe the same pull request and they are served by different endpoints, which is the entire mechanism. A bot that only ever calls <code>.../files</code> has no way to know what it is missing, because the response that is short does not carry the number it is short of. The bot is not ignoring a warning. There is no warning to ignore.</p>
<p>The default page size does most of the damage before either cap is reached. A client that reads one page of files at the default 30, decides that is the diff and moves on, is wrong on every pull request with 31 changed files &mdash; a much lower bar than 3,000, and one your repository crossed long ago. The cap is the ceiling; the default is the floor, and a bot can be losing data at both ends of the same endpoint.</p>
<p>What makes it stay hidden is that the truncation is plausible. Three files changed is a normal-looking answer. Two hundred and fifty commits is a normal-looking answer for a long-lived branch. Nothing in the output reads as broken, so the failure shows up as a judgment call nobody questions: the security bot that did not flag a file, the changelog that skipped a fix, the reviewer requirement that matched no owner because the owned path was on page four.</p>""",
"why": """<p><strong>The ground truth is at a different URL from the list.</strong> <code>changed_files</code>, <code>commits</code>, <code>additions</code> and <code>deletions</code> are fields on the pull request object. The lists that enumerate those things are separate endpoints with their own pagination and their own ceilings. Any check worth running therefore costs at least two requests, because it is a comparison between two responses and there is no single response that contains both sides of it.</p>
<p><strong>Two different caps, two different repairs.</strong> Files stop at 3,000, commits at 250. Above the commit cap the answer is a different endpoint: <code>GET /repos/{owner}/{repo}/commits</code> with a <code>sha</code> and a range paginates conventionally and has no such ceiling. Above the file cap the answer is not an endpoint at all but a media type &mdash; request the pull request with <code>application/vnd.github.diff</code> and parse the diff, because the JSON list is simply not going to hand you file 3,001.</p>
<p><strong>This is not the compare endpoint's 250-commit cap.</strong> <a href="/github/compare-250-commit-cap/">That note</a> is about <code>/compare/{base}...{head}</code>, where <code>total_commits</code> arrives in the same body as the truncated array, so the finding is arithmetic you can do on one response. Here the counter is on another resource entirely, and a client that never fetches it cannot detect the truncation at all. Same number, 250, in both places; completely different detection.</p>
<p><strong>Pagination is necessary and not sufficient.</strong> A client that follows <code>rel="next"</code> to the end of <code>.../files</code> is doing the right thing and still stops at 3,000 on a big enough pull request, with no <code>rel="next"</code> left to warn it. That is why the check compares against a counter rather than against the shape of the last page: the header is telling the truth about the endpoint, and the endpoint is not telling the whole truth about the pull request.</p>
<p><strong>The pull requests that trip it are the ones that matter.</strong> Vendored dependency bumps, generated clients, framework upgrades, the merge of a long-running branch. These are exactly the changes a review bot exists to look at, and exactly the ones where its answer is truncated. A bot that is right on small pull requests and quietly wrong on large ones is worse than no bot, because it is trusted in inverse proportion to how correct it is.</p>
<p><strong>The API cannot see your collector, so the script measures the endpoint.</strong> Nothing GitHub returns says how many pages your bot read. What a read-only script can do is state the declared counts, ask each list endpoint how far it is willing to go by reading its <code>Link</code> header at <code>per_page=100</code>, and report where those two things cannot be reconciled. That is the gap; whether your code falls into it is one loop away and the script prints the assertion to add.</p>""",
"steps": [
 {"h": "Fetch the pull request object first, not the lists",
  "body": """<p>One request to <code>GET /repos/{owner}/{repo}/pulls/{n}</code> gives you <code>changed_files</code> and <code>commits</code>. This is the only place those numbers exist, and every later judgment is a comparison against them. A collector that skips this call has nothing to check itself against and will believe whatever the list endpoints hand it.</p>"""},
 {"h": "Ask each list endpoint how far it will go",
  "body": """<p>One page of <code>.../files</code> and one of <code>.../commits</code> at <code>per_page=100</code>, read for the <code>Link</code> header rather than for the items. A <code>rel="last"</code> gives the endpoint's own page count; the absence of both <code>next</code> and <code>last</code> means one page is all there is. Either way you now know the widest band of items the endpoint is prepared to serve.</p>"""},
 {"h": "Reconcile the counter against the band",
  "body": """<p><code>changed_files</code> should land inside the range the page count implies. Above 3,000 files or 250 commits it cannot, and no page size will change that. Below the cap but outside the band, something else truncated the list and the mismatch is the finding either way.</p>"""},
 {"h": "Set per_page to 100 and assert on the collected count",
  "body": """<p>The default of 30 is where most of this is lost, long before either ceiling. Collect to the end of the <code>Link</code> header at 100, then compare what you collected against <code>changed_files</code> and <code>commits</code>, and raise rather than log when they differ. An assertion that fires on the one pull request in a thousand is what turns this from a silent wrong answer into a ticket.</p>"""},
 {"h": "Take the big ones through the diff instead",
  "body": """<p>Above 3,000 files, request the pull request with the <code>application/vnd.github.diff</code> media type and parse the diff; above 250 commits, walk <code>GET /repos/{owner}/{repo}/commits</code> with a <code>sha</code> and a date range. Both are more work than the JSON list and both are the only ways to see the whole thing. The audit itself costs three requests per pull request against the hourly <code>core</code> quota.</p>"""},
],
"verify": """<p>Once the collector paginates at 100 and asserts against the counters, the audit turns into a description of the pull request rather than a warning about it.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_pr_truncation.py --repo acme/monorepo --pr 4821
# read cost: 3 request(s) against the core hourly quota
# pull 4821 declares 4200 changed file(s) and 61 commit(s)
# files: beyond-cap - 4200 file(s) are declared and the endpoint stops at 3000,
# so 1200 of them cannot be read through it at any page size
# repair: request the pull request with the application/vnd.github.diff media
# type and parse the diff; the JSON list will not return file 3001
# commits: multi-page - 61 commit(s) across 1 page(s) at per_page=100. A client
# reading one page at the default 30 sees 30 of them and misses 31

# a normal pull request, after the collector was fixed
GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_pr_truncation.py --repo acme/monorepo --pr 4830
# files: single-page - 7 file(s) fit in one page at any page size
# commits: single-page - 2 commit(s) fit in one page at any page size</code></pre>""",
"code_intro": "Three GETs per pull request: the pull request object for its counters, then one page each of files and commits at the maximum page size, read for their Link headers rather than for their contents. Everything after that is arithmetic over two numbers that came from two different responses, which is the whole point of the note, so all of it is pure and all of it is tested offline. The cost is computed and printed before the first request, because a section full of quota notes should not ship a diagnostic that surprises you.",
"py_file": "github_pr_truncation.py",
"py": '''"""Compare a pull request's own counters against what its lists can return.

Read only. Three GETs per pull request. Nothing is written and the repair is
printed rather than performed.

A pull request object carries changed_files and commits. The two list endpoints
hanging off it do not: .../files stops at 3,000 files and .../commits at 250,
and both answer 200 with a shorter array rather than saying they stopped. The
counters are therefore the only ground truth a client has, and they live at a
different URL from the lists they describe.

What this can and cannot see: the API has no idea how many pages your collector
read. It can state what the pull request declares, how far each list endpoint is
prepared to go, and where those two things cannot be reconciled.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import json
import logging
import math
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_pr_truncation")

API = "https://api.github.com"
UA = "github-pr-truncation/1.0"

MAX_PER_PAGE = 100
# What you get when nobody sets per_page, which is where most of the loss
# happens: long before either ceiling, on any pull request over thirty files.
DEFAULT_PER_PAGE = 30

# The documented ceilings on the two lists hanging off a pull request. Named
# together because the note is about the pair of them and their repairs differ.
CAPS = {"files": 3000, "commits": 250}

# Anchored on the angle brackets rather than split on commas: a pagination URL
# can carry a comma of its own and splitting on it breaks the link in half.
LINK = re.compile(r'<([^>]+)>\\s*;\\s*rel="([^"]+)"')
PAGE = re.compile(r'[?&]page=(\\d+)')


def parse_link(header):
    """Parse a Link header into {rel: url}. Pure."""
    if not header:
        return {}
    return {rel: url for url, rel in LINK.findall(header)}


def page_of(url):
    """The page number inside a pagination URL, or None. Pure."""
    if not url:
        return None
    m = PAGE.search(str(url))
    return int(m.group(1)) if m else None


def cap_for(kind):
    """The documented ceiling on this list, or None if there isn't one. Pure."""
    return CAPS.get(kind)


def pages_needed(total, per_page):
    """Pages required to hold this many items. Pure. None for nonsense input."""
    try:
        n, size = int(total), int(per_page)
    except (TypeError, ValueError):
        return None
    if n < 0 or size < 1:
        return None
    return int(math.ceil(n / float(size)))


def reachable(kind, declared):
    """How many of the declared items the list endpoint can actually hand over."""
    cap = cap_for(kind)
    try:
        n = int(declared)
    except (TypeError, ValueError):
        return None
    if cap is None:
        return n
    return min(n, cap)


def beyond_cap(kind, declared):
    """How many items are unreachable through this endpoint. Pure. 0 when fine."""
    cap = cap_for(kind)
    try:
        n = int(declared)
    except (TypeError, ValueError):
        return 0
    if cap is None:
        return 0
    return max(0, n - cap)


def bounds_from_last(last_page, per_page):
    """The item count a rel=last page number implies, as (low, high). Pure.

    A last page of 3 at per_page=100 means somewhere between 201 and 300 items:
    the final page holds at least one and at most a full page. That band is the
    widest honest statement the header supports, so the counter is only called a
    disagreement when it falls outside it.
    """
    try:
        last, size = int(last_page), int(per_page)
    except (TypeError, ValueError):
        return None
    if last < 1 or size < 1:
        return None
    return ((last - 1) * size + 1, last * size)


def counter_outside_bounds(declared, bounds):
    """Whether the pull request's own count contradicts the page count. Pure."""
    if not bounds:
        return False
    try:
        n = int(declared)
    except (TypeError, ValueError):
        return False
    return n < bounds[0] or n > bounds[1]


def one_page_shortfall(declared, per_page=DEFAULT_PER_PAGE):
    """Items a client reading a single page never sees. Pure."""
    try:
        n, size = int(declared), int(per_page)
    except (TypeError, ValueError):
        return 0
    return max(0, n - max(0, size))


def verdict(kind, declared, last_page=None, per_page=MAX_PER_PAGE):
    """Classify one list against the counter that describes it. Pure.

    Returns (state, detail). The states keep three unreconcilable things apart:
    a count above the endpoint's ceiling, a count the endpoint's own page count
    cannot contain, and a count that is fine but needs more than one page.
    """
    cap = cap_for(kind)
    if cap is None:
        return ("unknown", "%r is not a list this check knows a ceiling for." % kind)
    try:
        n = int(declared)
    except (TypeError, ValueError):
        return ("unknown",
                "the pull request did not report a count for %s, so there is "
                "nothing to reconcile the list against." % kind)
    if n < 0:
        return ("unknown", "a negative count for %s is not a number this check "
                           "can use." % kind)

    over = beyond_cap(kind, n)
    if over:
        return ("beyond-cap",
                "%d %s are declared and the endpoint stops at %d, so %d of them "
                "cannot be read through it at any page size."
                % (n, kind, cap, over))

    bounds = bounds_from_last(last_page, per_page)
    if counter_outside_bounds(n, bounds):
        return ("counter-disagrees",
                "the pull request declares %d %s and the Link header stops at "
                "page %s, which can hold between %d and %d, so the list is "
                "shorter than the counter and something truncated it."
                % (n, kind, last_page, bounds[0], bounds[1]))

    if n > DEFAULT_PER_PAGE:
        return ("multi-page",
                "%d %s across %d page(s) at per_page=%d. A client reading one "
                "page at the default %d sees %d of them and misses %d."
                % (n, kind, pages_needed(n, per_page) or 1, int(per_page),
                   DEFAULT_PER_PAGE, min(n, DEFAULT_PER_PAGE),
                   one_page_shortfall(n)))

    return ("single-page",
            "%d %s fit in one page at any page size, so nothing here is being "
            "truncated today." % (n, kind))


def repair(state, kind):
    """The sentence a reader has to act on. Pure."""
    if state == "beyond-cap" and kind == "files":
        return ("request the pull request with the application/vnd.github.diff "
                "media type and parse the diff. The JSON list will not return "
                "file 3001 however you paginate it.")
    if state == "beyond-cap" and kind == "commits":
        return ("read the branch through GET /repos/{owner}/{repo}/commits with "
                "a sha and a date range, which paginates conventionally and has "
                "no ceiling of its own.")
    if state == "counter-disagrees":
        return ("collect the whole list at per_page=100 and compare the count "
                "you collected against changed_files and commits on the pull "
                "request object, raising rather than logging on a mismatch.")
    if state == "multi-page":
        return ("set per_page=100, follow rel=next to the end, and assert the "
                "collected count against the counter on the pull request "
                "object. The default page size of 30 is where this is lost.")
    if state == "single-page":
        return ("nothing on this pull request. Run the same check against your "
                "largest ones, which are the ones a review bot is trusted on.")
    return "point the check at a pull request this token can read."


def read_cost(prs):
    """Requests this run will spend against the core quota. Pure.

    Three per pull request: the object for its counters, and one page each of
    files and commits for their Link headers.
    """
    return 3 * len(prs or [])


def get(session, path, params=None):
    """One GET. Returns (status, parsed-body-or-None, links)."""
    r = session.get(API + path, params=params or {}, timeout=30)
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
        return r.status_code, r.json(), links
    except ValueError:
        return r.status_code, None, links


def last_page_from(links):
    """The endpoint's own page count, or 1 when it says there is only one. Pure.

    None where there is a next page but no last, because then the page count is
    genuinely unknown and guessing it is how the other notes in this section
    start.
    """
    last = page_of(links.get("last"))
    if last:
        return last
    if "next" in links:
        return None
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--pr", action="append", type=int, required=True,
                    help="pull request number. Repeatable.")
    ap.add_argument("--per-page", type=int, default=MAX_PER_PAGE,
                    help="page size used to probe the lists. 100 is the maximum "
                         "and there is no reason to probe with less.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(args.pr))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for number in args.pr:
        base = "/repos/%s/pulls/%d" % (args.repo, number)
        _status, pr, _links = get(session, base)
        if not isinstance(pr, dict):
            continue
        log.info("pull %d declares %s changed file(s) and %s commit(s)",
                 number, pr.get("changed_files"), pr.get("commits"))

        for kind, declared in (("files", pr.get("changed_files")),
                               ("commits", pr.get("commits"))):
            _s, _body, links = get(session, base + "/" + kind,
                                   {"per_page": args.per_page})
            last = last_page_from(links)
            state, detail = verdict(kind, declared, last, args.per_page)
            log.info("%s: %s - %s", kind, state, detail)
            log.info("repair: %s", repair(state, kind))
            findings.append({
                "pull_request": number,
                "list": kind,
                "declared": declared,
                "cap": cap_for(kind),
                "reachable": reachable(kind, declared),
                "unreachable": beyond_cap(kind, declared),
                "endpoint_last_page": last,
                "implied_bounds": bounds_from_last(last, args.per_page),
                "missed_by_one_default_page": one_page_shortfall(declared),
                "state": state,
                "detail": detail,
                "repair": repair(state, kind),
            })

    print(json.dumps({"requests_spent": read_cost(args.pr),
                      "findings": findings}, indent=2, default=str))
    bad = {"beyond-cap", "counter-disagrees", "multi-page"}
    return 1 if any(f["state"] in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-pr-truncation.mjs",
"js": '''/**
 * Compare a pull request's own counters against what its lists can return.
 *
 * Read only. Three GETs per pull request. Nothing is written and the repair is
 * printed rather than performed.
 *
 * Environment:
 *   GITHUB_TOKEN     a token with read access to the repository
 *   GITHUB_REPO      owner/name
 *   GITHUB_PRS       comma-separated pull request numbers
 *   GITHUB_PER_PAGE  page size used to probe the lists, default 100
 */
const API = 'https://api.github.com';
const UA = 'github-pr-truncation/1.0';

export const MAX_PER_PAGE = 100;
/** What you get when nobody sets per_page, and where most of the loss happens. */
export const DEFAULT_PER_PAGE = 30;

/** The documented ceilings on the two lists hanging off a pull request. */
export const CAPS = { files: 3000, commits: 250 };

// Anchored on the angle brackets rather than split on commas: a pagination URL
// can carry a comma of its own and splitting on it breaks the link in half.
const LINK = /<([^>]+)>\\s*;\\s*rel="([^"]+)"/g;
const PAGE = /[?&]page=(\\d+)/;

/**
 * A finite number, or null. Pure.
 *
 * Written out because Number(null) is 0 in JavaScript and Number('') is 0 too,
 * which is exactly how a missing counter turns into a confident zero and a
 * diagnostic starts reporting a truncation nobody has.
 */
function toNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Parse a Link header into {rel: url}. Pure. */
export function parseLink(header) {
  const out = {};
  if (!header) return out;
  for (const m of String(header).matchAll(LINK)) out[m[2]] = m[1];
  return out;
}

/** The page number inside a pagination URL, or null. Pure. */
export function pageOf(url) {
  if (!url) return null;
  const m = PAGE.exec(String(url));
  return m ? Number(m[1]) : null;
}

/** The documented ceiling on this list, or null. Pure. */
export function capFor(kind) {
  return Object.prototype.hasOwnProperty.call(CAPS, kind) ? CAPS[kind] : null;
}

/** Pages required to hold this many items. Pure. null for nonsense input. */
export function pagesNeeded(total, perPage) {
  const n = toNumber(total);
  const size = toNumber(perPage);
  if (n === null || size === null || n < 0 || size < 1) return null;
  return Math.ceil(n / size);
}

/** How many of the declared items the endpoint can actually hand over. Pure. */
export function reachable(kind, declared) {
  const cap = capFor(kind);
  const n = toNumber(declared);
  if (n === null) return null;
  return cap === null ? n : Math.min(n, cap);
}

/** How many items are unreachable through this endpoint. Pure. */
export function beyondCap(kind, declared) {
  const cap = capFor(kind);
  const n = toNumber(declared);
  if (n === null || cap === null) return 0;
  return Math.max(0, n - cap);
}

/**
 * The item count a rel=last page number implies, as [low, high]. Pure.
 *
 * A last page of 3 at per_page=100 means between 201 and 300 items. That band
 * is the widest honest statement the header supports.
 */
export function boundsFromLast(lastPage, perPage) {
  const last = toNumber(lastPage);
  const size = toNumber(perPage);
  if (last === null || size === null || last < 1 || size < 1) return null;
  return [(last - 1) * size + 1, last * size];
}

/** Whether the pull request's own count contradicts the page count. Pure. */
export function counterOutsideBounds(declared, bounds) {
  if (!bounds) return false;
  const n = toNumber(declared);
  if (n === null) return false;
  return n < bounds[0] || n > bounds[1];
}

/** Items a client reading a single page never sees. Pure. */
export function onePageShortfall(declared, perPage = DEFAULT_PER_PAGE) {
  const n = toNumber(declared);
  const size = toNumber(perPage);
  if (n === null || size === null) return 0;
  return Math.max(0, n - Math.max(0, size));
}

/** Classify one list against the counter that describes it. Pure. */
export function verdict(kind, declared, lastPage = null, perPage = MAX_PER_PAGE) {
  const cap = capFor(kind);
  if (cap === null) {
    return ['unknown', `${kind} is not a list this check knows a ceiling for.`];
  }
  const n = toNumber(declared);
  if (n === null) {
    return ['unknown',
      `the pull request did not report a count for ${kind}, so there is nothing `
      + 'to reconcile the list against.'];
  }
  if (n < 0) {
    return ['unknown', `a negative count for ${kind} is not a number this check can use.`];
  }

  const over = beyondCap(kind, n);
  if (over) {
    return ['beyond-cap',
      `${n} ${kind} are declared and the endpoint stops at ${cap}, so ${over} of `
      + 'them cannot be read through it at any page size.'];
  }

  const bounds = boundsFromLast(lastPage, perPage);
  if (counterOutsideBounds(n, bounds)) {
    return ['counter-disagrees',
      `the pull request declares ${n} ${kind} and the Link header stops at page `
      + `${lastPage}, which can hold between ${bounds[0]} and ${bounds[1]}, so `
      + 'the list is shorter than the counter and something truncated it.'];
  }

  if (n > DEFAULT_PER_PAGE) {
    return ['multi-page',
      `${n} ${kind} across ${pagesNeeded(n, perPage) || 1} page(s) at `
      + `per_page=${Number(perPage)}. A client reading one page at the default `
      + `${DEFAULT_PER_PAGE} sees ${Math.min(n, DEFAULT_PER_PAGE)} of them and `
      + `misses ${onePageShortfall(n)}.`];
  }

  return ['single-page',
    `${n} ${kind} fit in one page at any page size, so nothing here is being `
    + 'truncated today.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, kind) {
  if (state === 'beyond-cap' && kind === 'files') {
    return 'request the pull request with the application/vnd.github.diff media '
      + 'type and parse the diff. The JSON list will not return file 3001 '
      + 'however you paginate it.';
  }
  if (state === 'beyond-cap' && kind === 'commits') {
    return 'read the branch through GET /repos/{owner}/{repo}/commits with a sha '
      + 'and a date range, which paginates conventionally and has no ceiling of '
      + 'its own.';
  }
  if (state === 'counter-disagrees') {
    return 'collect the whole list at per_page=100 and compare the count you '
      + 'collected against changed_files and commits on the pull request object, '
      + 'raising rather than logging on a mismatch.';
  }
  if (state === 'multi-page') {
    return 'set per_page=100, follow rel=next to the end, and assert the '
      + 'collected count against the counter on the pull request object. The '
      + 'default page size of 30 is where this is lost.';
  }
  if (state === 'single-page') {
    return 'nothing on this pull request. Run the same check against your '
      + 'largest ones, which are the ones a review bot is trusted on.';
  }
  return 'point the check at a pull request this token can read.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(prs) {
  return 3 * (Array.isArray(prs) ? prs.length : 0);
}

/** The endpoint's own page count, or null when it cannot be known. Pure. */
export function lastPageFrom(links) {
  const last = pageOf((links || {}).last);
  if (last) return last;
  if (links && Object.prototype.hasOwnProperty.call(links, 'next')) return null;
  return 1;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const res = await fetch(url, { headers: headers(token) });
  const links = parseLink(res.headers.get('link'));
  if (!res.ok) return { status: res.status, body: null, links };
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body, links };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  const prs = (process.env.GITHUB_PRS || '').split(',').map((s) => s.trim()).filter(Boolean);
  if (!token || !repo || prs.length === 0) {
    console.error('set GITHUB_TOKEN (read-only is enough), GITHUB_REPO=owner/name '
      + 'and GITHUB_PRS=4821,4830');
    process.exitCode = 2;
    return;
  }
  const perPage = Number(process.env.GITHUB_PER_PAGE || MAX_PER_PAGE);
  console.log(`read cost: ${readCost(prs)} request(s) against the core hourly quota`);

  const findings = [];
  for (const number of prs) {
    const base = `/repos/${repo}/pulls/${number}`;
    const { body: pr } = await get(token, base);
    if (!pr || typeof pr !== 'object') continue;
    console.log(`pull ${number} declares ${pr.changed_files} changed file(s) and `
      + `${pr.commits} commit(s)`);

    for (const [kind, declared] of [['files', pr.changed_files], ['commits', pr.commits]]) {
      const { links } = await get(token, `${base}/${kind}`, { per_page: perPage });
      const last = lastPageFrom(links);
      const [state, detail] = verdict(kind, declared, last, perPage);
      console.log(`${kind}: ${state} - ${detail}`);
      console.log(`repair: ${repair(state, kind)}`);
      findings.push({
        pull_request: number,
        list: kind,
        declared,
        cap: capFor(kind),
        reachable: reachable(kind, declared),
        unreachable: beyondCap(kind, declared),
        endpoint_last_page: last,
        implied_bounds: boundsFromLast(last, perPage),
        missed_by_one_default_page: onePageShortfall(declared),
        state,
        detail,
        repair: repair(state, kind),
      });
    }
  }

  console.log(JSON.stringify({ requests_spent: readCost(prs), findings }, null, 2));
  const bad = ['beyond-cap', 'counter-disagrees', 'multi-page'];
  process.exitCode = findings.some((f) => bad.includes(f.state)) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The arithmetic gets the attention, because the arithmetic is the finding: a count above the ceiling, a count the endpoint's own page count cannot contain, and a count that merely needs more than one page are three different states with three different repairs, and the tests pin all three at their boundaries. After that, the band a rel=last implies, the shortfall a single default page leaves behind, the two repairs that must not be swapped between files and commits, and the read cost, which is asserted so a diagnostic in a section about quota cannot quietly start spending more of it.",
"test_py_file": "test_github_pr_truncation.py",
"test_py": '''from github_pr_truncation import (
    CAPS, DEFAULT_PER_PAGE, MAX_PER_PAGE, beyond_cap, bounds_from_last, cap_for,
    counter_outside_bounds, last_page_from, one_page_shortfall, page_of,
    pages_needed, parse_link, read_cost, reachable, repair, verdict,
)


def test_the_two_ceilings_are_different_numbers():
    assert cap_for("files") == 3000
    assert cap_for("commits") == 250
    assert cap_for("comments") is None
    assert CAPS["files"] > CAPS["commits"]


def test_pages_needed_rounds_up_and_refuses_nonsense():
    assert pages_needed(3000, 100) == 30
    assert pages_needed(901, 100) == 10
    assert pages_needed(1, 100) == 1
    assert pages_needed(0, 100) == 0
    assert pages_needed(250, 30) == 9
    assert pages_needed(10, 0) is None
    assert pages_needed(None, 100) is None


def test_what_is_reachable_stops_at_the_ceiling():
    assert reachable("files", 4200) == 3000
    assert reachable("files", 12) == 12
    assert reachable("commits", 812) == 250
    assert reachable("files", None) is None


def test_what_is_beyond_the_ceiling_is_counted_exactly():
    assert beyond_cap("files", 4200) == 1200
    assert beyond_cap("files", 3000) == 0
    assert beyond_cap("commits", 251) == 1
    assert beyond_cap("commits", None) == 0


def test_a_last_page_implies_a_band_rather_than_a_number():
    assert bounds_from_last(3, 100) == (201, 300)
    assert bounds_from_last(1, 100) == (1, 100)
    assert bounds_from_last(0, 100) is None
    assert bounds_from_last(None, 100) is None
    assert bounds_from_last(3, 0) is None


def test_the_counter_is_only_wrong_when_it_leaves_the_band():
    assert counter_outside_bounds(150, (1, 100))
    assert counter_outside_bounds(0, (1, 100))
    assert not counter_outside_bounds(100, (1, 100))
    assert not counter_outside_bounds(250, (201, 300))
    assert not counter_outside_bounds(150, None)


def test_one_default_page_is_where_most_of_it_is_lost():
    assert one_page_shortfall(900) == 900 - DEFAULT_PER_PAGE
    assert one_page_shortfall(31) == 1
    assert one_page_shortfall(30) == 0
    assert one_page_shortfall(7) == 0
    assert one_page_shortfall(900, 100) == 800


def test_a_count_above_the_ceiling_is_unreachable_at_any_page_size():
    state, detail = verdict("files", 4200, 30, MAX_PER_PAGE)
    assert state == "beyond-cap"
    assert "1200" in detail
    assert "any page size" in detail
    assert verdict("commits", 812, 3, MAX_PER_PAGE)[0] == "beyond-cap"


def test_a_page_count_that_cannot_hold_the_counter_is_its_own_finding():
    state, detail = verdict("files", 150, 1, MAX_PER_PAGE)
    assert state == "counter-disagrees"
    assert "between 1 and 100" in detail


def test_a_reconcilable_multi_page_list_names_what_one_page_misses():
    state, detail = verdict("files", 900, 9, MAX_PER_PAGE)
    assert state == "multi-page"
    assert "misses 870" in detail


def test_a_small_pull_request_is_not_a_finding():
    assert verdict("files", 7, 1, MAX_PER_PAGE)[0] == "single-page"
    assert verdict("commits", 30, 1, MAX_PER_PAGE)[0] == "single-page"


def test_a_missing_counter_is_reported_rather_than_assumed():
    assert verdict("files", None, 1, MAX_PER_PAGE)[0] == "unknown"
    assert verdict("files", "several", 1, MAX_PER_PAGE)[0] == "unknown"
    assert verdict("comments", 12, 1, MAX_PER_PAGE)[0] == "unknown"


def test_an_unknown_page_count_does_not_manufacture_a_disagreement():
    # rel=next with no rel=last: the page count is genuinely unknown, so the
    # only honest verdict is the one the counter alone supports.
    assert verdict("files", 900, None, MAX_PER_PAGE)[0] == "multi-page"


def test_the_two_repairs_are_not_interchangeable():
    assert "vnd.github.diff" in repair("beyond-cap", "files")
    assert "vnd.github.diff" not in repair("beyond-cap", "commits")
    assert "/commits" in repair("beyond-cap", "commits")
    assert "per_page=100" in repair("multi-page", "files")
    assert "changed_files" in repair("counter-disagrees", "files")
    assert repair("single-page", "files").startswith("nothing on this")


def test_the_page_count_is_read_from_the_header_not_guessed():
    header = ('<https://api.github.com/repos/o/n/pulls/1/files?page=2>; rel="next", '
              '<https://api.github.com/repos/o/n/pulls/1/files?page=9>; rel="last"')
    links = parse_link(header)
    assert page_of(links["last"]) == 9
    assert last_page_from(links) == 9
    assert last_page_from({"next": "https://api.github.com/x?page=2"}) is None
    assert last_page_from({}) == 1
    assert page_of(None) is None


def test_the_run_says_what_it_will_spend():
    assert read_cost([1, 2]) == 6
    assert read_cost([4821]) == 3
    assert read_cost([]) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-pr-truncation.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  CAPS, DEFAULT_PER_PAGE, MAX_PER_PAGE, beyondCap, boundsFromLast, capFor,
  counterOutsideBounds, lastPageFrom, onePageShortfall, pageOf, pagesNeeded,
  parseLink, readCost, reachable, repair, verdict,
} from './github-pr-truncation.mjs';

test('the two ceilings are different numbers', () => {
  assert.equal(capFor('files'), 3000);
  assert.equal(capFor('commits'), 250);
  assert.equal(capFor('comments'), null);
  assert.ok(CAPS.files > CAPS.commits);
});

test('pagesNeeded rounds up and refuses nonsense', () => {
  assert.equal(pagesNeeded(3000, 100), 30);
  assert.equal(pagesNeeded(901, 100), 10);
  assert.equal(pagesNeeded(1, 100), 1);
  assert.equal(pagesNeeded(0, 100), 0);
  assert.equal(pagesNeeded(250, 30), 9);
  assert.equal(pagesNeeded(10, 0), null);
  assert.equal(pagesNeeded(null, 100), null);
});

test('what is reachable stops at the ceiling', () => {
  assert.equal(reachable('files', 4200), 3000);
  assert.equal(reachable('files', 12), 12);
  assert.equal(reachable('commits', 812), 250);
  assert.equal(reachable('files', null), null);
});

test('what is beyond the ceiling is counted exactly', () => {
  assert.equal(beyondCap('files', 4200), 1200);
  assert.equal(beyondCap('files', 3000), 0);
  assert.equal(beyondCap('commits', 251), 1);
  assert.equal(beyondCap('commits', null), 0);
});

test('a last page implies a band rather than a number', () => {
  assert.deepEqual(boundsFromLast(3, 100), [201, 300]);
  assert.deepEqual(boundsFromLast(1, 100), [1, 100]);
  assert.equal(boundsFromLast(0, 100), null);
  assert.equal(boundsFromLast(null, 100), null);
  assert.equal(boundsFromLast(3, 0), null);
});

test('the counter is only wrong when it leaves the band', () => {
  assert.ok(counterOutsideBounds(150, [1, 100]));
  assert.ok(counterOutsideBounds(0, [1, 100]));
  assert.ok(!counterOutsideBounds(100, [1, 100]));
  assert.ok(!counterOutsideBounds(250, [201, 300]));
  assert.ok(!counterOutsideBounds(150, null));
});

test('one default page is where most of it is lost', () => {
  assert.equal(onePageShortfall(900), 900 - DEFAULT_PER_PAGE);
  assert.equal(onePageShortfall(31), 1);
  assert.equal(onePageShortfall(30), 0);
  assert.equal(onePageShortfall(7), 0);
  assert.equal(onePageShortfall(900, 100), 800);
});

test('a count above the ceiling is unreachable at any page size', () => {
  const [state, detail] = verdict('files', 4200, 30, MAX_PER_PAGE);
  assert.equal(state, 'beyond-cap');
  assert.match(detail, /1200/);
  assert.match(detail, /any page size/);
  assert.equal(verdict('commits', 812, 3, MAX_PER_PAGE)[0], 'beyond-cap');
});

test('a page count that cannot hold the counter is its own finding', () => {
  const [state, detail] = verdict('files', 150, 1, MAX_PER_PAGE);
  assert.equal(state, 'counter-disagrees');
  assert.match(detail, /between 1 and 100/);
});

test('a reconcilable multi-page list names what one page misses', () => {
  const [state, detail] = verdict('files', 900, 9, MAX_PER_PAGE);
  assert.equal(state, 'multi-page');
  assert.match(detail, /misses 870/);
});

test('a small pull request is not a finding', () => {
  assert.equal(verdict('files', 7, 1, MAX_PER_PAGE)[0], 'single-page');
  assert.equal(verdict('commits', 30, 1, MAX_PER_PAGE)[0], 'single-page');
});

test('a missing counter is reported rather than assumed', () => {
  assert.equal(verdict('files', null, 1, MAX_PER_PAGE)[0], 'unknown');
  assert.equal(verdict('files', 'several', 1, MAX_PER_PAGE)[0], 'unknown');
  assert.equal(verdict('comments', 12, 1, MAX_PER_PAGE)[0], 'unknown');
});

test('an unknown page count does not manufacture a disagreement', () => {
  assert.equal(verdict('files', 900, null, MAX_PER_PAGE)[0], 'multi-page');
});

test('the two repairs are not interchangeable', () => {
  assert.match(repair('beyond-cap', 'files'), /vnd\\.github\\.diff/);
  assert.ok(!repair('beyond-cap', 'commits').includes('vnd.github.diff'));
  assert.match(repair('beyond-cap', 'commits'), /\\/commits/);
  assert.match(repair('multi-page', 'files'), /per_page=100/);
  assert.match(repair('counter-disagrees', 'files'), /changed_files/);
  assert.ok(repair('single-page', 'files').startsWith('nothing on this'));
});

test('the page count is read from the header, not guessed', () => {
  const header = '<https://api.github.com/repos/o/n/pulls/1/files?page=2>; rel="next", '
    + '<https://api.github.com/repos/o/n/pulls/1/files?page=9>; rel="last"';
  const links = parseLink(header);
  assert.equal(pageOf(links.last), 9);
  assert.equal(lastPageFrom(links), 9);
  assert.equal(lastPageFrom({ next: 'https://api.github.com/x?page=2' }), null);
  assert.equal(lastPageFrom({}), 1);
  assert.equal(pageOf(null), null);
});

test('the run says what it will spend', () => {
  assert.equal(readCost([1, 2]), 6);
  assert.equal(readCost([4821]), 3);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("Is this the same as the compare endpoint's 250-commit cap?",
  "No, though the number 250 appears in both. On /compare/{base}...{head} the true count arrives as total_commits in the same body as the truncated array, so a client can detect the truncation from one response with one subtraction. Here the counters live on the pull request object and the lists live on separate endpoints, so a client that only calls .../files has nothing in hand to compare against. Same shape of failure, different detection, and a collector can be correct about one and wrong about the other."),
 ("Does paginating properly fix it?",
  "It fixes the part that matters most and not the whole thing. Paginating at per_page=100 to the end of the Link header gets you every file up to 3,000 and every commit up to 250, which covers almost every pull request anybody opens. Past those numbers the endpoint stops handing pages over and there is no rel=next left to tell you so, which is why the check compares against changed_files rather than against the shape of the last page."),
 ("How do I read a pull request with more than 3,000 files?",
  "Ask for the diff rather than the list. Requesting the pull request with the application/vnd.github.diff media type returns the unified diff, which you parse yourself. It is more work and it is the only route that does not stop at the cap. For commits above 250, GET /repos/{owner}/{repo}/commits with a sha and a date range paginates conventionally, so a long-lived branch can be walked in full there."),
 ("Why does the check need three requests per pull request?",
  "Because the comparison has two sides and they live in different places. One request gets the pull request object and its counters; the other two ask each list endpoint how far it is prepared to go, at per_page=100, reading the Link header rather than the items. There is no single response that contains both a counter and the list it describes, which is the mechanism of the bug and therefore also the cost of the check. The script prints that cost before it spends any of it."),
 ("Can the script tell whether my bot is truncating?",
  "Only by proxy, and it says so. The API cannot see how many pages your collector read or whether it read any. What the script establishes is what the pull request declares, what the endpoint is willing to serve, and where those two cannot be reconciled. If they cannot, any client is truncated there. If they can, yours might still be, and the assertion the script prints against changed_files is the one line that would have caught it."),
],
"related": [
 ("/github/compare-250-commit-cap/", "The compare endpoint stops at 250 commits"),
 ("/github/per-page-over-100-clamped/", "per_page above 100 is clamped silently"),
 ("/github/request-timeout-502/", "Expensive requests are killed at ten seconds"),
],
"citations": [CITE_PULLS, CITE_PAGINATION, CITE_MEDIA_TYPES, CITE_COMMITS],
},


{
"slug": "request-timeout-502",
"title": "Expensive requests are killed at ten seconds with a 502",
"description": "A heavy diff or a list on an enormous repository returns 502 after ten seconds. It is not a rate limit, and retrying the same call buys the same failure.",
"h1": "expensive requests are killed at ten seconds with a 502",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 502 bad gateway rest",
             "github api request timeout 10 seconds",
             "github api 504 gateway timeout expensive query",
             "github rest api server error large repository",
             "github api x-github-request-id 502"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One call in the whole integration returns <code>502 Bad Gateway</code>. Everything else is fine, the token is fine, the status page is green, and the call works on every repository except the big one. So the retry wrapper does what retry wrappers do: it waits a second and issues the identical expensive request, which takes the identical ten seconds and fails in the identical way, three times, before the job gives up and pages somebody.",
"short_answer": """<p>GitHub gives up on a request it cannot serve in about ten seconds and answers with a gateway error rather than a 4xx. A <code>502</code> or <code>504</code> that arrives reliably, on one path, after roughly ten seconds, while cheap calls on the same token are instant, is not an outage and not a throttle. It is the API telling you the query is too expensive to answer.</p>
<p>The repair is to make the request smaller, not to send it again: lower <code>per_page</code>, add a date or path filter, split a comparison into ranges, or ask GraphQL for only the fields you need. Capture <code>x-github-request-id</code> from the failing response before you change anything, because it is the first thing support asks for and it does not survive the retry.</p>""",
"problem": """<p>Every retry library in existence treats 5xx as transient, and it is right almost all of the time. A gateway error normally means something behind the proxy fell over and will be back shortly, so the correct response is to wait and try again. That reasoning is what makes this failure so durable: the code is doing the textbook thing, and the textbook thing is precisely wrong here, because the request will cost exactly as much the second time.</p>
<p>It also fails to look like a bug. It is one endpoint out of forty, it works in staging where the repository has eleven branches, and it works against every repository except the monorepo that everyone actually cares about. So it gets logged as flakiness, filed as a network issue, and worked around with a longer backoff and more attempts, which is the one change guaranteed to make it slower without making it work.</p>
<p>The thing that finally gets it fixed is usually the clock. Somebody notices the failures all take about the same time, and that the time is suspiciously round. Until then the evidence is unhelpfully empty: the body is a short generic message, there is no rate-limit header to read, no error code to look up, and <code>x-github-request-id</code> is sitting in a response object that the retry wrapper threw away in order to try again.</p>""",
"why": """<p><strong>The cutoff is on the server and it applies per request.</strong> GitHub terminates a request it cannot complete in roughly ten seconds. Your own client timeout is a separate number, and if yours is shorter you never see the gateway error at all &mdash; you see a client-side timeout instead and blame the network. Raising your timeout above the server's cutoff is the first step, because you cannot diagnose a response you never waited for.</p>
<p><strong>A gateway error carries no instructions.</strong> This is what separates it from every throttling failure in this section. <a href="/github/retry-after-ignored/">A secondary rate limit</a> hands you <code>retry-after</code>, and an exhausted primary quota hands you <code>x-ratelimit-reset</code>; in both cases the response tells you exactly how long to wait, and waiting is the repair. A 502 hands you nothing, because there is no amount of waiting that makes the query cheaper. Distinguishing the two is the first branch the script takes, by name, so a throttle never gets misfiled as a timeout.</p>
<p><strong>Retrying is not neutral, it is the wrong direction.</strong> Each attempt spends ten seconds of wall clock, one request against your hourly quota, and real work on GitHub's side. Three attempts is thirty seconds to arrive at the same answer with less quota than you started with. The only retry worth making is a retry of a <em>different, smaller</em> request, which is why the script prints the narrowed version of your call rather than a backoff schedule.</p>
<p><strong>Speed is the tell.</strong> A gateway error that comes back in 300 milliseconds is not your query running out of time; that is an incident, a proxy in front of you, or a load balancer with nothing to talk to, and the repair is to check the status page and retry. A gateway error at ten seconds is yours. Same status code, opposite diagnosis, and elapsed time is the only thing in the response that tells them apart &mdash; so the check times every attempt and reports the number.</p>
<p><strong>The success right below the line is the interesting one.</strong> A call that returns 200 after nine seconds is not healthy. It is one busy afternoon, one more branch or one more merge away from crossing the cutoff, and it will cross it in production first. Treating a slow success as a finding is the only way this gets fixed before it becomes an incident, so the check reports it as its own state rather than as a pass.</p>
<p><strong>This is not a partial answer.</strong> A search that runs out of time comes back <code>200</code> with <a href="/github/search-incomplete-results/"><code>incomplete_results</code> set</a> and gives you what it found. That is the same underlying constraint expressed as a shortfall you can read in the body. Here the request produces nothing at all, which is at least honest: you cannot mistake a 502 for data, and no cache will quietly keep it.</p>""",
"steps": [
 {"h": "Raise your own timeout above the server's cutoff",
  "body": """<p>If your client gives up at five seconds you will never see the gateway error, only a client-side timeout, and you will spend the afternoon looking at the network. Set the client timeout to thirty seconds for the duration of the investigation. The script reports a client-side timeout as its own state so the two are never confused.</p>"""},
 {"h": "Time the failing call, twice",
  "body": """<p>Reproducibility is most of the diagnosis. Two attempts that both fail at about ten seconds is a cost problem. Two attempts where one fails in 300 milliseconds and the other succeeds is an incident, and no amount of rewriting your query will help. The script makes both attempts, prints each elapsed time, and classifies on the pair.</p>"""},
 {"h": "Take a free baseline against GET /rate_limit",
  "body": """<p><code>GET /rate_limit</code> is instant and does not consume quota, which makes it the ideal control. If the baseline is also slow, your problem is the network or the machine and nothing about the endpoint matters yet. If the baseline is 80 milliseconds and the call under test is ten seconds, the endpoint is the whole story.</p>"""},
 {"h": "Rule out the throttle before you blame the cost",
  "body": """<p>A 403 or 429 carrying <code>retry-after</code>, or a response with <code>x-ratelimit-remaining: 0</code>, is a rate limit and belongs to a different note with a different repair. The script checks for those headers first and refuses to call anything a timeout while they are present, because a misfiled throttle sends you off rewriting a query that was never the problem.</p>"""},
 {"h": "Keep the request id, then shrink the request",
  "body": """<p>Read <code>x-github-request-id</code> off the failing response and record it; it is what support will ask for and the retry destroys it. Then halve <code>per_page</code>, add a <code>since</code> or a path filter, split the comparison into date ranges, or move the call to GraphQL and ask for fewer fields. The script prints the narrowed parameters for you to try; it never issues them itself.</p>"""},
],
"verify": """<p>Once the call is narrowed, the same probe answers in well under the cutoff and the state changes from a finding to a description.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_timeout_502.py \\
  --path /repos/acme/monorepo/compare/v1.0.0...main --param per_page=100
# read cost: 2 request(s) against the core hourly quota (the baseline is free)
# baseline: GET /rate_limit answered in 0.09s and consumed no quota
# attempt 1: 502 after 10.3s (x-github-request-id C4E2:1F03:...)
# attempt 2: 502 after 10.1s
# timeout: 502 came back after 10.3s, at the cutoff GitHub applies to a single
# request. The query is too expensive to serve, not unlucky
# repair: make the request cheaper rather than sending it again
# try instead: per_page=50

# after the comparison was split into two ranges
GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_timeout_502.py \\
  --path /repos/acme/monorepo/compare/v1.0.0...v1.1.0 --param per_page=50
# attempt 1: 200 after 1.4s
# ok: the call answered in 1.4s, comfortably inside the cutoff</code></pre>""",
"code_intro": "Two timed GETs against the path under test, plus one free baseline against GET /rate_limit, which is the only endpoint that answers without consuming quota and therefore the only honest control. Everything else is a pure classifier over three inputs: a status code, an elapsed time and the response headers. That is deliberate, because the whole note lives in the difference between a 502 at ten seconds and a 502 at three hundred milliseconds, and a rule that important should be testable without a network.",
"py_file": "github_timeout_502.py",
"py": '''"""Tell an expensive request that GitHub gave up on from an incident.

Read only. Two timed GETs against the path under test, plus one free baseline
against GET /rate_limit. Nothing is written and the repair is printed rather
than performed.

GitHub terminates a request it cannot serve in about ten seconds and answers
with a gateway error rather than a 4xx. Retry logic reads 5xx as transient and
sends the identical expensive request again, which costs the same ten seconds
and fails the same way. The repair is to make the request smaller, so this
script prints a narrowed version of your parameters rather than a backoff.

What this can and cannot see: the API does not report a per-request time budget
anywhere, so the cutoff is inferred from elapsed time. A gateway error that
arrives quickly is an incident rather than a cost problem, and the script says
so rather than sending you to rewrite a query that was fine.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_timeout_502")

API = "https://api.github.com"
UA = "github-timeout-502/1.0"

# The server-side budget for a single request, in seconds. Approximate by
# nature: it is not published as a header and cannot be read from a response.
CUTOFF_SECONDS = 10.0
# How close to the cutoff still counts as "this ran out of time". A success at
# nine seconds is not healthy, it is next week's failure.
TOLERANCE = 2.0

# The statuses a killed request comes back as. 500 is deliberately not here: it
# is a different failure and calling it a timeout would be a guess.
GATEWAY = (502, 503, 504)

# The largest page size worth suggesting when nobody set one.
MAX_PER_PAGE = 100


def lower_headers(headers):
    """Headers keyed by lowercase name. Pure.

    HTTP header names are case-insensitive and every client returns them in a
    different case, so a check that reads Retry-After from a dict typed by hand
    finds nothing and reports a timeout that was really a throttle.
    """
    return {str(k).lower(): v for k, v in (headers or {}).items()}


def request_id(headers):
    """The value support will ask for, or None. Pure."""
    return lower_headers(headers).get("x-github-request-id")


def is_gateway(status):
    """Whether this status is the shape a killed request comes back as. Pure."""
    try:
        return int(status) in GATEWAY
    except (TypeError, ValueError):
        return False


def is_throttled(status, headers):
    """Whether the response is a rate limit rather than a timeout. Pure.

    Checked before anything else, because a throttle misfiled as a timeout
    sends you off rewriting a query that was never the problem. The two are
    separated by headers, not by status: a secondary limit answers 403 or 429
    with retry-after, and an exhausted primary quota answers with a remaining
    count of zero.
    """
    h = lower_headers(headers)
    try:
        code = int(status)
    except (TypeError, ValueError):
        return False
    if code not in (403, 429):
        return False
    return "retry-after" in h or str(h.get("x-ratelimit-remaining", "")).strip() == "0"


def near_cutoff(elapsed, cutoff=CUTOFF_SECONDS, tolerance=TOLERANCE):
    """Whether this call ran long enough to have been killed for it. Pure."""
    try:
        return float(elapsed) >= float(cutoff) - float(tolerance)
    except (TypeError, ValueError):
        return False


def classify(status, elapsed, headers=None):
    """Classify one timed attempt. Pure. Returns (state, detail)."""
    try:
        secs = float(elapsed)
    except (TypeError, ValueError):
        secs = None

    if status is None:
        if secs is not None and secs >= CUTOFF_SECONDS:
            return ("client-timeout",
                    "your own client gave up after %.1fs, which is at or past "
                    "the server's own budget, so there is no response to read."
                    % secs)
        return ("unknown", "the attempt produced neither a status nor a usable "
                           "elapsed time.")

    try:
        code = int(status)
    except (TypeError, ValueError):
        return ("unknown", "the attempt produced no readable status.")

    if is_throttled(code, headers):
        return ("throttled",
                "%d carries rate-limit headers, so this is a throttle and not a "
                "timeout. The response says how long to wait and waiting is the "
                "repair." % code)

    if is_gateway(code):
        if secs is not None and near_cutoff(secs):
            return ("timeout",
                    "%d came back after %.1fs, at the cutoff GitHub applies to "
                    "a single request. The query is too expensive to serve, not "
                    "unlucky." % (code, secs))
        return ("gateway-early",
                "%d came back after %.1fs, far short of the cutoff, so this is "
                "not your query running out of time. Check the status page "
                "before rewriting anything." % (code, secs if secs is not None else -1.0))

    if 500 <= code < 600:
        return ("server-other",
                "%d is a server error of a different shape. It is not the "
                "per-request cutoff and it is not a throttle." % code)

    if 400 <= code < 500:
        return ("client-error",
                "%d is a client error, so the request was understood and "
                "refused rather than abandoned partway through." % code)

    if secs is not None and near_cutoff(secs):
        return ("slow-success",
                "the call answered %d in %.1fs, inside the tolerance of the "
                "%.0fs cutoff. It works today and fails on the week the "
                "repository grows." % (code, secs, CUTOFF_SECONDS))

    return ("ok",
            "the call answered %d in %.1fs, comfortably inside the cutoff."
            % (code, secs if secs is not None else -1.0))


def retry_repeats_it(state):
    """Whether sending the identical request again reproduces this. Pure."""
    return state in ("timeout", "client-timeout")


def wasted_retries(state, retries):
    """Attempts a retry wrapper would spend to no purpose at all. Pure."""
    try:
        n = int(retries)
    except (TypeError, ValueError):
        return 0
    return max(0, n) if retry_repeats_it(state) else 0


def narrow(params):
    """A cheaper version of the same request. Pure.

    Halving the page size is the one narrowing that applies to every list
    endpoint without knowing anything about the query. Everything else worth
    trying is specific to the call and is printed as prose instead.
    """
    out = dict(params or {})
    try:
        size = int(out.get("per_page", MAX_PER_PAGE))
    except (TypeError, ValueError):
        size = MAX_PER_PAGE
    out["per_page"] = max(1, size // 2)
    return out


def narrowing_exhausted(params):
    """Whether the page size can no longer be halved. Pure."""
    try:
        return int((params or {}).get("per_page", MAX_PER_PAGE)) <= 1
    except (TypeError, ValueError):
        return False


def repair(state, params=None):
    """The sentence a reader has to act on. Pure."""
    if state == "timeout":
        base = ("make the request cheaper rather than sending it again: halve "
                "per_page, add a date or path filter, split a comparison into "
                "ranges, or ask GraphQL for only the fields you need. Record "
                "x-github-request-id from the failing response first, because "
                "the retry destroys it.")
        if narrowing_exhausted(params):
            return base + " The page size is already at 1, so the request has "\\
                          "to be split by range or path instead."
        return base
    if state == "client-timeout":
        return ("raise your own client timeout above the server's budget and "
                "run this again. Until you wait longer than GitHub does you are "
                "diagnosing your own deadline, not GitHub's.")
    if state == "gateway-early":
        return ("retry this one and check the status page. A gateway error that "
                "arrives in a fraction of a second is not your query running "
                "out of time.")
    if state == "throttled":
        return ("wait exactly as long as the response tells you to. This is the "
                "rate-limit path, it has its own repair, and rewriting the "
                "query will not change it.")
    if state == "slow-success":
        return ("narrow it now, while it still works. A call this close to the "
                "cutoff crosses it on the busiest day of the quarter.")
    if state == "server-other":
        return ("retry once, then take x-github-request-id to support. This is "
                "neither the per-request cutoff nor a throttle.")
    if state == "client-error":
        return "read the status: the request was refused, not abandoned."
    if state == "ok":
        return "nothing."
    return "give the probe a path it can reach and a timeout longer than 10s."


def read_cost(paths, attempts=2):
    """Requests this run will spend against the core quota. Pure.

    The baseline against GET /rate_limit is deliberately not counted: that
    endpoint answers without consuming any, which is what makes it usable as a
    control in a section full of notes about running out.
    """
    try:
        n, tries = len(paths or []), int(attempts)
    except (TypeError, ValueError):
        return 0
    return n * max(0, tries)


def timed_get(session, path, params, timeout):
    """One timed GET. Returns (status, elapsed, headers)."""
    started = time.monotonic()
    try:
        r = session.get(API + path, params=params, timeout=timeout)
    except requests.exceptions.RequestException:
        return None, time.monotonic() - started, {}
    return r.status_code, time.monotonic() - started, dict(r.headers)


def parse_params(pairs):
    """key=value strings into a dict. Pure."""
    out = {}
    for pair in pairs or []:
        if "=" in pair:
            key, value = pair.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", action="append", required=True,
                    help="the expensive API path, e.g. "
                         "/repos/o/n/compare/v1...main. Repeatable.")
    ap.add_argument("--param", action="append",
                    help="key=value query parameter. Repeatable.")
    ap.add_argument("--attempts", type=int, default=2,
                    help="timed attempts per path. Two is enough to tell a "
                         "repeatable cost problem from an incident.")
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="client timeout in seconds. Keep it above the "
                         "server's own budget or you will only ever measure "
                         "your own deadline.")
    ap.add_argument("--no-baseline", action="store_true",
                    help="skip the free GET /rate_limit control")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    params = parse_params(args.param)
    log.info("read cost: %d request(s) against the core hourly quota "
             "(the baseline is free)", read_cost(args.path, args.attempts))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    baseline = None
    if not args.no_baseline:
        _s, baseline, _h = timed_get(session, "/rate_limit", {}, args.timeout)
        log.info("baseline: GET /rate_limit answered in %.2fs and consumed no "
                 "quota", baseline)

    findings = []
    for path in args.path:
        attempts = []
        for i in range(max(1, args.attempts)):
            status, elapsed, headers = timed_get(session, path, params, args.timeout)
            state, detail = classify(status, elapsed, headers)
            rid = request_id(headers)
            log.info("attempt %d: %s after %.1fs%s", i + 1, status, elapsed,
                     " (x-github-request-id %s)" % rid if rid else "")
            attempts.append({"status": status, "elapsed": round(elapsed, 2),
                             "request_id": rid, "state": state, "detail": detail})

        worst = attempts[0]
        for a in attempts:
            if retry_repeats_it(a["state"]):
                worst = a
                break
        log.info("%s: %s", worst["state"], worst["detail"])
        log.info("repair: %s", repair(worst["state"], params))
        if worst["state"] in ("timeout", "slow-success"):
            log.info("try instead: %s",
                     ", ".join("%s=%s" % kv for kv in sorted(narrow(params).items())))

        findings.append({
            "path": path,
            "baseline_seconds": round(baseline, 3) if baseline is not None else None,
            "attempts": attempts,
            "state": worst["state"],
            "detail": worst["detail"],
            "retry_reproduces_it": retry_repeats_it(worst["state"]),
            "retries_wasted_on_three": wasted_retries(worst["state"], 3),
            "narrowed_params": narrow(params),
            "repair": repair(worst["state"], params),
        })

    print(json.dumps({"requests_spent": read_cost(args.path, args.attempts),
                      "findings": findings}, indent=2, default=str))
    bad = {"timeout", "client-timeout", "slow-success"}
    return 1 if any(f["state"] in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-timeout-502.mjs",
"js": '''/**
 * Tell an expensive request that GitHub gave up on from an incident.
 *
 * Read only. Two timed GETs against the path under test, plus one free
 * baseline against GET /rate_limit. Nothing is written and the repair is
 * printed rather than performed.
 *
 * Environment:
 *   GITHUB_TOKEN     a token with read access to the repository
 *   GITHUB_PATH      the expensive API path, e.g. /repos/o/n/compare/v1...main
 *   GITHUB_PARAMS    key=value pairs separated by commas, optional
 *   GITHUB_ATTEMPTS  timed attempts, default 2
 *   GITHUB_TIMEOUT   client timeout in seconds, default 30
 */
const API = 'https://api.github.com';
const UA = 'github-timeout-502/1.0';

/** The server-side budget for a single request, in seconds. */
export const CUTOFF_SECONDS = 10.0;
/** How close to the cutoff still counts as having run out of time. */
export const TOLERANCE = 2.0;
/** The statuses a killed request comes back as. 500 is deliberately not here. */
export const GATEWAY = [502, 503, 504];
export const MAX_PER_PAGE = 100;

/** A finite number, or null. Pure. Number(null) is 0, which would lie here. */
function toNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Headers keyed by lowercase name. Pure. */
export function lowerHeaders(headers) {
  const out = {};
  for (const [k, v] of Object.entries(headers || {})) out[String(k).toLowerCase()] = v;
  return out;
}

/** The value support will ask for, or null. Pure. */
export function requestId(headers) {
  const h = lowerHeaders(headers);
  return Object.prototype.hasOwnProperty.call(h, 'x-github-request-id')
    ? h['x-github-request-id'] : null;
}

/** Whether this status is the shape a killed request comes back as. Pure. */
export function isGateway(status) {
  const n = toNumber(status);
  return n !== null && GATEWAY.includes(n);
}

/** Whether the response is a rate limit rather than a timeout. Pure. */
export function isThrottled(status, headers) {
  const h = lowerHeaders(headers);
  const code = toNumber(status);
  if (code === null || ![403, 429].includes(code)) return false;
  if (Object.prototype.hasOwnProperty.call(h, 'retry-after')) return true;
  return String(h['x-ratelimit-remaining'] ?? '').trim() === '0';
}

/** Whether this call ran long enough to have been killed for it. Pure. */
export function nearCutoff(elapsed, cutoff = CUTOFF_SECONDS, tolerance = TOLERANCE) {
  const secs = toNumber(elapsed);
  return secs !== null && secs >= cutoff - tolerance;
}

/** Classify one timed attempt. Pure. Returns [state, detail]. */
export function classify(status, elapsed, headers = null) {
  const secs = toNumber(elapsed);

  if (status === null || status === undefined) {
    if (secs !== null && secs >= CUTOFF_SECONDS) {
      return ['client-timeout',
        `your own client gave up after ${secs.toFixed(1)}s, which is at or past `
        + "the server's own budget, so there is no response to read."];
    }
    return ['unknown', 'the attempt produced neither a status nor a usable elapsed time.'];
  }

  const code = toNumber(status);
  if (code === null) return ['unknown', 'the attempt produced no readable status.'];

  if (isThrottled(code, headers)) {
    return ['throttled',
      `${code} carries rate-limit headers, so this is a throttle and not a `
      + 'timeout. The response says how long to wait and waiting is the repair.'];
  }

  if (isGateway(code)) {
    if (secs !== null && nearCutoff(secs)) {
      return ['timeout',
        `${code} came back after ${secs.toFixed(1)}s, at the cutoff GitHub `
        + 'applies to a single request. The query is too expensive to serve, '
        + 'not unlucky.'];
    }
    return ['gateway-early',
      `${code} came back after ${(secs === null ? -1 : secs).toFixed(1)}s, far `
      + 'short of the cutoff, so this is not your query running out of time. '
      + 'Check the status page before rewriting anything.'];
  }

  if (code >= 500 && code < 600) {
    return ['server-other',
      `${code} is a server error of a different shape. It is not the `
      + 'per-request cutoff and it is not a throttle.'];
  }

  if (code >= 400 && code < 500) {
    return ['client-error',
      `${code} is a client error, so the request was understood and refused `
      + 'rather than abandoned partway through.'];
  }

  if (secs !== null && nearCutoff(secs)) {
    return ['slow-success',
      `the call answered ${code} in ${secs.toFixed(1)}s, inside the tolerance `
      + `of the ${CUTOFF_SECONDS.toFixed(0)}s cutoff. It works today and fails `
      + 'on the week the repository grows.'];
  }

  return ['ok',
    `the call answered ${code} in ${(secs === null ? -1 : secs).toFixed(1)}s, `
    + 'comfortably inside the cutoff.'];
}

/** Whether sending the identical request again reproduces this. Pure. */
export function retryRepeatsIt(state) {
  return state === 'timeout' || state === 'client-timeout';
}

/** Attempts a retry wrapper would spend to no purpose at all. Pure. */
export function wastedRetries(state, retries) {
  const n = toNumber(retries);
  if (n === null) return 0;
  return retryRepeatsIt(state) ? Math.max(0, Math.trunc(n)) : 0;
}

/** A cheaper version of the same request. Pure. */
export function narrow(params) {
  const out = { ...(params || {}) };
  const size = toNumber(out.per_page) ?? MAX_PER_PAGE;
  out.per_page = Math.max(1, Math.trunc(size / 2));
  return out;
}

/** Whether the page size can no longer be halved. Pure. */
export function narrowingExhausted(params) {
  const size = toNumber((params || {}).per_page);
  return size === null ? false : size <= 1;
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, params = null) {
  if (state === 'timeout') {
    const base = 'make the request cheaper rather than sending it again: halve '
      + 'per_page, add a date or path filter, split a comparison into ranges, or '
      + 'ask GraphQL for only the fields you need. Record x-github-request-id '
      + 'from the failing response first, because the retry destroys it.';
    if (narrowingExhausted(params)) {
      return `${base} The page size is already at 1, so the request has to be `
        + 'split by range or path instead.';
    }
    return base;
  }
  if (state === 'client-timeout') {
    return "raise your own client timeout above the server's budget and run this "
      + 'again. Until you wait longer than GitHub does you are diagnosing your '
      + "own deadline, not GitHub's.";
  }
  if (state === 'gateway-early') {
    return 'retry this one and check the status page. A gateway error that '
      + 'arrives in a fraction of a second is not your query running out of time.';
  }
  if (state === 'throttled') {
    return 'wait exactly as long as the response tells you to. This is the '
      + 'rate-limit path, it has its own repair, and rewriting the query will '
      + 'not change it.';
  }
  if (state === 'slow-success') {
    return 'narrow it now, while it still works. A call this close to the cutoff '
      + 'crosses it on the busiest day of the quarter.';
  }
  if (state === 'server-other') {
    return 'retry once, then take x-github-request-id to support. This is '
      + 'neither the per-request cutoff nor a throttle.';
  }
  if (state === 'client-error') {
    return 'read the status: the request was refused, not abandoned.';
  }
  if (state === 'ok') return 'nothing.';
  return 'give the probe a path it can reach and a timeout longer than 10s.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(paths, attempts = 2) {
  const n = Array.isArray(paths) ? paths.length : 0;
  const tries = toNumber(attempts);
  if (tries === null) return 0;
  return n * Math.max(0, Math.trunc(tries));
}

/** key=value strings into an object. Pure. */
export function parseParams(pairs) {
  const out = {};
  for (const pair of pairs || []) {
    const i = String(pair).indexOf('=');
    if (i > 0) out[String(pair).slice(0, i).trim()] = String(pair).slice(i + 1).trim();
  }
  return out;
}

function headersFor(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function timedGet(token, path, params, timeoutSeconds) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params || {})) url.searchParams.set(k, String(v));
  const started = process.hrtime.bigint();
  const elapsed = () => Number(process.hrtime.bigint() - started) / 1e9;
  try {
    const res = await fetch(url, {
      headers: headersFor(token),
      signal: AbortSignal.timeout(timeoutSeconds * 1000),
    });
    return { status: res.status, elapsed: elapsed(), headers: Object.fromEntries(res.headers) };
  } catch {
    return { status: null, elapsed: elapsed(), headers: {} };
  }
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const path = process.env.GITHUB_PATH;
  if (!token || !path) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_PATH');
    process.exitCode = 2;
    return;
  }
  const params = parseParams((process.env.GITHUB_PARAMS || '').split(',').filter(Boolean));
  const attempts = Number(process.env.GITHUB_ATTEMPTS || 2);
  const timeoutSeconds = Number(process.env.GITHUB_TIMEOUT || 30);
  console.log(`read cost: ${readCost([path], attempts)} request(s) against the core `
    + 'hourly quota (the baseline is free)');

  const base = await timedGet(token, '/rate_limit', {}, timeoutSeconds);
  console.log(`baseline: GET /rate_limit answered in ${base.elapsed.toFixed(2)}s `
    + 'and consumed no quota');

  const tried = [];
  for (let i = 0; i < Math.max(1, attempts); i += 1) {
    const { status, elapsed, headers } = await timedGet(token, path, params, timeoutSeconds);
    const [state, detail] = classify(status, elapsed, headers);
    const rid = requestId(headers);
    console.log(`attempt ${i + 1}: ${status} after ${elapsed.toFixed(1)}s`
      + (rid ? ` (x-github-request-id ${rid})` : ''));
    tried.push({ status, elapsed: Number(elapsed.toFixed(2)), request_id: rid, state, detail });
  }

  const worst = tried.find((a) => retryRepeatsIt(a.state)) || tried[0];
  console.log(`${worst.state}: ${worst.detail}`);
  console.log(`repair: ${repair(worst.state, params)}`);
  if (['timeout', 'slow-success'].includes(worst.state)) {
    console.log(`try instead: ${Object.entries(narrow(params)).sort()
      .map(([k, v]) => `${k}=${v}`).join(', ')}`);
  }

  console.log(JSON.stringify({
    requests_spent: readCost([path], attempts),
    findings: [{
      path,
      baseline_seconds: Number(base.elapsed.toFixed(3)),
      attempts: tried,
      state: worst.state,
      detail: worst.detail,
      retry_reproduces_it: retryRepeatsIt(worst.state),
      retries_wasted_on_three: wastedRetries(worst.state, 3),
      narrowed_params: narrow(params),
      repair: repair(worst.state, params),
    }],
  }, null, 2));
  process.exitCode = ['timeout', 'client-timeout', 'slow-success'].includes(worst.state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The classifier is the note, so the tests are mostly about the boundaries it draws: a gateway error at ten seconds and the same status at three hundred milliseconds have to come out as different states, a throttle has to be caught before either of them however its headers are capitalised, and a success just under the cutoff has to be a finding rather than a pass. The rest pins the arithmetic a reader will act on: what a retry actually costs when the retry cannot work, what the narrowed request looks like when the page size is already at its floor, and a read cost that never counts the free baseline as spending.",
"test_py_file": "test_github_timeout_502.py",
"test_py": '''from github_timeout_502 import (
    CUTOFF_SECONDS, GATEWAY, classify, is_gateway, is_throttled, lower_headers,
    narrow, narrowing_exhausted, near_cutoff, parse_params, read_cost, repair,
    request_id, retry_repeats_it, wasted_retries,
)

THROTTLE = {"Retry-After": "60"}
EXHAUSTED = {"X-RateLimit-Remaining": "0"}
RID = {"X-GitHub-Request-Id": "C4E2:1F03:9AB"}


def test_only_gateway_shaped_statuses_count():
    assert is_gateway(502)
    assert is_gateway(504)
    assert 500 not in GATEWAY
    assert not is_gateway(500)
    assert not is_gateway(200)
    assert not is_gateway(None)


def test_headers_are_read_case_insensitively():
    assert lower_headers(RID)["x-github-request-id"] == "C4E2:1F03:9AB"
    assert request_id(RID) == "C4E2:1F03:9AB"
    assert request_id({}) is None
    assert request_id(None) is None


def test_a_throttle_is_recognised_before_anything_else():
    assert is_throttled(403, THROTTLE)
    assert is_throttled(429, EXHAUSTED)
    assert not is_throttled(403, {})
    assert not is_throttled(502, THROTTLE)
    assert classify(403, 0.4, THROTTLE)[0] == "throttled"
    assert classify(429, 0.2, EXHAUSTED)[0] == "throttled"


def test_the_cutoff_has_a_tolerance_and_it_is_generous():
    assert near_cutoff(10.4)
    assert near_cutoff(8.0)
    assert not near_cutoff(7.9)
    assert not near_cutoff(0.3)
    assert not near_cutoff(None)


def test_a_gateway_error_at_the_cutoff_is_the_finding():
    state, detail = classify(502, 10.4, RID)
    assert state == "timeout"
    assert "10.4s" in detail
    assert "too expensive" in detail


def test_the_same_status_arriving_fast_is_a_different_diagnosis():
    state, detail = classify(502, 0.3, {})
    assert state == "gateway-early"
    assert "status page" in detail


def test_a_success_just_under_the_line_is_not_a_pass():
    state, detail = classify(200, 9.4, {})
    assert state == "slow-success"
    assert "fails on the week" in detail
    assert classify(200, 0.4, {})[0] == "ok"


def test_the_other_failures_are_named_rather_than_lumped_in():
    assert classify(500, 3.0, {})[0] == "server-other"
    assert classify(404, 0.2, {})[0] == "client-error"
    assert classify(None, 30.0, {})[0] == "client-timeout"
    assert classify(None, None, {})[0] == "unknown"
    assert classify("not a status", 1.0, {})[0] == "unknown"


def test_only_the_states_a_retry_cannot_fix_are_called_repeatable():
    assert retry_repeats_it("timeout")
    assert retry_repeats_it("client-timeout")
    assert not retry_repeats_it("gateway-early")
    assert not retry_repeats_it("throttled")
    assert wasted_retries("timeout", 3) == 3
    assert wasted_retries("gateway-early", 3) == 0
    assert wasted_retries("timeout", None) == 0


def test_narrowing_halves_the_page_and_keeps_everything_else():
    assert narrow({"per_page": 100})["per_page"] == 50
    assert narrow({})["per_page"] == 50
    assert narrow({"per_page": 1})["per_page"] == 1
    assert narrow({"per_page": 40, "since": "2026-01-01"})["since"] == "2026-01-01"
    assert not narrowing_exhausted({"per_page": 2})
    assert narrowing_exhausted({"per_page": 1})
    assert not narrowing_exhausted({})


def test_the_repair_for_a_timeout_never_says_retry():
    text = repair("timeout", {"per_page": 100})
    assert "cheaper" in text
    assert "x-github-request-id" in text
    assert "split by range" in repair("timeout", {"per_page": 1})
    assert "wait exactly as long" in repair("throttled")
    assert "status page" in repair("gateway-early")
    assert repair("ok") == "nothing."


def test_the_baseline_is_never_counted_as_spending():
    assert read_cost(["/a"], 2) == 2
    assert read_cost(["/a", "/b"], 3) == 6
    assert read_cost(["/a"], 0) == 0
    assert read_cost([], 2) == 0
    assert read_cost(None, 2) == 0


def test_parameters_survive_a_value_containing_an_equals_sign():
    assert parse_params(["per_page=100", "q=repo:acme/x is:open"]) == {
        "per_page": "100", "q": "repo:acme/x is:open"}
    assert parse_params(["base=v1...main"])["base"] == "v1...main"
    assert parse_params(None) == {}
''',
"test_js_file": "github-timeout-502.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  GATEWAY, classify, isGateway, isThrottled, lowerHeaders, narrow,
  narrowingExhausted, nearCutoff, parseParams, readCost, repair, requestId,
  retryRepeatsIt, wastedRetries,
} from './github-timeout-502.mjs';

const THROTTLE = { 'Retry-After': '60' };
const EXHAUSTED = { 'X-RateLimit-Remaining': '0' };
const RID = { 'X-GitHub-Request-Id': 'C4E2:1F03:9AB' };

test('only gateway-shaped statuses count', () => {
  assert.ok(isGateway(502));
  assert.ok(isGateway(504));
  assert.ok(!GATEWAY.includes(500));
  assert.ok(!isGateway(500));
  assert.ok(!isGateway(200));
  assert.ok(!isGateway(null));
});

test('headers are read case-insensitively', () => {
  assert.equal(lowerHeaders(RID)['x-github-request-id'], 'C4E2:1F03:9AB');
  assert.equal(requestId(RID), 'C4E2:1F03:9AB');
  assert.equal(requestId({}), null);
  assert.equal(requestId(null), null);
});

test('a throttle is recognised before anything else', () => {
  assert.ok(isThrottled(403, THROTTLE));
  assert.ok(isThrottled(429, EXHAUSTED));
  assert.ok(!isThrottled(403, {}));
  assert.ok(!isThrottled(502, THROTTLE));
  assert.equal(classify(403, 0.4, THROTTLE)[0], 'throttled');
  assert.equal(classify(429, 0.2, EXHAUSTED)[0], 'throttled');
});

test('the cutoff has a tolerance and it is generous', () => {
  assert.ok(nearCutoff(10.4));
  assert.ok(nearCutoff(8.0));
  assert.ok(!nearCutoff(7.9));
  assert.ok(!nearCutoff(0.3));
  assert.ok(!nearCutoff(null));
});

test('a gateway error at the cutoff is the finding', () => {
  const [state, detail] = classify(502, 10.4, RID);
  assert.equal(state, 'timeout');
  assert.match(detail, /10\\.4s/);
  assert.match(detail, /too expensive/);
});

test('the same status arriving fast is a different diagnosis', () => {
  const [state, detail] = classify(502, 0.3, {});
  assert.equal(state, 'gateway-early');
  assert.match(detail, /status page/);
});

test('a success just under the line is not a pass', () => {
  const [state, detail] = classify(200, 9.4, {});
  assert.equal(state, 'slow-success');
  assert.match(detail, /fails on the week/);
  assert.equal(classify(200, 0.4, {})[0], 'ok');
});

test('the other failures are named rather than lumped in', () => {
  assert.equal(classify(500, 3.0, {})[0], 'server-other');
  assert.equal(classify(404, 0.2, {})[0], 'client-error');
  assert.equal(classify(null, 30.0, {})[0], 'client-timeout');
  assert.equal(classify(null, null, {})[0], 'unknown');
  assert.equal(classify('not a status', 1.0, {})[0], 'unknown');
});

test('only the states a retry cannot fix are called repeatable', () => {
  assert.ok(retryRepeatsIt('timeout'));
  assert.ok(retryRepeatsIt('client-timeout'));
  assert.ok(!retryRepeatsIt('gateway-early'));
  assert.ok(!retryRepeatsIt('throttled'));
  assert.equal(wastedRetries('timeout', 3), 3);
  assert.equal(wastedRetries('gateway-early', 3), 0);
  assert.equal(wastedRetries('timeout', null), 0);
});

test('narrowing halves the page and keeps everything else', () => {
  assert.equal(narrow({ per_page: 100 }).per_page, 50);
  assert.equal(narrow({}).per_page, 50);
  assert.equal(narrow({ per_page: 1 }).per_page, 1);
  assert.equal(narrow({ per_page: 40, since: '2026-01-01' }).since, '2026-01-01');
  assert.ok(!narrowingExhausted({ per_page: 2 }));
  assert.ok(narrowingExhausted({ per_page: 1 }));
  assert.ok(!narrowingExhausted({}));
});

test('the repair for a timeout never says retry', () => {
  const text = repair('timeout', { per_page: 100 });
  assert.match(text, /cheaper/);
  assert.match(text, /x-github-request-id/);
  assert.match(repair('timeout', { per_page: 1 }), /split by range/);
  assert.match(repair('throttled'), /wait exactly as long/);
  assert.match(repair('gateway-early'), /status page/);
  assert.equal(repair('ok'), 'nothing.');
});

test('the baseline is never counted as spending', () => {
  assert.equal(readCost(['/a'], 2), 2);
  assert.equal(readCost(['/a', '/b'], 3), 6);
  assert.equal(readCost(['/a'], 0), 0);
  assert.equal(readCost([], 2), 0);
  assert.equal(readCost(null, 2), 0);
});

test('parameters survive a value containing an equals sign', () => {
  assert.deepEqual(parseParams(['per_page=100', 'q=repo:acme/x is:open']),
    { per_page: '100', q: 'repo:acme/x is:open' });
  assert.equal(parseParams(['base=v1...main']).base, 'v1...main');
  assert.deepEqual(parseParams(null), {});
});
''',
"faq": [
 ("Is a 502 from GitHub ever worth retrying?",
  "Yes, when it comes back fast. A gateway error in a few hundred milliseconds is an incident, a proxy problem or a load balancer with nothing behind it, and a retry is exactly right. A gateway error at ten seconds is your query being killed for cost, and the retry costs another ten seconds, another request against your quota and arrives at the same place. The elapsed time is the only thing in the response that separates the two, which is why the script prints it on every attempt."),
 ("How is this different from being rate limited?",
  "A throttle tells you what to do. A secondary limit answers with retry-after and an exhausted primary quota answers with x-ratelimit-reset, and in both cases waiting the stated interval is the whole repair. A timeout gives you no header, no interval and nothing to wait for, because time is not what is missing. The script checks for the rate-limit headers first and refuses to classify anything as a timeout while they are present."),
 ("Where exactly is the ten seconds documented?",
  "GitHub documents that it terminates requests it cannot serve in about ten seconds and asks you to make the query cheaper rather than retry it. The number is approximate and it is not returned in any header, so a script can only infer it from elapsed time. That is why the check uses a tolerance rather than an equality, and why a success at nine seconds is reported as a finding: near the boundary, the exact value matters less than the distance from it."),
 ("What do I actually change to make the request cheaper?",
  "Whatever makes the server do less work. Halve per_page, which the script prints for you. Add since or a path filter to a commits listing. Split a comparison of two distant tags into a few smaller ranges and stitch them. Move the call to GraphQL and request only the fields you use, which for wide REST resources is often the biggest saving available. If none of those are possible, the shape of the data has outgrown the endpoint and the answer is usually a different endpoint."),
 ("Why bother recording x-github-request-id?",
  "Because it identifies your exact failing request in GitHub's logs and it is the first thing support asks for. It only exists on the response, and the response is what a retry wrapper throws away before trying again, so by the time a human is looking at the incident the identifier has usually been destroyed several times over. The script reads it off every attempt and prints it, which costs nothing and occasionally saves a week."),
],
"related": [
 ("/github/retry-after-ignored/", "The client ignores retry-after and hammers on"),
 ("/github/search-incomplete-results/", "incomplete_results is true and nobody checks"),
 ("/github/pr-files-and-commits-caps/", "A pull request's lists are both capped"),
],
"citations": [CITE_TROUBLESHOOTING, CITE_RESOURCE_LIMITS, CITE_BEST_PRACTICES, CITE_STATUS],
},


{
"slug": "unstable-sort-duplicates",
"title": "Rows move between pages and the walk skips records",
"description": "A nightly sync misses issues at random and processes others twice. Offset pagination over a list sorted on a field that changes is not a stable walk.",
"h1": "rows move between pages and the walk skips records",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api pagination duplicate items between pages",
             "github api sort updated pagination missing items",
             "github rest api unstable pagination offset",
             "github issues sync misses records",
             "github api sort created direction asc pagination"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The sync reads the <code>Link</code> header, follows <code>rel=\"next\"</code> to the very end and asks for a hundred items a page. It is, by every check in this section, a correct pagination loop. It also misses about one issue a night and occasionally imports the same one twice, and nobody can reproduce it, because reproducing it requires somebody to touch an issue during the eleven seconds the walk is passing over it.",
"short_answer": """<p>Offset pagination is only stable if the ordering is. <code>page=2</code> means "items 101 to 200 in the current sort", evaluated fresh at the moment page two is requested &mdash; so if the collection is sorted on a field that changes, an item touched between your two requests moves, everything behind it shifts by one, and the record on the boundary is never returned to you at all.</p>
<p>Sort on something immutable and ascending: <code>sort=created&amp;direction=asc</code>. For incremental work use <code>since=&lt;timestamp&gt;</code> and deduplicate on <code>id</code> as you go. Where the walk is long or the collection busy, use the GraphQL API's cursors, which describe a position in the result rather than an offset into it.</p>""",
"problem": """<p>Every other pagination bug in this section leaves a mark you can find later: a short page, a missing header, a count that does not add up. This one leaves nothing. Each individual response is correct, complete and internally consistent. The damage is in the seam between two responses, and the seam is not in either of them.</p>
<p>So the investigation goes to all the wrong places first. The loop gets reviewed and is fine. The page size gets raised and it changes nothing except the size of the gap. Somebody adds a retry, which cannot help, and somebody else adds logging, which records that the record was never seen &mdash; not that it was seen and dropped. The API gets blamed for losing data it returned exactly as asked.</p>
<p>The frequency is what makes it unfixable by staring at it. The window in which an edit can hurt you is the time between two consecutive requests, so the loss rate is roughly the write rate times the walk time, divided by the collection size. On a quiet repository that is zero for months. On a busy one it is one record a night, which is exactly the rate at which a problem is annoying enough to complain about and rare enough that nobody can catch it in the act.</p>""",
"why": """<p><strong>An offset is a position in an ordering, not a bookmark on a record.</strong> When you ask for page two, GitHub sorts the collection as it exists at that moment and hands you the second slice of it. Nothing carries over from your first request; there is no snapshot and no cursor. If the ordering changed in between, the slice boundaries fall in different places, and the difference between where they fell the first time and where they fall now is the data you lose.</p>
<p><strong>Skips and duplicates are not the same failure.</strong> If an item moves <em>forward</em> past your read position, everything behind it shifts back by one and one record slides from the top of page two to the bottom of page one, which you have already read: it is never returned. If an item is <em>inserted</em> at the head, everything shifts the other way and one record appears on both pages: you process it twice. Duplicates are visible and idempotency handles them. Skips are silent and idempotency does nothing at all for them.</p>
<p><strong>Which one you get depends on the sort key, and it is a real distinction.</strong> An immutable key in ascending order &mdash; <code>created</code>, oldest first &mdash; only ever grows at the end you have not reached yet, so a walk over it can neither skip nor repeat. The same key descending has new rows arriving at the head, which shifts your window and repeats records, but never hides one. A mutable key such as <code>updated</code> lets any row move anywhere at any time, and that is the only combination that can lose data for good.</p>
<p><strong>Correct pagination does not save you.</strong> This is the note for the client that got everything else right. Following <code>rel="next"</code> to the end is necessary and it is not sufficient, because the header describes where the next slice starts, not which records were in the previous one. <a href="/github/link-header-not-followed/">The first-page-only bug</a> and <a href="/github/per-page-over-100-clamped/">the clamped page size</a> are both loop bugs with loop repairs. This one is repaired by changing two query parameters and touching the loop not at all.</p>
<p><strong>A bigger page size helps a little and for the wrong reason.</strong> Raising <code>per_page</code> to 100 reduces the number of seams, because there are fewer requests and therefore fewer moments at which the ordering can change under you. It does not remove a single one of them. Treating it as the fix produces a job that loses a fifth as much data and is exactly as wrong.</p>
<p><strong>The script proves the exposure and sometimes catches it in the act.</strong> Sorting on a mutable key is a property of your request that a read-only observer can read straight back. Whether it has actually cost you a record needs evidence, so the check walks the same window twice and diffs the id sets, and it is careful about what it counts: a row appearing only in the second walk of an ascending, immutable listing is the collection growing, not the walk failing, and calling that a finding would be a false alarm shipped to a reader.</p>""",
"steps": [
 {"h": "Write down the sort your request actually sends",
  "body": """<p>Not the one you assume. If your code does not set <code>sort</code> and <code>direction</code>, the endpoint picks, and the choice is documented per endpoint rather than being one rule across the API. The script takes the sort as an argument and refuses to guess it, because a check that assumed the wrong default would give a confident answer about a request you never made.</p>"""},
 {"h": "Classify the key before you measure anything",
  "body": """<p><code>updated</code>, <code>pushed</code>, <code>comments</code> and <code>popularity</code> all change while you read. <code>created</code> does not. Ascending on an immutable key is the only combination that cannot lose you a record, and knowing which of the three you are in tells you whether you are looking for duplicates, for skips, or for nothing at all.</p>"""},
 {"h": "Walk the same window twice and diff the ids",
  "body": """<p>Two walks of the first few pages, back to back, on the collection as it really is. Any id present in one and absent from the other is the ordering moving under the loop. On a quiet repository the diff will be empty, which is not a clean bill of health &mdash; it is a quiet hour, and the script says so rather than reporting a pass.</p>"""},
 {"h": "Count repeats inside a single walk too",
  "body": """<p>The same id twice in one walk is the other half of the failure and it is proof on its own, without needing a second walk to compare against. It is also the friendlier half: a duplicate you can see is a duplicate you can deduplicate. The script reports the two kinds of evidence separately because they mean different things about what you have lost.</p>"""},
 {"h": "Move to an immutable sort, or to cursors",
  "body": """<p><code>sort=created&amp;direction=asc</code> with <code>per_page=100</code> turns the walk into an append-only read. For incremental syncs, add <code>since</code> and keep deduplicating on <code>id</code>, because overlap at the boundary is by design. For long walks over busy collections, the GraphQL API's cursors are stable against insertion and are the right tool. The check costs one request per page, per walk, and prints that number before it starts.</p>"""},
],
"verify": """<p>After the sort changes, the two walks agree and the risk classification changes with them, which is the part worth checking: the evidence was always intermittent, but the exposure is constant and readable.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_unstable_sort.py \\
  --repo acme/monorepo --sort updated --direction desc --pages 3
# read cost: 6 request(s) against the core hourly quota
# sort=updated direction=desc: mutable key, so a row can move anywhere between
# two requests. Both skips and duplicates are possible
# walk 1 collected 300 id(s), walk 2 collected 300 id(s)
# proven-skips: 2 id(s) appeared in one walk and not the other
# repair: sort on an immutable key ascending, sort=created&direction=asc

# the same window, sorted on something that does not move
GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_unstable_sort.py \\
  --repo acme/monorepo --sort created --direction asc --pages 3
# stable-walk: created ascending only grows at the end you have not reached,
# so this walk can neither skip a record nor return one twice</code></pre>""",
"code_intro": "One request per page per walk, two walks, and a classification that does not need the network at all. The interesting part is what counts as evidence: a two-walk diff means different things depending on the sort, so an id that shows up only in the second walk of an ascending immutable listing is growth rather than instability, and the script drops it rather than reporting a finding it cannot stand behind. All of that is pure, so the rule can be argued with in the tests instead of in production.",
"py_file": "github_unstable_sort.py",
"py": '''"""Show that a paginated walk is being reordered underneath itself.

Read only. One GET per page per walk, two walks by default. Nothing is written
and the repair is printed rather than performed.

Offset pagination is only stable if the ordering is. page=2 means "items 101 to
200 in the current sort", evaluated when page two is asked for, so an item that
moves between two requests shifts everything behind it and the record on the
boundary is never returned at all.

What this can and cannot see: the exposure is readable from your own request,
because the sort key is in it. The damage is intermittent by nature, so an empty
diff means a quiet window rather than a safe walk, and the script says which of
the two it is looking at.

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
log = logging.getLogger("github_unstable_sort")

API = "https://api.github.com"
UA = "github-unstable-sort/1.0"

MAX_PER_PAGE = 100

# Keys whose value changes while you are reading the collection. A row sorted on
# one of these can move in either direction at any moment.
MUTABLE_SORTS = {"updated", "pushed", "comments", "popularity", "long-running",
                 "reactions", "interactions", "best-match", "relevance", "stars",
                 "forks", "help-wanted-issues"}

# Keys that are set once and never move afterwards.
IMMUTABLE_SORTS = {"created", "full_name", "id"}

# What GitHub applies when a request names a sort but no direction. Descending
# is the common default and it is the one that shifts a window.
DEFAULT_DIRECTION = "desc"

LINK = re.compile(r'<([^>]+)>\\s*;\\s*rel="([^"]+)"')


def parse_link(header):
    """Parse a Link header into {rel: url}. Pure."""
    if not header:
        return {}
    return {rel: url for url, rel in LINK.findall(header)}


def normalize(ids):
    """Ids as strings, so two walks can be compared and sorted the same way."""
    return [str(i) for i in (ids or [])]


def sort_kind(sort):
    """Whether this sort key moves while you read. Pure."""
    key = str(sort or "").strip().lower()
    if key in MUTABLE_SORTS:
        return "mutable"
    if key in IMMUTABLE_SORTS:
        return "immutable"
    return "unknown"


def walk_risk(sort, direction=None):
    """What a walk over this ordering can lose. Pure. Returns (risk, detail).

    Three outcomes, not two, and the middle one is the reason this function
    exists. An immutable key descending shifts your window when a row is
    inserted at the head, which repeats records and never hides one. A mutable
    key lets a row move past your read position, which hides it for good.
    """
    kind = sort_kind(sort)
    way = str(direction or DEFAULT_DIRECTION).strip().lower()
    if kind == "unknown":
        return ("unknown",
                "%r is not a sort key this check knows, so name the one your "
                "request actually sends." % (sort,))
    if way not in ("asc", "desc"):
        return ("unknown", "%r is not a direction." % (direction,))
    if kind == "mutable":
        return ("skips-and-duplicates",
                "sort=%s is a key that changes while you read, so a row can "
                "move anywhere between two requests. Both skips and duplicates "
                "are possible and only one of them is visible." % sort)
    if way == "desc":
        return ("duplicates-only",
                "sort=%s descending is stable per row, but new rows arrive at "
                "the head and shift your window, so a record can be returned "
                "twice. Nothing can be hidden." % sort)
    return ("append-only",
            "sort=%s ascending only grows at the end you have not reached yet, "
            "so this walk can neither skip a record nor return one twice." % sort)


def duplicates_within(ids):
    """Ids returned more than once inside a single walk. Pure, sorted."""
    seen, twice = set(), set()
    for i in normalize(ids):
        if i in seen:
            twice.add(i)
        seen.add(i)
    return sorted(twice)


def compare_walks(first, second):
    """Diff two walks of the same window. Pure.

    Reports the raw difference in both directions plus the repeats inside each
    walk. Interpretation is deliberately somebody else's job, because what the
    difference means depends on how the collection is sorted.
    """
    a, b = normalize(first), normalize(second)
    sa, sb = set(a), set(b)
    return {
        "missing": sorted(sa - sb),
        "appeared": sorted(sb - sa),
        "repeated": sorted(set(duplicates_within(a)) | set(duplicates_within(b))),
        "first_count": len(a),
        "second_count": len(b),
    }


def evidence(risk, diff):
    """Which parts of a two-walk diff actually prove instability. Pure.

    On an append-only walk, ids that show up only in the second pass are the
    collection growing, which is not a finding and must not be reported as one.
    On a window that shifts by design, set differences at the edges prove
    nothing either way, so only repeats count.
    """
    diff = diff or {}
    if risk == "skips-and-duplicates":
        return sorted(set(diff.get("missing") or []) | set(diff.get("appeared") or []))
    if risk == "append-only":
        return sorted(diff.get("missing") or [])
    return []


def verdict(sort, direction=None, first=None, second=None):
    """Classify the ordering, and the evidence if there is any. Pure."""
    risk, detail = walk_risk(sort, direction)
    if risk == "unknown":
        return ("unknown", detail)

    if first is not None and second is not None:
        diff = compare_walks(first, second)
        proof = evidence(risk, diff)
        if proof:
            return ("proven-skips",
                    "%d id(s) appeared in one walk of this window and not the "
                    "other, so the ordering moved between the two reads and a "
                    "record on a page boundary was never returned."
                    % len(proof))
        if diff["repeated"]:
            return ("proven-duplicates",
                    "%d id(s) came back twice inside a single walk, so the "
                    "window shifted mid read. Nothing was hidden, but the job "
                    "processed a record more than once." % len(diff["repeated"]))

    if risk == "skips-and-duplicates":
        return ("exposed",
                detail + " The two walks agreed this time, which is a quiet "
                         "window rather than a safe walk.")
    if risk == "duplicates-only":
        return ("insertion-shift", detail)
    return ("stable-walk", detail)


def stable_params(per_page=MAX_PER_PAGE, since=None):
    """The request that makes the walk safe. Pure."""
    params = {"sort": "created", "direction": "asc", "per_page": int(per_page)}
    if since:
        params["since"] = since
    return params


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state in ("proven-skips", "exposed"):
        return ("sort on an immutable key ascending, sort=created&direction=asc, "
                "so the collection only grows at the end you have not reached. "
                "For incremental work add since=<timestamp> and deduplicate on "
                "id, and for long walks use GraphQL cursors instead of offsets.")
    if state in ("proven-duplicates", "insertion-shift"):
        return ("deduplicate on id as you go, and prefer direction=asc so new "
                "rows land behind your read position instead of in front of "
                "it. Nothing is being lost here, but the same record is being "
                "processed more than once.")
    if state == "stable-walk":
        return ("nothing on the ordering. Keep per_page at 100 to reduce the "
                "number of seams, and keep the sort where it is.")
    return "name the sort and direction your request actually sends."


def read_cost(pages, walks=2):
    """Requests this run will spend against the core quota. Pure."""
    try:
        return max(0, int(pages)) * max(0, int(walks))
    except (TypeError, ValueError):
        return 0


def walk_once(session, path, params, pages):
    """Follow rel=next for at most `pages` pages, collecting ids."""
    ids, url, query = [], API + path, dict(params)
    for _ in range(max(1, pages)):
        r = session.get(url, params=query, timeout=30)
        if r.status_code == 401:
            raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, "
                             "malformed or revoked")
        if r.status_code == 403 and "rate limit" in r.text.lower():
            raise SystemExit("403 rate limited. GET /rate_limit reports the "
                             "reset time and does not itself consume quota")
        if r.status_code != 200:
            log.info("%s returned %d; stopping this walk", url, r.status_code)
            break
        try:
            items = r.json()
        except ValueError:
            break
        if not isinstance(items, list):
            break
        ids.extend(item.get("id") for item in items if isinstance(item, dict))
        nxt = parse_link(r.headers.get("Link")).get("next")
        if not nxt:
            break
        # The next URL already carries the query, so it is followed exactly as
        # given rather than rebuilt from the parameters.
        url, query = nxt, {}
    return normalize(ids)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--path", help="API path to walk, default the repo's issues")
    ap.add_argument("--sort", required=True,
                    help="the sort your request actually sends, e.g. updated")
    ap.add_argument("--direction", default=DEFAULT_DIRECTION,
                    choices=("asc", "desc"))
    ap.add_argument("--pages", type=int, default=3,
                    help="pages per walk. Two walks are made.")
    ap.add_argument("--per-page", type=int, default=MAX_PER_PAGE)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    path = args.path or "/repos/%s/issues" % args.repo
    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(args.pages, 2))

    risk, detail = walk_risk(args.sort, args.direction)
    log.info("sort=%s direction=%s: %s", args.sort, args.direction, detail)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    params = {"sort": args.sort, "direction": args.direction,
              "per_page": args.per_page}
    first = walk_once(session, path, params, args.pages)
    second = walk_once(session, path, params, args.pages)
    log.info("walk 1 collected %d id(s), walk 2 collected %d id(s)",
             len(first), len(second))

    diff = compare_walks(first, second)
    state, verdict_detail = verdict(args.sort, args.direction, first, second)
    log.info("%s: %s", state, verdict_detail)
    log.info("repair: %s", repair(state))

    print(json.dumps({
        "requests_spent": read_cost(args.pages, 2),
        "path": path,
        "sort": args.sort,
        "direction": args.direction,
        "sort_kind": sort_kind(args.sort),
        "risk": risk,
        "diff": diff,
        "evidence": evidence(risk, diff),
        "state": state,
        "detail": verdict_detail,
        "stable_params": stable_params(args.per_page),
        "repair": repair(state),
    }, indent=2, default=str))
    return 1 if state in ("proven-skips", "proven-duplicates", "exposed") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-unstable-sort.mjs",
"js": '''/**
 * Show that a paginated walk is being reordered underneath itself.
 *
 * Read only. One GET per page per walk, two walks. Nothing is written and the
 * repair is printed rather than performed.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the repository
 *   GITHUB_REPO       owner/name
 *   GITHUB_PATH       API path to walk, default the repo's issues
 *   GITHUB_SORT       the sort your request actually sends, e.g. updated
 *   GITHUB_DIRECTION  asc or desc, default desc
 *   GITHUB_PAGES      pages per walk, default 3
 */
const API = 'https://api.github.com';
const UA = 'github-unstable-sort/1.0';

export const MAX_PER_PAGE = 100;

/** Keys whose value changes while you are reading the collection. */
export const MUTABLE_SORTS = new Set(['updated', 'pushed', 'comments', 'popularity',
  'long-running', 'reactions', 'interactions', 'best-match', 'relevance', 'stars',
  'forks', 'help-wanted-issues']);

/** Keys that are set once and never move afterwards. */
export const IMMUTABLE_SORTS = new Set(['created', 'full_name', 'id']);

/** What GitHub applies when a request names a sort but no direction. */
export const DEFAULT_DIRECTION = 'desc';

const LINK = /<([^>]+)>\\s*;\\s*rel="([^"]+)"/g;

/** Parse a Link header into {rel: url}. Pure. */
export function parseLink(header) {
  const out = {};
  if (!header) return out;
  for (const m of String(header).matchAll(LINK)) out[m[2]] = m[1];
  return out;
}

/** Ids as strings, so two walks compare and sort the same way. Pure. */
export function normalize(ids) {
  return (ids || []).map((i) => String(i));
}

/** Whether this sort key moves while you read. Pure. */
export function sortKind(sort) {
  const key = String(sort ?? '').trim().toLowerCase();
  if (MUTABLE_SORTS.has(key)) return 'mutable';
  if (IMMUTABLE_SORTS.has(key)) return 'immutable';
  return 'unknown';
}

/** What a walk over this ordering can lose. Pure. Returns [risk, detail]. */
export function walkRisk(sort, direction = null) {
  const kind = sortKind(sort);
  const way = String(direction ?? DEFAULT_DIRECTION).trim().toLowerCase();
  if (kind === 'unknown') {
    return ['unknown',
      `${sort} is not a sort key this check knows, so name the one your request `
      + 'actually sends.'];
  }
  if (way !== 'asc' && way !== 'desc') {
    return ['unknown', `${direction} is not a direction.`];
  }
  if (kind === 'mutable') {
    return ['skips-and-duplicates',
      `sort=${sort} is a key that changes while you read, so a row can move `
      + 'anywhere between two requests. Both skips and duplicates are possible '
      + 'and only one of them is visible.'];
  }
  if (way === 'desc') {
    return ['duplicates-only',
      `sort=${sort} descending is stable per row, but new rows arrive at the `
      + 'head and shift your window, so a record can be returned twice. Nothing '
      + 'can be hidden.'];
  }
  return ['append-only',
    `sort=${sort} ascending only grows at the end you have not reached yet, so `
    + 'this walk can neither skip a record nor return one twice.'];
}

/** Ids returned more than once inside a single walk. Pure, sorted. */
export function duplicatesWithin(ids) {
  const seen = new Set();
  const twice = new Set();
  for (const i of normalize(ids)) {
    if (seen.has(i)) twice.add(i);
    seen.add(i);
  }
  return [...twice].sort();
}

/** Diff two walks of the same window. Pure. */
export function compareWalks(first, second) {
  const a = normalize(first);
  const b = normalize(second);
  const sa = new Set(a);
  const sb = new Set(b);
  return {
    missing: [...sa].filter((i) => !sb.has(i)).sort(),
    appeared: [...sb].filter((i) => !sa.has(i)).sort(),
    repeated: [...new Set([...duplicatesWithin(a), ...duplicatesWithin(b)])].sort(),
    first_count: a.length,
    second_count: b.length,
  };
}

/** Which parts of a two-walk diff actually prove instability. Pure. */
export function evidence(risk, diff) {
  const d = diff || {};
  if (risk === 'skips-and-duplicates') {
    return [...new Set([...(d.missing || []), ...(d.appeared || [])])].sort();
  }
  if (risk === 'append-only') return [...(d.missing || [])].sort();
  return [];
}

/** Classify the ordering, and the evidence if there is any. Pure. */
export function verdict(sort, direction = null, first = null, second = null) {
  const [risk, detail] = walkRisk(sort, direction);
  if (risk === 'unknown') return ['unknown', detail];

  if (first !== null && second !== null) {
    const diff = compareWalks(first, second);
    const proof = evidence(risk, diff);
    if (proof.length) {
      return ['proven-skips',
        `${proof.length} id(s) appeared in one walk of this window and not the `
        + 'other, so the ordering moved between the two reads and a record on a '
        + 'page boundary was never returned.'];
    }
    if (diff.repeated.length) {
      return ['proven-duplicates',
        `${diff.repeated.length} id(s) came back twice inside a single walk, so `
        + 'the window shifted mid read. Nothing was hidden, but the job '
        + 'processed a record more than once.'];
    }
  }

  if (risk === 'skips-and-duplicates') {
    return ['exposed',
      `${detail} The two walks agreed this time, which is a quiet window rather `
      + 'than a safe walk.'];
  }
  if (risk === 'duplicates-only') return ['insertion-shift', detail];
  return ['stable-walk', detail];
}

/** The request that makes the walk safe. Pure. */
export function stableParams(perPage = MAX_PER_PAGE, since = null) {
  const params = { sort: 'created', direction: 'asc', per_page: Number(perPage) };
  if (since) params.since = since;
  return params;
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'proven-skips' || state === 'exposed') {
    return 'sort on an immutable key ascending, sort=created&direction=asc, so '
      + 'the collection only grows at the end you have not reached. For '
      + 'incremental work add since=<timestamp> and deduplicate on id, and for '
      + 'long walks use GraphQL cursors instead of offsets.';
  }
  if (state === 'proven-duplicates' || state === 'insertion-shift') {
    return 'deduplicate on id as you go, and prefer direction=asc so new rows '
      + 'land behind your read position instead of in front of it. Nothing is '
      + 'being lost here, but the same record is being processed more than once.';
  }
  if (state === 'stable-walk') {
    return 'nothing on the ordering. Keep per_page at 100 to reduce the number '
      + 'of seams, and keep the sort where it is.';
  }
  return 'name the sort and direction your request actually sends.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(pages, walks = 2) {
  const p = Number(pages);
  const w = Number(walks);
  if (!Number.isFinite(p) || !Number.isFinite(w)) return 0;
  return Math.max(0, Math.trunc(p)) * Math.max(0, Math.trunc(w));
}

function headersFor(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function walkOnce(token, path, params, pages) {
  const ids = [];
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  let next = url.toString();
  for (let i = 0; i < Math.max(1, pages) && next; i += 1) {
    const res = await fetch(next, { headers: headersFor(token) });
    if (!res.ok) {
      console.log(`${next} returned ${res.status}; stopping this walk`);
      break;
    }
    let items = null;
    try { items = await res.json(); } catch { items = null; }
    if (!Array.isArray(items)) break;
    for (const item of items) if (item && item.id !== undefined) ids.push(item.id);
    next = parseLink(res.headers.get('link')).next || null;
  }
  return normalize(ids);
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  const sort = process.env.GITHUB_SORT;
  if (!token || !repo || !sort) {
    console.error('set GITHUB_TOKEN (read-only is enough), GITHUB_REPO=owner/name '
      + 'and GITHUB_SORT=updated');
    process.exitCode = 2;
    return;
  }
  const direction = process.env.GITHUB_DIRECTION || DEFAULT_DIRECTION;
  const pages = Number(process.env.GITHUB_PAGES || 3);
  const path = process.env.GITHUB_PATH || `/repos/${repo}/issues`;
  console.log(`read cost: ${readCost(pages, 2)} request(s) against the core hourly quota`);

  const [risk, detail] = walkRisk(sort, direction);
  console.log(`sort=${sort} direction=${direction}: ${detail}`);

  const params = { sort, direction, per_page: MAX_PER_PAGE };
  const first = await walkOnce(token, path, params, pages);
  const second = await walkOnce(token, path, params, pages);
  console.log(`walk 1 collected ${first.length} id(s), walk 2 collected ${second.length} id(s)`);

  const diff = compareWalks(first, second);
  const [state, verdictDetail] = verdict(sort, direction, first, second);
  console.log(`${state}: ${verdictDetail}`);
  console.log(`repair: ${repair(state)}`);

  console.log(JSON.stringify({
    requests_spent: readCost(pages, 2),
    path,
    sort,
    direction,
    sort_kind: sortKind(sort),
    risk,
    diff,
    evidence: evidence(risk, diff),
    state,
    detail: verdictDetail,
    stable_params: stableParams(MAX_PER_PAGE),
    repair: repair(state),
  }, null, 2));
  process.exitCode = ['proven-skips', 'proven-duplicates', 'exposed'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three tests carry the note. The first is that the risk classification has three outcomes rather than two, because an immutable key descending can repeat a record and can never hide one, and collapsing that into \"unstable\" would send a reader chasing data that was never lost. The second is that evidence is interpreted against the ordering, so growth in an append-only walk is not reported as a skip. The third is that an empty diff on a mutable sort comes back as exposure rather than as a pass. The rest pins the diff, the repairs, and the cost of the two walks.",
"test_py_file": "test_github_unstable_sort.py",
"test_py": '''from github_unstable_sort import (
    DEFAULT_DIRECTION, compare_walks, duplicates_within, evidence, normalize,
    parse_link, read_cost, repair, sort_kind, stable_params, verdict, walk_risk,
)


def test_sort_keys_are_sorted_into_movers_and_non_movers():
    assert sort_kind("updated") == "mutable"
    assert sort_kind("PUSHED") == "mutable"
    assert sort_kind("comments") == "mutable"
    assert sort_kind("created") == "immutable"
    assert sort_kind("full_name") == "immutable"
    assert sort_kind("banana") == "unknown"
    assert sort_kind(None) == "unknown"


def test_the_risk_has_three_outcomes_not_two():
    assert walk_risk("updated", "desc")[0] == "skips-and-duplicates"
    assert walk_risk("updated", "asc")[0] == "skips-and-duplicates"
    assert walk_risk("created", "desc")[0] == "duplicates-only"
    assert walk_risk("created", "asc")[0] == "append-only"
    assert walk_risk("banana", "asc")[0] == "unknown"
    assert walk_risk("created", "sideways")[0] == "unknown"


def test_a_missing_direction_is_treated_as_the_one_that_shifts():
    assert DEFAULT_DIRECTION == "desc"
    assert walk_risk("created")[0] == "duplicates-only"


def test_only_the_mutable_key_can_hide_a_record():
    assert "hidden" in walk_risk("created", "desc")[1]
    assert "neither skip" in walk_risk("created", "asc")[1]
    assert "only one of them is visible" in walk_risk("updated", "desc")[1]


def test_repeats_inside_one_walk_are_found_and_deduplicated():
    assert duplicates_within([1, 2, 2, 3, 3, 3]) == ["2", "3"]
    assert duplicates_within([1, 2, 3]) == []
    assert duplicates_within([]) == []
    assert duplicates_within(None) == []


def test_ids_are_compared_as_strings_so_two_walks_line_up():
    assert normalize([1, "1", 2]) == ["1", "1", "2"]
    diff = compare_walks([1, 2, 3], ["1", "2", "4"])
    assert diff["missing"] == ["3"]
    assert diff["appeared"] == ["4"]
    assert diff["first_count"] == 3


def test_growth_in_an_append_only_walk_is_not_a_finding():
    diff = compare_walks([1, 2, 3], [1, 2, 3, 4])
    assert evidence("append-only", diff) == []
    assert evidence("skips-and-duplicates", diff) == ["4"]


def test_a_shifting_window_proves_nothing_from_set_differences():
    diff = compare_walks([1, 2, 3], [0, 1, 2])
    assert evidence("duplicates-only", diff) == []
    assert evidence("append-only", diff) == ["3"]


def test_a_record_in_one_walk_and_not_the_other_is_the_finding():
    state, detail = verdict("updated", "desc", [1, 2, 3], [1, 2, 4])
    assert state == "proven-skips"
    assert "never returned" in detail


def test_a_repeat_inside_a_walk_is_reported_as_the_gentler_failure():
    state, detail = verdict("created", "desc", [1, 2, 2, 3], [1, 2, 3])
    assert state == "proven-duplicates"
    assert "Nothing was hidden" in detail


def test_agreeing_walks_on_a_mutable_sort_are_exposure_not_a_pass():
    state, detail = verdict("updated", "desc", [1, 2, 3], [1, 2, 3])
    assert state == "exposed"
    assert "quiet window rather than a safe walk" in detail


def test_the_safe_ordering_comes_back_clean():
    assert verdict("created", "asc", [1, 2, 3], [1, 2, 3])[0] == "stable-walk"
    assert verdict("created", "desc", [1, 2, 3], [1, 2, 3])[0] == "insertion-shift"
    assert verdict("banana", "asc", [1], [1])[0] == "unknown"


def test_a_walk_with_no_evidence_still_gets_classified():
    assert verdict("updated", "desc")[0] == "exposed"
    assert verdict("created", "asc")[0] == "stable-walk"


def test_the_repairs_are_different_for_skips_and_for_duplicates():
    assert "sort=created&direction=asc" in repair("proven-skips")
    assert "since=" in repair("exposed")
    assert "deduplicate on id" in repair("proven-duplicates")
    assert "Nothing is being lost" in repair("insertion-shift")
    assert repair("stable-walk").startswith("nothing on the ordering")


def test_the_printed_repair_is_a_request_you_can_send():
    assert stable_params() == {"sort": "created", "direction": "asc", "per_page": 100}
    assert stable_params(50, "2026-01-01T00:00:00Z")["since"] == "2026-01-01T00:00:00Z"


def test_the_walk_follows_the_header_rather_than_counting_pages():
    header = ('<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=2>; rel="next", '
              '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=9>; rel="last"')
    assert set(parse_link(header)) == {"next", "last"}
    assert parse_link(None) == {}


def test_two_walks_cost_twice_what_one_does():
    assert read_cost(3) == 6
    assert read_cost(3, 1) == 3
    assert read_cost(0) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-unstable-sort.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_DIRECTION, compareWalks, duplicatesWithin, evidence, normalize,
  parseLink, readCost, repair, sortKind, stableParams, verdict, walkRisk,
} from './github-unstable-sort.mjs';

test('sort keys are sorted into movers and non-movers', () => {
  assert.equal(sortKind('updated'), 'mutable');
  assert.equal(sortKind('PUSHED'), 'mutable');
  assert.equal(sortKind('comments'), 'mutable');
  assert.equal(sortKind('created'), 'immutable');
  assert.equal(sortKind('full_name'), 'immutable');
  assert.equal(sortKind('banana'), 'unknown');
  assert.equal(sortKind(null), 'unknown');
});

test('the risk has three outcomes, not two', () => {
  assert.equal(walkRisk('updated', 'desc')[0], 'skips-and-duplicates');
  assert.equal(walkRisk('updated', 'asc')[0], 'skips-and-duplicates');
  assert.equal(walkRisk('created', 'desc')[0], 'duplicates-only');
  assert.equal(walkRisk('created', 'asc')[0], 'append-only');
  assert.equal(walkRisk('banana', 'asc')[0], 'unknown');
  assert.equal(walkRisk('created', 'sideways')[0], 'unknown');
});

test('a missing direction is treated as the one that shifts', () => {
  assert.equal(DEFAULT_DIRECTION, 'desc');
  assert.equal(walkRisk('created')[0], 'duplicates-only');
});

test('only the mutable key can hide a record', () => {
  assert.match(walkRisk('created', 'desc')[1], /hidden/);
  assert.match(walkRisk('created', 'asc')[1], /neither skip/);
  assert.match(walkRisk('updated', 'desc')[1], /only one of them is visible/);
});

test('repeats inside one walk are found and deduplicated', () => {
  assert.deepEqual(duplicatesWithin([1, 2, 2, 3, 3, 3]), ['2', '3']);
  assert.deepEqual(duplicatesWithin([1, 2, 3]), []);
  assert.deepEqual(duplicatesWithin([]), []);
  assert.deepEqual(duplicatesWithin(null), []);
});

test('ids are compared as strings so two walks line up', () => {
  assert.deepEqual(normalize([1, '1', 2]), ['1', '1', '2']);
  const diff = compareWalks([1, 2, 3], ['1', '2', '4']);
  assert.deepEqual(diff.missing, ['3']);
  assert.deepEqual(diff.appeared, ['4']);
  assert.equal(diff.first_count, 3);
});

test('growth in an append-only walk is not a finding', () => {
  const diff = compareWalks([1, 2, 3], [1, 2, 3, 4]);
  assert.deepEqual(evidence('append-only', diff), []);
  assert.deepEqual(evidence('skips-and-duplicates', diff), ['4']);
});

test('a shifting window proves nothing from set differences', () => {
  const diff = compareWalks([1, 2, 3], [0, 1, 2]);
  assert.deepEqual(evidence('duplicates-only', diff), []);
  assert.deepEqual(evidence('append-only', diff), ['3']);
});

test('a record in one walk and not the other is the finding', () => {
  const [state, detail] = verdict('updated', 'desc', [1, 2, 3], [1, 2, 4]);
  assert.equal(state, 'proven-skips');
  assert.match(detail, /never returned/);
});

test('a repeat inside a walk is reported as the gentler failure', () => {
  const [state, detail] = verdict('created', 'desc', [1, 2, 2, 3], [1, 2, 3]);
  assert.equal(state, 'proven-duplicates');
  assert.match(detail, /Nothing was hidden/);
});

test('agreeing walks on a mutable sort are exposure, not a pass', () => {
  const [state, detail] = verdict('updated', 'desc', [1, 2, 3], [1, 2, 3]);
  assert.equal(state, 'exposed');
  assert.match(detail, /quiet window rather than a safe walk/);
});

test('the safe ordering comes back clean', () => {
  assert.equal(verdict('created', 'asc', [1, 2, 3], [1, 2, 3])[0], 'stable-walk');
  assert.equal(verdict('created', 'desc', [1, 2, 3], [1, 2, 3])[0], 'insertion-shift');
  assert.equal(verdict('banana', 'asc', [1], [1])[0], 'unknown');
});

test('a walk with no evidence still gets classified', () => {
  assert.equal(verdict('updated', 'desc')[0], 'exposed');
  assert.equal(verdict('created', 'asc')[0], 'stable-walk');
});

test('the repairs are different for skips and for duplicates', () => {
  assert.match(repair('proven-skips'), /sort=created&direction=asc/);
  assert.match(repair('exposed'), /since=/);
  assert.match(repair('proven-duplicates'), /deduplicate on id/);
  assert.match(repair('insertion-shift'), /Nothing is being lost/);
  assert.ok(repair('stable-walk').startsWith('nothing on the ordering'));
});

test('the printed repair is a request you can send', () => {
  assert.deepEqual(stableParams(), { sort: 'created', direction: 'asc', per_page: 100 });
  assert.equal(stableParams(50, '2026-01-01T00:00:00Z').since, '2026-01-01T00:00:00Z');
});

test('the walk follows the header rather than counting pages', () => {
  const header = '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=2>; rel="next", '
    + '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=9>; rel="last"';
  assert.deepEqual(Object.keys(parseLink(header)).sort(), ['last', 'next']);
  assert.deepEqual(parseLink(null), {});
});

test('two walks cost twice what one does', () => {
  assert.equal(readCost(3), 6);
  assert.equal(readCost(3, 1), 3);
  assert.equal(readCost(0), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("Is this just the pagination bug again?",
  "No. Every other pagination note in this section is about a loop that stopped too early or read the wrong thing: the header was ignored, the page size was clamped, the page parameter did nothing. Here the loop is correct and the ordering is not. You can follow rel=next perfectly to the end of a collection and still never be handed a record, because the record moved to a page you had already read. The repair changes two query parameters and leaves the loop alone."),
 ("Does a bigger page size fix it?",
  "It reduces the exposure and does not remove it. Each request is a moment at which the ordering can change, so ten requests at per_page=100 have a tenth as many seams as a hundred requests at 30. The seams that remain behave exactly as before. per_page=100 is worth setting for its own reasons; treating it as the fix for this gives you a job that loses less data and is no more correct."),
 ("Why is sorting by created ascending safe when descending is not?",
  "Because of where new rows land. Ascending, oldest first, new records are appended after the position you have already passed, so they cannot shift anything you are about to read. Descending, new records arrive at the head, everything moves down by one, and a record you have already seen is served to you again on the next page. That is a duplicate rather than a skip, which is the friendlier of the two failures, but the walk is still not stable."),
 ("What is the default sort on the endpoint I am using?",
  "Look it up for that endpoint rather than assuming, because it is documented per endpoint and it is not one rule across the API. The script takes the sort as a required argument for exactly this reason: a check that guessed the default would report confidently on a request you never sent. If your code does not set sort and direction explicitly, set them, if only so the next person can tell what you are relying on."),
 ("Does GraphQL have the same problem?",
  "Not in the same way. GraphQL pagination is cursor-based: a cursor names a position in the result set rather than an offset into it, so a row inserted or updated elsewhere does not renumber everything behind your position. That makes it the right tool for long walks over busy collections. It has its own costs in points and node limits, but the instability this note is about is not one of them."),
],
"related": [
 ("/github/link-header-not-followed/", "Only the first page is ever read"),
 ("/github/per-page-over-100-clamped/", "per_page above 100 is clamped silently"),
 ("/github/polling-instead-of-webhooks/", "The job polls what a webhook would push"),
],
"citations": [CITE_PAGINATION, CITE_ISSUES, CITE_BEST_PRACTICES, CITE_REPOS],
},


{
"slug": "repo-renamed-301-redirect",
"title": "The repository was renamed and every call now 301s",
"description": "A renamed repository leaves a redirect at the old path. A client that ignores it sees an empty body; one that follows it pays an extra round trip forever.",
"h1": "the repository was renamed and every call now 301s",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 301 moved permanently repository",
             "github repository renamed api redirect",
             "github api location header repositories id",
             "github repo transferred api integration broken",
             "github api node_id stable across rename"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody renamed the repository on a Tuesday. Nothing broke, which is the problem: GitHub left a redirect at the old path and most clients follow it without mentioning it, so the integration kept working against a name that no longer exists. The config still says <code>acme/platform-api</code>. The repository is called <code>acme/core-api</code>. Every request the job makes takes two round trips instead of one, and has done for eight months.",
"short_answer": """<p>Renaming or transferring a repository leaves a permanent redirect at the old path. <code>GET /repos/{owner}/{repo}</code> on the stale name answers <code>301</code> with a <code>Location</code> pointing at the repository's canonical URL, usually <code>https://api.github.com/repositories/{id}</code> rather than the new name.</p>
<p>A <code>301</code> is an instruction to update your code, not something to keep following. Read the new <code>full_name</code> from the response you get after following it once, write that into your configuration, and key any persistent state on the repository's <code>id</code> or <code>node_id</code>, both of which survive every future rename. A <code>302</code> or <code>307</code> is different and should just be followed.</p>""",
"problem": """<p>The two ways this shows up look nothing alike, which is why it gets diagnosed twice.</p>
<p>If your client does not follow redirects &mdash; a hand-rolled fetch wrapper, a webhook receiver, anything with <code>redirect: 'manual'</code> set for good security reasons &mdash; you get a <code>301</code> with an empty body. The code checks the status against 200, or checks whether the parsed body is truthy, and reports the repository as missing. Then somebody spends an afternoon on the token, because "cannot see the repository" is a permissions shape of problem and permissions are where those investigations start.</p>
<p>If your client does follow redirects, which most do, nothing fails at all. That is worse in the long run. Every single call to that repository now costs two requests instead of one: one to be told where it went, one to go there. Your hourly quota drains at double the rate on that path, every latency measurement includes a round trip nobody asked for, and the configuration slowly rots because nothing is ever forcing anyone to correct it. Eight months later the old name means nothing to anyone on the team and it is still what the job is asking for.</p>
<p>The rename itself is invisible from your side. It happened in an org you may not be in, announced in a channel you are not in, and it left no trace in your logs because the API went out of its way to keep working.</p>""",
"why": """<p><strong>301 means update, 302 and 307 mean follow.</strong> GitHub documents the distinction and it matters. A permanent redirect is the API telling you that the resource has a new address and that continuing to ask for the old one is your choice, not its problem. A temporary one is routing, and writing it into your config would be the actual mistake. The check treats them as two different states with two opposite repairs, because a script that says "follow it" for both is wrong half the time.</p>
<p><strong>The <code>Location</code> usually names an id, not a name.</strong> The canonical URL is typically <code>https://api.github.com/repositories/{id}</code>, so the header hands you the durable key rather than the new string. That is a hint about the real repair: names are labels people change, ids are not. Follow it once, read <code>full_name</code> out of the body for the configuration a human reads, and key your database rows, caches and mappings on the numeric <code>id</code> or the <code>node_id</code> so the next rename costs nothing at all.</p>
<p><strong>Redirect behaviour is not uniform across methods or clients.</strong> Reads are followed by nearly every HTTP library. Anything that is not a read is treated differently by different clients: some refuse to follow at all, some drop the request body, some silently change the request into a read. All of the scripts in this section are read-only so none of them can demonstrate that for you, but it is the reason a stale name is a latent failure rather than a permanent success &mdash; the day the integration starts doing something other than reading, the redirect stops being free.</p>
<p><strong>This is not a 404.</strong> <a href="/github/404-masking-403/">The 404 note</a> is about an answer that means four different things at once: no such repository, no permission, no installation, dead token. A 301 has none of that ambiguity; it is the most informative answer in this whole section, because it contains the address of the thing you were looking for. The failure is entirely in not reading it. If your check reports a 404 on a name you believe in, that is the other note and a different set of probes.</p>
<p><strong>Case is not a rename.</strong> Repository names are matched case-insensitively, so <code>acme/Platform</code> and <code>acme/platform</code> are the same repository and neither one is stale. A comparison of <code>full_name</code> against the configured string with the wrong case sensitivity manufactures a rename that never happened, which is a false alarm shipped to somebody who then goes and edits a config that was fine. The check reports it as its own state and tells you there is nothing to do.</p>
<p><strong>What a read-only script can prove here is unusually complete.</strong> Most notes in this section can only show that a trap is set. This one can show the whole thing: the old path answers 301, here is where it points, here is the current <code>full_name</code>, and here is the id to key on instead. The only part it cannot see is whether your client follows redirects, so it reports both consequences and lets you recognise yours.</p>""",
"steps": [
 {"h": "Ask for the configured name with redirects turned off",
  "body": """<p>One <code>GET /repos/{owner}/{repo}</code> with automatic redirects disabled. This is the only way to see the <code>301</code> at all; with following enabled your client swallows it and hands you a <code>200</code> from a different URL, which is precisely how this has been invisible for months.</p>"""},
 {"h": "Read the status and the Location together",
  "body": """<p><code>301</code> or <code>308</code> means the name in your configuration is stale. <code>302</code> or <code>307</code> means follow it and change nothing. The <code>Location</code> usually points at <code>/repositories/{id}</code>, which is the durable identifier rather than the new name, so it is worth keeping even after you have looked up the label.</p>"""},
 {"h": "Follow it once to get the current full_name",
  "body": """<p>A second request, to the address you were given, returns the repository object. <code>full_name</code> in that body is what goes into your configuration; <code>id</code> and <code>node_id</code> are what should go into anything persistent. Two requests total per repository, which the script prints before it spends them.</p>"""},
 {"h": "Compare names case-insensitively",
  "body": """<p>A difference in capitalisation is not a rename and must not be reported as one. Compare the configured string against <code>full_name</code> with case folded, and only call it stale when the letters themselves differ. The script has a state for the case-only result so that nobody edits a config that was already correct.</p>"""},
 {"h": "Write down the id, not just the new name",
  "body": """<p>Updating the name fixes today. Keying persistent state on <code>id</code> or <code>node_id</code> fixes every future rename, including the ones nobody will tell you about. If your integration stores a mapping from repository to anything at all &mdash; queue, config, dashboard row &mdash; the string is the wrong key and always was.</p>"""},
],
"verify": """<p>After the configuration is updated, the first request is the only request, and the state changes from a redirect to a name that matches.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_repo_renamed.py --repo acme/platform-api
# read cost: at most 2 request(s) per repository against the core hourly quota
# acme/platform-api: 301 -> https://api.github.com/repositories/1300192
# renamed-permanent: the configured name is stale and GitHub is redirecting it
# permanently to repository id 1300192, now called acme/core-api
# repair: update the stored name to acme/core-api and key persistent state on
# id 1300192 or node_id R_kgDOE..., which survive the next rename too
# a client that follows this pays 1 extra request per call: 1200 calls an hour
# becomes 2400

GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_repo_renamed.py --repo acme/core-api
# current: the configured name matches full_name and the request was answered
# without a redirect</code></pre>""",
"code_intro": "One GET with automatic redirects disabled, which is the only way the 301 is visible at all, and one more to follow it where there is something to follow. The classification afterwards is pure and has more states than you would expect from a two-branch problem, because a permanent redirect and a temporary one have opposite repairs, a difference of capitalisation is not a rename, and a 404 belongs to another note entirely. Each of those distinctions is one wrong config edit avoided.",
"py_file": "github_repo_renamed.py",
"py": '''"""Find repositories whose configured name is a redirect to somewhere else.

Read only. At most two GETs per repository: one with redirects disabled, and
one to follow the redirect where there is one. Nothing is written and the
repair is printed rather than performed.

Renaming or transferring a repository leaves a permanent redirect at the old
path. A client that does not follow redirects sees a 301 with an empty body and
reports the repository as missing; a client that does follow them works
perfectly and pays an extra round trip on every call, forever, while the
configured name rots.

What this can and cannot see: whether your own client follows redirects is
invisible from here, so both consequences are reported and you recognise yours.
Everything else about this failure is fully readable, which is unusual.

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
log = logging.getLogger("github_repo_renamed")

API = "https://api.github.com"
UA = "github-repo-renamed/1.0"

# 301 and 308 say the address changed. 302 and 307 say the routing changed.
# The difference is the whole reason this script has more than two states.
PERMANENT = (301, 308)
TEMPORARY = (302, 307)

# The canonical URL is usually the numeric form, which hands you the durable
# key rather than the new name.
LOC_ID = re.compile(r"/repositories/(\\d+)")
LOC_FULL = re.compile(r"/repos/([^/?#]+)/([^/?#]+)")


def is_redirect(status):
    """Whether this status moves you somewhere else. Pure."""
    try:
        return int(status) in PERMANENT + TEMPORARY
    except (TypeError, ValueError):
        return False


def is_permanent(status):
    """Whether this status means update your code rather than follow it. Pure."""
    try:
        return int(status) in PERMANENT
    except (TypeError, ValueError):
        return False


def repo_from_location(location):
    """What the Location header points at. Pure. Returns (kind, value) or None.

    Two shapes, and the numeric one is the common answer: GitHub redirects a
    renamed repository to /repositories/{id}, which is the identifier that
    survives every future rename.
    """
    if not location:
        return None
    text = str(location)
    m = LOC_ID.search(text)
    if m:
        return ("id", m.group(1))
    m = LOC_FULL.search(text)
    if m:
        return ("full_name", "%s/%s" % (m.group(1), m.group(2)))
    return None


def same_repo(a, b):
    """Whether two owner/name strings name the same repository. Pure.

    Case-insensitively, because GitHub matches names that way and a comparison
    that does not manufactures a rename nobody performed.
    """
    if not a or not b:
        return False
    return str(a).strip().lower() == str(b).strip().lower()


def verdict(asked, status, location=None, full_name=None):
    """Classify one probe of a configured repository name. Pure."""
    try:
        code = int(status)
    except (TypeError, ValueError):
        return ("unknown", "the probe produced no readable status.")

    if is_permanent(code):
        target = repo_from_location(location)
        if not target:
            return ("renamed-permanent",
                    "%d says the configured name is stale, but the response "
                    "carried no usable Location, so the new name has to be read "
                    "from the body after following it once." % code)
        kind, value = target
        named = (", now called %s" % full_name) if full_name else ""
        if kind == "id":
            return ("renamed-permanent",
                    "the configured name is stale and GitHub is redirecting it "
                    "permanently to repository id %s%s." % (value, named))
        return ("renamed-permanent",
                "the configured name is stale and GitHub is redirecting it "
                "permanently to %s%s." % (value, named))

    if is_redirect(code):
        return ("moved-temporary",
                "%d is a temporary redirect, so follow it and change nothing. "
                "Writing this address into your configuration is the mistake "
                "here, not the fix." % code)

    if code == 404:
        return ("not-found",
                "404 is not a rename. It means no repository, no permission, no "
                "installation or a dead token, and separating those four is a "
                "different check.")

    if code != 200:
        return ("unknown",
                "%d is neither a redirect nor a readable repository." % code)

    if not full_name:
        return ("unknown",
                "the repository was returned without a full_name, so there is "
                "nothing to compare the configured name against.")

    if str(asked).strip() == str(full_name).strip():
        return ("current",
                "the configured name matches full_name and the request was "
                "answered without a redirect.")

    if same_repo(asked, full_name):
        return ("case-only",
                "the configured name differs from %s only in capitalisation. "
                "GitHub matches names case-insensitively, so this is the same "
                "repository and there is nothing to do." % full_name)

    return ("renamed-followed",
            "the request was answered as %s rather than as the name that was "
            "asked for, so a redirect was followed somewhere between here and "
            "GitHub and nobody was told." % full_name)


def durable_key(repo):
    """The identifiers that survive a rename. Pure. None when absent."""
    if not isinstance(repo, dict):
        return None
    key = {k: repo.get(k) for k in ("id", "node_id") if repo.get(k) is not None}
    return key or None


def extra_round_trips(calls):
    """Requests a followed redirect adds over a period. Pure.

    One per call: the redirect itself is a request, and it buys nothing except
    an address you could have written down once.
    """
    try:
        return max(0, int(calls))
    except (TypeError, ValueError):
        return 0


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "renamed-permanent":
        return ("update the stored owner/name to the value in the Location or "
                "in full_name, and key persistent state on the repository id or "
                "node_id, which survive the next rename too.")
    if state == "renamed-followed":
        return ("your client is following a redirect silently. Update the "
                "configured name to the full_name that came back, and key "
                "persistent state on id or node_id so the next rename is free.")
    if state == "moved-temporary":
        return ("follow it and change nothing. A temporary redirect is routing "
                "and does not belong in your configuration.")
    if state == "case-only":
        return ("nothing. The names differ only in capitalisation and GitHub "
                "matches them case-insensitively.")
    if state == "not-found":
        return ("triage the 404 rather than assuming a rename: check the token, "
                "the scopes and the installation before the name.")
    if state == "current":
        return "nothing."
    return "point the check at a repository this token can read."


def read_cost(repos):
    """Requests this run will spend against the core quota. Pure.

    An upper bound: one probe per repository, plus one more only where there is
    a redirect to follow.
    """
    return 2 * len(repos or [])


def probe(session, full_name):
    """One GET with redirects disabled. Returns (status, location)."""
    r = session.get(API + "/repos/" + full_name, allow_redirects=False, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    return r.status_code, r.headers.get("Location")


def resolve(session, url):
    """Follow one redirect and read the repository object. Returns dict or None."""
    r = session.get(url, timeout=30)
    if r.status_code != 200:
        return None
    try:
        body = r.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", required=True,
                    help="owner/name as your configuration has it. Repeatable.")
    ap.add_argument("--calls-per-hour", type=int, default=0,
                    help="how often your integration calls this repository, so "
                         "the cost of a followed redirect can be stated in "
                         "requests rather than in adjectives")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    log.info("read cost: at most %d request(s) per repository against the core "
             "hourly quota", 2)
    log.info("read cost: %d request(s) in total at most", read_cost(args.repo))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for name in args.repo:
        status, location = probe(session, name)
        repo = None
        if is_redirect(status) and location:
            log.info("%s: %d -> %s", name, status, location)
            repo = resolve(session, location)
        elif status == 200:
            repo = resolve(session, API + "/repos/" + name)

        full_name = (repo or {}).get("full_name")
        state, detail = verdict(name, status, location, full_name)
        log.info("%s: %s", state, detail)
        log.info("repair: %s", repair(state))
        if state in ("renamed-permanent", "renamed-followed") and args.calls_per_hour:
            log.info("a client that follows this pays 1 extra request per call: "
                     "%d calls an hour becomes %d", args.calls_per_hour,
                     args.calls_per_hour + extra_round_trips(args.calls_per_hour))

        findings.append({
            "configured": name,
            "status": status,
            "location": location,
            "location_points_at": repo_from_location(location),
            "full_name": full_name,
            "durable_key": durable_key(repo),
            "extra_requests_per_hour": (
                extra_round_trips(args.calls_per_hour)
                if state in ("renamed-permanent", "renamed-followed") else 0),
            "state": state,
            "detail": detail,
            "repair": repair(state),
        })

    print(json.dumps({"requests_spent_at_most": read_cost(args.repo),
                      "findings": findings}, indent=2, default=str))
    bad = {"renamed-permanent", "renamed-followed"}
    return 1 if any(f["state"] in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-repo-renamed.mjs",
"js": '''/**
 * Find repositories whose configured name is a redirect to somewhere else.
 *
 * Read only. At most two GETs per repository: one with redirects disabled, and
 * one to follow the redirect where there is one. Nothing is written and the
 * repair is printed rather than performed.
 *
 * Environment:
 *   GITHUB_TOKEN     a token with read access to the repository
 *   GITHUB_REPOS     comma-separated owner/name values as your config has them
 *   GITHUB_CALLS     calls an hour your integration makes, optional
 */
const API = 'https://api.github.com';
const UA = 'github-repo-renamed/1.0';

/** 301 and 308 say the address changed. 302 and 307 say the routing changed. */
export const PERMANENT = [301, 308];
export const TEMPORARY = [302, 307];

const LOC_ID = /\\/repositories\\/(\\d+)/;
const LOC_FULL = /\\/repos\\/([^/?#]+)\\/([^/?#]+)/;

/** A finite number, or null. Pure. Number(null) is 0, which would lie here. */
function toNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Whether this status moves you somewhere else. Pure. */
export function isRedirect(status) {
  const n = toNumber(status);
  return n !== null && (PERMANENT.includes(n) || TEMPORARY.includes(n));
}

/** Whether this status means update your code rather than follow it. Pure. */
export function isPermanent(status) {
  const n = toNumber(status);
  return n !== null && PERMANENT.includes(n);
}

/** What the Location header points at. Pure. Returns [kind, value] or null. */
export function repoFromLocation(location) {
  if (!location) return null;
  const text = String(location);
  const byId = LOC_ID.exec(text);
  if (byId) return ['id', byId[1]];
  const byName = LOC_FULL.exec(text);
  if (byName) return ['full_name', `${byName[1]}/${byName[2]}`];
  return null;
}

/** Whether two owner/name strings name the same repository. Pure. */
export function sameRepo(a, b) {
  if (!a || !b) return false;
  return String(a).trim().toLowerCase() === String(b).trim().toLowerCase();
}

/** Classify one probe of a configured repository name. Pure. */
export function verdict(asked, status, location = null, fullName = null) {
  const code = toNumber(status);
  if (code === null) return ['unknown', 'the probe produced no readable status.'];

  if (isPermanent(code)) {
    const target = repoFromLocation(location);
    if (!target) {
      return ['renamed-permanent',
        `${code} says the configured name is stale, but the response carried no `
        + 'usable Location, so the new name has to be read from the body after '
        + 'following it once.'];
    }
    const [kind, value] = target;
    const named = fullName ? `, now called ${fullName}` : '';
    if (kind === 'id') {
      return ['renamed-permanent',
        'the configured name is stale and GitHub is redirecting it permanently '
        + `to repository id ${value}${named}.`];
    }
    return ['renamed-permanent',
      'the configured name is stale and GitHub is redirecting it permanently to '
      + `${value}${named}.`];
  }

  if (isRedirect(code)) {
    return ['moved-temporary',
      `${code} is a temporary redirect, so follow it and change nothing. `
      + 'Writing this address into your configuration is the mistake here, not '
      + 'the fix.'];
  }

  if (code === 404) {
    return ['not-found',
      '404 is not a rename. It means no repository, no permission, no '
      + 'installation or a dead token, and separating those four is a different '
      + 'check.'];
  }

  if (code !== 200) {
    return ['unknown', `${code} is neither a redirect nor a readable repository.`];
  }

  if (!fullName) {
    return ['unknown',
      'the repository was returned without a full_name, so there is nothing to '
      + 'compare the configured name against.'];
  }

  if (String(asked).trim() === String(fullName).trim()) {
    return ['current',
      'the configured name matches full_name and the request was answered '
      + 'without a redirect.'];
  }

  if (sameRepo(asked, fullName)) {
    return ['case-only',
      `the configured name differs from ${fullName} only in capitalisation. `
      + 'GitHub matches names case-insensitively, so this is the same repository '
      + 'and there is nothing to do.'];
  }

  return ['renamed-followed',
    `the request was answered as ${fullName} rather than as the name that was `
    + 'asked for, so a redirect was followed somewhere between here and GitHub '
    + 'and nobody was told.'];
}

/** The identifiers that survive a rename. Pure. null when absent. */
export function durableKey(repo) {
  if (!repo || typeof repo !== 'object') return null;
  const key = {};
  for (const k of ['id', 'node_id']) {
    if (repo[k] !== undefined && repo[k] !== null) key[k] = repo[k];
  }
  return Object.keys(key).length ? key : null;
}

/** Requests a followed redirect adds over a period. Pure. */
export function extraRoundTrips(calls) {
  const n = toNumber(calls);
  if (n === null) return 0;
  return Math.max(0, Math.trunc(n));
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'renamed-permanent') {
    return 'update the stored owner/name to the value in the Location or in '
      + 'full_name, and key persistent state on the repository id or node_id, '
      + 'which survive the next rename too.';
  }
  if (state === 'renamed-followed') {
    return 'your client is following a redirect silently. Update the configured '
      + 'name to the full_name that came back, and key persistent state on id or '
      + 'node_id so the next rename is free.';
  }
  if (state === 'moved-temporary') {
    return 'follow it and change nothing. A temporary redirect is routing and '
      + 'does not belong in your configuration.';
  }
  if (state === 'case-only') {
    return 'nothing. The names differ only in capitalisation and GitHub matches '
      + 'them case-insensitively.';
  }
  if (state === 'not-found') {
    return 'triage the 404 rather than assuming a rename: check the token, the '
      + 'scopes and the installation before the name.';
  }
  if (state === 'current') return 'nothing.';
  return 'point the check at a repository this token can read.';
}

/** Requests this run will spend against the core quota, as an upper bound. Pure. */
export function readCost(repos) {
  return 2 * (Array.isArray(repos) ? repos.length : 0);
}

function headersFor(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repos = (process.env.GITHUB_REPOS || '').split(',').map((s) => s.trim()).filter(Boolean);
  if (!token || repos.length === 0) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPOS=owner/name');
    process.exitCode = 2;
    return;
  }
  const calls = Number(process.env.GITHUB_CALLS || 0);
  console.log(`read cost: at most ${readCost(repos)} request(s) against the core hourly quota`);

  const findings = [];
  for (const name of repos) {
    // Manual, because with following enabled the client swallows the 301 and
    // hands back a 200 from an address nobody looked at.
    const res = await fetch(`${API}/repos/${name}`, {
      headers: headersFor(token),
      redirect: 'manual',
    });
    const location = res.headers.get('location');
    let repo = null;
    if (isRedirect(res.status) && location) {
      console.log(`${name}: ${res.status} -> ${location}`);
      const followed = await fetch(location, { headers: headersFor(token) });
      if (followed.ok) { try { repo = await followed.json(); } catch { repo = null; } }
    } else if (res.status === 200) {
      try { repo = await res.json(); } catch { repo = null; }
    }

    const fullName = repo ? repo.full_name : null;
    const [state, detail] = verdict(name, res.status, location, fullName);
    console.log(`${state}: ${detail}`);
    console.log(`repair: ${repair(state)}`);
    if (['renamed-permanent', 'renamed-followed'].includes(state) && calls) {
      console.log(`a client that follows this pays 1 extra request per call: `
        + `${calls} calls an hour becomes ${calls + extraRoundTrips(calls)}`);
    }

    findings.push({
      configured: name,
      status: res.status,
      location,
      location_points_at: repoFromLocation(location),
      full_name: fullName,
      durable_key: durableKey(repo),
      extra_requests_per_hour: ['renamed-permanent', 'renamed-followed'].includes(state)
        ? extraRoundTrips(calls) : 0,
      state,
      detail,
      repair: repair(state),
    });
  }

  console.log(JSON.stringify({ requests_spent_at_most: readCost(repos), findings }, null, 2));
  const bad = ['renamed-permanent', 'renamed-followed'];
  process.exitCode = findings.some((f) => bad.includes(f.state)) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The states are the point, so the tests are mostly about keeping them apart: a permanent redirect and a temporary one must never produce the same repair, a difference of capitalisation must not be reported as a rename, and a 404 must be handed to the note that owns it rather than guessed at here. The Location parser gets its own attention because the header usually names an id rather than a name, and that id is the durable key the repair is really about. The read cost is asserted as the upper bound it claims to be.",
"test_py_file": "test_github_repo_renamed.py",
"test_py": '''from github_repo_renamed import (
    PERMANENT, TEMPORARY, durable_key, extra_round_trips, is_permanent,
    is_redirect, read_cost, repair, repo_from_location, same_repo, verdict,
)

BY_ID = "https://api.github.com/repositories/1300192"
BY_NAME = "https://api.github.com/repos/acme/core-api"


def test_permanent_and_temporary_redirects_are_kept_apart():
    assert is_redirect(301) and is_permanent(301)
    assert is_redirect(308) and is_permanent(308)
    assert is_redirect(302) and not is_permanent(302)
    assert is_redirect(307) and not is_permanent(307)
    assert not is_redirect(200)
    assert not is_redirect(None)
    assert set(PERMANENT).isdisjoint(TEMPORARY)


def test_the_location_usually_names_an_id_rather_than_a_name():
    assert repo_from_location(BY_ID) == ("id", "1300192")
    assert repo_from_location(BY_NAME) == ("full_name", "acme/core-api")
    assert repo_from_location("/repos/acme/core-api") == ("full_name", "acme/core-api")
    assert repo_from_location("https://example.test/nothing") is None
    assert repo_from_location(None) is None


def test_names_are_compared_the_way_github_compares_them():
    assert same_repo("Acme/Platform", "acme/platform")
    assert same_repo(" acme/platform ", "acme/platform")
    assert not same_repo("acme/platform", "acme/core-api")
    assert not same_repo(None, "acme/platform")


def test_a_permanent_redirect_is_the_finding_and_names_the_target():
    state, detail = verdict("acme/platform-api", 301, BY_ID, "acme/core-api")
    assert state == "renamed-permanent"
    assert "1300192" in detail
    assert "acme/core-api" in detail


def test_a_permanent_redirect_without_a_location_is_still_a_finding():
    state, detail = verdict("acme/platform-api", 301, None, None)
    assert state == "renamed-permanent"
    assert "no usable Location" in detail


def test_a_temporary_redirect_must_not_be_written_into_a_config():
    state, detail = verdict("acme/platform-api", 302, BY_NAME, None)
    assert state == "moved-temporary"
    assert "change nothing" in detail
    assert "change nothing" in repair(state)


def test_a_followed_redirect_is_caught_by_the_name_that_came_back():
    state, detail = verdict("acme/platform-api", 200, None, "acme/core-api")
    assert state == "renamed-followed"
    assert "nobody was told" in detail


def test_capitalisation_is_not_a_rename():
    state, detail = verdict("Acme/Platform", 200, None, "acme/platform")
    assert state == "case-only"
    assert "capitalisation" in detail
    assert repair(state).startswith("nothing.")


def test_a_matching_name_is_not_a_finding():
    assert verdict("acme/core-api", 200, None, "acme/core-api")[0] == "current"
    assert repair("current") == "nothing."


def test_a_404_is_handed_to_the_note_that_owns_it():
    state, detail = verdict("acme/gone", 404, None, None)
    assert state == "not-found"
    assert "not a rename" in detail
    assert "triage the 404" in repair(state)


def test_an_unreadable_probe_is_never_reported_as_a_rename():
    assert verdict("acme/x", None, None, None)[0] == "unknown"
    assert verdict("acme/x", 500, None, None)[0] == "unknown"
    assert verdict("acme/x", 200, None, None)[0] == "unknown"


def test_the_durable_key_is_what_the_repair_is_really_about():
    assert durable_key({"id": 1300192, "node_id": "R_kgDOE", "name": "core-api"}) == {
        "id": 1300192, "node_id": "R_kgDOE"}
    assert durable_key({"name": "core-api"}) is None
    assert durable_key(None) is None


def test_a_followed_redirect_doubles_the_requests_on_that_path():
    assert extra_round_trips(1200) == 1200
    assert extra_round_trips(0) == 0
    assert extra_round_trips(-5) == 0
    assert extra_round_trips(None) == 0


def test_the_two_rename_repairs_both_point_at_the_id():
    assert "node_id" in repair("renamed-permanent")
    assert "node_id" in repair("renamed-followed")
    assert "following a redirect silently" in repair("renamed-followed")


def test_the_cost_is_stated_as_the_upper_bound_it_is():
    assert read_cost(["a/b", "c/d"]) == 4
    assert read_cost(["a/b"]) == 2
    assert read_cost([]) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-repo-renamed.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PERMANENT, TEMPORARY, durableKey, extraRoundTrips, isPermanent, isRedirect,
  readCost, repair, repoFromLocation, sameRepo, verdict,
} from './github-repo-renamed.mjs';

const BY_ID = 'https://api.github.com/repositories/1300192';
const BY_NAME = 'https://api.github.com/repos/acme/core-api';

test('permanent and temporary redirects are kept apart', () => {
  assert.ok(isRedirect(301) && isPermanent(301));
  assert.ok(isRedirect(308) && isPermanent(308));
  assert.ok(isRedirect(302) && !isPermanent(302));
  assert.ok(isRedirect(307) && !isPermanent(307));
  assert.ok(!isRedirect(200));
  assert.ok(!isRedirect(null));
  assert.ok(!PERMANENT.some((c) => TEMPORARY.includes(c)));
});

test('the Location usually names an id rather than a name', () => {
  assert.deepEqual(repoFromLocation(BY_ID), ['id', '1300192']);
  assert.deepEqual(repoFromLocation(BY_NAME), ['full_name', 'acme/core-api']);
  assert.deepEqual(repoFromLocation('/repos/acme/core-api'), ['full_name', 'acme/core-api']);
  assert.equal(repoFromLocation('https://example.test/nothing'), null);
  assert.equal(repoFromLocation(null), null);
});

test('names are compared the way GitHub compares them', () => {
  assert.ok(sameRepo('Acme/Platform', 'acme/platform'));
  assert.ok(sameRepo(' acme/platform ', 'acme/platform'));
  assert.ok(!sameRepo('acme/platform', 'acme/core-api'));
  assert.ok(!sameRepo(null, 'acme/platform'));
});

test('a permanent redirect is the finding and names the target', () => {
  const [state, detail] = verdict('acme/platform-api', 301, BY_ID, 'acme/core-api');
  assert.equal(state, 'renamed-permanent');
  assert.match(detail, /1300192/);
  assert.match(detail, /acme\\/core-api/);
});

test('a permanent redirect without a Location is still a finding', () => {
  const [state, detail] = verdict('acme/platform-api', 301, null, null);
  assert.equal(state, 'renamed-permanent');
  assert.match(detail, /no usable Location/);
});

test('a temporary redirect must not be written into a config', () => {
  const [state, detail] = verdict('acme/platform-api', 302, BY_NAME, null);
  assert.equal(state, 'moved-temporary');
  assert.match(detail, /change nothing/);
  assert.match(repair(state), /change nothing/);
});

test('a followed redirect is caught by the name that came back', () => {
  const [state, detail] = verdict('acme/platform-api', 200, null, 'acme/core-api');
  assert.equal(state, 'renamed-followed');
  assert.match(detail, /nobody was told/);
});

test('capitalisation is not a rename', () => {
  const [state, detail] = verdict('Acme/Platform', 200, null, 'acme/platform');
  assert.equal(state, 'case-only');
  assert.match(detail, /capitalisation/);
  assert.ok(repair(state).startsWith('nothing.'));
});

test('a matching name is not a finding', () => {
  assert.equal(verdict('acme/core-api', 200, null, 'acme/core-api')[0], 'current');
  assert.equal(repair('current'), 'nothing.');
});

test('a 404 is handed to the note that owns it', () => {
  const [state, detail] = verdict('acme/gone', 404, null, null);
  assert.equal(state, 'not-found');
  assert.match(detail, /not a rename/);
  assert.match(repair(state), /triage the 404/);
});

test('an unreadable probe is never reported as a rename', () => {
  assert.equal(verdict('acme/x', null, null, null)[0], 'unknown');
  assert.equal(verdict('acme/x', 500, null, null)[0], 'unknown');
  assert.equal(verdict('acme/x', 200, null, null)[0], 'unknown');
});

test('the durable key is what the repair is really about', () => {
  assert.deepEqual(durableKey({ id: 1300192, node_id: 'R_kgDOE', name: 'core-api' }),
    { id: 1300192, node_id: 'R_kgDOE' });
  assert.equal(durableKey({ name: 'core-api' }), null);
  assert.equal(durableKey(null), null);
});

test('a followed redirect doubles the requests on that path', () => {
  assert.equal(extraRoundTrips(1200), 1200);
  assert.equal(extraRoundTrips(0), 0);
  assert.equal(extraRoundTrips(-5), 0);
  assert.equal(extraRoundTrips(null), 0);
});

test('the two rename repairs both point at the id', () => {
  assert.match(repair('renamed-permanent'), /node_id/);
  assert.match(repair('renamed-followed'), /node_id/);
  assert.match(repair('renamed-followed'), /following a redirect silently/);
});

test('the cost is stated as the upper bound it is', () => {
  assert.equal(readCost(['a/b', 'c/d']), 4);
  assert.equal(readCost(['a/b']), 2);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("Should I just follow the redirect and move on?",
  "You can, and your client probably already does, which is why nobody noticed. The cost is that every call to that repository takes two requests instead of one: one to be told where it went and one to go there. On a job making a thousand calls an hour that is a thousand requests an hour of your quota spent re-learning a fact you could have written down once. GitHub's own guidance is that a 301 means update your code, and it means it."),
 ("Why does the Location point at a number instead of the new name?",
  "Because the number is the repository's canonical identity and the name is a label somebody chose. The redirect resolves to https://api.github.com/repositories/{id}, which is stable across every rename and every transfer that will ever happen to that repository. That is a hint worth taking: update the name in the configuration a human reads, and key anything persistent on id or node_id so the next rename does not reach your code at all."),
 ("How is this different from getting a 404?",
  "A 404 on this API is deliberately ambiguous: no such repository, no permission, not in the installation, or a dead token, all with the same status and no way to tell them apart from the response alone. A 301 is the opposite, the most informative answer in this section, because it contains the address of what you asked for. If your probe returns 404 on a name you are sure about, stop reading this note and go and triage the 404 instead."),
 ("Does the redirect work for everything, not just reads?",
  "Not dependably, and that is what makes a stale name a latent problem rather than a permanent workaround. HTTP libraries treat redirects on non-read requests very differently: some refuse them, some drop the body, some quietly turn the request into a read. Every script in this section is read only so none of them can demonstrate it for you, but the day your integration stops only reading is the day the redirect stops being free."),
 ("What if the name only differs in capitalisation?",
  "Then nothing happened. GitHub matches repository names case-insensitively, so acme/Platform and acme/platform are one repository and neither name is stale. A comparison that does not fold case will report a rename that nobody performed, and somebody will go and edit a configuration that was already right. The check has a state for this specifically so a false alarm never reaches a reader."),
],
"related": [
 ("/github/404-masking-403/", "A permission error is disguised as 404"),
 ("/github/app-installation-id-hardcoded/", "The installation id is hard coded"),
 ("/github/no-conditional-requests/", "Every poll spends quota on unchanged data"),
],
"citations": [CITE_BEST_PRACTICES, CITE_REPOS, CITE_RENAME, CITE_TROUBLESHOOTING],
},

]
