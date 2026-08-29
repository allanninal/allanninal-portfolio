#!/usr/bin/env python3
"""/twilio/ field notes, batch Q — four messaging-delivery error codes.

Two of these look like the same failure and are not: 30003 is a handset that
might answer in ten minutes, 30005 is a number the carrier does not have. The
retry policy that is correct for one is a billed no-op for the other, and that
distinction is the whole reason both notes exist. The other two are the queue
deadline (30036) and the carrier media ceiling (30019).

Every script here is read only. GET requests and nothing else: they hold a
credential to an account that can send messages and spend money, so none of them
writes. They report, and they print the repair for a human to run.
"""

CITE_30003 = ("Error 30003: unreachable destination handset — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30003")
CITE_30005 = ("Error 30005: unknown destination handset — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30005")
CITE_30036 = ("Error 30036: validity period expired — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30036")
CITE_30045 = ("Error 30045: validity period out of range — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30045")
CITE_30019 = ("Error 30019: content size exceeds carrier limit — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30019")
CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_MEDIA = ("Media resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/media-resource")
CITE_MIME = ("Accepted MIME types for MMS — Twilio Docs",
             "https://www.twilio.com/docs/messaging/guides/accepted-mime-types")
CITE_LOOKUP = ("Lookup Line Type Intelligence — Twilio Docs",
               "https://www.twilio.com/docs/lookup/v2-api/line-type-intelligence")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_QUEUE = ("Scaling, queueing and message latency — Twilio Docs",
              "https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency")

GUIDES = [

{
"slug": "unreachable-destination-handset-30003",
"title": "Error 30003 is a handset that is off, not a dead number",
"description": "30003 is transient: retry once and most of it delivers. But a fifth of one sender's traffic failing this way is a carrier block wearing a handset error code.",
"h1": "error 30003 is a handset that is off, not a dead number",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30003", "unreachable destination handset",
             "twilio 30003 retry", "twilio undelivered 30003",
             "twilio sms handset unreachable"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The send succeeded. The status walked <code>queued</code>, <code>sent</code>, then <code>undelivered</code> with <code>error_code</code> <code>30003</code>, and the docs say the handset was unreachable &mdash; powered off, out of coverage, roaming. That is usually true and usually fixes itself. It is also exactly what a carrier block looks like from the outside, and the difference is arithmetic you have to do yourself.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and keep rows where <code>status</code> is <code>undelivered</code> and <code>error_code</code> is <code>30003</code>. Group them twice: by <code>to</code>, and by <code>messaging_service_sid</code> or <code>from</code>.</p>
<p>A recipient that fails repeatedly and has <em>never</em> delivered is a number to check with <code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence</code>. A <em>sender</em> losing a fifth of its traffic to 30003 across many different recipients is not handsets at all &mdash; carriers do not switch off a fifth of their subscribers at once.</p>""",
"problem": """<p>30003 is the error code that is safe to ignore right up until it isn't. Most of the time the phone really was off and a retry an hour later delivers, so the standard handling &mdash; log it, retry once, move on &mdash; is correct and stays correct for months. Nothing about a single 30003 tells you otherwise.</p>
<p>What the code cannot tell you is the shape of the failure across the account, and the shape is where the two real problems live. One is list decay: the same handful of numbers failing every campaign, never delivering once, quietly consuming a retry budget. The other is worse. When a carrier starts refusing a sender it does not always come back as 30007; a persistent 30003 on one long code, spread across hundreds of unrelated recipients, is the same outage with a friendlier error code on it. Both are invisible to per-message handling because both are properties of the set, not of any message in it.</p>""",
"why": """<p><strong>The Messages list has no error filter.</strong> No <code>Status</code> parameter and no <code>ErrorCode</code> parameter exist on <code>Messages.json</code>; the documented filters are <code>To</code>, <code>From</code>, <code>DateSent</code>, <code>DateSent&lt;</code>, <code>DateSent&gt;</code> and paging. Finding 30003 at all means paging the window and filtering in your own code, so this check exists only if somebody writes it.</p>
<p><strong>The retry that fixes it also hides it.</strong> A queue that retries 30003 automatically converts a permanent problem into a recurring cost. The message eventually stops being retried, nobody looks at why, and the number stays on the list for another year.</p>
<p><strong>Per-message handling cannot see a rate.</strong> Your webhook receives one status callback at a time. Whether this is the third 30003 today or the three-thousandth is not in the payload, and 30003 at 1% is normal traffic while 30003 at 20% on one sender is an incident.</p>
<p><strong>Roaming and coverage are real, which makes the excuse durable.</strong> There is always a plausible story for any individual 30003, so the finding has to be a number rather than an anecdote: how many, over how many distinct recipients, from which sender.</p>""",
"steps": [
 {"h": "Page the Messages list over a bounded window",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. Bound it by days and by a hard message cap. A busy account will hand you a million rows and the answer stops improving after a few thousand.</p>"""},
 {"h": "Read error_code as a number",
  "body": """<p><code>error_code</code> is <code>null</code> on healthy messages and an integer on failed ones, but it comes back as a string often enough that a comparison against <code>30003</code> without coercion reports zero findings on an account full of them. Coerce once, in one place.</p>"""},
 {"h": "Group by recipient and count what else that number did",
  "body": """<p>For each <code>to</code> with a 30003, count how many 30003s it has and how many messages to it <code>delivered</code> in the same window. A number with failures <em>and</em> deliveries is a flaky handset and stays on the list. A number with failures and no deliveries has never taken a message from you, which is a different claim entirely.</p>"""},
 {"h": "Group by sender and compute the rate",
  "body": """<p>Bucket on <code>messaging_service_sid</code> when set and <code>from</code> otherwise. Two numbers matter per sender: the share of its outbound traffic that 30003'd, and how many <em>distinct</em> recipients those failures touched. Many failures over few recipients is list hygiene. Many failures over many recipients is the sender.</p>"""},
 {"h": "Settle the repeat offenders with Lookup, escalate the sender",
  "body": """<p><code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence</code> and read <code>line_type_intelligence.type</code>; anything that is not <code>mobile</code> comes off the SMS list. If the finding is sender-shaped instead, collect three Message SIDs and open a Twilio Support ticket &mdash; there is no field to set for this one.</p>"""},
],
"verify": """<p>Re-run the script over the same window after the list clean-up. Senders should read <code>handsets</code> or <code>clean</code>, and no sender should be <code>sender-blocked</code>.</p>
<pre><code class="language-bash">python3 twilio_unreachable_handset_audit.py --days 7
# 4 sender(s), 61 recipient(s) with a 30003, 0 sender-level problem(s)</code></pre>""",
"code_intro": "One paginated GET over the Messages list and nothing else &mdash; an API Key with read access is all it can use. The grouping and both verdicts are pure functions, because every judgement in this note is arithmetic (what share is too high, how many failures per recipient stops being coincidence) and arithmetic belongs somewhere you can read it and argue with it.",
"py_file": "twilio_unreachable_handset_audit.py",
"py": '''"""Report Twilio 30003 failures, split into unreachable handsets and a blocked sender.

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
log = logging.getLogger("twilio_unreachable_handset_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

UNREACHABLE = 30003


def error_code(message):
    """Read error_code as an integer, or None.

    It is null on every healthy message and a number on failed ones, but it
    arrives as a string often enough to matter. Comparing the raw value against
    30003 is the mistake that makes this audit report nothing on an account that
    is full of findings.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def group(messages):
    """Bucket 30003 twice over: by recipient and by sender.

    Pure, so both grouping rules can be tested without a network. Recipients with
    no 30003 are dropped at the end; they are only tracked along the way so that
    a failing number's delivered count is available, which is what separates a
    flaky handset from a number that has never once taken a message.

    Returns (recipients, senders).
    """
    recipients = {}
    senders = {}
    touched = {}

    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue

        sender = m.get("messaging_service_sid") or m.get("from") or "unknown sender"
        stats = senders.setdefault(sender, {"total": 0, "failed": 0,
                                            "recipients": 0, "sids": []})
        stats["total"] += 1

        to = m.get("to") or "unknown recipient"
        row = recipients.setdefault(to, {"hits": 0, "delivered": 0, "sids": []})
        if str(m.get("status") or "").lower() == "delivered":
            row["delivered"] += 1

        if error_code(m) == UNREACHABLE:
            row["hits"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
            stats["failed"] += 1
            if len(stats["sids"]) < 3:
                stats["sids"].append(m.get("sid"))
            touched.setdefault(sender, set()).add(to)

    for sender, tos in touched.items():
        senders[sender]["recipients"] = len(tos)

    return ({k: v for k, v in recipients.items() if v["hits"]}, senders)


def recipient_verdict(row):
    """Classify one recipient's 30003 history. Pure, so the rule is testable.

    Returns (state, detail).
    """
    hits = int(row.get("hits") or 0)
    delivered = int(row.get("delivered") or 0)

    if hits <= 1:
        return ("transient",
                "one 30003 and %d delivered. Powered off, out of coverage or "
                "roaming: retry once after a delay and expect it to arrive."
                % delivered)

    if delivered:
        return ("flaky",
                "%d unreachable, %d delivered in the same window. This number "
                "does take SMS, just not every time: back the retries off, do "
                "not drop it." % (hits, delivered))

    return ("never-reached",
            "%d unreachable and not one delivery, ever. Stop retrying and run "
            "Lookup line type intelligence: a number that has never accepted a "
            "message is usually not a mobile." % hits)


def sender_verdict(stats, min_failed=3):
    """Classify one sender's 30003 rate. Pure, so the thresholds are visible.

    Returns (state, detail).
    """
    total = int(stats.get("total") or 0)
    failed = int(stats.get("failed") or 0)
    distinct = int(stats.get("recipients") or 0)

    if not failed:
        return ("clean", "%d message(s), no 30003" % total)

    rate = (failed / total) if total else 1.0

    if failed < min_failed:
        return ("isolated",
                "%d of %d unreachable (%.1f%%). Too few to read anything into: "
                "handsets are off all the time." % (failed, total, rate * 100))

    if distinct and failed / distinct >= 3:
        return ("dead-numbers",
                "%d failures over only %d recipient(s). The failures pile onto a "
                "handful of numbers, so this is list decay rather than anything "
                "wrong with the sender." % (failed, distinct))

    if rate >= 0.2:
        return ("sender-blocked",
                "%d of %d unreachable (%.1f%%) across %d recipient(s). No carrier "
                "switches off a fifth of its subscribers at once: at this spread "
                "30003 is masking a block on the sender itself."
                % (failed, total, rate * 100, distinct))

    return ("handsets",
            "%d of %d unreachable (%.1f%%) across %d recipient(s). Thin and spread "
            "out, which is what genuine handset unreachability looks like: one "
            "retry each." % (failed, total, rate * 100, distinct))


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
    resource, so the date window and the page cap are the only bounds available."""
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
    ap.add_argument("--min-failed", type=int, default=3,
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

    recipients, senders = group(messages)

    bad = 0
    for sender, stats in sorted(senders.items()):
        state, detail = sender_verdict(stats, args.min_failed)
        line = "%-14s %s  %s" % (state, sender, detail)
        if state in ("clean", "isolated", "handsets"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
        if state == "sender-blocked":
            log.warning("  repair: no API call fixes this. Send those SIDs to "
                        "Twilio Support and ask whether the sender is blocked "
                        "on the destination carrier.")
        else:
            log.warning("  repair: check each repeat offender with GET "
                        "https://lookups.twilio.com/v2/PhoneNumbers/{E164}"
                        "?Fields=line_type_intelligence and drop anything whose "
                        "line_type_intelligence.type is not mobile.")

    for to, row in sorted(recipients.items()):
        state, detail = recipient_verdict(row)
        if state == "transient":
            continue
        log.warning("%-14s %s  %s", state, to, detail)

    log.info("%d sender(s), %d recipient(s) with a 30003, %d sender-level problem(s)",
             len(senders), len(recipients), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-unreachable-handset-audit.mjs",
"js": '''/**
 * Report Twilio 30003 failures, split into unreachable handsets and a blocked sender.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const UNREACHABLE = 30003;

/**
 * Read error_code as a number, or null. It is null on healthy messages and a
 * number on failed ones, but it arrives as a string often enough that comparing
 * the raw value against 30003 is how this audit reports nothing on an account
 * full of findings.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Bucket 30003 twice over: by recipient and by sender. Pure, so both grouping
 * rules can be tested without a network. Recipients with no 30003 are dropped at
 * the end; they are tracked along the way only so a failing number's delivered
 * count is available. Returns { recipients, senders }.
 */
export function group(messages) {
  const recipients = new Map();
  const senders = new Map();
  const touched = new Map();

  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;

    const sender = m.messaging_service_sid || m.from || 'unknown sender';
    if (!senders.has(sender)) {
      senders.set(sender, { total: 0, failed: 0, recipients: 0, sids: [] });
    }
    const stats = senders.get(sender);
    stats.total += 1;

    const to = m.to || 'unknown recipient';
    if (!recipients.has(to)) recipients.set(to, { hits: 0, delivered: 0, sids: [] });
    const row = recipients.get(to);
    if (String(m.status ?? '').toLowerCase() === 'delivered') row.delivered += 1;

    if (errorCode(m) === UNREACHABLE) {
      row.hits += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
      stats.failed += 1;
      if (stats.sids.length < 3) stats.sids.push(m.sid);
      if (!touched.has(sender)) touched.set(sender, new Set());
      touched.get(sender).add(to);
    }
  }

  for (const [sender, tos] of touched) senders.get(sender).recipients = tos.size;
  for (const [to, row] of [...recipients]) if (!row.hits) recipients.delete(to);

  return { recipients, senders };
}

/**
 * Classify one recipient's 30003 history. Pure. Returns [state, detail].
 */
export function recipientVerdict(row) {
  const hits = Number(row.hits ?? 0);
  const delivered = Number(row.delivered ?? 0);

  if (hits <= 1) {
    return ['transient',
      `one 30003 and ${delivered} delivered. Powered off, out of coverage or ` +
      'roaming: retry once after a delay and expect it to arrive.'];
  }

  if (delivered) {
    return ['flaky',
      `${hits} unreachable, ${delivered} delivered in the same window. This ` +
      'number does take SMS, just not every time: back the retries off, do not ' +
      'drop it.'];
  }

  return ['never-reached',
    `${hits} unreachable and not one delivery, ever. Stop retrying and run ` +
    'Lookup line type intelligence: a number that has never accepted a message ' +
    'is usually not a mobile.'];
}

/**
 * Classify one sender's 30003 rate. Pure, so the thresholds are visible and
 * testable. Returns [state, detail].
 */
export function senderVerdict(stats, minFailed = 3) {
  const total = Number(stats.total ?? 0);
  const failed = Number(stats.failed ?? 0);
  const distinct = Number(stats.recipients ?? 0);

  if (!failed) return ['clean', `${total} message(s), no 30003`];

  const rate = total ? failed / total : 1;
  const pct = (rate * 100).toFixed(1);

  if (failed < minFailed) {
    return ['isolated',
      `${failed} of ${total} unreachable (${pct}%). Too few to read anything ` +
      'into: handsets are off all the time.'];
  }

  if (distinct && failed / distinct >= 3) {
    return ['dead-numbers',
      `${failed} failures over only ${distinct} recipient(s). The failures pile ` +
      'onto a handful of numbers, so this is list decay rather than anything ' +
      'wrong with the sender.'];
  }

  if (rate >= 0.2) {
    return ['sender-blocked',
      `${failed} of ${total} unreachable (${pct}%) across ${distinct} ` +
      'recipient(s). No carrier switches off a fifth of its subscribers at ' +
      'once: at this spread 30003 is masking a block on the sender itself.'];
  }

  return ['handsets',
    `${failed} of ${total} unreachable (${pct}%) across ${distinct} recipient(s). ` +
    'Thin and spread out, which is what genuine handset unreachability looks ' +
    'like: one retry each.'];
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

  const { recipients, senders } = group(messages);

  let bad = 0;
  for (const [sender, stats] of [...senders.entries()].sort()) {
    const [state, detail] = senderVerdict(stats);
    const line = `${state.padEnd(14)} ${sender}  ${detail}`;
    if (state === 'clean' || state === 'isolated' || state === 'handsets') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    console.warn(`  message sids: ${stats.sids.join(', ')}`);
    if (state === 'sender-blocked') {
      console.warn('  repair: no API call fixes this. Send those SIDs to Twilio ' +
                   'Support and ask whether the sender is blocked on the ' +
                   'destination carrier.');
    } else {
      console.warn('  repair: check each repeat offender with GET ' +
                   'https://lookups.twilio.com/v2/PhoneNumbers/{E164}' +
                   '?Fields=line_type_intelligence and drop anything whose ' +
                   'line_type_intelligence.type is not mobile.');
    }
  }

  for (const [to, row] of [...recipients.entries()].sort()) {
    const [state, detail] = recipientVerdict(row);
    if (state === 'transient') continue;
    console.warn(`${state.padEnd(14)} ${to}  ${detail}`);
  }

  console.log(`${senders.size} sender(s), ${recipients.size} recipient(s) with a ` +
              `30003, ${bad} sender-level problem(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones where the same failure count means two different things. Twelve failures over three recipients is list decay; thirty failures over thirty recipients at the same volume is a blocked sender. And a recipient that fails twice but delivered once stays on the list, because dropping numbers that demonstrably receive your SMS is the expensive way to get this wrong.",
"test_py_file": "test_twilio_unreachable_handset_audit.py",
"test_py": '''from twilio_unreachable_handset_audit import (error_code, group,
                                              recipient_verdict, sender_verdict)


def unreachable(sid, to="+15557770001", sender="+15550001111"):
    return {"sid": sid, "to": to, "from": sender, "status": "undelivered",
            "error_code": 30003, "direction": "outbound-api"}


def delivered(sid, to="+15557770001", sender="+15550001111"):
    return {"sid": sid, "to": to, "from": sender, "status": "delivered",
            "error_code": None, "direction": "outbound-api"}


def test_error_code_reads_strings_and_numbers_the_same():
    assert error_code({"error_code": 30003}) == 30003
    assert error_code({"error_code": "30003"}) == 30003
    assert error_code({"error_code": None}) is None
    assert error_code({}) is None


def test_group_drops_recipients_that_never_failed():
    recipients, senders = group([unreachable("SM1"), delivered("SM2", to="+15557770002")])
    assert set(recipients) == {"+15557770001"}
    assert senders["+15550001111"]["total"] == 2
    assert senders["+15550001111"]["failed"] == 1


def test_group_counts_distinct_recipients_per_sender():
    msgs = [unreachable("SM%d" % i, to="+1555777%04d" % i) for i in range(5)]
    _, senders = group(msgs)
    assert senders["+15550001111"]["recipients"] == 5


def test_group_prefers_the_messaging_service_over_the_from_number():
    m = unreachable("SM1")
    m["messaging_service_sid"] = "MG1"
    _, senders = group([m])
    assert set(senders) == {"MG1"}


def test_group_ignores_inbound_messages():
    recipients, senders = group([{"sid": "SM1", "to": "+15550001111",
                                  "direction": "inbound", "status": "received"}])
    assert recipients == {}
    assert senders == {}


def test_one_failure_is_transient():
    state, detail = recipient_verdict({"hits": 1, "delivered": 0})
    assert state == "transient"
    assert "retry once" in detail


def test_a_number_that_also_delivers_is_flaky_and_stays_on_the_list():
    state, detail = recipient_verdict({"hits": 4, "delivered": 2})
    assert state == "flaky"
    assert "do not drop it" in detail


def test_repeated_failures_with_no_delivery_ever_go_to_lookup():
    state, detail = recipient_verdict({"hits": 4, "delivered": 0})
    assert state == "never-reached"
    assert "Lookup" in detail


def test_no_failures_is_a_clean_sender():
    state, detail = sender_verdict({"total": 900, "failed": 0})
    assert state == "clean"
    assert "900" in detail


def test_two_failures_are_too_few_to_mean_anything():
    state, _ = sender_verdict({"total": 4, "failed": 2, "recipients": 1})
    assert state == "isolated"


def test_many_failures_over_few_recipients_is_list_decay():
    # Same failure count as the blocked-sender case below; the spread is the
    # only thing that distinguishes them.
    state, detail = sender_verdict({"total": 100, "failed": 12, "recipients": 3})
    assert state == "dead-numbers"
    assert "list decay" in detail


def test_the_same_failures_spread_wide_is_a_blocked_sender():
    state, detail = sender_verdict({"total": 100, "failed": 30, "recipients": 30})
    assert state == "sender-blocked"
    assert "fifth" in detail


def test_a_thin_wide_spread_is_ordinary_handsets():
    state, detail = sender_verdict({"total": 500, "failed": 5, "recipients": 5})
    assert state == "handsets"
    assert "one retry each" in detail
''',
"test_js_file": "twilio-unreachable-handset-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { errorCode, group, recipientVerdict, senderVerdict }
  from './twilio-unreachable-handset-audit.mjs';

const unreachable = (sid, to = '+15557770001', sender = '+15550001111') => ({
  sid, to, from: sender, status: 'undelivered', error_code: 30003,
  direction: 'outbound-api',
});

const delivered = (sid, to = '+15557770001', sender = '+15550001111') => ({
  sid, to, from: sender, status: 'delivered', error_code: null,
  direction: 'outbound-api',
});

test('error code reads strings and numbers the same', () => {
  assert.equal(errorCode({ error_code: 30003 }), 30003);
  assert.equal(errorCode({ error_code: '30003' }), 30003);
  assert.equal(errorCode({ error_code: null }), null);
  assert.equal(errorCode({}), null);
});

test('group drops recipients that never failed', () => {
  const { recipients, senders } = group([
    unreachable('SM1'), delivered('SM2', '+15557770002')]);
  assert.deepEqual([...recipients.keys()], ['+15557770001']);
  assert.equal(senders.get('+15550001111').total, 2);
  assert.equal(senders.get('+15550001111').failed, 1);
});

test('group counts distinct recipients per sender', () => {
  const msgs = [0, 1, 2, 3, 4].map((i) => unreachable(`SM${i}`, `+1555777000${i}`));
  const { senders } = group(msgs);
  assert.equal(senders.get('+15550001111').recipients, 5);
});

test('group prefers the messaging service over the from number', () => {
  const m = { ...unreachable('SM1'), messaging_service_sid: 'MG1' };
  const { senders } = group([m]);
  assert.deepEqual([...senders.keys()], ['MG1']);
});

test('group ignores inbound messages', () => {
  const { recipients, senders } = group([
    { sid: 'SM1', to: '+15550001111', direction: 'inbound', status: 'received' }]);
  assert.equal(recipients.size, 0);
  assert.equal(senders.size, 0);
});

test('one failure is transient', () => {
  const [state, detail] = recipientVerdict({ hits: 1, delivered: 0 });
  assert.equal(state, 'transient');
  assert.match(detail, /retry once/);
});

test('a number that also delivers is flaky and stays on the list', () => {
  const [state, detail] = recipientVerdict({ hits: 4, delivered: 2 });
  assert.equal(state, 'flaky');
  assert.match(detail, /do not drop it/);
});

test('repeated failures with no delivery ever go to Lookup', () => {
  const [state, detail] = recipientVerdict({ hits: 4, delivered: 0 });
  assert.equal(state, 'never-reached');
  assert.match(detail, /Lookup/);
});

test('no failures is a clean sender', () => {
  const [state, detail] = senderVerdict({ total: 900, failed: 0 });
  assert.equal(state, 'clean');
  assert.match(detail, /900/);
});

test('two failures are too few to mean anything', () => {
  const [state] = senderVerdict({ total: 4, failed: 2, recipients: 1 });
  assert.equal(state, 'isolated');
});

test('many failures over few recipients is list decay', () => {
  const [state, detail] = senderVerdict({ total: 100, failed: 12, recipients: 3 });
  assert.equal(state, 'dead-numbers');
  assert.match(detail, /list decay/);
});

test('the same failures spread wide is a blocked sender', () => {
  const [state, detail] = senderVerdict({ total: 100, failed: 30, recipients: 30 });
  assert.equal(state, 'sender-blocked');
  assert.match(detail, /fifth/);
});

test('a thin wide spread is ordinary handsets', () => {
  const [state, detail] = senderVerdict({ total: 500, failed: 5, recipients: 5 });
  assert.equal(state, 'handsets');
  assert.match(detail, /one retry each/);
});
''',
"faq": [
 ("Is 30003 worth retrying?",
  "Once, after a delay. The handset really may be off or out of coverage, and a single retry an hour later recovers most of it. What is not worth retrying is a number that has produced several 30003s and never a single delivery, because that pattern is not a handset that happens to be off."),
 ("How is 30003 different from 30005?",
  "30003 is transient and 30005 is permanent. 30003 says the handset could not be reached right now; 30005 says the carrier does not recognise the number at all. Retrying the first is correct, retrying the second is billed and can never succeed. They need separate handling, which is why they are separate notes."),
 ("Why can't I filter the Messages list for error 30003 directly?",
  "Because the list resource has no ErrorCode parameter and no Status parameter. The documented filters are To, From, DateSent, DateSent< and DateSent>, plus paging. Every 30003 report pages the window and filters client-side."),
 ("When does 30003 actually mean my sender is blocked?",
  "When the rate is high and the spread is wide. A fifth of one sender's traffic failing across dozens of unrelated recipients is not dozens of phones being off simultaneously. Carriers do not always return 30007 when they refuse a sender, and a persistent wide 30003 is one of the shapes that refusal takes."),
 ("Does the script change anything on my account?",
  "No. It issues GET requests to the Messages list and nothing else, and it prints the repair rather than performing it: which numbers to check with Lookup, and which Message SIDs to attach to a Support ticket. Give it an API Key with read access, not the account auth token."),
],
"related": [
 ("/twilio/unknown-destination-handset-30005/", "The permanent version: error 30005"),
 ("/twilio/landline-destination-30006/", "SMS to landlines that can never receive it"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering that drops SMS silently"),
],
"citations": [CITE_30003, CITE_30005, CITE_MSG, CITE_LOOKUP],
},


{
"slug": "unknown-destination-handset-30005",
"title": "Error 30005 is permanent: the carrier has no such number",
"description": "30005 means the number does not exist on the carrier. Retrying is billed and can never work, so the finding is which contacts to delete rather than requeue.",
"h1": "error 30005 is permanent: the carrier has no such number",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30005", "unknown destination handset",
             "twilio 30005 permanent failure", "twilio disconnected number sms",
             "twilio undelivered 30005"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The same number fails every campaign. Every time, <code>undelivered</code>, <code>error_code</code> <code>30005</code>, and every time the retry queue picks it up again because the handler that wrote it treated 30005 the way it treats 30003. It is not the same thing. The carrier is not saying the handset was busy; it is saying it has never heard of that number.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and collect the distinct <code>to</code> values on rows where <code>error_code</code> is <code>30005</code>. Any recipient with two or more 30005s <strong>on separate days</strong> is permanently dead: delete it from the sending list.</p>
<p>Two guards keep that rule honest. Count the same recipient's <code>delivered</code> messages in the window &mdash; a number that later delivered was reassigned and must not be deleted. And parse the day properly: the Messages list returns RFC 2822 timestamps, so slicing the first ten characters gives you <code>Fri, 21 A</code> and collapses every failure onto one day.</p>""",
"problem": """<p>30005 is the cheapest problem on this list to fix and the easiest to leave running for years, because it costs a fraction of a cent at a time. A number gets disconnected, or was mistyped at signup, or was never real. Your list keeps it. Every campaign sends to it, every send is accepted, priced and marked undelivered, and nothing anywhere says <em>stop</em>.</p>
<p>The retry loop is what turns it from a rounding error into a real one. Most delivery handlers are written around 30003, where retrying is the correct answer, and 30005 arrives through the same code path with the same shape: undelivered, an error code, a Message SID. So it is retried on the same schedule, indefinitely, against a number the carrier has already said does not exist. Multiply by a list that has been accumulating dead numbers since the product launched and the cost stops being invisible &mdash; and the delivery rate you report to the business has a permanent floor in it that nobody can explain.</p>""",
"why": """<p><strong>Nothing in the payload says permanent.</strong> A status callback carrying 30005 looks exactly like one carrying 30003: same fields, same shape, same status. The permanence lives in the docs for the code, not in the message, so a handler that switches on <code>status</code> rather than on <code>error_code</code> cannot tell them apart.</p>
<p><strong>The Messages list cannot be queried by error.</strong> No <code>ErrorCode</code> parameter, no <code>Status</code> parameter &mdash; only <code>To</code>, <code>From</code>, <code>DateSent</code> and paging. The only way to find your 30005s is to page the window and filter client-side.</p>
<p><strong>Twilio's timestamps are not ISO.</strong> <code>date_sent</code> comes back as <code>Fri, 21 Aug 2026 19:14:22 +0000</code>. The distinct-day count is the entire rule that separates a dead number from a single anomaly, and the obvious ten-character slice destroys it silently: every failure lands on the same fake day and every dead number reads as a one-off.</p>
<p><strong>Numbers get reassigned.</strong> US carriers reissue disconnected numbers to new subscribers. A number that 30005'd in March can deliver in August, to a different person. Deleting on the strength of an old failure is how a real customer stops receiving anything, which is why the delivered count has to be part of the verdict.</p>""",
"steps": [
 {"h": "Page the Messages list over a bounded window",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>, with a day window and a hard message cap. Make the window at least a fortnight: the rule needs failures on separate days, and a two-day window cannot produce that evidence.</p>"""},
 {"h": "Filter on error_code 30005 and nothing else",
  "body": """<p>Coerce <code>error_code</code> to an integer first; it is <code>null</code> on healthy rows and sometimes a string on failed ones. Do not fold 30003 or 30006 into the same bucket. They are different failures with different repairs, and pooling them is how a transient handset ends up deleted.</p>"""},
 {"h": "Reduce each timestamp to a real calendar day",
  "body": """<p><code>date_sent</code> is RFC 2822. Parse the month name and rebuild <code>YYYY-MM-DD</code>, then dedupe. Two failures on the same afternoon are one retry loop; two failures three weeks apart are a carrier telling you the same thing twice, which is the finding.</p>"""},
 {"h": "Count deliveries to the same number before condemning it",
  "body": """<p>For every recipient with a 30005, count messages to it with <code>status</code> <code>delivered</code> in the same window. Any delivery at all overrides the failures: the number is live now, whoever owns it, and it stays on the list.</p>"""},
 {"h": "Delete, do not requeue, and validate at capture time",
  "body": """<p>Remove the confirmed numbers from your own contact table &mdash; there is no Twilio-side list to update. Then close the source: <code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence</code> at signup rejects invalid and non-mobile numbers before they ever reach a campaign.</p>"""},
],
"verify": """<p>Re-run over the same window after the deletions. Nothing should be in the <code>dead</code> or <code>retry-loop</code> state; a handful of <code>suspect</code> rows is normal on any live list.</p>
<pre><code class="language-bash">python3 twilio_dead_number_audit.py --days 30
# 30005 on 14 recipient(s) over 30 day(s), 0 confirmed dead</code></pre>""",
"code_intro": "One paginated GET over the Messages list, and an API Key with read access is all it can use. Three pure functions carry the note: the error-code coercion, the RFC 2822 day parser, and the verdict. The day parser looks like plumbing and is not &mdash; it is the function the whole permanence rule rests on, and it is the one most likely to be written as a ten-character slice and never questioned.",
"py_file": "twilio_dead_number_audit.py",
"py": '''"""Report phone numbers that Twilio reports as unknown to the carrier (30005).

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
log = logging.getLogger("twilio_dead_number_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

UNKNOWN_HANDSET = 30005

MONTHS = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05",
          "jun": "06", "jul": "07", "aug": "08", "sep": "09", "oct": "10",
          "nov": "11", "dec": "12"}


def error_code(message):
    """Read error_code as an integer, or None.

    Null on healthy messages, a number on failed ones, and a string often enough
    that comparing the raw value against 30005 quietly reports nothing.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def day(value):
    """Reduce a Twilio timestamp to YYYY-MM-DD. Pure, and load-bearing.

    The Messages list returns RFC 2822 dates like "Fri, 21 Aug 2026 19:14:22
    +0000", not ISO ones. The obvious value[:10] slice yields "Fri, 21 A", so
    every failure collapses onto one identical fake day and the distinct-day
    rule - which is the only thing separating a dead number from an anomaly -
    silently stops working. ISO strings are accepted too, because scheduled
    messages and exports can hand you either.
    """
    s = str(value or "").strip()
    if not s:
        return None
    if "," in s:
        parts = s.replace(",", " ").split()
        if len(parts) >= 4 and parts[2][:3].lower() in MONTHS:
            try:
                return "%s-%s-%02d" % (parts[3], MONTHS[parts[2][:3].lower()],
                                       int(parts[1]))
            except (TypeError, ValueError):
                return None
        return None
    return s[:10] if len(s) >= 10 else None


def by_recipient(messages):
    """Bucket 30005 by destination number, with the delivered count alongside.

    Pure, so the grouping can be tested without a network. Recipients with no
    30005 are dropped at the end; they are tracked along the way only so that a
    failing number's deliveries are counted, which is the guard against deleting
    a number that was reassigned to somebody real.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        to = m.get("to") or "unknown recipient"
        row = out.setdefault(to, {"dead": 0, "delivered": 0, "days": [], "sids": []})
        if str(m.get("status") or "").lower() == "delivered":
            row["delivered"] += 1
        if error_code(m) == UNKNOWN_HANDSET:
            row["dead"] += 1
            d = day(m.get("date_sent") or m.get("date_created"))
            if d and d not in row["days"]:
                row["days"].append(d)
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
    for row in out.values():
        row["days"].sort()
    return {k: v for k, v in out.items() if v["dead"]}


def verdict(row):
    """Classify one recipient. Pure, so the permanence rule is testable.

    Returns (state, detail).
    """
    dead = int(row.get("dead") or 0)
    delivered = int(row.get("delivered") or 0)
    days = list(row.get("days") or [])

    if not dead:
        return ("clean", "no 30005 on this number")

    if delivered:
        return ("recovered",
                "%d unknown-handset failures but %d delivered in the same window. "
                "30005 is permanent for a number, not for a person: carriers "
                "reissue disconnected numbers. Keep this one." % (dead, delivered))

    if dead >= 2 and len(days) >= 2:
        return ("dead",
                "%d failures on %d separate days (%s). The carrier does not have "
                "this number. Delete it from the list: no retry can ever succeed "
                "and every attempt is billed."
                % (dead, len(days), ", ".join(days)))

    if dead >= 2:
        return ("retry-loop",
                "%d failures, all on %s. Something is retrying a permanent "
                "failure inside a single day. 30005 is not 30003 - waiting "
                "changes nothing, and each attempt costs."
                % (dead, days[0] if days else "one day"))

    return ("suspect",
            "one 30005. Permanent by definition, but one row is one row: confirm "
            "with Lookup line type intelligence before deleting a customer record.")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. No Status or ErrorCode filter exists on this resource,
    so the date window and the page cap are the only bounds available."""
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
                    help="how far back to read the Messages list; the rule needs "
                         "failures on separate days, so keep this wide")
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

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages sent since %s", since)
        return 0

    rows = by_recipient(messages)
    if not rows:
        log.info("no 30005 in %d message(s) since %s", len(messages), since)
        return 0

    confirmed = 0
    for to, row in sorted(rows.items()):
        state, detail = verdict(row)
        line = "%-11s %s  %s" % (state, to, detail)
        if state in ("recovered", "suspect"):
            log.info(line)
            continue
        confirmed += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in row["sids"]))
        log.warning("  repair: delete %s from your own contact table - Twilio has "
                    "no list to update - and gate new signups with GET "
                    "https://lookups.twilio.com/v2/PhoneNumbers/%s"
                    "?Fields=line_type_intelligence", to, to)

    log.info("30005 on %d recipient(s) over %d day(s), %d confirmed dead",
             len(rows), args.days, confirmed)
    return 1 if confirmed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-dead-number-audit.mjs",
"js": '''/**
 * Report phone numbers that Twilio reports as unknown to the carrier (30005).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const UNKNOWN_HANDSET = 30005;

const MONTHS = {
  jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06',
  jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12',
};

/**
 * Read error_code as a number, or null. Null on healthy messages, a number on
 * failed ones, and a string often enough that comparing the raw value against
 * 30005 quietly reports nothing.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Reduce a Twilio timestamp to YYYY-MM-DD. Pure, and load-bearing.
 *
 * The Messages list returns RFC 2822 dates like "Fri, 21 Aug 2026 19:14:22
 * +0000". Slicing the first ten characters yields "Fri, 21 A", so every failure
 * collapses onto one fake day and the distinct-day rule stops working without
 * ever raising anything. ISO strings are accepted too.
 */
export function day(value) {
  const s = String(value ?? '').trim();
  if (!s) return null;
  if (s.includes(',')) {
    const parts = s.replace(/,/g, ' ').split(/\\s+/).filter(Boolean);
    const month = parts.length >= 4 ? MONTHS[parts[2].slice(0, 3).toLowerCase()] : null;
    if (!month) return null;
    const dd = Number(parts[1]);
    if (!Number.isFinite(dd)) return null;
    return `${parts[3]}-${month}-${String(dd).padStart(2, '0')}`;
  }
  return s.length >= 10 ? s.slice(0, 10) : null;
}

/**
 * Bucket 30005 by destination number, with the delivered count alongside. Pure,
 * so the grouping can be tested without a network. Recipients with no 30005 are
 * dropped at the end; they are tracked only so a failing number's deliveries are
 * counted, which is the guard against deleting a reassigned number.
 */
export function byRecipient(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const to = m.to || 'unknown recipient';
    if (!out.has(to)) out.set(to, { dead: 0, delivered: 0, days: [], sids: [] });
    const row = out.get(to);
    if (String(m.status ?? '').toLowerCase() === 'delivered') row.delivered += 1;
    if (errorCode(m) === UNKNOWN_HANDSET) {
      row.dead += 1;
      const d = day(m.date_sent || m.date_created);
      if (d && !row.days.includes(d)) row.days.push(d);
      if (row.sids.length < 3) row.sids.push(m.sid);
    }
  }
  for (const [to, row] of [...out]) {
    if (!row.dead) out.delete(to);
    else row.days.sort();
  }
  return out;
}

/**
 * Classify one recipient. Pure, so the permanence rule is testable.
 * Returns [state, detail].
 */
export function verdict(row) {
  const dead = Number(row.dead ?? 0);
  const delivered = Number(row.delivered ?? 0);
  const days = [...(row.days ?? [])];

  if (!dead) return ['clean', 'no 30005 on this number'];

  if (delivered) {
    return ['recovered',
      `${dead} unknown-handset failures but ${delivered} delivered in the same ` +
      'window. 30005 is permanent for a number, not for a person: carriers ' +
      'reissue disconnected numbers. Keep this one.'];
  }

  if (dead >= 2 && days.length >= 2) {
    return ['dead',
      `${dead} failures on ${days.length} separate days (${days.join(', ')}). ` +
      'The carrier does not have this number. Delete it from the list: no retry ' +
      'can ever succeed and every attempt is billed.'];
  }

  if (dead >= 2) {
    return ['retry-loop',
      `${dead} failures, all on ${days[0] ?? 'one day'}. Something is retrying a ` +
      'permanent failure inside a single day. 30005 is not 30003 - waiting ' +
      'changes nothing, and each attempt costs.'];
  }

  return ['suspect',
    'one 30005. Permanent by definition, but one row is one row: confirm with ' +
    'Lookup line type intelligence before deleting a customer record.'];
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
    console.log(`no messages sent since ${since}`);
    return;
  }

  const rows = byRecipient(messages);
  if (rows.size === 0) {
    console.log(`no 30005 in ${messages.length} message(s) since ${since}`);
    return;
  }

  let confirmed = 0;
  for (const [to, row] of [...rows.entries()].sort()) {
    const [state, detail] = verdict(row);
    const line = `${state.padEnd(11)} ${to}  ${detail}`;
    if (state === 'recovered' || state === 'suspect') { console.log(line); continue; }
    confirmed += 1;
    console.warn(line);
    console.warn(`  message sids: ${row.sids.join(', ')}`);
    console.warn(`  repair: delete ${to} from your own contact table - Twilio has ` +
                 'no list to update - and gate new signups with GET ' +
                 `https://lookups.twilio.com/v2/PhoneNumbers/${to}` +
                 '?Fields=line_type_intelligence');
  }

  console.log(`30005 on ${rows.size} recipient(s) over ${days} day(s), ` +
              `${confirmed} confirmed dead`);
  process.exitCode = confirmed ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The day parser gets its own cases first, because it is where this silently breaks: an RFC 2822 timestamp sliced to ten characters produces the same string for every message ever sent, and every dead number then reads as a single anomaly. After that, the two cases that decide whether a contact is deleted: two failures on separate days is dead, and any delivery at all in the window overrides the failures completely.",
"test_py_file": "test_twilio_dead_number_audit.py",
"test_py": '''from twilio_dead_number_audit import by_recipient, day, error_code, verdict


def dead(sid, to="+15557770001", when="Fri, 21 Aug 2026 19:14:22 +0000"):
    return {"sid": sid, "to": to, "from": "+15550001111", "status": "undelivered",
            "error_code": 30005, "date_sent": when, "direction": "outbound-api"}


def test_error_code_reads_strings_and_numbers_the_same():
    assert error_code({"error_code": 30005}) == 30005
    assert error_code({"error_code": "30005"}) == 30005
    assert error_code({"error_code": None}) is None
    assert error_code({}) is None


def test_day_parses_the_rfc_2822_form_the_messages_list_actually_returns():
    # A ten-character slice of this gives "Fri, 21 A" for every message ever
    # sent, which is what makes the distinct-day rule fail silently.
    assert day("Fri, 21 Aug 2026 19:14:22 +0000") == "2026-08-21"
    assert day("Mon, 03 Aug 2026 01:02:03 +0000") == "2026-08-03"


def test_day_also_accepts_an_iso_timestamp():
    assert day("2026-08-21T19:14:22Z") == "2026-08-21"


def test_day_returns_none_rather_than_a_wrong_answer():
    assert day(None) is None
    assert day("") is None
    assert day("Fri, 21 Xxx 2026 19:14:22 +0000") is None


def test_by_recipient_dedupes_days_and_keeps_them_sorted():
    rows = by_recipient([
        dead("SM1", when="Fri, 21 Aug 2026 19:14:22 +0000"),
        dead("SM2", when="Fri, 21 Aug 2026 22:00:00 +0000"),
        dead("SM3", when="Mon, 03 Aug 2026 08:00:00 +0000"),
    ])
    assert rows["+15557770001"]["days"] == ["2026-08-03", "2026-08-21"]
    assert rows["+15557770001"]["dead"] == 3


def test_by_recipient_drops_numbers_with_no_30005_and_ignores_inbound():
    rows = by_recipient([
        {"sid": "SM1", "to": "+15557770002", "status": "delivered",
         "error_code": None, "direction": "outbound-api"},
        {"sid": "SM2", "to": "+15557770003", "direction": "inbound",
         "status": "received"},
    ])
    assert rows == {}


def test_two_failures_on_separate_days_is_a_dead_number():
    state, detail = verdict({"dead": 2, "delivered": 0,
                             "days": ["2026-08-03", "2026-08-21"]})
    assert state == "dead"
    assert "Delete it" in detail


def test_a_delivery_in_the_window_overrides_the_failures():
    # Carriers reissue disconnected numbers. Deleting on the strength of an old
    # 30005 is how a live customer stops hearing from you.
    state, detail = verdict({"dead": 3, "delivered": 1,
                             "days": ["2026-08-03", "2026-08-21"]})
    assert state == "recovered"
    assert "Keep this one" in detail


def test_repeats_inside_one_day_are_a_retry_loop_not_evidence():
    state, detail = verdict({"dead": 5, "delivered": 0, "days": ["2026-08-21"]})
    assert state == "retry-loop"
    assert "30005 is not 30003" in detail


def test_a_single_failure_is_only_a_suspect():
    state, detail = verdict({"dead": 1, "delivered": 0, "days": ["2026-08-21"]})
    assert state == "suspect"
    assert "Lookup" in detail


def test_no_failures_at_all_is_clean():
    state, _ = verdict({"dead": 0, "delivered": 4, "days": []})
    assert state == "clean"
''',
"test_js_file": "twilio-dead-number-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { byRecipient, day, errorCode, verdict }
  from './twilio-dead-number-audit.mjs';

const dead = (sid, to = '+15557770001', when = 'Fri, 21 Aug 2026 19:14:22 +0000') => ({
  sid, to, from: '+15550001111', status: 'undelivered', error_code: 30005,
  date_sent: when, direction: 'outbound-api',
});

test('error code reads strings and numbers the same', () => {
  assert.equal(errorCode({ error_code: 30005 }), 30005);
  assert.equal(errorCode({ error_code: '30005' }), 30005);
  assert.equal(errorCode({ error_code: null }), null);
  assert.equal(errorCode({}), null);
});

test('day parses the RFC 2822 form the Messages list actually returns', () => {
  // A ten-character slice gives "Fri, 21 A" for every message ever sent, which
  // is what makes the distinct-day rule fail silently.
  assert.equal(day('Fri, 21 Aug 2026 19:14:22 +0000'), '2026-08-21');
  assert.equal(day('Mon, 03 Aug 2026 01:02:03 +0000'), '2026-08-03');
});

test('day also accepts an ISO timestamp', () => {
  assert.equal(day('2026-08-21T19:14:22Z'), '2026-08-21');
});

test('day returns null rather than a wrong answer', () => {
  assert.equal(day(null), null);
  assert.equal(day(''), null);
  assert.equal(day('Fri, 21 Xxx 2026 19:14:22 +0000'), null);
});

test('byRecipient dedupes days and keeps them sorted', () => {
  const rows = byRecipient([
    dead('SM1', '+15557770001', 'Fri, 21 Aug 2026 19:14:22 +0000'),
    dead('SM2', '+15557770001', 'Fri, 21 Aug 2026 22:00:00 +0000'),
    dead('SM3', '+15557770001', 'Mon, 03 Aug 2026 08:00:00 +0000'),
  ]);
  assert.deepEqual(rows.get('+15557770001').days, ['2026-08-03', '2026-08-21']);
  assert.equal(rows.get('+15557770001').dead, 3);
});

test('byRecipient drops numbers with no 30005 and ignores inbound', () => {
  const rows = byRecipient([
    { sid: 'SM1', to: '+15557770002', status: 'delivered', error_code: null,
      direction: 'outbound-api' },
    { sid: 'SM2', to: '+15557770003', direction: 'inbound', status: 'received' },
  ]);
  assert.equal(rows.size, 0);
});

test('two failures on separate days is a dead number', () => {
  const [state, detail] = verdict({ dead: 2, delivered: 0,
                                    days: ['2026-08-03', '2026-08-21'] });
  assert.equal(state, 'dead');
  assert.match(detail, /Delete it/);
});

test('a delivery in the window overrides the failures', () => {
  const [state, detail] = verdict({ dead: 3, delivered: 1,
                                    days: ['2026-08-03', '2026-08-21'] });
  assert.equal(state, 'recovered');
  assert.match(detail, /Keep this one/);
});

test('repeats inside one day are a retry loop, not evidence', () => {
  const [state, detail] = verdict({ dead: 5, delivered: 0, days: ['2026-08-21'] });
  assert.equal(state, 'retry-loop');
  assert.match(detail, /30005 is not 30003/);
});

test('a single failure is only a suspect', () => {
  const [state, detail] = verdict({ dead: 1, delivered: 0, days: ['2026-08-21'] });
  assert.equal(state, 'suspect');
  assert.match(detail, /Lookup/);
});

test('no failures at all is clean', () => {
  const [state] = verdict({ dead: 0, delivered: 4, days: [] });
  assert.equal(state, 'clean');
});
''',
"faq": [
 ("Should I ever retry a message that failed with 30005?",
  "No. The carrier is saying it has no record of that number, and that answer does not change because you asked again ten minutes later. Every retry is accepted, priced and marked undelivered. The only thing worth doing is confirming the number with Lookup and removing it."),
 ("How do I tell 30005 apart from 30003 in my delivery handler?",
  "Switch on error_code, not on status. Both arrive as undelivered with an error code attached and are indistinguishable from the status alone. 30003 is transient and worth one retry; 30005 is permanent and worth a deletion. A handler written for one and reused for the other is the usual cause of the retry loop."),
 ("Why does the script want failures on two different days?",
  "Because several failures inside one day usually mean your own queue retried, which is one carrier answer counted five times. Two failures weeks apart are two independent answers. The window has to be wide enough to produce that evidence, which is why the default here is 30 days rather than 7."),
 ("Could a number that returned 30005 start working again?",
  "Yes, and that is why the delivered count is part of the verdict. US carriers reissue disconnected numbers to new subscribers, so a number that was unknown in March can be a real handset in August. Any delivery in the window overrides the failures and the contact is kept. Treat the new owner as a new contact, though, not as the old one."),
 ("Where do I delete the number, on Twilio or in my database?",
  "In your database. Twilio has no list of dead numbers to update and no resource to write, which is also why this script only reads. It prints which numbers to remove and the Lookup call to gate future signups with."),
],
"related": [
 ("/twilio/unreachable-destination-handset-30003/", "The transient version: error 30003"),
 ("/twilio/landline-destination-30006/", "SMS to landlines that can never receive it"),
 ("/twilio/deactivated-number-recycling/", "Recycled numbers sending OTPs to strangers"),
],
"citations": [CITE_30005, CITE_30003, CITE_MSG, CITE_LOOKUP],
},


{
"slug": "validity-period-expired-30036",
"title": "Error 30036: messages expire in the queue before they send",
"description": "A ValidityPeriod shorter than the real queue wait kills messages before their turn. 30045 and 30012 are the request-time cousins with a different fix.",
"h1": "error 30036: messages expire in the queue before they send",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30036", "twilio validity period expired",
             "twilio validityperiod", "twilio error 30045",
             "twilio message expired in queue"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The messages were accepted. They were never sent. <code>error_code</code> <code>30036</code> means the message sat in the sender's queue until its <code>ValidityPeriod</code> ran out and Twilio dropped it &mdash; a deadline your own code set, enforced against a queue whose depth your own code did not know.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and count rows where <code>error_code</code> is <code>30036</code> (expired in queue), <code>30045</code> (validity period outside 1&ndash;36,000 seconds) or <code>30012</code> (TTL below what the route accepts), bucketed by <code>messaging_service_sid</code> or <code>from</code>.</p>
<p>Then read the sender's cap: <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}</code> and look at <code>validity_period</code>. A service well under 36,000 with 30036s behind it is the cause. A service at the default with 30036s anyway means the deadline came from the send call &mdash; or the queue really is ten hours deep, which is a throughput problem wearing a TTL error code.</p>""",
"problem": """<p><code>ValidityPeriod</code> is a promise about time that gets set once, usually early, usually by someone reasoning about the message rather than about the queue. Five minutes sounds right for a one-time passcode: if it has not gone in five minutes it is useless anyway. That is true of the passcode and false of the mechanism, because the deadline is enforced from the moment Twilio accepts the message, not from the moment your sender is free.</p>
<p>So the failure only appears under load. At low volume the queue drains in a second and no deadline is ever reached. Then a campaign, a retry storm or a Monday morning puts four thousand messages in front of a long code that clears about one per second, and everything with a five-minute ceiling behind position three hundred dies without ever being transmitted. The API returned <code>201</code> for every one. The error arrives later, asynchronously, on messages your code already considers sent.</p>
<p>What makes it hard to read is that three different error codes describe three different moments. 30045 and 30012 are request-time rejections: nothing queued at all, and the fix is in the caller. 30036 is a queue timeout: the message queued, waited, and lost. Pooling them produces a count that points at no repair in particular.</p>""",
"why": """<p><strong>The deadline is measured against queue time, not send time.</strong> <code>ValidityPeriod</code> starts when Twilio accepts the message. Everything spent waiting for a sender to be free counts against it, which is exactly the interval your application has no visibility into.</p>
<p><strong>It can be set in two places and the lower one wins.</strong> A Messaging Service carries a <code>validity_period</code> for everything sent through it, and a send call can pass its own. Reading only the service explains half the findings; reading only the messages explains none of them.</p>
<p><strong>The default is 36,000 seconds, and that is not a safe answer either.</strong> Ten hours means a passcode can arrive long after the user gave up and requested three more. Raising the ceiling stops the 30036s and converts them into very late deliveries, which for time-critical traffic is worse. The right number depends on what the message is for.</p>
<p><strong>The Messages list cannot be filtered by error.</strong> No <code>ErrorCode</code> parameter and no <code>Status</code> parameter exist &mdash; only <code>To</code>, <code>From</code>, <code>DateSent</code> and paging. All three codes have to be counted client-side after paging the window.</p>""",
"steps": [
 {"h": "Page the Messages list and count the three codes separately",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. Keep 30036, 30045 and 30012 in three separate counters. They are three different moments in the send and they have three different repairs.</p>"""},
 {"h": "Bucket by the sender that owns the queue",
  "body": """<p>Use <code>messaging_service_sid</code> when it is set and <code>from</code> otherwise. The queue that filled up belongs to a sender, so an account-wide expiry count tells you nothing actionable; a per-sender rate tells you which pool is too narrow for its traffic.</p>"""},
 {"h": "Read validity_period off each Messaging Service",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}</code> for every <code>MG</code> bucket you found, and read <code>validity_period</code>. This is the one number that decides whether the deadline is a service setting somebody can change or a per-message argument in the sending code.</p>"""},
 {"h": "Handle 30045 and 30012 first, in the caller",
  "body": """<p>Neither of these ever reached a queue. 30045 means a <code>ValidityPeriod</code> outside the permitted 1 to 36,000 seconds &mdash; usually a unit mix-up, milliseconds where seconds were meant. 30012 means the TTL asked for is below what the route will accept. Both are fixed where the send is constructed, and both will keep firing no matter what you do to the service.</p>"""},
 {"h": "Match the deadline to the traffic, then widen the pool",
  "body": """<p><code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}</code> with a <code>ValidityPeriod</code> that suits the traffic &mdash; long for marketing, deliberately short for passcodes so a stale code fails rather than arrives. Then fix the actual cause by adding senders to the pool or rate-limiting the producer, because a deadline is only ever a symptom of a queue that is too long.</p>"""},
],
"verify": """<p>Re-run over the same window after the change. Every sender should read <code>clean</code>, and no sender should be in <code>out-of-range</code> or <code>ttl-too-small</code>.</p>
<pre><code class="language-bash">python3 twilio_validity_period_audit.py --days 7
# 3 sender(s) over 7 day(s), 0 with an expiry problem</code></pre>""",
"code_intro": "One paginated GET over the Messages list, plus one GET per Messaging Service that actually appears in the results &mdash; an API Key with read access covers both. The tally and the verdict are pure. The verdict's ordering is the interesting part: the request-time codes are checked before the queue-timeout code, because when both are present the caller is the thing to fix and the service setting is a distraction.",
"py_file": "twilio_validity_period_audit.py",
"py": '''"""Report Twilio messages that expired in the queue (30036) and the TTL rejections near it.

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
log = logging.getLogger("twilio_validity_period_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

EXPIRED = 30036         # queued past its ValidityPeriod and dropped
OUT_OF_RANGE = 30045    # ValidityPeriod outside 1..36000, rejected at request time
TTL_TOO_SMALL = 30012   # TTL below what the route accepts, rejected at request time

MAX_VALIDITY = 36000


def error_code(message):
    """Read error_code as an integer, or None.

    Null on healthy messages, a number on failed ones, and a string often enough
    that comparing the raw value against 30036 quietly reports nothing.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def tally(messages):
    """Bucket the three TTL codes by the sender whose queue they waited in.

    Pure, so the grouping can be tested without a network. The codes are kept
    apart rather than summed: 30045 and 30012 never reached a queue at all, so
    folding them into the expiry count produces a number that points at no
    particular repair.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        key = m.get("messaging_service_sid") or m.get("from") or "unknown sender"
        row = out.setdefault(key, {"total": 0, "expired": 0, "out_of_range": 0,
                                   "ttl_too_small": 0, "sids": []})
        row["total"] += 1
        code = error_code(m)
        if code == EXPIRED:
            row["expired"] += 1
        elif code == OUT_OF_RANGE:
            row["out_of_range"] += 1
        elif code == TTL_TOO_SMALL:
            row["ttl_too_small"] += 1
        else:
            continue
        if len(row["sids"]) < 3:
            row["sids"].append(m.get("sid"))
    return out


def verdict(stats, validity_period=None, floor=3600):
    """Classify one sender. Pure, so the ordering and the thresholds are visible.

    validity_period is the service-level cap in seconds, or None when the sender
    is a bare From number with no Messaging Service behind it.

    The request-time codes are checked first on purpose. When both kinds are
    present the caller is constructing bad sends, and changing the service
    setting fixes none of those.

    Returns (state, detail).
    """
    total = int(stats.get("total") or 0)
    expired = int(stats.get("expired") or 0)
    out_of_range = int(stats.get("out_of_range") or 0)
    ttl_too_small = int(stats.get("ttl_too_small") or 0)

    if out_of_range:
        return ("out-of-range",
                "%d message(s) rejected with 30045. ValidityPeriod has to be 1 to "
                "%d seconds and something is passing a value outside that, so "
                "those sends never entered a queue. Usually a unit mix-up: "
                "milliseconds where seconds were meant."
                % (out_of_range, MAX_VALIDITY))

    if ttl_too_small:
        return ("ttl-too-small",
                "%d message(s) rejected with 30012: the TTL asked for is below "
                "what the route will accept, so the send was refused before "
                "anything was queued. Fix it where the send is built."
                % ttl_too_small)

    if not expired:
        return ("clean", "%d message(s), none expired in queue" % total)

    rate = (expired / total) if total else 1.0

    if validity_period is not None and validity_period < floor:
        return ("service-too-low",
                "%d of %d expired with 30036 (%.1f%%) and this Messaging Service "
                "caps every message at %d second(s). The queue in front of these "
                "messages is deeper than that deadline, so they died waiting for "
                "a sender that was never going to be free in time."
                % (expired, total, rate * 100, validity_period))

    allowed = ("no service-level cap" if validity_period is None
               else "the service allows %d second(s)" % validity_period)
    return ("per-message",
            "%d of %d expired with 30036 (%.1f%%) while there is %s. The short "
            "deadline is coming from the send call itself, or the queue really is "
            "hours deep, which is a throughput problem wearing a TTL error code."
            % (expired, total, rate * 100, allowed))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. No Status or ErrorCode filter exists on this resource,
    so the date window and the page cap are the only bounds available."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def service_validity(session, service_sid):
    """Read validity_period off one Messaging Service, or None if it is not
    readable. A bare From number has no service and therefore no cap."""
    if not str(service_sid or "").startswith("MG"):
        return None
    svc = get(session, "%s/Services/%s" % (MESSAGING, service_sid))
    raw = svc.get("validity_period")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--floor", type=int, default=3600,
                    help="a service cap below this is treated as the cause")
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
        cap = service_validity(session, sender)
        state, detail = verdict(stats, cap, args.floor)
        line = "%-15s %s  %s" % (state, sender, detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
        if state in ("out-of-range", "ttl-too-small"):
            log.warning("  repair: fix the ValidityPeriod argument where the send "
                        "is constructed. It must be 1 to %d seconds, and no "
                        "service setting can rescue a rejected request.",
                        MAX_VALIDITY)
        elif state == "service-too-low":
            log.warning("  repair: raise the cap with a write to %s/Services/%s "
                        "(ValidityPeriod), then widen the sender pool so the "
                        "queue drains inside the new deadline.", MESSAGING, sender)
        else:
            log.warning("  repair: stop passing a short per-message "
                        "ValidityPeriod, and add senders to the pool or rate "
                        "limit the producer. The deadline is the symptom; the "
                        "queue length is the problem.")

    log.info("%d sender(s) over %d day(s), %d with an expiry problem",
             len(senders), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-validity-period-audit.mjs",
"js": '''/**
 * Report Twilio messages that expired in the queue (30036) and the TTL rejections
 * near it.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

const EXPIRED = 30036;        // queued past its ValidityPeriod and dropped
const OUT_OF_RANGE = 30045;   // ValidityPeriod outside 1..36000, rejected outright
const TTL_TOO_SMALL = 30012;  // TTL below what the route accepts, rejected outright

const MAX_VALIDITY = 36000;

/**
 * Read error_code as a number, or null. Null on healthy messages, a number on
 * failed ones, and a string often enough that comparing the raw value against
 * 30036 quietly reports nothing.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Bucket the three TTL codes by the sender whose queue they waited in. Pure, so
 * the grouping can be tested without a network. The codes are kept apart rather
 * than summed: 30045 and 30012 never reached a queue at all.
 */
export function tally(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const key = m.messaging_service_sid || m.from || 'unknown sender';
    if (!out.has(key)) {
      out.set(key, { total: 0, expired: 0, out_of_range: 0, ttl_too_small: 0,
                     sids: [] });
    }
    const row = out.get(key);
    row.total += 1;
    const code = errorCode(m);
    if (code === EXPIRED) row.expired += 1;
    else if (code === OUT_OF_RANGE) row.out_of_range += 1;
    else if (code === TTL_TOO_SMALL) row.ttl_too_small += 1;
    else continue;
    if (row.sids.length < 3) row.sids.push(m.sid);
  }
  return out;
}

/**
 * Classify one sender. Pure, so the ordering and the thresholds are visible.
 * validityPeriod is the service-level cap in seconds, or null for a bare From
 * number. The request-time codes are checked first on purpose: when both kinds
 * are present the caller is building bad sends and the service setting fixes
 * none of them. Returns [state, detail].
 */
export function verdict(stats, validityPeriod = null, floor = 3600) {
  const total = Number(stats.total ?? 0);
  const expired = Number(stats.expired ?? 0);
  const outOfRange = Number(stats.out_of_range ?? 0);
  const ttlTooSmall = Number(stats.ttl_too_small ?? 0);

  if (outOfRange) {
    return ['out-of-range',
      `${outOfRange} message(s) rejected with 30045. ValidityPeriod has to be 1 ` +
      `to ${MAX_VALIDITY} seconds and something is passing a value outside that, ` +
      'so those sends never entered a queue. Usually a unit mix-up: milliseconds ' +
      'where seconds were meant.'];
  }

  if (ttlTooSmall) {
    return ['ttl-too-small',
      `${ttlTooSmall} message(s) rejected with 30012: the TTL asked for is below ` +
      'what the route will accept, so the send was refused before anything was ' +
      'queued. Fix it where the send is built.'];
  }

  if (!expired) return ['clean', `${total} message(s), none expired in queue`];

  const rate = total ? expired / total : 1;
  const pct = (rate * 100).toFixed(1);

  if (validityPeriod !== null && validityPeriod !== undefined
      && validityPeriod < floor) {
    return ['service-too-low',
      `${expired} of ${total} expired with 30036 (${pct}%) and this Messaging ` +
      `Service caps every message at ${validityPeriod} second(s). The queue in ` +
      'front of these messages is deeper than that deadline, so they died ' +
      'waiting for a sender that was never going to be free in time.'];
  }

  const allowed = (validityPeriod === null || validityPeriod === undefined)
    ? 'no service-level cap'
    : `the service allows ${validityPeriod} second(s)`;
  return ['per-message',
    `${expired} of ${total} expired with 30036 (${pct}%) while there is ${allowed}. ` +
    'The short deadline is coming from the send call itself, or the queue really ' +
    'is hours deep, which is a throughput problem wearing a TTL error code.'];
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

async function serviceValidity(auth, serviceSid) {
  if (!String(serviceSid ?? '').startsWith('MG')) return null;
  const svc = await get(auth, `${MESSAGING}/Services/${serviceSid}`);
  const n = Number(svc.validity_period);
  return Number.isFinite(n) ? n : null;
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
    const cap = await serviceValidity(auth, sender);
    const [state, detail] = verdict(stats, cap);
    const line = `${state.padEnd(15)} ${sender}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  message sids: ${stats.sids.join(', ')}`);
    if (state === 'out-of-range' || state === 'ttl-too-small') {
      console.warn('  repair: fix the ValidityPeriod argument where the send is ' +
                   `constructed. It must be 1 to ${MAX_VALIDITY} seconds, and no ` +
                   'service setting can rescue a rejected request.');
    } else if (state === 'service-too-low') {
      console.warn(`  repair: raise the cap with a write to ${MESSAGING}/Services/` +
                   `${sender} (ValidityPeriod), then widen the sender pool so the ` +
                   'queue drains inside the new deadline.');
    } else {
      console.warn('  repair: stop passing a short per-message ValidityPeriod, ' +
                   'and add senders to the pool or rate limit the producer. The ' +
                   'deadline is the symptom; the queue length is the problem.');
    }
  }

  console.log(`${senders.size} sender(s) over ${days} day(s), ${bad} with an ` +
              'expiry problem');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Precedence is the thing worth pinning. A sender with both a 30045 and fifty 30036s reports <code>out-of-range</code>, not <code>service-too-low</code>, because the rejected sends never queued and no service change touches them. After that, the same expiry count reads two different ways depending on one number read from a different API: a 300-second service cap makes it the service's fault, the 36,000-second default makes it the send call's or the pool's.",
"test_py_file": "test_twilio_validity_period_audit.py",
"test_py": '''from twilio_validity_period_audit import error_code, tally, verdict


def msg(sid, code=None, sender="+15550001111"):
    return {"sid": sid, "from": sender, "status": "undelivered",
            "error_code": code, "direction": "outbound-api"}


def test_error_code_reads_strings_and_numbers_the_same():
    assert error_code({"error_code": 30036}) == 30036
    assert error_code({"error_code": "30036"}) == 30036
    assert error_code({"error_code": None}) is None
    assert error_code({}) is None


def test_tally_keeps_the_three_codes_apart():
    rows = tally([msg("SM1", 30036), msg("SM2", 30045), msg("SM3", 30012),
                  msg("SM4")])
    row = rows["+15550001111"]
    assert row["total"] == 4
    assert row["expired"] == 1
    assert row["out_of_range"] == 1
    assert row["ttl_too_small"] == 1


def test_tally_groups_on_the_messaging_service_when_there_is_one():
    m = msg("SM1", 30036)
    m["messaging_service_sid"] = "MG1"
    rows = tally([m])
    assert set(rows) == {"MG1"}


def test_tally_ignores_inbound_and_caps_the_sids():
    rows = tally([msg("SM%d" % i, 30036) for i in range(7)]
                 + [{"sid": "SM9", "direction": "inbound", "status": "received"}])
    assert rows["+15550001111"]["sids"] == ["SM0", "SM1", "SM2"]
    assert len(rows) == 1


def test_no_expiries_is_clean():
    state, detail = verdict({"total": 400, "expired": 0})
    assert state == "clean"
    assert "400" in detail


def test_a_request_time_rejection_outranks_the_queue_timeout():
    # 30045 never queued, so the service cap is irrelevant to it. Reporting
    # service-too-low here would send someone to change the wrong setting.
    state, detail = verdict({"total": 100, "expired": 50, "out_of_range": 1},
                            validity_period=300)
    assert state == "out-of-range"
    assert "36000" in detail


def test_a_ttl_below_the_route_minimum_is_its_own_state():
    state, detail = verdict({"total": 100, "expired": 50, "ttl_too_small": 2},
                            validity_period=300)
    assert state == "ttl-too-small"
    assert "before anything was queued" in detail


def test_a_low_service_cap_behind_expiries_is_the_cause():
    state, detail = verdict({"total": 100, "expired": 40}, validity_period=300)
    assert state == "service-too-low"
    assert "300 second(s)" in detail


def test_expiries_at_the_default_cap_point_at_the_send_call_or_the_queue():
    state, detail = verdict({"total": 100, "expired": 40}, validity_period=36000)
    assert state == "per-message"
    assert "throughput problem" in detail


def test_a_bare_from_number_has_no_service_cap_to_blame():
    state, detail = verdict({"total": 100, "expired": 40}, validity_period=None)
    assert state == "per-message"
    assert "no service-level cap" in detail
''',
"test_js_file": "twilio-validity-period-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { errorCode, tally, verdict } from './twilio-validity-period-audit.mjs';

const msg = (sid, code = null, sender = '+15550001111') => ({
  sid, from: sender, status: 'undelivered', error_code: code,
  direction: 'outbound-api',
});

test('error code reads strings and numbers the same', () => {
  assert.equal(errorCode({ error_code: 30036 }), 30036);
  assert.equal(errorCode({ error_code: '30036' }), 30036);
  assert.equal(errorCode({ error_code: null }), null);
  assert.equal(errorCode({}), null);
});

test('tally keeps the three codes apart', () => {
  const rows = tally([msg('SM1', 30036), msg('SM2', 30045), msg('SM3', 30012),
                      msg('SM4')]);
  const row = rows.get('+15550001111');
  assert.equal(row.total, 4);
  assert.equal(row.expired, 1);
  assert.equal(row.out_of_range, 1);
  assert.equal(row.ttl_too_small, 1);
});

test('tally groups on the messaging service when there is one', () => {
  const rows = tally([{ ...msg('SM1', 30036), messaging_service_sid: 'MG1' }]);
  assert.deepEqual([...rows.keys()], ['MG1']);
});

test('tally ignores inbound and caps the sids', () => {
  const rows = tally([
    ...[0, 1, 2, 3, 4, 5, 6].map((i) => msg(`SM${i}`, 30036)),
    { sid: 'SM9', direction: 'inbound', status: 'received' },
  ]);
  assert.deepEqual(rows.get('+15550001111').sids, ['SM0', 'SM1', 'SM2']);
  assert.equal(rows.size, 1);
});

test('no expiries is clean', () => {
  const [state, detail] = verdict({ total: 400, expired: 0 });
  assert.equal(state, 'clean');
  assert.match(detail, /400/);
});

test('a request-time rejection outranks the queue timeout', () => {
  // 30045 never queued, so the service cap is irrelevant to it.
  const [state, detail] = verdict(
    { total: 100, expired: 50, out_of_range: 1 }, 300);
  assert.equal(state, 'out-of-range');
  assert.match(detail, /36000/);
});

test('a TTL below the route minimum is its own state', () => {
  const [state, detail] = verdict(
    { total: 100, expired: 50, ttl_too_small: 2 }, 300);
  assert.equal(state, 'ttl-too-small');
  assert.match(detail, /before anything was queued/);
});

test('a low service cap behind expiries is the cause', () => {
  const [state, detail] = verdict({ total: 100, expired: 40 }, 300);
  assert.equal(state, 'service-too-low');
  assert.match(detail, /300 second\\(s\\)/);
});

test('expiries at the default cap point at the send call or the queue', () => {
  const [state, detail] = verdict({ total: 100, expired: 40 }, 36000);
  assert.equal(state, 'per-message');
  assert.match(detail, /throughput problem/);
});

test('a bare From number has no service cap to blame', () => {
  const [state, detail] = verdict({ total: 100, expired: 40}, null);
  assert.equal(state, 'per-message');
  assert.match(detail, /no service-level cap/);
});
''',
"faq": [
 ("What exactly does ValidityPeriod measure?",
  "The time from Twilio accepting the message to the message being handed to the carrier. Queue time counts against it in full. That is why a five-minute value looks safe in testing, where the queue is empty, and starts killing messages the first time a campaign puts a few thousand segments in front of a one-per-second long code."),
 ("Should I just set ValidityPeriod to the maximum?",
  "Only for traffic where a late delivery is still worth something. 36,000 seconds is ten hours, so a passcode can arrive long after the user gave up and requested three more codes. For time-critical messages a short period is correct and the 30036s are telling you the queue is too long, not that the deadline is too short."),
 ("How is 30036 different from 30045 and 30012?",
  "30036 happens after the message queued and waited. 30045 and 30012 happen at request time: the first means the ValidityPeriod is outside the permitted 1 to 36,000 seconds, the second that the TTL is below what the route accepts. Neither of those messages was ever queued, so no service setting will change the outcome. Fix them where the send is constructed."),
 ("Where does the deadline come from if the service is set to 36,000?",
  "The send call. A per-message ValidityPeriod overrides the service, so a service at the default with expiries behind it means the short value is in your sending code. If it is not there either, the queue genuinely is ten hours deep and the finding is a throughput problem, not a TTL one."),
 ("Does the script change my Messaging Service?",
  "No. It reads validity_period from the service and prints the write you would run yourself. Everything it issues is a GET, which is why an API Key with read access is enough and is what you should give it."),
],
"related": [
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never reach a final state"),
 ("/twilio/messaging-queue-overflow-30001/", "Queue overflow when sends outrun throughput"),
 ("/twilio/ucs2-segment-inflation/", "One emoji tripling your segment count"),
],
"citations": [CITE_30036, CITE_30045, CITE_SERVICE, CITE_QUEUE],
},


{
"slug": "mms-content-size-exceeds-carrier-30019",
"title": "Error 30019: the MMS is too big for the carrier, not for Twilio",
"description": "Twilio accepts 5 MB and carriers stop between 300 KB and 3.5 MB, so the same image delivers to one recipient and fails for the next with error 30019.",
"h1": "error 30019: the MMS is too big for the carrier, not for Twilio",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30019", "content size exceeds carrier limit",
             "twilio mms size limit", "twilio mms 600kb",
             "twilio mms not delivered"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The image sends fine to your own phone. It sends fine to two of the three people who tested it. To the fourth it comes back <code>undelivered</code> with <code>error_code</code> <code>30019</code>, content size exceeds carrier limit &mdash; and the file has not changed. Twilio's ceiling and the carrier's ceiling are different numbers, an order of magnitude apart, and only one of them rejects you up front.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and keep rows where <code>error_code</code> is <code>30019</code> and <code>num_media</code> is greater than zero. Read <code>num_media</code> as an integer &mdash; the 2010-04-01 API returns it as a string.</p>
<p>Then name the offending file: <code>GET /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}/Media.json</code> gives you the media list and each <code>content_type</code>, but <strong>no size field</strong>. The bytes have to be measured separately, with a streamed <code>GET</code> whose <code>Content-Length</code> you read and whose body you never download.</p>""",
"problem": """<p>Two ceilings apply to every MMS and they are not close together. Twilio accepts up to 5 MB of body plus attachments and will take your 4 MB photograph without complaint. The carrier on the other end stops somewhere between roughly 300 KB and 3.5 MB depending on the network &mdash; AT&amp;T short-code MMS caps at 600 KB &mdash; and there is no way to ask in advance which ceiling a given destination number sits under.</p>
<p>So the failure is per-recipient, which is the worst shape it could take for debugging. The developer sends to their own handset on a tier-one carrier, it arrives, and the ticket is closed. It arrives for most of the recipient list too. The complaints come from whichever subset happens to be on the networks with the low ceiling, they are a minority, they are geographically scattered, and nothing about them correlates with anything except the carrier &mdash; a field you do not have.</p>
<p>Meanwhile the media is usually not the size anyone assumes. A photograph straight from a phone camera is three to five megabytes; a designer's export at 2x for retina is not far behind. Nobody looked, because nothing in the send pipeline ever mentions the size and Twilio accepted it.</p>""",
"why": """<p><strong>Twilio's limit is not the limit that matters.</strong> 5 MB gets your request accepted. The carrier's ceiling is enforced later, asynchronously, per destination, and that is where 30019 comes from. Passing the Twilio check tells you nothing about delivery.</p>
<p><strong>The Media resource has no size field.</strong> <code>Media.json</code> returns the SID, the <code>content_type</code> and the URIs. It does not return a byte count, so the only way to know how big the file actually is is to fetch its headers &mdash; which is a separate request nobody makes by default.</p>
<p><strong><code>num_media</code> is a string.</strong> The 2010-04-01 API returns <code>"1"</code>, not <code>1</code>. A truthiness test happens to work; an arithmetic comparison against zero does not, and <code>"0"</code> is truthy, so the naive filter keeps every SMS in the account and reports an MMS problem across traffic that has no media at all.</p>
<p><strong>The Messages list cannot be filtered by error.</strong> No <code>ErrorCode</code> and no <code>Status</code> parameter exist on the resource. Finding 30019 means paging the window and filtering client-side, which is why nobody has this number to hand when the complaints start.</p>""",
"steps": [
 {"h": "Page the Messages list and keep only real MMS",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. Coerce <code>num_media</code> to an integer and drop anything at zero before counting anything, or the denominator includes every SMS you sent and the MMS failure rate comes out as a rounding error.</p>"""},
 {"h": "Compute the failure rate per sender, not per account",
  "body": """<p>Bucket on <code>messaging_service_sid</code> or <code>from</code> and divide 30019s by MMS sends. Above about half means the media is over even the tier-one ceiling and nobody is receiving it. Below that is the carrier-dependent case, which is the one that produces the confusing partial complaints.</p>"""},
 {"h": "Name the file from the Media subresource",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}/Media.json</code> lists each attachment with its <code>content_type</code>. Check the type while you are there: Twilio transcodes <code>image/jpeg</code>, <code>image/png</code> and <code>image/gif</code>, and anything else is passed through untouched at whatever size it was.</p>"""},
 {"h": "Measure the bytes without downloading them",
  "body": """<p>The Media resource carries no size, so issue a streamed <code>GET</code> against the media URI, read <code>Content-Length</code> from the response headers and close the connection before the body transfers. Some media hosts answer <code>HEAD</code> badly or not at all, which is why this is a <code>GET</code> that is abandoned rather than a <code>HEAD</code>.</p>"""},
 {"h": "Recompress under 600 KB and turn on the converter",
  "body": """<p>600 KB is the conservative target: under the AT&amp;T short-code cap and under every published carrier ceiling. Recompress at the source, serve only jpeg, png or gif, and enable the MMS Converter on the Messaging Service so Twilio downsizes what slips through. The script prints that change; it does not make it.</p>"""},
],
"verify": """<p>Re-run over the same window once the media has been recompressed. Every sender should read <code>clean</code>, and every probed file should be <code>safe</code>.</p>
<pre><code class="language-bash">python3 twilio_mms_size_audit.py --days 7 --probe-size
# 2 sender(s) over 7 day(s), 0 with a 30019 problem</code></pre>""",
"code_intro": "GET requests throughout, including the size probe &mdash; a streamed <code>GET</code> whose headers are read and whose body is discarded &mdash; so an API Key with read access is enough. Three pure functions: the <code>num_media</code> coercion, the per-sender tally, and the size ladder. The ladder is the piece worth having in one readable place, because those thresholds are carrier facts rather than opinions and they are the whole explanation for why the same file delivers to one person and not the next.",
"py_file": "twilio_mms_size_audit.py",
"py": '''"""Report Twilio MMS rejected by the carrier for size (30019), and how big the media is.

Read only. GET requests and nothing else, including the size probe: give this an
API Key with read access rather than the account auth token. The repair is
printed, never performed, because this script holds a credential to an account
that can send messages and spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_mms_size_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

OVERSIZE = 30019

# Carrier ceilings, not Twilio's. Twilio accepts 5 MB of body plus attachments;
# the networks stop far earlier and each at its own number, which is the entire
# reason one file delivers to one handset and 30019s on the next.
SAFE_BYTES = 300000        # under every published carrier ceiling
CARRIER_FLOOR = 600000     # AT&T short-code MMS stops here
TIER_ONE = 3500000         # about as far as the most generous networks go
TWILIO_MAX = 5000000       # body plus attachments, enforced by Twilio itself

TRANSCODED = ("image/jpeg", "image/png", "image/gif")


def error_code(message):
    """Read error_code as an integer, or None. Null on healthy messages, a number
    on failed ones, and a string often enough to matter."""
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def media_count(message):
    """Read num_media as an integer. Pure, and less trivial than it looks.

    The 2010-04-01 API returns num_media as a string: "0" for an SMS, "1" for a
    one-image MMS. "0" is truthy, so a plain truthiness test keeps every SMS in
    the account and the MMS failure rate comes out divided by the wrong
    denominator.
    """
    raw = message.get("num_media")
    if raw is None or raw == "":
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def mms_tally(messages):
    """Bucket MMS sends and their 30019s by sender. Pure, so the denominator
    rule can be tested without a network. Messages with no media never enter
    the count at all."""
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        if media_count(m) <= 0:
            continue
        key = m.get("messaging_service_sid") or m.get("from") or "unknown sender"
        row = out.setdefault(key, {"mms": 0, "oversize": 0, "sids": []})
        row["mms"] += 1
        if error_code(m) == OVERSIZE:
            row["oversize"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
    return out


def size_verdict(content_length):
    """Place a media file on the carrier ceiling ladder. Pure, so the thresholds
    are readable and arguable rather than buried in a request loop.

    Returns (state, detail).
    """
    if content_length is None or content_length == "":
        return ("unknown",
                "the media host returned no Content-Length, so the size is not "
                "knowable from the headers. Check the object at its source.")
    try:
        n = int(content_length)
    except (TypeError, ValueError):
        return ("unknown",
                "Content-Length was not a number, so the size is not knowable "
                "from the headers. Check the object at its source.")

    kb = n / 1000.0

    if n <= SAFE_BYTES:
        return ("safe", "%.0f kB, under every published carrier ceiling." % kb)

    if n <= CARRIER_FLOOR:
        return ("at-risk",
                "%.0f kB. Inside Twilio's limit and right at the conservative "
                "carrier floor: AT&T short-code MMS stops at 600 kB." % kb)

    if n <= TIER_ONE:
        return ("carrier-dependent",
                "%.0f kB. Tier-one carriers take up to about 3.5 MB while many "
                "others stop between 300 and 600 kB. This is the exact band "
                "where one recipient gets the image and the next gets 30019."
                % kb)

    if n <= TWILIO_MAX:
        return ("over-carriers",
                "%.0f kB. Under Twilio's 5 MB ceiling for body plus attachments "
                "and over every carrier ceiling: 30019 on all of them." % kb)

    return ("over-twilio",
            "%.0f kB, past Twilio's own 5 MB ceiling for body plus attachments."
            % kb)


def sender_verdict(stats):
    """Classify one sender's MMS traffic. Pure. Returns (state, detail)."""
    mms = int(stats.get("mms") or 0)
    over = int(stats.get("oversize") or 0)

    if not mms:
        return ("no-mms", "no MMS from this sender in the window")

    if not over:
        return ("clean", "%d MMS, none rejected for size" % mms)

    rate = over / mms

    if rate >= 0.5:
        return ("every-carrier",
                "%d of %d MMS rejected with 30019 (%.1f%%). At that rate the "
                "media is over the tier-one ceiling too, so nobody is receiving "
                "it." % (over, mms, rate * 100))

    return ("carrier-dependent",
            "%d of %d MMS rejected with 30019 (%.1f%%). It delivers on the "
            "networks with the higher ceiling and fails on the rest, which is "
            "why it works on the phone in your hand."
            % (over, mms, rate * 100))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. No Status or ErrorCode filter exists on this resource,
    so the date window and the page cap are the only bounds available."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def media_for(session, account, message_sid):
    """List the attachments on one message. Media.json carries the content_type
    but no byte count, which is why the size needs its own request."""
    page = get(session, "%s/Accounts/%s/Messages/%s/Media.json"
               % (BASE, account, message_sid))
    return page.get("media_list", [])


def probe_size(session, media_uri):
    """Read Content-Length without downloading the file.

    A streamed GET whose body is never read and whose connection is closed
    immediately. HEAD would be tidier, but media is often served from object
    storage behind a redirect that answers HEAD inconsistently, and a GET that is
    abandoned costs the same and always works.
    """
    url = HOST + str(media_uri or "").replace(".json", "")
    r = session.get(url, stream=True, timeout=30, allow_redirects=True)
    try:
        if not r.ok:
            return None
        return r.headers.get("Content-Length")
    finally:
        r.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--probe-size", action="store_true",
                    help="read Content-Length on the media of each flagged "
                         "message; one extra GET per attachment, body discarded")
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

    senders = mms_tally(messages)
    if not senders:
        log.info("no MMS in %d message(s) since %s", len(messages), since)
        return 0

    bad = 0
    for sender, stats in sorted(senders.items()):
        state, detail = sender_verdict(stats)
        line = "%-18s %s  %s" % (state, sender, detail)
        if state in ("clean", "no-mms"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))

        if args.probe_size:
            for sid in stats["sids"]:
                for item in media_for(session, account, sid):
                    ctype = item.get("content_type") or "unknown type"
                    mstate, mdetail = size_verdict(probe_size(session,
                                                              item.get("uri")))
                    log.warning("  %s %-18s %s  %s", sid, mstate, ctype, mdetail)
                    if ctype not in TRANSCODED:
                        log.warning("    %s is not transcoded by Twilio: it goes "
                                    "to the carrier at whatever size it is.",
                                    ctype)

        log.warning("  repair: recompress the media under 600 kB, serve it as "
                    "jpeg, png or gif, and enable the MMS Converter on the "
                    "Messaging Service (MmsConverter) so what slips through is "
                    "downsized.")

    log.info("%d sender(s) over %d day(s), %d with a 30019 problem",
             len(senders), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-mms-size-audit.mjs",
"js": '''/**
 * Report Twilio MMS rejected by the carrier for size (30019), and how big the
 * media is.
 *
 * Read only. GET requests and nothing else, including the size probe: give this
 * an API Key with read access rather than the account auth token. The repair is
 * printed, never performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const OVERSIZE = 30019;

// Carrier ceilings, not Twilio's. Twilio accepts 5 MB of body plus attachments;
// the networks stop far earlier and each at its own number, which is the entire
// reason one file delivers to one handset and 30019s on the next.
const SAFE_BYTES = 300000;      // under every published carrier ceiling
const CARRIER_FLOOR = 600000;   // AT&T short-code MMS stops here
const TIER_ONE = 3500000;       // about as far as the most generous networks go
const TWILIO_MAX = 5000000;     // body plus attachments, enforced by Twilio

const TRANSCODED = ['image/jpeg', 'image/png', 'image/gif'];

/**
 * Read error_code as a number, or null. Null on healthy messages, a number on
 * failed ones, and a string often enough to matter.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Read num_media as an integer. Pure, and less trivial than it looks: the
 * 2010-04-01 API returns it as a string, and "0" is truthy, so a plain
 * truthiness test keeps every SMS in the account and divides the MMS failure
 * rate by the wrong denominator.
 */
export function mediaCount(message) {
  const raw = message.num_media;
  if (raw === null || raw === undefined || raw === '') return 0;
  const n = Number(raw);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Bucket MMS sends and their 30019s by sender. Pure, so the denominator rule can
 * be tested without a network. Messages with no media never enter the count.
 */
export function mmsTally(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    if (mediaCount(m) <= 0) continue;
    const key = m.messaging_service_sid || m.from || 'unknown sender';
    if (!out.has(key)) out.set(key, { mms: 0, oversize: 0, sids: [] });
    const row = out.get(key);
    row.mms += 1;
    if (errorCode(m) === OVERSIZE) {
      row.oversize += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
    }
  }
  return out;
}

/**
 * Place a media file on the carrier ceiling ladder. Pure, so the thresholds are
 * readable and arguable. Returns [state, detail].
 */
export function sizeVerdict(contentLength) {
  if (contentLength === null || contentLength === undefined || contentLength === '') {
    return ['unknown',
      'the media host returned no Content-Length, so the size is not knowable ' +
      'from the headers. Check the object at its source.'];
  }
  const n = Number(contentLength);
  if (!Number.isFinite(n)) {
    return ['unknown',
      'Content-Length was not a number, so the size is not knowable from the ' +
      'headers. Check the object at its source.'];
  }

  const kb = (n / 1000).toFixed(0);

  if (n <= SAFE_BYTES) {
    return ['safe', `${kb} kB, under every published carrier ceiling.`];
  }

  if (n <= CARRIER_FLOOR) {
    return ['at-risk',
      `${kb} kB. Inside Twilio's limit and right at the conservative carrier ` +
      'floor: AT&T short-code MMS stops at 600 kB.'];
  }

  if (n <= TIER_ONE) {
    return ['carrier-dependent',
      `${kb} kB. Tier-one carriers take up to about 3.5 MB while many others ` +
      'stop between 300 and 600 kB. This is the exact band where one recipient ' +
      'gets the image and the next gets 30019.'];
  }

  if (n <= TWILIO_MAX) {
    return ['over-carriers',
      `${kb} kB. Under Twilio's 5 MB ceiling for body plus attachments and over ` +
      'every carrier ceiling: 30019 on all of them.'];
  }

  return ['over-twilio',
    `${kb} kB, past Twilio's own 5 MB ceiling for body plus attachments.`];
}

/**
 * Classify one sender's MMS traffic. Pure. Returns [state, detail].
 */
export function senderVerdict(stats) {
  const mms = Number(stats.mms ?? 0);
  const over = Number(stats.oversize ?? 0);

  if (!mms) return ['no-mms', 'no MMS from this sender in the window'];
  if (!over) return ['clean', `${mms} MMS, none rejected for size`];

  const rate = over / mms;
  const pct = (rate * 100).toFixed(1);

  if (rate >= 0.5) {
    return ['every-carrier',
      `${over} of ${mms} MMS rejected with 30019 (${pct}%). At that rate the ` +
      'media is over the tier-one ceiling too, so nobody is receiving it.'];
  }

  return ['carrier-dependent',
    `${over} of ${mms} MMS rejected with 30019 (${pct}%). It delivers on the ` +
    'networks with the higher ceiling and fails on the rest, which is why it ' +
    'works on the phone in your hand.'];
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

/**
 * Read Content-Length without downloading the file: a GET whose body stream is
 * cancelled as soon as the headers are in. Media often sits behind a redirect to
 * object storage that answers HEAD inconsistently, so an abandoned GET is the
 * reliable read.
 */
async function probeSize(auth, mediaUri) {
  const url = HOST + String(mediaUri ?? '').replace('.json', '');
  const res = await fetch(url, { headers: { Authorization: auth } });
  const len = res.ok ? res.headers.get('content-length') : null;
  if (res.body) await res.body.cancel();
  return len;
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
  const probe = process.argv.includes('--probe-size');

  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  const senders = mmsTally(messages);
  if (senders.size === 0) {
    console.log(`no MMS in ${messages.length} message(s) since ${since}`);
    return;
  }

  let bad = 0;
  for (const [sender, stats] of [...senders.entries()].sort()) {
    const [state, detail] = senderVerdict(stats);
    const line = `${state.padEnd(18)} ${sender}  ${detail}`;
    if (state === 'clean' || state === 'no-mms') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  message sids: ${stats.sids.join(', ')}`);

    if (probe) {
      for (const sid of stats.sids) {
        const page = await get(auth,
          `${BASE}/Accounts/${account}/Messages/${sid}/Media.json`);
        for (const item of page.media_list ?? []) {
          const ctype = item.content_type || 'unknown type';
          const [mstate, mdetail] = sizeVerdict(await probeSize(auth, item.uri));
          console.warn(`  ${sid} ${mstate.padEnd(18)} ${ctype}  ${mdetail}`);
          if (!TRANSCODED.includes(ctype)) {
            console.warn(`    ${ctype} is not transcoded by Twilio: it goes to ` +
                         'the carrier at whatever size it is.');
          }
        }
      }
    }

    console.warn('  repair: recompress the media under 600 kB, serve it as jpeg, ' +
                 'png or gif, and enable the MMS Converter on the Messaging ' +
                 'Service (MmsConverter) so what slips through is downsized.');
  }

  console.log(`${senders.size} sender(s) over ${days} day(s), ${bad} with a ` +
              '30019 problem');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The ladder is tested on its boundaries, because every one of those numbers is a claim about a carrier and an off-by-one turns a safe file into an at-risk one in the report. The <code>num_media</code> cases matter just as much: <code>\"0\"</code> arriving as a string is truthy, and a tally that believes it counts every SMS in the account as an MMS send and divides the failure rate into nothing.",
"test_py_file": "test_twilio_mms_size_audit.py",
"test_py": '''from twilio_mms_size_audit import (error_code, media_count, mms_tally,
                                   sender_verdict, size_verdict)


def mms(sid, code=None, media="1", sender="+15550001111"):
    return {"sid": sid, "from": sender, "status": "undelivered",
            "error_code": code, "num_media": media, "direction": "outbound-api"}


def test_error_code_reads_strings_and_numbers_the_same():
    assert error_code({"error_code": 30019}) == 30019
    assert error_code({"error_code": "30019"}) == 30019
    assert error_code({}) is None


def test_num_media_arrives_as_a_string_and_zero_is_truthy():
    # The whole reason this is a function: "0" is a truthy string, so a
    # truthiness test counts every SMS in the account as an MMS.
    assert media_count({"num_media": "0"}) == 0
    assert media_count({"num_media": "1"}) == 1
    assert media_count({"num_media": 2}) == 2
    assert media_count({}) == 0
    assert media_count({"num_media": "not a number"}) == 0


def test_tally_counts_only_messages_that_carry_media():
    rows = mms_tally([mms("SM1", 30019), mms("SM2"), mms("SM3", media="0"),
                      {"sid": "SM4", "direction": "inbound", "num_media": "1"}])
    assert rows["+15550001111"] == {"mms": 2, "oversize": 1, "sids": ["SM1"]}


def test_tally_groups_on_the_messaging_service_when_there_is_one():
    m = mms("SM1", 30019)
    m["messaging_service_sid"] = "MG1"
    assert set(mms_tally([m])) == {"MG1"}


def test_the_size_ladder_holds_at_every_boundary():
    assert size_verdict(300000)[0] == "safe"
    assert size_verdict(300001)[0] == "at-risk"
    assert size_verdict(600000)[0] == "at-risk"
    assert size_verdict(600001)[0] == "carrier-dependent"
    assert size_verdict(3500000)[0] == "carrier-dependent"
    assert size_verdict(3500001)[0] == "over-carriers"
    assert size_verdict(5000000)[0] == "over-carriers"
    assert size_verdict(5000001)[0] == "over-twilio"


def test_the_ladder_takes_content_length_as_the_string_a_header_is():
    state, detail = size_verdict("4200000")
    assert state == "over-carriers"
    assert "4200 kB" in detail


def test_a_missing_or_unparseable_content_length_is_unknown_not_safe():
    assert size_verdict(None)[0] == "unknown"
    assert size_verdict("")[0] == "unknown"
    assert size_verdict("chunked")[0] == "unknown"


def test_the_carrier_dependent_band_explains_the_partial_failures():
    _, detail = size_verdict(1200000)
    assert "one recipient gets the image and the next gets 30019" in detail


def test_a_sender_with_no_failures_is_clean():
    state, detail = sender_verdict({"mms": 40, "oversize": 0})
    assert state == "clean"
    assert "40" in detail


def test_most_of_the_mms_failing_means_no_carrier_takes_it():
    state, detail = sender_verdict({"mms": 10, "oversize": 8})
    assert state == "every-carrier"
    assert "nobody is receiving it" in detail


def test_a_minority_failing_is_the_carrier_dependent_case():
    state, detail = sender_verdict({"mms": 100, "oversize": 12})
    assert state == "carrier-dependent"
    assert "phone in your hand" in detail


def test_a_sender_with_no_mms_at_all_says_so():
    state, _ = sender_verdict({"mms": 0, "oversize": 0})
    assert state == "no-mms"
''',
"test_js_file": "twilio-mms-size-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { errorCode, mediaCount, mmsTally, senderVerdict, sizeVerdict }
  from './twilio-mms-size-audit.mjs';

const mms = (sid, code = null, media = '1', sender = '+15550001111') => ({
  sid, from: sender, status: 'undelivered', error_code: code, num_media: media,
  direction: 'outbound-api',
});

test('error code reads strings and numbers the same', () => {
  assert.equal(errorCode({ error_code: 30019 }), 30019);
  assert.equal(errorCode({ error_code: '30019' }), 30019);
  assert.equal(errorCode({}), null);
});

test('num_media arrives as a string and "0" is truthy', () => {
  assert.equal(mediaCount({ num_media: '0' }), 0);
  assert.equal(mediaCount({ num_media: '1' }), 1);
  assert.equal(mediaCount({ num_media: 2 }), 2);
  assert.equal(mediaCount({}), 0);
  assert.equal(mediaCount({ num_media: 'not a number' }), 0);
});

test('tally counts only messages that carry media', () => {
  const rows = mmsTally([
    mms('SM1', 30019), mms('SM2'), mms('SM3', null, '0'),
    { sid: 'SM4', direction: 'inbound', num_media: '1' },
  ]);
  assert.deepEqual(rows.get('+15550001111'),
    { mms: 2, oversize: 1, sids: ['SM1'] });
});

test('tally groups on the messaging service when there is one', () => {
  const rows = mmsTally([{ ...mms('SM1', 30019), messaging_service_sid: 'MG1' }]);
  assert.deepEqual([...rows.keys()], ['MG1']);
});

test('the size ladder holds at every boundary', () => {
  assert.equal(sizeVerdict(300000)[0], 'safe');
  assert.equal(sizeVerdict(300001)[0], 'at-risk');
  assert.equal(sizeVerdict(600000)[0], 'at-risk');
  assert.equal(sizeVerdict(600001)[0], 'carrier-dependent');
  assert.equal(sizeVerdict(3500000)[0], 'carrier-dependent');
  assert.equal(sizeVerdict(3500001)[0], 'over-carriers');
  assert.equal(sizeVerdict(5000000)[0], 'over-carriers');
  assert.equal(sizeVerdict(5000001)[0], 'over-twilio');
});

test('the ladder takes Content-Length as the string a header is', () => {
  const [state, detail] = sizeVerdict('4200000');
  assert.equal(state, 'over-carriers');
  assert.match(detail, /4200 kB/);
});

test('a missing or unparseable Content-Length is unknown, not safe', () => {
  assert.equal(sizeVerdict(null)[0], 'unknown');
  assert.equal(sizeVerdict('')[0], 'unknown');
  assert.equal(sizeVerdict('chunked')[0], 'unknown');
});

test('the carrier-dependent band explains the partial failures', () => {
  const [, detail] = sizeVerdict(1200000);
  assert.match(detail, /one recipient gets the image and the next gets 30019/);
});

test('a sender with no failures is clean', () => {
  const [state, detail] = senderVerdict({ mms: 40, oversize: 0 });
  assert.equal(state, 'clean');
  assert.match(detail, /40/);
});

test('most of the MMS failing means no carrier takes it', () => {
  const [state, detail] = senderVerdict({ mms: 10, oversize: 8 });
  assert.equal(state, 'every-carrier');
  assert.match(detail, /nobody is receiving it/);
});

test('a minority failing is the carrier-dependent case', () => {
  const [state, detail] = senderVerdict({ mms: 100, oversize: 12 });
  assert.equal(state, 'carrier-dependent');
  assert.match(detail, /phone in your hand/);
});

test('a sender with no MMS at all says so', () => {
  const [state] = senderVerdict({ mms: 0, oversize: 0 });
  assert.equal(state, 'no-mms');
});
''',
"faq": [
 ("What size should I actually target for MMS?",
  "Under 600 KB. That is beneath the AT&T short-code cap and beneath every published carrier ceiling, so it removes the per-carrier lottery entirely. Twilio's own 5 MB limit is not a useful target: it only tells you whether the request will be accepted, not whether anything will be delivered."),
 ("Why does the same image deliver to some recipients and not others?",
  "Because the ceiling belongs to the destination carrier, and they differ by roughly an order of magnitude. Tier-one networks take up to about 3.5 MB, many others stop between 300 and 600 KB. A file in that band delivers to whoever is on a generous network and returns 30019 for everyone else, and the destination carrier is not a field you can read before sending."),
 ("Can I get the media size from the API?",
  "Not directly. The Media subresource returns the SID, the content_type and the URIs, but no byte count. The script reads Content-Length from the media URL with a GET whose body it never downloads, which is the only read-only way to get the number."),
 ("Does the MMS Converter fix this on its own?",
  "It helps and it is not a substitute for fixing the source. The converter downsizes and transcodes what passes through the Messaging Service, but Twilio only transcodes jpeg, png and gif; anything else goes to the carrier untouched at whatever size it is. Recompress at the source and treat the converter as the safety net."),
 ("Why does the script care whether num_media is a string?",
  "Because the 2010-04-01 API returns it as one, and \\"0\\" is truthy. A filter written as a truthiness test keeps every SMS on the account in the denominator, so a real MMS failure rate of thirty percent is reported as a fraction of a percent and nobody investigates."),
],
"related": [
 ("/twilio/ucs2-segment-inflation/", "One emoji tripling your segment count"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering that drops SMS silently"),
 ("/twilio/unknown-destination-handset-30005/", "Numbers the carrier does not recognise"),
],
"citations": [CITE_30019, CITE_MEDIA, CITE_MIME, CITE_MSG],
},

]
