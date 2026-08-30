#!/usr/bin/env python3
"""/github/ field notes, batch F — the writing.

Four notes about spending less, which is a different subject from being
throttled. Nothing here is broken: every script in this batch runs against an
integration that is working, returning correct data, and costing several times
what it needs to.

They deliberately probe four different surfaces, because "use ETags" is one
sentence and these are not four restatements of it. The first reads the
per-resource table in GET /rate_limit and finds that code search is billed to
its own ten-a-minute bucket, so the cost of a scan is decided by its shape
rather than by its caching. The second takes a cache that already works and
shows it stops working the moment the credential changes, because an ETag is
scoped to the token that minted it. The third asks whether the polling loop
should exist at all, by reading the webhook inventory and costing the poll in
latency rather than in quota. The fourth reads a header almost nobody reads,
x-poll-interval, which is the server telling you the floor.

Read only throughout. Where the repair is a hook that has to be created, the
script prints the command and leaves it to you.
"""

CITE_BEST = ("Best practices for using the REST API — GitHub Docs",
             "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_REST_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_RATE_ENDPOINT = ("Rate limit — GitHub REST API",
                      "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_SEARCH = ("Search — GitHub REST API",
               "https://docs.github.com/en/rest/search/search")
CITE_SEARCH_SYNTAX = ("Searching code — GitHub Docs",
                      "https://docs.github.com/en/search-github/searching-on-github/searching-code")
CITE_APP_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_CONDITIONAL = ("Getting started with the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api")
CITE_WEBHOOKS = ("Repository webhooks — GitHub REST API",
                 "https://docs.github.com/en/rest/repos/webhooks")
CITE_WEBHOOK_EVENTS = ("Webhook events and payloads — GitHub Docs",
                       "https://docs.github.com/en/webhooks/webhook-events-and-payloads")
CITE_ABOUT_WEBHOOKS = ("About webhooks — GitHub Docs",
                       "https://docs.github.com/en/webhooks/about-webhooks")
CITE_EVENTS = ("Events — GitHub REST API",
               "https://docs.github.com/en/rest/activity/events")

GUIDES = [

{
"slug": "code-search-bucket-exhausted",
"title": "Code search is billed to its own 10 a minute bucket",
"description": "GET /search/code is metered by resources.code_search, not core and not search. Ten a minute is why a loop over repositories stops within seconds.",
"h1": "code search is billed to its own 10 a minute bucket",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github code search rate limit", "search/code 403 secondary rate limit",
             "github api code_search bucket", "github code search 10 per minute",
             "github search api rate limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The script walks the org, calling <code>GET /search/code</code> once per repository. It gets through nine of them. The tenth returns <code>403</code>, and <code>GET /rate_limit</code> says you have 4,987 requests left in the hour. Both statements are correct, because the request that was refused was never being counted in the bucket you just looked at.",
"short_answer": """<p>Code search has its own bucket. <code>GET /rate_limit</code> returns a <code>resources</code> table, and <code>resources.code_search</code> is a separate row from <code>resources.search</code> and from <code>resources.core</code> &mdash; roughly <strong>10 requests a minute</strong> against 30 a minute for other searches and 5,000 an hour for core. Every code-search response also names its bucket in <code>x-ratelimit-resource</code>, so there is no guessing about which allowance you spent.</p>
<p>The repair is not caching. It is the shape of the scan. One <code>org:</code>-qualified query, paged, covers what a loop of one query per repository covers, and it costs pages instead of repositories: 600 repositories collapse into ten pages. The script below costs both shapes against the bucket the API actually reports and tells you how many minutes each takes.</p>""",
"problem": """<p>What makes this one slow to work out is that the number everybody checks is the wrong number. A 403 sends you to <code>GET /rate_limit</code>, the response is 4,987 remaining, and that reading is accurate about the <em>core</em> bucket, which is not the bucket that stopped you. Nothing in the error says "you are looking at the wrong row".</p>
<p>It also survives the first fix. Adding a one-second sleep between repositories turns 10 a minute into 60 a minute, which is still six times the allowance, so the job now fails a little later and looks intermittent. Then someone adds ETags, which do nothing here, because the requests are not repeats: each one is a different query.</p>
<p>And it scales the wrong way. Iterating repositories means the cost of the scan is the number of repositories, so the tool that worked on the twelve-repo test org falls over on the day it is pointed at the real one. The output is worse than an error, too: a partial scan looks like a clean result with fewer hits.</p>""",
"why": """<p><strong>The buckets are separate on purpose.</strong> <code>GET /rate_limit</code> reports <code>core</code>, <code>search</code>, <code>code_search</code>, <code>graphql</code>, <code>integration_manifest</code> and more as independent rows with their own limit, remaining and reset. Code search is the tightest of them because it is the most expensive query GitHub answers, and it is the only one metered per minute rather than per hour at that size.</p>
<p><strong><code>x-ratelimit-resource</code> removes the ambiguity.</strong> Every response names the bucket it was charged to. If you are ever unsure whether a call went to <code>search</code> or <code>code_search</code>, read that header on the call itself rather than reasoning about the path.</p>
<p><strong>Code search refuses to work unauthenticated at all.</strong> Unlike most read endpoints, which fall back to 60 an hour for anonymous callers, code search requires authentication. A script that quietly lost its token does not get a smaller allowance here, it gets nothing.</p>
<p><strong>Per-repository iteration is the anti-pattern the qualifiers exist to prevent.</strong> <code>q=addClass+org:acme</code> is one query. <code>repo:acme/api</code> repeated 600 times is 600 queries for the same coverage, and it spends 600 units of a 10-a-minute allowance to do it.</p>
<p><strong>A single query still cannot return more than 1,000 results.</strong> Collapsing the loop does not remove that ceiling, it just moves the problem: past 1,000 matches you have to narrow by path, extension or date rather than page further. That is <a href="/github/search-1000-result-cap/">its own note</a>, and the costing below counts pages only up to the cap so it does not promise you results the API will not serve.</p>""",
"steps": [
 {"h": "Read the whole resources table, not just core",
  "body": """<p><code>GET /rate_limit</code> is free &mdash; it does not consume quota from any bucket &mdash; and it returns every row at once. Print <code>resources.code_search</code> next to <code>resources.search</code> and <code>resources.core</code> so the difference in scale is on the screen. If the row is missing entirely, you are on a deployment that does not report it, and the documented default applies.</p>"""},
 {"h": "Confirm the bucket on a live call with x-ratelimit-resource",
  "body": """<p>One <code>GET /search/code?q=...&amp;per_page=1</code> and read <code>x-ratelimit-resource</code> on the response. It will say <code>code_search</code>. This is the cheapest possible way to settle which allowance an endpoint spends, and it works for any endpoint you are unsure about.</p>"""},
 {"h": "Cost the scan you are actually running",
  "body": """<p>Requests equals repositories times queries per repository, and wall clock equals that divided by ten. Six hundred repositories with one query each is 600 requests and an hour of waiting even if nothing is refused. Put that number in front of whoever is asking why the scan is slow.</p>"""},
 {"h": "Collapse the loop into one qualified query and page it",
  "body": """<p>Replace <code>repo:</code> per repository with a single <code>org:acme</code> or <code>user:someone</code> query and follow the <code>Link</code> header. At <code>per_page=100</code> the whole reachable result set is at most ten requests, so the entire scan fits in one minute of the allowance rather than an hour of it.</p>"""},
 {"h": "For an exhaustive scan, stop using the search API",
  "body": """<p>If you genuinely need every occurrence in every file, the search index is the wrong tool: it is capped, ranked and rate limited. Shallow-clone the repositories and grep locally. The API is for finding where something is; the clone is for auditing everywhere it is.</p>"""},
],
"verify": """<p>Re-cost the scan after the loop is collapsed. The report should put the whole thing inside a single minute of the code-search allowance.</p>
<pre><code class="language-bash">python3 github_code_search_budget.py --repos 600 --queries 1 --results 800
# per-repo-scan: 600 request(s) is 60 minute(s) at 10 a minute; the same
# coverage as 1 qualified query is 8 request(s) and 1 minute(s)</code></pre>""",
"code_intro": "The only network call the script needs is <code>GET /rate_limit</code>, which spends nothing, and the optional probe is one search with <code>per_page=1</code>. Everything that produces a finding is arithmetic: a normaliser for the resources table that tells a missing row apart from an empty one, two costings, and a verdict. All four are pure, so the tests can hand them a bucket that is already exhausted instead of exhausting one.",
"py_file": "github_code_search_budget.py",
"py": '''"""Cost a code-search scan against the bucket code search is actually billed to.

Read only. Every request is a GET. GET /rate_limit consumes no quota from any
bucket, and the optional live probe is a single search with per_page=1.

Code search is metered by resources.code_search, which is roughly 10 requests a
minute. That is a different row from resources.search and a different row again
from resources.core, and reading the wrong row is most of why this failure takes
an afternoon.
"""
import argparse
import json
import logging
import math
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_code_search_budget")

API = "https://api.github.com"
UA = "github-code-search-budget/1.0"

# Documented defaults, used only to fill in a row GET /rate_limit did not return.
DEFAULTS = {"code_search": 10, "search": 30, "core": 5000}

# A single search query cannot return more than this many results however many
# pages are requested, and 100 is the largest page the API will serve.
RESULT_CAP = 1000
MAX_PAGE = 100


def buckets(payload):
    """Normalise the resources table from GET /rate_limit. Pure.

    Returns {name: {"limit", "remaining", "reset", "present"}}. A row the
    deployment does not report comes back with present False and the documented
    default, because "the field is missing" and "the allowance is zero" are
    different findings and only one of them is a problem you can wait out.
    """
    resources = ((payload or {}).get("resources") or {})
    out = {}
    for name, default in DEFAULTS.items():
        raw = resources.get(name)
        if not isinstance(raw, dict):
            out[name] = {"limit": default, "remaining": None,
                         "reset": None, "present": False}
            continue
        parsed = {}
        for key in ("limit", "remaining", "reset"):
            try:
                parsed[key] = int(raw.get(key))
            except (TypeError, ValueError):
                parsed[key] = None
        out[name] = {"limit": default if parsed["limit"] is None else parsed["limit"],
                     "remaining": parsed["remaining"],
                     "reset": parsed["reset"],
                     "present": True}
    return out


def scan_cost(repos, queries_per_repo, per_minute):
    """Requests and wall-clock minutes for a scan that iterates repositories. Pure.

    The number that surprises people is minutes, not requests: at ten a minute a
    six hundred repository loop is an hour of waiting even when nothing is
    refused.
    """
    try:
        repos = max(0, int(repos))
        queries_per_repo = max(0, int(queries_per_repo))
    except (TypeError, ValueError):
        return {"requests": 0, "minutes": 0}
    per_minute = max(1, int(per_minute or 1))
    needed = repos * queries_per_repo
    return {"requests": needed,
            "minutes": math.ceil(needed / per_minute) if needed else 0}


def collapsed_cost(queries, results_per_query, per_minute,
                   page_size=MAX_PAGE, cap=RESULT_CAP):
    """Cost of the same coverage as one qualified query per concern, paged. Pure.

    Capped at `cap` because a single query cannot return more than that many
    results, so counting pages past it would promise results the API will not
    serve. `truncated` says so out loud rather than quietly under-reporting.
    """
    try:
        queries = max(0, int(queries))
        results = max(0, int(results_per_query))
    except (TypeError, ValueError):
        return {"requests": 0, "pages_per_query": 0, "minutes": 0, "truncated": False}
    page_size = max(1, min(int(page_size or MAX_PAGE), MAX_PAGE))
    reachable = min(results, cap)
    # A query with no results still costs the one request that discovers that.
    per_query = math.ceil(reachable / page_size) if reachable else 1
    needed = queries * per_query
    per_minute = max(1, int(per_minute or 1))
    return {"requests": needed, "pages_per_query": per_query,
            "minutes": math.ceil(needed / per_minute) if needed else 0,
            "truncated": results > cap}


def seconds_until(reset, now):
    """Seconds until a bucket resets, floored at zero. Pure.

    None rather than 0 when the value is unreadable: "resets right now" and "I
    could not read the reset" should not print the same.
    """
    try:
        return max(0, int(reset) - int(now))
    except (TypeError, ValueError):
        return None


def verdict(bucket, iterating, collapsed):
    """Turn the bucket state and the two costings into a finding. Pure."""
    limit = bucket.get("limit") or DEFAULTS["code_search"]
    remaining = bucket.get("remaining")
    note = "" if bucket.get("present") else (
        " (GET /rate_limit did not report a code_search row, so this uses the "
        "documented default of %d a minute)" % limit)

    if remaining == 0:
        return ("exhausted",
                "the code_search bucket is empty. This is not the core quota, "
                "which is why it can read as thousands remaining at the same "
                "time. It refills on its own minute-long clock.%s" % note)
    if not iterating.get("requests"):
        return ("no-scan", "no scan described, so nothing to cost%s" % note)

    ratio = iterating["requests"] / max(1, collapsed.get("requests") or 1)
    if ratio >= 4:
        return ("per-repo-scan",
                "%d request(s) is %d minute(s) at %d a minute; the same coverage "
                "as %d qualified quer(y/ies) is %d request(s) and %d minute(s). "
                "The loop is the cost, not the caching.%s"
                % (iterating["requests"], iterating["minutes"], limit,
                   max(1, collapsed.get("requests", 0) // max(1, collapsed.get("pages_per_query", 1))),
                   collapsed.get("requests", 0), collapsed.get("minutes", 0), note))
    if iterating["minutes"] > 1:
        return ("over-budget",
                "%d request(s) at %d a minute is %d minute(s) of wall clock even "
                "if nothing is refused.%s"
                % (iterating["requests"], limit, iterating["minutes"], note))
    return ("clear",
            "%d request(s) fits inside one minute of a %d a minute allowance.%s"
            % (iterating["requests"], limit, note))


def get(session, path, **kwargs):
    """One GET. Returns (status, json-or-None, headers)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30, **kwargs)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body, dict(r.headers)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", type=int, default=0,
                    help="repositories the current scan iterates over")
    ap.add_argument("--queries", type=int, default=1,
                    help="code-search queries issued per repository")
    ap.add_argument("--results", type=int, default=200,
                    help="results you expect one qualified query to match")
    ap.add_argument("--probe-query",
                    help="optional q= value; issues one search with per_page=1 "
                         "to read x-ratelimit-resource on a live response")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN. Code search refuses unauthenticated "
                  "callers outright, so there is no anonymous fallback here")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, payload, _ = get(session, "/rate_limit")
    if status != 200:
        log.error("GET /rate_limit returned %d; cannot read the buckets", status)
        return 2

    table = buckets(payload)
    for name in ("core", "search", "code_search"):
        row = table[name]
        wait = seconds_until(row["reset"], time.time())
        log.info("%-12s limit %-5s remaining %-5s reset in %s",
                 name, row["limit"],
                 "?" if row["remaining"] is None else row["remaining"],
                 "unknown" if wait is None else "%ds" % wait)
        if not row["present"]:
            log.warning("  %s was not in the resources table; showing the "
                        "documented default", name)

    if args.probe_query:
        status, _, headers = get(session, "/search/code",
                                 params={"q": args.probe_query, "per_page": 1})
        lowered = {k.lower(): v for k, v in headers.items()}
        log.info("probe: /search/code returned %d, billed to %s",
                 status, lowered.get("x-ratelimit-resource", "an unnamed bucket"))
        if status == 403:
            log.warning("  a 403 here with core headroom left is this bucket, "
                        "not the hourly quota and not your token scopes")

    code = table["code_search"]
    iterating = scan_cost(args.repos, args.queries, code["limit"])
    collapsed = collapsed_cost(max(1, args.queries), args.results, code["limit"])
    state, detail = verdict(code, iterating, collapsed)
    log.info("%s: %s", state, detail)

    if collapsed["truncated"]:
        log.warning("one query cannot return more than %d results, so the "
                    "collapsed costing counts %d page(s) and stops. Narrow by "
                    "path, extension or date rather than paging further.",
                    RESULT_CAP, collapsed["pages_per_query"])

    if state in ("per-repo-scan", "over-budget", "exhausted"):
        log.info("repair: one qualified query instead of one per repository, "
                 "for example q=YOURTERM+org:YOURORG with per_page=100, and "
                 "follow the Link header.")
        log.info("repair: for an exhaustive audit, shallow-clone and grep "
                 "locally. The search index is capped, ranked and metered; a "
                 "clone is none of those.")

    print(json.dumps({"buckets": table, "iterating": iterating,
                      "collapsed": collapsed, "state": state}, indent=2))
    return 1 if state in ("per-repo-scan", "over-budget", "exhausted") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-code-search-budget.mjs",
"js": '''/**
 * Cost a code-search scan against the bucket code search is actually billed to.
 *
 * Read only. Every request is a GET. GET /rate_limit consumes no quota, and the
 * optional live probe is a single search with per_page=1.
 *
 * Code search is metered by resources.code_search, roughly 10 a minute. That is
 * a different row from resources.search and from resources.core.
 */
const API = 'https://api.github.com';
const UA = 'github-code-search-budget/1.0';

// Documented defaults, used only to fill in a row GET /rate_limit did not return.
export const DEFAULTS = { code_search: 10, search: 30, core: 5000 };

// A single query cannot return more than this many results, and 100 is the
// largest page the API will serve.
export const RESULT_CAP = 1000;
export const MAX_PAGE = 100;

/**
 * Normalise the resources table from GET /rate_limit. Pure.
 * A missing row comes back with present false and the documented default:
 * "the field is missing" and "the allowance is zero" are different findings.
 */
export function buckets(payload) {
  const resources = (payload ?? {}).resources ?? {};
  const out = {};
  for (const [name, fallback] of Object.entries(DEFAULTS)) {
    const raw = resources[name];
    if (!raw || typeof raw !== 'object') {
      out[name] = { limit: fallback, remaining: null, reset: null, present: false };
      continue;
    }
    const num = (key) => {
      const n = Number.parseInt(raw[key], 10);
      return Number.isFinite(n) ? n : null;
    };
    const limit = num('limit');
    out[name] = {
      limit: limit === null ? fallback : limit,
      remaining: num('remaining'),
      reset: num('reset'),
      present: true,
    };
  }
  return out;
}

/** Requests and wall-clock minutes for a scan that iterates repositories. Pure. */
export function scanCost(repos, queriesPerRepo, perMinute) {
  const r = Math.max(0, Number.parseInt(repos, 10) || 0);
  const q = Math.max(0, Number.parseInt(queriesPerRepo, 10) || 0);
  const rate = Math.max(1, Number.parseInt(perMinute, 10) || 1);
  const needed = r * q;
  return { requests: needed, minutes: needed ? Math.ceil(needed / rate) : 0 };
}

/**
 * Cost of the same coverage as one qualified query per concern, paged. Pure.
 * Capped at RESULT_CAP, because counting pages past it would promise results
 * the API will not serve.
 */
export function collapsedCost(queries, resultsPerQuery, perMinute,
                              pageSize = MAX_PAGE, cap = RESULT_CAP) {
  const q = Math.max(0, Number.parseInt(queries, 10) || 0);
  const results = Math.max(0, Number.parseInt(resultsPerQuery, 10) || 0);
  const size = Math.max(1, Math.min(Number.parseInt(pageSize, 10) || MAX_PAGE, MAX_PAGE));
  const reachable = Math.min(results, cap);
  // A query with no results still costs the one request that discovers that.
  const perQuery = reachable ? Math.ceil(reachable / size) : 1;
  const needed = q * perQuery;
  const rate = Math.max(1, Number.parseInt(perMinute, 10) || 1);
  return {
    requests: needed,
    pages_per_query: perQuery,
    minutes: needed ? Math.ceil(needed / rate) : 0,
    truncated: results > cap,
  };
}

/** Seconds until a bucket resets, floored at zero; null when unreadable. Pure. */
export function secondsUntil(reset, now) {
  const r = Number.parseInt(reset, 10);
  const n = Number.parseInt(now, 10);
  if (!Number.isFinite(r) || !Number.isFinite(n)) return null;
  return Math.max(0, r - n);
}

/** Turn the bucket state and the two costings into a finding. Pure. */
export function verdict(bucket, iterating, collapsed) {
  const limit = bucket.limit || DEFAULTS.code_search;
  const note = bucket.present ? '' :
    ` (GET /rate_limit did not report a code_search row, so this uses the ` +
    `documented default of ${limit} a minute)`;

  if (bucket.remaining === 0) {
    return ['exhausted',
      'the code_search bucket is empty. This is not the core quota, which is ' +
      'why it can read as thousands remaining at the same time. It refills on ' +
      `its own minute-long clock.${note}`];
  }
  if (!iterating.requests) return ['no-scan', `no scan described, so nothing to cost${note}`];

  const ratio = iterating.requests / Math.max(1, collapsed.requests || 1);
  if (ratio >= 4) {
    const queries = Math.max(1, Math.floor((collapsed.requests || 0) /
      Math.max(1, collapsed.pages_per_query || 1)));
    return ['per-repo-scan',
      `${iterating.requests} request(s) is ${iterating.minutes} minute(s) at ` +
      `${limit} a minute; the same coverage as ${queries} qualified quer(y/ies) ` +
      `is ${collapsed.requests} request(s) and ${collapsed.minutes} minute(s). ` +
      `The loop is the cost, not the caching.${note}`];
  }
  if (iterating.minutes > 1) {
    return ['over-budget',
      `${iterating.requests} request(s) at ${limit} a minute is ` +
      `${iterating.minutes} minute(s) of wall clock even if nothing is refused.${note}`];
  }
  return ['clear',
    `${iterating.requests} request(s) fits inside one minute of a ${limit} a ` +
    `minute allowance.${note}`];
}

async function get(token, path, params) {
  const url = new URL(path.startsWith('/') ? API + path : path);
  for (const [k, v] of Object.entries(params ?? {})) url.searchParams.set(k, v);
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  const headers = {};
  for (const [k, v] of res.headers.entries()) headers[k.toLowerCase()] = v;
  return { status: res.status, body, headers };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN. Code search refuses unauthenticated ' +
      'callers outright, so there is no anonymous fallback here');
    process.exitCode = 2;
    return;
  }
  const repos = Number.parseInt(process.argv[2] ?? '0', 10) || 0;
  const queries = Number.parseInt(process.argv[3] ?? '1', 10) || 1;
  const results = Number.parseInt(process.argv[4] ?? '200', 10) || 200;
  const probeQuery = process.argv[5];

  const rate = await get(token, '/rate_limit');
  if (rate.status !== 200) {
    console.error(`GET /rate_limit returned ${rate.status}; cannot read the buckets`);
    process.exitCode = 2;
    return;
  }

  const table = buckets(rate.body);
  const now = Math.floor(Date.now() / 1000);
  for (const name of ['core', 'search', 'code_search']) {
    const row = table[name];
    const wait = secondsUntil(row.reset, now);
    console.log(`${name.padEnd(12)} limit ${row.limit} remaining ` +
      `${row.remaining ?? '?'} reset in ${wait === null ? 'unknown' : `${wait}s`}`);
    if (!row.present) {
      console.warn(`  ${name} was not in the resources table; showing the ` +
        'documented default');
    }
  }

  if (probeQuery) {
    const probe = await get(token, '/search/code', { q: probeQuery, per_page: 1 });
    console.log(`probe: /search/code returned ${probe.status}, billed to ` +
      `${probe.headers['x-ratelimit-resource'] ?? 'an unnamed bucket'}`);
    if (probe.status === 403) {
      console.warn('  a 403 here with core headroom left is this bucket, not ' +
        'the hourly quota and not your token scopes');
    }
  }

  const code = table.code_search;
  const iterating = scanCost(repos, queries, code.limit);
  const collapsed = collapsedCost(Math.max(1, queries), results, code.limit);
  const [state, detail] = verdict(code, iterating, collapsed);
  console.log(`${state}: ${detail}`);

  if (collapsed.truncated) {
    console.warn(`one query cannot return more than ${RESULT_CAP} results, so ` +
      `the collapsed costing counts ${collapsed.pages_per_query} page(s) and ` +
      'stops. Narrow by path, extension or date rather than paging further.');
  }
  if (state === 'per-repo-scan' || state === 'over-budget' || state === 'exhausted') {
    console.log('repair: one qualified query instead of one per repository, ' +
      'for example q=YOURTERM+org:YOURORG with per_page=100, and follow the ' +
      'Link header.');
    console.log('repair: for an exhaustive audit, shallow-clone and grep ' +
      'locally. The search index is capped, ranked and metered; a clone is none ' +
      'of those.');
  }

  console.log(JSON.stringify({ buckets: table, iterating, collapsed, state }, null, 2));
  process.exitCode = (state === 'per-repo-scan' || state === 'over-budget' ||
    state === 'exhausted') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing token and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The interesting cases are the ones you cannot arrange on demand: a <code>code_search</code> row that is already at zero, a deployment that does not return the row at all, and a query whose result count is past the 1,000 ceiling so the page count has to stop rather than keep multiplying. All four functions take plain values and return plain values, so every one of those is a two-line test.",
"test_py_file": "test_github_code_search_budget.py",
"test_py": '''from github_code_search_budget import (
    buckets, collapsed_cost, scan_cost, seconds_until, verdict)

PAYLOAD = {"resources": {
    "core": {"limit": 5000, "remaining": 4987, "reset": 1700000000},
    "search": {"limit": 30, "remaining": 30, "reset": 1700000060},
    "code_search": {"limit": 10, "remaining": 0, "reset": 1700000060},
}}


def test_every_documented_bucket_is_reported_separately():
    table = buckets(PAYLOAD)
    assert table["core"]["remaining"] == 4987
    assert table["code_search"]["remaining"] == 0
    assert table["code_search"]["limit"] == 10


def test_a_missing_row_is_flagged_rather_than_read_as_zero():
    table = buckets({"resources": {"core": {"limit": 5000, "remaining": 10}}})
    assert table["code_search"]["present"] is False
    assert table["code_search"]["remaining"] is None
    assert table["code_search"]["limit"] == 10


def test_an_empty_payload_still_returns_the_full_table():
    table = buckets(None)
    assert set(table) == {"core", "search", "code_search"}
    assert all(row["present"] is False for row in table.values())


def test_unreadable_numbers_do_not_become_zero():
    table = buckets({"resources": {"code_search": {"limit": "ten", "remaining": None}}})
    assert table["code_search"]["limit"] == 10
    assert table["code_search"]["remaining"] is None


def test_a_per_repo_scan_costs_repositories_not_pages():
    cost = scan_cost(600, 1, 10)
    assert cost["requests"] == 600
    assert cost["minutes"] == 60


def test_minutes_round_up_because_a_partial_minute_still_waits():
    assert scan_cost(11, 1, 10)["minutes"] == 2
    assert scan_cost(0, 3, 10) == {"requests": 0, "minutes": 0}


def test_the_collapsed_scan_costs_pages():
    cost = collapsed_cost(1, 800, 10)
    assert cost["pages_per_query"] == 8
    assert cost["requests"] == 8
    assert cost["minutes"] == 1
    assert cost["truncated"] is False


def test_paging_stops_at_the_thousand_result_ceiling():
    cost = collapsed_cost(1, 50000, 10)
    assert cost["pages_per_query"] == 10
    assert cost["truncated"] is True


def test_a_query_with_no_matches_still_costs_one_request():
    assert collapsed_cost(3, 0, 10)["requests"] == 3


def test_the_page_size_cannot_be_raised_past_a_hundred():
    assert collapsed_cost(1, 500, 10, page_size=500)["pages_per_query"] == 5


def test_seconds_until_floors_at_zero_and_reports_junk_as_unknown():
    assert seconds_until(1700000060, 1700000000) == 60
    assert seconds_until(1700000000, 1700000060) == 0
    assert seconds_until(None, 1700000000) is None


def test_an_empty_code_search_bucket_is_not_the_hourly_quota():
    state, detail = verdict(buckets(PAYLOAD)["code_search"],
                            scan_cost(600, 1, 10), collapsed_cost(1, 800, 10))
    assert state == "exhausted"
    assert "not the core quota" in detail


def test_the_loop_is_named_as_the_cost_when_it_dwarfs_the_query():
    bucket = {"limit": 10, "remaining": 10, "reset": 0, "present": True}
    state, detail = verdict(bucket, scan_cost(600, 1, 10), collapsed_cost(1, 800, 10))
    assert state == "per-repo-scan"
    assert "600 request(s)" in detail
    assert "8 request(s)" in detail


def test_a_scan_inside_one_minute_is_clear():
    bucket = {"limit": 10, "remaining": 10, "reset": 0, "present": True}
    state, _ = verdict(bucket, scan_cost(5, 1, 10), collapsed_cost(1, 200, 10))
    assert state == "clear"


def test_a_missing_row_is_said_out_loud_in_the_verdict():
    bucket = {"limit": 10, "remaining": None, "reset": None, "present": False}
    _, detail = verdict(bucket, scan_cost(5, 1, 10), collapsed_cost(1, 200, 10))
    assert "documented default" in detail


def test_nothing_to_cost_is_its_own_state():
    bucket = {"limit": 10, "remaining": 10, "reset": 0, "present": True}
    assert verdict(bucket, scan_cost(0, 0, 10), collapsed_cost(1, 200, 10))[0] == "no-scan"
''',
"test_js_file": "github-code-search-budget.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  buckets, collapsedCost, scanCost, secondsUntil, verdict,
} from './github-code-search-budget.mjs';

const PAYLOAD = {
  resources: {
    core: { limit: 5000, remaining: 4987, reset: 1700000000 },
    search: { limit: 30, remaining: 30, reset: 1700000060 },
    code_search: { limit: 10, remaining: 0, reset: 1700000060 },
  },
};

test('every documented bucket is reported separately', () => {
  const table = buckets(PAYLOAD);
  assert.equal(table.core.remaining, 4987);
  assert.equal(table.code_search.remaining, 0);
  assert.equal(table.code_search.limit, 10);
});

test('a missing row is flagged rather than read as zero', () => {
  const table = buckets({ resources: { core: { limit: 5000, remaining: 10 } } });
  assert.equal(table.code_search.present, false);
  assert.equal(table.code_search.remaining, null);
  assert.equal(table.code_search.limit, 10);
});

test('an empty payload still returns the full table', () => {
  const table = buckets(null);
  assert.deepEqual(Object.keys(table).sort(), ['code_search', 'core', 'search']);
  assert.ok(Object.values(table).every((row) => row.present === false));
});

test('unreadable numbers do not become zero', () => {
  const table = buckets({ resources: { code_search: { limit: 'ten', remaining: null } } });
  assert.equal(table.code_search.limit, 10);
  assert.equal(table.code_search.remaining, null);
});

test('a per-repo scan costs repositories, not pages', () => {
  const cost = scanCost(600, 1, 10);
  assert.equal(cost.requests, 600);
  assert.equal(cost.minutes, 60);
});

test('minutes round up because a partial minute still waits', () => {
  assert.equal(scanCost(11, 1, 10).minutes, 2);
  assert.deepEqual(scanCost(0, 3, 10), { requests: 0, minutes: 0 });
});

test('the collapsed scan costs pages', () => {
  const cost = collapsedCost(1, 800, 10);
  assert.equal(cost.pages_per_query, 8);
  assert.equal(cost.requests, 8);
  assert.equal(cost.minutes, 1);
  assert.equal(cost.truncated, false);
});

test('paging stops at the thousand-result ceiling', () => {
  const cost = collapsedCost(1, 50000, 10);
  assert.equal(cost.pages_per_query, 10);
  assert.equal(cost.truncated, true);
});

test('a query with no matches still costs one request', () => {
  assert.equal(collapsedCost(3, 0, 10).requests, 3);
});

test('the page size cannot be raised past a hundred', () => {
  assert.equal(collapsedCost(1, 500, 10, 500).pages_per_query, 5);
});

test('secondsUntil floors at zero and reports junk as unknown', () => {
  assert.equal(secondsUntil(1700000060, 1700000000), 60);
  assert.equal(secondsUntil(1700000000, 1700000060), 0);
  assert.equal(secondsUntil(null, 1700000000), null);
});

test('an empty code_search bucket is not the hourly quota', () => {
  const [state, detail] = verdict(buckets(PAYLOAD).code_search,
    scanCost(600, 1, 10), collapsedCost(1, 800, 10));
  assert.equal(state, 'exhausted');
  assert.match(detail, /not the core quota/);
});

test('the loop is named as the cost when it dwarfs the query', () => {
  const bucket = { limit: 10, remaining: 10, reset: 0, present: true };
  const [state, detail] = verdict(bucket, scanCost(600, 1, 10), collapsedCost(1, 800, 10));
  assert.equal(state, 'per-repo-scan');
  assert.match(detail, /600 request\\(s\\)/);
  assert.match(detail, /8 request\\(s\\)/);
});

test('a scan inside one minute is clear', () => {
  const bucket = { limit: 10, remaining: 10, reset: 0, present: true };
  assert.equal(verdict(bucket, scanCost(5, 1, 10), collapsedCost(1, 200, 10))[0], 'clear');
});

test('a missing row is said out loud in the verdict', () => {
  const bucket = { limit: 10, remaining: null, reset: null, present: false };
  const [, detail] = verdict(bucket, scanCost(5, 1, 10), collapsedCost(1, 200, 10));
  assert.match(detail, /documented default/);
});

test('nothing to cost is its own state', () => {
  const bucket = { limit: 10, remaining: 10, reset: 0, present: true };
  assert.equal(verdict(bucket, scanCost(0, 0, 10), collapsedCost(1, 200, 10))[0], 'no-scan');
});
''',
"faq": [
 ("Why does GET /rate_limit say I have thousands of requests left when code search is refusing me?",
  "Because you are reading the core row. The response is a table of independent buckets: core, search, code_search, graphql and others, each with its own limit, remaining and reset. Code search is billed to code_search, at roughly 10 a minute, and nothing you do there moves the core number. Print the whole resources table rather than the one field, and read x-ratelimit-resource on the refused response to confirm which allowance was spent."),
 ("Is the code search limit the same as the search limit?",
  "No. General search is around 30 requests a minute for an authenticated caller; code search is around 10. They are separate rows in the same table, so spending one does not spend the other. This matters when a tool mixes them: a scan that issues one code search and one issue search per repository is draining two different buckets at two different rates and will hit the code-search one first."),
 ("Would caching with ETags fix this?",
  "Not here, and that is worth being clear about because it is the reflex. Conditional requests save you when you ask the same question repeatedly and the answer has not changed. A per-repository scan asks a different question every time: repo:acme/api, then repo:acme/web, then repo:acme/jobs. There is no cache hit to be had. The fix is asking one question instead of six hundred."),
 ("Can I run code search without a token?",
  "No. Most read endpoints degrade to 60 requests an hour for an anonymous caller, but code search requires authentication outright. That makes a lost token look different here than elsewhere: instead of a smaller allowance you get a refusal, which is worth knowing when a job that used to work stops working after a credential change."),
 ("What should I do when one query genuinely matches more than 1,000 results?",
  "Split the query rather than paging further, because the 1,000-result ceiling applies per query and no amount of pagination gets past it. Narrow by language, by path, by extension, or by pushed date, and run the narrower queries as separate searches. If you need genuine completeness rather than a ranked sample, clone the repositories and grep, which has no ceiling and no meter."),
],
"related": [
 ("/github/search-1000-result-cap/", "Search stops at 1,000 results per query"),
 ("/github/per-page-default-30/", "per_page is unset so every list costs more"),
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
],
"citations": [CITE_RATE_ENDPOINT, CITE_SEARCH, CITE_SEARCH_SYNTAX, CITE_REST_LIMITS],
},


{
"slug": "etag-invalidated-by-token-rotation",
"title": "Rotating the token invalidates every cached ETag at once",
"description": "ETags are scoped to the credential that minted them. When an App installation token expires each hour, a cache that returned 304s returns 200s instead.",
"h1": "rotating the token invalidates every cached ETag at once",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github etag invalidated token", "github app installation token etag",
             "github api 304 becomes 200", "github conditional request rate limit spike",
             "github etag cache credential"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The graph is a sawtooth and it is a very tidy one. Quota consumption sits near zero for fifty-odd minutes, jumps, and settles back, every hour, on the hour. Nothing in the schedule matches. The poller runs every thirty seconds and has done for months. What runs hourly is the installation token.",
"short_answer": """<p>An ETag is not a property of the resource. It is a property of the resource <em>as served to that credential</em>, so the moment the credential changes, every ETag you stored stops matching and every conditional request that was returning a free <code>304</code> returns a billable <code>200</code> instead. GitHub App installation tokens expire after an hour, so this happens on a schedule you did not write.</p>
<p>You can demonstrate it in three requests. Fetch a URL, replay its <code>etag</code> as <code>If-None-Match</code> with the same token &mdash; that should be <code>304</code> &mdash; then replay the same ETag with a second credential. If the second one comes back <code>200</code>, the cache is credential-scoped, and the repair is to key it that way and to reuse each token for its whole hour instead of minting one per cycle.</p>""",
"problem": """<p>Everything about this reads as someone else's fault. The cache works &mdash; you can watch it work &mdash; and then for one minute an hour it does not, and the requests it lets through are exactly the requests you thought you had eliminated. The first theory is always that GitHub changed something, because the client did not.</p>
<p>The cost is quiet until the fleet grows. One process polling forty URLs pays forty extra full responses an hour, which nobody notices. The same code deployed per tenant, polling two thousand URLs, pays two thousand full responses in the few seconds after each rotation, and because they all land together the graph shows a spike rather than a drift, which gets read as an incident rather than as a cache miss.</p>
<p>Then the well-meaning fix makes it worse. A team that mints a fresh installation token for every request &mdash; safer sounding, and easy to write &mdash; has a cache that never hits at all, because no two requests ever share a credential. The conditional-request machinery is still there, still correct, and permanently useless.</p>""",
"why": """<p><strong>Validators are scoped to the response the server sent you.</strong> GitHub computes an ETag against the representation it produced for that request, and that representation depends on who asked: visibility, installation permissions and the fields a given credential is allowed to see all feed into it. A different credential can legitimately be owed a different body, so the old validator cannot be honoured.</p>
<p><strong>Installation tokens expire in an hour, by design.</strong> That is the whole security argument for GitHub Apps over long-lived PATs: the credential is short-lived. It is a good property, but it means an App's cache has a built-in hourly cliff that a PAT-based integration never sees, which is why this shows up when a team migrates from a PAT to an App and not before.</p>
<p><strong>A cache keyed only by URL will silently mix credentials.</strong> Store <code>url -&gt; etag</code> and the entry written under yesterday's token is served to today's, produces a <code>200</code>, and gets overwritten. Nothing errors. The only visible symptom is the bill.</p>
<p><strong>A 200 answer to a conditional request is not a failed saving, it is a missing match.</strong> This is the same signal as a stripped header or a changed resource, so a client that only counts <code>304</code>s cannot tell rotation apart from real change. Comparing the same ETag across two credentials is what separates them.</p>
<p><strong>Minting per request costs twice.</strong> Every mint is itself a request, and it throws away the cache the previous token had warmed. Holding one installation token for its full hour is both fewer requests and more <code>304</code>s.</p>""",
"steps": [
 {"h": "Fetch once and keep the etag",
  "body": """<p>Any GET that returns an <code>etag</code> works; use one your integration actually polls. Keep the header value exactly as sent, quotes and any <code>W/</code> weak prefix included, because <code>If-None-Match</code> is compared as a string.</p>"""},
 {"h": "Replay it with the same credential as a control",
  "body": """<p>Send the identical GET with <code>If-None-Match: &lt;etag&gt;</code> and the same token. This should be <code>304</code>. If it is not, stop here: the endpoint is not returning a usable validator and the rest of the test would be measuring the wrong thing.</p>"""},
 {"h": "Replay it with a second credential",
  "body": """<p>Same URL, same ETag, different token &mdash; a second PAT is fine for the demonstration, and for an App this is exactly what the next hour looks like. A <code>200</code> here is the finding. It proves the validator did not survive the credential change, without waiting an hour to watch it happen.</p>"""},
 {"h": "Cost the rotation against your own poll shape",
  "body": """<p>Full responses per day equals rotations per day times cached URLs. With an hourly token that is 24 times your URL count, all of it arriving in the seconds after each mint. Compare that number against 5,000 an hour: it is not the volume that hurts, it is that it is concentrated.</p>"""},
 {"h": "Key the cache by credential and hold the token for its hour",
  "body": """<p>Make the cache key <code>(credential identity, url)</code> &mdash; a hash of the token, or the installation id plus token expiry, never the token itself &mdash; so a rotation produces an honest miss instead of a silent one. Then mint one installation token per hour and let it serve the whole polling cycle, refreshing a minute or two before <code>expires_at</code> rather than on every request.</p>"""},
],
"verify": """<p>Run the check again with the two credentials swapped. The control request should still be <code>304</code>, and the projection should show what the rotation costs once the cache is keyed properly: nothing, because a miss under a new key is a first fetch rather than a repeat.</p>
<pre><code class="language-bash">python3 github_etag_credential_check.py --path /user --urls 2000 --ttl 3600
# credential-scoped, rotation-dominates: 2000 full response(s) per rotation</code></pre>""",
"code_intro": "Three GETs and some arithmetic. The classification takes the two status codes rather than the responses, so the tests can cover the combinations that need two live tokens and an hour of waiting to produce. <code>token_ttl</code> parses the <code>expires_at</code> an App hands back with an installation token, and takes <code>now</code> as an argument so \"this expires in six minutes\" is reproducible instead of dependent on when the suite runs.",
"py_file": "github_etag_credential_check.py",
"py": '''"""Prove whether a cached ETag survives a change of credential, and cost it.

Read only. Three GETs against one URL, and the third is only issued when a
second credential is available in the environment.

An ETag is scoped to the representation the server produced for that caller, so
rotating a credential invalidates the whole cache at once. For a GitHub App that
happens every hour, on a schedule nobody wrote.
"""
import argparse
import hashlib
import json
import logging
import math
import os
import sys
import time
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_etag_credential_check")

API = "https://api.github.com"
UA = "github-etag-credential-check/1.0"

# Installation access tokens are valid for one hour.
INSTALLATION_TOKEN_TTL = 3600
HOURLY_LIMIT = 5000


def classify_pair(same, other):
    """Sort the two conditional replays into a finding. Pure.

    `same` is the status when the ETag is replayed with the credential that
    minted it, which is the control. `other` is the status for the same ETag
    under a second credential. Returns (state, detail).
    """
    def code(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    same, other = code(same), code(other)

    if same is None:
        return ("inconclusive", "the control request did not complete, so "
                                "nothing below it can be trusted")
    if same == 200:
        return ("not-cacheable",
                "the endpoint answered 200 to its own etag. Either no validator "
                "came back, something between here and GitHub stripped the "
                "If-None-Match header, or the resource genuinely changed between "
                "the two calls. Rule those out before testing rotation.")
    if same != 304:
        return ("inconclusive",
                "the control request returned %d rather than 304 or 200, which "
                "is not a cache answer at all" % same)

    if other is None:
        return ("unproven",
                "the etag matched its own credential, but no second credential "
                "was available to test the rotation against. The projection "
                "below is arithmetic, not a measurement.")
    if other == 304:
        return ("shared",
                "the same etag matched under both credentials, so rotation is "
                "not what is draining this quota. Look for a poll interval or a "
                "cache key problem instead.")
    if other == 200:
        return ("credential-scoped",
                "the etag that returned 304 for the credential that minted it "
                "returned 200 for another. Every rotation therefore refetches "
                "the entire cache at full price.")
    return ("inconclusive",
            "the second credential returned %d, which is neither a match nor a "
            "miss. Check that it can read this URL at all." % other)


def rotation_waste(urls, poll_interval_s, token_ttl_s,
                   hourly_limit=HOURLY_LIMIT, hours=24):
    """Full responses per day caused by rotation alone. Pure.

    The headline is not the daily total, which is usually modest. It is
    per_rotation: those requests all arrive in the seconds after a mint, which
    is why this reads as a spike rather than as a drift.
    """
    try:
        urls = max(0, int(urls))
    except (TypeError, ValueError):
        urls = 0
    interval = max(1, int(poll_interval_s or 1))
    ttl = max(1, int(token_ttl_s or 1))
    window = max(0, int(hours)) * 3600

    rotations = window // ttl
    polls = (window // interval) * urls
    return {"rotations": rotations,
            "per_rotation": urls,
            "daily": rotations * urls,
            "polls": polls,
            "hourly_share": round(urls / max(1, hourly_limit), 4)}


def token_ttl(expires_at, now):
    """Seconds left on an installation token from its ISO-8601 expires_at. Pure.

    None when it cannot be read, rather than 0: "already expired" and "I could
    not parse this" lead to different next steps.
    """
    if not expires_at:
        return None
    text = str(expires_at).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    try:
        return max(0, int(parsed.timestamp() - float(now)))
    except (TypeError, ValueError):
        return None


def verdict(state, waste):
    """Combine the measurement and the projection into one finding. Pure."""
    if state in ("not-cacheable", "inconclusive"):
        return (state, "no rotation cost can be projected until the control "
                       "request behaves")
    if state == "shared":
        return ("shared", "rotation is not the problem here")

    share = waste.get("hourly_share", 0)
    per_rotation = waste.get("per_rotation", 0)
    daily = waste.get("daily", 0)

    if state == "unproven" and not daily:
        return ("clear", "nothing to project: no cached urls, or a credential "
                         "that outlives the window")
    if share >= 0.25:
        return ("rotation-dominates",
                "%d full response(s) land in the seconds after every mint, which "
                "is %.0f%% of one hour's entire quota, %d time(s) a day"
                % (per_rotation, share * 100, waste.get("rotations", 0)))
    if daily:
        return ("rotation-costs",
                "%d full response(s) per rotation, %d a day, all of which a "
                "credential-keyed cache would have kept as 304s"
                % (per_rotation, daily))
    return ("clear", "the credential outlives the window, so no rotation cost "
                     "falls inside it")


def fingerprint(token):
    """A stable, non-reversible id for a credential, for use as a cache key.

    The token itself must never be the key: cache keys get logged, dumped and
    put in error messages.
    """
    return hashlib.sha256(("gh:" + str(token)).encode("utf-8")).hexdigest()[:12]


def get(session, url, token, etag=None):
    """One GET, optionally conditional. Returns (status, etag, used)."""
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    }
    if etag:
        headers["If-None-Match"] = etag
    r = session.get(url, headers=headers, timeout=30)
    lowered = {k.lower(): v for k, v in r.headers.items()}
    return r.status_code, lowered.get("etag"), lowered.get("x-ratelimit-used")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", default="/user",
                    help="any GET that returns an etag; use one you poll")
    ap.add_argument("--urls", type=int, default=40,
                    help="how many distinct urls your cache holds")
    ap.add_argument("--interval", type=int, default=30,
                    help="seconds between polls of each url")
    ap.add_argument("--ttl", type=int, default=INSTALLATION_TOKEN_TTL,
                    help="credential lifetime in seconds (an installation token "
                         "is 3600)")
    ap.add_argument("--expires-at",
                    help="ISO-8601 expires_at from an installation token, if you "
                         "have one; overrides --ttl for the report")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2
    second = os.environ.get("GITHUB_TOKEN_SECOND")

    url = API + args.path if args.path.startswith("/") else args.path
    session = requests.Session()

    first_status, etag, used_before = get(session, url, token)
    if first_status != 200 or not etag:
        log.error("first GET %s returned %d with etag %r; pick a url that "
                  "returns a validator", url, first_status, etag)
        return 2
    log.info("cache key would be (%s, %s)", fingerprint(token), args.path)

    same_status, _, used_control = get(session, url, token, etag)
    log.info("control: same credential, same etag -> %d", same_status)

    other_status = None
    if second:
        other_status, _, _ = get(session, url, second, etag)
        log.info("rotation: second credential, same etag -> %d", other_status)
    else:
        log.warning("set GITHUB_TOKEN_SECOND to a second credential to measure "
                    "the rotation rather than project it")

    state, detail = classify_pair(same_status, other_status)
    log.info("%s: %s", state, detail)

    ttl = args.ttl
    if args.expires_at:
        left = token_ttl(args.expires_at, time.time())
        if left is None:
            log.warning("could not read --expires-at %r; falling back to --ttl",
                        args.expires_at)
        else:
            log.info("the credential you named expires in %ds", left)

    waste = rotation_waste(args.urls, args.interval, ttl)
    final, why = verdict(state, waste)
    log.info("%s: %s", final, why)

    if final in ("rotation-dominates", "rotation-costs"):
        log.info("repair: key the cache by (credential fingerprint, url) so a "
                 "rotation is an honest miss rather than a silent one.")
        log.info("repair: hold one installation token for its full hour and "
                 "refresh a minute before expires_at, rather than minting a "
                 "fresh one per request.")

    print(json.dumps({"measured": state, "state": final, "waste": waste,
                      "used_before": used_before, "used_control": used_control},
                     indent=2))
    return 1 if final in ("rotation-dominates", "rotation-costs",
                          "not-cacheable") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-etag-credential-check.mjs",
"js": '''/**
 * Prove whether a cached ETag survives a change of credential, and cost it.
 *
 * Read only. Three GETs against one URL, and the third is only issued when a
 * second credential is available in the environment.
 *
 * An ETag is scoped to the representation the server produced for that caller,
 * so rotating a credential invalidates the whole cache at once.
 */
import { createHash } from 'node:crypto';

const API = 'https://api.github.com';
const UA = 'github-etag-credential-check/1.0';

// Installation access tokens are valid for one hour.
export const INSTALLATION_TOKEN_TTL = 3600;
export const HOURLY_LIMIT = 5000;

/**
 * Sort the two conditional replays into a finding. Pure.
 * `same` is the control: the etag replayed with the credential that minted it.
 * `other` is the same etag under a second credential.
 */
export function classifyPair(same, other) {
  const code = (v) => {
    const n = Number.parseInt(v, 10);
    return Number.isFinite(n) ? n : null;
  };
  const control = code(same);
  const rotated = code(other);

  if (control === null) {
    return ['inconclusive',
      'the control request did not complete, so nothing below it can be trusted'];
  }
  if (control === 200) {
    return ['not-cacheable',
      'the endpoint answered 200 to its own etag. Either no validator came ' +
      'back, something between here and GitHub stripped the If-None-Match ' +
      'header, or the resource genuinely changed between the two calls. Rule ' +
      'those out before testing rotation.'];
  }
  if (control !== 304) {
    return ['inconclusive',
      `the control request returned ${control} rather than 304 or 200, which ` +
      'is not a cache answer at all'];
  }
  if (rotated === null) {
    return ['unproven',
      'the etag matched its own credential, but no second credential was ' +
      'available to test the rotation against. The projection below is ' +
      'arithmetic, not a measurement.'];
  }
  if (rotated === 304) {
    return ['shared',
      'the same etag matched under both credentials, so rotation is not what ' +
      'is draining this quota. Look for a poll interval or a cache key ' +
      'problem instead.'];
  }
  if (rotated === 200) {
    return ['credential-scoped',
      'the etag that returned 304 for the credential that minted it returned ' +
      '200 for another. Every rotation therefore refetches the entire cache ' +
      'at full price.'];
  }
  return ['inconclusive',
    `the second credential returned ${rotated}, which is neither a match nor a ` +
    'miss. Check that it can read this URL at all.'];
}

/**
 * Full responses per day caused by rotation alone. Pure.
 * The headline is per_rotation, not the daily total: those requests arrive
 * together, which is why this reads as a spike rather than a drift.
 */
export function rotationWaste(urls, pollIntervalS, tokenTtlS,
                              hourlyLimit = HOURLY_LIMIT, hours = 24) {
  const n = Math.max(0, Number.parseInt(urls, 10) || 0);
  const interval = Math.max(1, Number.parseInt(pollIntervalS, 10) || 1);
  const ttl = Math.max(1, Number.parseInt(tokenTtlS, 10) || 1);
  const window = Math.max(0, Number.parseInt(hours, 10) || 0) * 3600;

  const rotations = Math.floor(window / ttl);
  const polls = Math.floor(window / interval) * n;
  return {
    rotations,
    per_rotation: n,
    daily: rotations * n,
    polls,
    hourly_share: Math.round((n / Math.max(1, hourlyLimit)) * 10000) / 10000,
  };
}

/**
 * Seconds left on an installation token from its ISO-8601 expires_at. Pure.
 * null when unreadable, because "already expired" and "could not parse" lead
 * to different next steps.
 */
export function tokenTtl(expiresAt, now) {
  if (!expiresAt) return null;
  const at = Date.parse(String(expiresAt));
  const n = Number(now);
  if (!Number.isFinite(at) || !Number.isFinite(n)) return null;
  return Math.max(0, Math.trunc(at / 1000 - n));
}

/** Combine the measurement and the projection into one finding. Pure. */
export function verdict(state, waste) {
  if (state === 'not-cacheable' || state === 'inconclusive') {
    return [state, 'no rotation cost can be projected until the control request behaves'];
  }
  if (state === 'shared') return ['shared', 'rotation is not the problem here'];

  const share = waste.hourly_share ?? 0;
  const perRotation = waste.per_rotation ?? 0;
  const daily = waste.daily ?? 0;

  if (state === 'unproven' && !daily) {
    return ['clear',
      'nothing to project: no cached urls, or a credential that outlives the window'];
  }
  if (share >= 0.25) {
    return ['rotation-dominates',
      `${perRotation} full response(s) land in the seconds after every mint, ` +
      `which is ${Math.round(share * 100)}% of one hour's entire quota, ` +
      `${waste.rotations ?? 0} time(s) a day`];
  }
  if (daily) {
    return ['rotation-costs',
      `${perRotation} full response(s) per rotation, ${daily} a day, all of ` +
      'which a credential-keyed cache would have kept as 304s'];
  }
  return ['clear', 'the credential outlives the window, so no rotation cost falls inside it'];
}

/** A stable, non-reversible id for a credential, safe to use as a cache key. */
export function fingerprint(token) {
  return createHash('sha256').update(`gh:${token}`).digest('hex').slice(0, 12);
}

async function get(url, token, etag) {
  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
  if (etag) headers['If-None-Match'] = etag;
  const res = await fetch(url, { headers });
  return {
    status: res.status,
    etag: res.headers.get('etag'),
    used: res.headers.get('x-ratelimit-used'),
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const second = process.env.GITHUB_TOKEN_SECOND;
  const path = process.argv[2] ?? '/user';
  const urls = Number.parseInt(process.argv[3] ?? '40', 10) || 40;
  const interval = Number.parseInt(process.argv[4] ?? '30', 10) || 30;
  const ttl = Number.parseInt(process.argv[5] ?? String(INSTALLATION_TOKEN_TTL), 10)
    || INSTALLATION_TOKEN_TTL;
  const url = path.startsWith('/') ? API + path : path;

  const first = await get(url, token);
  if (first.status !== 200 || !first.etag) {
    console.error(`first GET ${url} returned ${first.status} with etag ` +
      `${first.etag}; pick a url that returns a validator`);
    process.exitCode = 2;
    return;
  }
  console.log(`cache key would be (${fingerprint(token)}, ${path})`);

  const control = await get(url, token, first.etag);
  console.log(`control: same credential, same etag -> ${control.status}`);

  let rotated = null;
  if (second) {
    rotated = (await get(url, second, first.etag)).status;
    console.log(`rotation: second credential, same etag -> ${rotated}`);
  } else {
    console.warn('set GITHUB_TOKEN_SECOND to a second credential to measure ' +
      'the rotation rather than project it');
  }

  const [state, detail] = classifyPair(control.status, rotated);
  console.log(`${state}: ${detail}`);

  const waste = rotationWaste(urls, interval, ttl);
  const [final, why] = verdict(state, waste);
  console.log(`${final}: ${why}`);

  if (final === 'rotation-dominates' || final === 'rotation-costs') {
    console.log('repair: key the cache by (credential fingerprint, url) so a ' +
      'rotation is an honest miss rather than a silent one.');
    console.log('repair: hold one installation token for its full hour and ' +
      'refresh a minute before expires_at, rather than minting a fresh one ' +
      'per request.');
  }

  console.log(JSON.stringify({
    measured: state, state: final, waste,
    used_before: first.used, used_control: control.used,
  }, null, 2));
  process.exitCode = (final === 'rotation-dominates' || final === 'rotation-costs' ||
    final === 'not-cacheable') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail on the missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The whole point of the note is a combination that takes two live credentials and an expiring token to produce, so the classifier takes two status codes and nothing else. That makes 304-then-200 a one-line test, and it makes the near misses testable too: the control that answers 200 because a proxy stripped the header, and the second credential that answers 404 because it cannot see the repository at all, which is not a cache finding and must not be reported as one.",
"test_py_file": "test_github_etag_credential_check.py",
"test_py": '''from datetime import datetime, timezone

from github_etag_credential_check import (
    classify_pair, fingerprint, rotation_waste, token_ttl, verdict)

NOON = datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()


def test_a_304_that_becomes_a_200_under_another_credential_is_the_finding():
    state, detail = classify_pair(304, 200)
    assert state == "credential-scoped"
    assert "full price" in detail


def test_a_304_under_both_credentials_clears_rotation():
    assert classify_pair(304, 304)[0] == "shared"


def test_a_control_that_answers_200_is_not_a_rotation_result():
    state, detail = classify_pair(200, 200)
    assert state == "not-cacheable"
    assert "If-None-Match" in detail


def test_no_second_credential_is_unproven_rather_than_clear():
    state, detail = classify_pair(304, None)
    assert state == "unproven"
    assert "arithmetic, not a measurement" in detail


def test_a_second_credential_that_cannot_see_the_url_is_not_a_cache_finding():
    state, detail = classify_pair(304, 404)
    assert state == "inconclusive"
    assert "404" in detail


def test_a_control_that_did_not_complete_stops_the_analysis():
    assert classify_pair(None, 200)[0] == "inconclusive"
    assert classify_pair(500, 200)[0] == "inconclusive"


def test_an_hourly_token_rotates_twenty_four_times_a_day():
    waste = rotation_waste(40, 30, 3600)
    assert waste["rotations"] == 24
    assert waste["per_rotation"] == 40
    assert waste["daily"] == 960
    assert waste["polls"] == 115200


def test_a_credential_that_outlives_the_window_costs_nothing_inside_it():
    waste = rotation_waste(10, 60, 172800)
    assert waste["rotations"] == 0
    assert waste["daily"] == 0


def test_the_share_is_of_one_hours_quota_not_of_the_day():
    assert rotation_waste(2000, 60, 3600)["hourly_share"] == 0.4


def test_a_zero_interval_does_not_divide_by_zero():
    assert rotation_waste(5, 0, 0)["polls"] >= 0


def test_token_ttl_reads_the_z_suffix_github_actually_sends():
    assert token_ttl("2026-08-30T13:00:00Z", NOON) == 3600
    assert token_ttl("2026-08-30T13:00:00+00:00", NOON) == 3600


def test_an_expired_token_is_zero_and_an_unreadable_one_is_none():
    assert token_ttl("2026-08-30T11:00:00Z", NOON) == 0
    assert token_ttl("next tuesday", NOON) is None
    assert token_ttl(None, NOON) is None


def test_a_fleet_sized_cache_spends_a_quarter_of_an_hour_of_quota_per_mint():
    state, detail = verdict("credential-scoped", rotation_waste(2000, 60, 3600))
    assert state == "rotation-dominates"
    assert "40%" in detail


def test_a_small_cache_is_still_reported_as_a_cost():
    state, detail = verdict("credential-scoped", rotation_waste(40, 30, 3600))
    assert state == "rotation-costs"
    assert "960 a day" in detail


def test_nothing_is_projected_until_the_control_behaves():
    assert verdict("not-cacheable", rotation_waste(40, 30, 3600))[0] == "not-cacheable"
    assert verdict("shared", rotation_waste(40, 30, 3600))[0] == "shared"


def test_the_cache_key_is_a_digest_and_never_the_token():
    key = fingerprint("ghp_secretvalue")
    assert "ghp_secretvalue" not in key
    assert key == fingerprint("ghp_secretvalue")
    assert key != fingerprint("ghp_other")
''',
"test_js_file": "github-etag-credential-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classifyPair, fingerprint, rotationWaste, tokenTtl, verdict,
} from './github-etag-credential-check.mjs';

const NOON = Date.parse('2026-08-30T12:00:00Z') / 1000;

test('a 304 that becomes a 200 under another credential is the finding', () => {
  const [state, detail] = classifyPair(304, 200);
  assert.equal(state, 'credential-scoped');
  assert.match(detail, /full price/);
});

test('a 304 under both credentials clears rotation', () => {
  assert.equal(classifyPair(304, 304)[0], 'shared');
});

test('a control that answers 200 is not a rotation result', () => {
  const [state, detail] = classifyPair(200, 200);
  assert.equal(state, 'not-cacheable');
  assert.match(detail, /If-None-Match/);
});

test('no second credential is unproven rather than clear', () => {
  const [state, detail] = classifyPair(304, null);
  assert.equal(state, 'unproven');
  assert.match(detail, /arithmetic, not a measurement/);
});

test('a second credential that cannot see the url is not a cache finding', () => {
  const [state, detail] = classifyPair(304, 404);
  assert.equal(state, 'inconclusive');
  assert.match(detail, /404/);
});

test('a control that did not complete stops the analysis', () => {
  assert.equal(classifyPair(null, 200)[0], 'inconclusive');
  assert.equal(classifyPair(500, 200)[0], 'inconclusive');
});

test('an hourly token rotates twenty-four times a day', () => {
  const waste = rotationWaste(40, 30, 3600);
  assert.equal(waste.rotations, 24);
  assert.equal(waste.per_rotation, 40);
  assert.equal(waste.daily, 960);
  assert.equal(waste.polls, 115200);
});

test('a credential that outlives the window costs nothing inside it', () => {
  const waste = rotationWaste(10, 60, 172800);
  assert.equal(waste.rotations, 0);
  assert.equal(waste.daily, 0);
});

test('the share is of one hour of quota, not of the day', () => {
  assert.equal(rotationWaste(2000, 60, 3600).hourly_share, 0.4);
});

test('a zero interval does not divide by zero', () => {
  assert.ok(rotationWaste(5, 0, 0).polls >= 0);
});

test('tokenTtl reads the Z suffix GitHub actually sends', () => {
  assert.equal(tokenTtl('2026-08-30T13:00:00Z', NOON), 3600);
  assert.equal(tokenTtl('2026-08-30T13:00:00+00:00', NOON), 3600);
});

test('an expired token is zero and an unreadable one is null', () => {
  assert.equal(tokenTtl('2026-08-30T11:00:00Z', NOON), 0);
  assert.equal(tokenTtl('next tuesday', NOON), null);
  assert.equal(tokenTtl(null, NOON), null);
});

test('a fleet-sized cache spends a quarter of an hour of quota per mint', () => {
  const [state, detail] = verdict('credential-scoped', rotationWaste(2000, 60, 3600));
  assert.equal(state, 'rotation-dominates');
  assert.match(detail, /40%/);
});

test('a small cache is still reported as a cost', () => {
  const [state, detail] = verdict('credential-scoped', rotationWaste(40, 30, 3600));
  assert.equal(state, 'rotation-costs');
  assert.match(detail, /960 a day/);
});

test('nothing is projected until the control behaves', () => {
  assert.equal(verdict('not-cacheable', rotationWaste(40, 30, 3600))[0], 'not-cacheable');
  assert.equal(verdict('shared', rotationWaste(40, 30, 3600))[0], 'shared');
});

test('the cache key is a digest and never the token', () => {
  const key = fingerprint('ghp_secretvalue');
  assert.ok(!key.includes('ghp_secretvalue'));
  assert.equal(key, fingerprint('ghp_secretvalue'));
  assert.notEqual(key, fingerprint('ghp_other'));
});
''',
"faq": [
 ("Why would an ETag depend on which token asked for it?",
  "Because the ETag validates a representation, not a resource, and the representation depends on the caller. What a token is permitted to see feeds into the body GitHub builds, so the same URL can legitimately produce different bytes for two credentials. A validator computed for one of those bodies cannot be honoured for the other, and the server has no way to know your two tokens would have been owed identical content."),
 ("Does this affect personal access tokens as well as GitHub Apps?",
  "Yes, but on a schedule you control rather than an hourly one. Rotating a PAT invalidates the cache in exactly the same way; the difference is that a PAT might be rotated quarterly while an App installation token expires every hour by design. That is why teams usually meet this failure during a migration from a PAT to an App: the code did not change, the credential lifetime did."),
 ("Should I stop rotating tokens to keep the cache warm?",
  "No. Short-lived credentials are the point of GitHub Apps and a cache is not a reason to give that up. Reuse each installation token for the full hour it is valid, refreshing shortly before expires_at, and key the cache so a rotation registers as a miss. That gets you one cold minute an hour instead of a permanently cold cache, at no cost to the security property."),
 ("Can I use the token itself as part of the cache key?",
  "Do not. Cache keys end up in logs, in dumps and in error messages, and a token in any of those places is a token you have to rotate. Use a digest of it, or the installation id combined with the token's expiry, which identifies the credential just as precisely and is safe to print. The script uses a truncated SHA-256 for exactly this reason."),
 ("How do I tell rotation apart from the resource actually changing?",
  "By replaying one ETag under two credentials in quick succession, which is what the script does. A resource that changed answers 200 to both. A credential-scoped validator answers 304 to the credential that minted it and 200 to the other, in the same second, with nothing having changed in between. That is the difference a rate-limit graph cannot show you."),
],
"related": [
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
 ("/github/poll-interval-header-ignored/", "The x-poll-interval header is ignored"),
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
],
"citations": [CITE_CONDITIONAL, CITE_APP_INSTALL_AUTH, CITE_BEST, CITE_REST_LIMITS],
},


{
"slug": "polling-instead-of-webhooks",
"title": "The integration polls for events a webhook would push",
"description": "An empty hook list next to a climbing core counter is the signature of a poller. Read the inventory, cost the loop in latency, and print the hook to create.",
"h1": "the integration polls for events a webhook would push",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api polling vs webhooks", "github webhook instead of polling",
             "github api rate limit polling", "github repository hooks list",
             "github api best practices polling"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The integration works. It notices new pull requests, it picks up comments, it has never lost anything. It also makes 4,320 requests an hour to do it, notices each of those events an average of thirty seconds after it happened, and would notice nothing at all if the poll ran once a day instead. There is no bug here. There is a design that was never revisited.",
"short_answer": """<p>GitHub's own guidance is to subscribe rather than poll, and the check is two GETs: <code>GET /repos/{owner}/{repo}/hooks</code> and <code>GET /orgs/{org}/hooks</code>. An empty array, or an array whose <code>events</code> do not include what the loop is looking for, next to a core counter that climbs at a constant rate, is a poller.</p>
<p>Polling costs quota linearly in <em>time</em>; a webhook costs it linearly in <em>activity</em>, which for most repositories is a much smaller number. It also costs latency: a loop with a 60-second interval notices things 30 seconds late on average and 60 seconds late at worst, and it cannot see a change that happened and was undone between two polls. The script below lists what is subscribed, names which polled concerns nothing would push, and prints the <code>gh</code> command that creates the missing hook.</p>""",
"problem": """<p>This never gets escalated, because nothing fails. The poll is correct, the data is right, and the only symptom is a graph nobody looks at. It becomes visible on the day the same integration is pointed at forty repositories instead of one and the hourly quota stops being theoretical.</p>
<p>The interval is where the argument usually gets stuck. Someone wants faster reactions so the interval drops to ten seconds, which quadruples the cost to halve a latency that is still measured in seconds. Someone else wants to save quota so the interval goes to five minutes, and now the bot answers pull requests two and a half minutes after they open. Both sides are optimising a trade-off that only exists because the events are being pulled instead of pushed.</p>
<p>And there is a correctness edge nobody plans for. A poll sees state, not history. A label added and removed between two polls never happened as far as the loop is concerned; a branch pushed and force-pushed over looks like one event. A webhook delivers both, because it fires on the transition rather than sampling the result.</p>""",
"why": """<p><strong>Cost scales with the clock, not with the work.</strong> Six endpoints polled every thirty seconds is 720 requests an hour whether the repository saw four hundred events or none. A webhook on a quiet weekend costs nothing at all. The comparison people skip is that most repositories are quiet most of the time.</p>
<p><strong>Latency is half the interval, on average, and you are paying for it either way.</strong> A poll's mean detection delay is the interval divided by two, and its worst case is the whole interval. There is no configuration that makes polling both cheap and prompt, which is the entire reason the push path exists.</p>
<p><strong>A hook that exists is not necessarily a hook that delivers.</strong> Every hook object has an <code>active</code> flag, and an inactive one is configuration that does nothing. So is a hook subscribed to the wrong event names, which is a common outcome of copying a hook between repositories. Read <code>events</code> and <code>active</code> together, and treat anything else as absent.</p>
<p><strong>Subscribing to everything is not the fix either.</strong> A wildcard subscription delivers every event GitHub has, including ones you do not handle, which turns a quota problem into a receiver problem. Name the events you actually consume.</p>
<p><strong>A slow poll is still worth keeping.</strong> Deliveries can fail, and a receiver can be down for an hour. The correct end state is a webhook for promptness and an infrequent poll for reconciliation, which is a different thing from the poll you have now &mdash; hourly rather than every thirty seconds, and reconciling rather than detecting.</p>""",
"steps": [
 {"h": "List the hooks that exist at both levels",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code> needs admin on the repository, and <code>GET /orgs/{org}/hooks</code> needs org admin. A read-only token that lacks either gets a 403, and that is a blind spot rather than a finding: report it as unknown instead of reporting zero hooks.</p>"""},
 {"h": "Read events and active together",
  "body": """<p>Collect the <code>events</code> array from every hook where <code>active</code> is true. A hook with <code>active: false</code> delivers nothing, and a hook subscribed to <code>push</code> does not help a loop that is polling for issue comments. Keep the inactive ones aside so you can say "there is a hook for this, it is switched off", which is a much faster fix than creating a new one.</p>"""},
 {"h": "Map each polled endpoint to the event that would replace it",
  "body": """<p>Issues to <code>issues</code>, issue comments to <code>issue_comment</code>, pull requests to <code>pull_request</code>, commits to <code>push</code>, releases to <code>release</code>, workflow runs to <code>workflow_run</code>. Anything in your loop with no event on this list is a genuine reason to keep polling; everything else is not.</p>"""},
 {"h": "Cost the loop in requests an hour and in seconds of latency",
  "body": """<p>Requests an hour is endpoints times repositories times 3,600 over the interval. Mean latency is the interval over two. Put both numbers next to the 5,000-an-hour quota, because the second number is usually the one that changes the conversation: the poll is slower <em>and</em> more expensive.</p>"""},
 {"h": "Create the hook, then slow the poll down rather than deleting it",
  "body": """<p>Subscribe to the named events, point the hook at a receiver that verifies <code>X-Hub-Signature-256</code>, and keep a reconciliation poll at a much longer interval &mdash; hourly, say &mdash; to catch anything a failed delivery lost. That is a safety net at 24 requests a day rather than a detection mechanism at 4,320.</p>"""},
],
"verify": """<p>Re-run the audit once the hook exists. Every polled concern should come back covered, and the report should show the reconciliation interval rather than the detection one.</p>
<pre><code class="language-bash">python3 github_webhook_vs_poll.py --repo acme/api --interval 3600 \\
    --concerns issues,pulls,commits
# push: every polled concern already has an active hook</code></pre>""",
"code_intro": "Two list endpoints and a mapping table. The interesting part is what counts as covered: a hook that exists but is switched off, and a hook subscribed to a wildcard, are opposite mistakes and both are easy to get wrong in a one-line check. So <code>coverage()</code> takes hook objects and returns a row per concern with a reason attached, and <code>poll_cost()</code> reports latency alongside requests, because the latency is the argument that actually lands.",
"py_file": "github_webhook_vs_poll.py",
"py": '''"""Decide whether a polling loop should be a webhook, and cost it if it should.

Read only. Two GETs to list hooks, one to read the quota, and the repair is
printed as a command rather than run.

Detecting the client's polling behaviour from the API is a blind spot: nothing
GitHub returns says how often you call it. What is readable is the other half of
the question, which is whether a push path exists at all.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_webhook_vs_poll")

API = "https://api.github.com"
UA = "github-webhook-vs-poll/1.0"
HOURLY_LIMIT = 5000

# The polled endpoint on the left, the event that would push the same thing on
# the right. Anything a loop reads that is not on this list is a real reason to
# keep polling, and the report says so rather than pretending otherwise.
CONCERNS = {
    "issues": ("GET /repos/{owner}/{repo}/issues", ("issues",)),
    "issue_comments": ("GET /repos/{owner}/{repo}/issues/comments", ("issue_comment",)),
    "pulls": ("GET /repos/{owner}/{repo}/pulls", ("pull_request",)),
    "commits": ("GET /repos/{owner}/{repo}/commits", ("push",)),
    "releases": ("GET /repos/{owner}/{repo}/releases", ("release",)),
    "workflow_runs": ("GET /repos/{owner}/{repo}/actions/runs", ("workflow_run",)),
}


def subscribed_events(hooks):
    """Split hook subscriptions into what delivers and what does not. Pure.

    Inactive hooks are kept separately rather than dropped. "There is a hook for
    this and it is switched off" is a thirty-second fix; "there is no hook" is a
    different job, and reporting the first as the second wastes the difference.
    """
    active, inactive = set(), set()
    wildcard = inactive_wildcard = False
    for hook in hooks or []:
        if not isinstance(hook, dict):
            continue
        live = hook.get("active") is not False
        for event in hook.get("events") or []:
            name = str(event)
            if live:
                active.add(name)
                wildcard = wildcard or name == "*"
            else:
                inactive.add(name)
                inactive_wildcard = inactive_wildcard or name == "*"
    return {"events": active, "wildcard": wildcard,
            "inactive": inactive, "inactive_wildcard": inactive_wildcard}


def coverage(concerns, hooks):
    """One row per polled concern saying whether anything would push it. Pure."""
    subs = subscribed_events(hooks)
    rows = []
    for concern in concerns or []:
        wanted = CONCERNS.get(concern, (None, (concern,)))[1]
        names = "/".join(wanted)
        if subs["wildcard"]:
            rows.append({"concern": concern, "state": "covered",
                         "detail": "a wildcard subscription delivers %s, though "
                                   "it delivers everything else too" % names})
        elif any(w in subs["events"] for w in wanted):
            rows.append({"concern": concern, "state": "covered",
                         "detail": "an active hook subscribes to %s" % names})
        elif any(w in subs["inactive"] for w in wanted) or subs["inactive_wildcard"]:
            rows.append({"concern": concern, "state": "uncovered",
                         "detail": "a hook subscribes to %s but it is not "
                                   "active, and an inactive hook delivers "
                                   "nothing" % names})
        else:
            rows.append({"concern": concern, "state": "uncovered",
                         "detail": "no hook subscribes to %s" % names})
    return rows


def poll_cost(concerns, interval_s, repos=1):
    """Requests and detection latency for the loop as configured. Pure.

    Latency is reported alongside cost because it is usually the number that
    settles the argument: the poll is both slower and more expensive than the
    push it replaces.
    """
    try:
        repos = max(0, int(repos))
    except (TypeError, ValueError):
        repos = 0
    interval = max(1, int(interval_s or 1))
    calls = len(concerns or []) * repos
    per_hour = round(calls * 3600 / interval)
    return {"requests_per_hour": per_hour,
            "requests_per_day": per_hour * 24,
            "mean_latency_s": interval / 2,
            "worst_latency_s": interval}


def verdict(rows, cost, hourly_limit=HOURLY_LIMIT):
    """Turn coverage and cost into one finding. Pure."""
    if not rows:
        return ("nothing-polled", "no concerns were named, so there is nothing "
                                  "to compare against the hooks")
    uncovered = [r for r in rows if r["state"] == "uncovered"]
    share = cost.get("requests_per_hour", 0) / max(1, hourly_limit)

    if not uncovered:
        return ("push",
                "every polled concern already has an active hook, so this loop "
                "is a reconciliation pass rather than a detection mechanism. "
                "Run it on a slow schedule.")
    summary = ("%d of %d polled concern(s) have no active hook. The loop costs "
               "%d request(s) an hour to notice them %.0fs late on average."
               % (len(uncovered), len(rows), cost.get("requests_per_hour", 0),
                  cost.get("mean_latency_s", 0)))
    if share >= 0.5:
        return ("polling-dominates",
                summary + " That is %.0f%% of the hourly quota spent on the "
                          "clock rather than on activity." % (share * 100))
    return ("polling", summary)


def get(session, path):
    """One GET. Returns (status, parsed-json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--org", help="also read the org-level hooks (needs org admin)")
    ap.add_argument("--concerns", default="issues,issue_comments,pulls",
                    help="comma-separated list of what the loop polls for; "
                         "known names: " + ", ".join(sorted(CONCERNS)))
    ap.add_argument("--interval", type=int, default=30,
                    help="seconds between polls")
    ap.add_argument("--repos", type=int, default=1,
                    help="how many repositories the loop covers")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN. Listing hooks needs admin on the "
                  "repository, but only read access to it")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    hooks, blind = [], []
    status, body = get(session, "/repos/%s/hooks" % args.repo)
    if status == 200 and isinstance(body, list):
        hooks.extend(body)
        log.info("%s: %d repository hook(s)", args.repo, len(body))
    else:
        blind.append("repository hooks (%d)" % status)
        log.warning("could not read repository hooks: %d. This token cannot see "
                    "them, which is not the same as there being none.", status)

    if args.org:
        status, body = get(session, "/orgs/%s/hooks" % args.org)
        if status == 200 and isinstance(body, list):
            hooks.extend(body)
            log.info("%s: %d organisation hook(s)", args.org, len(body))
        else:
            blind.append("organisation hooks (%d)" % status)
            log.warning("could not read organisation hooks: %d", status)

    for hook in hooks:
        log.info("  hook %s active=%s events=%s", hook.get("id"),
                 hook.get("active"), ",".join(hook.get("events") or []) or "none")

    concerns = [c.strip() for c in args.concerns.split(",") if c.strip()]
    unknown = [c for c in concerns if c not in CONCERNS]
    for name in unknown:
        log.warning("%r is not a concern with a known event; it will be "
                    "matched against an event of the same name", name)

    rows = coverage(concerns, hooks)
    cost = poll_cost(concerns, args.interval, args.repos)
    for row in rows:
        log.info("%-16s %-10s %s", row["concern"], row["state"], row["detail"])

    status, payload = get(session, "/rate_limit")
    if status == 200:
        core = ((payload or {}).get("resources") or {}).get("core") or {}
        log.info("core quota: %s used of %s", core.get("used"), core.get("limit"))

    state, detail = verdict(rows, cost)
    log.info("%s: %s", state, detail)
    if blind:
        log.warning("unread: %s. Anything reported as uncovered may already be "
                    "covered by a hook this token cannot see.", "; ".join(blind))

    if state in ("polling", "polling-dominates"):
        needed = sorted({e for r in rows if r["state"] == "uncovered"
                         for e in CONCERNS.get(r["concern"], (None, (r["concern"],)))[1]})
        log.info("repair: create one hook for the events you consume. This "
                 "script does not create it:")
        log.info("  gh api --method POST /repos/%s/hooks -f name=web "
                 "-f config[url]=https://example.test/hooks "
                 "-f config[content_type]=json -f config[secret]=YOURSECRET %s",
                 args.repo, " ".join("-f events[]=%s" % e for e in needed))
        log.info("repair: keep the poll as reconciliation at a much longer "
                 "interval, an hour rather than %ds.", args.interval)

    print(json.dumps({"rows": rows, "cost": cost, "state": state,
                      "hooks": len(hooks), "unread": blind}, indent=2))
    return 1 if state in ("polling", "polling-dominates") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-webhook-vs-poll.mjs",
"js": '''/**
 * Decide whether a polling loop should be a webhook, and cost it if it should.
 *
 * Read only. Two GETs to list hooks, one to read the quota, and the repair is
 * printed as a command rather than run.
 *
 * How often a client polls is not visible from the API. Whether a push path
 * exists at all is, and that is the half worth checking.
 */
const API = 'https://api.github.com';
const UA = 'github-webhook-vs-poll/1.0';
export const HOURLY_LIMIT = 5000;

// The polled endpoint on the left, the event that would push the same thing on
// the right. Anything not on this list is a real reason to keep polling.
export const CONCERNS = {
  issues: ['GET /repos/{owner}/{repo}/issues', ['issues']],
  issue_comments: ['GET /repos/{owner}/{repo}/issues/comments', ['issue_comment']],
  pulls: ['GET /repos/{owner}/{repo}/pulls', ['pull_request']],
  commits: ['GET /repos/{owner}/{repo}/commits', ['push']],
  releases: ['GET /repos/{owner}/{repo}/releases', ['release']],
  workflow_runs: ['GET /repos/{owner}/{repo}/actions/runs', ['workflow_run']],
};

/**
 * Split hook subscriptions into what delivers and what does not. Pure.
 * Inactive hooks are kept separately: "there is a hook and it is switched off"
 * is a much faster fix than "there is no hook".
 */
export function subscribedEvents(hooks) {
  const active = new Set();
  const inactive = new Set();
  let wildcard = false;
  let inactiveWildcard = false;
  for (const hook of hooks ?? []) {
    if (!hook || typeof hook !== 'object') continue;
    const live = hook.active !== false;
    for (const event of hook.events ?? []) {
      const name = String(event);
      if (live) {
        active.add(name);
        wildcard = wildcard || name === '*';
      } else {
        inactive.add(name);
        inactiveWildcard = inactiveWildcard || name === '*';
      }
    }
  }
  return { events: active, wildcard, inactive, inactive_wildcard: inactiveWildcard };
}

/** One row per polled concern saying whether anything would push it. Pure. */
export function coverage(concerns, hooks) {
  const subs = subscribedEvents(hooks);
  const rows = [];
  for (const concern of concerns ?? []) {
    const wanted = (CONCERNS[concern] ?? [null, [concern]])[1];
    const names = wanted.join('/');
    if (subs.wildcard) {
      rows.push({ concern, state: 'covered',
        detail: `a wildcard subscription delivers ${names}, though it delivers everything else too` });
    } else if (wanted.some((w) => subs.events.has(w))) {
      rows.push({ concern, state: 'covered', detail: `an active hook subscribes to ${names}` });
    } else if (wanted.some((w) => subs.inactive.has(w)) || subs.inactive_wildcard) {
      rows.push({ concern, state: 'uncovered',
        detail: `a hook subscribes to ${names} but it is not active, and an inactive hook delivers nothing` });
    } else {
      rows.push({ concern, state: 'uncovered', detail: `no hook subscribes to ${names}` });
    }
  }
  return rows;
}

/** Requests and detection latency for the loop as configured. Pure. */
export function pollCost(concerns, intervalS, repos = 1) {
  const n = Math.max(0, Number.parseInt(repos, 10) || 0);
  const interval = Math.max(1, Number.parseInt(intervalS, 10) || 1);
  const calls = (concerns ?? []).length * n;
  const perHour = Math.round((calls * 3600) / interval);
  return {
    requests_per_hour: perHour,
    requests_per_day: perHour * 24,
    mean_latency_s: interval / 2,
    worst_latency_s: interval,
  };
}

/** Turn coverage and cost into one finding. Pure. */
export function verdict(rows, cost, hourlyLimit = HOURLY_LIMIT) {
  if (!rows || !rows.length) {
    return ['nothing-polled',
      'no concerns were named, so there is nothing to compare against the hooks'];
  }
  const uncovered = rows.filter((r) => r.state === 'uncovered');
  const share = (cost.requests_per_hour ?? 0) / Math.max(1, hourlyLimit);

  if (!uncovered.length) {
    return ['push',
      'every polled concern already has an active hook, so this loop is a ' +
      'reconciliation pass rather than a detection mechanism. Run it on a slow schedule.'];
  }
  const summary = `${uncovered.length} of ${rows.length} polled concern(s) have ` +
    `no active hook. The loop costs ${cost.requests_per_hour ?? 0} request(s) an ` +
    `hour to notice them ${Math.round(cost.mean_latency_s ?? 0)}s late on average.`;
  if (share >= 0.5) {
    return ['polling-dominates',
      `${summary} That is ${Math.round(share * 100)}% of the hourly quota spent ` +
      'on the clock rather than on activity.'];
  }
  return ['polling', summary];
}

async function get(token, path) {
  const url = path.startsWith('/') ? API + path : path;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN. Listing hooks needs admin on the ' +
      'repository, but only read access to it');
    process.exitCode = 2;
    return;
  }
  const repo = process.argv[2];
  if (!repo) {
    console.error('usage: node github-webhook-vs-poll.mjs owner/name [concerns] [interval] [repos] [org]');
    process.exitCode = 2;
    return;
  }
  const concerns = (process.argv[3] ?? 'issues,issue_comments,pulls')
    .split(',').map((c) => c.trim()).filter(Boolean);
  const interval = Number.parseInt(process.argv[4] ?? '30', 10) || 30;
  const repos = Number.parseInt(process.argv[5] ?? '1', 10) || 1;
  const org = process.argv[6];

  const hooks = [];
  const blind = [];
  const repoHooks = await get(token, `/repos/${repo}/hooks`);
  if (repoHooks.status === 200 && Array.isArray(repoHooks.body)) {
    hooks.push(...repoHooks.body);
    console.log(`${repo}: ${repoHooks.body.length} repository hook(s)`);
  } else {
    blind.push(`repository hooks (${repoHooks.status})`);
    console.warn(`could not read repository hooks: ${repoHooks.status}. This ` +
      'token cannot see them, which is not the same as there being none.');
  }

  if (org) {
    const orgHooks = await get(token, `/orgs/${org}/hooks`);
    if (orgHooks.status === 200 && Array.isArray(orgHooks.body)) {
      hooks.push(...orgHooks.body);
      console.log(`${org}: ${orgHooks.body.length} organisation hook(s)`);
    } else {
      blind.push(`organisation hooks (${orgHooks.status})`);
      console.warn(`could not read organisation hooks: ${orgHooks.status}`);
    }
  }

  for (const hook of hooks) {
    console.log(`  hook ${hook.id} active=${hook.active} events=` +
      `${(hook.events ?? []).join(',') || 'none'}`);
  }

  const rows = coverage(concerns, hooks);
  const cost = pollCost(concerns, interval, repos);
  for (const row of rows) console.log(`${row.concern} ${row.state} ${row.detail}`);

  const rate = await get(token, '/rate_limit');
  if (rate.status === 200) {
    const core = ((rate.body ?? {}).resources ?? {}).core ?? {};
    console.log(`core quota: ${core.used} used of ${core.limit}`);
  }

  const [state, detail] = verdict(rows, cost);
  console.log(`${state}: ${detail}`);
  if (blind.length) {
    console.warn(`unread: ${blind.join('; ')}. Anything reported as uncovered ` +
      'may already be covered by a hook this token cannot see.');
  }

  if (state === 'polling' || state === 'polling-dominates') {
    const needed = [...new Set(rows.filter((r) => r.state === 'uncovered')
      .flatMap((r) => (CONCERNS[r.concern] ?? [null, [r.concern]])[1]))].sort();
    console.log('repair: create one hook for the events you consume. This ' +
      'script does not create it:');
    console.log(`  gh api --method POST /repos/${repo}/hooks -f name=web ` +
      '-f config[url]=https://example.test/hooks -f config[content_type]=json ' +
      `-f config[secret]=YOURSECRET ${needed.map((e) => `-f events[]=${e}`).join(' ')}`);
    console.log(`repair: keep the poll as reconciliation at a much longer ` +
      `interval, an hour rather than ${interval}s.`);
  }

  console.log(JSON.stringify({ rows, cost, state, hooks: hooks.length, unread: blind }, null, 2));
  process.exitCode = (state === 'polling' || state === 'polling-dominates') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail on the missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Coverage has three answers, not two, and the third is the one worth pinning: a hook that subscribes to exactly the right event but has <code>active</code> set to false is uncovered, and saying so in those words saves someone from creating a duplicate hook next to the disabled one. The wildcard case goes the other way, and the cost function is checked in both units it reports, because a latency of half the interval is the number the argument turns on.",
"test_py_file": "test_github_webhook_vs_poll.py",
"test_py": '''from github_webhook_vs_poll import coverage, poll_cost, subscribed_events, verdict

ACTIVE = [{"id": 1, "active": True, "events": ["issues", "issue_comment"]}]
DISABLED = [{"id": 2, "active": False, "events": ["issues"]}]
WILDCARD = [{"id": 3, "active": True, "events": ["*"]}]


def test_active_and_inactive_subscriptions_are_kept_apart():
    subs = subscribed_events(ACTIVE + DISABLED)
    assert "issue_comment" in subs["events"]
    assert subs["inactive"] == {"issues"}
    assert subs["wildcard"] is False


def test_a_wildcard_is_recognised_only_when_the_hook_is_active():
    assert subscribed_events(WILDCARD)["wildcard"] is True
    off = [{"id": 4, "active": False, "events": ["*"]}]
    assert subscribed_events(off)["wildcard"] is False
    assert subscribed_events(off)["inactive_wildcard"] is True


def test_junk_in_the_hook_list_does_not_raise():
    assert subscribed_events([None, "nope", {}])["events"] == set()
    assert subscribed_events(None)["events"] == set()


def test_an_active_hook_covers_its_concern():
    rows = coverage(["issues", "pulls"], ACTIVE)
    assert rows[0]["state"] == "covered"
    assert rows[1]["state"] == "uncovered"


def test_a_disabled_hook_is_uncovered_and_says_why():
    rows = coverage(["issues"], DISABLED)
    assert rows[0]["state"] == "uncovered"
    assert "not active" in rows[0]["detail"]


def test_a_wildcard_covers_everything_and_warns_that_it_does():
    rows = coverage(["issues", "commits", "releases"], WILDCARD)
    assert [r["state"] for r in rows] == ["covered"] * 3
    assert "everything else" in rows[0]["detail"]


def test_an_unknown_concern_is_matched_against_its_own_name():
    rows = coverage(["deployment"], [{"active": True, "events": ["deployment"]}])
    assert rows[0]["state"] == "covered"


def test_no_hooks_at_all_leaves_every_concern_uncovered():
    rows = coverage(["issues", "pulls"], [])
    assert all(r["state"] == "uncovered" for r in rows)
    assert "no hook subscribes" in rows[0]["detail"]


def test_the_poll_costs_endpoints_times_repos_times_the_clock():
    cost = poll_cost(["issues", "pulls"], 60, repos=3)
    assert cost["requests_per_hour"] == 360
    assert cost["requests_per_day"] == 8640


def test_latency_is_half_the_interval_on_average_and_all_of_it_at_worst():
    cost = poll_cost(["issues"], 60)
    assert cost["mean_latency_s"] == 30
    assert cost["worst_latency_s"] == 60


def test_a_zero_interval_is_clamped_rather_than_dividing_by_zero():
    assert poll_cost(["issues"], 0)["requests_per_hour"] == 3600


def test_an_uncovered_concern_is_reported_with_both_numbers():
    rows = coverage(["issues", "pulls"], [])
    state, detail = verdict(rows, poll_cost(["issues", "pulls"], 60, repos=3))
    assert state == "polling"
    assert "2 of 2" in detail
    assert "360 request(s)" in detail
    assert "30s late" in detail


def test_a_loop_spending_half_the_quota_is_called_out_as_such():
    rows = coverage(["issues", "pulls"], [])
    state, detail = verdict(rows, poll_cost(["issues", "pulls"], 1, repos=1))
    assert state == "polling-dominates"
    assert "%" in detail


def test_full_coverage_reframes_the_loop_as_reconciliation():
    state, detail = verdict(coverage(["issues"], ACTIVE), poll_cost(["issues"], 3600))
    assert state == "push"
    assert "reconciliation" in detail


def test_polling_nothing_is_its_own_state():
    assert verdict([], poll_cost([], 60))[0] == "nothing-polled"
''',
"test_js_file": "github-webhook-vs-poll.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  coverage, pollCost, subscribedEvents, verdict,
} from './github-webhook-vs-poll.mjs';

const ACTIVE = [{ id: 1, active: true, events: ['issues', 'issue_comment'] }];
const DISABLED = [{ id: 2, active: false, events: ['issues'] }];
const WILDCARD = [{ id: 3, active: true, events: ['*'] }];

test('active and inactive subscriptions are kept apart', () => {
  const subs = subscribedEvents([...ACTIVE, ...DISABLED]);
  assert.ok(subs.events.has('issue_comment'));
  assert.deepEqual([...subs.inactive], ['issues']);
  assert.equal(subs.wildcard, false);
});

test('a wildcard is recognised only when the hook is active', () => {
  assert.equal(subscribedEvents(WILDCARD).wildcard, true);
  const off = [{ id: 4, active: false, events: ['*'] }];
  assert.equal(subscribedEvents(off).wildcard, false);
  assert.equal(subscribedEvents(off).inactive_wildcard, true);
});

test('junk in the hook list does not throw', () => {
  assert.equal(subscribedEvents([null, 'nope', {}]).events.size, 0);
  assert.equal(subscribedEvents(null).events.size, 0);
});

test('an active hook covers its concern', () => {
  const rows = coverage(['issues', 'pulls'], ACTIVE);
  assert.equal(rows[0].state, 'covered');
  assert.equal(rows[1].state, 'uncovered');
});

test('a disabled hook is uncovered and says why', () => {
  const rows = coverage(['issues'], DISABLED);
  assert.equal(rows[0].state, 'uncovered');
  assert.match(rows[0].detail, /not active/);
});

test('a wildcard covers everything and warns that it does', () => {
  const rows = coverage(['issues', 'commits', 'releases'], WILDCARD);
  assert.deepEqual(rows.map((r) => r.state), ['covered', 'covered', 'covered']);
  assert.match(rows[0].detail, /everything else/);
});

test('an unknown concern is matched against its own name', () => {
  const rows = coverage(['deployment'], [{ active: true, events: ['deployment'] }]);
  assert.equal(rows[0].state, 'covered');
});

test('no hooks at all leaves every concern uncovered', () => {
  const rows = coverage(['issues', 'pulls'], []);
  assert.ok(rows.every((r) => r.state === 'uncovered'));
  assert.match(rows[0].detail, /no hook subscribes/);
});

test('the poll costs endpoints times repos times the clock', () => {
  const cost = pollCost(['issues', 'pulls'], 60, 3);
  assert.equal(cost.requests_per_hour, 360);
  assert.equal(cost.requests_per_day, 8640);
});

test('latency is half the interval on average and all of it at worst', () => {
  const cost = pollCost(['issues'], 60);
  assert.equal(cost.mean_latency_s, 30);
  assert.equal(cost.worst_latency_s, 60);
});

test('a zero interval is clamped rather than dividing by zero', () => {
  assert.equal(pollCost(['issues'], 0).requests_per_hour, 3600);
});

test('an uncovered concern is reported with both numbers', () => {
  const rows = coverage(['issues', 'pulls'], []);
  const [state, detail] = verdict(rows, pollCost(['issues', 'pulls'], 60, 3));
  assert.equal(state, 'polling');
  assert.match(detail, /2 of 2/);
  assert.match(detail, /360 request\\(s\\)/);
  assert.match(detail, /30s late/);
});

test('a loop spending half the quota is called out as such', () => {
  const rows = coverage(['issues', 'pulls'], []);
  const [state, detail] = verdict(rows, pollCost(['issues', 'pulls'], 1, 1));
  assert.equal(state, 'polling-dominates');
  assert.match(detail, /%/);
});

test('full coverage reframes the loop as reconciliation', () => {
  const [state, detail] = verdict(coverage(['issues'], ACTIVE), pollCost(['issues'], 3600));
  assert.equal(state, 'push');
  assert.match(detail, /reconciliation/);
});

test('polling nothing is its own state', () => {
  assert.equal(verdict([], pollCost([], 60))[0], 'nothing-polled');
});
''',
"faq": [
 ("Can a script tell that my integration is polling?",
  "Not directly. Nothing GitHub returns says how often you call it, so the client half of this is a blind spot. What the API does show is the other half: whether any active hook exists for the events you are reading, and how fast the core counter is climbing between two samples. An empty hook list next to steady consumption is strong evidence, and it is the evidence this script collects."),
 ("Is it wrong to keep polling once the webhook exists?",
  "No, and removing the poll entirely is usually a mistake. Deliveries fail, receivers go down, and a webhook has no replay you can rely on beyond the retained delivery log. Keep a reconciliation poll, but change what it is for: hourly rather than every thirty seconds, sweeping for anything missed rather than being the way things are noticed."),
 ("Should I just subscribe to every event with a wildcard?",
  "It is tempting and it moves the cost rather than removing it. A wildcard delivers everything GitHub emits for that repository, including large payloads for events you do not handle, so your receiver spends its time discarding them and your signature verification runs on all of it. Name the events you consume; the list is short and it documents the integration."),
 ("What do I need to read the hook list?",
  "Admin permission on the repository for the repository hooks, and org admin for the org ones. A read-only token that lacks those gets a 403, which is genuinely different from an empty list: it means unknown, not none. The script reports it as unread rather than folding it into the finding, because treating a permissions gap as an absence is how you end up creating a second hook beside the one you could not see."),
 ("How much latency does polling actually add?",
  "Half the interval on average and the full interval at worst, plus whatever your own processing takes. A thirty-second loop notices a pull request fifteen seconds after it opens, typically. A webhook is delivered in about the time it takes to make the request. The gap matters most for anything a person is waiting on, which is usually the bot comment on a pull request."),
],
"related": [
 ("/github/webhook-event-not-subscribed/", "The hook is not subscribed to the event"),
 ("/github/webhook-deliveries-failing/", "Deliveries have been failing unnoticed"),
 ("/github/poll-interval-header-ignored/", "The x-poll-interval header is ignored"),
],
"citations": [CITE_BEST, CITE_WEBHOOKS, CITE_ABOUT_WEBHOOKS, CITE_WEBHOOK_EVENTS],
},


{
"slug": "poll-interval-header-ignored",
"title": "The x-poll-interval header is ignored on events endpoints",
"description": "Events endpoints return x-poll-interval, the minimum seconds to wait. Polling faster returns the same cached page, and without an ETag you pay for each one.",
"h1": "the x-poll-interval header is ignored on events endpoints",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github x-poll-interval", "github events api poll interval",
             "github api events endpoint rate limit", "github events 304 not modified",
             "github repository events polling"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The events consumer polls every five seconds because five seconds felt responsive. It gets the same page back seven hundred times an hour. On every one of those responses GitHub has been returning a header that says how long to wait before the next one, and the client has never read it.",
"short_answer": """<p>The events endpoints &mdash; <code>/repos/{owner}/{repo}/events</code>, <code>/users/{user}/events</code>, <code>/orgs/{org}/events</code> and the rest &mdash; return <code>x-poll-interval</code> on every response. It is the server telling you the minimum number of seconds to wait, usually 60, and it is the only place in the API where GitHub states a rate for you rather than leaving you to guess one.</p>
<p>The feed is cached and regenerated no faster than that interval, so polling underneath it returns the page you already have. With <code>If-None-Match</code> those extra calls come back <code>304</code> and cost no quota, which makes them merely pointless. Without it they are full <code>200</code>s billed at full price for data that has not changed. Read the header on every response and use it as the sleep, because the value is not a constant &mdash; GitHub raises it under load.</p>""",
"problem": """<p>The reason this survives review is that a faster poll <em>looks</em> like it is working. Events do arrive; they simply arrive no sooner than they would have. The client cannot tell the difference between a page that is fresh and a page that is a cached copy of the last one, so nobody discovers that eleven of every twelve requests were answered from the same cache entry.</p>
<p>It gets worse under exactly the conditions you would want it to get better. GitHub raises <code>x-poll-interval</code> when the service is under pressure, so a client that hardcoded 60 seconds keeps its rate constant while the server is asking everyone to slow down, and a client that hardcoded five seconds is now twenty-four times over a floor it never read.</p>
<p>Then the accounting misleads. If the client does send ETags, the wasted polls are free, so the quota graph stays flat and there is nothing to find. The waste is real &mdash; connections, wakeups, log lines, a scheduler that never idles &mdash; but it does not show up in the one place anyone looks for it.</p>""",
"why": """<p><strong>The events feed is a cache, not a live stream.</strong> It is regenerated on its own schedule, and <code>x-poll-interval</code> is the period of that schedule. A request that arrives between regenerations cannot see anything the previous one did not, whatever it costs you.</p>
<p><strong>The header is dynamic and per-response.</strong> It is not a documented constant to be pasted into a config file. Read it off each response and let it set the next sleep; that way a client that is asked to back off actually backs off, and one that could safely be quicker is.</p>
<p><strong>A 304 does not count against the primary rate limit, but it is not free of everything.</strong> Conditional requests turn the extra polls from expensive into harmless, which is a real improvement and not the same as correct. The <a href="/github/no-conditional-requests/">conditional-request note</a> covers the saving itself; this one is about the fact that the server already told you how often to ask.</p>
<p><strong>Polling slower than the floor is a different mistake with the opposite cost.</strong> A five-minute interval against a 60-second floor wastes no quota at all and adds up to four minutes of avoidable staleness. Both directions are worth reporting, and only one of them shows up on a bill.</p>
<p><strong>Events are also capped and deduplicated.</strong> The feed holds a limited window of recent activity, so an interval far above the floor can miss events entirely on a busy repository rather than merely noticing them late. That is the case where the fix is a webhook rather than a better interval.</p>""",
"steps": [
 {"h": "Make one request and read the header",
  "body": """<p><code>GET /repos/{owner}/{repo}/events</code> and look at <code>x-poll-interval</code>. It is in seconds. That number, not the one in your config, is the fastest useful poll for this endpoint at this moment.</p>"""},
 {"h": "Check that an etag came back on the same response",
  "body": """<p>The events endpoints return one. If your client is not sending it back as <code>If-None-Match</code>, every poll under the floor is a billable duplicate rather than a free one, which decides whether this is a quota problem or just a pointless one.</p>"""},
 {"h": "Compare your configured interval against the floor",
  "body": """<p>Polls an hour is 3,600 divided by your interval; the allowance is 3,600 divided by the floor. The difference is the number of requests that cannot return anything new. Five seconds against a 60-second floor is 720 polls an hour where 60 would do.</p>"""},
 {"h": "Use the header as the sleep, on every cycle",
  "body": """<p>Not a constant read once at startup: the value changes, and it goes up precisely when GitHub wants fewer requests. Store it per endpoint alongside the ETag and treat a missing header as the documented default rather than as permission to go faster.</p>"""},
 {"h": "If you need faster than the floor, stop polling events",
  "body": """<p>The floor is not negotiable and no interval gets under it, so a requirement for sub-minute reaction is a requirement for a webhook. That is a different note, but it is the honest end of this one: the events API is a reconciliation feed, not a notification channel.</p>"""},
],
"verify": """<p>Re-run the check with the interval taken from the header. The report should show the configured interval sitting at the floor, with no wasted polls in either direction.</p>
<pre><code class="language-bash">python3 github_poll_interval_check.py --repo acme/api --interval 60
# at-floor: polling every 60s against a floor of 60s, nothing to reclaim</code></pre>""",
"code_intro": "One GET, and everything after it is header arithmetic. <code>floor_seconds()</code> returns the source of the number as well as the number, because \"the server said 60\" and \"nothing said anything so I assumed 60\" are the same value with different confidence, and a report that conflates them will be trusted more than it should be.",
"py_file": "github_poll_interval_check.py",
"py": '''"""Compare a configured poll interval against the floor GitHub declares.

Read only. One GET against an events endpoint, and the finding comes from its
response headers.

Events endpoints return x-poll-interval: the minimum seconds to wait before the
next poll. The feed is regenerated no faster than that, so a request underneath
it returns the page you already have.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_poll_interval_check")

API = "https://api.github.com"
UA = "github-poll-interval-check/1.0"

# What the events endpoints have historically returned when nothing else says
# otherwise. Used only as a last resort, and labelled as an assumption.
DEFAULT_FLOOR = 60


def parse_max_age(value):
    """Seconds from a Cache-Control header, or None. Pure."""
    match = re.search(r"max-age\\s*=\\s*(\\d+)", str(value or ""), re.I)
    if not match:
        return None
    try:
        seconds = int(match.group(1))
    except ValueError:
        return None
    return seconds if seconds > 0 else None


def floor_seconds(headers, default=DEFAULT_FLOOR):
    """The minimum poll interval the server declared. Pure.

    Returns (seconds, source). The source matters: "the server said 60" and
    "nothing said anything so I assumed 60" are the same number with very
    different confidence, and a report that prints only the number will be
    trusted more than it has earned.
    """
    lowered = {str(k).lower(): v for k, v in (headers or {}).items()}
    raw = lowered.get("x-poll-interval")
    try:
        declared = int(str(raw).strip())
    except (TypeError, ValueError):
        declared = None
    if declared and declared > 0:
        return (declared, "x-poll-interval")

    age = parse_max_age(lowered.get("cache-control"))
    if age:
        return (age, "cache-control max-age")
    return (default, "documented default")


def assess(configured, floor, has_etag):
    """Compare the configured interval against the floor. Pure.

    Both directions are findings. Under the floor costs requests that cannot
    return anything new; over it costs freshness and nothing else, which is why
    only one of the two ever shows up on a quota graph.
    """
    try:
        configured = max(1, int(configured))
    except (TypeError, ValueError):
        configured = 1
    floor = max(1, int(floor or 1))

    polls = round(3600 / configured)
    allowed = round(3600 / floor)
    wasted = max(0, polls - allowed)

    if configured < floor:
        state = "under-floor"
    elif configured <= floor * 1.5:
        state = "at-floor"
    else:
        state = "over-floor"

    return {"state": state, "configured": configured, "floor": floor,
            "polls_per_hour": polls, "allowed_per_hour": allowed,
            "wasted_per_hour": wasted,
            "billable_per_hour": 0 if has_etag else wasted,
            "extra_staleness_s": max(0, configured - floor)}


def verdict(assessment):
    """Turn the comparison into a finding. Pure."""
    state = assessment.get("state")
    floor = assessment.get("floor", DEFAULT_FLOOR)
    configured = assessment.get("configured", floor)

    if state == "under-floor":
        if assessment.get("billable_per_hour"):
            return ("burning-quota",
                    "%d request(s) an hour beyond the %ds floor the server "
                    "declared, and every one of them is billable because no "
                    "etag is being sent. They return the page you already have."
                    % (assessment.get("billable_per_hour", 0), floor))
        return ("free-but-pointless",
                "%d conditional request(s) an hour beyond the %ds floor. They "
                "cost no quota, because an unchanged feed answers 304, but they "
                "cannot return anything new either: the feed is not regenerated "
                "faster than that." % (assessment.get("wasted_per_hour", 0), floor))
    if state == "over-floor":
        return ("slower-than-needed",
                "polling every %ds against a %ds floor adds up to %ds of "
                "avoidable staleness and saves nothing, because the requests "
                "you skipped would have been 304s."
                % (configured, floor, assessment.get("extra_staleness_s", 0)))
    return ("at-floor",
            "polling every %ds against a floor of %ds: nothing to reclaim in "
            "either direction." % (configured, floor))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", help="owner/name; polls that repository's events")
    ap.add_argument("--user", help="poll a user's events instead")
    ap.add_argument("--interval", type=int, default=5,
                    help="the interval your client is configured with, seconds")
    args = ap.parse_args()

    if not args.repo and not args.user:
        log.error("give --repo owner/name or --user login")
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    path = ("/repos/%s/events" % args.repo) if args.repo else ("/users/%s/events" % args.user)
    r = requests.get(API + path, timeout=30, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })
    if r.status_code != 200:
        log.error("GET %s returned %d", path, r.status_code)
        return 2

    headers = dict(r.headers)
    lowered = {k.lower(): v for k, v in headers.items()}
    floor, source = floor_seconds(headers)
    etag = lowered.get("etag")

    log.info("%s: floor %ds (from %s), etag %s, %d event(s) on this page",
             path, floor, source, "present" if etag else "absent",
             len(r.json() if r.content else []))
    if source != "x-poll-interval":
        log.warning("x-poll-interval was not on the response, so the floor "
                    "above is an assumption. Read it per response rather than "
                    "hardcoding one: the value goes up when GitHub is busy.")

    result = assess(args.interval, floor, bool(etag))
    state, detail = verdict(result)
    log.info("%s: %s", state, detail)

    if state != "at-floor":
        log.info("repair: sleep for the value of x-poll-interval on the last "
                 "response, re-reading it every cycle, and send the etag back "
                 "as If-None-Match so an unchanged page is free.")
    if state == "slower-than-needed":
        log.info("repair: the events feed holds only a window of recent "
                 "activity, so an interval far above the floor can miss events "
                 "outright rather than merely notice them late.")

    print(json.dumps({"path": path, "floor": floor, "floor_source": source,
                      "etag": bool(etag), "assessment": result,
                      "state": state}, indent=2))
    return 1 if state in ("burning-quota", "slower-than-needed") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-poll-interval-check.mjs",
"js": '''/**
 * Compare a configured poll interval against the floor GitHub declares.
 *
 * Read only. One GET against an events endpoint, and the finding comes from its
 * response headers.
 *
 * Events endpoints return x-poll-interval: the minimum seconds to wait. The
 * feed is regenerated no faster than that, so a request underneath it returns
 * the page you already have.
 */
const API = 'https://api.github.com';
const UA = 'github-poll-interval-check/1.0';

// What the events endpoints have historically returned when nothing else says
// otherwise. Used only as a last resort, and labelled as an assumption.
export const DEFAULT_FLOOR = 60;

/** Seconds from a Cache-Control header, or null. Pure. */
export function parseMaxAge(value) {
  const match = /max-age\\s*=\\s*(\\d+)/i.exec(String(value ?? ''));
  if (!match) return null;
  const seconds = Number.parseInt(match[1], 10);
  return Number.isFinite(seconds) && seconds > 0 ? seconds : null;
}

/**
 * The minimum poll interval the server declared. Pure.
 * Returns [seconds, source]. The source matters: "the server said 60" and
 * "nothing said anything so I assumed 60" are the same number with very
 * different confidence.
 */
export function floorSeconds(headers, fallback = DEFAULT_FLOOR) {
  const lowered = {};
  for (const [k, v] of Object.entries(headers ?? {})) lowered[String(k).toLowerCase()] = v;

  const declared = Number.parseInt(String(lowered['x-poll-interval'] ?? '').trim(), 10);
  if (Number.isFinite(declared) && declared > 0) return [declared, 'x-poll-interval'];

  const age = parseMaxAge(lowered['cache-control']);
  if (age) return [age, 'cache-control max-age'];
  return [fallback, 'documented default'];
}

/**
 * Compare the configured interval against the floor. Pure.
 * Both directions are findings; only one of them shows up on a quota graph.
 */
export function assess(configured, floor, hasEtag) {
  const every = Math.max(1, Number.parseInt(configured, 10) || 1);
  const min = Math.max(1, Number.parseInt(floor, 10) || 1);

  const polls = Math.round(3600 / every);
  const allowed = Math.round(3600 / min);
  const wasted = Math.max(0, polls - allowed);

  let state = 'at-floor';
  if (every < min) state = 'under-floor';
  else if (every > min * 1.5) state = 'over-floor';

  return {
    state,
    configured: every,
    floor: min,
    polls_per_hour: polls,
    allowed_per_hour: allowed,
    wasted_per_hour: wasted,
    billable_per_hour: hasEtag ? 0 : wasted,
    extra_staleness_s: Math.max(0, every - min),
  };
}

/** Turn the comparison into a finding. Pure. */
export function verdict(assessment) {
  const floor = assessment.floor ?? DEFAULT_FLOOR;
  const configured = assessment.configured ?? floor;

  if (assessment.state === 'under-floor') {
    if (assessment.billable_per_hour) {
      return ['burning-quota',
        `${assessment.billable_per_hour} request(s) an hour beyond the ${floor}s ` +
        'floor the server declared, and every one of them is billable because ' +
        'no etag is being sent. They return the page you already have.'];
    }
    return ['free-but-pointless',
      `${assessment.wasted_per_hour} conditional request(s) an hour beyond the ` +
      `${floor}s floor. They cost no quota, because an unchanged feed answers ` +
      '304, but they cannot return anything new either: the feed is not ' +
      'regenerated faster than that.'];
  }
  if (assessment.state === 'over-floor') {
    return ['slower-than-needed',
      `polling every ${configured}s against a ${floor}s floor adds up to ` +
      `${assessment.extra_staleness_s}s of avoidable staleness and saves ` +
      'nothing, because the requests you skipped would have been 304s.'];
  }
  return ['at-floor',
    `polling every ${configured}s against a floor of ${floor}s: nothing to ` +
    'reclaim in either direction.'];
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const target = process.argv[2];
  if (!target) {
    console.error('usage: node github-poll-interval-check.mjs owner/name [interval]');
    process.exitCode = 2;
    return;
  }
  const interval = Number.parseInt(process.argv[3] ?? '5', 10) || 5;
  const path = target.includes('/') ? `/repos/${target}/events` : `/users/${target}/events`;

  const res = await fetch(API + path, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  if (res.status !== 200) {
    console.error(`GET ${path} returned ${res.status}`);
    process.exitCode = 2;
    return;
  }

  const headers = {};
  for (const [k, v] of res.headers.entries()) headers[k.toLowerCase()] = v;
  const [floor, source] = floorSeconds(headers);
  const etag = headers.etag;
  const page = await res.json().catch(() => []);

  console.log(`${path}: floor ${floor}s (from ${source}), etag ` +
    `${etag ? 'present' : 'absent'}, ${Array.isArray(page) ? page.length : 0} event(s) on this page`);
  if (source !== 'x-poll-interval') {
    console.warn('x-poll-interval was not on the response, so the floor above ' +
      'is an assumption. Read it per response rather than hardcoding one: the ' +
      'value goes up when GitHub is busy.');
  }

  const result = assess(interval, floor, Boolean(etag));
  const [state, detail] = verdict(result);
  console.log(`${state}: ${detail}`);

  if (state !== 'at-floor') {
    console.log('repair: sleep for the value of x-poll-interval on the last ' +
      'response, re-reading it every cycle, and send the etag back as ' +
      'If-None-Match so an unchanged page is free.');
  }
  if (state === 'slower-than-needed') {
    console.log('repair: the events feed holds only a window of recent ' +
      'activity, so an interval far above the floor can miss events outright ' +
      'rather than merely notice them late.');
  }

  console.log(JSON.stringify({
    path, floor, floor_source: source, etag: Boolean(etag),
    assessment: result, state,
  }, null, 2));
  process.exitCode = (state === 'burning-quota' || state === 'slower-than-needed') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail on the missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three things decide whether the report is honest. Header names arrive in whatever case the server felt like, so the lookup has to be case-insensitive. A missing <code>x-poll-interval</code> must fall through to a labelled assumption rather than to a confident number. And the same interval has to produce two different verdicts depending on whether an ETag is being sent, because that is the difference between wasteful and merely futile.",
"test_py_file": "test_github_poll_interval_check.py",
"test_py": '''from github_poll_interval_check import assess, floor_seconds, parse_max_age, verdict


def test_the_declared_interval_wins_and_is_named_as_the_source():
    seconds, source = floor_seconds({"X-Poll-Interval": "60"})
    assert seconds == 60
    assert source == "x-poll-interval"


def test_header_case_does_not_matter():
    assert floor_seconds({"x-poll-interval": "90"})[0] == 90


def test_cache_control_is_the_fallback_before_the_assumption():
    seconds, source = floor_seconds({"Cache-Control": "public, max-age=45, s-maxage=60"})
    assert seconds == 45
    assert source == "cache-control max-age"


def test_a_missing_header_is_labelled_as_an_assumption():
    seconds, source = floor_seconds({})
    assert seconds == 60
    assert source == "documented default"


def test_junk_and_zero_values_do_not_become_the_floor():
    assert floor_seconds({"x-poll-interval": "soon"})[1] == "documented default"
    assert floor_seconds({"x-poll-interval": "0"})[1] == "documented default"
    assert parse_max_age("max-age=0") is None
    assert parse_max_age(None) is None


def test_polling_under_the_floor_counts_the_requests_that_cannot_help():
    result = assess(5, 60, has_etag=False)
    assert result["state"] == "under-floor"
    assert result["polls_per_hour"] == 720
    assert result["allowed_per_hour"] == 60
    assert result["wasted_per_hour"] == 660
    assert result["billable_per_hour"] == 660


def test_an_etag_makes_the_same_extra_polls_free():
    result = assess(5, 60, has_etag=True)
    assert result["wasted_per_hour"] == 660
    assert result["billable_per_hour"] == 0


def test_the_floor_itself_is_at_the_floor():
    assert assess(60, 60, has_etag=True)["state"] == "at-floor"
    assert assess(75, 60, has_etag=True)["state"] == "at-floor"


def test_polling_far_slower_is_measured_in_staleness_not_requests():
    result = assess(600, 60, has_etag=True)
    assert result["state"] == "over-floor"
    assert result["wasted_per_hour"] == 0
    assert result["extra_staleness_s"] == 540


def test_a_zero_interval_is_clamped_rather_than_dividing_by_zero():
    assert assess(0, 60, has_etag=True)["polls_per_hour"] == 3600


def test_extra_polls_without_an_etag_are_a_quota_finding():
    state, detail = verdict(assess(5, 60, has_etag=False))
    assert state == "burning-quota"
    assert "660 request(s)" in detail


def test_extra_polls_with_an_etag_are_pointless_rather_than_expensive():
    state, detail = verdict(assess(5, 60, has_etag=True))
    assert state == "free-but-pointless"
    assert "cost no quota" in detail


def test_too_slow_is_reported_as_staleness():
    state, detail = verdict(assess(600, 60, has_etag=True))
    assert state == "slower-than-needed"
    assert "540s" in detail


def test_matching_the_floor_has_nothing_to_reclaim():
    state, detail = verdict(assess(60, 60, has_etag=True))
    assert state == "at-floor"
    assert "either direction" in detail
''',
"test_js_file": "github-poll-interval-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  assess, floorSeconds, parseMaxAge, verdict,
} from './github-poll-interval-check.mjs';

test('the declared interval wins and is named as the source', () => {
  const [seconds, source] = floorSeconds({ 'X-Poll-Interval': '60' });
  assert.equal(seconds, 60);
  assert.equal(source, 'x-poll-interval');
});

test('header case does not matter', () => {
  assert.equal(floorSeconds({ 'x-poll-interval': '90' })[0], 90);
});

test('cache-control is the fallback before the assumption', () => {
  const [seconds, source] = floorSeconds({ 'Cache-Control': 'public, max-age=45, s-maxage=60' });
  assert.equal(seconds, 45);
  assert.equal(source, 'cache-control max-age');
});

test('a missing header is labelled as an assumption', () => {
  const [seconds, source] = floorSeconds({});
  assert.equal(seconds, 60);
  assert.equal(source, 'documented default');
});

test('junk and zero values do not become the floor', () => {
  assert.equal(floorSeconds({ 'x-poll-interval': 'soon' })[1], 'documented default');
  assert.equal(floorSeconds({ 'x-poll-interval': '0' })[1], 'documented default');
  assert.equal(parseMaxAge('max-age=0'), null);
  assert.equal(parseMaxAge(null), null);
});

test('polling under the floor counts the requests that cannot help', () => {
  const result = assess(5, 60, false);
  assert.equal(result.state, 'under-floor');
  assert.equal(result.polls_per_hour, 720);
  assert.equal(result.allowed_per_hour, 60);
  assert.equal(result.wasted_per_hour, 660);
  assert.equal(result.billable_per_hour, 660);
});

test('an etag makes the same extra polls free', () => {
  const result = assess(5, 60, true);
  assert.equal(result.wasted_per_hour, 660);
  assert.equal(result.billable_per_hour, 0);
});

test('the floor itself is at the floor', () => {
  assert.equal(assess(60, 60, true).state, 'at-floor');
  assert.equal(assess(75, 60, true).state, 'at-floor');
});

test('polling far slower is measured in staleness, not requests', () => {
  const result = assess(600, 60, true);
  assert.equal(result.state, 'over-floor');
  assert.equal(result.wasted_per_hour, 0);
  assert.equal(result.extra_staleness_s, 540);
});

test('a zero interval is clamped rather than dividing by zero', () => {
  assert.equal(assess(0, 60, true).polls_per_hour, 3600);
});

test('extra polls without an etag are a quota finding', () => {
  const [state, detail] = verdict(assess(5, 60, false));
  assert.equal(state, 'burning-quota');
  assert.match(detail, /660 request\\(s\\)/);
});

test('extra polls with an etag are pointless rather than expensive', () => {
  const [state, detail] = verdict(assess(5, 60, true));
  assert.equal(state, 'free-but-pointless');
  assert.match(detail, /cost no quota/);
});

test('too slow is reported as staleness', () => {
  const [state, detail] = verdict(assess(600, 60, true));
  assert.equal(state, 'slower-than-needed');
  assert.match(detail, /540s/);
});

test('matching the floor has nothing to reclaim', () => {
  const [state, detail] = verdict(assess(60, 60, true));
  assert.equal(state, 'at-floor');
  assert.match(detail, /either direction/);
});
''',
"faq": [
 ("What value does x-poll-interval usually have?",
  "Sixty seconds is the common answer for the events endpoints, but treating that as a constant is the mistake the note is about. GitHub raises the value when the service is under load, which means the moment it matters most is the moment a hardcoded interval is most wrong. Read it off each response and use it for the next sleep."),
 ("If my extra polls all come back 304, is there anything left to fix?",
  "The quota cost is gone, which is the expensive part, and what remains is real but small: connections, wakeups, log volume and a process that never idles. The stronger argument is that those requests cannot return anything new, because the feed is not regenerated faster than the floor. Aligning to the header costs nothing and removes a whole class of confusing behaviour, like a consumer that appears to poll twelve times faster than it reacts."),
 ("Does the events feed return everything that happened?",
  "No, and this is the trap at the slow end. The feed holds a bounded window of recent activity and does not replay beyond it, so an interval far above the floor can miss events outright rather than notice them late. If you need completeness rather than a recent sample, a webhook with a reconciliation pass is the right shape, not a longer poll."),
 ("Do the events endpoints support conditional requests?",
  "Yes, and you should use them alongside the interval, not instead of it. They answer with an etag, an unchanged page comes back 304, and a 304 does not count against the primary rate limit. The two mechanisms solve different halves: the ETag makes a repeat request cheap, and x-poll-interval tells you not to make it at all."),
 ("Is x-poll-interval only on the events endpoints?",
  "That is where it is documented and where it is reliably present. Other endpoints may not send it, which is why the script labels its fallback as an assumption rather than quietly presenting 60 as fact. If the header is absent, the honest position is that GitHub has not stated a floor for that endpoint and you should be conservative rather than confident."),
],
"related": [
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
 ("/github/polling-instead-of-webhooks/", "Polling for events a webhook would push"),
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
],
"citations": [CITE_EVENTS, CITE_BEST, CITE_CONDITIONAL, CITE_REST_LIMITS],
},

]
