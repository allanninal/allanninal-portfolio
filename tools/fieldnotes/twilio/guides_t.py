#!/usr/bin/env python3
"""/twilio/ field notes, batch T — the writing.

Four SIP and carrier failures that all carry a real error code and are all
invisible to the place people look for them. 32009 is a registration that
lapsed or a username that never matched. 32011 is your own edge refusing or
ignoring Twilio. 32001 is a ceiling hit inside one second of a batch, which no
hourly average will ever show. 32017 is a terminating carrier refusing a number
Twilio was perfectly willing to present.

Read-only throughout. An API Key with read access, never the account auth
token, and every repair is printed for a human to run rather than performed.

The thing to carry between all four: several voice failures are logged at
LogLevel=warning rather than error, 32012 among them, so every Alerts sweep
here reads both levels and merges on the alert sid. A sweep filtered to error
alone reports a clean account while the calls keep failing.
"""

CITE_32009 = ("Error 32009: the user is not registered with the SIP Domain — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/32009")
CITE_32011 = ("Error 32011: error communicating with your SIP infrastructure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/32011")
CITE_32001 = ("Error 32001: SIP trunk CPS limit exceeded — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/32001")
CITE_32017 = ("Error 32017: carrier blocked the call due to the calling number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/32017")
CITE_SIP_DOMAIN = ("SIP Domain resource — Twilio Docs",
                   "https://www.twilio.com/docs/voice/sip/api/sip-domain-resource")
CITE_SIP_CRED = ("SIP Credential resource — Twilio Docs",
                 "https://www.twilio.com/docs/voice/sip/api/sip-credential-resource")
CITE_TWIML_SIP = ("TwiML Voice: &lt;Sip&gt; — Twilio Docs",
                  "https://www.twilio.com/docs/voice/twiml/sip")
CITE_ORIGINATION = ("OriginationUrl resource — Twilio Docs",
                    "https://www.twilio.com/docs/sip-trunking/api/origination-url-resource")
CITE_TRUNK = ("Trunk resource — Twilio Docs",
              "https://www.twilio.com/docs/sip-trunking/api/trunk-resource")
CITE_TRUNK_TROUBLE = ("Elastic SIP Trunking troubleshooting — Twilio Docs",
                      "https://www.twilio.com/docs/sip-trunking/troubleshooting")
CITE_CALL = ("Call resource — Twilio Docs",
             "https://www.twilio.com/docs/voice/api/call-resource")
CITE_ALERT = ("Alert resource (Monitor) — Twilio Docs",
              "https://www.twilio.com/docs/usage/monitor-alert")
CITE_CALLER_IDS = ("OutgoingCallerId resource — Twilio Docs",
                   "https://www.twilio.com/docs/voice/api/outgoing-caller-ids")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "sip-endpoint-not-registered-32009",
"title": "Dial fails with 32009 because the SIP endpoint is not there",
"description": "32009 means the user you dialled holds no registration on the domain. A dropped REGISTER refresh and a username that never matched look identical.",
"h1": "Dial fails with 32009 because the SIP endpoint is not there",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 32009", "sip user not registered twilio",
             "twilio dial sip domain not registered",
             "twilio sip_registration false", "twilio sip credential username"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "PSTN legs work. SIP legs fail. Same TwiML, same account, same day &mdash; the <code>&lt;Dial&gt;&lt;Number&gt;</code> connects and the <code>&lt;Dial&gt;&lt;Sip&gt;</code> beside it comes back <code>32009 The user you tried to dial is not registered with the corresponding SIP Domain</code>. The error names the endpoint, which reads like it is the endpoint's fault, and about half the time it is not: the softphone is sitting there registered under a username that differs from the one your TwiML asks for by a letter or a capital.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts</code> at <strong>both</strong> <code>LogLevel=error</code> and <code>LogLevel=warning</code> and keep <code>error_code</code> <code>32009</code>. Take each alert's <code>resource_sid</code> and read <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?ParentCallSid={CallSid}</code>: the child leg's <code>to</code> is the <code>sip:user@domain</code> that could not be routed to.</p>
<p>Then build the account's side of the comparison. <code>GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains.json</code> gives <code>domain_name</code> and <code>sip_registration</code>; <code>GET .../SIP/Domains/{DomainSid}/Auth/Registrations/CredentialListMappings.json</code> gives the credential lists that may register, and <code>GET .../SIP/CredentialLists/{CLSid}/Credentials.json</code> gives the usernames. A dialled user that is not in that set was never going to work; one that is in it was simply not registered at that moment.</p>""",
"problem": """<p>32009 is a runtime fact stated as a configuration complaint. Twilio looked for a live registration for <code>sip:user@domain</code>, found none, and said so. That single sentence covers a softphone that closed its laptop lid, a domain that never had registration enabled, a credential list that was mapped for calls but not for registrations, and a username typo in a TwiML template. All four produce the identical alert text, and only one of them is transient.</p>
<p>Which is why the ticket cycles. The endpoint owner checks their softphone, sees it registered, and says it works. The application owner sees a hard error naming that user, and says it does not. Both are looking at the truth. Nobody is looking at the two strings side by side, which is where the answer usually is, because a registration list and a TwiML template live in different systems and nothing in either one compares them.</p>""",
"why": """<p><strong>SIP usernames are compared exactly and people are not.</strong> A credential created as <code>Reception</code> and a <code>&lt;Sip&gt;</code> that dials <code>sip:reception@example.sip.twilio.com</code> are two different endpoints. Every human reading them will say they are the same, and every case-insensitive check you write will agree, which is how this one survives review.</p>
<p><strong>Registration is a separate switch from routing.</strong> <code>sip_registration</code> is a field on the domain, and a domain can accept inbound INVITEs from mapped credentials while refusing to let anything register. That domain works for one direction of traffic and fails every <code>&lt;Dial&gt;&lt;Sip&gt;</code> aimed at it, permanently, with no error until someone dials.</p>
<p><strong>Calls and registrations have separate credential mappings.</strong> The domain has an <code>Auth/Calls</code> mapping subresource and an <code>Auth/Registrations</code> one. Mapping a credential list to the first and not the second is a natural half-completion, and it produces a domain where the credentials exist, are correct, and cannot register.</p>
<p><strong>The failing leg is a child call.</strong> The parent call runs its TwiML and ends normally, so a dashboard counting parent call status sees nothing. The alert exists, the child leg exists, and joining the two is work that only happens if someone decides to do it.</p>""",
"steps": [
 {"h": "Sweep the Alerts API at both log levels",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, then the same request at <code>LogLevel=warning</code>, following <code>meta.next_page_url</code> &mdash; this API paginates with an absolute URL rather than the relative <code>next_page_uri</code> the 2010-04-01 API uses. Merge on <code>sid</code>. Alerts are retained 30 days, so asking for 90 gets you 30 under a misleading label.</p>"""},
 {"h": "Resolve each alert to the leg that actually failed",
  "body": """<p>The alert's <code>resource_sid</code> is the parent call. <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?ParentCallSid={CallSid}</code> lists its children, and the child whose <code>to</code> begins <code>sip:</code> is the one that was refused. Cache by parent SID: one bad template produces many alerts against few calls.</p>"""},
 {"h": "Build the registerable username set for each domain",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains.json</code> for <code>domain_name</code> and <code>sip_registration</code>, then per domain <code>GET .../Auth/Registrations/CredentialListMappings.json</code> for the credential list SIDs, then <code>GET .../SIP/CredentialLists/{CLSid}/Credentials.json</code> for the usernames. Read the <em>registrations</em> mapping, not the calls one; they are different subresources and a list mapped to only the second cannot register.</p>"""},
 {"h": "Compare the dialled user against that set exactly, then case-insensitively",
  "body": """<p>An exact hit means the credential is right and the endpoint was simply not registered when the call arrived, which is an operational problem at the endpoint. A hit only when you fold case is a configuration problem in your TwiML, and it is worth its own state because it is the one people argue about. No hit at all means the username was never going to register.</p>"""},
 {"h": "Fix the string or the endpoint, then re-run over a fresh window",
  "body": """<p>Correct the username in the <code>&lt;Sip&gt;</code> noun, or <code>POST /2010-04-01/Accounts/{AccountSid}/SIP/Domains/{DomainSid}.json</code> with <code>SipRegistration=true</code>, or map the credential list to <code>Auth/Registrations</code>. Then sweep again over a window that starts after the change; you cannot reproduce a lapsed registration on demand, so the count going to zero is the only evidence there is.</p>"""},
],
"verify": """<p>Re-run the sweep over a window that begins after the deploy. The 32009 count should be zero.</p>
<pre><code class="language-bash">python3 twilio_sip_registration_audit.py --days 7
# 0 alert(s) with error_code 32009 in the last 7 day(s)</code></pre>""",
"code_intro": "Two paginated alert sweeps, one cached child-call listing per failing call, and one pass over the SIP Domains with their registration credential lists. Every request is a GET and an API Key with read access is enough. Two pure functions hold the diagnosis: one splits a SIP URI into user and domain without lowercasing the user, and one decides which of five things a 32009 actually was. The first is where this check is usually got wrong, because a URI parser that normalises case destroys the evidence the second function needs.",
"py_file": "twilio_sip_registration_audit.py",
"py": '''"""Report Twilio 32009 alerts and say why each SIP endpoint was unreachable.

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
log = logging.getLogger("twilio_sip_registration_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

NOT_REGISTERED = 32009


def sip_target(uri):
    """Split a SIP URI into (user, domain).

    The domain is lowercased because SIP hostnames are case insensitive. The
    user is not, and that is the entire point of this function: a credential
    created as Reception and a Dial aimed at reception are different endpoints,
    and a parser that folds case throws away the only evidence that says so.

    Handles sip: and sips:, a display name in angle brackets, a port, and URI
    parameters. Returns ("", "") when there is nothing to split.
    """
    v = str(uri or "").strip()
    if "<" in v and ">" in v:
        v = v[v.index("<") + 1:v.index(">")].strip()
    low = v.lower()
    for scheme in ("sips:", "sip:"):
        if low.startswith(scheme):
            v = v[len(scheme):]
            break
    else:
        return ("", "")
    v = v.split(";", 1)[0].split("?", 1)[0]
    if "@" not in v:
        return ("", "")
    user, host = v.rsplit("@", 1)
    return (user.strip(), host.split(":", 1)[0].strip().lower())


def verdict(target, domains):
    """Explain one 32009. Pure, so the rules can be tested without a network.

    target is (user, domain) from sip_target. domains maps a lowercase
    domain_name to {"sip_registration": bool, "usernames": [...]}, assembled
    from the SIP Domains list and each domain's registration credential lists.

    Returns (state, detail).
    """
    user, host = target
    if not host:
        return ("unresolved",
                "no sip: destination on the failing leg, so the username cannot "
                "be compared against anything. Check the child call by hand.")

    domain = domains.get(host)
    if domain is None:
        return ("unknown-domain",
                "%s is not a SIP Domain on this account, so no endpoint can "
                "hold a registration on it and every Dial to it fails the same "
                "way." % host)

    if not domain.get("sip_registration"):
        return ("registration-off",
                "sip_registration is false on %s: the domain can accept INVITEs "
                "from mapped credentials but nothing may register to it, so "
                "sip:%s@%s has no registration to route to and never will."
                % (host, user, host))

    usernames = list(domain.get("usernames") or [])
    if not usernames:
        return ("no-credentials",
                "%s allows registration but no credential list is mapped to its "
                "Auth/Registrations subresource, so there is no username any "
                "endpoint could register with." % host)

    if user in usernames:
        return ("offline",
                "%s is a registerable credential on %s, so the username is "
                "right and the endpoint simply held no registration when the "
                "call arrived: a dropped REGISTER refresh, a closed softphone, "
                "or a NAT binding that expired." % (user, host))

    folded = {u.casefold(): u for u in usernames}
    if user.casefold() in folded:
        return ("case-mismatch",
                "the credential on %s is %s and the Dial asked for %s. SIP "
                "usernames are compared exactly, so these are two different "
                "endpoints however alike they read."
                % (host, folded[user.casefold()], user))

    return ("unknown-user",
            "%s is not among the %d registerable username(s) on %s, so this "
            "call was never going to connect regardless of who was online."
            % (user, len(usernames), host))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


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

    Several voice failures are logged at warning rather than error. A sweep that
    reads only the error level reports a clean account while the calls keep
    failing, which is why this function takes a list of levels at all.
    """
    seen = {}
    for level in levels:
        for a in list_alerts(session, since, limit, level):
            seen.setdefault(a.get("sid"), a)
    return list(seen.values())


def registerable_domains(session, account):
    """Map each SIP domain to its registration flag and registerable usernames.

    The Auth/Registrations mapping is a different subresource from Auth/Calls. A
    credential list mapped only to the latter is correct, present, and unable to
    register anything, so reading the wrong one produces a confident wrong answer.
    """
    out = {}
    domains = page_2010(session, "%s/Accounts/%s/SIP/Domains.json" % (BASE, account),
                        "sip_domains")
    for d in domains:
        name = str(d.get("domain_name") or "").strip().lower()
        if not name:
            continue
        usernames = []
        if d.get("sip_registration"):
            mappings = page_2010(
                session,
                "%s/Accounts/%s/SIP/Domains/%s/Auth/Registrations/"
                "CredentialListMappings.json" % (BASE, account, d.get("sid")),
                "credential_list_mappings")
            for m in mappings:
                creds = page_2010(
                    session,
                    "%s/Accounts/%s/SIP/CredentialLists/%s/Credentials.json"
                    % (BASE, account, m.get("sid")), "credentials")
                usernames.extend(str(c.get("username") or "").strip() for c in creds)
        out[name] = {"sip_registration": bool(d.get("sip_registration")),
                     "usernames": [u for u in usernames if u]}
    return out


def sip_leg(session, account, parent_sid):
    """The child leg of a call whose destination is a SIP URI, or an empty string."""
    children = page_2010(session, "%s/Accounts/%s/Calls.json" % (BASE, account),
                         "calls", ParentCallSid=parent_sid)
    for c in children:
        to = str(c.get("to") or "").strip()
        if to.lower().startswith("sip:") or to.lower().startswith("sips:"):
            return to
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to sweep (alerts are retained 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop after this many alerts per log level")
    ap.add_argument("--errors-only", action="store_true",
                    help="skip the warning level, which will under-report")
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
            if str(a.get("error_code") or "").strip() == str(NOT_REGISTERED)]
    if not hits:
        log.info("0 alert(s) with error_code %d in the last %d day(s)",
                 NOT_REGISTERED, days)
        return 0

    domains = registerable_domains(session, account)
    targets = {}
    counts = {}
    for a in hits:
        parent = str(a.get("resource_sid") or "")
        if not parent.startswith("CA"):
            log.warning("32009 alert %s has no call sid to resolve", a.get("sid"))
            continue
        if parent not in targets:
            targets[parent] = sip_target(sip_leg(session, account, parent))
        state, detail = verdict(targets[parent], domains)
        counts[state] = counts.get(state, 0) + 1
        log.warning("%-16s %s  %s", state, parent, detail)

    log.warning("%d alert(s) with error_code %d across %d call(s): %s",
                len(hits), NOT_REGISTERED, len(targets),
                ", ".join("%s=%d" % kv for kv in sorted(counts.items())))
    log.warning("  repair: make the username in <Sip> match a credential "
                "exactly, or set SipRegistration=true on the domain, or map the "
                "credential list to Auth/Registrations")
    log.warning("  live registrations: Console > Voice > Manage > SIP Domains > "
                "Registered SIP Endpoints")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sip-registration-audit.mjs",
"js": '''/**
 * Report Twilio 32009 alerts and say why each SIP endpoint was unreachable.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const NOT_REGISTERED = 32009;

/**
 * Split a SIP URI into [user, domain]. The domain is lowercased because SIP
 * hostnames are case insensitive; the user is not, because a credential created
 * as Reception and a Dial aimed at reception are different endpoints and folding
 * case throws away the evidence that says so.
 */
export function sipTarget(uri) {
  let v = String(uri ?? '').trim();
  if (v.includes('<') && v.includes('>')) {
    v = v.slice(v.indexOf('<') + 1, v.indexOf('>')).trim();
  }
  const low = v.toLowerCase();
  let matched = false;
  for (const scheme of ['sips:', 'sip:']) {
    if (low.startsWith(scheme)) { v = v.slice(scheme.length); matched = true; break; }
  }
  if (!matched) return ['', ''];
  v = v.split(';')[0].split('?')[0];
  if (!v.includes('@')) return ['', ''];
  const at = v.lastIndexOf('@');
  const user = v.slice(0, at).trim();
  const host = v.slice(at + 1).split(':')[0].trim().toLowerCase();
  return [user, host];
}

/**
 * Explain one 32009. `target` is [user, domain] from sipTarget; `domains` maps a
 * lowercase domain_name to { sip_registration, usernames }. Pure. Returns
 * [state, detail].
 */
export function verdict(target, domains = {}) {
  const [user, host] = target;
  if (!host) {
    return ['unresolved',
      'no sip: destination on the failing leg, so the username cannot be ' +
      'compared against anything. Check the child call by hand.'];
  }

  const domain = domains[host];
  if (domain === undefined) {
    return ['unknown-domain',
      `${host} is not a SIP Domain on this account, so no endpoint can hold a ` +
      'registration on it and every Dial to it fails the same way.'];
  }

  if (!domain.sip_registration) {
    return ['registration-off',
      `sip_registration is false on ${host}: the domain can accept INVITEs from ` +
      `mapped credentials but nothing may register to it, so sip:${user}@${host} ` +
      'has no registration to route to and never will.'];
  }

  const usernames = domain.usernames ?? [];
  if (usernames.length === 0) {
    return ['no-credentials',
      `${host} allows registration but no credential list is mapped to its ` +
      'Auth/Registrations subresource, so there is no username any endpoint ' +
      'could register with.'];
  }

  if (usernames.includes(user)) {
    return ['offline',
      `${user} is a registerable credential on ${host}, so the username is right ` +
      'and the endpoint simply held no registration when the call arrived: a ' +
      'dropped REGISTER refresh, a closed softphone, or a NAT binding that expired.'];
  }

  const folded = new Map(usernames.map((u) => [u.toLowerCase(), u]));
  if (folded.has(user.toLowerCase())) {
    return ['case-mismatch',
      `the credential on ${host} is ${folded.get(user.toLowerCase())} and the ` +
      `Dial asked for ${user}. SIP usernames are compared exactly, so these are ` +
      'two different endpoints however alike they read.'];
  }

  return ['unknown-user',
    `${user} is not among the ${usernames.length} registerable username(s) on ` +
    `${host}, so this call was never going to connect regardless of who was online.`];
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

/** Page a 2010-04-01 listing. next_page_uri here is a path, not a URL. */
export async function page2010(auth, url, key, params = {}) {
  let next = url;
  let query = { PageSize: 1000, ...params };
  const out = [];
  while (next) {
    const body = await get(auth, next, query);
    out.push(...(body[key] ?? []));
    next = body.next_page_uri ? HOST + body.next_page_uri : null;
    query = {};
  }
  return out;
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

/** Both log levels, merged on sid: several voice failures are warnings. */
export async function sweepAlerts(auth, since, limit, levels) {
  const seen = new Map();
  for (const level of levels) {
    for (const a of await listAlerts(auth, since, limit, level)) {
      if (!seen.has(a.sid)) seen.set(a.sid, a);
    }
  }
  return [...seen.values()];
}

async function registerableDomains(auth, account) {
  const out = {};
  const domains = await page2010(
    auth, `${BASE}/Accounts/${account}/SIP/Domains.json`, 'sip_domains');
  for (const d of domains) {
    const name = String(d.domain_name ?? '').trim().toLowerCase();
    if (!name) continue;
    const usernames = [];
    if (d.sip_registration) {
      const mappings = await page2010(
        auth,
        `${BASE}/Accounts/${account}/SIP/Domains/${d.sid}/Auth/Registrations/` +
        'CredentialListMappings.json', 'credential_list_mappings');
      for (const m of mappings) {
        const creds = await page2010(
          auth,
          `${BASE}/Accounts/${account}/SIP/CredentialLists/${m.sid}/Credentials.json`,
          'credentials');
        for (const c of creds) {
          const u = String(c.username ?? '').trim();
          if (u) usernames.push(u);
        }
      }
    }
    out[name] = { sip_registration: Boolean(d.sip_registration), usernames };
  }
  return out;
}

async function sipLeg(auth, account, parentSid) {
  const children = await page2010(
    auth, `${BASE}/Accounts/${account}/Calls.json`, 'calls',
    { ParentCallSid: parentSid });
  for (const c of children) {
    const to = String(c.to ?? '').trim().toLowerCase();
    if (to.startsWith('sip:') || to.startsWith('sips:')) return String(c.to).trim();
  }
  return '';
}

function flagValue(name, fallback) {
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
  const days = Math.min(flagValue('--days', 7), 30);
  const levels = process.argv.includes('--errors-only') ? ['error'] : ['error', 'warning'];
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await sweepAlerts(auth, since, 10000, levels);
  const hits = alerts.filter(
    (a) => String(a.error_code ?? '').trim() === String(NOT_REGISTERED));
  if (hits.length === 0) {
    console.log(`0 alert(s) with error_code ${NOT_REGISTERED} in the last ${days} day(s)`);
    return;
  }

  const domains = await registerableDomains(auth, account);
  const targets = new Map();
  const counts = new Map();
  for (const a of hits) {
    const parent = String(a.resource_sid ?? '');
    if (!parent.startsWith('CA')) {
      console.warn(`32009 alert ${a.sid} has no call sid to resolve`);
      continue;
    }
    if (!targets.has(parent)) {
      targets.set(parent, sipTarget(await sipLeg(auth, account, parent)));
    }
    const [state, detail] = verdict(targets.get(parent), domains);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    console.warn(`${state.padEnd(16)} ${parent}  ${detail}`);
  }

  const summary = [...counts.entries()].sort().map(([k, v]) => `${k}=${v}`).join(', ');
  console.warn(`${hits.length} alert(s) with error_code ${NOT_REGISTERED} across ` +
               `${targets.size} call(s): ${summary}`);
  console.warn('  repair: make the username in <Sip> match a credential exactly, ' +
               'or set SipRegistration=true on the domain, or map the credential ' +
               'list to Auth/Registrations');
  console.warn('  live registrations: Console > Voice > Manage > SIP Domains > ' +
               'Registered SIP Endpoints');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that earns this test file is the one where the credential and the dialled user differ only in capitalisation. It has to come back as its own state and it has to name both strings, because a check that reports it as <em>unknown user</em> sends someone to create a credential that already exists. The rest pin the URI parser: a display name, a port, a URI parameter and a <code>sips:</code> scheme all have to reduce to the same pair.",
"test_py_file": "test_twilio_sip_registration_audit.py",
"test_py": '''from twilio_sip_registration_audit import sip_target, verdict

DOMAINS = {
    "acme.sip.twilio.com": {"sip_registration": True,
                            "usernames": ["Reception", "warehouse"]},
    "calls-only.sip.twilio.com": {"sip_registration": False, "usernames": []},
    "open.sip.twilio.com": {"sip_registration": True, "usernames": []},
}


def test_plain_uri_splits_into_user_and_domain():
    assert sip_target("sip:warehouse@acme.sip.twilio.com") == \\
        ("warehouse", "acme.sip.twilio.com")


def test_domain_is_lowercased_and_the_user_is_not():
    # Folding the user would destroy the only evidence the case-mismatch state
    # has to work with, so the asymmetry is deliberate and pinned here.
    assert sip_target("SIP:Reception@ACME.sip.twilio.com") == \\
        ("Reception", "acme.sip.twilio.com")


def test_port_parameters_display_name_and_sips_all_reduce_the_same():
    assert sip_target("sips:warehouse@acme.sip.twilio.com:5061") == \\
        ("warehouse", "acme.sip.twilio.com")
    assert sip_target("sip:warehouse@acme.sip.twilio.com;transport=tls") == \\
        ("warehouse", "acme.sip.twilio.com")
    assert sip_target('"Front desk" <sip:warehouse@acme.sip.twilio.com>') == \\
        ("warehouse", "acme.sip.twilio.com")


def test_a_tel_uri_or_a_bare_number_is_not_a_sip_target():
    assert sip_target("+15005550006") == ("", "")
    assert sip_target("sip:acme.sip.twilio.com") == ("", "")
    assert sip_target(None) == ("", "")


def test_missing_destination_is_unresolved_rather_than_a_guess():
    state, _ = verdict(("", ""), DOMAINS)
    assert state == "unresolved"


def test_domain_not_on_the_account_is_its_own_state():
    state, _ = verdict(("warehouse", "other.sip.twilio.com"), DOMAINS)
    assert state == "unknown-domain"


def test_registration_disabled_is_permanent_not_transient():
    state, detail = verdict(("warehouse", "calls-only.sip.twilio.com"), DOMAINS)
    assert state == "registration-off"
    assert "never will" in detail


def test_registration_enabled_with_nothing_mapped():
    state, detail = verdict(("warehouse", "open.sip.twilio.com"), DOMAINS)
    assert state == "no-credentials"
    assert "Auth/Registrations" in detail


def test_exact_match_means_the_endpoint_was_merely_offline():
    state, detail = verdict(("warehouse", "acme.sip.twilio.com"), DOMAINS)
    assert state == "offline"
    assert "REGISTER refresh" in detail


def test_case_mismatch_is_reported_separately_and_names_both_strings():
    # Reported as unknown-user, this sends someone to create a credential that
    # already exists. It is the whole reason the parser preserves case.
    state, detail = verdict(("reception", "acme.sip.twilio.com"), DOMAINS)
    assert state == "case-mismatch"
    assert "Reception" in detail
    assert "reception" in detail


def test_username_nobody_ever_created_is_unknown_user():
    state, detail = verdict(("nightshift", "acme.sip.twilio.com"), DOMAINS)
    assert state == "unknown-user"
    assert "2 registerable" in detail
''',
"test_js_file": "twilio-sip-registration-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sipTarget, verdict } from './twilio-sip-registration-audit.mjs';

const DOMAINS = {
  'acme.sip.twilio.com': { sip_registration: true, usernames: ['Reception', 'warehouse'] },
  'calls-only.sip.twilio.com': { sip_registration: false, usernames: [] },
  'open.sip.twilio.com': { sip_registration: true, usernames: [] },
};

test('plain uri splits into user and domain', () => {
  assert.deepEqual(sipTarget('sip:warehouse@acme.sip.twilio.com'),
                   ['warehouse', 'acme.sip.twilio.com']);
});

test('domain is lowercased and the user is not', () => {
  assert.deepEqual(sipTarget('SIP:Reception@ACME.sip.twilio.com'),
                   ['Reception', 'acme.sip.twilio.com']);
});

test('port, parameters, display name and sips all reduce the same', () => {
  assert.deepEqual(sipTarget('sips:warehouse@acme.sip.twilio.com:5061'),
                   ['warehouse', 'acme.sip.twilio.com']);
  assert.deepEqual(sipTarget('sip:warehouse@acme.sip.twilio.com;transport=tls'),
                   ['warehouse', 'acme.sip.twilio.com']);
  assert.deepEqual(sipTarget('"Front desk" <sip:warehouse@acme.sip.twilio.com>'),
                   ['warehouse', 'acme.sip.twilio.com']);
});

test('a tel uri or a bare number is not a sip target', () => {
  assert.deepEqual(sipTarget('+15005550006'), ['', '']);
  assert.deepEqual(sipTarget('sip:acme.sip.twilio.com'), ['', '']);
  assert.deepEqual(sipTarget(null), ['', '']);
});

test('missing destination is unresolved rather than a guess', () => {
  assert.equal(verdict(['', ''], DOMAINS)[0], 'unresolved');
});

test('domain not on the account is its own state', () => {
  assert.equal(verdict(['warehouse', 'other.sip.twilio.com'], DOMAINS)[0],
               'unknown-domain');
});

test('registration disabled is permanent not transient', () => {
  const [state, detail] = verdict(['warehouse', 'calls-only.sip.twilio.com'], DOMAINS);
  assert.equal(state, 'registration-off');
  assert.match(detail, /never will/);
});

test('registration enabled with nothing mapped', () => {
  const [state, detail] = verdict(['warehouse', 'open.sip.twilio.com'], DOMAINS);
  assert.equal(state, 'no-credentials');
  assert.match(detail, /Auth.Registrations/);
});

test('exact match means the endpoint was merely offline', () => {
  const [state, detail] = verdict(['warehouse', 'acme.sip.twilio.com'], DOMAINS);
  assert.equal(state, 'offline');
  assert.match(detail, /REGISTER refresh/);
});

test('case mismatch is reported separately and names both strings', () => {
  const [state, detail] = verdict(['reception', 'acme.sip.twilio.com'], DOMAINS);
  assert.equal(state, 'case-mismatch');
  assert.match(detail, /Reception/);
  assert.match(detail, /reception/);
});

test('username nobody ever created is unknown user', () => {
  const [state, detail] = verdict(['nightshift', 'acme.sip.twilio.com'], DOMAINS);
  assert.equal(state, 'unknown-user');
  assert.match(detail, /2 registerable/);
});
''',
"faq": [
 ("Why does the sweep read the warning level too?",
  "Because several voice failures are logged at LogLevel=warning rather than error, and a sweep filtered to the error level returns nothing while the calls keep failing. Reading both and merging on the alert sid costs one extra paginated read and removes an entire class of false reassurance."),
 ("Is 32009 always the endpoint's fault?",
  "No, and that is why the script has five states instead of one. An exact username match means the credential is correct and the registration had lapsed, which is the endpoint's side. A case mismatch, an unmapped credential list or sip_registration set to false are all yours, and none of them will fix itself when the softphone reconnects."),
 ("Why not just compare usernames case-insensitively?",
  "Because SIP compares them exactly, so a case-insensitive check reports a broken call as healthy. The script folds case only after the exact comparison has already failed, and then reports the result as its own state so nobody is sent to create a credential that already exists under a different capitalisation."),
 ("Why read the Auth/Registrations mappings rather than Auth/Calls?",
  "They are different subresources and they answer different questions. Auth/Calls governs which credentials may place calls through the domain; Auth/Registrations governs which may register to it. A credential list mapped only to the first produces a domain full of correct credentials that cannot register, which is exactly the shape this note is about."),
 ("Can the script re-register the endpoint or fix the username?",
  "It will not. Registration happens at the endpoint, not through the API, and rewriting a live domain's SipRegistration flag or a TwiML template from a monitoring job is how a working phone system goes down unattended. It prints the resource and the field, and you run it."),
],
"related": [
 ("/twilio/sip-domain-no-auth-type/", "A SIP Domain with no auth_type accepts nothing"),
 ("/twilio/sip-infrastructure-communication-error-32011/", "Twilio cannot reach your SIP infrastructure"),
 ("/twilio/dial-invalid-caller-id-13214/", "Dial rejected on a passed-through caller ID"),
],
"citations": [CITE_32009, CITE_SIP_DOMAIN, CITE_SIP_CRED, CITE_TWIML_SIP],
},

{
"slug": "sip-infrastructure-communication-error-32011",
"title": "32011: Twilio cannot reach your SIP infrastructure",
"description": "Twilio got no answer, a SIP 5xx, or something it could not parse from your origination URI. Redundancy that all resolves to one host is not redundancy.",
"h1": "32011: Twilio cannot reach your SIP infrastructure",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 32011", "error communicating with your sip infrastructure",
             "twilio origination url sip_url", "twilio sip tls 1.2",
             "elastic sip trunking firewall allowlist"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Call setup gets slow, then calls stop. The trunk configuration has not been touched in months and does not need to have been: <code>32011 Error communicating with your SIP communications infrastructure</code> means Twilio sent an INVITE to the address you gave it and got nothing back, or got a 5xx, or got something it could not make sense of. The change was on your side of the boundary, and it was probably a firewall rule, a TLS version, or a host that has quietly been carrying every origination URI on the trunk.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts</code> at <strong>both</strong> <code>LogLevel=error</code> and <code>LogLevel=warning</code> and keep <code>error_code</code> <code>32011</code>. That is the count. The shape is on the trunks: <code>GET https://trunking.twilio.com/v1/Trunks</code>, then per trunk <code>GET https://trunking.twilio.com/v1/Trunks/{TrunkSid}/OriginationUrls</code> for <code>sip_url</code>, <code>enabled</code>, <code>priority</code> and <code>weight</code>.</p>
<p>Read the <code>sip_url</code> strings rather than counting them. Several URIs that all resolve to one hostname are one path with three entries. A trunk whose <code>secure</code> is <code>true</code> while every enabled URI names a cleartext transport is a mismatch that will produce 32011 on every call. And a set of URIs that all share one <code>priority</code> is distributed across by weight, not failed over in order.</p>""",
"problem": """<p>The error is accurate and unhelpful in the same sentence. Twilio is telling you it could not talk to your infrastructure, which you can do nothing with until you know <em>which</em> infrastructure and <em>why</em>. The alert does not name the origination URI it tried, the trunk does not record its last successful contact, and the only thing on the Twilio side that changes when your PBX goes unreachable is the count of these alerts.</p>
<p>What makes it drag is that the trunk looks redundant. There are three origination URLs in the console. Somebody configured them deliberately, years ago, and everyone since has read three rows as three paths. If all three point at <code>sip:pbx.example.com</code> with different ports, or two of them are disabled, or they differ only in the transport parameter, then the firewall change that took out one host took out all of them at once, and the configuration that was supposed to prevent that is the reason nobody suspects it.</p>""",
"why": """<p><strong>The failure is outside Twilio, so Twilio can only report the symptom.</strong> A 32011 covers a dropped packet, a SIP 503, a malformed response and a TLS handshake that never completed. Twilio has no way to distinguish those from the outside, and neither will you from the alert text alone. The configuration is what narrows it.</p>
<p><strong>Rows in a list read as redundancy.</strong> Three origination URLs feel like three chances. Counting rows is the check everyone does; resolving them to distinct hostnames is the check that finds the trunk where all three are the same box.</p>
<p><strong>Transport is a URI parameter, not a field.</strong> Whether a URI uses TLS lives inside the <code>sip_url</code> string as <code>;transport=tls</code>, or in a <code>sips:</code> scheme. It is not a separate column, so it does not appear in a table view and it does not get compared against the trunk's <code>secure</code> setting by anything except you.</p>
<p><strong>TLS versions expire on a date nobody has in their calendar.</strong> An endpoint that was fine on TLS 1.0 stops being reachable when support for it ends. Nothing in the trunk changes, nothing in the alert says <em>TLS</em>, and the symptom is a communication error that looks like a network problem.</p>""",
"steps": [
 {"h": "Count the 32011s across both log levels",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, then the same at <code>LogLevel=warning</code>, following <code>meta.next_page_url</code> and merging on <code>sid</code>. The count is the evidence that this is happening now; the trunk configuration is the evidence about why. Neither alone is a diagnosis.</p>"""},
 {"h": "List the trunks and their origination URIs",
  "body": """<p><code>GET https://trunking.twilio.com/v1/Trunks</code> and then <code>GET https://trunking.twilio.com/v1/Trunks/{TrunkSid}/OriginationUrls</code> per trunk. Both paginate with an absolute <code>meta.next_page_url</code> rather than the relative <code>next_page_uri</code> the 2010-04-01 API uses. Keep <code>sip_url</code>, <code>enabled</code>, <code>priority</code> and <code>weight</code>.</p>"""},
 {"h": "Reduce every enabled sip_url to a hostname and count distinct ones",
  "body": """<p>Strip the scheme, any user part, the port and the parameters, and lowercase what is left. Three enabled URIs across one hostname is a single point of failure with three rows in the console, and it is the finding that people are most surprised by because the console looks like the opposite.</p>"""},
 {"h": "Compare the transport against the trunk's secure flag",
  "body": """<p><code>secure</code> on the trunk means TLS and SRTP are required. If no enabled URI carries <code>;transport=tls</code> or a <code>sips:</code> scheme, the trunk is asking for an encrypted path to an address that does not offer one. That combination produces 32011 on every call rather than intermittently, which usefully separates it from a firewall problem.</p>"""},
 {"h": "Fix the edge, then add a genuinely separate path",
  "body": """<p>Allowlist Twilio's SIP signalling and media ranges, confirm the endpoint negotiates TLS 1.2, and correct the <code>sip_url</code> if it is wrong. Then <code>POST https://trunking.twilio.com/v1/Trunks/{TrunkSid}/OriginationUrls</code> with a second URI on a different host and a higher <code>priority</code> number, so there is an ordered failover rather than a weighted spread across one machine. Re-run afterwards over a fresh window.</p>"""},
],
"verify": """<p>Re-run over a window that begins after the change. The alert count should be zero and every trunk should report <code>redundant</code>.</p>
<pre><code class="language-bash">python3 twilio_trunk_origination_audit.py --days 3
# 3 trunk(s), 0 alert(s) with error_code 32011 in the last 3 day(s)</code></pre>""",
"code_intro": "Two alert sweeps for the count, one paginated GET over the trunks, and one GET per trunk for its origination URIs. All reads; an API Key with read access is enough. Two pure functions do the thinking: one reduces a <code>sip_url</code> to a hostname and one to a transport, and the classifier works on those rather than on the raw strings. Reducing first is what turns three rows that look redundant into one host that is not.",
"py_file": "twilio_trunk_origination_audit.py",
"py": '''"""Report Twilio SIP trunks whose origination path explains a 32011.

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
log = logging.getLogger("twilio_trunk_origination_audit")

TRUNKING = "https://trunking.twilio.com/v1"
MONITOR = "https://monitor.twilio.com/v1"

SIP_COMMS = 32011


def sip_host(sip_url):
    """Reduce a sip_url to its lowercase hostname.

    Three origination URIs that differ only in port or transport are three rows
    in the console and one machine on the network. Comparing hostnames is what
    tells those apart; comparing the raw strings never will.

    A value with no sip: or sips: scheme is not a SIP URI, so it reduces to ""
    and is reported rather than quietly treated as a hostname.
    """
    v = str(sip_url or "").strip()
    low = v.lower()
    for scheme in ("sips:", "sip:"):
        if low.startswith(scheme):
            v = v[len(scheme):]
            break
    else:
        return ""
    v = v.split(";", 1)[0].split("?", 1)[0]
    if "@" in v:
        v = v.rsplit("@", 1)[1]
    return v.split(":", 1)[0].strip().lower()


def transport_of(sip_url):
    """The transport a sip_url asks for: tls, tcp, udp, or "" when unstated.

    Transport lives inside the URI string as a parameter, or is implied by the
    sips: scheme. It is not a field on the resource, so nothing but this
    function will ever compare it against the trunk's secure flag.
    """
    v = str(sip_url or "").strip().lower()
    if v.startswith("sips:"):
        return "tls"
    for part in v.split(";")[1:]:
        name, _, value = part.partition("=")
        if name.strip() == "transport":
            return value.strip().split("?", 1)[0]
    return ""


def verdict(trunk, origination, alerts=0):
    """Classify one trunk's origination path. Pure, so it tests offline.

    origination is the trunk's OriginationUrl list. alerts is how many 32011
    alerts were seen in the window, which changes what a healthy-looking
    topology means: diverse paths plus alerts points at the edge rather than at
    the configuration.

    Returns (state, detail).
    """
    live = [u for u in (origination or []) if u.get("enabled")]
    if not live:
        return ("no-enabled-uri",
                "no enabled origination URI: Twilio has no address to send an "
                "INVITE to, so every inbound call on this trunk fails and %d "
                "alert(s) is an undercount of the damage." % alerts)

    hosts = [sip_host(u.get("sip_url")) for u in live]
    if "" in hosts:
        return ("unparseable-uri",
                "an enabled origination URI has no hostname this script can "
                "read, which usually means the sip_url is malformed and Twilio "
                "cannot resolve it either.")

    if trunk.get("secure") and not any(transport_of(u.get("sip_url")) == "tls"
                                       for u in live):
        return ("transport-mismatch",
                "secure is true on the trunk but no enabled URI asks for TLS: "
                "the trunk requires an encrypted path to an address that does "
                "not offer one, which fails every call rather than some of them.")

    distinct = sorted(set(hosts))
    if len(live) == 1:
        return ("single-path",
                "one enabled origination URI (%s): the %d alert(s) in this "
                "window had no second address to try, so a firewall rule or a "
                "reboot on that host is a full outage."
                % (live[0].get("sip_url") or "?", alerts))

    if len(distinct) == 1:
        return ("one-host",
                "%d enabled origination URIs all resolving to %s: three rows in "
                "the console, one machine on the network, and nothing to fail "
                "over to when it stops answering." % (len(live), distinct[0]))

    priorities = {u.get("priority") for u in live}
    if len(priorities) == 1:
        return ("flat-priority",
                "%d enabled URIs across %d hosts all share one priority, so "
                "Twilio spreads traffic over them by weight rather than trying "
                "them in order. That is load balancing, not failover."
                % (len(live), len(distinct)))

    if alerts:
        return ("reachability",
                "%d alert(s) against %d ordered URIs across %d hosts: the "
                "topology is not the problem, so look at the firewall ranges, "
                "the TLS version on the endpoint, and whether the PBX is "
                "answering with a 5xx." % (alerts, len(live), len(distinct)))

    return ("redundant",
            "%d enabled URIs across %d hosts with distinct priorities and no "
            "32011 in this window." % (len(live), len(distinct)))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page_meta(session, url, key, limit=100000, **params):
    """Page an API that carries an absolute meta.next_page_url."""
    params.setdefault("PageSize", 100)
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def sweep_alerts(session, since, limit, levels):
    """Both log levels, merged on sid.

    Several voice failures are logged at warning rather than error. Filtering to
    error alone reports a clean account while the trunk keeps failing.
    """
    seen = {}
    for level in levels:
        url = MONITOR + "/Alerts"
        params = {"LogLevel": level, "StartDate": since, "PageSize": 1000}
        got = 0
        while url and got < limit:
            page = get(session, url, **params)
            for a in page.get("alerts", []):
                seen.setdefault(a.get("sid"), a)
                got += 1
            url = (page.get("meta") or {}).get("next_page_url")
            params = {}
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=3,
                    help="how far back to sweep (alerts are retained 30 days)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop after this many alerts per log level")
    ap.add_argument("--errors-only", action="store_true",
                    help="skip the warning level, which will under-report")
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
            if str(a.get("error_code") or "").strip() == str(SIP_COMMS)]

    trunks = page_meta(session, TRUNKING + "/Trunks", "trunks")
    if not trunks:
        log.info("no SIP trunks on this account")
        return 0

    bad = 0
    for t in trunks:
        origination = page_meta(
            session, "%s/Trunks/%s/OriginationUrls" % (TRUNKING, t.get("sid")),
            "origination_urls")
        state, detail = verdict(t, origination, len(hits))
        name = t.get("friendly_name") or t.get("domain_name") or t.get("sid")
        line = "%-18s %s  %s" % (state, name, detail)
        if state == "redundant":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for u in origination:
            log.warning("    %-5s priority=%s weight=%s %s",
                        "on" if u.get("enabled") else "off", u.get("priority"),
                        u.get("weight"), u.get("sip_url"))
        log.warning("  repair: allowlist Twilio's SIP signalling and media "
                    "ranges, confirm the endpoint negotiates TLS 1.2, and add a "
                    "second origination URI on a different host with a higher "
                    "priority number")

    log.info("%d trunk(s), %d alert(s) with error_code %d in the last %d day(s)",
             len(trunks), len(hits), SIP_COMMS, days)
    return 1 if (bad or hits) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-trunk-origination-audit.mjs",
"js": '''/**
 * Report Twilio SIP trunks whose origination path explains a 32011.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const TRUNKING = 'https://trunking.twilio.com/v1';
const MONITOR = 'https://monitor.twilio.com/v1';

const SIP_COMMS = 32011;

/**
 * Reduce a sip_url to its lowercase hostname. Three URIs that differ only in
 * port or transport are three rows in the console and one machine on the
 * network, and only a hostname comparison tells those apart. A value with no
 * sip: or sips: scheme is not a SIP URI, so it reduces to '' and is reported
 * rather than quietly treated as a hostname.
 */
export function sipHost(sipUrl) {
  let v = String(sipUrl ?? '').trim();
  const low = v.toLowerCase();
  let matched = false;
  for (const scheme of ['sips:', 'sip:']) {
    if (low.startsWith(scheme)) { v = v.slice(scheme.length); matched = true; break; }
  }
  if (!matched) return '';
  v = v.split(';')[0].split('?')[0];
  if (v.includes('@')) v = v.slice(v.lastIndexOf('@') + 1);
  return v.split(':')[0].trim().toLowerCase();
}

/**
 * The transport a sip_url asks for: tls, tcp, udp, or '' when unstated.
 * Transport is a URI parameter rather than a field on the resource, so nothing
 * but this compares it against the trunk's secure flag.
 */
export function transportOf(sipUrl) {
  const v = String(sipUrl ?? '').trim().toLowerCase();
  if (v.startsWith('sips:')) return 'tls';
  for (const part of v.split(';').slice(1)) {
    const eq = part.indexOf('=');
    if (eq === -1) continue;
    if (part.slice(0, eq).trim() === 'transport') {
      return part.slice(eq + 1).trim().split('?')[0];
    }
  }
  return '';
}

/**
 * Classify one trunk's origination path. `alerts` is how many 32011 alerts were
 * seen in the window, which changes what a healthy topology means. Pure.
 * Returns [state, detail].
 */
export function verdict(trunk, origination, alerts = 0) {
  const live = (origination ?? []).filter((u) => u.enabled);
  if (live.length === 0) {
    return ['no-enabled-uri',
      'no enabled origination URI: Twilio has no address to send an INVITE to, ' +
      `so every inbound call on this trunk fails and ${alerts} alert(s) is an ` +
      'undercount of the damage.'];
  }

  const hosts = live.map((u) => sipHost(u.sip_url));
  if (hosts.includes('')) {
    return ['unparseable-uri',
      'an enabled origination URI has no hostname this script can read, which ' +
      'usually means the sip_url is malformed and Twilio cannot resolve it either.'];
  }

  if (trunk.secure && !live.some((u) => transportOf(u.sip_url) === 'tls')) {
    return ['transport-mismatch',
      'secure is true on the trunk but no enabled URI asks for TLS: the trunk ' +
      'requires an encrypted path to an address that does not offer one, which ' +
      'fails every call rather than some of them.'];
  }

  const distinct = [...new Set(hosts)].sort();
  if (live.length === 1) {
    return ['single-path',
      `one enabled origination URI (${live[0].sip_url ?? '?'}): the ${alerts} ` +
      'alert(s) in this window had no second address to try, so a firewall rule ' +
      'or a reboot on that host is a full outage.'];
  }

  if (distinct.length === 1) {
    return ['one-host',
      `${live.length} enabled origination URIs all resolving to ${distinct[0]}: ` +
      'three rows in the console, one machine on the network, and nothing to ' +
      'fail over to when it stops answering.'];
  }

  if (new Set(live.map((u) => u.priority)).size === 1) {
    return ['flat-priority',
      `${live.length} enabled URIs across ${distinct.length} hosts all share one ` +
      'priority, so Twilio spreads traffic over them by weight rather than trying ' +
      'them in order. That is load balancing, not failover.'];
  }

  if (alerts) {
    return ['reachability',
      `${alerts} alert(s) against ${live.length} ordered URIs across ` +
      `${distinct.length} hosts: the topology is not the problem, so look at the ` +
      'firewall ranges, the TLS version on the endpoint, and whether the PBX is ' +
      'answering with a 5xx.'];
  }

  return ['redundant',
    `${live.length} enabled URIs across ${distinct.length} hosts with distinct ` +
    'priorities and no 32011 in this window.'];
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

/** Page an API that carries an absolute meta.next_page_url. */
export async function pageMeta(auth, url, key, params = {}) {
  let next = url;
  let query = { PageSize: 100, ...params };
  const out = [];
  while (next) {
    const page = await get(auth, next, query);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    query = {};
  }
  return out;
}

/** Both log levels, merged on sid: several voice failures are warnings. */
export async function sweepAlerts(auth, since, limit, levels) {
  const seen = new Map();
  for (const level of levels) {
    let url = `${MONITOR}/Alerts`;
    let params = { LogLevel: level, StartDate: since, PageSize: 1000 };
    let got = 0;
    while (url && got < limit) {
      const page = await get(auth, url, params);
      for (const a of page.alerts ?? []) {
        if (!seen.has(a.sid)) seen.set(a.sid, a);
        got += 1;
      }
      url = page.meta?.next_page_url ?? null;
      params = {};
    }
  }
  return [...seen.values()];
}

function flagValue(name, fallback) {
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
  const days = Math.min(flagValue('--days', 3), 30);
  const levels = process.argv.includes('--errors-only') ? ['error'] : ['error', 'warning'];
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await sweepAlerts(auth, since, 10000, levels);
  const hits = alerts.filter(
    (a) => String(a.error_code ?? '').trim() === String(SIP_COMMS));

  const trunks = await pageMeta(auth, `${TRUNKING}/Trunks`, 'trunks');
  if (trunks.length === 0) {
    console.log('no SIP trunks on this account');
    return;
  }

  let bad = 0;
  for (const t of trunks) {
    const origination = await pageMeta(
      auth, `${TRUNKING}/Trunks/${t.sid}/OriginationUrls`, 'origination_urls');
    const [state, detail] = verdict(t, origination, hits.length);
    const name = t.friendly_name || t.domain_name || t.sid;
    const line = `${state.padEnd(18)} ${name}  ${detail}`;
    if (state === 'redundant') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    for (const u of origination) {
      console.warn(`    ${(u.enabled ? 'on' : 'off').padEnd(5)} ` +
                   `priority=${u.priority} weight=${u.weight} ${u.sip_url}`);
    }
    console.warn("  repair: allowlist Twilio's SIP signalling and media ranges, " +
                 'confirm the endpoint negotiates TLS 1.2, and add a second ' +
                 'origination URI on a different host with a higher priority number');
  }

  console.log(`${trunks.length} trunk(s), ${hits.length} alert(s) with error_code ` +
              `${SIP_COMMS} in the last ${days} day(s)`);
  process.exitCode = (bad || hits.length) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning hardest is three enabled URIs that all reduce to one hostname. It has to come back as <code>one-host</code>, not as redundant, because everything about the console view says otherwise. The rest pin the reductions: a port, a transport parameter and a <code>sips:</code> scheme must not change the hostname, and a disabled URI must not count towards anything.",
"test_py_file": "test_twilio_trunk_origination_audit.py",
"test_py": '''from twilio_trunk_origination_audit import sip_host, transport_of, verdict


def test_sip_host_ignores_scheme_port_and_parameters():
    assert sip_host("sip:PBX.example.com:5060;transport=udp") == "pbx.example.com"
    assert sip_host("sips:pbx.example.com") == "pbx.example.com"
    assert sip_host("sip:trunk@pbx.example.com") == "pbx.example.com"
    # A bare host is not a SIP URI, so it reduces to nothing and gets reported.
    assert sip_host("pbx.example.com") == ""
    assert sip_host("") == ""


def test_transport_is_read_from_the_parameter_or_the_scheme():
    assert transport_of("sip:pbx.example.com;transport=TLS") == "tls"
    assert transport_of("sips:pbx.example.com") == "tls"
    assert transport_of("sip:pbx.example.com;transport=tcp") == "tcp"
    assert transport_of("sip:pbx.example.com") == ""


def test_no_enabled_uri_is_the_first_thing_reported():
    state, detail = verdict({}, [{"sip_url": "sip:a.example.com", "enabled": False}], 9)
    assert state == "no-enabled-uri"
    assert "9 alert(s)" in detail


def test_three_uris_on_one_host_is_not_redundancy():
    # The finding the console view argues against: three rows, one machine.
    origination = [
        {"sip_url": "sip:pbx.example.com:5060", "enabled": True, "priority": 10},
        {"sip_url": "sip:pbx.example.com:5061", "enabled": True, "priority": 20},
        {"sip_url": "sip:PBX.example.com;transport=tcp", "enabled": True, "priority": 30},
    ]
    state, detail = verdict({}, origination, 4)
    assert state == "one-host"
    assert "pbx.example.com" in detail


def test_secure_trunk_with_no_tls_uri_fails_every_call():
    origination = [{"sip_url": "sip:a.example.com;transport=udp", "enabled": True,
                    "priority": 10},
                   {"sip_url": "sip:b.example.com;transport=udp", "enabled": True,
                    "priority": 20}]
    state, detail = verdict({"secure": True}, origination, 0)
    assert state == "transport-mismatch"
    assert "every call" in detail


def test_a_secure_trunk_with_one_tls_uri_is_not_a_mismatch():
    origination = [{"sip_url": "sips:a.example.com", "enabled": True, "priority": 10},
                   {"sip_url": "sip:b.example.com", "enabled": True, "priority": 20}]
    assert verdict({"secure": True}, origination, 0)[0] == "redundant"


def test_one_enabled_uri_carries_the_alert_count():
    origination = [{"sip_url": "sip:a.example.com", "enabled": True, "priority": 10},
                   {"sip_url": "sip:b.example.com", "enabled": False, "priority": 20}]
    state, detail = verdict({}, origination, 12)
    assert state == "single-path"
    assert "12 alert(s)" in detail


def test_equal_priorities_are_load_balancing_not_failover():
    origination = [{"sip_url": "sip:a.example.com", "enabled": True, "priority": 10},
                   {"sip_url": "sip:b.example.com", "enabled": True, "priority": 10}]
    state, detail = verdict({}, origination, 0)
    assert state == "flat-priority"
    assert "not failover" in detail


def test_a_good_topology_with_alerts_points_at_the_edge():
    origination = [{"sip_url": "sip:a.example.com", "enabled": True, "priority": 10},
                   {"sip_url": "sip:b.example.com", "enabled": True, "priority": 20}]
    state, detail = verdict({}, origination, 31)
    assert state == "reachability"
    assert "TLS version" in detail


def test_a_malformed_uri_is_reported_rather_than_silently_dropped():
    origination = [{"sip_url": "pbx.example.com", "enabled": True, "priority": 10},
                   {"sip_url": "sip:b.example.com", "enabled": True, "priority": 20}]
    assert verdict({}, origination, 0)[0] == "unparseable-uri"
''',
"test_js_file": "twilio-trunk-origination-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sipHost, transportOf, verdict } from './twilio-trunk-origination-audit.mjs';

test('sipHost ignores scheme, port and parameters', () => {
  assert.equal(sipHost('sip:PBX.example.com:5060;transport=udp'), 'pbx.example.com');
  assert.equal(sipHost('sips:pbx.example.com'), 'pbx.example.com');
  assert.equal(sipHost('sip:trunk@pbx.example.com'), 'pbx.example.com');
  // A bare host is not a SIP URI, so it reduces to nothing and gets reported.
  assert.equal(sipHost('pbx.example.com'), '');
  assert.equal(sipHost(''), '');
});

test('transport is read from the parameter or the scheme', () => {
  assert.equal(transportOf('sip:pbx.example.com;transport=TLS'), 'tls');
  assert.equal(transportOf('sips:pbx.example.com'), 'tls');
  assert.equal(transportOf('sip:pbx.example.com;transport=tcp'), 'tcp');
  assert.equal(transportOf('sip:pbx.example.com'), '');
});

test('no enabled uri is the first thing reported', () => {
  const [state, detail] = verdict({}, [{ sip_url: 'sip:a.example.com', enabled: false }], 9);
  assert.equal(state, 'no-enabled-uri');
  assert.match(detail, /9 alert/);
});

test('three uris on one host is not redundancy', () => {
  const origination = [
    { sip_url: 'sip:pbx.example.com:5060', enabled: true, priority: 10 },
    { sip_url: 'sip:pbx.example.com:5061', enabled: true, priority: 20 },
    { sip_url: 'sip:PBX.example.com;transport=tcp', enabled: true, priority: 30 },
  ];
  const [state, detail] = verdict({}, origination, 4);
  assert.equal(state, 'one-host');
  assert.match(detail, /pbx.example.com/);
});

test('secure trunk with no tls uri fails every call', () => {
  const origination = [
    { sip_url: 'sip:a.example.com;transport=udp', enabled: true, priority: 10 },
    { sip_url: 'sip:b.example.com;transport=udp', enabled: true, priority: 20 },
  ];
  const [state, detail] = verdict({ secure: true }, origination, 0);
  assert.equal(state, 'transport-mismatch');
  assert.match(detail, /every call/);
});

test('a secure trunk with one tls uri is not a mismatch', () => {
  const origination = [{ sip_url: 'sips:a.example.com', enabled: true, priority: 10 },
                       { sip_url: 'sip:b.example.com', enabled: true, priority: 20 }];
  assert.equal(verdict({ secure: true }, origination, 0)[0], 'redundant');
});

test('one enabled uri carries the alert count', () => {
  const origination = [{ sip_url: 'sip:a.example.com', enabled: true, priority: 10 },
                       { sip_url: 'sip:b.example.com', enabled: false, priority: 20 }];
  const [state, detail] = verdict({}, origination, 12);
  assert.equal(state, 'single-path');
  assert.match(detail, /12 alert/);
});

test('equal priorities are load balancing not failover', () => {
  const origination = [{ sip_url: 'sip:a.example.com', enabled: true, priority: 10 },
                       { sip_url: 'sip:b.example.com', enabled: true, priority: 10 }];
  const [state, detail] = verdict({}, origination, 0);
  assert.equal(state, 'flat-priority');
  assert.match(detail, /not failover/);
});

test('a good topology with alerts points at the edge', () => {
  const origination = [{ sip_url: 'sip:a.example.com', enabled: true, priority: 10 },
                       { sip_url: 'sip:b.example.com', enabled: true, priority: 20 }];
  const [state, detail] = verdict({}, origination, 31);
  assert.equal(state, 'reachability');
  assert.match(detail, /TLS version/);
});

test('a malformed uri is reported rather than silently dropped', () => {
  const origination = [{ sip_url: 'pbx.example.com', enabled: true, priority: 10 },
                       { sip_url: 'sip:b.example.com', enabled: true, priority: 20 }];
  assert.equal(verdict({}, origination, 0)[0], 'unparseable-uri');
});
''',
"faq": [
 ("Does a 32011 mean my PBX is down?",
  "Not necessarily. It means Twilio got no response, an error response, or a response it could not parse from the origination URI. A firewall that stopped permitting Twilio's signalling range, an endpoint that never enabled TLS 1.2, a sip_url pointing at a host that was decommissioned and a PBX returning 503 all produce the same code, which is why the configuration has to do the narrowing."),
 ("Why does the script reduce sip_url to a hostname?",
  "Because that is the difference between three paths and three rows. URIs that vary only by port or transport parameter look like redundancy in the console and share a single machine, a single firewall rule and a single power feed. Comparing hostnames is a two-line reduction that changes the answer on a surprising number of trunks."),
 ("What is wrong with several URIs at the same priority?",
  "Nothing, if you meant load balancing. Twilio tries lower priority numbers first and distributes across equal priorities by weight, so a flat set spreads traffic rather than failing over in order. Teams who configured a flat set believing they had a primary and a standby have neither, and it is worth knowing which one you have before the standby is needed."),
 ("Why sweep the warning level for a code that is an error?",
  "Because the sweep is cheap and the assumption is not safe. Several voice failures are logged at warning rather than error, and a sweep hard-coded to one level is exactly the habit that leaves an account reading clean. Merging both on the alert sid costs one extra paginated read."),
 ("Can the script add the second origination URI itself?",
  "It will not. Adding an origination URI changes where live inbound calls are routed, and doing that from a monitoring job with no knowledge of whether the new host is actually answering is a good way to turn a partial outage into a complete one. It prints the resource and the fields, and you run it."),
],
"related": [
 ("/twilio/trunk-missing-disaster-recovery-url/", "A SIP trunk with no disaster recovery URL"),
 ("/twilio/trunk-cps-limit-exceeded-32001/", "A trunk shedding calls at its CPS limit"),
 ("/twilio/sip-endpoint-not-registered-32009/", "Dial fails because the SIP endpoint is not there"),
],
"citations": [CITE_32011, CITE_ORIGINATION, CITE_TRUNK_TROUBLE, CITE_ALERT],
},

{
"slug": "trunk-cps-limit-exceeded-32001",
"title": "A trunk sheds calls at its CPS limit and the average hides it",
"description": "32001 is a ceiling hit inside one second. Failures cluster in the first moments of a batch and disappear into any hourly rate you compute afterwards.",
"h1": "a trunk sheds calls at its CPS limit and the average hides it",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 32001", "sip trunk cps limit exceeded",
             "twilio calls per second limit", "twilio 32012 warning",
             "predictive dialer twilio rate limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The dialer starts a campaign and the first second of it is thrown away. <code>32001 SIP: Trunk CPS limit exceeded</code>, a hundred of them, and then nothing for an hour. Anybody who looks at the hourly call rate sees a number well under the limit and concludes the limit is not the problem. It is: a ceiling measured per second cannot be checked against a rate measured per hour, and every graph you own is drawn at the wrong resolution to show it.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts</code> at <strong>both</strong> <code>LogLevel=error</code> and <code>LogLevel=warning</code>. <code>32001</code> arrives at the error level; the related CPS warning <code>32012</code> is logged at warning, so an error-only sweep sees the outcome and never the run-up to it.</p>
<p>Then get the shape from the calls. <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, bucket every <code>start_time</code> to the second, and take the busiest bucket. Compare that peak against the trunk's calls-per-second ceiling &mdash; which no read API exposes, so you supply the number Twilio gave you. A peak several times the mean is the finding even when it is under the ceiling, because the next campaign will be bigger.</p>""",
"problem": """<p>This one is a resolution problem before it is a capacity problem. A CPS ceiling is enforced against a one-second window. Every tool anybody uses to look at call volume &mdash; the console graphs, a daily export, a dashboard panel &mdash; aggregates to a minute at best and usually an hour. Divide a burst of 300 calls in four seconds across an hour and you get a rate that looks like nothing at all, which is exactly what the person investigating reports back.</p>
<p>So the failures get attributed to whatever else is nearby. The list is blamed, or the carrier, or an intermittent network problem, because the one explanation that fits perfectly has been ruled out by a calculation done at the wrong granularity. And the ceiling itself is not readable through the API, so even someone who suspects it has nothing to compare against unless they go and find the number in a support ticket from two years ago.</p>""",
"why": """<p><strong>A per-second limit and a per-hour average are different quantities.</strong> They are not approximations of each other. A dialer that opens 200 calls in two seconds and then idles has a peak of 100 and an hourly mean below one. Both numbers are correct and only one of them is the one being enforced.</p>
<p><strong>The burst is at the start, where nobody is watching.</strong> Campaign dialers open as many channels as they are permitted the moment a batch begins. The failures land in the first seconds, before anyone opens a dashboard, and the run recovers by itself as the queue drains.</p>
<p><strong>Some of the CPS family are warnings.</strong> 32012 is logged at <code>LogLevel=warning</code>, so a monitor filtered to errors misses the signal that comes before the shedding starts. That is the alert that would have given you notice, and it is the one most likely to be filtered out.</p>
<p><strong>The ceiling is not in any response.</strong> There is no field on the Trunk resource that reports its calls-per-second allowance. It is set by Twilio, changed through Support, and lives in a ticket rather than in the API, which means any automated check has to be told what it is.</p>""",
"steps": [
 {"h": "Sweep the alerts at both levels and count 32001 and 32012 separately",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, then the same at <code>LogLevel=warning</code>, following <code>meta.next_page_url</code> and merging on <code>sid</code>. Keeping the two codes apart matters: 32001 is calls you lost, 32012 is the warning you were given first.</p>"""},
 {"h": "Page the calls over the same window",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>, which on this API is a path rather than an absolute URL. Keep the window short. A day of calls at second resolution is the point; a month of them is a slow way to compute the same peak.</p>"""},
 {"h": "Bucket start_time to the second, not to the minute",
  "body": """<p><code>start_time</code> comes back in RFC 2822 form. Parse it, floor it to the second, and count. Bucketing to the minute divides the peak by sixty and is the single step that turns this investigation into a dead end &mdash; the numbers still look plausible, they are just answering a different question.</p>"""},
 {"h": "Compare the peak against the ceiling, and against the mean",
  "body": """<p>The peak over the ceiling is calls you lost. The peak equal to the ceiling means the next batch spills. A peak several times the mean rate is worth reporting even when it clears the ceiling, because it is the shape that will breach it as soon as the list grows, and it is invisible in every average anyone will quote at you.</p>"""},
 {"h": "Flatten the burst or raise the ceiling, then re-measure",
  "body": """<p>Rate-limit the dialer to a value under the ceiling, spread the traffic across additional trunks, or ask Twilio Support to raise the trunk's CPS. Then run this again over a window containing a real campaign; a peak measured on a quiet afternoon confirms nothing.</p>"""},
],
"verify": """<p>Re-run over a window that contains a campaign. The peak should sit under the ceiling and the alert count should be zero.</p>
<pre><code class="language-bash">python3 twilio_trunk_cps_audit.py --days 1 --cps 10
# peak 7 call(s) in one second against a ceiling of 10, 0 CPS alert(s)</code></pre>""",
"code_intro": "One pair of alert sweeps, one paginated pass over the calls, and no per-trunk requests at all, because the Calls resource does not record which trunk carried a call. Everything is a GET and an API Key with read access is enough. The pure part is three small functions: one parses a timestamp to a whole second, one folds a list of timestamps into a burst profile, and one judges that profile against a ceiling you supply. Splitting them that way is what lets the second-resolution bucketing be tested on its own, which is where this check is easiest to get quietly wrong.",
"py_file": "twilio_trunk_cps_audit.py",
"py": '''"""Report whether outbound call bursts are hitting a Twilio trunk CPS ceiling.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import datetime as dt
import email.utils
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_trunk_cps_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"
TRUNKING = "https://trunking.twilio.com/v1"

CPS_EXCEEDED = 32001
CPS_WARNING = 32012


def second_bucket(value):
    """Floor a Twilio timestamp to a whole UTC second, as an ISO string.

    start_time comes back in RFC 2822 form on the 2010-04-01 API. ISO is
    accepted too so the same function can be pointed at other resources. An
    unparseable value returns "" rather than a guess, because a timestamp
    silently bucketed to the epoch would drag the peak somewhere meaningless.
    """
    v = str(value or "").strip()
    if not v:
        return ""
    parsed = None
    if "," in v:
        try:
            parsed = email.utils.parsedate_to_datetime(v)
        except (TypeError, ValueError):
            parsed = None
    if parsed is None:
        try:
            parsed = dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def burst_profile(timestamps):
    """Fold call start times into the shape a CPS ceiling is enforced against.

    Returns a dict with the total parsed, the busiest one-second bucket and when
    it was, how many seconds carried any traffic at all, and the span from first
    call to last. Bucketing to the minute instead would divide the peak by sixty
    and produce a reassuring number that answers a different question.
    """
    buckets = {}
    for t in timestamps:
        key = second_bucket(t)
        if not key:
            continue
        buckets[key] = buckets.get(key, 0) + 1
    if not buckets:
        return {"calls": 0, "peak": 0, "at": "", "active_seconds": 0, "span_seconds": 0}
    at = max(sorted(buckets), key=lambda k: buckets[k])
    keys = sorted(buckets)
    first = dt.datetime.strptime(keys[0], "%Y-%m-%dT%H:%M:%SZ")
    last = dt.datetime.strptime(keys[-1], "%Y-%m-%dT%H:%M:%SZ")
    return {"calls": sum(buckets.values()),
            "peak": buckets[at],
            "at": at,
            "active_seconds": len(buckets),
            "span_seconds": int((last - first).total_seconds()) + 1}


def verdict(profile, ceiling, alerts=0, warnings=0, burst_ratio=4):
    """Judge a burst profile against a CPS ceiling. Pure, so it tests offline.

    ceiling is the trunk's calls-per-second allowance. No read API reports it,
    so it is supplied by whoever runs this rather than discovered.

    Returns (state, detail).
    """
    calls = profile.get("calls", 0)
    if not calls:
        return ("no-calls", "no calls with a readable start_time in this window.")

    peak = profile.get("peak", 0)
    span = max(profile.get("span_seconds", 0), 1)
    mean = calls / float(span)

    if alerts:
        return ("shedding",
                "%d call(s) rejected with %d: the peak was %d call(s) in the "
                "second at %s against a ceiling of %d, while the mean over the "
                "window was %.2f per second and hid all of it."
                % (alerts, CPS_EXCEEDED, peak, profile.get("at"), ceiling, mean))

    if peak > ceiling:
        return ("over-ceiling",
                "peak of %d call(s) at %s is above the ceiling of %d with no "
                "%d alert in the window, so either the ceiling is higher than "
                "the value given here or the calls were spread across trunks."
                % (peak, profile.get("at"), ceiling, CPS_EXCEEDED))

    if peak == ceiling:
        return ("at-ceiling",
                "peak of %d call(s) at %s sits exactly on the ceiling: nothing "
                "was lost this time and a batch one call larger will be."
                % (peak, profile.get("at")))

    if warnings:
        return ("warned",
                "%d %d warning(s) at LogLevel=warning with a peak of %d against "
                "a ceiling of %d. That is the notice that comes before the "
                "shedding, and it is the one an error-only sweep drops."
                % (warnings, CPS_WARNING, peak, ceiling))

    if peak >= burst_ratio * mean and peak >= 2:
        return ("bursty",
                "peak of %d call(s) at %s against a mean of %.2f per second: "
                "under the ceiling of %d today, but the traffic arrives in "
                "bursts and no hourly average will ever show it."
                % (peak, profile.get("at"), mean, ceiling))

    return ("within-ceiling",
            "peak of %d call(s) in one second against a ceiling of %d, mean "
            "%.2f per second over %d second(s)."
            % (peak, ceiling, mean, span))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_calls(session, account, since, limit):
    """Page the calls. next_page_uri here is a path, and there is no ErrorCode
    filter on this resource, so everything is bucketed client-side."""
    url = "%s/Accounts/%s/Calls.json" % (BASE, account)
    params = {"StartTime>=": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        body = get(session, url, **params)
        out.extend(body.get("calls", []))
        nxt = body.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def sweep_alerts(session, since, limit, levels):
    """Both log levels, merged on sid.

    32001 is an error and 32012 is a warning. A sweep hard-coded to the error
    level sees the calls you lost and never the warning that preceded them.
    """
    seen = {}
    for level in levels:
        url = MONITOR + "/Alerts"
        params = {"LogLevel": level, "StartDate": since, "PageSize": 1000}
        got = 0
        while url and got < limit:
            page = get(session, url, **params)
            for a in page.get("alerts", []):
                seen.setdefault(a.get("sid"), a)
                got += 1
            url = (page.get("meta") or {}).get("next_page_url")
            params = {}
    return list(seen.values())


def count_trunks(session):
    """How many trunks the traffic could be spread across. One paginated read."""
    url = TRUNKING + "/Trunks"
    params = {"PageSize": 100}
    total = 0
    while url:
        page = get(session, url, **params)
        total += len(page.get("trunks", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=1,
                    help="window to measure; keep it short, this reads every call")
    ap.add_argument("--cps", type=int, default=1,
                    help="the trunk's calls-per-second ceiling, which no read API "
                         "reports: use the value Twilio gave you")
    ap.add_argument("--max-calls", type=int, default=20000,
                    help="stop after this many calls")
    ap.add_argument("--errors-only", action="store_true",
                    help="skip the warning level, which drops 32012 entirely")
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

    alerts = sweep_alerts(session, since, 10000, levels)
    exceeded = [a for a in alerts
                if str(a.get("error_code") or "").strip() == str(CPS_EXCEEDED)]
    warned = [a for a in alerts
              if str(a.get("error_code") or "").strip() == str(CPS_WARNING)]

    calls = list_calls(session, account, since, args.max_calls)
    profile = burst_profile(c.get("start_time") for c in calls)
    state, detail = verdict(profile, args.cps, len(exceeded), len(warned))

    log.info("%d call(s) over %d day(s) across %d trunk(s)",
             len(calls), days, count_trunks(session))
    if state in ("within-ceiling", "no-calls"):
        log.info("%-15s %s", state, detail)
        return 0

    log.warning("%-15s %s", state, detail)
    log.warning("  repair: rate-limit the dialer below %d call(s) per second, "
                "spread the campaign across additional trunks, or ask Twilio "
                "Support to raise the trunk's CPS", args.cps)
    log.warning("  measure again over a window containing a real campaign: a "
                "peak taken on a quiet afternoon confirms nothing")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-trunk-cps-audit.mjs",
"js": '''/**
 * Report whether outbound call bursts are hitting a Twilio trunk CPS ceiling.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';
const TRUNKING = 'https://trunking.twilio.com/v1';

const CPS_EXCEEDED = 32001;
const CPS_WARNING = 32012;

/**
 * Floor a Twilio timestamp to a whole UTC second, as an ISO string. start_time
 * comes back in RFC 2822 form on the 2010-04-01 API; ISO is accepted too. An
 * unparseable value returns '' rather than a guess, because a timestamp
 * silently bucketed to the epoch would drag the peak somewhere meaningless.
 */
export function secondBucket(value) {
  const v = String(value ?? '').trim();
  if (!v) return '';
  const ms = Date.parse(v);
  if (Number.isNaN(ms)) return '';
  return new Date(Math.floor(ms / 1000) * 1000).toISOString().replace('.000Z', 'Z');
}

/**
 * Fold call start times into the shape a CPS ceiling is enforced against.
 * Bucketing to the minute instead would divide the peak by sixty and produce a
 * reassuring number that answers a different question.
 */
export function burstProfile(timestamps) {
  const buckets = new Map();
  for (const t of timestamps) {
    const key = secondBucket(t);
    if (!key) continue;
    buckets.set(key, (buckets.get(key) ?? 0) + 1);
  }
  if (buckets.size === 0) {
    return { calls: 0, peak: 0, at: '', active_seconds: 0, span_seconds: 0 };
  }
  const keys = [...buckets.keys()].sort();
  let at = keys[0];
  for (const k of keys) if (buckets.get(k) > buckets.get(at)) at = k;
  const first = Date.parse(keys[0]);
  const last = Date.parse(keys[keys.length - 1]);
  let calls = 0;
  for (const n of buckets.values()) calls += n;
  return {
    calls,
    peak: buckets.get(at),
    at,
    active_seconds: buckets.size,
    span_seconds: Math.round((last - first) / 1000) + 1,
  };
}

/**
 * Judge a burst profile against a CPS ceiling. `ceiling` is supplied rather than
 * discovered: no read API reports a trunk's calls-per-second allowance. Pure.
 * Returns [state, detail].
 */
export function verdict(profile, ceiling, alerts = 0, warnings = 0, burstRatio = 4) {
  const calls = profile.calls ?? 0;
  if (!calls) return ['no-calls', 'no calls with a readable start_time in this window.'];

  const peak = profile.peak ?? 0;
  const span = Math.max(profile.span_seconds ?? 0, 1);
  const mean = calls / span;

  if (alerts) {
    return ['shedding',
      `${alerts} call(s) rejected with ${CPS_EXCEEDED}: the peak was ${peak} ` +
      `call(s) in the second at ${profile.at} against a ceiling of ${ceiling}, ` +
      `while the mean over the window was ${mean.toFixed(2)} per second and hid ` +
      'all of it.'];
  }

  if (peak > ceiling) {
    return ['over-ceiling',
      `peak of ${peak} call(s) at ${profile.at} is above the ceiling of ` +
      `${ceiling} with no ${CPS_EXCEEDED} alert in the window, so either the ` +
      'ceiling is higher than the value given here or the calls were spread ' +
      'across trunks.'];
  }

  if (peak === ceiling) {
    return ['at-ceiling',
      `peak of ${peak} call(s) at ${profile.at} sits exactly on the ceiling: ` +
      'nothing was lost this time and a batch one call larger will be.'];
  }

  if (warnings) {
    return ['warned',
      `${warnings} ${CPS_WARNING} warning(s) at LogLevel=warning with a peak of ` +
      `${peak} against a ceiling of ${ceiling}. That is the notice that comes ` +
      'before the shedding, and it is the one an error-only sweep drops.'];
  }

  if (peak >= burstRatio * mean && peak >= 2) {
    return ['bursty',
      `peak of ${peak} call(s) at ${profile.at} against a mean of ` +
      `${mean.toFixed(2)} per second: under the ceiling of ${ceiling} today, but ` +
      'the traffic arrives in bursts and no hourly average will ever show it.'];
  }

  return ['within-ceiling',
    `peak of ${peak} call(s) in one second against a ceiling of ${ceiling}, mean ` +
    `${mean.toFixed(2)} per second over ${span} second(s).`];
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

export async function listCalls(auth, account, since, limit) {
  let url = `${BASE}/Accounts/${account}/Calls.json`;
  let params = { 'StartTime>=': since, PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const body = await get(auth, url, params);
    out.push(...(body.calls ?? []));
    url = body.next_page_uri ? HOST + body.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Both log levels, merged on sid: 32001 is an error and 32012 is a warning. */
export async function sweepAlerts(auth, since, limit, levels) {
  const seen = new Map();
  for (const level of levels) {
    let url = `${MONITOR}/Alerts`;
    let params = { LogLevel: level, StartDate: since, PageSize: 1000 };
    let got = 0;
    while (url && got < limit) {
      const page = await get(auth, url, params);
      for (const a of page.alerts ?? []) {
        if (!seen.has(a.sid)) seen.set(a.sid, a);
        got += 1;
      }
      url = page.meta?.next_page_url ?? null;
      params = {};
    }
  }
  return [...seen.values()];
}

async function countTrunks(auth) {
  let url = `${TRUNKING}/Trunks`;
  let params = { PageSize: 100 };
  let total = 0;
  while (url) {
    const page = await get(auth, url, params);
    total += (page.trunks ?? []).length;
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return total;
}

function flagValue(name, fallback) {
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
  const days = Math.min(flagValue('--days', 1), 30);
  const ceiling = flagValue('--cps', 1);
  const maxCalls = flagValue('--max-calls', 20000);
  const levels = process.argv.includes('--errors-only') ? ['error'] : ['error', 'warning'];
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await sweepAlerts(auth, since, 10000, levels);
  const code = (a) => String(a.error_code ?? '').trim();
  const exceeded = alerts.filter((a) => code(a) === String(CPS_EXCEEDED));
  const warned = alerts.filter((a) => code(a) === String(CPS_WARNING));

  const calls = await listCalls(auth, account, since, maxCalls);
  const profile = burstProfile(calls.map((c) => c.start_time));
  const [state, detail] = verdict(profile, ceiling, exceeded.length, warned.length);

  console.log(`${calls.length} call(s) over ${days} day(s) across ` +
              `${await countTrunks(auth)} trunk(s)`);
  if (state === 'within-ceiling' || state === 'no-calls') {
    console.log(`${state.padEnd(15)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(15)} ${detail}`);
  console.warn(`  repair: rate-limit the dialer below ${ceiling} call(s) per ` +
               'second, spread the campaign across additional trunks, or ask ' +
               "Twilio Support to raise the trunk's CPS");
  console.warn('  measure again over a window containing a real campaign: a peak ' +
               'taken on a quiet afternoon confirms nothing');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things have to be pinned here or the whole note is worthless. The bucketing has to be to the second, which the fixture proves by putting six calls in one second and one in the next and expecting a peak of six rather than seven. And a burst that clears the ceiling still has to be reported, because a peak four times the mean is a campaign that will breach the limit the week the list grows.",
"test_py_file": "test_twilio_trunk_cps_audit.py",
"test_py": '''from twilio_trunk_cps_audit import burst_profile, second_bucket, verdict

# Six starts inside one second, one in the next. The peak is six.
BURST = ["Tue, 31 Aug 2010 20:36:28 +0000"] * 6 + ["Tue, 31 Aug 2010 20:36:29 +0000"]


def test_rfc_2822_start_time_is_floored_to_the_second():
    assert second_bucket("Tue, 31 Aug 2010 20:36:28 +0000") == "2010-08-31T20:36:28Z"


def test_iso_timestamps_and_offsets_normalise_to_utc():
    assert second_bucket("2010-08-31T21:36:28+01:00") == "2010-08-31T20:36:28Z"
    assert second_bucket("2010-08-31T20:36:28Z") == "2010-08-31T20:36:28Z"


def test_an_unparseable_timestamp_is_dropped_rather_than_guessed():
    # Bucketed to the epoch it would stretch the span and flatten the peak.
    assert second_bucket("last tuesday") == ""
    assert second_bucket(None) == ""


def test_the_peak_is_the_busiest_single_second():
    p = burst_profile(BURST)
    assert p["calls"] == 7
    assert p["peak"] == 6
    assert p["at"] == "2010-08-31T20:36:28Z"
    assert p["active_seconds"] == 2
    assert p["span_seconds"] == 2


def test_an_empty_window_has_no_peak_and_no_span():
    p = burst_profile([])
    assert p == {"calls": 0, "peak": 0, "at": "", "active_seconds": 0,
                 "span_seconds": 0}
    assert verdict(p, 10)[0] == "no-calls"


def test_alerts_outrank_everything_and_quote_the_hiding_mean():
    state, detail = verdict(burst_profile(BURST), 5, alerts=44)
    assert state == "shedding"
    assert "44 call(s) rejected" in detail
    assert "3.50 per second" in detail


def test_a_peak_on_the_ceiling_is_its_own_state():
    state, detail = verdict(burst_profile(BURST), 6)
    assert state == "at-ceiling"
    assert "one call larger" in detail


def test_a_peak_above_the_ceiling_with_no_alert_says_so():
    state, detail = verdict(burst_profile(BURST), 4)
    assert state == "over-ceiling"
    assert "spread across trunks" in detail


def test_the_warning_level_code_is_reported_before_anything_is_lost():
    state, detail = verdict(burst_profile(BURST), 20, warnings=3)
    assert state == "warned"
    assert "error-only sweep" in detail


def test_a_burst_well_under_the_ceiling_is_still_the_finding():
    # 6 in one second against a mean of 3.5 is not four times the mean, so
    # stretch the window: the same six calls over a quieter minute are.
    quiet = BURST + ["Tue, 31 Aug 2010 20:37:%02d +0000" % s for s in range(30, 50)]
    state, detail = verdict(burst_profile(quiet), 50)
    assert state == "bursty"
    assert "no hourly average" in detail


def test_a_flat_stream_under_the_ceiling_is_clean():
    flat = ["Tue, 31 Aug 2010 20:36:%02d +0000" % s for s in range(10, 40)]
    state, _ = verdict(burst_profile(flat), 5)
    assert state == "within-ceiling"
''',
"test_js_file": "twilio-trunk-cps-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { burstProfile, secondBucket, verdict } from './twilio-trunk-cps-audit.mjs';

// Six starts inside one second, one in the next. The peak is six.
const BURST = [
  ...Array(6).fill('Tue, 31 Aug 2010 20:36:28 +0000'),
  'Tue, 31 Aug 2010 20:36:29 +0000',
];

const pad = (n) => String(n).padStart(2, '0');

test('rfc 2822 start_time is floored to the second', () => {
  assert.equal(secondBucket('Tue, 31 Aug 2010 20:36:28 +0000'), '2010-08-31T20:36:28Z');
});

test('iso timestamps and offsets normalise to utc', () => {
  assert.equal(secondBucket('2010-08-31T21:36:28+01:00'), '2010-08-31T20:36:28Z');
  assert.equal(secondBucket('2010-08-31T20:36:28Z'), '2010-08-31T20:36:28Z');
});

test('an unparseable timestamp is dropped rather than guessed', () => {
  assert.equal(secondBucket('last tuesday'), '');
  assert.equal(secondBucket(null), '');
});

test('the peak is the busiest single second', () => {
  const p = burstProfile(BURST);
  assert.equal(p.calls, 7);
  assert.equal(p.peak, 6);
  assert.equal(p.at, '2010-08-31T20:36:28Z');
  assert.equal(p.active_seconds, 2);
  assert.equal(p.span_seconds, 2);
});

test('an empty window has no peak and no span', () => {
  const p = burstProfile([]);
  assert.deepEqual(p, { calls: 0, peak: 0, at: '', active_seconds: 0, span_seconds: 0 });
  assert.equal(verdict(p, 10)[0], 'no-calls');
});

test('alerts outrank everything and quote the hiding mean', () => {
  const [state, detail] = verdict(burstProfile(BURST), 5, 44);
  assert.equal(state, 'shedding');
  assert.match(detail, /44 call\\(s\\) rejected/);
  assert.match(detail, /3.50 per second/);
});

test('a peak on the ceiling is its own state', () => {
  const [state, detail] = verdict(burstProfile(BURST), 6);
  assert.equal(state, 'at-ceiling');
  assert.match(detail, /one call larger/);
});

test('a peak above the ceiling with no alert says so', () => {
  const [state, detail] = verdict(burstProfile(BURST), 4);
  assert.equal(state, 'over-ceiling');
  assert.match(detail, /spread across trunks/);
});

test('the warning level code is reported before anything is lost', () => {
  const [state, detail] = verdict(burstProfile(BURST), 20, 0, 3);
  assert.equal(state, 'warned');
  assert.match(detail, /error-only sweep/);
});

test('a burst well under the ceiling is still the finding', () => {
  const quiet = [...BURST];
  for (let s = 30; s < 50; s += 1) quiet.push(`Tue, 31 Aug 2010 20:37:${pad(s)} +0000`);
  const [state, detail] = verdict(burstProfile(quiet), 50);
  assert.equal(state, 'bursty');
  assert.match(detail, /no hourly average/);
});

test('a flat stream under the ceiling is clean', () => {
  const flat = [];
  for (let s = 10; s < 40; s += 1) flat.push(`Tue, 31 Aug 2010 20:36:${pad(s)} +0000`);
  assert.equal(verdict(burstProfile(flat), 5)[0], 'within-ceiling');
});
''',
"faq": [
 ("Why does the script need me to supply the CPS ceiling?",
  "Because no read API reports it. There is no field on the Trunk resource for a calls-per-second allowance; it is set by Twilio and changed through Support, so it lives in a ticket rather than in a response. Inventing a default would be worse than asking, so the script takes it as an argument and prints it in every line it writes."),
 ("Why bucket to the second rather than the minute?",
  "Because the limit is enforced per second. A minute bucket divides a peak by sixty and returns a number that looks fine, which is the precise reason this problem survives investigation. Every graph in every console aggregates coarser than the thing being enforced, so the bucketing has to be done deliberately."),
 ("What is 32012 and why does the sweep look for it?",
  "It is the CPS warning, logged at LogLevel=warning rather than error. It arrives before calls start being rejected, which makes it the most useful alert in this whole note and the one most likely to be filtered out by a monitor built around errors. The script counts it separately from 32001 so you can tell a warning from a loss."),
 ("Why report a burst that is under the ceiling?",
  "Because a peak several times the mean is a shape, and shapes are stable while volumes are not. A dialer that peaks at four times its average is under the limit only until the list grows, and by then the failures will be attributed to the list rather than to the ceiling. Reporting the shape is how you get the warning before the campaign."),
 ("Can the script slow the dialer down or ask for a CPS increase?",
  "Neither. It holds a read-only credential, it makes GET requests, and it prints what it found. Rate limits belong in the dialer, where the batch is actually built, and a CPS increase is a conversation with Twilio Support rather than an API call anything here could make."),
],
"related": [
 ("/twilio/sip-infrastructure-communication-error-32011/", "Twilio cannot reach your SIP infrastructure"),
 ("/twilio/trunk-missing-disaster-recovery-url/", "A SIP trunk with no disaster recovery URL"),
 ("/twilio/outbound-call-failure-rate-spike/", "Outbound calls quietly failing more often"),
],
"citations": [CITE_32001, CITE_TRUNK, CITE_TRUNK_TROUBLE, CITE_ALERT],
},

{
"slug": "carrier-blocked-caller-id-32017",
"title": "A carrier blocks your caller ID and 32017 is the only notice",
"description": "32017 is a terminating carrier refusing a number on reputation. The score is built from answer rate and call duration, both of which you can read.",
"h1": "a carrier blocks your caller ID and 32017 is the only notice",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 32017", "carrier blocked call caller id",
             "twilio number flagged spam likely", "free caller registry twilio",
             "twilio outbound number reputation"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing on your side changed and one of your numbers stopped working. <code>32017 PSTN: Carrier blocked call due to calling number</code>, clustered on one <code>from</code> and, at first, one carrier. There is no setting to correct and no ticket to file with Twilio, because the decision was made by an analytics provider on the terminating carrier's side using data you never see &mdash; except that you do see most of it, in your own call records, in the answer rate and the mean duration that earned the score.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts</code> at <strong>both</strong> <code>LogLevel=error</code> and <code>LogLevel=warning</code> and keep <code>error_code</code> <code>32017</code>. Resolve each alert's <code>resource_sid</code> with <code>GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json</code> and group by <code>from</code>: the blocks concentrate on one number, which is the number that has the reputation problem.</p>
<p>Then read the traffic that produced the score. <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, tally per <code>from</code>, and compute two numbers: the share of attempts that reached <code>completed</code>, and the mean <code>duration</code> of the ones that did. A number placing many short unanswered calls is being scored on exactly that, and the same two figures tell you which of your other numbers is next.</p>""",
"problem": """<p>Every other failure in this section is yours to fix. This one is a judgement made about you by a third party, delivered as a rejection, with no appeal path in the API and no explanation attached. The block is at the terminating carrier, so it can affect one carrier's subscribers and not another's, which is why it presents as an intermittent problem for days before anyone notices it is entirely one network.</p>
<p>And the natural reaction makes it worse. A number stops connecting, so traffic is moved to another number, which then places the same volume of the same short calls and earns the same score a few weeks later. Rotating numbers without changing the behaviour that produced the score converts one blocked number into several, and the failure rate on each one looks like bad luck rather than a pattern.</p>""",
"why": """<p><strong>The score is built from call outcomes, not from content.</strong> Answer rate, call duration and complaint volume are what analytics providers weigh. A number that places hundreds of calls a day which ring out or are hung up in five seconds looks like a nuisance dialer, because at the level of the data it is indistinguishable from one.</p>
<p><strong>Twilio is not the one blocking it.</strong> There is no setting in the console, no field on the number, and nothing Twilio can change on request, because the decision belongs to the terminating carrier and its analytics partner. The registration paths that exist are outside Twilio entirely, which is why nobody's first day of searching finds them.</p>
<p><strong>The 32017 is the end of the process, not the start.</strong> Before a number is blocked outright it is usually labelled, and a labelled number is answered less, which lowers its answer rate further. By the time the error code appears, the underlying metrics have been bad for weeks and are visible in call records nobody was aggregating.</p>
<p><strong>Rotation spreads it.</strong> Moving the same traffic to a fresh number restores service for a while and starts the same clock. Without looking at answer rate and duration per number, there is no way to tell a number that is next from one that is fine.</p>""",
"steps": [
 {"h": "Sweep alerts at both levels and keep 32017",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, then the same at <code>LogLevel=warning</code>, following <code>meta.next_page_url</code> and merging on <code>sid</code>. Sweeping one level is the habit that leaves voice accounts reading clean, and it costs one extra paginated read to avoid.</p>"""},
 {"h": "Resolve each alert to the number it was raised against",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json</code> on the alert's <code>resource_sid</code>, then group by <code>from</code>. Cache by SID; a block produces many alerts against a modest set of calls. The grouping is the diagnosis: 32017 spread evenly across every number is a different story from 32017 on one.</p>"""},
 {"h": "Tally attempts, completions and answered seconds per number",
  "body": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime&gt;=YYYY-MM-DD</code> over the same window and bucket by <code>from</code>. Count every terminal outcome as an attempt, count <code>completed</code> separately, and sum <code>duration</code> only over the completed ones &mdash; averaging duration across calls that were never answered produces a number that means nothing.</p>"""},
 {"h": "Read the two ratios rather than the raw counts",
  "body": """<p>Answer rate is completions over attempts. Mean answered duration is seconds over completions. A number low on both is being scored the way a nuisance dialer is scored, whether or not it has been blocked yet. Set a floor on attempts before judging either, because three calls cannot support a rate.</p>"""},
 {"h": "Register the numbers and change the traffic, then re-measure",
  "body": """<p>Register at <code>freecallerregistry.com</code>, and for T-Mobile at <code>portal.firstorion.com</code>. Then fix the behaviour: fewer attempts per number, call at hours people answer, and raise mean duration. Re-run this monthly &mdash; the metrics move slowly, and a number recovers or degrades over weeks rather than days.</p>"""},
],
"verify": """<p>Re-run after a month of changed traffic. The blocked count should be zero and no number should report <code>at-risk</code>.</p>
<pre><code class="language-bash">python3 twilio_caller_id_reputation_audit.py --days 30
# 6 number(s), 0 blocked, 0 at risk</code></pre>""",
"code_intro": "Two alert sweeps, one cached GET per alerted call, and one paginated pass over the window's calls. All GETs; an API Key with read access is enough. Both halves of the thinking are pure: one function folds a list of call records into per-number counters, and one turns those counters into a verdict. Keeping the tally pure matters more than usual here, because the mistake that ruins this check is averaging duration over calls that were never answered, and that is a mistake you want visible in a test rather than buried in a loop.",
"py_file": "twilio_caller_id_reputation_audit.py",
"py": '''"""Report Twilio numbers blocked with 32017 and the ones scoring like them.

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
log = logging.getLogger("twilio_caller_id_reputation_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

CARRIER_BLOCKED = 32017

# A call that reached one of these was attempted and finished. Anything still in
# flight is excluded so a window that ends mid-campaign does not depress the rate.
TERMINAL = {"completed", "busy", "no-answer", "failed", "canceled"}


def seconds(value):
    """Duration as an integer. The API returns it as a string, and absent on
    calls that never connected."""
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def tally(calls, blocked=None):
    """Fold call records into per-caller-ID counters. Pure, so it tests offline.

    blocked maps a number to how many 32017 alerts were raised against it.

    Answered seconds are summed only over completed calls. Averaging duration
    across calls that rang out gives every busy dialer a flattering number and
    is the mistake that makes this whole check useless.
    """
    out = {}
    for c in calls or []:
        frm = str(c.get("from") or "").strip()
        status = str(c.get("status") or "").strip().lower()
        if not frm or status not in TERMINAL:
            continue
        row = out.setdefault(frm, {"attempts": 0, "completed": 0,
                                   "answered_seconds": 0, "blocked": 0})
        row["attempts"] += 1
        if status == "completed":
            row["completed"] += 1
            row["answered_seconds"] += seconds(c.get("duration"))
    for number, count in (blocked or {}).items():
        row = out.setdefault(str(number).strip(),
                             {"attempts": 0, "completed": 0,
                              "answered_seconds": 0, "blocked": 0})
        row["blocked"] = count
    return out


def verdict(stats, min_attempts=20, min_answer_rate=0.30, min_mean_duration=30):
    """Judge one caller ID's reputation profile. Pure.

    The thresholds are defaults, not physics: analytics providers do not publish
    theirs. They are set where a legitimate outbound operation is comfortably
    clear and a short-call dialer is not.

    Returns (state, detail).
    """
    attempts = stats.get("attempts", 0)
    completed = stats.get("completed", 0)
    rate = (completed / float(attempts)) if attempts else 0.0
    mean = (stats.get("answered_seconds", 0) / float(completed)) if completed else 0.0
    shape = ("%d of %d answered (%.0f%%), mean answered call %.0fs"
             % (completed, attempts, rate * 100, mean))

    if stats.get("blocked"):
        return ("blocked",
                "%d call(s) refused with %d by a terminating carrier: %s. The "
                "block is carrier side, so there is nothing to change on the "
                "number itself." % (stats["blocked"], CARRIER_BLOCKED, shape))

    if attempts < min_attempts:
        return ("thin",
                "%d attempt(s) is too little traffic to read a reputation from. "
                "%s" % (attempts, shape))

    low_rate = rate < min_answer_rate
    short = mean < min_mean_duration
    if low_rate and short:
        return ("at-risk",
                "%s. Low answer rate and short answered calls together are the "
                "profile carrier analytics score as a nuisance dialer, and this "
                "number has not been blocked yet." % shape)
    if short:
        return ("short-calls",
                "%s. Mean answered duration under %ds is the single metric most "
                "likely to pull a score down." % (shape, min_mean_duration))
    if low_rate:
        return ("low-answer",
                "%s. An answer rate under %.0f%% suggests the number is already "
                "being labelled on some handsets, which lowers it further."
                % (shape, min_answer_rate * 100))

    return ("healthy", shape)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_calls(session, account, since, limit):
    """Page the calls. next_page_uri here is a path, not an absolute URL, and
    this resource has no ErrorCode filter, so the bucketing is client-side."""
    url = "%s/Accounts/%s/Calls.json" % (BASE, account)
    params = {"StartTime>=": since, "PageSize": 1000}
    out = []
    while url and len(out) < limit:
        body = get(session, url, **params)
        out.extend(body.get("calls", []))
        nxt = body.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def sweep_alerts(session, since, limit, levels):
    """Both log levels, merged on sid.

    Several voice failures are logged at warning rather than error. Sweeping the
    error level alone is how a voice account reads clean while numbers are being
    refused.
    """
    seen = {}
    for level in levels:
        url = MONITOR + "/Alerts"
        params = {"LogLevel": level, "StartDate": since, "PageSize": 1000}
        got = 0
        while url and got < limit:
            page = get(session, url, **params)
            for a in page.get("alerts", []):
                seen.setdefault(a.get("sid"), a)
                got += 1
            url = (page.get("meta") or {}).get("next_page_url")
            params = {}
    return list(seen.values())


def blocked_numbers(session, account, alerts):
    """Resolve 32017 alerts to the caller ID each was raised against."""
    cache = {}
    counts = {}
    for a in alerts:
        sid = str(a.get("resource_sid") or "")
        if not sid.startswith("CA"):
            continue
        if sid not in cache:
            cache[sid] = get(session, "%s/Accounts/%s/Calls/%s.json"
                             % (BASE, account, sid))
        frm = str(cache[sid].get("from") or "").strip()
        if frm:
            counts[frm] = counts.get(frm, 0) + 1
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="window to measure; reputation moves over weeks")
    ap.add_argument("--max-calls", type=int, default=20000,
                    help="stop after this many calls")
    ap.add_argument("--min-attempts", type=int, default=20,
                    help="below this a number has too little traffic to judge")
    ap.add_argument("--errors-only", action="store_true",
                    help="skip the warning level, which will under-report")
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

    alerts = sweep_alerts(session, since, 10000, levels)
    hits = [a for a in alerts
            if str(a.get("error_code") or "").strip() == str(CARRIER_BLOCKED)]
    blocked = blocked_numbers(session, account, hits)

    calls = list_calls(session, account, since, args.max_calls)
    rows = tally(calls, blocked)
    if not rows:
        log.info("no outbound calls with a caller ID in the last %d day(s)", days)
        return 0

    bad = 0
    at_risk = 0
    for number in sorted(rows):
        state, detail = verdict(rows[number], args.min_attempts)
        line = "%-12s %s  %s" % (state, number, detail)
        if state in ("healthy", "thin"):
            log.info(line)
            continue
        bad += 1
        if state != "blocked":
            at_risk += 1
        log.warning(line)

    if bad:
        log.warning("  repair: register the numbers at freecallerregistry.com "
                    "and, for T-Mobile, portal.firstorion.com")
        log.warning("  then change the traffic: fewer attempts per number, "
                    "call at hours people answer, raise mean duration. Rotating "
                    "to a fresh number without that earns the same score again")

    log.info("%d number(s), %d blocked, %d at risk",
             len(rows), len(blocked), at_risk)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-caller-id-reputation-audit.mjs",
"js": '''/**
 * Report Twilio numbers blocked with 32017 and the ones scoring like them.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const CARRIER_BLOCKED = 32017;

// A call that reached one of these was attempted and finished. Anything still in
// flight is excluded so a window ending mid-campaign does not depress the rate.
const TERMINAL = new Set(['completed', 'busy', 'no-answer', 'failed', 'canceled']);

/** Duration as an integer. The API returns it as a string. */
export function seconds(value) {
  const n = Number.parseInt(String(value ?? '0').trim(), 10);
  return Number.isNaN(n) ? 0 : n;
}

/**
 * Fold call records into per-caller-ID counters. `blocked` maps a number to how
 * many 32017 alerts were raised against it. Answered seconds are summed only
 * over completed calls: averaging duration across calls that rang out gives
 * every busy dialer a flattering number. Pure.
 */
export function tally(calls, blocked = {}) {
  const out = {};
  const row = (n) => {
    if (!out[n]) out[n] = { attempts: 0, completed: 0, answered_seconds: 0, blocked: 0 };
    return out[n];
  };
  for (const c of calls ?? []) {
    const frm = String(c.from ?? '').trim();
    const status = String(c.status ?? '').trim().toLowerCase();
    if (!frm || !TERMINAL.has(status)) continue;
    const r = row(frm);
    r.attempts += 1;
    if (status === 'completed') {
      r.completed += 1;
      r.answered_seconds += seconds(c.duration);
    }
  }
  for (const [number, count] of Object.entries(blocked ?? {})) {
    row(String(number).trim()).blocked = count;
  }
  return out;
}

/**
 * Judge one caller ID's reputation profile. The thresholds are defaults, not
 * physics: analytics providers do not publish theirs. Pure. Returns
 * [state, detail].
 */
export function verdict(stats, minAttempts = 20, minAnswerRate = 0.30,
                        minMeanDuration = 30) {
  const attempts = stats.attempts ?? 0;
  const completed = stats.completed ?? 0;
  const rate = attempts ? completed / attempts : 0;
  const mean = completed ? (stats.answered_seconds ?? 0) / completed : 0;
  const shape = `${completed} of ${attempts} answered (${Math.round(rate * 100)}%), ` +
                `mean answered call ${Math.round(mean)}s`;

  if (stats.blocked) {
    return ['blocked',
      `${stats.blocked} call(s) refused with ${CARRIER_BLOCKED} by a terminating ` +
      `carrier: ${shape}. The block is carrier side, so there is nothing to ` +
      'change on the number itself.'];
  }

  if (attempts < minAttempts) {
    return ['thin',
      `${attempts} attempt(s) is too little traffic to read a reputation from. ${shape}`];
  }

  const lowRate = rate < minAnswerRate;
  const short = mean < minMeanDuration;
  if (lowRate && short) {
    return ['at-risk',
      `${shape}. Low answer rate and short answered calls together are the ` +
      'profile carrier analytics score as a nuisance dialer, and this number ' +
      'has not been blocked yet.'];
  }
  if (short) {
    return ['short-calls',
      `${shape}. Mean answered duration under ${minMeanDuration}s is the single ` +
      'metric most likely to pull a score down.'];
  }
  if (lowRate) {
    return ['low-answer',
      `${shape}. An answer rate under ${Math.round(minAnswerRate * 100)}% suggests ` +
      'the number is already being labelled on some handsets, which lowers it further.'];
  }

  return ['healthy', shape];
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

export async function listCalls(auth, account, since, limit) {
  let url = `${BASE}/Accounts/${account}/Calls.json`;
  let params = { 'StartTime>=': since, PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const body = await get(auth, url, params);
    out.push(...(body.calls ?? []));
    url = body.next_page_uri ? HOST + body.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Both log levels, merged on sid: several voice failures are warnings. */
export async function sweepAlerts(auth, since, limit, levels) {
  const seen = new Map();
  for (const level of levels) {
    let url = `${MONITOR}/Alerts`;
    let params = { LogLevel: level, StartDate: since, PageSize: 1000 };
    let got = 0;
    while (url && got < limit) {
      const page = await get(auth, url, params);
      for (const a of page.alerts ?? []) {
        if (!seen.has(a.sid)) seen.set(a.sid, a);
        got += 1;
      }
      url = page.meta?.next_page_url ?? null;
      params = {};
    }
  }
  return [...seen.values()];
}

async function blockedNumbers(auth, account, alerts) {
  const cache = new Map();
  const counts = {};
  for (const a of alerts) {
    const sid = String(a.resource_sid ?? '');
    if (!sid.startsWith('CA')) continue;
    if (!cache.has(sid)) {
      cache.set(sid, await get(auth, `${BASE}/Accounts/${account}/Calls/${sid}.json`));
    }
    const frm = String(cache.get(sid).from ?? '').trim();
    if (frm) counts[frm] = (counts[frm] ?? 0) + 1;
  }
  return counts;
}

function flagValue(name, fallback) {
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
  const days = Math.min(flagValue('--days', 30), 30);
  const minAttempts = flagValue('--min-attempts', 20);
  const maxCalls = flagValue('--max-calls', 20000);
  const levels = process.argv.includes('--errors-only') ? ['error'] : ['error', 'warning'];
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await sweepAlerts(auth, since, 10000, levels);
  const hits = alerts.filter(
    (a) => String(a.error_code ?? '').trim() === String(CARRIER_BLOCKED));
  const blocked = await blockedNumbers(auth, account, hits);

  const calls = await listCalls(auth, account, since, maxCalls);
  const rows = tally(calls, blocked);
  const numbers = Object.keys(rows).sort();
  if (numbers.length === 0) {
    console.log(`no outbound calls with a caller ID in the last ${days} day(s)`);
    return;
  }

  let bad = 0;
  let atRisk = 0;
  for (const number of numbers) {
    const [state, detail] = verdict(rows[number], minAttempts);
    const line = `${state.padEnd(12)} ${number}  ${detail}`;
    if (state === 'healthy' || state === 'thin') { console.log(line); continue; }
    bad += 1;
    if (state !== 'blocked') atRisk += 1;
    console.warn(line);
  }

  if (bad) {
    console.warn('  repair: register the numbers at freecallerregistry.com and, ' +
                 'for T-Mobile, portal.firstorion.com');
    console.warn('  then change the traffic: fewer attempts per number, call at ' +
                 'hours people answer, raise mean duration. Rotating to a fresh ' +
                 'number without that earns the same score again');
  }

  console.log(`${numbers.length} number(s), ${Object.keys(blocked).length} blocked, ` +
              `${atRisk} at risk`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tally is where this check lives or dies, so the fixture includes calls that were never answered and asserts that their zero duration does not enter the mean. The rest pin the ordering: a blocked number is reported as blocked whatever its volume, and a number with four calls is reported as too thin to judge rather than given a rate computed from four data points.",
"test_py_file": "test_twilio_caller_id_reputation_audit.py",
"test_py": '''from twilio_caller_id_reputation_audit import seconds, tally, verdict


def call(frm, status, duration="0"):
    return {"from": frm, "status": status, "duration": duration}


def test_duration_parses_from_the_string_the_api_returns():
    assert seconds("45") == 45
    assert seconds(None) == 0
    assert seconds("") == 0
    assert seconds("n/a") == 0


def test_unanswered_calls_count_as_attempts_and_not_towards_the_mean():
    # The mistake that makes this whole check useless: a dialer whose calls ring
    # out looks fine if their zero durations are averaged in.
    calls = [call("+15005550006", "completed", "120"),
             call("+15005550006", "no-answer"),
             call("+15005550006", "busy")]
    row = tally(calls)["+15005550006"]
    assert row == {"attempts": 3, "completed": 1, "answered_seconds": 120,
                   "blocked": 0}


def test_calls_still_in_flight_are_excluded_from_the_denominator():
    calls = [call("+15005550006", "completed", "60"),
             call("+15005550006", "in-progress"),
             call("+15005550006", "queued")]
    assert tally(calls)["+15005550006"]["attempts"] == 1


def test_a_blocked_number_with_no_calls_in_the_window_still_appears():
    rows = tally([], {"+15005550006": 4})
    assert rows["+15005550006"]["blocked"] == 4
    assert verdict(rows["+15005550006"])[0] == "blocked"


def test_a_block_outranks_every_other_signal():
    stats = {"attempts": 500, "completed": 480, "answered_seconds": 96000,
             "blocked": 7}
    state, detail = verdict(stats)
    assert state == "blocked"
    assert "carrier side" in detail


def test_too_few_attempts_is_reported_as_thin_rather_than_scored():
    state, detail = verdict({"attempts": 4, "completed": 0, "answered_seconds": 0})
    assert state == "thin"
    assert "0 of 4" in detail


def test_low_answer_rate_and_short_calls_together_are_the_at_risk_profile():
    stats = {"attempts": 400, "completed": 40, "answered_seconds": 320}
    state, detail = verdict(stats)
    assert state == "at-risk"
    assert "10%" in detail
    assert "8s" in detail


def test_short_calls_alone_are_their_own_state():
    stats = {"attempts": 100, "completed": 90, "answered_seconds": 900}
    state, detail = verdict(stats)
    assert state == "short-calls"
    assert "under 30s" in detail


def test_a_low_answer_rate_on_long_calls_is_a_different_finding():
    stats = {"attempts": 200, "completed": 40, "answered_seconds": 8000}
    state, detail = verdict(stats)
    assert state == "low-answer"
    assert "labelled" in detail


def test_a_healthy_number_reports_the_two_numbers_that_matter():
    stats = {"attempts": 200, "completed": 150, "answered_seconds": 30000}
    state, detail = verdict(stats)
    assert state == "healthy"
    assert "150 of 200" in detail
    assert "200s" in detail
''',
"test_js_file": "twilio-caller-id-reputation-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { seconds, tally, verdict } from './twilio-caller-id-reputation-audit.mjs';

const call = (from, status, duration = '0') => ({ from, status, duration });

test('duration parses from the string the api returns', () => {
  assert.equal(seconds('45'), 45);
  assert.equal(seconds(null), 0);
  assert.equal(seconds(''), 0);
  assert.equal(seconds('n/a'), 0);
});

test('unanswered calls count as attempts and not towards the mean', () => {
  const calls = [call('+15005550006', 'completed', '120'),
                 call('+15005550006', 'no-answer'),
                 call('+15005550006', 'busy')];
  assert.deepEqual(tally(calls)['+15005550006'],
                   { attempts: 3, completed: 1, answered_seconds: 120, blocked: 0 });
});

test('calls still in flight are excluded from the denominator', () => {
  const calls = [call('+15005550006', 'completed', '60'),
                 call('+15005550006', 'in-progress'),
                 call('+15005550006', 'queued')];
  assert.equal(tally(calls)['+15005550006'].attempts, 1);
});

test('a blocked number with no calls in the window still appears', () => {
  const rows = tally([], { '+15005550006': 4 });
  assert.equal(rows['+15005550006'].blocked, 4);
  assert.equal(verdict(rows['+15005550006'])[0], 'blocked');
});

test('a block outranks every other signal', () => {
  const [state, detail] = verdict(
    { attempts: 500, completed: 480, answered_seconds: 96000, blocked: 7 });
  assert.equal(state, 'blocked');
  assert.match(detail, /carrier side/);
});

test('too few attempts is reported as thin rather than scored', () => {
  const [state, detail] = verdict({ attempts: 4, completed: 0, answered_seconds: 0 });
  assert.equal(state, 'thin');
  assert.match(detail, /0 of 4/);
});

test('low answer rate and short calls together are the at-risk profile', () => {
  const [state, detail] = verdict(
    { attempts: 400, completed: 40, answered_seconds: 320 });
  assert.equal(state, 'at-risk');
  assert.match(detail, /10%/);
  assert.match(detail, /8s/);
});

test('short calls alone are their own state', () => {
  const [state, detail] = verdict(
    { attempts: 100, completed: 90, answered_seconds: 900 });
  assert.equal(state, 'short-calls');
  assert.match(detail, /under 30s/);
});

test('a low answer rate on long calls is a different finding', () => {
  const [state, detail] = verdict(
    { attempts: 200, completed: 40, answered_seconds: 8000 });
  assert.equal(state, 'low-answer');
  assert.match(detail, /labelled/);
});

test('a healthy number reports the two numbers that matter', () => {
  const [state, detail] = verdict(
    { attempts: 200, completed: 150, answered_seconds: 30000 });
  assert.equal(state, 'healthy');
  assert.match(detail, /150 of 200/);
  assert.match(detail, /200s/);
});
''',
"faq": [
 ("Can Twilio unblock the number for me?",
  "No. The block is applied by the terminating carrier and its analytics partner, not by Twilio, so there is no field on the number and no setting in the console that changes it. The routes that exist are outside Twilio: freecallerregistry.com covers several carriers and portal.firstorion.com covers T-Mobile."),
 ("Will rotating to a fresh number fix it?",
  "It will restore service and start the same clock. A new number placing the same volume of short, unanswered calls accumulates the same score, usually within weeks, and now you have two numbers with a history instead of one. That is why the script scores every number in the window rather than only the blocked one."),
 ("Where do the thresholds come from?",
  "From judgement, not from published rules. No analytics provider publishes its scoring, so a 30 percent answer rate and a 30 second mean are set where a legitimate outbound operation sits comfortably clear and a short-call dialer does not. Both are arguments to the classifier, and moving them for your own traffic is expected."),
 ("Why exclude calls that are still in progress?",
  "Because a window that ends in the middle of a campaign is full of them, and counting them as attempts that were not answered depresses the answer rate for a reason that has nothing to do with reputation. Only calls that reached a terminal status are counted, which makes the same window comparable month to month."),
 ("Why does the script sweep the warning level as well?",
  "Because several voice failures are logged at LogLevel=warning rather than error, and a sweep pinned to the error level is the most common reason a voice account reads clean while calls are being refused. Sweeping both and merging on the alert sid costs one extra paginated read."),
],
"related": [
 ("/twilio/dial-invalid-caller-id-13214/", "Dial rejected on a passed-through caller ID"),
 ("/twilio/outbound-call-failure-rate-spike/", "Outbound calls quietly failing more often"),
 ("/twilio/trunk-cps-limit-exceeded-32001/", "A trunk shedding calls at its CPS limit"),
],
"citations": [CITE_32017, CITE_CALL, CITE_ALERT, CITE_CALLER_IDS],
},

]
