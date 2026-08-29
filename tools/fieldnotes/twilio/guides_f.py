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


{
"slug": "ucs2-segment-inflation",
"title": "One smart quote triples your segment count and your bill",
"description": "One smart quote forces UCS-2 for the whole body: 70 characters a segment instead of 160. Nothing errors, num_segments triples and so does the bill.",
"h1": "one smart quote triples your segment count and your bill",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio ucs-2 segments", "twilio smart encoding",
             "sms 70 character segment", "twilio num_segments high",
             "gsm-7 vs ucs-2 sms"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing failed. Every message says <code>delivered</code>, every customer got it, and the only thing that changed is the invoice: the SMS line is three times what it was on the same send volume. Somewhere in a template, an edit made in a rich text box replaced a straight apostrophe with a curly one. Every message that template renders now costs three segments instead of one, and there is no error code anywhere in the account to say so.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and recompute the encoding from <code>body</code> yourself: GSM-7 if every character is in the GSM 03.38 alphabet, UCS-2 if even one is not. Compare your segment count against <code>num_segments</code>.</p>
<p>UCS-2 fits <strong>70</strong> characters in a single segment and <strong>67</strong> in a concatenated one, against 160 and 153 for GSM-7. Then read <code>smart_encoding</code> on each Messaging Service to see whether the mitigation is even on.</p>""",
"problem": """<p>SMS has two alphabets. GSM-7 packs 160 characters into one segment; UCS-2 packs 70. The choice is not per-character, it is per-message: a single character outside the GSM alphabet forces the entire body into UCS-2, and a 150 character message that used to be one segment becomes three.</p>
<p>The characters that do it are not exotic. A curly apostrophe from a word processor, an en dash from a designer's copy deck, a non-breaking space pasted out of a spreadsheet, an emoji added to a campaign because it lifted click-through by two percent. None of them look different in the console. The message renders identically on the handset. Delivery is unaffected.</p>
<p>So the failure is purely financial, and it shows up in the only place nobody wires an alert to: the monthly bill, six weeks later, as a number somebody explains away as growth.</p>""",
"why": """<p><strong>One character decides the encoding for the whole body.</strong> There is no partial encoding and no per-character cost. The message is GSM-7 or it is not, and the cost of the sixty-ninth ordinary character is decided by one curly quote in the first line.</p>
<p><strong>The arithmetic is a cliff, not a slope.</strong> Concatenated segments hold 153 GSM-7 characters or 67 UCS-2 characters, because the concatenation header eats part of each one. A 150 character body goes from one segment to three &mdash; a 200% increase for a character nobody typed deliberately.</p>
<p><strong>Nothing errors.</strong> No <code>error_code</code>, status <code>delivered</code>, no alert, no Debugger entry. The single field that records what happened is <code>num_segments</code>, and it is an integer on a resource nobody reads after the send succeeds.</p>
<p><strong>Smart Encoding is a per-service toggle.</strong> It transliterates the common offenders for you, and it is the correct fix &mdash; but it applies to the Messaging Service it is set on. A second service for a new tenant, a service cloned for staging, or a send with a bare <code>From</code> and no service at all has none of it.</p>""",
"steps": [
 {"h": "Page the Messages list over a window",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. There is nothing to filter on here &mdash; no error code exists for this &mdash; so bound the sweep by days and by a hard message cap and read the bodies.</p>"""},
 {"h": "Recompute the encoding from the body",
  "body": """<p>GSM-7 if every character is in the GSM 03.38 basic set or its extension table; UCS-2 otherwise. The extension characters &mdash; <code>^ { } [ ] ~ | €</code> and backslash &mdash; are GSM-7 but cost <em>two</em> units each, which is the detail that makes a hand-rolled length check wrong by a segment.</p>"""},
 {"h": "Count segments the way the carrier does",
  "body": """<p>160 units in a single GSM-7 segment, 153 per segment once concatenated. 70 and 67 for UCS-2, counted in UTF-16 code units, so anything outside the Basic Multilingual Plane &mdash; every emoji &mdash; costs two.</p>"""},
 {"h": "Compare your count with num_segments",
  "body": """<p>If Twilio billed fewer segments than the raw body would cost, Smart Encoding already rewrote that message on the way out and the template is still wrong &mdash; it is just being paid for by a setting. If the counts match, nothing is mitigating anything.</p>"""},
 {"h": "Turn on Smart Encoding, then fix the template",
  "body": """<p><code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}</code> with <code>SmartEncoding=true</code> (Console &rarr; Messaging &rarr; Services &rarr; Content Settings), and normalise curly quotes and dashes where the template is authored. Corroborate the saving afterwards with <code>GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Daily.json?Category=sms-outbound</code>, comparing <code>count</code> against <code>usage</code>.</p>"""},
],
"verify": """<p>Re-run over the same window after the change. The extra segment count should be zero, and anything still in UCS-2 should be there because it genuinely has to be.</p>
<pre><code class="language-bash">python3 twilio_segment_audit.py --days 7
# 3 sender(s) over 7 day(s), 0 extra segment(s) from avoidable UCS-2</code></pre>""",
"code_intro": "The interesting half of this script never touches the network. Deciding GSM-7 against UCS-2, counting units with the extension table, and working out what the same body would have cost after transliteration is all arithmetic over a string &mdash; so it is a pure function with the alphabet written out in full, and the tests exercise it offline. The network half is one paginated <code>GET</code> over the Messages list and one over the Messaging Services.",
"py_file": "twilio_segment_audit.py",
"py": '''"""Report Twilio messages inflated into UCS-2 by a handful of characters.

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
log = logging.getLogger("twilio_segment_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

# GSM 03.38, the alphabet a single segment of 160 characters is drawn from.
GSM_BASIC = set(
    "@£$¥èéùìòÇØøÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !#¤%&()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")
# The four that cannot sit in the literal above without fighting the quoting:
# double quote, apostrophe, newline, carriage return.
GSM_BASIC.update({chr(34), chr(39), chr(10), chr(13)})

# The extension table. These are GSM-7, but each one costs two units, which is
# the detail that makes a naive len() check wrong by a whole segment.
GSM_EXT = set("^{}[~]|€")
GSM_EXT.add(chr(92))  # backslash

GSM_SINGLE, GSM_MULTI = 160, 153
UCS_SINGLE, UCS_MULTI = 70, 67

# What Smart Encoding substitutes, near enough: the characters a rich text
# editor inserts silently and that nobody meant to pay three times for.
TRANSLITERATE = {
    "‘": chr(39), "’": chr(39), "‚": chr(39), "‛": chr(39),
    "′": chr(39), "´": chr(39), "ʼ": chr(39),
    "“": chr(34), "”": chr(34), "„": chr(34),
    "«": chr(34), "»": chr(34),
    "–": "-", "—": "-", "−": "-",
    "…": "...", " ": " ", "•": "*", "™": "TM",
}


def sms_encoding(body):
    """GSM-7 if every character is in the GSM alphabet, UCS-2 otherwise. Pure.

    The choice is per message, not per character: one character outside the
    alphabet moves the entire body to UCS-2 and 70 characters a segment.
    """
    for c in str(body or ""):
        if c not in GSM_BASIC and c not in GSM_EXT:
            return "UCS-2"
    return "GSM-7"


def segments(body):
    """Return (encoding, units, segment_count) for a body. Pure.

    Units, not characters: an extension character costs two in GSM-7, and a
    character outside the Basic Multilingual Plane (every emoji) costs two
    UTF-16 code units in UCS-2.
    """
    text = str(body or "")
    encoding = sms_encoding(text)
    if encoding == "GSM-7":
        units = sum(2 if c in GSM_EXT else 1 for c in text)
        single, multi = GSM_SINGLE, GSM_MULTI
    else:
        units = sum(2 if ord(c) > 0xFFFF else 1 for c in text)
        single, multi = UCS_SINGLE, UCS_MULTI
    if units <= single:
        return (encoding, units, 1)
    return (encoding, units, -(-units // multi))


def offenders(body):
    """Every distinct character forcing UCS-2, with its substitute or None.

    Pure. None means nothing can stand in for it: an emoji, or a script that is
    simply not Latin, in which case UCS-2 is correct and the cost is real.
    """
    out, seen = [], set()
    for c in str(body or ""):
        if c in GSM_BASIC or c in GSM_EXT or c in seen:
            continue
        seen.add(c)
        out.append((c, TRANSLITERATE.get(c)))
    return out


def transliterate(body):
    """The body as Smart Encoding would rewrite it. Pure."""
    return "".join(TRANSLITERATE.get(c, c) for c in str(body or ""))


def describe(chars):
    return ", ".join("%s (U+%04X)" % (c, ord(c)) for c in chars)


def verdict(body, reported=None):
    """Classify one message body. Pure, and the whole point of this script.

    `reported` is num_segments as Twilio billed it. When it is lower than the
    raw body would cost, Smart Encoding rewrote the message on the way out: the
    template is still wrong, a setting is just paying for it.

    Returns (state, detail).
    """
    text = str(body or "")
    encoding, units, count = segments(text)
    if encoding == "GSM-7":
        return ("gsm-7", "%d segment(s), GSM-7, %d unit(s)" % (count, units))

    if reported is not None:
        try:
            billed = int(reported)
        except (TypeError, ValueError):
            billed = None
        if billed is not None and billed < count:
            return ("smart-encoded",
                    "billed %d segment(s), not the %d this body costs as UCS-2: "
                    "Smart Encoding rewrote it on the way out, so the template "
                    "is still wrong and a setting is paying for it."
                    % (billed, count))

    found = offenders(text)
    fixable = [c for c, sub in found if sub is not None]
    stuck = [c for c, sub in found if sub is None]

    if stuck:
        return ("ucs2-required",
                "%d segment(s) as UCS-2, %d unit(s). Nothing to strip: %s cannot "
                "be transliterated, so UCS-2 is correct here and the cost is "
                "expected rather than accidental."
                % (count, units, describe(stuck[:4])))

    clean = segments(transliterate(text))[2]
    return ("ucs2-avoidable",
            "%d segment(s) as UCS-2 against %d after transliteration: %d extra "
            "segment(s) on every send of this body, caused by %s."
            % (count, clean, count - clean, describe(fixable[:4])))


def tally(messages):
    """Bucket outbound messages by sender and add up the avoidable segments.

    Pure. Inbound messages are skipped: their encoding is the sender's problem
    and you are not billed by the segment for receiving them.
    """
    rows = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        body = str(m.get("body") or "")
        if not body.strip():
            continue
        key = m.get("messaging_service_sid") or m.get("from") or "unknown sender"
        row = rows.setdefault(key, {"total": 0, "ucs2": 0, "extra": 0,
                                    "chars": [], "sids": []})
        row["total"] += 1
        state, _ = verdict(body, m.get("num_segments"))
        if state == "gsm-7":
            continue
        row["ucs2"] += 1
        if state == "ucs2-avoidable":
            row["extra"] += segments(body)[2] - segments(transliterate(body))[2]
        for c, _sub in offenders(body):
            if c not in row["chars"]:
                row["chars"].append(c)
        if len(row["sids"]) < 3:
            row["sids"].append(m.get("sid"))
    return rows


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. Nothing to filter on: this failure has no error
    code, so the window and the cap are the only bounds there are."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def smart_encoding_by_service(session):
    """Map service sid to its smart_encoding flag. next_page_url is absolute on
    this API, unlike the relative next_page_uri on the 2010 one."""
    url = "%s/Services" % MESSAGING
    params = {"PageSize": 50}
    out = {}
    while url:
        page = get(session, url, **params)
        for s in page.get("services", []):
            out[s.get("sid")] = bool(s.get("smart_encoding"))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
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

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = list_messages(session, account, since, args.max_messages)
    if not messages:
        log.info("no messages sent since %s", since)
        return 0

    senders = tally(messages)
    services = smart_encoding_by_service(session)

    extra = 0
    for sender, stats in sorted(senders.items()):
        if not stats["ucs2"]:
            log.info("%-15s %s  %d message(s), all GSM-7",
                     "gsm-7", sender, stats["total"])
            continue
        extra += stats["extra"]
        state = "inflated" if stats["extra"] else "ucs2"
        log.warning("%-15s %s  %d of %d message(s) in UCS-2, %d extra "
                    "segment(s) over the window, offenders: %s",
                    state, sender, stats["ucs2"], stats["total"], stats["extra"],
                    describe(stats["chars"][:6]))
        log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
        if str(sender).startswith("MG"):
            if services.get(sender):
                log.warning("  smart_encoding is already true on %s: what is "
                            "left is genuinely non-GSM content, or a template "
                            "using characters the substitution table misses.",
                            sender)
            else:
                log.warning("  repair: POST %s/Services/%s SmartEncoding=true, "
                            "and normalise curly quotes and dashes where the "
                            "template is authored.", MESSAGING, sender)
        else:
            log.warning("  repair: this sent with a bare From, so no Messaging "
                        "Service and no Smart Encoding to enable. Send through "
                        "a service, or normalise the body before the call.")

    log.info("%d sender(s) over %d day(s), %d extra segment(s) from avoidable "
             "UCS-2", len(senders), args.days, extra)
    return 1 if extra else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-segment-audit.mjs",
"js": '''/**
 * Report Twilio messages inflated into UCS-2 by a handful of characters.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

// GSM 03.38, the alphabet a single segment of 160 characters is drawn from.
const GSM_BASIC = new Set(
  '@£$¥èéùìòÇØøÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !#¤%&()*+,-./0123456789:;<=>?' +
  '¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà');
// Double quote, apostrophe, newline and carriage return, kept out of the
// literal above so it does not fight the quoting.
for (const code of [34, 39, 10, 13]) GSM_BASIC.add(String.fromCharCode(code));

// The extension table: GSM-7, but two units each.
const GSM_EXT = new Set('^{}[~]|€');
GSM_EXT.add(String.fromCharCode(92)); // backslash

const GSM_SINGLE = 160, GSM_MULTI = 153;
const UCS_SINGLE = 70, UCS_MULTI = 67;

// What Smart Encoding substitutes, near enough.
const TRANSLITERATE = new Map(Object.entries({
  '‘': "'", '’': "'", '‚': "'", '‛': "'",
  '′': "'", '´': "'", 'ʼ': "'",
  '“': '"', '”': '"', '„': '"', '«': '"', '»': '"',
  '–': '-', '—': '-', '−': '-',
  '…': '...', ' ': ' ', '•': '*', '™': 'TM',
}));

/**
 * GSM-7 if every character is in the GSM alphabet, UCS-2 otherwise. Pure. The
 * choice is per message: one character outside the alphabet moves the whole
 * body to 70 characters a segment.
 */
export function smsEncoding(body) {
  for (const c of String(body ?? '')) {
    if (!GSM_BASIC.has(c) && !GSM_EXT.has(c)) return 'UCS-2';
  }
  return 'GSM-7';
}

/**
 * Return [encoding, units, segmentCount]. Pure. Units, not characters: an
 * extension character costs two in GSM-7, and anything outside the Basic
 * Multilingual Plane costs two UTF-16 code units in UCS-2.
 */
export function segments(body) {
  const text = String(body ?? '');
  const encoding = smsEncoding(text);
  let units = 0;
  for (const c of text) {
    if (encoding === 'GSM-7') units += GSM_EXT.has(c) ? 2 : 1;
    else units += c.codePointAt(0) > 0xFFFF ? 2 : 1;
  }
  const single = encoding === 'GSM-7' ? GSM_SINGLE : UCS_SINGLE;
  const multi = encoding === 'GSM-7' ? GSM_MULTI : UCS_MULTI;
  return [encoding, units, units <= single ? 1 : Math.ceil(units / multi)];
}

/**
 * Every distinct character forcing UCS-2, with its substitute or null. Pure.
 * null means nothing can stand in for it, and UCS-2 is correct.
 */
export function offenders(body) {
  const out = [];
  const seen = new Set();
  for (const c of String(body ?? '')) {
    if (GSM_BASIC.has(c) || GSM_EXT.has(c) || seen.has(c)) continue;
    seen.add(c);
    out.push([c, TRANSLITERATE.get(c) ?? null]);
  }
  return out;
}

/** The body as Smart Encoding would rewrite it. Pure. */
export function transliterate(body) {
  return [...String(body ?? '')].map((c) => TRANSLITERATE.get(c) ?? c).join('');
}

export function describe(chars) {
  return chars.map((c) =>
    `${c} (U+${c.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')})`)
    .join(', ');
}

/**
 * Classify one message body. Pure, and the whole point of this script.
 * `reported` is num_segments as Twilio billed it; lower than the raw cost means
 * Smart Encoding rewrote the message on the way out. Returns [state, detail].
 */
export function verdict(body, reported = null) {
  const text = String(body ?? '');
  const [encoding, units, count] = segments(text);
  if (encoding === 'GSM-7') {
    return ['gsm-7', `${count} segment(s), GSM-7, ${units} unit(s)`];
  }

  if (reported !== null && reported !== undefined) {
    const billed = Number(reported);
    if (Number.isFinite(billed) && billed < count) {
      return ['smart-encoded',
        `billed ${billed} segment(s), not the ${count} this body costs as ` +
        'UCS-2: Smart Encoding rewrote it on the way out, so the template is ' +
        'still wrong and a setting is paying for it.'];
    }
  }

  const found = offenders(text);
  const fixable = found.filter(([, sub]) => sub !== null).map(([c]) => c);
  const stuck = found.filter(([, sub]) => sub === null).map(([c]) => c);

  if (stuck.length) {
    return ['ucs2-required',
      `${count} segment(s) as UCS-2, ${units} unit(s). Nothing to strip: ` +
      `${describe(stuck.slice(0, 4))} cannot be transliterated, so UCS-2 is ` +
      'correct here and the cost is expected rather than accidental.'];
  }

  const clean = segments(transliterate(text))[2];
  return ['ucs2-avoidable',
    `${count} segment(s) as UCS-2 against ${clean} after transliteration: ` +
    `${count - clean} extra segment(s) on every send of this body, caused by ` +
    `${describe(fixable.slice(0, 4))}.`];
}

/**
 * Bucket outbound messages by sender and add up the avoidable segments. Pure.
 */
export function tally(messages) {
  const rows = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const body = String(m.body ?? '');
    if (!body.trim()) continue;
    const key = m.messaging_service_sid || m.from || 'unknown sender';
    if (!rows.has(key)) rows.set(key, { total: 0, ucs2: 0, extra: 0, chars: [], sids: [] });
    const row = rows.get(key);
    row.total += 1;
    const [state] = verdict(body, m.num_segments ?? null);
    if (state === 'gsm-7') continue;
    row.ucs2 += 1;
    if (state === 'ucs2-avoidable') {
      row.extra += segments(body)[2] - segments(transliterate(body))[2];
    }
    for (const [c] of offenders(body)) if (!row.chars.includes(c)) row.chars.push(c);
    if (row.sids.length < 3) row.sids.push(m.sid);
  }
  return rows;
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

async function smartEncodingByService(auth) {
  let url = `${MESSAGING}/Services`;
  let params = { PageSize: 50 };
  const out = new Map();
  while (url) {
    const page = await get(auth, url, params);
    for (const s of page.services ?? []) out.set(s.sid, Boolean(s.smart_encoding));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out;
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
  const days = flag('--days', 7);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since, flag('--max-messages', 20000));
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  const senders = tally(messages);
  const services = await smartEncodingByService(auth);

  let extra = 0;
  for (const sender of [...senders.keys()].sort()) {
    const stats = senders.get(sender);
    if (!stats.ucs2) {
      console.log(`gsm-7           ${sender}  ${stats.total} message(s), all GSM-7`);
      continue;
    }
    extra += stats.extra;
    const state = stats.extra ? 'inflated' : 'ucs2';
    console.warn(`${state.padEnd(15)} ${sender}  ${stats.ucs2} of ${stats.total} ` +
                 `message(s) in UCS-2, ${stats.extra} extra segment(s) over the ` +
                 `window, offenders: ${describe(stats.chars.slice(0, 6))}`);
    console.warn(`  message sids: ${stats.sids.join(', ')}`);
    if (String(sender).startsWith('MG')) {
      if (services.get(sender)) {
        console.warn(`  smart_encoding is already true on ${sender}: what is left ` +
                     'is genuinely non-GSM content, or characters the ' +
                     'substitution table misses.');
      } else {
        console.warn(`  repair: POST ${MESSAGING}/Services/${sender} ` +
                     'SmartEncoding=true, and normalise curly quotes and dashes ' +
                     'where the template is authored.');
      }
    } else {
      console.warn('  repair: this sent with a bare From, so no Messaging Service ' +
                   'and no Smart Encoding to enable. Send through a service, or ' +
                   'normalise the body before the call.');
    }
  }

  console.log(`${senders.size} sender(s) over ${days} day(s), ${extra} extra ` +
              'segment(s) from avoidable UCS-2');
  process.exitCode = extra ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// run main(), fail on the missing credentials and set a non-zero exit code.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "This is the classifier worth testing hardest, because every number it produces is money. The cases below pin the boundaries the arithmetic turns on: 160 characters against 161, an extension character costing two units, a 150 character body going from one segment to three on one curly apostrophe, and an emoji correctly reported as something no transliteration can rescue.",
"test_py_file": "test_twilio_segment_audit.py",
"test_py": '''from twilio_segment_audit import (offenders, segments, sms_encoding, tally,
                                  transliterate, verdict)

CURLY = "’"     # right single quotation mark, the usual culprit
PARTY = "\U0001F389"  # an emoji, outside the Basic Multilingual Plane


def test_plain_ascii_is_gsm7():
    assert sms_encoding("Your code is 123456") == "GSM-7"


def test_one_curly_apostrophe_moves_the_whole_body_to_ucs2():
    assert sms_encoding("It%ss ready" % CURLY) == "UCS-2"


def test_gsm7_segment_boundary_is_160_then_153():
    assert segments("a" * 160) == ("GSM-7", 160, 1)
    assert segments("a" * 161)[2] == 2
    assert segments("a" * 306)[2] == 2
    assert segments("a" * 307)[2] == 3


def test_extension_characters_cost_two_units():
    # 80 euro signs is 160 units: still one segment, but at half the characters.
    assert segments("€" * 80) == ("GSM-7", 160, 1)
    assert segments("€" * 81)[2] == 2


def test_ucs2_segment_boundary_is_70_then_67():
    body = "а" * 70  # Cyrillic
    assert segments(body) == ("UCS-2", 70, 1)
    assert segments("а" * 71)[2] == 2


def test_an_emoji_costs_two_utf16_units():
    encoding, units, count = segments(PARTY * 40)
    assert encoding == "UCS-2"
    assert units == 80
    assert count == 2


def test_one_smart_quote_turns_one_segment_into_three():
    body = "a" * 149 + CURLY
    state, detail = verdict(body)
    assert state == "ucs2-avoidable"
    assert segments(body)[2] == 3
    assert segments(transliterate(body))[2] == 1
    assert "2 extra segment(s)" in detail


def test_an_emoji_is_ucs2_that_nothing_can_fix():
    state, detail = verdict("Sale today " + PARTY)
    assert state == "ucs2-required"
    assert "cannot be transliterated" in detail


def test_billing_fewer_segments_means_smart_encoding_already_ran():
    state, detail = verdict("a" * 149 + CURLY, reported=1)
    assert state == "smart-encoded"
    assert "still wrong" in detail


def test_offenders_are_deduplicated_and_carry_their_substitute():
    found = offenders("%s%s ok %s" % (CURLY, CURLY, PARTY))
    assert [c for c, _ in found] == [CURLY, PARTY]
    assert found[0][1] == chr(39)
    assert found[1][1] is None


def test_tally_adds_up_the_avoidable_segments_per_sender():
    body = "a" * 149 + CURLY
    rows = tally([
        {"sid": "SM1", "messaging_service_sid": "MG1", "body": body},
        {"sid": "SM2", "messaging_service_sid": "MG1", "body": body},
        {"sid": "SM3", "messaging_service_sid": "MG1", "body": "plain text"},
        {"sid": "SM4", "from": "+15550001111", "direction": "inbound", "body": body},
    ])
    assert list(rows) == ["MG1"]
    assert rows["MG1"] == {"total": 3, "ucs2": 2, "extra": 4,
                           "chars": [CURLY], "sids": ["SM1", "SM2"]}
''',
"test_js_file": "twilio-segment-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { offenders, segments, smsEncoding, tally, transliterate, verdict }
  from './twilio-segment-audit.mjs';

const CURLY = '’';       // right single quotation mark, the usual culprit
const PARTY = '🎉'; // an emoji, outside the Basic Multilingual Plane

test('plain ascii is gsm-7', () => {
  assert.equal(smsEncoding('Your code is 123456'), 'GSM-7');
});

test('one curly apostrophe moves the whole body to ucs-2', () => {
  assert.equal(smsEncoding(`It${CURLY}s ready`), 'UCS-2');
});

test('gsm-7 segment boundary is 160 then 153', () => {
  assert.deepEqual(segments('a'.repeat(160)), ['GSM-7', 160, 1]);
  assert.equal(segments('a'.repeat(161))[2], 2);
  assert.equal(segments('a'.repeat(306))[2], 2);
  assert.equal(segments('a'.repeat(307))[2], 3);
});

test('extension characters cost two units', () => {
  assert.deepEqual(segments('€'.repeat(80)), ['GSM-7', 160, 1]);
  assert.equal(segments('€'.repeat(81))[2], 2);
});

test('ucs-2 segment boundary is 70 then 67', () => {
  assert.deepEqual(segments('а'.repeat(70)), ['UCS-2', 70, 1]);
  assert.equal(segments('а'.repeat(71))[2], 2);
});

test('an emoji costs two utf-16 units', () => {
  assert.deepEqual(segments(PARTY.repeat(40)), ['UCS-2', 80, 2]);
});

test('one smart quote turns one segment into three', () => {
  const body = 'a'.repeat(149) + CURLY;
  const [state, detail] = verdict(body);
  assert.equal(state, 'ucs2-avoidable');
  assert.equal(segments(body)[2], 3);
  assert.equal(segments(transliterate(body))[2], 1);
  assert.match(detail, /2 extra segment\\(s\\)/);
});

test('an emoji is ucs-2 that nothing can fix', () => {
  const [state, detail] = verdict(`Sale today ${PARTY}`);
  assert.equal(state, 'ucs2-required');
  assert.match(detail, /cannot be transliterated/);
});

test('billing fewer segments means smart encoding already ran', () => {
  const [state, detail] = verdict('a'.repeat(149) + CURLY, 1);
  assert.equal(state, 'smart-encoded');
  assert.match(detail, /still wrong/);
});

test('offenders are deduplicated and carry their substitute', () => {
  const found = offenders(`${CURLY}${CURLY} ok ${PARTY}`);
  assert.deepEqual(found.map(([c]) => c), [CURLY, PARTY]);
  assert.equal(found[0][1], "'");
  assert.equal(found[1][1], null);
});

test('tally adds up the avoidable segments per sender', () => {
  const body = 'a'.repeat(149) + CURLY;
  const rows = tally([
    { sid: 'SM1', messaging_service_sid: 'MG1', body },
    { sid: 'SM2', messaging_service_sid: 'MG1', body },
    { sid: 'SM3', messaging_service_sid: 'MG1', body: 'plain text' },
    { sid: 'SM4', from: '+15550001111', direction: 'inbound', body },
  ]);
  assert.deepEqual([...rows.keys()], ['MG1']);
  assert.deepEqual(rows.get('MG1'), { total: 3, ucs2: 2, extra: 4,
                                      chars: [CURLY], sids: ['SM1', 'SM2'] });
});
''',
"faq": [
 ("Which characters actually force UCS-2?",
  "Anything outside the GSM 03.38 alphabet. In practice: curly quotes and apostrophes, en and em dashes, the ellipsis character, non-breaking spaces, bullets, most accented letters beyond the handful GSM includes, every emoji, and every non-Latin script. The GSM set does include à, ä, é, ö, ñ, ü, £, ¥ and €, which is why some accented copy stays cheap and some does not."),
 ("Why does one character cost so much?",
  "Because the encoding is chosen for the whole message. GSM-7 fits 160 characters in a single segment and 153 in each concatenated one; UCS-2 fits 70 and 67. A 150 character body is one segment as GSM-7 and three as UCS-2, so a single curly apostrophe is a 200% price rise on every send of that template."),
 ("Does Smart Encoding fix all of it?",
  "It fixes the accidental part. Smart Encoding substitutes look-alike GSM characters for the common offenders, which is exactly right for a curly quote that a rich text editor inserted. It cannot help an emoji or a Cyrillic word, and it should not: those messages need UCS-2, and the script reports them separately so you are not chasing a saving that does not exist."),
 ("Why recompute the encoding when num_segments is right there?",
  "Because num_segments tells you the cost and not the cause. Recomputing from the body names the character responsible and says what the same message would have cost without it. Comparing the two numbers is also the only way to notice that Smart Encoding is quietly rescuing a template that is still wrong."),
 ("Can the script enable Smart Encoding itself?",
  "No. Everything in this section is read-only, and this one holds a credential to an account that can spend money. It prints the exact POST against the Messaging Service, with the service SID, for you to run."),
],
"related": [
 ("/twilio/body-exceeds-1600-chars-21617/", "Rendered bodies that blow past the 1600 character limit"),
 ("/twilio/messaging-queue-overflow-30001/", "A send loop that overflows one sender's queue"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering drops SMS with error 30007"),
],
"citations": [CITE_SERVICE, CITE_SERVICES, CITE_MSG, CITE_USAGE],
},


{
"slug": "messaging-queue-overflow-30001",
"title": "Queue overflow 30001: a send loop outruns one long code",
"description": "Bulk sends through one long code fail with error_code 30001. The queue holds about ten hours of segments at 1 MPS, and the producer outruns it.",
"h1": "queue overflow 30001: a send loop outruns one long code",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 30001", "twilio queue overflow",
             "twilio error 21611", "twilio messages per second",
             "twilio long code throughput"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The nightly job dispatched forty thousand messages in about eleven minutes, the way it always has. This time six thousand of them came back with <code>error_code</code> <code>30001</code>, some of the rest were rejected at request time with <code>21611</code>, and the ones that survived arrived the following afternoon. Nothing in the code changed. The list got longer, and a single long code can only send about one message a second.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, keep rows where <code>error_code</code> is <code>30001</code> or <code>21611</code>, and group them by <code>from</code> &mdash; the queue belongs to the sender, not to the account.</p>
<p>Then do the arithmetic that predicts the next failure: total the <code>num_segments</code> you pushed at each sender and divide by that sender's throughput. A US long code is around 1 MPS, and its queue holds roughly ten hours of segments. Forty thousand segments at 1 MPS is eleven hours, and eleven does not fit into ten.</p>""",
"problem": """<p>Throughput in SMS is a property of the sender, not of your account or your plan. A US long code sends about one message segment per second. A toll-free number is faster, a short code faster again. Twilio accepts everything you hand it and queues it against that sender, and the queue is finite: roughly ten hours of segments at that sender's rate.</p>
<p>Below the ceiling this is invisible &mdash; you send in a burst, Twilio drains at 1 MPS, everything arrives, nobody notices there was a queue. Above it, two failures appear at once. Messages already queued start expiring or being rejected with <code>30001</code>, and new requests come back at the API with <code>21611</code>, the request-time version of the same wall.</p>
<p>What makes it a Tuesday-night incident rather than a capacity plan is that the list grows gradually and the wall does not move. The job that took eight hours to drain last month takes eleven this month, and eleven is on the wrong side of the line.</p>""",
"why": """<p><strong>The queue is per sender.</strong> One long code has one queue. Adding a second application server, a bigger worker pool or more parallel requests changes nothing at all &mdash; it only fills the same queue faster.</p>
<p><strong>Segments are the unit, not messages.</strong> A three-segment message occupies three slots. A campaign that drifted into UCS-2 tripled its segment count without changing its message count, which is how a job that fit last month stops fitting without anybody sending more.</p>
<p><strong>30001 and 21611 are the same wall from two sides.</strong> 21611 rejects the request because the queue for that <code>From</code> is already full; 30001 fails a message that got in and could not be drained in time. An audit that reads only one of them reports half an incident.</p>
<p><strong>The Messages list has no error filter.</strong> No <code>Status</code> parameter, no <code>ErrorCode</code> parameter &mdash; only <code>To</code>, <code>From</code>, <code>DateSent</code> and paging. Both codes have to be found by paging the window and filtering client-side, which is also the only way to total the segments per sender.</p>""",
"steps": [
 {"h": "Page the Messages list over the window that contains the job",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. A bulk run is exactly the case where the message cap matters, so bound it and say so in the output rather than paging a hundred thousand rows to reach the same conclusion.</p>"""},
 {"h": "Keep 30001 and 21611 together, grouped by sender",
  "body": """<p>Group on <code>from</code>, because that is what owns the queue. Read <code>error_code</code> as an integer: it is <code>null</code> on healthy messages and comparing it to the string <code>"30001"</code> silently matches nothing.</p>"""},
 {"h": "Total the segments, not the messages",
  "body": """<p>Sum <code>num_segments</code> per sender. That number, divided by the sender's messages-per-second, is how many hours of sending you queued. Compare it with the ten hours or so of depth the queue has, and you have the answer before the next run rather than after it.</p>"""},
 {"h": "Check how wide the pool actually is",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> counts the senders in the Messaging Service pool. A service with one number in it has exactly the throughput of one number, whatever the code sending through it believes.</p>"""},
 {"h": "Spread the load, then rate-limit the producer",
  "body": """<p>Send through a Messaging Service (<code>MessagingServiceSid=MG…</code>) rather than a bare <code>From</code>, add senders with <code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code>, and cap the producer at what the pool can physically drain. For genuine bulk volume, escalate to toll-free or a short code rather than adding long codes one at a time.</p>"""},
],
"verify": """<p>Re-run over the window covering the next bulk run. Every sender should report <code>clean</code> or <code>draining</code>, and no sender should be over capacity.</p>
<pre><code class="language-bash">python3 twilio_queue_overflow_audit.py --days 2 --mps 1
# 6 sender(s) over 2 day(s), 0 over capacity</code></pre>""",
"code_intro": "One paginated <code>GET</code> over the Messages list, plus one per Messaging Service to count its pool. The arithmetic is where the value is &mdash; segments divided by throughput against the depth of the queue &mdash; so it is a pure function taking the sender's MPS as an argument, because 1 MPS is right for a US long code and wrong for everything else.",
"py_file": "twilio_queue_overflow_audit.py",
"py": '''"""Report Twilio senders whose queue is overflowing with 30001 or 21611.

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
log = logging.getLogger("twilio_queue_overflow_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

# The same wall from two sides: 21611 rejects the request because the queue for
# that From is full, 30001 fails a message that got in and never drained.
OVERFLOW = (30001, 21611)
WAITING = ("queued", "accepted", "scheduled", "sending")


def error_code(message):
    """Read error_code as an integer, or None.

    It is null on every healthy message. Comparing the raw value against 30001
    is the mistake that reports a clean account the morning after an overflow.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def queue_hours(segments, mps):
    """How many hours of sending a pile of segments represents. Pure.

    Segments, not messages: a three-segment body occupies three slots in the
    sender's queue.
    """
    rate = max(float(mps or 0), 0.01)
    return segments / (rate * 3600.0)


def tally(messages):
    """Bucket outbound messages by the sender that owns the queue. Pure.

    The key is `from`, because throughput and the queue behind it belong to the
    sending number. The Messaging Service is kept alongside, since that is what
    you would widen to fix it.
    """
    rows = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        key = m.get("from") or m.get("messaging_service_sid") or "unknown sender"
        row = rows.setdefault(key, {"total": 0, "overflow": 0, "queued": 0,
                                    "segments": 0, "service": None, "sids": []})
        row["total"] += 1
        try:
            row["segments"] += max(int(m.get("num_segments") or 1), 1)
        except (TypeError, ValueError):
            row["segments"] += 1
        if m.get("messaging_service_sid"):
            row["service"] = m.get("messaging_service_sid")
        if str(m.get("status") or "").lower() in WAITING:
            row["queued"] += 1
        if error_code(m) in OVERFLOW:
            row["overflow"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
    return rows


def verdict(stats, mps=1.0, capacity_hours=10.0):
    """Classify one sender against what it can physically drain. Pure, so the
    throughput assumption is an argument rather than a hidden constant.

    Returns (state, detail).
    """
    total = int(stats.get("total") or 0)
    overflow = int(stats.get("overflow") or 0)
    waiting = int(stats.get("queued") or 0)
    segments = int(stats.get("segments") or 0) or total
    hours = queue_hours(segments, mps)
    tail = ("" if stats.get("service") else
            " Sent with a bare From, so there is one queue and no pool to spread "
            "it over.")

    if overflow:
        return ("overflow",
                "%d of %d rejected with 30001 or 21611. %d segment(s) is %.1f "
                "hours of sending at %.2f MPS, against a queue that holds about "
                "%.0f.%s" % (overflow, total, segments, hours, mps,
                             capacity_hours, tail))

    if hours >= capacity_hours:
        return ("over-capacity",
                "%d segment(s) is %.1f hours at %.2f MPS, past the roughly %.0f "
                "hour queue. Nothing failed yet, and the next run this size "
                "overflows.%s" % (segments, hours, mps, capacity_hours, tail))

    if hours >= capacity_hours / 2:
        return ("near-capacity",
                "%d segment(s) is %.1f hours at %.2f MPS against a queue of "
                "about %.0f. One retry storm, one duplicate batch or one "
                "template drifting into UCS-2 away from 30001.%s"
                % (segments, hours, mps, capacity_hours, tail))

    if waiting:
        return ("draining",
                "%d message(s) still queued or accepted; %d segment(s) is %.1f "
                "hours at %.2f MPS.%s" % (waiting, segments, hours, mps, tail))

    return ("clean", "%d message(s), %d segment(s), about %.1f hours at %.2f MPS"
            % (total, segments, hours, mps))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. There is no Status or ErrorCode filter here, so both
    error codes have to be found client-side."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def pool_size(session, service_sid):
    """Count the senders in a Messaging Service pool. A service with one number
    has the throughput of one number."""
    url = "%s/Services/%s/PhoneNumbers" % (MESSAGING, service_sid)
    params = {"PageSize": 100}
    count = 0
    while url:
        page = get(session, url, **params)
        count += len(page.get("phone_numbers", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=2,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=50000,
                    help="stop paging after this many messages")
    ap.add_argument("--mps", type=float, default=1.0,
                    help="segments per second for these senders: about 1 for a "
                         "US long code, higher for toll-free or a short code")
    ap.add_argument("--capacity-hours", type=float, default=10.0,
                    help="how many hours of segments the sender queue holds")
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
    pools = {}
    bad = 0
    for sender, stats in sorted(senders.items()):
        state, detail = verdict(stats, args.mps, args.capacity_hours)
        line = "%-14s %s  %s" % (state, sender, detail)
        if state in ("clean", "draining"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if stats["sids"]:
            log.warning("  message sids: %s",
                        ", ".join(str(s) for s in stats["sids"]))
        service = stats.get("service")
        if service:
            if service not in pools:
                pools[service] = pool_size(session, service)
            log.warning("  %s has %d sender(s) in its pool: that is the "
                        "throughput you actually have.", service, pools[service])
            log.warning("  repair: POST %s/Services/%s/PhoneNumbers "
                        "PhoneNumberSid=PN... to widen the pool, and rate-limit "
                        "the producer to what the pool can drain.",
                        MESSAGING, service)
        else:
            log.warning("  repair: send through a Messaging Service "
                        "(MessagingServiceSid=MG...) instead of a bare From, add "
                        "senders to its pool, and rate-limit the producer. For "
                        "volume at this scale, toll-free or a short code.")

    log.info("%d sender(s) over %d day(s), %d over capacity",
             len(senders), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-queue-overflow-audit.mjs",
"js": '''/**
 * Report Twilio senders whose queue is overflowing with 30001 or 21611.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

// The same wall from two sides: 21611 rejects the request because the queue for
// that From is full, 30001 fails a message that got in and never drained.
const OVERFLOW = new Set([30001, 21611]);
const WAITING = new Set(['queued', 'accepted', 'scheduled', 'sending']);

/**
 * Read error_code as a number, or null. It is null on healthy messages, and
 * comparing the raw value is how the audit reports a clean account the morning
 * after an overflow.
 */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * How many hours of sending a pile of segments represents. Pure. Segments, not
 * messages: a three-segment body occupies three slots in the queue.
 */
export function queueHours(segments, mps) {
  const rate = Math.max(Number(mps) || 0, 0.01);
  return segments / (rate * 3600);
}

/**
 * Bucket outbound messages by the sender that owns the queue. Pure. The key is
 * `from`, because throughput belongs to the sending number.
 */
export function tally(messages) {
  const rows = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const key = m.from || m.messaging_service_sid || 'unknown sender';
    if (!rows.has(key)) {
      rows.set(key, { total: 0, overflow: 0, queued: 0, segments: 0,
                      service: null, sids: [] });
    }
    const row = rows.get(key);
    row.total += 1;
    row.segments += Math.max(Number(m.num_segments ?? 1) || 1, 1);
    if (m.messaging_service_sid) row.service = m.messaging_service_sid;
    if (WAITING.has(String(m.status ?? '').toLowerCase())) row.queued += 1;
    if (OVERFLOW.has(errorCode(m))) {
      row.overflow += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
    }
  }
  return rows;
}

/**
 * Classify one sender against what it can physically drain. Pure, so the
 * throughput assumption is an argument. Returns [state, detail].
 */
export function verdict(stats, mps = 1.0, capacityHours = 10.0) {
  const total = Number(stats.total ?? 0);
  const overflow = Number(stats.overflow ?? 0);
  const waiting = Number(stats.queued ?? 0);
  const segments = Number(stats.segments ?? 0) || total;
  const hours = queueHours(segments, mps);
  const h = hours.toFixed(1);
  const rate = Number(mps).toFixed(2);
  const cap = capacityHours.toFixed(0);
  const tail = stats.service ? ''
    : ' Sent with a bare From, so there is one queue and no pool to spread it over.';

  if (overflow) {
    return ['overflow',
      `${overflow} of ${total} rejected with 30001 or 21611. ${segments} ` +
      `segment(s) is ${h} hours of sending at ${rate} MPS, against a queue ` +
      `that holds about ${cap}.${tail}`];
  }

  if (hours >= capacityHours) {
    return ['over-capacity',
      `${segments} segment(s) is ${h} hours at ${rate} MPS, past the roughly ` +
      `${cap} hour queue. Nothing failed yet, and the next run this size ` +
      `overflows.${tail}`];
  }

  if (hours >= capacityHours / 2) {
    return ['near-capacity',
      `${segments} segment(s) is ${h} hours at ${rate} MPS against a queue of ` +
      `about ${cap}. One retry storm, one duplicate batch or one template ` +
      `drifting into UCS-2 away from 30001.${tail}`];
  }

  if (waiting) {
    return ['draining',
      `${waiting} message(s) still queued or accepted; ${segments} segment(s) ` +
      `is ${h} hours at ${rate} MPS.${tail}`];
  }

  return ['clean',
    `${total} message(s), ${segments} segment(s), about ${h} hours at ${rate} MPS`];
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

async function poolSize(auth, serviceSid) {
  let url = `${MESSAGING}/Services/${serviceSid}/PhoneNumbers`;
  let params = { PageSize: 100 };
  let count = 0;
  while (url) {
    const page = await get(auth, url, params);
    count += (page.phone_numbers ?? []).length;
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return count;
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
  const days = flag('--days', 2);
  const mps = flag('--mps', 1.0);
  const capacityHours = flag('--capacity-hours', 10.0);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, since, flag('--max-messages', 50000));
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    return;
  }

  const senders = tally(messages);
  const pools = new Map();
  let bad = 0;
  for (const sender of [...senders.keys()].sort()) {
    const stats = senders.get(sender);
    const [state, detail] = verdict(stats, mps, capacityHours);
    const line = `${state.padEnd(14)} ${sender}  ${detail}`;
    if (state === 'clean' || state === 'draining') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (stats.sids.length) console.warn(`  message sids: ${stats.sids.join(', ')}`);
    if (stats.service) {
      if (!pools.has(stats.service)) {
        pools.set(stats.service, await poolSize(auth, stats.service));
      }
      console.warn(`  ${stats.service} has ${pools.get(stats.service)} sender(s) ` +
                   'in its pool: that is the throughput you actually have.');
      console.warn(`  repair: POST ${MESSAGING}/Services/${stats.service}` +
                   '/PhoneNumbers PhoneNumberSid=PN... to widen the pool, and ' +
                   'rate-limit the producer to what the pool can drain.');
    } else {
      console.warn('  repair: send through a Messaging Service ' +
                   '(MessagingServiceSid=MG...) instead of a bare From, add ' +
                   'senders to its pool, and rate-limit the producer. For volume ' +
                   'at this scale, toll-free or a short code.');
    }
  }

  console.log(`${senders.size} sender(s) over ${days} day(s), ${bad} over capacity`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// run main(), fail on the missing credentials and set a non-zero exit code.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the arithmetic and the one grouping decision that changes the answer: segments rather than messages, <code>from</code> rather than the Messaging Service, and both error codes counted as one wall. The last case is the useful one &mdash; a sender with no failures at all that is already past ten hours of queue, which is the report you want the week before the incident.",
"test_py_file": "test_twilio_queue_overflow_audit.py",
"test_py": '''from twilio_queue_overflow_audit import queue_hours, tally, verdict


def sent(sid, sender, **extra):
    row = {"sid": sid, "from": sender, "status": "delivered", "num_segments": 1}
    row.update(extra)
    return row


def test_ten_hours_is_thirty_six_thousand_segments_at_one_mps():
    assert queue_hours(36000, 1) == 10.0
    assert round(queue_hours(3600, 0.5), 1) == 2.0


def test_a_zero_rate_does_not_divide_by_zero():
    assert queue_hours(100, 0) > 0


def test_tally_groups_by_sending_number_and_counts_segments():
    rows = tally([
        sent("SM1", "+15550001111", num_segments="3"),
        sent("SM2", "+15550001111", status="queued"),
        sent("SM3", "+15550002222", messaging_service_sid="MG1"),
        {"sid": "SM4", "from": "+15550001111", "direction": "inbound"},
    ])
    assert sorted(rows) == ["+15550001111", "+15550002222"]
    assert rows["+15550001111"]["segments"] == 4
    assert rows["+15550001111"]["queued"] == 1
    assert rows["+15550001111"]["service"] is None
    assert rows["+15550002222"]["service"] == "MG1"


def test_both_error_codes_count_as_the_same_wall():
    rows = tally([
        sent("SM1", "+1555", error_code=30001, status="failed"),
        sent("SM2", "+1555", error_code="21611", status="failed"),
        sent("SM3", "+1555"),
    ])
    assert rows["+1555"]["overflow"] == 2
    assert rows["+1555"]["sids"] == ["SM1", "SM2"]


def test_overflow_errors_are_the_headline():
    state, detail = verdict({"total": 40000, "overflow": 6000, "segments": 40000,
                             "service": "MG1"})
    assert state == "overflow"
    assert "11.1 hours" in detail


def test_a_sender_past_the_queue_depth_is_flagged_before_it_fails():
    state, detail = verdict({"total": 40000, "segments": 40000, "service": "MG1"})
    assert state == "over-capacity"
    assert "Nothing failed yet" in detail


def test_half_the_queue_is_already_worth_saying():
    state, detail = verdict({"total": 20000, "segments": 20000, "service": "MG1"})
    assert state == "near-capacity"
    assert "UCS-2" in detail


def test_a_bare_from_says_so():
    _, detail = verdict({"total": 40000, "segments": 40000})
    assert "bare From" in detail


def test_messages_still_waiting_are_draining_not_broken():
    state, detail = verdict({"total": 900, "segments": 900, "queued": 40,
                             "service": "MG1"})
    assert state == "draining"
    assert "40 message(s)" in detail


def test_a_small_run_is_clean():
    state, detail = verdict({"total": 100, "segments": 100, "service": "MG1"})
    assert state == "clean"
    assert "100 segment(s)" in detail


def test_three_segment_bodies_fill_the_queue_three_times_faster():
    # The same 18,000 messages, one segment each and then three each.
    assert verdict({"total": 18000, "segments": 18000, "service": "MG1"})[0] == "near-capacity"
    assert verdict({"total": 18000, "segments": 54000, "service": "MG1"})[0] == "over-capacity"
''',
"test_js_file": "twilio-queue-overflow-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { queueHours, tally, verdict } from './twilio-queue-overflow-audit.mjs';

const sent = (sid, from, extra = {}) => ({
  sid, from, status: 'delivered', num_segments: 1, ...extra,
});

test('ten hours is thirty six thousand segments at one MPS', () => {
  assert.equal(queueHours(36000, 1), 10);
  assert.equal(Number(queueHours(3600, 0.5).toFixed(1)), 2);
});

test('a zero rate does not divide by zero', () => {
  assert.ok(Number.isFinite(queueHours(100, 0)));
});

test('tally groups by sending number and counts segments', () => {
  const rows = tally([
    sent('SM1', '+15550001111', { num_segments: '3' }),
    sent('SM2', '+15550001111', { status: 'queued' }),
    sent('SM3', '+15550002222', { messaging_service_sid: 'MG1' }),
    { sid: 'SM4', from: '+15550001111', direction: 'inbound' },
  ]);
  assert.deepEqual([...rows.keys()].sort(), ['+15550001111', '+15550002222']);
  assert.equal(rows.get('+15550001111').segments, 4);
  assert.equal(rows.get('+15550001111').queued, 1);
  assert.equal(rows.get('+15550001111').service, null);
  assert.equal(rows.get('+15550002222').service, 'MG1');
});

test('both error codes count as the same wall', () => {
  const rows = tally([
    sent('SM1', '+1555', { error_code: 30001, status: 'failed' }),
    sent('SM2', '+1555', { error_code: '21611', status: 'failed' }),
    sent('SM3', '+1555'),
  ]);
  assert.equal(rows.get('+1555').overflow, 2);
  assert.deepEqual(rows.get('+1555').sids, ['SM1', 'SM2']);
});

test('overflow errors are the headline', () => {
  const [state, detail] = verdict({ total: 40000, overflow: 6000, segments: 40000,
                                    service: 'MG1' });
  assert.equal(state, 'overflow');
  assert.match(detail, /11\\.1 hours/);
});

test('a sender past the queue depth is flagged before it fails', () => {
  const [state, detail] = verdict({ total: 40000, segments: 40000, service: 'MG1' });
  assert.equal(state, 'over-capacity');
  assert.match(detail, /Nothing failed yet/);
});

test('half the queue is already worth saying', () => {
  const [state, detail] = verdict({ total: 20000, segments: 20000, service: 'MG1' });
  assert.equal(state, 'near-capacity');
  assert.match(detail, /UCS-2/);
});

test('a bare From says so', () => {
  const [, detail] = verdict({ total: 40000, segments: 40000 });
  assert.match(detail, /bare From/);
});

test('messages still waiting are draining, not broken', () => {
  const [state, detail] = verdict({ total: 900, segments: 900, queued: 40,
                                    service: 'MG1' });
  assert.equal(state, 'draining');
  assert.match(detail, /40 message\\(s\\)/);
});

test('a small run is clean', () => {
  const [state, detail] = verdict({ total: 100, segments: 100, service: 'MG1' });
  assert.equal(state, 'clean');
  assert.match(detail, /100 segment\\(s\\)/);
});

test('three segment bodies fill the queue three times faster', () => {
  assert.equal(verdict({ total: 18000, segments: 18000, service: 'MG1' })[0],
               'near-capacity');
  assert.equal(verdict({ total: 18000, segments: 54000, service: 'MG1' })[0],
               'over-capacity');
});
''',
"faq": [
 ("What exactly is the queue, and how deep is it?",
  "Each sender has its own queue, and it holds roughly ten hours of message segments at that sender's throughput. A US long code sends about one segment per second, so about 36,000 segments. A short code drains a hundred times faster and effectively never overflows on this kind of volume."),
 ("Is 21611 the same problem as 30001?",
  "It is the same wall from the other side. 21611 is returned at request time because the queue for that From is already full, so no Message is created. 30001 fails a message that made it into the queue and could not be drained. Counting only one of them reports half the incident, so the script keeps both."),
 ("Will sending through a Messaging Service make it faster?",
  "Only if the pool has more than one sender in it. A Messaging Service spreads traffic across the numbers it holds, so its throughput is the sum of theirs — which is why the script counts the pool. A service with one long code in it has exactly the throughput of one long code."),
 ("Why count segments instead of messages?",
  "Because the queue is measured in segments, and a three-segment body takes three slots. This is the mechanism behind jobs that stop fitting without anyone sending more: a template drifts into UCS-2, every message becomes three segments, and the run that took eight hours now needs twenty-four."),
 ("Should the producer just retry the failures?",
  "Not into the same sender. Retrying an overflow refills the queue that just overflowed, and the retries compete with the messages already waiting. Rate-limit the producer to what the pool can drain, widen the pool, or move the volume to toll-free or a short code."),
],
"related": [
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never leave queued or accepted"),
 ("/twilio/ucs2-segment-inflation/", "One smart quote triples the segment count"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering drops SMS with error 30007"),
],
"citations": [CITE_30001, CITE_21611, CITE_QUEUEING, CITE_SERVICE_PN],
},

]
