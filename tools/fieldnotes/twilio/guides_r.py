#!/usr/bin/env python3
"""/twilio/ field notes, batch R — the four A2P failures that are not paperwork.

The registration notes in batch C read a status field and an errors array. These
four do not: one dates a suspension from the send side and asks what the producer
did afterwards, one does arithmetic on a per-minute send rate against the ceiling
the carrier assigned, one takes a set difference between an account's numbers and
its sender pools, and one reads a clock. Read-only throughout: an API Key with
read access, never the account auth token, and the repair is printed for a human
to run.
"""

CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_USA2P = ("UsAppToPerson resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/usapptoperson-resource")
CITE_MSPN = ("Messaging Service PhoneNumber resource — Twilio Docs",
             "https://www.twilio.com/docs/messaging/api/phonenumber-resource")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_BRAND = ("BrandRegistration resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/brand-registration-resource")
CITE_30033 = ("Error 30033: US A2P 10DLC campaign suspended — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30033")
CITE_30022 = ("Error 30022: US A2P 10DLC rate limit exceeded — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30022")
CITE_30034 = ("Error 30034: message from an unregistered number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30034")
CITE_30035 = ("Error 30035: number pending registration — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30035")
CITE_30024 = ("Error 30024: numeric sender ID not provisioned on carrier — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30024")
CITE_A2P = ("A2P 10DLC — Twilio Docs",
            "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc")
CITE_PNREG = (
    "Troubleshooting A2P phone number registration issues — Twilio Docs",
    "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-a2p-phone-number-registration-issues")
CITE_QUEUEING = ("Scaling, queueing and latency — Twilio Docs",
                 "https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency")

GUIDES = [

{
"slug": "a2p-campaign-suspended-30033",
"title": "A suspended campaign returns 30033 and the sends keep coming",
"description": "Every US message fails with 30033 and the producer has not been told. The Messages list dates the suspension and shows what your code did after it.",
"h1": "a suspended campaign returns 30033 and the sends keep coming",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30033", "a2p campaign suspended", "10dlc campaign suspension",
             "twilio campaign_status suspended", "30033 still sending"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The suspension email went to the account owner's address, which forwards to a distribution list nobody reads. The send worker knows nothing about it: it dequeues, it calls the API, it gets a Message back with <code>status</code> <code>undelivered</code> and <code>error_code</code> <code>30033</code>, and it retries. Four days later somebody notices, and by then the only question that matters &mdash; when did this start, and what has the code been doing since &mdash; is answerable only from the Messages list.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and keep the rows where <code>error_code</code> is <code>30033</code>. The oldest of those dates the suspension. Everything after it is the interesting part: sends that were refused, and any sender that started carrying this traffic only after the onset.</p>
<p>Confirm the state with <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> and read <code>campaign_status</code>. But the campaign resource cannot tell you when the suspension began or whether your producer is still pushing into it, and those are the two facts an incident needs.</p>""",
"problem": """<p><code>30033</code> is a per-message error, and messages are the only place it is recorded. The campaign resource shows <code>campaign_status</code> as <code>SUSPENDED</code>, which is a present-tense fact with no timestamp on it. So the first questions asked in the incident channel &mdash; when did we start failing, how many customers did we miss, is it still happening &mdash; have no answer on the compliance resources at all.</p>
<p>The second problem is the response. Because the failure is per-message and looks like a sender problem, the instinct is to move the traffic: point the worker at a different Messaging Service, or a toll-free number, or a second campaign that was registered for something else. That instinct is the reason this note exists. Rerouting suspended traffic is the specific behaviour that turns a campaign suspension into an account termination, and it is visible in the Messages list as a sender that appears for the first time after the onset.</p>""",
"why": """<p><strong>The error arrives at the worker, not at a human.</strong> An undelivered Message with an error code is a normal outcome for a send loop. It is logged at whatever level undelivered messages are logged at, which on most systems is the level nobody alerts on, and 30033 looks exactly like 30007 or 30003 from inside that loop.</p>
<p><strong>Nothing in the API timestamps the suspension.</strong> <code>campaign_status</code> has no <code>date_updated</code> you can trust for this, and the campaign carries no history. The first <code>30033</code> in the Messages list is the closest thing to an onset time that exists, and it is only as good as the window you paged.</p>
<p><strong>Retries make the number look worse than the outage.</strong> A worker that retries three times turns one blocked customer into three 30033 rows. Counting rows overstates the impact; counting distinct <code>to</code> values gives the number you actually need for the customer comms.</p>
<p><strong>The dangerous fix looks like the obvious fix.</strong> Sending the same traffic from a different sender is one config change and it appears to work for a few hours. It is also the thing Twilio and the carriers explicitly watch for, and the escalation from it is not another suspension.</p>""",
"steps": [
 {"h": "Page the Messages list over a window wider than the outage",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. There is no <code>ErrorCode</code> filter on this resource, so the filtering happens in your code. Make the window wide enough that it opens on healthy traffic: if the oldest row in the window is already a <code>30033</code>, the onset is outside it and the report cannot date anything.</p>"""},
 {"h": "Sort by date_sent, which is RFC 2822",
  "body": """<p><code>date_sent</code> comes back as <code>Mon, 24 Aug 2026 12:00:00 +0000</code>, not ISO 8601. A parser that raises on it throws away the window, and a parser that raises on one malformed row throws away the rest. Parse leniently and keep the rows you could not date rather than dropping them silently.</p>"""},
 {"h": "Take the first 30033 as the onset and split there",
  "body": """<p>Everything before it is what normal looked like: which Messaging Services and which <code>from</code> numbers were carrying traffic. Everything after it is the response. That split is the only structure in this data, and both halves are needed &mdash; the reroute check is meaningless without knowing what was there before.</p>"""},
 {"h": "Count refusals after the onset, and count distinct recipients",
  "body": """<p>Rows after the onset that still return <code>30033</code> are sends the producer made knowing nothing had changed. Report both the row count and the distinct <code>to</code> count: the first is how much the send loop wasted, the second is how many people did not get their message.</p>"""},
 {"h": "Flag any sender that appears only after the onset",
  "body": """<p>A <code>messaging_service_sid</code> or a <code>from</code> that carried nothing before the first <code>30033</code> and carries traffic after it is a reroute. Report it loudly and separately. This is the one finding here where the correct action is to undo something rather than to wait.</p>"""},
 {"h": "Confirm the status, then take it to Support and stop the producer",
  "body": """<p><code>GET /v1/Services/{ServiceSid}/Compliance/Usa2p</code> to confirm <code>campaign_status</code> is <code>SUSPENDED</code>, and check the brand above it before assuming the campaign is where the decision was made. There is no API repair for either. Remediate the traffic that caused it, reply to the suspension notice with evidence, and in the meantime stop sending rather than moving the sends.</p>"""},
],
"verify": """<p>Re-run the script over the same window. The report should read <code>clean</code>, and no sender should be flagged as having appeared after an onset.</p>
<pre><code class="language-bash">python3 twilio_a2p_campaign_suspension_report.py --days 14
# clean  0 x 30033 across 8412 message(s) since 2026-08-16</code></pre>""",
"code_intro": "One paginated read of the Messages list, then one confirming read per affected Messaging Service. Everything that matters happens in <code>verdict()</code>, which takes a list of message dicts and returns a state: the onset split, the refusal count after it and the reroute check are all decided without a network, because those are the parts worth pinning with tests.",
"py_file": "twilio_a2p_campaign_suspension_report.py",
"py": '''"""Date a 10DLC campaign suspension from the Messages list and say what happened next.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_a2p_campaign_suspension_report")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"

SUSPENDED = "30033"


def parse_when(value):
    """date_sent is RFC 2822, not ISO 8601. Returns epoch seconds, or None.

    Lenient on purpose. One malformed row should cost one row, not the window,
    and the rows that matter most here are the oldest ones in it.
    """
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError):
        return None


def sender_key(message):
    """What carried this message.

    The Messaging Service wins when both are set, because the campaign is
    attached to the service rather than to the number.
    """
    for k in ("messaging_service_sid", "from"):
        value = message.get(k)
        if value:
            return str(value)
    return "unknown"


def ordered(messages):
    """Oldest first. Rows with no usable date_sent keep their original order at
    the end rather than being dropped, so a bad timestamp cannot hide a 30033."""
    keyed = [(parse_when(m.get("date_sent")), i, m) for i, m in enumerate(messages)]
    dated = sorted(k for k in keyed if k[0] is not None)
    undated = [k for k in keyed if k[0] is None]
    return [m for _w, _i, m in dated] + [m for _w, _i, m in undated]


def is_suspended(message):
    return str(message.get("error_code") or "") == SUSPENDED


def recipients(messages):
    """Distinct to values. Retries turn one blocked customer into three rows, so
    this is the number that belongs in the customer comms."""
    return len({str(m.get("to") or "") for m in messages if m.get("to")})


def verdict(messages):
    """Classify a window by what the sends did after the first 30033. Pure.

    Returns (state, detail). States: clean, rerouted, still-pushing, stopped.
    """
    rows = ordered(messages)
    blocked = [m for m in rows if is_suspended(m)]
    if not blocked:
        return ("clean", "no 30033 in this window.")

    first = next(i for i, m in enumerate(rows) if is_suspended(m))
    after = rows[first + 1:]
    later = [m for m in after if is_suspended(m)]

    partial = ""
    seen_before = None
    if first == 0:
        partial = (" The window opens on a 30033, so the suspension started "
                   "before it: widen --days before reading anything into which "
                   "senders look new.")
    else:
        seen_before = {sender_key(m) for m in rows[:first]}

    if seen_before is not None:
        fresh = []
        for m in after:
            key = sender_key(m)
            if key not in seen_before and not is_suspended(m) and key not in fresh:
                fresh.append(key)
        if fresh:
            return ("rerouted",
                    "%d x 30033 over %d recipient(s), and then %s started "
                    "carrying traffic that had never used it before. Moving "
                    "suspended traffic to another sender is the response that "
                    "escalates to account termination."
                    % (len(blocked), recipients(blocked), ", ".join(fresh)))

    if later:
        return ("still-pushing",
                "%d x 30033 over %d recipient(s), %d of them after the first. "
                "The producer has not been told to stop and every one of those "
                "is a send that was refused.%s"
                % (len(blocked), recipients(blocked), len(later), partial))

    return ("stopped",
            "%d x 30033 over %d recipient(s), and nothing refused since. The "
            "sending stopped; the suspension is open until Support clears it.%s"
            % (len(blocked), recipients(blocked), partial))


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


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14,
                    help="how far back to read the Messages list")
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

    since = (datetime.now(timezone.utc)
             - timedelta(days=args.days)).strftime("%Y-%m-%d")
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages sent since %s", since)
        return 0

    state, detail = verdict(messages)
    line = "%-14s %s  %d message(s) since %s" % (state, detail, len(messages), since)
    if state == "clean":
        log.info(line)
        return 0
    log.warning(line)

    blocked = [m for m in messages if is_suspended(m)]
    services = set()
    for sender in sorted({sender_key(m) for m in blocked}):
        count = len([m for m in blocked if sender_key(m) == sender])
        log.warning("  %s  %d x 30033", sender, count)
        if sender.startswith("MG"):
            services.add(sender)

    for service in sorted(services):
        campaigns = list_v1(session, "%s/Services/%s/Compliance/Usa2p" % (MSG, service),
                            "compliance")
        status = (campaigns[0].get("campaign_status") if campaigns else None)
        log.warning("  %s  campaign_status=%s", service, status or "no campaign")

    log.warning("  repair: none by API. Stop the producer, remediate the traffic "
                "named in the suspension notice and reply to Twilio Support with "
                "evidence. Check the brand above the campaign before assuming the "
                "decision was made at the campaign.")
    if state == "rerouted":
        log.warning("  repair: undo the reroute first. Sending the same traffic "
                    "from another sender escalates a campaign suspension to the "
                    "account.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-campaign-suspension-report.mjs",
"js": '''/**
 * Date a 10DLC campaign suspension from the Messages list and say what happened next.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';

const SUSPENDED = '30033';

/**
 * date_sent is RFC 2822, not ISO 8601. Returns epoch seconds, or null. Lenient
 * on purpose: one malformed row should cost one row, not the window.
 */
export function parseWhen(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isNaN(ms) ? null : ms / 1000;
}

/**
 * What carried this message. The Messaging Service wins when both are set,
 * because the campaign is attached to the service rather than to the number.
 */
export function senderKey(message) {
  for (const k of ['messaging_service_sid', 'from']) {
    if (message[k]) return String(message[k]);
  }
  return 'unknown';
}

/** Oldest first. Rows with no usable date_sent keep their order at the end. */
export function ordered(messages) {
  const keyed = messages.map((m, i) => [parseWhen(m.date_sent), i, m]);
  const dated = keyed.filter(([w]) => w !== null)
    .sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  const undated = keyed.filter(([w]) => w === null);
  return [...dated, ...undated].map(([, , m]) => m);
}

export function isSuspended(message) {
  return String(message.error_code ?? '') === SUSPENDED;
}

/** Distinct to values: retries turn one blocked customer into three rows. */
export function recipients(messages) {
  return new Set(messages.filter((m) => m.to).map((m) => String(m.to))).size;
}

/**
 * Classify a window by what the sends did after the first 30033. Pure. Returns
 * [state, detail] with state clean, rerouted, still-pushing or stopped.
 */
export function verdict(messages) {
  const rows = ordered(messages);
  const blocked = rows.filter(isSuspended);
  if (blocked.length === 0) return ['clean', 'no 30033 in this window.'];

  const first = rows.findIndex(isSuspended);
  const after = rows.slice(first + 1);
  const later = after.filter(isSuspended);

  let partial = '';
  let seenBefore = null;
  if (first === 0) {
    partial = ' The window opens on a 30033, so the suspension started before ' +
      'it: widen --days before reading anything into which senders look new.';
  } else {
    seenBefore = new Set(rows.slice(0, first).map(senderKey));
  }

  if (seenBefore !== null) {
    const fresh = [];
    for (const m of after) {
      const key = senderKey(m);
      if (!seenBefore.has(key) && !isSuspended(m) && !fresh.includes(key)) {
        fresh.push(key);
      }
    }
    if (fresh.length) {
      return ['rerouted',
        `${blocked.length} x 30033 over ${recipients(blocked)} recipient(s), ` +
        `and then ${fresh.join(', ')} started carrying traffic that had never ` +
        'used it before. Moving suspended traffic to another sender is the ' +
        'response that escalates to account termination.'];
    }
  }

  if (later.length) {
    return ['still-pushing',
      `${blocked.length} x 30033 over ${recipients(blocked)} recipient(s), ` +
      `${later.length} of them after the first. The producer has not been told ` +
      `to stop and every one of those is a send that was refused.${partial}`];
  }

  return ['stopped',
    `${blocked.length} x 30033 over ${recipients(blocked)} recipient(s), and ` +
    'nothing refused since. The sending stopped; the suspension is open until ' +
    `Support clears it.${partial}`];
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

async function listMessages(auth, account, since, limit = 20000) {
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

async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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
    ? process.argv[process.argv.indexOf('--days') + 1] : 14) || 14;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  const [state, detail] = verdict(messages);
  const line = `${state.padEnd(14)} ${detail}  ${messages.length} message(s) ` +
               `since ${since}`;
  if (state === 'clean') { console.log(line); return; }
  console.warn(line);

  const blocked = messages.filter(isSuspended);
  const services = new Set();
  for (const sender of [...new Set(blocked.map(senderKey))].sort()) {
    const count = blocked.filter((m) => senderKey(m) === sender).length;
    console.warn(`  ${sender}  ${count} x 30033`);
    if (sender.startsWith('MG')) services.add(sender);
  }

  for (const service of [...services].sort()) {
    const campaigns = await listV1(auth,
      `${MSG}/Services/${service}/Compliance/Usa2p`, 'compliance');
    const status = campaigns[0]?.campaign_status ?? null;
    console.warn(`  ${service}  campaign_status=${status ?? 'no campaign'}`);
  }

  console.warn('  repair: none by API. Stop the producer, remediate the traffic ' +
               'named in the suspension notice and reply to Twilio Support with ' +
               'evidence. Check the brand above the campaign before assuming the ' +
               'decision was made at the campaign.');
  if (state === 'rerouted') {
    console.warn('  repair: undo the reroute first. Sending the same traffic ' +
                 'from another sender escalates a campaign suspension to the ' +
                 'account.');
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
"test_intro": "Four states and one edge that decides which of them is even reachable. The reroute case is the one worth reading twice: it only fires when there was healthy traffic before the onset, so a window that opens on a <code>30033</code> deliberately refuses to guess. The rest pin the RFC 2822 parsing, since a strict parser here silently reports every account as clean.",
"test_py_file": "test_twilio_a2p_campaign_suspension_report.py",
"test_py": '''from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from twilio_a2p_campaign_suspension_report import (ordered, recipients,
                                                   sender_key, verdict)

T0 = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def at(seconds, **kw):
    """One Message row, dated the way Twilio dates them."""
    row = {"date_sent": format_datetime(T0 + timedelta(seconds=seconds)),
           "messaging_service_sid": "MG1", "to": "+15550000001"}
    row.update(kw)
    return row


def test_a_window_with_no_30033_is_clean():
    state, _ = verdict([at(0), at(60, error_code=30007)])
    assert state == "clean"


def test_sends_continuing_after_the_onset_are_counted_separately():
    state, detail = verdict([at(0), at(60, error_code=30033),
                             at(120, error_code=30033),
                             at(180, error_code=30033)])
    assert state == "still-pushing"
    assert "2 of them after the first" in detail


def test_traffic_that_stopped_after_the_onset_is_its_own_state():
    state, detail = verdict([at(0), at(60, error_code=30033), at(120)])
    assert state == "stopped"
    assert "open until Support" in detail


def test_a_sender_that_appears_only_after_the_onset_is_a_reroute():
    # The dangerous one. MG2 carried nothing before the suspension and is
    # carrying the same traffic afterwards.
    state, detail = verdict([at(0), at(60, error_code=30033),
                             at(120, messaging_service_sid="MG2")])
    assert state == "rerouted"
    assert "MG2" in detail
    assert "termination" in detail


def test_a_window_opening_on_a_30033_refuses_to_guess_at_reroutes():
    # With nothing before the onset every sender looks new, so the check is
    # skipped and the report says to widen the window instead.
    state, detail = verdict([at(0, error_code=30033),
                             at(60, messaging_service_sid="MG2"),
                             at(120, error_code=30033)])
    assert state == "still-pushing"
    assert "widen --days" in detail


def test_retries_are_counted_as_rows_and_recipients_separately():
    rows = [at(0), at(60, error_code=30033), at(70, error_code=30033),
            at(80, error_code=30033)]
    assert recipients(rows[1:]) == 1
    assert "3 x 30033 over 1 recipient(s)" in verdict(rows)[1]


def test_the_messaging_service_wins_over_the_from_number():
    assert sender_key({"messaging_service_sid": "MG1", "from": "+15550001"}) == "MG1"
    assert sender_key({"from": "+15550001"}) == "+15550001"


def test_an_unparseable_date_keeps_its_row_instead_of_dropping_it():
    rows = ordered([{"date_sent": "not a date", "error_code": 30033}, at(0)])
    assert len(rows) == 2
    assert verdict(rows)[0] != "clean"
''',
"test_js_file": "twilio-a2p-campaign-suspension-report.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ordered, recipients, senderKey, verdict }
  from './twilio-a2p-campaign-suspension-report.mjs';

const T0 = Date.UTC(2026, 7, 24, 12, 0, 0);

/** One Message row, dated the way Twilio dates them. */
const at = (seconds, extra = {}) => ({
  date_sent: new Date(T0 + seconds * 1000).toUTCString(),
  messaging_service_sid: 'MG1',
  to: '+15550000001',
  ...extra,
});

test('a window with no 30033 is clean', () => {
  assert.equal(verdict([at(0), at(60, { error_code: 30007 })])[0], 'clean');
});

test('sends continuing after the onset are counted separately', () => {
  const [state, detail] = verdict([at(0), at(60, { error_code: 30033 }),
    at(120, { error_code: 30033 }), at(180, { error_code: 30033 })]);
  assert.equal(state, 'still-pushing');
  assert.match(detail, /2 of them after the first/);
});

test('traffic that stopped after the onset is its own state', () => {
  const [state, detail] = verdict([at(0), at(60, { error_code: 30033 }), at(120)]);
  assert.equal(state, 'stopped');
  assert.match(detail, /open until Support/);
});

test('a sender that appears only after the onset is a reroute', () => {
  const [state, detail] = verdict([at(0), at(60, { error_code: 30033 }),
    at(120, { messaging_service_sid: 'MG2' })]);
  assert.equal(state, 'rerouted');
  assert.match(detail, /MG2/);
  assert.match(detail, /termination/);
});

test('a window opening on a 30033 refuses to guess at reroutes', () => {
  const [state, detail] = verdict([at(0, { error_code: 30033 }),
    at(60, { messaging_service_sid: 'MG2' }), at(120, { error_code: 30033 })]);
  assert.equal(state, 'still-pushing');
  assert.match(detail, /widen --days/);
});

test('retries are counted as rows and recipients separately', () => {
  const rows = [at(0), at(60, { error_code: 30033 }), at(70, { error_code: 30033 }),
    at(80, { error_code: 30033 })];
  assert.equal(recipients(rows.slice(1)), 1);
  assert.match(verdict(rows)[1], /3 x 30033 over 1 recipient\\(s\\)/);
});

test('the messaging service wins over the from number', () => {
  assert.equal(senderKey({ messaging_service_sid: 'MG1', from: '+15550001' }), 'MG1');
  assert.equal(senderKey({ from: '+15550001' }), '+15550001');
});

test('an unparseable date keeps its row instead of dropping it', () => {
  const rows = ordered([{ date_sent: 'not a date', error_code: 30033 }, at(0)]);
  assert.equal(rows.length, 2);
  assert.notEqual(verdict(rows)[0], 'clean');
});
''',
"faq": [
 ("Can I get the exact time the campaign was suspended?",
  "Not from the compliance resources. campaign_status is a present-tense field with no history, and the campaign object carries no suspension timestamp. The oldest 30033 in the Messages list is the closest thing that exists, and it is only as accurate as the window you paged, which is why the script says so when the window opens on a 30033."),
 ("Is 30033 always the campaign rather than the brand?",
  "No. A suspended brand suspends every campaign under it, and the send-side symptom is identical. The layer question is answered by joining BrandRegistrations to the campaigns on brand_registration_sid, which is a separate check with a separate note."),
 ("Why does the script care which sender carried traffic after the onset?",
  "Because rerouting suspended traffic through a different Messaging Service, number or campaign is the specific response that escalates a campaign suspension to account termination. It is a config change that looks like a fix, and the Messages list is the only place it is visible."),
 ("Should I keep sending while I wait for Support?",
  "No. Every send into a suspended campaign is refused and still consumes your worker's retries. Stop the producer for the affected sender, and if the traffic is genuinely urgent use a channel that was already provisioned for it rather than one you switch to today."),
 ("Why not just filter the Messages list by error code?",
  "There is no ErrorCode filter and no Status filter on that resource. The documented parameters are To, From, DateSent, DateSent<, DateSent> and paging. Every 30033 report pages the window and filters client-side, which is the reason so few accounts have one."),
],
"related": [
 ("/twilio/a2p-brand-suspended/", "A SUSPENDED brand suspends every campaign underneath it"),
 ("/twilio/a2p-campaign-vetting-failed/", "A FAILED campaign and the errors[] that names why"),
 ("/twilio/a2p-throughput-exceeded-30022/", "30022 when sends outrun the assigned throughput"),
],
"citations": [CITE_30033, CITE_MSG, CITE_USA2P, CITE_BRAND],
},

{
"slug": "a2p-throughput-exceeded-30022",
"title": "30022 when sends outrun the throughput the carrier assigned",
"description": "Intermittent 30022 at peak and nothing wrong at 3am. Compare your busiest minute against rate_limits on the campaign before asking for more throughput.",
"h1": "30022 when sends outrun the throughput the carrier assigned",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30022", "a2p 10dlc rate limit exceeded", "10dlc mps throughput",
             "twilio rate_limits campaign", "twilio message throughput exceeded"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It only happens during the morning send. The same message, retried at lunchtime, delivers. So the bug report reads &ldquo;intermittent SMS failures&rdquo; and gets triaged as a Twilio problem, when <code>30022</code> is Twilio telling you precisely what it is: your combined send rate across the campaign went past a number the carrier assigned you, and that number is published on the campaign resource.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, bucket the rows by the minute in <code>date_sent</code>, and find the busiest minute. Then read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> and take the lowest MPS in <code>rate_limits</code>.</p>
<p>Peak minute divided by 60 against that number gives you the answer. Above it, throttle the producer. Below it and still getting <code>30022</code>, the burst is inside a single second or piled onto one recipient, and more throughput will not fix either.</p>""",
"problem": """<p><code>30022</code> is rate limiting, so it is load-shaped: invisible off-peak, unreproducible in staging, and cleared by a retry. That combination sends teams looking for a network fault. Meanwhile the actual ceiling is a per-carrier number sitting in <code>rate_limits</code> on the campaign, which almost nobody reads, because nothing in the send path ever refers to it.</p>
<p>The other half of the problem is what people do next. The assumed fix is more senders: add numbers to the pool and the throughput goes up. It does not. A 10DLC campaign's throughput is assigned at the campaign, derived from the brand's trust score, and shared across every number in the pool. Ten numbers under one campaign have exactly the throughput of one. Buying nine more numbers to fix <code>30022</code> is a monthly bill for nothing.</p>""",
"why": """<p><strong>The ceiling is on a resource the send path never touches.</strong> Your code knows a Messaging Service SID and a destination. <code>rate_limits</code> lives two hops away, on the campaign attached to that service, and there is no field on the Message that says what limit it hit.</p>
<p><strong>A minute average hides a one-second burst.</strong> The limit is messages per second. A job that fires 900 messages in the first four seconds of a minute is at 15 per second while averaging 15 per minute, which looks fine at every granularity except the one the carrier enforces. That is why &ldquo;under the ceiling and still failing&rdquo; is a real state and not a measurement error.</p>
<p><strong>Throughput scales with trust, not with hardware.</strong> MPS toward AT&amp;T, T-Mobile and Verizon is a function of the brand's vetting score and the campaign's use case. The lever is secondary vetting on the brand, not senders, not instances, and not a support ticket asking for more.</p>
<p><strong>Per-recipient throttling wears the same code.</strong> Too many messages to one handset in quick succession also returns <code>30022</code>, and it produces a very different fix &mdash; deduplicate the producer &mdash; from an account-wide overrun. The tell is that the failures pile onto a handful of <code>to</code> values instead of spreading.</p>""",
"steps": [
 {"h": "Read the ceiling off the campaign, per carrier",
  "body": """<p><code>GET /v1/Services/{ServiceSid}/Compliance/Usa2p</code> and look at <code>rate_limits</code>. It is reported per carrier, and the shape has changed more than once, so walk it rather than indexing into it. Take the lowest MPS you find: your producer meets the tightest carrier first, and that is the number it has to respect.</p>"""},
 {"h": "Page the Messages list over hours, not weeks",
  "body": """<p>This check needs resolution, not history. A day or two at <code>PageSize=1000</code> is enough to catch a peak, and a wider window mostly costs you paging time. There is no <code>ErrorCode</code> filter on the resource, so read <code>error_code</code> yourself and keep <code>30022</code>.</p>"""},
 {"h": "Bucket by minute, using date_sent",
  "body": """<p><code>date_sent</code> is RFC 2822. Parse it, floor to the minute, and count sends and <code>30022</code>s in each bucket. The busiest bucket divided by 60 is your observed rate. Say plainly in the report that this is an average, because the next state depends on knowing it is.</p>"""},
 {"h": "Check whether the failures concentrate on one recipient first",
  "body": """<p>If most of the <code>30022</code>s land on a small number of <code>to</code> values, this is per-recipient throttling and the account-wide arithmetic is beside the point. Deduplicate the producer or collapse the messages; the campaign's MPS is not involved.</p>"""},
 {"h": "Compare, then pick the lever that matches",
  "body": """<p>Observed peak above the ceiling: throttle the producer to the published MPS and queue the overflow on your side. Below the ceiling and still failing: your burst is sub-second, so smooth it rather than raise it. Either way, adding numbers to the pool changes nothing, because the limit is on the campaign.</p>"""},
 {"h": "Raise the ceiling only through the brand",
  "body": """<p>More throughput comes from a higher trust score, which comes from secondary vetting on the brand. That is a request against <code>BrandRegistrations/{BrandSid}/Vettings</code>, not a change to the campaign or the pool, and it takes days rather than minutes &mdash; so the client-side queue is what carries you until then.</p>"""},
],
"verify": """<p>Re-run over a window that includes a peak. The busiest minute should sit under the published ceiling, with no <code>30022</code> in the window.</p>
<pre><code class="language-bash">python3 twilio_a2p_throughput_report.py --days 2
# clean  no 30022 in this window.  peak 42/min = 0.7/s against a ceiling of 4.5/s</code></pre>""",
"code_intro": "Two reads: the campaign for the ceiling, the Messages list for the rate. The classifier takes the messages and a ceiling and nothing else, so every branch that matters &mdash; over the ceiling, under it and still failing, concentrated on one handset, no ceiling published at all &mdash; is decided offline. <code>mps_ceiling()</code> walks <code>rate_limits</code> instead of indexing into it, because that structure is reported per carrier and has not held one shape.",
"py_file": "twilio_a2p_throughput_report.py",
"py": '''"""Compare an account's peak send rate against the MPS the carrier assigned the campaign.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_a2p_throughput_report")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"

THROTTLED = "30022"


def parse_when(value):
    """date_sent is RFC 2822, not ISO 8601. Returns epoch seconds, or None."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError):
        return None


def is_throttled(message):
    return str(message.get("error_code") or "") == THROTTLED


def mps_ceiling(rate_limits):
    """The lowest per-second ceiling anywhere in rate_limits, or None.

    Walked rather than indexed. rate_limits is reported per carrier and the
    layout has changed more than once, so this collects any positive number
    under a key that mentions mps and takes the smallest: the producer meets
    the tightest carrier first, and that is the number it has to respect.
    """
    found = []

    def walk(node, key=""):
        if isinstance(node, dict):
            for k, value in node.items():
                walk(value, str(k))
        elif isinstance(node, list):
            for value in node:
                walk(value, key)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            if "mps" in key.lower() and node > 0:
                found.append(float(node))

    walk(rate_limits or {})
    return min(found) if found else None


def per_minute(messages):
    """Bucket a window by the minute a message was sent.

    Returns {epoch_minute: {"sent": n, "blocked": n}}. Rows with no usable
    date_sent cannot be placed on the timeline and are skipped here; they are
    still counted in the totals the caller reports.
    """
    out = {}
    for message in messages:
        when = parse_when(message.get("date_sent"))
        if when is None:
            continue
        bucket = out.setdefault(int(when // 60), {"sent": 0, "blocked": 0})
        bucket["sent"] += 1
        if is_throttled(message):
            bucket["blocked"] += 1
    return out


def busiest_recipient(messages):
    """(to, share) for the destination carrying the largest share of these rows."""
    counts = {}
    for message in messages:
        to = str(message.get("to") or "")
        counts[to] = counts.get(to, 0) + 1
    if not counts:
        return ("", 0.0)
    to, count = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
    return (to, count / float(len(messages)))


def peak(buckets):
    """(epoch_minute, sends) for the busiest minute, or (None, 0)."""
    if not buckets:
        return (None, 0)
    minute, counts = max(buckets.items(), key=lambda kv: (kv[1]["sent"], kv[0]))
    return (minute, counts["sent"])


def verdict(messages, ceiling):
    """Classify a window against the campaign's published MPS. Pure.

    Returns (state, detail). States: clean, per-recipient, no-ceiling-published,
    over-the-ceiling, under-the-ceiling.
    """
    _minute, sends = peak(per_minute(messages))
    observed = sends / 60.0
    blocked = [m for m in messages if is_throttled(m)]
    if not blocked:
        return ("clean",
                "no 30022 in this window. Peak %d/min = %.2f/s against a "
                "ceiling of %s." % (sends, observed,
                                    "%.2f/s" % ceiling if ceiling else "unpublished"))

    to, share = busiest_recipient(blocked)
    if len(blocked) >= 4 and share >= 0.5:
        return ("per-recipient",
                "%d x 30022 and %.0f%% of them went to %s. That is per "
                "destination throttling, not the campaign's MPS: collapse or "
                "deduplicate the messages to that handset."
                % (len(blocked), share * 100, to))

    if ceiling is None:
        return ("no-ceiling-published",
                "%d x 30022, and rate_limits published no MPS to compare "
                "against. Peak minute was %d sends = %.2f/s. Check the campaign "
                "is VERIFIED before reading anything into that."
                % (len(blocked), sends, observed))

    if observed > ceiling:
        return ("over-the-ceiling",
                "%d x 30022. Peak minute averaged %.2f/s against a published "
                "ceiling of %.2f/s. Throttle the producer to the ceiling and "
                "queue the overflow; more numbers in the pool share the same "
                "limit." % (len(blocked), observed, ceiling))

    return ("under-the-ceiling",
            "%d x 30022, but the peak minute averaged %.2f/s under a ceiling of "
            "%.2f/s. The burst is inside a second rather than across the "
            "minute, so smooth the send loop; raising the limit will not reach "
            "it." % (len(blocked), observed, ceiling))


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
    window and the page cap are the only ways to bound the read."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=2,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=50000,
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

    ceilings = {}
    for service in list_v1(session, MSG + "/Services", "services"):
        campaigns = list_v1(session,
                            "%s/Services/%s/Compliance/Usa2p" % (MSG, service["sid"]),
                            "compliance")
        if campaigns:
            ceilings[service["sid"]] = mps_ceiling(campaigns[0].get("rate_limits"))

    since = (datetime.now(timezone.utc)
             - timedelta(days=args.days)).strftime("%Y-%m-%d")
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages sent since %s", since)
        return 0

    bad = 0
    for service in sorted(ceilings):
        rows = [m for m in messages
                if str(m.get("messaging_service_sid") or "") == service]
        if not rows:
            continue
        state, detail = verdict(rows, ceilings[service])
        line = "%-21s %s  %s" % (state, service, detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "over-the-ceiling":
            log.warning("  repair: throttle the producer to %.2f/s and queue the "
                        "overflow client side. To lift the ceiling, request "
                        "secondary vetting on the brand.", ceilings[service])
        elif state == "under-the-ceiling":
            log.warning("  repair: spread the send loop across the second rather "
                        "than firing the batch at once. The ceiling is already "
                        "above your minute average.")
        elif state == "per-recipient":
            log.warning("  repair: deduplicate the producer. Per destination "
                        "throttling is not raised by trust score or by senders.")
        else:
            log.warning("  repair: confirm campaign_status is VERIFIED, then "
                        "re-read rate_limits before changing the send rate.")

    log.info("%d Messaging Service(s) with a campaign, %d over throughput",
             len(ceilings), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-throughput-report.mjs",
"js": '''/**
 * Compare an account's peak send rate against the MPS the carrier assigned the campaign.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';

const THROTTLED = '30022';

/** date_sent is RFC 2822, not ISO 8601. Returns epoch seconds, or null. */
export function parseWhen(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isNaN(ms) ? null : ms / 1000;
}

export function isThrottled(message) {
  return String(message.error_code ?? '') === THROTTLED;
}

/**
 * The lowest per-second ceiling anywhere in rate_limits, or null. Walked rather
 * than indexed: rate_limits is reported per carrier and the layout has changed
 * more than once, and the tightest carrier is the one the producer meets first.
 */
export function mpsCeiling(rateLimits) {
  const found = [];
  const walk = (node, key = '') => {
    if (Array.isArray(node)) {
      for (const value of node) walk(value, key);
    } else if (node && typeof node === 'object') {
      for (const [k, value] of Object.entries(node)) walk(value, String(k));
    } else if (typeof node === 'number' && Number.isFinite(node)) {
      if (key.toLowerCase().includes('mps') && node > 0) found.push(node);
    }
  };
  walk(rateLimits ?? {});
  return found.length ? Math.min(...found) : null;
}

/**
 * Bucket a window by the minute a message was sent. Returns a Map of
 * epoch minute to { sent, blocked }. Rows with no usable date_sent cannot be
 * placed on the timeline and are skipped here.
 */
export function perMinute(messages) {
  const out = new Map();
  for (const message of messages) {
    const when = parseWhen(message.date_sent);
    if (when === null) continue;
    const minute = Math.floor(when / 60);
    const bucket = out.get(minute) ?? { sent: 0, blocked: 0 };
    bucket.sent += 1;
    if (isThrottled(message)) bucket.blocked += 1;
    out.set(minute, bucket);
  }
  return out;
}

/** [to, share] for the destination carrying the largest share of these rows. */
export function busiestRecipient(messages) {
  const counts = new Map();
  for (const message of messages) {
    const to = String(message.to ?? '');
    counts.set(to, (counts.get(to) ?? 0) + 1);
  }
  if (counts.size === 0) return ['', 0];
  let best = ['', 0];
  for (const [to, count] of [...counts.entries()].sort()) {
    if (count > best[1]) best = [to, count];
  }
  return [best[0], best[1] / messages.length];
}

/** [epochMinute, sends] for the busiest minute, or [null, 0]. */
export function peak(buckets) {
  let best = [null, 0];
  for (const [minute, counts] of [...buckets.entries()].sort((a, b) => a[0] - b[0])) {
    if (counts.sent > best[1]) best = [minute, counts.sent];
  }
  return best;
}

/**
 * Classify a window against the campaign's published MPS. Pure. Returns
 * [state, detail] with state clean, per-recipient, no-ceiling-published,
 * over-the-ceiling or under-the-ceiling.
 */
export function verdict(messages, ceiling) {
  const [, sends] = peak(perMinute(messages));
  const observed = sends / 60;
  const blocked = messages.filter(isThrottled);
  const ceilingText = ceiling ? `${ceiling.toFixed(2)}/s` : 'unpublished';
  if (blocked.length === 0) {
    return ['clean',
      `no 30022 in this window. Peak ${sends}/min = ${observed.toFixed(2)}/s ` +
      `against a ceiling of ${ceilingText}.`];
  }

  const [to, share] = busiestRecipient(blocked);
  if (blocked.length >= 4 && share >= 0.5) {
    return ['per-recipient',
      `${blocked.length} x 30022 and ${(share * 100).toFixed(0)}% of them went ` +
      `to ${to}. That is per destination throttling, not the campaign's MPS: ` +
      'collapse or deduplicate the messages to that handset.'];
  }

  if (ceiling === null || ceiling === undefined) {
    return ['no-ceiling-published',
      `${blocked.length} x 30022, and rate_limits published no MPS to compare ` +
      `against. Peak minute was ${sends} sends = ${observed.toFixed(2)}/s. ` +
      'Check the campaign is VERIFIED before reading anything into that.'];
  }

  if (observed > ceiling) {
    return ['over-the-ceiling',
      `${blocked.length} x 30022. Peak minute averaged ${observed.toFixed(2)}/s ` +
      `against a published ceiling of ${ceiling.toFixed(2)}/s. Throttle the ` +
      'producer to the ceiling and queue the overflow; more numbers in the pool ' +
      'share the same limit.'];
  }

  return ['under-the-ceiling',
    `${blocked.length} x 30022, but the peak minute averaged ` +
    `${observed.toFixed(2)}/s under a ceiling of ${ceiling.toFixed(2)}/s. The ` +
    'burst is inside a second rather than across the minute, so smooth the send ' +
    'loop; raising the limit will not reach it.'];
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

async function listMessages(auth, account, since, limit = 50000) {
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

async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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

  const ceilings = new Map();
  for (const service of await listV1(auth, `${MSG}/Services`, 'services')) {
    const campaigns = await listV1(auth,
      `${MSG}/Services/${service.sid}/Compliance/Usa2p`, 'compliance');
    if (campaigns.length) {
      ceilings.set(service.sid, mpsCeiling(campaigns[0].rate_limits));
    }
  }

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 2) || 2;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  let bad = 0;
  for (const service of [...ceilings.keys()].sort()) {
    const rows = messages.filter(
      (m) => String(m.messaging_service_sid ?? '') === service);
    if (rows.length === 0) continue;
    const ceiling = ceilings.get(service);
    const [state, detail] = verdict(rows, ceiling);
    const line = `${state.padEnd(21)} ${service}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'over-the-ceiling') {
      console.warn(`  repair: throttle the producer to ${ceiling.toFixed(2)}/s ` +
                   'and queue the overflow client side. To lift the ceiling, ' +
                   'request secondary vetting on the brand.');
    } else if (state === 'under-the-ceiling') {
      console.warn('  repair: spread the send loop across the second rather than ' +
                   'firing the batch at once. The ceiling is already above your ' +
                   'minute average.');
    } else if (state === 'per-recipient') {
      console.warn('  repair: deduplicate the producer. Per destination ' +
                   'throttling is not raised by trust score or by senders.');
    } else {
      console.warn('  repair: confirm campaign_status is VERIFIED, then re-read ' +
                   'rate_limits before changing the send rate.');
    }
  }

  console.log(`${ceilings.size} Messaging Service(s) with a campaign, ${bad} ` +
              'over throughput');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two states that look identical in a log and mean opposite things are the point: over the ceiling means throttle, under it means the burst is sub-second and the ceiling was never the problem. The <code>mps_ceiling()</code> cases matter just as much &mdash; a walker that indexed into <code>rate_limits</code> would return nothing the day the shape changes, and a report comparing against nothing reads as clean.",
"test_py_file": "test_twilio_a2p_throughput_report.py",
"test_py": '''from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from twilio_a2p_throughput_report import (mps_ceiling, per_minute, peak, verdict)

T0 = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)

RATE_LIMITS = {"carriers": [{"carrier": "att", "mps": 12},
                            {"carrier": "tmobile", "mps": 4.5},
                            {"carrier": "verizon", "mps": 30}]}


def at(seconds, **kw):
    row = {"date_sent": format_datetime(T0 + timedelta(seconds=seconds)),
           "to": "+1555000%04d" % seconds}
    row.update(kw)
    return row


def burst(count, *, second=0, **kw):
    """count messages inside one minute, so the minute bucket sees all of them."""
    return [at(second + (i % 50), **kw) for i in range(count)]


def test_a_window_with_no_30022_is_clean():
    state, detail = verdict(burst(120), 4.5)
    assert state == "clean"
    assert "4.50/s" in detail


def test_a_peak_above_the_ceiling_says_throttle():
    rows = burst(500) + burst(6, error_code=30022)
    state, detail = verdict(rows, 4.5)
    assert state == "over-the-ceiling"
    assert "8.43/s" in detail and "4.50/s" in detail


def test_failures_under_the_ceiling_are_a_sub_second_burst():
    # 60 sends in the minute is 1/s on average, well under 4.5, and it still
    # 30022s: the batch went out inside one second.
    rows = burst(60) + burst(5, error_code=30022)
    state, detail = verdict(rows, 4.5)
    assert state == "under-the-ceiling"
    assert "inside a second" in detail


def test_failures_piled_on_one_handset_are_per_recipient_throttling():
    rows = burst(60) + [at(i, to="+15550009999", error_code=30022) for i in range(6)]
    state, detail = verdict(rows, 4.5)
    assert state == "per-recipient"
    assert "+15550009999" in detail


def test_no_published_mps_is_reported_rather_than_compared():
    state, detail = verdict(burst(60) + burst(5, error_code=30022), None)
    assert state == "no-ceiling-published"
    assert "VERIFIED" in detail


def test_the_lowest_carrier_mps_is_the_one_that_binds():
    assert mps_ceiling(RATE_LIMITS) == 4.5


def test_an_absent_or_shapeless_rate_limits_yields_no_ceiling():
    assert mps_ceiling(None) is None
    assert mps_ceiling({"carriers": [{"carrier": "att", "daily_cap": 200000}]}) is None


def test_buckets_are_minutes_not_seconds():
    buckets = per_minute([at(0), at(30), at(59), at(60)])
    assert len(buckets) == 2
    assert peak(buckets)[1] == 3
''',
"test_js_file": "twilio-a2p-throughput-report.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mpsCeiling, perMinute, peak, verdict }
  from './twilio-a2p-throughput-report.mjs';

const T0 = Date.UTC(2026, 7, 24, 12, 0, 0);

const RATE_LIMITS = { carriers: [{ carrier: 'att', mps: 12 },
  { carrier: 'tmobile', mps: 4.5 }, { carrier: 'verizon', mps: 30 }] };

const at = (seconds, extra = {}) => ({
  date_sent: new Date(T0 + seconds * 1000).toUTCString(),
  to: `+1555000${String(seconds).padStart(4, '0')}`,
  ...extra,
});

/** count messages inside one minute, so the minute bucket sees all of them. */
const burst = (count, extra = {}) =>
  Array.from({ length: count }, (_, i) => at(i % 50, extra));

test('a window with no 30022 is clean', () => {
  const [state, detail] = verdict(burst(120), 4.5);
  assert.equal(state, 'clean');
  assert.match(detail, /4\\.50\\/s/);
});

test('a peak above the ceiling says throttle', () => {
  const [state, detail] = verdict([...burst(500),
    ...burst(6, { error_code: 30022 })], 4.5);
  assert.equal(state, 'over-the-ceiling');
  assert.match(detail, /8\\.43\\/s/);
  assert.match(detail, /4\\.50\\/s/);
});

test('failures under the ceiling are a sub second burst', () => {
  const [state, detail] = verdict([...burst(60),
    ...burst(5, { error_code: 30022 })], 4.5);
  assert.equal(state, 'under-the-ceiling');
  assert.match(detail, /inside a second/);
});

test('failures piled on one handset are per recipient throttling', () => {
  const piled = Array.from({ length: 6 },
    (_, i) => at(i, { to: '+15550009999', error_code: 30022 }));
  const [state, detail] = verdict([...burst(60), ...piled], 4.5);
  assert.equal(state, 'per-recipient');
  assert.match(detail, /\\+15550009999/);
});

test('no published mps is reported rather than compared', () => {
  const [state, detail] = verdict([...burst(60),
    ...burst(5, { error_code: 30022 })], null);
  assert.equal(state, 'no-ceiling-published');
  assert.match(detail, /VERIFIED/);
});

test('the lowest carrier mps is the one that binds', () => {
  assert.equal(mpsCeiling(RATE_LIMITS), 4.5);
});

test('an absent or shapeless rate_limits yields no ceiling', () => {
  assert.equal(mpsCeiling(null), null);
  assert.equal(mpsCeiling({ carriers: [{ carrier: 'att', daily_cap: 200000 }] }), null);
});

test('buckets are minutes not seconds', () => {
  const buckets = perMinute([at(0), at(30), at(59), at(60)]);
  assert.equal(buckets.size, 2);
  assert.equal(peak(buckets)[1], 3);
});
''',
"faq": [
 ("Will adding more phone numbers raise my throughput?",
  "No. A 10DLC campaign's MPS is assigned at the campaign and shared across every number in its sender pool, so ten numbers under one campaign send at the rate of one. More senders help with sticky sender behaviour and with per-number carrier limits on other channels, not with 30022."),
 ("Where is my actual throughput number?",
  "In rate_limits on the campaign, returned by GET /v1/Services/{ServiceSid}/Compliance/Usa2p. It is reported per carrier, so read all of them and plan against the lowest: your producer hits the tightest carrier first and that is where the 30022 comes from."),
 ("Why does the script say I am under the ceiling and still failing?",
  "Because the limit is per second and the script can only measure per minute from date_sent. A job that fires its whole batch in the first two seconds of a minute averages far below the ceiling and still exceeds it while it runs. That state is a signal to smooth the send loop rather than ask for more throughput."),
 ("How do I actually get a higher ceiling?",
  "Through the brand, not the campaign. Throughput toward AT&T, T-Mobile and Verizon scales with the brand's vetting score, so the lever is secondary vetting on the BrandRegistration. That takes days, which is why the client-side queue is the part you build first."),
 ("Is 30022 the same as 30001?",
  "No. 30022 is the carrier refusing the send because the campaign's assigned throughput was exceeded. 30001 is Twilio's own outbound queue overflowing because the producer outran the sender for long enough to fill it. They often appear together under the same load and they have different fixes."),
],
"related": [
 ("/twilio/messaging-queue-overflow-30001/", "30001 when the send loop outruns the sender"),
 ("/twilio/a2p-brand-missing-secondary-vetting/", "No trust score, so throughput stays floored"),
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never leave queued or accepted"),
],
"citations": [CITE_30022, CITE_USA2P, CITE_MSG, CITE_QUEUEING],
},

{
"slug": "number-missing-from-campaign-sender-pool",
"title": "A 10DLC number outside the sender pool is never registered",
"description": "The brand is APPROVED and the campaign VERIFIED, and this number still 30034s. A2P registration attaches through the pool, and this number is not in one.",
"h1": "a 10DLC number outside the sender pool is never registered",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30034", "10dlc number not registered", "messaging service sender pool",
             "twilio a2p phone number registration", "from bypasses messaging service"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody bought a second number for the marketing send, because the support number was busy. The brand is <code>APPROVED</code>, the campaign is <code>VERIFIED</code>, so the number is registered &mdash; that is how everyone on the team understood it. Except registration does not attach to an account or to a brand. It attaches to numbers, one at a time, through the sender pool of the Messaging Service that carries the campaign, and this number was never added to one.",
"short_answer": """<p>Take a set difference. <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> gives every number you own; keep the SMS-capable <code>+1</code> long codes. <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> per Messaging Service gives every number in a pool. Anything in the first list and not in the second is <code>UNREGISTERED</code>, whatever the brand and campaign say.</p>
<p>Cross-check against <code>Messages.json</code> rows with <code>error_code</code> <code>30034</code> grouped by <code>from</code>, which tells you which of those gaps is already costing you deliveries and which is merely waiting to.</p>""",
"problem": """<p>Every status a team checks is green. The brand is <code>APPROVED</code>, the campaign is <code>VERIFIED</code>, the Messaging Service reports <code>us_app_to_person_registered</code> as <code>true</code>. Then one number returns <code>30034</code> on everything it sends, and <code>30034</code> is documented as an unregistered number, which reads as a contradiction of all three.</p>
<p>It is not. The campaign is a registration of a use case; the pool is the list of numbers that registration covers. Adding a number to your account, or setting it as a <code>From</code> in your code, never touches the pool. So the failure is a gap between two lists that no single API response shows, and nothing errors at the moment the gap is created &mdash; not when you buy the number, not when you deploy the code that sends from it.</p>
<p>The send path makes it worse. Code that sets <code>From=+1…</code> directly bypasses the Messaging Service entirely, which means it bypasses the object that carries the campaign. That pattern is why the gap survives: the number works for inbound, it works for voice, it accepts the API call, and it fails only on the carrier's side of a US A2P send.</p>""",
"why": """<p><strong>Nothing in the account view is number-shaped.</strong> The A2P console and the compliance API are organised by brand, campaign and Messaging Service. Numbers appear inside a service's pool, so a number that is in no service appears in no A2P view at all. Absence is genuinely hard to see.</p>
<p><strong>30034 is the same code for four different causes.</strong> No campaign at all, a failed campaign, a suspended one, and a number outside the pool all return it. The code tells you the carrier considered the sender unregistered, which is true in all four cases and diagnostic in none.</p>
<p><strong>Buying a number never fails.</strong> The purchase succeeds, the number is SMS-capable, and the first US send is the first thing that fails. In a system that buys numbers programmatically that is a very long feedback loop.</p>
<p><strong>A bare From looks like the simple option.</strong> It is one field instead of one field, and it works everywhere except US A2P. Teams that started before 10DLC still have it in the send path, and the code that reads it has no idea a Messaging Service exists.</p>
<p><strong>A recently added number is a different finding.</strong> A number that is in the pool and still failing may be inside the carrier's registration window rather than misconfigured, and waiting is the correct action there. Reporting the two as one thing sends people to remove and re-add a number that was going to work in an hour.</p>""",
"steps": [
 {"h": "List every number the account owns",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, following <code>next_page_uri</code>. Keep the rows where <code>capabilities.sms</code> is true.</p>"""},
 {"h": "Narrow to the numbers 10DLC actually governs",
  "body": """<p>US long codes only: <code>+1</code>, eleven digits, and not toll-free. Toll-free numbers under <code>+1800</code>, <code>+1833</code>, <code>+1844</code>, <code>+1855</code>, <code>+1866</code>, <code>+1877</code> and <code>+1888</code> have their own verification path and belong in a different report. Short codes and non-US numbers are out of scope entirely.</p>"""},
 {"h": "Build the pool from every Messaging Service",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code>, then <code>GET /v1/Services/{ServiceSid}/PhoneNumbers</code> for each. Keep the service alongside each number: whether that service has a campaign is the difference between two of the findings below.</p>"""},
 {"h": "Take the difference, and read us_app_to_person_registered on the service",
  "body": """<p>A number in no pool is unregistered. A number in a pool whose service reports <code>us_app_to_person_registered</code> as <code>false</code> is also unregistered, and the repair is different: that service needs a campaign, not that number a pool.</p>"""},
 {"h": "Join the 30034s by from, to separate the urgent from the latent",
  "body": """<p>Page <code>Messages.json</code> and group <code>error_code</code> <code>30034</code> by <code>from</code>. A gap with failures is live breakage. A gap with no traffic is a number that will fail the first time somebody uses it, which is worth fixing while it is cheap.</p>"""},
 {"h": "Add the number to the pool, then stop sending with a bare From",
  "body": """<p><code>POST /v1/Services/{ServiceSid}/PhoneNumbers</code> with <code>PhoneNumberSid=PN…</code>, and switch the send to <code>MessagingServiceSid=MG…</code>. Registration at the carrier takes up to 24 hours after that, so expect the number to keep failing briefly &mdash; with <code>30035</code> rather than <code>30034</code>, which is how you know it worked.</p>"""},
],
"verify": """<p>Re-run the script. Every SMS-capable US long code should sit in the pool of a Messaging Service that has a campaign.</p>
<pre><code class="language-bash">python3 twilio_10dlc_sender_pool_gap.py
# 11 US long code(s), 0 outside a registered sender pool</code></pre>""",
"code_intro": "Three lists and a difference: the account's numbers, each Messaging Service's pool, and the <code>30034</code>s from the Messages window. The classifier takes one number, the service holding it (or <code>None</code>) and that number's failures, which is why the difference between a gap that is breaking today and a gap that will break at launch is a test rather than a comment.",
"py_file": "twilio_10dlc_sender_pool_gap.py",
"py": '''"""Find SMS-capable US long codes that sit outside any registered A2P sender pool.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_10dlc_sender_pool_gap")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"

UNREGISTERED = "30034"
# Toll-free has its own verification path and its own failure code, 30032. A
# report that mixes the two sends people to the wrong console page.
TOLLFREE_NPA = {"800", "833", "844", "855", "866", "877", "888"}


def is_us_long_code(phone_number):
    """True for a +1 ten digit number that is not toll-free. Pure.

    Short codes, non-US numbers and toll-free numbers are all out of scope for
    10DLC, and each of them has a different registration story.
    """
    number = str(phone_number or "")
    if not number.startswith("+1") or len(number) != 12 or not number[1:].isdigit():
        return False
    return number[2:5] not in TOLLFREE_NPA


def sms_capable(number):
    return bool((number.get("capabilities") or {}).get("sms"))


def bare_from_share(failures):
    """The share of these failures sent with a From rather than a service SID.

    A bare From bypasses the Messaging Service, and therefore the campaign the
    service carries, which is how a gap survives a green compliance dashboard.
    """
    if not failures:
        return 0.0
    bare = len([m for m in failures if not m.get("messaging_service_sid")])
    return bare / float(len(failures))


def verdict(number, service, failures):
    """Classify one owned number. Pure.

    number is an IncomingPhoneNumbers row, service is the Messaging Service
    whose pool contains it or None, failures are that number's 30034 rows.
    Returns (state, detail).
    """
    phone = str(number.get("phone_number") or "")
    if not sms_capable(number):
        return ("not-in-scope", "capabilities.sms is false: not an SMS sender.")
    if not is_us_long_code(phone):
        return ("not-in-scope",
                "not a US long code, so 10DLC registration does not govern it. "
                "Toll-free numbers verify separately and fail with 30032.")

    if service is None:
        if failures:
            return ("sending-direct",
                    "%d x 30034 from a number that is in no Messaging Service "
                    "pool, %.0f%% of them sent with a bare From. A2P approval "
                    "attaches through the pool, so this number is UNREGISTERED "
                    "whatever the brand and campaign say."
                    % (len(failures), bare_from_share(failures) * 100))
        return ("outside-the-pool",
                "SMS capable US long code in no Messaging Service pool, with no "
                "traffic yet. The first US A2P send from it will 30034.")

    name = service.get("friendly_name") or service.get("sid") or "?"
    if not service.get("us_app_to_person_registered"):
        return ("pool-without-a-campaign",
                "in the pool of %s, which has no A2P campaign at all. The pool "
                "is not the problem here; the service is." % name)

    if failures:
        return ("registered-but-failing",
                "%d x 30034 from a number that is already in %s. Either it was "
                "added in the last two weeks and is still PENDING_REGISTRATION, "
                "or the brand is Sole Proprietor and this is the extra number "
                "that never registers." % (len(failures), name))

    return ("registered", "in the pool of %s, which has a campaign." % name)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_2010(session, url, key, limit=2000, **params):
    """Page a 2010-04-01 list. next_page_uri is a path, not a URL."""
    out = []
    params = dict(params, PageSize=1000)
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the Messages list for 30034s")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging the Messages list after this many rows")
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

    numbers = list_2010(session, "%s/Accounts/%s/IncomingPhoneNumbers.json"
                        % (BASE, account), "incoming_phone_numbers")

    pool = {}
    for service in list_v1(session, MSG + "/Services", "services"):
        for entry in list_v1(session, "%s/Services/%s/PhoneNumbers"
                             % (MSG, service["sid"]), "phone_numbers"):
            pool[str(entry.get("phone_number"))] = service

    since = (datetime.now(timezone.utc)
             - timedelta(days=args.days)).strftime("%Y-%m-%d")
    failures = {}
    for message in list_2010(session, "%s/Accounts/%s/Messages.json" % (BASE, account),
                             "messages", args.max_messages,
                             **{"DateSent>=": since}):
        if str(message.get("error_code") or "") == UNREGISTERED:
            failures.setdefault(str(message.get("from") or ""), []).append(message)

    in_scope = bad = 0
    for number in numbers:
        phone = str(number.get("phone_number") or "")
        state, detail = verdict(number, pool.get(phone), failures.get(phone, []))
        if state == "not-in-scope":
            continue
        in_scope += 1
        line = "%-23s %s  %s" % (state, phone, detail)
        if state == "registered":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("sending-direct", "outside-the-pool"):
            log.warning("  repair: POST %s/Services/{ServiceSid}/PhoneNumbers with "
                        "PhoneNumberSid=%s, then send with MessagingServiceSid "
                        "rather than a bare From", MSG, number.get("sid", "PN..."))
        elif state == "pool-without-a-campaign":
            log.warning("  repair: register a campaign on that Messaging Service "
                        "before touching the pool")
        else:
            log.warning("  repair: wait out the carrier registration window "
                        "before changing anything; removing and re-adding the "
                        "number restarts it")

    log.info("%d US long code(s), %d outside a registered sender pool",
             in_scope, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-10dlc-sender-pool-gap.mjs",
"js": '''/**
 * Find SMS-capable US long codes that sit outside any registered A2P sender pool.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';

const UNREGISTERED = '30034';
// Toll-free has its own verification path and its own failure code, 30032.
const TOLLFREE_NPA = new Set(['800', '833', '844', '855', '866', '877', '888']);

/**
 * True for a +1 ten digit number that is not toll-free. Pure. Short codes,
 * non-US numbers and toll-free numbers are all out of scope for 10DLC.
 */
export function isUsLongCode(phoneNumber) {
  const number = String(phoneNumber ?? '');
  if (!number.startsWith('+1') || number.length !== 12) return false;
  if (!/^[0-9]+$/.test(number.slice(1))) return false;
  return !TOLLFREE_NPA.has(number.slice(2, 5));
}

export function smsCapable(number) {
  return Boolean(number.capabilities?.sms);
}

/**
 * The share of these failures sent with a From rather than a service SID. A
 * bare From bypasses the Messaging Service, and therefore the campaign it
 * carries, which is how a gap survives a green compliance dashboard.
 */
export function bareFromShare(failures) {
  if (failures.length === 0) return 0;
  return failures.filter((m) => !m.messaging_service_sid).length / failures.length;
}

/**
 * Classify one owned number. Pure. number is an IncomingPhoneNumbers row,
 * service is the Messaging Service whose pool contains it or null, failures are
 * that number's 30034 rows. Returns [state, detail].
 */
export function verdict(number, service, failures) {
  const phone = String(number.phone_number ?? '');
  if (!smsCapable(number)) {
    return ['not-in-scope', 'capabilities.sms is false: not an SMS sender.'];
  }
  if (!isUsLongCode(phone)) {
    return ['not-in-scope',
      'not a US long code, so 10DLC registration does not govern it. Toll-free ' +
      'numbers verify separately and fail with 30032.'];
  }

  if (!service) {
    if (failures.length) {
      return ['sending-direct',
        `${failures.length} x 30034 from a number that is in no Messaging ` +
        `Service pool, ${(bareFromShare(failures) * 100).toFixed(0)}% of them ` +
        'sent with a bare From. A2P approval attaches through the pool, so this ' +
        'number is UNREGISTERED whatever the brand and campaign say.'];
    }
    return ['outside-the-pool',
      'SMS capable US long code in no Messaging Service pool, with no traffic ' +
      'yet. The first US A2P send from it will 30034.'];
  }

  const name = service.friendly_name ?? service.sid ?? '?';
  if (!service.us_app_to_person_registered) {
    return ['pool-without-a-campaign',
      `in the pool of ${name}, which has no A2P campaign at all. The pool is ` +
      'not the problem here; the service is.'];
  }

  if (failures.length) {
    return ['registered-but-failing',
      `${failures.length} x 30034 from a number that is already in ${name}. ` +
      'Either it was added in the last two weeks and is still ' +
      'PENDING_REGISTRATION, or the brand is Sole Proprietor and this is the ' +
      'extra number that never registers.'];
  }

  return ['registered', `in the pool of ${name}, which has a campaign.`];
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

async function list2010(auth, url, key, limit = 2000, extra = {}) {
  const out = [];
  let next = url;
  let params = { ...extra, PageSize: 1000 };
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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

  const numbers = await list2010(auth,
    `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`, 'incoming_phone_numbers');

  const pool = new Map();
  for (const service of await listV1(auth, `${MSG}/Services`, 'services')) {
    for (const entry of await listV1(auth,
      `${MSG}/Services/${service.sid}/PhoneNumbers`, 'phone_numbers')) {
      pool.set(String(entry.phone_number), service);
    }
  }

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 7) || 7;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const failures = new Map();
  const messages = await list2010(auth, `${BASE}/Accounts/${account}/Messages.json`,
    'messages', 20000, { 'DateSent>=': since });
  for (const message of messages) {
    if (String(message.error_code ?? '') !== UNREGISTERED) continue;
    const from = String(message.from ?? '');
    failures.set(from, [...(failures.get(from) ?? []), message]);
  }

  let inScope = 0;
  let bad = 0;
  for (const number of numbers) {
    const phone = String(number.phone_number ?? '');
    const [state, detail] = verdict(number, pool.get(phone) ?? null,
                                    failures.get(phone) ?? []);
    if (state === 'not-in-scope') continue;
    inScope += 1;
    const line = `${state.padEnd(23)} ${phone}  ${detail}`;
    if (state === 'registered') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'sending-direct' || state === 'outside-the-pool') {
      console.warn(`  repair: POST ${MSG}/Services/{ServiceSid}/PhoneNumbers ` +
                   `with PhoneNumberSid=${number.sid ?? 'PN...'}, then send with ` +
                   'MessagingServiceSid rather than a bare From');
    } else if (state === 'pool-without-a-campaign') {
      console.warn('  repair: register a campaign on that Messaging Service ' +
                   'before touching the pool');
    } else {
      console.warn('  repair: wait out the carrier registration window before ' +
                   'changing anything; removing and re-adding the number ' +
                   'restarts it');
    }
  }

  console.log(`${inScope} US long code(s), ${bad} outside a registered sender pool`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Five states, and the ones worth separating are the three that all render as &ldquo;this number 30034s&rdquo;: no pool at all, a pool on a service with no campaign, and a pool on a registered service where the number is simply new. They need three different actions, and one of those actions is to do nothing. The scope tests keep toll-free numbers out, because their failure code is 30032 and their console page is somewhere else.",
"test_py_file": "test_twilio_10dlc_sender_pool_gap.py",
"test_py": '''from twilio_10dlc_sender_pool_gap import (bare_from_share, is_us_long_code,
                                             verdict)

LONG_CODE = {"sid": "PN1", "phone_number": "+15125550123",
             "capabilities": {"sms": True, "voice": True}}
REGISTERED = {"sid": "MG1", "friendly_name": "prod",
              "us_app_to_person_registered": True}
UNREGISTERED_SERVICE = {"sid": "MG2", "friendly_name": "staging",
                        "us_app_to_person_registered": False}


def fail(**kw):
    return dict({"error_code": 30034, "from": "+15125550123"}, **kw)


def test_a_number_in_no_pool_that_is_failing_is_sending_direct():
    state, detail = verdict(LONG_CODE, None, [fail(), fail()])
    assert state == "sending-direct"
    assert "100%" in detail and "UNREGISTERED" in detail


def test_a_number_in_no_pool_with_no_traffic_is_latent_not_broken():
    state, detail = verdict(LONG_CODE, None, [])
    assert state == "outside-the-pool"
    assert "will 30034" in detail


def test_a_pool_on_a_service_with_no_campaign_points_at_the_service():
    state, detail = verdict(LONG_CODE, UNREGISTERED_SERVICE, [fail()])
    assert state == "pool-without-a-campaign"
    assert "staging" in detail


def test_a_pooled_number_that_still_fails_may_just_be_new():
    # The one finding here where the right action is to wait rather than change
    # anything, so it must not share a state with the gaps.
    state, detail = verdict(LONG_CODE, REGISTERED, [fail()])
    assert state == "registered-but-failing"
    assert "PENDING_REGISTRATION" in detail


def test_a_pooled_number_with_no_failures_is_clean():
    assert verdict(LONG_CODE, REGISTERED, [])[0] == "registered"


def test_toll_free_is_out_of_scope_and_says_why():
    tf = dict(LONG_CODE, phone_number="+18885550123")
    state, detail = verdict(tf, None, [])
    assert state == "not-in-scope"
    assert "30032" in detail


def test_a_number_that_cannot_send_sms_is_out_of_scope():
    voice_only = dict(LONG_CODE, capabilities={"sms": False, "voice": True})
    assert verdict(voice_only, None, [fail()])[0] == "not-in-scope"


def test_scope_is_us_ten_digit_long_codes_only():
    assert is_us_long_code("+15125550123")
    assert not is_us_long_code("+442071838750")
    assert not is_us_long_code("+18445550123")
    assert not is_us_long_code("12345")
    assert not is_us_long_code(None)


def test_a_send_carrying_a_service_sid_is_not_a_bare_from():
    assert bare_from_share([fail(messaging_service_sid="MG1"), fail()]) == 0.5
''',
"test_js_file": "twilio-10dlc-sender-pool-gap.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bareFromShare, isUsLongCode, verdict }
  from './twilio-10dlc-sender-pool-gap.mjs';

const LONG_CODE = { sid: 'PN1', phone_number: '+15125550123',
  capabilities: { sms: true, voice: true } };
const REGISTERED = { sid: 'MG1', friendly_name: 'prod',
  us_app_to_person_registered: true };
const UNREGISTERED_SERVICE = { sid: 'MG2', friendly_name: 'staging',
  us_app_to_person_registered: false };

const fail = (extra = {}) => ({ error_code: 30034, from: '+15125550123', ...extra });

test('a number in no pool that is failing is sending direct', () => {
  const [state, detail] = verdict(LONG_CODE, null, [fail(), fail()]);
  assert.equal(state, 'sending-direct');
  assert.match(detail, /100%/);
  assert.match(detail, /UNREGISTERED/);
});

test('a number in no pool with no traffic is latent, not broken', () => {
  const [state, detail] = verdict(LONG_CODE, null, []);
  assert.equal(state, 'outside-the-pool');
  assert.match(detail, /will 30034/);
});

test('a pool on a service with no campaign points at the service', () => {
  const [state, detail] = verdict(LONG_CODE, UNREGISTERED_SERVICE, [fail()]);
  assert.equal(state, 'pool-without-a-campaign');
  assert.match(detail, /staging/);
});

test('a pooled number that still fails may just be new', () => {
  const [state, detail] = verdict(LONG_CODE, REGISTERED, [fail()]);
  assert.equal(state, 'registered-but-failing');
  assert.match(detail, /PENDING_REGISTRATION/);
});

test('a pooled number with no failures is clean', () => {
  assert.equal(verdict(LONG_CODE, REGISTERED, [])[0], 'registered');
});

test('toll free is out of scope and says why', () => {
  const [state, detail] = verdict({ ...LONG_CODE, phone_number: '+18885550123' },
                                  null, []);
  assert.equal(state, 'not-in-scope');
  assert.match(detail, /30032/);
});

test('a number that cannot send sms is out of scope', () => {
  const voiceOnly = { ...LONG_CODE, capabilities: { sms: false, voice: true } };
  assert.equal(verdict(voiceOnly, null, [fail()])[0], 'not-in-scope');
});

test('scope is us ten digit long codes only', () => {
  assert.equal(isUsLongCode('+15125550123'), true);
  assert.equal(isUsLongCode('+442071838750'), false);
  assert.equal(isUsLongCode('+18445550123'), false);
  assert.equal(isUsLongCode('12345'), false);
  assert.equal(isUsLongCode(null), false);
});

test('a send carrying a service sid is not a bare from', () => {
  assert.equal(bareFromShare([fail({ messaging_service_sid: 'MG1' }), fail()]), 0.5);
});
''',
"faq": [
 ("The brand is APPROVED and the campaign VERIFIED. How can a number be unregistered?",
  "Because A2P approval attaches to numbers through the sender pool of the Messaging Service that carries the campaign, and carriers register each number individually after the campaign is approved. A number you own but never added to that pool was never submitted to anyone."),
 ("Does sending with From instead of MessagingServiceSid actually matter?",
  "For US A2P, yes. A bare From bypasses the Messaging Service, and the campaign lives on the service. It also loses everything else the service does: sender selection, sticky sender, the pool-level status callback and scheduling."),
 ("How do I tell this apart from a campaign that was never registered?",
  "By where the number is. If it is in no pool at all, the number is the gap. If it is in a pool whose service reports us_app_to_person_registered as false, the service is the gap and adding numbers to it changes nothing. The script reports those as different states for that reason."),
 ("The number is in the pool and it still 30034s. What now?",
  "Wait, probably. Carrier registration after a number joins a pool takes up to 24 hours and can show as PENDING_REGISTRATION for longer after a campaign approval backlog. The other cause is a Sole Proprietor brand, which allows exactly one number on its one campaign, so any extras stay unregistered forever."),
 ("Why not just check the console?",
  "The A2P views are organised by brand, campaign and Messaging Service, so a number in no service appears in none of them. The gap is between two lists, and only one of those lists is on the compliance side."),
],
"related": [
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign attached"),
 ("/twilio/messaging-service-empty-sender-pool/", "An empty sender pool and 21704 on every send"),
 ("/twilio/sender-pending-carrier-provisioning/", "30035 and 30024 while the carrier catches up"),
],
"citations": [CITE_MSPN, CITE_30034, CITE_PNREG, CITE_SERVICE],
},

{
"slug": "sender-pending-carrier-provisioning",
"title": "30035 and 30024 are a clock, not a configuration mistake",
"description": "A new sender fails for up to 24 hours while carrier routing catches up. Removing and re-adding the number restarts the clock instead of ending it.",
"h1": "30035 and 30024 are a clock, not a configuration mistake",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30035", "twilio 30024", "number pending registration",
             "numeric sender id not provisioned", "twilio sender provisioning delay"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The number was added to the Messaging Service an hour before the launch, which felt like plenty of margin. Sends come back <code>30035</code>. Somebody removes the number and adds it again, because that is what you do when a config change did not take. The clock they were forty minutes from the end of has just been set back to zero, and they will do it twice more before the day is out.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and keep <code>error_code</code> <code>30035</code> (number pending registration) and <code>30024</code> (numeric sender ID not provisioned on the carrier), grouped by <code>from</code>. Confirm the number is in a pool with <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code>.</p>
<p>Then read the timestamps, not the codes. The age of the <strong>first</strong> failure against the 24-hour provisioning window is the entire diagnosis: inside it, wait; past it, open a ticket with the <code>PN…</code> SID. And if the most recent send from that number succeeded, the clock already ran out and there is nothing to do.</p>""",
"problem": """<p>These two codes look like every other configuration error and they are not one. Nothing is misconfigured: the number is in the pool, the campaign is verified, the brand is approved. The carrier's routing tables simply have not been updated yet, and that update happens on the carrier's schedule, which the API cannot influence and cannot report progress on.</p>
<p>So the only two useful facts are how long it has been failing and whether it is still failing. Neither is a field anywhere. <code>Messages.json</code> is the only surface that records a time, so a diagnosis here is arithmetic on <code>date_sent</code> and nothing else.</p>
<p>And the natural response is the harmful one. Removing the number from the Messaging Service and adding it back is a deregistration followed by a registration, which puts the number through <code>PENDING_DEREGISTRATION</code> and then back to <code>PENDING_REGISTRATION</code>. Every retry of that adds another window. Teams that do this three times spend three days on a problem that resolves itself in one.</p>""",
"why": """<p><strong>Waiting does not look like an action.</strong> During an incident, doing nothing is the hardest thing to justify, so somebody changes something. The change here is the one thing that measurably makes it worse, and it produces no error to tell you so.</p>
<p><strong>There is no progress indicator.</strong> The number's A2P status is not exposed as a countdown, and no resource says how far through the window you are. The first failure's <code>date_sent</code> is a proxy for the start of the clock, and it is the best one available.</p>
<p><strong>The two codes are not the same problem.</strong> <code>30035</code> is a registration that is in flight. <code>30024</code> is the carrier refusing that numeric sender for the destination, which can also mean the sender is wrong for the country rather than merely new. A window that only ever shows <code>30024</code> is worth reading differently from one that shows <code>30035</code>.</p>
<p><strong>A number outside every pool produces neither.</strong> If a sender is failing and it is in no Messaging Service, nothing has been submitted for it to be waiting on: the code you will actually see is <code>30034</code>, and the fix is to add it to a pool. Checking pool membership is what stops this report from telling somebody to wait forever.</p>""",
"steps": [
 {"h": "Collect the provisioning failures per sender",
  "body": """<p>Page <code>Messages.json</code> over two or three days and keep the rows where <code>error_code</code> is <code>30035</code> or <code>30024</code>, grouped by <code>from</code>. Keep the sender's successful rows too &mdash; a success after the last failure is the cleanest possible answer.</p>"""},
 {"h": "Confirm the sender is actually in a pool",
  "body": """<p><code>GET /v1/Services</code>, then <code>GET /v1/Services/{ServiceSid}/PhoneNumbers</code>. A failing number that is in no pool is not waiting on anything, and telling somebody to wait on it is the worst outcome this report can produce.</p>"""},
 {"h": "Order by date_sent and take the oldest failure as the start",
  "body": """<p><code>date_sent</code> is RFC 2822. Parse it leniently: a row you cannot date is a row you cannot use for the clock, and dropping the whole sender because of one is worse than skipping it. The oldest failure is when the window started, as far as anything observable is concerned.</p>"""},
 {"h": "Compare its age against 24 hours",
  "body": """<p>Under 24 hours and still failing: wait, and route the traffic through a sender that is already registered. Over 24 hours and still failing: this is no longer a clock, and it needs a Support ticket quoting the <code>PN…</code> SID and the Messaging Service.</p>"""},
 {"h": "Check whether it already fixed itself",
  "body": """<p>If the most recent message from that sender went through, provisioning completed while nobody was looking. Report it as resolved rather than as an open failure &mdash; otherwise the sender stays on the incident list and somebody eventually removes and re-adds it.</p>"""},
 {"h": "Do not touch the assignment while the clock runs",
  "body": """<p>No API repair, and specifically no repair that involves the pool. Removing and re-adding restarts the window. If the traffic cannot wait, send it from a number that was registered days ago; that is a routing change in your code, not a change to the number that is provisioning.</p>"""},
],
"verify": """<p>Re-run after the window has passed. Every sender that was waiting should read <code>provisioned</code> or drop out of the report entirely.</p>
<pre><code class="language-bash">python3 twilio_sender_provisioning_clock.py --days 3
# 1 sender(s) with provisioning errors, 0 still waiting</code></pre>""",
"code_intro": "The classifier takes one sender's messages, the current time and whether the number is in a pool, and returns a state. Passing the clock in rather than reading it is what makes the interesting cases testable: two hours in, thirty hours in, and already recovered are three different answers from the same rows, and the only thing separating them is <code>now</code>.",
"py_file": "twilio_sender_provisioning_clock.py",
"py": '''"""Report senders failing on 30035 or 30024, and say whether waiting is still the answer.

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
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_sender_provisioning_clock")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"

# 30035 is a registration in flight. 30024 is the carrier refusing the numeric
# sender for that destination, which is not always a clock at all.
PROVISIONING = {"30035": "number pending registration",
                "30024": "numeric sender ID not provisioned on the carrier"}
WINDOW_HOURS = 24


def parse_when(value):
    """date_sent is RFC 2822, not ISO 8601. Returns epoch seconds, or None.

    Lenient: a row that cannot be dated is a row that cannot start the clock,
    and dropping the whole sender over one malformed timestamp is worse.
    """
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError):
        return None


def ordered(messages):
    """Oldest first. Undated rows keep their original order at the end."""
    keyed = [(parse_when(m.get("date_sent")), i, m) for i, m in enumerate(messages)]
    dated = sorted(k for k in keyed if k[0] is not None)
    undated = [k for k in keyed if k[0] is None]
    return [m for _w, _i, m in dated] + [m for _w, _i, m in undated]


def is_provisioning(message):
    return str(message.get("error_code") or "") in PROVISIONING


def codes_seen(messages):
    """The provisioning codes present, sorted, without repeats."""
    return sorted({str(m.get("error_code")) for m in messages
                   if is_provisioning(m)})


def verdict(messages, now, in_pool):
    """Classify one sender's window. Pure.

    messages are every row from that sender, now is epoch seconds, in_pool says
    whether the number is in any Messaging Service pool. Returns (state, detail).
    """
    rows = ordered(messages)
    failing = [m for m in rows if is_provisioning(m)]
    if not failing:
        return ("clean", "no 30035 or 30024 from this sender in the window.")

    codes = codes_seen(failing)
    named = ", ".join(codes)

    if not is_provisioning(rows[-1]):
        return ("provisioned",
                "%d x %s, and the most recent send from this number went "
                "through. The carrier caught up while nobody was watching."
                % (len(failing), named))

    if not in_pool:
        return ("not-in-any-pool",
                "%d x %s from a number that is in no Messaging Service sender "
                "pool. Nothing has been submitted for this to be waiting on, so "
                "waiting will not end it." % (len(failing), named))

    started = parse_when(failing[0].get("date_sent"))
    if started is None:
        return ("undated",
                "%d x %s, but no failing row carries a parseable date_sent, so "
                "there is no clock to read." % (len(failing), named))

    tail = ""
    if codes == ["30024"]:
        tail = (" Only 30024 here and never 30035: that is the carrier refusing "
                "the numeric sender for the destination, which is not always a "
                "registration in flight. Check the destination country too.")

    hours = (now - started) / 3600.0
    if hours < WINDOW_HOURS:
        return ("waiting",
                "%d x %s, first seen %.1f h ago. Carrier provisioning takes up "
                "to %d h. Do not remove and re-add the number: that restarts "
                "the clock.%s" % (len(failing), named, hours, WINDOW_HOURS, tail))

    return ("overdue",
            "%d x %s, first seen %.1f h ago, past the %d h provisioning window "
            "and still failing.%s"
            % (len(failing), named, hours, WINDOW_HOURS, tail))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. No ErrorCode filter exists on this resource."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=3,
                    help="how far back to read the Messages list")
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

    pool = {}
    for service in list_v1(session, MSG + "/Services", "services"):
        for entry in list_v1(session, "%s/Services/%s/PhoneNumbers"
                             % (MSG, service["sid"]), "phone_numbers"):
            pool[str(entry.get("phone_number"))] = (service, entry)

    since = (datetime.now(timezone.utc)
             - timedelta(days=args.days)).strftime("%Y-%m-%d")
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages sent since %s", since)
        return 0

    by_sender = {}
    for message in messages:
        by_sender.setdefault(str(message.get("from") or ""), []).append(message)

    now = time.time()
    seen = waiting = 0
    for sender in sorted(by_sender):
        rows = by_sender[sender]
        if not any(is_provisioning(m) for m in rows):
            continue
        seen += 1
        service, entry = pool.get(sender, (None, None))
        state, detail = verdict(rows, now, service is not None)
        line = "%-16s %s  %s" % (state, sender, detail)
        if state == "provisioned":
            log.info(line)
            continue
        waiting += 1
        log.warning(line)
        if state == "waiting":
            log.warning("  repair: none, and specifically not the pool. Route "
                        "this traffic through a sender registered days ago "
                        "until the window closes.")
        elif state == "overdue":
            log.warning("  repair: open Twilio Support quoting %s on %s. Past "
                        "the window this is no longer a provisioning delay.",
                        (entry or {}).get("sid", "the PN SID"),
                        (service or {}).get("sid", "the Messaging Service"))
        elif state == "not-in-any-pool":
            log.warning("  repair: add the number to the Messaging Service that "
                        "carries the campaign, then wait out the window once.")

    log.info("%d sender(s) with provisioning errors, %d still waiting",
             seen, waiting)
    return 1 if waiting else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sender-provisioning-clock.mjs",
"js": '''/**
 * Report senders failing on 30035 or 30024, and say whether waiting is still the answer.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';

// 30035 is a registration in flight. 30024 is the carrier refusing the numeric
// sender for that destination, which is not always a clock at all.
const PROVISIONING = {
  30035: 'number pending registration',
  30024: 'numeric sender ID not provisioned on the carrier',
};
const WINDOW_HOURS = 24;

/** date_sent is RFC 2822, not ISO 8601. Returns epoch seconds, or null. */
export function parseWhen(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isNaN(ms) ? null : ms / 1000;
}

/** Oldest first. Undated rows keep their original order at the end. */
export function ordered(messages) {
  const keyed = messages.map((m, i) => [parseWhen(m.date_sent), i, m]);
  const dated = keyed.filter(([w]) => w !== null)
    .sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  const undated = keyed.filter(([w]) => w === null);
  return [...dated, ...undated].map(([, , m]) => m);
}

export function isProvisioning(message) {
  return Object.prototype.hasOwnProperty.call(
    PROVISIONING, String(message.error_code ?? ''));
}

/** The provisioning codes present, sorted, without repeats. */
export function codesSeen(messages) {
  return [...new Set(messages.filter(isProvisioning)
    .map((m) => String(m.error_code)))].sort();
}

/**
 * Classify one sender's window. Pure. messages are every row from that sender,
 * now is epoch seconds, inPool says whether the number is in any Messaging
 * Service pool. Returns [state, detail].
 */
export function verdict(messages, now, inPool) {
  const rows = ordered(messages);
  const failing = rows.filter(isProvisioning);
  if (failing.length === 0) {
    return ['clean', 'no 30035 or 30024 from this sender in the window.'];
  }

  const codes = codesSeen(failing);
  const named = codes.join(', ');

  if (!isProvisioning(rows[rows.length - 1])) {
    return ['provisioned',
      `${failing.length} x ${named}, and the most recent send from this number ` +
      'went through. The carrier caught up while nobody was watching.'];
  }

  if (!inPool) {
    return ['not-in-any-pool',
      `${failing.length} x ${named} from a number that is in no Messaging ` +
      'Service sender pool. Nothing has been submitted for this to be waiting ' +
      'on, so waiting will not end it.'];
  }

  const started = parseWhen(failing[0].date_sent);
  if (started === null) {
    return ['undated',
      `${failing.length} x ${named}, but no failing row carries a parseable ` +
      'date_sent, so there is no clock to read.'];
  }

  let tail = '';
  if (codes.length === 1 && codes[0] === '30024') {
    tail = ' Only 30024 here and never 30035: that is the carrier refusing the ' +
      'numeric sender for the destination, which is not always a registration ' +
      'in flight. Check the destination country too.';
  }

  const hours = (now - started) / 3600;
  if (hours < WINDOW_HOURS) {
    return ['waiting',
      `${failing.length} x ${named}, first seen ${hours.toFixed(1)} h ago. ` +
      `Carrier provisioning takes up to ${WINDOW_HOURS} h. Do not remove and ` +
      `re-add the number: that restarts the clock.${tail}`];
  }

  return ['overdue',
    `${failing.length} x ${named}, first seen ${hours.toFixed(1)} h ago, past ` +
    `the ${WINDOW_HOURS} h provisioning window and still failing.${tail}`];
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

async function listMessages(auth, account, since, limit = 20000) {
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

async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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

  const pool = new Map();
  for (const service of await listV1(auth, `${MSG}/Services`, 'services')) {
    for (const entry of await listV1(auth,
      `${MSG}/Services/${service.sid}/PhoneNumbers`, 'phone_numbers')) {
      pool.set(String(entry.phone_number), [service, entry]);
    }
  }

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 3) || 3;
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  const bySender = new Map();
  for (const message of messages) {
    const from = String(message.from ?? '');
    bySender.set(from, [...(bySender.get(from) ?? []), message]);
  }

  const now = Date.now() / 1000;
  let seen = 0;
  let waiting = 0;
  for (const sender of [...bySender.keys()].sort()) {
    const rows = bySender.get(sender);
    if (!rows.some(isProvisioning)) continue;
    seen += 1;
    const [service, entry] = pool.get(sender) ?? [null, null];
    const [state, detail] = verdict(rows, now, service !== null);
    const line = `${state.padEnd(16)} ${sender}  ${detail}`;
    if (state === 'provisioned') { console.log(line); continue; }
    waiting += 1;
    console.warn(line);
    if (state === 'waiting') {
      console.warn('  repair: none, and specifically not the pool. Route this ' +
                   'traffic through a sender registered days ago until the ' +
                   'window closes.');
    } else if (state === 'overdue') {
      console.warn(`  repair: open Twilio Support quoting ` +
                   `${entry?.sid ?? 'the PN SID'} on ` +
                   `${service?.sid ?? 'the Messaging Service'}. Past the window ` +
                   'this is no longer a provisioning delay.');
    } else if (state === 'not-in-any-pool') {
      console.warn('  repair: add the number to the Messaging Service that ' +
                   'carries the campaign, then wait out the window once.');
    }
  }

  console.log(`${seen} sender(s) with provisioning errors, ${waiting} still waiting`);
  process.exitCode = waiting ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The same rows produce three different answers depending on <code>now</code>, which is exactly why the clock is a parameter and not a call to the system time. The other two cases guard the ends: a sender in no pool must never be told to wait, and a window showing only <code>30024</code> has to say that it might not be a registration at all.",
"test_py_file": "test_twilio_sender_provisioning_clock.py",
"test_py": '''from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from twilio_sender_provisioning_clock import codes_seen, verdict

T0 = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)
START = T0.timestamp()
HOUR = 3600.0


def at(minutes, **kw):
    row = {"date_sent": format_datetime(T0 + timedelta(minutes=minutes)),
           "from": "+15125550123"}
    row.update(kw)
    return row


def test_a_sender_with_no_provisioning_codes_is_clean():
    state, _ = verdict([at(0), at(5, error_code=30007)], START + HOUR, True)
    assert state == "clean"


def test_two_hours_in_and_still_failing_says_wait():
    rows = [at(0, error_code=30035), at(60, error_code=30035)]
    state, detail = verdict(rows, START + 2 * HOUR, True)
    assert state == "waiting"
    assert "2.0 h ago" in detail
    assert "restarts the clock" in detail


def test_the_same_rows_past_the_window_are_overdue():
    rows = [at(0, error_code=30035), at(60, error_code=30035)]
    state, detail = verdict(rows, START + 30 * HOUR, True)
    assert state == "overdue"
    assert "past the 24 h" in detail


def test_a_success_after_the_last_failure_means_it_already_cleared():
    rows = [at(0, error_code=30035), at(60, error_code=30035), at(120)]
    state, detail = verdict(rows, START + 3 * HOUR, True)
    assert state == "provisioned"
    assert "caught up" in detail


def test_a_sender_in_no_pool_is_never_told_to_wait():
    # Nothing was submitted, so the window is not running. Telling somebody to
    # wait here costs them the whole day.
    state, detail = verdict([at(0, error_code=30035)], START + HOUR, False)
    assert state == "not-in-any-pool"
    assert "waiting will not end it" in detail


def test_a_window_of_only_30024_is_flagged_as_maybe_not_a_clock():
    state, detail = verdict([at(0, error_code=30024)], START + HOUR, True)
    assert state == "waiting"
    assert "destination country" in detail


def test_a_mixed_window_is_not_flagged_that_way():
    rows = [at(0, error_code=30024), at(10, error_code=30035)]
    assert codes_seen(rows) == ["30024", "30035"]
    assert "destination country" not in verdict(rows, START + HOUR, True)[1]


def test_failures_with_no_usable_timestamp_report_that_rather_than_guessing():
    rows = [{"date_sent": "not a date", "error_code": 30035}]
    state, detail = verdict(rows, START + HOUR, True)
    assert state == "undated"
    assert "no clock to read" in detail
''',
"test_js_file": "twilio-sender-provisioning-clock.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { codesSeen, verdict } from './twilio-sender-provisioning-clock.mjs';

const T0 = Date.UTC(2026, 7, 24, 12, 0, 0);
const START = T0 / 1000;
const HOUR = 3600;

const at = (minutes, extra = {}) => ({
  date_sent: new Date(T0 + minutes * 60000).toUTCString(),
  from: '+15125550123',
  ...extra,
});

test('a sender with no provisioning codes is clean', () => {
  assert.equal(verdict([at(0), at(5, { error_code: 30007 })],
                       START + HOUR, true)[0], 'clean');
});

test('two hours in and still failing says wait', () => {
  const rows = [at(0, { error_code: 30035 }), at(60, { error_code: 30035 })];
  const [state, detail] = verdict(rows, START + 2 * HOUR, true);
  assert.equal(state, 'waiting');
  assert.match(detail, /2\\.0 h ago/);
  assert.match(detail, /restarts the clock/);
});

test('the same rows past the window are overdue', () => {
  const rows = [at(0, { error_code: 30035 }), at(60, { error_code: 30035 })];
  const [state, detail] = verdict(rows, START + 30 * HOUR, true);
  assert.equal(state, 'overdue');
  assert.match(detail, /past the 24 h/);
});

test('a success after the last failure means it already cleared', () => {
  const rows = [at(0, { error_code: 30035 }), at(60, { error_code: 30035 }), at(120)];
  const [state, detail] = verdict(rows, START + 3 * HOUR, true);
  assert.equal(state, 'provisioned');
  assert.match(detail, /caught up/);
});

test('a sender in no pool is never told to wait', () => {
  const [state, detail] = verdict([at(0, { error_code: 30035 })],
                                  START + HOUR, false);
  assert.equal(state, 'not-in-any-pool');
  assert.match(detail, /waiting will not end it/);
});

test('a window of only 30024 is flagged as maybe not a clock', () => {
  const [state, detail] = verdict([at(0, { error_code: 30024 })],
                                  START + HOUR, true);
  assert.equal(state, 'waiting');
  assert.match(detail, /destination country/);
});

test('a mixed window is not flagged that way', () => {
  const rows = [at(0, { error_code: 30024 }), at(10, { error_code: 30035 })];
  assert.deepEqual(codesSeen(rows), ['30024', '30035']);
  assert.doesNotMatch(verdict(rows, START + HOUR, true)[1], /destination country/);
});

test('failures with no usable timestamp report that rather than guessing', () => {
  const rows = [{ date_sent: 'not a date', error_code: 30035 }];
  const [state, detail] = verdict(rows, START + HOUR, true);
  assert.equal(state, 'undated');
  assert.match(detail, /no clock to read/);
});
''',
"faq": [
 ("How long does carrier provisioning actually take?",
  "Up to 24 hours after the number joins a Messaging Service, and usually far less. The number sits at PENDING_REGISTRATION during that time, and moving it between services puts it through PENDING_DEREGISTRATION first, which is why a move costs more than an add."),
 ("Why does removing and re-adding the number make it worse?",
  "Because it is a deregistration followed by a registration. The carrier starts the routing update from scratch, so each attempt adds another window rather than shortening the current one. The check exists mostly to give somebody a reason not to do it."),
 ("What is the difference between 30035 and 30024?",
  "30035 is a registration in flight: the number is submitted and the carrier has not finished. 30024 is the carrier refusing that numeric sender for the destination, which can be a provisioning delay or can mean the sender is not valid for that country at all. A window that only ever shows 30024 deserves a second look at where you are sending."),
 ("What if the number is not in any Messaging Service?",
  "Then nothing is provisioning and waiting achieves nothing. That case usually shows up as 30034 rather than 30035, and the fix is to add the number to the service that carries the campaign. The script reports it as its own state so nobody is told to wait on a submission that was never made."),
 ("Can I poll a status field instead of reading messages?",
  "Not usefully. There is no countdown and no progress field on the number or the pool entry, so the first failing send is the only observable start of the clock. That is why this check is arithmetic on date_sent rather than a status read."),
],
"related": [
 ("/twilio/number-missing-from-campaign-sender-pool/", "A 10DLC number that is in no sender pool at all"),
 ("/twilio/a2p-campaign-stuck-in-progress/", "A campaign parked at IN_PROGRESS is not live"),
 ("/twilio/tollfree-number-not-verified/", "An unverified toll-free number blocks all US SMS"),
],
"citations": [CITE_30035, CITE_30024, CITE_MSPN, CITE_A2P],
},

]
