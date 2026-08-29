#!/usr/bin/env python3
"""/stripe/ field notes, batch H — the writing.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair
for a human to run against a live payments account.
"""

CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")
CITE_VERSIONING = ("Webhook versioning — Stripe Docs",
                   "https://docs.stripe.com/webhooks/versioning")
CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")
CITE_WEBHOOK_UPDATE = ("Update a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/update")
CITE_WEBHOOK_CREATE = ("Create a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/create")
CITE_UPGRADES = ("Upgrade your API version — Stripe Docs",
                 "https://docs.stripe.com/upgrades")
CITE_API_VERSIONING = ("Versioning — Stripe API reference",
                       "https://docs.stripe.com/api/versioning")
CITE_IDEMPOTENCY = ("Idempotent requests — Stripe API reference",
                    "https://docs.stripe.com/api/idempotent_requests")
CITE_EVENT_OBJ = ("The event object — Stripe API reference",
                  "https://docs.stripe.com/api/events/object")
CITE_EVENTS_LIST = ("List all events — Stripe API reference",
                    "https://docs.stripe.com/api/events/list")
CITE_EVENT_TYPES = ("Types of events — Stripe API reference",
                    "https://docs.stripe.com/api/events/types")
CITE_SOURCES = ("Sources API — Stripe Docs", "https://docs.stripe.com/sources")
CITE_OLDER_APIS = ("Older payments APIs — Stripe Docs",
                   "https://docs.stripe.com/payments/older-apis")
CITE_PM_OBJ = ("The PaymentMethod object — Stripe API reference",
               "https://docs.stripe.com/api/payment_methods/object")
CITE_PM_LIST = ("List a customer's PaymentMethods — Stripe API reference",
                "https://docs.stripe.com/api/payment_methods/customer_list")
CITE_CARDS = ("Card payments overview — Stripe Docs",
              "https://docs.stripe.com/payments/cards/overview")
CITE_DECLINES = ("Decline codes — Stripe Docs",
                 "https://docs.stripe.com/declines/codes")

GUIDES = [

{
"slug": "endpoint-api-version-pinned-stale",
"title": "A webhook endpoint is pinned to an ancient api_version",
"description": "Fields the SDK expects are missing from event.data.object, but re-fetching works. The endpoint renders events at the version it was created with.",
"h1": "a webhook endpoint is pinned to an ancient api_version",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe webhook api_version", "stripe endpoint pinned version",
             "getDataObjectDeserializer empty", "stripe event data object null",
             "stripe webhook versioning"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The signature verifies. The event arrives. And then the object inside it is missing half the fields the current SDK expects, so the deserializer hands back an empty <code>Optional</code> or a null cast, and nobody throws anything. Fetching the same object straight from the API returns it complete, which makes the whole thing look like Stripe sending empty payloads.",
"short_answer": """<p>Read <code>GET /v1/webhook_endpoints</code> and look at <code>api_version</code> on each one. Treat both <code>null</code> and the empty string as <em>unpinned</em>; an <code>is not None</code> test quietly reports every unpinned endpoint as pinned. For the rest, compare the <code>YYYY-MM-DD</code> prefix against the current release line and hard-flag anything before <code>2024-09-30</code>, the Acacia boundary.</p>
<p>Then note the part that catches people out: <code>api_version</code> is not updatable. <code>POST /v1/webhook_endpoints/{id}</code> accepts <code>url</code>, <code>enabled_events</code>, <code>description</code>, <code>metadata</code> and <code>disabled</code>, and nothing else. Fixing this means creating a second endpoint and retiring the first.</p>""",
"problem": """<p>What makes this expensive is the order the failure happens in. Signature verification passes, because the signature covers the raw bytes and has nothing to do with the payload shape. The handler is entered. Only then does the typed deserializer look at a JSON body rendered two years ago, fail to find the fields it was generated against, and return an empty object rather than an error. In stripe-java that is <code>getDataObjectDeserializer().getObject()</code> giving you an empty <code>Optional</code>; in stripe-dotnet it is <code>Data.Object as PaymentIntent</code> evaluating to <code>null</code> without throwing.</p>
<p>So the log shows a received, verified, 200-returning webhook that did nothing. The first debugging move anyone makes is to re-fetch the object by ID, which works perfectly, because that request is rendered at the SDK's own version. Every piece of evidence points at the payload rather than at a configuration field nobody remembers setting.</p>""",
"why": """<p><strong>The version is frozen at creation and there is no field to move it.</strong> When an endpoint is created with an explicit <code>api_version</code>, every event it is ever sent is rendered at that version, forever, regardless of what the account default does afterwards. Unlike almost everything else on the object, this one cannot be edited, so the natural repair &mdash; open the endpoint, change the version, save &mdash; does not exist.</p>
<p><strong>Statically typed SDKs degrade instead of failing.</strong> stripe-node hands you a plain object and your code reads whatever is there. stripe-java, stripe-dotnet and stripe-go deserialize against the schema they were generated for, and when a field has moved or been renamed the safe behaviour they chose is an empty result. That is the right call for resilience and the wrong one for discovery: an exception would have named the problem in the first stack trace.</p>
<p><strong>The account default moves and the pin does not.</strong> Upgrading the account version is a deliberate act with a changelog and a 72-hour rollback window, and it is the thing people plan for. Pinned endpoints sit outside that upgrade entirely. An account can be fully current while an endpoint created in 2022 keeps rendering 2022 payloads into current code.</p>
<p><strong>Unpinned reads as <code>null</code> or as an empty string, depending on the endpoint.</strong> Both mean the same thing &mdash; inherit the account default &mdash; and a check that only tests one of them classifies half the unpinned endpoints as pinned to nothing, then compares that against a date and reports nonsense.</p>""",
"steps": [
 {"h": "List the endpoints and read api_version on each",
  "body": """<p>One GET. <code>GET /v1/webhook_endpoints?limit=100</code> returns <code>api_version</code> per endpoint. Normalise <code>null</code> and <code>""</code> to a single sentinel before you compare anything, because they are the same state written two ways.</p>"""},
 {"h": "Compare the date prefix, not the full string",
  "body": """<p>A pinned version looks like <code>2024-09-30.acacia</code>: an ISO date, then the release-line name. Only the date part is orderable, and because it is ISO you can compare it as a string. Anything before <code>2024-09-30</code> predates Acacia, and every release line since has carried breaking changes.</p>"""},
 {"h": "Check what the SDK is actually generated for",
  "body": """<p>The pin is only a problem relative to the code reading it. An endpoint pinned to the same version your SDK targets is correct and deliberate. Print both numbers next to each other; the gap is the finding, not the pin.</p>"""},
 {"h": "Migrate with a second endpoint, because the field is immutable",
  "body": """<p><code>POST /v1/webhook_endpoints</code> with the same <code>url</code> plus a distinguishing query parameter, the same <code>enabled_events</code>, and the target <code>api_version</code>. Both endpoints deliver for a while. Have the route ignore-and-200 the new shape until the code that understands it ships.</p>"""},
 {"h": "Disable the old endpoint once, and only once, the new one is live",
  "body": """<p><code>POST /v1/webhook_endpoints/{old_id}</code> with <code>disabled=true</code>. Do this deliberately and soon: two enabled endpoints on one URL is a different failure that delivers every event twice, and it is the usual residue of a migration that stopped halfway.</p>"""},
],
"verify": """<p>Re-run the script. Every endpoint should report either the current line or a pin you chose on purpose.</p>
<pre><code class="language-bash">python3 stripe_endpoint_api_version.py
# current    https://example.com/stripe/webhook  pinned to 2025-09-30, on the current line</code></pre>""",
"code_intro": "One GET and nothing else &mdash; a restricted key with read access to Webhook Endpoints is enough, and is what you should give it. The classification is a pure function over a single string, because the two ways to get this wrong are both string handling: treating <code>\"\"</code> as a pinned version, and comparing <code>2024-09-30.acacia</code> to <code>2025-09-30.clover</code> without trimming to the date first.",
"py_file": "stripe_endpoint_api_version.py",
"py": '''"""Report Stripe webhook endpoints pinned to an outdated api_version.

Read only. One GET and no writes: give this a RESTRICTED key with read access
to Webhook Endpoints. The migration is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_endpoint_api_version")

API = "https://api.stripe.com/v1"

CURRENT_LINE = "2025-09-30"  # Clover
ACACIA = "2024-09-30"        # every line from here on carried breaking changes
DATE = re.compile(r"^(\\d{4}-\\d{2}-\\d{2})")


def verdict(api_version, current_line=CURRENT_LINE):
    """Classify one endpoint's pin. Pure, so the string handling can be tested.

    `api_version` is the raw field: None or "" for an unpinned endpoint, else
    something like "2024-09-30.acacia". Returns (state, detail).
    """
    if api_version is None or api_version == "":
        return ("unpinned",
                "no api_version: events render at the account default, which "
                "moves under this endpoint whenever the account is upgraded")
    m = DATE.match(str(api_version))
    if not m:
        return ("unreadable",
                "api_version %s has no YYYY-MM-DD prefix to compare"
                % str(api_version))
    date = m.group(1)
    if date < ACACIA:
        return ("ancient",
                "pinned to %s, before the %s Acacia line. Typed SDKs deserialize "
                "this into empty objects without throwing." % (date, ACACIA))
    if date < current_line:
        return ("stale",
                "pinned to %s, behind the current %s line. Check the changelog "
                "for the fields your handler reads." % (date, current_line))
    return ("current", "pinned to %s, on the current line" % date)


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
    ap.add_argument("--current-line", default=CURRENT_LINE,
                    help="the release line your SDK targets, as YYYY-MM-DD")
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

    bad = 0
    for ep in eps:
        state, detail = verdict(ep.get("api_version"), args.current_line)
        line = "%-10s %s  %s" % (state, ep.get("url", "?"), detail)
        if state == "current":
            log.info(line)
            continue
        if state == "unpinned":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  api_version is not updatable: POST %s/webhook_endpoints/%s "
                    "accepts only url, enabled_events, description, metadata, disabled",
                    API, ep["id"])
        log.warning("  migrate instead: create a second endpoint on the same url "
                    "with a distinguishing query param and api_version=%s, keeping "
                    "enabled_events identical", args.current_line)
        log.warning("  then, once the new shape is handled: POST %s/"
                    "webhook_endpoints/%s -d disabled=true", API, ep["id"])

    log.info("%d endpoint(s), %d on an outdated pin", len(eps), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-endpoint-api-version.mjs",
"js": '''/**
 * Report Stripe webhook endpoints pinned to an outdated api_version.
 *
 * Read only. One GET and no writes: give this a RESTRICTED key with read access
 * to Webhook Endpoints. The migration is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const CURRENT_LINE = '2025-09-30'; // Clover
const ACACIA = '2024-09-30';              // breaking changes from here on
const DATE = /^(\\d{4}-\\d{2}-\\d{2})/;

/**
 * Classify one endpoint's pin. Pure, so the string handling can be tested.
 * `apiVersion` is the raw field: null or '' when the endpoint is unpinned.
 */
export function verdict(apiVersion, currentLine = CURRENT_LINE) {
  if (apiVersion === null || apiVersion === undefined || apiVersion === '') {
    return ['unpinned',
      'no api_version: events render at the account default, which moves under ' +
      'this endpoint whenever the account is upgraded'];
  }
  const m = DATE.exec(String(apiVersion));
  if (!m) {
    return ['unreadable',
      `api_version ${apiVersion} has no YYYY-MM-DD prefix to compare`];
  }
  const date = m[1];
  if (date < ACACIA) {
    return ['ancient',
      `pinned to ${date}, before the ${ACACIA} Acacia line. Typed SDKs ` +
      'deserialize this into empty objects without throwing.'];
  }
  if (date < currentLine) {
    return ['stale',
      `pinned to ${date}, behind the current ${currentLine} line. Check the ` +
      'changelog for the fields your handler reads.'];
  }
  return ['current', `pinned to ${date}, on the current line`];
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

  let bad = 0;
  for (const ep of eps) {
    const [state, detail] = verdict(ep.api_version);
    const line = `${state.padEnd(10)} ${ep.url ?? '?'}  ${detail}`;
    if (state === 'current' || state === 'unpinned') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  api_version is not updatable: POST ${API}/webhook_endpoints/` +
                 `${ep.id} accepts only url, enabled_events, description, ` +
                 'metadata, disabled');
    console.warn('  migrate instead: create a second endpoint on the same url ' +
                 `with a distinguishing query param and api_version=${CURRENT_LINE}, ` +
                 'keeping enabled_events identical');
    console.warn(`  then, once the new shape is handled: POST ${API}/` +
                 `webhook_endpoints/${ep.id} -d disabled=true`);
  }

  console.log(`${eps.length} endpoint(s), ${bad} on an outdated pin`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these tests exist because of one line of research. An empty string and a <code>null</code> both mean unpinned, and a check written with <code>is not None</code> reports the empty-string case as a pinned version, then compares <code>\"\"</code> against a date and calls it ancient. The third pins the date comparison, which has to trim the release-line suffix before it can order anything.",
"test_py_file": "test_stripe_endpoint_api_version.py",
"test_py": '''from stripe_endpoint_api_version import verdict


def test_null_is_unpinned():
    state, _ = verdict(None)
    assert state == "unpinned"


def test_empty_string_is_also_unpinned():
    # The trap: `if ep.api_version is not None` calls this pinned, then compares
    # an empty string against a date and reports it as the oldest pin on record.
    state, _ = verdict("")
    assert state == "unpinned"


def test_pre_acacia_is_hard_flagged():
    state, detail = verdict("2022-11-15")
    assert state == "ancient"
    assert "2024-09-30" in detail


def test_the_suffix_is_trimmed_before_comparing():
    # "2024-09-30.acacia" > "2025-09-30" as a naive string compare is False, but
    # "2025-09-30.clover" > "2025-09-30" is True, so the suffix has to go first.
    assert verdict("2024-09-30.acacia")[0] == "stale"
    assert verdict("2025-09-30.clover")[0] == "current"


def test_a_version_with_no_date_is_not_silently_current():
    state, _ = verdict("beta")
    assert state == "unreadable"
''',
"test_js_file": "stripe-endpoint-api-version.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-endpoint-api-version.mjs';

test('null is unpinned', () => {
  assert.equal(verdict(null)[0], 'unpinned');
});

test('empty string is also unpinned', () => {
  assert.equal(verdict('')[0], 'unpinned');
});

test('pre acacia is hard flagged', () => {
  const [state, detail] = verdict('2022-11-15');
  assert.equal(state, 'ancient');
  assert.match(detail, /2024-09-30/);
});

test('the suffix is trimmed before comparing', () => {
  assert.equal(verdict('2024-09-30.acacia')[0], 'stale');
  assert.equal(verdict('2025-09-30.clover')[0], 'current');
});

test('a version with no date is not silently current', () => {
  assert.equal(verdict('beta')[0], 'unreadable');
});
''',
"faq": [
 ("Can I just change api_version on the existing endpoint?",
  "No. Update accepts url, enabled_events, description, metadata and disabled. api_version is fixed when the endpoint is created and there is no parameter to move it, which is why the documented upgrade path is to create a second endpoint and retire the first."),
 ("Why does the signature still verify if the payload is wrong?",
  "Because the signature is computed over the raw request bytes, which are perfectly valid. It proves the body came from Stripe unmodified. It says nothing about which API version rendered the object inside, so verification passing tells you nothing about whether your SDK can read it."),
 ("Is an unpinned endpoint better or worse than a pinned one?",
  "Neither, but it is a different risk. Unpinned means the endpoint follows the account default, so an account upgrade changes your webhook payloads at the same time as everything else. Pinned means the payload shape is stable until you migrate it deliberately. The failure here is a pin nobody chose and nobody revisited."),
 ("How do I tell what version my SDK expects?",
  "Every Stripe SDK release targets one API version and pins it on outgoing requests. Read it from the library's changelog or its version constant, then compare it with the endpoint pin. The gap between the two is the finding; the pin on its own is not."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Webhook Endpoints is enough, and it is what this script should be given. It cannot move money if it leaks."),
],
"related": [
 ("/stripe/duplicate-endpoints-same-url/", "Two endpoints share one URL, so every event is handled twice"),
 ("/stripe/dead-or-rejected-enabled-events/", "enabled_events lists event types that are dead or rejected"),
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
],
"citations": [CITE_VERSIONING, CITE_WEBHOOK_UPDATE, CITE_WEBHOOK_OBJ, CITE_UPGRADES],
},

{
"slug": "missing-idempotency-keys-on-payments",
"title": "Payment-creating requests carry no idempotency key",
"description": "Occasional duplicate charges during network blips, impossible to reproduce. The events show API requests with request.idempotency_key null.",
"h1": "payment-creating requests carry no idempotency key",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe idempotency key", "stripe duplicate charge",
             "request.idempotency_key null", "stripe retry duplicate payment",
             "Idempotency-Key header"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A customer is charged twice. It happens perhaps once a week, always to someone on a phone, always during a moment when the network was bad, and never once on a developer machine. There is no bug in the checkout code. There is a missing HTTP header, and the events already recorded which requests were sent without it.",
"short_answer": """<p>Page <code>GET /v1/events</code> filtered to the types that create money or customers, and read the <code>request</code> object on each. Flag events where <code>request.id</code> is set <em>and</em> <code>request.idempotency_key</code> is null: that is an API call your code made, without a key, that a retry would have executed twice.</p>
<p>The <code>request.id</code> guard is not optional. Stripe-initiated events &mdash; renewal invoices, <code>customer.subscription.trial_will_end</code> &mdash; have both fields null, so a check that only looks at the key reports every automated Billing event as a finding and buries the real ones.</p>""",
"problem": """<p>The defining property of this failure is that it is unreproducible by construction. It needs a request that reaches Stripe, succeeds, and then fails to deliver its response &mdash; a timeout, a dropped mobile connection, a load balancer giving up. Locally the response always arrives, so the retry never happens, so the second charge never exists. Every attempt to reproduce it confirms the code is fine.</p>
<p>The retry also does not have to be yours. A user double-tapping a button, a proxy configured to retry idempotent-looking POSTs, a job runner that treats a timeout as a failure and re-queues: all of them produce a second identical request. Without a key, Stripe has no way to know it is the same operation, and it does exactly what it was asked to do a second time.</p>""",
"why": """<p><strong>Nothing requires the header, so nothing reminds you.</strong> Every mutating Stripe request accepts <code>Idempotency-Key</code> and none of them demands it. Requests without one succeed normally and look identical in the logs to requests with one. The protection is opt-in and its absence is silent.</p>
<p><strong>It lives in the options argument, not the parameters.</strong> In every official SDK the key is a second argument, separate from the request body: <code>stripe.paymentIntents.create(params, { idempotencyKey })</code> in Node, <code>idempotency_key=</code> as a keyword in Python, <code>['idempotency_key' => $key]</code> as the options array in PHP. Passing it inside the parameters hash is a very natural mistake, and it does not error &mdash; it is simply ignored.</p>
<p><strong>A key regenerated per attempt is the same as no key at all.</strong> The common near-miss is generating a fresh UUID inside the retry loop. Each attempt then carries a different key, so Stripe sees a series of distinct operations. The key has to be derived from the business operation and stay fixed across every retry of it.</p>
<p><strong>The events already hold the evidence, and the obvious query misreads it.</strong> Every event carries the <code>request</code> that caused it. Stripe's own automated actions produce events with a null <code>request.id</code>, and there are a lot of them on a Billing account. Filtering on the key alone drowns the real signal in renewal invoices.</p>""",
"steps": [
 {"h": "Pull the events that represent money moving",
  "body": """<p><code>GET /v1/events?types[]=payment_intent.created&amp;types[]=charge.succeeded&amp;types[]=customer.created&amp;types[]=refund.created</code>. These are the operations where a duplicate costs something real. The 30-day retention window is a large enough sample to be conclusive.</p>"""},
 {"h": "Separate your requests from Stripe's",
  "body": """<p><code>request.id</code> non-null means the event was caused by an API call from your integration. Null means Stripe did it on your behalf and there was never a key to send. Only the first group can be judged, and mixing them makes the report useless.</p>"""},
 {"h": "Report the ratio per event type, not a total",
  "body": """<p>A single number hides where the exposure is. If <code>customer.created</code> is unkeyed but <code>payment_intent.created</code> is not, you have duplicate customer rows, which is annoying. The reverse means duplicate charges, which is a refund and an apology. Anything above zero on a money-moving type is a finding.</p>"""},
 {"h": "Add the key at the call site, derived from the operation",
  "body": """<p>A v4 UUID generated once per logical operation, persisted next to the order record, and reused verbatim for every retry of that request. Not a customer ID, not a cart ID, not a date; those repeat, and a key reused with different parameters produces an <code>idempotency_error</code> rather than protection.</p>"""},
 {"h": "Re-run after a deploy and watch the ratio fall",
  "body": """<p>Because the window is rolling, the old unkeyed events stay in the sample for 30 days after the fix. The number to watch is the ratio over the last day or two, which should reach zero on money-moving types and stay there.</p>"""},
],
"verify": """<p>Re-run the script a day after the deploy. Every money-moving type should report every API-originated event as keyed.</p>
<pre><code class="language-bash">python3 stripe_idempotency_keys.py --days 1
# keyed      payment_intent.created  312 API request(s), all carrying a key</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/events</code> &mdash; a restricted key with read access to Events is enough. There are two pure functions because there are two decisions: what a single <code>request</code> object means, and what a whole type's tally means. The first is where the false positives live, so it is worth being able to test it on its own.",
"py_file": "stripe_idempotency_keys.py",
"py": '''"""Report Stripe API requests made without an Idempotency-Key.

Read only. One paginated GET and no writes: give this a RESTRICTED key with
read access to Events. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_idempotency_keys")

API = "https://api.stripe.com/v1"

# A duplicate of any of these costs real money or real support time.
MONEY_MOVING = ("payment_intent.created", "charge.succeeded", "refund.created")
WATCHED = MONEY_MOVING + ("customer.created",)


def classify(request):
    """What one event's `request` field says about the call that caused it.

    Pure. Returns one of:
      "stripe"     no request id at all: Stripe did this on your behalf, and
                   there was never a key to send. Not a finding.
      "unreported" a bare string request id, which is how very old API versions
                   rendered this field. The key is unknown, not absent.
      "keyed"      an API request that carried an Idempotency-Key.
      "unkeyed"    an API request that did not. This is the finding.
    """
    if request is None:
        return "stripe"
    if isinstance(request, str):
        return "unreported" if request else "stripe"
    if not request.get("id"):
        return "stripe"
    return "keyed" if request.get("idempotency_key") else "unkeyed"


def verdict(event_type, api_requests, unkeyed):
    """Classify one event type's tally. Pure, so the thresholds can be tested."""
    if not api_requests:
        return ("stripe-only",
                "no API-originated events in the window: nothing here is yours "
                "to key")
    if not unkeyed:
        return ("keyed",
                "%d API request(s), all carrying a key" % api_requests)
    pct = 100.0 * unkeyed / api_requests
    if event_type in MONEY_MOVING:
        return ("exposed",
                "%d of %d API request(s) sent no key (%.1f%%). A retried timeout "
                "on any of these charges the customer twice."
                % (unkeyed, api_requests, pct))
    return ("unkeyed",
            "%d of %d API request(s) sent no key (%.1f%%). Retries create "
            "duplicate records rather than duplicate charges."
            % (unkeyed, api_requests, pct))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def tally(session, since, limit):
    """Per-type counts of API-originated events and how many carried no key."""
    counts = {t: {"api": 0, "unkeyed": 0, "unreported": 0} for t in WATCHED}
    total = 0
    params = {"limit": 100, "created[gte]": int(since)}
    for i, t in enumerate(WATCHED):
        params["types[%d]" % i] = t
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        for ev in data:
            total += 1
            row = counts.get(ev.get("type"))
            if row is None:
                continue
            state = classify(ev.get("request"))
            if state == "stripe":
                continue
            if state == "unreported":
                row["unreported"] += 1
                continue
            row["api"] += 1
            if state == "unkeyed":
                row["unkeyed"] += 1
        if not data or not page.get("has_more") or total >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return counts, total


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
    counts, total = tally(s, since, args.max_events)
    log.info("sampled %d event(s) over %d day(s)", total, args.days)

    bad = 0
    for t in WATCHED:
        row = counts[t]
        state, detail = verdict(t, row["api"], row["unkeyed"])
        line = "%-11s %-24s %s" % (state, t, detail)
        if state in ("keyed", "stripe-only"):
            log.info(line)
        else:
            bad += 1
            log.warning(line)
        if row["unreported"]:
            log.info("  %d event(s) rendered at an API version that does not "
                     "report the key; upgrade the endpoint pin to judge them",
                     row["unreported"])

    if bad:
        log.warning("  repair: send an Idempotency-Key header on every mutating "
                    "request, in the options argument rather than the params:")
        log.warning("  node:   stripe.paymentIntents.create(params, { idempotencyKey })")
        log.warning("  python: stripe.PaymentIntent.create(..., idempotency_key=key)")
        log.warning("  php:    $stripe->paymentIntents->create($params, "
                    "['idempotency_key' => $key])")
        log.warning("  the key is a v4 uuid per logical operation, persisted with "
                    "the order and reused unchanged for every retry of it")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-idempotency-keys.mjs",
"js": '''/**
 * Report Stripe API requests made without an Idempotency-Key.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// A duplicate of any of these costs real money or real support time.
export const MONEY_MOVING = ['payment_intent.created', 'charge.succeeded',
                             'refund.created'];
const WATCHED = [...MONEY_MOVING, 'customer.created'];

/**
 * What one event's `request` field says about the call that caused it. Pure.
 * Returns 'stripe', 'unreported', 'keyed' or 'unkeyed'.
 */
export function classify(request) {
  if (request === null || request === undefined) return 'stripe';
  if (typeof request === 'string') return request ? 'unreported' : 'stripe';
  if (!request.id) return 'stripe';
  return request.idempotency_key ? 'keyed' : 'unkeyed';
}

/** Classify one event type's tally. Pure, so the thresholds can be tested. */
export function verdict(eventType, apiRequests, unkeyed) {
  if (!apiRequests) {
    return ['stripe-only',
      'no API-originated events in the window: nothing here is yours to key'];
  }
  if (!unkeyed) return ['keyed', `${apiRequests} API request(s), all carrying a key`];
  const pct = ((100 * unkeyed) / apiRequests).toFixed(1);
  if (MONEY_MOVING.includes(eventType)) {
    return ['exposed',
      `${unkeyed} of ${apiRequests} API request(s) sent no key (${pct}%). ` +
      'A retried timeout on any of these charges the customer twice.'];
  }
  return ['unkeyed',
    `${unkeyed} of ${apiRequests} API request(s) sent no key (${pct}%). ` +
    'Retries create duplicate records rather than duplicate charges.'];
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

export async function tally(key, since, limit = 5000) {
  const counts = new Map(WATCHED.map((t) => [t, { api: 0, unkeyed: 0, unreported: 0 }]));
  let total = 0;
  const params = { limit: 100, 'created[gte]': Math.floor(since) };
  WATCHED.forEach((t, i) => { params[`types[${i}]`] = t; });
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    for (const ev of data) {
      total += 1;
      const row = counts.get(ev.type);
      if (!row) continue;
      const state = classify(ev.request);
      if (state === 'stripe') continue;
      if (state === 'unreported') { row.unreported += 1; continue; }
      row.api += 1;
      if (state === 'unkeyed') row.unkeyed += 1;
    }
    if (data.length === 0 || !page.has_more || total >= limit) break;
    params.starting_after = data[data.length - 1].id;
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

  const days = Number(process.env.DAYS ?? 30);
  const since = Date.now() / 1000 - days * 86400;
  const { counts, total } = await tally(key, since);
  console.log(`sampled ${total} event(s) over ${days} day(s)`);

  let bad = 0;
  for (const t of WATCHED) {
    const row = counts.get(t);
    const [state, detail] = verdict(t, row.api, row.unkeyed);
    const line = `${state.padEnd(11)} ${t.padEnd(24)} ${detail}`;
    if (state === 'keyed' || state === 'stripe-only') {
      console.log(line);
    } else {
      bad += 1;
      console.warn(line);
    }
    if (row.unreported) {
      console.log(`  ${row.unreported} event(s) rendered at an API version that ` +
                  'does not report the key; upgrade the endpoint pin to judge them');
    }
  }

  if (bad) {
    console.warn('  repair: send an Idempotency-Key header on every mutating ' +
                 'request, in the options argument rather than the params:');
    console.warn('  node:   stripe.paymentIntents.create(params, { idempotencyKey })');
    console.warn('  python: stripe.PaymentIntent.create(..., idempotency_key=key)');
    console.warn("  php:    $stripe->paymentIntents->create($params, " +
                 "['idempotency_key' => $key])");
    console.warn('  the key is a v4 uuid per logical operation, persisted with ' +
                 'the order and reused unchanged for every retry of it');
  }
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the whole reason this check is worth writing carefully. Stripe-initiated events have a null <code>request.id</code> and a null <code>request.idempotency_key</code>, and on a Billing account they outnumber everything else. A check that reads only the key reports every renewal invoice as an unkeyed payment request, and the report gets ignored on its first run.",
"test_py_file": "test_stripe_idempotency_keys.py",
"test_py": '''from stripe_idempotency_keys import classify, verdict


def test_stripe_initiated_events_are_not_findings():
    # Both fields null. Stripe did this; there was never a key to send. Reading
    # only idempotency_key here flags every renewal invoice on the account.
    assert classify({"id": None, "idempotency_key": None}) == "stripe"
    assert classify(None) == "stripe"


def test_an_api_request_without_a_key_is_the_finding():
    assert classify({"id": "req_123", "idempotency_key": None}) == "unkeyed"


def test_an_api_request_with_a_key_is_clean():
    assert classify({"id": "req_123", "idempotency_key": "8f14e45f"}) == "keyed"


def test_a_bare_string_request_is_unreported_not_unkeyed():
    # Old API versions rendered `request` as a bare id string. The key is
    # unknown there, and counting it as absent invents a problem.
    assert classify("req_123") == "unreported"


def test_one_unkeyed_charge_is_already_exposed():
    state, detail = verdict("payment_intent.created", 400, 1)
    assert state == "exposed"
    assert "twice" in detail
    assert verdict("customer.created", 400, 1)[0] == "unkeyed"
    assert verdict("payment_intent.created", 400, 0)[0] == "keyed"
''',
"test_js_file": "stripe-idempotency-keys.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, verdict } from './stripe-idempotency-keys.mjs';

test('stripe initiated events are not findings', () => {
  assert.equal(classify({ id: null, idempotency_key: null }), 'stripe');
  assert.equal(classify(null), 'stripe');
});

test('an api request without a key is the finding', () => {
  assert.equal(classify({ id: 'req_123', idempotency_key: null }), 'unkeyed');
});

test('an api request with a key is clean', () => {
  assert.equal(classify({ id: 'req_123', idempotency_key: '8f14e45f' }), 'keyed');
});

test('a bare string request is unreported not unkeyed', () => {
  assert.equal(classify('req_123'), 'unreported');
});

test('one unkeyed charge is already exposed', () => {
  const [state, detail] = verdict('payment_intent.created', 400, 1);
  assert.equal(state, 'exposed');
  assert.match(detail, /twice/);
  assert.equal(verdict('customer.created', 400, 1)[0], 'unkeyed');
  assert.equal(verdict('payment_intent.created', 400, 0)[0], 'keyed');
});
''',
"faq": [
 ("Which requests need an idempotency key?",
  "Every mutating one. GETs are already idempotent and Stripe ignores the header on them. In practice the ones that matter are the requests that create something: PaymentIntents, charges, refunds, customers, subscriptions. Those are the operations where doing it twice is visible to a customer."),
 ("Why does request.id have to be non-null in the check?",
  "Because Stripe-initiated events have both request fields null. Renewal invoices, trial_will_end, automatic payout events: none of them came from an API call of yours, so none of them could have carried a key. Without the guard those dominate the report and the real findings disappear into them."),
 ("How long does Stripe remember an idempotency key?",
  "Results are saved for roughly 24 hours, after which the key is pruned. A retry inside that window replays the saved status code and body. A request reusing the same key after pruning is treated as brand new, which is one reason keys derived from something long-lived, like a customer ID, cause duplicates rather than preventing them."),
 ("Can I use the order ID as the key?",
  "Only if it is unique per attempt at that specific request, and usually it is not. An order that is retried after a failed payment, or that creates both a customer and a PaymentIntent, reuses the value across different operations and different parameters, which returns an idempotency_error instead of protection. Derive the key from the operation and persist it."),
 ("What does a 409 idempotency_key_in_use mean?",
  "Two requests carrying the same key arrived close enough together that neither result was saved yet. It is retryable, and the retry must use the same key. It is a signal that the key is shared across concurrent operations rather than unique to one."),
],
"related": [
 ("/stripe/duplicate-customers-same-email/", "One customer has several Customer records"),
 ("/stripe/duplicate-endpoints-same-url/", "Two endpoints share one URL, so every event is handled twice"),
 ("/stripe/refunds-failed-or-stuck/", "Refunds fail or sit unresolved"),
],
"citations": [CITE_IDEMPOTENCY, CITE_EVENT_OBJ, CITE_EVENTS_LIST, CITE_API_VERSIONING],
},

{
"slug": "dead-or-rejected-enabled-events",
"title": "enabled_events lists event types that are dead or rejected",
"description": "A handler branch that has not run in a year, and an endpoint update that fails with do not have access to the event types. Two kinds of decay.",
"h1": "enabled_events lists event types that are dead or rejected",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe enabled_events invalid", "customer.source.expiring",
             "source.chargeable deprecated", "stripe event type removed",
             "do not have access to the event types"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Card-expiry reminder emails stopped going out. Nobody can say when, because nothing failed: the handler branch simply never runs, and a branch that never runs produces no logs. Separately, and apparently unrelatedly, an attempt to add one new event type to the endpoint comes back with <em>You do not have access to the event types</em>, naming a type that has been in the list for years.",
"short_answer": """<p>Read <code>enabled_events</code> from <code>GET /v1/webhook_endpoints</code> and check each entry two ways. First: anything under <code>source.</code> or <code>customer.source.</code> belongs to the Sources API, and stops firing entirely once the integration moves to PaymentMethods. Confirm with <code>GET /v1/events?types[]=...</code> over the retained window &mdash; zero results across 30 days on a busy account is your answer.</p>
<p>Second: diff every entry against the live enum of event types. A type Stripe has removed stays happily in your <code>enabled_events</code> array until the next update, which then fails wholesale &mdash; including the change you actually wanted to make.</p>""",
"problem": """<p>These are two different failures that look like one because they live in the same array. The first is a branch that has quietly stopped executing. <code>customer.source.expiring</code> does not fire for an integration using PaymentMethods, so the card-expiry warning it drove has not been sent since the migration. Nothing errors. The subscription is still there, the handler code is still there, the emails are not.</p>
<p>The second only shows up when you try to change something else. <code>enabled_events</code> is replaced wholesale on update, so the array you send back includes every existing entry, including one the API no longer accepts. The rejection names a type you were not touching, on a request you made for an unrelated reason, and the obvious reading &mdash; a permissions problem on the key &mdash; is wrong.</p>""",
"why": """<p><strong>Deprecated types stay configurable long after they stop firing.</strong> Stripe does not reject <code>customer.source.expiring</code>; it is a valid type that simply will not occur if you use the PaymentMethod API. So the subscription looks correct in the Dashboard, in the API response, and in your infrastructure code. The only evidence is an absence, and absences are not alerted on.</p>
<p><strong>SDK constant lists outlive the API.</strong> A type removed from the API stays in the enum of an SDK version you have pinned, so your code compiles, your infrastructure definition validates, and the rejection arrives at runtime from Stripe rather than at build time from your tooling.</p>
<p><strong>Updates replace the whole array.</strong> There is no add-one-type operation. Every update re-sends the full list, which means one dead entry poisons every future change to that endpoint until somebody reads the error message carefully enough to notice it names something they did not touch.</p>
<p><strong>A type that has not fired is not necessarily dead.</strong> This is the trap in the other direction. <code>charge.dispute.created</code> firing zero times in 30 days is good news, not decay. Only the legacy families can be judged by silence; for everything else, silence is just low volume, and a check that conflates the two will tell you to unsubscribe from disputes.</p>""",
"steps": [
 {"h": "List every subscribed type across every endpoint",
  "body": """<p><code>GET /v1/webhook_endpoints?limit=100</code>, then flatten <code>enabled_events</code>. A literal <code>"*"</code> short-circuits this entirely: a wildcard subscription has nothing to diff, and is its own separate problem.</p>"""},
 {"h": "Flag the legacy families by prefix",
  "body": """<p><code>source.</code> and <code>customer.source.</code> are the Sources API. If your integration creates PaymentIntents and PaymentMethods, these types do not fire, and any handler branch behind them is dead code that looks live.</p>"""},
 {"h": "Confirm with the event stream rather than assuming",
  "body": """<p>Tally <code>GET /v1/events</code> across the retained window and check whether each flagged type appears. A legacy type that <em>is</em> still firing means something in the integration is still creating Sources, which is a migration finding rather than a cleanup one.</p>"""},
 {"h": "Diff the rest against the accepted enum",
  "body": """<p>The authoritative list is the <code>enabled_events</code> enum documented on endpoint creation. Anything in your array that is absent from it will be rejected the next time the endpoint is updated, whatever else that update was for.</p>"""},
 {"h": "Rewrite the array without the dead entries",
  "body": """<p><code>POST /v1/webhook_endpoints/{id}</code> with the full corrected list. Replace card-expiry logic with <code>payment_method.automatically_updated</code> plus a periodic sweep of <code>card.exp_month</code> and <code>card.exp_year</code>; replace <code>source.chargeable</code> with the PaymentIntent lifecycle events.</p>"""},
],
"verify": """<p>Re-run the script. Every subscribed type should be one the API still accepts, and every legacy entry should be gone or explained.</p>
<pre><code class="language-bash">python3 stripe_dead_event_types.py
# live       payment_intent.succeeded  seen firing in the retained window</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Webhook Endpoints and Events is enough. The classifier takes one subscribed type and the set of types actually observed, because the difference between <em>dead</em> and <em>quiet</em> is the whole point of the check and it is decided by rules that should be visible rather than buried in a request loop.",
"py_file": "stripe_dead_event_types.py",
"py": '''"""Report Stripe webhook subscriptions to event types that are dead or rejected.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access
to Webhook Endpoints and Events. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_dead_event_types")

API = "https://api.stripe.com/v1"

# The Sources API families. These stay configurable but stop occurring once the
# integration moves to PaymentIntents and PaymentMethods.
LEGACY_PREFIXES = ("source.", "customer.source.")

# Types the API no longer accepts on an update, so one of these poisons every
# future change to the endpoint. Keep in step with the enabled_events enum in
# the create-endpoint reference; this is the short list seen in the wild.
REJECTED = frozenset({"invoiceitem.updated"})


def verdict(event_type, fired):
    """Classify one subscribed event type. Pure, so the rules can be tested.

    `fired` is the set of event types actually seen in the retained window.
    Returns (state, detail).
    """
    if event_type == "*":
        return ("wildcard",
                "subscribed to every type: there is no list here to diff")
    seen = set(fired or [])
    if event_type in REJECTED:
        return ("rejected",
                "the API no longer accepts this type. The next update to this "
                "endpoint fails on it, whatever the update was for.")
    if event_type.startswith(LEGACY_PREFIXES):
        if event_type in seen:
            return ("legacy",
                    "a Sources API type that is still firing: something in the "
                    "integration still creates Sources")
        return ("dead",
                "a Sources API type with no occurrences in the retained window. "
                "It does not fire for a PaymentMethod integration, so any "
                "handler branch behind it is dead code.")
    if event_type in seen:
        return ("live", "seen firing in the retained window")
    return ("quiet",
            "no occurrences in the retained window. That is low volume, not "
            "proof of decay: disputes and failures are supposed to be rare.")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def fired_types(session, limit):
    """The set of event types seen in the retained window."""
    seen = set()
    total = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        for ev in data:
            total += 1
            seen.add(ev.get("type"))
        if not data or not page.get("has_more") or total >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return seen, total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=5000,
                    help="stop sampling event types after this many events")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    eps = get(s, "/webhook_endpoints", limit=100).get("data", [])
    if not eps:
        log.info("no webhook endpoints configured for this key's mode")
        return 0

    seen, total = fired_types(s, args.max_events)
    log.info("sampled %d event(s) across %d distinct type(s)", total, len(seen))

    bad = 0
    for ep in eps:
        keep = []
        drop = []
        for t in ep.get("enabled_events") or []:
            state, detail = verdict(t, seen)
            line = "%-9s %-32s %s" % (state, t, detail)
            if state in ("dead", "rejected"):
                bad += 1
                drop.append(t)
                log.warning("%s  %s", ep.get("url", "?"), line)
            else:
                keep.append(t)
                log.info("%s  %s", ep.get("url", "?"), line)
        if drop:
            log.warning("  enabled_events is replaced wholesale on update, so "
                        "re-send the full corrected list:")
            log.warning("  repair: POST %s/webhook_endpoints/%s %s",
                        API, ep["id"],
                        " ".join("-d enabled_events[]=%s" % t for t in keep[:6])
                        + (" ..." if len(keep) > 6 else ""))
            log.warning("  dropping: %s", ", ".join(drop))

    log.info("%d endpoint(s), %d dead or rejected subscription(s)", len(eps), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-dead-event-types.mjs",
"js": '''/**
 * Report Stripe webhook subscriptions to event types that are dead or rejected.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read
 * access to Webhook Endpoints and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// The Sources API families. These stay configurable but stop occurring once the
// integration moves to PaymentIntents and PaymentMethods.
const LEGACY_PREFIXES = ['source.', 'customer.source.'];

// Types the API no longer accepts on an update, so one of these poisons every
// future change to the endpoint.
export const REJECTED = new Set(['invoiceitem.updated']);

/**
 * Classify one subscribed event type. Pure, so the rules can be tested.
 * `fired` is the set of event types actually seen in the retained window.
 */
export function verdict(eventType, fired) {
  if (eventType === '*') {
    return ['wildcard', 'subscribed to every type: there is no list here to diff'];
  }
  const seen = new Set(fired ?? []);
  if (REJECTED.has(eventType)) {
    return ['rejected',
      'the API no longer accepts this type. The next update to this endpoint ' +
      'fails on it, whatever the update was for.'];
  }
  if (LEGACY_PREFIXES.some((p) => eventType.startsWith(p))) {
    if (seen.has(eventType)) {
      return ['legacy',
        'a Sources API type that is still firing: something in the integration ' +
        'still creates Sources'];
    }
    return ['dead',
      'a Sources API type with no occurrences in the retained window. It does ' +
      'not fire for a PaymentMethod integration, so any handler branch behind ' +
      'it is dead code.'];
  }
  if (seen.has(eventType)) return ['live', 'seen firing in the retained window'];
  return ['quiet',
    'no occurrences in the retained window. That is low volume, not proof of ' +
    'decay: disputes and failures are supposed to be rare.'];
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

export async function firedTypes(key, limit = 5000) {
  const seen = new Set();
  let total = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    for (const ev of data) { total += 1; seen.add(ev.type); }
    if (data.length === 0 || !page.has_more || total >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { seen, total };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: eps = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  if (eps.length === 0) {
    console.log("no webhook endpoints configured for this key's mode");
    return;
  }

  const { seen, total } = await firedTypes(key);
  console.log(`sampled ${total} event(s) across ${seen.size} distinct type(s)`);

  let bad = 0;
  for (const ep of eps) {
    const keep = [];
    const drop = [];
    for (const t of ep.enabled_events ?? []) {
      const [state, detail] = verdict(t, seen);
      const line = `${state.padEnd(9)} ${t.padEnd(32)} ${detail}`;
      if (state === 'dead' || state === 'rejected') {
        bad += 1;
        drop.push(t);
        console.warn(`${ep.url ?? '?'}  ${line}`);
      } else {
        keep.push(t);
        console.log(`${ep.url ?? '?'}  ${line}`);
      }
    }
    if (drop.length) {
      console.warn('  enabled_events is replaced wholesale on update, so ' +
                   're-send the full corrected list:');
      const args = keep.slice(0, 6).map((t) => `-d enabled_events[]=${t}`).join(' ');
      console.warn(`  repair: POST ${API}/webhook_endpoints/${ep.id} ${args}` +
                   (keep.length > 6 ? ' ...' : ''));
      console.warn(`  dropping: ${drop.join(', ')}`);
    }
  }

  console.log(`${eps.length} endpoint(s), ${bad} dead or rejected subscription(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that stops this check being harmful is the one about <code>charge.dispute.created</code>. Silence over 30 days means a dead subscription for a Sources type and a good month for a dispute type, and a classifier that cannot tell them apart will confidently recommend unsubscribing from disputes. The legacy prefixes are the only place where an absence is evidence.",
"test_py_file": "test_stripe_dead_event_types.py",
"test_py": '''from stripe_dead_event_types import verdict

FIRED = {"payment_intent.succeeded", "invoice.paid", "customer.source.expiring"}


def test_a_removed_type_is_rejected():
    state, detail = verdict("invoiceitem.updated", FIRED)
    assert state == "rejected"
    assert "update" in detail


def test_a_silent_sources_type_is_dead():
    state, _ = verdict("source.chargeable", FIRED)
    assert state == "dead"


def test_a_sources_type_that_still_fires_is_not_dead():
    # Still firing means something still creates Sources. That is a migration
    # finding, not a subscription to delete.
    state, _ = verdict("customer.source.expiring", FIRED)
    assert state == "legacy"


def test_silence_on_a_current_type_is_not_decay():
    # Zero disputes in 30 days is a good month. Calling this dead would have the
    # script recommend unsubscribing from disputes.
    state, detail = verdict("charge.dispute.created", FIRED)
    assert state == "quiet"
    assert "low volume" in detail


def test_a_wildcard_has_nothing_to_diff():
    assert verdict("*", FIRED)[0] == "wildcard"
''',
"test_js_file": "stripe-dead-event-types.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-dead-event-types.mjs';

const FIRED = ['payment_intent.succeeded', 'invoice.paid',
               'customer.source.expiring'];

test('a removed type is rejected', () => {
  const [state, detail] = verdict('invoiceitem.updated', FIRED);
  assert.equal(state, 'rejected');
  assert.match(detail, /update/);
});

test('a silent sources type is dead', () => {
  assert.equal(verdict('source.chargeable', FIRED)[0], 'dead');
});

test('a sources type that still fires is not dead', () => {
  assert.equal(verdict('customer.source.expiring', FIRED)[0], 'legacy');
});

test('silence on a current type is not decay', () => {
  const [state, detail] = verdict('charge.dispute.created', FIRED);
  assert.equal(state, 'quiet');
  assert.match(detail, /low volume/);
});

test('a wildcard has nothing to diff', () => {
  assert.equal(verdict('*', FIRED)[0], 'wildcard');
});
''',
"faq": [
 ("Why does customer.source.expiring never fire for us?",
  "Because it belongs to the Sources API. Stripe documents that it will not occur for an integration using the PaymentMethod API, and most integrations moved to PaymentMethods years ago. The subscription stays valid and configurable; the event just never happens, so the handler branch behind it is unreachable."),
 ("What replaces the card-expiry warning it used to drive?",
  "Two things together. Subscribe to payment_method.automatically_updated so network-driven card refreshes update your local copy, and run a periodic sweep over card.exp_month and card.exp_year on each customer's saved PaymentMethods to find the ones the updater does not cover."),
 ("Why did adding one event type fail on a different type?",
  "Because enabled_events is replaced wholesale rather than appended to. Your update re-sent the entire existing array, including an entry the API no longer accepts, and the request is rejected as a unit. The error names the dead type, not the one you were adding, which is why it reads like a permissions problem."),
 ("Is a type that never fires always a problem?",
  "No, and this is the easiest way to make the check worse than useless. Dispute and failure events are supposed to be rare, so 30 days of silence on charge.dispute.created is good news. Only the legacy families can be judged by absence; everything else needs a positive reason to be called dead."),
 ("Does removing a dead type change my signing secret?",
  "No. Updating an endpoint preserves the secret. Deleting and recreating it does not, which is why the repair here is an update with a corrected list rather than a rebuild."),
],
"related": [
 ("/stripe/wildcard-enabled-events/", "An endpoint subscribes to every event and floods the handler"),
 ("/stripe/endpoint-api-version-pinned-stale/", "A webhook endpoint is pinned to an ancient api_version"),
 ("/stripe/missing-payout-failed/", "payout.failed is unsubscribed so failures go unseen"),
],
"citations": [CITE_EVENT_TYPES, CITE_WEBHOOK_CREATE, CITE_SOURCES, CITE_OLDER_APIS],
},

{
"slug": "expired-saved-cards-attached",
"title": "Saved cards are already expired but still attached",
"description": "Renewals fail with expired_card while your UI still shows the card as valid. The automatic updater covers some issuers, and you cannot tell which.",
"h1": "saved cards are already expired but still attached",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe expired_card", "stripe expired saved card",
             "stripe card updater", "involuntary churn stripe",
             "payment method exp_year"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "MRR leaks by a percent or two every month and the churn report calls it voluntary. It is not: these customers never chose to leave. Their saved card expired, the renewal failed with <code>expired_card</code>, the dunning emails went to an inbox they do not read, and the account settings page still shows the card as though it works.",
"short_answer": """<p>For each customer, read <code>GET /v1/payment_methods?customer={id}&amp;type=card</code> and compare <code>card.exp_month</code> and <code>card.exp_year</code> against today. A card is expired when <code>exp_year &lt; now.year</code>, or when the years match and <code>exp_month &lt; now.month</code>. A card whose expiry month <em>is</em> the current month is still good until the last day of it.</p>
<p>Escalate the ones that matter: an expired PaymentMethod referenced by <code>customer.invoice_settings.default_payment_method</code> or by an active subscription's <code>default_payment_method</code> is not dead weight, it is the next failed renewal.</p>""",
"problem": """<p>The reason this survives is that Stripe's automatic card updater works, just not everywhere. It handles a good share of US-issued Visa, Mastercard, Amex and Discover reissues, and when it fires the customer never notices anything. Coverage outside that is partial and varies by issuer and country, and there is no field that tells you which of your saved cards participate. So the same integration gets a silent, self-healing renewal for one customer and a hard <code>expired_card</code> decline for the next, with nothing in your data to distinguish them beforehand.</p>
<p>Meanwhile the expired card stays attached to the Customer indefinitely. Nothing prunes it. Your own account page renders <code>last4</code> and a brand icon and looks entirely healthy, so a customer who does go and check sees a card on file and concludes the problem is on your side.</p>""",
"why": """<p><strong>Expiry is knowable months ahead and almost nobody acts on it.</strong> <code>exp_month</code> and <code>exp_year</code> are on the PaymentMethod from the moment it is saved. The information required to prevent this failure is sitting in the API the whole time, and the overwhelmingly common design is to wait for the decline and then start a dunning sequence.</p>
<p><strong>The off-by-one is in the direction that costs you.</strong> A card is valid through the <em>end</em> of its expiry month. A check written as <code>exp_month &lt;= now.month</code> declares a perfectly good card dead for its final month, and a system that acts on that emails customers to replace cards that work. The comparison has to be strictly less-than within the same year.</p>
<p><strong>Being expired and being the default are very different findings.</strong> A stale card sitting on a customer alongside three working ones is untidy. The same card set as <code>invoice_settings.default_payment_method</code> on an active subscription is a renewal that has already failed or is about to, and the two should never appear in the same bucket in a report.</p>
<p><strong>Dunning is where recovery goes to die.</strong> By the time the decline happens, recovery depends on an email reaching someone and persuading them to re-enter card details. That funnel converts poorly, which is exactly why the fix lives before the expiry date rather than after it.</p>""",
"steps": [
 {"h": "Scope to customers who are actually being billed",
  "body": """<p>Sweeping every Customer on the account is mostly noise; a one-off purchaser from two years ago with a dead card costs you nothing. Start from <code>GET /v1/subscriptions?status=active</code> and check those customers, which is where an expired card turns into lost revenue.</p>"""},
 {"h": "Compare against the end of the expiry month",
  "body": """<p>Expired means the expiry month is strictly in the past. Same year and same month is still valid, and worth reporting separately as the last month it will work, because that is the one where a nudge still prevents the decline.</p>"""},
 {"h": "Cross-reference the defaults",
  "body": """<p>Read <code>customer.invoice_settings.default_payment_method</code> and each active subscription's <code>default_payment_method</code>. An expired card in either position is the finding to act on today; the rest is cleanup.</p>"""},
 {"h": "Confirm the damage in the payment data",
  "body": """<p><code>GET /v1/payment_intents</code> counting <code>last_payment_error.decline_code == "expired_card"</code>, and <code>GET /v1/charges</code> where <code>outcome.reason</code> says the same. This turns an estimate into a number of failed renewals, which is what makes the ticket move.</p>"""},
 {"h": "Detach and re-collect, then close the loop",
  "body": """<p>Detach the dead PaymentMethod and send the customer a Customer Portal link or a SetupIntent to add a new one. Then subscribe to <code>payment_method.automatically_updated</code> so that when the network updater <em>does</em> fire, your local copy of <code>exp_month</code>, <code>exp_year</code> and <code>last4</code> stops drifting out of date.</p>"""},
],
"verify": """<p>Re-run the script. No customer with an active subscription should have an expired card in a default position.</p>
<pre><code class="language-bash">python3 stripe_expired_cards.py
# valid      cus_QxAbc123  pm_1Nx  good to 04/2029</code></pre>""",
"code_intro": "Two GETs per customer and no writes &mdash; a restricted key with read access to Customers, Subscriptions and PaymentMethods is enough. The date comparison is a pure function taking explicit year and month arguments rather than reading the clock, both so the boundary can be tested and so a run near midnight on the last day of a month cannot disagree with itself halfway through.",
"py_file": "stripe_expired_cards.py",
"py": '''"""Report expired card PaymentMethods still attached to Stripe customers.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Customers, Subscriptions and PaymentMethods. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_expired_cards")

API = "https://api.stripe.com/v1"


def verdict(exp_month, exp_year, now_year, now_month, is_default=False):
    """Classify one saved card against today. Pure, so the boundary is testable.

    A card is valid through the END of its expiry month, so the same month in
    the same year is still good. Returns (state, detail).
    """
    if not exp_month or not exp_year:
        return ("unreadable",
                "no exp_month/exp_year on this payment method: it cannot be aged")
    label = "%02d/%d" % (int(exp_month), int(exp_year))
    expired = (exp_year < now_year
               or (exp_year == now_year and exp_month < now_month))
    if expired and is_default:
        return ("expired-default",
                "expired %s and it is the billing default: the next renewal "
                "fails with expired_card" % label)
    if expired:
        return ("expired",
                "expired %s and still attached. Nothing prunes it, so your UI "
                "keeps showing it as a card on file." % label)
    if exp_year == now_year and exp_month == now_month:
        return ("last-month",
                "valid to the end of %s and then it stops. This is the month a "
                "nudge still prevents the decline." % label)
    return ("valid", "good to %s" % label)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def billed_customers(session, limit):
    """Customer ids with an active subscription, and the default PM per customer."""
    out = {}
    params = {"limit": 100, "status": "active"}
    while True:
        page = get(session, "/subscriptions", **params)
        data = page.get("data", [])
        for sub in data:
            cus = sub.get("customer")
            if isinstance(cus, dict):
                cus = cus.get("id")
            if not cus:
                continue
            defaults = out.setdefault(cus, set())
            pm = sub.get("default_payment_method")
            if isinstance(pm, dict):
                pm = pm.get("id")
            if pm:
                defaults.add(pm)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-customers", type=int, default=500,
                    help="stop after this many billed customers")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    today = dt.date.today()
    customers = billed_customers(s, args.max_customers)
    if not customers:
        log.info("no active subscriptions for this key's mode")
        return 0

    bad = 0
    for cus, sub_defaults in customers.items():
        customer = get(s, "/customers/" + cus)
        settings = customer.get("invoice_settings") or {}
        defaults = set(sub_defaults)
        if settings.get("default_payment_method"):
            defaults.add(settings["default_payment_method"])

        pms = get(s, "/payment_methods", customer=cus, type="card",
                  limit=100).get("data", [])
        for pm in pms:
            card = pm.get("card") or {}
            state, detail = verdict(card.get("exp_month"), card.get("exp_year"),
                                    today.year, today.month,
                                    pm.get("id") in defaults)
            line = "%-15s %s  %s  %s" % (state, cus, pm.get("id"), detail)
            if state in ("valid",):
                log.info(line)
                continue
            if state == "last-month":
                log.info(line)
                continue
            bad += 1
            log.warning(line)
            log.warning("  repair: POST %s/payment_methods/%s/detach, then send "
                        "the customer a Customer Portal session or a SetupIntent "
                        "to add a new card", API, pm.get("id"))
            log.warning("  and subscribe to payment_method.automatically_updated "
                        "so network updates refresh your local exp_month/exp_year")

    log.info("%d billed customer(s), %d expired card(s) still attached",
             len(customers), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-expired-cards.mjs",
"js": '''/**
 * Report expired card PaymentMethods still attached to Stripe customers.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to Customers, Subscriptions and PaymentMethods. The repair is printed, never
 * performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one saved card against today. Pure, so the boundary is testable.
 * A card is valid through the END of its expiry month, so the same month in the
 * same year is still good.
 */
export function verdict(expMonth, expYear, nowYear, nowMonth, isDefault = false) {
  if (!expMonth || !expYear) {
    return ['unreadable',
      'no exp_month/exp_year on this payment method: it cannot be aged'];
  }
  const label = `${String(expMonth).padStart(2, '0')}/${expYear}`;
  const expired = expYear < nowYear || (expYear === nowYear && expMonth < nowMonth);
  if (expired && isDefault) {
    return ['expired-default',
      `expired ${label} and it is the billing default: the next renewal fails ` +
      'with expired_card'];
  }
  if (expired) {
    return ['expired',
      `expired ${label} and still attached. Nothing prunes it, so your UI keeps ` +
      'showing it as a card on file.'];
  }
  if (expYear === nowYear && expMonth === nowMonth) {
    return ['last-month',
      `valid to the end of ${label} and then it stops. This is the month a nudge ` +
      'still prevents the decline.'];
  }
  return ['valid', `good to ${label}`];
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

export async function billedCustomers(key, limit = 500) {
  const out = new Map();
  const params = { limit: 100, status: 'active' };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const data = page.data ?? [];
    for (const sub of data) {
      const cus = typeof sub.customer === 'object' ? sub.customer?.id : sub.customer;
      if (!cus) continue;
      if (!out.has(cus)) out.set(cus, new Set());
      const pm = typeof sub.default_payment_method === 'object'
        ? sub.default_payment_method?.id
        : sub.default_payment_method;
      if (pm) out.get(cus).add(pm);
    }
    if (data.length === 0 || !page.has_more || out.size >= limit) break;
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

  const now = new Date();
  const nowYear = now.getFullYear();
  const nowMonth = now.getMonth() + 1;

  const customers = await billedCustomers(key);
  if (customers.size === 0) {
    console.log("no active subscriptions for this key's mode");
    return;
  }

  let bad = 0;
  for (const [cus, subDefaults] of customers) {
    const customer = await get(key, `/customers/${cus}`);
    const defaults = new Set(subDefaults);
    const settingsDefault = customer.invoice_settings?.default_payment_method;
    if (settingsDefault) defaults.add(settingsDefault);

    const { data: pms = [] } = await get(key, '/payment_methods',
      { customer: cus, type: 'card', limit: 100 });
    for (const pm of pms) {
      const card = pm.card ?? {};
      const [state, detail] = verdict(card.exp_month, card.exp_year,
        nowYear, nowMonth, defaults.has(pm.id));
      const line = `${state.padEnd(15)} ${cus}  ${pm.id}  ${detail}`;
      if (state === 'valid' || state === 'last-month') { console.log(line); continue; }
      bad += 1;
      console.warn(line);
      console.warn(`  repair: POST ${API}/payment_methods/${pm.id}/detach, then ` +
                   'send the customer a Customer Portal session or a SetupIntent ' +
                   'to add a new card');
      console.warn('  and subscribe to payment_method.automatically_updated so ' +
                   'network updates refresh your local exp_month/exp_year');
    }
  }

  console.log(`${customers.size} billed customer(s), ${bad} expired card(s) ` +
              'still attached');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the one that decides whether this script is safe to act on. A card marked 06/2026 works until the last day of June 2026, so on the 3rd of June it is valid, not expired. Get that wrong and the script emails a month's worth of customers asking them to replace cards that are working perfectly.",
"test_py_file": "test_stripe_expired_cards.py",
"test_py": '''from stripe_expired_cards import verdict


def test_the_expiry_month_itself_is_still_valid():
    # 06/2026 works until 30 June 2026. `exp_month <= now_month` would call this
    # expired and send a replace-your-card email for a card that works.
    state, detail = verdict(6, 2026, 2026, 6)
    assert state == "last-month"
    assert "end of 06/2026" in detail


def test_last_month_of_the_same_year_is_expired():
    assert verdict(5, 2026, 2026, 6)[0] == "expired"


def test_a_previous_year_is_expired_whatever_the_month():
    # December of last year is still in the past in January.
    assert verdict(12, 2025, 2026, 1)[0] == "expired"


def test_an_expired_default_is_escalated():
    state, detail = verdict(1, 2024, 2026, 6, True)
    assert state == "expired-default"
    assert "expired_card" in detail


def test_a_card_with_no_expiry_fields_is_not_silently_valid():
    assert verdict(None, None, 2026, 6)[0] == "unreadable"
''',
"test_js_file": "stripe-expired-cards.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-expired-cards.mjs';

test('the expiry month itself is still valid', () => {
  const [state, detail] = verdict(6, 2026, 2026, 6);
  assert.equal(state, 'last-month');
  assert.match(detail, /end of 06\\/2026/);
});

test('last month of the same year is expired', () => {
  assert.equal(verdict(5, 2026, 2026, 6)[0], 'expired');
});

test('a previous year is expired whatever the month', () => {
  assert.equal(verdict(12, 2025, 2026, 1)[0], 'expired');
});

test('an expired default is escalated', () => {
  const [state, detail] = verdict(1, 2024, 2026, 6, true);
  assert.equal(state, 'expired-default');
  assert.match(detail, /expired_card/);
});

test('a card with no expiry fields is not silently valid', () => {
  assert.equal(verdict(null, null, 2026, 6)[0], 'unreadable');
});
''',
"faq": [
 ("Does Stripe not update expired cards automatically?",
  "For many of them, yes. The automatic card updater handles a large share of US-issued Visa, Mastercard, Amex and Discover reissues, and when it works the customer never notices. Coverage outside that is partial and varies by issuer and country, and no field on the PaymentMethod tells you whether a given card participates. So you cannot rely on it and you cannot predict where it will fail."),
 ("Is a card valid on the last day of its expiry month?",
  "Yes. Expiry is the end of the stated month, so a card marked 06/2026 works through 30 June 2026. That is why the check compares strictly less-than within the same year, and reports the current month as a separate state rather than as expired."),
 ("Why detach the old card instead of leaving it?",
  "Because nothing else will, and while it is attached your own UI renders it as a card on file. A customer who checks their account after a failed payment sees a valid-looking card and concludes the failure is on your side, which turns a two-minute self-service fix into a support ticket."),
 ("What is payment_method.automatically_updated for?",
  "It fires when the card network updates a saved card's details behind the scenes. Subscribing to it keeps your local copy of exp_month, exp_year and last4 in step with Stripe's. Without it, the updater silently fixes the card at Stripe while your database and your account page keep showing the old one."),
 ("Should I warn customers before the card expires?",
  "Yes, and it is the only part of this that reliably recovers revenue. Once the renewal has declined you are relying on a dunning email reaching someone and persuading them to re-enter card details, which converts poorly. A Customer Portal link sent while the card still works converts far better."),
],
"related": [
 ("/stripe/subscription-without-payment-method/", "An active subscription has no payment method attached"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions accumulate unnoticed"),
 ("/stripe/trial-ends-without-payment-method/", "A trial ends with no payment method on file"),
],
"citations": [CITE_PM_OBJ, CITE_PM_LIST, CITE_CARDS, CITE_DECLINES],
},

]
