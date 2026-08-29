#!/usr/bin/env python3
"""/twilio/ field notes, batch J — the writing.

Four problems that live in the account rather than in the traffic: no spend
alarm at all, the account auth token doing the work of an API key, API keys
nobody can account for, and a regulatory bundle quietly counting down to the
day it stops being approved.

The API key note is the one the rest of this section points at. Every other
script here tells you to use an API Key with read access rather than the auth
token; that one explains why, and how to find the places still holding the
token.

Read-only throughout. GET requests only, and every repair is printed for a
human to run rather than performed.
"""

CITE_TRIGGER = ("UsageTrigger resource — Twilio Docs",
                "https://www.twilio.com/docs/usage/api/usage-trigger")
CITE_RECORD = ("UsageRecord resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/api/usage-record")
CITE_FRAUD = ("Fraud response guide: contain — Twilio Docs",
              "https://www.twilio.com/docs/usage/fraud-response-guide/contain")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_KEY_RESOURCE = ("Key resource (2010-04-01) — Twilio Docs",
                     "https://www.twilio.com/docs/iam/api-keys/key-resource-v2010")
CITE_SECURE = ("Secure your Twilio account — Twilio Docs",
               "https://www.twilio.com/docs/usage/security/secure-your-twilio-account")
CITE_SIGNATURE = ("Webhook security and X-Twilio-Signature — Twilio Docs",
                  "https://www.twilio.com/docs/usage/webhooks/webhooks-security")
CITE_BUNDLES = ("Bundle resource — Twilio Docs",
                "https://www.twilio.com/docs/phone-numbers/regulatory/api/bundles")
CITE_REGULATORY = ("Regulatory compliance for phone numbers — Twilio Docs",
                   "https://www.twilio.com/docs/phone-numbers/regulatory")
CITE_SUPPORTING = ("Supporting Document resource — Twilio Docs",
                   "https://www.twilio.com/docs/phone-numbers/regulatory/api/supporting-documents")

GUIDES = [

{
"slug": "no-usage-trigger-configured",
"title": "No Usage Trigger, so overspend runs with nothing watching",
"description": "Usage Triggers are the only server-side spend alarm Twilio has, and an account starts with none. Find that, and the dead triggers, before the invoice does.",
"h1": "no Usage Trigger, so overspend runs with nothing watching",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio usage trigger", "twilio spend alert", "twilio sms pumping bill",
             "twilio usage_triggers empty", "twilio balance exhausted 20005"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The invoice is for eleven thousand dollars. Most of it is SMS to a country you do not sell in, sent over a Saturday night by the verification form on your signup page. Nobody was paged, because there was nothing to page: Usage Triggers are the only spend alarm Twilio runs on its own side, and an account is created with none of them.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Triggers.json</code>. An empty <code>usage_triggers[]</code> means nothing on Twilio's side is watching this account at all.</p>
<p>A non-empty list is not the same as coverage. A trigger only alarms if it can fire again (<code>recurring</code> set to <code>daily</code> or <code>monthly</code>, not a one-shot with <code>date_fired</code> already stamped), if there is somewhere for it to fire to (<code>callback_url</code> populated), and if it measures money (<code>trigger_by</code> of <code>price</code> on <code>usage_category</code> <code>totalprice</code>) rather than a count of messages.</p>""",
"problem": """<p>Fraud on a messaging account is not a slow leak. A pumping burst against an unprotected verification endpoint runs at whatever throughput your senders allow, for as long as the balance lasts, and the traffic looks entirely legitimate on the way out: valid destinations, valid segments, <code>delivered</code> status callbacks. Nothing in your application errors. Nothing in the Debugger appears, because nothing failed.</p>
<p>The end of it is either an invoice or a <code>20005</code>: the balance runs out, the account is suspended, and now your real traffic stops too. Both endings arrive without warning, and both arrive hours or days after the point where a five-line alarm would have caught it. The window between the first anomalous hour and the damage is the entire value of this check, and it is a window you can only use if something is watching during it.</p>""",
"why": """<p><strong>The default is zero.</strong> No trigger is created when you open an account, buy a number, or start a Messaging Service. Nothing in onboarding asks. The absence is not a misconfiguration anyone made; it is what an account looks like until somebody deliberately adds one.</p>
<p><strong>A one-shot trigger is a fuse, not an alarm.</strong> Created without <code>Recurring</code>, a trigger fires once, stamps <code>date_fired</code>, and is finished. It stays in the API forever afterwards, with a friendly name and a threshold, looking exactly like a working alarm. The account it was protecting has been unprotected since the day it fired.</p>
<p><strong>A trigger with no <code>callback_url</code> reaches nobody who is on call.</strong> The threshold is evaluated either way, but with no URL there is no request, so there is nothing for your alerting to receive and nothing to route to a pager at two in the morning.</p>
<p><strong>Counts do not cap money.</strong> A trigger on <code>sms</code> with <code>trigger_by</code> of <code>count</code> is a reasonable volume alarm and a poor spend alarm: the same segment count to a premium destination can cost an order of magnitude more, which is exactly what pumping is engineered to exploit. <code>totalprice</code> with <code>trigger_by=price</code> is the one that catches it regardless of which product the money went out through.</p>
<p><strong>Triggers belong to an account, so subaccounts start over.</strong> The trigger you carefully set on the parent is evaluated against the parent's usage records. Every subaccount you create is a fresh unalarmed account.</p>""",
"steps": [
 {"h": "List the triggers on the account",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Triggers.json?PageSize=50</code>, following <code>next_page_uri</code>. Read <code>usage_category</code>, <code>trigger_by</code>, <code>trigger_value</code>, <code>recurring</code>, <code>callback_url</code> and <code>date_fired</code> on each. An empty list ends the audit right there with the worst possible answer.</p>"""},
 {"h": "Ask of each trigger whether it can fire again",
  "body": """<p><code>recurring</code> is the field that separates an alarm from a fuse. Empty means one-shot; combined with a populated <code>date_fired</code> it means the alarm has already been used up. This is the single most common way an account with triggers is still unprotected.</p>"""},
 {"h": "Ask where it fires to",
  "body": """<p>A blank <code>callback_url</code> means no request is made when the threshold is crossed. Check <code>callback_method</code> too while you are in the response: a URL that only accepts POST paired with a GET method is the same outcome with more steps.</p>"""},
 {"h": "Ask what it actually measures",
  "body": """<p><code>usage_category</code> of <code>totalprice</code> with <code>trigger_by</code> of <code>price</code> is the one that catches spend wherever it happens. Category triggers on <code>sms</code> or <code>calls</code> are useful additions and a poor substitute, because the money can leave through the category you did not cover.</p>"""},
 {"h": "Set a daily price cap, then re-run per subaccount",
  "body": """<p><code>POST /2010-04-01/Accounts/{AccountSid}/Usage/Triggers.json</code> with <code>UsageCategory=totalprice</code>, <code>TriggerBy=price</code>, <code>TriggerValue</code> at roughly three times your busiest recent day, <code>Recurring=daily</code>, and a <code>CallbackUrl</code> that reaches your on-call rotation. Then run the audit against every subaccount, because each one needs its own.</p>"""},
],
"verify": """<p>Re-run the script. The account should report <code>covered</code>, and the exit code should be zero.</p>
<pre><code class="language-bash">python3 twilio_usage_trigger_audit.py
# covered  1 recurring price trigger(s) on totalprice with a callback.</code></pre>""",
"code_intro": "One paginated GET over the triggers, and with <code>--suggest-cap</code> one more over the daily usage records so the printed repair carries a real number instead of a placeholder. Read access is all it needs and all you should give it. The classification is a pure function over the whole list rather than over one trigger, because the finding here is about what the set as a whole fails to cover.",
"py_file": "twilio_usage_trigger_audit.py",
"py": '''"""Report a Twilio account with no Usage Trigger that can actually fire.

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
log = logging.getLogger("twilio_usage_trigger_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

SPEND_CATEGORY = "totalprice"
RECURRING = ("daily", "monthly", "yearly")


def fires_again(trigger):
    """True when the trigger resets itself rather than firing once and stopping.

    An empty recurring is the difference between an alarm and a fuse, and the
    fired fuse looks identical to a working alarm in the console.
    """
    return str(trigger.get("recurring") or "").strip().lower() in RECURRING


def has_callback(trigger):
    """True when crossing the threshold results in a request to something."""
    return bool(str(trigger.get("callback_url") or "").strip())


def by_price(trigger):
    """True when the threshold is money rather than a count of messages or calls."""
    return str(trigger.get("trigger_by") or "").strip().lower() == "price"


def verdict(triggers):
    """Classify an account's Usage Triggers as a set. Pure, so the coverage rules
    can be tested without a network.

    The finding is about the set rather than about any one trigger: an account
    with six triggers and no recurring price cap is as unalarmed as an account
    with none, and the report has to say so.

    Returns (state, detail).
    """
    triggers = list(triggers or [])
    if not triggers:
        return ("none",
                "no usage triggers on this account: nothing on Twilio's side is "
                "watching spend or volume, and nothing will be until somebody "
                "creates one.")

    live = [t for t in triggers if fires_again(t) and has_callback(t)]
    if not live:
        if any(fires_again(t) for t in triggers):
            return ("no-callback",
                    "%d recurring trigger(s), none with a callback_url: the "
                    "threshold is evaluated and no request is ever made, so "
                    "nothing reaches whoever is on call."
                    % len([t for t in triggers if fires_again(t)]))
        fired = [t for t in triggers if str(t.get("date_fired") or "").strip()]
        if fired:
            return ("spent",
                    "%d of %d trigger(s) have fired and none of them recur: the "
                    "fuse blew and was never replaced, and the account has been "
                    "unalarmed ever since." % (len(fired), len(triggers)))
        return ("one-shot",
                "%d trigger(s), none recurring: each fires exactly once and then "
                "sits in the API looking configured." % len(triggers))

    spend = [t for t in live
             if str(t.get("usage_category") or "").strip().lower() == SPEND_CATEGORY
             and by_price(t)]
    if spend:
        return ("covered",
                "%d recurring price trigger(s) on %s with a callback."
                % (len(spend), SPEND_CATEGORY))

    priced = [t for t in live if by_price(t)]
    if priced:
        cats = sorted({str(t.get("usage_category") or "?").strip().lower()
                       for t in priced})
        return ("category-only",
                "price triggers on %s but none on %s: money that leaves through "
                "any other category is unalarmed."
                % (", ".join(cats), SPEND_CATEGORY))

    return ("count-only",
            "%d live trigger(s), all measuring counts rather than price: the same "
            "segment count to a premium destination costs many times more, which "
            "is the whole point of a pumping attack." % len(live))


def suggested_cap(records, multiplier=3.0, floor=5.0):
    """A daily price cap taken from the busiest of the recent days.

    Pure, and separate from the fetch, because the number this prints ends up in
    somebody's repair command and the arithmetic behind it should be readable.
    """
    prices = []
    for record in records:
        try:
            prices.append(float(record.get("price") or 0.0))
        except (TypeError, ValueError):
            continue
    peak = max(prices) if prices else 0.0
    return round(max(floor, peak * multiplier), 2)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_triggers(session, account, limit=200):
    """Page Usage/Triggers. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts/%s/Usage/Triggers.json" % (BASE, account)
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("usage_triggers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def daily_spend(session, account, days):
    """One page of daily totalprice records, enough to find the busiest day."""
    start = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    page = get(session, "%s/Accounts/%s/Usage/Records/Daily.json" % (BASE, account),
               Category=SPEND_CATEGORY, StartDate=start, PageSize=100)
    return page.get("usage_records", [])


def describe(trigger):
    return "%s %s %s %s recurring=%s callback=%s" % (
        trigger.get("sid", "?"),
        trigger.get("usage_category", "?"),
        trigger.get("trigger_by", "?"),
        trigger.get("trigger_value", "?"),
        trigger.get("recurring") or "none",
        "yes" if has_callback(trigger) else "no",
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--suggest-cap", action="store_true",
                    help="read daily usage records and print a cap based on them")
    ap.add_argument("--days", type=int, default=30,
                    help="how many days of usage the suggested cap looks at")
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

    triggers = list_triggers(session, account)
    for trigger in triggers:
        log.info("  %s", describe(trigger))

    state, detail = verdict(triggers)
    if state == "covered":
        log.info("%-14s %s", state, detail)
        return 0

    log.warning("%-14s %s", state, detail)

    cap = "{daily cap}"
    if args.suggest_cap:
        cap = suggested_cap(daily_spend(session, account, args.days))
        log.warning("  busiest recent day times three: %s", cap)

    log.warning("  repair: POST %s/Accounts/%s/Usage/Triggers.json "
                "UsageCategory=totalprice TriggerBy=price TriggerValue=%s "
                "Recurring=daily CallbackUrl=https://your-app.example.com/usage "
                "CallbackMethod=POST", BASE, account, cap)
    log.warning("  then run this against every subaccount: triggers do not inherit")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-usage-trigger-audit.mjs",
"js": '''/**
 * Report a Twilio account with no Usage Trigger that can actually fire.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const SPEND_CATEGORY = 'totalprice';
const RECURRING = ['daily', 'monthly', 'yearly'];

/** True when the trigger resets itself rather than firing once and stopping. */
export function firesAgain(trigger) {
  return RECURRING.includes(String(trigger.recurring ?? '').trim().toLowerCase());
}

/** True when crossing the threshold results in a request to something. */
export function hasCallback(trigger) {
  return Boolean(String(trigger.callback_url ?? '').trim());
}

/** True when the threshold is money rather than a count of messages or calls. */
export function byPrice(trigger) {
  return String(trigger.trigger_by ?? '').trim().toLowerCase() === 'price';
}

/**
 * Classify an account's Usage Triggers as a set. Pure, so the coverage rules can
 * be tested without a network. Returns [state, detail].
 */
export function verdict(triggers) {
  const all = [...(triggers ?? [])];
  if (all.length === 0) {
    return ['none',
      "no usage triggers on this account: nothing on Twilio's side is watching " +
      'spend or volume, and nothing will be until somebody creates one.'];
  }

  const live = all.filter((t) => firesAgain(t) && hasCallback(t));
  if (live.length === 0) {
    const recurring = all.filter(firesAgain);
    if (recurring.length) {
      return ['no-callback',
        `${recurring.length} recurring trigger(s), none with a callback_url: the ` +
        'threshold is evaluated and no request is ever made, so nothing reaches ' +
        'whoever is on call.'];
    }
    const fired = all.filter((t) => String(t.date_fired ?? '').trim());
    if (fired.length) {
      return ['spent',
        `${fired.length} of ${all.length} trigger(s) have fired and none of them ` +
        'recur: the fuse blew and was never replaced, and the account has been ' +
        'unalarmed ever since.'];
    }
    return ['one-shot',
      `${all.length} trigger(s), none recurring: each fires exactly once and then ` +
      'sits in the API looking configured.'];
  }

  const spend = live.filter(
    (t) => String(t.usage_category ?? '').trim().toLowerCase() === SPEND_CATEGORY
      && byPrice(t));
  if (spend.length) {
    return ['covered',
      `${spend.length} recurring price trigger(s) on ${SPEND_CATEGORY} with a callback.`];
  }

  const priced = live.filter(byPrice);
  if (priced.length) {
    const cats = [...new Set(priced.map(
      (t) => String(t.usage_category ?? '?').trim().toLowerCase()))].sort();
    return ['category-only',
      `price triggers on ${cats.join(', ')} but none on ${SPEND_CATEGORY}: money ` +
      'that leaves through any other category is unalarmed.'];
  }

  return ['count-only',
    `${live.length} live trigger(s), all measuring counts rather than price: the ` +
    'same segment count to a premium destination costs many times more, which is ' +
    'the whole point of a pumping attack.'];
}

/** A daily price cap taken from the busiest of the recent days. Pure. */
export function suggestedCap(records, multiplier = 3.0, floor = 5.0) {
  const prices = (records ?? [])
    .map((r) => Number.parseFloat(r.price ?? '0'))
    .filter((n) => Number.isFinite(n));
  const peak = prices.length ? Math.max(...prices) : 0;
  return Math.round(Math.max(floor, peak * multiplier) * 100) / 100;
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

export async function listTriggers(auth, account, limit = 200) {
  let url = `${BASE}/Accounts/${account}/Usage/Triggers.json`;
  let params = { PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.usage_triggers ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

function describe(t) {
  return `${t.sid ?? '?'} ${t.usage_category ?? '?'} ${t.trigger_by ?? '?'} ` +
         `${t.trigger_value ?? '?'} recurring=${t.recurring || 'none'} ` +
         `callback=${hasCallback(t) ? 'yes' : 'no'}`;
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
  const suggest = process.argv.includes('--suggest-cap');

  const triggers = await listTriggers(auth, account);
  for (const t of triggers) console.log(`  ${describe(t)}`);

  const [state, detail] = verdict(triggers);
  if (state === 'covered') {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }
  console.warn(`${state.padEnd(14)} ${detail}`);

  let cap = '{daily cap}';
  if (suggest) {
    const since = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
    const page = await get(auth, `${BASE}/Accounts/${account}/Usage/Records/Daily.json`,
                           { Category: SPEND_CATEGORY, StartDate: since, PageSize: 100 });
    cap = suggestedCap(page.usage_records ?? []);
    console.warn(`  busiest recent day times three: ${cap}`);
  }

  console.warn(`  repair: POST ${BASE}/Accounts/${account}/Usage/Triggers.json ` +
               `UsageCategory=totalprice TriggerBy=price TriggerValue=${cap} ` +
               'Recurring=daily CallbackUrl=https://your-app.example.com/usage ' +
               'CallbackMethod=POST');
  console.warn('  then run this against every subaccount: triggers do not inherit');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that look like coverage in the console: a trigger that recurs but fires into nothing, a one-shot that has already been used up, and a count cap on an account whose exposure is priced per destination. Each of those reads as a configured alarm to a human scanning a list, and each leaves the account exactly as unwatched as an empty response.",
"test_py_file": "test_twilio_usage_trigger_audit.py",
"test_py": '''from twilio_usage_trigger_audit import suggested_cap, verdict


def make(**kw):
    trigger = {"sid": "UT01", "usage_category": "totalprice", "trigger_by": "price",
               "trigger_value": "250", "recurring": "daily",
               "callback_url": "https://ops.example.com/twilio-usage"}
    trigger.update(kw)
    return trigger


def test_an_account_with_no_triggers_is_the_worst_answer():
    state, detail = verdict([])
    assert state == "none"
    assert "nothing" in detail


def test_a_recurring_price_trigger_with_a_callback_is_coverage():
    state, _ = verdict([make()])
    assert state == "covered"


def test_a_one_shot_trigger_that_already_fired_is_a_spent_fuse():
    state, detail = verdict([make(recurring=None,
                                  date_fired="Tue, 18 Apr 2023 09:12:00 +0000")])
    assert state == "spent"
    assert "fuse" in detail


def test_a_one_shot_that_has_not_fired_yet_is_still_not_an_alarm():
    state, _ = verdict([make(recurring="")])
    assert state == "one-shot"


def test_a_recurring_trigger_with_no_callback_url_reaches_nobody():
    state, detail = verdict([make(callback_url="")])
    assert state == "no-callback"
    assert "on call" in detail


def test_price_triggers_on_a_category_but_not_on_totalprice():
    state, detail = verdict([make(usage_category="sms")])
    assert state == "category-only"
    assert "sms" in detail


def test_counting_messages_is_not_capping_money():
    state, detail = verdict([make(trigger_by="count")])
    assert state == "count-only"
    assert "premium" in detail


def test_one_live_price_trigger_outweighs_the_dead_ones_around_it():
    state, _ = verdict([make(recurring=None), make(callback_url=""), make()])
    assert state == "covered"


def test_suggested_cap_is_the_busiest_day_times_three():
    records = [{"price": "12.50"}, {"price": "40.00"}, {"price": "3.10"}]
    assert suggested_cap(records) == 120.0


def test_suggested_cap_falls_back_to_the_floor_on_a_quiet_account():
    assert suggested_cap([]) == 5.0
    assert suggested_cap([{"price": None}, {"price": "not a number"}]) == 5.0
''',
"test_js_file": "twilio-usage-trigger-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { suggestedCap, verdict } from './twilio-usage-trigger-audit.mjs';

const make = (over = {}) => ({
  sid: 'UT01',
  usage_category: 'totalprice',
  trigger_by: 'price',
  trigger_value: '250',
  recurring: 'daily',
  callback_url: 'https://ops.example.com/twilio-usage',
  ...over,
});

test('an account with no triggers is the worst answer', () => {
  const [state, detail] = verdict([]);
  assert.equal(state, 'none');
  assert.match(detail, /nothing/);
});

test('a recurring price trigger with a callback is coverage', () => {
  assert.equal(verdict([make()])[0], 'covered');
});

test('a one-shot trigger that already fired is a spent fuse', () => {
  const [state, detail] = verdict([
    make({ recurring: null, date_fired: 'Tue, 18 Apr 2023 09:12:00 +0000' })]);
  assert.equal(state, 'spent');
  assert.match(detail, /fuse/);
});

test('a one-shot that has not fired yet is still not an alarm', () => {
  assert.equal(verdict([make({ recurring: '' })])[0], 'one-shot');
});

test('a recurring trigger with no callback_url reaches nobody', () => {
  const [state, detail] = verdict([make({ callback_url: '' })]);
  assert.equal(state, 'no-callback');
  assert.match(detail, /on call/);
});

test('price triggers on a category but not on totalprice', () => {
  const [state, detail] = verdict([make({ usage_category: 'sms' })]);
  assert.equal(state, 'category-only');
  assert.match(detail, /sms/);
});

test('counting messages is not capping money', () => {
  const [state, detail] = verdict([make({ trigger_by: 'count' })]);
  assert.equal(state, 'count-only');
  assert.match(detail, /premium/);
});

test('one live price trigger outweighs the dead ones around it', () => {
  assert.equal(
    verdict([make({ recurring: null }), make({ callback_url: '' }), make()])[0],
    'covered');
});

test('suggested cap is the busiest day times three', () => {
  assert.equal(suggestedCap([{ price: '12.50' }, { price: '40.00' }, { price: '3.10' }]),
               120.0);
});

test('suggested cap falls back to the floor on a quiet account', () => {
  assert.equal(suggestedCap([]), 5.0);
  assert.equal(suggestedCap([{ price: null }, { price: 'not a number' }]), 5.0);
});
''',
"faq": [
 ("Does Twilio really not warn me by default?",
  "Not in a way you can rely on or assert through the API. There are balance emails to the account owner's address, which is a mailbox and not a pager, and there is nothing at all keyed to a daily rate of spend. The Usage Trigger is the only alarm that exists as a resource you can read back and prove is there, which is why this check is about that resource and not about your inbox."),
 ("What number should the trigger value be?",
  "Three times your busiest recent day is a reasonable start, with a floor so that a quiet account still gets a usable threshold. The point is not precision. A cap set at ten times normal still catches a pumping burst inside the first hour, and a cap set too tight gets muted after the third false alarm, which leaves you exactly where you started."),
 ("Does a Usage Trigger stop the traffic?",
  "No, and this is the part people get wrong. It fires a webhook. Nothing is blocked, nothing is suspended, no sender is disabled. Containment is your own code reacting to that webhook, or a human in the console. Treat the trigger as the smoke detector, not the sprinkler, and write the handler that actually turns off the sender."),
 ("Why does the script care about callback_url when the console shows alerts?",
  "Because the console is a place someone has to be looking. A trigger with no callback_url has a threshold that is evaluated and an outcome that reaches nobody at three in the morning on a Saturday, which is when this failure happens. The URL is the difference between a record of the event and a response to it."),
 ("Do I need one per subaccount?",
  "Yes. Usage Triggers are a subresource of an account, and a trigger created on the parent is evaluated against the parent's usage records. If you split tenants into subaccounts, every one of them is a fresh account with no alarm on it, so this script wants to run per account SID rather than once at the top."),
],
"related": [
 ("/twilio/sms-pumping-protection-30450/", "SMS pumping traffic that bills before it is blocked"),
 ("/twilio/messaging-queue-overflow-30001/", "A queue overflowing because sends outran throughput"),
 ("/twilio/idle-phone-numbers-billed/", "Numbers billed every month for carrying nothing"),
],
"citations": [CITE_TRIGGER, CITE_RECORD, CITE_FRAUD, CITE_KEYS],
},

{
"slug": "auth-token-used-instead-of-api-key",
"title": "No API keys exist, so the auth token is the credential",
"description": "The auth token authenticates every service and signs every webhook, so rotating it is account-wide and instant. Find out whether anything still holds it.",
"h1": "no API keys exist, so the auth token is the credential",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio auth token vs api key", "twilio api key sk", "twilio 20003",
             "rotate twilio auth token", "x-twilio-signature auth token"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every other note in this section tells you to run its script with an API Key that has read access rather than the account auth token. This is the one that explains why, and how to find out whether anything you run is still holding the token. Nothing is failing right now. That is the shape of the problem: it costs you nothing until the day you have to rotate, and then it costs you everything at once.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/Keys.json</code>. An empty <code>keys[]</code> is conclusive: there is no API key on the account, so whatever authenticates to Twilio is presenting the account auth token.</p>
<p>For the harder question &mdash; which of your deployments still holds it &mdash; look at the basic-auth username rather than the password. A username beginning <code>SK</code> is an API Key SID. A username that is the account SID, beginning <code>AC</code>, means the password beside it is the auth token. There is no field anywhere in the API that reports this; it is in your configuration, and the script reads the one instance it can see for certain, which is its own.</p>""",
"problem": """<p>The account auth token is a single secret that does two unrelated jobs. It is the password for every REST call your services make, and it is the HMAC key Twilio uses to sign inbound webhooks in <code>X-Twilio-Signature</code>. Those two jobs have completely different lifecycles and completely different exposure, and one string covers both.</p>
<p>So the failure is not an outage today, it is the shape of the outage later. A token that appears in a log line, a screenshot, a support ticket or a departing contractor's shell history has to be rotated, and rotating it revokes access for every service simultaneously and changes the signing key for every webhook receiver at the same moment. Anything you miss starts returning <code>20003</code> immediately, with no grace period and no per-service fallback. The blast radius of the fix is the whole integration, which is exactly why the fix keeps getting postponed and the token keeps living in more places.</p>""",
"why": """<p><strong>The auth token is the credential the console hands you.</strong> It sits on the dashboard next to the account SID, it is what every quickstart pastes into a <code>.env</code>, and it works immediately for everything. Creating an API key is a deliberate extra step that nothing prompts you to take, so the default state of a working integration is one secret shared everywhere.</p>
<p><strong>One secret, two jobs, one lifecycle.</strong> You cannot rotate the REST credential without also rotating the webhook signing key, because they are the same string. A rotation therefore has to be coordinated across the services that call Twilio and the services Twilio calls, in the same window, which is a change nobody wants to schedule.</p>
<p><strong>Revocation has no granularity.</strong> An API key can be deleted on its own: one service loses access and everything else carries on. The auth token cannot. Killing a compromised credential and killing your production traffic are the same action.</p>
<p><strong>The API cannot tell you where a credential is used.</strong> <code>Keys.json</code> lists which keys exist. There is no last-used timestamp, no per-key request log, and nothing that maps a key to a deployment. That is a real blind spot, not a gap in the script, and it is why the useful signal is the username your own clients present rather than anything you can query.</p>
<p><strong>Fewer keys than services means sharing.</strong> If one key is spread across six deployments, deleting it takes down six things, which puts you back in exactly the position the key was supposed to get you out of. Counting keys against separately deployed workloads is a rough measure and a useful one.</p>""",
"steps": [
 {"h": "Read the keys that exist",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Keys.json?PageSize=50</code>, following <code>next_page_uri</code>. Each entry has <code>sid</code>, <code>friendly_name</code>, <code>date_created</code> and <code>date_updated</code>. An empty list ends the question: nothing but the auth token is in use.</p>"""},
 {"h": "Look at the username, not the password",
  "body": """<p>Every client that authenticates to the Twilio REST API sends HTTP basic auth. The username is either an <code>SK</code> key SID or the <code>AC</code> account SID, and there is no third option. The script classifies the credential it was given, which proves at minimum that this one shell is or is not on a key. For the rest, audit configuration: grep your secret store and deployment manifests for <code>TWILIO_AUTH_TOKEN</code> and for any Twilio client constructed with the account SID as its username.</p>"""},
 {"h": "Count the workloads that should have their own key",
  "body": """<p>There is no exact number, so use an upper bound you can read: <code>GET https://messaging.twilio.com/v1/Services</code> and <code>GET /2010-04-01/Accounts/{AccountSid}/Applications.json</code>. If you have eight of those between them and two keys, at least some deployments are sharing a credential. Override the count with <code>--workloads</code> when you know the real answer.</p>"""},
 {"h": "Leave the auth token exactly one job",
  "body": """<p>Signature validation. The service that receives Twilio's webhooks needs the auth token to verify <code>X-Twilio-Signature</code>, and that is the only place it should exist. Everything making outbound calls moves to a key of its own, named after the thing that holds it.</p>"""},
 {"h": "Migrate one service at a time, and verify by deleting",
  "body": """<p><code>POST /2010-04-01/Accounts/{AccountSid}/Keys.json</code> with <code>FriendlyName</code> set to the service name; store the returned <code>sid</code> and <code>secret</code> as the basic-auth pair. The proof that a service moved is that deleting its old key breaks only that service. That is a test you can run deliberately in a maintenance window, which is the whole difference from rotating an auth token.</p>"""},
],
"verify": """<p>Re-run the script with a key rather than the token. It should report <code>keyed</code> and exit zero.</p>
<pre><code class="language-bash">python3 twilio_credential_audit.py
# keyed          6 API key(s) for 5 workload(s).</code></pre>""",
"code_intro": "Three GETs &mdash; the keys, the Messaging Services and the TwiML Applications &mdash; plus one fact the API will never give you, which this script gets for free: the username it authenticated with. If that username is the account SID, the password beside it was the auth token, and the report says so before it says anything else. The classifier is pure and takes the credential kind as an argument, so all four outcomes can be exercised offline.",
"py_file": "twilio_credential_audit.py",
"py": '''"""Report whether a Twilio account is still running on its auth token.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. If you give it the auth token, it will tell
you so, which is the point.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_credential_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"


def credential_kind(username):
    """Which Twilio credential a basic-auth username implies.

    Every client that talks to the REST API sends basic auth, and the username is
    either an SK API Key SID or the AC account SID. If it is the account SID then
    the password beside it is the account auth token: there is no other password
    that pairs with it. No API field reports this, so the username is the only
    read-only tell there is.
    """
    u = str(username or "").strip().upper()
    if u.startswith("SK"):
        return "api-key"
    if u.startswith("AC"):
        return "auth-token"
    return "unknown"


def verdict(keys, workloads=0, running_as="unknown"):
    """Classify the account's credential posture. Pure, so all four outcomes can
    be tested without a network.

    Order matters: running under the auth token is proof, while a key count is
    inference, and the report should lead with whichever it actually knows.

    Returns (state, detail).
    """
    keys = list(keys or [])
    if running_as == "auth-token":
        return ("auth-token",
                "this run authenticated with the account SID as its basic-auth "
                "username, so the password was the account auth token. That is "
                "proof rather than inference: at least one deployment, this one, "
                "holds the account-wide secret. %d API key(s) exist." % len(keys))

    if not keys:
        return ("no-keys",
                "the account has no API keys, so every service that talks to "
                "Twilio is presenting the auth token: one secret, no per-service "
                "revocation, and the same value that signs your webhooks.")

    if workloads and len(keys) < workloads:
        return ("under-keyed",
                "%d API key(s) for %d separately deployed thing(s): some of them "
                "share a credential, and a shared credential cannot be revoked "
                "for one service without breaking the others."
                % (len(keys), workloads))

    return ("keyed", "%d API key(s) for %d workload(s)." % (len(keys), workloads))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "credential belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_keys(session, account, limit=200):
    """Page Keys.json. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts/%s/Keys.json" % (BASE, account)
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("keys", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def count_workloads(session, account):
    """An upper bound on how many separate credentials the account should have.

    Messaging Services and TwiML Applications are a proxy for deployed things,
    not a census of them. It is a rough number and the flag exists to replace it.
    """
    services = get(session, "%s/Services" % MESSAGING, PageSize=50)
    apps = get(session, "%s/Accounts/%s/Applications.json" % (BASE, account),
               PageSize=50)
    return len(services.get("services", [])) + len(apps.get("applications", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workloads", type=int, default=None,
                    help="how many services should have their own key; "
                         "skips the Messaging Service and Application count")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    running_as = credential_kind(key)
    log.info("this run is authenticating as: %s", running_as)

    session = requests.Session()
    session.auth = (key, secret)

    keys = list_keys(session, account)
    for entry in keys:
        log.info("  %s  %s  created %s", entry.get("sid", "?"),
                 entry.get("friendly_name") or "(unnamed)",
                 entry.get("date_created", "?"))

    workloads = args.workloads
    if workloads is None:
        workloads = count_workloads(session, account)

    state, detail = verdict(keys, workloads, running_as)
    if state == "keyed":
        log.info("%-12s %s", state, detail)
        return 0

    log.warning("%-12s %s", state, detail)
    log.warning("  repair: POST %s/Accounts/%s/Keys.json FriendlyName={service-name}, "
                "then store the returned sid and secret as the basic-auth pair",
                BASE, account)
    log.warning("  keep the auth token for X-Twilio-Signature validation and "
                "nowhere else")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-credential-audit.mjs",
"js": '''/**
 * Report whether a Twilio account is still running on its auth token.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. If you give it the auth token, it
 * will tell you so, which is the point.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

/**
 * Which Twilio credential a basic-auth username implies. An SK username is an
 * API Key SID; the AC account SID as a username means the password beside it is
 * the account auth token. No API field reports this, so the username is the only
 * read-only tell there is.
 */
export function credentialKind(username) {
  const u = String(username ?? '').trim().toUpperCase();
  if (u.startsWith('SK')) return 'api-key';
  if (u.startsWith('AC')) return 'auth-token';
  return 'unknown';
}

/**
 * Classify the account's credential posture. Pure, so all four outcomes can be
 * tested without a network. Returns [state, detail].
 */
export function verdict(keys, workloads = 0, runningAs = 'unknown') {
  const all = [...(keys ?? [])];
  if (runningAs === 'auth-token') {
    return ['auth-token',
      'this run authenticated with the account SID as its basic-auth username, ' +
      'so the password was the account auth token. That is proof rather than ' +
      'inference: at least one deployment, this one, holds the account-wide ' +
      `secret. ${all.length} API key(s) exist.`];
  }

  if (all.length === 0) {
    return ['no-keys',
      'the account has no API keys, so every service that talks to Twilio is ' +
      'presenting the auth token: one secret, no per-service revocation, and the ' +
      'same value that signs your webhooks.'];
  }

  if (workloads && all.length < workloads) {
    return ['under-keyed',
      `${all.length} API key(s) for ${workloads} separately deployed thing(s): ` +
      'some of them share a credential, and a shared credential cannot be revoked ' +
      'for one service without breaking the others.'];
  }

  return ['keyed', `${all.length} API key(s) for ${workloads} workload(s).`];
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
                    'that the credential belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listKeys(auth, account, limit = 200) {
  let url = `${BASE}/Accounts/${account}/Keys.json`;
  let params = { PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.keys ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function countWorkloads(auth, account) {
  const services = await get(auth, `${MESSAGING}/Services`, { PageSize: 50 });
  const apps = await get(auth, `${BASE}/Accounts/${account}/Applications.json`,
                         { PageSize: 50 });
  return (services.services ?? []).length + (apps.applications ?? []).length;
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

  const runningAs = credentialKind(key);
  console.log(`this run is authenticating as: ${runningAs}`);

  const auth = authHeader(key, secret);
  const keys = await listKeys(auth, account);
  for (const entry of keys) {
    console.log(`  ${entry.sid ?? '?'}  ${entry.friendly_name || '(unnamed)'}  ` +
                `created ${entry.date_created ?? '?'}`);
  }

  const flag = process.argv.indexOf('--workloads');
  const workloads = flag === -1
    ? await countWorkloads(auth, account)
    : Number.parseInt(process.argv[flag + 1], 10);

  const [state, detail] = verdict(keys, workloads, runningAs);
  if (state === 'keyed') {
    console.log(`${state.padEnd(12)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(12)} ${detail}`);
  console.warn(`  repair: POST ${BASE}/Accounts/${account}/Keys.json ` +
               'FriendlyName={service-name}, then store the returned sid and ' +
               'secret as the basic-auth pair');
  console.warn('  keep the auth token for X-Twilio-Signature validation and ' +
               'nowhere else');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth pinning here. The username classification, because everything else in the note rests on <code>SK</code> against <code>AC</code> and on it surviving whatever casing and stray whitespace an environment variable arrives with. And the precedence: an account with keys is still running on the auth token if this process authenticated with one, and the report has to lead with the thing it knows rather than the thing it inferred.",
"test_py_file": "test_twilio_credential_audit.py",
"test_py": '''from twilio_credential_audit import credential_kind, verdict

KEY = {"sid": "SK00000000000000000000000000000001", "friendly_name": "billing-worker"}


def test_an_sk_username_is_an_api_key():
    assert credential_kind("SK00000000000000000000000000000001") == "api-key"


def test_an_account_sid_as_the_username_means_the_auth_token():
    assert credential_kind("AC00000000000000000000000000000001") == "auth-token"


def test_case_and_whitespace_do_not_change_the_answer():
    assert credential_kind("  sk0123456789  ") == "api-key"
    assert credential_kind("ac0123456789") == "auth-token"


def test_an_empty_or_odd_username_is_not_guessed_at():
    assert credential_kind("") == "unknown"
    assert credential_kind(None) == "unknown"
    assert credential_kind("username") == "unknown"


def test_no_keys_at_all_is_the_headline_finding():
    state, detail = verdict([], workloads=4)
    assert state == "no-keys"
    assert "signs your webhooks" in detail


def test_running_under_the_auth_token_outranks_a_healthy_key_count():
    # Six keys and a tidy account, and this shell still holds the account secret.
    state, detail = verdict([KEY] * 6, workloads=3, running_as="auth-token")
    assert state == "auth-token"
    assert "proof" in detail


def test_fewer_keys_than_workloads_means_a_shared_credential():
    state, detail = verdict([KEY, KEY], workloads=7, running_as="api-key")
    assert state == "under-keyed"
    assert "share a credential" in detail


def test_a_key_per_workload_passes():
    state, _ = verdict([KEY] * 5, workloads=5, running_as="api-key")
    assert state == "keyed"


def test_an_unknown_workload_count_does_not_manufacture_a_finding():
    state, _ = verdict([KEY], workloads=0, running_as="api-key")
    assert state == "keyed"
''',
"test_js_file": "twilio-credential-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { credentialKind, verdict } from './twilio-credential-audit.mjs';

const KEY = { sid: 'SK00000000000000000000000000000001', friendly_name: 'billing-worker' };
const keys = (n) => Array.from({ length: n }, () => KEY);

test('an SK username is an api key', () => {
  assert.equal(credentialKind('SK00000000000000000000000000000001'), 'api-key');
});

test('an account sid as the username means the auth token', () => {
  assert.equal(credentialKind('AC00000000000000000000000000000001'), 'auth-token');
});

test('case and whitespace do not change the answer', () => {
  assert.equal(credentialKind('  sk0123456789  '), 'api-key');
  assert.equal(credentialKind('ac0123456789'), 'auth-token');
});

test('an empty or odd username is not guessed at', () => {
  assert.equal(credentialKind(''), 'unknown');
  assert.equal(credentialKind(null), 'unknown');
  assert.equal(credentialKind('username'), 'unknown');
});

test('no keys at all is the headline finding', () => {
  const [state, detail] = verdict([], 4);
  assert.equal(state, 'no-keys');
  assert.match(detail, /signs your webhooks/);
});

test('running under the auth token outranks a healthy key count', () => {
  const [state, detail] = verdict(keys(6), 3, 'auth-token');
  assert.equal(state, 'auth-token');
  assert.match(detail, /proof/);
});

test('fewer keys than workloads means a shared credential', () => {
  const [state, detail] = verdict(keys(2), 7, 'api-key');
  assert.equal(state, 'under-keyed');
  assert.match(detail, /share a credential/);
});

test('a key per workload passes', () => {
  assert.equal(verdict(keys(5), 5, 'api-key')[0], 'keyed');
});

test('an unknown workload count does not manufacture a finding', () => {
  assert.equal(verdict(keys(1), 0, 'api-key')[0], 'keyed');
});
''',
"faq": [
 ("Can I not just rotate the auth token and be done?",
  "You can rotate it, and it is instant and account-wide. Every deployment that was not updated in the same window starts returning 20003 with no fallback, and your webhook receivers begin rejecting Twilio's signatures at the same moment because the signing key changed underneath them. Twilio provides a secondary auth token so the change can be staged rather than done as a cutover, but staged or not, the unit of change is the entire account. That is the property an API key removes."),
 ("What is the auth token still for, then?",
  "Validating X-Twilio-Signature on inbound webhooks. Twilio signs those with the account auth token, so the service that receives them needs it and nothing else does. Keeping it in exactly one place, held by exactly one service, turns a shared password into a signing secret with a single consumer."),
 ("How do I find every place it is still used, given there is no last-used field?",
  "By reading configuration rather than the API, and the tell is the username. Any Twilio client constructed with the account SID as its username is sending the auth token as the password. Grep the secret store, the deployment manifests and the CI variables for TWILIO_AUTH_TOKEN, and for account SIDs appearing where a credential is expected. The script proves the case for one process, its own; the rest is an audit of your own repos."),
 ("Are API keys actually less privileged than the auth token?",
  "A standard key carries the same REST privileges the auth token does, so the win is not least privilege by default. The win is revocation scope: deleting one key takes down one service, at a moment you chose. Twilio also offers restricted keys with per-resource permissions where the product supports them, and a read-scoped key is what every script in this section asks for, because a leaked read key exposes your configuration rather than your ability to send."),
 ("Should this fail a CI job?",
  "It exits non-zero on anything but keyed, which makes it usable as a gate. The more valuable placement is a scheduled run rather than a pipeline step, because this state does not change when you deploy. It changes when somebody adds a service in a hurry, and that is a Tuesday, not a release."),
],
"related": [
 ("/twilio/stale-or-orphaned-api-keys/", "Old API keys still live with nobody owning them"),
 ("/twilio/status-callback-webhook-failing-11200/", "Status callbacks failing with error 11200"),
 ("/twilio/no-usage-trigger-configured/", "No spend alarm on an account that can spend"),
],
"citations": [CITE_KEYS, CITE_SECURE, CITE_SIGNATURE, CITE_KEY_RESOURCE],
},

{
"slug": "stale-or-orphaned-api-keys",
"title": "Years-old API keys are still live with nobody owning them",
"description": "API keys never expire and carry no last-used timestamp. Find the nameless ones, and know what deleting one takes down before you delete it.",
"h1": "years-old API keys are still live with nobody owning them",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio api key rotation", "twilio unused api key", "twilio 20003 after deleting key",
             "twilio keys.json friendly_name", "twilio access token invalidated"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "There are eleven keys on the account. Four have names. One of the unnamed ones was created in March 2023 by a contractor whose email address stopped working two years ago, and nobody can say what it authenticates. It has never expired, because Twilio keys do not. It has no last-used timestamp, because that field does not exist. And deleting it to find out will also invalidate every Access Token it ever signed.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/Keys.json</code> and, per entry, look at <code>sid</code>, <code>friendly_name</code>, <code>date_created</code> and <code>date_updated</code>. Flag any key whose name is empty or a placeholder, and any key created before your rotation window.</p>
<p>Those four fields are all there is. There is no expiry, no last-used timestamp and no per-key request count, so the audit is about ownership rather than activity: a named key belongs to something and can be retired deliberately, an unnamed one cannot be retired at all.</p>
<p><code>date_created</code> comes back in RFC 2822 on this API, not ISO 8601. Parse it as such or your age comparison silently returns nothing.</p>""",
"problem": """<p>API keys accumulate and never leave. One from the original integration, one from a load test, one from the Zapier connector somebody set up for the sales team, three from a migration that took two attempts, and several with no name at all because the console does not insist on one. Each of them is a full-privilege path into an account that can send messages and spend money, held by a person or a process nobody has an inventory of.</p>
<p>The reason this stays unfixed is not laziness, it is that deletion is genuinely dangerous and nobody can measure the danger. Removing a key immediately revokes REST access for whatever was using it, with a <code>20003</code> and no grace period, and it also invalidates every Access Token that was signed with that key's secret &mdash; so browser and mobile clients holding a live Voice or Video token drop as well. The API will not tell you whether anything is using the key. So the safe move looks like leaving it, and the set grows for another year.</p>""",
"why": """<p><strong>Keys have no lifecycle.</strong> They do not expire, they are not reviewed, and nothing in the account ages them out. Creating one is a two-field form; retiring one is an act of research. That asymmetry is the whole reason the count only ever goes up.</p>
<p><strong>There is no last-used field, on any Twilio resource.</strong> This is the blind spot that shapes the entire check. You cannot ask which keys are live, so the audit has to be about whether a human can account for the key, which means the name is the control and an empty name is the finding.</p>
<p><strong><code>date_updated</code> is not activity.</strong> It moves when the friendly name is edited, and not when the key is used. Reading it as a last-seen timestamp is the specific mistake that keeps a dead key alive for another cycle, because a key renamed last month looks recently active and is not.</p>
<p><strong>Deleting reaches further than REST.</strong> The key's secret signs Access Tokens for the client SDKs. Delete the key and every token signed with it stops validating, including tokens already issued to browsers that are mid-call. A key used only by a nightly script and a key underpinning your softphone look identical in <code>Keys.json</code>.</p>
<p><strong>The dates are in a format that quietly breaks comparisons.</strong> The 2010-04-01 API returns <code>Tue, 18 Apr 2023 09:12:00 +0000</code>. Newer Twilio domains return ISO 8601. A parser written for one and fed the other returns nothing, and a report with no findings reads exactly like a clean account.</p>""",
"steps": [
 {"h": "List every key, following the pages",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Keys.json?PageSize=50</code> and follow <code>next_page_uri</code>, which is a path rather than an absolute URL. Do this per subaccount too: keys belong to an account, and a subaccount's keys are invisible from the parent's list.</p>"""},
 {"h": "Parse the dates for the API you are actually calling",
  "body": """<p><code>date_created</code> and <code>date_updated</code> are RFC 2822 here. Python's <code>email.utils.parsedate_to_datetime</code> reads them; <code>datetime.fromisoformat</code> does not. Normalise to UTC before comparing, because a naive datetime compared against an aware one raises rather than returning a wrong answer, which is at least the better failure.</p>"""},
 {"h": "Judge on the name first and the age second",
  "body": """<p>A key called <code>billing-worker-prod</code> that is three years old is a rotation task. A key with no name at all, or called <code>Untitled</code>, is a different and worse thing: there is no path from that key to a person, so it cannot be retired safely at any age.</p>"""},
 {"h": "Rename before you delete",
  "body": """<p><code>friendly_name</code> is the only ownership record the resource has, and renaming is reversible in a way that deleting is not. Give every key an owner and a purpose, wait a cycle to see whether anybody claims one, and only then remove what is still unclaimed.</p>"""},
 {"h": "Delete one, watch for 20003, then do the next",
  "body": """<p><code>DELETE /2010-04-01/Accounts/{AccountSid}/Keys/{KeySid}</code> takes effect immediately and cannot be undone; a new key is a new SID and a new secret. Remove one key per change window and watch the Alerts for <code>20003</code>, and remember that anything holding an Access Token signed by that key loses it at the same moment.</p>"""},
],
"verify": """<p>Re-run the script. Every key should report <code>current</code> with a name that identifies its owner.</p>
<pre><code class="language-bash">python3 twilio_api_key_audit.py --max-age-days 365
# 6 key(s), 0 unowned, 0 past the rotation window</code></pre>""",
"code_intro": "One paginated GET and two pure functions: the date parser, because the RFC 2822 format on this API is the thing that silently empties the report, and the per-key verdict, because the rules about names and ages are the content of the note. An API Key with read access is enough; the audit will find itself in its own output, which is a good reason to have named it.",
"py_file": "twilio_api_key_audit.py",
"py": '''"""Report Twilio API keys that are old, unnamed, or otherwise unaccounted for.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because deleting a key revokes REST access immediately and invalidates every
Access Token that key's secret ever signed.
"""
import argparse
import datetime
import logging
import os
import sys
from email.utils import parsedate_to_datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_api_key_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# Names that identify nothing. A key wearing one of these cannot be traced to an
# owner, which is worse than a key that is merely old.
PLACEHOLDER_NAMES = {"", "untitled", "untitled key", "default", "key", "my key",
                     "test", "temp", "tmp", "quickstart", "new key", "api key"}


def parse_date(value):
    """Parse a Twilio timestamp into an aware UTC datetime.

    The 2010-04-01 API returns RFC 2822 ("Tue, 18 Apr 2023 09:12:00 +0000") while
    the newer Twilio domains return ISO 8601. Branch on the first characters
    rather than letting one parser guess at the other's format: a parser that
    returns nothing produces a report with no findings, which reads exactly like
    a clean account.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text[:4].isdigit():
        try:
            parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def age_days(key, now):
    """Days since the key was created, or None when the date will not parse."""
    created = parse_date(key.get("date_created"))
    if created is None:
        return None
    return (now - created).days


def verdict(key, now, max_age_days=365):
    """Classify one API key. Pure, so the rules can be tested without a network.

    There is no last-used timestamp on a Twilio key, on any Twilio resource. So
    this cannot ask whether a key is in use; it asks whether a human can account
    for it, which makes the name the control and an empty name the finding.

    Returns (state, detail).
    """
    name = str(key.get("friendly_name") or "").strip()
    sid = str(key.get("sid") or "").strip()

    if name.lower() in PLACEHOLDER_NAMES or (sid and name == sid):
        return ("unowned",
                "friendly_name is %s: nothing on the account records what this "
                "key authenticates, and a key nobody can account for is a key "
                "nobody will ever be willing to delete." % (name or "empty"))

    age = age_days(key, now)
    if age is None:
        return ("undated",
                "date_created did not parse (%s): this API returns RFC 2822, not "
                "ISO 8601. Treat the key as the oldest on the account until "
                "somebody establishes otherwise." % (key.get("date_created") or "empty"))

    if age > max_age_days:
        created = parse_date(key.get("date_created"))
        renamed = parse_date(key.get("date_updated"))
        untouched = (renamed is not None and created is not None and renamed <= created)
        return ("stale",
                "%s, created %d days ago, past the %d day rotation window%s."
                % (name, age, max_age_days,
                   "; date_updated has never moved, so nobody has even renamed it"
                   if untouched else ""))

    return ("current", "%s, created %d days ago." % (name, age))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_keys(session, account, limit=500):
    """Page Keys.json. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts/%s/Keys.json" % (BASE, account)
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("keys", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-age-days", type=int, default=365,
                    help="keys older than this are reported for rotation")
    ap.add_argument("--as-of", default=None,
                    help="ISO date to age keys against, for a reproducible run")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    now = parse_date(args.as_of) if args.as_of else None
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    session = requests.Session()
    session.auth = (key, secret)

    keys = list_keys(session, account)
    if not keys:
        log.info("no API keys on this account: see the note on the auth token")
        return 0

    unowned = stale = 0
    for entry in keys:
        state, detail = verdict(entry, now, args.max_age_days)
        line = "%-8s %s  %s" % (state, entry.get("sid", "?"), detail)
        if state == "current":
            log.info(line)
            continue
        if state == "unowned":
            unowned += 1
        else:
            stale += 1
        log.warning(line)
        log.warning("  repair: rename it first, POST %s/Accounts/%s/Keys/%s.json "
                    "FriendlyName={owner}-{service}; once a cycle has passed with "
                    "nobody claiming it, remove it with DELETE on the same resource",
                    BASE, account, entry.get("sid", "?"))
        log.warning("  deleting also invalidates every Access Token signed with "
                    "this key's secret, so client SDK sessions drop with it")

    log.info("%d key(s), %d unowned, %d past the rotation window",
             len(keys), unowned, stale)
    return 1 if (unowned or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-api-key-audit.mjs",
"js": '''/**
 * Report Twilio API keys that are old, unnamed, or otherwise unaccounted for.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed, because removing a key revokes REST access immediately and
 * invalidates every Access Token that key's secret ever signed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// Names that identify nothing. A key wearing one of these cannot be traced to an
// owner, which is worse than a key that is merely old.
const PLACEHOLDER_NAMES = new Set(['', 'untitled', 'untitled key', 'default', 'key',
  'my key', 'test', 'temp', 'tmp', 'quickstart', 'new key', 'api key']);

/**
 * Parse a Twilio timestamp. The 2010-04-01 API returns RFC 2822 while the newer
 * domains return ISO 8601; Date.parse reads both, and Twilio always sends an
 * explicit offset, so there is no local-time ambiguity to guard against.
 */
export function parseDate(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : new Date(ms);
}

/** Days since the key was created, or null when the date will not parse. */
export function ageDays(key, now) {
  const created = parseDate(key.date_created);
  if (created === null) return null;
  return Math.floor((now.getTime() - created.getTime()) / 86400000);
}

/**
 * Classify one API key. Pure, so the rules can be tested without a network.
 *
 * There is no last-used timestamp on a Twilio key, so this cannot ask whether a
 * key is in use. It asks whether a human can account for it, which makes the
 * name the control and an empty name the finding. Returns [state, detail].
 */
export function verdict(key, now, maxAgeDays = 365) {
  const name = String(key.friendly_name ?? '').trim();
  const sid = String(key.sid ?? '').trim();

  if (PLACEHOLDER_NAMES.has(name.toLowerCase()) || (sid && name === sid)) {
    return ['unowned',
      `friendly_name is ${name || 'empty'}: nothing on the account records what ` +
      'this key authenticates, and a key nobody can account for is a key nobody ' +
      'will ever be willing to delete.'];
  }

  const age = ageDays(key, now);
  if (age === null) {
    return ['undated',
      `date_created did not parse (${key.date_created || 'empty'}): this API ` +
      'returns RFC 2822, not ISO 8601. Treat the key as the oldest on the account ' +
      'until somebody establishes otherwise.'];
  }

  if (age > maxAgeDays) {
    const created = parseDate(key.date_created);
    const renamed = parseDate(key.date_updated);
    const untouched = renamed !== null && created !== null
      && renamed.getTime() <= created.getTime();
    return ['stale',
      `${name}, created ${age} days ago, past the ${maxAgeDays} day rotation ` +
      `window${untouched ? '; date_updated has never moved, so nobody has even renamed it' : ''}.`];
  }

  return ['current', `${name}, created ${age} days ago.`];
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

export async function listKeys(auth, account, limit = 500) {
  let url = `${BASE}/Accounts/${account}/Keys.json`;
  let params = { PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.keys ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
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

  const flag = process.argv.indexOf('--max-age-days');
  const maxAgeDays = flag === -1 ? 365 : Number.parseInt(process.argv[flag + 1], 10);
  const now = new Date();

  const auth = authHeader(key, secret);
  const keys = await listKeys(auth, account);
  if (keys.length === 0) {
    console.log('no API keys on this account: see the note on the auth token');
    return;
  }

  let unowned = 0;
  let stale = 0;
  for (const entry of keys) {
    const [state, detail] = verdict(entry, now, maxAgeDays);
    const line = `${state.padEnd(8)} ${entry.sid ?? '?'}  ${detail}`;
    if (state === 'current') { console.log(line); continue; }
    if (state === 'unowned') unowned += 1; else stale += 1;
    console.warn(line);
    console.warn(`  repair: rename it first, POST ${BASE}/Accounts/${account}/Keys/` +
                 `${entry.sid ?? '?'}.json FriendlyName={owner}-{service}; once a ` +
                 'cycle has passed with nobody claiming it, remove it with DELETE ' +
                 'on the same resource');
    console.warn('  deleting also invalidates every Access Token signed with this ' +
                 "key's secret, so client SDK sessions drop with it");
  }

  console.log(`${keys.length} key(s), ${unowned} unowned, ${stale} past the rotation window`);
  process.exitCode = (unowned || stale) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The date parsing gets its own tests because it is the failure that hides every other one: hand an ISO parser the RFC 2822 string this API actually returns and it reports nothing, and nothing is indistinguishable from a tidy account. The rest pin the precedence &mdash; an unnamed key is a finding whatever its age &mdash; and the <code>date_updated</code> case, which is the field most often mistaken for activity.",
"test_py_file": "test_twilio_api_key_audit.py",
"test_py": '''import datetime

from twilio_api_key_audit import age_days, parse_date, verdict

NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)


def make(**kw):
    key = {"sid": "SK00000000000000000000000000000001",
           "friendly_name": "billing-worker-prod",
           "date_created": "Sat, 01 Aug 2026 09:12:00 +0000",
           "date_updated": "Sat, 01 Aug 2026 09:12:00 +0000"}
    key.update(kw)
    return key


def test_the_2010_api_returns_rfc_2822_and_it_has_to_parse():
    parsed = parse_date("Tue, 18 Apr 2023 09:12:00 +0000")
    assert parsed == datetime.datetime(2023, 4, 18, 9, 12,
                                       tzinfo=datetime.timezone.utc)


def test_iso_8601_from_the_newer_domains_parses_too():
    parsed = parse_date("2023-04-18T09:12:00Z")
    assert parsed == datetime.datetime(2023, 4, 18, 9, 12,
                                       tzinfo=datetime.timezone.utc)


def test_an_unparseable_date_is_none_rather_than_a_wrong_answer():
    assert parse_date("last tuesday") is None
    assert parse_date("") is None
    assert parse_date(None) is None


def test_age_is_measured_in_whole_days_from_the_created_date():
    assert age_days(make(date_created="Thu, 30 Jul 2026 00:00:00 +0000"), NOW) == 31


def test_a_recently_created_named_key_is_current():
    state, _ = verdict(make(), NOW)
    assert state == "current"


def test_an_empty_friendly_name_is_unowned_whatever_its_age():
    state, detail = verdict(make(friendly_name="",
                                 date_created="Sat, 01 Aug 2026 09:12:00 +0000"), NOW)
    assert state == "unowned"
    assert "nobody can account for" in detail


def test_a_placeholder_name_counts_as_no_name():
    assert verdict(make(friendly_name="Untitled"), NOW)[0] == "unowned"
    assert verdict(make(friendly_name="  test  "), NOW)[0] == "unowned"


def test_a_key_named_after_its_own_sid_records_nothing():
    sid = "SK00000000000000000000000000000009"
    assert verdict(make(sid=sid, friendly_name=sid), NOW)[0] == "unowned"


def test_a_named_key_past_the_window_is_stale():
    state, detail = verdict(make(date_created="Wed, 15 Mar 2023 09:12:00 +0000",
                                 date_updated="Wed, 15 Mar 2023 09:12:00 +0000"),
                            NOW, max_age_days=365)
    assert state == "stale"
    assert "never moved" in detail


def test_date_updated_after_creation_is_a_rename_not_activity():
    # It moved, so the report drops the "never renamed" clause. It still says
    # nothing about whether the key has ever been used.
    state, detail = verdict(make(date_created="Wed, 15 Mar 2023 09:12:00 +0000",
                                 date_updated="Mon, 06 Jan 2025 11:00:00 +0000"),
                            NOW, max_age_days=365)
    assert state == "stale"
    assert "never moved" not in detail


def test_a_key_whose_date_will_not_parse_is_reported_not_skipped():
    state, detail = verdict(make(date_created="18/04/2023"), NOW)
    assert state == "undated"
    assert "RFC 2822" in detail
''',
"test_js_file": "twilio-api-key-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageDays, parseDate, verdict } from './twilio-api-key-audit.mjs';

const NOW = new Date('2026-08-30T00:00:00Z');

const make = (over = {}) => ({
  sid: 'SK00000000000000000000000000000001',
  friendly_name: 'billing-worker-prod',
  date_created: 'Sat, 01 Aug 2026 09:12:00 +0000',
  date_updated: 'Sat, 01 Aug 2026 09:12:00 +0000',
  ...over,
});

test('the 2010 api returns rfc 2822 and it has to parse', () => {
  assert.equal(parseDate('Tue, 18 Apr 2023 09:12:00 +0000').toISOString(),
               '2023-04-18T09:12:00.000Z');
});

test('iso 8601 from the newer domains parses too', () => {
  assert.equal(parseDate('2023-04-18T09:12:00Z').toISOString(),
               '2023-04-18T09:12:00.000Z');
});

test('an unparseable date is null rather than a wrong answer', () => {
  assert.equal(parseDate('last tuesday'), null);
  assert.equal(parseDate(''), null);
  assert.equal(parseDate(null), null);
});

test('age is measured in whole days from the created date', () => {
  assert.equal(ageDays(make({ date_created: 'Thu, 30 Jul 2026 00:00:00 +0000' }), NOW),
               31);
});

test('a recently created named key is current', () => {
  assert.equal(verdict(make(), NOW)[0], 'current');
});

test('an empty friendly name is unowned whatever its age', () => {
  const [state, detail] = verdict(make({ friendly_name: '' }), NOW);
  assert.equal(state, 'unowned');
  assert.match(detail, /nobody can account for/);
});

test('a placeholder name counts as no name', () => {
  assert.equal(verdict(make({ friendly_name: 'Untitled' }), NOW)[0], 'unowned');
  assert.equal(verdict(make({ friendly_name: '  test  ' }), NOW)[0], 'unowned');
});

test('a key named after its own sid records nothing', () => {
  const sid = 'SK00000000000000000000000000000009';
  assert.equal(verdict(make({ sid, friendly_name: sid }), NOW)[0], 'unowned');
});

test('a named key past the window is stale', () => {
  const [state, detail] = verdict(make({
    date_created: 'Wed, 15 Mar 2023 09:12:00 +0000',
    date_updated: 'Wed, 15 Mar 2023 09:12:00 +0000',
  }), NOW, 365);
  assert.equal(state, 'stale');
  assert.match(detail, /never moved/);
});

test('date_updated after creation is a rename not activity', () => {
  const [state, detail] = verdict(make({
    date_created: 'Wed, 15 Mar 2023 09:12:00 +0000',
    date_updated: 'Mon, 06 Jan 2025 11:00:00 +0000',
  }), NOW, 365);
  assert.equal(state, 'stale');
  assert.doesNotMatch(detail, /never moved/);
});

test('a key whose date will not parse is reported not skipped', () => {
  const [state, detail] = verdict(make({ date_created: 'not a date at all' }), NOW);
  assert.equal(state, 'undated');
  assert.match(detail, /RFC 2822/);
});
''',
"faq": [
 ("Why not just delete every key nobody claims?",
  "Because deletion reaches further than REST access. The key's secret signs Access Tokens for the client SDKs, so removing it invalidates every token signed with it, including ones already issued to browsers and handsets. A key used by a nightly report and a key underpinning your softphone are indistinguishable in Keys.json, which is why renaming comes first and deleting comes one key per change window."),
 ("Is there really no way to see whether a key is being used?",
  "Not from the API. There is no last-used timestamp, no per-key request count, and no field that maps a key to a deployment. That is the blind spot this check is built around: it cannot report activity, so it reports accountability instead. The nearest thing to evidence is deleting the key and watching for 20003, which is a test you run deliberately rather than discover."),
 ("Does date_updated tell me when the key was last used?",
  "No. It moves when the friendly name is edited and at no other time. Treating it as a last-seen timestamp is the most common reason a dead key survives a review: it was renamed during a tidy-up eight months ago, so it looks recently active, and it has authenticated nothing since 2023."),
 ("What is a sensible rotation window?",
  "Whatever you will actually keep to. A year is a defensible default for a small account and quarterly is normal where the keys map to deployments you can redeploy without ceremony. The number matters much less than every key having a name that says who owns it, because that is what turns rotation from research into a scheduled task."),
 ("What about the key this script is using?",
  "It appears in its own report, which is a good argument for giving it a name like fieldnotes-readonly-audit before you run it. If your own audit credential shows up as unowned, that is the finding working correctly."),
],
"related": [
 ("/twilio/auth-token-used-instead-of-api-key/", "Why the auth token should not be your credential"),
 ("/twilio/no-usage-trigger-configured/", "No spend alarm on an account that can spend"),
 ("/twilio/idle-phone-numbers-billed/", "Numbers billed every month for carrying nothing"),
],
"citations": [CITE_KEY_RESOURCE, CITE_KEYS, CITE_SECURE, CITE_SIGNATURE],
},

{
"slug": "regulatory-bundle-expiring",
"title": "An approved regulatory bundle is counting down to expiry",
"description": "The bundle proving your address to a regulator has a valid_until. It passes, the bundle is auto-rejected, and the numbers attached to it go non-compliant.",
"h1": "an approved regulatory bundle is counting down to expiry",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio regulatory bundle expiring", "twilio bundle valid_until",
             "twilio-approved bundle rejected", "twilio german numbers stopped",
             "twilio regulatory compliance api"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Eighteen months of German numbers working perfectly, and then one Tuesday they stop. Nothing was deployed. The bundle that proved your business address to the regulator reached its <code>valid_until</code>, flipped out of <code>twilio-approved</code> on its own, and the numbers attached to it are now non-compliant. There was a date, it was in the API the whole time, and nothing ever mentioned it.",
"short_answer": """<p>Read <code>GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles?HasValidUntilDate=true&amp;SortBy=valid-until&amp;SortDirection=ASC</code> and flag any bundle with <code>status</code> of <code>twilio-approved</code> whose <code>valid_until</code> falls inside your renewal window.</p>
<p><code>valid_until</code> is the whole check. Approval is a snapshot of documents a regulator accepted, not a permanent state, and when the date passes the bundle is rejected without anyone acting. A bundle with a null <code>valid_until</code> needs no re-attestation and is not a finding &mdash; treating null as expired buries the real ones under noise.</p>""",
"problem": """<p>Nothing is wrong today, and nothing will report that anything is wrong today. The bundle reads <code>twilio-approved</code>, the numbers send and receive, and the only evidence of the deadline is a timestamp sitting in a resource nobody reads between purchases. Meanwhile the clock is real: many national regulators require periodic re-attestation of the address and identity documents behind a number, and Twilio encodes that requirement as <code>valid_until</code> on the Bundle.</p>
<p>What makes it an outage rather than a chore is the lead time. Renewing is not a field you set. It is gathering current documents, uploading them, reassigning them to the bundle and resubmitting for review, and review takes as long as it takes. If you discover the date on the day it passes, you cannot fix it that week, and the numbers are already non-compliant and exposed to reclamation while you wait. This is the failure that ends with a country's worth of traffic gone and no deploy to blame it on.</p>""",
"why": """<p><strong>Approval is a snapshot, not a state.</strong> The regulator accepted a set of documents at a point in time. <code>twilio-approved</code> means that happened, not that it is still true, and the date on which it stops being true is the field almost nobody looks at.</p>
<p><strong>The deadline lives on the bundle, not on the number.</strong> Nothing in the phone-number API changes as the date approaches. If you monitor numbers, this is invisible right up until the numbers are the thing that broke.</p>
<p><strong>The transition happens without anybody acting.</strong> No human rejects the bundle. It ages out. So there is no ticket, no approval queue, no email thread &mdash; nothing that leaves the trace an ordinary compliance failure leaves.</p>
<p><strong>Renewal has a lead time that a short window cannot absorb.</strong> New documents, an item assignment, a resubmission and a review. A seven-day alert on a process that takes three weeks is an alert that tells you the outage is now unavoidable.</p>
<p><strong>The status callback fires too late to help.</strong> A <code>status_callback</code> on the bundle webhooks its transitions, which is genuinely useful and is not an early warning: it fires when the bundle has already changed state. Polling <code>valid_until</code> is the only thing that gives you warning rather than notification.</p>""",
"steps": [
 {"h": "List the bundles that have a date at all",
  "body": """<p><code>GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles</code> with <code>HasValidUntilDate=true</code>, <code>SortBy=valid-until</code> and <code>SortDirection=ASC</code>. The sort matters: the first page is then the bundles closest to expiry, which is the report you actually want to read.</p>"""},
 {"h": "Follow v2 pagination, which is not the 2010-04-01 shape",
  "body": """<p>This API returns results under <code>results</code> and the next page as an absolute URL in <code>meta.next_page_url</code>. Code written against the older account API looks for <code>next_page_uri</code> and a host prefix, finds neither, and stops after the first page &mdash; with the bundles sorted ascending, that at least fails in the safe direction, but only by accident.</p>"""},
 {"h": "Classify against a horizon that matches your renewal time",
  "body": """<p>Compare <code>valid_until</code> to now. Anything already past is an incident, not a warning. The window for the rest should be as long as gathering documents and waiting for review actually takes at your organisation, which is usually sixty to ninety days rather than seven.</p>"""},
 {"h": "Check status_callback while you are in the response",
  "body": """<p>An empty <code>status_callback</code> means the eventual transition is announced to nobody. It is not the reason this fails, but it is the reason it is discovered by a customer. Report it alongside the date rather than instead of it.</p>"""},
 {"h": "Refresh the documents, resubmit, then re-run",
  "body": """<p><code>POST /v2/RegulatoryCompliance/SupportingDocuments</code> for the current paperwork, reassign with <code>POST /v2/RegulatoryCompliance/Bundles/{BundleSid}/ItemAssignments</code>, then <code>POST /v2/RegulatoryCompliance/Bundles/{BundleSid}</code> with <code>Status=pending-review</code>. Run this audit on a schedule afterwards: the renewal you just completed sets a new <code>valid_until</code>, and the same date arrives again.</p>"""},
],
"verify": """<p>Re-run the script. Every approved bundle should report <code>current</code>, with the nearest date beyond your horizon.</p>
<pre><code class="language-bash">python3 twilio_bundle_expiry_audit.py --horizon-days 60
# 4 bundle(s), 0 expired, 0 inside the 60 day horizon</code></pre>""",
"code_intro": "One paginated GET, sorted by the field the whole note is about, and a pure classifier that keys on <code>valid_until</code>. The two states worth reading carefully are <code>no-expiry</code>, which is a healthy bundle under a regulation that needs no re-attestation, and <code>rejected</code>, which is what this failure looks like from the other side of the date.",
"py_file": "twilio_bundle_expiry_audit.py",
"py": '''"""Report regulatory Bundles whose approval is about to expire.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because resubmitting a bundle starts a review you want a human watching.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_bundle_expiry_audit")

NUMBERS = "https://numbers.twilio.com/v2"

APPROVED = "twilio-approved"
REJECTED = "twilio-rejected"


def parse_date(value):
    """Parse an ISO 8601 timestamp from the numbers v2 API into aware UTC.

    fromisoformat on Python 3.9 does not accept a trailing Z, and a naive
    datetime compared against an aware one raises rather than returning a wrong
    answer, so both are normalised here instead of at every call site.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def verdict(bundle, now, horizon_days=60):
    """Classify one Bundle on valid_until. Pure, so the dates can be tested
    without a network and without waiting eighteen months.

    valid_until is the field this whole check exists for: an approved bundle is
    approved as of a date, and when that date passes the bundle is rejected with
    nobody acting. A null valid_until is a regulation that needs no
    re-attestation, which is a healthy state and not a finding.

    Returns (state, detail).
    """
    status = str(bundle.get("status") or "").strip().lower()
    valid_until = parse_date(bundle.get("valid_until"))
    days = None if valid_until is None else (valid_until - now).days

    if status == REJECTED and days is not None and days < 0:
        return ("rejected",
                "valid_until passed %d day(s) ago and the bundle is now %s: this "
                "is the failure after the fact, and the numbers on this bundle "
                "are non-compliant today." % (-days, REJECTED))

    if status != APPROVED:
        return ("not-approved",
                "status is %s, so there is no approval to expire. That is a "
                "different problem from this one." % (status or "unset"))

    if valid_until is None:
        return ("no-expiry",
                "approved with no valid_until: this regulation does not require "
                "periodic re-attestation, so there is no date to watch.")

    if days < 0:
        return ("expired",
                "valid_until passed %d day(s) ago while the status still reads "
                "%s: the flip is not instantaneous, and the numbers on this "
                "bundle are already out of time." % (-days, APPROVED))

    if days <= horizon_days:
        return ("expiring",
                "valid_until is %d day(s) away. Renewal means new supporting "
                "documents, a reassignment and a review, so start now rather "
                "than on the date." % days)

    return ("current", "valid_until is %d day(s) away." % days)


def callback_note(bundle):
    """The reason this arrives as an outage rather than a notification, or None.

    A status_callback does not give warning, because it fires at the transition.
    It is still the difference between finding out at the moment the bundle
    changes and finding out from a customer.
    """
    if str(bundle.get("status_callback") or "").strip():
        return None
    return ("status_callback is unset: when this bundle changes state nothing is "
            "told, so the first signal will be numbers that stopped working.")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_bundles(session, only_dated=True, limit=500):
    """Page the Bundles list.

    The numbers v2 API returns rows under `results` and an absolute next page in
    `meta.next_page_url`, unlike the 2010-04-01 API's `next_page_uri` path.
    Sorted ascending on valid-until so the first page is the urgent one.
    """
    url = "%s/RegulatoryCompliance/Bundles" % NUMBERS
    params = {"SortBy": "valid-until", "SortDirection": "ASC", "PageSize": 50}
    if only_dated:
        params["HasValidUntilDate"] = "true"
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("results", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--horizon-days", type=int, default=60,
                    help="how far ahead an expiry counts as a finding")
    ap.add_argument("--all", action="store_true",
                    help="include bundles with no valid_until date")
    ap.add_argument("--as-of", default=None,
                    help="ISO date to measure against, for a reproducible run")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    now = parse_date(args.as_of) if args.as_of else None
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    session = requests.Session()
    session.auth = (key, secret)

    bundles = list_bundles(session, only_dated=not args.all)
    if not bundles:
        log.info("no regulatory bundles with a valid_until on this account")
        return 0

    expired = soon = 0
    for bundle in bundles:
        state, detail = verdict(bundle, now, args.horizon_days)
        label = "%s/%s" % (bundle.get("iso_country") or "??",
                           bundle.get("number_type") or "?")
        line = "%-12s %s  %s  %s" % (state, bundle.get("sid", "?"), label, detail)
        if state in ("current", "no-expiry", "not-approved"):
            log.info(line)
            continue
        if state in ("expired", "rejected"):
            expired += 1
        else:
            soon += 1
        log.warning(line)
        note = callback_note(bundle)
        if note:
            log.warning("  %s", note)
        log.warning("  repair: POST %s/RegulatoryCompliance/SupportingDocuments with "
                    "current paperwork, assign it via POST %s/RegulatoryCompliance/"
                    "Bundles/%s/ItemAssignments, then POST the bundle with "
                    "Status=pending-review", NUMBERS, NUMBERS, bundle.get("sid", "?"))

    log.info("%d bundle(s), %d expired, %d inside the %d day horizon",
             len(bundles), expired, soon, args.horizon_days)
    return 1 if (expired or soon) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-bundle-expiry-audit.mjs",
"js": '''/**
 * Report regulatory Bundles whose approval is about to expire.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed, because resubmitting a bundle starts a review you want a human
 * watching.
 */
const NUMBERS = 'https://numbers.twilio.com/v2';

const APPROVED = 'twilio-approved';
const REJECTED = 'twilio-rejected';

/** Parse an ISO 8601 timestamp from the numbers v2 API. */
export function parseDate(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : new Date(ms);
}

/**
 * Classify one Bundle on valid_until. Pure, so the dates can be tested without a
 * network and without waiting eighteen months.
 *
 * An approved bundle is approved as of a date, and when that date passes the
 * bundle is rejected with nobody acting. A null valid_until is a regulation that
 * needs no re-attestation: a healthy state, not a finding.
 *
 * Returns [state, detail].
 */
export function verdict(bundle, now, horizonDays = 60) {
  const status = String(bundle.status ?? '').trim().toLowerCase();
  const validUntil = parseDate(bundle.valid_until);
  const days = validUntil === null
    ? null
    : Math.floor((validUntil.getTime() - now.getTime()) / 86400000);

  if (status === REJECTED && days !== null && days < 0) {
    return ['rejected',
      `valid_until passed ${-days} day(s) ago and the bundle is now ${REJECTED}: ` +
      'this is the failure after the fact, and the numbers on this bundle are ' +
      'non-compliant today.'];
  }

  if (status !== APPROVED) {
    return ['not-approved',
      `status is ${status || 'unset'}, so there is no approval to expire. That is ` +
      'a different problem from this one.'];
  }

  if (validUntil === null) {
    return ['no-expiry',
      'approved with no valid_until: this regulation does not require periodic ' +
      're-attestation, so there is no date to watch.'];
  }

  if (days < 0) {
    return ['expired',
      `valid_until passed ${-days} day(s) ago while the status still reads ` +
      `${APPROVED}: the flip is not instantaneous, and the numbers on this bundle ` +
      'are already out of time.'];
  }

  if (days <= horizonDays) {
    return ['expiring',
      `valid_until is ${days} day(s) away. Renewal means new supporting documents, ` +
      'a reassignment and a review, so start now rather than on the date.'];
  }

  return ['current', `valid_until is ${days} day(s) away.`];
}

/** The reason this arrives as an outage rather than a notification, or null. */
export function callbackNote(bundle) {
  if (String(bundle.status_callback ?? '').trim()) return null;
  return 'status_callback is unset: when this bundle changes state nothing is ' +
         'told, so the first signal will be numbers that stopped working.';
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

/**
 * The numbers v2 API returns rows under `results` and an absolute next page in
 * `meta.next_page_url`, unlike the 2010-04-01 API's `next_page_uri` path.
 */
export async function listBundles(auth, onlyDated = true, limit = 500) {
  let url = `${NUMBERS}/RegulatoryCompliance/Bundles`;
  let params = { SortBy: 'valid-until', SortDirection: 'ASC', PageSize: 50 };
  if (onlyDated) params.HasValidUntilDate = 'true';
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.results ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
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

  const flag = process.argv.indexOf('--horizon-days');
  const horizonDays = flag === -1 ? 60 : Number.parseInt(process.argv[flag + 1], 10);
  const now = new Date();

  const auth = authHeader(key, secret);
  const bundles = await listBundles(auth, !process.argv.includes('--all'));
  if (bundles.length === 0) {
    console.log('no regulatory bundles with a valid_until on this account');
    return;
  }

  let expired = 0;
  let soon = 0;
  for (const bundle of bundles) {
    const [state, detail] = verdict(bundle, now, horizonDays);
    const label = `${bundle.iso_country ?? '??'}/${bundle.number_type ?? '?'}`;
    const line = `${state.padEnd(12)} ${bundle.sid ?? '?'}  ${label}  ${detail}`;
    if (state === 'current' || state === 'no-expiry' || state === 'not-approved') {
      console.log(line);
      continue;
    }
    if (state === 'expired' || state === 'rejected') expired += 1; else soon += 1;
    console.warn(line);
    const note = callbackNote(bundle);
    if (note) console.warn(`  ${note}`);
    console.warn(`  repair: POST ${NUMBERS}/RegulatoryCompliance/SupportingDocuments ` +
                 `with current paperwork, assign it via POST ${NUMBERS}/` +
                 `RegulatoryCompliance/Bundles/${bundle.sid ?? '?'}/ItemAssignments, ` +
                 'then POST the bundle with Status=pending-review');
  }

  console.log(`${bundles.length} bundle(s), ${expired} expired, ${soon} inside the ` +
              `${horizonDays} day horizon`);
  process.exitCode = (expired || soon) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Pinning a date-based rule means pinning the clock, so every case runs against a fixed <em>now</em>. The two that matter most are the ones a naive check gets wrong in opposite directions: a bundle with a null <code>valid_until</code> must not be reported as expired, and a bundle already past its date must not be quietly filed under the horizon warning it has outrun.",
"test_py_file": "test_twilio_bundle_expiry_audit.py",
"test_py": '''import datetime

from twilio_bundle_expiry_audit import callback_note, parse_date, verdict

NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)


def make(**kw):
    bundle = {"sid": "BU00000000000000000000000000000001",
              "friendly_name": "DE local address",
              "iso_country": "DE",
              "number_type": "local",
              "status": "twilio-approved",
              "valid_until": "2027-06-01T00:00:00Z",
              "status_callback": "https://ops.example.com/bundle"}
    bundle.update(kw)
    return bundle


def test_iso_dates_from_the_numbers_v2_api_parse_with_a_trailing_z():
    assert parse_date("2027-06-01T00:00:00Z") == \\
        datetime.datetime(2027, 6, 1, tzinfo=datetime.timezone.utc)


def test_an_approved_bundle_far_from_its_date_is_current():
    state, detail = verdict(make(), NOW, horizon_days=60)
    assert state == "current"
    assert "275 day(s)" in detail


def test_an_approved_bundle_inside_the_horizon_is_the_warning():
    state, detail = verdict(make(valid_until="2026-09-15T00:00:00Z"), NOW,
                            horizon_days=60)
    assert state == "expiring"
    assert "16 day(s)" in detail


def test_the_horizon_is_the_thing_that_decides():
    bundle = make(valid_until="2026-10-20T00:00:00Z")
    assert verdict(bundle, NOW, horizon_days=30)[0] == "current"
    assert verdict(bundle, NOW, horizon_days=60)[0] == "expiring"


def test_a_date_already_past_is_an_incident_not_a_warning():
    state, detail = verdict(make(valid_until="2026-08-01T00:00:00Z"), NOW)
    assert state == "expired"
    assert "29 day(s) ago" in detail


def test_the_aftermath_reads_as_rejected_rather_than_as_expired():
    state, detail = verdict(make(status="twilio-rejected",
                                 valid_until="2026-07-01T00:00:00Z"), NOW)
    assert state == "rejected"
    assert "non-compliant today" in detail


def test_a_null_valid_until_is_healthy_and_must_not_be_read_as_expired():
    state, detail = verdict(make(valid_until=None), NOW)
    assert state == "no-expiry"
    assert "re-attestation" in detail


def test_a_bundle_that_was_never_approved_is_somebody_else_s_note():
    state, _ = verdict(make(status="pending-review", valid_until=None), NOW)
    assert state == "not-approved"


def test_a_missing_status_callback_is_reported_alongside_the_date():
    assert callback_note(make(status_callback="")) is not None
    assert callback_note(make()) is None
''',
"test_js_file": "twilio-bundle-expiry-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { callbackNote, parseDate, verdict } from './twilio-bundle-expiry-audit.mjs';

const NOW = new Date('2026-08-30T00:00:00Z');

const make = (over = {}) => ({
  sid: 'BU00000000000000000000000000000001',
  friendly_name: 'DE local address',
  iso_country: 'DE',
  number_type: 'local',
  status: 'twilio-approved',
  valid_until: '2027-06-01T00:00:00Z',
  status_callback: 'https://ops.example.com/bundle',
  ...over,
});

test('iso dates from the numbers v2 api parse with a trailing z', () => {
  assert.equal(parseDate('2027-06-01T00:00:00Z').toISOString(),
               '2027-06-01T00:00:00.000Z');
});

test('an approved bundle far from its date is current', () => {
  const [state, detail] = verdict(make(), NOW, 60);
  assert.equal(state, 'current');
  assert.match(detail, /275 day\\(s\\)/);
});

test('an approved bundle inside the horizon is the warning', () => {
  const [state, detail] = verdict(make({ valid_until: '2026-09-15T00:00:00Z' }), NOW, 60);
  assert.equal(state, 'expiring');
  assert.match(detail, /16 day\\(s\\)/);
});

test('the horizon is the thing that decides', () => {
  const bundle = make({ valid_until: '2026-10-20T00:00:00Z' });
  assert.equal(verdict(bundle, NOW, 30)[0], 'current');
  assert.equal(verdict(bundle, NOW, 60)[0], 'expiring');
});

test('a date already past is an incident not a warning', () => {
  const [state, detail] = verdict(make({ valid_until: '2026-08-01T00:00:00Z' }), NOW);
  assert.equal(state, 'expired');
  assert.match(detail, /29 day\\(s\\) ago/);
});

test('the aftermath reads as rejected rather than as expired', () => {
  const [state, detail] = verdict(make({
    status: 'twilio-rejected', valid_until: '2026-07-01T00:00:00Z' }), NOW);
  assert.equal(state, 'rejected');
  assert.match(detail, /non-compliant today/);
});

test('a null valid_until is healthy and must not be read as expired', () => {
  const [state, detail] = verdict(make({ valid_until: null }), NOW);
  assert.equal(state, 'no-expiry');
  assert.match(detail, /re-attestation/);
});

test('a bundle that was never approved is somebody else\\'s note', () => {
  assert.equal(
    verdict(make({ status: 'pending-review', valid_until: null }), NOW)[0],
    'not-approved');
});

test('a missing status_callback is reported alongside the date', () => {
  assert.notEqual(callbackNote(make({ status_callback: '' })), null);
  assert.equal(callbackNote(make()), null);
});
''',
"faq": [
 ("What actually happens to the numbers when the bundle expires?",
  "They become non-compliant with the regulation the bundle satisfied, which puts them at risk of being reclaimed. The timing after that is not a published SLA and it is not something to plan around: treat valid_until as the deadline and the period after it as borrowed time, not as a grace period you can schedule work in."),
 ("How long should the horizon be?",
  "As long as your renewal actually takes end to end. Gathering current documents from a legal or finance team, uploading them, reassigning them and waiting for review is measured in weeks, so sixty to ninety days is a realistic window. A seven-day alert on a three-week process is a notification that the outage is now unavoidable."),
 ("Why is the status still twilio-approved after the date has passed?",
  "Because the status changes when Twilio processes the expiry, not at the stroke of midnight in the field. That is why the script keys on the date rather than waiting for the status, and why an approved bundle with a date in the past gets its own state: it is the last moment at which the problem is still cheap."),
 ("Can I use the status callback instead of polling?",
  "Set it, and do not rely on it for this. A status_callback webhooks the bundle's transitions, so it tells you at the moment the bundle stops being approved, which is the moment the numbers are already exposed. Polling valid_until is what buys you the weeks you need. The callback is how you find out about everything else that happens to the bundle."),
 ("What about bundles with no valid_until at all?",
  "They are fine, and reporting them is actively harmful. Many regulations require a one-time attestation with no renewal, so a null date means there is nothing to watch. Treating null as expired fills the report with noise and hides the four bundles that genuinely have a date coming."),
],
"related": [
 ("/twilio/tollfree-number-not-verified/", "A toll-free number sending before verification"),
 ("/twilio/from-number-not-sms-capable/", "Sending from a number that cannot carry SMS"),
 ("/twilio/idle-phone-numbers-billed/", "Numbers billed every month for carrying nothing"),
],
"citations": [CITE_BUNDLES, CITE_REGULATORY, CITE_SUPPORTING, CITE_KEYS],
},

]
