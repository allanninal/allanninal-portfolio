#!/usr/bin/env python3
"""/github/ field notes, batch A — the writing.

Four ways the GitHub REST API hands you a short answer and calls it a complete
one. None of them errors, none of them is logged, and all four are arithmetic:
a header you did not read, a page size you did not set, a cap you did not know
about. Read-only throughout — a token with read access, GET requests only, and
the repair printed for a human to run.

The honest limit, stated in every one of these notes: the API cannot see your
client. It cannot tell whether you follow the `Link` header or stop at the first
page. What it can tell you is whether there is a second page there to be missed,
which is the trap rather than the fall.
"""

CITE_PAGINATION = ("Using pagination in the REST API — GitHub Docs",
                   "https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api")
CITE_BEST = ("Best practices for using the REST API — GitHub Docs",
             "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_RATE = ("Rate limits for the REST API — GitHub Docs",
             "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_RATE_EP = ("Rate limit — GitHub REST API",
                "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_SEARCH = ("Search — GitHub REST API",
               "https://docs.github.com/en/rest/search/search")
CITE_SEARCH_SYNTAX = ("Understanding the search syntax — GitHub Docs",
                      "https://docs.github.com/en/search-github/searching-on-github/understanding-the-search-syntax")
CITE_COMMITS = ("Commits — GitHub REST API",
                "https://docs.github.com/en/rest/commits/commits")
CITE_PULLS = ("Pull requests — GitHub REST API",
              "https://docs.github.com/en/rest/pulls/pulls")

REL_LINK = ("/github/link-header-not-followed/",
            "Only the first page of results is ever read")
REL_PER_PAGE = ("/github/per-page-default-30/",
                "per_page is unset so every list costs more requests")
REL_SEARCH = ("/github/search-1000-result-cap/",
              "Search returns at most 1,000 results")
REL_COMPARE = ("/github/compare-250-commit-cap/",
               "The compare endpoint stops at 250 commits")

GUIDES = [

{
"slug": "link-header-not-followed",
"title": "Only the first page is read because the Link header is ignored",
"description": "A repository with 340 open pull requests reports 30. The next page is advertised in the Link header, nothing errors, and page one is a truthful lie.",
"h1": "only the first page is read because the Link header is ignored",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api pagination", "github link header",
             "github api returns only 30 results", "github rest api next page",
             "octokit paginate"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The request returned <code>200</code>. The JSON is a well-formed array of pull requests. Your audit read it, counted 30, and reported that the repository is tidy. There are 340 open pull requests. Nothing failed, nothing was logged, and the number you are now acting on is wrong by an order of magnitude &mdash; the answer was complete for one page and the rest was advertised in a header nobody read.",
"short_answer": """<p>Call the list endpoint your integration uses with <code>per_page=1</code> and read the <code>Link</code> response header. It looks like <code>&lt;...&amp;page=2&gt;; rel="next", &lt;...&amp;page=340&gt;; rel="last"</code>, and at <code>per_page=1</code> the <code>page</code> number in <code>rel="last"</code> <em>is</em> the exact item count. Compare it against whatever your integration reports.</p>
<p>Where <code>rel="last"</code> is absent, follow <code>rel="next"</code> until it disappears. Terminating on a missing <code>rel="last"</code> is the same bug in a different costume.</p>""",
"problem": """<p>Every other failure in this section announces itself with a status code. This one returns 200 and valid JSON, and the JSON is not even wrong: the API was asked for a page and it returned that page, correctly. The mistake is entirely in the reading, which is why it survives code review, passes tests written against a fixture of five items, and ships.</p>
<p>It is also the failure that scales in the wrong direction. On a small repository the first page <em>is</em> the whole list, so the code appears to work for months. The bug activates on the thirty-first item, in whichever repository grows past it first, usually the busiest and most important one. A stale-branch report that says "no stale branches" for the monorepo is not reporting health; it is reporting that the monorepo has more than 30 branches.</p>""",
"why": """<p><strong>The size of the collection is in a header, not in the body.</strong> There is no <code>total_count</code> on REST list endpoints and no <code>has_more</code> flag. The only statement about completeness is the <code>Link</code> header, and a client that deserialises the body and discards the response object never sees it. Most convenience wrappers around <code>fetch</code> and <code>requests</code> return parsed JSON and throw the headers away by default.</p>
<p><strong>Thirty is a plausible number.</strong> If the default page were 3 items, someone would notice on day one. Thirty open pull requests, thirty branches, thirty workflow runs &mdash; every one of those is a number a human will accept without checking, which is what makes the default page size a trap rather than an inconvenience.</p>
<p><strong>Hand-built page URLs drift.</strong> Clients that do paginate often construct <code>?page=N</code> themselves rather than following the URL GitHub returned. That works until an endpoint moves to cursor-based paging, at which point the loop keeps returning page 1 forever, or terminates immediately, and again nothing errors.</p>
<p><strong>The API cannot see your client, so nothing on GitHub's side will ever complain.</strong> This is the honest limit of every check on this page. No endpoint reports whether you followed <code>rel="next"</code>; there is no server-side record of your parsing. What a read-only script <em>can</em> prove is that the trap is set: that this endpoint, for this repository, right now, has pages beyond the first and a true count that differs from 30. Whether your code walks them is a question for your code.</p>""",
"steps": [
 {"h": "Probe the endpoint with per_page=1",
  "body": """<p>One request, one item of transfer, and the <code>rel="last"</code> page number comes back as the exact size of the collection. This is the cheapest true count the REST API offers, and it costs one unit of the hourly 5,000.</p>"""},
 {"h": "Read the Link header, not the body",
  "body": """<p>Parse it by matching <code>&lt;url&gt;; rel="name"</code> rather than splitting on commas &mdash; pagination URLs can contain commas of their own (<code>labels=bug,ci</code> is the everyday case) and a naive <code>split(",")</code> produces two broken links out of one good one.</p>"""},
 {"h": "Compare the true count against what your integration reports",
  "body": """<p>If your dashboard says 30, 60 or 100 and the header says 340, you have found it. Round numbers that are exact multiples of a page size are the signature; a client that paginates correctly almost never lands on one.</p>"""},
 {"h": "Follow rel=\"next\" until it is absent",
  "body": """<p>That is the whole termination condition. Not a page count, not <code>rel="last"</code>, not an empty array &mdash; the absence of <code>rel="next"</code>. Use <code>octokit.paginate()</code>, PyGithub's <code>PaginatedList</code>, or <code>gh api --paginate</code>, all three of which implement exactly that.</p>"""},
 {"h": "Set per_page=100 while you are in there",
  "body": """<p>It costs nothing and cuts the request count by roughly 70%, but do it <em>after</em> the loop is correct. A non-paginating client with <code>per_page=100</code> is not fixed; it now reports 100 instead of 30, which is a larger and more convincing lie.</p>"""},
],
"verify": """<p>Re-run the script against the repository that was under-reporting. Every probed endpoint should either be a single page or be one you now walk in full.</p>
<pre><code class="language-bash">GITHUB_TOKEN=... python3 github_link_header_audit.py --repo octocat/hello-world
# 5 endpoint(s) probed, 2 with pages beyond the first; x-ratelimit-remaining 4993</code></pre>""",
"code_intro": "The script probes a handful of list endpoints at <code>per_page=1</code> and reads the header rather than the body &mdash; five GETs, no writes, a read-only token. The parsing and the judgement are two pure functions, because the interesting bugs here are in exactly those two places: a header split on the wrong character, and a loop that stops on the wrong condition.",
"py_file": "github_link_header_audit.py",
"py": '''"""Report GitHub list endpoints that advertise pages your client may not read.

Read only. GET requests and nothing else: a token with read access to the
repository is enough, and that is what you should give it. The repair is printed,
never performed.

What this can and cannot see: the API has no idea whether your client follows
rel="next". It can only say whether there is a next page there to be missed, and
how many items are on the far side of it. That is the trap, not the fall.
"""
import argparse
import logging
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_link_header_audit")

API = "https://api.github.com"

# Anchored on the angle brackets rather than split on ",". A pagination URL can
# contain a comma of its own -- labels=bug,ci is the everyday case -- and
# splitting the header on commas turns one good link into two broken ones.
LINK = re.compile(r\'<([^>]+)>\\s*;\\s*rel="([^"]+)"\')

PROBES = [
    ("pulls", {"state": "open"}),
    ("issues", {"state": "all"}),
    ("branches", {}),
    ("tags", {}),
    ("contributors", {}),
]


def parse_link(header):
    """Parse a Link header into {rel: url}. Pure, so it is tested offline."""
    if not header:
        return {}
    return {rel: url for url, rel in LINK.findall(header)}


def page_number(url):
    """Read the page query parameter out of a pagination URL, or None."""
    if not url:
        return None
    values = parse_qs(urlparse(url).query).get("page") or []
    try:
        return int(values[0])
    except (IndexError, TypeError, ValueError):
        return None


def verdict(links, received, per_page=1):
    """Classify what one list response says about its own completeness.

    Pure, so the rules are visible rather than buried in a request loop.
    Returns (state, detail).

    The states are deliberately three and not two. "more-pages-unsized" is the
    case where rel="next" exists and rel="last" does not: the list is still
    truncated, and a loop that terminates on the missing rel="last" is the same
    bug this note is about.
    """
    if "next" not in links:
        return ("single-page",
                '%d item(s) and no rel="next". One request really is the whole '
                "list here." % received)

    last = page_number(links.get("last"))
    if last is None:
        return ("more-pages-unsized",
                'rel="next" is present and rel="last" is not, so the total is only '
                "knowable by walking it. Terminate on the absence of "
                'rel="next", never on the absence of rel="last".')

    if per_page == 1:
        return ("more-pages",
                "%d item(s) in total. A client that reads the first page and stops "
                "reports %d." % (last, received))

    return ("more-pages",
            "%d page(s) at per_page=%d, so %d to %d item(s) in total. A client "
            "that reads the first page and stops reports %d."
            % (last, per_page, (last - 1) * per_page + 1, last * per_page, received))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed or "
                         "revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset time "
                         "and does not itself consume quota")
    if r.status_code == 404:
        raise SystemExit("404 on %s: the repository does not exist, or this token "
                         "cannot see it -- GitHub returns 404 rather than 403 for "
                         "resources you may not know about" % path)
    r.raise_for_status()
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--path", action="append",
                    help="probe this API path instead of the defaults, e.g. "
                         "/repos/o/n/releases. Repeatable.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": "github-link-header-audit",
    })

    if args.path:
        probes = [(p, {}) for p in args.path]
    else:
        probes = [("/repos/%s/%s" % (args.repo, name), extra)
                  for name, extra in PROBES]

    truncatable = 0
    remaining = "?"
    for path, extra in probes:
        # per_page=1 makes the rel="last" page number the exact item count, for
        # one request and one item of transfer.
        r = get(session, path, per_page=1, **extra)
        remaining = r.headers.get("x-ratelimit-remaining", "?")
        body = r.json()
        received = len(body) if isinstance(body, list) else 0
        state, detail = verdict(parse_link(r.headers.get("Link")), received, 1)

        line = "%-18s %s  %s" % (state, path, detail)
        if state == "single-page":
            log.info(line)
            continue
        truncatable += 1
        log.warning(line)
        log.warning('  repair: follow rel="next" until it is absent -- '
                    "octokit.paginate() in Octokit, the PaginatedList in PyGithub, "
                    "gh api --paginate on the command line. Never build page URLs "
                    "by hand.")

    log.info("%d endpoint(s) probed, %d with pages beyond the first; "
             "x-ratelimit-remaining %s", len(probes), truncatable, remaining)
    return 1 if truncatable else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-link-header-audit.mjs",
"js": '''/**
 * Report GitHub list endpoints that advertise pages your client may not read.
 *
 * Read only. GET requests and nothing else: a token with read access to the
 * repository is enough. The repair is printed, never performed.
 *
 * The API cannot see whether your client follows rel="next". It can only say
 * whether there is a next page there to be missed.
 */
const API = 'https://api.github.com';

// Anchored on the angle brackets rather than split on ','. A pagination URL can
// contain a comma of its own (labels=bug,ci) and splitting the header on commas
// turns one good link into two broken ones.
const LINK = /<([^>]+)>\\s*;\\s*rel="([^"]+)"/g;

const PROBES = [
  ['pulls', { state: 'open' }],
  ['issues', { state: 'all' }],
  ['branches', {}],
  ['tags', {}],
  ['contributors', {}],
];

/** Parse a Link header into a Map of rel to url. Pure, so it is tested offline. */
export function parseLink(header) {
  const out = new Map();
  if (!header) return out;
  for (const m of String(header).matchAll(LINK)) out.set(m[2], m[1]);
  return out;
}

/** Read the page query parameter out of a pagination URL, or null. */
export function pageNumber(url) {
  if (!url) return null;
  let value;
  try {
    value = new URL(url, API).searchParams.get('page');
  } catch {
    return null;
  }
  const n = Number(value);
  return value !== null && Number.isInteger(n) ? n : null;
}

/**
 * Classify what one list response says about its own completeness. Pure.
 * Returns [state, detail].
 *
 * Three states, not two: a rel="next" with no rel="last" is still a truncated
 * list, and a loop that stops there has the same bug in a different costume.
 */
export function verdict(links, received, perPage = 1) {
  if (!links.has('next')) {
    return ['single-page',
      `${received} item(s) and no rel="next". One request really is the whole ` +
      'list here.'];
  }

  const last = pageNumber(links.get('last'));
  if (last === null) {
    return ['more-pages-unsized',
      'rel="next" is present and rel="last" is not, so the total is only ' +
      'knowable by walking it. Terminate on the absence of rel="next", never ' +
      'on the absence of rel="last".'];
  }

  if (perPage === 1) {
    return ['more-pages',
      `${last} item(s) in total. A client that reads the first page and stops ` +
      `reports ${received}.`];
  }

  return ['more-pages',
    `${last} page(s) at per_page=${perPage}, so ${(last - 1) * perPage + 1} to ` +
    `${last * perPage} item(s) in total. A client that reads the first page and ` +
    `stops reports ${received}.`];
}

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i === -1 ? fallback : process.argv[i + 1];
}

async function get(token, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'github-link-header-audit',
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, malformed or revoked');
  }
  if (res.status === 403) {
    throw new Error('403 from GitHub. If this is a rate limit, GET /rate_limit ' +
                    'reports the reset and does not itself consume quota');
  }
  if (res.status === 404) {
    throw new Error(`404 on ${path}: the repository does not exist, or this token ` +
                    'cannot see it');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const repo = arg('repo');
  if (!repo) {
    console.error('usage: node github-link-header-audit.mjs --repo owner/name');
    process.exitCode = 2;
    return;
  }

  const probes = PROBES.map(([name, extra]) => [`/repos/${repo}/${name}`, extra]);

  let truncatable = 0;
  let remaining = '?';
  for (const [path, extra] of probes) {
    const res = await get(token, path, { per_page: 1, ...extra });
    remaining = res.headers.get('x-ratelimit-remaining') ?? '?';
    const body = await res.json();
    const received = Array.isArray(body) ? body.length : 0;
    const [state, detail] = verdict(parseLink(res.headers.get('link')), received, 1);

    const line = `${state.padEnd(18)} ${path}  ${detail}`;
    if (state === 'single-page') { console.log(line); continue; }
    truncatable += 1;
    console.warn(line);
    console.warn('  repair: follow rel="next" until it is absent -- ' +
                 'octokit.paginate() in Octokit, the PaginatedList in PyGithub, ' +
                 'gh api --paginate on the command line. Never build page URLs ' +
                 'by hand.');
  }

  console.log(`${probes.length} endpoint(s) probed, ${truncatable} with pages ` +
              `beyond the first; x-ratelimit-remaining ${remaining}`);
  process.exitCode = truncatable ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two rules are worth pinning. A <code>Link</code> header carrying a comma inside a URL must still parse into two links and not four, because that is a parser that looks correct on every repository until someone filters by two labels. And a <code>rel=\"next\"</code> with no <code>rel=\"last\"</code> must not collapse into either neighbour: it is not a complete list, and it is not a sized one either.",
"test_py_file": "test_github_link_header_audit.py",
"test_py": '''from github_link_header_audit import page_number, parse_link, verdict

FULL = ('<https://api.github.com/repositories/1/pulls?per_page=1&page=2>; rel="next", '
        '<https://api.github.com/repositories/1/pulls?per_page=1&page=340>; rel="last"')


def test_link_header_parses_both_relations():
    links = parse_link(FULL)
    assert set(links) == {"next", "last"}
    assert page_number(links["last"]) == 340


def test_a_comma_inside_a_url_does_not_become_a_second_link():
    # labels=bug,ci is ordinary. Splitting the header on "," makes four broken
    # entries out of two good ones and the walk then terminates on page one.
    header = ('<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=2>; rel="next", '
              '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=9>; rel="last"')
    links = parse_link(header)
    assert set(links) == {"next", "last"}
    assert links["next"].endswith("labels=bug,ci&page=2")


def test_no_link_header_is_a_single_page():
    state, detail = verdict(parse_link(None), 7, 1)
    assert state == "single-page"
    assert "7 item(s)" in detail


def test_rel_last_at_per_page_one_is_the_exact_count():
    state, detail = verdict(parse_link(FULL), 1, 1)
    assert state == "more-pages"
    assert "340 item(s)" in detail


def test_next_without_last_is_its_own_state():
    header = '<https://api.github.com/repos/o/n/branches?page=2>; rel="next"'
    state, detail = verdict(parse_link(header), 1, 1)
    assert state == "more-pages-unsized"
    assert 'rel="last"' in detail


def test_page_number_is_none_when_there_is_no_page_parameter():
    assert page_number("https://api.github.com/repos/o/n/pulls?per_page=100") is None
    assert page_number(None) is None
''',
"test_js_file": "github-link-header-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pageNumber, parseLink, verdict } from './github-link-header-audit.mjs';

const FULL =
  '<https://api.github.com/repositories/1/pulls?per_page=1&page=2>; rel="next", ' +
  '<https://api.github.com/repositories/1/pulls?per_page=1&page=340>; rel="last"';

test('link header parses both relations', () => {
  const links = parseLink(FULL);
  assert.deepEqual([...links.keys()].sort(), ['last', 'next']);
  assert.equal(pageNumber(links.get('last')), 340);
});

test('a comma inside a url does not become a second link', () => {
  const header =
    '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=2>; rel="next", ' +
    '<https://api.github.com/repos/o/n/issues?labels=bug,ci&page=9>; rel="last"';
  const links = parseLink(header);
  assert.deepEqual([...links.keys()].sort(), ['last', 'next']);
  assert.match(links.get('next'), /labels=bug,ci&page=2$/);
});

test('no link header is a single page', () => {
  const [state, detail] = verdict(parseLink(null), 7, 1);
  assert.equal(state, 'single-page');
  assert.match(detail, /7 item\\(s\\)/);
});

test('rel=last at per_page=1 is the exact count', () => {
  const [state, detail] = verdict(parseLink(FULL), 1, 1);
  assert.equal(state, 'more-pages');
  assert.match(detail, /340 item\\(s\\)/);
});

test('next without last is its own state', () => {
  const header = '<https://api.github.com/repos/o/n/branches?page=2>; rel="next"';
  const [state, detail] = verdict(parseLink(header), 1, 1);
  assert.equal(state, 'more-pages-unsized');
  assert.match(detail, /rel="last"/);
});

test('page number is null when there is no page parameter', () => {
  assert.equal(pageNumber('https://api.github.com/repos/o/n/pulls?per_page=100'), null);
  assert.equal(pageNumber(null), null);
});
''',
"faq": [
 ("How do I know the true number of items without reading every page?",
  "Request the endpoint with per_page=1 and read the page number in the Link header's rel=\"last\". At a page size of one, the last page number is the exact item count. It costs a single request, and it is the only cheap true count REST offers, since list endpoints carry no total_count field."),
 ("Why not just build the page URLs myself with ?page=2, ?page=3?",
  "Because the format is GitHub's to change, and some endpoints have already moved to cursor-based paging where a page number means nothing. Following the URL in rel=\"next\" is correct for both styles; constructing URLs is correct for one of them until it silently is not."),
 ("Is an empty array a safe signal to stop paginating?",
  "It works, but it costs one wasted request every time and it is wrong on endpoints that can return an empty page in the middle of a result set. The documented termination condition is the absence of rel=\"next\", which needs no extra call."),
 ("Can a script prove that my client is not following the Link header?",
  "No, and no script can. GitHub keeps no record of how you parsed a response, so nothing in the API reports client behaviour. What a read-only script proves is that the endpoint has pages beyond the first and what the real total is; the comparison against your dashboard's number is the part a human does."),
 ("Does setting per_page=100 fix this?",
  "No. It reduces the request count, which is worth doing, but a client that reads one page still reads one page. It will now confidently report 100 items instead of 30, which is a larger number and a more convincing one, so fix the loop first and the page size second."),
],
"related": [REL_PER_PAGE, REL_COMPARE, REL_SEARCH],
"citations": [CITE_PAGINATION, CITE_BEST, CITE_PULLS, CITE_RATE],
},

{
"slug": "per-page-default-30",
"title": "per_page is unset so every list costs 3.3x more requests",
"description": "Reading 3,000 issues takes 100 requests instead of 30 because nobody set per_page. The default is 30, the maximum is 100, and the difference is free.",
"h1": "per_page is unset so every list costs 3.3x more requests",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api per_page", "github api rate limit pagination",
             "github per_page 100", "github api too many requests",
             "github api default page size"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The job is correct. It follows <code>rel=\"next\"</code> to the end, it reads every issue, and it burns through the hourly quota by lunchtime. Nothing is broken and nothing needs debugging &mdash; it is simply making three and a third times as many requests as it needs to, because <code>per_page</code> was never set and the default is 30.",
"short_answer": """<p>Send <code>per_page=100</code> on every list request. The default is 30 and the maximum is 100, and a page of 100 costs exactly the same one request as a page of 30, so the change is free in every sense except the typing.</p>
<p>To measure it before you commit: read the <code>rel="last"</code> page number at the default page size and again at <code>per_page=100</code>. The difference between those two numbers is the requests per full pass you are currently spending on nothing.</p>""",
"problem": """<p>This is not a correctness bug, and that is exactly why it survives. The data is right. The loop terminates. Nobody opens a ticket for a job that produces the correct answer. It shows up much later, as a rate-limit incident with no obvious cause: an integration that used to finish at 09:20 now 403s at 09:14, because a repository grew and the request count grew with it at 3.3 times the rate it needed to.</p>
<p>The cost lands somewhere other than where the mistake was made, too. The <code>core</code> bucket is shared by every process using that token, and the API reports the drain but never says which process caused it. So a nightly export with an unset page size quietly steals headroom from an unrelated deployment bot on the same credential, and the bot is what gets paged.</p>""",
"why": """<p><strong>The default is a compatibility decision, not a recommendation.</strong> Thirty items per page has been the REST default for a very long time and cannot change without breaking clients that depend on the shape of a response. It is the value you get for not having an opinion, and there is no configuration anywhere that changes it for your token or your app.</p>
<p><strong>Requests are the billed unit, not items.</strong> The primary rate limit counts requests: 5,000 an hour for a user token, 1,000 an hour per repository for the Actions <code>GITHUB_TOKEN</code>. Bytes and items are free. Under that model a full page is straightforwardly better arithmetic, and a page of 30 is 70 items of headroom you paid for and threw away.</p>
<p><strong>Above 100 is clamped, not rejected.</strong> Asking for <code>per_page=500</code> does not error. The response quietly contains 100 items, so a loop built on the assumption that it received 500 will compute the wrong page count and, if it derives an offset from it, skip records outright.</p>
<p><strong>Quota is not the only cost.</strong> Each request is a round trip: TLS, latency, and a slice of the secondary limits that govern requests per minute against a single endpoint. Cutting the request count by 70% shortens wall-clock time by roughly the same proportion, which is often the thing that actually gets noticed.</p>""",
"steps": [
 {"h": "Get the true item count for the endpoints you read",
  "body": """<p>Request <code>per_page=100&amp;page=1</code>, read the <code>rel="last"</code> page number, then request that last page and count what is on it. Two requests give an exact total: <code>(last - 1) * 100 + len(last page)</code>. Where there is no <code>rel="last"</code>, page one is the whole list.</p>"""},
 {"h": "Do the arithmetic against your current page size",
  "body": """<p>Requests at 30 versus requests at 100, per full pass. For 3,412 issues that is 114 against 35: 79 requests of a 5,000-hour saved every time the job runs, and 79 fewer round trips of latency.</p>"""},
 {"h": "Set per_page=100 on every list call, including the nested ones",
  "body": """<p>The forgotten ones are the inner loops &mdash; comments per issue, reviews per pull request, workflow runs per workflow. Those are the calls that multiply, and they are usually written with defaults because each one individually looks tiny.</p>"""},
 {"h": "Do not ask for more than 100",
  "body": """<p><code>per_page=500</code> returns 100 items without complaint. If your code trusts the number it asked for rather than the length of the array it received, that is a silent data-loss bug rather than a wasted request.</p>"""},
 {"h": "Confirm the saving against the quota, which is free to read",
  "body": """<p><code>GET /rate_limit</code> returns <code>resources.core.used</code> and does not itself consume quota, so you can sample it immediately before and after a run and read the real cost rather than a projection.</p>"""},
],
"verify": """<p>Re-run with the page size your client actually sends. Every endpoint should report <code>at-maximum</code>.</p>
<pre><code class="language-bash">GITHUB_TOKEN=... python3 github_per_page_audit.py --repo octocat/hello-world --per-page 100
# 5 endpoint(s), 0 wasteful, 0 request(s) per pass recoverable</code></pre>""",
"code_intro": "The script counts each collection exactly &mdash; two GETs per endpoint, no writes &mdash; and then does arithmetic you can check by hand. The page-count function clamps at 100 the same way the API does, because a helper that cheerfully returns \"7 pages at per_page=500\" is a helper that hides the bug it was written to find.",
"py_file": "github_per_page_audit.py",
"py": '''"""Report how many requests an unset per_page is costing on each list endpoint.

Read only. GET requests and nothing else: a token with read access is enough.
The repair is printed, never performed.

This is a cost check, not a correctness one. Raising per_page does not make a
client that ignores the Link header correct; it makes it wrong by 100 instead
of by 30.
"""
import argparse
import logging
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_per_page_audit")

API = "https://api.github.com"
LINK = re.compile(r\'<([^>]+)>\\s*;\\s*rel="([^"]+)"\')

MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 30

PROBES = [
    ("issues", {"state": "all"}),
    ("pulls", {"state": "all"}),
    ("commits", {}),
    ("branches", {}),
    ("tags", {}),
]


def pages_for(items, per_page):
    """Requests needed to read `items` at `per_page`. Pure.

    Clamps to 100 the way the API does rather than the way the caller hoped:
    per_page above the maximum is silently reduced, not rejected, so pretending
    500 works here would hide exactly the mistake this script exists to find.
    """
    size = min(max(int(per_page or DEFAULT_PER_PAGE), 1), MAX_PER_PAGE)
    items = int(items or 0)
    if items <= 0:
        return 0
    return -(-items // size)


def verdict(items, per_page=DEFAULT_PER_PAGE):
    """Classify one endpoint's page-size arithmetic. Pure. Returns (state, detail)."""
    items = int(items or 0)
    if items <= 0:
        return ("empty", "no items; nothing to page and nothing to save")

    now = pages_for(items, per_page)
    best = pages_for(items, MAX_PER_PAGE)

    if now == best:
        if int(per_page or DEFAULT_PER_PAGE) > MAX_PER_PAGE:
            return ("at-maximum",
                    "%d item(s) in %d request(s). per_page=%s is above the maximum "
                    "and was clamped to 100, which costs nothing here but will "
                    "mislead any loop that trusts the number it asked for."
                    % (items, now, per_page))
        return ("at-maximum" if now > 1 else "single-page",
                "%d item(s) in %d request(s); per_page=100 would not improve on it."
                % (items, now))

    saved = now - best
    return ("wasteful",
            "%d item(s): %d request(s) at per_page=%d, %d at per_page=100. "
            "%d request(s) of quota and %d round trip(s) wasted on every full "
            "pass (%.0f%%)."
            % (items, now, int(per_page), best, saved, saved, 100.0 * saved / now))


def parse_link(header):
    if not header:
        return {}
    return {rel: url for url, rel in LINK.findall(header)}


def page_number(url):
    if not url:
        return None
    values = parse_qs(urlparse(url).query).get("page") or []
    try:
        return int(values[0])
    except (IndexError, TypeError, ValueError):
        return None


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed or "
                         "revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset time "
                         "and does not itself consume quota")
    r.raise_for_status()
    return r


def count_items(session, path, extra):
    """Exact item count in at most two requests.

    Page one at the maximum page size gives rel="last"; reading that last page
    gives the remainder. (last - 1) * 100 + len(last page) is the total, with no
    estimation anywhere in it.
    """
    first = get(session, path, per_page=MAX_PER_PAGE, **extra)
    body = first.json()
    if not isinstance(body, list):
        return None
    last = page_number(parse_link(first.headers.get("Link")).get("last"))
    if last is None or last <= 1:
        return len(body)
    tail = get(session, path, per_page=MAX_PER_PAGE, page=last, **extra).json()
    return (last - 1) * MAX_PER_PAGE + len(tail)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE,
                    help="the page size your client currently sends "
                         "(default 30, which is what an unset per_page means)")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-per-page-audit",
    })

    wasteful = 0
    recoverable = 0
    for name, extra in PROBES:
        path = "/repos/%s/%s" % (args.repo, name)
        items = count_items(session, path, extra)
        if items is None:
            log.info("%-12s %s  not a list endpoint, skipped", "skipped", path)
            continue
        state, detail = verdict(items, args.per_page)
        line = "%-12s %s  %s" % (state, path, detail)
        if state == "wasteful":
            wasteful += 1
            recoverable += pages_for(items, args.per_page) - pages_for(items, MAX_PER_PAGE)
            log.warning(line)
            log.warning("  repair: add per_page=100 to this request. It returns the "
                        "same data for the same one request per page.")
        else:
            log.info(line)

    log.info("%d endpoint(s), %d wasteful, %d request(s) per pass recoverable",
             len(PROBES), wasteful, recoverable)
    return 1 if wasteful else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-per-page-audit.mjs",
"js": '''/**
 * Report how many requests an unset per_page is costing on each list endpoint.
 *
 * Read only. GET requests and nothing else: a token with read access is enough.
 * The repair is printed, never performed.
 *
 * A cost check, not a correctness one. Raising per_page does not make a client
 * that ignores the Link header correct.
 */
const API = 'https://api.github.com';
const LINK = /<([^>]+)>\\s*;\\s*rel="([^"]+)"/g;

const MAX_PER_PAGE = 100;
const DEFAULT_PER_PAGE = 30;

const PROBES = [
  ['issues', { state: 'all' }],
  ['pulls', { state: 'all' }],
  ['commits', {}],
  ['branches', {}],
  ['tags', {}],
];

/**
 * Requests needed to read `items` at `perPage`. Pure. Clamps at 100 the way the
 * API does, because per_page above the maximum is reduced rather than rejected.
 */
export function pagesFor(items, perPage) {
  const size = Math.min(Math.max(Number(perPage) || DEFAULT_PER_PAGE, 1), MAX_PER_PAGE);
  const n = Number(items) || 0;
  return n <= 0 ? 0 : Math.ceil(n / size);
}

/** Classify one endpoint's page-size arithmetic. Pure. Returns [state, detail]. */
export function verdict(items, perPage = DEFAULT_PER_PAGE) {
  const n = Number(items) || 0;
  if (n <= 0) return ['empty', 'no items; nothing to page and nothing to save'];

  const now = pagesFor(n, perPage);
  const best = pagesFor(n, MAX_PER_PAGE);

  if (now === best) {
    if ((Number(perPage) || DEFAULT_PER_PAGE) > MAX_PER_PAGE) {
      return ['at-maximum',
        `${n} item(s) in ${now} request(s). per_page=${perPage} is above the ` +
        'maximum and was clamped to 100, which costs nothing here but will ' +
        'mislead any loop that trusts the number it asked for.'];
    }
    return [now > 1 ? 'at-maximum' : 'single-page',
      `${n} item(s) in ${now} request(s); per_page=100 would not improve on it.`];
  }

  const saved = now - best;
  const pct = Math.round((100 * saved) / now);
  return ['wasteful',
    `${n} item(s): ${now} request(s) at per_page=${perPage}, ${best} at ` +
    `per_page=100. ${saved} request(s) of quota and ${saved} round trip(s) ` +
    `wasted on every full pass (${pct}%).`];
}

function parseLink(header) {
  const out = new Map();
  if (!header) return out;
  for (const m of String(header).matchAll(LINK)) out.set(m[2], m[1]);
  return out;
}

function pageNumber(url) {
  if (!url) return null;
  const value = new URL(url, API).searchParams.get('page');
  const n = Number(value);
  return value !== null && Number.isInteger(n) ? n : null;
}

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i === -1 ? fallback : process.argv[i + 1];
}

async function get(token, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'github-per-page-audit',
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, malformed or revoked');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res;
}

async function countItems(token, path, extra) {
  const first = await get(token, path, { per_page: MAX_PER_PAGE, ...extra });
  const body = await first.json();
  if (!Array.isArray(body)) return null;
  const last = pageNumber(parseLink(first.headers.get('link')).get('last'));
  if (last === null || last <= 1) return body.length;
  const tail = await (await get(token, path,
    { per_page: MAX_PER_PAGE, page: last, ...extra })).json();
  return (last - 1) * MAX_PER_PAGE + tail.length;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = arg('repo');
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN and pass --repo owner/name');
    process.exitCode = 2;
    return;
  }
  const perPage = Number(arg('per-page', DEFAULT_PER_PAGE)) || DEFAULT_PER_PAGE;

  let wasteful = 0;
  let recoverable = 0;
  for (const [name, extra] of PROBES) {
    const path = `/repos/${repo}/${name}`;
    const items = await countItems(token, path, extra);
    if (items === null) {
      console.log(`skipped      ${path}  not a list endpoint, skipped`);
      continue;
    }
    const [state, detail] = verdict(items, perPage);
    const line = `${state.padEnd(12)} ${path}  ${detail}`;
    if (state === 'wasteful') {
      wasteful += 1;
      recoverable += pagesFor(items, perPage) - pagesFor(items, MAX_PER_PAGE);
      console.warn(line);
      console.warn('  repair: add per_page=100 to this request. It returns the ' +
                   'same data for the same one request per page.');
    } else {
      console.log(line);
    }
  }

  console.log(`${PROBES.length} endpoint(s), ${wasteful} wasteful, ` +
              `${recoverable} request(s) per pass recoverable`);
  process.exitCode = wasteful ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not run main(), fail on the missing token and fail the whole suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The arithmetic is the whole note, so the tests are arithmetic. The one that matters is <code>per_page=500</code>: it has to come back as 100 items per page, because a page-count helper that takes the caller at their word will report a saving that does not exist and, worse, agrees with a loop that skips records.",
"test_py_file": "test_github_per_page_audit.py",
"test_py": '''from github_per_page_audit import pages_for, verdict


def test_page_count_is_a_ceiling_not_a_division():
    assert pages_for(3000, 30) == 100
    assert pages_for(3000, 100) == 30
    assert pages_for(3001, 100) == 31
    assert pages_for(1, 100) == 1


def test_per_page_above_the_maximum_is_clamped_to_100():
    # The API reduces it silently rather than rejecting it, so the arithmetic
    # has to reduce it too or the saving reported here is fiction.
    assert pages_for(3000, 500) == 30
    state, detail = verdict(3000, 500)
    assert state == "at-maximum"
    assert "clamped" in detail


def test_the_default_page_size_is_the_finding():
    state, detail = verdict(3412, 30)
    assert state == "wasteful"
    assert "114 request(s) at per_page=30" in detail
    assert "35 at per_page=100" in detail
    assert "79 request(s)" in detail


def test_a_full_page_size_has_nothing_to_recover():
    assert verdict(3412, 100)[0] == "at-maximum"


def test_a_short_list_is_one_request_either_way():
    state, _ = verdict(12, 30)
    assert state == "single-page"


def test_an_empty_collection_is_not_reported_as_wasteful():
    assert verdict(0, 30)[0] == "empty"
    assert pages_for(0, 30) == 0
''',
"test_js_file": "github-per-page-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pagesFor, verdict } from './github-per-page-audit.mjs';

test('page count is a ceiling, not a division', () => {
  assert.equal(pagesFor(3000, 30), 100);
  assert.equal(pagesFor(3000, 100), 30);
  assert.equal(pagesFor(3001, 100), 31);
  assert.equal(pagesFor(1, 100), 1);
});

test('per_page above the maximum is clamped to 100', () => {
  assert.equal(pagesFor(3000, 500), 30);
  const [state, detail] = verdict(3000, 500);
  assert.equal(state, 'at-maximum');
  assert.match(detail, /clamped/);
});

test('the default page size is the finding', () => {
  const [state, detail] = verdict(3412, 30);
  assert.equal(state, 'wasteful');
  assert.match(detail, /114 request\\(s\\) at per_page=30/);
  assert.match(detail, /35 at per_page=100/);
  assert.match(detail, /79 request\\(s\\)/);
});

test('a full page size has nothing to recover', () => {
  assert.equal(verdict(3412, 100)[0], 'at-maximum');
});

test('a short list is one request either way', () => {
  assert.equal(verdict(12, 30)[0], 'single-page');
});

test('an empty collection is not reported as wasteful', () => {
  assert.equal(verdict(0, 30)[0], 'empty');
  assert.equal(pagesFor(0, 30), 0);
});
''',
"faq": [
 ("What is the actual default and maximum page size?",
  "Thirty items per page by default, one hundred at most, on the REST list endpoints that paginate. A few endpoints ignore per_page entirely, which you can see by asking for 100 and counting what comes back."),
 ("Does a bigger page cost more rate limit?",
  "No. The primary limit counts requests, not items or bytes, so a page of 100 and a page of 30 cost exactly one request each. That is what makes this free: you are buying 70 extra items for nothing."),
 ("What happens if I ask for per_page=500?",
  "You get 100 items and no error. That is worse than a rejection, because code that assumes it received 500 will compute the wrong number of pages, and code that derives an offset from the page size will skip four hundred records per page without a word."),
 ("How much can I really expect to save?",
  "Requests drop by a factor of 3.3 for the same data: 100 requests becomes 30. Wall-clock time falls by roughly the same proportion, since each removed request is a removed round trip. GET /rate_limit reports resources.core.used and does not consume quota, so you can measure the before and after exactly rather than estimating."),
 ("Should I set per_page before or after fixing my pagination loop?",
  "After. A client that reads one page and stops is wrong at 30 and equally wrong at 100, but at 100 it returns a bigger, more plausible number that is harder to spot. Get the loop right, then make it cheap."),
],
"related": [REL_LINK, REL_SEARCH, REL_COMPARE],
"citations": [CITE_PAGINATION, CITE_RATE, CITE_RATE_EP, CITE_BEST],
},

{
"slug": "search-1000-result-cap",
"title": "Search returns at most 1,000 results whatever total_count says",
"description": "total_count says 24,831 and page 11 returns 422 Validation Failed. The count is real; the results past the thousandth cannot be paged to at all.",
"h1": "search returns at most 1,000 results whatever total_count says",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github search api 1000 results", "github search only first 1000",
             "github api 422 validation failed search",
             "github search total_count", "github search api pagination limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The response says <code>\"total_count\": 24831</code>. You page through it at 100 per request, and on page 11 the API returns <code>422 Validation Failed</code> with <code>\"Only the first 1000 search results are available\"</code>. The count was true. The results were never there to fetch &mdash; <code>total_count</code> describes the match set, not the part of it you are allowed to page through.",
"short_answer": """<p>Read <code>total_count</code> from the first page of any <code>/search/*</code> response. Anything above 1,000 is a query whose tail you cannot reach at any page size: the Search API serves at most the first 1,000 results per query, and asking past that boundary returns <code>422</code> rather than an empty page.</p>
<p>The repair is to partition the query &mdash; by <code>created:</code> date ranges, by <code>repo:</code>, by label &mdash; until every slice reports under 1,000, then union the slices yourself. Where you want an inventory rather than a search, the equivalent list endpoint has no such cap.</p>""",
"problem": """<p>The dangerous version of this is not the 422. A crash is a gift; someone sees it and fixes it. The dangerous version is the code that pages until it gets a short page or an error, catches the error, logs a warning nobody reads, and reports 1,000 results as though that were the answer. The number is oddly round, and round numbers in a report are the thing to be suspicious of, but 1,000 issues is not obviously wrong to anyone reading a dashboard.</p>
<p>It is worse than plain truncation because <code>total_count</code> is sitting right there in the same response, correct and unreachable. Every consumer of that field &mdash; the progress bar, the "showing 1,000 of 24,831" label, the capacity plan &mdash; is being told the truth about a set it cannot enumerate. The gap between the two numbers is not an error state anywhere in the API; it is the normal, documented behaviour.</p>""",
"why": """<p><strong>The cap is per query, not per token or per hour.</strong> Waiting does not help, a bigger page size does not help, and a second token does not help. One thousand results is what a single query yields, so the only lever is making the query narrower.</p>
<p><strong>Paging past the boundary is an error, not an empty page.</strong> A client that expects pagination to end quietly with a short page instead receives <code>422 Validation Failed</code>. Generic retry logic then treats a permanent, arithmetic condition as a transient failure and retries it, which spends the search bucket without ever getting further.</p>
<p><strong>Search has its own small bucket.</strong> Search requests are not billed to <code>core</code>: authenticated search is limited per minute rather than per hour, so a partitioning strategy that fires dozens of narrow queries in a burst trades one limit for another. <code>GET /rate_limit</code> reports <code>resources.search</code> separately, and asking costs nothing.</p>
<p><strong>Sorting decides which thousand you get.</strong> Since only 1,000 results are reachable, the <code>sort</code> and <code>order</code> parameters stop being cosmetic and become the definition of your dataset. "The 1,000 most recently updated" is a defensible sample; "the first 1,000 in whatever order the index felt like" is not, and results can also shift between pages as items are updated underneath the walk.</p>""",
"steps": [
 {"h": "Read total_count with a one-item page",
  "body": """<p><code>GET /search/issues?q=...&amp;per_page=1</code> returns the full <code>total_count</code> for the cost of one search request and one item. You do not need to fetch anything to learn whether the query is over the cap.</p>"""},
 {"h": "Compare it against 1,000, not against your page count",
  "body": """<p>Above 1,000 means results exist that no amount of paging will return. Between about 900 and 1,000 is the state worth acting on <em>before</em> it breaks: a query that returns 950 today crosses the cap on its own as the repository grows, and nothing about that transition is announced.</p>"""},
 {"h": "Work out where the 422 starts",
  "body": """<p>Pages entirely inside the first 1,000 results are fine; the request that reaches across the boundary is the one that fails. At <code>per_page=100</code> that is page 11, at <code>per_page=30</code> it is page 34. Knowing the number turns a mystery 422 into an expected one.</p>"""},
 {"h": "Partition the query until every slice is under the cap",
  "body": """<p><code>created:2024-01-01..2024-03-31</code>, then the next quarter; or one query per <code>repo:</code>; or one per label. Each slice is an independent query with its own 1,000-result budget. Union them client-side and de-duplicate on the item id, because slices on non-disjoint fields overlap.</p>"""},
 {"h": "Ask whether you wanted search at all",
  "body": """<p>If the goal is "every issue in this repository", the list endpoint <code>GET /repos/{owner}/{repo}/issues</code> has no 1,000-result ceiling, is billed to the ordinary <code>core</code> quota rather than the small search bucket, and paginates conventionally. Search is for finding things; lists are for enumerating them.</p>"""},
],
"verify": """<p>Re-run against each partitioned query. Every slice should report <code>reachable</code>.</p>
<pre><code class="language-bash">GITHUB_TOKEN=... python3 github_search_cap_audit.py --query "repo:octocat/hello-world is:issue created:2024-01-01..2024-03-31"
# 1 quer(y/ies), 0 over the 1,000-result cap</code></pre>""",
"code_intro": "One search request per query, no writes, a read-only token. It also reads <code>GET /rate_limit</code> first to show the search bucket, which is a separate and much smaller allowance than <code>core</code> and costs nothing to inspect. The classifier is pure arithmetic over <code>total_count</code>, including the near-cap state that exists so the note arrives before the outage rather than after it.",
"py_file": "github_search_cap_audit.py",
"py": '''"""Report search queries whose results cannot be paged through in full.

Read only. GET requests and nothing else: a token with read access is enough.
The repair is printed, never performed.

The cap is a property of the query, so this is one of the few checks here that
gives a complete answer: total_count above 1,000 means results exist that no
client, correct or otherwise, can reach.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_search_cap_audit")

API = "https://api.github.com"

CAP = 1000
NEAR = 900
MAX_PER_PAGE = 100


def last_reachable_page(per_page=MAX_PER_PAGE):
    """The highest page number that lies entirely inside the 1,000-result cap.

    Pure. The request that straddles the boundary is the one that returns 422,
    so this is the page after which a walk stops working: 10 at per_page=100,
    33 at per_page=30.
    """
    size = min(max(int(per_page or 30), 1), MAX_PER_PAGE)
    return CAP // size


def reach(total_count, per_page=MAX_PER_PAGE):
    """Classify one query against the cap. Pure. Returns (state, detail)."""
    total = int(total_count or 0)
    last = last_reachable_page(per_page)

    if total <= 0:
        return ("no-matches", "no results; the query matches nothing")

    if total > CAP:
        slices = -(-total // CAP)
        return ("capped",
                "total_count is %d and only the first %d are reachable, so %d "
                "match(es) cannot be paged to at any page size. Page %d at "
                "per_page=%d is the last that works; the next one returns 422. "
                "Partition into at least %d narrower queries."
                % (total, CAP, total - CAP, last, per_page, slices))

    if total >= NEAR:
        return ("near-cap",
                "total_count is %d, inside the 1,000-result cap but close to it. "
                "This query starts losing results silently as soon as it grows "
                "past %d; partition it now rather than after."
                % (total, CAP))

    return ("reachable",
            "total_count is %d, all reachable in %d request(s) at per_page=%d."
            % (total, -(-total // min(max(int(per_page), 1), MAX_PER_PAGE)), per_page))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed or "
                         "revoked")
    if r.status_code == 403:
        raise SystemExit("403 from GitHub. Search has its own small per-minute "
                         "bucket; GET /rate_limit reports resources.search and "
                         "does not itself consume quota")
    if r.status_code == 422:
        raise SystemExit("422 from search: either the query is malformed or it "
                         "already reaches past the 1,000-result cap")
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", action="append", required=True,
                    help="a search query string. Repeatable, so a partitioned "
                         "query can be checked slice by slice.")
    ap.add_argument("--endpoint", default="issues",
                    choices=["issues", "repositories", "commits", "code", "users",
                             "labels", "topics"],
                    help="which /search/ endpoint to ask")
    ap.add_argument("--per-page", type=int, default=MAX_PER_PAGE,
                    help="the page size your client sends, used for the page "
                         "arithmetic")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-search-cap-audit",
    })

    # Free to ask: /rate_limit is not billed against any bucket, and search is
    # not billed against core, so this is the only cheap way to see the bucket
    # these queries will actually spend.
    quota = get(session, "/rate_limit").get("resources", {}).get("search", {})
    log.info("search bucket: %s of %s remaining, resets at %s",
             quota.get("remaining", "?"), quota.get("limit", "?"),
             quota.get("reset", "?"))

    over = 0
    for q in args.query:
        # per_page=1 is enough: total_count is on every page, and the first item
        # costs less to transfer than a hundred you are not going to read.
        body = get(session, "/search/%s" % args.endpoint, q=q, per_page=1)
        state, detail = reach(body.get("total_count"), args.per_page)
        line = "%-10s %s  %s" % (state, q, detail)
        if state in ("capped", "near-cap"):
            over += 1
            log.warning(line)
            log.warning("  repair: split this query by created: date ranges, by "
                        "repo:, or by label until every slice reports under "
                        "1,000, then union the slices and de-duplicate on id. "
                        "For a full inventory use the matching list endpoint "
                        "instead, which has no such cap.")
        else:
            log.info(line)

    log.info("%d quer(y/ies), %d over or near the %d-result cap",
             len(args.query), over, CAP)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-search-cap-audit.mjs",
"js": '''/**
 * Report search queries whose results cannot be paged through in full.
 *
 * Read only. GET requests and nothing else: a token with read access is enough.
 * The repair is printed, never performed.
 */
const API = 'https://api.github.com';

const CAP = 1000;
const NEAR = 900;
const MAX_PER_PAGE = 100;

/**
 * The highest page number that lies entirely inside the 1,000-result cap. Pure.
 * The request that straddles the boundary is the one that returns 422.
 */
export function lastReachablePage(perPage = MAX_PER_PAGE) {
  const size = Math.min(Math.max(Number(perPage) || 30, 1), MAX_PER_PAGE);
  return Math.floor(CAP / size);
}

/** Classify one query against the cap. Pure. Returns [state, detail]. */
export function reach(totalCount, perPage = MAX_PER_PAGE) {
  const total = Number(totalCount) || 0;
  const size = Math.min(Math.max(Number(perPage) || 30, 1), MAX_PER_PAGE);
  const last = lastReachablePage(perPage);

  if (total <= 0) return ['no-matches', 'no results; the query matches nothing'];

  if (total > CAP) {
    const slices = Math.ceil(total / CAP);
    return ['capped',
      `total_count is ${total} and only the first ${CAP} are reachable, so ` +
      `${total - CAP} match(es) cannot be paged to at any page size. Page ` +
      `${last} at per_page=${perPage} is the last that works; the next one ` +
      `returns 422. Partition into at least ${slices} narrower queries.`];
  }

  if (total >= NEAR) {
    return ['near-cap',
      `total_count is ${total}, inside the 1,000-result cap but close to it. ` +
      `This query starts losing results silently as soon as it grows past ` +
      `${CAP}; partition it now rather than after.`];
  }

  return ['reachable',
    `total_count is ${total}, all reachable in ${Math.ceil(total / size)} ` +
    `request(s) at per_page=${perPage}.`];
}

function args(name) {
  const out = [];
  process.argv.forEach((a, i) => { if (a === `--${name}`) out.push(process.argv[i + 1]); });
  return out;
}

async function get(token, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'github-search-cap-audit',
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, malformed or revoked');
  }
  if (res.status === 403) {
    throw new Error('403 from GitHub. Search has its own small per-minute bucket; ' +
                    'GET /rate_limit reports resources.search and does not itself ' +
                    'consume quota');
  }
  if (res.status === 422) {
    throw new Error('422 from search: the query is malformed, or it already ' +
                    'reaches past the 1,000-result cap');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const queries = args('query');
  if (!token || queries.length === 0) {
    console.error('set GITHUB_TOKEN and pass --query "..." at least once');
    process.exitCode = 2;
    return;
  }
  const endpoint = args('endpoint')[0] ?? 'issues';
  const perPage = Number(args('per-page')[0] ?? MAX_PER_PAGE) || MAX_PER_PAGE;

  // Free to ask: /rate_limit is not billed against any bucket, and search is not
  // billed against core.
  const quota = (await get(token, '/rate_limit')).resources?.search ?? {};
  console.log(`search bucket: ${quota.remaining ?? '?'} of ${quota.limit ?? '?'} ` +
              `remaining, resets at ${quota.reset ?? '?'}`);

  let over = 0;
  for (const q of queries) {
    const body = await get(token, `/search/${endpoint}`, { q, per_page: 1 });
    const [state, detail] = reach(body.total_count, perPage);
    const line = `${state.padEnd(10)} ${q}  ${detail}`;
    if (state === 'capped' || state === 'near-cap') {
      over += 1;
      console.warn(line);
      console.warn('  repair: split this query by created: date ranges, by repo:, ' +
                   'or by label until every slice reports under 1,000, then union ' +
                   'the slices and de-duplicate on id. For a full inventory use ' +
                   'the matching list endpoint instead, which has no such cap.');
    } else {
      console.log(line);
    }
  }

  console.log(`${queries.length} quer(y/ies), ${over} over or near the ${CAP}-result cap`);
  process.exitCode = over ? 1 : 0;
}

// Only run when invoked directly, so the test file can import the pure functions
// without main() running, failing on the missing token and failing the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The near-cap state is the one that earns its keep. A query returning 950 results is working perfectly today and will start losing results with no error and no deploy, so a classifier that only knows \"fine\" and \"broken\" reports this note one growth spurt too late. The page arithmetic is pinned too, because \"page 11 fails at per_page=100\" is the sentence that turns an unexplained 422 into an expected one.",
"test_py_file": "test_github_search_cap_audit.py",
"test_py": '''from github_search_cap_audit import last_reachable_page, reach


def test_a_small_query_is_fully_reachable():
    state, detail = reach(240, 100)
    assert state == "reachable"
    assert "3 request(s)" in detail


def test_a_query_over_the_cap_names_what_is_unreachable():
    state, detail = reach(24831, 100)
    assert state == "capped"
    assert "23831 match(es)" in detail
    assert "at least 25 narrower queries" in detail


def test_just_under_the_cap_is_a_warning_not_a_pass():
    # 950 works today and silently loses results the moment it passes 1,000.
    state, detail = reach(950, 100)
    assert state == "near-cap"
    assert "950" in detail


def test_no_matches_is_not_confused_with_a_capped_query():
    assert reach(0, 100)[0] == "no-matches"
    assert reach(None, 100)[0] == "no-matches"


def test_the_last_working_page_depends_on_the_page_size():
    assert last_reachable_page(100) == 10
    assert last_reachable_page(30) == 33
    assert last_reachable_page(1) == 1000


def test_page_size_above_the_maximum_is_clamped_before_the_arithmetic():
    assert last_reachable_page(500) == 10
''',
"test_js_file": "github-search-cap-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { lastReachablePage, reach } from './github-search-cap-audit.mjs';

test('a small query is fully reachable', () => {
  const [state, detail] = reach(240, 100);
  assert.equal(state, 'reachable');
  assert.match(detail, /3 request\\(s\\)/);
});

test('a query over the cap names what is unreachable', () => {
  const [state, detail] = reach(24831, 100);
  assert.equal(state, 'capped');
  assert.match(detail, /23831 match\\(es\\)/);
  assert.match(detail, /at least 25 narrower queries/);
});

test('just under the cap is a warning, not a pass', () => {
  const [state, detail] = reach(950, 100);
  assert.equal(state, 'near-cap');
  assert.match(detail, /950/);
});

test('no matches is not confused with a capped query', () => {
  assert.equal(reach(0, 100)[0], 'no-matches');
  assert.equal(reach(null, 100)[0], 'no-matches');
});

test('the last working page depends on the page size', () => {
  assert.equal(lastReachablePage(100), 10);
  assert.equal(lastReachablePage(30), 33);
  assert.equal(lastReachablePage(1), 1000);
});

test('page size above the maximum is clamped before the arithmetic', () => {
  assert.equal(lastReachablePage(500), 10);
});
''',
"faq": [
 ("Why does total_count report more results than I can fetch?",
  "Because it describes the match set and the pagination describes what is served. The Search API returns at most the first 1,000 results for a query; total_count is the honest size of the match, which makes the two numbers correct and incompatible at the same time."),
 ("Can a larger per_page get me past 1,000?",
  "No. The cap counts results, not pages. At per_page=100 you get ten usable pages, at per_page=30 you get thirty-three, and in both cases the eleventh hundred does not exist as far as the API is concerned."),
 ("Is the cap different in GraphQL?",
  "No. The same 1,000-result ceiling applies to search there, so migrating the query to GraphQL changes the cost model and the response shape but not this limit."),
 ("What is the right way to partition a query?",
  "Any qualifier that splits the match set into disjoint slices. created: date ranges are the most reliable, because every item has exactly one creation date; repo: and label slices work too but can overlap, so de-duplicate on the item id when you union them."),
 ("Should I be using search for this at all?",
  "Often not. If you want every issue or every pull request in a repository, the corresponding list endpoint has no 1,000-result cap, paginates conventionally with the Link header, and is billed to the ordinary hourly quota rather than to search's much smaller per-minute bucket."),
],
"related": [REL_LINK, REL_PER_PAGE, REL_COMPARE],
"citations": [CITE_SEARCH, CITE_SEARCH_SYNTAX, CITE_PAGINATION, CITE_RATE],
},

{
"slug": "compare-250-commit-cap",
"title": "The compare endpoint stops at 250 commits and says nothing",
"description": "A release-notes job diffs two tags and gets exactly 250 commits back. total_commits says 812. The response is a 200 with a truncated array and no flag.",
"h1": "the compare endpoint stops at 250 commits and says nothing",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github compare api 250 commits", "github compare two commits limit",
             "github api release notes missing commits",
             "github compare total_commits", "github api truncated commit list"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The release-notes generator diffs <code>v4.2.0...v4.3.0</code> and produces a changelog that looks entirely plausible. It has 250 entries. The release contains 812 commits, and the ones it dropped are not the boring ones at the end &mdash; the shape of what came back is not what the code assumed at all.",
"short_answer": """<p>Compare <code>total_commits</code> against <code>len(commits)</code> in the same response. <code>GET /repos/{owner}/{repo}/compare/{base}...{head}</code> returns at most 250 commits when called without pagination parameters, and says so nowhere except in that arithmetic.</p>
<p>Where <code>total_commits</code> exceeds what you received, paginate with <code>per_page</code> and <code>page</code> &mdash; noting that <code>files</code> comes back only on the first page &mdash; or switch to <code>GET /repos/{owner}/{repo}/commits</code>, which paginates conventionally through the <code>Link</code> header.</p>""",
"problem": """<p>A truncated changelog is a specific kind of bad. It is not empty, so no alarm fires; it is not obviously short, because nobody knows how many commits a release should have; and it is wrong in a way that only the author of a missing commit will notice, weeks later, when their fix is not in the notes and nobody can say whether it shipped.</p>
<p>There is a second, sharper problem underneath. In the unpaginated response the final element of <code>commits</code> is the most recent commit of the entire comparison rather than the 250th &mdash; the array is not a contiguous prefix. Any code that reasons about boundaries from the list, such as taking the first entry as the merge base or assuming <code>commits[i]</code> and <code>commits[i+1]</code> are adjacent in history, is drawing conclusions from a sequence with a hole in it.</p>""",
"why": """<p><strong>The cap applies to the unpaginated call specifically.</strong> Ask without <code>per_page</code> or <code>page</code> and you get up to 250 commits, whatever the comparison contains. There is no <code>truncated: true</code> field to check and no warning header; the only evidence is that <code>total_commits</code> is larger than the array you were handed.</p>
<p><strong>Pagination changes the semantics as well as the size.</strong> Once you page the endpoint, <code>files</code> is returned on the first page only, so a job that collects changed files from every page ends up with the file list of page one and nothing else. Code written for the unpaginated shape does not simply become slower when you add paging; it changes what it collects.</p>
<p><strong>250 is a plausible number for a real release.</strong> Unlike 30, which people learn to distrust, a 250-commit release is entirely believable for a busy repository. That is what lets this survive: the failure produces a defensible-looking artefact rather than an error.</p>
<p><strong>The comparison is against the merge base, which people forget.</strong> <code>base...head</code> compares <code>head</code> against the common ancestor, so <code>total_commits</code> is the count of commits on <code>head</code> that are not on <code>base</code>. A long-lived branch behind on <code>base</code> produces a much larger number than the diff a human has in mind, and pushes past 250 sooner than expected.</p>""",
"steps": [
 {"h": "Read total_commits before you read commits",
  "body": """<p>It is in every compare response and it is the true count. If it exceeds the number of items in <code>commits</code>, the list in your hands is a truncated list, whatever it looks like.</p>"""},
 {"h": "Treat exactly 250 as the signature",
  "body": """<p>A response with 250 commits and a larger <code>total_commits</code> is the unpaginated cap, precisely. It is not a coincidence and it is not a network problem; the next commit was never sent.</p>"""},
 {"h": "Do not read the last element as the oldest commit",
  "body": """<p>In the capped response the final entry is the head of the comparison, not the 250th commit from the base. Anything that walks the array as a contiguous history &mdash; computing a previous-release boundary, diffing adjacent pairs &mdash; is reading across a gap that is invisible in the JSON.</p>"""},
 {"h": "Paginate, and collect files from page one only",
  "body": """<p>Add <code>per_page=100</code> and walk pages until you have <code>total_commits</code> commits. Keep <code>files</code> from the first page and ignore the field afterwards; that is where it is, and re-reading it per page gives you nothing but confusion.</p>"""},
 {"h": "Or use the commits list instead",
  "body": """<p><code>GET /repos/{owner}/{repo}/commits?sha={head}&amp;since=...</code> paginates through the <code>Link</code> header like every other list endpoint and has no 250-item ceiling. It does not compute a merge base for you, which is the trade: you get complete data and you do the ancestry yourself.</p>"""},
],
"verify": """<p>Re-run against the same pair of refs. The script should report <code>complete</code>, or tell you precisely how many commits are missing from an unpaginated read.</p>
<pre><code class="language-bash">GITHUB_TOKEN=... python3 github_compare_truncation.py --repo octocat/hello-world --base v4.2.0 --head v4.3.0
# complete  v4.2.0...v4.3.0  18 commit(s), all present</code></pre>""",
"code_intro": "One GET against the compare endpoint, deliberately without pagination parameters, because the point is to see what an unpaginated client sees. The verdict is a pure function over the response so the four outcomes can be exercised offline: a comparison inside the cap, one truncated at exactly 250, a partial page from a paginated read, and a response with no <code>total_commits</code> at all, which must not be mistaken for a complete one.",
"py_file": "github_compare_truncation.py",
"py": '''"""Report whether a compare response was silently truncated at 250 commits.

Read only. One GET, no writes: a token with read access to the repository is
enough. The repair is printed, never performed.

The request is deliberately made without per_page or page, because that is the
call whose 250-commit cap is invisible, and reproducing it is the only way to
measure what an unpaginated client is missing.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_compare_truncation")

API = "https://api.github.com"

CAP = 250


def verdict(compare):
    """Classify one compare response. Pure. Returns (state, detail).

    `compare` is the parsed JSON: total_commits, commits and files.

    A missing total_commits is its own state rather than a default of zero.
    Defaulting it would report a truncated comparison as complete, which is the
    exact failure this script exists to catch.
    """
    total = compare.get("total_commits")
    if total is None:
        return ("unknown",
                "no total_commits in the response, so completeness cannot be "
                "judged. Do not treat this as complete.")

    total = int(total)
    commits = compare.get("commits") or []
    received = len(commits)
    files = len(compare.get("files") or [])

    if total == 0:
        return ("empty", "no commits between these refs; head is not ahead of base")

    if received >= total:
        return ("complete",
                "%d commit(s), all present%s."
                % (total, " (%d changed file(s))" % files if files else ""))

    if received == CAP:
        return ("capped",
                "total_commits is %d and %d came back: the unpaginated 250-commit "
                "cap, so %d commit(s) are missing. The last entry in this list is "
                "the head of the comparison, not the 250th commit from the base, "
                "so the array is not a contiguous history."
                % (total, received, total - received))

    return ("truncated",
            "total_commits is %d and %d came back, so %d commit(s) are missing. "
            "This is what a paginated read looks like mid-walk; keep paging until "
            "the counts agree." % (total, received, total - received))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed or "
                         "revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset time "
                         "and does not itself consume quota")
    if r.status_code == 404:
        raise SystemExit("404 on %s: check the repository and that both refs exist" % path)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--base", required=True, help="base ref, tag or sha")
    ap.add_argument("--head", required=True, help="head ref, tag or sha")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-compare-truncation",
    })

    # No per_page and no page on purpose: this is the call the cap applies to.
    path = "/repos/%s/compare/%s...%s" % (args.repo, args.base, args.head)
    body = get(session, path)
    state, detail = verdict(body)

    line = "%-10s %s...%s  %s" % (state, args.base, args.head, detail)
    if state in ("complete", "empty"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  repair: read total_commits first, then page this endpoint with "
                "per_page=100 and page=N until you have that many commits, keeping "
                "files from the first page only. Or read "
                "/repos/%s/commits?sha=%s, which paginates through the Link "
                "header and has no 250-commit ceiling.", args.repo, args.head)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-compare-truncation.mjs",
"js": '''/**
 * Report whether a compare response was silently truncated at 250 commits.
 *
 * Read only. One GET, no writes: a token with read access is enough. The repair
 * is printed, never performed.
 *
 * The request deliberately omits per_page and page, because that is the call the
 * 250-commit cap applies to.
 */
const API = 'https://api.github.com';

const CAP = 250;

/**
 * Classify one compare response. Pure. Returns [state, detail].
 *
 * A missing total_commits is its own state rather than a default of zero:
 * defaulting it would report a truncated comparison as complete.
 */
export function verdict(compare) {
  const raw = compare.total_commits;
  if (raw === undefined || raw === null) {
    return ['unknown',
      'no total_commits in the response, so completeness cannot be judged. Do ' +
      'not treat this as complete.'];
  }

  const total = Number(raw);
  const commits = compare.commits ?? [];
  const received = commits.length;
  const files = (compare.files ?? []).length;

  if (total === 0) {
    return ['empty', 'no commits between these refs; head is not ahead of base'];
  }

  if (received >= total) {
    return ['complete',
      `${total} commit(s), all present` +
      (files ? ` (${files} changed file(s))` : '') + '.'];
  }

  if (received === CAP) {
    return ['capped',
      `total_commits is ${total} and ${received} came back: the unpaginated ` +
      `250-commit cap, so ${total - received} commit(s) are missing. The last ` +
      'entry in this list is the head of the comparison, not the 250th commit ' +
      'from the base, so the array is not a contiguous history.'];
  }

  return ['truncated',
    `total_commits is ${total} and ${received} came back, so ${total - received} ` +
    'commit(s) are missing. This is what a paginated read looks like mid-walk; ' +
    'keep paging until the counts agree.'];
}

function arg(name) {
  const i = process.argv.indexOf(`--${name}`);
  return i === -1 ? undefined : process.argv[i + 1];
}

async function get(token, path) {
  const res = await fetch(API + path, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'github-compare-truncation',
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, malformed or revoked');
  }
  if (res.status === 403) {
    throw new Error('403 from GitHub. If this is a rate limit, GET /rate_limit ' +
                    'reports the reset and does not itself consume quota');
  }
  if (res.status === 404) {
    throw new Error(`404 on ${path}: check the repository and that both refs exist`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = arg('repo');
  const base = arg('base');
  const head = arg('head');
  if (!token || !repo || !base || !head) {
    console.error('set GITHUB_TOKEN and pass --repo owner/name --base X --head Y');
    process.exitCode = 2;
    return;
  }

  const path = `/repos/${repo}/compare/${base}...${head}`;
  const [state, detail] = verdict(await get(token, path));

  const line = `${state.padEnd(10)} ${base}...${head}  ${detail}`;
  if (state === 'complete' || state === 'empty') {
    console.log(line);
    return;
  }

  console.warn(line);
  console.warn('  repair: read total_commits first, then page this endpoint with ' +
               'per_page=100 and page=N until you have that many commits, keeping ' +
               'files from the first page only. Or read ' +
               `/repos/${repo}/commits?sha=${head}, which paginates through the ` +
               'Link header and has no 250-commit ceiling.');
  process.exitCode = 1;
}

// Only run when invoked directly, so the test file can import verdict without
// main() running and failing the suite on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Four responses, four different things to say about them. The one that would otherwise slip through is a response with no <code>total_commits</code> at all: the tempting default is zero, and a zero there turns \"I cannot tell\" into \"everything is present\", which is the failure this whole note is about, reproduced inside the checker meant to catch it.",
"test_py_file": "test_github_compare_truncation.py",
"test_py": '''from github_compare_truncation import verdict


def compare(total, received, files=0):
    return {"total_commits": total,
            "commits": [{"sha": "%040x" % i} for i in range(received)],
            "files": [{"filename": "f%d" % i} for i in range(files)]}


def test_a_small_comparison_is_complete():
    state, detail = verdict(compare(18, 18, files=42))
    assert state == "complete"
    assert "18 commit(s)" in detail
    assert "42 changed file(s)" in detail


def test_exactly_250_with_more_to_come_is_the_cap():
    state, detail = verdict(compare(812, 250))
    assert state == "capped"
    assert "562 commit(s) are missing" in detail
    # The sharp edge: the array is not a contiguous prefix of the history.
    assert "not the 250th commit" in detail


def test_a_partial_page_is_not_the_same_finding_as_the_cap():
    state, detail = verdict(compare(812, 100))
    assert state == "truncated"
    assert "712 commit(s) are missing" in detail


def test_no_commits_between_the_refs_is_not_a_failure():
    assert verdict(compare(0, 0))[0] == "empty"


def test_a_missing_total_commits_is_never_reported_as_complete():
    # Defaulting the count to zero here would call a truncated comparison
    # complete, which is precisely the bug being hunted.
    state, _ = verdict({"commits": [{"sha": "abc"}]})
    assert state == "unknown"
''',
"test_js_file": "github-compare-truncation.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './github-compare-truncation.mjs';

const compare = (total, received, files = 0) => ({
  total_commits: total,
  commits: Array.from({ length: received }, (_, i) => ({ sha: String(i) })),
  files: Array.from({ length: files }, (_, i) => ({ filename: `f${i}` })),
});

test('a small comparison is complete', () => {
  const [state, detail] = verdict(compare(18, 18, 42));
  assert.equal(state, 'complete');
  assert.match(detail, /18 commit\\(s\\)/);
  assert.match(detail, /42 changed file\\(s\\)/);
});

test('exactly 250 with more to come is the cap', () => {
  const [state, detail] = verdict(compare(812, 250));
  assert.equal(state, 'capped');
  assert.match(detail, /562 commit\\(s\\) are missing/);
  assert.match(detail, /not the 250th commit/);
});

test('a partial page is not the same finding as the cap', () => {
  const [state, detail] = verdict(compare(812, 100));
  assert.equal(state, 'truncated');
  assert.match(detail, /712 commit\\(s\\) are missing/);
});

test('no commits between the refs is not a failure', () => {
  assert.equal(verdict(compare(0, 0))[0], 'empty');
});

test('a missing total_commits is never reported as complete', () => {
  assert.equal(verdict({ commits: [{ sha: 'abc' }] })[0], 'unknown');
});
''',
"faq": [
 ("Where is the flag that says the commit list was truncated?",
  "There isn't one. The response is a 200 with a shorter array, and the only evidence is that total_commits is larger than the number of commits you received. That comparison is the check; nothing else in the response mentions it."),
 ("Why is 250 the number?",
  "It is the documented ceiling on the unpaginated compare response. Paginating the endpoint with per_page and page gets past it, at the cost of a different response shape."),
 ("What changes when I paginate the compare endpoint?",
  "The files array is returned on the first page only. Code that gathers changed files from every page silently ends up with page one's files, which for a large release is a small and misleading subset."),
 ("Is the truncated list the first 250 commits in order?",
  "Not exactly, and this is the part that catches people. The last entry in the capped list is the most recent commit of the whole comparison rather than the 250th, so the array is not a contiguous slice of history and adjacent entries are not necessarily adjacent commits."),
 ("What should a release-notes job use instead?",
  "Either page the compare endpoint properly, or read GET /repos/{owner}/{repo}/commits with a sha and a since, which paginates through the Link header and has no cap. The compare endpoint's advantage is that it computes the merge base for you; the commits list makes you do that yourself in exchange for complete data."),
],
"related": [REL_LINK, REL_PER_PAGE, REL_SEARCH],
"citations": [CITE_COMMITS, CITE_PAGINATION, CITE_BEST, CITE_RATE_EP],
},

]
