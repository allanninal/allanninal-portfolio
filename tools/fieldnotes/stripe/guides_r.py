#!/usr/bin/env python3
"""/stripe/ field notes, batch R — the two legacy card paths, expiring
authorization holds, and bank debits parked in processing.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

Two of these four are about an integration that half-moved to the modern API and
left the other half where it was: charges created without a PaymentIntent, and
cards saved under `customer.sources` instead of as PaymentMethods. The other two
are about time — an authorization that expires on the network's clock rather than
yours, and an ACH debit whose `processing` state is legitimate right up until it
is not.
"""

CITE_OLDER_APIS = ("Older payments APIs — Stripe Docs",
                   "https://docs.stripe.com/payments/older-apis")
CITE_SCA = ("Strong Customer Authentication — Stripe Docs",
            "https://docs.stripe.com/strong-customer-authentication")
CITE_CHARGE_OBJ = ("The charge object — Stripe API reference",
                   "https://docs.stripe.com/api/charges/object")
CITE_DECLINE_CODES = ("Decline codes — Stripe Docs",
                      "https://docs.stripe.com/declines/codes")
CITE_SOURCES = ("Sources — Stripe Docs", "https://docs.stripe.com/sources")
CITE_CUSTOMER_OBJ = ("The customer object — Stripe API reference",
                     "https://docs.stripe.com/api/customers/object")
CITE_PM_LIST = ("List a customer's PaymentMethods — Stripe API reference",
                "https://docs.stripe.com/api/payment_methods/list")
CITE_HOLD = ("Place a hold on a payment method — Stripe Docs",
             "https://docs.stripe.com/payments/place-a-hold-on-a-payment-method")
CITE_PI_OBJ = ("The PaymentIntent object — Stripe API reference",
               "https://docs.stripe.com/api/payment_intents/object")
CITE_ERROR_CODES = ("Error codes — Stripe Docs",
                    "https://docs.stripe.com/error-codes")
CITE_REFUND_OBJ = ("The refund object — Stripe API reference",
                   "https://docs.stripe.com/api/refunds/object")
CITE_LIFECYCLE = ("The PaymentIntent lifecycle — Stripe Docs",
                  "https://docs.stripe.com/payments/paymentintents/lifecycle")
CITE_ACH = ("ACH Direct Debit — Stripe Docs",
            "https://docs.stripe.com/payments/ach-direct-debit")
CITE_SEPA = ("SEPA Direct Debit — Stripe Docs",
             "https://docs.stripe.com/payments/sepa-debit")

GUIDES = [

{
"slug": "legacy-charges-api-no-payment-intent",
"title": "Charges have a null payment_intent: the legacy Charges API",
"description": "European decline rates run above the account average and 3D Secure never appears. The charges were made by an API call that cannot ask for it.",
"h1": "charges have a null payment_intent, which means the legacy Charges API",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe charges api payment_intent null", "stripe legacy charges api",
             "stripe authentication_required decline", "stripe sca declines",
             "migrate charges to payment intents"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "European card volume declines at two or three times the rate of everything else, and nobody can find a cause. The cards are good. Radar is not blocking them. And 3D Secure never appears &mdash; not on a single one of these payments, ever, on any card from any issuer. That last detail is the whole diagnosis.",
"short_answer": """<p>Paginate <code>GET /v1/charges</code> and count the charges whose <code>payment_intent</code> is null. Those were created by <code>POST /v1/charges</code> with a token or a source. That API predates SCA and has no way to run 3D Secure, so an issuer that requires authentication has nothing to accept and declines.</p>
<p>Then measure the damage rather than the count. Inside that same subset, count <code>outcome.reason == "authentication_required"</code> and compare the decline rate against the charges that <em>do</em> carry a PaymentIntent id. The gap between those two numbers is what the legacy path costs you per month.</p>""",
"problem": """<p>Nothing about this looks like a bug. The code works, has worked for years, and still succeeds for most of your customers. Cards from the United States clear normally, because their issuers rarely demand authentication. The failures cluster in Europe, India and the UK, which reads to most teams as a fraud pattern or a bad BIN range rather than as a missing capability.</p>
<p>It is also invisible in the place people look first. The Dashboard shows a payment, an amount and a decline, and the decline message is the issuer's, not Stripe's. There is no warning banner on a charge saying that the API used to create it cannot authenticate. The only visible tell is a field that is null, and a null field is exactly the kind of thing an eye slides over.</p>""",
"why": """<p><strong>The Charges API cannot perform 3D Secure at all.</strong> Authentication is a step in the PaymentIntent lifecycle: the intent moves to <code>requires_action</code>, the client completes the challenge, the intent is confirmed. A direct charge has no such state. When the issuer says authenticate, the only thing the legacy path can do is fail, and it fails with <code>outcome.reason</code> of <code>authentication_required</code>.</p>
<p><strong>Retrying makes it worse, not better.</strong> The natural reaction to a decline is to try again, and a retry on the same source declines identically because nothing about the second attempt can authenticate either. Teams then add a backoff, which turns one decline into four, which is visible to the issuer as repeated failed attempts against the same card.</p>
<p><strong>Half-migrated is the normal state.</strong> Almost nobody is entirely on the old API. Checkout was moved to PaymentIntents years ago; a renewal job, an admin "charge this customer" button and an internal reconciliation script were not, because they worked. So the legacy cohort is small, specific and easy to overlook, and it is usually the recurring one &mdash; the payments that matter most.</p>
<p><strong>A null <code>payment_intent</code> is the cleanest signal you will get.</strong> Every charge created through a PaymentIntent carries that id, including ones created by invoices, subscriptions and Checkout. So the null set is not a proxy for the legacy path; it <em>is</em> the legacy path, countable in one paginated read.</p>""",
"steps": [
 {"h": "Count the null-payment_intent charges, not the failures",
  "body": """<p>Start with exposure rather than symptoms. Page <code>GET /v1/charges</code> over the last 90 days and count where <code>payment_intent</code> is null, as a share of all charges and as a sum of <code>amount</code>. That number tells you how much traffic is on a path that cannot authenticate, whether or not it has bitten yet.</p>"""},
 {"h": "Treat an absent key the same as an explicit null",
  "body": """<p>Depending on the API version and the expansion you asked for, the field can come back as <code>null</code> or not come back at all. A check written as <code>if charge.payment_intent is None</code> catches both; one written as <code>if "payment_intent" in charge</code> catches neither reliably.</p>"""},
 {"h": "Separate authentication_required from every other decline",
  "body": """<p><code>outcome.reason == "authentication_required"</code> is the decline that proves the diagnosis. Other declines &mdash; <code>insufficient_funds</code>, <code>card_declined</code> &mdash; would have happened on the modern path too and are not evidence of anything. Report them separately or you will overstate the problem and get argued out of the migration.</p>"""},
 {"h": "Compare the two cohorts before writing the ticket",
  "body": """<p>The persuasive number is a ratio, not a count: the decline rate among null-<code>payment_intent</code> charges against the decline rate among the rest, over the same window and the same currencies. A legacy path declining at 9% against a modern path at 3% is a migration; the same path declining at 3.1% is a cleanup task for next quarter.</p>"""},
 {"h": "Check the companion signal on the customers",
  "body": """<p>Integrations on the legacy charge path usually store cards the legacy way too, under <code>customer.sources</code>. Those cards have to be dealt with before or during the cutover, because a PaymentIntent will not accept a <code>card_</code> id where it expects a <code>pm_</code> one.</p>"""},
],
"verify": """<p>Re-run the script over the same window. The legacy count should be falling towards zero as call sites move across, and the <code>authentication_required</code> count should reach zero first, because the migrated paths can authenticate.</p>
<pre><code class="language-bash">python3 stripe_legacy_charges.py --days 90
# 18,204 charge(s): 18,204 modern, 0 legacy, 0 declined for authentication</code></pre>""",
"code_intro": "One paginated GET over <code>/v1/charges</code> and nothing else &mdash; a restricted key with read access to Charges is enough. The classifier is pure and takes a single charge, so the difference between <em>this was going to decline anyway</em> and <em>this declined because the API cannot authenticate</em> is a rule you can read rather than an aggregate you have to trust.",
"py_file": "stripe_legacy_charges.py",
"py": '''"""Report Stripe charges created without a PaymentIntent, and what it costs.

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
log = logging.getLogger("stripe_legacy_charges")

API = "https://api.stripe.com/v1"


def classify(charge):
    """Sort one charge by the API that created it and by what the issuer did.

    Pure, so the rules can be tested without a network.

    A charge created through a PaymentIntent carries that intent's id, whatever
    made it: Checkout, an invoice, a subscription renewal, a direct confirm. A
    null or absent `payment_intent` therefore is not a proxy for the legacy
    Charges API, it is the legacy Charges API.

    Returns (state, detail).
    """
    if charge.get("payment_intent"):
        return ("modern", "created through a PaymentIntent")

    status = charge.get("status")
    outcome = charge.get("outcome") or {}
    reason = outcome.get("reason")

    if status == "succeeded":
        return ("legacy",
                "succeeded on the legacy Charges API: no 3D Secure was possible "
                "on this payment, and none was attempted")

    if reason == "authentication_required":
        return ("unauthenticated",
                "declined for authentication_required: the Charges API cannot "
                "run 3D Secure, so retrying the same source declines again")

    if status == "failed":
        return ("legacy_declined",
                "legacy charge declined (%s): this one would likely have failed "
                "on the modern path too" % (reason or "no outcome.reason"))

    if status == "pending":
        return ("legacy_pending",
                "legacy charge still pending: an asynchronous method on an API "
                "with no intent to track it")

    return ("unknown", "unrecognised charge status: %r" % (status,))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def charges(session, since, cap):
    """Yield charges newest first, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/charges", **params)
        data = page.get("data", [])
        for ch in data:
            yield ch
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to read charges")
    ap.add_argument("--max-charges", type=int, default=20000,
                    help="stop paginating after this many charges")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    counts, amounts = {}, {}
    scanned = 0
    for ch in charges(s, since, args.max_charges):
        scanned += 1
        state, detail = classify(ch)
        counts[state] = counts.get(state, 0) + 1
        amounts[state] = amounts.get(state, 0) + (ch.get("amount") or 0)
        if state in ("unauthenticated", "unknown"):
            log.warning("%s  %-15s %s", ch.get("id", "ch_?"), state, detail)

    legacy_states = ("legacy", "unauthenticated", "legacy_declined", "legacy_pending")
    legacy = sum(counts.get(k, 0) for k in legacy_states)
    blocked = counts.get("unauthenticated", 0)

    log.info("%d charge(s): %d modern, %d legacy, %d declined for authentication",
             scanned, counts.get("modern", 0), legacy, blocked)

    if legacy and scanned:
        log.warning("  %.1f%% of charges have no PaymentIntent, %d minor unit(s) "
                    "of volume on an API that cannot authenticate",
                    100.0 * legacy / scanned,
                    sum(amounts.get(k, 0) for k in legacy_states))
    if blocked:
        log.warning("  %d of those were declined for authentication_required. "
                    "A retry on the same source declines again.", blocked)
    if legacy:
        log.warning("  repair: replace POST %s/charges -d source=tok_... with", API)
        log.warning("  POST %s/payment_intents -d amount=... -d currency=... "
                    "-d customer=cus_... -d payment_method=pm_... -d confirm=true", API)
        log.warning("  and handle requires_action on the client. Convert stored "
                    "card_ sources to PaymentMethods before cutting over.")
    return 1 if legacy else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-legacy-charges.mjs",
"js": '''/**
 * Report Stripe charges created without a PaymentIntent, and what it costs.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Charges. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Sort one charge by the API that created it and by what the issuer did. Pure,
 * so the rules can be tested without a network.
 *
 * A charge created through a PaymentIntent carries that intent's id, whatever
 * made it. A null or absent payment_intent is the legacy Charges API itself,
 * not a proxy for it. Returns [state, detail].
 */
export function classify(charge) {
  if (charge.payment_intent) return ['modern', 'created through a PaymentIntent'];

  const status = charge.status;
  const outcome = charge.outcome ?? {};
  const reason = outcome.reason ?? null;

  if (status === 'succeeded') {
    return ['legacy',
      'succeeded on the legacy Charges API: no 3D Secure was possible on this ' +
      'payment, and none was attempted'];
  }

  if (reason === 'authentication_required') {
    return ['unauthenticated',
      'declined for authentication_required: the Charges API cannot run 3D ' +
      'Secure, so retrying the same source declines again'];
  }

  if (status === 'failed') {
    return ['legacy_declined',
      `legacy charge declined (${reason ?? 'no outcome.reason'}): this one ` +
      'would likely have failed on the modern path too'];
  }

  if (status === 'pending') {
    return ['legacy_pending',
      'legacy charge still pending: an asynchronous method on an API with no ' +
      'intent to track it'];
  }

  return ['unknown', `unrecognised charge status: ${JSON.stringify(status)}`];
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

export async function* charges(key, since, cap = 20000) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/charges', params);
    const data = page.data ?? [];
    for (const ch of data) {
      yield ch;
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

  const days = Number(process.env.DAYS ?? 90);
  const since = Math.floor(Date.now() / 1000) - days * 86400;

  const counts = {};
  const amounts = {};
  let scanned = 0;
  for await (const ch of charges(key, since)) {
    scanned += 1;
    const [state, detail] = classify(ch);
    counts[state] = (counts[state] ?? 0) + 1;
    amounts[state] = (amounts[state] ?? 0) + (ch.amount ?? 0);
    if (state === 'unauthenticated' || state === 'unknown') {
      console.warn(`${ch.id ?? 'ch_?'}  ${state.padEnd(15)} ${detail}`);
    }
  }

  const legacyStates = ['legacy', 'unauthenticated', 'legacy_declined', 'legacy_pending'];
  const legacy = legacyStates.reduce((n, k) => n + (counts[k] ?? 0), 0);
  const blocked = counts.unauthenticated ?? 0;

  console.log(`${scanned} charge(s): ${counts.modern ?? 0} modern, ${legacy} ` +
              `legacy, ${blocked} declined for authentication`);

  if (legacy && scanned) {
    const volume = legacyStates.reduce((n, k) => n + (amounts[k] ?? 0), 0);
    console.warn(`  ${(100 * legacy / scanned).toFixed(1)}% of charges have no ` +
                 `PaymentIntent, ${volume} minor unit(s) of volume on an API ` +
                 'that cannot authenticate');
  }
  if (blocked) {
    console.warn(`  ${blocked} of those were declined for authentication_required. ` +
                 'A retry on the same source declines again.');
  }
  if (legacy) {
    console.warn(`  repair: replace POST ${API}/charges -d source=tok_... with`);
    console.warn(`  POST ${API}/payment_intents -d amount=... -d currency=... ` +
                 '-d customer=cus_... -d payment_method=pm_... -d confirm=true');
    console.warn('  and handle requires_action on the client. Convert stored ' +
                 'card_ sources to PaymentMethods before cutting over.');
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
"test_intro": "Two cases carry the note. A charge with no <code>payment_intent</code> key at all has to sort as legacy rather than modern, because the field is sometimes absent rather than null and the wrong test reports a clean account. And an <code>authentication_required</code> decline has to be its own state, separate from an ordinary decline, because only one of the two is caused by the API you are using.",
"test_py_file": "test_stripe_legacy_charges.py",
"test_py": '''from stripe_legacy_charges import classify


def test_charge_with_an_intent_is_modern():
    state, _ = classify({"payment_intent": "pi_123", "status": "succeeded"})
    assert state == "modern"


def test_absent_payment_intent_key_is_legacy_not_modern():
    # The field is sometimes absent rather than null. A membership test would
    # report a clean account here.
    state, detail = classify({"status": "succeeded"})
    assert state == "legacy"
    assert "3D Secure" in detail


def test_authentication_required_is_its_own_state():
    state, detail = classify({
        "payment_intent": None,
        "status": "failed",
        "outcome": {"type": "issuer_declined", "reason": "authentication_required"},
    })
    assert state == "unauthenticated"
    assert "declines again" in detail


def test_ordinary_decline_is_not_blamed_on_the_legacy_api():
    state, detail = classify({
        "payment_intent": None,
        "status": "failed",
        "outcome": {"type": "issuer_declined", "reason": "insufficient_funds"},
    })
    assert state == "legacy_declined"
    assert "insufficient_funds" in detail


def test_unrecognised_status_is_not_silently_counted_as_modern():
    state, _ = classify({"payment_intent": None, "status": "reversed"})
    assert state == "unknown"
''',
"test_js_file": "stripe-legacy-charges.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-legacy-charges.mjs';

test('charge with an intent is modern', () => {
  assert.equal(classify({ payment_intent: 'pi_123', status: 'succeeded' })[0], 'modern');
});

test('absent payment_intent key is legacy, not modern', () => {
  const [state, detail] = classify({ status: 'succeeded' });
  assert.equal(state, 'legacy');
  assert.match(detail, /3D Secure/);
});

test('authentication_required is its own state', () => {
  const [state, detail] = classify({
    payment_intent: null,
    status: 'failed',
    outcome: { type: 'issuer_declined', reason: 'authentication_required' },
  });
  assert.equal(state, 'unauthenticated');
  assert.match(detail, /declines again/);
});

test('an ordinary decline is not blamed on the legacy API', () => {
  const [state, detail] = classify({
    payment_intent: null,
    status: 'failed',
    outcome: { type: 'issuer_declined', reason: 'insufficient_funds' },
  });
  assert.equal(state, 'legacy_declined');
  assert.match(detail, /insufficient_funds/);
});

test('unrecognised status is not silently counted as modern', () => {
  assert.equal(classify({ payment_intent: null, status: 'reversed' })[0], 'unknown');
});
''',
"faq": [
 ("Does a null payment_intent always mean the legacy Charges API?",
  "In practice yes. Every charge created through a PaymentIntent carries that intent's id, including charges made by Checkout, invoices and subscription renewals. So the null set is the set of charges created by POST /v1/charges with a token or a source, which is the API that predates SCA."),
 ("Why do only European cards decline?",
  "Because SCA is enforced by the issuer, and European, UK and Indian issuers enforce it. A US issuer that never asks for authentication is perfectly happy with a legacy charge, so the same code path succeeds there and fails in Europe, which is why this reads as a regional fraud pattern rather than an API problem."),
 ("Can I retry an authentication_required decline?",
  "Not usefully. The retry runs through the same API, which still cannot present a 3D Secure challenge, so the issuer declines it for the same reason. The only fix is to create a PaymentIntent and handle requires_action on the client."),
 ("Do I have to migrate the stored cards at the same time?",
  "You have to migrate them before the cutover. A PaymentIntent expects a pm_ id, and a card saved the old way is a card_ or src_ under customer.sources. Convert them to PaymentMethods first, or the migrated code path fails on customers it has always been able to charge."),
 ("Is the Charges API deprecated?",
  "Stripe still accepts the calls, and that is the problem: nothing breaks loudly. Stripe's own guidance is that integrations still on it can see high decline rates from banks that enforce SCA, which is a slow revenue leak rather than an outage."),
],
"related": [
 ("/stripe/legacy-card-sources-still-attached/", "Legacy card sources still live under customer.sources"),
 ("/stripe/off-session-authentication-required-declines/", "Off-session charges die on authentication_required"),
 ("/stripe/abandoned-requires-action-intents/", "3DS handoff breaks and requires_action intents pile up"),
],
"citations": [CITE_OLDER_APIS, CITE_SCA, CITE_CHARGE_OBJ, CITE_DECLINE_CODES],
},

{
"slug": "legacy-card-sources-still-attached",
"title": "Legacy card sources still live under customer.sources",
"description": "Some customers charge fine and others fail with no active card. Two parallel card stores exist on the same account and each code path can see one.",
"h1": "legacy card sources still live under customer.sources",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe customer sources card_", "stripe default_source vs default_payment_method",
             "cannot charge a customer that has no active card",
             "stripe migrate sources to payment methods", "stripe legacy card store"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Half your customers renew without incident. The other half fail with <code>Cannot charge a customer that has no active card</code>, and when you open one of them in the Dashboard there is a card sitting right there. Both statements are true. The card is in a store the code that renews them cannot see.",
"short_answer": """<p>For each customer, read <code>GET /v1/customers/{id}/sources?object=card</code> and <code>GET /v1/payment_methods?customer={id}&amp;type=card</code>. Cards saved before the PaymentMethods API live in the first list as <code>card_</code> or <code>src_</code> objects and are invisible to the second.</p>
<p>The sharpest signal is the split: <code>customer.default_source</code> set while <code>customer.invoice_settings.default_payment_method</code> is null and the PaymentMethods list is empty. That customer has a usable card and every modern code path reports them as having none.</p>""",
"problem": """<p>What makes this expensive is that it fails per customer rather than per deploy. The renewal job runs, most customers charge, a subset throws, and the error is one that sounds like a customer problem: no active card. Support tells the customer to re-enter their card. Some of them do, which quietly fixes that one row and removes the evidence, and the rest churn.</p>
<p>The error messages compound the confusion because they name ids that look right. <code>Customer cus_... does not have a linked card with ID ...</code> is Stripe saying the id you passed is in the other store, not that the customer has nothing. So the id is real, the customer is real, the card is real, and the call still fails.</p>""",
"why": """<p><strong>There are genuinely two card stores.</strong> <code>customer.sources</code> holds the old objects and is reached through <code>/v1/customers/{id}/sources</code>. PaymentMethods are a separate collection reached through <code>/v1/payment_methods</code>. A card in one does not appear in the other, and no field on the customer tells you that the other store is where everything lives.</p>
<p><strong>Billing falls back in a way that hides the problem for months.</strong> When <code>invoice_settings.default_payment_method</code> is null, subscription invoices fall back to <code>customer.default_source</code>. So an account that never migrated renews perfectly, and only the customers touched by newer code &mdash; who got a PaymentMethod and therefore stopped falling back &mdash; behave differently. The half-migrated account is less consistent than either extreme.</p>
<p><strong>A legacy source carries no SCA mandate.</strong> These objects predate authentication, so even where they charge, they charge on the path that cannot authenticate. Converting them is not only tidying: it is what earns the off-session mandate that European renewals need.</p>
<p><strong>The migration is per customer, and the failures are per customer.</strong> There is no account-level switch. Every customer is in one of a handful of states &mdash; modern only, legacy only, both, neither &mdash; and each state has a different repair. A script that reports one number cannot tell you which repair to run, which is why the classifier here returns a state rather than a boolean.</p>""",
"steps": [
 {"h": "Read both stores for the same customer",
  "body": """<p>One call to <code>/v1/customers/{id}/sources?object=card</code> and one to <code>/v1/payment_methods?customer={id}&amp;type=card</code>. Two customers can produce identical Dashboard pages and different results here, and the pair of answers is the only thing that distinguishes them.</p>"""},
 {"h": "Read both defaults too",
  "body": """<p><code>default_source</code> and <code>invoice_settings.default_payment_method</code> are separate fields with separate meanings. Which one is populated decides what Billing will use on the next renewal, so a customer with cards in both stores and no <code>default_payment_method</code> is still being charged the old way.</p>"""},
 {"h": "Find the customers with no card at all",
  "body": """<p>Empty in both stores is a different problem with the same error message. Those customers cannot be migrated, only asked &mdash; usually through a SetupIntent, which also collects the mandate.</p>"""},
 {"h": "Migrate, then set the modern default, then delete",
  "body": """<p>In that order. Setting <code>invoice_settings[default_payment_method]</code> before the PaymentMethod exists fails; deleting the source before the default is moved leaves the customer with nothing chargeable between the two calls.</p>"""},
 {"h": "Stop reading default_source anywhere in the billing path",
  "body": """<p>Until that field is out of your code, a customer created by an old path can still end up with a legacy default, and the cohort refills behind you. The check is cheap enough to run weekly and prove the number stays at zero.</p>"""},
],
"verify": """<p>Re-run the script. Every customer should report <code>modern</code>, with no split defaults and no legacy-only rows left.</p>
<pre><code class="language-bash">python3 stripe_legacy_card_sources.py
# 3,141 customer(s): 3,141 modern, 0 legacy-only, 0 split, 0 cardless</code></pre>""",
"code_intro": "One paginated GET over the customers, then one or two small GETs per customer &mdash; a restricted key with read access to Customers and PaymentMethods covers all of it. The second call is skipped where a customer already has a modern default and no legacy sources, because that is the majority and it is the only place the cost of this script lives.",
"py_file": "stripe_legacy_card_sources.py",
"py": '''"""Report Stripe customers whose cards are still in the legacy sources store.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Customers and PaymentMethods. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_legacy_card_sources")

API = "https://api.stripe.com/v1"

# Cards saved before the PaymentMethods API. `src_` covers the Sources API that
# briefly sat between the two; both live under customer.sources and neither is
# visible to GET /v1/payment_methods.
LEGACY_PREFIXES = ("card_", "src_")


def classify(customer, sources, payment_methods):
    """Sort one customer by which card store actually holds their card.

    Pure, so the states can be tested without a network. `sources` is the data
    array from GET /v1/customers/{id}/sources?object=card and `payment_methods`
    the data array from GET /v1/payment_methods?customer={id}&type=card.

    Returns (state, detail).
    """
    legacy = [s for s in (sources or [])
              if str(s.get("id", "")).startswith(LEGACY_PREFIXES)]
    modern = list(payment_methods or [])
    default_source = customer.get("default_source")
    default_pm = (customer.get("invoice_settings") or {}).get("default_payment_method")

    if not legacy and modern:
        if not default_pm:
            return ("no_default",
                    "%d PaymentMethod(s) and no invoice_settings."
                    "default_payment_method: Billing has nothing to fall back to"
                    % len(modern))
        return ("modern", "%d PaymentMethod(s), modern default set" % len(modern))

    if not legacy and not modern:
        return ("cardless",
                "no card in either store: this is the other cause of "
                "'cannot charge a customer that has no active card'")

    if legacy and not modern:
        if default_source:
            return ("split_brain",
                    "%d legacy source(s) and default_source set, but no "
                    "PaymentMethod at all: every modern code path sees this "
                    "customer as having no card" % len(legacy))
        return ("legacy_only",
                "%d legacy source(s) and no PaymentMethod: charged only by code "
                "that still reads customer.sources" % len(legacy))

    if not default_pm:
        return ("split_default",
                "%d legacy source(s) alongside %d PaymentMethod(s), but "
                "default_payment_method is null: Billing falls back to "
                "default_source and renews on the legacy card"
                % (len(legacy), len(modern)))

    return ("residue",
            "%d legacy source(s) left behind a completed migration: the modern "
            "default is set, so these are safe to remove" % len(legacy))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def customers(session, cap):
    """Yield customers, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/customers", **params)
        data = page.get("data", [])
        for cust in data:
            yield cust
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-customers", type=int, default=5000,
                    help="stop paginating after this many customers")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    counts = {}
    scanned = 0
    for cust in customers(s, args.max_customers):
        scanned += 1
        cid = cust.get("id", "")
        srcs = get(s, "/customers/%s/sources" % cid,
                   object="card", limit=100).get("data", [])

        # Skip the second call for the healthy majority: a customer with no
        # legacy source and a modern default is already migrated, and the
        # PaymentMethod list cannot change that answer.
        default_pm = (cust.get("invoice_settings") or {}).get("default_payment_method")
        pms = []
        if srcs or not default_pm:
            pms = get(s, "/payment_methods",
                      customer=cid, type="card", limit=100).get("data", [])

        state, detail = classify(cust, srcs, pms)
        counts[state] = counts.get(state, 0) + 1
        if state != "modern":
            log.warning("%s  %-14s %s", cid or "cus_?", state, detail)

    split = counts.get("split_brain", 0) + counts.get("split_default", 0)
    legacy_only = counts.get("legacy_only", 0)
    cardless = counts.get("cardless", 0)

    log.info("%d customer(s): %d modern, %d legacy-only, %d split, %d cardless",
             scanned, counts.get("modern", 0), legacy_only, split, cardless)

    if legacy_only or split or counts.get("residue"):
        log.warning("  repair, in this order, per customer:")
        log.warning("  1. create a PaymentMethod from the legacy card, or send "
                    "the customer through a SetupIntent to re-add it")
        log.warning("  2. POST %s/customers/{id} with "
                    "invoice_settings[default_payment_method]=pm_...", API)
        log.warning("  3. only then remove the old object at "
                    "%s/customers/{id}/sources/{card_id}", API)
    if cardless:
        log.warning("  %d customer(s) have no card in either store: a SetupIntent "
                    "is the only repair, and it collects the mandate too", cardless)
    bad = scanned - counts.get("modern", 0)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-legacy-card-sources.mjs",
"js": '''/**
 * Report Stripe customers whose cards are still in the legacy sources store.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Customers and PaymentMethods. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Cards saved before the PaymentMethods API. `src_` covers the Sources API that
// briefly sat between the two; neither is visible to GET /v1/payment_methods.
const LEGACY_PREFIXES = ['card_', 'src_'];

/**
 * Sort one customer by which card store actually holds their card. Pure, so the
 * states can be tested without a network. Returns [state, detail].
 */
export function classify(customer, sources, paymentMethods) {
  const legacy = (sources ?? []).filter(
    (s) => LEGACY_PREFIXES.some((p) => String(s.id ?? '').startsWith(p)));
  const modern = paymentMethods ?? [];
  const defaultSource = customer.default_source ?? null;
  const defaultPm = (customer.invoice_settings ?? {}).default_payment_method ?? null;

  if (legacy.length === 0 && modern.length > 0) {
    if (!defaultPm) {
      return ['no_default',
        `${modern.length} PaymentMethod(s) and no invoice_settings.` +
        'default_payment_method: Billing has nothing to fall back to'];
    }
    return ['modern', `${modern.length} PaymentMethod(s), modern default set`];
  }

  if (legacy.length === 0 && modern.length === 0) {
    return ['cardless',
      "no card in either store: this is the other cause of 'cannot charge a " +
      "customer that has no active card'"];
  }

  if (modern.length === 0) {
    if (defaultSource) {
      return ['split_brain',
        `${legacy.length} legacy source(s) and default_source set, but no ` +
        'PaymentMethod at all: every modern code path sees this customer as ' +
        'having no card'];
    }
    return ['legacy_only',
      `${legacy.length} legacy source(s) and no PaymentMethod: charged only by ` +
      'code that still reads customer.sources'];
  }

  if (!defaultPm) {
    return ['split_default',
      `${legacy.length} legacy source(s) alongside ${modern.length} ` +
      'PaymentMethod(s), but default_payment_method is null: Billing falls back ' +
      'to default_source and renews on the legacy card'];
  }

  return ['residue',
    `${legacy.length} legacy source(s) left behind a completed migration: the ` +
    'modern default is set, so these are safe to remove'];
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

export async function* customers(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/customers', params);
    const data = page.data ?? [];
    for (const cust of data) {
      yield cust;
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

  const counts = {};
  let scanned = 0;
  for await (const cust of customers(key)) {
    scanned += 1;
    const srcs = (await get(key, `/customers/${cust.id}/sources`,
                            { object: 'card', limit: 100 })).data ?? [];

    // Skip the second call for the healthy majority: no legacy source plus a
    // modern default is already migrated, whatever the PaymentMethod list says.
    const defaultPm = (cust.invoice_settings ?? {}).default_payment_method ?? null;
    let pms = [];
    if (srcs.length || !defaultPm) {
      pms = (await get(key, '/payment_methods',
                       { customer: cust.id, type: 'card', limit: 100 })).data ?? [];
    }

    const [state, detail] = classify(cust, srcs, pms);
    counts[state] = (counts[state] ?? 0) + 1;
    if (state !== 'modern') {
      console.warn(`${cust.id ?? 'cus_?'}  ${state.padEnd(14)} ${detail}`);
    }
  }

  const split = (counts.split_brain ?? 0) + (counts.split_default ?? 0);
  const legacyOnly = counts.legacy_only ?? 0;
  const cardless = counts.cardless ?? 0;

  console.log(`${scanned} customer(s): ${counts.modern ?? 0} modern, ` +
              `${legacyOnly} legacy-only, ${split} split, ${cardless} cardless`);

  if (legacyOnly || split || counts.residue) {
    console.warn('  repair, in this order, per customer:');
    console.warn('  1. create a PaymentMethod from the legacy card, or send the ' +
                 'customer through a SetupIntent to re-add it');
    console.warn(`  2. POST ${API}/customers/{id} with ` +
                 'invoice_settings[default_payment_method]=pm_...');
    console.warn(`  3. only then remove the old object at ` +
                 `${API}/customers/{id}/sources/{card_id}`);
  }
  if (cardless) {
    console.warn(`  ${cardless} customer(s) have no card in either store: a ` +
                 'SetupIntent is the only repair, and it collects the mandate too');
  }
  if (scanned - (counts.modern ?? 0)) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The state worth pinning is the split default: cards in both stores, no <code>default_payment_method</code>, which means Billing quietly renews on the legacy card even though the migration looks finished. A check that only asks <em>does this customer have a PaymentMethod</em> reports that customer as done, and the renewal still cannot authenticate.",
"test_py_file": "test_stripe_legacy_card_sources.py",
"test_py": '''from stripe_legacy_card_sources import classify

MODERN_DEFAULT = {"invoice_settings": {"default_payment_method": "pm_1"}}


def test_migrated_customer_is_modern():
    state, _ = classify(MODERN_DEFAULT, [], [{"id": "pm_1"}])
    assert state == "modern"


def test_legacy_card_with_no_payment_method_is_the_split_brain_case():
    cust = {"default_source": "card_1", "invoice_settings": {}}
    state, detail = classify(cust, [{"id": "card_1"}], [])
    assert state == "split_brain"
    assert "no card" in detail


def test_src_objects_count_as_legacy_too():
    cust = {"default_source": "src_1", "invoice_settings": {}}
    assert classify(cust, [{"id": "src_1"}], [])[0] == "split_brain"


def test_both_stores_with_no_modern_default_still_renews_on_the_old_card():
    cust = {"default_source": "card_1", "invoice_settings": {}}
    state, detail = classify(cust, [{"id": "card_1"}], [{"id": "pm_1"}])
    assert state == "split_default"
    assert "falls back" in detail


def test_both_stores_with_a_modern_default_is_only_residue():
    state, _ = classify(MODERN_DEFAULT, [{"id": "card_1"}], [{"id": "pm_1"}])
    assert state == "residue"


def test_no_card_anywhere_is_its_own_state():
    state, _ = classify({"invoice_settings": {}}, [], [])
    assert state == "cardless"
''',
"test_js_file": "stripe-legacy-card-sources.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-legacy-card-sources.mjs';

const MODERN_DEFAULT = { invoice_settings: { default_payment_method: 'pm_1' } };

test('migrated customer is modern', () => {
  assert.equal(classify(MODERN_DEFAULT, [], [{ id: 'pm_1' }])[0], 'modern');
});

test('legacy card with no PaymentMethod is the split-brain case', () => {
  const cust = { default_source: 'card_1', invoice_settings: {} };
  const [state, detail] = classify(cust, [{ id: 'card_1' }], []);
  assert.equal(state, 'split_brain');
  assert.match(detail, /no card/);
});

test('src objects count as legacy too', () => {
  const cust = { default_source: 'src_1', invoice_settings: {} };
  assert.equal(classify(cust, [{ id: 'src_1' }], [])[0], 'split_brain');
});

test('both stores with no modern default still renews on the old card', () => {
  const cust = { default_source: 'card_1', invoice_settings: {} };
  const [state, detail] = classify(cust, [{ id: 'card_1' }], [{ id: 'pm_1' }]);
  assert.equal(state, 'split_default');
  assert.match(detail, /falls back/);
});

test('both stores with a modern default is only residue', () => {
  assert.equal(
    classify(MODERN_DEFAULT, [{ id: 'card_1' }], [{ id: 'pm_1' }])[0], 'residue');
});

test('no card anywhere is its own state', () => {
  assert.equal(classify({ invoice_settings: {} }, [], [])[0], 'cardless');
});
''',
"faq": [
 ("Why does GET /v1/payment_methods return nothing when the Dashboard shows a card?",
  "Because the card is in the other store. Cards saved before the PaymentMethods API are card_ or src_ objects under customer.sources, reached through /v1/customers/{id}/sources. The Dashboard renders both stores on one page; the API does not."),
 ("What does 'Cannot charge a customer that has no active card' actually mean?",
  "That the store your call reads is empty. It has two causes with the same wording: the customer genuinely has no card anywhere, or the card is a legacy source and the call is looking for a PaymentMethod. The classifier keeps them apart because only one of the two can be repaired without asking the customer."),
 ("Which default does a subscription renewal use?",
  "invoice_settings.default_payment_method if it is set, and customer.default_source if it is not. That fallback is why a half-migrated account keeps renewing on legacy cards long after the new code has shipped."),
 ("Can I convert a legacy source into a PaymentMethod?",
  "Often yes, and where it is not possible the alternative is a SetupIntent that asks the customer to re-add the card. The SetupIntent route is slower but earns an SCA mandate, which the legacy object never had."),
 ("What order should the migration run in?",
  "Create or convert the PaymentMethod, set invoice_settings[default_payment_method], and only then remove the old source. Reversing the last two steps leaves the customer with no chargeable card in the gap between the calls."),
],
"related": [
 ("/stripe/legacy-charges-api-no-payment-intent/", "Charges have a null payment_intent: the legacy Charges API"),
 ("/stripe/expired-saved-cards-attached/", "Saved cards are already expired but still attached"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
],
"citations": [CITE_SOURCES, CITE_CUSTOMER_OBJ, CITE_PM_LIST, CITE_OLDER_APIS],
},

{
"slug": "expired-manual-capture-holds",
"title": "Manual-capture holds expire before anyone captures them",
"description": "The authorization is valid for days, not weeks, and the clock is the network's. Capture late and the hold drops off the card and the money is gone.",
"h1": "manual-capture holds expire before anyone captures them",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe charge_expired_for_capture", "stripe manual capture window",
             "capture_before payment intent", "stripe authorization expired",
             "stripe requires_capture stuck"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A customer messages to say the pending charge disappeared from their statement, and they are pleased about it. You go to capture the payment, and Stripe answers <code>charge_expired_for_capture</code>. The order shipped. The authorization is gone, the money was never taken, and no retry exists that can take it now.",
"short_answer": """<p>Page <code>GET /v1/payment_intents?expand[]=data.latest_charge</code>, keep the ones with <code>capture_method</code> of <code>manual</code>, and read <code>latest_charge.payment_method_details.card.capture_before</code>. That timestamp is when the authorization dies. Anything at <code>requires_capture</code> with <code>capture_before</code> inside the next 48 hours is about to become revenue you do not collect.</p>
<p>For the historical loss, count manual-capture intents at <code>status: "canceled"</code> with <code>cancellation_reason: "automatic"</code>. That is Stripe recording an authorization that expired rather than a cancellation anyone asked for.</p>""",
"problem": """<p>The shape of this failure is that it looks like nothing at all. There is no failed payment, no decline, no error event. The intent quietly changes status, the hold falls off the customer's card, and your order table still says authorized. The first person to notice is usually the customer, who noticed money coming back.</p>
<p>It hurts most in exactly the businesses that chose manual capture on purpose: made-to-order goods, rentals, anything that authorizes at checkout and captures at dispatch. Those are the fulfilment cycles that sometimes take eight days, and the authorization window does not care that the delay was legitimate.</p>""",
"why": """<p><strong>The window is short and it is not yours.</strong> The authorization is held by the card network, not by Stripe, and it is valid for roughly seven days for most card-not-present transactions &mdash; less in several common cases: about five days for some Visa merchant-initiated transactions and as little as two for most card-present ones. A cron that captures on day seven is correct for one of those and too late for the others.</p>
<p><strong>So the date has to be read, never computed.</strong> Stripe puts the real deadline on the charge as <code>capture_before</code>. Any job that derives its own deadline from <code>created</code> plus a fixed number of days is guessing at a number the network already told you, and it guesses wrong for every transaction type outside the one it was written against.</p>
<p><strong>Expiry is silent by design.</strong> When the window closes the intent moves to <code>canceled</code> with <code>cancellation_reason</code> of <code>automatic</code>. Nothing failed, so nothing raises. If your webhook handler only listens for payment failures, this state never reaches it.</p>
<p><strong>The refund it generates pollutes your metrics.</strong> An expired uncaptured authorization produces a Refund whose <code>reason</code> is <code>expired_uncaptured_charge</code>. Nobody issued it, no customer asked for it, and it lands in the same table your refund rate is computed from &mdash; so the integration failure shows up in a report as unhappy customers.</p>""",
"steps": [
 {"h": "Expand the charge, because the deadline is not on the intent",
  "body": """<p><code>capture_before</code> lives at <code>payment_method_details.card.capture_before</code> on the charge, not on the PaymentIntent. Without <code>expand[]=data.latest_charge</code> the list gives you a charge id and nothing to read, which is the most common reason a check like this reports everything as unknown.</p>"""},
 {"h": "Sort by time remaining, not by age",
  "body": """<p>Two intents created the same minute can have different deadlines. Ordering the work queue by <code>capture_before</code> ascending puts the ones you are about to lose at the top regardless of when they were authorized.</p>"""},
 {"h": "Treat a missing capture_before as unknown, not as safe",
  "body": """<p>Non-card payment methods and unexpanded charges both produce an absent field. Defaulting that to seven days is how a check passes on the exact transactions it was supposed to catch.</p>"""},
 {"h": "Count what has already been lost",
  "body": """<p>Manual-capture intents at <code>canceled</code> with <code>cancellation_reason: "automatic"</code> are the historical bill. Sum their amounts before proposing the fix; the number is usually the argument.</p>"""},
 {"h": "Change the mechanism, not just the schedule",
  "body": """<p>If the fulfilment cycle genuinely runs longer than the window, a faster cron is a patch. Extended authorization buys a longer window on supported cards, and asking Stripe to capture automatically near the expiry moves the deadline off your infrastructure entirely.</p>"""},
],
"verify": """<p>Re-run the script. Nothing should be inside the warning window, and the historical count of automatically canceled holds should stop growing between runs.</p>
<pre><code class="language-bash">python3 stripe_manual_capture_holds.py --warn-hours 48
# 214 manual-capture intent(s): 209 captured, 5 held, 0 expiring, 0 lost</code></pre>""",
"code_intro": "One paginated GET with a single expansion, and no writes &mdash; a restricted key with read access to PaymentIntents and Charges is enough. The classifier is pure and takes the current time as an argument, which is what makes the interesting cases &mdash; two hours left, an hour past, no deadline at all &mdash; testable without waiting a week for one to occur.",
"py_file": "stripe_manual_capture_holds.py",
"py": '''"""Report Stripe manual-capture authorizations about to expire, or already lost.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to PaymentIntents and Charges. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_manual_capture_holds")

API = "https://api.stripe.com/v1"


def classify(intent, now, warn_seconds=48 * 3600):
    """Sort one PaymentIntent by how much of its authorization window is left.

    Pure, and `now` is passed in rather than read, so the states that matter
    here -- two hours left, an hour past, no deadline at all -- can be tested
    without waiting a week for a real one.

    The deadline is `capture_before` on the charge, not a fixed number of days
    after `created`: the window is roughly 7 days for most card-not-present
    transactions but shorter for several common types, so anything computed
    locally is wrong for whichever type it was not written against.

    Returns (state, detail).
    """
    if intent.get("capture_method") != "manual":
        return ("automatic", "captured automatically, no hold to lose")

    status = intent.get("status")

    if status == "succeeded":
        return ("captured", "captured inside the window")

    if status == "canceled":
        if intent.get("cancellation_reason") == "automatic":
            return ("lost",
                    "the authorization expired uncaptured: Stripe canceled it, "
                    "the hold was released, and no capture can take the money now")
        return ("canceled",
                "canceled deliberately (%s)"
                % (intent.get("cancellation_reason") or "no reason recorded"))

    if status != "requires_capture":
        return ("open", "status %s: nothing is authorised yet" % (status,))

    charge = intent.get("latest_charge")
    if not isinstance(charge, dict):
        return ("unknown",
                "requires_capture with no expanded charge: add "
                "expand[]=data.latest_charge, and do not assume seven days")

    card = ((charge.get("payment_method_details") or {}).get("card") or {})
    capture_before = card.get("capture_before")
    if not capture_before:
        return ("unknown",
                "requires_capture with no capture_before on the charge: the "
                "deadline is unknown, which is not the same as far away")

    left = int(capture_before) - int(now)
    if left <= 0:
        return ("expired",
                "capture_before passed %dh ago: the hold is gone even if the "
                "status has not caught up" % (-left // 3600))
    if left <= warn_seconds:
        return ("expiring",
                "%dh left to capture: past that the funds are released to the "
                "cardholder" % (left // 3600))
    return ("held", "%dh left to capture" % (left // 3600))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def intents(session, since, cap):
    """Yield PaymentIntents with their charge expanded, paginating to the cap."""
    seen = 0
    params = {"limit": 100, "created[gte]": since,
              "expand[]": "data.latest_charge"}
    while True:
        page = get(session, "/payment_intents", **params)
        data = page.get("data", [])
        for pi in data:
            yield pi
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read intents")
    ap.add_argument("--warn-hours", type=int, default=48,
                    help="flag holds with less than this much time left")
    ap.add_argument("--max-intents", type=int, default=20000,
                    help="stop paginating after this many intents")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    since = now - args.days * 86400
    counts, lost_amount = {}, 0
    manual = 0
    urgent = []

    for pi in intents(s, since, args.max_intents):
        state, detail = classify(pi, now, args.warn_hours * 3600)
        if state == "automatic":
            continue
        manual += 1
        counts[state] = counts.get(state, 0) + 1
        if state == "lost":
            lost_amount += pi.get("amount") or 0
        if state in ("expiring", "expired", "unknown"):
            urgent.append((pi, state, detail))

    # Soonest deadline first: two intents created the same minute can have very
    # different windows, so age is the wrong sort key.
    def deadline(row):
        charge = row[0].get("latest_charge")
        card = ((charge or {}).get("payment_method_details") or {}).get("card") or {}
        return card.get("capture_before") or 0

    for pi, state, detail in sorted(urgent, key=deadline):
        log.warning("%s  %-9s %s", pi.get("id", "pi_?"), state, detail)

    log.info("%d manual-capture intent(s): %d captured, %d held, %d expiring, "
             "%d lost", manual, counts.get("captured", 0), counts.get("held", 0),
             counts.get("expiring", 0) + counts.get("expired", 0),
             counts.get("lost", 0))

    if counts.get("expiring") or counts.get("expired"):
        log.warning("  repair: capture now, oldest deadline first:")
        log.warning("  POST %s/payment_intents/{id}/capture", API)
    if counts.get("lost"):
        log.warning("  %d authorization(s) already expired, %d minor unit(s) "
                    "never collected. Each one also produced a refund with "
                    "reason expired_uncaptured_charge.",
                    counts["lost"], lost_amount)
        log.warning("  repair: drive the capture job from capture_before rather "
                    "than a fixed delay, or request extended authorization, or "
                    "let Stripe capture near expiry.")
    return 1 if (counts.get("expiring") or counts.get("expired")
                 or counts.get("lost") or counts.get("unknown")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-manual-capture-holds.mjs",
"js": '''/**
 * Report Stripe manual-capture authorizations about to expire, or already lost.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to PaymentIntents and Charges. The repair is printed, never
 * performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Sort one PaymentIntent by how much of its authorization window is left. Pure,
 * and `now` is passed in rather than read, so two hours left, an hour past, and
 * no deadline at all are all testable. The deadline is capture_before on the
 * charge, never created plus a fixed number of days. Returns [state, detail].
 */
export function classify(intent, now, warnSeconds = 48 * 3600) {
  if (intent.capture_method !== 'manual') {
    return ['automatic', 'captured automatically, no hold to lose'];
  }

  const status = intent.status;

  if (status === 'succeeded') return ['captured', 'captured inside the window'];

  if (status === 'canceled') {
    if (intent.cancellation_reason === 'automatic') {
      return ['lost',
        'the authorization expired uncaptured: Stripe canceled it, the hold was ' +
        'released, and no capture can take the money now'];
    }
    return ['canceled',
      `canceled deliberately (${intent.cancellation_reason ?? 'no reason recorded'})`];
  }

  if (status !== 'requires_capture') {
    return ['open', `status ${status}: nothing is authorised yet`];
  }

  const charge = intent.latest_charge;
  if (!charge || typeof charge !== 'object') {
    return ['unknown',
      'requires_capture with no expanded charge: add expand[]=data.latest_charge, ' +
      'and do not assume seven days'];
  }

  const card = (charge.payment_method_details ?? {}).card ?? {};
  const captureBefore = card.capture_before;
  if (!captureBefore) {
    return ['unknown',
      'requires_capture with no capture_before on the charge: the deadline is ' +
      'unknown, which is not the same as far away'];
  }

  const left = Number(captureBefore) - Number(now);
  if (left <= 0) {
    return ['expired',
      `capture_before passed ${Math.floor(-left / 3600)}h ago: the hold is gone ` +
      'even if the status has not caught up'];
  }
  if (left <= warnSeconds) {
    return ['expiring',
      `${Math.floor(left / 3600)}h left to capture: past that the funds are ` +
      'released to the cardholder'];
  }
  return ['held', `${Math.floor(left / 3600)}h left to capture`];
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

export async function* intents(key, since, cap = 20000) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since,
                   'expand[]': 'data.latest_charge' };
  for (;;) {
    const page = await get(key, '/payment_intents', params);
    const data = page.data ?? [];
    for (const pi of data) {
      yield pi;
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
  const days = Number(process.env.DAYS ?? 30);
  const warnHours = Number(process.env.WARN_HOURS ?? 48);

  const counts = {};
  let manual = 0;
  let lostAmount = 0;
  const urgent = [];

  for await (const pi of intents(key, now - days * 86400)) {
    const [state, detail] = classify(pi, now, warnHours * 3600);
    if (state === 'automatic') continue;
    manual += 1;
    counts[state] = (counts[state] ?? 0) + 1;
    if (state === 'lost') lostAmount += pi.amount ?? 0;
    if (state === 'expiring' || state === 'expired' || state === 'unknown') {
      urgent.push([pi, state, detail]);
    }
  }

  // Soonest deadline first: age is the wrong sort key, because two intents
  // created the same minute can have very different windows.
  const deadline = ([pi]) =>
    (((pi.latest_charge ?? {}).payment_method_details ?? {}).card ?? {})
      .capture_before ?? 0;

  for (const [pi, state, detail] of urgent.sort((a, b) => deadline(a) - deadline(b))) {
    console.warn(`${pi.id ?? 'pi_?'}  ${state.padEnd(9)} ${detail}`);
  }

  const expiring = (counts.expiring ?? 0) + (counts.expired ?? 0);
  console.log(`${manual} manual-capture intent(s): ${counts.captured ?? 0} ` +
              `captured, ${counts.held ?? 0} held, ${expiring} expiring, ` +
              `${counts.lost ?? 0} lost`);

  if (expiring) {
    console.warn('  repair: capture now, oldest deadline first:');
    console.warn(`  POST ${API}/payment_intents/{id}/capture`);
  }
  if (counts.lost) {
    console.warn(`  ${counts.lost} authorization(s) already expired, ${lostAmount} ` +
                 'minor unit(s) never collected. Each one also produced a refund ' +
                 'with reason expired_uncaptured_charge.');
    console.warn('  repair: drive the capture job from capture_before rather than ' +
                 'a fixed delay, or request extended authorization, or let Stripe ' +
                 'capture near expiry.');
  }
  if (expiring || counts.lost || counts.unknown) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Passing the clock in is what makes this testable at all: an expiry that happens once a week in production is three lines here. The case worth being strict about is the missing <code>capture_before</code>, which has to sort as unknown rather than as safe &mdash; a default of seven days would clear exactly the card-present holds whose window is two.",
"test_py_file": "test_stripe_manual_capture_holds.py",
"test_py": '''from stripe_manual_capture_holds import classify

NOW = 1_700_000_000


def hold(capture_before, status="requires_capture"):
    return {
        "capture_method": "manual",
        "status": status,
        "latest_charge": {
            "payment_method_details": {"card": {"capture_before": capture_before}},
        },
    }


def test_automatic_capture_is_not_this_problem():
    assert classify({"capture_method": "automatic"}, NOW)[0] == "automatic"


def test_a_hold_with_days_left_is_held():
    state, detail = classify(hold(NOW + 5 * 86400), NOW)
    assert state == "held"
    assert "120h" in detail


def test_a_hold_inside_the_warning_window_is_expiring():
    state, detail = classify(hold(NOW + 6 * 3600), NOW)
    assert state == "expiring"
    assert "released to the cardholder" in detail


def test_a_passed_deadline_is_expired_even_at_requires_capture():
    # Stripe's status can lag the network. The deadline is the fact.
    state, _ = classify(hold(NOW - 3600), NOW)
    assert state == "expired"


def test_missing_capture_before_is_unknown_not_safe():
    state, detail = classify(hold(None), NOW)
    assert state == "unknown"
    assert "not the same as far away" in detail


def test_automatic_cancellation_is_the_historical_loss():
    state, detail = classify({
        "capture_method": "manual",
        "status": "canceled",
        "cancellation_reason": "automatic",
    }, NOW)
    assert state == "lost"
    assert "expired uncaptured" in detail
''',
"test_js_file": "stripe-manual-capture-holds.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-manual-capture-holds.mjs';

const NOW = 1700000000;

const hold = (captureBefore, status = 'requires_capture') => ({
  capture_method: 'manual',
  status,
  latest_charge: {
    payment_method_details: { card: { capture_before: captureBefore } },
  },
});

test('automatic capture is not this problem', () => {
  assert.equal(classify({ capture_method: 'automatic' }, NOW)[0], 'automatic');
});

test('a hold with days left is held', () => {
  const [state, detail] = classify(hold(NOW + 5 * 86400), NOW);
  assert.equal(state, 'held');
  assert.match(detail, /120h/);
});

test('a hold inside the warning window is expiring', () => {
  const [state, detail] = classify(hold(NOW + 6 * 3600), NOW);
  assert.equal(state, 'expiring');
  assert.match(detail, /released to the cardholder/);
});

test('a passed deadline is expired even at requires_capture', () => {
  assert.equal(classify(hold(NOW - 3600), NOW)[0], 'expired');
});

test('missing capture_before is unknown, not safe', () => {
  const [state, detail] = classify(hold(null), NOW);
  assert.equal(state, 'unknown');
  assert.match(detail, /not the same as far away/);
});

test('automatic cancellation is the historical loss', () => {
  const [state, detail] = classify({
    capture_method: 'manual',
    status: 'canceled',
    cancellation_reason: 'automatic',
  }, NOW);
  assert.equal(state, 'lost');
  assert.match(detail, /expired uncaptured/);
});
''',
"faq": [
 ("How long is a manual-capture authorization actually valid?",
  "Roughly seven days for most card-not-present transactions, and less for several common cases: around five days for some Visa merchant-initiated transactions and about two for most card-present ones. Because the number varies by transaction type, read capture_before off the charge instead of assuming any of them."),
 ("Where does capture_before live?",
  "On the charge, at payment_method_details.card.capture_before, so you need expand[]=data.latest_charge when listing PaymentIntents. The PaymentIntent itself does not carry the deadline."),
 ("What happens when the window closes?",
  "Stripe cancels the intent with cancellation_reason 'automatic' and the hold is released back to the cardholder. Nothing fails, so nothing raises, and a capture attempt afterwards returns charge_expired_for_capture."),
 ("Why is my refund rate wrong?",
  "An expired uncaptured authorization produces a Refund whose reason is expired_uncaptured_charge. Nobody issued it and no customer asked for it, so counting it as a refund turns an integration failure into a customer-satisfaction number."),
 ("What if fulfilment genuinely takes longer than the window?",
  "Then a faster cron only shrinks the losses. Extended authorization lengthens the window on supported cards, and letting Stripe capture automatically near the expiry moves the deadline off your own scheduler, which is where it keeps being missed."),
],
"related": [
 ("/stripe/stale-requires-payment-method-intents/", "PaymentIntents sit in requires_payment_method for weeks"),
 ("/stripe/abandoned-requires-action-intents/", "3DS handoff breaks and requires_action intents pile up"),
 ("/stripe/refunds-failed-or-stuck/", "Refunds sit failed or requires_action and nobody notices"),
],
"citations": [CITE_HOLD, CITE_PI_OBJ, CITE_ERROR_CODES, CITE_REFUND_OBJ],
},

{
"slug": "bank-debit-intents-stuck-processing",
"title": "Bank-debit intents stay in processing for over a week",
"description": "ACH and SEPA payments legitimately sit in processing for days. Code that only ever looks for succeeded turns that state into a permanent one.",
"h1": "bank-debit intents stay in processing for over a week",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payment intent processing stuck", "stripe ach processing status",
             "sepa debit processing stripe", "stripe us_bank_account settlement",
             "stripe async payment method webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Bank-debit orders divide into two piles and neither is right. Some shipped the moment the customer clicked, and a few of those later bounced. The rest have never shipped at all, because nothing in the code ever looked at them again. The intents are all sitting in <code>processing</code>, which is where an ACH payment is supposed to sit &mdash; for a while.",
"short_answer": """<p>Page <code>GET /v1/payment_intents</code>, keep <code>status == "processing"</code>, and read <code>payment_method_types</code>. For <code>us_bank_account</code>, <code>sepa_debit</code>, <code>acss_debit</code>, <code>bacs_debit</code> and <code>au_becs_debit</code>, a few days in that state is settlement working normally.</p>
<p>The number that matters is age against the method's own window: ACH settles in about four business days, SEPA in about five. An intent still processing well past its window is stuck, and one still processing on a card is a different failure entirely.</p>""",
"problem": """<p>The damage arrives in two directions from the same missing check. Fulfil on <code>processing</code> and you ship before the money exists, so a failed debit weeks later is a loss with the goods already gone. Fulfil only on <code>succeeded</code> but never look again, and the payment settles perfectly and the order sits unshipped until the customer asks.</p>
<p>Most integrations manage both at once, because different code paths made different assumptions. The checkout controller treats anything not-failed as good; the reconciliation job treats anything not-succeeded as pending. Neither is wrong about cards, where <code>processing</code> lasts seconds and is effectively invisible.</p>""",
"why": """<p><strong><code>processing</code> is a legitimate resting state here, not an error.</strong> That is what makes it dangerous. Every other stuck status &mdash; <code>requires_payment_method</code>, <code>requires_action</code> &mdash; means somebody has to do something. This one means the bank has it and you wait, so there is no wrong-looking value to alert on and no threshold that is right for every method.</p>
<p><strong>The window is per method, so one number cannot cover them all.</strong> A single seven-day rule flags healthy SEPA debits while missing ACH debits that have been stuck for a week. The check has to carry a small table of settlement windows and compare each intent against its own.</p>
<p><strong>Nothing polls you.</strong> A card payment resolves inside the request that created it, so a great deal of integration code assumes the answer is available at checkout. For a bank debit the answer arrives days later as <code>payment_intent.succeeded</code> or <code>payment_intent.payment_failed</code>, and an integration with no endpoint subscribed to those simply never learns it.</p>
<p><strong>A stuck debit and a slow one look identical from outside.</strong> Both are <code>processing</code>. Only the age separates them, which is why this check is arithmetic rather than a status read, and why the classifier takes the current time as an argument.</p>""",
"steps": [
 {"h": "Filter to the asynchronous methods",
  "body": """<p><code>payment_method_types</code> tells you what the intent could have been paid with. The bank debits are <code>us_bank_account</code>, <code>sepa_debit</code>, <code>acss_debit</code>, <code>bacs_debit</code> and <code>au_becs_debit</code>; everything else in <code>processing</code> for more than a day is a different problem worth reporting separately.</p>"""},
 {"h": "Compare age against the method's own window",
  "body": """<p>Keep the windows in one small table so they can be argued about in one place. Where an intent lists more than one debit type, use the most generous window of the set rather than the first one, or the check reports settlement as failure.</p>"""},
 {"h": "Corroborate against the charge",
  "body": """<p>The charge for a bank debit sits at <code>status: "pending"</code> for the same period, and <code>payment_method_details</code> carries the method-specific detail. Where a verification problem is the cause, that is where the wording lives.</p>"""},
 {"h": "Fix the reason there is no answer, not just the backlog",
  "body": """<p>A backlog of stuck intents is the symptom of nothing listening. An endpoint subscribed to <code>payment_intent.succeeded</code>, <code>payment_intent.processing</code> and <code>payment_intent.payment_failed</code> is what stops the pile re-forming after you clear it.</p>"""},
 {"h": "Decide what to do with the genuinely dead ones",
  "body": """<p>Cancellation is permitted in <code>processing</code> for bank debits, but only inside a limited window, so very old intents may not be cancellable at all. Those have to be reconciled against the charges rather than tidied through the API.</p>"""},
],
"verify": """<p>Re-run the script. Everything still processing should be inside its own settlement window, with nothing in the stuck or long-stuck buckets.</p>
<pre><code class="language-bash">python3 stripe_bank_debit_processing.py --days 90
# 1,180 processing intent(s): 1,180 settling, 0 stuck, 0 long-stuck, 0 non-debit</code></pre>""",
"code_intro": "One paginated GET over <code>/v1/payment_intents</code> and no writes &mdash; a restricted key with read access to PaymentIntents is enough. The settlement windows live in one table at the top of the file so they can be adjusted in a single place, and the classifier takes both the intent and the clock, which is what makes a nine-day-old ACH debit a test rather than a wait.",
"py_file": "stripe_bank_debit_processing.py",
"py": '''"""Report Stripe bank-debit PaymentIntents stuck in processing past settlement.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to PaymentIntents. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_bank_debit_processing")

API = "https://api.stripe.com/v1"

# Calendar days, generous on purpose: the documented settlement times are in
# business days (ACH about four, SEPA about five), so these carry a weekend.
# One number for every method would flag healthy SEPA while missing stuck ACH,
# which is the whole reason this is a table rather than a constant.
SETTLEMENT_DAYS = {
    "us_bank_account": 6,
    "acss_debit": 6,
    "sepa_debit": 7,
    "bacs_debit": 5,
    "au_becs_debit": 5,
}


def classify(intent, now, grace_days=0):
    """Sort one processing PaymentIntent against its own settlement window.

    Pure, and `now` is passed in rather than read, so a nine-day-old ACH debit
    is a test case rather than a wait.

    `processing` is a legitimate resting state for a bank debit and a fault for
    anything else, so the method decides which rule applies. Where an intent
    lists several debit types, the most generous window wins: reporting normal
    settlement as failure is how a check like this gets switched off.

    Returns (state, detail).
    """
    if intent.get("status") != "processing":
        return ("not_processing", "status %s" % (intent.get("status"),))

    types = [t for t in (intent.get("payment_method_types") or [])
             if t in SETTLEMENT_DAYS]
    age_days = (int(now) - int(intent.get("created") or now)) / 86400.0

    if not types:
        if age_days < 1:
            return ("settling",
                    "processing on a synchronous method, less than a day old")
        return ("non_debit",
                "processing for %.1f day(s) on a method with no multi-day "
                "settlement: the confirmation never completed" % age_days)

    window = max(SETTLEMENT_DAYS[t] for t in types) + grace_days
    method = max(types, key=lambda t: SETTLEMENT_DAYS[t])

    if age_days <= window:
        return ("settling",
                "day %.1f of a %d day window for %s" % (age_days, window, method))
    if age_days > 30:
        return ("long_stuck",
                "%.1f day(s) in processing on %s: far past settlement, and past "
                "the window in which cancelling is still permitted" % (age_days, method))
    return ("stuck",
            "%.1f day(s) in processing on %s, window is %d: this is not "
            "settlement taking its time" % (age_days, method, window))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def intents(session, since, cap):
    """Yield PaymentIntents, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/payment_intents", **params)
        data = page.get("data", [])
        for pi in data:
            yield pi
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to read intents")
    ap.add_argument("--grace-days", type=int, default=0,
                    help="add this many days to every settlement window")
    ap.add_argument("--max-intents", type=int, default=20000,
                    help="stop paginating after this many intents")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    counts, amounts = {}, {}
    processing = 0

    for pi in intents(s, now - args.days * 86400, args.max_intents):
        state, detail = classify(pi, now, args.grace_days)
        if state == "not_processing":
            continue
        processing += 1
        counts[state] = counts.get(state, 0) + 1
        amounts[state] = amounts.get(state, 0) + (pi.get("amount") or 0)
        if state != "settling":
            log.warning("%s  %-11s %s", pi.get("id", "pi_?"), state, detail)

    stuck = counts.get("stuck", 0)
    long_stuck = counts.get("long_stuck", 0)

    log.info("%d processing intent(s): %d settling, %d stuck, %d long-stuck, "
             "%d non-debit", processing, counts.get("settling", 0), stuck,
             long_stuck, counts.get("non_debit", 0))

    if stuck or long_stuck:
        log.warning("  %d minor unit(s) sitting in processing past settlement",
                    amounts.get("stuck", 0) + amounts.get("long_stuck", 0))
        log.warning("  repair: subscribe an endpoint to payment_intent.succeeded, "
                    "payment_intent.processing and payment_intent.payment_failed, "
                    "and gate fulfilment on succeeded only:")
        log.warning("  POST %s/webhook_endpoints -d url=... "
                    "-d enabled_events[]=payment_intent.succeeded", API)
    if long_stuck:
        log.warning("  %d intent(s) are past the point where cancelling is "
                    "permitted. Reconcile those against GET %s/charges.",
                    long_stuck, API)
    if counts.get("non_debit"):
        log.warning("  %d intent(s) are processing on a method with no "
                    "multi-day settlement: those are a confirmation that never "
                    "finished, not a slow bank.", counts["non_debit"])
    return 1 if (stuck or long_stuck or counts.get("non_debit")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-bank-debit-processing.mjs",
"js": '''/**
 * Report Stripe bank-debit PaymentIntents stuck in processing past settlement.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to PaymentIntents. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Calendar days, generous on purpose: the documented settlement times are in
// business days (ACH about four, SEPA about five), so these carry a weekend.
// One number for every method would flag healthy SEPA while missing stuck ACH.
const SETTLEMENT_DAYS = {
  us_bank_account: 6,
  acss_debit: 6,
  sepa_debit: 7,
  bacs_debit: 5,
  au_becs_debit: 5,
};

/**
 * Sort one processing PaymentIntent against its own settlement window. Pure,
 * and `now` is passed in rather than read. Where an intent lists several debit
 * types the most generous window wins. Returns [state, detail].
 */
export function classify(intent, now, graceDays = 0) {
  if (intent.status !== 'processing') return ['not_processing', `status ${intent.status}`];

  const types = (intent.payment_method_types ?? []).filter((t) => t in SETTLEMENT_DAYS);
  const ageDays = (Number(now) - Number(intent.created ?? now)) / 86400;

  if (types.length === 0) {
    if (ageDays < 1) {
      return ['settling', 'processing on a synchronous method, less than a day old'];
    }
    return ['non_debit',
      `processing for ${ageDays.toFixed(1)} day(s) on a method with no ` +
      'multi-day settlement: the confirmation never completed'];
  }

  const window = Math.max(...types.map((t) => SETTLEMENT_DAYS[t])) + graceDays;
  const method = types.reduce(
    (a, b) => (SETTLEMENT_DAYS[b] > SETTLEMENT_DAYS[a] ? b : a));

  if (ageDays <= window) {
    return ['settling', `day ${ageDays.toFixed(1)} of a ${window} day window for ${method}`];
  }
  if (ageDays > 30) {
    return ['long_stuck',
      `${ageDays.toFixed(1)} day(s) in processing on ${method}: far past ` +
      'settlement, and past the window in which cancelling is still permitted'];
  }
  return ['stuck',
    `${ageDays.toFixed(1)} day(s) in processing on ${method}, window is ` +
    `${window}: this is not settlement taking its time`];
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

export async function* intents(key, since, cap = 20000) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/payment_intents', params);
    const data = page.data ?? [];
    for (const pi of data) {
      yield pi;
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
  const days = Number(process.env.DAYS ?? 90);
  const graceDays = Number(process.env.GRACE_DAYS ?? 0);

  const counts = {};
  const amounts = {};
  let processing = 0;

  for await (const pi of intents(key, now - days * 86400)) {
    const [state, detail] = classify(pi, now, graceDays);
    if (state === 'not_processing') continue;
    processing += 1;
    counts[state] = (counts[state] ?? 0) + 1;
    amounts[state] = (amounts[state] ?? 0) + (pi.amount ?? 0);
    if (state !== 'settling') {
      console.warn(`${pi.id ?? 'pi_?'}  ${state.padEnd(11)} ${detail}`);
    }
  }

  const stuck = counts.stuck ?? 0;
  const longStuck = counts.long_stuck ?? 0;

  console.log(`${processing} processing intent(s): ${counts.settling ?? 0} ` +
              `settling, ${stuck} stuck, ${longStuck} long-stuck, ` +
              `${counts.non_debit ?? 0} non-debit`);

  if (stuck || longStuck) {
    console.warn(`  ${(amounts.stuck ?? 0) + (amounts.long_stuck ?? 0)} minor ` +
                 'unit(s) sitting in processing past settlement');
    console.warn('  repair: subscribe an endpoint to payment_intent.succeeded, ' +
                 'payment_intent.processing and payment_intent.payment_failed, ' +
                 'and gate fulfilment on succeeded only:');
    console.warn(`  POST ${API}/webhook_endpoints -d url=... ` +
                 '-d enabled_events[]=payment_intent.succeeded');
  }
  if (longStuck) {
    console.warn(`  ${longStuck} intent(s) are past the point where cancelling ` +
                 `is permitted. Reconcile those against GET ${API}/charges.`);
  }
  if (counts.non_debit) {
    console.warn(`  ${counts.non_debit} intent(s) are processing on a method ` +
                 'with no multi-day settlement: those are a confirmation that ' +
                 'never finished, not a slow bank.');
  }
  if (stuck || longStuck || counts.non_debit) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests exist mostly to defend the per-method table. A five-day-old SEPA debit and a nine-day-old ACH debit are the pair that a single threshold gets wrong in both directions, and an intent listing two debit types has to take the longer window or the check reports normal settlement as failure and gets switched off within a week.",
"test_py_file": "test_stripe_bank_debit_processing.py",
"test_py": '''from stripe_bank_debit_processing import classify

NOW = 1_700_000_000
DAY = 86400


def intent(types, age_days, status="processing"):
    return {
        "status": status,
        "payment_method_types": types,
        "created": NOW - int(age_days * DAY),
    }


def test_settled_intents_are_ignored():
    state, _ = classify(intent(["us_bank_account"], 30, status="succeeded"), NOW)
    assert state == "not_processing"


def test_ach_inside_its_window_is_settling():
    state, detail = classify(intent(["us_bank_account"], 3), NOW)
    assert state == "settling"
    assert "us_bank_account" in detail


def test_sepa_at_five_days_is_still_settling():
    # A single seven-day rule would be wrong here in one direction and wrong
    # about the ACH case below in the other.
    assert classify(intent(["sepa_debit"], 5), NOW)[0] == "settling"


def test_ach_at_nine_days_is_stuck():
    state, detail = classify(intent(["us_bank_account"], 9), NOW)
    assert state == "stuck"
    assert "not settlement taking its time" in detail


def test_several_debit_types_take_the_most_generous_window():
    state, _ = classify(intent(["us_bank_account", "sepa_debit"], 6.5), NOW)
    assert state == "settling"


def test_a_card_left_processing_is_a_different_failure():
    state, detail = classify(intent(["card"], 4), NOW)
    assert state == "non_debit"
    assert "confirmation never completed" in detail
''',
"test_js_file": "stripe-bank-debit-processing.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-bank-debit-processing.mjs';

const NOW = 1700000000;
const DAY = 86400;

const intent = (types, ageDays, status = 'processing') => ({
  status,
  payment_method_types: types,
  created: NOW - Math.round(ageDays * DAY),
});

test('settled intents are ignored', () => {
  assert.equal(
    classify(intent(['us_bank_account'], 30, 'succeeded'), NOW)[0], 'not_processing');
});

test('ACH inside its window is settling', () => {
  const [state, detail] = classify(intent(['us_bank_account'], 3), NOW);
  assert.equal(state, 'settling');
  assert.match(detail, /us_bank_account/);
});

test('SEPA at five days is still settling', () => {
  assert.equal(classify(intent(['sepa_debit'], 5), NOW)[0], 'settling');
});

test('ACH at nine days is stuck', () => {
  const [state, detail] = classify(intent(['us_bank_account'], 9), NOW);
  assert.equal(state, 'stuck');
  assert.match(detail, /not settlement taking its time/);
});

test('several debit types take the most generous window', () => {
  assert.equal(
    classify(intent(['us_bank_account', 'sepa_debit'], 6.5), NOW)[0], 'settling');
});

test('a card left processing is a different failure', () => {
  const [state, detail] = classify(intent(['card'], 4), NOW);
  assert.equal(state, 'non_debit');
  assert.match(detail, /confirmation never completed/);
});
''',
"faq": [
 ("Is processing an error state?",
  "No, and that is what makes it awkward. For ACH, SEPA, BECS, Bacs and pre-authorized debit, processing is where a payment legitimately sits while the bank moves the money. Only the age tells you whether a given intent is settling or stuck."),
 ("How long should each method take?",
  "Roughly four business days for ACH and about five for SEPA, with the other debits in the same range. Because the numbers differ, a single threshold flags healthy payments on one method while missing stuck ones on another, so keep a small per-method table instead."),
 ("Can I just poll the intent at checkout and be done?",
  "No. The answer does not exist yet at checkout, and no amount of polling in that request will produce it. The result arrives days later as payment_intent.succeeded or payment_intent.payment_failed, so an endpoint subscribed to those is the only way to learn it."),
 ("Should I fulfil while the intent is processing?",
  "Only if you are willing to lose the goods when the debit fails, which does happen. Gate fulfilment on succeeded and treat processing as a state your order system understands and displays, rather than one it silently rounds to either good or bad."),
 ("Can I cancel a payment that has been processing for months?",
  "Probably not. Cancellation is permitted in processing for bank debits but only inside a limited window, so very old intents have to be reconciled against the charges instead of tidied up through the API."),
],
"related": [
 ("/stripe/stale-requires-payment-method-intents/", "PaymentIntents sit in requires_payment_method for weeks"),
 ("/stripe/checkout-complete-payment-unpaid/", "Session status is complete but payment_status is still unpaid"),
 ("/stripe/expired-manual-capture-holds/", "Manual-capture holds expire before anyone captures them"),
],
"citations": [CITE_LIFECYCLE, CITE_PI_OBJ, CITE_ACH, CITE_SEPA],
},

]
