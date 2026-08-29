#!/usr/bin/env python3
"""/twilio/ field notes, batch P — the writing.

Four problems that are arithmetic rather than configuration: a balance that no
longer covers a busy day, a subaccount suspended without anybody being told, a
concurrency ceiling nobody has measured, and recordings billing for storage
because nothing deletes them.

None of the four raises an error in your code on the day it starts. Three of
them end in a 20005 or a 20429 that arrives during your busiest hour, and the
fourth ends on an invoice. All four are a number you can read today with a
read-only credential.

Read-only throughout. GET requests only, and every repair is printed for a human
to run rather than performed.
"""

CITE_RECORD = ("UsageRecord resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/api/usage-record")
CITE_TRIGGER = ("UsageTrigger resource — Twilio Docs",
                "https://www.twilio.com/docs/usage/api/usage-trigger")
CITE_ACCOUNT = ("Account resource — Twilio Docs",
                "https://www.twilio.com/docs/usage/api/account")
CITE_IAM_ACCOUNT = ("Account resource (IAM) — Twilio Docs",
                    "https://www.twilio.com/docs/iam/api/account")
CITE_SUBACCOUNTS = ("Subaccounts — Twilio Docs",
                    "https://www.twilio.com/docs/iam/api/subaccounts")
CITE_20005 = ("Error 20005: account not active — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/20005")
CITE_30002 = ("Error 30002: account suspended — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30002")
CITE_20429 = ("Error 20429: too many requests — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/20429")
CITE_BEST_PRACTICES = ("REST API best practices — Twilio Docs",
                       "https://www.twilio.com/docs/usage/rest-api-best-practices")
CITE_USAGE_API = ("Twilio REST API — Twilio Docs",
                  "https://www.twilio.com/docs/usage/api")
CITE_UNUSED = ("Manage unused resources — Twilio Docs",
               "https://www.twilio.com/docs/usage/manage-unused-resources")
CITE_RECORDING = ("Recording resource — Twilio Docs",
                  "https://www.twilio.com/docs/voice/api/recording")
CITE_ENCRYPTION = ("Voice recording encryption — Twilio Docs",
                   "https://www.twilio.com/docs/voice/tutorials/voice-recording-encryption")

GUIDES = [

{
"slug": "balance-below-safety-floor",
"title": "The balance is one busy hour from a 20005 suspension",
"description": "Twilio is prepay: at zero the account is suspended, not throttled. Compare Balance.json against your real daily burn and count the days of runway.",
"h1": "the balance is one busy hour from a 20005 suspension",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio balance api", "twilio 20005 account not active",
             "twilio auto recharge failed", "twilio balance.json",
             "twilio prepay account suspended"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The account had ninety dollars on it, which had been plenty for eight months. Then a product launch put four times the usual traffic through it in one evening, the balance crossed zero somewhere around nine o'clock, and every send after that came back <code>20005</code>. Nobody had done anything wrong. The number in <code>Balance.json</code> had simply stopped being large enough, and nothing in the system's job was to notice that.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/Balance.json</code> for <code>balance</code> and <code>currency</code>, then read <code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Daily.json?Category=totalprice</code> over the last month for <code>usage_records[].price</code>. Divide one by the other. That quotient is days of runway, and it is the number worth alerting on.</p>
<p>Twilio is prepay by default: when the balance reaches zero the account is <em>suspended</em>, not slowed. Compare the balance against the busiest day in the window as well as the median one, because the day that empties the account is never the median day.</p>""",
"problem": """<p>A balance is a stock and your traffic is a flow, and a healthy-looking stock tells you nothing on its own. Ninety dollars is six months of runway on an account that sends a hundred messages a day and forty minutes of runway on an account running a campaign. The console shows you the stock. Nothing in the console or the API divides it by the flow, which is the only form of the number that means anything.</p>
<p>The failure is also discontinuous, and that is what makes it expensive. Twilio does not throttle you down as the balance thins; the account runs at full speed until the balance is gone and then stops entirely, with <code>20005</code> on every REST call and <code>30002</code> on everything already queued. There is no degraded mode in between where somebody notices something is off. The first symptom is total outage, and it arrives during peak traffic by construction, because peak traffic is what consumed the balance.</p>""",
"why": """<p><strong>Auto Recharge fails silently, and its state is not readable.</strong> The card expires, the issuer declines an unusual amount, the billing email goes to a mailbox nobody has opened since the person who set it up left. There is no API field that says "auto recharge is enabled and last succeeded", so the only evidence you can gather through the API is the balance itself and the fact that it is not going back up.</p>
<p><strong>The account average is not the risk.</strong> Burn rate computed as a monthly total divided by thirty flatters every account with spiky traffic, which is most of them. A launch day, a end-of-month billing run or an OTP surge can cost five times a normal day, and the balance has to survive that day rather than the average one.</p>
<p><strong>Suspension cascades to subaccounts.</strong> The parent runs out and every tenant underneath it stops at the same instant, including the ones whose own usage was trivial. One balance is a shared single point of failure across every tenant you have.</p>
<p><strong>Reactivation is not instant.</strong> Adding funds clears the suspension after a delay measured in minutes, and anything that was queued has already failed with <code>30002</code> and will not be retried for you. The recovery is not just the payment, it is the replay of everything the outage dropped.</p>""",
"steps": [
 {"h": "Read the balance and the currency together",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Balance.json</code> returns <code>balance</code> as a string and <code>currency</code> beside it. Keep the currency: an account billed in EUR compared against a USD threshold somebody hardcoded is a check that reports the wrong answer with total confidence.</p>"""},
 {"h": "Get a real burn rate, not a monthly average",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Daily.json?Category=totalprice&amp;StartDate={30d ago}</code> gives one row per day with a <code>price</code> on it. <code>totalprice</code> is the category that captures spend wherever it happened, so a voice bill and a messaging bill both land in it.</p>"""},
 {"h": "Divide by the median day and check against the busiest one",
  "body": """<p>The median day is the honest denominator for runway, because a single quiet weekend does not deserve to double your estimate. The maximum day is the one that answers the question in the title: if the whole balance is smaller than one day you have already had, the account is one repeat of that day away from a suspension.</p>"""},
 {"h": "Pick a floor and treat crossing it as an incident",
  "body": """<p>Seven days is a reasonable floor: long enough that a failed card, a weekend and a purchasing process all fit inside it. The exact number matters less than having one, because a threshold you can compute is a threshold you can page on, and a balance you merely look at is not.</p>"""},
 {"h": "Fix the recharge, then set the alarm that catches the next one",
  "body": """<p>Console &rarr; Billing &rarr; Manage billing, enable Auto Recharge with a trigger amount of at least a week of spend and a card that is not about to expire. Then set the spend alarm, which is a different check with a different failure mode: <a href="/twilio/no-usage-trigger-configured/">no Usage Trigger, so overspend runs with nothing watching</a>.</p>"""},
],
"verify": """<p>Re-run the script. The state should be <code>ok</code> and the runway should be comfortably past your floor.</p>
<pre><code class="language-bash">python3 twilio_balance_runway.py --floor-days 7
# balance 412.80 USD over 30 day(s)
# ok             balance 412.80 against a median day of 9.44: 43.7 days of runway.</code></pre>""",
"code_intro": "Two GETs: the balance, and one page of daily usage records. A read-access API Key is enough and is what you should give it, because the credential this holds could otherwise spend the very balance it is measuring. The arithmetic &mdash; the median, the runway, and the comparison against the busiest day &mdash; is a pure function, since that is the part worth arguing about and the part worth testing.",
"py_file": "twilio_balance_runway.py",
"py": '''"""Report a Twilio balance that will not survive the next busy day.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_balance_runway")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

SPEND_CATEGORY = "totalprice"


def price_of(record):
    """One daily usage record as a float, or None when the field is unusable.

    price arrives as a string. A negative day is a credit or an adjustment
    rather than spend, and letting it through would drag the burn rate down and
    report runway the account does not have, so it is clamped at zero.
    """
    try:
        value = float(record.get("price"))
    except (TypeError, ValueError):
        return None
    return max(0.0, value)


def daily_prices(records):
    """The parseable daily prices out of a Usage/Records/Daily page. Pure."""
    return [p for p in (price_of(r) for r in records or []) if p is not None]


def median(values):
    """Median of a list of floats, 0.0 when empty.

    The median rather than the mean because one launch day in thirty should not
    be allowed to flatten into a burn rate that looks survivable.
    """
    ordered = sorted(values or [])
    n = len(ordered)
    if not n:
        return 0.0
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def runway_days(balance, rate):
    """Days the balance covers at a given daily rate, or None at a zero rate."""
    if not rate or rate <= 0:
        return None
    return balance / rate


def verdict(balance, prices, floor_days=7.0):
    """Classify a balance against the spend behind it. Pure, so the arithmetic
    that decides whether somebody gets paged is testable without a network.

    Returns (state, detail).
    """
    if balance is None:
        return ("unknown",
                "Balance.json returned no usable balance: with no number there is "
                "nothing to divide by a burn rate, and the check cannot answer.")

    values = list(prices or [])
    typical = median(values)
    peak = max(values) if values else 0.0

    if balance <= 0:
        return ("empty",
                "balance is %.2f: this is the state Twilio suspends on rather than "
                "throttles, so REST calls come back 20005 and anything already "
                "queued fails 30002." % balance)

    if typical <= 0:
        return ("idle",
                "balance %.2f and no priced usage in the window: there is no burn "
                "rate to divide by, so the floor has to come from the spend you "
                "expect rather than the spend you have had." % balance)

    days = balance / typical
    if days < 1.0:
        return ("critical",
                "balance %.2f against a median day of %.2f: under one ordinary day "
                "of runway left." % (balance, typical))
    if days < floor_days:
        return ("low",
                "balance %.2f against a median day of %.2f: %.1f days of runway, "
                "below the %.0f-day floor." % (balance, typical, days, floor_days))
    if balance < peak:
        return ("burst-exposed",
                "%.1f days of runway at the median day of %.2f, but the busiest day "
                "in the window cost %.2f, more than the entire balance: one repeat "
                "of that day ends in a suspension." % (days, typical, peak))
    return ("ok",
            "balance %.2f against a median day of %.2f: %.1f days of runway."
            % (balance, typical, days))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def read_balance(session, account):
    """Returns (balance as float or None, currency)."""
    page = get(session, "%s/Accounts/%s/Balance.json" % (BASE, account))
    try:
        return (float(page.get("balance")), page.get("currency") or "")
    except (TypeError, ValueError):
        return (None, page.get("currency") or "")


def read_daily(session, account, days):
    """One page of daily totalprice records covering the requested window."""
    start = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    page = get(session, "%s/Accounts/%s/Usage/Records/Daily.json" % (BASE, account),
               Category=SPEND_CATEGORY, StartDate=start, PageSize=100)
    return page.get("usage_records", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how many days of usage the burn rate is taken from")
    ap.add_argument("--floor-days", type=float, default=7.0,
                    help="days of runway below which the balance is a finding")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    balance, currency = read_balance(session, account)
    prices = daily_prices(read_daily(session, account, args.days))
    log.info("balance %s %s over %d day(s)",
             "unreadable" if balance is None else "%.2f" % balance,
             currency, args.days)

    state, detail = verdict(balance, prices, args.floor_days)
    if state == "ok":
        log.info("%-14s %s", state, detail)
        return 0

    log.warning("%-14s %s", state, detail)
    if prices:
        needed = median(prices) * args.floor_days
        log.warning("  %.0f days at the median day is %.2f %s: keep the recharge "
                    "trigger at or above that", args.floor_days, needed, currency)
    log.warning("  repair: Console > Billing > Manage billing > Auto Recharge, with "
                "a trigger amount of at least %.0f days of spend and a card that is "
                "not about to expire", args.floor_days)
    log.warning("  auto recharge state is not exposed by the API: the only evidence "
                "it is working is this balance going back up")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-balance-runway.mjs",
"js": '''/**
 * Report a Twilio balance that will not survive the next busy day.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const SPEND_CATEGORY = 'totalprice';

/**
 * One daily usage record as a number, or null when the field is unusable.
 * A negative day is a credit rather than spend and is clamped at zero, because
 * letting it through reports runway the account does not have.
 */
export function priceOf(record) {
  const value = Number.parseFloat(record?.price ?? '');
  if (!Number.isFinite(value)) return null;
  return Math.max(0, value);
}

/** The parseable daily prices out of a Usage/Records/Daily page. Pure. */
export function dailyPrices(records) {
  return (records ?? []).map(priceOf).filter((p) => p !== null);
}

/** Median of a list of numbers, 0 when empty. Pure. */
export function median(values) {
  const ordered = [...(values ?? [])].sort((a, b) => a - b);
  if (!ordered.length) return 0;
  const mid = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[mid] : (ordered[mid - 1] + ordered[mid]) / 2;
}

/** Days the balance covers at a given daily rate, or null at a zero rate. */
export function runwayDays(balance, rate) {
  if (!rate || rate <= 0) return null;
  return balance / rate;
}

/**
 * Classify a balance against the spend behind it. Pure, so the arithmetic that
 * decides whether somebody gets paged is testable without a network.
 * Returns [state, detail].
 */
export function verdict(balance, prices, floorDays = 7.0) {
  if (balance === null || balance === undefined || !Number.isFinite(balance)) {
    return ['unknown',
      'Balance.json returned no usable balance: with no number there is nothing ' +
      'to divide by a burn rate, and the check cannot answer.'];
  }

  const values = [...(prices ?? [])];
  const typical = median(values);
  const peak = values.length ? Math.max(...values) : 0;

  if (balance <= 0) {
    return ['empty',
      `balance is ${balance.toFixed(2)}: this is the state Twilio suspends on ` +
      'rather than throttles, so REST calls come back 20005 and anything already ' +
      'queued fails 30002.'];
  }

  if (typical <= 0) {
    return ['idle',
      `balance ${balance.toFixed(2)} and no priced usage in the window: there is ` +
      'no burn rate to divide by, so the floor has to come from the spend you ' +
      'expect rather than the spend you have had.'];
  }

  const days = balance / typical;
  if (days < 1) {
    return ['critical',
      `balance ${balance.toFixed(2)} against a median day of ${typical.toFixed(2)}: ` +
      'under one ordinary day of runway left.'];
  }
  if (days < floorDays) {
    return ['low',
      `balance ${balance.toFixed(2)} against a median day of ${typical.toFixed(2)}: ` +
      `${days.toFixed(1)} days of runway, below the ${floorDays.toFixed(0)}-day floor.`];
  }
  if (balance < peak) {
    return ['burst-exposed',
      `${days.toFixed(1)} days of runway at the median day of ${typical.toFixed(2)}, ` +
      `but the busiest day in the window cost ${peak.toFixed(2)}, more than the ` +
      'entire balance: one repeat of that day ends in a suspension.'];
  }
  return ['ok',
    `balance ${balance.toFixed(2)} against a median day of ${typical.toFixed(2)}: ` +
    `${days.toFixed(1)} days of runway.`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function readBalance(auth, account) {
  const page = await get(auth, `${BASE}/Accounts/${account}/Balance.json`);
  const value = Number.parseFloat(page.balance ?? '');
  return [Number.isFinite(value) ? value : null, page.currency ?? ''];
}

export async function readDaily(auth, account, days) {
  const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const page = await get(auth, `${BASE}/Accounts/${account}/Usage/Records/Daily.json`,
                         { Category: SPEND_CATEGORY, StartDate: start, PageSize: 100 });
  return page.usage_records ?? [];
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const arg = (name, fallback) => {
    const i = process.argv.indexOf(name);
    return i === -1 ? fallback : Number.parseFloat(process.argv[i + 1]);
  };
  const days = arg('--days', 30);
  const floorDays = arg('--floor-days', 7);

  const [balance, currency] = await readBalance(auth, account);
  const prices = dailyPrices(await readDaily(auth, account, days));
  console.log(`balance ${balance === null ? 'unreadable' : balance.toFixed(2)} ` +
              `${currency} over ${days} day(s)`);

  const [state, detail] = verdict(balance, prices, floorDays);
  if (state === 'ok') {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }
  console.warn(`${state.padEnd(14)} ${detail}`);
  if (prices.length) {
    const needed = median(prices) * floorDays;
    console.warn(`  ${floorDays.toFixed(0)} days at the median day is ` +
                 `${needed.toFixed(2)} ${currency}: keep the recharge trigger at ` +
                 'or above that');
  }
  console.warn('  repair: Console > Billing > Manage billing > Auto Recharge, with ' +
               `a trigger amount of at least ${floorDays.toFixed(0)} days of spend ` +
               'and a card that is not about to expire');
  console.warn('  auto recharge state is not exposed by the API: the only evidence ' +
               'it is working is this balance going back up');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases that matter are the ones where a healthy-looking balance is not healthy: a month of quiet days hiding one enormous one, a negative usage row that would otherwise flatter the burn rate, and an account with no spend at all, where dividing by zero is not an answer and saying so is. The rest pins the boundary either side of the floor.",
"test_py_file": "test_twilio_balance_runway.py",
"test_py": '''from twilio_balance_runway import (daily_prices, median, price_of, runway_days,
                                   verdict)


def test_median_of_an_even_run_is_the_middle_pair():
    assert median([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert median([3.0, 1.0, 2.0]) == 2.0
    assert median([]) == 0.0


def test_a_credit_day_is_clamped_rather_than_subtracted():
    assert price_of({"price": "-42.00"}) == 0.0
    assert price_of({"price": "12.50"}) == 12.5


def test_unparseable_prices_are_dropped_not_guessed():
    assert price_of({"price": None}) is None
    assert price_of({"price": "n/a"}) is None
    assert daily_prices([{"price": "4"}, {"price": "x"}, {}]) == [4.0]


def test_runway_is_undefined_at_a_zero_burn_rate():
    assert runway_days(100.0, 0.0) is None
    assert runway_days(100.0, 10.0) == 10.0


def test_a_missing_balance_is_reported_rather_than_assumed_healthy():
    state, _ = verdict(None, [{"price": "10"}])
    assert state == "unknown"


def test_a_zero_balance_is_already_the_suspension():
    state, detail = verdict(0.0, [10.0, 10.0])
    assert state == "empty"
    assert "20005" in detail


def test_an_account_with_no_spend_has_no_runway_to_compute():
    state, _ = verdict(500.0, [])
    assert state == "idle"


def test_under_one_median_day_is_critical():
    state, _ = verdict(5.0, [10.0, 10.0, 10.0])
    assert state == "critical"


def test_four_days_of_runway_is_below_a_seven_day_floor():
    state, detail = verdict(40.0, [10.0, 10.0, 10.0])
    assert state == "low"
    assert "4.0 days" in detail


def test_a_quiet_median_hides_a_day_bigger_than_the_whole_balance():
    state, detail = verdict(500.0, [1.0, 1.0, 900.0])
    assert state == "burst-exposed"
    assert "900.00" in detail


def test_a_balance_past_the_floor_and_past_the_busiest_day_is_fine():
    state, _ = verdict(10000.0, [10.0, 10.0, 12.0])
    assert state == "ok"
''',
"test_js_file": "twilio-balance-runway.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dailyPrices, median, priceOf, runwayDays, verdict }
  from './twilio-balance-runway.mjs';

test('median of an even run is the middle pair', () => {
  assert.equal(median([1, 2, 3, 4]), 2.5);
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([]), 0);
});

test('a credit day is clamped rather than subtracted', () => {
  assert.equal(priceOf({ price: '-42.00' }), 0);
  assert.equal(priceOf({ price: '12.50' }), 12.5);
});

test('unparseable prices are dropped, not guessed', () => {
  assert.equal(priceOf({ price: null }), null);
  assert.equal(priceOf({ price: 'n/a' }), null);
  assert.deepEqual(dailyPrices([{ price: '4' }, { price: 'x' }, {}]), [4]);
});

test('runway is undefined at a zero burn rate', () => {
  assert.equal(runwayDays(100, 0), null);
  assert.equal(runwayDays(100, 10), 10);
});

test('a missing balance is reported rather than assumed healthy', () => {
  assert.equal(verdict(null, [10])[0], 'unknown');
});

test('a zero balance is already the suspension', () => {
  const [state, detail] = verdict(0, [10, 10]);
  assert.equal(state, 'empty');
  assert.match(detail, /20005/);
});

test('an account with no spend has no runway to compute', () => {
  assert.equal(verdict(500, [])[0], 'idle');
});

test('under one median day is critical', () => {
  assert.equal(verdict(5, [10, 10, 10])[0], 'critical');
});

test('four days of runway is below a seven-day floor', () => {
  const [state, detail] = verdict(40, [10, 10, 10]);
  assert.equal(state, 'low');
  assert.match(detail, /4\\.0 days/);
});

test('a quiet median hides a day bigger than the whole balance', () => {
  const [state, detail] = verdict(500, [1, 1, 900]);
  assert.equal(state, 'burst-exposed');
  assert.match(detail, /900\\.00/);
});

test('a balance past the floor and past the busiest day is fine', () => {
  assert.equal(verdict(10000, [10, 10, 12])[0], 'ok');
});
''',
"faq": [
 ("Does Twilio not email me before the balance runs out?",
  "There are balance notification emails to the account owner, and they are a mailbox rather than a pager. They are also not something you can assert on: no API field tells you whether the notification is enabled, where it goes, or whether it was delivered. The balance and the daily usage records are readable, which is why the check is built on those two numbers and not on your inbox."),
 ("Why the median day rather than the average?",
  "Because the mean is dragged around by exactly the days you care about. One launch day at twenty times normal pushes the mean up, which makes the runway estimate look shorter than the account's ordinary behaviour warrants, and a fortnight of quiet weekends pushes it down. The median describes an ordinary day, and the maximum, checked separately, describes the day that will actually empty the account."),
 ("What should the floor be?",
  "Seven days is a defensible starting point because it spans a weekend, a declined card and a purchase approval. If your recharge is automatic and reliable, three days is fine; if funding the account involves a finance team and a purchase order, fourteen is not paranoid. The value of the floor is that it is a number the script can compare against, not that it is the right number."),
 ("Will adding funds bring the account straight back?",
  "The suspension clears a few minutes after the payment, but that is not the whole recovery. Everything that was queued during the outage has already failed with 30002, and Twilio does not replay it. Whatever your application does about undelivered messages has to run afterwards, so the outage is longer than the suspension was."),
 ("Should this run per subaccount?",
  "Read the balance on the parent, because that is where the money is: subaccounts bill up to the parent rather than holding their own balance. What is worth running per subaccount is the status check, since a parent suspension cascades and one tenant can also be suspended on its own. That is covered separately in the subaccount note."),
],
"related": [
 ("/twilio/no-usage-trigger-configured/", "The spend alarm that would have caught the burn"),
 ("/twilio/subaccount-suspended-silently/", "One tenant suspended while the parent looks healthy"),
 ("/twilio/idle-phone-numbers-billed/", "Numbers billed every month for carrying nothing"),
],
"citations": [CITE_ACCOUNT, CITE_RECORD, CITE_20005, CITE_TRIGGER],
},

{
"slug": "subaccount-suspended-silently",
"title": "A suspended subaccount, so one tenant's traffic 20005s",
"description": "Twilio notifies nobody when a subaccount is suspended. List Accounts.json by status with parent credentials and find the tenant that quietly stopped.",
"h1": "a suspended subaccount, so one tenant's traffic 20005s",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio subaccount suspended", "twilio 20005 subaccount",
             "twilio accounts.json status", "twilio subaccount closed",
             "twilio multi tenant messaging"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One customer opens a ticket saying none of their messages have gone out since Thursday. Every other customer is fine. The parent account dashboard is green, the balance is healthy, the Debugger is quiet, and the only thing wrong is a three-letter field on a resource nobody on the team has read since the tenant was provisioned: that subaccount's <code>status</code> is <code>suspended</code>, and Twilio told nobody.",
"short_answer": """<p>With parent credentials, read <code>GET /2010-04-01/Accounts.json?Status=suspended</code> and then <code>GET /2010-04-01/Accounts.json?Status=closed</code>. Any row whose <code>owner_account_sid</code> is your parent SID is one of your tenants, and it is not sending anything.</p>
<p>Reactivating is a write on the subaccount with parent credentials, so this script prints it rather than doing it. <code>closed</code> is terminal &mdash; there is no path back from it, which is why the two statuses are reported separately instead of as one count of "not active".</p>""",
"problem": """<p>Multi-tenant Twilio integrations put each customer in a subaccount, which is the right shape: separate SIDs, separate usage records, separate numbers. What the shape does not give you is a single place that says whether every tenant can still send. Your application authenticates as the parent, or with an API key on the parent, and every health check you wrote asks the parent how it is doing. The parent is fine. The parent is always fine.</p>
<p>Meanwhile the suspended tenant fails uniformly and quietly. Their REST calls come back <code>20005</code>, their queued messages fail <code>30002</code>, and because their traffic is a small slice of the account total, no aggregate graph moves enough to notice. The finding arrives through support, days late, from the customer &mdash; which is the most expensive possible route for a fact that one paginated GET could have delivered every morning.</p>""",
"why": """<p><strong>Nothing notifies you.</strong> A subaccount suspended through the API or by an internal process generates no email, no Debugger alert and no webhook. The status field changes and the API starts refusing that SID's traffic. Reading the field is the entire detection surface.</p>
<p><strong>Suspension cascades downward, and only downward.</strong> If the parent is suspended every subaccount stops with it. If a subaccount is suspended the parent carries on undisturbed, which is exactly the direction that makes the parent a useless place to watch from.</p>
<p><strong>Teams suspend tenants deliberately and then forget.</strong> Suspending a subaccount is a reasonable response to a non-paying customer or an abuse investigation. It becomes a bug the moment the customer pays, the ticket closes, and nobody flips the status back &mdash; and there is no expiry, so it stays suspended forever.</p>
<p><strong>Closed is not a worse kind of suspended, it is permanent.</strong> A closed subaccount cannot be reopened. Its numbers are released. Reporting the two states as one number invites somebody to treat a closure as a thing they can undo on Monday.</p>""",
"steps": [
 {"h": "List by status rather than listing everything",
  "body": """<p><code>GET /2010-04-01/Accounts.json?Status=suspended&amp;PageSize=50</code>, following <code>next_page_uri</code>, is a much cheaper question than paging every account on a large parent. Repeat it for <code>Status=closed</code>. On a parent with a handful of tenants, listing all of them is fine too and gives you a denominator.</p>"""},
 {"h": "Confirm ownership with owner_account_sid",
  "body": """<p>Each row carries <code>sid</code>, <code>friendly_name</code>, <code>status</code>, <code>type</code> and <code>owner_account_sid</code>. The parent's own row appears in the list with <code>owner_account_sid</code> equal to its own <code>sid</code>; a genuine tenant is a row where the two differ and the owner is your parent. Keying on that field rather than on position keeps the check honest when credentials get swapped around.</p>"""},
 {"h": "Keep suspended and closed apart",
  "body": """<p>Suspended is recoverable by one write with parent credentials. Closed is not recoverable at all: the subaccount is gone, its numbers have been released, and the tenant needs a new subaccount and new numbers. These are different incidents with different response times and they should never be summed into a single count.</p>"""},
 {"h": "Cross-check against the tenant's traffic",
  "body": """<p><code>GET /2010-04-01/Accounts/{SubAccountSid}/Messages.json?PageSize=1</code> with the sub SID in the path tells you when that tenant last sent anything. A suspension dated to the last message is the confirmation, and it also gives support the exact window of dropped traffic to talk to the customer about.</p>"""},
 {"h": "Print the reactivation, run the audit on a schedule",
  "body": """<p>The repair is a POST to <code>/2010-04-01/Accounts/{SubAccountSid}.json</code> with <code>Status=active</code>, authenticated as the parent. This script prints that and stops. Then run it every morning: the check is two GETs, and the whole point is that this failure has no other way to reach you.</p>"""},
],
"verify": """<p>Re-run the script. Every tenant should classify as <code>active</code> and the roll-up should be <code>clean</code>.</p>
<pre><code class="language-bash">python3 twilio_subaccount_status_audit.py --all
# ACxxxxxxxx  Acme Corp (prod)                active
# ACyyyyyyyy  Northwind (prod)                active
# clean          14 subaccount(s), all active.</code></pre>""",
"code_intro": "Two GETs by default, one per status, or a single paginated listing with <code>--all</code> so the report has a denominator. A read-access API Key on the parent is enough. The classifier is pure and takes one account row plus the parent SID, because the interesting judgements &mdash; the parent's own row is not a finding, a row owned by somebody else is a different finding, closed is not suspended &mdash; are all decisions about fields rather than about HTTP.",
"py_file": "twilio_subaccount_status_audit.py",
"py": '''"""Report Twilio subaccounts that are suspended or closed under this parent.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_subaccount_status_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

STATUSES = ("suspended", "closed")


def verdict(account, parent_sid):
    """Classify one row from Accounts.json against the parent it should belong
    to. Pure, so the ownership and status rules can be tested without a network.

    Returns (state, detail).
    """
    sid = str(account.get("sid") or "").strip()
    owner = str(account.get("owner_account_sid") or "").strip()
    status = str(account.get("status") or "").strip().lower()
    kind = str(account.get("type") or "").strip().lower()
    name = str(account.get("friendly_name") or "").strip() or "(no friendly name)"

    if sid and sid == parent_sid:
        return ("parent",
                "%s is the parent account itself, not a tenant: its own row always "
                "lists it as its owner." % name)

    if owner and parent_sid and owner != parent_sid:
        return ("foreign",
                "%s is owned by %s rather than by this parent: the credential in "
                "use is not the one that can change it." % (name, owner))

    if status == "suspended":
        return ("suspended",
                "%s is suspended: every REST call on that SID returns 20005 and "
                "anything queued fails 30002, and nothing was sent to tell you."
                % name)

    if status == "closed":
        return ("closed",
                "%s is closed, which is terminal: the subaccount cannot be "
                "reopened and its numbers have been released." % name)

    if kind == "trial":
        return ("trial",
                "%s is active but still of type Trial: sends are restricted to "
                "verified numbers and carry the trial prefix." % name)

    if status == "active":
        return ("active", "%s is active." % name)

    return ("unknown",
            "%s has status %r, which is not one of active, suspended or closed."
            % (name, status or ""))


def summary(states):
    """Roll a run of per-account states into one answer. Pure.

    Suspended outranks closed in the report only because it is the one you can
    still do something about this morning; both are printed either way.
    """
    states = list(states or [])
    tenants = [s for s in states if s != "parent"]
    suspended = states.count("suspended")
    closed = states.count("closed")

    if suspended:
        return ("suspended",
                "%d suspended subaccount(s): that tenant's traffic is failing now "
                "and can be restored with one write." % suspended)
    if closed:
        return ("closed",
                "%d closed subaccount(s) and none suspended: closures are "
                "permanent, so this is a record rather than a repair." % closed)
    if not tenants:
        return ("single",
                "no subaccounts under this parent: there is nothing here to "
                "suspend, and this check has nothing to watch.")
    return ("clean", "%d subaccount(s), all active." % len(tenants))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_accounts(session, status=None, limit=500):
    """Page Accounts.json. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts.json" % BASE
    params = {"PageSize": 50}
    if status:
        params["Status"] = status
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("accounts", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def last_message(session, account_sid):
    """When this tenant last sent anything, or None. One GET, one row."""
    page = get(session, "%s/Accounts/%s/Messages.json" % (BASE, account_sid),
               PageSize=1)
    rows = page.get("messages", [])
    return rows[0].get("date_sent") if rows else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true",
                    help="list every subaccount rather than only the stopped ones")
    ap.add_argument("--check-traffic", action="store_true",
                    help="for each finding, read when that tenant last sent")
    args = ap.parse_args()

    parent = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (parent and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access on the parent, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    if args.all:
        rows = list_accounts(session)
    else:
        rows = []
        for status in STATUSES:
            rows.extend(list_accounts(session, status=status))

    states = []
    findings = []
    for row in rows:
        state, detail = verdict(row, parent)
        states.append(state)
        line = "%-34s %s" % (row.get("sid", "?"), state)
        if state in ("suspended", "closed", "foreign", "unknown"):
            findings.append((row, state, detail))
            log.warning("%s  %s", line, detail)
        else:
            log.info("%s", line)

    state, detail = summary(states)
    if state in ("clean", "single"):
        log.info("%-14s %s", state, detail)
        return 0

    log.warning("%-14s %s", state, detail)
    for row, kind, _ in findings:
        sid = row.get("sid", "{SubAccountSid}")
        if args.check_traffic:
            log.warning("  %s last sent: %s", sid, last_message(session, sid) or "never")
        if kind == "suspended":
            log.warning("  repair: POST %s/Accounts/%s.json Status=active, "
                        "authenticated as the parent account", BASE, sid)
        elif kind == "closed":
            log.warning("  %s is closed and cannot be reopened: provision a new "
                        "subaccount and new numbers for that tenant", sid)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-subaccount-status-audit.mjs",
"js": '''/**
 * Report Twilio subaccounts that are suspended or closed under this parent.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const STATUSES = ['suspended', 'closed'];

/**
 * Classify one row from Accounts.json against the parent it should belong to.
 * Pure, so the ownership and status rules can be tested without a network.
 * Returns [state, detail].
 */
export function verdict(account, parentSid) {
  const sid = String(account?.sid ?? '').trim();
  const owner = String(account?.owner_account_sid ?? '').trim();
  const status = String(account?.status ?? '').trim().toLowerCase();
  const kind = String(account?.type ?? '').trim().toLowerCase();
  const name = String(account?.friendly_name ?? '').trim() || '(no friendly name)';

  if (sid && sid === parentSid) {
    return ['parent',
      `${name} is the parent account itself, not a tenant: its own row always ` +
      'lists it as its owner.'];
  }

  if (owner && parentSid && owner !== parentSid) {
    return ['foreign',
      `${name} is owned by ${owner} rather than by this parent: the credential ` +
      'in use is not the one that can change it.'];
  }

  if (status === 'suspended') {
    return ['suspended',
      `${name} is suspended: every REST call on that SID returns 20005 and ` +
      'anything queued fails 30002, and nothing was sent to tell you.'];
  }

  if (status === 'closed') {
    return ['closed',
      `${name} is closed, which is terminal: the subaccount cannot be reopened ` +
      'and its numbers have been released.'];
  }

  if (kind === 'trial') {
    return ['trial',
      `${name} is active but still of type Trial: sends are restricted to ` +
      'verified numbers and carry the trial prefix.'];
  }

  if (status === 'active') return ['active', `${name} is active.`];

  return ['unknown',
    `${name} has status "${status}", which is not one of active, suspended or closed.`];
}

/** Roll a run of per-account states into one answer. Pure. */
export function summary(states) {
  const all = [...(states ?? [])];
  const tenants = all.filter((s) => s !== 'parent');
  const suspended = all.filter((s) => s === 'suspended').length;
  const closed = all.filter((s) => s === 'closed').length;

  if (suspended) {
    return ['suspended',
      `${suspended} suspended subaccount(s): that tenant's traffic is failing now ` +
      'and can be restored with one write.'];
  }
  if (closed) {
    return ['closed',
      `${closed} closed subaccount(s) and none suspended: closures are permanent, ` +
      'so this is a record rather than a repair.'];
  }
  if (!tenants.length) {
    return ['single',
      'no subaccounts under this parent: there is nothing here to suspend, and ' +
      'this check has nothing to watch.'];
  }
  return ['clean', `${tenants.length} subaccount(s), all active.`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listAccounts(auth, status = null, limit = 500) {
  let url = `${BASE}/Accounts.json`;
  let params = status ? { PageSize: 50, Status: status } : { PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.accounts ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function lastMessage(auth, accountSid) {
  const page = await get(auth, `${BASE}/Accounts/${accountSid}/Messages.json`,
                         { PageSize: 1 });
  const rows = page.messages ?? [];
  return rows.length ? rows[0].date_sent : null;
}

async function main() {
  const parent = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!parent || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access on the parent, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);
  const listAll = process.argv.includes('--all');
  const checkTraffic = process.argv.includes('--check-traffic');

  let rows = [];
  if (listAll) {
    rows = await listAccounts(auth);
  } else {
    for (const status of STATUSES) rows.push(...await listAccounts(auth, status));
  }

  const states = [];
  const findings = [];
  for (const row of rows) {
    const [state, detail] = verdict(row, parent);
    states.push(state);
    const line = `${String(row.sid ?? '?').padEnd(34)} ${state}`;
    if (['suspended', 'closed', 'foreign', 'unknown'].includes(state)) {
      findings.push([row, state]);
      console.warn(`${line}  ${detail}`);
    } else {
      console.log(line);
    }
  }

  const [state, detail] = summary(states);
  if (state === 'clean' || state === 'single') {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }
  console.warn(`${state.padEnd(14)} ${detail}`);
  for (const [row, kind] of findings) {
    const sid = row.sid ?? '{SubAccountSid}';
    if (checkTraffic) {
      console.warn(`  ${sid} last sent: ${await lastMessage(auth, sid) ?? 'never'}`);
    }
    if (kind === 'suspended') {
      console.warn(`  repair: POST ${BASE}/Accounts/${sid}.json Status=active, ` +
                   'authenticated as the parent account');
    } else if (kind === 'closed') {
      console.warn(`  ${sid} is closed and cannot be reopened: provision a new ` +
                   'subaccount and new numbers for that tenant');
    }
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three of these cases are the ones that turn a useful report into a misleading one: the parent's own row, which lists itself as its owner and is not a finding; a row belonging to a different parent, which this credential cannot fix; and a closed subaccount, which must never be counted alongside a suspended one because only one of the two can be undone.",
"test_py_file": "test_twilio_subaccount_status_audit.py",
"test_py": '''from twilio_subaccount_status_audit import summary, verdict

PARENT = "ACparent0000000000000000000000000"


def make(**kw):
    row = {"sid": "ACtenant000000000000000000000001",
           "owner_account_sid": PARENT,
           "friendly_name": "Acme Corp (prod)",
           "status": "active",
           "type": "Full"}
    row.update(kw)
    return row


def test_the_parents_own_row_is_not_a_tenant():
    state, detail = verdict(make(sid=PARENT, owner_account_sid=PARENT), PARENT)
    assert state == "parent"
    assert "owner" in detail


def test_a_suspended_tenant_is_the_finding():
    state, detail = verdict(make(status="suspended"), PARENT)
    assert state == "suspended"
    assert "20005" in detail


def test_a_closed_tenant_is_reported_as_terminal():
    state, detail = verdict(make(status="closed"), PARENT)
    assert state == "closed"
    assert "cannot be reopened" in detail


def test_a_row_owned_by_another_parent_is_not_ours_to_fix():
    state, _ = verdict(make(owner_account_sid="ACsomeoneelse"), PARENT)
    assert state == "foreign"


def test_an_active_trial_subaccount_is_still_worth_saying():
    state, _ = verdict(make(type="Trial"), PARENT)
    assert state == "trial"


def test_status_casing_from_the_api_does_not_change_the_answer():
    assert verdict(make(status="SUSPENDED"), PARENT)[0] == "suspended"


def test_an_unrecognised_status_is_not_quietly_called_active():
    state, _ = verdict(make(status="pending"), PARENT)
    assert state == "unknown"


def test_summary_reports_the_recoverable_failure_first():
    state, detail = summary(["parent", "active", "suspended", "closed"])
    assert state == "suspended"
    assert "one write" in detail


def test_summary_keeps_closures_separate_from_suspensions():
    state, detail = summary(["parent", "active", "closed"])
    assert state == "closed"
    assert "permanent" in detail


def test_a_parent_with_no_subaccounts_has_nothing_to_watch():
    assert summary(["parent"])[0] == "single"


def test_all_active_tenants_are_clean():
    state, detail = summary(["parent", "active", "active", "trial"])
    assert state == "clean"
    assert "3 subaccount(s)" in detail
''',
"test_js_file": "twilio-subaccount-status-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { summary, verdict } from './twilio-subaccount-status-audit.mjs';

const PARENT = 'ACparent0000000000000000000000000';

const make = (over = {}) => ({
  sid: 'ACtenant000000000000000000000001',
  owner_account_sid: PARENT,
  friendly_name: 'Acme Corp (prod)',
  status: 'active',
  type: 'Full',
  ...over,
});

test("the parent's own row is not a tenant", () => {
  const [state, detail] = verdict(
    make({ sid: PARENT, owner_account_sid: PARENT }), PARENT);
  assert.equal(state, 'parent');
  assert.match(detail, /owner/);
});

test('a suspended tenant is the finding', () => {
  const [state, detail] = verdict(make({ status: 'suspended' }), PARENT);
  assert.equal(state, 'suspended');
  assert.match(detail, /20005/);
});

test('a closed tenant is reported as terminal', () => {
  const [state, detail] = verdict(make({ status: 'closed' }), PARENT);
  assert.equal(state, 'closed');
  assert.match(detail, /cannot be reopened/);
});

test('a row owned by another parent is not ours to fix', () => {
  assert.equal(verdict(make({ owner_account_sid: 'ACsomeoneelse' }), PARENT)[0],
               'foreign');
});

test('an active trial subaccount is still worth saying', () => {
  assert.equal(verdict(make({ type: 'Trial' }), PARENT)[0], 'trial');
});

test('status casing from the API does not change the answer', () => {
  assert.equal(verdict(make({ status: 'SUSPENDED' }), PARENT)[0], 'suspended');
});

test('an unrecognised status is not quietly called active', () => {
  assert.equal(verdict(make({ status: 'pending' }), PARENT)[0], 'unknown');
});

test('summary reports the recoverable failure first', () => {
  const [state, detail] = summary(['parent', 'active', 'suspended', 'closed']);
  assert.equal(state, 'suspended');
  assert.match(detail, /one write/);
});

test('summary keeps closures separate from suspensions', () => {
  const [state, detail] = summary(['parent', 'active', 'closed']);
  assert.equal(state, 'closed');
  assert.match(detail, /permanent/);
});

test('a parent with no subaccounts has nothing to watch', () => {
  assert.equal(summary(['parent'])[0], 'single');
});

test('all active tenants are clean', () => {
  const [state, detail] = summary(['parent', 'active', 'active', 'trial']);
  assert.equal(state, 'clean');
  assert.match(detail, /3 subaccount\\(s\\)/);
});
''',
"faq": [
 ("Who suspends a subaccount, if nobody on my team did?",
  "Three routes. Somebody on your side called the API or used the console, usually during a billing or abuse process. The parent account was suspended, which cascades to every subaccount underneath it. Or Twilio acted on the account for policy or payment reasons. The status field does not record which, so the audit tells you a tenant is stopped and your billing and abuse history tells you why."),
 ("Can I reactivate it from this script?",
  "No, and deliberately so. Every script in this section holds a credential to an account that can send messages and spend money, so none of them writes. Reactivation is one POST to the subaccount with parent credentials and Status=active; the script prints exactly that line so a human can run it after deciding the suspension should not have happened."),
 ("Is a closed subaccount really unrecoverable?",
  "Yes. Closing is permanent, the numbers attached to it are released back to the pool, and there is no reopen. If a tenant's subaccount is closed, that tenant needs a new subaccount and new numbers, and any A2P registration or toll-free verification attached to the old numbers has to be done again. That is why the report never merges the two states."),
 ("Should I run this with the parent auth token instead?",
  "No. An API Key created on the parent with read access lists subaccounts perfectly well, and it is the credential that cannot do damage if the audit host is compromised. If you have no keys at all, the auth token is doing this work everywhere, which is its own finding, covered in the API key note."),
 ("How often should it run?",
  "Daily is enough for most, and hourly is cheap: it is two GETs on a small collection. The value is bounded by how long you are willing for a tenant to be down before you hear it from them, so pick an interval shorter than your support response time and let it run."),
],
"related": [
 ("/twilio/balance-below-safety-floor/", "The parent balance whose exhaustion cascades to every tenant"),
 ("/twilio/outbound-messaging-disabled-30037/", "A subaccount that cannot send even while active"),
 ("/twilio/no-usage-trigger-configured/", "Spend alarms, which every subaccount needs its own of"),
],
"citations": [CITE_SUBACCOUNTS, CITE_IAM_ACCOUNT, CITE_20005, CITE_30002],
},

{
"slug": "rest-api-concurrency-exhausted",
"title": "REST concurrency exhausted, so bursts come back 20429",
"description": "Twilio caps concurrent REST requests per account and the ceiling is in no response body. Sample Twilio-Concurrent-Requests at peak, before it bites.",
"h1": "REST concurrency exhausted, so bursts come back 20429",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 20429", "twilio concurrency limit",
             "twilio-concurrent-requests header", "twilio 429 too many requests",
             "twilio rest api rate limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The fan-out worked in staging with fifty recipients and fell over in production with fifty thousand. Not slowly: a wall of HTTP 429s with <code>20429</code> in the body, all at once, from a client that was doing nothing wrong except doing it all at the same moment. Retrying fixed it, which is exactly why the underlying number went unmeasured for another six months.",
"short_answer": """<p>Twilio limits how many REST requests an account can have <em>in flight</em> at once. Issue any cheap read &mdash; <code>GET /2010-04-01/Accounts/{AccountSid}.json</code> will do &mdash; and read the <code>Twilio-Concurrent-Requests</code> response header, which reports the account's current concurrency at the moment your request was served.</p>
<p>Sample it repeatedly during peak rather than once at midnight. A value that sits near your ceiling is the warning; an observed <code>20429</code> is the confirmation. The ceiling itself is not in any response field, so the script takes it as an argument and refuses to invent one.</p>""",
"problem": """<p>Concurrency is not requests per second, and conflating the two is why this surprises people. A hundred requests a second that each return in 50 ms is five in flight. A hundred a second that each take two seconds &mdash; because a downstream carrier is slow, or because you are creating messages rather than reading them &mdash; is two hundred in flight, from a client whose request rate never changed. The thing that breaches the limit is often Twilio's own latency rising, not your traffic.</p>
<p>The failure mode compounds itself. When responses slow down, in-flight requests pile up; when the account hits the ceiling, Twilio starts returning <code>20429</code>, and a naive client retries immediately, adding load to a system already at its limit. Every rejected request still occupied a slot to be rejected. Without backoff, the client's own retry storm is what keeps the account pinned there long after the original slow patch has cleared.</p>""",
"why": """<p><strong>Nothing in the response body mentions the limit.</strong> The concurrency figure arrives in a header, and the ceiling it should be compared against is not published per account through the API at all. That is why this check samples an observable and asks you for the threshold, instead of pretending to read a limit that does not exist as a field.</p>
<p><strong>Serverless multiplies concurrency by design.</strong> A queue consumer that scales to two hundred parallel invocations, each holding one Twilio request open, is two hundred concurrent requests by construction. The limit lives on the account; your scaling policy does not know that, and there is no shared counter between invocations to enforce it.</p>
<p><strong>Subaccount concurrency does not roll up.</strong> Requests made against a subaccount SID count against that subaccount, so splitting a large tenant into its own subaccount genuinely gives it its own budget. This is the one architectural lever here, and it is worth knowing before you need it.</p>
<p><strong>Retrying a 20429 is safe, and that is not permission to retry immediately.</strong> The request was rejected before it was processed, so nothing was half-created &mdash; but retries without exponential backoff and jitter reconverge on the same instant and reproduce the burst that caused the problem.</p>""",
"steps": [
 {"h": "Pick a read that costs nothing and sample it",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code> is a single small resource. The header is attached to the response regardless of which endpoint produced it, so there is no reason to sample with an expensive call.</p>"""},
 {"h": "Sample during peak, and sample repeatedly",
  "body": """<p>One reading is a single instant of a quantity that moves constantly. A dozen samples spread across the busiest ten minutes of your day describes the shape of it; a reading at three in the morning describes an idle account and reassures you about nothing.</p>"""},
 {"h": "Remember the probe counts itself",
  "body": """<p>The request that carries the header is itself in flight when the number is computed, so a completely quiet account reads 1 rather than 0. It also means a probe running in a tight loop is contributing to the very figure it reports, which is why the sampling interval here is seconds rather than milliseconds.</p>"""},
 {"h": "Compare against your actual ceiling, not a guess",
  "body": """<p>The limit is an account property Twilio support can tell you, and it is not exposed as a readable field. Pass it in with <code>--limit</code>. Without it the script still reports the observed peak, but it labels the state <code>unmeasured</code>, because a number with no threshold beside it is not a finding.</p>"""},
 {"h": "Cap the client, then shard if capping is not enough",
  "body": """<p>There is no console setting to fix. Bound your own concurrency below the ceiling with a semaphore or a worker pool, retry <code>20429</code> with exponential backoff and jitter, and if one tenant genuinely needs more headroom than the account has, move that tenant into its own subaccount so its budget is separate. Check first that the subaccount is not itself stopped: <a href="/twilio/subaccount-suspended-silently/">a suspended subaccount fails the same way for entirely different reasons</a>.</p>"""},
],
"verify": """<p>Re-run the probe during your busiest window with the ceiling your account actually has. The peak should sit under the warning ratio.</p>
<pre><code class="language-bash">python3 twilio_concurrency_probe.py --samples 12 --interval 5 --limit 100
# 12 sample(s), peak 34, no 20429 observed
# headroom       peak concurrency 34 of a 100 ceiling (34%).</code></pre>""",
"code_intro": "The probe issues one cheap GET per sample and reads a response header off each. It counts a <code>429</code> as data rather than as an error, because observing one is the strongest confirmation available. The classifier is pure and takes the samples, the ceiling and whether a 429 was seen, so the rules about what counts as near the limit can be argued with in a test rather than in production.",
"py_file": "twilio_concurrency_probe.py",
"py": '''"""Sample Twilio's REST concurrency header and report how close to the ceiling.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_concurrency_probe")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

HEADER = "Twilio-Concurrent-Requests"


def concurrency_of(headers):
    """The concurrency figure out of a response's headers, or None.

    Pure, and case-insensitive by hand: requests hands back a case-insensitive
    mapping, a plain dict in a test does not, and the difference should not
    decide whether the check works.
    """
    for name, value in (headers or {}).items():
        if str(name).lower() != HEADER.lower():
            continue
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None
    return None


def verdict(samples, limit=None, saw_429=False, warn_ratio=0.7):
    """Classify a run of concurrency samples. Pure, so the thresholds are
    testable without waiting for a real peak.

    samples: the per-request readings, with None for a response that carried no
    header. Returns (state, detail).
    """
    readings = [s for s in (samples or []) if s is not None]

    if saw_429:
        peak = max(readings) if readings else 0
        return ("throttled",
                "a 429 came back during the sample itself, at a peak concurrency "
                "of %d: the account is at its ceiling right now, and every "
                "rejected request still took a slot to be rejected." % peak)

    if not readings:
        return ("no-header",
                "no %s header on any of the %d sample(s): with nothing to read, "
                "this check cannot say anything about concurrency."
                % (HEADER, len(samples or [])))

    peak = max(readings)
    if limit is None:
        return ("unmeasured",
                "peak concurrency %d over %d sample(s), and no ceiling to compare "
                "it against: the limit is not a readable field, so pass the one "
                "your account has with --limit." % (peak, len(readings)))

    ratio = peak / float(limit)
    if ratio >= 1.0:
        return ("at-limit",
                "peak concurrency %d against a %d ceiling: requests are being "
                "refused with 20429 at the top of every burst." % (peak, limit))
    if ratio >= warn_ratio:
        return ("near-limit",
                "peak concurrency %d of a %d ceiling (%.0f%%): one slow patch "
                "downstream lengthens every in-flight request and closes that "
                "gap without your traffic changing at all."
                % (peak, limit, ratio * 100))
    return ("headroom",
            "peak concurrency %d of a %d ceiling (%.0f%%)."
            % (peak, limit, ratio * 100))


def probe(session, account, samples, interval):
    """Take n samples of the concurrency header. Returns (readings, saw_429)."""
    readings = []
    saw_429 = False
    url = "%s/Accounts/%s.json" % (BASE, account)
    for i in range(samples):
        r = session.get(url, timeout=30)
        if r.status_code in (401, 403):
            raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that "
                             "the API key belongs to that account with read access"
                             % r.status_code)
        if r.status_code == 429:
            saw_429 = True
        value = concurrency_of(r.headers)
        readings.append(value)
        log.info("  sample %2d: %s", i + 1,
                 "no header" if value is None else "%d in flight" % value)
        if i + 1 < samples:
            time.sleep(interval)
    return readings, saw_429


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=int, default=12,
                    help="how many readings to take")
    ap.add_argument("--interval", type=float, default=5.0,
                    help="seconds between readings; keep it above one so the "
                         "probe is not measuring itself")
    ap.add_argument("--limit", type=int, default=None,
                    help="your account's concurrency ceiling, which is not a "
                         "readable field: get it from Twilio support")
    ap.add_argument("--warn-ratio", type=float, default=0.7,
                    help="fraction of the ceiling that counts as too close")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    readings, saw_429 = probe(session, account, args.samples, args.interval)
    seen = [r for r in readings if r is not None]
    log.info("%d sample(s), peak %s, %s",
             len(readings), max(seen) if seen else "unknown",
             "a 20429 was observed" if saw_429 else "no 20429 observed")

    state, detail = verdict(readings, args.limit, saw_429, args.warn_ratio)
    if state == "headroom":
        log.info("%-14s %s", state, detail)
        return 0

    log.warning("%-14s %s", state, detail)
    log.warning("  no console setting fixes this: bound the client's own "
                "concurrency below the ceiling with a semaphore or a fixed "
                "worker pool")
    log.warning("  retry 20429 with exponential backoff and jitter; the request "
                "was rejected before processing, so retrying is safe")
    log.warning("  a high-volume tenant can be moved into its own subaccount: "
                "concurrency is counted per account and does not roll up")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-concurrency-probe.mjs",
"js": '''/**
 * Sample Twilio's REST concurrency header and report how close to the ceiling.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const HEADER = 'twilio-concurrent-requests';

/**
 * The concurrency figure out of a response's headers, or null. Pure, and
 * case-insensitive by hand so a plain object in a test behaves like the real
 * Headers instance.
 */
export function concurrencyOf(headers) {
  const entries = headers instanceof Headers
    ? [...headers.entries()]
    : Object.entries(headers ?? {});
  for (const [name, value] of entries) {
    if (String(name).toLowerCase() !== HEADER) continue;
    const n = Number.parseInt(String(value).trim(), 10);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

/**
 * Classify a run of concurrency samples. Pure, so the thresholds are testable
 * without waiting for a real peak. Returns [state, detail].
 */
export function verdict(samples, limit = null, saw429 = false, warnRatio = 0.7) {
  const readings = (samples ?? []).filter((s) => s !== null && s !== undefined);

  if (saw429) {
    const peak = readings.length ? Math.max(...readings) : 0;
    return ['throttled',
      `a 429 came back during the sample itself, at a peak concurrency of ${peak}: ` +
      'the account is at its ceiling right now, and every rejected request still ' +
      'took a slot to be rejected.'];
  }

  if (!readings.length) {
    return ['no-header',
      `no Twilio-Concurrent-Requests header on any of the ${(samples ?? []).length} ` +
      'sample(s): with nothing to read, this check cannot say anything about ' +
      'concurrency.'];
  }

  const peak = Math.max(...readings);
  if (limit === null || limit === undefined) {
    return ['unmeasured',
      `peak concurrency ${peak} over ${readings.length} sample(s), and no ceiling ` +
      'to compare it against: the limit is not a readable field, so pass the one ' +
      'your account has with --limit.'];
  }

  const ratio = peak / limit;
  if (ratio >= 1) {
    return ['at-limit',
      `peak concurrency ${peak} against a ${limit} ceiling: requests are being ` +
      'refused with 20429 at the top of every burst.'];
  }
  if (ratio >= warnRatio) {
    return ['near-limit',
      `peak concurrency ${peak} of a ${limit} ceiling (${Math.round(ratio * 100)}%): ` +
      'one slow patch downstream lengthens every in-flight request and closes that ' +
      'gap without your traffic changing at all.'];
  }
  return ['headroom',
    `peak concurrency ${peak} of a ${limit} ceiling (${Math.round(ratio * 100)}%).`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function probe(auth, account, samples, interval) {
  const readings = [];
  let saw429 = false;
  const url = `${BASE}/Accounts/${account}.json`;
  for (let i = 0; i < samples; i += 1) {
    const res = await fetch(url, { headers: { Authorization: auth } });
    if (res.status === 401 || res.status === 403) {
      throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                      'that the API key belongs to that account with read access');
    }
    if (res.status === 429) saw429 = true;
    const value = concurrencyOf(res.headers);
    readings.push(value);
    console.log(`  sample ${String(i + 1).padStart(2)}: ` +
                `${value === null ? 'no header' : `${value} in flight`}`);
    if (i + 1 < samples) await sleep(interval * 1000);
  }
  return [readings, saw429];
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const arg = (name, fallback) => {
    const i = process.argv.indexOf(name);
    return i === -1 ? fallback : Number.parseFloat(process.argv[i + 1]);
  };
  const samples = arg('--samples', 12);
  const interval = arg('--interval', 5);
  const limit = process.argv.includes('--limit') ? arg('--limit', null) : null;
  const warnRatio = arg('--warn-ratio', 0.7);

  const [readings, saw429] = await probe(auth, account, samples, interval);
  const seen = readings.filter((r) => r !== null);
  console.log(`${readings.length} sample(s), peak ` +
              `${seen.length ? Math.max(...seen) : 'unknown'}, ` +
              `${saw429 ? 'a 20429 was observed' : 'no 20429 observed'}`);

  const [state, detail] = verdict(readings, limit, saw429, warnRatio);
  if (state === 'headroom') {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }
  console.warn(`${state.padEnd(14)} ${detail}`);
  console.warn('  no console setting fixes this: bound the client\\'s own ' +
               'concurrency below the ceiling with a semaphore or a fixed worker pool');
  console.warn('  retry 20429 with exponential backoff and jitter; the request was ' +
               'rejected before processing, so retrying is safe');
  console.warn('  a high-volume tenant can be moved into its own subaccount: ' +
               'concurrency is counted per account and does not roll up');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The header lookup gets its own cases because header casing differs between a real response object and the dictionary anybody writes in a test, and a check that silently returns nothing is worse than one that fails. The rest fixes the boundaries: a run with no ceiling is not a finding, an observed 429 outranks every reading, and 70% of the limit is close enough to say so.",
"test_py_file": "test_twilio_concurrency_probe.py",
"test_py": '''from twilio_concurrency_probe import concurrency_of, verdict


def test_the_header_is_read_whatever_its_casing():
    assert concurrency_of({"Twilio-Concurrent-Requests": "7"}) == 7
    assert concurrency_of({"twilio-concurrent-requests": " 12 "}) == 12


def test_a_missing_or_unusable_header_is_none_rather_than_zero():
    assert concurrency_of({}) is None
    assert concurrency_of({"Content-Type": "application/json"}) is None
    assert concurrency_of({"Twilio-Concurrent-Requests": "many"}) is None


def test_no_header_anywhere_is_reported_as_unmeasurable():
    state, detail = verdict([None, None, None])
    assert state == "no-header"
    assert "3 sample(s)" in detail


def test_samples_with_no_ceiling_are_an_observation_not_a_finding():
    state, detail = verdict([3, 5, 4])
    assert state == "unmeasured"
    assert "peak concurrency 5" in detail


def test_a_quiet_account_against_a_real_ceiling_has_headroom():
    state, _ = verdict([3, 5, 4], limit=100)
    assert state == "headroom"


def test_seventy_percent_of_the_ceiling_is_close_enough_to_warn():
    state, detail = verdict([40, 70, 55], limit=100)
    assert state == "near-limit"
    assert "70%" in detail


def test_touching_the_ceiling_is_the_20429():
    state, detail = verdict([98, 100], limit=100)
    assert state == "at-limit"
    assert "20429" in detail


def test_an_observed_429_outranks_every_reading():
    state, detail = verdict([2, 3], limit=100, saw_429=True)
    assert state == "throttled"
    assert "a peak concurrency of 3" in detail


def test_a_429_with_no_readings_still_reports_rather_than_crashing():
    state, _ = verdict([None], limit=100, saw_429=True)
    assert state == "throttled"


def test_the_warn_ratio_is_adjustable():
    assert verdict([50], limit=100, warn_ratio=0.4)[0] == "near-limit"
    assert verdict([50], limit=100, warn_ratio=0.9)[0] == "headroom"
''',
"test_js_file": "twilio-concurrency-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { concurrencyOf, verdict } from './twilio-concurrency-probe.mjs';

test('the header is read whatever its casing', () => {
  assert.equal(concurrencyOf({ 'Twilio-Concurrent-Requests': '7' }), 7);
  assert.equal(concurrencyOf({ 'twilio-concurrent-requests': ' 12 ' }), 12);
});

test('a missing or unusable header is null rather than zero', () => {
  assert.equal(concurrencyOf({}), null);
  assert.equal(concurrencyOf({ 'Content-Type': 'application/json' }), null);
  assert.equal(concurrencyOf({ 'Twilio-Concurrent-Requests': 'many' }), null);
});

test('a real Headers instance is read the same way', () => {
  assert.equal(concurrencyOf(new Headers({ 'Twilio-Concurrent-Requests': '9' })), 9);
});

test('no header anywhere is reported as unmeasurable', () => {
  const [state, detail] = verdict([null, null, null]);
  assert.equal(state, 'no-header');
  assert.match(detail, /3 sample\\(s\\)/);
});

test('samples with no ceiling are an observation, not a finding', () => {
  const [state, detail] = verdict([3, 5, 4]);
  assert.equal(state, 'unmeasured');
  assert.match(detail, /peak concurrency 5/);
});

test('a quiet account against a real ceiling has headroom', () => {
  assert.equal(verdict([3, 5, 4], 100)[0], 'headroom');
});

test('seventy percent of the ceiling is close enough to warn', () => {
  const [state, detail] = verdict([40, 70, 55], 100);
  assert.equal(state, 'near-limit');
  assert.match(detail, /70%/);
});

test('touching the ceiling is the 20429', () => {
  const [state, detail] = verdict([98, 100], 100);
  assert.equal(state, 'at-limit');
  assert.match(detail, /20429/);
});

test('an observed 429 outranks every reading', () => {
  const [state, detail] = verdict([2, 3], 100, true);
  assert.equal(state, 'throttled');
  assert.match(detail, /a peak concurrency of 3/);
});

test('a 429 with no readings still reports rather than crashing', () => {
  assert.equal(verdict([null], 100, true)[0], 'throttled');
});

test('the warn ratio is adjustable', () => {
  assert.equal(verdict([50], 100, false, 0.4)[0], 'near-limit');
  assert.equal(verdict([50], 100, false, 0.9)[0], 'headroom');
});
''',
"faq": [
 ("What is my account's concurrency limit?",
  "It is an account property rather than a documented constant, and it is not returned by any endpoint, which is why this script takes it as an argument. Twilio support will tell you what yours is and will discuss raising it for a documented workload. Until you have the number, the probe still reports your observed peak, which is the half of the comparison you can gather yourself."),
 ("How is this different from a rate limit?",
  "A rate limit counts requests per unit of time; concurrency counts requests that have been sent and not yet answered. You can breach a concurrency limit without your request rate changing at all, simply because responses got slower and the in-flight pile grew. That is the usual cause, and it is why the fix is a bound on parallelism rather than a delay between calls."),
 ("Is it safe to retry a 20429?",
  "Yes. The request was refused before it was processed, so nothing was partially created and no message was sent. What is not safe is retrying immediately: without exponential backoff and jitter, every rejected caller retries at the same moment and reproduces the burst. Retrying wrong is what turns a two-second problem into a two-minute one."),
 ("Does the probe itself affect the number?",
  "Slightly, and honestly so. The request carrying the header is in flight while the figure is computed, so an idle account reads 1 rather than 0. At a sampling interval of seconds that contribution is one request and negligible; at an interval of milliseconds you would be measuring your own probe, which is why the default interval is five seconds."),
 ("Will splitting into subaccounts really help?",
  "It genuinely separates the budgets, because concurrency is counted against the account SID the request is made under and subaccount usage does not roll up into the parent's tally. It is a real lever for isolating one loud tenant. It is also a structural change with its own operational cost, so cap the client first and shard only when a single client cannot fit under the ceiling."),
],
"related": [
 ("/twilio/messaging-queue-overflow-30001/", "The other burst failure, where the queue rather than the API gives way"),
 ("/twilio/subaccount-suspended-silently/", "Sharding across subaccounts, and the way one goes quiet"),
 ("/twilio/auth-token-used-instead-of-api-key/", "The credential this probe should be holding"),
],
"citations": [CITE_20429, CITE_BEST_PRACTICES, CITE_USAGE_API, CITE_SUBACCOUNTS],
},

{
"slug": "unreleased-recordings-storage",
"title": "Recordings billed for storage until something deletes them",
"description": "Twilio stores call recordings forever and bills per stored minute. Read the accumulated recordings spend and the oldest file, not the number of files.",
"h1": "recordings billed for storage until something deletes them",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio recording storage cost", "twilio delete recordings",
             "twilio recordings usage record", "twilio recording retention",
             "twilio unused resources"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody enabled recording on a support line in 2022, wrote the code that downloads each file into your own bucket, and never wrote the line that deletes the Twilio-side copy. Every one of those recordings is still there. You are paying to store all of them, every month, and the charge is a small enough line on the invoice that it has survived four years of expense reviews.",
"short_answer": """<p>The count of recordings is not the finding. The finding is the money: read <code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/AllTime.json?Category=recordings</code> for what this has cost to date, and <code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Daily.json?Category=recordings</code> for the rate it is still running at. A daily rate times a year is the number that gets this prioritised.</p>
<p>Then page <code>GET /2010-04-01/Accounts/{AccountSid}/Recordings.json</code> and look at <code>date_created</code> on the oldest rows. A recording older than any retention policy you claim to have is the evidence that nothing is deleting them.</p>""",
"problem": """<p>Twilio keeps a recording until something tells it not to. There is no default expiry, no lifecycle rule of the sort object storage has trained everyone to expect, and no warning as the collection grows. The application that fetches the media and archives it properly is doing exactly half the job, and the half it skips is invisible, because the archive works, the recordings play, and nothing anywhere reports a failure.</p>
<p>What makes it survive review is the shape of the cost. It is not one bad month, it is a per-minute charge on an ever-growing pile: this month's bill is last month's bill plus a bit, forever, and no single month's increase is large enough to open a ticket about. Counting files does not communicate that at all &mdash; forty thousand recordings is a number nobody can price. The accumulated spend and the projected next twelve months are the same fact in the units that get a retention job written.</p>""",
"why": """<p><strong>The delete is a separate call from the download.</strong> Fetching the media is a GET on the recording's URI; removing it is a delete on the recording resource. Nothing about a successful download implies or triggers the second, so the natural first version of the archiving code &mdash; the one that works &mdash; is the one that leaks storage.</p>
<p><strong>The charge is tiny per unit and unbounded in aggregate.</strong> A per-stored-minute rate on a collection that only grows produces a bill whose derivative is small and whose integral is not. It is the archetypal cost that is never worth anybody's afternoon until somebody puts a year's projection next to it.</p>
<p><strong>Recordings you no longer want are also a liability you still hold.</strong> Every stored call is retrievable with account credentials, so the pile is subject access requests, discovery, and whatever your privacy notice promised about retention. If those recordings are unencrypted, holding them longer than you said you would is a finding in an audit as well as a line on an invoice.</p>
<p><strong>Nothing tells you which are safe to delete.</strong> There is no field marking a recording as archived elsewhere. That knowledge lives in your own bucket, which is why this script reports and prints rather than deleting: matching Twilio's list against your archive is a decision only your side can make.</p>""",
"steps": [
 {"h": "Price it before you count it",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/AllTime.json?Category=recordings</code> returns the accumulated <code>price</code>, <code>usage</code> and <code>price_unit</code> for the category. That single figure is the argument. Categories are named on your usage report, so if yours itemises recording storage under a different one, pass it with <code>--category</code>.</p>"""},
 {"h": "Get the rate it is still running at",
  "body": """<p><code>Usage/Records/Daily.json?Category=recordings&amp;StartDate={30d ago}</code> gives one priced row per day. The mean of those is a daily rate, and a daily rate times 365 is the projection: what another year of doing nothing costs, in the same currency as the invoice.</p>"""},
 {"h": "Find the oldest recording still there",
  "body": """<p>Page <code>Recordings.json?PageSize=1000</code> and parse <code>date_created</code>, which is RFC 2822 (<code>Tue, 18 Apr 2023 09:12:00 +0000</code>) rather than ISO 8601. Anything older than your stated retention window is proof that no retention job exists, as distinct from one that exists and is behind.</p>"""},
 {"h": "Sum the durations to see what you are storing",
  "body": """<p>Each row carries <code>duration</code> in seconds as a string. Summing them across the sample gives stored minutes, which is the unit the storage charge is levied in and the bridge between "forty thousand files" and a number on a bill.</p>"""},
 {"h": "Delete after archiving, and decide the window once",
  "body": """<p>The repair is a delete on each recording you have already archived, after the download has been verified, plus a retention policy in Console &rarr; Voice &rarr; Settings so the next four years do not repeat this one. Pick the window from your privacy notice rather than from the cost, then let the cost tell you how urgent the backfill is.</p>"""},
],
"verify": """<p>Re-run after the retention job has caught up. Nothing should be older than the window, and the state should be <code>retained</code>.</p>
<pre><code class="language-bash">python3 twilio_recording_storage_audit.py --window-days 90
# 1,204 recording(s) sampled, 3,412.5 stored minute(s)
# retained       1204 recording(s) sampled, none older than 90 days, 812.44 billed
#                to recordings so far: something is deleting them.</code></pre>""",
"code_intro": "Three reads: the all-time usage record for the category, one page of daily records for the rate, and a paginated sweep of recordings for the ages and durations. The classifier is pure and takes numbers rather than responses &mdash; accumulated spend, daily rate, how many of the sample are past the window &mdash; because the judgement worth testing is the one that turns those into a sentence somebody will act on.",
"py_file": "twilio_recording_storage_audit.py",
"py": '''"""Report Twilio call recordings that are still billing for storage.

The finding is the money, not the file count: a count of recordings is a number
nobody can price, and the accumulated spend plus a year's projection is the same
fact in the units that get a retention job written.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime
import email.utils
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_recording_storage_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

CATEGORY = "recordings"


def parse_created(value):
    """A Twilio date_created as a date, or None.

    The 2010-04-01 API returns RFC 2822 dates (Tue, 18 Apr 2023 09:12:00 +0000),
    not ISO 8601. Handing one of those to a date parser expecting ISO gives you
    an exception on every row, which reads exactly like an empty account.
    """
    try:
        return email.utils.parsedate_to_datetime(str(value)).date()
    except (TypeError, ValueError, AttributeError):
        return None


def older_than(recordings, window_days, today):
    """(how many are past the window, age in days of the oldest). Pure."""
    ages = []
    for recording in recordings or []:
        created = parse_created(recording.get("date_created"))
        if created is None:
            continue
        ages.append((today - created).days)
    if not ages:
        return (0, None)
    return (len([a for a in ages if a > window_days]), max(ages))


def stored_minutes(recordings):
    """Minutes of media in the sample. Duration is seconds, as a string. Pure."""
    total = 0.0
    for recording in recordings or []:
        try:
            total += float(recording.get("duration"))
        except (TypeError, ValueError):
            continue
    return round(total / 60.0, 1)


def daily_rate(records):
    """Mean priced day out of a Usage/Records/Daily page. Pure.

    The mean rather than the median here: storage accrues every day at a rate
    set by the size of the pile, so there is no spiky day to defend against and
    the mean is the honest per-day figure to project from.
    """
    prices = []
    for record in records or []:
        try:
            prices.append(max(0.0, float(record.get("price"))))
        except (TypeError, ValueError):
            continue
    if not prices:
        return 0.0
    return sum(prices) / len(prices)


def project(rate, days=365):
    """What the current rate costs over a horizon. Pure."""
    return round((rate or 0.0) * days, 2)


def verdict(total_price, rate, stale_count, sample_size, window_days):
    """Classify the storage position. Pure, so the arithmetic that turns a pile
    of files into a number somebody will act on is testable offline.

    Returns (state, detail).
    """
    total_price = total_price or 0.0

    if sample_size <= 0:
        if total_price <= 0:
            return ("empty",
                    "no recordings and nothing billed to recording storage: there "
                    "is nothing here to release.")
        return ("billed-only",
                "no recordings stored now, but %.2f billed to recording storage "
                "historically: the spend is in the past and the pile is gone."
                % total_price)

    if stale_count == 0:
        return ("retained",
                "%d recording(s) sampled, none older than %d days, %.2f billed to "
                "recording storage so far: something is deleting them."
                % (sample_size, window_days, total_price))

    if rate > 0:
        return ("accumulating",
                "%d of %d sampled recording(s) older than %d days. %.2f billed to "
                "recording storage to date, running at %.2f a day: about %.2f more "
                "over the next year unless something deletes them."
                % (stale_count, sample_size, window_days, total_price, rate,
                   project(rate)))

    return ("unpriced",
            "%d of %d sampled recording(s) older than %d days, and no priced usage "
            "in the window: the media is still stored, so check the category name "
            "on your usage report and re-run with --category."
            % (stale_count, sample_size, window_days))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_recordings(session, account, limit=2000):
    """Page Recordings.json. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts/%s/Recordings.json" % (BASE, account)
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("recordings", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def all_time_spend(session, account, category):
    """Accumulated (price, usage, price_unit) for one usage category."""
    page = get(session, "%s/Accounts/%s/Usage/Records/AllTime.json" % (BASE, account),
               Category=category, PageSize=1)
    rows = page.get("usage_records", [])
    if not rows:
        return (0.0, "0", "")
    row = rows[0]
    try:
        price = float(row.get("price"))
    except (TypeError, ValueError):
        price = 0.0
    return (price, row.get("usage", "0"), row.get("price_unit", ""))


def daily_records(session, account, category, days):
    start = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    page = get(session, "%s/Accounts/%s/Usage/Records/Daily.json" % (BASE, account),
               Category=category, StartDate=start, PageSize=100)
    return page.get("usage_records", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window-days", type=int, default=90,
                    help="retention window: anything older is evidence that "
                         "nothing is deleting recordings")
    ap.add_argument("--days", type=int, default=30,
                    help="days of usage records the daily rate is taken from")
    ap.add_argument("--sample", type=int, default=2000,
                    help="how many recordings to page through")
    ap.add_argument("--category", default=CATEGORY,
                    help="usage category carrying recording storage on your bill")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    recordings = list_recordings(session, account, args.sample)
    total_price, usage, unit = all_time_spend(session, account, args.category)
    rate = daily_rate(daily_records(session, account, args.category, args.days))
    stale, oldest = older_than(recordings, args.window_days, datetime.date.today())

    log.info("%d recording(s) sampled, %s stored minute(s), %.2f %s billed to %s "
             "all time", len(recordings), stored_minutes(recordings), total_price,
             unit, args.category)
    if oldest is not None:
        log.info("oldest recording in the sample: %d days old", oldest)

    state, detail = verdict(total_price, rate, stale, len(recordings),
                            args.window_days)
    if state in ("empty", "retained", "billed-only"):
        log.info("%-14s %s", state, detail)
        return 0

    log.warning("%-14s %s", state, detail)
    log.warning("  repair: for each recording already archived on your side, "
                "delete it from %s/Accounts/%s/Recordings/{RecordingSid}.json "
                "after verifying the copy you hold", BASE, account)
    log.warning("  then set a retention policy in Console > Voice > Settings so "
                "the next four years do not repeat this one")
    log.warning("  the API has no field saying which recordings you have "
                "archived: that match is yours to make, which is why this "
                "script only reports")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-recording-storage-audit.mjs",
"js": '''/**
 * Report Twilio call recordings that are still billing for storage.
 *
 * The finding is the money, not the file count. Read only: GET requests and
 * nothing else, with the repair printed rather than performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const CATEGORY = 'recordings';

/**
 * A Twilio date_created as a date at UTC midnight, or null. The 2010-04-01 API
 * returns RFC 2822 dates rather than ISO 8601, and a parser that assumes ISO
 * fails on every row, which reads exactly like an empty account.
 */
export function parseCreated(value) {
  if (value === null || value === undefined) return null;
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) return null;
  return new Date(Date.UTC(parsed.getUTCFullYear(), parsed.getUTCMonth(),
                           parsed.getUTCDate()));
}

/** [how many are past the window, age in days of the oldest]. Pure. */
export function olderThan(recordings, windowDays, today) {
  const ages = [];
  for (const recording of recordings ?? []) {
    const created = parseCreated(recording?.date_created);
    if (created === null) continue;
    ages.push(Math.floor((today.getTime() - created.getTime()) / 86400000));
  }
  if (!ages.length) return [0, null];
  return [ages.filter((a) => a > windowDays).length, Math.max(...ages)];
}

/** Minutes of media in the sample. duration is seconds, as a string. Pure. */
export function storedMinutes(recordings) {
  let total = 0;
  for (const recording of recordings ?? []) {
    const seconds = Number.parseFloat(recording?.duration ?? '');
    if (Number.isFinite(seconds)) total += seconds;
  }
  return Math.round((total / 60) * 10) / 10;
}

/** Mean priced day out of a Usage/Records/Daily page. Pure. */
export function dailyRate(records) {
  const prices = [];
  for (const record of records ?? []) {
    const price = Number.parseFloat(record?.price ?? '');
    if (Number.isFinite(price)) prices.push(Math.max(0, price));
  }
  if (!prices.length) return 0;
  return prices.reduce((a, b) => a + b, 0) / prices.length;
}

/** What the current rate costs over a horizon. Pure. */
export function project(rate, days = 365) {
  return Math.round((rate || 0) * days * 100) / 100;
}

/**
 * Classify the storage position. Pure, so the arithmetic that turns a pile of
 * files into a number somebody will act on is testable offline.
 * Returns [state, detail].
 */
export function verdict(totalPrice, rate, staleCount, sampleSize, windowDays) {
  const total = totalPrice || 0;

  if (sampleSize <= 0) {
    if (total <= 0) {
      return ['empty',
        'no recordings and nothing billed to recording storage: there is nothing ' +
        'here to release.'];
    }
    return ['billed-only',
      `no recordings stored now, but ${total.toFixed(2)} billed to recording ` +
      'storage historically: the spend is in the past and the pile is gone.'];
  }

  if (staleCount === 0) {
    return ['retained',
      `${sampleSize} recording(s) sampled, none older than ${windowDays} days, ` +
      `${total.toFixed(2)} billed to recording storage so far: something is ` +
      'deleting them.'];
  }

  if (rate > 0) {
    return ['accumulating',
      `${staleCount} of ${sampleSize} sampled recording(s) older than ${windowDays} ` +
      `days. ${total.toFixed(2)} billed to recording storage to date, running at ` +
      `${rate.toFixed(2)} a day: about ${project(rate).toFixed(2)} more over the ` +
      'next year unless something deletes them.'];
  }

  return ['unpriced',
    `${staleCount} of ${sampleSize} sampled recording(s) older than ${windowDays} ` +
    'days, and no priced usage in the window: the media is still stored, so check ' +
    'the category name on your usage report and re-run with --category.'];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listRecordings(auth, account, limit = 2000) {
  let url = `${BASE}/Accounts/${account}/Recordings.json`;
  let params = { PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.recordings ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function allTimeSpend(auth, account, category) {
  const page = await get(auth, `${BASE}/Accounts/${account}/Usage/Records/AllTime.json`,
                         { Category: category, PageSize: 1 });
  const rows = page.usage_records ?? [];
  if (!rows.length) return [0, '0', ''];
  const price = Number.parseFloat(rows[0].price ?? '');
  return [Number.isFinite(price) ? price : 0, rows[0].usage ?? '0',
          rows[0].price_unit ?? ''];
}

async function dailyRecords(auth, account, category, days) {
  const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const page = await get(auth, `${BASE}/Accounts/${account}/Usage/Records/Daily.json`,
                         { Category: category, StartDate: start, PageSize: 100 });
  return page.usage_records ?? [];
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const arg = (name, fallback) => {
    const i = process.argv.indexOf(name);
    return i === -1 ? fallback : Number.parseFloat(process.argv[i + 1]);
  };
  const windowDays = arg('--window-days', 90);
  const days = arg('--days', 30);
  const sample = arg('--sample', 2000);
  const ci = process.argv.indexOf('--category');
  const category = ci === -1 ? CATEGORY : process.argv[ci + 1];

  const recordings = await listRecordings(auth, account, sample);
  const [totalPrice, , unit] = await allTimeSpend(auth, account, category);
  const rate = dailyRate(await dailyRecords(auth, account, category, days));
  const now = new Date();
  const today = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(),
                                  now.getUTCDate()));
  const [stale, oldest] = olderThan(recordings, windowDays, today);

  console.log(`${recordings.length} recording(s) sampled, ` +
              `${storedMinutes(recordings)} stored minute(s), ` +
              `${totalPrice.toFixed(2)} ${unit} billed to ${category} all time`);
  if (oldest !== null) {
    console.log(`oldest recording in the sample: ${oldest} days old`);
  }

  const [state, detail] = verdict(totalPrice, rate, stale, recordings.length,
                                  windowDays);
  if (['empty', 'retained', 'billed-only'].includes(state)) {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(14)} ${detail}`);
  console.warn('  repair: for each recording already archived on your side, delete ' +
               `it from ${BASE}/Accounts/${account}/Recordings/{RecordingSid}.json ` +
               'after verifying the copy you hold');
  console.warn('  then set a retention policy in Console > Voice > Settings so the ' +
               'next four years do not repeat this one');
  console.warn('  the API has no field saying which recordings you have archived: ' +
               'that match is yours to make, which is why this script only reports');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The date parsing gets its own cases because Twilio's RFC 2822 timestamps break every ISO parser, and a parser that throws on every row produces a report that says the account is clean. The rest of the cases pin the distinction the guide is about: an account with recordings and no deletions is reported as a projected annual cost, not as a file count.",
"test_py_file": "test_twilio_recording_storage_audit.py",
"test_py": '''import datetime

from twilio_recording_storage_audit import (daily_rate, older_than, parse_created,
                                            project, stored_minutes, verdict)

TODAY = datetime.date(2026, 8, 30)


def rec(created, duration="120"):
    return {"sid": "RE01", "date_created": created, "duration": duration}


def test_rfc_2822_dates_parse_and_iso_style_junk_does_not():
    assert parse_created("Tue, 18 Apr 2023 09:12:00 +0000") == datetime.date(2023, 4, 18)
    assert parse_created("not a date") is None
    assert parse_created(None) is None


def test_ages_are_measured_against_the_day_you_pass_in():
    stale, oldest = older_than([rec("Mon, 01 Jun 2026 00:00:00 +0000"),
                                rec("Sat, 01 Jun 2024 00:00:00 +0000")], 90, TODAY)
    assert stale == 1
    assert oldest == 820


def test_an_unparseable_row_is_skipped_rather_than_counted_as_new():
    stale, oldest = older_than([rec("garbage")], 90, TODAY)
    assert (stale, oldest) == (0, None)


def test_stored_minutes_add_up_and_ignore_bad_durations():
    assert stored_minutes([rec("x", "90"), rec("x", "30"), rec("x", None)]) == 2.0


def test_the_daily_rate_is_the_mean_of_the_priced_days():
    assert daily_rate([{"price": "1.00"}, {"price": "3.00"}]) == 2.0
    assert daily_rate([]) == 0.0


def test_the_projection_is_the_rate_over_a_year():
    assert project(0.5) == 182.5
    assert project(0.0) == 0.0


def test_no_recordings_and_no_spend_is_nothing_to_do():
    state, _ = verdict(0.0, 0.0, 0, 0, 90)
    assert state == "empty"


def test_historic_spend_with_nothing_stored_is_not_a_finding():
    state, detail = verdict(400.0, 0.0, 0, 0, 90)
    assert state == "billed-only"
    assert "in the past" in detail


def test_a_working_retention_job_reads_as_retained():
    state, detail = verdict(812.44, 0.4, 0, 1204, 90)
    assert state == "retained"
    assert "something is deleting them" in detail


def test_the_finding_is_the_projected_cost_not_the_file_count():
    state, detail = verdict(3200.0, 2.0, 38000, 40000, 90)
    assert state == "accumulating"
    assert "730.00 more over the next year" in detail


def test_stale_files_with_no_priced_usage_send_you_to_the_category_name():
    state, detail = verdict(0.0, 0.0, 12, 40, 90)
    assert state == "unpriced"
    assert "--category" in detail
''',
"test_js_file": "twilio-recording-storage-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dailyRate, olderThan, parseCreated, project, storedMinutes, verdict }
  from './twilio-recording-storage-audit.mjs';

const TODAY = new Date(Date.UTC(2026, 7, 30));

const rec = (created, duration = '120') => ({
  sid: 'RE01', date_created: created, duration,
});

test('RFC 2822 dates parse and junk does not', () => {
  assert.equal(parseCreated('Tue, 18 Apr 2023 09:12:00 +0000').toISOString(),
               '2023-04-18T00:00:00.000Z');
  assert.equal(parseCreated('not a date'), null);
  assert.equal(parseCreated(null), null);
});

test('ages are measured against the day you pass in', () => {
  const [stale, oldest] = olderThan([rec('Mon, 01 Jun 2026 00:00:00 +0000'),
                                     rec('Sat, 01 Jun 2024 00:00:00 +0000')],
                                    90, TODAY);
  assert.equal(stale, 1);
  assert.equal(oldest, 820);
});

test('an unparseable row is skipped rather than counted as new', () => {
  assert.deepEqual(olderThan([rec('garbage')], 90, TODAY), [0, null]);
});

test('stored minutes add up and ignore bad durations', () => {
  assert.equal(storedMinutes([rec('x', '90'), rec('x', '30'), rec('x', null)]), 2.0);
});

test('the daily rate is the mean of the priced days', () => {
  assert.equal(dailyRate([{ price: '1.00' }, { price: '3.00' }]), 2.0);
  assert.equal(dailyRate([]), 0);
});

test('the projection is the rate over a year', () => {
  assert.equal(project(0.5), 182.5);
  assert.equal(project(0), 0);
});

test('no recordings and no spend is nothing to do', () => {
  assert.equal(verdict(0, 0, 0, 0, 90)[0], 'empty');
});

test('historic spend with nothing stored is not a finding', () => {
  const [state, detail] = verdict(400, 0, 0, 0, 90);
  assert.equal(state, 'billed-only');
  assert.match(detail, /in the past/);
});

test('a working retention job reads as retained', () => {
  const [state, detail] = verdict(812.44, 0.4, 0, 1204, 90);
  assert.equal(state, 'retained');
  assert.match(detail, /something is deleting them/);
});

test('the finding is the projected cost, not the file count', () => {
  const [state, detail] = verdict(3200, 2, 38000, 40000, 90);
  assert.equal(state, 'accumulating');
  assert.match(detail, /730\\.00 more over the next year/);
});

test('stale files with no priced usage send you to the category name', () => {
  const [state, detail] = verdict(0, 0, 12, 40, 90);
  assert.equal(state, 'unpriced');
  assert.match(detail, /--category/);
});
''',
"faq": [
 ("Why report the cost rather than the number of recordings?",
  "Because a count does not survive a prioritisation meeting. Forty thousand recordings is a number nobody can price and everybody can defer. The same fact expressed as what it has cost so far and what another year costs at the current rate is a line somebody can compare against the afternoon it takes to write the deletion job, which is the comparison that actually gets it done."),
 ("Does deleting a recording break anything that references it?",
  "The recording resource and its media are gone, so any URL you handed out or stored that points at Twilio's copy stops resolving, and the recording disappears from the call's subresources. Nothing else is affected: the call record, its duration and its billing history all remain. This is exactly why the deletion has to follow a verified archive on your side rather than run on a timer."),
 ("Is there a retention setting that does this automatically?",
  "There is a retention configuration in the voice settings of the console, and setting it is the right long-term answer. It does not retrospectively clear what has already accumulated, so the backfill is still yours to run once. Set the policy first so the pile stops growing, then work backwards through what is already there."),
 ("What if my usage report calls the category something else?",
  "Pass it with --category. Usage categories are the names on your own usage report, and which ones an account itemises depends on the products it uses. The script defaults to the recordings category and takes an override precisely so that nobody has to edit code to point the check at whatever their invoice actually calls it."),
 ("Should this script delete the old ones for me?",
  "No. Nothing in the Twilio API records whether a given recording has been archived on your side; that knowledge lives in your bucket and your database. A script holding a read-only credential is in no position to decide which media is safe to destroy, so it prints the delete and the retention setting and lets a human who can check the archive run them."),
],
"related": [
 ("/twilio/idle-phone-numbers-billed/", "The other recurring charge for something nobody uses"),
 ("/twilio/balance-below-safety-floor/", "What steady unnoticed spend does to the balance"),
 ("/twilio/no-usage-trigger-configured/", "The alarm that would have flagged the growing line"),
],
"citations": [CITE_UNUSED, CITE_RECORDING, CITE_RECORD, CITE_ENCRYPTION],
},

]
