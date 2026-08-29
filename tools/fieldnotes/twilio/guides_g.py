#!/usr/bin/env python3
"""/twilio/ field notes, batch G — the writing.

Four problems that a read-only credential can see and that error-based
monitoring mostly cannot: rent paid on numbers nobody uses, a trial account
that silently caps message length, an account whose outbound messaging is
switched off, and a contact list still holding numbers the carrier has given to
somebody else.

Read-only throughout. An API Key with read access, never the account auth
token, and every repair is printed for a human to run rather than performed.
"""

CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_USAGE = ("Usage Record resource — Twilio Docs",
              "https://www.twilio.com/docs/usage/api/usage-record")
CITE_UNUSED = ("Manage unused resources — Twilio Docs",
               "https://www.twilio.com/docs/usage/manage-unused-resources")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_30044 = ("Error 30044: trial account message length exceeded — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30044")
CITE_30037 = ("Error 30037: outbound message not allowed — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30037")
CITE_30007 = ("Error 30007: message filtered — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30007")
CITE_ACCOUNT = ("Account resource — Twilio Docs",
                "https://www.twilio.com/docs/iam/api/account")
CITE_SUBACCOUNTS = ("Subaccounts — Twilio Docs",
                    "https://www.twilio.com/docs/iam/api/subaccounts")
CITE_SERVICES = ("Messaging Services — Twilio Docs",
                 "https://www.twilio.com/docs/messaging/services")
CITE_DEACT = ("Deactivations resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/deactivations-resource")

GUIDES = [

{
"slug": "idle-phone-numbers-billed",
"title": "Phone numbers with no traffic still bill every month",
"description": "Idle Twilio numbers rent forever. Compare each number's inbound and outbound activity against its monthly rate to get a figure somebody can act on.",
"h1": "phone numbers with no traffic still bill every month",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio unused phone numbers", "twilio number rental cost",
             "release twilio number", "twilio idle number audit",
             "twilio phonenumbers usage record"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing is broken. The invoice creeps up while message volume stays flat, and when somebody finally asks what the forty-one numbers on the account are for, the honest answer is that nobody knows. There is no error to search for, no alert to acknowledge &mdash; just a line item that has been quietly compounding since the last time anyone looked.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code>, then for each number ask <code>Messages.json?From=</code>, <code>Messages.json?To=</code>, <code>Calls.json?From=</code> and <code>Calls.json?To=</code> over a 90-day window. A number with nothing on any of the four is idle.</p>
<p>Idle on its own is not a decision. Take the monthly spend from <code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Monthly.json?Category=phonenumbers</code>, divide by the number count, and report each idle number as an annual figure. "Release this and stop paying $13.80 a year" is something a person will act on; "this number looks unused" is not.</p>""",
"problem": """<p>A phone number is the one Twilio resource that charges you for existing. Messages cost when they send, calls cost when they connect, but a number costs whether or not anything ever touches it. Buy one to reproduce a bug on a Thursday afternoon and it will still be on the invoice three years later, having carried four test messages in its entire life.</p>
<p>The reason this survives every cost review is that the invoice aggregates. It says <code>phonenumbers</code> and a total. It does not say which numbers, and it certainly does not say which of them carried no traffic. To get from the total to a decision you have to join billing against usage per number, and no single Twilio response does that join for you.</p>
<p>The cost is not only money. Every idle number is a number that has to be registered for A2P if it is ever used, a number that shows up in your Trust Hub surface, and a number that somebody can still send from if a credential leaks. Numbers you cannot account for are numbers you cannot secure.</p>""",
"why": """<p><strong>No response carries both facts.</strong> <code>IncomingPhoneNumbers.json</code> knows the number and its capabilities but not its price and not its traffic. <code>Usage/Records/Monthly.json</code> knows the spend for the whole <code>phonenumbers</code> category but not which numbers it covers. Messages and Calls know the traffic but only if you ask per number. The audit is three resources or it is nothing.</p>
<p><strong>Outbound-only checks miss the useful half.</strong> A number that never sends may still be the one printed on the invoices, taking inbound calls all day. Checking <code>From=</code> alone reports it as idle and somebody releases a working support line. The check has to be four queries per number, not one.</p>
<p><strong>Volume is not the same as value, and the interesting case is in between.</strong> A number with three messages in ninety days is not idle, so a boolean check clears it. Divide its rent by its traffic and it worked out at more than four dollars a message. That number belongs in the report with a figure attached, not in the silent majority.</p>
<p><strong>Nobody releases a number they are unsure about.</strong> Release is free and Twilio will hold it for a short recovery window, but the fear of killing a live line beats a vague suspicion every time. An exact annual cost and an exact "zero messages, zero calls, ninety days" is what turns the suspicion into a ticket.</p>""",
"steps": [
 {"h": "List every number on the account",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=100</code>, following <code>next_page_uri</code> until it is absent. Keep <code>sid</code>, <code>phone_number</code> and <code>friendly_name</code>: the friendly name is often the only surviving hint about why the number was bought.</p>"""},
 {"h": "Derive a monthly rate you can defend",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Monthly.json?Category=phonenumbers</code> returns one record per month with a <code>price</code>. Take the most recent, divide by the number count, and you have an average rate per number per month. It is an average: a toll-free number costs more than a local one, so this under-reports the expensive ones. Pass the real figure with <code>--monthly-cost</code> when you know it.</p>"""},
 {"h": "Ask four questions per number, not one",
  "body": """<p><code>Messages.json?From={E164}&amp;DateSent&gt;={since}</code>, <code>Messages.json?To={E164}&amp;DateSent&gt;={since}</code>, <code>Calls.json?From={E164}&amp;StartTime&gt;={since}</code> and <code>Calls.json?To={E164}&amp;StartTime&gt;={since}</code>. One page each is enough &mdash; a number with fifty messages in the window is not idle and the exact count changes nothing.</p>"""},
 {"h": "Turn the counts into money",
  "body": """<p>Zero on all four is idle, and its cost for the year is the number you report. Traffic in only one direction is a separate finding, because an inbound-only number is usually deliberate. A handful of messages is a third: divide the window's rent by the traffic and print the cost per message.</p>"""},
 {"h": "Release, then re-run",
  "body": """<p>The repair is a delete against <code>/2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json</code>. Releasing is free and recoverable for a short window, so the risk is low and the saving is immediate. Put the audit on a quarterly schedule; the numbers bought for the next incident will accumulate exactly like these did.</p>"""},
],
"verify": """<p>Run it again after releasing. The idle count and the annual total should both fall by what you released.</p>
<pre><code class="language-bash">python3 twilio_idle_numbers_audit.py --days 90
# 41 number(s), 0 idle, $0.00/year in rent for numbers with no traffic</code></pre>""",
"code_intro": "One paginated GET for the numbers, one for the monthly usage record, and four small GETs per number for traffic. Read access is all it needs and all it should have. The interesting part &mdash; how activity, rent and a threshold combine into a verdict and an annual figure &mdash; is a pure function, so the arithmetic is visible and the tests do not need an account.",
"py_file": "twilio_idle_numbers_audit.py",
"py": '''"""Report Twilio phone numbers carrying no traffic, priced per year.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_idle_numbers_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# One page of traffic settles the question. A number with this many messages in
# the window is in use, and the exact figure would not change the verdict.
PROBE = 50


def monthly_rate(records, number_count, override=None):
    """Dollars per number per month.

    IncomingPhoneNumbers carries no price, so the rate has to come from the
    monthly usage record for the phonenumbers category divided by the numbers on
    the account. That is an average and it under-reports toll-free and short
    codes, which cost more than a local number. Pass --monthly-cost when you
    know the real figure.

    Usage prices arrive as strings and the sign convention differs between usage
    records and the balance resource, so take the magnitude.
    """
    if override is not None:
        return max(0.0, float(override))
    rows = [r for r in records
            if str(r.get("category") or "") == "phonenumbers"]
    if not rows or not number_count:
        return 0.0
    latest = max(rows, key=lambda r: str(r.get("start_date") or ""))
    try:
        price = abs(float(latest.get("price") or 0))
    except (TypeError, ValueError):
        return 0.0
    return price / float(number_count)


def verdict(activity, rate, window_days=90, min_traffic=5, flag_above=24.0):
    """Classify one number by what it carried against what it costs.

    activity: counts keyed outbound_messages, inbound_messages, outbound_calls,
    inbound_calls. rate: dollars per month. Pure, so the thresholds and the
    arithmetic are visible and testable rather than buried in a request loop.

    Returns (state, detail, annual_cost).
    """
    out = (int(activity.get("outbound_messages") or 0)
           + int(activity.get("outbound_calls") or 0))
    inb = (int(activity.get("inbound_messages") or 0)
           + int(activity.get("inbound_calls") or 0))
    annual = max(0.0, float(rate)) * 12.0
    window_cost = max(0.0, float(rate)) * (float(window_days) / 30.44)

    if out == 0 and inb == 0:
        if annual >= flag_above:
            return ("idle-costly",
                    "no messages and no calls either way in %d days, and it is "
                    "one of the more expensive numbers on the account at $%.2f "
                    "a year. Release this one first."
                    % (window_days, annual),
                    annual)
        return ("idle",
                "no messages and no calls either way in %d days. $%.2f a year "
                "for a number nothing touches." % (window_days, annual),
                annual)

    if out == 0:
        return ("inbound-only",
                "%d inbound event(s) in %d days and nothing outbound. Often "
                "deliberate, so confirm before releasing: $%.2f a year."
                % (inb, window_days, annual),
                annual)

    total = out + inb
    if total < min_traffic:
        per = window_cost / total if total else window_cost
        return ("trickle",
                "%d event(s) in %d days at $%.2f of rent, which is $%.2f per "
                "message or call. Cheaper to fold this traffic onto a number "
                "you already keep." % (total, window_days, window_cost, per),
                annual)

    return ("active",
            "%d outbound and %d inbound event(s) in %d days"
            % (out, inb, window_days),
            annual)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_numbers(session, account, limit):
    """Page IncomingPhoneNumbers. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def activity_for(session, account, e164, since):
    """Four small reads: messages and calls, each direction."""
    msgs = "%s/Accounts/%s/Messages.json" % (BASE, account)
    calls = "%s/Accounts/%s/Calls.json" % (BASE, account)
    params = {"PageSize": PROBE}
    out = {}
    out["outbound_messages"] = len(get(session, msgs, **dict(
        params, **{"From": e164, "DateSent>": since})).get("messages", []))
    out["inbound_messages"] = len(get(session, msgs, **dict(
        params, **{"To": e164, "DateSent>": since})).get("messages", []))
    out["outbound_calls"] = len(get(session, calls, **dict(
        params, **{"From": e164, "StartTime>": since})).get("calls", []))
    out["inbound_calls"] = len(get(session, calls, **dict(
        params, **{"To": e164, "StartTime>": since})).get("calls", []))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="traffic window, in days")
    ap.add_argument("--max-numbers", type=int, default=200,
                    help="stop after this many numbers; each costs four reads")
    ap.add_argument("--monthly-cost", type=float, default=None,
                    help="dollars per number per month, overriding the average")
    ap.add_argument("--min-traffic", type=int, default=5,
                    help="fewer events than this in the window reads as a trickle")
    ap.add_argument("--flag-above", type=float, default=24.0,
                    help="annual dollars above which an idle number is urgent")
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

    numbers = list_numbers(session, account, args.max_numbers)
    if not numbers:
        log.info("no phone numbers on this account")
        return 0

    usage = get(session, "%s/Accounts/%s/Usage/Records/Monthly.json"
                % (BASE, account), Category="phonenumbers")
    rate = monthly_rate(usage.get("usage_records", []), len(numbers),
                        args.monthly_cost)
    log.info("%d number(s) at about $%.2f each per month", len(numbers), rate)

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    idle, wasted = 0, 0.0
    for n in numbers:
        e164 = n.get("phone_number", "?")
        state, detail, annual = verdict(
            activity_for(session, account, e164, since), rate,
            args.days, args.min_traffic, args.flag_above)
        label = n.get("friendly_name") or e164
        line = "%-13s %s (%s)  %s" % (state, e164, label, detail)
        if state == "active":
            log.info(line)
            continue
        log.warning(line)
        if state.startswith("idle"):
            idle += 1
            wasted += annual
            log.warning("  repair: release it with a delete on %s/Accounts/%s"
                        "/IncomingPhoneNumbers/%s.json. Release is free and "
                        "recoverable for a short window.", BASE, account,
                        n.get("sid"))

    log.info("%d number(s), %d idle, $%.2f/year in rent for numbers with no "
             "traffic", len(numbers), idle, wasted)
    return 1 if idle else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-idle-numbers-audit.mjs",
"js": '''/**
 * Report Twilio phone numbers carrying no traffic, priced per year.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// One page of traffic settles the question. A number with this many messages in
// the window is in use, and the exact figure would not change the verdict.
const PROBE = 50;

/**
 * Dollars per number per month. IncomingPhoneNumbers carries no price, so the
 * rate comes from the monthly usage record for the phonenumbers category
 * divided by the numbers on the account. That is an average and it
 * under-reports toll-free and short codes. Prices arrive as strings and the
 * sign convention differs between resources, so take the magnitude.
 */
export function monthlyRate(records, numberCount, override = null) {
  if (override !== null && override !== undefined) return Math.max(0, Number(override));
  const rows = records.filter((r) => String(r.category ?? '') === 'phonenumbers');
  if (!rows.length || !numberCount) return 0;
  const latest = rows.reduce((a, b) =>
    String(b.start_date ?? '') > String(a.start_date ?? '') ? b : a);
  const price = Math.abs(Number(latest.price ?? 0));
  if (!Number.isFinite(price)) return 0;
  return price / Number(numberCount);
}

/**
 * Classify one number by what it carried against what it costs. Pure, so the
 * thresholds and the arithmetic are visible and testable.
 * Returns [state, detail, annualCost].
 */
export function verdict(activity, rate, windowDays = 90, minTraffic = 5, flagAbove = 24) {
  const out = Number(activity.outbound_messages ?? 0) + Number(activity.outbound_calls ?? 0);
  const inb = Number(activity.inbound_messages ?? 0) + Number(activity.inbound_calls ?? 0);
  const annual = Math.max(0, Number(rate)) * 12;
  const windowCost = Math.max(0, Number(rate)) * (Number(windowDays) / 30.44);

  if (out === 0 && inb === 0) {
    if (annual >= flagAbove) {
      return ['idle-costly',
        `no messages and no calls either way in ${windowDays} days, and it is ` +
        `one of the more expensive numbers on the account at $${annual.toFixed(2)} ` +
        'a year. Release this one first.', annual];
    }
    return ['idle',
      `no messages and no calls either way in ${windowDays} days. ` +
      `$${annual.toFixed(2)} a year for a number nothing touches.`, annual];
  }

  if (out === 0) {
    return ['inbound-only',
      `${inb} inbound event(s) in ${windowDays} days and nothing outbound. Often ` +
      `deliberate, so confirm before releasing: $${annual.toFixed(2)} a year.`, annual];
  }

  const total = out + inb;
  if (total < minTraffic) {
    const per = total ? windowCost / total : windowCost;
    return ['trickle',
      `${total} event(s) in ${windowDays} days at $${windowCost.toFixed(2)} of ` +
      `rent, which is $${per.toFixed(2)} per message or call. Cheaper to fold ` +
      'this traffic onto a number you already keep.', annual];
  }

  return ['active',
    `${out} outbound and ${inb} inbound event(s) in ${windowDays} days`, annual];
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

export async function listNumbers(auth, account, limit = 200) {
  let url = `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`;
  let params = { PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.incoming_phone_numbers ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function activityFor(auth, account, e164, since) {
  const msgs = `${BASE}/Accounts/${account}/Messages.json`;
  const calls = `${BASE}/Accounts/${account}/Calls.json`;
  const p = { PageSize: PROBE };
  const om = await get(auth, msgs, { ...p, From: e164, 'DateSent>': since });
  const im = await get(auth, msgs, { ...p, To: e164, 'DateSent>': since });
  const oc = await get(auth, calls, { ...p, From: e164, 'StartTime>': since });
  const ic = await get(auth, calls, { ...p, To: e164, 'StartTime>': since });
  return {
    outbound_messages: (om.messages ?? []).length,
    inbound_messages: (im.messages ?? []).length,
    outbound_calls: (oc.calls ?? []).length,
    inbound_calls: (ic.calls ?? []).length,
  };
}

function flag(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : Number(process.argv[i + 1]);
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
  const days = flag('--days', 90);
  const minTraffic = flag('--min-traffic', 5);
  const flagAbove = flag('--flag-above', 24);
  const override = process.argv.includes('--monthly-cost')
    ? flag('--monthly-cost', null) : null;

  const numbers = await listNumbers(auth, account);
  if (numbers.length === 0) {
    console.log('no phone numbers on this account');
    return;
  }

  const usage = await get(auth, `${BASE}/Accounts/${account}/Usage/Records/Monthly.json`,
                          { Category: 'phonenumbers' });
  const rate = monthlyRate(usage.usage_records ?? [], numbers.length, override);
  console.log(`${numbers.length} number(s) at about $${rate.toFixed(2)} each per month`);

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  let idle = 0;
  let wasted = 0;
  for (const n of numbers) {
    const e164 = n.phone_number ?? '?';
    const act = await activityFor(auth, account, e164, since);
    const [state, detail, annual] = verdict(act, rate, days, minTraffic, flagAbove);
    const label = n.friendly_name || e164;
    const line = `${state.padEnd(13)} ${e164} (${label})  ${detail}`;
    if (state === 'active') { console.log(line); continue; }
    console.warn(line);
    if (state.startsWith('idle')) {
      idle += 1;
      wasted += annual;
      console.warn(`  repair: release it with a delete on ${BASE}/Accounts/` +
                   `${account}/IncomingPhoneNumbers/${n.sid}.json. Release is ` +
                   'free and recoverable for a short window.');
    }
  }

  console.log(`${numbers.length} number(s), ${idle} idle, $${wasted.toFixed(2)}` +
              '/year in rent for numbers with no traffic');
  process.exitCode = idle ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that change what somebody does: an idle number over the urgency threshold, a number that only ever receives, and the trickle case where the rent per message is the whole finding. The rate helper gets its own tests because it takes the newest month out of several and has to survive a price that arrives as a signed string.",
"test_py_file": "test_twilio_idle_numbers_audit.py",
"test_py": '''from twilio_idle_numbers_audit import monthly_rate, verdict

NOTHING = {"outbound_messages": 0, "inbound_messages": 0,
           "outbound_calls": 0, "inbound_calls": 0}


def test_silent_number_is_idle_and_priced_for_the_year():
    state, detail, annual = verdict(NOTHING, 1.15)
    assert state == "idle"
    assert round(annual, 2) == 13.80
    assert "13.80" in detail


def test_expensive_idle_number_is_escalated():
    # A toll-free number rents for more, so it is the one to release first.
    state, _, annual = verdict(NOTHING, 2.15, flag_above=24.0)
    assert state == "idle-costly"
    assert annual > 24.0


def test_inbound_only_number_is_not_reported_as_idle():
    # Checking From= alone is how somebody releases a working support line.
    act = dict(NOTHING, inbound_calls=31)
    state, detail, _ = verdict(act, 1.15)
    assert state == "inbound-only"
    assert "confirm before releasing" in detail


def test_a_handful_of_messages_reports_cost_per_message():
    act = dict(NOTHING, outbound_messages=3)
    state, detail, _ = verdict(act, 1.15, window_days=90, min_traffic=5)
    assert state == "trickle"
    assert "per message or call" in detail


def test_busy_number_is_active():
    act = dict(NOTHING, outbound_messages=50, inbound_messages=12)
    state, _, _ = verdict(act, 1.15)
    assert state == "active"


def test_monthly_rate_uses_the_newest_month_and_divides_by_the_numbers():
    records = [
        {"category": "phonenumbers", "start_date": "2026-06-01", "price": "23.00"},
        {"category": "phonenumbers", "start_date": "2026-07-01", "price": "46.00"},
    ]
    assert monthly_rate(records, 40) == 1.15


def test_monthly_rate_takes_the_magnitude_of_a_signed_price():
    records = [{"category": "phonenumbers", "start_date": "2026-07-01",
                "price": "-46.00"}]
    assert monthly_rate(records, 40) == 1.15


def test_monthly_rate_override_wins_and_survives_an_empty_account():
    assert monthly_rate([], 0, override=2.0) == 2.0
    assert monthly_rate([], 0) == 0.0
''',
"test_js_file": "twilio-idle-numbers-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { monthlyRate, verdict } from './twilio-idle-numbers-audit.mjs';

const NOTHING = {
  outbound_messages: 0, inbound_messages: 0, outbound_calls: 0, inbound_calls: 0,
};

test('silent number is idle and priced for the year', () => {
  const [state, detail, annual] = verdict(NOTHING, 1.15);
  assert.equal(state, 'idle');
  assert.equal(Number(annual.toFixed(2)), 13.80);
  assert.match(detail, /13\\.80/);
});

test('expensive idle number is escalated', () => {
  const [state, , annual] = verdict(NOTHING, 2.15, 90, 5, 24);
  assert.equal(state, 'idle-costly');
  assert.ok(annual > 24);
});

test('inbound only number is not reported as idle', () => {
  const [state, detail] = verdict({ ...NOTHING, inbound_calls: 31 }, 1.15);
  assert.equal(state, 'inbound-only');
  assert.match(detail, /confirm before releasing/);
});

test('a handful of messages reports cost per message', () => {
  const [state, detail] = verdict({ ...NOTHING, outbound_messages: 3 }, 1.15, 90, 5);
  assert.equal(state, 'trickle');
  assert.match(detail, /per message or call/);
});

test('busy number is active', () => {
  const [state] = verdict(
    { ...NOTHING, outbound_messages: 50, inbound_messages: 12 }, 1.15);
  assert.equal(state, 'active');
});

test('monthlyRate uses the newest month and divides by the numbers', () => {
  const records = [
    { category: 'phonenumbers', start_date: '2026-06-01', price: '23.00' },
    { category: 'phonenumbers', start_date: '2026-07-01', price: '46.00' },
  ];
  assert.equal(monthlyRate(records, 40), 1.15);
});

test('monthlyRate takes the magnitude of a signed price', () => {
  const records = [
    { category: 'phonenumbers', start_date: '2026-07-01', price: '-46.00' },
  ];
  assert.equal(monthlyRate(records, 40), 1.15);
});

test('monthlyRate override wins and survives an empty account', () => {
  assert.equal(monthlyRate([], 0, 2), 2);
  assert.equal(monthlyRate([], 0), 0);
});
''',
"faq": [
 ("Why not just read the price off the phone number?",
  "Because IncomingPhoneNumbers does not carry one. The number resource knows the SID, the E.164 and the capabilities, and nothing about billing. The only read-only route to a price is the monthly usage record for the phonenumbers category, which is an account total, so the per-number figure this script prints is that total divided by the number count."),
 ("Is an average rate good enough to act on?",
  "For a report that says which numbers to look at, yes. For a number you are about to defend in a budget meeting, no: an average under-reports toll-free and short codes and over-reports local ones. Pass --monthly-cost with the real rate for the class of number you care about and the figures become exact."),
 ("Why check inbound as well as outbound?",
  "Because the most common false positive is a number that only ever receives. It is on the invoices, on the website, in the email signature, and it has never sent a message in its life. A From= check alone reports it as dead and somebody releases it. Four queries per number is the price of not doing that."),
 ("What is the trickle state for?",
  "The number that is technically in use and not worth keeping. Three messages in ninety days is not idle, so a boolean check clears it, but dividing the rent by the traffic gives you a cost per message that is usually absurd. Fold that traffic onto a number you already keep."),
 ("Can I release a number and get it back?",
  "For a short window, yes. Twilio holds a released number briefly and you can reclaim it from the console, after which it goes back into the general pool and may be reissued to somebody else. That is exactly the recycling problem this section covers elsewhere, so treat the recovery window as short and confirm before you release."),
],
"related": [
 ("/twilio/phone-number-still-on-demo-twiml/", "Numbers still pointing at Twilio's demo TwiML"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
 ("/twilio/deactivated-number-recycling/", "Recycled numbers send OTPs to a stranger"),
],
"citations": [CITE_PN, CITE_USAGE, CITE_UNUSED, CITE_KEYS],
},

{
"slug": "trial-account-segment-limit-30044",
"title": "A trial account rejects multi-segment messages with 30044",
"description": "Short test messages send. Real templates fail with 30044 because a trial account caps length, and one emoji halves the per-segment budget to 70 characters.",
"h1": "a trial account rejects multi-segment messages with 30044",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30044", "trial account message length exceeded",
             "twilio ucs2 segment limit", "twilio smart encoding",
             "twilio trial limitations sms"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "&ldquo;Test&rdquo; sends. &ldquo;Your verification code is 481920&rdquo; sends. The real welcome message, the one with the customer's name and a link and a single cheerful emoji at the end, comes back <code>undelivered</code> with <code>error_code=30044</code>. Everyone's first theory is the link. It is not the link.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}.json</code> and check <code>type</code>. If it is <code>Trial</code>, the account caps message length far below a paid one and <code>30044</code> is the rejection. Then page <code>Messages.json?DateSent&gt;={since}</code>, count rows with <code>error_code == 30044</code> and look at <code>num_segments</code> on them.</p>
<p>The reason a body that "fits" stops fitting is encoding. A body made entirely of GSM-7 characters gets 160 characters in one segment and 153 in each of several. One character outside that alphabet &mdash; a curly apostrophe pasted from a document, an emoji, an accented name &mdash; flips the whole body to UCS-2 and the budget drops to 70 and 67.</p>""",
"problem": """<p>This is a length limit that moves. Not gradually, and not in proportion to what you added: paste a smart quote into a 150-character template and the same 150 characters now need three segments instead of one. The character you added cost you nothing; the encoding change it forced cost you the whole budget.</p>
<p>On a paid account that shows up as a bigger bill. On a trial account it shows up as <code>30044</code> and the message never leaves. Which means the failure is bound to the account rather than to the code, and it will disappear the moment somebody runs the same template against a paid account and declares the bug unreproducible.</p>
<p>Then there is the direction of travel. Trial is where every integration starts. The template gets written short, tested, approved. Real data arrives &mdash; a customer called Zoë, an order reference, a two-line address &mdash; and the body crosses the line in production, on the account that is least able to send it.</p>""",
"why": """<p><strong>Encoding is a property of the whole body, not of the character.</strong> There is no mixed mode. One character outside GSM-7 and every character in the message is encoded as UCS-2, at 70 per single segment and 67 per concatenated one. This is why "I only added an emoji" and "the message is now three segments" are the same sentence.</p>
<p><strong>An emoji is usually two units, not one.</strong> Most emoji live outside the Basic Multilingual Plane and occupy two UTF-16 code units. A length check written with a language's character count will under-count them, agree the body fits, and hand Twilio something that does not.</p>
<p><strong>Some GSM-7 characters already cost two.</strong> The extended set &mdash; the euro sign, square brackets, braces, the tilde, the backslash and the caret &mdash; is encoded as an escape plus the character. They stay GSM-7, they just spend twice. A template full of square brackets is closer to the limit than it looks.</p>
<p><strong>The trial cap is invisible until it is hit.</strong> Nothing in the Account resource says "your messages are capped at this length". You get <code>type: Trial</code>, and you are expected to know what that implies. The script has to carry that knowledge, because the API will not tell you.</p>""",
"steps": [
 {"h": "Confirm the account really is a trial",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code> and read <code>type</code> and <code>status</code>. <code>Trial</code> is the precondition for <code>30044</code>; anything else and the error is telling you the sending code is authenticating as a different account from the one you are reading.</p>"""},
 {"h": "Count the rejections in the window",
  "body": """<p>Page <code>Messages.json?DateSent&gt;={since}&amp;PageSize=1000</code> and filter client-side. There is no <code>ErrorCode</code> filter on this resource, so the window and the page cap are the only bounds you get. Read <code>error_code</code> as an integer: it arrives as a string often enough to make a raw comparison report zero findings on an account full of them.</p>"""},
 {"h": "Read num_segments on the failures",
  "body": """<p>Twilio reports <code>num_segments</code> on the Message resource. A <code>30044</code> with <code>num_segments</code> greater than one confirms the diagnosis outright. If the count is low and the body is short, the cap has been hit by encoding rather than by length, which points at the next step.</p>"""},
 {"h": "Run the body through the segment planner before you send it",
  "body": """<p>The pure function in this script takes a body and returns the encoding, the unit count, the per-segment budget and the number of segments. Run your templates through it with realistic data in the placeholders. That is where the smart quote and the accented name show up, on a laptop, rather than in production.</p>"""},
 {"h": "Upgrade, or shorten, or turn on Smart Encoding",
  "body": """<p>Upgrading the account removes the cap. Short of that, strip the Unicode: replace curly quotes with straight ones, drop the emoji, transliterate where you can. If you send through a Messaging Service, Smart Encoding does the common substitutions for you &mdash; it is a field on the service, and the script prints the call rather than making it.</p>"""},
],
"verify": """<p>Re-run after upgrading or shortening. The 30044 count for the window should be zero and the state should no longer be <code>trial-blocked</code>.</p>
<pre><code class="language-bash">python3 twilio_trial_segment_audit.py --days 7
# paid          AC00000000  1,204 message(s), no 30044 in 7 days</code></pre>""",
"code_intro": "Two GETs: the account, then the Messages list for the window. Everything that decides anything is pure &mdash; the GSM-7 alphabet, the segment arithmetic and the verdict &mdash; because the encoding rules are the part worth reading and the part worth testing. The repair, including the Smart Encoding call, is printed rather than performed.",
"py_file": "twilio_trial_segment_audit.py",
"py": '''"""Report Twilio messages rejected with 30044, and plan any body's segments.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime as dt
import logging
import math
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_trial_segment_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

TRIAL_LENGTH = 30044

# The GSM 03.38 basic alphabet. A body made only of these encodes as GSM-7 at
# 160 characters in a single segment and 153 in each concatenated one.
GSM7_BASIC = set(
    "@£$¥èéùìòÇ"
    + chr(10) + "Øø" + chr(13) + "Åå"
    "Δ_ΦΓΛΩΠΨΣΘΞ"
    "ÆæßÉ"
    " !\\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§"
    "¿abcdefghijklmnopqrstuvwxyzäöñüà"
)

# Still GSM-7, but each is sent as an escape plus the character, so it spends
# two of the budget rather than one.
GSM7_EXTENDED = set("^{}[~]|€") | {chr(92)}


def segment_plan(body):
    """Encoding, unit count, per-segment budget and segment count for a body.

    Pure, so the encoding rules are visible and testable without a network.

    There is no mixed mode: one character outside GSM-7 and the entire body is
    encoded as UCS-2, dropping the budget from 160 to 70. UCS-2 is counted in
    UTF-16 code units, not characters, because most emoji occupy two of them and
    a character count quietly under-reports them.
    """
    text = str(body or "")
    units = 0
    gsm = True
    for ch in text:
        if ch in GSM7_BASIC:
            units += 1
        elif ch in GSM7_EXTENDED:
            units += 2
        else:
            gsm = False
            break

    if gsm:
        single, multi, encoding = 160, 153, "GSM-7"
    else:
        units = sum(2 if ord(c) > 0xFFFF else 1 for c in text)
        single, multi, encoding = 70, 67, "UCS-2"

    if units <= single:
        return {"encoding": encoding, "units": units,
                "per_segment": single, "segments": 1}
    return {"encoding": encoding, "units": units, "per_segment": multi,
            "segments": int(math.ceil(units / float(multi)))}


def error_code(message):
    """Read error_code as an integer, or None.

    It is null on healthy messages and a number on failed ones, but it arrives
    as a string often enough that a raw comparison against 30044 is how this
    audit reports zero findings on an account that is full of them.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def tally(messages):
    """Count outbound messages and the 30044 rejections among them. Pure."""
    stats = {"total": 0, "blocked": 0, "multi_segment": 0, "sids": []}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        stats["total"] += 1
        if error_code(m) != TRIAL_LENGTH:
            continue
        stats["blocked"] += 1
        try:
            if int(m.get("num_segments") or 1) > 1:
                stats["multi_segment"] += 1
        except (TypeError, ValueError):
            pass
        if len(stats["sids"]) < 3:
            stats["sids"].append(m.get("sid"))
    return stats


def verdict(account, stats):
    """Classify the account against its rejections. Pure.

    Returns (state, detail).
    """
    kind = str((account or {}).get("type") or "").strip().lower()
    status = str((account or {}).get("status") or "").strip().lower()
    total = int(stats.get("total") or 0)
    blocked = int(stats.get("blocked") or 0)
    multi = int(stats.get("multi_segment") or 0)

    if kind == "trial" and blocked:
        return ("trial-blocked",
                "%d of %d outbound message(s) rejected with 30044, %d of them "
                "over one segment. The account is a Trial, so the length cap is "
                "real and no amount of retrying will move it."
                % (blocked, total, multi))

    if kind == "trial":
        return ("trial-exposed",
                "%d outbound message(s) and no 30044 yet, but the account is a "
                "Trial and the length cap applies to every send. One accented "
                "name or one emoji in a template and this becomes an outage."
                % total)

    if blocked:
        return ("unexpected",
                "%d message(s) rejected with 30044 but this account reads as "
                "'%s', not Trial. 30044 only exists on trial accounts, so the "
                "code that sent these is authenticating as a different account "
                "from the one being audited." % (blocked, kind or "unknown"))

    return ("paid",
            "%d message(s), no 30044 in the window%s"
            % (total, "" if status in ("active", "") else " (status %s)" % status))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. There is no ErrorCode filter on this resource, so the
    window and the page cap are the only ways to bound it."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--plan",
                    help="print the segment plan for one body and exit")
    args = ap.parse_args()

    if args.plan is not None:
        p = segment_plan(args.plan)
        log.info("%s, %d unit(s), %d per segment, %d segment(s)",
                 p["encoding"], p["units"], p["per_segment"], p["segments"])
        return 0

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    detail_account = get(session, "%s/Accounts/%s.json" % (BASE, account))
    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    stats = tally(list_messages(session, account, since, args.max_messages))
    state, detail = verdict(detail_account, stats)

    line = "%-14s %s  %s" % (state, account, detail)
    if state == "paid":
        log.info(line)
        return 0

    log.warning(line)
    if stats["sids"]:
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
    log.warning("  repair: upgrade the account in Console > Billing > Upgrade, "
                "or shorten the body and strip Unicode so it stays GSM-7. On a "
                "Messaging Service, enable Smart Encoding with a write to "
                "https://messaging.twilio.com/v1/Services/{ServiceSid} setting "
                "SmartEncoding=true.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-trial-segment-audit.mjs",
"js": '''/**
 * Report Twilio messages rejected with 30044, and plan any body's segments.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const TRIAL_LENGTH = 30044;

// The GSM 03.38 basic alphabet. A body made only of these encodes as GSM-7 at
// 160 characters in a single segment and 153 in each concatenated one.
const GSM7_BASIC = new Set(
  '@\\u00a3$\\u00a5\\u00e8\\u00e9\\u00f9\\u00ec\\u00f2\\u00c7'
  + '\\n\\u00d8\\u00f8\\r\\u00c5\\u00e5'
  + '\\u0394_\\u03a6\\u0393\\u039b\\u03a9\\u03a0\\u03a8\\u03a3\\u0398\\u039e'
  + '\\u00c6\\u00e6\\u00df\\u00c9'
  + ' !"#\\u00a4%&\\'()*+,-./0123456789:;<=>?'
  + '\\u00a1ABCDEFGHIJKLMNOPQRSTUVWXYZ\\u00c4\\u00d6\\u00d1\\u00dc\\u00a7'
  + '\\u00bfabcdefghijklmnopqrstuvwxyz\\u00e4\\u00f6\\u00f1\\u00fc\\u00e0',
);

// Still GSM-7, but each is sent as an escape plus the character, so it spends
// two of the budget rather than one.
const GSM7_EXTENDED = new Set('^{}[~]|\\u20ac' + String.fromCharCode(92));

/**
 * Encoding, unit count, per-segment budget and segment count for a body. Pure,
 * so the encoding rules are visible and testable without a network.
 *
 * There is no mixed mode: one character outside GSM-7 and the entire body is
 * encoded as UCS-2, dropping the budget from 160 to 70. UCS-2 is counted in
 * UTF-16 code units, not characters, because most emoji occupy two of them.
 */
export function segmentPlan(body) {
  const text = String(body ?? '');
  let units = 0;
  let gsm = true;
  for (const ch of text) {
    if (GSM7_BASIC.has(ch)) units += 1;
    else if (GSM7_EXTENDED.has(ch)) units += 2;
    else { gsm = false; break; }
  }

  let single;
  let multi;
  let encoding;
  if (gsm) {
    [single, multi, encoding] = [160, 153, 'GSM-7'];
  } else {
    units = text.length; // UTF-16 code units, which is what UCS-2 counts
    [single, multi, encoding] = [70, 67, 'UCS-2'];
  }

  if (units <= single) {
    return { encoding, units, per_segment: single, segments: 1 };
  }
  return { encoding, units, per_segment: multi, segments: Math.ceil(units / multi) };
}

/**
 * Read error_code as a number, or null. It arrives as a string often enough
 * that a raw comparison against 30044 reports nothing on an account full of
 * findings.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** Count outbound messages and the 30044 rejections among them. Pure. */
export function tally(messages) {
  const stats = { total: 0, blocked: 0, multi_segment: 0, sids: [] };
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    stats.total += 1;
    if (errorCode(m) !== TRIAL_LENGTH) continue;
    stats.blocked += 1;
    if (Number(m.num_segments ?? 1) > 1) stats.multi_segment += 1;
    if (stats.sids.length < 3) stats.sids.push(m.sid);
  }
  return stats;
}

/** Classify the account against its rejections. Pure. Returns [state, detail]. */
export function verdict(account, stats) {
  const kind = String(account?.type ?? '').trim().toLowerCase();
  const status = String(account?.status ?? '').trim().toLowerCase();
  const total = Number(stats.total ?? 0);
  const blocked = Number(stats.blocked ?? 0);
  const multi = Number(stats.multi_segment ?? 0);

  if (kind === 'trial' && blocked) {
    return ['trial-blocked',
      `${blocked} of ${total} outbound message(s) rejected with 30044, ${multi} ` +
      'of them over one segment. The account is a Trial, so the length cap is ' +
      'real and no amount of retrying will move it.'];
  }

  if (kind === 'trial') {
    return ['trial-exposed',
      `${total} outbound message(s) and no 30044 yet, but the account is a Trial ` +
      'and the length cap applies to every send. One accented name or one emoji ' +
      'in a template and this becomes an outage.'];
  }

  if (blocked) {
    return ['unexpected',
      `${blocked} message(s) rejected with 30044 but this account reads as ` +
      `'${kind || 'unknown'}', not Trial. 30044 only exists on trial accounts, ` +
      'so the code that sent these is authenticating as a different account ' +
      'from the one being audited.'];
  }

  const suffix = (status === 'active' || status === '') ? '' : ` (status ${status})`;
  return ['paid', `${total} message(s), no 30044 in the window${suffix}`];
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

export async function listMessages(auth, account, since, limit = 20000) {
  let url = `${BASE}/Accounts/${account}/Messages.json`;
  let params = { PageSize: 1000, 'DateSent>': since };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.messages ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function main() {
  const planAt = process.argv.indexOf('--plan');
  if (planAt !== -1) {
    const p = segmentPlan(process.argv[planAt + 1] ?? '');
    console.log(`${p.encoding}, ${p.units} unit(s), ${p.per_segment} per segment, ` +
                `${p.segments} segment(s)`);
    return;
  }

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
  const daysAt = process.argv.indexOf('--days');
  const days = daysAt === -1 ? 7 : Number(process.argv[daysAt + 1]);

  const detailAccount = await get(auth, `${BASE}/Accounts/${account}.json`);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const stats = tally(await listMessages(auth, account, since));
  const [state, detail] = verdict(detailAccount, stats);

  const line = `${state.padEnd(14)} ${account}  ${detail}`;
  if (state === 'paid') { console.log(line); return; }

  console.warn(line);
  if (stats.sids.length) console.warn(`  message sids: ${stats.sids.join(', ')}`);
  console.warn('  repair: upgrade the account in Console > Billing > Upgrade, or ' +
               'shorten the body and strip Unicode so it stays GSM-7. On a ' +
               'Messaging Service, enable Smart Encoding with a write to ' +
               'https://messaging.twilio.com/v1/Services/{ServiceSid} setting ' +
               'SmartEncoding=true.');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The segment planner is where the tests earn their keep. A 160-character ASCII body is one segment; adding a single emoji makes the same body two, because the emoji is two UTF-16 units and it drags the other 160 characters into UCS-2 with it. The euro sign gets its own test because it stays GSM-7 and still costs two.",
"test_py_file": "test_twilio_trial_segment_audit.py",
"test_py": '''from twilio_trial_segment_audit import segment_plan, tally, verdict


def test_one_hundred_and_sixty_ascii_characters_is_one_gsm7_segment():
    p = segment_plan("a" * 160)
    assert p["encoding"] == "GSM-7"
    assert p["segments"] == 1
    assert p["per_segment"] == 160


def test_one_more_character_drops_the_budget_to_153():
    p = segment_plan("a" * 161)
    assert p["per_segment"] == 153
    assert p["segments"] == 2


def test_a_single_emoji_flips_the_whole_body_to_ucs2():
    p = segment_plan("Welcome aboard")
    assert p["encoding"] == "GSM-7"
    p = segment_plan("Welcome aboard \\U0001F389")
    assert p["encoding"] == "UCS-2"
    assert p["per_segment"] == 70


def test_an_emoji_counts_as_two_utf16_units():
    # A character count would say 1 here and agree the body fits.
    assert segment_plan("\\U0001F389" + "a" * 69)["segments"] == 2


def test_the_euro_sign_stays_gsm7_and_costs_two():
    p = segment_plan("\\u20ac" * 80)
    assert p["encoding"] == "GSM-7"
    assert p["units"] == 160
    assert p["segments"] == 1


def test_a_curly_apostrophe_is_not_gsm7():
    assert segment_plan("we\\u2019re open")["encoding"] == "UCS-2"
    assert segment_plan("we're open")["encoding"] == "GSM-7"


def test_tally_counts_only_outbound_rejections():
    rows = [
        {"direction": "outbound-api", "error_code": "30044", "num_segments": "3",
         "sid": "SM1"},
        {"direction": "outbound-api", "error_code": 30044, "num_segments": 1,
         "sid": "SM2"},
        {"direction": "inbound", "error_code": 30044, "sid": "SM3"},
        {"direction": "outbound-api", "error_code": None, "sid": "SM4"},
    ]
    stats = tally(rows)
    assert stats["total"] == 3
    assert stats["blocked"] == 2
    assert stats["multi_segment"] == 1
    assert stats["sids"] == ["SM1", "SM2"]


def test_trial_account_with_rejections_is_blocked():
    state, detail = verdict({"type": "Trial", "status": "active"},
                            {"total": 40, "blocked": 12, "multi_segment": 12})
    assert state == "trial-blocked"
    assert "no amount of retrying" in detail


def test_trial_account_with_no_rejections_is_still_exposed():
    state, _ = verdict({"type": "Trial", "status": "active"},
                       {"total": 40, "blocked": 0, "multi_segment": 0})
    assert state == "trial-exposed"


def test_30044_on_a_paid_account_means_the_wrong_account_is_being_read():
    state, detail = verdict({"type": "Full", "status": "active"},
                            {"total": 40, "blocked": 3, "multi_segment": 3})
    assert state == "unexpected"
    assert "different account" in detail
''',
"test_js_file": "twilio-trial-segment-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { segmentPlan, tally, verdict } from './twilio-trial-segment-audit.mjs';

test('160 ascii characters is one gsm7 segment', () => {
  const p = segmentPlan('a'.repeat(160));
  assert.equal(p.encoding, 'GSM-7');
  assert.equal(p.segments, 1);
  assert.equal(p.per_segment, 160);
});

test('one more character drops the budget to 153', () => {
  const p = segmentPlan('a'.repeat(161));
  assert.equal(p.per_segment, 153);
  assert.equal(p.segments, 2);
});

test('a single emoji flips the whole body to ucs2', () => {
  assert.equal(segmentPlan('Welcome aboard').encoding, 'GSM-7');
  const p = segmentPlan('Welcome aboard \\u{1F389}');
  assert.equal(p.encoding, 'UCS-2');
  assert.equal(p.per_segment, 70);
});

test('an emoji counts as two utf16 units', () => {
  assert.equal(segmentPlan('\\u{1F389}' + 'a'.repeat(69)).segments, 2);
});

test('the euro sign stays gsm7 and costs two', () => {
  const p = segmentPlan('\\u20ac'.repeat(80));
  assert.equal(p.encoding, 'GSM-7');
  assert.equal(p.units, 160);
  assert.equal(p.segments, 1);
});

test('a curly apostrophe is not gsm7', () => {
  assert.equal(segmentPlan('we\\u2019re open').encoding, 'UCS-2');
  assert.equal(segmentPlan("we're open").encoding, 'GSM-7');
});

test('tally counts only outbound rejections', () => {
  const stats = tally([
    { direction: 'outbound-api', error_code: '30044', num_segments: '3', sid: 'SM1' },
    { direction: 'outbound-api', error_code: 30044, num_segments: 1, sid: 'SM2' },
    { direction: 'inbound', error_code: 30044, sid: 'SM3' },
    { direction: 'outbound-api', error_code: null, sid: 'SM4' },
  ]);
  assert.equal(stats.total, 3);
  assert.equal(stats.blocked, 2);
  assert.equal(stats.multi_segment, 1);
  assert.deepEqual(stats.sids, ['SM1', 'SM2']);
});

test('trial account with rejections is blocked', () => {
  const [state, detail] = verdict({ type: 'Trial', status: 'active' },
    { total: 40, blocked: 12, multi_segment: 12 });
  assert.equal(state, 'trial-blocked');
  assert.match(detail, /no amount of retrying/);
});

test('trial account with no rejections is still exposed', () => {
  const [state] = verdict({ type: 'Trial', status: 'active' },
    { total: 40, blocked: 0, multi_segment: 0 });
  assert.equal(state, 'trial-exposed');
});

test('30044 on a paid account means the wrong account is being read', () => {
  const [state, detail] = verdict({ type: 'Full', status: 'active' },
    { total: 40, blocked: 3, multi_segment: 3 });
  assert.equal(state, 'unexpected');
  assert.match(detail, /different account/);
});
''',
"faq": [
 ("Why does one emoji cost so much?",
  "Because SMS has no mixed encoding. Every character in the body has to use the same alphabet, so a single character outside GSM-7 re-encodes the entire message as UCS-2. The budget falls from 160 characters to 70 for a single segment and from 153 to 67 for concatenated ones, and a 150-character body that was one segment becomes three."),
 ("Where does 30044 come from if the message is short?",
  "From the encoding rather than the length. A trial account's cap is on the message, and a body that reads as short on screen can be well over the limit once it is counted in UCS-2 units. Run the body through the segment planner in this script and it will tell you the unit count the carrier will see."),
 ("Can I get 30044 on a paid account?",
  "No, which is why the script has a state for it. 30044 is the trial-account length rejection. If you are seeing it in the Messages list of an account whose type is not Trial, the credential you are auditing with and the credential your application sends with are pointing at different accounts, and that mismatch is the real finding."),
 ("Does Smart Encoding fix this?",
  "Partly. Smart Encoding substitutes common look-alike characters, so a curly apostrophe or an en dash pasted from a document becomes its GSM-7 equivalent and the body stays at 160. It cannot help with an emoji or an accented name, because there is no GSM-7 character to substitute. It is a setting on the Messaging Service, and this script prints the call rather than making it."),
 ("Should I test with real customer data?",
  "Test with realistic data, which is not the same thing. The failures come from names with accents, addresses with line breaks and text pasted out of a word processor, so a template filled with 'Test User' will pass every time. Substitute a name like Zoe with the diaeresis and see what the planner says."),
],
"related": [
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never reach a final state"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering that drops SMS silently"),
 ("/twilio/outbound-messaging-disabled-30037/", "An account that cannot send at all"),
],
"citations": [CITE_30044, CITE_MSG, CITE_ACCOUNT, CITE_SERVICES],
},

{
"slug": "outbound-messaging-disabled-30037",
"title": "Outbound messaging is off, so every send fails with 30037",
"description": "One subaccount returns 30037 on every send while the others are fine. Read Accounts.json for status, attribute the failures by account_sid, and find it.",
"h1": "outbound messaging is off, so every send fails with 30037",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30037", "outbound message not allowed",
             "twilio subaccount suspended", "twilio account status",
             "twilio wrong account sid"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One tenant stopped receiving messages. Not slowly, not partially &mdash; every send from that subaccount comes back with <code>error_code=30037</code>, &ldquo;outbound message not allowed&rdquo;, while the other nineteen tenants on the same code, the same numbers and the same deploy are entirely unaffected. Nothing changed on your side, which is exactly what makes it hard to look for.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}.json</code> for the account you are sending as and check <code>status</code>. Anything other than <code>active</code> and that is your answer. Then enumerate <code>GET /2010-04-01/Accounts.json</code> to get the status of every subaccount at once, because the one that is failing is rarely the one you were looking at.</p>
<p>Attribute the failures rather than counting them. Every Message row carries an <code>account_sid</code>. Bucket the <code>30037</code>s by that field and you learn which account cannot send, and whether it is one of yours at all &mdash; a <code>30037</code> attributed to a SID that is not in your account list means the sending code is authenticating as something you are not auditing.</p>""",
"problem": """<p>The failure is per account, and almost every debugging instinct is per request. You check the body, the To number, the From number, the Messaging Service, the campaign. All of them are identical to the nineteen tenants that work. The variable is the account the credential belongs to, and the account is the one thing nobody re-reads because it has been correct since the day it was created.</p>
<p>It gets worse when the answer is that the credential is wrong rather than the account. A key created in the parent and used to send as a subaccount, or a staging SID left in an environment variable, produces exactly the same symptom: sends that should be fine are refused on an account you were not thinking about. The error tells you a send was not allowed. It does not tell you which account did the not-allowing.</p>
<p>And a suspended subaccount is silent. There is no notification into your application, no state change you can subscribe to, no difference in the API response until something tries to send. It is a field on a resource nobody reads until the day it matters.</p>""",
"why": """<p><strong>Status lives on a resource nobody polls.</strong> <code>status</code> on the Account resource is <code>active</code>, <code>suspended</code> or <code>closed</code>. It is read-only information that changes for billing, compliance or fraud reasons, entirely outside your deploy cycle, and there is no reason your application would ever have looked at it.</p>
<p><strong>The parent looks healthy while the child is not.</strong> Enumerating subaccounts is the only way to see this. Reading the account your credential belongs to tells you about that account, and the one that has stopped sending is usually a subaccount you have not thought about since onboarding.</p>
<p><strong>A parent API Key cannot read a subaccount's messages.</strong> API Keys are scoped to the account they were created in. The status enumeration works from the parent, because subaccounts are listed there; the Messages sweep does not, and has to run with the failing subaccount's own key. That split is why this script takes the account to sweep as an argument.</p>
<p><strong>30037 and a wrong SID are indistinguishable from the error alone.</strong> Outbound messaging genuinely disabled, an account suspended for billing, and code that authenticates as the wrong account all produce the same code on the same field. Only the join between the Messages list and the account list separates them.</p>""",
"steps": [
 {"h": "Read the status of the account you are sending as",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code>. <code>status</code> is <code>active</code>, <code>suspended</code> or <code>closed</code>; <code>type</code> is <code>Trial</code> or <code>Full</code>. A suspended or closed account explains every failing send on its own and no further investigation is needed.</p>"""},
 {"h": "Enumerate every subaccount",
  "body": """<p><code>GET /2010-04-01/Accounts.json?PageSize=100</code> from the parent, following <code>next_page_uri</code>. This lists the parent and all its subaccounts with their statuses in one sweep, and it is the only way to find the suspended tenant you were not looking for.</p>"""},
 {"h": "Sweep the Messages list and bucket by account_sid",
  "body": """<p><code>Messages.json?DateSent&gt;={since}&amp;PageSize=1000</code>, filtered client-side for <code>error_code == 30037</code>. Bucket by the <code>account_sid</code> on each row. Read the code as an integer &mdash; it arrives as a string often enough that a raw comparison quietly returns nothing.</p>"""},
 {"h": "Join the two, and pay attention to what does not join",
  "body": """<p>A bucket whose <code>account_sid</code> is not in the account list is the most useful finding in the report. It means the credential doing the sending is not one of the accounts you are auditing, which is a configuration problem rather than a Twilio one, and no amount of reading the account you thought you were on would have found it.</p>"""},
 {"h": "Reactivate, or take it to Support",
  "body": """<p>A suspended subaccount is reactivated by writing <code>Status=active</code> to <code>/2010-04-01/Accounts/{SubAccountSid}.json</code>. A closed one is permanent. A parent suspended by Twilio, or messaging disabled at the platform level, only Support can lift. The script prints the exact resource and field and stops there.</p>"""},
],
"verify": """<p>Re-run after reactivating. Every account should read <code>active</code> and the 30037 count should be zero.</p>
<pre><code class="language-bash">python3 twilio_outbound_disabled_audit.py --days 3
# 20 account(s), 0 unable to send</code></pre>""",
"code_intro": "One paginated GET over the accounts, one over the messages, and a join between them. Read access is enough. The attribution and the verdict are pure functions, because the whole difficulty of this problem is deciding which of four indistinguishable causes you are looking at, and that decision is worth having in a form you can read and test.",
"py_file": "twilio_outbound_disabled_audit.py",
"py": '''"""Report Twilio accounts that cannot send, and the 30037s attributed to them.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_outbound_disabled_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

NOT_ALLOWED = 30037


def error_code(message):
    """Read error_code as an integer, or None.

    It arrives as a string often enough that comparing the raw value against
    30037 is how this audit reports nothing on an account that is failing every
    send.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def attribute(messages, code=NOT_ALLOWED):
    """Bucket outbound messages by the account that actually sent them.

    Pure, so the grouping rule can be tested without a network. account_sid is
    the field that distinguishes a subaccount problem from a credential
    problem, and it is on every Message row.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        sid = str(m.get("account_sid") or "unknown")
        row = out.setdefault(sid, {"total": 0, "blocked": 0, "sids": []})
        row["total"] += 1
        if error_code(m) == code:
            row["blocked"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
    return out


def verdict(account, stats):
    """Classify one account against the 30037s attributed to it. Pure.

    account is None when the failures belong to a SID that is not in the
    account list at all, which is the finding worth having. Returns
    (state, detail).
    """
    total = int((stats or {}).get("total") or 0)
    blocked = int((stats or {}).get("blocked") or 0)

    if account is None:
        return ("unknown-account",
                "%d of %d message(s) rejected with 30037 on an account_sid that "
                "is not in this account list. The code doing the sending is "
                "authenticating as something you are not auditing: check the "
                "Account SID in its environment." % (blocked, total))

    status = str(account.get("status") or "").strip().lower()
    kind = str(account.get("type") or "").strip()

    if status == "closed":
        return ("closed",
                "account is closed, so every send fails permanently. Closure is "
                "not reversible: move the numbers and the traffic to a live "
                "account. %d message(s) attempted in the window." % total)

    if status == "suspended":
        return ("suspended",
                "account is suspended, so outbound messaging is off for every "
                "sender under it. %d message(s) attempted, %d rejected with "
                "30037." % (total, blocked))

    if blocked:
        return ("messaging-disabled",
                "account status is active but %d of %d message(s) were rejected "
                "with 30037. Outbound messaging is disabled on this account "
                "specifically, or the sending credential belongs to a different "
                "one." % (blocked, total))

    return ("active",
            "%s account, %d message(s) in the window, none rejected with 30037"
            % (kind or "unknown", total))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page(session, url, key, params, limit):
    """Page any 2010-04-01 list. next_page_uri is a path, not an absolute URL."""
    out = []
    while url and len(out) < limit:
        body = get(session, url, **params)
        out.extend(body.get(key, []))
        nxt = body.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=3,
                    help="how far back to read the Messages list")
    ap.add_argument("--account",
                    help="account to sweep for messages; defaults to the "
                         "credential's own account. An API Key cannot read a "
                         "subaccount's Messages, so run this with that "
                         "subaccount's own key.")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
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

    accounts = page(session, "%s/Accounts.json" % BASE, "accounts",
                    {"PageSize": 100}, 1000)
    by_sid = {str(a.get("sid")): a for a in accounts}

    sweep = args.account or account
    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = page(session, "%s/Accounts/%s/Messages.json" % (BASE, sweep),
                    "messages", {"PageSize": 1000, "DateSent>": since},
                    args.max_messages)
    buckets = attribute(messages)

    bad = 0
    for sid in sorted(set(by_sid) | set(buckets)):
        stats = buckets.get(sid, {"total": 0, "blocked": 0, "sids": []})
        acct = by_sid.get(sid)
        state, detail = verdict(acct, stats)
        label = (acct or {}).get("friendly_name") or sid
        line = "%-18s %s (%s)  %s" % (state, sid, label, detail)
        if state == "active":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if stats["sids"]:
            log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
        if state == "suspended":
            log.warning("  repair: reactivate by writing Status=active to "
                        "%s/Accounts/%s.json. If the parent was suspended by "
                        "Twilio, only Support can lift it.", BASE, sid)
        elif state == "messaging-disabled":
            log.warning("  repair: confirm the credential's Account SID matches "
                        "this account, then ask Twilio Support to re-enable "
                        "outbound messaging on %s.", sid)
        elif state == "unknown-account":
            log.warning("  repair: no Twilio call fixes this. Find the "
                        "TWILIO_ACCOUNT_SID your sender is configured with and "
                        "reconcile it with the account you meant to send as.")
        else:
            log.warning("  repair: a closed account cannot be reopened. Move "
                        "the numbers and the traffic to a live account.")

    log.info("%d account(s), %d unable to send", len(by_sid), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-outbound-disabled-audit.mjs",
"js": '''/**
 * Report Twilio accounts that cannot send, and the 30037s attributed to them.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const NOT_ALLOWED = 30037;

/**
 * Read error_code as a number, or null. It arrives as a string often enough
 * that a raw comparison against 30037 reports nothing on an account that is
 * failing every send.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Bucket outbound messages by the account that actually sent them. Pure, so the
 * grouping rule can be tested without a network. account_sid is the field that
 * distinguishes a subaccount problem from a credential problem.
 */
export function attribute(messages, code = NOT_ALLOWED) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const sid = String(m.account_sid ?? 'unknown');
    if (!out.has(sid)) out.set(sid, { total: 0, blocked: 0, sids: [] });
    const row = out.get(sid);
    row.total += 1;
    if (errorCode(m) === code) {
      row.blocked += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
    }
  }
  return out;
}

/**
 * Classify one account against the 30037s attributed to it. Pure. account is
 * null when the failures belong to a SID that is not in the account list at
 * all, which is the finding worth having. Returns [state, detail].
 */
export function verdict(account, stats) {
  const total = Number(stats?.total ?? 0);
  const blocked = Number(stats?.blocked ?? 0);

  if (account === null || account === undefined) {
    return ['unknown-account',
      `${blocked} of ${total} message(s) rejected with 30037 on an account_sid ` +
      'that is not in this account list. The code doing the sending is ' +
      'authenticating as something you are not auditing: check the Account SID ' +
      'in its environment.'];
  }

  const status = String(account.status ?? '').trim().toLowerCase();
  const kind = String(account.type ?? '').trim();

  if (status === 'closed') {
    return ['closed',
      'account is closed, so every send fails permanently. Closure is not ' +
      'reversible: move the numbers and the traffic to a live account. ' +
      `${total} message(s) attempted in the window.`];
  }

  if (status === 'suspended') {
    return ['suspended',
      'account is suspended, so outbound messaging is off for every sender ' +
      `under it. ${total} message(s) attempted, ${blocked} rejected with 30037.`];
  }

  if (blocked) {
    return ['messaging-disabled',
      `account status is active but ${blocked} of ${total} message(s) were ` +
      'rejected with 30037. Outbound messaging is disabled on this account ' +
      'specifically, or the sending credential belongs to a different one.'];
  }

  return ['active',
    `${kind || 'unknown'} account, ${total} message(s) in the window, none ` +
    'rejected with 30037'];
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

/** Page any 2010-04-01 list. next_page_uri is a path, not an absolute URL. */
export async function pageAll(auth, url, key, params, limit) {
  const out = [];
  let next = url;
  let p = params;
  while (next && out.length < limit) {
    const body = await get(auth, next, p);
    out.push(...(body[key] ?? []));
    next = body.next_page_uri ? HOST + body.next_page_uri : null;
    p = {};
  }
  return out.slice(0, limit);
}

function argOf(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
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
  const days = Number(argOf('--days', 3));
  const sweep = argOf('--account', account);

  const accounts = await pageAll(auth, `${BASE}/Accounts.json`, 'accounts',
                                 { PageSize: 100 }, 1000);
  const bySid = new Map(accounts.map((a) => [String(a.sid), a]));

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const messages = await pageAll(auth, `${BASE}/Accounts/${sweep}/Messages.json`,
                                 'messages',
                                 { PageSize: 1000, 'DateSent>': since }, 20000);
  const buckets = attribute(messages);

  let bad = 0;
  const sids = [...new Set([...bySid.keys(), ...buckets.keys()])].sort();
  for (const sid of sids) {
    const stats = buckets.get(sid) ?? { total: 0, blocked: 0, sids: [] };
    const acct = bySid.get(sid) ?? null;
    const [state, detail] = verdict(acct, stats);
    const label = acct?.friendly_name || sid;
    const line = `${state.padEnd(18)} ${sid} (${label})  ${detail}`;
    if (state === 'active') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (stats.sids.length) console.warn(`  message sids: ${stats.sids.join(', ')}`);
    if (state === 'suspended') {
      console.warn('  repair: reactivate by writing Status=active to ' +
                   `${BASE}/Accounts/${sid}.json. If the parent was suspended ` +
                   'by Twilio, only Support can lift it.');
    } else if (state === 'messaging-disabled') {
      console.warn("  repair: confirm the credential's Account SID matches this " +
                   'account, then ask Twilio Support to re-enable outbound ' +
                   `messaging on ${sid}.`);
    } else if (state === 'unknown-account') {
      console.warn('  repair: no Twilio call fixes this. Find the ' +
                   'TWILIO_ACCOUNT_SID your sender is configured with and ' +
                   'reconcile it with the account you meant to send as.');
    } else {
      console.warn('  repair: a closed account cannot be reopened. Move the ' +
                   'numbers and the traffic to a live account.');
    }
  }

  console.log(`${bySid.size} account(s), ${bad} unable to send`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Four causes produce one error code, so the tests are one per cause: suspended, closed, active-but-refused, and failures attributed to a SID that is not yours. The last is the one that saves the most time, because no amount of reading the account you thought you were on will ever surface it.",
"test_py_file": "test_twilio_outbound_disabled_audit.py",
"test_py": '''from twilio_outbound_disabled_audit import attribute, verdict


def test_attribute_buckets_by_account_sid_and_skips_inbound():
    rows = [
        {"direction": "outbound-api", "account_sid": "ACchild",
         "error_code": "30037", "sid": "SM1"},
        {"direction": "outbound-api", "account_sid": "ACchild",
         "error_code": 30037, "sid": "SM2"},
        {"direction": "outbound-api", "account_sid": "ACparent",
         "error_code": None, "sid": "SM3"},
        {"direction": "inbound", "account_sid": "ACchild",
         "error_code": 30037, "sid": "SM4"},
    ]
    buckets = attribute(rows)
    assert buckets["ACchild"]["total"] == 2
    assert buckets["ACchild"]["blocked"] == 2
    assert buckets["ACparent"]["blocked"] == 0
    assert buckets["ACchild"]["sids"] == ["SM1", "SM2"]


def test_other_error_codes_are_not_counted():
    rows = [{"direction": "outbound-api", "account_sid": "AC1",
             "error_code": 30007, "sid": "SM1"}]
    assert attribute(rows)["AC1"]["blocked"] == 0


def test_suspended_account_explains_every_failure():
    state, detail = verdict({"status": "suspended", "type": "Full"},
                            {"total": 120, "blocked": 120})
    assert state == "suspended"
    assert "every sender" in detail


def test_closed_account_is_permanent():
    state, detail = verdict({"status": "closed", "type": "Full"},
                            {"total": 0, "blocked": 0})
    assert state == "closed"
    assert "not reversible" in detail


def test_active_account_with_30037_means_messaging_is_disabled():
    state, detail = verdict({"status": "active", "type": "Full"},
                            {"total": 90, "blocked": 90})
    assert state == "messaging-disabled"
    assert "disabled on this account" in detail


def test_active_account_with_no_rejections_is_fine():
    state, _ = verdict({"status": "active", "type": "Full"},
                       {"total": 90, "blocked": 0})
    assert state == "active"


def test_failures_on_a_sid_outside_the_account_list_are_a_credential_problem():
    state, detail = verdict(None, {"total": 40, "blocked": 40})
    assert state == "unknown-account"
    assert "Account SID" in detail
''',
"test_js_file": "twilio-outbound-disabled-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attribute, verdict } from './twilio-outbound-disabled-audit.mjs';

test('attribute buckets by account_sid and skips inbound', () => {
  const buckets = attribute([
    { direction: 'outbound-api', account_sid: 'ACchild', error_code: '30037', sid: 'SM1' },
    { direction: 'outbound-api', account_sid: 'ACchild', error_code: 30037, sid: 'SM2' },
    { direction: 'outbound-api', account_sid: 'ACparent', error_code: null, sid: 'SM3' },
    { direction: 'inbound', account_sid: 'ACchild', error_code: 30037, sid: 'SM4' },
  ]);
  assert.equal(buckets.get('ACchild').total, 2);
  assert.equal(buckets.get('ACchild').blocked, 2);
  assert.equal(buckets.get('ACparent').blocked, 0);
  assert.deepEqual(buckets.get('ACchild').sids, ['SM1', 'SM2']);
});

test('other error codes are not counted', () => {
  const buckets = attribute([
    { direction: 'outbound-api', account_sid: 'AC1', error_code: 30007, sid: 'SM1' },
  ]);
  assert.equal(buckets.get('AC1').blocked, 0);
});

test('suspended account explains every failure', () => {
  const [state, detail] = verdict({ status: 'suspended', type: 'Full' },
    { total: 120, blocked: 120 });
  assert.equal(state, 'suspended');
  assert.match(detail, /every sender/);
});

test('closed account is permanent', () => {
  const [state, detail] = verdict({ status: 'closed', type: 'Full' },
    { total: 0, blocked: 0 });
  assert.equal(state, 'closed');
  assert.match(detail, /not reversible/);
});

test('active account with 30037 means messaging is disabled', () => {
  const [state, detail] = verdict({ status: 'active', type: 'Full' },
    { total: 90, blocked: 90 });
  assert.equal(state, 'messaging-disabled');
  assert.match(detail, /disabled on this account/);
});

test('active account with no rejections is fine', () => {
  const [state] = verdict({ status: 'active', type: 'Full' },
    { total: 90, blocked: 0 });
  assert.equal(state, 'active');
});

test('failures on a sid outside the account list are a credential problem', () => {
  const [state, detail] = verdict(null, { total: 40, blocked: 40 });
  assert.equal(state, 'unknown-account');
  assert.match(detail, /Account SID/);
});
''',
"faq": [
 ("Does 30037 always mean the account is suspended?",
  "No, and that is why the script separates the states. Suspended is one cause. Outbound messaging disabled on an otherwise active account is another. A closed account is a third. Code authenticating as an account you did not intend is a fourth, and it is the one that looks least like a Twilio problem because it is not one."),
 ("Why can this script not sweep every subaccount's messages at once?",
  "Because API Keys are scoped to the account they were created in. The parent lists its subaccounts, so status enumeration works from one credential, but a parent key cannot read a subaccount's Messages resource. Run the sweep once per failing subaccount with that subaccount's own read key, which is what --account is for."),
 ("Can the script reactivate a suspended subaccount?",
  "It will not. Reactivating an account is a write to a resource that can immediately start spending money, made from a script that runs unattended. It prints the resource, the field and the value, and a person decides whether the reason for the suspension has actually been dealt with."),
 ("What if the account list and the failing account_sid do not overlap at all?",
  "Then you are auditing the wrong account, and the report says so rather than reporting nothing. It is the most valuable output of the whole script: the sending credential and the auditing credential belong to different accounts, which usually means a stale environment variable pointing at staging."),
 ("Is a suspended parent the same as a suspended subaccount?",
  "In effect, worse. A suspended parent takes every subaccount under it with it, so a report full of failing tenants can have a single cause sitting above all of them. Reactivating a subaccount will not help while the parent is suspended, and lifting a parent suspension is a Support conversation rather than an API call."),
],
"related": [
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never reach a final state"),
 ("/twilio/trial-account-segment-limit-30044/", "A trial account rejecting multi-segment sends"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering that drops SMS silently"),
],
"citations": [CITE_30037, CITE_SUBACCOUNTS, CITE_ACCOUNT, CITE_KEYS],
},

{
"slug": "deactivated-number-recycling",
"title": "Recycled numbers send OTPs to whoever owns them now",
"description": "Carriers reissue deactivated numbers. Pull Twilio's Deactivations feed, reconcile it against your contact list, and find the codes going to a stranger.",
"h1": "recycled numbers send OTPs to whoever owns them now",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio deactivations api", "recycled phone number otp",
             "carrier number reassignment", "twilio deactivation feed",
             "stale consent sms"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every message says <code>delivered</code>. The password reset code, the appointment reminder, the balance alert &mdash; all of them accepted by the carrier, all of them handed to a handset. Just not the handset you think. The number was disconnected eleven weeks ago and reissued to somebody who has never heard of you, and your contact table has not noticed.",
"short_answer": """<p>Pull <code>GET https://messaging.twilio.com/v1/Deactivations?Date=YYYY-MM-DD</code> for each day you want to cover. The response points you at a signed URL through <code>redirect_to</code>, valid for a couple of minutes, holding a newline-delimited list of numbers US carriers deactivated that day. It is free.</p>
<p>Then reconcile. Normalise both sides to the same E.164 form &mdash; your contact table almost certainly does not store them the way the feed does &mdash; intersect, and split the matches by whether you have already sent to them since the deactivation date. Those are the ones that reached a stranger.</p>""",
"problem": """<p>There is no error code for this, because from the network's point of view nothing failed. The number is live, the handset is on, the message was delivered. Every metric you have says the send succeeded, and it did. The only thing that went wrong is the identity behind the number, and that is not a field in any API response.</p>
<p>What you get instead is a slow leak of consequences. Someone receives a verification code for an account they do not have, and either ignores it or uses it. Someone receives marketing they never consented to and reports it as spam. Complaint rates climb, and eventually the carriers start filtering your traffic with 30007 &mdash; at which point you have a delivery problem that looks like a content problem and is actually a data problem three months old.</p>
<p>Meanwhile your consent record still says yes. It was recorded honestly, by the previous owner, and it has silently transferred to a person who never gave it. That is the part that turns an operational nuisance into a compliance exposure.</p>""",
"why": """<p><strong>Nothing tells you.</strong> The carrier does not signal reassignment on the message. Twilio publishes a daily feed precisely because there is no in-band way to learn this, and a feed only helps you if something is pulling it.</p>
<p><strong>The reconciliation fails on formatting, silently.</strong> The feed is E.164. Contact tables hold <code>(415) 555-0100</code>, <code>415-555-0100</code>, <code>+1 415 555 0100</code> and a stray one with a trailing space. Intersect the raw strings and you match nothing, the report says zero, and everybody concludes the problem does not apply to them.</p>
<p><strong>The download URL expires almost immediately.</strong> <code>redirect_to</code> is signed and short-lived, on the order of a couple of minutes. Fetching it a day later, or logging it for a colleague to run, gets you a 403 and a confusing afternoon.</p>
<p><strong>Send the signed URL your Twilio credentials and it may refuse you.</strong> The redirect target is object storage, not the Twilio API. The signature is the authorisation. An HTTP client that helpfully attaches basic auth to every request, including redirects, is the reason this works on one machine and not another.</p>"""
,
"steps": [
 {"h": "Pull the feed one day at a time",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Deactivations?Date=YYYY-MM-DD</code> with your read credential. Handle both shapes: a JSON body carrying <code>redirect_to</code>, and a redirect response whose <code>Location</code> header carries the same URL. Days outside the retention window return a 404, which is information rather than an error.</p>"""},
 {"h": "Fetch the signed URL without your credentials",
  "body": """<p>The target is object storage and the signature is the authorisation. Use a bare request, not the authenticated session, and do it immediately &mdash; the URL is valid for about two minutes. The body is newline-delimited E.164 numbers.</p>"""},
 {"h": "Normalise both sides before comparing",
  "body": """<p>Strip everything that is not a digit or a leading plus, then add the default country code to a bare national number. Do it to the feed and to your contacts with the same function. This is the step that decides whether the whole audit works, and it is the step that fails quietly when it does not.</p>"""},
 {"h": "Split the matches by whether you have already sent",
  "body": """<p>A match you have not messaged since the deactivation date is a suppression job. A match you have messaged since is an incident: at least one message reached the new owner, and if any of them was a verification code you have an access-control problem rather than a marketing one.</p>"""},
 {"h": "Suppress, re-verify, and run it daily",
  "body": """<p>Suppress every match before the next send, and re-verify ownership rather than reusing the consent record you already have. Then schedule it. The feed is daily and free; a weekly pull means up to six days of messages going to people who never asked for them.</p>"""},
],
"verify": """<p>Run yesterday's feed again after suppressing. Every match should come back as already suppressed and the incident count should be zero.</p>
<pre><code class="language-bash">python3 twilio_deactivations_audit.py --days 7 --contacts contacts.json
# 4,812 deactivation(s) over 7 day(s), 3 match(es), 0 already messaged</code></pre>""",
"code_intro": "One authenticated GET per day for the feed, one unauthenticated GET per signed URL, and no other network access: the contact list is a local file. The reconciliation &mdash; normalising, intersecting, and deciding which matches are incidents &mdash; is pure, which is what the tests exercise, because a normaliser that silently matches nothing is the failure mode of this whole exercise.",
"py_file": "twilio_deactivations_audit.py",
"py": '''"""Reconcile Twilio's daily deactivation feed against your contact list.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime as dt
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_deactivations_audit")

MESSAGING = "https://messaging.twilio.com/v1"


def normalize(raw, default_cc="1"):
    """Reduce any phone number to one comparable E.164 string, or None.

    The feed is E.164. Contact tables are not: they hold (415) 555-0100,
    415-555-0100, +1 415 555 0100 and one with a trailing space. Comparing the
    raw strings matches nothing, the report says zero findings, and everybody
    concludes the problem does not apply to them. Pure, and tested, because this
    function silently decides whether the audit works at all.
    """
    text = str(raw or "").strip()
    if not text:
        return None
    plus = text.startswith("+")
    digits = "".join(c for c in text if c.isdigit())
    if not digits:
        return None
    if not plus and len(digits) == 10:
        digits = str(default_cc) + digits
    elif not plus and len(digits) == 11 and digits.startswith(str(default_cc)):
        pass
    elif not plus and len(digits) < 10:
        return None
    return "+" + digits


def load_contacts(rows, default_cc="1"):
    """Normalise a contact list into number -> record. Pure.

    Accepts plain strings or dicts carrying number, suppressed and last_sent_at.
    """
    out = {}
    for row in rows:
        record = {"number": row} if isinstance(row, str) else dict(row)
        key = normalize(record.get("number"), default_cc)
        if key:
            record["number"] = key
            out[key] = record
    return out


def reconcile(deactivations, contacts):
    """Intersect the feed with the contact list. Pure.

    deactivations: number -> deactivation date (YYYY-MM-DD).
    contacts: number -> record, both already normalised.
    """
    matches = []
    for number, on in deactivations.items():
        record = contacts.get(number)
        if record is None:
            continue
        matches.append({
            "number": number,
            "deactivated_on": on,
            "last_sent_at": record.get("last_sent_at"),
            "suppressed": bool(record.get("suppressed")),
            "label": record.get("label") or record.get("name") or "",
        })
    return sorted(matches, key=lambda m: m["number"])


def verdict(match):
    """Classify one match. Pure. Returns (state, detail).

    Dates are compared as ISO strings on the first ten characters, so a full
    timestamp and a bare date compare correctly against each other.
    """
    on = str(match.get("deactivated_on") or "")[:10]
    sent = str(match.get("last_sent_at") or "")[:10]

    if match.get("suppressed"):
        return ("suppressed",
                "already suppressed. Keep the record: it is the evidence that "
                "consent for this number ended on %s." % on)

    if sent and on and sent >= on:
        return ("misdelivered",
                "deactivated %s and you sent to it on %s. Those messages "
                "reached whoever owns the number now. If any of them carried a "
                "verification code, treat it as an access-control incident."
                % (on, sent))

    return ("at-risk",
            "deactivated %s and still active in your list. The next send goes "
            "to a stranger and the consent record you hold is the previous "
            "owner's." % on)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30, allow_redirects=False)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    return r


def feed_for(session, day):
    """Numbers deactivated on one day, or an empty list.

    The API answers with a short-lived signed URL, either as redirect_to in a
    JSON body or as a Location header on a redirect. The signature is the
    authorisation on that URL, so it is fetched with a bare request: an HTTP
    client that attaches basic auth to the redirect too is why this works on one
    machine and not another.
    """
    r = get(session, "%s/Deactivations" % MESSAGING, Date=day)
    if r.status_code == 404:
        log.info("no deactivation feed published for %s", day)
        return []
    target = r.headers.get("Location")
    if not target:
        try:
            target = (r.json() or {}).get("redirect_to")
        except ValueError:
            target = None
    if not target:
        log.warning("no redirect_to for %s (status %d)", day, r.status_code)
        return []

    body = requests.get(target, timeout=60)
    body.raise_for_status()
    return [line.strip() for line in body.text.splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how many days of the feed to pull, ending yesterday")
    ap.add_argument("--contacts", required=True,
                    help="JSON file: a list of numbers, or of objects with "
                         "number, suppressed and last_sent_at")
    ap.add_argument("--country-code", default="1",
                    help="country code to assume for bare national numbers")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    with open(args.contacts, encoding="utf-8") as fh:
        contacts = load_contacts(json.load(fh), args.country_code)
    log.info("%d contact(s) after normalisation", len(contacts))

    session = requests.Session()
    session.auth = (key, secret)

    deactivations = {}
    for offset in range(1, args.days + 1):
        day = (dt.date.today() - dt.timedelta(days=offset)).isoformat()
        for raw in feed_for(session, day):
            number = normalize(raw, args.country_code)
            if number and number not in deactivations:
                deactivations[number] = day

    matches = reconcile(deactivations, contacts)
    incidents = 0
    for match in matches:
        state, detail = verdict(match)
        line = "%-13s %s  %s" % (state, match["number"], detail)
        if state == "suppressed":
            log.info(line)
            continue
        if state == "misdelivered":
            incidents += 1
        log.warning(line)
        log.warning("  repair: suppress %s in your contact table now, and "
                    "re-verify ownership before you send to it again. Do not "
                    "carry the old consent record onto a recycled number.",
                    match["number"])

    log.info("%d deactivation(s) over %d day(s), %d match(es), %d already "
             "messaged", len(deactivations), args.days, len(matches), incidents)
    return 1 if matches else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-deactivations-audit.mjs",
"js": '''/**
 * Reconcile Twilio's daily deactivation feed against your contact list.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
import { readFile } from 'node:fs/promises';

const MESSAGING = 'https://messaging.twilio.com/v1';

/**
 * Reduce any phone number to one comparable E.164 string, or null.
 *
 * The feed is E.164. Contact tables are not: they hold (415) 555-0100,
 * 415-555-0100, +1 415 555 0100 and one with a trailing space. Comparing the
 * raw strings matches nothing, the report says zero findings, and everybody
 * concludes the problem does not apply to them. Pure, and tested, because this
 * function silently decides whether the audit works at all.
 */
export function normalize(raw, defaultCc = '1') {
  const text = String(raw ?? '').trim();
  if (!text) return null;
  const plus = text.startsWith('+');
  let digits = text.replace(/[^0-9]/g, '');
  if (!digits) return null;
  if (!plus && digits.length === 10) digits = String(defaultCc) + digits;
  else if (!plus && digits.length === 11 && digits.startsWith(String(defaultCc))) {
    // already national plus country code
  } else if (!plus && digits.length < 10) return null;
  return `+${digits}`;
}

/**
 * Normalise a contact list into a Map of number to record. Pure. Accepts plain
 * strings or objects carrying number, suppressed and last_sent_at.
 */
export function loadContacts(rows, defaultCc = '1') {
  const out = new Map();
  for (const row of rows) {
    const record = typeof row === 'string' ? { number: row } : { ...row };
    const key = normalize(record.number, defaultCc);
    if (key) {
      record.number = key;
      out.set(key, record);
    }
  }
  return out;
}

/** Intersect the feed with the contact list. Pure. Both already normalised. */
export function reconcile(deactivations, contacts) {
  const matches = [];
  for (const [number, on] of deactivations) {
    const record = contacts.get(number);
    if (!record) continue;
    matches.push({
      number,
      deactivated_on: on,
      last_sent_at: record.last_sent_at ?? null,
      suppressed: Boolean(record.suppressed),
      label: record.label ?? record.name ?? '',
    });
  }
  return matches.sort((a, b) => (a.number < b.number ? -1 : 1));
}

/**
 * Classify one match. Pure. Returns [state, detail]. Dates are compared as ISO
 * strings on the first ten characters, so a full timestamp and a bare date
 * compare correctly against each other.
 */
export function verdict(match) {
  const on = String(match.deactivated_on ?? '').slice(0, 10);
  const sent = String(match.last_sent_at ?? '').slice(0, 10);

  if (match.suppressed) {
    return ['suppressed',
      'already suppressed. Keep the record: it is the evidence that consent ' +
      `for this number ended on ${on}.`];
  }

  if (sent && on && sent >= on) {
    return ['misdelivered',
      `deactivated ${on} and you sent to it on ${sent}. Those messages reached ` +
      'whoever owns the number now. If any of them carried a verification code, ' +
      'treat it as an access-control incident.'];
  }

  return ['at-risk',
    `deactivated ${on} and still active in your list. The next send goes to a ` +
    "stranger and the consent record you hold is the previous owner's."];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

/**
 * Numbers deactivated on one day, or an empty array. The API answers with a
 * short-lived signed URL, either as redirect_to in a JSON body or as a Location
 * header on a redirect. The signature is the authorisation on that URL, so it
 * is fetched without the Twilio credentials.
 */
async function feedFor(auth, day) {
  const u = new URL(`${MESSAGING}/Deactivations`);
  u.searchParams.set('Date', day);
  const res = await fetch(u, { headers: { Authorization: auth }, redirect: 'manual' });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (res.status === 404) {
    console.log(`no deactivation feed published for ${day}`);
    return [];
  }
  let target = res.headers.get('location');
  if (!target) {
    try { target = (await res.json())?.redirect_to ?? null; } catch { target = null; }
  }
  if (!target) {
    console.warn(`no redirect_to for ${day} (status ${res.status})`);
    return [];
  }
  const body = await fetch(target);
  if (!body.ok) throw new Error(`${body.status} fetching the signed feed for ${day}`);
  return (await body.text()).split('\\n').map((l) => l.trim()).filter(Boolean);
}

function argOf(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
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
  const path = argOf('--contacts', null);
  if (!path) {
    console.error('--contacts is required: a JSON file of numbers or records');
    process.exitCode = 2;
    return;
  }
  const days = Number(argOf('--days', 7));
  const cc = String(argOf('--country-code', '1'));
  const auth = authHeader(key, secret);

  const contacts = loadContacts(JSON.parse(await readFile(path, 'utf-8')), cc);
  console.log(`${contacts.size} contact(s) after normalisation`);

  const deactivations = new Map();
  for (let offset = 1; offset <= days; offset += 1) {
    const day = new Date(Date.now() - offset * 86400000).toISOString().slice(0, 10);
    for (const raw of await feedFor(auth, day)) {
      const number = normalize(raw, cc);
      if (number && !deactivations.has(number)) deactivations.set(number, day);
    }
  }

  const matches = reconcile(deactivations, contacts);
  let incidents = 0;
  for (const match of matches) {
    const [state, detail] = verdict(match);
    const line = `${state.padEnd(13)} ${match.number}  ${detail}`;
    if (state === 'suppressed') { console.log(line); continue; }
    if (state === 'misdelivered') incidents += 1;
    console.warn(line);
    console.warn(`  repair: suppress ${match.number} in your contact table now, ` +
                 'and re-verify ownership before you send to it again. Do not ' +
                 'carry the old consent record onto a recycled number.');
  }

  console.log(`${deactivations.size} deactivation(s) over ${days} day(s), ` +
              `${matches.length} match(es), ${incidents} already messaged`);
  process.exitCode = matches.length ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The normaliser gets the most tests, because it is the function that decides whether this audit finds anything at all. A version that returns the raw string matches nothing against an E.164 feed, prints a clean report, and is indistinguishable from an account with no problem. The rest pin the split between a number to suppress and a message already sent to a stranger.",
"test_py_file": "test_twilio_deactivations_audit.py",
"test_py": '''from twilio_deactivations_audit import load_contacts, normalize, reconcile, verdict


def test_every_common_contact_format_normalises_to_one_key():
    for raw in ["+14155550100", "(415) 555-0100", "415-555-0100",
                " +1 415 555 0100 ", "1 (415) 555 0100"]:
        assert normalize(raw) == "+14155550100"


def test_a_non_us_number_keeps_its_own_country_code():
    assert normalize("+44 20 7946 0100") == "+442079460100"


def test_junk_and_short_numbers_are_dropped_rather_than_guessed():
    assert normalize("") is None
    assert normalize(None) is None
    assert normalize("not a number") is None
    assert normalize("5550100") is None


def test_reconcile_matches_across_different_formats():
    # The whole point: the feed is E.164 and the contact table is not.
    contacts = load_contacts([
        {"number": "(415) 555-0100", "last_sent_at": None},
        {"number": "415-555-0199"},
    ])
    deactivations = {"+14155550100": "2026-08-01"}
    matches = reconcile(deactivations, contacts)
    assert [m["number"] for m in matches] == ["+14155550100"]
    assert matches[0]["deactivated_on"] == "2026-08-01"


def test_sending_after_the_deactivation_date_is_an_incident():
    state, detail = verdict({"number": "+14155550100",
                             "deactivated_on": "2026-08-01",
                             "last_sent_at": "2026-08-14T09:12:00Z"})
    assert state == "misdelivered"
    assert "access-control incident" in detail


def test_a_send_before_the_deactivation_is_only_at_risk():
    state, _ = verdict({"number": "+14155550100",
                        "deactivated_on": "2026-08-01",
                        "last_sent_at": "2026-07-30"})
    assert state == "at-risk"


def test_a_match_with_no_sends_is_still_at_risk():
    state, detail = verdict({"number": "+14155550100",
                             "deactivated_on": "2026-08-01",
                             "last_sent_at": None})
    assert state == "at-risk"
    assert "consent record" in detail


def test_an_already_suppressed_match_is_not_reported_as_a_problem():
    state, _ = verdict({"number": "+14155550100", "deactivated_on": "2026-08-01",
                        "last_sent_at": "2026-08-14", "suppressed": True})
    assert state == "suppressed"
''',
"test_js_file": "twilio-deactivations-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  loadContacts, normalize, reconcile, verdict,
} from './twilio-deactivations-audit.mjs';

test('every common contact format normalises to one key', () => {
  for (const raw of ['+14155550100', '(415) 555-0100', '415-555-0100',
    ' +1 415 555 0100 ', '1 (415) 555 0100']) {
    assert.equal(normalize(raw), '+14155550100');
  }
});

test('a non us number keeps its own country code', () => {
  assert.equal(normalize('+44 20 7946 0100'), '+442079460100');
});

test('junk and short numbers are dropped rather than guessed', () => {
  assert.equal(normalize(''), null);
  assert.equal(normalize(null), null);
  assert.equal(normalize('not a number'), null);
  assert.equal(normalize('5550100'), null);
});

test('reconcile matches across different formats', () => {
  const contacts = loadContacts([
    { number: '(415) 555-0100', last_sent_at: null },
    { number: '415-555-0199' },
  ]);
  const deactivations = new Map([['+14155550100', '2026-08-01']]);
  const matches = reconcile(deactivations, contacts);
  assert.deepEqual(matches.map((m) => m.number), ['+14155550100']);
  assert.equal(matches[0].deactivated_on, '2026-08-01');
});

test('sending after the deactivation date is an incident', () => {
  const [state, detail] = verdict({
    number: '+14155550100',
    deactivated_on: '2026-08-01',
    last_sent_at: '2026-08-14T09:12:00Z',
  });
  assert.equal(state, 'misdelivered');
  assert.match(detail, /access-control incident/);
});

test('a send before the deactivation is only at risk', () => {
  const [state] = verdict({
    number: '+14155550100', deactivated_on: '2026-08-01', last_sent_at: '2026-07-30',
  });
  assert.equal(state, 'at-risk');
});

test('a match with no sends is still at risk', () => {
  const [state, detail] = verdict({
    number: '+14155550100', deactivated_on: '2026-08-01', last_sent_at: null,
  });
  assert.equal(state, 'at-risk');
  assert.match(detail, /consent record/);
});

test('an already suppressed match is not reported as a problem', () => {
  const [state] = verdict({
    number: '+14155550100',
    deactivated_on: '2026-08-01',
    last_sent_at: '2026-08-14',
    suppressed: true,
  });
  assert.equal(state, 'suppressed');
});
''',
"faq": [
 ("How often should the feed run?",
  "Daily. The feed is published per day and it is free, so the only cost of running it every morning is a handful of requests. A weekly pull leaves up to six days during which you are still sending verification codes to numbers that changed hands, and those are the sends that hurt most."),
 ("Why does the download URL stop working?",
  "Because it is signed and short-lived, on the order of a couple of minutes. Fetch it in the same run that asked for it. If you are pasting it into a terminal or handing it to a colleague, it will have expired by the time it is used, and the 403 you get back looks like a permissions problem rather than an expiry."),
 ("Why fetch the signed URL without my Twilio credentials?",
  "Because the target is object storage rather than the Twilio API, and the signature in the URL is the authorisation. An HTTP client configured with basic auth for every request will attach it to the redirect too, and some storage backends reject a request that carries both. Use a bare request for that one fetch."),
 ("Does this apply outside the United States?",
  "The Twilio feed covers US carrier deactivations. The underlying behaviour is not unique to the US, but the data source is, so treat this as a US control and handle other markets with re-verification on a schedule instead. The script's country-code option exists so your non-US contacts normalise correctly rather than being silently dropped."),
 ("What is the connection to carrier filtering?",
  "Complaints. A stranger who receives your marketing or your OTPs reports it, and enough of that damages the sender reputation the carriers score you on. Weeks later the symptom is 30007 filtering on traffic that looks perfectly clean, and the actual cause is a contact list that was never reconciled."),
],
"related": [
 ("/twilio/opted-out-recipients-21610/", "Sends to STOP'd recipients that keep bouncing"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering that drops SMS silently"),
 ("/twilio/landline-destination-30006/", "SMS sent to landlines that can never receive it"),
],
"citations": [CITE_DEACT, CITE_MSG, CITE_30007, CITE_KEYS],
},

]
