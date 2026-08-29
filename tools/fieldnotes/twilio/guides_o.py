#!/usr/bin/env python3
"""/twilio/ field notes, batch O — the writing.

Four webhook failures that sit either side of the TLS handshake. Two of them
happen during it: 11220, where no protocol version or cipher suite is shared,
and 11237, where the chain the server presents leads nowhere Twilio trusts.
One happens after it: 11206, where bytes come back and Twilio's HTTP client
cannot parse them. The fourth happens before anything is attempted at all — a
URL sitting in the number's configuration that is cleartext, unroutable, or a
dev tunnel with a battery life.

Three constraints shape the scripts. `response_body` and `response_headers` are
populated only by the single-alert fetch `GET /v1/Alerts/{Sid}` and appear on no
row of the list, so the 11206 script pays one request per alert it wants to look
inside and says so before it starts. Alerts are retained 30 days, so nothing
here claims to know what happened before that. And several Twilio failures are
logged at `LogLevel=warning` rather than `error`, so a sweep that reads only the
error level can miss the evidence that changes a verdict.

Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run.
"""

CITE_11220 = ("Error 11220: SSL/TLS handshake error — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11220")
CITE_11235 = ("Error 11235: certificate invalid, domain mismatch — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11235")
CITE_11237 = ("Error 11237: certificate invalid, could not find path to "
              "certificate — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11237")
CITE_11206 = ("Error 11206: HTTP protocol violation — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11206")
CITE_11100 = ("Error 11100: invalid URL format — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11100")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_WEBHOOKS = ("Webhooks (HTTP callbacks) — Twilio Docs",
                 "https://www.twilio.com/docs/usage/webhooks")
CITE_SECURITY = ("Security — Twilio Docs", "https://www.twilio.com/docs/usage/security")
CITE_APPS = ("Application resource — Twilio Docs",
             "https://www.twilio.com/docs/usage/api/applications")
CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "webhook-tls-handshake-failure-11220",
"title": "Error 11220: the TLS handshake with your webhook never completes",
"description": "11220 is a refusal during negotiation, before any certificate is presented. Browsers still load the URL because they offer things Twilio's client does not.",
"h1": "error 11220: the TLS handshake with your webhook never completes",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11220", "twilio ssl tls handshake error",
             "twilio webhook tls 1.2", "twilio webhook cipher suite",
             "twilio handshake failure webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You paste the webhook URL into a browser and it loads, padlock and all. You run <code>curl</code> against it and get your TwiML back. And the Debugger keeps filling with <code>11220 SSL/TLS Handshake Error</code> for that exact URL. Nothing is wrong with the certificate, because nothing ever got as far as looking at the certificate &mdash; the two ends could not agree on how to talk before either of them said who they were.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code>, keep <code>error_code</code> <code>11220</code>, and key the results on <em>host and port</em> from <code>request_url</code>, writing the port out even when it is 443.</p>
<p>Then read every other code logged against that same listener. If <code>11200</code>, <code>11206</code>, <code>12100</code>, <code>12300</code> or <code>11750</code> also appear, TLS completed for those requests, so the endpoint is not uniformly refusing to negotiate and you are looking at one machine with an old configuration. If nothing but 11220 appears, the listener offers no protocol version or cipher suite Twilio's client accepts &mdash; almost always TLS 1.0/1.1 only, or a hand-hardened suite list.</p>""",
"problem": """<p>The handshake is the part of TLS that happens before identity. Client and server exchange what versions and cipher suites they support and pick an intersection; the certificate is not sent until that intersection exists. So an 11220 tells you something narrower than "TLS is broken": it tells you the intersection was empty. Nothing was validated, nothing was refused on trust grounds, and the certificate on that host may be flawless.</p>
<p>That is why every tool on your desk disagrees with Twilio. A browser carries a deliberately generous compatibility list, and <code>curl</code> offers whatever the local OpenSSL was built with, which on a developer laptop is usually broad. Twilio's HTTP client offers what it offers. Three clients, three different intersections with your server, and only one of them empty &mdash; which is experienced as "it works everywhere except Twilio", a sentence that sends people to look at Twilio.</p>""",
"why": """<p><strong>A handshake failure is not a certificate failure, and the codes are separate for a reason.</strong> <code>11235</code>, <code>11236</code> and <code>11237</code> all mean a certificate was presented and rejected. 11220 means the conversation ended earlier than that. Treating them as one bucket called "SSL problems" is how a team spends an afternoon renewing a certificate that had two months left on it.</p>
<p><strong>The listener is the unit, not the hostname.</strong> One hostname can front <code>:443</code> and <code>:8443</code> with two entirely separate protocol configurations, often on two different pieces of software. Keying on the hostname alone merges them and produces a verdict about an endpoint that does not exist. Writing the port out even when it is the default keeps the report readable as a list of things you can go and reconfigure.</p>
<p><strong>Other codes on the same listener are the strongest evidence you have.</strong> An <code>11200</code> means Twilio read a response and disliked the status; an <code>11206</code> means it read bytes it could not parse; a <code>12100</code> means it parsed the HTTP and disliked the XML. Every one of those required a completed handshake. Their presence alongside 11220 is proof that the endpoint negotiates fine with Twilio some of the time, which narrows the problem from "the server" to "one node behind the balancer".</p>
<p><strong>Sweeping only the error level hides that evidence.</strong> Several Twilio failures are recorded at <code>LogLevel=warning</code> rather than <code>error</code>. The 11220s themselves are errors, so a single-level sweep still finds the failing listener &mdash; it just loses some of the alerts that prove TLS worked, and the verdict flips from "one stale node" to "this endpoint is misconfigured". Read both levels.</p>""",
"steps": [
 {"h": "Sweep both log levels for the window you care about",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>, then the same again with <code>LogLevel=warning</code>. Alerts are retained 30 days and the request is capped at 10,000, so pick a window rather than asking for everything and hoping.</p>"""},
 {"h": "Read error_code as an integer",
  "body": """<p>The Monitor API returns <code>error_code</code> as a string. Comparing the raw value against <code>11220</code> matches nothing and reports a spotless account, which is the single most convincing wrong answer this API can give you.</p>"""},
 {"h": "Key on host and port, with the port written out",
  "body": """<p>Derive the key from <code>request_url</code> as <code>host:port</code>, filling in 443 for <code>https</code> and 80 for <code>http</code>. The negotiation belongs to a listener. Two on the same name can have two different stories, and the port is the half of the key that tells you which config file to open.</p>"""},
 {"h": "Count every code against that listener, not just 11220",
  "body": """<p>Keep the whole tally. Certificate codes <code>11235</code>, <code>11236</code> and <code>11237</code> mean a certificate was presented, so the handshake reached that stage at least sometimes. Codes that require a response body &mdash; <code>11200</code>, <code>11206</code>, <code>11750</code>, <code>12100</code>, <code>12300</code> &mdash; mean it completed. Both groups change what the 11220s mean.</p>"""},
 {"h": "Fix it on the endpoint, because there is no Twilio-side setting",
  "body": """<p>Enable TLS 1.2 or later with a mainstream cipher suite list on the server or load balancer terminating that port, then re-run over a window that starts after the change. If the verdict was one stale node, find the node: a pool member restored from an old image, or a terminator that was upgraded everywhere except one region.</p>"""},
],
"verify": """<p>Re-run over a window that begins after the reconfiguration. The listener should be gone from the report entirely, not merely quieter.</p>
<pre><code class="language-bash">python3 twilio_tls_handshake_audit.py --days 1
# 0 listener(s) failing the TLS handshake</code></pre>""",
"code_intro": "Two sweeps of one endpoint &mdash; the alerts list at error level and at warning level &mdash; and a classifier made entirely of code counts. The pure parts are the listener key and the verdict, because the whole argument of this note is that other codes on the same listener change what an 11220 means, and an argument like that should be somewhere a test can hold it still.",
"py_file": "twilio_tls_handshake_audit.py",
"py": '''"""Report webhook listeners whose TLS handshake Twilio cannot complete (11220).

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
log = logging.getLogger("twilio_tls_handshake_audit")

MONITOR = "https://monitor.twilio.com/v1"

HANDSHAKE = 11220

# Certificate validation failures. Each of these means a certificate was
# presented, which means the handshake got past version and cipher negotiation.
# They are a different fault on a different file from an 11220.
CERT_CODES = (11235, 11236, 11237)

# Codes that cannot be raised until a response has been read back. Every one of
# them required a completed handshake, so their presence beside an 11220 is the
# evidence that separates "this listener offers nothing we accept" from "one
# machine behind the balancer does not".
REACHED_CODES = (11200, 11206, 11750, 12100, 12300)

# Alerts are retained 30 days. Nothing here can see further back than that.
MAX_DAYS = 30

# Several Twilio failures are logged at warning rather than error. The 11220s
# are errors either way, but some of the REACHED_CODES are not, and losing them
# turns one stale node into a report that condemns the whole endpoint.
LEVELS = ("error", "warning")

DEFAULT_PORTS = {"http": 80, "https": 443}


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API returns this as a string. Comparing the raw value against
    11220 matches nothing and reports a healthy account.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def listener(url):
    """Host and port, with the port always written out.

    A handshake is negotiated by whatever is listening on a port, not by a
    domain, and the port is the half of the key that says which config file to
    open. It stays in the key even when it is the default, because a report that
    silently drops 443 reads as though the port did not matter.
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
    scheme = (parts.scheme or "").lower()
    return "%s:%d" % (host, port or DEFAULT_PORTS.get(scheme, 443))


def sweep(alerts):
    """Tally every alert per listener, by error code. Pure.

    Listeners with no 11220 are dropped at the end: they are the healthy rest of
    the account and they would bury the four rows that matter.
    """
    out = {}
    for a in alerts:
        code = code_of(a)
        if code is None:
            continue
        key = listener(a.get("request_url"))
        if not key:
            continue
        row = out.setdefault(key, {"codes": {}, "sids": [], "url": ""})
        row["codes"][code] = row["codes"].get(code, 0) + 1
        if code == HANDSHAKE:
            row["url"] = row["url"] or (a.get("request_url") or "")
            if len(row["sids"]) < 3:
                row["sids"].append(a.get("sid"))
    return {k: v for k, v in out.items() if v["codes"].get(HANDSHAKE)}


def verdict(row):
    """Classify one listener from the mix of codes logged against it. Pure.

    The order is the point. A certificate code proves the handshake reached the
    stage where a certificate is sent; a code that needed a response proves it
    finished. Either one contradicts the simple reading of an 11220, and both
    are cheaper to act on than a protocol audit.

    Returns (state, detail).
    """
    codes = row.get("codes") or {}
    n = int(codes.get(HANDSHAKE) or 0)
    if not n:
        return ("clean", "no 11220 on this listener")

    certs = sorted((c, codes[c]) for c in CERT_CODES if codes.get(c))
    if certs:
        named = ", ".join("%d x %d" % (count, code) for code, count in certs)
        return ("certificate-first",
                "%d x 11220, and also %s. A certificate is only sent once "
                "version and cipher are agreed, so this listener is not "
                "refusing every negotiation. Clear the named certificate fault "
                "first and re-run." % (n, named))

    reached = sum(codes.get(c, 0) for c in REACHED_CODES)
    if reached:
        return ("one-node",
                "%d x 11220 beside %d alert(s) that could only be raised after "
                "a response was read. TLS completed for those, so the endpoint "
                "does negotiate with this client: one machine behind the "
                "balancer is still on the old protocol configuration."
                % (n, reached))

    return ("no-shared-parameters",
            "%d x 11220 and not one alert that required a response. Every "
            "attempt ended during negotiation: this listener offers no protocol "
            "version or cipher suite the client will accept." % n)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, since, limit, log_level):
    """Page the Monitor alerts at one level. next_page_url is absolute here."""
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
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging at this many alerts per log level")
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

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=days)).date().isoformat()

    alerts = []
    for level in LEVELS:
        got = list_alerts(session, since, args.max_alerts, level)
        log.info("%d alert(s) at LogLevel=%s since %s", len(got), level, since)
        alerts.extend(got)

    rows = sweep(alerts)
    if not rows:
        log.info("no 11220 since %s across %d alert(s)", since, len(alerts))
        return 0

    bad = 0
    for key, row in sorted(rows.items()):
        state, detail = verdict(row)
        line = "%-21s %s  %s" % (state, key, detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  sample %s, alert sids: %s", row["url"] or "(none)",
                    ", ".join(str(s) for s in row["sids"]))
        log.warning("  codes seen here: %s",
                    ", ".join("%d x %d" % (v, c)
                              for c, v in sorted(row["codes"].items())))
        log.warning("  repair: enable TLS 1.2 or later with a mainstream cipher "
                    "suite list on the server or load balancer terminating %s. "
                    "There is no Twilio-side setting for this; the negotiation "
                    "happens entirely on your endpoint.", key)

    log.info("%d listener(s) failing the TLS handshake", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-tls-handshake-audit.mjs",
"js": '''/**
 * Report webhook listeners whose TLS handshake Twilio cannot complete (11220).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';

const HANDSHAKE = 11220;

// A certificate is only presented once version and cipher are agreed, so any of
// these means the handshake got past negotiation.
const CERT_CODES = [11235, 11236, 11237];

// Codes that cannot be raised until a response was read back, so each one
// required a completed handshake.
const REACHED_CODES = [11200, 11206, 11750, 12100, 12300];

// Alerts are retained 30 days.
const MAX_DAYS = 30;

// Several Twilio failures are logged at warning rather than error, and some of
// the REACHED_CODES are among them.
const LEVELS = ['error', 'warning'];

const DEFAULT_PORTS = { 'http:': 80, 'https:': 443 };

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
 * Host and port, with the port always written out. A handshake belongs to a
 * listener, and the port is the half of the key that names the config file.
 */
export function listener(url) {
  if (!url) return '';
  let u;
  try {
    u = new URL(String(url).trim());
  } catch {
    return '';
  }
  const host = u.hostname.toLowerCase();
  if (!host) return '';
  const port = u.port ? Number(u.port) : (DEFAULT_PORTS[u.protocol] ?? 443);
  return `${host}:${port}`;
}

/**
 * Tally every alert per listener, by error code. Pure. Listeners with no 11220
 * are dropped, because they are the healthy rest of the account.
 */
export function sweep(alerts) {
  const out = new Map();
  for (const a of alerts) {
    const code = codeOf(a);
    if (code === null) continue;
    const key = listener(a.request_url);
    if (!key) continue;
    if (!out.has(key)) out.set(key, { codes: {}, sids: [], url: '' });
    const row = out.get(key);
    row.codes[code] = (row.codes[code] ?? 0) + 1;
    if (code === HANDSHAKE) {
      row.url = row.url || (a.request_url ?? '');
      if (row.sids.length < 3) row.sids.push(a.sid);
    }
  }
  for (const [key, row] of out) if (!row.codes[HANDSHAKE]) out.delete(key);
  return out;
}

/**
 * Classify one listener from the mix of codes logged against it. Pure.
 * Returns [state, detail].
 */
export function verdict(row) {
  const codes = row.codes ?? {};
  const n = Number(codes[HANDSHAKE] ?? 0);
  if (!n) return ['clean', 'no 11220 on this listener'];

  const certs = CERT_CODES.filter((c) => codes[c]).sort((a, b) => a - b);
  if (certs.length) {
    const named = certs.map((c) => `${codes[c]} x ${c}`).join(', ');
    return ['certificate-first',
      `${n} x 11220, and also ${named}. A certificate is only sent once ` +
      'version and cipher are agreed, so this listener is not refusing every ' +
      'negotiation. Clear the named certificate fault first and re-run.'];
  }

  const reached = REACHED_CODES.reduce((t, c) => t + (codes[c] ?? 0), 0);
  if (reached) {
    return ['one-node',
      `${n} x 11220 beside ${reached} alert(s) that could only be raised ` +
      'after a response was read. TLS completed for those, so the endpoint ' +
      'does negotiate with this client: one machine behind the balancer is ' +
      'still on the old protocol configuration.'];
  }

  return ['no-shared-parameters',
    `${n} x 11220 and not one alert that required a response. Every attempt ` +
    'ended during negotiation: this listener offers no protocol version or ' +
    'cipher suite the client will accept.'];
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

export async function listAlerts(auth, since, limit, logLevel) {
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

  const arg = process.argv.indexOf('--days');
  let days = arg > -1 ? Number(process.argv[arg + 1]) : 7;
  if (!Number.isFinite(days) || days < 1) days = 7;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS}`);
    days = MAX_DAYS;
  }

  const since = new Date(Date.now() - days * 86400_000).toISOString().slice(0, 10);

  const alerts = [];
  for (const level of LEVELS) {
    const got = await listAlerts(auth, since, 10000, level);
    console.log(`${got.length} alert(s) at LogLevel=${level} since ${since}`);
    alerts.push(...got);
  }

  const rows = sweep(alerts);
  if (rows.size === 0) {
    console.log(`no 11220 since ${since} across ${alerts.length} alert(s)`);
    return;
  }

  let bad = 0;
  for (const key of [...rows.keys()].sort()) {
    const row = rows.get(key);
    const [state, detail] = verdict(row);
    const line = `${state.padEnd(21)} ${key}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  sample ${row.url || '(none)'}, alert sids: ${row.sids.join(', ')}`);
    const seen = Object.entries(row.codes)
      .sort((a, b) => Number(a[0]) - Number(b[0]))
      .map(([c, v]) => `${v} x ${c}`).join(', ');
    console.warn(`  codes seen here: ${seen}`);
    console.warn('  repair: enable TLS 1.2 or later with a mainstream cipher ' +
      `suite list on the server or load balancer terminating ${key}. There is ` +
      'no Twilio-side setting for this; the negotiation happens entirely on ' +
      'your endpoint.');
  }

  console.log(`${bad} listener(s) failing the TLS handshake`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The judgements worth freezing are the three readings of an 11220. A listener with certificate errors beside it reached the stage where certificates are sent, so it is not the protocol. A listener with codes that required a response body negotiated successfully at least sometimes, so it is one machine and not the endpoint. Only the listener with nothing but 11220 against it is the plain case, and it is the least common of the three.",
"test_py_file": "test_twilio_tls_handshake_audit.py",
"test_py": '''from twilio_tls_handshake_audit import code_of, listener, sweep, verdict


def alert(sid, url, code="11220"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": "2026-05-05T14:08:00Z"}


def test_listener_always_writes_the_port_out():
    assert listener("https://hooks.example.com/voice") == "hooks.example.com:443"
    assert listener("https://Hooks.Example.com:8443/voice") == "hooks.example.com:8443"
    assert listener("http://hooks.example.com/voice") == "hooks.example.com:80"
    assert listener("not a url") == ""
    assert listener(None) == ""


def test_code_of_reads_the_string_the_monitor_api_returns():
    assert code_of({"error_code": "11220"}) == 11220
    assert code_of({"error_code": 11220}) == 11220
    assert code_of({"error_code": ""}) is None
    assert code_of({}) is None


def test_sweep_drops_listeners_with_no_handshake_failure():
    rows = sweep([alert("A1", "https://a.example.com/voice"),
                  alert("A2", "https://b.example.com/voice", code="11200"),
                  alert("A3", "https://a.example.com:8443/voice")])
    assert sorted(rows) == ["a.example.com:443", "a.example.com:8443"]


def test_two_ports_on_one_host_are_two_listeners():
    rows = sweep([alert("A1", "https://a.example.com/voice"),
                  alert("A2", "https://a.example.com:8443/voice")])
    assert rows["a.example.com:443"]["codes"][11220] == 1
    assert rows["a.example.com:8443"]["codes"][11220] == 1


def test_a_certificate_code_beside_it_means_the_handshake_got_further():
    state, detail = verdict({"codes": {11220: 40, 11236: 12}})
    assert state == "certificate-first"
    assert "11236" in detail


def test_a_code_that_needed_a_response_means_one_stale_node():
    # 11200 cannot be raised without a completed handshake, so TLS worked for
    # those requests and the endpoint as a whole negotiates fine.
    state, detail = verdict({"codes": {11220: 9, 11200: 300}})
    assert state == "one-node"
    assert "balancer" in detail


def test_only_11220_is_the_plain_protocol_mismatch():
    state, detail = verdict({"codes": {11220: 512}})
    assert state == "no-shared-parameters"
    assert "cipher suite" in detail


def test_no_handshake_failures_is_clean():
    assert verdict({"codes": {11200: 4}})[0] == "clean"
    assert verdict({})[0] == "clean"
''',
"test_js_file": "twilio-tls-handshake-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { codeOf, listener, sweep, verdict } from './twilio-tls-handshake-audit.mjs';

const alert = (sid, url, code = '11220') => ({
  sid, request_url: url, error_code: code, date_generated: '2026-05-05T14:08:00Z',
});

test('listener always writes the port out', () => {
  assert.equal(listener('https://hooks.example.com/voice'), 'hooks.example.com:443');
  assert.equal(listener('https://Hooks.Example.com:8443/voice'), 'hooks.example.com:8443');
  assert.equal(listener('http://hooks.example.com/voice'), 'hooks.example.com:80');
  assert.equal(listener('not a url'), '');
  assert.equal(listener(null), '');
});

test('codeOf reads the string the Monitor API returns', () => {
  assert.equal(codeOf({ error_code: '11220' }), 11220);
  assert.equal(codeOf({ error_code: 11220 }), 11220);
  assert.equal(codeOf({ error_code: '' }), null);
  assert.equal(codeOf({}), null);
});

test('sweep drops listeners with no handshake failure', () => {
  const rows = sweep([
    alert('A1', 'https://a.example.com/voice'),
    alert('A2', 'https://b.example.com/voice', '11200'),
    alert('A3', 'https://a.example.com:8443/voice'),
  ]);
  assert.deepEqual([...rows.keys()].sort(), ['a.example.com:443', 'a.example.com:8443']);
});

test('two ports on one host are two listeners', () => {
  const rows = sweep([
    alert('A1', 'https://a.example.com/voice'),
    alert('A2', 'https://a.example.com:8443/voice'),
  ]);
  assert.equal(rows.get('a.example.com:443').codes[11220], 1);
  assert.equal(rows.get('a.example.com:8443').codes[11220], 1);
});

test('a certificate code beside it means the handshake got further', () => {
  const [state, detail] = verdict({ codes: { 11220: 40, 11236: 12 } });
  assert.equal(state, 'certificate-first');
  assert.match(detail, /11236/);
});

test('a code that needed a response means one stale node', () => {
  const [state, detail] = verdict({ codes: { 11220: 9, 11200: 300 } });
  assert.equal(state, 'one-node');
  assert.match(detail, /balancer/);
});

test('only 11220 is the plain protocol mismatch', () => {
  const [state, detail] = verdict({ codes: { 11220: 512 } });
  assert.equal(state, 'no-shared-parameters');
  assert.match(detail, /cipher suite/);
});

test('no handshake failures is clean', () => {
  assert.equal(verdict({ codes: { 11200: 4 } })[0], 'clean');
  assert.equal(verdict({})[0], 'clean');
});
''',
"faq": [
 ("The URL loads in my browser. How can the handshake be failing?",
  "Because a browser and Twilio's HTTP client offer different sets of protocol versions and cipher suites. The handshake succeeds when the two sides share at least one; a browser carries a deliberately generous compatibility list, so it can find an intersection where a stricter client finds none. Your browser is evidence about your browser."),
 ("Is 11220 the same thing as an expired or untrusted certificate?",
  "No, and the distinction saves real time. A certificate is sent only after version and cipher are agreed, so 11235, 11236 and 11237 all imply the handshake got that far. An 11220 means it ended before the server ever identified itself, which is why the certificate on the host is often perfectly fine."),
 ("Why key the report on host and port rather than hostname?",
  "Because the protocol configuration belongs to whatever is listening on a port. One hostname can front 443 and 8443 with two different terminators and two different cipher lists, and merging them yields a verdict about an endpoint that does not exist."),
 ("I get some 11220s and plenty of successful webhooks on the same host. What does that mean?",
  "That the endpoint negotiates with Twilio perfectly well most of the time, so it is not offering an unacceptable protocol set. Look for one machine: a pool member restored from an older image, a terminator upgraded everywhere except one region, or a canary running different software."),
 ("Can I ask Twilio to accept the older TLS version?",
  "No. There is no per-account setting for the protocol versions or cipher suites Twilio's client offers, and Twilio has been retiring TLS 1.0 and 1.1 across its interfaces. The entire repair is on the terminating server or load balancer."),
],
"related": [
 ("/twilio/webhook-tls-chain-untrusted-11237/", "A chain Twilio cannot build a path from"),
 ("/twilio/webhook-tls-certificate-expired-11236/", "An expired certificate fails everything at once"),
 ("/twilio/webhook-connection-timeout-11205/", "Twilio cannot open a connection at all"),
],
"citations": [CITE_11220, CITE_ALERTS, CITE_WEBHOOKS, CITE_KEYS],
},

{
"slug": "webhook-tls-chain-untrusted-11237",
"title": "Error 11237: your webhook sends a chain Twilio cannot verify",
"description": "A missing intermediate or a private CA leaves Twilio with no path to a trusted root. Browsers hide the fault by fetching the part your server left out.",
"h1": "error 11237: your webhook sends a chain Twilio cannot verify",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11237", "twilio error 11235",
             "twilio certificate could not find path", "twilio webhook missing intermediate",
             "twilio self signed certificate webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The certificate is valid. It was issued last week, it does not expire for a year, and every browser in the office shows a padlock. Twilio still refuses it with <code>11237 Certificate Invalid - Could not find path to certificate</code>, because your server is sending one certificate where it should be sending two, and the browsers have been quietly covering for it since the day it was installed.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> and keep <code>error_code</code> in <code>(11235, 11237)</code>. Group by the hostname in <code>request_url</code> and count the two codes separately: they are different repairs. <code>11237</code> means no path to a trusted root &mdash; a missing intermediate, or a certificate from a CA that is not in Twilio's trust store. <code>11235</code> means the certificate is trusted but does not name the host that was requested.</p>
<p>Then read <code>GET /2010-04-01/Accounts/{AccountSid}/Applications.json</code> and find which TwiML Apps carry that host in any URL field, because an Application's URLs do not appear on the phone numbers that use it and are the ones people forget.</p>""",
"problem": """<p>A certificate on its own proves nothing. It is signed by an intermediate, which is signed by a root, and the verifying party has to be able to walk that path to a root it already trusts. Your server is supposed to send the leaf <em>and</em> the intermediates so the other end can do the walk. When it sends only the leaf, verification depends entirely on whether the client happens to have the intermediate lying around.</p>
<p>Browsers usually do. They cache intermediates from other sites, and most will fetch a missing one from the URL named in the certificate rather than fail. Twilio's client does neither. So the install looks perfect from every desk in the building, ships, and then one class of traffic &mdash; the automated kind, the kind with no human to click through &mdash; fails completely and permanently while the padlock stays green.</p>""",
"why": """<p><strong>Twilio validates against a fixed trust store and does not chase what is missing.</strong> Only CAs in that store are trusted, and no intermediate is fetched on demand. A certificate signed by an internal CA, a corporate MITM appliance, or a self-signed one has no path at all, and no amount of reissuing will produce one until the certificate comes from a public CA.</p>
<p><strong>11235 and 11237 arrive together and mean different things.</strong> 11237 is a trust problem: the chain does not reach a root. 11235 is a naming problem: the chain is fine but no SAN covers the host requested. Counting them as one number produces a report that recommends installing intermediates on a host whose actual fault is a wildcard that does not cover the label it was pointed at.</p>
<p><strong>A URL written as an IP address cannot really be fixed by a certificate.</strong> Certificates can carry an IP in a SAN, but very few public CAs issue them and almost no deployment has one. A webhook whose <code>request_url</code> is an address rather than a name is an internal value that escaped into production, and the repair is a hostname, not a reissue.</p>
<p><strong>Alongside an expiry, the chain finding is usually the second symptom of one event.</strong> Renewal rewrites the file the chain is read from. A renewal script that installs only the leaf takes a host straight from <code>11236</code> to <code>11237</code>, so a host showing both did not develop two independent faults &mdash; it had one bad renewal, and the repair is to install the full bundle in the same step.</p>""",
"steps": [
 {"h": "Sweep the alerts for both certificate-path codes",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>, keeping <code>11235</code> and <code>11237</code> in separate counters. Read <code>error_code</code> as an integer; the API returns it as a string. Alerts stop at 30 days, so this is a window, not a history.</p>"""},
 {"h": "Group by hostname, and notice when it is an address",
  "body": """<p>A certificate names hosts, so the hostname is the right key here. Flag the case where the host is an IPv4 or IPv6 literal: that is a structural finding rather than a certificate one, and it needs a DNS name before anything else is worth trying.</p>"""},
 {"h": "Keep 11236 in the tally without merging it",
  "body": """<p>An expiry on the same host almost always shares a cause with the chain finding, because a renewal replaces the file both are read from. Report it as one event with two symptoms so the fix installs the full bundle rather than the leaf again.</p>"""},
 {"h": "Check whether anything on that host ever answered",
  "body": """<p>If codes that require a response body &mdash; <code>11200</code>, <code>11206</code>, <code>12100</code>, <code>12300</code> &mdash; also appear against the host, then some requests validated fine. That is a partial chain: one node serving the full bundle and another serving the leaf, which is what a deploy that copied only one file looks like.</p>"""},
 {"h": "Find the TwiML Apps pointing at it, then serve the full bundle",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Applications.json</code> and list every app with that host in <code>voice_url</code>, <code>sms_url</code>, either fallback, or a status callback. Concatenate leaf plus intermediates in the server's certificate file and reload. For an 11235, reissue with a SAN that covers the exact host. The <a href="/twilio/webhook-tls-certificate-expired-11236/">expiry note</a> covers the number-side blast radius.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the reload. The host should be absent, not merely reduced.</p>
<pre><code class="language-bash">python3 twilio_webhook_chain_audit.py --days 1
# 0 host(s) with a certificate Twilio cannot verify</code></pre>""",
"code_intro": "One alerts sweep, one applications list, and a classifier that keeps the two certificate-path codes apart. The pure parts are the IP-literal test and the verdict, because the ordering inside that verdict &mdash; expiry before chain, address before name &mdash; is the whole recommendation, and an ordering is exactly the kind of thing that drifts unless a test is holding it.",
"py_file": "twilio_webhook_chain_audit.py",
"py": '''"""Report webhook hosts whose certificate chain Twilio cannot verify (11237/11235).

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
log = logging.getLogger("twilio_webhook_chain_audit")

HOST_API = "https://api.twilio.com"
BASE = HOST_API + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

NO_PATH = 11237       # trusted root not reachable from what was presented
NAME_MISMATCH = 11235  # trusted, but no SAN covers the host requested
EXPIRED = 11236        # dated out; shares a cause with NO_PATH after a renewal

# Codes that require a response to have been read, so validation succeeded for
# those requests. Their presence means some nodes serve a complete chain.
REACHED_CODES = (11200, 11206, 11750, 12100, 12300)

# Alerts are retained 30 days.
MAX_DAYS = 30

# Every Application field that can hold a URL. An app's URLs are invisible from
# the phone numbers that use it, which is why they get missed.
APP_URL_FIELDS = ("voice_url", "voice_fallback_url", "sms_url", "sms_fallback_url",
                  "status_callback", "sms_status_callback")


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API returns this as a string, and comparing it raw against
    11237 quietly reports a clean account.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def webhook_host(url):
    """Lowercase hostname from a URL, with no port.

    Certificates name hosts, not listeners, so unlike a protocol audit the port
    is noise here: one certificate covers every port on the name.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    return (parts.hostname or "").lower()


def is_ip_literal(host):
    """True when the host is an address rather than a name. Pure.

    A certificate can carry an IP in a SAN, but few public CAs issue one and
    almost no deployment has one, so an address in a webhook URL is an internal
    value that escaped rather than a certificate to reissue.
    """
    h = str(host or "").strip().lower()
    if not h:
        return False
    if ":" in h:
        return True
    parts = h.split(".")
    return (len(parts) == 4
            and all(p.isdigit() and len(p) <= 3 and int(p) < 256 for p in parts))


def sweep(alerts):
    """Tally alerts per hostname, by error code. Pure.

    Hosts with neither certificate-path code are dropped at the end: they are
    the healthy remainder and they would bury the rows worth reading.
    """
    out = {}
    for a in alerts:
        code = code_of(a)
        if code is None:
            continue
        host = webhook_host(a.get("request_url"))
        if not host:
            continue
        row = out.setdefault(host, {"codes": {}, "sids": [], "url": "",
                                    "ip": is_ip_literal(host)})
        row["codes"][code] = row["codes"].get(code, 0) + 1
        if code in (NO_PATH, NAME_MISMATCH):
            row["url"] = row["url"] or (a.get("request_url") or "")
            if len(row["sids"]) < 3:
                row["sids"].append(a.get("sid"))
    return {h: r for h, r in out.items()
            if r["codes"].get(NO_PATH) or r["codes"].get(NAME_MISMATCH)}


def verdict(row):
    """Classify one host from the codes logged against it. Pure.

    The order is the recommendation. An expiry is checked first because renewal
    rewrites the file the chain is read from, so fixing it fixes both. An
    address is checked next because no reissue helps a URL that should have been
    a name. Only then does the split between trust and naming matter.

    Returns (state, detail).
    """
    codes = row.get("codes") or {}
    path = int(codes.get(NO_PATH) or 0)
    name = int(codes.get(NAME_MISMATCH) or 0)
    if not path and not name:
        return ("clean", "no 11237 or 11235 on this host")

    if codes.get(EXPIRED):
        return ("renew-first",
                "%d x 11237 and %d x 11235 beside %d x 11236. A renewal rewrites "
                "the file the chain is read from, so this is one bad renewal "
                "with two symptoms: install the leaf and the intermediates "
                "together." % (path, name, codes[EXPIRED]))

    if row.get("ip") and name:
        return ("address-not-a-name",
                "%d x 11235 against an IP address. Almost no public CA issues "
                "certificates for addresses, so this URL needs a DNS name "
                "before a certificate can cover it at all." % name)

    if path and name:
        return ("chain-and-name",
                "%d x 11237 and %d x 11235: two independent faults. The chain "
                "does not reach a trusted root, and the certificate does not "
                "name this host either." % (path, name))

    if name:
        return ("name-mismatch",
                "%d x 11235. The chain verifies, but no SAN covers this exact "
                "host: usually a wildcard pointed at the apex, or at a label "
                "one level deeper than it covers." % name)

    if sum(codes.get(c, 0) for c in REACHED_CODES):
        return ("partial-chain",
                "%d x 11237 alongside requests that were answered. Validation "
                "succeeded for those, so some nodes send the intermediates and "
                "some send only the leaf." % path)

    return ("no-trust-path",
            "%d x 11237 and nothing answered. Either the intermediates are "
            "missing from the certificate file, or the issuer is a private CA "
            "that no public trust store contains." % path)


def apps_on_host(applications, host):
    """Which TwiML Apps carry this host in any URL field. Pure.

    Worth its own pass because an Application's URLs never appear on the phone
    numbers that route through it, so they survive an audit that only reads
    numbers.
    """
    out = []
    for app in applications or []:
        fields = [f for f in APP_URL_FIELDS if webhook_host(app.get(f)) == host]
        if fields:
            out.append({"sid": app.get("sid") or "?",
                        "name": app.get("friendly_name") or "(unnamed)",
                        "fields": fields})
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


def list_applications(session, account, limit=2000):
    """Page the TwiML Applications. next_page_uri here is a path, not a URL."""
    url = "%s/Accounts/%s/Applications.json" % (BASE, account)
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("applications", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST_API + nxt) if nxt else None, {}
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

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=days)).date().isoformat()

    alerts = list_alerts(session, since, args.max_alerts)
    rows = sweep(alerts)
    if not rows:
        log.info("no 11237 or 11235 since %s across %d alert(s)",
                 since, len(alerts))
        return 0

    applications = list_applications(session, account)
    bad = 0
    for host, row in sorted(rows.items()):
        state, detail = verdict(row)
        line = "%-19s %s  %s" % (state, host, detail)
        if state == "clean":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  sample %s, alert sids: %s", row["url"] or "(none)",
                    ", ".join(str(s) for s in row["sids"]))
        for app in apps_on_host(applications, host):
            log.warning("  app %s %s uses it on %s", app["sid"], app["name"],
                        ", ".join(app["fields"]))
        log.warning("  repair: serve the leaf and its intermediates "
                    "concatenated in the certificate file and reload the "
                    "terminating server. For an 11235, reissue with a SAN that "
                    "covers %s exactly. There is no Twilio-side setting.", host)

    log.info("%d host(s) with a certificate Twilio cannot verify", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-webhook-chain-audit.mjs",
"js": '''/**
 * Report webhook hosts whose certificate chain Twilio cannot verify
 * (11237 and 11235).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST_API = 'https://api.twilio.com';
const BASE = `${HOST_API}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const NO_PATH = 11237;        // trusted root not reachable from what was sent
const NAME_MISMATCH = 11235;  // trusted, but no SAN covers the host requested
const EXPIRED = 11236;        // shares a cause with NO_PATH after a renewal

// Codes that require a response to have been read, so validation succeeded.
const REACHED_CODES = [11200, 11206, 11750, 12100, 12300];

// Alerts are retained 30 days.
const MAX_DAYS = 30;

// Every Application field that can hold a URL.
const APP_URL_FIELDS = ['voice_url', 'voice_fallback_url', 'sms_url',
  'sms_fallback_url', 'status_callback', 'sms_status_callback'];

/** Read error_code off an alert as a number, or null. */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Lowercase hostname from a URL, with no port. Certificates name hosts, so the
 * port is noise here: one certificate covers every port on the name.
 */
export function webhookHost(url) {
  if (!url) return '';
  try {
    return new URL(String(url).trim()).hostname.toLowerCase();
  } catch {
    return '';
  }
}

/**
 * True when the host is an address rather than a name. Pure. Few public CAs
 * issue certificates for addresses, so this is a URL to replace, not a
 * certificate to reissue.
 */
export function isIpLiteral(host) {
  const h = String(host ?? '').trim().toLowerCase();
  if (!h) return false;
  if (h.includes(':')) return true;
  const parts = h.split('.');
  return parts.length === 4 && parts.every(
    (p) => /^[0-9]{1,3}$/.test(p) && Number(p) < 256);
}

/**
 * Tally alerts per hostname, by error code. Pure. Hosts with neither
 * certificate-path code are dropped.
 */
export function sweep(alerts) {
  const out = new Map();
  for (const a of alerts) {
    const code = codeOf(a);
    if (code === null) continue;
    const host = webhookHost(a.request_url);
    if (!host) continue;
    if (!out.has(host)) {
      out.set(host, { codes: {}, sids: [], url: '', ip: isIpLiteral(host) });
    }
    const row = out.get(host);
    row.codes[code] = (row.codes[code] ?? 0) + 1;
    if (code === NO_PATH || code === NAME_MISMATCH) {
      row.url = row.url || (a.request_url ?? '');
      if (row.sids.length < 3) row.sids.push(a.sid);
    }
  }
  for (const [host, row] of out) {
    if (!row.codes[NO_PATH] && !row.codes[NAME_MISMATCH]) out.delete(host);
  }
  return out;
}

/**
 * Classify one host from the codes logged against it. Pure.
 * Returns [state, detail].
 */
export function verdict(row) {
  const codes = row.codes ?? {};
  const path = Number(codes[NO_PATH] ?? 0);
  const name = Number(codes[NAME_MISMATCH] ?? 0);
  if (!path && !name) return ['clean', 'no 11237 or 11235 on this host'];

  if (codes[EXPIRED]) {
    return ['renew-first',
      `${path} x 11237 and ${name} x 11235 beside ${codes[EXPIRED]} x 11236. ` +
      'A renewal rewrites the file the chain is read from, so this is one bad ' +
      'renewal with two symptoms: install the leaf and the intermediates ' +
      'together.'];
  }

  if (row.ip && name) {
    return ['address-not-a-name',
      `${name} x 11235 against an IP address. Almost no public CA issues ` +
      'certificates for addresses, so this URL needs a DNS name before a ' +
      'certificate can cover it at all.'];
  }

  if (path && name) {
    return ['chain-and-name',
      `${path} x 11237 and ${name} x 11235: two independent faults. The chain ` +
      'does not reach a trusted root, and the certificate does not name this ' +
      'host either.'];
  }

  if (name) {
    return ['name-mismatch',
      `${name} x 11235. The chain verifies, but no SAN covers this exact host: ` +
      'usually a wildcard pointed at the apex, or at a label one level deeper ' +
      'than it covers.'];
  }

  if (REACHED_CODES.reduce((t, c) => t + (codes[c] ?? 0), 0)) {
    return ['partial-chain',
      `${path} x 11237 alongside requests that were answered. Validation ` +
      'succeeded for those, so some nodes send the intermediates and some ' +
      'send only the leaf.'];
  }

  return ['no-trust-path',
    `${path} x 11237 and nothing answered. Either the intermediates are ` +
    'missing from the certificate file, or the issuer is a private CA that no ' +
    'public trust store contains.'];
}

/**
 * Which TwiML Apps carry this host in any URL field. Pure. An app's URLs never
 * appear on the numbers routing through it, so they survive a number-only audit.
 */
export function appsOnHost(applications, host) {
  const out = [];
  for (const app of applications ?? []) {
    const fields = APP_URL_FIELDS.filter((f) => webhookHost(app[f]) === host);
    if (fields.length) {
      out.push({ sid: app.sid ?? '?', name: app.friendly_name ?? '(unnamed)', fields });
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

export async function listApplications(auth, account, limit = 2000) {
  let url = `${BASE}/Accounts/${account}/Applications.json`;
  let params = { PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.applications ?? []));
    url = page.next_page_uri ? HOST_API + page.next_page_uri : null;
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

  const arg = process.argv.indexOf('--days');
  let days = arg > -1 ? Number(process.argv[arg + 1]) : 7;
  if (!Number.isFinite(days) || days < 1) days = 7;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS}`);
    days = MAX_DAYS;
  }
  const since = new Date(Date.now() - days * 86400_000).toISOString().slice(0, 10);

  const alerts = await listAlerts(auth, since);
  const rows = sweep(alerts);
  if (rows.size === 0) {
    console.log(`no 11237 or 11235 since ${since} across ${alerts.length} alert(s)`);
    return;
  }

  const applications = await listApplications(auth, account);
  let bad = 0;
  for (const host of [...rows.keys()].sort()) {
    const row = rows.get(host);
    const [state, detail] = verdict(row);
    const line = `${state.padEnd(19)} ${host}  ${detail}`;
    if (state === 'clean') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  sample ${row.url || '(none)'}, alert sids: ${row.sids.join(', ')}`);
    for (const app of appsOnHost(applications, host)) {
      console.warn(`  app ${app.sid} ${app.name} uses it on ${app.fields.join(', ')}`);
    }
    console.warn('  repair: serve the leaf and its intermediates concatenated ' +
      'in the certificate file and reload the terminating server. For an ' +
      `11235, reissue with a SAN that covers ${host} exactly. There is no ` +
      'Twilio-side setting.');
  }

  console.log(`${bad} host(s) with a certificate Twilio cannot verify`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "What the tests hold in place is the order of the verdict. An expiry on the same host outranks the chain finding, because one renewal caused both and one renewal fixes both. An address outranks a naming complaint, because no reissue rescues a URL that should have been a hostname. And a host that answered some requests is a partial chain rather than a missing one, which is a different machine to go and look at.",
"test_py_file": "test_twilio_webhook_chain_audit.py",
"test_py": '''from twilio_webhook_chain_audit import (
    apps_on_host, is_ip_literal, sweep, verdict, webhook_host)


def alert(sid, url, code="11237"):
    return {"sid": sid, "request_url": url, "error_code": code,
            "date_generated": "2026-05-05T14:08:00Z"}


def test_webhook_host_drops_the_port_because_certificates_name_hosts():
    assert webhook_host("https://Hooks.Example.com:8443/voice") == "hooks.example.com"
    assert webhook_host("https://hooks.example.com/voice") == "hooks.example.com"
    assert webhook_host("nonsense") == ""
    assert webhook_host(None) == ""


def test_is_ip_literal_accepts_addresses_and_rejects_names():
    assert is_ip_literal("203.0.113.9") is True
    assert is_ip_literal("2001:db8::1") is True
    assert is_ip_literal("hooks.example.com") is False
    assert is_ip_literal("203.0.113.999") is False
    assert is_ip_literal("") is False


def test_sweep_keeps_only_hosts_with_a_certificate_path_failure():
    rows = sweep([alert("A1", "https://a.example.com/voice"),
                  alert("A2", "https://b.example.com/voice", code="11200"),
                  alert("A3", "https://c.example.com/sms", code="11235")])
    assert sorted(rows) == ["a.example.com", "c.example.com"]


def test_a_port_does_not_split_a_host_the_way_it_splits_a_listener():
    rows = sweep([alert("A1", "https://a.example.com/voice"),
                  alert("A2", "https://a.example.com:8443/voice")])
    assert sorted(rows) == ["a.example.com"]
    assert rows["a.example.com"]["codes"][11237] == 2


def test_an_expiry_on_the_same_host_is_reported_as_one_bad_renewal():
    state, detail = verdict({"codes": {11237: 900, 11236: 120}})
    assert state == "renew-first"
    assert "one bad renewal" in detail


def test_a_mismatch_against_an_address_needs_a_name_not_a_reissue():
    state, detail = verdict({"codes": {11235: 40}, "ip": True})
    assert state == "address-not-a-name"
    assert "DNS name" in detail


def test_answered_requests_beside_11237_mean_a_partial_chain():
    state, detail = verdict({"codes": {11237: 30, 11200: 200}})
    assert state == "partial-chain"
    assert "only the leaf" in detail


def test_11237_alone_is_a_missing_intermediate_or_a_private_ca():
    state, detail = verdict({"codes": {11237: 2000}})
    assert state == "no-trust-path"
    assert "private CA" in detail


def test_both_codes_without_an_expiry_are_two_faults():
    assert verdict({"codes": {11237: 5, 11235: 5}})[0] == "chain-and-name"


def test_no_path_codes_is_clean():
    assert verdict({"codes": {11200: 12}})[0] == "clean"


def test_apps_on_host_finds_urls_that_no_phone_number_shows():
    apps = [
        {"sid": "AP1", "friendly_name": "voice router",
         "voice_url": "https://hooks.example.com/voice",
         "sms_url": "https://other.example.net/sms"},
        {"sid": "AP2", "voice_url": "https://elsewhere.example.net/voice"},
    ]
    hit = apps_on_host(apps, "hooks.example.com")
    assert [h["sid"] for h in hit] == ["AP1"]
    assert hit[0]["fields"] == ["voice_url"]
''',
"test_js_file": "twilio-webhook-chain-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  appsOnHost, isIpLiteral, sweep, verdict, webhookHost,
} from './twilio-webhook-chain-audit.mjs';

const alert = (sid, url, code = '11237') => ({
  sid, request_url: url, error_code: code, date_generated: '2026-05-05T14:08:00Z',
});

test('webhookHost drops the port because certificates name hosts', () => {
  assert.equal(webhookHost('https://Hooks.Example.com:8443/voice'), 'hooks.example.com');
  assert.equal(webhookHost('https://hooks.example.com/voice'), 'hooks.example.com');
  assert.equal(webhookHost('nonsense'), '');
  assert.equal(webhookHost(null), '');
});

test('isIpLiteral accepts addresses and rejects names', () => {
  assert.equal(isIpLiteral('203.0.113.9'), true);
  assert.equal(isIpLiteral('2001:db8::1'), true);
  assert.equal(isIpLiteral('hooks.example.com'), false);
  assert.equal(isIpLiteral('203.0.113.999'), false);
  assert.equal(isIpLiteral(''), false);
});

test('sweep keeps only hosts with a certificate path failure', () => {
  const rows = sweep([
    alert('A1', 'https://a.example.com/voice'),
    alert('A2', 'https://b.example.com/voice', '11200'),
    alert('A3', 'https://c.example.com/sms', '11235'),
  ]);
  assert.deepEqual([...rows.keys()].sort(), ['a.example.com', 'c.example.com']);
});

test('a port does not split a host the way it splits a listener', () => {
  const rows = sweep([
    alert('A1', 'https://a.example.com/voice'),
    alert('A2', 'https://a.example.com:8443/voice'),
  ]);
  assert.deepEqual([...rows.keys()], ['a.example.com']);
  assert.equal(rows.get('a.example.com').codes[11237], 2);
});

test('an expiry on the same host is reported as one bad renewal', () => {
  const [state, detail] = verdict({ codes: { 11237: 900, 11236: 120 } });
  assert.equal(state, 'renew-first');
  assert.match(detail, /one bad renewal/);
});

test('a mismatch against an address needs a name not a reissue', () => {
  const [state, detail] = verdict({ codes: { 11235: 40 }, ip: true });
  assert.equal(state, 'address-not-a-name');
  assert.match(detail, /DNS name/);
});

test('answered requests beside 11237 mean a partial chain', () => {
  const [state, detail] = verdict({ codes: { 11237: 30, 11200: 200 } });
  assert.equal(state, 'partial-chain');
  assert.match(detail, /only the leaf/);
});

test('11237 alone is a missing intermediate or a private CA', () => {
  const [state, detail] = verdict({ codes: { 11237: 2000 } });
  assert.equal(state, 'no-trust-path');
  assert.match(detail, /private CA/);
});

test('both codes without an expiry are two faults', () => {
  assert.equal(verdict({ codes: { 11237: 5, 11235: 5 } })[0], 'chain-and-name');
});

test('no path codes is clean', () => {
  assert.equal(verdict({ codes: { 11200: 12 } })[0], 'clean');
});

test('appsOnHost finds urls that no phone number shows', () => {
  const apps = [
    { sid: 'AP1',
      friendly_name: 'voice router',
      voice_url: 'https://hooks.example.com/voice',
      sms_url: 'https://other.example.net/sms' },
    { sid: 'AP2', voice_url: 'https://elsewhere.example.net/voice' },
  ];
  const hit = appsOnHost(apps, 'hooks.example.com');
  assert.deepEqual(hit.map((h) => h.sid), ['AP1']);
  assert.deepEqual(hit[0].fields, ['voice_url']);
});
''',
"faq": [
 ("Why does my browser accept a certificate that Twilio rejects?",
  "Because browsers fill in what your server left out. They cache intermediates seen on other sites and most will fetch a missing one from the address printed in the certificate. Twilio's client does neither: it validates against a fixed trust store using only what the server actually presented."),
 ("What is the difference between 11237 and 11235?",
  "11237 is a trust problem: nothing in what was presented leads to a root Twilio trusts, so the intermediates are missing or the issuer is private. 11235 is a naming problem: the chain is fine and the certificate simply does not cover the host requested. Different files, different repairs."),
 ("Can I add my internal CA to Twilio's trust store?",
  "No. There is no per-account trust configuration, which means a certificate from an internal CA, a corporate inspection appliance or a self-signed pair can never validate. A webhook endpoint has to hold a certificate from a public CA."),
 ("Why does the script report an expired certificate as the same finding?",
  "Because it usually is. Renewal replaces the file the chain is read from, and a renewal script that writes only the leaf takes a host straight from 11236 to 11237. Two symptoms, one bad renewal, one repair that installs the full bundle."),
 ("A few 11237s but most webhooks work. Is the chain broken or not?",
  "On some nodes. Validation is all or nothing for a given certificate, so requests that were answered were answered by a machine sending the complete bundle. Look for the node that got only the leaf copied to it, typically after a deploy that moved one file of two."),
],
"related": [
 ("/twilio/webhook-tls-certificate-expired-11236/", "The same host, dated out instead"),
 ("/twilio/webhook-tls-handshake-failure-11220/", "A refusal before any certificate is sent"),
 ("/twilio/webhook-dns-resolution-failure-11210/", "A hostname with no public DNS record"),
],
"citations": [CITE_11237, CITE_11235, CITE_ALERTS, CITE_APPS],
},

{
"slug": "webhook-http-protocol-violation-11206",
"title": "Error 11206: Twilio cannot parse your webhook's HTTP response",
"description": "Your server logs a 200 and Twilio logs a protocol violation. What broke the parse is in response_headers, which only the single-alert fetch returns.",
"h1": "error 11206: Twilio cannot parse your webhook's HTTP response",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 11206", "twilio http protocol violation",
             "twilio webhook set-cookie invalid", "twilio malformed response header",
             "twilio alert response_headers"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Your access log shows <code>200</code> for the request. Your framework's own instrumentation shows the handler completed in nine milliseconds and returned valid TwiML. And Twilio recorded <code>11206 HTTP protocol violation</code> for that exact request, which is not a complaint about your status code or your XML &mdash; it is Twilio saying that the bytes coming back were not a well-formed HTTP response at all.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> for <code>error_code</code> <code>11206</code> to find the failing endpoints. That is as far as the list gets you: <code>response_headers</code> and <code>response_body</code> are populated only by the single-alert fetch <code>GET https://monitor.twilio.com/v1/Alerts/{Sid}</code> and are absent from every row of the list.</p>
<p>So fetch a sample individually and read the header block. A <code>Set-Cookie</code> with an empty name, or one carrying raw control characters in its value, is the commonest cause. An alert with no header block at all usually means plain HTTP was served on a port the URL called <code>https</code>, so the first bytes were never a status line.</p>""",
"problem": """<p>11206 sits at a layer almost nothing else in your stack inspects. Your framework wrote a status line and a header block, your web server framed them, and somewhere between those two the result stopped being parseable. Because the response left your process looking correct, every log you own reports success, and the only party that saw the malformed bytes is the client &mdash; which is Twilio, and which wrote it down in a system you have to go and read on purpose.</p>
<p>The commonest source is a cookie, which is why it is so hard to guess. A session library that writes a cookie whose value came from user input, an A/B framework that stores a raw string, a middleware that sets a cookie with an empty name during an error path: all of them produce a header that your own server accepts and emits happily, and that a strict parser refuses. It is also intermittent by nature, because it depends on the value, so it looks like flakiness rather than a defect.</p>""",
"why": """<p><strong>The evidence is not in the list, and there is no way to filter for it.</strong> Every row of <code>GET /v1/Alerts</code> carries the code, the URL and the timestamp, and none of them carries <code>response_headers</code>. Seeing what actually came back costs one <code>GET /v1/Alerts/{Sid}</code> per alert, which is why this script samples rather than fetching everything: a busy account can log thousands of 11206s and you need five.</p>
<p><strong>11206 is not 11200, and the difference is where to look.</strong> An 11200 means Twilio read your response and disliked the status. An 11206 means it could not read the response. If you go looking for a bad status code in your handler you will find a good one, conclude Twilio is wrong, and stop.</p>
<p><strong>A cookie value is a header value, and header values have rules.</strong> Raw control characters &mdash; a stray newline, a tab, a <code>\\r</code> from a Windows-authored string &mdash; are not permitted in a header value, and a newline in particular is how header injection works, so strict clients refuse rather than repair. A cookie with an empty name is malformed for a simpler reason: there is nothing to name the value.</p>
<p><strong>Everything downstream of the parse is a different error code.</strong> If the HTTP parses and the Content-Type is wrong, that is <code>12300</code>. If the Content-Type is right and the XML is not well-formed, that is <code>12100</code>. If the TwiML is fine but enormous, that is <code>11750</code>. Reaching 11206 means the failure happened before any of those checks could run.</p>""",
"steps": [
 {"h": "Find the failing endpoints in the list",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>meta.next_page_url</code>, keeping <code>error_code</code> <code>11206</code>. Read the code as an integer; the API returns a string. Group by the host and path in <code>request_url</code> so you know which handler to open.</p>"""},
 {"h": "Budget the second fetch before you start it",
  "body": """<p><code>response_headers</code> exists only on <code>GET /v1/Alerts/{Sid}</code>, one request per alert. Take a small sample per endpoint rather than the whole set: the cause repeats, and a few alerts from one handler show the same malformed header the thousandth would.</p>"""},
 {"h": "Read the Set-Cookie values, character by character",
  "body": """<p>Look for two things. A value with any character below <code>0x20</code> or equal to <code>0x7f</code> in it &mdash; a newline, a carriage return, a tab &mdash; and a cookie whose name is empty, which is what <code>=value</code> means. Both are emitted happily by most servers and refused by strict clients.</p>"""},
 {"h": "Treat an empty header block as a scheme mismatch",
  "body": """<p>If the fetched alert has a <code>response_headers</code> field and it is empty, the parse failed before a header block existed. The usual cause is a listener answering plain HTTP on a port the configured URL declares as <code>https</code>, so the first bytes back are not a status line at all.</p>"""},
 {"h": "Fix the emitter, not the response",
  "body": """<p>Strip control characters from cookie values at the point they are set and drop cookies with no name; if the value is user-controlled, encode it. Where the header block was empty, make the scheme in the configured URL match what the port actually speaks. Then re-run over a fresh window.</p>"""},
],
"verify": """<p>Re-run over a window starting after the deploy. The endpoint should log no 11206 at all, rather than fewer.</p>
<pre><code class="language-bash">python3 twilio_webhook_protocol_audit.py --days 1 --sample 5
# 0 endpoint(s) returning an unparseable HTTP response</code></pre>""",
"code_intro": "Two stages, deliberately: one paginated sweep of the alerts list to find the endpoints, then one fetch per sampled alert to see what came back, because <code>response_headers</code> exists nowhere else. The pure parts are the header normaliser, the cookie fault test and the verdict &mdash; including the state for a list row, which encodes the trap that this whole note is about.",
"py_file": "twilio_webhook_protocol_audit.py",
"py": '''"""Report webhook endpoints returning HTTP that Twilio cannot parse (11206).

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
log = logging.getLogger("twilio_webhook_protocol_audit")

MONITOR = "https://monitor.twilio.com/v1"

PROTOCOL_VIOLATION = 11206

# Alerts are retained 30 days.
MAX_DAYS = 30


def code_of(alert):
    """Read error_code off an alert as an integer, or None.

    The Monitor API returns this as a string, and comparing it raw against
    11206 finds nothing at all.
    """
    raw = alert.get("error_code")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def endpoint(url):
    """Host and path from a request URL, dropping the query string.

    Twilio appends its own parameters to the URL it fetches, so the query string
    differs on every alert and grouping on the whole URL would file each one
    under its own heading.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        return ""
    return host + (parts.path or "/")


def header_lines(response_headers):
    """Normalise a fetched alert's response_headers into "Name: value" lines.

    The field's shape is not worth betting on: it arrives as a newline-joined
    string on some alerts and as a mapping on others, and a mapping can hold a
    list where a header repeats. Accepting all three costs six lines and saves a
    parser that silently returns nothing.
    """
    h = response_headers
    if not h:
        return []
    if isinstance(h, str):
        return [ln.strip() for ln in h.replace("\\r\\n", "\\n").split("\\n") if ln.strip()]
    if isinstance(h, dict):
        out = []
        for name, value in h.items():
            values = value if isinstance(value, (list, tuple)) else [value]
            out.extend("%s: %s" % (name, v) for v in values)
        return out
    if isinstance(h, (list, tuple)):
        return [str(x) for x in h if str(x).strip()]
    return []


def header_values(lines, name):
    """Every value for one header name, matched case-insensitively. Pure."""
    want = name.lower()
    out = []
    for line in lines:
        head, sep, rest = line.partition(":")
        if sep and head.strip().lower() == want:
            out.append(rest.strip())
    return out


def cookie_faults(value):
    """What is wrong with one Set-Cookie value. Pure, returns a sorted list.

    Both faults are emitted happily by most servers and refused by strict
    clients, which is the whole reason this failure reads as flakiness: it
    depends on the value, not on the code path.
    """
    faults = []
    raw = "" if value is None else str(value)
    if any(ord(c) < 0x20 or ord(c) == 0x7f for c in raw):
        faults.append("control-characters")
    pair = raw.split(";", 1)[0]
    if "=" not in pair or not pair.split("=", 1)[0].strip():
        faults.append("nameless")
    return sorted(faults)


def verdict(alert):
    """Classify one alert. Pure, so the two-stage read is testable offline.

    The first branch is the point of the note. A row from the alerts list has no
    response_headers key at all, and treating that absence as an empty header
    block would report every alert in the account as a scheme mismatch.

    Returns (state, detail).
    """
    if code_of(alert) != PROTOCOL_VIOLATION:
        return ("not-11206", "this alert is not an HTTP protocol violation")

    if "response_headers" not in alert:
        return ("unfetched",
                "this is a row from the alerts list. response_headers is "
                "populated only by GET /v1/Alerts/{Sid}, so nothing can be "
                "concluded until the alert is fetched on its own.")

    lines = header_lines(alert.get("response_headers"))
    cookies = header_values(lines, "set-cookie")
    broken = [(c, cookie_faults(c)) for c in cookies]
    broken = [(c, f) for c, f in broken if f]
    if broken:
        names = sorted({f for _c, faults in broken for f in faults})
        return ("malformed-cookie",
                "%d Set-Cookie value(s) a strict parser will refuse (%s). Most "
                "servers emit these without complaint, which is why your own "
                "logs show a clean 200." % (len(broken), ", ".join(names)))

    if not lines:
        return ("no-header-block",
                "the fetched alert carries no response headers, so the parse "
                "failed before a header block existed. The usual cause is a "
                "listener answering plain HTTP on a port the configured URL "
                "calls https.")

    return ("headers-parse",
            "%d header(s) read cleanly, so the violation is in the framing of "
            "the response itself: a truncated body, a Content-Length that does "
            "not match, or a chunked encoding that ended early." % len(lines))


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
    """One alert on its own. The only place response_headers exists."""
    return get(session, "%s/Alerts/%s" % (MONITOR, sid))


def group(alerts):
    """Bucket the 11206s by endpoint, keeping the sids to sample from. Pure."""
    out = {}
    for a in alerts:
        if code_of(a) != PROTOCOL_VIOLATION:
            continue
        key = endpoint(a.get("request_url"))
        row = out.setdefault(key, {"alerts": 0, "sids": [], "url": ""})
        row["alerts"] += 1
        row["sids"].append(a.get("sid"))
        row["url"] = row["url"] or (a.get("request_url") or "")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read alerts (Twilio keeps 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging alerts after this many")
    ap.add_argument("--sample", type=int, default=3,
                    help="alerts to fetch individually per endpoint; each one is "
                         "a request, and response_headers exists nowhere else")
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

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=days)).date().isoformat()

    alerts = list_alerts(session, since, args.max_alerts)
    rows = group(alerts)
    if not rows:
        log.info("no 11206 since %s across %d alert(s)", since, len(alerts))
        return 0

    log.info("%d endpoint(s) with 11206; fetching up to %d alert(s) each",
             len(rows), args.sample)

    bad = 0
    for key, row in sorted(rows.items()):
        bad += 1
        log.warning("%-17s %s  %d x 11206", "protocol-violation", key,
                    row["alerts"])
        log.warning("  sample %s", row["url"] or "(none)")
        for sid in row["sids"][:args.sample]:
            detailed = fetch_alert(session, sid)
            state, detail = verdict(detailed)
            log.warning("  %s %s  %s", sid, state, detail)
        log.warning("  repair: strip characters below 0x20 from cookie values "
                    "where they are set, drop cookies with an empty name, and "
                    "make the scheme in the configured URL match what the port "
                    "actually speaks.")

    log.info("%d endpoint(s) returning an unparseable HTTP response", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-webhook-protocol-audit.mjs",
"js": '''/**
 * Report webhook endpoints returning HTTP that Twilio cannot parse (11206).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';

const PROTOCOL_VIOLATION = 11206;

// Alerts are retained 30 days.
const MAX_DAYS = 30;

/** Read error_code off an alert as a number, or null. */
export function codeOf(alert) {
  const raw = alert.error_code;
  if (raw === null || raw === undefined || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Host and path from a request URL, dropping the query string. Twilio appends
 * its own parameters, so grouping on the whole URL files every alert separately.
 */
export function endpoint(url) {
  if (!url) return '';
  let u;
  try {
    u = new URL(String(url).trim());
  } catch {
    return '';
  }
  const host = u.hostname.toLowerCase();
  if (!host) return '';
  return host + (u.pathname || '/');
}

/**
 * Normalise a fetched alert's response_headers into "Name: value" lines. The
 * field arrives as a string on some alerts and as a mapping on others, and a
 * mapping can hold a list where a header repeats.
 */
export function headerLines(responseHeaders) {
  const h = responseHeaders;
  if (!h) return [];
  if (typeof h === 'string') {
    return h.replace(/\\r\\n/g, '\\n').split('\\n')
      .map((ln) => ln.trim()).filter(Boolean);
  }
  if (Array.isArray(h)) return h.map(String).filter((x) => x.trim());
  if (typeof h === 'object') {
    const out = [];
    for (const [name, value] of Object.entries(h)) {
      for (const v of (Array.isArray(value) ? value : [value])) out.push(`${name}: ${v}`);
    }
    return out;
  }
  return [];
}

/** Every value for one header name, matched case-insensitively. Pure. */
export function headerValues(lines, name) {
  const want = name.toLowerCase();
  const out = [];
  for (const line of lines) {
    const i = line.indexOf(':');
    if (i > -1 && line.slice(0, i).trim().toLowerCase() === want) {
      out.push(line.slice(i + 1).trim());
    }
  }
  return out;
}

/**
 * What is wrong with one Set-Cookie value. Pure, returns a sorted list. Both
 * faults are emitted happily by most servers and refused by strict clients.
 */
export function cookieFaults(value) {
  const faults = [];
  const raw = value === null || value === undefined ? '' : String(value);
  if ([...raw].some((c) => c.charCodeAt(0) < 0x20 || c.charCodeAt(0) === 0x7f)) {
    faults.push('control-characters');
  }
  const pair = raw.split(';')[0];
  if (!pair.includes('=') || !pair.split('=')[0].trim()) faults.push('nameless');
  return faults.sort();
}

/**
 * Classify one alert. Pure, so the two-stage read is testable offline. The
 * first branch is the point: a row from the list has no response_headers key,
 * and treating that absence as an empty header block would misreport everything.
 * Returns [state, detail].
 */
export function verdict(alert) {
  if (codeOf(alert) !== PROTOCOL_VIOLATION) {
    return ['not-11206', 'this alert is not an HTTP protocol violation'];
  }

  if (!Object.prototype.hasOwnProperty.call(alert, 'response_headers')) {
    return ['unfetched',
      'this is a row from the alerts list. response_headers is populated only ' +
      'by GET /v1/Alerts/{Sid}, so nothing can be concluded until the alert ' +
      'is fetched on its own.'];
  }

  const lines = headerLines(alert.response_headers);
  const broken = headerValues(lines, 'set-cookie')
    .map((c) => [c, cookieFaults(c)]).filter(([, f]) => f.length);
  if (broken.length) {
    const names = [...new Set(broken.flatMap(([, f]) => f))].sort();
    return ['malformed-cookie',
      `${broken.length} Set-Cookie value(s) a strict parser will refuse ` +
      `(${names.join(', ')}). Most servers emit these without complaint, ` +
      'which is why your own logs show a clean 200.'];
  }

  if (lines.length === 0) {
    return ['no-header-block',
      'the fetched alert carries no response headers, so the parse failed ' +
      'before a header block existed. The usual cause is a listener answering ' +
      'plain HTTP on a port the configured URL calls https.'];
  }

  return ['headers-parse',
    `${lines.length} header(s) read cleanly, so the violation is in the ` +
    'framing of the response itself: a truncated body, a Content-Length that ' +
    'does not match, or a chunked encoding that ended early.'];
}

/** Bucket the 11206s by endpoint, keeping the sids to sample from. Pure. */
export function group(alerts) {
  const out = new Map();
  for (const a of alerts) {
    if (codeOf(a) !== PROTOCOL_VIOLATION) continue;
    const key = endpoint(a.request_url);
    if (!out.has(key)) out.set(key, { alerts: 0, sids: [], url: '' });
    const row = out.get(key);
    row.alerts += 1;
    row.sids.push(a.sid);
    row.url = row.url || (a.request_url ?? '');
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

  const dayArg = process.argv.indexOf('--days');
  let days = dayArg > -1 ? Number(process.argv[dayArg + 1]) : 7;
  if (!Number.isFinite(days) || days < 1) days = 7;
  if (days > MAX_DAYS) {
    console.warn(`alerts are retained ${MAX_DAYS} days; reading ${MAX_DAYS}`);
    days = MAX_DAYS;
  }
  const sampleArg = process.argv.indexOf('--sample');
  const sample = sampleArg > -1 ? Number(process.argv[sampleArg + 1]) || 3 : 3;

  const since = new Date(Date.now() - days * 86400_000).toISOString().slice(0, 10);

  const alerts = await listAlerts(auth, since);
  const rows = group(alerts);
  if (rows.size === 0) {
    console.log(`no 11206 since ${since} across ${alerts.length} alert(s)`);
    return;
  }

  console.log(`${rows.size} endpoint(s) with 11206; fetching up to ${sample} each`);

  let bad = 0;
  for (const key of [...rows.keys()].sort()) {
    const row = rows.get(key);
    bad += 1;
    console.warn(`${'protocol-violation'.padEnd(17)} ${key}  ${row.alerts} x 11206`);
    console.warn(`  sample ${row.url || '(none)'}`);
    for (const sid of row.sids.slice(0, sample)) {
      const detailed = await get(auth, `${MONITOR}/Alerts/${sid}`);
      const [state, detail] = verdict(detailed);
      console.warn(`  ${sid} ${state}  ${detail}`);
    }
    console.warn('  repair: strip characters below 0x20 from cookie values ' +
      'where they are set, drop cookies with an empty name, and make the ' +
      'scheme in the configured URL match what the port actually speaks.');
  }

  console.log(`${bad} endpoint(s) returning an unparseable HTTP response`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first case is the one that matters most: an alert straight out of the list has no <code>response_headers</code> key, and a classifier that reads that absence as an empty header block will confidently report every 11206 on the account as a scheme mismatch. The rest pin the two cookie faults, including a value that looks fine until you count the characters, and the case where a clean header block moves the diagnosis into the body framing.",
"test_py_file": "test_twilio_webhook_protocol_audit.py",
"test_py": '''from twilio_webhook_protocol_audit import (
    cookie_faults, endpoint, group, header_lines, header_values, verdict)


def listed(sid="NO1", url="https://hooks.example.com/voice?AccountSid=AC1"):
    """A row exactly as the alerts list returns it: no response_headers key."""
    return {"sid": sid, "request_url": url, "error_code": "11206",
            "date_generated": "2026-05-05T14:08:00Z"}


def fetched(headers):
    d = listed()
    d["response_headers"] = headers
    return d


def test_a_list_row_is_reported_as_unfetched_not_as_an_empty_header_block():
    # The whole trap of this note. response_headers exists only on the
    # single-alert fetch, and absence is not emptiness.
    state, detail = verdict(listed())
    assert state == "unfetched"
    assert "/v1/Alerts/" in detail


def test_endpoint_drops_the_query_twilio_appends():
    assert endpoint("https://Hooks.Example.com/voice?AccountSid=AC1") == \\
        "hooks.example.com/voice"
    assert endpoint("https://hooks.example.com") == "hooks.example.com/"
    assert endpoint("") == ""


def test_header_lines_accepts_a_string_a_mapping_and_a_repeat():
    assert header_lines("Content-Type: text/xml\\r\\nServer: nginx") == \\
        ["Content-Type: text/xml", "Server: nginx"]
    assert header_lines({"Set-Cookie": ["a=1", "b=2"]}) == \\
        ["Set-Cookie: a=1", "Set-Cookie: b=2"]
    assert header_lines(None) == []


def test_header_values_matches_case_insensitively():
    lines = ["set-cookie: a=1", "Set-Cookie: b=2", "Server: nginx"]
    assert header_values(lines, "Set-Cookie") == ["a=1", "b=2"]


def test_cookie_faults_finds_a_control_character_and_an_empty_name():
    assert cookie_faults("sid=abc123; Path=/") == []
    assert cookie_faults("sid=ab\\ncd; Path=/") == ["control-characters"]
    assert cookie_faults("=abc123; Path=/") == ["nameless"]
    assert cookie_faults("=ab\\tcd") == ["control-characters", "nameless"]


def test_a_malformed_cookie_is_named_in_the_verdict():
    state, detail = verdict(fetched({"Set-Cookie": ["ok=1", "=orphan"]}))
    assert state == "malformed-cookie"
    assert "nameless" in detail


def test_an_empty_header_block_on_a_fetched_alert_is_a_scheme_mismatch():
    state, detail = verdict(fetched(""))
    assert state == "no-header-block"
    assert "plain HTTP" in detail


def test_clean_headers_move_the_diagnosis_into_the_body_framing():
    state, detail = verdict(fetched("Content-Type: text/xml\\nSet-Cookie: sid=1"))
    assert state == "headers-parse"
    assert "Content-Length" in detail


def test_another_error_code_is_not_this_failure():
    other = fetched("Content-Type: text/xml")
    other["error_code"] = "11200"
    assert verdict(other)[0] == "not-11206"


def test_group_buckets_by_endpoint_and_keeps_the_sids():
    rows = group([listed("A1"), listed("A2"),
                  listed("A3", "https://hooks.example.com/sms?x=1")])
    assert sorted(rows) == ["hooks.example.com/sms", "hooks.example.com/voice"]
    assert rows["hooks.example.com/voice"]["sids"] == ["A1", "A2"]
''',
"test_js_file": "twilio-webhook-protocol-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  cookieFaults, endpoint, group, headerLines, headerValues, verdict,
} from './twilio-webhook-protocol-audit.mjs';

// A row exactly as the alerts list returns it: no response_headers key.
const listed = (sid = 'NO1', url = 'https://hooks.example.com/voice?AccountSid=AC1') => ({
  sid, request_url: url, error_code: '11206', date_generated: '2026-05-05T14:08:00Z',
});

const fetched = (headers) => ({ ...listed(), response_headers: headers });

test('a list row is reported as unfetched not as an empty header block', () => {
  const [state, detail] = verdict(listed());
  assert.equal(state, 'unfetched');
  assert.match(detail, /\\/v1\\/Alerts\\//);
});

test('endpoint drops the query Twilio appends', () => {
  assert.equal(endpoint('https://Hooks.Example.com/voice?AccountSid=AC1'),
    'hooks.example.com/voice');
  assert.equal(endpoint('https://hooks.example.com'), 'hooks.example.com/');
  assert.equal(endpoint(''), '');
});

test('headerLines accepts a string, a mapping and a repeat', () => {
  assert.deepEqual(headerLines('Content-Type: text/xml\\r\\nServer: nginx'),
    ['Content-Type: text/xml', 'Server: nginx']);
  assert.deepEqual(headerLines({ 'Set-Cookie': ['a=1', 'b=2'] }),
    ['Set-Cookie: a=1', 'Set-Cookie: b=2']);
  assert.deepEqual(headerLines(null), []);
});

test('headerValues matches case insensitively', () => {
  const lines = ['set-cookie: a=1', 'Set-Cookie: b=2', 'Server: nginx'];
  assert.deepEqual(headerValues(lines, 'Set-Cookie'), ['a=1', 'b=2']);
});

test('cookieFaults finds a control character and an empty name', () => {
  assert.deepEqual(cookieFaults('sid=abc123; Path=/'), []);
  assert.deepEqual(cookieFaults('sid=ab\\ncd; Path=/'), ['control-characters']);
  assert.deepEqual(cookieFaults('=abc123; Path=/'), ['nameless']);
  assert.deepEqual(cookieFaults('=ab\\tcd'), ['control-characters', 'nameless']);
});

test('a malformed cookie is named in the verdict', () => {
  const [state, detail] = verdict(fetched({ 'Set-Cookie': ['ok=1', '=orphan'] }));
  assert.equal(state, 'malformed-cookie');
  assert.match(detail, /nameless/);
});

test('an empty header block on a fetched alert is a scheme mismatch', () => {
  const [state, detail] = verdict(fetched(''));
  assert.equal(state, 'no-header-block');
  assert.match(detail, /plain HTTP/);
});

test('clean headers move the diagnosis into the body framing', () => {
  const [state, detail] = verdict(fetched('Content-Type: text/xml\\nSet-Cookie: sid=1'));
  assert.equal(state, 'headers-parse');
  assert.match(detail, /Content-Length/);
});

test('another error code is not this failure', () => {
  const other = fetched('Content-Type: text/xml');
  other.error_code = '11200';
  assert.equal(verdict(other)[0], 'not-11206');
});

test('group buckets by endpoint and keeps the sids', () => {
  const rows = group([listed('A1'), listed('A2'),
    listed('A3', 'https://hooks.example.com/sms?x=1')]);
  assert.deepEqual([...rows.keys()].sort(),
    ['hooks.example.com/sms', 'hooks.example.com/voice']);
  assert.deepEqual(rows.get('hooks.example.com/voice').sids, ['A1', 'A2']);
});
''',
"faq": [
 ("My server logged a 200. How can this be a protocol violation?",
  "Because 11206 is not about the status code. Your framework wrote a status line and headers, your web server framed them, and the result was not parseable by a strict HTTP client. Everything inside your process succeeded, which is exactly why no log of yours records the failure."),
 ("Why does the script fetch alerts one at a time?",
  "Because response_headers and response_body appear only on GET /v1/Alerts/{Sid}. Every row of the list carries the code, the URL and the timestamp and nothing about what came back, so seeing the malformed header costs one request per alert. That is why it samples instead of fetching thousands."),
 ("What is actually wrong with the cookie?",
  "One of two things. Its value contains a raw control character - a newline, a carriage return, a tab - which is not permitted in a header value and is how header injection works, so strict clients refuse rather than repair it. Or the cookie has no name at all, which is what a Set-Cookie beginning with an equals sign means."),
 ("How is this different from 12300 or 12100?",
  "Those are later checks. 12300 means the HTTP parsed and the Content-Type was wrong for TwiML; 12100 means the Content-Type was right and the XML was not well-formed. An 11206 means the failure happened before either check could run, at the HTTP layer itself."),
 ("The alert has no response headers at all. What does that mean?",
  "That Twilio abandoned the parse before a header block existed, which usually means the first bytes back were not a status line. The classic cause is a listener speaking plain HTTP on a port the configured URL declares as https, so make the scheme match what the port actually serves."),
],
"related": [
 ("/twilio/webhook-invalid-content-type-12300/", "The next check along: the wrong Content-Type"),
 ("/twilio/twiml-document-parse-failure-12100/", "TwiML that is not well-formed XML"),
 ("/twilio/status-callback-webhook-failing-11200/", "A response Twilio read and disliked"),
],
"citations": [CITE_11206, CITE_ALERTS, CITE_WEBHOOKS, CITE_KEYS],
},

{
"slug": "phone-number-insecure-or-unreachable-webhook-url",
"title": "Number webhooks on http, a private address or a dev tunnel",
"description": "Three faults in one field: cleartext signatures, an address Twilio can never reach, and a tunnel that dies with the laptop. All visible in configuration.",
"h1": "number webhooks on http, a private address or a dev tunnel",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio webhook http not https", "twilio webhook localhost",
             "twilio ngrok url in production", "twilio webhook private ip",
             "twilio x-twilio-signature cleartext"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody wired a number to <code>http://</code> eighteen months ago and it has worked ever since, which is the problem. Somebody else pointed one at the ngrok URL from their laptop to test an idea on a Friday. A third pointed one at <code>10.0.4.31</code>, copied from a staging config. Nothing about any of these appears in the Debugger until the day it breaks, and the first one never will.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code> and <code>GET /2010-04-01/Accounts/{AccountSid}/Applications.json?PageSize=1000</code>, and check every URL field on both: <code>voice_url</code>, <code>sms_url</code>, both fallbacks and the status callbacks.</p>
<p>Flag three shapes. Scheme <code>http:</code> means the request body and the <code>X-Twilio-Signature</code> header cross the internet in cleartext. A host in <code>127.0.0.0/8</code>, <code>10.0.0.0/8</code>, <code>192.168.0.0/16</code>, <code>172.16.0.0/12</code> or <code>169.254.0.0/16</code> is unreachable from Twilio and produces <code>11205</code> or <code>11210</code> forever. And a host under <code>ngrok</code>, <code>trycloudflare</code>, <code>loca.lt</code>, <code>serveo</code> or <code>localtunnel</code> is a dev tunnel with a battery life.</p>""",
"problem": """<p>Every other webhook note in this section starts from an alert, which means it starts after something broke. This one does not, because two of these three faults break loudly and one never breaks at all. A number on <code>http://</code> works perfectly. The webhook is delivered, the signature header is present, your validator verifies it, and the whole exchange &mdash; including the phone numbers, the message bodies, and the signature that authenticates them &mdash; is readable by anything on the path.</p>
<p>The other two are the same mistake at different speeds. A private address never worked from Twilio and never will, so the number has been dead since the day it was configured; if it is a fallback URL, nobody has noticed because fallbacks are only used on the worst day. A tunnel host worked brilliantly for an afternoon and then stopped when a laptop lid closed, and the URL is still sitting in the field, looking like a real hostname to anyone reading the console.</p>""",
"why": """<p><strong>The signature does not protect the payload from being read.</strong> <code>X-Twilio-Signature</code> is an HMAC that proves the request came from Twilio and was not altered. It is not encryption. Over <code>http://</code>, the caller's number, the message body and the signature itself are all in clear on the wire, and the signature is replayable by anyone who captured it.</p>
<p><strong>A private address is not a firewall problem.</strong> Twilio dials from its own network toward the public internet. <code>10.0.4.31</code> resolves to nothing it can route to, and no allowlist, security group or WAF rule changes that. The near miss is worth knowing: <code>172.31.255.255</code> is private and <code>172.32.0.1</code> is not, and a range check written by eye usually gets that boundary wrong in one direction or the other.</p>
<p><strong>Tunnel URLs are indistinguishable from real ones in the console.</strong> They are HTTPS, they have a plausible hostname, and while the tunnel is up they answer correctly. What they do not have is a life expectancy beyond the session that created them, so this is a configuration that works during the demo and is dead by Monday with no deploy to blame.</p>
<p><strong>An Application SID moves the URLs somewhere the number does not show them.</strong> When <code>voice_application_sid</code> is set it wins, and the number's own <code>voice_url</code> is ignored entirely. An audit that reads only <code>IncomingPhoneNumbers</code> will clear a number whose effective handler is a tunnel URL parked on a TwiML App, so the Applications list has to be read too. The <a href="/twilio/number-conflicting-url-and-application-sid/">precedence note</a> covers what that override does on its own.</p>""",
"steps": [
 {"h": "Page both resources, not just the numbers",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code> following <code>next_page_uri</code>, then the same over <code>Applications.json</code>. On this API <code>next_page_uri</code> is a path, so join it to <code>https://api.twilio.com</code> rather than requesting it as-is.</p>"""},
 {"h": "Check every URL field, including the fallbacks",
  "body": """<p>A fallback on <code>http://</code> is the same exposure as a primary, and a fallback pointed at a private address is a safety net with a hole in it that nobody will discover until the primary fails. Status callbacks carry message and call metadata and belong in the same sweep.</p>"""},
 {"h": "Classify the host before the scheme",
  "body": """<p>A URL can be several things at once, and <code>http://localhost:3000/voice</code> is both cleartext and unroutable. Report the unreachable finding for it: the exposure is theoretical on a host Twilio can never connect to, while the outage is happening now.</p>"""},
 {"h": "Rank the findings so the report is a work queue",
  "body": """<p>Unreachable first, because those requests are failing today. Cleartext second, because it is working and leaking. Tunnel third, because it is working and counting down. A report that lists forty numbers in the order the API returned them gets read once.</p>"""},
 {"h": "Repoint to a public HTTPS hostname, then re-run",
  "body": """<p>The repair is the same shape in all three cases: a real hostname on <code>https</code>, set on the object that actually wins &mdash; the number, or the Application when one is attached. Keep the audit on a schedule, because the next tunnel URL will be pasted in by somebody who only needed it for an afternoon.</p>"""},
],
"verify": """<p>Re-run the script. Every URL field on every number and every app should classify as <code>ok</code>.</p>
<pre><code class="language-bash">python3 twilio_webhook_url_audit.py
# 12 number(s), 3 app(s), 0 with an insecure or unreachable webhook URL</code></pre>""",
"code_intro": "Two paginated GETs and no alerts at all, because this note is about finding the fault before it becomes an incident. The classifier is one pure function over a single URL string, plus a ranking function that decides which of several findings on one object leads the line &mdash; and the ranking is a judgement about urgency, so it is written where a test can argue with it.",
"py_file": "twilio_webhook_url_audit.py",
"py": '''"""Report Twilio webhook URLs that are cleartext, unroutable, or a dev tunnel.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_webhook_url_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# Every field on a number that can hold a URL Twilio will fetch or notify.
NUMBER_URL_FIELDS = ("voice_url", "voice_fallback_url", "sms_url",
                     "sms_fallback_url", "status_callback")

# The same idea on a TwiML App, which wins outright when its SID is set on a
# number, so a number-only audit clears endpoints it never looked at.
APP_URL_FIELDS = ("voice_url", "voice_fallback_url", "sms_url",
                  "sms_fallback_url", "status_callback", "sms_status_callback")

# Substrings, not exact hosts. These services move between apex domains often
# enough that pinning the full name dates the check within a year.
TUNNEL_MARKERS = ("ngrok", "trycloudflare", "loca.lt", "serveo", "localtunnel")

# Urgency, worst first. Unreachable is failing now; cleartext is working and
# leaking; a tunnel is working and counting down. The order is the report.
SEVERITY = ("unreachable", "cleartext", "tunnel", "unreadable", "unset", "ok")


def is_private_host(host):
    """True for a host Twilio cannot route to from the public internet. Pure.

    The boundary worth getting right is 172.16.0.0/12: 172.31.x.x is private
    and 172.32.x.x is not, and a check written by eye usually places that edge
    one octet away from where it belongs.
    """
    h = str(host or "").strip().lower()
    if not h:
        return False
    if h in ("localhost", "localhost.localdomain") or h.endswith(".localhost"):
        return True
    if h in ("::1", "0:0:0:0:0:0:0:1"):
        return True
    parts = h.split(".")
    if len(parts) != 4 or not all(p.isdigit() and len(p) <= 3 for p in parts):
        return False
    octets = [int(p) for p in parts]
    if any(o > 255 for o in octets):
        return False
    a, b = octets[0], octets[1]
    return (a == 10 or a == 127 or a == 0
            or (a == 172 and 16 <= b <= 31)
            or (a == 192 and b == 168)
            or (a == 169 and b == 254))


def classify_url(url):
    """Classify one configured webhook URL. Pure. Returns (state, detail).

    Host before scheme, deliberately. http://localhost:3000/voice is both
    cleartext and unroutable, and only one of those is costing anything today:
    the exposure is theoretical on an endpoint Twilio can never connect to.
    """
    raw = str(url or "").strip()
    if not raw:
        return ("unset", "no URL configured on this field")

    parts = urlsplit(raw)
    scheme = (parts.scheme or "").lower()
    host = (parts.hostname or "").lower()
    if not host or scheme not in ("http", "https"):
        return ("unreadable",
                "not an absolute http or https URL, so Twilio has nothing to "
                "fetch: %r" % raw[:80])

    if is_private_host(host):
        return ("unreachable",
                "%s is a loopback or private address. Twilio dials from the "
                "public internet, so no firewall or allowlist change makes this "
                "reachable: every request raises 11205 or 11210." % host)

    if any(m in host for m in TUNNEL_MARKERS):
        return ("tunnel",
                "%s is a development tunnel. It answers correctly while the "
                "session that created it is alive and stops the moment that "
                "laptop sleeps, with no deploy to blame." % host)

    if scheme == "http":
        return ("cleartext",
                "http means the request body and the X-Twilio-Signature header "
                "cross the internet in clear. The signature proves origin, it "
                "does not encrypt: the caller number, the message body and the "
                "signature itself are all readable on the path.")

    return ("ok", "https on a public hostname")


def audit(resource, fields):
    """Classify every URL field on one number or app. Pure.

    Returns a list of (field, state, detail), with the healthy and unset fields
    kept in: the caller decides what to print, and dropping them here would make
    it impossible to say that an object was checked and was fine.
    """
    return [(f,) + classify_url(resource.get(f)) for f in fields]


def worst(findings):
    """The most urgent state among a resource's fields. Pure.

    A number can be cleartext on one field and unreachable on another, and the
    line it gets in the report should lead with the one that is failing now.
    """
    states = {state for _f, state, _d in findings}
    for state in SEVERITY:
        if state in states:
            return state
    return "ok"


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page_all(session, path, key, limit):
    """Page a 2010-04-01 list. next_page_uri here is a path, not a full URL."""
    url = BASE + path
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def report(label, resource, fields, sid_field="sid"):
    """Print one object's findings. Returns 1 when anything needed flagging."""
    findings = audit(resource, fields)
    state = worst(findings)
    if state in ("ok", "unset"):
        log.info("%-12s %s  every URL field is https on a public hostname",
                 state, label)
        return 0
    log.warning("%-12s %s", state, label)
    for field, fstate, detail in findings:
        if fstate in ("ok", "unset"):
            continue
        log.warning("  %s: %s  %s", field, fstate, detail)
    log.warning("  repair: set the field to https://{public-host}/... on %s %s. "
                "When an Application SID is attached to a number, the app's "
                "URLs are the ones that win.",
                "app" if sid_field == "app" else "number",
                resource.get("sid") or "?")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000,
                    help="stop after this many phone numbers")
    ap.add_argument("--max-apps", type=int, default=1000,
                    help="stop after this many TwiML applications")
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

    numbers = page_all(session, "/Accounts/%s/IncomingPhoneNumbers.json" % account,
                       "incoming_phone_numbers", args.max_numbers)
    apps = page_all(session, "/Accounts/%s/Applications.json" % account,
                    "applications", args.max_apps)

    bad = 0
    for n in numbers:
        label = n.get("phone_number") or n.get("sid") or "?"
        bad += report(label, n, NUMBER_URL_FIELDS)
    for a in apps:
        label = "%s %s" % (a.get("sid") or "?", a.get("friendly_name") or "(unnamed)")
        bad += report(label, a, APP_URL_FIELDS, sid_field="app")

    log.info("%d number(s), %d app(s), %d with an insecure or unreachable "
             "webhook URL", len(numbers), len(apps), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-webhook-url-audit.mjs",
"js": '''/**
 * Report Twilio webhook URLs that are cleartext, unroutable, or a dev tunnel.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// Every field on a number that can hold a URL Twilio will fetch or notify.
const NUMBER_URL_FIELDS = ['voice_url', 'voice_fallback_url', 'sms_url',
  'sms_fallback_url', 'status_callback'];

// The same on a TwiML App, whose URLs win outright when its SID is on a number.
const APP_URL_FIELDS = ['voice_url', 'voice_fallback_url', 'sms_url',
  'sms_fallback_url', 'status_callback', 'sms_status_callback'];

// Substrings, not exact hosts: these services change apex domains often enough
// that pinning the full name dates the check within a year.
const TUNNEL_MARKERS = ['ngrok', 'trycloudflare', 'loca.lt', 'serveo', 'localtunnel'];

// Urgency, worst first. Unreachable is failing now; cleartext is working and
// leaking; a tunnel is working and counting down.
const SEVERITY = ['unreachable', 'cleartext', 'tunnel', 'unreadable', 'unset', 'ok'];

/**
 * True for a host Twilio cannot route to from the public internet. Pure. The
 * boundary worth getting right is 172.16.0.0/12: 172.31 is private, 172.32 is
 * not, and a range written by eye usually misplaces that edge.
 */
export function isPrivateHost(host) {
  const h = String(host ?? '').trim().toLowerCase();
  if (!h) return false;
  if (h === 'localhost' || h === 'localhost.localdomain' || h.endsWith('.localhost')) {
    return true;
  }
  if (h === '::1' || h === '0:0:0:0:0:0:0:1') return true;
  const parts = h.split('.');
  if (parts.length !== 4 || !parts.every((p) => /^[0-9]{1,3}$/.test(p))) return false;
  const o = parts.map(Number);
  if (o.some((x) => x > 255)) return false;
  const [a, b] = o;
  return (a === 10 || a === 127 || a === 0
    || (a === 172 && b >= 16 && b <= 31)
    || (a === 192 && b === 168)
    || (a === 169 && b === 254));
}

/**
 * Classify one configured webhook URL. Pure. Returns [state, detail].
 * Host before scheme: http://localhost:3000/voice is both cleartext and
 * unroutable, and only the outage is costing anything today.
 */
export function classifyUrl(url) {
  const raw = String(url ?? '').trim();
  if (!raw) return ['unset', 'no URL configured on this field'];

  let u;
  try {
    u = new URL(raw);
  } catch {
    return ['unreadable',
      'not an absolute http or https URL, so Twilio has nothing to fetch: ' +
      raw.slice(0, 80)];
  }
  const scheme = u.protocol.replace(':', '').toLowerCase();
  const host = u.hostname.toLowerCase();
  if (!host || (scheme !== 'http' && scheme !== 'https')) {
    return ['unreadable',
      'not an absolute http or https URL, so Twilio has nothing to fetch: ' +
      raw.slice(0, 80)];
  }

  if (isPrivateHost(host)) {
    return ['unreachable',
      `${host} is a loopback or private address. Twilio dials from the public ` +
      'internet, so no firewall or allowlist change makes this reachable: ' +
      'every request raises 11205 or 11210.'];
  }

  if (TUNNEL_MARKERS.some((m) => host.includes(m))) {
    return ['tunnel',
      `${host} is a development tunnel. It answers correctly while the session ` +
      'that created it is alive and stops the moment that laptop sleeps, with ' +
      'no deploy to blame.'];
  }

  if (scheme === 'http') {
    return ['cleartext',
      'http means the request body and the X-Twilio-Signature header cross the ' +
      'internet in clear. The signature proves origin, it does not encrypt: ' +
      'the caller number, the message body and the signature itself are all ' +
      'readable on the path.'];
  }

  return ['ok', 'https on a public hostname'];
}

/**
 * Classify every URL field on one number or app. Pure. Healthy and unset fields
 * stay in, so a caller can still say an object was checked and was fine.
 */
export function audit(resource, fields) {
  return fields.map((f) => [f, ...classifyUrl(resource[f])]);
}

/** The most urgent state among a resource's fields. Pure. */
export function worst(findings) {
  const states = new Set(findings.map(([, state]) => state));
  for (const state of SEVERITY) if (states.has(state)) return state;
  return 'ok';
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

export async function pageAll(auth, path, key, limit = 1000) {
  let url = BASE + path;
  let params = { PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page[key] ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

function report(label, resource, fields, kind) {
  const findings = audit(resource, fields);
  const state = worst(findings);
  if (state === 'ok' || state === 'unset') {
    console.log(`${state.padEnd(12)} ${label}  every URL field is https on a public hostname`);
    return 0;
  }
  console.warn(`${state.padEnd(12)} ${label}`);
  for (const [field, fstate, detail] of findings) {
    if (fstate === 'ok' || fstate === 'unset') continue;
    console.warn(`  ${field}: ${fstate}  ${detail}`);
  }
  console.warn(`  repair: set the field to https://{public-host}/... on ${kind} ` +
    `${resource.sid ?? '?'}. When an Application SID is attached to a number, ` +
    "the app's URLs are the ones that win.");
  return 1;
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

  const numbers = await pageAll(auth, `/Accounts/${account}/IncomingPhoneNumbers.json`,
    'incoming_phone_numbers');
  const apps = await pageAll(auth, `/Accounts/${account}/Applications.json`,
    'applications');

  let bad = 0;
  for (const n of numbers) {
    bad += report(n.phone_number ?? n.sid ?? '?', n, NUMBER_URL_FIELDS, 'number');
  }
  for (const a of apps) {
    bad += report(`${a.sid ?? '?'} ${a.friendly_name ?? '(unnamed)'}`, a,
      APP_URL_FIELDS, 'app');
  }

  console.log(`${numbers.length} number(s), ${apps.length} app(s), ${bad} with ` +
    'an insecure or unreachable webhook URL');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth freezing here. The private range boundary, because <code>172.31.255.255</code> and <code>172.32.0.1</code> look identical at a glance and only one of them is unroutable, and a check that gets it wrong either clears a dead number or condemns a live one. And the precedence between findings, because a URL that is both cleartext and unreachable has to be reported as the outage it is rather than the exposure it theoretically also is.",
"test_py_file": "test_twilio_webhook_url_audit.py",
"test_py": '''from twilio_webhook_url_audit import (
    NUMBER_URL_FIELDS, audit, classify_url, is_private_host, worst)


def test_https_on_a_public_host_is_ok():
    state, detail = classify_url("https://hooks.example.com/voice")
    assert state == "ok"
    assert "public hostname" in detail


def test_http_is_reported_as_a_cleartext_signature():
    state, detail = classify_url("http://hooks.example.com/voice")
    assert state == "cleartext"
    assert "X-Twilio-Signature" in detail


def test_private_and_loopback_hosts_are_unreachable():
    for url in ("https://localhost:3000/voice", "https://127.0.0.1/voice",
                "https://10.0.4.31/sms", "https://192.168.1.20/sms",
                "https://172.16.0.9/sms", "https://169.254.169.254/voice"):
        assert classify_url(url)[0] == "unreachable", url


def test_the_172_boundary_is_where_the_rfc_puts_it():
    # 172.31 is private and 172.32 is not. A check that slides this edge either
    # clears a number that has never worked or condemns one that does.
    assert is_private_host("172.31.255.255") is True
    assert is_private_host("172.32.0.1") is False
    assert is_private_host("172.15.0.1") is False


def test_tunnel_hosts_are_their_own_finding():
    for url in ("https://ab12cd.ngrok.io/voice",
                "https://tall-cat-runs.trycloudflare.com/sms",
                "https://demo.loca.lt/voice"):
        state, detail = classify_url(url)
        assert state == "tunnel", url
        assert "laptop sleeps" in detail


def test_an_unreachable_host_over_http_leads_with_the_outage():
    # Both faults are present. Only one of them is costing anything today.
    assert classify_url("http://localhost:3000/voice")[0] == "unreachable"


def test_a_blank_field_is_unset_and_a_relative_path_is_unreadable():
    assert classify_url("")[0] == "unset"
    assert classify_url(None)[0] == "unset"
    assert classify_url("/voice")[0] == "unreadable"
    assert classify_url("ftp://hooks.example.com/voice")[0] == "unreadable"


def test_worst_ranks_the_outage_above_the_exposure():
    number = {"voice_url": "http://hooks.example.com/voice",
              "sms_url": "https://10.0.4.31/sms",
              "voice_fallback_url": "https://hooks.example.com/fallback"}
    findings = audit(number, NUMBER_URL_FIELDS)
    assert worst(findings) == "unreachable"
    assert ("voice_url", "cleartext") == findings[0][:2]


def test_a_fully_healthy_number_reports_ok():
    number = {"voice_url": "https://hooks.example.com/voice",
              "sms_url": "https://hooks.example.com/sms"}
    assert worst(audit(number, NUMBER_URL_FIELDS)) == "unset"
''',
"test_js_file": "twilio-webhook-url-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  audit, classifyUrl, isPrivateHost, worst,
} from './twilio-webhook-url-audit.mjs';

const NUMBER_URL_FIELDS = ['voice_url', 'voice_fallback_url', 'sms_url',
  'sms_fallback_url', 'status_callback'];

test('https on a public host is ok', () => {
  const [state, detail] = classifyUrl('https://hooks.example.com/voice');
  assert.equal(state, 'ok');
  assert.match(detail, /public hostname/);
});

test('http is reported as a cleartext signature', () => {
  const [state, detail] = classifyUrl('http://hooks.example.com/voice');
  assert.equal(state, 'cleartext');
  assert.match(detail, /X-Twilio-Signature/);
});

test('private and loopback hosts are unreachable', () => {
  for (const url of ['https://localhost:3000/voice', 'https://127.0.0.1/voice',
    'https://10.0.4.31/sms', 'https://192.168.1.20/sms',
    'https://172.16.0.9/sms', 'https://169.254.169.254/voice']) {
    assert.equal(classifyUrl(url)[0], 'unreachable', url);
  }
});

test('the 172 boundary is where the RFC puts it', () => {
  assert.equal(isPrivateHost('172.31.255.255'), true);
  assert.equal(isPrivateHost('172.32.0.1'), false);
  assert.equal(isPrivateHost('172.15.0.1'), false);
});

test('tunnel hosts are their own finding', () => {
  for (const url of ['https://ab12cd.ngrok.io/voice',
    'https://tall-cat-runs.trycloudflare.com/sms',
    'https://demo.loca.lt/voice']) {
    const [state, detail] = classifyUrl(url);
    assert.equal(state, 'tunnel', url);
    assert.match(detail, /laptop sleeps/);
  }
});

test('an unreachable host over http leads with the outage', () => {
  assert.equal(classifyUrl('http://localhost:3000/voice')[0], 'unreachable');
});

test('a blank field is unset and a relative path is unreadable', () => {
  assert.equal(classifyUrl('')[0], 'unset');
  assert.equal(classifyUrl(null)[0], 'unset');
  assert.equal(classifyUrl('/voice')[0], 'unreadable');
  assert.equal(classifyUrl('ftp://hooks.example.com/voice')[0], 'unreadable');
});

test('worst ranks the outage above the exposure', () => {
  const number = {
    voice_url: 'http://hooks.example.com/voice',
    sms_url: 'https://10.0.4.31/sms',
    voice_fallback_url: 'https://hooks.example.com/fallback',
  };
  const findings = audit(number, NUMBER_URL_FIELDS);
  assert.equal(worst(findings), 'unreachable');
  assert.deepEqual(findings[0].slice(0, 2), ['voice_url', 'cleartext']);
});

test('a fully healthy number reports unset for the fields it does not set', () => {
  const number = {
    voice_url: 'https://hooks.example.com/voice',
    sms_url: 'https://hooks.example.com/sms',
  };
  assert.equal(worst(audit(number, NUMBER_URL_FIELDS)), 'unset');
});
''',
"faq": [
 ("The signature is on the request. Why does http matter?",
  "Because a signature is not encryption. X-Twilio-Signature proves the request came from Twilio and was not altered; it does nothing to hide the contents. Over http the caller's number, the message body and the signature itself are readable by anything on the path, and a captured signature can be replayed against the same URL."),
 ("Can I allowlist Twilio's IP ranges so a private address works?",
  "No. Twilio dials outward from its own network toward the public internet, and 10.0.4.31 is not something it can route to at all. No firewall rule, security group or WAF change alters that: the URL needs a publicly resolvable hostname."),
 ("Why flag a tunnel URL when it is HTTPS and working?",
  "Because it stops working when the session that created it ends, and there is no deploy or config change to blame it on afterwards. In the console it is indistinguishable from a real endpoint, which is exactly why it survives past the afternoon it was needed for."),
 ("Why does the script read the Applications list as well as the numbers?",
  "Because when voice_application_sid is set on a number the app's URLs win and the number's own are ignored. A number-only audit will pass a number whose effective handler is a tunnel URL parked on a TwiML App that nobody has opened in a year."),
 ("Is a fallback URL on http really worth reporting?",
  "Yes, on both counts. It is the same cleartext exposure as a primary, and it is the URL used on the day the primary is already failing - which is a bad day to discover that the safety net points at a private address or a dead tunnel."),
],
"related": [
 ("/twilio/webhook-connection-timeout-11205/", "What an unreachable URL looks like in the alerts"),
 ("/twilio/number-conflicting-url-and-application-sid/", "When the app's URLs win instead"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still answering with demo TwiML"),
],
"citations": [CITE_PN, CITE_APPS, CITE_SECURITY, CITE_11100],
},

]
