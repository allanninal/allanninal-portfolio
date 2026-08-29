#!/usr/bin/env python3
"""/twilio/ field notes, batch F — the writing.

Four messaging failures that all live in the same list resource and all cost
money in a way no error page shows you: a fraud block that lifts before anyone
looks, a rendered template that never becomes a Message row at all, an encoding
switch that triples the segment count with no error code whatsoever, and a send
loop that outruns the one long code it was pointed at.

The constraint that shapes every script here is that `GET .../Messages.json`
has **no** `Status` and no `ErrorCode` filter. The documented parameters are
`To`, `From`, `DateSent`, `DateSent<`, `DateSent>` and paging, and that is the
whole list. Every error-code audit in this batch pages the window and filters
client-side, which is precisely why so few accounts have one. Where the send is
rejected before a Message row exists — 21617 is the example here — the Monitor
Alerts list is the only read-only path to it.

Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run.
"""

CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_30450 = ("Error 30450: message delivery blocked — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30450")
CITE_PUMPING = ("SMS Pumping Protection — Twilio Docs",
                "https://www.twilio.com/docs/messaging/features/"
                "sms-pumping-protection-programmable-messaging")
CITE_21617 = ("Error 21617: message body exceeds 1600 characters — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21617")
CITE_30001 = ("Error 30001: queue overflow — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30001")
CITE_21611 = ("Error 21611: this From number has exceeded the queue limit — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21611")
CITE_QUEUEING = ("Scaling, queueing and latency — Twilio Docs",
                 "https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_SERVICE_PN = ("Messaging Service PhoneNumber resource — Twilio Docs",
                   "https://www.twilio.com/docs/messaging/api/phonenumber-resource")
CITE_SERVICES = ("Messaging Services — Twilio Docs",
                 "https://www.twilio.com/docs/messaging/services")
CITE_USAGE = ("Usage Record resource — Twilio Docs",
              "https://www.twilio.com/docs/usage/api/usage-record")

GUIDES = [

{
"slug": "sms-pumping-protection-30450",
"title": "SMS Pumping Protection blocks legitimate OTPs with 30450",
"description": "Sends to one country start failing with error_code 30450, then recover on their own. The Messages list has no error filter, so nothing catches the window.",
"h1": "SMS Pumping Protection blocks legitimate OTPs with 30450",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30450", "twilio message delivery blocked",
             "sms pumping protection", "twilio riskcheck disable",
             "twilio global safe list"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The one-time passcodes were arriving. Then, for one country, they stopped: <code>error_code</code> <code>30450</code>, a few hundred of them, over about twenty minutes. By the time the first support ticket reached anyone the sends had resumed on their own and every dashboard was green again. Nothing in your code changed, nothing in the account changed, and there is nothing left to point at &mdash; except a login page where a few hundred people could not get in.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, keep the rows where <code>error_code</code> is <code>30450</code> or <code>30485</code>, and group them by the dialling code of <code>to</code>. Record the first and last blocked timestamp in each group.</p>
<p>The shape of that window is the diagnosis. A bounded burst against one prefix that stopped on its own is SMS Pumping Protection, not a carrier and not your code. The Messages list has <strong>no</strong> <code>Status</code> or <code>ErrorCode</code> filter, so the grouping has to happen in your own process.</p>""",
"problem": """<p>Twilio's fraud heuristics watch for SMS pumping: traffic artificially inflated against expensive destinations so that somebody downstream collects the termination fee. When your traffic pattern resembles that shape against an unusual destination, the protection applies a temporary block on that destination or region and refuses the sends with <code>30450</code>.</p>
<p>The word doing the damage is <em>temporary</em>. The block lifts by itself, usually in the fifteen to thirty minute range, which means that by the time anybody investigates, the thing to investigate is gone. Delivery rate for the day barely moves. The account-wide error count is a rounding error. The only durable evidence is an integer on a few hundred Message resources that nobody is reading, in a list you cannot query by error code.</p>
<p>And it lands on the worst possible traffic. Pumping protection exists because OTP routes are what fraudsters pump, so OTP routes are what it guards &mdash; and an OTP is the one message where a twenty minute gap is a login outage rather than a delay.</p>""",
"why": """<p><strong>The heuristic judges the destination, not your intent.</strong> A genuine expansion into a new country looks, from the outside, exactly like the opening move of a pumping attack: sudden volume, unfamiliar prefix, one message per number, no replies. Nothing about being legitimate makes your traffic look different.</p>
<p><strong>The block is not a field on anything.</strong> No resource says <em>this destination is currently blocked</em>. There is no flag on the Account, none on the Messaging Service, none on the number. The only read-only evidence that it happened is <code>error_code</code> on the messages that were refused, which makes this audit arithmetic over failed sends or nothing at all.</p>
<p><strong>The Messages list cannot be queried by error.</strong> <code>Messages.json</code> takes <code>To</code>, <code>From</code>, <code>DateSent</code> and paging. There is no <code>ErrorCode</code> parameter and no <code>Status</code> parameter, so finding a two hundred message burst inside a day of traffic means paging the day and filtering it yourself.</p>
<p><strong>Self-healing failures never get owned.</strong> Anything that recovers before the investigation starts gets recorded as <em>a blip</em>, filed under carrier weirdness, and hit again next month. The window is the one artefact that turns it into a fact: <em>eleven minutes, one prefix, ninety-four messages, stopped at 14:02</em> is a thing you can safe-list against.</p>""",
"steps": [
 {"h": "Page the Messages list over a bounded window",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. Bound it by days and by a hard message cap. Three days is usually the right window: long enough to hold the burst, short enough that you are not paging a million rows to find two hundred.</p>"""},
 {"h": "Keep 30450 and 30485, read as integers",
  "body": """<p><code>error_code</code> is <code>null</code> on healthy messages and a number on failed ones. A comparison against the string <code>"30450"</code> matches nothing and reports a clean account, which is the failure mode this whole check exists to avoid. Keep both codes: they come from the same protection and splitting them tells you nothing you can act on.</p>"""},
 {"h": "Group by dialling code, not by number",
  "body": """<p>The block is scoped to a destination or a region, so the per-number view scatters the evidence across hundreds of rows that each look like a one-off. Bucketing on the country code turns them back into one event with a size. Match the code longest-first &mdash; <code>880</code> before <code>88</code>, <code>1</code> last &mdash; or every Bangladeshi number lands in the North American bucket.</p>"""},
 {"h": "Read the window, because the window is the verdict",
  "body": """<p>Take the first and last blocked <code>date_sent</code> in each group. A short span that ended an hour ago is the temporary block doing its job badly: it has already lifted, and it will come back. A span that is still producing failures right now is a different conversation, and it is the one that goes to Support.</p>"""},
 {"h": "Safe-list the route, then re-run over the same window",
  "body": """<p>For destinations you have verified are real customers, add the numbers or prefixes to the Global Safe List (Console &rarr; Messaging &rarr; Settings &rarr; Global Safe List), or send that specific traffic with <code>RiskCheck=disable</code>. Leave RiskCheck on everywhere else &mdash; it is protecting the same OTP route from the attack it was built for. If legitimate traffic keeps being blocked, escalate with three Message SIDs.</p>"""},
],
"verify": """<p>Re-run the script over a window that covers the next campaign to that country. Every prefix should report <code>clean</code>.</p>
<pre><code class="language-bash">python3 twilio_pumping_block_audit.py --days 3
# 6 destination prefix(es) over 3 day(s), 0 blocked</code></pre>""",
"code_intro": "One paginated GET over the Messages list and nothing else &mdash; an API Key with read access is enough and is what you should give it. The classifier takes the clock as an argument rather than reading it, because <em>this block has already lifted</em> is a claim about time, and the only way to test a claim about time is to hand it a fixed <code>now</code>.",
"py_file": "twilio_pumping_block_audit.py",
"py": '''"""Report destinations blocked by Twilio SMS Pumping Protection (30450).

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
log = logging.getLogger("twilio_pumping_block_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# Both codes come out of the same fraud protection. Splitting them produces two
# reports about one event and no extra decision.
BLOCKED = (30450, 30485)

# Dialling codes, matched longest first. Without the length ordering every
# Bangladeshi number (880) lands in the North American bucket (1).
CODE_1 = {"1", "7"}
CODE_2 = {"20", "27", "30", "31", "32", "33", "34", "36", "39", "40", "41", "43",
          "44", "45", "46", "47", "48", "49", "51", "52", "53", "54", "55", "56",
          "57", "58", "60", "61", "62", "63", "64", "65", "66", "81", "82", "84",
          "86", "90", "91", "92", "93", "94", "95", "98"}
CODE_3 = {"211", "212", "213", "216", "218", "220", "221", "223", "225", "226",
          "227", "228", "229", "233", "234", "237", "243", "244", "249", "250",
          "251", "254", "255", "256", "260", "263", "264", "265", "267", "351",
          "352", "353", "354", "355", "356", "357", "358", "359", "370", "371",
          "372", "373", "374", "375", "376", "380", "381", "385", "386", "387",
          "389", "420", "421", "423", "500", "501", "502", "503", "504", "505",
          "506", "507", "508", "509", "852", "853", "855", "856", "880", "886",
          "960", "961", "962", "963", "964", "965", "966", "967", "968", "970",
          "971", "972", "973", "974", "975", "976", "977", "992", "993", "994",
          "995", "996", "998"}


def country_prefix(e164):
    """Dialling code for a destination number. Pure.

    Longest match wins, because the codes are a prefix-free set only when you
    read them that way: 880 has to be tested before 88 and before 1.
    """
    digits = "".join(c for c in str(e164 or "") if c.isdigit())
    if not digits:
        return "unknown"
    for size, table in ((3, CODE_3), (2, CODE_2), (1, CODE_1)):
        if digits[:size] in table:
            return digits[:size]
    return digits[:3]


def error_code(message):
    """Read error_code as an integer, or None.

    It is null on every healthy message and a number on failed ones, but some
    exports hand it back as a string. Comparing the raw value against 30450 is
    the mistake that reports a clean account in the middle of a block.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def parse_ts(raw):
    """date_sent is RFC 2822 on this API. ISO is accepted too, because that is
    what fixtures and exports tend to carry."""
    s = str(raw or "").strip()
    if not s:
        return None
    stamp = None
    try:
        stamp = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            stamp = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if stamp is not None and stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt.timezone.utc)
    return stamp


def minutes_between(start, end):
    if start is None or end is None:
        return None
    return int((end - start).total_seconds() // 60)


def tally(messages, now):
    """Bucket outbound messages by destination dialling code. Pure, and `now`
    is an argument so the age of a block is testable without a clock.

    Inbound messages are skipped: they have no destination of ours and no
    delivery error worth counting.
    """
    rows = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        prefix = country_prefix(m.get("to"))
        row = rows.setdefault(prefix, {"total": 0, "blocked": 0, "sids": [],
                                       "first": None, "last": None})
        row["total"] += 1
        if error_code(m) in BLOCKED:
            row["blocked"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
            stamp = parse_ts(m.get("date_sent") or m.get("date_created"))
            if stamp is not None:
                if row["first"] is None or stamp < row["first"]:
                    row["first"] = stamp
                if row["last"] is None or stamp > row["last"]:
                    row["last"] = stamp
    for row in rows.values():
        row["span_minutes"] = minutes_between(row["first"], row["last"])
        row["minutes_since_last"] = minutes_between(row["last"], now)
    return rows


def verdict(stats, min_blocked=3):
    """Classify one destination prefix. Pure, so the thresholds are visible
    rather than buried in a request loop.

    Returns (state, detail).
    """
    total = int(stats.get("total") or 0)
    blocked = int(stats.get("blocked") or 0)
    if not blocked:
        return ("clean", "%d message(s), none blocked" % total)

    rate = (blocked / total) if total else 1.0
    pct = rate * 100
    span = stats.get("span_minutes")
    since = stats.get("minutes_since_last")

    if blocked < min_blocked:
        return ("isolated",
                "%d of %d blocked (%.1f%%). Too few to separate a fraud block "
                "from an ordinary carrier reject, and Support wants at least %d "
                "Message SIDs before it will look."
                % (blocked, total, pct, min_blocked))

    if since is not None and since >= 60 and (span is None or span <= 240):
        return ("recovered",
                "%d of %d blocked (%.1f%%) inside a %s minute window that ended "
                "%d minutes ago. That is the shape of the temporary block: it "
                "lifted by itself, nobody was told, and the same prefix will hit "
                "it again." % (blocked, total, pct, span, since))

    if rate >= 0.5:
        return ("region-blocked",
                "%d of %d blocked (%.1f%%), last one %s minutes ago. More than "
                "half of everything to this prefix is being refused: treat it as "
                "an outage for that country, not as noise."
                % (blocked, total, pct, since))

    return ("intermittent",
            "%d of %d blocked (%.1f%%) spread over %s minutes. Recurring rather "
            "than one burst, so a safe list entry is worth more than waiting it "
            "out." % (blocked, total, pct, span))


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
    resource, so the date window and the page cap are the only bounds there
    are."""
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
    ap.add_argument("--days", type=int, default=3,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--min-blocked", type=int, default=3,
                    help="fewer than this on one prefix is reported as isolated")
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

    now = dt.datetime.now(dt.timezone.utc)
    prefixes = tally(messages, now)
    bad = 0
    for prefix, stats in sorted(prefixes.items()):
        state, detail = verdict(stats, args.min_blocked)
        line = "%-15s +%-5s %s" % (state, prefix, detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
        log.warning("  repair: no API call lifts a 30450. Add the verified "
                    "numbers or the +%s prefix to the Global Safe List (Console "
                    "-> Messaging -> Settings -> Global Safe List), or send that "
                    "route with RiskCheck=disable. Keep RiskCheck on elsewhere.",
                    prefix)

    log.info("%d destination prefix(es) over %d day(s), %d blocked",
             len(prefixes), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-pumping-block-audit.mjs",
"js": '''/**
 * Report destinations blocked by Twilio SMS Pumping Protection (30450).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// Both codes come out of the same fraud protection. Splitting them produces two
// reports about one event and no extra decision.
const BLOCKED = new Set([30450, 30485]);

// Dialling codes, matched longest first. Without the length ordering every
// Bangladeshi number (880) lands in the North American bucket (1).
const CODE_1 = new Set(['1', '7']);
const CODE_2 = new Set(['20', '27', '30', '31', '32', '33', '34', '36', '39', '40',
  '41', '43', '44', '45', '46', '47', '48', '49', '51', '52', '53', '54', '55',
  '56', '57', '58', '60', '61', '62', '63', '64', '65', '66', '81', '82', '84',
  '86', '90', '91', '92', '93', '94', '95', '98']);
const CODE_3 = new Set(['211', '212', '213', '216', '218', '220', '221', '223',
  '225', '226', '227', '228', '229', '233', '234', '237', '243', '244', '249',
  '250', '251', '254', '255', '256', '260', '263', '264', '265', '267', '351',
  '352', '353', '354', '355', '356', '357', '358', '359', '370', '371', '372',
  '373', '374', '375', '376', '380', '381', '385', '386', '387', '389', '420',
  '421', '423', '500', '501', '502', '503', '504', '505', '506', '507', '508',
  '509', '852', '853', '855', '856', '880', '886', '960', '961', '962', '963',
  '964', '965', '966', '967', '968', '970', '971', '972', '973', '974', '975',
  '976', '977', '992', '993', '994', '995', '996', '998']);

/**
 * Dialling code for a destination number. Pure. Longest match wins, because the
 * codes are a prefix-free set only when you read them that way.
 */
export function countryPrefix(e164) {
  const digits = String(e164 ?? '').replace(/\\D/g, '');
  if (!digits) return 'unknown';
  for (const [size, table] of [[3, CODE_3], [2, CODE_2], [1, CODE_1]]) {
    if (table.has(digits.slice(0, size))) return digits.slice(0, size);
  }
  return digits.slice(0, 3);
}

/**
 * Read error_code as a number, or null. It is null on healthy messages and a
 * number on failed ones; comparing the raw value is how the audit reports a
 * clean account in the middle of a block.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** date_sent is RFC 2822 on this API; ISO is accepted too. */
export function parseTs(raw) {
  const s = String(raw ?? '').trim();
  if (!s) return null;
  const t = Date.parse(s);
  return Number.isNaN(t) ? null : new Date(t);
}

function minutesBetween(start, end) {
  if (!start || !end) return null;
  return Math.floor((end.getTime() - start.getTime()) / 60000);
}

/**
 * Bucket outbound messages by destination dialling code. Pure, and `now` is an
 * argument so the age of a block is testable without a clock.
 */
export function tally(messages, now) {
  const rows = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const prefix = countryPrefix(m.to);
    if (!rows.has(prefix)) {
      rows.set(prefix, { total: 0, blocked: 0, sids: [], first: null, last: null });
    }
    const row = rows.get(prefix);
    row.total += 1;
    if (BLOCKED.has(errorCode(m))) {
      row.blocked += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
      const stamp = parseTs(m.date_sent ?? m.date_created);
      if (stamp) {
        if (!row.first || stamp < row.first) row.first = stamp;
        if (!row.last || stamp > row.last) row.last = stamp;
      }
    }
  }
  for (const row of rows.values()) {
    row.span_minutes = minutesBetween(row.first, row.last);
    row.minutes_since_last = minutesBetween(row.last, now);
  }
  return rows;
}

/**
 * Classify one destination prefix. Pure, so the thresholds are visible rather
 * than buried in a request loop. Returns [state, detail].
 */
export function verdict(stats, minBlocked = 3) {
  const total = Number(stats.total ?? 0);
  const blocked = Number(stats.blocked ?? 0);
  if (!blocked) return ['clean', `${total} message(s), none blocked`];

  const rate = total ? blocked / total : 1;
  const pct = (rate * 100).toFixed(1);
  const span = stats.span_minutes;
  const since = stats.minutes_since_last;

  if (blocked < minBlocked) {
    return ['isolated',
      `${blocked} of ${total} blocked (${pct}%). Too few to separate a fraud ` +
      'block from an ordinary carrier reject, and Support wants at least ' +
      `${minBlocked} Message SIDs before it will look.`];
  }

  if (since !== null && since !== undefined && since >= 60 &&
      (span === null || span === undefined || span <= 240)) {
    return ['recovered',
      `${blocked} of ${total} blocked (${pct}%) inside a ${span} minute window ` +
      `that ended ${since} minutes ago. That is the shape of the temporary ` +
      'block: it lifted by itself, nobody was told, and the same prefix will ' +
      'hit it again.'];
  }

  if (rate >= 0.5) {
    return ['region-blocked',
      `${blocked} of ${total} blocked (${pct}%), last one ${since} minutes ago. ` +
      'More than half of everything to this prefix is being refused: treat it ' +
      'as an outage for that country, not as noise.'];
  }

  return ['intermittent',
    `${blocked} of ${total} blocked (${pct}%) spread over ${span} minutes. ` +
    'Recurring rather than one burst, so a safe list entry is worth more than ' +
    'waiting it out.'];
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

async function listMessages(auth, account, since, limit) {
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
  const days = flag('--days', 3);
  const minBlocked = flag('--min-blocked', 3);

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const messages = await listMessages(auth, account, since, flag('--max-messages', 20000));
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  const prefixes = tally(messages, new Date());
  let bad = 0;
  for (const prefix of [...prefixes.keys()].sort()) {
    const stats = prefixes.get(prefix);
    const [state, detail] = verdict(stats, minBlocked);
    const line = `${state.padEnd(15)} +${prefix.padEnd(5)} ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  message sids: ${stats.sids.join(', ')}`);
    console.warn('  repair: no API call lifts a 30450. Add the verified numbers ' +
                 `or the +${prefix} prefix to the Global Safe List (Console -> ` +
                 'Messaging -> Settings -> Global Safe List), or send that route ' +
                 'with RiskCheck=disable. Keep RiskCheck on elsewhere.');
  }

  console.log(`${prefixes.size} destination prefix(es) over ${days} day(s), ${bad} blocked`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three things are worth pinning here. That the dialling code match is longest-first, because <code>880</code> falling into the <code>1</code> bucket quietly merges Bangladesh into North America. That a burst which has already stopped reads as <code>recovered</code> rather than as an active incident. And that a prefix still failing right now does not, no matter how neat the window looks.",
"test_py_file": "test_twilio_pumping_block_audit.py",
"test_py": '''import datetime as dt

from twilio_pumping_block_audit import country_prefix, tally, verdict

NOW = dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.timezone.utc)


def blocked(sid, to, sent):
    return {"sid": sid, "to": to, "error_code": 30450, "status": "failed",
            "date_sent": sent}


def test_dialling_codes_match_longest_first():
    assert country_prefix("+8801711000000") == "880"
    assert country_prefix("+447700900000") == "44"
    assert country_prefix("+15551230000") == "1"


def test_prefix_of_junk_is_not_a_crash():
    assert country_prefix(None) == "unknown"
    assert country_prefix("not a number") == "unknown"


def test_error_code_as_a_string_still_counts():
    rows = tally([{"sid": "SM1", "to": "+8801711000000", "error_code": "30450",
                   "date_sent": "Mon, 02 Mar 2026 09:00:00 +0000"}], NOW)
    assert rows["880"]["blocked"] == 1


def test_tally_groups_by_prefix_and_skips_inbound():
    rows = tally([
        blocked("SM1", "+8801711000000", "Mon, 02 Mar 2026 09:00:00 +0000"),
        blocked("SM2", "+8801711000001", "Mon, 02 Mar 2026 09:11:00 +0000"),
        {"sid": "SM3", "to": "+15551230000", "status": "delivered"},
        {"sid": "SM4", "to": "+15551230000", "direction": "inbound"},
    ], NOW)
    assert sorted(rows) == ["1", "880"]
    assert rows["880"]["blocked"] == 2
    assert rows["880"]["span_minutes"] == 11
    assert rows["880"]["minutes_since_last"] == 169
    assert rows["1"]["total"] == 1


def test_a_burst_that_already_stopped_reads_as_recovered():
    state, detail = verdict({"total": 400, "blocked": 94, "span_minutes": 11,
                             "minutes_since_last": 169})
    assert state == "recovered"
    assert "lifted by itself" in detail


def test_a_prefix_still_failing_now_is_an_outage_not_a_blip():
    state, detail = verdict({"total": 10, "blocked": 8, "span_minutes": 600,
                             "minutes_since_last": 4})
    assert state == "region-blocked"
    assert "outage" in detail


def test_recurring_low_rate_is_intermittent():
    state, _ = verdict({"total": 500, "blocked": 40, "span_minutes": 3000,
                        "minutes_since_last": 6})
    assert state == "intermittent"


def test_two_blocked_is_too_few_to_escalate():
    state, detail = verdict({"total": 50, "blocked": 2, "span_minutes": 3,
                             "minutes_since_last": 400})
    assert state == "isolated"
    assert "at least 3" in detail


def test_no_blocked_messages_is_clean():
    state, detail = verdict({"total": 900, "blocked": 0})
    assert state == "clean"
    assert "900" in detail


def test_sids_are_capped_at_the_three_support_asks_for():
    rows = tally([blocked("SM%d" % i, "+8801711000000",
                          "Mon, 02 Mar 2026 09:00:00 +0000") for i in range(9)], NOW)
    assert rows["880"]["sids"] == ["SM0", "SM1", "SM2"]
    assert rows["880"]["blocked"] == 9
''',
"test_js_file": "twilio-pumping-block-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countryPrefix, tally, verdict } from './twilio-pumping-block-audit.mjs';

const NOW = new Date('2026-03-02T12:00:00Z');

const blocked = (sid, to, sent) => ({
  sid, to, error_code: 30450, status: 'failed', date_sent: sent,
});

test('dialling codes match longest first', () => {
  assert.equal(countryPrefix('+8801711000000'), '880');
  assert.equal(countryPrefix('+447700900000'), '44');
  assert.equal(countryPrefix('+15551230000'), '1');
});

test('prefix of junk is not a crash', () => {
  assert.equal(countryPrefix(null), 'unknown');
  assert.equal(countryPrefix('not a number'), 'unknown');
});

test('error_code as a string still counts', () => {
  const rows = tally([{ sid: 'SM1', to: '+8801711000000', error_code: '30450',
                        date_sent: 'Mon, 02 Mar 2026 09:00:00 +0000' }], NOW);
  assert.equal(rows.get('880').blocked, 1);
});

test('tally groups by prefix and skips inbound', () => {
  const rows = tally([
    blocked('SM1', '+8801711000000', 'Mon, 02 Mar 2026 09:00:00 +0000'),
    blocked('SM2', '+8801711000001', 'Mon, 02 Mar 2026 09:11:00 +0000'),
    { sid: 'SM3', to: '+15551230000', status: 'delivered' },
    { sid: 'SM4', to: '+15551230000', direction: 'inbound' },
  ], NOW);
  assert.deepEqual([...rows.keys()].sort(), ['1', '880']);
  assert.equal(rows.get('880').blocked, 2);
  assert.equal(rows.get('880').span_minutes, 11);
  assert.equal(rows.get('880').minutes_since_last, 169);
  assert.equal(rows.get('1').total, 1);
});

test('a burst that already stopped reads as recovered', () => {
  const [state, detail] = verdict({ total: 400, blocked: 94, span_minutes: 11,
                                    minutes_since_last: 169 });
  assert.equal(state, 'recovered');
  assert.match(detail, /lifted by itself/);
});

test('a prefix still failing now is an outage, not a blip', () => {
  const [state, detail] = verdict({ total: 10, blocked: 8, span_minutes: 600,
                                    minutes_since_last: 4 });
  assert.equal(state, 'region-blocked');
  assert.match(detail, /outage/);
});

test('recurring low rate is intermittent', () => {
  assert.equal(verdict({ total: 500, blocked: 40, span_minutes: 3000,
                         minutes_since_last: 6 })[0], 'intermittent');
});

test('two blocked is too few to escalate', () => {
  const [state, detail] = verdict({ total: 50, blocked: 2, span_minutes: 3,
                                    minutes_since_last: 400 });
  assert.equal(state, 'isolated');
  assert.match(detail, /at least 3/);
});

test('no blocked messages is clean', () => {
  const [state, detail] = verdict({ total: 900, blocked: 0 });
  assert.equal(state, 'clean');
  assert.match(detail, /900/);
});

test('sids are capped at the three Support asks for', () => {
  const rows = tally([...Array(9).keys()].map((i) =>
    blocked(`SM${i}`, '+8801711000000', 'Mon, 02 Mar 2026 09:00:00 +0000')), NOW);
  assert.deepEqual(rows.get('880').sids, ['SM0', 'SM1', 'SM2']);
  assert.equal(rows.get('880').blocked, 9);
});
''',
"faq": [
 ("Why did the sends start working again with no change from me?",
  "Because the block is temporary by design. SMS Pumping Protection applies it to a destination or region for a short period, typically fifteen to thirty minutes, and then releases it. That is why almost nobody ever diagnoses this one: the evidence expires before the investigation starts, and all that is left is a gap in your OTP conversion."),
 ("Can I ask Twilio for messages with error_code 30450 directly?",
  "No. The Messages list resource has no ErrorCode parameter and no Status parameter — the documented filters are To, From, DateSent, DateSent< and DateSent>, plus paging. Finding a two hundred message burst inside a day of traffic means paging the day and filtering it in your own process."),
 ("Should I just disable RiskCheck?",
  "Not globally. It exists because OTP routes are exactly what SMS pumping attacks target, and turning it off account-wide converts an occasional twenty minute gap into an open invoice. Disable it per-send on a route you have verified, or safe-list the specific numbers and prefixes, and leave the protection running everywhere else."),
 ("Why group by dialling code instead of by destination number?",
  "Because the block is scoped to a destination or region, not to one handset. Per number, two hundred failures look like two hundred unrelated one-offs. Per prefix they are a single event with a size, a start and an end, which is the form you need before you can safe-list anything or open a ticket."),
 ("Can the script add the safe list entry itself?",
  "It will not, and for the Global Safe List there is nothing to call: it is a Console setting. The script prints the prefix, the count, the window and three Message SIDs, which is everything a human needs to make the change or escalate it."),
],
"related": [
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering drops SMS with error 30007"),
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never leave queued or accepted"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_30450, CITE_PUMPING, CITE_MSG, CITE_ALERTS],
},


{
"slug": "body-exceeds-1600-chars-21617",
"title": "Error 21617: the rendered message body exceeds 1600 chars",
"description": "Error 21617 rejects the send before a Message row exists, so it never appears in the Messages list. Monitor Alerts is the only read-only path to it.",
"h1": "error 21617: the rendered message body exceeds 1600 chars",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 21617", "twilio 1600 character limit",
             "concatenated message body exceeds", "twilio message too long",
             "twilio num_segments 8"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The template is fine. It has been fine for a year. Then one customer with a long company name, three line items and a German address renders past sixteen hundred characters, Twilio refuses the request with <code>21617</code>, and that customer never receives the message. Their Message SID is not in your logs because there is no Message SID: the send was rejected before a resource was created, so it appears nowhere in the Messages list at all.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> and keep alerts whose <code>error_code</code> is <code>21617</code>. Request-time rejections never create a Message row, so the Alerts list is the only read-only place they exist.</p>
<p>Then page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json</code> for the near misses: any sender whose longest body is close to the sixteen hundred character ceiling, or whose messages are already at eight or more segments, is one long customer name from being rejected.</p>""",
"problem": """<p>Two facts combine badly here. The first is that <code>21617</code> is a request-time rejection: the API refuses the parameters, no Message resource is created, nothing is billed, and no status callback fires. The second is that the rejection is data-dependent &mdash; it happens for the subset of recipients whose interpolated values are long, which is a subset your test fixtures do not contain and your staging data almost certainly does not either.</p>
<p>So the failure lands entirely in your own error handling, and only for some users. If the send happens inside a background job that logs and moves on, the outcome is a customer who silently stops receiving one class of message while everybody else keeps getting it. Nobody reports it, because a message that never arrives leaves no trace to report.</p>
<p>The account-level view is worse than useless: delivery rate is unaffected, because a rejected send never enters the denominator.</p>""",
"why": """<p><strong>Rejected sends are invisible in the Messages list.</strong> The row does not exist. You can page <code>Messages.json</code> for a year and never see a single 21617, which is why the Monitor Alerts list, not the message list, is the read path for this whole class of error.</p>
<p><strong>The limit is on the rendered body, not the template.</strong> Validation that runs against the template passes forever. The only length that matters is the one produced after every variable has been substituted, for the specific recipient, at the moment of the call.</p>
<p><strong>Sixteen hundred characters is not sixteen hundred bytes.</strong> The ceiling counts characters, but the encoding those characters force decides how many segments a body of a given length becomes, which is why long non-Latin bodies feel like they hit the wall sooner. Anything at eight segments or more is close enough to the edge to be worth reading before it goes over.</p>
<p><strong>Alerts are retained thirty days.</strong> Whatever this script says about how long the problem has been happening is bounded by that window, and it should say so rather than implying it looked further back than it can.</p>""",
"steps": [
 {"h": "Sweep the Monitor alerts for the window you care about",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=100</code>, following <code>meta.next_page_url</code> &mdash; on this API the next page is an absolute URL, not the relative <code>next_page_uri</code> the 2010 API uses. Read <code>error_code</code> as an integer: the Monitor API returns it as a string.</p>"""},
 {"h": "Count the rejections and take the first and last date",
  "body": """<p><code>date_generated</code> on the earliest and latest 21617 tells you whether this started with last week's template change or has been quietly running all month. Alerts are kept thirty days, so the earliest one you can see may not be the first one that happened.</p>"""},
 {"h": "Fetch a few alerts individually to see what was sent",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> returns <code>request_variables</code>, <code>request_headers</code> and <code>response_body</code>, none of which appear in the list rows. That is one request per alert, so cap it: two or three examples are enough to identify which template and which variable did it.</p>"""},
 {"h": "Page the Messages list for the near misses",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>. Group by <code>messaging_service_sid</code> or <code>from</code>, keep the longest <code>body</code> length seen and count the rows at <code>num_segments</code> eight or higher. Those are the sends that will be rejected the next time a longer name comes through.</p>"""},
 {"h": "Truncate at the source, then re-run",
  "body": """<p>Validate the fully rendered body before the call, truncate or split server-side, and aim well below the ceiling &mdash; under 320 characters is the range where deliverability and cost both behave. Re-run the sweep over the following week; the alert count should be zero and the longest body should have moved.</p>"""},
],
"verify": """<p>Re-run over a window that covers the sends since the change. The alert count should be zero and every sender should report <code>fine</code>.</p>
<pre><code class="language-bash">python3 twilio_body_length_audit.py --days 14
# 0 rejection(s) with 21617, 3 sender(s), 0 near the limit</code></pre>""",
"code_intro": "Two read paths, because the failure and its warning signs live in different places: the Monitor Alerts list for the rejections that never became messages, and the Messages list for the bodies that are nearly there. Both are <code>GET</code>. The summary and the verdict are pure functions, so the thresholds &mdash; what counts as near the limit, what counts as merely long &mdash; are visible rather than buried.",
"py_file": "twilio_body_length_audit.py",
"py": '''"""Report Twilio sends rejected with 21617 and the bodies that are nearly there.

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
log = logging.getLogger("twilio_body_length_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

TOO_LONG = 21617
LIMIT = 1600      # the hard ceiling on a concatenated body
NEAR = 1200       # close enough that one long name goes over
COMFORTABLE = 320  # above this, cost and deliverability both start to bite
NEAR_SEGMENTS = 8


def alert_error_code(alert):
    """Read error_code off a Monitor alert as an integer, or None.

    The Monitor API returns it as a string, unlike the Messages list. Comparing
    it to 21617 without the conversion matches nothing at all.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def parse_ts(raw):
    """date_generated is ISO 8601 on the Monitor API and RFC 2822 on the 2010
    one. Accept both rather than guessing which list is being read."""
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(s)
    except (TypeError, ValueError):
        return None


def alert_summary(alerts, code=TOO_LONG):
    """Reduce a page of alerts to the rejections that matter. Pure.

    Returns {"count", "first", "last", "sids"}. The SIDs are capped at three,
    because each one costs a separate GET to expand and three examples identify
    the template.
    """
    out = {"count": 0, "first": None, "last": None, "sids": []}
    for a in alerts:
        if alert_error_code(a) != code:
            continue
        out["count"] += 1
        if len(out["sids"]) < 3:
            out["sids"].append(a.get("sid"))
        stamp = parse_ts(a.get("date_generated"))
        if stamp is not None:
            if out["first"] is None or stamp < out["first"]:
                out["first"] = stamp
            if out["last"] is None or stamp > out["last"]:
                out["last"] = stamp
    return out


def tally(messages):
    """Bucket outbound messages by sender, keeping the length evidence. Pure.

    Inbound messages are skipped: their length is not yours to control and they
    cannot be rejected by an API you did not call.
    """
    rows = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        key = m.get("messaging_service_sid") or m.get("from") or "unknown sender"
        row = rows.setdefault(key, {"total": 0, "longest": 0, "near": 0,
                                    "sids": []})
        row["total"] += 1
        size = len(str(m.get("body") or ""))
        try:
            segments = int(m.get("num_segments") or 1)
        except (TypeError, ValueError):
            segments = 1
        if size > row["longest"]:
            row["longest"] = size
        if size >= NEAR or segments >= NEAR_SEGMENTS:
            row["near"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
    return rows


def verdict(stats, limit=LIMIT, near=NEAR, comfortable=COMFORTABLE):
    """Classify one sender by how close its longest body came to the ceiling.

    Pure, so the thresholds can be read and argued with. Returns
    (state, detail).
    """
    total = int(stats.get("total") or 0)
    longest = int(stats.get("longest") or 0)
    close = int(stats.get("near") or 0)
    headroom = limit - longest

    if longest >= near:
        return ("near-limit",
                "longest body %d of %d characters, %d to spare, %d message(s) "
                "already past %d. One longer name or one extra line item and "
                "that send is rejected with 21617 and never becomes a Message."
                % (longest, limit, headroom, close, near))

    if longest >= comfortable:
        return ("long",
                "longest body %d characters over %d message(s). Under the "
                "ceiling, but past the point where segments and carrier "
                "tolerance both start to cost you." % (longest, total))

    return ("fine", "%d message(s), longest body %d characters" % (total, longest))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, start, limit):
    """Page the Monitor alerts. next_page_url is absolute on this API."""
    url = "%s/Alerts" % MONITOR
    params = {"LogLevel": "error", "StartDate": start, "PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def list_messages(session, account, since, limit):
    """Page Messages.json. No Status or ErrorCode filter exists on this
    resource, so the window and the cap are the only bounds."""
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
    ap.add_argument("--days", type=int, default=14,
                    help="window for both sweeps; alerts are retained 30 days")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging the Messages list after this many rows")
    ap.add_argument("--detail", type=int, default=2,
                    help="expand this many alerts individually for the request "
                         "variables the list omits (one GET each)")
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

    days = min(args.days, 30)
    if days != args.days:
        log.info("alerts are retained 30 days; window shortened to %d", days)
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()

    rejected = alert_summary(list_alerts(session, since, 10000))
    if rejected["count"]:
        log.warning("rejected       21617 x%d, first %s, last %s",
                    rejected["count"], rejected["first"], rejected["last"])
        log.warning("  alert sids: %s", ", ".join(str(s) for s in rejected["sids"]))
        for sid in rejected["sids"][:max(0, args.detail)]:
            one = get(session, "%s/Alerts/%s" % (MONITOR, sid))
            log.warning("  %s request_variables: %.400s", sid,
                        one.get("request_variables") or "(empty)")
        log.warning("  repair: truncate or split the rendered body before the "
                    "call. The limit is on the substituted text, not the "
                    "template, so validate the string you are about to send.")
    else:
        log.info("rejected       no 21617 alerts since %s", since)

    messages = list_messages(session, account, since, args.max_messages)
    senders = tally(messages)
    bad = 0
    for sender, stats in sorted(senders.items()):
        state, detail = verdict(stats)
        line = "%-11s %s  %s" % (state, sender, detail)
        if state == "fine":
            log.info(line)
            continue
        if state == "long":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))

    log.info("%d rejection(s) with 21617, %d sender(s), %d near the limit",
             rejected["count"], len(senders), bad)
    return 1 if (bad or rejected["count"]) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-body-length-audit.mjs",
"js": '''/**
 * Report Twilio sends rejected with 21617 and the bodies that are nearly there.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const TOO_LONG = 21617;
const LIMIT = 1600;       // the hard ceiling on a concatenated body
const NEAR = 1200;        // close enough that one long name goes over
const COMFORTABLE = 320;  // above this, cost and deliverability both bite
const NEAR_SEGMENTS = 8;

/**
 * Read error_code off a Monitor alert as a number, or null. The Monitor API
 * returns it as a string, unlike the Messages list.
 */
export function alertErrorCode(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

function parseTs(raw) {
  const s = String(raw ?? '').trim();
  if (!s) return null;
  const t = Date.parse(s);
  return Number.isNaN(t) ? null : new Date(t);
}

/**
 * Reduce a page of alerts to the rejections that matter. Pure. SIDs are capped
 * at three, because each one costs a separate GET to expand.
 */
export function alertSummary(alerts, code = TOO_LONG) {
  const out = { count: 0, first: null, last: null, sids: [] };
  for (const a of alerts) {
    if (alertErrorCode(a) !== code) continue;
    out.count += 1;
    if (out.sids.length < 3) out.sids.push(a.sid);
    const stamp = parseTs(a.date_generated);
    if (stamp) {
      if (!out.first || stamp < out.first) out.first = stamp;
      if (!out.last || stamp > out.last) out.last = stamp;
    }
  }
  return out;
}

/**
 * Bucket outbound messages by sender, keeping the length evidence. Pure.
 */
export function tally(messages) {
  const rows = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const key = m.messaging_service_sid || m.from || 'unknown sender';
    if (!rows.has(key)) rows.set(key, { total: 0, longest: 0, near: 0, sids: [] });
    const row = rows.get(key);
    row.total += 1;
    const size = String(m.body ?? '').length;
    const segments = Number(m.num_segments ?? 1) || 1;
    if (size > row.longest) row.longest = size;
    if (size >= NEAR || segments >= NEAR_SEGMENTS) {
      row.near += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
    }
  }
  return rows;
}

/**
 * Classify one sender by how close its longest body came to the ceiling. Pure.
 * Returns [state, detail].
 */
export function verdict(stats, limit = LIMIT, near = NEAR, comfortable = COMFORTABLE) {
  const total = Number(stats.total ?? 0);
  const longest = Number(stats.longest ?? 0);
  const close = Number(stats.near ?? 0);
  const headroom = limit - longest;

  if (longest >= near) {
    return ['near-limit',
      `longest body ${longest} of ${limit} characters, ${headroom} to spare, ` +
      `${close} message(s) already past ${near}. One longer name or one extra ` +
      'line item and that send is rejected with 21617 and never becomes a Message.'];
  }

  if (longest >= comfortable) {
    return ['long',
      `longest body ${longest} characters over ${total} message(s). Under the ` +
      'ceiling, but past the point where segments and carrier tolerance both ' +
      'start to cost you.'];
  }

  return ['fine', `${total} message(s), longest body ${longest} characters`];
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

async function listAlerts(auth, start, limit) {
  let url = `${MONITOR}/Alerts`;
  let params = { LogLevel: 'error', StartDate: start, PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.alerts ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

async function listMessages(auth, account, since, limit) {
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
  const days = Math.min(flag('--days', 14), 30);
  const detail = flag('--detail', 2);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const rejected = alertSummary(await listAlerts(auth, since, 10000));
  if (rejected.count) {
    console.warn(`rejected    21617 x${rejected.count}, first ${rejected.first}, ` +
                 `last ${rejected.last}`);
    console.warn(`  alert sids: ${rejected.sids.join(', ')}`);
    for (const sid of rejected.sids.slice(0, Math.max(0, detail))) {
      const one = await get(auth, `${MONITOR}/Alerts/${sid}`);
      console.warn(`  ${sid} request_variables: ` +
                   String(one.request_variables ?? '(empty)').slice(0, 400));
    }
    console.warn('  repair: truncate or split the rendered body before the call. ' +
                 'The limit is on the substituted text, not the template, so ' +
                 'validate the string you are about to send.');
  } else {
    console.log(`rejected    no 21617 alerts since ${since}`);
  }

  const messages = await listMessages(auth, account, since, flag('--max-messages', 20000));
  const senders = tally(messages);
  let bad = 0;
  for (const sender of [...senders.keys()].sort()) {
    const stats = senders.get(sender);
    const [state, detail2] = verdict(stats);
    const line = `${state.padEnd(11)} ${sender}  ${detail2}`;
    if (state !== 'near-limit') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  message sids: ${stats.sids.join(', ')}`);
  }

  console.log(`${rejected.count} rejection(s) with 21617, ${senders.size} ` +
              `sender(s), ${bad} near the limit`);
  process.exitCode = (bad || rejected.count) ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// run main(), fail on the missing credentials and set a non-zero exit code.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that matters most is the one that costs nothing to get wrong and everything to miss: the Monitor API hands back <code>error_code</code> as a string, so a summary that compares it to the integer <code>21617</code> reports a clean account forever. The rest pin the thresholds &mdash; a body at 1250 characters is a warning, a body at 400 is not.",
"test_py_file": "test_twilio_body_length_audit.py",
"test_py": '''from twilio_body_length_audit import alert_summary, tally, verdict


def alert(sid, code, when="2026-03-02T09:00:00Z"):
    return {"sid": sid, "error_code": code, "date_generated": when}


def test_monitor_returns_error_code_as_a_string():
    # The whole audit reports nothing if this comparison is done on the raw value.
    out = alert_summary([alert("NO1", "21617")])
    assert out["count"] == 1


def test_summary_ignores_other_error_codes():
    out = alert_summary([alert("NO1", "11200"), alert("NO2", "21617")])
    assert out["count"] == 1
    assert out["sids"] == ["NO2"]


def test_summary_keeps_the_first_and_last_rejection():
    out = alert_summary([
        alert("NO1", "21617", "2026-03-02T09:00:00Z"),
        alert("NO2", "21617", "2026-02-25T04:30:00Z"),
        alert("NO3", "21617", "2026-03-04T18:00:00Z"),
    ])
    assert out["count"] == 3
    assert out["first"].day == 25
    assert out["last"].day == 4


def test_alert_sids_are_capped_at_three():
    out = alert_summary([alert("NO%d" % i, "21617") for i in range(7)])
    assert out["sids"] == ["NO0", "NO1", "NO2"]
    assert out["count"] == 7


def test_tally_keeps_the_longest_body_per_sender_and_skips_inbound():
    rows = tally([
        {"sid": "SM1", "from": "+15550001111", "body": "x" * 40},
        {"sid": "SM2", "from": "+15550001111", "body": "x" * 1250},
        {"sid": "SM3", "from": "+15550001111", "direction": "inbound", "body": "y" * 90},
        {"sid": "SM4", "messaging_service_sid": "MG1", "from": "+15550001111",
         "body": "z" * 20},
    ])
    assert sorted(rows) == ["+15550001111", "MG1"]
    assert rows["+15550001111"]["longest"] == 1250
    assert rows["+15550001111"]["near"] == 1
    assert rows["+15550001111"]["sids"] == ["SM2"]


def test_eight_segments_counts_as_near_even_on_a_short_body():
    # num_segments is the near-miss signal when the body was truncated in transit
    # or the encoding inflated it.
    rows = tally([{"sid": "SM1", "from": "+1555", "body": "x" * 600,
                   "num_segments": "9"}])
    assert rows["+1555"]["near"] == 1


def test_a_body_past_the_warning_line_is_near_limit():
    state, detail = verdict({"total": 900, "longest": 1250, "near": 4})
    assert state == "near-limit"
    assert "350 to spare" in detail
    assert "21617" in detail


def test_a_long_but_safe_body_is_only_long():
    state, detail = verdict({"total": 900, "longest": 400})
    assert state == "long"
    assert "ceiling" in detail


def test_short_bodies_are_fine():
    state, detail = verdict({"total": 900, "longest": 120})
    assert state == "fine"
    assert "120" in detail
''',
"test_js_file": "twilio-body-length-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { alertSummary, tally, verdict } from './twilio-body-length-audit.mjs';

const alert = (sid, code, when = '2026-03-02T09:00:00Z') => ({
  sid, error_code: code, date_generated: when,
});

test('monitor returns error_code as a string', () => {
  assert.equal(alertSummary([alert('NO1', '21617')]).count, 1);
});

test('summary ignores other error codes', () => {
  const out = alertSummary([alert('NO1', '11200'), alert('NO2', '21617')]);
  assert.equal(out.count, 1);
  assert.deepEqual(out.sids, ['NO2']);
});

test('summary keeps the first and last rejection', () => {
  const out = alertSummary([
    alert('NO1', '21617', '2026-03-02T09:00:00Z'),
    alert('NO2', '21617', '2026-02-25T04:30:00Z'),
    alert('NO3', '21617', '2026-03-04T18:00:00Z'),
  ]);
  assert.equal(out.count, 3);
  assert.equal(out.first.getUTCDate(), 25);
  assert.equal(out.last.getUTCDate(), 4);
});

test('alert sids are capped at three', () => {
  const out = alertSummary([...Array(7).keys()].map((i) => alert(`NO${i}`, '21617')));
  assert.deepEqual(out.sids, ['NO0', 'NO1', 'NO2']);
  assert.equal(out.count, 7);
});

test('tally keeps the longest body per sender and skips inbound', () => {
  const rows = tally([
    { sid: 'SM1', from: '+15550001111', body: 'x'.repeat(40) },
    { sid: 'SM2', from: '+15550001111', body: 'x'.repeat(1250) },
    { sid: 'SM3', from: '+15550001111', direction: 'inbound', body: 'y'.repeat(90) },
    { sid: 'SM4', messaging_service_sid: 'MG1', from: '+15550001111', body: 'z'.repeat(20) },
  ]);
  assert.deepEqual([...rows.keys()].sort(), ['+15550001111', 'MG1']);
  assert.equal(rows.get('+15550001111').longest, 1250);
  assert.equal(rows.get('+15550001111').near, 1);
  assert.deepEqual(rows.get('+15550001111').sids, ['SM2']);
});

test('eight segments counts as near even on a short body', () => {
  const rows = tally([{ sid: 'SM1', from: '+1555', body: 'x'.repeat(600),
                        num_segments: '9' }]);
  assert.equal(rows.get('+1555').near, 1);
});

test('a body past the warning line is near-limit', () => {
  const [state, detail] = verdict({ total: 900, longest: 1250, near: 4 });
  assert.equal(state, 'near-limit');
  assert.match(detail, /350 to spare/);
  assert.match(detail, /21617/);
});

test('a long but safe body is only long', () => {
  const [state, detail] = verdict({ total: 900, longest: 400 });
  assert.equal(state, 'long');
  assert.match(detail, /ceiling/);
});

test('short bodies are fine', () => {
  const [state, detail] = verdict({ total: 900, longest: 120 });
  assert.equal(state, 'fine');
  assert.match(detail, /120/);
});
''',
"faq": [
 ("Why can't I find the failed message in the Messages list?",
  "Because it was never created. 21617 is a request-time rejection: the API refuses the parameters, no Message resource exists, nothing is billed and no status callback fires. The Monitor Alerts list is the only read-only record that the attempt happened at all."),
 ("Is the limit 1600 characters or 1600 bytes?",
  "Characters, on the concatenated body. What the encoding changes is the cost of getting there: a body forced into UCS-2 fits 70 characters per segment instead of 160, so a long non-Latin message becomes many more segments well before it reaches the ceiling."),
 ("Why does the script flag messages at eight segments?",
  "Because eight segments is the neighbourhood of the wall, and near misses are the only early warning this failure has. A sender whose longest body is already 1250 characters is one longer customer name away from silently dropping a message, and you would rather know now than from a support ticket."),
 ("Why does it fetch some alerts individually?",
  "Because request_variables, request_headers and response_body are populated only on GET /v1/Alerts/{Sid} and are absent from every row of the list. That is what tells you which template and which variable did it. It costs one request per alert, so the script caps it at two by default."),
 ("How far back can this look?",
  "Thirty days. Alerts are retained for that long, so any statement about when the problem started is bounded by the window and the script says so rather than implying it looked further."),
],
"related": [
 ("/twilio/ucs2-segment-inflation/", "One smart quote triples the segment count"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering drops SMS with error 30007"),
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never leave queued or accepted"),
],
"citations": [CITE_21617, CITE_ALERTS, CITE_MSG, CITE_SERVICES],
},

]
