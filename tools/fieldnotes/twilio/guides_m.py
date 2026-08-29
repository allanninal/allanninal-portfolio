#!/usr/bin/env python3
"""/twilio/ field notes, batch M — the writing.

Four regulatory and geographic failures: a country that was never enabled for
SMS, a sender ID that was never registered where it is being used, a US or
Canadian number that cannot deliver an address to a 911 dispatcher, and a short
code selected for a destination it is not licensed to reach.

Two of these have no configuration to read. SMS Geo Permissions has no REST
resource in either direction, and no API lists which alphanumeric sender IDs a
regulator has approved for a country. Both notes therefore infer the state from
the error codes the traffic produces, and both say so in the output rather than
implying the script read a setting it cannot see.

Read-only throughout. GET requests only, and every repair is printed for a
human to run rather than performed.
"""

CITE_21408 = ("Error 21408: permission to send to this region has not been enabled "
              "— Twilio Docs", "https://www.twilio.com/docs/api/errors/21408")
CITE_MESSAGE = ("Message resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_30041 = ("Error 30041: message from a restricted or unregistered sender "
              "— Twilio Docs", "https://www.twilio.com/docs/api/errors/30041")
CITE_30040 = ("Error 30040: sender ID pre-registration required by the destination "
              "carrier — Twilio Docs", "https://www.twilio.com/docs/api/errors/30040")
CITE_ALPHA = ("AlphaSender resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/alphasender-resource")
CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_E911 = ("Emergency calling for Programmable Voice — Twilio Docs",
             "https://www.twilio.com/docs/voice/tutorials/emergency-calling-for-programmable-voice")
CITE_ADDRESS = ("Address resource — Twilio Docs",
                "https://www.twilio.com/docs/usage/api/address")
CITE_SHORTCODE = ("ShortCode resource — Twilio Docs",
                  "https://www.twilio.com/docs/messaging/api/short-code-resource")
CITE_21612 = ("Error 21612: the To phone number is not currently reachable via SMS "
              "— Twilio Docs", "https://www.twilio.com/docs/api/errors/21612")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")

GUIDES = [

{
"slug": "sms-geo-permissions-disabled",
"title": "SMS Geo Permissions are off for the destination country",
"description": "Error 21408 on every message to one country. There is no API that reads this setting, so the traffic is the only evidence you can get.",
"h1": "SMS Geo Permissions are off for the destination country",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 21408", "twilio geo permissions", "twilio international sms blocked",
             "permission to send has not been enabled", "twilio country not enabled"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The German customers onboarded this morning have received nothing. The same code, the same template and the same Messaging Service deliver perfectly at home. Every one of the failed messages carries <code>21408</code>, and there is no setting you can read through the API to confirm why &mdash; SMS Geo Permissions is a console-only switch, in both directions.",
"short_answer": """<p>There is no REST resource for SMS Geo Permissions, so this cannot be audited by reading configuration. Read the traffic instead: page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=…</code>, filter <code>error_code == 21408</code> client-side, and group by the calling code of <code>to</code>. That enumerates the countries which are, on this evidence, disabled.</p>
<p>Grouping matters more than counting. A country where every message is blocked and none was accepted is a disabled permission. A country where some messages are accepted and others carry <code>21408</code> is enabled, and those failures are <code>To</code> values resolving to a country you did not intend &mdash; which produces the identical error.</p>""",
"problem": """<p>New projects are SMS-enabled for one country: the one Twilio inferred from the phone number verified at signup. Every other destination is off until somebody turns it on in the console. Nothing about that is visible in a deployment, in a Messaging Service, or in a phone number's configuration, so it survives every review that reads configuration and fails on the first day the product has a customer abroad.</p>
<p>The error itself is honest &mdash; <code>21408</code> says permissions are disabled for the region &mdash; but it arrives one message at a time, in status callbacks and message rows, on the day of the launch. And because the setting cannot be read, nobody can answer the follow-up question of which <em>other</em> countries are also off. The only way to find out is to have already sent there and failed.</p>""",
"why": """<p><strong>The default is one country, chosen for you.</strong> Geo Permissions start enabled for the home country implied by the signup phone number. Nobody chose that country for the product, and nobody was asked to extend it, so the setting matches the founder's phone rather than the customer base.</p>
<p><strong>There is no read API and no write API.</strong> Not a resource that returns the permission list, not one that sets it. Every other note in this section ends with a printed <code>POST</code>; this one ends with a console path, because the console is the only place the switch exists. That also means no script can confirm the repair &mdash; only the next successful message can.</p>
<p><strong>The same error code covers two different faults.</strong> Permissions are evaluated on the destination country code, so a <code>To</code> value with a mangled prefix &mdash; a stripped leading zero, a national number sent without a country code, a trunk prefix left on &mdash; is judged against whichever country those digits resolve to, and rejected with <code>21408</code>. Reading the code without grouping by country turns a data-quality bug into a permissions ticket.</p>
<p><strong>Plus one is not a country.</strong> The North American numbering plan spans the US, Canada and twenty-odd Caribbean countries under a single calling code, and each is permissioned separately. An account can be fully enabled for the US and blocked for Jamaica, and both sets of numbers begin <code>+1</code>.</p>
<p><strong>Three destinations can never be enabled.</strong> Iran, Syria and Cuba are blocked outright regardless of the setting. A ticket asking for them to be switched on has no possible resolution, so they deserve their own verdict rather than being counted alongside countries a form can fix.</p>""",
"steps": [
 {"h": "Page the message list over a window you actually sent in",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. There is no <code>Status</code> or <code>ErrorCode</code> filter on this resource, so the date window and a page cap are the only ways to bound the read, and the filtering happens on your side.</p>"""},
 {"h": "Group by destination country, not by message",
  "body": """<p>Resolve the calling code of each <code>to</code> with a longest-prefix match and bucket the messages under it. One row per country is the report; a list of failed message SIDs is not, because the question being answered is which countries to enable.</p>"""},
 {"h": "Separate a disabled country from a bad To value",
  "body": """<p>Within one calling code, count what got through as well as what was blocked. Nothing accepted means the permission is off. Something accepted means it is on, and the blocked messages are <code>To</code> values that resolve elsewhere. A <code>to</code> that is not E.164 at all belongs in its own bucket for the same reason.</p>"""},
 {"h": "Corroborate against the Alerts log",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=…</code> and count <code>error_code</code> <code>21408</code>. Request-time rejections do not always leave a message row behind, and alerts are retained for 30 days, so the two surfaces bound each other: a count in Alerts with nothing in the message list means the sends are being rejected before a row exists.</p>"""},
 {"h": "Enable the countries in the console, then send again",
  "body": """<p>Console &rarr; Messaging &rarr; Settings &rarr; Geo Permissions, tick the countries, save. There is no REST equivalent to print. Check the <code>To</code> values first if the country showed accepted traffic too, because in that case the permission is not what is wrong. Then re-run this script over a fresh window: the only proof available is a message that goes through.</p>"""},
],
"verify": """<p>Send to the country again and re-run over a window that includes the new traffic. It should report <code>permitted</code>, with no country in the blocked list.</p>
<pre><code class="language-bash">python3 twilio_geo_permission_audit.py --days 3
# 6 destination(s) over 3 day(s), 0 blocked by geo permissions</code></pre>""",
"code_intro": "One paginated GET over the message list, plus one optional GET against the Alerts log. There is no configuration endpoint to read, which is the whole reason the classifier works on traffic: it takes the per-country tally and decides between a disabled permission, a malformed destination, an embargoed country and a country that is plainly working. That decision is a pure function, because it is the only part of this note that is not a request loop.",
"py_file": "twilio_geo_permission_audit.py",
"py": '''"""Report destination countries blocked by SMS Geo Permissions (error 21408).

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed, and
here it could not be anything else: SMS Geo Permissions has no REST resource in
either direction, so the switch lives in the console and the traffic is the only
evidence available.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_geo_permission_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

GEO_BLOCKED = 21408

# Blocked outright, whatever the geo permission says. A ticket asking for these
# to be enabled has no possible resolution, so they get their own verdict.
EMBARGOED = {"98": "Iran", "963": "Syria", "53": "Cuba"}

# Enough calling codes to group the destinations an account actually sends to.
# The table does not have to be exhaustive: an unrecognised prefix is itself a
# finding, because a malformed To produces the same 21408 as a disabled country.
DIAL_CODES = {
    "1": "the NANP (US, Canada and the Caribbean)", "7": "Russia or Kazakhstan",
    "20": "Egypt", "27": "South Africa", "30": "Greece", "31": "the Netherlands",
    "32": "Belgium", "33": "France", "34": "Spain", "36": "Hungary",
    "39": "Italy", "40": "Romania", "43": "Austria", "44": "the UK",
    "45": "Denmark", "46": "Sweden", "47": "Norway", "48": "Poland",
    "49": "Germany", "51": "Peru", "52": "Mexico", "53": "Cuba",
    "54": "Argentina", "55": "Brazil", "56": "Chile", "57": "Colombia",
    "58": "Venezuela", "60": "Malaysia", "61": "Australia", "62": "Indonesia",
    "63": "the Philippines", "64": "New Zealand", "65": "Singapore",
    "66": "Thailand", "81": "Japan", "82": "South Korea", "84": "Vietnam",
    "86": "China", "90": "Turkey", "91": "India", "92": "Pakistan",
    "94": "Sri Lanka", "98": "Iran", "212": "Morocco", "213": "Algeria",
    "234": "Nigeria", "254": "Kenya", "255": "Tanzania", "351": "Portugal",
    "353": "Ireland", "358": "Finland", "380": "Ukraine", "420": "Czechia",
    "421": "Slovakia", "852": "Hong Kong", "880": "Bangladesh", "886": "Taiwan",
    "963": "Syria", "966": "Saudi Arabia", "971": "the UAE", "972": "Israel",
    "977": "Nepal", "998": "Uzbekistan",
}


def error_code(message):
    """Read error_code as an integer, or None.

    Null on healthy messages, a number on failed ones, and a string in some
    exports. Comparing the raw value against 21408 is how this audit reports
    nothing on an account whose international traffic is entirely blocked.
    """
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def dial_code(to):
    """Longest matching country calling code for an E.164 destination, or None.

    None is not a shrug. Geo permissions are evaluated on the destination
    country code, so a To value Twilio cannot resolve the way you intended
    produces exactly the same 21408 as a country nobody enabled. Keeping those
    two apart is most of what this script is for.
    """
    raw = str(to or "").strip()
    if not raw.startswith("+"):
        return None
    digits = "".join(c for c in raw[1:] if c.isdigit())
    for size in (3, 2, 1):
        if digits[:size] in DIAL_CODES:
            return digits[:size]
    return None


def tally(messages):
    """Bucket outbound messages by destination country.

    Pure, so the grouping rule can be tested without a network. Inbound messages
    are skipped: they have no destination of ours and no permission to fail.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        code = dial_code(m.get("to"))
        row = out.setdefault(code, {"code": code, "total": 0, "blocked": 0,
                                    "accepted": 0, "sids": [], "examples": []})
        row["total"] += 1
        if error_code(m) == GEO_BLOCKED:
            row["blocked"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
            if len(row["examples"]) < 2 and m.get("to"):
                row["examples"].append(m.get("to"))
        else:
            # Anything that is not a 21408 got past the permission check, even
            # if a carrier rejected it later. Undelivered still means the
            # message reached the network, which is the proof we want here.
            row["accepted"] += 1
    return out


def verdict(stats):
    """Decide what one country's tally says about its geo permission.

    Pure, so the inference is visible and testable. It is an inference: there is
    no endpoint that returns the permission, so the strongest honest claim is
    about the traffic. Returns (state, detail).
    """
    code = stats.get("code")
    total = int(stats.get("total") or 0)
    blocked = int(stats.get("blocked") or 0)
    accepted = int(stats.get("accepted") or 0)

    if blocked == 0:
        return ("permitted",
                "%d message(s), none rejected with 21408" % total)

    if code is None:
        return ("unresolved-to",
                "%d of %d rejected with 21408, and the To values are not E.164 "
                "with a calling code this script can resolve. Permissions are "
                "judged on the destination country, so a mangled prefix reads as "
                "a disabled country. Fix the numbers before the setting."
                % (blocked, total))

    if code in EMBARGOED:
        return ("embargoed",
                "%d of %d to %s rejected with 21408. Twilio blocks this "
                "destination outright, so no geo permission can be switched on "
                "for it and the answer is to stop sending."
                % (blocked, total, EMBARGOED[code]))

    if accepted:
        return ("partly-blocked",
                "%d of %d to +%s rejected with 21408 while %d got through, so "
                "the country is enabled. These are To values resolving somewhere "
                "else: +1 alone spans the US, Canada and twenty Caribbean "
                "countries, each permissioned separately."
                % (blocked, total, code, accepted))

    return ("disabled",
            "%d of %d to +%s rejected with 21408 and nothing accepted. On this "
            "evidence the country was never enabled: nobody sent there until the "
            "day it mattered." % (blocked, total, code))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. This resource has no Status or ErrorCode filter, so
    the window and the page cap are the only ways to bound the read."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def alert_count(session, since):
    """Count 21408 in the Alerts log.

    A request-time rejection does not always leave a message row, so a count
    here with nothing in the list means the sends never became messages.
    """
    page = get(session, "%s/Alerts" % MONITOR, LogLevel="error",
               StartDate=since, PageSize=1000)
    return sum(1 for a in page.get("alerts", [])
               if str(a.get("error_code") or "") == str(GEO_BLOCKED))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the message list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--check-alerts", action="store_true",
                    help="one extra GET against the Alerts log to catch sends "
                         "rejected before a message row existed")
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
        log.info("this check reads traffic because geo permissions have no read "
                 "API. With no traffic there is nothing to infer from.")
        return 0

    countries = tally(messages)
    bad = 0
    for code, stats in sorted(countries.items(), key=lambda kv: str(kv[0])):
        state, detail = verdict(stats)
        label = "+%s" % code if code else "unparseable"
        line = "%-14s %-12s %s" % (state, label, detail)
        if state == "permitted":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if stats["examples"]:
            log.warning("  example To values: %s", ", ".join(stats["examples"]))
        if stats["sids"]:
            log.warning("  message sids: %s", ", ".join(str(s) for s in stats["sids"]))
        if state == "disabled":
            log.warning("  repair: Console -> Messaging -> Settings -> Geo "
                        "Permissions -> enable %s. There is no REST path for "
                        "this, so nothing can be printed for you to run and "
                        "nothing can confirm it afterwards except a message "
                        "that goes through.", DIAL_CODES.get(code, "+" + code))
        elif state == "embargoed":
            log.warning("  repair: none available. Remove this destination from "
                        "the sending list.")
        else:
            log.warning("  repair: correct the To values to E.164 for the country "
                        "you mean. The permission is not what is wrong here.")

    if args.check_alerts:
        n = alert_count(session, since)
        log.info("%d alert(s) with error_code 21408 since %s", n, since)
        if n and not bad:
            log.warning("alerts show 21408 but no message row carries it: those "
                        "sends were rejected before a message existed")

    log.info("%d destination(s) over %d day(s), %d blocked by geo permissions",
             len(countries), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-geo-permission-audit.mjs",
"js": '''/**
 * Report destination countries blocked by SMS Geo Permissions (error 21408).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed, and here it could not be anything else: SMS Geo Permissions has no
 * REST resource in either direction.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const GEO_BLOCKED = 21408;

/** Blocked outright, whatever the geo permission says. */
const EMBARGOED = { 98: 'Iran', 963: 'Syria', 53: 'Cuba' };

/**
 * Enough calling codes to group real destinations. An unrecognised prefix is
 * itself a finding: a malformed To produces the same 21408 as a disabled
 * country.
 */
const DIAL_CODES = {
  1: 'the NANP (US, Canada and the Caribbean)', 7: 'Russia or Kazakhstan',
  20: 'Egypt', 27: 'South Africa', 30: 'Greece', 31: 'the Netherlands',
  32: 'Belgium', 33: 'France', 34: 'Spain', 36: 'Hungary', 39: 'Italy',
  40: 'Romania', 43: 'Austria', 44: 'the UK', 45: 'Denmark', 46: 'Sweden',
  47: 'Norway', 48: 'Poland', 49: 'Germany', 51: 'Peru', 52: 'Mexico',
  53: 'Cuba', 54: 'Argentina', 55: 'Brazil', 56: 'Chile', 57: 'Colombia',
  58: 'Venezuela', 60: 'Malaysia', 61: 'Australia', 62: 'Indonesia',
  63: 'the Philippines', 64: 'New Zealand', 65: 'Singapore', 66: 'Thailand',
  81: 'Japan', 82: 'South Korea', 84: 'Vietnam', 86: 'China', 90: 'Turkey',
  91: 'India', 92: 'Pakistan', 94: 'Sri Lanka', 98: 'Iran', 212: 'Morocco',
  213: 'Algeria', 234: 'Nigeria', 254: 'Kenya', 255: 'Tanzania',
  351: 'Portugal', 353: 'Ireland', 358: 'Finland', 380: 'Ukraine',
  420: 'Czechia', 421: 'Slovakia', 852: 'Hong Kong', 880: 'Bangladesh',
  886: 'Taiwan', 963: 'Syria', 966: 'Saudi Arabia', 971: 'the UAE',
  972: 'Israel', 977: 'Nepal', 998: 'Uzbekistan',
};

/** Read error_code as a number, or null. */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Longest matching country calling code for an E.164 destination, or null.
 * Null is a finding of its own: a mangled prefix is rejected with the same
 * 21408 as a country nobody enabled.
 */
export function dialCode(to) {
  const raw = String(to ?? '').trim();
  if (!raw.startsWith('+')) return null;
  const digits = raw.slice(1).replace(/\\D/g, '');
  for (const size of [3, 2, 1]) {
    const head = digits.slice(0, size);
    if (Object.prototype.hasOwnProperty.call(DIAL_CODES, head)) return head;
  }
  return null;
}

/**
 * Bucket outbound messages by destination country. Pure, so the grouping rule
 * can be tested without a network.
 */
export function tally(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const code = dialCode(m.to);
    const key = code ?? '';
    if (!out.has(key)) {
      out.set(key, { code, total: 0, blocked: 0, accepted: 0, sids: [], examples: [] });
    }
    const row = out.get(key);
    row.total += 1;
    if (errorCode(m) === GEO_BLOCKED) {
      row.blocked += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
      if (row.examples.length < 2 && m.to) row.examples.push(m.to);
    } else {
      // Not a 21408 means it got past the permission check, even if a carrier
      // rejected it later.
      row.accepted += 1;
    }
  }
  return out;
}

/**
 * Decide what one country's tally says about its geo permission. Pure, and an
 * inference rather than a reading: no endpoint returns the permission.
 * Returns [state, detail].
 */
export function verdict(stats) {
  const code = stats.code ?? null;
  const total = Number(stats.total ?? 0);
  const blocked = Number(stats.blocked ?? 0);
  const accepted = Number(stats.accepted ?? 0);

  if (blocked === 0) return ['permitted', `${total} message(s), none rejected with 21408`];

  if (code === null) {
    return ['unresolved-to',
      `${blocked} of ${total} rejected with 21408, and the To values are not ` +
      'E.164 with a calling code this script can resolve. Permissions are judged ' +
      'on the destination country, so a mangled prefix reads as a disabled ' +
      'country. Fix the numbers before the setting.'];
  }

  if (Object.prototype.hasOwnProperty.call(EMBARGOED, code)) {
    return ['embargoed',
      `${blocked} of ${total} to ${EMBARGOED[code]} rejected with 21408. Twilio ` +
      'blocks this destination outright, so no geo permission can be switched on ' +
      'for it and the answer is to stop sending.'];
  }

  if (accepted) {
    return ['partly-blocked',
      `${blocked} of ${total} to +${code} rejected with 21408 while ${accepted} ` +
      'got through, so the country is enabled. These are To values resolving ' +
      'somewhere else: +1 alone spans the US, Canada and twenty Caribbean ' +
      'countries, each permissioned separately.'];
  }

  return ['disabled',
    `${blocked} of ${total} to +${code} rejected with 21408 and nothing ` +
    'accepted. On this evidence the country was never enabled: nobody sent ' +
    'there until the day it mattered.'];
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
  const days = Number(process.argv[process.argv.indexOf('--days') + 1]) || 7;
  const checkAlerts = process.argv.includes('--check-alerts');

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const messages = await listMessages(auth, account, since);
  if (messages.length === 0) {
    console.log(`no messages sent since ${since}`);
    console.log('this check reads traffic because geo permissions have no read ' +
                'API. With no traffic there is nothing to infer from.');
    return;
  }

  const countries = tally(messages);
  let bad = 0;
  for (const [key, stats] of [...countries.entries()].sort()) {
    const [state, detail] = verdict(stats);
    const label = stats.code ? `+${stats.code}` : 'unparseable';
    const line = `${state.padEnd(14)} ${label.padEnd(12)} ${detail}`;
    if (state === 'permitted') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (stats.examples.length) console.warn(`  example To values: ${stats.examples.join(', ')}`);
    if (stats.sids.length) console.warn(`  message sids: ${stats.sids.join(', ')}`);
    if (state === 'disabled') {
      console.warn('  repair: Console -> Messaging -> Settings -> Geo Permissions ' +
                   `-> enable ${DIAL_CODES[key] ?? label}. There is no REST path ` +
                   'for this, so nothing can be printed for you to run and nothing ' +
                   'can confirm it afterwards except a message that goes through.');
    } else if (state === 'embargoed') {
      console.warn('  repair: none available. Remove this destination from the ' +
                   'sending list.');
    } else {
      console.warn('  repair: correct the To values to E.164 for the country you ' +
                   'mean. The permission is not what is wrong here.');
    }
  }

  if (checkAlerts) {
    const page = await get(auth, `${MONITOR}/Alerts`,
                           { LogLevel: 'error', StartDate: since, PageSize: 1000 });
    const n = (page.alerts ?? []).filter(
      (a) => String(a.error_code ?? '') === String(GEO_BLOCKED)).length;
    console.log(`${n} alert(s) with error_code 21408 since ${since}`);
    if (n && !bad) {
      console.warn('alerts show 21408 but no message row carries it: those sends ' +
                   'were rejected before a message existed');
    }
  }

  console.log(`${countries.size} destination(s) over ${days} day(s), ${bad} ` +
              'blocked by geo permissions');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not start an audit and fail on the missing credentials.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases that matter are the ones where the same error code means different things. A country with nothing but <code>21408</code> is a disabled permission; the same code alongside accepted traffic is a bad <code>To</code> value; a destination that is not E.164 at all is a third thing again; and an embargoed country is a finding with no repair. Each of those is a different sentence in the report, so each gets a test.",
"test_py_file": "test_twilio_geo_permission_audit.py",
"test_py": '''from twilio_geo_permission_audit import dial_code, error_code, tally, verdict


def make(to, code=None, direction="outbound-api", sid="SM1", status="sent"):
    return {"to": to, "error_code": code, "direction": direction, "sid": sid,
            "status": status}


def test_country_with_only_21408_reads_as_disabled():
    stats = tally([make("+4915112345678", 21408), make("+4915112345679", 21408)])["49"]
    state, detail = verdict(stats)
    assert state == "disabled"
    assert "never enabled" in detail


def test_21408_alongside_accepted_traffic_is_a_bad_to_value():
    # The permission is on, so these failures are destinations resolving
    # somewhere other than where the code assumed.
    stats = tally([make("+12025550123"), make("+18765550123", 21408)])["1"]
    state, detail = verdict(stats)
    assert state == "partly-blocked"
    assert "enabled" in detail


def test_destination_that_is_not_e164_gets_its_own_bucket():
    stats = tally([make("07700900123", 21408)])[None]
    state, detail = verdict(stats)
    assert state == "unresolved-to"
    assert "before the setting" in detail


def test_embargoed_country_has_no_repair():
    stats = tally([make("+989121234567", 21408)])["98"]
    state, detail = verdict(stats)
    assert state == "embargoed"
    assert "stop sending" in detail


def test_country_with_no_21408_is_permitted():
    state, _ = verdict(tally([make("+33612345678"), make("+33612345679")])["33"])
    assert state == "permitted"


def test_dial_code_prefers_the_longest_match():
    assert dial_code("+998901234567") == "998"
    assert dial_code("+441632960000") == "44"
    assert dial_code("+12025550123") == "1"
    assert dial_code("447700900123") is None


def test_error_code_handles_a_string_from_an_export():
    assert error_code({"error_code": "21408"}) == 21408
    assert error_code({"error_code": None}) is None


def test_inbound_messages_are_not_counted():
    assert tally([make("+4915112345678", direction="inbound")]) == {}
''',
"test_js_file": "twilio-geo-permission-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dialCode, errorCode, tally, verdict } from './twilio-geo-permission-audit.mjs';

const make = (to, code = null, direction = 'outbound-api') => ({
  to, error_code: code, direction, sid: 'SM1', status: 'sent',
});

test('country with only 21408 reads as disabled', () => {
  const stats = tally([make('+4915112345678', 21408), make('+4915112345679', 21408)]).get('49');
  const [state, detail] = verdict(stats);
  assert.equal(state, 'disabled');
  assert.match(detail, /never enabled/);
});

test('21408 alongside accepted traffic is a bad To value', () => {
  const stats = tally([make('+12025550123'), make('+18765550123', 21408)]).get('1');
  const [state, detail] = verdict(stats);
  assert.equal(state, 'partly-blocked');
  assert.match(detail, /enabled/);
});

test('destination that is not E.164 gets its own bucket', () => {
  const stats = tally([make('07700900123', 21408)]).get('');
  const [state, detail] = verdict(stats);
  assert.equal(state, 'unresolved-to');
  assert.match(detail, /before the setting/);
});

test('embargoed country has no repair', () => {
  const [state, detail] = verdict(tally([make('+989121234567', 21408)]).get('98'));
  assert.equal(state, 'embargoed');
  assert.match(detail, /stop sending/);
});

test('country with no 21408 is permitted', () => {
  const [state] = verdict(tally([make('+33612345678'), make('+33612345679')]).get('33'));
  assert.equal(state, 'permitted');
});

test('dialCode prefers the longest match', () => {
  assert.equal(dialCode('+998901234567'), '998');
  assert.equal(dialCode('+441632960000'), '44');
  assert.equal(dialCode('+12025550123'), '1');
  assert.equal(dialCode('447700900123'), null);
});

test('errorCode handles a string from an export', () => {
  assert.equal(errorCode({ error_code: '21408' }), 21408);
  assert.equal(errorCode({ error_code: null }), null);
});

test('inbound messages are not counted', () => {
  assert.equal(tally([make('+4915112345678', null, 'inbound')]).size, 0);
});
''',
"faq": [
 ("Why can't the script just read the geo permission setting?",
  "Because no such endpoint exists. SMS Geo Permissions is a console-only setting with no REST resource for reading it and none for changing it, so a configuration audit cannot see it at all. Everything in this note is inferred from what the traffic did: 21408 grouped by destination country. The output says inferred rather than confirmed for that reason."),
 ("Does a clean report mean every country is enabled?",
  "No, and this is the honest limit of the method. A country you have never sent to produces no evidence either way. The report covers the destinations in the window you read, so it tells you which countries are blocked, never which countries are open. Only a message that goes through proves the latter."),
 ("Why does one country show both delivered and blocked messages?",
  "Because the permission is on and something else is wrong with those particular To values. The commonest cause is a calling code that spans several countries: +1 covers the US, Canada and the Caribbean, each permissioned separately, so US traffic can flow while Jamaica is refused. The next commonest is a national number sent without a country code."),
 ("Am I billed for a message rejected with 21408?",
  "No. The rejection happens on Twilio's side before the message reaches a carrier, so there is no carrier charge to pass on. The cost is the one that does not appear on the invoice: the verification code that never arrived, and the customer who could not finish signing up."),
 ("Can the script enable the countries it finds?",
  "It cannot, and neither can any script. There is no write API for geo permissions any more than there is a read one, so the repair printed here is a console path rather than a request. Every other note in this section prints a POST you could run; this is the one where the honest answer is a menu."),
],
"related": [
 ("/twilio/alphanumeric-sender-id-unregistered/", "The sender ID that is unregistered where you send"),
 ("/twilio/carrier-filtered-messages-30007/", "Messages a carrier filters as spam"),
 ("/twilio/landline-destination-30006/", "SMS to a landline that can never receive it"),
],
"citations": [CITE_21408, CITE_MESSAGE, CITE_ALERTS, CITE_KEYS],
},

]
