#!/usr/bin/env python3
"""/github/ field notes, batch D — the writing.

Four rate-limit failures that are not the hourly quota. Three of them are
secondary limits, which are the least observable thing in the whole API: there
is no `x-ratelimit-*` bucket for them, `GET /rate_limit` reports primary quota
only, and the first and only signal is the 403 or 429 itself. The fourth is the
opposite kind of problem, and the nicest one in this section to write about,
because a conditional request that comes back `304 Not Modified` does not count
against the quota at all, which means the saving can be *measured* rather than
argued for.

Two constraints shape every script here. Secondary limits have no headroom API,
so nothing below claims to predict one: the scripts classify a throttled
response after the fact, measure the fan-out the client actually achieved, or
read the creation timestamps a bulk writer left behind. And this section is read
only, so where the repair is a POST, the script prints it.
"""

CITE_REST_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_BEST = ("Best practices for using the REST API — GitHub Docs",
             "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_RATE_ENDPOINT = ("Rate limit — GitHub REST API",
                      "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_TROUBLESHOOT = ("Troubleshooting the REST API — GitHub Docs",
                     "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_GETTING_STARTED = ("Getting started with the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api")
CITE_ISSUES = ("Issues — GitHub REST API",
               "https://docs.github.com/en/rest/issues/issues")
CITE_ISSUE_COMMENTS = ("Issue comments — GitHub REST API",
                       "https://docs.github.com/en/rest/issues/comments")
CITE_GRAPHQL_LIMITS = ("Rate limits and node limits for the GraphQL API — GitHub Docs",
                       "https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api")

GUIDES = [

{
"slug": "secondary-limit-concurrency",
"title": "Over 100 concurrent requests trips a secondary rate limit",
"description": "A fan-out of parallel GETs returns 403 while x-ratelimit-remaining still shows thousands left. That combination is the whole diagnosis.",
"h1": "over 100 concurrent requests trips a secondary rate limit",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github secondary rate limit", "you have exceeded a secondary rate limit",
             "github api 403 concurrent requests", "github api concurrency limit",
             "github api 429 retry-after"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Someone replaces a <code>for</code> loop with a <code>Promise.all</code> and the job goes from nine minutes to forty seconds, once. The next run returns <code>403</code> on two thirds of the requests. You check the quota, because a 403 from GitHub means the quota, and the quota says four thousand eight hundred requests left. Both numbers are true. They are about different limits.",
"short_answer": """<p>Read the body, not just the status. A <code>403</code> or <code>429</code> whose JSON message contains <code>"You have exceeded a secondary rate limit"</code> <strong>while <code>x-ratelimit-remaining</code> is still non-zero</strong> is a secondary limit. GitHub caps you at 100 concurrent requests across REST and GraphQL, and that cap is entirely separate from the hourly bucket.</p>
<p>There is no header for it. No <code>x-ratelimit-*</code> field tracks secondary limits and <code>GET /rate_limit</code> reports primary quota only, so nothing can tell you how close you are before you arrive. What a script <em>can</em> do is measure the concurrency your own client actually achieved, which is usually not the number you configured, and classify a throttled response correctly when one comes back.</p>""",
"problem": """<p>The parallel version works in development and fails in production, and the difference is not the code. It is that development ran it against six repositories and production runs it against six hundred, so the fan-out that peaked at six in flight now peaks at two hundred. Nothing in the code changed; the shape of the input did.</p>
<p>What makes this expensive to diagnose is that the error looks exactly like the one you already know how to fix. A <code>403</code> from GitHub with the word "rate" in it sends everyone to <code>GET /rate_limit</code>, which reports a healthy bucket, which makes the 403 look like a permissions problem instead, which sends the next hour into checking token scopes. The quota is fine. The scopes are fine. The client sent 200 requests at once.</p>
<p>And the failure is partial, which is worse than total. Some requests in the batch succeed, so the job completes and writes a result. The result is missing whatever the throttled requests would have contributed, and nothing marks it as incomplete.</p>""",
"why": """<p><strong>Secondary limits protect burst behaviour, not volume.</strong> The hourly bucket is about how much you ask for over an hour. Secondary limits are about how hard you ask at any instant: no more than 100 concurrent requests, no more than 900 points per minute on a single endpoint, no more than 90 seconds of CPU per 60 seconds of wall clock. A script can spend two hundred requests in one second and still have 4,800 of its 5,000 left.</p>
<p><strong>There is no headroom API, and that is the honest answer.</strong> This is the one place in these notes where detection genuinely cannot come first. No <code>x-ratelimit-*</code> header reports a secondary bucket, and <code>GET /rate_limit</code> documents itself as covering primary quota. A secondary limit becomes observable at the moment you exceed it and not one request before, so any tool that claims to warn you in advance is inferring, not measuring.</p>
<p><strong>The two limits are told apart by one field.</strong> On a primary exhaustion, <code>x-ratelimit-remaining</code> is <code>0</code>: that is what exhausted means. On a secondary limit it is whatever it was, usually thousands. So <em>403 with headroom</em> is the signature, and it is reliable enough to branch on even when the message wording changes.</p>
<p><strong>Your configured concurrency is not your actual concurrency.</strong> A pool of 50 workers against an endpoint that answers in 40 ms rarely has 50 requests in flight; a pool of 20 against an endpoint that answers in four seconds reliably does. The number that matters is the peak overlap of the request spans, and it is measurable from timestamps the client already has.</p>
<p><strong>Retrying immediately extends the window.</strong> The response carries <code>retry-after</code>. A client that treats the 403 as a generic transient error and retries in a second keeps the limit engaged, which is how a two-minute pause turns into a twenty-minute one.</p>""",
"steps": [
 {"h": "Read the body of the 403 before you read anything else",
  "body": """<p>GitHub returns JSON on every error. <code>{"message": "You have exceeded a secondary rate limit..."}</code> settles it immediately. A permissions 403 says <code>"Resource not accessible by integration"</code> or names a missing scope, and a primary exhaustion says <code>"API rate limit exceeded for user ID ..."</code>. Three different repairs, one status code.</p>"""},
 {"h": "Cross-check x-ratelimit-remaining on the same response",
  "body": """<p>The throttled response still carries the primary headers. If <code>x-ratelimit-remaining</code> is a large number and you were refused anyway, the refusal did not come from the bucket those headers describe. This check works even when the message wording is one you have not seen, which matters because the wording has changed before.</p>"""},
 {"h": "Measure the peak overlap your client actually reaches",
  "body": """<p>Record a start and end timestamp for every request and sweep them: the peak number of spans open at once is your real concurrency. Run this against a cheap endpoint at your production settings. <code>GET /rate_limit</code> is the right probe because it does not consume primary quota, so the measurement costs nothing except the requests themselves.</p>"""},
 {"h": "Bound the pool instead of fanning out over the input",
  "body": """<p><code>Promise.all(repos.map(fetch))</code> has a concurrency equal to <code>repos.length</code>, which is an input, not a setting. Replace it with a worker pool of a fixed small size &mdash; five to ten for reads is plenty, one for anything that writes &mdash; so the ceiling belongs to your code rather than to whoever added the six hundredth repository.</p>"""},
 {"h": "Honour retry-after and pause the whole pool, not one request",
  "body": """<p>When one request in a batch is throttled, every other request in that batch is about to be. Sleep <code>retry-after</code> seconds before resuming <em>anything</em>; where the header is absent, wait at least 60 seconds and then back off exponentially. Retrying the single failed item while the other 99 keep going is why the window never closes.</p>"""},
],
"verify": """<p>Re-run the probe at your production concurrency. The peak overlap should sit well under the ceiling and no response should classify as a secondary limit.</p>
<pre><code class="language-bash">python3 github_concurrency_probe.py --requests 24 --concurrency 6
# peak overlap 6 of a 100 ceiling, 0 throttled: clear</code></pre>""",
"code_intro": "The probe defaults to <code>GET /rate_limit</code>, which is the only endpoint in the API that does not spend what it measures. Two pure functions carry the diagnosis: one classifies a response into primary, secondary, permission or fine, and one sweeps request spans into a peak overlap. Neither touches the network, because both need to be exercised against responses you cannot conveniently produce on demand.",
"py_file": "github_concurrency_probe.py",
"py": '''"""Measure the concurrency a client actually reaches, and classify any throttling.

Read only. Every request is a GET, and the default probe endpoint is
GET /rate_limit, which does not count against the primary rate limit.

There is no API for secondary-limit headroom: no x-ratelimit-* field tracks one
and GET /rate_limit covers primary quota only. So this script does not predict a
secondary limit. It measures the fan-out this client reaches and reports
correctly if one fires.
"""
import argparse
import concurrent.futures
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_concurrency_probe")

API = "https://api.github.com"
UA = "github-concurrency-probe/1.0"

# Documented ceiling on requests in flight at once, across REST and GraphQL.
CONCURRENCY_CEILING = 100

# The wording has changed over the years, so match on the stable part of both
# the current phrasing and the one that predates it.
SECONDARY_MARKERS = ("secondary rate limit", "abuse detection")


def classify(status, body, headers):
    """Sort one response into primary, secondary, permission or fine. Pure.

    Returns (state, detail). The distinguishing field is x-ratelimit-remaining on
    the refused response itself: a primary exhaustion reports 0 there because that
    is what exhausted means, while a secondary limit leaves the primary bucket
    untouched. So "403 with headroom left" is the signature, and it still holds
    when the message wording is one this code has never seen.
    """
    lowered = {str(k).lower(): v for k, v in (headers or {}).items()}
    text = str(body or "").lower()
    try:
        remaining = int(lowered.get("x-ratelimit-remaining"))
    except (TypeError, ValueError):
        remaining = None

    try:
        status = int(status)
    except (TypeError, ValueError):
        status = 0

    if 200 <= status < 400:
        seen = "unknown" if remaining is None else str(remaining)
        return ("ok", "%d, primary bucket reports %s left" % (status, seen))
    if status not in (403, 429):
        return ("other", "%d is not a throttle at all" % status)

    if any(marker in text for marker in SECONDARY_MARKERS):
        return ("secondary",
                "%d and the body names a secondary rate limit. The hourly quota "
                "is not involved: it still reports %s remaining."
                % (status, "an unknown number" if remaining is None else remaining))
    if remaining == 0:
        return ("primary",
                "%d with x-ratelimit-remaining at 0. This is the hourly quota, "
                "not a secondary limit, and it clears at x-ratelimit-reset."
                % status)
    if remaining is not None and remaining > 0:
        return ("secondary-suspected",
                "%d while %d request(s) remain in the primary bucket. The body "
                "does not say secondary, but a refusal with headroom left did "
                "not come from the bucket these headers describe."
                % (status, remaining))
    return ("forbidden",
            "%d with no rate-limit headers to read. Treat this as permissions "
            "until something proves otherwise." % status)


def peak_overlap(spans):
    """Peak number of requests in flight at once, from (start, end) pairs. Pure.

    A sweep rather than a max of the pool size, because the pool size is a
    ceiling and this is the number that was actually reached. Twenty workers
    against a 40 ms endpoint rarely overlap; six against a four-second one
    always do.
    """
    events = []
    for span in spans or []:
        start, end = float(span[0]), float(span[1])
        if end < start:
            start, end = end, start
        events.append((start, 1))
        events.append((end, -1))
    # A request that ended at the exact instant another began was never beside
    # it, so ends are ordered before starts at an equal timestamp.
    events.sort(key=lambda e: (e[0], e[1]))
    peak = current = 0
    for _, delta in events:
        current += delta
        if current > peak:
            peak = current
    return peak


def verdict(peak, states, ceiling=CONCURRENCY_CEILING):
    """Turn a peak overlap and a list of response states into a finding. Pure.

    "clear" deliberately does not say the client is safe. Nothing can say that:
    the limit has no headroom API, so a probe that did not trip it has shown
    only that this run, at this moment, did not trip it.
    """
    throttled = [s for s in (states or []) if s in ("secondary", "secondary-suspected")]
    if throttled:
        return ("tripped",
                "%d of %d response(s) were refused with the primary bucket still "
                "healthy. Peak overlap was %d. Bound the pool and honour "
                "retry-after." % (len(throttled), len(states or []), peak))
    if peak >= ceiling:
        return ("over-ceiling",
                "peak overlap %d at or above the documented ceiling of %d. This "
                "run happened not to be refused; a slower endpoint or a busier "
                "moment will be." % (peak, ceiling))
    if peak >= ceiling * 0.8:
        return ("near-ceiling",
                "peak overlap %d against a ceiling of %d. One more worker or one "
                "slow response is the difference." % (peak, ceiling))
    return ("clear",
            "peak overlap %d of a %d ceiling, nothing throttled. This proves the "
            "run was fine, not that the client is: secondary limits have no "
            "headroom API to check against." % (peak, ceiling))


def probe(session, url, index):
    """One timed GET. Returns a record; never raises, because a failed request
    is data here rather than an error."""
    start = time.monotonic()
    try:
        r = session.get(url, timeout=30)
        end = time.monotonic()
        return {"i": index, "start": start, "end": end, "status": r.status_code,
                "body": r.text[:400], "headers": dict(r.headers)}
    except requests.RequestException as exc:
        return {"i": index, "start": start, "end": time.monotonic(), "status": 0,
                "body": str(exc), "headers": {}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--endpoint", default="/rate_limit",
                    help="path to probe (default /rate_limit, which is free)")
    ap.add_argument("--requests", type=int, default=12,
                    help="how many GETs to issue in total")
    ap.add_argument("--concurrency", type=int, default=6,
                    help="worker pool size; the ceiling, not the achieved peak")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    workers = max(1, min(args.concurrency, CONCURRENCY_CEILING))
    if workers != args.concurrency:
        log.warning("clamping concurrency to %d: going past the documented "
                    "ceiling on purpose spends a shared quota to learn nothing "
                    "new", workers)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    url = API + args.endpoint if args.endpoint.startswith("/") else args.endpoint
    log.info("probing %s: %d request(s), pool of %d", url, args.requests, workers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda i: probe(session, url, i),
                                range(max(1, args.requests))))

    states = []
    for r in sorted(results, key=lambda r: r["i"]):
        state, detail = classify(r["status"], r["body"], r["headers"])
        states.append(state)
        if state in ("ok", "other"):
            log.debug("request %d: %s %s", r["i"], state, detail)
        else:
            log.warning("request %d: %-20s %s", r["i"], state, detail)
            retry_after = {k.lower(): v for k, v in r["headers"].items()}.get("retry-after")
            if retry_after:
                log.warning("  retry-after: %s second(s). Pause the whole pool "
                            "for that long, not just this request.", retry_after)

    peak = peak_overlap([(r["start"], r["end"]) for r in results])
    state, detail = verdict(peak, states)
    log.info("%s: %s", state, detail)

    if state != "clear":
        log.info("repair: replace the fan-out with a bounded pool. Python: "
                 "ThreadPoolExecutor(max_workers=6). Node: a queue of 6 rather "
                 "than Promise.all over the whole input list.")
        log.info("repair: on a throttled response sleep retry-after seconds "
                 "before resuming any worker, and where the header is absent "
                 "wait 60 seconds and then back off exponentially.")

    print(json.dumps({"peak_overlap": peak, "ceiling": CONCURRENCY_CEILING,
                      "requests": len(results), "state": state,
                      "states": states}, indent=2))
    return 1 if state in ("tripped", "over-ceiling") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-concurrency-probe.mjs",
"js": '''/**
 * Measure the concurrency a client actually reaches, and classify any throttling.
 *
 * Read only. Every request is a GET, and the default probe endpoint is
 * GET /rate_limit, which does not count against the primary rate limit.
 *
 * Secondary limits have no headroom API, so nothing here predicts one.
 */
const API = 'https://api.github.com';
const UA = 'github-concurrency-probe/1.0';

// Documented ceiling on requests in flight at once, across REST and GraphQL.
export const CONCURRENCY_CEILING = 100;

// The wording has changed over the years; match the stable part of both forms.
const SECONDARY_MARKERS = ['secondary rate limit', 'abuse detection'];

/**
 * Sort one response into primary, secondary, permission or fine. Pure.
 * The distinguishing field is x-ratelimit-remaining on the refused response:
 * a primary exhaustion reports 0, a secondary limit leaves the bucket alone.
 */
export function classify(status, body, headers) {
  const lowered = {};
  for (const [k, v] of Object.entries(headers ?? {})) lowered[k.toLowerCase()] = v;
  const text = String(body ?? '').toLowerCase();
  const rawRemaining = lowered['x-ratelimit-remaining'];
  const parsed = Number.parseInt(rawRemaining, 10);
  const remaining = Number.isFinite(parsed) ? parsed : null;
  const code = Number.parseInt(status, 10) || 0;

  if (code >= 200 && code < 400) {
    return ['ok', `${code}, primary bucket reports ${remaining ?? 'unknown'} left`];
  }
  if (code !== 403 && code !== 429) return ['other', `${code} is not a throttle at all`];

  if (SECONDARY_MARKERS.some((m) => text.includes(m))) {
    return ['secondary',
      `${code} and the body names a secondary rate limit. The hourly quota is ` +
      `not involved: it still reports ${remaining ?? 'an unknown number'} remaining.`];
  }
  if (remaining === 0) {
    return ['primary',
      `${code} with x-ratelimit-remaining at 0. This is the hourly quota, not a ` +
      'secondary limit, and it clears at x-ratelimit-reset.'];
  }
  if (remaining !== null && remaining > 0) {
    return ['secondary-suspected',
      `${code} while ${remaining} request(s) remain in the primary bucket. The ` +
      'body does not say secondary, but a refusal with headroom left did not ' +
      'come from the bucket these headers describe.'];
  }
  return ['forbidden',
    `${code} with no rate-limit headers to read. Treat this as permissions ` +
    'until something proves otherwise.'];
}

/**
 * Peak number of requests in flight at once, from [start, end] pairs. Pure.
 * A sweep, because the pool size is a ceiling and this is what was reached.
 */
export function peakOverlap(spans) {
  const events = [];
  for (const span of spans ?? []) {
    let start = Number(span[0]);
    let end = Number(span[1]);
    if (end < start) [start, end] = [end, start];
    events.push([start, 1], [end, -1]);
  }
  // Ends sort before starts at an equal timestamp: a request that ended as
  // another began was never beside it.
  events.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  let peak = 0;
  let current = 0;
  for (const [, delta] of events) {
    current += delta;
    if (current > peak) peak = current;
  }
  return peak;
}

/**
 * Turn a peak overlap and a list of response states into a finding. Pure.
 * "clear" says this run was fine, never that the client is: the limit has no
 * headroom API to check against.
 */
export function verdict(peak, states, ceiling = CONCURRENCY_CEILING) {
  const list = states ?? [];
  const throttled = list.filter((s) => s === 'secondary' || s === 'secondary-suspected');
  if (throttled.length) {
    return ['tripped',
      `${throttled.length} of ${list.length} response(s) were refused with the ` +
      `primary bucket still healthy. Peak overlap was ${peak}. Bound the pool ` +
      'and honour retry-after.'];
  }
  if (peak >= ceiling) {
    return ['over-ceiling',
      `peak overlap ${peak} at or above the documented ceiling of ${ceiling}. ` +
      'This run happened not to be refused; a slower endpoint or a busier ' +
      'moment will be.'];
  }
  if (peak >= ceiling * 0.8) {
    return ['near-ceiling',
      `peak overlap ${peak} against a ceiling of ${ceiling}. One more worker or ` +
      'one slow response is the difference.'];
  }
  return ['clear',
    `peak overlap ${peak} of a ${ceiling} ceiling, nothing throttled. This ` +
    'proves the run was fine, not that the client is: secondary limits have no ' +
    'headroom API to check against.'];
}

async function probe(token, url, index) {
  const start = performance.now() / 1000;
  try {
    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': UA,
      },
    });
    const body = (await res.text()).slice(0, 400);
    const headers = Object.fromEntries(res.headers.entries());
    return { i: index, start, end: performance.now() / 1000, status: res.status, body, headers };
  } catch (err) {
    return {
      i: index, start, end: performance.now() / 1000, status: 0,
      body: err.message, headers: {},
    };
  }
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const endpoint = process.argv[2] ?? '/rate_limit';
  const total = Math.max(1, Number.parseInt(process.argv[3] ?? '12', 10) || 12);
  const wanted = Number.parseInt(process.argv[4] ?? '6', 10) || 6;
  const workers = Math.max(1, Math.min(wanted, CONCURRENCY_CEILING));
  const url = endpoint.startsWith('/') ? API + endpoint : endpoint;

  console.log(`probing ${url}: ${total} request(s), pool of ${workers}`);

  // A queue, not Promise.all over the input: the whole point of the note is
  // that Promise.all borrows its concurrency from the length of the list.
  const results = [];
  let next = 0;
  await Promise.all(Array.from({ length: workers }, async () => {
    while (next < total) {
      const index = next;
      next += 1;
      results.push(await probe(token, url, index));
    }
  }));

  const states = [];
  for (const r of results.sort((a, b) => a.i - b.i)) {
    const [state, detail] = classify(r.status, r.body, r.headers);
    states.push(state);
    if (state !== 'ok' && state !== 'other') {
      console.warn(`request ${r.i}: ${state.padEnd(20)} ${detail}`);
      const lowered = {};
      for (const [k, v] of Object.entries(r.headers)) lowered[k.toLowerCase()] = v;
      if (lowered['retry-after']) {
        console.warn(`  retry-after: ${lowered['retry-after']} second(s). Pause ` +
          'the whole pool for that long, not just this request.');
      }
    }
  }

  const peak = peakOverlap(results.map((r) => [r.start, r.end]));
  const [state, detail] = verdict(peak, states);
  console.log(`${state}: ${detail}`);

  if (state !== 'clear') {
    console.log('repair: replace the fan-out with a bounded queue of 6 rather ' +
      'than Promise.all over the whole input list.');
    console.log('repair: on a throttled response sleep retry-after seconds ' +
      'before resuming any worker; where the header is absent wait 60 seconds ' +
      'and then back off exponentially.');
  }

  console.log(JSON.stringify({
    peak_overlap: peak, ceiling: CONCURRENCY_CEILING,
    requests: results.length, state, states,
  }, null, 2));
  process.exitCode = (state === 'tripped' || state === 'over-ceiling') ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones the API deliberately makes ambiguous. A 403 with headroom left and a 403 with an empty bucket are the same status code and opposite repairs. A 403 with no rate-limit headers at all is neither, and calling it a secondary limit sends someone to add backoff to a permissions problem. And the overlap sweep has one edge that decides whether the number means anything: a request that ends exactly when the next begins was never in flight beside it.",
"test_py_file": "test_github_concurrency_probe.py",
"test_py": '''from github_concurrency_probe import classify, peak_overlap, verdict

SECONDARY = ('{"message":"You have exceeded a secondary rate limit. '
             'Please wait a few minutes before you try again."}')
PRIMARY = '{"message":"API rate limit exceeded for user ID 12345."}'
DENIED = '{"message":"Resource not accessible by integration"}'


def headers(remaining=4800, **extra):
    h = {"X-RateLimit-Limit": "5000", "X-RateLimit-Used": str(5000 - remaining)}
    if remaining is not None:
        h["X-RateLimit-Remaining"] = str(remaining)
    h.update(extra)
    return h


def test_a_secondary_limit_is_named_in_the_body():
    state, detail = classify(403, SECONDARY, headers(4800))
    assert state == "secondary"
    assert "4800" in detail


def test_the_same_message_on_a_429_classifies_identically():
    assert classify(429, SECONDARY, headers(4800))[0] == "secondary"


def test_an_empty_bucket_is_the_primary_quota_not_a_secondary_limit():
    state, detail = classify(403, PRIMARY, headers(0))
    assert state == "primary"
    assert "x-ratelimit-reset" in detail


def test_headroom_left_is_enough_to_suspect_a_secondary_limit():
    # The wording has changed before, so the fallback must not need it.
    state, detail = classify(403, '{"message":"Something new"}', headers(4321))
    assert state == "secondary-suspected"
    assert "4321" in detail


def test_a_403_with_no_rate_limit_headers_is_a_permissions_problem():
    state, _ = classify(403, DENIED, {})
    assert state == "forbidden"


def test_header_case_does_not_change_the_verdict():
    lower = {"x-ratelimit-remaining": "0"}
    assert classify(403, PRIMARY, lower)[0] == "primary"


def test_a_404_is_not_a_throttle():
    assert classify(404, '{"message":"Not Found"}', headers())[0] == "other"


def test_a_success_is_reported_with_its_headroom():
    state, detail = classify(200, "{}", headers(4999))
    assert state == "ok"
    assert "4999" in detail


def test_overlap_of_sequential_requests_is_one():
    assert peak_overlap([(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]) == 1


def test_overlap_counts_only_spans_open_at_the_same_instant():
    assert peak_overlap([(0.0, 3.0), (1.0, 2.0), (1.5, 4.0)]) == 3
    assert peak_overlap([(0.0, 1.0), (0.5, 2.0)]) == 2


def test_an_empty_probe_has_no_overlap():
    assert peak_overlap([]) == 0
    assert peak_overlap(None) == 0


def test_a_reversed_span_is_still_measured():
    assert peak_overlap([(2.0, 0.0), (1.0, 1.5)]) == 2


def test_any_throttled_response_beats_a_low_peak():
    state, detail = verdict(3, ["ok", "secondary", "ok"])
    assert state == "tripped"
    assert "1 of 3" in detail


def test_a_peak_at_the_ceiling_is_reported_even_when_nothing_failed():
    state, _ = verdict(100, ["ok"] * 100)
    assert state == "over-ceiling"
    assert verdict(85, ["ok"])[0] == "near-ceiling"


def test_clear_does_not_claim_the_client_is_safe():
    state, detail = verdict(6, ["ok", "ok"])
    assert state == "clear"
    assert "headroom API" in detail
''',
"test_js_file": "github-concurrency-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, peakOverlap, verdict } from './github-concurrency-probe.mjs';

const SECONDARY = '{"message":"You have exceeded a secondary rate limit. ' +
  'Please wait a few minutes before you try again."}';
const PRIMARY = '{"message":"API rate limit exceeded for user ID 12345."}';
const DENIED = '{"message":"Resource not accessible by integration"}';

const headers = (remaining = 4800, extra = {}) => ({
  'X-RateLimit-Limit': '5000',
  'X-RateLimit-Used': String(5000 - remaining),
  'X-RateLimit-Remaining': String(remaining),
  ...extra,
});

test('a secondary limit is named in the body', () => {
  const [state, detail] = classify(403, SECONDARY, headers(4800));
  assert.equal(state, 'secondary');
  assert.match(detail, /4800/);
});

test('the same message on a 429 classifies identically', () => {
  assert.equal(classify(429, SECONDARY, headers(4800))[0], 'secondary');
});

test('an empty bucket is the primary quota, not a secondary limit', () => {
  const [state, detail] = classify(403, PRIMARY, headers(0));
  assert.equal(state, 'primary');
  assert.match(detail, /x-ratelimit-reset/);
});

test('headroom left is enough to suspect a secondary limit', () => {
  const [state, detail] = classify(403, '{"message":"Something new"}', headers(4321));
  assert.equal(state, 'secondary-suspected');
  assert.match(detail, /4321/);
});

test('a 403 with no rate-limit headers is a permissions problem', () => {
  assert.equal(classify(403, DENIED, {})[0], 'forbidden');
});

test('header case does not change the verdict', () => {
  assert.equal(classify(403, PRIMARY, { 'x-ratelimit-remaining': '0' })[0], 'primary');
});

test('a 404 is not a throttle', () => {
  assert.equal(classify(404, '{"message":"Not Found"}', headers())[0], 'other');
});

test('a success is reported with its headroom', () => {
  const [state, detail] = classify(200, '{}', headers(4999));
  assert.equal(state, 'ok');
  assert.match(detail, /4999/);
});

test('overlap of sequential requests is one', () => {
  assert.equal(peakOverlap([[0, 1], [1, 2], [2, 3]]), 1);
});

test('overlap counts only spans open at the same instant', () => {
  assert.equal(peakOverlap([[0, 3], [1, 2], [1.5, 4]]), 3);
  assert.equal(peakOverlap([[0, 1], [0.5, 2]]), 2);
});

test('an empty probe has no overlap', () => {
  assert.equal(peakOverlap([]), 0);
  assert.equal(peakOverlap(null), 0);
});

test('a reversed span is still measured', () => {
  assert.equal(peakOverlap([[2, 0], [1, 1.5]]), 2);
});

test('any throttled response beats a low peak', () => {
  const [state, detail] = verdict(3, ['ok', 'secondary', 'ok']);
  assert.equal(state, 'tripped');
  assert.match(detail, /1 of 3/);
});

test('a peak at the ceiling is reported even when nothing failed', () => {
  assert.equal(verdict(100, new Array(100).fill('ok'))[0], 'over-ceiling');
  assert.equal(verdict(85, ['ok'])[0], 'near-ceiling');
});

test('clear does not claim the client is safe', () => {
  const [state, detail] = verdict(6, ['ok', 'ok']);
  assert.equal(state, 'clear');
  assert.match(detail, /headroom API/);
});
''',
"faq": [
 ("Can I check how close I am to a secondary rate limit before I hit one?",
  "No, and this is worth being blunt about. There is no x-ratelimit-* header for secondary limits and GET /rate_limit documents itself as reporting primary quota only. A secondary limit becomes observable at the moment you exceed it, in the body of the 403 or 429 and in the retry-after header on it. Anything that claims to show you secondary headroom is inferring from your own request pattern, not reading a number GitHub published."),
 ("Why does x-ratelimit-remaining still show thousands when I am being refused?",
  "Because it is describing a different limit. The hourly bucket counts requests over an hour; the secondary limits count bursts, concurrency and CPU time. You can spend two hundred requests in one second and still hold 4,800 of your 5,000. That mismatch is not a bug in the headers, it is the single most reliable way to tell the two failures apart, which is why the classifier branches on it."),
 ("Does GraphQL have its own concurrency allowance?",
  "No. The 100-concurrent-request ceiling is shared across REST and GraphQL, even though the two have entirely separate primary buckets. A job that runs REST calls and GraphQL queries in parallel is spending one concurrency budget from two places, which is a common way to trip this while both point counters look healthy."),
 ("Is the probe safe to run against production credentials?",
  "It only issues GETs, and its default endpoint is GET /rate_limit, which does not count against the primary rate limit. The concurrency argument is clamped at the documented ceiling, because deliberately exceeding it spends a quota that is shared with every other process using that token in order to learn something the documentation already states."),
 ("What concurrency should I actually use?",
  "Lower than you think, and fixed rather than derived from the input. Five to ten in flight is comfortable for reads and leaves room for whatever else holds the same token; anything that creates content should be serialised to one at a time with a pause between items. The important change is not the number, it is that the number stops being repos.length."),
],
"related": [
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
 ("/github/secondary-limit-content-creation/", "Bulk creation exceeds 80 a minute"),
 ("/github/per-page-default-30/", "per_page is unset so every list costs more"),
],
"citations": [CITE_REST_LIMITS, CITE_BEST, CITE_RATE_ENDPOINT, CITE_TROUBLESHOOT],
},


{
"slug": "secondary-limit-content-creation",
"title": "Bulk issue or comment creation exceeds 80 requests a minute",
"description": "Content-generating requests get 80 a minute and 500 an hour, separately from the quota. A migration runs clean for 80 items and then 403s on every one.",
"h1": "bulk issue or comment creation exceeds 80 requests a minute",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github secondary rate limit creating issues",
             "github api 403 creating comments", "github bulk create issues rate limit",
             "github content creation limit 80", "github migration rate limited"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The migration script imports 2,400 issues from the old tracker. It gets through about eighty of them, then every remaining call comes back <code>403</code>. You check the quota and there are 4,900 requests left in it. The limit that stopped you is not counting requests. It is counting the things you created.",
"short_answer": """<p>Content-generating requests &mdash; anything that creates an issue, a comment, a commit, a pull request &mdash; are capped at roughly <strong>80 per minute and 500 per hour</strong>, and that cap is separate from the hourly quota. A single issue created with a body and three labels can bill as more than one content-generating request, so the practical ceiling is lower than 80 items.</p>
<p>You cannot ask the API how much of that allowance you have left; it has no bucket. What you <em>can</em> read is what a previous run left behind. List issues and issue comments sorted by creation time and slide a 60-second window over the timestamps, grouped by author. A dense burst by one account is the fingerprint of a writer that will trip this again the next time it runs.</p>""",
"problem": """<p>This one always arrives during a migration, a backfill or a bot's first busy day, which is exactly when nobody has a baseline to compare against. The job is new, so a partial failure looks like a bug in the job. The status code is 403, so the first hour goes into token scopes. The quota is untouched, so the second hour goes into wondering why the quota is untouched.</p>
<p>Then the retry logic makes it worse. A queue that retries the individual failed item immediately keeps issuing content-generating requests into an engaged limit, which extends the window. The job ends up in a stable failure mode where it retries forever, creates nothing, and looks busy the entire time.</p>
<p>The residue is the part nobody plans for. A migration that got 80 issues in before it stopped has created 80 real issues, and re-running it from the top creates them again. The limit turns a clean re-runnable job into a partially applied one, and the API will not tell you where it stopped &mdash; the issues it created are the only record.</p>""",
"why": """<p><strong>Creation is metered separately from reading.</strong> The hourly bucket does not distinguish a <code>GET</code> from a write. The content-creation limit does: it exists so that one account cannot manufacture thousands of notifications, emails and timeline entries in a minute. Reads pass through it untouched, which is why a job that reads 5,000 times and writes 100 times fails on the hundred.</p>
<p><strong>One item is not one request.</strong> The billing is per content-generating request, not per object you think you created. An issue with a body, then labels, then an assignee is several. A comment that triggers a mention is doing more work than the single call suggests. So a job pacing itself at 79 items a minute can still be over the limit.</p>
<p><strong>There is no bucket to read, so detection has to be indirect.</strong> This is a secondary limit, and secondary limits publish nothing: no <code>x-ratelimit-*</code> field, nothing in <code>GET /rate_limit</code>. The only pre-emptive evidence available to a read-only script is the shape of what has already been created, which is genuinely informative because bulk writers leave an unmistakable timestamp signature that human activity never produces.</p>
<p><strong>The hourly ceiling catches the jobs that dodge the per-minute one.</strong> Pacing to 60 a minute feels safe and is still 3,600 an hour, seven times the hourly content allowance. A job that respects one limit and not the other fails later and more confusingly, roughly eight minutes in rather than at the start.</p>
<p><strong>The response tells you how long to wait and it usually gets ignored.</strong> A content-creation 403 carries <code>retry-after</code>. Treating it as a signal to pause the whole queue is the difference between a job that finishes late and a job that never finishes.</p>""",
"steps": [
 {"h": "List what has already been created, newest first",
  "body": """<p><code>GET /repos/{owner}/{repo}/issues?state=all&amp;sort=created&amp;direction=desc&amp;per_page=100</code> and <code>GET /repos/{owner}/{repo}/issues/comments?sort=created&amp;direction=desc&amp;per_page=100</code>. Both are ordinary reads billed to the core bucket. Note that the issues endpoint returns pull requests too, which is correct here: a pull request is also content that was created.</p>"""},
 {"h": "Group by author before you count anything",
  "body": """<p>The limit is per account. Forty issues in a minute across a busy repository during a triage session is normal; forty in a minute from one login is a script. Bucket on <code>user.login</code> and keep <code>user.type</code>, because <code>Bot</code> settles the question of whether a burst was a person.</p>"""},
 {"h": "Slide a 60-second and a 3,600-second window over the timestamps",
  "body": """<p>A sorted list of <code>created_at</code> values and two pointers gives the densest minute and the densest hour per author. Compare those against 80 and 500. This is the whole detection: everything else is presentation.</p>"""},
 {"h": "Pace the writer well under both ceilings",
  "body": """<p>Aim for one content-generating request per second and no more than about 300 an hour, which leaves room for the requests you did not count. Sleep between items rather than relying on the network being slow; the day the API gets faster is the day the job starts failing.</p>"""},
 {"h": "Pause the queue on retry-after, and make the job resumable",
  "body": """<p>On a 403 with <code>retry-after</code>, stop every worker for that many seconds instead of retrying the one item. Then give the job a record of what it has already created &mdash; an external id in the issue body, a checkpoint file &mdash; so that resuming after a throttle does not duplicate the first eighty.</p>"""},
],
"verify": """<p>Re-run the audit after the writer has been paced. The densest minute for the bot account should sit far below 80, and the report should say so per author rather than for the repository as a whole.</p>
<pre><code class="language-bash">python3 github_content_burst_audit.py --repo acme/api
# migrator-bot: densest minute 12, densest hour 214: clear</code></pre>""",
"code_intro": "Two list endpoints, both plain reads, and the rest is arithmetic on timestamps. The sliding window is a pure function so the tests can hand it a synthetic burst instead of waiting for one, and the verdict takes <code>now</code> as an argument so that \"this happened four minutes ago\" is reproducible rather than dependent on when the suite runs.",
"py_file": "github_content_burst_audit.py",
"py": '''"""Find bursts of created issues and comments that will trip the content limit.

Read only. Every request is a GET, and the repair is printed rather than run.

Content-generating requests are capped at about 80 a minute and 500 an hour,
separately from the hourly quota, and no API reports how much of that allowance
is left. So this looks at the evidence a bulk writer leaves behind: the density
of created_at timestamps for a single account.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_content_burst_audit")

API = "https://api.github.com"
UA = "github-content-burst-audit/1.0"

# Documented content-creation ceilings. Both are approximate on GitHub's side and
# neither is exposed as a bucket, which is why they are constants here.
MINUTE_LIMIT = 80
HOUR_LIMIT = 500

# A burst whose newest item is inside this many seconds of now is still running,
# which changes the advice from "pace it before next time" to "stop it".
LIVE_SECONDS = 900


def parse_ts(value):
    """ISO 8601 to epoch seconds, or None. Pure.

    GitHub always sends UTC with a trailing Z. A value that parses without a
    timezone is still treated as UTC rather than as local time, because reading
    the same log on two machines must not produce two different answers.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp()


def peak_rate(times, window):
    """Most timestamps falling inside any window of that many seconds. Pure.

    Two pointers over a sorted list. Returns (count, ending_at) so the caller can
    say when the densest stretch was, which is what turns a number into something
    someone can go and look at.
    """
    values = sorted(t for t in (times or []) if t is not None)
    peak, at, start = 0, None, 0
    for end in range(len(values)):
        while values[end] - values[start] >= window:
            start += 1
        count = end - start + 1
        if count > peak:
            peak, at = count, values[end]
    return (peak, at)


def by_actor(items):
    """Group created_at timestamps by the login that created them. Pure.

    The limit is per account, so a repository-wide count is the wrong number:
    thirty issues in a minute from thirty people is a triage session, and thirty
    from one login is a script that is about to be throttled.
    """
    out = {}
    for item in items or []:
        user = item.get("user") or {}
        login = str(user.get("login") or "unknown")
        when = parse_ts(item.get("created_at"))
        if when is None:
            continue
        bucket = out.setdefault(login, {"times": [], "type": user.get("type") or "User"})
        bucket["times"].append(when)
    return out


def verdict(peak_minute, peak_hour, last_seen, now):
    """Classify one account's creation pattern. Pure. Returns (state, detail).

    now is a parameter rather than a call to time.time() so the same input always
    produces the same output, and so the tests can put a burst four minutes in the
    past without sleeping for four minutes.
    """
    if not peak_minute:
        return ("quiet", "nothing created in the window that was read")

    age = None if last_seen is None else max(0.0, float(now) - float(last_seen))
    when = ("still running" if age is not None and age < LIVE_SECONDS
            else "already finished" if age is not None
            else "at an unknown time")
    tail = ", %s (newest item %d minute(s) ago)" % (when, int((age or 0) // 60))

    if peak_minute >= MINUTE_LIMIT:
        return ("over-minute",
                "%d created inside one minute against a ceiling of %d. This "
                "account has already been throttled or is about to be%s"
                % (peak_minute, MINUTE_LIMIT, tail))
    if peak_hour >= HOUR_LIMIT:
        return ("over-hour",
                "%d created inside one hour against a ceiling of %d. Pacing "
                "under the per-minute limit is not enough on its own%s"
                % (peak_hour, HOUR_LIMIT, tail))
    if peak_minute >= MINUTE_LIMIT * 0.8:
        return ("near-minute",
                "%d in a minute, %d%% of the ceiling. One issue billed as two "
                "requests puts this over%s"
                % (peak_minute, int(100 * peak_minute / MINUTE_LIMIT), tail))
    if peak_hour >= HOUR_LIMIT * 0.8:
        return ("near-hour",
                "%d in an hour, %d%% of the ceiling. The per-minute rate is fine "
                "and the sustained rate is not%s"
                % (peak_hour, int(100 * peak_hour / HOUR_LIMIT), tail))
    return ("clear",
            "densest minute %d, densest hour %d, both well under %d and %d"
            % (peak_minute, peak_hour, MINUTE_LIMIT, HOUR_LIMIT))


def next_link(response):
    """The rel=next URL from the Link header, or None."""
    for part in (response.headers.get("Link") or "").split(","):
        chunk = part.strip()
        if chunk.startswith("<") and chunk.endswith('rel="next"'):
            return chunk[1:chunk.index(">")]
    return None


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, expired or "
                         "malformed")
    if r.status_code in (403, 404):
        raise SystemExit("%d from %s: this needs read access to the repository's "
                         "issues. GitHub answers 404 rather than 403 when a "
                         "token cannot see a resource at all."
                         % (r.status_code, url))
    r.raise_for_status()
    return r


def page(session, url, limit, **params):
    out = []
    while url and len(out) < limit:
        r = get(session, url, **params)
        out.extend(r.json())
        url, params = next_link(r), {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--max-items", type=int, default=600,
                    help="stop paging each list after this many items")
    ap.add_argument("--actor", default=None,
                    help="only report this login (default: every author found)")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    owner, _, name = args.repo.partition("/")
    if not (owner and name):
        log.error("--repo takes owner/name, for example acme/api")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    base = "%s/repos/%s/%s" % (API, owner, name)
    items = page(session, base + "/issues", args.max_items, state="all",
                 sort="created", direction="desc", per_page=100)
    items += page(session, base + "/issues/comments", args.max_items,
                  sort="created", direction="desc", per_page=100)
    log.info("read %d issue(s), pull request(s) and comment(s) on %s",
             len(items), args.repo)

    now = datetime.now(timezone.utc).timestamp()
    findings = 0
    actors = by_actor(items)
    for login, bucket in sorted(actors.items(),
                                key=lambda kv: -len(kv[1]["times"])):
        if args.actor and login != args.actor:
            continue
        times = bucket["times"]
        peak_minute, minute_at = peak_rate(times, 60)
        peak_hour, _ = peak_rate(times, 3600)
        state, detail = verdict(peak_minute, peak_hour,
                                max(times) if times else None, now)
        line = "%s (%s): %s" % (login, bucket["type"], detail)
        if state in ("clear", "quiet"):
            log.info(line)
            continue
        findings += 1
        log.warning(line)
        if minute_at:
            log.warning("  densest minute ended at %s",
                        datetime.fromtimestamp(minute_at, timezone.utc).isoformat())
        log.warning("  repair: pace this writer to one creating request per "
                    "second and under 300 an hour, sleeping between items "
                    "rather than relying on the network being slow.")
        log.warning("  repair: on a 403 carrying retry-after, pause every "
                    "worker for that many seconds instead of retrying the one "
                    "item, and checkpoint what was created so a resume does "
                    "not duplicate it.")

    log.info("%d author(s) examined, %d over or near a content-creation ceiling",
             len(actors) if not args.actor else 1, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-content-burst-audit.mjs",
"js": '''/**
 * Find bursts of created issues and comments that will trip the content limit.
 *
 * Read only. Every request is a GET, and the repair is printed rather than run.
 *
 * Content-generating requests are capped at about 80 a minute and 500 an hour,
 * separately from the hourly quota, and no API reports the remaining allowance.
 */
const API = 'https://api.github.com';
const UA = 'github-content-burst-audit/1.0';

export const MINUTE_LIMIT = 80;
export const HOUR_LIMIT = 500;

// A burst whose newest item is inside this many seconds of now is still running.
const LIVE_SECONDS = 900;

/** ISO 8601 to epoch seconds, or null. Pure. */
export function parseTs(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isFinite(ms) ? ms / 1000 : null;
}

/**
 * Most timestamps falling inside any window of that many seconds. Pure.
 * Two pointers over a sorted list. Returns [count, endingAt].
 */
export function peakRate(times, window) {
  const values = (times ?? []).filter((t) => t !== null && t !== undefined)
    .map(Number).sort((a, b) => a - b);
  let peak = 0;
  let at = null;
  let start = 0;
  for (let end = 0; end < values.length; end += 1) {
    while (values[end] - values[start] >= window) start += 1;
    const count = end - start + 1;
    if (count > peak) { peak = count; at = values[end]; }
  }
  return [peak, at];
}

/**
 * Group created_at timestamps by the login that created them. Pure.
 * The limit is per account, so a repository-wide count is the wrong number.
 */
export function byActor(items) {
  const out = {};
  for (const item of items ?? []) {
    const user = item.user ?? {};
    const login = String(user.login ?? 'unknown');
    const when = parseTs(item.created_at);
    if (when === null) continue;
    const bucket = (out[login] ??= { times: [], type: user.type ?? 'User' });
    bucket.times.push(when);
  }
  return out;
}

/**
 * Classify one account's creation pattern. Pure. Returns [state, detail].
 * now is a parameter so the same input always produces the same output.
 */
export function verdict(peakMinute, peakHour, lastSeen, now) {
  if (!peakMinute) return ['quiet', 'nothing created in the window that was read'];

  const age = lastSeen === null || lastSeen === undefined
    ? null : Math.max(0, Number(now) - Number(lastSeen));
  const when = age === null ? 'at an unknown time'
    : age < LIVE_SECONDS ? 'still running' : 'already finished';
  const tail = `, ${when} (newest item ${Math.floor((age ?? 0) / 60)} minute(s) ago)`;

  if (peakMinute >= MINUTE_LIMIT) {
    return ['over-minute',
      `${peakMinute} created inside one minute against a ceiling of ${MINUTE_LIMIT}. ` +
      `This account has already been throttled or is about to be${tail}`];
  }
  if (peakHour >= HOUR_LIMIT) {
    return ['over-hour',
      `${peakHour} created inside one hour against a ceiling of ${HOUR_LIMIT}. ` +
      `Pacing under the per-minute limit is not enough on its own${tail}`];
  }
  if (peakMinute >= MINUTE_LIMIT * 0.8) {
    return ['near-minute',
      `${peakMinute} in a minute, ${Math.floor(100 * peakMinute / MINUTE_LIMIT)}% of ` +
      `the ceiling. One issue billed as two requests puts this over${tail}`];
  }
  if (peakHour >= HOUR_LIMIT * 0.8) {
    return ['near-hour',
      `${peakHour} in an hour, ${Math.floor(100 * peakHour / HOUR_LIMIT)}% of the ` +
      `ceiling. The per-minute rate is fine and the sustained rate is not${tail}`];
  }
  return ['clear',
    `densest minute ${peakMinute}, densest hour ${peakHour}, both well under ` +
    `${MINUTE_LIMIT} and ${HOUR_LIMIT}`];
}

function nextLink(res) {
  for (const part of (res.headers.get('link') ?? '').split(',')) {
    const chunk = part.trim();
    if (chunk.startsWith('<') && chunk.endsWith('rel="next"')) {
      return chunk.slice(1, chunk.indexOf('>'));
    }
  }
  return null;
}

async function get(token, url) {
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, expired or malformed');
  }
  if (res.status === 403 || res.status === 404) {
    throw new Error(`${res.status} from ${url}: this needs read access to the ` +
      "repository's issues. GitHub answers 404 rather than 403 when a token " +
      'cannot see a resource at all.');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url}`);
  return res;
}

async function page(token, url, limit) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const res = await get(token, next);
    out.push(...(await res.json()));
    next = nextLink(res);
  }
  return out.slice(0, limit);
}

async function main() {
  const repo = process.argv[2];
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  if (!repo || !repo.includes('/')) {
    console.error('usage: node github-content-burst-audit.mjs owner/name');
    process.exitCode = 2;
    return;
  }

  const base = `${API}/repos/${repo}`;
  const limit = 600;
  const items = [
    ...await page(token,
      `${base}/issues?state=all&sort=created&direction=desc&per_page=100`, limit),
    ...await page(token,
      `${base}/issues/comments?sort=created&direction=desc&per_page=100`, limit),
  ];
  console.log(`read ${items.length} issue(s), pull request(s) and comment(s) on ${repo}`);

  const now = Date.now() / 1000;
  const actors = byActor(items);
  let findings = 0;
  const ranked = Object.entries(actors).sort((a, b) => b[1].times.length - a[1].times.length);
  for (const [login, bucket] of ranked) {
    const [peakMinute, minuteAt] = peakRate(bucket.times, 60);
    const [peakHour] = peakRate(bucket.times, 3600);
    const lastSeen = bucket.times.length ? Math.max(...bucket.times) : null;
    const [state, detail] = verdict(peakMinute, peakHour, lastSeen, now);
    const line = `${login} (${bucket.type}): ${detail}`;
    if (state === 'clear' || state === 'quiet') { console.log(line); continue; }
    findings += 1;
    console.warn(line);
    if (minuteAt) {
      console.warn(`  densest minute ended at ${new Date(minuteAt * 1000).toISOString()}`);
    }
    console.warn('  repair: pace this writer to one creating request per second ' +
      'and under 300 an hour, sleeping between items rather than relying on the ' +
      'network being slow.');
    console.warn('  repair: on a 403 carrying retry-after, pause every worker ' +
      'for that many seconds instead of retrying the one item, and checkpoint ' +
      'what was created so a resume does not duplicate it.');
  }

  console.log(`${ranked.length} author(s) examined, ${findings} over or near a ` +
    'content-creation ceiling');
  process.exitCode = findings ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The sliding window is the only part of this that can be quietly wrong, and it is wrong in a way that reads as correct: an off-by-one at the window edge turns 80 items in a minute into 79 and reports clear on the exact case the note exists for. So the tests pin both edges. The verdict takes <code>now</code>, which means \"this burst is still running\" is a fact the suite can assert rather than a coincidence of when it ran.",
"test_py_file": "test_github_content_burst_audit.py",
"test_py": '''from github_content_burst_audit import by_actor, parse_ts, peak_rate, verdict

NOW = 1756512000.0  # 2025-08-30T00:00:00Z, so every case below is anchored.


def issue(login, created_at, kind="Bot"):
    return {"user": {"login": login, "type": kind}, "created_at": created_at}


def test_parse_ts_reads_githubs_z_suffix():
    assert parse_ts("2025-08-30T00:00:00Z") == NOW


def test_parse_ts_returns_none_rather_than_raising():
    assert parse_ts(None) is None
    assert parse_ts("") is None
    assert parse_ts("last tuesday") is None


def test_a_naive_timestamp_is_read_as_utc_not_as_local_time():
    # Two machines in two timezones must not disagree about the same log.
    assert parse_ts("2025-08-30T00:00:00") == NOW


def test_peak_rate_of_a_steady_trickle_is_one_per_window():
    times = [NOW + 120 * i for i in range(10)]
    peak, _ = peak_rate(times, 60)
    assert peak == 1


def test_peak_rate_finds_the_burst_and_says_when_it_ended():
    times = [NOW + i for i in range(90)] + [NOW + 10000]
    peak, at = peak_rate(times, 60)
    assert peak == 60
    assert at == NOW + 59


def test_the_window_edge_is_exclusive_so_a_full_minute_counts_once():
    assert peak_rate([NOW, NOW + 60], 60)[0] == 1
    assert peak_rate([NOW, NOW + 59.9], 60)[0] == 2


def test_peak_rate_of_nothing_is_zero():
    assert peak_rate([], 60) == (0, None)
    assert peak_rate(None, 60) == (0, None)


def test_by_actor_groups_per_login_and_keeps_the_account_type():
    grouped = by_actor([issue("bot", "2025-08-30T00:00:00Z"),
                        issue("bot", "2025-08-30T00:00:01Z"),
                        issue("person", "2025-08-30T00:00:02Z", "User")])
    assert sorted(grouped) == ["bot", "person"]
    assert len(grouped["bot"]["times"]) == 2
    assert grouped["person"]["type"] == "User"


def test_by_actor_drops_items_with_no_readable_timestamp():
    grouped = by_actor([issue("bot", None), issue("bot", "2025-08-30T00:00:00Z")])
    assert len(grouped["bot"]["times"]) == 1


def test_eighty_in_a_minute_is_the_finding():
    state, detail = verdict(80, 80, NOW, NOW)
    assert state == "over-minute"
    assert "still running" in detail


def test_a_burst_that_finished_hours_ago_is_reported_as_finished():
    state, detail = verdict(90, 90, NOW - 7200, NOW)
    assert state == "over-minute"
    assert "already finished" in detail
    assert "120 minute(s) ago" in detail


def test_a_gentle_rate_can_still_break_the_hourly_ceiling():
    # Ten a minute never trips the per-minute limit and is 600 an hour.
    state, detail = verdict(10, 600, NOW, NOW)
    assert state == "over-hour"
    assert "per-minute limit is not enough" in detail


def test_the_near_states_warn_before_the_ceiling():
    assert verdict(64, 64, NOW, NOW)[0] == "near-minute"
    assert verdict(10, 400, NOW, NOW)[0] == "near-hour"


def test_an_ordinary_repository_is_clear():
    state, _ = verdict(3, 40, NOW, NOW)
    assert state == "clear"


def test_no_activity_is_quiet_rather_than_clear():
    assert verdict(0, 0, None, NOW)[0] == "quiet"
''',
"test_js_file": "github-content-burst-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  byActor, parseTs, peakRate, verdict,
} from './github-content-burst-audit.mjs';

const NOW = 1756512000; // 2025-08-30T00:00:00Z, so every case below is anchored.

const issue = (login, created_at, type = 'Bot') => ({ user: { login, type }, created_at });

test('parseTs reads the Z suffix GitHub sends', () => {
  assert.equal(parseTs('2025-08-30T00:00:00Z'), NOW);
});

test('parseTs returns null rather than throwing', () => {
  assert.equal(parseTs(null), null);
  assert.equal(parseTs(''), null);
  assert.equal(parseTs('last tuesday'), null);
});

test('peakRate of a steady trickle is one per window', () => {
  const times = Array.from({ length: 10 }, (_, i) => NOW + 120 * i);
  assert.equal(peakRate(times, 60)[0], 1);
});

test('peakRate finds the burst and says when it ended', () => {
  const times = [...Array.from({ length: 90 }, (_, i) => NOW + i), NOW + 10000];
  const [peak, at] = peakRate(times, 60);
  assert.equal(peak, 60);
  assert.equal(at, NOW + 59);
});

test('the window edge is exclusive so a full minute counts once', () => {
  assert.equal(peakRate([NOW, NOW + 60], 60)[0], 1);
  assert.equal(peakRate([NOW, NOW + 59.9], 60)[0], 2);
});

test('peakRate of nothing is zero', () => {
  assert.deepEqual(peakRate([], 60), [0, null]);
  assert.deepEqual(peakRate(null, 60), [0, null]);
});

test('byActor groups per login and keeps the account type', () => {
  const grouped = byActor([
    issue('bot', '2025-08-30T00:00:00Z'),
    issue('bot', '2025-08-30T00:00:01Z'),
    issue('person', '2025-08-30T00:00:02Z', 'User'),
  ]);
  assert.deepEqual(Object.keys(grouped).sort(), ['bot', 'person']);
  assert.equal(grouped.bot.times.length, 2);
  assert.equal(grouped.person.type, 'User');
});

test('byActor drops items with no readable timestamp', () => {
  const grouped = byActor([issue('bot', null), issue('bot', '2025-08-30T00:00:00Z')]);
  assert.equal(grouped.bot.times.length, 1);
});

test('eighty in a minute is the finding', () => {
  const [state, detail] = verdict(80, 80, NOW, NOW);
  assert.equal(state, 'over-minute');
  assert.match(detail, /still running/);
});

test('a burst that finished hours ago is reported as finished', () => {
  const [state, detail] = verdict(90, 90, NOW - 7200, NOW);
  assert.equal(state, 'over-minute');
  assert.match(detail, /already finished/);
  assert.match(detail, /120 minute/);
});

test('a gentle rate can still break the hourly ceiling', () => {
  const [state, detail] = verdict(10, 600, NOW, NOW);
  assert.equal(state, 'over-hour');
  assert.match(detail, /per-minute limit is not enough/);
});

test('the near states warn before the ceiling', () => {
  assert.equal(verdict(64, 64, NOW, NOW)[0], 'near-minute');
  assert.equal(verdict(10, 400, NOW, NOW)[0], 'near-hour');
});

test('an ordinary repository is clear', () => {
  assert.equal(verdict(3, 40, NOW, NOW)[0], 'clear');
});

test('no activity is quiet rather than clear', () => {
  assert.equal(verdict(0, 0, null, NOW)[0], 'quiet');
});
''',
"faq": [
 ("Is the content-creation limit the same 5,000 requests an hour?",
  "No. It is a secondary limit and it is counted separately, which is why the quota looks untouched while every creation fails. Roughly 80 content-generating requests a minute and 500 an hour, against a primary bucket of 5,000 an hour that your reads are also drawing from. A job can exhaust one without moving the other at all."),
 ("Why did my job fail at 80 items when I paced it at 79 a minute?",
  "Because the unit is the request, not the item. Creating an issue and then adding labels and an assignee is several content-generating requests for one issue. Anything that fans out per item multiplies the same way. Pace to one request per second and count the requests you actually send, not the objects you meant to create."),
 ("Can the script tell me how much of the 80 I have left right now?",
  "No, and nothing can. Secondary limits publish no bucket: there is no x-ratelimit-* header for them and GET /rate_limit reports primary quota only. The script reads the timestamps of what has already been created, which is real evidence about a writer's behaviour but is history rather than headroom."),
 ("The audit flags a human with 40 issues in a minute. Is that a false positive?",
  "Check user.type and the shape of the burst. A person can open several issues quickly by pasting from a document, but 40 in 60 seconds is almost always a script running under someone's personal token, which is its own problem: the throttle then lands on that person's account and takes their interactive use down with it."),
 ("Does this apply to GraphQL mutations too?",
  "Yes, and more expensively. Mutations count against the secondary limits at a higher weight than a REST write, so a GraphQL batch that looks efficient in points can be tripping the content limit sooner than the equivalent REST calls. The pacing advice is the same and the ceiling arrives earlier."),
],
"related": [
 ("/github/secondary-limit-concurrency/", "Over 100 concurrent requests trips a limit"),
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
 ("/github/link-header-not-followed/", "Only the first page of results is read"),
],
"citations": [CITE_REST_LIMITS, CITE_BEST, CITE_ISSUES, CITE_ISSUE_COMMENTS],
},

]
