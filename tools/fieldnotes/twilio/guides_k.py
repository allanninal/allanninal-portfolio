#!/usr/bin/env python3
"""/twilio/ field notes, batch K — the writing.

Four failures that all happen after Twilio has already reached your handler. The
connection opened, the certificate validated, the request arrived, and then the
response was wrong: rejected by your own signature check, sent with a media type
Twilio does not dispatch on, malformed as XML, or too big to accept.

That shared shape sets the method. The Monitor Alerts list says which endpoint
failed and how often, but every one of these verdicts needs the response itself,
and `response_body`, `response_headers`, `request_headers` and
`request_variables` are populated **only** on the single-alert fetch
`GET /v1/Alerts/{Sid}`. They are blank on every row of the list. So each script
here sweeps cheaply, then pays one request per alert it wants to read, and caps
how many of those it will make.

Two more constraints run through the batch. Alerts are retained 30 days, so
every window is clamped and says so. And not everything lands at
`LogLevel=error` — 12200 schema validation warnings are logged at
`LogLevel=warning`, so the parse-failure script sweeps both levels rather than
reporting a clean account while the warning shelf fills up.

Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run.
"""

CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_WEBHOOKS = ("Webhooks (HTTP callbacks) — Twilio Docs",
                 "https://www.twilio.com/docs/usage/webhooks")
CITE_SECURITY = ("Security: validating requests from Twilio — Twilio Docs",
                 "https://www.twilio.com/docs/usage/security")
CITE_11200 = ("Error 11200: HTTP retrieval failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11200")
CITE_11750 = ("Error 11750: TwiML response body too large — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11750")
CITE_12100 = ("Error 12100: document parse failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/12100")
CITE_12200 = ("Error 12200: schema validation warning — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/12200")
CITE_12300 = ("Error 12300: invalid Content-Type — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/12300")
CITE_TWIML_VOICE = ("TwiML for Programmable Voice — Twilio Docs",
                    "https://www.twilio.com/docs/voice/twiml")
CITE_TWIML_PLAY = ("TwiML Voice: <Play> — Twilio Docs",
                   "https://www.twilio.com/docs/voice/twiml/play")
CITE_TWIML_REDIRECT = ("TwiML Voice: <Redirect> — Twilio Docs",
                       "https://www.twilio.com/docs/voice/twiml/redirect")

GUIDES = [

{
"slug": "webhook-signature-validation-403-behind-proxy",
"title": "Signature validation rejects Twilio with 403 behind a proxy",
"description": "It worked on the laptop and 403s in production. The signature covers the URL Twilio called, not the one your proxy handed the app.",
"h1": "signature validation rejects Twilio with 403 behind a proxy",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio signature validation failing", "x-twilio-signature 403",
             "twilio RequestValidator behind proxy", "twilio webhook 403 forbidden",
             "twilio signature x-forwarded-proto"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It works on the laptop with the tunnel running. It works in staging. Then it goes behind the load balancer and every Twilio request comes back <code>403</code> from your own middleware &mdash; the code you added to keep other people <em>out</em>. Twilio logs it as <code>11200</code>, exactly like a 404 or a crash, and the Debugger row looks the same as every other retrieval failure on the account.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> for <code>error_code == 11200</code>, then fetch a sample of those alerts individually with <code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> and read <code>response_body</code>. A body that mentions a signature, or is a bare <code>403</code>, separates this from an ordinary 5xx.</p>
<p>The cause is almost always the URL. <code>X-Twilio-Signature</code> is an HMAC-SHA1 over the <em>full</em> URL Twilio called &mdash; scheme, host, port and query string &mdash; plus the sorted POST parameters. A TLS-terminating proxy hands your app <code>http://</code> and often an internal hostname, so the app signs a different string and rejects a legitimate request. The alert's <code>request_url</code> is the exact string the validator has to be given.</p>""",
"problem": """<p>Every other webhook failure in this section is something breaking. This one is something working: the validator is doing precisely what it was written to do, on an input that is wrong by one field. The request really did come from Twilio, the signature header really is valid, and your app really cannot verify it, because it is verifying against a URL that no longer matches the one Twilio signed.</p>
<p>What makes it expensive is where it appears. It cannot be reproduced locally, because locally there is no proxy in front and the app sees the same URL Twilio called. It survives every test that mocks the request. It shows up the hour the service moves behind a load balancer, a CDN, an ingress controller or an API gateway, and it presents as <code>11200</code> &mdash; the same code as a 404 and the same code as a crash. Teams spend a day on routing and deploys before anyone opens a single alert body and reads the word <em>signature</em>.</p>""",
"why": """<p><strong>The signature covers the URL, and the proxy changes the URL.</strong> Twilio computes the HMAC over the exact URL it requested. Your app reconstructs that URL from what the proxy gave it: <code>http</code> instead of <code>https</code>, an internal service name instead of the public host, sometimes port <code>8080</code> instead of no port. Change one character and the HMAC changes completely, which is the property that makes signatures useful and this bug invisible.</p>
<p><strong>11200 is a bucket, not a diagnosis.</strong> Twilio treats anything outside <code>2xx</code> as a retrieval failure. A 403 from your validator, a 404 from a moved route and a 500 from a crash all arrive with the same <code>error_code</code>, the same shape and the same <code>request_url</code> field. The only thing that separates them is what came back, and that is not in the list.</p>
<p><strong>The response body is only on the single-alert fetch.</strong> Every row of <code>GET /v1/Alerts</code> has <code>response_body</code> and <code>response_headers</code> blank. They are populated when you fetch one alert by SID and nowhere else. So the sweep is cheap and tells you nothing about the cause, and the cause costs one request per alert.</p>
<p><strong>The obvious normalisation is the wrong move here.</strong> Grouping webhook alerts by lowercase host and path is the right instinct for finding <em>which endpoint</em> is failing, and it is exactly wrong for fixing this one. The scheme, the port and the query string are all inside the HMAC. The string you need is <code>request_url</code> untouched, and a script that tidies it before printing it has thrown away the answer.</p>""",
"steps": [
 {"h": "Sweep 11200 over a bounded window and group by host",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>. Keep alerts where <code>error_code</code> is <code>11200</code> &mdash; read it as an integer, because the Monitor API returns error codes as strings. Group by hostname so a burst on one service is one line rather than four hundred.</p>"""},
 {"h": "Fetch a few of them by SID to see what came back",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> is the only place <code>response_body</code> and <code>response_headers</code> exist. Two or three per host is enough to characterise the failure, and each one is a request, so cap it. If the sample comes back with empty bodies, the endpoint returned nothing at all and this is not your validator.</p>"""},
 {"h": "Read the body before you believe the error code",
  "body": """<p>A body naming <code>X-Twilio-Signature</code>, saying <em>invalid signature</em>, or coming from a framework's request-validator middleware is this problem. A bare <code>403 Forbidden</code> page from nginx or a WAF is a different one with a different owner: something in front of the app is refusing Twilio before your code runs. A stack trace is an application error, and none of the three share a repair.</p>"""},
 {"h": "Take request_url exactly as logged and change nothing",
  "body": """<p>That field is the string the HMAC was computed over. Do not lowercase it, do not drop the query string, do not add or remove a trailing slash. Feed it to the validator alongside the POST parameters and the header, and you will reproduce the failure locally in one line &mdash; which is the fastest confirmation available and needs no traffic.</p>"""},
 {"h": "Rebuild the public URL in the app, then re-run the sweep",
  "body": """<p>Reconstruct the URL from <code>X-Forwarded-Proto</code> and <code>X-Forwarded-Host</code>, or hardcode the public base URL and append the request path, before calling <code>RequestValidator.validate()</code>. Trust those headers only from your own proxy. Re-run this script over the window afterwards: the signature bucket should empty while the other buckets stay exactly as they were.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the deploy. The signature bucket goes to zero; anything left is a different failure and is reported as one.</p>
<pre><code class="language-bash">python3 twilio_signature_403_audit.py --days 1
# 0 endpoint(s) rejecting Twilio's signature, 1 with other 11200 failures</code></pre>""",
"code_intro": "One cheap sweep, then a capped number of single-alert fetches, because that is the only place the response body lives. The classifier is pure and takes the fetched alert as an argument rather than doing the fetching, so every branch &mdash; a signature rejection, a proxy 403, a stack trace, an empty body &mdash; is exercised offline. <code>signed_url()</code> is one line and has a test anyway, because the temptation to normalise that string is the whole trap.",
"py_file": "twilio_signature_403_audit.py",
"py": '''"""Separate signature-validation rejections from ordinary 11200 webhook failures.

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
log = logging.getLogger("twilio_signature_403_audit")

MONITOR = "https://monitor.twilio.com/v1"

RETRIEVAL_FAILURE = 11200

# Alerts are retained 30 days. A longer window is not more history, it is the
# same history under a label that makes the report look more thorough.
MAX_DAYS = 30

# Phrases that mean the endpoint refused Twilio's own request. Framework
# middleware and hand-rolled checks both tend to name the header or the word.
SIGNATURE_MARKERS = (
    "x-twilio-signature",
    "invalid signature",
    "signature validation",
    "signature mismatch",
    "signature verification",
    "twilio signature",
    "requestvalidator",
)

# A refusal with no mention of a signature. Something in front of the app said
# no before the app ran, which is a different owner and a different repair.
FORBIDDEN_MARKERS = (
    "403 forbidden",
    "forbidden",
    "access denied",
    "not authorized",
    "unauthorized",
)

# The application ran and blew up. Nothing to do with request validation.
APP_ERROR_MARKERS = (
    "traceback (most recent call last)",
    "internal server error",
    "stack trace",
    "exception",
)


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API hands this back as a string while the Messages list hands
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


def host_of(url):
    """Lowercase hostname, for grouping only.

    Grouping is the one place it is safe to throw information away. The repair
    needs the whole URL, which is why signed_url() exists separately.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    return (parts.hostname or str(url).strip()).lower()


def signed_url(alert):
    """The exact string the signature was computed over.

    Returned untouched on purpose. Scheme, host, port and query string are all
    inside the HMAC, so lowercasing the host or dropping the parameters gives
    you a string that will never validate and looks like it should.
    """
    return str(alert.get("request_url") or "").strip()


def header_text(headers):
    """Flatten response_headers into searchable text.

    Twilio returns this field in more than one shape depending on the product
    that logged the alert: a mapping, a list of lines, or one blob. Handling
    only the shape you happened to see first is how a working check quietly
    stops matching six months later.
    """
    if headers is None:
        return ""
    if isinstance(headers, dict):
        return "\\n".join("%s: %s" % (k, v) for k, v in headers.items())
    if isinstance(headers, (list, tuple)):
        return "\\n".join(str(h) for h in headers)
    return str(headers)


def found(text, needles):
    """Which of these phrases appear, case-insensitively. Pure and boring."""
    low = str(text or "").lower()
    return [n for n in needles if n in low]


def classify(alert, detail):
    """Decide what one 11200 alert actually was.

    Pure: `detail` is the single-alert fetch, GET /v1/Alerts/{Sid}, or None when
    it was not fetched. The list response blanks response_body and
    response_headers on every row, so without that second request there is no
    honest verdict to give and this says so rather than guessing.

    Returns (state, detail_text).
    """
    if code_of(alert) != RETRIEVAL_FAILURE:
        return ("not-11200", "some other error code; this script only reads 11200")

    if detail is None:
        return ("unfetched",
                "the alerts list blanks response_body, so what the endpoint "
                "returned is unknown until this alert is fetched by SID")

    body = str(detail.get("response_body") or "")
    text = body + "\\n" + header_text(detail.get("response_headers"))

    hits = found(text, SIGNATURE_MARKERS)
    if hits:
        return ("signature",
                "the endpoint rejected Twilio's own request (%s). The signature "
                "covers the full URL Twilio called, and behind a TLS-terminating "
                "proxy the app rebuilds a different one." % ", ".join(hits))

    if found(text, FORBIDDEN_MARKERS):
        return ("forbidden",
                "refused with nothing about signatures: a WAF, an ingress rule "
                "or auth middleware in front of the app said no before your code "
                "ran. Different owner, different repair.")

    if found(text, APP_ERROR_MARKERS):
        return ("app-error",
                "the handler ran and threw. This is an application failure "
                "wearing the same error code, not a validation problem.")

    if not body.strip():
        return ("no-body",
                "non-2xx with an empty body. Nothing here points at validation; "
                "look at the status the endpoint returned and at its own logs.")

    return ("other",
            "non-2xx with a body that names neither a signature nor an error. "
            "Read the first line of it before deciding.")


def group(alerts):
    """Bucket 11200 alerts by hostname. Pure.

    date_generated is ISO 8601 in UTC on every alert, so a string comparison
    orders them and finding the ends needs no date parsing.
    """
    out = {}
    for a in alerts:
        if code_of(a) != RETRIEVAL_FAILURE:
            continue
        host = host_of(a.get("request_url"))
        row = out.setdefault(host, {"alerts": 0, "sids": [], "urls": [],
                                    "methods": set(), "first": None, "last": None})
        row["alerts"] += 1
        if len(row["sids"]) < 5:
            row["sids"].append(a.get("sid"))
            row["urls"].append(signed_url(a))
        method = str(a.get("request_method") or "").upper()
        if method:
            row["methods"].add(method)
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
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
    """One alert by SID: the only place response_body is populated."""
    return get(session, "%s/Alerts/%s" % (MONITOR, sid))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=1,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    ap.add_argument("--sample", type=int, default=2,
                    help="alerts to fetch individually per host for the response "
                         "body (0 to skip; each one is a request)")
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
    rows = group(alerts)
    log.info("%d alert(s) since %s, %d host(s) with 11200", len(alerts), since,
             len(rows))

    signature = other = 0
    for host, row in sorted(rows.items()):
        states = []
        for sid in row["sids"][:max(0, args.sample)]:
            states.append(classify({"error_code": RETRIEVAL_FAILURE},
                                   fetch_alert(session, sid)))
        if not states:
            states = [classify({"error_code": RETRIEVAL_FAILURE}, None)]

        state, detail = states[0]
        for s, d in states:
            if s == "signature":
                state, detail = s, d
                break

        log.warning("%-10s %s  %d x 11200 (%s)  %s", state, host, row["alerts"],
                    ", ".join(sorted(row["methods"])) or "?", detail)
        log.warning("  first %s, last %s", row["first"], row["last"])
        if state == "signature":
            signature += 1
            log.warning("  validate against this exact string, unmodified: %s",
                        row["urls"][0])
            log.warning("  repair: rebuild the URL from X-Forwarded-Proto and "
                        "X-Forwarded-Host (or hardcode the public base URL) "
                        "before calling RequestValidator.validate, and trust "
                        "those headers only from your own proxy")
        else:
            other += 1

    log.info("%d endpoint(s) rejecting Twilio's signature, %d with other 11200 "
             "failures", signature, other)
    return 1 if signature else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-signature-403-audit.mjs",
"js": '''/**
 * Separate signature-validation rejections from ordinary 11200 webhook failures.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';

const RETRIEVAL_FAILURE = 11200;

// Alerts are retained 30 days. A longer window is the same history mislabelled.
const MAX_DAYS = 30;

// Phrases that mean the endpoint refused Twilio's own request.
const SIGNATURE_MARKERS = [
  'x-twilio-signature', 'invalid signature', 'signature validation',
  'signature mismatch', 'signature verification', 'twilio signature',
  'requestvalidator',
];

// A refusal with no mention of a signature: something in front of the app.
const FORBIDDEN_MARKERS = [
  '403 forbidden', 'forbidden', 'access denied', 'not authorized', 'unauthorized',
];

// The application ran and blew up. Nothing to do with request validation.
const APP_ERROR_MARKERS = [
  'traceback (most recent call last)', 'internal server error', 'stack trace',
  'exception',
];

/**
 * Read error_code off an alert as a number, or null. The Monitor API returns it
 * as a string while the Messages list returns a number.
 */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** Lowercase hostname, for grouping only. */
export function hostOf(url) {
  if (!url) return '';
  const raw = String(url).trim();
  try {
    return new URL(raw).hostname.toLowerCase();
  } catch {
    return raw.toLowerCase();
  }
}

/**
 * The exact string the signature was computed over, returned untouched. Scheme,
 * host, port and query string are all inside the HMAC.
 */
export function signedUrl(alert) {
  return String(alert.request_url ?? '').trim();
}

/**
 * Flatten response_headers into searchable text. Twilio returns this field as a
 * mapping, a list of lines or one blob depending on the product.
 */
export function headerText(headers) {
  if (headers === null || headers === undefined) return '';
  if (Array.isArray(headers)) return headers.map(String).join('\\n');
  if (typeof headers === 'object') {
    return Object.entries(headers).map(([k, v]) => `${k}: ${v}`).join('\\n');
  }
  return String(headers);
}

/** Which of these phrases appear, case-insensitively. */
export function found(text, needles) {
  const low = String(text ?? '').toLowerCase();
  return needles.filter((n) => low.includes(n));
}

/**
 * Decide what one 11200 alert actually was. Pure: `detail` is the single-alert
 * fetch, or null when it was not fetched. Returns [state, detailText].
 */
export function classify(alert, detail) {
  if (codeOf(alert) !== RETRIEVAL_FAILURE) {
    return ['not-11200', 'some other error code; this script only reads 11200'];
  }
  if (detail === null || detail === undefined) {
    return ['unfetched',
      'the alerts list blanks response_body, so what the endpoint returned is ' +
      'unknown until this alert is fetched by SID'];
  }

  const body = String(detail.response_body ?? '');
  const text = `${body}\\n${headerText(detail.response_headers)}`;

  const hits = found(text, SIGNATURE_MARKERS);
  if (hits.length) {
    return ['signature',
      `the endpoint rejected Twilio's own request (${hits.join(', ')}). The ` +
      'signature covers the full URL Twilio called, and behind a ' +
      'TLS-terminating proxy the app rebuilds a different one.'];
  }

  if (found(text, FORBIDDEN_MARKERS).length) {
    return ['forbidden',
      'refused with nothing about signatures: a WAF, an ingress rule or auth ' +
      'middleware in front of the app said no before your code ran. Different ' +
      'owner, different repair.'];
  }

  if (found(text, APP_ERROR_MARKERS).length) {
    return ['app-error',
      'the handler ran and threw. This is an application failure wearing the ' +
      'same error code, not a validation problem.'];
  }

  if (!body.trim()) {
    return ['no-body',
      'non-2xx with an empty body. Nothing here points at validation; look at ' +
      'the status the endpoint returned and at its own logs.'];
  }

  return ['other',
    'non-2xx with a body that names neither a signature nor an error. Read the ' +
    'first line of it before deciding.'];
}

/** Bucket 11200 alerts by hostname. Pure. */
export function group(alerts) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== RETRIEVAL_FAILURE) continue;
    const host = hostOf(a.request_url);
    if (!out.has(host)) {
      out.set(host, {
        alerts: 0, sids: [], urls: [], methods: new Set(), first: null, last: null,
      });
    }
    const row = out.get(host);
    row.alerts += 1;
    if (row.sids.length < 5) {
      row.sids.push(a.sid);
      row.urls.push(signedUrl(a));
    }
    const method = String(a.request_method ?? '').toUpperCase();
    if (method) row.methods.add(method);
    const when = a.date_generated ?? '';
    if (when) {
      row.first = row.first === null || when < row.first ? when : row.first;
      row.last = row.last === null || when > row.last ? when : row.last;
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

/** One alert by SID: the only place response_body is populated. */
export async function fetchAlert(auth, sid) {
  return get(auth, `${MONITOR}/Alerts/${sid}`);
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
    ? process.argv[process.argv.indexOf('--days') + 1] : 1) || 1;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }
  const sample = Number(process.argv.includes('--sample')
    ? process.argv[process.argv.indexOf('--sample') + 1] : 2);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await listAlerts(auth, since);
  const rows = group(alerts);
  console.log(`${alerts.length} alert(s) since ${since}, ${rows.size} host(s) with 11200`);

  let signature = 0;
  let other = 0;
  for (const [host, row] of [...rows.entries()].sort()) {
    const states = [];
    for (const sid of row.sids.slice(0, Math.max(0, sample))) {
      states.push(classify({ error_code: RETRIEVAL_FAILURE }, await fetchAlert(auth, sid)));
    }
    if (!states.length) states.push(classify({ error_code: RETRIEVAL_FAILURE }, null));

    let [state, detail] = states[0];
    for (const [s, d] of states) {
      if (s === 'signature') { state = s; detail = d; break; }
    }

    const methods = [...row.methods].sort().join(', ') || '?';
    console.warn(`${state.padEnd(10)} ${host}  ${row.alerts} x 11200 (${methods})  ${detail}`);
    console.warn(`  first ${row.first}, last ${row.last}`);
    if (state === 'signature') {
      signature += 1;
      console.warn(`  validate against this exact string, unmodified: ${row.urls[0]}`);
      console.warn('  repair: rebuild the URL from X-Forwarded-Proto and ' +
                   'X-Forwarded-Host (or hardcode the public base URL) before ' +
                   'calling RequestValidator.validate, and trust those headers ' +
                   'only from your own proxy');
    } else {
      other += 1;
    }
  }

  console.log(`${signature} endpoint(s) rejecting Twilio's signature, ${other} ` +
              'with other 11200 failures');
  process.exitCode = signature ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the four bodies that arrive at a 403 by four different routes, because filing any one of them under the wrong heading sends somebody to the wrong team. They also pin the thing that is easy to get right and easier to undo: <code>signed_url()</code> returns <code>request_url</code> with its scheme, port and query string intact, while <code>host_of()</code> throws all three away &mdash; one is for the repair, the other is only for grouping.",
"test_py_file": "test_twilio_signature_403_audit.py",
"test_py": '''from twilio_signature_403_audit import (classify, code_of, found, group,
                                          header_text, host_of, signed_url)


def alert(sid, url, code="11200", when="2026-04-02T10:00:00Z", method="POST"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when, "request_method": method, "log_level": "error"}


def detail(body="", headers=None):
    return {"response_body": body, "response_headers": headers}


def test_code_of_reads_the_string_the_monitor_api_returns():
    assert code_of({"error_code": "11200"}) == 11200
    assert code_of({"error_code": 11200}) == 11200
    assert code_of({"error_code": ""}) is None
    assert code_of({}) is None


def test_signed_url_keeps_everything_the_hmac_covers():
    # The scheme, the port and the query string are all inside the signature.
    # Tidying any of them produces a string that can never validate.
    a = alert("NO1", "https://hooks.example.com:8443/twilio/voice?From=%2B15551112222")
    assert signed_url(a) == \\
        "https://hooks.example.com:8443/twilio/voice?From=%2B15551112222"


def test_host_of_throws_away_what_signed_url_keeps():
    assert host_of("https://Hooks.Example.com:8443/twilio/voice?a=b") == \\
        "hooks.example.com"
    assert host_of(None) == ""


def test_a_body_naming_the_header_is_a_signature_rejection():
    state, why = classify(alert("NO1", "https://a.example.com/voice"),
                          detail("Invalid signature for X-Twilio-Signature"))
    assert state == "signature"
    assert "URL" in why


def test_a_bare_403_page_is_not_blamed_on_the_validator():
    # nginx or a WAF refused before the app ran. Same error code, other owner.
    state, why = classify(alert("NO1", "https://a.example.com/voice"),
                          detail("<html><head><title>403 Forbidden</title></head></html>"))
    assert state == "forbidden"
    assert "WAF" in why


def test_a_stack_trace_is_an_application_error():
    state, _ = classify(alert("NO1", "https://a.example.com/voice"),
                        detail("Traceback (most recent call last):\\n  File ..."))
    assert state == "app-error"


def test_an_empty_body_is_reported_as_unknown_rather_than_guessed():
    state, _ = classify(alert("NO1", "https://a.example.com/voice"), detail(""))
    assert state == "no-body"


def test_without_the_single_alert_fetch_there_is_no_verdict():
    state, why = classify(alert("NO1", "https://a.example.com/voice"), None)
    assert state == "unfetched"
    assert "response_body" in why


def test_markers_are_also_read_from_the_response_headers():
    state, _ = classify(
        alert("NO1", "https://a.example.com/voice"),
        detail("", {"X-Rejected-By": "RequestValidator", "Server": "gunicorn"}))
    assert state == "signature"


def test_header_text_flattens_every_shape_the_field_arrives_in():
    assert header_text({"A": "1"}) == "A: 1"
    assert header_text(["A: 1", "B: 2"]) == "A: 1\\nB: 2"
    assert header_text("A: 1") == "A: 1"
    assert header_text(None) == ""


def test_group_buckets_by_host_and_records_the_ends():
    rows = group([
        alert("NO1", "https://a.example.com/voice?x=1", when="2026-04-02T10:00:00Z"),
        alert("NO2", "https://a.example.com/sms?x=2", when="2026-04-01T09:00:00Z"),
        alert("NO3", "https://b.example.com/voice", code="11205"),
    ])
    assert set(rows) == {"a.example.com"}
    assert rows["a.example.com"]["alerts"] == 2
    assert rows["a.example.com"]["first"] == "2026-04-01T09:00:00Z"
    assert rows["a.example.com"]["urls"][0].endswith("?x=1")


def test_found_is_case_insensitive():
    assert found("INVALID SIGNATURE", ["invalid signature"]) == ["invalid signature"]
    assert found(None, ["invalid signature"]) == []
''',
"test_js_file": "twilio-signature-403-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, codeOf, found, group, headerText, hostOf, signedUrl,
} from './twilio-signature-403-audit.mjs';

const alert = (sid, url, code = '11200', when = '2026-04-02T10:00:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when,
  request_method: 'POST', log_level: 'error',
});

const detail = (body = '', headers = null) => ({
  response_body: body, response_headers: headers,
});

test('codeOf reads the string the Monitor API returns', () => {
  assert.equal(codeOf({ error_code: '11200' }), 11200);
  assert.equal(codeOf({ error_code: 11200 }), 11200);
  assert.equal(codeOf({ error_code: '' }), null);
  assert.equal(codeOf({}), null);
});

test('signedUrl keeps everything the HMAC covers', () => {
  const a = alert('NO1', 'https://hooks.example.com:8443/twilio/voice?From=%2B15551112222');
  assert.equal(signedUrl(a),
    'https://hooks.example.com:8443/twilio/voice?From=%2B15551112222');
});

test('hostOf throws away what signedUrl keeps', () => {
  assert.equal(hostOf('https://Hooks.Example.com:8443/twilio/voice?a=b'),
    'hooks.example.com');
  assert.equal(hostOf(null), '');
});

test('a body naming the header is a signature rejection', () => {
  const [state, why] = classify(alert('NO1', 'https://a.example.com/voice'),
    detail('Invalid signature for X-Twilio-Signature'));
  assert.equal(state, 'signature');
  assert.match(why, /URL/);
});

test('a bare 403 page is not blamed on the validator', () => {
  const [state, why] = classify(alert('NO1', 'https://a.example.com/voice'),
    detail('<html><head><title>403 Forbidden</title></head></html>'));
  assert.equal(state, 'forbidden');
  assert.match(why, /WAF/);
});

test('a stack trace is an application error', () => {
  const [state] = classify(alert('NO1', 'https://a.example.com/voice'),
    detail('Traceback (most recent call last):\\n  File ...'));
  assert.equal(state, 'app-error');
});

test('an empty body is reported as unknown rather than guessed', () => {
  const [state] = classify(alert('NO1', 'https://a.example.com/voice'), detail(''));
  assert.equal(state, 'no-body');
});

test('without the single-alert fetch there is no verdict', () => {
  const [state, why] = classify(alert('NO1', 'https://a.example.com/voice'), null);
  assert.equal(state, 'unfetched');
  assert.match(why, /response_body/);
});

test('markers are also read from the response headers', () => {
  const [state] = classify(alert('NO1', 'https://a.example.com/voice'),
    detail('', { 'X-Rejected-By': 'RequestValidator', Server: 'gunicorn' }));
  assert.equal(state, 'signature');
});

test('headerText flattens every shape the field arrives in', () => {
  assert.equal(headerText({ A: '1' }), 'A: 1');
  assert.equal(headerText(['A: 1', 'B: 2']), 'A: 1\\nB: 2');
  assert.equal(headerText('A: 1'), 'A: 1');
  assert.equal(headerText(null), '');
});

test('group buckets by host and records the ends', () => {
  const rows = group([
    alert('NO1', 'https://a.example.com/voice?x=1', '11200', '2026-04-02T10:00:00Z'),
    alert('NO2', 'https://a.example.com/sms?x=2', '11200', '2026-04-01T09:00:00Z'),
    alert('NO3', 'https://b.example.com/voice', '11205'),
  ]);
  assert.deepEqual([...rows.keys()], ['a.example.com']);
  assert.equal(rows.get('a.example.com').alerts, 2);
  assert.equal(rows.get('a.example.com').first, '2026-04-01T09:00:00Z');
  assert.ok(rows.get('a.example.com').urls[0].endsWith('?x=1'));
});

test('found is case-insensitive', () => {
  assert.deepEqual(found('INVALID SIGNATURE', ['invalid signature']),
    ['invalid signature']);
  assert.deepEqual(found(null, ['invalid signature']), []);
});
''',
"faq": [
 ("Why does it work locally and fail behind the load balancer?",
  "Because locally your app sees the same URL Twilio called, and behind a proxy it does not. The proxy terminates TLS and forwards http:// to an internal hostname, so the app reconstructs a URL that differs from the signed one in scheme, host or port. The HMAC is over the whole string, so one character is enough."),
 ("Is there a Twilio error code specific to this?",
  "No. It arrives as 11200, the generic HTTP retrieval failure, exactly like a 404 or a 500. That is why the script fetches alerts individually: the error code cannot tell these apart, and the response body can."),
 ("Why can't the alerts list show me the response body?",
  "Because response_body, response_headers, request_headers and request_variables are populated only on the single-alert fetch, GET /v1/Alerts/{Sid}. Every row of the list has them blank. The list is the cheap sweep; reading a body is one request per alert, which is why the sample size is an argument."),
 ("Should I just trust X-Forwarded-Proto and X-Forwarded-Host?",
  "Only from your own proxy. Those headers are client-supplied unless something you control overwrites them, so an app that trusts them from anywhere lets a caller choose the URL its own signature is checked against. Terminate the trust at the proxy, or hardcode the public base URL instead."),
 ("Can I confirm the fix without waiting for real traffic?",
  "Yes, and that is the fastest route. Take request_url from a failing alert exactly as logged, feed it to the validator with the POST parameters and the signature header, and you reproduce the rejection offline. Then rerun with the rebuilt URL and watch it pass."),
],
"related": [
 ("/twilio/status-callback-webhook-failing-11200/", "11200 on a status callback leaves delivery state blind"),
 ("/twilio/twiml-document-parse-failure-12100/", "TwiML that is not well-formed XML"),
 ("/twilio/webhook-connection-timeout-11205/", "Twilio cannot open a connection to your webhook"),
],
"citations": [CITE_SECURITY, CITE_11200, CITE_ALERTS, CITE_WEBHOOKS],
},


{
"slug": "webhook-invalid-content-type-12300",
"title": "A TwiML response with the wrong Content-Type fails with 12300",
"description": "The body is valid TwiML and Twilio never parses it. 12300 is decided on the response header, and a missing header shows up as 502 instead.",
"h1": "a TwiML response with the wrong Content-Type fails with 12300",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 12300", "twilio invalid content-type",
             "twilio twiml content type text/xml", "twilio 502 bad gateway webhook",
             "twilio play url not audio"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You paste the URL into a browser and the TwiML is right there, well-formed, exactly what you meant to send. Twilio disagrees: <code>12300 Invalid Content-Type</code>, and the call ends. Nothing is wrong with the document. The rejection happened on a header, before Twilio looked at a single byte of the body.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> for <code>error_code == 12300</code>, then fetch each interesting alert with <code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> and read the <code>Content-Type</code> out of <code>response_headers</code>. That field only exists on the single-alert fetch.</p>
<p>Twilio dispatches on the media type. <code>text/xml</code> and <code>application/xml</code> are parsed as TwiML; <code>text/html</code>, <code>application/json</code> and <code>text/plain</code> are not, whatever the body contains. No header at all is the nastiest case, because the Debugger reports that as <code>502 Bad Gateway</code> rather than 12300 and the hunt starts in the wrong place.</p>""",
"problem": """<p>This failure inverts the usual debugging order. Normally the body is suspect and the headers are boring, so you read the body, find nothing wrong with it, and conclude the problem must be elsewhere &mdash; routing, caching, the wrong deploy. The document is fine. It was always fine. Twilio simply never got as far as reading it.</p>
<p>It also arrives in two disguises. A framework that defaults to <code>text/html</code> gives you a clean 12300 with a clear name. A serverless function that returns a string with no headers at all gives you <code>502 Bad Gateway</code> in the Debugger, which reads like an infrastructure problem and sends people to look at the gateway, the timeout and the cold start &mdash; anywhere except the two words missing from the response.</p>
<p>And the same error code covers a case that is not TwiML at all: a <code>&lt;Play&gt;</code> pointing at a URL that serves an HTML error page instead of audio. Same code, same alert shape, different file and different fix.</p>""",
"why": """<p><strong>The media type is the routing decision.</strong> Twilio has to know whether the response is TwiML, audio for <code>&lt;Play&gt;</code>, or something it should refuse. It answers that from <code>Content-Type</code>, because sniffing bodies is how a security bug gets written. A valid TwiML document served as <code>text/html</code> is, to that decision, an HTML page.</p>
<p><strong>Frameworks default to HTML and serverless defaults to nothing.</strong> Returning a string from a handler gives you the framework's default media type, which is almost always <code>text/html</code>. A function returning a bare string through an API gateway may send no <code>Content-Type</code> at all. Neither is a mistake anyone typed; both are what happens when nobody sets the header explicitly.</p>
<p><strong>A missing header is reported as a different failure.</strong> Requests with no <code>Content-Type</code> show in the Debugger as <code>502 Bad Gateway</code>. Searching for 12300 will not find them, and searching for the cause of a 502 leads to gateways and timeouts. This is the single reason the check has to look at the header value rather than only counting error codes.</p>
<p><strong>The header is not in the alerts list.</strong> <code>response_headers</code> is populated only on the single-alert fetch, <code>GET /v1/Alerts/{Sid}</code>. The list gives you the endpoint and the count; the actual media type that was sent costs one request per alert.</p>""",
"steps": [
 {"h": "Sweep for 12300 and group by endpoint",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>, keeping alerts where <code>error_code</code> is <code>12300</code>. Read the code as an integer: the Monitor API returns it as a string. Group by host and path so one broken handler is one line.</p>"""},
 {"h": "Fetch one alert per endpoint and read the header",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> returns <code>response_headers</code>, which the list omits. Look up <code>Content-Type</code> case-insensitively &mdash; header names are not case-sensitive and the field does not arrive in a consistent shape across products, so accept a mapping, a list of lines and a single blob.</p>"""},
 {"h": "Compare the media type, not the whole header",
  "body": """<p><code>text/xml; charset=utf-8</code> is correct and an exact-match check on <code>text/xml</code> rejects it. Split on the semicolon, trim, lowercase, then compare. Everything after the semicolon is a parameter and none of it changes the routing decision.</p>"""},
 {"h": "Split the verdict by what was actually sent",
  "body": """<p><code>text/html</code> is a framework default. <code>application/json</code> is an API handler wired to the wrong route. <code>text/plain</code> is a string return. An empty value is the missing-header case that reads as 502. And <code>audio/*</code> means the alert is about a <code>&lt;Play&gt;</code> target, not your TwiML at all. Four different files get edited.</p>"""},
 {"h": "Set the header explicitly and re-run",
  "body": """<p>Send <code>Content-Type: text/xml</code> (or <code>application/xml</code>) on every TwiML response, from every branch of the handler including the error branches, and serve <code>&lt;Play&gt;</code> targets as <code>audio/mpeg</code> or <code>audio/wav</code>. Re-run the sweep over a window that starts after the deploy; the count should be zero rather than smaller.</p>"""},
],
"verify": """<p>Re-run over a window beginning after the deploy. A smaller count is not a fix &mdash; it is the same bug on a quieter route.</p>
<pre><code class="language-bash">python3 twilio_content_type_audit.py --days 1
# 0 endpoint(s) returning a Content-Type Twilio will not parse</code></pre>""",
"code_intro": "Two pure functions carry the whole check and both exist because of a shape mismatch rather than a rule. <code>header_value()</code> finds a header case-insensitively across the shapes <code>response_headers</code> arrives in, and <code>content_type_verdict()</code> compares media types with the parameters stripped. The network part is a sweep plus one fetch per endpoint, capped, because that fetch is the only place the header exists.",
"py_file": "twilio_content_type_audit.py",
"py": '''"""Report Twilio webhooks returning a Content-Type that TwiML parsing rejects.

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
log = logging.getLogger("twilio_content_type_audit")

MONITOR = "https://monitor.twilio.com/v1"

INVALID_CONTENT_TYPE = 12300

# Alerts are retained 30 days. A longer window is not more history, it is the
# same history under a label that makes the report look more thorough.
MAX_DAYS = 30

# The two media types Twilio will parse as TwiML.
TWIML_TYPES = ("text/xml", "application/xml")


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API hands this back as a string while the Messages list hands
    back a number for the same concept, and a check written for one and pointed
    at the other matches nothing and reports a healthy account.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def endpoint_of(url):
    """Lowercase host plus path, for grouping. Query string dropped."""
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        return str(url).strip().lower().rstrip("/")
    return host + (parts.path or "").rstrip("/")


def header_value(headers, name):
    """Case-insensitively read one header out of an alert's response_headers.

    Two things make this less trivial than it looks. Header names are not
    case-sensitive, so a lookup for "Content-Type" has to find "content-type".
    And the field does not arrive in one shape: it can be a mapping, a list of
    lines, or a single blob using either ':' or '=' between name and value.
    Supporting only the shape you saw first is how a check stops matching.
    """
    want = str(name).strip().lower()
    if headers is None:
        return ""
    if isinstance(headers, dict):
        for k, v in headers.items():
            if str(k).strip().lower() == want:
                return str(v).strip()
        return ""
    if isinstance(headers, (list, tuple)):
        lines = [str(h) for h in headers]
    else:
        lines = str(headers).replace("\\r\\n", "\\n").replace("&", "\\n").split("\\n")
    for line in lines:
        for sep in (":", "="):
            k, found, v = line.partition(sep)
            if found and k.strip().lower() == want:
                return v.strip()
    return ""


def media_type(value):
    """The media type with its parameters stripped.

    'text/xml; charset=utf-8' is a correct TwiML response and an exact-match
    check on 'text/xml' rejects it. Everything after the semicolon is a
    parameter and none of it changes how Twilio routes the response.
    """
    return str(value or "").split(";", 1)[0].strip().lower()


def content_type_verdict(value):
    """Classify one Content-Type. Pure, so every branch is testable offline.

    Returns (state, detail).
    """
    mt = media_type(value)

    if not mt:
        return ("missing",
                "no Content-Type at all. Twilio has nothing to dispatch on, and "
                "the Debugger shows this as 502 Bad Gateway rather than 12300, "
                "which is why it gets chased as a gateway problem.")

    if mt in TWIML_TYPES:
        return ("ok", "%s is parsed as TwiML" % mt)

    if mt.startswith("audio/"):
        return ("audio",
                "%s is an audio type, so this alert is about a <Play> target "
                "rather than your TwiML. Fix the file that URL serves, not the "
                "webhook." % mt)

    if mt in ("text/html", "application/xhtml+xml"):
        return ("html",
                "%s is the framework default when nothing sets the header. The "
                "body may be perfect TwiML; Twilio never reads it." % mt)

    if mt in ("application/json", "text/json"):
        return ("json",
                "%s means an API handler is answering a TwiML webhook. Either "
                "the route is wrong or the serialiser is." % mt)

    if mt == "text/plain":
        return ("plain",
                "text/plain is what a bare string return produces. Set the "
                "header explicitly on every branch of the handler.")

    if mt.endswith("+xml"):
        return ("odd-xml",
                "%s is XML-shaped but is not one of the two media types Twilio "
                "dispatches TwiML on. Send text/xml or application/xml." % mt)

    return ("other",
            "%s is not a media type Twilio parses as TwiML." % mt)


def group(alerts, code=INVALID_CONTENT_TYPE):
    """Bucket alerts with one error code by endpoint. Pure.

    date_generated is ISO 8601 in UTC, so a string comparison finds the ends of
    the window without parsing anything.
    """
    out = {}
    for a in alerts:
        if code_of(a) != code:
            continue
        key = endpoint_of(a.get("request_url"))
        row = out.setdefault(key, {"alerts": 0, "sids": [], "first": None,
                                   "last": None})
        row["alerts"] += 1
        if len(row["sids"]) < 3:
            row["sids"].append(a.get("sid"))
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
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
    """One alert by SID: the only place response_headers is populated."""
    return get(session, "%s/Alerts/%s" % (MONITOR, sid))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=1,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    ap.add_argument("--sample", type=int, default=1,
                    help="alerts to fetch individually per endpoint for the "
                         "response headers (each one is a request)")
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
    rows = group(alerts)
    log.info("%d alert(s) since %s, %d endpoint(s) with 12300", len(alerts),
             since, len(rows))

    bad = 0
    for key, row in sorted(rows.items()):
        sent = ""
        for sid in row["sids"][:max(1, args.sample)]:
            sent = header_value(fetch_alert(session, sid).get("response_headers"),
                                "Content-Type")
            if sent:
                break
        state, detail = content_type_verdict(sent)
        log.warning("%-8s %s  %d x 12300  %s", state, key, row["alerts"], detail)
        log.warning("  first %s, last %s", row["first"], row["last"])
        if state == "ok":
            log.warning("  the sampled alert carried a valid TwiML type: sample "
                        "more alerts, the failing responses came from another "
                        "branch of the handler")
            continue
        bad += 1
        if state == "audio":
            log.warning("  repair: serve that <Play> URL as audio/mpeg or "
                        "audio/wav; it is currently an HTML or error response")
        else:
            log.warning("  repair: set Content-Type: text/xml on this response, "
                        "on every branch of the handler including the error "
                        "branches")

    log.info("%d endpoint(s) returning a Content-Type Twilio will not parse", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-content-type-audit.mjs",
"js": '''/**
 * Report Twilio webhooks returning a Content-Type that TwiML parsing rejects.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';

const INVALID_CONTENT_TYPE = 12300;

// Alerts are retained 30 days. A longer window is the same history mislabelled.
const MAX_DAYS = 30;

// The two media types Twilio will parse as TwiML.
const TWIML_TYPES = ['text/xml', 'application/xml'];

/** Read error_code off an alert as a number, or null. */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** Lowercase host plus path, for grouping. Query string dropped. */
export function endpointOf(url) {
  if (!url) return '';
  const raw = String(url).trim();
  try {
    const u = new URL(raw);
    let path = u.pathname;
    while (path.endsWith('/')) path = path.slice(0, -1);
    return u.hostname.toLowerCase() + path;
  } catch {
    return raw.toLowerCase().replace(/\\/+$/, '');
  }
}

/**
 * Case-insensitively read one header out of an alert's response_headers. The
 * field arrives as a mapping, a list of lines or one blob using ':' or '='.
 */
export function headerValue(headers, name) {
  const want = String(name).trim().toLowerCase();
  if (headers === null || headers === undefined) return '';
  if (!Array.isArray(headers) && typeof headers === 'object') {
    for (const [k, v] of Object.entries(headers)) {
      if (k.trim().toLowerCase() === want) return String(v).trim();
    }
    return '';
  }
  const lines = Array.isArray(headers)
    ? headers.map(String)
    : String(headers).replace(/\\r\\n/g, '\\n').split(/[\\n&]/);
  for (const line of lines) {
    for (const sep of [':', '=']) {
      const at = line.indexOf(sep);
      if (at > 0 && line.slice(0, at).trim().toLowerCase() === want) {
        return line.slice(at + 1).trim();
      }
    }
  }
  return '';
}

/**
 * The media type with its parameters stripped. 'text/xml; charset=utf-8' is a
 * correct TwiML response and an exact-match check rejects it.
 */
export function mediaType(value) {
  return String(value ?? '').split(';')[0].trim().toLowerCase();
}

/** Classify one Content-Type. Pure. Returns [state, detail]. */
export function contentTypeVerdict(value) {
  const mt = mediaType(value);

  if (!mt) {
    return ['missing',
      'no Content-Type at all. Twilio has nothing to dispatch on, and the ' +
      'Debugger shows this as 502 Bad Gateway rather than 12300, which is why ' +
      'it gets chased as a gateway problem.'];
  }

  if (TWIML_TYPES.includes(mt)) return ['ok', `${mt} is parsed as TwiML`];

  if (mt.startsWith('audio/')) {
    return ['audio',
      `${mt} is an audio type, so this alert is about a <Play> target rather ` +
      'than your TwiML. Fix the file that URL serves, not the webhook.'];
  }

  if (mt === 'text/html' || mt === 'application/xhtml+xml') {
    return ['html',
      `${mt} is the framework default when nothing sets the header. The body ` +
      'may be perfect TwiML; Twilio never reads it.'];
  }

  if (mt === 'application/json' || mt === 'text/json') {
    return ['json',
      `${mt} means an API handler is answering a TwiML webhook. Either the ` +
      'route is wrong or the serialiser is.'];
  }

  if (mt === 'text/plain') {
    return ['plain',
      'text/plain is what a bare string return produces. Set the header ' +
      'explicitly on every branch of the handler.'];
  }

  if (mt.endsWith('+xml')) {
    return ['odd-xml',
      `${mt} is XML-shaped but is not one of the two media types Twilio ` +
      'dispatches TwiML on. Send text/xml or application/xml.'];
  }

  return ['other', `${mt} is not a media type Twilio parses as TwiML.`];
}

/** Bucket alerts with one error code by endpoint. Pure. */
export function group(alerts, code = INVALID_CONTENT_TYPE) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== code) continue;
    const key = endpointOf(a.request_url);
    if (!out.has(key)) out.set(key, { alerts: 0, sids: [], first: null, last: null });
    const row = out.get(key);
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

/** One alert by SID: the only place response_headers is populated. */
export async function fetchAlert(auth, sid) {
  return get(auth, `${MONITOR}/Alerts/${sid}`);
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
    ? process.argv[process.argv.indexOf('--days') + 1] : 1) || 1;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await listAlerts(auth, since);
  const rows = group(alerts);
  console.log(`${alerts.length} alert(s) since ${since}, ${rows.size} endpoint(s) with 12300`);

  let bad = 0;
  for (const [key, row] of [...rows.entries()].sort()) {
    let sent = '';
    for (const sid of row.sids.slice(0, 1)) {
      const full = await fetchAlert(auth, sid);
      sent = headerValue(full.response_headers, 'Content-Type');
    }
    const [state, detail] = contentTypeVerdict(sent);
    console.warn(`${state.padEnd(8)} ${key}  ${row.alerts} x 12300  ${detail}`);
    console.warn(`  first ${row.first}, last ${row.last}`);
    if (state === 'ok') {
      console.warn('  the sampled alert carried a valid TwiML type: sample more ' +
                   'alerts, the failing responses came from another branch of ' +
                   'the handler');
      continue;
    }
    bad += 1;
    if (state === 'audio') {
      console.warn('  repair: serve that <Play> URL as audio/mpeg or audio/wav; ' +
                   'it is currently an HTML or error response');
    } else {
      console.warn('  repair: set Content-Type: text/xml on this response, on ' +
                   'every branch of the handler including the error branches');
    }
  }

  console.log(`${bad} endpoint(s) returning a Content-Type Twilio will not parse`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three things break this check in practice and each one has a test. A correct response carrying <code>; charset=utf-8</code> must not be reported as wrong. A header spelled <code>content-type</code> in lowercase must still be found. And an empty value must come back as its own state rather than as <code>other</code>, because that is the case the Debugger hides behind a 502.",
"test_py_file": "test_twilio_content_type_audit.py",
"test_py": '''from twilio_content_type_audit import (code_of, content_type_verdict, endpoint_of,
                                         group, header_value, media_type)


def alert(sid, url, code="12300", when="2026-04-02T10:00:00Z"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when, "log_level": "error"}


def test_code_of_reads_the_string_the_monitor_api_returns():
    assert code_of({"error_code": "12300"}) == 12300
    assert code_of({"error_code": 12300}) == 12300
    assert code_of({}) is None


def test_a_charset_parameter_does_not_make_the_type_wrong():
    # The single most common false positive: this response is correct.
    assert content_type_verdict("text/xml; charset=utf-8")[0] == "ok"
    assert content_type_verdict("TEXT/XML")[0] == "ok"
    assert content_type_verdict("application/xml")[0] == "ok"


def test_a_missing_header_is_its_own_state_because_it_reads_as_502():
    state, detail = content_type_verdict("")
    assert state == "missing"
    assert "502" in detail
    assert content_type_verdict(None)[0] == "missing"


def test_html_json_and_plain_are_told_apart():
    assert content_type_verdict("text/html; charset=utf-8")[0] == "html"
    assert content_type_verdict("application/json")[0] == "json"
    assert content_type_verdict("text/plain")[0] == "plain"


def test_an_audio_type_means_the_alert_is_about_a_play_target():
    state, detail = content_type_verdict("audio/mpeg")
    assert state == "audio"
    assert "<Play>" in detail


def test_an_xml_flavoured_type_is_still_not_twiml():
    assert content_type_verdict("application/soap+xml")[0] == "odd-xml"
    assert content_type_verdict("application/pdf")[0] == "other"


def test_header_lookup_is_case_insensitive_across_every_shape():
    assert header_value({"content-type": "text/html"}, "Content-Type") == "text/html"
    assert header_value(["Server: nginx", "Content-Type: text/html"],
                        "Content-Type") == "text/html"
    assert header_value("Server: nginx\\nContent-Type: text/html",
                        "content-type") == "text/html"
    assert header_value("Server=nginx&Content-Type=application/json",
                        "Content-Type") == "application/json"
    assert header_value(None, "Content-Type") == ""


def test_media_type_strips_parameters_and_whitespace():
    assert media_type("  Text/XML ; charset=UTF-8 ") == "text/xml"
    assert media_type(None) == ""


def test_group_keeps_only_the_requested_code_and_records_the_ends():
    rows = group([
        alert("NO1", "https://a.example.com/voice?CallSid=CA1",
              when="2026-04-02T10:00:00Z"),
        alert("NO2", "https://a.example.com/voice/", when="2026-04-01T09:00:00Z"),
        alert("NO3", "https://a.example.com/voice", code="12100"),
    ])
    assert set(rows) == {"a.example.com/voice"}
    assert rows["a.example.com/voice"]["alerts"] == 2
    assert rows["a.example.com/voice"]["first"] == "2026-04-01T09:00:00Z"


def test_endpoint_of_drops_the_query_string_twilio_appends():
    assert endpoint_of("https://A.example.com/voice?CallSid=CA1") == \\
        "a.example.com/voice"
    assert endpoint_of(None) == ""
''',
"test_js_file": "twilio-content-type-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  codeOf, contentTypeVerdict, endpointOf, group, headerValue, mediaType,
} from './twilio-content-type-audit.mjs';

const alert = (sid, url, code = '12300', when = '2026-04-02T10:00:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when, log_level: 'error',
});

test('codeOf reads the string the Monitor API returns', () => {
  assert.equal(codeOf({ error_code: '12300' }), 12300);
  assert.equal(codeOf({ error_code: 12300 }), 12300);
  assert.equal(codeOf({}), null);
});

test('a charset parameter does not make the type wrong', () => {
  assert.equal(contentTypeVerdict('text/xml; charset=utf-8')[0], 'ok');
  assert.equal(contentTypeVerdict('TEXT/XML')[0], 'ok');
  assert.equal(contentTypeVerdict('application/xml')[0], 'ok');
});

test('a missing header is its own state because it reads as 502', () => {
  const [state, detail] = contentTypeVerdict('');
  assert.equal(state, 'missing');
  assert.match(detail, /502/);
  assert.equal(contentTypeVerdict(null)[0], 'missing');
});

test('html, json and plain are told apart', () => {
  assert.equal(contentTypeVerdict('text/html; charset=utf-8')[0], 'html');
  assert.equal(contentTypeVerdict('application/json')[0], 'json');
  assert.equal(contentTypeVerdict('text/plain')[0], 'plain');
});

test('an audio type means the alert is about a Play target', () => {
  const [state, detail] = contentTypeVerdict('audio/mpeg');
  assert.equal(state, 'audio');
  assert.match(detail, /<Play>/);
});

test('an xml-flavoured type is still not TwiML', () => {
  assert.equal(contentTypeVerdict('application/soap+xml')[0], 'odd-xml');
  assert.equal(contentTypeVerdict('application/pdf')[0], 'other');
});

test('header lookup is case-insensitive across every shape', () => {
  assert.equal(headerValue({ 'content-type': 'text/html' }, 'Content-Type'), 'text/html');
  assert.equal(headerValue(['Server: nginx', 'Content-Type: text/html'], 'Content-Type'),
    'text/html');
  assert.equal(headerValue('Server: nginx\\nContent-Type: text/html', 'content-type'),
    'text/html');
  assert.equal(headerValue('Server=nginx&Content-Type=application/json', 'Content-Type'),
    'application/json');
  assert.equal(headerValue(null, 'Content-Type'), '');
});

test('mediaType strips parameters and whitespace', () => {
  assert.equal(mediaType('  Text/XML ; charset=UTF-8 '), 'text/xml');
  assert.equal(mediaType(null), '');
});

test('group keeps only the requested code and records the ends', () => {
  const rows = group([
    alert('NO1', 'https://a.example.com/voice?CallSid=CA1', '12300', '2026-04-02T10:00:00Z'),
    alert('NO2', 'https://a.example.com/voice/', '12300', '2026-04-01T09:00:00Z'),
    alert('NO3', 'https://a.example.com/voice', '12100'),
  ]);
  assert.deepEqual([...rows.keys()], ['a.example.com/voice']);
  assert.equal(rows.get('a.example.com/voice').alerts, 2);
  assert.equal(rows.get('a.example.com/voice').first, '2026-04-01T09:00:00Z');
});

test('endpointOf drops the query string Twilio appends', () => {
  assert.equal(endpointOf('https://A.example.com/voice?CallSid=CA1'), 'a.example.com/voice');
  assert.equal(endpointOf(null), '');
});
''',
"faq": [
 ("My body is valid TwiML. Why does Twilio reject it?",
  "Because the decision is made on the response header, not the body. Twilio dispatches on Content-Type: text/xml and application/xml are parsed as TwiML, and anything else is refused before the body is read. A perfect document served as text/html is, to that decision, an HTML page."),
 ("Is application/xml as good as text/xml?",
  "Yes. Both are parsed as TwiML, and both are fine with a charset parameter attached. The script treats them identically, which is why it compares the media type with the parameters stripped rather than matching the header string."),
 ("Why do I see 502 Bad Gateway instead of 12300?",
  "That is the missing-header case. When the response carries no Content-Type at all, the Debugger reports 502 Bad Gateway rather than an invalid content type, so searching for 12300 will not find it and the investigation starts at the gateway. The script reports an empty header as its own state for exactly this reason."),
 ("Why does an audio media type show up in a TwiML report?",
  "Because 12300 also covers a <Play> whose URL serves something that is not audio. The alert looks the same, but the file to fix is the media asset rather than the webhook, so it gets its own state and its own printed repair."),
 ("Can I see the Content-Type without fetching each alert?",
  "No. response_headers is populated only on the single-alert fetch, GET /v1/Alerts/{Sid}, and is blank on every row of the list. The list gives you the endpoint and the count; reading the header is one request per alert, which is why the sample is capped."),
],
"related": [
 ("/twilio/twiml-document-parse-failure-12100/", "TwiML that is not well-formed XML"),
 ("/twilio/twiml-response-body-too-large-11750/", "A TwiML response over the 64 kB limit"),
 ("/twilio/status-callback-webhook-failing-11200/", "11200 on a status callback leaves delivery state blind"),
],
"citations": [CITE_12300, CITE_ALERTS, CITE_TWIML_VOICE, CITE_TWIML_PLAY],
},


{
"slug": "twiml-document-parse-failure-12100",
"title": "TwiML that is not well-formed XML fails with 12100",
"description": "12100 is an XML parser refusing your document. Usually one blank line before the declaration. The bytes Twilio received are one fetch away.",
"h1": "TwiML that is not well-formed XML fails with 12100",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 12100", "twilio document parse failure",
             "twiml invalid xml", "twilio application error message",
             "twilio twiml whitespace before xml declaration"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The caller hears &ldquo;an application error has occurred&rdquo; and the line goes dead. Your handler ran, returned <code>200</code>, and logged nothing unusual. Twilio logged <code>12100 Document parse failure</code>, which means an XML parser looked at what you sent and refused it &mdash; and the usual reason is a single blank line that no code review will ever show you.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> for <code>error_code == 12100</code>, then fetch the interesting ones with <code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code>. <code>response_body</code> holds the exact bytes Twilio received and <code>alert_text</code> names the line and column. Neither is in the list response.</p>
<p>Diagnose the body rather than eyeballing it: output before the XML declaration, a UTF-8 byte order mark, an HTML error page where TwiML was expected, a missing <code>&lt;Response&gt;</code> root, a bare <code>&amp;</code> in interpolated text, or a tag opened and never closed. Sweep <code>LogLevel=warning</code> in the same run too &mdash; its sibling 12200 is logged as a warning and never appears in an error-only query.</p>""",
"problem": """<p>What makes 12100 disproportionately annoying is that the fault is usually invisible in the source. Nobody wrote invalid XML. The template is fine, the view is fine, the TwiML builder is fine &mdash; and then a newline after a closing PHP tag, or a stray line at the top of an included header, or a byte order mark added by an editor puts one character before the XML declaration. XML permits nothing there. The parser stops at position zero.</p>
<p>Meanwhile the caller gets the worst possible experience for something so small: a generic application-error recording and a dropped call, with no way for them to tell you what happened. Your own logs show a clean <code>200</code>, because from the handler's point of view it did its job. The only place the truth exists is in the alert, and only if you fetch that alert individually.</p>
<p>And there is a quieter neighbour. TwiML that parses but uses a verb Twilio does not recognise raises <code>12200</code>, which is logged at <code>LogLevel=warning</code>. A dashboard that only ever queries errors reports an account with no TwiML problems while every call silently skips a verb.</p>""",
"why": """<p><strong>XML allows nothing before the declaration.</strong> Not a space, not a newline, not a byte order mark. Any of those and the document is malformed at the first byte, whatever follows it. This is why the failure is so often a whitespace character nobody can see in a diff.</p>
<p><strong>The handler cannot tell that it failed.</strong> It returned <code>200</code> with a body it believes in. The rejection happens inside Twilio's parser, after the response has left your process, so nothing in your logging or your error tracker knows anything went wrong.</p>
<p><strong>Unescaped text is the second cause and it is data-dependent.</strong> Interpolating a customer name containing <code>&amp;</code> into <code>&lt;Say&gt;</code> produces invalid XML for that one caller and valid XML for everybody else. It passes every test written with sensible fixtures and fails in production on the account belonging to a company with an ampersand in its name.</p>
<p><strong>The bytes are only on the single-alert fetch.</strong> <code>response_body</code> is blank on every row of <code>GET /v1/Alerts</code>. It is populated when you fetch one alert by SID, and it is the only place you can see what actually left your server &mdash; which matters here more than anywhere, because what left your server is not what your template says.</p>
<p><strong>Its sibling hides at a different log level.</strong> 12200 schema validation is a warning, not an error. Sweeping only <code>LogLevel=error</code> is how a report comes back clean while calls quietly skip a misspelled verb.</p>""",
"steps": [
 {"h": "Sweep both log levels, not just errors",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code> for the 12100s, then the same query with <code>LogLevel=warning</code> for 12200. They are the same family of problem and only one of them is an error, so a single-level sweep gives a false all-clear.</p>"""},
 {"h": "Group by endpoint before you fetch anything",
  "body": """<p>One broken template usually produces hundreds of identical alerts. Group by host and path first, then sample. That turns a report into a handful of lines and keeps the number of single-alert fetches proportional to the number of distinct problems rather than to traffic.</p>"""},
 {"h": "Fetch a sample by SID and read the actual bytes",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> returns <code>response_body</code>: precisely what Twilio received, including the leading whitespace your editor will not show you. <code>alert_text</code> carries the line and column the parser stopped at. Print both, and print the first forty characters as a repr so an invisible character becomes visible.</p>"""},
 {"h": "Classify the body instead of reading it by eye",
  "body": """<p>Leading whitespace, a byte order mark, an HTML error page, a missing <code>&lt;Response&gt;</code> root, a bare <code>&amp;</code>, an unclosed tag: six causes with six different repairs, and each is a mechanical check over the body. Doing it by eye works until the body is 4 kB of generated TwiML.</p>"""},
 {"h": "Fix the emission point, then re-run over a fresh window",
  "body": """<p>Emit the XML declaration as the first byte with nothing before it, save templates without a BOM, and XML-escape every interpolated value rather than the ones that looked risky. Then re-run with a window that starts after the deploy. Alerts are retained 30 days, so a stale window will keep showing you the old failures for a month.</p>"""},
],
"verify": """<p>Re-run over a window that begins after the deploy. Both counts should be zero, including the warning-level one.</p>
<pre><code class="language-bash">python3 twilio_twiml_parse_audit.py --days 1
# 0 endpoint(s) returning malformed TwiML, 0 schema warning(s) at LogLevel=warning</code></pre>""",
"code_intro": "The diagnosis is a pure function over the response body, which is what makes this checkable at all: six causes, ordered so the earliest byte wins, and each with its own repair. The unclosed-tag check is a small tag balancer rather than a real XML parser, because a real parser refuses the document and tells you where &mdash; it does not tell you <em>which element</em> was left open, which is the thing you need to go and fix.",
"py_file": "twilio_twiml_parse_audit.py",
"py": '''"""Report Twilio webhooks returning TwiML that is not well-formed XML.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import re
import sys
from urllib.parse import unquote_plus, urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_twiml_parse_audit")

MONITOR = "https://monitor.twilio.com/v1"

PARSE_FAILURE = 12100
# Logged at LogLevel=warning, never at error. Sweeping one level is how an
# account with hundreds of skipped verbs reports as clean.
SCHEMA_WARNING = 12200

# Alerts are retained 30 days. A longer window is not more history, it is the
# same history under a label that makes the report look more thorough.
MAX_DAYS = 30

# A '&' that does not begin a named, decimal or hex entity. This is the second
# most common 12100 and the only one that depends on the data rather than the
# code: one customer with an ampersand in their name breaks one call.
UNESCAPED_AMP = re.compile(r"&(?!(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#[xX][0-9A-Fa-f]+);)")

TAG = re.compile(r"<\\s*(/?)\\s*([A-Za-z][\\w.:-]*)([^>]*?)(/?)\\s*>", re.S)

LINE_AT = re.compile(r"line\\s*[:= ]\\s*(\\d+)", re.I)
COLUMN_AT = re.compile(r"column\\s*[:= ]\\s*(\\d+)", re.I)


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API hands this back as a string while the Messages list hands
    back a number for the same concept, and a check written for one and pointed
    at the other matches nothing and reports a healthy account.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def endpoint_of(url):
    """Lowercase host plus path, for grouping. Query string dropped."""
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        return str(url).strip().lower().rstrip("/")
    return host + (parts.path or "").rstrip("/")


def unbalanced(xml):
    """The name of the first element left open, or None.

    Deliberately not an XML parser. A parser refuses the document and tells you
    where it stopped, which is a position; what you need in order to fix it is
    which element was never closed. Declarations, comments and self-closing tags
    are skipped. Attribute values containing '>' will confuse it, which is worth
    less than the answer it gives on every other document.
    """
    body = re.sub(r"<\\?.*?\\?>", "", str(xml or ""), flags=re.S)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    stack = []
    for m in TAG.finditer(body):
        closing, name, _attrs, selfclose = m.groups()
        if selfclose:
            continue
        if closing:
            if stack and stack[-1] == name:
                stack.pop()
            else:
                return stack[-1] if stack else name
        else:
            stack.append(name)
    return stack[-1] if stack else None


def diagnose(body):
    """Say why a response body is not well-formed TwiML. Pure.

    Ordered so the earliest byte wins, because that is the order the parser
    fails in: anything before the declaration ends the document at position
    zero, whatever is wrong further down.

    Returns (cause, detail).
    """
    raw = "" if body is None else str(body)
    if not raw.strip():
        return ("no-body",
                "the single-alert fetch returned an empty body. Either the "
                "handler sent nothing, or this alert predates what the API "
                "still stores.")

    if raw.startswith("\\ufeff"):
        return ("byte-order-mark",
                "the document begins with a UTF-8 byte order mark. XML allows "
                "nothing before the declaration, and an editor added three "
                "bytes no diff will show you.")

    stripped = raw.lstrip()
    if not raw.startswith("<"):
        prefix = raw[:len(raw) - len(stripped)]
        if prefix and stripped.startswith("<"):
            return ("leading-whitespace",
                    "%d byte(s) of whitespace before the document. This is the "
                    "commonest 12100: a newline after a template header or a "
                    "closing tag in an included file." % len(prefix))
        return ("leading-output",
                "the response starts with %r rather than '<'. Something printed "
                "before the document was emitted." % raw[:40])

    low = stripped.lower()
    if low.startswith("<!doctype html") or low.startswith("<html"):
        return ("html-error-page",
                "an HTML page, not TwiML. The handler threw and the framework "
                "returned its error page with a 200 or a 500.")

    if "<response" not in low:
        return ("no-response-root",
                "no <Response> element anywhere. TwiML has exactly one root and "
                "this is not it.")

    amp = UNESCAPED_AMP.search(raw)
    if amp:
        return ("unescaped-entity",
                "a bare '&' at offset %d. Interpolated text was not XML-escaped, "
                "so this breaks for one customer's name and nobody else's."
                % amp.start())

    open_tag = unbalanced(raw)
    if open_tag:
        return ("unclosed-tag",
                "<%s> is opened and never closed." % open_tag)

    return ("parses-here",
            "this copy parses as far as these checks go. response_body is stored "
            "with a size limit, so the break may be past the end of what was "
            "kept: read the line and column out of alert_text.")


def location(alert_text):
    """Line and column from alert_text, best effort. Pure.

    alert_text is a URL-encoded blob whose exact keys differ between products,
    so this scans it rather than parsing a named field, and returns (None, None)
    when the parser did not report a position. Guessing would be worse than
    saying nothing.
    """
    text = unquote_plus(str(alert_text or ""))
    line = LINE_AT.search(text)
    column = COLUMN_AT.search(text)
    return (int(line.group(1)) if line else None,
            int(column.group(1)) if column else None)


def group(alerts, code):
    """Bucket alerts with one error code by endpoint. Pure."""
    out = {}
    for a in alerts:
        if code_of(a) != code:
            continue
        key = endpoint_of(a.get("request_url"))
        row = out.setdefault(key, {"alerts": 0, "sids": [], "first": None,
                                   "last": None})
        row["alerts"] += 1
        if len(row["sids"]) < 3:
            row["sids"].append(a.get("sid"))
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
    return out


REPAIRS = {
    "leading-whitespace": "emit the XML declaration as the first byte: strip "
                          "output before the template and check included files "
                          "for a trailing newline after their closing tag",
    "leading-output": "something writes to the response before the document. "
                      "Find that write; XML allows nothing before the declaration",
    "byte-order-mark": "save the template as UTF-8 without a BOM, or strip the "
                       "mark before writing the response",
    "html-error-page": "the handler is throwing. Fix the exception, and return "
                       "a short TwiML document from the error branch rather than "
                       "a framework page",
    "no-response-root": "wrap the document in a single <Response> element",
    "unescaped-entity": "XML-escape every interpolated value, not the ones that "
                        "looked risky. Use the TwiML helper library rather than "
                        "string concatenation",
    "unclosed-tag": "close the element, or emit it self-closed",
    "parses-here": "read the line and column from alert_text and compare against "
                   "the full document your handler generates",
    "no-body": "reproduce the request against the handler and capture what it "
               "actually writes",
}


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
    """One alert by SID: the only place response_body is populated."""
    return get(session, "%s/Alerts/%s" % (MONITOR, sid))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=1,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many, per log level")
    ap.add_argument("--sample", type=int, default=1,
                    help="alerts to fetch individually per endpoint for the "
                         "response body (each one is a request)")
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
    errors = list_alerts(session, since, args.max_alerts, "error")
    warnings = list_alerts(session, since, args.max_alerts, "warning")

    rows = group(errors, PARSE_FAILURE)
    log.info("%d error alert(s) and %d warning alert(s) since %s, %d endpoint(s) "
             "with 12100", len(errors), len(warnings), since, len(rows))

    bad = 0
    for key, row in sorted(rows.items()):
        bad += 1
        cause, detail = ("no-body", "not sampled")
        line = column = None
        for sid in row["sids"][:max(1, args.sample)]:
            full = fetch_alert(session, sid)
            cause, detail = diagnose(full.get("response_body"))
            line, column = location(full.get("alert_text"))
            if cause != "no-body":
                break
        log.warning("%-18s %s  %d x 12100  %s", cause, key, row["alerts"], detail)
        log.warning("  first %s, last %s", row["first"], row["last"])
        if line is not None:
            log.warning("  parser stopped at line %s, column %s", line, column)
        log.warning("  repair: %s", REPAIRS.get(cause, "read the body by hand"))

    schema = group(warnings, SCHEMA_WARNING)
    for key, row in sorted(schema.items()):
        log.warning("schema-warning     %s  %d x 12200  a verb or attribute is "
                    "misspelled or wrongly cased. Logged at LogLevel=warning, "
                    "so an error-only sweep never sees it and the call runs on "
                    "with the verb skipped.", key, row["alerts"])

    log.info("%d endpoint(s) returning malformed TwiML, %d endpoint(s) with "
             "schema warning(s) at LogLevel=warning", bad, len(schema))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-twiml-parse-audit.mjs",
"js": '''/**
 * Report Twilio webhooks returning TwiML that is not well-formed XML.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';

const PARSE_FAILURE = 12100;
// Logged at LogLevel=warning, never at error. Sweeping one level is how an
// account with hundreds of skipped verbs reports as clean.
const SCHEMA_WARNING = 12200;

// Alerts are retained 30 days. A longer window is the same history mislabelled.
const MAX_DAYS = 30;

// A '&' that does not begin a named, decimal or hex entity.
const UNESCAPED_AMP = /&(?!(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#[xX][0-9A-Fa-f]+);)/;

const TAG = /<\\s*(\\/?)\\s*([A-Za-z][\\w.:-]*)([^>]*?)(\\/?)\\s*>/g;

const LINE_AT = /line\\s*[:= ]\\s*(\\d+)/i;
const COLUMN_AT = /column\\s*[:= ]\\s*(\\d+)/i;

/** Read error_code off an alert as a number, or null. */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** Lowercase host plus path, for grouping. Query string dropped. */
export function endpointOf(url) {
  if (!url) return '';
  const raw = String(url).trim();
  try {
    const u = new URL(raw);
    let path = u.pathname;
    while (path.endsWith('/')) path = path.slice(0, -1);
    return u.hostname.toLowerCase() + path;
  } catch {
    return raw.toLowerCase().replace(/\\/+$/, '');
  }
}

/**
 * The name of the first element left open, or null. Deliberately not an XML
 * parser: a parser tells you where it stopped, and what you need is which
 * element was never closed.
 */
export function unbalanced(xml) {
  const body = String(xml ?? '')
    .replace(/<\\?[\\s\\S]*?\\?>/g, '')
    .replace(/<!--[\\s\\S]*?-->/g, '');
  const stack = [];
  TAG.lastIndex = 0;
  let m = TAG.exec(body);
  while (m !== null) {
    const [, closing, name, , selfclose] = m;
    if (!selfclose) {
      if (closing) {
        if (stack.length && stack[stack.length - 1] === name) stack.pop();
        else return stack.length ? stack[stack.length - 1] : name;
      } else {
        stack.push(name);
      }
    }
    m = TAG.exec(body);
  }
  return stack.length ? stack[stack.length - 1] : null;
}

/**
 * Say why a response body is not well-formed TwiML. Pure, ordered so the
 * earliest byte wins. Returns [cause, detail].
 */
export function diagnose(body) {
  const raw = body === null || body === undefined ? '' : String(body);
  if (!raw.trim()) {
    return ['no-body',
      'the single-alert fetch returned an empty body. Either the handler sent ' +
      'nothing, or this alert predates what the API still stores.'];
  }

  if (raw.startsWith('\\uFEFF')) {
    return ['byte-order-mark',
      'the document begins with a UTF-8 byte order mark. XML allows nothing ' +
      'before the declaration, and an editor added three bytes no diff will ' +
      'show you.'];
  }

  const stripped = raw.replace(/^\\s+/, '');
  if (!raw.startsWith('<')) {
    const prefix = raw.slice(0, raw.length - stripped.length);
    if (prefix && stripped.startsWith('<')) {
      return ['leading-whitespace',
        `${prefix.length} byte(s) of whitespace before the document. This is ` +
        'the commonest 12100: a newline after a template header or a closing ' +
        'tag in an included file.'];
    }
    return ['leading-output',
      `the response starts with ${JSON.stringify(raw.slice(0, 40))} rather ` +
      "than '<'. Something printed before the document was emitted."];
  }

  const low = stripped.toLowerCase();
  if (low.startsWith('<!doctype html') || low.startsWith('<html')) {
    return ['html-error-page',
      'an HTML page, not TwiML. The handler threw and the framework returned ' +
      'its error page with a 200 or a 500.'];
  }

  if (!low.includes('<response')) {
    return ['no-response-root',
      'no <Response> element anywhere. TwiML has exactly one root and this is ' +
      'not it.'];
  }

  const amp = UNESCAPED_AMP.exec(raw);
  if (amp) {
    return ['unescaped-entity',
      `a bare '&' at offset ${amp.index}. Interpolated text was not ` +
      "XML-escaped, so this breaks for one customer's name and nobody else's."];
  }

  const openTag = unbalanced(raw);
  if (openTag) return ['unclosed-tag', `<${openTag}> is opened and never closed.`];

  return ['parses-here',
    'this copy parses as far as these checks go. response_body is stored with ' +
    'a size limit, so the break may be past the end of what was kept: read the ' +
    'line and column out of alert_text.'];
}

/**
 * Line and column from alert_text, best effort. alert_text is a URL-encoded
 * blob whose keys differ between products, so this scans rather than parses and
 * returns nulls when there is no position to report.
 */
export function location(alertText) {
  const text = decodeURIComponent(String(alertText ?? '').replace(/\\+/g, ' '));
  const line = LINE_AT.exec(text);
  const column = COLUMN_AT.exec(text);
  return [line ? Number(line[1]) : null, column ? Number(column[1]) : null];
}

/** Bucket alerts with one error code by endpoint. Pure. */
export function group(alerts, code) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== code) continue;
    const key = endpointOf(a.request_url);
    if (!out.has(key)) out.set(key, { alerts: 0, sids: [], first: null, last: null });
    const row = out.get(key);
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

const REPAIRS = {
  'leading-whitespace': 'emit the XML declaration as the first byte: strip ' +
    'output before the template and check included files for a trailing ' +
    'newline after their closing tag',
  'leading-output': 'something writes to the response before the document. ' +
    'Find that write; XML allows nothing before the declaration',
  'byte-order-mark': 'save the template as UTF-8 without a BOM, or strip the ' +
    'mark before writing the response',
  'html-error-page': 'the handler is throwing. Fix the exception, and return a ' +
    'short TwiML document from the error branch rather than a framework page',
  'no-response-root': 'wrap the document in a single <Response> element',
  'unescaped-entity': 'XML-escape every interpolated value, not the ones that ' +
    'looked risky. Use the TwiML helper library rather than string concatenation',
  'unclosed-tag': 'close the element, or emit it self-closed',
  'parses-here': 'read the line and column from alert_text and compare against ' +
    'the full document your handler generates',
  'no-body': 'reproduce the request against the handler and capture what it ' +
    'actually writes',
};

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
    ? process.argv[process.argv.indexOf('--days') + 1] : 1) || 1;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const errors = await listAlerts(auth, since, 10000, 'error');
  const warnings = await listAlerts(auth, since, 10000, 'warning');

  const rows = group(errors, PARSE_FAILURE);
  console.log(`${errors.length} error alert(s) and ${warnings.length} warning ` +
              `alert(s) since ${since}, ${rows.size} endpoint(s) with 12100`);

  let bad = 0;
  for (const [key, row] of [...rows.entries()].sort()) {
    bad += 1;
    let cause = 'no-body';
    let detail = 'not sampled';
    let line = null;
    let column = null;
    for (const sid of row.sids.slice(0, 1)) {
      const full = await fetchAlert(auth, sid);
      [cause, detail] = diagnose(full.response_body);
      [line, column] = location(full.alert_text);
    }
    console.warn(`${cause.padEnd(18)} ${key}  ${row.alerts} x 12100  ${detail}`);
    console.warn(`  first ${row.first}, last ${row.last}`);
    if (line !== null) console.warn(`  parser stopped at line ${line}, column ${column}`);
    console.warn(`  repair: ${REPAIRS[cause] ?? 'read the body by hand'}`);
  }

  const schema = group(warnings, SCHEMA_WARNING);
  for (const [key, row] of [...schema.entries()].sort()) {
    console.warn(`schema-warning     ${key}  ${row.alerts} x 12200  a verb or ` +
                 'attribute is misspelled or wrongly cased. Logged at ' +
                 'LogLevel=warning, so an error-only sweep never sees it and ' +
                 'the call runs on with the verb skipped.');
  }

  console.log(`${bad} endpoint(s) returning malformed TwiML, ${schema.size} ` +
              'endpoint(s) with schema warning(s) at LogLevel=warning');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every branch of <code>diagnose()</code> gets a body, because the ordering is the substance: a document with both a leading newline <em>and</em> an unclosed tag has to be reported as the leading newline, since that is where the parser actually stopped. The entity regex is pinned in both directions &mdash; <code>&amp;amp;</code> and <code>&amp;#38;</code> are fine, a bare <code>&amp;</code> is not &mdash; and <code>location()</code> is pinned to return nothing rather than a guess when <code>alert_text</code> carries no position.",
"test_py_file": "test_twilio_twiml_parse_audit.py",
"test_py": '''from twilio_twiml_parse_audit import (code_of, diagnose, endpoint_of, group,
                                        location, unbalanced)

GOOD = '<?xml version="1.0" encoding="UTF-8"?>\\n<Response><Say>Hi</Say></Response>'


def alert(sid, url, code="12100", when="2026-04-02T10:00:00Z"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when}


def test_a_well_formed_document_is_not_flagged():
    cause, _ = diagnose(GOOD)
    assert cause == "parses-here"


def test_one_newline_before_the_declaration_is_the_commonest_cause():
    cause, detail = diagnose("\\n" + GOOD)
    assert cause == "leading-whitespace"
    assert "1 byte" in detail


def test_a_byte_order_mark_beats_every_other_check():
    # It is the first byte, so it is where the parser stops, even though the
    # rest of the document is also broken.
    cause, _ = diagnose("\\ufeff<Response><Say>Hi</Response>")
    assert cause == "byte-order-mark"


def test_output_before_the_document_is_not_whitespace():
    cause, detail = diagnose("Warning: undefined index\\n" + GOOD)
    assert cause == "leading-output"
    assert "Warning" in detail


def test_a_framework_error_page_is_named_as_one():
    cause, _ = diagnose("<!DOCTYPE html><html><body>500</body></html>")
    assert cause == "html-error-page"


def test_a_document_with_no_response_root_is_its_own_cause():
    cause, _ = diagnose("<Say>Hi</Say>")
    assert cause == "no-response-root"


def test_a_bare_ampersand_is_caught_and_real_entities_are_not():
    cause, detail = diagnose("<Response><Say>Ben & Jerry</Say></Response>")
    assert cause == "unescaped-entity"
    assert "offset" in detail
    assert diagnose("<Response><Say>Ben &amp; Jerry</Say></Response>")[0] == \\
        "parses-here"
    assert diagnose("<Response><Say>Ben &#38; Jerry</Say></Response>")[0] == \\
        "parses-here"


def test_an_unclosed_verb_is_named():
    cause, detail = diagnose("<Response><Say>Hi</Response>")
    assert cause == "unclosed-tag"
    assert "<Say>" in detail


def test_self_closing_and_declared_tags_do_not_count_as_open():
    assert unbalanced('<?xml version="1.0"?><Response><Hangup/></Response>') is None
    assert unbalanced("<Response><!-- <Say> --></Response>") is None


def test_an_empty_body_is_reported_rather_than_guessed():
    assert diagnose("")[0] == "no-body"
    assert diagnose(None)[0] == "no-body"


def test_location_reads_a_position_and_admits_when_there_is_none():
    assert location("Msg=Error+on+line+1%2C+column+3") == (1, 3)
    assert location("ErrorCode=12100") == (None, None)
    assert location(None) == (None, None)


def test_group_keeps_only_the_requested_code():
    rows = group([alert("NO1", "https://a.example.com/voice?CallSid=CA1"),
                  alert("NO2", "https://a.example.com/voice"),
                  alert("NO3", "https://a.example.com/voice", code="12200")],
                 12100)
    assert rows["a.example.com/voice"]["alerts"] == 2
    assert code_of({"error_code": "12100"}) == 12100
    assert endpoint_of("https://A.example.com/voice/") == "a.example.com/voice"
''',
"test_js_file": "twilio-twiml-parse-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  codeOf, diagnose, endpointOf, group, location, unbalanced,
} from './twilio-twiml-parse-audit.mjs';

const GOOD = '<?xml version="1.0" encoding="UTF-8"?>\\n<Response><Say>Hi</Say></Response>';

const alert = (sid, url, code = '12100', when = '2026-04-02T10:00:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when,
});

test('a well-formed document is not flagged', () => {
  assert.equal(diagnose(GOOD)[0], 'parses-here');
});

test('one newline before the declaration is the commonest cause', () => {
  const [cause, detail] = diagnose(`\\n${GOOD}`);
  assert.equal(cause, 'leading-whitespace');
  assert.match(detail, /1 byte/);
});

test('a byte order mark beats every other check', () => {
  assert.equal(diagnose('\\uFEFF<Response><Say>Hi</Response>')[0], 'byte-order-mark');
});

test('output before the document is not whitespace', () => {
  const [cause, detail] = diagnose(`Warning: undefined index\\n${GOOD}`);
  assert.equal(cause, 'leading-output');
  assert.match(detail, /Warning/);
});

test('a framework error page is named as one', () => {
  assert.equal(diagnose('<!DOCTYPE html><html><body>500</body></html>')[0],
    'html-error-page');
});

test('a document with no Response root is its own cause', () => {
  assert.equal(diagnose('<Say>Hi</Say>')[0], 'no-response-root');
});

test('a bare ampersand is caught and real entities are not', () => {
  const [cause, detail] = diagnose('<Response><Say>Ben & Jerry</Say></Response>');
  assert.equal(cause, 'unescaped-entity');
  assert.match(detail, /offset/);
  assert.equal(diagnose('<Response><Say>Ben &amp; Jerry</Say></Response>')[0],
    'parses-here');
  assert.equal(diagnose('<Response><Say>Ben &#38; Jerry</Say></Response>')[0],
    'parses-here');
});

test('an unclosed verb is named', () => {
  const [cause, detail] = diagnose('<Response><Say>Hi</Response>');
  assert.equal(cause, 'unclosed-tag');
  assert.match(detail, /<Say>/);
});

test('self-closing and declared tags do not count as open', () => {
  assert.equal(unbalanced('<?xml version="1.0"?><Response><Hangup/></Response>'), null);
  assert.equal(unbalanced('<Response><!-- <Say> --></Response>'), null);
});

test('an empty body is reported rather than guessed', () => {
  assert.equal(diagnose('')[0], 'no-body');
  assert.equal(diagnose(null)[0], 'no-body');
});

test('location reads a position and admits when there is none', () => {
  assert.deepEqual(location('Msg=Error+on+line+1%2C+column+3'), [1, 3]);
  assert.deepEqual(location('ErrorCode=12100'), [null, null]);
  assert.deepEqual(location(null), [null, null]);
});

test('group keeps only the requested code', () => {
  const rows = group([
    alert('NO1', 'https://a.example.com/voice?CallSid=CA1'),
    alert('NO2', 'https://a.example.com/voice'),
    alert('NO3', 'https://a.example.com/voice', '12200'),
  ], 12100);
  assert.equal(rows.get('a.example.com/voice').alerts, 2);
  assert.equal(codeOf({ error_code: '12100' }), 12100);
  assert.equal(endpointOf('https://A.example.com/voice/'), 'a.example.com/voice');
});
''',
"faq": [
 ("How can one blank line break the whole document?",
  "Because XML allows nothing before the declaration. Not a space, not a newline, not a byte order mark. The parser fails at the first byte and never looks at the rest, which is why the source can be perfect and the response still invalid."),
 ("My handler returns 200 and logs nothing. Where is the failure?",
  "Inside Twilio's parser, after your response left the process. From the handler's point of view it succeeded. The only record is the alert, and the only place the bytes it sent are visible is the single-alert fetch, GET /v1/Alerts/{Sid}."),
 ("Why does the script sweep LogLevel=warning as well?",
  "Because 12200, the schema validation failure for a misspelled or wrongly cased verb, is logged at warning level and never appears in an error-only query. It is the same family of problem: the document parses, the verb is skipped, the call runs on doing nothing. An error-only sweep reports that account as clean."),
 ("Why not just run the body through a real XML parser?",
  "The script does the equivalent, but a parser answers a different question. It refuses the document and reports a position; what you need in order to fix it is which element was never closed, or that the first three bytes are a byte order mark. That is why the diagnosis is a small ordered set of named causes with named repairs."),
 ("The body came back looking valid. Now what?",
  "Then read the line and column from alert_text and compare against the full document your handler generates. response_body is stored with a size limit, so on a large document the break can be past the end of the copy the API kept, and the script says so rather than declaring the endpoint healthy."),
],
"related": [
 ("/twilio/twiml-response-body-too-large-11750/", "A TwiML response over the 64 kB limit"),
 ("/twilio/webhook-invalid-content-type-12300/", "The wrong Content-Type on a TwiML response"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
],
"citations": [CITE_12100, CITE_12200, CITE_ALERTS, CITE_TWIML_VOICE],
},


{
"slug": "twiml-response-body-too-large-11750",
"title": "A TwiML response over 64 kB drops the call with 11750",
"description": "11750 is usually not a big TwiML document. It is an HTML stack trace returned where TwiML was expected, and the giveaway is in the body.",
"h1": "a TwiML response over 64 kB drops the call with 11750",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11750", "twiml response body too large",
             "twilio 64kb twiml limit", "twilio call drops after webhook",
             "twilio html error page instead of twiml"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>11750 TwiML response body too large</code> reads like a capacity problem, so people go looking for the enormous document they must have generated. Usually there isn't one. The handler threw, the framework returned its debug page, and a stack trace with syntax highlighting and every local variable inlined sails past 64 kB without difficulty.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> for <code>error_code == 11750</code>, group by endpoint, then fetch a sample with <code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> and look at <code>response_body</code>. The question that decides the repair is whether the body is TwiML at all.</p>
<p>An HTML page or a stack trace means the application is failing and the size is a symptom &mdash; turn off debug pages in production so a failure returns a short 500. Genuine TwiML over the limit means the document needs splitting across <code>&lt;Redirect&gt;</code> hops. Note that <code>response_body</code> is itself stored with a size limit, so its length is a floor, not a measurement.</p>""",
"problem": """<p>The error code sends you the wrong way. It names a size, so the search starts with the biggest document the app can produce &mdash; the conference with three hundred participants, the <code>&lt;Say&gt;</code> loop over a long list &mdash; and often that document turns out to be 6 kB and entirely innocent. Meanwhile the real cause is an exception, and it is only visible if you look at what came back rather than at how much of it there was.</p>
<p>The reason a debug page gets so big is that it is designed to. Source context around every frame, all the locals, the request environment, the loaded modules, and CSS to render it: that is comfortably tens of kilobytes on a framework's default settings. So a handler that throws in production with debug output still on does not return a small error, it returns an essay, and Twilio refuses the essay for its size rather than its content.</p>
<p>Either way the caller is gone. 11750 fires after the webhook, and the call drops immediately.</p>""",
"why": """<p><strong>64 kB is the cap, in bytes.</strong> Not characters. A document full of non-ASCII text in <code>&lt;Say&gt;</code> is meaningfully larger on the wire than its length suggests, and any check that measures with a character count will read a failing document as comfortably under the limit.</p>
<p><strong>A debug page is enormous by design.</strong> Framework error pages inline source context, local variables and styling. Leaving that enabled in production converts every unhandled exception into a response that is both wrong and oversized, which is why the honest repair is two changes: fix the exception, and stop returning debug pages.</p>
<p><strong>The stored body is truncated, so its length proves nothing.</strong> <code>response_body</code> on an alert is kept with a size limit. Measuring it and finding 20 kB does not mean the response was 20 kB. That is why the classification keys on <em>what</em> the body is &mdash; HTML, a traceback, real TwiML &mdash; and treats the byte count as a floor.</p>
<p><strong>Status callbacks do not need a document at all.</strong> A handler that returns a full page to a status callback is doing needless work at every event. An empty <code>&lt;Response/&gt;</code> is the correct answer there, and it is one of the easiest ways to remove a whole class of size failures.</p>""",
"steps": [
 {"h": "Sweep for 11750 and group by endpoint",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>, keeping <code>error_code == 11750</code>. Read it as an integer; the Monitor API returns error codes as strings. One failing route is one line in the report regardless of how many calls hit it.</p>"""},
 {"h": "Fetch a sample and read what came back",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> is the only place <code>response_body</code> exists. One alert per endpoint answers the question that matters: is this a document, or is it an accident? A <code>&lt;!DOCTYPE html&gt;</code> or a traceback is an accident.</p>"""},
 {"h": "Measure in bytes and treat the number as a floor",
  "body": """<p>The limit is 64 kB of bytes, so encode before you count &mdash; a character count under-reports any document with accented or non-Latin text in it. And because the stored body is truncated, a measurement below the limit is not evidence the response was: it only ever proves the response was at least that big.</p>"""},
 {"h": "Split the verdict by cause, because the repairs differ",
  "body": """<p>An HTML page or a stack trace is an application failure: fix the exception and disable debug output in production. Real TwiML over the cap is a design problem: split it across <code>&lt;Redirect&gt;</code> hops so each response is small. A status callback returning anything substantial should return an empty <code>&lt;Response/&gt;</code> instead.</p>"""},
 {"h": "Re-run over a window that starts after the deploy",
  "body": """<p>Alerts are retained 30 days, so a window inherited from the previous run will keep showing failures that are already fixed. Start the window after the deploy. A count that drops without reaching zero means one branch of the handler still returns the old page.</p>"""},
],
"verify": """<p>Re-run over a window beginning after the deploy. Zero, not fewer &mdash; a smaller number usually means one code path was missed.</p>
<pre><code class="language-bash">python3 twilio_twiml_size_audit.py --days 1
# 0 endpoint(s) exceeding the 64 kB TwiML limit</code></pre>""",
"code_intro": "Two pure functions and one honest limitation. <code>byte_length()</code> encodes before counting, because the cap is bytes. <code>classify_body()</code> decides what the response was rather than how long it was, and reports the length as a floor, because the copy the Alerts API stores is truncated. Everything else is the usual sweep plus a capped number of single-alert fetches, since that fetch is the only place the body lives.",
"py_file": "twilio_twiml_size_audit.py",
"py": '''"""Report Twilio webhooks whose response exceeds the 64 kB TwiML limit (11750).

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
log = logging.getLogger("twilio_twiml_size_audit")

MONITOR = "https://monitor.twilio.com/v1"

BODY_TOO_LARGE = 11750

# The cap Twilio applies to a TwiML response, in bytes.
LIMIT = 64 * 1024

# Alerts are retained 30 days. A longer window is not more history, it is the
# same history under a label that makes the report look more thorough.
MAX_DAYS = 30

# Markers of a framework error page: the far commoner cause of 11750 than a
# genuinely large document.
TRACE_MARKERS = (
    "traceback (most recent call last)",
    "stack trace",
    "stacktrace",
    "whoops! there was an error",
    "werkzeug debugger",
    "actiondispatch",
)


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API hands this back as a string while the Messages list hands
    back a number for the same concept, and a check written for one and pointed
    at the other matches nothing and reports a healthy account.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def endpoint_of(url):
    """Lowercase host plus path, for grouping. Query string dropped."""
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        return str(url).strip().lower().rstrip("/")
    return host + (parts.path or "").rstrip("/")


def byte_length(text):
    """Size in bytes, which is the unit the limit is expressed in.

    len() on a string counts characters. A document with accented or non-Latin
    text in <Say> is larger on the wire than its length, so a character count
    reads a failing response as comfortably inside the cap.
    """
    return len(str(text or "").encode("utf-8"))


def classify_body(body):
    """Say what the oversized response actually was. Pure.

    The verdict keys on what the body is rather than on how long it is, because
    response_body is stored with a size limit of its own: measuring it gives a
    floor, never the size of the response Twilio refused.

    Returns (state, detail).
    """
    raw = "" if body is None else str(body)
    size = byte_length(raw)

    if not raw.strip():
        return ("no-body",
                "the single-alert fetch returned nothing, so the cause cannot "
                "be read from here. Reproduce the request against the handler "
                "and measure what it writes.")

    low = raw.lstrip().lower()
    if (low.startswith("<!doctype html") or low.startswith("<html")
            or "<html" in low[:2000]):
        return ("error-page",
                "an HTML page, not TwiML: at least %d bytes of framework debug "
                "output. The size is a symptom; the handler threw." % size)

    if any(m in low for m in TRACE_MARKERS):
        return ("stack-trace",
                "a stack trace, at least %d bytes of it. Debug output is still "
                "on in production and every unhandled exception returns an "
                "essay." % size)

    if "<response" in low:
        if size >= LIMIT:
            return ("oversized-twiml",
                    "real TwiML, %d bytes, over the %d byte cap. This one needs "
                    "splitting rather than fixing." % (size, LIMIT))
        return ("twiml-truncated",
                "real TwiML. The stored copy is %d bytes, under the cap, but "
                "response_body is truncated: that is a floor, not the size of "
                "the response." % size)

    return ("not-twiml",
            "at least %d bytes of something that is neither TwiML nor a "
            "recognisable error page. Read the first line of it." % size)


def group(alerts, code=BODY_TOO_LARGE):
    """Bucket alerts with one error code by endpoint. Pure."""
    out = {}
    for a in alerts:
        if code_of(a) != code:
            continue
        key = endpoint_of(a.get("request_url"))
        row = out.setdefault(key, {"alerts": 0, "sids": [], "first": None,
                                   "last": None})
        row["alerts"] += 1
        if len(row["sids"]) < 3:
            row["sids"].append(a.get("sid"))
        when = a.get("date_generated") or ""
        if when:
            row["first"] = when if row["first"] is None else min(row["first"], when)
            row["last"] = when if row["last"] is None else max(row["last"], when)
    return out


REPAIRS = {
    "error-page": "fix the exception, and turn debug pages off in production so "
                  "a failure returns a short 500 rather than a rendered page",
    "stack-trace": "disable debug output in production and return a small TwiML "
                   "document from the error branch",
    "oversized-twiml": "split the flow across <Redirect> hops so each response "
                       "is small, and return an empty <Response/> to status "
                       "callbacks",
    "twiml-truncated": "the stored copy is truncated: generate the same document "
                       "locally and measure it in bytes",
    "not-twiml": "read the first line of the body and find what writes it",
    "no-body": "reproduce the request against the handler and measure what it "
               "writes",
}


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
    """One alert by SID: the only place response_body is populated."""
    return get(session, "%s/Alerts/%s" % (MONITOR, sid))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=1,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    ap.add_argument("--sample", type=int, default=1,
                    help="alerts to fetch individually per endpoint for the "
                         "response body (each one is a request)")
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
    rows = group(alerts)
    log.info("%d alert(s) since %s, %d endpoint(s) with 11750", len(alerts),
             since, len(rows))

    bad = 0
    for key, row in sorted(rows.items()):
        bad += 1
        state, detail = ("no-body", "not sampled")
        for sid in row["sids"][:max(1, args.sample)]:
            state, detail = classify_body(fetch_alert(session, sid)
                                          .get("response_body"))
            if state != "no-body":
                break
        log.warning("%-16s %s  %d x 11750  %s", state, key, row["alerts"], detail)
        log.warning("  first %s, last %s", row["first"], row["last"])
        log.warning("  repair: %s", REPAIRS.get(state, "read the body by hand"))

    log.info("%d endpoint(s) exceeding the %d byte TwiML limit", bad, LIMIT)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-twiml-size-audit.mjs",
"js": '''/**
 * Report Twilio webhooks whose response exceeds the 64 kB TwiML limit (11750).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';

const BODY_TOO_LARGE = 11750;

// The cap Twilio applies to a TwiML response, in bytes.
const LIMIT = 64 * 1024;

// Alerts are retained 30 days. A longer window is the same history mislabelled.
const MAX_DAYS = 30;

// Markers of a framework error page: the far commoner cause of 11750.
const TRACE_MARKERS = [
  'traceback (most recent call last)', 'stack trace', 'stacktrace',
  'whoops! there was an error', 'werkzeug debugger', 'actiondispatch',
];

/** Read error_code off an alert as a number, or null. */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** Lowercase host plus path, for grouping. Query string dropped. */
export function endpointOf(url) {
  if (!url) return '';
  const raw = String(url).trim();
  try {
    const u = new URL(raw);
    let path = u.pathname;
    while (path.endsWith('/')) path = path.slice(0, -1);
    return u.hostname.toLowerCase() + path;
  } catch {
    return raw.toLowerCase().replace(/\\/+$/, '');
  }
}

/**
 * Size in bytes, which is the unit the limit is expressed in. A character count
 * reads a document with non-Latin text in <Say> as smaller than it is.
 */
export function byteLength(text) {
  return Buffer.byteLength(String(text ?? ''), 'utf8');
}

/**
 * Say what the oversized response actually was. Pure. Keys on what the body is
 * rather than how long it is, because response_body is stored truncated and its
 * length is a floor. Returns [state, detail].
 */
export function classifyBody(body) {
  const raw = body === null || body === undefined ? '' : String(body);
  const size = byteLength(raw);

  if (!raw.trim()) {
    return ['no-body',
      'the single-alert fetch returned nothing, so the cause cannot be read ' +
      'from here. Reproduce the request against the handler and measure what ' +
      'it writes.'];
  }

  const low = raw.replace(/^\\s+/, '').toLowerCase();
  if (low.startsWith('<!doctype html') || low.startsWith('<html')
      || low.slice(0, 2000).includes('<html')) {
    return ['error-page',
      `an HTML page, not TwiML: at least ${size} bytes of framework debug ` +
      'output. The size is a symptom; the handler threw.'];
  }

  if (TRACE_MARKERS.some((m) => low.includes(m))) {
    return ['stack-trace',
      `a stack trace, at least ${size} bytes of it. Debug output is still on ` +
      'in production and every unhandled exception returns an essay.'];
  }

  if (low.includes('<response')) {
    if (size >= LIMIT) {
      return ['oversized-twiml',
        `real TwiML, ${size} bytes, over the ${LIMIT} byte cap. This one needs ` +
        'splitting rather than fixing.'];
    }
    return ['twiml-truncated',
      `real TwiML. The stored copy is ${size} bytes, under the cap, but ` +
      'response_body is truncated: that is a floor, not the size of the response.'];
  }

  return ['not-twiml',
    `at least ${size} bytes of something that is neither TwiML nor a ` +
    'recognisable error page. Read the first line of it.'];
}

/** Bucket alerts with one error code by endpoint. Pure. */
export function group(alerts, code = BODY_TOO_LARGE) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== code) continue;
    const key = endpointOf(a.request_url);
    if (!out.has(key)) out.set(key, { alerts: 0, sids: [], first: null, last: null });
    const row = out.get(key);
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

const REPAIRS = {
  'error-page': 'fix the exception, and turn debug pages off in production so a ' +
    'failure returns a short 500 rather than a rendered page',
  'stack-trace': 'disable debug output in production and return a small TwiML ' +
    'document from the error branch',
  'oversized-twiml': 'split the flow across <Redirect> hops so each response is ' +
    'small, and return an empty <Response/> to status callbacks',
  'twiml-truncated': 'the stored copy is truncated: generate the same document ' +
    'locally and measure it in bytes',
  'not-twiml': 'read the first line of the body and find what writes it',
  'no-body': 'reproduce the request against the handler and measure what it writes',
};

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
    ? process.argv[process.argv.indexOf('--days') + 1] : 1) || 1;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS} instead`);
    days = MAX_DAYS;
  }
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await listAlerts(auth, since);
  const rows = group(alerts);
  console.log(`${alerts.length} alert(s) since ${since}, ${rows.size} endpoint(s) with 11750`);

  let bad = 0;
  for (const [key, row] of [...rows.entries()].sort()) {
    bad += 1;
    let state = 'no-body';
    let detail = 'not sampled';
    for (const sid of row.sids.slice(0, 1)) {
      const full = await fetchAlert(auth, sid);
      [state, detail] = classifyBody(full.response_body);
    }
    console.warn(`${state.padEnd(16)} ${key}  ${row.alerts} x 11750  ${detail}`);
    console.warn(`  first ${row.first}, last ${row.last}`);
    console.warn(`  repair: ${REPAIRS[state] ?? 'read the body by hand'}`);
  }

  console.log(`${bad} endpoint(s) exceeding the ${LIMIT} byte TwiML limit`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests hold the two claims this note makes. The limit is in bytes, so <code>byte_length()</code> is pinned against strings whose character count is smaller than their size &mdash; the exact case a naive check gets wrong. And a body under the cap must never be reported as fine, because the stored copy is truncated; the test asserts the verdict says <em>floor</em> rather than declaring the endpoint healthy.",
"test_py_file": "test_twilio_twiml_size_audit.py",
"test_py": '''from twilio_twiml_size_audit import (byte_length, classify_body, code_of,
                                       endpoint_of, group, LIMIT)


def alert(sid, url, code="11750", when="2026-04-02T10:00:00Z"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": when}


def test_the_limit_is_measured_in_bytes_not_characters():
    # The mistake this exists to prevent: len() on a str reads a failing
    # document as comfortably inside the cap.
    assert byte_length("caf\\u00e9") == 5
    assert len("caf\\u00e9") == 4
    assert byte_length("\\U0001f600") == 4
    assert byte_length(None) == 0


def test_a_framework_debug_page_is_the_usual_cause():
    state, detail = classify_body("<!DOCTYPE html><html><body>Server Error</body></html>")
    assert state == "error-page"
    assert "symptom" in detail


def test_a_stack_trace_is_named_separately_from_a_rendered_page():
    state, _ = classify_body("Traceback (most recent call last):\\n  File ...")
    assert state == "stack-trace"


def test_genuine_twiml_over_the_cap_is_a_splitting_problem():
    body = "<Response>" + ("<Say>hello</Say>" * 6000) + "</Response>"
    assert byte_length(body) > LIMIT
    state, detail = classify_body(body)
    assert state == "oversized-twiml"
    assert "splitting" in detail


def test_twiml_under_the_cap_is_reported_as_a_floor_not_a_clean_bill():
    # response_body is stored truncated, so a small stored copy proves nothing
    # about the response Twilio actually refused.
    state, detail = classify_body("<Response><Say>Hi</Say></Response>")
    assert state == "twiml-truncated"
    assert "floor" in detail


def test_an_empty_body_is_reported_rather_than_guessed():
    assert classify_body("")[0] == "no-body"
    assert classify_body(None)[0] == "no-body"


def test_something_that_is_neither_twiml_nor_an_error_page():
    state, detail = classify_body('{"error": "too many participants"}')
    assert state == "not-twiml"
    assert "bytes" in detail


def test_group_keeps_only_11750_and_records_the_ends():
    rows = group([alert("NO1", "https://a.example.com/voice?CallSid=CA1",
                        when="2026-04-02T10:00:00Z"),
                  alert("NO2", "https://a.example.com/voice/",
                        when="2026-04-01T09:00:00Z"),
                  alert("NO3", "https://a.example.com/voice", code="12100")])
    assert set(rows) == {"a.example.com/voice"}
    assert rows["a.example.com/voice"]["alerts"] == 2
    assert rows["a.example.com/voice"]["last"] == "2026-04-02T10:00:00Z"


def test_code_and_endpoint_helpers():
    assert code_of({"error_code": "11750"}) == 11750
    assert code_of({}) is None
    assert endpoint_of("https://A.example.com/voice?x=1") == "a.example.com/voice"
''',
"test_js_file": "twilio-twiml-size-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  byteLength, classifyBody, codeOf, endpointOf, group,
} from './twilio-twiml-size-audit.mjs';

const LIMIT = 64 * 1024;

const alert = (sid, url, code = '11750', when = '2026-04-02T10:00:00Z') => ({
  sid, request_url: url, error_code: code, date_generated: when,
});

test('the limit is measured in bytes, not characters', () => {
  assert.equal(byteLength('caf\\u00e9'), 5);
  assert.equal('caf\\u00e9'.length, 4);
  assert.equal(byteLength('\\u{1f600}'), 4);
  assert.equal(byteLength(null), 0);
});

test('a framework debug page is the usual cause', () => {
  const [state, detail] = classifyBody('<!DOCTYPE html><html><body>Server Error</body></html>');
  assert.equal(state, 'error-page');
  assert.match(detail, /symptom/);
});

test('a stack trace is named separately from a rendered page', () => {
  assert.equal(classifyBody('Traceback (most recent call last):\\n  File ...')[0],
    'stack-trace');
});

test('genuine TwiML over the cap is a splitting problem', () => {
  const body = `<Response>${'<Say>hello</Say>'.repeat(6000)}</Response>`;
  assert.ok(byteLength(body) > LIMIT);
  const [state, detail] = classifyBody(body);
  assert.equal(state, 'oversized-twiml');
  assert.match(detail, /splitting/);
});

test('TwiML under the cap is reported as a floor, not a clean bill', () => {
  const [state, detail] = classifyBody('<Response><Say>Hi</Say></Response>');
  assert.equal(state, 'twiml-truncated');
  assert.match(detail, /floor/);
});

test('an empty body is reported rather than guessed', () => {
  assert.equal(classifyBody('')[0], 'no-body');
  assert.equal(classifyBody(null)[0], 'no-body');
});

test('something that is neither TwiML nor an error page', () => {
  const [state, detail] = classifyBody('{"error": "too many participants"}');
  assert.equal(state, 'not-twiml');
  assert.match(detail, /bytes/);
});

test('group keeps only 11750 and records the ends', () => {
  const rows = group([
    alert('NO1', 'https://a.example.com/voice?CallSid=CA1', '11750', '2026-04-02T10:00:00Z'),
    alert('NO2', 'https://a.example.com/voice/', '11750', '2026-04-01T09:00:00Z'),
    alert('NO3', 'https://a.example.com/voice', '12100'),
  ]);
  assert.deepEqual([...rows.keys()], ['a.example.com/voice']);
  assert.equal(rows.get('a.example.com/voice').alerts, 2);
  assert.equal(rows.get('a.example.com/voice').last, '2026-04-02T10:00:00Z');
});

test('code and endpoint helpers', () => {
  assert.equal(codeOf({ error_code: '11750' }), 11750);
  assert.equal(codeOf({}), null);
  assert.equal(endpointOf('https://A.example.com/voice?x=1'), 'a.example.com/voice');
});
''',
"faq": [
 ("My TwiML is tiny. Why am I getting 11750?",
  "Because the response Twilio received was not your TwiML. The handler threw and the framework returned its debug page, which inlines source context, local variables and styling and passes 64 kB easily. Fetch the alert by SID and read response_body: if it opens with <!DOCTYPE html>, that is the whole answer."),
 ("Is the 64 kB limit in bytes or characters?",
  "Bytes. A document with accented or non-Latin text in <Say> is larger on the wire than its character count suggests, so any check that measures with a string length will pass a response that Twilio refuses. The script encodes before counting."),
 ("The stored response body is only 20 kB. Doesn't that disprove the error?",
  "No. response_body on an alert is kept with a size limit of its own, so its length is a floor rather than a measurement. That is why the verdict is based on what the body is, and why a body under the cap is reported as truncated rather than as healthy."),
 ("What should a status callback return?",
  "An empty <Response/>. Status callbacks are notifications, not instructions, so there is nothing useful to say back. Handlers that return a full page to every callback do needless work at every event and put themselves one exception away from this error."),
 ("How do I get a genuinely large TwiML document under the limit?",
  "Split it across <Redirect> hops. Emit as much of the flow as fits comfortably, end with a <Redirect> to the next segment, and let Twilio fetch it. Each response stays small and the call continues without the caller noticing a boundary."),
],
"related": [
 ("/twilio/twiml-document-parse-failure-12100/", "TwiML that is not well-formed XML"),
 ("/twilio/webhook-invalid-content-type-12300/", "The wrong Content-Type on a TwiML response"),
 ("/twilio/status-callback-webhook-failing-11200/", "11200 on a status callback leaves delivery state blind"),
],
"citations": [CITE_11750, CITE_ALERTS, CITE_TWIML_VOICE, CITE_TWIML_REDIRECT],
},

]
