#!/usr/bin/env python3
"""/stripe/ field notes, batch L — the writing.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair
for a human to run against a live payments account.

This batch is about the delivery side of webhooks rather than the shape of the
subscription list: whether a destination exists at all, whether the events that
were sent ever landed, and whether the two signals that end a customer
relationship — the subscription ending and the chargeback arriving — have
anywhere to arrive.
"""

CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")
CITE_WEBHOOK_CREATE = ("Create a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/create")
CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")
CITE_CLI = ("Stripe CLI — Stripe Docs", "https://docs.stripe.com/stripe-cli")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")
CITE_EVENT_OBJ = ("The event object — Stripe API reference",
                  "https://docs.stripe.com/api/events/object")
CITE_EVENTS_LIST = ("List all events — Stripe API reference",
                    "https://docs.stripe.com/api/events/list")
CITE_UNDELIVERED = ("Process undelivered events — Stripe Docs",
                    "https://docs.stripe.com/webhooks/process-undelivered-events")
CITE_EVENT_TYPES = ("Types of events — Stripe API reference",
                    "https://docs.stripe.com/api/events/types")
CITE_SUB_OBJ = ("The subscription object — Stripe API reference",
                "https://docs.stripe.com/api/subscriptions/object")
CITE_SUB_CANCEL = ("Cancel subscriptions — Stripe Docs",
                   "https://docs.stripe.com/billing/subscriptions/cancel")
CITE_EFW = ("Early fraud warnings — Stripe API reference",
            "https://docs.stripe.com/api/radar/early_fraud_warnings")
CITE_DISPUTES = ("Disputes and fraud — Stripe Docs", "https://docs.stripe.com/disputes")
CITE_RADAR_TESTING = ("Testing Radar — Stripe Docs",
                      "https://docs.stripe.com/radar/testing")

GUIDES = [

{
"slug": "no-live-webhook-endpoints",
"title": "Live mode has no webhook endpoint, so nothing is ever pushed",
"description": "Payments succeed and the application never hears about them. The CLI listener was doing the delivery all along and no live endpoint was ever created.",
"h1": "live mode has no webhook endpoint, so nothing is ever pushed",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe webhook not configured", "no webhook endpoint live mode",
             "stripe listen production", "stripe events not received",
             "stripe webhook never fires"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The first real payment arrives and the application does nothing with it. No order row, no fulfilment email, no account provisioned. The charge is right there in the Dashboard, marked succeeded. It all worked perfectly in development, every single time, because <code>stripe listen</code> was doing the delivering and nobody noticed that it was the only thing that ever had.",
"short_answer": """<p>Call <code>GET /v1/webhook_endpoints?limit=100</code> with a <strong>live</strong> restricted key and look at the length of <code>data</code>. Zero means Stripe has no registered destination for this mode and never pushed anything anywhere.</p>
<p>Then prove it matters: <code>GET /v1/events?limit=100&amp;types[]=payment_intent.succeeded</code> and friends. Zero endpoints plus real payment traffic is the confirmed diagnosis. Zero endpoints on an account with no traffic yet is the same bug caught before it costs anything.</p>""",
"problem": """<p>Every other webhook failure leaves a trace somewhere. A disabled endpoint has a status you can read. A failing one has attempts and response codes. This one has nothing at all, because there is no object to have a state: the events were generated, they were listed in <code>/v1/events</code> like always, and no destination existed for Stripe to push them to. There is nothing in your logs because nothing was ever sent to you, and nothing in Stripe's because there was no delivery to record.</p>
<p>What makes it survive review is that the integration genuinely works. The signature verification is correct, the handler is correct, the tests pass. All of it was exercised against <code>stripe listen</code>, which creates its own ephemeral destination and prints its own <code>whsec_</code>, and none of that configuration lives in your account. The step that was skipped is not code at all, so no code review would have caught it.</p>""",
"why": """<p><strong>The CLI listener is a destination, and it is invisible to the API.</strong> <code>stripe listen</code> forwards events to your machine for as long as it is running. It does not create a webhook endpoint object, so <code>GET /v1/webhook_endpoints</code> returned an empty list throughout development and nobody had any reason to look.</p>
<p><strong>The two modes are entirely separate configurations.</strong> Test-mode endpoints and live-mode endpoints are different objects with different secrets, and a key can only see its own mode. A team that did create a test endpoint, and checked it, has confirmed nothing whatsoever about live.</p>
<p><strong>Nothing degrades: it simply never starts.</strong> There is no first successful delivery to compare against, no date the graph changed. The absence looks identical on day one and day ninety, which is why this is usually found by a customer asking where their thing is rather than by an alert.</p>
<p><strong>The signing secret in your environment may be from the CLI.</strong> A <code>whsec_</code> copied out of <code>stripe listen</code> output during development is mode-scoped and temporary. Even after somebody creates the endpoint, the handler will reject every live event with a 400 until the secret from the endpoint object replaces it, which turns this failure into the disabled-endpoint one a few days later.</p>""",
"steps": [
 {"h": "List the endpoints with a live key, and read the count",
  "body": """<p><code>GET /v1/webhook_endpoints?limit=100</code>. An empty <code>data</code> array is the whole finding. Do this with a key whose prefix is <code>rk_live_</code> or <code>sk_live_</code>: a test key will happily report the test-mode endpoint somebody made months ago and tell you nothing about production.</p>"""},
 {"h": "Confirm the mode from the objects, not from memory",
  "body": """<p>Every Stripe object carries <code>livemode</code>. Read it off an event or an endpoint rather than trusting which key you think is in the environment. This is a two-line check that removes the most common way this diagnosis goes wrong.</p>"""},
 {"h": "Measure what has already been lost",
  "body": """<p><code>GET /v1/events</code> filtered to <code>payment_intent.succeeded</code>, <code>checkout.session.completed</code> and <code>invoice.paid</code> counts the business events that had nowhere to go. Events are retained for 30 days, so this count is both the size of the backlog and the size of the window you have to work through it.</p>"""},
 {"h": "Create the endpoint and take the secret from the response",
  "body": """<p><code>POST /v1/webhook_endpoints</code> with your production URL and an explicit <code>enabled_events[]</code> list. The <code>secret</code> is returned on creation; that value, not the one from the CLI, is what your handler must verify against.</p>"""},
 {"h": "Backfill from the source objects, not only from the events",
  "body": """<p>Anything older than 30 days is gone from <code>/v1/events</code> for good. Charges, invoices and subscriptions are not retention-limited, so reconcile the gap from <code>GET /v1/charges?created[gte]=</code> and <code>GET /v1/invoices?created[gte]=</code> instead.</p>"""},
],
"verify": """<p>Re-run the script with the live key. It should report at least one enabled endpoint in live mode.</p>
<pre><code class="language-bash">python3 stripe_live_webhook_endpoints.py
# covered   1 enabled endpoint(s) in this mode</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Webhook Endpoints and Events is enough, and is what you should give it. The classifier takes the endpoint list, the count of payment events seen, and whether this is live mode, because the same empty list is a non-event on a fresh test account and an outage on a live one.",
"py_file": "stripe_live_webhook_endpoints.py",
"py": '''"""Report whether this mode has a webhook endpoint at all, and whether it needs one.

Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints and Events. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_live_webhook_endpoints")

API = "https://api.stripe.com/v1"

# Events that prove this mode is carrying real business traffic. If any of these
# fired and no endpoint exists, work that should follow a payment never happened.
TRAFFIC_TYPES = ("payment_intent.succeeded", "checkout.session.completed",
                 "invoice.paid")


def verdict(endpoints, payment_events, livemode):
    """Classify webhook coverage for one mode. Pure, so the rules can be tested.

    `endpoints` is the raw data array from /v1/webhook_endpoints, `payment_events`
    the count of business events seen in the retained window, and `livemode`
    whether this key reads live data. Returns (state, detail).
    """
    eps = list(endpoints or [])
    enabled = [e for e in eps if e.get("status") == "enabled"]
    if not eps:
        if payment_events:
            return ("blind",
                    "%d payment event(s) in the retained window and no webhook "
                    "endpoint to receive them. Stripe had nowhere to push, so "
                    "nothing that should follow a payment ever ran."
                    % payment_events)
        return ("empty",
                "no webhook endpoint, and no payment events in the retained "
                "window either. Nothing has been lost yet: create the endpoint "
                "before the first real payment rather than after it.")
    if not enabled:
        return ("all-disabled",
                "%d endpoint(s) exist and every one of them is disabled, which "
                "delivers exactly as much as having none." % len(eps))
    if not livemode:
        return ("test-mode",
                "%d enabled endpoint(s), all test mode. A healthy test mode is "
                "what lets this ship: re-run with a live restricted key before "
                "concluding anything about production." % len(enabled))
    return ("covered", "%d enabled endpoint(s) in this mode" % len(enabled))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def is_livemode(key):
    """Mode from the key prefix. Confirmed against object livemode where possible."""
    return not key.startswith(("sk_test_", "rk_test_", "pk_test_"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=100,
                    help="how many recent payment events to count as evidence")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    events = get(s, "/events", limit=min(args.max_events, 100),
                 **{"types[]": list(TRAFFIC_TYPES)}).get("data", [])

    # Prefer the objects over the key prefix: a restricted key can be named
    # anything, but livemode on a returned object is the account's own answer.
    livemode = is_livemode(key)
    for obj in list(endpoints) + list(events):
        if "livemode" in obj:
            livemode = bool(obj["livemode"])
            break

    state, detail = verdict(endpoints, len(events), livemode)
    line = "%-12s %s" % (state, detail)
    if state == "covered":
        log.info(line)
        for ep in endpoints:
            log.info("  %s  %d subscribed type(s)",
                     ep.get("url", "?"), len(ep.get("enabled_events") or []))
        return 0

    log.warning(line)
    if state in ("blind", "empty"):
        log.warning("  repair: POST %s/webhook_endpoints", API)
        log.warning("    -d url=https://<your-domain>/stripe/webhook")
        log.warning("    -d enabled_events[]=payment_intent.succeeded")
        log.warning("    -d enabled_events[]=payment_intent.payment_failed")
        log.warning("  then copy the secret from the response into the server "
                    "environment: the whsec_ printed by the CLI is not it")
    if state == "blind":
        log.warning("  backfill: GET %s/charges?created[gte]=<unix> and "
                    "%s/invoices?created[gte]=<unix>, which are not retention "
                    "limited the way /v1/events is", API, API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-live-webhook-endpoints.mjs",
"js": '''/**
 * Report whether this mode has a webhook endpoint at all, and whether it needs one.
 *
 * Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
 * Webhook Endpoints and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const TRAFFIC_TYPES = ['payment_intent.succeeded', 'checkout.session.completed',
  'invoice.paid'];

/**
 * Classify webhook coverage for one mode. Pure, so the rules can be tested.
 */
export function verdict(endpoints, paymentEvents, livemode) {
  const eps = endpoints ?? [];
  const enabled = eps.filter((e) => e.status === 'enabled');
  if (eps.length === 0) {
    if (paymentEvents) {
      return ['blind',
        `${paymentEvents} payment event(s) in the retained window and no webhook ` +
        'endpoint to receive them. Stripe had nowhere to push, so nothing that ' +
        'should follow a payment ever ran.'];
    }
    return ['empty',
      'no webhook endpoint, and no payment events in the retained window either. ' +
      'Nothing has been lost yet: create the endpoint before the first real ' +
      'payment rather than after it.'];
  }
  if (enabled.length === 0) {
    return ['all-disabled',
      `${eps.length} endpoint(s) exist and every one of them is disabled, which ` +
      'delivers exactly as much as having none.'];
  }
  if (!livemode) {
    return ['test-mode',
      `${enabled.length} enabled endpoint(s), all test mode. A healthy test mode ` +
      'is what lets this ship: re-run with a live restricted key before ' +
      'concluding anything about production.'];
  }
  return ['covered', `${enabled.length} enabled endpoint(s) in this mode`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, item);
    else url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export function isLivemode(key) {
  return !/^(sk|rk|pk)_test_/.test(key);
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  const { data: events = [] } = await get(key, '/events',
    { limit: 100, 'types[]': TRAFFIC_TYPES });

  let livemode = isLivemode(key);
  for (const obj of [...endpoints, ...events]) {
    if ('livemode' in obj) { livemode = Boolean(obj.livemode); break; }
  }

  const [state, detail] = verdict(endpoints, events.length, livemode);
  const line = `${state.padEnd(12)} ${detail}`;
  if (state === 'covered') {
    console.log(line);
    for (const ep of endpoints) {
      console.log(`  ${ep.url ?? '?'}  ${(ep.enabled_events ?? []).length} subscribed type(s)`);
    }
    return;
  }

  console.warn(line);
  if (state === 'blind' || state === 'empty') {
    console.warn(`  repair: POST ${API}/webhook_endpoints`);
    console.warn('    -d url=https://<your-domain>/stripe/webhook');
    console.warn('    -d enabled_events[]=payment_intent.succeeded');
    console.warn('    -d enabled_events[]=payment_intent.payment_failed');
    console.warn('  then copy the secret from the response into the server ' +
                 'environment: the whsec_ printed by the CLI is not it');
  }
  if (state === 'blind') {
    console.warn(`  backfill: GET ${API}/charges?created[gte]=<unix> and ` +
                 `${API}/invoices?created[gte]=<unix>, which are not retention ` +
                 'limited the way /v1/events is');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. An empty endpoint list on an account with payments is not the same finding as an empty list on an account with none, and a green result from a test key is not a result at all &mdash; it is the exact reassurance that let this reach production in the first place.",
"test_py_file": "test_stripe_live_webhook_endpoints.py",
"test_py": '''from stripe_live_webhook_endpoints import verdict, is_livemode


def test_no_endpoints_with_payments_is_the_outage():
    state, detail = verdict([], 47, True)
    assert state == "blind"
    assert "47" in detail


def test_no_endpoints_and_no_traffic_is_a_gap_not_an_outage():
    state, detail = verdict([], 0, True)
    assert state == "empty"
    assert "before the first real payment" in detail


def test_endpoints_that_are_all_disabled_deliver_nothing():
    state, _ = verdict([{"status": "disabled"}, {"status": "disabled"}], 12, True)
    assert state == "all-disabled"


def test_a_healthy_test_mode_is_not_a_pass():
    state, detail = verdict([{"status": "enabled"}], 12, False)
    assert state == "test-mode"
    assert "live restricted key" in detail


def test_an_enabled_live_endpoint_is_covered():
    state, _ = verdict([{"status": "enabled"}], 12, True)
    assert state == "covered"


def test_missing_status_does_not_count_as_enabled():
    state, _ = verdict([{}], 0, True)
    assert state == "all-disabled"


def test_key_prefix_decides_the_mode():
    assert is_livemode("rk_live_abc") is True
    assert is_livemode("rk_test_abc") is False
''',
"test_js_file": "stripe-live-webhook-endpoints.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, isLivemode } from './stripe-live-webhook-endpoints.mjs';

test('no endpoints with payments is the outage', () => {
  const [state, detail] = verdict([], 47, true);
  assert.equal(state, 'blind');
  assert.match(detail, /47/);
});

test('no endpoints and no traffic is a gap not an outage', () => {
  const [state, detail] = verdict([], 0, true);
  assert.equal(state, 'empty');
  assert.match(detail, /before the first real payment/);
});

test('endpoints that are all disabled deliver nothing', () => {
  const eps = [{ status: 'disabled' }, { status: 'disabled' }];
  assert.equal(verdict(eps, 12, true)[0], 'all-disabled');
});

test('a healthy test mode is not a pass', () => {
  const [state, detail] = verdict([{ status: 'enabled' }], 12, false);
  assert.equal(state, 'test-mode');
  assert.match(detail, /live restricted key/);
});

test('an enabled live endpoint is covered', () => {
  assert.equal(verdict([{ status: 'enabled' }], 12, true)[0], 'covered');
});

test('missing status does not count as enabled', () => {
  assert.equal(verdict([{}], 0, true)[0], 'all-disabled');
});

test('key prefix decides the mode', () => {
  assert.equal(isLivemode('rk_live_abc'), true);
  assert.equal(isLivemode('rk_test_abc'), false);
});
''',
"faq": [
 ("Does stripe listen count as a webhook endpoint?",
  "No. The CLI opens a temporary destination for as long as the process runs and prints its own signing secret. It creates no webhook endpoint object, so nothing about it survives the terminal session and nothing about it appears in GET /v1/webhook_endpoints."),
 ("I created an endpoint in the Dashboard and events still do not arrive.",
  "Check which mode you were in when you created it. Test-mode and live-mode endpoints are separate objects and the Dashboard toggle is easy to miss. Listing endpoints with a live key is the unambiguous answer."),
 ("Can I recover the payments that came in before the endpoint existed?",
  "Partly. Events are retained for 30 days, so anything inside that window can be replayed through your handler. Beyond it, reconcile from the objects instead: charges, invoices and subscriptions have no retention limit."),
 ("Which events should the new endpoint subscribe to?",
  "The ones your handler has a branch for, listed explicitly. payment_intent.succeeded and payment_intent.payment_failed are the usual minimum, plus checkout.session.completed if you use Checkout. Do not open with a wildcard to be safe: it is a different problem, not a safer default."),
 ("Why does the signing secret matter here?",
  "Because the whsec_ in your environment is probably the CLI's. Once the real endpoint exists it signs with its own secret, and a handler still verifying against the old one rejects every event with a 400, which after three days of retries gets the new endpoint disabled."),
],
"related": [
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
 ("/stripe/events-with-pending-webhooks/", "Events still show pending_webhooks hours after they fired"),
 ("/stripe/dead-or-rejected-enabled-events/", "enabled_events lists types that are dead or rejected"),
],
"citations": [CITE_WEBHOOKS, CITE_WEBHOOK_CREATE, CITE_CLI, CITE_KEYS],
},

{
"slug": "events-with-pending-webhooks",
"title": "Events still show pending_webhooks hours after they fired",
"description": "The endpoint is enabled and the Dashboard is green, but a subset of payments never got processed. Failures look random rather than total.",
"h1": "events still show pending_webhooks hours after they fired",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe pending_webhooks", "stripe webhook not delivered",
             "stripe webhook timeout retry", "delivery_success false",
             "stripe events stuck pending"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Most payments are processed and some are not. There is no pattern anyone can see: the same customer, the same product, the same code path, and one order exists while the next does not. The endpoint is enabled, the Dashboard shows no banner, and your logs show the handler running successfully for every request it received.",
"short_answer": """<p><code>pending_webhooks</code> on the event object is the number of destinations that have not yet returned a 2xx for it. Page <code>GET /v1/events?created[lt]=&lt;now-3600&gt;</code> and flag every event where that count is above zero. An hour after creation, first delivery and the early retries are long finished, so a nonzero value is a delivery that failed rather than one still in flight.</p>
<p>Then group the stuck events by <code>type</code>. That tally is the finding: one type dominating means a single handler branch is failing, while an even spread means the endpoint as a whole is timing out.</p>""",
"problem": """<p>This is the partial failure between the two states people know how to look for. The endpoint has not been disabled, so nothing draws attention to it. It has not stopped delivering either, so the graph of received webhooks looks approximately normal. Some fraction of events is failing, being retried, failing again, and eventually being dropped, and the fraction is small enough that it reads as flakiness rather than as a bug.</p>
<p>The confusing part is that your own logs support the wrong conclusion. Every request you received you handled correctly, so the handler looks innocent. The requests that failed are not in your logs at all &mdash; they timed out before the response, or the load balancer answered before your code did, or your framework issued a redirect. Stripe records those as failures and you record them as nothing.</p>""",
"why": """<p><strong>The handler does its work before it answers.</strong> A route that writes to the database, calls a fulfilment API and sends an email before returning 200 is fine at four events an hour and fails at four hundred. Stripe's timeout does not care that the work eventually succeeded; a slow 200 is a failed delivery, and the retry runs the same expensive work again.</p>
<p><strong>Redirects count as failures.</strong> A 301 from an <code>https</code> canonicalisation rule, a trailing-slash redirect, or an auth middleware that bounces unauthenticated requests to a login page all return 3xx. Stripe treats a redirect on a webhook request as a failed delivery and does not follow it, so the endpoint looks reachable in a browser and unreachable to Stripe.</p>
<p><strong>One bad branch fails only its own events.</strong> If <code>invoice.payment_failed</code> throws on a null customer, only that type accumulates. Everything else delivers perfectly, which is exactly why the failure looks random from the outside: it is not random at all, it is one type, and nobody has grouped it.</p>
<p><strong>Retries hide the start and the scale.</strong> Stripe retries with exponential backoff for up to three days, so an event created this morning may still be pending this evening and succeed tomorrow. The count you get is a snapshot of a moving backlog, which is why the age filter matters more than the raw number.</p>""",
"steps": [
 {"h": "Page the events with an age filter, not the whole window",
  "body": """<p><code>GET /v1/events?limit=100&amp;created[lt]=&lt;now minus one hour&gt;</code>. Excluding the last hour at the API rather than in your own loop is what keeps the count meaningful: an event created two minutes ago with <code>pending_webhooks</code> of 1 is a delivery in progress, not a problem.</p>"""},
 {"h": "Count the stuck ones and their share of the sample",
  "body": """<p>The absolute count tells you how much replaying there is to do. The share of the sample tells you what kind of failure it is, which is the more useful of the two.</p>"""},
 {"h": "Group by event type before touching any code",
  "body": """<p>If four fifths of the stuck events are one type, you have found the branch. If they are spread across everything the endpoint receives, the handler is not the problem: the response time is, or the route is answering with a redirect.</p>"""},
 {"h": "Answer first, work second",
  "body": """<p>Return 200 as soon as the signature verifies, then process from a queue. This is the only structural fix; every other change just moves the timeout around. It also makes the retry harmless, because a duplicate delivery enqueues a job your processed-event table will drop.</p>"""},
 {"h": "Replay what was lost, oldest first",
  "body": """<p><code>GET /v1/events?delivery_success=false</code> paginated, pushed through your own handler in chronological order and guarded by your processed-event table. Do the oldest first: those are the ones closest to leaving the 30 day retention window.</p>"""},
],
"verify": """<p>Re-run the script. Nothing older than an hour should still have deliveries outstanding.</p>
<pre><code class="language-bash">python3 stripe_pending_webhooks.py
# clear      412 event(s) older than the grace period, all delivered</code></pre>""",
"code_intro": "One paginated GET and no writes &mdash; a restricted key with read access to Events is enough. The classification is a pure function of four numbers: how many events were old enough to judge, how many of those are still outstanding, and which single type accounts for the most of them. That last pair is what separates a broken branch from a slow endpoint, and it should be a visible rule rather than a judgement call made while reading output.",
"py_file": "stripe_pending_webhooks.py",
"py": '''"""Report Stripe events whose deliveries are still outstanding hours after they fired.

Read only. One paginated GET, no writes: give this a RESTRICTED key with read
access to Events. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_pending_webhooks")

API = "https://api.stripe.com/v1"

# An event younger than this is a delivery in progress, not a failure.
GRACE_SECONDS = 3600

# A single type holding this share of the stuck events is a handler branch.
CONCENTRATED = 0.8

# Stuck events at this share of the whole sample is an endpoint level failure.
WIDESPREAD = 0.5


def verdict(sampled, stuck, top_type, top_count):
    """Classify a window of events. Pure, so the rules can be tested offline.

    `sampled` is how many events were old enough to judge, `stuck` how many of
    those still have pending_webhooks above zero, and `top_type`/`top_count` the
    most common type among the stuck ones. Returns (state, detail).
    """
    if sampled <= 0:
        return ("empty",
                "no events older than the grace period in the retained window: "
                "nothing here can be judged yet")
    if stuck <= 0:
        return ("clear",
                "%d event(s) older than the grace period, all delivered" % sampled)
    share = top_count / float(stuck)
    if share >= CONCENTRATED:
        return ("one-branch",
                "%d of %d stuck event(s) are %s. That is one handler branch "
                "failing, not the endpoint." % (top_count, stuck, top_type))
    if stuck / float(sampled) >= WIDESPREAD:
        return ("endpoint-wide",
                "%d of %d sampled event(s) never got a 2xx, across %s and other "
                "types. The route is timing out or answering with a redirect."
                % (stuck, sampled, top_type))
    return ("intermittent",
            "%d of %d sampled event(s) stuck, spread across types. This is the "
            "handler running out of time under load rather than one bad branch."
            % (stuck, sampled))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def scan(session, cutoff, limit):
    """Count events older than `cutoff` and tally the stuck ones by type."""
    sampled = 0
    stuck = 0
    by_type = {}
    params = {"limit": 100, "created[lt]": cutoff}
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        for ev in data:
            sampled += 1
            if (ev.get("pending_webhooks") or 0) > 0:
                stuck += 1
                t = ev.get("type", "unknown")
                by_type[t] = by_type.get(t, 0) + 1
        if not data or not page.get("has_more") or sampled >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return sampled, stuck, by_type


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=1000,
                    help="stop after sampling this many events")
    ap.add_argument("--grace", type=int, default=GRACE_SECONDS,
                    help="ignore events younger than this many seconds")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    cutoff = int(time.time()) - args.grace
    sampled, stuck, by_type = scan(s, cutoff, args.max_events)

    # Sorted by count then name so a tie reports the same type on every run.
    ranked = sorted(by_type.items(), key=lambda kv: (-kv[1], kv[0]))
    top_type, top_count = ranked[0] if ranked else ("none", 0)

    state, detail = verdict(sampled, stuck, top_type, top_count)
    if state in ("empty", "clear"):
        log.info("%-13s %s", state, detail)
        return 0

    log.warning("%-13s %s", state, detail)
    for t, n in ranked[:8]:
        log.warning("  %5d  %s", n, t)
    log.warning("  repair: return 200 as soon as the signature verifies and move "
                "the work to a queue. A slow 200 is a failed delivery.")
    log.warning("  then replay: GET %s/events?delivery_success=false paginated "
                "oldest first, guarded by your processed event table", API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-pending-webhooks.mjs",
"js": '''/**
 * Report Stripe events whose deliveries are still outstanding hours after they fired.
 *
 * Read only. One paginated GET, no writes: give this a RESTRICTED key with read
 * access to Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const GRACE_SECONDS = 3600;
const CONCENTRATED = 0.8;
const WIDESPREAD = 0.5;

/**
 * Classify a window of events. Pure, so the rules can be tested offline.
 */
export function verdict(sampled, stuck, topType, topCount) {
  if (sampled <= 0) {
    return ['empty',
      'no events older than the grace period in the retained window: nothing ' +
      'here can be judged yet'];
  }
  if (stuck <= 0) {
    return ['clear', `${sampled} event(s) older than the grace period, all delivered`];
  }
  const share = topCount / stuck;
  if (share >= CONCENTRATED) {
    return ['one-branch',
      `${topCount} of ${stuck} stuck event(s) are ${topType}. That is one ` +
      'handler branch failing, not the endpoint.'];
  }
  if (stuck / sampled >= WIDESPREAD) {
    return ['endpoint-wide',
      `${stuck} of ${sampled} sampled event(s) never got a 2xx, across ` +
      `${topType} and other types. The route is timing out or answering with a ` +
      'redirect.'];
  }
  return ['intermittent',
    `${stuck} of ${sampled} sampled event(s) stuck, spread across types. This is ` +
    'the handler running out of time under load rather than one bad branch.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function scan(key, cutoff, limit = 1000) {
  let sampled = 0;
  let stuck = 0;
  const byType = new Map();
  const params = { limit: 100, 'created[lt]': cutoff };
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    for (const ev of data) {
      sampled += 1;
      if ((ev.pending_webhooks ?? 0) > 0) {
        stuck += 1;
        const t = ev.type ?? 'unknown';
        byType.set(t, (byType.get(t) ?? 0) + 1);
      }
    }
    if (data.length === 0 || !page.has_more || sampled >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { sampled, stuck, byType };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const cutoff = Math.floor(Date.now() / 1000) - GRACE_SECONDS;
  const { sampled, stuck, byType } = await scan(key, cutoff);

  // Sorted by count then name so a tie reports the same type on every run.
  const ranked = [...byType.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const [topType, topCount] = ranked[0] ?? ['none', 0];

  const [state, detail] = verdict(sampled, stuck, topType, topCount);
  if (state === 'empty' || state === 'clear') {
    console.log(`${state.padEnd(13)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(13)} ${detail}`);
  for (const [t, n] of ranked.slice(0, 8)) {
    console.warn(`  ${String(n).padStart(5)}  ${t}`);
  }
  console.warn('  repair: return 200 as soon as the signature verifies and move ' +
               'the work to a queue. A slow 200 is a failed delivery.');
  console.warn(`  then replay: GET ${API}/events?delivery_success=false paginated ` +
               'oldest first, guarded by your processed event table');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The shape of the failure is the finding, so the tests pin the two thresholds that decide it. Eighty percent of the stuck events being one type is a branch; below that it is the endpoint, and which side of the line a given tally falls on has to be a rule rather than an impression. The empty sample is worth a test of its own, because dividing by a stuck count of zero is exactly how a check like this ends up crashing on the healthy accounts.",
"test_py_file": "test_stripe_pending_webhooks.py",
"test_py": '''from stripe_pending_webhooks import verdict


def test_an_empty_sample_reports_nothing_rather_than_dividing_by_zero():
    state, _ = verdict(0, 0, "none", 0)
    assert state == "empty"


def test_everything_delivered_is_clear():
    state, detail = verdict(412, 0, "none", 0)
    assert state == "clear"
    assert "412" in detail


def test_one_type_dominating_names_the_branch():
    state, detail = verdict(500, 40, "invoice.payment_failed", 36)
    assert state == "one-branch"
    assert "invoice.payment_failed" in detail


def test_the_concentration_threshold_is_inclusive():
    # 80 of 100 is a branch; 79 of 100 is not.
    assert verdict(1000, 100, "charge.refunded", 80)[0] == "one-branch"
    assert verdict(1000, 100, "charge.refunded", 79)[0] != "one-branch"


def test_a_majority_stuck_across_types_is_the_endpoint():
    state, detail = verdict(100, 60, "payment_intent.succeeded", 20)
    assert state == "endpoint-wide"
    assert "redirect" in detail


def test_a_thin_spread_is_load_not_a_bad_branch():
    state, detail = verdict(1000, 40, "payment_intent.succeeded", 12)
    assert state == "intermittent"
    assert "under load" in detail
''',
"test_js_file": "stripe-pending-webhooks.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-pending-webhooks.mjs';

test('an empty sample reports nothing rather than dividing by zero', () => {
  assert.equal(verdict(0, 0, 'none', 0)[0], 'empty');
});

test('everything delivered is clear', () => {
  const [state, detail] = verdict(412, 0, 'none', 0);
  assert.equal(state, 'clear');
  assert.match(detail, /412/);
});

test('one type dominating names the branch', () => {
  const [state, detail] = verdict(500, 40, 'invoice.payment_failed', 36);
  assert.equal(state, 'one-branch');
  assert.match(detail, /invoice\\.payment_failed/);
});

test('the concentration threshold is inclusive', () => {
  assert.equal(verdict(1000, 100, 'charge.refunded', 80)[0], 'one-branch');
  assert.notEqual(verdict(1000, 100, 'charge.refunded', 79)[0], 'one-branch');
});

test('a majority stuck across types is the endpoint', () => {
  const [state, detail] = verdict(100, 60, 'payment_intent.succeeded', 20);
  assert.equal(state, 'endpoint-wide');
  assert.match(detail, /redirect/);
});

test('a thin spread is load not a bad branch', () => {
  const [state, detail] = verdict(1000, 40, 'payment_intent.succeeded', 12);
  assert.equal(state, 'intermittent');
  assert.match(detail, /under load/);
});
''',
"faq": [
 ("What exactly does pending_webhooks count?",
  "The number of destinations that have not yet returned a 2xx for that event. It starts at the number of endpoints subscribed to the type and drops as each one acknowledges, so a value above zero long after the event was created means at least one destination is still failing."),
 ("Why ignore events from the last hour?",
  "Because first delivery and the first retries happen inside it. An event created minutes ago with a pending delivery is normal traffic; counting it produces a number that looks alarming on a completely healthy account."),
 ("Is a 3xx really a failure?",
  "Yes. Stripe does not follow redirects on webhook requests, so an https canonicalisation rule, a trailing-slash rule, or an auth middleware bouncing to a login page all read as failed deliveries. The URL will look perfectly fine in a browser."),
 ("The endpoint is enabled, so how bad is this?",
  "It is the window before it is not. Sustained failures end with Stripe disabling the endpoint after about three days of retries, and once disabled it stops retrying the queued events. Fixing it now costs a replay; fixing it later costs a replay plus a re-enable plus whatever left the retention window."),
 ("Can I tell which endpoint is failing when there are several?",
  "Yes, from the event object: it reports the destinations that have not acknowledged it, so you can attribute the stuck count per endpoint rather than guessing. With a single endpoint the type tally is the more useful cut."),
],
"related": [
 ("/stripe/undelivered-events-nearing-retention/", "Undelivered events aging out of the 30 day window"),
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
 ("/stripe/duplicate-endpoints-same-url/", "Two endpoints on one URL handle every event twice"),
],
"citations": [CITE_EVENT_OBJ, CITE_EVENTS_LIST, CITE_UNDELIVERED, CITE_WEBHOOKS],
},

{
"slug": "missing-subscription-deleted",
"title": "customer.subscription.deleted is missing, so access never ends",
"description": "Cancelled and dunning-exhausted customers keep full product access. Revenue looks fine and entitlements are wrong, usually found by an honest user.",
"h1": "customer.subscription.deleted is missing, so access never ends",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["customer.subscription.deleted", "stripe cancel_at_period_end webhook",
             "stripe access not revoked", "stripe subscription canceled event",
             "stripe entitlement webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A support ticket arrives from somebody trying to be helpful: they cancelled two months ago and can still log in and use everything. You check Stripe and they really did cancel, on time, and the subscription really is <code>canceled</code>. The revenue reporting is correct. It is only the entitlement in your own database that has never been told.",
"short_answer": """<p>Union the <code>enabled_events</code> arrays from <code>GET /v1/webhook_endpoints</code> and check for <code>customer.subscription.deleted</code>. It is the only event that fires when a subscription actually ends, including the delayed end of a <code>cancel_at_period_end</code> cancellation and the point where Smart Retries give up.</p>
<p>Then size the damage with <code>GET /v1/subscriptions?status=canceled</code>. Every one of those is a customer whose access your application was never asked to revoke.</p>""",
"problem": """<p>Subscription handlers are written from the top down: created, then paid, then maybe updated. Each of those is a moment where something visible happens and somebody is watching. The ending is different. It happens on a date nobody chose, often weeks after the customer clicked cancel, and frequently with no human involved at all &mdash; a card expired, the retries ran out, and Stripe closed the subscription on a schedule.</p>
<p>Because the money side is entirely correct, none of your reporting disagrees with reality. MRR drops on cancellation, the invoices stop, the dashboards are accurate. The only wrong number is the one nobody looks at, which is how many accounts have an active flag they should not. It surfaces as an honest user writing in, or as an audit, or not at all.</p>""",
"why": """<p><strong>Cancellation and ending are different moments.</strong> <code>cancel_at_period_end</code> sets a flag now and ends the subscription in three weeks. The update that sets the flag is <code>customer.subscription.updated</code>; the actual end, three weeks later, is <code>customer.subscription.deleted</code>. A handler wired only to the update either revokes access far too early or, more commonly, records the intent and never gets told when it takes effect.</p>
<p><strong>Dunning ends the same way, with nobody present.</strong> When retries are exhausted the subscription can be set to cancel automatically. There is no click, no session, no request from the customer. If the deleted event is not subscribed, the only trace is a status change on an object nobody is polling.</p>
<p><strong>The event is not implied by the ones you have.</strong> <code>enabled_events</code> is an allowlist. Subscribing to <code>customer.subscription.created</code> and <code>invoice.paid</code> gives you exactly those two. Nothing about a subscription family subscription includes its terminal event.</p>
<p><strong>Nothing complains, because the error is a permission that is too generous.</strong> Bugs that deny access get reported within minutes. Bugs that grant it are reported by whoever happens to have a conscience, and the rest is quiet revenue leakage that looks like nothing at all.</p>""",
"steps": [
 {"h": "Establish that this account actually uses subscriptions",
  "body": """<p><code>GET /v1/subscriptions?limit=100</code> for active and for canceled. On an account that has never had a subscription, a missing subscription event is not a finding, and reporting it is how a check trains people to ignore it.</p>"""},
 {"h": "Union enabled_events across every endpoint",
  "body": """<p>Coverage belongs to the account, not to one endpoint. Billing events commonly live on a different destination from payment ones. A literal <code>"*"</code> covers this type, and brings its own problems.</p>"""},
 {"h": "Check for the companion event as well",
  "body": """<p><code>customer.subscription.updated</code> is what tells you a cancellation has been <em>scheduled</em>, along with plan changes and trials converting. Deleted without updated means you learn about every ending on the day it happens and nothing before it, which is enough for correctness and not enough for a retention email.</p>"""},
 {"h": "Count the customers who are already over-entitled",
  "body": """<p>Every subscription in <code>canceled</code> is a candidate. Reconcile that list against your own entitlement table; the rows that disagree are the ones to fix, and the count is what makes the case for doing it this week.</p>"""},
 {"h": "Subscribe, then reconcile rather than waiting",
  "body": """<p><code>POST /v1/webhook_endpoints/{id}</code> adding <code>customer.subscription.deleted</code> and <code>customer.subscription.updated</code>. Subscribing fixes the future only: the existing over-entitled accounts have to be swept from the canceled list, because their events are long gone.</p>"""},
],
"verify": """<p>Re-run the script. The union should contain the terminal event and the state should be covered.</p>
<pre><code class="language-bash">python3 stripe_subscription_deleted_events.py
# covered   customer.subscription.deleted is subscribed on at least one endpoint</code></pre>""",
"code_intro": "Three GETs and no writes &mdash; endpoints, active subscriptions and canceled ones. A restricted key with read access to Webhook Endpoints and Subscriptions covers it. The classifier takes the subscription union plus both counts, because the same missing event type is noise on an account with no subscriptions, a gap on one with no cancellations yet, and a list of specific over-entitled customers on one that has them.",
"py_file": "stripe_subscription_deleted_events.py",
"py": '''"""Report whether customer.subscription.deleted is subscribed, and who is over-entitled.

Read only. Three GETs, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints and Subscriptions. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_subscription_deleted_events")

API = "https://api.stripe.com/v1"

TARGET = "customer.subscription.deleted"
COMPANION = "customer.subscription.updated"


def verdict(subscribed, canceled, active):
    """Classify entitlement-revocation coverage. Pure, so the rules can be tested.

    `subscribed` is the union of enabled_events across every endpoint, `canceled`
    the number of subscriptions already ended, `active` the number still running.
    Returns (state, detail).
    """
    events = set(subscribed or [])
    if not canceled and not active:
        return ("not-billing",
                "no subscriptions on this account at all, so %s is not a gap "
                "worth reporting yet" % TARGET)
    if "*" in events:
        return ("wildcard",
                "a wildcard subscription covers %s, but it also delivers every "
                "other event type to the same handler." % TARGET)
    if TARGET in events:
        if COMPANION not in events:
            return ("partial",
                    "%s is subscribed but %s is not. You learn that a "
                    "subscription ended, never that a cancellation was scheduled."
                    % (TARGET, COMPANION))
        return ("covered", "%s is subscribed on at least one endpoint" % TARGET)
    if canceled:
        return ("over-entitled",
                "%d canceled subscription(s) and nothing subscribes to %s. Each "
                "one is an account your application was never asked to revoke."
                % (canceled, TARGET))
    return ("unsubscribed",
            "%d active subscription(s) and nothing subscribes to %s. Nothing has "
            "ended yet, so this is a gap rather than a backlog."
            % (active, TARGET))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def subscribed_events(endpoints):
    """Union of enabled_events across endpoints. Pure, given the endpoint list."""
    union = set()
    for ep in endpoints:
        union.update(ep.get("enabled_events") or [])
    return union


def count_subscriptions(session, status, limit):
    """Count subscriptions in one status, keeping the first few ids for the report."""
    count = 0
    ids = []
    params = {"limit": 100, "status": status}
    while True:
        page = get(session, "/subscriptions", **params)
        data = page.get("data", [])
        for sub in data:
            count += 1
            if len(ids) < 10:
                ids.append(sub["id"])
        if not data or not page.get("has_more") or count >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return count, ids


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=1000,
                    help="stop counting each status after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    union = subscribed_events(endpoints)
    canceled, canceled_ids = count_subscriptions(s, "canceled", args.max_subscriptions)
    active, _ = count_subscriptions(s, "active", args.max_subscriptions)

    state, detail = verdict(union, canceled, active)
    line = "%-14s %s" % (state, detail)
    if state in ("covered", "not-billing"):
        log.info(line)
        return 0

    log.warning(line)
    if state == "over-entitled":
        for sid in canceled_ids:
            log.warning("  reconcile: %s", sid)
    if state != "wildcard":
        log.warning("  repair: POST %s/webhook_endpoints/%s", API,
                    endpoints[0]["id"] if endpoints else "<we_id>")
        log.warning("    -d enabled_events[]=%s", TARGET)
        log.warning("    -d enabled_events[]=%s", COMPANION)
        log.warning("    (enabled_events is replaced wholesale: send the existing "
                    "types too)")
    log.warning("  then sweep GET %s/subscriptions?status=canceled against your "
                "own entitlement table: subscribing fixes the future only", API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-subscription-deleted-events.mjs",
"js": '''/**
 * Report whether customer.subscription.deleted is subscribed, and who is over-entitled.
 *
 * Read only. Three GETs, no writes: give this a RESTRICTED key with read access
 * to Webhook Endpoints and Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const TARGET = 'customer.subscription.deleted';
const COMPANION = 'customer.subscription.updated';

/**
 * Classify entitlement-revocation coverage. Pure, so the rules can be tested.
 */
export function verdict(subscribed, canceled, active) {
  const events = new Set(subscribed ?? []);
  if (!canceled && !active) {
    return ['not-billing',
      `no subscriptions on this account at all, so ${TARGET} is not a gap worth ` +
      'reporting yet'];
  }
  if (events.has('*')) {
    return ['wildcard',
      `a wildcard subscription covers ${TARGET}, but it also delivers every ` +
      'other event type to the same handler.'];
  }
  if (events.has(TARGET)) {
    if (!events.has(COMPANION)) {
      return ['partial',
        `${TARGET} is subscribed but ${COMPANION} is not. You learn that a ` +
        'subscription ended, never that a cancellation was scheduled.'];
    }
    return ['covered', `${TARGET} is subscribed on at least one endpoint`];
  }
  if (canceled) {
    return ['over-entitled',
      `${canceled} canceled subscription(s) and nothing subscribes to ${TARGET}. ` +
      'Each one is an account your application was never asked to revoke.'];
  }
  return ['unsubscribed',
    `${active} active subscription(s) and nothing subscribes to ${TARGET}. ` +
    'Nothing has ended yet, so this is a gap rather than a backlog.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

/** Union of enabled_events across endpoints. Pure, given the endpoint list. */
export function subscribedEvents(endpoints) {
  const union = new Set();
  for (const ep of endpoints ?? []) {
    for (const t of ep.enabled_events ?? []) union.add(t);
  }
  return union;
}

async function countSubscriptions(key, status, limit = 1000) {
  let count = 0;
  const ids = [];
  const params = { limit: 100, status };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const data = page.data ?? [];
    for (const sub of data) {
      count += 1;
      if (ids.length < 10) ids.push(sub.id);
    }
    if (data.length === 0 || !page.has_more || count >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { count, ids };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  const union = subscribedEvents(endpoints);
  const canceled = await countSubscriptions(key, 'canceled');
  const active = await countSubscriptions(key, 'active');

  const [state, detail] = verdict(union, canceled.count, active.count);
  const line = `${state.padEnd(14)} ${detail}`;
  if (state === 'covered' || state === 'not-billing') {
    console.log(line);
    return;
  }

  console.warn(line);
  if (state === 'over-entitled') {
    for (const sid of canceled.ids) console.warn(`  reconcile: ${sid}`);
  }
  if (state !== 'wildcard') {
    console.warn(`  repair: POST ${API}/webhook_endpoints/${endpoints[0]?.id ?? '<we_id>'}`);
    console.warn(`    -d enabled_events[]=${TARGET}`);
    console.warn(`    -d enabled_events[]=${COMPANION}`);
    console.warn('    (enabled_events is replaced wholesale: send the existing types too)');
  }
  console.warn(`  then sweep GET ${API}/subscriptions?status=canceled against your ` +
               'own entitlement table: subscribing fixes the future only');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The states worth pinning are the two that look alike from a distance. A missing subscription on an account that has never cancelled anybody is a gap you close this quarter; the same missing subscription with two hundred cancellations behind it is a list of people using a product they stopped paying for, and the report has to say so in those words. The account with no subscriptions at all has to stay silent, or nobody will read the output twice.",
"test_py_file": "test_stripe_subscription_deleted_events.py",
"test_py": '''from stripe_subscription_deleted_events import verdict, subscribed_events


def test_an_account_without_subscriptions_is_not_a_finding():
    state, _ = verdict([], 0, 0)
    assert state == "not-billing"


def test_missing_with_cancellations_behind_it_is_a_backlog():
    state, detail = verdict(["invoice.paid"], 214, 900)
    assert state == "over-entitled"
    assert "214" in detail


def test_missing_with_nothing_ended_yet_is_only_a_gap():
    state, detail = verdict(["invoice.paid"], 0, 40)
    assert state == "unsubscribed"
    assert "gap rather than a backlog" in detail


def test_deleted_without_updated_is_partial():
    state, detail = verdict(["customer.subscription.deleted"], 5, 40)
    assert state == "partial"
    assert "customer.subscription.updated" in detail


def test_both_events_subscribed_is_covered():
    state, _ = verdict(["customer.subscription.deleted",
                        "customer.subscription.updated"], 5, 40)
    assert state == "covered"


def test_a_wildcard_covers_it_and_is_still_called_out():
    state, _ = verdict(["*"], 5, 40)
    assert state == "wildcard"


def test_the_union_flattens_every_endpoint():
    union = subscribed_events([{"enabled_events": ["invoice.paid"]},
                               {"enabled_events": ["customer.subscription.deleted"]},
                               {}])
    assert union == {"invoice.paid", "customer.subscription.deleted"}
''',
"test_js_file": "stripe-subscription-deleted-events.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, subscribedEvents } from './stripe-subscription-deleted-events.mjs';

test('an account without subscriptions is not a finding', () => {
  assert.equal(verdict([], 0, 0)[0], 'not-billing');
});

test('missing with cancellations behind it is a backlog', () => {
  const [state, detail] = verdict(['invoice.paid'], 214, 900);
  assert.equal(state, 'over-entitled');
  assert.match(detail, /214/);
});

test('missing with nothing ended yet is only a gap', () => {
  const [state, detail] = verdict(['invoice.paid'], 0, 40);
  assert.equal(state, 'unsubscribed');
  assert.match(detail, /gap rather than a backlog/);
});

test('deleted without updated is partial', () => {
  const [state, detail] = verdict(['customer.subscription.deleted'], 5, 40);
  assert.equal(state, 'partial');
  assert.match(detail, /customer\\.subscription\\.updated/);
});

test('both events subscribed is covered', () => {
  const subs = ['customer.subscription.deleted', 'customer.subscription.updated'];
  assert.equal(verdict(subs, 5, 40)[0], 'covered');
});

test('a wildcard covers it and is still called out', () => {
  assert.equal(verdict(['*'], 5, 40)[0], 'wildcard');
});

test('the union flattens every endpoint', () => {
  const union = subscribedEvents([{ enabled_events: ['invoice.paid'] },
    { enabled_events: ['customer.subscription.deleted'] }, {}]);
  assert.deepEqual([...union].sort(),
    ['customer.subscription.deleted', 'invoice.paid']);
});
''',
"faq": [
 ("Is customer.subscription.deleted not just the cancel button?",
  "No. It fires when the subscription actually ends, which for a cancel_at_period_end cancellation is weeks after the customer clicked anything, and for an exhausted dunning sequence involves no customer action at all. It is the only event that marks the end itself."),
 ("Can I revoke access on customer.subscription.updated instead?",
  "Not on its own. The update that sets cancel_at_period_end arrives while the customer is still fully paid up, so acting on it cuts off access they have bought. Use updated to know a cancellation is scheduled and deleted to act on it."),
 ("What about a subscription that ends because the card kept failing?",
  "Same event. When retries are exhausted the subscription can be cancelled automatically, and the ending is reported the same way. That case is the one most likely to be missing from an entitlement system, because nobody was present for it."),
 ("Does subscribing now fix the customers who are already over-entitled?",
  "No. Webhooks are not retroactive and the events for those cancellations are outside the 30 day retention window. Sweep GET /v1/subscriptions?status=canceled against your entitlement table once, then rely on the event going forward."),
 ("Why does the check care whether the account has subscriptions at all?",
  "Because a missing subscription event on an account that only takes one-off payments is not a defect, and a report that flags it is a report people learn to skip. The count of active and canceled subscriptions is what makes the finding true rather than merely technically correct."),
],
"related": [
 ("/stripe/missing-payout-failed/", "payout.failed is unsubscribed so failures go unseen"),
 ("/stripe/dunning-retries-exhausted/", "Dunning retries run out and the subscription ends"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions accumulate unnoticed"),
],
"citations": [CITE_WEBHOOK_CREATE, CITE_SUB_OBJ, CITE_SUB_CANCEL, CITE_EVENT_TYPES],
},

{
"slug": "missing-dispute-and-fraud-events",
"title": "Nothing subscribes to disputes or early fraud warnings",
"description": "Chargebacks are first noticed when the balance drops or Stripe emails a deadline. The evidence window is already half gone and nothing flagged the fraud.",
"h1": "nothing subscribes to disputes or early fraud warnings",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["charge.dispute.created webhook", "stripe early fraud warning",
             "radar.early_fraud_warning.created", "stripe chargeback alert",
             "stripe dispute notification"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The first anyone knows about a chargeback is an email from Stripe about a deadline, or an unexplained dip in the balance. By the time somebody opens the dashboard, several days of the evidence window are gone. Separately and more expensively, the order that caused it shipped a week ago, even though the issuer had already flagged the card.",
"short_answer": """<p>Union the <code>enabled_events</code> arrays from <code>GET /v1/webhook_endpoints</code> and check for two types. <code>charge.dispute.created</code> is the only push signal that a chargeback has been opened. <code>radar.early_fraud_warning.created</code> fires when the issuer flags a payment <em>before</em> it becomes a formal dispute.</p>
<p>Corroborate with <code>GET /v1/disputes?limit=1</code> and <code>GET /v1/radar/early_fraud_warnings?limit=1</code>. A missing subscription on an account that has already had either one is not a gap in coverage; it is a class of event you have been finding out about by email.</p>""",
"problem": """<p>Disputes are the one part of a payments integration where the clock is set by somebody else. The card network decides the response deadline, it is short, and it does not extend because your team was not told. Every day between the dispute being opened and somebody noticing is a day removed from the time available to assemble receipts, delivery confirmation and terms acceptance.</p>
<p>The early fraud warning is the part that is genuinely worth money and almost nobody has wired up. It arrives when the issuer has flagged a payment as fraudulent but no chargeback has been filed yet. In that window a refund usually prevents the dispute altogether, which avoids both the chargeback fee and the hit to your dispute rate. Without the event, the warning sits in the API and the order ships.</p>""",
"why": """<p><strong>Neither type is implied by the payment events you already have.</strong> Subscribing to <code>charge.succeeded</code> or <code>payment_intent.succeeded</code> tells Stripe nothing about disputes. <code>enabled_events</code> is an allowlist, and a dispute is a different family with a different prefix that has to be asked for by name.</p>
<p><strong>Email is not a delivery mechanism you can build on.</strong> Stripe does notify the account owner, and that notification goes to one inbox, is filtered, is missed on holidays, and cannot open a ticket or halt a shipment. The event can do all three.</p>
<p><strong>Disputes are rare enough to never have been designed for.</strong> An integration can run for a year without one. The handler branch is therefore written, if at all, on the day of the first chargeback, under time pressure, by somebody reading the evidence documentation for the first time.</p>
<p><strong>The fraud warning has a shorter useful life than the dispute.</strong> A dispute has a deadline measured in days; the window in which a proactive refund still prevents it closes as soon as the issuer files. That makes the early fraud warning the one signal here where hours matter, and it is the one people leave out.</p>""",
"steps": [
 {"h": "Union enabled_events across every endpoint, in both modes",
  "body": """<p>Coverage is a property of the account. It is common for a Radar or dispute endpoint to be separate from the payment one, and equally common for it to have been planned and never created. A literal <code>"*"</code> covers both types and brings its own problems.</p>"""},
 {"h": "Ask whether it has already happened",
  "body": """<p><code>GET /v1/disputes?limit=100</code> and <code>GET /v1/radar/early_fraud_warnings?limit=100</code>. These are two independent facts: an account can have warnings and no disputes, which is the best possible position to be in and the one where the missing subscription costs the most.</p>"""},
 {"h": "Subscribe to the opening and the closing",
  "body": """<p><code>charge.dispute.created</code> starts the clock; <code>charge.dispute.closed</code> tells you how it ended. Without the second, your own records of win rate come from the Dashboard by hand, and nothing reverses the internal state you set when the dispute opened.</p>"""},
 {"h": "Handle the fraud warning as an action, not a log line",
  "body": """<p>On a warning with no dispute and no full refund yet, a refund usually prevents the chargeback. That decision needs the order state, so the handler branch has to do more than write a row: it has to be able to stop a shipment or reverse a provisioning step.</p>"""},
 {"h": "Backfill from the objects, not the events",
  "body": """<p>Both resources list without a retention limit, unlike <code>/v1/events</code>. Once subscribed, sweep the existing disputes and warnings once to catch anything that arrived while nothing was listening.</p>"""},
],
"verify": """<p>Re-run the script. Both signals should be subscribed on at least one endpoint.</p>
<pre><code class="language-bash">python3 stripe_dispute_events.py
# covered   charge.dispute.created and radar.early_fraud_warning.created subscribed</code></pre>""",
"code_intro": "Three GETs and no writes &mdash; endpoints, disputes and early fraud warnings. A restricted key with read access to Webhook Endpoints, Disputes and Radar covers it. The classifier keeps the two signals separate rather than collapsing them into one coverage flag, because they fail at different times and only one of them still has a cheap remedy available when it arrives.",
"py_file": "stripe_dispute_events.py",
"py": '''"""Report whether dispute and early fraud warning events are subscribed anywhere.

Read only. Three GETs, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints, Disputes and Radar. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_dispute_events")

API = "https://api.stripe.com/v1"

DISPUTE = "charge.dispute.created"
DISPUTE_CLOSED = "charge.dispute.closed"
FRAUD = "radar.early_fraud_warning.created"


def verdict(subscribed, disputes, warnings):
    """Classify dispute and fraud coverage. Pure, so the rules can be tested.

    `subscribed` is the union of enabled_events across every endpoint, `disputes`
    and `warnings` the counts already on the account. The two signals stay
    separate because they fail at different times. Returns (state, detail).
    """
    events = set(subscribed or [])
    if "*" in events:
        return ("wildcard",
                "a wildcard subscription covers both signals, but it also "
                "delivers every other event type to the same handler.")
    if DISPUTE not in events:
        if disputes:
            return ("blind",
                    "%d dispute(s) on this account and nothing subscribes to %s. "
                    "Every response deadline so far was found by email."
                    % (disputes, DISPUTE))
        return ("unsubscribed",
                "nothing subscribes to %s. No disputes yet, so this is a gap "
                "rather than a deadline already running." % DISPUTE)
    if FRAUD not in events:
        if warnings:
            return ("fraud-blind",
                    "%d early fraud warning(s) already raised and nothing "
                    "subscribes to %s. A refund during that window prevents the "
                    "chargeback outright." % (warnings, FRAUD))
        return ("dispute-only",
                "%s is subscribed but %s is not. You will hear about chargebacks "
                "after they are filed and never before." % (DISPUTE, FRAUD))
    if DISPUTE_CLOSED not in events:
        return ("partial",
                "both opening signals are subscribed but %s is not, so nothing "
                "tells you how a dispute ended." % DISPUTE_CLOSED)
    return ("covered", "%s and %s subscribed" % (DISPUTE, FRAUD))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def subscribed_events(endpoints):
    """Union of enabled_events across endpoints. Pure, given the endpoint list."""
    union = set()
    for ep in endpoints:
        union.update(ep.get("enabled_events") or [])
    return union


def count(session, path, limit):
    """Count a paginated resource up to `limit`."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        seen += len(data)
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return seen


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-records", type=int, default=500,
                    help="stop counting disputes and warnings after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    union = subscribed_events(endpoints)
    disputes = count(s, "/disputes", args.max_records)
    warnings = count(s, "/radar/early_fraud_warnings", args.max_records)

    state, detail = verdict(union, disputes, warnings)
    line = "%-13s %s" % (state, detail)
    if state == "covered":
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  %d dispute(s), %d early fraud warning(s) on this account",
                disputes, warnings)
    if state != "wildcard":
        log.warning("  repair: POST %s/webhook_endpoints/%s", API,
                    endpoints[0]["id"] if endpoints else "<we_id>")
        for t in (DISPUTE, DISPUTE_CLOSED, FRAUD):
            if t not in union:
                log.warning("    -d enabled_events[]=%s", t)
        log.warning("    (enabled_events is replaced wholesale: send the existing "
                    "types too)")
    log.warning("  then sweep GET %s/disputes and %s/radar/early_fraud_warnings "
                "once: neither is retention limited the way /v1/events is",
                API, API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-dispute-events.mjs",
"js": '''/**
 * Report whether dispute and early fraud warning events are subscribed anywhere.
 *
 * Read only. Three GETs, no writes: give this a RESTRICTED key with read access
 * to Webhook Endpoints, Disputes and Radar. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const DISPUTE = 'charge.dispute.created';
const DISPUTE_CLOSED = 'charge.dispute.closed';
const FRAUD = 'radar.early_fraud_warning.created';

/**
 * Classify dispute and fraud coverage. Pure, so the rules can be tested.
 */
export function verdict(subscribed, disputes, warnings) {
  const events = new Set(subscribed ?? []);
  if (events.has('*')) {
    return ['wildcard',
      'a wildcard subscription covers both signals, but it also delivers every ' +
      'other event type to the same handler.'];
  }
  if (!events.has(DISPUTE)) {
    if (disputes) {
      return ['blind',
        `${disputes} dispute(s) on this account and nothing subscribes to ` +
        `${DISPUTE}. Every response deadline so far was found by email.`];
    }
    return ['unsubscribed',
      `nothing subscribes to ${DISPUTE}. No disputes yet, so this is a gap ` +
      'rather than a deadline already running.'];
  }
  if (!events.has(FRAUD)) {
    if (warnings) {
      return ['fraud-blind',
        `${warnings} early fraud warning(s) already raised and nothing subscribes ` +
        `to ${FRAUD}. A refund during that window prevents the chargeback outright.`];
    }
    return ['dispute-only',
      `${DISPUTE} is subscribed but ${FRAUD} is not. You will hear about ` +
      'chargebacks after they are filed and never before.'];
  }
  if (!events.has(DISPUTE_CLOSED)) {
    return ['partial',
      `both opening signals are subscribed but ${DISPUTE_CLOSED} is not, so ` +
      'nothing tells you how a dispute ended.'];
  }
  return ['covered', `${DISPUTE} and ${FRAUD} subscribed`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

/** Union of enabled_events across endpoints. Pure, given the endpoint list. */
export function subscribedEvents(endpoints) {
  const union = new Set();
  for (const ep of endpoints ?? []) {
    for (const t of ep.enabled_events ?? []) union.add(t);
  }
  return union;
}

async function countRecords(key, path, limit = 500) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    seen += data.length;
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return seen;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  const union = subscribedEvents(endpoints);
  const disputes = await countRecords(key, '/disputes');
  const warnings = await countRecords(key, '/radar/early_fraud_warnings');

  const [state, detail] = verdict(union, disputes, warnings);
  const line = `${state.padEnd(13)} ${detail}`;
  if (state === 'covered') {
    console.log(line);
    return;
  }

  console.warn(line);
  console.warn(`  ${disputes} dispute(s), ${warnings} early fraud warning(s) on this account`);
  if (state !== 'wildcard') {
    console.warn(`  repair: POST ${API}/webhook_endpoints/${endpoints[0]?.id ?? '<we_id>'}`);
    for (const t of [DISPUTE, DISPUTE_CLOSED, FRAUD]) {
      if (!union.has(t)) console.warn(`    -d enabled_events[]=${t}`);
    }
    console.warn('    (enabled_events is replaced wholesale: send the existing types too)');
  }
  console.warn(`  then sweep GET ${API}/disputes and ${API}/radar/early_fraud_warnings ` +
               'once: neither is retention limited the way /v1/events is');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests exist to stop the two signals collapsing into one. An account that hears about disputes but not about early fraud warnings is not covered, and calling it covered would delete the only state where a refund still costs less than a chargeback. The order matters too: a missing dispute subscription outranks everything else, because nothing downstream of it can be assessed.",
"test_py_file": "test_stripe_dispute_events.py",
"test_py": '''from stripe_dispute_events import verdict


def test_no_dispute_subscription_with_disputes_already_filed():
    state, detail = verdict(["charge.succeeded"], 7, 0)
    assert state == "blind"
    assert "7" in detail


def test_no_dispute_subscription_and_no_disputes_yet_is_only_a_gap():
    state, detail = verdict(["charge.succeeded"], 0, 0)
    assert state == "unsubscribed"
    assert "gap" in detail


def test_disputes_covered_but_fraud_warnings_are_not():
    state, detail = verdict(["charge.dispute.created"], 3, 12)
    assert state == "fraud-blind"
    assert "12" in detail


def test_disputes_covered_with_no_warnings_seen_is_still_incomplete():
    state, _ = verdict(["charge.dispute.created"], 3, 0)
    assert state == "dispute-only"


def test_both_opening_signals_without_the_closing_one():
    state, detail = verdict(["charge.dispute.created",
                             "radar.early_fraud_warning.created"], 3, 2)
    assert state == "partial"
    assert "charge.dispute.closed" in detail


def test_all_three_is_covered():
    state, _ = verdict(["charge.dispute.created", "charge.dispute.closed",
                        "radar.early_fraud_warning.created"], 3, 2)
    assert state == "covered"


def test_a_wildcard_is_reported_before_anything_else():
    state, _ = verdict(["*"], 7, 12)
    assert state == "wildcard"
''',
"test_js_file": "stripe-dispute-events.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-dispute-events.mjs';

test('no dispute subscription with disputes already filed', () => {
  const [state, detail] = verdict(['charge.succeeded'], 7, 0);
  assert.equal(state, 'blind');
  assert.match(detail, /7/);
});

test('no dispute subscription and no disputes yet is only a gap', () => {
  const [state, detail] = verdict(['charge.succeeded'], 0, 0);
  assert.equal(state, 'unsubscribed');
  assert.match(detail, /gap/);
});

test('disputes covered but fraud warnings are not', () => {
  const [state, detail] = verdict(['charge.dispute.created'], 3, 12);
  assert.equal(state, 'fraud-blind');
  assert.match(detail, /12/);
});

test('disputes covered with no warnings seen is still incomplete', () => {
  assert.equal(verdict(['charge.dispute.created'], 3, 0)[0], 'dispute-only');
});

test('both opening signals without the closing one', () => {
  const subs = ['charge.dispute.created', 'radar.early_fraud_warning.created'];
  const [state, detail] = verdict(subs, 3, 2);
  assert.equal(state, 'partial');
  assert.match(detail, /charge\\.dispute\\.closed/);
});

test('all three is covered', () => {
  const subs = ['charge.dispute.created', 'charge.dispute.closed',
    'radar.early_fraud_warning.created'];
  assert.equal(verdict(subs, 3, 2)[0], 'covered');
});

test('a wildcard is reported before anything else', () => {
  assert.equal(verdict(['*'], 7, 12)[0], 'wildcard');
});
''',
"faq": [
 ("What is an early fraud warning, exactly?",
  "A signal from the card issuer that a payment has been reported as fraudulent, raised before any chargeback is filed. It is listed at /v1/radar/early_fraud_warnings and pushed as radar.early_fraud_warning.created, and it is the last cheap moment to act on a bad order."),
 ("Should I refund every early fraud warning automatically?",
  "Refunding a warning with no dispute and no existing full refund is the usual policy, because it avoids the chargeback fee and keeps your dispute rate down. It is still a business decision: the handler should be able to consult the order state rather than refunding blindly."),
 ("Does Stripe not email me about disputes anyway?",
  "It notifies the account owner, which is one inbox with a filter in front of it. An email cannot open a ticket, halt a shipment or start a timer. Use the notification as a backstop and the event as the mechanism."),
 ("Why subscribe to charge.dispute.closed as well?",
  "Because it carries the outcome. Without it your win rate is compiled by hand from the Dashboard, and whatever internal state you set when the dispute opened is never cleared when it resolves."),
 ("Can I catch up on disputes that happened before I subscribed?",
  "Yes. Disputes and early fraud warnings both list from their own endpoints with no 30 day retention limit, unlike /v1/events. Sweep both once after subscribing, then rely on the events."),
],
"related": [
 ("/stripe/dispute-deadline-72h-no-evidence/", "A dispute deadline passes with no evidence submitted"),
 ("/stripe/disputes-lost-without-response/", "Disputes lost by default with no response filed"),
 ("/stripe/wildcard-enabled-events/", "An endpoint subscribes to every event and floods the handler"),
],
"citations": [CITE_EFW, CITE_DISPUTES, CITE_WEBHOOK_CREATE, CITE_RADAR_TESTING],
},

]
