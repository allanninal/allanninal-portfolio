#!/usr/bin/env python3
"""/stripe/ field notes, batch W — the writing.

Four notes about the two things that decide what shape a payload arrives in and
whether a repeated request is one operation or two: API versions, and idempotency
keys. Same constraint as the rest of the section — every problem here is one a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.
"""

CITE_VERSIONING = ("Webhook versioning — Stripe Docs",
                   "https://docs.stripe.com/webhooks/versioning")
CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")
CITE_WEBHOOK_LIST = ("List all webhook endpoints — Stripe API reference",
                     "https://docs.stripe.com/api/webhook_endpoints/list")
CITE_UPGRADES = ("Upgrade your API version — Stripe Docs",
                 "https://docs.stripe.com/upgrades")
CITE_API_VERSIONING = ("Versioning — Stripe API reference",
                       "https://docs.stripe.com/api/versioning")
CITE_EVENT_OBJ = ("The event object — Stripe API reference",
                  "https://docs.stripe.com/api/events/object")
CITE_EVENTS_LIST = ("List all events — Stripe API reference",
                    "https://docs.stripe.com/api/events/list")
CITE_IDEMPOTENCY = ("Idempotent requests — Stripe API reference",
                    "https://docs.stripe.com/api/idempotent_requests")
CITE_ERRORS = ("Errors — Stripe API reference", "https://docs.stripe.com/api/errors")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

GUIDES = [

{
"slug": "endpoint-api-version-drift",
"title": "Endpoints render events at different pinned API versions",
"description": "One endpoint reads invoice.subscription, the other reads invoice.parent, and only one of them crashes. A migration that started and never finished.",
"h1": "endpoints render events at different pinned API versions",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe webhook version drift", "two webhook endpoints different api_version",
             "stripe endpoint migration unfinished", "invoice.parent invoice.subscription",
             "stripe webhook versioning"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "This is not <a href=\"/stripe/endpoint-api-version-pinned-stale/\">one endpoint pinned to an ancient version</a>, where every consumer at least agrees on the shape. This is two endpoints that <em>disagree with each other</em>. The same logical event goes to both, one service reads <code>invoice.subscription</code> and the other reads <code>invoice.parent</code>, and only one of them falls over. Both are configured exactly as somebody intended, six months apart.",
"short_answer": """<p>Read <code>GET /v1/webhook_endpoints?limit=100</code> and collect the distinct <code>api_version</code> across every endpoint whose <code>status</code> is <code>"enabled"</code>. Normalise both <code>null</code> and the empty string to one sentinel meaning <em>account default</em> before you deduplicate; skip that and two unpinned endpoints look like two different versions, and the script reports drift on a perfectly consistent account.</p>
<p>More than one member in that set is the finding. Then check whether any two of the URLs are identical once the query string is stripped: that is the documented dual-endpoint upgrade shape, and finding it still running means the migration stopped halfway.</p>""",
"problem": """<p>The damage here is proportional to how many services you have. A single pin that is out of date is wrong everywhere at once, which at least means one bug report and one fix. Drift is wrong in one place and right in another, so the evidence contradicts itself. The billing service handles renewals correctly all week. The fulfilment service, subscribed to the same event types, throws on a field that is definitely present in the payload the other service received. Comparing the two payloads is the only way to see it, and nobody compares payloads across services.</p>
<p>The half-finished migration variant is worse, because the two endpoints usually sit on the same URL with a query parameter distinguishing them, which is exactly what the upgrade guide tells you to do. Your route handler sees both, at two versions, and whichever branch it takes depends on which endpoint delivered. Two enabled endpoints on one URL is also its own separate problem: every event is handled twice.</p>""",
"why": """<p><strong>Each endpoint pins independently, and one of them usually is not pinned at all.</strong> An endpoint created through the Dashboard inherits the account default. One created through the API during an upgrade carries an explicit <code>api_version</code>. Both are ordinary ways to make an endpoint, and nothing anywhere shows you the two values side by side.</p>
<p><strong>The documented upgrade deliberately creates this state.</strong> Because <code>api_version</code> cannot be edited, the way to move an endpoint forward is to create a second one at the new version, run both, then disable the old one. The procedure is correct. The failure is the last step never happening, and there is no deadline or reminder attached to it.</p>
<p><strong>No SDK can decode two API versions at once.</strong> Each Stripe library is generated against exactly one version and deserializes against that schema. So there is no code-side workaround: you cannot write a handler that is simultaneously correct for both shapes using the typed objects, only one that reads raw JSON and branches by hand.</p>
<p><strong>Unpinned is written two ways.</strong> The field comes back as <code>null</code> on some endpoints and as <code>""</code> on others, and both mean <em>follow the account default</em>. Deduplicating the raw values counts those as two versions and produces a drift report on an account with no drift, which is the fastest way to get the whole check ignored.</p>""",
"steps": [
 {"h": "List the endpoints and keep only the enabled ones",
  "body": """<p><code>GET /v1/webhook_endpoints?limit=100</code>, paginated. A disabled endpoint delivers nothing, so its pin cannot cause a shape mismatch. Including it in the comparison invents drift out of residue somebody already retired.</p>"""},
 {"h": "Normalise before you deduplicate",
  "body": """<p><code>null</code> and <code>""</code> collapse to one sentinel. Do this first, on the raw field, before anything else looks at the value. It is one line, and it is the difference between a report people act on and a report people mute.</p>"""},
 {"h": "Count the distinct versions",
  "body": """<p>One member is consistent, whatever that member is. Two or more is the finding, and the list of them tells you how many shapes your handlers have to cope with today.</p>"""},
 {"h": "Strip the query string and look for repeats",
  "body": """<p>If two enabled endpoints share a URL once <code>?</code> onwards is removed, you are looking at an unfinished dual-endpoint upgrade rather than two independent consumers. That distinction changes the repair completely: one is a cutover to finish, the other is a decision about which version each service should be on.</p>"""},
 {"h": "Finish the migration, or abandon it deliberately",
  "body": """<p>Keep exactly one endpoint per logical consumer. Disable the loser with <code>disabled=true</code>, confirm nothing depends on it, then remove it. Pin the survivor on purpose rather than leaving it inheriting a default that will move under it at the next account upgrade.</p>"""},
],
"verify": """<p>Re-run the script. Every enabled endpoint should report the same version, and it should be one you chose.</p>
<pre><code class="language-bash">python3 stripe_endpoint_version_drift.py
# consistent  all 3 enabled endpoint(s) render at 2025-09-30.clover</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/webhook_endpoints</code> &mdash; a restricted key with read access to Webhook Endpoints is enough, and is what you should give it. The classification is a pure function over a list of endpoints, because both ways of getting this wrong are decisions the function makes and not requests it makes: counting a disabled endpoint, and counting <code>null</code> and <code>\"\"</code> as two versions.",
"py_file": "stripe_endpoint_version_drift.py",
"py": '''"""Report Stripe webhook endpoints rendering events at different api_versions.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Webhook Endpoints. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_endpoint_version_drift")

API = "https://api.stripe.com/v1"

# Both spellings of "this endpoint has no pin" collapse here, before anything
# deduplicates. An account with two unpinned endpoints has one shape, not two.
ACCOUNT_DEFAULT = "account default"


def normalise(api_version):
    """Map an endpoint's raw api_version onto the shape it actually renders.

    Pure. Stripe returns None on some unpinned endpoints and "" on others; both
    mean "follow the account default", so both become one sentinel.
    """
    if api_version is None or api_version == "":
        return ACCOUNT_DEFAULT
    return str(api_version)


def base_url(url):
    """The URL without its query string or fragment. Pure.

    The documented dual-endpoint upgrade puts two endpoints on one URL,
    distinguished only by a query parameter, so the query string is exactly what
    has to come off before two endpoints can be recognised as the same one.
    """
    return str(url or "").split("?", 1)[0].split("#", 1)[0]


def verdict(endpoints):
    """Classify a whole account's endpoints. Pure, so both traps are testable.

    `endpoints` is a list of dicts with `url`, `api_version` and `status`.
    Returns (state, detail).
    """
    live = [e for e in endpoints if e.get("status") == "enabled"]
    if not live:
        return ("none",
                "no enabled endpoints in this mode: nothing is being delivered, "
                "so nothing can disagree about a shape")

    versions = sorted({normalise(e.get("api_version")) for e in live})
    if len(versions) == 1:
        return ("consistent",
                "all %d enabled endpoint(s) render at %s" % (len(live), versions[0]))

    by_url = {}
    for e in live:
        by_url.setdefault(base_url(e.get("url")), set()).add(
            normalise(e.get("api_version")))
    shared = sorted(u for u, v in by_url.items() if len(v) > 1)
    if shared:
        return ("migration",
                "%d versions in use (%s), and %s is served at more than one of "
                "them. That is the dual-endpoint upgrade shape, still running: "
                "the handler is being sent every event twice, in two shapes."
                % (len(versions), ", ".join(versions), shared[0]))
    return ("drift",
            "%d versions in use (%s) across %d endpoint(s) on different URLs. "
            "The same event reaches your services in different shapes and only "
            "the ones reading a moved field will fail."
            % (len(versions), ", ".join(versions), len(live)))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def endpoints(session):
    """Every webhook endpoint in this key's mode, paginated."""
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/webhook_endpoints", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more"):
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--show-disabled", action="store_true",
                    help="also list disabled endpoints, which are never counted")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    eps = endpoints(s)
    if not eps:
        log.info("no webhook endpoints configured for this key's mode")
        return 0

    state, detail = verdict(eps)
    for ep in eps:
        if ep.get("status") != "enabled" and not args.show_disabled:
            continue
        log.info("  %-9s %-24s %s", ep.get("status", "?"),
                 normalise(ep.get("api_version")), ep.get("url", "?"))

    if state in ("consistent", "none"):
        log.info("%s  %s", state, detail)
        return 0

    log.warning("%s  %s", state, detail)
    log.warning("  api_version cannot be edited, so the repair is a cutover, not "
                "an update: pick the version every consumer should be on")
    log.warning("  disable the losing endpoint: POST %s/webhook_endpoints/{id} "
                "-d disabled=true", API)
    log.warning("  once nothing depends on it, remove it: DELETE %s/"
                "webhook_endpoints/{id}", API)
    log.warning("  then pin the survivor deliberately rather than leaving it on "
                "the account default, which moves at the next upgrade")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-endpoint-version-drift.mjs",
"js": '''/**
 * Report Stripe webhook endpoints rendering events at different api_versions.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Webhook Endpoints. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Both spellings of "this endpoint has no pin" collapse here, before anything
// deduplicates. An account with two unpinned endpoints has one shape, not two.
export const ACCOUNT_DEFAULT = 'account default';

/**
 * Map an endpoint's raw api_version onto the shape it actually renders. Pure.
 * Stripe returns null on some unpinned endpoints and '' on others.
 */
export function normalise(apiVersion) {
  if (apiVersion === null || apiVersion === undefined || apiVersion === '') {
    return ACCOUNT_DEFAULT;
  }
  return String(apiVersion);
}

/** The URL without its query string or fragment. Pure. */
export function baseUrl(url) {
  return String(url ?? '').split('?')[0].split('#')[0];
}

/**
 * Classify a whole account's endpoints. Pure, so both traps are testable.
 * `endpoints` is an array of objects with url, api_version and status.
 */
export function verdict(endpoints) {
  const live = endpoints.filter((e) => e.status === 'enabled');
  if (live.length === 0) {
    return ['none',
      'no enabled endpoints in this mode: nothing is being delivered, so ' +
      'nothing can disagree about a shape'];
  }

  const versions = [...new Set(live.map((e) => normalise(e.api_version)))].sort();
  if (versions.length === 1) {
    return ['consistent',
      `all ${live.length} enabled endpoint(s) render at ${versions[0]}`];
  }

  const byUrl = new Map();
  for (const e of live) {
    const u = baseUrl(e.url);
    if (!byUrl.has(u)) byUrl.set(u, new Set());
    byUrl.get(u).add(normalise(e.api_version));
  }
  const shared = [...byUrl.entries()].filter(([, v]) => v.size > 1)
    .map(([u]) => u).sort();
  if (shared.length > 0) {
    return ['migration',
      `${versions.length} versions in use (${versions.join(', ')}), and ` +
      `${shared[0]} is served at more than one of them. That is the ` +
      'dual-endpoint upgrade shape, still running: the handler is being sent ' +
      'every event twice, in two shapes.'];
  }
  return ['drift',
    `${versions.length} versions in use (${versions.join(', ')}) across ` +
    `${live.length} endpoint(s) on different URLs. The same event reaches your ` +
    'services in different shapes and only the ones reading a moved field will fail.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function endpoints(key) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/webhook_endpoints', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const eps = await endpoints(key);
  if (eps.length === 0) {
    console.log("no webhook endpoints configured for this key's mode");
    return;
  }

  const [state, detail] = verdict(eps);
  for (const ep of eps) {
    if (ep.status !== 'enabled') continue;
    console.log(`  ${String(ep.status).padEnd(9)} ` +
                `${normalise(ep.api_version).padEnd(24)} ${ep.url ?? '?'}`);
  }

  if (state === 'consistent' || state === 'none') {
    console.log(`${state}  ${detail}`);
    return;
  }

  console.warn(`${state}  ${detail}`);
  console.warn('  api_version cannot be edited, so the repair is a cutover, not ' +
               'an update: pick the version every consumer should be on');
  console.warn(`  disable the losing endpoint: POST ${API}/webhook_endpoints/{id} ` +
               '-d disabled=true');
  console.warn(`  once nothing depends on it, remove it: DELETE ${API}/` +
               'webhook_endpoints/{id}');
  console.warn('  then pin the survivor deliberately rather than leaving it on ' +
               'the account default, which moves at the next upgrade');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the one that decides whether anybody trusts this script. Two endpoints that both inherit the account default are consistent, and an account can report one as <code>null</code> and the other as <code>\"\"</code>. Deduplicating the raw field calls that drift, on an account with none, and a check that cries wolf on its first run does not get a second.",
"test_py_file": "test_stripe_endpoint_version_drift.py",
"test_py": '''from stripe_endpoint_version_drift import base_url, normalise, verdict


def test_null_and_empty_string_are_one_version_not_two():
    # The trap. Deduplicating the raw field reports drift on an account where
    # both endpoints simply follow the account default.
    assert normalise(None) == normalise("")
    state, _ = verdict([
        {"url": "https://a.example/hook", "api_version": None, "status": "enabled"},
        {"url": "https://b.example/hook", "api_version": "", "status": "enabled"},
    ])
    assert state == "consistent"


def test_a_disabled_endpoint_never_counts():
    # It delivers nothing, so its pin cannot put a second shape on the wire.
    state, _ = verdict([
        {"url": "https://a.example/hook", "api_version": "2025-09-30.clover",
         "status": "enabled"},
        {"url": "https://old.example/hook", "api_version": "2019-12-03",
         "status": "disabled"},
    ])
    assert state == "consistent"


def test_one_pinned_and_one_unpinned_is_drift():
    state, detail = verdict([
        {"url": "https://a.example/hook", "api_version": "2025-09-30.clover",
         "status": "enabled"},
        {"url": "https://b.example/hook", "api_version": None, "status": "enabled"},
    ])
    assert state == "drift"
    assert "account default" in detail


def test_same_url_differing_only_by_query_is_an_unfinished_migration():
    state, detail = verdict([
        {"url": "https://a.example/hook", "api_version": "2024-09-30.acacia",
         "status": "enabled"},
        {"url": "https://a.example/hook?version=2025-09-30",
         "api_version": "2025-09-30.clover", "status": "enabled"},
    ])
    assert state == "migration"
    assert "https://a.example/hook" in detail
    assert base_url("https://a.example/hook?version=x") == "https://a.example/hook"


def test_no_enabled_endpoints_is_not_reported_as_consistent():
    state, _ = verdict([{"url": "https://a.example/hook", "api_version": None,
                         "status": "disabled"}])
    assert state == "none"
''',
"test_js_file": "stripe-endpoint-version-drift.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { baseUrl, normalise, verdict } from './stripe-endpoint-version-drift.mjs';

test('null and empty string are one version not two', () => {
  assert.equal(normalise(null), normalise(''));
  const [state] = verdict([
    { url: 'https://a.example/hook', api_version: null, status: 'enabled' },
    { url: 'https://b.example/hook', api_version: '', status: 'enabled' },
  ]);
  assert.equal(state, 'consistent');
});

test('a disabled endpoint never counts', () => {
  const [state] = verdict([
    { url: 'https://a.example/hook', api_version: '2025-09-30.clover', status: 'enabled' },
    { url: 'https://old.example/hook', api_version: '2019-12-03', status: 'disabled' },
  ]);
  assert.equal(state, 'consistent');
});

test('one pinned and one unpinned is drift', () => {
  const [state, detail] = verdict([
    { url: 'https://a.example/hook', api_version: '2025-09-30.clover', status: 'enabled' },
    { url: 'https://b.example/hook', api_version: null, status: 'enabled' },
  ]);
  assert.equal(state, 'drift');
  assert.match(detail, /account default/);
});

test('same url differing only by query is an unfinished migration', () => {
  const [state, detail] = verdict([
    { url: 'https://a.example/hook', api_version: '2024-09-30.acacia', status: 'enabled' },
    { url: 'https://a.example/hook?version=2025-09-30',
      api_version: '2025-09-30.clover', status: 'enabled' },
  ]);
  assert.equal(state, 'migration');
  assert.match(detail, /https:\\/\\/a\\.example\\/hook/);
  assert.equal(baseUrl('https://a.example/hook?version=x'), 'https://a.example/hook');
});

test('no enabled endpoints is not reported as consistent', () => {
  const [state] = verdict([
    { url: 'https://a.example/hook', api_version: null, status: 'disabled' },
  ]);
  assert.equal(state, 'none');
});
''',
"faq": [
 ("How is this different from one endpoint pinned to an old version?",
  "A single stale pin is wrong consistently: every consumer of that endpoint sees the same old shape, so one bug report describes the whole problem. Drift is two endpoints disagreeing, so the same event is correct in one service and broken in another, and no single payload shows you both halves."),
 ("Is an endpoint pinned to an older version always wrong?",
  "No. A deliberate pin is how you keep a payload shape stable while the code that reads it is still being written. What makes drift a finding is that the versions were not chosen together, so nobody can say which shape is the intended one."),
 ("Can I just edit api_version on the endpoint that is behind?",
  "No. Update accepts url, enabled_events, description, metadata and disabled. api_version is fixed at creation, which is exactly why the upgrade path creates a second endpoint, and why an abandoned upgrade leaves two versions running."),
 ("Two endpoints on the same URL: is that the drift or a separate problem?",
  "Both, and they need different repairs. The version difference means two payload shapes. The shared URL means every event is delivered twice, so an unfinished migration is also a duplicate-delivery incident until the old endpoint is disabled."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Webhook Endpoints is enough, and it is what this script should be given. It reads configuration and cannot move money if it leaks."),
],
"related": [
 ("/stripe/endpoint-api-version-pinned-stale/", "A webhook endpoint is pinned to an ancient api_version"),
 ("/stripe/mixed-event-api-versions/", "Recent events carry two different api_version values"),
 ("/stripe/duplicate-endpoints-same-url/", "Two endpoints share one URL, so every event is handled twice"),
],
"citations": [CITE_VERSIONING, CITE_WEBHOOK_LIST, CITE_WEBHOOK_OBJ, CITE_UPGRADES],
},

{
"slug": "account-default-api-version-stale",
"title": "Account default API version is years behind the current one",
"description": "Documented parameters come back as no such parameter, and Stripe-generated events arrive in an old shape. No endpoint returns the account default.",
"h1": "account default API version is years behind the current one",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe account api version", "stripe no such parameter",
             "stripe default api version", "Stripe-Version header",
             "stripe upgrade api version"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing on a webhook endpoint explains this one. The <a href=\"/stripe/endpoint-api-version-pinned-stale/\">pinned-endpoint note</a> is about a value you can read straight off the endpoint object; this is the account-wide default sitting underneath it, and there is no API endpoint anywhere that returns it. It is why a parameter copied out of the current documentation comes back as <em>no such parameter</em>, and why renewal invoices Stripe generates for you arrive in a shape from two years ago.",
"short_answer": """<p>There is no <code>GET</code> that returns the account default, so read it two indirect ways and compare them. First, <code>GET /v1/events?limit=1</code> and take <code>data[0].api_version</code>: an event is rendered at the account default in force when it was created, so the newest event tells you what the default was as of then.</p>
<p>Second, and more authoritative: issue any GET over raw HTTP <em>without</em> a <code>Stripe-Version</code> request header and read the <code>Stripe-Version</code> header off the response. That is the default right now. Use curl or a plain HTTP client for this &mdash; every official SDK sends its own <code>Stripe-Version</code>, and gets its own value echoed back.</p>""",
"problem": """<p>The symptom does not look like a version problem. You copy a parameter out of the API reference, send it, and Stripe replies that it does not exist. The natural conclusion is a typo, or a feature not enabled on the account, or documentation that is ahead of the release. It is none of those: the documentation describes the current version and your requests are being served at whatever version your very first API call happened to land on, years ago.</p>
<p>The half that costs money is quieter. Automated Billing operations Stripe performs on your behalf &mdash; generating renewal invoices, advancing subscriptions &mdash; run at the account default. So the objects those operations produce, and the events announcing them, carry an old shape even though your own code is current. A field that moved is absent in exactly the places nobody is looking, and present everywhere they are.</p>""",
"why": """<p><strong>The version is set once, by accident, and never moves.</strong> It is fixed at the moment of your first API request and there is no automatic advance. An account created for a prototype in 2021 is still on the 2021 version in 2026, including after the entire integration has been rewritten twice.</p>
<p><strong>No endpoint reports it.</strong> Unpinned webhook endpoints return <code>null</code> or <code>""</code> for <code>api_version</code>, not the inherited value, so the obvious place to look is deliberately silent. This is why the check has to infer it from an event and corroborate it from a response header.</p>
<p><strong>Every SDK hides the answer.</strong> Each library pins a <code>Stripe-Version</code> on its outgoing requests, and Stripe honours it. So a script written with the SDK reads back the SDK's version and reports it as the account default, which is confidently wrong. The corroborating read only works from a client that sends no version header at all.</p>
<p><strong>The releases in between are not cosmetic.</strong> Acacia <code>2024-09-30</code>, Basil <code>2025-03-31</code> and Clover <code>2025-09-30</code> each carried breaking changes, and they accumulate. Skipping four of them is four changelogs to read, not one, and that reading is the actual work of the upgrade.</p>""",
"steps": [
 {"h": "Read the newest event and take its api_version",
  "body": """<p><code>GET /v1/events?limit=1</code>. Events are immutable and rendered at the default in force when they occurred, so the newest one is the best evidence available through the API. On a dormant account there may be nothing in the 30-day window, and the check has to say so rather than guess.</p>"""},
 {"h": "Read the Stripe-Version response header on the same request",
  "body": """<p>Send no <code>Stripe-Version</code> request header and Stripe answers with the account default in the response header. Both scripts here use a plain HTTP client for exactly this reason: an SDK would send its own version and the answer would be the SDK's, not the account's.</p>"""},
 {"h": "Compare the two before judging either",
  "body": """<p>If the header and the newest event disagree, the default moved after that event was created &mdash; an upgrade, or a rollback inside the 72-hour window. The header is the current truth; the mismatch itself is worth reporting, because it means the event stream in the retained window spans two shapes.</p>"""},
 {"h": "Measure the gap in years, not in release names",
  "body": """<p>Compare the <code>YYYY-MM-DD</code> prefix against today. More than about twelve months behind is the threshold worth acting on, because that is roughly two release lines and the changelog reading stops being a single afternoon.</p>"""},
 {"h": "Test with a per-request header before touching the account",
  "body": """<p>Send <code>Stripe-Version: &lt;target&gt;</code> on individual requests and run your integration against it. Nothing about the account changes, and you find the breaking changes on your own schedule. Only then upgrade the account in the Dashboard, where you get a 72-hour rollback window with old-shape retries for failed webhooks.</p>"""},
],
"verify": """<p>Re-run the script after the upgrade. The header and the newest event should agree, and the date should be on the current line.</p>
<pre><code class="language-bash">python3 stripe_account_api_version.py
# current    2025-09-30.clover  header and newest event agree</code></pre>""",
"code_intro": "One GET against <code>/v1/events</code>, read twice: once for the body and once for the response header. A restricted key with read access to Events is enough. Both classifications are pure functions &mdash; one decides which of the two readings to believe, the other decides how far behind that reading is &mdash; and the second takes today's date as an argument so the tests do not change verdict as the calendar moves.",
"py_file": "stripe_account_api_version.py",
"py": '''"""Report the Stripe account's default API version and how far behind it is.

Read only. One GET and no writes: give this a RESTRICTED key with read access to
Events. The upgrade is printed, never performed, because this script holds a
credential to a live payments account.

Deliberately uses a plain HTTP client rather than an SDK. Every official Stripe
library sends its own Stripe-Version header, and Stripe honours it, so an
SDK-based version of this script reads back the library's version and reports it
as the account's.
"""
import argparse
import datetime as dt
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_account_api_version")

API = "https://api.stripe.com/v1"

CURRENT_LINE = "2025-09-30"  # Clover
DATE = re.compile(r"^(\\d{4}-\\d{2}-\\d{2})")
YEAR = 365


def authority(event_version, header_version):
    """Decide which of the two indirect readings to believe. Pure.

    Returns (version, note). The response header is the default right now; the
    newest event is the default at the moment that event was created. When they
    disagree the account moved recently, and that is worth saying out loud.
    """
    if not event_version and not header_version:
        return (None,
                "no reading available: no events in the 30 day window and no "
                "Stripe-Version on the response")
    if header_version and not event_version:
        return (header_version,
                "from the Stripe-Version response header; no events in the "
                "window to corroborate it")
    if event_version and not header_version:
        return (event_version,
                "from the newest event; the response carried no Stripe-Version "
                "header, so this is the default as of that event and not now")
    if str(header_version).split(".")[0] != str(event_version).split(".")[0]:
        return (header_version,
                "the header says %s and the newest event says %s: the default "
                "moved after that event, or was rolled back inside the 72 hour "
                "window. The retained events span both shapes."
                % (header_version, event_version))
    return (header_version, "header and newest event agree")


def verdict(version, today, current_line=CURRENT_LINE):
    """How far behind the account default is. Pure.

    `today` is an ISO date string and is an argument rather than a call to
    date.today() so the tests keep the same answer as the calendar moves.
    """
    if not version:
        return ("unknown",
                "nothing to judge: the account default could not be read from "
                "an event or from a response header")
    m = DATE.match(str(version))
    if not m:
        return ("unreadable",
                "%r has no YYYY-MM-DD prefix to compare" % (version,))
    date = m.group(1)
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=YEAR)).isoformat()
    if date < cutoff:
        return ("stale",
                "the account default is %s, more than a year behind. Read the "
                "changelog for every release line between %s and %s; the "
                "breaking changes accumulate rather than replace each other."
                % (date, date, current_line))
    if date < current_line:
        return ("trailing",
                "the account default is %s, behind the current %s line but "
                "within a year of it. One changelog to read."
                % (date, current_line))
    return ("current", "the account default is %s, on the current line" % date)


def read_default(session):
    """One GET, read twice: the newest event's version and the response header."""
    r = session.get(API + "/events", params={"limit": 1}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    data = r.json().get("data", [])
    event_version = data[0].get("api_version") if data else None
    return event_version, r.headers.get("Stripe-Version")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--current-line", default=CURRENT_LINE,
                    help="the release line to measure against, as YYYY-MM-DD")
    ap.add_argument("--today", default=dt.date.today().isoformat(),
                    help="ISO date to measure the gap from, for reproducible runs")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    # No Stripe-Version header here on purpose: that is what makes the response
    # header report the account default rather than echo a version we chose.
    s.headers.update({"Authorization": "Bearer " + key})

    event_version, header_version = read_default(s)
    version, note = authority(event_version, header_version)
    state, detail = verdict(version, args.today, args.current_line)

    log.info("  %-9s %s", state, version or "unknown")
    log.info("  %s", note)

    if state == "current":
        log.info("%s  %s", state, detail)
        return 0

    log.warning("%s  %s", state, detail)
    log.warning("  test first without changing anything: send a per-request "
                "Stripe-Version: %s header and run your integration against it",
                args.current_line)
    log.warning("  then upgrade in the Dashboard: Workbench, Overview, API "
                "versions, Upgrade available")
    log.warning("  you get a 72 hour rollback window, during which webhooks that "
                "fail on the new shape are retried with the old structure")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-account-api-version.mjs",
"js": '''/**
 * Report the Stripe account's default API version and how far behind it is.
 *
 * Read only. One GET and no writes: give this a RESTRICTED key with read access
 * to Events. The upgrade is printed, never performed.
 *
 * Deliberately uses fetch rather than an SDK. Every official Stripe library
 * sends its own Stripe-Version header, and Stripe honours it, so an SDK-based
 * version of this script reads back the library's version, not the account's.
 */
const API = 'https://api.stripe.com/v1';

export const CURRENT_LINE = '2025-09-30'; // Clover
const DATE = /^(\\d{4}-\\d{2}-\\d{2})/;
const YEAR = 365;

/**
 * Decide which of the two indirect readings to believe. Pure.
 * Returns [version, note].
 */
export function authority(eventVersion, headerVersion) {
  if (!eventVersion && !headerVersion) {
    return [null,
      'no reading available: no events in the 30 day window and no ' +
      'Stripe-Version on the response'];
  }
  if (headerVersion && !eventVersion) {
    return [headerVersion,
      'from the Stripe-Version response header; no events in the window to ' +
      'corroborate it'];
  }
  if (eventVersion && !headerVersion) {
    return [eventVersion,
      'from the newest event; the response carried no Stripe-Version header, ' +
      'so this is the default as of that event and not now'];
  }
  if (String(headerVersion).split('.')[0] !== String(eventVersion).split('.')[0]) {
    return [headerVersion,
      `the header says ${headerVersion} and the newest event says ` +
      `${eventVersion}: the default moved after that event, or was rolled back ` +
      'inside the 72 hour window. The retained events span both shapes.'];
  }
  return [headerVersion, 'header and newest event agree'];
}

/**
 * How far behind the account default is. Pure. `today` is an ISO date string
 * and is an argument so the tests keep the same answer as the calendar moves.
 */
export function verdict(version, today, currentLine = CURRENT_LINE) {
  if (!version) {
    return ['unknown',
      'nothing to judge: the account default could not be read from an event ' +
      'or from a response header'];
  }
  const m = DATE.exec(String(version));
  if (!m) {
    return ['unreadable', `${version} has no YYYY-MM-DD prefix to compare`];
  }
  const date = m[1];
  const cutoff = new Date(Date.parse(`${today}T00:00:00Z`) - YEAR * 86400000)
    .toISOString().slice(0, 10);
  if (date < cutoff) {
    return ['stale',
      `the account default is ${date}, more than a year behind. Read the ` +
      `changelog for every release line between ${date} and ${currentLine}; the ` +
      'breaking changes accumulate rather than replace each other.'];
  }
  if (date < currentLine) {
    return ['trailing',
      `the account default is ${date}, behind the current ${currentLine} line ` +
      'but within a year of it. One changelog to read.'];
  }
  return ['current', `the account default is ${date}, on the current line`];
}

export async function readDefault(key) {
  const url = new URL(API + '/events');
  url.searchParams.set('limit', '1');
  // No Stripe-Version header here on purpose: that is what makes the response
  // header report the account default rather than echo a version we chose.
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  const body = await res.json();
  const first = (body.data ?? [])[0];
  return [first ? first.api_version : null, res.headers.get('stripe-version')];
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const today = process.env.TODAY ?? new Date().toISOString().slice(0, 10);
  const [eventVersion, headerVersion] = await readDefault(key);
  const [version, note] = authority(eventVersion, headerVersion);
  const [state, detail] = verdict(version, today);

  console.log(`  ${state.padEnd(9)} ${version ?? 'unknown'}`);
  console.log(`  ${note}`);

  if (state === 'current') {
    console.log(`${state}  ${detail}`);
    return;
  }

  console.warn(`${state}  ${detail}`);
  console.warn('  test first without changing anything: send a per-request ' +
               `Stripe-Version: ${CURRENT_LINE} header and run your integration ` +
               'against it');
  console.warn('  then upgrade in the Dashboard: Workbench, Overview, API ' +
               'versions, Upgrade available');
  console.warn('  you get a 72 hour rollback window, during which webhooks that ' +
               'fail on the new shape are retried with the old structure');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these exist because the account default is read indirectly and the two readings can legitimately disagree. The header is now; the newest event is whenever that event happened. A check that trusts the event alone reports the pre-upgrade version for as long as the account stays quiet, and a check that reports nothing when there are no events at all is better than one that calls silence current.",
"test_py_file": "test_stripe_account_api_version.py",
"test_py": '''from stripe_account_api_version import authority, verdict

TODAY = "2026-01-15"


def test_nothing_readable_is_not_reported_as_current():
    version, note = authority(None, None)
    assert version is None
    assert verdict(version, TODAY)[0] == "unknown"
    assert "30 day" in note


def test_the_header_wins_and_the_disagreement_is_named():
    # The header is the default now. The event is the default when it fired.
    version, note = authority("2024-09-30.acacia", "2025-09-30.clover")
    assert version == "2025-09-30.clover"
    assert "2024-09-30.acacia" in note and "72 hour" in note


def test_over_a_year_behind_is_stale_and_under_it_is_not():
    assert verdict("2024-09-30.acacia", TODAY)[0] == "stale"
    assert verdict("2025-03-31.basil", TODAY)[0] == "trailing"


def test_the_release_line_suffix_is_trimmed_before_comparing():
    # "2025-09-30.clover" as a raw string is greater than "2025-09-30", so the
    # date has to be cut off the front before anything is ordered.
    assert verdict("2025-09-30.clover", TODAY)[0] == "current"


def test_a_version_with_no_date_is_not_silently_current():
    assert verdict("beta", TODAY)[0] == "unreadable"
''',
"test_js_file": "stripe-account-api-version.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { authority, verdict } from './stripe-account-api-version.mjs';

const TODAY = '2026-01-15';

test('nothing readable is not reported as current', () => {
  const [version, note] = authority(null, null);
  assert.equal(version, null);
  assert.equal(verdict(version, TODAY)[0], 'unknown');
  assert.match(note, /30 day/);
});

test('the header wins and the disagreement is named', () => {
  const [version, note] = authority('2024-09-30.acacia', '2025-09-30.clover');
  assert.equal(version, '2025-09-30.clover');
  assert.match(note, /2024-09-30\\.acacia/);
  assert.match(note, /72 hour/);
});

test('over a year behind is stale and under it is not', () => {
  assert.equal(verdict('2024-09-30.acacia', TODAY)[0], 'stale');
  assert.equal(verdict('2025-03-31.basil', TODAY)[0], 'trailing');
});

test('the release line suffix is trimmed before comparing', () => {
  assert.equal(verdict('2025-09-30.clover', TODAY)[0], 'current');
});

test('a version with no date is not silently current', () => {
  assert.equal(verdict('beta', TODAY)[0], 'unreadable');
});
''',
"faq": [
 ("Is there really no API call that returns the account default?",
  "There is no field on any object that reports it. The two ways to read it are both indirect: the api_version on an event, which is the default at the moment that event was created, and the Stripe-Version response header on a request that sent no version header of its own."),
 ("Why does my SDK report a different version than this script?",
  "Because it sent one. Every official library pins a Stripe-Version on outgoing requests, so the response echoes the library's version rather than the account's. Reading the account default requires a client that sends no version header, which is why both scripts here use plain HTTP."),
 ("Will upgrading the account break my webhook handlers?",
  "It changes the shape of events for any endpoint that is unpinned, because unpinned means follow the account default. Pinned endpoints are unaffected by the account upgrade and stay on their own version, which is a separate thing to check."),
 ("What happens if the upgrade goes badly?",
  "There is a 72-hour rollback window. During it, webhook events that failed against the new shape are retried with the old structure. That window is also what leaves two api_version values in the retained event stream, which is worth knowing before you debug the aftermath."),
 ("Can I move one integration forward without upgrading the account?",
  "Yes, and it is the safer order. Send Stripe-Version on individual requests and that request alone is served at the target version. Nothing about the account changes, so you can find the breaking changes one call site at a time."),
],
"related": [
 ("/stripe/endpoint-api-version-pinned-stale/", "A webhook endpoint is pinned to an ancient api_version"),
 ("/stripe/mixed-event-api-versions/", "Recent events carry two different api_version values"),
 ("/stripe/dead-or-rejected-enabled-events/", "enabled_events lists event types that are dead or rejected"),
],
"citations": [CITE_UPGRADES, CITE_API_VERSIONING, CITE_EVENT_OBJ, CITE_KEYS],
},

{
"slug": "mixed-event-api-versions",
"title": "Recent events carry two different api_version values",
"description": "A handler that parsed fine all week starts throwing at one timestamp, and replaying an older event through the same code succeeds. The stream has a boundary.",
"h1": "recent events carry two different api_version values",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe event api_version", "stripe events different versions",
             "stripe replay old event fails", "stripe api upgrade boundary",
             "stripe event object version"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing here is a configuration field you can go and correct. The <a href=\"/stripe/endpoint-api-version-drift/\">drift note</a> is about endpoints disagreeing; this is about the stored events themselves. Event objects are immutable and rendered at whatever the account default was when they occurred, so an upgrade cuts a hard line across the 30-day window. Everything after it is one shape, everything before it is another, and a backfill walks straight through the boundary.",
"short_answer": """<p>Page <code>GET /v1/events?limit=100</code> across the retained window and collect the distinct <code>api_version</code> on the events themselves. More than one value means the stream has a boundary in it. Because Stripe returns events newest first, the <code>created</code> on the last event before the value changes is the timestamp of the transition.</p>
<p>Count the transitions, not just the versions. One is an upgrade. Two or more is an upgrade followed by a rollback inside the 72-hour window, which means the window contains a shape sandwich rather than a clean cut. Then read <code>api_version</code> on your endpoints: if any of them is unpinned, the boundary reached your handler; if all of them are pinned, it only shows in replays and in anything reading <code>/v1/events</code> directly.</p>""",
"problem": """<p>The tell is that the same code succeeds and fails on the same event type depending on when the event happened. A handler that ran clean all week starts throwing at a precise moment, and reprocessing an event from the day before through the identical code path works. That combination rules out a deploy, rules out data, and points at something nobody thinks of as data at all: the version the payload was frozen at.</p>
<p>It bites hardest in the two places that read old events. A backfill after an outage walks the whole retained window and hits both shapes in one loop. A replay of a specific event, done to debug something else, quietly exercises the old shape and produces a result that does not match production. The historical example everyone remembers is <code>request</code> changing from a bare string ID into an object with <code>id</code> and <code>idempotency_key</code>; every handler that read it as a string broke at exactly one timestamp.</p>""",
"why": """<p><strong>Events are immutable, including their version.</strong> Stripe renders an event once, at the account default in force at that moment, and stores it. Nothing re-renders it later. So the API can hand you two payload shapes for the same event type, from the same account, inside one paginated response, and both are correct.</p>
<p><strong>The boundary can come from three different actions.</strong> An account upgrade, a rollback inside the 72-hour window, or a re-pin. Each leaves the same evidence in the stream, and only the number of transitions distinguishes an upgrade from an upgrade-then-rollback.</p>
<p><strong>Whether it reaches your handler depends on the endpoint pin, not on the event.</strong> A pinned endpoint renders delivered payloads at its own version regardless of what the event object says, so a pinned integration can be sitting on a boundary and never see it in production &mdash; right up until someone writes a backfill that reads <code>/v1/events</code> and gets the raw shapes.</p>
<p><strong>There is no Stripe-side repair.</strong> You cannot re-render stored events. The fix is in your code: branch on <code>event.api_version</code> for the overlap, or stop trusting <code>data.object</code> during the transition and re-fetch the object by ID, which always comes back at the version your request asks for.</p>""",
"steps": [
 {"h": "Page the whole window, not the first page",
  "body": """<p><code>GET /v1/events?limit=100</code> with <code>starting_after</code> until the retention limit. A boundary two days ago is invisible on page one if page one is the last hour of traffic.</p>"""},
 {"h": "Group by api_version and keep nulls separate",
  "body": """<p>An event that reports no <code>api_version</code> goes in its own bucket rather than being dropped. Dropping it means the transition that produced it disappears from the count, and the check reports one clean shape on a window that has two.</p>"""},
 {"h": "Count transitions in timestamp order",
  "body": """<p>Walking the newest-first list, every position where the version differs from the next one is a transition. One transition is an upgrade with a clean cut. More than one is a rollback, and it means the shape alternates rather than changing once.</p>"""},
 {"h": "Ask whether any endpoint is unpinned",
  "body": """<p><code>GET /v1/webhook_endpoints</code>. Any endpoint with <code>null</code> or <code>""</code> for <code>api_version</code> follows the account default, so the boundary in the stream is also a boundary in what was delivered. If every endpoint is pinned, the exposure is limited to code that reads the events API itself.</p>"""},
 {"h": "Make the handler survive the overlap",
  "body": """<p>Branch on <code>event.api_version</code> for the 30 days the two shapes coexist, or prefer re-fetching the object by ID over trusting <code>data.object</code>. After 30 days the old shape ages out of retention and the branch can go.</p>"""},
],
"verify": """<p>Re-run the script. Once the boundary has aged past the retention window, everything in the sample should be one version.</p>
<pre><code class="language-bash">python3 stripe_event_version_boundary.py
# single  every one of the 4120 event(s) sampled rendered at 2025-09-30.clover</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/events</code>, plus one against <code>/v1/webhook_endpoints</code> to say whether the boundary reached anything. A restricted key with read access to both is enough. Two pure functions, because there are two questions: how many shapes are in the window, and whether they were delivered. The first has to be given the events newest first, which is the order Stripe returns them in.",
"py_file": "stripe_event_version_boundary.py",
"py": '''"""Report a version boundary inside the retained Stripe event stream.

Read only. Two paginated GETs and no writes: give this a RESTRICTED key with
read access to Events and Webhook Endpoints. The repair is a code change and is
printed, never performed, because this script holds a credential to a live
payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_event_version_boundary")

API = "https://api.stripe.com/v1"

# An event with no api_version gets its own bucket rather than being dropped.
# Dropping it hides the transition that produced it.
UNREPORTED = "unreported"


def label(api_version):
    """One event's version, with a bucket for the absent case. Pure."""
    if api_version is None or api_version == "":
        return UNREPORTED
    return str(api_version)


def verdict(events):
    """Classify the window. Pure, so the ordering logic can be tested offline.

    `events` is a list of dicts with `api_version` and `created`, NEWEST FIRST,
    which is the order the events API returns. Returns (state, detail).
    """
    if not events:
        return ("empty", "no events in the window: nothing to compare")

    seq = [label(e.get("api_version")) for e in events]
    distinct = sorted(set(seq))
    if len(distinct) == 1:
        return ("single",
                "every one of the %d event(s) sampled rendered at %s"
                % (len(seq), distinct[0]))

    transitions = []
    for i in range(len(seq) - 1):
        if seq[i] != seq[i + 1]:
            transitions.append((events[i].get("created"), seq[i + 1], seq[i]))

    if len(transitions) == 1:
        at, older, newer = transitions[0]
        return ("boundary",
                "two shapes in the window: %s up to created=%s, %s from there "
                "on. Any backfill across this window walks through both."
                % (older, at, newer))
    return ("churn",
            "%d transitions between %d versions (%s). That is an upgrade "
            "followed by a rollback inside the 72 hour window: the shape "
            "alternates rather than changing once."
            % (len(transitions), len(distinct), ", ".join(distinct)))


def exposure(endpoint_versions):
    """Did the boundary reach a handler? Pure.

    `endpoint_versions` is the raw api_version of each enabled endpoint. An
    unpinned endpoint follows the account default, so it moved with the stream.
    """
    if not endpoint_versions:
        return ("no-endpoints",
                "no enabled endpoints: the boundary only affects code reading "
                "the events API directly")
    unpinned = [v for v in endpoint_versions if v is None or v == ""]
    if unpinned:
        return ("inherited",
                "%d of %d enabled endpoint(s) are unpinned and follow the "
                "account default, so the boundary was delivered to your handler"
                % (len(unpinned), len(endpoint_versions)))
    return ("pinned",
            "all %d enabled endpoint(s) are pinned, so delivered payloads keep "
            "one shape. The boundary shows up in replays and backfills."
            % len(endpoint_versions))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def sample_events(session, limit):
    """Events newest first, paginated, up to `limit`."""
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def enabled_endpoint_versions(session):
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/webhook_endpoints", **params)
        data = page.get("data", [])
        out.extend(e.get("api_version") for e in data if e.get("status") == "enabled")
        if not data or not page.get("has_more"):
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=5000,
                    help="stop paginating the event stream after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    events = sample_events(s, args.max_events)
    state, detail = verdict(events)
    reach, reach_detail = exposure(enabled_endpoint_versions(s))

    log.info("  sampled %d event(s)", len(events))
    log.info("  %-12s %s", reach, reach_detail)

    if state in ("single", "empty"):
        log.info("%s  %s", state, detail)
        return 0

    log.warning("%s  %s", state, detail)
    log.warning("  there is no Stripe-side repair: stored events are immutable "
                "and are never re-rendered")
    log.warning("  branch on event.api_version for the 30 days the two shapes "
                "coexist, then delete the branch")
    log.warning("  or stop trusting data.object during the overlap and re-fetch "
                "the object by id, which is rendered at your request's version")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-event-version-boundary.mjs",
"js": '''/**
 * Report a version boundary inside the retained Stripe event stream.
 *
 * Read only. Two paginated GETs and no writes: give this a RESTRICTED key with
 * read access to Events and Webhook Endpoints. The repair is a code change and
 * is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// An event with no api_version gets its own bucket rather than being dropped.
// Dropping it hides the transition that produced it.
export const UNREPORTED = 'unreported';

/** One event's version, with a bucket for the absent case. Pure. */
export function label(apiVersion) {
  if (apiVersion === null || apiVersion === undefined || apiVersion === '') {
    return UNREPORTED;
  }
  return String(apiVersion);
}

/**
 * Classify the window. Pure, so the ordering logic can be tested offline.
 * `events` is an array of objects with api_version and created, NEWEST FIRST,
 * which is the order the events API returns.
 */
export function verdict(events) {
  if (!events || events.length === 0) {
    return ['empty', 'no events in the window: nothing to compare'];
  }

  const seq = events.map((e) => label(e.api_version));
  const distinct = [...new Set(seq)].sort();
  if (distinct.length === 1) {
    return ['single',
      `every one of the ${seq.length} event(s) sampled rendered at ${distinct[0]}`];
  }

  const transitions = [];
  for (let i = 0; i < seq.length - 1; i += 1) {
    if (seq[i] !== seq[i + 1]) transitions.push([events[i].created, seq[i + 1], seq[i]]);
  }

  if (transitions.length === 1) {
    const [at, older, newer] = transitions[0];
    return ['boundary',
      `two shapes in the window: ${older} up to created=${at}, ${newer} from ` +
      'there on. Any backfill across this window walks through both.'];
  }
  return ['churn',
    `${transitions.length} transitions between ${distinct.length} versions ` +
    `(${distinct.join(', ')}). That is an upgrade followed by a rollback inside ` +
    'the 72 hour window: the shape alternates rather than changing once.'];
}

/**
 * Did the boundary reach a handler? Pure. `endpointVersions` is the raw
 * api_version of each enabled endpoint.
 */
export function exposure(endpointVersions) {
  if (!endpointVersions || endpointVersions.length === 0) {
    return ['no-endpoints',
      'no enabled endpoints: the boundary only affects code reading the events ' +
      'API directly'];
  }
  const unpinned = endpointVersions.filter(
    (v) => v === null || v === undefined || v === '');
  if (unpinned.length > 0) {
    return ['inherited',
      `${unpinned.length} of ${endpointVersions.length} enabled endpoint(s) are ` +
      'unpinned and follow the account default, so the boundary was delivered ' +
      'to your handler'];
  }
  return ['pinned',
    `all ${endpointVersions.length} enabled endpoint(s) are pinned, so delivered ` +
    'payloads keep one shape. The boundary shows up in replays and backfills.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function sampleEvents(key, limit = 5000) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

export async function enabledEndpointVersions(key) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/webhook_endpoints', params);
    const data = page.data ?? [];
    for (const e of data) if (e.status === 'enabled') out.push(e.api_version);
    if (data.length === 0 || !page.has_more) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const events = await sampleEvents(key);
  const [state, detail] = verdict(events);
  const [reach, reachDetail] = exposure(await enabledEndpointVersions(key));

  console.log(`  sampled ${events.length} event(s)`);
  console.log(`  ${reach.padEnd(12)} ${reachDetail}`);

  if (state === 'single' || state === 'empty') {
    console.log(`${state}  ${detail}`);
    return;
  }

  console.warn(`${state}  ${detail}`);
  console.warn('  there is no Stripe-side repair: stored events are immutable ' +
               'and are never re-rendered');
  console.warn('  branch on event.api_version for the 30 days the two shapes ' +
               'coexist, then delete the branch');
  console.warn('  or stop trusting data.object during the overlap and re-fetch ' +
               "the object by id, which is rendered at your request's version");
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The interesting case is the third one. Two versions with one transition is an upgrade, and the fix is a branch you can delete in thirty days. Two versions with three transitions is an upgrade that was rolled back, so the shape alternates and a handler written for a single cut-over date gets it wrong for a slice of the window. Counting distinct versions cannot tell those apart; counting transitions can.",
"test_py_file": "test_stripe_event_version_boundary.py",
"test_py": '''from stripe_event_version_boundary import exposure, label, verdict

NEW = "2025-09-30.clover"
OLD = "2024-09-30.acacia"


def ev(version, created):
    return {"api_version": version, "created": created}


def test_one_version_across_the_window_is_single():
    state, _ = verdict([ev(NEW, 300), ev(NEW, 200), ev(NEW, 100)])
    assert state == "single"


def test_a_missing_version_is_bucketed_not_dropped():
    # Dropping it removes the transition it produced, and the window reports
    # one clean shape when it has two.
    assert label(None) == label("") == "unreported"
    state, _ = verdict([ev(NEW, 300), ev(None, 200), ev(None, 100)])
    assert state == "boundary"


def test_a_clean_cut_reports_the_transition_timestamp():
    # Newest first, so the transition is the created of the oldest new-shape
    # event: the first moment the new version was in force.
    state, detail = verdict([ev(NEW, 300), ev(NEW, 200), ev(OLD, 100)])
    assert state == "boundary"
    assert "created=200" in detail
    assert OLD in detail and NEW in detail


def test_an_upgrade_that_was_rolled_back_is_not_a_clean_cut():
    state, detail = verdict([ev(OLD, 400), ev(NEW, 300), ev(NEW, 200), ev(OLD, 100)])
    assert state == "churn"
    assert "72 hour" in detail


def test_one_unpinned_endpoint_means_the_boundary_was_delivered():
    assert exposure([NEW, None])[0] == "inherited"
    assert exposure([NEW, ""])[0] == "inherited"
    assert exposure([NEW, OLD])[0] == "pinned"
    assert exposure([])[0] == "no-endpoints"
''',
"test_js_file": "stripe-event-version-boundary.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { exposure, label, verdict } from './stripe-event-version-boundary.mjs';

const NEW = '2025-09-30.clover';
const OLD = '2024-09-30.acacia';
const ev = (api_version, created) => ({ api_version, created });

test('one version across the window is single', () => {
  assert.equal(verdict([ev(NEW, 300), ev(NEW, 200), ev(NEW, 100)])[0], 'single');
});

test('a missing version is bucketed not dropped', () => {
  assert.equal(label(null), 'unreported');
  assert.equal(label(''), 'unreported');
  assert.equal(verdict([ev(NEW, 300), ev(null, 200), ev(null, 100)])[0], 'boundary');
});

test('a clean cut reports the transition timestamp', () => {
  const [state, detail] = verdict([ev(NEW, 300), ev(NEW, 200), ev(OLD, 100)]);
  assert.equal(state, 'boundary');
  assert.match(detail, /created=200/);
  assert.ok(detail.includes(OLD) && detail.includes(NEW));
});

test('an upgrade that was rolled back is not a clean cut', () => {
  const [state, detail] = verdict([ev(OLD, 400), ev(NEW, 300), ev(NEW, 200), ev(OLD, 100)]);
  assert.equal(state, 'churn');
  assert.match(detail, /72 hour/);
});

test('one unpinned endpoint means the boundary was delivered', () => {
  assert.equal(exposure([NEW, null])[0], 'inherited');
  assert.equal(exposure([NEW, ''])[0], 'inherited');
  assert.equal(exposure([NEW, OLD])[0], 'pinned');
  assert.equal(exposure([])[0], 'no-endpoints');
});
''',
"faq": [
 ("Can I re-render an old event at the current version?",
  "No. Event objects are immutable, including their api_version, and Stripe never re-renders them. If you need the current shape of the underlying object, fetch it by ID instead: that request is served at whatever version you ask for."),
 ("Why did replaying an old event succeed when the live one failed?",
  "Because they were rendered at different versions. The replayed one predates the boundary and carries the shape your handler was written for; the live one is on the other side of it. Same code, same event type, different payload."),
 ("Does a pinned endpoint protect me from this?",
  "In production, largely yes: a pinned endpoint renders delivered payloads at its own version regardless of the event's. It does not protect a backfill, because code reading GET /v1/events sees the events as stored, boundary and all."),
 ("How many api_version values should a healthy account show?",
  "One, for any window that does not contain an upgrade. Two is an upgrade you can date. More than two transitions between the same versions is a rollback, and it means the shape alternates rather than changing once."),
 ("How long do I have to keep the compatibility branch?",
  "Thirty days from the boundary. Events are retained for 30 days, so once the last pre-boundary event ages out there is nothing left in the API that carries the old shape, and the branch can go."),
],
"related": [
 ("/stripe/endpoint-api-version-drift/", "Endpoints render events at different pinned API versions"),
 ("/stripe/account-default-api-version-stale/", "Account default API version is years behind the current one"),
 ("/stripe/undelivered-events-nearing-retention/", "Undelivered events are aging out of the retention window"),
],
"citations": [CITE_EVENT_OBJ, CITE_EVENTS_LIST, CITE_UPGRADES, CITE_VERSIONING],
},

{
"slug": "idempotency-key-reuse-conflict",
"title": "Reused idempotency keys hit 409 idempotency_key_in_use",
"description": "Checkout fails for a slice of users under load with a 409, or duplicates appear a day later. The same key is on more than one request id.",
"h1": "reused idempotency keys hit 409 idempotency_key_in_use",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["idempotency_key_in_use", "stripe 409 conflict",
             "stripe idempotency_error same parameters", "stripe duplicate key",
             "stripe idempotency key expiry"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The keys are being sent. That is what makes this different from <a href=\"/stripe/missing-idempotency-keys-on-payments/\">payment requests with no key at all</a>, where the header is simply absent. Here every request carries one, and the same one keeps turning up on requests that are not the same operation &mdash; so under load a slice of checkouts fails with <code>409 idempotency_key_in_use</code>, and a day later the protection stops working entirely and the duplicates come back.",
"short_answer": """<p>Page <code>GET /v1/events</code> across the retained window and group the events by <code>request.idempotency_key</code>, ignoring nulls. A key that appears against more than one distinct <code>request.id</code> was not deduplicated: both requests really executed. Inside 24 hours that is two concurrent operations sharing a key, which is the <code>409</code>. Beyond 24 hours it is a key that was pruned and then reused, which is a duplicate rather than a replay.</p>
<p>Then look at the shape of the keys themselves. Anything that reads as a customer ID, a PaymentIntent ID, a user ID, a bare integer, a date or an email address is derived from something that repeats, and it will collide as soon as that thing comes round again.</p>""",
"problem": """<p>Two different failures come out of the same mistake, and they arrive weeks apart. The first is a <code>409 Conflict</code> reading <em>There is currently another in-progress request using this Idempotent Key</em>. It only happens under concurrency, so it is rare in staging and clustered at your busiest hour in production, which makes it look like a capacity problem. The second is a <code>400 idempotency_error</code>: <em>Keys for idempotent requests can only be used with the same parameters they were first used with.</em> That one names the cause precisely and is still usually read as a Stripe quirk.</p>
<p>The third outcome is the one nobody sees. Keys are pruned after roughly 24 hours. A key derived from a customer ID protects a retry at 10:00 and does nothing at all for the same customer the next morning, because Stripe has forgotten it and starts a genuinely new operation. The protection appears to work for as long as anybody tests it, and fails on exactly the timescale nobody tests.</p>""",
"why": """<p><strong>Stripe saves the result after execution begins, not before.</strong> Two requests carrying one key that arrive close enough together both get past that point, so neither can replay the other. One of them gets the <code>409</code>. It is a retryable error, and the correct retry uses the <em>same</em> key &mdash; but the reason it happened is that the key is shared between operations that should have had their own.</p>
<p><strong>Keys live for about 24 hours.</strong> After that they are pruned, and a request carrying a pruned key is brand new. Any key derived from something long-lived &mdash; a customer, an order, a cart &mdash; is fine for hours and useless for days, which is why the duplicates look uncorrelated with the retries.</p>
<p><strong>Same key plus different parameters is an error, not a replay.</strong> Reusing a key across two operations that differ at all returns <code>idempotency_error</code>. So a key derived from an order ID breaks the moment one order creates both a customer and a PaymentIntent, or the moment a failed payment is retried with a different amount.</p>
<p><strong>The evidence is in the events, and it needs two conditions.</strong> Every event carries the <code>request</code> that caused it, including its <code>idempotency_key</code>. One key on one request ID is normal. One key on several request IDs means the deduplication did not happen, and the spread between their timestamps says which of the two failures you have.</p>""",
"steps": [
 {"h": "Page the window and group by key",
  "body": """<p><code>GET /v1/events?limit=100</code> with <code>starting_after</code>. Skip events where <code>request.idempotency_key</code> is null: Stripe-initiated events never had a key, and unkeyed API requests are a different problem with a different fix.</p>"""},
 {"h": "Count distinct request ids per key",
  "body": """<p>One key on one <code>request.id</code> is a key doing its job. Two or more means both requests executed, so nothing was deduplicated. That is the finding, and it is a fact rather than an inference.</p>"""},
 {"h": "Measure the spread between the timestamps",
  "body": """<p>More than 86400 seconds between the first and last event for a key puts the reuse either side of the pruning window. That is a duplicate created rather than a conflict returned, and it is the more expensive of the two.</p>"""},
 {"h": "Read the shape of the key",
  "body": """<p>A key that starts <code>cus_</code>, <code>pi_</code> or <code>user_</code>, or that parses as a bare integer or a date, or that contains an <code>@</code>, is derived from something that repeats. It has not necessarily collided yet; it will. Personal identifiers are also simply not acceptable as keys.</p>"""},
 {"h": "Generate one key per logical operation and persist it",
  "body": """<p>A v4 UUID, made once when the operation is first attempted, written next to the operation record, and reused byte for byte on every retry of that exact request. Keys cap at 255 characters. On a <code>409</code>, back off and retry with the same key rather than minting a new one.</p>"""},
],
"verify": """<p>Re-run the script after the deploy. Because the window is rolling, the old keys stay in the sample for 30 days; the number to watch is that no key created since the deploy appears twice.</p>
<pre><code class="language-bash">python3 stripe_idempotency_key_reuse.py --days 1
# 412 key(s) sampled, 0 reused, 0 derived from something that repeats</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/events</code> &mdash; a restricted key with read access to Events is enough. Two pure functions: one reads the shape of a key string, the other turns a key's tally into a verdict. Keeping them apart matters because a key can be perfectly unique so far and still be built out of something that will repeat next Tuesday, and that is a finding the counts alone cannot produce.",
"py_file": "stripe_idempotency_key_reuse.py",
"py": '''"""Report Stripe idempotency keys reused across more than one request.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Events. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_idempotency_key_reuse")

API = "https://api.stripe.com/v1"

# Stripe prunes saved idempotency results after roughly 24 hours. A key seen
# either side of that gap was not replayed; it started a new operation.
PRUNE_WINDOW = 86400
MAX_KEY_LEN = 255

OBJECT_ID = re.compile(r"^(cus_|pi_|ch_|sub_|in_|seti_|user[-_])", re.I)
UUID4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
ISO_DATE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}")


def key_shape(key):
    """What a key string is built out of. Pure.

    Returns (shape, description). Anything but "uuid" and "opaque" is derived
    from something that comes round again, whether or not it has collided yet.
    """
    if key is None or key == "":
        return ("missing", "no key at all")
    k = str(key)
    if len(k) > MAX_KEY_LEN:
        return ("over-long",
                "%d characters, over the %d limit" % (len(k), MAX_KEY_LEN))
    if "@" in k:
        return ("personal",
                "an email address, which repeats and should not be sent as a key")
    if UUID4.match(k):
        return ("uuid", "a v4 uuid")
    if OBJECT_ID.match(k):
        return ("object-id", "an object id, which repeats every time that object "
                             "is used again")
    if k.isdigit():
        return ("integer", "a bare integer, which repeats")
    if ISO_DATE.match(k):
        return ("date", "a date, which repeats for every operation that day")
    return ("opaque", "not obviously derived from anything that repeats")


def verdict(key, request_ids, spread_seconds):
    """Classify one key's tally. Pure, so the thresholds can be tested.

    `request_ids` is the number of distinct request ids carrying this key, and
    `spread_seconds` the gap between its first and last event.
    """
    shape, described = key_shape(key)
    if request_ids > 1 and spread_seconds > PRUNE_WINDOW:
        return ("pruned",
                "%d distinct requests, %d seconds apart. Stripe forgets a key "
                "after about %d seconds, so the later one started a fresh "
                "operation and created a duplicate rather than replaying."
                % (request_ids, spread_seconds, PRUNE_WINDOW))
    if request_ids > 1:
        return ("concurrent",
                "%d distinct requests inside the window Stripe remembers the "
                "key. Both executed, so the key is shared between operations "
                "rather than unique to one. Under load this returns 409 "
                "idempotency_key_in_use." % request_ids)
    if shape not in ("uuid", "opaque"):
        return ("derived",
                "one request so far, but the key is %s" % described)
    return ("unique", "one request, and the key is %s" % described)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def keys_seen(session, since, limit):
    """Per-key distinct request ids and the timestamp spread. Keyed requests only."""
    seen = {}
    total = 0
    params = {"limit": 100, "created[gte]": int(since)}
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        for ev in data:
            total += 1
            req = ev.get("request")
            if not isinstance(req, dict):
                continue  # Stripe-initiated, or an old bare-string request field
            key = req.get("idempotency_key")
            if not key:
                continue  # unkeyed requests are a different problem
            row = seen.setdefault(key, {"ids": set(), "first": None, "last": None})
            if req.get("id"):
                row["ids"].add(req["id"])
            created = ev.get("created")
            if created is not None:
                row["first"] = created if row["first"] is None else min(row["first"], created)
                row["last"] = created if row["last"] is None else max(row["last"], created)
        if not data or not page.get("has_more") or total >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return seen, total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to sample, up to the 30-day retention limit")
    ap.add_argument("--max-events", type=int, default=5000,
                    help="stop paginating after this many events")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = time.time() - args.days * 86400
    seen, total = keys_seen(s, since, args.max_events)
    log.info("sampled %d event(s) over %d day(s)", total, args.days)

    reused = derived = 0
    for k in sorted(seen):
        row = seen[k]
        spread = (row["last"] or 0) - (row["first"] or 0)
        state, detail = verdict(k, len(row["ids"]) or 1, spread)
        if state == "unique":
            continue
        line = "%-11s %-40s %s" % (state, k[:40], detail)
        if state == "derived":
            derived += 1
            log.info(line)
        else:
            reused += 1
            log.warning(line)

    if reused or derived:
        log.warning("  repair: one fresh v4 uuid per logical operation, made when "
                    "the operation is first attempted")
        log.warning("  persist it next to the operation record and resend it "
                    "unchanged for every retry of that exact request")
        log.warning("  on 409 idempotency_key_in_use, back off and retry with the "
                    "same key rather than minting a new one")
        log.warning("  never derive a key from a customer id, an order id, a date "
                    "or an email address; keys cap at %d characters", MAX_KEY_LEN)
    log.info("%d key(s) sampled, %d reused, %d derived from something that repeats",
             len(seen), reused, derived)
    return 1 if reused else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-idempotency-key-reuse.mjs",
"js": '''/**
 * Report Stripe idempotency keys reused across more than one request.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Stripe prunes saved idempotency results after roughly 24 hours. A key seen
// either side of that gap was not replayed; it started a new operation.
export const PRUNE_WINDOW = 86400;
const MAX_KEY_LEN = 255;

const OBJECT_ID = /^(cus_|pi_|ch_|sub_|in_|seti_|user[-_])/i;
const UUID4 =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ISO_DATE = /^\\d{4}-\\d{2}-\\d{2}/;

/**
 * What a key string is built out of. Pure. Returns [shape, description].
 * Anything but 'uuid' and 'opaque' is derived from something that comes round
 * again, whether or not it has collided yet.
 */
export function keyShape(key) {
  if (key === null || key === undefined || key === '') {
    return ['missing', 'no key at all'];
  }
  const k = String(key);
  if (k.length > MAX_KEY_LEN) {
    return ['over-long', `${k.length} characters, over the ${MAX_KEY_LEN} limit`];
  }
  if (k.includes('@')) {
    return ['personal',
      'an email address, which repeats and should not be sent as a key'];
  }
  if (UUID4.test(k)) return ['uuid', 'a v4 uuid'];
  if (OBJECT_ID.test(k)) {
    return ['object-id',
      'an object id, which repeats every time that object is used again'];
  }
  if (/^\\d+$/.test(k)) return ['integer', 'a bare integer, which repeats'];
  if (ISO_DATE.test(k)) {
    return ['date', 'a date, which repeats for every operation that day'];
  }
  return ['opaque', 'not obviously derived from anything that repeats'];
}

/**
 * Classify one key's tally. Pure, so the thresholds can be tested.
 * `requestIds` is the number of distinct request ids carrying this key.
 */
export function verdict(key, requestIds, spreadSeconds) {
  const [shape, described] = keyShape(key);
  if (requestIds > 1 && spreadSeconds > PRUNE_WINDOW) {
    return ['pruned',
      `${requestIds} distinct requests, ${spreadSeconds} seconds apart. Stripe ` +
      `forgets a key after about ${PRUNE_WINDOW} seconds, so the later one ` +
      'started a fresh operation and created a duplicate rather than replaying.'];
  }
  if (requestIds > 1) {
    return ['concurrent',
      `${requestIds} distinct requests inside the window Stripe remembers the ` +
      'key. Both executed, so the key is shared between operations rather than ' +
      'unique to one. Under load this returns 409 idempotency_key_in_use.'];
  }
  if (shape !== 'uuid' && shape !== 'opaque') {
    return ['derived', `one request so far, but the key is ${described}`];
  }
  return ['unique', `one request, and the key is ${described}`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function keysSeen(key, since, limit = 5000) {
  const seen = new Map();
  let total = 0;
  const params = { limit: 100, 'created[gte]': Math.floor(since) };
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    for (const ev of data) {
      total += 1;
      const req = ev.request;
      if (!req || typeof req !== 'object') continue;
      const idem = req.idempotency_key;
      if (!idem) continue; // unkeyed requests are a different problem
      if (!seen.has(idem)) seen.set(idem, { ids: new Set(), first: null, last: null });
      const row = seen.get(idem);
      if (req.id) row.ids.add(req.id);
      const created = ev.created;
      if (created !== null && created !== undefined) {
        row.first = row.first === null ? created : Math.min(row.first, created);
        row.last = row.last === null ? created : Math.max(row.last, created);
      }
    }
    if (data.length === 0 || !page.has_more || total >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { seen, total };
}

async function main() {
  const apiKey = process.env.STRIPE_API_KEY;
  if (!apiKey) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 30);
  const since = Date.now() / 1000 - days * 86400;
  const { seen, total } = await keysSeen(apiKey, since);
  console.log(`sampled ${total} event(s) over ${days} day(s)`);

  let reused = 0;
  let derived = 0;
  for (const k of [...seen.keys()].sort()) {
    const row = seen.get(k);
    const spread = (row.last ?? 0) - (row.first ?? 0);
    const [state, detail] = verdict(k, row.ids.size || 1, spread);
    if (state === 'unique') continue;
    const line = `${state.padEnd(11)} ${k.slice(0, 40).padEnd(40)} ${detail}`;
    if (state === 'derived') { derived += 1; console.log(line); }
    else { reused += 1; console.warn(line); }
  }

  if (reused || derived) {
    console.warn('  repair: one fresh v4 uuid per logical operation, made when ' +
                 'the operation is first attempted');
    console.warn('  persist it next to the operation record and resend it ' +
                 'unchanged for every retry of that exact request');
    console.warn('  on 409 idempotency_key_in_use, back off and retry with the ' +
                 'same key rather than minting a new one');
    console.warn('  never derive a key from a customer id, an order id, a date ' +
                 `or an email address; keys cap at ${MAX_KEY_LEN} characters`);
  }
  console.log(`${seen.size} key(s) sampled, ${reused} reused, ${derived} derived ` +
              'from something that repeats');
  process.exitCode = reused ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first two tests separate the two failures, which matter differently. Inside the pruning window a shared key produces a <code>409</code> that a caller can retry: noisy, survivable. Outside it, the same shared key produces a second real charge and no error at all. The gap between the timestamps is the only thing in the data that tells them apart, so it is worth pinning that the threshold is read the right way round.",
"test_py_file": "test_stripe_idempotency_key_reuse.py",
"test_py": '''from stripe_idempotency_key_reuse import key_shape, verdict

UUID = "6f9619ff-8b86-4d01-b42d-00cf4fc964ff"


def test_two_requests_inside_the_window_is_the_409():
    state, detail = verdict(UUID, 2, 30)
    assert state == "concurrent"
    assert "409" in detail


def test_two_requests_a_day_apart_is_a_duplicate_not_a_conflict():
    # Past the pruning window Stripe has forgotten the key, so the second
    # request is genuinely new and no error is returned at all.
    state, detail = verdict(UUID, 2, 108000)
    assert state == "pruned"
    assert "86400" in detail


def test_a_key_built_from_a_customer_id_is_flagged_before_it_collides():
    assert key_shape("cus_Nc1mzuAyRlKmGT")[0] == "object-id"
    state, _ = verdict("cus_Nc1mzuAyRlKmGT", 1, 0)
    assert state == "derived"


def test_an_email_address_is_never_an_acceptable_key():
    shape, described = key_shape("ada@example.com")
    assert shape == "personal"
    assert "email" in described
    assert verdict("ada@example.com", 1, 0)[0] == "derived"


def test_a_uuid_on_one_request_is_clean():
    assert key_shape(UUID)[0] == "uuid"
    assert verdict(UUID, 1, 0)[0] == "unique"
    assert key_shape("2026-08-30")[0] == "date"
    assert key_shape("41231")[0] == "integer"
''',
"test_js_file": "stripe-idempotency-key-reuse.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keyShape, verdict } from './stripe-idempotency-key-reuse.mjs';

const UUID = '6f9619ff-8b86-4d01-b42d-00cf4fc964ff';

test('two requests inside the window is the 409', () => {
  const [state, detail] = verdict(UUID, 2, 30);
  assert.equal(state, 'concurrent');
  assert.match(detail, /409/);
});

test('two requests a day apart is a duplicate not a conflict', () => {
  const [state, detail] = verdict(UUID, 2, 108000);
  assert.equal(state, 'pruned');
  assert.match(detail, /86400/);
});

test('a key built from a customer id is flagged before it collides', () => {
  assert.equal(keyShape('cus_Nc1mzuAyRlKmGT')[0], 'object-id');
  assert.equal(verdict('cus_Nc1mzuAyRlKmGT', 1, 0)[0], 'derived');
});

test('an email address is never an acceptable key', () => {
  const [shape, described] = keyShape('ada@example.com');
  assert.equal(shape, 'personal');
  assert.match(described, /email/);
  assert.equal(verdict('ada@example.com', 1, 0)[0], 'derived');
});

test('a uuid on one request is clean', () => {
  assert.equal(keyShape(UUID)[0], 'uuid');
  assert.equal(verdict(UUID, 1, 0)[0], 'unique');
  assert.equal(keyShape('2026-08-30')[0], 'date');
  assert.equal(keyShape('41231')[0], 'integer');
});
''',
"faq": [
 ("Is reusing an idempotency key ever correct?",
  "Yes, for a retry of the exact same request with the exact same parameters. That is the entire point of the key. What this check finds is a key reused for a different operation, or reused so long after the first that Stripe has already forgotten it."),
 ("What does 409 idempotency_key_in_use actually mean?",
  "Two requests carrying the same key arrived close enough together that neither result had been saved yet. Stripe saves the response only after execution begins, so there was nothing to replay. It is retryable, and the retry should carry the same key."),
 ("Why do duplicates come back after a day?",
  "Because the key was pruned. Saved idempotency results live for roughly 24 hours. A key derived from something long-lived, like a customer or an order, protects retries within that day and does nothing at all the next morning, when Stripe treats it as a key it has never seen."),
 ("What is the difference between the 409 and idempotency_error?",
  "The 409 is a timing collision: same key, two in-flight requests. The idempotency_error is a semantic one: same key, different parameters. The first says your key is shared across concurrent operations; the second says it is shared across different ones."),
 ("How is this different from sending no key at all?",
  "A missing key means every retry executes, always. A reused key means deduplication works right up until the moment two requests collide or the key is pruned, so it fails intermittently and looks like load rather than like a bug. The detection is different too: this one groups by the key, the other one looks for its absence."),
],
"related": [
 ("/stripe/missing-idempotency-keys-on-payments/", "Payment-creating requests carry no idempotency key"),
 ("/stripe/duplicate-customers-same-email/", "One customer has several Customer records"),
 ("/stripe/duplicate-endpoints-same-url/", "Two endpoints share one URL, so every event is handled twice"),
],
"citations": [CITE_IDEMPOTENCY, CITE_ERRORS, CITE_EVENT_OBJ, CITE_EVENTS_LIST],
},

]
