#!/usr/bin/env python3
"""/twilio/ field notes, batch AB — the writing.

Five voice problems, and they sort into two kinds. Two are read off the call
records themselves: a Dial destination Twilio refuses to terminate on, and an
answering-machine classifier that is putting live humans into the voicemail
branch. One is read off a resource that exists while the thing it points at does
not: a Recording row with status absent. Two are the same dialling-permissions
listing read in opposite directions, and they are deliberately a pair — one is
legitimate destinations blocked, the other is high-risk destinations left open,
which is the toll-fraud exposure.

Read-only throughout. An API Key with read access, never the account auth token,
and every repair is printed for a human to run rather than performed.

The rule carried over from the earlier voice batches still applies: several
voice failures are logged at LogLevel=warning rather than error, including some
of the 132xx Dial attribute errors. Every script here that reads Alerts sweeps
both levels, because an error-only sweep reports a clean account while the calls
keep failing.
"""

CITE_13224 = ("Error 13224: Dial: Twilio does not support calling this number "
              "— Twilio Docs", "https://www.twilio.com/docs/api/errors/13224")
CITE_TWIML_DIAL = ("TwiML Voice: &lt;Dial&gt; — Twilio Docs",
                   "https://www.twilio.com/docs/voice/twiml/dial")
CITE_LOOKUP = ("Lookup v2 API — Twilio Docs",
               "https://www.twilio.com/docs/lookup/v2-api")
CITE_ALERT = ("Alert resource (Monitor) — Twilio Docs",
              "https://www.twilio.com/docs/usage/monitor-alert")
CITE_CALL = ("Call resource — Twilio Docs",
             "https://www.twilio.com/docs/voice/api/call-resource")
CITE_AMD = ("Answering Machine Detection — Twilio Docs",
            "https://www.twilio.com/docs/voice/answering-machine-detection")
CITE_MAKE_CALLS = ("Making calls — Twilio Docs",
                   "https://www.twilio.com/docs/voice/make-calls")
CITE_RECORDING = ("Recording resource — Twilio Docs",
                  "https://www.twilio.com/docs/voice/api/recording")
CITE_TWIML_RECORD = ("TwiML Voice: &lt;Record&gt; — Twilio Docs",
                     "https://www.twilio.com/docs/voice/twiml/record")
CITE_DP_COUNTRY = ("DialingPermissions Country resource — Twilio Docs",
                   "https://www.twilio.com/docs/voice/api/dialingpermissions-country-resource")
CITE_DP_SETTINGS = ("DialingPermissions Settings resource — Twilio Docs",
                    "https://www.twilio.com/docs/voice/api/dialingpermissions-settings-resource")
CITE_DP_RESOURCES = ("Voice Dialing Permissions — Twilio Docs",
                     "https://www.twilio.com/docs/voice/api/dialing-permissions-resources")
CITE_DP_PREFIX = ("DialingPermissions HighRiskSpecialPrefix resource — Twilio Docs",
                  "https://www.twilio.com/docs/voice/api/dialingpermissions-highriskspecialprefix-resource")
CITE_21215 = ("Error 21215: Account not authorized to call this number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21215")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "dial-number-unsupported-or-invalid-13224",
"title": "13224: Twilio refuses the number your Dial verb asked for",
"description": "The leg never rings and the parent call carries on to the action URL. The destination is national format, a premium range, or a number that does not exist.",
"h1": "13224: Twilio refuses the number your Dial verb asked for",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 13224", "twilio does not support calling this number",
             "twilio dial invalid number", "twilio e164 normalization",
             "twilio premium rate blocked"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The call connects, your TwiML runs, the <code>&lt;Dial&gt;</code> produces silence, and then the call carries on to the action URL as though the leg had simply not been answered. Nobody rang. <code>13224 Dial: Twilio does not support calling this number or the number is invalid</code> is sitting in the Debugger, and about half the time it is not in the error level at all.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts</code> at <strong>both</strong> <code>LogLevel=error</code> and <code>LogLevel=warning</code> and keep <code>error_code</code> <code>13224</code>. Several 132xx Dial attribute errors are logged as warnings, so an error-only sweep will tell you this is not happening while it happens.</p>
<p>Take each alert's <code>resource_sid</code> and read <code>GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json</code>. When <code>direction</code> is <code>outbound-api</code>, <code>outbound-dial</code> or <code>trunking</code>, the record's <code>to</code> is the destination that was refused and you can classify it directly. When <code>direction</code> is <code>inbound</code>, <code>to</code> is your own number and the dial target is not on that record at all &mdash; the request variables live only on the single-alert fetch <code>GET /v1/Alerts/{AlertSid}</code>, never in the list response.</p>""",
"problem": """<p>13224 is a refusal, not a failure, and refusals are quiet. Twilio looked at the destination, decided it would not place the call, and returned control to your TwiML. The <code>&lt;Dial&gt;</code> ends with no <code>DialCallStatus</code> worth branching on, your action URL runs its "nobody answered" path, and the caller hears whatever you wrote for that case. Which is usually an apology, so it sounds like the far end was busy.</p>
<p>The parent call's <code>status</code> is <code>completed</code>. There is no failed call to count, no child leg to inspect, no duration anomaly. The only artefact anywhere is a Debugger alert that a dashboard filtered to the error level may never show you. So the failure gets attributed to the recipients &mdash; they are not picking up, their numbers are stale, the list is bad &mdash; and the list is indeed bad, but in a way that a script can name exactly.</p>""",
"why": """<p><strong>The numbers come out of a column that predates E.164.</strong> A CRM that stored <code>(0161) 496 0000</code> or <code>0161 496 0000</code> for fifteen years is not wrong; it is national format, which is what a human writes down. Fed into <code>&lt;Number&gt;</code> it is a destination Twilio cannot resolve to a country, and the refusal is immediate and total.</p>
<p><strong>Normalising on the way in feels like it has been done.</strong> Most such systems have a normaliser somewhere. It runs on the signup path, or the import path, or the path that was in scope when the ticket was written, and the rows that came in through the other three paths sit there looking exactly like the ones that were cleaned.</p>
<p><strong>Some destinations are refused on purpose and read as valid.</strong> A premium-rate, shared-cost or special-service range is well-formed E.164, passes every regex you own, and is a range Twilio will not terminate on. The number is not invalid. It is unsupported, which is the other half of the error text and the half people skip.</p>
<p><strong>The error names no number.</strong> Read the alert list and you get a count and a call SID. The destination is one join away on the Calls resource, and only when the call is outbound &mdash; on an inbound forwarding leg it is one <em>extra</em> fetch away, on the single alert, because the list response omits the request variables entirely.</p>""",
"steps": [
 {"h": "Sweep the Alerts API at both log levels",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, then the same request at <code>LogLevel=warning</code>, following <code>meta.next_page_url</code> &mdash; this API paginates with an absolute URL rather than the relative <code>next_page_uri</code> the 2010-04-01 API uses. Merge on <code>sid</code>. Alerts are retained 30 days, so a 90-day window quietly becomes a 30-day one.</p>"""},
 {"h": "Resolve each alert to the call it was raised against",
  "body": """<p>The alert's <code>resource_sid</code> is a <code>CA</code> call SID. <code>GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json</code> gives you <code>to</code> and <code>direction</code>. Cache by SID: one bad batch produces many alerts against a handful of calls, and the fetch is the expensive part of this check.</p>"""},
 {"h": "Decide whether the record can even carry the answer",
  "body": """<p><code>direction</code> is the gate. Outbound and trunking calls carry the refused destination in <code>to</code>. An <code>inbound</code> call does not: <code>to</code> is the number the caller dialled, which is yours and is fine, and reporting it as the bad destination is the mistake this check exists to avoid. For those, fetch <code>GET https://monitor.twilio.com/v1/Alerts/{AlertSid}</code> &mdash; <code>alert_text</code>, <code>request_variables</code> and the rest are populated only on the single-alert fetch.</p>"""},
 {"h": "Classify the destination string strictly, without cleaning it first",
  "body": """<p>Test for a plus followed by digits and nothing else. Do not strip brackets, spaces or dashes before the test: the punctuation <em>is</em> the finding. A destination that only becomes E.164 after your script tidies it is a destination your application should have tidied and did not.</p>"""},
 {"h": "Normalise at the source, then validate what survives",
  "body": """<p>Convert to E.164 where the row is stored, not in the dial path, so every caller of that column benefits. Then <code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}</code> and keep only the numbers whose <code>valid</code> is <code>true</code>. Exclude premium and special-service ranges from the dial list outright; they will be refused every time and each attempt is a failed leg your campaign counts as a no-answer.</p>"""},
],
"verify": """<p>Re-run the sweep over a window that begins after the deploy. The 13224 count should be zero.</p>
<pre><code class="language-bash">python3 twilio_dial_target_audit.py --days 7
# 0 alert(s) with error_code 13224 in the last 7 day(s)</code></pre>""",
"code_intro": "Two paginated alert sweeps, one cached call fetch per failing call, and one optional single-alert fetch for the inbound cases the call record cannot answer. Every request is a GET and an API Key with read access is enough. Three pure functions hold the diagnosis: one tests a destination for strict E.164, one matches it against the international ranges that are refused by allocation, and one turns a call into a verdict. The strictness of the first is the whole point &mdash; a parser that helpfully normalises the punctuation away reports a clean list of the numbers that just failed.",
"py_file": "twilio_dial_target_audit.py",
"py": '''"""Report Twilio 13224 alerts and say why each Dial destination was refused.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_dial_target_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

UNSUPPORTED = 13224

# Ranges that are premium, shared cost or special service by international
# allocation rather than by national convention. The table is deliberately
# short. Every country also has its own premium ranges, and a table of all of
# them is a maintenance project you will lose; Lookups settles the rest.
REFUSED_PREFIXES = (
    ("+979", "ITU international premium rate service"),
    ("+808", "ITU international shared cost service"),
    ("+882", "ITU international networks"),
    ("+883", "ITU international networks"),
    ("+881", "global mobile satellite system"),
    ("+870", "Inmarsat single network access code"),
    ("+4470", "UK personal numbering, forwarded at premium cost"),
    ("+449", "UK premium rate"),
    ("+1900", "North American premium rate"),
)

# Directions whose call record carries the destination that was dialled. An
# inbound call does not: its `to` is your own number.
OUTBOUND = ("outbound-api", "outbound-dial", "trunking")


def e164_digits(to):
    """The digits of a strictly E.164 destination, or an empty string.

    Strict deliberately. A plus, then one to fifteen digits, and nothing else:
    no spaces, no brackets, no dashes, no leading zero after the plus.
    Normalising the punctuation away here would destroy the evidence, because a
    column of national-format numbers going straight into the Dial noun is the
    single most common cause of this error.
    """
    v = str(to or "").strip()
    if not v.startswith("+"):
        return ""
    digits = v[1:]
    if not digits.isdigit() or not 1 <= len(digits) <= 15:
        return ""
    return digits


def refused_range(to):
    """The allocation a destination falls in, or an empty string.

    Longest prefix wins, so +4470 is reported as personal numbering rather than
    as UK premium rate.
    """
    v = str(to or "").strip()
    best, label = "", ""
    for prefix, name in REFUSED_PREFIXES:
        if v.startswith(prefix) and len(prefix) > len(best):
            best, label = prefix, name
    return label


def verdict(call):
    """Explain one 13224 from the call it was raised against.

    Pure, so the rules can be tested without a network. `call` is the Call
    resource the alert's resource_sid resolved to. Returns (state, detail).
    """
    to = str(call.get("to") or "").strip()
    direction = str(call.get("direction") or "").strip().lower()

    if not to:
        return ("no-destination",
                "the call record has no `to`, so there is nothing to classify. "
                "Read the single alert for the request variables.")

    if direction and direction not in OUTBOUND:
        return ("target-not-on-record",
                "direction is %s, so `to` (%s) is the number the caller dialled "
                "and not the destination that was refused. The dial target is "
                "in the request variables, which are populated only on GET "
                "/v1/Alerts/{AlertSid}." % (direction, to))

    low = to.lower()
    if low.startswith("sip:") or low.startswith("sips:") or low.startswith("client:"):
        return ("non-pstn",
                "%s is not a PSTN destination, so this refusal is about a "
                "different Dial noun and E.164 has nothing to do with it." % to)

    if not to.startswith("+"):
        return ("not-e164",
                "%s has no leading plus, so Twilio cannot tell which country it "
                "belongs to. This is national format arriving straight from a "
                "column that predates E.164." % to)

    digits = e164_digits(to)
    if not digits:
        return ("malformed",
                "%s starts with a plus but is not digits after it, or runs past "
                "the fifteen digit E.164 ceiling. The punctuation is the "
                "finding: the value was never normalised." % to)

    if len(digits) < 8:
        return ("too-short",
                "%s carries only %d digits, which is shorter than a full "
                "international destination. This is usually an internal "
                "extension dialled as though it were a phone number."
                % (to, len(digits)))

    allocation = refused_range(to)
    if allocation:
        return ("refused-range",
                "%s is in the %s range. It is well formed and it is unsupported, "
                "which is the other half of the error text: Twilio will not "
                "terminate on it, today or ever." % (to, allocation))

    return ("unallocated",
            "%s is shaped correctly and is outside the ranges this table knows, "
            "so the number itself does not exist: an unassigned area code, a "
            "country code that was never allocated, or a digit lost in "
            "transcription. Lookups v2 will report valid false." % to)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, since, limit, log_level):
    """Page the Monitor alerts at one log level. next_page_url is absolute."""
    url = MONITOR + "/Alerts"
    params = {"LogLevel": log_level, "StartDate": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def sweep_alerts(session, since, limit, levels):
    """Both log levels, merged on sid.

    Several of the 132xx Dial attribute errors are logged at warning rather than
    error. A sweep that reads only the error level reports a clean account while
    the legs keep failing, which is why this takes a list of levels at all.
    """
    seen = {}
    for level in levels:
        for a in list_alerts(session, since, limit, level):
            seen.setdefault(a.get("sid"), a)
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to sweep (alerts are retained 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop after this many alerts per log level")
    ap.add_argument("--errors-only", action="store_true",
                    help="skip the warning level, which will under-report")
    ap.add_argument("--alert-detail", action="store_true",
                    help="one extra GET per inbound case for the request variables")
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
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    levels = ["error"] if args.errors_only else ["error", "warning"]

    alerts = sweep_alerts(session, since, args.max_alerts, levels)
    hits = [a for a in alerts
            if str(a.get("error_code") or "").strip() == str(UNSUPPORTED)]
    if not hits:
        log.info("0 alert(s) with error_code %d in the last %d day(s)",
                 UNSUPPORTED, days)
        return 0

    calls = {}
    counts = {}
    for a in hits:
        sid = str(a.get("resource_sid") or "")
        if not sid.startswith("CA"):
            log.warning("13224 alert %s has no call sid to resolve", a.get("sid"))
            continue
        if sid not in calls:
            calls[sid] = get(session, "%s/Accounts/%s/Calls/%s.json"
                             % (BASE, account, sid))
        state, detail = verdict(calls[sid])
        counts[state] = counts.get(state, 0) + 1
        log.warning("%-21s %s  %s", state, sid, detail)
        if state == "target-not-on-record" and args.alert_detail:
            one = get(session, "%s/Alerts/%s" % (MONITOR, a.get("sid")))
            log.warning("  alert_text: %s", one.get("alert_text"))

    log.warning("%d alert(s) with error_code %d across %d call(s): %s",
                len(hits), UNSUPPORTED, len(calls),
                ", ".join("%s=%d" % kv for kv in sorted(counts.items())))
    log.warning("  repair: normalise the destination column to E.164 where it "
                "is stored, then validate with GET "
                "https://lookups.twilio.com/v2/PhoneNumbers/{E164} and keep "
                "only valid == true")
    log.warning("  repair: exclude premium and special service ranges from the "
                "dial list; they are refused every time")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-dial-target-audit.mjs",
"js": '''/**
 * Report Twilio 13224 alerts and say why each Dial destination was refused.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const UNSUPPORTED = 13224;

// Premium, shared cost and special service ranges by international allocation.
// Deliberately short: national premium ranges are a table you will lose track
// of, and Lookups settles the rest.
const REFUSED_PREFIXES = [
  ['+979', 'ITU international premium rate service'],
  ['+808', 'ITU international shared cost service'],
  ['+882', 'ITU international networks'],
  ['+883', 'ITU international networks'],
  ['+881', 'global mobile satellite system'],
  ['+870', 'Inmarsat single network access code'],
  ['+4470', 'UK personal numbering, forwarded at premium cost'],
  ['+449', 'UK premium rate'],
  ['+1900', 'North American premium rate'],
];

const OUTBOUND = ['outbound-api', 'outbound-dial', 'trunking'];

/**
 * The digits of a strictly E.164 destination, or an empty string. Strict on
 * purpose: cleaning the punctuation here would destroy the evidence.
 */
export function e164Digits(to) {
  const v = String(to ?? '').trim();
  if (!v.startsWith('+')) return '';
  const digits = v.slice(1);
  if (!/^[0-9]+$/.test(digits) || digits.length > 15) return '';
  return digits;
}

/** The allocation a destination falls in, or an empty string. Longest wins. */
export function refusedRange(to) {
  const v = String(to ?? '').trim();
  let best = '';
  let label = '';
  for (const [prefix, name] of REFUSED_PREFIXES) {
    if (v.startsWith(prefix) && prefix.length > best.length) {
      best = prefix;
      label = name;
    }
  }
  return label;
}

/**
 * Explain one 13224 from the call it was raised against. Pure. Returns
 * [state, detail].
 */
export function verdict(call) {
  const to = String(call.to ?? '').trim();
  const direction = String(call.direction ?? '').trim().toLowerCase();

  if (!to) {
    return ['no-destination',
      'the call record has no `to`, so there is nothing to classify. Read the ' +
      'single alert for the request variables.'];
  }

  if (direction && !OUTBOUND.includes(direction)) {
    return ['target-not-on-record',
      `direction is ${direction}, so \\`to\\` (${to}) is the number the caller ` +
      'dialled and not the destination that was refused. The dial target is in ' +
      'the request variables, which are populated only on GET ' +
      '/v1/Alerts/{AlertSid}.'];
  }

  const low = to.toLowerCase();
  if (low.startsWith('sip:') || low.startsWith('sips:') || low.startsWith('client:')) {
    return ['non-pstn',
      `${to} is not a PSTN destination, so this refusal is about a different ` +
      'Dial noun and E.164 has nothing to do with it.'];
  }

  if (!to.startsWith('+')) {
    return ['not-e164',
      `${to} has no leading plus, so Twilio cannot tell which country it ` +
      'belongs to. This is national format arriving straight from a column ' +
      'that predates E.164.'];
  }

  const digits = e164Digits(to);
  if (!digits) {
    return ['malformed',
      `${to} starts with a plus but is not digits after it, or runs past the ` +
      'fifteen digit E.164 ceiling. The punctuation is the finding: the value ' +
      'was never normalised.'];
  }

  if (digits.length < 8) {
    return ['too-short',
      `${to} carries only ${digits.length} digits, which is shorter than a ` +
      'full international destination. This is usually an internal extension ' +
      'dialled as though it were a phone number.'];
  }

  const allocation = refusedRange(to);
  if (allocation) {
    return ['refused-range',
      `${to} is in the ${allocation} range. It is well formed and it is ` +
      'unsupported, which is the other half of the error text: Twilio will not ' +
      'terminate on it, today or ever.'];
  }

  return ['unallocated',
    `${to} is shaped correctly and is outside the ranges this table knows, so ` +
    'the number itself does not exist: an unassigned area code, a country code ' +
    'that was never allocated, or a digit lost in transcription. Lookups v2 ' +
    'will report valid false.'];
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

async function listAlerts(auth, since, limit, logLevel) {
  let url = `${MONITOR}/Alerts`;
  let params = { LogLevel: logLevel, StartDate: since, PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.alerts ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Both log levels, merged on sid. Some 132xx errors are logged as warnings. */
export async function sweepAlerts(auth, since, limit, levels) {
  const seen = new Map();
  for (const level of levels) {
    for (const a of await listAlerts(auth, since, limit, level)) {
      if (!seen.has(a.sid)) seen.set(a.sid, a);
    }
  }
  return [...seen.values()];
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
    return i === -1 ? fallback : Number(process.argv[i + 1]);
  };
  const days = Math.min(arg('--days', 7), 30);
  const detail = process.argv.includes('--alert-detail');
  const levels = process.argv.includes('--errors-only') ? ['error'] : ['error', 'warning'];

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const alerts = await sweepAlerts(auth, since, 10000, levels);
  const hits = alerts.filter((a) => String(a.error_code ?? '').trim() === String(UNSUPPORTED));
  if (hits.length === 0) {
    console.log(`0 alert(s) with error_code ${UNSUPPORTED} in the last ${days} day(s)`);
    return;
  }

  const calls = new Map();
  const counts = new Map();
  for (const a of hits) {
    const sid = String(a.resource_sid ?? '');
    if (!sid.startsWith('CA')) {
      console.warn(`13224 alert ${a.sid} has no call sid to resolve`);
      continue;
    }
    if (!calls.has(sid)) {
      calls.set(sid, await get(auth, `${BASE}/Accounts/${account}/Calls/${sid}.json`));
    }
    const [state, why] = verdict(calls.get(sid));
    counts.set(state, (counts.get(state) ?? 0) + 1);
    console.warn(`${state.padEnd(21)} ${sid}  ${why}`);
    if (state === 'target-not-on-record' && detail) {
      const one = await get(auth, `${MONITOR}/Alerts/${a.sid}`);
      console.warn(`  alert_text: ${one.alert_text}`);
    }
  }

  const summary = [...counts.entries()].sort().map(([k, v]) => `${k}=${v}`).join(', ');
  console.warn(`${hits.length} alert(s) with error_code ${UNSUPPORTED} across ` +
               `${calls.size} call(s): ${summary}`);
  console.warn('  repair: normalise the destination column to E.164 where it is ' +
               'stored, then validate with GET ' +
               'https://lookups.twilio.com/v2/PhoneNumbers/{E164} and keep only ' +
               'valid == true');
  console.warn('  repair: exclude premium and special service ranges from the ' +
               'dial list; they are refused every time');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry this note. The first is the inbound call whose <code>to</code> is a perfectly valid number that has nothing to do with the failure &mdash; a checker that classifies it will report your own inbound line as an invalid destination and send somebody to look at the wrong thing. The second is the punctuated number: <code>+44 161 496 0000</code> must come back as malformed rather than being tidied into a pass, because tidying it is exactly what the application failed to do.",
"test_py_file": "test_twilio_dial_target_audit.py",
"test_py": '''from twilio_dial_target_audit import e164_digits, refused_range, verdict


def test_national_format_is_the_common_cause():
    state, detail = verdict({"to": "01614960000", "direction": "outbound-api"})
    assert state == "not-e164"
    assert "predates E.164" in detail


def test_punctuated_number_is_malformed_rather_than_tidied():
    # Cleaning it here would hide the thing the application should have done.
    state, _ = verdict({"to": "+44 161 496 0000", "direction": "outbound-api"})
    assert state == "malformed"


def test_inbound_call_does_not_carry_the_dial_target():
    state, detail = verdict({"to": "+441614960000", "direction": "inbound"})
    assert state == "target-not-on-record"
    assert "AlertSid" in detail


def test_premium_range_is_unsupported_not_invalid():
    state, detail = verdict({"to": "+19005551234", "direction": "outbound-api"})
    assert state == "refused-range"
    assert "North American premium rate" in detail


def test_longest_prefix_wins_over_the_shorter_one():
    assert refused_range("+447012345678") == \\
        "UK personal numbering, forwarded at premium cost"
    assert refused_range("+449001234567") == "UK premium rate"


def test_extension_dialled_as_a_number_is_too_short():
    state, _ = verdict({"to": "+4021", "direction": "outbound-dial"})
    assert state == "too-short"


def test_well_formed_unknown_number_points_at_lookups():
    state, detail = verdict({"to": "+15005550001", "direction": "outbound-api"})
    assert state == "unallocated"
    assert "valid false" in detail


def test_e164_digits_is_strict_about_the_ceiling_and_the_plus():
    assert e164_digits("+441614960000") == "441614960000"
    assert e164_digits("441614960000") == ""
    assert e164_digits("+1234567890123456") == ""
''',
"test_js_file": "twilio-dial-target-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { e164Digits, refusedRange, verdict } from './twilio-dial-target-audit.mjs';

test('national format is the common cause', () => {
  const [state, detail] = verdict({ to: '01614960000', direction: 'outbound-api' });
  assert.equal(state, 'not-e164');
  assert.match(detail, /predates E\\.164/);
});

test('punctuated number is malformed rather than tidied', () => {
  assert.equal(verdict({ to: '+44 161 496 0000', direction: 'outbound-api' })[0],
               'malformed');
});

test('inbound call does not carry the dial target', () => {
  const [state, detail] = verdict({ to: '+441614960000', direction: 'inbound' });
  assert.equal(state, 'target-not-on-record');
  assert.match(detail, /AlertSid/);
});

test('premium range is unsupported not invalid', () => {
  const [state, detail] = verdict({ to: '+19005551234', direction: 'outbound-api' });
  assert.equal(state, 'refused-range');
  assert.match(detail, /North American premium rate/);
});

test('longest prefix wins over the shorter one', () => {
  assert.equal(refusedRange('+447012345678'),
               'UK personal numbering, forwarded at premium cost');
  assert.equal(refusedRange('+449001234567'), 'UK premium rate');
});

test('extension dialled as a number is too short', () => {
  assert.equal(verdict({ to: '+4021', direction: 'outbound-dial' })[0], 'too-short');
});

test('well formed unknown number points at lookups', () => {
  const [state, detail] = verdict({ to: '+15005550001', direction: 'outbound-api' });
  assert.equal(state, 'unallocated');
  assert.match(detail, /valid false/);
});

test('e164Digits is strict about the ceiling and the plus', () => {
  assert.equal(e164Digits('+441614960000'), '441614960000');
  assert.equal(e164Digits('441614960000'), '');
  assert.equal(e164Digits('+1234567890123456'), '');
});
''',
"faq": [
 ("Why sweep the warning level as well as the error level?",
  "Because several of the 132xx Dial attribute errors are logged at LogLevel=warning rather than error. A dashboard or a script filtered to errors alone will show a clean account while every leg in a campaign is being refused. Sweeping both levels and merging on the alert sid costs one extra paginated read."),
 ("The call shows as completed. How can the leg have failed?",
  "The parent call did complete. Twilio refused the destination, the <Dial> ended without connecting anything, and control returned to your TwiML, which carried on to the action URL. Nothing about the parent call is abnormal, which is why counting call status never finds this."),
 ("What is the difference between unsupported and invalid?",
  "Invalid means the number does not exist: an unassigned range, a country code that was never allocated, a lost digit. Unsupported means it exists and Twilio will not terminate on it, which covers premium rate, shared cost and special service allocations. Both raise 13224 and only the first is fixable by cleaning your data."),
 ("Why not normalise the number in the script before classifying it?",
  "Because the punctuation is the finding. A destination that only becomes E.164 after the audit tidies it is a destination the application should have tidied and did not, and a report that quietly cleans its input will tell you the list is fine while the calls keep failing."),
 ("Can the script fix the numbers it finds?",
  "It will not. It has a read-only key and the repair is not on Twilio's side anyway: the destination column in your own database is where the normalisation belongs, so every caller of that column gets it rather than the dial path alone."),
],
"related": [
 ("/twilio/dial-invalid-caller-id-13214/", "13214: the caller ID passed through from the inbound leg"),
 ("/twilio/outbound-call-failure-rate-spike/", "A rising share of outbound calls end in failed"),
 ("/twilio/sip-endpoint-not-registered-32009/", "32009: the SIP endpoint is not registered"),
],
"citations": [CITE_13224, CITE_TWIML_DIAL, CITE_LOOKUP, CITE_ALERT],
},

{
"slug": "amd-machine-answer-misrouting",
"title": "Answering machine detection is routing humans to voicemail",
"description": "answered_by comes back machine_start or unknown on calls a person picked up. The connect rate falls and every call still reads as completed.",
"h1": "answering machine detection is routing humans to voicemail",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio answered_by machine_start", "twilio amd unknown",
             "twilio machine detection tuning", "MachineDetection DetectMessageEnd",
             "twilio asyncamd"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Connect rates are down and nobody can say why. The calls go out, they are answered, they last a few seconds, and they end. Every one of them is <code>completed</code>. What happened is that a person said hello, Twilio decided they were an answering machine, and your flow did what you told it to do for machines: it started a voicemail drop at somebody who was standing there holding the phone.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and tally <code>answered_by</code> across the completed calls. With <code>MachineDetection=Enable</code> the values are <code>human</code>, <code>machine_start</code>, <code>fax</code> and <code>unknown</code>; with <code>DetectMessageEnd</code> you also get the <code>machine_end_*</code> family.</p>
<p>Two numbers decide it. An <code>unknown</code> share above a few percent means detection is timing out rather than deciding. A <code>machine_start</code> share well above the voicemail rate you would expect, <em>concentrated in calls of a few seconds</em>, is the misroute: that short duration is a human hanging up on a voicemail greeting aimed at them.</p>""",
"problem": """<p>Nothing here is an error, so nothing here is logged as one. Answering-machine detection is a judgement Twilio makes in the first seconds of audio and hands to you in a webhook parameter. Whatever your flow does with that judgement is your code running correctly on a wrong input. The call completes, it is billed, the Debugger is empty, and the only visible symptom is a business metric moving in the wrong direction.</p>
<p>Which means it is diagnosed as a list problem or a script problem, because those are the usual causes of a falling connect rate. It survives that investigation intact: the list is fine, the script is fine, and the detector in between is quietly reclassifying a slice of your live humans as machines every single day. The share is rarely large enough to be obvious and rarely small enough not to matter.</p>""",
"why": """<p><strong>Detection has a few seconds of audio and a hard deadline.</strong> It is listening for the shape of a greeting: how long the speech runs, whether it stops. A person who answers with a long "hello, this is Sam speaking, how can I help" produces the same shape as a recorded greeting, and a line with hold music or background noise produces something detection cannot parse at all.</p>
<p><strong><code>unknown</code> is a timeout, not a category.</strong> It does not mean Twilio decided the call was ambiguous. It means the deadline passed before a decision was reached, and your flow got a value it almost certainly has no branch for. Flows tend to treat <code>unknown</code> as machine, because the machine branch is the safe-looking one.</p>
<p><strong>The default mode answers early on purpose.</strong> <code>MachineDetection=Enable</code> is optimised to return as soon as it can, which is what you want for a dialler and is exactly what produces borderline calls. <code>DetectMessageEnd</code> waits for the greeting to finish, which is slower and far more certain, and it is a different value in a different field on the create request.</p>
<p><strong>The evidence is an aggregate, so no single call proves anything.</strong> Pull up one <code>machine_start</code> call and it looks entirely reasonable. Only the distribution across a few hundred calls, cut by duration, shows you that a quarter of your "machines" hung up after four seconds.</p>""",
"steps": [
 {"h": "Page the calls over a window you actually campaigned in",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>, which on this API is a path rather than an absolute URL. Pick a window with real volume in it; a distribution over forty calls is noise wearing a percentage sign.</p>"""},
 {"h": "Count only the calls detection actually graded",
  "body": """<p>A call with no <code>answered_by</code> never asked for detection, and a call whose <code>status</code> is not <code>completed</code> was never answered by anything. Both belong out of the denominator. Leaving them in is what produces the reassuring report: hundreds of calls, a tiny machine share, and a campaign that is still failing.</p>"""},
 {"h": "Split machine_start by duration",
  "body": """<p>This is the measurement that names the problem. A <code>machine_start</code> call lasting a few seconds is a human who heard a recording begin and hung up. Do not apply the same rule to <code>machine_end_beep</code> and its siblings: those come from <code>DetectMessageEnd</code>, where Twilio waited for the greeting to finish, so a short call there means something else.</p>"""},
 {"h": "Read unknown as a separate failure from machine_start",
  "body": """<p>They have different repairs. A high <code>unknown</code> share is a timing problem: raise <code>MachineDetectionTimeout</code> and <code>MachineDetectionSpeechThreshold</code>. A high <code>machine_start</code> share with short durations is a mode problem: <code>DetectMessageEnd</code>, or <code>AsyncAmd=true</code> so the call connects to a human first and reclassifies afterwards through <code>AsyncAmdStatusCallback</code>.</p>"""},
 {"h": "Change one parameter, re-run over a fresh window, compare",
  "body": """<p>Detection tuning is empirical and the only instrument is this distribution. Change <code>MachineDetection</code> or one threshold on the outbound create request, run the campaign, and tally the same window again. Keep the earlier numbers: a share that moved from 34% to 31% is not a fix, and without the previous run you will believe it was.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the change. The unknown share should be under a couple of percent and the short share of machine_start calls should collapse.</p>
<pre><code class="language-bash">python3 twilio_amd_classification_audit.py --days 3
# healthy  620 graded call(s): human 71.0%, machine 26.0%, unknown 1.3%</code></pre>""",
"code_intro": "One paginated GET over the calls and nothing else, with an API Key that has read access. Two pure functions carry the analysis: one puts a single call in a bucket, and one turns the tally of buckets into a verdict against thresholds you pass in. Separating them is what makes the thresholds arguable &mdash; they are defaults, not truths, and the only way to have that argument honestly is to be able to change the numbers and re-run without touching the bucketing.",
"py_file": "twilio_amd_classification_audit.py",
"py": '''"""Report how Twilio's answering machine detection is classifying your calls.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_amd_classification_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# DetectMessageEnd waits for the greeting to finish before deciding, so its
# verdicts arrive as this family rather than as machine_start.
MACHINE_END = ("machine_end_beep", "machine_end_silence", "machine_end_other")

GRADED = ("human", "machine", "machine-short", "unknown", "fax")


def seconds(value):
    """A call duration as an int. It arrives as a string and can be absent."""
    try:
        return int(str(value or "0").strip() or 0)
    except ValueError:
        return 0


def bucket(call, short_seconds=8):
    """Put one call in an answering-machine bucket. Pure, so the rules can be
    tested without a network.

    A machine_start call of a few seconds is the misroute this note is about: a
    person answered, detection called them a machine, and they hung up on the
    voicemail drop. The machine_end_* family is deliberately not split the same
    way, because there Twilio waited for the greeting to end and a short call
    means something else entirely.
    """
    if str(call.get("status") or "").strip().lower() != "completed":
        return "not-completed"

    answered = str(call.get("answered_by") or "").strip().lower()
    if not answered:
        return "no-amd"
    if answered in ("human", "fax", "unknown"):
        return answered
    if answered == "machine_start":
        return "machine-short" if seconds(call.get("duration")) <= short_seconds else "machine"
    if answered in MACHINE_END:
        return "machine"
    return "other"


def verdict(tally, min_calls=50, unknown_pct=3.0, machine_pct=40.0, short_pct=25.0):
    """Turn a tally of buckets into a verdict. Pure.

    The thresholds are arguments rather than constants because they are
    defaults, not truths: a debt collector's real voicemail rate is nothing like
    a delivery notification's. Returns (state, detail).
    """
    graded = sum(tally.get(k, 0) for k in GRADED)
    if graded == 0:
        return ("no-amd",
                "no call in this window carries answered_by, so machine "
                "detection was never requested and there is nothing to tune.")
    if graded < min_calls:
        return ("thin-sample",
                "only %d graded call(s), under the %d needed to read a "
                "distribution. Widen the window rather than trusting this."
                % (graded, min_calls))

    machines = tally.get("machine", 0) + tally.get("machine-short", 0)
    unknown_share = 100.0 * tally.get("unknown", 0) / graded
    machine_share = 100.0 * machines / graded
    short_share = (100.0 * tally.get("machine-short", 0) / machines) if machines else 0.0

    if unknown_share > unknown_pct:
        return ("detection-timing-out",
                "%.1f%% of %d graded call(s) came back unknown, over the %.1f%% "
                "threshold. unknown is a timeout, not a category: detection ran "
                "out of time and your flow branched on a value it has no case "
                "for." % (unknown_share, graded, unknown_pct))

    if machine_share > machine_pct and short_share > short_pct:
        return ("over-classifying",
                "%.1f%% of %d graded call(s) were called machines and %.1f%% of "
                "those lasted seconds. That short tail is people hanging up on a "
                "voicemail drop aimed at them."
                % (machine_share, graded, short_share))

    if machine_share > machine_pct:
        return ("machine-heavy",
                "%.1f%% of %d graded call(s) were machines, over the %.1f%% "
                "threshold, but only %.1f%% of them were short. This looks like "
                "a list that really does reach voicemail, not a detector fault."
                % (machine_share, graded, machine_pct, short_share))

    return ("healthy",
            "%d graded call(s): human %.1f%%, machine %.1f%%, unknown %.1f%%"
            % (graded, 100.0 * tally.get("human", 0) / graded,
               machine_share, unknown_share))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_calls(session, account, since, limit):
    """Page the Calls listing. next_page_uri here is a path, not a URL."""
    url = "%s/Accounts/%s/Calls.json" % (BASE, account)
    params = {"StartTime>=": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("calls", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7, help="window to tally")
    ap.add_argument("--max-calls", type=int, default=20000,
                    help="stop after this many calls")
    ap.add_argument("--short-seconds", type=int, default=8,
                    help="a machine_start call this short is a suspected misroute")
    ap.add_argument("--min-calls", type=int, default=50,
                    help="fewer graded calls than this is not a distribution")
    ap.add_argument("--unknown-pct", type=float, default=3.0,
                    help="unknown share above this is a detection timeout")
    ap.add_argument("--machine-pct", type=float, default=40.0,
                    help="machine share above this is worth explaining")
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
    calls = list_calls(session, account, since, args.max_calls)
    if not calls:
        log.info("no calls in the last %d day(s)", args.days)
        return 0

    tally = {}
    for c in calls:
        b = bucket(c, args.short_seconds)
        tally[b] = tally.get(b, 0) + 1

    for name in sorted(tally):
        log.info("%-14s %d", name, tally[name])

    state, detail = verdict(tally, args.min_calls, args.unknown_pct,
                            args.machine_pct)
    if state in ("healthy", "no-amd", "thin-sample"):
        log.info("%s  %s", state, detail)
        return 0

    log.warning("%s  %s", state, detail)
    log.warning("  repair: on the outbound create request set "
                "MachineDetection=DetectMessageEnd, or raise "
                "MachineDetectionTimeout and MachineDetectionSpeechThreshold")
    log.warning("  repair: or set AsyncAmd=true with AsyncAmdStatusCallback so "
                "the call connects first and is reclassified after")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-amd-classification-audit.mjs",
"js": '''/**
 * Report how Twilio's answering machine detection is classifying your calls.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// DetectMessageEnd waits for the greeting to finish, so its verdicts arrive as
// this family rather than as machine_start.
const MACHINE_END = ['machine_end_beep', 'machine_end_silence', 'machine_end_other'];

const GRADED = ['human', 'machine', 'machine-short', 'unknown', 'fax'];

/** A call duration as a number. It arrives as a string and can be absent. */
export function seconds(value) {
  const n = Number.parseInt(String(value ?? '0').trim(), 10);
  return Number.isFinite(n) ? n : 0;
}

/**
 * Put one call in an answering-machine bucket. Pure.
 *
 * A machine_start call of a few seconds is the misroute: a person answered,
 * detection called them a machine, and they hung up on the voicemail drop. The
 * machine_end_* family is not split the same way, because there Twilio waited
 * for the greeting to end and a short call means something else.
 */
export function bucket(call, shortSeconds = 8) {
  if (String(call.status ?? '').trim().toLowerCase() !== 'completed') return 'not-completed';

  const answered = String(call.answered_by ?? '').trim().toLowerCase();
  if (!answered) return 'no-amd';
  if (['human', 'fax', 'unknown'].includes(answered)) return answered;
  if (answered === 'machine_start') {
    return seconds(call.duration) <= shortSeconds ? 'machine-short' : 'machine';
  }
  if (MACHINE_END.includes(answered)) return 'machine';
  return 'other';
}

/**
 * Turn a tally of buckets into a verdict. Pure. The thresholds are arguments
 * rather than constants because they are defaults, not truths. Returns
 * [state, detail].
 */
export function verdict(tally, minCalls = 50, unknownPct = 3.0, machinePct = 40.0,
                        shortPct = 25.0) {
  const graded = GRADED.reduce((n, k) => n + (tally[k] ?? 0), 0);
  if (graded === 0) {
    return ['no-amd',
      'no call in this window carries answered_by, so machine detection was ' +
      'never requested and there is nothing to tune.'];
  }
  if (graded < minCalls) {
    return ['thin-sample',
      `only ${graded} graded call(s), under the ${minCalls} needed to read a ` +
      'distribution. Widen the window rather than trusting this.'];
  }

  const machines = (tally.machine ?? 0) + (tally['machine-short'] ?? 0);
  const unknownShare = (100 * (tally.unknown ?? 0)) / graded;
  const machineShare = (100 * machines) / graded;
  const shortShare = machines ? (100 * (tally['machine-short'] ?? 0)) / machines : 0;

  if (unknownShare > unknownPct) {
    return ['detection-timing-out',
      `${unknownShare.toFixed(1)}% of ${graded} graded call(s) came back ` +
      `unknown, over the ${unknownPct.toFixed(1)}% threshold. unknown is a ` +
      'timeout, not a category: detection ran out of time and your flow ' +
      'branched on a value it has no case for.'];
  }

  if (machineShare > machinePct && shortShare > shortPct) {
    return ['over-classifying',
      `${machineShare.toFixed(1)}% of ${graded} graded call(s) were called ` +
      `machines and ${shortShare.toFixed(1)}% of those lasted seconds. That ` +
      'short tail is people hanging up on a voicemail drop aimed at them.'];
  }

  if (machineShare > machinePct) {
    return ['machine-heavy',
      `${machineShare.toFixed(1)}% of ${graded} graded call(s) were machines, ` +
      `over the ${machinePct.toFixed(1)}% threshold, but only ` +
      `${shortShare.toFixed(1)}% of them were short. This looks like a list ` +
      'that really does reach voicemail, not a detector fault.'];
  }

  return ['healthy',
    `${graded} graded call(s): human ` +
    `${((100 * (tally.human ?? 0)) / graded).toFixed(1)}%, machine ` +
    `${machineShare.toFixed(1)}%, unknown ${unknownShare.toFixed(1)}%`];
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

export async function listCalls(auth, account, since, limit = 20000) {
  let url = `${BASE}/Accounts/${account}/Calls.json`;
  let params = { 'StartTime>=': since, PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.calls ?? []));
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
  const arg = (name, fallback) => {
    const i = process.argv.indexOf(name);
    return i === -1 ? fallback : Number(process.argv[i + 1]);
  };
  const days = arg('--days', 7);
  const shortSeconds = arg('--short-seconds', 8);

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const calls = await listCalls(auth, account, since);
  if (calls.length === 0) {
    console.log(`no calls in the last ${days} day(s)`);
    return;
  }

  const tally = {};
  for (const c of calls) {
    const b = bucket(c, shortSeconds);
    tally[b] = (tally[b] ?? 0) + 1;
  }
  for (const name of Object.keys(tally).sort()) {
    console.log(`${name.padEnd(14)} ${tally[name]}`);
  }

  const [state, detail] = verdict(tally, arg('--min-calls', 50),
                                  arg('--unknown-pct', 3.0), arg('--machine-pct', 40.0));
  if (['healthy', 'no-amd', 'thin-sample'].includes(state)) {
    console.log(`${state}  ${detail}`);
    return;
  }
  console.warn(`${state}  ${detail}`);
  console.warn('  repair: on the outbound create request set ' +
               'MachineDetection=DetectMessageEnd, or raise ' +
               'MachineDetectionTimeout and MachineDetectionSpeechThreshold');
  console.warn('  repair: or set AsyncAmd=true with AsyncAmdStatusCallback so ' +
               'the call connects first and is reclassified after');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main(), fail on the missing credentials and set an exit code
// that fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The bucketing tests are the ones that matter, because the denominator is where this analysis is usually lost. A call with no <code>answered_by</code> and a call that was never completed both have to stay out of the graded set, or a campaign with a thousand unanswered dials reports a comfortable two percent machine rate. The other pinned case is the asymmetry between <code>machine_start</code> and <code>machine_end_beep</code> at the same short duration: only the first is evidence.",
"test_py_file": "test_twilio_amd_classification_audit.py",
"test_py": '''from twilio_amd_classification_audit import bucket, verdict


def test_short_machine_start_is_the_misroute_bucket():
    assert bucket({"status": "completed", "answered_by": "machine_start",
                   "duration": "4"}) == "machine-short"


def test_machine_end_beep_is_not_split_by_duration():
    # DetectMessageEnd waited for the greeting, so a short call means something
    # else and must not land in the misroute bucket.
    assert bucket({"status": "completed", "answered_by": "machine_end_beep",
                   "duration": "4"}) == "machine"


def test_calls_without_detection_stay_out_of_the_denominator():
    assert bucket({"status": "completed", "duration": "90"}) == "no-amd"
    assert bucket({"status": "no-answer", "answered_by": "unknown"}) == "not-completed"


def test_unknown_share_over_the_threshold_reads_as_a_timeout():
    state, detail = verdict({"human": 400, "machine": 80, "unknown": 30})
    assert state == "detection-timing-out"
    assert "timeout, not a category" in detail


def test_machine_heavy_with_a_short_tail_is_over_classifying():
    state, detail = verdict({"human": 100, "machine": 60, "machine-short": 40})
    assert state == "over-classifying"
    assert "hanging up" in detail


def test_machine_heavy_without_a_short_tail_is_a_list_not_a_detector():
    state, _ = verdict({"human": 100, "machine": 98, "machine-short": 2})
    assert state == "machine-heavy"


def test_thin_sample_is_reported_rather_than_scored():
    assert verdict({"human": 10, "machine": 4})[0] == "thin-sample"


def test_no_graded_calls_means_detection_was_never_asked_for():
    assert verdict({"no-amd": 900, "not-completed": 100})[0] == "no-amd"
''',
"test_js_file": "twilio-amd-classification-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bucket, verdict } from './twilio-amd-classification-audit.mjs';

test('short machine_start is the misroute bucket', () => {
  assert.equal(
    bucket({ status: 'completed', answered_by: 'machine_start', duration: '4' }),
    'machine-short');
});

test('machine_end_beep is not split by duration', () => {
  assert.equal(
    bucket({ status: 'completed', answered_by: 'machine_end_beep', duration: '4' }),
    'machine');
});

test('calls without detection stay out of the denominator', () => {
  assert.equal(bucket({ status: 'completed', duration: '90' }), 'no-amd');
  assert.equal(bucket({ status: 'no-answer', answered_by: 'unknown' }), 'not-completed');
});

test('unknown share over the threshold reads as a timeout', () => {
  const [state, detail] = verdict({ human: 400, machine: 80, unknown: 30 });
  assert.equal(state, 'detection-timing-out');
  assert.match(detail, /timeout, not a category/);
});

test('machine heavy with a short tail is over classifying', () => {
  const [state, detail] = verdict({ human: 100, machine: 60, 'machine-short': 40 });
  assert.equal(state, 'over-classifying');
  assert.match(detail, /hanging up/);
});

test('machine heavy without a short tail is a list not a detector', () => {
  assert.equal(verdict({ human: 100, machine: 98, 'machine-short': 2 })[0],
               'machine-heavy');
});

test('thin sample is reported rather than scored', () => {
  assert.equal(verdict({ human: 10, machine: 4 })[0], 'thin-sample');
});

test('no graded calls means detection was never asked for', () => {
  assert.equal(verdict({ 'no-amd': 900, 'not-completed': 100 })[0], 'no-amd');
});
''',
"faq": [
 ("What does answered_by unknown actually mean?",
  "That detection did not reach a decision before its deadline. It is a timeout rather than a third category, which matters because flows written against human and machine tend to fall through to the machine branch on unknown. Raising MachineDetectionTimeout and MachineDetectionSpeechThreshold is the lever for it."),
 ("Why treat machine_start differently from machine_end_beep?",
  "They come from different modes. machine_start is Enable deciding as early as it can, which is where borderline humans get miscalled. The machine_end_* family comes from DetectMessageEnd, which waits for the greeting to finish, so a short call there is not the same signal and folding them together destroys the measurement."),
 ("Is there an error code or a Debugger alert for this?",
  "No. Detection returning the wrong answer is not a failure of anything: the call completed, it was billed, and your flow branched correctly on the value it was given. This is only visible as a distribution, which is why the script counts rather than filters."),
 ("Why does the denominator exclude calls with no answered_by?",
  "Because those calls never requested detection, so they say nothing about how it is performing. Leaving them in dilutes every share toward zero and produces a report that looks healthy on a campaign that is failing. The same goes for calls that were never completed."),
 ("Should I use AsyncAmd instead of tuning the thresholds?",
  "It is a different trade rather than a better one. AsyncAmd=true connects the call immediately and delivers the classification afterwards through AsyncAmdStatusCallback, so a human is never held waiting for a decision. You pay for it with a flow that has to handle being told, mid-call, that it is talking to a machine."),
],
"related": [
 ("/twilio/dial-number-unsupported-or-invalid-13224/", "13224: the Dial destination Twilio refuses"),
 ("/twilio/outbound-call-failure-rate-spike/", "A rising share of outbound calls end in failed"),
 ("/twilio/status-callback-webhook-failing-11200/", "Status callbacks failing with 11200"),
],
"citations": [CITE_AMD, CITE_CALL, CITE_MAKE_CALLS, CITE_KEYS],
},

{
"slug": "recording-absent-with-error-code",
"title": "A recording row says absent and there is no media behind it",
"description": "The Recording resource exists, status is absent, error_code is set and the media URL 404s. The call completed normally, so nothing else looks wrong.",
"h1": "a recording row says absent and there is no media behind it",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio recording status absent", "twilio recording error_code",
             "twilio recording missing media", "recordingStatusCallback",
             "twilio recording source dialverb"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Someone in compliance asks for the call from the fourteenth. The recording is in the list, with a SID, a date and a call SID beside it. The media URL returns 404. Its <code>status</code> is <code>absent</code>, its <code>error_code</code> is populated, and it has been sitting there like that for six weeks because nothing in the system treats a row that exists as a recording that does not.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Recordings.json?DateCreated&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and keep every row whose <code>status</code> is <code>absent</code>. On those rows <code>error_code</code> is populated, which it is not on a healthy recording.</p>
<p>Then read <code>source</code> on each one. It tells you which mechanism asked for the recording &mdash; <code>DialVerb</code>, <code>RecordVerb</code>, <code>Conference</code>, <code>OutboundAPI</code>, <code>StartCallRecordingAPI</code>, <code>Trunking</code> &mdash; and therefore where the recording status callback that would have alerted you in real time is supposed to be attached. Cross-reference each <code>call_sid</code> against a sweep of <code>GET https://monitor.twilio.com/v1/Alerts</code> over the same window, at both log levels.</p>""",
"problem": """<p>Twilio creates the Recording resource when recording is requested, not when media lands. So the row is real, immediate, and complete enough to satisfy anything that checks for existence: your database stores the SID, your UI renders a player, your retention job counts it. If the media is never produced, the row's <code>status</code> becomes <code>absent</code> and everything downstream carries on referencing a recording that is not there.</p>
<p>The call itself is untouched by this. It rang, it connected, it lasted eleven minutes, it completed. Nothing in the call logs, the call events or the connect metrics is different from the calls whose audio you do have. That is the whole difficulty: the failure is in a sibling resource that only reveals itself if you go and read its <code>status</code> field, and nobody reads a status field on a resource they have already stored the SID of.</p>""",
"why": """<p><strong>Existence and availability are different questions and only one gets asked.</strong> The recording SID comes back, gets persisted, and is treated as a fact from then on. Re-reading the resource later to find out whether it ever became audio is an extra call that no ordinary code path has a reason to make.</p>
<p><strong><code>error_code</code> is only populated on the absent rows.</strong> Which is correct and is also why it is easy to miss: a scan that reads <code>error_code</code> across all recordings sees it empty everywhere and concludes the field is unused. It only means anything on the subset you have to filter for first.</p>
<p><strong>The discovery is always months late and always external.</strong> Recordings are written for a purpose that is not today's: a dispute, an audit, a quality review. Nobody plays yesterday's recordings, so the gap is found by the one party who cannot be told to check again next week.</p>
<p><strong>The callback that would have told you is optional and per-verb.</strong> A recording status callback is an attribute on the <code>&lt;Dial&gt;</code> or <code>&lt;Record&gt;</code> verb, or a parameter on the create request, depending on which mechanism started the recording. It is not a single account-level setting, so getting it onto every path is four or five separate small changes and one of them is always missed.</p>""",
"steps": [
 {"h": "Page the recordings over the window you care about",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Recordings.json?DateCreated&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>, which on this API is a path rather than an absolute URL. Pick the window from your retention policy, not from the incident: the question is how many of the recordings you believe you hold are real.</p>"""},
 {"h": "Filter on status, then read error_code",
  "body": """<p><code>absent</code> is the finding. <code>error_code</code> is populated on those rows and on essentially none of the others, so read it after filtering rather than scanning for it &mdash; a scan across everything makes the field look unused and the problem look absent in the other sense.</p>"""},
 {"h": "Group by source to find which mechanism is failing",
  "body": """<p><code>source</code> names what asked for the recording. A gap concentrated in <code>DialVerb</code> is a different investigation from one spread evenly across <code>RecordVerb</code>, <code>Conference</code> and <code>OutboundAPI</code>: the first points at one TwiML path, the second at something account-wide. This grouping is what turns a list of missing files into one thing to fix.</p>"""},
 {"h": "Treat a completed recording of zero duration as a second finding",
  "body": """<p>A row with <code>status</code> <code>completed</code> and <code>duration</code> of <code>0</code> is media that exists and contains nothing. It will play, it will pass any check for presence, and it holds no audio. It is not the same failure as <code>absent</code> and it belongs in the same report, because the person asking for the call cannot use either.</p>"""},
 {"h": "Cross-reference the call SIDs, then wire up the callback",
  "body": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts</code> at both <code>LogLevel=error</code> and <code>LogLevel=warning</code> over the same window and match on <code>resource_sid</code>: an alert against the same call tells you what else was going wrong at the time. Then add <code>recordingStatusCallback</code> to the verb, or <code>RecordingStatusCallback</code> to the create request, so the next one alerts on the day rather than at the audit.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the callback is in place. Absent rows should be zero, and any that do appear should now also be in your own alerting.</p>
<pre><code class="language-bash">python3 twilio_absent_recordings_audit.py --days 30
# 1420 recording(s), 0 absent, 0 empty</code></pre>""",
"code_intro": "One paginated GET over the recordings, plus two alert sweeps when you ask for the cross-reference. An API Key with read access is enough. The classification is a pure function over a single Recording, paired with a small table that maps <code>source</code> to where the status callback for that mechanism is configured &mdash; because the finding is only half useful without the sentence telling you which of five places to put the callback that would have caught it.",
"py_file": "twilio_absent_recordings_audit.py",
"py": '''"""Report Twilio recordings whose media was never produced.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_absent_recordings_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

# Where the status callback lives for each mechanism that can start a recording.
# The finding is only half useful without this sentence: knowing a recording is
# missing does not tell you which of five places the callback belongs in.
SOURCES = {
    "DialVerb": "recordingStatusCallback is an attribute on the Dial verb",
    "RecordVerb": "recordingStatusCallback is an attribute on the Record verb",
    "Conference": "recordingStatusCallback is an attribute on the Conference noun",
    "OutboundAPI": "RecordingStatusCallback is a parameter on the call create request",
    "StartCallRecordingAPI":
        "RecordingStatusCallback is a parameter on the recording create request",
    "StartConferenceRecordingAPI":
        "RecordingStatusCallback is a parameter on the recording create request",
    "Trunking": "recording is configured on the trunk itself, so there is no "
                "per-call attribute to add here",
}


def source_meaning(source):
    """Where the recording status callback is configured for this source. Pure."""
    key = str(source or "").strip()
    return SOURCES.get(
        key, "the source is not one this script recognises, so check how the "
             "recording was started before deciding where the callback goes")


def seconds(value):
    """A recording duration as an int. It arrives as a string and can be absent."""
    try:
        return int(str(value or "0").strip() or 0)
    except ValueError:
        return 0


def verdict(recording):
    """Classify one Recording. Pure, so the rules can be tested without a
    network.

    Returns (state, detail). The two states worth acting on are absent, where no
    media was ever produced, and empty, where media exists and holds no audio.
    Both fail the person who asks for the call, and only the first has an
    error_code to explain itself.
    """
    status = str(recording.get("status") or "").strip().lower()
    source = str(recording.get("source") or "").strip()
    code = str(recording.get("error_code") or "").strip()

    if status == "absent":
        why = ("error_code %s" % code) if code else \\
            "no error_code, which is unusual on an absent row"
        return ("absent",
                "%s asked for this recording and no media was produced (%s). "
                "The call itself completed normally, so nothing else about it "
                "looks wrong. %s."
                % (source or "An unnamed source", why, source_meaning(source)))

    if status in ("processing", "in-progress"):
        return ("in-flight",
                "status is %s: the media is still being written, so this is a "
                "verdict about a moment rather than a fault." % status)

    if status == "deleted":
        return ("deleted",
                "the media has been deleted. The row survives deletion, so a "
                "check that only looks for the recording's existence will keep "
                "reporting this call as recorded.")

    if status == "completed":
        if seconds(recording.get("duration")) <= 0:
            return ("empty",
                    "completed with a duration of zero: the media exists, it "
                    "will play, and there is no audio in it. It passes every "
                    "check for presence and fails the only one that matters.")
        return ("stored", "completed with %ds of media."
                % seconds(recording.get("duration")))

    return ("other", "status is %s, which this script has no rule for."
            % (status or "empty"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_recordings(session, account, since, limit):
    """Page the Recordings listing. next_page_uri here is a path, not a URL."""
    url = "%s/Accounts/%s/Recordings.json" % (BASE, account)
    params = {"DateCreated>=": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("recordings", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def list_alerts(session, since, limit, log_level):
    """Page the Monitor alerts at one log level. next_page_url is absolute."""
    url = MONITOR + "/Alerts"
    params = {"LogLevel": log_level, "StartDate": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def alerts_by_call(session, since, limit):
    """Alert error codes keyed by the call sid they were raised against.

    Both log levels, because several voice failures are logged at warning and an
    error-only sweep will report that nothing else was wrong with these calls.
    """
    out = {}
    for level in ("error", "warning"):
        for a in list_alerts(session, since, limit, level):
            sid = str(a.get("resource_sid") or "")
            if sid.startswith("CA"):
                out.setdefault(sid, set()).add(str(a.get("error_code") or "?"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30, help="window to audit")
    ap.add_argument("--max-recordings", type=int, default=20000,
                    help="stop after this many recordings")
    ap.add_argument("--with-alerts", action="store_true",
                    help="also sweep Alerts and match on the call sid")
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
    recordings = list_recordings(session, account, since, args.max_recordings)
    if not recordings:
        log.info("no recordings in the last %d day(s)", args.days)
        return 0

    alerts = {}
    if args.with_alerts:
        # Alerts are retained 30 days, so a longer recording window is only
        # partially covered by this cross-reference.
        alerts = alerts_by_call(session, since, 10000)

    absent = 0
    empty = 0
    by_source = {}
    for rec in recordings:
        state, detail = verdict(rec)
        if state not in ("absent", "empty"):
            continue
        if state == "absent":
            absent += 1
            src = str(rec.get("source") or "unknown")
            by_source[src] = by_source.get(src, 0) + 1
        else:
            empty += 1
        log.warning("%-9s %s  %s", state, rec.get("sid"), detail)
        call_sid = str(rec.get("call_sid") or "")
        if call_sid in alerts:
            log.warning("  same call raised alert(s): %s",
                        ", ".join(sorted(alerts[call_sid])))

    log.info("%d recording(s), %d absent, %d empty",
             len(recordings), absent, empty)
    if not (absent or empty):
        return 0
    if by_source:
        log.warning("absent by source: %s",
                    ", ".join("%s=%d" % kv for kv in sorted(by_source.items())))
    log.warning("  repair: attach a recording status callback where the "
                "recording is started, so the next failure alerts on the day "
                "instead of at the audit")
    log.warning("  repair: reconcile your own recording table against status, "
                "not against the presence of a recording sid")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-absent-recordings-audit.mjs",
"js": '''/**
 * Report Twilio recordings whose media was never produced.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

// Where the status callback lives for each mechanism that can start a
// recording. Knowing a recording is missing does not tell you which of five
// places the callback belongs in.
const SOURCES = {
  DialVerb: 'recordingStatusCallback is an attribute on the Dial verb',
  RecordVerb: 'recordingStatusCallback is an attribute on the Record verb',
  Conference: 'recordingStatusCallback is an attribute on the Conference noun',
  OutboundAPI: 'RecordingStatusCallback is a parameter on the call create request',
  StartCallRecordingAPI:
    'RecordingStatusCallback is a parameter on the recording create request',
  StartConferenceRecordingAPI:
    'RecordingStatusCallback is a parameter on the recording create request',
  Trunking: 'recording is configured on the trunk itself, so there is no ' +
            'per-call attribute to add here',
};

/** Where the recording status callback is configured for this source. Pure. */
export function sourceMeaning(source) {
  const key = String(source ?? '').trim();
  return SOURCES[key] ??
    'the source is not one this script recognises, so check how the recording ' +
    'was started before deciding where the callback goes';
}

/** A recording duration as a number. It arrives as a string. */
export function seconds(value) {
  const n = Number.parseInt(String(value ?? '0').trim(), 10);
  return Number.isFinite(n) ? n : 0;
}

/**
 * Classify one Recording. Pure. Returns [state, detail]. The two states worth
 * acting on are absent, where no media was ever produced, and empty, where
 * media exists and holds no audio.
 */
export function verdict(recording) {
  const status = String(recording.status ?? '').trim().toLowerCase();
  const source = String(recording.source ?? '').trim();
  const code = String(recording.error_code ?? '').trim();

  if (status === 'absent') {
    const why = code ? `error_code ${code}`
                     : 'no error_code, which is unusual on an absent row';
    return ['absent',
      `${source || 'An unnamed source'} asked for this recording and no media ` +
      `was produced (${why}). The call itself completed normally, so nothing ` +
      `else about it looks wrong. ${sourceMeaning(source)}.`];
  }

  if (status === 'processing' || status === 'in-progress') {
    return ['in-flight',
      `status is ${status}: the media is still being written, so this is a ` +
      'verdict about a moment rather than a fault.'];
  }

  if (status === 'deleted') {
    return ['deleted',
      'the media has been deleted. The row survives deletion, so a check that ' +
      'only looks for the recording\\'s existence will keep reporting this call ' +
      'as recorded.'];
  }

  if (status === 'completed') {
    if (seconds(recording.duration) <= 0) {
      return ['empty',
        'completed with a duration of zero: the media exists, it will play, ' +
        'and there is no audio in it. It passes every check for presence and ' +
        'fails the only one that matters.'];
    }
    return ['stored', `completed with ${seconds(recording.duration)}s of media.`];
  }

  return ['other', `status is ${status || 'empty'}, which this script has no rule for.`];
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

export async function listRecordings(auth, account, since, limit = 20000) {
  let url = `${BASE}/Accounts/${account}/Recordings.json`;
  let params = { 'DateCreated>=': since, PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.recordings ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function listAlerts(auth, since, limit, logLevel) {
  let url = `${MONITOR}/Alerts`;
  let params = { LogLevel: logLevel, StartDate: since, PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.alerts ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Alert error codes keyed by call sid, swept at both log levels. */
export async function alertsByCall(auth, since, limit = 10000) {
  const out = new Map();
  for (const level of ['error', 'warning']) {
    for (const a of await listAlerts(auth, since, limit, level)) {
      const sid = String(a.resource_sid ?? '');
      if (!sid.startsWith('CA')) continue;
      if (!out.has(sid)) out.set(sid, new Set());
      out.get(sid).add(String(a.error_code ?? '?'));
    }
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
  const i = process.argv.indexOf('--days');
  const days = i === -1 ? 30 : Number(process.argv[i + 1]);

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const recordings = await listRecordings(auth, account, since);
  if (recordings.length === 0) {
    console.log(`no recordings in the last ${days} day(s)`);
    return;
  }

  // Alerts are retained 30 days, so a longer recording window is only partially
  // covered by this cross-reference.
  const alerts = process.argv.includes('--with-alerts')
    ? await alertsByCall(auth, since)
    : new Map();

  let absent = 0;
  let empty = 0;
  const bySource = new Map();
  for (const rec of recordings) {
    const [state, detail] = verdict(rec);
    if (state !== 'absent' && state !== 'empty') continue;
    if (state === 'absent') {
      absent += 1;
      const src = String(rec.source ?? 'unknown');
      bySource.set(src, (bySource.get(src) ?? 0) + 1);
    } else {
      empty += 1;
    }
    console.warn(`${state.padEnd(9)} ${rec.sid}  ${detail}`);
    const callSid = String(rec.call_sid ?? '');
    if (alerts.has(callSid)) {
      console.warn(`  same call raised alert(s): ${[...alerts.get(callSid)].sort().join(', ')}`);
    }
  }

  console.log(`${recordings.length} recording(s), ${absent} absent, ${empty} empty`);
  if (!absent && !empty) return;
  if (bySource.size) {
    console.warn('absent by source: ' +
      [...bySource.entries()].sort().map(([k, v]) => `${k}=${v}`).join(', '));
  }
  console.warn('  repair: attach a recording status callback where the recording ' +
               'is started, so the next failure alerts on the day instead of at ' +
               'the audit');
  console.warn('  repair: reconcile your own recording table against status, not ' +
               'against the presence of a recording sid');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main(), fail on the missing credentials and set an exit code
// that fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that earns its place is <code>completed</code> with a duration of zero. It is the one a reasonable implementation gets wrong, because <code>completed</code> reads as success and the row has media behind it &mdash; media containing no audio. The others pin the boundary between a recording that is still being written and one that never will be, which is the difference between re-running the audit in a minute and opening a ticket.",
"test_py_file": "test_twilio_absent_recordings_audit.py",
"test_py": '''from twilio_absent_recordings_audit import source_meaning, verdict


def test_absent_row_names_the_error_code_and_the_source():
    state, detail = verdict({"status": "absent", "error_code": 12400,
                             "source": "DialVerb"})
    assert state == "absent"
    assert "error_code 12400" in detail
    assert "Dial verb" in detail


def test_absent_row_without_an_error_code_says_so():
    state, detail = verdict({"status": "absent", "source": "RecordVerb"})
    assert state == "absent"
    assert "unusual" in detail


def test_completed_with_zero_duration_is_its_own_finding():
    state, detail = verdict({"status": "completed", "duration": "0"})
    assert state == "empty"
    assert "no audio" in detail


def test_completed_with_media_is_stored():
    assert verdict({"status": "completed", "duration": "671"})[0] == "stored"


def test_in_progress_is_a_moment_not_a_fault():
    assert verdict({"status": "processing"})[0] == "in-flight"


def test_deleted_row_survives_the_media():
    state, detail = verdict({"status": "deleted"})
    assert state == "deleted"
    assert "recording sid" not in detail


def test_trunking_source_has_nowhere_to_put_a_per_call_callback():
    assert "trunk itself" in source_meaning("Trunking")


def test_unrecognised_source_does_not_invent_a_place_for_the_callback():
    assert "not one this script recognises" in source_meaning("SomethingNew")
''',
"test_js_file": "twilio-absent-recordings-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sourceMeaning, verdict } from './twilio-absent-recordings-audit.mjs';

test('absent row names the error code and the source', () => {
  const [state, detail] = verdict({ status: 'absent', error_code: 12400,
                                    source: 'DialVerb' });
  assert.equal(state, 'absent');
  assert.match(detail, /error_code 12400/);
  assert.match(detail, /Dial verb/);
});

test('absent row without an error code says so', () => {
  const [state, detail] = verdict({ status: 'absent', source: 'RecordVerb' });
  assert.equal(state, 'absent');
  assert.match(detail, /unusual/);
});

test('completed with zero duration is its own finding', () => {
  const [state, detail] = verdict({ status: 'completed', duration: '0' });
  assert.equal(state, 'empty');
  assert.match(detail, /no audio/);
});

test('completed with media is stored', () => {
  assert.equal(verdict({ status: 'completed', duration: '671' })[0], 'stored');
});

test('in progress is a moment not a fault', () => {
  assert.equal(verdict({ status: 'processing' })[0], 'in-flight');
});

test('deleted row survives the media', () => {
  assert.equal(verdict({ status: 'deleted' })[0], 'deleted');
});

test('trunking source has nowhere to put a per call callback', () => {
  assert.match(sourceMeaning('Trunking'), /trunk itself/);
});

test('unrecognised source does not invent a place for the callback', () => {
  assert.match(sourceMeaning('SomethingNew'), /not one this script recognises/);
});
''',
"faq": [
 ("Does an absent recording mean the call was not recorded?",
  "It means no media was produced or the media was lost. Recording was requested, which is why the resource exists at all, and the audio you would have played is not there. The call itself is unaffected and completed normally, which is exactly why nothing else in the system flags it."),
 ("Why is error_code empty on all my other recordings?",
  "Because it is populated only when status is absent. A scan that reads error_code across every recording sees it blank everywhere and concludes the field is unused. Filter on status first, then read the code on what is left."),
 ("What does source tell me that status does not?",
  "Which mechanism asked for the recording, and therefore where the status callback belongs. A gap concentrated in DialVerb is one TwiML path to fix; one spread across RecordVerb, Conference and OutboundAPI is something account-wide. It turns a list of missing files into a single thing to change."),
 ("Is a completed recording with zero duration the same problem?",
  "No, and that is why it is a separate state. Absent means no media. Zero duration means media that exists, plays, and contains nothing. Both fail the person who asked for the call, and only the first carries an error code to explain itself, so a check written against error_code alone misses the second entirely."),
 ("Can the script delete or re-request the broken rows?",
  "It will not. It holds a read-only key, and there is nothing to re-request anyway: the audio was never produced and cannot be recovered after the fact. What it prints is the change that stops the next one going unnoticed for six weeks."),
],
"related": [
 ("/twilio/recordings-not-encrypted/", "Recordings stored without encryption at rest"),
 ("/twilio/unreleased-recordings-storage/", "Recordings billed for storage until something deletes them"),
 ("/twilio/status-callback-webhook-failing-11200/", "Status callbacks failing with 11200"),
],
"citations": [CITE_RECORDING, CITE_TWIML_RECORD, CITE_TWIML_DIAL, CITE_ALERT],
},

{
"slug": "voice-dialing-permissions-blocked",
"title": "21215: dialing permissions block a country you sell into",
"description": "Calls to one country fail with 21215 or 13227 while the identical code works at home. Subaccounts fail on their own when inheritance is off.",
"h1": "21215: dialing permissions block a country you sell into",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 21215", "twilio 13227", "voice dialing permissions",
             "twilio account not authorized to call this number",
             "dialing_permissions_inheritance"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The integration has worked for a year. A customer in a new country signs up, the first call to them fails with <code>21215 Account not authorized to call this number</code>, and every explanation you can think of is about the number. It is not about the number. Your account has an allowlist of countries it may dial, it was built from where you signed up, and nobody has looked at it since.",
"short_answer": """<p>Read <code>GET https://voice.twilio.com/v1/DialingPermissions/Countries</code>. Each entry carries <code>iso_code</code>, <code>country_codes</code> and three independent switches: <code>low_risk_numbers_enabled</code>, <code>high_risk_special_numbers_enabled</code> and <code>high_risk_tollfraud_numbers_enabled</code>. A country with <code>low_risk_numbers_enabled</code> <code>false</code> refuses ordinary calls, and you can filter straight to them with <code>?LowRiskNumbersEnabled=false</code>.</p>
<p>Then read <code>GET https://voice.twilio.com/v1/Settings</code> for <code>dialing_permissions_inheritance</code>. When it is <code>false</code>, subaccounts do not inherit the parent's permissions &mdash; each carries its own home-country-only default, which is why an integration breaks the day traffic moves onto a subaccount and nothing about the code changed. Confirm live damage by sweeping <code>GET https://monitor.twilio.com/v1/Alerts</code> at both log levels for <code>21215</code> and <code>13227</code>.</p>""",
"problem": """<p>The error text points at the number, so that is where everyone looks. The number gets re-checked, re-formatted, put through Lookup, dialled from a mobile to prove it rings. All of that succeeds, and the call from Twilio keeps failing, because the destination was never the subject: the account is not authorised, and the authorisation is a per-country allowlist that has nothing to do with the digits.</p>
<p>The subaccount case is worse, because it presents as a regression with no deploy behind it. The same code, the same numbers, the same TwiML, moved onto a subaccount for isolation or per-tenant billing, and suddenly half the destinations are refused. Nothing was changed except which account SID the credential belongs to, and that is the one variable nobody thinks to hold up against a permissions list.</p>""",
"why": """<p><strong>The allowlist is built from where you signed up.</strong> New projects are enabled for the home country inferred at signup and, in practice, very little else. That default is invisible while you sell domestically and becomes an outage the day you do not.</p>
<p><strong>Three switches per country, and they move independently.</strong> A country can be enabled for low-risk numbers while a specific high-risk prefix inside it stays blocked. So "we enabled that country" and "that call is allowed" are different claims, and the first is the one people make.</p>
<p><strong>Inheritance is a single account-wide flag that reads as a default.</strong> <code>dialing_permissions_inheritance</code> on <code>/v1/Settings</code> decides whether subaccounts get the parent's permissions at all. When it is off, every subaccount you create carries its own minimal set, and creating subaccounts is exactly what a growing integration does.</p>
<p><strong>The two error codes come from different places and get triaged separately.</strong> <code>21215</code> is the REST-initiated rejection and <code>13227</code> is the TwiML <code>&lt;Dial&gt;</code> one. Same cause, same fix, two different tickets, and often two different people who never compare notes.</p>""",
"steps": [
 {"h": "Read the whole countries listing, not the one you suspect",
  "body": """<p><code>GET https://voice.twilio.com/v1/DialingPermissions/Countries</code>, following <code>meta.next_page_url</code>. The single-country fetch <code>GET .../Countries/{IsoCode}</code> answers a question you already had; the listing answers the one you did not, which is which other countries are also closed and will fail the next time somebody sells into them.</p>"""},
 {"h": "Sweep both log levels for 21215 and 13227",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error</code> and the same at <code>LogLevel=warning</code>, merged on <code>sid</code>. Keep both codes: the REST rejection and the <code>&lt;Dial&gt;</code> rejection are the same permission refusing two different callers, and a report that covers one of them will convince somebody the other is a separate problem.</p>"""},
 {"h": "Join destinations back to countries by dialling prefix, longest first",
  "body": """<p><code>country_codes</code> gives the dialling prefixes per country, so a destination resolves by longest-prefix match. Expect ties: every NANP country shares <code>1</code>, so a match on <code>1</code> is a group of twenty-odd countries rather than one. Report the group honestly instead of picking the first member, which is how a check confidently blames Canada for traffic to the United States.</p>"""},
 {"h": "Separate a country that is blocked from a country that is merely off",
  "body": """<p>Most disabled countries are disabled correctly and you will never call them. The finding is the intersection of disabled and attempted &mdash; a country with <code>low_risk_numbers_enabled</code> <code>false</code> that has calls or alerts against it. Everything else is context, and reporting it as a problem is how a hundred-line audit gets ignored.</p>"""},
 {"h": "Check inheritance before you change anything per country",
  "body": """<p><code>GET https://voice.twilio.com/v1/Settings</code>. If <code>dialing_permissions_inheritance</code> is <code>false</code> and you have subaccounts, enabling countries on the parent fixes nothing for them. The repair is <code>POST https://voice.twilio.com/v1/Settings</code> with <code>DialingPermissionsInheritance=true</code>, then <code>POST .../DialingPermissions/BulkCountryUpdates</code> with an <code>UpdateRequest</code> array for the countries you actually serve.</p>"""},
],
"verify": """<p>Re-run over a fresh window. No served country should report as blocking, and inheritance should be on if you run subaccounts.</p>
<pre><code class="language-bash">python3 twilio_dialing_permissions_audit.py --days 7
# 0 blocked destination(s) with traffic; inheritance on across 6 subaccount(s)</code></pre>""",
"code_intro": "Three reads: the countries listing, the settings resource, and an alert sweep at both log levels with one cached call fetch per failing call. All GETs, all fine with a read-access API Key. Three pure functions do the work &mdash; one turns the listing into a prefix index, one resolves a destination to the countries that could own it, and one decides whether a disabled country is an outage or just a country you do not call. This note is the opposite half of a pair: the other one reads the same listing looking for permissions that are too open.",
"py_file": "twilio_dialing_permissions_audit.py",
"py": '''"""Report Twilio voice dialing permissions that are blocking real traffic.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_dialing_permissions_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"
VOICE = "https://voice.twilio.com/v1"

# The REST rejection and the TwiML Dial rejection. Same permission, two callers.
BLOCKED_CODES = ("21215", "13227")


def prefix_index(countries):
    """Map every dialling prefix in the countries listing to its ISO codes.

    Pure. The value is a list rather than a single code because prefixes are
    shared: every North American Numbering Plan country answers to 1.
    """
    index = {}
    for c in countries or []:
        iso = str(c.get("iso_code") or "").strip().upper()
        for code in c.get("country_codes") or []:
            digits = str(code or "").strip().lstrip("+")
            if iso and digits.isdigit():
                index.setdefault(digits, set()).add(iso)
    return {k: sorted(v) for k, v in index.items()}


def countries_for(to, index):
    """The ISO codes a destination could belong to, longest prefix first.

    Returns a list, and the list is often longer than one. Picking its first
    member would let this check blame Canada for traffic to the United States,
    so the caller is made to see the ambiguity rather than being handed a guess.
    """
    digits = str(to or "").strip().lstrip("+")
    if not digits.isdigit():
        return []
    for length in range(min(4, len(digits)), 0, -1):
        hit = index.get(digits[:length])
        if hit:
            return list(hit)
    return []


def verdict(country, attempts=0, blocked=0):
    """Decide what one country's permissions are doing to you. Pure.

    attempts is calls seen to that country in the window; blocked is the count
    of 21215/13227 alerts resolved to it. Returns (state, detail).
    """
    iso = str(country.get("iso_code") or "??").strip().upper()
    if country.get("low_risk_numbers_enabled"):
        return ("open",
                "%s is enabled for low risk numbers, so ordinary calls are "
                "permitted. The two high risk switches are separate and are the "
                "subject of the companion check." % iso)

    if blocked:
        return ("blocking-live-traffic",
                "%s has low_risk_numbers_enabled false and %d call(s) were "
                "refused with 21215 or 13227 in this window. This is an outage "
                "in a country you are selling into." % (iso, blocked))

    if attempts:
        return ("blocking-attempted",
                "%s has low_risk_numbers_enabled false and %d call(s) were "
                "placed toward it. No refusal alert landed in this window, so "
                "check the window before concluding they got through."
                % (iso, attempts))

    return ("closed-unused",
            "%s is disabled and nothing was dialled toward it. Almost every "
            "account looks like this for almost every country; it is context, "
            "not a finding." % iso)


def settings_verdict(settings, subaccounts=0):
    """Decide whether subaccounts get the parent's permissions at all. Pure.

    Returns (state, detail). This is the check that explains a regression with
    no deploy behind it: the same code on a subaccount, refused.
    """
    if settings.get("dialing_permissions_inheritance"):
        return ("inherited",
                "dialing_permissions_inheritance is true, so subaccounts use "
                "the parent's country permissions.")
    if subaccounts:
        return ("not-inherited",
                "dialing_permissions_inheritance is false and this account has "
                "%d subaccount(s). Each one carries its own home-country-only "
                "default, so enabling a country here does nothing for them."
                % subaccounts)
    return ("not-inherited-no-subaccounts",
            "dialing_permissions_inheritance is false, which changes nothing "
            "today because there are no subaccounts. It will change everything "
            "on the day somebody creates one.")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page_meta(session, url, key, **params):
    """Page an API that paginates with an absolute meta.next_page_url."""
    params.setdefault("PageSize", 1000)
    out = []
    while url:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out


def page_2010(session, url, key, **params):
    """Page a 2010-04-01 listing. next_page_uri here is a path, not a URL."""
    params.setdefault("PageSize", 1000)
    out = []
    while url:
        body = get(session, url, **params)
        out.extend(body.get(key, []))
        nxt = body.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out


def sweep_alerts(session, since, limit):
    """Alerts at both log levels, merged on sid.

    Several voice failures are logged at warning rather than error, so an
    error-only sweep reports a clean account while the calls keep failing.
    """
    seen = {}
    for level in ("error", "warning"):
        url = MONITOR + "/Alerts"
        params = {"LogLevel": level, "StartDate": since, "PageSize": 1000}
        count = 0
        while url and count < limit:
            page = get(session, url, **params)
            for a in page.get("alerts", []):
                seen.setdefault(a.get("sid"), a)
                count += 1
            url = (page.get("meta") or {}).get("next_page_url")
            params = {}
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="window to sweep (alerts are retained 30 days)")
    ap.add_argument("--max-calls", type=int, default=20000,
                    help="stop after this many calls when counting attempts")
    ap.add_argument("--no-calls", action="store_true",
                    help="skip the Calls listing and rely on alerts alone")
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

    since = (dt.date.today() - dt.timedelta(days=min(args.days, 30))).isoformat()
    countries = page_meta(session, VOICE + "/DialingPermissions/Countries",
                          "content")
    if not countries:
        log.info("no dialing permission countries returned")
        return 0
    index = prefix_index(countries)

    attempts = {}
    if not args.no_calls:
        for c in page_2010(session, "%s/Accounts/%s/Calls.json" % (BASE, account),
                           "calls", **{"StartTime>=": since}):
            for iso in countries_for(c.get("to"), index):
                attempts[iso] = attempts.get(iso, 0) + 1

    blocked = {}
    calls = {}
    for a in sweep_alerts(session, since, 10000):
        if str(a.get("error_code") or "").strip() not in BLOCKED_CODES:
            continue
        sid = str(a.get("resource_sid") or "")
        if not sid.startswith("CA"):
            continue
        if sid not in calls:
            calls[sid] = get(session, "%s/Accounts/%s/Calls/%s.json"
                             % (BASE, account, sid))
        for iso in countries_for(calls[sid].get("to"), index):
            blocked[iso] = blocked.get(iso, 0) + 1

    findings = 0
    for c in sorted(countries, key=lambda x: str(x.get("iso_code") or "")):
        iso = str(c.get("iso_code") or "").strip().upper()
        state, detail = verdict(c, attempts.get(iso, 0), blocked.get(iso, 0))
        if state in ("open", "closed-unused"):
            continue
        findings += 1
        log.warning("%-22s %s", state, detail)

    subaccounts = len(page_2010(session, BASE + "/Accounts.json", "accounts")) - 1
    state, detail = settings_verdict(get(session, VOICE + "/Settings"),
                                     max(subaccounts, 0))
    (log.info if state == "inherited" else log.warning)("%-22s %s", state, detail)

    log.info("%d blocked destination(s) with traffic across %d country entries",
             findings, len(countries))
    if findings or state == "not-inherited":
        log.warning("  repair: POST %s/DialingPermissions/BulkCountryUpdates "
                    "with an UpdateRequest array of "
                    "{\\"iso_code\\":\\"XX\\",\\"low_risk_numbers_enabled\\":true}", VOICE)
        log.warning("  repair: POST %s/Settings with "
                    "DialingPermissionsInheritance=true to stop every new "
                    "subaccount starting from the home-country default", VOICE)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-dialing-permissions-audit.mjs",
"js": '''/**
 * Report Twilio voice dialing permissions that are blocking real traffic.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';
const VOICE = 'https://voice.twilio.com/v1';

// The REST rejection and the TwiML Dial rejection. Same permission, two callers.
const BLOCKED_CODES = ['21215', '13227'];

/**
 * Map every dialling prefix in the countries listing to its ISO codes. Pure.
 * The value is a list because prefixes are shared: every NANP country answers
 * to 1.
 */
export function prefixIndex(countries) {
  const index = new Map();
  for (const c of countries ?? []) {
    const iso = String(c.iso_code ?? '').trim().toUpperCase();
    for (const code of c.country_codes ?? []) {
      const digits = String(code ?? '').trim().replace(/^\\+/, '');
      if (!iso || !/^[0-9]+$/.test(digits)) continue;
      if (!index.has(digits)) index.set(digits, new Set());
      index.get(digits).add(iso);
    }
  }
  return Object.fromEntries([...index].map(([k, v]) => [k, [...v].sort()]));
}

/**
 * The ISO codes a destination could belong to, longest prefix first. Returns a
 * list, and the list is often longer than one: picking its first member would
 * let this check blame Canada for traffic to the United States.
 */
export function countriesFor(to, index) {
  const digits = String(to ?? '').trim().replace(/^\\+/, '');
  if (!/^[0-9]+$/.test(digits)) return [];
  for (let length = Math.min(4, digits.length); length > 0; length -= 1) {
    const hit = index[digits.slice(0, length)];
    if (hit) return [...hit];
  }
  return [];
}

/**
 * Decide what one country's permissions are doing to you. Pure. Returns
 * [state, detail].
 */
export function verdict(country, attempts = 0, blocked = 0) {
  const iso = String(country.iso_code ?? '??').trim().toUpperCase();
  if (country.low_risk_numbers_enabled) {
    return ['open',
      `${iso} is enabled for low risk numbers, so ordinary calls are permitted. ` +
      'The two high risk switches are separate and are the subject of the ' +
      'companion check.'];
  }

  if (blocked) {
    return ['blocking-live-traffic',
      `${iso} has low_risk_numbers_enabled false and ${blocked} call(s) were ` +
      'refused with 21215 or 13227 in this window. This is an outage in a ' +
      'country you are selling into.'];
  }

  if (attempts) {
    return ['blocking-attempted',
      `${iso} has low_risk_numbers_enabled false and ${attempts} call(s) were ` +
      'placed toward it. No refusal alert landed in this window, so check the ' +
      'window before concluding they got through.'];
  }

  return ['closed-unused',
    `${iso} is disabled and nothing was dialled toward it. Almost every account ` +
    'looks like this for almost every country; it is context, not a finding.'];
}

/**
 * Decide whether subaccounts get the parent's permissions at all. Pure. This is
 * the check that explains a regression with no deploy behind it.
 */
export function settingsVerdict(settings, subaccounts = 0) {
  if (settings.dialing_permissions_inheritance) {
    return ['inherited',
      'dialing_permissions_inheritance is true, so subaccounts use the ' +
      "parent's country permissions."];
  }
  if (subaccounts) {
    return ['not-inherited',
      `dialing_permissions_inheritance is false and this account has ` +
      `${subaccounts} subaccount(s). Each one carries its own ` +
      'home-country-only default, so enabling a country here does nothing for them.'];
  }
  return ['not-inherited-no-subaccounts',
    'dialing_permissions_inheritance is false, which changes nothing today ' +
    'because there are no subaccounts. It will change everything on the day ' +
    'somebody creates one.'];
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

async function pageMeta(auth, url, key, params = {}) {
  const out = [];
  let next = url;
  let p = { PageSize: 1000, ...params };
  while (next) {
    const page = await get(auth, next, p);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    p = {};
  }
  return out;
}

async function page2010(auth, url, key, params = {}) {
  const out = [];
  let next = url;
  let p = { PageSize: 1000, ...params };
  while (next) {
    const body = await get(auth, next, p);
    out.push(...(body[key] ?? []));
    next = body.next_page_uri ? HOST + body.next_page_uri : null;
    p = {};
  }
  return out;
}

async function sweepAlerts(auth, since, limit = 10000) {
  const seen = new Map();
  for (const level of ['error', 'warning']) {
    let url = `${MONITOR}/Alerts`;
    let p = { LogLevel: level, StartDate: since, PageSize: 1000 };
    let count = 0;
    while (url && count < limit) {
      const page = await get(auth, url, p);
      for (const a of page.alerts ?? []) {
        if (!seen.has(a.sid)) seen.set(a.sid, a);
        count += 1;
      }
      url = page.meta?.next_page_url ?? null;
      p = {};
    }
  }
  return [...seen.values()];
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
  const i = process.argv.indexOf('--days');
  const days = Math.min(i === -1 ? 7 : Number(process.argv[i + 1]), 30);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const countries = await pageMeta(auth, `${VOICE}/DialingPermissions/Countries`, 'content');
  if (countries.length === 0) {
    console.log('no dialing permission countries returned');
    return;
  }
  const index = prefixIndex(countries);

  const attempts = new Map();
  if (!process.argv.includes('--no-calls')) {
    const calls = await page2010(auth, `${BASE}/Accounts/${account}/Calls.json`,
                                 'calls', { 'StartTime>=': since });
    for (const c of calls) {
      for (const iso of countriesFor(c.to, index)) {
        attempts.set(iso, (attempts.get(iso) ?? 0) + 1);
      }
    }
  }

  const blocked = new Map();
  const seen = new Map();
  for (const a of await sweepAlerts(auth, since)) {
    if (!BLOCKED_CODES.includes(String(a.error_code ?? '').trim())) continue;
    const sid = String(a.resource_sid ?? '');
    if (!sid.startsWith('CA')) continue;
    if (!seen.has(sid)) {
      seen.set(sid, await get(auth, `${BASE}/Accounts/${account}/Calls/${sid}.json`));
    }
    for (const iso of countriesFor(seen.get(sid).to, index)) {
      blocked.set(iso, (blocked.get(iso) ?? 0) + 1);
    }
  }

  let findings = 0;
  for (const c of [...countries].sort((a, b) =>
    String(a.iso_code ?? '').localeCompare(String(b.iso_code ?? '')))) {
    const iso = String(c.iso_code ?? '').trim().toUpperCase();
    const [state, detail] = verdict(c, attempts.get(iso) ?? 0, blocked.get(iso) ?? 0);
    if (state === 'open' || state === 'closed-unused') continue;
    findings += 1;
    console.warn(`${state.padEnd(22)} ${detail}`);
  }

  const accounts = await page2010(auth, `${BASE}/Accounts.json`, 'accounts');
  const [state, detail] = settingsVerdict(await get(auth, `${VOICE}/Settings`),
                                          Math.max(accounts.length - 1, 0));
  (state === 'inherited' ? console.log : console.warn)(`${state.padEnd(22)} ${detail}`);

  console.log(`${findings} blocked destination(s) with traffic across ` +
              `${countries.length} country entries`);
  if (findings || state === 'not-inherited') {
    console.warn(`  repair: POST ${VOICE}/DialingPermissions/BulkCountryUpdates ` +
                 'with an UpdateRequest array of ' +
                 '{"iso_code":"XX","low_risk_numbers_enabled":true}');
    console.warn(`  repair: POST ${VOICE}/Settings with ` +
                 'DialingPermissionsInheritance=true to stop every new subaccount ' +
                 'starting from the home-country default');
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main(), fail on the missing credentials and set an exit code
// that fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The prefix join is where this check is won or lost, so most of these cases are about it: a destination in a shared dialling code has to come back as the whole group rather than one confident wrong answer, and a longer prefix has to beat a shorter one that also matches. The rest pin the difference between a country that is blocking your traffic and a country that is simply switched off, because reporting the second as a finding is how the report gets ignored.",
"test_py_file": "test_twilio_dialing_permissions_audit.py",
"test_py": '''from twilio_dialing_permissions_audit import (countries_for, prefix_index,
                                                 settings_verdict, verdict)

LISTING = [
    {"iso_code": "US", "country_codes": ["1"], "low_risk_numbers_enabled": True},
    {"iso_code": "CA", "country_codes": ["1"], "low_risk_numbers_enabled": True},
    {"iso_code": "GB", "country_codes": ["44"], "low_risk_numbers_enabled": False},
    {"iso_code": "AU", "country_codes": ["61"], "low_risk_numbers_enabled": False},
]


def test_shared_dialling_code_resolves_to_the_whole_group():
    # Picking one member would blame Canada for traffic to the United States.
    assert countries_for("+14155550100", prefix_index(LISTING)) == ["CA", "US"]


def test_longest_prefix_wins():
    index = prefix_index([{"iso_code": "GB", "country_codes": ["44"]},
                          {"iso_code": "XX", "country_codes": ["4470"]}])
    assert countries_for("+447012345678", index) == ["XX"]


def test_destination_outside_every_prefix_resolves_to_nothing():
    assert countries_for("not-a-number", prefix_index(LISTING)) == []


def test_disabled_country_with_refusals_is_an_outage():
    state, detail = verdict(LISTING[2], attempts=40, blocked=12)
    assert state == "blocking-live-traffic"
    assert "21215" in detail


def test_disabled_country_with_traffic_but_no_alerts_is_softer():
    assert verdict(LISTING[2], attempts=40)[0] == "blocking-attempted"


def test_disabled_country_nobody_calls_is_context_not_a_finding():
    state, detail = verdict(LISTING[3])
    assert state == "closed-unused"
    assert "not a finding" in detail


def test_inheritance_off_with_subaccounts_explains_the_regression():
    state, detail = settings_verdict({"dialing_permissions_inheritance": False}, 6)
    assert state == "not-inherited"
    assert "6 subaccount(s)" in detail


def test_inheritance_off_without_subaccounts_is_a_future_problem():
    assert settings_verdict({"dialing_permissions_inheritance": False})[0] == \\
        "not-inherited-no-subaccounts"
''',
"test_js_file": "twilio-dialing-permissions-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countriesFor, prefixIndex, settingsVerdict, verdict }
  from './twilio-dialing-permissions-audit.mjs';

const LISTING = [
  { iso_code: 'US', country_codes: ['1'], low_risk_numbers_enabled: true },
  { iso_code: 'CA', country_codes: ['1'], low_risk_numbers_enabled: true },
  { iso_code: 'GB', country_codes: ['44'], low_risk_numbers_enabled: false },
  { iso_code: 'AU', country_codes: ['61'], low_risk_numbers_enabled: false },
];

test('shared dialling code resolves to the whole group', () => {
  assert.deepEqual(countriesFor('+14155550100', prefixIndex(LISTING)), ['CA', 'US']);
});

test('longest prefix wins', () => {
  const index = prefixIndex([{ iso_code: 'GB', country_codes: ['44'] },
                             { iso_code: 'XX', country_codes: ['4470'] }]);
  assert.deepEqual(countriesFor('+447012345678', index), ['XX']);
});

test('destination outside every prefix resolves to nothing', () => {
  assert.deepEqual(countriesFor('not-a-number', prefixIndex(LISTING)), []);
});

test('disabled country with refusals is an outage', () => {
  const [state, detail] = verdict(LISTING[2], 40, 12);
  assert.equal(state, 'blocking-live-traffic');
  assert.match(detail, /21215/);
});

test('disabled country with traffic but no alerts is softer', () => {
  assert.equal(verdict(LISTING[2], 40)[0], 'blocking-attempted');
});

test('disabled country nobody calls is context not a finding', () => {
  const [state, detail] = verdict(LISTING[3]);
  assert.equal(state, 'closed-unused');
  assert.match(detail, /not a finding/);
});

test('inheritance off with subaccounts explains the regression', () => {
  const [state, detail] = settingsVerdict({ dialing_permissions_inheritance: false }, 6);
  assert.equal(state, 'not-inherited');
  assert.match(detail, /6 subaccount\\(s\\)/);
});

test('inheritance off without subaccounts is a future problem', () => {
  assert.equal(settingsVerdict({ dialing_permissions_inheritance: false })[0],
               'not-inherited-no-subaccounts');
});
''',
"faq": [
 ("Why does the error name the number when the number is fine?",
  "Because 21215 is phrased from the account's point of view: this account is not authorised to call this number. The authorisation is a per-country allowlist and has nothing to do with the digits, so every check you run against the number itself will pass while the call keeps failing."),
 ("What is the difference between 21215 and 13227?",
  "Where the call came from. 21215 is the REST-initiated rejection, raised when your code creates the call through the API. 13227 is the same refusal reaching a TwiML <Dial>. Same permission, same repair, and they are usually triaged as two unrelated problems."),
 ("Everything works on the parent account and fails on a subaccount. Why?",
  "dialing_permissions_inheritance on /v1/Settings. When it is false, subaccounts do not receive the parent's permissions; each starts from its own home-country-only default. Nothing about your code changed, so this is the variable nobody thinks to check."),
 ("Why report a group of countries for one destination?",
  "Because dialling prefixes are shared. Every North American Numbering Plan country answers to 1, so a destination beginning +1 genuinely could belong to any of them and the API gives no more information than the prefix. Naming one of them would be a guess dressed as a finding."),
 ("Is this the same check as the high-risk one?",
  "It is the same listing read in the opposite direction. This note looks for legitimate destinations that are blocked; the companion note looks for high-risk destinations that are open, which is the toll-fraud exposure. A country can be both at once, and that combination is worth seeing."),
],
"related": [
 ("/twilio/high-risk-dialing-permissions-open/", "High risk dialing prefixes left open to toll fraud"),
 ("/twilio/sms-geo-permissions-disabled/", "SMS Geo Permissions blocking a destination country"),
 ("/twilio/subaccount-suspended-silently/", "A subaccount suspended without anyone noticing"),
],
"citations": [CITE_DP_COUNTRY, CITE_DP_SETTINGS, CITE_21215, CITE_ALERT],
},

{
"slug": "high-risk-dialing-permissions-open",
"title": "High risk dialing prefixes left open to toll fraud",
"description": "Nothing fails. The toll-fraud and special-service ranges stay callable on an upgraded account, and one compromised endpoint runs five figures overnight.",
"h1": "high risk dialing prefixes left open to toll fraud",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio toll fraud", "high_risk_tollfraud_numbers_enabled",
             "irsf international revenue share fraud",
             "twilio dialing permissions high risk", "twilio premium rate fraud"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "This is the note in the section where nothing is broken. Every call succeeds, every setting is at its default, and the finding is an invoice you have not received yet. High-risk special-service and toll-fraud ranges stay dialable on an upgraded account until somebody switches them off, and the people who look for accounts in that state do it at scale and at three in the morning.",
"short_answer": """<p>Read <code>GET https://voice.twilio.com/v1/DialingPermissions/Countries</code> and keep every entry where <code>high_risk_special_numbers_enabled</code> or <code>high_risk_tollfraud_numbers_enabled</code> is <code>true</code> for a country you do not serve. On an upgraded account those stay enabled until you disable them.</p>
<p>Then cross-reference reality: page <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD</code>, group by the dialling prefix of <code>to</code>, and sum <code>price</code>. An open range with calls against it is not an exposure any more. Read <code>GET .../DialingPermissions/Countries/{IsoCode}</code> and its <code>HighRiskSpecialPrefixes</code> subresource when you need the exact ranges.</p>""",
"problem": """<p>Every other note here starts with something failing. This one starts with an account working perfectly and a switch left where it was found. International revenue share fraud is a business: the attacker owns, or rents, a premium range that pays out per minute of traffic terminated on it, and then finds somebody else's telephony account to generate that traffic. Your account is a candidate the moment those ranges are dialable from it.</p>
<p>What makes it expensive is the rate. The fraud does not build slowly; it runs at whatever concurrency your account permits, overnight, on a weekend, in a country nobody watches. By the time a usage alert fires or somebody reads the invoice, the calls are complete, the minutes are billed, and the money has already been shared out at the far end. There is no failed request to find afterwards because none of it failed.</p>""",
"why": """<p><strong>Upgrading opens the account, and opening it is not announced.</strong> A trial account is heavily constrained. Upgrading lifts constraints, which is the point of upgrading, and the high-risk classes are part of what gets lifted. Nothing prompts you to decide about them, so the decision is made by not making it.</p>
<p><strong>The classes are separate switches and read as one setting.</strong> <code>low_risk_numbers_enabled</code>, <code>high_risk_special_numbers_enabled</code> and <code>high_risk_tollfraud_numbers_enabled</code> move independently. The consequence is a state nobody would ever configure deliberately: a country where an ordinary business call is refused and its most expensive ranges are not.</p>
<p><strong>The exposure is in countries you have never thought about.</strong> Attackers do not use ranges in your home market. They use narrow allocations in places you have no customers, which is exactly the set of countries you will never audit by hand and never notice on a bill until the total moves.</p>
<p><strong>It is a per-account state, not a per-call one.</strong> A dialer, a compromised SIP credential, a leaked API key, an injection in a click-to-call form &mdash; the entry point varies and does not matter. What decides how much it costs is whether the expensive ranges were reachable, and that is one read.</p>""",
"steps": [
 {"h": "Read the countries listing and both high-risk flags",
  "body": """<p><code>GET https://voice.twilio.com/v1/DialingPermissions/Countries</code>, following <code>meta.next_page_url</code>. Record <code>iso_code</code>, <code>country_codes</code> and all three switches per entry. The two high-risk ones are the subject here; the low-risk one is needed for context, because its value changes what an open high-risk flag means.</p>"""},
 {"h": "Declare the countries you actually serve",
  "body": """<p>The audit cannot infer this and should not try. Pass the ISO codes your business calls into. Everything outside that list with a high-risk class enabled is exposure you are carrying for no return, and the list is usually far shorter than people expect when they write it down.</p>"""},
 {"h": "Flag the combination nobody configured on purpose",
  "body": """<p><code>low_risk_numbers_enabled</code> <code>false</code> with either high-risk flag <code>true</code> means ordinary calls to that country are refused while its premium ranges are reachable. It is the clearest evidence available that these switches were never set as a group, and it is worth reporting on its own even where there is no traffic.</p>"""},
 {"h": "Put money against each open country",
  "body": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, resolve each <code>to</code> to a country by longest dialling prefix, and sum <code>price</code> &mdash; which arrives as a negative string, so take the absolute value. A country with open high-risk classes and calls already against it is not a risk assessment any more; it is an incident to check.</p>"""},
 {"h": "Close the classes you do not need, then keep the check running",
  "body": """<p><code>POST https://voice.twilio.com/v1/DialingPermissions/BulkCountryUpdates</code> with an <code>UpdateRequest</code> array disabling both high-risk flags for every ISO code you do not serve. Then run this on a schedule. Permissions get widened during incidents by people trying to unblock a customer, and the widening outlives the incident every time.</p>"""},
],
"verify": """<p>Re-run after the bulk update. No unserved country should report an open high-risk class.</p>
<pre><code class="language-bash">python3 twilio_high_risk_dialing_audit.py --serve US,GB,DE --days 30
# 0 country entries with a high risk class open outside the served set</code></pre>""",
"code_intro": "Two paginated GETs &mdash; the countries listing and the calls &mdash; and no third. An API Key with read access is enough, and read access is emphatically what you want on a script whose subject is somebody spending your money. Two pure functions: one turns Twilio's negative price strings into an amount, and one classifies a country against the set you serve and the traffic you have. This is the mirror image of the companion note, which reads the same listing looking for legitimate destinations that are blocked.",
"py_file": "twilio_high_risk_dialing_audit.py",
"py": '''"""Report Twilio countries whose high risk dialing classes are left open.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_high_risk_dialing_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
VOICE = "https://voice.twilio.com/v1"


def money(price):
    """A Twilio price as a positive amount.

    Prices arrive as strings and outbound ones are negative, because they are
    charges against the account. Absolute value here so the report reads as
    money spent rather than as a balance, and 0.0 on anything unparseable so a
    missing price never takes the run down.
    """
    try:
        return abs(float(str(price or "0").strip() or 0))
    except ValueError:
        return 0.0


def prefix_index(countries):
    """Map every dialling prefix in the countries listing to its ISO codes.

    Pure. The value is a list because prefixes are shared: every North American
    Numbering Plan country answers to 1.
    """
    index = {}
    for c in countries or []:
        iso = str(c.get("iso_code") or "").strip().upper()
        for code in c.get("country_codes") or []:
            digits = str(code or "").strip().lstrip("+")
            if iso and digits.isdigit():
                index.setdefault(digits, set()).add(iso)
    return {k: sorted(v) for k, v in index.items()}


def countries_for(to, index):
    """The ISO codes a destination could belong to, longest prefix first."""
    digits = str(to or "").strip().lstrip("+")
    if not digits.isdigit():
        return []
    for length in range(min(4, len(digits)), 0, -1):
        hit = index.get(digits[:length])
        if hit:
            return list(hit)
    return []


def verdict(country, served=(), attempts=0, spend=0.0):
    """Classify one country's high risk exposure. Pure, so the rules can be
    tested without a network.

    served is the set of ISO codes the business actually calls into; it has to
    be declared because no API can infer it. Returns (state, detail).
    """
    iso = str(country.get("iso_code") or "??").strip().upper()
    serving = {str(s).strip().upper() for s in served}
    special = bool(country.get("high_risk_special_numbers_enabled"))
    fraud = bool(country.get("high_risk_tollfraud_numbers_enabled"))
    low = bool(country.get("low_risk_numbers_enabled"))

    if not (special or fraud):
        return ("closed",
                "%s has both high risk classes disabled, so its premium and "
                "toll fraud ranges are not reachable from this account." % iso)

    classes = ", ".join([n for n, on in
                         (("high_risk_special_numbers_enabled", special),
                          ("high_risk_tollfraud_numbers_enabled", fraud)) if on])

    if attempts:
        return ("open-and-dialled",
                "%s has %s and %d call(s) already went to it in this window, "
                "costing %.2f. This has stopped being a risk assessment: check "
                "what placed them before you close anything."
                % (iso, classes, attempts, spend))

    if not low:
        return ("premium-only",
                "%s has low_risk_numbers_enabled false while %s is true: an "
                "ordinary business call to this country is refused and its most "
                "expensive ranges are not. Nobody configures that deliberately."
                % (iso, classes))

    if iso in serving:
        return ("open-in-market",
                "%s is a country you serve and %s is on. Low risk traffic is "
                "what your customers are; the high risk classes are what "
                "somebody else's revenue share is." % (iso, classes))

    return ("open-unused",
            "%s is outside the served set and %s is on. This is exposure "
            "carried for no return, in exactly the kind of country an IRSF "
            "range sits in." % (iso, classes))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page_meta(session, url, key, **params):
    """Page an API that paginates with an absolute meta.next_page_url."""
    params.setdefault("PageSize", 1000)
    out = []
    while url:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out


def page_2010(session, url, key, limit, **params):
    """Page a 2010-04-01 listing. next_page_uri here is a path, not a URL."""
    params.setdefault("PageSize", 1000)
    out = []
    while url and len(out) < limit:
        body = get(session, url, **params)
        out.extend(body.get(key, []))
        nxt = body.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serve", default="",
                    help="comma separated ISO codes your business calls into")
    ap.add_argument("--days", type=int, default=30,
                    help="window over which to count traffic and spend")
    ap.add_argument("--max-calls", type=int, default=20000,
                    help="stop after this many calls")
    ap.add_argument("--no-calls", action="store_true",
                    help="skip the traffic join and report permissions alone")
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

    served = [s for s in (p.strip().upper() for p in args.serve.split(",")) if s]
    if not served:
        log.warning("no --serve list given: every country with a high risk "
                    "class open will be reported as unused")

    countries = page_meta(session, VOICE + "/DialingPermissions/Countries",
                          "content")
    if not countries:
        log.info("no dialing permission countries returned")
        return 0
    index = prefix_index(countries)

    attempts, spend = {}, {}
    if not args.no_calls:
        since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
        calls = page_2010(session, "%s/Accounts/%s/Calls.json" % (BASE, account),
                          "calls", args.max_calls, **{"StartTime>=": since})
        for c in calls:
            for iso in countries_for(c.get("to"), index):
                attempts[iso] = attempts.get(iso, 0) + 1
                spend[iso] = spend.get(iso, 0.0) + money(c.get("price"))

    findings = []
    for c in countries:
        iso = str(c.get("iso_code") or "").strip().upper()
        state, detail = verdict(c, served, attempts.get(iso, 0), spend.get(iso, 0.0))
        if state == "closed":
            continue
        findings.append((state, iso, detail))

    order = {"open-and-dialled": 0, "premium-only": 1, "open-unused": 2,
             "open-in-market": 3}
    for state, iso, detail in sorted(findings, key=lambda f: (order.get(f[0], 9), f[1])):
        log.warning("%-17s %s", state, detail)

    unserved = [f for f in findings if f[0] in ("open-unused", "premium-only",
                                                "open-and-dialled")]
    log.info("%d country entries with a high risk class open outside the served set",
             len(unserved))
    if not findings:
        return 0
    log.warning("  repair: POST %s/DialingPermissions/BulkCountryUpdates with an "
                "UpdateRequest array disabling high_risk_special_numbers_enabled "
                "and high_risk_tollfraud_numbers_enabled for every unused ISO "
                "code", VOICE)
    log.warning("  repair: run this on a schedule. Permissions get widened "
                "during incidents and the widening outlives the incident")
    return 1 if unserved else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-high-risk-dialing-audit.mjs",
"js": '''/**
 * Report Twilio countries whose high risk dialing classes are left open.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const VOICE = 'https://voice.twilio.com/v1';

/**
 * A Twilio price as a positive amount. Prices arrive as strings and outbound
 * ones are negative, because they are charges against the account. Zero on
 * anything unparseable so a missing price never takes the run down.
 */
export function money(price) {
  const n = Number.parseFloat(String(price ?? '0').trim());
  return Number.isFinite(n) ? Math.abs(n) : 0;
}

/** Map every dialling prefix in the countries listing to its ISO codes. Pure. */
export function prefixIndex(countries) {
  const index = new Map();
  for (const c of countries ?? []) {
    const iso = String(c.iso_code ?? '').trim().toUpperCase();
    for (const code of c.country_codes ?? []) {
      const digits = String(code ?? '').trim().replace(/^\\+/, '');
      if (!iso || !/^[0-9]+$/.test(digits)) continue;
      if (!index.has(digits)) index.set(digits, new Set());
      index.get(digits).add(iso);
    }
  }
  return Object.fromEntries([...index].map(([k, v]) => [k, [...v].sort()]));
}

/** The ISO codes a destination could belong to, longest prefix first. */
export function countriesFor(to, index) {
  const digits = String(to ?? '').trim().replace(/^\\+/, '');
  if (!/^[0-9]+$/.test(digits)) return [];
  for (let length = Math.min(4, digits.length); length > 0; length -= 1) {
    const hit = index[digits.slice(0, length)];
    if (hit) return [...hit];
  }
  return [];
}

/**
 * Classify one country's high risk exposure. Pure. `served` is the set of ISO
 * codes the business actually calls into, which has to be declared because no
 * API can infer it. Returns [state, detail].
 */
export function verdict(country, served = [], attempts = 0, spend = 0) {
  const iso = String(country.iso_code ?? '??').trim().toUpperCase();
  const serving = new Set([...served].map((s) => String(s).trim().toUpperCase()));
  const special = Boolean(country.high_risk_special_numbers_enabled);
  const fraud = Boolean(country.high_risk_tollfraud_numbers_enabled);
  const low = Boolean(country.low_risk_numbers_enabled);

  if (!special && !fraud) {
    return ['closed',
      `${iso} has both high risk classes disabled, so its premium and toll ` +
      'fraud ranges are not reachable from this account.'];
  }

  const classes = [['high_risk_special_numbers_enabled', special],
                   ['high_risk_tollfraud_numbers_enabled', fraud]]
    .filter(([, on]) => on).map(([n]) => n).join(', ');

  if (attempts) {
    return ['open-and-dialled',
      `${iso} has ${classes} and ${attempts} call(s) already went to it in this ` +
      `window, costing ${spend.toFixed(2)}. This has stopped being a risk ` +
      'assessment: check what placed them before you close anything.'];
  }

  if (!low) {
    return ['premium-only',
      `${iso} has low_risk_numbers_enabled false while ${classes} is true: an ` +
      'ordinary business call to this country is refused and its most expensive ' +
      'ranges are not. Nobody configures that deliberately.'];
  }

  if (serving.has(iso)) {
    return ['open-in-market',
      `${iso} is a country you serve and ${classes} is on. Low risk traffic is ` +
      "what your customers are; the high risk classes are what somebody else's " +
      'revenue share is.'];
  }

  return ['open-unused',
    `${iso} is outside the served set and ${classes} is on. This is exposure ` +
    'carried for no return, in exactly the kind of country an IRSF range sits in.'];
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

async function pageMeta(auth, url, key, params = {}) {
  const out = [];
  let next = url;
  let p = { PageSize: 1000, ...params };
  while (next) {
    const page = await get(auth, next, p);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    p = {};
  }
  return out;
}

async function page2010(auth, url, key, limit, params = {}) {
  const out = [];
  let next = url;
  let p = { PageSize: 1000, ...params };
  while (next && out.length < limit) {
    const body = await get(auth, next, p);
    out.push(...(body[key] ?? []));
    next = body.next_page_uri ? HOST + body.next_page_uri : null;
    p = {};
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
  const flag = (name, fallback) => {
    const i = process.argv.indexOf(name);
    return i === -1 ? fallback : process.argv[i + 1];
  };
  const served = String(flag('--serve', '')).split(',')
    .map((s) => s.trim().toUpperCase()).filter(Boolean);
  const days = Number(flag('--days', 30));
  if (served.length === 0) {
    console.warn('no --serve list given: every country with a high risk class ' +
                 'open will be reported as unused');
  }

  const countries = await pageMeta(auth, `${VOICE}/DialingPermissions/Countries`, 'content');
  if (countries.length === 0) {
    console.log('no dialing permission countries returned');
    return;
  }
  const index = prefixIndex(countries);

  const attempts = new Map();
  const spend = new Map();
  if (!process.argv.includes('--no-calls')) {
    const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
    const calls = await page2010(auth, `${BASE}/Accounts/${account}/Calls.json`,
                                 'calls', 20000, { 'StartTime>=': since });
    for (const c of calls) {
      for (const iso of countriesFor(c.to, index)) {
        attempts.set(iso, (attempts.get(iso) ?? 0) + 1);
        spend.set(iso, (spend.get(iso) ?? 0) + money(c.price));
      }
    }
  }

  const findings = [];
  for (const c of countries) {
    const iso = String(c.iso_code ?? '').trim().toUpperCase();
    const [state, detail] = verdict(c, served, attempts.get(iso) ?? 0,
                                    spend.get(iso) ?? 0);
    if (state === 'closed') continue;
    findings.push([state, iso, detail]);
  }

  const order = { 'open-and-dialled': 0, 'premium-only': 1, 'open-unused': 2,
                  'open-in-market': 3 };
  findings.sort((a, b) => (order[a[0]] ?? 9) - (order[b[0]] ?? 9) ||
                          a[1].localeCompare(b[1]));
  for (const [state, , detail] of findings) {
    console.warn(`${state.padEnd(17)} ${detail}`);
  }

  const unserved = findings.filter(([s]) =>
    ['open-unused', 'premium-only', 'open-and-dialled'].includes(s));
  console.log(`${unserved.length} country entries with a high risk class open ` +
              'outside the served set');
  if (findings.length === 0) return;
  console.warn(`  repair: POST ${VOICE}/DialingPermissions/BulkCountryUpdates ` +
               'with an UpdateRequest array disabling ' +
               'high_risk_special_numbers_enabled and ' +
               'high_risk_tollfraud_numbers_enabled for every unused ISO code');
  console.warn('  repair: run this on a schedule. Permissions get widened during ' +
               'incidents and the widening outlives the incident');
  if (unserved.length) process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main(), fail on the missing credentials and set an exit code
// that fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that has to be pinned is <code>premium-only</code>: low risk off, high risk on. It is the combination that proves the three switches were never considered together, and a check that only asks whether the country is enabled will class it as blocked and move on. The rest hold the line between exposure and incident, because a country with open ranges and traffic already against it needs a different response from one with open ranges and none.",
"test_py_file": "test_twilio_high_risk_dialing_audit.py",
"test_py": '''from twilio_high_risk_dialing_audit import countries_for, money, prefix_index, verdict


def open_country(iso, low=True, special=False, fraud=False):
    return {"iso_code": iso, "country_codes": ["500"],
            "low_risk_numbers_enabled": low,
            "high_risk_special_numbers_enabled": special,
            "high_risk_tollfraud_numbers_enabled": fraud}


def test_both_classes_disabled_is_closed():
    assert verdict(open_country("LV"))[0] == "closed"


def test_low_risk_off_with_high_risk_on_is_the_telling_combination():
    state, detail = verdict(open_country("LV", low=False, fraud=True),
                            served=["US"])
    assert state == "premium-only"
    assert "Nobody configures that deliberately" in detail


def test_open_range_with_traffic_is_an_incident_not_an_exposure():
    state, detail = verdict(open_country("LV", special=True), served=["US"],
                            attempts=41, spend=1830.5)
    assert state == "open-and-dialled"
    assert "1830.50" in detail


def test_open_range_outside_the_served_set_is_carried_for_no_return():
    assert verdict(open_country("LV", fraud=True), served=["US", "GB"])[0] == \\
        "open-unused"


def test_open_range_in_a_served_country_is_still_reported():
    state, _ = verdict(open_country("GB", special=True), served=["us", "gb"])
    assert state == "open-in-market"


def test_served_codes_are_compared_case_insensitively():
    assert verdict(open_country("GB", fraud=True), served=["gb"])[0] == "open-in-market"


def test_price_strings_are_negative_and_report_as_spend():
    assert money("-0.0850") == 0.085
    assert money(None) == 0.0
    assert money("not a price") == 0.0


def test_prefix_join_keeps_shared_codes_as_a_group():
    index = prefix_index([open_country("A"), open_country("B")])
    assert countries_for("+5005550100", index) == ["A", "B"]
''',
"test_js_file": "twilio-high-risk-dialing-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countriesFor, money, prefixIndex, verdict }
  from './twilio-high-risk-dialing-audit.mjs';

const openCountry = (iso, low = true, special = false, fraud = false) => ({
  iso_code: iso,
  country_codes: ['500'],
  low_risk_numbers_enabled: low,
  high_risk_special_numbers_enabled: special,
  high_risk_tollfraud_numbers_enabled: fraud,
});

test('both classes disabled is closed', () => {
  assert.equal(verdict(openCountry('LV'))[0], 'closed');
});

test('low risk off with high risk on is the telling combination', () => {
  const [state, detail] = verdict(openCountry('LV', false, false, true), ['US']);
  assert.equal(state, 'premium-only');
  assert.match(detail, /Nobody configures that deliberately/);
});

test('open range with traffic is an incident not an exposure', () => {
  const [state, detail] = verdict(openCountry('LV', true, true), ['US'], 41, 1830.5);
  assert.equal(state, 'open-and-dialled');
  assert.match(detail, /1830\\.50/);
});

test('open range outside the served set is carried for no return', () => {
  assert.equal(verdict(openCountry('LV', true, false, true), ['US', 'GB'])[0],
               'open-unused');
});

test('open range in a served country is still reported', () => {
  assert.equal(verdict(openCountry('GB', true, true), ['us', 'gb'])[0],
               'open-in-market');
});

test('price strings are negative and report as spend', () => {
  assert.equal(money('-0.0850'), 0.085);
  assert.equal(money(null), 0);
  assert.equal(money('not a price'), 0);
});

test('prefix join keeps shared codes as a group', () => {
  const index = prefixIndex([openCountry('A'), openCountry('B')]);
  assert.deepEqual(countriesFor('+5005550100', index), ['A', 'B']);
});
''',
"faq": [
 ("Nothing is failing. Why is this in a section about failures?",
  "Because the failure has not happened yet and the read that would have prevented it is one GET. Every other note here starts from an error code; this one starts from a switch left at the value it shipped with, and the symptom when it finally arrives is an invoice rather than an alert."),
 ("What is IRSF?",
  "International revenue share fraud. Someone controls a premium range that pays out per minute terminated on it, then generates traffic to it from somebody else's account. Your exposure is not the compromise itself but whether those ranges were dialable from your account when it happened."),
 ("Why does low risk disabled with high risk enabled matter so much?",
  "Because it is a state nobody would choose. It means an ordinary business call to that country is refused while its most expensive ranges are reachable, which is only possible if the three switches were never looked at as a group. Wherever it appears, treat the rest of that account's permissions as unreviewed."),
 ("Why do I have to declare the countries I serve?",
  "Because no API knows. Twilio can tell you what is enabled; only you can say which of it is deliberate. Without that list the script has to report every open country as unused, which is a longer report and a less useful one."),
 ("Should the script close the ranges it finds?",
  "It will not, and here the read-only rule earns itself twice. Closing a class from a scheduled job would cut off live traffic in a country somebody does serve. It prints the bulk update, with the exact flags and ISO codes, for a person who can check that list against the business first."),
],
"related": [
 ("/twilio/voice-dialing-permissions-blocked/", "21215: dialing permissions block a country you sell into"),
 ("/twilio/no-usage-trigger-configured/", "No usage trigger, so nothing warns you about spend"),
 ("/twilio/balance-below-safety-floor/", "The account balance is below its safety floor"),
],
"citations": [CITE_DP_RESOURCES, CITE_DP_PREFIX, CITE_DP_COUNTRY, CITE_CALL],
},

]
