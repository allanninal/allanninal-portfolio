#!/usr/bin/env python3
"""/stripe/ field notes, batch Q — reporting and reconciliation: reserves held
against negative connected accounts, currency buckets with no way out, missing
application fees, and payouts that cannot be tied back to what they contain.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

These four are all failures of arithmetic rather than of delivery. Nothing errors,
no request 500s, no webhook goes missing: the money simply does not add up, and
the gap is only visible to somebody who reads the balance object one currency at
a time and the payout object one field at a time.
"""

CITE_ACCOUNT_BALANCES = ("Account balances — Stripe Docs",
                         "https://docs.stripe.com/connect/account-balances")
CITE_BALANCE_OBJ = ("The balance object — Stripe API reference",
                    "https://docs.stripe.com/api/balance/balance_object")
CITE_BALANCE_TXN_OBJ = ("The balance transaction object — Stripe API reference",
                        "https://docs.stripe.com/api/balance_transactions/object")
CITE_DEBIT_NEGATIVE = ("Debit negative balances — Stripe Docs",
                       "https://docs.stripe.com/connect/debit-negative-balances")
CITE_PAYOUTS = ("Payouts — Stripe Docs", "https://docs.stripe.com/payouts")
CITE_PAYOUT_OBJ = ("The payout object — Stripe API reference",
                   "https://docs.stripe.com/api/payouts/object")
CITE_CURRENCIES = ("Supported currencies — Stripe Docs",
                   "https://docs.stripe.com/currencies")
CITE_CONNECT_PAYOUTS = ("Payouts to connected accounts — Stripe Docs",
                        "https://docs.stripe.com/connect/payouts-connected-accounts")
CITE_APP_FEE_OBJ = ("The application fee object — Stripe API reference",
                    "https://docs.stripe.com/api/application_fees/object")
CITE_CONNECT_CHARGES = ("Charge types — Stripe Docs",
                        "https://docs.stripe.com/connect/charges")
CITE_DESTINATION_CHARGES = ("Destination charges — Stripe Docs",
                            "https://docs.stripe.com/connect/destination-charges")
CITE_CHARGE_OBJ = ("The charge object — Stripe API reference",
                   "https://docs.stripe.com/api/charges/object")
CITE_PAYOUT_RECON = ("Payout reconciliation report — Stripe Docs",
                     "https://docs.stripe.com/reports/report-types/payout-reconciliation")
CITE_REPORTING_API = ("Reporting API — Stripe Docs",
                      "https://docs.stripe.com/reports/api")
CITE_TRANSFER_OBJ = ("The transfer object — Stripe API reference",
                     "https://docs.stripe.com/api/transfers/object")

GUIDES = [

{
"slug": "connect-reserved-balance-growing",
"title": "connect_reserved grows as connected accounts go negative",
"description": "The platform's available balance is short of the books and the gap widens monthly. Stripe is reserving against connected accounts that went negative.",
"h1": "connect_reserved grows as connected accounts go negative",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe connect_reserved", "stripe connect reserved balance",
             "connect_collection_transfer", "stripe reserve_transaction",
             "stripe negative connected account balance"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Payouts to the platform's own bank are smaller than the ledger says they should be, and the shortfall grows a little every month. No payout failed, no charge was refunded twice, and the Dashboard's headline balance looks plausible. The money is not missing &mdash; it is reserved, against connected accounts whose own balances have gone below zero.",
"short_answer": """<p>Read <code>GET /v1/balance</code> on the platform and look at <code>connect_reserved</code>. It is an array, one entry per currency, and any entry with <code>amount &gt; 0</code> is money Stripe is holding out of your <code>available</code> balance to cover connected accounts you are liable for.</p>
<p>Then read the direction of travel from <code>GET /v1/balance_transactions?type=reserve_transaction</code> over the last 90 days, and the damage already taken from <code>type=connect_collection_transfer</code>. A <code>connect_collection_transfer</code> is not a hold: it is Stripe zeroing an account that stayed negative for 180 days by keeping your reserve, which makes it a permanent platform loss.</p>""",
"problem": """<p>The reserve does not appear as a transaction anyone reviews. It is a field on the balance object, and almost every reconciler ever written reads <code>available[0].amount</code> and stops there. So the platform's own bank deposits quietly shrink while every individual charge, refund and fee reconciles perfectly, which is exactly the pattern that makes finance suspect the ledger rather than Stripe.</p>
<p>What makes it expensive is the clock attached to it. A reserve is recoverable: pay the negative account back and the hold is released. After 180 days it stops being recoverable, because Stripe settles the account by moving your reserve across for good. Nobody gets an invoice for that. It appears as a balance transaction of a type most teams have never listed.</p>""",
"why": """<p><strong>The platform is the loss-bearing party by default on most Connect configurations.</strong> When <code>controller.losses.payments</code> is <code>"application"</code>, a refund or a chargeback on a connected account that has already been paid out lands on you. Stripe covers it by reserving from your balance, because it has nowhere else to take it from.</p>
<p><strong>Negative balances are normal and self-clearing until they are not.</strong> An account that keeps trading earns its way back to zero out of its next charges, and the reserve releases on its own. The accounts that hurt are the ones that stopped trading: a seller who churned, a merchant who was suspended, a test account nobody closed. They have no incoming volume, so the negative balance is frozen and the reserve against it never releases.</p>
<p><strong>The setting that would fix it is off by default and account-scoped.</strong> With <code>debit_negative_balances</code> enabled, Stripe pulls the shortfall from the connected account's own bank rather than holding your money against it. It is set per account, so it is easy to have it on for the accounts onboarded since somebody thought about this and off for everything older.</p>
<p><strong>180 days is not a warning, it is a settlement.</strong> Stripe zeroes an account that has stayed negative that long with a <code>connect_collection_transfer</code>, funded from the reserve it was already holding. From your side the reserve simply disappears and the <code>available</code> balance does not go back up. There is no reversal for it and no invoice announcing it.</p>""",
"steps": [
 {"h": "Read connect_reserved on the platform balance, per currency",
  "body": """<p><code>GET /v1/balance</code> returns <code>available</code>, <code>pending</code> and <code>connect_reserved</code> as arrays. A platform trading in two currencies has two entries in each, and a check that reads index zero can miss the whole problem because the reserve happens to sit in the other one.</p>"""},
 {"h": "Get the trend from reserve_transaction, not from one reading",
  "body": """<p>A reserve balance is a level, and a level tells you nothing about direction. <code>GET /v1/balance_transactions?type=reserve_transaction&amp;created[gte]=</code> over 90 days says whether the hold is being topped up, released, or has been frozen at the same figure since a seller left.</p>"""},
 {"h": "List connect_collection_transfer separately, because that is the loss",
  "body": """<p>These are the 180-day settlements. Anything in this list is money you have already lost rather than money being held, and the total is the honest number to give finance. It is also the argument for fixing the setting: every one of them started as a recoverable reserve.</p>"""},
 {"h": "Find the accounts responsible",
  "body": """<p><code>GET /v1/balance</code> with a <code>Stripe-Account</code> header returns that account's own balance, and <code>available[].amount &lt; 0</code> names the culprit. Confirm you are actually liable with <code>GET /v1/accounts/{id}</code> and <code>controller.losses.payments</code>; where that reads <code>"stripe"</code> the negative balance is not funded from your reserve.</p>"""},
 {"h": "Decide per account: pay it back, or make it pay itself back",
  "body": """<p>A transfer to the account zeroes the balance and releases the reserve immediately, which is the right move for a live seller who will earn it back. For accounts that will never trade again, enabling <code>debit_negative_balances</code> moves the recovery to their bank instead of your balance. Doing neither is choosing the 180-day outcome.</p>"""},
],
"verify": """<p>Re-run the script. <code>connect_reserved</code> should be zero in every currency, and the 90-day <code>connect_collection_transfer</code> total should stay at zero from here on.</p>
<pre><code class="language-bash">python3 stripe_connect_reserve.py
# usd  clear     nothing reserved
# 1 currency bucket(s): 0 growing, 0 held, 0 written off</code></pre>""",
"code_intro": "Two GETs for the summary and one paginated list per balance transaction type, all read-only &mdash; a restricted key with read access to Balance and Balance transactions is enough. The per-account pass is behind a flag because it costs one request per connected account. The classifier is pure and takes three numbers per currency: what is held now, what moved into reserve recently, and what has already been collected, because those three answers have three different repairs.",
"py_file": "stripe_connect_reserve.py",
"py": '''"""Report platform funds held in connect_reserved against negative accounts.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Balance, Balance transactions and Connected accounts. The repair is
printed, never performed, because this script holds a credential to a live
payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_connect_reserve")

API = "https://api.stripe.com/v1"

DAY = 86400


def classify(entry, reserved, collected):
    """Sort one currency bucket of connect_reserved. Pure, so the states can be
    tested without a network.

    `entry` is one element of balance.connect_reserved. `reserved` is the total
    reserve_transaction activity seen in that currency over the window and
    `collected` the total connect_collection_transfer activity, both passed as
    magnitudes in minor units: the sign of a balance transaction depends on the
    direction of the movement, and only the size matters here.

    Returns (state, detail).
    """
    amount = entry.get("amount")
    if not isinstance(amount, int):
        return ("unknown", "connect_reserved entry has no numeric amount: %r" % (amount,))

    if collected:
        return ("written-off",
                "%d already moved out as connect_collection_transfer: accounts that "
                "stayed negative for 180 days were settled from your reserve, and "
                "that money is not coming back" % collected)

    if amount > 0 and reserved:
        return ("growing",
                "%d held now and %d of reserve_transaction activity in the window: "
                "accounts are still going negative faster than they earn back"
                % (amount, reserved))

    if amount > 0:
        return ("held",
                "%d held with no reserve_transaction activity in the window: the "
                "negative account behind it has stopped trading, so nothing will "
                "release this before the 180 day settlement" % amount)

    if reserved:
        return ("settled",
                "nothing held now, %d of reserve_transaction activity in the window: "
                "reserves were taken and released as accounts earned back" % reserved)

    return ("clear", "nothing reserved")


def get(session, path, headers=None, **params):
    r = session.get(API + path, params=params, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def totals_by_currency(session, btype, since, cap):
    """Sum balance transactions of one type per currency, as magnitudes."""
    totals = {}
    seen = 0
    params = {"type": btype, "limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/balance_transactions", **params)
        data = page.get("data", [])
        for bt in data:
            cur = bt.get("currency", "?")
            totals[cur] = totals.get(cur, 0) + abs(bt.get("amount") or 0)
            seen += 1
        if not data or not page.get("has_more") or seen >= cap:
            return totals
        params["starting_after"] = data[-1]["id"]


def negative_accounts(session, cap):
    """Yield (account_id, currency, amount, liable) for accounts below zero.

    One extra GET per connected account, which is why this is behind a flag.
    """
    params = {"limit": 100}
    seen = 0
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            seen += 1
            aid = acct.get("id", "")
            controller = acct.get("controller") or {}
            losses = (controller.get("losses") or {}).get("payments")
            bal = get(session, "/balance", headers={"Stripe-Account": aid})
            for entry in bal.get("available", []):
                if (entry.get("amount") or 0) < 0:
                    yield (aid, entry.get("currency", "?"), entry["amount"],
                           losses == "application")
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="window for reserve and collection activity")
    ap.add_argument("--accounts", action="store_true",
                    help="also find the negative connected accounts (one GET each)")
    ap.add_argument("--max-accounts", type=int, default=1000,
                    help="stop the per-account pass after this many accounts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * DAY
    balance = get(s, "/balance")
    reserved_now = balance.get("connect_reserved") or []
    if not reserved_now:
        log.info("no connect_reserved on this balance: either not a platform, or "
                 "no account has ever gone negative")

    reserved = totals_by_currency(s, "reserve_transaction", since, 5000)
    collected = totals_by_currency(s, "connect_collection_transfer", since, 5000)

    # A currency can have activity in the window and nothing held now, so union
    # the buckets rather than iterating connect_reserved alone.
    currencies = ({e.get("currency", "?") for e in reserved_now}
                  | set(reserved) | set(collected))

    counts = {}
    for cur in sorted(currencies):
        entry = next((e for e in reserved_now if e.get("currency") == cur),
                     {"currency": cur, "amount": 0})
        state, detail = classify(entry, reserved.get(cur, 0), collected.get(cur, 0))
        counts[state] = counts.get(state, 0) + 1
        line = "%-4s %-11s %s" % (cur, state, detail)
        (log.info if state in ("clear", "settled") else log.warning)(line)

    log.info("%d currency bucket(s): %d growing, %d held, %d written off",
             len(currencies), counts.get("growing", 0), counts.get("held", 0),
             counts.get("written-off", 0))

    if args.accounts:
        found = 0
        for aid, cur, amount, liable in negative_accounts(s, args.max_accounts):
            found += 1
            log.warning("%s  %s %d  liable=%s", aid, cur, amount, liable)
        if not found:
            log.info("no connected account is currently below zero")

    if counts.get("growing") or counts.get("held") or counts.get("written-off"):
        log.warning("  repair, per negative account, in order of preference:")
        log.warning("  1. transfer the shortfall to the account to release the "
                    "reserve now: %s/transfers with destination=acct_x", API)
        log.warning("  2. make future shortfalls come out of the account's own "
                    "bank: %s/balance_settings with Stripe-Account, "
                    "payments[debit_negative_balances]=true", API)
        log.warning("  3. for accounts that will never trade again, reject them "
                    "so nothing more accrues: %s/accounts/{id}/reject", API)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-connect-reserve.mjs",
"js": '''/**
 * Report platform funds held in connect_reserved against negative accounts.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Balance, Balance transactions and Connected accounts. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;

/**
 * Sort one currency bucket of connect_reserved. Pure, so the states can be
 * tested without a network. `reserved` and `collected` are magnitudes in minor
 * units, because the sign of a balance transaction depends on the direction of
 * the movement and only the size matters here. Returns [state, detail].
 */
export function classify(entry, reserved, collected) {
  const amount = entry.amount;
  if (typeof amount !== 'number' || !Number.isFinite(amount)) {
    return ['unknown',
      `connect_reserved entry has no numeric amount: ${JSON.stringify(amount)}`];
  }

  if (collected) {
    return ['written-off',
      `${collected} already moved out as connect_collection_transfer: accounts ` +
      'that stayed negative for 180 days were settled from your reserve, and ' +
      'that money is not coming back'];
  }

  if (amount > 0 && reserved) {
    return ['growing',
      `${amount} held now and ${reserved} of reserve_transaction activity in the ` +
      'window: accounts are still going negative faster than they earn back'];
  }

  if (amount > 0) {
    return ['held',
      `${amount} held with no reserve_transaction activity in the window: the ` +
      'negative account behind it has stopped trading, so nothing will release ' +
      'this before the 180 day settlement'];
  }

  if (reserved) {
    return ['settled',
      `nothing held now, ${reserved} of reserve_transaction activity in the ` +
      'window: reserves were taken and released as accounts earned back'];
  }

  return ['clear', 'nothing reserved'];
}

async function get(key, path, params = {}, headers = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${key}`, ...headers },
  });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function totalsByCurrency(key, type, since, cap = 5000) {
  const totals = new Map();
  let seen = 0;
  const params = { type, limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/balance_transactions', params);
    const data = page.data ?? [];
    for (const bt of data) {
      const cur = bt.currency ?? '?';
      totals.set(cur, (totals.get(cur) ?? 0) + Math.abs(bt.amount ?? 0));
      seen += 1;
    }
    if (data.length === 0 || !page.has_more || seen >= cap) return totals;
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

  const days = Number(process.env.WINDOW_DAYS ?? 90);
  const since = Math.floor(Date.now() / 1000) - days * DAY;

  const balance = await get(key, '/balance');
  const reservedNow = balance.connect_reserved ?? [];
  if (reservedNow.length === 0) {
    console.log('no connect_reserved on this balance: either not a platform, or ' +
                'no account has ever gone negative');
  }

  const reserved = await totalsByCurrency(key, 'reserve_transaction', since);
  const collected = await totalsByCurrency(key, 'connect_collection_transfer', since);

  const currencies = new Set([
    ...reservedNow.map((e) => e.currency ?? '?'),
    ...reserved.keys(), ...collected.keys(),
  ]);

  const counts = {};
  for (const cur of [...currencies].sort()) {
    const entry = reservedNow.find((e) => e.currency === cur)
      ?? { currency: cur, amount: 0 };
    const [state, detail] = classify(entry, reserved.get(cur) ?? 0,
                                     collected.get(cur) ?? 0);
    counts[state] = (counts[state] ?? 0) + 1;
    const line = `${cur.padEnd(4)} ${state.padEnd(11)} ${detail}`;
    if (state === 'clear' || state === 'settled') console.log(line);
    else console.warn(line);
  }

  console.log(`${currencies.size} currency bucket(s): ${counts.growing ?? 0} ` +
              `growing, ${counts.held ?? 0} held, ` +
              `${counts['written-off'] ?? 0} written off`);

  if (counts.growing || counts.held || counts['written-off']) {
    console.warn('  repair, per negative account, in order of preference:');
    console.warn(`  1. transfer the shortfall to the account to release the ` +
                 `reserve now: ${API}/transfers with destination=acct_x`);
    console.warn(`  2. make future shortfalls come out of the account's own bank: ` +
                 `${API}/balance_settings with Stripe-Account, ` +
                 `payments[debit_negative_balances]=true`);
    console.warn(`  3. for accounts that will never trade again, reject them so ` +
                 `nothing more accrues: ${API}/accounts/{id}/reject`);
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
"test_intro": "The two states worth pinning apart are <em>growing</em> and <em>held</em>. They look identical on the balance object &mdash; both are a positive number sitting in <code>connect_reserved</code> &mdash; and they mean opposite things: one is a business still taking losses, the other is a single dead account counting down to a settlement. The third test covers the case where the countdown already finished.",
"test_py_file": "test_stripe_connect_reserve.py",
"test_py": '''from stripe_connect_reserve import classify


def test_a_collection_transfer_outranks_everything_else():
    # The 180 day settlement already happened. Whatever is held now is a
    # secondary concern next to money that has permanently left.
    state, detail = classify({"currency": "usd", "amount": 4000}, 4000, 25000)
    assert state == "written-off"
    assert "connect_collection_transfer" in detail


def test_reserve_with_recent_activity_is_growing():
    state, detail = classify({"currency": "usd", "amount": 12000}, 9000, 0)
    assert state == "growing"
    assert "12000" in detail


def test_reserve_with_no_activity_is_the_dead_account_case():
    # Same positive amount, no movement behind it: nothing will release this
    # on its own, because the account that caused it has stopped trading.
    state, detail = classify({"currency": "usd", "amount": 12000}, 0, 0)
    assert state == "held"
    assert "180 day" in detail


def test_activity_with_nothing_held_is_normal_operation():
    state, _ = classify({"currency": "eur", "amount": 0}, 30000, 0)
    assert state == "settled"


def test_missing_amount_is_not_silently_clear():
    state, _ = classify({"currency": "usd"}, 0, 0)
    assert state == "unknown"
''',
"test_js_file": "stripe-connect-reserve.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-connect-reserve.mjs';

test('a collection transfer outranks everything else', () => {
  const [state, detail] = classify({ currency: 'usd', amount: 4000 }, 4000, 25000);
  assert.equal(state, 'written-off');
  assert.match(detail, /connect_collection_transfer/);
});

test('reserve with recent activity is growing', () => {
  const [state, detail] = classify({ currency: 'usd', amount: 12000 }, 9000, 0);
  assert.equal(state, 'growing');
  assert.match(detail, /12000/);
});

test('reserve with no activity is the dead account case', () => {
  const [state, detail] = classify({ currency: 'usd', amount: 12000 }, 0, 0);
  assert.equal(state, 'held');
  assert.match(detail, /180 day/);
});

test('activity with nothing held is normal operation', () => {
  assert.equal(classify({ currency: 'eur', amount: 0 }, 30000, 0)[0], 'settled');
});

test('missing amount is not silently clear', () => {
  assert.equal(classify({ currency: 'usd' }, 0, 0)[0], 'unknown');
});
''',
"faq": [
 ("What is connect_reserved actually holding?",
  "Money Stripe has taken out of your available balance to cover connected accounts whose own balance is negative and whose losses you are liable for. It is still your money while it sits there, and it is released as soon as the account behind it returns to zero."),
 ("What happens after 180 days?",
  "Stripe zeroes the negative account with a connect_collection_transfer funded from your reserve. At that point the shortfall stops being a hold and becomes a realised platform loss, with no reversal and no invoice. It shows up only as a balance transaction of that type."),
 ("How do I find which connected account is causing it?",
  "GET /v1/balance with a Stripe-Account header returns that account's own balance; available[].amount below zero names it. Check GET /v1/accounts/{id} and controller.losses.payments to confirm you are the liable party, because a value of stripe there means the negative balance is not funded from your reserve."),
 ("Does debit_negative_balances fix the reserves I already have?",
  "No. It changes what happens next: Stripe recovers future shortfalls from the connected account's own bank instead of holding yours. Existing holds still need the account brought back to zero, which usually means transferring the shortfall to it."),
 ("Can a read-only key do this check?",
  "Yes. Balance, Balance transactions and Connected accounts with read access covers every request here, including the per-account balances read through the Stripe-Account header. It cannot move money if it leaks."),
],
"related": [
 ("/stripe/payout-reconciliation-unavailable/", "Payouts cannot be tied back to their balance transactions"),
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
 ("/stripe/transfers-capability-inactive/", "The transfers capability is inactive so every transfer 400s"),
],
"citations": [CITE_ACCOUNT_BALANCES, CITE_BALANCE_OBJ, CITE_BALANCE_TXN_OBJ,
              CITE_DEBIT_NEGATIVE],
},

{
"slug": "stranded-currency-balance",
"title": "A second-currency balance bucket can never be paid out",
"description": "The Stripe total never matches the bank, and the gap is a fixed amount in a currency you barely trade in. No payout will ever drain it.",
"h1": "a second-currency balance bucket can never be paid out",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe balance multiple currencies", "stripe balance not paid out",
             "default_for_currency", "stripe available balance stuck",
             "stripe payout currency mismatch"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Stripe balance and the bank statements have been out by the same figure for months. It is not a rounding error and it is not a timing difference: it is a few hundred euros, on an account that pays out in dollars, sitting in a bucket that no payout has ever touched or ever will.",
"short_answer": """<p><code>GET /v1/balance</code> returns <code>available</code> and <code>pending</code> as <em>arrays</em>, one entry per currency. Flag any account where either array has more than one entry, then check each currency for an exit: <code>GET /v1/accounts/{id}/external_accounts</code> must have a destination whose <code>currency</code> matches, and <code>GET /v1/payouts</code> should show that currency actually being paid out.</p>
<p>Automatic payouts only clear a currency that has a matching external account marked <code>default_for_currency</code>. Without one, the bucket accumulates and never drains, and a reconciler reading <code>available[0].amount</code> never sees it.</p>""",
"problem": """<p>Nothing about this looks like a fault. The Dashboard shows the balance, the payouts run on schedule, and the payments in the stranded currency succeeded exactly as intended. The only symptom is a reconciliation difference that never closes, which is the kind of thing that gets a note in a spreadsheet rather than a ticket.</p>
<p>It is usually created by a decision nobody remembers making. A payment method configuration was widened, or a Checkout page was localised, or one enterprise customer was invoiced in their own currency as a favour. A handful of charges settle in EUR on a USD-only account, and from that moment there is a permanent second bucket with no way out of it.</p>""",
"why": """<p><strong>Payouts are per currency, and so are external accounts.</strong> Stripe will not convert a EUR balance to send it to a USD bank. The payout has to go to a destination that holds that currency, and if no external account has <code>currency: "eur"</code> there is nothing for the payout to target.</p>
<p><strong><code>default_for_currency</code> is the field that actually decides it.</strong> Adding a EUR bank account is not enough on its own: automatic payouts follow the destination flagged as the default for that currency. An external account added and never flagged leaves the balance exactly where it was, which is why this problem sometimes survives a first attempt at fixing it.</p>
<p><strong>The array shape hides it from every reconciler written in a hurry.</strong> <code>available</code> looks like a single number in the Dashboard and is a list in the API. Code that reads <code>available[0]</code> gets whichever currency Stripe happened to list first, reconciles it perfectly, and is structurally incapable of noticing the second entry.</p>
<p><strong>The pending array is the early warning.</strong> Funds land in <code>pending</code> first and move to <code>available</code> after the settlement delay. A currency whose <code>pending</code> grows while its <code>available</code> stays flat is a bucket being filled with the tap already known to be blocked, and it is visible days before the money is stuck.</p>""",
"steps": [
 {"h": "Read both arrays in full, on every account",
  "body": """<p><code>GET /v1/balance</code> for the platform, then the same call with a <code>Stripe-Account</code> header per connected account. More than one entry in <code>available</code> or <code>pending</code> is the flag; a single entry with a non-zero amount in a currency you do not bank in is the same problem with only one bucket.</p>"""},
 {"h": "Look for an exit for each currency",
  "body": """<p><code>GET /v1/accounts/{id}/external_accounts?limit=100</code> and match on the <code>currency</code> field of each bank account or card. No match means the balance is stranded by construction, not delayed.</p>"""},
 {"h": "Check that payouts in that currency have actually happened",
  "body": """<p>A destination can exist and still not be used, because <code>default_for_currency</code> was never set on it. <code>GET /v1/payouts?limit=100</code> over the last 90 days, grouped by <code>currency</code>, is the evidence that the route works rather than the assumption that it does.</p>"""},
 {"h": "Separate stranded from merely accruing",
  "body": """<p>Money already in <code>available</code> with no destination is stuck now. Money in <code>pending</code> with no destination will be stuck in a few days. They deserve the same fix and a different urgency, and reporting them as one number loses that.</p>"""},
 {"h": "Either add the destination or stop accepting the currency",
  "body": """<p>Both are legitimate. If you want the currency, add an external account in it and set <code>default_for_currency</code>. If you do not, remove it from the payment method configuration so no new charges settle there, and then drain the residue once with a one-off payout to a destination you added for the purpose.</p>"""},
],
"verify": """<p>Re-run the script. Every currency with a balance should report a destination and recent payouts, and the account total should reconcile against the bank without a residual.</p>
<pre><code class="language-bash">python3 stripe_stranded_currency.py
# usd  draining   destination present, 14 payout(s) in the window
# 1 bucket(s): 0 stranded, 0 accruing, 0 stalled</code></pre>""",
"code_intro": "Three GETs: the balance, the external accounts, and the recent payouts, all read-only. The classifier is pure and takes the four facts that decide the outcome for one currency &mdash; what is settled, what is on the way, whether a destination exists, and whether payouts in that currency have actually happened &mdash; because a missing destination and an unused destination look the same on the balance and need different repairs.",
"py_file": "stripe_stranded_currency.py",
"py": '''"""Report Stripe balance currencies that no payout can drain.

Read only. Three GETs and no writes: give this a RESTRICTED key with read access
to Balance, Connected accounts and Payouts. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_stranded_currency")

API = "https://api.stripe.com/v1"

DAY = 86400


def classify(entry, pending, has_destination, payouts_seen):
    """Sort one currency of a Stripe balance. Pure, so the states can be tested
    without a network.

    `entry` is one element of balance.available. `pending` is the amount in the
    matching balance.pending entry. `has_destination` is whether any external
    account on this account holds that currency, and `payouts_seen` is how many
    payouts in that currency happened in the window.

    Returns (state, detail).
    """
    amount = entry.get("amount")
    if not isinstance(amount, int):
        return ("unknown", "available entry has no numeric amount: %r" % (amount,))

    if not has_destination:
        if amount > 0:
            return ("stranded",
                    "%d settled with no external account in this currency: no "
                    "automatic payout can target it, so it will sit here "
                    "indefinitely" % amount)
        if pending > 0:
            return ("accruing",
                    "%d still pending with no external account in this currency: "
                    "it becomes stranded when it settles" % pending)
        return ("clear", "no destination for this currency, but nothing is in it")

    if amount > 0 and not payouts_seen:
        return ("stalled",
                "%d settled and a destination exists, but no payout in this "
                "currency in the window: the external account is probably not "
                "default_for_currency" % amount)

    if amount > 0 or pending > 0:
        return ("draining",
                "destination present, %d payout(s) in the window" % payouts_seen)

    return ("clear", "empty bucket")


def get(session, path, headers=None, **params):
    r = session.get(API + path, params=params, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def payout_currencies(session, headers, since):
    """Count payouts per currency over the window."""
    counts = {}
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/payouts", headers=headers, **params)
        data = page.get("data", [])
        for p in data:
            cur = p.get("currency", "?")
            counts[cur] = counts.get(cur, 0) + 1
        if not data or not page.get("has_more"):
            return counts
        params["starting_after"] = data[-1]["id"]


def destination_currencies(session, headers, account_id):
    """Currencies that have somewhere to be paid out to."""
    out = set()
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts/%s/external_accounts" % account_id,
                   headers=headers, **params)
        data = page.get("data", [])
        for ext in data:
            if ext.get("currency"):
                out.add(ext["currency"])
        if not data or not page.get("has_more"):
            return out
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--account", help="a connected account id to check instead of "
                                      "the account the key belongs to")
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to look for payouts in each currency")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})
    headers = {"Stripe-Account": args.account} if args.account else None

    since = int(time.time()) - args.days * DAY
    account_id = args.account or get(s, "/account").get("id", "")
    balance = get(s, "/balance", headers=headers)
    destinations = destination_currencies(s, headers, account_id)
    payouts = payout_currencies(s, headers, since)

    pending = {e.get("currency", "?"): e.get("amount") or 0
               for e in balance.get("pending", [])}
    available = balance.get("available", [])

    # Union both arrays: a currency can be entirely in pending, which is the
    # state worth catching because it is the one you can still act on early.
    currencies = {e.get("currency", "?") for e in available} | set(pending)

    counts = {}
    for cur in sorted(currencies):
        entry = next((e for e in available if e.get("currency") == cur),
                     {"currency": cur, "amount": 0})
        state, detail = classify(entry, pending.get(cur, 0),
                                 cur in destinations, payouts.get(cur, 0))
        counts[state] = counts.get(state, 0) + 1
        line = "%-4s %-10s %s" % (cur, state, detail)
        (log.info if state in ("clear", "draining") else log.warning)(line)

    stranded = counts.get("stranded", 0)
    accruing = counts.get("accruing", 0)
    stalled = counts.get("stalled", 0)
    log.info("%d bucket(s): %d stranded, %d accruing, %d stalled",
             len(currencies), stranded, accruing, stalled)

    if stranded or accruing:
        log.warning("  repair: add a destination in that currency and make it the "
                    "default, or stop accepting the currency:")
        log.warning("  POST %s/accounts/%s with external_account in the currency, "
                    "then default_for_currency=true", API, account_id or "{id}")
    if stalled:
        log.warning("  repair: a destination exists but is not being used. Check "
                    "default_for_currency on it before adding another one.")
    return 1 if (stranded or accruing or stalled or counts.get("unknown")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-stranded-currency.mjs",
"js": '''/**
 * Report Stripe balance currencies that no payout can drain.
 *
 * Read only. Three GETs and no writes: give this a RESTRICTED key with read
 * access to Balance, Connected accounts and Payouts. The repair is printed,
 * never performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;

/**
 * Sort one currency of a Stripe balance. Pure, so the states can be tested
 * without a network. Returns [state, detail].
 */
export function classify(entry, pending, hasDestination, payoutsSeen) {
  const amount = entry.amount;
  if (typeof amount !== 'number' || !Number.isFinite(amount)) {
    return ['unknown',
      `available entry has no numeric amount: ${JSON.stringify(amount)}`];
  }

  if (!hasDestination) {
    if (amount > 0) {
      return ['stranded',
        `${amount} settled with no external account in this currency: no ` +
        'automatic payout can target it, so it will sit here indefinitely'];
    }
    if (pending > 0) {
      return ['accruing',
        `${pending} still pending with no external account in this currency: ` +
        'it becomes stranded when it settles'];
    }
    return ['clear', 'no destination for this currency, but nothing is in it'];
  }

  if (amount > 0 && !payoutsSeen) {
    return ['stalled',
      `${amount} settled and a destination exists, but no payout in this ` +
      'currency in the window: the external account is probably not ' +
      'default_for_currency'];
  }

  if (amount > 0 || pending > 0) {
    return ['draining', `destination present, ${payoutsSeen} payout(s) in the window`];
  }

  return ['clear', 'empty bucket'];
}

async function get(key, path, params = {}, headers = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${key}`, ...headers },
  });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function payoutCurrencies(key, headers, since) {
  const counts = new Map();
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/payouts', params, headers);
    const data = page.data ?? [];
    for (const p of data) {
      const cur = p.currency ?? '?';
      counts.set(cur, (counts.get(cur) ?? 0) + 1);
    }
    if (data.length === 0 || !page.has_more) return counts;
    params.starting_after = data[data.length - 1].id;
  }
}

export async function destinationCurrencies(key, headers, accountId) {
  const out = new Set();
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, `/accounts/${accountId}/external_accounts`,
                           params, headers);
    const data = page.data ?? [];
    for (const ext of data) if (ext.currency) out.add(ext.currency);
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

  const account = process.env.STRIPE_ACCOUNT ?? null;
  const headers = account ? { 'Stripe-Account': account } : {};
  const since = Math.floor(Date.now() / 1000) - 90 * DAY;

  const accountId = account ?? (await get(key, '/account')).id;
  const balance = await get(key, '/balance', {}, headers);
  const destinations = await destinationCurrencies(key, headers, accountId);
  const payouts = await payoutCurrencies(key, headers, since);

  const pending = new Map((balance.pending ?? [])
    .map((e) => [e.currency ?? '?', e.amount ?? 0]));
  const available = balance.available ?? [];
  const currencies = new Set([
    ...available.map((e) => e.currency ?? '?'), ...pending.keys(),
  ]);

  const counts = {};
  for (const cur of [...currencies].sort()) {
    const entry = available.find((e) => e.currency === cur)
      ?? { currency: cur, amount: 0 };
    const [state, detail] = classify(entry, pending.get(cur) ?? 0,
                                     destinations.has(cur), payouts.get(cur) ?? 0);
    counts[state] = (counts[state] ?? 0) + 1;
    const line = `${cur.padEnd(4)} ${state.padEnd(10)} ${detail}`;
    if (state === 'clear' || state === 'draining') console.log(line);
    else console.warn(line);
  }

  const stranded = counts.stranded ?? 0;
  const accruing = counts.accruing ?? 0;
  const stalled = counts.stalled ?? 0;
  console.log(`${currencies.size} bucket(s): ${stranded} stranded, ` +
              `${accruing} accruing, ${stalled} stalled`);

  if (stranded || accruing) {
    console.warn('  repair: add a destination in that currency and make it the ' +
                 'default, or stop accepting the currency:');
    console.warn(`  POST ${API}/accounts/${accountId} with external_account in ` +
                 'the currency, then default_for_currency=true');
  }
  if (stalled) {
    console.warn('  repair: a destination exists but is not being used. Check ' +
                 'default_for_currency on it before adding another one.');
  }
  if (stranded || accruing || stalled || counts.unknown) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The interesting boundary is between <em>stranded</em> and <em>stalled</em>: both are money that is not moving, but one has no destination at all and the other has one that automatic payouts are ignoring. The <em>accruing</em> test covers the case that is still cheap to fix, where the funds are in <code>pending</code> and the exit does not exist yet.",
"test_py_file": "test_stripe_stranded_currency.py",
"test_py": '''from stripe_stranded_currency import classify


def test_settled_funds_with_no_destination_are_stranded():
    state, detail = classify({"currency": "eur", "amount": 41200}, 0, False, 0)
    assert state == "stranded"
    assert "41200" in detail


def test_pending_funds_with_no_destination_are_caught_early():
    # Nothing has settled yet, so this is the version of the problem you can
    # still fix before anybody has to reconcile around it.
    state, detail = classify({"currency": "eur", "amount": 0}, 8000, False, 0)
    assert state == "accruing"
    assert "stranded when it settles" in detail


def test_a_destination_that_never_pays_out_is_its_own_state():
    state, detail = classify({"currency": "gbp", "amount": 9500}, 0, True, 0)
    assert state == "stalled"
    assert "default_for_currency" in detail


def test_destination_and_payouts_is_healthy():
    state, _ = classify({"currency": "usd", "amount": 250000}, 40000, True, 14)
    assert state == "draining"


def test_empty_bucket_with_no_destination_is_not_a_problem():
    state, _ = classify({"currency": "eur", "amount": 0}, 0, False, 0)
    assert state == "clear"
''',
"test_js_file": "stripe-stranded-currency.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-stranded-currency.mjs';

test('settled funds with no destination are stranded', () => {
  const [state, detail] = classify({ currency: 'eur', amount: 41200 }, 0, false, 0);
  assert.equal(state, 'stranded');
  assert.match(detail, /41200/);
});

test('pending funds with no destination are caught early', () => {
  const [state, detail] = classify({ currency: 'eur', amount: 0 }, 8000, false, 0);
  assert.equal(state, 'accruing');
  assert.match(detail, /stranded when it settles/);
});

test('a destination that never pays out is its own state', () => {
  const [state, detail] = classify({ currency: 'gbp', amount: 9500 }, 0, true, 0);
  assert.equal(state, 'stalled');
  assert.match(detail, /default_for_currency/);
});

test('destination and payouts is healthy', () => {
  assert.equal(
    classify({ currency: 'usd', amount: 250000 }, 40000, true, 14)[0], 'draining');
});

test('empty bucket with no destination is not a problem', () => {
  assert.equal(classify({ currency: 'eur', amount: 0 }, 0, false, 0)[0], 'clear');
});
''',
"faq": [
 ("Why will Stripe not just convert the balance and pay it out?",
  "Payouts settle in the currency of the funds. Stripe pays a EUR balance to a destination that holds EUR, and will not convert it into your USD bank account on the way. Without a matching external account there is nothing for the payout to target."),
 ("I added a bank account in that currency and nothing happened. Why?",
  "Adding the destination is only half of it. Automatic payouts follow the external account flagged default_for_currency for that currency, so an account added without the flag sits there unused and the balance does not move."),
 ("How did I end up with a currency I do not sell in?",
  "Usually a widened payment method configuration, a localised Checkout page, or one invoice raised in a customer's own currency. A handful of charges is enough: once any amount settles in a currency, the bucket exists permanently."),
 ("Is a growing pending amount in that currency worse?",
  "It is the same problem earlier. Funds land in pending and move to available after the settlement delay, so a currency whose pending grows while its available stays flat tells you money is on its way into a bucket with no exit, days before it is stuck."),
 ("Does this need a live secret key?",
  "No. Balance, Connected accounts and Payouts with read access covers all three requests, including the per-account version through the Stripe-Account header."),
],
"related": [
 ("/stripe/no-external-account-attached/", "No external account is attached so payouts cannot land"),
 ("/stripe/payout-schedule-left-on-manual/", "A payout schedule left on manual strands the balance"),
 ("/stripe/connect-reserved-balance-growing/", "connect_reserved grows as connected accounts go negative"),
],
"citations": [CITE_BALANCE_OBJ, CITE_PAYOUTS, CITE_CURRENCIES, CITE_CONNECT_PAYOUTS],
},

{
"slug": "application-fees-zero-on-platform",
"title": "The platform collects zero application fees on its charges",
"description": "Marketplace volume climbs while platform revenue stays at zero. No ApplicationFee object exists, because application_fee_amount was never passed.",
"h1": "the platform collects zero application fees on its charges",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe application_fee_amount", "stripe application fees empty",
             "stripe connect platform revenue", "destination charge fee",
             "stripe transfer_data amount"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The marketplace is working. Volume is up, sellers are getting paid, the Connect dashboard is busy. The platform's own revenue line reads zero, and has since launch. Nothing errored: every charge did exactly what it was told, which was to pass the whole amount through.",
"short_answer": """<p>Read <code>GET /v1/application_fees?limit=100&amp;created[gte]=</code> over the last 30 days. An empty list on a platform that is taking destination charges means no <code>ApplicationFee</code> object has ever been created, and a fee object only exists when you pass <code>application_fee_amount</code> on the charge.</p>
<p>Then count the other side: <code>GET /v1/charges</code> and look for entries with <code>transfer_data.destination</code> set but <code>application_fee_amount</code> null. That count is how many charges went out at full value. Cross-check with <code>GET /v1/balance_transactions?type=application_fee</code>, which should be empty for the same reason.</p>""",
"problem": """<p>There is no error to find. Omitting <code>application_fee_amount</code> is a perfectly valid destination charge: the platform takes the payment, the whole amount is transferred to the connected account, and everybody involved gets a success response. The only thing missing is the platform's cut, and nothing in the API is going to raise that as a concern.</p>
<p>The second version is worse, because it looks like it is working. If the integration under-transfers by setting <code>transfer_data.amount</code> to less than the charge, the platform does keep the difference &mdash; but no <code>ApplicationFee</code> object is created for it. Revenue is real and invisible: every fee report, every reconciliation built on <code>/v1/application_fees</code>, and the Dashboard's own application fees page all read zero.</p>""",
"why": """<p><strong>The fee object is created by a parameter, not by a setting.</strong> There is no platform-level fee percentage that Stripe applies for you. <code>ApplicationFee</code> exists only where <code>application_fee_amount</code> was passed on the PaymentIntent or Charge, in minor units, per charge. Miss the parameter on one code path and that path is free.</p>
<p><strong>Under-transferring is a different mechanism with the same balance effect.</strong> Setting <code>transfer_data.amount</code> below the charge total leaves the remainder on the platform. The money is right and the reporting is wrong, because the split happened inside the transfer rather than as a fee. Anyone reconciling platform revenue from application fees will conclude the marketplace is free.</p>
<p><strong>It usually starts as one code path.</strong> Subscriptions, invoices, a mobile checkout added later, a manual charge for enterprise deals. Each of these creates charges through a different call, and the one written last is the one that forgot the parameter. Which is why the useful number is not <em>are there fees</em> but <em>what fraction of destination charges have one</em>.</p>
<p><strong>Fee collection depends on the destination's transfers capability.</strong> Passing <code>application_fee_amount</code> to an account whose <code>transfers</code> capability is not <code>active</code> fails the whole charge rather than quietly dropping the fee. So a team that adds the parameter without checking capabilities first turns a revenue leak into declined payments, which is a worse Monday.</p>""",
"steps": [
 {"h": "List application fees over a window you actually traded in",
  "body": """<p><code>GET /v1/application_fees?limit=100&amp;created[gte]=</code> for the last 30 days. Zero results on a platform with destination charges in the same window is the finding; zero results on a platform with no destination charges at all just means the window was quiet.</p>"""},
 {"h": "Count the destination charges, split three ways",
  "body": """<p>Paginate <code>GET /v1/charges</code> and sort each charge with <code>transfer_data.destination</code> into one of three buckets: it has <code>application_fee_amount</code>, it has a <code>transfer_data.amount</code> below the charge total, or it has neither. The three buckets are collected revenue, invisible revenue and no revenue.</p>"""},
 {"h": "Cross-check the balance transactions",
  "body": """<p><code>GET /v1/balance_transactions?type=application_fee</code> should agree with the fee list. If fees exist as objects but never as balance transactions, you are looking at a different problem &mdash; fees on charges that were later refunded &mdash; and the revenue was collected and given back.</p>"""},
 {"h": "Check the transfers capability before changing anything",
  "body": """<p>For each destination you are about to start charging a fee on, confirm <code>capabilities.transfers</code> is <code>active</code>. Adding <code>application_fee_amount</code> to a charge aimed at an account without it fails the payment outright, so this check is what keeps the fix from becoming an outage.</p>"""},
 {"h": "Add the parameter on every path that creates a charge",
  "body": """<p>The gap is almost never in the main checkout. Enumerate the places charges are created &mdash; subscriptions, invoices, the mobile app, the admin tool &mdash; and confirm each one passes <code>application_fee_amount</code> alongside <code>transfer_data.destination</code>. Then re-run this script and watch the fraction, not the total.</p>"""},
],
"verify": """<p>Re-run the script over the days since the fix. Every destination charge should carry a fee, and the fee count should track the charge count rather than sitting at zero.</p>
<pre><code class="language-bash">python3 stripe_application_fees.py --days 7
# collecting  312 destination charge(s), 312 with application_fee_amount
# 288 application fee object(s) in the window</code></pre>""",
"code_intro": "Two paginated GETs and one cheap cross-check, all read-only &mdash; a restricted key with read access to Charges, Application fees and Balance transactions covers it. The classifier is pure and takes four counts, because the difference between <em>no fee is being taken</em> and <em>a fee is being taken invisibly</em> is arithmetic on those counts and not something you can see on any single charge.",
"py_file": "stripe_application_fees.py",
"py": '''"""Report destination charges that carry no application fee.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Charges, Application fees and Balance transactions. The repair is
printed, never performed, because this script holds a credential to a live
payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_application_fees")

API = "https://api.stripe.com/v1"

DAY = 86400


def classify(fee_count, dest_total, dest_with_fee, dest_implicit):
    """Sort a platform's fee collection over one window. Pure, so the states can
    be tested without a network.

    `fee_count` is how many ApplicationFee objects exist in the window.
    `dest_total` is how many charges had transfer_data.destination set,
    `dest_with_fee` how many of those carried application_fee_amount, and
    `dest_implicit` how many instead under-transferred with transfer_data.amount,
    which keeps money on the platform without ever creating a fee object.

    Returns (state, detail).
    """
    counts = (fee_count, dest_total, dest_with_fee, dest_implicit)
    if any(not isinstance(c, int) or c < 0 for c in counts):
        return ("unknown", "counts must be non-negative integers: %r" % (counts,))
    if dest_with_fee + dest_implicit > dest_total:
        return ("unknown",
                "%d charges with a fee and %d implicit against only %d destination "
                "charges: the counts do not agree"
                % (dest_with_fee, dest_implicit, dest_total))

    if dest_total == 0:
        return ("idle",
                "no destination charges in the window, so there is nothing here "
                "that could carry an application fee")

    if fee_count == 0 and dest_implicit and not dest_with_fee:
        return ("invisible",
                "%d of %d destination charge(s) keep money on the platform via "
                "transfer_data[amount] and no ApplicationFee object exists: the "
                "revenue is real but every fee report will read zero"
                % (dest_implicit, dest_total))

    if fee_count == 0:
        return ("zero",
                "%d destination charge(s), none with application_fee_amount: the "
                "full amount went to the connected account every time"
                % dest_total)

    missing = dest_total - dest_with_fee - dest_implicit
    if missing > 0:
        return ("partial",
                "%d of %d destination charge(s) carry no fee at all: one code path "
                "that creates charges is not passing application_fee_amount"
                % (missing, dest_total))

    if dest_implicit:
        return ("mixed",
                "%d charge(s) take the fee explicitly and %d take it implicitly "
                "through transfer_data[amount]: the implicit ones never appear in "
                "/v1/application_fees" % (dest_with_fee, dest_implicit))

    return ("collecting",
            "%d destination charge(s), %d with application_fee_amount"
            % (dest_total, dest_with_fee))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def count_pages(session, path, since, cap, on_item=None):
    """Paginate a created[gte] list, optionally inspecting each item."""
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for item in data:
            seen += 1
            if on_item:
                on_item(item)
        if not data or not page.get("has_more") or seen >= cap:
            return seen
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30, help="window to look at")
    ap.add_argument("--max-charges", type=int, default=5000,
                    help="stop paginating charges after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * DAY

    fee_count = count_pages(s, "/application_fees", since, 5000)

    tally = {"dest": 0, "fee": 0, "implicit": 0}
    destinations = set()

    def inspect(charge):
        transfer = charge.get("transfer_data") or {}
        dest = transfer.get("destination")
        if not dest:
            return
        tally["dest"] += 1
        destinations.add(dest if isinstance(dest, str) else dest.get("id", "?"))
        if charge.get("application_fee_amount") is not None:
            tally["fee"] += 1
        elif (transfer.get("amount") is not None
              and transfer["amount"] < (charge.get("amount") or 0)):
            tally["implicit"] += 1

    count_pages(s, "/charges", since, args.max_charges, inspect)

    state, detail = classify(fee_count, tally["dest"], tally["fee"],
                             tally["implicit"])
    (log.info if state in ("collecting", "idle") else log.warning)(
        "%-11s %s", state, detail)
    log.info("%d application fee object(s) in the window", fee_count)

    # The fee list and the application_fee balance transactions should agree.
    # Fees that exist as objects but never as balance transactions were
    # collected and then refunded, which is a different problem from this one.
    bt_page = get(s, "/balance_transactions", limit=100, type="application_fee",
                  **{"created[gte]": since})
    if fee_count and not bt_page.get("data"):
        log.warning("fee objects exist but no application_fee balance transaction "
                    "in the window: the fees were taken and refunded back out")

    if state in ("zero", "invisible", "partial", "mixed"):
        log.warning("  repair: pass application_fee_amount in minor units on every "
                    "call that creates a charge with transfer_data[destination], "
                    "including subscriptions and invoices.")
        log.warning("  check first, on each destination: GET %s/accounts/{id} and "
                    "confirm capabilities.transfers is active, because a fee on an "
                    "account without it fails the whole charge.", API)
        log.warning("  %d destination account(s) seen in this window", len(destinations))
        return 1
    return 1 if state == "unknown" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-application-fees.mjs",
"js": '''/**
 * Report destination charges that carry no application fee.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Charges, Application fees and Balance transactions. The repair is
 * printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;

/**
 * Sort a platform's fee collection over one window. Pure, so the states can be
 * tested without a network. Returns [state, detail].
 */
export function classify(feeCount, destTotal, destWithFee, destImplicit) {
  const counts = [feeCount, destTotal, destWithFee, destImplicit];
  if (counts.some((c) => !Number.isInteger(c) || c < 0)) {
    return ['unknown',
      `counts must be non-negative integers: ${JSON.stringify(counts)}`];
  }
  if (destWithFee + destImplicit > destTotal) {
    return ['unknown',
      `${destWithFee} charges with a fee and ${destImplicit} implicit against ` +
      `only ${destTotal} destination charges: the counts do not agree`];
  }

  if (destTotal === 0) {
    return ['idle',
      'no destination charges in the window, so there is nothing here that ' +
      'could carry an application fee'];
  }

  if (feeCount === 0 && destImplicit && !destWithFee) {
    return ['invisible',
      `${destImplicit} of ${destTotal} destination charge(s) keep money on the ` +
      'platform via transfer_data[amount] and no ApplicationFee object exists: ' +
      'the revenue is real but every fee report will read zero'];
  }

  if (feeCount === 0) {
    return ['zero',
      `${destTotal} destination charge(s), none with application_fee_amount: ` +
      'the full amount went to the connected account every time'];
  }

  const missing = destTotal - destWithFee - destImplicit;
  if (missing > 0) {
    return ['partial',
      `${missing} of ${destTotal} destination charge(s) carry no fee at all: ` +
      'one code path that creates charges is not passing application_fee_amount'];
  }

  if (destImplicit) {
    return ['mixed',
      `${destWithFee} charge(s) take the fee explicitly and ${destImplicit} take ` +
      'it implicitly through transfer_data[amount]: the implicit ones never ' +
      'appear in /v1/application_fees'];
  }

  return ['collecting',
    `${destTotal} destination charge(s), ${destWithFee} with application_fee_amount`];
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

export async function countPages(key, path, since, cap = 5000, onItem = null) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const item of data) {
      seen += 1;
      if (onItem) onItem(item);
    }
    if (data.length === 0 || !page.has_more || seen >= cap) return seen;
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

  const days = Number(process.env.WINDOW_DAYS ?? 30);
  const since = Math.floor(Date.now() / 1000) - days * DAY;

  const feeCount = await countPages(key, '/application_fees', since);

  const tally = { dest: 0, fee: 0, implicit: 0 };
  const destinations = new Set();

  await countPages(key, '/charges', since, 5000, (charge) => {
    const transfer = charge.transfer_data ?? {};
    const dest = transfer.destination;
    if (!dest) return;
    tally.dest += 1;
    destinations.add(typeof dest === 'string' ? dest : (dest.id ?? '?'));
    if (charge.application_fee_amount !== null
        && charge.application_fee_amount !== undefined) {
      tally.fee += 1;
    } else if (transfer.amount !== null && transfer.amount !== undefined
               && transfer.amount < (charge.amount ?? 0)) {
      tally.implicit += 1;
    }
  });

  const [state, detail] = classify(feeCount, tally.dest, tally.fee, tally.implicit);
  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'collecting' || state === 'idle') console.log(line);
  else console.warn(line);
  console.log(`${feeCount} application fee object(s) in the window`);

  // Fees that exist as objects but never as balance transactions were collected
  // and then refunded, which is a different problem from this one.
  const btPage = await get(key, '/balance_transactions',
    { limit: 100, type: 'application_fee', 'created[gte]': since });
  if (feeCount && (btPage.data ?? []).length === 0) {
    console.warn('fee objects exist but no application_fee balance transaction in ' +
                 'the window: the fees were taken and refunded back out');
  }

  if (['zero', 'invisible', 'partial', 'mixed'].includes(state)) {
    console.warn('  repair: pass application_fee_amount in minor units on every ' +
                 'call that creates a charge with transfer_data[destination], ' +
                 'including subscriptions and invoices.');
    console.warn(`  check first, on each destination: GET ${API}/accounts/{id} and ` +
                 'confirm capabilities.transfers is active, because a fee on an ' +
                 'account without it fails the whole charge.');
    console.warn(`  ${destinations.size} destination account(s) seen in this window`);
    process.exitCode = 1;
  } else if (state === 'unknown') {
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
"test_intro": "The test that matters is <em>invisible</em>: a platform that keeps money by under-transferring has real revenue and zero fee objects, and collapsing that into the same bucket as a platform taking nothing at all sends somebody to add a parameter that would double-charge the seller. The <em>partial</em> test covers the ordinary version, where one code path out of four forgot.",
"test_py_file": "test_stripe_application_fees.py",
"test_py": '''from stripe_application_fees import classify


def test_no_destination_charges_is_not_a_finding():
    state, _ = classify(0, 0, 0, 0)
    assert state == "idle"


def test_destination_charges_with_no_fees_anywhere():
    state, detail = classify(0, 480, 0, 0)
    assert state == "zero"
    assert "480" in detail


def test_under_transferring_is_revenue_that_no_report_shows():
    # The platform is keeping the difference, so the money is right and every
    # fee report is wrong. Telling someone to "add the fee" here is a mistake.
    state, detail = classify(0, 480, 0, 480)
    assert state == "invisible"
    assert "transfer_data[amount]" in detail


def test_one_code_path_missing_the_parameter():
    state, detail = classify(360, 480, 360, 0)
    assert state == "partial"
    assert "120 of 480" in detail


def test_counts_that_do_not_add_up_are_not_reported_as_healthy():
    state, _ = classify(10, 5, 4, 3)
    assert state == "unknown"
''',
"test_js_file": "stripe-application-fees.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-application-fees.mjs';

test('no destination charges is not a finding', () => {
  assert.equal(classify(0, 0, 0, 0)[0], 'idle');
});

test('destination charges with no fees anywhere', () => {
  const [state, detail] = classify(0, 480, 0, 0);
  assert.equal(state, 'zero');
  assert.match(detail, /480/);
});

test('under transferring is revenue that no report shows', () => {
  const [state, detail] = classify(0, 480, 0, 480);
  assert.equal(state, 'invisible');
  assert.match(detail, /transfer_data\\[amount\\]/);
});

test('one code path missing the parameter', () => {
  const [state, detail] = classify(360, 480, 360, 0);
  assert.equal(state, 'partial');
  assert.match(detail, /120 of 480/);
});

test('counts that do not add up are not reported as healthy', () => {
  assert.equal(classify(10, 5, 4, 3)[0], 'unknown');
});
''',
"faq": [
 ("Why is /v1/application_fees empty when the marketplace is busy?",
  "Because an ApplicationFee object is only created when application_fee_amount is passed on the charge. There is no platform-wide fee setting that Stripe applies for you, so a destination charge without that parameter transfers the full amount and leaves no fee behind."),
 ("We keep money by setting transfer_data[amount] lower. Is that the same thing?",
  "Financially yes, for reporting no. Under-transferring leaves the remainder on the platform without creating a fee object, so the revenue exists but /v1/application_fees, the application fee balance transactions and the Dashboard's fees page all read zero."),
 ("Can I add the fee retroactively to charges that already settled?",
  "No. The fee is part of the charge, so it has to be set when the charge is created. Money already transferred can only be recovered by a separate transfer reversal, which is a different operation with different consequences for the seller."),
 ("Why did adding application_fee_amount start failing charges?",
  "Fee collection depends on the destination account's transfers capability being active. Passing the parameter to an account without it fails the entire charge rather than dropping the fee, so check capabilities.transfers on every destination before rolling the change out."),
 ("Which code paths usually forget the parameter?",
  "The ones written after the main checkout: subscriptions and invoices, a mobile client, an internal admin tool for enterprise deals. That is why the number to watch is the fraction of destination charges carrying a fee, not whether any fees exist."),
],
"related": [
 ("/stripe/transfers-capability-inactive/", "The transfers capability is inactive so every transfer 400s"),
 ("/stripe/connect-reserved-balance-growing/", "connect_reserved grows as connected accounts go negative"),
 ("/stripe/payout-reconciliation-unavailable/", "Payouts cannot be tied back to their balance transactions"),
],
"citations": [CITE_APP_FEE_OBJ, CITE_CONNECT_CHARGES, CITE_DESTINATION_CHARGES,
              CITE_CHARGE_OBJ],
},

{
"slug": "payout-reconciliation-unavailable",
"title": "Payouts cannot be tied back to their balance transactions",
"description": "Finance gets one bank deposit and cannot say what is in it. balance_transactions?payout=po_x returns nothing, because manual payouts are never reconciled.",
"h1": "payouts cannot be tied back to their balance transactions",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payout reconciliation", "reconciliation_status not_applicable",
             "balance_transactions payout", "stripe manual payout reconciliation",
             "payout_reconciliation itemized"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A single deposit arrives in the bank and finance asks the only reasonable question: what is in it? The obvious answer, <code>GET /v1/balance_transactions?payout=po_x</code>, comes back with an empty list. Not an error, not a permissions problem &mdash; an empty list, on a payout that definitely happened.",
"short_answer": """<p>Read <code>reconciliation_status</code> on the payout. Stripe only lets you list balance transactions by payout when that field is <code>"completed"</code>, and it only reaches <code>completed</code> for standard <em>automatic</em> payouts. Every payout you create yourself comes back <code>not_applicable</code>, and no balance transaction will ever list against it.</p>
<p>So <code>GET /v1/payouts?limit=100&amp;created[gte]=</code> and flag anything where <code>reconciliation_status != "completed"</code> or <code>automatic == false</code>. For the ones that are completed, check the arithmetic: paginate <code>GET /v1/balance_transactions?payout=po_x</code> and confirm the sum of <code>net</code> equals the payout <code>amount</code>.</p>""",
"problem": """<p>This is a structural loss, not an outage. A platform that runs its payouts manually &mdash; because somebody wanted control over the timing, or because the schedule was set to manual during testing and never changed &mdash; has permanently given up the ability to ask Stripe what a given deposit contained. The payouts work perfectly. It is the audit trail that does not exist.</p>
<p>It surfaces at the worst time, which is during a reconciliation somebody else is running: an accountant closing a quarter, an auditor sampling deposits, a finance hire trying to explain a variance. The answer is not in the API and cannot be added retroactively by changing a setting today, because the linkage was never recorded for the payouts that already went out.</p>""",
"why": """<p><strong><code>reconciliation_status</code> is not a progress indicator, it is a capability flag.</strong> <code>completed</code> means Stripe has assembled the list of balance transactions for that payout. <code>in_progress</code> means it is doing so. <code>not_applicable</code> means it never will, and that is the value manual payouts get from the moment they are created.</p>
<p><strong>Manual payouts opt out of it by definition.</strong> When you decide what leaves and when, Stripe is no longer the party assembling the payout out of a known set of transactions, so it cannot report which ones went into it. This is the trade for the control, and it is rarely made deliberately &mdash; the schedule usually got left on manual by accident.</p>
<p><strong>The sum is worth checking even when the status is right.</strong> A payout whose linked balance transactions do not sum to its amount is telling you something specific: transactions in a currency you did not expect, a reversal that landed in the window, or a page of results you stopped paginating too early. A reconciliation that never verifies the total is only checking that the endpoint responds.</p>
<p><strong><code>transfer_group</code> is the part you control, and it is usually empty.</strong> Charges and transfers that share a <code>transfer_group</code> can be joined back together whatever the payout says. Left null, as it is by default, each side of a marketplace transaction is an unrelated object and the reconstruction is guesswork even where Stripe does give you the payout breakdown.</p>""",
"steps": [
 {"h": "Read reconciliation_status and automatic on every recent payout",
  "body": """<p><code>GET /v1/payouts?limit=100&amp;created[gte]=</code> over 90 days. Two fields decide everything: <code>reconciliation_status</code> says whether a breakdown exists, and <code>automatic</code> says why. A <code>not_applicable</code> on a manual payout is a policy problem; the same value on an automatic one means the payout is of a kind Stripe does not itemise.</p>"""},
 {"h": "Verify the arithmetic on the ones that are reconcilable",
  "body": """<p>Paginate <code>GET /v1/balance_transactions?payout=po_x&amp;limit=100</code> and sum <code>net</code>. It should equal the payout's <code>amount</code>. Anything else is a real discrepancy and worth a look before the quarter closes rather than after.</p>"""},
 {"h": "Move the schedule to automatic so future payouts are itemised",
  "body": """<p>An automatic daily or weekly schedule restores <code>reconciliation_status: "completed"</code> from the next payout onward. It does nothing for history, which is the argument for doing it today rather than at the next audit.</p>"""},
 {"h": "Use the Reporting API for the payouts you cannot re-run",
  "body": """<p><code>payout_reconciliation.by_id.itemized.1</code> takes a single payout id; <code>payout_reconciliation.itemized.7</code> covers an interval and joins on the <code>automatic_payout_id</code> column. This is the only route to a breakdown of payouts that have already left.</p>"""},
 {"h": "Set transfer_group on everything from now on",
  "body": """<p>It costs one parameter at charge and transfer creation and it is the only linkage that survives regardless of payout mechanics. Also worth listing reversed transfers &mdash; <code>amount_reversed &gt; 0</code> &mdash; because they move money without a matching charge and are the usual explanation for a sum that is close but not equal.</p>"""},
],
"verify": """<p>Re-run the script over the days since the schedule changed. Every payout should be <code>completed</code>, and every checked sum should match the payout amount exactly.</p>
<pre><code class="language-bash">python3 stripe_payout_reconciliation.py --days 14
# po_1Abc  reconciled   87 balance transaction(s) sum to the payout
# 12 payout(s): 0 manual, 0 mismatched, 0 unsupported</code></pre>""",
"code_intro": "One paginated GET over the payouts, then one paginated GET per reconcilable payout to check the sum &mdash; read access to Payouts and Balance transactions is all the key needs. The classifier is pure and takes the payout plus the summed <code>net</code> of its balance transactions, with <code>None</code> meaning the sum was not fetched, so the difference between <em>not checked</em>, <em>checked and correct</em> and <em>checked and wrong</em> stays visible instead of collapsing into a boolean.",
"py_file": "stripe_payout_reconciliation.py",
"py": '''"""Report payouts that cannot be tied back to their balance transactions.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Payouts and Balance transactions. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_payout_reconciliation")

API = "https://api.stripe.com/v1"

DAY = 86400


def classify(payout, txn_sum, txn_count):
    """Sort one payout by whether its contents can be recovered. Pure, so the
    states can be tested without a network.

    `txn_sum` is the sum of `net` over the balance transactions listed against
    this payout, or None when they were not fetched. `txn_count` is how many
    there were. Only payouts with reconciliation_status "completed" can be
    listed against at all, so for the rest both arguments are meaningless.

    Returns (state, detail).
    """
    status = payout.get("reconciliation_status")
    automatic = payout.get("automatic")
    amount = payout.get("amount")

    if status == "completed":
        if txn_sum is None:
            return ("reconcilable",
                    "reconciliation_status completed: the breakdown exists, this "
                    "run did not fetch it")
        if not isinstance(amount, int):
            return ("unknown", "payout has no numeric amount: %r" % (amount,))
        if txn_sum != amount:
            return ("mismatch",
                    "%d balance transaction(s) sum to %d against a payout amount "
                    "of %d, %d apart: look for another currency, a reversal in the "
                    "window, or a page you stopped paginating"
                    % (txn_count, txn_sum, amount, abs(amount - txn_sum)))
        return ("reconciled",
                "%d balance transaction(s) sum to the payout" % txn_count)

    if status == "in_progress":
        return ("pending",
                "reconciliation_status in_progress: Stripe is still assembling the "
                "breakdown, which fills in after the payout settles")

    if status == "not_applicable":
        if automatic is False:
            return ("manual",
                    "manual payout: reconciliation_status not_applicable, so no "
                    "balance transaction will ever list against it. The itemized "
                    "report is the only route to its contents")
        return ("unsupported",
                "reconciliation_status not_applicable on an automatic payout: "
                "Stripe itemises standard automatic payouts only")

    return ("unknown", "unrecognised reconciliation_status: %r" % (status,))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def payout_transactions(session, payout_id, cap):
    """Sum `net` over the balance transactions Stripe attributes to a payout."""
    total = 0
    count = 0
    params = {"payout": payout_id, "limit": 100}
    while True:
        page = get(session, "/balance_transactions", **params)
        data = page.get("data", [])
        for bt in data:
            total += bt.get("net") or 0
            count += 1
        if not data or not page.get("has_more") or count >= cap:
            return total, count
        params["starting_after"] = data[-1]["id"]


def orphan_charges(session, since):
    """Count charges created without a transfer_group, one page deep.

    Not the finding itself, but the reason a reconstruction is guesswork even
    where Stripe does hand you the payout breakdown.
    """
    page = get(session, "/charges", limit=100, **{"created[gte]": since})
    data = page.get("data", [])
    return sum(1 for c in data if not c.get("transfer_group")), len(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90, help="window to look at")
    ap.add_argument("--no-sums", action="store_true",
                    help="skip the per-payout balance transaction sums")
    ap.add_argument("--transfer-groups", action="store_true",
                    help="also count recent charges with no transfer_group")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * DAY
    counts = {}
    scanned = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(s, "/payouts", **params)
        data = page.get("data", [])
        for payout in data:
            scanned += 1
            txn_sum = txn_count = None
            if payout.get("reconciliation_status") == "completed" and not args.no_sums:
                txn_sum, txn_count = payout_transactions(s, payout["id"], 10000)
            state, detail = classify(payout, txn_sum, txn_count)
            counts[state] = counts.get(state, 0) + 1
            line = "%s  %-13s %s" % (payout.get("id", "po_?"), state, detail)
            (log.info if state in ("reconciled", "reconcilable", "pending")
             else log.warning)(line)
        if not data or not page.get("has_more"):
            break
        params["starting_after"] = data[-1]["id"]

    manual = counts.get("manual", 0)
    mismatched = counts.get("mismatch", 0)
    unsupported = counts.get("unsupported", 0)
    log.info("%d payout(s): %d manual, %d mismatched, %d unsupported",
             scanned, manual, mismatched, unsupported)

    if args.transfer_groups:
        orphans, sampled = orphan_charges(s, since)
        log.info("%d of %d recent charge(s) have no transfer_group", orphans, sampled)

    if manual or unsupported:
        log.warning("  repair: move the account to an automatic schedule so future "
                    "payouts are itemised:")
        log.warning("  POST %s/accounts/{id} with "
                    "settings[payouts][schedule][interval]=daily", API)
        log.warning("  for history, run the itemized report: POST "
                    "%s/reporting/report_runs with "
                    "report_type=payout_reconciliation.by_id.itemized.1", API)
    if mismatched:
        log.warning("  repair: the breakdown exists but does not add up. Check for "
                    "a second currency and for transfers with amount_reversed > 0 "
                    "in the same window.")
    return 1 if (manual or mismatched or unsupported or counts.get("unknown")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-payout-reconciliation.mjs",
"js": '''/**
 * Report payouts that cannot be tied back to their balance transactions.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Payouts and Balance transactions. The repair is printed, never
 * performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;

/**
 * Sort one payout by whether its contents can be recovered. Pure, so the states
 * can be tested without a network. `txnSum` is null when the balance
 * transactions were not fetched. Returns [state, detail].
 */
export function classify(payout, txnSum, txnCount) {
  const status = payout.reconciliation_status;
  const automatic = payout.automatic;
  const amount = payout.amount;

  if (status === 'completed') {
    if (txnSum === null || txnSum === undefined) {
      return ['reconcilable',
        'reconciliation_status completed: the breakdown exists, this run did ' +
        'not fetch it'];
    }
    if (!Number.isInteger(amount)) {
      return ['unknown', `payout has no numeric amount: ${JSON.stringify(amount)}`];
    }
    if (txnSum !== amount) {
      return ['mismatch',
        `${txnCount} balance transaction(s) sum to ${txnSum} against a payout ` +
        `amount of ${amount}, ${Math.abs(amount - txnSum)} apart: look for ` +
        'another currency, a reversal in the window, or a page you stopped ' +
        'paginating'];
    }
    return ['reconciled', `${txnCount} balance transaction(s) sum to the payout`];
  }

  if (status === 'in_progress') {
    return ['pending',
      'reconciliation_status in_progress: Stripe is still assembling the ' +
      'breakdown, which fills in after the payout settles'];
  }

  if (status === 'not_applicable') {
    if (automatic === false) {
      return ['manual',
        'manual payout: reconciliation_status not_applicable, so no balance ' +
        'transaction will ever list against it. The itemized report is the only ' +
        'route to its contents'];
    }
    return ['unsupported',
      'reconciliation_status not_applicable on an automatic payout: Stripe ' +
      'itemises standard automatic payouts only'];
  }

  return ['unknown',
    `unrecognised reconciliation_status: ${JSON.stringify(status)}`];
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

export async function payoutTransactions(key, payoutId, cap = 10000) {
  let total = 0;
  let count = 0;
  const params = { payout: payoutId, limit: 100 };
  for (;;) {
    const page = await get(key, '/balance_transactions', params);
    const data = page.data ?? [];
    for (const bt of data) {
      total += bt.net ?? 0;
      count += 1;
    }
    if (data.length === 0 || !page.has_more || count >= cap) {
      return { total, count };
    }
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

  const days = Number(process.env.WINDOW_DAYS ?? 90);
  const since = Math.floor(Date.now() / 1000) - days * DAY;

  const counts = {};
  let scanned = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/payouts', params);
    const data = page.data ?? [];
    for (const payout of data) {
      scanned += 1;
      let txnSum = null;
      let txnCount = null;
      if (payout.reconciliation_status === 'completed') {
        const { total, count } = await payoutTransactions(key, payout.id);
        txnSum = total;
        txnCount = count;
      }
      const [state, detail] = classify(payout, txnSum, txnCount);
      counts[state] = (counts[state] ?? 0) + 1;
      const line = `${payout.id ?? 'po_?'}  ${state.padEnd(13)} ${detail}`;
      if (['reconciled', 'reconcilable', 'pending'].includes(state)) console.log(line);
      else console.warn(line);
    }
    if (data.length === 0 || !page.has_more) break;
    params.starting_after = data[data.length - 1].id;
  }

  const manual = counts.manual ?? 0;
  const mismatched = counts.mismatch ?? 0;
  const unsupported = counts.unsupported ?? 0;
  console.log(`${scanned} payout(s): ${manual} manual, ${mismatched} mismatched, ` +
              `${unsupported} unsupported`);

  if (manual || unsupported) {
    console.warn('  repair: move the account to an automatic schedule so future ' +
                 'payouts are itemised:');
    console.warn(`  POST ${API}/accounts/{id} with ` +
                 'settings[payouts][schedule][interval]=daily');
    console.warn(`  for history, run the itemized report: POST ` +
                 `${API}/reporting/report_runs with ` +
                 'report_type=payout_reconciliation.by_id.itemized.1');
  }
  if (mismatched) {
    console.warn('  repair: the breakdown exists but does not add up. Check for a ' +
                 'second currency and for transfers with amount_reversed > 0 in ' +
                 'the same window.');
  }
  if (manual || mismatched || unsupported || counts.unknown) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three of these tests exist to keep <code>not_applicable</code> from being one thing. On a manual payout it is a decision somebody made and can unmake; on an automatic one it means Stripe does not itemise that kind of payout at all. The fourth pins the arithmetic, because a breakdown that responds and does not add up is the failure most reconciliations are not looking for.",
"test_py_file": "test_stripe_payout_reconciliation.py",
"test_py": '''from stripe_payout_reconciliation import classify


def test_manual_payout_can_never_be_listed_against():
    state, detail = classify(
        {"id": "po_1", "amount": 500000, "automatic": False,
         "reconciliation_status": "not_applicable"}, None, None)
    assert state == "manual"
    assert "itemized report" in detail


def test_not_applicable_on_an_automatic_payout_is_different():
    # Same field value, different cause: nothing about the schedule will change
    # this one, because Stripe only itemises standard automatic payouts.
    state, _ = classify(
        {"id": "po_2", "amount": 500000, "automatic": True,
         "reconciliation_status": "not_applicable"}, None, None)
    assert state == "unsupported"


def test_completed_payout_whose_transactions_do_not_add_up():
    state, detail = classify(
        {"id": "po_3", "amount": 500000, "automatic": True,
         "reconciliation_status": "completed"}, 497500, 84)
    assert state == "mismatch"
    assert "2500 apart" in detail


def test_completed_and_balanced_is_the_healthy_case():
    state, _ = classify(
        {"id": "po_4", "amount": 500000, "automatic": True,
         "reconciliation_status": "completed"}, 500000, 84)
    assert state == "reconciled"


def test_in_progress_is_not_reported_as_broken():
    state, _ = classify(
        {"id": "po_5", "amount": 500000, "automatic": True,
         "reconciliation_status": "in_progress"}, None, None)
    assert state == "pending"
''',
"test_js_file": "stripe-payout-reconciliation.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-payout-reconciliation.mjs';

test('manual payout can never be listed against', () => {
  const [state, detail] = classify(
    { id: 'po_1', amount: 500000, automatic: false,
      reconciliation_status: 'not_applicable' }, null, null);
  assert.equal(state, 'manual');
  assert.match(detail, /itemized report/);
});

test('not_applicable on an automatic payout is different', () => {
  const [state] = classify(
    { id: 'po_2', amount: 500000, automatic: true,
      reconciliation_status: 'not_applicable' }, null, null);
  assert.equal(state, 'unsupported');
});

test('completed payout whose transactions do not add up', () => {
  const [state, detail] = classify(
    { id: 'po_3', amount: 500000, automatic: true,
      reconciliation_status: 'completed' }, 497500, 84);
  assert.equal(state, 'mismatch');
  assert.match(detail, /2500 apart/);
});

test('completed and balanced is the healthy case', () => {
  const [state] = classify(
    { id: 'po_4', amount: 500000, automatic: true,
      reconciliation_status: 'completed' }, 500000, 84);
  assert.equal(state, 'reconciled');
});

test('in_progress is not reported as broken', () => {
  const [state] = classify(
    { id: 'po_5', amount: 500000, automatic: true,
      reconciliation_status: 'in_progress' }, null, null);
  assert.equal(state, 'pending');
});
''',
"faq": [
 ("Why does balance_transactions?payout=po_x return an empty list?",
  "Because that payout's reconciliation_status is not completed. Stripe only assembles the list of balance transactions for standard automatic payouts, so a payout you created yourself has no breakdown to return and the filter matches nothing."),
 ("Does switching to an automatic schedule fix the payouts I already made?",
  "No. It changes the status of payouts made from that point on. History is only recoverable through the Reporting API, using payout_reconciliation.by_id.itemized.1 for a single payout or payout_reconciliation.itemized.7 over an interval."),
 ("What does in_progress mean, and how long does it last?",
  "Stripe is still assembling the breakdown. It resolves on its own after the payout settles, so an in_progress payout from this morning is not a finding. One that has been in_progress for days is worth a support ticket."),
 ("The transactions sum close to the payout but not exactly. What is missing?",
  "Usually one of three things: transactions in a second currency, a transfer reversal that landed inside the window, or pagination that stopped at the first page. Check amount_reversed on transfers in the same period before assuming the API is wrong."),
 ("What does transfer_group actually buy me?",
  "A join key you own. Charges and transfers sharing a transfer_group can be reassembled from your own data regardless of what the payout object reports, which is the only reconciliation route that does not depend on Stripe's payout mechanics."),
],
"related": [
 ("/stripe/payout-schedule-left-on-manual/", "A payout schedule left on manual strands the balance"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout sessions that cannot be reconciled to orders"),
 ("/stripe/stranded-currency-balance/", "A second-currency balance bucket can never be paid out"),
],
"citations": [CITE_PAYOUT_OBJ, CITE_PAYOUT_RECON, CITE_REPORTING_API,
              CITE_TRANSFER_OBJ],
},

]
