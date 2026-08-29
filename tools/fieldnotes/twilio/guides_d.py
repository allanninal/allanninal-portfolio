#!/usr/bin/env python3
"""/twilio/ field notes, batch D — the writing.

Four failures that all surface in the same place: the Monitor Alerts list. A
webhook that returns the wrong thing, one that never answers the phone, one
whose certificate ran out, and one whose name does not exist. Twilio logs all
four identically from the outside, and the error code is the only thing that
separates them.

Two constraints shape every script here. `response_body` and `response_headers`
are populated only on the single-alert fetch `GET /v1/Alerts/{Sid}` and are
absent from every row of the list, so anything that needs to see what a webhook
returned pays one request per alert. And alerts are retained 30 days, so every
verdict about when something started is bounded by that window and says so.

Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run.
"""

CITE_11200 = ("Error 11200: HTTP retrieval failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11200")
CITE_11205 = ("Error 11205: HTTP connection failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11205")
CITE_11210 = ("Error 11210: HTTP bad host name — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11210")
CITE_11236 = ("Error 11236: certificate invalid, certificate expired — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11236")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_WEBHOOKS = ("Webhooks (HTTP callbacks) — Twilio Docs",
                 "https://www.twilio.com/docs/usage/webhooks")
CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "status-callback-webhook-failing-11200",
"title": "Status callback failures with 11200 leave delivery state blind",
"description": "Twilio delivered the message and your database still says queued. The 11200 alerts name the failing endpoint; the Messages list is the state that is true.",
"h1": "status callback failures with 11200 leave delivery state blind",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11200", "twilio status callback failing",
             "twilio statuscallback not received", "twilio http retrieval failure",
             "twilio message stuck queued in database"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Support says the customer never got the text. Your dashboard agrees: the row still reads <code>queued</code>, hours later. Then you open the Twilio Console, paste the Message SID, and it says <code>delivered</code> &mdash; forty seconds after you sent it. Nothing was lost. Twilio tried to tell you, your endpoint returned something other than a <code>2xx</code>, and the update went in the bin along with every other one that day.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code>, keep alerts where <code>error_code</code> is <code>11200</code>, and group them by <code>request_url</code>. Then read the configured <code>status_callback</code> off <code>GET https://messaging.twilio.com/v1/Services</code> and <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code>, and match the two.</p>
<p>An 11200 on a URL that is one of those is a status callback: delivery state your database never received. An 11200 on any other URL is an inbound handler, which is a different failure with a different repair. Reconcile against <code>Messages.json</code> &mdash; that list is the state that is actually true.</p>""",
"problem": """<p>A status callback is a push copy of something Twilio already knows. That is what makes this failure so patient: nothing is destroyed, the Message resource carries the correct final status the whole time, and every symptom shows up only in your own database. The gap opens quietly and stays open until a human compares two screens.</p>
<p>The shape it takes downstream is worse than a stale row. Retry jobs fire against messages that already arrived. Dunning emails go out to customers whose payment reminder was delivered. A support agent reads <code>queued</code>, resends by hand, and the recipient gets the same one-time passcode twice. Every one of those is caused by trusting a push where a pull was available.</p>""",
"why": """<p><strong>Twilio does not retry status callbacks forever.</strong> A callback is a best-effort delivery of an event that has already happened. If your endpoint returns a <code>500</code>, or takes longer than Twilio's HTTP window, the attempt is logged as 11200 and the event moves on. There is no queue holding it for you and no replay endpoint to ask for it back.</p>
<p><strong>The alert names the URL, not the setting.</strong> <code>request_url</code> is the URL Twilio fetched, complete with the query string it appended. The configured value on the Messaging Service or the phone number has no query string, and may differ in scheme or trailing slash. Comparing the two as raw strings matches nothing, which is exactly how a report ends up claiming every alert is on some other webhook.</p>
<p><strong>Two resources own the same setting.</strong> <code>status_callback</code> exists on the Messaging Service and on each phone number. Read only one of them and half your alerts get misattributed &mdash; and misattribution matters here, because an 11200 on an inbound handler means the message or call itself dropped, while an 11200 on a status callback means only that your bookkeeping is behind.</p>
<p><strong>The response body is not in the list.</strong> Every row of <code>GET /v1/Alerts</code> has <code>response_body</code> and <code>response_headers</code> blank. They are populated only when you fetch a single alert by SID. So the cheap sweep tells you which endpoint is failing and how often, and finding out <em>what</em> it returned costs one extra request per alert you care about.</p>""",
"steps": [
 {"h": "Sweep the alerts for 11200 over a bounded window",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>. Alerts are retained 30 days, so a window longer than that is not a longer window, it is the same one with a misleading label. Read <code>error_code</code> as an integer: the Monitor API returns it as a string, unlike the Messages list.</p>"""},
 {"h": "Normalise the URLs before you compare them",
  "body": """<p>Reduce both the alert's <code>request_url</code> and the configured <code>status_callback</code> to lowercase host plus path, dropping the query string and any trailing slash. Twilio appends parameters to the URL it fetches, so the logged URL never equals the configured one character for character.</p>"""},
 {"h": "Read the configured callbacks from both resources",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code> gives <code>status_callback</code> per Messaging Service; <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> gives it per number. Build one set from both. An endpoint in that set is a status callback; anything else is an inbound handler and belongs in a different report.</p>"""},
 {"h": "Fetch one failing alert by SID to see the response",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> returns <code>response_body</code> and <code>response_headers</code>, which the list omits entirely. One fetch per failing endpoint is usually enough: a stack trace, a login redirect, or an empty body with a <code>502</code> each point at a different repair. Cap the number of fetches, because this is one request per alert.</p>"""},
 {"h": "Reconcile against the Messages list and backfill",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD</code> and count how many messages reached a final status while the callbacks were failing. That number is the size of the hole in your database. Fix the handler so it returns an empty <code>200</code> immediately and does its work asynchronously, then backfill by polling that list rather than waiting for a replay that is never coming.</p>"""},
],
"verify": """<p>Re-run the script over the same window after the handler change. Configured callbacks should stop appearing in the report entirely.</p>
<pre><code class="language-bash">python3 twilio_status_callback_audit.py --days 3
# 0 status callback endpoint(s) failing, 0 other webhook(s) with 11200</code></pre>""",
"code_intro": "Four reads joined into one report: the alerts, the two places a status callback can be configured, and the Messages list that says what really happened. The pure functions are the URL normalisation and the classification, because both are where this check quietly fails &mdash; a comparison that never matches reports a clean account, and so does one that never ran.",
"py_file": "twilio_status_callback_audit.py",
"py": '''"""Find StatusCallback endpoints failing with 11200 and size the gap they left.

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
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_status_callback_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"
MESSAGING = "https://messaging.twilio.com/v1"

RETRIEVAL_FAILURE = 11200

# Statuses a message never leaves. Anything else is still in flight, and the
# callback that would have told you it moved is the thing that failed.
FINAL = {"delivered", "undelivered", "failed", "received", "read"}

# Alerts are retained 30 days. A longer window is not more history, it is the
# same history under a label that makes the report look more thorough.
MAX_DAYS = 30


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API hands this back as a string, while the Messages list hands
    back a number for the same concept. A comparison written against one and
    pointed at the other matches nothing and reports a healthy account.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def endpoint(url):
    """Reduce a webhook URL to lowercase host plus path.

    Twilio logs the URL it actually fetched, carrying the parameters it appended
    and whatever scheme and trailing slash the configuration happened to have.
    The configured value has none of that. Comparing the two raw is the mistake
    that makes every alert look like it belongs to some other webhook.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        return str(url).strip().lower().rstrip("/")
    path = (parts.path or "").rstrip("/")
    return host + path


def callback_endpoints(services, numbers):
    """Every status_callback configured on the account, normalised.

    Two resources own one setting: a Messaging Service carries a status_callback
    for everything sent through it, and each phone number carries its own for
    messages sent from that number outside a service. Reading only one of them
    misattributes half the alerts, and the two roles have opposite urgency.
    """
    out = {}
    for s in services or []:
        e = endpoint(s.get("status_callback"))
        if e:
            out.setdefault(e, []).append("service %s" % (s.get("sid") or "?"))
    for n in numbers or []:
        e = endpoint(n.get("status_callback"))
        if e:
            label = n.get("phone_number") or n.get("sid") or "?"
            out.setdefault(e, []).append("number %s" % label)
    return out


def tally(alerts, callbacks):
    """Group 11200 alerts by the endpoint that failed.

    Pure, so the grouping and the role assignment can be tested without a
    network. date_generated is ISO 8601 in UTC on every alert, so a string
    comparison orders them correctly and no parsing is needed to find the ends.
    """
    out = {}
    for a in alerts:
        if code_of(a) != RETRIEVAL_FAILURE:
            continue
        e = endpoint(a.get("request_url"))
        row = out.setdefault(e, {
            "alerts": 0,
            "sids": [],
            "owners": list(callbacks.get(e, [])),
            "role": "status-callback" if e in callbacks else "other-webhook",
            "first": None,
            "last": None,
        })
        row["alerts"] += 1
        if len(row["sids"]) < 3:
            row["sids"].append(a.get("sid"))
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
    return out


def verdict(row, min_alerts=3):
    """Classify one failing endpoint. Pure, so the thresholds are visible.

    Returns (state, detail).
    """
    n = int(row.get("alerts") or 0)
    if not n:
        return ("clean", "no 11200 in the window")

    if row.get("role") != "status-callback":
        return ("other-webhook",
                "%d x 11200 on a URL that is not a configured status_callback. "
                "This is an inbound handler, so the call or message itself "
                "dropped rather than the bookkeeping: a fallback URL is the "
                "mitigation there, not a backfill." % n)

    if n < min_alerts:
        return ("intermittent",
                "%d x 11200 on a status callback. A handful is a slow handler "
                "under load rather than an outage, but those updates are still "
                "gone and only the Messages list has them." % n)

    return ("blind",
            "%d x 11200 on a status callback. Every one is a delivery update "
            "your database never received, and Twilio does not hold them for a "
            "replay." % n)


def reconcile(messages):
    """Count what the Messages list says, which is the state that is true.

    The callback is a push copy of this resource. When the push fails nothing is
    lost, it is simply not in your database, so the number worth printing is how
    many messages reached a final status during the window.
    """
    out = {"total": 0, "final": 0, "open": 0, "failed": 0}
    for m in messages:
        status = str(m.get("status") or "").lower()
        out["total"] += 1
        if status in FINAL:
            out["final"] += 1
        else:
            out["open"] += 1
        if status in ("undelivered", "failed"):
            out["failed"] += 1
    return out


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, since, limit, log_level="error"):
    """Page the Monitor alerts. next_page_url is absolute on this API."""
    url = MONITOR + "/Alerts"
    params = {"LogLevel": log_level, "StartDate": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def fetch_alert(session, sid):
    """One alert by SID, which is the only place response_body exists.

    The list resource blanks response_body and response_headers on every row, so
    seeing what the endpoint actually returned costs one request per alert.
    """
    return get(session, "%s/Alerts/%s" % (MONITOR, sid))


def list_services(session, limit=1000):
    url = MESSAGING + "/Services"
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("services", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out


def list_numbers(session, account, limit=2000):
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out


def list_messages(session, account, since, limit):
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
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging the Messages list after this many")
    ap.add_argument("--min-alerts", type=int, default=3,
                    help="fewer than this on one endpoint is reported as intermittent")
    ap.add_argument("--sample", type=int, default=1,
                    help="alerts to fetch individually per endpoint for the "
                         "response body (0 to skip; each one is a request)")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    days = args.days
    if days > MAX_DAYS:
        log.warning("alerts are retained %d days; reading %d instead of %d",
                    MAX_DAYS, MAX_DAYS, days)
        days = MAX_DAYS

    session = requests.Session()
    session.auth = (key, secret)

    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    alerts = list_alerts(session, since, args.max_alerts)
    callbacks = callback_endpoints(list_services(session),
                                   list_numbers(session, account))
    log.info("%d alert(s) since %s, %d configured status_callback endpoint(s)",
             len(alerts), since, len(callbacks))

    rows = tally(alerts, callbacks)
    blind = other = 0
    for e, row in sorted(rows.items()):
        state, detail = verdict(row, args.min_alerts)
        line = "%-14s %s  %s" % (state, e, detail)
        if state == "clean":
            log.info(line)
            continue
        if state == "other-webhook":
            other += 1
            log.warning(line)
            continue
        blind += 1
        log.warning(line)
        if row["owners"]:
            log.warning("  configured on: %s", ", ".join(row["owners"]))
        log.warning("  first %s, last %s", row["first"], row["last"])
        for sid in row["sids"][:max(0, args.sample)]:
            full = fetch_alert(session, sid)
            body = (full.get("response_body") or "").strip().replace("\\n", " ")
            log.warning("  %s returned: %s", sid, body[:200] or "(empty body)")
        log.warning("  repair: return an empty 200 from this handler before you "
                    "do any work, process the payload asynchronously, and "
                    "allowlist Twilio's egress ranges if a WAF is in front of "
                    "it. Then backfill from Messages.json.")

    counts = reconcile(list_messages(session, account, since, args.max_messages))
    log.info("messages since %s: %d total, %d final, %d still open, %d failed",
             since, counts["total"], counts["final"], counts["open"],
             counts["failed"])
    log.info("%d status callback endpoint(s) failing, %d other webhook(s) with "
             "11200", blind, other)
    return 1 if blind else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-status-callback-audit.mjs",
"js": '''/**
 * Find StatusCallback endpoints failing with 11200 and size the gap they left.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';
const MESSAGING = 'https://messaging.twilio.com/v1';

const RETRIEVAL_FAILURE = 11200;

// Statuses a message never leaves. Anything else is still in flight.
const FINAL = new Set(['delivered', 'undelivered', 'failed', 'received', 'read']);

// Alerts are retained 30 days. A longer window is the same history mislabelled.
const MAX_DAYS = 30;

/**
 * Read error_code off an alert as a number, or null. The Monitor API returns it
 * as a string while the Messages list returns a number, and a check written for
 * one and pointed at the other reports a healthy account.
 */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Reduce a webhook URL to lowercase host plus path. Twilio logs the URL it
 * fetched, with the parameters it appended; the configured value has none of
 * them, so a raw comparison never matches.
 */
export function endpoint(url) {
  if (!url) return '';
  const raw = String(url).trim();
  let host = '';
  let path = '';
  try {
    const u = new URL(raw);
    host = u.hostname.toLowerCase();
    path = u.pathname;
  } catch {
    return raw.toLowerCase().replace(/\\/+$/, '');
  }
  if (!host) return raw.toLowerCase().replace(/\\/+$/, '');
  while (path.endsWith('/')) path = path.slice(0, -1);
  return host + path;
}

/**
 * Every status_callback configured on the account, normalised. A Messaging
 * Service carries one for the whole service and each phone number carries its
 * own; reading only one of them misattributes half the alerts.
 */
export function callbackEndpoints(services, numbers) {
  const out = new Map();
  for (const s of services ?? []) {
    const e = endpoint(s.status_callback);
    if (!e) continue;
    if (!out.has(e)) out.set(e, []);
    out.get(e).push(`service ${s.sid ?? '?'}`);
  }
  for (const n of numbers ?? []) {
    const e = endpoint(n.status_callback);
    if (!e) continue;
    if (!out.has(e)) out.set(e, []);
    out.get(e).push(`number ${n.phone_number ?? n.sid ?? '?'}`);
  }
  return out;
}

/**
 * Group 11200 alerts by the endpoint that failed. Pure. date_generated is ISO
 * 8601 in UTC, so a string comparison finds the ends without parsing.
 */
export function tally(alerts, callbacks) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== RETRIEVAL_FAILURE) continue;
    const e = endpoint(a.request_url);
    if (!out.has(e)) {
      out.set(e, {
        alerts: 0,
        sids: [],
        owners: [...(callbacks.get(e) ?? [])],
        role: callbacks.has(e) ? 'status-callback' : 'other-webhook',
        first: null,
        last: null,
      });
    }
    const row = out.get(e);
    row.alerts += 1;
    if (row.sids.length < 3) row.sids.push(a.sid);
    const when = a.date_generated ?? '';
    if (when) {
      row.first = row.first === null || when < row.first ? when : row.first;
      row.last = row.last === null || when > row.last ? when : row.last;
    }
  }
  return out;
}

/** Classify one failing endpoint. Pure. Returns [state, detail]. */
export function verdict(row, minAlerts = 3) {
  const n = Number(row.alerts ?? 0);
  if (!n) return ['clean', 'no 11200 in the window'];

  if (row.role !== 'status-callback') {
    return ['other-webhook',
      `${n} x 11200 on a URL that is not a configured status_callback. This is ` +
      'an inbound handler, so the call or message itself dropped rather than ' +
      'the bookkeeping: a fallback URL is the mitigation there, not a backfill.'];
  }

  if (n < minAlerts) {
    return ['intermittent',
      `${n} x 11200 on a status callback. A handful is a slow handler under ` +
      'load rather than an outage, but those updates are still gone and only ' +
      'the Messages list has them.'];
  }

  return ['blind',
    `${n} x 11200 on a status callback. Every one is a delivery update your ` +
    'database never received, and Twilio does not hold them for a replay.'];
}

/**
 * Count what the Messages list says, which is the state that is true. The
 * callback is only a push copy of this resource.
 */
export function reconcile(messages) {
  const out = { total: 0, final: 0, open: 0, failed: 0 };
  for (const m of messages) {
    const status = String(m.status ?? '').toLowerCase();
    out.total += 1;
    if (FINAL.has(status)) out.final += 1;
    else out.open += 1;
    if (status === 'undelivered' || status === 'failed') out.failed += 1;
  }
  return out;
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

export async function listAlerts(auth, since, limit = 10000, logLevel = 'error') {
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

/** One alert by SID: the only place response_body is populated. */
export async function fetchAlert(auth, sid) {
  return get(auth, `${MONITOR}/Alerts/${sid}`);
}

async function listServices(auth) {
  let url = `${MESSAGING}/Services`;
  let params = { PageSize: 100 };
  const out = [];
  while (url) {
    const page = await get(auth, url, params);
    out.push(...(page.services ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out;
}

async function listNumbers(auth, account) {
  let url = `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`;
  let params = { PageSize: 1000 };
  const out = [];
  while (url) {
    const page = await get(auth, url, params);
    out.push(...(page.incoming_phone_numbers ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out;
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

  let days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 3) || 3;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await listAlerts(auth, since);
  const callbacks = callbackEndpoints(await listServices(auth),
                                      await listNumbers(auth, account));
  console.log(`${alerts.length} alert(s) since ${since}, ${callbacks.size} ` +
              'configured status_callback endpoint(s)');

  const rows = tally(alerts, callbacks);
  let blind = 0;
  let other = 0;
  for (const [e, row] of [...rows.entries()].sort()) {
    const [state, detail] = verdict(row);
    const line = `${state.padEnd(14)} ${e}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    if (state === 'other-webhook') { other += 1; console.warn(line); continue; }
    blind += 1;
    console.warn(line);
    if (row.owners.length) console.warn(`  configured on: ${row.owners.join(', ')}`);
    console.warn(`  first ${row.first}, last ${row.last}`);
    if (row.sids.length) {
      const full = await fetchAlert(auth, row.sids[0]);
      const body = (full.response_body ?? '').trim();
      console.warn(`  ${row.sids[0]} returned: ${body.slice(0, 200) || '(empty body)'}`);
    }
    console.warn('  repair: return an empty 200 from this handler before you do ' +
                 'any work, process the payload asynchronously, and allowlist ' +
                 "Twilio's egress ranges if a WAF is in front of it. Then " +
                 'backfill from Messages.json.');
  }

  const counts = reconcile(await listMessages(auth, account, since));
  console.log(`messages since ${since}: ${counts.total} total, ${counts.final} ` +
              `final, ${counts.open} still open, ${counts.failed} failed`);
  console.log(`${blind} status callback endpoint(s) failing, ${other} other ` +
              'webhook(s) with 11200');
  process.exitCode = blind ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Four rules carry this report. An <code>error_code</code> that arrives as the string <code>&quot;11200&quot;</code> still has to match. A logged URL with an appended query string still has to equal the configured value it came from. A callback set on a phone number counts as much as one set on a Messaging Service. And an 11200 on something that is <em>not</em> a configured callback has to be reported differently, because that one dropped a call.",
"test_py_file": "test_twilio_status_callback_audit.py",
"test_py": '''from twilio_status_callback_audit import (callback_endpoints, code_of, endpoint,
                                            reconcile, tally, verdict)


def alert(sid, url, code="11200", when="2026-03-02T10:00:00Z"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when, "log_level": "error"}


def test_code_of_reads_the_string_the_monitor_api_actually_returns():
    assert code_of({"error_code": "11200"}) == 11200
    assert code_of({"error_code": 11200}) == 11200
    assert code_of({"error_code": None}) is None
    assert code_of({}) is None


def test_endpoint_ignores_the_query_string_twilio_appends():
    logged = "https://hooks.example.com/twilio/status?MessageSid=SM1&AccountSid=AC1"
    assert endpoint(logged) == "hooks.example.com/twilio/status"
    assert endpoint("https://Hooks.Example.com/twilio/status/") == \\
        "hooks.example.com/twilio/status"
    assert endpoint("http://hooks.example.com:8443/twilio/status") == \\
        "hooks.example.com/twilio/status"
    assert endpoint(None) == ""


def test_callbacks_come_from_services_and_from_numbers():
    cbs = callback_endpoints(
        [{"sid": "MG1", "status_callback": "https://hooks.example.com/svc"}],
        [{"phone_number": "+15550001111",
          "status_callback": "https://hooks.example.com/pn/"}],
    )
    assert set(cbs) == {"hooks.example.com/svc", "hooks.example.com/pn"}
    assert cbs["hooks.example.com/pn"] == ["number +15550001111"]


def test_a_number_only_callback_is_still_a_callback():
    # Reading services alone is how a real status callback gets filed as some
    # other webhook and quietly dropped from the report.
    cbs = callback_endpoints([], [{"sid": "PN1",
                                   "status_callback": "https://hooks.example.com/pn"}])
    rows = tally([alert("NO1", "https://hooks.example.com/pn?MessageStatus=sent")], cbs)
    assert rows["hooks.example.com/pn"]["role"] == "status-callback"


def test_tally_skips_alerts_with_other_error_codes():
    cbs = callback_endpoints([], [])
    rows = tally([alert("NO1", "https://hooks.example.com/s", code="11205"),
                  alert("NO2", "https://hooks.example.com/s", code="11200")], cbs)
    assert rows["hooks.example.com/s"]["alerts"] == 1
    assert rows["hooks.example.com/s"]["sids"] == ["NO2"]


def test_tally_records_the_ends_of_the_window():
    cbs = callback_endpoints([], [])
    rows = tally([alert("NO1", "https://a.example.com/s", when="2026-03-02T10:00:00Z"),
                  alert("NO2", "https://a.example.com/s", when="2026-03-01T09:00:00Z"),
                  alert("NO3", "https://a.example.com/s", when="2026-03-03T11:00:00Z")],
                 cbs)
    row = rows["a.example.com/s"]
    assert row["first"] == "2026-03-01T09:00:00Z"
    assert row["last"] == "2026-03-03T11:00:00Z"


def test_an_11200_on_something_that_is_not_a_callback_is_a_dropped_call():
    state, detail = verdict({"alerts": 40, "role": "other-webhook"})
    assert state == "other-webhook"
    assert "fallback" in detail


def test_two_failures_on_a_callback_are_a_slow_handler_not_an_outage():
    state, detail = verdict({"alerts": 2, "role": "status-callback"})
    assert state == "intermittent"


def test_a_run_of_failures_on_a_callback_is_blindness():
    state, detail = verdict({"alerts": 900, "role": "status-callback"})
    assert state == "blind"
    assert "replay" in detail


def test_reconcile_counts_the_state_that_is_actually_true():
    counts = reconcile([{"status": "delivered"}, {"status": "queued"},
                        {"status": "undelivered"}, {"status": "sent"}])
    assert counts == {"total": 4, "final": 2, "open": 2, "failed": 1}
''',
"test_js_file": "twilio-status-callback-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  callbackEndpoints, codeOf, endpoint, reconcile, tally, verdict,
} from './twilio-status-callback-audit.mjs';

const alert = (sid, url, code = '11200', when = '2026-03-02T10:00:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when, log_level: 'error',
});

test('codeOf reads the string the Monitor API actually returns', () => {
  assert.equal(codeOf({ error_code: '11200' }), 11200);
  assert.equal(codeOf({ error_code: 11200 }), 11200);
  assert.equal(codeOf({ error_code: null }), null);
  assert.equal(codeOf({}), null);
});

test('endpoint ignores the query string Twilio appends', () => {
  const logged = 'https://hooks.example.com/twilio/status?MessageSid=SM1&AccountSid=AC1';
  assert.equal(endpoint(logged), 'hooks.example.com/twilio/status');
  assert.equal(endpoint('https://Hooks.Example.com/twilio/status/'),
    'hooks.example.com/twilio/status');
  assert.equal(endpoint('http://hooks.example.com:8443/twilio/status'),
    'hooks.example.com/twilio/status');
  assert.equal(endpoint(null), '');
});

test('callbacks come from services and from numbers', () => {
  const cbs = callbackEndpoints(
    [{ sid: 'MG1', status_callback: 'https://hooks.example.com/svc' }],
    [{ phone_number: '+15550001111', status_callback: 'https://hooks.example.com/pn/' }],
  );
  assert.deepEqual([...cbs.keys()].sort(),
    ['hooks.example.com/pn', 'hooks.example.com/svc']);
  assert.deepEqual(cbs.get('hooks.example.com/pn'), ['number +15550001111']);
});

test('a number-only callback is still a callback', () => {
  const cbs = callbackEndpoints([],
    [{ sid: 'PN1', status_callback: 'https://hooks.example.com/pn' }]);
  const rows = tally([alert('NO1', 'https://hooks.example.com/pn?MessageStatus=sent')], cbs);
  assert.equal(rows.get('hooks.example.com/pn').role, 'status-callback');
});

test('tally skips alerts with other error codes', () => {
  const cbs = callbackEndpoints([], []);
  const rows = tally([
    alert('NO1', 'https://hooks.example.com/s', '11205'),
    alert('NO2', 'https://hooks.example.com/s', '11200'),
  ], cbs);
  assert.equal(rows.get('hooks.example.com/s').alerts, 1);
  assert.deepEqual(rows.get('hooks.example.com/s').sids, ['NO2']);
});

test('tally records the ends of the window', () => {
  const cbs = callbackEndpoints([], []);
  const rows = tally([
    alert('NO1', 'https://a.example.com/s', '11200', '2026-03-02T10:00:00Z'),
    alert('NO2', 'https://a.example.com/s', '11200', '2026-03-01T09:00:00Z'),
    alert('NO3', 'https://a.example.com/s', '11200', '2026-03-03T11:00:00Z'),
  ], cbs);
  const row = rows.get('a.example.com/s');
  assert.equal(row.first, '2026-03-01T09:00:00Z');
  assert.equal(row.last, '2026-03-03T11:00:00Z');
});

test('an 11200 on something that is not a callback is a dropped call', () => {
  const [state, detail] = verdict({ alerts: 40, role: 'other-webhook' });
  assert.equal(state, 'other-webhook');
  assert.match(detail, /fallback/);
});

test('two failures on a callback are a slow handler, not an outage', () => {
  const [state] = verdict({ alerts: 2, role: 'status-callback' });
  assert.equal(state, 'intermittent');
});

test('a run of failures on a callback is blindness', () => {
  const [state, detail] = verdict({ alerts: 900, role: 'status-callback' });
  assert.equal(state, 'blind');
  assert.match(detail, /replay/);
});

test('reconcile counts the state that is actually true', () => {
  const counts = reconcile([{ status: 'delivered' }, { status: 'queued' },
    { status: 'undelivered' }, { status: 'sent' }]);
  assert.deepEqual(counts, { total: 4, final: 2, open: 2, failed: 1 });
});
''',
"faq": [
 ("Does Twilio retry a status callback that fails?",
  "Not in a way you can rely on. A callback is a best-effort push of an event that already happened; a non-2xx or a slow response is logged as 11200 and the event moves on. There is no replay endpoint, which is why the repair always ends with backfilling from the Messages list."),
 ("Why does the script compare host and path instead of the whole URL?",
  "Because Twilio appends its own parameters to the URL it fetches, so request_url on the alert is never character-for-character equal to the status_callback you configured. Scheme and a trailing slash differ too. Matching on lowercase host plus path is the comparison that survives all three."),
 ("Why can't I see what my endpoint returned in the alert list?",
  "Because response_body and response_headers are blank on every row of GET /v1/Alerts. They are populated only on the single-alert fetch, GET /v1/Alerts/{Sid}. The list tells you which endpoint is failing and how often; the body costs one request per alert, which is why the script caps how many it pulls."),
 ("How far back can this look?",
  "Thirty days. Alerts are retained for that long and no further, so a window longer than 30 days returns the same data under a more confident label. The script clamps the argument and says so rather than quietly returning less than you asked for."),
 ("Is an 11200 on a status callback as serious as one on my inbound handler?",
  "No, and that is why they are separate states. A failing status callback loses bookkeeping you can re-read from Messages.json. A failing inbound handler loses the call or the message itself, and the mitigation there is a fallback URL, not a backfill."),
],
"related": [
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never reach a final state"),
 ("/twilio/webhook-connection-timeout-11205/", "Twilio cannot open a connection to your webhook"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL"),
],
"citations": [CITE_11200, CITE_ALERTS, CITE_MSG, CITE_SERVICE],
},


{
"slug": "webhook-connection-timeout-11205",
"title": "Twilio cannot open a TCP connection to your webhook (11205)",
"description": "11205 means the handshake never completed, so your access log is empty. Whether that is a firewall, a dead host or a private address is one read away.",
"h1": "twilio cannot open a TCP connection to your webhook (11205)",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11205", "twilio http connection failure",
             "twilio webhook timeout", "twilio cannot reach webhook",
             "twilio webhook firewall allowlist"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You have the URL open in a browser tab and it works. Curl works. The health check is green. And the Twilio Debugger is filling with <code>11205 HTTP connection failure</code> for that exact URL, while your access log has no entry for it at all &mdash; not a 500, not a 404, nothing. The request never arrived, because the connection was never opened.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> and group alerts by the hostname in <code>request_url</code>, keeping the count of <code>11205</code> and the count of <code>11200</code> per host side by side.</p>
<p>That pairing is the diagnosis. 11205 means the TCP handshake never completed; 11200 means it completed and the response was wrong. A host with only 11205 was never reachable from the public internet &mdash; a firewall, a dead host, or a private address. A host with both answered <em>sometimes</em>, which is a capacity problem, not a network one.</p>""",
"problem": """<p>11205 is the failure that makes people doubt their own tools. Every check available from a laptop passes, because a laptop is not where Twilio dials from. Twilio connects from its own egress ranges over the public internet, and it allows 10 seconds to establish the connection and 15 seconds for the whole exchange. A WAF rule, a security group that lost a CIDR, a host that was replaced, or a URL that quietly points at an internal address all end the same way: nothing to connect to, inside the budget.</p>
<p>Because the request never reaches your application, nothing in your stack records it. There is no request ID, no trace, no error, no log line to grep for. The only party that saw the failure is Twilio, and the only place it wrote it down is the alerts list, which expires after 30 days.</p>""",
"why": """<p><strong>The request never reached your app, so your logs are the wrong place to look.</strong> This is the difference between 11205 and 11200 and it is worth internalising: 11200 is your application answering badly, 11205 is nothing answering at all. Searching your access log for evidence of an 11205 will always come back empty, and that emptiness is routinely misread as "Twilio never sent it".</p>
<p><strong>There is a connect budget and it is short.</strong> Twilio allows roughly 10 seconds to establish the TCP connection and 15 seconds in total. A backlog queue that is full, an autoscaler mid-scale, or a load balancer with no healthy targets can all blow through that while the host is technically alive, which is why a host that also has 11200 alerts is a different diagnosis from one that has only 11205.</p>
<p><strong>A private address cannot be allowlisted into working.</strong> If <code>request_url</code> points at <code>10.0.0.0/8</code>, <code>192.168.0.0/16</code>, <code>172.16.0.0/12</code>, <code>127.0.0.1</code> or <code>169.254.169.254</code>, no firewall change will help: the packets never leave Twilio's network toward anything you own. The classic case is a staging value copied into production, and the classic near miss is <code>172.32.x.x</code>, which looks private and is not &mdash; the block stops at <code>172.31</code>.</p>
<p><strong>Alerts are the only record and they expire.</strong> Thirty days of retention, and nothing else on the account remembers that a webhook was attempted and failed to connect. Any trend you want beyond that window has to be captured by something of yours, on a schedule, before the evidence ages out.</p>""",
"steps": [
 {"h": "Confirm the credential is on the account you think it is",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code> first. An API Key created on a different subaccount returns 401 here, and half of "no alerts found" reports are a key pointed at the wrong account rather than a healthy webhook. It also tells you the account is <code>active</code> rather than suspended.</p>"""},
 {"h": "Sweep the alerts once and keep both codes",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>. Do not filter to 11205 in the request &mdash; you want the 11200s from the same window, on the same hosts, because the comparison between them is the whole diagnosis.</p>"""},
 {"h": "Group by hostname, not by URL",
  "body": """<p>A connection failure happens before any path is requested, so the path is noise here. Strip it, lowercase the host, drop the port. Ten different endpoints on one dead host are one finding, and reporting them as ten is how a single expired security group looks like an application-wide collapse.</p>"""},
 {"h": "Ask whether the host is reachable from anywhere public",
  "body": """<p>Check the hostname for a private, loopback or link-local literal before you blame the network. If it is one of those the repair is the configured URL, not the firewall. Everything else is a real host, and the question becomes whether it ever answered.</p>"""},
 {"h": "Split firewall from capacity, then repair the right one",
  "body": """<p>Only 11205 on a host means nothing ever completed a handshake: allowlist Twilio's egress ranges at the firewall or WAF and confirm the host answers publicly on that port. Both 11205 and 11200 on a host means it answers some of the time: that is backlog, pool exhaustion or a scaling event, and the repair is capacity plus a handler that returns immediately. Verify the configured URL with <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code>.</p>"""},
],
"verify": """<p>Re-run over the same window after the firewall or capacity change. Every host should come back <code>clean</code>.</p>
<pre><code class="language-bash">python3 twilio_webhook_timeout_audit.py --days 2
# 3 host(s) with webhook alerts, 0 unreachable</code></pre>""",
"code_intro": "One alerts sweep, one account preflight, and a classifier that reads the two error codes against each other. The pure parts are the host extraction and the private-address test, because the second one is where this check is most often wrong in a way that looks right: <code>172.31</code> is private, <code>172.32</code> is not, and a report that gets that backwards sends someone to argue with a firewall team for a week.",
"py_file": "twilio_webhook_timeout_audit.py",
"py": '''"""Report webhook hosts Twilio cannot open a connection to (error 11205).

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
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_webhook_timeout_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

CONNECT_FAILURE = 11205
RETRIEVAL_FAILURE = 11200

# Alerts are retained 30 days and nothing else on the account remembers a
# webhook that failed to connect.
MAX_DAYS = 30


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API returns this as a string. Comparing the raw value against
    11205 is the mistake that makes the whole sweep report nothing.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def host_of(url):
    """Lowercase hostname from a webhook URL, without the port.

    A connection failure happens before a path is ever requested, so grouping by
    full URL splits one dead host into one finding per endpoint and makes a
    single expired firewall rule look like an application-wide collapse.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    if parts.hostname:
        return parts.hostname.lower()
    return str(url).strip().lower()


def unroutable(host):
    """Why Twilio can never open a connection to this host, or None.

    Twilio dials from the public internet. A private, loopback or link-local
    address is not a firewall problem and no allowlist will fix it: the packets
    never leave Twilio's network toward anything you own.

    The 172 range is the one worth writing a test for. RFC 1918 reserves
    172.16.0.0/12, which stops at 172.31 -- 172.32.0.0 is ordinary public space,
    and a check that treats it as private sends somebody to argue with a network
    team about an address that was never the problem.
    """
    h = (host or "").strip().lower().strip("[]")
    if not h:
        return "empty host"
    if h in ("localhost", "::1"):
        return "loopback"

    labels = h.split(".")
    if len(labels) == 4 and all(l.isdigit() and len(l) <= 3 for l in labels):
        octets = [int(l) for l in labels]
        if any(o > 255 for o in octets):
            return "malformed IP literal"
        a, b = octets[0], octets[1]
        if a == 0:
            return "unspecified address"
        if a == 127:
            return "loopback"
        if a == 10:
            return "private address"
        if a == 172 and 16 <= b <= 31:
            return "private address"
        if a == 192 and b == 168:
            return "private address"
        if a == 169 and b == 254:
            return "link-local address"
        if a == 100 and 64 <= b <= 127:
            return "carrier-grade NAT address"
    return None


def tally(alerts):
    """Group connection and retrieval failures by host.

    Pure, so the pairing can be tested without a network. Both codes are kept
    per host on purpose: 11205 says the handshake never completed, 11200 says it
    completed and the response was wrong, and a host carrying both answered some
    of the time.
    """
    out = {}
    for a in alerts:
        code = code_of(a)
        if code not in (CONNECT_FAILURE, RETRIEVAL_FAILURE):
            continue
        h = host_of(a.get("request_url"))
        row = out.setdefault(h, {"timeouts": 0, "retrievals": 0, "sids": [],
                                 "first": None, "last": None, "url": ""})
        if code == CONNECT_FAILURE:
            row["timeouts"] += 1
            if len(row["sids"]) < 3:
                row["sids"].append(a.get("sid"))
            row["url"] = row["url"] or (a.get("request_url") or "")
        else:
            row["retrievals"] += 1
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
    return out


def verdict(host, row, min_alerts=3):
    """Classify one host. Pure, so the thresholds and the order are visible.

    Returns (state, detail). The order matters: an unroutable address is
    reported even on a single alert, because one is proof, and a host that also
    has 11200 alerts is reported as capacity however few connection failures it
    has, because it demonstrably answers.
    """
    timeouts = int(row.get("timeouts") or 0)
    retrievals = int(row.get("retrievals") or 0)
    if not timeouts:
        return ("clean", "%d retrieval failure(s), no connection failures"
                % retrievals)

    reason = unroutable(host)
    if reason:
        return ("misconfigured",
                "%d x 11205 against a %s. No firewall change reaches this: the "
                "configured URL points somewhere Twilio can never dial, so the "
                "repair is the URL." % (timeouts, reason))

    if retrievals:
        return ("flapping",
                "%d x 11205 and %d x 11200 on the same host. It answers some of "
                "the time, so this is capacity rather than a firewall: a full "
                "backlog queue or an exhausted pool inside the 10 second connect "
                "budget." % (timeouts, retrievals))

    if timeouts < min_alerts:
        return ("isolated",
                "%d x 11205 and nothing else. Too few to call an outage; a "
                "restart or a scaling event closes the listener for a moment and "
                "looks exactly like this." % timeouts)

    return ("unreachable",
            "%d x 11205 and not one 11200. Nothing ever completed a handshake, "
            "so your access log has no record of any of it: a firewall dropping "
            "Twilio's egress ranges, or a host that is gone." % timeouts)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def account_preflight(session, account):
    """Confirm the key really belongs to this account before reporting nothing.

    An API Key made on a different subaccount 401s here rather than returning an
    empty alerts list, which is the difference between "no problems" and "no
    permission".
    """
    return get(session, "%s/Accounts/%s.json" % (BASE, account))


def list_alerts(session, since, limit, log_level="error"):
    """Page the Monitor alerts. next_page_url is absolute on this API."""
    url = MONITOR + "/Alerts"
    params = {"LogLevel": log_level, "StartDate": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=2,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    ap.add_argument("--min-alerts", type=int, default=3,
                    help="fewer connection failures than this is reported as isolated")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    days = args.days
    if days > MAX_DAYS:
        log.warning("alerts are retained %d days; reading %d instead of %d",
                    MAX_DAYS, MAX_DAYS, days)
        days = MAX_DAYS

    session = requests.Session()
    session.auth = (key, secret)

    acct = account_preflight(session, account)
    log.info("account %s (%s), status %s", account, acct.get("friendly_name"),
             acct.get("status"))

    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    alerts = list_alerts(session, since, args.max_alerts)
    rows = tally(alerts)
    bad = 0
    for host, row in sorted(rows.items()):
        state, detail = verdict(host, row, args.min_alerts)
        line = "%-14s %s  %s" % (state, host or "(no host)", detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  first %s, last %s, sample %s", row["first"], row["last"],
                    row["url"] or "(none)")
        log.warning("  alert sids: %s", ", ".join(str(s) for s in row["sids"]))
        if state == "misconfigured":
            log.warning("  repair: repoint the webhook at a publicly resolvable "
                        "host. Check VoiceUrl and SmsUrl on the number with GET "
                        "/2010-04-01/Accounts/%s/IncomingPhoneNumbers.json",
                        account)
        elif state == "flapping":
            log.warning("  repair: acknowledge with an empty 200 immediately and "
                        "do the work asynchronously, then give the listener "
                        "enough backlog and workers to accept a connection "
                        "within 10 seconds.")
        else:
            log.warning("  repair: allowlist Twilio's egress ranges at the "
                        "firewall or WAF and confirm the host answers publicly "
                        "on that port. Nothing in your own logs will confirm "
                        "this: the request never arrived.")

    log.info("%d host(s) with webhook alerts, %d unreachable", len(rows), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-webhook-timeout-audit.mjs",
"js": '''/**
 * Report webhook hosts Twilio cannot open a connection to (error 11205).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const CONNECT_FAILURE = 11205;
const RETRIEVAL_FAILURE = 11200;

// Alerts are retained 30 days and nothing else remembers a failed connection.
const MAX_DAYS = 30;

/**
 * Read error_code off an alert as a number, or null. The Monitor API returns it
 * as a string, and comparing the raw value against 11205 reports nothing.
 */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Lowercase hostname from a webhook URL, without the port. A connection failure
 * happens before any path is requested, so grouping by full URL turns one dead
 * host into one finding per endpoint.
 */
export function hostOf(url) {
  if (!url) return '';
  const raw = String(url).trim();
  try {
    const u = new URL(raw);
    if (u.hostname) return u.hostname.toLowerCase();
  } catch {
    return raw.toLowerCase();
  }
  return raw.toLowerCase();
}

/**
 * Why Twilio can never open a connection to this host, or null. Twilio dials
 * from the public internet, so a private or loopback address is not a firewall
 * problem and no allowlist will fix it.
 *
 * RFC 1918 reserves 172.16.0.0/12, which stops at 172.31. Treating 172.32 as
 * private sends somebody to argue with a network team about an address that was
 * never the problem.
 */
export function unroutable(host) {
  let h = String(host ?? '').trim().toLowerCase();
  while (h.startsWith('[')) h = h.slice(1);
  while (h.endsWith(']')) h = h.slice(0, -1);
  if (!h) return 'empty host';
  if (h === 'localhost' || h === '::1') return 'loopback';

  const labels = h.split('.');
  const numeric = labels.length === 4
    && labels.every((l) => l.length > 0 && l.length <= 3
      && [...l].every((c) => c >= '0' && c <= '9'));
  if (numeric) {
    const o = labels.map((l) => Number(l));
    if (o.some((n) => n > 255)) return 'malformed IP literal';
    const [a, b] = o;
    if (a === 0) return 'unspecified address';
    if (a === 127) return 'loopback';
    if (a === 10) return 'private address';
    if (a === 172 && b >= 16 && b <= 31) return 'private address';
    if (a === 192 && b === 168) return 'private address';
    if (a === 169 && b === 254) return 'link-local address';
    if (a === 100 && b >= 64 && b <= 127) return 'carrier-grade NAT address';
  }
  return null;
}

/**
 * Group connection and retrieval failures by host. Pure. Both codes are kept
 * per host because the comparison between them is the diagnosis.
 */
export function tally(alerts) {
  const out = new Map();
  for (const a of alerts) {
    const code = codeOf(a);
    if (code !== CONNECT_FAILURE && code !== RETRIEVAL_FAILURE) continue;
    const h = hostOf(a.request_url);
    if (!out.has(h)) {
      out.set(h, { timeouts: 0, retrievals: 0, sids: [], first: null, last: null, url: '' });
    }
    const row = out.get(h);
    if (code === CONNECT_FAILURE) {
      row.timeouts += 1;
      if (row.sids.length < 3) row.sids.push(a.sid);
      row.url = row.url || (a.request_url ?? '');
    } else {
      row.retrievals += 1;
    }
    const when = a.date_generated ?? '';
    if (when) {
      row.first = row.first === null || when < row.first ? when : row.first;
      row.last = row.last === null || when > row.last ? when : row.last;
    }
  }
  return out;
}

/**
 * Classify one host. Pure. The order matters: an unroutable address is reported
 * on a single alert because one is proof, and a host that also has 11200 alerts
 * is capacity however few connection failures it has, because it answers.
 * Returns [state, detail].
 */
export function verdict(host, row, minAlerts = 3) {
  const timeouts = Number(row.timeouts ?? 0);
  const retrievals = Number(row.retrievals ?? 0);
  if (!timeouts) {
    return ['clean', `${retrievals} retrieval failure(s), no connection failures`];
  }

  const reason = unroutable(host);
  if (reason) {
    return ['misconfigured',
      `${timeouts} x 11205 against a ${reason}. No firewall change reaches ` +
      'this: the configured URL points somewhere Twilio can never dial, so the ' +
      'repair is the URL.'];
  }

  if (retrievals) {
    return ['flapping',
      `${timeouts} x 11205 and ${retrievals} x 11200 on the same host. It ` +
      'answers some of the time, so this is capacity rather than a firewall: a ' +
      'full backlog queue or an exhausted pool inside the 10 second connect budget.'];
  }

  if (timeouts < minAlerts) {
    return ['isolated',
      `${timeouts} x 11205 and nothing else. Too few to call an outage; a ` +
      'restart or a scaling event closes the listener for a moment and looks ' +
      'exactly like this.'];
  }

  return ['unreachable',
    `${timeouts} x 11205 and not one 11200. Nothing ever completed a handshake, ` +
    'so your access log has no record of any of it: a firewall dropping ' +
    "Twilio's egress ranges, or a host that is gone."];
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

/** Confirm the key belongs to this account before reporting an empty result. */
export async function accountPreflight(auth, account) {
  return get(auth, `${BASE}/Accounts/${account}.json`);
}

export async function listAlerts(auth, since, limit = 10000, logLevel = 'error') {
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

  let days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 2) || 2;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }

  const acct = await accountPreflight(auth, account);
  console.log(`account ${account} (${acct.friendly_name}), status ${acct.status}`);

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const alerts = await listAlerts(auth, since);
  const rows = tally(alerts);
  let bad = 0;
  for (const [host, row] of [...rows.entries()].sort()) {
    const [state, detail] = verdict(host, row);
    const line = `${state.padEnd(14)} ${host || '(no host)'}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  first ${row.first}, last ${row.last}, sample ${row.url || '(none)'}`);
    console.warn(`  alert sids: ${row.sids.join(', ')}`);
    if (state === 'misconfigured') {
      console.warn('  repair: repoint the webhook at a publicly resolvable host. ' +
                   `Check VoiceUrl and SmsUrl with GET /2010-04-01/Accounts/${account}` +
                   '/IncomingPhoneNumbers.json');
    } else if (state === 'flapping') {
      console.warn('  repair: acknowledge with an empty 200 immediately and do ' +
                   'the work asynchronously, then give the listener enough ' +
                   'backlog and workers to accept a connection within 10 seconds.');
    } else {
      console.warn("  repair: allowlist Twilio's egress ranges at the firewall " +
                   'or WAF and confirm the host answers publicly on that port. ' +
                   'Nothing in your own logs will confirm this: the request ' +
                   'never arrived.');
    }
  }

  console.log(`${rows.size} host(s) with webhook alerts, ${bad} unreachable`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The address test is the one that earns its keep. <code>172.31.5.4</code> is private and <code>172.32.5.4</code> is not, and a report that confuses them costs a network team a week. The rest pins down the pairing: a host with only 11205 is unreachable, the same host with a single 11200 beside it is a capacity problem, and those two sentences send you to different people.",
"test_py_file": "test_twilio_webhook_timeout_audit.py",
"test_py": '''from twilio_webhook_timeout_audit import code_of, host_of, tally, unroutable, verdict


def alert(sid, url, code="11205", when="2026-04-01T12:00:00Z"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when, "log_level": "error"}


def test_code_of_reads_the_string_the_monitor_api_returns():
    assert code_of({"error_code": "11205"}) == 11205
    assert code_of({"error_code": 11205}) == 11205
    assert code_of({"error_code": ""}) is None


def test_host_of_drops_the_path_and_the_port():
    assert host_of("https://Hooks.Example.com:8443/voice?CallSid=CA1") == \\
        "hooks.example.com"
    assert host_of("https://hooks.example.com/sms") == "hooks.example.com"
    assert host_of(None) == ""


def test_the_172_block_stops_at_31():
    # RFC 1918 reserves 172.16.0.0/12. Getting this wrong sends somebody to
    # argue with a network team about a perfectly public address.
    assert unroutable("172.16.0.1") == "private address"
    assert unroutable("172.31.255.254") == "private address"
    assert unroutable("172.32.0.1") is None
    assert unroutable("172.15.0.1") is None


def test_the_other_addresses_twilio_can_never_dial():
    assert unroutable("127.0.0.1") == "loopback"
    assert unroutable("localhost") == "loopback"
    assert unroutable("10.4.2.1") == "private address"
    assert unroutable("192.168.1.10") == "private address"
    assert unroutable("169.254.169.254") == "link-local address"
    assert unroutable("100.100.0.1") == "carrier-grade NAT address"
    assert unroutable("hooks.example.com") is None
    assert unroutable("999.1.1.1") == "malformed IP literal"


def test_tally_keeps_both_codes_on_one_host():
    rows = tally([alert("NO1", "https://hooks.example.com/voice"),
                  alert("NO2", "https://hooks.example.com/sms"),
                  alert("NO3", "https://hooks.example.com/sms", code="11200"),
                  alert("NO4", "https://hooks.example.com/sms", code="11236")])
    row = rows["hooks.example.com"]
    assert row["timeouts"] == 2
    assert row["retrievals"] == 1
    assert row["sids"] == ["NO1", "NO2"]


def test_a_private_address_is_reported_on_a_single_alert():
    state, detail = verdict("10.0.0.7", {"timeouts": 1, "retrievals": 0})
    assert state == "misconfigured"
    assert "No firewall change" in detail


def test_a_host_with_both_codes_is_capacity_not_a_firewall():
    state, detail = verdict("hooks.example.com", {"timeouts": 40, "retrievals": 2})
    assert state == "flapping"
    assert "10 second" in detail


def test_a_run_of_timeouts_with_no_replies_is_unreachable():
    state, detail = verdict("hooks.example.com", {"timeouts": 40, "retrievals": 0})
    assert state == "unreachable"
    assert "access log" in detail


def test_one_timeout_is_a_restart_not_an_outage():
    state, _ = verdict("hooks.example.com", {"timeouts": 1, "retrievals": 0})
    assert state == "isolated"


def test_retrieval_failures_alone_are_not_this_report():
    state, _ = verdict("hooks.example.com", {"timeouts": 0, "retrievals": 90})
    assert state == "clean"
''',
"test_js_file": "twilio-webhook-timeout-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  codeOf, hostOf, tally, unroutable, verdict,
} from './twilio-webhook-timeout-audit.mjs';

const alert = (sid, url, code = '11205', when = '2026-04-01T12:00:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when, log_level: 'error',
});

test('codeOf reads the string the Monitor API returns', () => {
  assert.equal(codeOf({ error_code: '11205' }), 11205);
  assert.equal(codeOf({ error_code: 11205 }), 11205);
  assert.equal(codeOf({ error_code: '' }), null);
});

test('hostOf drops the path and the port', () => {
  assert.equal(hostOf('https://Hooks.Example.com:8443/voice?CallSid=CA1'),
    'hooks.example.com');
  assert.equal(hostOf('https://hooks.example.com/sms'), 'hooks.example.com');
  assert.equal(hostOf(null), '');
});

test('the 172 block stops at 31', () => {
  assert.equal(unroutable('172.16.0.1'), 'private address');
  assert.equal(unroutable('172.31.255.254'), 'private address');
  assert.equal(unroutable('172.32.0.1'), null);
  assert.equal(unroutable('172.15.0.1'), null);
});

test('the other addresses Twilio can never dial', () => {
  assert.equal(unroutable('127.0.0.1'), 'loopback');
  assert.equal(unroutable('localhost'), 'loopback');
  assert.equal(unroutable('10.4.2.1'), 'private address');
  assert.equal(unroutable('192.168.1.10'), 'private address');
  assert.equal(unroutable('169.254.169.254'), 'link-local address');
  assert.equal(unroutable('100.100.0.1'), 'carrier-grade NAT address');
  assert.equal(unroutable('hooks.example.com'), null);
  assert.equal(unroutable('999.1.1.1'), 'malformed IP literal');
});

test('tally keeps both codes on one host', () => {
  const rows = tally([
    alert('NO1', 'https://hooks.example.com/voice'),
    alert('NO2', 'https://hooks.example.com/sms'),
    alert('NO3', 'https://hooks.example.com/sms', '11200'),
    alert('NO4', 'https://hooks.example.com/sms', '11236'),
  ]);
  const row = rows.get('hooks.example.com');
  assert.equal(row.timeouts, 2);
  assert.equal(row.retrievals, 1);
  assert.deepEqual(row.sids, ['NO1', 'NO2']);
});

test('a private address is reported on a single alert', () => {
  const [state, detail] = verdict('10.0.0.7', { timeouts: 1, retrievals: 0 });
  assert.equal(state, 'misconfigured');
  assert.match(detail, /No firewall change/);
});

test('a host with both codes is capacity, not a firewall', () => {
  const [state, detail] = verdict('hooks.example.com', { timeouts: 40, retrievals: 2 });
  assert.equal(state, 'flapping');
  assert.match(detail, /10 second/);
});

test('a run of timeouts with no replies is unreachable', () => {
  const [state, detail] = verdict('hooks.example.com', { timeouts: 40, retrievals: 0 });
  assert.equal(state, 'unreachable');
  assert.match(detail, /access log/);
});

test('one timeout is a restart, not an outage', () => {
  const [state] = verdict('hooks.example.com', { timeouts: 1, retrievals: 0 });
  assert.equal(state, 'isolated');
});

test('retrieval failures alone are not this report', () => {
  const [state] = verdict('hooks.example.com', { timeouts: 0, retrievals: 90 });
  assert.equal(state, 'clean');
});
''',
"faq": [
 ("What is the difference between 11205 and 11200?",
  "11205 means Twilio could not open the TCP connection at all, so the request never reached your application and your access log has no trace of it. 11200 means the connection succeeded and the response was unusable - a non-2xx, or nothing back inside the HTTP window. The first is a network fact, the second is your code."),
 ("The URL works from my laptop. Why does Twilio time out?",
  "Because Twilio dials from its own egress ranges over the public internet, not from your laptop or your VPN. A WAF rule, a security group that lost a CIDR, or a host that only answers on a private interface all pass every test you can run locally and still fail every webhook."),
 ("How long does Twilio wait?",
  "Roughly 10 seconds to establish the connection and 15 seconds for the whole exchange. That budget is why a host under load can produce connection failures while it is still technically alive: the listener backlog is full and the handshake never completes in time."),
 ("Why does the script report a private address separately?",
  "Because no firewall change will ever fix it. If the configured URL points at 10.x, 192.168.x, 172.16-31.x, 127.0.0.1 or 169.254.169.254, the packets never leave Twilio's network. That finding is worth reporting on a single alert, where a public host needs a few before it means anything."),
 ("Can the script fix the webhook URL for me?",
  "No. Everything here is a GET, including the account preflight, so an API Key with read access is all it can use. It prints the number, the field and the repair, and a human runs it - a script holding a credential that can place calls should not be editing routing at 3am."),
],
"related": [
 ("/twilio/webhook-dns-resolution-failure-11210/", "A webhook hostname with no public DNS record"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL"),
 ("/twilio/status-callback-webhook-failing-11200/", "Status callbacks failing with 11200"),
],
"citations": [CITE_11205, CITE_11200, CITE_ALERTS, CITE_WEBHOOKS],
},

{
"slug": "webhook-tls-certificate-expired-11236",
"title": "An expired webhook certificate fails every request with 11236",
"description": "11236 arrives at a sharp timestamp boundary and every number on that hostname breaks at once. Alerts are kept 30 days, which bounds what you can see.",
"h1": "an expired webhook certificate fails every request with 11236",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11236", "twilio certificate expired",
             "twilio webhook ssl certificate invalid", "twilio tls webhook failure",
             "twilio certificate invalid certificate expired"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "At 14:07 UTC everything was fine. At 14:08 every webhook on one hostname started failing with <code>11236 Certificate Invalid - Certificate Expired</code>, and it has not stopped since. No deploy went out. No configuration changed. A renewal job stopped working ninety days ago and nobody noticed, because a certificate does not degrade &mdash; it works perfectly until the second it does not.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code>, keep <code>error_code</code> <code>11236</code>, and group by the host <em>and port</em> in <code>request_url</code>. The <code>date_generated</code> of the first alert is the expiry moment; the last one tells you whether it is still broken.</p>
<p>Then read <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> and list every number whose <code>voice_url</code>, <code>sms_url</code>, <code>status_callback</code> or either fallback points at that host. A certificate covers a hostname, so all of them broke in the same second &mdash; and if a fallback is on the same host, it expired too.</p>""",
"problem": """<p>Twilio validates the certificate chain before it sends anything. An expired leaf fails validation, so the request is never made and your server never sees a connection. That is why this failure has no gradient: it is not slower, not flaky, not partial. Every HTTPS webhook to that hostname stops at the same instant, and every one of them keeps stopping until somebody renews.</p>
<p>The reason it survives long enough to become an outage is that certificates are usually somebody else's job. Renewal is automated, the automation is invisible, and the failure mode of the automation is silence. A renewal hook that broke when a package was upgraded, a certificate that lives on a failover node that never runs the renewal, an internal CA nobody documented &mdash; all of them look identical until the expiry date arrives.</p>""",
"why": """<p><strong>A certificate is presented by a listener, not by a domain.</strong> Two ports on the same hostname can serve two different certificates, and only one of them may be the stale one. Grouping by hostname alone merges a healthy <code>:443</code> with a broken <code>:8443</code> and produces a report that says the host is half broken, which is not a state anyone can act on.</p>
<p><strong>The first alert is the expiry moment, unless it is not.</strong> <code>date_generated</code> on the earliest 11236 is normally the second the certificate lapsed. But alerts are retained 30 days, so if the earliest alert sits right at the start of your window, the real expiry is older than the window and the timestamp you are reading is the retention boundary, not the event. Those two look identical and mean very different things.</p>
<p><strong>Failures spread thinly over days are not one expiry.</strong> A truly expired certificate fails everything, continuously. A handful of 11236s scattered over a week means most requests succeeded, which means most requests reached a different machine &mdash; one node behind a load balancer still serving an old certificate, or a failover host nobody renewed.</p>
<p><strong>The blast radius is every number on that hostname.</strong> Certificates are per hostname, so voice, messaging and status callbacks pointing at it all failed together. The worst version is a fallback URL on the same host as the primary: the fallback was supposed to be the safety net and it expired at exactly the same instant.</p>""",
"steps": [
 {"h": "Sweep the alerts for 11236",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>. Read <code>error_code</code> as an integer &mdash; the Monitor API returns it as a string. Keep <code>date_generated</code> for every alert; the timestamps are the entire diagnosis here.</p>"""},
 {"h": "Group by host and port, not by hostname",
  "body": """<p>Keep the port when the URL carries a non-default one. A certificate belongs to whatever is terminating TLS on that port, and one hostname can front several listeners with independent renewal stories.</p>"""},
 {"h": "Find the cliff, and check it is not the retention edge",
  "body": """<p>The first <code>date_generated</code> is the expiry moment. If it lands within an hour of the start of your window, treat it as unknown instead: alerts stop at 30 days, so an old expiry produces an oldest-alert timestamp that is really just the edge of what Twilio still remembers.</p>"""},
 {"h": "Separate a hard expiry from one stale node",
  "body": """<p>Compare the number of alerts against the span they cover. Thousands of failures over two days is an expired certificate. Twelve failures spread over five days is one machine in a pool: most requests succeeded, which is impossible if the certificate the hostname serves is expired.</p>"""},
 {"h": "Measure the blast radius, then renew",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> and list every number with any URL field on that host. Renew the certificate and reload the terminating server or load balancer &mdash; there is no Twilio-side setting for this. Then move any fallback URL onto a different hostname, because a fallback that shares a certificate with the primary is not a fallback.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the renewal. The host should disappear from the report entirely.</p>
<pre><code class="language-bash">python3 twilio_webhook_cert_audit.py --days 1
# 0 host(s) failing certificate validation</code></pre>""",
"code_intro": "One alerts sweep, one numbers list, and a classifier built entirely out of timestamps. The pure parts are the host-and-port key, the timestamp parsing, and the verdict &mdash; the last one because deciding that an oldest alert is the retention boundary rather than an expiry is a judgement call, and judgement calls belong somewhere a test can hold them still.",
"py_file": "twilio_webhook_cert_audit.py",
"py": '''"""Report webhook hosts whose TLS certificate has expired (error 11236).

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
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_webhook_cert_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

CERT_EXPIRED = 11236

# Alerts are retained 30 days. An expiry older than that cannot be dated from
# this API at all, which the verdict has to say out loud rather than guess.
MAX_DAYS = 30

# Every field on a phone number that can carry a URL. A certificate covers the
# hostname, so all of these broke at the same second.
URL_FIELDS = ("voice_url", "voice_fallback_url", "sms_url", "sms_fallback_url",
              "status_callback")
DEFAULT_PORTS = {"http": 80, "https": 443}


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API returns this as a string. Comparing the raw value against
    11236 is the mistake that makes the sweep report a healthy account.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def cert_host(url):
    """Host, plus the port when it is not the default for the scheme.

    A certificate is presented by whatever terminates TLS on a port, not by a
    domain. Two listeners on one hostname can serve two certificates with two
    different renewal stories, and merging them produces a report that says a
    host is half broken.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        return ""
    try:
        port = parts.port
    except ValueError:
        port = None
    if port and port != DEFAULT_PORTS.get((parts.scheme or "").lower()):
        return "%s:%d" % (host, port)
    return host


def at(iso):
    """Epoch seconds for a Monitor timestamp, or None.

    date_generated is ISO 8601 in UTC. Fractional seconds and the trailing Z are
    trimmed rather than parsed, and a value with no offset is read as UTC, so
    this behaves identically on a machine whose clock is not.
    """
    if not iso:
        return None
    s = str(iso).strip()
    if s.endswith("Z"):
        s = s[:-1]
    s = s[:19]
    try:
        naive = dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
    return naive.replace(tzinfo=dt.timezone.utc).timestamp()


def sweep(alerts):
    """Group certificate failures by host and port.

    Pure, so the grouping can be tested without a network. ISO 8601 UTC strings
    order correctly as strings, so the ends of each run need no parsing here.
    """
    out = {}
    for a in alerts:
        if code_of(a) != CERT_EXPIRED:
            continue
        key = cert_host(a.get("request_url"))
        row = out.setdefault(key, {"alerts": 0, "sids": [], "first": None,
                                   "last": None, "url": ""})
        row["alerts"] += 1
        if len(row["sids"]) < 3:
            row["sids"].append(a.get("sid"))
        row["url"] = row["url"] or (a.get("request_url") or "")
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
    return out


def verdict(row, window_start, window_end, edge_minutes=60, quiet_minutes=180):
    """Classify one host from its timestamps alone. Pure.

    The order is deliberate. A host that stopped failing needs no repair
    whatever its history, so recovery is checked first. An oldest alert sitting
    on the edge of the retention window is reported as undatable rather than
    dated, because those two are indistinguishable and only one of them is true.

    Returns (state, detail).
    """
    n = int(row.get("alerts") or 0)
    if not n:
        return ("clean", "no 11236 in the window")

    first, last = at(row.get("first")), at(row.get("last"))
    start, end = at(window_start), at(window_end)
    if first is None or last is None or start is None or end is None:
        return ("undated", "%d x 11236 with unreadable timestamps" % n)

    if last <= end - quiet_minutes * 60:
        down = (last - first) / 3600.0
        return ("recovered",
                "%d x 11236, none in the last %d minutes. The certificate was "
                "replaced; the outage ran about %.1f hour(s) from %s."
                % (n, quiet_minutes, down, row.get("first")))

    if first <= start + edge_minutes * 60:
        return ("at-retention-edge",
                "%d x 11236, the oldest right at the start of the window. "
                "Alerts are kept %d days, so the expiry is older than that and "
                "this timestamp is the retention boundary, not the event."
                % (n, MAX_DAYS))

    span = (last - first) / 3600.0
    if n >= 2 and span >= 24 and n < span:
        return ("sporadic",
                "%d x 11236 spread over %.0f hour(s). An expired certificate "
                "fails everything, so most requests reaching this host "
                "succeeded: one node behind the balancer is still serving a "
                "stale certificate." % (n, span))

    return ("expired",
            "%d x 11236, first at %s and still failing. Every HTTPS webhook to "
            "this host has been refused since that moment, before any request "
            "was sent." % (n, row.get("first")))


def exposure(numbers, host):
    """Which numbers point at this host, and on which fields. Pure.

    The field list matters more than the count. When a fallback URL sits on the
    same host as the primary, the fallback was covered by the same certificate
    and expired in the same second, so there was never a second chance.
    """
    out = []
    for n in numbers or []:
        fields = [f for f in URL_FIELDS if cert_host(n.get(f)) == host]
        if not fields:
            continue
        primary = [f for f in fields if f in ("voice_url", "sms_url")]
        fallback = [f for f in fields if f.endswith("fallback_url")]
        out.append({
            "number": n.get("phone_number") or n.get("sid") or "?",
            "fields": fields,
            "fallback_shares_host": bool(primary and fallback),
        })
    return out


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, since, limit, log_level="error"):
    """Page the Monitor alerts. next_page_url is absolute on this API."""
    url = MONITOR + "/Alerts"
    params = {"LogLevel": log_level, "StartDate": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def list_numbers(session, account, limit=2000):
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    ap.add_argument("--quiet-minutes", type=int, default=180,
                    help="silence for this long counts as recovered")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    days = args.days
    if days > MAX_DAYS:
        log.warning("alerts are retained %d days; reading %d instead of %d",
                    MAX_DAYS, MAX_DAYS, days)
        days = MAX_DAYS

    session = requests.Session()
    session.auth = (key, secret)

    now = dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(days=days)).date().isoformat()
    window_start = since + "T00:00:00Z"
    window_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    alerts = list_alerts(session, since, args.max_alerts)
    rows = sweep(alerts)
    if not rows:
        log.info("no 11236 since %s across %d alert(s)", since, len(alerts))
        return 0

    numbers = list_numbers(session, account)
    bad = 0
    for host, row in sorted(rows.items()):
        state, detail = verdict(row, window_start, window_end,
                                quiet_minutes=args.quiet_minutes)
        line = "%-18s %s  %s" % (state, host or "(no host)", detail)
        if state in ("clean", "recovered"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  sample %s, alert sids: %s", row["url"] or "(none)",
                    ", ".join(str(s) for s in row["sids"]))
        hit = exposure(numbers, host)
        for row2 in hit:
            log.warning("  %s uses it on %s%s", row2["number"],
                        ", ".join(row2["fields"]),
                        "  <- the fallback is on the same certificate"
                        if row2["fallback_shares_host"] else "")
        log.warning("  %d number(s) affected", len(hit))
        log.warning("  repair: renew the certificate and reload the terminating "
                    "server or load balancer. There is no Twilio-side setting "
                    "for this. Then move fallback URLs onto a hostname with a "
                    "separate certificate.")

    log.info("%d host(s) failing certificate validation", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-webhook-cert-audit.mjs",
"js": '''/**
 * Report webhook hosts whose TLS certificate has expired (error 11236).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const CERT_EXPIRED = 11236;

// Alerts are retained 30 days. An older expiry cannot be dated from this API.
const MAX_DAYS = 30;

// Every field on a phone number that can carry a URL.
const URL_FIELDS = ['voice_url', 'voice_fallback_url', 'sms_url',
  'sms_fallback_url', 'status_callback'];
const DEFAULT_PORTS = { 'http:': '80', 'https:': '443' };

/**
 * Read error_code off an alert as a number, or null. The Monitor API returns it
 * as a string, and a raw comparison reports a healthy account.
 */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Host, plus the port when it is not the default for the scheme. A certificate
 * is presented by whatever terminates TLS on a port, not by a domain.
 */
export function certHost(url) {
  if (!url) return '';
  let u;
  try {
    u = new URL(String(url).trim());
  } catch {
    return '';
  }
  const host = u.hostname.toLowerCase();
  if (!host) return '';
  if (u.port && u.port !== DEFAULT_PORTS[u.protocol]) return `${host}:${u.port}`;
  return host;
}

/**
 * Epoch seconds for a Monitor timestamp, or null. A value with no offset is
 * read as UTC, so this behaves the same on a machine whose clock is not.
 */
export function at(iso) {
  if (!iso) return null;
  let s = String(iso).trim();
  if (s.endsWith('Z')) s = s.slice(0, -1);
  s = `${s.slice(0, 19)}Z`;
  const ms = Date.parse(s);
  return Number.isFinite(ms) ? ms / 1000 : null;
}

/**
 * Group certificate failures by host and port. Pure. ISO 8601 UTC strings order
 * correctly as strings, so the ends of each run need no parsing here.
 */
export function sweep(alerts) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== CERT_EXPIRED) continue;
    const key = certHost(a.request_url);
    if (!out.has(key)) {
      out.set(key, { alerts: 0, sids: [], first: null, last: null, url: '' });
    }
    const row = out.get(key);
    row.alerts += 1;
    if (row.sids.length < 3) row.sids.push(a.sid);
    row.url = row.url || (a.request_url ?? '');
    const when = a.date_generated ?? '';
    if (when) {
      row.first = row.first === null || when < row.first ? when : row.first;
      row.last = row.last === null || when > row.last ? when : row.last;
    }
  }
  return out;
}

/**
 * Classify one host from its timestamps alone. Pure. Recovery is checked first
 * because a host that stopped failing needs no repair whatever its history, and
 * an oldest alert on the edge of the retention window is reported as undatable
 * rather than dated. Returns [state, detail].
 */
export function verdict(row, windowStart, windowEnd, edgeMinutes = 60, quietMinutes = 180) {
  const n = Number(row.alerts ?? 0);
  if (!n) return ['clean', 'no 11236 in the window'];

  const first = at(row.first);
  const last = at(row.last);
  const start = at(windowStart);
  const end = at(windowEnd);
  if (first === null || last === null || start === null || end === null) {
    return ['undated', `${n} x 11236 with unreadable timestamps`];
  }

  if (last <= end - quietMinutes * 60) {
    const down = ((last - first) / 3600).toFixed(1);
    return ['recovered',
      `${n} x 11236, none in the last ${quietMinutes} minutes. The certificate ` +
      `was replaced; the outage ran about ${down} hour(s) from ${row.first}.`];
  }

  if (first <= start + edgeMinutes * 60) {
    return ['at-retention-edge',
      `${n} x 11236, the oldest right at the start of the window. Alerts are ` +
      `kept ${MAX_DAYS} days, so the expiry is older than that and this ` +
      'timestamp is the retention boundary, not the event.'];
  }

  const span = (last - first) / 3600;
  if (n >= 2 && span >= 24 && n < span) {
    return ['sporadic',
      `${n} x 11236 spread over ${span.toFixed(0)} hour(s). An expired ` +
      'certificate fails everything, so most requests reaching this host ' +
      'succeeded: one node behind the balancer is still serving a stale ' +
      'certificate.'];
  }

  return ['expired',
    `${n} x 11236, first at ${row.first} and still failing. Every HTTPS webhook ` +
    'to this host has been refused since that moment, before any request was sent.'];
}

/**
 * Which numbers point at this host, and on which fields. Pure. A fallback on the
 * same host was covered by the same certificate and expired in the same second.
 */
export function exposure(numbers, host) {
  const out = [];
  for (const n of numbers ?? []) {
    const fields = URL_FIELDS.filter((f) => certHost(n[f]) === host);
    if (!fields.length) continue;
    const primary = fields.some((f) => f === 'voice_url' || f === 'sms_url');
    const fallback = fields.some((f) => f.endsWith('fallback_url'));
    out.push({
      number: n.phone_number ?? n.sid ?? '?',
      fields,
      fallback_shares_host: primary && fallback,
    });
  }
  return out;
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

export async function listAlerts(auth, since, limit = 10000, logLevel = 'error') {
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

async function listNumbers(auth, account) {
  let url = `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`;
  let params = { PageSize: 1000 };
  const out = [];
  while (url) {
    const page = await get(auth, url, params);
    out.push(...(page.incoming_phone_numbers ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
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

  let days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 7) || 7;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const windowStart = `${since}T00:00:00Z`;
  const windowEnd = new Date().toISOString();

  const alerts = await listAlerts(auth, since);
  const rows = sweep(alerts);
  if (rows.size === 0) {
    console.log(`no 11236 since ${since} across ${alerts.length} alert(s)`);
    return;
  }

  const numbers = await listNumbers(auth, account);
  let bad = 0;
  for (const [host, row] of [...rows.entries()].sort()) {
    const [state, detail] = verdict(row, windowStart, windowEnd);
    const line = `${state.padEnd(18)} ${host || '(no host)'}  ${detail}`;
    if (state === 'clean' || state === 'recovered') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  sample ${row.url || '(none)'}, alert sids: ${row.sids.join(', ')}`);
    const hit = exposure(numbers, host);
    for (const e of hit) {
      console.warn(`  ${e.number} uses it on ${e.fields.join(', ')}` +
        (e.fallback_shares_host ? '  <- the fallback is on the same certificate' : ''));
    }
    console.warn(`  ${hit.length} number(s) affected`);
    console.warn('  repair: renew the certificate and reload the terminating ' +
                 'server or load balancer. There is no Twilio-side setting for ' +
                 'this. Then move fallback URLs onto a hostname with a separate ' +
                 'certificate.');
  }

  console.log(`${bad} host(s) failing certificate validation`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three judgements are worth freezing. An oldest alert sitting on the edge of the 30 day window is <em>not</em> an expiry timestamp, and a report that presents it as one invents a story about a certificate that lapsed weeks earlier. Twelve failures over five days is not an expiry either. And a number whose fallback shares the hostname has to be flagged, because that is the case where the safety net expired too.",
"test_py_file": "test_twilio_webhook_cert_audit.py",
"test_py": '''from twilio_webhook_cert_audit import (at, cert_host, exposure, sweep, verdict)

START = "2026-05-01T00:00:00Z"
END = "2026-05-08T00:00:00Z"


def alert(sid, url, code="11236", when="2026-05-05T14:08:00Z"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when, "log_level": "error"}


def test_cert_host_keeps_a_non_default_port():
    assert cert_host("https://hooks.example.com/voice") == "hooks.example.com"
    assert cert_host("https://hooks.example.com:443/voice") == "hooks.example.com"
    assert cert_host("https://Hooks.Example.com:8443/voice") == \\
        "hooks.example.com:8443"
    assert cert_host("http://hooks.example.com:80/voice") == "hooks.example.com"
    assert cert_host(None) == ""


def test_at_reads_the_monitor_timestamp_as_utc():
    assert at("2026-05-05T14:08:00Z") == at("2026-05-05T14:08:00")
    assert at("2026-05-05T14:08:00Z") + 60 == at("2026-05-05T14:09:00Z")
    assert at("not a date") is None
    assert at(None) is None


def test_sweep_keeps_only_certificate_failures():
    rows = sweep([alert("NO1", "https://a.example.com/voice"),
                  alert("NO2", "https://a.example.com/sms", code="11220"),
                  alert("NO3", "https://a.example.com:8443/sms")])
    assert sorted(rows) == ["a.example.com", "a.example.com:8443"]
    assert rows["a.example.com"]["alerts"] == 1


def test_an_oldest_alert_on_the_window_edge_is_not_an_expiry_time():
    # Alerts stop at 30 days. A certificate that expired six weeks ago produces
    # an oldest alert at the edge of retention, which is a fact about Twilio's
    # storage rather than about the certificate.
    row = {"alerts": 5000, "first": "2026-05-01T00:10:00Z",
           "last": "2026-05-07T23:00:00Z"}
    state, detail = verdict(row, START, END)
    assert state == "at-retention-edge"
    assert "retention boundary" in detail


def test_a_clean_cliff_inside_the_window_is_an_expiry():
    row = {"alerts": 4000, "first": "2026-05-05T14:08:00Z",
           "last": "2026-05-07T23:30:00Z"}
    state, detail = verdict(row, START, END)
    assert state == "expired"
    assert "2026-05-05T14:08:00Z" in detail


def test_a_dozen_failures_over_five_days_is_one_stale_node():
    row = {"alerts": 12, "first": "2026-05-02T00:00:00Z",
           "last": "2026-05-07T23:30:00Z"}
    state, detail = verdict(row, START, END)
    assert state == "sporadic"
    assert "balancer" in detail


def test_silence_since_the_renewal_is_reported_as_recovered():
    row = {"alerts": 900, "first": "2026-05-02T00:00:00Z",
           "last": "2026-05-02T06:00:00Z"}
    state, detail = verdict(row, START, END)
    assert state == "recovered"
    assert "6.0 hour(s)" in detail


def test_no_alerts_is_clean():
    assert verdict({"alerts": 0}, START, END)[0] == "clean"


def test_exposure_flags_a_fallback_on_the_same_certificate():
    numbers = [
        {"phone_number": "+15550001111",
         "voice_url": "https://hooks.example.com/voice",
         "voice_fallback_url": "https://hooks.example.com/fallback",
         "sms_url": "https://other.example.net/sms"},
        {"phone_number": "+15550002222",
         "voice_url": "https://hooks.example.com/voice",
         "voice_fallback_url": "https://backup.example.net/fallback"},
        {"phone_number": "+15550003333",
         "voice_url": "https://elsewhere.example.net/voice"},
    ]
    hit = exposure(numbers, "hooks.example.com")
    assert [h["number"] for h in hit] == ["+15550001111", "+15550002222"]
    assert hit[0]["fields"] == ["voice_url", "voice_fallback_url"]
    assert hit[0]["fallback_shares_host"] is True
    assert hit[1]["fallback_shares_host"] is False
''',
"test_js_file": "twilio-webhook-cert-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  at, certHost, exposure, sweep, verdict,
} from './twilio-webhook-cert-audit.mjs';

const START = '2026-05-01T00:00:00Z';
const END = '2026-05-08T00:00:00Z';

const alert = (sid, url, code = '11236', when = '2026-05-05T14:08:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when, log_level: 'error',
});

test('certHost keeps a non-default port', () => {
  assert.equal(certHost('https://hooks.example.com/voice'), 'hooks.example.com');
  assert.equal(certHost('https://hooks.example.com:443/voice'), 'hooks.example.com');
  assert.equal(certHost('https://Hooks.Example.com:8443/voice'), 'hooks.example.com:8443');
  assert.equal(certHost('http://hooks.example.com:80/voice'), 'hooks.example.com');
  assert.equal(certHost(null), '');
});

test('at reads the Monitor timestamp as UTC', () => {
  assert.equal(at('2026-05-05T14:08:00Z'), at('2026-05-05T14:08:00'));
  assert.equal(at('2026-05-05T14:08:00Z') + 60, at('2026-05-05T14:09:00Z'));
  assert.equal(at('not a date'), null);
  assert.equal(at(null), null);
});

test('sweep keeps only certificate failures', () => {
  const rows = sweep([
    alert('NO1', 'https://a.example.com/voice'),
    alert('NO2', 'https://a.example.com/sms', '11220'),
    alert('NO3', 'https://a.example.com:8443/sms'),
  ]);
  assert.deepEqual([...rows.keys()].sort(), ['a.example.com', 'a.example.com:8443']);
  assert.equal(rows.get('a.example.com').alerts, 1);
});

test('an oldest alert on the window edge is not an expiry time', () => {
  const row = { alerts: 5000, first: '2026-05-01T00:10:00Z', last: '2026-05-07T23:00:00Z' };
  const [state, detail] = verdict(row, START, END);
  assert.equal(state, 'at-retention-edge');
  assert.match(detail, /retention boundary/);
});

test('a clean cliff inside the window is an expiry', () => {
  const row = { alerts: 4000, first: '2026-05-05T14:08:00Z', last: '2026-05-07T23:30:00Z' };
  const [state, detail] = verdict(row, START, END);
  assert.equal(state, 'expired');
  assert.match(detail, /2026-05-05T14:08:00Z/);
});

test('a dozen failures over five days is one stale node', () => {
  const row = { alerts: 12, first: '2026-05-02T00:00:00Z', last: '2026-05-07T23:30:00Z' };
  const [state, detail] = verdict(row, START, END);
  assert.equal(state, 'sporadic');
  assert.match(detail, /balancer/);
});

test('silence since the renewal is reported as recovered', () => {
  const row = { alerts: 900, first: '2026-05-02T00:00:00Z', last: '2026-05-02T06:00:00Z' };
  const [state, detail] = verdict(row, START, END);
  assert.equal(state, 'recovered');
  assert.match(detail, /6.0 hour\\(s\\)/);
});

test('no alerts is clean', () => {
  assert.equal(verdict({ alerts: 0 }, START, END)[0], 'clean');
});

test('exposure flags a fallback on the same certificate', () => {
  const numbers = [
    { phone_number: '+15550001111',
      voice_url: 'https://hooks.example.com/voice',
      voice_fallback_url: 'https://hooks.example.com/fallback',
      sms_url: 'https://other.example.net/sms' },
    { phone_number: '+15550002222',
      voice_url: 'https://hooks.example.com/voice',
      voice_fallback_url: 'https://backup.example.net/fallback' },
    { phone_number: '+15550003333', voice_url: 'https://elsewhere.example.net/voice' },
  ];
  const hit = exposure(numbers, 'hooks.example.com');
  assert.deepEqual(hit.map((h) => h.number), ['+15550001111', '+15550002222']);
  assert.deepEqual(hit[0].fields, ['voice_url', 'voice_fallback_url']);
  assert.equal(hit[0].fallback_shares_host, true);
  assert.equal(hit[1].fallback_shares_host, false);
});
''',
"faq": [
 ("Why does every webhook to the host fail at exactly the same second?",
  "Because Twilio validates the certificate chain before it sends the request. An expired leaf fails validation, so nothing is sent at all. There is no partial state and no degradation: the certificate is valid until its notAfter timestamp and refused immediately afterwards."),
 ("Is the first alert always the moment the certificate expired?",
  "Only if it sits comfortably inside your window. Alerts are retained 30 days, so a certificate that lapsed six weeks ago produces an oldest alert at the edge of retention, which tells you about Twilio's storage rather than about the certificate. The script reports that case as undatable instead of inventing a date."),
 ("I get a few 11236s a day and most webhooks work. Is the certificate expired?",
  "No. An expired certificate fails everything. Scattered failures mean most requests reached a machine with a valid certificate and a few reached one without - a node behind a load balancer, or a failover host that the renewal job never touches."),
 ("Why does the script group by host and port?",
  "Because a certificate is served by a listener. One hostname can front 443 and 8443 with two different certificates and two different renewal stories, and merging them produces a verdict that is half true, which is worse than either half."),
 ("Can Twilio be told to ignore the expired certificate?",
  "No. There is no setting for skipping certificate validation on webhooks, which is the correct design: the signature on the request protects the payload, and TLS protects everything else. The repair is entirely on your endpoint - renew, reload, and check the chain is complete."),
],
"related": [
 ("/twilio/webhook-connection-timeout-11205/", "Twilio cannot open a connection to your webhook"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL"),
 ("/twilio/inbound-webhook-black-hole/", "Inbound messages that go nowhere"),
],
"citations": [CITE_11236, CITE_ALERTS, CITE_PN, CITE_WEBHOOKS],
},

{
"slug": "webhook-dns-resolution-failure-11210",
"title": "A webhook hostname with no public DNS record fails with 11210",
"description": "11210 is a name Twilio cannot resolve from the public internet: an internal zone, a dead developer tunnel, or a record that was never published.",
"h1": "a webhook hostname with no public DNS record fails with 11210",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11210", "twilio http bad host name",
             "twilio webhook dns failure", "twilio cannot resolve webhook host",
             "twilio ngrok url in production"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It worked on the laptop it was written on. It worked in staging. It reached production and every inbound call to that number now produces <code>11210 HTTP bad host name</code>, because the hostname in the webhook resolves through an <code>/etc/hosts</code> line, an internal zone, or a tunnel that died when someone closed a terminal. Twilio resolves from the public internet and gets nothing back.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code>, keep <code>error_code</code> <code>11210</code>, and pull the hostname out of <code>request_url</code>. The shape of the name is usually the diagnosis: a reserved suffix like <code>.internal</code> or <code>.local</code>, a single label with no dot, or an ephemeral tunnel domain.</p>
<p>Then scan the configuration itself. <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> and check every URL field on every number, because a number that has not been called in 30 days produces no alerts at all and is still broken.</p>""",
"problem": """<p>DNS is the one dependency a webhook has that nobody thinks of as a dependency. The URL is a string in a settings screen; it looks like configuration, not infrastructure. So it gets copied between environments, filled in from a tunnel during a demo, or pointed at a name that only exists inside a VPC, and every one of those passes review because the person reviewing it can resolve the name.</p>
<p>What makes 11210 worse than the other webhook failures is that there is nothing to retry into. There is no connection, no response, no timeout to tune. Twilio asks the public DNS system for a name, gets <code>NXDOMAIN</code>, and the call or the message ends there. Any fallback URL on the same dead hostname fails identically, which is the usual reason a fallback did not help.</p>""",
"why": """<p><strong>Twilio resolves from outside your network.</strong> A split-horizon zone, a search domain, a VPC-private zone or an <code>/etc/hosts</code> entry are all invisible from the public internet. The name resolves for you, for CI, and for the load balancer, and not for the one resolver that matters.</p>
<p><strong>Reserved suffixes never resolve publicly, by design.</strong> <code>.local</code>, <code>.internal</code>, <code>.test</code>, <code>.invalid</code>, <code>.example</code>, <code>.lan</code> and friends are reserved precisely so they cannot collide with public names. A webhook on one of those is not a DNS outage, it is a URL that could never have worked.</p>
<p><strong>Tunnel hostnames are ephemeral and end up in production anyway.</strong> A free ngrok or Cloudflare quick tunnel gets a new hostname on every restart. It is the fastest way to receive a webhook during development and the easiest thing in the world to leave in a settings field, where it works until the tunnel drops and then fails forever.</p>
<p><strong>Silence in the alerts is not evidence of health.</strong> An alert only exists if Twilio tried. A number nobody dialled, or a Messaging Service with no inbound traffic this month, generates nothing, and alerts age out after 30 days regardless. That is why the script reads the configuration as well as the alerts: the configuration is the part that is true even when nothing has been attempted.</p>""",
"steps": [
 {"h": "Sweep the alerts for 11210",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>. Read <code>error_code</code> as an integer; the Monitor API returns it as a string. Group by hostname, because the path is irrelevant when the name never resolved.</p>"""},
 {"h": "Classify the name before you blame the resolver",
  "body": """<p>Check the last label against the reserved suffixes, check for a single label with no dot at all, and check for the known ephemeral tunnel domains. Most 11210s are answered by the shape of the name alone, and the ones that are not &mdash; an ordinary public-looking hostname &mdash; are the ones worth a real DNS investigation.</p>"""},
 {"h": "Scan the configuration, not just the alerts",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> and check <code>voice_url</code>, <code>sms_url</code>, <code>status_callback</code> and both fallback fields on every number. A number that was never dialled produces no alert and is still broken; this is the only way to find it before a customer does.</p>"""},
 {"h": "Check whether the fallback shares the fate of the primary",
  "body": """<p>A fallback URL on the same unresolvable hostname is not a fallback. If the primary and the fallback both point at the dead tunnel, the number had no second chance at any point, which is worth knowing before you conclude the fallback mechanism is broken.</p>"""},
 {"h": "Publish a record or repoint, then re-check",
  "body": """<p>Either publish a public A, AAAA or CNAME record for that hostname, or repoint the webhook at a host that already has one. There is nothing to fix on the Twilio side; the repair is a DNS record or a settings change, and the script prints which number and which field to change.</p>"""},
],
"verify": """<p>Re-run after the change. Both halves of the report should be empty: no 11210 in the window, and no configured hostname that cannot resolve publicly.</p>
<pre><code class="language-bash">python3 twilio_webhook_dns_audit.py --days 7
# 0 host(s) failing to resolve, 0 configured hostname(s) that never can</code></pre>""",
"code_intro": "Two reads that answer two different questions: the alerts say what has already failed, the numbers list says what will fail the next time it is used. The pure part is the name classifier, and the case it exists for is <code>hooks.example.com</code> versus <code>hooks.example</code> &mdash; one is an ordinary public hostname and the other is a reserved suffix that can never resolve, and only the last label separates them.",
"py_file": "twilio_webhook_dns_audit.py",
"py": '''"""Report webhook hostnames Twilio cannot resolve (error 11210).

Reads the alerts for names that have already failed, and the phone number
configuration for names that will fail the first time they are used.

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
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_webhook_dns_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

BAD_HOST_NAME = 11210
MAX_DAYS = 30

URL_FIELDS = ("voice_url", "voice_fallback_url", "sms_url", "sms_fallback_url",
              "status_callback")

# Reserved and private-use top-level labels. These exist so they cannot collide
# with public names, which means they can never resolve from Twilio's side.
RESERVED = {"local", "localhost", "internal", "intranet", "lan", "home", "corp",
            "test", "example", "invalid", "localdomain"}

# Tunnel hostnames are handed out per session and die with the process. They are
# the fastest way to receive a webhook in development and the easiest thing to
# leave behind in a production settings field.
TUNNELS = ("ngrok.io", "ngrok-free.app", "ngrok.app", "ngrok.dev",
           "trycloudflare.com", "loca.lt", "localtunnel.me", "serveo.net",
           "lhr.life", "pagekite.me", "bore.pub")


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API returns this as a string, and a raw comparison against
    11210 quietly matches nothing at all.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def hostname(url):
    """Lowercase hostname from a URL, without port or trailing dot.

    The path is irrelevant when the name never resolved, so everything after the
    host is discarded and ten endpoints on one dead name become one finding.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        host = str(url).strip().lower()
    while host.endswith("."):
        host = host[:-1]
    return host


def name_class(host):
    """What kind of name this is. Pure, and the whole diagnosis for most 11210s.

    The case this function exists for is hooks.example.com against
    hooks.example. Only the last label separates an ordinary public hostname
    from a reserved suffix that can never resolve, and a check written against
    the whole string gets both of them wrong.
    """
    h = (host or "").strip().lower()
    if not h:
        return "empty"

    labels = h.split(".")
    if ":" in h or (len(labels) == 4
                    and all(l.isdigit() and len(l) <= 3 for l in labels)):
        return "ip-literal"

    for suffix in TUNNELS:
        if h == suffix or h.endswith("." + suffix):
            return "ephemeral-tunnel"

    if labels[-1] in RESERVED:
        return "reserved-suffix"

    if len(labels) == 1:
        return "single-label"

    return "public"


def tally(alerts):
    """Group name resolution failures by hostname. Pure."""
    out = {}
    for a in alerts:
        if code_of(a) != BAD_HOST_NAME:
            continue
        h = hostname(a.get("request_url"))
        row = out.setdefault(h, {"alerts": 0, "sids": [], "first": None,
                                 "last": None, "url": ""})
        row["alerts"] += 1
        if len(row["sids"]) < 3:
            row["sids"].append(a.get("sid"))
        row["url"] = row["url"] or (a.get("request_url") or "")
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
    return out


def verdict(host, row):
    """Classify one failing hostname. Pure, so the repair follows from the name.

    Returns (state, detail).
    """
    n = int(row.get("alerts") or 0)
    if not n:
        return ("clean", "no 11210 in the window")

    kind = name_class(host)
    if kind == "ephemeral-tunnel":
        return ("dev-tunnel",
                "%d x 11210 on a tunnel hostname. Those are handed out per "
                "session and die with the process, so this one was wired into "
                "production configuration during development and has been dead "
                "ever since." % n)

    if kind in ("reserved-suffix", "single-label"):
        return ("private-name",
                "%d x 11210 on a name that resolves only inside your own "
                "network. An /etc/hosts line, a search domain or a split "
                "horizon zone: this URL could never have worked from outside." % n)

    if kind == "ip-literal":
        return ("malformed",
                "%d x 11210 against something that needs no DNS at all. Twilio "
                "could not parse a usable host out of this URL, so the URL "
                "itself is the defect." % n)

    return ("unpublished",
            "%d x 11210 on an ordinary public name. Either the record was never "
            "published or the registration lapsed; Twilio asked the public DNS "
            "system and got nothing back." % n)


def scan_numbers(numbers):
    """Configured hostnames that can never resolve, whether or not they failed yet.

    Pure. An alert only exists if Twilio tried, so a number nobody has dialled
    this month produces no alert and is broken all the same. This half of the
    report is the one that finds a problem before a customer does.
    """
    out = []
    for n in numbers or []:
        for field in URL_FIELDS:
            host = hostname(n.get(field))
            if not host:
                continue
            kind = name_class(host)
            if kind in ("public", "empty"):
                continue
            out.append({"number": n.get("phone_number") or n.get("sid") or "?",
                        "field": field, "host": host, "class": kind})
    return out


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, since, limit, log_level="error"):
    """Page the Monitor alerts. next_page_url is absolute on this API."""
    url = MONITOR + "/Alerts"
    params = {"LogLevel": log_level, "StartDate": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def list_numbers(session, account, limit=2000):
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    days = args.days
    if days > MAX_DAYS:
        log.warning("alerts are retained %d days; reading %d instead of %d",
                    MAX_DAYS, MAX_DAYS, days)
        days = MAX_DAYS

    session = requests.Session()
    session.auth = (key, secret)

    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    rows = tally(list_alerts(session, since, args.max_alerts))
    numbers = list_numbers(session, account)

    failing = 0
    for host, row in sorted(rows.items()):
        state, detail = verdict(host, row)
        line = "%-13s %s  %s" % (state, host or "(no host)", detail)
        if state == "clean":
            log.info(line)
            continue
        failing += 1
        log.warning(line)
        log.warning("  first %s, last %s, sample %s", row["first"], row["last"],
                    row["url"] or "(none)")
        log.warning("  alert sids: %s", ", ".join(str(s) for s in row["sids"]))
        log.warning("  repair: publish a public A, AAAA or CNAME record for "
                    "this name, or repoint the webhook at a host that already "
                    "has one. Nothing on the Twilio side can be changed to make "
                    "an unresolvable name resolve.")

    latent = [f for f in scan_numbers(numbers) if f["host"] not in rows]
    for f in latent:
        log.warning("latent        %s %s = %s (%s). No alert yet only because "
                    "nothing has used it; it cannot resolve publicly.",
                    f["number"], f["field"], f["host"], f["class"])

    log.info("%d host(s) failing to resolve, %d configured hostname(s) that "
             "never can", failing, len(latent))
    return 1 if (failing or latent) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-webhook-dns-audit.mjs",
"js": '''/**
 * Report webhook hostnames Twilio cannot resolve (error 11210).
 *
 * Reads the alerts for names that have already failed, and the phone number
 * configuration for names that will fail the first time they are used.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const BAD_HOST_NAME = 11210;
const MAX_DAYS = 30;

const URL_FIELDS = ['voice_url', 'voice_fallback_url', 'sms_url',
  'sms_fallback_url', 'status_callback'];

// Reserved and private-use top-level labels: they exist so they cannot collide
// with public names, which means they can never resolve from Twilio's side.
const RESERVED = new Set(['local', 'localhost', 'internal', 'intranet', 'lan',
  'home', 'corp', 'test', 'example', 'invalid', 'localdomain']);

// Tunnel hostnames are handed out per session and die with the process.
const TUNNELS = ['ngrok.io', 'ngrok-free.app', 'ngrok.app', 'ngrok.dev',
  'trycloudflare.com', 'loca.lt', 'localtunnel.me', 'serveo.net', 'lhr.life',
  'pagekite.me', 'bore.pub'];

/**
 * Read error_code off an alert as a number, or null. The Monitor API returns it
 * as a string, and a raw comparison against 11210 matches nothing.
 */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** Lowercase hostname from a URL, without port or trailing dot. */
export function hostname(url) {
  if (!url) return '';
  const raw = String(url).trim();
  let host = '';
  try {
    host = new URL(raw).hostname.toLowerCase();
  } catch {
    host = raw.toLowerCase();
  }
  if (!host) host = raw.toLowerCase();
  while (host.endsWith('.')) host = host.slice(0, -1);
  return host;
}

/**
 * What kind of name this is. Pure, and the whole diagnosis for most 11210s.
 *
 * The case this exists for is hooks.example.com against hooks.example: only the
 * last label separates an ordinary public hostname from a reserved suffix that
 * can never resolve.
 */
export function nameClass(host) {
  const h = String(host ?? '').trim().toLowerCase();
  if (!h) return 'empty';

  const labels = h.split('.');
  const numeric = labels.length === 4
    && labels.every((l) => l.length > 0 && l.length <= 3
      && [...l].every((c) => c >= '0' && c <= '9'));
  if (h.includes(':') || numeric) return 'ip-literal';

  for (const suffix of TUNNELS) {
    if (h === suffix || h.endsWith(`.${suffix}`)) return 'ephemeral-tunnel';
  }

  if (RESERVED.has(labels[labels.length - 1])) return 'reserved-suffix';
  if (labels.length === 1) return 'single-label';
  return 'public';
}

/** Group name resolution failures by hostname. Pure. */
export function tally(alerts) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== BAD_HOST_NAME) continue;
    const h = hostname(a.request_url);
    if (!out.has(h)) {
      out.set(h, { alerts: 0, sids: [], first: null, last: null, url: '' });
    }
    const row = out.get(h);
    row.alerts += 1;
    if (row.sids.length < 3) row.sids.push(a.sid);
    row.url = row.url || (a.request_url ?? '');
    const when = a.date_generated ?? '';
    if (when) {
      row.first = row.first === null || when < row.first ? when : row.first;
      row.last = row.last === null || when > row.last ? when : row.last;
    }
  }
  return out;
}

/** Classify one failing hostname. Pure. Returns [state, detail]. */
export function verdict(host, row) {
  const n = Number(row.alerts ?? 0);
  if (!n) return ['clean', 'no 11210 in the window'];

  const kind = nameClass(host);
  if (kind === 'ephemeral-tunnel') {
    return ['dev-tunnel',
      `${n} x 11210 on a tunnel hostname. Those are handed out per session and ` +
      'die with the process, so this one was wired into production ' +
      'configuration during development and has been dead ever since.'];
  }

  if (kind === 'reserved-suffix' || kind === 'single-label') {
    return ['private-name',
      `${n} x 11210 on a name that resolves only inside your own network. An ` +
      '/etc/hosts line, a search domain or a split horizon zone: this URL ' +
      'could never have worked from outside.'];
  }

  if (kind === 'ip-literal') {
    return ['malformed',
      `${n} x 11210 against something that needs no DNS at all. Twilio could ` +
      'not parse a usable host out of this URL, so the URL itself is the defect.'];
  }

  return ['unpublished',
    `${n} x 11210 on an ordinary public name. Either the record was never ` +
    'published or the registration lapsed; Twilio asked the public DNS system ' +
    'and got nothing back.'];
}

/**
 * Configured hostnames that can never resolve, whether or not they have failed
 * yet. Pure. An alert exists only if Twilio tried, so a number nobody dialled
 * this month is broken and silent at the same time.
 */
export function scanNumbers(numbers) {
  const out = [];
  for (const n of numbers ?? []) {
    for (const field of URL_FIELDS) {
      const host = hostname(n[field]);
      if (!host) continue;
      const kind = nameClass(host);
      if (kind === 'public' || kind === 'empty') continue;
      out.push({ number: n.phone_number ?? n.sid ?? '?', field, host, class: kind });
    }
  }
  return out;
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

export async function listAlerts(auth, since, limit = 10000, logLevel = 'error') {
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

async function listNumbers(auth, account) {
  let url = `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`;
  let params = { PageSize: 1000 };
  const out = [];
  while (url) {
    const page = await get(auth, url, params);
    out.push(...(page.incoming_phone_numbers ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
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

  let days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 7) || 7;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const rows = tally(await listAlerts(auth, since));
  const numbers = await listNumbers(auth, account);

  let failing = 0;
  for (const [host, row] of [...rows.entries()].sort()) {
    const [state, detail] = verdict(host, row);
    const line = `${state.padEnd(13)} ${host || '(no host)'}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    failing += 1;
    console.warn(line);
    console.warn(`  first ${row.first}, last ${row.last}, sample ${row.url || '(none)'}`);
    console.warn(`  alert sids: ${row.sids.join(', ')}`);
    console.warn('  repair: publish a public A, AAAA or CNAME record for this ' +
                 'name, or repoint the webhook at a host that already has one. ' +
                 'Nothing on the Twilio side can be changed to make an ' +
                 'unresolvable name resolve.');
  }

  const latent = scanNumbers(numbers).filter((f) => !rows.has(f.host));
  for (const f of latent) {
    console.warn(`latent        ${f.number} ${f.field} = ${f.host} (${f.class}). ` +
                 'No alert yet only because nothing has used it; it cannot ' +
                 'resolve publicly.');
  }

  console.log(`${failing} host(s) failing to resolve, ${latent.length} configured ` +
              'hostname(s) that never can');
  process.exitCode = (failing || latent.length) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The last label is the whole game. <code>hooks.example.com</code> is an ordinary public hostname and <code>hooks.example</code> is a reserved suffix that can never resolve, and a classifier that matches on substrings gets both wrong. The rest pins down the half of the report that has no alerts behind it: a number nobody has dialled still has a broken URL, and silence is not the same as health.",
"test_py_file": "test_twilio_webhook_dns_audit.py",
"test_py": '''from twilio_webhook_dns_audit import (code_of, hostname, name_class,
                                       scan_numbers, tally, verdict)


def alert(sid, url, code="11210", when="2026-06-02T08:00:00Z"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when, "log_level": "error"}


def test_code_of_reads_the_string_the_monitor_api_returns():
    assert code_of({"error_code": "11210"}) == 11210
    assert code_of({"error_code": 11210}) == 11210
    assert code_of({}) is None


def test_hostname_drops_the_port_the_path_and_a_trailing_dot():
    assert hostname("https://Hooks.Example.com:8443/voice?CallSid=CA1") == \\
        "hooks.example.com"
    assert hostname("https://hooks.example.com./voice") == "hooks.example.com"
    assert hostname(None) == ""


def test_only_the_last_label_decides_a_reserved_suffix():
    # hooks.example.com is a perfectly ordinary public name; hooks.example is a
    # reserved suffix that cannot resolve. A substring match gets both wrong.
    assert name_class("hooks.example.com") == "public"
    assert name_class("hooks.example") == "reserved-suffix"
    assert name_class("api.internal") == "reserved-suffix"
    assert name_class("printer.local") == "reserved-suffix"
    assert name_class("localhost") == "reserved-suffix"


def test_the_other_shapes_a_name_can_take():
    assert name_class("webhooks") == "single-label"
    assert name_class("10.0.0.5") == "ip-literal"
    assert name_class("a1b2c3d4.ngrok.io") == "ephemeral-tunnel"
    assert name_class("wandering-cat.trycloudflare.com") == "ephemeral-tunnel"
    assert name_class("") == "empty"


def test_tally_groups_by_name_and_ignores_other_codes():
    rows = tally([alert("NO1", "https://api.internal/voice"),
                  alert("NO2", "https://api.internal/sms"),
                  alert("NO3", "https://api.internal/sms", code="11205")])
    assert list(rows) == ["api.internal"]
    assert rows["api.internal"]["alerts"] == 2
    assert rows["api.internal"]["sids"] == ["NO1", "NO2"]


def test_a_dead_tunnel_is_reported_as_a_development_leftover():
    state, detail = verdict("a1b2c3d4.ngrok.io", {"alerts": 60})
    assert state == "dev-tunnel"
    assert "per session" in detail


def test_an_internal_name_is_reported_as_never_having_worked():
    state, detail = verdict("api.internal", {"alerts": 9})
    assert state == "private-name"
    assert "outside" in detail


def test_a_public_looking_name_is_the_one_worth_investigating():
    state, detail = verdict("hooks.example.com", {"alerts": 9})
    assert state == "unpublished"
    assert "registration lapsed" in detail


def test_the_config_scan_finds_numbers_that_have_produced_no_alerts():
    findings = scan_numbers([
        {"phone_number": "+15550001111",
         "voice_url": "https://a1b2c3d4.ngrok.io/voice",
         "voice_fallback_url": "https://a1b2c3d4.ngrok.io/fallback",
         "sms_url": "https://hooks.example.com/sms"},
        {"phone_number": "+15550002222",
         "voice_url": "https://hooks.example.com/voice"},
    ])
    assert [(f["number"], f["field"]) for f in findings] == [
        ("+15550001111", "voice_url"), ("+15550001111", "voice_fallback_url")]
    assert all(f["class"] == "ephemeral-tunnel" for f in findings)
''',
"test_js_file": "twilio-webhook-dns-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  codeOf, hostname, nameClass, scanNumbers, tally, verdict,
} from './twilio-webhook-dns-audit.mjs';

const alert = (sid, url, code = '11210', when = '2026-06-02T08:00:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when, log_level: 'error',
});

test('codeOf reads the string the Monitor API returns', () => {
  assert.equal(codeOf({ error_code: '11210' }), 11210);
  assert.equal(codeOf({ error_code: 11210 }), 11210);
  assert.equal(codeOf({}), null);
});

test('hostname drops the port, the path and a trailing dot', () => {
  assert.equal(hostname('https://Hooks.Example.com:8443/voice?CallSid=CA1'),
    'hooks.example.com');
  assert.equal(hostname('https://hooks.example.com./voice'), 'hooks.example.com');
  assert.equal(hostname(null), '');
});

test('only the last label decides a reserved suffix', () => {
  assert.equal(nameClass('hooks.example.com'), 'public');
  assert.equal(nameClass('hooks.example'), 'reserved-suffix');
  assert.equal(nameClass('api.internal'), 'reserved-suffix');
  assert.equal(nameClass('printer.local'), 'reserved-suffix');
  assert.equal(nameClass('localhost'), 'reserved-suffix');
});

test('the other shapes a name can take', () => {
  assert.equal(nameClass('webhooks'), 'single-label');
  assert.equal(nameClass('10.0.0.5'), 'ip-literal');
  assert.equal(nameClass('a1b2c3d4.ngrok.io'), 'ephemeral-tunnel');
  assert.equal(nameClass('wandering-cat.trycloudflare.com'), 'ephemeral-tunnel');
  assert.equal(nameClass(''), 'empty');
});

test('tally groups by name and ignores other codes', () => {
  const rows = tally([
    alert('NO1', 'https://api.internal/voice'),
    alert('NO2', 'https://api.internal/sms'),
    alert('NO3', 'https://api.internal/sms', '11205'),
  ]);
  assert.deepEqual([...rows.keys()], ['api.internal']);
  assert.equal(rows.get('api.internal').alerts, 2);
  assert.deepEqual(rows.get('api.internal').sids, ['NO1', 'NO2']);
});

test('a dead tunnel is reported as a development leftover', () => {
  const [state, detail] = verdict('a1b2c3d4.ngrok.io', { alerts: 60 });
  assert.equal(state, 'dev-tunnel');
  assert.match(detail, /per session/);
});

test('an internal name is reported as never having worked', () => {
  const [state, detail] = verdict('api.internal', { alerts: 9 });
  assert.equal(state, 'private-name');
  assert.match(detail, /outside/);
});

test('a public-looking name is the one worth investigating', () => {
  const [state, detail] = verdict('hooks.example.com', { alerts: 9 });
  assert.equal(state, 'unpublished');
  assert.match(detail, /registration lapsed/);
});

test('the config scan finds numbers that have produced no alerts', () => {
  const findings = scanNumbers([
    { phone_number: '+15550001111',
      voice_url: 'https://a1b2c3d4.ngrok.io/voice',
      voice_fallback_url: 'https://a1b2c3d4.ngrok.io/fallback',
      sms_url: 'https://hooks.example.com/sms' },
    { phone_number: '+15550002222', voice_url: 'https://hooks.example.com/voice' },
  ]);
  assert.deepEqual(findings.map((f) => [f.number, f.field]),
    [['+15550001111', 'voice_url'], ['+15550001111', 'voice_fallback_url']]);
  assert.ok(findings.every((f) => f.class === 'ephemeral-tunnel'));
});
''',
"faq": [
 ("The URL works in my browser. Why does Twilio say bad host name?",
  "Because your resolver is not Twilio's. A split-horizon zone, a VPC-private zone, a search domain or an /etc/hosts entry all make a name resolve for you and for nobody on the public internet. Twilio asks public DNS and gets NXDOMAIN, so no connection is ever attempted."),
 ("Why does the script look at phone number configuration as well as alerts?",
  "Because an alert only exists if Twilio tried. A number nobody has dialled in a month produces no alerts and is broken all the same, and alerts age out after 30 days regardless. The configuration is true whether or not anything has been attempted, so both halves are needed."),
 ("What is wrong with using an ngrok URL in a real account?",
  "Nothing, until the tunnel restarts. Free tunnel hostnames are handed out per session, so the URL is correct for hours and dead forever after. It is the single most common source of 11210 in accounts that used to work, which is why those domains get their own verdict."),
 ("Did my fallback URL not save the call?",
  "Not if it is on the same hostname. A fallback that shares an unresolvable name fails in exactly the same way at exactly the same moment. Fallbacks are only worth having on infrastructure that can fail independently of the primary."),
 ("Is there anything to change on the Twilio side?",
  "No. The repair is a DNS record or a different URL, both of which live with you. Everything the script does is a GET, so it names the number and the field and stops there; a script holding a credential that can place calls has no business editing routing."),
],
"related": [
 ("/twilio/webhook-connection-timeout-11205/", "Twilio cannot open a connection to your webhook"),
 ("/twilio/webhook-tls-certificate-expired-11236/", "An expired webhook certificate"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still answering with demo TwiML"),
],
"citations": [CITE_11210, CITE_ALERTS, CITE_PN, CITE_WEBHOOKS],
},

]
