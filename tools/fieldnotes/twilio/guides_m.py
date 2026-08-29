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

{
"slug": "alphanumeric-sender-id-unregistered",
"title": "An alphanumeric sender ID is unregistered where you send",
"description": "30040 and 30041 arrive only from the destination carrier, so the API returned 201 and the sender looks fine. Find which sender IDs die in which country.",
"h1": "an alphanumeric sender ID is unregistered where you send",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30041", "twilio 30040", "alphanumeric sender id registration",
             "twilio sender id india", "restricted or unregistered sender"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The launch in India went out on the same sender ID that has worked in Europe for two years. Every message came back <code>30041</code>. The create calls all returned <code>201</code>, the sender is configured on the Messaging Service, and the console shows nothing wrong &mdash; because the rejection happened at a carrier in Mumbai, long after Twilio accepted the request.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=…</code>, filter <code>error_code</code> in <code>{30040, 30041, 30018}</code> client-side, and group by the pair that actually matters: the <code>from</code> string and the calling code of <code>to</code>. Registration is granted per sender per country, so one row per sender is the wrong shape for the report.</p>
<p>Then read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/AlphaSenders</code> and compare the <code>alpha_sender</code> values against the <code>from</code> strings byte for byte. Matching is case-sensitive: <code>MyBrand</code> and <code>MYBRAND</code> are two different senders, and only one of them was registered.</p>""",
"problem": """<p>An alphanumeric sender ID is not a resource you own; it is a string you assert. India, Saudi Arabia, the UAE, Vietnam and a growing list of others require that string to be pre-registered with the local regulator or carrier before anything sent from it is delivered. Twilio has no way to check that at request time, so the API accepts the message, creates a row, and returns <code>201</code> like any other send.</p>
<p>What comes back later is <code>30040</code> or <code>30041</code>, in a status callback, or in a message row nobody is reading. If your status callback endpoint is missing or your dashboards count HTTP responses rather than delivery states, the failure is invisible from the application side entirely. The traffic is billed, the OTPs are not delivered, and support tickets arrive as "the code never came" from one country while everything else looks healthy.</p>""",
"why": """<p><strong>The API cannot reject what the carrier will.</strong> Sender ID rules live at the destination network. Twilio validates the shape of the string, not its registration status in the country the message is going to, so the create call succeeds everywhere and the outcome differs by destination.</p>
<p><strong>Registration is per country, so success elsewhere proves nothing.</strong> The same sender ID delivering happily across most of Europe carries no weight in India. A report grouped by sender alone shows a mostly healthy sender with a few failures; grouped by sender and country it shows one country where nothing has ever been delivered.</p>
<p><strong>The string comparison is case-sensitive and nobody expects that.</strong> A registration for <code>MyBrand</code> does not cover <code>MYBRAND</code> or <code>Mybrand</code>. One service sending in title case and one legacy job shouting the same word will register as two senders, one of them unregistered, and the difference is invisible in any dashboard that upper-cases labels for display.</p>
<p><strong>No API lists what is registered.</strong> <code>AlphaSenders</code> tells you which strings are attached to a Messaging Service, not which strings a regulator has approved for a country. So this check, like geo permissions, has to reason from the error codes; the service listing only adds the case comparison and tells you whether the sender is managed at all.</p>
<p><strong>30018 is the same problem before it becomes fatal.</strong> It is logged at warning level rather than error, which means an alert sweep filtered to <code>LogLevel=error</code> will not show it, and the sweep that would have given you a week's notice returns clean.</p>""",
"steps": [
 {"h": "Page the message list and keep the alphanumeric senders",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. A <code>from</code> that does not start with <code>+</code> and is not a short code is an alphanumeric sender ID; those are the only rows this audit is about.</p>"""},
 {"h": "Group by sender and destination country together",
  "body": """<p>Resolve the calling code of <code>to</code> and key the tally on the pair. Registration is granted for one sender in one country, so that pair is the unit of the finding. Counting per sender averages a dead country into a healthy total and hides it.</p>"""},
 {"h": "Read the AlphaSenders on every Messaging Service",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code>, then <code>GET /v1/Services/{ServiceSid}/AlphaSenders</code> for each. Collect every <code>alpha_sender</code> exactly as returned. This does not tell you what is registered with a regulator &mdash; no API does &mdash; but it tells you which strings are configured and lets you catch the case mismatch.</p>"""},
 {"h": "Compare the strings byte for byte before blaming registration",
  "body": """<p>If a failing <code>from</code> matches a configured sender only when case is ignored, the registration is probably fine and the sending code is wrong. That is a one-line fix in your application, not a form and a two-week wait, so it is worth separating in the output.</p>"""},
 {"h": "Register per country, then send from the exact string",
  "body": """<p>Console &rarr; Messaging &rarr; Senders &rarr; Alphanumeric Sender IDs, submit the registration for each destination country, then attach it with <code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}/AlphaSenders</code> and <code>AlphaSender=</code> the exact string. Where registration is not possible, route that country through a long code instead and re-run this audit over the following week.</p>"""},
],
"verify": """<p>Re-run over a window containing traffic to the country you registered. The sender should report <code>delivering</code> for that destination.</p>
<pre><code class="language-bash">python3 twilio_alpha_sender_audit.py --days 7
# 4 sender/destination pair(s), 0 rejected by the destination carrier</code></pre>""",
"code_intro": "One paginated GET over the message list, then one GET for the Messaging Services and one per service for its alphanumeric senders. The classifier takes a sender-and-country tally plus the set of configured sender strings and decides between an unregistered sender, a case mismatch, an early warning and a sender that is simply working. It is pure, because the case comparison is the part everyone gets wrong and it should be readable on its own.",
"py_file": "twilio_alpha_sender_audit.py",
"py": '''"""Report alphanumeric sender IDs rejected by the destination carrier.

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
log = logging.getLogger("twilio_alpha_sender_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

# Rejected outright by the destination carrier for a sender it does not know.
BLOCKING = (30040, 30041)
# The warning-level sibling. Logged below error level, so an alert sweep
# filtered to LogLevel=error never shows it.
WARNING = 30018

# Countries that mandate pre-registration of alphanumeric sender IDs. The list
# grows; it is used to explain a finding, never to decide one, because the
# decision is made by what the traffic did.
REGISTRATION_REQUIRED = {"91": "India", "966": "Saudi Arabia", "971": "the UAE",
                         "84": "Vietnam", "880": "Bangladesh", "94": "Sri Lanka",
                         "977": "Nepal", "998": "Uzbekistan"}

DIAL_CODES = {
    "1", "7", "20", "27", "30", "31", "32", "33", "34", "36", "39", "40", "43",
    "44", "45", "46", "47", "48", "49", "51", "52", "54", "55", "56", "57",
    "58", "60", "61", "62", "63", "64", "65", "66", "81", "82", "84", "86",
    "90", "91", "92", "94", "212", "213", "234", "254", "351", "353", "358",
    "380", "420", "421", "852", "880", "886", "966", "971", "972", "977", "998",
}


def error_code(message):
    """Read error_code as an integer, or None. Some exports hand it back as a
    string, and comparing the raw value finds nothing on a broken account."""
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def sender_kind(value):
    """Classify a From value as e164, short-code or alphanumeric.

    Alphanumeric sender IDs are the only ones this audit is about, and the one
    thing that distinguishes them in a message row is that they are not a
    number. A digit string short enough to be a short code is not one either.
    """
    raw = str(value or "").strip()
    if not raw:
        return "unknown"
    if raw.startswith("+"):
        return "e164"
    if raw.isdigit():
        return "short-code" if len(raw) <= 8 else "e164"
    return "alphanumeric"


def dial_code(to):
    """Longest matching country calling code for an E.164 destination, or None.

    Registration is granted per country, so the destination country is half of
    the key this audit groups on.
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
    """Bucket outbound alphanumeric-sender messages by sender and destination.

    Pure, so the grouping rule can be tested without a network. The key is the
    pair, not the sender: a sender ID registered in one country and not in the
    next is the normal case, and a per-sender total hides it.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        sender = str(m.get("from") or "").strip()
        if sender_kind(sender) != "alphanumeric":
            continue
        code = dial_code(m.get("to"))
        row = out.setdefault((sender, code),
                             {"sender": sender, "code": code, "total": 0,
                              "blocked": 0, "warned": 0, "accepted": 0, "sids": []})
        row["total"] += 1
        err = error_code(m)
        if err in BLOCKING:
            row["blocked"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
        elif err == WARNING:
            row["warned"] += 1
        else:
            row["accepted"] += 1
    return out


def verdict(row, configured=None):
    """Classify one sender-and-country pair.

    `configured` is the set of alpha_sender strings attached to the account's
    Messaging Services, or None when those were not read. It is not a list of
    what a regulator has approved, because no API returns that; it is only good
    enough to catch the case mismatch, which is the cheap fix worth separating
    from the slow one.

    Pure. Returns (state, detail).
    """
    sender = str(row.get("sender") or "")
    code = row.get("code")
    where = "+%s" % code if code else "an unresolved destination"
    if code in REGISTRATION_REQUIRED:
        where = REGISTRATION_REQUIRED[code]
    total = int(row.get("total") or 0)
    blocked = int(row.get("blocked") or 0)
    warned = int(row.get("warned") or 0)

    known = set(configured or ())
    exact = sender in known
    folded = {s.casefold() for s in known}
    near = (not exact) and sender.casefold() in folded

    if blocked:
        if near:
            return ("case-mismatch",
                    "%d of %d to %s rejected with 30040/30041, and '%s' differs "
                    "from a configured sender only in case. Sender IDs are "
                    "matched byte for byte, so this is a change in your sending "
                    "code, not a registration." % (blocked, total, where, sender))
        return ("unregistered",
                "%d of %d to %s rejected with 30040/30041. The destination "
                "carrier requires this sender to be pre-registered there; the "
                "API accepted every one of these because it cannot know that."
                % (blocked, total, where))

    if warned:
        return ("warned",
                "%d of %d to %s carry 30018. That is the warning-level sibling "
                "of 30041 and it is below the error threshold most alert sweeps "
                "use, so this is the notice you would otherwise miss."
                % (warned, total, where))

    if configured is not None and not exact:
        return ("not-in-pool",
                "%d message(s) to %s delivering from '%s', which is not attached "
                "to any Messaging Service. It works today, but nothing on the "
                "account records that this string is a sender of yours."
                % (total, where, sender))

    return ("delivering", "%d message(s) to %s, none rejected" % (total, where))


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
    resource, so the window and the page cap are the only bounds."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def configured_senders(session):
    """Every alpha_sender attached to every Messaging Service, exactly as
    returned. Not a registration list: no API returns one."""
    out = {}
    services = get(session, "%s/Services" % MESSAGING, PageSize=100).get("services", [])
    for svc in services:
        sid = svc.get("sid")
        page = get(session, "%s/Services/%s/AlphaSenders" % (MESSAGING, sid),
                   PageSize=100)
        for alpha in page.get("alpha_senders", []):
            out[str(alpha.get("alpha_sender") or "")] = sid
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the message list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--skip-services", action="store_true",
                    help="do not read the Messaging Services, which disables the "
                         "case-mismatch comparison")
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
    pairs = tally(messages)
    if not pairs:
        log.info("no messages from an alphanumeric sender since %s", since)
        return 0

    owners = {} if args.skip_services else configured_senders(session)
    configured = None if args.skip_services else set(owners)

    bad = 0
    for _, row in sorted(pairs.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        state, detail = verdict(row, configured)
        line = "%-14s %-12s %s" % (state, row["sender"][:12], detail)
        if state == "delivering":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if row["sids"]:
            log.warning("  message sids: %s", ", ".join(str(s) for s in row["sids"]))
        if state == "case-mismatch":
            match = [s for s in owners if s.casefold() == row["sender"].casefold()]
            log.warning("  repair: send From='%s', the string already configured "
                        "on service %s. No registration is needed for that.",
                        match[0], owners.get(match[0], "?"))
        elif state == "unregistered":
            log.warning("  repair: register '%s' for this country at Console -> "
                        "Messaging -> Senders -> Alphanumeric Sender IDs, then "
                        "attach it with a create call on %s/Services/{ServiceSid}"
                        "/AlphaSenders. Until it is approved, route this country "
                        "through a long code.", row["sender"], MESSAGING)
        else:
            log.warning("  repair: attach '%s' to the Messaging Service that "
                        "should own it, so the account records it as a sender.",
                        row["sender"])

    log.info("%d sender/destination pair(s), %d rejected by the destination "
             "carrier", len(pairs), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-alpha-sender-audit.mjs",
"js": '''/**
 * Report alphanumeric sender IDs rejected by the destination carrier.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

/** Rejected outright by the destination carrier for a sender it does not know. */
const BLOCKING = [30040, 30041];
/** The warning-level sibling, below the threshold most alert sweeps use. */
const WARNING = 30018;

/** Countries that mandate pre-registration. Used to explain, never to decide. */
const REGISTRATION_REQUIRED = {
  91: 'India', 966: 'Saudi Arabia', 971: 'the UAE', 84: 'Vietnam',
  880: 'Bangladesh', 94: 'Sri Lanka', 977: 'Nepal', 998: 'Uzbekistan',
};

const DIAL_CODES = new Set([
  '1', '7', '20', '27', '30', '31', '32', '33', '34', '36', '39', '40', '43',
  '44', '45', '46', '47', '48', '49', '51', '52', '54', '55', '56', '57', '58',
  '60', '61', '62', '63', '64', '65', '66', '81', '82', '84', '86', '90', '91',
  '92', '94', '212', '213', '234', '254', '351', '353', '358', '380', '420',
  '421', '852', '880', '886', '966', '971', '972', '977', '998',
]);

/** Read error_code as a number, or null. */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Classify a From value as e164, short-code or alphanumeric. Alphanumeric
 * senders are the only rows this audit is about.
 */
export function senderKind(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return 'unknown';
  if (raw.startsWith('+')) return 'e164';
  if (/^\\d+$/.test(raw)) return raw.length <= 8 ? 'short-code' : 'e164';
  return 'alphanumeric';
}

/** Longest matching country calling code for an E.164 destination, or null. */
export function dialCode(to) {
  const raw = String(to ?? '').trim();
  if (!raw.startsWith('+')) return null;
  const digits = raw.slice(1).replace(/\\D/g, '');
  for (const size of [3, 2, 1]) {
    const head = digits.slice(0, size);
    if (DIAL_CODES.has(head)) return head;
  }
  return null;
}

/**
 * Bucket outbound alphanumeric-sender messages by sender and destination. Pure,
 * so the grouping rule can be tested without a network. The key is the pair:
 * registration is granted for one sender in one country.
 */
export function tally(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const sender = String(m.from ?? '').trim();
    if (senderKind(sender) !== 'alphanumeric') continue;
    const code = dialCode(m.to);
    const key = `${sender}\\u0000${code ?? ''}`;
    if (!out.has(key)) {
      out.set(key, { sender, code, total: 0, blocked: 0, warned: 0, accepted: 0, sids: [] });
    }
    const row = out.get(key);
    row.total += 1;
    const err = errorCode(m);
    if (BLOCKING.includes(err)) {
      row.blocked += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
    } else if (err === WARNING) {
      row.warned += 1;
    } else {
      row.accepted += 1;
    }
  }
  return out;
}

/**
 * Classify one sender-and-country pair. `configured` is the set of alpha_sender
 * strings attached to the account's Messaging Services, or null when they were
 * not read; it is not a registration list, because no API returns one.
 * Pure. Returns [state, detail].
 */
export function verdict(row, configured = null) {
  const sender = String(row.sender ?? '');
  const code = row.code ?? null;
  let where = code ? `+${code}` : 'an unresolved destination';
  if (code && Object.prototype.hasOwnProperty.call(REGISTRATION_REQUIRED, code)) {
    where = REGISTRATION_REQUIRED[code];
  }
  const total = Number(row.total ?? 0);
  const blocked = Number(row.blocked ?? 0);
  const warned = Number(row.warned ?? 0);

  const known = configured ? [...configured] : [];
  const exact = known.includes(sender);
  const near = !exact && known.some((s) => s.toLowerCase() === sender.toLowerCase());

  if (blocked) {
    if (near) {
      return ['case-mismatch',
        `${blocked} of ${total} to ${where} rejected with 30040/30041, and ` +
        `'${sender}' differs from a configured sender only in case. Sender IDs ` +
        'are matched byte for byte, so this is a change in your sending code, ' +
        'not a registration.'];
    }
    return ['unregistered',
      `${blocked} of ${total} to ${where} rejected with 30040/30041. The ` +
      'destination carrier requires this sender to be pre-registered there; the ' +
      'API accepted every one of these because it cannot know that.'];
  }

  if (warned) {
    return ['warned',
      `${warned} of ${total} to ${where} carry 30018. That is the ` +
      'warning-level sibling of 30041 and it is below the error threshold most ' +
      'alert sweeps use, so this is the notice you would otherwise miss.'];
  }

  if (configured !== null && !exact) {
    return ['not-in-pool',
      `${total} message(s) to ${where} delivering from '${sender}', which is ` +
      'not attached to any Messaging Service. It works today, but nothing on ' +
      'the account records that this string is a sender of yours.'];
  }

  return ['delivering', `${total} message(s) to ${where}, none rejected`];
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

async function configuredSenders(auth) {
  const owners = new Map();
  const services = (await get(auth, `${MESSAGING}/Services`, { PageSize: 100 })).services ?? [];
  for (const svc of services) {
    const page = await get(auth, `${MESSAGING}/Services/${svc.sid}/AlphaSenders`,
                           { PageSize: 100 });
    for (const alpha of page.alpha_senders ?? []) {
      owners.set(String(alpha.alpha_sender ?? ''), svc.sid);
    }
  }
  return owners;
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
  const skipServices = process.argv.includes('--skip-services');

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const pairs = tally(await listMessages(auth, account, since));
  if (pairs.size === 0) {
    console.log(`no messages from an alphanumeric sender since ${since}`);
    return;
  }

  const owners = skipServices ? new Map() : await configuredSenders(auth);
  const configured = skipServices ? null : new Set(owners.keys());

  let bad = 0;
  for (const key2 of [...pairs.keys()].sort()) {
    const row = pairs.get(key2);
    const [state, detail] = verdict(row, configured);
    const line = `${state.padEnd(14)} ${row.sender.slice(0, 12).padEnd(12)} ${detail}`;
    if (state === 'delivering') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (row.sids.length) console.warn(`  message sids: ${row.sids.join(', ')}`);
    if (state === 'case-mismatch') {
      const match = [...owners.keys()].find(
        (s) => s.toLowerCase() === row.sender.toLowerCase());
      console.warn(`  repair: send From='${match}', the string already ` +
                   `configured on service ${owners.get(match)}. No registration ` +
                   'is needed for that.');
    } else if (state === 'unregistered') {
      console.warn(`  repair: register '${row.sender}' for this country at ` +
                   'Console -> Messaging -> Senders -> Alphanumeric Sender IDs, ' +
                   `then attach it with a create call on ${MESSAGING}/Services/` +
                   '{ServiceSid}/AlphaSenders. Until it is approved, route this ' +
                   'country through a long code.');
    } else {
      console.warn(`  repair: attach '${row.sender}' to the Messaging Service ` +
                   'that should own it, so the account records it as a sender.');
    }
  }

  console.log(`${pairs.size} sender/destination pair(s), ${bad} rejected by the ` +
              'destination carrier');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not start an audit and fail on the missing credentials.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three of these cases produce the same error code and need different answers: a sender that was never registered in the country, a sender whose string differs from the configured one only in case, and a sender working perfectly in a country next door. The fourth is the one that gives you warning &mdash; <code>30018</code>, which sits below the level most alert sweeps read.",
"test_py_file": "test_twilio_alpha_sender_audit.py",
"test_py": '''from twilio_alpha_sender_audit import dial_code, sender_kind, tally, verdict


def make(sender, to, code=None, direction="outbound-api", sid="SM1"):
    return {"from": sender, "to": to, "error_code": code, "direction": direction,
            "sid": sid}


def test_sender_blocked_in_one_country_is_unregistered_there():
    rows = tally([make("MyBrand", "+919812345678", 30041),
                  make("MyBrand", "+919812345679", 30040)])
    state, detail = verdict(rows[("MyBrand", "91")], {"MyBrand"})
    assert state == "unregistered"
    assert "India" in detail


def test_the_same_sender_is_healthy_in_the_next_country():
    # Grouping by sender alone would average this into the Indian failures and
    # report one mostly working sender.
    rows = tally([make("MyBrand", "+919812345678", 30041),
                  make("MyBrand", "+33612345678")])
    assert verdict(rows[("MyBrand", "33")], {"MyBrand"})[0] == "delivering"


def test_case_difference_is_reported_as_a_code_change_not_a_registration():
    rows = tally([make("MYBRAND", "+919812345678", 30041)])
    state, detail = verdict(rows[("MYBRAND", "91")], {"MyBrand"})
    assert state == "case-mismatch"
    assert "byte for byte" in detail


def test_30018_is_reported_before_anything_is_blocked():
    rows = tally([make("MyBrand", "+9715012345678", 30018)])
    state, detail = verdict(rows[("MyBrand", "971")], {"MyBrand"})
    assert state == "warned"
    assert "30018" in detail


def test_working_sender_missing_from_every_service_is_its_own_state():
    rows = tally([make("Ghost", "+33612345678")])
    assert verdict(rows[("Ghost", "33")], {"MyBrand"})[0] == "not-in-pool"
    # With the services unread there is nothing to compare against, so no claim.
    assert verdict(rows[("Ghost", "33")], None)[0] == "delivering"


def test_only_alphanumeric_senders_are_counted():
    assert tally([make("+15005550006", "+33612345678"),
                  make("12345", "+33612345678")]) == {}
    assert sender_kind("MyBrand") == "alphanumeric"
    assert sender_kind("12345") == "short-code"


def test_dial_code_prefers_the_longest_match():
    assert dial_code("+971501234567") == "971"
    assert dial_code("+919812345678") == "91"
    assert dial_code("07700900123") is None
''',
"test_js_file": "twilio-alpha-sender-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dialCode, senderKind, tally, verdict } from './twilio-alpha-sender-audit.mjs';

const make = (sender, to, code = null, direction = 'outbound-api') => ({
  from: sender, to, error_code: code, direction, sid: 'SM1',
});
const row = (rows, sender, code) => rows.get(`${sender}\\u0000${code}`);

test('sender blocked in one country is unregistered there', () => {
  const rows = tally([make('MyBrand', '+919812345678', 30041),
                      make('MyBrand', '+919812345679', 30040)]);
  const [state, detail] = verdict(row(rows, 'MyBrand', '91'), new Set(['MyBrand']));
  assert.equal(state, 'unregistered');
  assert.match(detail, /India/);
});

test('the same sender is healthy in the next country', () => {
  const rows = tally([make('MyBrand', '+919812345678', 30041),
                      make('MyBrand', '+33612345678')]);
  assert.equal(verdict(row(rows, 'MyBrand', '33'), new Set(['MyBrand']))[0], 'delivering');
});

test('case difference is a code change, not a registration', () => {
  const rows = tally([make('MYBRAND', '+919812345678', 30041)]);
  const [state, detail] = verdict(row(rows, 'MYBRAND', '91'), new Set(['MyBrand']));
  assert.equal(state, 'case-mismatch');
  assert.match(detail, /byte for byte/);
});

test('30018 is reported before anything is blocked', () => {
  const rows = tally([make('MyBrand', '+9715012345678', 30018)]);
  const [state, detail] = verdict(row(rows, 'MyBrand', '971'), new Set(['MyBrand']));
  assert.equal(state, 'warned');
  assert.match(detail, /30018/);
});

test('working sender missing from every service is its own state', () => {
  const rows = tally([make('Ghost', '+33612345678')]);
  assert.equal(verdict(row(rows, 'Ghost', '33'), new Set(['MyBrand']))[0], 'not-in-pool');
  assert.equal(verdict(row(rows, 'Ghost', '33'), null)[0], 'delivering');
});

test('only alphanumeric senders are counted', () => {
  assert.equal(tally([make('+15005550006', '+33612345678'),
                      make('12345', '+33612345678')]).size, 0);
  assert.equal(senderKind('MyBrand'), 'alphanumeric');
  assert.equal(senderKind('12345'), 'short-code');
});

test('dialCode prefers the longest match', () => {
  assert.equal(dialCode('+971501234567'), '971');
  assert.equal(dialCode('+919812345678'), '91');
  assert.equal(dialCode('07700900123'), null);
});
''',
"faq": [
 ("Why did the API accept a message it could not deliver?",
  "Because the rule being broken belongs to a carrier in another country. Twilio validates that the sender string is a legal alphanumeric sender ID, not that a regulator in the destination country has approved it, so the create call returns 201 and the failure arrives later as 30040 or 30041 on the message record."),
 ("Which countries require registration?",
  "The list grows, and it is set by regulators rather than by Twilio. India, Saudi Arabia, the UAE and Vietnam are the ones teams hit first. The script names them where it can, but it never decides a finding from that list: the decision comes from what the traffic did, so a country that starts requiring registration next month is still caught."),
 ("Is there an API that tells me which sender IDs are registered?",
  "No. AlphaSenders lists the strings attached to a Messaging Service, which is a different question; a string can be attached and unregistered, or registered in one country and useless in the next. That is why this note reasons from error codes and uses the service listing only for the case comparison."),
 ("Does upper-casing the sender ID really break it?",
  "Yes. Registration is for an exact string, and matching is case-sensitive, so MyBrand and MYBRAND are two senders of which one is registered. It is worth separating in the report because the fix is a one-line change in your sending code rather than a form and a wait of days or weeks."),
 ("What should the country do in the meantime?",
  "Route it through a long code or a registered short code for that market. Sends will keep failing for as long as registration is pending, and re-sending from the same unregistered string only adds cost. Neither of those is something this script will do for you: it reads, and prints what to change."),
],
"related": [
 ("/twilio/sms-geo-permissions-disabled/", "The country that was never enabled for SMS"),
 ("/twilio/shortcode-cross-border-sender-mismatch/", "A short code selected outside its country"),
 ("/twilio/messaging-service-empty-sender-pool/", "A Messaging Service with no sender at all"),
],
"citations": [CITE_30041, CITE_30040, CITE_ALPHA, CITE_MESSAGE],
},

{
"slug": "emergency-address-unregistered",
"title": "US and Canadian numbers with no registered E911 address",
"description": "There is no error until somebody dials 911. Then the call reaches a national centre that has to ask where you are, and the per-call fee arrives later.",
"h1": "US and Canadian numbers with no registered E911 address",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio e911", "emergency_address_sid", "twilio emergency address",
             "emergency_address_status registration-failure", "twilio 911 calling"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing about this number looks wrong. It answers, it dials out, the webhooks are healthy, and it has been in production for a year. Then somebody on the sales floor dials 911 from a softphone. The call connects to a national emergency call centre with no idea where the caller is, an operator asks for an address the caller may not be able to give, and a $75 pass-through charge turns up on a later invoice.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> and, for every <code>+1</code> number whose <code>capabilities.voice</code> is true, read both <code>emergency_address_sid</code> and <code>emergency_address_status</code>. A null SID is unregistered. A status of <code>registration-failure</code> or <code>pending-registration</code> is also unregistered, in the ways that matter on the day.</p>
<p>Read both fields, not one. A number can carry an <code>emergency_address_sid</code> whose registration was rejected by the address validation that happens afterwards, and it will look configured in the console for as long as nobody opens it.</p>""",
"problem": """<p>Every other failure in this section shows up as a status, a code, or a message that did not arrive. This one produces nothing at all until the worst possible moment. <code>emergency_address_sid</code> is optional at purchase, so a number bought through the API arrives without one, works perfectly for voice, and stays that way. There is no alert, no degraded metric, no failed request. The number is fine in every sense except the one that matters once a year.</p>
<p>When the call does happen, the outcome is not a busy tone; it is worse. The call is routed to a national emergency call centre rather than the local PSAP, staffed by people who cannot see a location and have to ask for one. That is the cost. The pass-through fee on the invoice is the part that gets noticed afterwards, and it is the smaller half.</p>""",
"why": """<p><strong>It is optional at purchase and nothing prompts you.</strong> Buying a number through the API takes an area code and a friendly name. The emergency address is a separate call against a separate resource, made afterwards, and nothing in the purchase flow fails without it.</p>
<p><strong>Registration is asynchronous, so submitting is not finishing.</strong> The address is validated against the MSAG after you attach it. It can be rejected days later for a suite number, an abbreviation or a rural address the database does not carry, and the number is left carrying an address SID with a <code>registration-failure</code> status. Auditing the SID alone reports that number as protected.</p>
<p><strong>The console shows an address, which is what people check.</strong> Somebody opening the number in the console sees a street address in the emergency address field and moves on. The status is the field that says whether a dispatcher will ever receive it.</p>
<p><strong>Softphones move and the address does not.</strong> The registered address is where the number is registered, not where the person is sitting. A remote team dialling out on a shared caller ID is exactly the case E911 handles badly, and it is worth knowing which numbers are exposed before deciding what to do about it.</p>
<p><strong>The obligation is US and Canadian.</strong> Numbers outside <code>+1</code>, and SMS-only numbers with no voice capability, cannot dial 911 through this path at all. Reporting them alongside the real findings is how a list of forty exposed numbers gets ignored, so they belong in a separate state.</p>""",
"steps": [
 {"h": "List every number with its capabilities",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, following <code>next_page_uri</code>. The response carries <code>phone_number</code>, <code>capabilities</code>, <code>emergency_address_sid</code>, <code>emergency_address_status</code> and <code>emergency_status</code> on every row, so this is one paginated read and no joins.</p>"""},
 {"h": "Narrow to the numbers that can actually dial 911",
  "body": """<p>A <code>+1</code> prefix and <code>capabilities.voice</code> true. Everything else is out of scope rather than compliant, and the difference matters: a report that mixes forty European numbers into the exposed list will not be read twice.</p>"""},
 {"h": "Judge on the status, not on the SID",
  "body": """<p><code>emergency_address_status</code> of <code>registration-failure</code> is the finding that looks configured everywhere else. <code>pending-registration</code> is submitted and not yet usable. Only a registered status with a SID means a dispatcher will receive an address.</p>"""},
 {"h": "Check whether the number is used for outbound calls",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?From={E164}&amp;PageSize=1</code> is one extra GET per finding and it sets the order of the work. A number that is a caller ID for a team of softphones is the one to fix this afternoon; a number nobody has ever dialled out on can wait for the batch.</p>"""},
 {"h": "Register an address, attach it, then read the status again",
  "body": """<p><code>POST /2010-04-01/Accounts/{AccountSid}/Addresses.json</code> with <code>EmergencyEnabled=true</code>, then <code>POST …/IncomingPhoneNumbers/{PNSid}.json</code> with <code>EmergencyAddressSid=AD…</code> and <code>EmergencyStatus=Active</code>. Re-run this script a day later rather than the same minute: validation is asynchronous, and the answer you want is the status after it has run, not the 200 from the update.</p>"""},
],
"verify": """<p>Re-run the script. Every US and Canadian voice number should report <code>registered</code>, and the exposed count should be zero.</p>
<pre><code class="language-bash">python3 twilio_emergency_address_audit.py
# 18 number(s), 12 in scope for E911, 0 without a working registration</code></pre>""",
"code_intro": "One paginated GET over the numbers, and with <code>--check-traffic</code> one extra GET per finding to see whether the number is used as a caller ID. Read access is all it needs. The classifier is a pure function over a single number resource, because the whole substance of this note is the difference between an address SID and a registration that completed, and that difference should be four lines you can read rather than a branch inside a request loop.",
"py_file": "twilio_emergency_address_audit.py",
"py": '''"""Report US and Canadian Twilio numbers with no working E911 registration.

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
log = logging.getLogger("twilio_emergency_address_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"


def in_scope(number):
    """True when this number could carry a 911 call at all.

    E911 registration is a North American obligation and needs a voice
    capability. Everything else is out of scope rather than compliant, and
    mixing the two is how a list of exposed numbers stops being read.
    """
    e164 = str(number.get("phone_number") or "").strip()
    caps = number.get("capabilities") or {}
    return e164.startswith("+1") and bool(caps.get("voice"))


def verdict(number):
    """Classify one IncomingPhoneNumber's emergency registration.

    Pure, so the rule can be tested without a network. The rule that matters:
    an emergency_address_sid is a submission, and emergency_address_status is
    the outcome. Judging on the SID alone reports a rejected address as done.

    Returns (state, detail).
    """
    if not in_scope(number):
        e164 = str(number.get("phone_number") or "").strip()
        if not e164.startswith("+1"):
            return ("out-of-scope",
                    "not a +1 number: E911 address registration is a US and "
                    "Canadian requirement and does not apply here.")
        return ("out-of-scope",
                "no voice capability, so no call can be placed to 911 from it.")

    status = str(number.get("emergency_address_status") or "").strip().lower()
    sid = str(number.get("emergency_address_sid") or "").strip()

    if status == "registration-failure":
        return ("registration-failed",
                "an address was submitted and the validation rejected it. The "
                "console still shows a street address on this number, which is "
                "why it survives every visual check; no dispatcher will get it.")

    if status == "pending-registration":
        return ("pending",
                "submitted and not yet validated against the address database. "
                "Until it passes, a 911 call from here routes exactly as an "
                "unregistered number does.")

    if not sid or status == "unregistered":
        return ("unregistered",
                "no emergency address at all. A 911 call reaches a national "
                "emergency call centre that cannot see a location and has to ask "
                "for one, and the per-call fee is passed through to you.")

    if str(number.get("emergency_status") or "").strip().lower() == "inactive":
        return ("disabled",
                "address %s is registered but emergency calling is switched off "
                "on the number, so the registration buys nothing." % sid)

    return ("registered", "address %s, status %s" % (sid, status or "registered"))


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


def dials_out(session, account, e164):
    """One outbound call is enough to know the number is somebody's caller ID,
    which is what decides whether this is today's job or this month's."""
    page = get(session, "%s/Accounts/%s/Calls.json" % (BASE, account),
               From=e164, PageSize=1)
    return bool(page.get("calls"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000,
                    help="stop after this many numbers")
    ap.add_argument("--check-traffic", action="store_true",
                    help="one extra GET per finding to see if the number is used "
                         "as an outbound caller ID")
    ap.add_argument("--show-out-of-scope", action="store_true",
                    help="also list the numbers E911 does not apply to")
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

    scoped = 0
    bad = 0
    for n in numbers:
        state, detail = verdict(n)
        line = "%-20s %s  %s" % (state, n.get("phone_number", "?"), detail)
        if state == "out-of-scope":
            if args.show_out_of_scope:
                log.info(line)
            continue
        scoped += 1
        if state == "registered":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if args.check_traffic and dials_out(session, account, n.get("phone_number")):
            log.warning("  this number places outbound calls: somebody may dial "
                        "911 from it today")
        log.warning("  repair: create an Address on %s/Accounts/%s/Addresses.json "
                    "with EmergencyEnabled=true, then update "
                    "%s/Accounts/%s/IncomingPhoneNumbers/%s.json with "
                    "EmergencyAddressSid=AD... and EmergencyStatus=Active. "
                    "Read the status again a day later: validation is "
                    "asynchronous and the 200 is not the answer.",
                    BASE, account, BASE, account, n.get("sid"))

    log.info("%d number(s), %d in scope for E911, %d without a working "
             "registration", len(numbers), scoped, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-emergency-address-audit.mjs",
"js": '''/**
 * Report US and Canadian Twilio numbers with no working E911 registration.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

/**
 * True when this number could carry a 911 call at all. E911 registration is a
 * North American obligation and needs a voice capability; everything else is
 * out of scope rather than compliant.
 */
export function inScope(number) {
  const e164 = String(number.phone_number ?? '').trim();
  const caps = number.capabilities ?? {};
  return e164.startsWith('+1') && Boolean(caps.voice);
}

/**
 * Classify one IncomingPhoneNumber's emergency registration. Pure, so the rule
 * can be tested without a network: emergency_address_sid is a submission and
 * emergency_address_status is the outcome, and judging on the SID alone reports
 * a rejected address as done. Returns [state, detail].
 */
export function verdict(number) {
  const e164 = String(number.phone_number ?? '').trim();
  const caps = number.capabilities ?? {};
  if (!e164.startsWith('+1')) {
    return ['out-of-scope',
      'not a +1 number: E911 address registration is a US and Canadian ' +
      'requirement and does not apply here.'];
  }
  if (!caps.voice) {
    return ['out-of-scope',
      'no voice capability, so no call can be placed to 911 from it.'];
  }

  const status = String(number.emergency_address_status ?? '').trim().toLowerCase();
  const sid = String(number.emergency_address_sid ?? '').trim();

  if (status === 'registration-failure') {
    return ['registration-failed',
      'an address was submitted and the validation rejected it. The console ' +
      'still shows a street address on this number, which is why it survives ' +
      'every visual check; no dispatcher will get it.'];
  }

  if (status === 'pending-registration') {
    return ['pending',
      'submitted and not yet validated against the address database. Until it ' +
      'passes, a 911 call from here routes exactly as an unregistered number does.'];
  }

  if (!sid || status === 'unregistered') {
    return ['unregistered',
      'no emergency address at all. A 911 call reaches a national emergency ' +
      'call centre that cannot see a location and has to ask for one, and the ' +
      'per-call fee is passed through to you.'];
  }

  if (String(number.emergency_status ?? '').trim().toLowerCase() === 'inactive') {
    return ['disabled',
      `address ${sid} is registered but emergency calling is switched off on ` +
      'the number, so the registration buys nothing.'];
  }

  return ['registered', `address ${sid}, status ${status || 'registered'}`];
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

export async function listNumbers(auth, account, limit = 1000) {
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
  const checkTraffic = process.argv.includes('--check-traffic');
  const showOutOfScope = process.argv.includes('--show-out-of-scope');

  const numbers = await listNumbers(auth, account);
  if (numbers.length === 0) {
    console.log('no phone numbers on this account');
    return;
  }

  let scoped = 0;
  let bad = 0;
  for (const n of numbers) {
    const [state, detail] = verdict(n);
    const line = `${state.padEnd(20)} ${n.phone_number ?? '?'}  ${detail}`;
    if (state === 'out-of-scope') {
      if (showOutOfScope) console.log(line);
      continue;
    }
    scoped += 1;
    if (state === 'registered') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (checkTraffic) {
      const calls = await get(auth, `${BASE}/Accounts/${account}/Calls.json`,
                              { From: n.phone_number, PageSize: 1 });
      if ((calls.calls ?? []).length) {
        console.warn('  this number places outbound calls: somebody may dial 911 ' +
                     'from it today');
      }
    }
    console.warn(`  repair: create an Address on ${BASE}/Accounts/${account}/` +
                 'Addresses.json with EmergencyEnabled=true, then update ' +
                 `${BASE}/Accounts/${account}/IncomingPhoneNumbers/${n.sid}.json ` +
                 'with EmergencyAddressSid=AD... and EmergencyStatus=Active. Read ' +
                 'the status again a day later: validation is asynchronous and ' +
                 'the 200 is not the answer.');
  }

  console.log(`${numbers.length} number(s), ${scoped} in scope for E911, ${bad} ` +
              'without a working registration');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not start an audit and fail on the missing credentials.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning hardest is the number that carries an <code>emergency_address_sid</code> and a <code>registration-failure</code> status, because every audit that checks the SID alone calls it compliant and every human opening the console sees a street address. The rest of the tests keep the out-of-scope numbers out of the finding list, which is what keeps the finding list short enough to act on.",
"test_py_file": "test_twilio_emergency_address_audit.py",
"test_py": '''from twilio_emergency_address_audit import in_scope, verdict


def us_number(**over):
    n = {"phone_number": "+12025550123", "capabilities": {"voice": True, "sms": True},
         "emergency_address_sid": None, "emergency_address_status": "unregistered",
         "emergency_status": "Active", "sid": "PN1"}
    n.update(over)
    return n


def test_number_with_no_address_is_unregistered():
    state, detail = verdict(us_number())
    assert state == "unregistered"
    assert "national emergency call centre" in detail


def test_rejected_registration_is_not_the_same_as_no_address():
    # The SID is populated, so a check that reads only the SID calls this fixed.
    state, detail = verdict(us_number(emergency_address_sid="AD1",
                                      emergency_address_status="registration-failure"))
    assert state == "registration-failed"
    assert "visual check" in detail


def test_pending_registration_is_still_exposed():
    state, _ = verdict(us_number(emergency_address_sid="AD1",
                                 emergency_address_status="pending-registration"))
    assert state == "pending"


def test_registered_address_with_emergency_calling_switched_off():
    state, detail = verdict(us_number(emergency_address_sid="AD1",
                                      emergency_address_status="registered",
                                      emergency_status="Inactive"))
    assert state == "disabled"
    assert "buys nothing" in detail


def test_registered_number_passes():
    state, _ = verdict(us_number(emergency_address_sid="AD1",
                                 emergency_address_status="registered"))
    assert state == "registered"


def test_non_north_american_number_is_out_of_scope_not_a_finding():
    state, detail = verdict(us_number(phone_number="+441632960000"))
    assert state == "out-of-scope"
    assert "does not apply" in detail


def test_sms_only_number_cannot_dial_911():
    state, _ = verdict(us_number(capabilities={"voice": False, "sms": True}))
    assert state == "out-of-scope"
    assert not in_scope(us_number(capabilities={"sms": True}))
''',
"test_js_file": "twilio-emergency-address-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inScope, verdict } from './twilio-emergency-address-audit.mjs';

const usNumber = (over = {}) => ({
  phone_number: '+12025550123',
  capabilities: { voice: true, sms: true },
  emergency_address_sid: null,
  emergency_address_status: 'unregistered',
  emergency_status: 'Active',
  sid: 'PN1',
  ...over,
});

test('number with no address is unregistered', () => {
  const [state, detail] = verdict(usNumber());
  assert.equal(state, 'unregistered');
  assert.match(detail, /national emergency call centre/);
});

test('rejected registration is not the same as no address', () => {
  const [state, detail] = verdict(usNumber({
    emergency_address_sid: 'AD1', emergency_address_status: 'registration-failure',
  }));
  assert.equal(state, 'registration-failed');
  assert.match(detail, /visual check/);
});

test('pending registration is still exposed', () => {
  const [state] = verdict(usNumber({
    emergency_address_sid: 'AD1', emergency_address_status: 'pending-registration',
  }));
  assert.equal(state, 'pending');
});

test('registered address with emergency calling switched off', () => {
  const [state, detail] = verdict(usNumber({
    emergency_address_sid: 'AD1', emergency_address_status: 'registered',
    emergency_status: 'Inactive',
  }));
  assert.equal(state, 'disabled');
  assert.match(detail, /buys nothing/);
});

test('registered number passes', () => {
  const [state] = verdict(usNumber({
    emergency_address_sid: 'AD1', emergency_address_status: 'registered',
  }));
  assert.equal(state, 'registered');
});

test('non North American number is out of scope, not a finding', () => {
  const [state, detail] = verdict(usNumber({ phone_number: '+441632960000' }));
  assert.equal(state, 'out-of-scope');
  assert.match(detail, /does not apply/);
});

test('sms only number cannot dial 911', () => {
  const [state] = verdict(usNumber({ capabilities: { voice: false, sms: true } }));
  assert.equal(state, 'out-of-scope');
  assert.equal(inScope(usNumber({ capabilities: { sms: true } })), false);
});
''',
"faq": [
 ("Which field actually decides whether this number is registered?",
  "emergency_address_status. The SID records that an address was attached; the status records what the validation made of it. A number with a SID and a registration-failure status is exposed, and it is the one case where the console looks correct, because the console shows the street address you submitted."),
 ("Why is a rejected registration so common?",
  "The address is checked against a dispatch database rather than a postal one. Suite and unit numbers, abbreviations, new-build streets and rural addresses are the usual rejections. None of that is visible when you submit, and the rejection lands days later on a resource nobody is watching."),
 ("Do numbers outside the US and Canada need this?",
  "Not through this mechanism. Emergency calling elsewhere is a different regime with different obligations, so this script puts non-+1 numbers and SMS-only numbers in an out-of-scope state rather than in the findings. A report where thirty of the forty rows do not need action gets read once."),
 ("What does an unregistered 911 call actually do?",
  "It is routed to a national emergency call centre instead of the local dispatch centre. An operator who cannot see a location has to ask for one and then relay it, on a call where the caller may not be able to speak. The per-call charge that Twilio passes through is the part that shows up in writing later."),
 ("Can the script register the address for me?",
  "No. Creating an address and attaching it to a live number are writes, and nothing in this section writes. It prints both calls with the phone number SID already filled in, and it tells you to read the status again the following day, because the 200 from the update is not the outcome."),
],
"related": [
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
 ("/twilio/idle-phone-numbers-billed/", "Numbers billed every month for nothing"),
 ("/twilio/regulatory-bundle-expiring/", "An approved bundle counting down to rejection"),
],
"citations": [CITE_E911, CITE_PN, CITE_ADDRESS, CITE_KEYS],
},

{
"slug": "shortcode-cross-border-sender-mismatch",
"title": "A short code used outside its own country fails 21612",
"description": "Short codes are licensed nationally. A pool that mixes one with long codes will hand it an international message, and that send is rejected 21612 or 21606.",
"h1": "a short code used outside its own country fails 21612",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 21612", "twilio short code international", "short code not supported country",
             "twilio 21606 short code", "messaging service sender selection short code"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The short code has been delivering domestic traffic for two years at a throughput no long code can match. Then a customer in Canada is added to the same campaign and those messages come back <code>21612</code>. Nothing changed about the short code, the Messaging Service or the campaign registration &mdash; the destination changed, and a short code is licensed for exactly one country.",
"short_answer": """<p>Enumerate the account's short codes with <code>GET /2010-04-01/Accounts/{AccountSid}/SMS/ShortCodes.json</code>, then find which Messaging Services can select one with <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/ShortCodes</code>. A service whose pool holds both a short code and long codes will eventually hand an international message to the short code.</p>
<p>Confirm it in the traffic: page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=…</code>, filter <code>error_code</code> in <code>{21612, 21606}</code> client-side, and group by <code>from</code>. Failures whose sender is a short code and whose destination is outside its country are this problem; the same codes from a long code are something else.</p>""",
"problem": """<p>A short code is a national licence, not a phone number that happens to be short. A US short code reaches US handsets and nothing else. That constraint is invisible in the resource: <code>GET /SMS/ShortCodes.json</code> returns the digits, the SID and the webhook URLs, and says nothing about the country the code is licensed in, so no configuration audit can compare a short code against a destination.</p>
<p>What makes it a production incident rather than a known limitation is sender selection. A Messaging Service picks a sender from its pool per message. Put a short code in a pool alongside long codes and the choice is made per send, at send time, by logic your code does not see. Domestic traffic works. The first international recipient gets whichever sender was picked, and if that is the short code the message is rejected outright with <code>21612</code>, or <code>21606</code>, at request time.</p>""",
"why": """<p><strong>Short codes are licensed per country and nothing in the API says which.</strong> The ShortCode resource carries no country field, so the licensing country has to come from you. This script takes it as an argument and treats every other destination as cross-border, which is honest about where the knowledge lives.</p>
<p><strong>Sender selection is per message, so the failure is intermittent by design.</strong> The same service, the same code, the same campaign: two sends to two countries take different paths. That is why this arrives as "some customers never get the code" rather than as an outage, and why it survives a test suite that only sends domestically.</p>
<p><strong>Short codes sit outside A2P 10DLC, which reads as approval.</strong> They need no brand and no campaign, so a team that fought through 10DLC registration and then added a short code to the same service reasonably assumes the hard part is behind them. The geographic constraint is a separate rule that the registration says nothing about.</p>
<p><strong>The error codes are shared with other faults.</strong> <code>21606</code> is also what a voice-only long code returns, and <code>21612</code> covers several unreachable combinations. Grouping by sender rather than by code is what separates this from those: a short code that fails only on foreign destinations is this note, and a long code failing everywhere is a different one.</p>
<p><strong>The rejection is at request time, so it may leave no message row.</strong> Sends refused before a message is created appear in the Alerts log rather than in the message list, which means the count you get from the traffic is a floor rather than a total.</p>""",
"steps": [
 {"h": "List the account's short codes",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/SMS/ShortCodes.json?PageSize=100</code>. Read <code>short_code</code> and <code>sid</code>. This is the set of senders the rest of the audit is about; an account with none of them has nothing to check here.</p>"""},
 {"h": "Find every Messaging Service that can select one",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code>, then <code>GET /v1/Services/{ServiceSid}/ShortCodes</code> and <code>GET /v1/Services/{ServiceSid}/PhoneNumbers</code> for each. A pool holding both kinds is the configuration that makes the failure possible, and it is visible before anyone sends a message.</p>"""},
 {"h": "Read the traffic the service actually carried",
  "body": """<p>Page the message list over a window and group by <code>messaging_service_sid</code>. Count the destinations outside the short code's licensing country, and count the sends already rejected with <code>21612</code> or <code>21606</code> from a short code. The first number says the exposure is real; the second says it has already cost you, and it is the only one that can see the border inside <code>+1</code>, where a US short code and a Canadian handset share a calling code.</p>"""},
 {"h": "Tell the two kinds of 21606 apart",
  "body": """<p>Group by sender before you group by error code. A short code failing only on foreign destinations is this problem. A long code failing on every destination is a sender with no SMS capability, which is a different note and a different repair.</p>"""},
 {"h": "Segregate the pools by destination",
  "body": """<p>Take the short code out of the mixed service and give international traffic its own Messaging Service with long codes or a registered alphanumeric sender. Then re-run: the check is cheap, and the next person to add a short code to a working service will do it for the same good reason as the last one.</p>"""},
],
"verify": """<p>Re-run after splitting the pools. No service should report a mixed pool, and no short code should carry cross-border rejections.</p>
<pre><code class="language-bash">python3 twilio_short_code_audit.py --home-country 1 --days 7
# 3 service(s), 0 with a short code exposed to cross-border traffic</code></pre>""",
"code_intro": "Four reads: the account's short codes, the Messaging Services, each service's two pool subresources, and the message list for the window. The classifier takes one service's pool and its traffic and decides whether the short code is already failing, exposed, or fine &mdash; and it takes the licensing country as an argument, because the ShortCode resource does not carry one and inventing a default that looks authoritative would be worse than asking.",
"py_file": "twilio_short_code_audit.py",
"py": '''"""Report Twilio short codes exposed to destinations they are not licensed for.

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
log = logging.getLogger("twilio_short_code_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

# 21612 is the combination of To and From that cannot be delivered; 21606 is the
# From that cannot send to this destination. Both are what a short code returns
# for a handset outside its own country, and both are request-time rejections.
CROSS_BORDER = (21612, 21606)

DIAL_CODES = {
    "1", "7", "20", "27", "30", "31", "32", "33", "34", "36", "39", "40", "43",
    "44", "45", "46", "47", "48", "49", "51", "52", "54", "55", "56", "57",
    "58", "60", "61", "62", "63", "64", "65", "66", "81", "82", "84", "86",
    "90", "91", "92", "94", "212", "213", "234", "254", "351", "353", "358",
    "380", "420", "421", "852", "880", "886", "966", "971", "972", "977", "998",
}


def error_code(message):
    """Read error_code as an integer, or None. Some exports return a string, and
    comparing the raw value finds nothing on an account full of findings."""
    raw = message.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def is_short_code(value):
    """True for a short code, which in a message row is simply a short run of
    digits with no plus sign. Long codes are E.164 and alphanumeric senders are
    not digits at all, so this is the whole distinction available."""
    raw = str(value or "").strip()
    return bool(raw) and raw.isdigit() and 3 <= len(raw) <= 8


def dial_code(to):
    """Longest matching country calling code for an E.164 destination, or None.

    A destination this cannot resolve is left out of the cross-border count
    rather than assumed foreign: the point of the count is to be believed. For
    the same reason the count cannot see the border inside +1, where a US short
    code and a Canadian handset share a calling code; that pairing is caught by
    the observed 21612 rejections instead.
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
    """Bucket outbound messages by the Messaging Service that carried them.

    Pure, so the grouping can be tested without a network. Sends with no
    messaging_service_sid are grouped under the empty key: a short code used
    directly as From is exposed in exactly the same way, minus the selection.
    """
    out = {}
    for m in messages:
        if str(m.get("direction") or "").startswith("inbound"):
            continue
        sid = str(m.get("messaging_service_sid") or "")
        row = out.setdefault(sid, {"service": sid, "total": 0, "blocked": 0,
                                   "destinations": {}, "sids": []})
        row["total"] += 1
        code = dial_code(m.get("to"))
        if code:
            row["destinations"][code] = row["destinations"].get(code, 0) + 1
        if error_code(m) in CROSS_BORDER and is_short_code(m.get("from")):
            row["blocked"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(m.get("sid"))
    return out


def verdict(service, home="1"):
    """Classify one Messaging Service's exposure to cross-border short code use.

    `service` carries the pool (`short_codes`, `long_codes`, `alpha_senders`)
    and the traffic tally (`total`, `blocked`, `destinations`). `home` is the
    calling code the short codes are licensed in, and it is an argument because
    the ShortCode resource does not carry a country: guessing one and printing
    it as fact would be worse than asking.

    Pure. Returns (state, detail).
    """
    short = list(service.get("short_codes") or [])
    longs = int(service.get("long_codes") or 0)
    alpha = int(service.get("alpha_senders") or 0)
    blocked = int(service.get("blocked") or 0)
    destinations = service.get("destinations") or {}
    foreign = sum(n for code, n in destinations.items() if code != str(home))

    if not short:
        return ("no-short-code",
                "no short code in the pool, so nothing here can be selected for a "
                "country it is not licensed in.")

    if blocked:
        return ("blocked",
                "%d send(s) from a short code rejected with 21612 or 21606. The "
                "short code %s is licensed for +%s only, and selection handed it "
                "a handset somewhere else."
                % (blocked, ", ".join(short[:2]), home))

    if foreign and not longs and not alpha:
        return ("unreachable-abroad",
                "%d message(s) went to destinations outside +%s and the pool has "
                "nothing but short codes. There is no sender here that can carry "
                "them, so every one of those sends fails at request time."
                % (foreign, home))

    if foreign:
        return ("exposed",
                "the pool mixes %d short code(s) with %d long code(s), and %d "
                "message(s) went outside +%s. Selection is per message, so the "
                "one that draws the short code is rejected while the rest "
                "deliver." % (len(short), longs, foreign, home))

    return ("domestic-only",
            "%d short code(s) in the pool and all %d message(s) stayed inside "
            "+%s. Correct today; the first international recipient is what "
            "changes it." % (len(short), int(service.get("total") or 0), home))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_short_codes(session, account):
    """The account's short codes. The resource carries the digits, the SID and
    the handler URLs, and no country: that has to come from the operator."""
    page = get(session, "%s/Accounts/%s/SMS/ShortCodes.json" % (BASE, account),
               PageSize=100)
    return [str(s.get("short_code") or "") for s in page.get("short_codes", [])]


def list_messages(session, account, since, limit):
    """Page Messages.json. No Status or ErrorCode filter exists here, so the
    window and the page cap are the only bounds."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def pools(session):
    """Every Messaging Service with the shape of its sender pool."""
    out = {}
    services = get(session, "%s/Services" % MESSAGING, PageSize=100).get("services", [])
    for svc in services:
        sid = svc.get("sid")
        codes = get(session, "%s/Services/%s/ShortCodes" % (MESSAGING, sid),
                    PageSize=100).get("short_codes", [])
        numbers = get(session, "%s/Services/%s/PhoneNumbers" % (MESSAGING, sid),
                      PageSize=100).get("phone_numbers", [])
        alpha = get(session, "%s/Services/%s/AlphaSenders" % (MESSAGING, sid),
                    PageSize=100).get("alpha_senders", [])
        out[sid] = {"service": sid,
                    "name": svc.get("friendly_name"),
                    "short_codes": [str(c.get("short_code") or "") for c in codes],
                    "long_codes": len(numbers),
                    "alpha_senders": len(alpha)}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--home-country", default="1",
                    help="calling code the short codes are licensed in; the "
                         "ShortCode resource does not carry one")
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the message list")
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

    account_codes = list_short_codes(session, account)
    if not account_codes:
        log.info("no short codes on this account")
        return 0

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    traffic = tally(list_messages(session, account, since, args.max_messages))
    services = pools(session)

    # Sends with no MessagingServiceSid used a From directly. Judge them too,
    # with the account's short codes standing in for a pool.
    if "" in traffic:
        services.setdefault("", {"service": "", "name": "direct From sends",
                                 "short_codes": account_codes, "long_codes": 1,
                                 "alpha_senders": 0})

    bad = 0
    for sid, pool in sorted(services.items()):
        row = dict(pool)
        row.update({k: v for k, v in traffic.get(sid, {}).items() if k != "service"})
        state, detail = verdict(row, args.home_country)
        label = row.get("name") or sid or "direct"
        line = "%-18s %-24s %s" % (state, str(label)[:24], detail)
        if state in ("no-short-code", "domestic-only"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if row.get("sids"):
            log.warning("  message sids: %s", ", ".join(str(s) for s in row["sids"]))
        log.warning("  repair: detach the short code from this pool (a delete on "
                    "%s/Services/%s/ShortCodes/{Sid}) and route traffic outside "
                    "+%s through a separate Messaging Service holding long codes "
                    "or a registered alphanumeric sender.",
                    MESSAGING, sid or "{ServiceSid}", args.home_country)

    log.info("%d service(s), %d with a short code exposed to cross-border "
             "traffic", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-short-code-audit.mjs",
"js": '''/**
 * Report Twilio short codes exposed to destinations they are not licensed for.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

/**
 * 21612 is the To and From combination that cannot be delivered; 21606 is the
 * From that cannot send to this destination. Both are what a short code returns
 * for a handset outside its own country, and both are request-time rejections.
 */
const CROSS_BORDER = [21612, 21606];

const DIAL_CODES = new Set([
  '1', '7', '20', '27', '30', '31', '32', '33', '34', '36', '39', '40', '43',
  '44', '45', '46', '47', '48', '49', '51', '52', '54', '55', '56', '57', '58',
  '60', '61', '62', '63', '64', '65', '66', '81', '82', '84', '86', '90', '91',
  '92', '94', '212', '213', '234', '254', '351', '353', '358', '380', '420',
  '421', '852', '880', '886', '966', '971', '972', '977', '998',
]);

/** Read error_code as a number, or null. */
export function errorCode(message) {
  const raw = message.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * True for a short code, which in a message row is a short run of digits with
 * no plus sign. Long codes are E.164 and alphanumeric senders are not digits.
 */
export function isShortCode(value) {
  const raw = String(value ?? '').trim();
  return /^\\d{3,8}$/.test(raw);
}

/** Longest matching country calling code for an E.164 destination, or null. */
export function dialCode(to) {
  const raw = String(to ?? '').trim();
  if (!raw.startsWith('+')) return null;
  const digits = raw.slice(1).replace(/\\D/g, '');
  for (const size of [3, 2, 1]) {
    const head = digits.slice(0, size);
    if (DIAL_CODES.has(head)) return head;
  }
  return null;
}

/**
 * Bucket outbound messages by the Messaging Service that carried them. Pure, so
 * the grouping can be tested without a network. Sends with no service are
 * grouped under the empty key: a short code used directly as From is exposed
 * the same way, minus the selection.
 */
export function tally(messages) {
  const out = new Map();
  for (const m of messages) {
    if (String(m.direction ?? '').startsWith('inbound')) continue;
    const sid = String(m.messaging_service_sid ?? '');
    if (!out.has(sid)) {
      out.set(sid, { service: sid, total: 0, blocked: 0, destinations: {}, sids: [] });
    }
    const row = out.get(sid);
    row.total += 1;
    const code = dialCode(m.to);
    if (code) row.destinations[code] = (row.destinations[code] ?? 0) + 1;
    if (CROSS_BORDER.includes(errorCode(m)) && isShortCode(m.from)) {
      row.blocked += 1;
      if (row.sids.length < 3) row.sids.push(m.sid);
    }
  }
  return out;
}

/**
 * Classify one Messaging Service's exposure to cross-border short code use.
 * `home` is the calling code the short codes are licensed in, and it is an
 * argument because the ShortCode resource does not carry a country.
 * Pure. Returns [state, detail].
 */
export function verdict(service, home = '1') {
  const short = service.short_codes ?? [];
  const longs = Number(service.long_codes ?? 0);
  const alpha = Number(service.alpha_senders ?? 0);
  const blocked = Number(service.blocked ?? 0);
  const destinations = service.destinations ?? {};
  const foreign = Object.entries(destinations)
    .filter(([code]) => code !== String(home))
    .reduce((sum, [, n]) => sum + n, 0);

  if (short.length === 0) {
    return ['no-short-code',
      'no short code in the pool, so nothing here can be selected for a country ' +
      'it is not licensed in.'];
  }

  if (blocked) {
    return ['blocked',
      `${blocked} send(s) from a short code rejected with 21612 or 21606. The ` +
      `short code ${short.slice(0, 2).join(', ')} is licensed for +${home} only, ` +
      'and selection handed it a handset somewhere else.'];
  }

  if (foreign && !longs && !alpha) {
    return ['unreachable-abroad',
      `${foreign} message(s) went to destinations outside +${home} and the pool ` +
      'has nothing but short codes. There is no sender here that can carry them, ' +
      'so every one of those sends fails at request time.'];
  }

  if (foreign) {
    return ['exposed',
      `the pool mixes ${short.length} short code(s) with ${longs} long code(s), ` +
      `and ${foreign} message(s) went outside +${home}. Selection is per ` +
      'message, so the one that draws the short code is rejected while the rest ' +
      'deliver.'];
  }

  return ['domestic-only',
    `${short.length} short code(s) in the pool and all ${Number(service.total ?? 0)} ` +
    `message(s) stayed inside +${home}. Correct today; the first international ` +
    'recipient is what changes it.'];
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

async function pools(auth) {
  const out = new Map();
  const services = (await get(auth, `${MESSAGING}/Services`, { PageSize: 100 })).services ?? [];
  for (const svc of services) {
    const codes = (await get(auth, `${MESSAGING}/Services/${svc.sid}/ShortCodes`,
                             { PageSize: 100 })).short_codes ?? [];
    const numbers = (await get(auth, `${MESSAGING}/Services/${svc.sid}/PhoneNumbers`,
                               { PageSize: 100 })).phone_numbers ?? [];
    const alpha = (await get(auth, `${MESSAGING}/Services/${svc.sid}/AlphaSenders`,
                             { PageSize: 100 })).alpha_senders ?? [];
    out.set(svc.sid, {
      service: svc.sid,
      name: svc.friendly_name,
      short_codes: codes.map((c) => String(c.short_code ?? '')),
      long_codes: numbers.length,
      alpha_senders: alpha.length,
    });
  }
  return out;
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
  const homeIdx = process.argv.indexOf('--home-country');
  const home = homeIdx === -1 ? '1' : String(process.argv[homeIdx + 1]);
  const days = Number(process.argv[process.argv.indexOf('--days') + 1]) || 7;

  const shortCodes = (await get(auth, `${BASE}/Accounts/${account}/SMS/ShortCodes.json`,
                                { PageSize: 100 })).short_codes ?? [];
  if (shortCodes.length === 0) {
    console.log('no short codes on this account');
    return;
  }

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const traffic = tally(await listMessages(auth, account, since));
  const services = await pools(auth);

  // Sends with no MessagingServiceSid used a From directly. Judge them too,
  // with the account's short codes standing in for a pool.
  if (traffic.has('') && !services.has('')) {
    services.set('', {
      service: '', name: 'direct From sends',
      short_codes: shortCodes.map((c) => String(c.short_code ?? '')),
      long_codes: 1, alpha_senders: 0,
    });
  }

  let bad = 0;
  for (const sid of [...services.keys()].sort()) {
    const row = { ...services.get(sid), ...(traffic.get(sid) ?? {}) };
    row.service = sid;
    const [state, detail] = verdict(row, home);
    const label = String(row.name ?? sid ?? 'direct').slice(0, 24);
    const line = `${state.padEnd(18)} ${label.padEnd(24)} ${detail}`;
    if (state === 'no-short-code' || state === 'domestic-only') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (row.sids?.length) console.warn(`  message sids: ${row.sids.join(', ')}`);
    console.warn('  repair: detach the short code from this pool (a delete on ' +
                 `${MESSAGING}/Services/${sid || '{ServiceSid}'}/ShortCodes/{Sid}) ` +
                 `and route traffic outside +${home} through a separate Messaging ` +
                 'Service holding long codes or a registered alphanumeric sender.');
  }

  console.log(`${services.size} service(s), ${bad} with a short code exposed to ` +
              'cross-border traffic');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not start an audit and fail on the missing credentials.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two cases that decide whether this report is worth reading are the mixed pool that has not failed yet and the pool that has. Both are findings; only one of them has message SIDs attached. The rest of the tests keep a short-code-only domestic service out of the list, and keep a <code>21606</code> from a long code from being counted as this problem at all.",
"test_py_file": "test_twilio_short_code_audit.py",
"test_py": '''from twilio_short_code_audit import dial_code, is_short_code, tally, verdict


def make(sender, to, code=None, service="MG1", direction="outbound-api", sid="SM1"):
    return {"from": sender, "to": to, "error_code": code, "sid": sid,
            "messaging_service_sid": service, "direction": direction}


def pool(**over):
    p = {"short_codes": ["12345"], "long_codes": 2, "alpha_senders": 0,
         "total": 0, "blocked": 0, "destinations": {}}
    p.update(over)
    return p


def test_short_code_already_rejected_abroad():
    row = tally([make("12345", "+14165550123", 21612)])["MG1"]
    state, detail = verdict(pool(**{k: v for k, v in row.items() if k != "service"}))
    assert state == "blocked"
    assert "21612" in detail


def test_mixed_pool_with_foreign_traffic_is_exposed_before_it_fails():
    row = tally([make("+12025550123", "+447700900123"),
                 make("+12025550123", "+12025550124")])["MG1"]
    state, detail = verdict(pool(**{k: v for k, v in row.items() if k != "service"}))
    assert state == "exposed"
    assert "per message" in detail


def test_pool_of_short_codes_only_cannot_reach_abroad_at_all():
    row = tally([make("12345", "+447700900123")])["MG1"]
    state, detail = verdict(pool(long_codes=0, alpha_senders=0,
                                 **{k: v for k, v in row.items() if k != "service"}))
    assert state == "unreachable-abroad"
    assert "request time" in detail


def test_domestic_only_traffic_is_not_a_finding():
    row = tally([make("12345", "+12025550123")])["MG1"]
    state, _ = verdict(pool(**{k: v for k, v in row.items() if k != "service"}))
    assert state == "domestic-only"


def test_service_with_no_short_code_is_skipped():
    assert verdict(pool(short_codes=[], destinations={"44": 5}))[0] == "no-short-code"


def test_21606_from_a_long_code_is_not_counted_as_this_problem():
    # Same error code, different fault: a voice-only long code fails everywhere.
    row = tally([make("+12025550123", "+14165550123", 21606)])["MG1"]
    assert row["blocked"] == 0


def test_home_country_is_an_argument_because_the_resource_has_no_country():
    row = tally([make("12345", "+447700900123")])["MG1"]
    stats = {k: v for k, v in row.items() if k != "service"}
    assert verdict(pool(**stats), home="1")[0] == "exposed"
    assert verdict(pool(**stats), home="44")[0] == "domestic-only"


def test_the_border_inside_plus_one_is_only_visible_in_the_rejections():
    # A US short code cannot reach a Canadian handset, but both share calling
    # code 1, so the destination count cannot see it and only the 21612 does.
    quiet = tally([make("12345", "+14165550123")])["MG1"]
    assert verdict(pool(**{k: v for k, v in quiet.items() if k != "service"}))[0] == \
        "domestic-only"
    loud = tally([make("12345", "+14165550123", 21612)])["MG1"]
    assert verdict(pool(**{k: v for k, v in loud.items() if k != "service"}))[0] == \
        "blocked"


def test_short_code_and_dial_code_helpers():
    assert is_short_code("12345")
    assert not is_short_code("+12025550123")
    assert not is_short_code("MyBrand")
    assert dial_code("+447700900123") == "44"
''',
"test_js_file": "twilio-short-code-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dialCode, isShortCode, tally, verdict } from './twilio-short-code-audit.mjs';

const make = (sender, to, code = null, service = 'MG1') => ({
  from: sender, to, error_code: code, sid: 'SM1',
  messaging_service_sid: service, direction: 'outbound-api',
});

const pool = (over = {}) => ({
  short_codes: ['12345'], long_codes: 2, alpha_senders: 0,
  total: 0, blocked: 0, destinations: {}, ...over,
});

const stats = (messages) => {
  const { service, ...rest } = tally(messages).get('MG1');
  return rest;
};

test('short code already rejected abroad', () => {
  const [state, detail] = verdict(pool(stats([make('12345', '+14165550123', 21612)])));
  assert.equal(state, 'blocked');
  assert.match(detail, /21612/);
});

test('mixed pool with foreign traffic is exposed before it fails', () => {
  const [state, detail] = verdict(pool(stats([
    make('+12025550123', '+447700900123'), make('+12025550123', '+12025550124'),
  ])));
  assert.equal(state, 'exposed');
  assert.match(detail, /per message/);
});

test('pool of short codes only cannot reach abroad at all', () => {
  const [state, detail] = verdict(pool({
    long_codes: 0, alpha_senders: 0, ...stats([make('12345', '+447700900123')]),
  }));
  assert.equal(state, 'unreachable-abroad');
  assert.match(detail, /request time/);
});

test('domestic only traffic is not a finding', () => {
  const [state] = verdict(pool(stats([make('12345', '+12025550123')])));
  assert.equal(state, 'domestic-only');
});

test('service with no short code is skipped', () => {
  assert.equal(verdict(pool({ short_codes: [], destinations: { 44: 5 } }))[0],
               'no-short-code');
});

test('21606 from a long code is not counted as this problem', () => {
  assert.equal(stats([make('+12025550123', '+14165550123', 21606)]).blocked, 0);
});

test('home country is an argument because the resource has no country', () => {
  const s = stats([make('12345', '+447700900123')]);
  assert.equal(verdict(pool(s), '1')[0], 'exposed');
  assert.equal(verdict(pool(s), '44')[0], 'domestic-only');
});

test('the border inside +1 is only visible in the rejections', () => {
  // A US short code cannot reach a Canadian handset, but both share calling
  // code 1, so the destination count cannot see it and only the 21612 does.
  assert.equal(verdict(pool(stats([make('12345', '+14165550123')])))[0], 'domestic-only');
  assert.equal(verdict(pool(stats([make('12345', '+14165550123', 21612)])))[0], 'blocked');
});

test('short code and dial code helpers', () => {
  assert.equal(isShortCode('12345'), true);
  assert.equal(isShortCode('+12025550123'), false);
  assert.equal(isShortCode('MyBrand'), false);
  assert.equal(dialCode('+447700900123'), '44');
});
''',
"faq": [
 ("Why does the script ask which country the short code belongs to?",
  "Because the API does not say. The ShortCode resource returns the digits, the SID, the handler URLs and the API version, and no country field, so the licensing country has to come from you. A default that looked authoritative would be worse than an argument you have to fill in, so it is a flag with a documented US default."),
 ("Is this the same as error 21606 from a long code?",
  "No, and the report separates them by sender for exactly that reason. A long code returning 21606 on every destination is a number without SMS capability. A short code returning it only on foreign destinations is a national licence meeting an international recipient. Same code, different repair."),
 ("The pool has never had an international send. Is it still a finding?",
  "It is reported, at a lower level than a pool that has already failed. Sender selection happens per message, so nothing is wrong until the first foreign recipient and then everything is. Knowing which pools carry that fuse is cheaper than finding out from a customer."),
 ("Does A2P 10DLC registration cover the short code?",
  "It does not apply to it at all: short codes sit outside 10DLC and need no brand or campaign. That is why the assumption is so easy to make. Registration says nothing about geography, and the geographic rule is the one being broken here."),
 ("Why might the failure count be lower than the real one?",
  "Two reasons, and both make the count a floor rather than a total. 21612 and 21606 are request-time rejections, so a send refused before a message row exists appears in the Alerts log instead of the message list. And the destination count groups by calling code, which cannot see the border inside +1: a US short code and a Canadian handset share it, so that pairing shows up only once it has already been rejected. Treat a mixed pool with no failures as unproven rather than clean."),
],
"related": [
 ("/twilio/from-number-not-sms-capable/", "A voice-only From number failing every SMS"),
 ("/twilio/messaging-service-empty-sender-pool/", "A Messaging Service with no sender at all"),
 ("/twilio/alphanumeric-sender-id-unregistered/", "The sender ID unregistered where you send"),
],
"citations": [CITE_SHORTCODE, CITE_21612, CITE_SERVICE, CITE_MESSAGE],
},

]
