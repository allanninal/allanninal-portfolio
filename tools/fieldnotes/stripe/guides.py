#!/usr/bin/env python3
"""/stripe/ field notes — the writing.

Every note here is a problem a script can find with a RESTRICTED, READ-ONLY
Stripe key. That constraint is the whole design: these scripts hold a credential
to a live payments account, so none of them writes. They read, they say exactly
what is wrong, and they print the repair for a human to run.
"""

CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")
CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")
CITE_UNDELIVERED = ("Process undelivered events — Stripe Docs",
                    "https://docs.stripe.com/webhooks/process-undelivered-events")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

GUIDES = [

{
"slug": "webhook-endpoint-disabled",
"title": "A webhook endpoint sits disabled after days of retries",
"description": "Events flowed for months, then stopped on one date with nothing in the logs. Stripe disabled the endpoint and no longer retries it.",
"h1": "a webhook endpoint sits disabled after days of retries",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe webhook disabled", "stripe webhook not firing",
             "webhook endpoint status disabled", "stripe events not delivered",
             "stripe webhook retries"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Orders stopped being fulfilled on a Tuesday. Nothing changed in your code that week, nothing appears in your application logs, and Stripe still shows the payments as succeeded. Nothing is arriving at all &mdash; Stripe gave up on the endpoint and stopped trying.",
"short_answer": """<p>Read <code>GET /v1/webhook_endpoints</code> and look for <code>status</code> of <code>"disabled"</code>. Stripe retries a failing destination with exponential backoff for up to three days in live mode; sustained non-2xx responses end with the endpoint disabled, after which it stops retrying entirely.</p>
<p>Then size the damage with <code>GET /v1/events?delivery_success=false</code>. Events are retained for 30 days, so a backfill is possible &mdash; but only inside that window.</p>""",
"problem": """<p>This failure is quiet in a way that most are not. There is no error in your logs, because no request is reaching you. There is no error in Stripe's dashboard unless you open the endpoint itself. The payments keep succeeding, so revenue looks normal; it is only the work that <em>follows</em> a payment &mdash; the fulfilment, the licence key, the welcome email &mdash; that stops.</p>
<p>It also tends to be discovered by a customer rather than by you. Someone paid, and nothing happened, and they wrote in. By then the three-day retry window has usually closed and some of the events are past the point where Stripe will hand them back.</p>""",
"why": """<p><strong>The endpoint failed for reasons that had nothing to do with Stripe.</strong> A rotated signing secret makes your handler reject every event with a 400. A route renamed during a refactor returns 404. A WAF rule or a new firewall returns 403. Each of those is a perfectly ordinary change, and each of them looks like a healthy deploy from your side.</p>
<p><strong>The retry schedule hides the beginning.</strong> Stripe backs off exponentially, so the first few hours look like a blip. By the time the pattern is obvious, it has been failing for a day.</p>
<p><strong>Disabling is deliberate, and it is terminal for pending events.</strong> Once the endpoint is disabled Stripe stops retrying the events that were queued for it. Re-enabling does not replay them; you have to go and fetch them.</p>""",
"steps": [
 {"h": "List every endpoint and read its status",
  "body": """<p>Do this for both modes. A test-mode endpoint and a live-mode endpoint are separate objects with separate secrets, and it is common for one to be healthy while the other is not.</p>"""},
 {"h": "Count what did not arrive",
  "body": """<p><code>GET /v1/events?delivery_success=false</code> returns the events Stripe could not deliver. The count is the size of your backfill; the earliest <code>created</code> timestamp is when the endpoint really broke, which is usually earlier than anyone remembers.</p>"""},
 {"h": "Fix the handler before re-enabling",
  "body": """<p>Re-enabling a still-broken endpoint just spends another three days of retries. Confirm the route answers 2xx to a signed test event first.</p>"""},
 {"h": "Re-enable, then replay",
  "body": """<p><code>POST /v1/webhook_endpoints/{id}</code> with <code>disabled=false</code>. Then walk the undelivered events and push them through your own handler. Your handler has to be idempotent on <code>event.id</code> for this to be safe, which is worth confirming before you start.</p>"""},
 {"h": "Add the check to something that runs weekly",
  "body": """<p>This is a state you can poll for in one API call. Anything that notices a disabled endpoint on day one instead of day thirty pays for itself immediately.</p>"""},
],
"verify": """<p>Re-run the script. Every endpoint should report <code>enabled</code> and the undelivered count should be zero.</p>
<pre><code class="language-bash">python3 stripe_webhook_health.py
# 2 endpoint(s), 0 disabled, 0 undelivered event(s) in the last 30 days</code></pre>""",
"code_intro": "The script makes two GET requests and no writes at all &mdash; a restricted key with read access to Webhook Endpoints and Events is enough, and is what you should give it. The classification is a pure function so the rules are visible and testable rather than buried in the request loop.",
"py_file": "stripe_webhook_health.py",
"py": '''"""Report Stripe webhook endpoints that are disabled or losing events.

Read only. Two GET requests, no writes: give this a RESTRICTED key with read
access to Webhook Endpoints and Events. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_webhook_health")

API = "https://api.stripe.com/v1"


def verdict(endpoint, undelivered):
    """Classify one endpoint. Pure, so the rules can be tested without a network.

    Returns (state, detail). `undelivered` is the count of failed deliveries seen
    for this endpoint in the retained window.
    """
    status = endpoint.get("status")
    if status == "disabled":
        return ("disabled",
                "Stripe stopped delivering after repeated failures. "
                "Re-enable only after the handler answers 2xx.")
    if status != "enabled":
        return ("unknown", "unrecognised status %r" % (status,))
    if undelivered:
        return ("failing",
                "%d event(s) did not deliver. The endpoint is still enabled, so "
                "you have time before Stripe disables it." % undelivered)
    return ("healthy", "delivering normally")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def undelivered_by_endpoint(session, limit):
    """Count failed deliveries per endpoint id.

    Stripe returns the destinations an event failed to reach, so the count is
    attributed rather than guessed. Events are retained for 30 days; anything
    older than that cannot be replayed and is not counted here.
    """
    counts = {}
    total = 0
    params = {"delivery_success": "false", "limit": 100}
    while True:
        page = get(session, "/events", **params)
        for ev in page.get("data", []):
            total += 1
            for dest in ev.get("pending_webhooks_destinations", []) or []:
                counts[dest] = counts.get(dest, 0) + 1
        if not page.get("has_more") or total >= limit:
            break
        params["starting_after"] = page["data"][-1]["id"]
    return counts, total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=1000,
                    help="stop counting undelivered events after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    if not endpoints:
        log.info("no webhook endpoints configured for this key's mode")
        return 0

    per_endpoint, total_undelivered = undelivered_by_endpoint(s, args.max_events)

    bad = 0
    for ep in endpoints:
        state, detail = verdict(ep, per_endpoint.get(ep["id"], 0))
        line = "%-9s %s  %s" % (state, ep.get("url", "?"), detail)
        if state == "healthy":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "disabled":
            log.warning("  repair: POST %s/webhook_endpoints/%s -d disabled=false",
                        API, ep["id"])
            log.warning("  then replay: GET %s/events?delivery_success=false", API)

    log.info("%d endpoint(s), %d needing attention, %d undelivered event(s)",
             len(endpoints), bad, total_undelivered)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-webhook-health.mjs",
"js": '''/**
 * Report Stripe webhook endpoints that are disabled or losing events.
 *
 * Read only. Two GET requests, no writes: give this a RESTRICTED key with read
 * access to Webhook Endpoints and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one endpoint. Pure, so the rules can be tested without a network.
 */
export function verdict(endpoint, undelivered) {
  const status = endpoint.status;
  if (status === 'disabled') {
    return ['disabled',
      'Stripe stopped delivering after repeated failures. Re-enable only after ' +
      'the handler answers 2xx.'];
  }
  if (status !== 'enabled') {
    return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
  }
  if (undelivered) {
    return ['failing',
      `${undelivered} event(s) did not deliver. The endpoint is still enabled, ` +
      'so you have time before Stripe disables it.'];
  }
  return ['healthy', 'delivering normally'];
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

export async function undeliveredByEndpoint(key, limit = 1000) {
  const counts = new Map();
  let total = 0;
  const params = { delivery_success: 'false', limit: 100 };
  for (;;) {
    const page = await get(key, '/events', params);
    for (const ev of page.data ?? []) {
      total += 1;
      for (const dest of ev.pending_webhooks_destinations ?? []) {
        counts.set(dest, (counts.get(dest) ?? 0) + 1);
      }
    }
    if (!page.has_more || total >= limit) break;
    params.starting_after = page.data[page.data.length - 1].id;
  }
  return { counts, total };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  if (endpoints.length === 0) {
    console.log("no webhook endpoints configured for this key's mode");
    return;
  }

  const { counts, total } = await undeliveredByEndpoint(key);

  let bad = 0;
  for (const ep of endpoints) {
    const [state, detail] = verdict(ep, counts.get(ep.id) ?? 0);
    const line = `${state.padEnd(9)} ${ep.url ?? '?'}  ${detail}`;
    if (state === 'healthy') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'disabled') {
      console.warn(`  repair: POST ${API}/webhook_endpoints/${ep.id} -d disabled=false`);
      console.warn(`  then replay: GET ${API}/events?delivery_success=false`);
    }
  }

  console.log(`${endpoints.length} endpoint(s), ${bad} needing attention, ` +
              `${total} undelivered event(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning is an enabled endpoint with failures against it. It is not healthy and it is not disabled either &mdash; it is the window in which you can still fix this without replaying anything, and collapsing it into either neighbour is what turns a warning into an outage.",
"test_py_file": "test_stripe_webhook_health.py",
"test_py": '''from stripe_webhook_health import verdict


def test_disabled_endpoint_is_reported_regardless_of_event_count():
    state, detail = verdict({"status": "disabled"}, 0)
    assert state == "disabled"
    assert "2xx" in detail


def test_enabled_and_quiet_is_healthy():
    state, _ = verdict({"status": "enabled"}, 0)
    assert state == "healthy"


def test_enabled_with_failures_is_its_own_state():
    # The point of the note: this is the window before Stripe disables it.
    state, detail = verdict({"status": "enabled"}, 12)
    assert state == "failing"
    assert "12" in detail


def test_unknown_status_is_not_silently_healthy():
    state, _ = verdict({"status": "paused"}, 0)
    assert state == "unknown"


def test_missing_status_is_not_silently_healthy():
    state, _ = verdict({}, 0)
    assert state == "unknown"
''',
"test_js_file": "stripe-webhook-health.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-webhook-health.mjs';

test('disabled endpoint is reported regardless of event count', () => {
  const [state, detail] = verdict({ status: 'disabled' }, 0);
  assert.equal(state, 'disabled');
  assert.match(detail, /2xx/);
});

test('enabled and quiet is healthy', () => {
  assert.equal(verdict({ status: 'enabled' }, 0)[0], 'healthy');
});

test('enabled with failures is its own state', () => {
  const [state, detail] = verdict({ status: 'enabled' }, 12);
  assert.equal(state, 'failing');
  assert.match(detail, /12/);
});

test('unknown status is not silently healthy', () => {
  assert.equal(verdict({ status: 'paused' }, 0)[0], 'unknown');
});

test('missing status is not silently healthy', () => {
  assert.equal(verdict({}, 0)[0], 'unknown');
});
''',
"faq": [
 ("Why did Stripe disable my webhook endpoint?",
  "Because it kept returning non-2xx. Stripe retries with exponential backoff for up to three days in live mode, and disables the endpoint if the failures continue through that window. The cause is almost always on your side: a rotated signing secret rejecting every event, a route that moved during a refactor, or a firewall rule added since."),
 ("Does re-enabling the endpoint replay the events I missed?",
  "No. Re-enabling resumes future deliveries only. The events queued while it was disabled have to be fetched with GET /v1/events?delivery_success=false and pushed through your handler yourself."),
 ("How long do I have to backfill?",
  "Events are retained for 30 days. Past that they are gone from the API, and the only record is whatever your own logs and the payment objects themselves can reconstruct."),
 ("Will replaying events double-charge or double-fulfil anything?",
  "Only if your handler is not idempotent. Stripe guarantees at-least-once delivery, so duplicates are normal even without a replay. Key your side effects on event.id and a replay is safe by construction."),
 ("Can I detect this without a live secret key?",
  "Yes, and you should. A restricted key with read access to Webhook Endpoints and Events is enough for this check, and it cannot move money if it leaks."),
],
"related": [
 ("/bigcommerce/order-webhooks-stop-firing-silently/", "Order webhooks that stop firing silently"),
 ("/bigcommerce/missed-webhooks-with-no-backfill/", "Missed webhooks with no backfill"),
 ("/woocommerce/duplicate-webhook-events/", "Duplicate webhook events run the handler twice"),
],
"citations": [CITE_WEBHOOK_OBJ, CITE_WEBHOOKS, CITE_UNDELIVERED, CITE_KEYS],
},

]
