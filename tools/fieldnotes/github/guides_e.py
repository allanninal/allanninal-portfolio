#!/usr/bin/env python3
"""/github/ field notes, batch E — the writing.

Four more rate-limit notes, and the risk in writing four of them at once is that
they all become the same note: you ran out, wait. They are not the same problem
and they are not found the same way, so each script here probes a different
surface and stops at a different conclusion.

  rate-limit-core-exhausted           the hourly core bucket. Arithmetic over
                                      used, limit and reset: does the drain you
                                      are running fit in the window that is left?
  rate-limit-unauthenticated          not a quota problem at all. An identity
                                      check: which tier is this request in, and
                                      if it is the anonymous one, why.
  secondary-limit-points-per-minute   a per-endpoint cost model. What is the
                                      highest request rate one path can sustain
                                      before points or CPU time bind?
  search-bucket-exhausted             a different bucket entirely. Search resets
                                      every minute, not every hour, and a loop
                                      that searches per repository empties it
                                      before core has noticed.

Read only throughout. GET /rate_limit is the workhorse because it is the one
endpoint that does not spend what it reports.
"""

CITE_REST_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_BEST = ("Best practices for using the REST API — GitHub Docs",
             "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_RATE_ENDPOINT = ("Rate limit — GitHub REST API",
                      "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_TROUBLESHOOT = ("Troubleshooting the REST API — GitHub Docs",
                     "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_APP_LIMITS = ("Rate limits for GitHub Apps — GitHub Docs",
                   "https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/rate-limits-for-github-apps")
CITE_AUTHENTICATING = ("Authenticating to the REST API — GitHub Docs",
                       "https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api")
CITE_PAT = ("Managing your personal access tokens — GitHub Docs",
            "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_GRAPHQL_LIMITS = ("Rate limits and node limits for the GraphQL API — GitHub Docs",
                       "https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api")
CITE_SEARCH = ("Search — GitHub REST API",
               "https://docs.github.com/en/rest/search/search")
CITE_SEARCH_SYNTAX = ("Searching issues and pull requests — GitHub Docs",
                      "https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests")

GUIDES = [

{
"slug": "rate-limit-core-exhausted",
"title": "Core REST quota is exhausted and every call returns 403",
"description": "GET /rate_limit is free and publishes used, limit and reset. Those three numbers say whether the drain you are running fits in the window left.",
"h1": "core REST quota is exhausted and every call returns 403",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api rate limit exceeded", "github 5000 requests per hour",
             "x-ratelimit-remaining 0", "github core rate limit reset",
             "api rate limit exceeded for user id"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every endpoint fails at once, with the same status, in the same second. That pattern says outage or bad credentials, and it is neither: the hourly bucket is empty, and an empty bucket refuses everything equally. The awkward part is that by the time you are reading the 403 the interesting question has already gone past. Not <em>are we out</em>, but <em>at what rate did we spend it, and would that rate have fitted</em>.",
"short_answer": """<p><code>GET /rate_limit</code> answers it, and it is the only endpoint in the API that does not count against the limit it reports. Read <code>resources.core</code>: <code>limit</code>, <code>used</code>, <code>remaining</code> and <code>reset</code>. A <code>remaining</code> of <code>0</code> with a <code>reset</code> in the future is the whole diagnosis, and the wait is <code>reset</code> minus now.</p>
<p>The useful version of the check runs <em>before</em> that. The core window is a fixed hour, so <code>used</code> divided by the time elapsed since the window opened is your average drain per minute, and <code>remaining</code> divided by the minutes left is the rate you can still afford. When the first number is larger than the second you are going to run out, and the script can name the minute.</p>""",
"problem": """<p>The failure is total, which misleads. A permissions problem breaks one endpoint; a bad token breaks authenticated calls and leaves public ones working; an outage has a status page. An exhausted bucket breaks every non-search REST call for the same token, everywhere, instantly, and then fixes itself an hour later without anyone touching anything. Half the time the incident is closed as "transient" and recurs the next day at the same hour.</p>
<p>The message names the account, not the process: <code>"API rate limit exceeded for user ID 12345."</code> That is a genuine dead end, because the bucket is per token and shared by everything holding it. The nightly sync, the dashboard that refreshes every thirty seconds, the bot, and the developer running a script by hand are all drawing on one 5,000. The API reports the drain and never says who caused it.</p>
<p>And the drain is rarely steady. A job that fires 3,000 requests in four minutes and then idles looks identical, an hour later, to a job that spent 3,000 evenly. They need opposite repairs, and the only way to tell them apart is to look while it is happening.</p>""",
"why": """<p><strong>The window is fixed, not sliding.</strong> The core bucket refills in full at <code>reset</code>, an epoch second that stays put for the whole hour. That is what makes the forecast possible: <code>reset</code> minus 3,600 is when the window opened, so the elapsed time is known, so <code>used / elapsed</code> is a real rate rather than a guess.</p>
<p><strong>The measurement is free.</strong> <code>GET /rate_limit</code> is documented as not counting against the primary rate limit. You can poll it every ten seconds during an incident without making the incident worse, which is not true of any other diagnostic in this section.</p>
<p><strong>Average drain and current drain are different numbers.</strong> Forty minutes into a window, <code>used</code> at 4,000 gives an average of 100 a minute. If the last two of those minutes spent nothing, you are idle and fine. If they spent 400, you have four minutes left, not twenty. One sample gives you the average; two samples a minute apart give you the rate you are actually running at, and the gap between them is the diagnosis.</p>
<p><strong>The limit is per token, not per process or per IP.</strong> Authenticated users get 5,000 an hour, 15,000 on Enterprise Cloud, and a GitHub App installation scales with installed repositories and users up to 12,500. Splitting a workload across four machines that share one token splits nothing.</p>
<p><strong>Not every 403 is this.</strong> A refusal with <code>x-ratelimit-remaining</code> still in the thousands is a secondary limit, which is a different mechanism with a different repair. Check the number before you accept the story the message tells.</p>""",
"steps": [
 {"h": "Ask the one endpoint that does not charge you for asking",
  "body": """<p><code>GET /rate_limit</code> returns every bucket the token has: <code>core</code>, <code>search</code>, <code>graphql</code>, <code>code_search</code> and the rest. Only <code>core</code> is the one that breaks ordinary REST calls. Read <code>used</code>, <code>limit</code> and <code>reset</code> from it, and ignore the deprecated top-level <code>rate</code> field, which mirrors <code>core</code> and exists only for compatibility.</p>"""},
 {"h": "Turn reset into an elapsed time",
  "body": """<p>The window is an hour, so it opened at <code>reset - 3600</code>. Elapsed is now minus that. This is the step everyone skips, and it is the one that converts a static counter into a rate: 2,400 used means nothing until you know whether it took fifty minutes or five.</p>"""},
 {"h": "Compare the drain against what you can still afford",
  "body": """<p>Two rates, both per minute. Drain is <code>used / elapsed_minutes</code>. Affordable is <code>remaining / minutes_left</code>. If drain is under affordable you finish the hour with quota to spare; if it is over, divide <code>remaining</code> by drain and you have the number of minutes until the bucket is empty.</p>"""},
 {"h": "Take a second sample to catch a spike",
  "body": """<p>Sample <code>used</code> again thirty or sixty seconds later. The difference over the gap is the drain right now, and it is the number to act on. If <code>reset</code> changed between the two samples the window rolled over and the counter went back to nearly zero, so report that rather than a nonsense negative rate.</p>"""},
 {"h": "Spend less rather than waiting better",
  "body": """<p>Waiting for reset is not a fix, it is a delay. The repairs that hold are conditional requests, because a <code>304</code> does not count at all; one GraphQL query in place of fifty REST calls, because GraphQL bills to a separate bucket; a webhook instead of a poll, because then GitHub tells you; and, when the workload is genuinely that big, a GitHub App installation token whose limit scales.</p>"""},
],
"verify": """<p>Run it again with a watch interval and confirm the drain sits under the affordable rate for the rest of the window.</p>
<pre><code class="language-bash">python3 github_quota_forecast.py --watch 30
# clear: drain 41/min against 78/min affordable, 3,102 left with 40 min to reset</code></pre>""",
"code_intro": "Three pure functions do the work and none of them touch the network: one turns a single <code>/rate_limit</code> body into an average drain and a projection, one turns two samples into the drain right now, and one turns both into a verdict. The network layer is a single GET that costs nothing. Splitting it this way is not tidiness — an exhausted bucket is inconvenient to reproduce on demand, and every interesting case here is one you want to test without waiting an hour for it.",
"py_file": "github_quota_forecast.py",
"py": '''"""Forecast when the core REST bucket empties, from three published numbers.

Read only. Every request is a GET, and GET /rate_limit is documented as not
counting against the primary rate limit, so this never spends what it measures.

The forecast is the point. A bucket that is already empty needs no analysis,
only a clock. The question worth asking is whether the drain running right now
fits inside the window that is left, and that is arithmetic over used, limit
and reset.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_quota_forecast")

API = "https://api.github.com"
UA = "github-quota-forecast/1.0"

# The core bucket is a fixed one-hour window that refills in full at `reset`,
# which is what makes the elapsed time knowable from a single sample.
WINDOW = 3600.0


def window_burn(used, limit, reset, now, window=WINDOW):
    """Average drain since this window opened, and where it lands. Pure.

    reset is an epoch second and the window is fixed, so the window opened at
    reset - window. That is the whole trick: it converts a counter, which says
    nothing on its own, into a rate. 2,400 used is comfortable at minute fifty
    and an emergency at minute five.
    """
    try:
        used = max(0, int(used))
        limit = max(1, int(limit))
        left = float(reset) - float(now)
    except (TypeError, ValueError):
        return None

    # A reset further away than the window itself means the clocks disagree.
    # Clamping is honest here: it makes elapsed small, which makes the drain
    # look high, which is the safe direction to be wrong in.
    left = min(max(left, 0.0), window)
    elapsed = max(1.0, window - left)
    remaining = max(0, limit - used)

    per_min = used / (elapsed / 60.0)
    left_min = left / 60.0
    projected = used + per_min * left_min
    # What you may still spend per minute and finish the window on zero.
    affordable = remaining / left_min if left_min > 0 else float(remaining)

    if remaining <= 0:
        empty_in = 0.0
    elif per_min <= 0:
        empty_in = None
    else:
        empty_in = remaining / (per_min / 60.0)
        if empty_in > left:
            empty_in = None  # the window refills first

    return {"used": used, "limit": limit, "remaining": remaining,
            "elapsed": round(elapsed, 1), "left": round(left, 1),
            "per_min": round(per_min, 2), "affordable": round(affordable, 2),
            "projected": round(projected), "empty_in": empty_in}


def sample_burn(first, second):
    """Drain between two samples of the same bucket. Pure.

    Returns (state, per_min). The average over the window is history; this is
    the rate right now, and the two disagree exactly when it matters, which is
    when a job burst and stopped or is bursting and has not stopped.

    A window that rolled between the samples resets `used` to nearly zero, so
    the difference goes negative. That is not a negative drain, it is a refill,
    and reporting it as "rolled" beats reporting it as a rate.
    """
    if not first or not second:
        return ("single", None)
    try:
        u1, r1, t1 = int(first["used"]), float(first["reset"]), float(first["at"])
        u2, r2, t2 = int(second["used"]), float(second["reset"]), float(second["at"])
    except (KeyError, TypeError, ValueError):
        return ("single", None)

    gap = t2 - t1
    if gap <= 0:
        return ("no-gap", None)
    if r2 != r1 or u2 < u1:
        return ("rolled", None)
    return ("measured", round((u2 - u1) / (gap / 60.0), 2))


def verdict(win, instant=("single", None), tight=0.8):
    """Turn the arithmetic into one finding. Pure.

    Prefers the measured drain over the window average when there is one,
    because the average is a claim about the past and the measurement is a
    claim about now.
    """
    if not win:
        return ("unreadable", "the rate-limit body did not contain usable numbers")

    state, measured = instant
    drain = measured if (state == "measured" and measured is not None) else win["per_min"]
    source = ("measured over the sample gap" if state == "measured"
              else "averaged over the window so far")
    mins = win["left"] / 60.0

    if win["remaining"] <= 0:
        return ("exhausted",
                "0 of %d left. Every non-search REST call refuses until reset, "
                "in %d second(s). Waiting is not the repair, spending less is."
                % (win["limit"], int(win["left"])))

    if drain > win["affordable"] and drain > 0:
        empty = win["remaining"] / (drain / 60.0)
        return ("will-exhaust",
                "drain is %.1f/min (%s) against %.1f/min affordable. %d left "
                "empties in about %d minute(s), %d minute(s) before reset."
                % (drain, source, win["affordable"], win["remaining"],
                   round(empty / 60.0), max(0, round(mins - empty / 60.0))))

    if (state == "measured" and measured is not None
            and win["per_min"] > 0 and measured > win["per_min"] * 2):
        return ("spiky",
                "drain is %.1f/min right now against a %.1f/min average for the "
                "window. The bucket fits it today, but the average is hiding a "
                "burst and a longer burst will not fit."
                % (measured, win["per_min"]))

    if win["used"] >= win["limit"] * tight:
        return ("tight",
                "%d of %d used with %d minute(s) to reset. The current drain of "
                "%.1f/min fits, but there is no room for a second consumer on "
                "this token." % (win["used"], win["limit"], round(mins), drain))

    return ("clear",
            "drain %.1f/min against %.1f/min affordable, %d left with %d "
            "minute(s) to reset."
            % (drain, win["affordable"], win["remaining"], round(mins)))


def sample(session):
    """One free GET of the whole rate-limit document."""
    r = session.get(API + "/rate_limit", timeout=30)
    if r.status_code != 200:
        log.error("GET /rate_limit returned %d: %s", r.status_code, r.text[:200])
        return None
    body = r.json()
    return {"resources": body.get("resources", {}), "at": time.time()}


def bucket(snapshot, name):
    """Pull one named bucket out of a snapshot as a flat dict."""
    b = (snapshot or {}).get("resources", {}).get(name) or {}
    return {"used": b.get("used", 0), "limit": b.get("limit", 0),
            "reset": b.get("reset", 0), "remaining": b.get("remaining", 0),
            "at": (snapshot or {}).get("at", 0)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--resource", default="core",
                    help="which bucket to forecast (default core)")
    ap.add_argument("--watch", type=int, default=0, metavar="SECONDS",
                    help="take a second sample after this many seconds to "
                         "measure the drain right now (0 = one sample only)")
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
        "User-Agent": UA,
    })

    first = sample(session)
    if first is None:
        return 2

    for name, b in sorted(first["resources"].items()):
        log.info("bucket %-22s %5s / %-6s remaining %s",
                 name, b.get("used"), b.get("limit"), b.get("remaining"))

    second = None
    if args.watch > 0:
        log.info("second sample in %d second(s)", args.watch)
        time.sleep(args.watch)
        second = sample(session)

    b1 = bucket(first, args.resource)
    b2 = bucket(second, args.resource) if second else None
    win = window_burn(b1["used"], b1["limit"], b1["reset"], first["at"])
    instant = sample_burn(b1, b2)
    state, detail = verdict(win, instant)

    if instant[0] == "rolled":
        log.info("the window rolled between samples: the bucket refilled, so "
                 "there is no drain to measure across that gap")
    log.info("%s: %s", state, detail)

    if state in ("exhausted", "will-exhaust", "tight", "spiky"):
        log.info("repair: send If-None-Match with the etag you already got "
                 "back. A 304 Not Modified does not count against this bucket "
                 "at all, so unchanged data becomes free.")
        log.info("repair: replace per-item REST reads with one GraphQL query. "
                 "GraphQL is billed to a separate bucket, so moving work there "
                 "removes it from this one twice over.")
        log.info("repair: stop polling for changes and subscribe to a webhook, "
                 "so the change arrives instead of being asked for every "
                 "thirty seconds by every consumer of this token.")
        log.info("repair: if the workload is genuinely this large, "
                 "authenticate as a GitHub App installation. That limit scales "
                 "with installed repositories and users, up to 12,500 an hour.")

    print(json.dumps({"resource": args.resource, "state": state,
                      "window": win, "instant": {"state": instant[0],
                                                 "per_min": instant[1]}},
                     indent=2))
    return 1 if state in ("exhausted", "will-exhaust") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-quota-forecast.mjs",
"js": '''/**
 * Forecast when the core REST bucket empties, from three published numbers.
 *
 * Read only. Every request is a GET, and GET /rate_limit does not count
 * against the primary rate limit, so this never spends what it measures.
 */
const API = 'https://api.github.com';
const UA = 'github-quota-forecast/1.0';

// The core bucket is a fixed one-hour window that refills in full at `reset`.
export const WINDOW = 3600;

/**
 * Average drain since this window opened, and where it lands. Pure.
 * reset - WINDOW is when the window opened, which turns a counter into a rate.
 */
export function windowBurn(used, limit, reset, now, window = WINDOW) {
  const u = Number.parseInt(used, 10);
  const l = Number.parseInt(limit, 10);
  const r = Number(reset);
  const t = Number(now);
  if (!Number.isFinite(u) || !Number.isFinite(l) || !Number.isFinite(r) || !Number.isFinite(t)) {
    return null;
  }
  const usedN = Math.max(0, u);
  const limitN = Math.max(1, l);
  // Clamped: a reset further away than the window means the clocks disagree,
  // and erring towards a high drain is the safe direction.
  const left = Math.min(Math.max(r - t, 0), window);
  const elapsed = Math.max(1, window - left);
  const remaining = Math.max(0, limitN - usedN);

  const perMin = usedN / (elapsed / 60);
  const leftMin = left / 60;
  const projected = usedN + perMin * leftMin;
  const affordable = leftMin > 0 ? remaining / leftMin : remaining;

  let emptyIn;
  if (remaining <= 0) emptyIn = 0;
  else if (perMin <= 0) emptyIn = null;
  else {
    const secs = remaining / (perMin / 60);
    emptyIn = secs > left ? null : secs;
  }

  return {
    used: usedN, limit: limitN, remaining,
    elapsed: Math.round(elapsed * 10) / 10,
    left: Math.round(left * 10) / 10,
    per_min: Math.round(perMin * 100) / 100,
    affordable: Math.round(affordable * 100) / 100,
    projected: Math.round(projected),
    empty_in: emptyIn,
  };
}

/**
 * Drain between two samples of the same bucket. Pure.
 * A window that rolled resets `used`, so the difference goes negative. That is
 * a refill, not a negative rate, and it is reported as one.
 */
export function sampleBurn(first, second) {
  if (!first || !second) return ['single', null];
  const u1 = Number.parseInt(first.used, 10);
  const u2 = Number.parseInt(second.used, 10);
  const r1 = Number(first.reset);
  const r2 = Number(second.reset);
  const t1 = Number(first.at);
  const t2 = Number(second.at);
  if (![u1, u2, r1, r2, t1, t2].every(Number.isFinite)) return ['single', null];

  const gap = t2 - t1;
  if (gap <= 0) return ['no-gap', null];
  if (r2 !== r1 || u2 < u1) return ['rolled', null];
  return ['measured', Math.round(((u2 - u1) / (gap / 60)) * 100) / 100];
}

/**
 * Turn the arithmetic into one finding. Pure.
 * Prefers the measured drain: the average is a claim about the past.
 */
export function verdict(win, instant = ['single', null], tight = 0.8) {
  if (!win) return ['unreadable', 'the rate-limit body did not contain usable numbers'];

  const [state, measured] = instant;
  const drain = (state === 'measured' && measured !== null) ? measured : win.per_min;
  const source = state === 'measured'
    ? 'measured over the sample gap'
    : 'averaged over the window so far';
  const mins = win.left / 60;

  if (win.remaining <= 0) {
    return ['exhausted',
      `0 of ${win.limit} left. Every non-search REST call refuses until reset, ` +
      `in ${Math.trunc(win.left)} second(s). Waiting is not the repair, ` +
      'spending less is.'];
  }

  if (drain > win.affordable && drain > 0) {
    const empty = win.remaining / (drain / 60);
    return ['will-exhaust',
      `drain is ${drain.toFixed(1)}/min (${source}) against ` +
      `${win.affordable.toFixed(1)}/min affordable. ${win.remaining} left ` +
      `empties in about ${Math.round(empty / 60)} minute(s), ` +
      `${Math.max(0, Math.round(mins - empty / 60))} minute(s) before reset.`];
  }

  if (state === 'measured' && measured !== null && win.per_min > 0
      && measured > win.per_min * 2) {
    return ['spiky',
      `drain is ${measured.toFixed(1)}/min right now against a ` +
      `${win.per_min.toFixed(1)}/min average for the window. The bucket fits ` +
      'it today, but the average is hiding a burst and a longer burst will not fit.'];
  }

  if (win.used >= win.limit * tight) {
    return ['tight',
      `${win.used} of ${win.limit} used with ${Math.round(mins)} minute(s) to ` +
      `reset. The current drain of ${drain.toFixed(1)}/min fits, but there is ` +
      'no room for a second consumer on this token.'];
  }

  return ['clear',
    `drain ${drain.toFixed(1)}/min against ${win.affordable.toFixed(1)}/min ` +
    `affordable, ${win.remaining} left with ${Math.round(mins)} minute(s) to reset.`];
}

async function sample(token) {
  const res = await fetch(`${API}/rate_limit`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  if (res.status !== 200) {
    console.error(`GET /rate_limit returned ${res.status}: ${(await res.text()).slice(0, 200)}`);
    return null;
  }
  const body = await res.json();
  return { resources: body.resources ?? {}, at: Date.now() / 1000 };
}

const bucket = (snapshot, name) => {
  const b = snapshot?.resources?.[name] ?? {};
  return {
    used: b.used ?? 0, limit: b.limit ?? 0,
    reset: b.reset ?? 0, remaining: b.remaining ?? 0,
    at: snapshot?.at ?? 0,
  };
};

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const resource = process.argv[2] ?? 'core';
  const watch = Math.max(0, Number.parseInt(process.argv[3] ?? '0', 10) || 0);

  const first = await sample(token);
  if (!first) { process.exitCode = 2; return; }

  for (const [name, b] of Object.entries(first.resources).sort()) {
    console.log(`bucket ${name.padEnd(22)} ${b.used} / ${b.limit} remaining ${b.remaining}`);
  }

  let second = null;
  if (watch > 0) {
    console.log(`second sample in ${watch} second(s)`);
    await new Promise((r) => { setTimeout(r, watch * 1000); });
    second = await sample(token);
  }

  const b1 = bucket(first, resource);
  const b2 = second ? bucket(second, resource) : null;
  const win = windowBurn(b1.used, b1.limit, b1.reset, first.at);
  const instant = sampleBurn(b1, b2);
  const [state, detail] = verdict(win, instant);

  if (instant[0] === 'rolled') {
    console.log('the window rolled between samples: the bucket refilled, so ' +
      'there is no drain to measure across that gap');
  }
  console.log(`${state}: ${detail}`);

  if (['exhausted', 'will-exhaust', 'tight', 'spiky'].includes(state)) {
    console.log('repair: send If-None-Match with the etag you already got back. ' +
      'A 304 Not Modified does not count against this bucket at all.');
    console.log('repair: replace per-item REST reads with one GraphQL query, ' +
      'which is billed to a separate bucket entirely.');
    console.log('repair: stop polling and subscribe to a webhook, so the change ' +
      'arrives instead of being asked for every thirty seconds.');
    console.log('repair: for a genuinely large workload, authenticate as a ' +
      'GitHub App installation, whose limit scales up to 12,500 an hour.');
  }

  console.log(JSON.stringify({
    resource, state, window: win,
    instant: { state: instant[0], per_min: instant[1] },
  }, null, 2));
  process.exitCode = (state === 'exhausted' || state === 'will-exhaust') ? 1 : 0;
}

// Only run when invoked directly, so importing this from the test file does not
// start main(), fail on the missing token and set a non-zero exit code.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones where a plausible implementation quietly returns nonsense: a window that rolled between the two samples, so <code>used</code> went backwards and a naive subtraction reports a negative drain; a <code>reset</code> that is further away than the window itself, which is what a skewed clock looks like; and the minute after a window opens, when elapsed time is nearly zero and dividing by it produces an infinite rate. Each of those is a real reading from a real API and none of them is an error.",
"test_py_file": "test_github_quota_forecast.py",
"test_py": '''from github_quota_forecast import window_burn, sample_burn, verdict

NOW = 1_800_000_000.0


def at_minute(minute, used, limit=5000):
    """A window that opened `minute` minutes ago with `used` spent."""
    reset = NOW + (3600 - minute * 60)
    return window_burn(used, limit, reset, NOW)


def test_used_alone_says_nothing_until_it_is_a_rate():
    early = at_minute(5, 2400)
    late = at_minute(50, 2400)
    assert early["per_min"] > late["per_min"] * 5
    assert early["remaining"] == late["remaining"] == 2600


def test_a_steady_drain_that_fits_leaves_the_window_intact():
    win = at_minute(30, 1500)
    assert win["per_min"] == 50.0
    assert win["affordable"] == round(3500 / 30.0, 2)
    assert win["empty_in"] is None


def test_a_drain_that_does_not_fit_names_the_minute():
    win = at_minute(30, 4000)
    assert win["per_min"] > win["affordable"]
    assert win["empty_in"] is not None
    assert 400 < win["empty_in"] < 500


def test_an_empty_bucket_empties_in_zero_seconds():
    win = at_minute(45, 5000)
    assert win["remaining"] == 0
    assert win["empty_in"] == 0.0


def test_the_first_minute_does_not_divide_by_zero():
    win = window_burn(3, 5000, NOW + 3600, NOW)
    assert win["elapsed"] == 1.0
    assert win["per_min"] == 180.0


def test_a_reset_beyond_the_window_is_clamped_rather_than_trusted():
    # A skewed clock. Clamping makes elapsed small and the drain look high,
    # which is the safe direction to be wrong in.
    win = window_burn(100, 5000, NOW + 9000, NOW)
    assert win["left"] == 3600.0
    assert win["elapsed"] == 1.0


def test_unusable_numbers_return_nothing_rather_than_a_guess():
    assert window_burn(None, 5000, NOW, NOW) is None
    assert window_burn("many", 5000, NOW, NOW) is None


def test_two_samples_measure_the_drain_right_now():
    first = {"used": 1000, "reset": NOW + 1800, "at": NOW}
    second = {"used": 1030, "reset": NOW + 1800, "at": NOW + 30}
    assert sample_burn(first, second) == ("measured", 60.0)


def test_a_rolled_window_is_a_refill_not_a_negative_drain():
    first = {"used": 4900, "reset": NOW + 10, "at": NOW}
    second = {"used": 12, "reset": NOW + 3610, "at": NOW + 30}
    assert sample_burn(first, second) == ("rolled", None)


def test_one_sample_is_reported_as_one_sample():
    assert sample_burn({"used": 1, "reset": NOW, "at": NOW}, None) == ("single", None)
    assert sample_burn(None, None)[0] == "single"


def test_two_samples_at_the_same_instant_measure_nothing():
    s = {"used": 10, "reset": NOW + 60, "at": NOW}
    assert sample_burn(s, dict(s, used=20)) == ("no-gap", None)


def test_exhausted_reports_the_wait_and_refuses_to_call_it_a_fix():
    state, detail = verdict(at_minute(45, 5000))
    assert state == "exhausted"
    assert "900 second(s)" in detail
    assert "Waiting is not the repair" in detail


def test_a_measured_spike_overrides_a_comfortable_average():
    win = at_minute(50, 1000)  # a 20/min average with 4,000 still in the bucket
    state, detail = verdict(win, ("measured", 600.0))
    assert state == "will-exhaust"
    assert "measured over the sample gap" in detail


def test_a_burst_that_still_fits_is_flagged_as_spiky_not_safe():
    win = at_minute(10, 200)  # 20/min average, 4800 left over 50 minutes
    state, _ = verdict(win, ("measured", 60.0))
    assert state == "spiky"


def test_eighty_percent_used_is_tight_even_when_the_drain_fits():
    win = at_minute(55, 4100)
    state, detail = verdict(win, ("measured", 1.0))
    assert state == "tight"
    assert "second consumer" in detail


def test_a_healthy_window_is_clear():
    state, detail = verdict(at_minute(30, 900), ("measured", 30.0))
    assert state == "clear"
    assert "4100 left" in detail


def test_an_unreadable_body_is_not_reported_as_healthy():
    assert verdict(None)[0] == "unreadable"
''',
"test_js_file": "github-quota-forecast.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { windowBurn, sampleBurn, verdict } from './github-quota-forecast.mjs';

const NOW = 1800000000;

/** A window that opened `minute` minutes ago with `used` spent. */
const atMinute = (minute, used, limit = 5000) =>
  windowBurn(used, limit, NOW + (3600 - minute * 60), NOW);

test('used alone says nothing until it is a rate', () => {
  const early = atMinute(5, 2400);
  const late = atMinute(50, 2400);
  assert.ok(early.per_min > late.per_min * 5);
  assert.equal(early.remaining, 2600);
  assert.equal(late.remaining, 2600);
});

test('a steady drain that fits leaves the window intact', () => {
  const win = atMinute(30, 1500);
  assert.equal(win.per_min, 50);
  assert.equal(win.affordable, Math.round((3500 / 30) * 100) / 100);
  assert.equal(win.empty_in, null);
});

test('a drain that does not fit names the minute', () => {
  const win = atMinute(30, 4000);
  assert.ok(win.per_min > win.affordable);
  assert.ok(win.empty_in > 400 && win.empty_in < 500);
});

test('an empty bucket empties in zero seconds', () => {
  const win = atMinute(45, 5000);
  assert.equal(win.remaining, 0);
  assert.equal(win.empty_in, 0);
});

test('the first minute does not divide by zero', () => {
  const win = windowBurn(3, 5000, NOW + 3600, NOW);
  assert.equal(win.elapsed, 1);
  assert.equal(win.per_min, 180);
});

test('a reset beyond the window is clamped rather than trusted', () => {
  const win = windowBurn(100, 5000, NOW + 9000, NOW);
  assert.equal(win.left, 3600);
  assert.equal(win.elapsed, 1);
});

test('unusable numbers return nothing rather than a guess', () => {
  assert.equal(windowBurn(null, 5000, NOW, NOW), null);
  assert.equal(windowBurn('many', 5000, NOW, NOW), null);
});

test('two samples measure the drain right now', () => {
  const first = { used: 1000, reset: NOW + 1800, at: NOW };
  const second = { used: 1030, reset: NOW + 1800, at: NOW + 30 };
  assert.deepEqual(sampleBurn(first, second), ['measured', 60]);
});

test('a rolled window is a refill, not a negative drain', () => {
  const first = { used: 4900, reset: NOW + 10, at: NOW };
  const second = { used: 12, reset: NOW + 3610, at: NOW + 30 };
  assert.deepEqual(sampleBurn(first, second), ['rolled', null]);
});

test('one sample is reported as one sample', () => {
  assert.deepEqual(sampleBurn({ used: 1, reset: NOW, at: NOW }, null), ['single', null]);
  assert.equal(sampleBurn(null, null)[0], 'single');
});

test('two samples at the same instant measure nothing', () => {
  const s = { used: 10, reset: NOW + 60, at: NOW };
  assert.deepEqual(sampleBurn(s, { ...s, used: 20 }), ['no-gap', null]);
});

test('exhausted reports the wait and refuses to call it a fix', () => {
  const [state, detail] = verdict(atMinute(45, 5000));
  assert.equal(state, 'exhausted');
  assert.match(detail, /900 second\\(s\\)/);
  assert.match(detail, /Waiting is not the repair/);
});

test('a measured spike overrides a comfortable average', () => {
  const [state, detail] = verdict(atMinute(50, 1000), ['measured', 600]);
  assert.equal(state, 'will-exhaust');
  assert.match(detail, /measured over the sample gap/);
});

test('a burst that still fits is flagged as spiky, not safe', () => {
  assert.equal(verdict(atMinute(10, 200), ['measured', 60])[0], 'spiky');
});

test('eighty percent used is tight even when the drain fits', () => {
  const [state, detail] = verdict(atMinute(55, 4100), ['measured', 1]);
  assert.equal(state, 'tight');
  assert.match(detail, /second consumer/);
});

test('a healthy window is clear', () => {
  const [state, detail] = verdict(atMinute(30, 900), ['measured', 30]);
  assert.equal(state, 'clear');
  assert.match(detail, /4100 left/);
});

test('an unreadable body is not reported as healthy', () => {
  assert.equal(verdict(null)[0], 'unreadable');
});
''',
"faq": [
 ("Does calling GET /rate_limit use up part of my rate limit?",
  "No. It is documented as not counting against the primary rate limit, which is what makes it usable as a monitor rather than only as a post-mortem. You can poll it every ten seconds during an incident without making the incident worse. It is the only diagnostic in this section with that property, and it is the reason this script defaults to it rather than probing a real endpoint."),
 ("Why does the error name a user ID instead of my script?",
  "Because the bucket belongs to the token, not to the process holding it. Every job, dashboard, bot and hand-run script authenticating with that token draws on the same 5,000 an hour, and the API reports the total drain without ever attributing it. That is a genuine blind spot: if you need to know which consumer spent the quota, you have to instrument the consumers, because GitHub will not tell you."),
 ("Will splitting the work across more machines help?",
  "Not if they share a token, which is the usual arrangement. The limit is per token, so four workers with one token have 5,000 between them, exactly as one worker did. Separate tokens do give separate buckets, but issuing a token per worker to dodge a limit is the kind of fix that becomes a security review later. Fewer requests is the durable version."),
 ("Is 403 always the rate limit?",
  "No, and the check that separates them takes one second. If x-ratelimit-remaining on the refused response is 0, it is this problem. If it is still in the thousands, the refusal came from somewhere else: a secondary rate limit, which throttles bursts rather than volume, or a permissions error, which GitHub also returns as 403 and sometimes as 404. Read the number before you accept the message."),
 ("How much headroom should I aim to keep?",
  "Enough that an unplanned consumer does not take you out. If the token is shared, treat 80 percent used as the ceiling rather than the target, because the remaining 20 percent is what absorbs the developer who runs a backfill by hand at four in the afternoon. If the token is genuinely single-purpose you can run closer to the line, but then the forecast matters more, not less."),
],
"related": [
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
 ("/github/per-page-default-30/", "per_page is unset so every list costs more"),
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
],
"citations": [CITE_REST_LIMITS, CITE_RATE_ENDPOINT, CITE_BEST, CITE_APP_LIMITS],
},


{
"slug": "rate-limit-unauthenticated",
"title": "Requests go out anonymous and are capped at 60 an hour",
"description": "A limit of 60 in GET /rate_limit proves the Authorization header never reached GitHub. The repair is to fail at startup rather than degrade quietly.",
"h1": "requests go out anonymous and are capped at 60 an hour",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 60 requests per hour", "api rate limit exceeded for ip address",
             "github unauthenticated rate limit", "github token not being sent",
             "github requires authentication 401"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It works on the first run and dies on the fourth. On a laptop it survives a couple of minutes; in CI, behind a shared NAT address, it is refused almost immediately and the run before yours gets the blame. Nothing in the code is wrong. The token simply is not arriving, and GitHub does not treat that as an error. It serves you anyway, as a stranger, from a bucket sixty deep.",
"short_answer": """<p>One number settles it. <code>GET /rate_limit</code> returns <code>resources.core.limit</code>, and that value is <code>60</code> for an anonymous request and <code>5000</code> or more for an authenticated one. The same value is on <code>x-ratelimit-limit</code> for any response, so it costs one round trip. Corroborate with <code>GET /user</code>: anonymous gets <code>401 {"message":"Requires authentication"}</code>, authenticated gets your login.</p>
<p>This is not a quota problem and it does not get better by spending less. It is an identity problem: the request went out without credentials, so GitHub applied the anonymous tier, which is <strong>60 an hour per originating IP address</strong> rather than per script. Everything else on that address shares it.</p>""",
"problem": """<p>The silence is the whole difficulty. Send a bad token and you get <code>401</code> immediately, which is a clear error with an obvious repair. Send <em>no</em> token and you get <code>200</code>, with real data, for a while. The failure is deferred until the sixty-first request, and by then the code has moved on and the traceback points at whatever call happened to be unlucky.</p>
<p>The message names an IP address rather than a user: <code>"API rate limit exceeded for 20.51.0.14."</code> That is easy to skim past as the same rate-limit error everyone knows, and it is the opposite one. A user ID in that message means the token arrived and its hourly quota is spent. An IP address means no token arrived at all.</p>
<p>The paths that produce it are boring, which is why they survive review. An environment variable that is exported in the shell but not in the container. A CI secret that is not exposed to pull requests from forks and resolves to an empty string. A value pasted with the surrounding quotes still attached. A client library whose default is to construct itself with no auth when the variable is missing, rather than to refuse. A copy of the <code>Bearer</code> prefix pasted into the variable as well as into the header.</p>""",
"why": """<p><strong>Anonymous is a supported tier, not a failure.</strong> Most of the REST API serves public data without credentials, so a request with no <code>Authorization</code> header is a legitimate request. GitHub answers it from the 60-an-hour bucket and moves on. Nothing warns you, because from the server's point of view nothing went wrong.</p>
<p><strong>The bucket is keyed on the address, not on you.</strong> Sixty per hour per originating IP. A laptop has that address to itself; a CI runner, a NAT gateway or a shared egress proxy does not, so the sixty is divided between every job on it and the effective allowance is whatever is left over. This is why the same code fails in minutes on CI and takes an hour to fail locally.</p>
<p><strong>An empty variable is not the same as a missing one, and both read as false.</strong> <code>GITHUB_TOKEN=""</code> is set. <code>os.environ.get("GITHUB_TOKEN")</code> returns <code>""</code>, the <code>if not token</code> guard fires, and the message says "not set" when the truth is "set to nothing". They have different repairs, and telling them apart is the first thing a check should do.</p>
<p><strong>The limit value names the tier.</strong> 60 is anonymous. 5,000 is an authenticated user, an OAuth token or the floor for a GitHub App installation. 15,000 is a user on Enterprise Cloud. Up to 12,500 is an App installation that has scaled with installed repositories and users. The one boundary that is unambiguous is 60 against anything larger, which is the only one this check needs.</p>
<p><strong>A token can be present and still not work.</strong> If the variable holds a well-formed token and <code>GET /user</code> still answers <code>401</code>, the token is expired, revoked, or something between your process and GitHub stripped the header. Those are different from "no token" and should not be reported as the same thing.</p>""",
"steps": [
 {"h": "Read the shape of the variable before you send it anywhere",
  "body": """<p>Unset, empty, whitespace only, wrapped in quotes, carrying a <code>Bearer</code> or <code>token</code> prefix that belongs in the header instead, or still holding the placeholder from the example file. Each of those is a different fix and all of them are visible locally, for free, before a single request goes out. Report a fingerprint &mdash; the recognised prefix and the length &mdash; and never the value.</p>"""},
 {"h": "Ask GET /rate_limit what tier you are in",
  "body": """<p><code>resources.core.limit</code> of <code>60</code> is proof of anonymity; anything above it is proof of authentication. The endpoint does not consume quota, so this check is free even when you are nearly out of it, and it works with any token including one whose scopes are empty.</p>"""},
 {"h": "Send the same request without the header as a control",
  "body": """<p>This is the step that turns a number into an argument. Call <code>/rate_limit</code> a second time with no <code>Authorization</code> header at all and compare. If the two calls report the same limit, the header you thought you were sending is not reaching GitHub. If they differ, it is.</p>"""},
 {"h": "Corroborate with GET /user",
  "body": """<p><code>401 Requires authentication</code> and a limit of 60 agree with each other: anonymous. A login and a limit of 5,000 agree the other way. A well-formed token with a <code>401</code> is the interesting third case &mdash; the token exists and GitHub rejected it, which is expiry, revocation or a stripped header, not a missing variable.</p>"""},
 {"h": "Make anonymous access impossible rather than merely unlikely",
  "body": """<p>Assert at startup that the limit is above 60 and exit if it is not. Three lines, once, at the top of the process. The reason this beats checking that the variable is non-empty is that it survives everything in between: the header that was built wrong, the client that silently dropped it, the proxy that stripped it. It checks the thing you actually care about, which is what GitHub thinks you are.</p>"""},
],
"verify": """<p>Run the check with the token in place. The authenticated limit and the anonymous control should disagree, and they should disagree by a lot.</p>
<pre><code class="language-bash">python3 github_auth_tier_check.py
# authenticated: limit 5000 against an anonymous control of 60, as ghp_ (40 chars)</code></pre>""",
"code_intro": "The interesting work happens before the network. One pure function inspects the environment variable's shape without ever returning its value, one maps a limit to a tier, and one combines those with two status codes into a verdict that distinguishes \"no token\" from \"a token GitHub refused\". The three requests are all GETs, two of them to <code>/rate_limit</code>, which costs nothing &mdash; and one of those deliberately carries no credentials, because a control is the only way to prove the header is missing rather than merely suspected.",
"py_file": "github_auth_tier_check.py",
"py": '''"""Prove which authentication tier your requests are actually in.

Read only. Three GETs: /rate_limit with the token, /rate_limit without it as a
control, and /user. GET /rate_limit does not count against the primary rate
limit, so the check is free in both tiers.

The token is read from the environment and never printed. What comes out is a
fingerprint: the recognised prefix and the length, which is enough to say "this
is a classic personal access token of the usual size" and not enough to use.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_auth_tier_check")

API = "https://api.github.com"
UA = "github-auth-tier-check/1.0"

ANON_LIMIT = 60

# Prefixes GitHub issues. Recognising one is not proof the token is valid; it is
# only evidence that the variable holds a token rather than a path, a URL or the
# placeholder somebody left in the example file.
PREFIXES = {
    "ghp_": "classic personal access token",
    "github_pat_": "fine-grained personal access token",
    "gho_": "OAuth app user token",
    "ghu_": "GitHub App user-to-server token",
    "ghs_": "GitHub App installation token",
    "ghr_": "GitHub App refresh token",
    "eyJ": "JSON Web Token, signed as a GitHub App",
}

PLACEHOLDERS = ("your", "xxx", "<", ">", "changeme", "replace", "example",
                "placeholder", "dummy", "here", "todo")


def inspect_secret(raw):
    """Describe the environment variable without disclosing it. Pure.

    Returns {"fingerprint", "kind", "problems"}. The distinction that matters
    most is unset against empty: both fail an `if not token` guard, both get
    reported as "not set", and they have different repairs. One is a missing
    export, the other is an export whose value did not survive.
    """
    problems = []
    if raw is None:
        return {"fingerprint": "absent", "kind": None, "problems": ["unset"]}
    if raw == "":
        return {"fingerprint": "empty string", "kind": None, "problems": ["empty"]}

    value = raw.strip()
    if not value:
        return {"fingerprint": "whitespace only", "kind": None, "problems": ["blank"]}
    if value != raw:
        problems.append("padded")

    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\\"'":
        problems.append("quoted")
        value = value[1:-1].strip()

    lowered = value.lower()
    for scheme in ("bearer ", "token "):
        if lowered.startswith(scheme):
            problems.append("scheme-included")
            value = value[len(scheme):].strip()
            lowered = value.lower()
            break

    if any(c.isspace() for c in value):
        problems.append("contains-whitespace")

    kind = None
    for prefix, name in PREFIXES.items():
        if value.startswith(prefix):
            kind = name
            break

    if kind is None:
        problems.append("unknown-prefix")
        # Only look for placeholder wording once the prefix has already failed,
        # so a real token that happens to contain "xxx" is not accused.
        if any(marker in lowered for marker in PLACEHOLDERS):
            problems.append("placeholder")

    prefix_shown = next((p for p in PREFIXES if value.startswith(p)), "unrecognised")
    return {"fingerprint": "%s (%d chars)" % (prefix_shown, len(value)),
            "kind": kind, "problems": problems}


def tier_from_limit(limit):
    """Name the tier a core limit belongs to. Pure.

    Only one boundary here is unambiguous, and it is the one that matters: 60
    against anything larger. The rest is useful colour and is labelled as such,
    because 5,000 is both an authenticated user and the floor for an App
    installation, and the API does not disambiguate them here.
    """
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return ("unknown", "no core limit was reported")

    if limit <= 0:
        return ("unknown", "a core limit of %d is not a tier" % limit)
    if limit <= ANON_LIMIT:
        return ("anonymous",
                "a core limit of %d is the anonymous tier, which is counted per "
                "originating IP address and shared with everything else on it"
                % limit)
    if limit == 5000:
        return ("authenticated",
                "5000 an hour: an authenticated user, an OAuth token, or a "
                "GitHub App installation that has not scaled beyond the floor")
    if limit == 15000:
        return ("enterprise",
                "15000 an hour: a user on GitHub Enterprise Cloud")
    if limit > 5000:
        return ("scaled",
                "%d an hour, above the 5000 floor: a GitHub App installation "
                "whose limit has grown with installed repositories and users"
                % limit)
    return ("authenticated", "%d an hour, which is above the anonymous 60" % limit)


def diagnose(authed_limit, anon_limit, user_status, secret):
    """Combine the local inspection and the two probes into one verdict. Pure.

    "No token" and "a token GitHub refused" both end in anonymous behaviour and
    they are not the same incident, so they do not get the same state.
    """
    secret = secret or {"problems": ["unset"], "fingerprint": "absent"}
    problems = secret.get("problems") or []
    tier, note = tier_from_limit(authed_limit)
    anon_tier, _ = tier_from_limit(anon_limit)

    if any(p in problems for p in ("unset", "empty", "blank")):
        return ("no-token",
                "GITHUB_TOKEN is %s, so every request goes out anonymous at 60 "
                "an hour per IP address. This is not a quota problem and "
                "spending less will not help it."
                % {"unset": "not set", "empty": "set to an empty string",
                   "blank": "whitespace only"}[problems[0]])

    if tier == "anonymous":
        if anon_tier == "anonymous":
            detail = ("the token was sent and GitHub still reports %s. The "
                      "control request without any header reports the same, so "
                      "the header is not arriving." % note)
        else:
            detail = note
        extra = ""
        if "scheme-included" in problems:
            extra = (" The variable itself starts with a scheme word, so the "
                     "header was probably built as \\"Bearer Bearer ...\\".")
        elif "quoted" in problems:
            extra = (" The variable still has its surrounding quotes, which "
                     "become part of the header value.")
        elif "padded" in problems or "contains-whitespace" in problems:
            extra = (" The variable carries whitespace, which is enough to "
                     "make the header invalid.")
        return ("anonymous", detail + extra)

    if user_status == 401:
        return ("token-rejected",
                "the variable holds %s but GET /user answered 401. The token "
                "is expired, revoked, or the header was removed between here "
                "and GitHub. That is not the same as a missing token."
                % (secret.get("kind") or "an unrecognised value"))

    if user_status == 403:
        return ("blocked",
                "authenticated at %s, but GET /user answered 403. Look at org "
                "SSO authorisation and IP allow lists rather than at the tier."
                % note)

    if user_status == 200:
        return ("authenticated",
                "%s. The anonymous control reports %s, so the header is "
                "arriving." % (note, anon_limit))

    return ("unclear",
            "core limit says %s but GET /user answered %s, so the two probes "
            "do not agree. Treat the limit as the more reliable of the two."
            % (note, user_status))


def get(url, token=None):
    """One GET. Returns (status, body-or-None, headers)."""
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": UA}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        r = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as exc:
        log.error("%s failed: %s", url, exc)
        return (0, None, {})
    try:
        body = r.json()
    except ValueError:
        body = None
    return (r.status_code, body, dict(r.headers))


def core_limit(body):
    return ((body or {}).get("resources", {}).get("core") or {}).get("limit")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--env", default="GITHUB_TOKEN",
                    help="environment variable holding the token")
    args = ap.parse_args()

    raw = os.environ.get(args.env)
    secret = inspect_secret(raw)
    log.info("%s: %s%s", args.env, secret["fingerprint"],
             ", " + secret["kind"] if secret["kind"] else "")
    for problem in secret["problems"]:
        log.warning("  variable problem: %s", problem)

    token = (raw or "").strip().strip("\\"'").strip()
    for scheme in ("Bearer ", "bearer ", "token ", "Token "):
        if token.startswith(scheme):
            token = token[len(scheme):].strip()
            break

    authed_status, authed_body, authed_headers = get(API + "/rate_limit", token or None)
    anon_status, anon_body, _ = get(API + "/rate_limit")
    user_status, user_body, _ = get(API + "/user", token or None)

    authed = core_limit(authed_body) if authed_status == 200 else None
    anon = core_limit(anon_body) if anon_status == 200 else None
    log.info("with the token:    core limit %s", authed)
    log.info("control, no token: core limit %s", anon)
    log.info("GET /user:         %s%s", user_status,
             " as " + str((user_body or {}).get("login")) if user_status == 200 else "")

    scopes = {k.lower(): v for k, v in authed_headers.items()}.get("x-oauth-scopes")
    if scopes is not None:
        log.info("x-oauth-scopes is present (%r), so this is a classic token or "
                 "an OAuth token rather than a fine-grained one",
                 scopes if scopes else "empty")

    state, detail = diagnose(authed, anon, user_status, secret)
    log.info("%s: %s", state, detail)

    if state != "authenticated":
        log.info("repair: export the token where the process can see it. In a "
                 "container that means passing it in, not exporting it in the "
                 "shell that ran the build.")
        log.info("repair: paste the value only. No surrounding quotes, no "
                 "Bearer prefix, no trailing newline from the file it came out "
                 "of.")
        log.info("repair: assert the tier at startup rather than asserting the "
                 "variable is non-empty. Add this to the top of the process:")
        log.info("  limit = get('%s/rate_limit').json()['resources']['core']"
                 "['limit']", API)
        log.info("  if limit <= %d: raise SystemExit('unauthenticated: refusing "
                 "to run at 60 requests an hour')", ANON_LIMIT)

    print(json.dumps({"state": state, "fingerprint": secret["fingerprint"],
                      "problems": secret["problems"],
                      "authenticated_limit": authed, "anonymous_limit": anon,
                      "user_status": user_status,
                      "tier": tier_from_limit(authed)[0]}, indent=2))
    return 0 if state == "authenticated" else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-auth-tier-check.mjs",
"js": '''/**
 * Prove which authentication tier your requests are actually in.
 *
 * Read only. Three GETs: /rate_limit with the token, /rate_limit without it as
 * a control, and /user. GET /rate_limit does not count against the primary
 * rate limit, so the check is free in both tiers.
 *
 * The token is read from the environment and never printed.
 */
const API = 'https://api.github.com';
const UA = 'github-auth-tier-check/1.0';

export const ANON_LIMIT = 60;

// Recognising a prefix is not proof the token is valid; it is evidence that the
// variable holds a token rather than a path, a URL or a leftover placeholder.
const PREFIXES = {
  ghp_: 'classic personal access token',
  github_pat_: 'fine-grained personal access token',
  gho_: 'OAuth app user token',
  ghu_: 'GitHub App user-to-server token',
  ghs_: 'GitHub App installation token',
  ghr_: 'GitHub App refresh token',
  eyJ: 'JSON Web Token, signed as a GitHub App',
};

const PLACEHOLDERS = ['your', 'xxx', '<', '>', 'changeme', 'replace', 'example',
  'placeholder', 'dummy', 'here', 'todo'];

/**
 * Describe the environment variable without disclosing it. Pure.
 * Unset and empty are different findings with different repairs, even though
 * both fail the same falsy check.
 */
export function inspectSecret(raw) {
  const problems = [];
  if (raw === null || raw === undefined) {
    return { fingerprint: 'absent', kind: null, problems: ['unset'] };
  }
  if (raw === '') return { fingerprint: 'empty string', kind: null, problems: ['empty'] };

  let value = raw.trim();
  if (!value) return { fingerprint: 'whitespace only', kind: null, problems: ['blank'] };
  if (value !== raw) problems.push('padded');

  if (value.length >= 2 && value[0] === value[value.length - 1] && '"\\''.includes(value[0])) {
    problems.push('quoted');
    value = value.slice(1, -1).trim();
  }

  let lowered = value.toLowerCase();
  for (const scheme of ['bearer ', 'token ']) {
    if (lowered.startsWith(scheme)) {
      problems.push('scheme-included');
      value = value.slice(scheme.length).trim();
      lowered = value.toLowerCase();
      break;
    }
  }

  if (/\\s/.test(value)) problems.push('contains-whitespace');

  let kind = null;
  for (const [prefix, name] of Object.entries(PREFIXES)) {
    if (value.startsWith(prefix)) { kind = name; break; }
  }

  if (kind === null) {
    problems.push('unknown-prefix');
    // Only after the prefix has already failed, so a real token containing
    // "xxx" by chance is not accused of being a placeholder.
    if (PLACEHOLDERS.some((m) => lowered.includes(m))) problems.push('placeholder');
  }

  const shown = Object.keys(PREFIXES).find((p) => value.startsWith(p)) ?? 'unrecognised';
  return { fingerprint: `${shown} (${value.length} chars)`, kind, problems };
}

/**
 * Name the tier a core limit belongs to. Pure.
 * Only the 60-against-anything-larger boundary is unambiguous; the rest is
 * colour, and 5,000 genuinely means two different things.
 */
export function tierFromLimit(limit) {
  const n = Number.parseInt(limit, 10);
  if (!Number.isFinite(n)) return ['unknown', 'no core limit was reported'];
  if (n <= 0) return ['unknown', `a core limit of ${n} is not a tier`];
  if (n <= ANON_LIMIT) {
    return ['anonymous',
      `a core limit of ${n} is the anonymous tier, which is counted per ` +
      'originating IP address and shared with everything else on it'];
  }
  if (n === 5000) {
    return ['authenticated',
      '5000 an hour: an authenticated user, an OAuth token, or a GitHub App ' +
      'installation that has not scaled beyond the floor'];
  }
  if (n === 15000) return ['enterprise', '15000 an hour: a user on GitHub Enterprise Cloud'];
  if (n > 5000) {
    return ['scaled',
      `${n} an hour, above the 5000 floor: a GitHub App installation whose ` +
      'limit has grown with installed repositories and users'];
  }
  return ['authenticated', `${n} an hour, which is above the anonymous 60`];
}

/**
 * Combine the local inspection and the two probes into one verdict. Pure.
 * "No token" and "a token GitHub refused" are not the same incident.
 */
export function diagnose(authedLimit, anonLimit, userStatus, secret) {
  const s = secret ?? { problems: ['unset'], fingerprint: 'absent' };
  const problems = s.problems ?? [];
  const [tier, note] = tierFromLimit(authedLimit);
  const [anonTier] = tierFromLimit(anonLimit);

  const missing = ['unset', 'empty', 'blank'].find((p) => problems.includes(p));
  if (missing) {
    const said = { unset: 'not set', empty: 'set to an empty string', blank: 'whitespace only' };
    return ['no-token',
      `GITHUB_TOKEN is ${said[missing]}, so every request goes out anonymous ` +
      'at 60 an hour per IP address. This is not a quota problem and spending ' +
      'less will not help it.'];
  }

  if (tier === 'anonymous') {
    let detail = note;
    if (anonTier === 'anonymous') {
      detail = 'the token was sent and GitHub still reports ' + note +
        '. The control request without any header reports the same, so the ' +
        'header is not arriving.';
    }
    let extra = '';
    if (problems.includes('scheme-included')) {
      extra = ' The variable itself starts with a scheme word, so the header ' +
        'was probably built as "Bearer Bearer ...".';
    } else if (problems.includes('quoted')) {
      extra = ' The variable still has its surrounding quotes, which become ' +
        'part of the header value.';
    } else if (problems.includes('padded') || problems.includes('contains-whitespace')) {
      extra = ' The variable carries whitespace, which is enough to make the ' +
        'header invalid.';
    }
    return ['anonymous', detail + extra];
  }

  if (userStatus === 401) {
    return ['token-rejected',
      `the variable holds ${s.kind ?? 'an unrecognised value'} but GET /user ` +
      'answered 401. The token is expired, revoked, or the header was removed ' +
      'between here and GitHub. That is not the same as a missing token.'];
  }

  if (userStatus === 403) {
    return ['blocked',
      `authenticated at ${note}, but GET /user answered 403. Look at org SSO ` +
      'authorisation and IP allow lists rather than at the tier.'];
  }

  if (userStatus === 200) {
    return ['authenticated',
      `${note}. The anonymous control reports ${anonLimit}, so the header is arriving.`];
  }

  return ['unclear',
    `core limit says ${note} but GET /user answered ${userStatus}, so the two ` +
    'probes do not agree. Treat the limit as the more reliable of the two.'];
}

async function get(url, token) {
  const headers = {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    const res = await fetch(url, { headers });
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    return [res.status, body, Object.fromEntries(res.headers.entries())];
  } catch (err) {
    console.error(`${url} failed: ${err.message}`);
    return [0, null, {}];
  }
}

const coreLimit = (body) => body?.resources?.core?.limit;

async function main() {
  const name = process.argv[2] ?? 'GITHUB_TOKEN';
  const raw = process.env[name];
  const secret = inspectSecret(raw);
  console.log(`${name}: ${secret.fingerprint}${secret.kind ? ', ' + secret.kind : ''}`);
  for (const problem of secret.problems) console.warn(`  variable problem: ${problem}`);

  let token = (raw ?? '').trim().replace(/^["']|["']$/g, '').trim();
  for (const scheme of ['Bearer ', 'bearer ', 'token ', 'Token ']) {
    if (token.startsWith(scheme)) { token = token.slice(scheme.length).trim(); break; }
  }

  const [authedStatus, authedBody, authedHeaders] = await get(`${API}/rate_limit`, token || null);
  const [anonStatus, anonBody] = await get(`${API}/rate_limit`);
  const [userStatus, userBody] = await get(`${API}/user`, token || null);

  const authed = authedStatus === 200 ? coreLimit(authedBody) : null;
  const anon = anonStatus === 200 ? coreLimit(anonBody) : null;
  console.log(`with the token:    core limit ${authed}`);
  console.log(`control, no token: core limit ${anon}`);
  console.log(`GET /user:         ${userStatus}${userStatus === 200 ? ' as ' + userBody?.login : ''}`);

  const lowered = {};
  for (const [k, v] of Object.entries(authedHeaders)) lowered[k.toLowerCase()] = v;
  if (lowered['x-oauth-scopes'] !== undefined) {
    console.log(`x-oauth-scopes is present (${lowered['x-oauth-scopes'] || 'empty'}), so ` +
      'this is a classic token or an OAuth token rather than a fine-grained one');
  }

  const [state, detail] = diagnose(authed, anon, userStatus, secret);
  console.log(`${state}: ${detail}`);

  if (state !== 'authenticated') {
    console.log('repair: export the token where the process can see it. In a ' +
      'container that means passing it in, not exporting it in the shell that ' +
      'ran the build.');
    console.log('repair: paste the value only. No surrounding quotes, no Bearer ' +
      'prefix, no trailing newline from the file it came out of.');
    console.log('repair: assert the tier at startup rather than asserting the ' +
      'variable is non-empty:');
    console.log("  const { resources } = await (await fetch(`${API}/rate_limit`, { headers })).json();");
    console.log(`  if (resources.core.limit <= ${ANON_LIMIT}) throw new Error('unauthenticated');`);
  }

  console.log(JSON.stringify({
    state, fingerprint: secret.fingerprint, problems: secret.problems,
    authenticated_limit: authed, anonymous_limit: anon,
    user_status: userStatus, tier: tierFromLimit(authed)[0],
  }, null, 2));
  process.exitCode = state === 'authenticated' ? 0 : 1;
}

// Only run when invoked directly, so importing this from the test file does not
// start main() and set an exit code the tests never asked for.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The environment variable is where this goes wrong, so that is where the tests are. Unset and empty are separate cases because they have separate repairs and the same falsy check swallows both. A value wrapped in quotes, a value carrying its own <code>Bearer</code>, a value that is still the placeholder from the example file: each of those is a real thing someone has shipped. And two cases exist to stop the check overreaching &mdash; a real token must not be accused of being a placeholder because it happens to contain three letters, and a token GitHub actively rejected must not be reported as a token that was never sent.",
"test_py_file": "test_github_auth_tier_check.py",
"test_py": '''from github_auth_tier_check import inspect_secret, tier_from_limit, diagnose

GOOD = {"fingerprint": "ghp_ (40 chars)", "kind": "classic personal access token",
        "problems": []}


def test_unset_and_empty_are_not_the_same_finding():
    assert inspect_secret(None)["problems"] == ["unset"]
    assert inspect_secret("")["problems"] == ["empty"]
    assert inspect_secret("   ")["problems"] == ["blank"]


def test_a_normal_token_reports_a_fingerprint_and_no_problems():
    got = inspect_secret("ghp_" + "A" * 36)
    assert got["problems"] == []
    assert got["kind"] == "classic personal access token"
    assert got["fingerprint"] == "ghp_ (40 chars)"


def test_the_fingerprint_never_contains_the_token():
    secret = "ghp_" + "S3CR3T" * 6
    got = inspect_secret(secret)
    assert "S3CR3T" not in got["fingerprint"]
    assert secret not in repr(got)


def test_a_fine_grained_token_is_recognised():
    assert inspect_secret("github_pat_" + "B" * 60)["kind"].startswith("fine-grained")


def test_an_app_installation_token_is_recognised():
    assert "installation" in inspect_secret("ghs_" + "C" * 36)["kind"]


def test_surrounding_quotes_survived_the_paste():
    got = inspect_secret('"ghp_' + "A" * 36 + '"')
    assert "quoted" in got["problems"]
    assert got["kind"] == "classic personal access token"


def test_the_scheme_word_ended_up_in_the_variable():
    got = inspect_secret("Bearer ghp_" + "A" * 36)
    assert "scheme-included" in got["problems"]
    assert got["kind"] == "classic personal access token"
    assert "scheme-included" in inspect_secret("token ghp_x")["problems"]


def test_a_trailing_newline_from_a_file_is_reported():
    assert "padded" in inspect_secret("ghp_" + "A" * 36 + "\\n")["problems"]


def test_the_placeholder_from_the_example_file_is_caught():
    got = inspect_secret("your_token_here")
    assert "unknown-prefix" in got["problems"]
    assert "placeholder" in got["problems"]


def test_a_real_token_is_never_accused_of_being_a_placeholder():
    # Placeholder wording is only looked for once the prefix has failed, so a
    # legitimate token containing "xxx" by chance stays clean.
    got = inspect_secret("ghp_xxx" + "A" * 33)
    assert got["problems"] == []


def test_sixty_is_the_only_boundary_that_matters():
    assert tier_from_limit(60)[0] == "anonymous"
    assert tier_from_limit(5000)[0] == "authenticated"
    assert tier_from_limit(15000)[0] == "enterprise"
    assert tier_from_limit(12500)[0] == "scaled"
    assert tier_from_limit(None)[0] == "unknown"


def test_five_thousand_is_reported_as_ambiguous_rather_than_as_a_user():
    _, note = tier_from_limit(5000)
    assert "App installation" in note


def test_a_missing_variable_is_named_as_such():
    state, detail = diagnose(60, 60, 401, inspect_secret(None))
    assert state == "no-token"
    assert "not set" in detail


def test_a_token_that_is_present_but_not_arriving_is_a_different_state():
    state, detail = diagnose(60, 60, 401, GOOD)
    assert state == "anonymous"
    assert "not arriving" in detail


def test_the_quoting_problem_is_named_in_the_anonymous_verdict():
    secret = inspect_secret('"ghp_' + "A" * 36 + '"')
    _, detail = diagnose(60, 60, 401, secret)
    assert "surrounding quotes" in detail


def test_a_rejected_token_is_not_reported_as_a_missing_one():
    state, detail = diagnose(5000, 60, 401, GOOD)
    assert state == "token-rejected"
    assert "expired" in detail


def test_a_403_points_at_sso_rather_than_at_the_tier():
    state, detail = diagnose(5000, 60, 403, GOOD)
    assert state == "blocked"
    assert "SSO" in detail


def test_the_healthy_case_cites_the_control():
    state, detail = diagnose(5000, 60, 200, GOOD)
    assert state == "authenticated"
    assert "control reports 60" in detail
''',
"test_js_file": "github-auth-tier-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectSecret, tierFromLimit, diagnose } from './github-auth-tier-check.mjs';

const GOOD = {
  fingerprint: 'ghp_ (40 chars)',
  kind: 'classic personal access token',
  problems: [],
};

test('unset and empty are not the same finding', () => {
  assert.deepEqual(inspectSecret(undefined).problems, ['unset']);
  assert.deepEqual(inspectSecret('').problems, ['empty']);
  assert.deepEqual(inspectSecret('   ').problems, ['blank']);
});

test('a normal token reports a fingerprint and no problems', () => {
  const got = inspectSecret('ghp_' + 'A'.repeat(36));
  assert.deepEqual(got.problems, []);
  assert.equal(got.kind, 'classic personal access token');
  assert.equal(got.fingerprint, 'ghp_ (40 chars)');
});

test('the fingerprint never contains the token', () => {
  const secret = 'ghp_' + 'S3CR3T'.repeat(6);
  const got = inspectSecret(secret);
  assert.ok(!got.fingerprint.includes('S3CR3T'));
  assert.ok(!JSON.stringify(got).includes(secret));
});

test('a fine-grained token is recognised', () => {
  assert.match(inspectSecret('github_pat_' + 'B'.repeat(60)).kind, /^fine-grained/);
});

test('an app installation token is recognised', () => {
  assert.match(inspectSecret('ghs_' + 'C'.repeat(36)).kind, /installation/);
});

test('surrounding quotes survived the paste', () => {
  const got = inspectSecret(`"ghp_${'A'.repeat(36)}"`);
  assert.ok(got.problems.includes('quoted'));
  assert.equal(got.kind, 'classic personal access token');
});

test('the scheme word ended up in the variable', () => {
  const got = inspectSecret('Bearer ghp_' + 'A'.repeat(36));
  assert.ok(got.problems.includes('scheme-included'));
  assert.equal(got.kind, 'classic personal access token');
  assert.ok(inspectSecret('token ghp_x').problems.includes('scheme-included'));
});

test('a trailing newline from a file is reported', () => {
  assert.ok(inspectSecret('ghp_' + 'A'.repeat(36) + '\\n').problems.includes('padded'));
});

test('the placeholder from the example file is caught', () => {
  const got = inspectSecret('your_token_here');
  assert.ok(got.problems.includes('unknown-prefix'));
  assert.ok(got.problems.includes('placeholder'));
});

test('a real token is never accused of being a placeholder', () => {
  assert.deepEqual(inspectSecret('ghp_xxx' + 'A'.repeat(33)).problems, []);
});

test('sixty is the only boundary that matters', () => {
  assert.equal(tierFromLimit(60)[0], 'anonymous');
  assert.equal(tierFromLimit(5000)[0], 'authenticated');
  assert.equal(tierFromLimit(15000)[0], 'enterprise');
  assert.equal(tierFromLimit(12500)[0], 'scaled');
  assert.equal(tierFromLimit(null)[0], 'unknown');
});

test('five thousand is reported as ambiguous rather than as a user', () => {
  assert.match(tierFromLimit(5000)[1], /App installation/);
});

test('a missing variable is named as such', () => {
  const [state, detail] = diagnose(60, 60, 401, inspectSecret(undefined));
  assert.equal(state, 'no-token');
  assert.match(detail, /not set/);
});

test('a token that is present but not arriving is a different state', () => {
  const [state, detail] = diagnose(60, 60, 401, GOOD);
  assert.equal(state, 'anonymous');
  assert.match(detail, /not arriving/);
});

test('the quoting problem is named in the anonymous verdict', () => {
  const secret = inspectSecret(`"ghp_${'A'.repeat(36)}"`);
  const [, detail] = diagnose(60, 60, 401, secret);
  assert.match(detail, /surrounding quotes/);
});

test('a rejected token is not reported as a missing one', () => {
  const [state, detail] = diagnose(5000, 60, 401, GOOD);
  assert.equal(state, 'token-rejected');
  assert.match(detail, /expired/);
});

test('a 403 points at SSO rather than at the tier', () => {
  const [state, detail] = diagnose(5000, 60, 403, GOOD);
  assert.equal(state, 'blocked');
  assert.match(detail, /SSO/);
});

test('the healthy case cites the control', () => {
  const [state, detail] = diagnose(5000, 60, 200, GOOD);
  assert.equal(state, 'authenticated');
  assert.match(detail, /control reports 60/);
});
''',
"faq": [
 ("How is this different from running out of my 5,000 an hour?",
  "It is a different bucket and a different repair. Running out means the token arrived and spent its quota; the message names a user ID, x-ratelimit-limit reads 5000, and the fix is to make fewer requests. Being anonymous means no token arrived at all; the message names an IP address, x-ratelimit-limit reads 60, and making fewer requests only postpones it. Read the limit value and you never confuse the two again."),
 ("Why does it fail immediately on CI but take an hour on my laptop?",
  "Because the anonymous bucket is counted per originating IP address. Your laptop usually has that address to itself. A CI runner shares an egress address with every other job on the fleet, so the sixty is spread across all of them and your share may be nothing at all. The same code, the same absent token, and a failure that arrives in seconds instead of an hour."),
 ("The variable is definitely set. Why is the limit still 60?",
  "Set where, and visible to what. Exported in the shell that launched a container is not exported inside it. A CI secret is often not exposed to workflows triggered from a fork, and resolves to an empty string rather than failing. Beyond that, the value can be present and the header still wrong: quotes that came along with the paste, a Bearer prefix stored in the variable as well as added by the client, a newline from the file it was read out of. The control request settles which of the two it is."),
 ("Is it safe for the script to make a request with no token?",
  "Yes, and it is the point of the check. It is a GET to /rate_limit, which serves anonymous callers and does not count against any bucket. Without that control you have one number and a theory; with it you have two numbers that either agree or disagree, and the disagreement is the proof that your header is arriving."),
 ("What should the code do when the token is missing?",
  "Stop. The failure mode this note describes exists entirely because the sensible-looking alternative is to carry on without credentials, and every client library that does so turns a loud configuration error into a quiet one that surfaces sixty requests later in an unrelated place. Assert at startup that the reported core limit is above 60 and exit if it is not."),
],
"related": [
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/saml-partial-results/", "Org lists silently omit SSO organizations"),
],
"citations": [CITE_AUTHENTICATING, CITE_REST_LIMITS, CITE_PAT, CITE_RATE_ENDPOINT],
},


{
"slug": "secondary-limit-points-per-minute",
"title": "A hot endpoint burns 900 points a minute and gets throttled",
"description": "Points and CPU time are two separate caps on one path. Measure an endpoint's response time and you can compute the request rate it will actually sustain.",
"h1": "a hot endpoint burns 900 points a minute and gets throttled",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github 900 points per minute", "github secondary rate limit points",
             "github api cpu time limit", "github api throttled one endpoint",
             "x-ratelimit-resource"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One endpoint in the job keeps failing and the rest are fine. It fails for about a minute, recovers, and fails again twenty minutes later. The hourly quota is barely touched and the concurrency is one, because someone already serialised it after the last incident. What is left is the cap nobody budgets for: not how many requests you make, but how much work you asked one path to do inside sixty seconds.",
"short_answer": """<p>There are two per-minute ceilings on a single endpoint and either can bind first. The point cap allows <strong>900 points a minute</strong>, where a read costs 1 point and a write costs 5. The CPU cap allows <strong>90 seconds of CPU time per 60 seconds of real time</strong>, and GitHub documents total response time as a rough estimate of it.</p>
<p>That second cap is why a modest request rate gets throttled. At 60&nbsp;ms a request the point cap binds and you can run 900 a minute. At 500&nbsp;ms a request the CPU cap binds at 180 a minute, and the point counter never comes close. So the number to compute is not "how many requests" but "how many <em>of this endpoint</em>", and it falls straight out of the response time you can measure in a few seconds.</p>""",
"problem": """<p>It is selective, which sends the investigation the wrong way. Every other call in the same process, on the same token, in the same second, keeps working. That looks like the endpoint is broken or the resource is special, so people go looking at permissions on that one path, or at the size of the repository behind it, and the answer is neither.</p>
<p>It also recovers on its own, quickly, which makes it hard to catch and easy to dismiss. A minute of 403s inside a fifteen-minute job shows up as a handful of retried items and a run that took slightly longer. Nobody opens an incident for that. It becomes a background failure rate that everyone has stopped seeing, until the day the job grows and the minute becomes ten.</p>
<p>And every number people habitually check looks healthy. The hourly bucket is fine. The concurrency is one. There is no header for the limit that fired, because secondary limits do not publish one. The only artefacts are a 403 or 429 whose body says "secondary rate limit", a <code>retry-after</code>, and the fact that the failures cluster on a single path.</p>""",
"why": """<p><strong>Points are charged per request, by method.</strong> A <code>GET</code>, <code>HEAD</code> or <code>OPTIONS</code> costs one point. Anything that changes something costs five. The REST allowance is 900 points a minute, so 900 reads or 180 writes, and the two are drawn from the same number.</p>
<p><strong>CPU time is charged per request, by how hard it was.</strong> No more than 90 seconds of CPU per 60 seconds of wall clock. Endpoints are not equal here: a search, a large diff, a commit comparison across a long range, or a repository listing for an org with thousands of repositories costs the server far more than reading one issue. GitHub's own guidance is to estimate this from total response time, which is generous to you as a measurement because response time also includes the network.</p>
<p><strong>Whichever cap is lower is the one that decides.</strong> Divide 900 by the points per request and you get the point ceiling. Divide 90 by the mean response time in seconds and you get the CPU ceiling. The smaller of the two is your real rate for that path. Below about a hundred milliseconds a request the points bind; above it, CPU does, and from there on the ceiling drops as the endpoint gets slower.</p>
<p><strong>The cap is per endpoint, which cuts both ways.</strong> It means one expensive path can be throttled while everything else runs, and it means moving work off that path fixes it. It also means <code>x-ratelimit-resource</code> on the failing response is worth reading: it names the bucket the request was billed to, which identifies the endpoint family rather than leaving you to guess from a URL.</p>
<p><strong>Retrying immediately makes it last longer.</strong> The retries are themselves requests to the same expensive path, so they keep the minute full. This is the mechanism by which a sixty-second throttle becomes a ten-minute one, and it is the reason the repair is to spread the calls rather than to catch the error.</p>""",
"steps": [
 {"h": "Find which path the failures cluster on",
  "body": """<p>Secondary limits are per endpoint, so the distribution of failures is the diagnosis. If the 403s are spread evenly across every call you make, this is not your problem. If nine in ten of them are on one path, it is. Read <code>x-ratelimit-resource</code> on a failing response to see which bucket GitHub billed it to.</p>"""},
 {"h": "Measure what one call to that path actually costs",
  "body": """<p>A handful of sequential requests, spaced out, is enough. Take the mean response time. It is not the server's CPU time &mdash; it includes network and queueing &mdash; but GitHub's own documentation offers total response time as the estimate, and over-estimating cost here means under-estimating your safe rate, which is the direction you want to be wrong in.</p>"""},
 {"h": "Compute both ceilings and take the smaller",
  "body": """<p>900 divided by the points per request, and 90 divided by the mean seconds. A 40&nbsp;ms read gives 900 and 2,250, so points bind at 900 a minute. A 600&nbsp;ms read gives 900 and 150, so CPU binds at 150. That second number is the one that surprises people, because 150 requests a minute is a rate a plain loop reaches without trying.</p>"""},
 {"h": "Compare it against the rate you are actually configured for",
  "body": """<p>A job with 4,000 items to fetch and no pacing will run at whatever the endpoint allows, which is exactly the rate that trips this. Divide the work by the safe rate and you get the honest duration: 4,000 items at 150 a minute is 27 minutes, and the alternative to 27 minutes is not 9 minutes, it is 9 minutes of failures followed by a retry storm.</p>"""},
 {"h": "Make the work cheaper before you make it slower",
  "body": """<p>Pacing is the fallback, not the fix. One GraphQL query that returns fields for fifty repositories replaces fifty expensive REST calls and is billed to a different allowance. A list endpoint with <code>per_page=100</code> replaces a hundred item reads. A conditional request that returns <code>304</code> costs the server almost nothing. Each of those lowers the numerator instead of raising the clock.</p>"""},
],
"verify": """<p>Re-measure the path and check the configured rate sits under the computed ceiling.</p>
<pre><code class="language-bash">python3 github_endpoint_cost_audit.py --path /repos/octocat/hello-world/commits --rate 90
# clear: 0.21 s a call, CPU binds at 428/min, configured 90/min</code></pre>""",
"code_intro": "Four pure functions and one small sampler. <code>points_for</code> encodes the documented method costs, <code>cost_profile</code> collapses samples into a mean per path, <code>safe_rate</code> computes both ceilings and reports which one binds, and <code>verdict</code> compares that against the rate you say you run at. The sampler defaults to <code>GET /rate_limit</code>, which is free, and warns before it measures anything that is not &mdash; the irony of a script that trips the limit it is measuring is available to anyone who forgets to pace the sampling.",
"py_file": "github_endpoint_cost_audit.py",
"py": '''"""Compute the request rate one endpoint can sustain before it is throttled.

Read only. Every request is a GET, and the default sampled path is
/rate_limit, which does not count against the primary rate limit.

Two ceilings apply per minute to a single endpoint: 900 points, where a read
costs one point and a write costs five, and 90 seconds of CPU time per 60
seconds of real time. GitHub documents total response time as a rough estimate
of the second one, so a few timed GETs are enough to compute both and see which
binds first. That is the number a caller needs, and it is usually far lower
than 900.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_endpoint_cost_audit")

API = "https://api.github.com"
UA = "github-endpoint-cost-audit/1.0"

# Documented secondary limits for a single REST endpoint.
POINT_CAP = 900          # points per minute
CPU_CAP = 90.0           # seconds of CPU per 60 seconds of real time

# Reads cost one point; everything that changes state costs five.
CHEAP_METHODS = ("GET", "HEAD", "OPTIONS")


def points_for(method):
    """Documented point cost of one request. Pure.

    Anything unrecognised is charged the expensive rate. Guessing low here
    would produce a safe-looking ceiling for a request that is not safe, and
    the whole output of this script is a number people will pace against.
    """
    try:
        name = str(method).strip().upper()
    except (TypeError, ValueError):
        return 5
    return 1 if name in CHEAP_METHODS else 5


def cost_profile(samples):
    """Collapse timed samples into one entry per path. Pure.

    samples: [{"path", "method", "seconds"}, ...]

    Keeps the max as well as the mean because a path whose mean is comfortable
    and whose worst case is four times that will be throttled during the worst
    case and nowhere else, which is exactly the intermittent shape people
    struggle to reproduce.
    """
    grouped = {}
    for s in samples or []:
        try:
            path = str(s["path"])
            seconds = float(s["seconds"])
        except (KeyError, TypeError, ValueError):
            continue
        if seconds < 0:
            continue
        entry = grouped.setdefault(path, {"path": path, "calls": 0, "total": 0.0,
                                          "max_seconds": 0.0,
                                          "points": points_for(s.get("method", "GET"))})
        entry["calls"] += 1
        entry["total"] += seconds
        entry["max_seconds"] = max(entry["max_seconds"], seconds)

    out = {}
    for path, entry in grouped.items():
        entry["mean_seconds"] = round(entry["total"] / entry["calls"], 4)
        entry["max_seconds"] = round(entry["max_seconds"], 4)
        del entry["total"]
        out[path] = entry
    return out


def safe_rate(mean_seconds, points=1, point_cap=POINT_CAP, cpu_cap=CPU_CAP):
    """Requests per minute this endpoint sustains, and which cap binds. Pure.

    The point ceiling is a constant per method. The CPU ceiling falls as the
    endpoint gets slower, and it crosses under the point ceiling at around a
    tenth of a second a call, which is why an endpoint that feels fast can
    still be throttled at a rate nowhere near 900.
    """
    try:
        seconds = float(mean_seconds)
    except (TypeError, ValueError):
        seconds = 0.0
    points = max(1, int(points))

    by_points = point_cap / points
    by_cpu = (cpu_cap / seconds) if seconds > 0 else float("inf")

    if by_cpu < by_points:
        binding, per_minute = "cpu", by_cpu
    else:
        binding, per_minute = "points", by_points

    return {"by_points": round(by_points, 1),
            "by_cpu": None if by_cpu == float("inf") else round(by_cpu, 1),
            "binding": binding, "per_minute": round(per_minute, 1),
            "mean_seconds": round(seconds, 4), "points": points}


def verdict(path, entry, safe, configured=None):
    """Compare the computed ceiling against the rate you run at. Pure."""
    mean = safe["mean_seconds"]
    ceiling = safe["per_minute"]
    cap_name = ("the 90s-of-CPU-per-60s cap" if safe["binding"] == "cpu"
                else "the 900-points-a-minute cap")

    if configured is None:
        return ("ceiling",
                "%s costs %.3f s a call, so %s allows about %d request(s) a "
                "minute on this path." % (path, mean, cap_name, ceiling))

    try:
        configured = float(configured)
    except (TypeError, ValueError):
        return ("ceiling", "%s allows about %d a minute; no configured rate "
                           "was given to compare it against." % (path, ceiling))

    if configured > ceiling:
        return ("over-budget",
                "%s is configured for %d a minute against a ceiling of %d. %s "
                "binds first at %.3f s a call, so the surplus is refused, "
                "retried, and refused again."
                % (path, configured, ceiling, cap_name, mean))

    if configured >= ceiling * 0.8:
        return ("near-budget",
                "%s runs at %d a minute against a ceiling of %d. One slower "
                "response, or one worst case of %.3f s, closes that gap."
                % (path, configured, ceiling, entry.get("max_seconds", mean)))

    if mean >= 1.0:
        return ("expensive",
                "%s costs %.3f s a call, which caps it at %d a minute however "
                "little you are asking for today. Treat it as a path to move "
                "work off rather than a path to pace." % (path, mean, ceiling))

    return ("clear",
            "%s runs at %d a minute against a ceiling of %d, %s binding."
            % (path, configured, ceiling, cap_name))


def sample_path(session, path, count, pause):
    """Time a few sequential GETs. Sequential and paced on purpose: a sampler
    that fans out would measure the limit it is trying to describe."""
    url = API + path if path.startswith("/") else path
    samples, resource, throttled = [], None, False
    for i in range(count):
        if i:
            time.sleep(pause)
        start = time.monotonic()
        try:
            r = session.get(url, timeout=60)
        except requests.RequestException as exc:
            log.warning("%s sample %d failed: %s", path, i, exc)
            continue
        elapsed = time.monotonic() - start
        headers = {k.lower(): v for k, v in r.headers.items()}
        resource = resource or headers.get("x-ratelimit-resource")
        if r.status_code in (403, 429) and "secondary rate limit" in r.text.lower():
            throttled = True
            log.warning("%s was throttled while being measured; retry-after %s",
                        path, headers.get("retry-after", "absent"))
            continue
        if r.status_code >= 400:
            log.warning("%s sample %d returned %d", path, i, r.status_code)
            continue
        samples.append({"path": path, "method": "GET", "seconds": elapsed})
    return samples, resource, throttled


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", action="append", default=None,
                    help="path to measure; repeatable (default /rate_limit)")
    ap.add_argument("--samples", type=int, default=4,
                    help="timed requests per path")
    ap.add_argument("--pause", type=float, default=1.0,
                    help="seconds between samples")
    ap.add_argument("--rate", type=float, default=None,
                    help="requests per minute your job runs at on these paths")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    paths = args.path or ["/rate_limit"]
    billed = [p for p in paths if p.rstrip("/") != "/rate_limit"]
    if billed:
        log.warning("measuring %d path(s) that do cost quota: %d sample(s) "
                    "each, one point per sample", len(billed),
                    args.samples)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    all_samples, resources, worst = [], {}, "clear"
    findings = []
    for path in paths:
        samples, resource, throttled = sample_path(session, path, max(1, args.samples),
                                                   max(0.0, args.pause))
        all_samples.extend(samples)
        if resource:
            resources[path] = resource
        if throttled:
            log.warning("%s tripped a secondary limit during measurement, which "
                        "is itself the finding: the endpoint is already over "
                        "budget at the rate this sampler used", path)

    profile = cost_profile(all_samples)
    if not profile:
        log.error("no successful samples, so there is nothing to cost")
        return 2

    ranked = sorted(profile.values(), key=lambda e: e["mean_seconds"], reverse=True)
    for entry in ranked:
        safe = safe_rate(entry["mean_seconds"], entry["points"])
        state, detail = verdict(entry["path"], entry, safe, args.rate)
        findings.append({"path": entry["path"], "state": state,
                         "mean_seconds": entry["mean_seconds"],
                         "max_seconds": entry["max_seconds"],
                         "billed_to": resources.get(entry["path"]), **safe})
        log.info("%-14s %s", state, detail)
        if resources.get(entry["path"]):
            log.info("               billed to the %s bucket",
                     resources[entry["path"]])
        if state in ("over-budget", "near-budget", "expensive"):
            worst = state if worst == "clear" else worst

    if worst != "clear":
        log.info("repair: replace per-item calls on the expensive path with one "
                 "GraphQL query returning the same fields, which is billed to a "
                 "different allowance entirely.")
        log.info("repair: raise per_page to 100 on list endpoints so the same "
                 "data arrives in a third of the calls.")
        log.info("repair: send If-None-Match with the stored etag. A 304 costs "
                 "the server almost nothing and costs you nothing at all.")
        log.info("repair: where the calls are unavoidable, spread them across "
                 "the minute rather than bursting, and on a throttled response "
                 "sleep the whole retry-after before resuming that path.")

    print(json.dumps({"findings": findings, "configured_per_minute": args.rate},
                     indent=2))
    return 1 if worst == "over-budget" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-endpoint-cost-audit.mjs",
"js": '''/**
 * Compute the request rate one endpoint can sustain before it is throttled.
 *
 * Read only. Every request is a GET, and the default sampled path is
 * /rate_limit, which does not count against the primary rate limit.
 *
 * Two per-minute ceilings apply to a single endpoint: 900 points, and 90
 * seconds of CPU per 60 seconds of real time. Response time is the documented
 * rough estimate of the second, so timed GETs are enough to see which binds.
 */
const API = 'https://api.github.com';
const UA = 'github-endpoint-cost-audit/1.0';

// Documented secondary limits for a single REST endpoint.
export const POINT_CAP = 900;
export const CPU_CAP = 90;

// Reads cost one point; everything that changes state costs five.
const CHEAP_METHODS = ['GET', 'HEAD', 'OPTIONS'];

/**
 * Documented point cost of one request. Pure.
 * Unrecognised methods are charged the expensive rate, because guessing low
 * produces a safe-looking ceiling for a request that is not safe.
 */
export function pointsFor(method) {
  const name = String(method ?? '').trim().toUpperCase();
  return CHEAP_METHODS.includes(name) ? 1 : 5;
}

/**
 * Collapse timed samples into one entry per path. Pure.
 * Keeps the max as well as the mean: a path with a comfortable mean and a bad
 * worst case is throttled during the worst case and nowhere else.
 */
export function costProfile(samples) {
  const grouped = new Map();
  for (const s of samples ?? []) {
    const path = s?.path === undefined ? null : String(s.path);
    const seconds = Number(s?.seconds);
    if (path === null || !Number.isFinite(seconds) || seconds < 0) continue;
    if (!grouped.has(path)) {
      grouped.set(path, {
        path, calls: 0, total: 0, max_seconds: 0, points: pointsFor(s.method ?? 'GET'),
      });
    }
    const entry = grouped.get(path);
    entry.calls += 1;
    entry.total += seconds;
    entry.max_seconds = Math.max(entry.max_seconds, seconds);
  }

  const out = {};
  for (const [path, entry] of grouped) {
    entry.mean_seconds = Math.round((entry.total / entry.calls) * 10000) / 10000;
    entry.max_seconds = Math.round(entry.max_seconds * 10000) / 10000;
    delete entry.total;
    out[path] = entry;
  }
  return out;
}

/**
 * Requests per minute this endpoint sustains, and which cap binds. Pure.
 * The CPU ceiling falls as the endpoint gets slower and crosses under the
 * point ceiling at around a tenth of a second a call.
 */
export function safeRate(meanSeconds, points = 1, pointCap = POINT_CAP, cpuCap = CPU_CAP) {
  const secs = Number.isFinite(Number(meanSeconds)) ? Number(meanSeconds) : 0;
  const p = Math.max(1, Number.parseInt(points, 10) || 1);

  const byPoints = pointCap / p;
  const byCpu = secs > 0 ? cpuCap / secs : Infinity;

  const binding = byCpu < byPoints ? 'cpu' : 'points';
  const perMinute = Math.min(byCpu, byPoints);

  return {
    by_points: Math.round(byPoints * 10) / 10,
    by_cpu: Number.isFinite(byCpu) ? Math.round(byCpu * 10) / 10 : null,
    binding,
    per_minute: Math.round(perMinute * 10) / 10,
    mean_seconds: Math.round(secs * 10000) / 10000,
    points: p,
  };
}

/** Compare the computed ceiling against the rate you run at. Pure. */
export function verdict(path, entry, safe, configured = null) {
  const mean = safe.mean_seconds;
  const ceiling = safe.per_minute;
  const capName = safe.binding === 'cpu'
    ? 'the 90s-of-CPU-per-60s cap'
    : 'the 900-points-a-minute cap';

  if (configured === null || configured === undefined) {
    return ['ceiling',
      `${path} costs ${mean.toFixed(3)} s a call, so ${capName} allows about ` +
      `${Math.trunc(ceiling)} request(s) a minute on this path.`];
  }

  const rate = Number(configured);
  if (!Number.isFinite(rate)) {
    return ['ceiling',
      `${path} allows about ${Math.trunc(ceiling)} a minute; no configured ` +
      'rate was given to compare it against.'];
  }

  if (rate > ceiling) {
    return ['over-budget',
      `${path} is configured for ${Math.trunc(rate)} a minute against a ` +
      `ceiling of ${Math.trunc(ceiling)}. ${capName} binds first at ` +
      `${mean.toFixed(3)} s a call, so the surplus is refused, retried, and ` +
      'refused again.'];
  }

  if (rate >= ceiling * 0.8) {
    return ['near-budget',
      `${path} runs at ${Math.trunc(rate)} a minute against a ceiling of ` +
      `${Math.trunc(ceiling)}. One slower response, or one worst case of ` +
      `${(entry?.max_seconds ?? mean).toFixed(3)} s, closes that gap.`];
  }

  if (mean >= 1) {
    return ['expensive',
      `${path} costs ${mean.toFixed(3)} s a call, which caps it at ` +
      `${Math.trunc(ceiling)} a minute however little you are asking for ` +
      'today. Treat it as a path to move work off rather than a path to pace.'];
  }

  return ['clear',
    `${path} runs at ${Math.trunc(rate)} a minute against a ceiling of ` +
    `${Math.trunc(ceiling)}, ${capName} binding.`];
}

const sleep = (ms) => new Promise((r) => { setTimeout(r, ms); });

/** Time a few sequential GETs. Sequential on purpose: a sampler that fanned
 * out would measure the limit it is trying to describe. */
async function samplePath(token, path, count, pause) {
  const url = path.startsWith('/') ? API + path : path;
  const samples = [];
  let resource = null;
  let throttled = false;
  for (let i = 0; i < count; i += 1) {
    if (i) await sleep(pause * 1000);
    const start = performance.now();
    let res;
    try {
      res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': UA,
        },
      });
    } catch (err) {
      console.warn(`${path} sample ${i} failed: ${err.message}`);
      continue;
    }
    const text = await res.text();
    const elapsed = (performance.now() - start) / 1000;
    const lowered = {};
    for (const [k, v] of res.headers.entries()) lowered[k.toLowerCase()] = v;
    resource = resource ?? lowered['x-ratelimit-resource'] ?? null;
    if ((res.status === 403 || res.status === 429)
        && text.toLowerCase().includes('secondary rate limit')) {
      throttled = true;
      console.warn(`${path} was throttled while being measured; retry-after ` +
        `${lowered['retry-after'] ?? 'absent'}`);
      continue;
    }
    if (res.status >= 400) {
      console.warn(`${path} sample ${i} returned ${res.status}`);
      continue;
    }
    samples.push({ path, method: 'GET', seconds: elapsed });
  }
  return { samples, resource, throttled };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const path = process.argv[2] ?? '/rate_limit';
  const count = Math.max(1, Number.parseInt(process.argv[3] ?? '4', 10) || 4);
  const rate = process.argv[4] === undefined ? null : Number(process.argv[4]);

  if (path.replace(/\\/$/, '') !== '/rate_limit') {
    console.warn(`measuring a path that does cost quota: ${count} sample(s), ` +
      'one point each');
  }

  const { samples, resource, throttled } = await samplePath(token, path, count, 1);
  if (throttled) {
    console.warn(`${path} tripped a secondary limit during measurement, which ` +
      'is itself the finding: the endpoint is already over budget at the rate ' +
      'this sampler used');
  }

  const profile = costProfile(samples);
  const entries = Object.values(profile).sort((a, b) => b.mean_seconds - a.mean_seconds);
  if (!entries.length) {
    console.error('no successful samples, so there is nothing to cost');
    process.exitCode = 2;
    return;
  }

  const findings = [];
  let worst = 'clear';
  for (const entry of entries) {
    const safe = safeRate(entry.mean_seconds, entry.points);
    const [state, detail] = verdict(entry.path, entry, safe, rate);
    findings.push({ path: entry.path, state, max_seconds: entry.max_seconds,
      billed_to: resource, ...safe });
    console.log(`${state.padEnd(14)} ${detail}`);
    if (resource) console.log(`               billed to the ${resource} bucket`);
    if (['over-budget', 'near-budget', 'expensive'].includes(state) && worst === 'clear') {
      worst = state;
    }
  }

  if (worst !== 'clear') {
    console.log('repair: replace per-item calls on the expensive path with one ' +
      'GraphQL query, which is billed to a different allowance entirely.');
    console.log('repair: raise per_page to 100 on list endpoints so the same ' +
      'data arrives in a third of the calls.');
    console.log('repair: send If-None-Match with the stored etag. A 304 costs ' +
      'the server almost nothing and costs you nothing at all.');
    console.log('repair: where the calls are unavoidable, spread them across ' +
      'the minute rather than bursting, and sleep the whole retry-after before ' +
      'resuming that path.');
  }

  console.log(JSON.stringify({ findings, configured_per_minute: rate }, null, 2));
  process.exitCode = worst === 'over-budget' ? 1 : 0;
}

// Only run when invoked directly, so importing this from the test file does not
// start main() and set an exit code the tests never asked for.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The crossover is the whole point of this note, so it is the case the tests spend most of their time on: the response time at which the CPU ceiling drops below the point ceiling, and what the answer looks like either side of it. Around a tenth of a second the two swap, and a script that only ever knew about 900 points a minute reports a rate three times too high for a slow endpoint. The rest pins the defensive choices &mdash; an unknown method is charged as a write, a zero response time does not divide by zero, and a sample with a missing field is dropped rather than counted as instant.",
"test_py_file": "test_github_endpoint_cost_audit.py",
"test_py": '''from github_endpoint_cost_audit import points_for, cost_profile, safe_rate, verdict


def test_reads_cost_one_point_and_writes_cost_five():
    assert points_for("GET") == 1
    assert points_for("head") == 1
    assert points_for("OPTIONS") == 1
    assert points_for("patch") == 5
    assert points_for("delete") == 5


def test_an_unknown_method_is_charged_the_expensive_rate():
    # Guessing low would produce a safe-looking ceiling for a request that is
    # not safe, and the ceiling is the number people pace against.
    assert points_for("QUERY") == 5
    assert points_for(None) == 5
    assert points_for("") == 5


def test_samples_are_grouped_by_path_and_averaged():
    profile = cost_profile([
        {"path": "/a", "method": "GET", "seconds": 0.1},
        {"path": "/a", "method": "GET", "seconds": 0.3},
        {"path": "/b", "method": "GET", "seconds": 1.0},
    ])
    assert profile["/a"]["calls"] == 2
    assert profile["/a"]["mean_seconds"] == 0.2
    assert profile["/a"]["max_seconds"] == 0.3
    assert profile["/b"]["mean_seconds"] == 1.0


def test_a_malformed_sample_is_dropped_rather_than_counted_as_instant():
    profile = cost_profile([
        {"path": "/a", "seconds": 0.5},
        {"path": "/a", "seconds": "slow"},
        {"seconds": 0.5},
        {"path": "/a", "seconds": -1},
    ])
    assert profile["/a"]["calls"] == 1
    assert profile["/a"]["mean_seconds"] == 0.5


def test_no_samples_profile_nothing():
    assert cost_profile([]) == {}
    assert cost_profile(None) == {}


def test_a_fast_endpoint_is_bound_by_points():
    safe = safe_rate(0.04)
    assert safe["binding"] == "points"
    assert safe["per_minute"] == 900.0
    assert safe["by_cpu"] == 2250.0


def test_a_slow_endpoint_is_bound_by_cpu_time_instead():
    safe = safe_rate(0.6)
    assert safe["binding"] == "cpu"
    assert safe["per_minute"] == 150.0


def test_the_two_ceilings_cross_at_a_tenth_of_a_second():
    assert safe_rate(0.09)["binding"] == "points"
    assert safe_rate(0.11)["binding"] == "cpu"


def test_a_very_expensive_endpoint_collapses_to_a_handful_a_minute():
    assert safe_rate(3.0)["per_minute"] == 30.0


def test_a_write_costs_five_points_so_its_ceiling_is_a_fifth():
    assert safe_rate(0.01, points=5)["per_minute"] == 180.0


def test_a_zero_response_time_does_not_divide_by_zero():
    safe = safe_rate(0.0)
    assert safe["by_cpu"] is None
    assert safe["binding"] == "points"
    assert safe_rate("unmeasured")["per_minute"] == 900.0


def test_with_no_configured_rate_the_ceiling_is_simply_reported():
    safe = safe_rate(0.5)
    state, detail = verdict("/x", {}, safe)
    assert state == "ceiling"
    assert "180" in detail


def test_a_rate_above_the_ceiling_names_the_cap_that_binds():
    safe = safe_rate(0.6)
    state, detail = verdict("/x", {"max_seconds": 0.9}, safe, configured=400)
    assert state == "over-budget"
    assert "CPU" in detail


def test_a_rate_just_under_the_ceiling_is_not_reported_as_fine():
    safe = safe_rate(0.6)  # 150 a minute
    state, detail = verdict("/x", {"max_seconds": 0.9}, safe, configured=130)
    assert state == "near-budget"
    assert "0.900 s" in detail


def test_an_expensive_path_is_flagged_even_at_a_low_rate():
    safe = safe_rate(2.0)  # 45 a minute
    state, detail = verdict("/x", {"max_seconds": 2.4}, safe, configured=5)
    assert state == "expensive"
    assert "move work off" in detail


def test_a_cheap_path_at_a_modest_rate_is_clear():
    state, detail = verdict("/x", {"max_seconds": 0.05}, safe_rate(0.04), configured=60)
    assert state == "clear"
    assert "900-points" in detail
''',
"test_js_file": "github-endpoint-cost-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  pointsFor, costProfile, safeRate, verdict,
} from './github-endpoint-cost-audit.mjs';

test('reads cost one point and writes cost five', () => {
  assert.equal(pointsFor('GET'), 1);
  assert.equal(pointsFor('head'), 1);
  assert.equal(pointsFor('OPTIONS'), 1);
  assert.equal(pointsFor('patch'), 5);
  assert.equal(pointsFor('delete'), 5);
});

test('an unknown method is charged the expensive rate', () => {
  assert.equal(pointsFor('QUERY'), 5);
  assert.equal(pointsFor(null), 5);
  assert.equal(pointsFor(''), 5);
});

test('samples are grouped by path and averaged', () => {
  const profile = costProfile([
    { path: '/a', method: 'GET', seconds: 0.1 },
    { path: '/a', method: 'GET', seconds: 0.3 },
    { path: '/b', method: 'GET', seconds: 1.0 },
  ]);
  assert.equal(profile['/a'].calls, 2);
  assert.equal(profile['/a'].mean_seconds, 0.2);
  assert.equal(profile['/a'].max_seconds, 0.3);
  assert.equal(profile['/b'].mean_seconds, 1);
});

test('a malformed sample is dropped rather than counted as instant', () => {
  const profile = costProfile([
    { path: '/a', seconds: 0.5 },
    { path: '/a', seconds: 'slow' },
    { seconds: 0.5 },
    { path: '/a', seconds: -1 },
  ]);
  assert.equal(profile['/a'].calls, 1);
  assert.equal(profile['/a'].mean_seconds, 0.5);
});

test('no samples profile nothing', () => {
  assert.deepEqual(costProfile([]), {});
  assert.deepEqual(costProfile(null), {});
});

test('a fast endpoint is bound by points', () => {
  const safe = safeRate(0.04);
  assert.equal(safe.binding, 'points');
  assert.equal(safe.per_minute, 900);
  assert.equal(safe.by_cpu, 2250);
});

test('a slow endpoint is bound by CPU time instead', () => {
  const safe = safeRate(0.6);
  assert.equal(safe.binding, 'cpu');
  assert.equal(safe.per_minute, 150);
});

test('the two ceilings cross at a tenth of a second', () => {
  assert.equal(safeRate(0.09).binding, 'points');
  assert.equal(safeRate(0.11).binding, 'cpu');
});

test('a very expensive endpoint collapses to a handful a minute', () => {
  assert.equal(safeRate(3).per_minute, 30);
});

test('a write costs five points so its ceiling is a fifth', () => {
  assert.equal(safeRate(0.01, 5).per_minute, 180);
});

test('a zero response time does not divide by zero', () => {
  const safe = safeRate(0);
  assert.equal(safe.by_cpu, null);
  assert.equal(safe.binding, 'points');
  assert.equal(safeRate('unmeasured').per_minute, 900);
});

test('with no configured rate the ceiling is simply reported', () => {
  const [state, detail] = verdict('/x', {}, safeRate(0.5));
  assert.equal(state, 'ceiling');
  assert.match(detail, /180/);
});

test('a rate above the ceiling names the cap that binds', () => {
  const [state, detail] = verdict('/x', { max_seconds: 0.9 }, safeRate(0.6), 400);
  assert.equal(state, 'over-budget');
  assert.match(detail, /CPU/);
});

test('a rate just under the ceiling is not reported as fine', () => {
  const [state, detail] = verdict('/x', { max_seconds: 0.9 }, safeRate(0.6), 130);
  assert.equal(state, 'near-budget');
  assert.match(detail, /0\\.900 s/);
});

test('an expensive path is flagged even at a low rate', () => {
  const [state, detail] = verdict('/x', { max_seconds: 2.4 }, safeRate(2), 5);
  assert.equal(state, 'expensive');
  assert.match(detail, /move work off/);
});

test('a cheap path at a modest rate is clear', () => {
  const [state, detail] = verdict('/x', { max_seconds: 0.05 }, safeRate(0.04), 60);
  assert.equal(state, 'clear');
  assert.match(detail, /900-points/);
});
''',
"faq": [
 ("How do I know it is the points cap and not the CPU cap?",
  "Compute both and take the smaller. 900 divided by the points per request gives the point ceiling, which is 900 for reads and 180 for writes. 90 divided by the mean response time in seconds gives the CPU ceiling. They cross at about a tenth of a second: faster than that and points bind, slower and CPU does. GitHub does not tell you which one fired, so knowing which is lower for your path is the closest you get to an answer."),
 ("Is response time really a fair proxy for CPU time?",
  "It is an over-estimate, and GitHub's own documentation offers total response time as the way to approximate the CPU cap. Your measurement includes network latency and queueing that the server never spent, so the ceiling it produces is lower than the real one. That is the useful direction to be wrong in: you end up pacing slightly more conservatively than you strictly need to."),
 ("Why is only one endpoint failing when the token is shared?",
  "Because this cap is per endpoint, unlike the hourly quota, which is per token. One expensive path can be throttled continuously while every other call on the same credentials succeeds. It is also the reason the repair is local: moving that one path to GraphQL, or to a list endpoint, or behind a cache, fixes it without touching anything else."),
 ("Does the retry itself count?",
  "Yes, and this is how a one-minute problem becomes a ten-minute one. A retry is another request to the same expensive path inside the same minute, so it keeps the budget full and the window keeps re-arming. Sleep the full retry-after and pause that path rather than that item, because every other in-flight request to the same endpoint is about to be refused too."),
 ("What if I cannot make the endpoint any cheaper?",
  "Then the ceiling is the schedule. If a path allows 150 requests a minute and you have 4,000 items, the job takes 27 minutes and no amount of parallelism changes that; parallelism only converts the wait into failures. Accepting the duration up front is usually cheaper than a job that appears to finish in nine minutes and quietly drops whatever was refused."),
],
"related": [
 ("/github/secondary-limit-concurrency/", "Over 100 concurrent requests trips a limit"),
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
 ("/github/per-page-default-30/", "per_page is unset so every list costs more"),
],
"citations": [CITE_REST_LIMITS, CITE_BEST, CITE_GRAPHQL_LIMITS, CITE_TROUBLESHOOT],
},


{
"slug": "search-bucket-exhausted",
"title": "Search has its own 30-per-minute bucket and drains separately",
"description": "resources.search is not resources.core, and its window is 60 seconds rather than an hour. A search-per-repository loop empties it in the first minute.",
"h1": "search has its own 30-per-minute bucket and drains separately",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github search api rate limit", "github 30 requests per minute search",
             "search api rate limit exceeded", "resources.search rate_limit",
             "github search query 256 characters"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The job loops over four hundred repositories and runs one search in each. Around the thirtieth it starts returning 403, and the part that makes no sense is that everything else keeps working: the repository reads in the same loop, on the same token, in the same second, are fine. Two buckets, and only one of them is empty. The error message does not mention which.",
"short_answer": """<p><code>GET /rate_limit</code> returns every bucket at once, and <code>resources.search</code> is not <code>resources.core</code>. Search allows <strong>30 requests a minute</strong> authenticated, 10 unauthenticated, and code search is tighter again at 10 a minute. The window is sixty seconds rather than an hour, so it empties and refills far faster than anything else on the token.</p>
<p>Compare them in the same units and the surprise goes away. Core is 5,000 an hour, which is about 83 a minute. Search is 30 a minute. The bucket with the smaller number is not the smaller allowance by accident &mdash; per minute, search is nearly three times tighter than core, and a loop that calls it once per item was never going to fit.</p>""",
"problem": """<p>The partial failure is what costs the time. If everything broke, you would suspect the token. Because only the searches break, the investigation goes to the search query, then to the repository the query names, then to permissions on that repository, and only much later to the idea that search is billed somewhere else entirely.</p>
<p>The recovery is fast enough to be misleading too. A sixty-second window means the bucket refills while you are still reading the stack trace, so a retry by hand works and the bug is filed as flaky. It reproduces reliably only at the original rate, which nobody runs by hand.</p>
<p>Underneath it is usually the same shape: a search that was written for one repository and later put in a loop. One search per repository is a perfectly reasonable thing to write and it scales exactly as badly as it can, because the cost is per call and the allowance resets on a clock rather than accumulating.</p>""",
"why": """<p><strong>Buckets are independent and the document lists all of them.</strong> <code>GET /rate_limit</code> returns <code>core</code>, <code>search</code>, <code>code_search</code>, <code>graphql</code> and several more. Spending one does not touch another, which is why ordinary REST calls carry on while search refuses, and it is also why the check is easy: the answer is in one free request.</p>
<p><strong>The windows are different lengths, so the raw numbers do not compare.</strong> 5,000 against 30 looks like an enormous gap and is not one, because the first is per hour and the second is per minute. Normalise both to requests per minute &mdash; 83 against 30 &mdash; and search is the tighter constraint on almost every job that uses it at all.</p>
<p><strong>On any real call, <code>x-ratelimit-resource</code> names the bucket that was billed.</strong> That header is the direct evidence. A response carrying <code>x-ratelimit-resource: search</code> was charged to the 30-a-minute allowance no matter what the rest of your integration is doing.</p>
<p><strong>One broad search costs the same as one narrow one.</strong> The allowance counts requests, not results. A query naming forty repositories costs a single call, the same as a query naming one, so batching is close to free and is the entire repair.</p>
<p><strong>What limits the batching is the query, not the API.</strong> A search query may be at most 256 characters and may use no more than five <code>AND</code>, <code>OR</code> or <code>NOT</code> operators. Multiple <code>repo:</code> qualifiers are combined for you and do not spend operators, so the practical constraint is the character budget, which is a packing problem with an exact answer.</p>""",
"steps": [
 {"h": "Read every bucket in one free request",
  "body": """<p><code>GET /rate_limit</code> does not consume any bucket, including the one it reports. Look at <code>resources.search</code> next to <code>resources.core</code>. If search is at zero and core has thousands left, the diagnosis is finished and the rest of this note is about the repair.</p>"""},
 {"h": "Put the two buckets in the same units",
  "body": """<p>Divide each limit by its window in minutes. Core over an hour is about 83 a minute; search over its sixty-second window is 30; code search is 10. Doing this once permanently fixes the intuition that search is a rounding error next to core, which is the belief that lets a per-item search loop get written in the first place.</p>"""},
 {"h": "Cost the loop you actually have",
  "body": """<p>Number of items divided by 30 is the number of minutes the loop needs at best, and every call past the first 30 in any minute is refused rather than queued. Four hundred repositories is fourteen minutes of pure waiting, assuming nothing else on the token searches at the same time.</p>"""},
 {"h": "Pack the loop into a handful of queries",
  "body": """<p>A search query accepts many <code>repo:</code> qualifiers, which are combined as alternatives, so one query can cover as many repositories as fit inside 256 characters. Pack greedily, filter the combined results client side, and four hundred calls become roughly twenty. Keep an eye on the five-operator limit if your base query already uses explicit <code>AND</code>, <code>OR</code> or <code>NOT</code>.</p>"""},
 {"h": "Prove which bucket moved",
  "body": """<p>Read <code>/rate_limit</code>, run one search, read it again. <code>search.used</code> goes up by one and <code>core.used</code> does not move. That is a two-request demonstration that costs one search call, and it settles the argument about whether search spends your hourly quota better than any amount of documentation reading.</p>"""},
],
"verify": """<p>Run the plan again with the packed queries and confirm the call count fits inside a single window.</p>
<pre><code class="language-bash">python3 github_search_budget.py --repos-file repos.txt --base "is:issue is:open label:bug"
# clear: 412 repositories pack into 19 queries, inside one 30-a-minute window</code></pre>""",
"code_intro": "Four pure functions, and the interesting one is the packer. <code>bucket_pressure</code> normalises every bucket in the rate-limit document to requests per minute so windows of different lengths can be compared at all; <code>plan_loop</code> costs a per-item loop against that rate; <code>pack_repo_queries</code> is a greedy bin pack against the 256-character query limit that also counts the boolean operators in your base query; and <code>verdict</code> puts them together. The network layer is one free <code>/rate_limit</code> call, optionally three if you ask it to prove the point with a single live search.",
"py_file": "github_search_budget.py",
"py": '''"""Budget a search workload against the search bucket, not the core one.

Read only. GET /rate_limit is free and reports every bucket; the optional probe
issues one real search, which is a GET and costs one search call.

Search is billed to resources.search, which allows 30 requests a minute
authenticated over a 60 second window. Core allows 5,000 an hour, which is
about 83 a minute. Comparing 5,000 against 30 is what makes people think search
is the generous one; comparing 83 against 30 is what makes them stop.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_search_budget")

API = "https://api.github.com"
UA = "github-search-budget/1.0"

# A search query is capped at 256 characters and five boolean operators.
MAX_QUERY = 256
MAX_OPERATORS = 5

# The rate-limit document reports limit, used and reset for every bucket but
# never the length of the window, and the windows are not all the same. Without
# this table a per-minute comparison is impossible, which is the comparison the
# whole note turns on.
WINDOWS = {
    "core": 3600, "graphql": 3600, "integration_manifest": 3600,
    "code_scanning_upload": 3600, "actions_runner_registration": 3600,
    "scim": 3600, "dependency_sbom": 3600, "audit_log": 3600,
    "search": 60, "code_search": 60, "source_import": 60,
    "dependency_snapshots": 60,
}


def bucket_pressure(resources, now):
    """Normalise every bucket to requests per minute. Pure.

    A bucket whose window this table does not know is still reported, with
    per_minute left as None rather than guessed. An invented window would
    produce a confident number that is wrong, and the point of the function is
    to make two numbers comparable.
    """
    out = {}
    for name, b in sorted((resources or {}).items()):
        try:
            limit = int(b.get("limit"))
            used = int(b.get("used", 0))
            reset = float(b.get("reset", 0))
        except (AttributeError, TypeError, ValueError):
            continue
        window = WINDOWS.get(name)
        remaining = b.get("remaining")
        if not isinstance(remaining, int):
            remaining = max(0, limit - used)
        out[name] = {
            "limit": limit, "used": used, "remaining": remaining,
            "window": window,
            "per_minute": round(limit / (window / 60.0), 1) if window else None,
            "refills_in": max(0, round(reset - float(now))),
        }
    return out


def plan_loop(items, per_minute):
    """Cost a one-call-per-item loop against a per-minute allowance. Pure.

    Calls past the allowance in a given minute are refused, not queued, which
    is the difference between a slow job and a failing one.
    """
    try:
        items = max(0, int(items))
    except (TypeError, ValueError):
        items = 0
    try:
        rate = float(per_minute)
    except (TypeError, ValueError):
        rate = 0.0

    if rate <= 0:
        return {"calls": items, "minutes": None, "refused_in_first_minute": None}
    return {"calls": items,
            "minutes": round(items / rate, 1),
            "refused_in_first_minute": max(0, items - int(rate))}


def pack_repo_queries(repos, base="", max_len=MAX_QUERY, max_operators=MAX_OPERATORS):
    """Pack repo: qualifiers into as few queries as the length limit allows. Pure.

    Multiple repo: qualifiers are combined as alternatives and do not spend
    boolean operators, so the binding constraint is the 256 character budget.
    Greedy is optimal enough here: the qualifiers are all about the same length,
    so there is nothing for a cleverer pack to recover.

    Returns {"queries", "too_long", "operators"}. too_long holds any single
    repository that cannot fit even on its own, which is a real if rare case
    for a long org and repository name under a long base query.
    """
    base = (base or "").strip()
    operators = sum(1 for token in base.split() if token in ("AND", "OR", "NOT"))

    queries, too_long = [], []
    current = ""
    for repo in repos or []:
        name = str(repo).strip()
        if not name:
            continue
        qualifier = "repo:" + name
        if len(base) + 1 + len(qualifier) > max_len:
            too_long.append(name)
            continue
        candidate = (current + " " + qualifier).strip() if current else qualifier
        if len(base) + (1 if base else 0) + len(candidate) <= max_len:
            current = candidate
        else:
            queries.append((base + " " + current).strip() if base else current)
            current = qualifier
    if current:
        queries.append((base + " " + current).strip() if base else current)

    return {"queries": queries, "too_long": too_long, "operators": operators,
            "over_operator_limit": operators > max_operators}


def verdict(search, core, plan=None, packed=None):
    """Turn the buckets and the plan into one finding. Pure."""
    if not search:
        return ("no-search-bucket",
                "the rate-limit document did not include a search bucket, so "
                "there is nothing to budget against")

    core_rate = (core or {}).get("per_minute")
    comparison = ("" if core_rate is None else
                  " Core allows %.0f a minute over its hour, so search is the "
                  "tighter of the two despite the larger-looking number."
                  % core_rate)

    if search["remaining"] <= 0:
        return ("exhausted",
                "search is empty and refills in %d second(s). Core still has "
                "%s of %s, which is why every non-search call kept working: "
                "they are different buckets."
                % (search["refills_in"], (core or {}).get("remaining", "?"),
                   (core or {}).get("limit", "?")))

    if plan and plan.get("refused_in_first_minute"):
        packing = ""
        if packed and packed.get("queries"):
            packing = (" Packed into repo: qualifiers the same work is %d "
                       "quer%s." % (len(packed["queries"]),
                                    "y" if len(packed["queries"]) == 1 else "ies"))
        return ("over-budget",
                "%d searches at %s a minute needs %s minute(s), and %d of them "
                "are refused inside the first minute rather than queued.%s%s"
                % (plan["calls"], search["per_minute"], plan["minutes"],
                   plan["refused_in_first_minute"], packing, comparison))

    if search["used"] >= search["limit"] * 0.8:
        return ("tight",
                "%d of %d spent in the current 60 second window, refilling in "
                "%d second(s).%s"
                % (search["used"], search["limit"], search["refills_in"],
                   comparison))

    if plan and plan.get("calls"):
        return ("clear",
                "%d search(es) at %s a minute fits in %s minute(s) with nothing "
                "refused.%s" % (plan["calls"], search["per_minute"],
                                plan["minutes"], comparison))

    return ("clear",
            "%d of %d left in this window.%s"
            % (search["remaining"], search["limit"], comparison))


def rate_limit(session):
    r = session.get(API + "/rate_limit", timeout=30)
    if r.status_code != 200:
        log.error("GET /rate_limit returned %d: %s", r.status_code, r.text[:200])
        return None
    return r.json().get("resources", {})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", default="",
                    help="comma separated owner/name list the loop searches")
    ap.add_argument("--repos-file", default=None,
                    help="file with one owner/name per line (read only)")
    ap.add_argument("--base", default="is:issue is:open",
                    help="the query your loop runs in each repository")
    ap.add_argument("--probe", default=None, metavar="QUERY",
                    help="run one real search to show which bucket it bills to")
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
        "User-Agent": UA,
    })

    before = rate_limit(session)
    if before is None:
        return 2

    pressure = bucket_pressure(before, time.time())
    for name, b in pressure.items():
        log.info("%-28s %5d / %-6d %s",
                 name, b["used"], b["limit"],
                 "%.0f a minute" % b["per_minute"] if b["per_minute"]
                 else "window not in this table")

    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    if args.repos_file:
        with open(args.repos_file, encoding="utf-8") as fh:
            repos.extend(line.strip() for line in fh if line.strip())

    search = pressure.get("search")
    plan = plan_loop(len(repos), (search or {}).get("per_minute")) if repos else None
    packed = pack_repo_queries(repos, args.base) if repos else None

    if args.probe:
        r = session.get(API + "/search/issues", params={"q": args.probe, "per_page": 1},
                        timeout=30)
        billed = {k.lower(): v for k, v in r.headers.items()}.get("x-ratelimit-resource")
        after = bucket_pressure(rate_limit(session) or {}, time.time())
        log.info("probe returned %d, billed to the %s bucket", r.status_code, billed)
        log.info("search.used %d -> %d, core.used %d -> %d",
                 pressure["search"]["used"], after["search"]["used"],
                 pressure["core"]["used"], after["core"]["used"])

    state, detail = verdict(search, pressure.get("core"), plan, packed)
    log.info("%s: %s", state, detail)

    if packed and packed["queries"] and state != "clear":
        log.info("repair: run these %d quer%s instead of one per repository, "
                 "and filter the combined results client side:",
                 len(packed["queries"]),
                 "y" if len(packed["queries"]) == 1 else "ies")
        for q in packed["queries"][:10]:
            log.info("  %s", q)
        if len(packed["queries"]) > 10:
            log.info("  ... and %d more", len(packed["queries"]) - 10)
    if packed and packed["too_long"]:
        log.warning("%d repositor(y/ies) cannot fit in a %d character query "
                    "beside this base query and still need their own call: %s",
                    len(packed["too_long"]), MAX_QUERY,
                    ", ".join(packed["too_long"][:5]))
    if packed and packed["over_operator_limit"]:
        log.warning("the base query already uses %d boolean operators and the "
                    "limit is %d", packed["operators"], MAX_OPERATORS)
    if state != "clear":
        log.info("repair: where a list endpoint can answer the same question, "
                 "use it instead. Issues, pull requests and commits all have "
                 "list endpoints billed to core rather than to search.")
        log.info("repair: cache search results by query string. The allowance "
                 "counts requests, so a repeated query is pure waste.")

    print(json.dumps({"state": state, "search": search,
                      "core": pressure.get("core"), "plan": plan,
                      "queries": (packed or {}).get("queries", [])}, indent=2))
    return 1 if state in ("exhausted", "over-budget") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-search-budget.mjs",
"js": '''/**
 * Budget a search workload against the search bucket, not the core one.
 *
 * Read only. GET /rate_limit is free and reports every bucket; the optional
 * probe issues one real search, which is a GET and costs one search call.
 *
 * Search allows 30 requests a minute over a 60 second window. Core allows
 * 5,000 an hour, which is about 83 a minute. The second comparison is the one
 * that stops people writing a search per item.
 */
const API = 'https://api.github.com';
const UA = 'github-search-budget/1.0';

// A search query is capped at 256 characters and five boolean operators.
export const MAX_QUERY = 256;
export const MAX_OPERATORS = 5;

// The rate-limit document never reports the length of a bucket's window, and
// the windows are not all the same, so a per-minute comparison needs this.
const WINDOWS = {
  core: 3600, graphql: 3600, integration_manifest: 3600,
  code_scanning_upload: 3600, actions_runner_registration: 3600,
  scim: 3600, dependency_sbom: 3600, audit_log: 3600,
  search: 60, code_search: 60, source_import: 60, dependency_snapshots: 60,
};

/**
 * Normalise every bucket to requests per minute. Pure.
 * An unknown window leaves per_minute null rather than guessed: an invented
 * window produces a confident wrong number.
 */
export function bucketPressure(resources, now) {
  const out = {};
  for (const name of Object.keys(resources ?? {}).sort()) {
    const b = resources[name];
    const limit = Number.parseInt(b?.limit, 10);
    const used = Number.parseInt(b?.used ?? 0, 10);
    const reset = Number(b?.reset ?? 0);
    if (!Number.isFinite(limit) || !Number.isFinite(used) || !Number.isFinite(reset)) continue;
    const window = WINDOWS[name] ?? null;
    const remaining = Number.isInteger(b?.remaining) ? b.remaining : Math.max(0, limit - used);
    out[name] = {
      limit, used, remaining, window,
      per_minute: window ? Math.round((limit / (window / 60)) * 10) / 10 : null,
      refills_in: Math.max(0, Math.round(reset - Number(now))),
    };
  }
  return out;
}

/**
 * Cost a one-call-per-item loop against a per-minute allowance. Pure.
 * Calls past the allowance are refused, not queued.
 */
export function planLoop(items, perMinute) {
  const n = Math.max(0, Number.parseInt(items, 10) || 0);
  const rate = Number(perMinute);
  if (!Number.isFinite(rate) || rate <= 0) {
    return { calls: n, minutes: null, refused_in_first_minute: null };
  }
  return {
    calls: n,
    minutes: Math.round((n / rate) * 10) / 10,
    refused_in_first_minute: Math.max(0, n - Math.trunc(rate)),
  };
}

/**
 * Pack repo: qualifiers into as few queries as the length limit allows. Pure.
 * repo: qualifiers are combined as alternatives and do not spend boolean
 * operators, so the binding constraint is the 256 character budget. Greedy is
 * good enough: the qualifiers are all about the same length.
 */
export function packRepoQueries(repos, base = '', maxLen = MAX_QUERY, maxOperators = MAX_OPERATORS) {
  const stem = (base ?? '').trim();
  const operators = stem.split(/\\s+/).filter((t) => ['AND', 'OR', 'NOT'].includes(t)).length;

  const queries = [];
  const tooLong = [];
  let current = '';
  for (const repo of repos ?? []) {
    const name = String(repo).trim();
    if (!name) continue;
    const qualifier = `repo:${name}`;
    if (stem.length + 1 + qualifier.length > maxLen) { tooLong.push(name); continue; }
    const candidate = current ? `${current} ${qualifier}` : qualifier;
    if (stem.length + (stem ? 1 : 0) + candidate.length <= maxLen) {
      current = candidate;
    } else {
      queries.push(stem ? `${stem} ${current}` : current);
      current = qualifier;
    }
  }
  if (current) queries.push(stem ? `${stem} ${current}` : current);

  return { queries, too_long: tooLong, operators, over_operator_limit: operators > maxOperators };
}

/** Turn the buckets and the plan into one finding. Pure. */
export function verdict(search, core, plan = null, packed = null) {
  if (!search) {
    return ['no-search-bucket',
      'the rate-limit document did not include a search bucket, so there is ' +
      'nothing to budget against'];
  }

  const coreRate = core?.per_minute ?? null;
  const comparison = coreRate === null ? ''
    : ` Core allows ${Math.round(coreRate)} a minute over its hour, so search ` +
      'is the tighter of the two despite the larger-looking number.';

  if (search.remaining <= 0) {
    return ['exhausted',
      `search is empty and refills in ${search.refills_in} second(s). Core ` +
      `still has ${core?.remaining ?? '?'} of ${core?.limit ?? '?'}, which is ` +
      'why every non-search call kept working: they are different buckets.'];
  }

  if (plan?.refused_in_first_minute) {
    let packing = '';
    if (packed?.queries?.length) {
      packing = ` Packed into repo: qualifiers the same work is ` +
        `${packed.queries.length} quer${packed.queries.length === 1 ? 'y' : 'ies'}.`;
    }
    return ['over-budget',
      `${plan.calls} searches at ${search.per_minute} a minute needs ` +
      `${plan.minutes} minute(s), and ${plan.refused_in_first_minute} of them ` +
      `are refused inside the first minute rather than queued.${packing}${comparison}`];
  }

  if (search.used >= search.limit * 0.8) {
    return ['tight',
      `${search.used} of ${search.limit} spent in the current 60 second ` +
      `window, refilling in ${search.refills_in} second(s).${comparison}`];
  }

  if (plan?.calls) {
    return ['clear',
      `${plan.calls} search(es) at ${search.per_minute} a minute fits in ` +
      `${plan.minutes} minute(s) with nothing refused.${comparison}`];
  }

  return ['clear',
    `${search.remaining} of ${search.limit} left in this window.${comparison}`];
}

async function rateLimit(headers) {
  const res = await fetch(`${API}/rate_limit`, { headers });
  if (res.status !== 200) {
    console.error(`GET /rate_limit returned ${res.status}: ${(await res.text()).slice(0, 200)}`);
    return null;
  }
  return (await res.json()).resources ?? {};
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const repos = (process.argv[2] ?? '').split(',').map((r) => r.trim()).filter(Boolean);
  const base = process.argv[3] ?? 'is:issue is:open';

  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };

  const before = await rateLimit(headers);
  if (!before) { process.exitCode = 2; return; }

  const pressure = bucketPressure(before, Date.now() / 1000);
  for (const [name, b] of Object.entries(pressure)) {
    const rate = b.per_minute ? `${Math.round(b.per_minute)} a minute` : 'window not in this table';
    console.log(`${name.padEnd(28)} ${b.used} / ${b.limit} ${rate}`);
  }

  const search = pressure.search;
  const plan = repos.length ? planLoop(repos.length, search?.per_minute) : null;
  const packed = repos.length ? packRepoQueries(repos, base) : null;

  const [state, detail] = verdict(search, pressure.core, plan, packed);
  console.log(`${state}: ${detail}`);

  if (packed?.queries?.length && state !== 'clear') {
    console.log(`repair: run these ${packed.queries.length} quer` +
      `${packed.queries.length === 1 ? 'y' : 'ies'} instead of one per ` +
      'repository, and filter the combined results client side:');
    for (const q of packed.queries.slice(0, 10)) console.log(`  ${q}`);
    if (packed.queries.length > 10) console.log(`  ... and ${packed.queries.length - 10} more`);
  }
  if (packed?.too_long?.length) {
    console.warn(`${packed.too_long.length} repository name(s) cannot fit in a ` +
      `${MAX_QUERY} character query beside this base query: ` +
      packed.too_long.slice(0, 5).join(', '));
  }
  if (packed?.over_operator_limit) {
    console.warn(`the base query already uses ${packed.operators} boolean ` +
      `operators and the limit is ${MAX_OPERATORS}`);
  }
  if (state !== 'clear') {
    console.log('repair: where a list endpoint can answer the same question, ' +
      'use it instead. Issues, pull requests and commits all have list ' +
      'endpoints billed to core rather than to search.');
    console.log('repair: cache search results by query string. The allowance ' +
      'counts requests, so a repeated query is pure waste.');
  }

  console.log(JSON.stringify({
    state, search, core: pressure.core, plan, queries: packed?.queries ?? [],
  }, null, 2));
  process.exitCode = (state === 'exhausted' || state === 'over-budget') ? 1 : 0;
}

// Only run when invoked directly, so importing this from the test file does not
// start main() and set an exit code the tests never asked for.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things here are worth pinning hard. The first is the unit conversion, because the entire note rests on it: 5,000 an hour and 30 a minute are 83 and 30 in the same units, and a test asserts that ordering explicitly so nobody later 'simplifies' the windows table away. The second is the packer, which has the ordinary bin-packing edges plus one specific to search &mdash; a repository whose name is long enough that it cannot share a query with anything, and the base query that has already spent the five boolean operators before a single <code>repo:</code> is added.",
"test_py_file": "test_github_search_budget.py",
"test_py": '''from github_search_budget import (bucket_pressure, plan_loop,
                                  pack_repo_queries, verdict)

NOW = 1_800_000_000.0

RESOURCES = {
    "core": {"limit": 5000, "used": 120, "remaining": 4880, "reset": NOW + 2400},
    "search": {"limit": 30, "used": 4, "remaining": 26, "reset": NOW + 41},
    "code_search": {"limit": 10, "used": 0, "remaining": 10, "reset": NOW + 55},
    "graphql": {"limit": 5000, "used": 0, "remaining": 5000, "reset": NOW + 2400},
}


def test_the_two_buckets_only_compare_once_the_windows_match():
    p = bucket_pressure(RESOURCES, NOW)
    assert p["core"]["per_minute"] == round(5000 / 60.0, 1)
    assert p["search"]["per_minute"] == 30.0
    # The whole point of the note: search is the tighter allowance even though
    # its limit is 166 times smaller.
    assert p["search"]["per_minute"] < p["core"]["per_minute"]


def test_code_search_is_tighter_still():
    p = bucket_pressure(RESOURCES, NOW)
    assert p["code_search"]["per_minute"] == 10.0


def test_a_bucket_with_an_unknown_window_is_reported_not_guessed():
    p = bucket_pressure({"something_new": {"limit": 99, "used": 1, "reset": NOW}}, NOW)
    assert p["something_new"]["per_minute"] is None
    assert p["something_new"]["limit"] == 99


def test_a_malformed_bucket_is_skipped():
    assert bucket_pressure({"core": {"limit": "lots"}}, NOW) == {}
    assert bucket_pressure(None, NOW) == {}


def test_refills_in_never_goes_negative():
    p = bucket_pressure({"search": {"limit": 30, "used": 30, "reset": NOW - 90}}, NOW)
    assert p["search"]["refills_in"] == 0


def test_a_loop_longer_than_the_window_refuses_the_surplus():
    plan = plan_loop(400, 30)
    assert plan["minutes"] == 13.3
    assert plan["refused_in_first_minute"] == 370


def test_a_loop_inside_the_window_refuses_nothing():
    assert plan_loop(12, 30)["refused_in_first_minute"] == 0


def test_a_missing_rate_is_not_treated_as_infinite():
    plan = plan_loop(400, None)
    assert plan["minutes"] is None
    assert plan["refused_in_first_minute"] is None


def test_a_short_list_becomes_one_query():
    packed = pack_repo_queries(["octo/one", "octo/two"], "is:issue is:open")
    assert len(packed["queries"]) == 1
    assert packed["queries"][0].startswith("is:issue is:open repo:octo/one")
    assert len(packed["queries"][0]) <= 256


def test_a_long_list_splits_and_every_query_fits():
    repos = ["acme/service-%02d" % i for i in range(40)]
    packed = pack_repo_queries(repos, "is:issue is:open label:bug")
    assert len(packed["queries"]) > 1
    assert all(len(q) <= 256 for q in packed["queries"])
    # Every repository appears exactly once across the packed queries.
    joined = " ".join(packed["queries"])
    assert all(joined.count("repo:" + r) == 1 for r in repos)
    # The saving is the point: 40 calls collapse to a handful.
    assert len(packed["queries"]) < 8


def test_a_repository_that_cannot_fit_beside_the_base_query_is_named():
    packed = pack_repo_queries(["acme/" + "x" * 250, "acme/ok"], "is:issue")
    assert packed["too_long"] == ["acme/" + "x" * 250]
    assert packed["queries"] == ["is:issue repo:acme/ok"]


def test_empty_input_packs_into_nothing():
    assert pack_repo_queries([], "is:issue")["queries"] == []
    assert pack_repo_queries(None)["queries"] == []
    assert pack_repo_queries(["", "  "])["queries"] == []


def test_boolean_operators_in_the_base_query_are_counted():
    packed = pack_repo_queries(["a/b"], "cat OR dog OR bird OR fish OR rat OR ox")
    assert packed["operators"] == 5
    assert packed["over_operator_limit"] is False
    more = pack_repo_queries(["a/b"], "a OR b OR c OR d OR e OR f OR g")
    assert more["over_operator_limit"] is True


def test_an_empty_search_bucket_points_at_the_healthy_core_one():
    p = bucket_pressure(dict(RESOURCES, search={"limit": 30, "used": 30,
                                                "remaining": 0, "reset": NOW + 12}), NOW)
    state, detail = verdict(p["search"], p["core"])
    assert state == "exhausted"
    assert "different buckets" in detail
    assert "12 second(s)" in detail


def test_an_oversized_loop_reports_the_packed_alternative():
    p = bucket_pressure(RESOURCES, NOW)
    repos = ["acme/service-%02d" % i for i in range(400)]
    state, detail = verdict(p["search"], p["core"],
                            plan_loop(400, p["search"]["per_minute"]),
                            pack_repo_queries(repos, "is:issue is:open"))
    assert state == "over-budget"
    assert "refused inside the first minute" in detail
    assert "queries" in detail


def test_the_core_comparison_is_stated_in_the_same_units():
    p = bucket_pressure(RESOURCES, NOW)
    _, detail = verdict(p["search"], p["core"])
    assert "83 a minute" in detail


def test_a_healthy_bucket_with_no_plan_is_clear():
    p = bucket_pressure(RESOURCES, NOW)
    assert verdict(p["search"], p["core"])[0] == "clear"


def test_no_search_bucket_is_not_reported_as_healthy():
    assert verdict(None, None)[0] == "no-search-bucket"
''',
"test_js_file": "github-search-budget.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  bucketPressure, planLoop, packRepoQueries, verdict,
} from './github-search-budget.mjs';

const NOW = 1800000000;

const RESOURCES = {
  core: { limit: 5000, used: 120, remaining: 4880, reset: NOW + 2400 },
  search: { limit: 30, used: 4, remaining: 26, reset: NOW + 41 },
  code_search: { limit: 10, used: 0, remaining: 10, reset: NOW + 55 },
  graphql: { limit: 5000, used: 0, remaining: 5000, reset: NOW + 2400 },
};

test('the two buckets only compare once the windows match', () => {
  const p = bucketPressure(RESOURCES, NOW);
  assert.equal(p.core.per_minute, Math.round((5000 / 60) * 10) / 10);
  assert.equal(p.search.per_minute, 30);
  assert.ok(p.search.per_minute < p.core.per_minute);
});

test('code search is tighter still', () => {
  assert.equal(bucketPressure(RESOURCES, NOW).code_search.per_minute, 10);
});

test('a bucket with an unknown window is reported, not guessed', () => {
  const p = bucketPressure({ something_new: { limit: 99, used: 1, reset: NOW } }, NOW);
  assert.equal(p.something_new.per_minute, null);
  assert.equal(p.something_new.limit, 99);
});

test('a malformed bucket is skipped', () => {
  assert.deepEqual(bucketPressure({ core: { limit: 'lots' } }, NOW), {});
  assert.deepEqual(bucketPressure(null, NOW), {});
});

test('refills_in never goes negative', () => {
  const p = bucketPressure({ search: { limit: 30, used: 30, reset: NOW - 90 } }, NOW);
  assert.equal(p.search.refills_in, 0);
});

test('a loop longer than the window refuses the surplus', () => {
  const plan = planLoop(400, 30);
  assert.equal(plan.minutes, 13.3);
  assert.equal(plan.refused_in_first_minute, 370);
});

test('a loop inside the window refuses nothing', () => {
  assert.equal(planLoop(12, 30).refused_in_first_minute, 0);
});

test('a missing rate is not treated as infinite', () => {
  const plan = planLoop(400, null);
  assert.equal(plan.minutes, null);
  assert.equal(plan.refused_in_first_minute, null);
});

test('a short list becomes one query', () => {
  const packed = packRepoQueries(['octo/one', 'octo/two'], 'is:issue is:open');
  assert.equal(packed.queries.length, 1);
  assert.ok(packed.queries[0].startsWith('is:issue is:open repo:octo/one'));
  assert.ok(packed.queries[0].length <= 256);
});

test('a long list splits and every query fits', () => {
  const repos = Array.from({ length: 40 }, (_, i) => `acme/service-${String(i).padStart(2, '0')}`);
  const packed = packRepoQueries(repos, 'is:issue is:open label:bug');
  assert.ok(packed.queries.length > 1);
  assert.ok(packed.queries.every((q) => q.length <= 256));
  const joined = packed.queries.join(' ');
  for (const r of repos) {
    assert.equal(joined.split(`repo:${r}`).length - 1, 1);
  }
  assert.ok(packed.queries.length < 8);
});

test('a repository that cannot fit beside the base query is named', () => {
  const huge = 'acme/' + 'x'.repeat(250);
  const packed = packRepoQueries([huge, 'acme/ok'], 'is:issue');
  assert.deepEqual(packed.too_long, [huge]);
  assert.deepEqual(packed.queries, ['is:issue repo:acme/ok']);
});

test('empty input packs into nothing', () => {
  assert.deepEqual(packRepoQueries([], 'is:issue').queries, []);
  assert.deepEqual(packRepoQueries(null).queries, []);
  assert.deepEqual(packRepoQueries(['', '  ']).queries, []);
});

test('boolean operators in the base query are counted', () => {
  const packed = packRepoQueries(['a/b'], 'cat OR dog OR bird OR fish OR rat OR ox');
  assert.equal(packed.operators, 5);
  assert.equal(packed.over_operator_limit, false);
  assert.equal(packRepoQueries(['a/b'], 'a OR b OR c OR d OR e OR f OR g').over_operator_limit, true);
});

test('an empty search bucket points at the healthy core one', () => {
  const p = bucketPressure({
    ...RESOURCES,
    search: { limit: 30, used: 30, remaining: 0, reset: NOW + 12 },
  }, NOW);
  const [state, detail] = verdict(p.search, p.core);
  assert.equal(state, 'exhausted');
  assert.match(detail, /different buckets/);
  assert.match(detail, /12 second\\(s\\)/);
});

test('an oversized loop reports the packed alternative', () => {
  const p = bucketPressure(RESOURCES, NOW);
  const repos = Array.from({ length: 400 }, (_, i) => `acme/service-${String(i).padStart(2, '0')}`);
  const [state, detail] = verdict(p.search, p.core,
    planLoop(400, p.search.per_minute), packRepoQueries(repos, 'is:issue is:open'));
  assert.equal(state, 'over-budget');
  assert.match(detail, /refused inside the first minute/);
  assert.match(detail, /queries/);
});

test('the core comparison is stated in the same units', () => {
  const p = bucketPressure(RESOURCES, NOW);
  assert.match(verdict(p.search, p.core)[1], /83 a minute/);
});

test('a healthy bucket with no plan is clear', () => {
  const p = bucketPressure(RESOURCES, NOW);
  assert.equal(verdict(p.search, p.core)[0], 'clear');
});

test('no search bucket is not reported as healthy', () => {
  assert.equal(verdict(null, null)[0], 'no-search-bucket');
});
''',
"faq": [
 ("Does a search request use up my 5,000 an hour as well?",
  "No, and you can watch that be true. Read GET /rate_limit, run one search, read it again: search.used goes up by one and core.used does not move. They are separate buckets with separate windows, which is exactly why the failure is so confusing when it happens, because every other call on the token carries on working."),
 ("Why is 30 a minute worse than 5,000 an hour?",
  "Because the windows differ and the raw numbers are not comparable. 5,000 an hour is about 83 a minute; 30 a minute is 30. Search is the tighter allowance by nearly three to one, and it also refuses rather than queues, so the thirty-first call in a minute is an error rather than a wait. Normalising both to per-minute is the single most useful thing you can do with that document."),
 ("How many repositories fit in one query?",
  "As many repo: qualifiers as fit in 256 characters, which for typical org and repository names is somewhere between fifteen and twenty-five. Multiple repo: qualifiers are treated as alternatives and do not spend any of the five permitted AND, OR or NOT operators, so the character budget is what actually binds. Pack greedily and check each query's length before you send it."),
 ("Should I use search at all?",
  "Often not. If a list endpoint can answer the question, it is billed to core, it paginates properly and it is not capped at 1,000 results. Search earns its place for cross-repository questions and full-text matching. A loop that searches one repository at a time is usually a list endpoint that has not been found yet."),
 ("What about code search?",
  "Tighter again: 10 requests a minute, reported separately as resources.code_search in the same document. It is the bucket most likely to be empty when someone reports that search is broken, and because it has its own entry, the same normalisation shows it at 10 a minute against search's 30 without any extra work."),
],
"related": [
 ("/github/search-1000-result-cap/", "Search returns at most 1,000 results"),
 ("/github/secondary-limit-concurrency/", "Over 100 concurrent requests trips a limit"),
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
],
"citations": [CITE_SEARCH, CITE_REST_LIMITS, CITE_SEARCH_SYNTAX, CITE_RATE_ENDPOINT],
},

]
