#!/usr/bin/env python3
"""/stripe/ field notes — batch AB: Connect scope, deadlines and frozen destinations.

Five problems where the account looks healthy from the platform's side and the
thing that broke is off the edge of what anyone is querying: a webhook
destination whose scope the API will not tell you, a deadline nobody turned into
a calendar, a bank account Stripe has stopped trying, a pause the platform
applied to itself, and a cardholder that keeps every card it owns inactive.

Every script here is read only. They hold a credential to a live payments
account, so none of them writes: they read, they say exactly what is wrong, and
they print the repair for a human to run.
"""

CITE_CONNECT_WEBHOOKS = ("Connect webhooks — Stripe Docs",
                         "https://docs.stripe.com/connect/webhooks")
CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")
CITE_WEBHOOK_CREATE = ("Create a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/create")
CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")
CITE_ACCOUNT_OBJECT = ("The Account object — Stripe API reference",
                       "https://docs.stripe.com/api/accounts/object")
CITE_ACCOUNT_LIST = ("List all connected accounts — Stripe API reference",
                     "https://docs.stripe.com/api/accounts/list")
CITE_VERIFICATION = ("Handling verification with the API — Stripe Docs",
                     "https://docs.stripe.com/connect/handling-api-verification")
CITE_HOSTED_ONBOARDING = ("Hosted onboarding — Stripe Docs",
                          "https://docs.stripe.com/connect/hosted-onboarding")
CITE_ACCOUNT_LINKS = ("Create an account link — Stripe API reference",
                      "https://docs.stripe.com/api/account_links/create")
CITE_EXTERNAL_ACCOUNT = ("The bank account object — Stripe API reference",
                         "https://docs.stripe.com/api/external_account_bank_accounts/object")
CITE_PAYOUT_OBJECT = ("The Payout object — Stripe API reference",
                      "https://docs.stripe.com/api/payouts/object")
CITE_PAYOUTS_CONNECT = ("Payouts to connected accounts — Stripe Docs",
                        "https://docs.stripe.com/connect/payouts-connected-accounts")
CITE_PAUSING = ("Pausing payments or payouts on connected accounts — Stripe Docs",
                "https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts")
CITE_CARDHOLDER_OBJECT = ("The Cardholder object — Stripe API reference",
                          "https://docs.stripe.com/api/issuing/cardholders/object")
CITE_CARD_OBJECT = ("The Card object — Stripe API reference",
                    "https://docs.stripe.com/api/issuing/cards/object")
CITE_AUTHORIZATION_OBJECT = ("The Authorization object — Stripe API reference",
                             "https://docs.stripe.com/api/issuing/authorizations/object")
CITE_ISSUING_CARDS = ("Issuing cards — Stripe Docs", "https://docs.stripe.com/issuing/cards")

GUIDES = [

{
"slug": "connect-platform-missing-account-updated",
"title": "A Connect platform has no endpoint for connected accounts",
"description": "Events about your sellers go to a destination nobody created. The endpoint object never returns its scope, so the gap has to be inferred.",
"h1": "a Connect platform has no endpoint for connected accounts",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe connect webhook", "account.updated never fires",
             "connect=true webhook endpoint", "stripe connected account events",
             "account.application.deauthorized"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The endpoint is enabled. It is subscribed to <code>account.updated</code>. It has been in the dashboard for two years and it delivers thousands of events a week without a single failure. And it has never once received an event about a connected account, because the thing that decides whether it does is not in <code>enabled_events</code> and is not returned on the object you are looking at.",
"short_answer": """<p>A Connect-scoped destination is a <em>different object</em> from an account-scoped one. Events raised by a connected account carry a top-level <code>account</code> property and are delivered only to an endpoint created with <code>connect=true</code> (in Workbench: an event destination listening to <strong>Connected accounts</strong>). Subscribing an ordinary endpoint to <code>account.updated</code> does not make it receive them.</p>
<p>The catch when you go to check: the endpoint object does not return the <code>connect</code> flag. Only <code>application</code>, <code>status</code>, <code>url</code> and <code>enabled_events</code> come back. So the read-only check is a proxy &mdash; confirm the account is a platform with <code>GET /v1/accounts?limit=1</code>, then look for any enabled endpoint subscribed to <code>account.updated</code> or <code>account.application.deauthorized</code>. Absence is proof of a gap. Presence is only evidence of intent.</p>""",
"problem": """<p>What this looks like day to day is a platform whose picture of its sellers is frozen at the moment each one finished onboarding. A seller's verification lapses and <code>charges_enabled</code> goes false; your database still says active, your UI still shows them live, and their customers hit a checkout that errors. A seller disconnects the platform from their own Stripe dashboard; you keep listing them, keep routing payments at them, keep counting them in the seller total.</p>
<p>The reason it survives so long is that nothing looks broken. Your platform's own events &mdash; charges, payouts, subscriptions on your account &mdash; arrive perfectly. The delivery success rate on the endpoint is 100%, because Stripe is not attempting the deliveries you are missing. There is no failed delivery to find, no retry to inspect, no error rate to alert on. The events simply were never addressed to you.</p>""",
"why": """<p><strong>The scope is set once, at creation, and is invisible afterwards.</strong> <code>connect=true</code> is a creation parameter. It is not returned when you list endpoints and there is no field on the object that reflects it, so no amount of reading <code>GET /v1/webhook_endpoints</code> will tell you directly whether your Connect events have a home. This is the whole reason the check has to be indirect.</p>
<p><strong><code>enabled_events</code> accepts the subscription either way.</strong> You can subscribe an account-scoped endpoint to <code>account.updated</code> and Stripe accepts it without complaint &mdash; it is a legitimate subscription, since your own account can be updated too. The list looks right. It just never fills with connected-account traffic.</p>
<p><strong>Nothing ever errors.</strong> Undelivered events, disabled endpoints and signature failures all leave a trace somewhere. An event with no matching destination leaves none. There is no counter of events you were not sent.</p>
<p><strong>The two events fail differently, so half a subscription is its own bug.</strong> <code>account.updated</code> carries verification and capability changes. <code>account.application.deauthorized</code> is the only signal that a seller has disconnected. A platform with the first and not the second sees every requirement problem and none of the departures, which is how a disconnected seller stays in the active list for a year.</p>""",
"steps": [
 {"h": "Establish that this check applies at all",
  "body": """<p><code>GET /v1/accounts?limit=1</code>. If it comes back empty, this is not a platform and there is nothing to scope. Running the Connect coverage check against a plain account produces a permanent warning that everybody learns to ignore, which then hides the day it becomes true.</p>"""},
 {"h": "Union the subscriptions across enabled endpoints only",
  "body": """<p>A disabled endpoint delivers nothing, so a disabled endpoint holding the only <code>account.updated</code> subscription is the same as not having one. Count them separately and mention them, because "we do have that endpoint" is the first thing anyone will say.</p>"""},
 {"h": "Treat a wildcard as unknown, not as covered",
  "body": """<p>An endpoint subscribed to <code>*</code> would receive connected-account events <em>if</em> it were Connect scoped, and the API will not say whether it is. That is genuinely inconclusive and should be reported as such rather than being counted either way. Open the destination in Workbench and read whether it listens to your account or to connected accounts.</p>"""},
 {"h": "Check both modes, and remember the events are the same either way",
  "body": """<p>Test-mode and live-mode endpoints are separate objects. A team that built Connect handling against a test-mode Connect destination and then created the live endpoint through a different route ends up with exactly the asymmetry this check finds.</p>"""},
 {"h": "Create the destination and handle event.account",
  "body": """<p>The new endpoint needs <code>connect=true</code> and a handler that reads the top-level <code>account</code> property, because an incoming <code>account.updated</code> now tells you <em>which</em> seller changed. Any API call you make in response has to be made as that account, with the <code>Stripe-Account</code> header.</p>"""},
],
"verify": """<p>Re-run the script. A platform should report <code>covered</code>, and the state should stay covered after the next endpoint is added.</p>
<pre><code class="language-bash">python3 stripe_connect_webhook_scope.py
# 3 endpoint(s), platform with connected accounts: covered</code></pre>""",
"code_intro": "Two GET requests: one page of accounts to establish the account is a platform, and the list of webhook endpoints. The classifier is pure and, more importantly, honest &mdash; it returns <code>inconclusive</code> when the API genuinely cannot answer, because a check that guesses in that case is worse than one that says so.",
"py_file": "stripe_connect_webhook_scope.py",
"py": '''"""Report a Connect platform with no webhook destination scoped to its accounts.

Read only. Two GET requests and no writes: give this a RESTRICTED key with read
access to Webhook Endpoints and Connected accounts. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_connect_webhook_scope")

API = "https://api.stripe.com/v1"

# The two events that only ever come from a connected account. The endpoint
# object does not return whether it was created with connect=true, so a
# subscription to one of these is the closest thing to evidence the API offers:
# their absence proves a gap, their presence only shows somebody meant to.
CONNECT_SIGNALS = ("account.updated", "account.application.deauthorized")


def coverage(endpoints, is_platform):
    """Decide whether connected-account events have anywhere to go. Pure.

    Takes the raw /v1/webhook_endpoints list and whether this account has any
    connected accounts. Returns (state, detail). `inconclusive` is a real answer
    here and not a failure of the check: a wildcard endpoint would receive these
    events if it were Connect scoped, and nothing in the API says whether it is.
    """
    if not is_platform:
        return ("not-a-platform",
                "no connected accounts on this key, so there is no Connect traffic "
                "to scope a destination for")

    enabled = [e for e in endpoints if e.get("status") == "enabled"]
    disabled = len(endpoints) - len(enabled)

    if not enabled:
        return ("no-endpoints",
                "no enabled endpoint in this mode at all (%d disabled): nothing is "
                "being delivered anywhere, connected or otherwise" % disabled)

    subscribed = set()
    wildcards = []
    for e in enabled:
        types = e.get("enabled_events") or []
        if "*" in types:
            wildcards.append(e.get("url") or e.get("id") or "?")
        subscribed.update(types)

    have = [s for s in CONNECT_SIGNALS if s in subscribed]

    if len(have) == len(CONNECT_SIGNALS):
        return ("covered",
                "an enabled endpoint subscribes to %s" % " and ".join(CONNECT_SIGNALS))

    if wildcards and not have:
        return ("inconclusive",
                "%d endpoint(s) subscribe to * and the endpoint object never returns "
                "whether they are Connect scoped: open %s in Workbench and read "
                "whether it listens to your account or to connected accounts"
                % (len(wildcards), wildcards[0]))

    if have:
        missing = [s for s in CONNECT_SIGNALS if s not in subscribed]
        return ("thin",
                "%s is subscribed but %s is not: %s"
                % (have[0], missing[0],
                   "sellers who disconnect keep looking active"
                   if missing[0] == "account.application.deauthorized"
                   else "you see the departures and none of the verification failures"))

    tail = ", and %d disabled endpoint(s) were ignored" % disabled if disabled else ""
    return ("uncovered",
            "no enabled endpoint subscribes to %s%s"
            % (" or ".join(CONNECT_SIGNALS), tail))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def endpoints(session):
    """Return every webhook endpoint, paginated. Usually one page; not always."""
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/webhook_endpoints", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more"):
            return out
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--show-endpoints", action="store_true",
                    help="print every endpoint with its status and subscription count")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    eps = endpoints(s)
    is_platform = bool(get(s, "/accounts", limit=1).get("data"))

    if args.show_endpoints:
        for e in eps:
            log.info("%s  %-8s %3d event type(s)  %s",
                     e.get("id", "we_?"), e.get("status", "?"),
                     len(e.get("enabled_events") or []), e.get("url", ""))

    state, detail = coverage(eps, is_platform)
    log.info("%d endpoint(s), %s: %s",
             len(eps), "platform with connected accounts" if is_platform
             else "no connected accounts", state)

    if state in ("covered", "not-a-platform"):
        log.info("  %s", detail)
        return 0

    log.warning("  %s", detail)
    log.warning("  repair: create a second destination scoped to connected accounts:")
    log.warning("  POST %s/webhook_endpoints with connect=true, "
                "url=https://<yourdomain>/stripe/connect-webhook", API)
    log.warning("  enabled_events[]=account.updated "
                "enabled_events[]=account.application.deauthorized "
                "enabled_events[]=capability.updated "
                "enabled_events[]=person.updated "
                "enabled_events[]=payout.failed")
    log.warning("  in Workbench: Create an event destination, then Connected accounts")
    log.warning("  then: read the top-level account property on each event and make "
                "any follow-up call as that account")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-connect-webhook-scope.mjs",
"js": '''/**
 * Report a Connect platform with no webhook destination scoped to its accounts.
 *
 * Read only. Two GET requests and no writes: give this a RESTRICTED key with
 * read access to Webhook Endpoints and Connected accounts. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// The two events that only ever come from a connected account. The endpoint
// object does not return whether it was created with connect=true, so their
// absence proves a gap and their presence only shows somebody meant to.
const CONNECT_SIGNALS = ['account.updated', 'account.application.deauthorized'];

/**
 * Decide whether connected-account events have anywhere to go. Pure.
 * Returns [state, detail]. `inconclusive` is a real answer, not a failure.
 */
export function coverage(endpoints, isPlatform) {
  if (!isPlatform) {
    return ['not-a-platform',
      'no connected accounts on this key, so there is no Connect traffic to ' +
      'scope a destination for'];
  }

  const enabled = endpoints.filter((e) => e.status === 'enabled');
  const disabled = endpoints.length - enabled.length;

  if (enabled.length === 0) {
    return ['no-endpoints',
      `no enabled endpoint in this mode at all (${disabled} disabled): nothing ` +
      'is being delivered anywhere, connected or otherwise'];
  }

  const subscribed = new Set();
  const wildcards = [];
  for (const e of enabled) {
    const types = e.enabled_events ?? [];
    if (types.includes('*')) wildcards.push(e.url ?? e.id ?? '?');
    for (const t of types) subscribed.add(t);
  }

  const have = CONNECT_SIGNALS.filter((s) => subscribed.has(s));

  if (have.length === CONNECT_SIGNALS.length) {
    return ['covered', `an enabled endpoint subscribes to ${CONNECT_SIGNALS.join(' and ')}`];
  }

  if (wildcards.length && have.length === 0) {
    return ['inconclusive',
      `${wildcards.length} endpoint(s) subscribe to * and the endpoint object ` +
      'never returns whether they are Connect scoped: open ' +
      `${wildcards[0]} in Workbench and read whether it listens to your account ` +
      'or to connected accounts'];
  }

  if (have.length) {
    const missing = CONNECT_SIGNALS.filter((s) => !subscribed.has(s));
    const consequence = missing[0] === 'account.application.deauthorized'
      ? 'sellers who disconnect keep looking active'
      : 'you see the departures and none of the verification failures';
    return ['thin', `${have[0]} is subscribed but ${missing[0]} is not: ${consequence}`];
  }

  const tail = disabled ? `, and ${disabled} disabled endpoint(s) were ignored` : '';
  return ['uncovered',
    `no enabled endpoint subscribes to ${CONNECT_SIGNALS.join(' or ')}${tail}`];
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

async function endpoints(key) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/webhook_endpoints', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more) return out;
    params.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const eps = await endpoints(key);
  const accounts = await get(key, '/accounts', { limit: 1 });
  const isPlatform = (accounts.data ?? []).length > 0;

  const [state, detail] = coverage(eps, isPlatform);
  console.log(`${eps.length} endpoint(s), ` +
    `${isPlatform ? 'platform with connected accounts' : 'no connected accounts'}: ${state}`);

  if (state === 'covered' || state === 'not-a-platform') {
    console.log(`  ${detail}`);
    return;
  }

  console.warn(`  ${detail}`);
  console.warn('  repair: create a second destination scoped to connected accounts:');
  console.warn(`  POST ${API}/webhook_endpoints with connect=true, ` +
               'url=https://<yourdomain>/stripe/connect-webhook');
  console.warn('  enabled_events[]=account.updated ' +
               'enabled_events[]=account.application.deauthorized ' +
               'enabled_events[]=capability.updated ' +
               'enabled_events[]=person.updated enabled_events[]=payout.failed');
  console.warn('  in Workbench: Create an event destination, then Connected accounts');
  console.warn('  then: read the top-level account property on each event and make ' +
               'any follow-up call as that account');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The interesting tests are the ones about what the check cannot know. A disabled endpoint holding the only relevant subscription has to count as a gap, and a wildcard endpoint has to come back as inconclusive rather than being quietly counted as coverage &mdash; that is the difference between a check that reports the truth and one that reports a guess.",
"test_py_file": "test_stripe_connect_webhook_scope.py",
"test_py": '''from stripe_connect_webhook_scope import coverage


def endpoint(events, status="enabled", url="https://example.com/hook"):
    return {"id": "we_1", "status": status, "url": url, "enabled_events": events}


def test_a_plain_account_is_not_asked_about_connect_scope():
    state, detail = coverage([endpoint(["charge.succeeded"])], False)
    assert state == "not-a-platform"
    assert "no connected accounts" in detail


def test_both_connect_signals_present_is_covered():
    state, _ = coverage(
        [endpoint(["account.updated", "account.application.deauthorized"])], True)
    assert state == "covered"


def test_neither_signal_is_uncovered():
    state, detail = coverage([endpoint(["charge.succeeded", "payout.paid"])], True)
    assert state == "uncovered"
    assert "account.updated" in detail


def test_a_disabled_endpoint_does_not_count_as_coverage():
    # A disabled endpoint delivers nothing, so it is the same as not having one.
    # It still gets mentioned, because "we do have that endpoint" is the first
    # thing anybody says.
    state, detail = coverage(
        [endpoint(["charge.succeeded"]),
         endpoint(["account.updated", "account.application.deauthorized"],
                  status="disabled")], True)
    assert state == "uncovered"
    assert "1 disabled endpoint(s) were ignored" in detail


def test_a_wildcard_is_inconclusive_rather_than_covered():
    # A wildcard endpoint would receive these events if it were Connect scoped,
    # and the object does not say whether it is. Reporting that honestly is the
    # whole point.
    state, detail = coverage([endpoint(["*"])], True)
    assert state == "inconclusive"
    assert "Workbench" in detail


def test_account_updated_without_deauthorized_is_half_a_subscription():
    state, detail = coverage([endpoint(["account.updated"])], True)
    assert state == "thin"
    assert "disconnect" in detail


def test_no_enabled_endpoint_at_all_says_so_first():
    state, detail = coverage([endpoint(["*"], status="disabled")], True)
    assert state == "no-endpoints"
    assert "nothing is being delivered anywhere" in detail
''',
"test_js_file": "stripe-connect-webhook-scope.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { coverage } from './stripe-connect-webhook-scope.mjs';

const endpoint = (events, status = 'enabled') => ({
  id: 'we_1', status, url: 'https://example.com/hook', enabled_events: events,
});

test('a plain account is not asked about connect scope', () => {
  const [state, detail] = coverage([endpoint(['charge.succeeded'])], false);
  assert.equal(state, 'not-a-platform');
  assert.match(detail, /no connected accounts/);
});

test('both connect signals present is covered', () => {
  const [state] = coverage(
    [endpoint(['account.updated', 'account.application.deauthorized'])], true);
  assert.equal(state, 'covered');
});

test('neither signal is uncovered', () => {
  const [state, detail] = coverage([endpoint(['charge.succeeded', 'payout.paid'])], true);
  assert.equal(state, 'uncovered');
  assert.match(detail, /account.updated/);
});

test('a disabled endpoint does not count as coverage', () => {
  // A disabled endpoint delivers nothing, so it is the same as not having one.
  const [state, detail] = coverage(
    [endpoint(['charge.succeeded']),
      endpoint(['account.updated', 'account.application.deauthorized'], 'disabled')], true);
  assert.equal(state, 'uncovered');
  assert.match(detail, /1 disabled endpoint\\(s\\) were ignored/);
});

test('a wildcard is inconclusive rather than covered', () => {
  const [state, detail] = coverage([endpoint(['*'])], true);
  assert.equal(state, 'inconclusive');
  assert.match(detail, /Workbench/);
});

test('account.updated without deauthorized is half a subscription', () => {
  const [state, detail] = coverage([endpoint(['account.updated'])], true);
  assert.equal(state, 'thin');
  assert.match(detail, /disconnect/);
});

test('no enabled endpoint at all says so first', () => {
  const [state, detail] = coverage([endpoint(['*'], 'disabled')], true);
  assert.equal(state, 'no-endpoints');
  assert.match(detail, /nothing is being delivered anywhere/);
});
''',
"faq": [
 ("Why can I not just read the connect flag on the endpoint?",
  "Because it is not returned. connect is a creation parameter, and the webhook endpoint object comes back with id, url, status, enabled_events, api_version, secret and application, but no field describing its scope. That is why this check works from the subscribed event types instead, and why it reports inconclusive when a wildcard makes the subscription uninformative."),
 ("Does an account-scoped endpoint ever receive account.updated?",
  "Yes, for your own account. Your platform account can be updated too, and that event goes to your normal endpoint. This is exactly what makes the subscription look correct: the event type is legitimate on both kinds of destination, and only the ones carrying a top-level account property are restricted to the Connect-scoped one."),
 ("Can one endpoint serve both my account and my connected accounts?",
  "No. The scope is fixed when the destination is created, so a platform needs two: one for its own events and one for its accounts'. They can point at the same URL if your handler branches on whether the event carries an account property, but they are two objects with two signing secrets."),
 ("What do I do with the account property once events arrive?",
  "Treat it as the identity of the seller the event is about, and make every follow-up API call as that account by setting the Stripe-Account header. Reading the account object without that header returns your platform's account, which is the classic way a newly built Connect handler appears to work and updates the wrong record."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Webhook Endpoints and Connected accounts is enough. The script lists endpoints and reads one page of accounts to establish that the check applies; it cannot create a destination, and prints the call for you to run instead."),
],
"related": [
 ("/stripe/missing-payout-failed/", "payout.failed is unsubscribed so broken bank details go unseen"),
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
 ("/stripe/no-live-webhook-endpoints/", "Live mode has no webhook endpoint at all"),
],
"citations": [CITE_CONNECT_WEBHOOKS, CITE_WEBHOOK_OBJ, CITE_WEBHOOK_CREATE, CITE_WEBHOOKS],
},

{
"slug": "current-deadline-passes-unwatched",
"title": "current_deadline passes before anyone collects the fields",
"description": "A cohort of healthy accounts breaks on one morning. The date that did it sat on every object for weeks, as a timestamp nothing ever sorted by.",
"h1": "current_deadline passes before anyone collects the fields",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe current_deadline", "connect requirements deadline",
             "stripe account deadline passed", "currently_due deadline",
             "stripe connect verification deadline"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nine sellers lost payouts on the same Monday. All nine had been processing happily for months, all nine had <code>payouts_enabled: true</code> on Sunday night, and all nine had the same Unix timestamp sitting in <code>requirements.current_deadline</code> since the middle of the previous month. Nothing read it. It is a number, not a flag, and every check anyone had written asked yes-or-no questions.",
"short_answer": """<p><code>requirements.current_deadline</code> is a Unix timestamp: the moment Stripe starts enforcing whatever is in <code>requirements.currently_due</code>. Until it arrives the account is completely normal &mdash; enabled, processing, paying out &mdash; which is why a boolean check finds nothing to say.</p>
<p>Paginate <code>GET /v1/accounts?limit=100</code>, keep accounts with a non-null <code>current_deadline</code> and a non-empty <code>currently_due</code>, and turn the timestamp into two things a person can act on: <strong>days remaining</strong>, so the list has an order, and the <strong>calendar date</strong>, so accounts sharing a date show up as the cohort they are. The deadline is the only advance warning Stripe gives you, and it is only useful as a schedule.</p>""",
"problem": """<p>The distinctive shape here is the clustering. Deadlines are set when an account crosses a processing threshold, and sellers who signed up in the same month cross the same threshold in the same month, so the dates land on top of each other. What arrives is not one broken account on a random Tuesday; it is a batch, all with the same missing field, all of whom were fine yesterday, all writing in at once to a support team sized for the usual trickle.</p>
<p>And it is the good accounts. Crossing a threshold means the seller is doing well. The list of accounts about to be disabled is roughly the list of accounts you least want to disable, and the fields being asked for are usually small &mdash; a tax id, a business URL, one director's date of birth &mdash; things a two-minute email would have collected six weeks earlier.</p>""",
"why": """<p><strong>A timestamp is not an alert.</strong> Every other field on <code>requirements</code> is a list or a string that reads as true or false: is anything due, is there a disabled reason. <code>current_deadline</code> is a number that is meaningful only in relation to today, so a check has to do arithmetic before it has anything to report. Checks that do no arithmetic report nothing, which is indistinguishable from all clear.</p>
<p><strong>The deadline is a minimum over things you cannot enumerate.</strong> It is the earliest deadline across every requested capability <em>plus</em> risk requirements that are not exposed to you. You cannot reconstruct it from the fields you can see, and you cannot assume the fields in <code>currently_due</code> are the ones that set it. The timestamp is the only place that information surfaces at all.</p>
<p><strong>It appears quietly and it can move.</strong> A deadline is set the moment a threshold is crossed, with no event dedicated to announcing it and no change to any capability. It can also come forward. A monthly report is not a substitute for reading the current value.</p>
<p><strong>Once it passes, this is a different problem.</strong> After the deadline the fields move into <code>past_due</code> and the capability is already gone; you are no longer scheduling work, you are running an incident. <a href="/stripe/requirements-past-due-disables-account/">That state has its own note</a>, and this check should hand off to it rather than pretend a passed deadline is still a warning.</p>""",
"steps": [
 {"h": "Convert the timestamp to days remaining before anything else",
  "body": """<p>Sorting by <code>current_deadline</code> ascending gives the list an order, and days remaining next to each account gives it urgency. This is the entire transformation that makes the field usable: from a number nobody reads into a queue with the nearest date at the top.</p>"""},
 {"h": "Group by calendar date, not just by account",
  "body": """<p>Accounts that share a date will fail together and can be collected together. One email template, one batch of onboarding links, one afternoon. Seeing "6 accounts due 12 March" is what turns this from a per-account chore into one scheduled piece of work.</p>"""},
 {"h": "Separate a deadline with nothing due from a deadline with fields due",
  "body": """<p>An account can carry a deadline while <code>currently_due</code> is empty &mdash; typically because Stripe is verifying documents it already has. There is nothing to collect and no email to send. Reporting it alongside accounts that need chasing adds noise to the one list that has to stay short.</p>"""},
 {"h": "Hand off anything already past the date",
  "body": """<p>A deadline in the past with fields still outstanding means the capability is already disabled. Report it in its own bucket, with a different word, so nobody reads an incident as a task with a week left on it.</p>"""},
 {"h": "Collect eventually_due when you send the link",
  "body": """<p><code>collection_options[fields]=eventually_due</code> on the account link asks for everything Stripe will ever want rather than only what is due now. Collecting <code>currently_due</code> clears this deadline and leaves the account free to acquire another one at the next threshold, which is how the same seller ends up in this report three times.</p>"""},
],
"verify": """<p>Re-run the script. Nothing should be enforced, and anything still listed should carry a date far enough out to be scheduled rather than chased.</p>
<pre><code class="language-bash">python3 stripe_current_deadline.py
# 412 account(s): 0 enforced, 0 inside 14 days, 3 scheduled across 2 date(s)</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/accounts</code>, read-only. Both interesting functions are pure and both take the clock as an argument: the classifier that turns a timestamp into an urgency, and the one that turns it into a calendar date. Time-dependent code that reads the clock itself cannot be tested, and a deadline report that is wrong about dates is worse than no report.",
"py_file": "stripe_current_deadline.py",
"py": '''"""Turn requirements.current_deadline into a dated queue of connected accounts.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_current_deadline")

API = "https://api.stripe.com/v1"

DAY = 86400


def days_left(requirements, now):
    """Whole days from `now` to requirements.current_deadline. None if unset.

    Pure, and the clock is an argument. Negative means the deadline has passed.
    """
    deadline = (requirements or {}).get("current_deadline")
    if deadline is None:
        return None
    return int((deadline - now) // DAY)


def cohort_day(deadline):
    """The UTC calendar date a deadline falls on, as YYYY-MM-DD, or None.

    Deadlines cluster: accounts that crossed a processing threshold in the same
    month share a date, and grouping by that date is what turns a list of account
    ids into one scheduled piece of work.
    """
    if deadline is None:
        return None
    return time.strftime("%Y-%m-%d", time.gmtime(deadline))


def horizon(account, now, window=14):
    """Classify one account's current deadline. Pure. Returns (state, detail).

    The states exist to separate three different jobs: an incident that has
    already happened, a batch of accounts to chase this week, and work to put in
    the calendar. An account with a deadline and nothing outstanding is a fourth
    thing: Stripe verifying what it already holds, with nothing for you to do.
    """
    reqs = account.get("requirements") or {}
    due = [f for f in (reqs.get("currently_due") or []) if f]
    left = days_left(reqs, now)

    if left is None:
        if due:
            return ("undated",
                    "%d field(s) currently due with no deadline set yet: real work, "
                    "no date to plan it around" % len(due))
        return ("clear", "no deadline and nothing currently due")

    when = cohort_day(reqs.get("current_deadline"))

    if left < 0:
        if due:
            return ("enforced",
                    "deadline passed %d day(s) ago on %s with %d field(s) still due: "
                    "these have moved into past_due and the capability is already off"
                    % (-left, when, len(due)))
        return ("passed",
                "deadline passed on %s with nothing outstanding: it was met" % when)

    if not due:
        return ("verifying",
                "deadline %s in %d day(s) with nothing currently due: Stripe is "
                "checking what it already has, so there is nothing to collect"
                % (when, left))

    if left <= window:
        return ("urgent",
                "%d day(s) left, due %s, %d field(s): %s"
                % (left, when, len(due), ", ".join(due[:4])))

    return ("scheduled",
            "%d day(s) left, due %s, %d field(s): %s"
            % (left, when, len(due), ", ".join(due[:4])))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
    """Yield connected accounts, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            yield acct
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window-days", type=int, default=14,
                    help="how many days out counts as urgent rather than scheduled")
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})
    now = int(time.time())

    rows = []
    counts = {}
    scanned = 0
    for acct in accounts(s, args.max_accounts):
        scanned += 1
        state, detail = horizon(acct, now, args.window_days)
        counts[state] = counts.get(state, 0) + 1
        if state in ("clear", "passed"):
            continue
        reqs = acct.get("requirements") or {}
        rows.append((days_left(reqs, now), cohort_day(reqs.get("current_deadline")),
                     acct.get("id", "acct_?"), state, detail))

    # Nearest deadline first; undated accounts last, since they are work you know
    # about with a date you do not.
    rows.sort(key=lambda r: (r[0] is None, r[0] if r[0] is not None else 0))
    for _left, _day, acct_id, state, detail in rows:
        log.warning("%s  %-10s %s", acct_id, state, detail)

    calendar = {}
    for _left, day, _id, state, _detail in rows:
        if day and state in ("urgent", "scheduled"):
            calendar[day] = calendar.get(day, 0) + 1

    log.info("%d account(s): %d enforced, %d inside %d days, %d scheduled across "
             "%d date(s)", scanned, counts.get("enforced", 0), counts.get("urgent", 0),
             args.window_days, counts.get("scheduled", 0), len(calendar))
    for day in sorted(calendar):
        log.info("  %s  %d account(s) fall due together", day, calendar[day])

    if counts.get("enforced"):
        log.warning("  the enforced accounts are already disabled: read past_due, not "
                    "currently_due, and treat them as an incident")
    if counts.get("urgent") or counts.get("scheduled"):
        log.warning("  repair: for each account, create an onboarding link and email it:")
        log.warning("  POST %s/account_links with account={id}, "
                    "type=account_onboarding, refresh_url, return_url,", API)
        log.warning("  collection_options[fields]=eventually_due  "
                    "(eventually_due, so the account does not come back next quarter)")
    if counts.get("undated"):
        log.warning("  the undated accounts have fields due and no deadline yet: "
                    "collect now rather than waiting for a date to appear")

    return 1 if (counts.get("enforced") or counts.get("urgent")
                 or counts.get("undated")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-current-deadline.mjs",
"js": '''/**
 * Turn requirements.current_deadline into a dated queue of connected accounts.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const DAY = 86400;

/** Whole days from `now` to requirements.current_deadline. Null if unset. */
export function daysLeft(requirements, now) {
  const deadline = (requirements ?? {}).current_deadline;
  if (deadline === null || deadline === undefined) return null;
  return Math.floor((deadline - now) / DAY);
}

/**
 * The UTC calendar date a deadline falls on, as YYYY-MM-DD, or null.
 * Deadlines cluster, and grouping by the date is what turns a list of account
 * ids into one scheduled piece of work.
 */
export function cohortDay(deadline) {
  if (deadline === null || deadline === undefined) return null;
  return new Date(deadline * 1000).toISOString().slice(0, 10);
}

/**
 * Classify one account's current deadline. Pure. Returns [state, detail].
 * The states separate an incident that already happened, a batch to chase this
 * week, work for the calendar, and a deadline with nothing to collect.
 */
export function horizon(account, now, window = 14) {
  const reqs = account.requirements ?? {};
  const due = (reqs.currently_due ?? []).filter(Boolean);
  const left = daysLeft(reqs, now);

  if (left === null) {
    if (due.length) {
      return ['undated',
        `${due.length} field(s) currently due with no deadline set yet: real work, ` +
        'no date to plan it around'];
    }
    return ['clear', 'no deadline and nothing currently due'];
  }

  const when = cohortDay(reqs.current_deadline);

  if (left < 0) {
    if (due.length) {
      return ['enforced',
        `deadline passed ${-left} day(s) ago on ${when} with ${due.length} field(s) ` +
        'still due: these have moved into past_due and the capability is already off'];
    }
    return ['passed', `deadline passed on ${when} with nothing outstanding: it was met`];
  }

  if (!due.length) {
    return ['verifying',
      `deadline ${when} in ${left} day(s) with nothing currently due: Stripe is ` +
      'checking what it already has, so there is nothing to collect'];
  }

  const detail = `${left} day(s) left, due ${when}, ${due.length} field(s): ` +
    due.slice(0, 4).join(', ');
  return [left <= window ? 'urgent' : 'scheduled', detail];
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

export async function* accounts(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/accounts', params);
    const data = page.data ?? [];
    for (const acct of data) {
      yield acct;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
    params.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const now = Math.floor(Date.now() / 1000);
  const windowDays = 14;
  const counts = new Map();
  const rows = [];
  let scanned = 0;

  for await (const acct of accounts(key)) {
    scanned += 1;
    const [state, detail] = horizon(acct, now, windowDays);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'clear' || state === 'passed') continue;
    const reqs = acct.requirements ?? {};
    rows.push({
      left: daysLeft(reqs, now),
      day: cohortDay(reqs.current_deadline),
      id: acct.id ?? 'acct_?',
      state,
      detail,
    });
  }

  // Nearest deadline first; undated accounts last, since they are work you know
  // about with a date you do not.
  rows.sort((a, b) => (a.left === null) - (b.left === null) || a.left - b.left);
  for (const r of rows) console.warn(`${r.id}  ${r.state.padEnd(10)} ${r.detail}`);

  const calendar = new Map();
  for (const r of rows) {
    if (r.day && (r.state === 'urgent' || r.state === 'scheduled')) {
      calendar.set(r.day, (calendar.get(r.day) ?? 0) + 1);
    }
  }

  const enforced = counts.get('enforced') ?? 0;
  const urgent = counts.get('urgent') ?? 0;
  const undated = counts.get('undated') ?? 0;

  console.log(`${scanned} account(s): ${enforced} enforced, ${urgent} inside ` +
    `${windowDays} days, ${counts.get('scheduled') ?? 0} scheduled across ` +
    `${calendar.size} date(s)`);
  for (const day of [...calendar.keys()].sort()) {
    console.log(`  ${day}  ${calendar.get(day)} account(s) fall due together`);
  }

  if (enforced) {
    console.warn('  the enforced accounts are already disabled: read past_due, not ' +
                 'currently_due, and treat them as an incident');
  }
  if (urgent || counts.get('scheduled')) {
    console.warn('  repair: for each account, create an onboarding link and email it:');
    console.warn(`  POST ${API}/account_links with account={id}, ` +
                 'type=account_onboarding, refresh_url, return_url,');
    console.warn('  collection_options[fields]=eventually_due  ' +
                 '(eventually_due, so the account does not come back next quarter)');
  }
  if (undated) {
    console.warn('  the undated accounts have fields due and no deadline yet: ' +
                 'collect now rather than waiting for a date to appear');
  }
  if (enforced || urgent || undated) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Both pure functions take the clock, so the tests pin real timestamps and assert on real dates. The cases that matter are the boundaries: a deadline one day inside the window against one day outside it, a deadline that has already passed, and a deadline attached to an account with nothing to collect &mdash; the last of which must not appear on a chase list, because a chase list with nothing to chase on it stops being read.",
"test_py_file": "test_stripe_current_deadline.py",
"test_py": '''from stripe_current_deadline import cohort_day, days_left, horizon

# 2026-01-01T00:00:00Z, so every assertion below is about a date a human can check.
JAN1 = 1767225600


def account(deadline=None, due=()):
    return {"id": "acct_1",
            "requirements": {"current_deadline": deadline,
                             "currently_due": list(due)}}


def test_a_missing_deadline_is_not_a_date_far_away():
    assert days_left({"current_deadline": None}, JAN1) is None
    assert days_left({}, JAN1) is None


def test_days_left_counts_whole_days_and_goes_negative():
    assert days_left({"current_deadline": JAN1 + 10 * 86400}, JAN1) == 10
    assert days_left({"current_deadline": JAN1 + 86399}, JAN1) == 0
    assert days_left({"current_deadline": JAN1 - 86400}, JAN1) == -1


def test_cohort_day_groups_by_utc_date():
    # Two accounts an hour apart on the same UTC day are one cohort; the third
    # is a separate batch, and separate is the whole point of the grouping.
    assert cohort_day(JAN1) == "2026-01-01"
    assert cohort_day(JAN1 + 3600) == "2026-01-01"
    assert cohort_day(JAN1 + 86400) == "2026-01-02"
    assert cohort_day(None) is None


def test_inside_the_window_is_urgent_and_outside_it_is_scheduled():
    urgent, detail = horizon(account(JAN1 + 13 * 86400, ["company.tax_id"]), JAN1)
    assert urgent == "urgent"
    assert "company.tax_id" in detail
    assert "2026-01-14" in detail
    later, _ = horizon(account(JAN1 + 40 * 86400, ["company.tax_id"]), JAN1)
    assert later == "scheduled"


def test_a_passed_deadline_with_fields_due_is_an_incident_not_a_warning():
    state, detail = horizon(account(JAN1 - 3 * 86400, ["company.tax_id"]), JAN1)
    assert state == "enforced"
    assert "3 day(s) ago" in detail
    assert "already off" in detail


def test_a_deadline_with_nothing_due_asks_nobody_for_anything():
    state, detail = horizon(account(JAN1 + 5 * 86400, []), JAN1)
    assert state == "verifying"
    assert "nothing to collect" in detail


def test_fields_due_with_no_deadline_are_still_work():
    state, detail = horizon(account(None, ["business_profile.url"]), JAN1)
    assert state == "undated"
    assert "no date" in detail


def test_a_healthy_account_is_clear():
    assert horizon(account(None, []), JAN1)[0] == "clear"
''',
"test_js_file": "stripe-current-deadline.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cohortDay, daysLeft, horizon } from './stripe-current-deadline.mjs';

// 2026-01-01T00:00:00Z, so every assertion below is about a date a human can check.
const JAN1 = 1767225600;

const account = (deadline = null, due = []) => ({
  id: 'acct_1',
  requirements: { current_deadline: deadline, currently_due: due },
});

test('a missing deadline is not a date far away', () => {
  assert.equal(daysLeft({ current_deadline: null }, JAN1), null);
  assert.equal(daysLeft({}, JAN1), null);
});

test('days left counts whole days and goes negative', () => {
  assert.equal(daysLeft({ current_deadline: JAN1 + 10 * 86400 }, JAN1), 10);
  assert.equal(daysLeft({ current_deadline: JAN1 + 86399 }, JAN1), 0);
  assert.equal(daysLeft({ current_deadline: JAN1 - 86400 }, JAN1), -1);
});

test('cohort day groups by utc date', () => {
  // Two accounts an hour apart on the same UTC day are one cohort; the third is
  // a separate batch, and separate is the whole point of the grouping.
  assert.equal(cohortDay(JAN1), '2026-01-01');
  assert.equal(cohortDay(JAN1 + 3600), '2026-01-01');
  assert.equal(cohortDay(JAN1 + 86400), '2026-01-02');
  assert.equal(cohortDay(null), null);
});

test('inside the window is urgent and outside it is scheduled', () => {
  const [urgent, detail] = horizon(account(JAN1 + 13 * 86400, ['company.tax_id']), JAN1);
  assert.equal(urgent, 'urgent');
  assert.match(detail, /company.tax_id/);
  assert.match(detail, /2026-01-14/);
  assert.equal(horizon(account(JAN1 + 40 * 86400, ['company.tax_id']), JAN1)[0],
    'scheduled');
});

test('a passed deadline with fields due is an incident not a warning', () => {
  const [state, detail] = horizon(account(JAN1 - 3 * 86400, ['company.tax_id']), JAN1);
  assert.equal(state, 'enforced');
  assert.match(detail, /3 day\\(s\\) ago/);
  assert.match(detail, /already off/);
});

test('a deadline with nothing due asks nobody for anything', () => {
  const [state, detail] = horizon(account(JAN1 + 5 * 86400, []), JAN1);
  assert.equal(state, 'verifying');
  assert.match(detail, /nothing to collect/);
});

test('fields due with no deadline are still work', () => {
  const [state, detail] = horizon(account(null, ['business_profile.url']), JAN1);
  assert.equal(state, 'undated');
  assert.match(detail, /no date/);
});

test('a healthy account is clear', () => {
  assert.equal(horizon(account(null, []), JAN1)[0], 'clear');
});
''',
"faq": [
 ("What sets a current_deadline in the first place?",
  "Crossing a threshold. Stripe asks for more verification as an account processes more volume or gets closer to a payout milestone, and the deadline is the date that new information starts being enforced. It is set silently: no capability changes, no disabled_reason appears, and the account keeps working normally right up to the date."),
 ("Why does the deadline not match the fields I can see?",
  "Because it is the earliest deadline across every requested capability plus risk requirements that are not exposed on the account object. You cannot reconstruct it from currently_due, and you should not assume the fields you can see are the ones that set it. Collect everything listed and re-read the object rather than reasoning about which field owns the date."),
 ("Is this the same as future_requirements.current_deadline?",
  "No, and both exist on the same account. This one is on the requirements hash and covers fields that are due now, with a date at which they start being enforced. The other is on a separate hash of fields Stripe has not started asking for yet, and has its own deadline for when they migrate across. A note on that hash is linked below."),
 ("Should I alert on every account with a deadline?",
  "No, only on those that also have something in currently_due. An account can carry a deadline with an empty currently_due while Stripe verifies documents it already holds, and nobody can act on that. Filtering it out is what keeps the list short enough to be read every morning."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Connected accounts is enough. The script reads one paginated list, sorts it by date and prints the account link call for you to run; it cannot create links, update accounts or collect anything."),
],
"related": [
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/future-requirements-deadline-ignored/", "future_requirements will revoke a capability on a date"),
 ("/stripe/onboarding-abandoned-details-not-submitted/", "Accounts stall at details_submitted false after link expiry"),
],
"citations": [CITE_VERIFICATION, CITE_ACCOUNT_OBJECT, CITE_ACCOUNT_LINKS, CITE_HOSTED_ONBOARDING],
},

{
"slug": "external-account-errored",
"title": "A bank account sits at status errored and payouts stop",
"description": "One payout failed a month ago and none has been attempted since. The destination is frozen, so the failure count stops growing exactly when it matters.",
"h1": "a bank account sits at status errored and payouts stop",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe external account errored", "bank account status errored",
             "stripe payouts stopped", "verification_failed bank account",
             "stripe external account status"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A seller's payout failed in July. Somebody looked, saw one failure, assumed a temporary bank problem and moved on. It is now September, the seller's balance has grown to five figures, and there have been no further failed payouts at all &mdash; which is exactly what everyone took as evidence that the problem had resolved itself.",
"short_answer": """<p>Read <code>status</code> on the external account itself: <code>GET /v1/accounts/{id}/external_accounts?limit=100</code>. When a payout fails, Stripe marks the destination <code>errored</code> and stops sending scheduled payouts to it until new details are attached. Two other statuses do the same thing for different reasons: <code>verification_failed</code> and <code>tokenized_account_number_deactivated</code>.</p>
<p>Corroborate with a balance that is going nowhere &mdash; <code>GET /v1/balance</code> and <code>GET /v1/payouts?limit=1</code> with the <code>Stripe-Account</code> header &mdash; and note the repair: for <code>errored</code>, editing the account and routing numbers on the existing object does <em>not</em> clear the status. A new external account, made <code>default_for_currency</code>, is the reliable fix.</p>""",
"problem": """<p>Everything about this failure argues that it is over. There was one bad event, it was weeks ago, and nothing bad has happened since. Any monitor built around <code>GET /v1/payouts?status=failed</code> agrees: the count went up by one and then stayed flat. Flat is what recovery looks like.</p>
<p>It is not recovery. It is the absence of attempts. Stripe froze the destination on the first failure, so there is nothing left to fail, and the metric everyone is watching goes quiet precisely because the problem became permanent. Meanwhile the money accumulates in a balance nobody is looking at, and the seller &mdash; who receives no notification when their account is Custom &mdash; finds out when they go to reconcile the quarter.</p>""",
"why": """<p><strong>The state lives on the destination, not on the payout.</strong> Payout objects record what happened to individual attempts. The external account records whether attempts will happen at all. Those are different objects, and only one of them is in most people's dashboards.</p>
<p><strong><code>errored</code> is sticky in a way that surprises people.</strong> It is not cleared by fixing the numbers in place. Updating the routing or account number on the existing bank account leaves the status where it is; Stripe wants a fresh external account attached and set as the default for that currency. Teams that patch the existing object see no change and conclude the API is broken.</p>
<p><strong>Three different statuses stop payouts for three different reasons.</strong> <code>errored</code> follows a failed payout. <code>verification_failed</code> means the ownership details did not check out. <code>tokenized_account_number_deactivated</code> means the token behind the destination was deactivated and it has to be re-linked. Same symptom, three repairs, and a check that only greps for <code>errored</code> finds one of them.</p>
<p><strong>Nothing on the account object says any of this.</strong> <code>payouts_enabled</code> can stay <code>true</code> with a frozen destination, because the capability is fine &mdash; it is the bank details that are not. An account-level health check passes cleanly the whole time.</p>""",
"steps": [
 {"h": "List the destinations, not the payouts",
  "body": """<p><code>GET /v1/accounts/{id}/external_accounts?limit=100</code> for each connected account, and for the platform's own account too. Read <code>status</code> on every one. This is the only field that distinguishes "no payouts because nothing was owed" from "no payouts because Stripe stopped trying".</p>"""},
 {"h": "Corroborate with a balance that is not moving",
  "body": """<p>A frozen destination on an account with a zero balance is untidy. A frozen destination on an account with a growing <code>available</code> balance and no payout for six weeks is money that belongs to somebody else sitting on your platform. Fetch <code>GET /v1/balance</code> and the most recent payout with the <code>Stripe-Account</code> header, and only for the accounts that already look halted, so the check stays cheap.</p>"""},
 {"h": "Read which status it is before writing the repair ticket",
  "body": """<p>The three halting statuses need three different conversations with the seller: fresh bank details, identity details that match the account holder, or a re-link through Financial Connections. Printing the status without the corresponding repair produces a ticket that bounces once before anyone can act on it.</p>"""},
 {"h": "Check whether the frozen one is even the default",
  "body": """<p><code>default_for_currency</code> tells you whether this destination is the one payouts actually use. An errored account that is not the default is a cleanup task; the default being errored is why the money stopped. The distinction decides which list the account goes on.</p>"""},
 {"h": "Attach a new external account rather than editing the old one",
  "body": """<p>New bank details, tokenized, attached to the account, then set <code>default_for_currency</code> on the new object. After that, re-check <code>status</code>: the new destination should read <code>new</code> or <code>validated</code>, and the accumulated balance pays out on the next scheduled run.</p>"""},
],
"verify": """<p>Re-run the script. Every destination should read a healthy status, and no account should be holding a balance behind a frozen one.</p>
<pre><code class="language-bash">python3 stripe_external_account_errored.py
# 412 account(s), 418 destination(s): 0 halted, 0 stranded</code></pre>""",
"code_intro": "One paginated GET for the accounts, one per account for its destinations, and the balance and last-payout lookups only for the accounts that already look halted &mdash; corroboration is worth two extra calls on a handful of accounts and not worth six hundred on a healthy platform. The classifier is pure and takes the evidence as arguments, including the case where it was not gathered.",
"py_file": "stripe_external_account_errored.py",
"py": '''"""Report connected accounts whose payout destination Stripe has stopped using.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Connected accounts, Bank accounts, Payouts and Balance. The repair is printed,
never performed, because this script holds a credential to a live payments
account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_external_account_errored")

API = "https://api.stripe.com/v1"

DAY = 86400

# Statuses where Stripe has stopped sending scheduled payouts to this
# destination. Same symptom, three different repairs, which is why the table is
# the check rather than a comparison against the one status everybody knows.
HALTED = {
    "errored":
        "a payout to this destination failed. Editing the account or routing "
        "number on the existing object does not clear this: attach a NEW external "
        "account and set default_for_currency on it.",
    "verification_failed":
        "the ownership details behind this destination could not be verified. "
        "Attach a new external account whose holder details match the account.",
    "tokenized_account_number_deactivated":
        "the tokenized account number behind this destination was deactivated. "
        "Re-link the bank through Financial Connections to mint a new one.",
}

# Statuses where payouts can be sent. `new` simply means Stripe has not yet had
# reason to validate it, which is not a problem.
HEALTHY = ("new", "validated", "verified")


def verdict(external, last_payout_created, available_amount, now):
    """Classify one external account. Pure. Returns (state, detail).

    `last_payout_created` and `available_amount` are the corroborating evidence
    and may be None, meaning it was not looked up. That is deliberate: the
    evidence is only fetched for destinations that already look halted, so the
    classifier has to be honest about the difference between "no money stranded"
    and "nobody checked".
    """
    if external is None:
        return ("no-destination",
                "no external account attached at all: there is nothing for a payout "
                "to be sent to")

    status = (external.get("status") or "").lower()

    if status in HALTED:
        bits = ["status %s" % status, HALTED[status]]
        if available_amount:
            bits.append("%d (minor units) sitting in the available balance"
                        % available_amount)
        if last_payout_created is not None:
            bits.append("last payout %d day(s) ago"
                        % ((now - last_payout_created) // DAY))
        elif available_amount is not None:
            bits.append("no payout has ever been attempted")
        if not external.get("default_for_currency"):
            bits.append("not the default destination for %s, so cleanup rather than "
                        "the cause" % (external.get("currency") or "its currency"))
        state = "stranded" if available_amount else "halted"
        return (state, " | ".join(bits))

    if status in HEALTHY:
        return ("healthy", "status %s: payouts can be sent here" % status)

    return ("unknown", "unrecognised status %r: read it before assuming it is fine"
            % (external.get("status"),))


def get(session, path, account=None, **params):
    headers = {"Stripe-Account": account} if account else None
    r = session.get(API + path, params=params, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
    """Yield connected accounts, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            yield acct
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def evidence(session, account_id):
    """Balance and last payout for one account. Only called when it may matter."""
    balance = get(session, "/balance", account=account_id)
    available = sum(b.get("amount", 0) for b in balance.get("available", []) or [])
    payouts = get(session, "/payouts", account=account_id, limit=1)
    data = payouts.get("data", [])
    return (data[0].get("created") if data else None), available


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--account", help="check one connected account instead of all")
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})
    now = int(time.time())

    if args.account:
        targets = [{"id": args.account}]
    else:
        targets = list(accounts(s, args.max_accounts))

    counts = {}
    destinations = 0

    for acct in targets:
        acct_id = acct.get("id")
        banks = get(s, "/accounts/%s/external_accounts" % acct_id,
                    object="bank_account", limit=100).get("data", [])
        if not banks:
            state, detail = verdict(None, None, None, now)
            counts[state] = counts.get(state, 0) + 1
            log.warning("%s  %-14s %s", acct_id, state, detail)
            continue

        for bank in banks:
            destinations += 1
            # The evidence costs two extra calls, so only spend them where the
            # status already says payouts have stopped.
            if (bank.get("status") or "").lower() in HALTED:
                last_payout, available = evidence(s, acct_id)
            else:
                last_payout, available = None, None
            state, detail = verdict(bank, last_payout, available, now)
            counts[state] = counts.get(state, 0) + 1
            if state == "healthy":
                continue
            log.warning("%s %s  %-14s %s", acct_id, bank.get("id", "ba_?"),
                        state, detail)

    halted = counts.get("halted", 0)
    stranded = counts.get("stranded", 0)
    log.info("%d account(s), %d destination(s): %d halted, %d stranded",
             len(targets), destinations, halted, stranded)

    if halted or stranded:
        log.warning("  repair: attach fresh details rather than editing the frozen "
                    "object, then make the new one default:")
        log.warning("  POST %s/accounts/{id} with external_account={{BANK_TOKEN}}", API)
        log.warning("  POST %s/accounts/{id}/external_accounts/{ba_id} with "
                    "default_for_currency=true", API)
        log.warning("  check: a flat count of failed payouts is not recovery when the "
                    "destination is frozen, because nothing is being attempted")
    if counts.get("no-destination"):
        log.warning("  %d account(s) have no bank account attached at all",
                    counts["no-destination"])
    return 1 if (halted or stranded or counts.get("no-destination")
                 or counts.get("unknown")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-external-account-errored.mjs",
"js": '''/**
 * Report connected accounts whose payout destination Stripe has stopped using.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to Connected accounts, Bank accounts, Payouts and Balance. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const DAY = 86400;

// Statuses where Stripe has stopped sending scheduled payouts to this
// destination. Same symptom, three different repairs.
const HALTED = {
  errored:
    'a payout to this destination failed. Editing the account or routing number ' +
    'on the existing object does not clear this: attach a NEW external account ' +
    'and set default_for_currency on it.',
  verification_failed:
    'the ownership details behind this destination could not be verified. Attach ' +
    'a new external account whose holder details match the account.',
  tokenized_account_number_deactivated:
    'the tokenized account number behind this destination was deactivated. ' +
    'Re-link the bank through Financial Connections to mint a new one.',
};

// Statuses where payouts can be sent. `new` means Stripe has had no reason to
// validate it yet, which is not a problem.
const HEALTHY = ['new', 'validated', 'verified'];

/**
 * Classify one external account. Pure. Returns [state, detail].
 * The evidence arguments may be null, meaning nobody looked: it is only fetched
 * for destinations that already look halted, and the classifier has to keep
 * "no money stranded" distinct from "not checked".
 */
export function verdict(external, lastPayoutCreated, availableAmount, now) {
  if (external === null || external === undefined) {
    return ['no-destination',
      'no external account attached at all: there is nothing for a payout to be ' +
      'sent to'];
  }

  const status = (external.status ?? '').toLowerCase();

  if (Object.prototype.hasOwnProperty.call(HALTED, status)) {
    const bits = [`status ${status}`, HALTED[status]];
    if (availableAmount) {
      bits.push(`${availableAmount} (minor units) sitting in the available balance`);
    }
    if (lastPayoutCreated !== null && lastPayoutCreated !== undefined) {
      bits.push(`last payout ${Math.floor((now - lastPayoutCreated) / DAY)} day(s) ago`);
    } else if (availableAmount !== null && availableAmount !== undefined) {
      bits.push('no payout has ever been attempted');
    }
    if (!external.default_for_currency) {
      bits.push(`not the default destination for ${external.currency ?? 'its currency'}, ` +
                'so cleanup rather than the cause');
    }
    return [availableAmount ? 'stranded' : 'halted', bits.join(' | ')];
  }

  if (HEALTHY.includes(status)) {
    return ['healthy', `status ${status}: payouts can be sent here`];
  }

  return ['unknown',
    `unrecognised status ${JSON.stringify(external.status)}: read it before ` +
    'assuming it is fine'];
}

async function get(key, path, { account, ...params } = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const headers = { Authorization: `Bearer ${key}` };
  if (account) headers['Stripe-Account'] = account;
  const res = await fetch(url, { headers });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function* accounts(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/accounts', params);
    const data = page.data ?? [];
    for (const acct of data) {
      yield acct;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
    params.starting_after = data[data.length - 1].id;
  }
}

async function evidence(key, accountId) {
  const balance = await get(key, '/balance', { account: accountId });
  const available = (balance.available ?? []).reduce((t, b) => t + (b.amount ?? 0), 0);
  const payouts = await get(key, '/payouts', { account: accountId, limit: 1 });
  const data = payouts.data ?? [];
  return [data.length ? data[0].created : null, available];
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const now = Math.floor(Date.now() / 1000);
  const targets = [];
  for await (const acct of accounts(key)) targets.push(acct);

  const counts = new Map();
  let destinations = 0;

  for (const acct of targets) {
    const banks = (await get(key, `/accounts/${acct.id}/external_accounts`,
      { object: 'bank_account', limit: 100 })).data ?? [];

    if (banks.length === 0) {
      const [state, detail] = verdict(null, null, null, now);
      counts.set(state, (counts.get(state) ?? 0) + 1);
      console.warn(`${acct.id}  ${state.padEnd(14)} ${detail}`);
      continue;
    }

    for (const bank of banks) {
      destinations += 1;
      // The evidence costs two extra calls, so only spend them where the status
      // already says payouts have stopped.
      const halted = Object.prototype.hasOwnProperty.call(
        HALTED, (bank.status ?? '').toLowerCase());
      const [lastPayout, available] = halted
        ? await evidence(key, acct.id) : [null, null];
      const [state, detail] = verdict(bank, lastPayout, available, now);
      counts.set(state, (counts.get(state) ?? 0) + 1);
      if (state === 'healthy') continue;
      console.warn(`${acct.id} ${bank.id ?? 'ba_?'}  ${state.padEnd(14)} ${detail}`);
    }
  }

  const halted = counts.get('halted') ?? 0;
  const stranded = counts.get('stranded') ?? 0;
  console.log(`${targets.length} account(s), ${destinations} destination(s): ` +
    `${halted} halted, ${stranded} stranded`);

  if (halted || stranded) {
    console.warn('  repair: attach fresh details rather than editing the frozen ' +
                 'object, then make the new one default:');
    console.warn(`  POST ${API}/accounts/{id} with external_account={{BANK_TOKEN}}`);
    console.warn(`  POST ${API}/accounts/{id}/external_accounts/{ba_id} with ` +
                 'default_for_currency=true');
    console.warn('  check: a flat count of failed payouts is not recovery when the ' +
                 'destination is frozen, because nothing is being attempted');
  }
  if (counts.get('no-destination')) {
    console.warn(`  ${counts.get('no-destination')} account(s) have no bank account ` +
                 'attached at all');
  }
  if (halted || stranded || counts.get('no-destination') || counts.get('unknown')) {
    process.exitCode = 1;
  }
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests cover all three halting statuses, because the repair text is the deliverable and getting it wrong sends a seller to fix the wrong thing. They also pin the difference between evidence that came back empty and evidence that was never gathered, which is the one place a classifier like this quietly lies.",
"test_py_file": "test_stripe_external_account_errored.py",
"test_py": '''from stripe_external_account_errored import HALTED, verdict

NOW = 1767225600  # 2026-01-01T00:00:00Z


def bank(status, default=True, currency="usd"):
    return {"id": "ba_1", "status": status, "currency": currency,
            "default_for_currency": default}


def test_a_validated_account_is_healthy():
    state, detail = verdict(bank("validated"), None, None, NOW)
    assert state == "healthy"
    assert "payouts can be sent" in detail


def test_new_is_not_an_error():
    # `new` only means Stripe has had no reason to validate it yet.
    assert verdict(bank("new"), None, None, NOW)[0] == "healthy"


def test_every_halting_status_is_caught_and_carries_its_own_repair():
    for status in HALTED:
        state, detail = verdict(bank(status), None, None, NOW)
        assert state == "halted", status
        assert status in detail


def test_errored_says_not_to_edit_the_existing_object():
    _, detail = verdict(bank("errored"), None, None, NOW)
    assert "does not clear this" in detail
    assert "NEW external account" in detail


def test_a_balance_behind_a_frozen_destination_is_stranded():
    state, detail = verdict(bank("errored"), NOW - 45 * 86400, 812340, NOW)
    assert state == "stranded"
    assert "812340" in detail
    assert "45 day(s) ago" in detail


def test_evidence_that_was_never_gathered_is_not_reported_as_no_money():
    # available_amount None means nobody looked. Saying "no payout has ever been
    # attempted" in that case would be an invention.
    _, detail = verdict(bank("errored"), None, None, NOW)
    assert "no payout has ever been attempted" not in detail
    _, detail = verdict(bank("errored"), None, 0, NOW)
    assert "no payout has ever been attempted" in detail


def test_a_frozen_non_default_destination_is_flagged_as_cleanup():
    _, detail = verdict(bank("verification_failed", default=False), None, None, NOW)
    assert "not the default destination for usd" in detail


def test_no_bank_account_at_all_is_its_own_answer():
    state, _ = verdict(None, None, None, NOW)
    assert state == "no-destination"


def test_an_unrecognised_status_is_not_assumed_healthy():
    assert verdict(bank("some_new_status"), None, None, NOW)[0] == "unknown"
''',
"test_js_file": "stripe-external-account-errored.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-external-account-errored.mjs';

const NOW = 1767225600; // 2026-01-01T00:00:00Z

const bank = (status, defaultForCurrency = true, currency = 'usd') => ({
  id: 'ba_1', status, currency, default_for_currency: defaultForCurrency,
});

test('a validated account is healthy', () => {
  const [state, detail] = verdict(bank('validated'), null, null, NOW);
  assert.equal(state, 'healthy');
  assert.match(detail, /payouts can be sent/);
});

test('new is not an error', () => {
  assert.equal(verdict(bank('new'), null, null, NOW)[0], 'healthy');
});

test('every halting status is caught and carries its own repair', () => {
  for (const status of ['errored', 'verification_failed',
    'tokenized_account_number_deactivated']) {
    const [state, detail] = verdict(bank(status), null, null, NOW);
    assert.equal(state, 'halted', status);
    assert.ok(detail.includes(status));
  }
});

test('errored says not to edit the existing object', () => {
  const [, detail] = verdict(bank('errored'), null, null, NOW);
  assert.match(detail, /does not clear this/);
  assert.match(detail, /NEW external account/);
});

test('a balance behind a frozen destination is stranded', () => {
  const [state, detail] = verdict(bank('errored'), NOW - 45 * 86400, 812340, NOW);
  assert.equal(state, 'stranded');
  assert.match(detail, /812340/);
  assert.match(detail, /45 day\\(s\\) ago/);
});

test('evidence that was never gathered is not reported as no money', () => {
  // A null available amount means nobody looked, which is not the same as zero.
  assert.ok(!verdict(bank('errored'), null, null, NOW)[1]
    .includes('no payout has ever been attempted'));
  assert.ok(verdict(bank('errored'), null, 0, NOW)[1]
    .includes('no payout has ever been attempted'));
});

test('a frozen non default destination is flagged as cleanup', () => {
  const [, detail] = verdict(bank('verification_failed', false), null, null, NOW);
  assert.match(detail, /not the default destination for usd/);
});

test('no bank account at all is its own answer', () => {
  assert.equal(verdict(null, null, null, NOW)[0], 'no-destination');
});

test('an unrecognised status is not assumed healthy', () => {
  assert.equal(verdict(bank('some_new_status'), null, null, NOW)[0], 'unknown');
});
''',
"faq": [
 ("Why did the failed payouts stop if nothing was fixed?",
  "Because Stripe stopped attempting them. The first failure sets the destination to errored and scheduled payouts to it are held until new details are attached, so the count of failed payouts goes flat. That flatness is the symptom, not the recovery, and it is why a monitor built only on failed payouts is blind to this state."),
 ("Can I clear errored by updating the account and routing numbers?",
  "No. Editing the numbers on the existing bank account object leaves the status where it is. Attach a new external account with the correct details and set default_for_currency on it; the old object can then be detached. Teams that patch in place see no change and usually conclude something is broken on Stripe's side."),
 ("Does payouts_enabled go false when this happens?",
  "Not necessarily. payouts_enabled describes the account's capability, and the capability is fine: it is the bank details that are not. An account-level health check can report a completely healthy account whose money has not moved in six weeks, which is exactly why the destination has to be read directly."),
 ("What is tokenized_account_number_deactivated?",
  "It means the tokenized account number behind the destination was deactivated, so the destination can no longer be used even though the details look right. The fix is to re-link the bank so a fresh token is minted, rather than to re-type the same numbers. It halts payouts the same way errored does, which is why it belongs in the same check."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Connected accounts, Bank accounts, Payouts and Balance is enough. It lists destinations and reads a balance; attaching new bank details is printed as a call for a human to run, and the script has no permission to run it."),
],
"related": [
 ("/stripe/payouts-failing-bank-rejection/", "Payouts fail with account_closed and nobody is watching"),
 ("/stripe/no-external-account-attached/", "A connected account has no external account to pay out to"),
 ("/stripe/payout-schedule-left-on-manual/", "Payout schedule was left on manual and funds pile up"),
],
"citations": [CITE_EXTERNAL_ACCOUNT, CITE_PAYOUT_OBJECT, CITE_PAYOUTS_CONNECT, CITE_ACCOUNT_OBJECT],
},

{
"slug": "platform-paused-payouts-left-on",
"title": "Platform-paused payouts were never unpaused",
"description": "The investigation closed months ago and the pause is still on. No API call reverses it, no event announced it, and the paper trail is canceled payouts.",
"h1": "platform-paused payouts were never unpaused",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe platform_paused", "unpause connected account",
             "stripe disabled_reason platform_paused", "canceled payouts stripe",
             "connect pause payouts"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "In March, risk paused a seller while a chargeback pattern was investigated. In April the investigation closed with nothing found, the ticket was marked resolved, and everyone moved on. It is now September. The seller has been taking payments the whole time, the money has been accumulating, and the pause is still on, because unpausing was a manual step in a dashboard and nothing anywhere remembers that it was owed.",
"short_answer": """<p>Paginate <code>GET /v1/accounts?limit=100</code> and flag <code>requirements.disabled_reason == "platform_paused"</code>. That string means the platform did this, deliberately, at some point &mdash; not Stripe, not the seller, and not a missing verification field.</p>
<p>Corroborate with <code>GET /v1/payouts?status=canceled</code> using the <code>Stripe-Account</code> header. Pausing leaves in-flight payouts <code>pending</code> for up to ten days and then cancels them, returning the funds to the connected balance, so the trail this leaves is a cluster of <em>canceled</em> payouts rather than failed ones. Unpausing is Dashboard-only: there is no v1 endpoint for it, and the canceled payouts are not re-issued for you.</p>""",
"problem": """<p>This is the one Connect failure that is entirely self-inflicted, and that is what makes it survive. Every other disabled account has an external cause and therefore an external prompt: a deadline, a verification failure, a rejection. A platform pause has none. It is a decision your own team made, recorded in a ticket system that has no connection to Stripe, and reversed only when a person remembers.</p>
<p>The seller often cannot tell you either. A Custom account receives no notification from Stripe when it is paused, so from their side money simply stopped arriving. If they are still processing payments &mdash; a payouts-only pause leaves charges working &mdash; their revenue reports look normal and only their bank statement disagrees. The gap between "we paused this in March" and "we noticed in September" is usually a seller doing their quarterly accounts.</p>""",
"why": """<p><strong>Generic disabled-account checks classify it wrongly.</strong> A monitor that reads <code>disabled_reason</code> and sorts into "collect some fields" or "Stripe rejected it" has no bucket for this one, so <code>platform_paused</code> lands in the collectable pile. The seller then receives an onboarding link, completes it perfectly, and nothing changes &mdash; because there was never a field missing. <a href="/stripe/connected-accounts-charges-disabled/">The broader charges_enabled check</a> is worth running, but it needs this reason carved out of it.</p>
<p><strong>There is no API to undo it.</strong> Unpausing lives in the Dashboard under Connect, Connected accounts, on the account itself. No <code>POST</code> reverses it, so it cannot be put in a runbook, a script, or a scheduled job that expires holds automatically. It is a manual action with no deadline attached, which is a category of task organisations are reliably bad at.</p>
<p><strong>The evidence is canceled, not failed.</strong> Payouts already in flight when the pause lands stay <code>pending</code> for up to ten days and are then canceled, with the money returned to the connected balance. Anyone searching for failures finds nothing, and <code>canceled</code> is a status most payout monitors ignore entirely because it usually means somebody intended it.</p>
<p><strong>Unpausing does not pay out the backlog.</strong> The canceled payouts stay canceled. Once the account is live again the accumulated balance goes out on the next scheduled run, or waits for a manual payout if the schedule is manual, so an account can be unpaused and still be sitting on the money.</p>""",
"steps": [
 {"h": "Search on the reason string, not on the boolean",
  "body": """<p><code>payouts_enabled: false</code> is shared by half a dozen unrelated problems. <code>requirements.disabled_reason == "platform_paused"</code> is unambiguous and identifies exactly the accounts your own team switched off. Pausing can apply to charges, to payouts, or to both, so read both flags rather than assuming which one was used.</p>"""},
 {"h": "Pull the canceled payouts for each paused account",
  "body": """<p><code>GET /v1/payouts?status=canceled&amp;limit=100</code> with the <code>Stripe-Account</code> header. The oldest canceled payout is a good estimate of when the pause landed, which is the number that turns "this account is paused" into "this account has been paused for 174 days" &mdash; and only the second version gets acted on.</p>"""},
 {"h": "Reconcile the list against the tickets that caused it",
  "body": """<p>Every paused account should map to an open investigation. The ones that map to a closed investigation, or to no ticket at all, are the finding. This is the only step that cannot be automated from Stripe's side, because the reason for the pause was never written down anywhere Stripe can see.</p>"""},
 {"h": "Unpause in the Dashboard, then confirm through the API",
  "body": """<p>Connect, Connected accounts, open the account, unpause payments or payouts. Then re-read the account: <code>payouts_enabled</code> should be <code>true</code> and <code>disabled_reason</code> should be gone. Believe the API rather than the dashboard's confirmation banner.</p>"""},
 {"h": "Re-issue what was canceled",
  "body": """<p>Nothing replays automatically. The balance is sitting on the connected account, and either the next scheduled payout collects it or somebody has to create one. An account left on a manual payout schedule will hold that money indefinitely even after the pause is lifted.</p>"""},
],
"verify": """<p>Re-run the script. No account should be paused without a matching open investigation, and none should be carrying canceled payouts nobody re-issued.</p>
<pre><code class="language-bash">python3 stripe_platform_paused.py
# 412 account(s): 0 paused by the platform, 0 with canceled payouts to re-issue</code></pre>""",
"code_intro": "One paginated GET for the accounts, and the canceled-payout lookup only for accounts that are actually paused &mdash; with a flag to widen it, since payouts canceled by a pause that has since been lifted are their own finding. The classifier is pure and deliberately refuses to claim accounts disabled for other reasons: this check is about one string, and a check that quietly absorbs its neighbours becomes impossible to act on.",
"py_file": "stripe_platform_paused.py",
"py": '''"""Report connected accounts the platform paused and never unpaused.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Connected accounts and Payouts. The repair is printed, never performed, because
this script holds a credential to a live payments account. It is also printed as
a Dashboard path rather than an API call, because Stripe has no v1 endpoint that
unpauses an account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_platform_paused")

API = "https://api.stripe.com/v1"

DAY = 86400

PAUSED = "platform_paused"


def verdict(account, canceled_count, oldest_canceled_created, now):
    """Classify one connected account against a platform pause. Pure.

    Returns (state, detail). Accounts disabled for any other reason are returned
    as `other-reason` rather than being folded in: a pause is a decision your own
    team made and needs a different response from a missing verification field,
    and a check that blurs the two sends onboarding links to sellers who have
    nothing to submit.
    """
    reqs = account.get("requirements") or {}
    reason = reqs.get("disabled_reason")

    if reason == PAUSED:
        off = []
        if account.get("charges_enabled") is False:
            off.append("charges")
        if account.get("payouts_enabled") is False:
            off.append("payouts")
        bits = ["paused by the platform: %s off" % (" and ".join(off) or "nothing")]
        if canceled_count:
            bits.append("%d canceled payout(s)" % canceled_count)
        if oldest_canceled_created is not None:
            bits.append("paused for at least %d day(s), from the oldest cancellation"
                        % ((now - oldest_canceled_created) // DAY))
        bits.append("no API call reverses this: Dashboard, Connect, Connected "
                    "accounts, open the account")
        return ("paused", " | ".join(bits))

    if reason:
        return ("other-reason",
                "disabled for %s, which is not a platform pause and is not this "
                "check's problem" % reason)

    if canceled_count:
        return ("residue",
                "%d canceled payout(s) on an account that is not paused now: a pause "
                "was lifted and the canceled payouts were never re-issued" % canceled_count)

    return ("healthy", "not paused")


def get(session, path, account=None, **params):
    headers = {"Stripe-Account": account} if account else None
    r = session.get(API + path, params=params, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
    """Yield connected accounts, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            yield acct
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def canceled_payouts(session, account_id):
    """Count canceled payouts for one account and find the oldest.

    A pause holds in-flight payouts as pending for up to ten days and then
    cancels them, so this is the paper trail. Failed payouts are a different
    problem entirely and are not counted here.
    """
    count = 0
    oldest = None
    params = {"status": "canceled", "limit": 100}
    while True:
        page = get(session, "/payouts", account=account_id, **params)
        data = page.get("data", [])
        for payout in data:
            count += 1
            created = payout.get("created")
            if created is not None and (oldest is None or created < oldest):
                oldest = created
        if not data or not page.get("has_more"):
            return count, oldest
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-canceled-everywhere", action="store_true",
                    help="look for canceled payouts on every account, not only the "
                         "paused ones. Two extra calls per account, and the only way "
                         "to find payouts canceled by a pause that was later lifted")
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})
    now = int(time.time())

    counts = {}
    scanned = 0

    for acct in accounts(s, args.max_accounts):
        scanned += 1
        reqs = acct.get("requirements") or {}
        paused = reqs.get("disabled_reason") == PAUSED

        if paused or args.check_canceled_everywhere:
            count, oldest = canceled_payouts(s, acct.get("id"))
        else:
            count, oldest = 0, None

        state, detail = verdict(acct, count, oldest, now)
        counts[state] = counts.get(state, 0) + 1
        if state in ("healthy", "other-reason"):
            continue
        log.warning("%s  %-8s %s", acct.get("id", "acct_?"), state, detail)

    paused = counts.get("paused", 0)
    residue = counts.get("residue", 0)
    log.info("%d account(s): %d paused by the platform, %d with canceled payouts "
             "to re-issue", scanned, paused, residue)

    if paused:
        log.warning("  repair: Dashboard, Connect, Connected accounts, open the "
                    "account, unpause payments or payouts. There is no v1 API for it.")
        log.warning("  then: re-read the account and confirm payouts_enabled is true "
                    "and disabled_reason is gone")
        log.warning("  reconcile: every paused account should map to an OPEN "
                    "investigation. The ones that do not are the finding.")
    if paused or residue:
        log.warning("  note: unpausing does not replay canceled payouts. The balance "
                    "waits for the next scheduled payout, or forever on a manual "
                    "schedule.")
    if not args.check_canceled_everywhere:
        log.info("  canceled payouts were only checked on paused accounts; "
                 "--check-canceled-everywhere widens it")
    return 1 if (paused or residue) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-platform-paused.mjs",
"js": '''/**
 * Report connected accounts the platform paused and never unpaused.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to Connected accounts and Payouts. The repair is printed, never performed, and
 * it is printed as a Dashboard path because Stripe has no v1 endpoint that
 * unpauses an account.
 */
const API = 'https://api.stripe.com/v1';

const DAY = 86400;

const PAUSED = 'platform_paused';

/**
 * Classify one connected account against a platform pause. Pure.
 * Returns [state, detail]. Accounts disabled for any other reason come back as
 * `other-reason` rather than being folded in: blurring the two sends onboarding
 * links to sellers who have nothing to submit.
 */
export function verdict(account, canceledCount, oldestCanceledCreated, now) {
  const reqs = account.requirements ?? {};
  const reason = reqs.disabled_reason ?? null;

  if (reason === PAUSED) {
    const off = [];
    if (account.charges_enabled === false) off.push('charges');
    if (account.payouts_enabled === false) off.push('payouts');
    const bits = [`paused by the platform: ${off.join(' and ') || 'nothing'} off`];
    if (canceledCount) bits.push(`${canceledCount} canceled payout(s)`);
    if (oldestCanceledCreated !== null && oldestCanceledCreated !== undefined) {
      bits.push('paused for at least ' +
        `${Math.floor((now - oldestCanceledCreated) / DAY)} day(s), from the ` +
        'oldest cancellation');
    }
    bits.push('no API call reverses this: Dashboard, Connect, Connected accounts, ' +
              'open the account');
    return ['paused', bits.join(' | ')];
  }

  if (reason) {
    return ['other-reason',
      `disabled for ${reason}, which is not a platform pause and is not this ` +
      "check's problem"];
  }

  if (canceledCount) {
    return ['residue',
      `${canceledCount} canceled payout(s) on an account that is not paused now: a ` +
      'pause was lifted and the canceled payouts were never re-issued'];
  }

  return ['healthy', 'not paused'];
}

async function get(key, path, { account, ...params } = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const headers = { Authorization: `Bearer ${key}` };
  if (account) headers['Stripe-Account'] = account;
  const res = await fetch(url, { headers });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function* accounts(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/accounts', params);
    const data = page.data ?? [];
    for (const acct of data) {
      yield acct;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
    params.starting_after = data[data.length - 1].id;
  }
}

/**
 * Count canceled payouts for one account and find the oldest. A pause holds
 * in-flight payouts as pending for up to ten days and then cancels them, so this
 * is the paper trail. Failed payouts are a different problem and are not counted.
 */
async function canceledPayouts(key, accountId) {
  let count = 0;
  let oldest = null;
  const params = { status: 'canceled', limit: 100, account: accountId };
  for (;;) {
    const page = await get(key, '/payouts', params);
    const data = page.data ?? [];
    for (const payout of data) {
      count += 1;
      if (payout.created !== undefined && (oldest === null || payout.created < oldest)) {
        oldest = payout.created;
      }
    }
    if (data.length === 0 || !page.has_more) return [count, oldest];
    params.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const everywhere = process.argv.includes('--check-canceled-everywhere');
  const now = Math.floor(Date.now() / 1000);
  const counts = new Map();
  let scanned = 0;

  for await (const acct of accounts(key)) {
    scanned += 1;
    const paused = (acct.requirements ?? {}).disabled_reason === PAUSED;
    const [count, oldest] = (paused || everywhere)
      ? await canceledPayouts(key, acct.id) : [0, null];

    const [state, detail] = verdict(acct, count, oldest, now);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'healthy' || state === 'other-reason') continue;
    console.warn(`${acct.id ?? 'acct_?'}  ${state.padEnd(8)} ${detail}`);
  }

  const paused = counts.get('paused') ?? 0;
  const residue = counts.get('residue') ?? 0;
  console.log(`${scanned} account(s): ${paused} paused by the platform, ` +
    `${residue} with canceled payouts to re-issue`);

  if (paused) {
    console.warn('  repair: Dashboard, Connect, Connected accounts, open the account, ' +
                 'unpause payments or payouts. There is no v1 API for it.');
    console.warn('  then: re-read the account and confirm payouts_enabled is true and ' +
                 'disabled_reason is gone');
    console.warn('  reconcile: every paused account should map to an OPEN ' +
                 'investigation. The ones that do not are the finding.');
  }
  if (paused || residue) {
    console.warn('  note: unpausing does not replay canceled payouts. The balance ' +
                 'waits for the next scheduled payout, or forever on a manual schedule.');
    process.exitCode = 1;
  }
  if (!everywhere) {
    console.log('  canceled payouts were only checked on paused accounts; ' +
                '--check-canceled-everywhere widens it');
  }
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that earns its place is the one asserting a rejected or past-due account does <em>not</em> come back as paused. Everything else in this check is a string comparison; the value is in refusing to claim accounts that belong to a different repair, since the whole failure mode being described here started with somebody treating a pause as a missing field.",
"test_py_file": "test_stripe_platform_paused.py",
"test_py": '''from stripe_platform_paused import verdict

NOW = 1767225600  # 2026-01-01T00:00:00Z


def account(reason=None, charges=True, payouts=True):
    return {"id": "acct_1", "charges_enabled": charges, "payouts_enabled": payouts,
            "requirements": {"disabled_reason": reason}}


def test_a_normal_account_is_healthy():
    assert verdict(account(), 0, None, NOW)[0] == "healthy"


def test_platform_paused_is_named_and_says_which_side_is_off():
    state, detail = verdict(account("platform_paused", charges=True, payouts=False),
                            0, None, NOW)
    assert state == "paused"
    assert "payouts off" in detail
    assert "no API call reverses this" in detail


def test_a_pause_on_both_sides_says_both():
    _, detail = verdict(account("platform_paused", charges=False, payouts=False),
                        0, None, NOW)
    assert "charges and payouts off" in detail


def test_canceled_payouts_date_the_pause():
    _, detail = verdict(account("platform_paused", payouts=False),
                        4, NOW - 174 * 86400, NOW)
    assert "4 canceled payout(s)" in detail
    assert "at least 174 day(s)" in detail


def test_other_disabled_reasons_are_not_claimed_by_this_check():
    # The failure this note describes starts with somebody treating a pause as a
    # missing field. Doing the reverse is just as wrong.
    for reason in ("requirements.past_due", "rejected.fraud", "under_review",
                   "requirements.pending_verification"):
        state, detail = verdict(account(reason, charges=False, payouts=False),
                                0, None, NOW)
        assert state == "other-reason", reason
        assert reason in detail


def test_canceled_payouts_without_a_pause_are_residue():
    state, detail = verdict(account(), 3, NOW - 200 * 86400, NOW)
    assert state == "residue"
    assert "never re-issued" in detail
''',
"test_js_file": "stripe-platform-paused.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-platform-paused.mjs';

const NOW = 1767225600; // 2026-01-01T00:00:00Z

const account = (reason = null, charges = true, payouts = true) => ({
  id: 'acct_1',
  charges_enabled: charges,
  payouts_enabled: payouts,
  requirements: { disabled_reason: reason },
});

test('a normal account is healthy', () => {
  assert.equal(verdict(account(), 0, null, NOW)[0], 'healthy');
});

test('platform paused is named and says which side is off', () => {
  const [state, detail] = verdict(account('platform_paused', true, false), 0, null, NOW);
  assert.equal(state, 'paused');
  assert.match(detail, /payouts off/);
  assert.match(detail, /no API call reverses this/);
});

test('a pause on both sides says both', () => {
  const [, detail] = verdict(account('platform_paused', false, false), 0, null, NOW);
  assert.match(detail, /charges and payouts off/);
});

test('canceled payouts date the pause', () => {
  const [, detail] = verdict(account('platform_paused', true, false),
    4, NOW - 174 * 86400, NOW);
  assert.match(detail, /4 canceled payout\\(s\\)/);
  assert.match(detail, /at least 174 day\\(s\\)/);
});

test('other disabled reasons are not claimed by this check', () => {
  // The failure this note describes starts with somebody treating a pause as a
  // missing field. Doing the reverse is just as wrong.
  for (const reason of ['requirements.past_due', 'rejected.fraud', 'under_review',
    'requirements.pending_verification']) {
    const [state, detail] = verdict(account(reason, false, false), 0, null, NOW);
    assert.equal(state, 'other-reason', reason);
    assert.ok(detail.includes(reason));
  }
});

test('canceled payouts without a pause are residue', () => {
  const [state, detail] = verdict(account(), 3, NOW - 200 * 86400, NOW);
  assert.equal(state, 'residue');
  assert.match(detail, /never re-issued/);
});
''',
"faq": [
 ("Is there really no API to unpause an account?",
  "Not in v1. Pausing and unpausing payments or payouts on a connected account is a Dashboard control, found on the account under Connect, Connected accounts, and it is not supported on Accounts v2 at all. That is why this script prints a Dashboard path rather than a call: there is no call to print."),
 ("Why are the payouts canceled rather than failed?",
  "Because they never left. A payout already in flight when the pause lands sits at pending for up to ten days, and if the pause is still on when that runs out Stripe cancels it and returns the funds to the connected balance. Nothing was rejected by a bank, so nothing appears in a failed-payout report."),
 ("Does the seller know they have been paused?",
  "Not reliably. A Custom account gets no notification from Stripe, so the platform is the only party that can tell them. If only payouts were paused, the seller keeps taking payments and their revenue dashboards look completely normal, which is why these pauses can outlive the investigations that caused them by months."),
 ("Will unpausing send the money that piled up?",
  "Eventually, and not automatically. The canceled payouts stay canceled. Once the account is live again the accumulated balance goes out on the next scheduled payout, and on a manual payout schedule it goes out only when somebody creates one, so an unpaused account can still be sitting on months of funds."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Connected accounts and Payouts is enough. The script reads account state and counts canceled payouts; the pause itself can only be lifted by a person in the Dashboard, which is the strongest possible guarantee that a monitoring script will not do it by accident."),
],
"related": [
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
 ("/stripe/connect-reserved-balance-growing/", "A connected account's reserved balance keeps growing"),
 ("/stripe/payout-schedule-left-on-manual/", "Payout schedule was left on manual and funds pile up"),
],
"citations": [CITE_PAUSING, CITE_ACCOUNT_OBJECT, CITE_PAYOUT_OBJECT, CITE_PAYOUTS_CONNECT],
},

{
"slug": "issuing-cardholder-requirements-past-due",
"title": "Cardholder requirements.past_due keeps every card inactive",
"description": "The card will not activate and every authorization declines instantly. What is blocking it lives on the cardholder, and often it is only a terms checkbox.",
"h1": "cardholder requirements.past_due keeps every card inactive",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe issuing card inactive", "cardholder requirements past_due",
             "card_inactive decline", "issuing user_terms_acceptance",
             "stripe issuing activation failed"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The card was issued in the morning, handed to an employee at lunch, and declined at a card reader by two. The dashboard shows the card as <code>inactive</code>. Activating it does nothing. Nothing about the card object explains why, because the reason is not on the card &mdash; it is a list of two missing strings on the cardholder the card belongs to, one of which is an IP address.",
"short_answer": """<p>Read the cardholder, not the card. <code>GET /v1/issuing/cardholders?limit=100</code> and flag any with <code>requirements.past_due</code> non-empty or <code>requirements.disabled_reason</code> set. While those are outstanding, Stripe blocks activation, so every card attached to that cardholder stays <code>inactive</code> and every authorization declines.</p>
<p>Sort the missing fields before you write the ticket. A <code>past_due</code> list containing only <code>individual.card_issuing.user_terms_acceptance.ip</code> and <code>.date</code> is not a verification problem at all &mdash; it is a terms acceptance that was never captured, and the fix is a checkbox plus the IP and timestamp from the moment they accepted. Confirm the impact with <code>GET /v1/issuing/authorizations</code> and read <code>request_history[].reason</code>, which is where <code>card_inactive</code> actually appears.</p>""",
"problem": """<p>The confusion is structural: the object that fails is not the object that is wrong. Someone is holding a card that does not work, so they look at the card, and the card says <code>inactive</code> with no explanation attached. Setting it to active either errors or silently stays inactive. Three objects are involved &mdash; the authorization that declined, the card that is inactive, and the cardholder that is blocking it &mdash; and only the third one carries the reason.</p>
<p>The declines make it worse by being instant and total. There is no partial degradation, no retry that succeeds, no pattern to narrow down. Every transaction on every card belonging to that cardholder fails at the terminal, which reads like a broken card program rather than a missing form field, and gets escalated accordingly.</p>""",
"why": """<p><strong>Cards default to inactive, so nothing looks unusual at first.</strong> A newly issued card is <code>inactive</code> by design and is meant to be activated by a call. The failure is that the activation does not take, and there is no error surfaced on the card object explaining that a different object is holding it.</p>
<p><strong>The commonest missing fields are not identity documents.</strong> <code>individual.card_issuing.user_terms_acceptance.ip</code> and <code>.date</code> record that the cardholder accepted the Authorized User Terms, and they have to be captured at the moment of acceptance. An integration that collects a name, a date of birth and an address, but never presents the terms, produces cardholders that look fully verified and are still blocked.</p>
<p><strong>The decline reason is in a nested array.</strong> An authorization carries <code>approved: false</code>, and the actual reason &mdash; <code>card_inactive</code>, <code>cardholder_inactive</code>, <code>verification_failed</code>, <code>insufficient_funds</code>, <code>spending_controls</code>, <code>webhook_timeout</code> &mdash; lives in <code>request_history[].reason</code>. Anything reading only the top-level fields sees that it declined and not why, and those six reasons have six unrelated repairs.</p>
<p><strong>A clean cardholder with inactive cards is a different bug.</strong> If nothing is past due and the cards are still inactive, nobody ever called activation. That is a gap in your issuing flow, not a Stripe block, and it needs saying separately or the two get conflated forever.</p>""",
"steps": [
 {"h": "Start from the cardholder list, not from the complaint",
  "body": """<p><code>GET /v1/issuing/cardholders?limit=100</code>, reading <code>status</code>, <code>requirements.past_due</code> and <code>requirements.disabled_reason</code>. Doing this as a sweep rather than per-complaint matters, because cardholders created by the same onboarding flow share the same missing field, and finding one usually means finding all of them.</p>"""},
 {"h": "Separate a terms gap from an identity gap",
  "body": """<p>If every entry in <code>past_due</code> sits under <code>individual.card_issuing.user_terms_acceptance</code>, no document is missing and nothing needs verifying: the cardholder was never shown the Authorized User Terms. That is a UI change and a stored IP and timestamp, which is a completely different piece of work from collecting a date of birth or an address.</p>"""},
 {"h": "Correlate the inactive cards",
  "body": """<p><code>GET /v1/issuing/cards?status=inactive&amp;limit=100</code>, grouped by <code>cardholder.id</code>. One blocked cardholder with eleven cards behind it is a bigger number than eleven separate tickets suggests, and the count is what gets the fix prioritised.</p>"""},
 {"h": "Read request_history on the declines",
  "body": """<p><code>GET /v1/issuing/authorizations?limit=100</code>, keep <code>approved: false</code>, and tally <code>request_history[].reason</code>. If the reasons are <code>card_inactive</code> you have confirmed the chain end to end. If they are <code>insufficient_funds</code> or <code>spending_controls</code>, the cardholder requirements are a real finding but they are not what declined this transaction, and fixing them will not stop the declines.</p>"""},
 {"h": "Collect the fields, then activate the cards",
  "body": """<p>Update the cardholder with everything in <code>past_due</code>, including the terms acceptance IP and date captured at acceptance time, then set each card to <code>active</code>. Activation before the requirements clear does not stick, so the order is not optional.</p>"""},
],
"verify": """<p>Re-run the script. No cardholder should have past-due requirements, and any card still inactive should be one nobody has issued to a person yet.</p>
<pre><code class="language-bash">python3 stripe_issuing_cardholder_requirements.py
# 24 cardholder(s), 31 inactive card(s): 0 blocked, 0 dormant</code></pre>""",
"code_intro": "Three GETs: cardholders, inactive cards grouped by cardholder, and recent authorizations for the decline reasons. Two pure functions carry the judgement &mdash; one that sorts a cardholder by what is actually missing, and one that turns a decline reason into the repair it implies &mdash; because a terms checkbox and a passport scan are the same shape of finding and completely different work.",
"py_file": "stripe_issuing_cardholder_requirements.py",
"py": '''"""Report Issuing cardholders whose requirements keep their cards inactive.

Read only. Three GET requests and no writes: give this a RESTRICTED key with
read access to Issuing cardholders, Issuing cards and Issuing authorizations.
The repair is printed, never performed, because this script holds a credential
to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_issuing_cardholder_requirements")

API = "https://api.stripe.com/v1"

# Fields under this prefix record that the cardholder accepted the Authorized
# User Terms. They are past due far more often than any identity field, and they
# are not a verification problem: nothing needs checking, the terms were never
# shown.
TERMS_PREFIX = "individual.card_issuing.user_terms_acceptance"

# What each decline reason actually implies. Six reasons, six unrelated repairs,
# and all six arrive as approved: false with nothing else to tell them apart.
DECLINE_HINTS = {
    "card_inactive":
        "the card itself is not active. Activation is blocked while the cardholder "
        "has past-due requirements, so check the cardholder first.",
    "cardholder_inactive":
        "the cardholder is not active. Its own status, not the card's, is the block.",
    "verification_failed":
        "the cardholder's identity verification did not pass. Collecting the same "
        "details again will not change it; read the requirements for what failed.",
    "insufficient_funds":
        "the Issuing balance is empty, which has nothing to do with requirements. "
        "Read balance.issuing.available and top it up.",
    "spending_controls":
        "a spending control on the card or cardholder rejected this. The card is "
        "working exactly as configured.",
    "webhook_timeout":
        "your real-time authorization endpoint did not answer in time, so Stripe "
        "applied the default. This is your latency, not a cardholder problem.",
}


def explain_decline(reason):
    """Turn an authorization decline reason into its repair. Pure.

    Unknown reasons come back named rather than swallowed: the enum grows, and a
    decline reported as "unknown reason" is still more useful than one silently
    dropped from the tally.
    """
    if reason in DECLINE_HINTS:
        return DECLINE_HINTS[reason]
    return "unrecognised reason %r: read the authorization's request_history" % (reason,)


def verdict(cardholder, inactive_cards):
    """Classify one cardholder. Pure. Returns (state, detail).

    `inactive_cards` is how many of its cards are sitting inactive. The states
    separate three different jobs: capture a terms acceptance, collect identity
    fields, or go and find out why your own code never called activation.
    """
    reqs = cardholder.get("requirements") or {}
    past_due = [f for f in (reqs.get("past_due") or []) if f]
    reason = reqs.get("disabled_reason")
    cards = " (%d inactive card(s) behind it)" % inactive_cards if inactive_cards else ""

    if past_due:
        if all(f.startswith(TERMS_PREFIX) for f in past_due):
            return ("blocked-terms",
                    "past_due is only terms acceptance: %s%s. Nothing needs "
                    "verifying. Capture the IP and the timestamp at the moment the "
                    "cardholder accepts the Authorized User Terms."
                    % (", ".join(past_due), cards))
        return ("blocked-identity",
                "%d field(s) past due: %s%s. Activation stays blocked until every "
                "one is supplied." % (len(past_due), ", ".join(past_due[:4]), cards))

    if reason:
        return ("disabled",
                "disabled_reason %s with nothing in past_due%s: read the "
                "requirements hash before collecting anything" % (reason, cards))

    if cardholder.get("status") != "active":
        return ("inactive-cardholder",
                "status %r with no outstanding requirements%s: this was set "
                "deliberately, so find out by whom"
                % (cardholder.get("status"), cards))

    if inactive_cards:
        return ("dormant",
                "cardholder is clean and %d card(s) are still inactive: nothing is "
                "blocking activation, so nobody ever called it" % inactive_cards)

    return ("healthy", "active, nothing past due")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def paginate(session, path, cap, **params):
    """Yield every object from a list endpoint, up to `cap`."""
    seen = 0
    params = dict(params, limit=100)
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for item in data:
            yield item
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-authorizations", type=int, default=1000,
                    help="how many recent authorizations to read for decline reasons")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    inactive = {}
    total_inactive = 0
    for card in paginate(s, "/issuing/cards", 5000, status="inactive"):
        total_inactive += 1
        holder = (card.get("cardholder") or {}).get("id")
        if holder:
            inactive[holder] = inactive.get(holder, 0) + 1

    counts = {}
    cardholders = 0
    for holder in paginate(s, "/issuing/cardholders", 5000):
        cardholders += 1
        state, detail = verdict(holder, inactive.get(holder.get("id"), 0))
        counts[state] = counts.get(state, 0) + 1
        if state == "healthy":
            continue
        log.warning("%s  %-18s %s", holder.get("id", "ich_?"), state, detail)

    reasons = {}
    for auth in paginate(s, "/issuing/authorizations", args.max_authorizations):
        if auth.get("approved"):
            continue
        for attempt in auth.get("request_history") or []:
            reason = attempt.get("reason")
            reasons[reason] = reasons.get(reason, 0) + 1

    blocked = counts.get("blocked-terms", 0) + counts.get("blocked-identity", 0)
    log.info("%d cardholder(s), %d inactive card(s): %d blocked, %d dormant",
             cardholders, total_inactive, blocked, counts.get("dormant", 0))

    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        log.warning("  %d decline(s) with reason %s: %s",
                    count, reason, explain_decline(reason))

    if counts.get("blocked-terms"):
        log.warning("  repair: POST %s/issuing/cardholders/{ich_id} with", API)
        log.warning("  individual[card_issuing][user_terms_acceptance][date] and [ip], "
                    "captured when the cardholder accepted the terms")
    if counts.get("blocked-identity"):
        log.warning("  repair: POST %s/issuing/cardholders/{ich_id} supplying every "
                    "field listed in requirements.past_due", API)
    if blocked or counts.get("dormant"):
        log.warning("  then: POST %s/issuing/cards/{ic_id} with status=active. "
                    "Activation before the requirements clear does not stick.", API)
    return 1 if (blocked or counts.get("dormant") or counts.get("disabled")
                 or counts.get("inactive-cardholder")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-issuing-cardholder-requirements.mjs",
"js": '''/**
 * Report Issuing cardholders whose requirements keep their cards inactive.
 *
 * Read only. Three GET requests and no writes: give this a RESTRICTED key with
 * read access to Issuing cardholders, Issuing cards and Issuing authorizations.
 * The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Fields under this prefix record that the cardholder accepted the Authorized
// User Terms. They are past due far more often than any identity field, and they
// are not a verification problem: nothing needs checking, the terms were never
// shown.
const TERMS_PREFIX = 'individual.card_issuing.user_terms_acceptance';

// What each decline reason actually implies. Six reasons, six unrelated repairs.
const DECLINE_HINTS = {
  card_inactive:
    'the card itself is not active. Activation is blocked while the cardholder ' +
    'has past-due requirements, so check the cardholder first.',
  cardholder_inactive:
    "the cardholder is not active. Its own status, not the card's, is the block.",
  verification_failed:
    "the cardholder's identity verification did not pass. Collecting the same " +
    'details again will not change it; read the requirements for what failed.',
  insufficient_funds:
    'the Issuing balance is empty, which has nothing to do with requirements. ' +
    'Read balance.issuing.available and top it up.',
  spending_controls:
    'a spending control on the card or cardholder rejected this. The card is ' +
    'working exactly as configured.',
  webhook_timeout:
    'your real-time authorization endpoint did not answer in time, so Stripe ' +
    'applied the default. This is your latency, not a cardholder problem.',
};

/** Turn an authorization decline reason into its repair. Pure. */
export function explainDecline(reason) {
  if (Object.prototype.hasOwnProperty.call(DECLINE_HINTS, reason)) {
    return DECLINE_HINTS[reason];
  }
  return `unrecognised reason ${JSON.stringify(reason)}: read the authorization's ` +
    'request_history';
}

/**
 * Classify one cardholder. Pure. Returns [state, detail].
 * The states separate three different jobs: capture a terms acceptance, collect
 * identity fields, or find out why your own code never called activation.
 */
export function verdict(cardholder, inactiveCards) {
  const reqs = cardholder.requirements ?? {};
  const pastDue = (reqs.past_due ?? []).filter(Boolean);
  const reason = reqs.disabled_reason ?? null;
  const cards = inactiveCards ? ` (${inactiveCards} inactive card(s) behind it)` : '';

  if (pastDue.length) {
    if (pastDue.every((f) => f.startsWith(TERMS_PREFIX))) {
      return ['blocked-terms',
        `past_due is only terms acceptance: ${pastDue.join(', ')}${cards}. Nothing ` +
        'needs verifying. Capture the IP and the timestamp at the moment the ' +
        'cardholder accepts the Authorized User Terms.'];
    }
    return ['blocked-identity',
      `${pastDue.length} field(s) past due: ${pastDue.slice(0, 4).join(', ')}${cards}. ` +
      'Activation stays blocked until every one is supplied.'];
  }

  if (reason) {
    return ['disabled',
      `disabled_reason ${reason} with nothing in past_due${cards}: read the ` +
      'requirements hash before collecting anything'];
  }

  if (cardholder.status !== 'active') {
    return ['inactive-cardholder',
      `status ${JSON.stringify(cardholder.status)} with no outstanding ` +
      `requirements${cards}: this was set deliberately, so find out by whom`];
  }

  if (inactiveCards) {
    return ['dormant',
      `cardholder is clean and ${inactiveCards} card(s) are still inactive: nothing ` +
      'is blocking activation, so nobody ever called it'];
  }

  return ['healthy', 'active, nothing past due'];
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

async function* paginate(key, path, cap, extra = {}) {
  let seen = 0;
  const params = { ...extra, limit: 100 };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const item of data) {
      yield item;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
    params.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const inactive = new Map();
  let totalInactive = 0;
  for await (const card of paginate(key, '/issuing/cards', 5000, { status: 'inactive' })) {
    totalInactive += 1;
    const holder = (card.cardholder ?? {}).id;
    if (holder) inactive.set(holder, (inactive.get(holder) ?? 0) + 1);
  }

  const counts = new Map();
  let cardholders = 0;
  for await (const holder of paginate(key, '/issuing/cardholders', 5000)) {
    cardholders += 1;
    const [state, detail] = verdict(holder, inactive.get(holder.id) ?? 0);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'healthy') continue;
    console.warn(`${holder.id ?? 'ich_?'}  ${state.padEnd(18)} ${detail}`);
  }

  const reasons = new Map();
  for await (const auth of paginate(key, '/issuing/authorizations', 1000)) {
    if (auth.approved) continue;
    for (const attempt of auth.request_history ?? []) {
      reasons.set(attempt.reason, (reasons.get(attempt.reason) ?? 0) + 1);
    }
  }

  const blocked = (counts.get('blocked-terms') ?? 0) + (counts.get('blocked-identity') ?? 0);
  console.log(`${cardholders} cardholder(s), ${totalInactive} inactive card(s): ` +
    `${blocked} blocked, ${counts.get('dormant') ?? 0} dormant`);

  for (const [reason, count] of [...reasons].sort((a, b) => b[1] - a[1])) {
    console.warn(`  ${count} decline(s) with reason ${reason}: ${explainDecline(reason)}`);
  }

  if (counts.get('blocked-terms')) {
    console.warn(`  repair: POST ${API}/issuing/cardholders/{ich_id} with`);
    console.warn('  individual[card_issuing][user_terms_acceptance][date] and [ip], ' +
                 'captured when the cardholder accepted the terms');
  }
  if (counts.get('blocked-identity')) {
    console.warn(`  repair: POST ${API}/issuing/cardholders/{ich_id} supplying every ` +
                 'field listed in requirements.past_due');
  }
  if (blocked || counts.get('dormant')) {
    console.warn(`  then: POST ${API}/issuing/cards/{ic_id} with status=active. ` +
                 'Activation before the requirements clear does not stick.');
  }
  if (blocked || counts.get('dormant') || counts.get('disabled')
      || counts.get('inactive-cardholder')) {
    process.exitCode = 1;
  }
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The split that matters is terms acceptance against everything else, so that is what most of these assert. A cardholder blocked only on <code>user_terms_acceptance</code> needs a checkbox and two stored values; one blocked on identity fields needs a person to send documents. Reporting them identically is how a two-hour fix waits three weeks behind a KYC queue.",
"test_py_file": "test_stripe_issuing_cardholder_requirements.py",
"test_py": '''from stripe_issuing_cardholder_requirements import explain_decline, verdict

TERMS = ["individual.card_issuing.user_terms_acceptance.ip",
         "individual.card_issuing.user_terms_acceptance.date"]


def cardholder(past_due=(), reason=None, status="active"):
    return {"id": "ich_1", "status": status,
            "requirements": {"past_due": list(past_due), "disabled_reason": reason}}


def test_a_clean_active_cardholder_with_no_inactive_cards_is_healthy():
    assert verdict(cardholder(), 0)[0] == "healthy"


def test_terms_only_is_not_a_verification_problem():
    state, detail = verdict(cardholder(TERMS), 3)
    assert state == "blocked-terms"
    assert "Nothing needs verifying" in detail
    assert "3 inactive card(s)" in detail


def test_one_identity_field_alongside_terms_is_an_identity_block():
    # The distinction is all-or-nothing on purpose: a passport scan in the list
    # means somebody has to send documents, whatever else is in there with it.
    state, _ = verdict(cardholder(TERMS + ["individual.dob.day"]), 1)
    assert state == "blocked-identity"


def test_identity_fields_are_named_in_the_detail():
    state, detail = verdict(
        cardholder(["individual.first_name", "individual.last_name"]), 0)
    assert state == "blocked-identity"
    assert "individual.first_name" in detail


def test_a_clean_cardholder_with_inactive_cards_is_a_gap_in_your_own_flow():
    state, detail = verdict(cardholder(), 4)
    assert state == "dormant"
    assert "nobody ever called it" in detail


def test_a_disabled_reason_without_past_due_is_reported_separately():
    state, _ = verdict(cardholder(reason="listed"), 2)
    assert state == "disabled"


def test_an_inactive_cardholder_with_nothing_outstanding_says_so():
    state, detail = verdict(cardholder(status="inactive"), 1)
    assert state == "inactive-cardholder"
    assert "deliberately" in detail


def test_every_known_decline_reason_gets_its_own_repair():
    hints = {r: explain_decline(r) for r in
             ("card_inactive", "cardholder_inactive", "verification_failed",
              "insufficient_funds", "spending_controls", "webhook_timeout")}
    assert len(set(hints.values())) == 6
    assert "top it up" in hints["insufficient_funds"]
    assert "latency" in hints["webhook_timeout"]


def test_an_unknown_decline_reason_is_named_not_swallowed():
    assert "some_new_reason" in explain_decline("some_new_reason")
''',
"test_js_file": "stripe-issuing-cardholder-requirements.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { explainDecline, verdict } from './stripe-issuing-cardholder-requirements.mjs';

const TERMS = ['individual.card_issuing.user_terms_acceptance.ip',
  'individual.card_issuing.user_terms_acceptance.date'];

const cardholder = (pastDue = [], reason = null, status = 'active') => ({
  id: 'ich_1', status, requirements: { past_due: pastDue, disabled_reason: reason },
});

test('a clean active cardholder with no inactive cards is healthy', () => {
  assert.equal(verdict(cardholder(), 0)[0], 'healthy');
});

test('terms only is not a verification problem', () => {
  const [state, detail] = verdict(cardholder(TERMS), 3);
  assert.equal(state, 'blocked-terms');
  assert.match(detail, /Nothing needs verifying/);
  assert.match(detail, /3 inactive card\\(s\\)/);
});

test('one identity field alongside terms is an identity block', () => {
  // All-or-nothing on purpose: a passport scan in the list means somebody has to
  // send documents, whatever else is in there with it.
  assert.equal(verdict(cardholder([...TERMS, 'individual.dob.day']), 1)[0],
    'blocked-identity');
});

test('identity fields are named in the detail', () => {
  const [state, detail] = verdict(
    cardholder(['individual.first_name', 'individual.last_name']), 0);
  assert.equal(state, 'blocked-identity');
  assert.match(detail, /individual.first_name/);
});

test('a clean cardholder with inactive cards is a gap in your own flow', () => {
  const [state, detail] = verdict(cardholder(), 4);
  assert.equal(state, 'dormant');
  assert.match(detail, /nobody ever called it/);
});

test('a disabled reason without past due is reported separately', () => {
  assert.equal(verdict(cardholder([], 'listed'), 2)[0], 'disabled');
});

test('an inactive cardholder with nothing outstanding says so', () => {
  const [state, detail] = verdict(cardholder([], null, 'inactive'), 1);
  assert.equal(state, 'inactive-cardholder');
  assert.match(detail, /deliberately/);
});

test('every known decline reason gets its own repair', () => {
  const reasons = ['card_inactive', 'cardholder_inactive', 'verification_failed',
    'insufficient_funds', 'spending_controls', 'webhook_timeout'];
  const hints = reasons.map(explainDecline);
  assert.equal(new Set(hints).size, 6);
  assert.match(explainDecline('insufficient_funds'), /top it up/);
  assert.match(explainDecline('webhook_timeout'), /latency/);
});

test('an unknown decline reason is named not swallowed', () => {
  assert.match(explainDecline('some_new_reason'), /some_new_reason/);
});
''',
"faq": [
 ("Why does setting the card to active not work?",
  "Because the block is on the cardholder. While requirements.past_due has anything in it, Stripe will not let cards belonging to that cardholder activate, so the call either errors or the card comes back inactive. Supply the missing fields on the cardholder first, then activate; the order is what makes it stick."),
 ("What are user_terms_acceptance.ip and .date?",
  "They record that the cardholder accepted the Authorized User Terms, and they have to be the real IP address and timestamp from the moment of acceptance rather than values filled in later. An integration that collects identity details but never presents the terms produces cardholders that look complete and cannot hold an active card."),
 ("Where do I actually see why an authorization declined?",
  "In request_history on the authorization. The top level tells you approved is false; the nested entries carry reason, which is where card_inactive, cardholder_inactive, verification_failed, insufficient_funds, spending_controls and webhook_timeout appear. Those six have six unrelated repairs, so the tally of reasons is the useful output rather than the count of declines."),
 ("The cardholder is clean but the cards are still inactive. What now?",
  "That is a gap in your own issuing flow rather than a Stripe block: nothing is preventing activation and nobody called it. It is worth reporting separately, because otherwise it hides inside the same list as the blocked cardholders and gets fixed by collecting fields that were never missing."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Issuing cardholders, cards and authorizations is enough. The script reads three lists and prints what to update; it cannot update a cardholder or activate a card, which is the right level of privilege for something that runs on a schedule."),
],
"related": [
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/person-requirements-outstanding/", "A person on the account has outstanding requirements"),
 ("/stripe/terminal-readers-offline/", "Terminal readers sit offline and take no payments"),
],
"citations": [CITE_CARDHOLDER_OBJECT, CITE_CARD_OBJECT, CITE_AUTHORIZATION_OBJECT, CITE_ISSUING_CARDS],
},

]
# end of batch AB
