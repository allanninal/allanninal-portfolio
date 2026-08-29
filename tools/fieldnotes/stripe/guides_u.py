#!/usr/bin/env python3
"""/stripe/ field notes, batch U — the writing.

Four notes about the Customer record and the credentials hanging off it: the
address Stripe Tax and the issuer both need, the consent recorded when a card is
saved, the payments that never reach a Customer at all, and the subscription
flag that decides whether the card that just paid is kept.

Same constraint as every other batch here: each problem is findable with a
RESTRICTED, READ-ONLY Stripe key. None of these scripts writes. They read, they
say exactly what is wrong, and they print the repair for a human to run against
a live payments account.
"""

CITE_CUSTOMER_OBJ = ("The customer object — Stripe API reference",
                     "https://docs.stripe.com/api/customers/object")
CITE_CUSTOMER_UPDATE = ("Update a customer — Stripe API reference",
                        "https://docs.stripe.com/api/customers/update")
CITE_ERROR_CODES = ("Error codes — Stripe Docs", "https://docs.stripe.com/error-codes")
CITE_SCA = ("Strong Customer Authentication — Stripe Docs",
            "https://docs.stripe.com/strong-customer-authentication")
CITE_SETUP_INTENT_OBJ = ("The SetupIntent object — Stripe API reference",
                         "https://docs.stripe.com/api/setup_intents/object")
CITE_SETUP_INTENT_CREATE = ("Create a SetupIntent — Stripe API reference",
                            "https://docs.stripe.com/api/setup_intents/create")
CITE_SAVE_REUSE = ("Set up future payments — Stripe Docs",
                   "https://docs.stripe.com/payments/save-and-reuse")
CITE_PI_OBJ = ("The PaymentIntent object — Stripe API reference",
               "https://docs.stripe.com/api/payment_intents/object")
CITE_PI_CREATE = ("Create a PaymentIntent — Stripe API reference",
                  "https://docs.stripe.com/api/payment_intents/create")
CITE_CHARGE_OBJ = ("The charge object — Stripe API reference",
                   "https://docs.stripe.com/api/charges/object")
CITE_SEARCH = ("Search — Stripe Docs", "https://docs.stripe.com/search")
CITE_SUB_OBJ = ("The subscription object — Stripe API reference",
                "https://docs.stripe.com/api/subscriptions/object")
CITE_SUB_CREATE = ("Create a subscription — Stripe API reference",
                   "https://docs.stripe.com/api/subscriptions/create")
CITE_SUB_UPDATE = ("Update a subscription — Stripe API reference",
                   "https://docs.stripe.com/api/subscriptions/update")

GUIDES = [

{
"slug": "customers-missing-address",
"title": "Customers have no address, so tax and SCA exemptions fail",
"description": "Stripe Tax refuses to finalize with customer_tax_location_invalid, AVS never runs, and European authorisation rates lag. customer.address is null.",
"h1": "customers have no address, so tax and SCA exemptions fail",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe customer address null", "customer_tax_location_invalid",
             "stripe tax customer location", "billing_address_collection required",
             "stripe address_postal_code_check"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "An invoice will not finalize. The error is <code>customer_tax_location_invalid</code>, which sounds like a Stripe Tax configuration problem and is not: the registrations are fine, the rates are fine, and the customer simply has no address on file. Your own database has their shipping address. Stripe's copy of the Customer has <code>address: null</code>, and it has been that way since the integration was written.",
"short_answer": """<p>Page <code>GET /v1/customers</code> and classify each <code>address</code> three ways, not two. <code>null</code> is the obvious case. An address object present but missing <code>country</code>, or missing <code>postal_code</code>, fails tax resolution in exactly the same way and does not look empty in the Dashboard.</p>
<p>Then weight it. Page <code>GET /v1/subscriptions?status=active&amp;expand[]=data.customer</code> and count the subscribed customers whose address is incomplete &mdash; those are the ones with a finalization due every cycle. Confirm the damage with <code>GET /v1/invoices/search?query=last_finalization_error_code:'customer_tax_location_invalid'</code>.</p>""",
"problem": """<p>The address is the field everybody assumes Stripe already has. It was collected at checkout, it is in the orders table, it is printed on the packing slip. It was just never written to the Customer object, because the code that creates the Customer runs before the address form and nothing ever goes back to fill it in.</p>
<p>What makes it expensive is that three unrelated systems quietly depend on it and each degrades differently. Stripe Tax does not degrade at all &mdash; it hard-fails at finalization, so the invoice simply does not go out. AVS has nothing to check, so <code>address_postal_code_check</code> comes back <code>null</code> on every card and one of the cheapest fraud signals you have is permanently off. And several SCA exemptions are calculated with the customer's location as an input, so European authorisation rates sag a few points in a way nobody attributes to a missing field.</p>""",
"why": """<p><strong>The Customer is created before the address exists.</strong> The usual sequence is create the <code>cus_</code> record at signup or at the start of checkout, then collect the address on a later step and store it locally. Stripe's copy stays null forever. The application is not broken by this because it reads the address from its own tables; only Stripe's own features are working blind.</p>
<p><strong>Checkout does not collect it unless you ask.</strong> <code>billing_address_collection</code> defaults to <code>auto</code>, which means Stripe collects an address only when the payment method needs one. Card payments frequently do not, so a Checkout integration can run for years collecting nothing. The Payment Element behaves the same way: the billing fields have to be turned on.</p>
<p><strong>A partial address is invisible.</strong> An address with <code>line1</code> and <code>city</code> filled in looks complete on the Customer page. Tax needs the country; AVS needs the postal code. Any check that only counts <code>address == null</code> reports a clean account while a third of it is unusable, which is the failure mode of every version of this check written in a hurry.</p>
<p><strong>Nothing fails at the moment of the mistake.</strong> Creating an addressless Customer is a 200. Charging one is a 200. Subscribing one is a 200. The first negative signal is an invoice that will not finalize, months later, on a customer who has already paid you several times.</p>""",
"steps": [
 {"h": "Classify every customer's address, not just the null ones",
  "body": """<p>Three failure states, one healthy one. <code>address</code> absent; <code>address</code> present with no <code>country</code>; <code>address</code> present with no <code>postal_code</code>. Treat an address object whose every field is <code>null</code> as absent &mdash; Stripe returns that shape and it is not a partial address, it is an empty one.</p>"""},
 {"h": "Weight the count by who is subscribed",
  "body": """<p>Ten thousand addressless customers from a free tier is a data-quality note. Forty addressless customers with active subscriptions is a finalization failure every month. <code>GET /v1/subscriptions?status=active&amp;limit=100&amp;expand[]=data.customer</code> gives you the second number in the same pass, without a per-customer request.</p>"""},
 {"h": "Confirm it against invoices that already failed",
  "body": """<p><code>GET /v1/invoices/search?query=last_finalization_error_code:'customer_tax_location_invalid'</code> turns the theory into a list. If that returns rows, this is not a risk assessment any more and the ticket should say so.</p>"""},
 {"h": "Check whether AVS has ever run",
  "body": """<p><code>GET /v1/payment_methods?customer={id}&amp;type=card</code> and read <code>card.checks.address_postal_code_check</code>. <code>null</code> means the check was never performed, because nothing was submitted to compare against. A wall of nulls is the fraud signal you have been paying for and not receiving.</p>"""},
 {"h": "Close the collection hole before backfilling",
  "body": """<p>Backfilling from your own users table fixes today's population and nothing else. Set <code>billing_address_collection=required</code> on Checkout Sessions, or configure the Payment Element to collect billing details, so tomorrow's customers arrive complete. Where a location is genuinely unavailable, <code>customer.tax.ip_address</code> gives Stripe Tax a fallback signal, though it is weaker than a real address.</p>"""},
],
"verify": """<p>Re-run the script. Every customer with an active subscription should classify as <code>complete</code>, and the tax-failure search should return nothing.</p>
<pre><code class="language-bash">python3 stripe_customer_address.py
# clear      1,204 customer(s), 0 with an incomplete address</code></pre>""",
"code_intro": "Two paginated GETs and one search, all reads &mdash; a restricted key with read access to Customers, Subscriptions and Invoices is enough, and is what you should give it. Two pure functions do the thinking: one classifies a single address, because the partial cases are where every hand-written version of this check goes wrong, and one rolls the counts up into a verdict.",
"py_file": "stripe_customer_address.py",
"py": '''"""Report Stripe customers whose address cannot satisfy Tax, AVS or SCA.

Read only. Paginated GETs and one search, no writes: give this a RESTRICTED key
with read access to Customers, Subscriptions and Invoices. The repair is printed,
never performed, because this script holds a credential to a live payments
account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_customer_address")

API = "https://api.stripe.com/v1"

WIDESPREAD = 0.25   # share of incomplete addresses that means the collection path is wrong


def address_state(customer):
    """Classify one customer's address. Pure, so it can be tested without a network.

    Returns one of "missing", "no_country", "no_postal_code" or "complete".

    Stripe returns `address` either as null or as an object whose fields are
    individually null. An object with nothing in it is an absent address, not a
    partial one, and collapsing the two hides the customers who look filled in on
    the Dashboard but resolve to no location at all.
    """
    addr = customer.get("address")
    if not isinstance(addr, dict):
        return "missing"
    if not any(v for v in addr.values()):
        return "missing"
    if not addr.get("country"):
        return "no_country"
    if not addr.get("postal_code"):
        return "no_postal_code"
    return "complete"


def verdict(total, incomplete, subscribed_incomplete, tax_failures):
    """Roll the counts up into one state. Pure.

    Ordered deliberately: an invoice that has already refused to finalize outranks
    any percentage, and a subscribed customer outranks a free-tier one, because
    only the subscribed ones have a finalization due every cycle.
    """
    if not total:
        return ("unknown", "no customers read; check the key and the mode it belongs to")
    if tax_failures:
        return ("failing",
                "%d invoice(s) already refused to finalize with "
                "customer_tax_location_invalid. This is not a risk, it is unsent "
                "revenue." % tax_failures)
    if subscribed_incomplete:
        return ("billing",
                "%d subscribed customer(s) have an incomplete address. Each renewal "
                "is a finalization that can fail." % subscribed_incomplete)
    share = incomplete / float(total)
    if share >= WIDESPREAD:
        return ("widespread",
                "%d of %d customer(s), %.0f%%, have an incomplete address. At that "
                "share the collection path is wrong, not the data." % (
                    incomplete, total, share * 100))
    if incomplete:
        return ("residue",
                "%d of %d customer(s) have an incomplete address. Backfill them and "
                "close the collection hole." % (incomplete, total))
    return ("clear", "%d customer(s), 0 with an incomplete address" % total)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Yield every object from a paginated list endpoint, up to `limit`."""
    seen = 0
    params = dict(params, limit=100)
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def tax_failure_count(session):
    """Count invoices that failed to finalize on the customer's location.

    Search is a separate index and is not enabled on every account, so a failure
    here is reported and treated as no evidence rather than as zero evidence.
    """
    try:
        page = get(session, "/invoices/search",
                   query="last_finalization_error_code:'customer_tax_location_invalid'",
                   limit=100)
    except requests.HTTPError as exc:
        log.info("invoice search unavailable (%s); skipping the confirmation step", exc)
        return 0
    return len(page.get("data", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-customers", type=int, default=5000,
                    help="stop paginating customers after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    buckets = {"missing": 0, "no_country": 0, "no_postal_code": 0, "complete": 0}
    examples = {}
    total = 0
    for cus in page_all(s, "/customers", args.max_customers):
        state = address_state(cus)
        buckets[state] += 1
        total += 1
        if state != "complete":
            examples.setdefault(state, cus["id"])

    subscribed_incomplete = 0
    for sub in page_all(s, "/subscriptions", 1000, status="active",
                        **{"expand[]": "data.customer"}):
        cus = sub.get("customer")
        if isinstance(cus, dict) and address_state(cus) != "complete":
            subscribed_incomplete += 1

    incomplete = total - buckets["complete"]
    state, detail = verdict(total, incomplete, subscribed_incomplete,
                            tax_failure_count(s))

    line = "%-11s %s" % (state, detail)
    if state in ("clear", "unknown"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  %d absent, %d without a country, %d without a postal code",
                buckets["missing"], buckets["no_country"], buckets["no_postal_code"])
    for bucket, cus_id in sorted(examples.items()):
        log.warning("  example %-14s %s", bucket, cus_id)
    log.warning("  repair one customer:")
    log.warning("  POST %s/customers/{id} -d \\"address[line1]=...\\" "
                "-d \\"address[city]=...\\" -d \\"address[postal_code]=...\\" "
                "-d \\"address[country]=US\\"", API)
    log.warning("  stop creating more: set billing_address_collection=required on "
                "Checkout Sessions, or collect billing details in the Payment Element")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-customer-address.mjs",
"js": '''/**
 * Report Stripe customers whose address cannot satisfy Tax, AVS or SCA.
 *
 * Read only. Paginated GETs and one search, no writes: give this a RESTRICTED
 * key with read access to Customers, Subscriptions and Invoices. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Share of incomplete addresses that means the collection path is wrong.
export const WIDESPREAD = 0.25;

/**
 * Classify one customer's address. Pure, so it can be tested without a network.
 * Returns 'missing', 'no_country', 'no_postal_code' or 'complete'.
 *
 * Stripe returns `address` either as null or as an object whose fields are
 * individually null. An object with nothing in it is an absent address, not a
 * partial one.
 */
export function addressState(customer) {
  const addr = customer.address;
  if (!addr || typeof addr !== 'object') return 'missing';
  if (!Object.values(addr).some((v) => v)) return 'missing';
  if (!addr.country) return 'no_country';
  if (!addr.postal_code) return 'no_postal_code';
  return 'complete';
}

/**
 * Roll the counts up into one state. Pure.
 * An invoice that has already refused to finalize outranks any percentage.
 */
export function verdict(total, incomplete, subscribedIncomplete, taxFailures) {
  if (!total) {
    return ['unknown', 'no customers read; check the key and the mode it belongs to'];
  }
  if (taxFailures) {
    return ['failing',
      `${taxFailures} invoice(s) already refused to finalize with ` +
      'customer_tax_location_invalid. This is not a risk, it is unsent revenue.'];
  }
  if (subscribedIncomplete) {
    return ['billing',
      `${subscribedIncomplete} subscribed customer(s) have an incomplete address. ` +
      'Each renewal is a finalization that can fail.'];
  }
  const share = incomplete / total;
  if (share >= WIDESPREAD) {
    return ['widespread',
      `${incomplete} of ${total} customer(s), ${Math.round(share * 100)}%, have an ` +
      'incomplete address. At that share the collection path is wrong, not the data.'];
  }
  if (incomplete) {
    return ['residue',
      `${incomplete} of ${total} customer(s) have an incomplete address. Backfill ` +
      'them and close the collection hole.'];
  }
  return ['clear', `${total} customer(s), 0 with an incomplete address`];
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

async function* pageAll(key, path, limit, params = {}) {
  let seen = 0;
  const p = { ...params, limit: 100 };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const obj of data) { yield obj; seen += 1; }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    p.starting_after = data[data.length - 1].id;
  }
}

async function taxFailureCount(key) {
  try {
    const page = await get(key, '/invoices/search', {
      query: "last_finalization_error_code:'customer_tax_location_invalid'",
      limit: 100,
    });
    return (page.data ?? []).length;
  } catch (err) {
    console.log(`invoice search unavailable (${err.message}); skipping the confirmation step`);
    return 0;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const buckets = { missing: 0, no_country: 0, no_postal_code: 0, complete: 0 };
  const examples = new Map();
  let total = 0;
  for await (const cus of pageAll(key, '/customers', 5000)) {
    const state = addressState(cus);
    buckets[state] += 1;
    total += 1;
    if (state !== 'complete' && !examples.has(state)) examples.set(state, cus.id);
  }

  let subscribedIncomplete = 0;
  for await (const sub of pageAll(key, '/subscriptions', 1000,
    { status: 'active', 'expand[]': 'data.customer' })) {
    const cus = sub.customer;
    if (cus && typeof cus === 'object' && addressState(cus) !== 'complete') {
      subscribedIncomplete += 1;
    }
  }

  const incomplete = total - buckets.complete;
  const [state, detail] = verdict(total, incomplete, subscribedIncomplete,
    await taxFailureCount(key));

  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'clear' || state === 'unknown') { console.log(line); return; }

  console.warn(line);
  console.warn(`  ${buckets.missing} absent, ${buckets.no_country} without a country, ` +
               `${buckets.no_postal_code} without a postal code`);
  for (const [bucket, id] of [...examples].sort()) {
    console.warn(`  example ${bucket.padEnd(14)} ${id}`);
  }
  console.warn('  repair one customer:');
  console.warn(`  POST ${API}/customers/{id} -d "address[line1]=..." ` +
               '-d "address[city]=..." -d "address[postal_code]=..." -d "address[country]=US"');
  console.warn('  stop creating more: set billing_address_collection=required on ' +
               'Checkout Sessions, or collect billing details in the Payment Element');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are mostly about the shapes that look complete and are not: an address object whose every field is null, and one with a street and a city but no country. Both render as a filled-in address in the Dashboard, both fail tax resolution, and a check that counts only <code>address == null</code> will call the account clean.",
"test_py_file": "test_stripe_customer_address.py",
"test_py": '''from stripe_customer_address import address_state, verdict


def test_absent_address_is_missing():
    assert address_state({"id": "cus_1"}) == "missing"
    assert address_state({"address": None}) == "missing"


def test_address_object_with_every_field_null_is_missing_not_partial():
    # Stripe returns this shape. It renders as an address and resolves to nothing.
    empty = {"line1": None, "line2": None, "city": None,
             "state": None, "postal_code": None, "country": None}
    assert address_state({"address": empty}) == "missing"


def test_street_and_city_without_a_country_still_fails_tax():
    addr = {"line1": "12 Rue de Rivoli", "city": "Paris", "postal_code": "75001"}
    assert address_state({"address": addr}) == "no_country"


def test_country_without_a_postal_code_fails_avs():
    assert address_state({"address": {"country": "US", "city": "Denver"}}) == "no_postal_code"


def test_a_complete_address_is_complete():
    addr = {"line1": "1 Main St", "city": "Denver", "postal_code": "80202", "country": "US"}
    assert address_state({"address": addr}) == "complete"


def test_a_failed_finalization_outranks_any_percentage():
    state, detail = verdict(1000, 1, 0, 3)
    assert state == "failing"
    assert "3" in detail


def test_subscribed_customers_outrank_the_overall_share():
    # 4 of 1000 is a rounding error until you notice all four are billed monthly.
    state, _ = verdict(1000, 4, 4, 0)
    assert state == "billing"


def test_a_quarter_incomplete_is_a_collection_problem():
    assert verdict(1000, 249, 0, 0)[0] == "residue"
    assert verdict(1000, 250, 0, 0)[0] == "widespread"


def test_no_customers_is_not_silently_clear():
    assert verdict(0, 0, 0, 0)[0] == "unknown"
''',
"test_js_file": "stripe-customer-address.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { addressState, verdict } from './stripe-customer-address.mjs';

test('absent address is missing', () => {
  assert.equal(addressState({ id: 'cus_1' }), 'missing');
  assert.equal(addressState({ address: null }), 'missing');
});

test('address object with every field null is missing not partial', () => {
  const empty = {
    line1: null, line2: null, city: null,
    state: null, postal_code: null, country: null,
  };
  assert.equal(addressState({ address: empty }), 'missing');
});

test('street and city without a country still fails tax', () => {
  const addr = { line1: '12 Rue de Rivoli', city: 'Paris', postal_code: '75001' };
  assert.equal(addressState({ address: addr }), 'no_country');
});

test('country without a postal code fails avs', () => {
  assert.equal(addressState({ address: { country: 'US', city: 'Denver' } }),
    'no_postal_code');
});

test('a complete address is complete', () => {
  const addr = { line1: '1 Main St', city: 'Denver', postal_code: '80202', country: 'US' };
  assert.equal(addressState({ address: addr }), 'complete');
});

test('a failed finalization outranks any percentage', () => {
  const [state, detail] = verdict(1000, 1, 0, 3);
  assert.equal(state, 'failing');
  assert.match(detail, /3/);
});

test('subscribed customers outrank the overall share', () => {
  assert.equal(verdict(1000, 4, 4, 0)[0], 'billing');
});

test('a quarter incomplete is a collection problem', () => {
  assert.equal(verdict(1000, 249, 0, 0)[0], 'residue');
  assert.equal(verdict(1000, 250, 0, 0)[0], 'widespread');
});

test('no customers is not silently clear', () => {
  assert.equal(verdict(0, 0, 0, 0)[0], 'unknown');
});
''',
"faq": [
 ("What exactly does Stripe Tax need from the customer?",
  "A location it can resolve, which in practice means at minimum address.country, and postal_code wherever the tax varies below the country level, as it does in the US and Canada. Without one it raises customer_tax_location_invalid at finalization rather than falling back to a default rate, so the invoice does not go out at all."),
 ("Some countries genuinely have no postal codes. Does that break the check?",
  "It flags them, which is why the script reports no_postal_code as its own bucket rather than lumping it in with the rest. Hong Kong, the UAE and a handful of others have no postcode system; a customer there with a country set is fine for tax, and only the AVS postal check is unavailable. Read the buckets before you write the backfill."),
 ("Does an address on the PaymentMethod count?",
  "Not for tax. billing_details.address lives on the PaymentMethod and is what AVS compares against; customer.address is what Stripe Tax resolves. They are separate fields and setting one does not populate the other, which is why an account can have good AVS coverage and still fail every finalization."),
 ("Will adding addresses actually improve authorisation rates?",
  "It removes one reason for a decline rather than guaranteeing an approval. AVS results and the customer's location feed both the issuer's decision and several SCA exemption calculations, so the effect shows up as a few points across a large population, not as a fixed transaction that used to fail."),
 ("Can I detect this without a live secret key?",
  "Yes. A restricted key with read access to Customers, Subscriptions and Invoices covers every call in this script, and it cannot move money if it leaks."),
],
"related": [
 ("/stripe/customers-missing-email/", "Customers have no email, so Stripe sends no receipts"),
 ("/stripe/avs-cvc-fail-captured/", "Charges captured after AVS and CVC verification failed"),
 ("/stripe/no-tax-registrations-while-selling-abroad/", "No tax registrations while invoicing many countries"),
],
"citations": [CITE_CUSTOMER_OBJ, CITE_CUSTOMER_UPDATE, CITE_ERROR_CODES, CITE_SCA],
},

{
"slug": "setup-intent-on-session-for-off-session",
"title": "SetupIntents use on_session but you bill off-session",
"description": "Cards saved through the save-for-later flow work at checkout and every unattended renewal dies on authentication_required. usage was set to on_session.",
"h1": "SetupIntents use on_session but you bill off-session",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["setup_intent usage on_session", "stripe authentication_required off session",
             "stripe mandate null", "setup_future_usage off_session",
             "stripe merchant initiated transaction"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The card saves cleanly. It shows up on the customer, the last four digits are right, and if the customer comes back and pays with it themselves it works every time. The renewal that runs at three in the morning fails with <code>authentication_required</code>, and so does the one after that. The card is saved; it was never authorised for anyone but the customer to use.",
"short_answer": """<p>Page <code>GET /v1/setup_intents?created[gte]={now-180d}</code> and look for <code>status == "succeeded"</code> together with <code>usage == "on_session"</code> and <code>mandate == null</code>. That combination is a card that was stored with consent for customer-present reuse only. Mirror it on the payment side by counting PaymentIntents with <code>setup_future_usage == "on_session"</code>.</p>
<p>The signal that turns it from a style question into a bug is the customer. An <code>on_session</code> save on a customer with an active subscription is a renewal waiting to fail. Confirm with <code>last_payment_error.decline_code == "authentication_required"</code> on the same customers.</p>""",
"problem": """<p>Two things have to line up for this to bite, and each of them is reasonable on its own. Saving a card with <code>usage: "on_session"</code> is correct if the customer will always be present when you charge it &mdash; a stored card in a one-click checkout, say. Billing a subscription off-session is correct too. The bug is the seam between them, and the seam is in two different files written months apart.</p>
<p>It also fails asymmetrically, which delays the diagnosis. Domestic cards from issuers that do not enforce SCA charge fine off-session with no mandate, because nobody checks. European cards and any issuer running strict rules decline. So the report is "renewals fail for some customers", the affected set looks random from the inside, and the first suspicion is always the card rather than the consent recorded when it was saved.</p>""",
"why": """<p><strong><code>usage</code> is about consent, not about storage.</strong> The card is stored either way. What <code>off_session</code> adds is a mandate: a record, shown to the issuer, that the customer agreed to unattended charges by this merchant. <code>on_session</code> creates no such agreement, so an off-session charge later has nothing to present and the issuer asks for authentication that nobody is there to provide.</p>
<p><strong><code>off_session</code> is already the default, so this is always an active choice.</strong> Omitting <code>usage</code> entirely gives you the right behaviour. It gets set to <code>on_session</code> deliberately, usually by someone reading the docs at the moment they are building a customer-present flow, and the same helper is later reused by the subscription code.</p>
<p><strong>The save looks perfect in every tool you have.</strong> The SetupIntent succeeds. The PaymentMethod attaches. It appears on the Customer in the Dashboard with the brand, the last four and the expiry. Nothing in that view mentions the mandate, and <code>mandate: null</code> on the SetupIntent is the only place the difference is visible.</p>
<p><strong>The failure arrives one billing cycle later.</strong> A monthly subscription puts thirty days between the save and the first unattended charge. By then the deploy is merged, the customer has forgotten the card form, and the decline code points at authentication rather than at consent.</p>""",
"steps": [
 {"h": "Count the on_session saves over a real window",
  "body": """<p>Page <code>GET /v1/setup_intents?limit=100&amp;created[gte]={now-180d}</code>. Six months rather than thirty days: a card saved in March is what breaks the renewal in September, and a short window will show you a healthy month while the damage sits just outside it.</p>"""},
 {"h": "Check the payment side too",
  "body": """<p>Cards are saved during payment as often as through a dedicated flow. <code>GET /v1/payment_intents</code> and count <code>setup_future_usage == "on_session"</code>. It is the same mistake through a different parameter, and a check that only reads SetupIntents misses whichever half of your integration saves cards at checkout.</p>"""},
 {"h": "Intersect with customers who are billed unattended",
  "body": """<p>An <code>on_session</code> card on a customer with no subscription may be exactly right. The same card on a subscribed customer is not. <code>GET /v1/subscriptions?status=active&amp;limit=100</code> gives you the customer ids to intersect against, and it is that intersection, not the raw count, that belongs in the ticket.</p>"""},
 {"h": "Corroborate with declines that already happened",
  "body": """<p>Count <code>last_payment_error.decline_code == "authentication_required"</code> on recent PaymentIntents. If those declines exist <em>and</em> the customers have <code>on_session</code> saves, the diagnosis is settled. If they exist and nobody has an <code>on_session</code> save, the cause is elsewhere and this note is the wrong one to be reading.</p>"""},
 {"h": "Re-collect consent rather than flipping a flag",
  "body": """<p>You cannot promote an existing <code>on_session</code> save to a mandate after the fact; the customer's agreement is the thing that is missing, and it has to be asked for. Create a fresh SetupIntent with <code>usage=off_session</code>, show mandate text covering what you will charge, how often, and how the amount is determined, and do it before the next renewal rather than after it fails.</p>"""},
],
"verify": """<p>Re-run the script. Every succeeded SetupIntent for a subscribed customer should read <code>off_session</code>, and the authentication_required count should stop rising.</p>
<pre><code class="language-bash">python3 stripe_setup_intent_usage.py
# clear       412 saved card(s), all off_session, 0 authentication_required decline(s)</code></pre>""",
"code_intro": "Three paginated GETs and no writes &mdash; a restricted key with read access to SetupIntents, PaymentIntents and Subscriptions is enough, and is what you should give it. The classifier is pure and its ordering is the interesting part: declines only mean this problem when there are <code>on_session</code> saves to blame them on, and a check that skips that condition will confidently misdiagnose an unrelated 3DS bug.",
"py_file": "stripe_setup_intent_usage.py",
"py": '''"""Report Stripe cards saved with usage=on_session but billed off-session.

Read only. Three paginated GETs, no writes: give this a RESTRICTED key with read
access to SetupIntents, PaymentIntents and Subscriptions. The repair is printed,
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
log = logging.getLogger("stripe_setup_intent_usage")

API = "https://api.stripe.com/v1"


def verdict(succeeded, on_session, on_session_subscribed, auth_required):
    """Classify the account. Pure, so the ordering can be tested without a network.

    `on_session` counts saved cards recorded for customer-present reuse only.
    `on_session_subscribed` is the subset belonging to customers with an active
    subscription, which is the only subset that is unambiguously wrong.

    The decline count is deliberately checked second, not first: authentication
    failures with no on_session save behind them are a different bug, and reporting
    them here sends people to re-collect consent that was already correct.
    """
    if not succeeded:
        return ("unknown", "no succeeded SetupIntents in the window; nothing to judge")
    if on_session_subscribed and auth_required:
        return ("declining",
                "%d card(s) saved on_session belong to subscribed customers, and "
                "%d off-session charge(s) have already failed on "
                "authentication_required." % (on_session_subscribed, auth_required))
    if on_session_subscribed:
        return ("exposed",
                "%d card(s) saved on_session belong to customers with an active "
                "subscription. Nothing has failed yet; the next renewal is the "
                "test." % on_session_subscribed)
    if on_session:
        return ("review",
                "%d of %d saved card(s) used usage=on_session, none of them for a "
                "subscribed customer. Correct only if you never charge without the "
                "customer present." % (on_session, succeeded))
    if auth_required:
        return ("elsewhere",
                "%d off-session decline(s) on authentication_required, but every "
                "saved card is off_session. The mandate is not the cause; look at "
                "the charge path." % auth_required)
    return ("clear",
            "%d saved card(s), all off_session, 0 authentication_required decline(s)"
            % succeeded)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    seen = 0
    params = dict(params, limit=100)
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def subscribed_customer_ids(session, limit):
    ids = set()
    for sub in page_all(session, "/subscriptions", limit, status="active"):
        cus = sub.get("customer")
        if isinstance(cus, dict):
            cus = cus.get("id")
        if cus:
            ids.add(cus)
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=180,
                    help="how far back to read SetupIntents and PaymentIntents")
    ap.add_argument("--max-intents", type=int, default=5000,
                    help="stop paginating each list after this many objects")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    subscribed = subscribed_customer_ids(s, 2000)

    succeeded = on_session = on_session_subscribed = 0
    offenders = []
    for si in page_all(s, "/setup_intents", args.max_intents,
                       **{"created[gte]": since}):
        if si.get("status") != "succeeded":
            continue
        succeeded += 1
        if si.get("usage") != "on_session":
            continue
        on_session += 1
        cus = si.get("customer")
        if isinstance(cus, dict):
            cus = cus.get("id")
        if cus in subscribed:
            on_session_subscribed += 1
            if len(offenders) < 10:
                offenders.append((si["id"], cus, si.get("mandate")))

    pi_on_session = auth_required = 0
    for pi in page_all(s, "/payment_intents", args.max_intents,
                       **{"created[gte]": since}):
        if pi.get("setup_future_usage") == "on_session":
            pi_on_session += 1
        err = pi.get("last_payment_error") or {}
        if err.get("decline_code") == "authentication_required":
            auth_required += 1

    state, detail = verdict(succeeded, on_session + pi_on_session,
                            on_session_subscribed, auth_required)

    line = "%-11s %s" % (state, detail)
    if state in ("clear", "unknown"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  %d SetupIntent(s) and %d PaymentIntent(s) recorded on_session",
                on_session, pi_on_session)
    for si_id, cus, mandate in offenders:
        log.warning("  %s  customer=%s  mandate=%s", si_id, cus, mandate)
    log.warning("  repair: collect fresh consent, then save with the right usage")
    log.warning("  POST %s/setup_intents -d customer=cus_XXX -d usage=off_session", API)
    log.warning("  when saving during a payment: -d setup_future_usage=off_session")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-setup-intent-usage.mjs",
"js": '''/**
 * Report Stripe cards saved with usage=on_session but billed off-session.
 *
 * Read only. Three paginated GETs, no writes: give this a RESTRICTED key with
 * read access to SetupIntents, PaymentIntents and Subscriptions. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify the account. Pure, so the ordering can be tested without a network.
 *
 * The decline count is deliberately checked second, not first: authentication
 * failures with no on_session save behind them are a different bug.
 */
export function verdict(succeeded, onSession, onSessionSubscribed, authRequired) {
  if (!succeeded) {
    return ['unknown', 'no succeeded SetupIntents in the window; nothing to judge'];
  }
  if (onSessionSubscribed && authRequired) {
    return ['declining',
      `${onSessionSubscribed} card(s) saved on_session belong to subscribed ` +
      `customers, and ${authRequired} off-session charge(s) have already failed ` +
      'on authentication_required.'];
  }
  if (onSessionSubscribed) {
    return ['exposed',
      `${onSessionSubscribed} card(s) saved on_session belong to customers with ` +
      'an active subscription. Nothing has failed yet; the next renewal is the test.'];
  }
  if (onSession) {
    return ['review',
      `${onSession} of ${succeeded} saved card(s) used usage=on_session, none of ` +
      'them for a subscribed customer. Correct only if you never charge without ' +
      'the customer present.'];
  }
  if (authRequired) {
    return ['elsewhere',
      `${authRequired} off-session decline(s) on authentication_required, but ` +
      'every saved card is off_session. The mandate is not the cause; look at ' +
      'the charge path.'];
  }
  return ['clear',
    `${succeeded} saved card(s), all off_session, 0 authentication_required decline(s)`];
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

async function* pageAll(key, path, limit, params = {}) {
  let seen = 0;
  const p = { ...params, limit: 100 };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const obj of data) { yield obj; seen += 1; }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    p.starting_after = data[data.length - 1].id;
  }
}

async function subscribedCustomerIds(key, limit = 2000) {
  const ids = new Set();
  for await (const sub of pageAll(key, '/subscriptions', limit, { status: 'active' })) {
    const cus = typeof sub.customer === 'object' ? sub.customer?.id : sub.customer;
    if (cus) ids.add(cus);
  }
  return ids;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = 180;
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  const subscribed = await subscribedCustomerIds(key);

  let succeeded = 0;
  let onSession = 0;
  let onSessionSubscribed = 0;
  const offenders = [];
  for await (const si of pageAll(key, '/setup_intents', 5000, { 'created[gte]': since })) {
    if (si.status !== 'succeeded') continue;
    succeeded += 1;
    if (si.usage !== 'on_session') continue;
    onSession += 1;
    const cus = typeof si.customer === 'object' ? si.customer?.id : si.customer;
    if (subscribed.has(cus)) {
      onSessionSubscribed += 1;
      if (offenders.length < 10) offenders.push([si.id, cus, si.mandate]);
    }
  }

  let piOnSession = 0;
  let authRequired = 0;
  for await (const pi of pageAll(key, '/payment_intents', 5000, { 'created[gte]': since })) {
    if (pi.setup_future_usage === 'on_session') piOnSession += 1;
    if (pi.last_payment_error?.decline_code === 'authentication_required') authRequired += 1;
  }

  const [state, detail] = verdict(succeeded, onSession + piOnSession,
    onSessionSubscribed, authRequired);

  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'clear' || state === 'unknown') { console.log(line); return; }

  console.warn(line);
  console.warn(`  ${onSession} SetupIntent(s) and ${piOnSession} PaymentIntent(s) recorded on_session`);
  for (const [id, cus, mandate] of offenders) {
    console.warn(`  ${id}  customer=${cus}  mandate=${mandate}`);
  }
  console.warn('  repair: collect fresh consent, then save with the right usage');
  console.warn(`  POST ${API}/setup_intents -d customer=cus_XXX -d usage=off_session`);
  console.warn('  when saving during a payment: -d setup_future_usage=off_session');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the ordering, because that is what separates a diagnosis from a guess. <code>authentication_required</code> declines are the loudest number on the page and they only mean <em>this</em> when there are <code>on_session</code> saves behind them; on their own they belong to a different note, and the classifier has to say so rather than claim the credit.",
"test_py_file": "test_stripe_setup_intent_usage.py",
"test_py": '''from stripe_setup_intent_usage import verdict


def test_on_session_saves_for_subscribed_customers_with_declines_are_the_diagnosis():
    state, detail = verdict(500, 40, 12, 7)
    assert state == "declining"
    assert "12" in detail and "7" in detail


def test_on_session_saves_for_subscribed_customers_are_flagged_before_anything_fails():
    state, detail = verdict(500, 40, 12, 0)
    assert state == "exposed"
    assert "next renewal" in detail


def test_on_session_saves_with_no_subscribers_are_only_worth_a_look():
    # A stored card for a customer-present one-click checkout is legitimately on_session.
    state, _ = verdict(500, 40, 0, 0)
    assert state == "review"


def test_declines_without_on_session_saves_are_a_different_bug():
    state, detail = verdict(500, 0, 0, 31)
    assert state == "elsewhere"
    assert "not the cause" in detail


def test_all_off_session_and_no_declines_is_clear():
    assert verdict(500, 0, 0, 0)[0] == "clear"


def test_an_empty_window_is_not_silently_clear():
    assert verdict(0, 0, 0, 0)[0] == "unknown"
''',
"test_js_file": "stripe-setup-intent-usage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-setup-intent-usage.mjs';

test('on_session saves for subscribed customers with declines are the diagnosis', () => {
  const [state, detail] = verdict(500, 40, 12, 7);
  assert.equal(state, 'declining');
  assert.match(detail, /12/);
  assert.match(detail, /7/);
});

test('on_session saves for subscribed customers are flagged before anything fails', () => {
  const [state, detail] = verdict(500, 40, 12, 0);
  assert.equal(state, 'exposed');
  assert.match(detail, /next renewal/);
});

test('on_session saves with no subscribers are only worth a look', () => {
  assert.equal(verdict(500, 40, 0, 0)[0], 'review');
});

test('declines without on_session saves are a different bug', () => {
  const [state, detail] = verdict(500, 0, 0, 31);
  assert.equal(state, 'elsewhere');
  assert.match(detail, /not the cause/);
});

test('all off_session and no declines is clear', () => {
  assert.equal(verdict(500, 0, 0, 0)[0], 'clear');
});

test('an empty window is not silently clear', () => {
  assert.equal(verdict(0, 0, 0, 0)[0], 'unknown');
});
''',
"faq": [
 ("What does usage actually change, if the card is stored either way?",
  "It changes what the issuer is told. off_session establishes a mandate recording the customer's agreement to merchant-initiated charges; on_session records consent for reuse while the customer is present. The stored credential is identical. Only the mandate lets a later unattended charge answer the issuer's question about authorisation."),
 ("Can I convert an existing on_session card to off_session?",
  "Not by updating the object. The missing piece is the customer's consent, which has to be collected again: create a new SetupIntent with usage=off_session for the same customer and payment method, show mandate text, and confirm it while they are on the page."),
 ("Is setup_future_usage=on_session on a PaymentIntent the same mistake?",
  "Yes, through a different parameter. It saves the card during a payment with the same customer-present consent, so a subscription created against that PaymentMethod hits the same wall. The script counts both, because integrations commonly save cards on one path and bill on the other."),
 ("Why do only some customers fail?",
  "Because enforcement varies by issuer and by region. Where SCA rules are applied strictly, an off-session charge with no mandate is challenged and there is nobody to complete the challenge. Elsewhere the same charge is approved. That is why the affected set looks random and why the raw decline rate underestimates the exposure."),
 ("Does this check need a live secret key?",
  "No. A restricted key with read access to SetupIntents, PaymentIntents and Subscriptions covers every call here, and it cannot move money if it leaks."),
],
"related": [
 ("/stripe/setup-intents-never-confirmed/", "SetupIntents are created but never confirmed by the client"),
 ("/stripe/off-session-authentication-required-declines/", "Off-session charges die on authentication_required"),
 ("/stripe/unattached-payment-methods-orphaned/", "PaymentMethods are created but never attached to a customer"),
],
"citations": [CITE_SETUP_INTENT_OBJ, CITE_SETUP_INTENT_CREATE, CITE_SAVE_REUSE, CITE_SCA],
},

{
"slug": "payment-intents-with-null-customer",
"title": "PaymentIntents have a null customer, so payments are orphaned",
"description": "The Dashboard lists payments with nobody attached. The card cannot be saved, Radar loses its history, and returning buyers pay every time as strangers.",
"h1": "PaymentIntents have a null customer, so payments are orphaned",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payment intent no customer", "stripe guest checkout customer",
             "stripe customer_creation always", "stripe card fingerprint repeat",
             "payment intent customer null"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Someone in support asks a simple question: how many times has this person bought from us? There is no answer. Their payments are in Stripe, four of them, all succeeded, all with the customer column empty. Same card, same email in the billing details, four separate strangers as far as Stripe is concerned &mdash; and as far as Radar is concerned too.",
"short_answer": """<p>Page <code>GET /v1/payment_intents?created[gte]={now-90d}</code> and count how many have <code>customer == null</code>, as a number, as a share of the total, and as a sum of <code>amount</code>. That is the size of the cohort you cannot see a history for.</p>
<p>Then find the part that is provably costing you something. Page <code>GET /v1/charges</code> over the same window, group the customerless ones by <code>payment_method_details.card.fingerprint</code>, and flag any fingerprint appearing more than once. Those are repeat buyers you are treating as first-timers, which is exactly the signal Radar uses to approve people.</p>""",
"problem": """<p>Nothing here is failing. The payments succeed, the money arrives, the accounting balances. What is missing is the connective tissue: with no <code>cus_</code> on the intent, there is no payment history to open, no card to offer back at the next checkout, and nothing for <code>setup_future_usage</code> to attach a saved credential to even if you passed it.</p>
<p>The part that costs money is the risk model. Stripe weighs a known, previously-successful customer very differently from an anonymous one. A buyer on their fourth purchase should be an easy approval; presented as a stranger every time, they get scored as a stranger every time, and some proportion of them are declined or land in review for no reason other than the missing link.</p>""",
"why": """<p><strong><code>customer</code> is optional and the guest path is the shortest path.</strong> A PaymentIntent with an amount, a currency and a payment method is a complete, valid request. Adding a Customer means a lookup, a create, an email to match on and a decision about what to do when two records collide. Skipping it ships a working checkout on the first afternoon.</p>
<p><strong>Checkout will not create one unless told.</strong> A Checkout Session without <code>customer</code> and without <code>customer_creation=always</code> produces a payment and no Customer record. This is easy to miss because the Session itself collects an email, so the data appears to have been captured &mdash; it just lives on the Session rather than on anything reusable.</p>
<p><strong>The loss is invisible from inside the application.</strong> Your own database has the user, the order and the email. Every screen you built looks right. The gap only exists on Stripe's side, in the systems you did not build: the payment history, the saved cards, the risk score.</p>
<p><strong>By the time you want it, backfilling is guesswork.</strong> Linking old payments to people after the fact means matching on card fingerprint and billing email, which works for most rows and not all of them. The fingerprint is stable per card, so a customer who has changed cards splits into two, and a shared family card merges two people into one.</p>""",
"steps": [
 {"h": "Measure the orphan share over ninety days",
  "body": """<p>Page <code>GET /v1/payment_intents?limit=100&amp;created[gte]={now-90d}</code>. Count <code>customer == null</code> and sum the <code>amount</code> for that slice. The share matters more than the count: 3% is a guest-checkout option working as intended, 60% is the default path.</p>"""},
 {"h": "Find the repeat buyers hiding in it",
  "body": """<p>This is the number that ends the argument. Page <code>GET /v1/charges</code> over the same window, take the customerless successes, and group by <code>payment_method_details.card.fingerprint</code>. Every fingerprint with a count above one is a returning customer whose history Stripe was not allowed to keep.</p>"""},
 {"h": "Check whether the card could have been saved",
  "body": """<p>Among the orphans, count how many also have <code>setup_future_usage == null</code>. That confirms the same code path is both failing to identify the buyer and failing to keep their card, which is one fix rather than two.</p>"""},
 {"h": "Attach a customer before the intent, not after",
  "body": """<p>Look up or create the Customer from your own user record, then pass <code>customer</code> into <code>POST /v1/payment_intents</code>. In Checkout, pass an existing <code>customer</code> or set <code>customer_creation=always</code>. Deduplicate on your own user id rather than on the email, or you will trade this problem for a different one.</p>"""},
 {"h": "Backfill carefully and only where it is safe",
  "body": """<p>Match historical orphans to your users on <code>billing_details.email</code> first and card fingerprint second, and leave the ambiguous ones alone. A wrong link is worse than a missing one: it puts one person's payment history on another person's account.</p>"""},
],
"verify": """<p>Re-run the script after the checkout change. New intents should carry a customer, and the repeat-fingerprint count should stop growing.</p>
<pre><code class="language-bash">python3 stripe_orphan_payments.py
# clear       2,318 payment intent(s), 0 with no customer attached</code></pre>""",
"code_intro": "Two paginated GETs and no writes &mdash; a restricted key with read access to PaymentIntents and Charges is enough, and is what you should give it. The classifier is pure and puts the fingerprint evidence above the percentage, because a repeat buyer counted twice is proof of a specific loss while a share is only ever an argument about product design.",
"py_file": "stripe_orphan_payments.py",
"py": '''"""Report Stripe payments with no Customer attached, and the repeat buyers in them.

Read only. Two paginated GETs, no writes: give this a RESTRICTED key with read
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
log = logging.getLogger("stripe_orphan_payments")

API = "https://api.stripe.com/v1"

DOMINANT = 0.5   # share of orphaned intents above which guest checkout is the default path


def verdict(total, orphans, repeat_fingerprints):
    """Classify the window. Pure, so the ordering can be tested without a network.

    `repeat_fingerprints` counts distinct cards that paid more than once with no
    Customer attached. It outranks the share on purpose: a share is an argument
    about how much guest checkout you meant to have, and a repeat fingerprint is a
    named buyer whose history Stripe was not allowed to keep.
    """
    if not total:
        return ("unknown", "no payment intents in the window; nothing to judge")
    share = orphans / float(total)
    if repeat_fingerprints:
        return ("repeat",
                "%d card(s) paid more than once with no customer attached. Those are "
                "returning buyers scored as strangers every time." % repeat_fingerprints)
    if share >= DOMINANT:
        return ("dominant",
                "%d of %d payment intent(s), %.0f%%, have no customer. Guest checkout "
                "is the default path, not an option." % (orphans, total, share * 100))
    if orphans:
        return ("guests",
                "%d of %d payment intent(s) have no customer. Expected if guest "
                "checkout is deliberate; costly if it is not." % (orphans, total))
    return ("clear", "%d payment intent(s), 0 with no customer attached" % total)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    seen = 0
    params = dict(params, limit=100)
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def repeat_cards(session, since, limit):
    """Group customerless successful charges by card fingerprint.

    The fingerprint is stable for one card across payments, so a count above one
    is the same physical card paying twice as two different strangers. It is not
    stable across a reissue, which makes this an undercount rather than a guess.
    """
    counts = {}
    for ch in page_all(session, "/charges", limit, **{"created[gte]": since}):
        if ch.get("customer") or ch.get("status") != "succeeded":
            continue
        card = ((ch.get("payment_method_details") or {}).get("card") or {})
        fp = card.get("fingerprint")
        if fp:
            counts[fp] = counts.get(fp, 0) + 1
    return {fp: n for fp, n in counts.items() if n > 1}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to read payment intents and charges")
    ap.add_argument("--max-objects", type=int, default=5000,
                    help="stop paginating each list after this many objects")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400

    total = orphans = orphan_amount = unsaveable = 0
    for pi in page_all(s, "/payment_intents", args.max_objects,
                       **{"created[gte]": since}):
        total += 1
        if pi.get("customer"):
            continue
        orphans += 1
        orphan_amount += pi.get("amount") or 0
        if not pi.get("setup_future_usage"):
            unsaveable += 1

    repeats = repeat_cards(s, since, args.max_objects)
    state, detail = verdict(total, orphans, len(repeats))

    line = "%-11s %s" % (state, detail)
    if state in ("clear", "unknown"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  %d in the smallest currency unit is unattributed to anyone",
                orphan_amount)
    log.warning("  %d of the orphans also had no setup_future_usage, so the card "
                "was discarded too", unsaveable)
    for fp, n in sorted(repeats.items(), key=lambda kv: -kv[1])[:10]:
        log.warning("  fingerprint %s paid %d times as a stranger", fp, n)
    log.warning("  repair: look the customer up before creating the intent")
    log.warning("  POST %s/payment_intents -d customer=cus_XXX "
                "-d setup_future_usage=off_session", API)
    log.warning("  in Checkout: pass an existing customer, or customer_creation=always")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-orphan-payments.mjs",
"js": '''/**
 * Report Stripe payments with no Customer attached, and the repeat buyers in them.
 *
 * Read only. Two paginated GETs, no writes: give this a RESTRICTED key with read
 * access to PaymentIntents and Charges. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Share of orphaned intents above which guest checkout is the default path.
export const DOMINANT = 0.5;

/**
 * Classify the window. Pure, so the ordering can be tested without a network.
 *
 * `repeatFingerprints` outranks the share on purpose: a share is an argument
 * about how much guest checkout you meant to have, and a repeat fingerprint is a
 * named buyer whose history Stripe was not allowed to keep.
 */
export function verdict(total, orphans, repeatFingerprints) {
  if (!total) return ['unknown', 'no payment intents in the window; nothing to judge'];
  const share = orphans / total;
  if (repeatFingerprints) {
    return ['repeat',
      `${repeatFingerprints} card(s) paid more than once with no customer attached. ` +
      'Those are returning buyers scored as strangers every time.'];
  }
  if (share >= DOMINANT) {
    return ['dominant',
      `${orphans} of ${total} payment intent(s), ${Math.round(share * 100)}%, have ` +
      'no customer. Guest checkout is the default path, not an option.'];
  }
  if (orphans) {
    return ['guests',
      `${orphans} of ${total} payment intent(s) have no customer. Expected if guest ` +
      'checkout is deliberate; costly if it is not.'];
  }
  return ['clear', `${total} payment intent(s), 0 with no customer attached`];
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

async function* pageAll(key, path, limit, params = {}) {
  let seen = 0;
  const p = { ...params, limit: 100 };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const obj of data) { yield obj; seen += 1; }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    p.starting_after = data[data.length - 1].id;
  }
}

/**
 * Group customerless successful charges by card fingerprint. The fingerprint is
 * stable for one card across payments and not across a reissue, which makes this
 * an undercount rather than a guess.
 */
export async function repeatCards(key, since, limit = 5000) {
  const counts = new Map();
  for await (const ch of pageAll(key, '/charges', limit, { 'created[gte]': since })) {
    if (ch.customer || ch.status !== 'succeeded') continue;
    const fp = ch.payment_method_details?.card?.fingerprint;
    if (fp) counts.set(fp, (counts.get(fp) ?? 0) + 1);
  }
  return new Map([...counts].filter(([, n]) => n > 1));
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const since = Math.floor(Date.now() / 1000) - 90 * 86400;

  let total = 0;
  let orphans = 0;
  let orphanAmount = 0;
  let unsaveable = 0;
  for await (const pi of pageAll(key, '/payment_intents', 5000, { 'created[gte]': since })) {
    total += 1;
    if (pi.customer) continue;
    orphans += 1;
    orphanAmount += pi.amount ?? 0;
    if (!pi.setup_future_usage) unsaveable += 1;
  }

  const repeats = await repeatCards(key, since);
  const [state, detail] = verdict(total, orphans, repeats.size);

  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'clear' || state === 'unknown') { console.log(line); return; }

  console.warn(line);
  console.warn(`  ${orphanAmount} in the smallest currency unit is unattributed to anyone`);
  console.warn(`  ${unsaveable} of the orphans also had no setup_future_usage, so the ` +
               'card was discarded too');
  for (const [fp, n] of [...repeats].sort((a, b) => b[1] - a[1]).slice(0, 10)) {
    console.warn(`  fingerprint ${fp} paid ${n} times as a stranger`);
  }
  console.warn('  repair: look the customer up before creating the intent');
  console.warn(`  POST ${API}/payment_intents -d customer=cus_XXX -d setup_future_usage=off_session`);
  console.warn('  in Checkout: pass an existing customer, or customer_creation=always');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters is the small one: a handful of orphaned payments among thousands is unremarkable until one card appears twice in it, at which point the share stops being the story. The classifier has to rank the fingerprint evidence above the percentage even when the percentage is tiny.",
"test_py_file": "test_stripe_orphan_payments.py",
"test_py": '''from stripe_orphan_payments import verdict


def test_a_repeat_fingerprint_outranks_a_tiny_share():
    # 6 of 4000 is noise. One of those cards paying twice is not.
    state, detail = verdict(4000, 6, 2)
    assert state == "repeat"
    assert "2" in detail


def test_majority_orphaned_means_guest_checkout_is_the_default():
    assert verdict(1000, 499, 0)[0] == "guests"
    state, _ = verdict(1000, 500, 0)
    assert state == "dominant"


def test_a_few_orphans_are_reported_without_alarm():
    state, detail = verdict(1000, 30, 0)
    assert state == "guests"
    assert "deliberate" in detail


def test_every_intent_attached_is_clear():
    assert verdict(1000, 0, 0)[0] == "clear"


def test_an_empty_window_is_not_silently_clear():
    assert verdict(0, 0, 0)[0] == "unknown"
''',
"test_js_file": "stripe-orphan-payments.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-orphan-payments.mjs';

test('a repeat fingerprint outranks a tiny share', () => {
  const [state, detail] = verdict(4000, 6, 2);
  assert.equal(state, 'repeat');
  assert.match(detail, /2/);
});

test('majority orphaned means guest checkout is the default', () => {
  assert.equal(verdict(1000, 499, 0)[0], 'guests');
  assert.equal(verdict(1000, 500, 0)[0], 'dominant');
});

test('a few orphans are reported without alarm', () => {
  const [state, detail] = verdict(1000, 30, 0);
  assert.equal(state, 'guests');
  assert.match(detail, /deliberate/);
});

test('every intent attached is clear', () => {
  assert.equal(verdict(1000, 0, 0)[0], 'clear');
});

test('an empty window is not silently clear', () => {
  assert.equal(verdict(0, 0, 0)[0], 'unknown');
});
''',
"faq": [
 ("Is guest checkout wrong?",
  "No. It is a deliberate product decision and it lifts conversion for one-off purchases. The problem is guest checkout by accident: an integration that never passes a customer because nobody chose to, which quietly forfeits saved cards, payment history and the returning-buyer signal Radar uses."),
 ("How reliable is the card fingerprint for grouping?",
  "It is stable for one card number across payments and across accounts, which makes it good evidence of a repeat purchase. It changes when the card is reissued and it is shared by anyone using the same physical card, so treat a match as strong evidence of a returning buyer and never as an identity."),
 ("Does attaching a Customer save the card automatically?",
  "No, those are two parameters. customer links the payment to a person; setup_future_usage is what stores the credential for reuse. A PaymentIntent can have the first without the second, which is a separate and very common way to lose a card."),
 ("What about Checkout Sessions specifically?",
  "A Session with no customer and no customer_creation setting completes the payment and creates nothing reusable, even though it collected an email. Pass an existing customer where you have one, or set customer_creation=always so the Session produces a record you can charge again."),
 ("Can I detect this with a restricted key?",
  "Yes. Read access to PaymentIntents and Charges is all this script uses. Give it nothing more, and a leak costs you a list of payment amounts rather than the ability to move money."),
],
"related": [
 ("/stripe/customers-missing-email/", "Customers have no email, so Stripe sends no receipts"),
 ("/stripe/duplicate-customers-same-email/", "Duplicate customers share an email and split billing"),
 ("/stripe/unattached-payment-methods-orphaned/", "PaymentMethods are created but never attached to a customer"),
],
"citations": [CITE_PI_OBJ, CITE_PI_CREATE, CITE_CHARGE_OBJ, CITE_SEARCH],
},

{
"slug": "save-default-payment-method-off",
"title": "save_default_payment_method off orphans the card after payment",
"description": "The first invoice pays and every renewal fails. The card that just worked was never promoted to the subscription's default payment method.",
"h1": "save_default_payment_method off orphans the card after payment",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["save_default_payment_method on_subscription", "stripe subscription renewal fails",
             "stripe default_payment_method null", "stripe payment_settings subscription",
             "stripe first invoice paid renewal failed"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The signup works end to end. The customer enters a card, the first invoice is paid, the subscription goes active, and everyone moves on. A month later the renewal fails and the subscription has nothing on it to charge. The card that paid the first invoice is not gone &mdash; it was simply never made the subscription's default, because a flag nobody set defaults to off.",
"short_answer": """<p>Page <code>GET /v1/subscriptions?status=active&amp;expand[]=data.customer</code> and look for three things being true at once: <code>payment_settings.save_default_payment_method</code> is <code>off</code> or absent, <code>default_payment_method</code> on the subscription is <code>null</code>, and <code>customer.invoice_settings.default_payment_method</code> is <code>null</code> too. That subscription has nothing to charge at renewal.</p>
<p>Read <code>past_due</code> and <code>unpaid</code> in the same pass. Any subscription in that state with the same three conditions is not at risk; it has already failed.</p>""",
"problem": """<p>The confusing part is that the first payment genuinely worked. A card was collected, confirmed against the first invoice's PaymentIntent, and charged. It just was not kept: paying an invoice does not attach the payment method to anything, and unless you asked for it to be saved, the subscription ends its first cycle with the same empty <code>default_payment_method</code> it started with.</p>
<p>Whether that matters depends entirely on the customer having a default set elsewhere. Integrations that also write <code>invoice_settings.default_payment_method</code> on the Customer never notice, because renewals quietly fall back to it. Integrations that do not have a working first month and a dead second one, and the bug reaches production because nobody waits a billing cycle before shipping.</p>""",
"why": """<p><strong>The default is <code>off</code>, and an unset field reads as null.</strong> <code>payment_settings.save_default_payment_method</code> is not something you turn off; it is something you have to turn on. A subscription created without the parameter comes back with the field absent, which any check comparing against the string <code>"off"</code> will treat as fine.</p>
<p><strong>Paying an invoice is not saving a card.</strong> Confirming the first invoice's PaymentIntent charges the card and finishes. Storing it for reuse is a separate instruction, and the subscription-level way to give it is this flag. Doing it by hand afterwards means listening for the right event and writing the payment method back, which is more code and more places to fail.</p>
<p><strong>The fallback masks the bug until it does not.</strong> When the Customer has an <code>invoice_settings.default_payment_method</code>, renewals work and the flag never matters. Change the signup flow so the Customer default is no longer written &mdash; a refactor, a new plan, a Checkout migration &mdash; and every subscription created after that date fails at its second invoice while the older ones carry on fine.</p>
<p><strong>The gap between cause and symptom is a full billing period.</strong> Monthly plans give you thirty days, annual plans give you a year. Nothing in the signup logs, the tests or the Dashboard hints at it during that time, because at every moment before the renewal the subscription is genuinely healthy.</p>""",
"steps": [
 {"h": "Read the flag and both defaults in one pass",
  "body": """<p>Expand the customer: <code>GET /v1/subscriptions?status=active&amp;limit=100&amp;expand[]=data.customer</code>. You need <code>payment_settings.save_default_payment_method</code>, <code>default_payment_method</code> and <code>customer.invoice_settings.default_payment_method</code> together, and expanding avoids a request per subscription.</p>"""},
 {"h": "Treat an absent flag as off",
  "body": """<p>Stripe omits the field when it was never set, which is the overwhelmingly common case. A classifier that only recognises the literal string <code>"off"</code> will report every affected subscription as fine, which is the single most likely way to write this check and get a clean bill of health from a broken account.</p>"""},
 {"h": "Separate the ones that are covered from the ones that are exposed",
  "body": """<p>The flag being off is not itself a fault. A subscription with a <code>default_payment_method</code> already set is fine; one with a customer-level default will fall back and also be fine. Only the subscription with neither has nothing to charge, and that is the list worth acting on.</p>"""},
 {"h": "Page past_due and unpaid as well as active",
  "body": """<p><code>status=active</code> shows you the ones that are about to fail. The same three conditions on a <code>past_due</code> or <code>unpaid</code> subscription mean it already has, and those need an email to the customer rather than a code change.</p>"""},
 {"h": "Set it at creation, and fix the existing ones in place",
  "body": """<p>New subscriptions: <code>POST /v1/subscriptions</code> with <code>payment_settings[save_default_payment_method]=on_subscription</code>. Existing ones are updatable, including while <code>incomplete</code>, so setting it before the next invoice is enough for anything that has not yet renewed. Subscriptions already <code>past_due</code> need a payment method attached too; the flag alone has nothing to save.</p>"""},
],
"verify": """<p>Re-run the script. Every active subscription should classify as <code>on</code> or <code>saved</code>, with none left stranded.</p>
<pre><code class="language-bash">python3 stripe_save_default_pm.py
# 318 subscription(s), 0 stranded, 0 already failing</code></pre>""",
"code_intro": "One paginated GET per status and no writes &mdash; a restricted key with read access to Subscriptions and Customers is enough, and is what you should give it. The classifier takes a whole subscription rather than a set of counts, because the interesting cases are the shapes the object can arrive in: the flag absent rather than <code>\"off\"</code>, and the customer left unexpanded, which looks exactly like a customer with no default unless you check.",
"py_file": "stripe_save_default_pm.py",
"py": '''"""Report Stripe subscriptions that will have nothing to charge at renewal.

Read only. One paginated GET per status, no writes: give this a RESTRICTED key
with read access to Subscriptions and Customers. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_save_default_pm")

API = "https://api.stripe.com/v1"

FAILED_STATUSES = ("past_due", "unpaid")


def verdict(subscription):
    """Classify one subscription. Pure, so the rules can be tested without a network.

    Returns (state, detail). The subscription's `customer` must be expanded; when
    it is only an id there is no way to know whether a customer-level default
    exists, and guessing either way is worse than saying so.
    """
    settings = subscription.get("payment_settings") or {}
    save = settings.get("save_default_payment_method")

    # Absent is the same as "off": Stripe omits the field when it was never set,
    # which is how almost every affected subscription actually looks.
    if save not in (None, "off", "on_subscription"):
        return ("unknown", "unrecognised save_default_payment_method %r" % (save,))
    if save == "on_subscription":
        return ("on", "the card that pays an invoice becomes the subscription default")

    if subscription.get("default_payment_method"):
        return ("saved", "the flag is off, but a default is already set on the "
                         "subscription")

    customer = subscription.get("customer")
    if not isinstance(customer, dict):
        return ("unknown",
                "customer is not expanded, so the fallback default cannot be read; "
                "re-read with expand[]=data.customer")

    invoice_settings = customer.get("invoice_settings") or {}
    if invoice_settings.get("default_payment_method"):
        return ("fallback",
                "nothing on the subscription; renewals fall back to the customer "
                "default. Working, and one refactor away from not working.")

    if subscription.get("status") in FAILED_STATUSES:
        return ("failing",
                "status %s with no payment method on the subscription and none on "
                "the customer. The renewal has already failed."
                % subscription.get("status"))

    return ("stranded",
            "no payment method on the subscription and none on the customer. The "
            "next renewal has nothing to charge.")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    seen = 0
    params = dict(params, limit=100)
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=5000,
                    help="stop paginating each status after this many subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    counts = {}
    flagged = []
    total = 0
    for status in ("active",) + FAILED_STATUSES:
        for sub in page_all(s, "/subscriptions", args.max_subscriptions,
                            status=status, **{"expand[]": "data.customer"}):
            total += 1
            state, detail = verdict(sub)
            counts[state] = counts.get(state, 0) + 1
            if state in ("stranded", "failing", "unknown"):
                flagged.append((state, sub["id"], detail))

    if not total:
        log.info("no subscriptions for this key's mode")
        return 0

    for state, sub_id, detail in flagged[:25]:
        log.warning("%-9s %s  %s", state, sub_id, detail)
        log.warning("  repair: POST %s/subscriptions/%s "
                    "-d \\"payment_settings[save_default_payment_method]=on_subscription\\"",
                    API, sub_id)

    bad = counts.get("stranded", 0) + counts.get("failing", 0)
    if counts.get("fallback"):
        log.info("%d subscription(s) rely on the customer default; they work until "
                 "the signup flow stops writing it", counts["fallback"])
    log.info("%d subscription(s), %d stranded, %d already failing",
             total, counts.get("stranded", 0), counts.get("failing", 0))
    if not bad:
        return 0
    log.warning("set it at creation so this stops recurring:")
    log.warning("  POST %s/subscriptions "
                "-d \\"payment_settings[save_default_payment_method]=on_subscription\\"",
                API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-save-default-pm.mjs",
"js": '''/**
 * Report Stripe subscriptions that will have nothing to charge at renewal.
 *
 * Read only. One paginated GET per status, no writes: give this a RESTRICTED key
 * with read access to Subscriptions and Customers. The repair is printed, never
 * performed.
 */
const API = 'https://api.stripe.com/v1';

export const FAILED_STATUSES = ['past_due', 'unpaid'];

/**
 * Classify one subscription. Pure, so the rules can be tested without a network.
 *
 * The subscription's `customer` must be expanded; when it is only an id there is
 * no way to know whether a customer-level default exists, and guessing either way
 * is worse than saying so.
 */
export function verdict(subscription) {
  const settings = subscription.payment_settings ?? {};
  const save = settings.save_default_payment_method;

  // Absent is the same as 'off': Stripe omits the field when it was never set,
  // which is how almost every affected subscription actually looks.
  if (save !== undefined && save !== null && save !== 'off' && save !== 'on_subscription') {
    return ['unknown', `unrecognised save_default_payment_method ${JSON.stringify(save)}`];
  }
  if (save === 'on_subscription') {
    return ['on', 'the card that pays an invoice becomes the subscription default'];
  }

  if (subscription.default_payment_method) {
    return ['saved', 'the flag is off, but a default is already set on the subscription'];
  }

  const customer = subscription.customer;
  if (!customer || typeof customer !== 'object') {
    return ['unknown',
      'customer is not expanded, so the fallback default cannot be read; ' +
      're-read with expand[]=data.customer'];
  }

  if (customer.invoice_settings?.default_payment_method) {
    return ['fallback',
      'nothing on the subscription; renewals fall back to the customer default. ' +
      'Working, and one refactor away from not working.'];
  }

  if (FAILED_STATUSES.includes(subscription.status)) {
    return ['failing',
      `status ${subscription.status} with no payment method on the subscription ` +
      'and none on the customer. The renewal has already failed.'];
  }

  return ['stranded',
    'no payment method on the subscription and none on the customer. The next ' +
    'renewal has nothing to charge.'];
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

async function* pageAll(key, path, limit, params = {}) {
  let seen = 0;
  const p = { ...params, limit: 100 };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const obj of data) { yield obj; seen += 1; }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    p.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const counts = new Map();
  const flagged = [];
  let total = 0;
  for (const status of ['active', ...FAILED_STATUSES]) {
    for await (const sub of pageAll(key, '/subscriptions', 5000,
      { status, 'expand[]': 'data.customer' })) {
      total += 1;
      const [state, detail] = verdict(sub);
      counts.set(state, (counts.get(state) ?? 0) + 1);
      if (state === 'stranded' || state === 'failing' || state === 'unknown') {
        flagged.push([state, sub.id, detail]);
      }
    }
  }

  if (!total) {
    console.log("no subscriptions for this key's mode");
    return;
  }

  for (const [state, id, detail] of flagged.slice(0, 25)) {
    console.warn(`${state.padEnd(9)} ${id}  ${detail}`);
    console.warn(`  repair: POST ${API}/subscriptions/${id} ` +
                 '-d "payment_settings[save_default_payment_method]=on_subscription"');
  }

  const stranded = counts.get('stranded') ?? 0;
  const failing = counts.get('failing') ?? 0;
  if (counts.get('fallback')) {
    console.log(`${counts.get('fallback')} subscription(s) rely on the customer ` +
                'default; they work until the signup flow stops writing it');
  }
  console.log(`${total} subscription(s), ${stranded} stranded, ${failing} already failing`);
  if (!(stranded + failing)) return;
  console.warn('set it at creation so this stops recurring:');
  console.warn(`  POST ${API}/subscriptions ` +
               '-d "payment_settings[save_default_payment_method]=on_subscription"');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these tests exist because of how the object arrives rather than what it means. An absent <code>save_default_payment_method</code> is the same as <code>\"off\"</code> and is how nearly every affected subscription looks; an unexpanded <code>customer</code> is a string that a naive read turns into a false clean result. Both are the difference between a check that finds this and one that reports zero forever.",
"test_py_file": "test_stripe_save_default_pm.py",
"test_py": '''from stripe_save_default_pm import verdict


def sub(**over):
    base = {"id": "sub_1", "status": "active", "payment_settings": {},
            "default_payment_method": None,
            "customer": {"id": "cus_1", "invoice_settings": {}}}
    base.update(over)
    return base


def test_an_absent_flag_is_treated_as_off():
    # Stripe omits the field when it was never set. This is the common shape.
    state, _ = verdict(sub(payment_settings={}))
    assert state == "stranded"


def test_an_explicit_off_reaches_the_same_verdict():
    assert verdict(sub(payment_settings={"save_default_payment_method": "off"}))[0] \\
        == "stranded"


def test_on_subscription_is_the_fix():
    state, _ = verdict(sub(payment_settings={"save_default_payment_method": "on_subscription"}))
    assert state == "on"


def test_a_subscription_default_makes_the_flag_moot():
    assert verdict(sub(default_payment_method="pm_1"))[0] == "saved"


def test_a_customer_default_is_a_fallback_not_a_fix():
    state, detail = verdict(sub(customer={"id": "cus_1",
                                          "invoice_settings": {"default_payment_method": "pm_2"}}))
    assert state == "fallback"
    assert "refactor" in detail


def test_past_due_with_nothing_to_charge_has_already_failed():
    state, _ = verdict(sub(status="past_due"))
    assert state == "failing"


def test_an_unexpanded_customer_is_not_silently_stranded():
    # A bare id looks exactly like a customer with no default. Say so instead.
    state, detail = verdict(sub(customer="cus_1"))
    assert state == "unknown"
    assert "expand" in detail


def test_an_unrecognised_value_is_not_silently_healthy():
    assert verdict(sub(payment_settings={"save_default_payment_method": "always"}))[0] \\
        == "unknown"
''',
"test_js_file": "stripe-save-default-pm.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-save-default-pm.mjs';

function sub(over = {}) {
  return {
    id: 'sub_1',
    status: 'active',
    payment_settings: {},
    default_payment_method: null,
    customer: { id: 'cus_1', invoice_settings: {} },
    ...over,
  };
}

test('an absent flag is treated as off', () => {
  assert.equal(verdict(sub({ payment_settings: {} }))[0], 'stranded');
});

test('an explicit off reaches the same verdict', () => {
  assert.equal(
    verdict(sub({ payment_settings: { save_default_payment_method: 'off' } }))[0],
    'stranded');
});

test('on_subscription is the fix', () => {
  assert.equal(
    verdict(sub({ payment_settings: { save_default_payment_method: 'on_subscription' } }))[0],
    'on');
});

test('a subscription default makes the flag moot', () => {
  assert.equal(verdict(sub({ default_payment_method: 'pm_1' }))[0], 'saved');
});

test('a customer default is a fallback not a fix', () => {
  const [state, detail] = verdict(sub({
    customer: { id: 'cus_1', invoice_settings: { default_payment_method: 'pm_2' } },
  }));
  assert.equal(state, 'fallback');
  assert.match(detail, /refactor/);
});

test('past_due with nothing to charge has already failed', () => {
  assert.equal(verdict(sub({ status: 'past_due' }))[0], 'failing');
});

test('an unexpanded customer is not silently stranded', () => {
  const [state, detail] = verdict(sub({ customer: 'cus_1' }));
  assert.equal(state, 'unknown');
  assert.match(detail, /expand/);
});

test('an unrecognised value is not silently healthy', () => {
  assert.equal(
    verdict(sub({ payment_settings: { save_default_payment_method: 'always' } }))[0],
    'unknown');
});
''',
"faq": [
 ("What does save_default_payment_method=on_subscription actually do?",
  "When an invoice for that subscription is paid, the payment method used is written to the subscription's default_payment_method. Renewals then charge it directly. With the flag off, the card pays the invoice and is never promoted, so the subscription keeps whatever default it had, which is usually nothing."),
 ("Why does the first invoice succeed if there is no payment method?",
  "Because the first invoice is paid by a PaymentIntent confirmed in the browser with a card the customer just entered. That confirmation is a one-off. Renewals are unattended and have to read a stored default, which is a completely different mechanism to the one that made the first payment work."),
 ("Can I set the flag on subscriptions that already exist?",
  "Yes, including while the subscription is incomplete. It takes effect from the next invoice, so anything that has not yet renewed is fixed by the update alone. Subscriptions already past_due need a payment method attached as well, because there is no successful invoice left for the flag to learn from."),
 ("Is setting invoice_settings.default_payment_method on the Customer enough instead?",
  "It works, and it is what silently rescues most integrations that never set this flag. It is fragile for a different reason: the subscription depends on a field maintained elsewhere, so the day the signup flow stops writing it, every subscription created after that date fails at its second invoice while the older ones carry on."),
 ("Does this check need write access?",
  "No. It reads Subscriptions with the Customer expanded and nothing else. Give it a restricted key with read access to Subscriptions and Customers, and run the printed update yourself."),
],
"related": [
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
 ("/stripe/dunning-retries-exhausted/", "Dunning ran out of retries and no attempt is scheduled"),
 ("/stripe/subscriptions-stuck-incomplete/", "Incomplete subscriptions die silently after 23 hours"),
],
"citations": [CITE_SUB_OBJ, CITE_SUB_CREATE, CITE_SUB_UPDATE, CITE_SAVE_REUSE],
},

]
