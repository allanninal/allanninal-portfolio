#!/usr/bin/env python3
"""/stripe/ field notes, batch AC — the writing.

The last four notes in the section's enumeration: the v2 event destination that
was never created, Radar turning good customers away, a Payment Link that closed
itself, and a Billing Portal with the cancel button switched off. Same constraint
as the rest of the section: every note here is a problem a script can find with a
RESTRICTED, READ-ONLY Stripe key. None of these scripts writes. They read, they
say exactly what is wrong, and they print the repair for a human to run against a
live payments account.
"""

CITE_DEST_OBJ = ("The event destination object — Stripe API reference",
                 "https://docs.stripe.com/api/v2/core/event-destinations/object")
CITE_DEST_CREATE = ("Create an event destination — Stripe API reference",
                    "https://docs.stripe.com/api/v2/core/event-destinations/create")
CITE_DESTINATIONS = ("Event destinations — Stripe Docs",
                     "https://docs.stripe.com/event-destinations")
CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")

CITE_DECLINES = ("Declines — Stripe Docs", "https://docs.stripe.com/declines")
CITE_RADAR_RULES = ("Radar rules — Stripe Docs", "https://docs.stripe.com/radar/rules")
CITE_CHARGE_OBJ = ("The charge object — Stripe API reference",
                   "https://docs.stripe.com/api/charges/object")
CITE_CHARGE_LIST = ("List all charges — Stripe API reference",
                    "https://docs.stripe.com/api/charges/list")

CITE_LINK_OBJ = ("The Payment Link object — Stripe API reference",
                 "https://docs.stripe.com/api/payment-link/object")
CITE_LINK_CREATE = ("Create a payment link — Stripe API reference",
                    "https://docs.stripe.com/api/payment-link/create")
CITE_LINK_UPDATE = ("Update a payment link — Stripe API reference",
                    "https://docs.stripe.com/api/payment-link/update")
CITE_LINKS = ("Payment Links — Stripe Docs", "https://docs.stripe.com/payment-links")

CITE_PORTAL_CONFIG_OBJ = ("The portal configuration object — Stripe API reference",
                          "https://docs.stripe.com/api/customer_portal/configurations/object")
CITE_PORTAL_CONFIG_UPDATE = ("Update a portal configuration — Stripe API reference",
                             "https://docs.stripe.com/api/customer_portal/configurations/update")
CITE_PORTAL_ACTIVATE = ("Set up the customer portal — Stripe Docs",
                        "https://docs.stripe.com/customer-management/activate-no-code-customer-portal")
CITE_MONITORING = ("Dispute monitoring programs — Stripe Docs",
                   "https://docs.stripe.com/disputes/monitoring-programs")

GUIDES = [

{
"slug": "no-v2-event-destinations",
"title": "No v2 event destination exists, so thin events never arrive",
"description": "A v1.* event was added to the webhook endpoint and nothing was delivered. Thin events only reach a v2 event destination, a separate object entirely.",
"h1": "no v2 event destination exists, so thin events never arrive",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe v2 event destination", "stripe thin events not delivered",
             "event_payload thin", "v1.billing.meter.error_report_triggered",
             "stripe v2 core event destinations"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The feature you turned on documents an event with a <code>v1.</code> prefix in its name. Somebody added it to the webhook endpoint, saved, and nothing happened &mdash; no delivery, no failure, no entry in the endpoint's log. The event is real and it is being generated. It is being handed to a kind of destination your account does not have.",
"short_answer": """<p>Call <code>GET /v2/core/event_destinations</code> with a <code>Stripe-Version</code> that supports v2. If <code>data</code> is empty, or no element has <code>event_payload</code> of <code>"thin"</code>, then no thin event can reach you no matter what is listed on your <code>/v1/webhook_endpoints</code>.</p>
<p>Thin events are delivered <em>only</em> to a v2 event destination. It is a different object, created at a different endpoint, with its own signing secret and its own status. A snapshot (v1) endpoint cannot carry them, and adding one to <code>enabled_events</code> there does not make it try.</p>""",
"problem": """<p>Nothing about this failure looks like a failure. The endpoint you configured is enabled and healthy; it is delivering every event it has ever delivered. The new event type sits in its subscription list looking exactly like the others. Stripe is generating the event on schedule. Every component reports success and the handler never runs.</p>
<p>What makes it hard to see is the naming. The events are called things like <code>v1.billing.meter.error_report_triggered</code> &mdash; a <code>v1</code> prefix on an event that belongs to the <em>v2</em> delivery system, because the prefix describes the version of the resource the event is about, not the API that delivers it. Reading that name, the obvious conclusion is that it belongs on the v1 endpoint you already have. It does not.</p>""",
"why": """<p><strong>Thin events and snapshot events are two different products.</strong> A snapshot event carries a full object payload rendered at a pinned API version, which is what <code>/v1/webhook_endpoints</code> has always delivered. A thin event carries an id, a type and a pointer; you fetch the related object yourself at whatever version you speak today. Those are different payload contracts, so they were given different destinations rather than one destination with a flag.</p>
<p><strong>The v2 destination is created somewhere your integration has never been.</strong> <code>POST /v2/core/event_destinations</code> is a separate endpoint under a separate API surface. If your code, your Terraform and your runbook only know <code>/v1/webhook_endpoints</code>, there is nothing in your repository that would ever produce one, and nothing that would notice its absence.</p>
<p><strong>Newer features are the ones that use it.</strong> Billing meters, Accounts v2 and the money-management APIs emit thin events. So the gap only bites the day somebody adopts one of those, which is long after the webhook integration was written and reviewed, by which point it is treated as finished.</p>
<p><strong>A destination can exist and still be off.</strong> The v2 object carries its own <code>status</code> and <code>status_details</code>. A destination that was created and then disabled after repeated failures reads as configured to anyone counting rows, and delivers nothing, which is the same outcome as never having created it.</p>""",
"steps": [
 {"h": "List v2 destinations with a version that knows about them",
  "body": """<p><code>GET /v2/core/event_destinations</code> and send <code>Stripe-Version</code> explicitly. A key pinned to an older account default will get an error from this path rather than an empty list, and an error here means "your version cannot see v2", not "there is nothing there".</p>"""},
 {"h": "Check event_payload, not just the count",
  "body": """<p>A destination with <code>event_payload</code> of <code>"snapshot"</code> is a v2-shaped object delivering v1-shaped events. It is a perfectly reasonable thing to have and it will not carry a single thin event. Only <code>"thin"</code> counts for this check.</p>"""},
 {"h": "Read status and status_details on the ones that do exist",
  "body": """<p>The same disable-after-failure behaviour applies here as on a v1 endpoint. <code>status_details</code> is where Stripe records why, and it is the difference between a destination you need to create and one you need to fix.</p>"""},
 {"h": "Confirm you are actually using a v2 feature",
  "body": """<p><code>GET /v1/billing/meters?limit=1</code> returning data means thin events are being generated right now and dropped. An account with no v2 feature in use has the same gap and is not yet losing anything, which is the difference between a ticket and an incident.</p>"""},
 {"h": "Create the destination and parse the thin payload properly",
  "body": """<p>A thin event body is small on purpose. Verify it, call <code>parse_event_notification()</code>, then <code>fetchRelatedObject()</code> to pull the object at your own API version. Copying the v1 handler across and reading <code>event.data.object</code> will find nothing there.</p>"""},
],
"verify": """<p>Re-run the script. One enabled destination with <code>event_payload</code> of <code>thin</code> is all this check wants to see.</p>
<pre><code class="language-bash">python3 stripe_v2_event_destinations.py
# covered          ed_61RVAaB is enabled and takes thin events</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; one against the v2 list endpoint, one against Billing Meters to establish whether the gap is currently costing anything. A restricted key with read access to Event Destinations and Billing Meters is enough. The classifier is pure and takes the destination list plus that one boolean, because the same empty list means two different things depending on it.",
"py_file": "stripe_v2_event_destinations.py",
"py": '''"""Report a Stripe account with no v2 event destination for thin events.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access to
Event Destinations and Billing Meters. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_v2_event_destinations")

API_V1 = "https://api.stripe.com/v1"
API_V2 = "https://api.stripe.com/v2"

# Sent explicitly. The account default may predate v2 entirely, in which case the
# v2 path errors instead of returning an empty list, and the two look nothing
# alike once you know to tell them apart.
DEFAULT_VERSION = "2025-03-31.basil"


def verdict(destinations, v2_feature_in_use=False):
    """Classify an account's v2 event destinations. Pure, so it is testable offline.

    `destinations` is the list from /v2/core/event_destinations. `v2_feature_in_use`
    says whether anything on the account is currently generating thin events, which
    is what separates a gap from an outage. Returns (state, detail).
    """
    dests = list(destinations or [])
    thin = [d for d in dests if d.get("event_payload") == "thin"]
    enabled = [d for d in thin if d.get("status") == "enabled"]
    if enabled:
        return ("covered",
                "%s is enabled and takes thin events"
                % enabled[0].get("id", "<no id>"))
    if thin:
        d = thin[0]
        return ("disabled",
                "%s takes thin events but its status is %r: %s"
                % (d.get("id", "<no id>"), d.get("status"),
                   d.get("status_details") or "no status_details given"))
    if dests:
        return ("snapshot-only",
                "%d event destination(s) exist and every one of them is "
                "event_payload=snapshot, which cannot carry a thin event"
                % len(dests))
    if v2_feature_in_use:
        return ("dropping",
                "no v2 event destination at all, and a v2 feature is in use: the "
                "thin events it emits are being generated and delivered nowhere")
    return ("none",
            "no v2 event destination exists. Nothing emits thin events yet, so "
            "nothing is being lost today.")


def get(session, url, params=None, version=None):
    headers = {"Stripe-Version": version} if version else {}
    r = session.get(url, params=params or {}, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code in (400, 404) and "/v2/" in url:
        raise SystemExit(
            "%d from %s: this key or API version cannot see v2 resources. Retry "
            "with --api-version set to a version that supports v2." % (r.status_code, url))
    r.raise_for_status()
    return r.json()


def event_destinations(session, version):
    """Every v2 event destination.

    The v2 list endpoints paginate with an absolute `next_page_url` rather than the
    `starting_after` cursor the v1 list endpoints use, so the loop follows the URL
    Stripe hands back instead of building one.
    """
    out = []
    url = API_V2 + "/core/event_destinations"
    params = {"limit": 100}
    while url:
        page = get(session, url, params, version)
        out.extend(page.get("data", []))
        url = page.get("next_page_url")
        params = None
    return out


def v2_feature_in_use(session):
    """One cheap probe: does anything on this account emit thin events yet?

    Billing meters are the most common entry point. A different v2 feature would
    need its own probe; the point of the flag is only to separate a gap that costs
    nothing today from one that is losing events right now.
    """
    page = get(session, API_V1 + "/billing/meters", {"limit": 1})
    return bool(page.get("data"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--api-version", default=DEFAULT_VERSION,
                    help="Stripe-Version to send on the v2 request")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    dests = event_destinations(s, args.api_version)
    in_use = v2_feature_in_use(s)
    state, detail = verdict(dests, in_use)

    log.info("%-16s %s", state, detail)
    for d in dests:
        log.info("  %s  payload=%s  status=%s  events_from=%s",
                 d.get("id"), d.get("event_payload"), d.get("status"),
                 d.get("events_from"))
    if state == "covered":
        return 0

    if state == "disabled":
        log.warning("  repair: fix the handler, then re-enable the destination at "
                    "%s/core/event_destinations/<id>/enable", API_V2)
        return 1

    log.warning("  repair: create a thin destination (a separate object from any "
                "/v1/webhook_endpoints you already have):")
    log.warning("  POST %s/core/event_destinations -d type=webhook_endpoint "
                "-d event_payload=thin -d \\"events_from[]=@self\\" "
                "-d \\"enabled_events[]=v1.billing.meter.error_report_triggered\\" "
                "-d webhook_endpoint[url]=https://<yourdomain>/stripe/thin-webhook "
                "-d \\"include[]=webhook_endpoint.signing_secret\\"", API_V2)
    log.warning("  the signing secret is returned once, on create, and only if you "
                "ask for it with include[]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-v2-event-destinations.mjs",
"js": '''/**
 * Report a Stripe account with no v2 event destination for thin events.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read access
 * to Event Destinations and Billing Meters. The repair is printed, never performed.
 */
const API_V1 = 'https://api.stripe.com/v1';
const API_V2 = 'https://api.stripe.com/v2';

// Sent explicitly. The account default may predate v2 entirely, in which case the
// v2 path errors instead of returning an empty list.
const DEFAULT_VERSION = '2025-03-31.basil';

/**
 * Classify an account's v2 event destinations. Pure, so it is testable offline.
 * The same empty list is a gap or an outage depending on `v2FeatureInUse`.
 */
export function verdict(destinations, v2FeatureInUse = false) {
  const dests = destinations ?? [];
  const thin = dests.filter((d) => d.event_payload === 'thin');
  const enabled = thin.filter((d) => d.status === 'enabled');
  if (enabled.length) {
    return ['covered', `${enabled[0].id ?? '<no id>'} is enabled and takes thin events`];
  }
  if (thin.length) {
    const d = thin[0];
    return ['disabled',
      `${d.id ?? '<no id>'} takes thin events but its status is ` +
      `${JSON.stringify(d.status)}: ${d.status_details ?? 'no status_details given'}`];
  }
  if (dests.length) {
    return ['snapshot-only',
      `${dests.length} event destination(s) exist and every one of them is ` +
      'event_payload=snapshot, which cannot carry a thin event'];
  }
  if (v2FeatureInUse) {
    return ['dropping',
      'no v2 event destination at all, and a v2 feature is in use: the thin ' +
      'events it emits are being generated and delivered nowhere'];
  }
  return ['none',
    'no v2 event destination exists. Nothing emits thin events yet, so nothing ' +
    'is being lost today.'];
}

async function get(key, url, params = {}, version = null) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const headers = { Authorization: `Bearer ${key}` };
  if (version) headers['Stripe-Version'] = version;
  const res = await fetch(u, { headers });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if ((res.status === 400 || res.status === 404) && u.pathname.startsWith('/v2/')) {
    throw new Error(`${res.status} from ${u.pathname}: this key or API version ` +
                    'cannot see v2 resources');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

/**
 * The v2 list endpoints paginate with an absolute next_page_url rather than the
 * starting_after cursor the v1 list endpoints use.
 */
export async function eventDestinations(key, version = DEFAULT_VERSION) {
  const out = [];
  let url = `${API_V2}/core/event_destinations`;
  let params = { limit: 100 };
  while (url) {
    const page = await get(key, url, params, version);
    out.push(...(page.data ?? []));
    url = page.next_page_url ?? null;
    params = {};
  }
  return out;
}

export async function v2FeatureInUse(key) {
  const page = await get(key, `${API_V1}/billing/meters`, { limit: 1 });
  return (page.data ?? []).length > 0;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const version = process.argv[2] ?? DEFAULT_VERSION;
  const dests = await eventDestinations(key, version);
  const inUse = await v2FeatureInUse(key);
  const [state, detail] = verdict(dests, inUse);

  console.log(`${state.padEnd(16)} ${detail}`);
  for (const d of dests) {
    console.log(`  ${d.id}  payload=${d.event_payload}  status=${d.status}  ` +
                `events_from=${JSON.stringify(d.events_from ?? null)}`);
  }
  if (state === 'covered') return;

  if (state === 'disabled') {
    console.warn('  repair: fix the handler, then re-enable the destination at ' +
                 `${API_V2}/core/event_destinations/<id>/enable`);
    process.exitCode = 1;
    return;
  }

  console.warn('  repair: create a thin destination (a separate object from any ' +
               '/v1/webhook_endpoints you already have):');
  console.warn(`  POST ${API_V2}/core/event_destinations -d type=webhook_endpoint ` +
               '-d event_payload=thin -d "events_from[]=@self" ' +
               '-d "enabled_events[]=v1.billing.meter.error_report_triggered" ' +
               '-d webhook_endpoint[url]=https://<yourdomain>/stripe/thin-webhook ' +
               '-d "include[]=webhook_endpoint.signing_secret"');
  console.warn('  the signing secret is returned once, on create, and only if you ' +
               'ask for it with include[]');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test to read is the snapshot-only one. An account with three v2 event destinations, none of them thin, satisfies every check that counts rows and drops every thin event Stripe generates. The other one worth pinning is the split between an empty list on an account using Billing meters and an empty list on an account that is not: identical configuration, and only one of them is currently losing events.",
"test_py_file": "test_stripe_v2_event_destinations.py",
"test_py": '''from stripe_v2_event_destinations import verdict

THIN = {"id": "ed_1", "event_payload": "thin", "status": "enabled"}
SNAPSHOT = {"id": "ed_2", "event_payload": "snapshot", "status": "enabled"}


def test_an_enabled_thin_destination_is_all_that_is_needed():
    state, detail = verdict([THIN, SNAPSHOT], True)
    assert state == "covered"
    assert "ed_1" in detail


def test_a_thin_destination_that_is_disabled_delivers_nothing():
    dead = {"id": "ed_3", "event_payload": "thin", "status": "disabled",
            "status_details": "disabled after repeated 500s"}
    state, detail = verdict([dead], True)
    assert state == "disabled"
    assert "repeated 500s" in detail


def test_snapshot_destinations_do_not_count_as_coverage():
    # Three destinations, a row count that looks configured, and not one of them
    # can carry a thin event.
    state, detail = verdict([SNAPSHOT, SNAPSHOT, SNAPSHOT], True)
    assert state == "snapshot-only"
    assert "3 event destination(s)" in detail


def test_nothing_configured_while_a_v2_feature_runs_is_an_outage():
    state, detail = verdict([], True)
    assert state == "dropping"
    assert "delivered nowhere" in detail


def test_nothing_configured_and_no_v2_feature_is_only_a_gap():
    assert verdict([], False)[0] == "none"
    assert verdict(None, False)[0] == "none"
''',
"test_js_file": "stripe-v2-event-destinations.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-v2-event-destinations.mjs';

const THIN = { id: 'ed_1', event_payload: 'thin', status: 'enabled' };
const SNAPSHOT = { id: 'ed_2', event_payload: 'snapshot', status: 'enabled' };

test('an enabled thin destination is all that is needed', () => {
  const [state, detail] = verdict([THIN, SNAPSHOT], true);
  assert.equal(state, 'covered');
  assert.match(detail, /ed_1/);
});

test('a thin destination that is disabled delivers nothing', () => {
  const dead = { id: 'ed_3', event_payload: 'thin', status: 'disabled',
                 status_details: 'disabled after repeated 500s' };
  const [state, detail] = verdict([dead], true);
  assert.equal(state, 'disabled');
  assert.match(detail, /repeated 500s/);
});

test('snapshot destinations do not count as coverage', () => {
  const [state, detail] = verdict([SNAPSHOT, SNAPSHOT, SNAPSHOT], true);
  assert.equal(state, 'snapshot-only');
  assert.match(detail, /3 event destination/);
});

test('nothing configured while a v2 feature runs is an outage', () => {
  const [state, detail] = verdict([], true);
  assert.equal(state, 'dropping');
  assert.match(detail, /delivered nowhere/);
});

test('nothing configured and no v2 feature is only a gap', () => {
  assert.equal(verdict([], false)[0], 'none');
  assert.equal(verdict(null, false)[0], 'none');
});
''',
"faq": [
 ("Why is the event called v1.something if it needs a v2 destination?",
  "The prefix names the version of the resource the event describes, not the API that delivers it. v1.billing.meter.error_report_triggered is an event about a v1-shaped billing meter, delivered as a thin event through the v2 event destination system. Reading the prefix as a delivery version is the exact mistake that puts it on the wrong endpoint."),
 ("Can I add a thin event type to my existing /v1/webhook_endpoints endpoint?",
  "No. A snapshot endpoint carries snapshot events. Listing a thin event type there does not cause delivery, and the absence of an error at save time is what makes the failure so quiet."),
 ("Does a v2 destination replace my v1 webhook endpoint?",
  "Not unless you want it to. Most accounts end up with both: the v1 endpoint keeps taking snapshot events with full payloads, and the v2 thin destination takes the newer ones. They are separate objects with separate signing secrets, and both have to be verified separately."),
 ("Where do I get the signing secret for a v2 event destination?",
  "It is returned on create, and only if you ask for it: pass include[]=webhook_endpoint.signing_secret in the create call. It is not shown again afterwards, so capture it in that response rather than planning to look it up later."),
 ("Why does the thin event payload not contain the object?",
  "By design. A thin event carries the id, the type and a pointer, and you fetch the related object yourself at your own API version. That removes the pinned-version problem snapshot events have, and it means a handler copied from the v1 side that reads event.data.object will find nothing there."),
],
"related": [
 ("/stripe/no-live-webhook-endpoints/", "Live mode has no webhook endpoint, so nothing is ever pushed"),
 ("/stripe/dead-or-rejected-enabled-events/", "enabled_events lists event types that are dead or rejected"),
 ("/stripe/endpoint-api-version-pinned-stale/", "A webhook endpoint is pinned to an ancient api_version"),
],
"citations": [CITE_DEST_OBJ, CITE_DEST_CREATE, CITE_DESTINATIONS, CITE_WEBHOOKS],
},

{
"slug": "radar-blocked-rate-overblocking",
"title": "Radar is blocking a large share of your charge attempts",
"description": "Conversion drops after a rule change. Customers say the card works everywhere else, and it does: the payment never reached their bank.",
"h1": "radar is blocking a large share of your charge attempts",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe radar blocking too many payments", "radar false positives",
             "stripe block rate", "radar rule overblocking",
             "not_sent_to_network"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Conversion stepped down on a specific day and stayed there. Support is hearing the same sentence from different customers: the card works everywhere else. It does work everywhere else &mdash; those payments were stopped before they were ever sent to an issuer, by a rule somebody wrote here.",
"short_answer": """<p>Over a fixed window, compute <code>count(outcome.type == "blocked") / count(all charges)</code>, then take out the blocks with <code>outcome.reason == "low_probability_of_authorization"</code>. Those are Adaptive Acceptance skipping an attempt Stripe expected to fail, not your rules. What is left is the rate you own.</p>
<p>Then group the remaining blocks by <code>outcome.rule.predicate</code>. One predicate responsible for most of them, on charges whose <code>outcome.risk_level</code> is <code>normal</code>, is the signature of an over-broad rule: it is not catching fraud, it is catching a country, a BIN or an amount band.</p>""",
"problem": """<p>Over-blocking is invisible from inside the account because it produces no bad records at all. There are no chargebacks from a payment that never happened, no refunds, no angry emails from anyone except the small fraction of customers who bother to write in. The fraud numbers look excellent, precisely because you are turning away the good traffic along with the bad.</p>
<p>The related note, <a href="/stripe/radar-blocked-payments-ignored/">Radar blocks payments and nobody reads the block reasons</a>, is about not looking at the individual reason codes at all. This one is the aggregate: you may be reading them fine and still not know that the rate has moved. A single rule edit can shift the block rate by several points overnight, and nothing in the Dashboard tells you that, because Stripe has no view on what your correct block rate is.</p>""",
"why": """<p><strong>A block leaves no trail on the customer's side.</strong> Radar stops the charge before authorization, so <code>outcome.network_status</code> reads <code>not_sent_to_network</code>. The customer's bank has no record of the attempt and will tell them the card is fine. Both of you are correct and neither of you can see the other's evidence.</p>
<p><strong>Rules are written broadly under pressure and narrowed never.</strong> Stripe's own documentation uses <code>if :card_country: != 'US'</code> as the example of a rule that is too broad. Rules like that get written during a fraud wave, when blocking a whole category is the fast fix. Nothing expires them, and no report tells you what one of them cost last month.</p>
<p><strong>The one number that would show it is not on any dashboard by default.</strong> Block rate as a share of attempts, tracked as a series, is the only thing that makes a step change visible. Every part of it is available in <code>outcome</code>, and computing it takes one paginated GET, which is why it is worth doing on a schedule rather than after a quarter of soft conversion.</p>
<p><strong>Adaptive Acceptance inflates the number if you let it.</strong> <code>low_probability_of_authorization</code> means Stripe predicted the issuer would decline and saved you the network fee. Counting those as your blocks sends you to edit rules that were never involved, and hides the movement in the rate you can actually change.</p>""",
"steps": [
 {"h": "Page a fixed window of charges and tally outcome.type",
  "body": """<p><code>GET /v1/charges?created[gte]=&lt;unix&gt;&amp;limit=100</code>, paginated. Add <code>expand[]=data.outcome.rule</code> so the rule comes back as an object with its <code>predicate</code> rather than as a bare id you would have to look up one at a time.</p>"""},
 {"h": "Subtract Adaptive Acceptance before you judge the rate",
  "body": """<p>Count <code>outcome.reason == "low_probability_of_authorization"</code> separately and take it out of the numerator. What remains is blocks caused by Stripe's risk threshold (<code>highest_risk_level</code>) and by your own rules (<code>rule</code>) &mdash; the two you can actually move.</p>"""},
 {"h": "Group the rule blocks by predicate",
  "body": """<p>The predicate string is the rule as written. Sorting blocks by predicate turns "Radar is blocking too much" into "this one line blocked 412 charges last month", which is a sentence somebody can act on.</p>"""},
 {"h": "Check the risk level on the charges that predicate blocked",
  "body": """<p>If most of them have <code>outcome.risk_level</code> of <code>normal</code>, the rule is not overlapping with Stripe's fraud signal at all. It is blocking on an attribute. That is the clearest evidence of over-blocking you will get from the API.</p>"""},
 {"h": "Compare against the window before it",
  "body": """<p>Run the same tally over the preceding window. A rate that doubled between two adjacent windows dates the change, and the date is usually enough to find the rule edit that caused it.</p>"""},
 {"h": "Narrow the predicate rather than deleting the rule",
  "body": """<p>Stripe's own remediation for a too-broad rule is to add a risk condition to it: <code>and :risk_level: = 'elevated'</code>. Converting the block to a review while you gather data is the other safe move. Check the rule's estimated false positive rate in the Dashboard before re-enabling it.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the rule change. The rate you own should be back in a range you can justify, and no single predicate should dominate it.</p>
<pre><code class="language-bash">python3 stripe_block_rate.py --days 30
# normal      41 of 8,120 attempt(s) blocked by rules or risk (0.5%)</code></pre>""",
"code_intro": "One paginated GET against Charges and no writes &mdash; a restricted key with read access to Charges is enough. The classifier is pure and takes four numbers plus the worst predicate, because every judgement in this check is a threshold, and thresholds are exactly what a live account makes impossible to test.",
"py_file": "stripe_block_rate.py",
"py": '''"""Report a Stripe account where Radar blocks too large a share of attempts.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Charges. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_block_rate")

API = "https://api.stripe.com/v1"

HIGH_RATE = 0.05    # one attempt in twenty stopped before the issuer saw it
WATCH_RATE = 0.02   # worth a look before it becomes the conversion investigation
DOMINANT = 0.5      # one predicate causing at least half of the blocks
MOSTLY_NORMAL = 0.8  # and those charges scoring normal risk, not elevated


def verdict(total, blocked, adaptive=0, top_rule=None):
    """Classify one window of charge attempts. Pure, so the thresholds are testable.

    `total` is every charge attempt in the window, `blocked` the ones Radar stopped,
    `adaptive` the subset blocked as low_probability_of_authorization, and
    `top_rule` is (predicate, blocked_count, normal_risk_count) for the single
    predicate responsible for the most blocks, or None. Returns (state, detail).
    """
    if not total:
        return ("no-data", "no charge attempts in the window")
    if not blocked:
        return ("normal", "no blocked charges in %d attempt(s)" % total)

    own = max(blocked - adaptive, 0)
    if not own:
        return ("adaptive-only",
                "%d of %d attempt(s) blocked (%.1f%%), every one of them "
                "low_probability_of_authorization: that is Adaptive Acceptance "
                "skipping a decline, not a rule of yours"
                % (blocked, total, 100.0 * blocked / total))

    pct = 100.0 * own / total
    if own / float(total) >= HIGH_RATE:
        if top_rule:
            predicate, count, normal = top_rule
            if (count >= DOMINANT * own
                    and count and normal >= MOSTLY_NORMAL * count):
                return ("overblocking-rule",
                        "%d of %d attempt(s) blocked (%.1f%%), and %d of those came "
                        "from one predicate (%s) on charges Radar scored normal risk"
                        % (own, total, pct, count, predicate))
        return ("elevated",
                "%d of %d attempt(s) blocked by rules or risk (%.1f%%), spread "
                "across predicates: check the risk threshold as well as the rules"
                % (own, total, pct))
    if own / float(total) >= WATCH_RATE:
        return ("watch",
                "%d of %d attempt(s) blocked by rules or risk (%.1f%%). Track it as "
                "a series; a step change dates the rule edit." % (own, total, pct))
    return ("normal",
            "%d of %d attempt(s) blocked by rules or risk (%.1f%%)"
            % (own, total, pct))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def scan(session, since, until, cap):
    """Tally blocks across one window.

    outcome.rule is expanded in the request, because unexpanded it is an id and the
    predicate is the only part of it worth reading.
    """
    total = blocked = adaptive = 0
    per_rule = {}
    params = {"created[gte]": since, "created[lt]": until, "limit": 100,
              "expand[]": "data.outcome.rule"}
    while True:
        page = get(session, "/charges", params)
        data = page.get("data", [])
        for charge in data:
            total += 1
            outcome = charge.get("outcome") or {}
            if outcome.get("type") != "blocked":
                continue
            blocked += 1
            reason = outcome.get("reason")
            if reason == "low_probability_of_authorization":
                adaptive += 1
                continue
            rule = outcome.get("rule")
            if isinstance(rule, dict):
                predicate = rule.get("predicate") or rule.get("id") or "<no predicate>"
            elif rule:
                predicate = str(rule)
            else:
                predicate = reason or "<no rule>"
            count, normal = per_rule.get(predicate, (0, 0))
            per_rule[predicate] = (
                count + 1,
                normal + (1 if outcome.get("risk_level") == "normal" else 0))
        if not data or not page.get("has_more") or total >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return total, blocked, adaptive, per_rule


def worst(per_rule):
    """The predicate with the most blocks, as (predicate, count, normal_risk)."""
    if not per_rule:
        return None
    predicate, (count, normal) = max(per_rule.items(), key=lambda kv: kv[1][0])
    return (predicate, count, normal)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="window to measure, in days (keep it fixed between runs)")
    ap.add_argument("--max-charges", type=int, default=5000,
                    help="stop paginating after this many charges per window")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    span = args.days * 86400
    total, blocked, adaptive, per_rule = scan(s, now - span, now, args.max_charges)
    state, detail = verdict(total, blocked, adaptive, worst(per_rule))

    log.info("%-17s %s", state, detail)
    if adaptive:
        log.info("  %d adaptive block(s) excluded (low_probability_of_authorization)",
                 adaptive)
    for predicate, (count, normal) in sorted(per_rule.items(),
                                             key=lambda kv: -kv[1][0])[:5]:
        log.info("  %4d blocked  %4d at normal risk  %s", count, normal, predicate)

    prev_total, prev_blocked, prev_adaptive, _ = scan(
        s, now - 2 * span, now - span, args.max_charges)
    if prev_total:
        log.info("  previous window: %.1f%% blocked by rules or risk",
                 100.0 * max(prev_blocked - prev_adaptive, 0) / prev_total)

    if state in ("normal", "no-data", "adaptive-only"):
        return 0
    log.warning("  repair: narrow the predicate in Dashboard > Radar > Rules rather "
                "than deleting the rule, e.g. add: and :risk_level: = 'elevated'")
    log.warning("  or convert it to a review rule while you gather data, and check "
                "its estimated false positive rate before re-enabling")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-block-rate.mjs",
"js": '''/**
 * Report a Stripe account where Radar blocks too large a share of attempts.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Charges. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const HIGH_RATE = 0.05;      // one attempt in twenty stopped before the issuer saw it
const WATCH_RATE = 0.02;     // worth a look before it becomes a conversion problem
const DOMINANT = 0.5;        // one predicate causing at least half of the blocks
const MOSTLY_NORMAL = 0.8;   // and those charges scoring normal risk, not elevated

/**
 * Classify one window of charge attempts. Pure, so the thresholds are testable.
 * `topRule` is [predicate, blockedCount, normalRiskCount] or null.
 */
export function verdict(total, blocked, adaptive = 0, topRule = null) {
  if (!total) return ['no-data', 'no charge attempts in the window'];
  if (!blocked) return ['normal', `no blocked charges in ${total} attempt(s)`];

  const own = Math.max(blocked - adaptive, 0);
  if (!own) {
    return ['adaptive-only',
      `${blocked} of ${total} attempt(s) blocked ` +
      `(${(100 * blocked / total).toFixed(1)}%), every one of them ` +
      'low_probability_of_authorization: that is Adaptive Acceptance skipping a ' +
      'decline, not a rule of yours'];
  }

  const pct = (100 * own / total).toFixed(1);
  if (own / total >= HIGH_RATE) {
    if (topRule) {
      const [predicate, count, normal] = topRule;
      if (count >= DOMINANT * own && count && normal >= MOSTLY_NORMAL * count) {
        return ['overblocking-rule',
          `${own} of ${total} attempt(s) blocked (${pct}%), and ${count} of those ` +
          `came from one predicate (${predicate}) on charges Radar scored normal risk`];
      }
    }
    return ['elevated',
      `${own} of ${total} attempt(s) blocked by rules or risk (${pct}%), spread ` +
      'across predicates: check the risk threshold as well as the rules'];
  }
  if (own / total >= WATCH_RATE) {
    return ['watch',
      `${own} of ${total} attempt(s) blocked by rules or risk (${pct}%). Track it ` +
      'as a series; a step change dates the rule edit.'];
  }
  return ['normal',
    `${own} of ${total} attempt(s) blocked by rules or risk (${pct}%)`];
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

export async function scan(key, since, until, cap = 5000) {
  let total = 0; let blocked = 0; let adaptive = 0;
  const perRule = new Map();
  const params = {
    'created[gte]': since, 'created[lt]': until, limit: 100,
    'expand[]': 'data.outcome.rule',
  };
  for (;;) {
    const page = await get(key, '/charges', params);
    const data = page.data ?? [];
    for (const charge of data) {
      total += 1;
      const outcome = charge.outcome ?? {};
      if (outcome.type !== 'blocked') continue;
      blocked += 1;
      if (outcome.reason === 'low_probability_of_authorization') { adaptive += 1; continue; }
      const rule = outcome.rule;
      const predicate = (rule && typeof rule === 'object')
        ? (rule.predicate ?? rule.id ?? '<no predicate>')
        : (rule ?? outcome.reason ?? '<no rule>');
      const [count, normal] = perRule.get(predicate) ?? [0, 0];
      perRule.set(predicate,
        [count + 1, normal + (outcome.risk_level === 'normal' ? 1 : 0)]);
    }
    if (data.length === 0 || !page.has_more || total >= cap) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { total, blocked, adaptive, perRule };
}

export function worst(perRule) {
  let best = null;
  for (const [predicate, [count, normal]] of perRule) {
    if (!best || count > best[1]) best = [predicate, count, normal];
  }
  return best;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.argv[2] ?? 30);
  const now = Math.floor(Date.now() / 1000);
  const span = days * 86400;
  const { total, blocked, adaptive, perRule } = await scan(key, now - span, now);
  const [state, detail] = verdict(total, blocked, adaptive, worst(perRule));

  console.log(`${state.padEnd(17)} ${detail}`);
  if (adaptive) {
    console.log(`  ${adaptive} adaptive block(s) excluded ` +
                '(low_probability_of_authorization)');
  }
  for (const [predicate, [count, normal]] of
       [...perRule].sort((a, b) => b[1][0] - a[1][0]).slice(0, 5)) {
    console.log(`  ${count} blocked  ${normal} at normal risk  ${predicate}`);
  }

  const prev = await scan(key, now - 2 * span, now - span);
  if (prev.total) {
    const prevOwn = Math.max(prev.blocked - prev.adaptive, 0);
    console.log(`  previous window: ${(100 * prevOwn / prev.total).toFixed(1)}% ` +
                'blocked by rules or risk');
  }

  if (state === 'normal' || state === 'no-data' || state === 'adaptive-only') return;
  console.warn('  repair: narrow the predicate in Dashboard > Radar > Rules rather ' +
               "than deleting the rule, e.g. add: and :risk_level: = 'elevated'");
  console.warn('  or convert it to a review rule while you gather data, and check ' +
               'its estimated false positive rate before re-enabling');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two tests carry the note. The first is the account whose entire block count is Adaptive Acceptance: a 6% raw block rate, nothing wrong, and a naive check would have sent somebody to edit rules that never fired. The second is the same high rate concentrated in one predicate on charges Radar itself scored normal &mdash; that is the shape of a rule catching an attribute rather than fraud, and it is the only state that names the line to change.",
"test_py_file": "test_stripe_block_rate.py",
"test_py": '''from stripe_block_rate import verdict


def test_an_empty_window_is_not_a_finding():
    assert verdict(0, 0)[0] == "no-data"


def test_a_low_block_rate_is_normal():
    assert verdict(1000, 4)[0] == "normal"


def test_blocks_that_are_all_adaptive_acceptance_are_not_yours():
    # 6% raw, and not one of them came from a rule. Editing rules here changes
    # nothing at all.
    state, detail = verdict(1000, 60, 60)
    assert state == "adaptive-only"
    assert "Adaptive Acceptance" in detail


def test_a_dominant_predicate_on_normal_risk_charges_names_the_rule():
    state, detail = verdict(1000, 80, 10, (":card_country: != 'US'", 60, 58))
    assert state == "overblocking-rule"
    assert ":card_country:" in detail


def test_a_high_rate_spread_across_predicates_is_still_elevated():
    state, _ = verdict(1000, 80, 0, ("amount > 20000", 20, 18))
    assert state == "elevated"


def test_a_dominant_predicate_on_risky_charges_is_the_rule_working():
    # Same share of blocks, but Radar scored those charges risky too, so the rule
    # is agreeing with the fraud signal rather than replacing it.
    state, _ = verdict(1000, 80, 0, ("card_country != 'US'", 60, 4))
    assert state == "elevated"


def test_a_middling_rate_is_worth_watching_not_paging():
    state, detail = verdict(1000, 30)
    assert state == "watch"
    assert "series" in detail
''',
"test_js_file": "stripe-block-rate.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-block-rate.mjs';

test('an empty window is not a finding', () => {
  assert.equal(verdict(0, 0)[0], 'no-data');
});

test('a low block rate is normal', () => {
  assert.equal(verdict(1000, 4)[0], 'normal');
});

test('blocks that are all adaptive acceptance are not yours', () => {
  const [state, detail] = verdict(1000, 60, 60);
  assert.equal(state, 'adaptive-only');
  assert.match(detail, /Adaptive Acceptance/);
});

test('a dominant predicate on normal risk charges names the rule', () => {
  const [state, detail] = verdict(1000, 80, 10, [":card_country: != 'US'", 60, 58]);
  assert.equal(state, 'overblocking-rule');
  assert.match(detail, /card_country/);
});

test('a high rate spread across predicates is still elevated', () => {
  assert.equal(verdict(1000, 80, 0, ['amount > 20000', 20, 18])[0], 'elevated');
});

test('a dominant predicate on risky charges is the rule working', () => {
  assert.equal(verdict(1000, 80, 0, ["card_country != 'US'", 60, 4])[0], 'elevated');
});

test('a middling rate is worth watching not paging', () => {
  const [state, detail] = verdict(1000, 30);
  assert.equal(state, 'watch');
  assert.match(detail, /series/);
});
''',
"faq": [
 ("What block rate is too high?",
  "There is no universal number, which is why the script reports a rate rather than a pass or fail. What matters is the series: a rate that was 0.4% for a year and is 5% since a Tuesday is a rule edit, not a change in your customers. The thresholds in the script are a starting point to be tuned to your own baseline."),
 ("How is this different from reading the block reasons?",
  "Reading reasons tells you why one charge was stopped. This note is about the aggregate share of attempts being stopped, which is the only way over-blocking shows up at all. The two go together: the rate says something moved, and the reasons say which rule moved it."),
 ("Why exclude low_probability_of_authorization from the rate?",
  "Because it is not a fraud decision and not yours. Adaptive Acceptance predicted the issuer would decline and skipped the network fee. Leaving it in the numerator inflates the rate and points the investigation at rules that never fired."),
 ("Can I tell how much revenue a rule cost me?",
  "Approximately. Sum the amount field on the charges a predicate blocked, and treat it as an upper bound: some of those attempts would have been declined by the issuer anyway, and genuine fraud is in there too. It is still the number that ends most arguments about whether to narrow a rule."),
 ("What is the safest way to loosen a rule?",
  "Add a condition rather than deleting the rule. Stripe's own remediation for an over-broad predicate is to require an elevated risk level alongside it. Converting the rule from block to review is the other option: you keep seeing the traffic and stop turning it away while you decide."),
],
"related": [
 ("/stripe/radar-blocked-payments-ignored/", "Radar blocks payments and nobody reads the block reasons"),
 ("/stripe/highest-risk-charges-succeeded/", "Highest-risk charges are succeeding instead of being blocked"),
 ("/stripe/elevated-risk-charges-no-review/", "Elevated-risk charges captured with no manual review step"),
],
"citations": [CITE_DECLINES, CITE_RADAR_RULES, CITE_CHARGE_OBJ, CITE_CHARGE_LIST],
},

{
"slug": "payment-link-completion-limit-reached",
"title": "Payment Link hit its completed-session limit and went dead",
"description": "A campaign link converts for the first N buyers and then stops. The restriction counter reached its cap and the link closed itself, silently.",
"h1": "payment link hit its completed-session limit and went dead",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payment link restrictions", "completed_sessions limit",
             "stripe payment link stopped working", "payment link sold out",
             "stripe payment link limit reached"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The campaign link worked. Fifty people bought through it and then the orders stopped, on a link nobody touched, in a week nobody deployed. The link is still active, still resolving, still in the email that goes out every morning. It reached the number of completed sessions it was created with and closed itself.",
"short_answer": """<p>Page <code>GET /v1/payment_links?limit=100</code> and read <code>restrictions.completed_sessions</code>. The failure is <code>count &gt;= limit</code>: the cap has been met and the link no longer accepts completions. <code>count / limit &gt;= 0.9</code> is the same link a few days earlier, which is the version worth catching.</p>
<p>Note that <code>active</code> is still <code>true</code> on an exhausted link. This is not the deactivated-link case in <a href="/stripe/payment-link-inactive-still-published/">A deactivated Payment Link is still linked from your site</a> &mdash; nobody switched this one off. It reached a number.</p>""",
"problem": """<p>A completion cap is set once, usually for a good reason: a limited run, a workshop with twenty seats, a founding-member price for the first hundred customers. It is set at creation, in a nested parameter, and then it is never seen again, because the link object is not something anyone opens after the campaign starts.</p>
<p>The counter that eventually closes the link is read-only and silent. There is no event when it approaches the limit and no event when it reaches it. From the outside the link looks completely normal: the URL resolves, <code>active</code> is <code>true</code>, and Stripe simply stops letting new sessions complete on it. Meanwhile every place the URL is published carries on sending people to it.</p>""",
"why": """<p><strong>The cap and the traffic are set by different people at different times.</strong> Whoever created the link picked a number that matched the plan that week. Whoever scheduled the newsletter, printed the QR code or wired the link into the pricing page did so later and knows nothing about a restriction nested three keys deep in the object.</p>
<p><strong>There is no notification as the counter approaches the cap.</strong> <code>restrictions.completed_sessions.count</code> is maintained by Stripe and cannot be written. Nothing fires at 90%, nothing fires at 100%, and the only way to see it is to ask for the object.</p>
<p><strong>The symptom looks like demand, not like a bug.</strong> Sales tail off at the end of a campaign, which is what campaigns do. A link that stops converting after fifty orders looks exactly like a campaign that ran out of audience, and that is the story everyone will believe until somebody reads the counter.</p>
<p><strong>The link stays <code>active</code>, so every check you own passes.</strong> A link checker gets a 200. A script that looks for <code>active == false</code> finds nothing. The one field that changed is a counter inside <code>restrictions</code>, and no generic health check has ever looked there.</p>""",
"steps": [
 {"h": "List every Payment Link and read the restrictions object",
  "body": """<p>Paginate <code>GET /v1/payment_links?limit=100</code>. <code>restrictions</code> is <code>null</code> on most links, which is the uncapped case and the one you can stop thinking about. The links with a <code>completed_sessions.limit</code> are the whole population of this problem.</p>"""},
 {"h": "Compare count against limit, and flag the near misses too",
  "body": """<p><code>count &gt;= limit</code> is already dead. <code>count / limit &gt;= 0.9</code> is dead this week. The second one is the finding worth acting on, because it is the only version of this you can fix before customers are turned away.</p>"""},
 {"h": "Check whether people are still arriving",
  "body": """<p><code>GET /v1/checkout/sessions?payment_link={plink_id}&amp;limit=100</code>. Recent sessions sitting at <code>open</code> or <code>expired</code> against an exhausted link are customers who clicked, found they could not complete, and left. That count is what turns this from housekeeping into lost revenue.</p>"""},
 {"h": "Decide whether the cap was a business rule or a guess",
  "body": """<p>Twenty seats in a room is a real constraint and the link doing its job. "A hundred, to be safe" is a guess that has now become a revenue ceiling. Only one of those should be raised, and the difference is not something the API can tell you.</p>"""},
 {"h": "Raise the cap or publish a fresh link",
  "body": """<p><code>POST /v1/payment_links/{plink_id}</code> with <code>restrictions[completed_sessions][limit]</code> set higher keeps the same URL, which fixes every place it was published at once. A new link for the next tranche means swapping the URL everywhere, which is the slower option and sometimes the right one.</p>"""},
],
"verify": """<p>Re-run the script. Every capped link should have headroom, and no link should be reporting recent sessions it cannot complete.</p>
<pre><code class="language-bash">python3 stripe_payment_link_limits.py
# headroom     plink_1MoBy5  42 of 200 completed session(s)
# uncapped     plink_1KqAa2  no completion limit set</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Payment Links and Checkout Sessions is enough. The classifier is pure and takes the <code>restrictions</code> object exactly as Stripe returns it, plus the recent session count, because the interesting judgement here is the difference between a link that is exhausted and one that is exhausted <em>and still being clicked</em>.",
"py_file": "stripe_payment_link_limits.py",
"py": '''"""Report Stripe Payment Links that have reached their completed-session limit.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access to
Payment Links and Checkout Sessions. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_payment_link_limits")

API = "https://api.stripe.com/v1"

NEAR = 0.9  # far enough along the cap that it will be met before anyone looks again


def verdict(restrictions, recent_sessions=0):
    """Classify one Payment Link's completion cap. Pure, so it is testable offline.

    `restrictions` is the link's restrictions object, which is None on most links.
    `recent_sessions` is the number of Checkout Sessions it created in the window,
    which separates a dead link nobody visits from one that is turning people away.
    Returns (state, detail).
    """
    completed = ((restrictions or {}).get("completed_sessions") or {})
    limit = completed.get("limit")
    count = completed.get("count")
    if limit is None:
        return ("uncapped", "no completion limit set")
    if count is None:
        return ("unknown",
                "capped at %s and the counter is missing from the response; treat "
                "it as unread rather than as zero" % limit)
    if count >= limit:
        if recent_sessions:
            return ("exhausted-in-use",
                    "%d of %d completed session(s): the cap is met and %d "
                    "customer(s) have still arrived since"
                    % (count, limit, recent_sessions))
        return ("exhausted",
                "%d of %d completed session(s): the cap is met and the link no "
                "longer accepts completions" % (count, limit))
    if limit and count / float(limit) >= NEAR:
        return ("near-limit",
                "%d of %d completed session(s): this link closes itself within "
                "days at the current rate" % (count, limit))
    return ("headroom", "%d of %d completed session(s)" % (count, limit))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def payment_links(session, cap):
    """Every Payment Link on the account, capped and not."""
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/payment_links", params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def recent_session_count(session, link_id, since):
    """Sessions this link created since `since`, whatever their status.

    An exhausted link still creates sessions; they just cannot complete. Counting
    them is how you find out whether the published URL is still in circulation.
    """
    count = 0
    params = {"payment_link": link_id, "limit": 100}
    while True:
        page = get(session, "/checkout/sessions", params)
        data = page.get("data", [])
        for cs in data:
            if (cs.get("created") or 0) >= since:
                count += 1
        if not data or not page.get("has_more"):
            break
        if (data[-1].get("created") or 0) < since:
            break
        params["starting_after"] = data[-1]["id"]
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back a session still counts as recent traffic")
    ap.add_argument("--max-links", type=int, default=500,
                    help="stop paginating after this many Payment Links")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    bad = 0
    for link in payment_links(s, args.max_links):
        restrictions = link.get("restrictions")
        # Only capped links are worth a second request, and most links are not.
        recent = 0
        if restrictions:
            recent = recent_session_count(s, link["id"], since)
        state, detail = verdict(restrictions, recent)
        line = "%-17s %-20s %s" % (state, link["id"], detail)
        if state in ("uncapped", "headroom"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  published at: %s", link.get("url") or "<no url>")
        log.warning("  repair: raise the cap and keep the same URL:")
        log.warning("  POST %s/payment_links/%s -d "
                    "\\"restrictions[completed_sessions][limit]=<higher>\\"",
                    API, link["id"])
        log.warning("  or create a fresh link for the next tranche and swap the "
                    "published URL everywhere it appears")

    log.info("%d capped link(s) at or near their completion limit", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-payment-link-limits.mjs",
"js": '''/**
 * Report Stripe Payment Links that have reached their completed-session limit.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read access
 * to Payment Links and Checkout Sessions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const NEAR = 0.9; // far enough along the cap that it closes before anyone looks again

/**
 * Classify one Payment Link's completion cap. Pure, so it is testable offline.
 * A missing counter is unread, not zero.
 */
export function verdict(restrictions, recentSessions = 0) {
  const completed = (restrictions ?? {}).completed_sessions ?? {};
  const limit = completed.limit;
  const count = completed.count;
  if (limit === null || limit === undefined) {
    return ['uncapped', 'no completion limit set'];
  }
  if (count === null || count === undefined) {
    return ['unknown',
      `capped at ${limit} and the counter is missing from the response; treat it ` +
      'as unread rather than as zero'];
  }
  if (count >= limit) {
    if (recentSessions) {
      return ['exhausted-in-use',
        `${count} of ${limit} completed session(s): the cap is met and ` +
        `${recentSessions} customer(s) have still arrived since`];
    }
    return ['exhausted',
      `${count} of ${limit} completed session(s): the cap is met and the link no ` +
      'longer accepts completions'];
  }
  if (limit && count / limit >= NEAR) {
    return ['near-limit',
      `${count} of ${limit} completed session(s): this link closes itself within ` +
      'days at the current rate'];
  }
  return ['headroom', `${count} of ${limit} completed session(s)`];
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

export async function paymentLinks(key, cap = 500) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/payment_links', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= cap) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

export async function recentSessionCount(key, linkId, since) {
  let count = 0;
  const params = { payment_link: linkId, limit: 100 };
  for (;;) {
    const page = await get(key, '/checkout/sessions', params);
    const data = page.data ?? [];
    for (const cs of data) if ((cs.created ?? 0) >= since) count += 1;
    if (data.length === 0 || !page.has_more) break;
    if ((data[data.length - 1].created ?? 0) < since) break;
    params.starting_after = data[data.length - 1].id;
  }
  return count;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.argv[2] ?? 30);
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  let bad = 0;
  for (const link of await paymentLinks(key)) {
    const restrictions = link.restrictions;
    const recent = restrictions ? await recentSessionCount(key, link.id, since) : 0;
    const [state, detail] = verdict(restrictions, recent);
    const line = `${state.padEnd(17)} ${link.id.padEnd(20)} ${detail}`;
    if (state === 'uncapped' || state === 'headroom') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  published at: ${link.url ?? '<no url>'}`);
    console.warn('  repair: raise the cap and keep the same URL:');
    console.warn(`  POST ${API}/payment_links/${link.id} -d ` +
                 '"restrictions[completed_sessions][limit]=<higher>"');
    console.warn('  or create a fresh link for the next tranche and swap the ' +
                 'published URL everywhere it appears');
  }

  console.log(`${bad} capped link(s) at or near their completion limit`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that earns its place is the missing counter. <code>restrictions.completed_sessions.count</code> absent is not the same as zero, and a classifier that treats it as zero reports a link with full headroom on the one link it could not actually read. The near-limit test is the other one: it is the only state where this problem is still cheap to fix.",
"test_py_file": "test_stripe_payment_link_limits.py",
"test_py": '''from stripe_payment_link_limits import verdict


def test_a_link_with_no_restrictions_is_uncapped():
    assert verdict(None)[0] == "uncapped"
    assert verdict({})[0] == "uncapped"


def test_a_link_well_inside_its_cap_has_headroom():
    state, detail = verdict({"completed_sessions": {"limit": 200, "count": 42}})
    assert state == "headroom"
    assert "42 of 200" in detail


def test_a_link_at_ninety_percent_is_the_one_worth_catching():
    state, detail = verdict({"completed_sessions": {"limit": 100, "count": 92}})
    assert state == "near-limit"
    assert "closes itself" in detail


def test_an_exhausted_link_with_no_traffic_is_only_housekeeping():
    assert verdict({"completed_sessions": {"limit": 50, "count": 50}})[0] == "exhausted"


def test_an_exhausted_link_still_being_clicked_is_lost_revenue():
    state, detail = verdict({"completed_sessions": {"limit": 50, "count": 50}}, 18)
    assert state == "exhausted-in-use"
    assert "18 customer(s)" in detail


def test_a_missing_counter_is_not_read_as_zero():
    # Reading absent as zero would report full headroom on the one link the
    # response did not describe.
    assert verdict({"completed_sessions": {"limit": 50}})[0] == "unknown"
''',
"test_js_file": "stripe-payment-link-limits.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-payment-link-limits.mjs';

test('a link with no restrictions is uncapped', () => {
  assert.equal(verdict(null)[0], 'uncapped');
  assert.equal(verdict({})[0], 'uncapped');
});

test('a link well inside its cap has headroom', () => {
  const [state, detail] = verdict({ completed_sessions: { limit: 200, count: 42 } });
  assert.equal(state, 'headroom');
  assert.match(detail, /42 of 200/);
});

test('a link at ninety percent is the one worth catching', () => {
  const [state, detail] = verdict({ completed_sessions: { limit: 100, count: 92 } });
  assert.equal(state, 'near-limit');
  assert.match(detail, /closes itself/);
});

test('an exhausted link with no traffic is only housekeeping', () => {
  const r = { completed_sessions: { limit: 50, count: 50 } };
  assert.equal(verdict(r)[0], 'exhausted');
});

test('an exhausted link still being clicked is lost revenue', () => {
  const r = { completed_sessions: { limit: 50, count: 50 } };
  const [state, detail] = verdict(r, 18);
  assert.equal(state, 'exhausted-in-use');
  assert.match(detail, /18 customer/);
});

test('a missing counter is not read as zero', () => {
  assert.equal(verdict({ completed_sessions: { limit: 50 } })[0], 'unknown');
});
''',
"faq": [
 ("What does a customer see on a link that has met its limit?",
  "A Stripe-hosted page saying the link is no longer available, not an error. The URL still resolves with a 200, so uptime checks and link checkers report it as healthy, exactly as they do for a deactivated link."),
 ("Is this the same as deactivating the link?",
  "No, and the fields differ. A deactivated link has active false because somebody switched it off. An exhausted link is still active true; what changed is restrictions.completed_sessions.count reaching the limit. A script that only looks at active will miss this entirely."),
 ("Can I reset the completed-sessions counter?",
  "No. The counter is read-only and maintained by Stripe. You can raise the limit above the current count, which reopens the link with its existing URL, or create a new link if you want the count to start again from zero."),
 ("Does the limit count sessions created or sessions completed?",
  "Completed ones. Sessions that are opened and abandoned do not consume the cap, which is why a link can show far more traffic than its counter and why the session count and the counter are two different numbers worth reading side by side."),
 ("Will Stripe warn me before the limit is reached?",
  "No. There is no event and no notification as the counter approaches the cap or when it meets it. Polling the object is the only way to see it coming, which is what makes the ninety-percent check the useful half of this script."),
],
"related": [
 ("/stripe/payment-link-inactive-still-published/", "A deactivated Payment Link is still linked from your site"),
 ("/stripe/payment-link-hosted-confirmation-no-fulfilment/", "Payment Link ends on Stripe's page, so fulfilment never fires"),
 ("/stripe/checkout-expired-session-share/", "Most Checkout Sessions expire unpaid and nobody is told"),
],
"citations": [CITE_LINK_OBJ, CITE_LINK_CREATE, CITE_LINK_UPDATE, CITE_LINKS],
},

{
"slug": "billing-portal-cancel-disabled",
"title": "Billing Portal can't cancel, so customers charge back instead",
"description": "Customers who want out email support, wait, and then dispute the charge. The portal exists; the cancellation feature on it was never switched on.",
"h1": "billing portal can't cancel, so customers charge back instead",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe billing portal cancel disabled",
             "subscription_cancel enabled false", "stripe subscription_canceled dispute",
             "stripe portal cancellation", "stripe self serve cancel"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Your dispute rate is drifting up and the reasons cluster on one code: <code>subscription_canceled</code>. These are not fraudsters. They are customers who wanted to stop paying, could not find a way to do it, emailed support, waited, and then used the one cancellation mechanism that always works &mdash; their bank.",
"short_answer": """<p>Read <code>GET /v1/billing_portal/configurations?limit=100</code> and check <code>features.subscription_cancel.enabled</code> on the default configuration. It defaults to <code>false</code>, so a portal created without asking for it has no cancel button. Check <code>features.payment_method_update.enabled</code> at the same time, for the same reason.</p>
<p>Then price it: <code>GET /v1/disputes?created[gte]=&lt;now-180d&gt;</code> and count <code>reason == "subscription_canceled"</code> as a share of all disputes. That share is what the missing button costs, in money and in dispute rate.</p>""",
"problem": """<p>This is the rare integration problem where the failure is not an error anywhere. The portal works. Customers open it, see their invoices, update their address, and find no way to leave. Every API call returns 200. The only trace is downstream, in a dispute reason code that nobody maps back to a feature flag.</p>
<p>It is distinct from having no portal at all, which is the <a href="/stripe/billing-portal-no-configuration/">portal sessions 400</a> case: that one throws, gets noticed, and gets fixed within a day. This one never throws. It quietly converts a customer who was leaving anyway into a chargeback, and chargebacks count against you in a way that voluntary cancellations never do.</p>""",
"why": """<p><strong>The feature defaults to off.</strong> <code>features.subscription_cancel.enabled</code> is <code>false</code> unless somebody explicitly turned it on, in the Dashboard or in the create call. Nobody notices an absent button while building the portal, because the person building it is not trying to cancel anything.</p>
<p><strong>Turning it off feels like retention.</strong> Making cancellation hard is a strategy some teams choose on purpose. It works, in the sense that fewer people cancel through the portal. It does not work in the sense that matters: the customer still stops paying, only now it happens through a dispute that costs a fee, counts toward your dispute rate, and cannot be won.</p>
<p><strong>A dispute is not a refund.</strong> Stripe's own dispute-prevention guidance says an in-app cancellation button is often the best solution because it does not require the cardholder to wait. Waiting is what turns an ordinary cancellation into a chargeback, and a chargeback is a fee plus a mark against the account, permanently.</p>
<p><strong>Card update matters for the same reason.</strong> If <code>payment_method_update</code> is off too, a customer whose card expired cannot fix it and cannot leave. Both roads lead to support, and one of them leads to the bank.</p>""",
"steps": [
 {"h": "Find the configuration your code actually uses",
  "body": """<p><code>GET /v1/billing_portal/configurations?limit=100</code>. If your session-create call passes an explicit <code>configuration</code>, check that one; if it does not, the one that matters is the one with <code>is_default == true</code> and <code>active == true</code>. If there is no configuration at all, that is a different note and a louder failure.</p>"""},
 {"h": "Read features.subscription_cancel.enabled",
  "body": """<p><code>false</code> is the finding. While you are there, read <code>mode</code> and <code>cancellation_reason</code>: <code>at_period_end</code> keeps the service running to the end of the paid period, and the reason prompt is the only structured churn data you will ever get for free.</p>"""},
 {"h": "Read features.payment_method_update.enabled too",
  "body": """<p>A portal that can cancel but cannot update a card sends every expired-card customer to support anyway. The two features fail into the same queue and it is worth fixing them in the same change.</p>"""},
 {"h": "Count the disputes that name it",
  "body": """<p><code>GET /v1/disputes?created[gte]=&lt;now-180d&gt;&amp;limit=100</code>, paginated. Count <code>reason == "subscription_canceled"</code> against the total. A material share is the direct cost of the missing button, and it is the number that gets the change approved.</p>"""},
 {"h": "Turn cancellation on, and collect the reason",
  "body": """<p>Enable <code>subscription_cancel</code> with <code>mode=at_period_end</code>, enable the cancellation reason prompt, and enable <code>payment_method_update</code>. You lose the customers you were going to lose anyway, and you keep the fee, the dispute rate and the explanation of why they left.</p>"""},
],
"verify": """<p>Re-run the script. The configuration your code uses should report cancellation available, and the dispute share should fall over the following months.</p>
<pre><code class="language-bash">python3 stripe_portal_cancel_disabled.py --days 180
# self-serve       bpc_1MrTdC: cancel at_period_end, card update on</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to the Customer Portal and Disputes is enough. The classifier is pure and takes one configuration object plus two dispute counts, because the same disabled flag is a design opinion on an account with no disputes and a measurable bill on one with a wall of <code>subscription_canceled</code>.",
"py_file": "stripe_portal_cancel_disabled.py",
"py": '''"""Report a Stripe Billing Portal configuration with cancellation switched off.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access to
the Customer Portal and Disputes. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_portal_cancel_disabled")

API = "https://api.stripe.com/v1"


def verdict(configuration, cancel_disputes=0, total_disputes=0):
    """Classify one portal configuration. Pure, so it is testable offline.

    `cancel_disputes` is the number of disputes in the window with reason
    subscription_canceled and `total_disputes` every dispute in the same window.
    Returns (state, detail).
    """
    features = ((configuration or {}).get("features") or {})
    cancel = features.get("subscription_cancel") or {}
    update = features.get("payment_method_update") or {}
    config_id = (configuration or {}).get("id", "<no id>")

    enabled = cancel.get("enabled")
    if enabled is None:
        return ("unknown",
                "%s does not report features.subscription_cancel.enabled; read the "
                "configuration rather than assuming either way" % config_id)
    if not enabled:
        if cancel_disputes:
            share = 100.0 * cancel_disputes / total_disputes if total_disputes else 0.0
            return ("cancel-off-disputed",
                    "%s has no cancel button, and %d of %d dispute(s) in the window "
                    "(%.1f%%) are subscription_canceled"
                    % (config_id, cancel_disputes, total_disputes, share))
        return ("cancel-off",
                "%s has no cancel button: the fastest exit a customer has is their "
                "bank" % config_id)
    if not update.get("enabled"):
        return ("update-off",
                "%s can cancel but cannot update a card, so an expired card still "
                "goes to support" % config_id)
    if not (cancel.get("cancellation_reason") or {}).get("enabled"):
        return ("no-reason",
                "%s cancels at %s and collects no cancellation reason: the churn "
                "data is free and is being discarded"
                % (config_id, cancel.get("mode") or "an unspecified point"))
    return ("self-serve",
            "%s: cancel %s, card update on" % (config_id, cancel.get("mode") or "on"))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def configurations(session):
    """Every portal configuration in whichever mode the key is for."""
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/billing_portal/configurations", params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more"):
            break
        params["starting_after"] = data[-1]["id"]
    return out


def dispute_counts(session, since, cap):
    """(disputes citing a cancelled subscription, all disputes) since `since`."""
    cancel = total = 0
    params = {"created[gte]": since, "limit": 100}
    while True:
        page = get(session, "/disputes", params)
        data = page.get("data", [])
        for d in data:
            total += 1
            if d.get("reason") == "subscription_canceled":
                cancel += 1
        if not data or not page.get("has_more") or total >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return cancel, total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=180,
                    help="dispute window to price the missing button over")
    ap.add_argument("--max-disputes", type=int, default=2000,
                    help="stop paginating after this many disputes")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    configs = configurations(s)
    if not configs:
        log.warning("no portal configuration exists at all, which is a louder "
                    "failure: every portal session create returns 400")
        return 1

    since = int(time.time()) - args.days * 86400
    cancel_disputes, total_disputes = dispute_counts(s, since, args.max_disputes)

    bad = 0
    for config in configs:
        if not config.get("active"):
            continue
        state, detail = verdict(config, cancel_disputes, total_disputes)
        line = "%-20s %s" % (state, detail)
        if state == "self-serve":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("cancel-off", "cancel-off-disputed", "unknown"):
            log.warning("  repair: POST %s/billing_portal/configurations/%s "
                        "-d \\"features[subscription_cancel][enabled]=true\\" "
                        "-d \\"features[subscription_cancel][mode]=at_period_end\\" "
                        "-d \\"features[subscription_cancel]"
                        "[cancellation_reason][enabled]=true\\"",
                        API, config.get("id"))
        if state in ("update-off", "cancel-off", "cancel-off-disputed"):
            log.warning("  and: POST %s/billing_portal/configurations/%s "
                        "-d \\"features[payment_method_update][enabled]=true\\"",
                        API, config.get("id"))

    log.info("%d active configuration(s), %d needing attention", len(configs), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-portal-cancel-disabled.mjs",
"js": '''/**
 * Report a Stripe Billing Portal configuration with cancellation switched off.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read access
 * to the Customer Portal and Disputes. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one portal configuration. Pure, so it is testable offline.
 * A missing enabled flag is unknown, not false.
 */
export function verdict(configuration, cancelDisputes = 0, totalDisputes = 0) {
  const features = (configuration ?? {}).features ?? {};
  const cancel = features.subscription_cancel ?? {};
  const update = features.payment_method_update ?? {};
  const id = (configuration ?? {}).id ?? '<no id>';

  const enabled = cancel.enabled;
  if (enabled === null || enabled === undefined) {
    return ['unknown',
      `${id} does not report features.subscription_cancel.enabled; read the ` +
      'configuration rather than assuming either way'];
  }
  if (!enabled) {
    if (cancelDisputes) {
      const share = totalDisputes ? (100 * cancelDisputes / totalDisputes) : 0;
      return ['cancel-off-disputed',
        `${id} has no cancel button, and ${cancelDisputes} of ${totalDisputes} ` +
        `dispute(s) in the window (${share.toFixed(1)}%) are subscription_canceled`];
    }
    return ['cancel-off',
      `${id} has no cancel button: the fastest exit a customer has is their bank`];
  }
  if (!update.enabled) {
    return ['update-off',
      `${id} can cancel but cannot update a card, so an expired card still goes ` +
      'to support'];
  }
  if (!(cancel.cancellation_reason ?? {}).enabled) {
    return ['no-reason',
      `${id} cancels at ${cancel.mode ?? 'an unspecified point'} and collects no ` +
      'cancellation reason: the churn data is free and is being discarded'];
  }
  return ['self-serve', `${id}: cancel ${cancel.mode ?? 'on'}, card update on`];
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

export async function configurations(key) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/billing_portal/configurations', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

export async function disputeCounts(key, since, cap = 2000) {
  let cancel = 0; let total = 0;
  const params = { 'created[gte]': since, limit: 100 };
  for (;;) {
    const page = await get(key, '/disputes', params);
    const data = page.data ?? [];
    for (const d of data) {
      total += 1;
      if (d.reason === 'subscription_canceled') cancel += 1;
    }
    if (data.length === 0 || !page.has_more || total >= cap) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { cancel, total };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const configs = await configurations(key);
  if (configs.length === 0) {
    console.warn('no portal configuration exists at all, which is a louder ' +
                 'failure: every portal session create returns 400');
    process.exitCode = 1;
    return;
  }

  const days = Number(process.argv[2] ?? 180);
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  const { cancel, total } = await disputeCounts(key, since);

  let bad = 0;
  for (const config of configs) {
    if (!config.active) continue;
    const [state, detail] = verdict(config, cancel, total);
    const line = `${state.padEnd(20)} ${detail}`;
    if (state === 'self-serve') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'cancel-off' || state === 'cancel-off-disputed' || state === 'unknown') {
      console.warn(`  repair: POST ${API}/billing_portal/configurations/${config.id} ` +
                   '-d "features[subscription_cancel][enabled]=true" ' +
                   '-d "features[subscription_cancel][mode]=at_period_end" ' +
                   '-d "features[subscription_cancel][cancellation_reason][enabled]=true"');
    }
    if (state === 'update-off' || state === 'cancel-off' || state === 'cancel-off-disputed') {
      console.warn(`  and: POST ${API}/billing_portal/configurations/${config.id} ` +
                   '-d "features[payment_method_update][enabled]=true"');
    }
  }

  console.log(`${configs.length} active configuration(s), ${bad} needing attention`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The split worth pinning is between a portal with no cancel button on an account with no disputes and the same portal on an account where a sixth of the disputes say <code>subscription_canceled</code>. Identical configuration, and only one of them has a number attached. The last test is the usual one: a missing <code>enabled</code> flag is something you did not read, not something you know is off.",
"test_py_file": "test_stripe_portal_cancel_disabled.py",
"test_py": '''from stripe_portal_cancel_disabled import verdict

FULL = {"id": "bpc_1", "features": {
    "subscription_cancel": {"enabled": True, "mode": "at_period_end",
                            "cancellation_reason": {"enabled": True}},
    "payment_method_update": {"enabled": True}}}
NO_CANCEL = {"id": "bpc_2", "features": {
    "subscription_cancel": {"enabled": False},
    "payment_method_update": {"enabled": True}}}


def test_a_portal_that_cancels_and_asks_why_is_done():
    state, detail = verdict(FULL, 0, 40)
    assert state == "self-serve"
    assert "at_period_end" in detail


def test_cancellation_off_with_no_disputes_is_still_the_finding():
    state, detail = verdict(NO_CANCEL, 0, 0)
    assert state == "cancel-off"
    assert "their bank" in detail


def test_cancellation_off_with_disputes_naming_it_is_priced():
    state, detail = verdict(NO_CANCEL, 7, 42)
    assert state == "cancel-off-disputed"
    assert "16.7%" in detail


def test_cancel_on_but_card_update_off_still_sends_people_to_support():
    config = {"id": "bpc_3", "features": {
        "subscription_cancel": {"enabled": True, "mode": "immediately",
                                "cancellation_reason": {"enabled": True}},
        "payment_method_update": {"enabled": False}}}
    assert verdict(config)[0] == "update-off"


def test_cancelling_without_asking_why_throws_away_the_churn_data():
    config = {"id": "bpc_4", "features": {
        "subscription_cancel": {"enabled": True, "mode": "at_period_end"},
        "payment_method_update": {"enabled": True}}}
    state, detail = verdict(config)
    assert state == "no-reason"
    assert "at_period_end" in detail


def test_a_missing_enabled_flag_is_not_read_as_off():
    # Reporting a cancel button as missing on a portal that has one sends somebody
    # to fix a configuration that is already correct.
    assert verdict({"id": "bpc_5", "features": {"subscription_cancel": {}}})[0] == "unknown"
    assert verdict(None)[0] == "unknown"
''',
"test_js_file": "stripe-portal-cancel-disabled.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-portal-cancel-disabled.mjs';

const FULL = { id: 'bpc_1', features: {
  subscription_cancel: { enabled: true, mode: 'at_period_end',
                         cancellation_reason: { enabled: true } },
  payment_method_update: { enabled: true } } };
const NO_CANCEL = { id: 'bpc_2', features: {
  subscription_cancel: { enabled: false },
  payment_method_update: { enabled: true } } };

test('a portal that cancels and asks why is done', () => {
  const [state, detail] = verdict(FULL, 0, 40);
  assert.equal(state, 'self-serve');
  assert.match(detail, /at_period_end/);
});

test('cancellation off with no disputes is still the finding', () => {
  const [state, detail] = verdict(NO_CANCEL, 0, 0);
  assert.equal(state, 'cancel-off');
  assert.match(detail, /their bank/);
});

test('cancellation off with disputes naming it is priced', () => {
  const [state, detail] = verdict(NO_CANCEL, 7, 42);
  assert.equal(state, 'cancel-off-disputed');
  assert.match(detail, /16\\.7%/);
});

test('cancel on but card update off still sends people to support', () => {
  const config = { id: 'bpc_3', features: {
    subscription_cancel: { enabled: true, mode: 'immediately',
                           cancellation_reason: { enabled: true } },
    payment_method_update: { enabled: false } } };
  assert.equal(verdict(config)[0], 'update-off');
});

test('cancelling without asking why throws away the churn data', () => {
  const config = { id: 'bpc_4', features: {
    subscription_cancel: { enabled: true, mode: 'at_period_end' },
    payment_method_update: { enabled: true } } };
  const [state, detail] = verdict(config);
  assert.equal(state, 'no-reason');
  assert.match(detail, /at_period_end/);
});

test('a missing enabled flag is not read as off', () => {
  assert.equal(verdict({ id: 'bpc_5', features: { subscription_cancel: {} } })[0],
               'unknown');
  assert.equal(verdict(null)[0], 'unknown');
});
''',
"faq": [
 ("Does letting customers cancel themselves increase churn?",
  "It increases visible cancellations and reduces disputes. The customer who wanted to leave leaves either way; the only variable is whether that exit costs you a dispute fee and a mark on your dispute rate, or a row in a churn report with a reason attached."),
 ("What is the subscription_canceled dispute reason?",
  "It is the reason a cardholder gives when they say they cancelled and were charged anyway, or could not cancel. A cluster of them is the clearest evidence that the exit path in your product does not work, whether that is a missing portal button or a support queue people gave up on."),
 ("Should cancellation take effect immediately or at period end?",
  "at_period_end is the usual choice: the customer keeps what they paid for, you keep the revenue for the current period, and there is no partial-refund argument. Immediate cancellation is right when the service is metered or when access itself is the thing being disputed."),
 ("Why does the script check payment_method_update as well?",
  "Because it fails into the same queue. A customer whose card expired cannot pay and cannot leave, so they contact support for one of two reasons and get the same wait either way. The two flags are almost always turned on in the same change."),
 ("What if my code passes an explicit configuration id?",
  "Then check that configuration rather than the default. The script classifies every active configuration on the account for exactly this reason: an account can have a perfectly configured default and pass the id of an older one that has cancellation switched off."),
],
"related": [
 ("/stripe/billing-portal-no-configuration/", "No Billing Portal configuration, so portal sessions 400"),
 ("/stripe/cancel-at-period-end-churn-backlog/", "A wall of cancel_at_period_end subscriptions nobody noticed"),
 ("/stripe/dispute-rate-above-threshold/", "Dispute activity is above the 0.75% excessive threshold"),
],
"citations": [CITE_PORTAL_CONFIG_OBJ, CITE_PORTAL_CONFIG_UPDATE, CITE_PORTAL_ACTIVATE,
              CITE_MONITORING],
},

]
