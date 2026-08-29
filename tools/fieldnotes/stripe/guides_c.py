#!/usr/bin/env python3
"""/stripe/ field notes — subscriptions and billing.

Four problems that all share one shape: the subscription object reads fine, or
reads like something a human would ignore, while the money either never arrives
or arrives and buys nothing. Every script here is READ-ONLY. They hold a
credential to a live payments account, so none of them writes: they classify
what they find and print the repair for a person to run.
"""

CITE_SUB_OBJ = ("The subscription object — Stripe API reference",
                "https://docs.stripe.com/api/subscriptions/object")
CITE_SUB_OVERVIEW = ("How subscriptions work — Stripe Docs",
                     "https://docs.stripe.com/billing/subscriptions/overview")
CITE_COLLECTION = ("Collection methods — Stripe Docs",
                   "https://docs.stripe.com/billing/collection-method")
CITE_RETRIES = ("Smart Retries — Stripe Docs",
                "https://docs.stripe.com/billing/revenue-recovery/smart-retries")
CITE_TRIALS = ("Trial periods on subscriptions — Stripe Docs",
               "https://docs.stripe.com/billing/subscriptions/trials")
CITE_SUB_CREATE = ("Create a subscription — Stripe API reference",
                   "https://docs.stripe.com/api/subscriptions/create")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

CHIPS = ["Read-only key", "Python and Node.js", "Tests included"]

GUIDES = [

{
"slug": "subscriptions-stuck-incomplete",
"title": "Incomplete subscriptions die silently after 23 hours",
"description": "A subscription that never gets its first invoice paid sits in incomplete for exactly 23 hours, then expires and cannot be revived.",
"h1": "incomplete subscriptions die silently after 23 hours",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe subscription incomplete", "incomplete_expired stripe",
             "stripe subscription never activates", "payment_behavior default_incomplete",
             "stripe first invoice unpaid"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Someone filled in the card form, saw a spinner, and closed the tab believing they had subscribed. Stripe has a subscription for them in <code>incomplete</code>. In under a day that record becomes <code>incomplete_expired</code>, the open invoice is voided, and there is nothing left to recover &mdash; no charge, no error, no ticket.",
"short_answer": """<p>Read <code>GET /v1/subscriptions?status=incomplete&amp;limit=100</code> and age every row against its <code>created</code> timestamp. Anything older than <strong>82800 seconds</strong> &mdash; 23 hours &mdash; is already past the point Stripe gives up on.</p>
<p>A handful of rows minutes old is normal: those are customers mid-confirmation. Rows hours old are not, and they are the signal. They mean the first invoice's PaymentIntent is never being confirmed, which is a bug in the handoff between your server and your client, not a card problem.</p>""",
"problem": """<p>A subscription created with <code>collection_method=charge_automatically</code> does not become <code>active</code> until its first invoice is paid. Until then it sits in <code>incomplete</code>, which is a real subscription object that shows up in the Dashboard, has an id, and bills nobody.</p>
<p>The window is 23 hours and it is fixed. After it, Stripe moves the subscription to <code>incomplete_expired</code>, voids the open invoice, and that state is terminal. You cannot reopen it, re-confirm it, or transition it back. The only path forward is a brand new subscription, which means going back to a customer who already believes they are a paying customer and asking them to sign up again.</p>
<p>What makes this expensive is that it fails on the happy path. The card was fine. The customer did everything right.</p>""",
"why": """<p><strong>The client never confirms the PaymentIntent.</strong> The documented flow is to create the subscription with <code>payment_behavior=default_incomplete</code>, hand the first invoice's client secret to the browser, and confirm it there. An integration that creates the subscription server-side and then redirects to a success page has skipped the confirmation entirely. Every signup lands in <code>incomplete</code> and stays there.</p>
<p><strong>The client secret gets lost between the two halves.</strong> A redirect that drops a query parameter, a single-page app that remounts and refetches, an error boundary that swallows the confirm call &mdash; the subscription exists and the secret needed to finish it does not.</p>
<p><strong>Nothing in your logs says so.</strong> The <code>POST /v1/subscriptions</code> call returned 200. From the server's point of view the signup worked. The failure is the absence of a second call that nobody is counting.</p>
<p><strong>The 23 hours run out overnight.</strong> A problem that starts at 5pm has expired every affected record before anyone opens a dashboard the next morning, so the evidence you find is a pile of <code>incomplete_expired</code> rather than something you can still act on.</p>""",
"steps": [
 {"h": "List the incomplete subscriptions and age them",
  "body": """<p>One GET call. Sort by <code>created</code> and look at the oldest. If the oldest is twenty minutes old you are watching normal traffic mid-flow; if it is nine hours old, the confirmation step is not happening at all.</p>"""},
 {"h": "Separate the two populations",
  "body": """<p>Rows under an hour old are noise. Rows over an hour old are the finding, because no real customer spends an hour on a card form. The script draws that line explicitly rather than reporting one undifferentiated count.</p>"""},
 {"h": "Check what fraction of signups this is",
  "body": """<p>Compare the count against subscriptions that reached <code>active</code> over the same period. A couple of stragglers a week is abandonment. A third of your signups is a broken integration, and the number tells you which conversation to have.</p>"""},
 {"h": "Fix the creation call, not the stuck records",
  "body": """<p>Create with <code>payment_behavior=default_incomplete</code>, expand the latest invoice, pass its confirmation secret to the client, and confirm it in the same session. Until that is true, every fix you apply to individual subscriptions is refilling a bucket with a hole in it.</p>"""},
 {"h": "Accept that the expired ones are gone",
  "body": """<p>Past 23 hours there is no API call that revives a subscription. The repair the script prints is a fresh <code>POST /v1/subscriptions</code> with the customer and price, which needs a payment method you do not have yet. That is a customer email, not a script.</p>"""},
],
"verify": """<p>Re-run the script after a normal day of signups. Everything it reports should be minutes old, not hours.</p>
<pre><code class="language-bash">python3 stripe_incomplete_subs.py
# 3 incomplete subscription(s), 0 past the 23 hour window, 0 stalled</code></pre>""",
"code_intro": "One GET request and no writes: a restricted key with read access to Subscriptions is enough, and is what you should give it. The ageing rules are a pure function, so the 23-hour boundary is something you can read and test rather than something buried in a loop.",
"py_file": "stripe_incomplete_subs.py",
"py": '''"""Report Stripe subscriptions stuck in incomplete before the 23-hour deadline.

Read only. One GET request, no writes: give this a RESTRICTED key with read
access to Subscriptions. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_incomplete_subs")

API = "https://api.stripe.com/v1"

# Stripe holds an unpaid first invoice open for exactly 23 hours, then moves the
# subscription to the terminal incomplete_expired and voids the invoice.
WINDOW = 82800
# The last stretch before that, where a human can still rescue an individual one.
LAST_CHANCE = 7200


def verdict(sub, now, grace=3600):
    """Classify one incomplete subscription by how long it has sat unconfirmed.

    Pure, so the 23-hour boundary can be tested without a network. `grace` is how
    long a real customer might plausibly spend on the confirmation step; anything
    older than that was never confirmed at all.
    """
    created = sub.get("created")
    if not isinstance(created, (int, float)):
        return ("unknown", "no created timestamp, so this row cannot be aged")
    age = now - created
    if age >= WINDOW:
        return ("expired",
                "%.1f h old: past the 23 hour window, so the invoice is voided and "
                "this record cannot be revived" % (age / 3600.0))
    if age >= WINDOW - LAST_CHANCE:
        return ("expiring",
                "%.1f h old: under %.1f h left before Stripe expires it"
                % (age / 3600.0, (WINDOW - age) / 3600.0))
    if age >= grace:
        return ("stalled",
                "%.1f h old and still unconfirmed: the first PaymentIntent was "
                "never confirmed by the client" % (age / 3600.0))
    return ("pending",
            "%.0f min old: a customer may still be on the confirmation step"
            % (age / 60.0))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Walk a list endpoint. Read only; every call here is a GET."""
    out = []
    params = dict(params, limit=100)
    while True:
        page = get(session, path, **params)
        out.extend(page.get("data", []))
        if not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = page["data"][-1]["id"]
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--grace", type=int, default=3600,
                    help="seconds a confirmation may plausibly take (default 3600)")
    ap.add_argument("--max", type=int, default=1000,
                    help="stop after this many subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    subs = page_all(s, "/subscriptions", args.max, status="incomplete")
    if not subs:
        log.info("no incomplete subscriptions for this key's mode")
        return 0

    now = time.time()
    counts = {}
    for sub in subs:
        state, detail = verdict(sub, now, args.grace)
        counts[state] = counts.get(state, 0) + 1
        line = "%-8s %s  %s" % (state, sub.get("id", "?"), detail)
        if state == "pending":
            log.info(line)
            continue
        log.warning(line)
        if state == "expired":
            log.warning("  repair: unrecoverable. Create a new subscription: "
                        "POST %s/subscriptions -d customer=%s -d items[0][price]=... "
                        "-d default_payment_method=...",
                        API, sub.get("customer", "cus_..."))
        else:
            log.warning("  repair: confirm the first invoice's PaymentIntent client "
                        "side before %s/subscriptions/%s expires", API, sub.get("id"))

    bad = len(subs) - counts.get("pending", 0)
    log.info("%d incomplete subscription(s), %d past the 23 hour window, %d stalled",
             len(subs), counts.get("expired", 0), counts.get("stalled", 0))
    if bad:
        log.warning("structural fix: create with payment_behavior=default_incomplete "
                    "and confirm the invoice's client secret in the same session")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-incomplete-subs.mjs",
"js": '''/**
 * Report Stripe subscriptions stuck in incomplete before the 23-hour deadline.
 *
 * Read only. One GET request, no writes: give this a RESTRICTED key with read
 * access to Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Stripe holds an unpaid first invoice open for exactly 23 hours, then moves the
// subscription to the terminal incomplete_expired and voids the invoice.
export const WINDOW = 82800;
// The last stretch before that, where a human can still rescue an individual one.
const LAST_CHANCE = 7200;

/**
 * Classify one incomplete subscription by how long it has sat unconfirmed.
 * Pure, so the 23-hour boundary can be tested without a network.
 */
export function verdict(sub, now, grace = 3600) {
  const created = sub.created;
  if (typeof created !== 'number') {
    return ['unknown', 'no created timestamp, so this row cannot be aged'];
  }
  const age = now - created;
  if (age >= WINDOW) {
    return ['expired',
      `${(age / 3600).toFixed(1)} h old: past the 23 hour window, so the invoice ` +
      'is voided and this record cannot be revived'];
  }
  if (age >= WINDOW - LAST_CHANCE) {
    return ['expiring',
      `${(age / 3600).toFixed(1)} h old: under ${((WINDOW - age) / 3600).toFixed(1)} h ` +
      'left before Stripe expires it'];
  }
  if (age >= grace) {
    return ['stalled',
      `${(age / 3600).toFixed(1)} h old and still unconfirmed: the first ` +
      'PaymentIntent was never confirmed by the client'];
  }
  return ['pending',
    `${(age / 60).toFixed(0)} min old: a customer may still be on the confirmation step`];
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

async function pageAll(key, path, limit, params = {}) {
  const out = [];
  const q = { ...params, limit: 100 };
  for (;;) {
    const page = await get(key, path, q);
    out.push(...(page.data ?? []));
    if (!page.has_more || out.length >= limit) break;
    q.starting_after = page.data[page.data.length - 1].id;
  }
  return out.slice(0, limit);
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const subs = await pageAll(key, '/subscriptions', 1000, { status: 'incomplete' });
  if (subs.length === 0) {
    console.log("no incomplete subscriptions for this key's mode");
    return;
  }

  const now = Date.now() / 1000;
  const counts = new Map();
  for (const sub of subs) {
    const [state, detail] = verdict(sub, now);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    const line = `${state.padEnd(8)} ${sub.id ?? '?'}  ${detail}`;
    if (state === 'pending') { console.log(line); continue; }
    console.warn(line);
    if (state === 'expired') {
      console.warn(`  repair: unrecoverable. Create a new subscription: ` +
        `POST ${API}/subscriptions -d customer=${sub.customer ?? 'cus_...'} ` +
        `-d items[0][price]=... -d default_payment_method=...`);
    } else {
      console.warn(`  repair: confirm the first invoice's PaymentIntent client side ` +
        `before ${API}/subscriptions/${sub.id} expires`);
    }
  }

  const bad = subs.length - (counts.get('pending') ?? 0);
  console.log(`${subs.length} incomplete subscription(s), ` +
    `${counts.get('expired') ?? 0} past the 23 hour window, ` +
    `${counts.get('stalled') ?? 0} stalled`);
  if (bad) {
    console.warn('structural fix: create with payment_behavior=default_incomplete ' +
      "and confirm the invoice's client secret in the same session");
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
"test_intro": "The boundary worth pinning is 82800 seconds, because it is the one number in this note that is not a judgement call. The other case to hold still is the young row: it has to stay quiet, or the check cries wolf on every healthy signup and gets muted within a week.",
"test_py_file": "test_stripe_incomplete_subs.py",
"test_py": '''from stripe_incomplete_subs import WINDOW, verdict

NOW = 1_800_000_000


def test_a_minutes_old_subscription_is_not_an_alert():
    state, detail = verdict({"created": NOW - 1800}, NOW)
    assert state == "pending"
    assert "confirmation step" in detail


def test_hours_old_and_unconfirmed_is_the_finding():
    state, detail = verdict({"created": NOW - 5 * 3600}, NOW)
    assert state == "stalled"
    assert "never confirmed" in detail


def test_the_last_two_hours_are_called_out_separately():
    # Still rescuable by a human, which is why it is not folded into "stalled".
    state, detail = verdict({"created": NOW - (WINDOW - 3600)}, NOW)
    assert state == "expiring"
    assert "left before" in detail


def test_exactly_23_hours_is_already_expired():
    # 82800 is the boundary Stripe documents, not a rounded-off guess.
    state, detail = verdict({"created": NOW - WINDOW}, NOW)
    assert state == "expired"
    assert "cannot be revived" in detail


def test_a_row_with_no_timestamp_is_not_silently_healthy():
    state, _ = verdict({}, NOW)
    assert state == "unknown"
''',
"test_js_file": "stripe-incomplete-subs.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, WINDOW } from './stripe-incomplete-subs.mjs';

const NOW = 1_800_000_000;

test('a minutes old subscription is not an alert', () => {
  const [state, detail] = verdict({ created: NOW - 1800 }, NOW);
  assert.equal(state, 'pending');
  assert.match(detail, /confirmation step/);
});

test('hours old and unconfirmed is the finding', () => {
  const [state, detail] = verdict({ created: NOW - 5 * 3600 }, NOW);
  assert.equal(state, 'stalled');
  assert.match(detail, /never confirmed/);
});

test('the last two hours are called out separately', () => {
  const [state, detail] = verdict({ created: NOW - (WINDOW - 3600) }, NOW);
  assert.equal(state, 'expiring');
  assert.match(detail, /left before/);
});

test('exactly 23 hours is already expired', () => {
  const [state, detail] = verdict({ created: NOW - WINDOW }, NOW);
  assert.equal(state, 'expired');
  assert.match(detail, /cannot be revived/);
});

test('a row with no timestamp is not silently healthy', () => {
  assert.equal(verdict({}, NOW)[0], 'unknown');
});
''',
"faq": [
 ("Can I recover a subscription that already went incomplete_expired?",
  "No. It is a terminal status: the open invoice has been voided and there is no transition out of it. The only way forward is a new subscription with POST /v1/subscriptions, which needs a payment method you do not have, so in practice it is an email to the customer rather than a script."),
 ("How long exactly does a subscription stay incomplete?",
  "23 hours, or 82800 seconds, measured from creation. It applies to the first invoice on a charge_automatically subscription that has not been paid. The window is not configurable."),
 ("Is a small number of incomplete subscriptions normal?",
  "Yes, if they are minutes old. Those are customers who are mid-confirmation right now. The number that matters is how many are older than an hour, because nobody spends an hour on a card form."),
 ("Why do these appear even though the card was valid?",
  "Because no charge was ever attempted. The subscription creation call succeeded and the client-side confirmation of the first invoice's PaymentIntent never happened, so the card was never used. It is a handoff bug, not a decline."),
 ("Does this happen with collection_method=send_invoice too?",
  "No. The 23-hour incomplete window applies to charge_automatically. Subscriptions billed by emailed invoice go active and leave the invoice open for its due date instead, which is a different problem with a different deadline."),
],
"related": [
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge"),
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after retries"),
 ("/woocommerce/orders-stuck-requires-action-3ds/", "Orders stuck on requires_action 3DS"),
],
"citations": [CITE_SUB_OBJ, CITE_SUB_OVERVIEW, CITE_COLLECTION, CITE_SUB_CREATE],
},

{
"slug": "subscription-without-payment-method",
"title": "Active subscriptions with nothing to charge on renewal",
"description": "Some subscriptions read active but have no payment method in any of the four places Stripe looks. Every renewal fails and no retry is ever scheduled.",
"h1": "active subscriptions with nothing to charge on renewal",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe subscription no payment method",
             "invoice_settings default_payment_method", "stripe renewal fails",
             "stripe default_source null", "stripe subscription not retrying"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The subscription says <code>active</code>. The customer has access, the MRR chart counts them, and the renewal date is in the calendar. Then the renewal date arrives and the invoice fails, and it fails again next month, and Stripe never retries any of it &mdash; because there is nothing to retry against.",
"short_answer": """<p>Stripe resolves a payment method for a renewal in a strict order: <code>subscription.default_payment_method</code>, then <code>subscription.default_source</code>, then <code>customer.invoice_settings.default_payment_method</code>, then <code>customer.default_source</code>. If all four are null the invoice cannot be paid.</p>
<p>Read <code>GET /v1/subscriptions?status=active&amp;limit=100&amp;expand[]=data.customer</code> and check all four fields on every row. Repeat for <code>status=trialing</code>, which is where most of them are hiding.</p>""",
"problem": """<p>A card attached to a customer is not the same thing as a card attached to a subscription, and neither is the same thing as a card that was merely used once. A PaymentMethod can exist on the customer, be visible in the Dashboard, and still not be any of the four defaults Stripe consults at renewal time.</p>
<p>Nothing about the subscription object flags this. <code>status</code> is <code>active</code> because the first payment succeeded. There is no <code>chargeable</code> boolean, no warning banner, no event. The four fields are just null, and null is what an unexpanded response looks like too, which is part of why nobody checks.</p>
<p>The failure is also delayed by exactly one billing period. A monthly plan set up wrong in January is fine until February. An annual plan set up wrong is fine until the following year, by which time the person who built the flow has moved on.</p>""",
"why": """<p><strong>The card was collected as a one-off payment.</strong> A PaymentIntent confirmed without <code>setup_future_usage</code> charges the card and does not save it as a default. The payment succeeds, the subscription activates, and no default is ever written.</p>
<p><strong>The default was set on the customer but not the subscription, or the reverse.</strong> Both work, because Stripe falls through the list. What does not work is setting it on neither, which is easy to do when two different code paths each assume the other did it.</p>
<p><strong>A payment method was detached and the default was not repointed.</strong> Detaching a PaymentMethod clears it from wherever it was the default. The subscription keeps running with a dangling null.</p>
<p><strong>Stripe does not retry when there is nothing to charge.</strong> This is the part that surprises people. Smart Retries exist to work around temporary declines; with no payment method available there is no decline to retry, so the recovery machinery you are relying on never engages. The invoice simply fails and stays failed.</p>""",
"steps": [
 {"h": "List active subscriptions with the customer expanded",
  "body": """<p><code>expand[]=data.customer</code> is not optional here. Without it the customer is a bare id string and you cannot see the two customer-level defaults, which means you cannot tell a genuinely unchargeable subscription from one you simply have not looked at properly.</p>"""},
 {"h": "Walk all four fields in Stripe's own order",
  "body": """<p>Check <code>default_payment_method</code>, then <code>default_source</code>, then the customer's <code>invoice_settings.default_payment_method</code>, then the customer's <code>default_source</code>. Report which one resolved, not just whether one did &mdash; knowing that a subscription is relying on a customer-level fallback is worth something on its own.</p>"""},
 {"h": "Run it against trialing as well",
  "body": """<p>Trialing subscriptions are the biggest source of these, because a trial that did not require a card at signup has nothing attached by definition. Those are covered separately, but the same query finds them.</p>"""},
 {"h": "Collect a card before setting anything",
  "body": """<p>There is no API call that conjures a payment method. The repair starts with a SetupIntent or a billing-portal link sent to the customer. Only once a PaymentMethod exists can you point the defaults at it.</p>"""},
 {"h": "Set it in both places",
  "body": """<p>Set <code>invoice_settings[default_payment_method]</code> on the customer and <code>default_payment_method</code> on the subscription. Retries follow the field the failure occurred on, so a single-sided fix leaves you relying on the fallthrough working exactly as you assumed.</p>"""},
],
"verify": """<p>Re-run the script. Every row should report which field the charge will come from, and the unchargeable count should be zero.</p>
<pre><code class="language-bash">python3 stripe_sub_payment_method.py
# 214 subscription(s) checked, 0 unchargeable, 31 relying on a customer-level default</code></pre>""",
"code_intro": "Two GET requests and no writes: a restricted key with read access to Subscriptions and Customers is enough. The resolution order lives in one pure function, in the same sequence Stripe documents, so it can be read against the docs line by line and tested without a network.",
"py_file": "stripe_sub_payment_method.py",
"py": '''"""Report Stripe subscriptions with no payment method in any of the four slots.

Read only. GET requests only, no writes: give this a RESTRICTED key with read
access to Subscriptions and Customers. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_sub_payment_method")

API = "https://api.stripe.com/v1"


def verdict(sub):
    """Walk Stripe's payment-method resolution order for one subscription.

    Pure, so the order can be tested against the documented one without a network.
    The order is: subscription.default_payment_method, subscription.default_source,
    customer.invoice_settings.default_payment_method, customer.default_source.
    """
    if sub.get("default_payment_method"):
        return ("subscription", "charges subscription.default_payment_method")
    if sub.get("default_source"):
        return ("subscription",
                "charges subscription.default_source, a legacy source object")
    customer = sub.get("customer")
    if not isinstance(customer, dict):
        return ("unknown",
                "customer was not expanded, so the two customer-level defaults "
                "cannot be read; re-run with expand[]=data.customer")
    settings = customer.get("invoice_settings") or {}
    if settings.get("default_payment_method"):
        return ("customer",
                "falls back to customer.invoice_settings.default_payment_method")
    if customer.get("default_source"):
        return ("customer",
                "falls back to customer.default_source, a legacy source object")
    return ("unchargeable",
            "all four resolution slots are null, so the renewal invoice cannot be "
            "paid and Stripe schedules no retry")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_subscriptions(session, status, limit):
    """Walk one status page by page. Read only; every call here is a GET."""
    out = []
    params = {"status": status, "limit": 100, "expand[]": "data.customer"}
    while True:
        page = get(session, "/subscriptions", **params)
        out.extend(page.get("data", []))
        if not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = page["data"][-1]["id"]
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", action="append", default=None,
                    help="subscription status to check (repeatable)")
    ap.add_argument("--max", type=int, default=1000,
                    help="stop after this many subscriptions per status")
    args = ap.parse_args()
    statuses = args.status or ["active", "trialing"]

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    checked = 0
    counts = {}
    for status in statuses:
        for sub in page_subscriptions(s, status, args.max):
            checked += 1
            state, detail = verdict(sub)
            counts[state] = counts.get(state, 0) + 1
            if state == "subscription":
                continue
            line = "%-13s %s (%s)  %s" % (state, sub.get("id", "?"), status, detail)
            if state == "customer":
                log.info(line)
                continue
            log.warning(line)
            cus = sub.get("customer")
            cus_id = cus.get("id") if isinstance(cus, dict) else cus
            log.warning("  repair: collect a card with a SetupIntent or the billing "
                        "portal, then POST %s/customers/%s "
                        "-d invoice_settings[default_payment_method]=pm_...",
                        API, cus_id or "cus_...")
            log.warning("  and pin it to the subscription too: POST %s/subscriptions/%s "
                        "-d default_payment_method=pm_...", API, sub.get("id"))

    log.info("%d subscription(s) checked, %d unchargeable, %d relying on a "
             "customer-level default", checked, counts.get("unchargeable", 0),
             counts.get("customer", 0))
    if counts.get("unknown"):
        log.warning("%d row(s) could not be classified: re-run with the customer "
                    "expanded", counts["unknown"])
    return 1 if counts.get("unchargeable") or counts.get("unknown") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-sub-payment-method.mjs",
"js": '''/**
 * Report Stripe subscriptions with no payment method in any of the four slots.
 *
 * Read only. GET requests only, no writes: give this a RESTRICTED key with read
 * access to Subscriptions and Customers. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Walk Stripe's payment-method resolution order for one subscription.
 * Pure, so the order can be tested against the documented one without a network.
 */
export function verdict(sub) {
  if (sub.default_payment_method) {
    return ['subscription', 'charges subscription.default_payment_method'];
  }
  if (sub.default_source) {
    return ['subscription', 'charges subscription.default_source, a legacy source object'];
  }
  const customer = sub.customer;
  if (customer === null || typeof customer !== 'object') {
    return ['unknown',
      'customer was not expanded, so the two customer-level defaults cannot be ' +
      'read; re-run with expand[]=data.customer'];
  }
  const settings = customer.invoice_settings ?? {};
  if (settings.default_payment_method) {
    return ['customer', 'falls back to customer.invoice_settings.default_payment_method'];
  }
  if (customer.default_source) {
    return ['customer', 'falls back to customer.default_source, a legacy source object'];
  }
  return ['unchargeable',
    'all four resolution slots are null, so the renewal invoice cannot be paid ' +
    'and Stripe schedules no retry'];
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

async function pageSubscriptions(key, status, limit) {
  const out = [];
  const q = { status, limit: 100, 'expand[]': 'data.customer' };
  for (;;) {
    const page = await get(key, '/subscriptions', q);
    out.push(...(page.data ?? []));
    if (!page.has_more || out.length >= limit) break;
    q.starting_after = page.data[page.data.length - 1].id;
  }
  return out.slice(0, limit);
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  let checked = 0;
  const counts = new Map();
  for (const status of ['active', 'trialing']) {
    for (const sub of await pageSubscriptions(key, status, 1000)) {
      checked += 1;
      const [state, detail] = verdict(sub);
      counts.set(state, (counts.get(state) ?? 0) + 1);
      if (state === 'subscription') continue;
      const line = `${state.padEnd(13)} ${sub.id ?? '?'} (${status})  ${detail}`;
      if (state === 'customer') { console.log(line); continue; }
      console.warn(line);
      const cus = typeof sub.customer === 'object' && sub.customer !== null
        ? sub.customer.id : sub.customer;
      console.warn(`  repair: collect a card with a SetupIntent or the billing portal, ` +
        `then POST ${API}/customers/${cus ?? 'cus_...'} ` +
        `-d invoice_settings[default_payment_method]=pm_...`);
      console.warn(`  and pin it to the subscription too: ` +
        `POST ${API}/subscriptions/${sub.id} -d default_payment_method=pm_...`);
    }
  }

  console.log(`${checked} subscription(s) checked, ` +
    `${counts.get('unchargeable') ?? 0} unchargeable, ` +
    `${counts.get('customer') ?? 0} relying on a customer-level default`);
  if (counts.get('unknown')) {
    console.warn(`${counts.get('unknown')} row(s) could not be classified: re-run ` +
      'with the customer expanded');
  }
  process.exitCode = (counts.get('unchargeable') ?? 0) + (counts.get('unknown') ?? 0)
    ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "These tests are really a transcription check against Stripe's documented resolution order, one case per slot, in sequence. The last one matters just as much: an unexpanded customer has to come back as <code>unknown</code>, because a bare id string looks exactly like an absent default and reporting it as unchargeable would send someone chasing hundreds of healthy subscriptions.",
"test_py_file": "test_stripe_sub_payment_method.py",
"test_py": '''from stripe_sub_payment_method import verdict


def test_subscription_level_payment_method_wins():
    state, detail = verdict({"default_payment_method": "pm_1", "customer": {}})
    assert state == "subscription"
    assert "subscription.default_payment_method" in detail


def test_legacy_subscription_source_is_still_chargeable():
    state, detail = verdict({"default_source": "card_1", "customer": {}})
    assert state == "subscription"
    assert "legacy" in detail


def test_customer_invoice_settings_are_the_third_slot():
    sub = {"customer": {"invoice_settings": {"default_payment_method": "pm_2"}}}
    state, detail = verdict(sub)
    assert state == "customer"
    assert "invoice_settings" in detail


def test_customer_default_source_is_the_fourth_slot():
    state, _ = verdict({"customer": {"default_source": "card_2"}})
    assert state == "customer"


def test_all_four_null_is_unchargeable_and_says_no_retry():
    sub = {"customer": {"invoice_settings": {"default_payment_method": None},
                        "default_source": None}}
    state, detail = verdict(sub)
    assert state == "unchargeable"
    assert "no retry" in detail


def test_unexpanded_customer_is_not_reported_as_unchargeable():
    # A bare id string looks identical to an absent default. Saying "unchargeable"
    # here would point someone at every healthy subscription in the account.
    state, detail = verdict({"customer": "cus_123"})
    assert state == "unknown"
    assert "expand" in detail
''',
"test_js_file": "stripe-sub-payment-method.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-sub-payment-method.mjs';

test('subscription level payment method wins', () => {
  const [state, detail] = verdict({ default_payment_method: 'pm_1', customer: {} });
  assert.equal(state, 'subscription');
  assert.match(detail, /subscription\\.default_payment_method/);
});

test('legacy subscription source is still chargeable', () => {
  const [state, detail] = verdict({ default_source: 'card_1', customer: {} });
  assert.equal(state, 'subscription');
  assert.match(detail, /legacy/);
});

test('customer invoice settings are the third slot', () => {
  const [state, detail] = verdict({
    customer: { invoice_settings: { default_payment_method: 'pm_2' } },
  });
  assert.equal(state, 'customer');
  assert.match(detail, /invoice_settings/);
});

test('customer default source is the fourth slot', () => {
  assert.equal(verdict({ customer: { default_source: 'card_2' } })[0], 'customer');
});

test('all four null is unchargeable and says no retry', () => {
  const [state, detail] = verdict({
    customer: { invoice_settings: { default_payment_method: null }, default_source: null },
  });
  assert.equal(state, 'unchargeable');
  assert.match(detail, /no retry/);
});

test('unexpanded customer is not reported as unchargeable', () => {
  const [state, detail] = verdict({ customer: 'cus_123' });
  assert.equal(state, 'unknown');
  assert.match(detail, /expand/);
});
''',
"faq": [
 ("Where exactly does Stripe look for a card at renewal?",
  "In this order: subscription.default_payment_method, subscription.default_source, customer.invoice_settings.default_payment_method, customer.default_source. The first non-null one is used. If all four are null the invoice cannot be paid."),
 ("The customer clearly has a card in the Dashboard. Why is it not used?",
  "Because a PaymentMethod attached to a customer is not automatically any of the four defaults. Attaching and defaulting are separate operations, and a card that was used once for a one-off payment is attached without being defaulted."),
 ("Will Stripe retry the failed renewal once I add a card?",
  "Not the invoice that already failed with nothing to charge, because no retry was ever scheduled for it. Add the payment method, then pay the open invoice directly. Future renewals will resolve normally."),
 ("Should I set the default on the customer or the subscription?",
  "Both. The customer-level default covers everything that customer is billed for; the subscription-level one covers the case where a customer has several subscriptions on different cards. Retries follow the field the failure occurred on, so setting one side only leaves the fallthrough doing work you have not tested."),
 ("Does this affect subscriptions billed by emailed invoice?",
  "No. With collection_method=send_invoice Stripe emails a hosted invoice and the customer pays it themselves, so no stored default is required. The check only applies to charge_automatically subscriptions."),
],
"related": [
 ("/stripe/trial-ends-without-payment-method/", "Trials ending with no card on file"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access"),
 ("/shopify/contract-has-no-valid-payment-method/", "A contract with no valid payment method"),
],
"citations": [CITE_RETRIES, CITE_SUB_OBJ, CITE_SUB_OVERVIEW, CITE_KEYS],
},

{
"slug": "past-due-subscriptions-accumulating",
"title": "past_due subscriptions keep their access forever",
"description": "Failed renewals move a subscription to past_due and leave it there. The app only checks for canceled, so the customer keeps everything and pays nothing.",
"h1": "past_due subscriptions keep their access forever",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe past_due subscription", "stripe dunning not cancelling",
             "revoke access on failed payment", "stripe smart retries exhausted",
             "past due subscriptions pile up"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Renewals have been failing for months and nobody noticed, because the customers are still logged in and still using the product. The entitlement check in your app asks whether the subscription is canceled. It is not canceled. It is <code>past_due</code>, which the check has never heard of, so the answer is yes, let them in.",
"short_answer": """<p>Read <code>GET /v1/subscriptions?status=past_due&amp;limit=100&amp;expand[]=data.latest_invoice</code>. Every row is a customer with access and no payment. Age each one from <code>latest_invoice.created</code> and read <code>latest_invoice.attempt_count</code> to tell live dunning from a subscription that Stripe has finished with and parked.</p>
<p>Then fix the entitlement check: gate on <code>status</code> being <code>active</code> or <code>trialing</code>, not on it being anything other than <code>canceled</code>.</p>""",
"problem": """<p><code>past_due</code> means the renewal invoice failed and Stripe is working on it. What happens at the end of that work is a Dashboard setting, and one of the valid choices is to do nothing &mdash; leave the subscription past due. That is a silent, permanent state. Stripe keeps generating an invoice each period, each one fails, and the pile grows.</p>
<p>Two independent mistakes have to line up for this to hurt, and they usually do. The billing side is configured to leave past-due subscriptions alone, and the application side treats every status except <code>canceled</code> as entitled. Each is defensible on its own. Together they mean a customer whose card expired in March is still using the product in October.</p>
<p>It is also invisible in the numbers people watch. These subscriptions still count in active-subscriber reports built on "not canceled", so churn looks fine while the cash does not arrive.</p>""",
"why": """<p><strong>The end-of-retries behaviour is set to leave it past due.</strong> Under Billing, Revenue recovery, Retries, the post-retry action can be cancel the subscription, mark it unpaid, or leave it as is. The last one is a real option and it produces exactly this.</p>
<p><strong>The entitlement check is written as a denial list.</strong> <code>status != "canceled"</code> reads as reasonable until you enumerate the statuses it lets through: <code>incomplete</code>, <code>past_due</code>, <code>unpaid</code>, and <code>paused</code> all pass.</p>
<p><strong>Nothing distinguishes a retrying subscription from a parked one.</strong> Both read <code>past_due</code>. The difference is in the latest invoice: an invoice a few days old with a rising <code>attempt_count</code> is dunning in progress and may still recover. An invoice two months old is a subscription Stripe has stopped working on and nobody has closed.</p>
<p><strong>An <code>attempt_count</code> of zero is a different problem wearing the same status.</strong> No attempt at all usually means no payment method resolved, so there is nothing for Smart Retries to retry and the dunning you are waiting on is never going to happen.</p>""",
"steps": [
 {"h": "Pull the past-due list with its latest invoice",
  "body": """<p><code>expand[]=data.latest_invoice</code> turns the invoice id into an object, which is where both signals live. Without it you get a list of ids and no way to tell which of them still have a chance.</p>"""},
 {"h": "Split live dunning from parked subscriptions",
  "body": """<p>Age the invoice. Inside about a month, with attempts on the clock, retries may still be running and the right move is to wait or email. Beyond that, no configuration keeps retrying, and the subscription is sitting there purely because nothing closed it.</p>"""},
 {"h": "Look for zero attempts",
  "body": """<p>A past-due subscription whose invoice has never been attempted is not a dunning problem. It has no chargeable payment method, and no amount of retry configuration will help it.</p>"""},
 {"h": "Compare the count to your active subscriptions",
  "body": """<p>The ratio is the argument. Twelve past-due against four thousand active is housekeeping; twelve against ninety is a leak someone needs to own this week.</p>"""},
 {"h": "Fix the entitlement check before the billing settings",
  "body": """<p>Changing the post-retry action to cancel only helps future failures. The customers already in <code>past_due</code> keep their access until the check that granted it is corrected to an allow list of <code>active</code> and <code>trialing</code>.</p>"""},
],
"verify": """<p>Re-run the script. The parked count should be zero, and anything still listed should be inside a live retry window.</p>
<pre><code class="language-bash">python3 stripe_past_due_subs.py
# 6 past_due against 1204 active (0.5%), 0 parked, 0 never attempted</code></pre>""",
"code_intro": "Three GET requests and no writes: a restricted key with read access to Subscriptions and Invoices is enough. The split between live dunning and a parked subscription is a pure function of the invoice's age and attempt count, so the thresholds are visible and adjustable rather than implied by the output.",
"py_file": "stripe_past_due_subs.py",
"py": '''"""Report Stripe subscriptions parked in past_due while access continues.

Read only. GET requests only, no writes: give this a RESTRICTED key with read
access to Subscriptions and Invoices. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_past_due_subs")

API = "https://api.stripe.com/v1"

# No retry schedule Stripe offers runs longer than a month, so an invoice older
# than this is not waiting on anything: the subscription has simply been left.
DUNNING_DAYS = 30


def verdict(sub, now, dunning_days=DUNNING_DAYS):
    """Classify one past_due subscription from its latest invoice.

    Pure, so the difference between live dunning and a parked subscription can be
    tested without a network. Needs the invoice expanded; an unexpanded id is
    reported as unknown rather than guessed at.
    """
    invoice = sub.get("latest_invoice")
    if not isinstance(invoice, dict):
        return ("unknown",
                "latest_invoice was not expanded; re-run with "
                "expand[]=data.latest_invoice")
    created = invoice.get("created")
    if not isinstance(created, (int, float)):
        return ("unknown", "latest_invoice has no created timestamp to age")
    attempts = invoice.get("attempt_count") or 0
    days = (now - created) / 86400.0
    if attempts == 0:
        return ("never-attempted",
                "invoice %.0f day(s) old with no payment attempt at all: usually no "
                "payment method resolves, so retries never run" % days)
    if days > dunning_days:
        return ("parked",
                "%d attempt(s), invoice %.0f day(s) old: past any retry schedule, so "
                "nothing further will happen to this on its own" % (attempts, days))
    return ("dunning",
            "%d attempt(s) over %.0f day(s): retries are still running and this may "
            "recover" % (attempts, days))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_subscriptions(session, status, limit, expand=None):
    """Walk one status page by page. Read only; every call here is a GET."""
    out = []
    params = {"status": status, "limit": 100}
    if expand:
        params["expand[]"] = expand
    while True:
        page = get(session, "/subscriptions", **params)
        out.extend(page.get("data", []))
        if not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = page["data"][-1]["id"]
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dunning-days", type=int, default=DUNNING_DAYS,
                    help="invoice age past which retries are certainly over")
    ap.add_argument("--max", type=int, default=1000,
                    help="stop after this many subscriptions per status")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    past_due = page_subscriptions(s, "past_due", args.max, expand="data.latest_invoice")
    active = page_subscriptions(s, "active", args.max)
    if not past_due:
        log.info("no past_due subscriptions for this key's mode")
        return 0

    now = time.time()
    counts = {}
    for sub in past_due:
        state, detail = verdict(sub, now, args.dunning_days)
        counts[state] = counts.get(state, 0) + 1
        log.warning("%-15s %s  %s", state, sub.get("id", "?"), detail)
        if state == "parked":
            log.warning("  repair: close it out with POST %s/subscriptions/%s "
                        "-d cancel_at_period_end=true, or DELETE %s/subscriptions/%s "
                        "to end it now", API, sub.get("id"), API, sub.get("id"))
        elif state == "never-attempted":
            log.warning("  repair: attach a payment method first, then pay invoice %s",
                        (sub.get("latest_invoice") or {}).get("id", "in_..."))

    ratio = 100.0 * len(past_due) / max(1, len(past_due) + len(active))
    log.info("%d past_due against %d active (%.1f%%), %d parked, %d never attempted",
             len(past_due), len(active), ratio, counts.get("parked", 0),
             counts.get("never-attempted", 0))
    log.warning("entitlement check: gate on status in (active, trialing), not on "
                "status != canceled")
    log.warning("billing setting: Billing > Revenue recovery > Retries, set the "
                "post-retry action to cancel or mark unpaid")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-past-due-subs.mjs",
"js": '''/**
 * Report Stripe subscriptions parked in past_due while access continues.
 *
 * Read only. GET requests only, no writes: give this a RESTRICTED key with read
 * access to Subscriptions and Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// No retry schedule Stripe offers runs longer than a month, so an invoice older
// than this is not waiting on anything: the subscription has simply been left.
export const DUNNING_DAYS = 30;

/**
 * Classify one past_due subscription from its latest invoice.
 * Pure, so live dunning and a parked subscription can be told apart in a test.
 */
export function verdict(sub, now, dunningDays = DUNNING_DAYS) {
  const invoice = sub.latest_invoice;
  if (invoice === null || typeof invoice !== 'object') {
    return ['unknown',
      'latest_invoice was not expanded; re-run with expand[]=data.latest_invoice'];
  }
  const created = invoice.created;
  if (typeof created !== 'number') {
    return ['unknown', 'latest_invoice has no created timestamp to age'];
  }
  const attempts = invoice.attempt_count ?? 0;
  const days = (now - created) / 86400;
  if (attempts === 0) {
    return ['never-attempted',
      `invoice ${days.toFixed(0)} day(s) old with no payment attempt at all: ` +
      'usually no payment method resolves, so retries never run'];
  }
  if (days > dunningDays) {
    return ['parked',
      `${attempts} attempt(s), invoice ${days.toFixed(0)} day(s) old: past any ` +
      'retry schedule, so nothing further will happen to this on its own'];
  }
  return ['dunning',
    `${attempts} attempt(s) over ${days.toFixed(0)} day(s): retries are still ` +
    'running and this may recover'];
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

async function pageSubscriptions(key, status, limit, expand) {
  const out = [];
  const q = { status, limit: 100 };
  if (expand) q['expand[]'] = expand;
  for (;;) {
    const page = await get(key, '/subscriptions', q);
    out.push(...(page.data ?? []));
    if (!page.has_more || out.length >= limit) break;
    q.starting_after = page.data[page.data.length - 1].id;
  }
  return out.slice(0, limit);
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const pastDue = await pageSubscriptions(key, 'past_due', 1000, 'data.latest_invoice');
  const active = await pageSubscriptions(key, 'active', 1000);
  if (pastDue.length === 0) {
    console.log("no past_due subscriptions for this key's mode");
    return;
  }

  const now = Date.now() / 1000;
  const counts = new Map();
  for (const sub of pastDue) {
    const [state, detail] = verdict(sub, now);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    console.warn(`${state.padEnd(15)} ${sub.id ?? '?'}  ${detail}`);
    if (state === 'parked') {
      console.warn(`  repair: close it out with POST ${API}/subscriptions/${sub.id} ` +
        `-d cancel_at_period_end=true, or DELETE ${API}/subscriptions/${sub.id} ` +
        `to end it now`);
    } else if (state === 'never-attempted') {
      console.warn(`  repair: attach a payment method first, then pay invoice ` +
        `${sub.latest_invoice?.id ?? 'in_...'}`);
    }
  }

  const ratio = (100 * pastDue.length) / Math.max(1, pastDue.length + active.length);
  console.log(`${pastDue.length} past_due against ${active.length} active ` +
    `(${ratio.toFixed(1)}%), ${counts.get('parked') ?? 0} parked, ` +
    `${counts.get('never-attempted') ?? 0} never attempted`);
  console.warn('entitlement check: gate on status in (active, trialing), not on ' +
    'status != canceled');
  console.warn('billing setting: Billing > Revenue recovery > Retries, set the ' +
    'post-retry action to cancel or mark unpaid');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case these tests exist for is the one where <code>attempt_count</code> is zero. It looks like the worst kind of past-due subscription and it is actually a different fault with a different repair, so folding it into the parked bucket would send someone to change a retry setting that was never going to fire.",
"test_py_file": "test_stripe_past_due_subs.py",
"test_py": '''from stripe_past_due_subs import verdict

NOW = 1_800_000_000
DAY = 86400


def inv(days_old, attempts):
    return {"id": "in_1", "created": NOW - days_old * DAY, "attempt_count": attempts}


def test_a_fresh_invoice_with_attempts_is_live_dunning():
    state, detail = verdict({"latest_invoice": inv(3, 2)}, NOW)
    assert state == "dunning"
    assert "may recover" in detail


def test_an_old_invoice_is_parked_not_dunning():
    state, detail = verdict({"latest_invoice": inv(75, 4)}, NOW)
    assert state == "parked"
    assert "nothing further will happen" in detail


def test_zero_attempts_is_its_own_fault_not_a_retry_problem():
    # No attempt means nothing to retry: this is a missing payment method, and
    # changing the retry configuration would not touch it.
    state, detail = verdict({"latest_invoice": inv(40, 0)}, NOW)
    assert state == "never-attempted"
    assert "no payment method" in detail


def test_unexpanded_invoice_is_not_classified():
    state, detail = verdict({"latest_invoice": "in_1"}, NOW)
    assert state == "unknown"
    assert "expand" in detail


def test_invoice_without_a_timestamp_is_not_classified():
    state, _ = verdict({"latest_invoice": {"attempt_count": 3}}, NOW)
    assert state == "unknown"
''',
"test_js_file": "stripe-past-due-subs.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-past-due-subs.mjs';

const NOW = 1_800_000_000;
const DAY = 86400;

const inv = (daysOld, attempts) => ({
  id: 'in_1', created: NOW - daysOld * DAY, attempt_count: attempts,
});

test('a fresh invoice with attempts is live dunning', () => {
  const [state, detail] = verdict({ latest_invoice: inv(3, 2) }, NOW);
  assert.equal(state, 'dunning');
  assert.match(detail, /may recover/);
});

test('an old invoice is parked not dunning', () => {
  const [state, detail] = verdict({ latest_invoice: inv(75, 4) }, NOW);
  assert.equal(state, 'parked');
  assert.match(detail, /nothing further will happen/);
});

test('zero attempts is its own fault not a retry problem', () => {
  const [state, detail] = verdict({ latest_invoice: inv(40, 0) }, NOW);
  assert.equal(state, 'never-attempted');
  assert.match(detail, /no payment method/);
});

test('unexpanded invoice is not classified', () => {
  const [state, detail] = verdict({ latest_invoice: 'in_1' }, NOW);
  assert.equal(state, 'unknown');
  assert.match(detail, /expand/);
});

test('invoice without a timestamp is not classified', () => {
  assert.equal(verdict({ latest_invoice: { attempt_count: 3 } }, NOW)[0], 'unknown');
});
''',
"faq": [
 ("Does past_due mean the customer still has access?",
  "That is entirely your decision, and it is the point of this note. Stripe reports the status; your application decides what it grants. If the entitlement check asks whether the status is canceled, then yes, past_due keeps full access indefinitely."),
 ("Will Stripe cancel a past_due subscription on its own?",
  "Only if you have told it to. Under Billing, Revenue recovery, Retries, the action after the retries finish can be cancel, mark unpaid, or leave the subscription past due. The last is a valid setting and produces subscriptions that sit there permanently."),
 ("What is the difference between past_due and unpaid?",
  "past_due means the renewal failed and Stripe may still be retrying. unpaid is one of the end states: Stripe still creates invoices but closes them immediately and attempts no payment. Both keep access if your check only excludes canceled."),
 ("Why would attempt_count be zero on a past-due invoice?",
  "Because no charge was ever attempted, which almost always means no payment method resolved for the subscription. Smart Retries do not run when there is nothing to charge, so the subscription is stuck without ever having been declined."),
 ("How do I decide which past-due subscriptions to cancel?",
  "By the age of the latest invoice. Inside a retry window there is a real chance of recovery and cancelling early throws away revenue. Past it, nothing more will happen automatically, and the only thing keeping the subscription open is that nobody closed it."),
],
"related": [
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge"),
 ("/stripe/trial-ends-without-payment-method/", "Trials ending with no card on file"),
 ("/woocommerce/dunning-stops-before-its-attempts/", "Dunning stops before its attempts"),
],
"citations": [CITE_SUB_OBJ, CITE_SUB_OVERVIEW, CITE_RETRIES, CITE_COLLECTION],
},

{
"slug": "trial-ends-without-payment-method",
"title": "Trials ending in days with no card on file",
"description": "A cohort of trialing subscriptions has no payment method. On the trial end date they all fail at once, and the default behaviour is silent dunning.",
"h1": "trials ending in days with no card on file",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe trial no payment method",
             "trial_settings end_behavior missing_payment_method",
             "stripe trial_will_end", "stripe trial ends past_due",
             "stripe paused subscription trial"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Card-free trials are good for signups and they build a queue. Everyone who started a trial on the first of the month reaches its end on the same day, and the ones without a card all fail together. What happens next is one Stripe setting most teams have never opened, and its default is the loudest of the three options and the quietest to you.",
"short_answer": """<p>Read <code>GET /v1/subscriptions?status=trialing&amp;limit=100&amp;expand[]=data.customer</code>. Flag rows where <code>trial_end</code> falls inside the next 72 hours and <code>default_payment_method</code>, <code>default_source</code> and <code>customer.invoice_settings.default_payment_method</code> are all null.</p>
<p>Then read <code>trial_settings.end_behavior.missing_payment_method</code> on those rows. It decides whether they land in <code>past_due</code>, in <code>paused</code>, or gone, and it defaults to <code>create_invoice</code>, which is the first of those.</p>""",
"problem": """<p>When a trial ends and no payment method resolves, Stripe consults one field: <code>trial_settings.end_behavior.missing_payment_method</code>. It has three values and they produce three completely different outcomes.</p>
<p><code>create_invoice</code>, the default, cuts an invoice that fails immediately because there is nothing to charge. The subscription drops into <code>past_due</code> and joins whatever pile you already have there, with access probably still granted. <code>pause</code> moves the subscription to <code>paused</code> and stops invoicing, which is recoverable but earns nothing and generates no dunning email. <code>cancel</code> ends it outright.</p>
<p>The reason this is worth a scheduled check rather than a one-off decision is the shape of the failure. It is not one subscription going wrong, it is a cohort. Trials started in a marketing push all end within a day or two of each other, so a setting you never chose produces a spike of broken subscriptions on a date you could have predicted a week in advance.</p>""",
"why": """<p><strong>The default was never chosen.</strong> <code>create_invoice</code> is what you get by not setting the field. It is a reasonable default for trials that required a card up front and a poor one for trials that did not, and nothing in the API distinguishes the two.</p>
<p><strong>The trial itself never asked for a card.</strong> That is usually deliberate &mdash; it is why the signup converts &mdash; but it means the subscription exists for the whole trial with all its payment-method slots empty and no code path that fills them.</p>
<p><strong>Nobody handles <code>customer.subscription.trial_will_end</code>.</strong> Stripe fires it three days before the trial end date, precisely so you can email the customer a link to add a card. An integration that does not subscribe to it has no notice at all; the first signal is the failure itself.</p>
<p><strong>The three outcomes fail differently, and two of them fail quietly.</strong> A <code>past_due</code> subscription at least shows up in a dunning report. A <code>paused</code> one shows up nowhere: it is not active, not past due, not canceled, and it will sit there until someone goes looking.</p>""",
"steps": [
 {"h": "List trialing subscriptions with the customer expanded",
  "body": """<p>The customer-level default is the third place Stripe looks, so without <code>expand[]=data.customer</code> you will flag customers who do have a card on file at the account level.</p>"""},
 {"h": "Filter to the next 72 hours",
  "body": """<p>A trial ending in three weeks is not a problem yet and putting it in the same list as one ending tomorrow makes the list unactionable. Seventy-two hours also lines up with <code>customer.subscription.trial_will_end</code>, which fires three days out.</p>"""},
 {"h": "Read the end behaviour on every flagged row",
  "body": """<p>This is what turns a count into a prediction. The same twelve card-free trials become twelve <code>past_due</code> subscriptions, twelve <code>paused</code> ones, or twelve cancellations depending on one field, and the script should tell you which before the date rather than after.</p>"""},
 {"h": "Send the customers a billing-portal link",
  "body": """<p>The only real repair is a card, and only the customer can supply one. A portal link or a SetupIntent, sent while the trial is still running, converts a subscription that would otherwise fail.</p>"""},
 {"h": "Set the end behaviour deliberately",
  "body": """<p>For card-free trials, <code>pause</code> is usually the honest choice: it stops billing, it is reversible, and it does not manufacture invoices that can never be paid. Whatever you pick, pick it, and subscribe to <code>customer.subscription.trial_will_end</code> so the next cohort gets warned.</p>"""},
],
"verify": """<p>Re-run the script a few days before your next big trial cohort ends. Nothing should be listed as ending soon without a card.</p>
<pre><code class="language-bash">python3 stripe_trial_no_card.py
# 88 trialing, 0 ending within 72h with no card, 4 with no card further out</code></pre>""",
"code_intro": "One GET request per page and no writes: a restricted key with read access to Subscriptions and Customers is enough. The classifier takes the current time as an argument rather than reading the clock itself, which is what lets the tests pin the 72-hour boundary exactly instead of approximately.",
"py_file": "stripe_trial_no_card.py",
"py": '''"""Report Stripe trials ending soon with no payment method on file.

Read only. GET requests only, no writes: give this a RESTRICTED key with read
access to Subscriptions and Customers. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_trial_no_card")

API = "https://api.stripe.com/v1"

# Stripe fires customer.subscription.trial_will_end three days out, so this is the
# window in which a warning email is still the documented remedy.
HORIZON = 259200

OUTCOMES = {
    "create_invoice": "Stripe invoices on the trial end date, the invoice fails "
                      "immediately, and the subscription drops into past_due",
    "pause": "the subscription moves to paused and stops invoicing, which is "
             "recoverable but earns nothing until someone resumes it",
    "cancel": "the subscription is cancelled outright on the trial end date",
}


def verdict(sub, now, horizon=HORIZON):
    """Classify one trialing subscription. Pure, so the horizon can be tested.

    Checks the three payment-method slots that apply to a trial ending, then reads
    trial_settings.end_behavior.missing_payment_method to say what will happen.
    """
    if sub.get("default_payment_method") or sub.get("default_source"):
        return ("carded", "a payment method resolves, so the trial will convert")
    customer = sub.get("customer")
    if not isinstance(customer, dict):
        return ("unknown",
                "customer was not expanded, so the customer-level default cannot be "
                "read; re-run with expand[]=data.customer")
    settings = customer.get("invoice_settings") or {}
    if settings.get("default_payment_method"):
        return ("carded",
                "falls back to customer.invoice_settings.default_payment_method")

    behaviour = (((sub.get("trial_settings") or {}).get("end_behavior") or {})
                 .get("missing_payment_method") or "create_invoice")
    outcome = OUTCOMES.get(
        behaviour, "end behaviour %r is not one Stripe documents" % (behaviour,))

    trial_end = sub.get("trial_end")
    if not isinstance(trial_end, (int, float)):
        return ("no-card", "no payment method and no trial_end to schedule against")
    remaining = trial_end - now
    if remaining <= horizon:
        return ("imminent",
                "no payment method, trial ends in %.0f h: %s"
                % (remaining / 3600.0, outcome))
    return ("no-card",
            "no payment method, trial ends in %.0f day(s): %s"
            % (remaining / 86400.0, outcome))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_trialing(session, limit):
    """Walk the trialing subscriptions. Read only; every call here is a GET."""
    out = []
    params = {"status": "trialing", "limit": 100, "expand[]": "data.customer"}
    while True:
        page = get(session, "/subscriptions", **params)
        out.extend(page.get("data", []))
        if not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = page["data"][-1]["id"]
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=int, default=72,
                    help="how far ahead counts as imminent (default 72)")
    ap.add_argument("--max", type=int, default=1000,
                    help="stop after this many subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    subs = page_trialing(s, args.max)
    if not subs:
        log.info("no trialing subscriptions for this key's mode")
        return 0

    now = time.time()
    counts = {}
    for sub in subs:
        state, detail = verdict(sub, now, args.hours * 3600)
        counts[state] = counts.get(state, 0) + 1
        if state == "carded":
            continue
        line = "%-9s %s  %s" % (state, sub.get("id", "?"), detail)
        if state == "no-card":
            log.info(line)
            continue
        log.warning(line)
        customer = sub.get("customer")
        cus_id = customer.get("id") if isinstance(customer, dict) else customer
        log.warning("  repair: email %s a billing-portal link and collect a card "
                    "before %s", cus_id or "the customer", sub.get("trial_end"))
        log.warning("  and choose the end behaviour deliberately: POST "
                    "%s/subscriptions/%s -d "
                    "trial_settings[end_behavior][missing_payment_method]=pause",
                    API, sub.get("id"))

    log.info("%d trialing, %d ending within %dh with no card, %d with no card "
             "further out", len(subs), counts.get("imminent", 0), args.hours,
             counts.get("no-card", 0))
    if counts.get("unknown"):
        log.warning("%d row(s) could not be classified: re-run with the customer "
                    "expanded", counts["unknown"])
    if counts.get("imminent"):
        log.warning("subscribe to customer.subscription.trial_will_end; it fires "
                    "three days out, which is the window this check reports on")
    return 1 if counts.get("imminent") or counts.get("unknown") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-trial-no-card.mjs",
"js": '''/**
 * Report Stripe trials ending soon with no payment method on file.
 *
 * Read only. GET requests only, no writes: give this a RESTRICTED key with read
 * access to Subscriptions and Customers. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Stripe fires customer.subscription.trial_will_end three days out, so this is the
// window in which a warning email is still the documented remedy.
export const HORIZON = 259200;

const OUTCOMES = {
  create_invoice: 'Stripe invoices on the trial end date, the invoice fails ' +
    'immediately, and the subscription drops into past_due',
  pause: 'the subscription moves to paused and stops invoicing, which is ' +
    'recoverable but earns nothing until someone resumes it',
  cancel: 'the subscription is cancelled outright on the trial end date',
};

/**
 * Classify one trialing subscription. Pure, so the horizon can be tested.
 */
export function verdict(sub, now, horizon = HORIZON) {
  if (sub.default_payment_method || sub.default_source) {
    return ['carded', 'a payment method resolves, so the trial will convert'];
  }
  const customer = sub.customer;
  if (customer === null || typeof customer !== 'object') {
    return ['unknown',
      'customer was not expanded, so the customer-level default cannot be read; ' +
      're-run with expand[]=data.customer'];
  }
  const settings = customer.invoice_settings ?? {};
  if (settings.default_payment_method) {
    return ['carded', 'falls back to customer.invoice_settings.default_payment_method'];
  }

  const behaviour = sub.trial_settings?.end_behavior?.missing_payment_method
    ?? 'create_invoice';
  const outcome = OUTCOMES[behaviour]
    ?? `end behaviour ${JSON.stringify(behaviour)} is not one Stripe documents`;

  const trialEnd = sub.trial_end;
  if (typeof trialEnd !== 'number') {
    return ['no-card', 'no payment method and no trial_end to schedule against'];
  }
  const remaining = trialEnd - now;
  if (remaining <= horizon) {
    return ['imminent',
      `no payment method, trial ends in ${(remaining / 3600).toFixed(0)} h: ${outcome}`];
  }
  return ['no-card',
    `no payment method, trial ends in ${(remaining / 86400).toFixed(0)} day(s): ${outcome}`];
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

async function pageTrialing(key, limit) {
  const out = [];
  const q = { status: 'trialing', limit: 100, 'expand[]': 'data.customer' };
  for (;;) {
    const page = await get(key, '/subscriptions', q);
    out.push(...(page.data ?? []));
    if (!page.has_more || out.length >= limit) break;
    q.starting_after = page.data[page.data.length - 1].id;
  }
  return out.slice(0, limit);
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const subs = await pageTrialing(key, 1000);
  if (subs.length === 0) {
    console.log("no trialing subscriptions for this key's mode");
    return;
  }

  const now = Date.now() / 1000;
  const counts = new Map();
  for (const sub of subs) {
    const [state, detail] = verdict(sub, now);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'carded') continue;
    const line = `${state.padEnd(9)} ${sub.id ?? '?'}  ${detail}`;
    if (state === 'no-card') { console.log(line); continue; }
    console.warn(line);
    const cus = typeof sub.customer === 'object' && sub.customer !== null
      ? sub.customer.id : sub.customer;
    console.warn(`  repair: email ${cus ?? 'the customer'} a billing-portal link ` +
      `and collect a card before ${sub.trial_end}`);
    console.warn(`  and choose the end behaviour deliberately: ` +
      `POST ${API}/subscriptions/${sub.id} ` +
      `-d trial_settings[end_behavior][missing_payment_method]=pause`);
  }

  console.log(`${subs.length} trialing, ${counts.get('imminent') ?? 0} ending ` +
    `within 72h with no card, ${counts.get('no-card') ?? 0} with no card further out`);
  if (counts.get('unknown')) {
    console.warn(`${counts.get('unknown')} row(s) could not be classified: re-run ` +
      'with the customer expanded');
  }
  if (counts.get('imminent')) {
    console.warn('subscribe to customer.subscription.trial_will_end; it fires three ' +
      'days out, which is the window this check reports on');
  }
  process.exitCode = (counts.get('imminent') ?? 0) + (counts.get('unknown') ?? 0)
    ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth holding still here. The first is that an absent <code>trial_settings</code> has to be read as <code>create_invoice</code>, because that is Stripe's default and treating it as unknown would hide the most common case. The second is the horizon: a trial ending in three weeks and one ending tomorrow are different findings and must not share a bucket.",
"test_py_file": "test_stripe_trial_no_card.py",
"test_py": '''from stripe_trial_no_card import verdict

NOW = 1_800_000_000
HOUR = 3600


def trial(hours_out, behaviour=None, customer=None):
    sub = {"trial_end": NOW + hours_out * HOUR,
           "customer": {} if customer is None else customer}
    if behaviour:
        sub["trial_settings"] = {"end_behavior": {"missing_payment_method": behaviour}}
    return sub


def test_a_card_on_the_subscription_is_not_a_finding():
    sub = {"default_payment_method": "pm_1", "customer": {}}
    assert verdict(sub, NOW)[0] == "carded"


def test_a_card_on_the_customer_counts_too():
    sub = trial(24, customer={"invoice_settings": {"default_payment_method": "pm_2"}})
    assert verdict(sub, NOW)[0] == "carded"


def test_missing_trial_settings_is_read_as_the_stripe_default():
    # create_invoice is what you get by not setting the field, and it is the case
    # that produces past_due, so it must not be reported as unknown.
    state, detail = verdict(trial(12), NOW)
    assert state == "imminent"
    assert "past_due" in detail


def test_pause_is_named_as_a_different_outcome():
    state, detail = verdict(trial(12, "pause"), NOW)
    assert state == "imminent"
    assert "paused" in detail


def test_a_trial_ending_in_three_weeks_is_not_imminent():
    state, detail = verdict(trial(24 * 21), NOW)
    assert state == "no-card"
    assert "day(s)" in detail


def test_unexpanded_customer_is_not_silently_carded():
    state, detail = verdict({"trial_end": NOW + HOUR, "customer": "cus_9"}, NOW)
    assert state == "unknown"
    assert "expand" in detail
''',
"test_js_file": "stripe-trial-no-card.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-trial-no-card.mjs';

const NOW = 1_800_000_000;
const HOUR = 3600;

function trial(hoursOut, behaviour, customer) {
  const sub = { trial_end: NOW + hoursOut * HOUR, customer: customer ?? {} };
  if (behaviour) {
    sub.trial_settings = { end_behavior: { missing_payment_method: behaviour } };
  }
  return sub;
}

test('a card on the subscription is not a finding', () => {
  assert.equal(verdict({ default_payment_method: 'pm_1', customer: {} }, NOW)[0],
    'carded');
});

test('a card on the customer counts too', () => {
  const sub = trial(24, null,
    { invoice_settings: { default_payment_method: 'pm_2' } });
  assert.equal(verdict(sub, NOW)[0], 'carded');
});

test('missing trial settings is read as the stripe default', () => {
  const [state, detail] = verdict(trial(12), NOW);
  assert.equal(state, 'imminent');
  assert.match(detail, /past_due/);
});

test('pause is named as a different outcome', () => {
  const [state, detail] = verdict(trial(12, 'pause'), NOW);
  assert.equal(state, 'imminent');
  assert.match(detail, /paused/);
});

test('a trial ending in three weeks is not imminent', () => {
  const [state, detail] = verdict(trial(24 * 21), NOW);
  assert.equal(state, 'no-card');
  assert.match(detail, /day\\(s\\)/);
});

test('unexpanded customer is not silently carded', () => {
  const [state, detail] = verdict({ trial_end: NOW + HOUR, customer: 'cus_9' }, NOW);
  assert.equal(state, 'unknown');
  assert.match(detail, /expand/);
});
''',
"faq": [
 ("What happens by default when a trial ends with no card?",
  "trial_settings.end_behavior.missing_payment_method defaults to create_invoice. Stripe cuts an invoice on the trial end date, it fails immediately because there is nothing to charge, and the subscription becomes past_due."),
 ("Which end behaviour should I choose for card-free trials?",
  "pause is usually the honest one. It stops invoicing, puts the subscription in paused, and is reversible once a card is attached. It does not manufacture invoices that can never be paid, and it does not delete a customer relationship the way cancel does."),
 ("How much warning does Stripe give me?",
  "customer.subscription.trial_will_end fires three days before the trial end date. That is the whole notice period, which is why this check uses a 72-hour horizon: anything it reports is something the webhook should also have told you about."),
 ("Why does a paused subscription never come back on its own?",
  "There is no timeout on paused. Stripe stops creating invoices and waits. The subscription resumes only when you explicitly resume it after a default payment method exists, so paused subscriptions accumulate quietly unless something is watching for them."),
 ("Can I check this without a live secret key?",
  "Yes. A restricted key with read access to Subscriptions and Customers covers the whole check, and if it leaks nobody can move money with it."),
],
"related": [
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access"),
 ("/woocommerce/free-trials-forced-to-manual-renewal/", "Free trials forced to manual renewal"),
],
"citations": [CITE_TRIALS, CITE_SUB_OBJ, CITE_COLLECTION, CITE_RETRIES],
},

]
