#!/usr/bin/env python3
"""/llm/ field notes, batch B — the writing.

Four failures about money on the OpenAI and Anthropic APIs. One is a 429 that is
not a rate limit, one is the absence of a ceiling, and two are about which tokens
the invoice is actually made of. Read-only throughout: an admin-read organization
key where the endpoint demands one, a Read Only project key where it does not,
and the repair is printed for a human to run.

Neither provider exposes a per-request log. There is no endpoint on either API
that lists individual inference calls with their status codes, so every error
finding here is inferred from aggregate usage buckets or from a live probe, and
the prose says so rather than implying a log exists.
"""

CITE_ERRORS = ("Error codes — OpenAI API",
               "https://developers.openai.com/api/docs/guides/error-codes")
CITE_RATE = ("Rate limits — OpenAI API",
             "https://developers.openai.com/api/docs/guides/rate-limits")
CITE_ADMIN = ("Administration APIs — OpenAI API",
              "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_USAGE = ("Usage — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_COSTS = ("Costs — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/costs")
CITE_PROJECTS = ("Projects — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/projects")
CITE_REASONING = ("Reasoning models — OpenAI API",
                  "https://developers.openai.com/api/docs/guides/reasoning")

CITE_CL_ERRORS = ("Errors — Claude API",
                  "https://platform.claude.com/docs/en/api/errors")
CITE_CL_PRICING = ("Pricing — Claude Docs",
                   "https://platform.claude.com/docs/en/about-claude/pricing")
CITE_CL_COST = ("Get cost report — Claude Admin API",
                "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report")
CITE_CL_USAGE = ("Get messages usage report — Claude Admin API",
                 "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_CL_THINKING = ("Extended thinking — Claude Docs",
                    "https://platform.claude.com/docs/en/build-with-claude/extended-thinking")

GUIDES = [

{
"slug": "quota-exhausted-not-rate-limited",
"title": "429 credit_balance_exhausted retried forever as a rate limit",
"description": "A 429 carrying insufficient_quota is a billing wall, not a throttle. Every SDK raises RateLimitError, so the retry loop hammers it until someone notices.",
"h1": "429 credit_balance_exhausted retried forever as a rate limit",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai insufficient_quota 429", "credit_balance_exhausted",
             "organization_spend_limit_exceeded", "openai ratelimiterror retry loop",
             "anthropic credit balance is too low"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Traffic did not degrade, it stopped. Every request comes back <code>429</code>, your retry wrapper does what it was built to do, and eight hours later it is still doing it. The status code says slow down. The <code>code</code> field inside the body says the account is out of money, and nothing in the SDK draws a line between the two &mdash; <code>RateLimitError</code> is raised for both.",
"short_answer": """<p>Branch on <code>error.code</code>, never on the status. A <code>429</code> whose code is <code>insufficient_quota</code>, <code>credit_balance_exhausted</code>, <code>organization_spend_limit_exceeded</code>, <code>project_spend_limit_exceeded</code> or <code>organization_usage_limit_exceeded</code> is a billing wall: it will still be there after a thousand retries. Only a missing code, or <code>rate_limit_exceeded</code>, is worth backing off against.</p>
<p>To see it coming rather than after the fact, read month-to-date spend from <code>GET /v1/organization/costs</code> against your tier's monthly ceiling, and watch <code>num_model_requests</code> in <code>GET /v1/organization/usage/completions</code> for the hour it falls off a cliff.</p>""",
"problem": """<p>The overload is the whole problem. HTTP 429 means "too many requests", and OpenAI uses it for at least five conditions of which only one is about how many requests you sent. The other four are about money: no prepaid credits, an org spend limit you set, a project spend limit somebody else set, and the monthly ceiling OpenAI assigns your usage tier. All five arrive as the same status, and every official SDK maps that status to one exception class before anything reads the body.</p>
<p>So the retry wrapper &mdash; which is correct code, written by someone who read the rate-limit guide &mdash; treats a wall as a queue. It sleeps, it jitters, it doubles, and it asks again. Nothing about the response changes, because nothing about the account has changed. The service is not busy; it is closed. Meanwhile the one signal that would have paged somebody, a hard failure, never happens: from the outside the process looks alive and merely slow.</p>""",
"why": """<p><strong>The status code carries less information than the body.</strong> <code>429</code> is the transport's opinion. <code>error.code</code> is the platform's. Retry logic written against the first is guessing, and the guess is wrong four times out of five here.</p>
<p><strong>The SDKs collapse the distinction before you see it.</strong> <code>openai.RateLimitError</code> is raised for a genuine throttle and for an empty balance alike, because it is keyed on the status. The code is still on the exception, but nothing forces you to look, and the obvious <code>except RateLimitError: backoff()</code> never does.</p>
<p><strong>Anthropic puts the same wall behind a different status.</strong> An exhausted Claude balance is a <code>400</code> <code>invalid_request_error</code> whose message reads "Your credit balance is too low", not a <code>429</code> at all. A cross-provider retry layer that special-cases OpenAI's codes still retries Anthropic's wall, or worse, treats a genuine <code>429</code> <code>rate_limit_error</code> from Anthropic as fatal because it has no <code>code</code> field to match on.</p>
<p><strong>You cannot go back and count the damage.</strong> Neither API exposes a request log, so there is no endpoint that will tell you how many calls got a <code>429</code> yesterday or which code they carried. The evidence available to a read-only script is the shape of the aggregate usage buckets and a live probe, which is why the detection here is a cliff in <code>num_model_requests</code> rather than an error rate.</p>""",
"steps": [
 {"h": "Read error.code in the classifier, not the status",
  "body": """<p>The body is <code>{"error": {"message": ..., "type": ..., "code": ...}}</code>. Pull <code>code</code> out defensively &mdash; it is absent on some <code>429</code>s and on every Anthropic error &mdash; and make the retry decision from it. A code you do not recognise should be treated as not retryable until somebody has read it, because the failure mode of guessing wrong in that direction is a slow page instead of an infinite loop.</p>"""},
 {"h": "Give each wall code its own remedy",
  "body": """<p>They are not interchangeable. <code>credit_balance_exhausted</code> wants credits or auto-recharge. <code>organization_spend_limit_exceeded</code> and <code>project_spend_limit_exceeded</code> want a limit raised, and you set those yourself. <code>organization_usage_limit_exceeded</code> is OpenAI's own ceiling for your tier and wants a request to OpenAI. Printing "quota exceeded" for all four sends the on-call engineer to the wrong console.</p>"""},
 {"h": "Compare month-to-date spend against the tier ceiling",
  "body": """<p>Admin key. <code>GET /v1/organization/costs?start_time={month_start}&amp;bucket_width=1d&amp;limit=31</code>, sum <code>results[].amount.value</code>. The monthly usage limits by tier are $100, $500, $1,000, $5,000 and $200,000. Approaching yours predicts <code>organization_usage_limit_exceeded</code> to the day, which is the only one of these you can forecast.</p>"""},
 {"h": "Look for the cliff, because there is no error log",
  "body": """<p><code>GET /v1/organization/usage/completions?start_time={T-48h}&amp;bucket_width=1h</code>. A wall that has already been hit looks like <code>num_model_requests</code> going to zero mid-cycle and staying there. A bucket with requests but <code>output_tokens</code> of zero is a different finding &mdash; calls that failed before generation &mdash; and folding the two together is how you end up chasing the wrong outage.</p>"""},
 {"h": "Probe live for the headroom numbers",
  "body": """<p>Rate-limit headroom exists only on response headers; there is no GET that returns it. <code>GET /v1/models</code> with the project key is the cheapest real call there is, and it hands back <code>x-ratelimit-remaining-requests</code> and friends. It does not consume inference quota, so it will usually answer <code>200</code> even while inference is walled off &mdash; treat it as proof the key still authenticates, not as proof the account can generate.</p>"""},
],
"verify": """<p>Re-run after credits are added or the limit is raised. Spend should sit clear of the ceiling and the hourly buckets should show traffic again.</p>
<pre><code class="language-bash">python3 openai_quota_wall_audit.py --tier 3
# month-to-date $412.80 against a $1,000.00 tier ceiling
# 48 hourly bucket(s) read, traffic flowing, 0 finding(s)</code></pre>""",
"code_intro": "Three GETs and no writes at all. <code>OPENAI_ADMIN_KEY</code> has to be an organization admin key, because every <code>/v1/organization/*</code> endpoint rejects a project key outright; <code>OPENAI_API_KEY</code> is optional and only used for the live probe, and a Read Only project key is enough for it. The classifier is pure and is the part worth stealing: it is what belongs inside your retry wrapper, and the tests exercise it with no network at all.",
"py_file": "openai_quota_wall_audit.py",
"py": '''"""Tell an OpenAI billing wall apart from a real rate limit, before it stops you.

Read only. GET requests and nothing else: OPENAI_ADMIN_KEY is an organization
admin key (sk-admin-...) with read scopes, and OPENAI_API_KEY is an optional
project key set to Read Only, used only for a live probe. The repair is printed,
never performed, because this script holds credentials that can spend money on
inference.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_quota_wall_audit")

API = "https://api.openai.com/v1"

# 429 codes that describe money rather than traffic. None of them clears on
# retry, and each one has a different remedy in a different console.
WALL = {
    "insufficient_quota":
        "no usable balance. This is the older name for the same wall and is "
        "still what many accounts return; add credits or enable auto-recharge.",
    "credit_balance_exhausted":
        "prepaid credits are gone. Add credits or enable auto-recharge.",
    "organization_spend_limit_exceeded":
        "the monthly spend limit you set on the organization was reached. "
        "Raise it, or wait for the interval to reset.",
    "project_spend_limit_exceeded":
        "the spend limit set on this project was reached. Raise it on the "
        "project, not on the organization.",
    "organization_usage_limit_exceeded":
        "the ceiling OpenAI assigns your usage tier was reached. Nothing you "
        "own can raise this; request an increase from OpenAI.",
}

# 429 codes that really are traffic shaping and really do clear on their own.
THROTTLE = ("rate_limit_exceeded", "requests_limit_reached", "tokens_limit_reached")

# The monthly usage limit OpenAI assigns each tier, in dollars.
TIER_LIMIT = {1: 100.0, 2: 500.0, 3: 1000.0, 4: 5000.0, 5: 200000.0}


def error_fields(body):
    """Return (code, type, message) from either provider's error envelope.

    OpenAI nests the useful part under "error"; some proxies and most logged
    exception dumps hand back the inner object on its own. Everything comes
    back as a string, empty when absent, so a caller never has to guard three
    levels of dict access before it can make a decision.
    """
    if not isinstance(body, dict):
        return ("", "", "")
    err = body.get("error")
    if not isinstance(err, dict):
        err = body
    return (str(err.get("code") or ""),
            str(err.get("type") or ""),
            str(err.get("message") or ""))


def classify(status, body):
    """Decide whether an error may be retried. Pure, so the rule is testable
    offline and can be lifted straight into a retry wrapper.

    Returns (state, detail). Only "throttle" and "transient" are safe to retry.
    """
    code, etype, message = error_fields(body)
    low = message.lower()

    if status == 429:
        if code in WALL:
            return ("wall",
                    "%s: %s Retrying cannot clear this, and the SDK still "
                    "raises RateLimitError for it." % (code, WALL[code]))
        if code in THROTTLE:
            return ("throttle",
                    "%s: a real limit on how fast you may send. Back off and "
                    "honour Retry-After." % code)
        if not code:
            if etype == "rate_limit_error":
                return ("throttle",
                        "Anthropic 429 rate_limit_error. It carries no code "
                        "field, so match on type here rather than on code.")
            return ("unclassified-429",
                    "429 with no code and no recognised type. Retry once, then "
                    "fail loudly: an unbounded loop against a wall is worse "
                    "than a page.")
        return ("unclassified-429",
                "429 with unrecognised code %s. Treat as not retryable until "
                "somebody has read it." % code)

    if status == 400 and "credit balance" in low:
        return ("wall",
                "Anthropic reports an exhausted balance as a 400 "
                "invalid_request_error, not a 429. There is no code field to "
                "branch on, so the message is the only signal available; it is "
                "a fragile match and worth an alert of its own when it fires.")

    if status in (401, 403):
        return ("auth",
                "status %d: the key is wrong, revoked, or scoped away from "
                "this endpoint. Retrying will not mint a new one." % status)

    if status >= 500 or status == 408:
        return ("transient", "status %d: server side. Retry with backoff." % status)

    return ("other", "status %d, code %s" % (status, code or "none"))


def headroom(spent, limit):
    """Compare month-to-date spend against a tier ceiling. Pure.

    Returns (state, detail). A missing limit is reported as unknown rather than
    as safe, because the tier is not readable from the API and has to be told
    to the script.
    """
    if limit is None:
        return ("tier-unknown",
                "$%.2f spent this month. Pass --tier to compare it against the "
                "ceiling OpenAI assigns that tier; the API does not expose "
                "which tier you are on." % spent)
    if spent >= limit:
        return ("at-ceiling",
                "$%.2f of a $%.2f monthly ceiling. Inference is returning, or "
                "is about to return, 429 organization_usage_limit_exceeded."
                % (spent, limit))
    if spent >= limit * 0.8:
        return ("approaching",
                "$%.2f of a $%.2f monthly ceiling (%.0f%%). This is the one "
                "wall you can forecast to the day."
                % (spent, limit, spent / limit * 100))
    return ("clear", "$%.2f of a $%.2f monthly ceiling" % (spent, limit))


def stalled(buckets, now, quiet_hours=6.0):
    """Find a cliff in the aggregate usage buckets. Pure, clock passed in.

    Neither provider exposes a per-request log, so a wall that has already been
    hit is not visible as an error rate. It is visible as traffic that stops:
    the most recent bucket carrying num_model_requests, aged against now.

    A bucket with requests but no output tokens is a separate finding -- calls
    that failed before generation -- and is reported as such rather than folded
    into the cliff, because the two have completely different repairs.

    Returns (state, detail).
    """
    rows = []
    for b in buckets:
        start = b.get("start_time")
        reqs = 0
        out = 0
        for r in b.get("results", []) or []:
            reqs += int(r.get("num_model_requests") or 0)
            out += int(r.get("output_tokens") or 0)
        if isinstance(start, (int, float)):
            rows.append((float(start), reqs, out))
    rows.sort()

    if not rows:
        return ("no-data", "no usage buckets returned for this window")

    busy = [r for r in rows if r[1] > 0]
    if not busy:
        return ("no-data",
                "%d bucket(s), none with a single model request. Either nothing "
                "ran, or the wall predates the window." % len(rows))

    barren = [r for r in busy if r[2] == 0]
    if barren:
        return ("failing-before-generation",
                "%d bucket(s) with requests but zero output tokens. Those calls "
                "did not generate: they were rejected before the model ran. "
                "That is an error shape, not a spend shape." % len(barren))

    age = (now.timestamp() - busy[-1][0]) / 3600.0
    if age >= quiet_hours:
        return ("cliff",
                "last model request %.1f hour(s) ago and nothing since. Traffic "
                "stopping dead mid-cycle is what a billing wall looks like from "
                "the usage API, because there is no error log to read." % age)
    return ("flowing", "traffic in the last %.1f hour(s)" % age)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization endpoints need an "
                         "organization admin key, not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def probe(key):
    """Make the cheapest real call there is and read what comes back.

    Rate-limit headroom is only ever attached to a response; there is no GET
    that returns it. GET /v1/models does not consume inference quota, so it
    usually answers 200 even while inference is walled off. Treat it as proof
    the key still authenticates, not as proof the account can generate.
    """
    r = requests.get(API + "/models",
                     headers={"Authorization": "Bearer " + key}, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = {}
    limits = {k: v for k, v in r.headers.items()
              if k.lower().startswith("x-ratelimit")}
    return r.status_code, body, limits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tier", type=int, default=0, choices=[0, 1, 2, 3, 4, 5],
                    help="usage tier, for the monthly ceiling comparison (0 = unknown)")
    ap.add_argument("--hours", type=int, default=48,
                    help="how far back to read hourly usage buckets")
    ap.add_argument("--quiet-hours", type=float, default=6.0,
                    help="hours without a model request before it counts as a cliff")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key with read "
                  "scopes; project keys are rejected by /v1/organization/*)")
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    costs = get(s, "/organization/costs", start_time=int(month_start.timestamp()),
                bucket_width="1d", limit=31)
    spent = 0.0
    for b in costs.get("data", []):
        for r in b.get("results", []) or []:
            spent += float((r.get("amount") or {}).get("value") or 0.0)

    bad = 0
    state, detail = headroom(spent, TIER_LIMIT.get(args.tier))
    if state in ("clear", "tier-unknown"):
        log.info("%-13s %s", state, detail)
    else:
        bad += 1
        log.warning("%-13s %s", state, detail)
        log.warning("  repair: add prepaid credits, raise the org or project "
                    "spend limit, or ask OpenAI for a higher approved usage "
                    "limit. Which one depends on the error code, not the status.")

    since = now - dt.timedelta(hours=args.hours)
    usage = get(s, "/organization/usage/completions",
                start_time=int(since.timestamp()), bucket_width="1h",
                limit=max(args.hours, 1))
    buckets = usage.get("data", [])
    state, detail = stalled(buckets, now, args.quiet_hours)
    if state == "flowing":
        log.info("%-13s %s", state, detail)
    else:
        bad += 1
        log.warning("%-13s %s", state, detail)

    key = os.environ.get("OPENAI_API_KEY")
    if key:
        status, body, limits = probe(key)
        pstate, pdetail = classify(status, body) if status >= 400 else ("ok", "200")
        if pstate == "ok":
            log.info("probe         GET /v1/models answered 200; headroom %s",
                     limits or "not reported on this response")
        else:
            bad += 1
            log.warning("probe         %s  %s", pstate, pdetail)
    else:
        log.info("probe         skipped: set OPENAI_API_KEY (Read Only) to read "
                 "rate-limit headers from a live response")

    log.info("%d bucket(s) read over %d hour(s), %d finding(s)",
             len(buckets), args.hours, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-quota-wall-audit.mjs",
"js": '''/**
 * Tell an OpenAI billing wall apart from a real rate limit, before it stops you.
 *
 * Read only. GET requests and nothing else: OPENAI_ADMIN_KEY is an organization
 * admin key with read scopes, OPENAI_API_KEY is an optional Read Only project
 * key used for a live probe. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

// 429 codes that describe money rather than traffic. None clears on retry.
export const WALL = {
  insufficient_quota:
    'no usable balance. This is the older name for the same wall and is still ' +
    'what many accounts return; add credits or enable auto-recharge.',
  credit_balance_exhausted:
    'prepaid credits are gone. Add credits or enable auto-recharge.',
  organization_spend_limit_exceeded:
    'the monthly spend limit you set on the organization was reached. Raise it, ' +
    'or wait for the interval to reset.',
  project_spend_limit_exceeded:
    'the spend limit set on this project was reached. Raise it on the project, ' +
    'not on the organization.',
  organization_usage_limit_exceeded:
    'the ceiling OpenAI assigns your usage tier was reached. Nothing you own ' +
    'can raise this; request an increase from OpenAI.',
};

const THROTTLE = ['rate_limit_exceeded', 'requests_limit_reached', 'tokens_limit_reached'];

export const TIER_LIMIT = { 1: 100, 2: 500, 3: 1000, 4: 5000, 5: 200000 };

/**
 * Return [code, type, message] from either provider's error envelope. Empty
 * strings when absent, so callers never guard three levels of property access.
 */
export function errorFields(body) {
  if (!body || typeof body !== 'object') return ['', '', ''];
  const err = (body.error && typeof body.error === 'object') ? body.error : body;
  return [String(err.code ?? ''), String(err.type ?? ''), String(err.message ?? '')];
}

/**
 * Decide whether an error may be retried. Pure, so it is testable offline and
 * can be lifted straight into a retry wrapper. Returns [state, detail]. Only
 * 'throttle' and 'transient' are safe to retry.
 */
export function classify(status, body) {
  const [code, etype, message] = errorFields(body);
  const low = message.toLowerCase();

  if (status === 429) {
    if (Object.hasOwn(WALL, code)) {
      return ['wall',
        `${code}: ${WALL[code]} Retrying cannot clear this, and the SDK still ` +
        'raises RateLimitError for it.'];
    }
    if (THROTTLE.includes(code)) {
      return ['throttle',
        `${code}: a real limit on how fast you may send. Back off and honour ` +
        'Retry-After.'];
    }
    if (!code) {
      if (etype === 'rate_limit_error') {
        return ['throttle',
          'Anthropic 429 rate_limit_error. It carries no code field, so match ' +
          'on type here rather than on code.'];
      }
      return ['unclassified-429',
        '429 with no code and no recognised type. Retry once, then fail loudly: ' +
        'an unbounded loop against a wall is worse than a page.'];
    }
    return ['unclassified-429',
      `429 with unrecognised code ${code}. Treat as not retryable until ` +
      'somebody has read it.'];
  }

  if (status === 400 && low.includes('credit balance')) {
    return ['wall',
      'Anthropic reports an exhausted balance as a 400 invalid_request_error, ' +
      'not a 429. There is no code field to branch on, so the message is the ' +
      'only signal available; it is a fragile match and worth an alert of its ' +
      'own when it fires.'];
  }

  if (status === 401 || status === 403) {
    return ['auth',
      `status ${status}: the key is wrong, revoked, or scoped away from this ` +
      'endpoint. Retrying will not mint a new one.'];
  }

  if (status >= 500 || status === 408) {
    return ['transient', `status ${status}: server side. Retry with backoff.`];
  }

  return ['other', `status ${status}, code ${code || 'none'}`];
}

/** Compare month-to-date spend against a tier ceiling. Pure. */
export function headroom(spent, limit) {
  if (limit === null || limit === undefined) {
    return ['tier-unknown',
      `$${spent.toFixed(2)} spent this month. Pass --tier to compare it against ` +
      'the ceiling OpenAI assigns that tier; the API does not expose which tier ' +
      'you are on.'];
  }
  if (spent >= limit) {
    return ['at-ceiling',
      `$${spent.toFixed(2)} of a $${limit.toFixed(2)} monthly ceiling. Inference ` +
      'is returning, or is about to return, 429 organization_usage_limit_exceeded.'];
  }
  if (spent >= limit * 0.8) {
    return ['approaching',
      `$${spent.toFixed(2)} of a $${limit.toFixed(2)} monthly ceiling ` +
      `(${((spent / limit) * 100).toFixed(0)}%). This is the one wall you can ` +
      'forecast to the day.'];
  }
  return ['clear', `$${spent.toFixed(2)} of a $${limit.toFixed(2)} monthly ceiling`];
}

/**
 * Find a cliff in the aggregate usage buckets. Pure, clock passed in.
 *
 * There is no per-request log on either API, so a wall that has already been hit
 * is not visible as an error rate. It is visible as traffic that stops.
 * Returns [state, detail].
 */
export function stalled(buckets, now, quietHours = 6) {
  const rows = [];
  for (const b of buckets) {
    let reqs = 0;
    let out = 0;
    for (const r of b.results ?? []) {
      reqs += Number(r.num_model_requests ?? 0);
      out += Number(r.output_tokens ?? 0);
    }
    if (typeof b.start_time === 'number') rows.push([b.start_time, reqs, out]);
  }
  rows.sort((a, b) => a[0] - b[0]);

  if (rows.length === 0) return ['no-data', 'no usage buckets returned for this window'];

  const busy = rows.filter((r) => r[1] > 0);
  if (busy.length === 0) {
    return ['no-data',
      `${rows.length} bucket(s), none with a single model request. Either ` +
      'nothing ran, or the wall predates the window.'];
  }

  const barren = busy.filter((r) => r[2] === 0);
  if (barren.length > 0) {
    return ['failing-before-generation',
      `${barren.length} bucket(s) with requests but zero output tokens. Those ` +
      'calls did not generate: they were rejected before the model ran. That is ' +
      'an error shape, not a spend shape.'];
  }

  const age = (now.getTime() / 1000 - busy[busy.length - 1][0]) / 3600;
  if (age >= quietHours) {
    return ['cliff',
      `last model request ${age.toFixed(1)} hour(s) ago and nothing since. ` +
      'Traffic stopping dead mid-cycle is what a billing wall looks like from ' +
      'the usage API, because there is no error log to read.'];
  }
  return ['flowing', `traffic in the last ${age.toFixed(1)} hour(s)`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization endpoints need ` +
                    'an organization admin key, not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key with read ' +
                  'scopes; project keys are rejected by /v1/organization/*)');
    process.exitCode = 2;
    return;
  }

  const argv = process.argv;
  const tier = Number(argv.includes('--tier') ? argv[argv.indexOf('--tier') + 1] : 0) || 0;
  const hours = Number(argv.includes('--hours') ? argv[argv.indexOf('--hours') + 1] : 48) || 48;

  const now = new Date();
  const monthStart = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1) / 1000;

  const costs = await get(admin, '/organization/costs',
    { start_time: Math.floor(monthStart), bucket_width: '1d', limit: 31 });
  let spent = 0;
  for (const b of costs.data ?? []) {
    for (const r of b.results ?? []) spent += Number(r.amount?.value ?? 0);
  }

  let bad = 0;
  {
    const [state, detail] = headroom(spent, TIER_LIMIT[tier] ?? null);
    if (state === 'clear' || state === 'tier-unknown') {
      console.log(`${state.padEnd(13)} ${detail}`);
    } else {
      bad += 1;
      console.warn(`${state.padEnd(13)} ${detail}`);
      console.warn('  repair: add prepaid credits, raise the org or project spend ' +
                   'limit, or ask OpenAI for a higher approved usage limit. Which ' +
                   'one depends on the error code, not the status.');
    }
  }

  const since = Math.floor(now.getTime() / 1000 - hours * 3600);
  const usage = await get(admin, '/organization/usage/completions',
    { start_time: since, bucket_width: '1h', limit: Math.max(hours, 1) });
  const buckets = usage.data ?? [];
  {
    const [state, detail] = stalled(buckets, now);
    if (state === 'flowing') console.log(`${state.padEnd(13)} ${detail}`);
    else { bad += 1; console.warn(`${state.padEnd(13)} ${detail}`); }
  }

  const key = process.env.OPENAI_API_KEY;
  if (key) {
    const res = await fetch(`${API}/models`, { headers: { Authorization: `Bearer ${key}` } });
    if (res.ok) {
      console.log(`probe         GET /v1/models answered 200; headroom ` +
                  `${res.headers.get('x-ratelimit-remaining-requests') ?? 'not reported'}`);
    } else {
      const body = await res.json().catch(() => ({}));
      const [state, detail] = classify(res.status, body);
      bad += 1;
      console.warn(`probe         ${state}  ${detail}`);
    }
  } else {
    console.log('probe         skipped: set OPENAI_API_KEY (Read Only) to read ' +
                'rate-limit headers from a live response');
  }

  console.log(`${buckets.length} bucket(s) read over ${hours} hour(s), ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests that matter are the ones that pin the branch. <code>insufficient_quota</code> and <code>rate_limit_exceeded</code> arrive with the identical status and have to come back as different states, or the whole note is decorative. A <code>429</code> with a code nobody recognises has to be treated as not retryable, because that is the safe direction to be wrong in. And the cliff detector is exercised at a fixed clock, so the boundary between quiet and stalled is a number you can read rather than a function of when the suite ran.",
"test_py_file": "test_openai_quota_wall_audit.py",
"test_py": '''import datetime as dt

from openai_quota_wall_audit import classify, error_fields, headroom, stalled

NOW = dt.datetime(2026, 8, 30, 12, 0, tzinfo=dt.timezone.utc)


def hours_ago(h):
    return int(NOW.timestamp() - h * 3600)


def bucket(h, requests=10, output=4000):
    return {"start_time": hours_ago(h),
            "results": [{"num_model_requests": requests, "input_tokens": 900,
                         "output_tokens": output}]}


def openai_error(code, status_message="You exceeded your current quota."):
    return {"error": {"message": status_message, "type": "insufficient_quota",
                      "code": code}}


def test_error_fields_reads_nested_and_bare_envelopes():
    assert error_fields(openai_error("insufficient_quota"))[0] == "insufficient_quota"
    assert error_fields({"code": "rate_limit_exceeded"})[0] == "rate_limit_exceeded"
    assert error_fields(None) == ("", "", "")
    assert error_fields({"error": "a string, not an object"})[0] == ""


def test_the_whole_point_two_429s_that_are_not_the_same_thing():
    wall, wall_detail = classify(429, openai_error("insufficient_quota"))
    throttle, _ = classify(429, openai_error("rate_limit_exceeded"))
    assert wall == "wall"
    assert throttle == "throttle"
    assert "RateLimitError" in wall_detail


def test_every_billing_code_is_a_wall_with_its_own_remedy():
    remedies = {}
    for code in ("credit_balance_exhausted", "organization_spend_limit_exceeded",
                 "project_spend_limit_exceeded", "organization_usage_limit_exceeded"):
        state, detail = classify(429, openai_error(code))
        assert state == "wall", code
        remedies[code] = detail
    # Four different consoles. Printing one message for all four sends the
    # on-call engineer to the wrong place.
    assert len(set(remedies.values())) == 4


def test_an_unrecognised_429_code_is_not_retried_blindly():
    state, detail = classify(429, openai_error("some_new_code_2027"))
    assert state == "unclassified-429"
    assert "not retryable" in detail


def test_a_429_with_no_code_at_all_is_still_not_a_free_retry_loop():
    assert classify(429, {"error": {"message": "Too many requests"}})[0] == "unclassified-429"


def test_anthropic_429_matches_on_type_because_it_has_no_code():
    state, _ = classify(429, {"type": "error",
                              "error": {"type": "rate_limit_error",
                                        "message": "Number of requests has exceeded"}})
    assert state == "throttle"


def test_anthropic_puts_the_same_wall_behind_a_400():
    state, detail = classify(400, {"error": {
        "type": "invalid_request_error",
        "message": "Your credit balance is too low to access the Claude API."}})
    assert state == "wall"
    assert "400" in detail


def test_auth_and_server_errors_are_not_confused_with_either():
    assert classify(401, {})[0] == "auth"
    assert classify(503, {})[0] == "transient"
    assert classify(404, {})[0] == "other"


def test_headroom_forecasts_the_one_wall_that_can_be_forecast():
    assert headroom(120.0, None)[0] == "tier-unknown"
    assert headroom(120.0, 1000.0)[0] == "clear"
    assert headroom(850.0, 1000.0)[0] == "approaching"
    assert headroom(1000.0, 1000.0)[0] == "at-ceiling"


def test_stalled_reads_a_cliff_against_the_clock_it_is_given():
    fresh = stalled([bucket(30), bucket(2)], NOW)
    assert fresh[0] == "flowing"
    state, detail = stalled([bucket(30), bucket(20)], NOW)
    assert state == "cliff"
    assert "20.0 hour(s) ago" in detail


def test_requests_with_no_output_is_a_different_finding_from_a_cliff():
    # A bucket that made calls and generated nothing is an error shape. Folding
    # it into the cliff sends you looking for a billing problem that is not there.
    state, _ = stalled([bucket(20, requests=40, output=0), bucket(1)], NOW)
    assert state == "failing-before-generation"


def test_empty_and_silent_windows_do_not_claim_a_wall():
    assert stalled([], NOW)[0] == "no-data"
    assert stalled([bucket(3, requests=0, output=0)], NOW)[0] == "no-data"
''',
"test_js_file": "openai-quota-wall-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, errorFields, headroom, stalled } from './openai-quota-wall-audit.mjs';

const NOW = new Date('2026-08-30T12:00:00Z');
const hoursAgo = (h) => Math.floor(NOW.getTime() / 1000 - h * 3600);

const bucket = (h, requests = 10, output = 4000) => ({
  start_time: hoursAgo(h),
  results: [{ num_model_requests: requests, input_tokens: 900, output_tokens: output }],
});

const openaiError = (code) => ({
  error: { message: 'You exceeded your current quota.', type: 'insufficient_quota', code },
});

test('error fields reads nested and bare envelopes', () => {
  assert.equal(errorFields(openaiError('insufficient_quota'))[0], 'insufficient_quota');
  assert.equal(errorFields({ code: 'rate_limit_exceeded' })[0], 'rate_limit_exceeded');
  assert.deepEqual(errorFields(null), ['', '', '']);
  assert.equal(errorFields({ error: 'a string, not an object' })[0], '');
});

test('the whole point: two 429s that are not the same thing', () => {
  const [wall, wallDetail] = classify(429, openaiError('insufficient_quota'));
  const [throttle] = classify(429, openaiError('rate_limit_exceeded'));
  assert.equal(wall, 'wall');
  assert.equal(throttle, 'throttle');
  assert.match(wallDetail, /RateLimitError/);
});

test('every billing code is a wall with its own remedy', () => {
  const remedies = new Set();
  for (const code of ['credit_balance_exhausted', 'organization_spend_limit_exceeded',
    'project_spend_limit_exceeded', 'organization_usage_limit_exceeded']) {
    const [state, detail] = classify(429, openaiError(code));
    assert.equal(state, 'wall', code);
    remedies.add(detail);
  }
  assert.equal(remedies.size, 4);
});

test('an unrecognised 429 code is not retried blindly', () => {
  const [state, detail] = classify(429, openaiError('some_new_code_2027'));
  assert.equal(state, 'unclassified-429');
  assert.match(detail, /not retryable/);
});

test('a 429 with no code at all is still not a free retry loop', () => {
  assert.equal(classify(429, { error: { message: 'Too many requests' } })[0],
    'unclassified-429');
});

test('anthropic 429 matches on type because it has no code', () => {
  const [state] = classify(429, {
    type: 'error',
    error: { type: 'rate_limit_error', message: 'Number of requests has exceeded' },
  });
  assert.equal(state, 'throttle');
});

test('anthropic puts the same wall behind a 400', () => {
  const [state, detail] = classify(400, {
    error: {
      type: 'invalid_request_error',
      message: 'Your credit balance is too low to access the Claude API.',
    },
  });
  assert.equal(state, 'wall');
  assert.match(detail, /400/);
});

test('auth and server errors are not confused with either', () => {
  assert.equal(classify(401, {})[0], 'auth');
  assert.equal(classify(503, {})[0], 'transient');
  assert.equal(classify(404, {})[0], 'other');
});

test('headroom forecasts the one wall that can be forecast', () => {
  assert.equal(headroom(120, null)[0], 'tier-unknown');
  assert.equal(headroom(120, 1000)[0], 'clear');
  assert.equal(headroom(850, 1000)[0], 'approaching');
  assert.equal(headroom(1000, 1000)[0], 'at-ceiling');
});

test('stalled reads a cliff against the clock it is given', () => {
  assert.equal(stalled([bucket(30), bucket(2)], NOW)[0], 'flowing');
  const [state, detail] = stalled([bucket(30), bucket(20)], NOW);
  assert.equal(state, 'cliff');
  assert.match(detail, /20\\.0 hour\\(s\\) ago/);
});

test('requests with no output is a different finding from a cliff', () => {
  const [state] = stalled([bucket(20, 40, 0), bucket(1)], NOW);
  assert.equal(state, 'failing-before-generation');
});

test('empty and silent windows do not claim a wall', () => {
  assert.equal(stalled([], NOW)[0], 'no-data');
  assert.equal(stalled([bucket(3, 0, 0)], NOW)[0], 'no-data');
});
''',
"faq": [
 ("Is a 429 from OpenAI ever safe to retry?",
  "Only when the code says so. A 429 with code rate_limit_exceeded, or with no code at all on a genuine throttle, clears on its own and deserves backoff. A 429 with insufficient_quota, credit_balance_exhausted, organization_spend_limit_exceeded, project_spend_limit_exceeded or organization_usage_limit_exceeded is a billing state, and no amount of waiting changes it."),
 ("Why does the SDK raise RateLimitError for a billing failure?",
  "Because the exception class is chosen from the HTTP status, before anything inspects the body. 429 maps to RateLimitError in every official client. The code is still available on the exception object; nothing forces you to read it, and the obvious except-and-backoff never does."),
 ("What is the difference between insufficient_quota and credit_balance_exhausted?",
  "They describe the same wall. insufficient_quota is the older name and is still what many accounts return; credit_balance_exhausted is the newer one. Match both, or a code rename ships an outage into your retry loop."),
 ("Can I find out how many requests got a 429 yesterday?",
  "No. Neither OpenAI nor Anthropic exposes a per-request log through the API, so there is no error rate to query. What a read-only script can see is the aggregate usage buckets: traffic falling to zero mid-cycle, or a bucket with num_model_requests above zero and output_tokens at zero, which means calls that were rejected before generation."),
 ("Does this apply to Anthropic too?",
  "The same failure, moved. Claude returns 429 with type rate_limit_error for a real throttle, and an exhausted balance comes back as a 400 invalid_request_error whose message mentions the credit balance. A cross-provider retry layer that only knows OpenAI's codes will retry that 400 or fail on the 429, so classify per provider rather than per status."),
],
"related": [
 ("/llm/no-organization-spend-limit/", "No spend limit means no ceiling"),
 ("/llm/reasoning-tokens-billed-invisibly/", "Reasoning tokens billed but never returned"),
 ("/llm/output-tokens-dominate-cost/", "Output tokens are what the bill is made of"),
],
"citations": [CITE_ERRORS, CITE_RATE, CITE_CL_ERRORS, CITE_USAGE],
},


{
"slug": "no-organization-spend-limit",
"title": "No hard spend limit is set, so the bill has no ceiling",
"description": "OpenAI's hard spend limit is opt-in and lives on its own admin endpoint. Read it, the alerts, and month-to-date spend to see if anything stops a runaway.",
"h1": "no hard spend limit is set, so the bill has no ceiling",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai spend limit api", "openai organization spend_limit",
             "openai spend alerts", "limit openai api spending",
             "openai budget not enforced"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The console shows a budget chart, and everybody who has looked at it believes it is a brake. It is not; it is a chart. The hard limit is a separate object on a separate admin endpoint, it is off by default, and until somebody turns it on there is no amount of spend in a month that will cause a request to be refused.",
"short_answer": """<p>Three read-only calls with an organization <strong>admin</strong> key. <code>GET /v1/organization/spend_limit</code> returns a <code>threshold_amount</code> <strong>in cents</strong>, an <code>interval</code>, and an <code>enforcement.status</code> that is either <code>"enforcing"</code> or <code>"inactive"</code>. <code>GET /v1/organization/spend_alerts</code> returns the warnings, which are configured separately and are frequently absent. <code>GET /v1/organization/costs</code> gives you month-to-date spend to judge both against.</p>
<p>Four states are worth telling apart: no limit at all, a limit that exists but is not enforcing, a limit so high it can never fire, and a limit with no alerts underneath it &mdash; a brake with no warning light.</p>""",
"problem": """<p>Post-paid billing with auto-recharge has no natural ceiling. The platform's job is to serve requests and it will keep serving them, funded by a card, for as long as something keeps asking. The things that ask are rarely people: an agent loop with a broken termination condition, a retry storm that has mistaken a wall for a queue, a key that got committed to a public repository on Friday evening.</p>
<p>None of those produce an error. They produce traffic, and traffic is what the platform is for. The first signal is the invoice, or a spend alert if somebody configured one, and the cost report itself lags real time &mdash; so even a person watching the dashboard is watching history. The limit is the only mechanism in the system that turns a runaway into a controlled outage, and it is opt-in.</p>""",
"why": """<p><strong>Enforcement and display live in different places.</strong> The budget number most teams have seen is a visualisation of the cost report. The thing that refuses requests is <code>organization.spend_limit</code>, on <code>/v1/organization/spend_limit</code>, with its own <code>enforcement.status</code>. An object can exist with a threshold set and a status of <code>"inactive"</code>, which reads as configured and behaves as absent.</p>
<p><strong>Alerts and limits are separately opt-in.</strong> You can have alerts and no limit, which is a warning with no brake. You can have a limit and no alerts, which is a brake with no warning &mdash; the first anyone hears is production returning <code>429</code> <code>organization_spend_limit_exceeded</code>. Both configurations are common and neither is visible without asking two endpoints.</p>
<p><strong><code>threshold_amount</code> is in cents.</strong> A limit typed as <code>500</code> intending five hundred dollars is five dollars, and it will fire within the hour. The mistake is easy, the symptom is a total outage, and the value reads perfectly plausible in the response body.</p>
<p><strong>Anthropic has no equivalent to read.</strong> The Claude Admin API exposes <code>GET /v1/organizations/cost_report</code> and nothing that sets or reports a spending ceiling. On that side the honest finding is that no API-visible brake exists at all, and the control has to be a workspace-level budget you manage by hand.</p>""",
"steps": [
 {"h": "Read the limit object, not the dashboard",
  "body": """<p><code>GET /v1/organization/spend_limit</code> with an admin key. You are looking at two fields: <code>threshold_amount</code>, in cents, and <code>enforcement.status</code>. A missing object and a present object with status <code>"inactive"</code> have exactly the same effect on your bill, and they should be reported as two different findings because they are two different mistakes.</p>"""},
 {"h": "Read the alerts separately",
  "body": """<p><code>GET /v1/organization/spend_alerts</code> returns <code>organization.spend_alert</code> objects with their own <code>threshold_amount</code> and a <code>notification_channel</code> carrying <code>recipients[]</code>. An empty list under a working limit is the quiet failure here. So is a recipient list full of people who have left, which you can check against <code>GET /v1/organization/users</code>.</p>"""},
 {"h": "Get month-to-date spend to judge the number against",
  "body": """<p><code>GET /v1/organization/costs?start_time={month_start}&amp;limit=31</code>, summing <code>results[].amount.value</code>. Without this the limit is an abstract number. With it you can say whether the ceiling is five times the run rate, in which case it will never fire, or below it, in which case it already has.</p>"""},
 {"h": "Project the month before you judge the ceiling",
  "body": """<p>Spend on the third of the month tells you almost nothing on its own. Pro-rate it: divide by the fraction of the month elapsed and you have a projected month-end figure to compare the threshold against. A limit at twice the projection is a real brake; a limit at fifty times it is decoration.</p>"""},
 {"h": "Repeat per project, and print the bodies rather than sending them",
  "body": """<p>Projects have their own limits at <code>GET /v1/organization/projects/{project_id}/spend_limit</code>. Walk them, then print the exact <code>POST</code> bodies for a human: the limit at roughly twice the projected month-end, in cents, and alerts at 50%, 75% and 90% of it with real recipients. A script holding an admin key should not be the thing that changes what your organization is allowed to spend.</p>"""},
],
"verify": """<p>Re-run after the limit and alerts are configured. Every scope should report <code>guarded</code>.</p>
<pre><code class="language-bash">python3 openai_spend_limit_audit.py --projects
# guarded   organization  $412.80 MTD, projecting $427.03, limit $900.00, 3 alert(s)
# 1 scope(s) checked, 0 finding(s)</code></pre>""",
"code_intro": "Read-only against <code>/v1/organization/*</code>, which means an organization <strong>admin</strong> key: <code>OPENAI_ADMIN_KEY</code>. A project key is rejected by every one of these endpoints, so there is no way to run this with the credential your application uses, and that is the correct outcome. The four pure functions carry all the judgement &mdash; the cents conversion, the month projection, the verdict, and the check that alert recipients still work here.",
"py_file": "openai_spend_limit_audit.py",
"py": '''"""Report whether anything would stop a runaway OpenAI bill.

Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
organization admin key (sk-admin-...) with read scopes, because every
/v1/organization endpoint rejects a project key. The repair is printed, never
performed, because a script should not be the thing that changes what an
organization is allowed to spend.
"""
import argparse
import calendar
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_spend_limit_audit")

API = "https://api.openai.com/v1"


def threshold_dollars(limit):
    """Read threshold_amount as dollars, or None when no limit is configured.

    The field is in CENTS. A limit typed as 500 meaning five hundred dollars is
    five dollars and takes production down inside the hour, so the conversion
    lives in one named place rather than inline at three call sites.
    """
    if not isinstance(limit, dict):
        return None
    obj = limit.get("spend_limit") if isinstance(limit.get("spend_limit"), dict) else limit
    raw = obj.get("threshold_amount")
    if raw is None or raw == "":
        return None
    try:
        return float(raw) / 100.0
    except (TypeError, ValueError):
        return None


def projected_month_end(spent, now):
    """Pro-rate month-to-date spend to a month-end figure. Pure, clock injected.

    Spend on the third of the month says almost nothing about the month. The
    fraction of the month elapsed is measured to the hour, so the first day
    does not divide by zero and does not produce an absurd projection either.
    """
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    elapsed_hours = (now.day - 1) * 24 + now.hour + now.minute / 60.0
    total_hours = days_in_month * 24.0
    fraction = max(elapsed_hours / total_hours, 1.0 / total_hours)
    return spent / fraction


def unknown_recipients(alerts, known_emails):
    """Alert recipients who are not members of the organization any more.

    An alert addressed to someone who left is not an alert. Returned sorted so
    the output is stable between runs.
    """
    known = {str(e).strip().lower() for e in known_emails}
    missing = set()
    for a in alerts:
        channel = a.get("notification_channel") or {}
        for r in channel.get("recipients") or []:
            if str(r).strip().lower() not in known:
                missing.add(str(r))
    return sorted(missing)


def verdict(limit, alerts, spent, now):
    """Classify one scope's protection against a runaway. Pure.

    Returns (state, detail). Ordered deliberately: an absent limit and an
    inactive one have the same effect on the bill and different repairs, and a
    ceiling that can never fire is a separate finding from one that already has.
    """
    projected = projected_month_end(spent, now)
    threshold = threshold_dollars(limit)
    money = "$%.2f month-to-date, projecting $%.2f" % (spent, projected)

    if threshold is None:
        return ("no-limit",
                "%s, and no spend limit is configured. Nothing in the platform "
                "will refuse a request no matter how much a runaway spends."
                % money)

    status = ""
    if isinstance(limit, dict):
        obj = limit.get("spend_limit") if isinstance(limit.get("spend_limit"), dict) else limit
        enforcement = obj.get("enforcement") or {}
        status = str(enforcement.get("status") or "")

    if status and status != "enforcing":
        return ("not-enforcing",
                "%s. A limit of $%.2f exists but enforcement.status is %r, so it "
                "displays and does not brake." % (money, threshold, status))

    if threshold * 100 <= projected:
        return ("cents-mistake",
                "%s, against a limit of $%.2f. threshold_amount is in cents: a "
                "value this far below the run rate is almost always a figure "
                "typed as dollars, which is 100x too low and will page you "
                "immediately." % (money, threshold))

    if threshold <= spent:
        return ("breached",
                "%s, against a limit of $%.2f. Requests are already being "
                "refused with 429 organization_spend_limit_exceeded."
                % (money, threshold))

    if threshold <= projected:
        return ("will-breach",
                "%s, against a limit of $%.2f. At this run rate the brake "
                "engages before the interval resets." % (money, threshold))

    if threshold >= projected * 5:
        return ("ceiling-too-high",
                "%s, against a limit of $%.2f. A ceiling more than five times "
                "the run rate cannot fire in time to be useful."
                % (money, threshold))

    if not alerts:
        return ("no-alerts",
                "%s, with a limit of $%.2f enforcing and no spend alerts. A "
                "brake with no warning light: the first signal is production "
                "returning 429." % (money, threshold))

    return ("guarded",
            "%s, limit $%.2f, %d alert(s)" % (money, threshold, len(alerts)))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization endpoints need an "
                         "organization admin key, not a project key"
                         % r.status_code)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return r.json()


def month_to_date(session, now, project_id=None):
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    params = {"start_time": int(start.timestamp()), "limit": 31}
    if project_id:
        params["project_ids"] = project_id
    costs = get(session, "/organization/costs", **params)
    total = 0.0
    for b in costs.get("data", []):
        for r in b.get("results", []) or []:
            total += float((r.get("amount") or {}).get("value") or 0.0)
    return total


def report(scope, limit, alerts, spent, now):
    state, detail = verdict(limit, alerts, spent, now)
    line = "%-16s %-24s %s" % (state, scope, detail)
    if state == "guarded":
        log.info(line)
        return 0
    log.warning(line)
    projected = projected_month_end(spent, now)
    suggested = int(round(projected * 2)) * 100
    log.warning("  repair, to run yourself: POST %s/organization/spend_limit "
                "with a body of {\\"threshold_amount\\": %d, \\"currency\\": "
                "\\"USD\\", \\"interval\\": \\"month\\"} -- that is %d cents, "
                "which is $%.2f.", API, suggested, suggested, suggested / 100.0)
    log.warning("  then alerts at 50%%, 75%% and 90%% of it via "
                "%s/organization/spend_alerts, with a real recipients list.", API)
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--projects", action="store_true",
                    help="also read the per-project limit and alerts")
    ap.add_argument("--max-projects", type=int, default=25,
                    help="stop after this many projects")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key with read "
                  "scopes; project keys are rejected by /v1/organization/*)")
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})

    limit = get(s, "/organization/spend_limit")
    alerts = get(s, "/organization/spend_alerts", limit=100).get("data", [])
    spent = month_to_date(s, now)

    scopes = 1
    bad = report("organization", limit, alerts, spent, now)

    users = get(s, "/organization/users", limit=100).get("data", [])
    stale = unknown_recipients(alerts, [u.get("email") for u in users])
    if stale:
        bad += 1
        log.warning("%-16s %-24s alert recipients not in the organization: %s",
                    "stale-recipient", "organization", ", ".join(stale))

    if args.projects:
        projects = get(s, "/organization/projects", limit=args.max_projects)
        for p in projects.get("data", [])[:args.max_projects]:
            pid = p.get("id")
            if not pid or str(p.get("status") or "active") != "active":
                continue
            scopes += 1
            plimit = get(s, "/organization/projects/%s/spend_limit" % pid)
            palerts = get(s, "/organization/projects/%s/spend_alerts" % pid,
                          limit=100).get("data", [])
            pspent = month_to_date(s, now, project_id=pid)
            bad += report(p.get("name") or pid, plimit, palerts, pspent, now)

    log.info("%d scope(s) checked, %d finding(s)", scopes, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-spend-limit-audit.mjs",
"js": '''/**
 * Report whether anything would stop a runaway OpenAI bill.
 *
 * Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
 * organization admin key with read scopes, because every /v1/organization
 * endpoint rejects a project key. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

/**
 * Read threshold_amount as dollars, or null when no limit is configured. The
 * field is in CENTS; a value typed as dollars is 100x too low and takes
 * production down inside the hour, so the conversion lives in one named place.
 */
export function thresholdDollars(limit) {
  if (!limit || typeof limit !== 'object') return null;
  const obj = (limit.spend_limit && typeof limit.spend_limit === 'object')
    ? limit.spend_limit : limit;
  const raw = obj.threshold_amount;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n / 100 : null;
}

/** Pro-rate month-to-date spend to a month-end figure. Pure, clock injected. */
export function projectedMonthEnd(spent, now) {
  const daysInMonth = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 0))
    .getUTCDate();
  const elapsedHours = (now.getUTCDate() - 1) * 24 + now.getUTCHours()
    + now.getUTCMinutes() / 60;
  const totalHours = daysInMonth * 24;
  const fraction = Math.max(elapsedHours / totalHours, 1 / totalHours);
  return spent / fraction;
}

/** Alert recipients who are not members of the organization any more. Sorted. */
export function unknownRecipients(alerts, knownEmails) {
  const known = new Set(knownEmails.map((e) => String(e ?? '').trim().toLowerCase()));
  const missing = new Set();
  for (const a of alerts) {
    for (const r of a.notification_channel?.recipients ?? []) {
      if (!known.has(String(r).trim().toLowerCase())) missing.add(String(r));
    }
  }
  return [...missing].sort();
}

/**
 * Classify one scope's protection against a runaway. Pure. Returns
 * [state, detail].
 */
export function verdict(limit, alerts, spent, now) {
  const projected = projectedMonthEnd(spent, now);
  const threshold = thresholdDollars(limit);
  const money = `$${spent.toFixed(2)} month-to-date, projecting $${projected.toFixed(2)}`;

  if (threshold === null) {
    return ['no-limit',
      `${money}, and no spend limit is configured. Nothing in the platform will ` +
      'refuse a request no matter how much a runaway spends.'];
  }

  const obj = (limit.spend_limit && typeof limit.spend_limit === 'object')
    ? limit.spend_limit : limit;
  const status = String(obj.enforcement?.status ?? '');

  if (status && status !== 'enforcing') {
    return ['not-enforcing',
      `${money}. A limit of $${threshold.toFixed(2)} exists but ` +
      `enforcement.status is "${status}", so it displays and does not brake.`];
  }

  if (threshold * 100 <= projected) {
    return ['cents-mistake',
      `${money}, against a limit of $${threshold.toFixed(2)}. threshold_amount ` +
      'is in cents: a value this far below the run rate is almost always a ' +
      'figure typed as dollars, which is 100x too low and will page you ' +
      'immediately.'];
  }

  if (threshold <= spent) {
    return ['breached',
      `${money}, against a limit of $${threshold.toFixed(2)}. Requests are ` +
      'already being refused with 429 organization_spend_limit_exceeded.'];
  }

  if (threshold <= projected) {
    return ['will-breach',
      `${money}, against a limit of $${threshold.toFixed(2)}. At this run rate ` +
      'the brake engages before the interval resets.'];
  }

  if (threshold >= projected * 5) {
    return ['ceiling-too-high',
      `${money}, against a limit of $${threshold.toFixed(2)}. A ceiling more ` +
      'than five times the run rate cannot fire in time to be useful.'];
  }

  if (!alerts || alerts.length === 0) {
    return ['no-alerts',
      `${money}, with a limit of $${threshold.toFixed(2)} enforcing and no ` +
      'spend alerts. A brake with no warning light: the first signal is ' +
      'production returning 429.'];
  }

  return ['guarded',
    `${money}, limit $${threshold.toFixed(2)}, ${alerts.length} alert(s)`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization endpoints need ` +
                    'an organization admin key, not a project key');
  }
  if (res.status === 404) return {};
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function monthToDate(key, now, projectId) {
  const start = Math.floor(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1) / 1000);
  const params = { start_time: start, limit: 31 };
  if (projectId) params.project_ids = projectId;
  const costs = await get(key, '/organization/costs', params);
  let total = 0;
  for (const b of costs.data ?? []) {
    for (const r of b.results ?? []) total += Number(r.amount?.value ?? 0);
  }
  return total;
}

function report(scope, limit, alerts, spent, now) {
  const [state, detail] = verdict(limit, alerts, spent, now);
  const line = `${state.padEnd(16)} ${String(scope).padEnd(24)} ${detail}`;
  if (state === 'guarded') { console.log(line); return 0; }
  console.warn(line);
  const suggested = Math.round(projectedMonthEnd(spent, now) * 2) * 100;
  console.warn(`  repair, to run yourself: POST ${API}/organization/spend_limit ` +
               `with a body of {"threshold_amount": ${suggested}, "currency": ` +
               `"USD", "interval": "month"} -- that is ${suggested} cents, which ` +
               `is $${(suggested / 100).toFixed(2)}.`);
  console.warn(`  then alerts at 50%, 75% and 90% of it via ` +
               `${API}/organization/spend_alerts, with a real recipients list.`);
  return 1;
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key with read ' +
                  'scopes; project keys are rejected by /v1/organization/*)');
    process.exitCode = 2;
    return;
  }

  const now = new Date();
  const limit = await get(admin, '/organization/spend_limit');
  const { data: alerts = [] } = await get(admin, '/organization/spend_alerts', { limit: 100 });
  const spent = await monthToDate(admin, now);

  let scopes = 1;
  let bad = report('organization', limit, alerts, spent, now);

  const { data: users = [] } = await get(admin, '/organization/users', { limit: 100 });
  const stale = unknownRecipients(alerts, users.map((u) => u.email));
  if (stale.length > 0) {
    bad += 1;
    console.warn(`${'stale-recipient'.padEnd(16)} ${'organization'.padEnd(24)} ` +
                 `alert recipients not in the organization: ${stale.join(', ')}`);
  }

  if (process.argv.includes('--projects')) {
    const { data: projects = [] } = await get(admin, '/organization/projects', { limit: 25 });
    for (const p of projects) {
      if (!p.id || (p.status ?? 'active') !== 'active') continue;
      scopes += 1;
      const plimit = await get(admin, `/organization/projects/${p.id}/spend_limit`);
      const { data: palerts = [] } = await get(
        admin, `/organization/projects/${p.id}/spend_alerts`, { limit: 100 });
      const pspent = await monthToDate(admin, now, p.id);
      bad += report(p.name ?? p.id, plimit, palerts, pspent, now);
    }
  }

  console.log(`${scopes} scope(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two rules earn their tests here. The cents conversion, because a threshold read as dollars is the difference between a $900 ceiling and a $9 one, and the only place that shows up is arithmetic. And the ordering of the states: a limit that exists but is not enforcing has to be reported before any comparison against spend, because comparing an inactive limit to a run rate produces a confident sentence about a brake that is not connected to anything. The month projection is exercised at a fixed clock so the first of the month and the twenty-eighth are both pinned.",
"test_py_file": "test_openai_spend_limit_audit.py",
"test_py": '''import datetime as dt

from openai_spend_limit_audit import (projected_month_end, threshold_dollars,
                                      unknown_recipients, verdict)

# The 15th of a 31-day month, so a little under half of it has elapsed.
NOW = dt.datetime(2026, 8, 15, 12, 0, tzinfo=dt.timezone.utc)


def limit_of(cents, status="enforcing"):
    return {"object": "organization.spend_limit", "threshold_amount": cents,
            "currency": "USD", "interval": "month",
            "enforcement": {"status": status}}


def alert(cents, recipients=("oncall@example.com",)):
    return {"object": "organization.spend_alert", "threshold_amount": cents,
            "notification_channel": {"type": "email",
                                     "recipients": list(recipients)}}


def test_threshold_is_cents_not_dollars():
    assert threshold_dollars(limit_of(90000)) == 900.0
    assert threshold_dollars({"spend_limit": limit_of(50000)}) == 500.0
    assert threshold_dollars({}) is None
    assert threshold_dollars(None) is None
    assert threshold_dollars(limit_of("not a number")) is None


def test_projection_pro_rates_against_the_clock_it_is_given():
    # 14.5 days of a 31 day month have elapsed, so spend roughly doubles.
    assert round(projected_month_end(1000.0, NOW)) == 2138
    # The first hour of the month must not divide by zero or project infinity.
    first = dt.datetime(2026, 8, 1, 0, 0, tzinfo=dt.timezone.utc)
    assert round(projected_month_end(10.0, first)) == 10 * 31 * 24


def test_no_limit_at_all_is_the_headline_finding():
    state, detail = verdict({}, [], 400.0, NOW)
    assert state == "no-limit"
    assert "no spend limit is configured" in detail


def test_a_limit_that_is_not_enforcing_is_reported_before_any_arithmetic():
    # An inactive limit has the same effect on the bill as no limit, and
    # comparing it against the run rate would describe a brake that is not
    # connected to anything.
    state, _ = verdict(limit_of(90000, status="inactive"), [alert(45000)], 400.0, NOW)
    assert state == "not-enforcing"


def test_a_threshold_typed_as_dollars_is_named_as_the_cents_mistake():
    # 500 meaning five hundred dollars is five dollars.
    state, detail = verdict(limit_of(500), [alert(250)], 400.0, NOW)
    assert state == "cents-mistake"
    assert "in cents" in detail


def test_already_over_and_on_track_to_go_over_are_different_states():
    assert verdict(limit_of(30000), [alert(15000)], 400.0, NOW)[0] == "breached"
    assert verdict(limit_of(70000), [alert(35000)], 400.0, NOW)[0] == "will-breach"


def test_a_ceiling_far_above_the_run_rate_cannot_fire_in_time():
    state, detail = verdict(limit_of(5000000), [alert(2500000)], 400.0, NOW)
    assert state == "ceiling-too-high"
    assert "five times" in detail


def test_a_brake_with_no_warning_light_is_its_own_finding():
    state, detail = verdict(limit_of(200000), [], 400.0, NOW)
    assert state == "no-alerts"
    assert "429" in detail


def test_a_limit_and_alerts_together_is_guarded():
    state, detail = verdict(limit_of(200000), [alert(100000), alert(150000)],
                            400.0, NOW)
    assert state == "guarded"
    assert "2 alert(s)" in detail


def test_recipients_who_left_are_not_an_alert():
    alerts = [alert(1000, ("oncall@example.com", "Departed@Example.com")),
              alert(2000, ("oncall@example.com",))]
    assert unknown_recipients(alerts, ["OnCall@example.com"]) == ["Departed@Example.com"]
    assert unknown_recipients(alerts, ["oncall@example.com", "departed@example.com"]) == []
''',
"test_js_file": "openai-spend-limit-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { projectedMonthEnd, thresholdDollars, unknownRecipients, verdict }
  from './openai-spend-limit-audit.mjs';

// The 15th of a 31-day month, so a little under half of it has elapsed.
const NOW = new Date('2026-08-15T12:00:00Z');

const limitOf = (cents, status = 'enforcing') => ({
  object: 'organization.spend_limit', threshold_amount: cents, currency: 'USD',
  interval: 'month', enforcement: { status },
});

const alert = (cents, recipients = ['oncall@example.com']) => ({
  object: 'organization.spend_alert', threshold_amount: cents,
  notification_channel: { type: 'email', recipients },
});

test('threshold is cents, not dollars', () => {
  assert.equal(thresholdDollars(limitOf(90000)), 900);
  assert.equal(thresholdDollars({ spend_limit: limitOf(50000) }), 500);
  assert.equal(thresholdDollars({}), null);
  assert.equal(thresholdDollars(null), null);
  assert.equal(thresholdDollars(limitOf('not a number')), null);
});

test('projection pro-rates against the clock it is given', () => {
  assert.equal(Math.round(projectedMonthEnd(1000, NOW)), 2138);
  const first = new Date('2026-08-01T00:00:00Z');
  assert.equal(Math.round(projectedMonthEnd(10, first)), 10 * 31 * 24);
});

test('no limit at all is the headline finding', () => {
  const [state, detail] = verdict({}, [], 400, NOW);
  assert.equal(state, 'no-limit');
  assert.match(detail, /no spend limit is configured/);
});

test('a limit that is not enforcing is reported before any arithmetic', () => {
  const [state] = verdict(limitOf(90000, 'inactive'), [alert(45000)], 400, NOW);
  assert.equal(state, 'not-enforcing');
});

test('a threshold typed as dollars is named as the cents mistake', () => {
  const [state, detail] = verdict(limitOf(500), [alert(250)], 400, NOW);
  assert.equal(state, 'cents-mistake');
  assert.match(detail, /in cents/);
});

test('already over and on track to go over are different states', () => {
  assert.equal(verdict(limitOf(30000), [alert(15000)], 400, NOW)[0], 'breached');
  assert.equal(verdict(limitOf(70000), [alert(35000)], 400, NOW)[0], 'will-breach');
});

test('a ceiling far above the run rate cannot fire in time', () => {
  const [state, detail] = verdict(limitOf(5000000), [alert(2500000)], 400, NOW);
  assert.equal(state, 'ceiling-too-high');
  assert.match(detail, /five times/);
});

test('a brake with no warning light is its own finding', () => {
  const [state, detail] = verdict(limitOf(200000), [], 400, NOW);
  assert.equal(state, 'no-alerts');
  assert.match(detail, /429/);
});

test('a limit and alerts together is guarded', () => {
  const [state, detail] = verdict(limitOf(200000), [alert(100000), alert(150000)],
    400, NOW);
  assert.equal(state, 'guarded');
  assert.match(detail, /2 alert\\(s\\)/);
});

test('recipients who left are not an alert', () => {
  const alerts = [alert(1000, ['oncall@example.com', 'Departed@Example.com']),
    alert(2000, ['oncall@example.com'])];
  assert.deepEqual(unknownRecipients(alerts, ['OnCall@example.com']),
    ['Departed@Example.com']);
  assert.deepEqual(
    unknownRecipients(alerts, ['oncall@example.com', 'departed@example.com']), []);
});
''',
"faq": [
 ("Is the budget number in the OpenAI console the same as a spend limit?",
  "No. The console shows the cost report, which is a chart of what you have already spent. The thing that refuses requests is the organization.spend_limit object, read at GET /v1/organization/spend_limit, and it has its own enforcement.status. A threshold can be set with that status inactive, which looks configured and behaves as absent."),
 ("Why does my limit read as a strange number?",
  "Because threshold_amount is in cents. 90000 is $900. If somebody typed 500 meaning five hundred dollars, the limit is $5 and production will stop almost immediately, which is the single most common mistake with this endpoint."),
 ("Do spend alerts come with the limit?",
  "No, they are separate objects on a separate endpoint and are configured independently. An org can have alerts and no limit, which warns but does not stop, or a limit and no alerts, which stops with no warning. Read both before concluding anything."),
 ("What happens to my application when the limit is reached?",
  "Requests start returning 429 with code organization_spend_limit_exceeded, or project_spend_limit_exceeded for a project cap. That is a controlled outage you chose over an unbounded invoice, but only if your retry logic branches on the code rather than the status, or it will sit there retrying a wall."),
 ("Does Anthropic have an equivalent endpoint?",
  "Not for reading or setting a ceiling. The Claude Admin API exposes GET /v1/organizations/cost_report and the messages usage report, so you can see spend, but there is no spend-limit object to audit. On that side the honest finding is that no API-visible brake exists."),
],
"related": [
 ("/llm/quota-exhausted-not-rate-limited/", "A 429 that is a wall, not a throttle"),
 ("/llm/output-tokens-dominate-cost/", "Output tokens are what the bill is made of"),
 ("/llm/reasoning-tokens-billed-invisibly/", "Reasoning tokens billed but never returned"),
],
"citations": [CITE_ADMIN, CITE_COSTS, CITE_PROJECTS, CITE_CL_COST],
},


{
"slug": "reasoning-tokens-billed-invisibly",
"title": "Reasoning tokens are billed as output but never returned",
"description": "Cost per request jumps after a model switch while the visible answers stay the same length. The reasoning tokens are billed as output and never returned.",
"h1": "reasoning tokens are billed as output but never returned",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai reasoning tokens cost", "reasoning_tokens billed as output",
             "output_tokens_details reasoning_tokens", "reasoning effort cost",
             "why did my openai bill triple"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody changed one model constant. The answers coming back are the same length as before, the prompts are the same length as before, the request count is flat &mdash; and the line for that model on the cost report went up by a factor of four. The tokens you are paying for were generated, billed at the output rate, and then not returned to you.",
"short_answer": """<p>Read <code>GET /v1/organization/usage/completions?start_time={T-30d}&amp;bucket_width=1d&amp;group_by[]=model</code> with an admin key and compute <code>output_tokens / num_model_requests</code> per model per day. A step change in that ratio, with <code>input_tokens / num_model_requests</code> flat across the same boundary, is reasoning tokens and nothing else. If both moved, your prompts grew; if requests moved and the ratios did not, you simply sent more traffic.</p>
<p>The tokens themselves are never in a response body, so no read call will ever show them to you directly. What you can see is their weight in the aggregate.</p>""",
"problem": """<p>Reasoning tokens are generated, priced at the output rate, and consume the context window, but they are not returned in the API response. The visible answer is the tip; the bill is the iceberg. A team costing a migration by measuring the length of the text they actually receive will underestimate by the entire reasoning fraction, which on a deliberation-heavy task is most of it.</p>
<p>Because nothing errors and nothing looks different, the discovery is almost always the invoice. And by then the change that caused it is weeks back in the history &mdash; a model constant bumped, an <code>effort</code> raised from <code>low</code> to <code>high</code>, or a move to a model where deliberation is on by default and omitting the parameter no longer means off.</p>""",
"why": """<p><strong>The number is real and it is invisible.</strong> <code>usage.output_tokens</code> in a response includes the reasoning tokens; <code>usage.output_tokens_details.reasoning_tokens</code> tells you how many of them there were. If your metrics count the characters you received instead of reading that block, your own dashboards disagree with the invoice by design.</p>
<p><strong>One flag can multiply the bill.</strong> Reasoning effort is a parameter, and the higher settings do more model work for the same request. No error, no warning, no change to the shape of the response. A single line in a config file is enough.</p>
<p><strong>Prompts and parameters are not readable.</strong> Nothing in either API returns what you sent, so a script cannot look at your <code>reasoning</code> setting and tell you it is too high. It can only look at what the setting cost. That is why the detection here is a ratio over aggregate buckets rather than a configuration check.</p>
<p><strong>Anthropic's usage report has no request count.</strong> <code>GET /v1/organizations/usage_report/messages</code> returns token sums per bucket and nothing else, so a per-request ratio is not computable there. The fallback is output tokens per input token, which is a weaker signal because it also moves when prompts change &mdash; and the script should say which of the two it used rather than quietly presenting them as the same measurement.</p>""",
"steps": [
 {"h": "Pull daily buckets grouped by model",
  "body": """<p>Admin key. <code>GET /v1/organization/usage/completions?start_time={T-30d}&amp;bucket_width=1d&amp;group_by[]=model&amp;group_by[]=project_id</code>. Group by model or the step change disappears into an average: a cheap model absorbing most of the traffic will hide a fourfold jump on the expensive one completely.</p>"""},
 {"h": "Compute the ratios per bucket, not per month",
  "body": """<p><code>output_tokens / num_model_requests</code> and <code>input_tokens / num_model_requests</code>. Buckets with zero requests have no ratio and must be dropped rather than treated as zero; averaging a zero in is how a quiet weekend becomes a fictional improvement.</p>"""},
 {"h": "Compare a recent window against a prior one",
  "body": """<p>Split the series in two &mdash; the last seven days against the seven before, or whatever bracket a deploy fell in &mdash; and compare the means. What you want is a factor, not a p-value: output per request up by half again or more, with input per request within twenty percent of where it was.</p>"""},
 {"h": "Rule out the two innocent explanations first",
  "body": """<p>If input per request rose by a similar factor, the prompts grew and reasoning is not the story. If the request count rose and both ratios held, you sent more traffic and the unit economics are unchanged. Both are ordinary and both look like a cost spike on a chart with no denominator.</p>"""},
 {"h": "Print the repair; do not send it",
  "body": """<p>Lower reasoning effort where the task does not need deliberation, and drop the higher modes unless an eval justifies the premium. Then log <code>usage.output_tokens_details.reasoning_tokens</code> per call, so the invisible half is visible in your own metrics next time instead of on an invoice. Cross-check the money with <code>GET /v1/organization/costs?group_by[]=line_item</code>.</p>"""},
],
"verify": """<p>Re-run a week after the effort change. The output-per-request ratio should return toward its prior level with input per request unmoved.</p>
<pre><code class="language-bash">python3 openai_reasoning_token_audit.py --days 30 --window 7
# gpt-5.6           steady  1,180 output/request, 940 input/request
# 2 model(s) over 30 day(s), 0 finding(s)</code></pre>""",
"code_intro": "Two GETs against <code>/v1/organization/*</code>, so <code>OPENAI_ADMIN_KEY</code> has to be an organization admin key. All three judgement calls are pure functions: the summing, the split of the series into a prior and a recent window against a clock you pass in, and the verdict that decides which of the four explanations for a cost jump the numbers actually support.",
"py_file": "openai_reasoning_token_audit.py",
"py": '''"""Find the cost jump that is reasoning tokens rather than traffic or prompts.

Read only. Two GET requests and nothing else: OPENAI_ADMIN_KEY must be an
organization admin key (sk-admin-...) with read scopes, because /v1/organization
endpoints reject project keys. The repair is printed, never performed, because
this script holds a credential that can spend money on inference.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_reasoning_token_audit")

API = "https://api.openai.com/v1"


def totals(buckets):
    """Sum a list of usage buckets into one row. Pure.

    OpenAI's completions usage carries num_model_requests; Anthropic's messages
    usage report does not carry any request count at all, so a caller working
    against that side gets requests == 0 here and the verdict falls back to a
    weaker ratio rather than dividing by nothing.
    """
    row = {"requests": 0, "input": 0, "output": 0, "buckets": 0}
    for b in buckets:
        row["buckets"] += 1
        for r in b.get("results", []) or []:
            row["requests"] += int(r.get("num_model_requests") or 0)
            row["input"] += int(r.get("input_tokens")
                                or r.get("uncached_input_tokens") or 0)
            row["output"] += int(r.get("output_tokens") or 0)
    return row


def split(buckets, now, window_days=7):
    """Cut a daily series into (prior, recent) around a boundary. Pure, clock
    passed in, so the boundary in a test is a date you can read rather than a
    function of when the suite happened to run.

    Buckets older than twice the window are dropped: comparing last week against
    a quarter ago answers a different question than the one being asked.
    """
    edge = now.timestamp() - window_days * 86400
    floor = now.timestamp() - 2 * window_days * 86400
    prior, recent = [], []
    for b in buckets:
        start = b.get("start_time")
        if not isinstance(start, (int, float)):
            continue
        if start >= edge:
            recent.append(b)
        elif start >= floor:
            prior.append(b)
    return prior, recent


def verdict(prior, recent, jump=1.5, flat=0.2):
    """Say which of the four explanations for a cost jump the numbers support.

    Pure. `jump` is the factor that counts as a step change; `flat` is how far
    the other ratio may move and still be called unchanged.

    Returns (state, detail).
    """
    a, b = totals(prior), totals(recent)

    if not b["requests"] and not b["output"]:
        return ("no-data", "no usage in the recent window")

    if b["requests"] and not b["output"]:
        return ("failing-before-generation",
                "%d request(s) in the recent window generated zero output "
                "tokens. Those calls were rejected before the model ran; that "
                "is an error shape and not a reasoning one." % b["requests"])

    if not a["requests"] or not b["requests"]:
        # Anthropic's usage report has no request count, so this is the honest
        # fallback rather than a per-request claim that cannot be made.
        if a["input"] and b["input"]:
            before = a["output"] / a["input"]
            after = b["output"] / b["input"]
            if before and after / before >= jump:
                return ("unmeasurable-but-rising",
                        "no request count in these buckets, so this is output "
                        "per input token, not per request: %.2f to %.2f. "
                        "Consistent with reasoning, but prompt shrinkage looks "
                        "identical." % (before, after))
            return ("unmeasurable",
                    "no request count in these buckets. Output per input token "
                    "is %.2f against %.2f before, which is the strongest claim "
                    "available without a request count." % (after, before))
        return ("unmeasurable",
                "no request count and no input tokens to fall back on")

    in_before = a["input"] / a["requests"]
    in_after = b["input"] / b["requests"]
    out_before = a["output"] / a["requests"]
    out_after = b["output"] / b["requests"]
    numbers = ("%.0f to %.0f output tokens per request, %.0f to %.0f input"
               % (out_before, out_after, in_before, in_after))

    out_factor = (out_after / out_before) if out_before else 0.0
    in_factor = (in_after / in_before) if in_before else 0.0

    if out_factor >= jump and abs(in_factor - 1.0) <= flat:
        return ("reasoning-tax",
                "%s. Output per request rose %.1fx while input per request held "
                "steady. Those tokens were generated and billed at the output "
                "rate and never returned to you." % (numbers, out_factor))

    if out_factor >= jump and in_factor >= jump:
        return ("longer-prompts",
                "%s. Both ratios rose together, so the prompts grew. Raising "
                "reasoning effort does not move the input side."
                % numbers)

    if b["requests"] >= a["requests"] * jump:
        return ("volume-only",
                "%s. Requests rose from %d to %d with the ratios unchanged: the "
                "bill grew because traffic grew, and unit economics did not "
                "move." % (numbers, a["requests"], b["requests"]))

    return ("steady", numbers)


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization endpoints need an "
                         "organization admin key, not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def usage_by_model(session, since, days):
    """Read daily completion usage grouped by model, following next_page."""
    params = [("start_time", int(since.timestamp())), ("bucket_width", "1d"),
              ("limit", max(days, 1)), ("group_by[]", "model")]
    out = {}
    while True:
        page = get(session, "/organization/usage/completions", params)
        for b in page.get("data", []):
            for r in b.get("results", []) or []:
                model = r.get("model") or "unspecified"
                out.setdefault(model, []).append(
                    {"start_time": b.get("start_time"), "results": [r]})
        if not page.get("has_more") or not page.get("next_page"):
            break
        params = [p for p in params if p[0] != "page"] + [("page", page["next_page"])]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read daily usage buckets")
    ap.add_argument("--window", type=int, default=7,
                    help="days in the recent window, compared against the days before it")
    ap.add_argument("--jump", type=float, default=1.5,
                    help="factor that counts as a step change")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key with read "
                  "scopes; project keys are rejected by /v1/organization/*)")
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})

    since = now - dt.timedelta(days=args.days)
    by_model = usage_by_model(s, since, args.days)
    if not by_model:
        log.info("no completion usage in the last %d day(s)", args.days)
        return 0

    bad = 0
    for model, buckets in sorted(by_model.items()):
        prior, recent = split(buckets, now, args.window)
        state, detail = verdict(prior, recent, args.jump)
        line = "%-22s %-26s %s" % (model, state, detail)
        if state in ("steady", "volume-only", "no-data", "unmeasurable"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("reasoning-tax", "unmeasurable-but-rising"):
            log.warning("  repair: lower the reasoning effort on this model for "
                        "tasks that do not need deliberation, and drop the "
                        "higher modes unless an eval justifies them. Log "
                        "usage.output_tokens_details.reasoning_tokens per call "
                        "so the invisible half shows up in your own metrics.")
            log.warning("  cross-check the money: GET %s/organization/costs"
                        "?start_time=%d&bucket_width=1d&group_by[]=line_item",
                        API, int(since.timestamp()))

    log.info("%d model(s) over %d day(s), %d finding(s)",
             len(by_model), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-reasoning-token-audit.mjs",
"js": '''/**
 * Find the cost jump that is reasoning tokens rather than traffic or prompts.
 *
 * Read only. Two GET requests and nothing else: OPENAI_ADMIN_KEY must be an
 * organization admin key with read scopes, because /v1/organization endpoints
 * reject project keys. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

/**
 * Sum a list of usage buckets into one row. Pure. Anthropic's messages usage
 * report carries no request count, so requests comes back 0 there and the
 * verdict falls back to a weaker ratio rather than dividing by nothing.
 */
export function totals(buckets) {
  const row = { requests: 0, input: 0, output: 0, buckets: 0 };
  for (const b of buckets) {
    row.buckets += 1;
    for (const r of b.results ?? []) {
      row.requests += Number(r.num_model_requests ?? 0);
      row.input += Number(r.input_tokens ?? r.uncached_input_tokens ?? 0);
      row.output += Number(r.output_tokens ?? 0);
    }
  }
  return row;
}

/**
 * Cut a daily series into [prior, recent] around a boundary. Pure, clock passed
 * in, so a test's boundary is a date you can read. Buckets older than twice the
 * window are dropped: last week against a quarter ago is a different question.
 */
export function split(buckets, now, windowDays = 7) {
  const edge = now.getTime() / 1000 - windowDays * 86400;
  const floor = now.getTime() / 1000 - 2 * windowDays * 86400;
  const prior = [];
  const recent = [];
  for (const b of buckets) {
    if (typeof b.start_time !== 'number') continue;
    if (b.start_time >= edge) recent.push(b);
    else if (b.start_time >= floor) prior.push(b);
  }
  return [prior, recent];
}

/**
 * Say which of the four explanations for a cost jump the numbers support. Pure.
 * Returns [state, detail].
 */
export function verdict(prior, recent, jump = 1.5, flat = 0.2) {
  const a = totals(prior);
  const b = totals(recent);

  if (!b.requests && !b.output) return ['no-data', 'no usage in the recent window'];

  if (b.requests && !b.output) {
    return ['failing-before-generation',
      `${b.requests} request(s) in the recent window generated zero output ` +
      'tokens. Those calls were rejected before the model ran; that is an error ' +
      'shape and not a reasoning one.'];
  }

  if (!a.requests || !b.requests) {
    if (a.input && b.input) {
      const before = a.output / a.input;
      const after = b.output / b.input;
      if (before && after / before >= jump) {
        return ['unmeasurable-but-rising',
          'no request count in these buckets, so this is output per input token, ' +
          `not per request: ${before.toFixed(2)} to ${after.toFixed(2)}. ` +
          'Consistent with reasoning, but prompt shrinkage looks identical.'];
      }
      return ['unmeasurable',
        `no request count in these buckets. Output per input token is ` +
        `${after.toFixed(2)} against ${before.toFixed(2)} before, which is the ` +
        'strongest claim available without a request count.'];
    }
    return ['unmeasurable', 'no request count and no input tokens to fall back on'];
  }

  const inBefore = a.input / a.requests;
  const inAfter = b.input / b.requests;
  const outBefore = a.output / a.requests;
  const outAfter = b.output / b.requests;
  const numbers = `${outBefore.toFixed(0)} to ${outAfter.toFixed(0)} output ` +
    `tokens per request, ${inBefore.toFixed(0)} to ${inAfter.toFixed(0)} input`;

  const outFactor = outBefore ? outAfter / outBefore : 0;
  const inFactor = inBefore ? inAfter / inBefore : 0;

  if (outFactor >= jump && Math.abs(inFactor - 1) <= flat) {
    return ['reasoning-tax',
      `${numbers}. Output per request rose ${outFactor.toFixed(1)}x while input ` +
      'per request held steady. Those tokens were generated and billed at the ' +
      'output rate and never returned to you.'];
  }

  if (outFactor >= jump && inFactor >= jump) {
    return ['longer-prompts',
      `${numbers}. Both ratios rose together, so the prompts grew. Raising ` +
      'reasoning effort does not move the input side.'];
  }

  if (b.requests >= a.requests * jump) {
    return ['volume-only',
      `${numbers}. Requests rose from ${a.requests} to ${b.requests} with the ` +
      'ratios unchanged: the bill grew because traffic grew, and unit economics ' +
      'did not move.'];
  }

  return ['steady', numbers];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of params) url.searchParams.append(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization endpoints need ` +
                    'an organization admin key, not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function usageByModel(key, since, days) {
  let params = [['start_time', String(since)], ['bucket_width', '1d'],
    ['limit', String(Math.max(days, 1))], ['group_by[]', 'model']];
  const out = new Map();
  for (;;) {
    const page = await get(key, '/organization/usage/completions', params);
    for (const b of page.data ?? []) {
      for (const r of b.results ?? []) {
        const model = r.model ?? 'unspecified';
        if (!out.has(model)) out.set(model, []);
        out.get(model).push({ start_time: b.start_time, results: [r] });
      }
    }
    if (!page.has_more || !page.next_page) break;
    params = params.filter((p) => p[0] !== 'page').concat([['page', page.next_page]]);
  }
  return out;
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key with read ' +
                  'scopes; project keys are rejected by /v1/organization/*)');
    process.exitCode = 2;
    return;
  }

  const argv = process.argv;
  const days = Number(argv.includes('--days') ? argv[argv.indexOf('--days') + 1] : 30) || 30;
  const win = Number(argv.includes('--window') ? argv[argv.indexOf('--window') + 1] : 7) || 7;

  const now = new Date();
  const since = Math.floor(now.getTime() / 1000 - days * 86400);
  const byModel = await usageByModel(admin, since, days);
  if (byModel.size === 0) {
    console.log(`no completion usage in the last ${days} day(s)`);
    return;
  }

  let bad = 0;
  for (const [model, buckets] of [...byModel.entries()].sort()) {
    const [prior, recent] = split(buckets, now, win);
    const [state, detail] = verdict(prior, recent);
    const line = `${model.padEnd(22)} ${state.padEnd(26)} ${detail}`;
    if (['steady', 'volume-only', 'no-data', 'unmeasurable'].includes(state)) {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (state === 'reasoning-tax' || state === 'unmeasurable-but-rising') {
      console.warn('  repair: lower the reasoning effort on this model for tasks ' +
                   'that do not need deliberation, and drop the higher modes ' +
                   'unless an eval justifies them. Log ' +
                   'usage.output_tokens_details.reasoning_tokens per call so the ' +
                   'invisible half shows up in your own metrics.');
      console.warn(`  cross-check the money: GET ${API}/organization/costs` +
                   `?start_time=${since}&bucket_width=1d&group_by[]=line_item`);
    }
  }

  console.log(`${byModel.size} model(s) over ${days} day(s), ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The interesting tests are the ones that refuse to cry wolf. Output per request tripling <em>with</em> input per request tripling is longer prompts, not reasoning, and has to come back as a different state. Traffic doubling at constant ratios is not a finding at all. And a series with no request count &mdash; which is every Anthropic bucket &mdash; must degrade to an explicitly weaker claim rather than dividing by zero or pretending it measured something it did not.",
"test_py_file": "test_openai_reasoning_token_audit.py",
"test_py": '''import datetime as dt

from openai_reasoning_token_audit import split, totals, verdict

NOW = dt.datetime(2026, 8, 30, 0, 0, tzinfo=dt.timezone.utc)


def days_ago(d):
    return int(NOW.timestamp() - d * 86400)


def day(d, requests=100, inp=90000, out=100000, model="gpt-5.6"):
    return {"start_time": days_ago(d),
            "results": [{"model": model, "num_model_requests": requests,
                         "input_tokens": inp, "output_tokens": out}]}


def anthropic_day(d, inp=90000, out=100000):
    """No num_model_requests: that field does not exist on Anthropic's report."""
    return {"start_time": days_ago(d),
            "results": [{"uncached_input_tokens": inp, "output_tokens": out}]}


def test_totals_sums_and_tolerates_a_missing_request_count():
    assert totals([day(1), day(2)]) == {"requests": 200, "input": 180000,
                                        "output": 200000, "buckets": 2}
    assert totals([anthropic_day(1)])["requests"] == 0


def test_split_cuts_the_series_at_the_clock_it_is_given():
    prior, recent = split([day(1), day(3), day(9), day(30)], NOW, 7)
    assert [b["start_time"] for b in recent] == [days_ago(1), days_ago(3)]
    assert [b["start_time"] for b in prior] == [days_ago(9)]
    # 30 days back is outside twice the window and is dropped, not compared.


def test_the_finding_output_per_request_rises_while_input_holds():
    prior = [day(9, requests=100, inp=90000, out=100000)]
    recent = [day(1, requests=100, inp=91000, out=400000)]
    state, detail = verdict(prior, recent)
    assert state == "reasoning-tax"
    assert "4.0x" in detail
    assert "never returned" in detail


def test_prompts_growing_is_not_the_same_finding():
    prior = [day(9, requests=100, inp=90000, out=100000)]
    recent = [day(1, requests=100, inp=360000, out=400000)]
    assert verdict(prior, recent)[0] == "longer-prompts"


def test_more_traffic_at_the_same_ratios_is_not_a_finding_at_all():
    prior = [day(9, requests=100, inp=90000, out=100000)]
    recent = [day(1, requests=400, inp=360000, out=400000)]
    state, detail = verdict(prior, recent)
    assert state == "volume-only"
    assert "unit economics" in detail


def test_flat_ratios_and_flat_traffic_are_steady():
    prior = [day(9, requests=100, inp=90000, out=100000)]
    recent = [day(1, requests=110, inp=99000, out=110000)]
    assert verdict(prior, recent)[0] == "steady"


def test_no_request_count_degrades_to_a_weaker_claim_and_says_so():
    prior = [anthropic_day(9, inp=90000, out=100000)]
    recent = [anthropic_day(1, inp=90000, out=400000)]
    state, detail = verdict(prior, recent)
    assert state == "unmeasurable-but-rising"
    assert "per input token, not per request" in detail
    assert verdict([anthropic_day(9)], [anthropic_day(1)])[0] == "unmeasurable"


def test_requests_with_no_output_is_an_error_shape_not_a_reasoning_one():
    prior = [day(9)]
    recent = [day(1, requests=50, inp=45000, out=0)]
    state, _ = verdict(prior, recent)
    assert state == "failing-before-generation"


def test_an_empty_recent_window_claims_nothing():
    assert verdict([day(9)], [])[0] == "no-data"
''',
"test_js_file": "openai-reasoning-token-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { split, totals, verdict } from './openai-reasoning-token-audit.mjs';

const NOW = new Date('2026-08-30T00:00:00Z');
const daysAgo = (d) => Math.floor(NOW.getTime() / 1000 - d * 86400);

const day = (d, requests = 100, inp = 90000, out = 100000, model = 'gpt-5.6') => ({
  start_time: daysAgo(d),
  results: [{ model, num_model_requests: requests, input_tokens: inp, output_tokens: out }],
});

// No num_model_requests: that field does not exist on Anthropic's report.
const anthropicDay = (d, inp = 90000, out = 100000) => ({
  start_time: daysAgo(d),
  results: [{ uncached_input_tokens: inp, output_tokens: out }],
});

test('totals sums and tolerates a missing request count', () => {
  assert.deepEqual(totals([day(1), day(2)]),
    { requests: 200, input: 180000, output: 200000, buckets: 2 });
  assert.equal(totals([anthropicDay(1)]).requests, 0);
});

test('split cuts the series at the clock it is given', () => {
  const [prior, recent] = split([day(1), day(3), day(9), day(30)], NOW, 7);
  assert.deepEqual(recent.map((b) => b.start_time), [daysAgo(1), daysAgo(3)]);
  assert.deepEqual(prior.map((b) => b.start_time), [daysAgo(9)]);
});

test('the finding: output per request rises while input holds', () => {
  const [state, detail] = verdict([day(9, 100, 90000, 100000)],
    [day(1, 100, 91000, 400000)]);
  assert.equal(state, 'reasoning-tax');
  assert.match(detail, /4\\.0x/);
  assert.match(detail, /never returned/);
});

test('prompts growing is not the same finding', () => {
  assert.equal(verdict([day(9, 100, 90000, 100000)],
    [day(1, 100, 360000, 400000)])[0], 'longer-prompts');
});

test('more traffic at the same ratios is not a finding at all', () => {
  const [state, detail] = verdict([day(9, 100, 90000, 100000)],
    [day(1, 400, 360000, 400000)]);
  assert.equal(state, 'volume-only');
  assert.match(detail, /unit economics/);
});

test('flat ratios and flat traffic are steady', () => {
  assert.equal(verdict([day(9, 100, 90000, 100000)],
    [day(1, 110, 99000, 110000)])[0], 'steady');
});

test('no request count degrades to a weaker claim and says so', () => {
  const [state, detail] = verdict([anthropicDay(9, 90000, 100000)],
    [anthropicDay(1, 90000, 400000)]);
  assert.equal(state, 'unmeasurable-but-rising');
  assert.match(detail, /per input token, not per request/);
  assert.equal(verdict([anthropicDay(9)], [anthropicDay(1)])[0], 'unmeasurable');
});

test('requests with no output is an error shape, not a reasoning one', () => {
  assert.equal(verdict([day(9)], [day(1, 50, 45000, 0)])[0],
    'failing-before-generation');
});

test('an empty recent window claims nothing', () => {
  assert.equal(verdict([day(9)], [])[0], 'no-data');
});
''',
"faq": [
 ("Can I see reasoning tokens in a response?",
  "You can see how many there were, not what they said. usage.output_tokens_details.reasoning_tokens carries the count, and usage.output_tokens already includes them. The content is never returned. If your own cost metric counts the characters you received, it will disagree with the invoice by exactly that number."),
 ("Why does the script compare ratios instead of totals?",
  "Because a total tells you the bill went up and nothing about why. Output tokens per request, against input tokens per request, separates the three ordinary explanations: more traffic moves the request count, longer prompts move the input ratio, and reasoning moves the output ratio on its own."),
 ("Do reasoning tokens use my context window?",
  "Yes. They are generated, they occupy the window, and they are billed at the output rate. That is also why raising effort can start producing truncated answers on requests that used to fit comfortably: the deliberation is competing with the response for the same budget."),
 ("Can a read-only script tell me what reasoning effort I have configured?",
  "No. Neither API returns what you sent, so prompts, parameters and client configuration are invisible to any read call. The script can only measure what the setting cost, which is why the finding is a step change in a ratio rather than a configuration warning."),
 ("Does this work against Anthropic?",
  "Partly, and the script says so. The Claude messages usage report has no request-count field, so no per-request ratio can be computed there. The fallback is output tokens per input token, which also moves when prompts change, so it is reported as a weaker claim rather than presented as the same measurement."),
],
"related": [
 ("/llm/output-tokens-dominate-cost/", "Output tokens are what the bill is made of"),
 ("/llm/no-organization-spend-limit/", "No spend limit means no ceiling"),
 ("/llm/quota-exhausted-not-rate-limited/", "A 429 that is a wall, not a throttle"),
],
"citations": [CITE_REASONING, CITE_USAGE, CITE_ADMIN, CITE_CL_THINKING],
},


{
"slug": "output-tokens-dominate-cost",
"title": "Output tokens, not input, are what the bill is made of",
"description": "Output is priced at five times input on every current Claude model, and thinking tokens bill as output. The cost report says which side the bill sits on.",
"h1": "output tokens, not input, are what the bill is made of",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude output token cost", "anthropic cost report token_type",
             "output tokens 5x input", "anthropic prompt caching savings",
             "claude cost optimisation"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every conversation about LLM cost starts with the prompt. The system prompt gets trimmed, the few-shot examples get cut, someone measures the context window. Then you group the cost report by <code>token_type</code> and find that three-quarters of the money is on the other side of the request, where none of the levers you just pulled reach.",
"short_answer": """<p>Admin API key. <code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;limit=31&amp;group_by[]=description</code> and sum <code>amount</code> by <code>token_type</code>. Output is priced at five times input on every current model, and thinking tokens are billed as output tokens when they are generated, so the share tells you which lever is worth pulling.</p>
<p>The repairs are not interchangeable. An output-dominated bill responds to generating less &mdash; lower effort, tighter stop conditions, shorter formats. An input-dominated bill responds to prompt caching. Applying the wrong one produces a week of work and no change to the invoice.</p>""",
"problem": """<p>The five-times ratio is the whole shape of the bill and almost nobody has it in their head. Twenty thousand tokens of context and four thousand tokens of answer feels like a request that is mostly input. Priced at 5:1 it is a request that is half output, and if adaptive thinking is running it is a request that is mostly output.</p>
<p>What makes it stick is that the cheap fix has already been applied. Prompt caching is well known, easy to enable, and genuinely effective, so teams turn it on, watch the input line fall, and conclude the problem is solved. The output line was always the larger number and it has not moved, because <strong>there is no caching discount on output</strong>. There is no discount on output at all. The only lever is generating fewer tokens.</p>""",
"why": """<p><strong>Output costs five times input, per token, on every current model.</strong> That is a pricing fact, not a workload one, and it applies before anything about your traffic is considered. A request has to be five times more input-heavy than it looks before input is the bigger line.</p>
<p><strong>Thinking tokens are output tokens.</strong> They are billed at the output rate when generated. Raising effort, or moving to a model that runs adaptive thinking when the parameter is omitted rather than treating omission as off, shifts spend onto the expensive side with no code change visible in a diff.</p>
<p><strong>Caching moves only one line, and can move it the wrong way.</strong> Cache writes are billed at a premium over base input; cache reads are a fraction of it. Writes without enough reads to amortise them is a real state, and it looks like caching that is working right up until you compare the two numbers.</p>
<p><strong>The cost report is the only place the split is visible.</strong> A per-request breakdown does not exist on either API. What exists is aggregate money grouped by <code>token_type</code> and aggregate tokens grouped by model, and the argument you can make from them is about proportion rather than about any individual call.</p>""",
"steps": [
 {"h": "Group the cost report by description",
  "body": """<p><code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;limit=31&amp;group_by[]=description</code> with an Admin API key. Each result carries <code>amount</code>, <code>currency</code>, <code>token_type</code> and a <code>description</code>. <code>amount</code> comes back as a decimal string, not a number; parsing it as if it were a float that already exists is the quiet way to sum nothing.</p>"""},
 {"h": "Bucket the token types into four, not fifteen",
  "body": """<p>Input, output, cache read and cache write. New token type names appear as products ship &mdash; different cache durations, different tiers &mdash; so match on the shape of the name and put anything unrecognised in a visible "other" bucket rather than dropping it. A silently discarded token type is a share that adds up to less than a hundred percent and nobody notices.</p>"""},
 {"h": "Read the share, then pick the lever",
  "body": """<p>Output above roughly seventy percent of spend means generating less is the only thing that will help. Input above sixty percent means caching is worth the work. In between, both help and neither is dramatic. This is a decision, not a metric, and it is worth writing down which one the numbers actually support before anyone opens a pull request.</p>"""},
 {"h": "Name the model carrying it",
  "body": """<p><code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=model</code> gives <code>output_tokens</code> and <code>uncached_input_tokens</code> per model per day. The model with the largest output share is where an effort change has the most effect; a step up in its output tokens with no matching input rise is a thinking or effort change rather than more traffic.</p>"""},
 {"h": "Print the change, do not make it",
  "body": """<p>The suggestion is a lower effort setting on the model carrying the output spend, and a re-read of the same daily series a week later to see whether the share moved. Nothing here should be altering an inference setting from inside an audit script, and the Admin API cannot do it anyway.</p>"""},
],
"verify": """<p>Re-run a week after the effort change. The output share should fall and total spend with it.</p>
<pre><code class="language-bash">python3 anthropic_output_cost_audit.py --days 30
# balanced   $1,204.55 over 30 day(s): output 52%, input 31%, cache read 14%, cache write 3%
# top model by output tokens: claude-sonnet-5 (61% of output)
# 0 finding(s)</code></pre>""",
"code_intro": "Two GETs against the Claude Admin API, so <code>ANTHROPIC_ADMIN_KEY</code> has to be an Admin API key (<code>sk-ant-admin...</code>) &mdash; a workspace key is rejected by every <code>/v1/organizations/*</code> endpoint, and an Admin key cannot send a message even if it wanted to. The pure functions are the amount parser, which exists because the field is a string, the token-type bucketing, which has to survive names that do not exist yet, and the verdict that turns a share into a decision.",
"py_file": "anthropic_output_cost_audit.py",
"py": '''"""Report which side of a Claude request the bill is actually on.

Read only. Two GET requests and nothing else: ANTHROPIC_ADMIN_KEY must be an
Admin API key (sk-ant-admin...), because every /v1/organizations endpoint
rejects a workspace key. The repair is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_output_cost_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Output is priced at five times input on every current model, so a request has
# to be markedly input-heavy before input is the larger line.
OUTPUT_MULTIPLE = 5


def amount(row):
    """Read a cost row's amount as a float. Pure.

    The cost report returns amount as a decimal STRING, not a number. Summing
    the raw values concatenates them in one language and throws in the other,
    and the failure is silent enough to ship.
    """
    raw = row.get("amount")
    if raw is None or raw == "":
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def bucket_of(token_type):
    """Fold a token_type into one of five buckets. Pure.

    Matched on the shape of the name rather than an exact list, because new
    token types arrive with new cache durations and new tiers. Anything
    unrecognised lands in "other" and stays visible; a silently dropped type is
    a set of shares that quietly adds up to less than one.
    """
    name = str(token_type or "").lower()
    if not name:
        return "other"
    if "cache_creation" in name or "cache_write" in name:
        return "cache_write"
    if "cache_read" in name:
        return "cache_read"
    if "output" in name:
        return "output"
    if "input" in name:
        return "input"
    return "other"


def by_bucket(cost_buckets):
    """Sum spend per token bucket across the cost report. Pure."""
    out = {"input": 0.0, "output": 0.0, "cache_read": 0.0,
           "cache_write": 0.0, "other": 0.0}
    for b in cost_buckets:
        for r in b.get("results", []) or []:
            out[bucket_of(r.get("token_type"))] += amount(r)
    return out


def top_model(usage_buckets):
    """The model carrying the most output tokens, and its share. Pure.

    Returns (model, share) or (None, 0.0). Answers the only actionable question
    the usage report can answer here: where an effort change would land.
    """
    per_model = {}
    total = 0
    for b in usage_buckets:
        for r in b.get("results", []) or []:
            model = r.get("model") or "unspecified"
            out = int(r.get("output_tokens") or 0)
            per_model[model] = per_model.get(model, 0) + out
            total += out
    if not total:
        return (None, 0.0)
    model = max(per_model, key=lambda m: per_model[m])
    return (model, per_model[model] / total)


def verdict(buckets, min_spend=1.0):
    """Turn the spend split into the lever that will actually move it. Pure.

    Returns (state, detail). The states are not degrees of the same finding:
    each one names a different repair, and applying the wrong one costs a week
    and changes nothing on the invoice.
    """
    total = sum(buckets.values())
    if total < min_spend:
        return ("no-spend", "$%.2f over the window: nothing to act on" % total)

    def pct(key):
        return buckets[key] / total * 100

    split = ("output %.0f%%, input %.0f%%, cache read %.0f%%, cache write %.0f%%"
             % (pct("output"), pct("input"), pct("cache_read"), pct("cache_write")))
    if buckets["other"] > 0:
        split += ", unrecognised %.0f%%" % pct("other")
    money = "$%.2f over the window: %s" % (total, split)

    if buckets["cache_write"] > buckets["cache_read"] and pct("cache_write") >= 15:
        return ("cache-write-heavy",
                "%s. You are paying the cache write premium without the reads "
                "to amortise it: the prefix is being rewritten more often than "
                "it is hit." % money)

    if pct("output") >= 70:
        return ("output-dominated",
                "%s. Output is priced at %dx input and there is no caching "
                "discount on it, so the only lever is generating fewer tokens: "
                "lower effort, tighter stop conditions, shorter output formats."
                % (money, OUTPUT_MULTIPLE))

    if pct("input") + pct("cache_read") + pct("cache_write") >= 60:
        return ("input-dominated",
                "%s. This is the shape prompt caching is for. Cache the stable "
                "prefix and read it back; trimming output here buys very "
                "little." % money)

    if pct("output") >= 50:
        return ("output-led",
                "%s. Output is the larger half but not overwhelmingly. Both "
                "levers help and neither is dramatic on its own." % money)

    return ("balanced", money)


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations endpoints need an "
                         "Admin API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def read_all(session, path, params):
    """Follow next_page until the report is exhausted."""
    out = []
    while True:
        page = get(session, path, params)
        out.extend(page.get("data", []))
        if not page.get("has_more") or not page.get("next_page"):
            break
        params = [p for p in params if p[0] != "page"] + [("page", page["next_page"])]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read the cost and usage reports")
    ap.add_argument("--min-spend", type=float, default=1.0,
                    help="below this total, report nothing rather than a noisy share")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not key:
        log.error("set ANTHROPIC_ADMIN_KEY (an Admin API key, sk-ant-admin...; "
                  "workspace keys are rejected by /v1/organizations/*)")
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(days=args.days)).strftime("%Y-%m-%dT00:00:00Z")

    s = requests.Session()
    s.headers.update({"x-api-key": key, "anthropic-version": VERSION})

    costs = read_all(s, "/organizations/cost_report",
                     [("starting_at", since), ("limit", 31),
                      ("group_by[]", "description")])
    usage = read_all(s, "/organizations/usage_report/messages",
                     [("starting_at", since), ("bucket_width", "1d"),
                      ("limit", 31), ("group_by[]", "model")])

    split = by_bucket(costs)
    state, detail = verdict(split, args.min_spend)
    line = "%-18s %s" % (state, detail)

    bad = 0
    if state in ("no-spend", "balanced", "input-dominated"):
        log.info(line)
    else:
        bad = 1
        log.warning(line)

    model, share = top_model(usage)
    if model:
        log.info("top model by output tokens: %s (%.0f%% of output)",
                 model, share * 100)
        if bad:
            log.warning("  repair, to run yourself: lower output_config.effort on "
                        "%s (high to medium is the usual first step), then re-read "
                        "this same daily series a week later. Thinking tokens bill "
                        "as output, so effort is the setting that moves this share.",
                        model)
            log.warning("  never change an effort setting from inside an audit; "
                        "the Admin API cannot do it and neither should this.")
    else:
        log.info("no output tokens in the usage report for this window")

    log.info("%d cost bucket(s), %d usage bucket(s) over %d day(s), %d finding(s)",
             len(costs), len(usage), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-output-cost-audit.mjs",
"js": '''/**
 * Report which side of a Claude request the bill is actually on.
 *
 * Read only. Two GET requests and nothing else: ANTHROPIC_ADMIN_KEY must be an
 * Admin API key (sk-ant-admin...), because every /v1/organizations endpoint
 * rejects a workspace key. The repair is printed, never performed.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// Output is priced at five times input on every current model.
export const OUTPUT_MULTIPLE = 5;

/**
 * Read a cost row's amount as a number. Pure. The cost report returns amount as
 * a decimal STRING; adding the raw values concatenates them instead of summing.
 */
export function amount(row) {
  const raw = row.amount;
  if (raw === null || raw === undefined || raw === '') return 0;
  const n = Number(raw);
  return Number.isFinite(n) ? n : 0;
}

/**
 * Fold a token_type into one of five buckets. Pure. Matched on the shape of the
 * name, because new token types arrive with new cache durations and tiers;
 * anything unrecognised stays visible in "other" rather than being dropped.
 */
export function bucketOf(tokenType) {
  const name = String(tokenType ?? '').toLowerCase();
  if (!name) return 'other';
  if (name.includes('cache_creation') || name.includes('cache_write')) return 'cache_write';
  if (name.includes('cache_read')) return 'cache_read';
  if (name.includes('output')) return 'output';
  if (name.includes('input')) return 'input';
  return 'other';
}

/** Sum spend per token bucket across the cost report. Pure. */
export function byBucket(costBuckets) {
  const out = { input: 0, output: 0, cache_read: 0, cache_write: 0, other: 0 };
  for (const b of costBuckets) {
    for (const r of b.results ?? []) out[bucketOf(r.token_type)] += amount(r);
  }
  return out;
}

/**
 * The model carrying the most output tokens, and its share. Pure.
 * Returns [model, share] or [null, 0].
 */
export function topModel(usageBuckets) {
  const perModel = new Map();
  let total = 0;
  for (const b of usageBuckets) {
    for (const r of b.results ?? []) {
      const model = r.model ?? 'unspecified';
      const out = Number(r.output_tokens ?? 0);
      perModel.set(model, (perModel.get(model) ?? 0) + out);
      total += out;
    }
  }
  if (!total) return [null, 0];
  let best = null;
  for (const [m, v] of perModel) if (best === null || v > perModel.get(best)) best = m;
  return [best, perModel.get(best) / total];
}

/**
 * Turn the spend split into the lever that will actually move it. Pure. Each
 * state names a different repair; applying the wrong one changes nothing.
 * Returns [state, detail].
 */
export function verdict(buckets, minSpend = 1) {
  const total = Object.values(buckets).reduce((a, b) => a + b, 0);
  if (total < minSpend) {
    return ['no-spend', `$${total.toFixed(2)} over the window: nothing to act on`];
  }

  const pct = (k) => (buckets[k] / total) * 100;
  let split = `output ${pct('output').toFixed(0)}%, input ${pct('input').toFixed(0)}%, ` +
    `cache read ${pct('cache_read').toFixed(0)}%, cache write ${pct('cache_write').toFixed(0)}%`;
  if (buckets.other > 0) split += `, unrecognised ${pct('other').toFixed(0)}%`;
  const money = `$${total.toFixed(2)} over the window: ${split}`;

  if (buckets.cache_write > buckets.cache_read && pct('cache_write') >= 15) {
    return ['cache-write-heavy',
      `${money}. You are paying the cache write premium without the reads to ` +
      'amortise it: the prefix is being rewritten more often than it is hit.'];
  }

  if (pct('output') >= 70) {
    return ['output-dominated',
      `${money}. Output is priced at ${OUTPUT_MULTIPLE}x input and there is no ` +
      'caching discount on it, so the only lever is generating fewer tokens: ' +
      'lower effort, tighter stop conditions, shorter output formats.'];
  }

  if (pct('input') + pct('cache_read') + pct('cache_write') >= 60) {
    return ['input-dominated',
      `${money}. This is the shape prompt caching is for. Cache the stable ` +
      'prefix and read it back; trimming output here buys very little.'];
  }

  if (pct('output') >= 50) {
    return ['output-led',
      `${money}. Output is the larger half but not overwhelmingly. Both levers ` +
      'help and neither is dramatic on its own.'];
  }

  return ['balanced', money];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of params) url.searchParams.append(k, v);
  const res = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations endpoints ` +
                    'need an Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function readAll(key, path, params) {
  const out = [];
  let p = params;
  for (;;) {
    const page = await get(key, path, p);
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) break;
    p = p.filter((x) => x[0] !== 'page').concat([['page', page.next_page]]);
  }
  return out;
}

async function main() {
  const key = process.env.ANTHROPIC_ADMIN_KEY;
  if (!key) {
    console.error('set ANTHROPIC_ADMIN_KEY (an Admin API key, sk-ant-admin...; ' +
                  'workspace keys are rejected by /v1/organizations/*)');
    process.exitCode = 2;
    return;
  }

  const argv = process.argv;
  const days = Number(argv.includes('--days') ? argv[argv.indexOf('--days') + 1] : 30) || 30;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10) +
    'T00:00:00Z';

  const costs = await readAll(key, '/organizations/cost_report',
    [['starting_at', since], ['limit', '31'], ['group_by[]', 'description']]);
  const usage = await readAll(key, '/organizations/usage_report/messages',
    [['starting_at', since], ['bucket_width', '1d'], ['limit', '31'],
      ['group_by[]', 'model']]);

  const split = byBucket(costs);
  const [state, detail] = verdict(split);
  const line = `${state.padEnd(18)} ${detail}`;

  let bad = 0;
  if (['no-spend', 'balanced', 'input-dominated'].includes(state)) console.log(line);
  else { bad = 1; console.warn(line); }

  const [model, share] = topModel(usage);
  if (model) {
    console.log(`top model by output tokens: ${model} ` +
                `(${(share * 100).toFixed(0)}% of output)`);
    if (bad) {
      console.warn(`  repair, to run yourself: lower output_config.effort on ${model} ` +
                   '(high to medium is the usual first step), then re-read this same ' +
                   'daily series a week later. Thinking tokens bill as output, so ' +
                   'effort is the setting that moves this share.');
      console.warn('  never change an effort setting from inside an audit; the Admin ' +
                   'API cannot do it and neither should this.');
    }
  } else {
    console.log('no output tokens in the usage report for this window');
  }

  console.log(`${costs.length} cost bucket(s), ${usage.length} usage bucket(s) ` +
              `over ${days} day(s), ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The amount parser gets a test because the field is a string and the bug it prevents is a total of zero on an account spending thousands. The bucketing gets one because a token type nobody has seen before must land somewhere visible instead of vanishing out of the denominator. And the states are pinned against each other: the same total spend, split three different ways, has to produce three different recommendations, because a caching project shipped against an output-dominated bill is a month of work for nothing.",
"test_py_file": "test_anthropic_output_cost_audit.py",
"test_py": '''from anthropic_output_cost_audit import (amount, bucket_of, by_bucket,
                                          top_model, verdict)


def cost(token_type, value, description="Claude Sonnet 5"):
    # amount arrives as a decimal STRING on this endpoint, not a number.
    return {"currency": "USD", "amount": str(value), "token_type": token_type,
            "description": description, "cost_type": "tokens"}


def cost_day(*rows):
    return {"starting_at": "2026-08-01T00:00:00Z", "results": list(rows)}


def usage_day(*rows):
    return {"starting_at": "2026-08-01T00:00:00Z", "results": list(rows)}


def test_amount_is_a_string_on_this_endpoint():
    assert amount({"amount": "12.34"}) == 12.34
    assert amount({"amount": 12.34}) == 12.34
    assert amount({"amount": ""}) == 0.0
    assert amount({}) == 0.0
    assert amount({"amount": "n/a"}) == 0.0


def test_token_types_fold_into_buckets_by_shape_not_by_exact_name():
    assert bucket_of("output_tokens") == "output"
    assert bucket_of("uncached_input_tokens") == "input"
    assert bucket_of("cache_read_input_tokens") == "cache_read"
    assert bucket_of("cache_creation_input_tokens") == "cache_write"
    assert bucket_of("1h_cache_creation_input_tokens") == "cache_write"
    # A type that does not exist yet must stay visible rather than vanish.
    assert bucket_of("some_future_tier_tokens") == "other"
    assert bucket_of(None) == "other"


def test_unrecognised_types_stay_in_the_denominator():
    rows = by_bucket([cost_day(cost("output_tokens", "60"),
                               cost("some_future_tier_tokens", "40"))])
    assert rows["other"] == 40.0
    state, detail = verdict(rows)
    assert "unrecognised 40%" in detail
    assert state == "output-led"


def test_the_same_spend_split_three_ways_gives_three_different_repairs():
    output_heavy = by_bucket([cost_day(cost("output_tokens", "800"),
                                       cost("uncached_input_tokens", "200"))])
    input_heavy = by_bucket([cost_day(cost("output_tokens", "300"),
                                      cost("uncached_input_tokens", "500"),
                                      cost("cache_read_input_tokens", "200"))])
    even = by_bucket([cost_day(cost("output_tokens", "450"),
                               cost("uncached_input_tokens", "550"))])

    assert verdict(output_heavy)[0] == "output-dominated"
    assert verdict(input_heavy)[0] == "input-dominated"
    assert verdict(even)[0] == "balanced"


def test_an_output_dominated_bill_names_the_only_lever_there_is():
    rows = by_bucket([cost_day(cost("output_tokens", "800"),
                               cost("uncached_input_tokens", "200"))])
    _, detail = verdict(rows)
    assert "no caching discount" in detail
    assert "5x input" in detail


def test_cache_writes_without_reads_is_its_own_finding():
    # Writes cost more than base input; without reads to amortise them the
    # caching is a premium being paid for nothing.
    rows = by_bucket([cost_day(cost("cache_creation_input_tokens", "400"),
                               cost("cache_read_input_tokens", "50"),
                               cost("output_tokens", "300"),
                               cost("uncached_input_tokens", "250"))])
    state, detail = verdict(rows)
    assert state == "cache-write-heavy"
    assert "amortise" in detail


def test_output_between_half_and_seventy_percent_is_not_an_emergency():
    rows = by_bucket([cost_day(cost("output_tokens", "550"),
                               cost("uncached_input_tokens", "450"))])
    assert verdict(rows)[0] == "output-led"


def test_a_quiet_window_reports_nothing_rather_than_a_noisy_share():
    rows = by_bucket([cost_day(cost("output_tokens", "0.10"))])
    assert verdict(rows)[0] == "no-spend"
    assert verdict(by_bucket([]))[0] == "no-spend"


def test_top_model_names_where_an_effort_change_would_land():
    model, share = top_model([
        usage_day({"model": "claude-opus-5", "output_tokens": 900,
                   "uncached_input_tokens": 4000},
                  {"model": "claude-sonnet-5", "output_tokens": 100,
                   "uncached_input_tokens": 8000}),
    ])
    assert model == "claude-opus-5"
    assert round(share, 2) == 0.9
    assert top_model([]) == (None, 0.0)
''',
"test_js_file": "anthropic-output-cost-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { amount, bucketOf, byBucket, topModel, verdict }
  from './anthropic-output-cost-audit.mjs';

// amount arrives as a decimal STRING on this endpoint, not a number.
const cost = (tokenType, value, description = 'Claude Sonnet 5') => ({
  currency: 'USD', amount: String(value), token_type: tokenType, description,
  cost_type: 'tokens',
});

const costDay = (...rows) => ({ starting_at: '2026-08-01T00:00:00Z', results: rows });
const usageDay = (...rows) => ({ starting_at: '2026-08-01T00:00:00Z', results: rows });

test('amount is a string on this endpoint', () => {
  assert.equal(amount({ amount: '12.34' }), 12.34);
  assert.equal(amount({ amount: 12.34 }), 12.34);
  assert.equal(amount({ amount: '' }), 0);
  assert.equal(amount({}), 0);
  assert.equal(amount({ amount: 'n/a' }), 0);
});

test('token types fold into buckets by shape, not by exact name', () => {
  assert.equal(bucketOf('output_tokens'), 'output');
  assert.equal(bucketOf('uncached_input_tokens'), 'input');
  assert.equal(bucketOf('cache_read_input_tokens'), 'cache_read');
  assert.equal(bucketOf('cache_creation_input_tokens'), 'cache_write');
  assert.equal(bucketOf('1h_cache_creation_input_tokens'), 'cache_write');
  assert.equal(bucketOf('some_future_tier_tokens'), 'other');
  assert.equal(bucketOf(null), 'other');
});

test('unrecognised types stay in the denominator', () => {
  const rows = byBucket([costDay(cost('output_tokens', '60'),
    cost('some_future_tier_tokens', '40'))]);
  assert.equal(rows.other, 40);
  const [state, detail] = verdict(rows);
  assert.match(detail, /unrecognised 40%/);
  assert.equal(state, 'output-led');
});

test('the same spend split three ways gives three different repairs', () => {
  const outputHeavy = byBucket([costDay(cost('output_tokens', '800'),
    cost('uncached_input_tokens', '200'))]);
  const inputHeavy = byBucket([costDay(cost('output_tokens', '300'),
    cost('uncached_input_tokens', '500'), cost('cache_read_input_tokens', '200'))]);
  const even = byBucket([costDay(cost('output_tokens', '450'),
    cost('uncached_input_tokens', '550'))]);

  assert.equal(verdict(outputHeavy)[0], 'output-dominated');
  assert.equal(verdict(inputHeavy)[0], 'input-dominated');
  assert.equal(verdict(even)[0], 'balanced');
});

test('an output dominated bill names the only lever there is', () => {
  const rows = byBucket([costDay(cost('output_tokens', '800'),
    cost('uncached_input_tokens', '200'))]);
  const [, detail] = verdict(rows);
  assert.match(detail, /no caching discount/);
  assert.match(detail, /5x input/);
});

test('cache writes without reads is its own finding', () => {
  const rows = byBucket([costDay(cost('cache_creation_input_tokens', '400'),
    cost('cache_read_input_tokens', '50'), cost('output_tokens', '300'),
    cost('uncached_input_tokens', '250'))]);
  const [state, detail] = verdict(rows);
  assert.equal(state, 'cache-write-heavy');
  assert.match(detail, /amortise/);
});

test('output between half and seventy percent is not an emergency', () => {
  const rows = byBucket([costDay(cost('output_tokens', '550'),
    cost('uncached_input_tokens', '450'))]);
  assert.equal(verdict(rows)[0], 'output-led');
});

test('a quiet window reports nothing rather than a noisy share', () => {
  assert.equal(verdict(byBucket([costDay(cost('output_tokens', '0.10'))]))[0], 'no-spend');
  assert.equal(verdict(byBucket([]))[0], 'no-spend');
});

test('top model names where an effort change would land', () => {
  const [model, share] = topModel([
    usageDay({ model: 'claude-opus-5', output_tokens: 900, uncached_input_tokens: 4000 },
      { model: 'claude-sonnet-5', output_tokens: 100, uncached_input_tokens: 8000 }),
  ]);
  assert.equal(model, 'claude-opus-5');
  assert.equal(Number(share.toFixed(2)), 0.9);
  assert.deepEqual(topModel([]), [null, 0]);
});
''',
"faq": [
 ("Is output really five times the price of input?",
  "Per token, yes, on every current Claude model. That ratio is fixed before anything about your workload matters, which is why a request that feels input-heavy often is not: twenty thousand tokens of context against four thousand of answer is roughly an even split once the prices are applied."),
 ("Does prompt caching reduce output cost?",
  "No. There is no caching discount on output tokens, and no discount on them of any kind. Caching reduces what you pay for the repeated part of the prompt. If output is already most of the bill, a caching project will produce a satisfying drop in one line of the cost report and almost no change to the total."),
 ("Where do thinking tokens show up?",
  "As output tokens, billed at the output rate when they are generated. That is why an effort change moves this share with no visible change to the code that reads the response, and why a model that runs adaptive thinking when the parameter is omitted can shift the bill on a version bump alone."),
 ("Why does the script parse amount as a string?",
  "Because that is how the cost report returns it. The values are decimal strings, so adding them without a conversion concatenates them in JavaScript and raises in Python. It is a small thing that silently produces either a nonsense total or none at all."),
 ("What does cache-write-heavy actually mean?",
  "That you are paying the premium for writing a cache entry more often than you are collecting the discount for reading one. It usually means the cached prefix is not stable between requests, so every call rewrites it. Caching is not free, and this is the state where it is costing more than it saves."),
],
"related": [
 ("/llm/reasoning-tokens-billed-invisibly/", "Reasoning tokens billed but never returned"),
 ("/llm/no-organization-spend-limit/", "No spend limit means no ceiling"),
 ("/llm/quota-exhausted-not-rate-limited/", "A 429 that is a wall, not a throttle"),
],
"citations": [CITE_CL_PRICING, CITE_CL_COST, CITE_CL_USAGE, CITE_CL_THINKING],
},

]
