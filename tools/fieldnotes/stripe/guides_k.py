#!/usr/bin/env python3
"""/stripe/ field notes, batch K — payments and intents.

Four ways a payment silently never happens: the deploy is transacting in the
wrong mode, the intent was created with a hardcoded method list, the saved card
has no mandate behind it, or the domain serving checkout was never registered so
the wallet is filtered out before it can render.

Same constraint as the rest of the section. Every script here reads and nothing
else. They hold a credential to a live payments account, so they report what is
wrong and print the repair for a human to run.
"""

CITE_DECLINE_CODES = ("Decline codes — Stripe Docs", "https://docs.stripe.com/declines/codes")
CITE_ERROR_CODES = ("Error codes — Stripe Docs", "https://docs.stripe.com/error-codes")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")
CITE_ACCOUNT_OBJ = ("The account object — Stripe API reference",
                    "https://docs.stripe.com/api/accounts/object")
CITE_PI_OBJ = ("The PaymentIntent object — Stripe API reference",
               "https://docs.stripe.com/api/payment_intents/object")
CITE_DPM = ("Dynamic payment methods — Stripe Docs",
            "https://docs.stripe.com/payments/payment-methods/dynamic-payment-methods")
CITE_PMC_OBJ = ("The payment method configuration object — Stripe API reference",
                "https://docs.stripe.com/api/payment_method_configurations/object")
CITE_SCA = ("Strong Customer Authentication — Stripe Docs",
            "https://docs.stripe.com/strong-customer-authentication")
CITE_SI_OBJ = ("The SetupIntent object — Stripe API reference",
               "https://docs.stripe.com/api/setup_intents/object")
CITE_SAVE_DURING = ("Save a card during a payment — Stripe Docs",
                    "https://docs.stripe.com/payments/save-during-payment")
CITE_PMD_OBJ = ("The payment method domain object — Stripe API reference",
                "https://docs.stripe.com/api/payment_method_domains/object")
CITE_PMD_REG = ("Payment method domain registration — Stripe Docs",
                "https://docs.stripe.com/payments/payment-methods/pmd-registration")
CITE_APPLE_PAY = ("Apple Pay — Stripe Docs", "https://docs.stripe.com/apple-pay")

GUIDES = [

{
"slug": "testmode-decline-in-live-mode",
"title": "Live charges fail with testmode_decline from test cards",
"description": "Real customers get card declined in production. The decline_code is testmode_decline: the deploy carries test keys, or a test-mode ID is hardcoded.",
"h1": "live charges fail with testmode_decline from test cards",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe testmode_decline", "stripe test card in live mode",
             "a similar object exists in test mode but a live mode key was used",
             "stripe resource_missing live key", "stripe charges_enabled false"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A customer writes in to say their card was declined. You try it yourself with 4242&nbsp;4242&nbsp;4242&nbsp;4242 and it works fine, so you tell them to call their bank. It is not their bank. The charge failed with <code>testmode_decline</code>, which is Stripe saying that something in the request belonged to test mode and the request did not &mdash; and the card that &ldquo;works fine&rdquo; is the reason you cannot see it.",
"short_answer": """<p>Read <code>GET /v1/charges</code> and count <code>failure_code</code> or <code>outcome.reason</code> equal to <code>testmode_decline</code>, and <code>GET /v1/payment_intents</code> for the same value in <code>last_payment_error.code</code>. Any non-zero count means a test artefact reached production.</p>
<p>Read <code>GET /v1/account</code> as well. If <code>charges_enabled</code> or <code>details_submitted</code> is <code>false</code>, the account was never activated and is restricted to test-mode charges no matter which key you send.</p>""",
"problem": """<p>Three unrelated mistakes produce the same symptom, which is why this one takes so long to place. A deploy can ship <code>sk_test_…</code> on the server, or ship a live secret key beside a test publishable key so the token created in the browser is never valid for the charge. A seeded price, product or customer ID from the sandbox can be hardcoded in a config file, in which case every live call returns <code>resource_missing</code> with the famously unhelpful &ldquo;a similar object exists in test mode, but a live mode key was used&rdquo;. Or the account was never finished, so Stripe accepts the live key and still refuses to take money with it.</p>
<p>The reason it survives testing is that all of your own testing is done with test cards, which behave perfectly in the broken configuration. The failure is only visible to people paying with real cards, and they do not file bug reports &mdash; they leave.</p>""",
"why": """<p><strong>The two modes are separate databases with separate IDs.</strong> A test-mode customer ID does not exist in live mode and never will. Stripe is not being pedantic when it rejects it; there is genuinely nothing there. The error message mentions the object existing in the other mode because that is the only useful thing it can say.</p>
<p><strong>Key pairs get split during a rotation.</strong> The secret key lives in the server environment and the publishable key lives in the frontend build, and they are usually rotated by different people at different times. A live secret with a test publishable key fails on every real payment and on none of your smoke tests.</p>
<p><strong>Activation is a separate thing from having keys.</strong> An account that has not submitted its details still issues live keys and still answers API calls. It just cannot charge anyone, and the condition it reports for that is a decline rather than an error.</p>""",
"steps": [
 {"h": "Establish which mode the key is really in",
  "body": """<p>Read it off the prefix before you read anything else. A key containing <code>_live_</code> is a live key; anything else is test. Half of the time this single line ends the investigation, because the environment variable in production turns out to hold a test key that someone pasted in during an incident and never replaced.</p>"""},
 {"h": "Ask the account whether it can charge at all",
  "body": """<p><code>GET /v1/account</code> returns <code>charges_enabled</code> and <code>details_submitted</code>. Both must be <code>true</code>. If either is <code>false</code> the account is in the <code>testmode_charges_only</code> condition and the keys are irrelevant &mdash; the onboarding is unfinished.</p>"""},
 {"h": "Count the declines that name themselves",
  "body": """<p>Stripe records this condition in three places depending on which object you read: <code>charge.failure_code</code>, <code>charge.outcome.reason</code>, and <code>payment_intent.last_payment_error.code</code>. A check that reads only one of them under-counts, because which fields are populated depends on how far the payment got.</p>"""},
 {"h": "Treat an empty live account as a positive result",
  "body": """<p>If a live key returns zero charges, zero PaymentIntents and zero customers while the business is demonstrably taking orders, nothing is failing in live mode because nothing is happening in live mode. The application is writing to test, and the dashboard everyone is looking at is the test dashboard.</p>"""},
 {"h": "Stop hardcoding IDs that only exist in one mode",
  "body": """<p>Price and product IDs are the usual offenders because they are stable enough to look like configuration. Look them up by <code>lookup_key</code> instead, so the same code resolves to the right object in whichever mode it is running.</p>"""},
],
"verify": """<p>Re-run the script against production. The mode should be live, the account should be activated, and the decline count should be zero.</p>
<pre><code class="language-bash">python3 stripe_live_mode_check.py
# healthy   live objects exist and no testmode_decline in the window</code></pre>""",
"code_intro": "Four GET requests and no writes. A restricted key with read access to Account, Charges, PaymentIntents and Customers is enough, and is what you should give it. The classification is split into two pure functions: one that knows where Stripe hides this decline, and one that decides what the counts mean.",
"py_file": "stripe_live_mode_check.py",
"py": '''"""Report whether a live Stripe key is actually transacting in live mode.

Read only. Four GET requests, no writes: give this a RESTRICTED key with read
access to Account, Charges, PaymentIntents and Customers. The repair is printed,
never performed, because this script holds a credential to a live payments
account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_live_mode_check")

API = "https://api.stripe.com/v1"
TESTMODE = "testmode_decline"


def count_testmode_declines(charges, intents):
    """Count objects that failed because a test artefact reached live mode.

    Pure, so the rules can be tested without a network. Stripe records this one
    condition in three different fields depending on how far the payment got: a
    charge carries it as `failure_code` and again as `outcome.reason`, while a
    PaymentIntent that never produced a charge carries it as
    `last_payment_error.code`. Reading only one of them under-counts.
    """
    n = 0
    for c in charges:
        outcome = c.get("outcome") or {}
        if c.get("failure_code") == TESTMODE or outcome.get("reason") == TESTMODE:
            n += 1
    for pi in intents:
        err = pi.get("last_payment_error") or {}
        if err.get("code") == TESTMODE:
            n += 1
    return n


def verdict(key_mode, account, counts):
    """Classify one account. Pure.

    key_mode is "live" or "test", taken from the key prefix. counts holds how
    many objects of each kind this key could see, plus the decline tally.
    """
    if key_mode != "live":
        return ("test_key",
                "this is a test-mode key, so it cannot see the live account at "
                "all: run it again with a restricted live key")
    if not account.get("details_submitted") or not account.get("charges_enabled"):
        return ("not_activated",
                "activation is unfinished, so the account is limited to "
                "test-mode charges: charges_enabled=%s details_submitted=%s"
                % (account.get("charges_enabled"), account.get("details_submitted")))
    if counts.get("testmode_declines"):
        return ("test_cards_live",
                "%d live payment(s) failed with testmode_decline: a test card "
                "number or a test-mode object id reached production"
                % counts["testmode_declines"])
    if not any(counts.get(k, 0) for k in ("charges", "payment_intents", "customers")):
        return ("pointed_at_test",
                "the live account holds no charges, intents or customers: the "
                "application is transacting in test mode")
    return ("healthy", "live objects exist and no testmode_decline in the window")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to " + path)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=100,
                    help="objects to read per resource (1-100)")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    mode = "live" if "_live_" in key else "test"
    account = get(s, "/account")
    charges = get(s, "/charges", limit=args.limit).get("data", [])
    intents = get(s, "/payment_intents", limit=args.limit).get("data", [])
    customers = get(s, "/customers", limit=args.limit).get("data", [])

    counts = {
        "charges": len(charges),
        "payment_intents": len(intents),
        "customers": len(customers),
        "testmode_declines": count_testmode_declines(charges, intents),
    }

    state, detail = verdict(mode, account, counts)
    line = "%-16s %s" % (state, detail)
    if state == "healthy":
        log.info(line)
        return 0

    log.warning(line)
    if state == "test_key":
        log.warning("  repair: export a restricted key beginning rk_live_ and re-run")
        return 2
    if state == "not_activated":
        log.warning("  repair: finish activation at "
                    "https://dashboard.stripe.com/account/onboarding until "
                    "charges_enabled is true")
    else:
        log.warning("  repair: put a matching sk_live_ and pk_live_ pair from the "
                    "same account on server and client")
        log.warning("  repair: remove hardcoded test-mode ids; resolve prices by "
                    "lookup_key so one code path works in both modes")
    log.info("read %d charge(s), %d intent(s), %d customer(s) in %s mode",
             counts["charges"], counts["payment_intents"], counts["customers"], mode)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-live-mode-check.mjs",
"js": '''/**
 * Report whether a live Stripe key is actually transacting in live mode.
 *
 * Read only. Four GET requests, no writes: give this a RESTRICTED key with read
 * access to Account, Charges, PaymentIntents and Customers. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const TESTMODE = 'testmode_decline';

/**
 * Count objects that failed because a test artefact reached live mode. Pure.
 *
 * Stripe records this one condition in three fields depending on how far the
 * payment got, so reading only one of them under-counts.
 */
export function countTestmodeDeclines(charges, intents) {
  let n = 0;
  for (const c of charges) {
    const outcome = c.outcome ?? {};
    if (c.failure_code === TESTMODE || outcome.reason === TESTMODE) n += 1;
  }
  for (const pi of intents) {
    const err = pi.last_payment_error ?? {};
    if (err.code === TESTMODE) n += 1;
  }
  return n;
}

/**
 * Classify one account. Pure.
 */
export function verdict(keyMode, account, counts) {
  if (keyMode !== 'live') {
    return ['test_key',
      'this is a test-mode key, so it cannot see the live account at all: run ' +
      'it again with a restricted live key'];
  }
  if (!account.details_submitted || !account.charges_enabled) {
    return ['not_activated',
      'activation is unfinished, so the account is limited to test-mode ' +
      `charges: charges_enabled=${account.charges_enabled} ` +
      `details_submitted=${account.details_submitted}`];
  }
  if (counts.testmode_declines) {
    return ['test_cards_live',
      `${counts.testmode_declines} live payment(s) failed with testmode_decline: ` +
      'a test card number or a test-mode object id reached production'];
  }
  const seen = (counts.charges ?? 0) + (counts.payment_intents ?? 0) +
               (counts.customers ?? 0);
  if (!seen) {
    return ['pointed_at_test',
      'the live account holds no charges, intents or customers: the ' +
      'application is transacting in test mode'];
  }
  return ['healthy', 'live objects exist and no testmode_decline in the window'];
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

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const mode = key.includes('_live_') ? 'live' : 'test';
  const account = await get(key, '/account');
  const { data: charges = [] } = await get(key, '/charges', { limit: 100 });
  const { data: intents = [] } = await get(key, '/payment_intents', { limit: 100 });
  const { data: customers = [] } = await get(key, '/customers', { limit: 100 });

  const counts = {
    charges: charges.length,
    payment_intents: intents.length,
    customers: customers.length,
    testmode_declines: countTestmodeDeclines(charges, intents),
  };

  const [state, detail] = verdict(mode, account, counts);
  const line = `${state.padEnd(16)} ${detail}`;
  if (state === 'healthy') { console.log(line); return; }

  console.warn(line);
  if (state === 'test_key') {
    console.warn('  repair: export a restricted key beginning rk_live_ and re-run');
    process.exitCode = 2;
    return;
  }
  if (state === 'not_activated') {
    console.warn('  repair: finish activation at ' +
      'https://dashboard.stripe.com/account/onboarding until charges_enabled is true');
  } else {
    console.warn('  repair: put a matching sk_live_ and pk_live_ pair from the ' +
      'same account on server and client');
    console.warn('  repair: remove hardcoded test-mode ids; resolve prices by ' +
      'lookup_key so one code path works in both modes');
  }
  console.log(`read ${counts.charges} charge(s), ${counts.payment_intents} intent(s), ` +
              `${counts.customers} customer(s) in ${mode} mode`);
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. One is the charge that only reports the condition in <code>outcome.reason</code> and not in <code>failure_code</code>, because a counter that reads a single field is the reason people conclude &ldquo;no test declines&rdquo; and go looking elsewhere for a day. The other is the silent one: a live key with an activated account and nothing at all behind it, which is not healthy and has to say so.",
"test_py_file": "test_stripe_live_mode_check.py",
"test_py": '''from stripe_live_mode_check import count_testmode_declines, verdict

LIVE = {"charges_enabled": True, "details_submitted": True}
BUSY = {"charges": 40, "payment_intents": 40, "customers": 12}


def test_counts_a_charge_that_only_names_it_in_outcome_reason():
    # failure_code is absent here; a counter reading one field misses this.
    charges = [{"outcome": {"reason": "testmode_decline"}}]
    assert count_testmode_declines(charges, []) == 1


def test_counts_an_intent_that_never_produced_a_charge():
    intents = [{"last_payment_error": {"code": "testmode_decline"}}]
    assert count_testmode_declines([], intents) == 1


def test_ordinary_declines_are_not_counted():
    charges = [{"failure_code": "card_declined",
                "outcome": {"reason": "insufficient_funds"}}]
    assert count_testmode_declines(charges, []) == 0


def test_a_test_key_short_circuits_every_other_rule():
    state, detail = verdict("test", {"charges_enabled": False}, {"testmode_declines": 9})
    assert state == "test_key"
    assert "live key" in detail


def test_unactivated_account_outranks_the_decline_count():
    # The declines are real, but the cause is the unfinished onboarding.
    state, _ = verdict("live", {"charges_enabled": False, "details_submitted": True},
                       {"testmode_declines": 3})
    assert state == "not_activated"


def test_declines_on_an_activated_account_name_the_count():
    state, detail = verdict("live", LIVE, dict(BUSY, testmode_declines=3))
    assert state == "test_cards_live"
    assert "3" in detail


def test_an_empty_live_account_is_not_healthy():
    state, _ = verdict("live", LIVE, {"testmode_declines": 0})
    assert state == "pointed_at_test"


def test_busy_and_clean_is_healthy():
    state, _ = verdict("live", LIVE, dict(BUSY, testmode_declines=0))
    assert state == "healthy"
''',
"test_js_file": "stripe-live-mode-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countTestmodeDeclines, verdict } from './stripe-live-mode-check.mjs';

const LIVE = { charges_enabled: true, details_submitted: true };
const BUSY = { charges: 40, payment_intents: 40, customers: 12 };

test('counts a charge that only names it in outcome.reason', () => {
  assert.equal(countTestmodeDeclines([{ outcome: { reason: 'testmode_decline' } }], []), 1);
});

test('counts an intent that never produced a charge', () => {
  const intents = [{ last_payment_error: { code: 'testmode_decline' } }];
  assert.equal(countTestmodeDeclines([], intents), 1);
});

test('ordinary declines are not counted', () => {
  const charges = [{ failure_code: 'card_declined',
                     outcome: { reason: 'insufficient_funds' } }];
  assert.equal(countTestmodeDeclines(charges, []), 0);
});

test('a test key short circuits every other rule', () => {
  const [state, detail] = verdict('test', { charges_enabled: false },
                                  { testmode_declines: 9 });
  assert.equal(state, 'test_key');
  assert.match(detail, /live key/);
});

test('unactivated account outranks the decline count', () => {
  const [state] = verdict('live', { charges_enabled: false, details_submitted: true },
                          { testmode_declines: 3 });
  assert.equal(state, 'not_activated');
});

test('declines on an activated account name the count', () => {
  const [state, detail] = verdict('live', LIVE, { ...BUSY, testmode_declines: 3 });
  assert.equal(state, 'test_cards_live');
  assert.match(detail, /3/);
});

test('an empty live account is not healthy', () => {
  assert.equal(verdict('live', LIVE, { testmode_declines: 0 })[0], 'pointed_at_test');
});

test('busy and clean is healthy', () => {
  assert.equal(verdict('live', LIVE, { ...BUSY, testmode_declines: 0 })[0], 'healthy');
});
''',
"faq": [
 ("What does testmode_decline actually mean?",
  "That something in the request belonged to the other mode. A test card number, a test token, or a test-mode object id was sent with a live key, so Stripe declined it rather than pretending the object existed. It is never the customer's bank."),
 ("Why does my live key say a similar object exists in test mode?",
  "Because the id you passed is a test-mode id. The two modes are separate datasets with separate ids, and Stripe adds that sentence because the id is well-formed and does exist, just not where you are looking. It is almost always a price or product id copied out of the sandbox into a config file."),
 ("Can this happen even with correct live keys?",
  "Yes, if the account was never activated. charges_enabled and details_submitted stay false until onboarding is finished, and until then the account is restricted to test-mode charges regardless of which key you send. That is why the script reads GET /v1/account before it reads anything else."),
 ("Why do my own tests never catch it?",
  "Because you test with test cards, and test cards work perfectly in the broken configuration. The failure is visible only to real cards, which means only to customers. Reading the live decline counts on a schedule is the substitute for a test you cannot write."),
 ("Do I need a live secret key to run this check?",
  "No. A restricted live key with read access to Account, Charges, PaymentIntents and Customers is enough. It cannot move money if it leaks, and it can still see everything this note depends on."),
],
"related": [
 ("/stripe/card-only-payment-method-types/", "Intents hardcode payment_method_types to card only"),
 ("/stripe/endpoint-api-version-pinned-stale/", "A webhook endpoint is pinned to an ancient api_version"),
 ("/stripe/radar-blocked-payments-ignored/", "Radar blocks payments and nobody reads the block reasons"),
],
"citations": [CITE_DECLINE_CODES, CITE_ERROR_CODES, CITE_ACCOUNT_OBJ, CITE_KEYS],
},

{
"slug": "card-only-payment-method-types",
"title": "Intents hardcode payment_method_types to card only",
"description": "The Payment Element renders a bare card form. An explicit payment_method_types array on the intent bypasses dynamic payment methods entirely.",
"h1": "intents hardcode payment_method_types to card only",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payment element not showing payment options",
             "stripe automatic_payment_methods", "payment_method_types card only",
             "stripe dynamic payment methods not working",
             "stripe link ideal not showing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You turned on iDEAL, Bancontact, Klarna and Link in the Dashboard weeks ago. The toggles are still on. The Payment Element in production still renders one card form, and conversion in the Netherlands is still flat. Nothing is broken and no error is thrown &mdash; the intent told Stripe exactly which methods to offer, and it named one.",
"short_answer": """<p>Read <code>GET /v1/payment_intents</code> and look for <code>automatic_payment_methods</code> of <code>null</code> together with <code>payment_method_types</code> equal to <code>["card"]</code>. That pair means the create call passed an explicit list, and an explicit list turns dynamic payment methods off completely.</p>
<p>Then read <code>GET /v1/payment_method_configurations</code> and compare. Any method with <code>available: true</code> and <code>display_preference.value</code> of <code>"on"</code> that never appears on an intent is a method you switched on and are not offering.</p>""",
"problem": """<p>The Dashboard is not lying to you and neither is the API. The methods really are enabled on the account. They are simply not being asked for, because <code>payment_method_types</code> is an allowlist and Stripe honours it exactly. When the array is present, the payment method configuration, the ordering models and every Dashboard toggle become inert for that intent.</p>
<p>What makes it durable is that the code looks correct. <code>payment_method_types: ['card']</code> was the required parameter for years, it appears in every tutorial written before 2023, and it is the first thing an LLM will hand you if you ask for a PaymentIntent. Nothing about it reads as a mistake in review.</p>
<p>The half-migrated case is worse than the fully broken one. A checkout page gets moved to <code>automatic_payment_methods</code> while the subscription upgrade flow, the invoice pay page and the mobile app keep their hardcoded list. Wallets appear in one place and not another, which everybody attributes to browser support.</p>""",
"why": """<p><strong>An explicit list is a promise Stripe keeps.</strong> There is no merge and no fallback. If you name the methods, you own the list, forever, in every currency and country you later sell into.</p>
<p><strong>The old parameter still works.</strong> Stripe did not deprecate it, because plenty of integrations legitimately need to pin a method. So there is no warning, no deprecation notice in the response, and nothing in the logs.</p>
<p><strong>Eligibility is silent too.</strong> Even with dynamic methods on, a method only renders when the currency, the country and the amount all qualify. That produces the same visible symptom as a hardcoded list, so the two have to be separated before you go changing code &mdash; which is what comparing the enabled set against the offered set actually does.</p>""",
"steps": [
 {"h": "Sample the intents you actually create",
  "body": """<p><code>GET /v1/payment_intents?limit=100&amp;created[gte]={now-30d}</code>, paginated. A month is enough to cover every code path that creates an intent, including the ones that only run at renewal.</p>"""},
 {"h": "Read both fields, not one",
  "body": """<p><code>payment_method_types</code> is always populated, even on a dynamic intent, because Stripe fills it with whatever it resolved. It is <code>automatic_payment_methods</code> being <code>null</code> that proves the list was passed in rather than computed. Judging on the types alone flags healthy intents that happened to resolve to card.</p>"""},
 {"h": "Ask what the account thinks is enabled",
  "body": """<p><code>GET /v1/payment_method_configurations</code>. Each method appears as its own object with <code>available</code> and a <code>display_preference</code>. Use <code>display_preference.value</code>, which is the resolved setting, rather than <code>display_preference.preference</code>, which is only what was requested.</p>"""},
 {"h": "Subtract, and read the remainder carefully",
  "body": """<p>Methods that are enabled and never offered are the finding. If most intents are hardcoded, that is the cause. If none are, the same remainder means an eligibility mismatch instead &mdash; wrong currency, unsupported country, amount below the method's minimum &mdash; and the fix is a different one.</p>"""},
 {"h": "Migrate every creation site, not the busiest one",
  "body": """<p>Drop the array and pass <code>automatic_payment_methods[enabled]=true</code>. If you need to suppress a method for one transaction, use <code>excluded_payment_method_types</code> rather than reinstating an allowlist, so new methods still arrive by default.</p>"""},
],
"verify": """<p>Re-run the script after the migration has been through a release. The hardcoded count should fall to zero and the unused list should empty as real traffic exercises each method.</p>
<pre><code class="language-bash">python3 stripe_payment_method_coverage.py --days 7
# healthy   every enabled method reaches at least one intent</code></pre>""",
"code_intro": "Two GET requests and no writes: a restricted key with read access to PaymentIntents and Payment Method Configurations is enough. The interesting part is that the script separates two problems with the same symptom, so the three pure functions are kept apart &mdash; one decides whether an intent was hardcoded, one reads the account's enabled set, and one weighs them against each other.",
"py_file": "stripe_payment_method_coverage.py",
"py": '''"""Report PaymentIntents that pin payment_method_types instead of using
dynamic payment methods, and enabled methods that never reach a customer.

Read only. Two GET requests, no writes: give this a RESTRICTED key with read
access to PaymentIntents and Payment Method Configurations. The repair is
printed, never performed.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_payment_method_coverage")

API = "https://api.stripe.com/v1"

# Sorted lists, because the comparison below sorts before matching. "card" alone
# is the classic tutorial line; "card" plus "link" is what it becomes after Link
# is switched on and the array is edited rather than removed.
CARD_ONLY = (["card"], ["card", "link"])


def is_card_only(intent):
    """True when this intent pinned an explicit card-only method list. Pure.

    `payment_method_types` is populated on every intent, dynamic or not, because
    Stripe fills it with whatever it resolved. Only `automatic_payment_methods`
    being absent proves the list was passed in by the caller, so both fields have
    to be read: judging on the types alone flags healthy intents that happened to
    resolve to card.
    """
    if intent.get("automatic_payment_methods"):
        return False
    return sorted(intent.get("payment_method_types") or []) in CARD_ONLY


def enabled_methods(configs):
    """Method names that are available and switched on for this account. Pure.

    A configuration carries one sub-object per method alongside ordinary metadata
    fields, so the method entries are found by shape rather than by name. Read
    `display_preference.value`, the resolved setting, not `preference`, which is
    only what was asked for and can still resolve to off.
    """
    out = set()
    for cfg in configs:
        for name, val in cfg.items():
            if not isinstance(val, dict):
                continue
            pref = val.get("display_preference") or {}
            if val.get("available") and pref.get("value") == "on":
                out.add(name)
    return out


def verdict(stats, enabled):
    """Weigh the intents against the account's enabled methods. Pure.

    stats: {"intents": n, "card_only": n, "offered": iterable of method names}.
    enabled: the set from enabled_methods().
    """
    total = stats.get("intents", 0)
    if not total:
        return ("no_data", "no PaymentIntents in the window: nothing to judge")

    card_only = stats.get("card_only", 0)
    unused = sorted(enabled - set(stats.get("offered") or ()))

    if card_only >= total * 0.8:
        return ("hardcoded",
                "%d of %d intent(s) pin payment_method_types to card, so dynamic "
                "payment methods are bypassed. Enabled and never offered: %s"
                % (card_only, total, ", ".join(unused) or "(nothing else)"))
    if card_only:
        return ("partial",
                "%d of %d intent(s) still pin payment_method_types: one creation "
                "site was migrated and another was not" % (card_only, total))
    if unused:
        return ("unused",
                "dynamic methods are on everywhere, but %s never appeared on an "
                "intent: check currency, country and amount eligibility"
                % ", ".join(unused))
    return ("healthy", "every enabled method reaches at least one intent")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to " + path)
    r.raise_for_status()
    return r.json()


def sample_intents(session, since, cap):
    """Walk recent intents and tally what they pinned and what they offered."""
    stats = {"intents": 0, "card_only": 0}
    offered = set()
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/payment_intents", **params)
        rows = page.get("data", [])
        for pi in rows:
            stats["intents"] += 1
            if is_card_only(pi):
                stats["card_only"] += 1
            offered.update(pi.get("payment_method_types") or [])
        if not rows or not page.get("has_more") or stats["intents"] >= cap:
            break
        params["starting_after"] = rows[-1]["id"]
    stats["offered"] = offered
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30, help="how far back to sample")
    ap.add_argument("--max-intents", type=int, default=2000,
                    help="stop sampling after this many intents")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    stats = sample_intents(s, since, args.max_intents)
    configs = get(s, "/payment_method_configurations", limit=100).get("data", [])
    enabled = enabled_methods(configs)

    state, detail = verdict(stats, enabled)
    line = "%-9s %s" % (state, detail)
    if state in ("healthy", "no_data"):
        log.info(line)
        return 0

    log.warning(line)
    if state in ("hardcoded", "partial"):
        log.warning("  repair: drop payment_method_types from the create call")
        log.warning('  repair: POST %s/payment_intents -d amount=1099 -d currency=eur '
                    '-d "automatic_payment_methods[enabled]=true"', API)
        log.warning("  repair: use excluded_payment_method_types for one-off "
                    "exclusions rather than an allowlist")
    else:
        log.warning("  repair: confirm currency, country and amount eligibility at "
                    "https://dashboard.stripe.com/settings/payment_methods")
    log.info("sampled %d intent(s); offered %d method(s); enabled %d",
             stats["intents"], len(stats.get("offered") or ()), len(enabled))
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-payment-method-coverage.mjs",
"js": '''/**
 * Report PaymentIntents that pin payment_method_types instead of using dynamic
 * payment methods, and enabled methods that never reach a customer.
 *
 * Read only. Two GET requests, no writes: give this a RESTRICTED key with read
 * access to PaymentIntents and Payment Method Configurations. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// "card" alone is the classic tutorial line; "card" plus "link" is what it
// becomes after Link is switched on and the array is edited rather than removed.
const CARD_ONLY = new Set(['card', 'card,link']);

/**
 * True when this intent pinned an explicit card-only method list. Pure.
 *
 * Both fields matter: payment_method_types is populated on every intent, so only
 * a missing automatic_payment_methods proves the list was passed in.
 */
export function isCardOnly(intent) {
  if (intent.automatic_payment_methods) return false;
  const types = [...(intent.payment_method_types ?? [])].sort();
  return CARD_ONLY.has(types.join(','));
}

/**
 * Method names that are available and switched on for this account. Pure.
 *
 * Read display_preference.value, the resolved setting, not preference.
 */
export function enabledMethods(configs) {
  const out = new Set();
  for (const cfg of configs) {
    for (const [name, val] of Object.entries(cfg)) {
      if (!val || typeof val !== 'object' || Array.isArray(val)) continue;
      const pref = val.display_preference ?? {};
      if (val.available && pref.value === 'on') out.add(name);
    }
  }
  return out;
}

/**
 * Weigh the intents against the account's enabled methods. Pure.
 */
export function verdict(stats, enabled) {
  const total = stats.intents ?? 0;
  if (!total) return ['no_data', 'no PaymentIntents in the window: nothing to judge'];

  const cardOnly = stats.card_only ?? 0;
  const offered = new Set(stats.offered ?? []);
  const unused = [...enabled].filter((m) => !offered.has(m)).sort();

  if (cardOnly >= total * 0.8) {
    return ['hardcoded',
      `${cardOnly} of ${total} intent(s) pin payment_method_types to card, so ` +
      'dynamic payment methods are bypassed. Enabled and never offered: ' +
      (unused.join(', ') || '(nothing else)')];
  }
  if (cardOnly) {
    return ['partial',
      `${cardOnly} of ${total} intent(s) still pin payment_method_types: one ` +
      'creation site was migrated and another was not'];
  }
  if (unused.length) {
    return ['unused',
      `dynamic methods are on everywhere, but ${unused.join(', ')} never ` +
      'appeared on an intent: check currency, country and amount eligibility'];
  }
  return ['healthy', 'every enabled method reaches at least one intent'];
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

export async function sampleIntents(key, since, cap = 2000) {
  const stats = { intents: 0, card_only: 0 };
  const offered = new Set();
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/payment_intents', params);
    const rows = page.data ?? [];
    for (const pi of rows) {
      stats.intents += 1;
      if (isCardOnly(pi)) stats.card_only += 1;
      for (const t of pi.payment_method_types ?? []) offered.add(t);
    }
    if (!rows.length || !page.has_more || stats.intents >= cap) break;
    params.starting_after = rows[rows.length - 1].id;
  }
  stats.offered = offered;
  return stats;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const since = Math.floor(Date.now() / 1000) - 30 * 86400;
  const stats = await sampleIntents(key, since);
  const { data: configs = [] } = await get(key, '/payment_method_configurations',
                                           { limit: 100 });
  const enabled = enabledMethods(configs);

  const [state, detail] = verdict(stats, enabled);
  const line = `${state.padEnd(9)} ${detail}`;
  if (state === 'healthy' || state === 'no_data') { console.log(line); return; }

  console.warn(line);
  if (state === 'hardcoded' || state === 'partial') {
    console.warn('  repair: drop payment_method_types from the create call');
    console.warn(`  repair: POST ${API}/payment_intents -d amount=1099 ` +
      '-d currency=eur -d "automatic_payment_methods[enabled]=true"');
    console.warn('  repair: use excluded_payment_method_types for one-off ' +
      'exclusions rather than an allowlist');
  } else {
    console.warn('  repair: confirm currency, country and amount eligibility at ' +
      'https://dashboard.stripe.com/settings/payment_methods');
  }
  console.log(`sampled ${stats.intents} intent(s); offered ${stats.offered.size} ` +
              `method(s); enabled ${enabled.size}`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail the suite on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters is the dynamic intent that resolved to card anyway. It has <code>payment_method_types: [\"card\"]</code> just like the hardcoded one, and a check that reads only that field reports a healthy integration as broken and sends someone to rewrite code that was already right. The other one worth pinning is the split between <em>hardcoded</em> and <em>unused</em>, because they share a symptom and have different fixes.",
"test_py_file": "test_stripe_payment_method_coverage.py",
"test_py": '''from stripe_payment_method_coverage import is_card_only, enabled_methods, verdict


def test_bare_card_list_is_hardcoded():
    assert is_card_only({"payment_method_types": ["card"]})


def test_card_plus_link_is_still_hardcoded():
    # Link gets added to the array instead of the array being removed.
    assert is_card_only({"payment_method_types": ["link", "card"]})


def test_dynamic_intent_that_resolved_to_card_is_not_hardcoded():
    # The whole point: same types, different origin.
    assert not is_card_only({
        "automatic_payment_methods": {"enabled": True},
        "payment_method_types": ["card"],
    })


def test_a_longer_explicit_list_is_not_flagged():
    assert not is_card_only({"payment_method_types": ["card", "ideal"]})


def test_enabled_methods_ignores_metadata_and_off_methods():
    configs = [{
        "id": "pmc_1", "object": "payment_method_configuration", "name": "default",
        "card": {"available": True, "display_preference": {"value": "on"}},
        "ideal": {"available": True, "display_preference": {"value": "off"}},
        "klarna": {"available": False, "display_preference": {"value": "on"}},
    }]
    assert enabled_methods(configs) == {"card"}


def test_mostly_hardcoded_names_the_methods_going_to_waste():
    stats = {"intents": 100, "card_only": 95, "offered": ["card"]}
    state, detail = verdict(stats, {"card", "ideal", "klarna"})
    assert state == "hardcoded"
    assert "ideal, klarna" in detail


def test_a_minority_is_a_half_finished_migration():
    stats = {"intents": 100, "card_only": 12, "offered": ["card", "ideal"]}
    state, _ = verdict(stats, {"card", "ideal"})
    assert state == "partial"


def test_nothing_hardcoded_but_a_method_never_offered_is_eligibility():
    stats = {"intents": 100, "card_only": 0, "offered": ["card"]}
    state, detail = verdict(stats, {"card", "klarna"})
    assert state == "unused"
    assert "eligibility" in detail


def test_full_coverage_is_healthy():
    stats = {"intents": 40, "card_only": 0, "offered": ["card", "ideal"]}
    assert verdict(stats, {"card", "ideal"})[0] == "healthy"


def test_an_empty_window_is_not_reported_as_healthy():
    assert verdict({"intents": 0}, {"card"})[0] == "no_data"
''',
"test_js_file": "stripe-payment-method-coverage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isCardOnly, enabledMethods, verdict } from './stripe-payment-method-coverage.mjs';

test('bare card list is hardcoded', () => {
  assert.equal(isCardOnly({ payment_method_types: ['card'] }), true);
});

test('card plus link is still hardcoded', () => {
  assert.equal(isCardOnly({ payment_method_types: ['link', 'card'] }), true);
});

test('dynamic intent that resolved to card is not hardcoded', () => {
  assert.equal(isCardOnly({
    automatic_payment_methods: { enabled: true },
    payment_method_types: ['card'],
  }), false);
});

test('a longer explicit list is not flagged', () => {
  assert.equal(isCardOnly({ payment_method_types: ['card', 'ideal'] }), false);
});

test('enabledMethods ignores metadata and off methods', () => {
  const configs = [{
    id: 'pmc_1', object: 'payment_method_configuration', name: 'default',
    card: { available: true, display_preference: { value: 'on' } },
    ideal: { available: true, display_preference: { value: 'off' } },
    klarna: { available: false, display_preference: { value: 'on' } },
  }];
  assert.deepEqual([...enabledMethods(configs)], ['card']);
});

test('mostly hardcoded names the methods going to waste', () => {
  const stats = { intents: 100, card_only: 95, offered: ['card'] };
  const [state, detail] = verdict(stats, new Set(['card', 'ideal', 'klarna']));
  assert.equal(state, 'hardcoded');
  assert.match(detail, /ideal, klarna/);
});

test('a minority is a half finished migration', () => {
  const stats = { intents: 100, card_only: 12, offered: ['card', 'ideal'] };
  assert.equal(verdict(stats, new Set(['card', 'ideal']))[0], 'partial');
});

test('nothing hardcoded but a method never offered is eligibility', () => {
  const stats = { intents: 100, card_only: 0, offered: ['card'] };
  const [state, detail] = verdict(stats, new Set(['card', 'klarna']));
  assert.equal(state, 'unused');
  assert.match(detail, /eligibility/);
});

test('full coverage is healthy', () => {
  const stats = { intents: 40, card_only: 0, offered: ['card', 'ideal'] };
  assert.equal(verdict(stats, new Set(['card', 'ideal']))[0], 'healthy');
});

test('an empty window is not reported as healthy', () => {
  assert.equal(verdict({ intents: 0 }, new Set(['card']))[0], 'no_data');
});
''',
"faq": [
 ("Why does my Payment Element only show a card form?",
  "Because the PaymentIntent named its methods. If payment_method_types was passed to the create call, Stripe offers exactly that list and dynamic payment methods are bypassed, so the Dashboard toggles have no effect on that intent."),
 ("How do I tell a hardcoded intent from a dynamic one?",
  "By automatic_payment_methods, not by the types. Stripe populates payment_method_types on every intent with whatever it resolved, so a dynamic intent in a card-only market looks identical. Only automatic_payment_methods being null proves the caller passed the list."),
 ("Is payment_method_types deprecated?",
  "No, and that is why nothing warns you. Pinning a method is legitimate when you genuinely want one, so Stripe keeps honouring the parameter. It is the wrong default, not a removed feature."),
 ("I removed the array and a method still does not appear. Why?",
  "Eligibility. A method renders only when the currency, the country and the amount all qualify, and each method has its own rules. That is the unused state in the script: dynamic methods are on, the method is enabled, and it still never gets offered because the transaction does not qualify."),
 ("How do I drop one method for a single transaction?",
  "Use excluded_payment_method_types on that create call. Reinstating an allowlist to exclude one method means every method Stripe adds later is excluded too, silently, forever."),
],
"related": [
 ("/stripe/wallet-domain-not-registered/", "No payment method domain registered, so wallets never show"),
 ("/stripe/abandoned-requires-action-intents/", "3DS handoff breaks and requires_action intents pile up"),
 ("/stripe/stale-requires-payment-method-intents/", "PaymentIntents sit in requires_payment_method for weeks"),
],
"citations": [CITE_DPM, CITE_PMC_OBJ, CITE_PI_OBJ, CITE_KEYS],
},

{
"slug": "off-session-authentication-required-declines",
"title": "Off-session charges die on authentication_required",
"description": "Renewals on saved cards fail with authentication_required. The card was attached without a SetupIntent, so no mandate exists and every retry declines.",
"h1": "off-session charges die on authentication_required",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe authentication_required off_session",
             "authentication_not_handled stripe", "stripe billing_invalid_mandate",
             "stripe saved card declined renewal", "stripe setup intent mandate"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A renewal fails. The customer's card is fine, it has not expired, it has money on it, and it worked when they first signed up. You retry off-session and it fails identically, so you retry again on a schedule and it fails identically again. The <code>decline_code</code> is <code>authentication_required</code>, and no number of retries will ever change it.",
"short_answer": """<p>Read <code>GET /v1/payment_intents</code> and count <code>last_payment_error.decline_code</code> in <code>authentication_required</code> or <code>authentication_not_handled</code>. Then, for each affected customer, read <code>GET /v1/setup_intents?customer={id}</code> and look for one with <code>status</code> of <code>"succeeded"</code> and a non-null <code>mandate</code>.</p>
<p>No such SetupIntent means the card was attached directly, no mandate was ever recorded, and the issuer will soft-decline every off-session attempt. The fix is a new on-session authentication, not a retry.</p>""",
"problem": """<p>Under SCA, a merchant-initiated off-session charge is only exempt from authentication if the card was authenticated on-session at the time it was saved, and a mandate exists recording that the customer agreed to be charged later. Attaching a payment method with a bare <code>POST /v1/payment_methods/{id}/attach</code> saves the card and records none of that. The card is stored, it looks correct in the Dashboard, and it is not chargeable off-session.</p>
<p>It passes every test you write, because the first charge is usually on-session and on-session charges work. The damage appears one billing cycle later, on renewals, on delayed captures, on the second invoice &mdash; at which point it looks like a dunning problem rather than a card-saving problem, and dunning is where teams spend the next two weeks.</p>
<p>Stripe names the same condition differently depending on where you meet it. On the invoice path it surfaces as <code>billing_invalid_mandate</code>; on the intent it is <code>authentication_required</code>. That the two are one bug is not obvious from either message.</p>""",
"why": """<p><strong>Retrying cannot help.</strong> The issuer is asking for a customer who is not there. Every off-session retry presents the same missing authentication and receives the same soft decline, which is why this failure has a completely flat retry curve while a genuine insufficient-funds decline does not.</p>
<p><strong>The generic code hides the specific one.</strong> <code>last_payment_error.code</code> is <code>card_declined</code> on all of these, exactly like an ordinary decline. The distinguishing value is one level down in <code>decline_code</code>, so a dashboard that groups by <code>code</code> shows this as noise inside the normal decline rate.</p>
<p><strong>Attaching is the obvious call and the wrong one.</strong> <code>attach</code> reads like the API for saving a card, and it is &mdash; for cards that will only ever be charged with the customer present. Off-session billing needs a SetupIntent with <code>usage=off_session</code>, or a payment created with <code>setup_future_usage=off_session</code>, and neither is discoverable from the name of the endpoint you reached for first.</p>""",
"steps": [
 {"h": "Find the declines by decline_code, not code",
  "body": """<p><code>GET /v1/payment_intents?limit=100&amp;created[gte]={now-90d}</code>, paginated, filtering <code>last_payment_error.decline_code</code>. Ninety days covers at least two monthly cycles, which is what separates a customer this happened to once from a customer it happens to every month.</p>"""},
 {"h": "Group by customer, not by intent",
  "body": """<p>The mandate is a property of how a card was saved for a customer, so one customer with six failed renewals is one problem, not six. Grouping first also keeps the second call cheap.</p>"""},
 {"h": "Ask whether a mandate was ever produced",
  "body": """<p><code>GET /v1/setup_intents?customer={id}</code>. A SetupIntent that was created and abandoned proves nothing. Only one that reached <code>succeeded</code> and carries a non-null <code>mandate</code> records that the customer authenticated and agreed to future charges.</p>"""},
 {"h": "Separate the two failures that look the same",
  "body": """<p>A decline with no mandate is a saving bug and needs re-authentication. A decline <em>with</em> a mandate is the issuer stepping up anyway, which happens, and that one is finished by bringing the customer back on-session for this single charge. Retrying is wrong in both cases but for different reasons.</p>"""},
 {"h": "Look at customers who have not failed yet",
  "body": """<p>Saved cards with no mandate behind them have not failed because they have not been charged off-session yet. Everyone on that list will fail at their next renewal, and there is a window to email them a SetupIntent link before it happens.</p>"""},
],
"verify": """<p>Re-run the script after the re-authentication emails have gone out. Customers should move from <code>unmandated</code> and <code>at_risk</code> into <code>covered</code>.</p>
<pre><code class="language-bash">python3 stripe_offsession_mandates.py --days 90
# 412 customer(s), 0 unmandated, 0 at risk</code></pre>""",
"code_intro": "Two kinds of GET request and no writes: a restricted key with read access to PaymentIntents, SetupIntents and PaymentMethods is enough. The classification is three pure functions because there are three separate judgements &mdash; what counts as this decline, what counts as a mandate, and what the combination means for one customer.",
"py_file": "stripe_offsession_mandates.py",
"py": '''"""Report customers whose saved cards cannot be charged off-session.

Read only. GET requests only, no writes: give this a RESTRICTED key with read
access to PaymentIntents, SetupIntents and PaymentMethods. The repair is printed,
never performed, because this script holds a credential to a live payments
account.
"""
import argparse
import collections
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_offsession_mandates")

API = "https://api.stripe.com/v1"

# Both mean the issuer wanted the cardholder present. The second is what Stripe
# returns when the integration never handled the step-up at all.
STEP_UP = ("authentication_required", "authentication_not_handled")


def is_step_up_decline(intent):
    """True when this intent failed for want of authentication. Pure.

    The generic `code` on these is `card_declined`, identical to an ordinary
    decline, so the distinguishing value is one level down in `decline_code`.
    Anything grouping by `code` buries this failure inside the normal decline
    rate.
    """
    err = intent.get("last_payment_error") or {}
    return err.get("decline_code") in STEP_UP


def has_mandate(setup_intents):
    """True when some SetupIntent for this customer actually produced a mandate.

    Pure. A SetupIntent that was created and abandoned proves nothing: only one
    that reached `succeeded` and carries a non-null `mandate` records that the
    customer authenticated on-session and agreed to be charged later.
    """
    return any(si.get("status") == "succeeded" and si.get("mandate")
               for si in setup_intents)


def verdict(declines, saved_cards, setup_intents):
    """Classify one customer. Pure.

    Two states share a symptom and need different repairs: a decline with no
    mandate is a card-saving bug, and a decline despite a mandate is the issuer
    stepping up anyway. Retrying off-session is wrong for both.
    """
    mandated = has_mandate(setup_intents)
    if declines and not mandated:
        return ("unmandated",
                "%d off-session decline(s) and no succeeded SetupIntent carrying "
                "a mandate: the card was attached directly, so every retry "
                "declines identically" % declines)
    if declines:
        return ("stepped_up",
                "%d off-session decline(s) despite a mandate on file: the issuer "
                "asked for the cardholder anyway, so this charge has to be "
                "finished on-session" % declines)
    if saved_cards and not mandated:
        return ("at_risk",
                "%d saved card(s) with no mandate behind them: nothing has failed "
                "yet only because nothing has been charged off-session yet"
                % saved_cards)
    if saved_cards:
        return ("covered", "saved cards are backed by a mandate")
    return ("clear", "no saved cards to charge off-session")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to " + path)
    r.raise_for_status()
    return r.json()


def declines_by_customer(session, since, cap):
    """Tally step-up declines per customer id over the window."""
    counts = collections.Counter()
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/payment_intents", **params)
        rows = page.get("data", [])
        for pi in rows:
            seen += 1
            if pi.get("customer") and is_step_up_decline(pi):
                counts[pi["customer"]] += 1
        if not rows or not page.get("has_more") or seen >= cap:
            break
        params["starting_after"] = rows[-1]["id"]
    return counts, seen


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to look for declines")
    ap.add_argument("--max-intents", type=int, default=5000,
                    help="stop sampling after this many intents")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    declines, sampled = declines_by_customer(s, since, args.max_intents)
    if not declines:
        log.info("sampled %d intent(s), no authentication_required declines", sampled)
        return 0

    unmandated = stepped_up = 0
    for customer, n in declines.most_common():
        sis = get(s, "/setup_intents", customer=customer, limit=100).get("data", [])
        cards = get(s, "/payment_methods", customer=customer, type="card",
                    limit=100).get("data", [])
        state, detail = verdict(n, len(cards), sis)
        log.warning("%-11s %s  %s", state, customer, detail)
        if state == "unmandated":
            unmandated += 1
            log.warning("  repair: send a SetupIntent link so the customer "
                        "re-authenticates, then charge with off_session=true "
                        "and confirm=true")
        elif state == "stepped_up":
            stepped_up += 1
            log.warning("  repair: bring the customer back on-session for this "
                        "charge; do not schedule another off-session retry")

    log.warning("  repair: stop attaching cards directly. Save with a SetupIntent "
                "using usage=off_session, or setup_future_usage=off_session during "
                "a payment")
    log.info("%d customer(s) declining: %d unmandated, %d stepped up",
             len(declines), unmandated, stepped_up)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-offsession-mandates.mjs",
"js": '''/**
 * Report customers whose saved cards cannot be charged off-session.
 *
 * Read only. GET requests only, no writes: give this a RESTRICTED key with read
 * access to PaymentIntents, SetupIntents and PaymentMethods. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Both mean the issuer wanted the cardholder present. The second is what Stripe
// returns when the integration never handled the step-up at all.
const STEP_UP = new Set(['authentication_required', 'authentication_not_handled']);

/**
 * True when this intent failed for want of authentication. Pure.
 *
 * The generic `code` is `card_declined` on all of these, so the distinguishing
 * value is one level down in `decline_code`.
 */
export function isStepUpDecline(intent) {
  const err = intent.last_payment_error ?? {};
  return STEP_UP.has(err.decline_code);
}

/**
 * True when some SetupIntent for this customer actually produced a mandate. Pure.
 *
 * An abandoned SetupIntent proves nothing: it has to have succeeded and to carry
 * a non-null mandate.
 */
export function hasMandate(setupIntents) {
  return setupIntents.some((si) => si.status === 'succeeded' && si.mandate);
}

/**
 * Classify one customer. Pure.
 */
export function verdict(declines, savedCards, setupIntents) {
  const mandated = hasMandate(setupIntents);
  if (declines && !mandated) {
    return ['unmandated',
      `${declines} off-session decline(s) and no succeeded SetupIntent carrying ` +
      'a mandate: the card was attached directly, so every retry declines identically'];
  }
  if (declines) {
    return ['stepped_up',
      `${declines} off-session decline(s) despite a mandate on file: the issuer ` +
      'asked for the cardholder anyway, so this charge has to be finished on-session'];
  }
  if (savedCards && !mandated) {
    return ['at_risk',
      `${savedCards} saved card(s) with no mandate behind them: nothing has ` +
      'failed yet only because nothing has been charged off-session yet'];
  }
  if (savedCards) return ['covered', 'saved cards are backed by a mandate'];
  return ['clear', 'no saved cards to charge off-session'];
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

export async function declinesByCustomer(key, since, cap = 5000) {
  const counts = new Map();
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/payment_intents', params);
    const rows = page.data ?? [];
    for (const pi of rows) {
      seen += 1;
      if (pi.customer && isStepUpDecline(pi)) {
        counts.set(pi.customer, (counts.get(pi.customer) ?? 0) + 1);
      }
    }
    if (!rows.length || !page.has_more || seen >= cap) break;
    params.starting_after = rows[rows.length - 1].id;
  }
  return { counts, seen };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const since = Math.floor(Date.now() / 1000) - 90 * 86400;
  const { counts, seen } = await declinesByCustomer(key, since);
  if (counts.size === 0) {
    console.log(`sampled ${seen} intent(s), no authentication_required declines`);
    return;
  }

  let unmandated = 0;
  let steppedUp = 0;
  for (const [customer, n] of [...counts].sort((a, b) => b[1] - a[1])) {
    const { data: sis = [] } = await get(key, '/setup_intents',
                                         { customer, limit: 100 });
    const { data: cards = [] } = await get(key, '/payment_methods',
                                           { customer, type: 'card', limit: 100 });
    const [state, detail] = verdict(n, cards.length, sis);
    console.warn(`${state.padEnd(11)} ${customer}  ${detail}`);
    if (state === 'unmandated') {
      unmandated += 1;
      console.warn('  repair: send a SetupIntent link so the customer ' +
        're-authenticates, then charge with off_session=true and confirm=true');
    } else if (state === 'stepped_up') {
      steppedUp += 1;
      console.warn('  repair: bring the customer back on-session for this charge; ' +
        'do not schedule another off-session retry');
    }
  }

  console.warn('  repair: stop attaching cards directly. Save with a SetupIntent ' +
    'using usage=off_session, or setup_future_usage=off_session during a payment');
  console.log(`${counts.size} customer(s) declining: ${unmandated} unmandated, ` +
              `${steppedUp} stepped up`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail the suite on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning hardest is the SetupIntent that succeeded with a null <code>mandate</code>. It is present, it is green in the Dashboard, and it does not make the card chargeable off-session &mdash; treating its existence as proof is how a check reports every affected customer as healthy. The other is <code>at_risk</code>: no declines yet, no mandate either, which is the only state where there is still time to act before a renewal fails.",
"test_py_file": "test_stripe_offsession_mandates.py",
"test_py": '''from stripe_offsession_mandates import is_step_up_decline, has_mandate, verdict

GOOD_SI = {"status": "succeeded", "mandate": "mandate_123"}


def test_authentication_required_is_a_step_up_decline():
    assert is_step_up_decline({"last_payment_error":
                               {"code": "card_declined",
                                "decline_code": "authentication_required"}})


def test_authentication_not_handled_counts_too():
    assert is_step_up_decline({"last_payment_error":
                               {"decline_code": "authentication_not_handled"}})


def test_an_ordinary_decline_is_not_one():
    assert not is_step_up_decline({"last_payment_error":
                                   {"code": "card_declined",
                                    "decline_code": "insufficient_funds"}})


def test_a_succeeded_setup_intent_without_a_mandate_is_not_proof():
    # Green in the Dashboard, still not chargeable off-session.
    assert not has_mandate([{"status": "succeeded", "mandate": None}])


def test_an_abandoned_setup_intent_is_not_proof():
    assert not has_mandate([{"status": "requires_confirmation", "mandate": None}])


def test_declines_without_a_mandate_are_a_card_saving_bug():
    state, detail = verdict(4, 1, [{"status": "succeeded", "mandate": None}])
    assert state == "unmandated"
    assert "4" in detail


def test_declines_with_a_mandate_are_the_issuer_stepping_up():
    state, detail = verdict(2, 1, [GOOD_SI])
    assert state == "stepped_up"
    assert "on-session" in detail


def test_saved_cards_with_no_mandate_and_no_declines_yet_are_at_risk():
    state, _ = verdict(0, 3, [])
    assert state == "at_risk"


def test_saved_cards_behind_a_mandate_are_covered():
    assert verdict(0, 2, [GOOD_SI])[0] == "covered"


def test_a_customer_with_no_saved_cards_is_clear():
    assert verdict(0, 0, [])[0] == "clear"
''',
"test_js_file": "stripe-offsession-mandates.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isStepUpDecline, hasMandate, verdict } from './stripe-offsession-mandates.mjs';

const GOOD_SI = { status: 'succeeded', mandate: 'mandate_123' };

test('authentication_required is a step up decline', () => {
  assert.equal(isStepUpDecline({
    last_payment_error: { code: 'card_declined',
                          decline_code: 'authentication_required' },
  }), true);
});

test('authentication_not_handled counts too', () => {
  assert.equal(isStepUpDecline({
    last_payment_error: { decline_code: 'authentication_not_handled' },
  }), true);
});

test('an ordinary decline is not one', () => {
  assert.equal(isStepUpDecline({
    last_payment_error: { code: 'card_declined', decline_code: 'insufficient_funds' },
  }), false);
});

test('a succeeded setup intent without a mandate is not proof', () => {
  assert.equal(hasMandate([{ status: 'succeeded', mandate: null }]), false);
});

test('an abandoned setup intent is not proof', () => {
  assert.equal(hasMandate([{ status: 'requires_confirmation', mandate: null }]), false);
});

test('declines without a mandate are a card saving bug', () => {
  const [state, detail] = verdict(4, 1, [{ status: 'succeeded', mandate: null }]);
  assert.equal(state, 'unmandated');
  assert.match(detail, /4/);
});

test('declines with a mandate are the issuer stepping up', () => {
  const [state, detail] = verdict(2, 1, [GOOD_SI]);
  assert.equal(state, 'stepped_up');
  assert.match(detail, /on-session/);
});

test('saved cards with no mandate and no declines yet are at risk', () => {
  assert.equal(verdict(0, 3, [])[0], 'at_risk');
});

test('saved cards behind a mandate are covered', () => {
  assert.equal(verdict(0, 2, [GOOD_SI])[0], 'covered');
});

test('a customer with no saved cards is clear', () => {
  assert.equal(verdict(0, 0, [])[0], 'clear');
});
''',
"faq": [
 ("What does decline_code authentication_required mean?",
  "That the issuer wants the cardholder present and there is nobody there. Off-session charges are only exempt from authentication when the card was authenticated on-session at the time it was saved and a mandate was recorded; without that, the issuer soft-declines."),
 ("Why does retrying never work?",
  "Because nothing about the attempt changes. Every retry presents the same missing authentication and gets the same answer, which is why these declines have a completely flat retry curve compared with insufficient funds. The card has to be re-authenticated by the customer."),
 ("How do I know whether a mandate exists?",
  "GET /v1/setup_intents?customer={id} and look for one with status succeeded and a non-null mandate. Both conditions matter: a SetupIntent can succeed and still carry no mandate, and that one does not make the card chargeable off-session."),
 ("Is billing_invalid_mandate the same problem?",
  "Yes, seen from the invoice side. Stripe reports the missing mandate as billing_invalid_mandate on subscription and invoice paths and as authentication_required on the intent itself, but the cause and the fix are identical."),
 ("How should cards be saved for later billing?",
  "With a SetupIntent using usage=off_session, confirmed on-session so a mandate is generated, or during a payment with setup_future_usage=off_session. Not with a bare attach call, which stores the card and records none of the consent that off-session charging depends on."),
],
"related": [
 ("/stripe/setup-intents-never-confirmed/", "SetupIntents are created but never confirmed by the client"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
 ("/stripe/dunning-retries-exhausted/", "Dunning ran out of retries and no attempt is scheduled"),
],
"citations": [CITE_SCA, CITE_DECLINE_CODES, CITE_SI_OBJ, CITE_SAVE_DURING],
},

{
"slug": "wallet-domain-not-registered",
"title": "No payment method domain registered, so wallets never show",
"description": "Apple Pay and Google Pay work on localhost and vanish in production. The serving domain is not registered with Stripe, so the wallet is filtered out.",
"h1": "no payment method domain registered, so wallets never show",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["apple pay button not showing stripe",
             "stripe payment element google pay not showing",
             "stripe payment method domain registration",
             "apple-developer-merchantid-domain-association",
             "stripe link not showing production"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Apple Pay renders perfectly on localhost. It renders in Stripe's own demo. It is enabled in the Dashboard, the browser is Safari, the device has a card in the wallet &mdash; and on <code>checkout.example.com</code> the button is simply not there. No console error, no failed request, nothing in the Stripe logs. The wallet was filtered out before it had a chance to render, because Stripe does not recognise the domain asking for it.",
"short_answer": """<p>Read <code>GET /v1/payment_method_domains</code> with a live key. An empty list is the answer on its own: no domain is registered, so every wallet is filtered out in production.</p>
<p>If the list is not empty, check each entry for <code>enabled: true</code>, <code>livemode: true</code>, and <code>apple_pay.status</code>, <code>google_pay.status</code> and <code>link.status</code> equal to <code>"active"</code>. Any other status means that one wallet is dark, and the reason is in <code>&lt;wallet&gt;.status_details.error_message</code>.</p>""",
"problem": """<p>Wallet registration is per-domain and per-mode, and both halves of that catch people. A domain verified in test mode does nothing for live traffic, so the wallet that worked all through development disappears at launch. And a registration for <code>example.com</code> does nothing for <code>checkout.example.com</code>, so moving checkout to a subdomain &mdash; a routine infrastructure change nobody thinks to mention &mdash; silently removes Apple Pay, Google Pay, Link and PayPal from the Payment Element.</p>
<p>Because the wallet is filtered rather than failed, there is nothing to find. The Element renders the methods it can offer, the page has no error, and the request never happens. The only visible trace is in the numbers: mobile conversion drops relative to desktop and stays there, which reads as a responsive-design problem for as long as anyone is willing to believe it.</p>""",
"why": """<p><strong>Domain verification is an Apple requirement that Stripe carries out for you.</strong> Apple Pay on the web will not run on an unverified domain, so Stripe has to register and verify the exact host before it can offer the button. That is why the check is a Stripe object rather than a Dashboard toggle.</p>
<p><strong>Modes are separate objects.</strong> <code>livemode</code> on the domain object is the thing to read. A perfectly healthy test-mode registration produces exactly the symptom you are investigating, and it looks correct in the test Dashboard everyone is checking.</p>
<p><strong>Each wallet has its own status.</strong> One domain can serve Link happily while Apple Pay is dark, so a check that stops at &ldquo;a domain is registered&rdquo; passes on an account where the specific wallet you care about never renders. The reason lives in <code>status_details.error_message</code>, not in the status.</p>""",
"steps": [
 {"h": "List the registered domains with a live key",
  "body": """<p><code>GET /v1/payment_method_domains?limit=100</code>. An empty list ends the investigation immediately, and it is the single most common result on an account where wallets have never worked in production.</p>"""},
 {"h": "Confirm the mode on each object",
  "body": """<p><code>livemode</code> must be <code>true</code>. A test-mode registration is not a partial credit; it has no effect at all on live traffic, and it is what people find when they go looking and conclude the domain is registered.</p>"""},
 {"h": "Read each wallet's status separately",
  "body": """<p><code>apple_pay</code>, <code>google_pay</code>, <code>link</code> and <code>paypal</code> each carry their own <code>status</code> on the domain object. Anything other than <code>active</code> means that wallet is dark, and <code>status_details.error_message</code> says why &mdash; usually that the association file is not being served from the domain.</p>"""},
 {"h": "Compare against the hosts you actually serve",
  "body": """<p>Pass the domains checkout runs on and subtract. This is where the subdomain case surfaces: <code>example.com</code> registered and healthy, <code>checkout.example.com</code> absent entirely, and every wallet missing on the page that matters.</p>"""},
 {"h": "Register each host and re-validate",
  "body": """<p>One registration per host, in live mode, then serve <code>/.well-known/apple-developer-merchantid-domain-association</code> from it. Stripe serves the file automatically for Stripe-hosted flows; for your own pages it has to be reachable before validation will pass.</p>"""},
],
"verify": """<p>Re-run with the same <code>--domain</code> arguments. Every host you serve should be present, live, enabled, and active on every wallet.</p>
<pre><code class="language-bash">python3 stripe_wallet_domains.py --domain checkout.example.com
# active    checkout.example.com  every wallet active</code></pre>""",
"code_intro": "One GET request and no writes: a restricted key with read access to Payment Method Domains is enough. Three pure functions, because the check has three separate questions in it &mdash; which wallets are dark on a domain, what one domain object as a whole means, and which of your hosts are not registered at all.",
"py_file": "stripe_wallet_domains.py",
"py": '''"""Report domains where Apple Pay, Google Pay, Link or PayPal will not render.

Read only. One GET request, no writes: give this a RESTRICTED key with read
access to Payment Method Domains. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_wallet_domains")

API = "https://api.stripe.com/v1"

WALLETS = ("apple_pay", "google_pay", "link", "paypal")


def dark_wallets(domain):
    """Wallets on this domain that are not active, with Stripe's own reason.

    Pure. Each wallet carries its own status on the domain object, so one domain
    can serve Link happily while Apple Pay is dark. The reason is in
    `<wallet>.status_details.error_message` rather than in the status itself,
    which is why a check that only reads the status has nothing useful to print.
    """
    out = []
    for name in WALLETS:
        w = domain.get(name)
        if not isinstance(w, dict):
            continue
        if w.get("status") != "active":
            details = w.get("status_details") or {}
            out.append((name, w.get("status"),
                        details.get("error_message") or "no reason given"))
    return out


def verdict(domain):
    """Classify one registered domain. Pure. Returns (state, detail, dark).

    livemode is checked before anything else: a healthy test-mode registration
    produces exactly the symptom being investigated and looks correct in the
    test Dashboard, so it cannot be allowed to read as a pass.
    """
    if not domain.get("livemode"):
        return ("test_only",
                "registered in test mode only, which has no effect on live "
                "traffic: live visitors see no wallet at all", [])
    if not domain.get("enabled"):
        return ("disabled",
                "registered but disabled, which filters the wallets out exactly "
                "as if it had never been registered", [])
    dark = dark_wallets(domain)
    if dark:
        return ("dark",
                "%d wallet(s) not active on a live, enabled domain" % len(dark),
                dark)
    return ("active", "every wallet active", [])


def missing_domains(registered, serving):
    """Hosts you serve checkout from that have no registration at all. Pure.

    Registration is per-host, not per-site, so checkout.example.com is invisible
    to Stripe even when example.com beside it is registered and healthy.
    """
    have = {d.get("domain_name") for d in registered}
    return sorted(set(serving) - have)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to " + path)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", action="append", default=[],
                    help="a host you serve checkout from; repeatable")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2
    if "_live_" not in key:
        log.warning("this is a test-mode key: registrations here say nothing "
                    "about what live visitors see")

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    domains = get(s, "/payment_method_domains", limit=100).get("data", [])
    if not domains:
        log.warning("no payment method domains registered: every wallet is "
                    "filtered out in production")
        log.warning("  repair: POST %s/payment_method_domains -d "
                    "domain_name=checkout.example.com in live mode", API)
        return 1

    bad = 0
    for d in domains:
        state, detail, dark = verdict(d)
        line = "%-9s %s  %s" % (state, d.get("domain_name", "?"), detail)
        if state == "active":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for name, status, reason in dark:
            log.warning("    %s is %s: %s", name, status, reason)
        if state == "test_only":
            log.warning("  repair: register the same host again with a live key")
        elif state == "disabled":
            log.warning("  repair: POST %s/payment_method_domains/%s -d enabled=true",
                        API, d.get("id"))
        else:
            log.warning("  repair: serve /.well-known/"
                        "apple-developer-merchantid-domain-association from the "
                        "host, then POST %s/payment_method_domains/%s/validate",
                        API, d.get("id"))

    for name in missing_domains(domains, args.domain):
        bad += 1
        log.warning("missing   %s  serves checkout and is not registered at all", name)
        log.warning("  repair: POST %s/payment_method_domains -d domain_name=%s",
                    API, name)

    log.info("%d registered domain(s), %d needing attention", len(domains), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-wallet-domains.mjs",
"js": '''/**
 * Report domains where Apple Pay, Google Pay, Link or PayPal will not render.
 *
 * Read only. One GET request, no writes: give this a RESTRICTED key with read
 * access to Payment Method Domains. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const WALLETS = ['apple_pay', 'google_pay', 'link', 'paypal'];

/**
 * Wallets on this domain that are not active, with Stripe's own reason. Pure.
 *
 * Each wallet carries its own status, and the reason lives in
 * status_details.error_message rather than in the status.
 */
export function darkWallets(domain) {
  const out = [];
  for (const name of WALLETS) {
    const w = domain[name];
    if (!w || typeof w !== 'object') continue;
    if (w.status !== 'active') {
      const details = w.status_details ?? {};
      out.push([name, w.status, details.error_message ?? 'no reason given']);
    }
  }
  return out;
}

/**
 * Classify one registered domain. Pure. Returns [state, detail, dark].
 *
 * livemode is checked first: a healthy test-mode registration produces exactly
 * the symptom being investigated and must not read as a pass.
 */
export function verdict(domain) {
  if (!domain.livemode) {
    return ['test_only',
      'registered in test mode only, which has no effect on live traffic: live ' +
      'visitors see no wallet at all', []];
  }
  if (!domain.enabled) {
    return ['disabled',
      'registered but disabled, which filters the wallets out exactly as if it ' +
      'had never been registered', []];
  }
  const dark = darkWallets(domain);
  if (dark.length) {
    return ['dark', `${dark.length} wallet(s) not active on a live, enabled domain`,
            dark];
  }
  return ['active', 'every wallet active', []];
}

/**
 * Hosts you serve checkout from that have no registration at all. Pure.
 */
export function missingDomains(registered, serving) {
  const have = new Set(registered.map((d) => d.domain_name));
  return [...new Set(serving)].filter((d) => !have.has(d)).sort();
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

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }
  if (!key.includes('_live_')) {
    console.warn('this is a test-mode key: registrations here say nothing about ' +
      'what live visitors see');
  }

  const serving = process.argv.slice(2).filter((a) => !a.startsWith('-'));
  const { data: domains = [] } = await get(key, '/payment_method_domains',
                                           { limit: 100 });
  if (domains.length === 0) {
    console.warn('no payment method domains registered: every wallet is filtered ' +
      'out in production');
    console.warn(`  repair: POST ${API}/payment_method_domains ` +
      '-d domain_name=checkout.example.com in live mode');
    process.exitCode = 1;
    return;
  }

  let bad = 0;
  for (const d of domains) {
    const [state, detail, dark] = verdict(d);
    const line = `${state.padEnd(9)} ${d.domain_name ?? '?'}  ${detail}`;
    if (state === 'active') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    for (const [name, status, reason] of dark) {
      console.warn(`    ${name} is ${status}: ${reason}`);
    }
    if (state === 'test_only') {
      console.warn('  repair: register the same host again with a live key');
    } else if (state === 'disabled') {
      console.warn(`  repair: POST ${API}/payment_method_domains/${d.id} -d enabled=true`);
    } else {
      console.warn('  repair: serve /.well-known/' +
        'apple-developer-merchantid-domain-association from the host, then ' +
        `POST ${API}/payment_method_domains/${d.id}/validate`);
    }
  }

  for (const name of missingDomains(domains, serving)) {
    bad += 1;
    console.warn(`missing   ${name}  serves checkout and is not registered at all`);
    console.warn(`  repair: POST ${API}/payment_method_domains -d domain_name=${name}`);
  }

  console.log(`${domains.length} registered domain(s), ${bad} needing attention`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail the suite on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases decide whether this check is worth running. A test-mode registration must not read as a pass, because it is the exact thing people find when they go looking and it is why they stop looking. And a subdomain must be reported as missing even when the apex domain beside it is registered, live and completely healthy &mdash; that is the case a human eye skips over.",
"test_py_file": "test_stripe_wallet_domains.py",
"test_py": '''from stripe_wallet_domains import dark_wallets, verdict, missing_domains

ACTIVE = {"status": "active"}


def healthy(name="example.com"):
    return {"domain_name": name, "livemode": True, "enabled": True,
            "apple_pay": dict(ACTIVE), "google_pay": dict(ACTIVE),
            "link": dict(ACTIVE), "paypal": dict(ACTIVE)}


def test_a_fully_active_domain_has_no_dark_wallets():
    assert dark_wallets(healthy()) == []


def test_a_dark_wallet_carries_stripes_reason():
    d = healthy()
    d["apple_pay"] = {"status": "inactive", "status_details":
                      {"error_message": "association file not found"}}
    assert dark_wallets(d) == [("apple_pay", "inactive",
                                "association file not found")]


def test_a_dark_wallet_without_a_message_still_reports():
    d = healthy()
    d["link"] = {"status": "inactive"}
    assert dark_wallets(d) == [("link", "inactive", "no reason given")]


def test_a_test_mode_registration_is_not_a_pass():
    # This is what people find when they check, and why they stop checking.
    d = healthy()
    d["livemode"] = False
    state, _, _ = verdict(d)
    assert state == "test_only"


def test_a_disabled_domain_is_not_a_pass():
    d = healthy()
    d["enabled"] = False
    assert verdict(d)[0] == "disabled"


def test_one_dark_wallet_fails_the_whole_domain():
    d = healthy()
    d["google_pay"] = {"status": "inactive"}
    state, detail, dark = verdict(d)
    assert state == "dark"
    assert "1" in detail and len(dark) == 1


def test_a_live_enabled_active_domain_passes():
    assert verdict(healthy())[0] == "active"


def test_a_subdomain_is_missing_even_when_the_apex_is_healthy():
    registered = [healthy("example.com")]
    assert missing_domains(registered, ["example.com", "checkout.example.com"]) == \\
        ["checkout.example.com"]


def test_nothing_is_missing_when_every_host_is_registered():
    registered = [healthy("example.com"), healthy("checkout.example.com")]
    assert missing_domains(registered, ["checkout.example.com"]) == []
''',
"test_js_file": "stripe-wallet-domains.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { darkWallets, verdict, missingDomains } from './stripe-wallet-domains.mjs';

const healthy = (name = 'example.com') => ({
  domain_name: name, livemode: true, enabled: true,
  apple_pay: { status: 'active' }, google_pay: { status: 'active' },
  link: { status: 'active' }, paypal: { status: 'active' },
});

test('a fully active domain has no dark wallets', () => {
  assert.deepEqual(darkWallets(healthy()), []);
});

test('a dark wallet carries stripe reason', () => {
  const d = healthy();
  d.apple_pay = { status: 'inactive',
                  status_details: { error_message: 'association file not found' } };
  assert.deepEqual(darkWallets(d),
                   [['apple_pay', 'inactive', 'association file not found']]);
});

test('a dark wallet without a message still reports', () => {
  const d = healthy();
  d.link = { status: 'inactive' };
  assert.deepEqual(darkWallets(d), [['link', 'inactive', 'no reason given']]);
});

test('a test mode registration is not a pass', () => {
  const d = healthy();
  d.livemode = false;
  assert.equal(verdict(d)[0], 'test_only');
});

test('a disabled domain is not a pass', () => {
  const d = healthy();
  d.enabled = false;
  assert.equal(verdict(d)[0], 'disabled');
});

test('one dark wallet fails the whole domain', () => {
  const d = healthy();
  d.google_pay = { status: 'inactive' };
  const [state, detail, dark] = verdict(d);
  assert.equal(state, 'dark');
  assert.match(detail, /1/);
  assert.equal(dark.length, 1);
});

test('a live enabled active domain passes', () => {
  assert.equal(verdict(healthy())[0], 'active');
});

test('a subdomain is missing even when the apex is healthy', () => {
  assert.deepEqual(missingDomains([healthy('example.com')],
                                  ['example.com', 'checkout.example.com']),
                   ['checkout.example.com']);
});

test('nothing is missing when every host is registered', () => {
  const registered = [healthy('example.com'), healthy('checkout.example.com')];
  assert.deepEqual(missingDomains(registered, ['checkout.example.com']), []);
});
''',
"faq": [
 ("Why does Apple Pay work on localhost but not in production?",
  "Because localhost is exempt from domain verification and your production host is not. Apple Pay on the web requires the serving domain to be registered and verified with Stripe, and that registration is per-host and per-mode."),
 ("Does registering example.com cover checkout.example.com?",
  "No. Registration is per-host, so a subdomain needs its own entry. Moving checkout to a subdomain removes every wallet from the page until that host is registered separately, and nothing anywhere reports an error when it happens."),
 ("Which wallets does this affect?",
  "Apple Pay, Google Pay, Link and PayPal in Elements all depend on the domain registration, and each carries its own status on the domain object. One can be active while another is dark, so read them individually rather than treating the domain as one flag."),
 ("Why is there no error in the console?",
  "Because nothing failed. The Payment Element asks Stripe which methods it may offer and renders those; an unregistered domain simply is not offered the wallet. There is no request to fail and nothing to log."),
 ("How do I find out why a wallet is inactive?",
  "Read status_details.error_message on that wallet in the domain object. It is usually that /.well-known/apple-developer-merchantid-domain-association is not reachable from the host, which Stripe serves automatically only for Stripe-hosted flows."),
],
"related": [
 ("/stripe/card-only-payment-method-types/", "Intents hardcode payment_method_types to card only"),
 ("/stripe/checkout-expired-session-share/", "Most Checkout Sessions expire unpaid and nobody is told"),
 ("/stripe/payment-link-inactive-still-published/", "A deactivated Payment Link is still linked from your site"),
],
"citations": [CITE_PMD_OBJ, CITE_PMD_REG, CITE_APPLE_PAY, CITE_KEYS],
},

]
