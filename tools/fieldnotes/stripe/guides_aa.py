#!/usr/bin/env python3
"""/stripe/ field notes — batch AA: expiry, risk review, and unconfirmed signups.

Four problems that all show up as a number in somebody else's report before they
show up as an error in yours: a refund Stripe wrote itself, a risk score nobody
acted on, a pile of expired signups, and a bank challenge that was never shown.
Every script here is read only. They hold a credential to a live payments
account, so none of them writes: they read, they say exactly what is wrong, and
they print the repair for a human to run.
"""

CHIPS = ["Read-only key", "Python and Node.js", "Tests included"]

CITE_REFUND_OBJECT = ("The Refund object — Stripe API reference",
                      "https://docs.stripe.com/api/refunds/object")
CITE_REFUNDS = ("Refunds — Stripe Docs", "https://docs.stripe.com/refunds")
CITE_HOLD = ("Place a hold on a payment method — Stripe Docs",
             "https://docs.stripe.com/payments/place-a-hold-on-a-payment-method")
CITE_CHARGE_OBJECT = ("The Charge object — Stripe API reference",
                      "https://docs.stripe.com/api/charges/object")
CITE_RADAR_RULES = ("Radar rules — Stripe Docs", "https://docs.stripe.com/radar/rules")
CITE_RADAR_REVIEWS = ("Reviewing payments — Stripe Docs",
                      "https://docs.stripe.com/radar/reviews")
CITE_DECLINES = ("Declines — Stripe Docs", "https://docs.stripe.com/declines")
CITE_SUB_OBJECT = ("The Subscription object — Stripe API reference",
                   "https://docs.stripe.com/api/subscriptions/object")
CITE_SUB_CREATE = ("Create a subscription — Stripe API reference",
                   "https://docs.stripe.com/api/subscriptions/create")
CITE_SUB_OVERVIEW = ("How subscriptions work — Stripe Docs",
                     "https://docs.stripe.com/billing/subscriptions/overview")
CITE_3DS = ("3D Secure authentication — Stripe Docs",
            "https://docs.stripe.com/payments/3d-secure")
CITE_SMART_RETRIES = ("Smart Retries — Stripe Docs",
                      "https://docs.stripe.com/billing/revenue-recovery/smart-retries")
CITE_INVOICE_WORKFLOW = ("Invoice workflow transitions — Stripe Docs",
                         "https://docs.stripe.com/invoicing/integration/workflow-transitions")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

GUIDES = [

{
"slug": "uncaptured-charge-expiry-refunds",
"title": "Refunds nobody issued with reason expired_uncaptured_charge",
"description": "Stripe writes a Refund of its own when an authorization expires. It lands in the refund rate and turns a capture bug into a customer complaint.",
"h1": "refunds nobody issued with reason expired_uncaptured_charge",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["expired_uncaptured_charge", "stripe refund reason expired",
             "stripe refund rate inflated", "stripe automatic refund not issued",
             "stripe uncaptured charge refund"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody in the monthly review asks why the refund rate went from 1.2% to 3.1%. Support has no extra tickets. Nobody remembers approving a wave of refunds, and the finance export shows money going back out that never came in. Every one of those refunds was written by Stripe, and no customer asked for a single one.",
"short_answer": """<p>Paginate <code>GET /v1/refunds?limit=100&amp;created[gte]=&lt;90 days ago&gt;</code> and group the results by <code>reason</code>. The value <code>expired_uncaptured_charge</code> is set by Stripe itself when an authorization runs out of time before anyone captures it. It is the only reason on the Refund object that no human in your business can choose.</p>
<p>Weight the groups by <code>amount</code>, not by count, and express the expired total as a share of everything refunded in the window. Then confirm each one against its charge: <code>GET /v1/charges/{id}</code> should report <code>captured: false</code>, which is the proof that no money was ever collected to give back.</p>""",
"problem": """<p>Refund rate is a metric that leaves engineering. It goes into board decks, into support QA, into the conversation about whether the product is disappointing people. These refunds are not that. They are an integration failure filed in a customer-satisfaction column, and the two get argued about for months because the numbers are real and the explanation is nowhere near them.</p>
<p>The object itself gives nothing away. It has an <code>amount</code>, a <code>currency</code>, a <code>charge</code>, a <code>status</code> of <code>succeeded</code>, and it appears in the Dashboard's refund list next to the ones your support team issued this morning. Any report built on <code>GET /v1/refunds</code> without grouping by <code>reason</code> counts it, and almost no report groups by <code>reason</code>.</p>
<p>The other half of the damage is the reconciliation side. A refund normally has a settled payment behind it. These do not, because the authorization was released rather than captured, so the ledger shows a return with no matching receipt and somebody spends a day trying to find the missing money.</p>""",
"why": """<p><strong>Stripe writes the refund, not you.</strong> When an uncaptured authorization reaches the end of its window, Stripe records the release as a Refund and stamps it <code>reason: "expired_uncaptured_charge"</code>. No API call of yours created it, so there is no code path to search for and no log line on your side that mentions it.</p>
<p><strong>The reason field is the only thing separating it from a real refund.</strong> Status, amount, currency, charge id and creation time all look exactly like a refund a person issued. If your reporting selects on status and sums amounts, which is the obvious way to write it, the two populations are already merged before anyone can tell them apart.</p>
<p><strong>It is a lagging indicator of a different bug.</strong> The refund appears at the end of the authorization window, days after the capture that never happened. By the time it lands, the deploy or the queue backlog that caused it is old news, so the spike in refunds and the cause sit too far apart in time to be connected by eye.</p>
<p><strong>The charge is where the proof lives.</strong> <code>captured: false</code> on the underlying charge is what turns "we think these are automatic" into a fact you can put in a ticket. It is one extra lookup per candidate and it is the difference between an argument and a finding.</p>
<p><strong>Nothing alerts on it.</strong> The refund is not a failure, so no error event is emitted for it. There is a <code>charge.refund.updated</code> event you can subscribe to, but nobody subscribes to refund events looking for good news, which is what this superficially is.</p>""",
"steps": [
 {"h": "Page the refunds, not the charges",
  "body": """<p>Start from <code>GET /v1/refunds</code> over a 90-day window. Starting from charges means scanning far more objects to find the same set, and the reason code you actually want to count only exists on the refund.</p>"""},
 {"h": "Group by reason and weight by amount",
  "body": """<p>Counts understate this badly. Expired authorizations skew toward the larger, slower orders &mdash; the made-to-order and rental flows that chose manual capture in the first place &mdash; so five of them can outweigh two hundred small customer refunds. Report money, then count.</p>"""},
 {"h": "Confirm each candidate against its charge",
  "body": """<p>Fetch <code>GET /v1/charges/{id}</code> for the <code>charge</code> on each expired refund and check <code>captured</code>. A <code>false</code> confirms the story. A <code>true</code> means something else produced that reason value and you should look at the charge before counting it, rather than assuming the label.</p>"""},
 {"h": "Express the result as a share of refunded value",
  "body": """<p>"Nine refunds" persuades nobody. "31% of everything we refunded last quarter was authorizations we let expire, and no customer asked for any of it" ends the conversation about product dissatisfaction in one line.</p>"""},
 {"h": "Split the metric, then go and fix the capture pipeline",
  "body": """<p>Exclude <code>expired_uncaptured_charge</code> from the customer-facing refund rate and give it its own operational number. That stops the misattribution but it does not stop the loss &mdash; for the forward-looking half, the deadline you are missing is on the charge as <code>capture_before</code>, which is <a href="/stripe/expired-manual-capture-holds/">a check of its own</a>.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the capture pipeline was fixed. The expired share should fall to zero, and the refund rate you report should drop to whatever your customers were actually asking for all along.</p>
<pre><code class="language-bash">python3 stripe_expired_capture_refunds.py --days 90 --verify-charges
# 412 refund(s) in 90 day(s): 0 expired uncaptured, 0.0% of refunded value</code></pre>""",
"code_intro": "One paginated GET over Refunds, plus one small lookup per candidate charge when you ask for it, and no writes &mdash; a restricted key with read access to Refunds and Charges is enough. The classifier is pure and takes the charge as a separate argument, because the case that matters most is the one where the charge was not fetched: an unverified expired refund is not the same finding as a confirmed one, and quietly treating it as such is how a report gets contradicted in the meeting it was written for.",
"py_file": "stripe_expired_capture_refunds.py",
"py": '''"""Report Stripe refunds that Stripe wrote itself when an authorization expired.

Read only. A paginated GET over Refunds and one lookup per candidate charge, no
writes: give this a RESTRICTED key with read access to Refunds and Charges. The
repair is printed, never performed, because this script holds a credential to a
live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_expired_capture_refunds")

API = "https://api.stripe.com/v1"

# Set by Stripe when an uncaptured authorization runs out of time. It is the one
# reason value on the Refund object that nobody in your business can choose, and
# so the one that should never be counted in a customer-facing refund rate.
EXPIRED = "expired_uncaptured_charge"

# The reasons a person picks. Everything here is a real refund.
CUSTOMER_REASONS = ("requested_by_customer", "duplicate", "fraudulent")


def classify(refund, charge=None):
    """Sort one Refund into money a human gave back and money that fell off a card.

    Pure, so the whole rule set is readable here and testable without a network.

    `charge` is the Charge this refund belongs to, or None when it was not looked
    up. That distinction is deliberate: an expired refund confirmed against
    `captured == false` is evidence, and an unconfirmed one is a candidate, and
    collapsing the two is how a finding gets contradicted later.

    Returns (state, detail).
    """
    reason = refund.get("reason")

    if reason == EXPIRED:
        if charge is None:
            return ("expired-unverified",
                    "Stripe wrote this when the authorization expired, but the "
                    "charge was not fetched, so captured is unconfirmed")
        captured = charge.get("captured")
        if captured is False:
            return ("expired",
                    "the authorization expired uncaptured: nobody issued this "
                    "refund and no customer asked for it")
        return ("inconsistent",
                "reason says the authorization expired but the charge reports "
                "captured=%r: read the charge before counting this one" % (captured,))

    if reason in CUSTOMER_REASONS:
        return ("customer", "a real refund (%s), belongs in the refund rate" % reason)

    if reason is None:
        return ("unlabelled",
                "no reason recorded: issued through the API or the Dashboard "
                "without one, so it counts as a real refund until proven otherwise")

    return ("other", "unrecognised reason %r, left in the rate" % (reason,))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_refunds(session, since, limit):
    """Yield refunds created since a unix timestamp, newest first."""
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/refunds", **params)
        rows = page.get("data", [])
        for refund in rows:
            yield refund
            seen += 1
        if not page.get("has_more") or not rows or seen >= limit:
            break
        params["starting_after"] = rows[-1]["id"]


def add(bucket, currency, amount):
    bucket[currency] = bucket.get(currency, 0) + (amount or 0)


def money(bucket):
    if not bucket:
        return "nothing"
    return ", ".join("%.2f %s" % (v / 100.0, k.upper()) for k, v in sorted(bucket.items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to scan refunds (default 90)")
    ap.add_argument("--max-refunds", type=int, default=2000,
                    help="stop paginating after this many refunds")
    ap.add_argument("--verify-charges", action="store_true",
                    help="fetch each candidate charge to confirm captured is false")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    charges = {}

    states = {}
    all_money = {}
    expired_money = {}
    scanned = 0

    for refund in page_refunds(s, since, args.max_refunds):
        scanned += 1
        currency = refund.get("currency") or "???"
        add(all_money, currency, refund.get("amount"))

        charge = None
        if args.verify_charges and refund.get("reason") == EXPIRED:
            charge_id = refund.get("charge")
            if isinstance(charge_id, str):
                if charge_id not in charges:
                    charges[charge_id] = get(s, "/charges/" + charge_id)
                charge = charges[charge_id]

        state, detail = classify(refund, charge)
        states[state] = states.get(state, 0) + 1

        if state in ("expired", "expired-unverified"):
            add(expired_money, currency, refund.get("amount"))
            log.warning("%-18s %s  %s", state, refund.get("id", "?"), detail)
        elif state == "inconsistent":
            log.warning("%-18s %s  %s", state, refund.get("id", "?"), detail)

    if not scanned:
        log.info("no refunds in the last %d day(s)", args.days)
        return 0

    log.info("%d refund(s) in %d day(s): %s", scanned, args.days,
             ", ".join("%d %s" % (n, k) for k, n in sorted(states.items())))
    log.info("refunded in total: %s", money(all_money))

    if not expired_money:
        log.info("nothing refunded because an authorization expired")
        return 0

    log.warning("refunded because an authorization expired: %s", money(expired_money))
    for currency, amount in sorted(expired_money.items()):
        total = all_money.get(currency, 0)
        if total:
            log.warning("  %s: %.1f%% of everything refunded in this window",
                        currency.upper(), 100.0 * amount / total)
    log.warning("repair: exclude reason=%s from the customer-facing refund rate "
                "and report it as an operational number instead", EXPIRED)
    log.warning("repair: fix the capture pipeline; the real deadline is "
                "capture_before on the charge, not created plus seven days")
    log.warning("repair: subscribe to charge.refund.updated and alert when a "
                "refund arrives carrying this reason")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-expired-capture-refunds.mjs",
"js": '''/**
 * Report Stripe refunds that Stripe wrote itself when an authorization expired.
 *
 * Read only. A paginated GET over Refunds and one lookup per candidate charge,
 * no writes: give this a RESTRICTED key with read access to Refunds and Charges.
 * The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Set by Stripe when an uncaptured authorization runs out of time. The one
// reason value on the Refund object nobody in your business can choose.
export const EXPIRED = 'expired_uncaptured_charge';

const CUSTOMER_REASONS = ['requested_by_customer', 'duplicate', 'fraudulent'];

/**
 * Sort one Refund into money a human gave back and money that fell off a card.
 * Pure. `charge` is the Charge it belongs to, or null when it was not fetched.
 */
export function classify(refund, charge = null) {
  const reason = refund.reason ?? null;

  if (reason === EXPIRED) {
    if (charge === null || charge === undefined) {
      return ['expired-unverified',
        'Stripe wrote this when the authorization expired, but the charge was ' +
        'not fetched, so captured is unconfirmed'];
    }
    if (charge.captured === false) {
      return ['expired',
        'the authorization expired uncaptured: nobody issued this refund and ' +
        'no customer asked for it'];
    }
    return ['inconsistent',
      `reason says the authorization expired but the charge reports ` +
      `captured=${JSON.stringify(charge.captured)}: read the charge before ` +
      'counting this one'];
  }

  if (CUSTOMER_REASONS.includes(reason)) {
    return ['customer', `a real refund (${reason}), belongs in the refund rate`];
  }

  if (reason === null) {
    return ['unlabelled',
      'no reason recorded: issued through the API or the Dashboard without one, ' +
      'so it counts as a real refund until proven otherwise'];
  }

  return ['other', `unrecognised reason ${JSON.stringify(reason)}, left in the rate`];
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

async function* pageRefunds(key, since, limit) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/refunds', params);
    const rows = page.data ?? [];
    for (const refund of rows) { yield refund; seen += 1; }
    if (!page.has_more || rows.length === 0 || seen >= limit) break;
    params.starting_after = rows[rows.length - 1].id;
  }
}

function add(bucket, currency, amount) {
  bucket.set(currency, (bucket.get(currency) ?? 0) + (amount ?? 0));
}

function money(bucket) {
  if (bucket.size === 0) return 'nothing';
  return [...bucket.entries()].sort()
    .map(([k, v]) => `${(v / 100).toFixed(2)} ${k.toUpperCase()}`).join(', ');
}

async function main() {
  const days = Number(process.argv[2] ?? 90);
  const verify = process.argv.includes('--verify-charges');

  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const since = Math.floor(Date.now() / 1000) - days * 86400;
  const charges = new Map();
  const states = new Map();
  const allMoney = new Map();
  const expiredMoney = new Map();
  let scanned = 0;

  for await (const refund of pageRefunds(key, since, 2000)) {
    scanned += 1;
    const currency = refund.currency ?? '???';
    add(allMoney, currency, refund.amount);

    let charge = null;
    if (verify && refund.reason === EXPIRED && typeof refund.charge === 'string') {
      if (!charges.has(refund.charge)) {
        charges.set(refund.charge, await get(key, `/charges/${refund.charge}`));
      }
      charge = charges.get(refund.charge);
    }

    const [state, detail] = classify(refund, charge);
    states.set(state, (states.get(state) ?? 0) + 1);

    if (state === 'expired' || state === 'expired-unverified') {
      add(expiredMoney, currency, refund.amount);
      console.warn(`${state.padEnd(18)} ${refund.id ?? '?'}  ${detail}`);
    } else if (state === 'inconsistent') {
      console.warn(`${state.padEnd(18)} ${refund.id ?? '?'}  ${detail}`);
    }
  }

  if (scanned === 0) {
    console.log(`no refunds in the last ${days} day(s)`);
    return;
  }

  const summary = [...states.entries()].sort().map(([k, n]) => `${n} ${k}`).join(', ');
  console.log(`${scanned} refund(s) in ${days} day(s): ${summary}`);
  console.log(`refunded in total: ${money(allMoney)}`);

  if (expiredMoney.size === 0) {
    console.log('nothing refunded because an authorization expired');
    return;
  }

  console.warn(`refunded because an authorization expired: ${money(expiredMoney)}`);
  for (const [currency, amount] of [...expiredMoney.entries()].sort()) {
    const total = allMoney.get(currency) ?? 0;
    if (total) {
      console.warn(`  ${currency.toUpperCase()}: ` +
        `${((100 * amount) / total).toFixed(1)}% of everything refunded in this window`);
    }
  }
  console.warn(`repair: exclude reason=${EXPIRED} from the customer-facing refund ` +
               'rate and report it as an operational number instead');
  console.warn('repair: fix the capture pipeline; the real deadline is ' +
               'capture_before on the charge, not created plus seven days');
  console.warn('repair: subscribe to charge.refund.updated and alert when a ' +
               'refund arrives carrying this reason');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main(), fail on the missing key, and set a non-zero exit code
// that fails the whole test run even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning is the expired refund whose charge was never fetched. It is almost certainly automatic and it is not yet proven, and a classifier that reports it as confirmed is the one that gets a finding thrown out when somebody opens the charge and sees something else. The inconsistent case is pinned for the same reason from the other direction.",
"test_py_file": "test_stripe_expired_capture_refunds.py",
"test_py": '''from stripe_expired_capture_refunds import classify


def refund(reason="requested_by_customer"):
    out = {"id": "re_1", "amount": 4900, "currency": "usd", "charge": "ch_1"}
    if reason is not None:
        out["reason"] = reason
    return out


def test_expired_reason_with_an_uncaptured_charge_is_confirmed():
    state, detail = classify(refund("expired_uncaptured_charge"), {"captured": False})
    assert state == "expired"
    assert "no customer asked" in detail


def test_expired_reason_without_the_charge_is_only_a_candidate():
    # The whole point: unverified is not the same finding as verified.
    state, detail = classify(refund("expired_uncaptured_charge"))
    assert state == "expired-unverified"
    assert "unconfirmed" in detail


def test_expired_reason_on_a_captured_charge_is_flagged_not_counted():
    state, detail = classify(refund("expired_uncaptured_charge"), {"captured": True})
    assert state == "inconsistent"
    assert "captured=True" in detail


def test_a_customer_refund_stays_in_the_rate():
    state, detail = classify(refund("requested_by_customer"), {"captured": True})
    assert state == "customer"
    assert "refund rate" in detail


def test_a_refund_with_no_reason_is_not_treated_as_expired():
    assert classify(refund(None))[0] == "unlabelled"
''',
"test_js_file": "stripe-expired-capture-refunds.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-expired-capture-refunds.mjs';

function refund(reason = 'requested_by_customer') {
  const out = { id: 're_1', amount: 4900, currency: 'usd', charge: 'ch_1' };
  if (reason !== null) out.reason = reason;
  return out;
}

test('expired reason with an uncaptured charge is confirmed', () => {
  const [state, detail] = classify(refund('expired_uncaptured_charge'), { captured: false });
  assert.equal(state, 'expired');
  assert.match(detail, /no customer asked/);
});

test('expired reason without the charge is only a candidate', () => {
  const [state, detail] = classify(refund('expired_uncaptured_charge'));
  assert.equal(state, 'expired-unverified');
  assert.match(detail, /unconfirmed/);
});

test('expired reason on a captured charge is flagged, not counted', () => {
  const [state, detail] = classify(refund('expired_uncaptured_charge'), { captured: true });
  assert.equal(state, 'inconsistent');
  assert.match(detail, /captured=true/);
});

test('a customer refund stays in the rate', () => {
  const [state, detail] = classify(refund('requested_by_customer'), { captured: true });
  assert.equal(state, 'customer');
  assert.match(detail, /refund rate/);
});

test('a refund with no reason is not treated as expired', () => {
  assert.equal(classify(refund(null))[0], 'unlabelled');
});
''',
"faq": [
 ("What does expired_uncaptured_charge actually mean?",
  "That a payment was authorized but never captured, and the authorization reached the end of its window. Stripe records the released hold as a Refund and sets that reason itself. No API call of yours created it, and the customer was never charged in the first place, so nothing was really returned to them."),
 ("Should these count in my refund rate?",
  "No. A refund rate is meant to measure customers changing their mind or being dissatisfied. These measure your capture pipeline missing a deadline. Keeping them in the same number means an engineering problem shows up as a product problem, and the team that can fix it never hears about it."),
 ("How do I prove a refund is one of these rather than a real one?",
  "Fetch the charge it points at and read captured. A false there means no money was ever collected, which no genuine refund can be true of. That single field turns a suspicion about a reason string into something you can put in a ticket."),
 ("Is this the same check as watching for holds about to expire?",
  "No, and you want both. Watching capture_before on the charge tells you which authorizations you are about to lose while you can still capture them. This one counts the ones already lost and shows what they did to your reported numbers. One is a work queue, the other is the bill."),
 ("Can I get alerted when one appears?",
  "Yes. Refund events are delivered like anything else, so a handler on charge.refund.updated that checks the reason will page you the same day rather than at the next monthly review. It is a lagging signal either way, but days late beats a quarter late."),
],
"related": [
 ("/stripe/expired-manual-capture-holds/", "Manual-capture holds expire before anyone captures them"),
 ("/stripe/refunds-failed-or-stuck/", "Refunds that failed or are stuck"),
 ("/stripe/stale-requires-payment-method-intents/", "Intents sitting in requires_payment_method for weeks"),
],
"citations": [CITE_REFUND_OBJECT, CITE_HOLD, CITE_REFUNDS, CITE_KEYS],
},

{
"slug": "elevated-risk-charges-no-review",
"title": "Elevated-risk charges captured with no manual review",
"description": "Radar scores a charge elevated and authorizes it anyway. Without a review rule nothing stops it, and the first you hear is the chargeback.",
"h1": "elevated-risk charges captured with no manual review",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe outcome risk_level elevated", "stripe radar review queue",
             "stripe manual review rule", "stripe elevated risk chargeback",
             "stripe radar not_assessed"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Disputes keep arriving for payments that went through weeks ago, and the chargeback rate is drifting toward the number the card networks care about. Open any one of them and Stripe already knew: the charge is marked elevated risk. Nobody was ever shown it, because nothing on the account was configured to show anybody anything.",
"short_answer": """<p>Paginate <code>GET /v1/charges?limit=100&amp;created[gte]=&lt;90 days ago&gt;</code> and keep the rows where <code>outcome.risk_level</code> is <code>"elevated"</code> and <code>outcome.type</code> is <code>"authorized"</code>. Count how many of those have <code>review: null</code> and <code>captured: true</code>. Those went to the bank, were captured, and never passed a human.</p>
<p>Then compare <code>disputed</code> across that group against your <code>normal</code>-risk baseline. The gap between the two rates is the cost of the missing review rule, in your own numbers rather than in general advice. If <code>not_assessed</code> dominates instead, Radar never scored the traffic at all and no rule of any kind could have fired.</p>""",
"problem": """<p>Radar's default rules block <code>highest</code>. They do nothing about <code>elevated</code>, and that is correct: <code>elevated</code> is the band where a meaningful share of the payments are genuine, so blocking it outright costs more in refused customers than it saves in fraud. The intended handling is a review queue, and a review queue only exists if somebody made one.</p>
<p>On an account where nobody did, the band behaves exactly like <code>normal</code>. The payment authorizes, captures, fulfils, and the risk score is written to a field that nothing in the integration reads. The Dashboard has a Reviews section, it is empty, and an empty queue looks identical whether it is empty because the traffic is clean or because it was never wired up.</p>
<p>The consequence lands six to eight weeks later as disputes, which is far enough away that it gets discussed as a fraud trend rather than as a configuration gap. Meanwhile every one of those disputes carries the fee, the lost goods, and a mark against the chargeback ratio that the networks measure you on.</p>""",
"why": """<p><strong>There is nothing to switch off, which is why nobody notices.</strong> The failure is an absent rule. A missing rule has no row in any list, no toggle in the wrong position, and no audit entry. Every screen you would think to check looks the way a healthy account looks.</p>
<p><strong>The score is written after the decision, on an object nobody reads.</strong> <code>outcome.risk_level</code> lands on the Charge. Order pipelines read the PaymentIntent status and move on; the charge is usually fetched only for receipts and refunds. The information was there the whole time, one field away from the code that shipped the goods.</p>
<p><strong>Review is a rule action, not a setting.</strong> Placing a payment in review means writing a Radar rule that says so &mdash; typically <code>:risk_level: = 'elevated'</code>, often narrowed by amount so the queue stays a size a human can actually work. Until that rule exists, <code>charge.review</code> is null on every payment, and null is the value the field has on a healthy account too.</p>
<p><strong>not_assessed is a different failure wearing the same clothes.</strong> If Radar never received a session from the client &mdash; Stripe.js not mounted on the payment page, or a server-side confirm without <code>radar_options[session]</code> &mdash; charges come back <code>not_assessed</code>. No score means no rule can match, so adding a review rule to that account changes nothing at all. Check this before you tune anything.</p>
<p><strong>The evidence is separated from the cause by weeks.</strong> Disputes arrive long after the payment, attributed to whoever is looking at fraud that month. Joining <code>disputed</code> back to <code>outcome.risk_level</code> on the same charges is what converts a vague sense that fraud is up into a specific, fixable gap.</p>""",
"steps": [
 {"h": "Scan 90 days, not 30",
  "body": """<p>Disputes lag the payment by weeks. A 30-day window shows you the elevated charges going through with the consequence still in the post, which reads as a much smaller problem than it is.</p>"""},
 {"h": "Check for not_assessed first",
  "body": """<p>If a large share of charges come back <code>not_assessed</code>, stop. Radar never scored them, so there is no risk band to act on and a review rule would sit there matching nothing. Get sessions flowing from the client, then come back.</p>"""},
 {"h": "Separate elevated charges that Radar already stopped",
  "body": """<p>An <code>outcome.type</code> other than <code>authorized</code> means a rule or the issuer already dealt with it. Those are not the finding. The finding is the ones that were authorized, captured, and never seen.</p>"""},
 {"h": "Treat uncaptured elevated charges as their own bucket",
  "body": """<p>An authorized but uncaptured elevated charge is a hold that can still be released, which is a different instruction to a human than one where the money already moved and the goods already shipped. It is also on a clock, so it belongs at the top of the output.</p>"""},
 {"h": "Compute the dispute rate for the group and compare it to normal",
  "body": """<p>This is the number that gets the rule written. If elevated charges dispute at several times the <code>normal</code> rate, the review queue pays for itself in one line of arithmetic. The repair is a Radar rule placing <code>:risk_level: = 'elevated'</code> in review, scoped by amount if the volume needs it, and somebody whose job is to work the queue daily.</p>"""},
],
"verify": """<p>Re-run over a window that begins after the rule was added. Elevated charges should be arriving in the review queue rather than in the captured-and-unseen bucket.</p>
<pre><code class="language-bash">python3 stripe_elevated_risk_review.py --days 90
# 3,104 charge(s): 0 elevated captured unreviewed, 41 reviewed, 0 not_assessed</code></pre>""",
"code_intro": "One paginated GET over Charges and no writes &mdash; a restricted key with read access to Charges is enough. The classifier is pure and reads five fields off one charge, because the distinctions that matter here are all made between charges that look identical from the order pipeline: scored or not scored, stopped or authorized, reviewed or not, captured or still a hold, disputed or not yet.",
"py_file": "stripe_elevated_risk_review.py",
"py": '''"""Report Stripe charges scored elevated risk that were captured with no review.

Read only. One paginated GET, no writes: give this a RESTRICTED key with read
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
log = logging.getLogger("stripe_elevated_risk_review")

API = "https://api.stripe.com/v1"


def verdict(charge):
    """Classify one Charge by what happened to an elevated risk score. Pure.

    Radar's default rules block `highest` and leave `elevated` alone, so an
    elevated charge is authorized and captured unless a review rule puts it in
    front of a human. `review` is null both when no such rule exists and on a
    perfectly healthy account, which is why the surrounding fields decide the
    verdict rather than that one on its own.

    Returns (state, detail).
    """
    outcome = charge.get("outcome") or {}
    risk = outcome.get("risk_level")

    if risk in (None, "not_assessed"):
        return ("not_assessed",
                "Radar never scored this charge: no Radar session reached the API, "
                "so no rule of any kind could have matched it")

    if risk != "elevated":
        return ("baseline", "risk_level %s, outside the scope of this check" % risk)

    if outcome.get("type") != "authorized":
        return ("stopped",
                "elevated and outcome.type %r: something already stopped it"
                % (outcome.get("type"),))

    if charge.get("review"):
        return ("reviewed", "elevated and placed in the manual review queue")

    if not charge.get("captured"):
        return ("uncaptured",
                "elevated and unreviewed, authorized but not captured: this is "
                "still a hold and it can be released rather than taken")

    if charge.get("disputed"):
        return ("disputed",
                "elevated, captured with no review in front of it, and already "
                "disputed: this one is the bill for the missing rule")

    return ("straight-through",
            "elevated risk, authorized, captured, and no human ever saw it")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_charges(session, since, limit):
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/charges", **params)
        rows = page.get("data", [])
        for charge in rows:
            yield charge
            seen += 1
        if not page.get("has_more") or not rows or seen >= limit:
            break
        params["starting_after"] = rows[-1]["id"]


def rate(disputed, total):
    return (100.0 * disputed / total) if total else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to scan charges (default 90)")
    ap.add_argument("--max-charges", type=int, default=5000,
                    help="stop paginating after this many charges")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400

    states = {}
    scanned = 0
    unreviewed_amount = {}
    normal_total = normal_disputed = 0
    elevated_total = elevated_disputed = 0

    for charge in page_charges(s, since, args.max_charges):
        scanned += 1
        state, detail = verdict(charge)
        states[state] = states.get(state, 0) + 1

        risk = (charge.get("outcome") or {}).get("risk_level")
        if risk == "normal" and charge.get("captured"):
            normal_total += 1
            normal_disputed += 1 if charge.get("disputed") else 0
        elif risk == "elevated" and charge.get("captured"):
            elevated_total += 1
            elevated_disputed += 1 if charge.get("disputed") else 0

        if state in ("straight-through", "disputed", "uncaptured"):
            currency = charge.get("currency") or "???"
            unreviewed_amount[currency] = (unreviewed_amount.get(currency, 0)
                                           + (charge.get("amount") or 0))
            log.warning("%-16s %s  %s", state, charge.get("id", "?"), detail)

    if not scanned:
        log.info("no charges in the last %d day(s)", args.days)
        return 0

    log.info("%d charge(s) in %d day(s): %s", scanned, args.days,
             ", ".join("%d %s" % (n, k) for k, n in sorted(states.items())))

    not_assessed = states.get("not_assessed", 0)
    if not_assessed > scanned / 2:
        log.warning("%d of %d charges are not_assessed: Radar is not scoring this "
                    "traffic, so fix that before adding any rule", not_assessed, scanned)
        log.warning("repair: mount Stripe.js on the payment page, or pass "
                    "radar_options[session] on server-side confirms")
        return 1

    leaked = states.get("straight-through", 0) + states.get("disputed", 0)
    if not leaked and not states.get("uncaptured", 0):
        log.info("no elevated-risk charge was captured without a review")
        return 0

    for currency, amount in sorted(unreviewed_amount.items()):
        log.warning("elevated and unreviewed: %.2f %s", amount / 100.0, currency.upper())
    log.warning("dispute rate: elevated %.2f%% (%d/%d) vs normal %.2f%% (%d/%d)",
                rate(elevated_disputed, elevated_total), elevated_disputed, elevated_total,
                rate(normal_disputed, normal_total), normal_disputed, normal_total)
    log.warning("repair: Dashboard, Radar, Rules: add \\"Place in review if "
                ":risk_level: = 'elevated'\\", scoped by amount if the queue is "
                "too large to work daily")
    log.warning("repair: give the review queue an owner; a queue nobody works "
                "expires its own payments and is worse than no queue")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-elevated-risk-review.mjs",
"js": '''/**
 * Report Stripe charges scored elevated risk that were captured with no review.
 *
 * Read only. One paginated GET, no writes: give this a RESTRICTED key with read
 * access to Charges. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one Charge by what happened to an elevated risk score. Pure.
 *
 * Radar's defaults block `highest` and leave `elevated` alone, so an elevated
 * charge is authorized and captured unless a review rule puts it in front of a
 * human. `review` is null both when no such rule exists and on a healthy
 * account, so the surrounding fields decide the verdict rather than that one.
 */
export function verdict(charge) {
  const outcome = charge.outcome ?? {};
  const risk = outcome.risk_level ?? null;

  if (risk === null || risk === 'not_assessed') {
    return ['not_assessed',
      'Radar never scored this charge: no Radar session reached the API, so no ' +
      'rule of any kind could have matched it'];
  }

  if (risk !== 'elevated') {
    return ['baseline', `risk_level ${risk}, outside the scope of this check`];
  }

  if (outcome.type !== 'authorized') {
    return ['stopped',
      `elevated and outcome.type ${JSON.stringify(outcome.type)}: something ` +
      'already stopped it'];
  }

  if (charge.review) {
    return ['reviewed', 'elevated and placed in the manual review queue'];
  }

  if (!charge.captured) {
    return ['uncaptured',
      'elevated and unreviewed, authorized but not captured: this is still a ' +
      'hold and it can be released rather than taken'];
  }

  if (charge.disputed) {
    return ['disputed',
      'elevated, captured with no review in front of it, and already disputed: ' +
      'this one is the bill for the missing rule'];
  }

  return ['straight-through',
    'elevated risk, authorized, captured, and no human ever saw it'];
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

async function* pageCharges(key, since, limit) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/charges', params);
    const rows = page.data ?? [];
    for (const charge of rows) { yield charge; seen += 1; }
    if (!page.has_more || rows.length === 0 || seen >= limit) break;
    params.starting_after = rows[rows.length - 1].id;
  }
}

const rate = (disputed, total) => (total ? (100 * disputed) / total : 0);

async function main() {
  const days = Number(process.argv[2] ?? 90);

  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const since = Math.floor(Date.now() / 1000) - days * 86400;
  const states = new Map();
  const unreviewed = new Map();
  let scanned = 0;
  let normalTotal = 0; let normalDisputed = 0;
  let elevatedTotal = 0; let elevatedDisputed = 0;

  for await (const charge of pageCharges(key, since, 5000)) {
    scanned += 1;
    const [state, detail] = verdict(charge);
    states.set(state, (states.get(state) ?? 0) + 1);

    const risk = (charge.outcome ?? {}).risk_level;
    if (risk === 'normal' && charge.captured) {
      normalTotal += 1;
      if (charge.disputed) normalDisputed += 1;
    } else if (risk === 'elevated' && charge.captured) {
      elevatedTotal += 1;
      if (charge.disputed) elevatedDisputed += 1;
    }

    if (state === 'straight-through' || state === 'disputed' || state === 'uncaptured') {
      const currency = charge.currency ?? '???';
      unreviewed.set(currency, (unreviewed.get(currency) ?? 0) + (charge.amount ?? 0));
      console.warn(`${state.padEnd(16)} ${charge.id ?? '?'}  ${detail}`);
    }
  }

  if (scanned === 0) {
    console.log(`no charges in the last ${days} day(s)`);
    return;
  }

  const summary = [...states.entries()].sort().map(([k, n]) => `${n} ${k}`).join(', ');
  console.log(`${scanned} charge(s) in ${days} day(s): ${summary}`);

  const notAssessed = states.get('not_assessed') ?? 0;
  if (notAssessed > scanned / 2) {
    console.warn(`${notAssessed} of ${scanned} charges are not_assessed: Radar is ` +
      'not scoring this traffic, so fix that before adding any rule');
    console.warn('repair: mount Stripe.js on the payment page, or pass ' +
      'radar_options[session] on server-side confirms');
    process.exitCode = 1;
    return;
  }

  const leaked = (states.get('straight-through') ?? 0) + (states.get('disputed') ?? 0);
  if (!leaked && !(states.get('uncaptured') ?? 0)) {
    console.log('no elevated-risk charge was captured without a review');
    return;
  }

  for (const [currency, amount] of [...unreviewed.entries()].sort()) {
    console.warn(`elevated and unreviewed: ${(amount / 100).toFixed(2)} ${currency.toUpperCase()}`);
  }
  console.warn(
    `dispute rate: elevated ${rate(elevatedDisputed, elevatedTotal).toFixed(2)}% ` +
    `(${elevatedDisputed}/${elevatedTotal}) vs normal ` +
    `${rate(normalDisputed, normalTotal).toFixed(2)}% (${normalDisputed}/${normalTotal})`);
  console.warn("repair: Dashboard, Radar, Rules: add \\"Place in review if " +
    ":risk_level: = 'elevated'\\", scoped by amount if the queue is too large to work daily");
  console.warn('repair: give the review queue an owner; a queue nobody works ' +
    'expires its own payments and is worse than no queue');
  process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that look alike from the order pipeline. An elevated charge Radar already stopped, one a human reviewed, and one that sailed through all read as the same score on the same object, and only the surrounding fields tell them apart. The not_assessed case is pinned separately because it is the one where adding the rule everybody reaches for would change nothing.",
"test_py_file": "test_stripe_elevated_risk_review.py",
"test_py": '''from stripe_elevated_risk_review import verdict


def charge(risk="elevated", outcome_type="authorized", review=None,
           captured=True, disputed=False):
    return {
        "id": "ch_1",
        "amount": 12900,
        "currency": "usd",
        "captured": captured,
        "disputed": disputed,
        "review": review,
        "outcome": {"risk_level": risk, "type": outcome_type},
    }


def test_elevated_captured_with_no_review_is_the_finding():
    state, detail = verdict(charge())
    assert state == "straight-through"
    assert "no human" in detail


def test_elevated_that_reached_review_is_not_flagged():
    assert verdict(charge(review="prv_1"))[0] == "reviewed"


def test_elevated_still_on_a_hold_is_its_own_state():
    # Different instruction to a human: this one can still be released.
    state, detail = verdict(charge(captured=False))
    assert state == "uncaptured"
    assert "released" in detail


def test_elevated_already_disputed_is_separated_from_the_rest():
    assert verdict(charge(disputed=True))[0] == "disputed"


def test_not_assessed_is_not_reported_as_clean():
    state, detail = verdict(charge(risk="not_assessed"))
    assert state == "not_assessed"
    assert "never scored" in detail
''',
"test_js_file": "stripe-elevated-risk-review.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-elevated-risk-review.mjs';

function charge({ risk = 'elevated', type = 'authorized', review = null,
                  captured = true, disputed = false } = {}) {
  return {
    id: 'ch_1',
    amount: 12900,
    currency: 'usd',
    captured,
    disputed,
    review,
    outcome: { risk_level: risk, type },
  };
}

test('elevated captured with no review is the finding', () => {
  const [state, detail] = verdict(charge());
  assert.equal(state, 'straight-through');
  assert.match(detail, /no human/);
});

test('elevated that reached review is not flagged', () => {
  assert.equal(verdict(charge({ review: 'prv_1' }))[0], 'reviewed');
});

test('elevated still on a hold is its own state', () => {
  const [state, detail] = verdict(charge({ captured: false }));
  assert.equal(state, 'uncaptured');
  assert.match(detail, /released/);
});

test('elevated already disputed is separated from the rest', () => {
  assert.equal(verdict(charge({ disputed: true }))[0], 'disputed');
});

test('not_assessed is not reported as clean', () => {
  const [state, detail] = verdict(charge({ risk: 'not_assessed' }));
  assert.equal(state, 'not_assessed');
  assert.match(detail, /never scored/);
});
''',
"faq": [
 ("Why does Stripe capture elevated-risk payments by default?",
  "Because a large share of them are genuine. Radar's default rules block the highest band, where the evidence is strong enough that refusing is cheaper than accepting. Elevated is the band where a blanket block would cost more in turned-away customers than it saves, which is why the intended handling is a review queue rather than a rule that refuses."),
 ("Is this the same as highest-risk charges getting through?",
  "No. A highest-risk charge succeeding means something overrode a rule that exists and is enabled, usually an allow rule sitting above it. An elevated-risk charge succeeding means no rule ever applied to it, because none was written. One is an override to find, the other is an absence to fill."),
 ("What if most of my charges come back not_assessed?",
  "Then Radar is not scoring your traffic and no review rule will help. It means no Radar session reached the API: Stripe.js is not mounted on the payment page, or a server-side confirm is not passing radar_options[session]. Fix that first, wait for a fresh window of scored charges, then look at risk levels."),
 ("How large will the review queue be?",
  "Larger than you expect, which is why the rule usually needs scoping. Adding an amount condition so only elevated payments above a threshold go to review keeps the queue at a size a person can actually work. A queue nobody works is worse than none, because payments sitting in review can expire while they wait."),
 ("Does this script need a live secret key?",
  "No. A restricted key with read access to Charges covers every call it makes. It never approves, refuses, refunds, or captures anything, so a leak exposes the shape of your payment volume and nothing else."),
],
"related": [
 ("/stripe/highest-risk-charges-succeeded/", "Highest-risk charges succeed instead of being blocked"),
 ("/stripe/radar-blocked-payments-ignored/", "Radar blocks payments and nobody reads the reasons"),
 ("/stripe/disputes-lost-without-response/", "Disputes lost without a response"),
],
"citations": [CITE_RADAR_REVIEWS, CITE_RADAR_RULES, CITE_CHARGE_OBJECT, CITE_DECLINES],
},

{
"slug": "incomplete-expired-signup-leak",
"title": "incomplete_expired volume means confirmation is broken",
"description": "A stack of incomplete_expired subscriptions is not customers changing their mind. Measured against activations it is a broken confirmation step.",
"h1": "incomplete_expired volume means confirmation is broken",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["incomplete_expired stripe", "stripe subscriptions never activate",
             "stripe signup conversion drop", "payment_behavior default_incomplete",
             "stripe first invoice never confirmed"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Sign-ups are steady, marketing spend is steady, and paid subscriptions are down. There are no failed payments to look at, because no payment was ever attempted. Filter the subscription list to <code>incomplete_expired</code> and there they are: a few hundred people who thought they had subscribed, in a state that Stripe considers finished.",
"short_answer": """<p>Count both populations over the same window and divide. <code>GET /v1/subscriptions?status=incomplete_expired&amp;limit=100&amp;created[gte]=&lt;30 days ago&gt;</code> against <code>GET /v1/subscriptions?status=active&amp;limit=100&amp;created[gte]=&lt;the same timestamp&gt;</code>, paginating both.</p>
<p>A ratio under a few percent is ordinary abandonment. At roughly 10% of activations the confirmation step is failing for a slice of your traffic. If activations are near zero while the expired count is not, nothing is confirming at all and the checkout has been broken since whatever shipped last.</p>""",
"problem": """<p><code>incomplete_expired</code> is what a first invoice becomes when nobody pays it within Stripe's window. It is terminal. There is no call that reopens it, no retry, and the invoice attached to it has been voided. Whatever the customer believed when they closed the tab, the only route back is a fresh subscription with a payment method you do not have.</p>
<p>What makes this hard to see is that a single expired record is unremarkable. People do abandon card forms. The failure only becomes legible as a proportion: dozens of them against a handful of activations is not a hundred people changing their mind, it is a step in your checkout that a hundred people could not get past. Nobody computes that proportion, because no screen puts the two counts next to each other.</p>
<p>Meanwhile every other signal says the funnel is fine. The <code>POST /v1/subscriptions</code> call returned 200 for every one of them. Product analytics recorded the signup event on the server. Only the money is missing, and it goes missing quietly enough that the first suspicion is usually a marketing channel rather than a bug.</p>""",
"why": """<p><strong>The ratio is the measurement, not the count.</strong> Two hundred expired subscriptions against four thousand activations is background noise. Two hundred against three hundred is an outage that has been running for a month. The same absolute number means opposite things, which is why any check built on a threshold count reports nothing useful.</p>
<p><strong>The client never finishes what the server started.</strong> The intended flow creates the subscription with <code>payment_behavior=default_incomplete</code>, hands the first invoice's confirmation secret to the browser, and confirms it there. An integration that creates the subscription server-side and then redirects to a thank-you page has skipped the only step that takes money. Every signup through that path expires.</p>
<p><strong>Partial breakage looks like a conversion dip.</strong> When the confirmation fails only in some conditions &mdash; one browser, one payment method, a redirect that drops a query parameter on mobile &mdash; the ratio moves from 2% to 15% rather than to 100%. That is exactly the size of change a growth team will attribute to seasonality for a quarter.</p>
<p><strong>The evidence expires on its own schedule.</strong> Records that are still <code>incomplete</code> can be looked at while they are live, and those are the actionable ones. By the time they read <code>incomplete_expired</code>, the invoice is void and the state is frozen. The pile is only useful as a measurement, which is what this check treats it as.</p>
<p><strong>Nothing fires when it happens.</strong> There is a <code>customer.subscription.updated</code> event carrying the transition, but no failure event and no dunning, because there was never a payment to fail. An integration listening for payment problems will never hear about this one.</p>""",
"steps": [
 {"h": "Count both statuses over one identical window",
  "body": """<p>The same <code>created[gte]</code> timestamp on both queries, or the ratio is meaningless. Thirty days is a reasonable default: long enough that a slow week does not swing it, short enough that a fix shows up in the next run.</p>"""},
 {"h": "Paginate to the end of both",
  "body": """<p>Stripe caps a page at 100. A check that reads one page of each and divides reports 1.00 on any account with real volume, which is both alarming and wrong. Page both lists fully before dividing anything.</p>"""},
 {"h": "Judge the ratio, not the count",
  "body": """<p>Under a few percent is ordinary abandonment on a card form. Around 10% of activations means a slice of traffic cannot complete the step. Half or more means it is broken for most people and the exceptions are the interesting ones.</p>"""},
 {"h": "Handle zero activations explicitly",
  "body": """<p>Expired subscriptions with no activations at all is the worst case, and it is also the one that divides by zero. It deserves its own verdict rather than an error or a silently skipped run, because it is the state that most needs a page.</p>"""},
 {"h": "Fix the creation call, and watch the live ones as well",
  "body": """<p>The repair is on the create path: <code>payment_behavior=default_incomplete</code>, expand the latest invoice, pass its confirmation secret to the client, confirm in the same session, and handle <code>invoice.payment_action_required</code> so an unfinished one gets an email instead of a countdown. For the records still inside the window, <a href="/stripe/subscriptions-stuck-incomplete/">ageing the live incomplete ones</a> is the check that can still rescue individuals.</p>"""},
],
"verify": """<p>Re-run a full window after the confirmation fix has been live for thirty days. The ratio should fall back to abandonment levels, and the absolute count should stop tracking your signup volume.</p>
<pre><code class="language-bash">python3 stripe_incomplete_expired_rate.py --days 30
# 30 day(s): 12 expired, 940 active — background, 1.3% of activations</code></pre>""",
"code_intro": "Two paginated GETs and no writes &mdash; a restricted key with read access to Subscriptions is enough. The classifier here takes two counts rather than one object, because the finding is a rate: the same number of expired subscriptions is noise on one account and an outage on another, and a function that only sees one row can never say which.",
"py_file": "stripe_incomplete_expired_rate.py",
"py": '''"""Measure Stripe incomplete_expired subscriptions against activations.

Read only. Two paginated GETs, no writes: give this a RESTRICTED key with read
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
log = logging.getLogger("stripe_incomplete_expired_rate")

API = "https://api.stripe.com/v1"

# Share of activations above which the confirmation step is failing for part of
# the traffic rather than being abandoned by part of the customers.
LEAKING = 0.10
# Above this, it is not a slice of traffic any more.
BROKEN = 0.50


def verdict(expired, active, days=30, leaking=LEAKING, broken=BROKEN):
    """Judge one window of signups by the share that never confirmed. Pure.

    Takes two counts rather than one subscription, because the finding is a
    ratio: 200 expired subscriptions is background noise against 4,000
    activations and an outage against 300, and no single row can tell you which.

    Returns (state, detail).
    """
    if expired < 0 or active < 0:
        return ("unknown", "negative counts, so the ratio means nothing")

    if expired == 0 and active == 0:
        return ("no-signups",
                "no subscriptions created in the last %d day(s), so there is "
                "nothing to measure" % days)

    if expired == 0:
        return ("clean",
                "%d activation(s) in %d day(s) and nothing expired unconfirmed"
                % (active, days))

    if active == 0:
        return ("broken",
                "%d subscription(s) expired unconfirmed and not one activated in "
                "%d day(s): nothing is confirming at all" % (expired, days))

    ratio = expired / active
    pct = 100.0 * ratio

    if ratio >= broken:
        return ("broken",
                "%d expired against %d activation(s), %.1f%%: the confirmation "
                "step is failing for most of the traffic" % (expired, active, pct))

    if ratio >= leaking:
        return ("leaking",
                "%d expired against %d activation(s), %.1f%%: a slice of the "
                "traffic cannot complete the confirmation" % (expired, active, pct))

    return ("background",
            "%d expired against %d activation(s), %.1f%%: ordinary abandonment"
            % (expired, active, pct))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def count(session, status, since, limit):
    """Page a status to the end. One page of each and a division is a wrong answer."""
    total = 0
    params = {"status": status, "limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/subscriptions", **params)
        rows = page.get("data", [])
        total += len(rows)
        if not page.get("has_more") or not rows or total >= limit:
            break
        params["starting_after"] = rows[-1]["id"]
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="window to measure, in days (default 30)")
    ap.add_argument("--max-rows", type=int, default=5000,
                    help="stop paginating each status after this many rows")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    expired = count(s, "incomplete_expired", since, args.max_rows)
    active = count(s, "active", since, args.max_rows)

    state, detail = verdict(expired, active, args.days)
    if state in ("clean", "background", "no-signups"):
        log.info("%s: %s", state, detail)
        return 0

    log.warning("%s: %s", state, detail)
    log.warning("repair: create with payment_behavior=default_incomplete, expand "
                "latest_invoice.confirmation_secret, and confirm it client side "
                "in the same session")
    log.warning("repair: handle invoice.payment_action_required so an unfinished "
                "signup gets an email rather than a countdown")
    log.warning("note: expired subscriptions are terminal. The invoice is void "
                "and no API call revives them; these customers need a new signup.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-incomplete-expired-rate.mjs",
"js": '''/**
 * Measure Stripe incomplete_expired subscriptions against activations.
 *
 * Read only. Two paginated GETs, no writes: give this a RESTRICTED key with read
 * access to Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Share of activations above which the confirmation step is failing for part of
// the traffic rather than being abandoned by part of the customers.
export const LEAKING = 0.10;
export const BROKEN = 0.50;

/**
 * Judge one window of signups by the share that never confirmed. Pure.
 *
 * Takes two counts rather than one subscription, because the finding is a ratio:
 * 200 expired is noise against 4,000 activations and an outage against 300.
 */
export function verdict(expired, active, days = 30, leaking = LEAKING, broken = BROKEN) {
  if (expired < 0 || active < 0) {
    return ['unknown', 'negative counts, so the ratio means nothing'];
  }

  if (expired === 0 && active === 0) {
    return ['no-signups',
      `no subscriptions created in the last ${days} day(s), so there is nothing to measure`];
  }

  if (expired === 0) {
    return ['clean',
      `${active} activation(s) in ${days} day(s) and nothing expired unconfirmed`];
  }

  if (active === 0) {
    return ['broken',
      `${expired} subscription(s) expired unconfirmed and not one activated in ` +
      `${days} day(s): nothing is confirming at all`];
  }

  const ratio = expired / active;
  const pct = (100 * ratio).toFixed(1);

  if (ratio >= broken) {
    return ['broken',
      `${expired} expired against ${active} activation(s), ${pct}%: the ` +
      'confirmation step is failing for most of the traffic'];
  }

  if (ratio >= leaking) {
    return ['leaking',
      `${expired} expired against ${active} activation(s), ${pct}%: a slice of ` +
      'the traffic cannot complete the confirmation'];
  }

  return ['background',
    `${expired} expired against ${active} activation(s), ${pct}%: ordinary abandonment`];
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

// Page a status to the end. One page of each and a division is a wrong answer.
async function count(key, status, since, limit) {
  let total = 0;
  const params = { status, limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const rows = page.data ?? [];
    total += rows.length;
    if (!page.has_more || rows.length === 0 || total >= limit) break;
    params.starting_after = rows[rows.length - 1].id;
  }
  return total;
}

async function main() {
  const days = Number(process.argv[2] ?? 30);

  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const since = Math.floor(Date.now() / 1000) - days * 86400;
  const expired = await count(key, 'incomplete_expired', since, 5000);
  const active = await count(key, 'active', since, 5000);

  const [state, detail] = verdict(expired, active, days);
  if (state === 'clean' || state === 'background' || state === 'no-signups') {
    console.log(`${state}: ${detail}`);
    return;
  }

  console.warn(`${state}: ${detail}`);
  console.warn('repair: create with payment_behavior=default_incomplete, expand ' +
    'latest_invoice.confirmation_secret, and confirm it client side in the same session');
  console.warn('repair: handle invoice.payment_action_required so an unfinished ' +
    'signup gets an email rather than a countdown');
  console.warn('note: expired subscriptions are terminal. The invoice is void and ' +
    'no API call revives them; these customers need a new signup.');
  process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the two ends that a count-based check gets wrong. The same twenty expired subscriptions must read as background against a healthy activation number and as a leak against a small one, and expired signups with no activations at all has to produce a verdict rather than a division by zero.",
"test_py_file": "test_stripe_incomplete_expired_rate.py",
"test_py": '''from stripe_incomplete_expired_rate import verdict


def test_the_same_count_is_noise_against_enough_activations():
    state, detail = verdict(20, 4000)
    assert state == "background"
    assert "abandonment" in detail


def test_the_same_count_is_a_leak_against_a_small_one():
    # 20 of 150 is 13% of activations: a slice of traffic cannot confirm.
    state, detail = verdict(20, 150)
    assert state == "leaking"
    assert "13.3%" in detail


def test_expired_with_no_activations_does_not_divide_by_zero():
    state, detail = verdict(31, 0, days=14)
    assert state == "broken"
    assert "not one activated" in detail


def test_a_quiet_window_is_not_reported_as_healthy_signups():
    assert verdict(0, 0)[0] == "no-signups"


def test_nothing_expired_is_clean():
    assert verdict(0, 900)[0] == "clean"
''',
"test_js_file": "stripe-incomplete-expired-rate.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-incomplete-expired-rate.mjs';

test('the same count is noise against enough activations', () => {
  const [state, detail] = verdict(20, 4000);
  assert.equal(state, 'background');
  assert.match(detail, /abandonment/);
});

test('the same count is a leak against a small one', () => {
  const [state, detail] = verdict(20, 150);
  assert.equal(state, 'leaking');
  assert.match(detail, /13\\.3%/);
});

test('expired with no activations does not divide by zero', () => {
  const [state, detail] = verdict(31, 0, 14);
  assert.equal(state, 'broken');
  assert.match(detail, /not one activated/);
});

test('a quiet window is not reported as healthy signups', () => {
  assert.equal(verdict(0, 0)[0], 'no-signups');
});

test('nothing expired is clean', () => {
  assert.equal(verdict(0, 900)[0], 'clean');
});
''',
"faq": [
 ("What is incomplete_expired?",
  "The terminal state of a subscription whose very first invoice was never paid inside Stripe's window. The invoice is voided and the subscription cannot be transitioned back. It is not a cancellation and not a failed payment; it is a signup that never became one."),
 ("How many is too many?",
  "It depends entirely on your activation volume, which is why the check divides rather than counts. Under a few percent of activations is normal abandonment on a card form. Around ten percent means part of your traffic cannot complete the confirmation. Expired signups with no activations at all means it is broken for everyone."),
 ("Can I recover the expired subscriptions?",
  "No. There is no call that revives one, and the attached invoice is already void. The only path is a new subscription, which needs a payment method you do not have, which means an email to somebody who believes they already subscribed. Fix the creation flow first so the pile stops growing."),
 ("How is this different from watching the incomplete ones?",
  "Different window and different purpose. Ageing live incomplete subscriptions catches individual records while there is still time for a human to rescue them. This check measures the ones already lost, as a rate, to tell you whether the checkout has a bug at all. Run both: one is a work queue, the other is a diagnosis."),
 ("Why does nothing alert on this today?",
  "Because nothing failed. No payment was attempted, so there is no failed-payment event, no decline code, and no dunning. The transition is carried on customer.subscription.updated among a great deal of other traffic, and an integration listening for payment problems will never hear it."),
],
"related": [
 ("/stripe/subscriptions-stuck-incomplete/", "Incomplete subscriptions die silently after 23 hours"),
 ("/stripe/sca-authentication-stuck-subscriptions/", "Subscriptions frozen on requires_action 3DS authentication"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with no payment method to charge"),
],
"citations": [CITE_SUB_OBJECT, CITE_SUB_CREATE, CITE_SUB_OVERVIEW, CITE_KEYS],
},

{
"slug": "sca-authentication-stuck-subscriptions",
"title": "Subscriptions frozen on requires_action 3DS authentication",
"description": "The issuer asked for a 3DS challenge and nobody showed it. The invoice stays open, the subscription stays incomplete, and retries never run.",
"h1": "subscriptions frozen on requires_action 3DS authentication",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe subscription requires_action", "stripe 3ds subscription stuck",
             "invoice payment_action_required", "stripe sca subscription incomplete",
             "stripe authentication_required retry"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "European signups convert worse than everyone else's and support has nothing to go on. The card is good, the customer entered it correctly, and the bank was ready to approve the payment as soon as somebody answered a question. Nobody asked them the question. The invoice is still open, waiting.",
"short_answer": """<p>Read the incomplete subscriptions and look at the intent behind the first invoice. On API versions before <code>2025-03-31.basil</code>: <code>GET /v1/subscriptions?status=incomplete&amp;limit=100&amp;expand[]=data.latest_invoice.payment_intent</code>, and flag rows where <code>latest_invoice.payment_intent.status</code> is <code>"requires_action"</code>. On Basil and later the intent moved: <code>GET /v1/invoices?status=open&amp;limit=100&amp;expand[]=data.payments.data.payment.payment_intent</code> reaches the same field.</p>
<p>Sort what you find by the intent status. <code>requires_action</code> is an unanswered 3DS challenge. <code>requires_payment_method</code> with a decline code is an ordinary card failure and a different repair. Treating both as "the subscription did not activate" is what hides the first behind the second.</p>""",
"problem": """<p>An unanswered authentication is not a decline. The issuer did not refuse the payment; it asked for a step-up and is waiting. So there is no <code>failure_code</code> to group by, no failed-payment event, and nothing in a dunning report. The invoice sits at <code>open</code> and the subscription at <code>incomplete</code>, which is exactly what a subscription looks like for the ordinary few seconds between creation and payment.</p>
<p>Retries do not save it either. <code>authentication_required</code> is on Stripe's hard-decline list, so the smart-retry schedule will not turn an unanswered challenge into a payment. Attempts get scheduled and go nowhere, because nothing about a retry produces the challenge screen the customer never saw.</p>
<p>The distribution is what makes it get misread. SCA applies to cards in the European Economic Area and the UK, and India mandates step-up authentication, so this only bites part of your traffic. From a dashboard it looks like certain markets convert badly, which is a plausible enough story to survive several quarters.</p>""",
"why": """<p><strong>The challenge has to be shown, and the code shows it only if it was written to.</strong> Handling a subscription signup means checking the returned intent status and calling <code>stripe.handleNextAction</code> with the client secret when it is <code>requires_action</code>. Code that branches on <code>succeeded</code> and treats everything else as an error leaves a customer looking at a spinner while a real payment waits behind it.</p>
<p><strong>Nobody emails them either.</strong> Stripe can send the customer a link to the Hosted Invoice Page where the challenge can be completed, but the automatic collection reminders have to be turned on, and the <code>invoice.payment_action_required</code> event has to be handled by someone. Neither is on by default, so a customer who leaves the page has no route back to a payment that is still open.</p>
<p><strong>The field moved between API versions.</strong> Before <code>2025-03-31.basil</code> the intent hangs off <code>invoice.payment_intent</code>. On Basil and later it is reached through the invoice's <code>payments</code> collection. A check written against one shape reports every subscription as unreadable on the other, which looks enough like a clean result to be believed.</p>
<p><strong>The two ways a first invoice fails need different repairs.</strong> An unanswered challenge is a client-side handoff bug and the money is still collectable. A declined card is a payment problem and needs a new card. Both leave the subscription <code>incomplete</code>, and a check that only reports the status cannot tell you which conversation to have.</p>
<p><strong>It is silently on a clock.</strong> The subscription is not going to wait indefinitely; a first invoice that stays unpaid expires and takes the signup with it. That deadline runs whether or not anybody knows the challenge is outstanding.</p>""",
"steps": [
 {"h": "Expand down to the PaymentIntent, and handle both shapes",
  "body": """<p>The subscription status alone tells you nothing about the cause. Read the intent behind the first invoice, and write the lookup so it finds the field on either side of the Basil change rather than reporting the whole account as unreadable on one of them.</p>"""},
 {"h": "Split requires_action from requires_payment_method",
  "body": """<p>This is the entire diagnosis. <code>requires_action</code> means a bank challenge was never shown and the payment is still live. <code>requires_payment_method</code> with a decline code means the card failed. The first is a bug in your checkout, the second is an email asking for a different card.</p>"""},
 {"h": "Read next_action to see what was supposed to happen",
  "body": """<p><code>use_stripe_sdk</code> means the client was expected to call into Stripe.js and did not. <code>redirect_to_url</code> means the customer should have been sent to the issuer. An empty <code>next_action</code> on a <code>requires_action</code> intent is a third thing again: nothing was ever prepared for the customer to do.</p>"""},
 {"h": "Check where the affected customers are",
  "body": """<p>If the stuck ones cluster in the EEA, the UK, or India, that is the regulation choosing them and it confirms the reading. It also explains why the problem never reproduced for anyone testing on a US card.</p>"""},
 {"h": "Turn on the recovery path before fixing the code",
  "body": """<p>The repair takes two parts. Enable automatic collection reminders so Stripe mails the Hosted Invoice Page link when a payment needs authentication, which recovers the customers already stuck. Then handle <code>invoice.payment_action_required</code> and pass the client secret to <code>stripe.handleNextAction</code> in the signup flow, so the next one never gets stuck at all.</p>"""},
],
"verify": """<p>Re-run after the handler ships. New incomplete subscriptions should be minutes old and resolving on their own, and nothing should be sitting at <code>requires_action</code> from previous days.</p>
<pre><code class="language-bash">python3 stripe_sca_stuck_subs.py
# 6 incomplete subscription(s): 0 awaiting authentication, 4 declined, 2 unconfirmed</code></pre>""",
"code_intro": "One paginated GET with an expansion, and no writes &mdash; a restricted key with read access to Subscriptions, Invoices and PaymentIntents is enough. The intent lookup is a pure function of its own because the field moved between API versions, and a check that silently reads the wrong shape reports a clean account rather than an error. The classifier then splits the unanswered challenges from the declines, which is the whole point of running it.",
"py_file": "stripe_sca_stuck_subs.py",
"py": '''"""Report Stripe subscriptions frozen on an unanswered 3DS authentication.

Read only. One paginated GET with an expansion, no writes: give this a
RESTRICTED key with read access to Subscriptions, Invoices and PaymentIntents.
The repair is printed, never performed, because this script holds a credential
to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_sca_stuck_subs")

API = "https://api.stripe.com/v1"


def intent_of(invoice):
    """Find the PaymentIntent on an invoice across the Basil API change. Pure.

    Before 2025-03-31.basil the intent hangs off `invoice.payment_intent`. On
    Basil and later it is reached through the invoice's `payments` collection.
    A check that only knows one shape reads every row as unexpanded on the
    other, which looks like a clean account rather than a broken query.

    Returns the intent dict, or None.
    """
    if not isinstance(invoice, dict):
        return None
    intent = invoice.get("payment_intent")
    if isinstance(intent, dict):
        return intent
    for payment in ((invoice.get("payments") or {}).get("data") or []):
        candidate = (payment.get("payment") or {}).get("payment_intent")
        if isinstance(candidate, dict):
            return candidate
    return None


def verdict(sub):
    """Say why one incomplete subscription never activated. Pure.

    The subscription status is the same whichever way the first invoice failed,
    so the answer is on the PaymentIntent behind it: an unanswered bank challenge
    is a client-side handoff bug with the money still collectable, and a decline
    is a card problem that needs a different card.

    Returns (state, detail).
    """
    status = sub.get("status")
    if status != "incomplete":
        return ("other", "status %r: not waiting on a first payment" % (status,))

    intent = intent_of(sub.get("latest_invoice"))
    if intent is None:
        return ("unexpanded",
                "no PaymentIntent found on the first invoice: expand "
                "latest_invoice.payment_intent, or on 2025-03-31.basil and later "
                "read payments.data.payment.payment_intent")

    pi_status = intent.get("status")

    if pi_status == "requires_action":
        action = (intent.get("next_action") or {}).get("type")
        if not action:
            return ("no-next-action",
                    "the intent wants authentication but nothing was prepared "
                    "for the customer to do, so nobody can finish this one")
        return ("authentication",
                "the issuer asked for a challenge (%s) and it was never shown to "
                "the customer; the payment is still live" % action)

    if pi_status == "requires_payment_method":
        error = intent.get("last_payment_error") or {}
        code = error.get("decline_code") or error.get("code") or "no code recorded"
        return ("declined",
                "the card failed (%s): a decline, not an unanswered challenge, so "
                "this customer needs a different card" % code)

    if pi_status == "requires_confirmation":
        return ("unconfirmed",
                "the intent was created and never confirmed at all: the client "
                "never called confirm, so no bank has seen this payment")

    if pi_status == "processing":
        return ("settling", "the payment is in flight, nothing to do yet")

    return ("other", "payment_intent status %r on an incomplete subscription"
            % (pi_status,))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_subscriptions(session, limit):
    seen = 0
    params = {"status": "incomplete", "limit": 100,
              "expand[]": "data.latest_invoice.payment_intent"}
    while True:
        page = get(session, "/subscriptions", **params)
        rows = page.get("data", [])
        for sub in rows:
            yield sub
            seen += 1
        if not page.get("has_more") or not rows or seen >= limit:
            break
        params["starting_after"] = rows[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=1000,
                    help="stop paginating after this many subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    states = {}
    scanned = 0
    for sub in page_subscriptions(s, args.max_subscriptions):
        scanned += 1
        state, detail = verdict(sub)
        states[state] = states.get(state, 0) + 1
        if state in ("authentication", "no-next-action", "unexpanded"):
            log.warning("%-15s %s  %s", state, sub.get("id", "?"), detail)
        elif state == "declined":
            log.info("%-15s %s  %s", state, sub.get("id", "?"), detail)

    if not scanned:
        log.info("no incomplete subscriptions")
        return 0

    log.info("%d incomplete subscription(s): %s", scanned,
             ", ".join("%d %s" % (n, k) for k, n in sorted(states.items())))

    if states.get("unexpanded"):
        log.warning("repair: re-run with the expansion that matches your API "
                    "version; an unreadable row is not a healthy one")

    stuck = states.get("authentication", 0) + states.get("no-next-action", 0)
    if not stuck:
        log.info("nothing is waiting on an unanswered authentication")
        return 1 if states.get("unexpanded") else 0

    log.warning("repair: Dashboard, Settings, Billing, Automatic collection: turn "
                "on reminder emails so Stripe sends the Hosted Invoice Page link "
                "when a payment needs authentication")
    log.warning("repair: handle invoice.payment_action_required and pass the "
                "client secret to stripe.handleNextAction in the signup flow")
    log.warning("note: authentication_required is a hard decline, so smart "
                "retries will never clear these on their own")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-sca-stuck-subs.mjs",
"js": '''/**
 * Report Stripe subscriptions frozen on an unanswered 3DS authentication.
 *
 * Read only. One paginated GET with an expansion, no writes: give this a
 * RESTRICTED key with read access to Subscriptions, Invoices and PaymentIntents.
 * The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Find the PaymentIntent on an invoice across the Basil API change. Pure.
 *
 * Before 2025-03-31.basil the intent hangs off `invoice.payment_intent`. On
 * Basil and later it is reached through the invoice's `payments` collection.
 */
export function intentOf(invoice) {
  if (!invoice || typeof invoice !== 'object') return null;
  if (invoice.payment_intent && typeof invoice.payment_intent === 'object') {
    return invoice.payment_intent;
  }
  for (const payment of invoice.payments?.data ?? []) {
    const candidate = payment.payment?.payment_intent;
    if (candidate && typeof candidate === 'object') return candidate;
  }
  return null;
}

/**
 * Say why one incomplete subscription never activated. Pure.
 *
 * The subscription status is the same whichever way the first invoice failed,
 * so the answer is on the PaymentIntent behind it.
 */
export function verdict(sub) {
  if (sub.status !== 'incomplete') {
    return ['other', `status ${JSON.stringify(sub.status)}: not waiting on a first payment`];
  }

  const intent = intentOf(sub.latest_invoice);
  if (intent === null) {
    return ['unexpanded',
      'no PaymentIntent found on the first invoice: expand ' +
      'latest_invoice.payment_intent, or on 2025-03-31.basil and later read ' +
      'payments.data.payment.payment_intent'];
  }

  if (intent.status === 'requires_action') {
    const action = intent.next_action?.type;
    if (!action) {
      return ['no-next-action',
        'the intent wants authentication but nothing was prepared for the ' +
        'customer to do, so nobody can finish this one'];
    }
    return ['authentication',
      `the issuer asked for a challenge (${action}) and it was never shown to ` +
      'the customer; the payment is still live'];
  }

  if (intent.status === 'requires_payment_method') {
    const error = intent.last_payment_error ?? {};
    const code = error.decline_code ?? error.code ?? 'no code recorded';
    return ['declined',
      `the card failed (${code}): a decline, not an unanswered challenge, so ` +
      'this customer needs a different card'];
  }

  if (intent.status === 'requires_confirmation') {
    return ['unconfirmed',
      'the intent was created and never confirmed at all: the client never ' +
      'called confirm, so no bank has seen this payment'];
  }

  if (intent.status === 'processing') {
    return ['settling', 'the payment is in flight, nothing to do yet'];
  }

  return ['other',
    `payment_intent status ${JSON.stringify(intent.status)} on an incomplete subscription`];
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

async function* pageSubscriptions(key, limit) {
  let seen = 0;
  const params = {
    status: 'incomplete',
    limit: 100,
    'expand[]': 'data.latest_invoice.payment_intent',
  };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const rows = page.data ?? [];
    for (const sub of rows) { yield sub; seen += 1; }
    if (!page.has_more || rows.length === 0 || seen >= limit) break;
    params.starting_after = rows[rows.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const states = new Map();
  let scanned = 0;

  for await (const sub of pageSubscriptions(key, 1000)) {
    scanned += 1;
    const [state, detail] = verdict(sub);
    states.set(state, (states.get(state) ?? 0) + 1);
    if (state === 'authentication' || state === 'no-next-action' || state === 'unexpanded') {
      console.warn(`${state.padEnd(15)} ${sub.id ?? '?'}  ${detail}`);
    } else if (state === 'declined') {
      console.log(`${state.padEnd(15)} ${sub.id ?? '?'}  ${detail}`);
    }
  }

  if (scanned === 0) {
    console.log('no incomplete subscriptions');
    return;
  }

  const summary = [...states.entries()].sort().map(([k, n]) => `${n} ${k}`).join(', ');
  console.log(`${scanned} incomplete subscription(s): ${summary}`);

  if (states.get('unexpanded')) {
    console.warn('repair: re-run with the expansion that matches your API version; ' +
      'an unreadable row is not a healthy one');
  }

  const stuck = (states.get('authentication') ?? 0) + (states.get('no-next-action') ?? 0);
  if (!stuck) {
    console.log('nothing is waiting on an unanswered authentication');
    process.exitCode = states.get('unexpanded') ? 1 : 0;
    return;
  }

  console.warn('repair: Dashboard, Settings, Billing, Automatic collection: turn on ' +
    'reminder emails so Stripe sends the Hosted Invoice Page link when a payment ' +
    'needs authentication');
  console.warn('repair: handle invoice.payment_action_required and pass the client ' +
    'secret to stripe.handleNextAction in the signup flow');
  console.warn('note: authentication_required is a hard decline, so smart retries ' +
    'will never clear these on their own');
  process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things get pinned here. The intent has to be found on both sides of the Basil change, because a lookup that only knows one shape returns a clean account instead of an error. And an unanswered challenge has to be reported differently from a declined card, since both leave the subscription incomplete and only one of them is still collectable.",
"test_py_file": "test_stripe_sca_stuck_subs.py",
"test_py": '''from stripe_sca_stuck_subs import intent_of, verdict


def legacy(intent):
    return {"id": "sub_1", "status": "incomplete",
            "latest_invoice": {"id": "in_1", "payment_intent": intent}}


def basil(intent):
    return {"id": "sub_1", "status": "incomplete",
            "latest_invoice": {"id": "in_1",
                               "payments": {"data": [{"payment": {"payment_intent": intent}}]}}}


def test_an_unanswered_challenge_is_named_as_one():
    sub = legacy({"status": "requires_action", "next_action": {"type": "use_stripe_sdk"}})
    state, detail = verdict(sub)
    assert state == "authentication"
    assert "use_stripe_sdk" in detail
    assert "still live" in detail


def test_the_intent_is_found_on_the_basil_shape_too():
    intent = {"status": "requires_action", "next_action": {"type": "redirect_to_url"}}
    assert intent_of(basil(intent)["latest_invoice"]) == intent
    assert verdict(basil(intent))[0] == "authentication"


def test_a_declined_card_is_not_reported_as_an_authentication_problem():
    sub = legacy({"status": "requires_payment_method",
                  "last_payment_error": {"decline_code": "insufficient_funds"}})
    state, detail = verdict(sub)
    assert state == "declined"
    assert "insufficient_funds" in detail


def test_an_unreadable_invoice_is_not_a_healthy_one():
    sub = {"id": "sub_1", "status": "incomplete", "latest_invoice": "in_1"}
    state, detail = verdict(sub)
    assert state == "unexpanded"
    assert "basil" in detail


def test_requires_action_with_nothing_to_do_is_its_own_state():
    assert verdict(legacy({"status": "requires_action"}))[0] == "no-next-action"
''',
"test_js_file": "stripe-sca-stuck-subs.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { intentOf, verdict } from './stripe-sca-stuck-subs.mjs';

const legacy = (payment_intent) => ({
  id: 'sub_1', status: 'incomplete',
  latest_invoice: { id: 'in_1', payment_intent },
});

const basil = (intent) => ({
  id: 'sub_1', status: 'incomplete',
  latest_invoice: { id: 'in_1', payments: { data: [{ payment: { payment_intent: intent } }] } },
});

test('an unanswered challenge is named as one', () => {
  const [state, detail] = verdict(
    legacy({ status: 'requires_action', next_action: { type: 'use_stripe_sdk' } }));
  assert.equal(state, 'authentication');
  assert.match(detail, /use_stripe_sdk/);
  assert.match(detail, /still live/);
});

test('the intent is found on the basil shape too', () => {
  const intent = { status: 'requires_action', next_action: { type: 'redirect_to_url' } };
  assert.deepEqual(intentOf(basil(intent).latest_invoice), intent);
  assert.equal(verdict(basil(intent))[0], 'authentication');
});

test('a declined card is not reported as an authentication problem', () => {
  const [state, detail] = verdict(legacy({
    status: 'requires_payment_method',
    last_payment_error: { decline_code: 'insufficient_funds' },
  }));
  assert.equal(state, 'declined');
  assert.match(detail, /insufficient_funds/);
});

test('an unreadable invoice is not a healthy one', () => {
  const [state, detail] = verdict({ id: 'sub_1', status: 'incomplete', latest_invoice: 'in_1' });
  assert.equal(state, 'unexpanded');
  assert.match(detail, /basil/);
});

test('requires_action with nothing to do is its own state', () => {
  assert.equal(verdict(legacy({ status: 'requires_action' }))[0], 'no-next-action');
});
''',
"faq": [
 ("Why does the subscription stay incomplete instead of failing?",
  "Because nothing failed. The issuer asked for a 3D Secure challenge and is waiting for an answer, so the PaymentIntent sits at requires_action, the invoice stays open, and the subscription stays incomplete. No decline code is produced, which is why the payment never shows up in a failed-payments report."),
 ("Will Stripe's retries eventually push it through?",
  "No. authentication_required is a hard decline as far as retry logic is concerned, so attempts can be scheduled but will not clear the challenge. Nothing about a retry causes the customer's browser to display the bank's authentication screen, and that display is the only thing missing."),
 ("Why is it mostly European and Indian customers?",
  "Because those are the cards that reach the challenge. Strong Customer Authentication applies in the European Economic Area and the UK, and India mandates step-up authentication. A broken handoff is invisible on traffic that authorizes without a challenge, so the failure looks like a regional conversion problem rather than a bug."),
 ("My expansion returns nothing. Did the field move?",
  "Yes. Before API version 2025-03-31.basil the intent is at latest_invoice.payment_intent. On Basil and later it is reached through the invoice's payments collection. A script written for one version reads every row on the other as unexpanded, so check for that before concluding the account is clean."),
 ("Can I rescue the ones that are already stuck?",
  "Often, yes, while the invoice is still open. Turning on automatic collection reminders makes Stripe email the customer a Hosted Invoice Page link where the challenge can be completed and the payment finished. Do that first, then fix the handoff so the next signup never reaches this state."),
],
"related": [
 ("/stripe/abandoned-requires-action-intents/", "3DS handoff breaks and requires_action intents pile up"),
 ("/stripe/subscriptions-stuck-incomplete/", "Incomplete subscriptions die silently after 23 hours"),
 ("/stripe/off-session-authentication-required-declines/", "Off-session charges die on authentication_required"),
],
"citations": [CITE_3DS, CITE_SUB_OVERVIEW, CITE_INVOICE_WORKFLOW, CITE_SMART_RETRIES],
},

]
