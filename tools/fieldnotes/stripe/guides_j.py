#!/usr/bin/env python3
"""/stripe/ field notes, batch J — the writing.

Four notes about the part of the integration that sits between a card and a
customer: PaymentMethods that were never attached, cards about to expire,
customers with no email to send anything to, and SetupIntents the client never
confirmed.

Same constraint as every other batch in this section: each note is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.
"""

CITE_PM_OBJ = ("The PaymentMethod object — Stripe API reference",
               "https://docs.stripe.com/api/payment_methods/object")
CITE_PM_LIST = ("List PaymentMethods — Stripe API reference",
                "https://docs.stripe.com/api/payment_methods/list")
CITE_PM_ATTACH = ("Attach a PaymentMethod to a Customer — Stripe API reference",
                  "https://docs.stripe.com/api/payment_methods/attach")
CITE_SAVE_DURING = ("Save a payment method during payment — Stripe Docs",
                    "https://docs.stripe.com/payments/save-during-payment")
CITE_SAVE_REUSE = ("Save and reuse payment methods — Stripe Docs",
                   "https://docs.stripe.com/payments/save-and-reuse")
CITE_CARDS = ("Cards overview — Stripe Docs",
              "https://docs.stripe.com/payments/cards/overview")
CITE_PORTAL_SESSIONS = ("Create a customer portal session — Stripe API reference",
                        "https://docs.stripe.com/api/customer_portal/sessions/create")
CITE_SMART_RETRIES = ("Smart Retries — Stripe Docs",
                      "https://docs.stripe.com/billing/revenue-recovery/smart-retries")
CITE_CUSTOMER_OBJ = ("The Customer object — Stripe API reference",
                     "https://docs.stripe.com/api/customers/object")
CITE_CUSTOMER_UPDATE = ("Update a customer — Stripe API reference",
                        "https://docs.stripe.com/api/customers/update")
CITE_RECEIPTS = ("Receipts — Stripe Docs", "https://docs.stripe.com/receipts")
CITE_PI_OBJ = ("The PaymentIntent object — Stripe API reference",
               "https://docs.stripe.com/api/payment_intents/object")
CITE_SI_OBJ = ("The SetupIntent object — Stripe API reference",
               "https://docs.stripe.com/api/setup_intents/object")
CITE_SI_LIST = ("List SetupIntents — Stripe API reference",
                "https://docs.stripe.com/api/setup_intents/list")
CITE_LIFECYCLE = ("The PaymentIntent lifecycle — Stripe Docs",
                  "https://docs.stripe.com/payments/paymentintents/lifecycle")

GUIDES = [

{
"slug": "unattached-payment-methods-orphaned",
"title": "PaymentMethods are created but never attached to a customer",
"description": "Reusing a saved card fails with payment_method_unexpected_state. The pm_ id in your database was consumed once and can never be charged again.",
"h1": "PaymentMethods are created but never attached to a customer",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["payment_method_unexpected_state", "stripe payment method not attached",
             "stripe reuse saved card fails", "stripe attach payment method",
             "setup_future_usage off_session"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The first charge works. The customer comes back a month later, picks their saved card, and the request fails with a sentence about a PaymentMethod that was previously used without being attached to a Customer. The <code>pm_</code> id is right there in your database, it looks fine, and it will never work again.",
"short_answer": """<p>Page <code>GET /v1/payment_methods?type=card</code> and count the ones where <code>customer</code> is <code>null</code> and <code>created</code> is more than a day old. Those were minted by Elements and never attached to anyone. Compare that against the attached population: the orphan share is the rate at which your integration is throwing saved cards away.</p>
<p>Confirm the mechanism from the payment side. <code>GET /v1/payment_intents</code> counting intents where <code>customer</code> is set but <code>setup_future_usage</code> is <code>null</code> finds the exact code path that charges a customer's card and then discards it, and <code>last_payment_error.code == "payment_method_unexpected_state"</code> counts the reuses that have already failed.</p>""",
"problem": """<p>A PaymentMethod created in the browser belongs to nobody. <code>customer</code> is <code>null</code> and stays that way unless something attaches it. That is not a bug; it is what lets you collect card details before you have decided which Customer they belong to. The trap is that the object is perfectly usable exactly once, so nothing goes wrong on the day you write the code.</p>
<p>Once an unattached PaymentMethod has been consumed by a PaymentIntent, it is burned. Not expired, not detached, not recoverable: the id resolves, the object is still readable through the API, and any attempt to charge it again is rejected. So your database fills up with card records that render a brand and a <code>last4</code> in your UI, and every one of them is a checkout that will fail at the last step.</p>""",
"why": """<p><strong>Saving a card is a parameter, not a side effect.</strong> Charging a customer and saving their card look like one action from the outside and are two in the API. A PaymentIntent with <code>customer</code> set will happily charge and then leave nothing behind, because <code>setup_future_usage</code> was never passed. Nothing warns you; the payment succeeded, which is what you were watching.</p>
<p><strong>The failure is separated from its cause by weeks.</strong> The mistake happens at the first checkout. The symptom appears at the second one, which for a typical customer is a month or a quarter later. By then the deploy that introduced it is long merged, and the error message points at the reuse rather than at the save.</p>
<p><strong>The error message reads like a permissions problem.</strong> "This PaymentMethod was previously used without being attached to a Customer or was detached from a Customer, and may not be used again" describes two entirely different histories in one sentence. Teams spend the first hour looking for the code that detached it, and there is none.</p>
<p><strong>A bare attach is not the same as saving during payment.</strong> <code>POST /v1/payment_methods/{id}/attach</code> works and is the obvious fix, but it skips the setup that <code>setup_future_usage</code> performs at confirmation time &mdash; the issuer never sees that this credential is being stored for later, so subsequent off-session charges are more likely to be declined for authentication.</p>""",
"steps": [
 {"h": "Count the orphans, and give them a day to grow up",
  "body": """<p><code>GET /v1/payment_methods?type=card&amp;limit=100</code> without a <code>customer</code> parameter lists the account-wide population. An unattached PaymentMethod created in the last few minutes is a checkout in progress, not a leak, so only count the ones older than 24 hours.</p>"""},
 {"h": "Turn the count into a ratio",
  "body": """<p>Two hundred orphans means nothing on its own. Two hundred orphans against two hundred attached cards means half of every card your customers enter is discarded. The ratio is the number that tells you whether this is residue from an old integration or the current behaviour of your checkout.</p>"""},
 {"h": "Find the code path in the PaymentIntents",
  "body": """<p>An intent with <code>customer</code> set and <code>setup_future_usage</code> unset is the smoking gun: that request knew who the customer was and still did not save the card. Counting them tells you the fix is one parameter, and roughly how much of your traffic goes through it.</p>"""},
 {"h": "Count the reuses that already failed",
  "body": """<p><code>last_payment_error.code == "payment_method_unexpected_state"</code> on recent PaymentIntents is the customer-visible half. If that count is above zero this is not a hygiene finding, it is a live checkout failure with a queue of affected customers behind it.</p>"""},
 {"h": "Save at confirmation time, not afterwards",
  "body": """<p>Pass <code>customer</code> and <code>setup_future_usage=off_session</code> on the PaymentIntent, and the PaymentMethod is attached for you when the payment succeeds. To store a card without charging it, create a SetupIntent with <code>usage=off_session</code>. Reserve the bare attach call for migrating cards you already hold.</p>"""},
],
"verify": """<p>Re-run the script after a deploy. New PaymentMethods should arrive attached, so the orphan count stops growing even while the historical residue is still there.</p>
<pre><code class="language-bash">python3 stripe_orphaned_payment_methods.py
# clear      every card PaymentMethod in the window is attached to a customer</code></pre>""",
"code_intro": "Two paginated GETs and nothing else &mdash; a restricted key with read access to PaymentMethods and PaymentIntents is enough, and is what you should give it. The classification is a pure function taking four counts, because the difference between \"residue from 2022\" and \"half of today's checkouts\" is a ratio, and a ratio is the kind of thing that is easy to get backwards and impossible to notice.",
"py_file": "stripe_orphaned_payment_methods.py",
"py": '''"""Report Stripe PaymentMethods that were never attached to a Customer.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
PaymentMethods and PaymentIntents. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_orphaned_payment_methods")

API = "https://api.stripe.com/v1"

MIN_AGE_HOURS = 24    # younger than this is a checkout still in progress
WARN_RATIO = 0.25     # a quarter of cards discarded is a code path, not residue
HIGH_RATIO = 0.50


def verdict(orphans, attached, unsaved_intents, reuse_errors):
    """Classify the orphan population. Pure, so the ratios can be tested offline.

    orphans        unattached card PaymentMethods older than MIN_AGE_HOURS
    attached       card PaymentMethods with a customer set
    unsaved_intents PaymentIntents with a customer but no setup_future_usage
    reuse_errors   PaymentIntents that failed with payment_method_unexpected_state

    Returns (state, detail).
    """
    total = orphans + attached
    if reuse_errors:
        return ("burned",
                "%d PaymentIntent(s) failed with payment_method_unexpected_state: "
                "a consumed pm_ is already being charged a second time. %d orphan(s) "
                "on the account." % (reuse_errors, orphans))
    if not total:
        return ("clear",
                "no card PaymentMethods older than %d hours to judge" % MIN_AGE_HOURS)
    ratio = orphans / float(total)
    if ratio >= HIGH_RATIO:
        return ("leaking",
                "%d of %d card PaymentMethods (%.0f%%) were never attached. This is "
                "the current behaviour of the checkout, not old residue."
                % (orphans, total, ratio * 100))
    if unsaved_intents:
        return ("unsaved",
                "%d PaymentIntent(s) charged a known customer with setup_future_usage "
                "unset, so those cards were discarded after one use. %d orphan(s) so "
                "far." % (unsaved_intents, orphans))
    if ratio >= WARN_RATIO:
        return ("orphaned",
                "%d of %d card PaymentMethods (%.0f%%) have no customer. Reusing any "
                "of them will fail." % (orphans, total, ratio * 100))
    if orphans:
        return ("residue",
                "%d of %d card PaymentMethods have no customer. Small enough to be "
                "history rather than the live path." % (orphans, total))
    return ("clear", "every card PaymentMethod in the window is attached to a customer")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Yield objects from a paginated list endpoint until `limit` is reached."""
    seen = 0
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-objects", type=int, default=2000,
                    help="stop paginating each list after this many objects")
    ap.add_argument("--min-age-hours", type=float, default=MIN_AGE_HOURS,
                    help="ignore unattached PaymentMethods younger than this")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    cutoff = time.time() - args.min_age_hours * 3600.0
    orphans = attached = 0
    sample = []
    for pm in page_all(s, "/payment_methods", args.max_objects, type="card", limit=100):
        if pm.get("customer"):
            attached += 1
        elif (pm.get("created") or 0) < cutoff:
            orphans += 1
            if len(sample) < 5:
                sample.append(pm.get("id"))

    unsaved = reuse_errors = 0
    for pi in page_all(s, "/payment_intents", args.max_objects, limit=100):
        if pi.get("customer") and not pi.get("setup_future_usage"):
            unsaved += 1
        err = pi.get("last_payment_error") or {}
        if err.get("code") == "payment_method_unexpected_state":
            reuse_errors += 1

    state, detail = verdict(orphans, attached, unsaved, reuse_errors)
    line = "%-9s %s" % (state, detail)
    if state == "clear":
        log.info(line)
        return 0

    log.warning(line)
    for pm_id in sample:
        log.warning("  orphan %s", pm_id)
    log.warning("  save the card as part of the payment rather than storing the id:")
    log.warning("  POST %s/payment_intents -d customer=cus_X "
                "-d setup_future_usage=off_session", API)
    log.warning("  to store a card without charging it:")
    log.warning("  POST %s/setup_intents -d customer=cus_X -d usage=off_session", API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-orphaned-payment-methods.mjs",
"js": '''/**
 * Report Stripe PaymentMethods that were never attached to a Customer.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to PaymentMethods and PaymentIntents. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const MIN_AGE_HOURS = 24; // younger than this is a checkout in progress
const WARN_RATIO = 0.25;
const HIGH_RATIO = 0.50;

/**
 * Classify the orphan population. Pure, so the ratios can be tested offline.
 * Returns [state, detail].
 */
export function verdict(orphans, attached, unsavedIntents, reuseErrors) {
  const total = orphans + attached;
  if (reuseErrors) {
    return ['burned',
      `${reuseErrors} PaymentIntent(s) failed with payment_method_unexpected_state: ` +
      `a consumed pm_ is already being charged a second time. ${orphans} orphan(s) ` +
      'on the account.'];
  }
  if (!total) {
    return ['clear', `no card PaymentMethods older than ${MIN_AGE_HOURS} hours to judge`];
  }
  const ratio = orphans / total;
  const pct = (ratio * 100).toFixed(0);
  if (ratio >= HIGH_RATIO) {
    return ['leaking',
      `${orphans} of ${total} card PaymentMethods (${pct}%) were never attached. ` +
      'This is the current behaviour of the checkout, not old residue.'];
  }
  if (unsavedIntents) {
    return ['unsaved',
      `${unsavedIntents} PaymentIntent(s) charged a known customer with ` +
      `setup_future_usage unset, so those cards were discarded after one use. ` +
      `${orphans} orphan(s) so far.`];
  }
  if (ratio >= WARN_RATIO) {
    return ['orphaned',
      `${orphans} of ${total} card PaymentMethods (${pct}%) have no customer. ` +
      'Reusing any of them will fail.'];
  }
  if (orphans) {
    return ['residue',
      `${orphans} of ${total} card PaymentMethods have no customer. Small enough ` +
      'to be history rather than the live path.'];
  }
  return ['clear', 'every card PaymentMethod in the window is attached to a customer'];
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

export async function pageAll(key, path, limit, params = {}) {
  const out = [];
  const q = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, q);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) return out;
    q.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const cutoff = Date.now() / 1000 - MIN_AGE_HOURS * 3600;
  let orphans = 0;
  let attached = 0;
  const sample = [];
  for (const pm of await pageAll(key, '/payment_methods', 2000, { type: 'card' })) {
    if (pm.customer) attached += 1;
    else if ((pm.created ?? 0) < cutoff) {
      orphans += 1;
      if (sample.length < 5) sample.push(pm.id);
    }
  }

  let unsaved = 0;
  let reuseErrors = 0;
  for (const pi of await pageAll(key, '/payment_intents', 2000)) {
    if (pi.customer && !pi.setup_future_usage) unsaved += 1;
    if (pi.last_payment_error?.code === 'payment_method_unexpected_state') reuseErrors += 1;
  }

  const [state, detail] = verdict(orphans, attached, unsaved, reuseErrors);
  const line = `${state.padEnd(9)} ${detail}`;
  if (state === 'clear') { console.log(line); return; }

  console.warn(line);
  for (const id of sample) console.warn(`  orphan ${id}`);
  console.warn('  save the card as part of the payment rather than storing the id:');
  console.warn(`  POST ${API}/payment_intents -d customer=cus_X -d setup_future_usage=off_session`);
  console.warn('  to store a card without charging it:');
  console.warn(`  POST ${API}/setup_intents -d customer=cus_X -d usage=off_session`);
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are about precedence and about the two ratios. A reuse that has already failed has to outrank every hygiene finding, because it is a customer at a checkout right now, and 25% has to mean 25% rather than 26% &mdash; a threshold that is off by a rounding is a threshold that reports the wrong shape of problem on the exact day someone reads it.",
"test_py_file": "test_stripe_orphaned_payment_methods.py",
"test_py": '''from stripe_orphaned_payment_methods import verdict


def test_nothing_to_judge_is_clear():
    assert verdict(0, 0, 0, 0)[0] == "clear"


def test_all_attached_is_clear():
    state, detail = verdict(0, 40, 0, 0)
    assert state == "clear"
    assert "attached" in detail


def test_a_failed_reuse_outranks_every_hygiene_finding():
    # Small orphan count, tiny ratio, but a customer is failing at checkout now.
    state, detail = verdict(1, 999, 0, 3)
    assert state == "burned"
    assert "payment_method_unexpected_state" in detail


def test_half_the_cards_orphaned_is_the_live_path():
    state, detail = verdict(50, 50, 0, 0)
    assert state == "leaking"
    assert "50%" in detail


def test_the_warn_ratio_is_inclusive():
    # 24% is residue, 25% is a code path. Off by one on this boundary reports
    # an active leak as history.
    assert verdict(2, 8, 0, 0)[0] == "residue"
    assert verdict(25, 75, 0, 0)[0] == "orphaned"


def test_unsaved_intents_are_named_even_with_few_orphans():
    state, detail = verdict(3, 97, 12, 0)
    assert state == "unsaved"
    assert "setup_future_usage" in detail
''',
"test_js_file": "stripe-orphaned-payment-methods.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-orphaned-payment-methods.mjs';

test('nothing to judge is clear', () => {
  assert.equal(verdict(0, 0, 0, 0)[0], 'clear');
});

test('all attached is clear', () => {
  const [state, detail] = verdict(0, 40, 0, 0);
  assert.equal(state, 'clear');
  assert.match(detail, /attached/);
});

test('a failed reuse outranks every hygiene finding', () => {
  const [state, detail] = verdict(1, 999, 0, 3);
  assert.equal(state, 'burned');
  assert.match(detail, /payment_method_unexpected_state/);
});

test('half the cards orphaned is the live path', () => {
  const [state, detail] = verdict(50, 50, 0, 0);
  assert.equal(state, 'leaking');
  assert.match(detail, /50%/);
});

test('the warn ratio is inclusive', () => {
  assert.equal(verdict(2, 8, 0, 0)[0], 'residue');
  assert.equal(verdict(25, 75, 0, 0)[0], 'orphaned');
});

test('unsaved intents are named even with few orphans', () => {
  const [state, detail] = verdict(3, 97, 12, 0);
  assert.equal(state, 'unsaved');
  assert.match(detail, /setup_future_usage/);
});
''',
"faq": [
 ("What does payment_method_unexpected_state actually mean?",
  "That the PaymentMethod is not in a state where it can be used for this request. In practice it almost always means the object was created without a customer, consumed by one PaymentIntent, and is now being charged again. The same error also covers a PaymentMethod that was detached, which is why the message names both histories."),
 ("Can I attach an orphaned PaymentMethod after the fact?",
  "Only if it has not been used yet. An unattached PaymentMethod that has never been confirmed can still be attached with POST /v1/payment_methods/{id}/attach. Once a PaymentIntent has consumed it, nothing brings it back and the customer has to enter the card again."),
 ("Is setup_future_usage=off_session or on_session the right value?",
  "off_session if you will ever charge the card when the customer is not there, which includes every subscription renewal and every retry. on_session records consent only for customer-present reuse, and unattended charges against it are more likely to be declined for authentication."),
 ("Why not just call attach every time?",
  "It works, but it skips what setup_future_usage does at confirmation. Passing the parameter tells the issuer during authorization that the credential is being stored, which is what makes later off-session charges succeed. A bare attach saves the card without that signal."),
 ("Does listing PaymentMethods without a customer parameter work?",
  "Yes. The customer parameter on GET /v1/payment_methods is optional; omitting it lists the account-wide population, which is the only way to see the orphans at all, since by definition they belong to no customer to filter by."),
],
"related": [
 ("/stripe/setup-intents-never-confirmed/", "SetupIntents are created but never confirmed by the client"),
 ("/stripe/expired-saved-cards-attached/", "Saved cards are already expired but still attached"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
],
"citations": [CITE_PM_LIST, CITE_PM_ATTACH, CITE_SAVE_DURING, CITE_PM_OBJ],
},

{
"slug": "cards-expiring-within-60-days",
"title": "Saved cards expire within 60 days and nothing warns anyone",
"description": "Churn arrives in monthly clusters that map exactly to card expiry dates. The date was in the API for years before the decline that revealed it.",
"h1": "saved cards expire within 60 days and nothing warns anyone",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe card expiring soon", "stripe card updater coverage",
             "involuntary churn stripe", "exp_month exp_year stripe",
             "stripe customer portal update card"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The churn chart has lumps in it, and the lumps are always at the end of a month. Nobody cancelled. Their card expired, the renewal declined, and the first the customer heard about it was a failed-payment email that reads like an accusation. The expiry date was sitting in the API from the day they saved the card.",
"short_answer": """<p>For every customer with an active subscription, read <code>GET /v1/payment_methods?customer={id}&amp;type=card</code> and turn <code>card.exp_month</code> and <code>card.exp_year</code> into an actual instant: a card dies at the <em>start of the month after</em> its expiry month. Flag anything falling inside the next 60 days.</p>
<p>Sort what you find. A card that is also the billing default is the next failed renewal. A card with <code>card.wallet.type</code> of <code>apple_pay</code> or <code>google_pay</code> is a network token that survives the plastic being reissued, so warning that customer is noise.</p>""",
"problem": """<p>This is the preventable half of an expired card. Everything needed to stop it is knowable months ahead: the expiry month is on the PaymentMethod from the moment it is stored, and it does not change. The overwhelmingly common design still waits for the decline and then starts dunning, which means recovery depends on an email persuading someone to re-enter card details after you have already failed to charge them.</p>
<p>Stripe's automatic card updater takes some of this off your hands, and that is exactly what makes it hard to reason about. It covers a good share of US-issued Visa, Mastercard, Amex and Discover reissues; coverage elsewhere is partial and varies by issuer and country. No field tells you which of your saved cards participate. So the outcome is a coin flip you cannot inspect, and the only thing under your control is whether the customer was warned.</p>""",
"why": """<p><strong>A card is valid through the end of its expiry month, not the start.</strong> A card marked 04/2029 works on 30 April 2029. Comparing <code>exp_month</code> against the current month with <code>&lt;=</code> declares a working card dead for its final month, and a system built on that emails customers to replace cards that are fine. Compute the expiry as the first instant of the following month and the off-by-one disappears.</p>
<p><strong>December is where the arithmetic breaks.</strong> The next month after 12 is 1 of the following year. Any code that adds one to the month without rolling the year over gets month 13, which most date libraries either reject or silently normalise in a way that differs between Python and JavaScript. That is a bug that only fires for one twelfth of your cards, in December.</p>
<p><strong>Not every credential expires with the plastic.</strong> Apple Pay, Google Pay and Link save network tokens rather than the raw card number. When the issuer reissues the card, the token follows. Warning those customers costs you a support ticket and some credibility, so read <code>card.wallet</code> and <code>card.networks</code> and leave them out.</p>
<p><strong>The default card is a different finding from the rest.</strong> A customer with four saved cards, one expiring, has an untidy account page. A customer whose <code>invoice_settings.default_payment_method</code> expires in three weeks has a renewal that is going to fail on a date you can name. Those two should never sit in the same bucket in a report.</p>""",
"steps": [
 {"h": "Start from the subscriptions, not the customers",
  "body": """<p><code>GET /v1/subscriptions?status=active&amp;limit=100</code> gives you the customers where an expiring card actually costs money. Sweeping every Customer on the account buries the finding under one-off purchasers from three years ago whose dead cards cost you nothing.</p>"""},
 {"h": "Convert the expiry to an instant",
  "body": """<p>The card stops working at the start of the month after <code>exp_month</code>. Roll December into January of the next year explicitly rather than trusting month arithmetic to normalise, then subtract from now to get days remaining.</p>"""},
 {"h": "Exclude the credentials that survive reissue",
  "body": """<p>Read <code>card.wallet.type</code>. A value of <code>apple_pay</code>, <code>google_pay</code> or <code>link</code> means a network token, which is reissued along with the card. Those belong in a separate bucket that nobody emails.</p>"""},
 {"h": "Split the defaults out",
  "body": """<p>Compare each expiring PaymentMethod against <code>customer.invoice_settings.default_payment_method</code> and the subscription's own <code>default_payment_method</code>. Those are the ones with a dated consequence, and they are the list the nudge campaign should run against first.</p>"""},
 {"h": "Nudge at 45 days, then let the recovery tools do the rest",
  "body": """<p>Email a Customer Portal link (<code>POST /v1/billing_portal/sessions</code>) well before the expiry rather than after the decline. Turn on Smart Retries so the cards you do not save are retried on a schedule that recovers more than a fixed one, and encourage wallet saves at checkout, since those tokens do not expire with the plastic.</p>"""},
],
"verify": """<p>Re-run the script after the nudges have gone out. The default-card bucket is the one that should empty; the rest is a list you keep watching.</p>
<pre><code class="language-bash">python3 stripe_card_expiry_window.py
# ok         cus_QxAbc123  pm_1Nx  expires in 240 day(s), outside the 60 day window</code></pre>""",
"code_intro": "Two GETs per customer, no writes &mdash; a restricted key with read access to Subscriptions, Customers and PaymentMethods covers it. Both pure functions are exported: the one that turns a month and a year into the instant the card dies, and the one that sorts a card by how long it has left. The date conversion is separate precisely because December and the last day of a month are where this check goes wrong, and neither is something you want to discover from a customer.",
"py_file": "stripe_card_expiry_window.py",
"py": '''"""Report saved Stripe cards expiring within the next 60 days.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Subscriptions, Customers and PaymentMethods. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import datetime as dt
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_card_expiry_window")

API = "https://api.stripe.com/v1"

WINDOW_DAYS = 60      # how far ahead to look
NUDGE_DAYS = 45       # when to send the first email
# Wallet-backed credentials are network tokens: the issuer reissues them along
# with the card, so their printed expiry date is not a churn event.
TOKENISED_WALLETS = ("apple_pay", "google_pay", "link", "samsung_pay")


def expires_at(exp_month, exp_year):
    """Unix seconds at which a card stops being valid.

    A card is good through the END of its expiry month, so the instant it dies is
    the start of the following month. December rolls the year over explicitly
    rather than relying on month 13 normalising the way you hope.
    """
    month, year = int(exp_month), int(exp_year)
    if month == 12:
        month, year = 1, year + 1
    else:
        month += 1
    return int(dt.datetime(year, month, 1, tzinfo=dt.timezone.utc).timestamp())


def verdict(days_left, is_default=False, wallet=None):
    """Classify one saved card. Pure, so the boundaries can be tested offline.

    `days_left` is None when the PaymentMethod carries no usable expiry.
    Returns (state, detail).
    """
    if days_left is None:
        return ("unreadable", "no exp_month/exp_year on this payment method")
    if days_left <= 0:
        return ("expired",
                "already expired%s; this is a decline that has happened, not one "
                "coming" % (" and it is the billing default" if is_default else ""))
    if wallet in TOKENISED_WALLETS:
        return ("tokenised",
                "prints an expiry in %.0f day(s) but is a %s credential, which is "
                "reissued with the card. Do not email this customer."
                % (days_left, wallet))
    if days_left > WINDOW_DAYS:
        return ("ok", "expires in %.0f day(s), outside the %d day window"
                % (days_left, WINDOW_DAYS))
    if is_default:
        return ("urgent",
                "expires in %.0f day(s) and is the billing default: name the renewal "
                "that fails and email the portal link today" % days_left)
    return ("warn",
            "expires in %.0f day(s); the nudge belongs at %d days, before the "
            "decline rather than after it" % (days_left, NUDGE_DAYS))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Yield objects from a paginated list endpoint until `limit` is reached."""
    seen = 0
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=1000,
                    help="stop after this many active subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    flagged = 0
    seen_customers = set()
    for sub in page_all(s, "/subscriptions", args.max_subscriptions,
                        status="active", limit=100):
        cid = sub.get("customer")
        if not cid or cid in seen_customers:
            continue
        seen_customers.add(cid)

        customer = get(s, "/customers/" + cid)
        invoice_settings = customer.get("invoice_settings") or {}
        defaults = {sub.get("default_payment_method"),
                    invoice_settings.get("default_payment_method")}
        defaults.discard(None)

        pms = get(s, "/payment_methods", customer=cid, type="card", limit=100)
        for pm in pms.get("data", []):
            card = pm.get("card") or {}
            if not card.get("exp_month") or not card.get("exp_year"):
                days_left = None
            else:
                days_left = (expires_at(card["exp_month"], card["exp_year"]) - now) / 86400.0
            wallet = (card.get("wallet") or {}).get("type")
            state, detail = verdict(days_left, pm.get("id") in defaults, wallet)

            line = "%-10s %s  %s  %s" % (state, cid, pm.get("id"), detail)
            if state in ("ok", "tokenised"):
                log.info(line)
                continue
            log.warning(line)
            flagged += 1

    if not flagged:
        log.info("clear      no card on an active subscription expires within %d days",
                 WINDOW_DAYS)
        return 0

    log.warning("  %d card(s) need a nudge. Email a portal link, do not wait for "
                "the decline:", flagged)
    log.warning("  POST %s/billing_portal/sessions -d customer=cus_X "
                "-d return_url=https://example.com/billing", API)
    log.warning("  and turn on Smart Retries at "
                "https://dashboard.stripe.com/settings/billing/automatic")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-card-expiry-window.mjs",
"js": '''/**
 * Report saved Stripe cards expiring within the next 60 days.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to Subscriptions, Customers and PaymentMethods. The repair is printed only.
 */
const API = 'https://api.stripe.com/v1';

export const WINDOW_DAYS = 60; // how far ahead to look
const NUDGE_DAYS = 45;         // when to send the first email
// Wallet-backed credentials are network tokens: the issuer reissues them along
// with the card, so their printed expiry date is not a churn event.
const TOKENISED_WALLETS = new Set(['apple_pay', 'google_pay', 'link', 'samsung_pay']);

/**
 * Unix seconds at which a card stops being valid: the start of the month after
 * its expiry month, with December rolled into the next year explicitly.
 */
export function expiresAt(expMonth, expYear) {
  let month = Number(expMonth);
  let year = Number(expYear);
  if (month === 12) { month = 1; year += 1; } else { month += 1; }
  return Date.UTC(year, month - 1, 1) / 1000;
}

/**
 * Classify one saved card. Pure, so the boundaries can be tested offline.
 * `daysLeft` is null when the PaymentMethod carries no usable expiry.
 */
export function verdict(daysLeft, isDefault = false, wallet = null) {
  if (daysLeft === null || daysLeft === undefined) {
    return ['unreadable', 'no exp_month/exp_year on this payment method'];
  }
  if (daysLeft <= 0) {
    return ['expired',
      `already expired${isDefault ? ' and it is the billing default' : ''}; ` +
      'this is a decline that has happened, not one coming'];
  }
  if (TOKENISED_WALLETS.has(wallet)) {
    return ['tokenised',
      `prints an expiry in ${daysLeft.toFixed(0)} day(s) but is a ${wallet} ` +
      'credential, which is reissued with the card. Do not email this customer.'];
  }
  if (daysLeft > WINDOW_DAYS) {
    return ['ok',
      `expires in ${daysLeft.toFixed(0)} day(s), outside the ${WINDOW_DAYS} day window`];
  }
  if (isDefault) {
    return ['urgent',
      `expires in ${daysLeft.toFixed(0)} day(s) and is the billing default: name ` +
      'the renewal that fails and email the portal link today'];
  }
  return ['warn',
    `expires in ${daysLeft.toFixed(0)} day(s); the nudge belongs at ${NUDGE_DAYS} ` +
    'days, before the decline rather than after it'];
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

export async function pageAll(key, path, limit, params = {}) {
  const out = [];
  const q = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, q);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) return out;
    q.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const now = Date.now() / 1000;
  let flagged = 0;
  const seen = new Set();
  for (const sub of await pageAll(key, '/subscriptions', 1000, { status: 'active' })) {
    const cid = sub.customer;
    if (!cid || seen.has(cid)) continue;
    seen.add(cid);

    const customer = await get(key, `/customers/${cid}`);
    const defaults = new Set([
      sub.default_payment_method,
      customer.invoice_settings?.default_payment_method,
    ].filter(Boolean));

    const pms = await get(key, '/payment_methods', { customer: cid, type: 'card', limit: 100 });
    for (const pm of pms.data ?? []) {
      const card = pm.card ?? {};
      const daysLeft = (card.exp_month && card.exp_year)
        ? (expiresAt(card.exp_month, card.exp_year) - now) / 86400
        : null;
      const [state, detail] = verdict(daysLeft, defaults.has(pm.id), card.wallet?.type ?? null);

      const line = `${state.padEnd(10)} ${cid}  ${pm.id}  ${detail}`;
      if (state === 'ok' || state === 'tokenised') { console.log(line); continue; }
      console.warn(line);
      flagged += 1;
    }
  }

  if (!flagged) {
    console.log(`clear      no card on an active subscription expires within ${WINDOW_DAYS} days`);
    return;
  }

  console.warn(`  ${flagged} card(s) need a nudge. Email a portal link, do not wait for the decline:`);
  console.warn(`  POST ${API}/billing_portal/sessions -d customer=cus_X -d return_url=https://example.com/billing`);
  console.warn('  and turn on Smart Retries at https://dashboard.stripe.com/settings/billing/automatic');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are tested and they are the two things that break: the calendar and the window edge. December has to roll into January of the next year, a card has to stay valid through the last day of its expiry month, and 60 days has to be inside the window while 61 is outside. A wallet credential has to fall out of the warning list before anything else looks at it.",
"test_py_file": "test_stripe_card_expiry_window.py",
"test_py": '''import datetime as dt

from stripe_card_expiry_window import expires_at, verdict


def utc(year, month):
    return int(dt.datetime(year, month, 1, tzinfo=dt.timezone.utc).timestamp())


def test_a_card_is_valid_through_the_end_of_its_month():
    # 04/2029 dies at the first instant of May, not of April.
    assert expires_at(4, 2029) == utc(2029, 5)


def test_december_rolls_into_the_next_year():
    assert expires_at(12, 2026) == utc(2027, 1)


def test_february_of_a_leap_year_still_lands_on_march():
    assert expires_at(2, 2028) == utc(2028, 3)


def test_an_expiry_already_past_is_a_decline_that_happened():
    state, detail = verdict(-3.0, is_default=True)
    assert state == "expired"
    assert "billing default" in detail


def test_the_window_edge_is_inclusive():
    assert verdict(60.0)[0] == "warn"
    assert verdict(60.1)[0] == "ok"


def test_the_default_card_is_its_own_bucket():
    assert verdict(20.0)[0] == "warn"
    assert verdict(20.0, is_default=True)[0] == "urgent"


def test_wallet_credentials_are_not_warned_about():
    state, detail = verdict(10.0, is_default=True, wallet="apple_pay")
    assert state == "tokenised"
    assert "reissued" in detail


def test_a_card_with_no_expiry_is_not_silently_fine():
    assert verdict(None)[0] == "unreadable"
''',
"test_js_file": "stripe-card-expiry-window.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { expiresAt, verdict } from './stripe-card-expiry-window.mjs';

test('a card is valid through the end of its month', () => {
  assert.equal(expiresAt(4, 2029), Date.UTC(2029, 4, 1) / 1000);
});

test('december rolls into the next year', () => {
  assert.equal(expiresAt(12, 2026), Date.UTC(2027, 0, 1) / 1000);
});

test('february of a leap year still lands on march', () => {
  assert.equal(expiresAt(2, 2028), Date.UTC(2028, 2, 1) / 1000);
});

test('an expiry already past is a decline that happened', () => {
  const [state, detail] = verdict(-3.0, true);
  assert.equal(state, 'expired');
  assert.match(detail, /billing default/);
});

test('the window edge is inclusive', () => {
  assert.equal(verdict(60.0)[0], 'warn');
  assert.equal(verdict(60.1)[0], 'ok');
});

test('the default card is its own bucket', () => {
  assert.equal(verdict(20.0)[0], 'warn');
  assert.equal(verdict(20.0, true)[0], 'urgent');
});

test('wallet credentials are not warned about', () => {
  const [state, detail] = verdict(10.0, true, 'apple_pay');
  assert.equal(state, 'tokenised');
  assert.match(detail, /reissued/);
});

test('a card with no expiry is not silently fine', () => {
  assert.equal(verdict(null)[0], 'unreadable');
});
''',
"faq": [
 ("Does the automatic card updater not handle this?",
  "Partly. It covers many US-issued Visa, Mastercard, Amex and Discover reissues, and coverage elsewhere is partial and varies by issuer and country. No API field tells you which of your saved cards participate, so you cannot predict per card whether it will self-heal. The nudge is what you control."),
 ("Is a card valid on the last day of its expiry month?",
  "Yes. A card marked 04/2029 works through 30 April 2029 and stops at the first instant of May. Computing the expiry as the start of the following month gets this right without a special case for month lengths or leap years."),
 ("Why exclude Apple Pay and Google Pay cards?",
  "Because card.wallet.type of apple_pay or google_pay means the PaymentMethod holds a network token rather than the raw card number. When the issuer reissues the card, the token is updated and the charge keeps working. Emailing those customers about an expiry that will not affect them costs support time and trust."),
 ("What is the right lead time for the email?",
  "Around 45 days. It is far enough ahead that the customer is not being asked to fix something urgent, and close enough that the message is still relevant when it arrives. Sending after the decline turns a housekeeping email into a failure notice."),
 ("Should I check every customer or only subscribers?",
  "Only customers with an active subscription, or with an upcoming invoice. A dead card on a one-off purchaser from two years ago costs nothing and buries the findings that do cost something."),
],
"related": [
 ("/stripe/expired-saved-cards-attached/", "Saved cards are already expired but still attached"),
 ("/stripe/dunning-retries-exhausted/", "Dunning ran out of retries and no attempt is scheduled"),
 ("/stripe/unattached-payment-methods-orphaned/", "PaymentMethods are created but never attached to a customer"),
],
"citations": [CITE_PM_OBJ, CITE_CARDS, CITE_PORTAL_SESSIONS, CITE_SMART_RETRIES],
},

{
"slug": "customers-missing-email",
"title": "Customers have no email, so Stripe sends no receipts",
"description": "Cardholders open unrecognised-charge disputes because no receipt ever arrived, and dunning emails for failed renewals go nowhere at all.",
"h1": "customers have no email, so Stripe sends no receipts",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe customer email null", "stripe receipt not sent",
             "stripe receipt_email", "stripe dunning email not received",
             "unrecognised charge dispute stripe"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A dispute arrives with the reason &ldquo;unrecognised&rdquo;. The cardholder is a real, current customer, and they are not lying: they never got a receipt, so the only thing linking that line on their statement to your business is a descriptor they have never seen before. The Customer record has an email column and it is empty.",
"short_answer": """<p>Page <code>GET /v1/customers</code> and count the ones where <code>email</code> is null or empty, as a number and as a share of the total. Then weight it: for each of those, <code>GET /v1/subscriptions?customer={id}&amp;status=active</code>. An emailless customer with an active subscription is not a data-quality issue, it is an account that dunning can never reach.</p>
<p>Cover the guest path too. <code>GET /v1/charges</code> counting rows where both <code>customer</code> and <code>receipt_email</code> are null finds the one-off payments that produced no receipt at all. Cross-check <code>disputed</code> on the emailless cohort to see what it has already cost.</p>""",
"problem": """<p>Stripe sends receipts and dunning notices to one of two places: <code>customer.email</code>, or the <code>receipt_email</code> on the individual payment. If neither is set, nothing is sent, and nothing reports that nothing was sent. There is no bounce, no error, no field on the charge saying the receipt went nowhere. The payment succeeded, which is the only thing anybody is watching.</p>
<p>The cost shows up twice, and neither time does it look like this. First as disputes: a customer who cannot connect a statement line to a purchase calls their bank, and you lose the amount plus the dispute fee on a charge that was entirely legitimate. Second as failed renewals that never recover, because the dunning sequence is emailing a null address while the subscription walks through its retry schedule and cancels.</p>""",
"why": """<p><strong>The Customer is usually created before you have the email.</strong> Server-side flows create the <code>cus_</code> record at signup or at the start of checkout, then collect contact details a step later and write them to your own users table. Stripe's copy stays null because nobody ever went back to update it, and your application works perfectly since it reads the email from its own database.</p>
<p><strong>Nothing in the API objects to it.</strong> <code>email</code> is optional on the Customer. Creating one without it is a 200. Charging it is a 200. Subscribing it is a 200. The first negative signal is a dispute or a churned subscriber, months later and attributed to something else.</p>
<p><strong>Guest checkout has a separate hole with the same shape.</strong> A one-off payment with no Customer at all can still send a receipt if you set <code>receipt_email</code> on the PaymentIntent. Integrations that collect an email purely for their own order confirmation frequently never pass it to Stripe, so the Stripe-side receipt &mdash; the one with the statement descriptor on it &mdash; is never sent.</p>
<p><strong>Missing receipts and friendly fraud are the same story.</strong> The receipt is what makes a charge recognisable weeks later. Take it away and an ordinary customer looking at an unfamiliar descriptor has no way to identify the purchase except by asking their bank, which is what a dispute is.</p>""",
"steps": [
 {"h": "Count the gap, as a number and a share",
  "body": """<p><code>GET /v1/customers?limit=100</code>, paginated. Count <code>email</code> that is null or an empty string &mdash; both occur, and only checking for null misses the ones written as blanks by a form. The share matters more than the count: 40 missing out of 12,000 is cleanup, 40 out of 90 is the current behaviour of your signup.</p>"""},
 {"h": "Weight by whether the customer is being billed",
  "body": """<p>For each emailless customer, check for an active subscription. Those are the accounts where the next failed payment starts a dunning sequence with nowhere to send it, and they should be at the top of the report regardless of how small the overall percentage is.</p>"""},
 {"h": "Check the guest payments separately",
  "body": """<p><code>GET /v1/charges?limit=100</code> and count rows where <code>customer</code> and <code>receipt_email</code> are both null. Those are payments that produced no receipt from Stripe at all. A high count here with a clean customer list means the gap is in the guest checkout, not in signup.</p>"""},
 {"h": "Price it with the disputes you already have",
  "body": """<p>Look at <code>disputed</code> on charges belonging to the emailless cohort. Turning "some customers have no email" into "eleven customers have no email and four of them have disputed a charge" is the difference between a backlog ticket and a fix that ships this week.</p>"""},
 {"h": "Backfill, then close the path that created it",
  "body": """<p>Write the addresses you already hold: <code>POST /v1/customers/{id} -d email=...</code>. Pass <code>email</code> at creation from then on, set <code>receipt_email</code> on guest PaymentIntents, and confirm successful-payment receipts are actually switched on under the Dashboard's email settings, since a populated field sends nothing if the setting is off.</p>"""},
],
"verify": """<p>Re-run after the backfill. The number to watch is the second one: no customer with an active subscription should be unreachable.</p>
<pre><code class="language-bash">python3 stripe_customers_missing_email.py
# clear      every customer in the window has an email</code></pre>""",
"code_intro": "Two paginated GETs, no writes &mdash; a restricted key with read access to Customers, Subscriptions and Charges is enough. The classifier takes five counts and is pure, because the ordering between them is the whole point: a disputed charge on an emailless customer has to outrank a percentage, however alarming the percentage looks.",
"py_file": "stripe_customers_missing_email.py",
"py": '''"""Report Stripe customers with no email, so no receipt or dunning notice is sent.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Customers, Subscriptions and Charges. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_customers_missing_email")

API = "https://api.stripe.com/v1"

WIDESPREAD_RATIO = 0.25   # a quarter of customers is a signup path, not a backlog


def verdict(missing, total, with_active_sub, receiptless_charges, disputed):
    """Classify the email gap. Pure, so the ordering can be tested offline.

    missing              customers with a null or empty email
    total                customers examined
    with_active_sub      of those, how many have an active subscription
    receiptless_charges  charges with neither a customer nor a receipt_email
    disputed             charges from emailless customers already disputed

    Returns (state, detail). The order is deliberate: money already lost outranks
    money about to be lost, which outranks a percentage.
    """
    if disputed:
        return ("disputed",
                "%d charge(s) from customers with no email have been disputed. The "
                "cardholder had no receipt to recognise the descriptor by."
                % disputed)
    if with_active_sub:
        return ("unreachable",
                "%d customer(s) with an active subscription have no email. When the "
                "renewal fails, dunning has nowhere to send anything."
                % with_active_sub)
    if not total:
        return ("clear", "no customers in the window")
    ratio = missing / float(total)
    if ratio >= WIDESPREAD_RATIO:
        return ("widespread",
                "%d of %d customers (%.0f%%) have no email. That is the signup path "
                "behaving this way now, not an old backlog."
                % (missing, total, ratio * 100))
    if missing:
        return ("gaps",
                "%d of %d customers have no email and will receive no receipt"
                % (missing, total))
    if receiptless_charges:
        return ("receiptless",
                "every customer has an email, but %d charge(s) had neither a "
                "customer nor a receipt_email: guest checkout sends no receipt"
                % receiptless_charges)
    return ("clear", "every customer in the window has an email")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Yield objects from a paginated list endpoint until `limit` is reached."""
    seen = 0
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-customers", type=int, default=2000,
                    help="stop paginating customers after this many")
    ap.add_argument("--max-charges", type=int, default=2000,
                    help="stop paginating charges after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    total = missing = with_active_sub = 0
    emailless = set()
    sample = []
    for cust in page_all(s, "/customers", args.max_customers, limit=100):
        total += 1
        # Both null and "" occur; a form that posts a blank field produces the
        # second, and a check for None alone walks straight past it.
        if (cust.get("email") or "").strip():
            continue
        missing += 1
        cid = cust.get("id")
        emailless.add(cid)
        if len(sample) < 5:
            sample.append(cid)
        subs = get(s, "/subscriptions", customer=cid, status="active", limit=1)
        if subs.get("data"):
            with_active_sub += 1

    receiptless = disputed = 0
    for ch in page_all(s, "/charges", args.max_charges, limit=100):
        if not ch.get("customer") and not ch.get("receipt_email"):
            receiptless += 1
        if ch.get("disputed") and ch.get("customer") in emailless:
            disputed += 1

    state, detail = verdict(missing, total, with_active_sub, receiptless, disputed)
    line = "%-11s %s" % (state, detail)
    if state == "clear":
        log.info(line)
        return 0

    log.warning(line)
    for cid in sample:
        log.warning("  no email  %s", cid)
    log.warning("  backfill from your own user table:")
    log.warning("  POST %s/customers/{id} -d email=user@example.com "
                "-d name=\\"Jenny Rosen\\"", API)
    if receiptless:
        log.warning("  and for guest payments, set the address on the intent:")
        log.warning("  POST %s/payment_intents -d receipt_email=user@example.com", API)
    log.warning("  then confirm receipts are enabled at "
                "https://dashboard.stripe.com/settings/emails")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-customers-missing-email.mjs",
"js": '''/**
 * Report Stripe customers with no email, so no receipt or dunning notice is sent.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to Customers, Subscriptions and Charges. The repair is printed only.
 */
const API = 'https://api.stripe.com/v1';

export const WIDESPREAD_RATIO = 0.25; // a quarter is a signup path, not a backlog

/**
 * Classify the email gap. Pure, so the ordering can be tested offline.
 * The order is deliberate: money already lost outranks money about to be lost,
 * which outranks a percentage. Returns [state, detail].
 */
export function verdict(missing, total, withActiveSub, receiptlessCharges, disputed) {
  if (disputed) {
    return ['disputed',
      `${disputed} charge(s) from customers with no email have been disputed. ` +
      'The cardholder had no receipt to recognise the descriptor by.'];
  }
  if (withActiveSub) {
    return ['unreachable',
      `${withActiveSub} customer(s) with an active subscription have no email. ` +
      'When the renewal fails, dunning has nowhere to send anything.'];
  }
  if (!total) return ['clear', 'no customers in the window'];
  const ratio = missing / total;
  if (ratio >= WIDESPREAD_RATIO) {
    return ['widespread',
      `${missing} of ${total} customers (${(ratio * 100).toFixed(0)}%) have no ` +
      'email. That is the signup path behaving this way now, not an old backlog.'];
  }
  if (missing) {
    return ['gaps',
      `${missing} of ${total} customers have no email and will receive no receipt`];
  }
  if (receiptlessCharges) {
    return ['receiptless',
      `every customer has an email, but ${receiptlessCharges} charge(s) had neither ` +
      'a customer nor a receipt_email: guest checkout sends no receipt'];
  }
  return ['clear', 'every customer in the window has an email'];
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

export async function pageAll(key, path, limit, params = {}) {
  const out = [];
  const q = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, q);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) return out;
    q.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  let total = 0;
  let missing = 0;
  let withActiveSub = 0;
  const emailless = new Set();
  const sample = [];
  for (const cust of await pageAll(key, '/customers', 2000)) {
    total += 1;
    // Both null and '' occur; a form that posts a blank field produces the
    // second, and a check for null alone walks straight past it.
    if ((cust.email ?? '').trim()) continue;
    missing += 1;
    emailless.add(cust.id);
    if (sample.length < 5) sample.push(cust.id);
    const subs = await get(key, '/subscriptions', { customer: cust.id, status: 'active', limit: 1 });
    if ((subs.data ?? []).length) withActiveSub += 1;
  }

  let receiptless = 0;
  let disputed = 0;
  for (const ch of await pageAll(key, '/charges', 2000)) {
    if (!ch.customer && !ch.receipt_email) receiptless += 1;
    if (ch.disputed && emailless.has(ch.customer)) disputed += 1;
  }

  const [state, detail] = verdict(missing, total, withActiveSub, receiptless, disputed);
  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'clear') { console.log(line); return; }

  console.warn(line);
  for (const cid of sample) console.warn(`  no email  ${cid}`);
  console.warn('  backfill from your own user table:');
  console.warn(`  POST ${API}/customers/{id} -d email=user@example.com -d name="Jenny Rosen"`);
  if (receiptless) {
    console.warn('  and for guest payments, set the address on the intent:');
    console.warn(`  POST ${API}/payment_intents -d receipt_email=user@example.com`);
  }
  console.warn('  then confirm receipts are enabled at https://dashboard.stripe.com/settings/emails');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the ordering, because that is the only interesting decision in the function. A single disputed charge on an emailless customer has to beat a scary-looking percentage, an unreachable subscriber has to beat a tidy one, and the guest-checkout finding must never hide behind a customer list that happens to be clean.",
"test_py_file": "test_stripe_customers_missing_email.py",
"test_py": '''from stripe_customers_missing_email import verdict


def test_a_full_customer_list_is_clear():
    assert verdict(0, 500, 0, 0, 0)[0] == "clear"


def test_a_dispute_outranks_everything_else():
    # One dispute, one missing email out of thousands. Still the top finding,
    # because that money is already gone.
    state, detail = verdict(1, 5000, 0, 0, 1)
    assert state == "disputed"
    assert "receipt" in detail


def test_an_active_subscriber_outranks_a_percentage():
    state, detail = verdict(400, 500, 1, 0, 0)
    assert state == "unreachable"
    assert "dunning" in detail


def test_a_quarter_missing_is_the_signup_path():
    state, detail = verdict(25, 100, 0, 0, 0)
    assert state == "widespread"
    assert "25%" in detail


def test_below_the_ratio_is_a_gap_not_a_path():
    assert verdict(24, 100, 0, 0, 0)[0] == "gaps"


def test_guest_receipts_are_reported_on_a_clean_customer_list():
    state, detail = verdict(0, 500, 0, 12, 0)
    assert state == "receiptless"
    assert "receipt_email" in detail
''',
"test_js_file": "stripe-customers-missing-email.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-customers-missing-email.mjs';

test('a full customer list is clear', () => {
  assert.equal(verdict(0, 500, 0, 0, 0)[0], 'clear');
});

test('a dispute outranks everything else', () => {
  const [state, detail] = verdict(1, 5000, 0, 0, 1);
  assert.equal(state, 'disputed');
  assert.match(detail, /receipt/);
});

test('an active subscriber outranks a percentage', () => {
  const [state, detail] = verdict(400, 500, 1, 0, 0);
  assert.equal(state, 'unreachable');
  assert.match(detail, /dunning/);
});

test('a quarter missing is the signup path', () => {
  const [state, detail] = verdict(25, 100, 0, 0, 0);
  assert.equal(state, 'widespread');
  assert.match(detail, /25%/);
});

test('below the ratio is a gap not a path', () => {
  assert.equal(verdict(24, 100, 0, 0, 0)[0], 'gaps');
});

test('guest receipts are reported on a clean customer list', () => {
  const [state, detail] = verdict(0, 500, 0, 12, 0);
  assert.equal(state, 'receiptless');
  assert.match(detail, /receipt_email/);
});
''',
"faq": [
 ("Where does Stripe send a receipt if the customer has no email?",
  "Nowhere. It checks customer.email and the charge's receipt_email, and if both are empty it sends nothing and records nothing. There is no bounce and no error field, which is why this survives so long unnoticed."),
 ("Does a missing email really cause disputes?",
  "It removes the thing that prevents them. The receipt is what lets a cardholder connect an unfamiliar statement descriptor to a purchase weeks later. Without it, the only way to find out what a charge was is to ask the bank, and asking the bank is a dispute."),
 ("Are receipts sent in test mode?",
  "No. Stripe does not send email receipts for test-mode payments, so a flow that looks correct in test can be silently sending nothing in live. Verify against a live payment or the Dashboard's email settings rather than assuming."),
 ("What about one-off payments with no Customer at all?",
  "Set receipt_email on the PaymentIntent. That is the guest-checkout equivalent of customer.email and it is the field integrations most often forget, because they already collected the address for their own order confirmation."),
 ("I set the email but customers still get no receipt.",
  "Check the Dashboard email settings. Receipts for successful payments are a per-account toggle; with it off, a fully populated email field sends nothing. The field and the setting have to both be right."),
],
"related": [
 ("/stripe/duplicate-customers-same-email/", "Duplicate customers share an email and split billing"),
 ("/stripe/dunning-retries-exhausted/", "Dunning ran out of retries and no attempt is scheduled"),
 ("/stripe/disputes-lost-without-response/", "Disputes closed as lost were never actually contested"),
],
"citations": [CITE_CUSTOMER_OBJ, CITE_CUSTOMER_UPDATE, CITE_RECEIPTS, CITE_PI_OBJ],
},

{
"slug": "setup-intents-never-confirmed",
"title": "SetupIntents are created but never confirmed by the client",
"description": "The add-a-card flow looks like it worked and no card ever lands on the customer. A pile of SetupIntents sits at requires_confirmation forever.",
"h1": "SetupIntents are created but never confirmed by the client",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe setup intent requires_confirmation",
             "confirmSetup not working", "stripe setup intent stuck",
             "setup_intent_authentication_failure", "stripe save card fails silently"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Support keeps hearing the same thing: they added a card, the page said it worked, and the next invoice failed anyway. In the API there are four hundred SetupIntents sitting at <code>requires_confirmation</code>, created over three months, none of which ever produced a mandate or a PaymentMethod on a Customer.",
"short_answer": """<p>Page <code>GET /v1/setup_intents?created[lt]={now-24h}</code> and bucket <code>status</code>. Anything still at <code>requires_payment_method</code>, <code>requires_confirmation</code> or <code>requires_action</code> a day after creation is stuck rather than in progress. Above roughly <strong>20%</strong> of the window, that is a broken confirm path, not user abandonment.</p>
<p>Which bucket dominates names the bug. <code>requires_confirmation</code> means <code>stripe.confirmSetup()</code> was never called. <code>requires_action</code> means the 3DS handoff started and the browser never came back, which is usually a missing or wrong <code>return_url</code>. <code>requires_payment_method</code> means the customer never got as far as entering details, or the confirm failed &mdash; read <code>last_setup_error.code</code> to tell those apart.</p>""",
"problem": """<p>A SetupIntent has the same lifecycle as a PaymentIntent, and creating one server-side is only the first step. The card is not saved until the client confirms, the customer completes any authentication the issuer asks for, and the intent reaches <code>succeeded</code>. Until then there is no mandate, and without a mandate every later off-session charge has nothing to authorise against.</p>
<p>What makes it silent is that the failure happens in the browser and the browser is where the success message lives. A frontend that closes the modal on the network response rather than on <code>setupIntent.status</code> tells the customer their card is saved while the intent is still at <code>requires_confirmation</code>. Your server never hears about it either, because the failure produced no event: an intent that is never confirmed generates nothing to subscribe to.</p>""",
"why": """<p><strong>Creating and confirming are separate calls, and only one of them is on your server.</strong> The server-side create returns a client secret and a 200, which is the part your logs and your tests cover. The confirm lives in the browser, where a JavaScript exception, a closed tab or an early redirect ends the flow with no trace on your side.</p>
<p><strong>The client secret makes success look like it already happened.</strong> Once the create call returns, there is a real object with a real id, and it is tempting to record "card added" against it. That object will sit unconfirmed forever, and it will still be readable through the API a year later, looking exactly like the ones that worked.</p>
<p><strong>A missing return_url only breaks the authenticated subset.</strong> With 3DS, the customer leaves your page and needs somewhere to come back to. If that landing page is missing or does not finish the flow, the intents that required authentication freeze at <code>requires_action</code> while the ones that did not sail through. The result is a bug that reproduces for some cards, some banks and some countries, which is the hardest kind to be believed about.</p>
<p><strong>Some abandonment is real and you have to allow for it.</strong> People do open a card form and walk away. That is why the useful signal is a ratio over a window rather than a raw count, and why the buckets matter: ordinary abandonment lands overwhelmingly in <code>requires_payment_method</code>, while a pile at <code>requires_confirmation</code> is your code.</p>""",
"steps": [
 {"h": "Give them a day before judging",
  "body": """<p><code>GET /v1/setup_intents?limit=100&amp;created[lt]={now-24h}</code>. An intent created ten minutes ago at <code>requires_confirmation</code> is a customer still typing. A day later it is never going to resolve on its own.</p>"""},
 {"h": "Bucket by status and take the ratio",
  "body": """<p>Count the three unresolved statuses against everything created in the window. Under about a fifth is ordinary drop-off from a card form. Above it, something in the confirm path is broken and the ratio is the fastest way to tell those apart without reading any frontend code.</p>"""},
 {"h": "Let the dominant bucket point at the bug",
  "body": """<p><code>requires_confirmation</code> means the confirm call never happened. <code>requires_action</code> means it happened and the customer never came back, so look at <code>next_action.type</code> and at your <code>return_url</code>. <code>requires_payment_method</code> means no usable card was ever attached, which is either abandonment or a confirm that failed.</p>"""},
 {"h": "Read the errors on the failures",
  "body": """<p><code>last_setup_error.code</code> separates the causes: <code>setup_intent_authentication_failure</code> is the customer failing 3DS, <code>setup_intent_setup_attempt_expired</code> is an attempt that timed out. An empty <code>last_setup_error</code> across the whole stuck population means nothing was ever attempted, which points back at the client.</p>"""},
 {"h": "Confirm properly and drive persistence from the webhook",
  "body": """<p>On the client, await <code>stripe.confirmSetup()</code> and treat only <code>setupIntent.status === 'succeeded'</code> as success. Implement the <code>return_url</code> landing page. Then save the PaymentMethod when the <code>setup_intent.succeeded</code> event arrives rather than when the browser says so, and cancel dead intents with <code>cancellation_reason=abandoned</code> so the backlog stops growing.</p>"""},
],
"verify": """<p>Re-run against a fresh window after the fix. The ratio is the number to watch: it should drop back under the threshold and stay there, with whatever remains landing in <code>requires_payment_method</code>.</p>
<pre><code class="language-bash">python3 stripe_setup_intents_stuck.py
# clear       all 312 SetupIntent(s) in the window resolved</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/setup_intents</code> and no writes &mdash; a restricted key with read access to SetupIntents is enough. The classifier takes the total and the three stuck counts and is pure, including the rule for what happens when two buckets tie, because a tie-break decided by dictionary ordering is a diagnosis that changes between runs.",
"py_file": "stripe_setup_intents_stuck.py",
"py": '''"""Report Stripe SetupIntents that were created and never confirmed.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to SetupIntents. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_setup_intents_stuck")

API = "https://api.stripe.com/v1"

STUCK_STATUSES = ("requires_payment_method", "requires_confirmation", "requires_action")
BROKEN_RATIO = 0.20   # above this, it is the confirm path rather than abandonment
MIN_AGE_HOURS = 24    # younger than this is a customer still typing


def verdict(total, requires_payment_method, requires_confirmation, requires_action):
    """Classify a window of SetupIntents. Pure, so it can be tested offline.

    Ties are broken in a fixed order rather than by whichever bucket a dict
    happened to yield first: requires_action wins, then requires_confirmation.
    Both are specific code defects, while requires_payment_method is the bucket
    ordinary abandonment also lands in, so it is the least informative of the
    three and should never win a tie.

    Returns (state, detail).
    """
    stuck = requires_payment_method + requires_confirmation + requires_action
    if not total:
        return ("clear", "no SetupIntents created in the window")
    if not stuck:
        return ("clear", "all %d SetupIntent(s) in the window resolved" % total)
    ratio = stuck / float(total)
    pct = ratio * 100
    if ratio < BROKEN_RATIO:
        return ("abandonment",
                "%d of %d SetupIntents (%.0f%%) are stuck, under the %.0f%% that "
                "separates a broken confirm path from ordinary drop-off"
                % (stuck, total, pct, BROKEN_RATIO * 100))
    if requires_action >= requires_confirmation and requires_action >= requires_payment_method:
        return ("return-url",
                "%d of %d (%.0f%%) stuck, mostly at requires_action: the 3DS handoff "
                "starts and never comes back. Check next_action.type and the "
                "return_url landing page." % (stuck, total, pct))
    if requires_confirmation >= requires_payment_method:
        return ("unconfirmed",
                "%d of %d (%.0f%%) stuck, mostly at requires_confirmation: "
                "confirmSetup() is never being called for these."
                % (stuck, total, pct))
    return ("no-payment-method",
            "%d of %d (%.0f%%) stuck at requires_payment_method, above the "
            "abandonment threshold: read last_setup_error.code before blaming "
            "the customers." % (stuck, total, pct))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Yield objects from a paginated list endpoint until `limit` is reached."""
    seen = 0
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-intents", type=int, default=2000,
                    help="stop paginating after this many SetupIntents")
    ap.add_argument("--min-age-hours", type=float, default=MIN_AGE_HOURS,
                    help="ignore SetupIntents younger than this")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    cutoff = int(time.time() - args.min_age_hours * 3600)
    buckets = dict.fromkeys(STUCK_STATUSES, 0)
    errors = {}
    next_actions = {}
    total = 0
    params = {"limit": 100, "created[lt]": cutoff}
    for si in page_all(s, "/setup_intents", args.max_intents, **params):
        total += 1
        status = si.get("status")
        if status not in buckets:
            continue
        buckets[status] += 1
        err = (si.get("last_setup_error") or {}).get("code")
        if err:
            errors[err] = errors.get(err, 0) + 1
        action = (si.get("next_action") or {}).get("type")
        if action:
            next_actions[action] = next_actions.get(action, 0) + 1

    state, detail = verdict(total, buckets["requires_payment_method"],
                            buckets["requires_confirmation"],
                            buckets["requires_action"])
    line = "%-18s %s" % (state, detail)
    if state == "clear":
        log.info(line)
        return 0

    log.warning(line)
    for status in STUCK_STATUSES:
        log.warning("  %-24s %d", status, buckets[status])
    for code, count in sorted(errors.items(), key=lambda kv: -kv[1]):
        log.warning("  last_setup_error %-20s %d", code, count)
    for action, count in sorted(next_actions.items(), key=lambda kv: -kv[1]):
        log.warning("  next_action %-25s %d", action, count)
    log.warning("  confirm on the client and treat only 'succeeded' as success:")
    log.warning("  await stripe.confirmSetup({elements, confirmParams: {return_url}})")
    log.warning("  persist from the setup_intent.succeeded webhook, not the browser")
    log.warning("  clear the backlog: POST %s/setup_intents/{id}/cancel "
                "-d cancellation_reason=abandoned", API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-setup-intents-stuck.mjs",
"js": '''/**
 * Report Stripe SetupIntents that were created and never confirmed.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to SetupIntents. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const STUCK_STATUSES = [
  'requires_payment_method', 'requires_confirmation', 'requires_action',
];
const BROKEN_RATIO = 0.20; // above this it is the confirm path, not abandonment
const MIN_AGE_HOURS = 24;  // younger than this is a customer still typing

/**
 * Classify a window of SetupIntents. Pure, so it can be tested offline.
 *
 * Ties are broken in a fixed order rather than by whichever bucket an object
 * happened to yield first: requiresAction wins, then requiresConfirmation. Both
 * are specific code defects, while requiresPaymentMethod is the bucket ordinary
 * abandonment also lands in, so it should never win a tie.
 */
export function verdict(total, requiresPaymentMethod, requiresConfirmation, requiresAction) {
  const stuck = requiresPaymentMethod + requiresConfirmation + requiresAction;
  if (!total) return ['clear', 'no SetupIntents created in the window'];
  if (!stuck) return ['clear', `all ${total} SetupIntent(s) in the window resolved`];
  const ratio = stuck / total;
  const pct = (ratio * 100).toFixed(0);
  if (ratio < BROKEN_RATIO) {
    return ['abandonment',
      `${stuck} of ${total} SetupIntents (${pct}%) are stuck, under the ` +
      `${(BROKEN_RATIO * 100).toFixed(0)}% that separates a broken confirm path ` +
      'from ordinary drop-off'];
  }
  if (requiresAction >= requiresConfirmation && requiresAction >= requiresPaymentMethod) {
    return ['return-url',
      `${stuck} of ${total} (${pct}%) stuck, mostly at requires_action: the 3DS ` +
      'handoff starts and never comes back. Check next_action.type and the ' +
      'return_url landing page.'];
  }
  if (requiresConfirmation >= requiresPaymentMethod) {
    return ['unconfirmed',
      `${stuck} of ${total} (${pct}%) stuck, mostly at requires_confirmation: ` +
      'confirmSetup() is never being called for these.'];
  }
  return ['no-payment-method',
    `${stuck} of ${total} (${pct}%) stuck at requires_payment_method, above the ` +
    'abandonment threshold: read last_setup_error.code before blaming the customers.'];
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

export async function pageAll(key, path, limit, params = {}) {
  const out = [];
  const q = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, q);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) return out;
    q.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const cutoff = Math.floor(Date.now() / 1000 - MIN_AGE_HOURS * 3600);
  const buckets = Object.fromEntries(STUCK_STATUSES.map((s) => [s, 0]));
  const errors = new Map();
  const nextActions = new Map();
  let total = 0;

  for (const si of await pageAll(key, '/setup_intents', 2000, { 'created[lt]': cutoff })) {
    total += 1;
    if (!(si.status in buckets)) continue;
    buckets[si.status] += 1;
    const err = si.last_setup_error?.code;
    if (err) errors.set(err, (errors.get(err) ?? 0) + 1);
    const action = si.next_action?.type;
    if (action) nextActions.set(action, (nextActions.get(action) ?? 0) + 1);
  }

  const [state, detail] = verdict(total, buckets.requires_payment_method,
    buckets.requires_confirmation, buckets.requires_action);
  const line = `${state.padEnd(18)} ${detail}`;
  if (state === 'clear') { console.log(line); return; }

  console.warn(line);
  for (const status of STUCK_STATUSES) {
    console.warn(`  ${status.padEnd(24)} ${buckets[status]}`);
  }
  for (const [code, count] of [...errors].sort((a, b) => b[1] - a[1])) {
    console.warn(`  last_setup_error ${code.padEnd(20)} ${count}`);
  }
  for (const [action, count] of [...nextActions].sort((a, b) => b[1] - a[1])) {
    console.warn(`  next_action ${action.padEnd(25)} ${count}`);
  }
  console.warn("  confirm on the client and treat only 'succeeded' as success:");
  console.warn('  await stripe.confirmSetup({elements, confirmParams: {return_url}})');
  console.warn('  persist from the setup_intent.succeeded webhook, not the browser');
  console.warn(`  clear the backlog: POST ${API}/setup_intents/{id}/cancel -d cancellation_reason=abandoned`);
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The threshold and the tie-break are what the tests are for. Nineteen percent stuck is a card form people walk away from; twenty is a bug, and the function has to agree with itself about which. The tie-break matters just as much: when two buckets are level, the diagnosis has to be the same on every run rather than depending on which status the iteration reached first.",
"test_py_file": "test_stripe_setup_intents_stuck.py",
"test_py": '''from stripe_setup_intents_stuck import verdict


def test_an_empty_window_is_clear():
    assert verdict(0, 0, 0, 0)[0] == "clear"


def test_everything_resolved_is_clear():
    state, detail = verdict(312, 0, 0, 0)
    assert state == "clear"
    assert "312" in detail


def test_nineteen_percent_is_ordinary_drop_off():
    assert verdict(100, 19, 0, 0)[0] == "abandonment"


def test_twenty_percent_is_a_broken_path():
    # The boundary is inclusive. One percentage point either side is the
    # difference between a report nobody acts on and one that names the bug.
    state, detail = verdict(100, 20, 0, 0)
    assert state == "no-payment-method"
    assert "last_setup_error" in detail


def test_a_pile_at_requires_confirmation_names_the_client():
    state, detail = verdict(100, 5, 40, 2)
    assert state == "unconfirmed"
    assert "confirmSetup" in detail


def test_requires_action_points_at_the_return_url():
    state, detail = verdict(100, 5, 10, 40)
    assert state == "return-url"
    assert "return_url" in detail


def test_a_tie_is_broken_deterministically():
    # Level buckets must not depend on iteration order: requires_action first,
    # then requires_confirmation.
    assert verdict(100, 20, 20, 20)[0] == "return-url"
    assert verdict(100, 20, 20, 0)[0] == "unconfirmed"
''',
"test_js_file": "stripe-setup-intents-stuck.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-setup-intents-stuck.mjs';

test('an empty window is clear', () => {
  assert.equal(verdict(0, 0, 0, 0)[0], 'clear');
});

test('everything resolved is clear', () => {
  const [state, detail] = verdict(312, 0, 0, 0);
  assert.equal(state, 'clear');
  assert.match(detail, /312/);
});

test('nineteen percent is ordinary drop off', () => {
  assert.equal(verdict(100, 19, 0, 0)[0], 'abandonment');
});

test('twenty percent is a broken path', () => {
  const [state, detail] = verdict(100, 20, 0, 0);
  assert.equal(state, 'no-payment-method');
  assert.match(detail, /last_setup_error/);
});

test('a pile at requires_confirmation names the client', () => {
  const [state, detail] = verdict(100, 5, 40, 2);
  assert.equal(state, 'unconfirmed');
  assert.match(detail, /confirmSetup/);
});

test('requires_action points at the return_url', () => {
  const [state, detail] = verdict(100, 5, 10, 40);
  assert.equal(state, 'return-url');
  assert.match(detail, /return_url/);
});

test('a tie is broken deterministically', () => {
  assert.equal(verdict(100, 20, 20, 20)[0], 'return-url');
  assert.equal(verdict(100, 20, 20, 0)[0], 'unconfirmed');
});
''',
"faq": [
 ("What is the difference between requires_confirmation and requires_action?",
  "requires_confirmation means the client never called confirmSetup at all, so nothing was attempted. requires_action means it did, and the issuer asked for authentication that the customer never completed, usually because the 3DS redirect had nowhere to come back to."),
 ("Is a stuck SetupIntent the same as a failed one?",
  "No, and that is why it is easy to miss. A failed setup has a last_setup_error and often an event you can subscribe to. An unconfirmed one has neither: it simply sits there, indistinguishable from a customer who is still typing, until you age it."),
 ("Why 24 hours before counting one as stuck?",
  "Because a SetupIntent created minutes ago is a card form that is open right now. A day is long enough that nothing legitimate is still in flight and short enough that a daily run catches a regression the day after it ships."),
 ("Should I cancel the backlog?",
  "Yes, once you have counted it. POST /v1/setup_intents/{id}/cancel with cancellation_reason=abandoned clears intents that will never resolve, so the ratio on the next run measures current behaviour instead of history. Count first, cancel second."),
 ("Why persist from the webhook instead of the browser?",
  "Because the browser is where this fails. A tab closed during the redirect, a JavaScript error after the confirm, a flaky network on the way back: all of them end with a card that really was set up and an application that never recorded it. setup_intent.succeeded arrives regardless."),
],
"related": [
 ("/stripe/unattached-payment-methods-orphaned/", "PaymentMethods are created but never attached to a customer"),
 ("/stripe/abandoned-requires-action-intents/", "3DS handoff breaks and requires_action intents pile up"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
],
"citations": [CITE_SI_OBJ, CITE_SI_LIST, CITE_LIFECYCLE, CITE_SAVE_REUSE],
},

]
