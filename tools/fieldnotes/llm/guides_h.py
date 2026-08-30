#!/usr/bin/env python3
"""/llm/ field notes, batch H — the writing.

Four notes about which limiter is actually binding, and they are not four
readings of one 429.

`rate-limit-headers-near-exhaustion` is the OpenAI half, and it exists because
OpenAI has no endpoint that returns your remaining quota. The only forward
looking signal is a set of response headers that come back on every successful
call, so the script makes one cheap real call and reads the headroom off it as
a ratio. Nothing has failed yet; that is the point of the note.

`rate-limit-429-limiter-unidentified` is the Anthropic half and asks a
different question. Anthropic does publish the configured limits on a GET, and
it returns four header triples rather than two: requests, input tokens, output
tokens, and an aggregate that mirrors whichever of them is currently most
restrictive. Matching the aggregate back to the named triples is how you find
out which bucket the platform itself thinks is emptying, which is the thing a
"429 then sleep(1)" handler throws away.

`itpm-exhausted-uncached-input` and `otpm-exhausted` both read the per minute
usage buckets, and they are deliberately written to reach different
conclusions. ITPM is charged on uncached input only: `uncached_input_tokens`
plus both members of `cache_creation`, with `cache_read_input_tokens` excluded
on every model except Claude Haiku 3.5. So an input limiter that is full while
the cache read share is near zero is a note about caching as a throughput
lever, not as a discount. OTPM has no cache concept at all, is roughly one
fifth of ITPM at every tier, and counts thinking tokens. An output limiter that
is full while input has headroom means the request rate was never the ceiling,
so adding workers adds nothing, and `max_tokens` is documented not to count
toward it, which rules out the fix most people try first.

Read only throughout. Two of the four want an Anthropic Admin API key, one
wants an OpenAI project key set to Read Only, and one wants both an Admin key
and a workspace key for a single probe. GET requests only. Every repair is
printed for a human to run: raising a rate limit, adding a cache breakpoint and
lowering an effort setting are all deploys or console actions, not side effects
of an audit.
"""

CITE_OAI_RATE = ("Rate limits — OpenAI API",
                 "https://developers.openai.com/api/docs/guides/rate-limits")
CITE_OAI_MODELS = ("Models — OpenAI API reference",
                   "https://platform.openai.com/docs/api-reference/models")
CITE_OAI_PROJECT_RATE = ("Project rate limits — OpenAI API reference",
                         "https://platform.openai.com/docs/api-reference/project-rate-limits")
CITE_OAI_ADMIN = ("Administration and the Admin APIs — OpenAI developer docs",
                  "https://developers.openai.com/api/docs/guides/admin-apis")

CITE_CL_RATE = ("Rate limits — Claude Docs",
                "https://platform.claude.com/docs/en/api/rate-limits")
CITE_CL_RATE_API = ("Rate Limits API — Claude Docs",
                    "https://platform.claude.com/docs/en/manage-claude/rate-limits-api")
CITE_CL_USAGE_API = ("Usage and Cost API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")
CITE_CL_USAGE_REPORT = ("Get messages usage report — Claude Admin API",
                        "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_CL_CACHING = ("Prompt caching — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/prompt-caching")
CITE_CL_ERRORS = ("Errors — Claude API",
                  "https://platform.claude.com/docs/en/api/errors")
CITE_CL_BATCHES = ("Message Batches — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/batch-processing")
CITE_CL_CONTEXT = ("Context windows — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/context-windows")

REL_LIMITER = ("/llm/rate-limit-429-limiter-unidentified/",
               "Naming which of the three limiters actually emptied")
REL_ITPM = ("/llm/itpm-exhausted-uncached-input/",
            "The input limiter is full and cache reads do not count toward it")
REL_OTPM = ("/llm/otpm-exhausted/",
            "Output per minute is the ceiling, so concurrency will not help")
REL_QUOTA = ("/llm/quota-exhausted-not-rate-limited/",
             "A 429 that is a billing wall rather than a throttle")
REL_NO_SPEND_LIMIT = ("/llm/no-organization-spend-limit/",
                      "Nothing in the platform stops a runaway bill")
REL_CACHE_NEVER = ("/llm/prompt-caching-never-used/",
                   "A stable prefix reprocessed at full price on every call")
REL_CACHE_WRITES = ("/llm/cache-writes-with-no-reads/",
                    "Cache writes paid for and never read back")
REL_BATCH = ("/llm/batch-discount-left-unused/",
             "Latency-tolerant work paying full price on the synchronous path")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "Output tokens, not input, are what the bill is made of")

GUIDES = [
{
"slug": "rate-limit-headers-near-exhaustion",
"title": "x-ratelimit-remaining sits near zero before any 429",
"description": "OpenAI has no endpoint that returns your remaining quota. The headers on one cheap GET are the only forward-looking view, and nothing reads them.",
"h1": "x-ratelimit-remaining sits near zero before any 429",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["x-ratelimit-remaining-tokens", "openai rate limit headroom",
             "x-ratelimit-limit-project-tokens", "openai 429 before it happens",
             "openai rate limit headers stripped by proxy"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, a project key set to Read Only.",
"lead": "Nothing has failed. There is no incident, no 429 in the logs, no page. There is a number that says you are running on four percent of your token budget at four in the afternoon, and it arrives attached to every successful response your application has ever received, and no code you own has ever looked at it.",
"short_answer": """<p>Make one cheap real call and read the headers off it. <code>GET /v1/models</code> with a project key set to Read Only returns <code>x-ratelimit-limit-requests</code>, <code>x-ratelimit-remaining-requests</code>, <code>x-ratelimit-reset-requests</code> and the matching <code>-tokens</code> triple. The finding is <code>remaining / limit</code>, and anything under about 0.2 at steady state is a 429 waiting for a traffic spike.</p>
<p>Read both triples, not one. Token headroom and request headroom empty independently: a workload of many tiny calls runs out of requests with most of its tokens unspent, and a workload of few enormous calls does the reverse. Only the scarcer of the two is worth quoting.</p>
<p>If <code>x-ratelimit-limit-project-tokens</code> comes back as well, the project ceiling is lower than the organization ceiling and is the number that actually binds. If none of the headers come back at all, something between you and OpenAI is stripping them, and that is the finding.</p>""",
"problem": """<p>OpenAI does not have a quota endpoint. There is no <code>GET</code> anywhere in the API that answers "how much of my rate limit is left", and the dashboard shows you what you have already spent rather than what you have left in the current window. The only forward-looking signal the platform emits is a set of response headers, and they arrive on <em>successful</em> responses &mdash; which is to say, on exactly the responses nobody inspects.</p>
<p>So the entire signal is discarded by construction. The SDK parses the body and hands you a typed object; the headers are on the raw response, one attribute deeper than anything the application touches. The result is a system that has no idea it is running at ninety-six percent utilisation, and finds out on the afternoon a customer sends twice the usual traffic, when a burst that would have been absorbed a month ago comes back <code>429</code> instead. Latency creeps first, because requests queue behind a bucket that is refilling as fast as it is being drained, and creeping latency is not a signal anyone traces back to a rate limit.</p>""",
"why": """<p><strong>The headroom is not stored anywhere you can query.</strong> These numbers describe the state of a token bucket at the instant your call was served, at the scope that call was made in. There is no history and no aggregate. A read-only audit sees them by making a real call and looking, which is why this script probes rather than reports &mdash; and why running it once at three in the morning tells you nothing about four in the afternoon.</p>
<p><strong>The two dimensions exhaust independently, and averaging them hides the finding.</strong> A classifier making four hundred tiny calls a second is limited by requests per minute long before it is limited by tokens per minute. A summariser sending sixty-thousand-token documents is the opposite. The dimension with the least headroom is the one that will produce your 429, and it is the only one whose number belongs in the report.</p>
<p><strong>A project-scoped triple means the org ceiling is not your ceiling.</strong> When <code>x-ratelimit-limit-project-tokens</code> is present it is a separate, usually lower limit configured on the project. Reading the org triple and concluding you have room is the specific mistake this causes: the org has room, and your project does not. Which limit is smaller is a comparison, and the script does it rather than assuming.</p>
<p><strong>Absent headers are worse news than low ones.</strong> Corporate proxies, API gateways and some LLM routers strip or rewrite response headers they do not recognise. If they never reach your process, you have no forward-looking signal <em>and</em> no diagnostic on the 429 when it comes, because <code>Retry-After</code> travels the same path. A clean run with no headers is not a clean bill of health and the script does not report it as one.</p>
<p><strong>This is not the billing wall.</strong> A 429 that carries <code>insufficient_quota</code> or <code>credit_balance_exhausted</code> has nothing to do with these headers and will not clear when the window resets. That is a <a href="/llm/quota-exhausted-not-rate-limited/">separate note</a> with a separate remedy, and telling them apart is the difference between waiting sixty seconds and adding credits.</p>""",
"steps": [
 {"h": "Probe with the cheapest real call there is",
  "body": """<p><code>GET /v1/models</code> returns the model list and consumes no inference quota, and it carries the same <code>x-ratelimit-*</code> header set as a completion. A Read Only project key is enough. Do not manufacture a 429 to see what one looks like &mdash; deliberately draining a bucket on a production key is an outage you caused for a diagram.</p>"""},
 {"h": "Parse the triple, including the reset",
  "body": """<p>Each dimension is three headers: <code>-limit-</code>, <code>-remaining-</code> and <code>-reset-</code>. The reset is a Go-style duration string, so <code>6m0s</code> and <code>500ms</code> and <code>1h2m3s</code> are all valid and none of them is an integer. A parser that calls <code>int()</code> on it throws away the one number that tells you how long the pressure lasts.</p>"""},
 {"h": "Compute the ratio and name the scarcest dimension",
  "body": """<p><code>remaining / limit</code> per dimension, then report the minimum. Quoting the healthy dimension alongside the scarce one reads like reassurance; the report should say "tokens, four percent" and stop. Twenty percent is a reasonable floor to alert on, and it is a floor about your traffic shape rather than a rule.</p>"""},
 {"h": "Compare the project ceiling against the organization ceiling",
  "body": """<p>If the project-scoped headers are present, put the two limits side by side. The smaller one is the real constraint and the larger one is decoration. This is also how a staging project's throttle gets discovered after it followed the project id into production.</p>"""},
 {"h": "Print the repair; do not apply it",
  "body": """<p>Three repairs, and the script prints whichever fits: request a tier increase, pace the client with a token bucket sized to <code>x-ratelimit-limit-tokens</code> so bursts are spread rather than rejected, or raise the project's limit through the Admin API. The last of those is a write call against a limit your colleagues share, and an audit script holding a key is not who should make that decision.</p>"""},
],
"verify": """<p>Run it on a schedule at your busiest hour rather than once. Headroom is a property of the moment, and a single sample at midnight is a number about midnight.</p>
<pre><code class="language-bash">python3 openai_rate_limit_headroom.py
# near-exhaustion  tokens             8000 of 200000 left (4%), resets in 47s
#   binding dimension: tokens, at 4% of its ceiling
#   note: project ceiling binds for tokens (150000 against an org 200000)
# 4 dimension(s) read, 1 finding(s)</code></pre>""",
"code_intro": "One GET and nothing else. It wants <code>OPENAI_API_KEY</code>, a project key set to Read Only, and it never touches <code>/v1/organization</code> at all &mdash; the headers are project- and org-scoped by whatever the key is. Six pure functions carry every judgement: two parsers for the formats the headers actually use, the triple reader that is case-insensitive because gateways rewrite header casing, the ratio, the verdict, and the comparison that decides whether the project or the organization owns your real ceiling.",
"py_file": "openai_rate_limit_headroom.py",
"py": '''"""Report how much OpenAI rate-limit headroom is left, before anything 429s.

Read only. One GET request and nothing else: OPENAI_API_KEY should be a project
key set to Read Only. GET /v1/models consumes no inference quota and carries the
same x-ratelimit-* header set as a completion, which is the whole trick, because
OpenAI has no endpoint that returns remaining quota on request.

The repair is printed, never performed. Raising a project rate limit is a write
call against a ceiling your colleagues share.

This script never tries to provoke a 429. Draining a production token bucket to
see what the error looks like is an outage you caused on purpose.
"""
import argparse
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_rate_limit_headroom")

API = "https://api.openai.com/v1"

# The dimensions OpenAI reports. The project-scoped pair is present only when the
# project carries its own limit, and when it is present it is usually the lower
# of the two, which makes it the one that actually binds.
DIMENSIONS = ("requests", "tokens", "project-requests", "project-tokens")

# The reset headers are Go duration strings: "6m0s", "500ms", "1h2m3s". Ordered
# so that "ms" is tried before "m", because the other way round parses 500ms as
# 500 minutes and reports eight hours of pressure that does not exist.
_DURATION = re.compile(r"(\\d+(?:\\.\\d+)?)(ms|us|ns|h|m|s)")
_UNITS = {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0}

FINDINGS = ("exhausted", "near-exhaustion")


def header_names(dimension):
    """The limit/remaining/reset header triple for one dimension. Pure."""
    return ("x-ratelimit-limit-" + dimension,
            "x-ratelimit-remaining-" + dimension,
            "x-ratelimit-reset-" + dimension)


def parse_count(value):
    """Read a limit or remaining header as an integer. Pure.

    Returns None rather than zero when the value is missing or unreadable.
    Zero is a real and important state here: it means the bucket is empty. A
    parser that folds "absent" into "empty" reports a stripped header as an
    exhausted limiter and sends somebody to the wrong console.
    """
    if value is None:
        return None
    text = str(value).strip().replace(",", "").replace("_", "")
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_reset(value):
    """Read a reset header as seconds. Pure. Returns None if unreadable.

    The whole string has to be consumed. A partial match on something like
    "60 seconds" would return 60.0 from a format this parser does not actually
    understand, and a reset window is exactly the number a reader will act on.
    """
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    parts = _DURATION.findall(text)
    if not parts:
        return None
    if "".join(a + b for a, b in parts) != text:
        return None
    return sum(float(a) * _UNITS[b] for a, b in parts)


def triples(headers):
    """Parse the x-ratelimit-* triples off one response. Pure.

    Matched case-insensitively because gateways and proxies rewrite header
    casing freely, and a dict keyed on the exact casing OpenAI sends is how a
    working probe starts reporting no headers the day a load balancer changes.
    """
    lower = {}
    for name, value in dict(headers or {}).items():
        lower[str(name).strip().lower()] = value

    out = {}
    for dimension in DIMENSIONS:
        limit_h, remaining_h, reset_h = header_names(dimension)
        if limit_h not in lower and remaining_h not in lower:
            continue
        out[dimension] = {"limit": parse_count(lower.get(limit_h)),
                          "remaining": parse_count(lower.get(remaining_h)),
                          "reset": parse_reset(lower.get(reset_h))}
    return out


def headroom(triple):
    """remaining / limit for one dimension, or None if it cannot be computed. Pure."""
    if not isinstance(triple, dict):
        return None
    limit = triple.get("limit")
    remaining = triple.get("remaining")
    if limit is None or remaining is None or limit <= 0:
        return None
    return max(0.0, min(1.0, remaining / float(limit)))


def verdict(dimension, triple, floor=0.2):
    """Classify one dimension. Pure. Returns (state, detail)."""
    share = headroom(triple)
    if share is None:
        return ("unreadable",
                "the %s triple arrived without a usable limit and remaining "
                "pair, so there is no ratio to read" % dimension)

    remaining = triple.get("remaining")
    limit = triple.get("limit")
    reset = triple.get("reset")
    window = ("resets in %.0fs" % reset) if reset is not None else "no readable reset"
    shape = "%d of %d left (%.0f%%), %s" % (remaining, limit, share * 100, window)

    if remaining == 0:
        return ("exhausted",
                "%s. This bucket is empty now, so the next call in this window "
                "is a 429 no matter how small it is." % shape)
    if share < floor:
        return ("near-exhaustion",
                "%s. Under the %.0f%% floor, which means the next traffic spike "
                "converts this into a 429." % (shape, floor * 100))
    return ("headroom", shape + ".")


def binding(parsed):
    """The dimension with the least headroom left. Pure. Returns (name, share).

    Token headroom and request headroom empty independently, so the mean of the
    two is a number about nothing. The minimum is the one that produces the 429
    and the only one worth putting in a report.
    """
    best = None
    for dimension in sorted(parsed or {}):
        share = headroom(parsed[dimension])
        if share is None:
            continue
        if best is None or share < best[1]:
            best = (dimension, share)
    return best


def scope_note(parsed):
    """Which scope owns the real ceiling, per dimension. Pure.

    Returns a list of (owner, dimension, binding_limit, other_limit). The
    project-scoped headers are present only when the project carries its own
    limit; when it is lower than the organization's, reading the org triple and
    concluding there is room is the exact mistake this function exists to stop.
    """
    out = []
    for dimension in ("requests", "tokens"):
        org = (parsed or {}).get(dimension) or {}
        project = (parsed or {}).get("project-" + dimension) or {}
        org_limit = org.get("limit")
        project_limit = project.get("limit")
        if org_limit is None or project_limit is None:
            continue
        if project_limit < org_limit:
            out.append(("project", dimension, project_limit, org_limit))
        elif org_limit < project_limit:
            out.append(("organization", dimension, org_limit, project_limit))
        else:
            out.append(("equal", dimension, project_limit, org_limit))
    return out


def probe(session):
    """One cheap real call. GET only, and it consumes no inference quota."""
    r = session.get(API + "/models", timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: OPENAI_API_KEY is not a valid key")
    if r.status_code == 429:
        # Worth saying plainly: the headers are still on this response, and a
        # 429 here is about the model-list endpoint, not about inference.
        log.warning("the probe itself was rate limited; the headers below "
                    "describe the bucket that rejected it")
        return r.headers
    r.raise_for_status()
    return r.headers


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--floor", type=float, default=0.2,
                    help="headroom share below which a dimension is a finding "
                         "(default 0.2)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print dimensions with plenty of headroom")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY (a project key set to Read Only)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    parsed = triples(probe(session))
    if not parsed:
        log.warning("headers-missing    no x-ratelimit-* headers reached this "
                    "process at all")
        log.warning("  This is not a clean bill of health. Something between "
                    "you and OpenAI is stripping response headers, so you have "
                    "no forward-looking signal and no Retry-After on the 429 "
                    "when it arrives.")
        log.warning("  repair: check the proxy, gateway or LLM router in front "
                    "of api.openai.com and allow the x-ratelimit-* and "
                    "retry-after headers through unmodified")
        return 1

    checked = 0
    bad = 0
    for dimension in sorted(parsed):
        state, detail = verdict(dimension, parsed[dimension], args.floor)
        checked += 1
        line = "%-16s %-18s %s" % (state, dimension, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
        elif state == "unreadable":
            log.warning(line)
        elif args.show_all:
            log.info(line)

    scarcest = binding(parsed)
    if scarcest:
        log.info("binding dimension: %s, at %.0f%% of its ceiling",
                 scarcest[0], scarcest[1] * 100)

    for owner, dimension, low, high in scope_note(parsed):
        if owner == "project":
            log.warning("  note: the project ceiling binds for %s (%d against "
                        "an org %d), so org headroom is not your headroom",
                        dimension, low, high)
        elif owner == "organization":
            log.info("  note: the org ceiling binds for %s (%d against a "
                     "project %d)", dimension, low, high)

    if bad:
        log.warning("  repair: request a usage tier increase, or pace the "
                    "client with a token bucket sized to the limit above so "
                    "bursts are spread across the window instead of rejected")
        log.warning("  repair: to raise the project ceiling instead, an admin "
                    "can call POST /v1/organization/projects/{project_id}"
                    "/rate_limits/{rate_limit_id}. That is a write against a "
                    "limit your colleagues share, so it is printed, not run.")

    log.info("%d dimension(s) read, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-rate-limit-headroom.mjs",
"js": '''/**
 * Report how much OpenAI rate-limit headroom is left, before anything 429s.
 *
 * Read only. One GET request and nothing else: OPENAI_API_KEY should be a
 * project key set to Read Only. GET /v1/models consumes no inference quota and
 * carries the same x-ratelimit-* header set as a completion, which is the whole
 * trick, because OpenAI has no endpoint that returns remaining quota.
 *
 * The repair is printed, never performed, and the script never tries to provoke
 * a 429.
 */
const API = 'https://api.openai.com/v1';

const DIMENSIONS = ['requests', 'tokens', 'project-requests', 'project-tokens'];

// "ms" before "m", because the other order parses 500ms as 500 minutes.
const DURATION = /(\\d+(?:\\.\\d+)?)(ms|us|ns|h|m|s)/g;
const UNITS = { ns: 1e-9, us: 1e-6, ms: 1e-3, s: 1, m: 60, h: 3600 };

const FINDINGS = new Set(['exhausted', 'near-exhaustion']);

/** The limit/remaining/reset header triple for one dimension. Pure. */
export function headerNames(dimension) {
  return [`x-ratelimit-limit-${dimension}`,
          `x-ratelimit-remaining-${dimension}`,
          `x-ratelimit-reset-${dimension}`];
}

/**
 * Read a limit or remaining header as an integer. Pure.
 * Returns null rather than 0 when absent: zero is a real state here and means
 * the bucket is empty, so folding the two reports a stripped header as an
 * exhausted limiter.
 */
export function parseCount(value) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim().replace(/[,_]/g, '');
  if (!text) return null;
  const n = Number(text);
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

/**
 * Read a reset header as seconds. Pure. Returns null if unreadable.
 * The whole string must be consumed; a partial match on "60 seconds" would
 * return a number from a format this parser does not understand.
 */
export function parseReset(value) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim().toLowerCase();
  if (!text) return null;
  const parts = [...text.matchAll(DURATION)];
  if (parts.length === 0) return null;
  if (parts.map(([whole]) => whole).join('') !== text) return null;
  return parts.reduce((sum, [, n, unit]) => sum + Number(n) * UNITS[unit], 0);
}

/**
 * Parse the x-ratelimit-* triples off one response. Pure.
 * Case-insensitive, because gateways rewrite header casing freely.
 */
export function triples(headers) {
  const lower = new Map();
  const entries = typeof headers?.entries === 'function'
    ? [...headers.entries()] : Object.entries(headers ?? {});
  for (const [name, value] of entries) lower.set(String(name).trim().toLowerCase(), value);

  const out = {};
  for (const dimension of DIMENSIONS) {
    const [limitH, remainingH, resetH] = headerNames(dimension);
    if (!lower.has(limitH) && !lower.has(remainingH)) continue;
    out[dimension] = {
      limit: parseCount(lower.get(limitH)),
      remaining: parseCount(lower.get(remainingH)),
      reset: parseReset(lower.get(resetH)),
    };
  }
  return out;
}

/** remaining / limit for one dimension, or null. Pure. */
export function headroom(triple) {
  if (!triple || typeof triple !== 'object') return null;
  const { limit, remaining } = triple;
  if (limit === null || limit === undefined) return null;
  if (remaining === null || remaining === undefined) return null;
  if (limit <= 0) return null;
  return Math.max(0, Math.min(1, remaining / limit));
}

/** Classify one dimension. Pure. Returns [state, detail]. */
export function verdict(dimension, triple, floor = 0.2) {
  const share = headroom(triple);
  if (share === null) {
    return ['unreadable',
      `the ${dimension} triple arrived without a usable limit and remaining ` +
      'pair, so there is no ratio to read'];
  }
  const { remaining, limit, reset } = triple;
  const window = reset === null || reset === undefined
    ? 'no readable reset' : `resets in ${reset.toFixed(0)}s`;
  const shape = `${remaining} of ${limit} left (${(share * 100).toFixed(0)}%), ${window}`;

  if (remaining === 0) {
    return ['exhausted',
      `${shape}. This bucket is empty now, so the next call in this window is ` +
      'a 429 no matter how small it is.'];
  }
  if (share < floor) {
    return ['near-exhaustion',
      `${shape}. Under the ${(floor * 100).toFixed(0)}% floor, which means the ` +
      'next traffic spike converts this into a 429.'];
  }
  return ['headroom', `${shape}.`];
}

/**
 * The dimension with the least headroom left. Pure. Returns [name, share].
 * The mean of two independently emptying buckets is a number about nothing.
 */
export function binding(parsed) {
  let best = null;
  for (const dimension of Object.keys(parsed ?? {}).sort()) {
    const share = headroom(parsed[dimension]);
    if (share === null) continue;
    if (best === null || share < best[1]) best = [dimension, share];
  }
  return best;
}

/**
 * Which scope owns the real ceiling, per dimension. Pure.
 * Returns [owner, dimension, bindingLimit, otherLimit] rows.
 */
export function scopeNote(parsed) {
  const out = [];
  for (const dimension of ['requests', 'tokens']) {
    const orgLimit = (parsed ?? {})[dimension]?.limit;
    const projectLimit = (parsed ?? {})[`project-${dimension}`]?.limit;
    if (orgLimit === null || orgLimit === undefined) continue;
    if (projectLimit === null || projectLimit === undefined) continue;
    if (projectLimit < orgLimit) out.push(['project', dimension, projectLimit, orgLimit]);
    else if (orgLimit < projectLimit) out.push(['organization', dimension, orgLimit, projectLimit]);
    else out.push(['equal', dimension, projectLimit, orgLimit]);
  }
  return out;
}

/** One cheap real call. GET only, and it consumes no inference quota. */
async function probe(key) {
  const res = await fetch(`${API}/models`, {
    headers: { Authorization: `Bearer ${key}` },
  });
  if (res.status === 401) throw new Error('401 from OpenAI: OPENAI_API_KEY is not a valid key');
  if (res.status === 429) {
    console.warn('the probe itself was rate limited; the headers below describe ' +
                 'the bucket that rejected it');
    return res.headers;
  }
  if (!res.ok) throw new Error(`${res.status} from /v1/models`);
  return res.headers;
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only)');
    process.exitCode = 2;
    return;
  }
  const floor = Number(process.env.FLOOR ?? 0.2);
  const showAll = process.env.SHOW_ALL === '1';

  const parsed = triples(await probe(key));
  if (Object.keys(parsed).length === 0) {
    console.warn('headers-missing    no x-ratelimit-* headers reached this process at all');
    console.warn('  This is not a clean bill of health. Something between you and ' +
                 'OpenAI is stripping response headers, so you have no forward-looking ' +
                 'signal and no Retry-After on the 429 when it arrives.');
    console.warn('  repair: check the proxy, gateway or LLM router in front of ' +
                 'api.openai.com and allow the x-ratelimit-* and retry-after headers ' +
                 'through unmodified');
    process.exitCode = 1;
    return;
  }

  let checked = 0;
  let bad = 0;
  for (const dimension of Object.keys(parsed).sort()) {
    const [state, detail] = verdict(dimension, parsed[dimension], floor);
    checked += 1;
    const line = `${state.padEnd(16)} ${dimension.padEnd(18)} ${detail}`;
    if (FINDINGS.has(state)) { bad += 1; console.warn(line); }
    else if (state === 'unreadable') console.warn(line);
    else if (showAll) console.log(line);
  }

  const scarcest = binding(parsed);
  if (scarcest) {
    console.log(`binding dimension: ${scarcest[0]}, at ` +
                `${(scarcest[1] * 100).toFixed(0)}% of its ceiling`);
  }

  for (const [owner, dimension, low, high] of scopeNote(parsed)) {
    if (owner === 'project') {
      console.warn(`  note: the project ceiling binds for ${dimension} (${low} ` +
                   `against an org ${high}), so org headroom is not your headroom`);
    } else if (owner === 'organization') {
      console.log(`  note: the org ceiling binds for ${dimension} (${low} against ` +
                  `a project ${high})`);
    }
  }

  if (bad) {
    console.warn('  repair: request a usage tier increase, or pace the client with ' +
                 'a token bucket sized to the limit above so bursts are spread ' +
                 'across the window instead of rejected');
    console.warn('  repair: to raise the project ceiling instead, an admin can call ' +
                 'POST /v1/organization/projects/{project_id}/rate_limits/{rate_limit_id}. ' +
                 'That is a write against a limit your colleagues share, so it is ' +
                 'printed, not run.');
  }

  console.log(`${checked} dimension(s) read, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is that four percent of token headroom is a finding while ninety-one percent of request headroom sits next to it &mdash; the two buckets empty independently and reporting the healthy one is how the finding gets lost. The rest pin the parsers, because the formats are not what a first draft assumes: the reset header is a Go duration string where <code>500ms</code> must not become five hundred minutes, an absent header must stay absent rather than becoming a zero that reads as an empty bucket, and a probe that arrives with no headers at all has to come back as its own state instead of a clean bill of health.",
"test_py_file": "test_openai_rate_limit_headroom.py",
"test_py": '''from openai_rate_limit_headroom import (binding, headroom, parse_count,
                                        parse_reset, scope_note, triples,
                                        verdict)


def test_token_headroom_is_the_finding_while_requests_look_fine():
    # The note in one assertion: 4% of tokens left, 91% of requests, and the
    # report has to name tokens. An average of the two says 47% and says it
    # about nothing. The mixed casing is deliberate: gateways rewrite it.
    parsed = triples({
        "X-RateLimit-Limit-Requests": "10000",
        "X-RateLimit-Remaining-Requests": "9100",
        "X-RateLimit-Reset-Requests": "6m0s",
        "x-ratelimit-limit-tokens": "200000",
        "x-ratelimit-remaining-tokens": "8000",
        "x-ratelimit-reset-tokens": "47s",
    })
    assert verdict("requests", parsed["requests"])[0] == "headroom"
    state, detail = verdict("tokens", parsed["tokens"])
    assert state == "near-exhaustion"
    assert "8000 of 200000 left (4%), resets in 47s" in detail
    assert binding(parsed) == ("tokens", 0.04)


def test_an_empty_bucket_is_reported_before_any_429_arrives():
    state, detail = verdict("tokens", {"limit": 200000, "remaining": 0, "reset": 12.0})
    assert state == "exhausted"
    assert "empty now" in detail


def test_absent_headers_are_not_an_empty_bucket():
    # parse_count must distinguish "the gateway stripped it" from "you are out".
    assert parse_count(None) is None
    assert parse_count("") is None
    assert parse_count("0") == 0
    assert parse_count("1,500,000") == 1500000
    assert parse_count("not a number") is None
    assert headroom({"limit": 200000, "remaining": None}) is None
    assert verdict("tokens", {"limit": 200000, "remaining": None})[0] == "unreadable"


def test_go_duration_resets_parse_and_ms_is_not_minutes():
    assert parse_reset("500ms") == 0.5
    assert parse_reset("6m0s") == 360.0
    assert parse_reset("1h2m3s") == 3723.0
    assert parse_reset("47s") == 47.0
    # Formats this parser does not understand must not half-parse into a number
    # a reader would then act on.
    assert parse_reset("60 seconds") is None
    assert parse_reset("soon") is None
    assert parse_reset("") is None
    assert parse_reset(None) is None


def test_a_probe_with_no_rate_limit_headers_parses_to_nothing():
    # Which main() reports as its own finding rather than as a clean run.
    assert triples({"content-type": "application/json"}) == {}
    assert triples({}) == {}
    assert triples(None) == {}
    assert binding({}) is None


def test_the_project_ceiling_is_the_real_ceiling_when_it_is_lower():
    parsed = triples({
        "x-ratelimit-limit-tokens": "200000",
        "x-ratelimit-remaining-tokens": "150000",
        "x-ratelimit-limit-project-tokens": "150000",
        "x-ratelimit-remaining-project-tokens": "12000",
        "x-ratelimit-reset-project-tokens": "30s",
    })
    assert scope_note(parsed) == [("project", "tokens", 150000, 200000)]
    # And the org triple, read alone, would have said everything was fine.
    assert verdict("tokens", parsed["tokens"])[0] == "headroom"
    assert verdict("project-tokens", parsed["project-tokens"])[0] == "near-exhaustion"
    assert binding(parsed)[0] == "project-tokens"


def test_scope_note_says_nothing_when_there_is_nothing_to_compare():
    assert scope_note(triples({
        "x-ratelimit-limit-tokens": "200000",
        "x-ratelimit-remaining-tokens": "150000",
    })) == []
    assert scope_note({}) == []
    assert scope_note(None) == []
''',
"test_js_file": "openai-rate-limit-headroom.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { binding, headroom, parseCount, parseReset, scopeNote, triples, verdict }
  from './openai-rate-limit-headroom.mjs';

test('token headroom is the finding while requests look fine', () => {
  const parsed = triples({
    'X-RateLimit-Limit-Requests': '10000',
    'X-RateLimit-Remaining-Requests': '9100',
    'X-RateLimit-Reset-Requests': '6m0s',
    'x-ratelimit-limit-tokens': '200000',
    'x-ratelimit-remaining-tokens': '8000',
    'x-ratelimit-reset-tokens': '47s',
  });
  assert.equal(verdict('requests', parsed.requests)[0], 'headroom');
  const [state, detail] = verdict('tokens', parsed.tokens);
  assert.equal(state, 'near-exhaustion');
  assert.match(detail, /8000 of 200000 left \\(4%\\), resets in 47s/);
  assert.deepEqual(binding(parsed), ['tokens', 0.04]);
});

test('an empty bucket is reported before any 429 arrives', () => {
  const [state, detail] = verdict('tokens', { limit: 200000, remaining: 0, reset: 12 });
  assert.equal(state, 'exhausted');
  assert.match(detail, /empty now/);
});

test('absent headers are not an empty bucket', () => {
  assert.equal(parseCount(null), null);
  assert.equal(parseCount(''), null);
  assert.equal(parseCount('0'), 0);
  assert.equal(parseCount('1,500,000'), 1500000);
  assert.equal(parseCount('not a number'), null);
  assert.equal(headroom({ limit: 200000, remaining: null }), null);
  assert.equal(verdict('tokens', { limit: 200000, remaining: null })[0], 'unreadable');
});

test('go duration resets parse and ms is not minutes', () => {
  assert.equal(parseReset('500ms'), 0.5);
  assert.equal(parseReset('6m0s'), 360);
  assert.equal(parseReset('1h2m3s'), 3723);
  assert.equal(parseReset('47s'), 47);
  assert.equal(parseReset('60 seconds'), null);
  assert.equal(parseReset('soon'), null);
  assert.equal(parseReset(''), null);
  assert.equal(parseReset(null), null);
});

test('a probe with no rate limit headers parses to nothing', () => {
  assert.deepEqual(triples({ 'content-type': 'application/json' }), {});
  assert.deepEqual(triples({}), {});
  assert.deepEqual(triples(null), {});
  assert.equal(binding({}), null);
});

test('a fetch Headers object is read the same way as a plain object', () => {
  const h = new Headers({ 'x-ratelimit-limit-tokens': '100',
                          'x-ratelimit-remaining-tokens': '5' });
  assert.equal(verdict('tokens', triples(h).tokens)[0], 'near-exhaustion');
});

test('the project ceiling is the real ceiling when it is lower', () => {
  const parsed = triples({
    'x-ratelimit-limit-tokens': '200000',
    'x-ratelimit-remaining-tokens': '150000',
    'x-ratelimit-limit-project-tokens': '150000',
    'x-ratelimit-remaining-project-tokens': '12000',
    'x-ratelimit-reset-project-tokens': '30s',
  });
  assert.deepEqual(scopeNote(parsed), [['project', 'tokens', 150000, 200000]]);
  assert.equal(verdict('tokens', parsed.tokens)[0], 'headroom');
  assert.equal(verdict('project-tokens', parsed['project-tokens'])[0], 'near-exhaustion');
  assert.equal(binding(parsed)[0], 'project-tokens');
});

test('scopeNote says nothing when there is nothing to compare', () => {
  assert.deepEqual(scopeNote(triples({
    'x-ratelimit-limit-tokens': '200000',
    'x-ratelimit-remaining-tokens': '150000',
  })), []);
  assert.deepEqual(scopeNote({}), []);
  assert.deepEqual(scopeNote(null), []);
});
''',
"faq": [
 ("Does the probe itself use up rate limit?",
  "It consumes a request against the model-list endpoint's limiter, and no inference quota at all: no tokens are generated and nothing is billed. That is why GET /v1/models is the probe rather than a one-token completion. Run it once a minute at most and it is invisible; run it in a tight loop and you are the traffic spike you were trying to predict."),
 ("Why not just catch the 429 and read the headers off that?",
  "Because by then it has happened. The headers come back on successful responses too, which is the entire point of this note: the signal that would have told you a fortnight ago is attached to every 200 you have ever received. Logging them on the error path only is a system that can explain outages and never prevent them."),
 ("What is a sensible floor?",
  "Twenty percent is a starting point, not a rule. The right number is a function of how spiky your traffic is: a workload whose peak is three times its mean needs far more headroom than one that runs flat all day. Watch the ratio at your busiest hour for a week and set the floor where a normal spike would still fit underneath it."),
 ("The headers are missing entirely. Is that good or bad?",
  "Bad, and worth chasing before anything else here. Corporate proxies, API gateways and LLM routers strip response headers they do not recognise, and Retry-After travels the same path as x-ratelimit-*. If they are not reaching your process you have no forward-looking signal and no correct backoff either, so a 429 becomes a guess in both directions."),
 ("Does Anthropic work the same way?",
  "The mechanism is the same and the shape is different. Anthropic returns four header triples rather than two, and it also publishes the configured limits on a GET, so you can read the ceilings without probing at all. Naming which of its three limiters emptied is a separate exercise, covered in the sibling note on limiter identification."),
],
"related": [REL_LIMITER, REL_QUOTA, REL_NO_SPEND_LIMIT],
"citations": [CITE_OAI_RATE, CITE_OAI_MODELS, CITE_OAI_PROJECT_RATE, CITE_OAI_ADMIN],
},
{
"slug": "rate-limit-429-limiter-unidentified",
"title": "429s are retried blindly without reading which limit hit",
"description": "Anthropic enforces three independent limiters and a fourth header that mirrors the tightest. A handler that catches 429 and sleeps discards all four.",
"h1": "429s are retried blindly without reading which limit hit",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic-ratelimit-tokens-remaining", "anthropic 429 rate_limit_error",
             "anthropic rpm itpm otpm", "GET /v1/organizations/rate_limits",
             "which rate limit did I hit anthropic"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_API_KEY for the probe and ANTHROPIC_ADMIN_KEY for the configured limits.",
"lead": "The handler is four lines long and it has been in production for a year. Catch the 429, sleep, retry, give up after three. It works, in the sense that the process does not crash. It has also never once told anybody which of three separate limiters emptied, because the answer was in the response headers and the handler caught an exception class instead of reading a response.",
"short_answer": """<p>Anthropic does not have a TPM limit. Every model group carries <strong>three</strong> limiters that empty independently &mdash; requests per minute, input tokens per minute, output tokens per minute &mdash; and each has its own header triple: <code>anthropic-ratelimit-requests-limit</code> / <code>-remaining</code> / <code>-reset</code>, and the same for <code>-input-tokens-</code> and <code>-output-tokens-</code>.</p>
<p>There is a fourth triple, <code>anthropic-ratelimit-tokens-*</code>, and it is not a fourth limiter. It reports whichever token limit is currently <em>most restrictive</em>. So its <code>-limit</code> value equals either the input ceiling or the output ceiling, and matching it back to the named triples is the platform telling you which bucket it thinks is binding.</p>
<p>Then read the configured numbers rather than guessing them: <code>GET /v1/organizations/rate_limits</code> with an Admin key returns each <code>model_group</code> with its <code>{type, value}</code> pairs for all three limiters.</p>""",
"problem": """<p>A 429 from Anthropic carries a message that names the limit that was exceeded, a <code>retry-after</code> header saying how long to wait, and three <code>-remaining</code> counters showing exactly how much of each bucket was left. A handler written as <code>except APIStatusError: sleep(1); retry()</code> receives all of it and keeps none of it. What reaches your logs is the string "429", and from a string that says 429 there is no way back to whether you sent too many requests, too much prompt, or asked for too much generation &mdash; three problems with three unrelated fixes.</p>
<p>So the incident review reaches for the only lever anybody can name. Concurrency comes down, because concurrency is the knob everyone has. Sometimes that helps, when requests per minute really was the binding limiter. Often it does nothing at all, because the bucket that emptied was output tokens and fewer workers generating the same volume of text saturate it just as fast. Nobody can tell which happened, so the next incident is debugged the same way.</p>""",
"why": """<p><strong>Three limiters, not one, and they are per model group.</strong> RPM, ITPM and OTPM are enforced by separate token buckets that refill continuously, and the docs are explicit that you hit whichever empties first. A model group can be saturated on output while its input bucket is barely touched. There is no single number that summarises that, which is why there is no single number in the headers.</p>
<p><strong>The aggregate triple is a pointer, not a limit.</strong> <code>anthropic-ratelimit-tokens-*</code> reports the most restrictive token limit in effect. It is the one header that already contains the answer to "which one", and it gives it up only if you compare its <code>-limit</code> value against the input and output ceilings. Logging it on its own is logging a number with no referent.</p>
<p><strong>The probe's headers describe the endpoint you probed.</strong> <code>GET /v1/models</code> counts against a limiter group, and it is not the group your inference traffic uses. The headers prove the plumbing works and show you the shape; the per-model-group ceilings have to come from <code>GET /v1/organizations/rate_limits</code>, which is why this script wants both credentials and says which number came from where.</p>
<p><strong>Token counters are rounded.</strong> The <code>-remaining</code> values on the token buckets are rounded to the nearest thousand. On a large ceiling that is noise; on a small one it means a bucket reading zero may not be quite empty and one reading a thousand may be. Treat them as a shape, not as an accounting record.</p>
<p><strong>Separate groups exist that nobody thinks to check.</strong> Message Batches, the Token Counting API, the Files API, agent skills and web search each carry their own limiters. A 429 from a batch submission is not the same bucket as a 429 from a message, and a handler that treats every 429 as "the model is busy" will back off inference because a file upload was throttled.</p>
<p><strong>A spend cap wears the same status.</strong> An Anthropic 429 whose <code>error.details.error_code</code> is <code>enforced_spend_limit_reached</code> arrives with <em>no</em> <code>retry-after</code> at all and will not clear until the month rolls over. Identifying the limiter and identifying <a href="/llm/quota-exhausted-not-rate-limited/">a billing wall</a> are two different reads of the same status code, and both have to happen before anything sleeps.</p>""",
"steps": [
 {"h": "Probe once, read all four triples",
  "body": """<p><code>GET /v1/models</code> with a workspace key and the <code>anthropic-version</code> header. It generates nothing and bills nothing, and it comes back with the full <code>anthropic-ratelimit-*</code> set. Do not manufacture a 429 to inspect one: driving a production bucket to zero to see the error is an outage you scheduled.</p>"""},
 {"h": "Match the aggregate ceiling back to a named one",
  "body": """<p>Compare <code>anthropic-ratelimit-tokens-limit</code> against <code>-input-tokens-limit</code> and <code>-output-tokens-limit</code>. Equal to one of them means that is the tighter ceiling and the platform is telling you so. Equal to neither means a third, lower limit is in play &mdash; a workspace override, or a different limiter group than the one you probed &mdash; and that is worth knowing before anything else.</p>"""},
 {"h": "Find the emptiest bucket separately",
  "body": """<p>The tightest <em>ceiling</em> and the emptiest <em>bucket</em> are different questions. A generous request limit that you have burned through will 429 you long before a tight token limit you are nowhere near. Compute <code>remaining / limit</code> for each named triple and report the minimum next to the aggregate's answer; when they disagree, both belong in the report.</p>"""},
 {"h": "Read the configured limits per model group",
  "body": """<p><code>GET /v1/organizations/rate_limits</code> with an Admin key returns every <code>model_group</code> and its <code>limits[]</code> array of <code>{type, value}</code>. A limiter type missing from that array is not unlimited &mdash; it inherits &mdash; so record it as unpublished rather than as absent. Reading a missing number as "no ceiling" is how a team decides it has room it does not have.</p>"""},
 {"h": "Print the header names the handler should have been logging",
  "body": """<p>The output of this script is a list: the exact headers that arrived on this response and that a 429 handler should record every time. That is the repair. Changing your retry code is a deploy with an owner, so the script names the headers and stops, and it never touches <code>max_retries</code> or the client's backoff.</p>"""},
],
"verify": """<p>Re-run after the handler starts logging the triples. Then the next 429 arrives already labelled, and this script becomes something you stop needing.</p>
<pre><code class="language-bash">python3 anthropic_limiter_identify.py
# identified       output-tokens is the emptiest named bucket at 3% remaining,
#                  and the aggregate ceiling mirrors output-tokens.
# claude-sonnet-5   rpm 4000  itpm 5000000  otpm 1000000
# log these on every 429: anthropic-ratelimit-output-tokens-remaining, retry-after, ...</code></pre>""",
"code_intro": "Two GETs: one probe with <code>ANTHROPIC_API_KEY</code>, a workspace key, and one Admin call with <code>ANTHROPIC_ADMIN_KEY</code> for the configured ceilings. Anthropic has no read-only tier on the data plane, so the workspace key <em>could</em> send a message; this script is written not to and makes exactly one request with it. Seven pure functions: the header reader, an RFC 3339 clock, the ratio, the match that names the bucket, the minimum that finds the emptiest one, the verdict that reports when those two disagree, and the fold of the Admin response that keeps an unpublished limiter distinct from an absent one.",
"py_file": "anthropic_limiter_identify.py",
"py": '''"""Name which Anthropic rate limiter is binding, instead of catching 429.

Read only. Two GET requests and nothing else. ANTHROPIC_API_KEY is a workspace
key used for a single probe against /v1/models, which generates no tokens and
bills nothing; ANTHROPIC_ADMIN_KEY is an Admin API key (sk-ant-admin...) used
for the configured limits, because /v1/organizations/* rejects a workspace key.

Anthropic has no read-only tier on the data plane: the same workspace key that
reads /v1/models could send a message. This script is trusted not to rather
than prevented from it, so it makes exactly one call with that credential.

Nothing here provokes a 429. Draining a production bucket to inspect the error
is an outage you scheduled on purpose.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_limiter_identify")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# The three limiters that empty independently. "tokens" is deliberately not in
# this tuple: it is not a fourth bucket, it is a report on whichever of the two
# token buckets is currently most restrictive.
NAMED = ("requests", "input-tokens", "output-tokens")
AGGREGATE = "tokens"

LIMITER_TYPES = ("requests_per_minute", "input_tokens_per_minute",
                 "output_tokens_per_minute")

FINDINGS = ("disagreement", "aggregate-unmatched", "headers-missing")


def parse_count(value):
    """Read a limit or remaining header as an integer. Pure, None if unreadable.

    None and zero must stay distinct. Zero means the bucket is empty; None means
    nothing told us, and reporting a stripped header as an empty limiter sends
    somebody chasing a throttle that is not there.
    """
    if value is None:
        return None
    text = str(value).strip().replace(",", "").replace("_", "")
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def read_triples(headers):
    """Parse the anthropic-ratelimit-* triples off one response. Pure.

    Case-insensitive, because a proxy that rewrites header casing should not be
    able to turn a working probe into a report of missing headers.
    """
    lower = {}
    for name, value in dict(headers or {}).items():
        lower[str(name).strip().lower()] = value

    out = {}
    for name in NAMED + (AGGREGATE,):
        limit_h = "anthropic-ratelimit-%s-limit" % name
        remaining_h = "anthropic-ratelimit-%s-remaining" % name
        reset_h = "anthropic-ratelimit-%s-reset" % name
        if limit_h not in lower and remaining_h not in lower:
            continue
        reset = lower.get(reset_h)
        out[name] = {"limit": parse_count(lower.get(limit_h)),
                     "remaining": parse_count(lower.get(remaining_h)),
                     "reset": str(reset).strip() if reset is not None else None}
    return out


def seconds_until(value, now):
    """Seconds until an RFC 3339 reset stamp. Pure; the caller supplies now.

    Returns None when the stamp cannot be read rather than guessing. A reset
    window is a number a reader will act on, and half-parsing one is worse than
    printing that it was unreadable.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for suffix in ("Z", "z"):
        if text.endswith(suffix):
            text = text[:-1] + "+00:00"
            break
    try:
        when = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    return (when - now).total_seconds()


def share_left(triple):
    """remaining / limit for one triple, or None. Pure."""
    if not isinstance(triple, dict):
        return None
    limit = triple.get("limit")
    remaining = triple.get("remaining")
    if limit is None or remaining is None or limit <= 0:
        return None
    return max(0.0, min(1.0, remaining / float(limit)))


def mirrors(parsed):
    """Which named token limiter the aggregate triple is reporting. Pure.

    anthropic-ratelimit-tokens-* is documented as the most restrictive token
    limit currently in effect, so its ceiling equals the input ceiling or the
    output ceiling. Matching it back is the platform naming the binding bucket
    for you; nothing else in the response does that.
    """
    aggregate = (parsed or {}).get(AGGREGATE) or {}
    limit = aggregate.get("limit")
    if limit is None:
        return "no-aggregate"
    matched = []
    for name in ("input-tokens", "output-tokens"):
        other = (parsed or {}).get(name) or {}
        if other.get("limit") is not None and other.get("limit") == limit:
            matched.append(name)
    if len(matched) == 2:
        return "both"
    if len(matched) == 1:
        return matched[0]
    return "unmatched"


def emptiest(parsed):
    """The named bucket with the least left. Pure. Returns (name, share).

    The aggregate is excluded on purpose: it duplicates one of the named
    buckets, and letting it compete would report the same limiter twice under
    two names and hide whichever one it is not mirroring.
    """
    best = None
    for name in NAMED:
        share = share_left((parsed or {}).get(name) or {})
        if share is None:
            continue
        if best is None or share < best[1]:
            best = (name, share)
    return best


def verdict(parsed):
    """Say which limiter is binding, and when the two answers disagree. Pure."""
    if not parsed:
        return ("headers-missing",
                "no anthropic-ratelimit-* headers reached this process, so a "
                "429 here would arrive with nothing to classify it by and "
                "retry-after would be missing too")
    scarce = emptiest(parsed)
    if scarce is None:
        return ("unreadable",
                "the named triples arrived without a usable limit and "
                "remaining pair, so there is no ratio to compare")

    name, share = scarce
    shape = "%s is the emptiest named bucket at %.0f%% remaining" % (name, share * 100)
    mirror = mirrors(parsed)

    if mirror == "no-aggregate":
        return ("no-aggregate",
                "%s, and the aggregate anthropic-ratelimit-tokens triple is "
                "absent, so the platform's own view of the most restrictive "
                "token limit is not available on this response." % shape)
    if mirror == "unmatched":
        return ("aggregate-unmatched",
                "%s, but the aggregate token ceiling matches neither the input "
                "nor the output ceiling. A third and lower limit is in effect: "
                "a workspace override, or a different limiter group than the "
                "one this probe touched." % shape)
    if mirror == "both":
        return ("identified",
                "%s, and the aggregate ceiling equals both token ceilings, so "
                "input and output share a number here and only the remaining "
                "counters tell them apart." % shape)
    if mirror == name:
        return ("identified",
                "%s, and the aggregate ceiling mirrors %s. The tightest ceiling "
                "and the emptiest bucket are the same limiter." % (shape, mirror))
    return ("disagreement",
            "%s, while the aggregate ceiling mirrors %s. The tightest ceiling "
            "and the emptiest bucket are different limiters, so a handler that "
            "records only one of them will name the wrong cause."
            % (shape, mirror))


def configured(payload):
    """Fold GET /v1/organizations/rate_limits into {model_group: {type: value}}. Pure.

    A limiter type missing from a group's limits[] is not unlimited: it
    inherits. It is recorded as None and printed as unpublished, never as
    absent, because "no number" read as "no ceiling" is how a team convinces
    itself it has headroom it was never granted.
    """
    out = {}
    for entry in (payload or {}).get("data") or []:
        group = str(entry.get("model_group") or "").strip()
        if not group:
            continue
        row = out.setdefault(group, dict.fromkeys(LIMITER_TYPES))
        for limit in entry.get("limits") or []:
            kind = str(limit.get("type") or "").strip()
            if kind not in row:
                continue
            try:
                row[kind] = int(limit.get("value"))
            except (TypeError, ValueError):
                row[kind] = None
    return out


def log_headers(headers):
    """The header names a 429 handler should be recording. Pure.

    Built from what actually arrived rather than from a hardcoded list, so the
    printed repair does not tell a reader to log a header their gateway is
    stripping. This list is the whole output of the script that matters.
    """
    lower = set()
    for name in dict(headers or {}):
        lower.add(str(name).strip().lower())
    wanted = set()
    for name in NAMED + (AGGREGATE,):
        for suffix in ("limit", "remaining", "reset"):
            candidate = "anthropic-ratelimit-%s-%s" % (name, suffix)
            if candidate in lower:
                wanted.add(candidate)
    for extra in ("retry-after", "request-id", "anthropic-organization-id"):
        if extra in lower:
            wanted.add(extra)
    return sorted(wanted)


def probe(session):
    """One cheap real call with the workspace key. Generates nothing."""
    r = session.get(API + "/models", timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: ANTHROPIC_API_KEY must be a "
                         "workspace or project key" % r.status_code)
    if r.status_code == 429:
        log.warning("the probe itself was rate limited; the headers below "
                    "describe the bucket that rejected it")
        return r.headers
    r.raise_for_status()
    return r.headers


def admin_limits(admin_key):
    """GET the configured per-model-group limits. Returns {} if no admin key."""
    if not admin_key:
        return {}
    s = requests.Session()
    s.headers.update({"x-api-key": admin_key, "anthropic-version": VERSION})
    r = s.get(API + "/organizations/rate_limits", timeout=60)
    if r.status_code in (401, 403):
        log.warning("%d from the Admin API: /v1/organizations/* needs an Admin "
                    "key (sk-ant-admin...). Continuing on headers alone.",
                    r.status_code)
        return {}
    r.raise_for_status()
    return configured(r.json())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--show-all", action="store_true",
                    help="also print every triple, not only the verdict")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY (a workspace key) for the probe")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION})

    headers = probe(session)
    parsed = read_triples(headers)
    state, detail = verdict(parsed)
    line = "%-20s %s" % (state, detail)
    if state in FINDINGS:
        log.warning(line)
    else:
        log.info(line)

    now = dt.datetime.now(dt.timezone.utc)
    if args.show_all:
        for name in sorted(parsed):
            triple = parsed[name]
            until = seconds_until(triple.get("reset"), now)
            log.info("  %-14s limit %s, remaining %s, resets %s", name,
                     triple.get("limit"), triple.get("remaining"),
                     "in %.0fs" % until if until is not None else "unreadable")

    groups = admin_limits(os.environ.get("ANTHROPIC_ADMIN_KEY"))
    for group in sorted(groups):
        row = groups[group]
        log.info("  %-24s rpm %s  itpm %s  otpm %s", group,
                 row["requests_per_minute"] if row["requests_per_minute"] is not None
                 else "unpublished",
                 row["input_tokens_per_minute"] if row["input_tokens_per_minute"] is not None
                 else "unpublished",
                 row["output_tokens_per_minute"] if row["output_tokens_per_minute"] is not None
                 else "unpublished")
    if not groups:
        log.info("  no configured limits read; set ANTHROPIC_ADMIN_KEY to name "
                 "the ceilings per model group rather than only the probe's")

    names = log_headers(headers)
    if names:
        log.warning("  repair: record these on every 429 instead of catching a "
                    "broad status error: %s", ", ".join(names))
        log.warning("  repair: branch before sleeping. No retry-after plus "
                    "error.details.error_code of enforced_spend_limit_reached "
                    "is a billing stop, not a throttle, and will not clear.")
    else:
        log.warning("  repair: no rate-limit headers arrived at all. Check the "
                    "proxy or gateway in front of api.anthropic.com and let "
                    "the anthropic-ratelimit-* and retry-after headers through.")

    return 1 if state in FINDINGS else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-limiter-identify.mjs",
"js": '''/**
 * Name which Anthropic rate limiter is binding, instead of catching 429.
 *
 * Read only. Two GET requests and nothing else. ANTHROPIC_API_KEY is a
 * workspace key used for a single probe against /v1/models, which generates no
 * tokens and bills nothing; ANTHROPIC_ADMIN_KEY is an Admin API key used for
 * the configured limits, because /v1/organizations/* rejects a workspace key.
 *
 * Nothing here provokes a 429.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// The three limiters that empty independently. "tokens" is not a fourth bucket:
// it reports whichever of the two token buckets is most restrictive.
const NAMED = ['requests', 'input-tokens', 'output-tokens'];
const AGGREGATE = 'tokens';

const LIMITER_TYPES = ['requests_per_minute', 'input_tokens_per_minute',
                       'output_tokens_per_minute'];

const FINDINGS = new Set(['disagreement', 'aggregate-unmatched', 'headers-missing']);

/**
 * Read a limit or remaining header as an integer. Pure, null if unreadable.
 * null and 0 stay distinct: 0 is an empty bucket, null is a stripped header.
 */
export function parseCount(value) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim().replace(/[,_]/g, '');
  if (!text) return null;
  const n = Number(text);
  return Number.isInteger(n) ? n : null;
}

/** Parse the anthropic-ratelimit-* triples off one response. Pure. */
export function readTriples(headers) {
  const lower = new Map();
  const entries = typeof headers?.entries === 'function'
    ? [...headers.entries()] : Object.entries(headers ?? {});
  for (const [name, value] of entries) lower.set(String(name).trim().toLowerCase(), value);

  const out = {};
  for (const name of [...NAMED, AGGREGATE]) {
    const limitH = `anthropic-ratelimit-${name}-limit`;
    const remainingH = `anthropic-ratelimit-${name}-remaining`;
    const resetH = `anthropic-ratelimit-${name}-reset`;
    if (!lower.has(limitH) && !lower.has(remainingH)) continue;
    const reset = lower.get(resetH);
    out[name] = {
      limit: parseCount(lower.get(limitH)),
      remaining: parseCount(lower.get(remainingH)),
      reset: reset === null || reset === undefined ? null : String(reset).trim(),
    };
  }
  return out;
}

/**
 * Seconds until an RFC 3339 reset stamp. Pure; the caller supplies now.
 * Returns null when the stamp cannot be read rather than guessing.
 */
export function secondsUntil(value, now) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim();
  if (!text) return null;
  const when = Date.parse(text);
  if (Number.isNaN(when)) return null;
  return (when - now.getTime()) / 1000;
}

/** remaining / limit for one triple, or null. Pure. */
export function shareLeft(triple) {
  if (!triple || typeof triple !== 'object') return null;
  const { limit, remaining } = triple;
  if (limit === null || limit === undefined) return null;
  if (remaining === null || remaining === undefined) return null;
  if (limit <= 0) return null;
  return Math.max(0, Math.min(1, remaining / limit));
}

/**
 * Which named token limiter the aggregate triple is reporting. Pure.
 * The aggregate ceiling equals the input ceiling or the output ceiling, so
 * matching it back is the platform naming the binding bucket for you.
 */
export function mirrors(parsed) {
  const limit = (parsed ?? {})[AGGREGATE]?.limit;
  if (limit === null || limit === undefined) return 'no-aggregate';
  const matched = [];
  for (const name of ['input-tokens', 'output-tokens']) {
    const other = (parsed ?? {})[name]?.limit;
    if (other !== null && other !== undefined && other === limit) matched.push(name);
  }
  if (matched.length === 2) return 'both';
  if (matched.length === 1) return matched[0];
  return 'unmatched';
}

/**
 * The named bucket with the least left. Pure. Returns [name, share].
 * The aggregate is excluded: it duplicates one of the named buckets.
 */
export function emptiest(parsed) {
  let best = null;
  for (const name of NAMED) {
    const share = shareLeft((parsed ?? {})[name]);
    if (share === null) continue;
    if (best === null || share < best[1]) best = [name, share];
  }
  return best;
}

/** Say which limiter is binding, and when the two answers disagree. Pure. */
export function verdict(parsed) {
  if (!parsed || Object.keys(parsed).length === 0) {
    return ['headers-missing',
      'no anthropic-ratelimit-* headers reached this process, so a 429 here ' +
      'would arrive with nothing to classify it by and retry-after would be ' +
      'missing too'];
  }
  const scarce = emptiest(parsed);
  if (scarce === null) {
    return ['unreadable',
      'the named triples arrived without a usable limit and remaining pair, ' +
      'so there is no ratio to compare'];
  }
  const [name, share] = scarce;
  const shape = `${name} is the emptiest named bucket at ` +
                `${(share * 100).toFixed(0)}% remaining`;
  const mirror = mirrors(parsed);

  if (mirror === 'no-aggregate') {
    return ['no-aggregate',
      `${shape}, and the aggregate anthropic-ratelimit-tokens triple is absent, ` +
      "so the platform's own view of the most restrictive token limit is not " +
      'available on this response.'];
  }
  if (mirror === 'unmatched') {
    return ['aggregate-unmatched',
      `${shape}, but the aggregate token ceiling matches neither the input nor ` +
      'the output ceiling. A third and lower limit is in effect: a workspace ' +
      'override, or a different limiter group than the one this probe touched.'];
  }
  if (mirror === 'both') {
    return ['identified',
      `${shape}, and the aggregate ceiling equals both token ceilings, so input ` +
      'and output share a number here and only the remaining counters tell ' +
      'them apart.'];
  }
  if (mirror === name) {
    return ['identified',
      `${shape}, and the aggregate ceiling mirrors ${mirror}. The tightest ` +
      'ceiling and the emptiest bucket are the same limiter.'];
  }
  return ['disagreement',
    `${shape}, while the aggregate ceiling mirrors ${mirror}. The tightest ` +
    'ceiling and the emptiest bucket are different limiters, so a handler that ' +
    'records only one of them will name the wrong cause.'];
}

/**
 * Fold GET /v1/organizations/rate_limits into {model_group: {type: value}}. Pure.
 * A limiter type missing from limits[] inherits rather than being unlimited, so
 * it is recorded as null and printed as unpublished.
 */
export function configured(payload) {
  const out = {};
  for (const entry of (payload ?? {}).data ?? []) {
    const group = String(entry.model_group ?? '').trim();
    if (!group) continue;
    if (!out[group]) {
      out[group] = {};
      for (const t of LIMITER_TYPES) out[group][t] = null;
    }
    for (const limit of entry.limits ?? []) {
      const kind = String(limit.type ?? '').trim();
      if (!(kind in out[group])) continue;
      const value = Number(limit.value);
      out[group][kind] = Number.isInteger(value) ? value : null;
    }
  }
  return out;
}

/**
 * The header names a 429 handler should be recording. Pure.
 * Built from what actually arrived, so the printed repair never tells a reader
 * to log a header their gateway is stripping.
 */
export function logHeaders(headers) {
  const lower = new Set();
  const entries = typeof headers?.entries === 'function'
    ? [...headers.entries()] : Object.entries(headers ?? {});
  for (const [name] of entries) lower.add(String(name).trim().toLowerCase());

  const wanted = new Set();
  for (const name of [...NAMED, AGGREGATE]) {
    for (const suffix of ['limit', 'remaining', 'reset']) {
      const candidate = `anthropic-ratelimit-${name}-${suffix}`;
      if (lower.has(candidate)) wanted.add(candidate);
    }
  }
  for (const extra of ['retry-after', 'request-id', 'anthropic-organization-id']) {
    if (lower.has(extra)) wanted.add(extra);
  }
  return [...wanted].sort();
}

/** One cheap real call with the workspace key. Generates nothing. */
async function probe(key) {
  const res = await fetch(`${API}/models`, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: ANTHROPIC_API_KEY must be a ` +
                    'workspace or project key');
  }
  if (res.status === 429) {
    console.warn('the probe itself was rate limited; the headers below describe ' +
                 'the bucket that rejected it');
    return res.headers;
  }
  if (!res.ok) throw new Error(`${res.status} from /v1/models`);
  return res.headers;
}

async function adminLimits(adminKey) {
  if (!adminKey) return {};
  const res = await fetch(`${API}/organizations/rate_limits`, {
    headers: { 'x-api-key': adminKey, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    console.warn(`${res.status} from the Admin API: /v1/organizations/* needs an ` +
                 'Admin key (sk-ant-admin...). Continuing on headers alone.');
    return {};
  }
  if (!res.ok) throw new Error(`${res.status} from /v1/organizations/rate_limits`);
  return configured(await res.json());
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY (a workspace key) for the probe');
    process.exitCode = 2;
    return;
  }
  const showAll = process.env.SHOW_ALL === '1';

  const headers = await probe(key);
  const parsed = readTriples(headers);
  const [state, detail] = verdict(parsed);
  const line = `${state.padEnd(20)} ${detail}`;
  if (FINDINGS.has(state)) console.warn(line); else console.log(line);

  const now = new Date();
  if (showAll) {
    for (const name of Object.keys(parsed).sort()) {
      const triple = parsed[name];
      const until = secondsUntil(triple.reset, now);
      console.log(`  ${name.padEnd(14)} limit ${triple.limit}, remaining ` +
                  `${triple.remaining}, resets ` +
                  `${until === null ? 'unreadable' : `in ${until.toFixed(0)}s`}`);
    }
  }

  const groups = await adminLimits(process.env.ANTHROPIC_ADMIN_KEY);
  const names = Object.keys(groups).sort();
  for (const group of names) {
    const row = groups[group];
    const show = (v) => (v === null ? 'unpublished' : String(v));
    console.log(`  ${group.padEnd(24)} rpm ${show(row.requests_per_minute)}  ` +
                `itpm ${show(row.input_tokens_per_minute)}  ` +
                `otpm ${show(row.output_tokens_per_minute)}`);
  }
  if (names.length === 0) {
    console.log('  no configured limits read; set ANTHROPIC_ADMIN_KEY to name the ' +
                "ceilings per model group rather than only the probe's");
  }

  const toLog = logHeaders(headers);
  if (toLog.length > 0) {
    console.warn('  repair: record these on every 429 instead of catching a broad ' +
                 `status error: ${toLog.join(', ')}`);
    console.warn('  repair: branch before sleeping. No retry-after plus ' +
                 'error.details.error_code of enforced_spend_limit_reached is a ' +
                 'billing stop, not a throttle, and will not clear.');
  } else {
    console.warn('  repair: no rate-limit headers arrived at all. Check the proxy ' +
                 'or gateway in front of api.anthropic.com and let the ' +
                 'anthropic-ratelimit-* and retry-after headers through.');
  }

  process.exitCode = FINDINGS.has(state) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the whole mechanism: an aggregate ceiling of four hundred thousand against an input ceiling of five million and an output ceiling of four hundred thousand, which identifies output as the limiter without any inference at all. The second is the case that makes the note worth writing &mdash; the tightest ceiling and the emptiest bucket are different limiters, and a report that prints one of them is confidently wrong. The rest hold the honest gaps open: an aggregate matching neither ceiling is a third limit rather than a bug to smooth over, an unpublished limiter is not an unlimited one, and a response with no headers at all is a finding rather than a pass.",
"test_py_file": "test_anthropic_limiter_identify.py",
"test_py": '''import datetime as dt

from anthropic_limiter_identify import (configured, emptiest, log_headers,
                                        mirrors, parse_count, read_triples,
                                        seconds_until, share_left, verdict)

NOW = dt.datetime(2026, 8, 30, 12, 0, 0, tzinfo=dt.timezone.utc)


def test_the_aggregate_ceiling_names_the_binding_limiter():
    # Sonnet-shaped numbers: ITPM five million, OTPM four hundred thousand. The
    # aggregate equals the output ceiling, which is Anthropic telling you which
    # bucket is tightest without anything having to infer it.
    parsed = read_triples({
        "anthropic-ratelimit-requests-limit": "4000",
        "anthropic-ratelimit-requests-remaining": "3600",
        "anthropic-ratelimit-input-tokens-limit": "5000000",
        "anthropic-ratelimit-input-tokens-remaining": "4000000",
        "anthropic-ratelimit-output-tokens-limit": "400000",
        "anthropic-ratelimit-output-tokens-remaining": "12000",
        "anthropic-ratelimit-tokens-limit": "400000",
        "anthropic-ratelimit-tokens-remaining": "12000",
    })
    assert mirrors(parsed) == "output-tokens"
    assert emptiest(parsed) == ("output-tokens", 0.03)
    state, detail = verdict(parsed)
    assert state == "identified"
    assert "output-tokens is the emptiest named bucket at 3% remaining" in detail


def test_the_tightest_ceiling_and_the_emptiest_bucket_can_disagree():
    # The request bucket is nearly gone while the output ceiling is the lower
    # number. Reporting either alone names the wrong cause.
    parsed = read_triples({
        "anthropic-ratelimit-requests-limit": "4000",
        "anthropic-ratelimit-requests-remaining": "40",
        "anthropic-ratelimit-input-tokens-limit": "5000000",
        "anthropic-ratelimit-input-tokens-remaining": "4900000",
        "anthropic-ratelimit-output-tokens-limit": "400000",
        "anthropic-ratelimit-output-tokens-remaining": "380000",
        "anthropic-ratelimit-tokens-limit": "400000",
        "anthropic-ratelimit-tokens-remaining": "380000",
    })
    state, detail = verdict(parsed)
    assert state == "disagreement"
    assert "requests is the emptiest named bucket at 1% remaining" in detail
    assert "mirrors output-tokens" in detail


def test_an_aggregate_matching_neither_ceiling_is_a_third_limit():
    parsed = read_triples({
        "anthropic-ratelimit-requests-limit": "4000",
        "anthropic-ratelimit-requests-remaining": "3900",
        "anthropic-ratelimit-input-tokens-limit": "5000000",
        "anthropic-ratelimit-input-tokens-remaining": "4900000",
        "anthropic-ratelimit-output-tokens-limit": "400000",
        "anthropic-ratelimit-output-tokens-remaining": "390000",
        "anthropic-ratelimit-tokens-limit": "150000",
        "anthropic-ratelimit-tokens-remaining": "150000",
    })
    assert mirrors(parsed) == "unmatched"
    assert verdict(parsed)[0] == "aggregate-unmatched"


def test_no_headers_is_a_finding_and_not_a_pass():
    assert read_triples({"content-type": "application/json"}) == {}
    assert read_triples(None) == {}
    state, detail = verdict({})
    assert state == "headers-missing"
    assert "retry-after would be missing too" in detail
    assert log_headers({"content-type": "application/json"}) == []


def test_the_aggregate_never_competes_to_be_the_emptiest_bucket():
    # Otherwise the same limiter is reported twice under two names, and the
    # bucket the aggregate is not mirroring disappears from the report.
    parsed = {"requests": {"limit": 100, "remaining": 90},
              "output-tokens": {"limit": 1000, "remaining": 500},
              "tokens": {"limit": 1000, "remaining": 1}}
    assert emptiest(parsed) == ("output-tokens", 0.5)


def test_absent_and_empty_are_different_readings():
    assert parse_count(None) is None
    assert parse_count("") is None
    assert parse_count("0") == 0
    assert parse_count("2,000,000") == 2000000
    assert parse_count("lots") is None
    assert share_left({"limit": 100, "remaining": None}) is None
    assert share_left({"limit": 0, "remaining": 0}) is None
    assert verdict({"requests": {"limit": None, "remaining": None}})[0] == "unreadable"


def test_rfc3339_resets_parse_and_unreadable_ones_stay_unreadable():
    assert seconds_until("2026-08-30T12:00:30Z", NOW) == 30.0
    assert seconds_until("2026-08-30T12:00:30+00:00", NOW) == 30.0
    assert seconds_until("in a bit", NOW) is None
    assert seconds_until("", NOW) is None
    assert seconds_until(None, NOW) is None


def test_an_unpublished_limiter_is_not_an_unlimited_one():
    payload = {"data": [
        {"model_group": "claude-sonnet-5", "limits": [
            {"type": "requests_per_minute", "value": 4000},
            {"type": "input_tokens_per_minute", "value": 5000000},
            {"type": "output_tokens_per_minute", "value": 1000000}]},
        {"model_group": "message-batches", "limits": [
            {"type": "requests_per_minute", "value": 100}]},
    ]}
    folded = configured(payload)
    assert folded["claude-sonnet-5"]["output_tokens_per_minute"] == 1000000
    # Absent from limits[] means it inherits, so it must read as None and get
    # printed as unpublished rather than silently becoming zero or infinity.
    assert folded["message-batches"]["input_tokens_per_minute"] is None
    assert folded["message-batches"]["requests_per_minute"] == 100
    assert configured({}) == {}
    assert configured(None) == {}


def test_the_repair_lists_only_headers_that_actually_arrived():
    names = log_headers({
        "Anthropic-RateLimit-Output-Tokens-Remaining": "12000",
        "anthropic-ratelimit-tokens-limit": "400000",
        "Retry-After": "12",
        "request-id": "req_fake123",
        "content-type": "application/json",
    })
    assert names == ["anthropic-ratelimit-output-tokens-remaining",
                     "anthropic-ratelimit-tokens-limit",
                     "request-id", "retry-after"]
''',
"test_js_file": "anthropic-limiter-identify.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { configured, emptiest, logHeaders, mirrors, parseCount, readTriples,
         secondsUntil, shareLeft, verdict }
  from './anthropic-limiter-identify.mjs';

const NOW = new Date('2026-08-30T12:00:00Z');

test('the aggregate ceiling names the binding limiter', () => {
  const parsed = readTriples({
    'anthropic-ratelimit-requests-limit': '4000',
    'anthropic-ratelimit-requests-remaining': '3600',
    'anthropic-ratelimit-input-tokens-limit': '5000000',
    'anthropic-ratelimit-input-tokens-remaining': '4000000',
    'anthropic-ratelimit-output-tokens-limit': '400000',
    'anthropic-ratelimit-output-tokens-remaining': '12000',
    'anthropic-ratelimit-tokens-limit': '400000',
    'anthropic-ratelimit-tokens-remaining': '12000',
  });
  assert.equal(mirrors(parsed), 'output-tokens');
  assert.deepEqual(emptiest(parsed), ['output-tokens', 0.03]);
  const [state, detail] = verdict(parsed);
  assert.equal(state, 'identified');
  assert.match(detail, /output-tokens is the emptiest named bucket at 3% remaining/);
});

test('the tightest ceiling and the emptiest bucket can disagree', () => {
  const parsed = readTriples({
    'anthropic-ratelimit-requests-limit': '4000',
    'anthropic-ratelimit-requests-remaining': '40',
    'anthropic-ratelimit-input-tokens-limit': '5000000',
    'anthropic-ratelimit-input-tokens-remaining': '4900000',
    'anthropic-ratelimit-output-tokens-limit': '400000',
    'anthropic-ratelimit-output-tokens-remaining': '380000',
    'anthropic-ratelimit-tokens-limit': '400000',
    'anthropic-ratelimit-tokens-remaining': '380000',
  });
  const [state, detail] = verdict(parsed);
  assert.equal(state, 'disagreement');
  assert.match(detail, /requests is the emptiest named bucket at 1% remaining/);
  assert.match(detail, /mirrors output-tokens/);
});

test('an aggregate matching neither ceiling is a third limit', () => {
  const parsed = readTriples({
    'anthropic-ratelimit-requests-limit': '4000',
    'anthropic-ratelimit-requests-remaining': '3900',
    'anthropic-ratelimit-input-tokens-limit': '5000000',
    'anthropic-ratelimit-input-tokens-remaining': '4900000',
    'anthropic-ratelimit-output-tokens-limit': '400000',
    'anthropic-ratelimit-output-tokens-remaining': '390000',
    'anthropic-ratelimit-tokens-limit': '150000',
    'anthropic-ratelimit-tokens-remaining': '150000',
  });
  assert.equal(mirrors(parsed), 'unmatched');
  assert.equal(verdict(parsed)[0], 'aggregate-unmatched');
});

test('no headers is a finding and not a pass', () => {
  assert.deepEqual(readTriples({ 'content-type': 'application/json' }), {});
  assert.deepEqual(readTriples(null), {});
  const [state, detail] = verdict({});
  assert.equal(state, 'headers-missing');
  assert.match(detail, /retry-after would be missing too/);
  assert.deepEqual(logHeaders({ 'content-type': 'application/json' }), []);
});

test('the aggregate never competes to be the emptiest bucket', () => {
  const parsed = {
    requests: { limit: 100, remaining: 90 },
    'output-tokens': { limit: 1000, remaining: 500 },
    tokens: { limit: 1000, remaining: 1 },
  };
  assert.deepEqual(emptiest(parsed), ['output-tokens', 0.5]);
});

test('absent and empty are different readings', () => {
  assert.equal(parseCount(null), null);
  assert.equal(parseCount(''), null);
  assert.equal(parseCount('0'), 0);
  assert.equal(parseCount('2,000,000'), 2000000);
  assert.equal(parseCount('lots'), null);
  assert.equal(shareLeft({ limit: 100, remaining: null }), null);
  assert.equal(shareLeft({ limit: 0, remaining: 0 }), null);
  assert.equal(verdict({ requests: { limit: null, remaining: null } })[0], 'unreadable');
});

test('rfc3339 resets parse and unreadable ones stay unreadable', () => {
  assert.equal(secondsUntil('2026-08-30T12:00:30Z', NOW), 30);
  assert.equal(secondsUntil('2026-08-30T12:00:30+00:00', NOW), 30);
  assert.equal(secondsUntil('in a bit', NOW), null);
  assert.equal(secondsUntil('', NOW), null);
  assert.equal(secondsUntil(null, NOW), null);
});

test('an unpublished limiter is not an unlimited one', () => {
  const folded = configured({ data: [
    { model_group: 'claude-sonnet-5', limits: [
      { type: 'requests_per_minute', value: 4000 },
      { type: 'input_tokens_per_minute', value: 5000000 },
      { type: 'output_tokens_per_minute', value: 1000000 }] },
    { model_group: 'message-batches', limits: [
      { type: 'requests_per_minute', value: 100 }] },
  ] });
  assert.equal(folded['claude-sonnet-5'].output_tokens_per_minute, 1000000);
  assert.equal(folded['message-batches'].input_tokens_per_minute, null);
  assert.equal(folded['message-batches'].requests_per_minute, 100);
  assert.deepEqual(configured({}), {});
  assert.deepEqual(configured(null), {});
});

test('the repair lists only headers that actually arrived', () => {
  assert.deepEqual(logHeaders({
    'Anthropic-RateLimit-Output-Tokens-Remaining': '12000',
    'anthropic-ratelimit-tokens-limit': '400000',
    'Retry-After': '12',
    'request-id': 'req_fake123',
    'content-type': 'application/json',
  }), ['anthropic-ratelimit-output-tokens-remaining',
       'anthropic-ratelimit-tokens-limit',
       'request-id', 'retry-after']);
});
''',
"faq": [
 ("Why is there no single TPM number on Anthropic?",
  "Because input and output are metered separately and empty at different rates. Input tokens per minute is roughly five times output tokens per minute at every tier, so a summarisation workload and a generation workload run out of completely different things. One combined number would have to be the minimum of the two, which is exactly what the aggregate anthropic-ratelimit-tokens header already is."),
 ("The aggregate matches neither ceiling. What now?",
  "Something lower than both is in effect. The usual cause is a workspace-level override, which can be set below the organization limit and which the aggregate faithfully reports. The other cause is that you probed a different limiter group than you think: batches, token counting, files and web search each carry their own. Read GET /v1/organizations/rate_limits and compare per model group before assuming a bug."),
 ("Can the script tell me which limiter caused yesterday's 429s?",
  "No, and nothing can. Neither provider exposes a request log, so there is no endpoint that will return the status codes or error bodies of calls you already made. That is precisely why the repair is to start recording the headers now: the only version of this question that has an answer is the one asked about a 429 you captured."),
 ("Should the script just retry until it sees a 429 and read that?",
  "No. Deliberately draining a production token bucket to inspect the error is an outage you scheduled, and it costs your colleagues the same headroom it costs you. Every header this note reads is present on a successful response, so one call to GET /v1/models answers the question without spending anything."),
 ("Does the retry-after header make the branching unnecessary?",
  "It makes the sleeping correct, not the diagnosis. retry-after tells you when the bucket refills; it does not tell you which bucket, so it cannot tell you whether to reduce concurrency, cache the prefix or shorten the answers. And its absence is itself a signal: a 429 with no retry-after and error.details.error_code of enforced_spend_limit_reached is a monthly spend cap that will not clear until the month does."),
],
"related": [REL_ITPM, REL_OTPM, REL_QUOTA],
"citations": [CITE_CL_RATE, CITE_CL_RATE_API, CITE_CL_ERRORS, CITE_CL_USAGE_API],
},
{
"slug": "itpm-exhausted-uncached-input",
"title": "ITPM runs out because uncached input is never cached",
"description": "Cache reads do not count toward the input limiter. A full ITPM bucket next to a zero cache-read share is a throughput problem caching fixes, not a discount.",
"h1": "ITPM runs out because uncached input is never cached",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic input tokens per minute limit", "itpm rate limit claude",
             "cache_read_input_tokens does not count toward itpm",
             "uncached_input_tokens", "anthropic 429 input tokens remaining zero"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_ADMIN_KEY, an Admin API key provisioned read-only.",
"lead": "The 429s arrive in the afternoon and the team does what teams do: fewer workers, longer sleeps, a queue in front. None of it moves. The request counter was never the thing that ran out. What ran out was input tokens per minute, and the reason is that the same forty thousand tokens of system prompt and tool schemas are sent uncached on every single call, and every one of those tokens is charged against the limiter.",
"short_answer": """<p>Read the per-minute usage buckets with an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={T-4h}&amp;bucket_width=1m&amp;limit=240&amp;group_by[]=model</code>. Per minute and per model, the number charged against ITPM is <code>uncached_input_tokens + cache_creation.ephemeral_5m_input_tokens + cache_creation.ephemeral_1h_input_tokens</code>.</p>
<p><code>cache_read_input_tokens</code> is <strong>not</strong> in that sum. Cache reads do not count toward the input limiter on any current model &mdash; the one exception is Claude Haiku 3.5, where they do. Compare the peak minute against <code>input_tokens_per_minute</code> from <code>GET /v1/organizations/rate_limits</code>.</p>
<p>A peak at the ceiling with a cache-read share near zero is the finding, and the conclusion is not the one the caching notes reach. Caching here buys <em>throughput</em>: at an eighty percent read share the same ITPM ceiling carries five times the total input.</p>""",
"problem": """<p>Rate limits are debugged with the knob everybody has, which is concurrency. It is the right knob when requests per minute is what emptied, and it does nothing whatsoever when input tokens per minute is. Six workers sending forty-thousand-token prompts and three workers sending the same prompts twice as often put identical pressure on ITPM; the queue in front of them just makes the pressure arrive more politely.</p>
<p>Underneath, the shape is almost always the same. A long, stable prefix &mdash; tool definitions, a system prompt, a few-shot block, a document that does not change between turns &mdash; is re-sent in full on every call. It is the part of the request nobody thinks about, because it was written once and works. And it is the part that dominates the token count, so the limiter is being spent almost entirely on text the model has already been shown.</p>""",
"why": """<p><strong>Only uncached input is charged against ITPM.</strong> <code>input_tokens</code> and <code>cache_creation_input_tokens</code> count; <code>cache_read_input_tokens</code> does not. That single exclusion is why this note is about a limiter rather than about a bill. Every token you move behind a cache breakpoint is a token that stops competing for the ceiling, and the effect on throughput is a multiplier rather than a percentage.</p>
<p><strong>Claude Haiku 3.5 is the exception and it inverts the advice.</strong> On that model cache reads <em>do</em> count toward ITPM. Caching still lowers the bill there and buys no headroom at all, so a script that applies one rule to every model tells half its readers to make a change that will not help them. The check has to branch on the model id, and this one does.</p>
<p><strong>The peak minute is the finding; the hourly mean is not.</strong> Buckets a minute wide exist because the limiter is enforced by the minute. A workload that saturates ITPM for ninety seconds every hour looks entirely comfortable at hourly resolution and is 429ing its users twice an hour. Fold to the maximum, never to the average.</p>
<p><strong>This is not the caching cost finding wearing different clothes.</strong> <a href="/llm/prompt-caching-never-used/">Caching never switched on</a> and <a href="/llm/cache-writes-with-no-reads/">writes with no reads</a> both end in a dollar figure and are true whether or not you are anywhere near a limit. This one is true whether or not caching would save you money: a workload can be comfortably profitable, already priced in, and still be unable to grow because its input limiter is full.</p>
<p><strong>The usage report has no request count.</strong> <code>GET /v1/organizations/usage_report/messages</code> returns token sums per bucket and nothing else, so nothing here is expressed per request. That is a real limit on what can be claimed: the script can say the input limiter is full and cannot tell you how many calls filled it.</p>
<p><strong>Note the <code>input_tokens</code> trap in the response object.</strong> On a live message, <code>usage.input_tokens</code> is only the tail after the last cache breakpoint. Total input is <code>cache_read + cache_creation + input_tokens</code>. Reading the field by its name and calling it the prompt size is how a caching workload gets reported as a tiny one.</p>""",
"steps": [
 {"h": "Pull minute buckets, not hour buckets",
  "body": """<p><code>bucket_width=1m</code> with <code>starting_at</code> floored to a minute boundary. Up to 1,440 buckets come back, and the endpoint paginates on <code>next_page</code>. Four hours across the busy part of the day is usually enough to find the peak; a full day is fine and is 1,440 buckets exactly.</p>"""},
 {"h": "Charge the right tokens against the limiter",
  "body": """<p><code>uncached_input_tokens</code> plus both members of the nested <code>cache_creation</code> object. <code>cache_read_input_tokens</code> is excluded &mdash; except on Claude Haiku 3.5, where it is included. A parser that looks for a flat <code>cache_creation_input_tokens</code> finds nothing and under-charges a caching workload into looking idle.</p>"""},
 {"h": "Take the maximum, and remember which minute it was",
  "body": """<p>Per model, keep the largest charged minute and the cache-read count from that same minute. Both numbers have to come from one minute: a peak from Tuesday compared against a read share from Sunday produces a confident sentence about nothing.</p>"""},
 {"h": "Compare against the published ITPM for the model group",
  "body": """<p><code>GET /v1/organizations/rate_limits</code> returns <code>model_group</code> entries whose <code>limits[]</code> carry <code>{type: "input_tokens_per_minute", value}</code>. Match the model id to its group by longest prefix. A group with no published ITPM is reported as unpublished, not as unlimited &mdash; the limiter still exists, you were simply not told the number.</p>"""},
 {"h": "Say what caching would buy here, in throughput",
  "body": """<p>The multiplier is <code>1 / (1 - read_share)</code>. Zero percent read share means the ceiling carries exactly your uncached input; eighty percent means it carries five times as much. Print that, print where the breakpoint goes &mdash; the render order is tools, then system, then messages &mdash; and stop. Moving a breakpoint changes what the model sees, and that is a deploy with an owner.</p>"""},
],
"verify": """<p>Add the breakpoint, wait an hour, and read the same window again. The charged peak should fall while total input holds steady; that difference is the headroom you just bought.</p>
<pre><code class="language-bash">python3 anthropic_itpm_headroom.py --minutes 240
# itpm-saturated-uncached  claude-sonnet-5  peak minute charged 4,880,000 token(s)
#   against an ITPM of 5,000,000 (98%); cache reads were 2% of that minute's input
#   at this read share the ceiling carries 1.0x your total input; at 80% it carries 5.0x
# 3 model(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "Two GETs against the Admin API and no writes. It wants <code>ANTHROPIC_ADMIN_KEY</code>, which can and should be provisioned read-only, because <code>/v1/organizations/*</code> rejects a workspace key outright. Six pure functions: the model test that decides whether cache reads are charged, the accumulator that reads the nested <code>cache_creation</code> object, the fold that keeps peaks rather than means, the group match, the multiplier, and a verdict that separates three different reasons an input limiter can be full.",
"py_file": "anthropic_itpm_headroom.py",
"py": '''"""Report an Anthropic input limiter that is full of uncached input.

Read only. Two GET requests and nothing else against the Admin API, which needs
an Admin API key (sk-ant-admin...); a workspace key is rejected by every
/v1/organizations/* path, and an Admin key can be provisioned read-only.

The repair is printed, never performed. Adding a cache_control breakpoint
changes what the model is shown on every request, which is a deploy.

The messages usage report carries token sums and no request count, so nothing
here is expressed per request. This script can say the input limiter is full.
It cannot say how many calls filled it.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_itpm_headroom")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# The one family where cache reads are charged against the input limiter. On
# every other current model a cache read is free of ITPM, which is the entire
# mechanism this script reports on, so the exception has to be explicit rather
# than a footnote in the prose.
CACHE_READS_CHARGED = ("claude-3-5-haiku",)

FINDINGS = ("itpm-saturated-uncached", "itpm-saturated-already-cached",
            "itpm-saturated-cache-counts")


def cache_reads_count(model):
    """Do cache reads count toward this model's ITPM? Pure.

    True only for Claude Haiku 3.5. Getting this backwards tells a reader to
    add a breakpoint that will not buy them a single token of headroom.
    """
    name = str(model or "").strip().lower()
    return any(name.startswith(prefix) for prefix in CACHE_READS_CHARGED)


def chargeable_input(result, model):
    """Tokens in one usage result that count against ITPM. Pure.

    cache_creation is a nested object holding ephemeral_5m_input_tokens and
    ephemeral_1h_input_tokens. A parser looking for a flat
    cache_creation_input_tokens sums zero and reports a heavily cached workload
    as one that writes nothing.
    """
    if not isinstance(result, dict):
        return 0
    total = 0
    for field in ("uncached_input_tokens",):
        try:
            total += int(result.get(field) or 0)
        except (TypeError, ValueError):
            pass
    creation = result.get("cache_creation") or {}
    for field in ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"):
        try:
            total += int(creation.get(field) or 0)
        except (TypeError, ValueError):
            pass
    if cache_reads_count(model):
        try:
            total += int(result.get("cache_read_input_tokens") or 0)
        except (TypeError, ValueError):
            pass
    return total


def peaks(buckets):
    """Fold one-minute buckets into per-model peaks. Pure.

    The peak is the finding and the mean is not. ITPM is enforced by the
    minute, so a workload that saturates for ninety seconds an hour has a
    comfortable hourly average and a queue of 429s inside it.
    """
    per_minute = {}
    for bucket in buckets or []:
        stamp = str(bucket.get("starting_at") or bucket.get("start_time") or "")
        for result in bucket.get("results") or []:
            model = str(result.get("model") or "").strip() or "all models"
            row = per_minute.setdefault((model, stamp), {"charged": 0, "read": 0})
            row["charged"] += chargeable_input(result, model)
            try:
                row["read"] += int(result.get("cache_read_input_tokens") or 0)
            except (TypeError, ValueError):
                pass

    out = {}
    for (model, stamp), row in per_minute.items():
        stats = out.setdefault(model, {"peak": 0, "peak_at": None, "peak_read": 0,
                                       "minutes": 0, "charged": 0, "read": 0})
        stats["minutes"] += 1
        stats["charged"] += row["charged"]
        stats["read"] += row["read"]
        if row["charged"] > stats["peak"]:
            stats["peak"] = row["charged"]
            stats["peak_at"] = stamp
            stats["peak_read"] = row["read"]
    return out


def cache_read_share(stats, model):
    """Share of the peak minute's input that arrived as a cache read. Pure.

    On a model where reads are charged the peak already contains them, so the
    denominator differs. Using one denominator for both models reports the
    Haiku 3.5 case at half its real share.
    """
    if not isinstance(stats, dict):
        return None
    read = int(stats.get("peak_read") or 0)
    charged = int(stats.get("peak") or 0)
    total = charged if cache_reads_count(model) else charged + read
    if total <= 0:
        return None
    return min(1.0, read / float(total))


def headroom_multiplier(share):
    """How much total input one ITPM ceiling carries at a given read share. Pure.

    1 / (1 - share). At zero the ceiling carries exactly your uncached input;
    at 0.8 it carries five times your total input. This is the throughput
    argument for caching and it is a different argument from the discount.
    """
    if share is None:
        return None
    bounded = max(0.0, min(0.99, float(share)))
    return 1.0 / (1.0 - bounded)


def itpm_by_group(payload):
    """{model_group: input_tokens_per_minute} from the rate-limits response. Pure.

    A group whose limits[] omits the type is recorded as None. Absent means it
    inherits, never that it is unlimited, and reading a missing number as no
    ceiling is how a team decides it has room nobody granted it.
    """
    out = {}
    for entry in (payload or {}).get("data") or []:
        group = str(entry.get("model_group") or "").strip()
        if not group:
            continue
        out.setdefault(group, None)
        for limit in entry.get("limits") or []:
            if str(limit.get("type") or "").strip() != "input_tokens_per_minute":
                continue
            try:
                out[group] = int(limit.get("value"))
            except (TypeError, ValueError):
                out[group] = None
    return out


def limit_for(groups, model):
    """The ITPM for the group a model id belongs to, or None. Pure.

    Longest prefix wins, so a dated id resolves to the most specific group that
    claims it rather than to whichever one the dict happened to yield first.
    """
    name = str(model or "").strip().lower()
    if not name:
        return None
    best_key, best_len = None, -1
    for group in (groups or {}):
        candidate = str(group).strip().lower()
        if not candidate:
            continue
        if name == candidate or name.startswith(candidate):
            if len(candidate) > best_len:
                best_key, best_len = group, len(candidate)
    if best_key is None:
        return None
    return (groups or {}).get(best_key)


def verdict(model, stats, limit, floor=0.9, watch=0.6, min_minutes=10,
            cached_enough=0.15):
    """Classify one model's input limiter. Pure. Returns (state, detail).

    Three ways an ITPM ceiling can be full, and they do not share a repair:
    the prefix is uncached and caching buys headroom; the prefix is already
    cached and only a limit increase is left; or the model charges cache reads
    so caching was never going to buy headroom in the first place.
    """
    minutes = int((stats or {}).get("minutes") or 0)
    if minutes < min_minutes:
        return ("too-few-buckets",
                "%d minute(s) of traffic in the window, under the floor of %d. "
                "A peak taken over this little is noise." % (minutes, min_minutes))
    if limit is None or limit <= 0:
        return ("no-limit-published",
                "no input_tokens_per_minute is published for this model's group, "
                "so there is no ceiling to compare the peak against. The limiter "
                "still exists; the number was simply not returned.")

    peak = int(stats.get("peak") or 0)
    used = peak / float(limit)
    share = cache_read_share(stats, model)
    shape = ("peak minute charged %d token(s) against an ITPM of %d (%.0f%%); "
             "cache reads were %.0f%% of that minute's input"
             % (peak, limit, used * 100, (share or 0.0) * 100))

    if used < watch:
        return ("itpm-headroom", shape + ".")
    if used < floor:
        return ("itpm-approaching",
                shape + ". Thin enough that an ordinary spike lands on the "
                "input limiter rather than on the request limiter.")
    if cache_reads_count(model):
        return ("itpm-saturated-cache-counts",
                shape + ". This model charges cache reads against ITPM, so "
                "caching lowers the bill here and buys no headroom at all. The "
                "levers are a shorter prefix or a higher limit.")
    if share is not None and share >= cached_enough:
        return ("itpm-saturated-already-cached",
                shape + ". The prefix is already being read back, so a "
                "breakpoint has little left to give. What remains is a limit "
                "increase, or splitting the workload across model groups.")
    return ("itpm-saturated-uncached",
            shape + ". Cache reads are not charged against ITPM on this model, "
            "so covering the stable prefix buys throughput and not only a "
            "discount.")


def window_start(minutes):
    """Floor to the minute: starting_at must sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    return (now - dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def read_buckets(session, path, params):
    """Walk the paginated usage report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=int, default=240,
                    help="minutes of one-minute buckets to read (max 1440)")
    ap.add_argument("--target-share", type=float, default=0.8,
                    help="cache-read share to quote the multiplier at (default 0.8)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print models with headroom left")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    minutes = max(1, min(int(args.minutes), 1440))
    session = requests.Session()
    session.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    params = {"starting_at": window_start(minutes), "bucket_width": "1m",
              "limit": minutes, "group_by[]": ["model"]}
    stats = peaks(read_buckets(session, "/organizations/usage_report/messages", params))
    if not stats:
        log.info("no message usage in the last %d minute(s)", minutes)
        return 0

    groups = itpm_by_group(get(session, "/organizations/rate_limits"))

    checked = 0
    bad = 0
    for model in sorted(stats, key=lambda m: -stats[m]["peak"]):
        row = stats[model]
        limit = limit_for(groups, model)
        state, detail = verdict(model, row, limit)
        checked += 1
        line = "%-30s %-28s %s" % (state, model, detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            if state == "itpm-saturated-uncached":
                share = cache_read_share(row, model) or 0.0
                now_x = headroom_multiplier(share)
                then_x = headroom_multiplier(args.target_share)
                log.warning("  at this read share the ceiling carries %.1fx your "
                            "total input; at %.0f%% it would carry %.1fx",
                            now_x, args.target_share * 100, then_x)
                log.warning("  repair: put a cache_control breakpoint at the end "
                            "of the stable prefix. The render order is tools, "
                            "then system, then messages, so the breakpoint goes "
                            "after the last thing that never changes.")
            else:
                log.warning("  repair: request an input_tokens_per_minute "
                            "increase for this model group, or move latency "
                            "tolerant work onto the Message Batches API, which "
                            "is metered by its own limiter group.")
        elif state in ("itpm-approaching", "no-limit-published"):
            log.warning(line)
        elif args.show_all:
            log.info(line)

    log.info("%d model(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-itpm-headroom.mjs",
"js": '''/**
 * Report an Anthropic input limiter that is full of uncached input.
 *
 * Read only. Two GET requests and nothing else against the Admin API, which
 * needs an Admin API key (sk-ant-admin...); a workspace key is rejected by
 * every /v1/organizations/* path. The repair is printed, never performed.
 *
 * The messages usage report carries token sums and no request count, so
 * nothing here is expressed per request.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// The one family where cache reads are charged against the input limiter.
const CACHE_READS_CHARGED = ['claude-3-5-haiku'];

const FINDINGS = new Set(['itpm-saturated-uncached', 'itpm-saturated-already-cached',
                          'itpm-saturated-cache-counts']);

/**
 * Do cache reads count toward this model's ITPM? Pure.
 * True only for Claude Haiku 3.5; getting it backwards tells a reader to add a
 * breakpoint that buys them no headroom.
 */
export function cacheReadsCount(model) {
  const name = String(model ?? '').trim().toLowerCase();
  return CACHE_READS_CHARGED.some((prefix) => name.startsWith(prefix));
}

/**
 * Tokens in one usage result that count against ITPM. Pure.
 * cache_creation is nested; a flat read sums zero and reports a heavily cached
 * workload as one that writes nothing.
 */
export function chargeableInput(result, model) {
  if (!result || typeof result !== 'object') return 0;
  const num = (v) => (Number.isFinite(Number(v)) ? Math.trunc(Number(v)) : 0);
  const creation = result.cache_creation ?? {};
  let total = num(result.uncached_input_tokens)
    + num(creation.ephemeral_5m_input_tokens)
    + num(creation.ephemeral_1h_input_tokens);
  if (cacheReadsCount(model)) total += num(result.cache_read_input_tokens);
  return total;
}

/**
 * Fold one-minute buckets into per-model peaks. Pure.
 * The peak is the finding and the mean is not: ITPM is enforced by the minute.
 */
export function peaks(buckets) {
  const perMinute = new Map();
  for (const bucket of buckets ?? []) {
    const stamp = String(bucket.starting_at ?? bucket.start_time ?? '');
    for (const result of bucket.results ?? []) {
      const model = String(result.model ?? '').trim() || 'all models';
      const key = `${model}\\u0000${stamp}`;
      const row = perMinute.get(key) ?? { model, charged: 0, read: 0 };
      row.charged += chargeableInput(result, model);
      const read = Number(result.cache_read_input_tokens ?? 0);
      row.read += Number.isFinite(read) ? Math.trunc(read) : 0;
      perMinute.set(key, row);
    }
  }

  const out = {};
  for (const [key, row] of perMinute) {
    const stamp = key.slice(key.indexOf('\\u0000') + 1);
    const stats = out[row.model] ?? { peak: 0, peak_at: null, peak_read: 0,
                                      minutes: 0, charged: 0, read: 0 };
    stats.minutes += 1;
    stats.charged += row.charged;
    stats.read += row.read;
    if (row.charged > stats.peak) {
      stats.peak = row.charged;
      stats.peak_at = stamp;
      stats.peak_read = row.read;
    }
    out[row.model] = stats;
  }
  return out;
}

/**
 * Share of the peak minute's input that arrived as a cache read. Pure.
 * The denominator differs on a model that charges reads, because the peak
 * already contains them.
 */
export function cacheReadShare(stats, model) {
  if (!stats || typeof stats !== 'object') return null;
  const read = Number(stats.peak_read ?? 0);
  const charged = Number(stats.peak ?? 0);
  const total = cacheReadsCount(model) ? charged : charged + read;
  if (!(total > 0)) return null;
  return Math.min(1, read / total);
}

/**
 * How much total input one ITPM ceiling carries at a given read share. Pure.
 * 1 / (1 - share): at 0.8 the same ceiling carries five times the input.
 */
export function headroomMultiplier(share) {
  if (share === null || share === undefined) return null;
  const bounded = Math.max(0, Math.min(0.99, Number(share)));
  return 1 / (1 - bounded);
}

/**
 * {model_group: input_tokens_per_minute} from the rate-limits response. Pure.
 * An omitted type is recorded as null: absent means it inherits, not unlimited.
 */
export function itpmByGroup(payload) {
  const out = {};
  for (const entry of (payload ?? {}).data ?? []) {
    const group = String(entry.model_group ?? '').trim();
    if (!group) continue;
    if (!(group in out)) out[group] = null;
    for (const limit of entry.limits ?? []) {
      if (String(limit.type ?? '').trim() !== 'input_tokens_per_minute') continue;
      const value = Number(limit.value);
      out[group] = Number.isInteger(value) ? value : null;
    }
  }
  return out;
}

/** The ITPM for the group a model id belongs to, or null. Pure. Longest prefix wins. */
export function limitFor(groups, model) {
  const name = String(model ?? '').trim().toLowerCase();
  if (!name) return null;
  let bestKey = null;
  let bestLen = -1;
  for (const group of Object.keys(groups ?? {})) {
    const candidate = group.trim().toLowerCase();
    if (!candidate) continue;
    if (name === candidate || name.startsWith(candidate)) {
      if (candidate.length > bestLen) { bestKey = group; bestLen = candidate.length; }
    }
  }
  if (bestKey === null) return null;
  const value = groups[bestKey];
  return value === undefined ? null : value;
}

/**
 * Classify one model's input limiter. Pure. Returns [state, detail].
 * Three ways an ITPM ceiling can be full, and they do not share a repair.
 */
export function verdict(model, stats, limit, {
  floor = 0.9, watch = 0.6, minMinutes = 10, cachedEnough = 0.15,
} = {}) {
  const minutes = Number((stats ?? {}).minutes ?? 0);
  if (minutes < minMinutes) {
    return ['too-few-buckets',
      `${minutes} minute(s) of traffic in the window, under the floor of ` +
      `${minMinutes}. A peak taken over this little is noise.`];
  }
  if (limit === null || limit === undefined || limit <= 0) {
    return ['no-limit-published',
      "no input_tokens_per_minute is published for this model's group, so there " +
      'is no ceiling to compare the peak against. The limiter still exists; the ' +
      'number was simply not returned.'];
  }

  const peak = Number(stats.peak ?? 0);
  const used = peak / limit;
  const share = cacheReadShare(stats, model);
  const shape = `peak minute charged ${peak} token(s) against an ITPM of ` +
    `${limit} (${(used * 100).toFixed(0)}%); cache reads were ` +
    `${((share ?? 0) * 100).toFixed(0)}% of that minute's input`;

  if (used < watch) return ['itpm-headroom', `${shape}.`];
  if (used < floor) {
    return ['itpm-approaching',
      `${shape}. Thin enough that an ordinary spike lands on the input limiter ` +
      'rather than on the request limiter.'];
  }
  if (cacheReadsCount(model)) {
    return ['itpm-saturated-cache-counts',
      `${shape}. This model charges cache reads against ITPM, so caching lowers ` +
      'the bill here and buys no headroom at all. The levers are a shorter ' +
      'prefix or a higher limit.'];
  }
  if (share !== null && share >= cachedEnough) {
    return ['itpm-saturated-already-cached',
      `${shape}. The prefix is already being read back, so a breakpoint has ` +
      'little left to give. What remains is a limit increase, or splitting the ' +
      'workload across model groups.'];
  }
  return ['itpm-saturated-uncached',
    `${shape}. Cache reads are not charged against ITPM on this model, so ` +
    'covering the stable prefix buys throughput and not only a discount.'];
}

/** Floor to the minute: starting_at must sit on a bucket boundary. */
export function windowStart(minutes, now = new Date()) {
  const floored = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
                           now.getUTCHours(), now.getUTCMinutes());
  return new Date(floored - minutes * 60000).toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function get(adminKey, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, one);
  }
  const res = await fetch(url, {
    headers: { 'x-api-key': adminKey, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs an ` +
                    'Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* readBuckets(adminKey, path, params) {
  const q = { ...params };
  for (;;) {
    const page = await get(adminKey, path, q);
    for (const bucket of page.data ?? []) yield bucket;
    if (!page.has_more || !page.next_page) return;
    q.page = page.next_page;
  }
}

async function main() {
  const adminKey = process.env.ANTHROPIC_ADMIN_KEY;
  if (!adminKey) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const minutes = Math.max(1, Math.min(Number(process.env.MINUTES ?? 240), 1440));
  const targetShare = Number(process.env.TARGET_SHARE ?? 0.8);
  const showAll = process.env.SHOW_ALL === '1';

  const collected = [];
  for await (const bucket of readBuckets(adminKey, '/organizations/usage_report/messages',
    { starting_at: windowStart(minutes), bucket_width: '1m', limit: minutes,
      'group_by[]': ['model'] })) {
    collected.push(bucket);
  }
  const stats = peaks(collected);
  const models = Object.keys(stats);
  if (models.length === 0) {
    console.log(`no message usage in the last ${minutes} minute(s)`);
    return;
  }

  const groups = itpmByGroup(await get(adminKey, '/organizations/rate_limits'));

  let bad = 0;
  models.sort((a, b) => stats[b].peak - stats[a].peak);
  for (const model of models) {
    const row = stats[model];
    const limit = limitFor(groups, model);
    const [state, detail] = verdict(model, row, limit);
    const line = `${state.padEnd(30)} ${model.padEnd(28)} ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      if (state === 'itpm-saturated-uncached') {
        const share = cacheReadShare(row, model) ?? 0;
        console.warn(`  at this read share the ceiling carries ` +
                     `${headroomMultiplier(share).toFixed(1)}x your total input; at ` +
                     `${(targetShare * 100).toFixed(0)}% it would carry ` +
                     `${headroomMultiplier(targetShare).toFixed(1)}x`);
        console.warn('  repair: put a cache_control breakpoint at the end of the ' +
                     'stable prefix. The render order is tools, then system, then ' +
                     'messages, so the breakpoint goes after the last thing that ' +
                     'never changes.');
      } else {
        console.warn('  repair: request an input_tokens_per_minute increase for this ' +
                     'model group, or move latency tolerant work onto the Message ' +
                     'Batches API, which is metered by its own limiter group.');
      }
    } else if (state === 'itpm-approaching' || state === 'no-limit-published') {
      console.warn(line);
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${models.length} model(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first two tests are the note and its opposite: an ITPM ceiling at ninety-eight percent with a two percent cache-read share is a caching finding, and the same ceiling at the same ninety-eight percent with an eighty percent read share is not &mdash; there the prefix is already covered and the only lever left is the limit. The third is the exception that would otherwise make the advice wrong for one family: on Claude Haiku 3.5 cache reads are charged against ITPM, so the script has to change both its arithmetic and its recommendation. The rest pin the nested <code>cache_creation</code> read, the fact that peaks are maxima rather than means, and a group with no published number staying unpublished rather than becoming unlimited.",
"test_py_file": "test_anthropic_itpm_headroom.py",
"test_py": '''from anthropic_itpm_headroom import (cache_read_share, cache_reads_count,
                                     chargeable_input, headroom_multiplier,
                                     itpm_by_group, limit_for, peaks, verdict)


def minute(stamp, model, uncached=0, write_5m=0, write_1h=0, read=0):
    """One 1m bucket from GET /v1/organizations/usage_report/messages."""
    return {"starting_at": stamp, "results": [{
        "model": model,
        "uncached_input_tokens": uncached,
        "cache_read_input_tokens": read,
        "cache_creation": {"ephemeral_5m_input_tokens": write_5m,
                           "ephemeral_1h_input_tokens": write_1h},
        "output_tokens": 12000,
    }]}


def test_a_full_input_limiter_with_no_cache_reads_is_the_finding():
    stats = peaks([minute("2026-08-30T14:%02d:00Z" % i, "claude-sonnet-5",
                          uncached=4_880_000 if i == 7 else 900_000,
                          read=100_000 if i == 7 else 0)
                   for i in range(20)])
    state, detail = verdict("claude-sonnet-5", stats["claude-sonnet-5"], 5_000_000)
    assert state == "itpm-saturated-uncached"
    assert "against an ITPM of 5000000 (98%)" in detail
    assert "cache reads were 2% of that minute's input" in detail
    assert "buys throughput and not only a discount" in detail
    # The throughput argument, which is the whole point of the note.
    assert round(headroom_multiplier(0.8), 1) == 5.0
    assert round(headroom_multiplier(0.0), 1) == 1.0


def test_the_same_full_ceiling_with_a_cached_prefix_is_a_different_finding():
    # 98% of ITPM again, but the prefix is already being read back. Telling this
    # reader to add a breakpoint sends them to do work that is already done.
    stats = peaks([minute("2026-08-30T14:%02d:00Z" % i, "claude-sonnet-5",
                          uncached=4_880_000 if i == 3 else 100_000,
                          read=19_520_000 if i == 3 else 0)
                   for i in range(20)])
    state, detail = verdict("claude-sonnet-5", stats["claude-sonnet-5"], 5_000_000)
    assert state == "itpm-saturated-already-cached"
    assert "cache reads were 80% of that minute's input" in detail
    assert "limit increase" in detail


def test_haiku_35_charges_cache_reads_so_caching_buys_no_headroom():
    assert cache_reads_count("claude-3-5-haiku-20241022") is True
    assert cache_reads_count("claude-haiku-4-5-20251001") is False
    assert cache_reads_count("claude-opus-5") is False
    # The read is inside the charged number on that model and outside it here.
    result = {"uncached_input_tokens": 1000, "cache_read_input_tokens": 4000,
              "cache_creation": {"ephemeral_5m_input_tokens": 500}}
    assert chargeable_input(result, "claude-sonnet-5") == 1500
    assert chargeable_input(result, "claude-3-5-haiku-20241022") == 5500

    stats = peaks([minute("2026-08-30T14:%02d:00Z" % i, "claude-3-5-haiku-20241022",
                          uncached=200_000, read=1_800_000) for i in range(20)])
    state, detail = verdict("claude-3-5-haiku-20241022",
                            stats["claude-3-5-haiku-20241022"], 2_000_000)
    assert state == "itpm-saturated-cache-counts"
    assert "buys no headroom at all" in detail


def test_chargeable_input_reads_the_nested_cache_creation_object():
    # The trap: these two fields live inside cache_creation, not at the top.
    assert chargeable_input({"uncached_input_tokens": 100,
                             "cache_creation": {"ephemeral_5m_input_tokens": 7,
                                                "ephemeral_1h_input_tokens": 3}},
                            "claude-opus-5") == 110
    assert chargeable_input({"cache_creation_input_tokens": 999}, "claude-opus-5") == 0
    assert chargeable_input({"uncached_input_tokens": None}, "claude-opus-5") == 0
    assert chargeable_input(None, "claude-opus-5") == 0


def test_the_peak_minute_survives_an_otherwise_quiet_window():
    # One saturated minute in twenty. The mean would read 24% of the ceiling and
    # report a comfortable workload that is 429ing every hour.
    stats = peaks([minute("2026-08-30T14:%02d:00Z" % i, "claude-opus-5",
                          uncached=4_800_000 if i == 11 else 200_000)
                   for i in range(20)])
    row = stats["claude-opus-5"]
    assert row["peak"] == 4_800_000
    assert row["peak_at"] == "2026-08-30T14:11:00Z"
    assert row["minutes"] == 20
    assert verdict("claude-opus-5", row, 5_000_000)[0] == "itpm-saturated-uncached"


def test_a_window_too_short_to_have_a_peak_gets_no_verdict():
    stats = peaks([minute("2026-08-30T14:00:00Z", "claude-opus-5", uncached=9_000_000)])
    assert verdict("claude-opus-5", stats["claude-opus-5"], 5_000_000)[0] == "too-few-buckets"


def test_an_unpublished_ceiling_is_not_an_absent_one():
    groups = itpm_by_group({"data": [
        {"model_group": "claude-sonnet-5",
         "limits": [{"type": "input_tokens_per_minute", "value": 5000000},
                    {"type": "output_tokens_per_minute", "value": 1000000}]},
        {"model_group": "claude-fable-5",
         "limits": [{"type": "output_tokens_per_minute", "value": 300000}]},
    ]})
    assert groups["claude-sonnet-5"] == 5000000
    assert groups["claude-fable-5"] is None
    assert limit_for(groups, "claude-sonnet-5-20260101") == 5000000
    assert limit_for(groups, "claude-fable-5") is None
    assert limit_for(groups, "claude-opus-5") is None
    assert verdict("claude-fable-5", {"minutes": 60, "peak": 9}, None)[0] == "no-limit-published"


def test_longest_prefix_wins_when_two_groups_could_claim_a_model():
    groups = {"claude-haiku": 1000, "claude-haiku-4-5": 5_000_000}
    assert limit_for(groups, "claude-haiku-4-5-20251001") == 5_000_000
    assert limit_for(groups, "") is None
    assert limit_for({}, "claude-opus-5") is None
    assert cache_read_share({"peak": 0, "peak_read": 0}, "claude-opus-5") is None
    assert headroom_multiplier(None) is None
''',
"test_js_file": "anthropic-itpm-headroom.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cacheReadShare, cacheReadsCount, chargeableInput, headroomMultiplier,
         itpmByGroup, limitFor, peaks, verdict }
  from './anthropic-itpm-headroom.mjs';

/** One 1m bucket from GET /v1/organizations/usage_report/messages. */
function minute(stamp, model, { uncached = 0, write5m = 0, write1h = 0, read = 0 } = {}) {
  return { starting_at: stamp, results: [{
    model,
    uncached_input_tokens: uncached,
    cache_read_input_tokens: read,
    cache_creation: { ephemeral_5m_input_tokens: write5m,
                      ephemeral_1h_input_tokens: write1h },
    output_tokens: 12000,
  }] };
}

const stamp = (i) => `2026-08-30T14:${String(i).padStart(2, '0')}:00Z`;

test('a full input limiter with no cache reads is the finding', () => {
  const stats = peaks([...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-sonnet-5',
      { uncached: i === 7 ? 4880000 : 900000, read: i === 7 ? 100000 : 0 })));
  const [state, detail] = verdict('claude-sonnet-5', stats['claude-sonnet-5'], 5000000);
  assert.equal(state, 'itpm-saturated-uncached');
  assert.match(detail, /against an ITPM of 5000000 \\(98%\\)/);
  assert.match(detail, /cache reads were 2% of that minute's input/);
  assert.match(detail, /buys throughput and not only a discount/);
  assert.equal(headroomMultiplier(0.8).toFixed(1), '5.0');
  assert.equal(headroomMultiplier(0).toFixed(1), '1.0');
});

test('the same full ceiling with a cached prefix is a different finding', () => {
  const stats = peaks([...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-sonnet-5',
      { uncached: i === 3 ? 4880000 : 100000, read: i === 3 ? 19520000 : 0 })));
  const [state, detail] = verdict('claude-sonnet-5', stats['claude-sonnet-5'], 5000000);
  assert.equal(state, 'itpm-saturated-already-cached');
  assert.match(detail, /cache reads were 80% of that minute's input/);
  assert.match(detail, /limit increase/);
});

test('haiku 3.5 charges cache reads so caching buys no headroom', () => {
  assert.equal(cacheReadsCount('claude-3-5-haiku-20241022'), true);
  assert.equal(cacheReadsCount('claude-haiku-4-5-20251001'), false);
  assert.equal(cacheReadsCount('claude-opus-5'), false);

  const result = { uncached_input_tokens: 1000, cache_read_input_tokens: 4000,
                   cache_creation: { ephemeral_5m_input_tokens: 500 } };
  assert.equal(chargeableInput(result, 'claude-sonnet-5'), 1500);
  assert.equal(chargeableInput(result, 'claude-3-5-haiku-20241022'), 5500);

  const stats = peaks([...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-3-5-haiku-20241022', { uncached: 200000, read: 1800000 })));
  const [state, detail] = verdict('claude-3-5-haiku-20241022',
    stats['claude-3-5-haiku-20241022'], 2000000);
  assert.equal(state, 'itpm-saturated-cache-counts');
  assert.match(detail, /buys no headroom at all/);
});

test('chargeableInput reads the nested cache_creation object', () => {
  assert.equal(chargeableInput({ uncached_input_tokens: 100,
    cache_creation: { ephemeral_5m_input_tokens: 7, ephemeral_1h_input_tokens: 3 } },
    'claude-opus-5'), 110);
  assert.equal(chargeableInput({ cache_creation_input_tokens: 999 }, 'claude-opus-5'), 0);
  assert.equal(chargeableInput({ uncached_input_tokens: null }, 'claude-opus-5'), 0);
  assert.equal(chargeableInput(null, 'claude-opus-5'), 0);
});

test('the peak minute survives an otherwise quiet window', () => {
  const stats = peaks([...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-opus-5', { uncached: i === 11 ? 4800000 : 200000 })));
  const row = stats['claude-opus-5'];
  assert.equal(row.peak, 4800000);
  assert.equal(row.peak_at, '2026-08-30T14:11:00Z');
  assert.equal(row.minutes, 20);
  assert.equal(verdict('claude-opus-5', row, 5000000)[0], 'itpm-saturated-uncached');
});

test('a window too short to have a peak gets no verdict', () => {
  const stats = peaks([minute('2026-08-30T14:00:00Z', 'claude-opus-5',
    { uncached: 9000000 })]);
  assert.equal(verdict('claude-opus-5', stats['claude-opus-5'], 5000000)[0],
               'too-few-buckets');
});

test('an unpublished ceiling is not an absent one', () => {
  const groups = itpmByGroup({ data: [
    { model_group: 'claude-sonnet-5', limits: [
      { type: 'input_tokens_per_minute', value: 5000000 },
      { type: 'output_tokens_per_minute', value: 1000000 }] },
    { model_group: 'claude-fable-5', limits: [
      { type: 'output_tokens_per_minute', value: 300000 }] },
  ] });
  assert.equal(groups['claude-sonnet-5'], 5000000);
  assert.equal(groups['claude-fable-5'], null);
  assert.equal(limitFor(groups, 'claude-sonnet-5-20260101'), 5000000);
  assert.equal(limitFor(groups, 'claude-fable-5'), null);
  assert.equal(limitFor(groups, 'claude-opus-5'), null);
  assert.equal(verdict('claude-fable-5', { minutes: 60, peak: 9 }, null)[0],
               'no-limit-published');
});

test('longest prefix wins when two groups could claim a model', () => {
  const groups = { 'claude-haiku': 1000, 'claude-haiku-4-5': 5000000 };
  assert.equal(limitFor(groups, 'claude-haiku-4-5-20251001'), 5000000);
  assert.equal(limitFor(groups, ''), null);
  assert.equal(limitFor({}, 'claude-opus-5'), null);
  assert.equal(cacheReadShare({ peak: 0, peak_read: 0 }, 'claude-opus-5'), null);
  assert.equal(headroomMultiplier(null), null);
});
''',
"faq": [
 ("Why does caching help a rate limit at all?",
  "Because the limiter is charged on uncached input only. cache_read_input_tokens is excluded from ITPM on every current model except Claude Haiku 3.5, so tokens you move behind a breakpoint stop competing for the ceiling entirely. At an eighty percent read share the same ITPM number carries five times the total input, which is a throughput change rather than a percentage saved."),
 ("Is this the same as the prompt caching cost notes?",
  "No, and the difference is worth holding onto. Those notes end in a dollar figure and are true whether or not you are near any limit. This one ends in a ceiling and is true whether or not caching would save you money: a workload can be comfortably profitable, already budgeted, and still unable to grow because its input limiter is full every afternoon."),
 ("Will lowering concurrency help?",
  "Almost never. ITPM is charged on tokens, not on connections, so the same volume of prompt spread over fewer workers arrives at the same rate. Concurrency is the right lever when requests per minute is the bucket that emptied, which is a different finding from a different header. Naming which one you hit is the sibling note on limiter identification."),
 ("Why minute buckets rather than hourly?",
  "Because the limiter is enforced by the minute and an hourly mean hides exactly the shape you are looking for. A workload saturating ITPM for ninety seconds an hour reads as a quarter of its ceiling on an hourly graph and is rejecting requests twice an hour. The usage report allows up to 1,440 one-minute buckets, which is a full day."),
 ("What about Claude Haiku 3.5?",
  "It is the one model family where cache reads are charged against ITPM. Caching still lowers the bill on it, and buys no headroom, so the script reports it as its own state rather than folding it in with the rest. If it is in your mix, the levers there are a shorter prefix, a different model, or a limit increase."),
],
"related": [REL_OTPM, REL_CACHE_NEVER, REL_CACHE_WRITES],
"citations": [CITE_CL_RATE, CITE_CL_USAGE_REPORT, CITE_CL_CACHING, CITE_CL_RATE_API],
},
{
"slug": "otpm-exhausted",
"title": "Output tokens per minute is the real ceiling, not RPM",
"description": "The output limiter is full while input and requests have room. More workers generate the same tokens against the same bucket, so concurrency changes nothing.",
"h1": "output tokens per minute is the real ceiling, not RPM",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic output tokens per minute", "otpm rate limit claude",
             "anthropic-ratelimit-output-tokens-remaining", "max_tokens does not affect otpm",
             "thinking tokens count as output"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_ADMIN_KEY, an Admin API key provisioned read-only.",
"lead": "The capacity plan is a spreadsheet with requests per minute in it, and it has been right about everything for a year. Then thinking gets turned up on the summariser, and the same number of calls starts 429ing. Nobody changed the request rate. Nobody changed the prompts. What changed is that each answer got four times longer, and the limiter that was never in the spreadsheet is the one counting characters as they come out.",
"short_answer": """<p>Read the per-minute buckets with an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={T-4h}&amp;bucket_width=1m&amp;limit=240&amp;group_by[]=model</code>, take the largest <code>output_tokens</code> minute per model, and compare it against <code>output_tokens_per_minute</code> from <code>GET /v1/organizations/rate_limits</code>.</p>
<p>OTPM is roughly one fifth of ITPM at every tier, so a generation-heavy workload reaches it first while the input limiter still looks comfortable. Thinking tokens are billed and counted as output, which is why raising effort can saturate it at an unchanged request rate.</p>
<p>The conclusion is the part that matters: divide the peak output by your configured RPM. That quotient is the mean answer length at which requests per minute would have been the binding limiter instead. If your answers are longer than it &mdash; and on a generation workload they are &mdash; the request rate was never the ceiling, and adding workers generates the same tokens against the same full bucket.</p>""",
"problem": """<p>Concurrency is the unit everyone plans in. Workers, connections, requests per second: it is what the queue is sized in, what the autoscaler reacts to, and what the runbook says to reduce. So when 429s appear, the response is to send fewer requests, and on an output limiter that does nothing at all. Three workers generating two hundred thousand tokens a minute and six workers generating two hundred thousand tokens a minute are the same load. The bucket is counting what comes out, not how many connections it came out of.</p>
<p>What makes it hard to see is that nothing in the request changed. The prompts are the same size, the traffic is the same shape, the model id is the same string. An effort setting moved, or a prompt started asking for a longer answer, or a summariser was pointed at bigger documents. All of those multiply the output side and leave the input side and the request count exactly where they were, which is precisely the shape that a request-rate mental model cannot explain.</p>""",
"why": """<p><strong>OTPM is about a fifth of ITPM at every tier.</strong> The two ceilings are not close to each other and they never were. Any workload whose output is more than about a fifth of its input volume reaches the output limiter first, which covers most generation, drafting and long-form summarisation. The ratio is printed by the script so the asymmetry is visible rather than assumed.</p>
<p><strong>Thinking tokens are output tokens.</strong> They are billed as output and counted as output, so an adaptive or high-effort configuration can saturate OTPM at an unchanged request rate and an unchanged prompt. This is the single most common way a system that was fine last month is not fine this month with no diff that explains it.</p>
<p><strong><code>max_tokens</code> is documented not to factor into OTPM.</strong> The limiter is evaluated against tokens actually generated, so there is no rate-limit penalty for setting a generous ceiling and no rate-limit benefit to lowering it. Lowering <code>max_tokens</code> is the first thing most teams try here, it truncates answers, and it does not move the limiter.</p>
<p><strong>You cannot count requests, so the script inverts the question.</strong> The Anthropic usage report has no request-count field at all. What it can do is divide the peak output minute by the configured RPM: the result is the mean answer length at which the request limiter would have bound first. It is a number you can compare against what you know your answers look like, and it is honest about being a comparison rather than a measurement.</p>
<p><strong>This is not the input-limiter finding.</strong> <a href="/llm/itpm-exhausted-uncached-input/">A full ITPM bucket</a> is fixed by caching the stable prefix, because cache reads are not charged against the input limiter. Nothing analogous exists on the output side: there is no cached output, so caching moves this number by exactly zero. The script reports an input-bound workload as a separate state and sends it to the other note rather than offering a repair that cannot work.</p>
<p><strong>The batch API is a different limiter group.</strong> Message Batches carries its own limits and a fifty percent discount, so latency-tolerant generation moved there stops competing for the synchronous OTPM bucket entirely. That is a real capacity increase rather than a rearrangement, which is why it is the first repair printed.</p>""",
"steps": [
 {"h": "Take the peak output minute per model",
  "body": """<p><code>bucket_width=1m</code>, <code>starting_at</code> floored to the minute, grouped by model. Keep the maximum <code>output_tokens</code> minute, because the limiter is enforced by the minute and an hourly mean hides a workload that saturates for ninety seconds an hour.</p>"""},
 {"h": "Keep the input from that same minute",
  "body": """<p>Not the largest input minute in the window &mdash; the input from the minute the output peaked. The whole judgement is whether output was full <em>while</em> input had room, and pairing an output peak from one minute with an input peak from another describes a workload that never existed.</p>"""},
 {"h": "Compare against both published ceilings",
  "body": """<p><code>GET /v1/organizations/rate_limits</code> gives <code>requests_per_minute</code>, <code>input_tokens_per_minute</code> and <code>output_tokens_per_minute</code> per model group. All three are needed: output against its own ceiling for the finding, input against its ceiling to rule out the sibling note, and requests to compute the answer length at which the request rate would have mattered.</p>"""},
 {"h": "Divide the peak output by RPM",
  "body": """<p>The quotient is the mean answer length below which requests per minute would have been the binding limiter. Print it and let the reader compare: nobody can count requests through this API, but everybody knows roughly how long their answers are. If the real mean is comfortably above the printed number, the request rate was never near its ceiling.</p>"""},
 {"h": "Print repairs that touch output, not concurrency",
  "body": """<p>Three of them: lower <code>output_config.effort</code> where the thinking is not earning its tokens, move latency-tolerant generation to the Message Batches API which is a separate limiter group at half the price, or request an OTPM increase. Changing an effort setting changes answer quality, so the script prints it and stops.</p>"""},
],
"verify": """<p>Re-run after the work moves. The peak output minute on the synchronous path should fall while total generated tokens hold steady; that is capacity moved rather than work dropped.</p>
<pre><code class="language-bash">python3 anthropic_otpm_ceiling.py --minutes 240
# otpm-saturated  claude-opus-5  peak minute generated 980,000 of an OTPM of
#   1,000,000 (98%) while input sat at 24% of ITPM
#   RPM would only have bound first at a mean answer of 245 token(s) or shorter
#   OTPM is 20% of ITPM on this group, so generation reaches its ceiling first
# 3 model(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "Two GETs against the Admin API and no writes, with <code>ANTHROPIC_ADMIN_KEY</code> provisioned read-only. Six pure functions, and the one worth stealing is the smallest: peak output divided by configured RPM, which converts an unanswerable question about request counts into an answerable one about answer length. The fold keeps the input from the peak output minute rather than the largest input minute, and the verdict has an explicit state for an input-bound workload so that this script hands it to the other note instead of prescribing a fix that cannot work.",
"py_file": "anthropic_otpm_ceiling.py",
"py": '''"""Report an Anthropic output limiter that concurrency cannot fix.

Read only. Two GET requests and nothing else against the Admin API, which needs
an Admin API key (sk-ant-admin...); a workspace key is rejected by every
/v1/organizations/* path, and an Admin key can be provisioned read-only.

The repair is printed, never performed. Lowering an effort setting changes what
the model does with a question, and moving traffic to the Batch API changes
when answers arrive. Both are decisions with owners.

The messages usage report has no request-count field. That is why this script
never claims a request rate: it divides the peak output minute by the
configured RPM and prints the answer length at which the request limiter would
have bound first, which is a comparison the reader can make and the API cannot.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_otpm_ceiling")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

LIMITER_TYPES = ("requests_per_minute", "input_tokens_per_minute",
                 "output_tokens_per_minute")

FINDINGS = ("otpm-saturated", "both-limiters-saturated")


def generated(result):
    """Output tokens in one usage result. Pure.

    Thinking tokens are billed as output and counted as output, so they are
    already inside this number. There is no separate field to add and no way to
    subtract them, which is exactly why an effort change can saturate the
    output limiter with nothing else in the request having moved.
    """
    if not isinstance(result, dict):
        return 0
    try:
        return int(result.get("output_tokens") or 0)
    except (TypeError, ValueError):
        return 0


def received(result):
    """Input tokens in one usage result, from every field that carries them. Pure.

    Total input is cache_read + cache_creation + uncached. This is only used to
    decide whether the input limiter also had pressure on it, so it is summed
    generously rather than charged the way ITPM charges.
    """
    if not isinstance(result, dict):
        return 0
    total = 0
    for field in ("uncached_input_tokens", "cache_read_input_tokens"):
        try:
            total += int(result.get(field) or 0)
        except (TypeError, ValueError):
            pass
    creation = result.get("cache_creation") or {}
    for field in ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"):
        try:
            total += int(creation.get(field) or 0)
        except (TypeError, ValueError):
            pass
    return total


def peaks(buckets):
    """Fold one-minute buckets into per-model output peaks. Pure.

    The input recorded is the input from the minute output peaked, not the
    largest input minute in the window. The judgement this script makes is
    whether output was full while input had room, and pairing two peaks from
    two different minutes describes a workload that never ran.
    """
    per_minute = {}
    for bucket in buckets or []:
        stamp = str(bucket.get("starting_at") or bucket.get("start_time") or "")
        for result in bucket.get("results") or []:
            model = str(result.get("model") or "").strip() or "all models"
            row = per_minute.setdefault((model, stamp), {"out": 0, "in": 0})
            row["out"] += generated(result)
            row["in"] += received(result)

    out = {}
    for (model, stamp), row in per_minute.items():
        stats = out.setdefault(model, {"peak_out": 0, "peak_at": None,
                                       "input_at_peak": 0, "minutes": 0,
                                       "total_out": 0})
        stats["minutes"] += 1
        stats["total_out"] += row["out"]
        if row["out"] > stats["peak_out"]:
            stats["peak_out"] = row["out"]
            stats["peak_at"] = stamp
            stats["input_at_peak"] = row["in"]
    return out


def limits_by_group(payload):
    """{model_group: {limiter type: value}} from the rate-limits response. Pure.

    All three limiters are kept because all three are needed: output for the
    verdict, input to rule out the sibling finding, and requests to compute the
    answer length at which the request rate would have mattered. A type absent
    from limits[] is None, which means it inherits, never that it is unlimited.
    """
    out = {}
    for entry in (payload or {}).get("data") or []:
        group = str(entry.get("model_group") or "").strip()
        if not group:
            continue
        row = out.setdefault(group, dict.fromkeys(LIMITER_TYPES))
        for limit in entry.get("limits") or []:
            kind = str(limit.get("type") or "").strip()
            if kind not in row:
                continue
            try:
                row[kind] = int(limit.get("value"))
            except (TypeError, ValueError):
                row[kind] = None
    return out


def limits_for(groups, model):
    """The limiter row for the group a model id belongs to. Pure. Longest prefix wins."""
    name = str(model or "").strip().lower()
    if not name:
        return None
    best_key, best_len = None, -1
    for group in (groups or {}):
        candidate = str(group).strip().lower()
        if not candidate:
            continue
        if name == candidate or name.startswith(candidate):
            if len(candidate) > best_len:
                best_key, best_len = group, len(candidate)
    if best_key is None:
        return None
    return (groups or {}).get(best_key)


def implied_mean_output(peak_output, rpm):
    """Answer length at which RPM would bind before OTPM. Pure.

    If a minute generated peak_output tokens, the request limiter could only
    have been what stopped you if you were also making rpm calls in that
    minute, which means a mean answer of peak_output / rpm tokens. Longer
    answers than that and the request rate was never close to its ceiling.

    This exists because the usage report has no request count. It converts a
    question the API cannot answer into one the reader already knows.
    """
    if rpm is None or rpm <= 0:
        return None
    try:
        peak = float(peak_output or 0)
    except (TypeError, ValueError):
        return None
    if peak <= 0:
        return None
    return peak / float(rpm)


def output_to_input_ratio(limits):
    """OTPM as a share of ITPM for one model group. Pure.

    Roughly one fifth at every tier, which is the structural reason a
    generation workload reaches the output ceiling first. Printed rather than
    assumed, because a workspace override can change it.
    """
    if not isinstance(limits, dict):
        return None
    otpm = limits.get("output_tokens_per_minute")
    itpm = limits.get("input_tokens_per_minute")
    if otpm is None or itpm is None or itpm <= 0:
        return None
    return otpm / float(itpm)


def verdict(model, stats, limits, floor=0.9, watch=0.6, min_minutes=10):
    """Classify one model's output limiter. Pure. Returns (state, detail)."""
    minutes = int((stats or {}).get("minutes") or 0)
    if minutes < min_minutes:
        return ("too-few-buckets",
                "%d minute(s) of traffic in the window, under the floor of %d. "
                "A peak taken over this little is noise." % (minutes, min_minutes))

    row = limits if isinstance(limits, dict) else {}
    otpm = row.get("output_tokens_per_minute")
    if otpm is None or otpm <= 0:
        return ("no-limit-published",
                "no output_tokens_per_minute is published for this model's "
                "group, so there is no ceiling to compare the peak against. The "
                "limiter still exists; the number was simply not returned.")

    peak_out = int(stats.get("peak_out") or 0)
    out_used = peak_out / float(otpm)

    itpm = row.get("input_tokens_per_minute")
    in_used = None
    if itpm is not None and itpm > 0:
        in_used = int(stats.get("input_at_peak") or 0) / float(itpm)

    shape = ("peak minute generated %d of an OTPM of %d (%.0f%%)"
             % (peak_out, otpm, out_used * 100))
    shape += (" while input sat at %.0f%% of ITPM" % (in_used * 100)
              if in_used is not None else ", with no ITPM published to compare")

    if out_used >= floor and in_used is not None and in_used >= floor:
        return ("both-limiters-saturated",
                shape + ". Both token limiters are full, so this is volume "
                "rather than shape: caching the prefix helps the input side "
                "and does nothing for the output side, and only batching or a "
                "limit increase moves both.")
    if out_used >= floor:
        return ("otpm-saturated",
                shape + ". The output limiter is what you are hitting, and "
                "there is no cached output, so nothing about the prompt moves "
                "this number.")
    if in_used is not None and in_used >= floor and out_used < watch:
        return ("input-bound",
                shape + ". The input limiter is the one that is full here, not "
                "the output one. Cache reads are not charged against ITPM, so "
                "that is a different finding with a different repair.")
    if out_used >= watch:
        return ("otpm-approaching",
                shape + ". Thin enough that a rise in answer length, or in "
                "thinking effort, lands on the output limiter.")
    return ("otpm-headroom", shape + ".")


def window_start(minutes):
    """Floor to the minute: starting_at must sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    return (now - dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def read_buckets(session, path, params):
    """Walk the paginated usage report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=int, default=240,
                    help="minutes of one-minute buckets to read (max 1440)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print models with headroom left")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    minutes = max(1, min(int(args.minutes), 1440))
    session = requests.Session()
    session.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    params = {"starting_at": window_start(minutes), "bucket_width": "1m",
              "limit": minutes, "group_by[]": ["model"]}
    stats = peaks(read_buckets(session, "/organizations/usage_report/messages", params))
    if not stats:
        log.info("no message usage in the last %d minute(s)", minutes)
        return 0

    groups = limits_by_group(get(session, "/organizations/rate_limits"))

    checked = 0
    bad = 0
    for model in sorted(stats, key=lambda m: -stats[m]["peak_out"]):
        row = stats[model]
        limits = limits_for(groups, model)
        state, detail = verdict(model, row, limits)
        checked += 1
        line = "%-24s %-28s %s" % (state, model, detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            mean = implied_mean_output(row["peak_out"],
                                       (limits or {}).get("requests_per_minute"))
            if mean is not None:
                log.warning("  RPM would only have bound first at a mean answer "
                            "of %.0f token(s) or shorter, so if your answers are "
                            "longer than that the request rate was never the "
                            "ceiling and more workers add nothing", mean)
            else:
                log.warning("  no requests_per_minute published for this group, "
                            "so the request rate cannot be ruled out from here")
            ratio = output_to_input_ratio(limits)
            if ratio is not None:
                log.warning("  OTPM is %.0f%% of ITPM on this group, so "
                            "generation reaches its ceiling first", ratio * 100)
            log.warning("  repair: move latency tolerant generation to the "
                        "Message Batches API, which has its own limiter group "
                        "and costs half; or lower output_config.effort, since "
                        "thinking tokens are counted as output; or request an "
                        "output_tokens_per_minute increase.")
            log.warning("  repair: do not lower max_tokens. It is documented "
                        "not to factor into OTPM, so it truncates answers "
                        "without buying a single token of headroom.")
        elif state == "input-bound":
            log.warning(line)
            log.warning("  repair: this one is the input limiter. Cache reads "
                        "are not charged against ITPM, so covering the stable "
                        "prefix is the lever there, not anything on this page.")
        elif state in ("otpm-approaching", "no-limit-published"):
            log.warning(line)
        elif args.show_all:
            log.info(line)

    log.info("%d model(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-otpm-ceiling.mjs",
"js": '''/**
 * Report an Anthropic output limiter that concurrency cannot fix.
 *
 * Read only. Two GET requests and nothing else against the Admin API, which
 * needs an Admin API key (sk-ant-admin...); a workspace key is rejected by
 * every /v1/organizations/* path. The repair is printed, never performed.
 *
 * The messages usage report has no request-count field, so this script never
 * claims a request rate: it divides the peak output minute by the configured
 * RPM and prints the answer length at which the request limiter would have
 * bound first.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const LIMITER_TYPES = ['requests_per_minute', 'input_tokens_per_minute',
                       'output_tokens_per_minute'];

const FINDINGS = new Set(['otpm-saturated', 'both-limiters-saturated']);

const int = (v) => (Number.isFinite(Number(v)) ? Math.trunc(Number(v)) : 0);

/**
 * Output tokens in one usage result. Pure.
 * Thinking tokens are billed and counted as output, so they are already inside
 * this number: there is nothing to add and nothing to subtract.
 */
export function generated(result) {
  if (!result || typeof result !== 'object') return 0;
  return int(result.output_tokens);
}

/**
 * Input tokens in one usage result, from every field that carries them. Pure.
 * Summed generously rather than charged the way ITPM charges, because this is
 * only used to decide whether the input limiter also had pressure on it.
 */
export function received(result) {
  if (!result || typeof result !== 'object') return 0;
  const creation = result.cache_creation ?? {};
  return int(result.uncached_input_tokens) + int(result.cache_read_input_tokens)
    + int(creation.ephemeral_5m_input_tokens) + int(creation.ephemeral_1h_input_tokens);
}

/**
 * Fold one-minute buckets into per-model output peaks. Pure.
 * The input kept is the input from the minute output peaked, not the largest
 * input minute: two peaks from two minutes describe a workload that never ran.
 */
export function peaks(buckets) {
  const perMinute = new Map();
  for (const bucket of buckets ?? []) {
    const stamp = String(bucket.starting_at ?? bucket.start_time ?? '');
    for (const result of bucket.results ?? []) {
      const model = String(result.model ?? '').trim() || 'all models';
      const key = `${model}\\u0000${stamp}`;
      const row = perMinute.get(key) ?? { model, stamp, out: 0, in: 0 };
      row.out += generated(result);
      row.in += received(result);
      perMinute.set(key, row);
    }
  }

  const out = {};
  for (const row of perMinute.values()) {
    const stats = out[row.model] ?? { peak_out: 0, peak_at: null, input_at_peak: 0,
                                      minutes: 0, total_out: 0 };
    stats.minutes += 1;
    stats.total_out += row.out;
    if (row.out > stats.peak_out) {
      stats.peak_out = row.out;
      stats.peak_at = row.stamp;
      stats.input_at_peak = row.in;
    }
    out[row.model] = stats;
  }
  return out;
}

/**
 * {model_group: {limiter type: value}} from the rate-limits response. Pure.
 * All three limiters are kept; a type absent from limits[] is null, which means
 * it inherits, never that it is unlimited.
 */
export function limitsByGroup(payload) {
  const out = {};
  for (const entry of (payload ?? {}).data ?? []) {
    const group = String(entry.model_group ?? '').trim();
    if (!group) continue;
    if (!out[group]) {
      out[group] = {};
      for (const t of LIMITER_TYPES) out[group][t] = null;
    }
    for (const limit of entry.limits ?? []) {
      const kind = String(limit.type ?? '').trim();
      if (!(kind in out[group])) continue;
      const value = Number(limit.value);
      out[group][kind] = Number.isInteger(value) ? value : null;
    }
  }
  return out;
}

/** The limiter row for the group a model id belongs to. Pure. Longest prefix wins. */
export function limitsFor(groups, model) {
  const name = String(model ?? '').trim().toLowerCase();
  if (!name) return null;
  let bestKey = null;
  let bestLen = -1;
  for (const group of Object.keys(groups ?? {})) {
    const candidate = group.trim().toLowerCase();
    if (!candidate) continue;
    if (name === candidate || name.startsWith(candidate)) {
      if (candidate.length > bestLen) { bestKey = group; bestLen = candidate.length; }
    }
  }
  return bestKey === null ? null : groups[bestKey];
}

/**
 * Answer length at which RPM would bind before OTPM. Pure.
 * peak_output / rpm. Longer answers than that and the request rate was never
 * close. This exists because the usage report has no request count: it turns a
 * question the API cannot answer into one the reader already knows.
 */
export function impliedMeanOutput(peakOutput, rpm) {
  if (rpm === null || rpm === undefined || rpm <= 0) return null;
  const peak = Number(peakOutput ?? 0);
  if (!Number.isFinite(peak) || peak <= 0) return null;
  return peak / rpm;
}

/**
 * OTPM as a share of ITPM for one model group. Pure.
 * Roughly one fifth at every tier, which is why generation hits its ceiling
 * first. Printed rather than assumed, because an override can change it.
 */
export function outputToInputRatio(limits) {
  if (!limits || typeof limits !== 'object') return null;
  const otpm = limits.output_tokens_per_minute;
  const itpm = limits.input_tokens_per_minute;
  if (otpm === null || otpm === undefined) return null;
  if (itpm === null || itpm === undefined || itpm <= 0) return null;
  return otpm / itpm;
}

/** Classify one model's output limiter. Pure. Returns [state, detail]. */
export function verdict(model, stats, limits, {
  floor = 0.9, watch = 0.6, minMinutes = 10,
} = {}) {
  const minutes = Number((stats ?? {}).minutes ?? 0);
  if (minutes < minMinutes) {
    return ['too-few-buckets',
      `${minutes} minute(s) of traffic in the window, under the floor of ` +
      `${minMinutes}. A peak taken over this little is noise.`];
  }

  const row = (limits && typeof limits === 'object') ? limits : {};
  const otpm = row.output_tokens_per_minute;
  if (otpm === null || otpm === undefined || otpm <= 0) {
    return ['no-limit-published',
      "no output_tokens_per_minute is published for this model's group, so " +
      'there is no ceiling to compare the peak against. The limiter still ' +
      'exists; the number was simply not returned.'];
  }

  const peakOut = Number(stats.peak_out ?? 0);
  const outUsed = peakOut / otpm;

  const itpm = row.input_tokens_per_minute;
  let inUsed = null;
  if (itpm !== null && itpm !== undefined && itpm > 0) {
    inUsed = Number(stats.input_at_peak ?? 0) / itpm;
  }

  let shape = `peak minute generated ${peakOut} of an OTPM of ${otpm} ` +
              `(${(outUsed * 100).toFixed(0)}%)`;
  shape += inUsed === null
    ? ', with no ITPM published to compare'
    : ` while input sat at ${(inUsed * 100).toFixed(0)}% of ITPM`;

  if (outUsed >= floor && inUsed !== null && inUsed >= floor) {
    return ['both-limiters-saturated',
      `${shape}. Both token limiters are full, so this is volume rather than ` +
      'shape: caching the prefix helps the input side and does nothing for the ' +
      'output side, and only batching or a limit increase moves both.'];
  }
  if (outUsed >= floor) {
    return ['otpm-saturated',
      `${shape}. The output limiter is what you are hitting, and there is no ` +
      'cached output, so nothing about the prompt moves this number.'];
  }
  if (inUsed !== null && inUsed >= floor && outUsed < watch) {
    return ['input-bound',
      `${shape}. The input limiter is the one that is full here, not the output ` +
      'one. Cache reads are not charged against ITPM, so that is a different ' +
      'finding with a different repair.'];
  }
  if (outUsed >= watch) {
    return ['otpm-approaching',
      `${shape}. Thin enough that a rise in answer length, or in thinking ` +
      'effort, lands on the output limiter.'];
  }
  return ['otpm-headroom', `${shape}.`];
}

/** Floor to the minute: starting_at must sit on a bucket boundary. */
export function windowStart(minutes, now = new Date()) {
  const floored = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
                           now.getUTCHours(), now.getUTCMinutes());
  return new Date(floored - minutes * 60000).toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function get(adminKey, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, one);
  }
  const res = await fetch(url, {
    headers: { 'x-api-key': adminKey, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs an ` +
                    'Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* readBuckets(adminKey, path, params) {
  const q = { ...params };
  for (;;) {
    const page = await get(adminKey, path, q);
    for (const bucket of page.data ?? []) yield bucket;
    if (!page.has_more || !page.next_page) return;
    q.page = page.next_page;
  }
}

async function main() {
  const adminKey = process.env.ANTHROPIC_ADMIN_KEY;
  if (!adminKey) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const minutes = Math.max(1, Math.min(Number(process.env.MINUTES ?? 240), 1440));
  const showAll = process.env.SHOW_ALL === '1';

  const collected = [];
  for await (const bucket of readBuckets(adminKey, '/organizations/usage_report/messages',
    { starting_at: windowStart(minutes), bucket_width: '1m', limit: minutes,
      'group_by[]': ['model'] })) {
    collected.push(bucket);
  }
  const stats = peaks(collected);
  const models = Object.keys(stats);
  if (models.length === 0) {
    console.log(`no message usage in the last ${minutes} minute(s)`);
    return;
  }

  const groups = limitsByGroup(await get(adminKey, '/organizations/rate_limits'));

  let bad = 0;
  models.sort((a, b) => stats[b].peak_out - stats[a].peak_out);
  for (const model of models) {
    const row = stats[model];
    const limits = limitsFor(groups, model);
    const [state, detail] = verdict(model, row, limits);
    const line = `${state.padEnd(24)} ${model.padEnd(28)} ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      const mean = impliedMeanOutput(row.peak_out, (limits ?? {}).requests_per_minute);
      if (mean !== null) {
        console.warn(`  RPM would only have bound first at a mean answer of ` +
                     `${mean.toFixed(0)} token(s) or shorter, so if your answers are ` +
                     'longer than that the request rate was never the ceiling and ' +
                     'more workers add nothing');
      } else {
        console.warn('  no requests_per_minute published for this group, so the ' +
                     'request rate cannot be ruled out from here');
      }
      const ratio = outputToInputRatio(limits);
      if (ratio !== null) {
        console.warn(`  OTPM is ${(ratio * 100).toFixed(0)}% of ITPM on this group, ` +
                     'so generation reaches its ceiling first');
      }
      console.warn('  repair: move latency tolerant generation to the Message ' +
                   'Batches API, which has its own limiter group and costs half; or ' +
                   'lower output_config.effort, since thinking tokens are counted as ' +
                   'output; or request an output_tokens_per_minute increase.');
      console.warn('  repair: do not lower max_tokens. It is documented not to factor ' +
                   'into OTPM, so it truncates answers without buying a single token ' +
                   'of headroom.');
    } else if (state === 'input-bound') {
      console.warn(line);
      console.warn('  repair: this one is the input limiter. Cache reads are not ' +
                   'charged against ITPM, so covering the stable prefix is the lever ' +
                   'there, not anything on this page.');
    } else if (state === 'otpm-approaching' || state === 'no-limit-published') {
      console.warn(line);
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${models.length} model(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the note: output at ninety-eight percent of its ceiling while input sits at twenty-four percent of its own, and a printed answer length of 245 tokens below which the request rate would have mattered. The second is the test that keeps this note from being the input note twice &mdash; the same fold, the same endpoints, an input limiter that is full and an output limiter that is not, and the script has to say so and hand the reader to the other page. The third is the reason the fold is written the way it is: the input recorded has to come from the minute output peaked, because pairing the two peaks in a window describes a workload that never ran.",
"test_py_file": "test_anthropic_otpm_ceiling.py",
"test_py": '''from anthropic_otpm_ceiling import (generated, implied_mean_output, limits_by_group,
                                    limits_for, output_to_input_ratio, peaks,
                                    received, verdict)

SONNET = {"requests_per_minute": 4000,
          "input_tokens_per_minute": 5000000,
          "output_tokens_per_minute": 1000000}


def minute(stamp, model, out=0, uncached=0, read=0):
    """One 1m bucket from GET /v1/organizations/usage_report/messages."""
    return {"starting_at": stamp, "results": [{
        "model": model,
        "output_tokens": out,
        "uncached_input_tokens": uncached,
        "cache_read_input_tokens": read,
        "cache_creation": {"ephemeral_5m_input_tokens": 0,
                           "ephemeral_1h_input_tokens": 0},
    }]}


def test_a_full_output_limiter_beside_a_comfortable_input_one_is_the_finding():
    stats = peaks([minute("2026-08-30T14:%02d:00Z" % i, "claude-opus-5",
                          out=980_000 if i == 5 else 200_000,
                          uncached=1_200_000 if i == 5 else 400_000)
                   for i in range(20)])
    state, detail = verdict("claude-opus-5", stats["claude-opus-5"], SONNET)
    assert state == "otpm-saturated"
    assert "generated 980000 of an OTPM of 1000000 (98%)" in detail
    assert "while input sat at 24% of ITPM" in detail
    assert "no cached output" in detail
    # The conclusion the note exists for: RPM was never the ceiling.
    assert round(implied_mean_output(980_000, 4000)) == 245
    assert round(output_to_input_ratio(SONNET) * 100) == 20


def test_a_full_input_limiter_is_handed_to_the_other_note():
    # The same fold and the same endpoints, and the opposite finding. If this
    # state did not exist, this script would prescribe batching and effort
    # changes for a workload whose repair is a cache breakpoint.
    stats = peaks([minute("2026-08-30T14:%02d:00Z" % i, "claude-sonnet-5",
                          out=100_000 if i == 9 else 20_000,
                          uncached=4_900_000 if i == 9 else 300_000)
                   for i in range(20)])
    state, detail = verdict("claude-sonnet-5", stats["claude-sonnet-5"], SONNET)
    assert state == "input-bound"
    assert "input limiter is the one that is full here" in detail


def test_both_limiters_full_is_volume_rather_than_shape():
    stats = peaks([minute("2026-08-30T14:%02d:00Z" % i, "claude-sonnet-5",
                          out=950_000, uncached=4_800_000) for i in range(20)])
    state, detail = verdict("claude-sonnet-5", stats["claude-sonnet-5"], SONNET)
    assert state == "both-limiters-saturated"
    assert "does nothing for the output side" in detail


def test_the_input_recorded_is_from_the_minute_output_peaked():
    # Output peaks at 14:05 and input peaks at 14:12. Taking the maximum of each
    # independently would report 98% of OTPM against 98% of ITPM and invent a
    # minute that never happened.
    buckets = [minute("2026-08-30T14:%02d:00Z" % i, "claude-opus-5",
                      out=200_000, uncached=400_000) for i in range(20)]
    buckets[5] = minute("2026-08-30T14:05:00Z", "claude-opus-5",
                        out=980_000, uncached=1_200_000)
    buckets[12] = minute("2026-08-30T14:12:00Z", "claude-opus-5",
                         out=300_000, uncached=4_900_000)
    row = peaks(buckets)["claude-opus-5"]
    assert row["peak_out"] == 980_000
    assert row["peak_at"] == "2026-08-30T14:05:00Z"
    assert row["input_at_peak"] == 1_200_000
    assert verdict("claude-opus-5", row, SONNET)[0] == "otpm-saturated"


def test_input_is_summed_from_every_field_that_carries_it():
    result = {"output_tokens": 50, "uncached_input_tokens": 100,
              "cache_read_input_tokens": 900,
              "cache_creation": {"ephemeral_5m_input_tokens": 7,
                                 "ephemeral_1h_input_tokens": 3}}
    assert generated(result) == 50
    assert received(result) == 1010
    assert generated({}) == 0
    assert generated(None) == 0
    assert received(None) == 0


def test_the_implied_answer_length_refuses_to_guess():
    assert implied_mean_output(980_000, None) is None
    assert implied_mean_output(980_000, 0) is None
    assert implied_mean_output(0, 4000) is None
    assert output_to_input_ratio({"output_tokens_per_minute": 1000}) is None
    assert output_to_input_ratio(None) is None


def test_an_unpublished_output_ceiling_gets_no_verdict():
    groups = limits_by_group({"data": [
        {"model_group": "claude-sonnet-5", "limits": [
            {"type": "requests_per_minute", "value": 4000},
            {"type": "input_tokens_per_minute", "value": 5000000},
            {"type": "output_tokens_per_minute", "value": 1000000}]},
        {"model_group": "claude-fable-5", "limits": [
            {"type": "requests_per_minute", "value": 500}]},
    ]})
    assert limits_for(groups, "claude-sonnet-5-20260101") == SONNET
    fable = limits_for(groups, "claude-fable-5")
    assert fable["output_tokens_per_minute"] is None
    assert verdict("claude-fable-5", {"minutes": 60, "peak_out": 9}, fable)[0] \\
        == "no-limit-published"
    assert limits_for(groups, "claude-haiku-4-5-20251001") is None
    assert verdict("claude-opus-5", {"minutes": 2, "peak_out": 9}, SONNET)[0] \\
        == "too-few-buckets"
''',
"test_js_file": "anthropic-otpm-ceiling.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { generated, impliedMeanOutput, limitsByGroup, limitsFor,
         outputToInputRatio, peaks, received, verdict }
  from './anthropic-otpm-ceiling.mjs';

const SONNET = { requests_per_minute: 4000,
                 input_tokens_per_minute: 5000000,
                 output_tokens_per_minute: 1000000 };

/** One 1m bucket from GET /v1/organizations/usage_report/messages. */
function minute(stamp, model, { out = 0, uncached = 0, read = 0 } = {}) {
  return { starting_at: stamp, results: [{
    model,
    output_tokens: out,
    uncached_input_tokens: uncached,
    cache_read_input_tokens: read,
    cache_creation: { ephemeral_5m_input_tokens: 0, ephemeral_1h_input_tokens: 0 },
  }] };
}

const stamp = (i) => `2026-08-30T14:${String(i).padStart(2, '0')}:00Z`;

test('a full output limiter beside a comfortable input one is the finding', () => {
  const stats = peaks([...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-opus-5',
      { out: i === 5 ? 980000 : 200000, uncached: i === 5 ? 1200000 : 400000 })));
  const [state, detail] = verdict('claude-opus-5', stats['claude-opus-5'], SONNET);
  assert.equal(state, 'otpm-saturated');
  assert.match(detail, /generated 980000 of an OTPM of 1000000 \\(98%\\)/);
  assert.match(detail, /while input sat at 24% of ITPM/);
  assert.match(detail, /no cached output/);
  assert.equal(Math.round(impliedMeanOutput(980000, 4000)), 245);
  assert.equal(Math.round(outputToInputRatio(SONNET) * 100), 20);
});

test('a full input limiter is handed to the other note', () => {
  const stats = peaks([...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-sonnet-5',
      { out: i === 9 ? 100000 : 20000, uncached: i === 9 ? 4900000 : 300000 })));
  const [state, detail] = verdict('claude-sonnet-5', stats['claude-sonnet-5'], SONNET);
  assert.equal(state, 'input-bound');
  assert.match(detail, /input limiter is the one that is full here/);
});

test('both limiters full is volume rather than shape', () => {
  const stats = peaks([...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-sonnet-5', { out: 950000, uncached: 4800000 })));
  const [state, detail] = verdict('claude-sonnet-5', stats['claude-sonnet-5'], SONNET);
  assert.equal(state, 'both-limiters-saturated');
  assert.match(detail, /does nothing for the output side/);
});

test('the input recorded is from the minute output peaked', () => {
  const buckets = [...Array(20).keys()].map((i) =>
    minute(stamp(i), 'claude-opus-5', { out: 200000, uncached: 400000 }));
  buckets[5] = minute(stamp(5), 'claude-opus-5', { out: 980000, uncached: 1200000 });
  buckets[12] = minute(stamp(12), 'claude-opus-5', { out: 300000, uncached: 4900000 });
  const row = peaks(buckets)['claude-opus-5'];
  assert.equal(row.peak_out, 980000);
  assert.equal(row.peak_at, '2026-08-30T14:05:00Z');
  assert.equal(row.input_at_peak, 1200000);
  assert.equal(verdict('claude-opus-5', row, SONNET)[0], 'otpm-saturated');
});

test('input is summed from every field that carries it', () => {
  const result = { output_tokens: 50, uncached_input_tokens: 100,
    cache_read_input_tokens: 900,
    cache_creation: { ephemeral_5m_input_tokens: 7, ephemeral_1h_input_tokens: 3 } };
  assert.equal(generated(result), 50);
  assert.equal(received(result), 1010);
  assert.equal(generated({}), 0);
  assert.equal(generated(null), 0);
  assert.equal(received(null), 0);
});

test('the implied answer length refuses to guess', () => {
  assert.equal(impliedMeanOutput(980000, null), null);
  assert.equal(impliedMeanOutput(980000, 0), null);
  assert.equal(impliedMeanOutput(0, 4000), null);
  assert.equal(outputToInputRatio({ output_tokens_per_minute: 1000 }), null);
  assert.equal(outputToInputRatio(null), null);
});

test('an unpublished output ceiling gets no verdict', () => {
  const groups = limitsByGroup({ data: [
    { model_group: 'claude-sonnet-5', limits: [
      { type: 'requests_per_minute', value: 4000 },
      { type: 'input_tokens_per_minute', value: 5000000 },
      { type: 'output_tokens_per_minute', value: 1000000 }] },
    { model_group: 'claude-fable-5', limits: [
      { type: 'requests_per_minute', value: 500 }] },
  ] });
  assert.deepEqual(limitsFor(groups, 'claude-sonnet-5-20260101'), SONNET);
  const fable = limitsFor(groups, 'claude-fable-5');
  assert.equal(fable.output_tokens_per_minute, null);
  assert.equal(verdict('claude-fable-5', { minutes: 60, peak_out: 9 }, fable)[0],
               'no-limit-published');
  assert.equal(limitsFor(groups, 'claude-haiku-4-5-20251001'), null);
  assert.equal(verdict('claude-opus-5', { minutes: 2, peak_out: 9 }, SONNET)[0],
               'too-few-buckets');
});
''',
"faq": [
 ("Why does reducing concurrency not help?",
  "Because OTPM counts tokens generated, not connections open. Three workers producing two hundred thousand tokens a minute and six workers producing two hundred thousand tokens a minute are the same load on that bucket. Concurrency is the right lever for the requests-per-minute limiter, which is a different bucket with a different header, and the script prints the answer length at which that bucket would have been the one you hit."),
 ("Will lowering max_tokens buy headroom?",
  "No, and this is documented rather than inferred: max_tokens does not factor into OTPM calculations, which are evaluated against tokens actually generated. Lowering it truncates answers mid-sentence and moves the limiter not at all. It is the most common wrong fix here, which is why the script prints a line saying so."),
 ("Why did this start after a config change nobody thinks is related?",
  "Thinking tokens are billed as output and counted as output. Raising effort, or switching to an adaptive setting, multiplies output volume at an unchanged request rate and an unchanged prompt size, so the OTPM bucket saturates with no diff that looks like it should have done it. Check the effort setting against the day the peaks changed."),
 ("How can the script talk about requests when the usage report has none?",
  "It does not claim one. It divides the peak output minute by your configured RPM, which yields the mean answer length at which requests per minute would have been the binding limiter, and prints that number for you to compare against what you know your answers look like. Nobody can count requests through the Anthropic usage report, so inverting the question is the honest version of the check."),
 ("Does the Batch API actually give more capacity?",
  "Yes, because it is a separate limiter group. Message Batches has its own limits, so work moved there stops competing for the synchronous output bucket rather than being spread more thinly across it, and it costs half. The trade is latency: batches complete within a window rather than immediately, so it fits evaluation runs, enrichment and reporting, not anything with a user waiting."),
],
"related": [REL_ITPM, REL_BATCH, REL_OUTPUT_COST],
"citations": [CITE_CL_RATE, CITE_CL_RATE_API, CITE_CL_BATCHES, CITE_CL_CONTEXT],
},

]
