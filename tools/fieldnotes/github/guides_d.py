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


{
"slug": "retry-after-ignored",
"title": "The client ignores retry-after and keeps hammering the API",
"description": "GitHub tells you exactly how long to wait. A fixed one-second backoff spends 60 refused requests inside that window and extends the throttle.",
"h1": "the client ignores retry-after and keeps hammering the API",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github retry-after header", "github api 429 backoff",
             "github x-ratelimit-reset", "github api exponential backoff",
             "github rate limit retry strategy"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The log shows four hundred consecutive <code>403</code>s, one second apart, for eleven minutes. The retry logic is working perfectly: it catches the error, waits, tries again, never gives up. GitHub said <code>retry-after: 120</code> on the very first one, and the client threw that header away along with the rest of the response.",
"short_answer": """<p>Throttled responses carry the answer. On a secondary limit you get <code>retry-after</code> in seconds; on a primary exhaustion you get <code>x-ratelimit-remaining: 0</code> and <code>x-ratelimit-reset</code> as an epoch timestamp. Branch on those two in that order, and only fall back to exponential backoff when neither is present.</p>
<p>What that saves is measurable. A client retrying every second inside a 120-second window issues 120 requests that were refused before they were sent, each one keeping the limit engaged. The script below reads the headers from a live probe or from a response you paste in from your logs, computes the exact wait, and reports how many of your retries land inside it.</p>""",
"problem": """<p>Retry logic is usually written once, early, against a generic HTTP client, and it is written for the failure everyone has seen: a transient connection reset that clears in a moment. So the shape is <code>except: sleep(1); retry</code>, and it is correct for that failure. Applied to a rate limit it is not just useless, it is actively harmful, because the requests it sends during the penalty window are themselves the thing being penalised.</p>
<p>The result is a failure mode that looks like persistence. The process is running. It is making requests. The logs are full. Nothing has crashed, no alert has a threshold for "same status code four hundred times", and the job that should have paused for two minutes and finished is now eleven minutes in and no closer.</p>
<p>And the two throttles want different waits, which is where the half-fixed version goes wrong. A team adds <code>retry-after</code> handling, the secondary-limit case gets better, and then a primary exhaustion arrives with no <code>retry-after</code> at all &mdash; that one is signalled by <code>x-ratelimit-reset</code>, up to an hour away &mdash; and the client falls straight back to hammering.</p>""",
"why": """<p><strong>Two throttles, two headers, one status code.</strong> A secondary limit answers <code>403</code> or <code>429</code> with <code>retry-after</code> and usually a wait measured in minutes. A primary exhaustion answers <code>403</code> with <code>x-ratelimit-remaining: 0</code> and <code>x-ratelimit-reset</code>, and the wait is however much of the hour is left. Reading only one of the two headers handles half the cases and looks like it handles all of them.</p>
<p><strong><code>retry-after</code> is not always a number.</strong> The HTTP specification allows either a delay in seconds or an HTTP-date. GitHub sends seconds, but a proxy in front of your client can rewrite it, and a parser that does <code>int(value)</code> and swallows the exception silently falls through to the default. Parse both forms and compute the delay against the current time.</p>
<p><strong>Retrying inside the window extends the window.</strong> Secondary limits are throttles on burst behaviour. Requests made while one is engaged are burst behaviour, so a client that keeps trying keeps supplying the evidence. This is why the observed pause is so often much longer than the <code>retry-after</code> value the first response contained.</p>
<p><strong>Exponential backoff is the fallback, not the strategy.</strong> It is what you use when the server told you nothing. When the server told you exactly how long to wait, backing off exponentially from one second is a worse guess than the answer you were handed, and it is a guess that starts by being wrong 119 times.</p>
<p><strong>The client's behaviour is a blind spot from the API side.</strong> Nothing GitHub exposes can tell you whether your code honours these headers; that lives in your code and in your request timestamps. What a read-only script can do is take a throttled response and show you the correct wait next to the wait your current settings would produce, which turns an argument about retry policy into a number.</p>""",
"steps": [
 {"h": "Capture a real throttled response, headers and all",
  "body": """<p>The next time a job is throttled, log the full response headers, not just the status. <code>retry-after</code>, <code>x-ratelimit-remaining</code>, <code>x-ratelimit-reset</code>, <code>x-ratelimit-resource</code> and <code>x-github-request-id</code> are the five that matter. The script accepts them on the command line so you can evaluate an incident after the fact, offline.</p>"""},
 {"h": "Branch on retry-after first",
  "body": """<p>If <code>retry-after</code> is present, that is the wait. Sleep exactly that long &mdash; not a fraction, not a capped version of it &mdash; and parse the HTTP-date form as well as the integer form. This branch has to come first because a secondary limit can arrive while the primary bucket is perfectly healthy, and the reset timestamp then tells you nothing useful.</p>"""},
 {"h": "Fall back to x-ratelimit-reset when the bucket is empty",
  "body": """<p><code>x-ratelimit-remaining: 0</code> means the hourly quota is gone and <code>x-ratelimit-reset</code> is the epoch second it returns. Sleep until then. It can be most of an hour, which is unpleasant and is still shorter than an hour of refused retries followed by the same wait.</p>"""},
 {"h": "Only then back off exponentially, with jitter and a cap",
  "body": """<p>No headers means no information, so guess: one second, two, four, eight, capped at a minute, with random jitter so that a fleet of workers does not synchronise into a thundering herd, and with a maximum attempt count so a permanent failure eventually surfaces as one.</p>"""},
 {"h": "Pause the whole client, and count what you would have wasted",
  "body": """<p>A throttle applies to the credential, not the request, so every other worker holding that token is about to be refused too. Sleep the shared client rather than the one call. Then run the script against the captured response: the number of retries your current interval fits inside the required wait is the size of the problem, stated plainly.</p>"""},
],
"verify": """<p>Feed the script the headers from a throttled response and confirm the wait it computes matches what you now sleep, with no requests scheduled inside the window.</p>
<pre><code class="language-bash">python3 github_backoff_plan.py --status 403 --header 'retry-after: 120' \\
    --header 'x-ratelimit-remaining: 4870' --interval 1
# hammering: wait 120s from retry-after; a 1.0s interval sends 120 refused requests</code></pre>""",
"code_intro": "The interesting code here has no network in it at all. Everything that decides how long to wait is pure and takes <code>now</code> as an argument, because the whole point is that the decision is a function of five header values and nothing else. The script's one live request exists only to fetch a real set of headers; <code>--status</code> and <code>--header</code> let you run the same analysis over a response you already captured.",
"py_file": "github_backoff_plan.py",
"py": '''"""Compute the wait a throttled GitHub response asks for, and cost your retries.

Read only. The single live request is a GET against /rate_limit, which does not
count against the primary rate limit. Everything that decides the wait is a pure
function of the response headers, so a response captured during an incident can
be analysed later with --status and --header.

Whether your client honours these headers is not visible through the API: it
lives in your code. What is visible is the contract, and what it costs to ignore.
"""
import argparse
import logging
import os
import sys
import time
from email.utils import parsedate_to_datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_backoff_plan")

API = "https://api.github.com"
UA = "github-backoff-plan/1.0"

# Where a secondary limit sends no retry-after, the documented advice is to wait
# at least a minute before trying again.
SECONDARY_FLOOR_SECONDS = 60.0


def retry_after_seconds(value, now):
    """Parse a retry-after header into seconds from now, or None. Pure.

    HTTP allows either a delay in seconds or an HTTP-date. GitHub sends seconds,
    but a proxy in front of the client is free to rewrite it into the other form,
    and a parser that only does int() treats that as absent and falls through to
    a default that is usually far too short.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return max(0.0, float(int(text)))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    return max(0.0, when.timestamp() - float(now))


def required_wait(status, headers, now):
    """How long a correct client sleeps before its next request. Pure.

    Returns (seconds, source, detail). The order is not arbitrary: a secondary
    limit can fire while the primary bucket is untouched, so retry-after has to
    win over the reset timestamp, which in that case is describing an hour that
    has nothing to do with why this request was refused.
    """
    lowered = {str(k).lower(): v for k, v in (headers or {}).items()}
    try:
        status = int(status)
    except (TypeError, ValueError):
        status = 0

    if status not in (403, 429):
        return (0.0, "none",
                "%d is not a throttled response, so there is nothing to wait for"
                % status)

    seconds = retry_after_seconds(lowered.get("retry-after"), now)
    if seconds is not None:
        return (seconds, "retry-after",
                "the response asked for %.0f second(s). Sleep exactly that, not "
                "a capped or scaled version of it." % seconds)

    try:
        remaining = int(lowered.get("x-ratelimit-remaining"))
    except (TypeError, ValueError):
        remaining = None
    try:
        reset = float(lowered.get("x-ratelimit-reset"))
    except (TypeError, ValueError):
        reset = None

    if remaining == 0 and reset is not None:
        return (max(0.0, reset - float(now)), "x-ratelimit-reset",
                "the hourly quota is spent and returns at the reset timestamp, "
                "%.0f second(s) from now" % max(0.0, reset - float(now)))

    return (SECONDARY_FLOOR_SECONDS, "floor",
            "no retry-after and the primary bucket is not empty, so this is a "
            "secondary limit that sent no wait. Treat %.0f seconds as the floor "
            "and back off exponentially from there."
            % SECONDARY_FLOOR_SECONDS)


def backoff(attempt, base=1.0, cap=60.0):
    """Exponential delay for a given attempt number. Pure, and unjittered.

    The fallback for when the server said nothing at all. Jitter is applied by the
    caller rather than in here, so that the schedule this returns is something the
    tests can assert on and a reader can predict.
    """
    attempt = max(0, int(attempt))
    return min(float(cap), float(base) * (2 ** attempt))


def wasted_requests(seconds, interval):
    """How many refused requests a fixed-interval retrier fits in the wait. Pure.

    This is the number that makes the argument. Every one of these is sent into a
    limit that is already engaged, and on a secondary limit each one is fresh
    evidence of the burst behaviour being throttled.
    """
    seconds = max(0.0, float(seconds))
    interval = float(interval)
    if interval <= 0:
        return 0
    return int(seconds // interval)


def plan(status, headers, now, interval=1.0):
    """Turn a throttled response into a finding. Pure. Returns (state, report)."""
    seconds, source, detail = required_wait(status, headers, now)
    wasted = wasted_requests(seconds, interval)
    report = {"wait_seconds": round(seconds, 1), "source": source,
              "detail": detail, "wasted_requests": wasted,
              "retry_interval": interval,
              "fallback_schedule": [backoff(i) for i in range(5)]}

    if source == "none":
        return ("not-throttled", report)
    if wasted >= 60:
        return ("hammering", report)
    if wasted > 0:
        return ("impatient", report)
    return ("honoured", report)


def parse_header(text):
    """'Name: value' from the command line into a (name, value) pair."""
    name, _, value = str(text).partition(":")
    return (name.strip(), value.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", type=int, default=None,
                    help="analyse a captured response with this status instead "
                         "of probing the API")
    ap.add_argument("--header", action="append", default=[],
                    help="'name: value' from a captured response; repeatable")
    ap.add_argument("--interval", type=float, default=1.0,
                    help="the retry interval your client currently uses")
    args = ap.parse_args()

    now = time.time()

    if args.status is not None:
        status = args.status
        headers = dict(parse_header(h) for h in args.header)
        log.info("analysing a captured %d with %d header(s)", status, len(headers))
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log.error("set GITHUB_TOKEN (a read-only token is enough), or pass "
                      "--status and --header to analyse a captured response")
            return 2
        r = requests.get(API + "/rate_limit", timeout=30, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
        })
        status, headers = r.status_code, dict(r.headers)
        log.info("probed GET /rate_limit: %d (this endpoint does not consume "
                 "quota)", status)

    state, report = plan(status, headers, now, args.interval)
    log.info("%s: wait %.0fs from %s", state, report["wait_seconds"],
             report["source"])
    log.info("  %s", report["detail"])

    if state == "not-throttled":
        log.info("  nothing is throttled right now. Re-run with --status and "
                 "--header against a response captured during an incident to "
                 "cost your current retry policy.")
        return 0

    log.warning("  a %.1fs retry interval sends %d refused request(s) inside "
                "that window", report["retry_interval"], report["wasted_requests"])
    log.warning("  repair: sleep the whole client for %.0f second(s) before the "
                "next request, not one call.", report["wait_seconds"])
    log.warning("  repair: branch on retry-after first, then on "
                "x-ratelimit-remaining being 0 plus x-ratelimit-reset, and only "
                "then on a jittered exponential schedule such as %s",
                ", ".join("%.0fs" % s for s in report["fallback_schedule"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-backoff-plan.mjs",
"js": '''/**
 * Compute the wait a throttled GitHub response asks for, and cost your retries.
 *
 * Read only. The single live request is a GET against /rate_limit, which does
 * not count against the primary rate limit. Everything that decides the wait is
 * a pure function of the response headers.
 */
const API = 'https://api.github.com';
const UA = 'github-backoff-plan/1.0';

// Where a secondary limit sends no retry-after, the documented advice is to
// wait at least a minute before trying again.
export const SECONDARY_FLOOR_SECONDS = 60;

/**
 * Parse a retry-after header into seconds from now, or null. Pure.
 * HTTP allows either a delay in seconds or an HTTP-date, and a parser that only
 * handles the integer form treats the other as absent.
 */
export function retryAfterSeconds(value, now) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  if (/^\\d+$/.test(text)) return Math.max(0, Number.parseInt(text, 10));
  const ms = Date.parse(text);
  if (!Number.isFinite(ms)) return null;
  return Math.max(0, ms / 1000 - Number(now));
}

/**
 * How long a correct client sleeps before its next request. Pure.
 * Returns [seconds, source, detail]. retry-after wins over the reset timestamp
 * because a secondary limit can fire while the primary bucket is untouched.
 */
export function requiredWait(status, headers, now) {
  const lowered = {};
  for (const [k, v] of Object.entries(headers ?? {})) lowered[k.toLowerCase()] = v;
  const code = Number.parseInt(status, 10) || 0;

  if (code !== 403 && code !== 429) {
    return [0, 'none',
      `${code} is not a throttled response, so there is nothing to wait for`];
  }

  const seconds = retryAfterSeconds(lowered['retry-after'], now);
  if (seconds !== null) {
    return [seconds, 'retry-after',
      `the response asked for ${Math.round(seconds)} second(s). Sleep exactly ` +
      'that, not a capped or scaled version of it.'];
  }

  const remainingRaw = Number.parseInt(lowered['x-ratelimit-remaining'], 10);
  const remaining = Number.isFinite(remainingRaw) ? remainingRaw : null;
  const resetRaw = Number.parseFloat(lowered['x-ratelimit-reset']);
  const reset = Number.isFinite(resetRaw) ? resetRaw : null;

  if (remaining === 0 && reset !== null) {
    const wait = Math.max(0, reset - Number(now));
    return [wait, 'x-ratelimit-reset',
      'the hourly quota is spent and returns at the reset timestamp, ' +
      `${Math.round(wait)} second(s) from now`];
  }

  return [SECONDARY_FLOOR_SECONDS, 'floor',
    'no retry-after and the primary bucket is not empty, so this is a secondary ' +
    `limit that sent no wait. Treat ${SECONDARY_FLOOR_SECONDS} seconds as the ` +
    'floor and back off exponentially from there.'];
}

/**
 * Exponential delay for a given attempt number. Pure, and unjittered.
 * Jitter belongs to the caller so this schedule stays predictable.
 */
export function backoff(attempt, base = 1, cap = 60) {
  const n = Math.max(0, Math.trunc(attempt));
  return Math.min(cap, base * (2 ** n));
}

/**
 * How many refused requests a fixed-interval retrier fits in the wait. Pure.
 * Every one of these is sent into a limit that is already engaged.
 */
export function wastedRequests(seconds, interval) {
  const wait = Math.max(0, Number(seconds));
  const gap = Number(interval);
  if (!(gap > 0)) return 0;
  return Math.floor(wait / gap);
}

/** Turn a throttled response into a finding. Pure. Returns [state, report]. */
export function plan(status, headers, now, interval = 1) {
  const [seconds, source, detail] = requiredWait(status, headers, now);
  const wasted = wastedRequests(seconds, interval);
  const report = {
    wait_seconds: Math.round(seconds * 10) / 10,
    source,
    detail,
    wasted_requests: wasted,
    retry_interval: interval,
    fallback_schedule: [0, 1, 2, 3, 4].map((i) => backoff(i)),
  };
  if (source === 'none') return ['not-throttled', report];
  if (wasted >= 60) return ['hammering', report];
  if (wasted > 0) return ['impatient', report];
  return ['honoured', report];
}

function parseHeader(text) {
  const at = String(text).indexOf(':');
  if (at < 0) return [String(text).trim(), ''];
  return [String(text).slice(0, at).trim(), String(text).slice(at + 1).trim()];
}

async function main() {
  const args = process.argv.slice(2);
  const now = Date.now() / 1000;

  let status = null;
  let interval = 1;
  const headers = {};
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === '--status') { status = Number.parseInt(args[i + 1], 10); i += 1; }
    else if (args[i] === '--interval') { interval = Number.parseFloat(args[i + 1]); i += 1; }
    else if (args[i] === '--header') {
      const [name, value] = parseHeader(args[i + 1]);
      headers[name] = value;
      i += 1;
    }
  }

  let live = headers;
  if (status === null) {
    const token = process.env.GITHUB_TOKEN;
    if (!token) {
      console.error('set GITHUB_TOKEN (a read-only token is enough), or pass ' +
        '--status and --header to analyse a captured response');
      process.exitCode = 2;
      return;
    }
    const res = await fetch(`${API}/rate_limit`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': UA,
      },
    });
    status = res.status;
    live = Object.fromEntries(res.headers.entries());
    console.log(`probed GET /rate_limit: ${status} (this endpoint does not consume quota)`);
  } else {
    console.log(`analysing a captured ${status} with ${Object.keys(headers).length} header(s)`);
  }

  const [state, report] = plan(status, live, now, interval);
  console.log(`${state}: wait ${Math.round(report.wait_seconds)}s from ${report.source}`);
  console.log(`  ${report.detail}`);

  if (state === 'not-throttled') {
    console.log('  nothing is throttled right now. Re-run with --status and ' +
      '--header against a response captured during an incident to cost your ' +
      'current retry policy.');
    return;
  }

  console.warn(`  a ${report.retry_interval}s retry interval sends ` +
    `${report.wasted_requests} refused request(s) inside that window`);
  console.warn(`  repair: sleep the whole client for ${Math.round(report.wait_seconds)} ` +
    'second(s) before the next request, not one call.');
  console.warn('  repair: branch on retry-after first, then on ' +
    'x-ratelimit-remaining being 0 plus x-ratelimit-reset, and only then on a ' +
    `jittered exponential schedule such as ${report.fallback_schedule.join('s, ')}s`);
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every case here is a set of headers and a fixed <code>now</code>, which is the whole reason the wait calculation was written as a pure function: a throttled response is not something you can produce on demand, and a test that needed one would never run. The cases that matter are the precedence between the two headers, the HTTP-date form of <code>retry-after</code> that a proxy can introduce, and the difference between a bucket at zero and a bucket that was never read.",
"test_py_file": "test_github_backoff_plan.py",
"test_py": '''from github_backoff_plan import (backoff, plan, required_wait,
                                 retry_after_seconds, wasted_requests)

NOW = 1756512000.0  # 2025-08-30T00:00:00Z


def test_retry_after_reads_the_integer_form():
    assert retry_after_seconds("120", NOW) == 120.0
    assert retry_after_seconds(" 60 ", NOW) == 60.0


def test_retry_after_reads_the_http_date_form_a_proxy_may_substitute():
    assert retry_after_seconds("Sat, 30 Aug 2025 00:02:00 GMT", NOW) == 120.0


def test_a_retry_after_already_in_the_past_is_zero_not_negative():
    assert retry_after_seconds("Fri, 29 Aug 2025 23:00:00 GMT", NOW) == 0.0


def test_an_unparseable_retry_after_is_absent_rather_than_zero():
    assert retry_after_seconds("soon", NOW) is None
    assert retry_after_seconds(None, NOW) is None
    assert retry_after_seconds("", NOW) is None


def test_retry_after_wins_over_the_reset_timestamp():
    # A secondary limit fires with the hourly bucket untouched, so the reset
    # timestamp is describing an hour that has nothing to do with this refusal.
    seconds, source, _ = required_wait(403, {
        "Retry-After": "120",
        "X-RateLimit-Remaining": "4870",
        "X-RateLimit-Reset": str(int(NOW + 3000)),
    }, NOW)
    assert source == "retry-after"
    assert seconds == 120.0


def test_an_empty_bucket_falls_through_to_the_reset_timestamp():
    seconds, source, detail = required_wait(403, {
        "x-ratelimit-remaining": "0",
        "x-ratelimit-reset": str(int(NOW + 1800)),
    }, NOW)
    assert source == "x-ratelimit-reset"
    assert seconds == 1800.0
    assert "hourly quota" in detail


def test_a_bucket_with_headroom_and_no_retry_after_uses_the_floor():
    seconds, source, _ = required_wait(429, {"x-ratelimit-remaining": "4900"}, NOW)
    assert source == "floor"
    assert seconds == 60.0


def test_a_response_that_is_not_throttled_asks_for_no_wait():
    seconds, source, _ = required_wait(200, {"retry-after": "120"}, NOW)
    assert source == "none"
    assert seconds == 0.0


def test_backoff_doubles_and_then_stops_at_the_cap():
    assert [backoff(i) for i in range(5)] == [1.0, 2.0, 4.0, 8.0, 16.0]
    assert backoff(20) == 60.0
    assert backoff(-3) == 1.0


def test_wasted_requests_counts_what_fits_inside_the_wait():
    assert wasted_requests(120, 1) == 120
    assert wasted_requests(120, 30) == 4
    assert wasted_requests(0, 1) == 0


def test_wasted_requests_survives_a_nonsense_interval():
    assert wasted_requests(120, 0) == 0
    assert wasted_requests(120, -5) == 0


def test_a_one_second_retry_inside_a_two_minute_wait_is_hammering():
    state, report = plan(403, {"retry-after": "120"}, NOW, 1.0)
    assert state == "hammering"
    assert report["wasted_requests"] == 120
    assert report["source"] == "retry-after"


def test_a_client_that_waits_longer_than_asked_has_honoured_it():
    state, report = plan(403, {"retry-after": "120"}, NOW, 300.0)
    assert state == "honoured"
    assert report["wasted_requests"] == 0


def test_a_few_retries_inside_the_window_are_impatient_not_hammering():
    state, _ = plan(429, {"retry-after": "120"}, NOW, 30.0)
    assert state == "impatient"


def test_an_untroubled_response_reports_nothing_to_do():
    state, report = plan(200, {}, NOW, 1.0)
    assert state == "not-throttled"
    assert report["wait_seconds"] == 0.0
''',
"test_js_file": "github-backoff-plan.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  backoff, plan, requiredWait, retryAfterSeconds, wastedRequests,
} from './github-backoff-plan.mjs';

const NOW = 1756512000; // 2025-08-30T00:00:00Z

test('retry-after reads the integer form', () => {
  assert.equal(retryAfterSeconds('120', NOW), 120);
  assert.equal(retryAfterSeconds(' 60 ', NOW), 60);
});

test('retry-after reads the HTTP-date form a proxy may substitute', () => {
  assert.equal(retryAfterSeconds('Sat, 30 Aug 2025 00:02:00 GMT', NOW), 120);
});

test('a retry-after already in the past is zero, not negative', () => {
  assert.equal(retryAfterSeconds('Fri, 29 Aug 2025 23:00:00 GMT', NOW), 0);
});

test('an unparseable retry-after is absent rather than zero', () => {
  assert.equal(retryAfterSeconds('soon', NOW), null);
  assert.equal(retryAfterSeconds(null, NOW), null);
  assert.equal(retryAfterSeconds('', NOW), null);
});

test('retry-after wins over the reset timestamp', () => {
  const [seconds, source] = requiredWait(403, {
    'Retry-After': '120',
    'X-RateLimit-Remaining': '4870',
    'X-RateLimit-Reset': String(NOW + 3000),
  }, NOW);
  assert.equal(source, 'retry-after');
  assert.equal(seconds, 120);
});

test('an empty bucket falls through to the reset timestamp', () => {
  const [seconds, source, detail] = requiredWait(403, {
    'x-ratelimit-remaining': '0',
    'x-ratelimit-reset': String(NOW + 1800),
  }, NOW);
  assert.equal(source, 'x-ratelimit-reset');
  assert.equal(seconds, 1800);
  assert.match(detail, /hourly quota/);
});

test('a bucket with headroom and no retry-after uses the floor', () => {
  const [seconds, source] = requiredWait(429, { 'x-ratelimit-remaining': '4900' }, NOW);
  assert.equal(source, 'floor');
  assert.equal(seconds, 60);
});

test('a response that is not throttled asks for no wait', () => {
  const [seconds, source] = requiredWait(200, { 'retry-after': '120' }, NOW);
  assert.equal(source, 'none');
  assert.equal(seconds, 0);
});

test('backoff doubles and then stops at the cap', () => {
  assert.deepEqual([0, 1, 2, 3, 4].map((i) => backoff(i)), [1, 2, 4, 8, 16]);
  assert.equal(backoff(20), 60);
  assert.equal(backoff(-3), 1);
});

test('wastedRequests counts what fits inside the wait', () => {
  assert.equal(wastedRequests(120, 1), 120);
  assert.equal(wastedRequests(120, 30), 4);
  assert.equal(wastedRequests(0, 1), 0);
});

test('wastedRequests survives a nonsense interval', () => {
  assert.equal(wastedRequests(120, 0), 0);
  assert.equal(wastedRequests(120, -5), 0);
});

test('a one-second retry inside a two-minute wait is hammering', () => {
  const [state, report] = plan(403, { 'retry-after': '120' }, NOW, 1);
  assert.equal(state, 'hammering');
  assert.equal(report.wasted_requests, 120);
  assert.equal(report.source, 'retry-after');
});

test('a client that waits longer than asked has honoured it', () => {
  const [state, report] = plan(403, { 'retry-after': '120' }, NOW, 300);
  assert.equal(state, 'honoured');
  assert.equal(report.wasted_requests, 0);
});

test('a few retries inside the window are impatient, not hammering', () => {
  assert.equal(plan(429, { 'retry-after': '120' }, NOW, 30)[0], 'impatient');
});

test('an untroubled response reports nothing to do', () => {
  const [state, report] = plan(200, {}, NOW, 1);
  assert.equal(state, 'not-throttled');
  assert.equal(report.wait_seconds, 0);
});
''',
"faq": [
 ("Does GitHub always send retry-after when it throttles me?",
  "No. Secondary limits normally carry it; primary exhaustion normally does not, and signals the wait through x-ratelimit-remaining being 0 plus x-ratelimit-reset instead. That is why the branch order matters and why a client that reads only one of the two headers handles half its throttles well and the other half not at all."),
 ("Can a script tell whether my client honours retry-after?",
  "Not through the API. GitHub sees your requests, not your code, and exposes nothing about your retry behaviour; that is a genuine blind spot for a read-only observer. What the script does instead is take a throttled response you captured and put the required wait next to the number of retries your current interval would fit inside it, which is the same argument made with a number."),
 ("Is it safe to just sleep for an hour whenever I see a 403?",
  "Safe, and usually far more than you need. A secondary limit often clears in a couple of minutes, so an unconditional hour turns a small pause into an outage. Read the headers: they distinguish a two-minute wait from a fifty-minute one, and the whole point is that you do not have to guess."),
 ("Why does the throttle last longer than the retry-after value said?",
  "Because the requests you sent while waiting counted. Secondary limits throttle burst behaviour, and retries during the penalty window are burst behaviour, so a client that keeps trying keeps re-arming the limit. Honouring the header exactly is not politeness; it is the shortest path back to working."),
 ("Should I add jitter even when I have a retry-after value?",
  "Not to that value; sleep it exactly. Jitter belongs to the fallback schedule, where several workers would otherwise wake at identical moments and re-create the burst that was throttled. A retry-after is a specific instruction and every worker obeying it lands at the same time by design, which is fine because that time is one GitHub chose."),
],
"related": [
 ("/github/secondary-limit-concurrency/", "Over 100 concurrent requests trips a limit"),
 ("/github/secondary-limit-content-creation/", "Bulk creation exceeds 80 a minute"),
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
],
"citations": [CITE_BEST, CITE_REST_LIMITS, CITE_TROUBLESHOOT, CITE_RATE_ENDPOINT],
},


{
"slug": "no-conditional-requests",
"title": "Polling without ETags spends full quota on unchanged data",
"description": "A 304 Not Modified does not count against the rate limit. Measure x-ratelimit-used before and after an If-None-Match request and the saving is exact.",
"h1": "polling without ETags spends full quota on unchanged data",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api etag", "github if-none-match 304",
             "github conditional requests rate limit", "github 304 not modified quota",
             "github api reduce rate limit usage"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The dashboard polls eight endpoints every thirty seconds and burns through 5,000 requests before lunch. Almost nothing it fetches has changed. GitHub has been sending an <code>etag</code> on every one of those responses, and every response that comes back <code>304 Not Modified</code> is free &mdash; it does not count against the rate limit at all. This is the one problem in this section where the fix pays for itself in a number you can print.",
"short_answer": """<p>Every response carries an <code>etag</code>. Send it back as <code>If-None-Match</code> and an unchanged resource answers <code>304 Not Modified</code> with an empty body, and <strong>that response does not count against your primary rate limit</strong>.</p>
<p>You do not have to take that on trust. <code>x-ratelimit-used</code> comes back on every response, so make the request twice &mdash; once plain, once conditional &mdash; and compare the two values. If the second call returned <code>304</code> and <code>used</code> did not move, the saving is proven for that endpoint, and multiplying it by your poll rate turns it into requests an hour.</p>""",
"problem": """<p>Quota exhaustion is usually blamed on volume, so the first fix attempted is always to poll less often. That is a real cost: the dashboard gets staler, the bot reacts later, and the quota problem comes back the next time someone adds a repository. The requests were never the problem. Paying full price for answers that say "nothing changed" was.</p>
<p>What hides it is that the wasteful version works perfectly. There is no error, no warning header, no degraded response. A poller with no conditional requests and a poller with them return identical data; the only difference is a counter neither one reads. So this survives code review indefinitely, and it is discovered when the quota runs out and every call starts returning 403 &mdash; at which point it looks like a rate-limit incident rather than a caching one.</p>
<p>It also scales in the wrong direction. Add a repository and the poll cost grows linearly; add a repository to a conditional poller and the cost stays near zero as long as nothing changes in it. Two integrations with the same shape end up in completely different places six months later.</p>""",
"why": """<p><strong>A 304 is free, and that is the whole mechanism.</strong> GitHub documents conditional requests as not counting against the primary rate limit. The request is still made, the round trip still happens, the bandwidth is still tiny, and <code>x-ratelimit-remaining</code> does not move. Nothing else in the API offers a discount like this.</p>
<p><strong>The evidence is on the response you already have.</strong> <code>etag</code> comes back on essentially every GET, and <code>x-ratelimit-used</code> comes back next to it. A script can therefore measure the saving rather than assert it, which is unusual: for most of the problems in these notes the fix has to be argued for.</p>
<p><strong>The cache key is the full request, not the path.</strong> An ETag belongs to a URL including its query string, its <code>Accept</code> header and the credential that fetched it. Change <code>per_page</code>, change the sort order, rotate the token, and the stored ETag stops matching &mdash; the request is billed again and nobody notices, because a <code>200</code> is not an error. Keeping request parameters stable is part of the fix, not an optimisation on top of it.</p>
<p><strong><code>304</code> is not a failure and clients keep treating it as one.</strong> Some HTTP libraries raise on any non-2xx, and a wrapper written for that behaviour turns the cheapest response in the API into an exception. The handling is one branch: on 304, keep what you already have.</p>
<p><strong>Some endpoints support <code>last-modified</code> instead or as well.</strong> Where an <code>etag</code> is absent, <code>if-modified-since</code> against the <code>last-modified</code> value does the same job. Where both are present, the ETag is the stronger validator and is what you should send.</p>""",
"steps": [
 {"h": "Fetch the endpoint once and keep two numbers",
  "body": """<p>Make the request your integration already makes and record <code>etag</code> and <code>x-ratelimit-used</code> from the response. If there is no <code>etag</code>, look for <code>last-modified</code>; if neither is present, this endpoint cannot be cached and the saving does not apply to it.</p>"""},
 {"h": "Repeat it with If-None-Match and read x-ratelimit-used again",
  "body": """<p>Send the exact ETag string back, quotes and any <code>W/</code> prefix included. An unchanged resource answers <code>304</code> with no body. Subtract the two <code>used</code> values: a difference of zero is the measurement this whole note exists to produce.</p>"""},
 {"h": "Multiply by your real poll rate",
  "body": """<p>Eight endpoints every thirty seconds is 960 requests an hour, roughly a fifth of a 5,000-request budget, spent almost entirely on unchanged data. The same schedule with conditional requests costs close to nothing until something actually changes. That is the number to put in the pull request.</p>"""},
 {"h": "Store the ETag per URL and per credential",
  "body": """<p>Key the cache on the full request &mdash; path plus query string plus <code>Accept</code> &mdash; and on the token that fetched it, because ETags are scoped to the credential. A rotation that silently invalidates the whole cache produces a quota spike with no error to explain it.</p>"""},
 {"h": "Treat 304 as data, not as an error",
  "body": """<p>On <code>304</code>, return the previously stored representation and do nothing else. Check that your HTTP client is not configured to raise on non-2xx, and that nothing between you and GitHub is stripping or rewriting the header: a proxy that drops <code>If-None-Match</code> turns every conditional request back into a billed one, which the measurement above will show as a <code>200</code> where a <code>304</code> was expected.</p>"""},
],
"verify": """<p>Run the script against an endpoint your integration polls. A confirmed saving reports the conditional request as free and prices the current poll rate against the quota.</p>
<pre><code class="language-bash">python3 github_etag_saving.py --repo acme/api --path /issues --poll-seconds 30 --endpoints 8
# free: the 304 cost 0 request(s); 960/hour becomes 0/hour, 19.2% of quota returned</code></pre>""",
"code_intro": "Two GETs, three header values, one subtraction. The measurement is the point, so <code>measure()</code> takes the two responses already reduced to <code>status</code>, <code>etag</code> and <code>used</code> and returns a verdict without touching the network &mdash; which lets the tests cover the cases you cannot arrange on demand, including the awkward one where the endpoint answers <code>200</code> to a conditional request because a proxy dropped the header.",
"py_file": "github_etag_saving.py",
"py": '''"""Measure what conditional requests would save against the GitHub rate limit.

Read only. Two GETs against one endpoint: the second sends If-None-Match with the
ETag the first returned. A 304 Not Modified does not count against the primary
rate limit, and x-ratelimit-used on both responses proves it rather than
asserting it.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_etag_saving")

API = "https://api.github.com"
UA = "github-etag-saving/1.0"

DEFAULT_LIMIT = 5000


def measure(first, second):
    """Compare a plain response with the conditional one that followed. Pure.

    Each argument is {"status": int, "etag": str|None, "used": int|None}. Returns
    (state, report). The states are deliberately separate because they have
    nothing in common: an endpoint that sends no ETag cannot be cached at all, an
    endpoint that answers 200 to a conditional request is being interfered with,
    and a 304 that still increments used would mean the documented discount did
    not apply.
    """
    etag = (first or {}).get("etag")
    before = (first or {}).get("used")
    after = (second or {}).get("used")
    status = (second or {}).get("status")

    try:
        delta = int(after) - int(before)
    except (TypeError, ValueError):
        delta = None

    report = {"etag": etag, "used_before": before, "used_after": after,
              "cost_of_unchanged_poll": delta,
              "first_status": (first or {}).get("status"), "second_status": status}

    if not etag:
        return ("no-etag", report)
    if status != 304:
        return ("not-honoured", report)
    if delta is None:
        return ("unmeasured", report)
    if delta > 0:
        return ("billed", report)
    return ("free", report)


def project(poll_seconds, endpoints, limit=DEFAULT_LIMIT, unchanged_fraction=1.0):
    """Price a polling schedule with and without conditional requests. Pure.

    unchanged_fraction is how much of what you poll is typically unchanged. At
    1.0 every poll is a 304 and costs nothing; at 0.0 nothing is cacheable and
    conditional requests save nothing, which is the honest end of the range.
    """
    poll_seconds = max(1.0, float(poll_seconds))
    endpoints = max(1, int(endpoints))
    limit = max(1, int(limit))
    fraction = min(1.0, max(0.0, float(unchanged_fraction)))

    without = (3600.0 / poll_seconds) * endpoints
    with_etags = without * (1.0 - fraction)
    return {"per_hour_without": round(without, 1),
            "per_hour_with": round(with_etags, 1),
            "saved_per_hour": round(without - with_etags, 1),
            "percent_without": round(100.0 * without / limit, 1),
            "percent_with": round(100.0 * with_etags / limit, 1),
            "limit": limit}


def verdict(state, projection):
    """Turn the measurement and the projection into one line. Pure."""
    saved = (projection or {}).get("saved_per_hour", 0)
    percent = (projection or {}).get("percent_without", 0)

    if state == "no-etag":
        return ("unavailable",
                "the response carried no etag, so this endpoint cannot be polled "
                "conditionally. Check last-modified and use if-modified-since "
                "where it is present.")
    if state == "not-honoured":
        return ("ignored",
                "the conditional request came back 200 rather than 304. Either "
                "the resource genuinely changed between the two calls, or "
                "something between this client and GitHub is dropping the "
                "If-None-Match header, which silently reinstates the full cost.")
    if state == "billed":
        return ("billed",
                "the 304 arrived and x-ratelimit-used still moved, which is not "
                "how conditional requests are documented to behave. Re-run "
                "before acting on it: another process sharing this token spends "
                "the same counter.")
    if state == "unmeasured":
        return ("unmeasured",
                "the 304 arrived but x-ratelimit-used was missing from one of "
                "the responses, so the saving is real and its size is not "
                "measured here.")
    return ("saving" if percent < 25 else "large-saving",
            "the 304 cost 0 request(s). At this poll rate that is %.0f request(s) "
            "an hour, %.1f%% of the quota, currently spent on data that did not "
            "change." % (saved, percent))


def read(response):
    """Reduce a response to the three fields the measurement needs."""
    headers = {k.lower(): v for k, v in response.headers.items()}
    try:
        used = int(headers.get("x-ratelimit-used"))
    except (TypeError, ValueError):
        used = None
    return {"status": response.status_code, "etag": headers.get("etag"),
            "used": used, "last_modified": headers.get("last-modified"),
            "limit": headers.get("x-ratelimit-limit")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--path", default="/issues",
                    help="path under the repository to probe, e.g. /issues")
    ap.add_argument("--poll-seconds", type=float, default=60.0,
                    help="how often your integration polls this endpoint")
    ap.add_argument("--endpoints", type=int, default=1,
                    help="how many endpoints are polled on that schedule")
    ap.add_argument("--unchanged", type=float, default=1.0,
                    help="fraction of polls that find nothing changed (0 to 1)")
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

    url = "%s/repos/%s/%s%s" % (API, owner, name, args.path)
    log.info("probing %s twice: once plain, once with If-None-Match", url)

    plain = session.get(url, timeout=30)
    if plain.status_code == 401:
        log.error("401 from GitHub: GITHUB_TOKEN is missing, expired or malformed")
        return 2
    if plain.status_code in (403, 404):
        log.error("%d from %s: this token cannot read that endpoint. GitHub "
                  "answers 404 rather than 403 when a token cannot see a "
                  "resource at all.", plain.status_code, url)
        return 2
    first = read(plain)
    log.info("  plain:       %d, etag %s, x-ratelimit-used %s",
             first["status"], first["etag"], first["used"])

    second = first
    if first["etag"]:
        conditional = session.get(url, timeout=30,
                                  headers={"If-None-Match": first["etag"]})
        second = read(conditional)
        log.info("  conditional: %d, x-ratelimit-used %s",
                 second["status"], second["used"])
    elif first["last_modified"]:
        log.warning("  no etag, but last-modified is %s: use if-modified-since "
                    "on this endpoint instead", first["last_modified"])

    state, report = measure(first, second)
    limit = DEFAULT_LIMIT
    try:
        limit = int(first["limit"])
    except (TypeError, ValueError):
        pass

    projection = project(args.poll_seconds, args.endpoints, limit, args.unchanged)
    level, detail = verdict(state, projection)
    log.info("%s: %s", level, detail)
    log.info("  %.0f request(s)/hour now (%.1f%% of %d), %.0f/hour with "
             "conditional requests (%.1f%%)",
             projection["per_hour_without"], projection["percent_without"],
             projection["limit"], projection["per_hour_with"],
             projection["percent_with"])

    if level in ("saving", "large-saving"):
        log.info("  repair: store %s against this exact URL and credential, send "
                 "it back as If-None-Match, and treat 304 as 'keep what you "
                 "have' rather than as an error.", report["etag"])
        log.info("  repair: keep per_page, sort and Accept stable, and key the "
                 "cache by token: an ETag is scoped to the credential that "
                 "fetched it, so a rotation invalidates every entry at once.")
    return 0 if level in ("saving", "large-saving", "unavailable") else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-etag-saving.mjs",
"js": '''/**
 * Measure what conditional requests would save against the GitHub rate limit.
 *
 * Read only. Two GETs against one endpoint: the second sends If-None-Match with
 * the ETag the first returned. A 304 Not Modified does not count against the
 * primary rate limit, and x-ratelimit-used on both responses proves it.
 */
const API = 'https://api.github.com';
const UA = 'github-etag-saving/1.0';

export const DEFAULT_LIMIT = 5000;

/**
 * Compare a plain response with the conditional one that followed. Pure.
 * Each argument is { status, etag, used }. Returns [state, report].
 */
export function measure(first, second) {
  const etag = first?.etag ?? null;
  const before = first?.used;
  const after = second?.used;
  const status = second?.status;

  const parsedBefore = Number.parseInt(before, 10);
  const parsedAfter = Number.parseInt(after, 10);
  const delta = (Number.isFinite(parsedBefore) && Number.isFinite(parsedAfter))
    ? parsedAfter - parsedBefore : null;

  const report = {
    etag,
    used_before: before ?? null,
    used_after: after ?? null,
    cost_of_unchanged_poll: delta,
    first_status: first?.status ?? null,
    second_status: status ?? null,
  };

  if (!etag) return ['no-etag', report];
  if (status !== 304) return ['not-honoured', report];
  if (delta === null) return ['unmeasured', report];
  if (delta > 0) return ['billed', report];
  return ['free', report];
}

/**
 * Price a polling schedule with and without conditional requests. Pure.
 * unchangedFraction is how much of what you poll is typically unchanged.
 */
export function project(pollSeconds, endpoints, limit = DEFAULT_LIMIT, unchangedFraction = 1) {
  const seconds = Math.max(1, Number(pollSeconds));
  const count = Math.max(1, Math.trunc(endpoints));
  const cap = Math.max(1, Math.trunc(limit));
  const fraction = Math.min(1, Math.max(0, Number(unchangedFraction)));

  const without = (3600 / seconds) * count;
  const withEtags = without * (1 - fraction);
  const round = (n) => Math.round(n * 10) / 10;
  return {
    per_hour_without: round(without),
    per_hour_with: round(withEtags),
    saved_per_hour: round(without - withEtags),
    percent_without: round(100 * without / cap),
    percent_with: round(100 * withEtags / cap),
    limit: cap,
  };
}

/** Turn the measurement and the projection into one line. Pure. */
export function verdict(state, projection) {
  const saved = projection?.saved_per_hour ?? 0;
  const percent = projection?.percent_without ?? 0;

  if (state === 'no-etag') {
    return ['unavailable',
      'the response carried no etag, so this endpoint cannot be polled ' +
      'conditionally. Check last-modified and use if-modified-since where it ' +
      'is present.'];
  }
  if (state === 'not-honoured') {
    return ['ignored',
      'the conditional request came back 200 rather than 304. Either the ' +
      'resource genuinely changed between the two calls, or something between ' +
      'this client and GitHub is dropping the If-None-Match header, which ' +
      'silently reinstates the full cost.'];
  }
  if (state === 'billed') {
    return ['billed',
      'the 304 arrived and x-ratelimit-used still moved, which is not how ' +
      'conditional requests are documented to behave. Re-run before acting on ' +
      'it: another process sharing this token spends the same counter.'];
  }
  if (state === 'unmeasured') {
    return ['unmeasured',
      'the 304 arrived but x-ratelimit-used was missing from one of the ' +
      'responses, so the saving is real and its size is not measured here.'];
  }
  return [percent < 25 ? 'saving' : 'large-saving',
    `the 304 cost 0 request(s). At this poll rate that is ${Math.round(saved)} ` +
    `request(s) an hour, ${percent}% of the quota, currently spent on data that ` +
    'did not change.'];
}

function read(res) {
  const headers = {};
  for (const [k, v] of res.headers.entries()) headers[k.toLowerCase()] = v;
  const used = Number.parseInt(headers['x-ratelimit-used'], 10);
  return {
    status: res.status,
    etag: headers.etag ?? null,
    used: Number.isFinite(used) ? used : null,
    last_modified: headers['last-modified'] ?? null,
    limit: headers['x-ratelimit-limit'] ?? null,
  };
}

function head(token, extra = {}) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
    ...extra,
  };
}

async function main() {
  const repo = process.argv[2];
  const path = process.argv[3] ?? '/issues';
  const pollSeconds = Number.parseFloat(process.argv[4] ?? '60') || 60;
  const endpoints = Number.parseInt(process.argv[5] ?? '1', 10) || 1;
  const token = process.env.GITHUB_TOKEN;

  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  if (!repo || !repo.includes('/')) {
    console.error('usage: node github-etag-saving.mjs owner/name [/path] ' +
      '[pollSeconds] [endpoints]');
    process.exitCode = 2;
    return;
  }

  const url = `${API}/repos/${repo}${path}`;
  console.log(`probing ${url} twice: once plain, once with If-None-Match`);

  const plain = await fetch(url, { headers: head(token) });
  if (plain.status === 401) {
    console.error('401 from GitHub: GITHUB_TOKEN is missing, expired or malformed');
    process.exitCode = 2;
    return;
  }
  if (plain.status === 403 || plain.status === 404) {
    console.error(`${plain.status} from ${url}: this token cannot read that ` +
      'endpoint. GitHub answers 404 rather than 403 when a token cannot see a ' +
      'resource at all.');
    process.exitCode = 2;
    return;
  }
  const first = read(plain);
  console.log(`  plain:       ${first.status}, etag ${first.etag}, ` +
    `x-ratelimit-used ${first.used}`);

  let second = first;
  if (first.etag) {
    const conditional = await fetch(url, {
      headers: head(token, { 'If-None-Match': first.etag }),
    });
    second = read(conditional);
    console.log(`  conditional: ${second.status}, x-ratelimit-used ${second.used}`);
  } else if (first.last_modified) {
    console.warn(`  no etag, but last-modified is ${first.last_modified}: use ` +
      'if-modified-since on this endpoint instead');
  }

  const [state, report] = measure(first, second);
  const limit = Number.parseInt(first.limit, 10) || DEFAULT_LIMIT;
  const projection = project(pollSeconds, endpoints, limit, 1);
  const [level, detail] = verdict(state, projection);
  console.log(`${level}: ${detail}`);
  console.log(`  ${projection.per_hour_without} request(s)/hour now ` +
    `(${projection.percent_without}% of ${projection.limit}), ` +
    `${projection.per_hour_with}/hour with conditional requests ` +
    `(${projection.percent_with}%)`);

  if (level === 'saving' || level === 'large-saving') {
    console.log(`  repair: store ${report.etag} against this exact URL and ` +
      "credential, send it back as If-None-Match, and treat 304 as 'keep what " +
      "you have' rather than as an error.");
    console.log('  repair: keep per_page, sort and Accept stable, and key the ' +
      'cache by token: an ETag is scoped to the credential that fetched it, so ' +
      'a rotation invalidates every entry at once.');
  }
  process.exitCode = ['saving', 'large-saving', 'unavailable'].includes(level) ? 0 : 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The measurement has one honest outcome and three dishonest ones, and the tests exist to keep them apart. A <code>200</code> where a <code>304</code> was expected is not a saving that failed to materialise, it is a header that did not arrive. A missing <code>etag</code> is not a bug in the endpoint. And a <code>304</code> whose <code>used</code> counter moved anyway is most likely another process spending the same shared quota, which the report has to say rather than quietly reporting a smaller saving.",
"test_py_file": "test_github_etag_saving.py",
"test_py": '''from github_etag_saving import measure, project, verdict

ETAG = 'W/"6c1a2f9e0b7d4a3c"'


def response(status, etag=ETAG, used=None):
    return {"status": status, "etag": etag, "used": used}


def test_a_304_that_did_not_move_the_counter_is_the_finding():
    state, report = measure(response(200, used=101), response(304, used=101))
    assert state == "free"
    assert report["cost_of_unchanged_poll"] == 0
    assert report["etag"] == ETAG


def test_an_endpoint_with_no_etag_cannot_be_polled_conditionally():
    state, _ = measure(response(200, etag=None, used=10), response(200, used=11))
    assert state == "no-etag"


def test_a_200_answer_to_a_conditional_request_is_its_own_finding():
    # A proxy that strips If-None-Match reinstates the full cost silently.
    state, report = measure(response(200, used=10), response(200, used=11))
    assert state == "not-honoured"
    assert report["cost_of_unchanged_poll"] == 1


def test_a_304_that_still_billed_is_reported_rather_than_smoothed_over():
    state, report = measure(response(200, used=10), response(304, used=12))
    assert state == "billed"
    assert report["cost_of_unchanged_poll"] == 2


def test_a_missing_used_header_leaves_the_saving_unmeasured():
    state, report = measure(response(200, used=None), response(304, used=None))
    assert state == "unmeasured"
    assert report["cost_of_unchanged_poll"] is None


def test_the_projection_prices_a_real_polling_schedule():
    p = project(30, 8, 5000, 1.0)
    assert p["per_hour_without"] == 960.0
    assert p["per_hour_with"] == 0.0
    assert p["saved_per_hour"] == 960.0
    assert p["percent_without"] == 19.2


def test_a_partly_changing_workload_saves_only_part_of_it():
    p = project(60, 1, 5000, 0.75)
    assert p["per_hour_without"] == 60.0
    assert p["per_hour_with"] == 15.0
    assert p["saved_per_hour"] == 45.0


def test_nothing_unchanged_means_nothing_saved():
    p = project(60, 1, 5000, 0.0)
    assert p["saved_per_hour"] == 0.0


def test_the_projection_refuses_nonsense_inputs_instead_of_dividing_by_zero():
    p = project(0, 0, 0, 5.0)
    assert p["limit"] == 1
    assert p["per_hour_without"] == 3600.0
    assert p["per_hour_with"] == 0.0


def test_a_large_share_of_quota_is_called_out_as_such():
    level, detail = verdict("free", project(30, 8, 5000, 1.0))
    assert level == "saving"
    assert "19.2%" in detail
    assert verdict("free", project(10, 8, 5000, 1.0))[0] == "large-saving"


def test_each_unhappy_state_names_a_different_repair():
    assert verdict("no-etag", project(60, 1))[0] == "unavailable"
    assert verdict("not-honoured", project(60, 1))[0] == "ignored"
    assert verdict("billed", project(60, 1))[0] == "billed"
    assert verdict("unmeasured", project(60, 1))[0] == "unmeasured"


def test_the_ignored_state_blames_the_header_not_the_quota():
    _, detail = verdict("not-honoured", project(60, 1))
    assert "If-None-Match" in detail


def test_the_billed_state_points_at_the_shared_counter():
    _, detail = verdict("billed", project(60, 1))
    assert "shares" in detail or "sharing" in detail
''',
"test_js_file": "github-etag-saving.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { measure, project, verdict } from './github-etag-saving.mjs';

const ETAG = 'W/"6c1a2f9e0b7d4a3c"';

const response = (status, etag = ETAG, used = null) => ({ status, etag, used });

test('a 304 that did not move the counter is the finding', () => {
  const [state, report] = measure(response(200, ETAG, 101), response(304, ETAG, 101));
  assert.equal(state, 'free');
  assert.equal(report.cost_of_unchanged_poll, 0);
  assert.equal(report.etag, ETAG);
});

test('an endpoint with no etag cannot be polled conditionally', () => {
  const [state] = measure(response(200, null, 10), response(200, ETAG, 11));
  assert.equal(state, 'no-etag');
});

test('a 200 answer to a conditional request is its own finding', () => {
  const [state, report] = measure(response(200, ETAG, 10), response(200, ETAG, 11));
  assert.equal(state, 'not-honoured');
  assert.equal(report.cost_of_unchanged_poll, 1);
});

test('a 304 that still billed is reported rather than smoothed over', () => {
  const [state, report] = measure(response(200, ETAG, 10), response(304, ETAG, 12));
  assert.equal(state, 'billed');
  assert.equal(report.cost_of_unchanged_poll, 2);
});

test('a missing used header leaves the saving unmeasured', () => {
  const [state, report] = measure(response(200, ETAG, null), response(304, ETAG, null));
  assert.equal(state, 'unmeasured');
  assert.equal(report.cost_of_unchanged_poll, null);
});

test('the projection prices a real polling schedule', () => {
  const p = project(30, 8, 5000, 1);
  assert.equal(p.per_hour_without, 960);
  assert.equal(p.per_hour_with, 0);
  assert.equal(p.saved_per_hour, 960);
  assert.equal(p.percent_without, 19.2);
});

test('a partly changing workload saves only part of it', () => {
  const p = project(60, 1, 5000, 0.75);
  assert.equal(p.per_hour_without, 60);
  assert.equal(p.per_hour_with, 15);
  assert.equal(p.saved_per_hour, 45);
});

test('nothing unchanged means nothing saved', () => {
  assert.equal(project(60, 1, 5000, 0).saved_per_hour, 0);
});

test('the projection refuses nonsense inputs instead of dividing by zero', () => {
  const p = project(0, 0, 0, 5);
  assert.equal(p.limit, 1);
  assert.equal(p.per_hour_without, 3600);
  assert.equal(p.per_hour_with, 0);
});

test('a large share of quota is called out as such', () => {
  const [level, detail] = verdict('free', project(30, 8, 5000, 1));
  assert.equal(level, 'saving');
  assert.match(detail, /19\\.2%/);
  assert.equal(verdict('free', project(10, 8, 5000, 1))[0], 'large-saving');
});

test('each unhappy state names a different repair', () => {
  assert.equal(verdict('no-etag', project(60, 1))[0], 'unavailable');
  assert.equal(verdict('not-honoured', project(60, 1))[0], 'ignored');
  assert.equal(verdict('billed', project(60, 1))[0], 'billed');
  assert.equal(verdict('unmeasured', project(60, 1))[0], 'unmeasured');
});

test('the ignored state blames the header, not the quota', () => {
  assert.match(verdict('not-honoured', project(60, 1))[1], /If-None-Match/);
});

test('the billed state points at the shared counter', () => {
  assert.match(verdict('billed', project(60, 1))[1], /shar/);
});
''',
"faq": [
 ("Does a 304 really cost nothing against the rate limit?",
  "Yes, and you do not have to believe it on principle. x-ratelimit-used comes back on the 304 exactly as it does on the 200, so make the plain request, note the number, repeat with If-None-Match, and compare. A difference of zero is the measurement. That is what the script does and why its output is a number rather than a recommendation."),
 ("Why did my conditional request come back 200 instead of 304?",
  "Either the resource changed between the two calls, which on a busy repository is entirely possible, or the If-None-Match header did not arrive. Proxies and some HTTP client wrappers strip or rewrite conditional headers. Re-run against a quiet endpoint to tell the two apart: if a repository's metadata still answers 200 to its own ETag, something in the path is removing the header."),
 ("Do ETags survive a token rotation?",
  "No. An ETag is scoped to the credential that fetched it, so rotating a personal access token or minting a new installation token invalidates every cached entry at once. The symptom is a quota spike on a fixed schedule with no error attached to it, which is why the cache should be keyed by token as well as by URL."),
 ("What about endpoints that send no etag?",
  "Look for last-modified and send if-modified-since instead; the discount is the same. A few endpoints support neither, and for those the answer is not caching but asking less often, or replacing the poll with a webhook so GitHub tells you when something changed instead of you asking."),
 ("Should I use conditional requests or webhooks?",
  "Webhooks where you can, conditional requests everywhere else. A webhook removes the poll entirely; a conditional request makes the poll free. They are not alternatives so much as layers, and most integrations end up with both because there is always some state that no event describes."),
],
"related": [
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
 ("/github/secondary-limit-concurrency/", "Over 100 concurrent requests trips a limit"),
 ("/github/per-page-default-30/", "per_page is unset so every list costs more"),
],
"citations": [CITE_BEST, CITE_GETTING_STARTED, CITE_REST_LIMITS, CITE_RATE_ENDPOINT],
},

]
