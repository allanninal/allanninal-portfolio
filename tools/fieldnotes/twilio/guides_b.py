#!/usr/bin/env python3
"""/twilio/ field notes, batch B — the writing.

Four failures that all live in the same place: the Messages list. That resource
has no Status filter and no ErrorCode filter, so every one of these scripts pages
it and does the filtering itself, which is exactly why these problems go unnoticed
for weeks. Read-only throughout: an API Key with read access, never the account
auth token, and the repair is printed for a human to run.
"""

CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_30007 = ("Error 30007: message filtered — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30007")
CITE_21610 = ("Error 21610: attempt to send to unsubscribed recipient — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21610")
CITE_30006 = ("Error 30006: landline or unreachable carrier — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30006")
CITE_21614 = ("Error 21614: 'To' number is not a valid mobile number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21614")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_A2P = ("A2P 10DLC — Twilio Docs",
            "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc")
CITE_OPTOUT = ("Advanced Opt-Out — Twilio Docs",
               "https://www.twilio.com/docs/messaging/tutorials/advanced-opt-out")
CITE_LOOKUP = ("Lookup v2 Line Type Intelligence — Twilio Docs",
               "https://www.twilio.com/docs/lookup/v2-api/line-type-intelligence")
CITE_SCHEDULE = ("Message scheduling — Twilio Docs",
                 "https://www.twilio.com/docs/messaging/features/message-scheduling")
CITE_QUEUEING = ("Scaling, queueing and latency — Twilio Docs",
                 "https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "carrier-filtered-messages-30007",
"title": "Carrier filtering drops your SMS silently with error 30007",
"description": "Messages go undelivered with error_code 30007. Nothing arrives, you are billed anyway, and the Messages list has no error filter to find them with.",
"h1": "carrier filtering drops your SMS silently with error 30007",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30007", "twilio message filtered",
             "twilio undelivered 30007", "carrier filtering sms",
             "twilio message blocked as spam"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The API returned <code>201</code>. The Message SID is in your logs. The status walked <code>queued</code>, <code>sent</code>, and then <code>undelivered</code> with <code>error_code</code> <code>30007</code>, and the recipient saw nothing at all. You were billed for the attempt. No HTTP request failed, no webhook errored, nothing appeared in your exception tracker &mdash; a carrier, or Twilio itself, read the message and dropped it.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and count rows where <code>status</code> is <code>undelivered</code> and <code>error_code</code> is <code>30007</code>, grouped by <code>from</code> or <code>messaging_service_sid</code>. Cross-check with <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error</code>.</p>
<p>The list resource has <strong>no</strong> <code>Status</code> or <code>ErrorCode</code> filter &mdash; only <code>To</code>, <code>From</code>, <code>DateSent</code> and paging. The filtering has to happen in your own code, which is the single reason nobody has a dashboard for this.</p>""",
"problem": """<p>Filtering is the one delivery failure that behaves like success right up until the final status. The request is accepted, the Message resource is created, the segments are priced, the status callback fires. Then the message is quietly discarded somewhere between Twilio and the handset, and the only trace is an integer on a resource nobody is reading.</p>
<p>What makes it expensive is that it is rarely uniform. A single sender in a pool of eight loses reputation, or one campaign's content trips a heuristic, and the aggregate delivery rate for the account slips from 97% to 92% &mdash; a number small enough to be dismissed as carrier noise for a quarter. Underneath it, one sender is at 40% and every customer routed to it has stopped hearing from you.</p>""",
"why": """<p><strong>The Messages list cannot be queried by error.</strong> There is no <code>Status</code> parameter and no <code>ErrorCode</code> parameter on <code>Messages.json</code>. You can filter by <code>To</code>, <code>From</code> and <code>DateSent</code>, and that is the whole list. Finding 30007 means paging every message in the window and filtering client-side, so the check only exists if somebody wrote it.</p>
<p><strong>You are billed for filtered messages.</strong> Twilio charges for the send attempt; the carrier drops it after that. A filtered message costs exactly what a delivered one costs, so cost monitoring will never show a dip and neither will your sent-volume chart.</p>
<p><strong>Reputation attaches to the sender, not the message.</strong> Once a long code is flagged, well-formed messages from it are filtered too. That is why the per-sender rate is the number worth alerting on and the account-wide rate is not: averaging a poisoned sender with seven healthy ones hides the outage.</p>
<p><strong>There is no API that repairs it.</strong> No field to set, no resource to <code>POST</code>. The fix is content, sender registration, and a Support ticket carrying at least three Message SIDs. A script that cannot fix anything is still the only thing that will tell you which three SIDs to send.</p>""",
"steps": [
 {"h": "Page the Messages list over a bounded window",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. Bound it by days and by a hard message cap; a busy account will happily hand you a million rows and the answer does not improve after the first few thousand.</p>"""},
 {"h": "Filter client-side on status and error_code",
  "body": """<p>Keep rows where <code>status == "undelivered"</code> and <code>error_code == 30007</code>. Read <code>error_code</code> defensively: it is <code>null</code> on healthy messages and arrives as a number, so a comparison against the string <code>"30007"</code> silently matches nothing.</p>"""},
 {"h": "Group by sender, not by account",
  "body": """<p>Bucket on <code>messaging_service_sid</code> when it is set and <code>from</code> otherwise. The rate per sender is what tells you whether this is a content problem across the account or one poisoned long code, and those have completely different repairs.</p>"""},
 {"h": "Read the content that is being filtered",
  "body": """<p>Public link shorteners (<code>bit.ly</code> and friends) are the most common single cause, followed by no opt-out language, followed by traffic that does not match the registered A2P campaign use case. Compare the filtered bodies against the <code>MessageSamples</code> you registered; if a marketing blast is going out through a campaign registered for one-time passcodes, the filtering is working as designed.</p>"""},
 {"h": "Collect three SIDs and escalate",
  "body": """<p>There is no API repair. Rewrite the content, confirm the campaign use case matches the traffic, and open a Twilio Support ticket with at least three Message SIDs showing 30007 so the filtering can be reviewed. Keep the script on a schedule afterwards: reputation damage recurs, and the per-sender rate is the early warning.</p>"""},
],
"verify": """<p>Re-run the script over the same window after the content change. Every sender should report <code>clean</code>, or at worst <code>isolated</code>.</p>
<pre><code class="language-bash">python3 twilio_filtered_messages_audit.py --days 7
# 4 sender(s) over 7 day(s), 0 with a filtering problem</code></pre>""",
"code_intro": "One paginated GET over the Messages list and nothing else &mdash; give it an API Key with read access, which is all it can use. The two pure functions are the bucketing and the verdict, because the judgement calls here are arithmetic (what rate counts as a problem, how few failures are too few to escalate) and arithmetic belongs somewhere you can read it.",
"py_file": "twilio_filtered_messages_audit.py",
"py": '''"""Report Twilio senders whose messages are being filtered with error 30007.

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
log = logging.getLogger("twilio_filtered_messages_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

FILTERED = 30007


def error_code(message):
    """Read error_code as an integer, or None.

    It is null on every healthy message and a number on failed ones, but some
    exports and some client libraries hand it back as a string. Comparing the
    raw value against 30007 is the mistake that makes this whole audit report
    zero findings on an account that is drowning in them.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def tally(messages):
    """Bucket outbound messages by the sender a carrier actually judges.

    Pure, so the grouping rule can be tested without a network. Inbound messages
    are skipped: they have no sender of ours and no delivery status worth
    counting.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        key = m.get("messaging_service_sid") or m.get("from") or "unknown sender"
        row = out.setdefault(key, {"total": 0, "filtered": 0, "undelivered": 0,
                                   "sids": []})
        row["total"] += 1
        if str(m.get("status") or "").lower() == "undelivered":
            row["undelivered"] += 1
        if error_code(m) == FILTERED:
            row["filtered"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
    return out


def verdict(stats, min_filtered=3):
    """Classify one sender's filtering rate. Pure, so the thresholds are
    visible and testable rather than buried in a request loop.

    Returns (state, detail).
    """
    total = int(stats.get("total") or 0)
    filtered = int(stats.get("filtered") or 0)

    if not filtered:
        return ("clean", "%d message(s), none filtered" % total)

    rate = (filtered / total) if total else 1.0

    if filtered < min_filtered:
        return ("isolated",
                "%d of %d filtered (%.1f%%). Too few to escalate: Support wants "
                "at least %d Message SIDs before it will review filtering."
                % (filtered, total, rate * 100, min_filtered))

    if rate >= 0.5:
        return ("sender-blocked",
                "%d of %d filtered (%.1f%%). At this rate the sender itself is "
                "the problem, not the wording: reputation damage or an "
                "unregistered sender, and you are billed for every one."
                % (filtered, total, rate * 100))

    return ("filtering",
            "%d of %d filtered (%.1f%%). Content or campaign mismatch: public "
            "link shorteners, no opt-out footer, or traffic that does not match "
            "the registered use case." % (filtered, total, rate * 100))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. There is no Status or ErrorCode filter on this
    resource, so the window and the page cap are the only ways to bound it."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
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
    ap.add_argument("--min-filtered", type=int, default=3,
                    help="fewer than this on one sender is reported as isolated")
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

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages sent since %s", since)
        return 0

    senders = tally(messages)
    bad = 0
    for sender, stats in sorted(senders.items()):
        state, detail = verdict(stats, args.min_filtered)
        line = "%-15s %s  %s" % (state, sender, detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
        log.warning("  repair: no API call fixes 30007. Drop public link "
                    "shorteners, add an opt-out footer, confirm the A2P campaign "
                    "use case matches this traffic, then send those SIDs to "
                    "Twilio Support for a filtering review.")

    log.info("%d sender(s) over %d day(s), %d with a filtering problem",
             len(senders), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-filtered-messages-audit.mjs",
"js": '''/**
 * Report Twilio senders whose messages are being filtered with error 30007.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const FILTERED = 30007;

/**
 * Read error_code as a number, or null. It is null on healthy messages and a
 * number on failed ones, but comparing the raw value against 30007 without this
 * is how the audit reports nothing on an account full of findings.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Bucket outbound messages by the sender a carrier actually judges. Pure, so
 * the grouping rule can be tested without a network.
 */
export function tally(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const key = m.messaging_service_sid || m.from || 'unknown sender';
    if (!out.has(key)) out.set(key, { total: 0, filtered: 0, undelivered: 0, sids: [] });
    const row = out.get(key);
    row.total += 1;
    if (String(m.status ?? '').toLowerCase() === 'undelivered') row.undelivered += 1;
    if (errorCode(m) === FILTERED) {
      row.filtered += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
    }
  }
  return out;
}

/**
 * Classify one sender's filtering rate. Pure, so the thresholds are visible and
 * testable. Returns [state, detail].
 */
export function verdict(stats, minFiltered = 3) {
  const total = Number(stats.total ?? 0);
  const filtered = Number(stats.filtered ?? 0);

  if (!filtered) return ['clean', `${total} message(s), none filtered`];

  const rate = total ? filtered / total : 1;
  const pct = (rate * 100).toFixed(1);

  if (filtered < minFiltered) {
    return ['isolated',
      `${filtered} of ${total} filtered (${pct}%). Too few to escalate: Support ` +
      `wants at least ${minFiltered} Message SIDs before it will review filtering.`];
  }

  if (rate >= 0.5) {
    return ['sender-blocked',
      `${filtered} of ${total} filtered (${pct}%). At this rate the sender itself ` +
      'is the problem, not the wording: reputation damage or an unregistered ' +
      'sender, and you are billed for every one.'];
  }

  return ['filtering',
    `${filtered} of ${total} filtered (${pct}%). Content or campaign mismatch: ` +
    'public link shorteners, no opt-out footer, or traffic that does not match ' +
    'the registered use case.'];
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
  let params = { PageSize: 1000, 'DateSent>=': since };
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

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 7) || 7;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  const senders = tally(messages);
  let bad = 0;
  for (const [sender, stats] of [...senders.entries()].sort()) {
    const [state, detail] = verdict(stats);
    const line = `${state.padEnd(15)} ${sender}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  message sids: ${stats.sids.join(', ')}`);
    console.warn('  repair: no API call fixes 30007. Drop public link shorteners, ' +
                 'add an opt-out footer, confirm the A2P campaign use case matches ' +
                 'this traffic, then send those SIDs to Twilio Support for a ' +
                 'filtering review.');
  }

  console.log(`${senders.size} sender(s) over ${days} day(s), ${bad} with a ` +
              'filtering problem');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three rules are worth pinning down. An <code>error_code</code> that arrives as a string still has to match, because that is the difference between a report full of findings and an empty one. Two filtered messages out of two is <em>not</em> escalated, because Support will not review fewer than three. And a sender above half is a different state from one at five percent, because the first is a dead sender and the second is bad copy.",
"test_py_file": "test_twilio_filtered_messages_audit.py",
"test_py": '''from twilio_filtered_messages_audit import error_code, tally, verdict


def filtered(sid, sender="+15550001111"):
    return {"sid": sid, "from": sender, "status": "undelivered",
            "error_code": 30007, "direction": "outbound-api"}


def delivered(sid, sender="+15550001111"):
    return {"sid": sid, "from": sender, "status": "delivered",
            "error_code": None, "direction": "outbound-api"}


def test_error_code_reads_strings_and_numbers_the_same():
    assert error_code({"error_code": 30007}) == 30007
    assert error_code({"error_code": "30007"}) == 30007
    assert error_code({"error_code": None}) is None
    assert error_code({}) is None


def test_tally_groups_on_the_messaging_service_when_there_is_one():
    rows = tally([
        {"sid": "SM1", "from": "+15550001111", "messaging_service_sid": "MG1",
         "status": "undelivered", "error_code": 30007},
        {"sid": "SM2", "from": "+15550002222", "messaging_service_sid": "MG1",
         "status": "delivered"},
    ])
    assert set(rows) == {"MG1"}
    assert rows["MG1"] == {"total": 2, "filtered": 1, "undelivered": 1,
                           "sids": ["SM1"]}


def test_tally_ignores_inbound_messages():
    rows = tally([{"sid": "SM1", "from": "+15559990000", "direction": "inbound",
                   "status": "received"}])
    assert rows == {}


def test_two_filtered_out_of_two_is_isolated_not_an_outage():
    # Support will not open a filtering review on fewer than three SIDs, so a
    # 100% rate on two messages is deliberately the quieter state.
    state, detail = verdict({"total": 2, "filtered": 2})
    assert state == "isolated"
    assert "at least 3" in detail


def test_a_sender_above_half_is_the_sender_not_the_wording():
    state, detail = verdict({"total": 10, "filtered": 8})
    assert state == "sender-blocked"
    assert "reputation" in detail


def test_a_low_but_real_rate_is_a_content_problem():
    state, detail = verdict({"total": 200, "filtered": 10})
    assert state == "filtering"
    assert "shorteners" in detail


def test_no_filtered_messages_is_clean():
    state, detail = verdict({"total": 500, "filtered": 0})
    assert state == "clean"
    assert "500" in detail


def test_sids_are_capped_at_the_three_support_asks_for():
    rows = tally([filtered("SM%d" % i) for i in range(9)])
    assert rows["+15550001111"]["sids"] == ["SM0", "SM1", "SM2"]
    assert rows["+15550001111"]["filtered"] == 9
    assert verdict(rows["+15550001111"])[0] == "sender-blocked"
    assert verdict(tally([delivered("SM9")])["+15550001111"])[0] == "clean"
''',
"test_js_file": "twilio-filtered-messages-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { errorCode, tally, verdict } from './twilio-filtered-messages-audit.mjs';

const filtered = (sid, sender = '+15550001111') => ({
  sid, from: sender, status: 'undelivered', error_code: 30007,
  direction: 'outbound-api',
});

test('error code reads strings and numbers the same', () => {
  assert.equal(errorCode({ error_code: 30007 }), 30007);
  assert.equal(errorCode({ error_code: '30007' }), 30007);
  assert.equal(errorCode({ error_code: null }), null);
  assert.equal(errorCode({}), null);
});

test('tally groups on the messaging service when there is one', () => {
  const rows = tally([
    { sid: 'SM1', from: '+15550001111', messaging_service_sid: 'MG1',
      status: 'undelivered', error_code: 30007 },
    { sid: 'SM2', from: '+15550002222', messaging_service_sid: 'MG1',
      status: 'delivered' },
  ]);
  assert.deepEqual([...rows.keys()], ['MG1']);
  assert.deepEqual(rows.get('MG1'),
    { total: 2, filtered: 1, undelivered: 1, sids: ['SM1'] });
});

test('tally ignores inbound messages', () => {
  const rows = tally([{ sid: 'SM1', from: '+15559990000', direction: 'inbound',
                        status: 'received' }]);
  assert.equal(rows.size, 0);
});

test('two filtered out of two is isolated, not an outage', () => {
  const [state, detail] = verdict({ total: 2, filtered: 2 });
  assert.equal(state, 'isolated');
  assert.match(detail, /at least 3/);
});

test('a sender above half is the sender, not the wording', () => {
  const [state, detail] = verdict({ total: 10, filtered: 8 });
  assert.equal(state, 'sender-blocked');
  assert.match(detail, /reputation/);
});

test('a low but real rate is a content problem', () => {
  const [state, detail] = verdict({ total: 200, filtered: 10 });
  assert.equal(state, 'filtering');
  assert.match(detail, /shorteners/);
});

test('no filtered messages is clean', () => {
  const [state, detail] = verdict({ total: 500, filtered: 0 });
  assert.equal(state, 'clean');
  assert.match(detail, /500/);
});

test('sids are capped at the three Support asks for', () => {
  const rows = tally([0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => filtered(`SM${i}`)));
  const row = rows.get('+15550001111');
  assert.deepEqual(row.sids, ['SM0', 'SM1', 'SM2']);
  assert.equal(row.filtered, 9);
  assert.equal(verdict(row)[0], 'sender-blocked');
});
''',
"faq": [
 ("Why can't I just query Twilio for messages with error 30007?",
  "Because the Messages list resource has no ErrorCode parameter and no Status parameter. The documented filters are To, From, DateSent, DateSent< and DateSent>, plus paging. Every 30007 report in existence pages the list and filters client-side, which is why so few accounts have one."),
 ("Am I charged for a message that gets filtered?",
  "Yes. Twilio prices the send attempt; the carrier discards it afterwards. Cost and sent-volume charts look identical whether the message arrived or not, so spend monitoring cannot detect this and neither can a delivery count that does not read error_code."),
 ("What actually triggers the filter?",
  "Most often a public link shortener in the body, missing opt-out language, traffic that does not match the registered A2P campaign use case, or a sender whose reputation is already damaged. Carriers do not publish the rules, which is why the per-sender rate matters more than any theory about the wording."),
 ("Why does the script want three Message SIDs before it says anything is wrong?",
  "Because that is what a Support filtering review needs. One or two 30007s inside a large volume is noise you cannot act on; three from the same sender is a ticket. The threshold is an argument so you can lower it when you already know something is wrong."),
 ("Can the script un-filter anything?",
  "No, and nothing else can either. There is no API field, no resource to update, no setting to flip. The repair is a content change, a registration change, or a Support escalation, so the script prints the escalation and the SIDs to attach to it."),
],
"related": [
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
 ("/twilio/landline-destination-30006/", "SMS to landlines that can never receive it"),
 ("/twilio/opted-out-recipients-21610/", "Sends to recipients who already texted STOP"),
],
"citations": [CITE_30007, CITE_MSG, CITE_A2P, CITE_ALERTS],
},


{
"slug": "opted-out-recipients-21610",
"title": "Sends to recipients who texted STOP bounce with 21610",
"description": "Twilio remembers the opt-out and your database does not, so every send to that number is rejected with 21610 and the compliance record keeps growing.",
"h1": "sends to recipients who texted STOP bounce with 21610",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 21610", "twilio unsubscribed recipient",
             "twilio stop keyword", "twilio opt out list",
             "attempt to send to unsubscribed recipient"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Someone replied <code>STOP</code> four months ago. Twilio recorded it, blocked that sender from reaching them, and has been rejecting your sends with <code>21610</code> ever since. You were never charged, so nothing showed up on the bill; your send queue treated the rejection as a transient failure and retried; and the only place the whole story exists is the Messages list, which has no filter for it.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, collect the distinct <code>to</code> values on rows with <code>error_code</code> <code>21610</code>, and separately collect inbound rows whose <code>body</code> is exactly <code>STOP</code>, <code>STOPALL</code>, <code>UNSUBSCRIBE</code>, <code>CANCEL</code>, <code>END</code> or <code>QUIT</code>. Join the two on the consumer's number.</p>
<p>Twilio exposes <strong>no read API for the opt-out list</strong>. These rejections and these inbound keywords are the only evidence available to a read-only credential, which is exactly why the list has to be rebuilt from them and then stored on your side.</p>""",
"problem": """<p>The opt-out is honoured either way &mdash; that is the part that hides it. Twilio rejects the send at request time, the recipient is not contacted, and nobody's phone buzzes. No message is billed. From the outside the system is behaving correctly, and in the narrow sense it is: the platform is enforcing an opt-out that your application forgot.</p>
<p>What you actually have is a record, growing daily, of your application attempting to contact someone who asked you to stop. A regulator, an auditor or a plaintiff reads that as intent. And because most send queues treat a 400 as retryable, the usual shape is not one attempt per campaign but dozens per day against the same number, each one another row.</p>""",
"why": """<p><strong>The opt-out lives on Twilio's side and cannot be read back.</strong> There is no endpoint that lists the numbers who have opted out of a sender or a Messaging Service. Nothing to sync from, nothing to reconcile against &mdash; the state exists, it is enforced, and it is invisible to your code until a send bounces off it.</p>
<p><strong>Nobody told the application.</strong> The STOP arrives as an inbound message. If the inbound webhook is missing, filtered, or wired to a handler that only looks for the words your product cares about, the opt-out is enforced by Twilio and never written to your database. Then your normal sending logic keeps selecting that contact forever.</p>
<p><strong>Opt-out is per sender, and reassignment is real.</strong> A recipient who stopped one long code has not stopped the others, so the same contact can be blocked on one sender in a pool and reachable on another. Separately, carriers recycle numbers: the person who opted out may not be the person who signed up.</p>
<p><strong>Only the recipient can undo it.</strong> START, UNSTOP or YES from their handset is the sole way back. There is no support ticket, no API call and no console button that re-subscribes someone on their behalf, which makes cleaning your own list the entire repair.</p>""",
"steps": [
 {"h": "Page the Messages list over a window you can defend",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. There is no <code>ErrorCode</code> filter, so the window is the only lever you have on the size of the read. Thirty days is usually enough to find the loops; ninety builds a better suppression list.</p>"""},
 {"h": "Collect the rejections",
  "body": """<p>Outbound rows with <code>error_code</code> <code>21610</code>. Group them by <code>to</code> and count: one rejection is a stale contact, forty is a retry loop, and those need different conversations. Cross-check against <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error</code> if you want the request that was rejected.</p>"""},
 {"h": "Match inbound keywords the way Twilio matches them",
  "body": """<p>Twilio compares the <em>whole</em> body, case-insensitively, after trimming whitespace. <code>STOP</code> opts out; <code>stop</code> opts out; <code>STOP please</code> does not. A substring search here inflates your opt-out list with everyone who wrote "please stop sending these at 6am", which is a different problem with a different fix.</p>"""},
 {"h": "Join on the consumer's number",
  "body": """<p>An inbound STOP is keyed on <code>from</code>; an outbound rejection is keyed on <code>to</code>. Both are the same person. The pairing you are looking for is a STOP followed by sends that were rejected afterwards: that is proof the opt-out reached Twilio and never reached your database.</p>"""},
 {"h": "Write the list down on your side, then stop the loop",
  "body": """<p>Mark every number found as unsubscribed in your own store, because nothing on Twilio's side will tell you again. Fix the inbound handler that missed the keyword, make your queue treat <code>21610</code> as permanent rather than retryable, and turn on Advanced Opt-Out on the Messaging Service so keywords and confirmation replies are identical across every sender in the pool.</p>"""},
],
"verify": """<p>Re-run over the same window after the suppression list is loaded. Recipients who opted out should report <code>suppressed</code>, and nothing should be in a retry loop.</p>
<pre><code class="language-bash">python3 twilio_opt_out_audit.py --days 30
# 63 recipient(s) over 30 day(s), 0 still being messaged after STOP</code></pre>""",
"code_intro": "One paginated GET, read with an API Key that has read access and nothing more. Two pure functions carry the note: the keyword matcher, which has to reproduce Twilio's whole-body rule rather than a friendly approximation of it, and the verdict, which decides whether a rejection is a stale contact or a machine that will not take no for an answer.",
"py_file": "twilio_opt_out_audit.py",
"py": '''"""Rebuild Twilio's opt-out list from 21610 rejections and inbound keywords.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_opt_out_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

UNSUBSCRIBED = 21610

OPT_OUT = ("STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT")
OPT_IN = ("START", "UNSTOP", "YES")


def error_code(message):
    """Read error_code as an integer, or None. It is null on healthy messages
    and a number on rejected ones; a string comparison finds nothing."""
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def keyword_kind(body):
    """Return "out", "in" or "" for one inbound message body.

    Twilio matches the entire body, case-insensitively, after trimming
    whitespace. "STOP" opts out and "STOP please" does not. Matching loosely
    here fills the suppression list with people who merely complained, which is
    a different problem with a different repair.
    """
    word = str(body or "").strip().upper()
    if word in OPT_OUT:
        return "out"
    if word in OPT_IN:
        return "in"
    return ""


def tally(messages):
    """Group both directions onto the consumer's number.

    An inbound keyword is keyed on `from`, an outbound rejection on `to`, and
    they are the same person. Pure, so the join can be tested without a network.
    """
    out = {}

    def row(number):
        return out.setdefault(str(number or "unknown"),
                              {"rejected": 0, "stops": 0, "starts": 0, "sids": []})

    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            kind = keyword_kind(m.get("body"))
            if kind == "out":
                row(m.get("from"))["stops"] += 1
            elif kind == "in":
                row(m.get("from"))["starts"] += 1
            continue
        if error_code(m) == UNSUBSCRIBED:
            r = row(m.get("to"))
            r["rejected"] += 1
            if len(r["sids"]) < 3:
                r["sids"].append(m.get("sid"))
    return out


def verdict(record, loop_threshold=10):
    """Classify one recipient. Pure, so the rules stay readable.

    Returns (state, detail).
    """
    rejected = int(record.get("rejected") or 0)
    stops = int(record.get("stops") or 0)
    starts = int(record.get("starts") or 0)

    note = ""
    if starts:
        note = (" A START was seen from this number too, and that re-subscribes "
                "them to one sender only, so the rejections are from a different "
                "sender in the pool.")

    if not rejected:
        if stops:
            return ("suppressed",
                    "texted an opt-out keyword %d time(s) and nothing has been "
                    "sent to them since." % stops + note)
        return ("clean", "no 21610 rejections and no opt-out keywords." + note)

    if rejected >= loop_threshold:
        return ("retry-loop",
                "%d sends rejected with 21610: something is retrying an opt-out "
                "on a loop. Twilio rejects each one at request time so none are "
                "billed, but each is a record of contacting someone who asked "
                "you to stop." % rejected + note)

    if stops:
        return ("ignored-opt-out",
                "texted an opt-out keyword %d time(s), then %d send(s) went out "
                "and were rejected with 21610: the opt-out reached Twilio and "
                "never reached your database." % (stops, rejected) + note)

    return ("invisible-opt-out",
            "%d send(s) rejected with 21610 and no opt-out keyword in this "
            "window: it happened before the window or on another sender. There "
            "is no read API for the opt-out list, so these rejections are the "
            "only evidence you will get." % rejected + note)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. No Status or ErrorCode filter exists on this
    resource, so the date window and the cap are the only bounds available."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--loop-threshold", type=int, default=10,
                    help="rejections against one number that count as a retry loop")
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

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages since %s", since)
        return 0

    people = tally(messages)
    bad = 0
    for number, record in sorted(people.items()):
        state, detail = verdict(record, args.loop_threshold)
        line = "%-18s %s  %s" % (state, number, detail)
        if state in ("clean", "suppressed"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if record["sids"]:
            log.warning("  message sids: %s",
                        ", ".join(str(s) for s in record["sids"]))
        log.warning("  repair: mark %s unsubscribed in your own database. Twilio "
                    "exposes no read API for the opt-out list and only the "
                    "recipient texting START, UNSTOP or YES re-subscribes them. "
                    "Enable Advanced Opt-Out on the Messaging Service so the "
                    "keywords are identical across every sender.", number)

    log.info("%d recipient(s) over %d day(s), %d still being messaged after STOP",
             len(people), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-opt-out-audit.mjs",
"js": '''/**
 * Rebuild Twilio's opt-out list from 21610 rejections and inbound keywords.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const UNSUBSCRIBED = 21610;

const OPT_OUT = ['STOP', 'STOPALL', 'UNSUBSCRIBE', 'CANCEL', 'END', 'QUIT'];
const OPT_IN = ['START', 'UNSTOP', 'YES'];

/** Read error_code as a number, or null. A string comparison finds nothing. */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Return 'out', 'in' or '' for one inbound body. Twilio matches the entire
 * body, case-insensitively, after trimming: 'STOP' opts out, 'STOP please' does
 * not. Matching loosely fills the suppression list with people who complained.
 */
export function keywordKind(body) {
  const word = String(body ?? '').trim().toUpperCase();
  if (OPT_OUT.includes(word)) return 'out';
  if (OPT_IN.includes(word)) return 'in';
  return '';
}

/**
 * Group both directions onto the consumer's number: inbound keywords are keyed
 * on `from`, outbound rejections on `to`, and they are the same person. Pure.
 */
export function tally(messages) {
  const out = new Map();
  const row = (number) => {
    const k = String(number ?? 'unknown');
    if (!out.has(k)) out.set(k, { rejected: 0, stops: 0, starts: 0, sids: [] });
    return out.get(k);
  };

  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) {
      const kind = keywordKind(m.body);
      if (kind === 'out') row(m.from).stops += 1;
      else if (kind === 'in') row(m.from).starts += 1;
      continue;
    }
    if (errorCode(m) === UNSUBSCRIBED) {
      const r = row(m.to);
      r.rejected += 1;
      if (r.sids.length < 3) r.sids.push(m.sid);
    }
  }
  return out;
}

/** Classify one recipient. Pure. Returns [state, detail]. */
export function verdict(record, loopThreshold = 10) {
  const rejected = Number(record.rejected ?? 0);
  const stops = Number(record.stops ?? 0);
  const starts = Number(record.starts ?? 0);

  const note = starts
    ? ' A START was seen from this number too, and that re-subscribes them to ' +
      'one sender only, so the rejections are from a different sender in the pool.'
    : '';

  if (!rejected) {
    if (stops) {
      return ['suppressed',
        `texted an opt-out keyword ${stops} time(s) and nothing has been sent ` +
        `to them since.${note}`];
    }
    return ['clean', `no 21610 rejections and no opt-out keywords.${note}`];
  }

  if (rejected >= loopThreshold) {
    return ['retry-loop',
      `${rejected} sends rejected with 21610: something is retrying an opt-out ` +
      'on a loop. Twilio rejects each one at request time so none are billed, ' +
      `but each is a record of contacting someone who asked you to stop.${note}`];
  }

  if (stops) {
    return ['ignored-opt-out',
      `texted an opt-out keyword ${stops} time(s), then ${rejected} send(s) ` +
      'went out and were rejected with 21610: the opt-out reached Twilio and ' +
      `never reached your database.${note}`];
  }

  return ['invisible-opt-out',
    `${rejected} send(s) rejected with 21610 and no opt-out keyword in this ` +
    'window: it happened before the window or on another sender. There is no ' +
    'read API for the opt-out list, so these rejections are the only evidence ' +
    `you will get.${note}`];
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
  let params = { PageSize: 1000, 'DateSent>=': since };
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

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 30) || 30;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages since ${since}`);
    return;
  }

  const people = tally(messages);
  let bad = 0;
  for (const [number, record] of [...people.entries()].sort()) {
    const [state, detail] = verdict(record);
    const line = `${state.padEnd(18)} ${number}  ${detail}`;
    if (state === 'clean' || state === 'suppressed') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (record.sids.length) console.warn(`  message sids: ${record.sids.join(', ')}`);
    console.warn(`  repair: mark ${number} unsubscribed in your own database. ` +
                 'Twilio exposes no read API for the opt-out list and only the ' +
                 'recipient texting START, UNSTOP or YES re-subscribes them. ' +
                 'Enable Advanced Opt-Out on the Messaging Service so the ' +
                 'keywords are identical across every sender.');
  }

  console.log(`${people.size} recipient(s) over ${days} day(s), ${bad} still ` +
              'being messaged after STOP');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The keyword rule is the one to pin: <code>stop</code> in lower case is an opt-out and <code>STOP please</code> is not, because that is where a well-meaning substring match starts suppressing customers who never asked to leave. After that, the join &mdash; an inbound STOP is keyed on <code>from</code> and the rejected sends on <code>to</code>, and the finding only exists when both land on the same person.",
"test_py_file": "test_twilio_opt_out_audit.py",
"test_py": '''from twilio_opt_out_audit import keyword_kind, tally, verdict

CONSUMER = "+15557654321"


def inbound(body):
    return {"sid": "SMin", "direction": "inbound", "from": CONSUMER,
            "to": "+15550001111", "body": body}


def rejected(sid):
    return {"sid": sid, "direction": "outbound-api", "from": "+15550001111",
            "to": CONSUMER, "status": "failed", "error_code": 21610}


def test_keyword_matching_follows_twilios_whole_body_rule():
    assert keyword_kind("STOP") == "out"
    assert keyword_kind("  stop  ") == "out"
    assert keyword_kind("Unsubscribe") == "out"
    assert keyword_kind("START") == "in"
    # The line that keeps complainers out of the suppression list.
    assert keyword_kind("STOP please") == ""
    assert keyword_kind("please stop sending these at 6am") == ""
    assert keyword_kind(None) == ""


def test_the_join_puts_the_inbound_stop_and_the_rejections_on_one_person():
    rows = tally([inbound("STOP"), rejected("SM1"), rejected("SM2")])
    assert set(rows) == {CONSUMER}
    assert rows[CONSUMER]["stops"] == 1
    assert rows[CONSUMER]["rejected"] == 2
    assert rows[CONSUMER]["sids"] == ["SM1", "SM2"]


def test_stop_seen_and_sends_afterwards_is_the_finding():
    state, detail = verdict({"rejected": 2, "stops": 1})
    assert state == "ignored-opt-out"
    assert "never reached your database" in detail


def test_rejections_with_no_stop_in_the_window_are_still_actionable():
    state, detail = verdict({"rejected": 3, "stops": 0})
    assert state == "invisible-opt-out"
    assert "no read API" in detail


def test_a_retry_loop_outranks_everything_else():
    state, detail = verdict({"rejected": 40, "stops": 1})
    assert state == "retry-loop"
    assert "not billed" not in detail
    assert "none are billed" in detail


def test_a_start_is_reported_as_a_different_sender_not_a_mistake():
    state, detail = verdict({"rejected": 1, "stops": 1, "starts": 1})
    assert state == "ignored-opt-out"
    assert "different sender" in detail


def test_stop_with_no_sends_afterwards_is_correct_behaviour():
    state, detail = verdict({"rejected": 0, "stops": 1})
    assert state == "suppressed"
    assert verdict({"rejected": 0, "stops": 0})[0] == "clean"
    assert "nothing has been sent" in detail
''',
"test_js_file": "twilio-opt-out-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keywordKind, tally, verdict } from './twilio-opt-out-audit.mjs';

const CONSUMER = '+15557654321';
const inbound = (body) => ({ sid: 'SMin', direction: 'inbound', from: CONSUMER,
                             to: '+15550001111', body });
const rejected = (sid) => ({ sid, direction: 'outbound-api', from: '+15550001111',
                             to: CONSUMER, status: 'failed', error_code: 21610 });

test('keyword matching follows twilio whole body rule', () => {
  assert.equal(keywordKind('STOP'), 'out');
  assert.equal(keywordKind('  stop  '), 'out');
  assert.equal(keywordKind('Unsubscribe'), 'out');
  assert.equal(keywordKind('START'), 'in');
  assert.equal(keywordKind('STOP please'), '');
  assert.equal(keywordKind('please stop sending these at 6am'), '');
  assert.equal(keywordKind(null), '');
});

test('the join puts the inbound stop and the rejections on one person', () => {
  const rows = tally([inbound('STOP'), rejected('SM1'), rejected('SM2')]);
  assert.deepEqual([...rows.keys()], [CONSUMER]);
  assert.equal(rows.get(CONSUMER).stops, 1);
  assert.equal(rows.get(CONSUMER).rejected, 2);
  assert.deepEqual(rows.get(CONSUMER).sids, ['SM1', 'SM2']);
});

test('stop seen and sends afterwards is the finding', () => {
  const [state, detail] = verdict({ rejected: 2, stops: 1 });
  assert.equal(state, 'ignored-opt-out');
  assert.match(detail, /never reached your database/);
});

test('rejections with no stop in the window are still actionable', () => {
  const [state, detail] = verdict({ rejected: 3, stops: 0 });
  assert.equal(state, 'invisible-opt-out');
  assert.match(detail, /no read API/);
});

test('a retry loop outranks everything else', () => {
  const [state, detail] = verdict({ rejected: 40, stops: 1 });
  assert.equal(state, 'retry-loop');
  assert.match(detail, /none are billed/);
});

test('a start is reported as a different sender, not a mistake', () => {
  const [state, detail] = verdict({ rejected: 1, stops: 1, starts: 1 });
  assert.equal(state, 'ignored-opt-out');
  assert.match(detail, /different sender/);
});

test('stop with no sends afterwards is correct behaviour', () => {
  const [state, detail] = verdict({ rejected: 0, stops: 1 });
  assert.equal(state, 'suppressed');
  assert.match(detail, /nothing has been sent/);
  assert.equal(verdict({ rejected: 0, stops: 0 })[0], 'clean');
});
''',
"faq": [
 ("Can I download the list of numbers that have opted out?",
  "No. Twilio enforces the opt-out but publishes no read API for it, on the number, the Messaging Service or the account. Rebuilding the list from 21610 rejections and inbound keywords is the only route a read-only credential has, which is also why the list has to be stored on your side once you have it."),
 ("Does a 21610 cost me anything?",
  "Not in money. The send is rejected at request time and no segment is billed. The cost is the record: each rejection is a logged attempt to contact someone who asked you to stop, and volume makes that look deliberate rather than accidental."),
 ("Why does the script ignore a message that reads STOP please?",
  "Because Twilio does. The keyword match is against the whole body after trimming, case-insensitively. Matching substrings would add every annoyed customer to your suppression list, silencing people who never opted out and hiding the real ones in the noise."),
 ("Someone opted out of one number but not another. Is that a bug?",
  "No, that is how it works. Opt-out is scoped to the sender, so a recipient blocked on one long code stays reachable on the others in the pool. Advanced Opt-Out on the Messaging Service is what makes the behaviour consistent, and treating the contact as globally unsubscribed in your own database is what makes it right."),
 ("How do I put someone back on the list after they opted out?",
  "You cannot, and neither can Twilio Support. Only the recipient texting START, UNSTOP or YES to that sender clears the block. Any flow that promises a customer they will start receiving messages again after they call you is a flow that will not work."),
],
"related": [
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering drops your SMS silently"),
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS disappears into a blank sms_url"),
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never reach a final state"),
],
"citations": [CITE_21610, CITE_OPTOUT, CITE_MSG, CITE_ALERTS],
},

{
"slug": "landline-destination-30006",
"title": "SMS to a landline fails with 30006 and retrying never helps",
"description": "Error 30006 and 21614 mean the destination cannot receive SMS at all. The retry loop bills you forever; Lookup line type is what settles the argument.",
"h1": "SMS to a landline fails with 30006 and retrying never helps",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30006", "twilio landline sms",
             "twilio 21614 not a valid mobile number",
             "line type intelligence lookup", "sms to landline fails"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The same twelve numbers fail every night. <code>error_code</code> <code>30006</code>, <code>status</code> <code>undelivered</code>, and a retry scheduled by a queue that assumes failures are temporary. They are not. Those numbers are desk phones, and no amount of retrying will make a desk phone receive an SMS &mdash; but you are billed for each attempt, and the customer is on your list as unreachable rather than as unreachable-by-this-channel.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and collect the distinct <code>to</code> values on rows with <code>error_code</code> <code>30006</code> (undelivered, after billing) or <code>21614</code> (rejected at request time, not billed).</p>
<p>Then confirm each one with <code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence</code> and read <code>line_type_intelligence.type</code>. <code>landline</code> or <code>fixedVoip</code> means permanently undeliverable. <code>mobile</code> means the line is fine and your <em>sender</em> cannot reach it, which is a completely different repair.</p>""",
"problem": """<p>A permanent failure that looks temporary is worse than a loud one, because the system built around it keeps working. The message goes out, comes back undelivered, and lands in the retry queue with the connection timeouts and the carrier hiccups. Tomorrow it goes out again. There is no counter anywhere that says "this address has failed thirty nights running", so nothing ever escalates it to a human.</p>
<p>The two error codes also arrive from opposite ends of the pipeline, which splits the evidence. <code>21614</code> is a request-time rejection: the number was never sent to, never billed, and the failure is visible immediately. <code>30006</code> comes back after the segment is priced and the message has been handed to a carrier. Read only one of them and you either miss the paid failures or miss the rejected ones.</p>""",
"why": """<p><strong>Landlines are indistinguishable from mobiles in an E.164 string.</strong> Nothing in <code>+15551234567</code> says whether it rings on a desk or in a pocket. In North America the number ranges have been portable for two decades, so area codes and prefixes tell you nothing either. Only a carrier lookup knows, and only if you ask.</p>
<p><strong>Contact forms collect whatever the customer types.</strong> Someone gives you their office line because it is the number they know by heart. The signup succeeds, the record is valid, and the failure surfaces weeks later in a channel nobody watches.</p>
<p><strong>30006 is not exclusively about landlines.</strong> The same code comes back when the sending route cannot reach the destination carrier at all &mdash; classically a short code with no long-code fallback in the pool. Same code, mobile handset, and dropping the contact would be the wrong fix, which is precisely why the line type is worth the lookup.</p>
<p><strong>Retries are the default and they are free to schedule.</strong> Message queues retry failed sends because most failures are transient. Nothing in the message resource marks 30006 as permanent, so the queue has no way to know it should stop, and each cycle bills you again for a message that physically cannot arrive.</p>""",
"steps": [
 {"h": "Page the Messages list and keep the two codes",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. There is no <code>ErrorCode</code> filter, so read <code>error_code</code> yourself and keep <code>30006</code> and <code>21614</code>. Count them separately: one was billed and the other was not.</p>"""},
 {"h": "Group by destination and count the nights",
  "body": """<p>One failure could be anything. The same <code>to</code> failing on several distinct days is the shape of a permanent problem, and it is also the shape a retry queue makes when it never gives up. Keep a couple of Message SIDs per number so the finding can be checked by hand.</p>"""},
 {"h": "Confirm the line type with Lookup",
  "body": """<p><code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence</code>. It is a GET, so it stays inside a read-only credential, but Line Type Intelligence is billed per lookup &mdash; put it behind a flag and a cap rather than running it over every number in the window.</p>"""},
 {"h": "Split landline from unreachable",
  "body": """<p><code>landline</code> and <code>fixedVoip</code> are permanent: that contact will never receive SMS. <code>mobile</code> with repeated 30006 is the opposite finding &mdash; the handset is fine and your sender cannot reach the carrier, which usually means a short code with no long-code fallback in the sender pool.</p>"""},
 {"h": "Gate at capture time, not at send time",
  "body": """<p>Run the same Lookup when the number is first collected and route landline contacts to voice or email instead. Suppress the confirmed landlines you already have, and if the failures are on a short code, widen the Messaging Service sender pool. Re-run the audit after a month; new bad numbers arrive with new customers.</p>"""},
],
"verify": """<p>Re-run over the same window once the suppression list is live. Confirmed landlines should stop appearing because nothing is being sent to them.</p>
<pre><code class="language-bash">python3 twilio_landline_audit.py --days 30 --confirm-with-lookup
# 8 destination(s) over 30 day(s), 0 still being retried</code></pre>""",
"code_intro": "One paginated GET over the Messages list, plus at most one Lookup per flagged number when you ask for it &mdash; both GETs, both inside an API Key with read access. The verdict is pure and takes the line type as an argument rather than fetching it, so the interesting decision (landline versus a sender that cannot reach the carrier) is testable without spending anything.",
"py_file": "twilio_landline_audit.py",
"py": '''"""Report SMS destinations that can never receive a message: 30006 and 21614.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_landline_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
LOOKUPS = "https://lookups.twilio.com/v2/PhoneNumbers"

UNDELIVERABLE = 30006   # undelivered, after the segment was billed
NOT_MOBILE = 21614      # rejected at request time, never billed

NO_SMS = ("landline", "fixedvoip")


def error_code(message):
    """Read error_code as an integer, or None. It is null on healthy messages
    and a number on failed ones; a string comparison finds nothing."""
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def tally(messages):
    """Group failures by destination, keeping the two codes apart.

    Pure, so the counting can be tested without a network. 30006 was billed and
    21614 was not, and a report that adds them together loses the only number
    anyone will ask you for.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        code = error_code(m)
        if code not in (UNDELIVERABLE, NOT_MOBILE):
            continue
        row = out.setdefault(str(m.get("to") or "unknown"),
                             {"attempts": 0, "undelivered": 0, "rejected": 0,
                              "sids": []})
        row["attempts"] += 1
        if code == UNDELIVERABLE:
            row["undelivered"] += 1
        else:
            row["rejected"] += 1
        if len(row["sids"]) < 3:
            row["sids"].append(m.get("sid"))
    return out


def describe(record):
    """Say which of the two failures this destination produced, and at what
    cost. Pure."""
    parts = []
    if record.get("undelivered"):
        parts.append("%d undelivered with 30006 and billed"
                     % record["undelivered"])
    if record.get("rejected"):
        parts.append("%d rejected at request time with 21614 and not billed"
                     % record["rejected"])
    return " and ".join(parts) if parts else "no refused attempts"


def verdict(record, line_type=None):
    """Classify one destination. `line_type` is line_type_intelligence.type from
    Lookup when it was fetched, and None when it was not.

    Pure, so the distinction that matters here can be tested without spending a
    lookup. Returns (state, detail).
    """
    failed = int(record.get("undelivered") or 0) + int(record.get("rejected") or 0)
    if not failed:
        return ("clean", "%d attempt(s), none refused" % (record.get("attempts") or 0))

    told = describe(record)
    kind = str(line_type or "").strip()

    if kind.lower() in NO_SMS:
        return ("landline",
                "Lookup says %s, which cannot receive SMS at any price: %s. "
                "Retrying never helps." % (kind, told))

    if kind.lower() == "mobile":
        return ("sender-cannot-reach",
                "Lookup says mobile, so this is not a landline: %s. The handset "
                "is fine and the sending route cannot reach that carrier, which "
                "is what a short code with no long code fallback looks like."
                % told)

    if kind and kind.lower() != "unknown":
        return ("not-sms-capable",
                "Lookup says %s, which is not an SMS capable line: %s."
                % (kind, told))

    if failed == 1:
        return ("one-off",
                "a single failure and no line type: %s. Confirm with Lookup "
                "before dropping the contact." % told)

    return ("undeliverable",
            "%d refused attempt(s) with no line type: %s. Treat it as permanent "
            "and confirm with Lookup Line Type Intelligence." % (failed, told))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. No ErrorCode filter exists on this resource, so the
    window and the cap are the only bounds available."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def line_type(session, e164):
    """One billed Lookup. A 404 means the number is not valid at all, which is
    an answer rather than an error."""
    r = session.get("%s/%s" % (LOOKUPS, e164),
                    params={"Fields": "line_type_intelligence"}, timeout=30)
    if r.status_code == 404:
        return "invalid"
    if r.status_code in (401, 403):
        raise SystemExit("%d from Lookups: the API key needs read access to "
                         "Lookup as well" % r.status_code)
    r.raise_for_status()
    body = r.json()
    if body.get("valid") is False:
        return "invalid"
    return (body.get("line_type_intelligence") or {}).get("type")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--confirm-with-lookup", action="store_true",
                    help="one billed Lookup per flagged destination")
    ap.add_argument("--max-lookups", type=int, default=50,
                    help="hard cap on billed lookups per run")
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

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = list_messages(session, account, since, args.max_messages)
    destinations = tally(messages)
    if not destinations:
        log.info("no 30006 or 21614 failures since %s", since)
        return 0

    spent = 0
    bad = 0
    for number, record in sorted(destinations.items()):
        kind = None
        if args.confirm_with_lookup and spent < args.max_lookups:
            kind = line_type(session, number)
            spent += 1
        state, detail = verdict(record, kind)
        line = "%-20s %s  %s" % (state, number, detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in record["sids"]))
        if state == "sender-cannot-reach":
            log.warning("  repair: add a long code sender to the Messaging "
                        "Service pool with POST %s/Services/{ServiceSid}"
                        "/PhoneNumbers PhoneNumberSid=PN...",
                        "https://messaging.twilio.com/v1")
        else:
            log.warning("  repair: suppress %s in your own database and gate new "
                        "numbers at capture time with GET %s/{E164}"
                        "?Fields=line_type_intelligence", number, LOOKUPS)

    log.info("%d destination(s) over %d day(s), %d still being retried",
             len(destinations), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-landline-audit.mjs",
"js": '''/**
 * Report SMS destinations that can never receive a message: 30006 and 21614.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const LOOKUPS = 'https://lookups.twilio.com/v2/PhoneNumbers';
const MSG = 'https://messaging.twilio.com/v1';

const UNDELIVERABLE = 30006;  // undelivered, after the segment was billed
const NOT_MOBILE = 21614;     // rejected at request time, never billed

const NO_SMS = ['landline', 'fixedvoip'];

/** Read error_code as a number, or null. A string comparison finds nothing. */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Group failures by destination, keeping the two codes apart: 30006 was billed
 * and 21614 was not. Pure, so the counting can be tested without a network.
 */
export function tally(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const code = errorCode(m);
    if (code !== UNDELIVERABLE && code !== NOT_MOBILE) continue;
    const k = String(m.to ?? 'unknown');
    if (!out.has(k)) out.set(k, { attempts: 0, undelivered: 0, rejected: 0, sids: [] });
    const row = out.get(k);
    row.attempts += 1;
    if (code === UNDELIVERABLE) row.undelivered += 1; else row.rejected += 1;
    if (row.sids.length < 3) row.sids.push(m.sid);
  }
  return out;
}

/** Say which failures this destination produced, and at what cost. Pure. */
export function describe(record) {
  const parts = [];
  if (record.undelivered) {
    parts.push(`${record.undelivered} undelivered with 30006 and billed`);
  }
  if (record.rejected) {
    parts.push(`${record.rejected} rejected at request time with 21614 and not billed`);
  }
  return parts.length ? parts.join(' and ') : 'no refused attempts';
}

/**
 * Classify one destination. `lineType` is line_type_intelligence.type from
 * Lookup when it was fetched, and null when it was not. Pure, so the
 * distinction that matters can be tested without spending a lookup.
 * Returns [state, detail].
 */
export function verdict(record, lineType = null) {
  const failed = Number(record.undelivered ?? 0) + Number(record.rejected ?? 0);
  if (!failed) return ['clean', `${record.attempts ?? 0} attempt(s), none refused`];

  const told = describe(record);
  const kind = String(lineType ?? '').trim();

  if (NO_SMS.includes(kind.toLowerCase())) {
    return ['landline',
      `Lookup says ${kind}, which cannot receive SMS at any price: ${told}. ` +
      'Retrying never helps.'];
  }

  if (kind.toLowerCase() === 'mobile') {
    return ['sender-cannot-reach',
      `Lookup says mobile, so this is not a landline: ${told}. The handset is ` +
      'fine and the sending route cannot reach that carrier, which is what a ' +
      'short code with no long code fallback looks like.'];
  }

  if (kind && kind.toLowerCase() !== 'unknown') {
    return ['not-sms-capable',
      `Lookup says ${kind}, which is not an SMS capable line: ${told}.`];
  }

  if (failed === 1) {
    return ['one-off',
      `a single failure and no line type: ${told}. Confirm with Lookup before ` +
      'dropping the contact.'];
  }

  return ['undeliverable',
    `${failed} refused attempt(s) with no line type: ${told}. Treat it as ` +
    'permanent and confirm with Lookup Line Type Intelligence.'];
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
  let params = { PageSize: 1000, 'DateSent>=': since };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.messages ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function lineType(auth, e164) {
  const u = new URL(`${LOOKUPS}/${e164}`);
  u.searchParams.set('Fields', 'line_type_intelligence');
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 404) return 'invalid';
  if (!res.ok) throw new Error(`${res.status} from Lookups for ${e164}`);
  const body = await res.json();
  if (body.valid === false) return 'invalid';
  return body.line_type_intelligence?.type ?? null;
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

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 30) || 30;
  const confirm = process.argv.includes('--confirm-with-lookup');
  const maxLookups = 50;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const destinations = tally(await listMessages(auth, account, since));
  if (destinations.size === 0) {
    console.log(`no 30006 or 21614 failures since ${since}`);
    return;
  }

  let spent = 0;
  let bad = 0;
  for (const [number, record] of [...destinations.entries()].sort()) {
    let kind = null;
    if (confirm && spent < maxLookups) { kind = await lineType(auth, number); spent += 1; }
    const [state, detail] = verdict(record, kind);
    const line = `${state.padEnd(20)} ${number}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  message sids: ${record.sids.join(', ')}`);
    if (state === 'sender-cannot-reach') {
      console.warn('  repair: add a long code sender to the Messaging Service ' +
                   `pool with POST ${MSG}/Services/{ServiceSid}/PhoneNumbers ` +
                   'PhoneNumberSid=PN...');
    } else {
      console.warn(`  repair: suppress ${number} in your own database and gate ` +
                   `new numbers at capture time with GET ${LOOKUPS}/{E164}` +
                   '?Fields=line_type_intelligence');
    }
  }

  console.log(`${destinations.size} destination(s) over ${days} day(s), ${bad} ` +
              'still being retried');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that earns the lookup is the mobile one: a handset that keeps returning 30006 is not a landline, and dropping that contact would be exactly the wrong repair. The rest of the tests hold the two codes apart, because the first question anyone asks about this report is how much of it was billed.",
"test_py_file": "test_twilio_landline_audit.py",
"test_py": '''from twilio_landline_audit import describe, tally, verdict

DESK = "+15551230000"


def failure(sid, code, to=DESK):
    return {"sid": sid, "direction": "outbound-api", "to": to,
            "status": "undelivered", "error_code": code}


def test_the_two_codes_are_counted_separately():
    rows = tally([failure("SM1", 30006), failure("SM2", 21614),
                  failure("SM3", 30006), failure("SM4", 30007)])
    assert rows[DESK]["undelivered"] == 2
    assert rows[DESK]["rejected"] == 1
    assert rows[DESK]["attempts"] == 3   # 30007 belongs to a different report


def test_describe_says_which_half_was_billed():
    told = describe({"undelivered": 2, "rejected": 1})
    assert "billed" in told
    assert "not billed" in told


def test_lookup_landline_is_permanent():
    state, detail = verdict({"undelivered": 4}, "landline")
    assert state == "landline"
    assert "Retrying never helps" in detail


def test_fixed_voip_is_treated_like_a_landline():
    assert verdict({"undelivered": 2}, "fixedVoip")[0] == "landline"


def test_a_mobile_that_keeps_failing_is_the_senders_problem():
    state, detail = verdict({"undelivered": 6}, "mobile")
    assert state == "sender-cannot-reach"
    assert "short code" in detail


def test_no_lookup_and_one_failure_is_not_yet_a_verdict():
    state, detail = verdict({"rejected": 1})
    assert state == "one-off"
    assert "Confirm with Lookup" in detail


def test_no_lookup_and_repeated_failures_is_treated_as_permanent():
    state, detail = verdict({"undelivered": 5})
    assert state == "undeliverable"
    assert "5 refused" in detail


def test_an_unknown_line_type_does_not_pretend_to_know():
    assert verdict({"undelivered": 5}, "unknown")[0] == "undeliverable"
    assert verdict({"undelivered": 5}, "invalid")[0] == "not-sms-capable"
    assert verdict({"attempts": 3})[0] == "clean"
''',
"test_js_file": "twilio-landline-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { describe as told, tally, verdict } from './twilio-landline-audit.mjs';

const DESK = '+15551230000';
const failure = (sid, code, to = DESK) => ({
  sid, direction: 'outbound-api', to, status: 'undelivered', error_code: code,
});

test('the two codes are counted separately', () => {
  const rows = tally([failure('SM1', 30006), failure('SM2', 21614),
                      failure('SM3', 30006), failure('SM4', 30007)]);
  const row = rows.get(DESK);
  assert.equal(row.undelivered, 2);
  assert.equal(row.rejected, 1);
  assert.equal(row.attempts, 3);  // 30007 belongs to a different report
});

test('describe says which half was billed', () => {
  const line = told({ undelivered: 2, rejected: 1 });
  assert.match(line, /and billed/);
  assert.match(line, /not billed/);
});

test('lookup landline is permanent', () => {
  const [state, detail] = verdict({ undelivered: 4 }, 'landline');
  assert.equal(state, 'landline');
  assert.match(detail, /Retrying never helps/);
});

test('fixed voip is treated like a landline', () => {
  assert.equal(verdict({ undelivered: 2 }, 'fixedVoip')[0], 'landline');
});

test('a mobile that keeps failing is the sender problem', () => {
  const [state, detail] = verdict({ undelivered: 6 }, 'mobile');
  assert.equal(state, 'sender-cannot-reach');
  assert.match(detail, /short code/);
});

test('no lookup and one failure is not yet a verdict', () => {
  const [state, detail] = verdict({ rejected: 1 });
  assert.equal(state, 'one-off');
  assert.match(detail, /Confirm with Lookup/);
});

test('no lookup and repeated failures is treated as permanent', () => {
  const [state, detail] = verdict({ undelivered: 5 });
  assert.equal(state, 'undeliverable');
  assert.match(detail, /5 refused/);
});

test('an unknown line type does not pretend to know', () => {
  assert.equal(verdict({ undelivered: 5 }, 'unknown')[0], 'undeliverable');
  assert.equal(verdict({ undelivered: 5 }, 'invalid')[0], 'not-sms-capable');
  assert.equal(verdict({ attempts: 3 })[0], 'clean');
});
''',
"faq": [
 ("What is the difference between 30006 and 21614?",
  "21614 is a request-time rejection: Twilio decides the To number is not a valid mobile number, nothing is sent and nothing is billed. 30006 comes back later, after the message was accepted, priced and handed onward, and the carrier reported that the destination is a landline or unreachable. Same underlying fact, opposite ends of the pipeline."),
 ("Does a Lookup cost money if the script is read-only?",
  "Read-only and free are different things. Line Type Intelligence is a GET, so it fits inside an API Key with read access, but it is a billed lookup per number. That is why it sits behind a flag and a hard cap: the Messages read is free and the confirmation is not."),
 ("Can I tell a landline from a mobile without paying for a lookup?",
  "Not reliably. Number ranges have been portable in North America for twenty years, so prefixes tell you nothing about the device. The failure history is the free signal, and it is a good one: the same destination refusing on several distinct days is close to proof even before the lookup confirms it."),
 ("The line type came back mobile but the messages keep failing. Now what?",
  "Then the destination is not the problem and the sender is. A short code that cannot reach that carrier returns 30006 exactly like a landline does. Add a long-code fallback sender to the Messaging Service pool so those messages have another route, and stop suppressing the contact."),
 ("Should the script delete the bad numbers for me?",
  "No, and nothing here writes. Suppression belongs in your own database where you can see who did it and when, and a script holding a messaging credential should not be the thing that edits your customer list at 3am."),
],
"related": [
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering drops your SMS silently"),
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never reach a final state"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_30006, CITE_21614, CITE_LOOKUP, CITE_MSG],
},

{
"slug": "messages-stuck-queued-or-accepted",
"title": "Messages stay queued or accepted and never reach a final state",
"description": "Status sits at queued or accepted for hours with no error_code. Part of it is throughput starvation, part is a scheduled send, and sent is not a failure.",
"h1": "messages stay queued or accepted and never reach a final state",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio message stuck queued", "twilio status accepted",
             "twilio message not delivered no error", "twilio message scheduled",
             "twilio sent vs delivered"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The send succeeded four hours ago. <code>status</code> is still <code>queued</code>. <code>error_code</code> is <code>null</code>, <code>date_sent</code> is <code>null</code>, and the status callback has never fired because nothing has happened to report. Nobody has been paged, because nothing has failed yet &mdash; and in six hours these will start failing with <code>30001</code> or expiring with <code>30036</code>, long after the passcode they carry stopped being useful.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and flag rows whose <code>status</code> is <code>queued</code>, <code>accepted</code> or <code>sending</code> while <code>date_created</code> is more than an hour old. That is throughput starvation: the sender's queue is not draining.</p>
<p>Two states next to it are <em>not</em> the same finding. <code>scheduled</code> is a message waiting for a send window you asked for. And <code>sent</code> is terminal on carriers that return no delivery receipt, so treating every non-<code>delivered</code> message as a failure invents an outage that is not there.</p>""",
"problem": """<p>Every alert anyone writes fires on an error. This has none. The message resource is healthy in every field a monitor looks at: no <code>error_code</code>, no failed status, no webhook to fail. It is simply not moving, and there is no event for not moving.</p>
<p>By the time it does produce an error, the useful window has closed. A one-time passcode queued behind eleven thousand marketing segments on the same long code arrives after the login page has timed out, or does not arrive at all when the validity period runs out. The user has already asked for another code, which goes into the same queue behind the first one, which is how a slow queue becomes a stopped one.</p>""",
"why": """<p><strong>Throughput belongs to the sender, not to the account.</strong> A US long code moves about one message segment per second. Handing it a bulk job puts every later message behind that job, and Twilio holds roughly ten hours of segments per sender before overflowing. Nothing rejects the send at the door; the queue accepts everything and then meters it out.</p>
<p><strong>Not moving is not an error.</strong> Twilio has nothing to report while a message waits, so no status callback fires and no alert exists. The only way to see it is to read <code>date_created</code> against the clock, which means someone has to have decided what "too old" means for your traffic.</p>
<p><strong>Two adjacent states look identical from a dashboard.</strong> A <code>scheduled</code> message is waiting on purpose &mdash; up to 35 days out &mdash; and fires no callbacks while it waits. A <code>sent</code> message on a carrier with no delivery receipts is finished and successful. Both are non-final in a naive query, and counting either as stuck produces a report nobody trusts twice.</p>
<p><strong>There is no status filter to ask with.</strong> The Messages list takes <code>To</code>, <code>From</code>, <code>DateSent</code> and paging, and nothing else. You cannot ask for the queued ones; you page the window and compare timestamps yourself, which is why almost nobody notices until the failures start.</p>""",
"steps": [
 {"h": "Page a short window, not a long one",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. Two days is usually right: anything older is already resolved one way or another, and a wider window mostly costs you paging time.</p>"""},
 {"h": "Age each non-final message against the clock",
  "body": """<p>Read <code>date_created</code>, which the 2010-04-01 API returns as an RFC 2822 string like <code>Mon, 12 Aug 2024 10:15:03 +0000</code>. Anything <code>queued</code>, <code>accepted</code> or <code>sending</code> older than about an hour is not in flight any more, it is starved. Make the threshold an argument; an OTP flow and a nightly batch do not deserve the same number.</p>"""},
 {"h": "Separate the scheduled ones",
  "body": """<p><code>scheduled</code> means you booked it, anywhere from 15 minutes to 35 days ahead, and no status callback fires while it waits. Those belong in their own bucket. A scheduled message whose send time has already passed and whose status has not moved is a real finding; one that is simply waiting is not.</p>"""},
 {"h": "Do not count sent as a failure",
  "body": """<p>On carriers that return no delivery receipt, <code>sent</code> is the last status a message will ever have. It never becomes <code>delivered</code> and nothing is wrong. Report it as its own state so the delivery rate you quote is not quietly wrong for entire countries.</p>"""},
 {"h": "Widen the sender pool, then raise the validity period",
  "body": """<p>The repair for starvation is more senders, not more retries: send through a Messaging Service and add numbers to the pool so the segments have somewhere to go. Raise <code>ValidityPeriod</code> to <code>36000</code> so throttled messages are not thrown away before their turn, and cancel scheduled sends you no longer want with <code>POST /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}.json</code> and <code>Status=canceled</code>.</p>"""},
],
"verify": """<p>Re-run after the pool is widened. The queued and accepted counts should drain within the threshold, and the only non-final states left should be scheduled and sent.</p>
<pre><code class="language-bash">python3 twilio_stuck_messages_audit.py --days 2 --stuck-after 60
# 4210 message(s) over 2 day(s), 0 not moving</code></pre>""",
"code_intro": "One paginated GET, read with an API Key that has read access. The two pure functions are the date parser and the verdict, and they are pure for the same reason: this whole note is about telling four non-final states apart, and a rule that decides what counts as stuck should be testable at a fixed clock rather than at whatever time the test happens to run.",
"py_file": "twilio_stuck_messages_audit.py",
"py": '''"""Report Twilio messages that are not moving, and the ones that only look stuck.

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
from email.utils import parsedate_to_datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_stuck_messages_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"

FINAL = ("delivered", "undelivered", "failed", "canceled", "read", "received")
WAITING = ("queued", "accepted", "sending")
NOT_MOVING = ("stuck", "scheduled-overdue", "unknown-age", "unknown-status")


def age_minutes(date_str, now):
    """Minutes between `date_str` and `now`; negative when it is in the future.

    The 2010-04-01 API returns RFC 2822 dates ("Mon, 12 Aug 2024 10:15:03
    +0000"), not ISO 8601, so the obvious parser is the wrong one. Returns None
    for a missing or unreadable value rather than guessing, because guessing
    here means reporting a message as stuck on the strength of a parse failure.
    """
    raw = str(date_str or "").strip()
    if not raw:
        return None
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    return (now - when).total_seconds() / 60.0


def verdict(message, now, stuck_after=60):
    """Classify one message against a clock you pass in.

    Pure, so the four non-final states can be told apart in a test at a fixed
    time instead of at whatever moment the suite happens to run.

    Returns (state, detail).
    """
    status = str(message.get("status") or "").lower()

    if status in FINAL:
        return ("final", "status %s" % (status or "unset"))

    if status == "scheduled":
        due = age_minutes(message.get("send_at"), now)
        if due is None:
            return ("scheduled",
                    "waiting for a send window. The list response does not "
                    "always carry send_at, so age these against your own record "
                    "of when they were booked.")
        if due < 0:
            return ("scheduled",
                    "waiting: due in %d minute(s). No status callback fires "
                    "while a message is scheduled." % round(-due))
        return ("scheduled-overdue",
                "its send_at passed %d minute(s) ago and the status has not "
                "moved." % round(due))

    age = age_minutes(message.get("date_created"), now)

    if status == "sent":
        if age is not None and age >= stuck_after:
            return ("sent-no-dlr",
                    "sent %d minute(s) ago with no delivery receipt. On carriers "
                    "that return no receipt, sent is the terminal state: count "
                    "it as success rather than as a failure." % round(age))
        return ("in-flight", "sent, waiting for a delivery receipt.")

    if status in WAITING:
        if age is None:
            return ("unknown-age",
                    "status %s but date_created could not be read, so it cannot "
                    "be aged." % status)
        if age >= stuck_after:
            return ("stuck",
                    "%s for %d minute(s) with no error_code. The sender's queue "
                    "is not draining; Twilio holds about ten hours of segments "
                    "per sender, then these fail with 30001 or expire with "
                    "30036." % (status, round(age)))
        return ("in-flight", "%s for %d minute(s), still inside the window."
                % (status, round(age)))

    return ("unknown-status",
            "status %s is not one this script knows how to age." % (status or "unset"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. There is no Status filter on this resource, so a
    short window and a hard cap are the only bounds available."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=2,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--stuck-after", type=int, default=60,
                    help="minutes in a waiting status before it counts as stuck")
    ap.add_argument("--show", type=int, default=20,
                    help="how many individual messages to print")
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

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages since %s", since)
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    counts, shown, bad = {}, 0, 0
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        state, detail = verdict(m, now, args.stuck_after)
        counts[state] = counts.get(state, 0) + 1
        if state not in NOT_MOVING:
            continue
        bad += 1
        if shown >= args.show:
            continue
        shown += 1
        log.warning("%-17s %s  %s", state, m.get("sid"), detail)
        if state == "scheduled-overdue":
            log.warning("  repair: cancel it with POST %s/Accounts/%s/Messages/"
                        "%s.json Status=canceled", BASE, account, m.get("sid"))
        elif state == "stuck":
            log.warning("  repair: send through a Messaging Service with more "
                        "senders in the pool, and raise the validity period with "
                        "POST %s/Services/{ServiceSid} ValidityPeriod=36000", MSG)

    log.info("states: %s",
             ", ".join("%s %d" % kv for kv in sorted(counts.items())))
    log.info("%d message(s) over %d day(s), %d not moving",
             len(messages), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-stuck-messages-audit.mjs",
"js": '''/**
 * Report Twilio messages that are not moving, and the ones that only look stuck.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';

const FINAL = ['delivered', 'undelivered', 'failed', 'canceled', 'read', 'received'];
const WAITING = ['queued', 'accepted', 'sending'];
const NOT_MOVING = ['stuck', 'scheduled-overdue', 'unknown-age', 'unknown-status'];

/**
 * Minutes between `dateStr` and `now`; negative when it is in the future. The
 * 2010-04-01 API returns RFC 2822 dates, not ISO 8601. Returns null for a
 * missing or unreadable value rather than guessing, because guessing means
 * calling a message stuck on the strength of a parse failure.
 */
export function ageMinutes(dateStr, now) {
  const raw = String(dateStr ?? '').trim();
  if (!raw) return null;
  const ms = Date.parse(raw);
  if (Number.isNaN(ms)) return null;
  return (now.getTime() - ms) / 60000;
}

/**
 * Classify one message against a clock you pass in. Pure, so the four non-final
 * states can be told apart at a fixed time in a test. Returns [state, detail].
 */
export function verdict(message, now, stuckAfter = 60) {
  const status = String(message.status ?? '').toLowerCase();

  if (FINAL.includes(status)) return ['final', `status ${status || 'unset'}`];

  if (status === 'scheduled') {
    const due = ageMinutes(message.send_at, now);
    if (due === null) {
      return ['scheduled',
        'waiting for a send window. The list response does not always carry ' +
        'send_at, so age these against your own record of when they were booked.'];
    }
    if (due < 0) {
      return ['scheduled',
        `waiting: due in ${Math.round(-due)} minute(s). No status callback ` +
        'fires while a message is scheduled.'];
    }
    return ['scheduled-overdue',
      `its send_at passed ${Math.round(due)} minute(s) ago and the status has ` +
      'not moved.'];
  }

  const age = ageMinutes(message.date_created, now);

  if (status === 'sent') {
    if (age !== null && age >= stuckAfter) {
      return ['sent-no-dlr',
        `sent ${Math.round(age)} minute(s) ago with no delivery receipt. On ` +
        'carriers that return no receipt, sent is the terminal state: count it ' +
        'as success rather than as a failure.'];
    }
    return ['in-flight', 'sent, waiting for a delivery receipt.'];
  }

  if (WAITING.includes(status)) {
    if (age === null) {
      return ['unknown-age',
        `status ${status} but date_created could not be read, so it cannot be aged.`];
    }
    if (age >= stuckAfter) {
      return ['stuck',
        `${status} for ${Math.round(age)} minute(s) with no error_code. The ` +
        "sender's queue is not draining; Twilio holds about ten hours of " +
        'segments per sender, then these fail with 30001 or expire with 30036.'];
    }
    return ['in-flight',
      `${status} for ${Math.round(age)} minute(s), still inside the window.`];
  }

  return ['unknown-status',
    `status ${status || 'unset'} is not one this script knows how to age.`];
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
  let params = { PageSize: 1000, 'DateSent>=': since };
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

  const arg = (name, fallback) => Number(process.argv.includes(name)
    ? process.argv[process.argv.indexOf(name) + 1] : fallback) || fallback;
  const days = arg('--days', 2);
  const stuckAfter = arg('--stuck-after', 60);
  const show = arg('--show', 20);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages since ${since}`);
    return;
  }

  const now = new Date();
  const counts = new Map();
  let shown = 0;
  let bad = 0;
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const [state, detail] = verdict(m, now, stuckAfter);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (!NOT_MOVING.includes(state)) continue;
    bad += 1;
    if (shown >= show) continue;
    shown += 1;
    console.warn(`${state.padEnd(17)} ${m.sid}  ${detail}`);
    if (state === 'scheduled-overdue') {
      console.warn(`  repair: cancel it with POST ${BASE}/Accounts/${account}` +
                   `/Messages/${m.sid}.json Status=canceled`);
    } else if (state === 'stuck') {
      console.warn('  repair: send through a Messaging Service with more senders ' +
                   `in the pool, and raise the validity period with POST ${MSG}` +
                   '/Services/{ServiceSid} ValidityPeriod=36000');
    }
  }

  console.log(`states: ${[...counts.entries()].sort()
    .map(([k, v]) => `${k} ${v}`).join(', ')}`);
  console.log(`${messages.length} message(s) over ${days} day(s), ${bad} not moving`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test here runs against a frozen clock, because a rule about age is untestable otherwise. The three that matter are the ones that keep the report honest: a message <code>scheduled</code> for next week is not stuck, a <code>sent</code> message with no delivery receipt is not a failure, and a date that will not parse is reported as unreadable rather than as four hours old.",
"test_py_file": "test_twilio_stuck_messages_audit.py",
"test_py": '''import datetime as dt

from twilio_stuck_messages_audit import age_minutes, verdict

NOW = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)


def rfc2822(hour, minute=0, day=1):
    return "Thu, %02d Jan 2026 %02d:%02d:00 +0000" % (day, hour, minute)


def test_age_is_read_from_rfc_2822_not_iso_8601():
    assert age_minutes(rfc2822(9), NOW) == 180
    assert age_minutes(rfc2822(14), NOW) == -120     # in the future
    assert age_minutes("2026-01-01T09:00:00Z", NOW) is None
    assert age_minutes("", NOW) is None
    assert age_minutes(None, NOW) is None


def test_four_hours_queued_with_no_error_code_is_stuck():
    state, detail = verdict({"status": "queued", "date_created": rfc2822(8)}, NOW)
    assert state == "stuck"
    assert "30036" in detail


def test_ten_minutes_queued_is_still_in_flight():
    state, _ = verdict({"status": "accepted", "date_created": rfc2822(11, 50)}, NOW)
    assert state == "in-flight"


def test_a_scheduled_message_is_not_stuck_however_old_the_row_is():
    state, detail = verdict({"status": "scheduled", "date_created": rfc2822(1),
                             "send_at": rfc2822(9, 0, day=8)}, NOW)
    assert state == "scheduled"
    assert "No status callback" in detail


def test_a_scheduled_message_whose_time_has_passed_is_a_finding():
    state, _ = verdict({"status": "scheduled", "send_at": rfc2822(9)}, NOW)
    assert state == "scheduled-overdue"


def test_sent_with_no_receipt_is_success_not_failure():
    state, detail = verdict({"status": "sent", "date_created": rfc2822(8)}, NOW)
    assert state == "sent-no-dlr"
    assert "success" in detail


def test_delivered_and_failed_are_both_final():
    assert verdict({"status": "delivered"}, NOW)[0] == "final"
    assert verdict({"status": "failed", "error_code": 30003}, NOW)[0] == "final"


def test_an_unreadable_date_is_reported_as_unreadable():
    state, detail = verdict({"status": "queued", "date_created": "yesterday"}, NOW)
    assert state == "unknown-age"
    assert "cannot" in detail
    assert verdict({"status": "partially_delivered"}, NOW)[0] == "unknown-status"


def test_the_threshold_is_an_argument_not_a_constant():
    msg = {"status": "queued", "date_created": rfc2822(11, 30)}
    assert verdict(msg, NOW)[0] == "in-flight"
    assert verdict(msg, NOW, stuck_after=15)[0] == "stuck"
''',
"test_js_file": "twilio-stuck-messages-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageMinutes, verdict } from './twilio-stuck-messages-audit.mjs';

const NOW = new Date('2026-01-01T12:00:00Z');
const pad = (n) => String(n).padStart(2, '0');
const rfc2822 = (hour, minute = 0, day = 1) =>
  `Thu, ${pad(day)} Jan 2026 ${pad(hour)}:${pad(minute)}:00 +0000`;

test('age is read from rfc 2822 dates', () => {
  assert.equal(ageMinutes(rfc2822(9), NOW), 180);
  assert.equal(ageMinutes(rfc2822(14), NOW), -120);
  assert.equal(ageMinutes('', NOW), null);
  assert.equal(ageMinutes(null, NOW), null);
});

test('four hours queued with no error code is stuck', () => {
  const [state, detail] = verdict({ status: 'queued', date_created: rfc2822(8) }, NOW);
  assert.equal(state, 'stuck');
  assert.match(detail, /30036/);
});

test('ten minutes queued is still in flight', () => {
  const [state] = verdict({ status: 'accepted', date_created: rfc2822(11, 50) }, NOW);
  assert.equal(state, 'in-flight');
});

test('a scheduled message is not stuck however old the row is', () => {
  const [state, detail] = verdict({ status: 'scheduled', date_created: rfc2822(1),
                                    send_at: rfc2822(9, 0, 8) }, NOW);
  assert.equal(state, 'scheduled');
  assert.match(detail, /No status callback/);
});

test('a scheduled message whose time has passed is a finding', () => {
  assert.equal(verdict({ status: 'scheduled', send_at: rfc2822(9) }, NOW)[0],
               'scheduled-overdue');
});

test('sent with no receipt is success, not failure', () => {
  const [state, detail] = verdict({ status: 'sent', date_created: rfc2822(8) }, NOW);
  assert.equal(state, 'sent-no-dlr');
  assert.match(detail, /success/);
});

test('delivered and failed are both final', () => {
  assert.equal(verdict({ status: 'delivered' }, NOW)[0], 'final');
  assert.equal(verdict({ status: 'failed', error_code: 30003 }, NOW)[0], 'final');
});

test('an unreadable date is reported as unreadable', () => {
  const [state, detail] = verdict({ status: 'queued', date_created: 'not a date' }, NOW);
  assert.equal(state, 'unknown-age');
  assert.match(detail, /cannot/);
  assert.equal(verdict({ status: 'partially_delivered' }, NOW)[0], 'unknown-status');
});

test('the threshold is an argument, not a constant', () => {
  const msg = { status: 'queued', date_created: rfc2822(11, 30) };
  assert.equal(verdict(msg, NOW)[0], 'in-flight');
  assert.equal(verdict(msg, NOW, 15)[0], 'stuck');
});
''',
"faq": [
 ("Why is there no error code on a message that has been queued for four hours?",
  "Because nothing has failed. Queued means Twilio holds the message and is metering it out at the sender's throughput. An error only appears when the queue overflows (30001) or the validity period runs out (30036), which is hours after the message stopped being useful."),
 ("How long is too long?",
  "It depends entirely on the traffic. An hour is a sane default for transactional sends and far too aggressive for a bulk campaign on a single long code, where a queue of several hours is the design working as intended. That is why the threshold is an argument rather than a constant in the script."),
 ("Is a message stuck at sent a problem?",
  "Usually not. Some carriers return no delivery receipt at all, and for those, sent is the last status the message will ever have. Counting them as failures understates delivery for entire countries; the script gives them their own state so the number you quote is defensible."),
 ("Does a scheduled message fire status callbacks while it waits?",
  "No. It sits with status scheduled until its send time arrives, which can be up to 35 days out, and nothing is reported in the meantime. A monitor that alerts on any non-final message will page somebody every night for messages that are working perfectly."),
 ("What actually fixes throughput starvation?",
  "More senders, not more retries. Send through a Messaging Service and put enough numbers in the pool that the segments have somewhere to go, then raise ValidityPeriod to 36000 so throttled messages are not discarded before their turn. The script prints both, and performs neither."),
],
"related": [
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering drops your SMS silently"),
 ("/twilio/landline-destination-30006/", "SMS to landlines that can never receive it"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_MSG, CITE_SCHEDULE, CITE_QUEUEING, CITE_SERVICE],
},

]
