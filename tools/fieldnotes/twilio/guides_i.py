#!/usr/bin/env python3
"""/twilio/ field notes, batch I — the writing.

Four voice problems. Two are settings that are empty by default and produce no
error until the day they matter: a SIP trunk with no disaster recovery URL, a
SIP Domain with no auth_type. Two are visible only in aggregate: caller IDs
passed through from inbound legs and rejected as 13214, and a failure rate on
outbound calls that no single error code explains.

Read-only throughout. An API Key with read access, never the account auth
token, and every repair is printed for a human to run rather than performed.

One thing worth carrying between these notes: several voice failures are logged
at LogLevel=warning rather than error, including some of the 132xx Dial
attribute errors. An Alerts sweep that filters to error alone will report a
clean account while the calls keep failing, so both scripts here that read
Alerts sweep both levels.
"""

CITE_TRUNK = ("Trunk resource — Twilio Docs",
              "https://www.twilio.com/docs/sip-trunking/api/trunk-resource")
CITE_ORIGINATION = ("OriginationUrl resource — Twilio Docs",
                    "https://www.twilio.com/docs/sip-trunking/api/origination-url-resource")
CITE_TRUNKING = ("Elastic SIP Trunking — Twilio Docs",
                 "https://www.twilio.com/docs/sip-trunking")
CITE_SIP_DOMAIN = ("SIP Domain resource — Twilio Docs",
                   "https://www.twilio.com/docs/voice/sip/api/sip-domain-resource")
CITE_SENDING_SIP = ("Sending SIP to Twilio — Twilio Docs",
                    "https://www.twilio.com/docs/voice/api/sending-sip")
CITE_CL_MAPPING = ("SIP CredentialListMapping resource — Twilio Docs",
                   "https://www.twilio.com/docs/voice/sip/api/sip-credentiallistmapping-resource")
CITE_13214 = ("Error 13214: Dial: Invalid callerId value — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/13214")
CITE_CALL = ("Call resource — Twilio Docs",
             "https://www.twilio.com/docs/voice/api/call-resource")
CITE_ALERT = ("Alert resource (Monitor) — Twilio Docs",
              "https://www.twilio.com/docs/usage/monitor-alert")
CITE_CALLER_IDS = ("OutgoingCallerId resource — Twilio Docs",
                   "https://www.twilio.com/docs/voice/api/outgoing-caller-ids")
CITE_TWIML_DIAL = ("TwiML Voice: &lt;Dial&gt; — Twilio Docs",
                   "https://www.twilio.com/docs/voice/twiml/dial")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "trunk-missing-disaster-recovery-url",
"title": "A SIP trunk with no disaster recovery URL loses every call",
"description": "disaster_recovery_url is empty by default. Nothing reports it until the PBX goes down, and then inbound calls to the trunk are dropped with no fallback.",
"h1": "a SIP trunk with no disaster recovery URL loses every call",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio disaster_recovery_url", "sip trunk failover twilio",
             "elastic sip trunking disaster recovery",
             "twilio trunk origination unreachable", "pbx down inbound calls lost"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The trunk works. It has worked for a year. Then the PBX reboots, or the firewall rule expires, or the datacentre link flaps for four minutes, and every inbound call in those four minutes is dropped at Twilio &mdash; not sent to voicemail, not answered by an apology, dropped. The field that would have caught them is empty, and it has always been empty, because nothing ever asked you to fill it in.",
"short_answer": """<p>Read <code>GET https://trunking.twilio.com/v1/Trunks?PageSize=1000</code> and flag every trunk whose <code>disaster_recovery_url</code> is null or empty. That URL is the TwiML endpoint Twilio calls when the trunk's origination URIs are unreachable; it is optional, it defaults to empty, and a trunk provisioned quickly ships without it.</p>
<p>Record <code>disaster_recovery_method</code>, <code>secure</code> and <code>transfer_mode</code> on the same pass. Then, if you want the second half of the picture, read <code>GET /v1/Trunks/{TrunkSid}/OriginationUrls</code>: a trunk with one enabled origination URI has a single point of failure that the disaster recovery URL is the only cover for.</p>""",
"problem": """<p>There is no error code for this note, because there is no error. A trunk without a disaster recovery URL behaves identically to one with it, right up until the moment the origination URIs stop answering. At that moment the trunk with the URL fetches TwiML and does something &mdash; plays a message, forwards to a mobile, drops the call into a queue &mdash; and the trunk without it has nowhere to go, so the call ends.</p>
<p>What makes it durable is that the outage that reveals it is short and someone else's fault. The PBX came back, the calls that got through afterwards were fine, and the incident is written up as a PBX incident. The trunk is never looked at, because the trunk was not the thing that broke. It was the thing that had no answer for something else breaking, which is a harder failure to attribute and a much easier one to leave in place.</p>""",
"why": """<p><strong>The field is optional and empty is the default.</strong> Creating a trunk requires a friendly name. Everything else, disaster recovery included, is a later step, and later steps are the ones that get skipped when a trunk is stood up to unblock a migration.</p>
<p><strong>Nothing exercises it.</strong> A disaster recovery URL is only fetched when origination fails. You can have one that returns 404 and never find out, and you can have none at all and never find out, and the two are indistinguishable from the outside during normal operation.</p>
<p><strong>Trunk failover intuition comes from the PBX side.</strong> Teams configure redundant origination URIs and reasonably conclude they have failover. They have failover between the URIs. They do not have an answer for the case where every URI is unreachable at once, which is the common case: the shared firewall, the shared uplink, the shared power feed.</p>
<p><strong>Trunks are few and long lived.</strong> An account has three or four of them, configured once, by someone who may have left. Nobody re-reads a trunk's configuration, so a mechanical check is the only kind that happens twice.</p>""",
"steps": [
 {"h": "List every trunk and read the disaster recovery pair",
  "body": """<p><code>GET https://trunking.twilio.com/v1/Trunks?PageSize=1000</code>, following <code>meta.next_page_url</code> &mdash; the trunking API paginates with an absolute URL in <code>meta</code>, not with the relative <code>next_page_uri</code> the 2010-04-01 API uses. Read <code>disaster_recovery_url</code> and <code>disaster_recovery_method</code> together: a URL with no method is fetched with the default, which is fine, but a method with no URL is nothing at all.</p>"""},
 {"h": "Treat an http disaster recovery URL as a separate finding",
  "body": """<p>A <code>disaster_recovery_url</code> on plain <code>http</code> is configured but is fetched in cleartext across the public internet at the exact moment your voice path is already degraded. It is not the same problem as an empty field and it should not be reported with the same words, but it belongs in the same run.</p>"""},
 {"h": "Read the origination URIs to size the risk",
  "body": """<p><code>GET https://trunking.twilio.com/v1/Trunks/{TrunkSid}/OriginationUrls</code> returns <code>sip_url</code>, <code>enabled</code>, <code>priority</code> and <code>weight</code> for each URI. Count the ones where <code>enabled</code> is true. Zero means inbound calls have nowhere to go even on a good day; one means the disaster recovery URL is the only thing standing between a single host and a dropped call.</p>"""},
 {"h": "Check secure and transfer_mode while you are in there",
  "body": """<p><code>secure</code> tells you whether the trunk requires TLS and SRTP. <code>transfer_mode</code> tells you whether SIP REFER is enabled. Neither is this note's failure, but both are settings that were left at their defaults by the same rushed provisioning that left the disaster recovery URL empty, and reading them costs nothing extra.</p>"""},
 {"h": "Point it at TwiML that does something useful, then re-run",
  "body": """<p><code>POST https://trunking.twilio.com/v1/Trunks/{TrunkSid}</code> with <code>DisasterRecoveryUrl</code> and <code>DisasterRecoveryMethod</code>. Host that TwiML somewhere that does not depend on the PBX &mdash; a disaster recovery endpoint behind the thing that just failed is not a disaster recovery endpoint. Then run the audit again, and keep running it, because the next trunk will be created the same way.</p>"""},
],
"verify": """<p>Re-run the script. Every trunk should report <code>covered</code>, and the exposed count should be zero.</p>
<pre><code class="language-bash">python3 twilio_trunk_dr_audit.py --check-origination
# 4 trunk(s), 0 without disaster recovery</code></pre>""",
"code_intro": "One paginated GET over the trunks, plus one GET per trunk when you ask for the origination detail. An API Key with read access is enough and is what you should give it. The classification is a pure function taking a trunk and, optionally, its origination URIs, because the interesting judgement is what an empty field means in the presence of one enabled URI versus five &mdash; and that deserves to be readable rather than buried in a request loop.",
"py_file": "twilio_trunk_dr_audit.py",
"py": '''"""Report Twilio SIP Trunks with no disaster recovery URL.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_trunk_dr_audit")

TRUNKING = "https://trunking.twilio.com/v1"


def scheme_of(url):
    """Lowercase URL scheme, or an empty string when there is not one.

    Kept separate because a disaster recovery URL on plain http is a different
    finding from one that is missing, and the difference is one substring.
    """
    u = str(url or "").strip()
    if "://" not in u:
        return ""
    return u.split("://", 1)[0].lower()


def enabled_uris(origination):
    """The origination URIs Twilio would actually try.

    A disabled URI is still in the listing and still has a sip_url, so counting
    the list rather than the enabled subset overstates the redundancy exactly
    when it matters.
    """
    return [u for u in (origination or []) if u.get("enabled")]


def verdict(trunk, origination=None):
    """Classify one Trunk. Pure, so the rules can be tested without a network.

    origination is the trunk's OriginationUrl list, or None when it was not
    fetched. None and an empty list mean different things: the first is "not
    checked", the second is "checked, and there is nowhere for calls to go".

    Returns (state, detail).
    """
    dr = str(trunk.get("disaster_recovery_url") or "").strip()
    if not dr:
        return ("exposed",
                "no disaster_recovery_url: when the origination URIs stop "
                "answering, inbound calls to this trunk end at Twilio with no "
                "fallback, no voicemail and nothing logged as a call failure.")

    if scheme_of(dr) == "http":
        return ("dr-cleartext",
                "disaster_recovery_url is plain http, so the one TwiML fetch "
                "that happens while your voice path is already degraded crosses "
                "the public internet in cleartext.")

    if origination is not None:
        live = enabled_uris(origination)
        if not live:
            return ("no-origination",
                    "disaster recovery is set, but no origination URI is "
                    "enabled: inbound calls have nowhere to go on a good day, "
                    "not only during an outage.")
        if len(live) == 1:
            return ("single-uri",
                    "one enabled origination URI (%s), so the disaster recovery "
                    "URL is the only cover for that single host."
                    % (live[0].get("sip_url") or "?"))

    method = str(trunk.get("disaster_recovery_method") or "").strip().upper()
    return ("covered",
            "disaster_recovery_url is set and will be fetched with %s"
            % (method or "the default, which is a POST"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_trunks(session, limit):
    """Page the trunks. This API paginates with an absolute meta.next_page_url."""
    url = TRUNKING + "/Trunks"
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("trunks", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def list_origination(session, trunk_sid):
    """Origination URIs for one trunk. Not paginated in practice, but read the
    meta anyway rather than assuming."""
    url = "%s/Trunks/%s/OriginationUrls" % (TRUNKING, trunk_sid)
    params = {"PageSize": 100}
    out = []
    while url:
        page = get(session, url, **params)
        out.extend(page.get("origination_urls", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-trunks", type=int, default=200,
                    help="stop after this many trunks")
    ap.add_argument("--check-origination", action="store_true",
                    help="one extra GET per trunk to count enabled origination URIs")
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

    trunks = list_trunks(session, args.max_trunks)
    if not trunks:
        log.info("no SIP trunks on this account")
        return 0

    bad = 0
    for t in trunks:
        origination = None
        if args.check_origination:
            origination = list_origination(session, t.get("sid"))
        state, detail = verdict(t, origination)
        name = t.get("friendly_name") or t.get("domain_name") or t.get("sid")
        line = "%-14s %s  %s" % (state, name, detail)
        if state == "covered":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  secure=%s transfer_mode=%s",
                    t.get("secure"), t.get("transfer_mode"))
        log.warning("  repair: POST %s/Trunks/%s "
                    "DisasterRecoveryUrl=https://your-app.example.com/dr-twiml "
                    "DisasterRecoveryMethod=POST", TRUNKING, t.get("sid"))
        log.warning("  host that TwiML somewhere that does not depend on the PBX")

    log.info("%d trunk(s), %d without disaster recovery", len(trunks), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-trunk-dr-audit.mjs",
"js": '''/**
 * Report Twilio SIP Trunks with no disaster recovery URL.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const TRUNKING = 'https://trunking.twilio.com/v1';

/**
 * Lowercase URL scheme, or an empty string when there is not one. A disaster
 * recovery URL on plain http is a different finding from a missing one.
 */
export function schemeOf(url) {
  const u = String(url ?? '').trim();
  if (!u.includes('://')) return '';
  return u.split('://')[0].toLowerCase();
}

/**
 * The origination URIs Twilio would actually try. A disabled URI is still in
 * the listing, so counting the list overstates the redundancy.
 */
export function enabledUris(origination) {
  return (origination ?? []).filter((u) => u.enabled);
}

/**
 * Classify one Trunk. Pure, so the rules can be tested without a network.
 * `origination` is the trunk's OriginationUrl list, or null when it was not
 * fetched: null means "not checked", an empty array means "checked, and there
 * is nowhere for calls to go". Returns [state, detail].
 */
export function verdict(trunk, origination = null) {
  const dr = String(trunk.disaster_recovery_url ?? '').trim();
  if (!dr) {
    return ['exposed',
      'no disaster_recovery_url: when the origination URIs stop answering, ' +
      'inbound calls to this trunk end at Twilio with no fallback, no ' +
      'voicemail and nothing logged as a call failure.'];
  }

  if (schemeOf(dr) === 'http') {
    return ['dr-cleartext',
      'disaster_recovery_url is plain http, so the one TwiML fetch that ' +
      'happens while your voice path is already degraded crosses the public ' +
      'internet in cleartext.'];
  }

  if (origination !== null) {
    const live = enabledUris(origination);
    if (live.length === 0) {
      return ['no-origination',
        'disaster recovery is set, but no origination URI is enabled: inbound ' +
        'calls have nowhere to go on a good day, not only during an outage.'];
    }
    if (live.length === 1) {
      return ['single-uri',
        `one enabled origination URI (${live[0].sip_url ?? '?'}), so the ` +
        'disaster recovery URL is the only cover for that single host.'];
    }
  }

  const method = String(trunk.disaster_recovery_method ?? '').trim().toUpperCase();
  return ['covered',
    `disaster_recovery_url is set and will be fetched with ${method || 'the default, which is a POST'}`];
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

/** Page the trunks. This API paginates with an absolute meta.next_page_url. */
export async function listTrunks(auth, limit = 200) {
  let url = `${TRUNKING}/Trunks`;
  let params = { PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.trunks ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

export async function listOrigination(auth, trunkSid) {
  let url = `${TRUNKING}/Trunks/${trunkSid}/OriginationUrls`;
  let params = { PageSize: 100 };
  const out = [];
  while (url) {
    const page = await get(auth, url, params);
    out.push(...(page.origination_urls ?? []));
    url = page.meta?.next_page_url ?? null;
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
  const checkOrigination = process.argv.includes('--check-origination');

  const trunks = await listTrunks(auth);
  if (trunks.length === 0) {
    console.log('no SIP trunks on this account');
    return;
  }

  let bad = 0;
  for (const t of trunks) {
    const origination = checkOrigination ? await listOrigination(auth, t.sid) : null;
    const [state, detail] = verdict(t, origination);
    const name = t.friendly_name || t.domain_name || t.sid;
    const line = `${state.padEnd(14)} ${name}  ${detail}`;
    if (state === 'covered') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  secure=${t.secure} transfer_mode=${t.transfer_mode}`);
    console.warn(`  repair: POST ${TRUNKING}/Trunks/${t.sid} ` +
                 'DisasterRecoveryUrl=https://your-app.example.com/dr-twiml ' +
                 'DisasterRecoveryMethod=POST');
    console.warn('  host that TwiML somewhere that does not depend on the PBX');
  }

  console.log(`${trunks.length} trunk(s), ${bad} without disaster recovery`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that separate <em>not checked</em> from <em>checked and empty</em>. A trunk audited without the origination fetch must not be reported as having no origination URIs, and a trunk with three URIs of which two are disabled must be reported as having one. Both are off-by-one mistakes that read as reassuring, which is the worst way for a check to be wrong.",
"test_py_file": "test_twilio_trunk_dr_audit.py",
"test_py": '''from twilio_trunk_dr_audit import enabled_uris, scheme_of, verdict


def test_empty_disaster_recovery_url_is_exposed():
    state, detail = verdict({"disaster_recovery_url": ""})
    assert state == "exposed"
    assert "no fallback" in detail


def test_missing_field_reads_the_same_as_an_empty_one():
    assert verdict({})[0] == "exposed"
    assert verdict({"disaster_recovery_url": None})[0] == "exposed"


def test_method_without_a_url_is_still_exposed():
    # A method is not a destination. Reading the pair as configured because one
    # half is populated is the mistake this case exists to prevent.
    assert verdict({"disaster_recovery_method": "POST"})[0] == "exposed"


def test_cleartext_disaster_recovery_url_is_its_own_state():
    state, _ = verdict({"disaster_recovery_url": "http://dr.example.com/twiml"})
    assert state == "dr-cleartext"


def test_https_url_with_no_origination_check_is_covered():
    # origination=None means not checked, and must not be read as "no URIs".
    state, detail = verdict({"disaster_recovery_url": "https://dr.example.com/twiml"})
    assert state == "covered"
    assert "the default" in detail


def test_checked_and_empty_origination_is_not_the_same_as_unchecked():
    state, _ = verdict({"disaster_recovery_url": "https://dr.example.com/twiml"}, [])
    assert state == "no-origination"


def test_disabled_uris_do_not_count_towards_redundancy():
    origination = [
        {"sip_url": "sip:a.example.com", "enabled": True},
        {"sip_url": "sip:b.example.com", "enabled": False},
        {"sip_url": "sip:c.example.com", "enabled": False},
    ]
    state, detail = verdict(
        {"disaster_recovery_url": "https://dr.example.com/twiml"}, origination)
    assert state == "single-uri"
    assert "a.example.com" in detail
    assert len(enabled_uris(origination)) == 1


def test_two_live_uris_and_a_recovery_url_is_covered():
    origination = [{"sip_url": "sip:a", "enabled": True},
                   {"sip_url": "sip:b", "enabled": True}]
    assert verdict({"disaster_recovery_url": "https://dr.example.com/twiml",
                    "disaster_recovery_method": "post"}, origination)[0] == "covered"


def test_scheme_of_handles_a_bare_host():
    assert scheme_of("HTTPS://dr.example.com/x") == "https"
    assert scheme_of("dr.example.com/x") == ""
''',
"test_js_file": "twilio-trunk-dr-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { enabledUris, schemeOf, verdict } from './twilio-trunk-dr-audit.mjs';

test('empty disaster recovery url is exposed', () => {
  const [state, detail] = verdict({ disaster_recovery_url: '' });
  assert.equal(state, 'exposed');
  assert.match(detail, /no fallback/);
});

test('missing field reads the same as an empty one', () => {
  assert.equal(verdict({})[0], 'exposed');
  assert.equal(verdict({ disaster_recovery_url: null })[0], 'exposed');
});

test('method without a url is still exposed', () => {
  assert.equal(verdict({ disaster_recovery_method: 'POST' })[0], 'exposed');
});

test('cleartext disaster recovery url is its own state', () => {
  assert.equal(verdict({ disaster_recovery_url: 'http://dr.example.com/twiml' })[0],
               'dr-cleartext');
});

test('https url with no origination check is covered', () => {
  const [state, detail] = verdict({ disaster_recovery_url: 'https://dr.example.com/twiml' });
  assert.equal(state, 'covered');
  assert.match(detail, /the default/);
});

test('checked and empty origination is not the same as unchecked', () => {
  assert.equal(
    verdict({ disaster_recovery_url: 'https://dr.example.com/twiml' }, [])[0],
    'no-origination');
});

test('disabled uris do not count towards redundancy', () => {
  const origination = [
    { sip_url: 'sip:a.example.com', enabled: true },
    { sip_url: 'sip:b.example.com', enabled: false },
    { sip_url: 'sip:c.example.com', enabled: false },
  ];
  const [state, detail] = verdict(
    { disaster_recovery_url: 'https://dr.example.com/twiml' }, origination);
  assert.equal(state, 'single-uri');
  assert.match(detail, /a\\.example\\.com/);
  assert.equal(enabledUris(origination).length, 1);
});

test('two live uris and a recovery url is covered', () => {
  const origination = [{ sip_url: 'sip:a', enabled: true },
                       { sip_url: 'sip:b', enabled: true }];
  assert.equal(verdict({ disaster_recovery_url: 'https://dr.example.com/twiml',
                         disaster_recovery_method: 'post' }, origination)[0], 'covered');
});

test('schemeOf handles a bare host', () => {
  assert.equal(schemeOf('HTTPS://dr.example.com/x'), 'https');
  assert.equal(schemeOf('dr.example.com/x'), '');
});
''',
"faq": [
 ("Why does this never show up in the Debugger?",
  "Because nothing failed while you were watching. The disaster recovery URL is only fetched when the origination URIs are unreachable, so an empty field generates no request, no alert and no error code during normal operation. It is a gap in coverage rather than an event, and event-based monitoring has nothing to report."),
 ("Is one origination URI actually a problem?",
  "Not on its own, and that is why it is a separate state rather than a failure. It becomes the finding when it is combined with an empty disaster recovery URL, because then a single unreachable host drops every inbound call with no second path and no fallback TwiML. The script reports the combination rather than either half."),
 ("Where should the disaster recovery TwiML be hosted?",
  "Somewhere that does not share a failure domain with the PBX. A recovery endpoint on the same rack, behind the same firewall, or on the same uplink as the thing that just failed is not recovery, it is a second copy of the outage. A TwiML Bin or a small serverless function is often the right answer precisely because it depends on nothing of yours."),
 ("Does the script check whether the recovery URL actually works?",
  "No, and deliberately. Fetching your disaster recovery endpoint from a monitoring script tells you it answered that request, from that network, at that moment, which is weaker evidence than it looks. What the script asserts is the thing it can assert with certainty from the API: the field is populated, and with what scheme."),
 ("Can the script set the URL for the trunks it finds?",
  "It will not. This section's scripts hold a credential to an account that can place calls and spend money, so they read and print. Writing a disaster recovery URL also means deciding what that TwiML says, which is a product decision rather than a repair a cron job should be making."),
],
"related": [
 ("/twilio/sip-domain-no-auth-type/", "A SIP Domain with no auth_type accepts nothing"),
 ("/twilio/outbound-call-failure-rate-spike/", "Outbound calls quietly failing more often"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
],
"citations": [CITE_TRUNK, CITE_ORIGINATION, CITE_TRUNKING, CITE_KEYS],
},

{
"slug": "sip-domain-no-auth-type",
"title": "A SIP Domain with no auth_type accepts no traffic at all",
"description": "A SIP Domain routes traffic only when auth_type is IP_ACL or CREDENTIAL_LIST. Left undefined, every INVITE is refused before your voice_url is fetched.",
"h1": "a SIP Domain with no auth_type accepts no traffic at all",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio sip domain auth_type", "twilio sip 403 forbidden",
             "sip domain credential list mapping", "twilio ip acl mapping",
             "twilio sip domain not receiving calls"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The domain exists. It has a name, it has a <code>voice_url</code>, it appears in the console alongside the ones that work, and it rejects every call. Not with a 500, not with a TwiML error, not with anything your application can see &mdash; the INVITE is refused at authentication, which happens before Twilio ever looks at the URL you configured. The domain looks provisioned because provisioning it and making it able to accept traffic are two different operations.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains.json</code> and flag every domain whose <code>auth_type</code> is empty or null. Twilio's documentation is explicit about this: a domain routes traffic only when <code>auth_type</code> is <code>IP_ACL</code>, <code>CREDENTIAL_LIST</code>, or both, and a domain with none defined cannot receive any traffic.</p>
<p>Then confirm the declaration is backed by something. <code>GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains/{DomainSid}/Auth/Calls/CredentialListMappings.json</code> and the IP ACL equivalent tell you whether the mode named in <code>auth_type</code> has anything mapped to it. Read <code>voice_url</code> and <code>voice_fallback_url</code> on the same pass.</p>""",
"problem": """<p>An inert SIP Domain produces silence in every log you own. Your application is never called, so there is no request to trace. Twilio has no TwiML to execute, so there is no Debugger alert about your endpoint. The far end sees a rejection at the SIP layer, which is visible to whoever runs the PBX or the softphone and to nobody on your side of the boundary.</p>
<p>That split is what makes it expensive. The team who configured the domain sees a domain that looks correct. The team dialling into it sees calls being refused. Each has evidence for their own position and neither has evidence about the other's, so the conversation goes several rounds before somebody reads <code>auth_type</code> and finds it empty.</p>""",
"why": """<p><strong>Creating the domain and enabling it are separate calls.</strong> Creating a SIP Domain needs a domain name. Mapping a credential list or an IP ACL to it is a POST to a different subresource, and a script or a runbook that does the first and not the second leaves a domain that is complete by every measure except the one that matters.</p>
<p><strong>The field is a description, not a switch.</strong> Setting <code>auth_type</code> to <code>CREDENTIAL_LIST</code> does not create a credential list or attach one. A domain can declare a mode and have nothing mapped to it, which is not the same failure as an empty <code>auth_type</code> but has the same effect for anybody trying to authenticate that way.</p>
<p><strong>The listing looks healthy.</strong> The domains list returns a name, a <code>voice_url</code>, timestamps and a SID for every domain, working or not. Nothing in a listing distinguishes the inert one, and <code>auth_type</code> is easy to skim past because an empty string does not draw the eye.</p>
<p><strong>A half-mapped domain fails for half your users.</strong> When <code>auth_type</code> declares both modes and only the credential list is mapped, the softphones authenticate and the PBX that registers by IP does not. That looks like an intermittent problem, and intermittency is the thing that keeps a ticket open longest.</p>""",
"steps": [
 {"h": "List the domains and read auth_type first",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains.json?PageSize=1000</code>, following <code>next_page_uri</code>, which on this API is a path rather than an absolute URL. An empty or null <code>auth_type</code> is the finding and it needs no further calls to confirm.</p>"""},
 {"h": "Parse auth_type as a list, not a string",
  "body": """<p>The field carries one mode or both, and both arrives comma separated. Comparing the raw string against <code>IP_ACL</code> reports a domain configured with <code>IP_ACL,CREDENTIAL_LIST</code> as something unrecognised. Split it, upper-case it, and work with the set.</p>"""},
 {"h": "Confirm each declared mode has something mapped",
  "body": """<p><code>GET .../SIP/Domains/{DomainSid}/Auth/Calls/CredentialListMappings.json</code> and <code>GET .../SIP/Domains/{DomainSid}/Auth/Calls/IpAccessControlListMappings.json</code>. Every declared mode with an empty mapping list is a mode nobody can authenticate with. All of them empty is an outage; one of two empty is the intermittent version.</p>"""},
 {"h": "Read the handler and its fallback while you are there",
  "body": """<p>A domain that authenticates correctly and has no <code>voice_url</code> accepts the call and then has no instructions for it. A domain with a <code>voice_url</code> and no <code>voice_fallback_url</code> works until your endpoint returns non-2xx, and then the call ends. Neither is this note's headline failure, but both are found by the same GET and both drop calls.</p>"""},
 {"h": "Map a credential list or an IP ACL, then re-run",
  "body": """<p><code>POST /2010-04-01/Accounts/{AccountSid}/SIP/Domains/{DomainSid}/Auth/Calls/CredentialListMappings.json</code> with <code>CredentialListSid=CL...</code>, or the IP ACL equivalent with <code>IpAccessControlListSid=AL...</code>. Re-run the audit afterwards, and put it on the same schedule as the rest of this section, because the next domain will be created by the same script that created this one.</p>"""},
],
"verify": """<p>Re-run the script. Every domain should report <code>routed</code>, and the inert count should be zero.</p>
<pre><code class="language-bash">python3 twilio_sip_domain_auth_audit.py --check-mappings
# 3 SIP domain(s), 0 unable to accept traffic</code></pre>""",
"code_intro": "One paginated GET over the domains, and with <code>--check-mappings</code> two more per domain for the credential list and IP ACL mappings. All of it reads; an API Key with read access is enough. The classifier is pure and takes the domain plus its mapping counts, because the whole subtlety here is the difference between a mode that is declared, a mode that is declared and mapped, and a mode that is declared while the <em>other</em> one carries all the mappings.",
"py_file": "twilio_sip_domain_auth_audit.py",
"py": '''"""Report Twilio SIP Domains that cannot accept traffic.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can place calls and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_sip_domain_auth_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# The two authentication modes a SIP Domain can declare, and the key each one
# counts its mappings under in the dict handed to verdict().
COUNT_KEY = {"IP_ACL": "ip_acl", "CREDENTIAL_LIST": "credential_list"}


def auth_modes(domain):
    """Split auth_type into the modes it declares.

    A domain can carry both modes, comma separated, and the field arrives with
    inconsistent case and spacing. Comparing the raw string against one mode
    name reports a correctly configured both-modes domain as unrecognised.
    """
    raw = str(domain.get("auth_type") or "")
    return [m.strip().upper() for m in raw.replace(";", ",").split(",") if m.strip()]


def verdict(domain, mappings=None):
    """Classify one SIP Domain. Pure, so the rules can be tested without a
    network.

    mappings is {"credential_list": n, "ip_acl": n} for this domain, or None
    when the mapping subresources were not fetched. None means "not checked"
    and must not be read as "nothing mapped".

    Returns (state, detail).
    """
    modes = auth_modes(domain)
    if not modes:
        return ("inert",
                "auth_type is empty: a SIP Domain with no auth_type cannot "
                "receive any traffic. Every INVITE is refused at "
                "authentication, before voice_url is ever fetched.")

    unmapped = []
    if mappings is not None:
        unmapped = [m for m in modes if not mappings.get(COUNT_KEY.get(m, m), 0)]
        if len(unmapped) == len(modes):
            return ("auth-unmapped",
                    "auth_type declares %s but no credential list or IP ACL is "
                    "mapped to this domain, so there is nothing for a caller to "
                    "authenticate against." % "/".join(modes))

    if not str(domain.get("voice_url") or "").strip():
        return ("no-handler",
                "authentication is configured but voice_url is empty: the call "
                "is accepted and then has no instructions.")

    if unmapped:
        return ("partial-auth",
                "%s is declared with nothing mapped to it, so callers using "
                "that mode are refused while the other mode works. This is the "
                "one that reads as intermittent." % "/".join(unmapped))

    if not str(domain.get("voice_fallback_url") or "").strip():
        return ("no-fallback",
                "no voice_fallback_url: authenticated calls are dropped rather "
                "than rescued the moment your handler returns non-2xx.")

    return ("routed",
            "authenticated by %s, with a handler and a fallback"
            % ", ".join(modes))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page(session, url, key, params=None):
    """Page a 2010-04-01 list. next_page_uri here is a path, not a full URL."""
    params = dict(params or {})
    params.setdefault("PageSize", 100)
    out = []
    while url:
        body = get(session, url, **params)
        out.extend(body.get(key, []))
        nxt = body.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out


def list_domains(session, account):
    return page(session, "%s/Accounts/%s/SIP/Domains.json" % (BASE, account),
                "domains")


def mapping_counts(session, account, domain_sid):
    """How many credential lists and IP ACLs are mapped to this domain."""
    root = "%s/Accounts/%s/SIP/Domains/%s/Auth/Calls" % (BASE, account, domain_sid)
    creds = page(session, root + "/CredentialListMappings.json",
                 "credential_list_mappings")
    acls = page(session, root + "/IpAccessControlListMappings.json",
                "ip_access_control_list_mappings")
    return {"credential_list": len(creds), "ip_acl": len(acls)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-mappings", action="store_true",
                    help="two extra GETs per domain to confirm the declared "
                         "auth modes have something mapped to them")
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

    domains = list_domains(session, account)
    if not domains:
        log.info("no SIP domains on this account")
        return 0

    bad = 0
    for d in domains:
        mappings = None
        if args.check_mappings:
            mappings = mapping_counts(session, account, d.get("sid"))
        state, detail = verdict(d, mappings)
        name = d.get("domain_name") or d.get("friendly_name") or d.get("sid")
        line = "%-13s %s  %s" % (state, name, detail)
        if state == "routed":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if mappings is not None:
            log.warning("  mapped: %d credential list(s), %d IP ACL(s)",
                        mappings["credential_list"], mappings["ip_acl"])
        log.warning("  repair: POST %s/Accounts/%s/SIP/Domains/%s/Auth/Calls/"
                    "CredentialListMappings.json CredentialListSid=CLxxx "
                    "(or the IpAccessControlListMappings equivalent)",
                    BASE, account, d.get("sid"))

    log.info("%d SIP domain(s), %d unable to accept traffic", len(domains), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sip-domain-auth-audit.mjs",
"js": '''/**
 * Report Twilio SIP Domains that cannot accept traffic.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// The two authentication modes a SIP Domain can declare, and the key each one
// counts its mappings under in the object handed to verdict().
const COUNT_KEY = { IP_ACL: 'ip_acl', CREDENTIAL_LIST: 'credential_list' };

/**
 * Split auth_type into the modes it declares. A domain can carry both, comma
 * separated, and the field arrives with inconsistent case and spacing.
 */
export function authModes(domain) {
  const raw = String(domain.auth_type ?? '');
  return raw.replace(/;/g, ',').split(',')
    .map((m) => m.trim().toUpperCase())
    .filter(Boolean);
}

/**
 * Classify one SIP Domain. Pure, so the rules can be tested without a network.
 * `mappings` is { credential_list, ip_acl } for this domain, or null when the
 * subresources were not fetched: null means "not checked", never "nothing
 * mapped". Returns [state, detail].
 */
export function verdict(domain, mappings = null) {
  const modes = authModes(domain);
  if (modes.length === 0) {
    return ['inert',
      'auth_type is empty: a SIP Domain with no auth_type cannot receive any ' +
      'traffic. Every INVITE is refused at authentication, before voice_url ' +
      'is ever fetched.'];
  }

  let unmapped = [];
  if (mappings !== null) {
    unmapped = modes.filter((m) => !(mappings[COUNT_KEY[m] ?? m] ?? 0));
    if (unmapped.length === modes.length) {
      return ['auth-unmapped',
        `auth_type declares ${modes.join('/')} but no credential list or IP ` +
        'ACL is mapped to this domain, so there is nothing for a caller to ' +
        'authenticate against.'];
    }
  }

  if (!String(domain.voice_url ?? '').trim()) {
    return ['no-handler',
      'authentication is configured but voice_url is empty: the call is ' +
      'accepted and then has no instructions.'];
  }

  if (unmapped.length) {
    return ['partial-auth',
      `${unmapped.join('/')} is declared with nothing mapped to it, so callers ` +
      'using that mode are refused while the other mode works. This is the one ' +
      'that reads as intermittent.'];
  }

  if (!String(domain.voice_fallback_url ?? '').trim()) {
    return ['no-fallback',
      'no voice_fallback_url: authenticated calls are dropped rather than ' +
      'rescued the moment your handler returns non-2xx.'];
  }

  return ['routed', `authenticated by ${modes.join(', ')}, with a handler and a fallback`];
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

/** Page a 2010-04-01 list. next_page_uri here is a path, not a full URL. */
async function pageAll(auth, url, key) {
  let params = { PageSize: 100 };
  const out = [];
  while (url) {
    const body = await get(auth, url, params);
    out.push(...(body[key] ?? []));
    url = body.next_page_uri ? HOST + body.next_page_uri : null;
    params = {};
  }
  return out;
}

export async function listDomains(auth, account) {
  return pageAll(auth, `${BASE}/Accounts/${account}/SIP/Domains.json`, 'domains');
}

export async function mappingCounts(auth, account, domainSid) {
  const root = `${BASE}/Accounts/${account}/SIP/Domains/${domainSid}/Auth/Calls`;
  const creds = await pageAll(auth, `${root}/CredentialListMappings.json`,
                              'credential_list_mappings');
  const acls = await pageAll(auth, `${root}/IpAccessControlListMappings.json`,
                             'ip_access_control_list_mappings');
  return { credential_list: creds.length, ip_acl: acls.length };
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
  const checkMappings = process.argv.includes('--check-mappings');

  const domains = await listDomains(auth, account);
  if (domains.length === 0) {
    console.log('no SIP domains on this account');
    return;
  }

  let bad = 0;
  for (const d of domains) {
    const mappings = checkMappings ? await mappingCounts(auth, account, d.sid) : null;
    const [state, detail] = verdict(d, mappings);
    const name = d.domain_name || d.friendly_name || d.sid;
    const line = `${state.padEnd(13)} ${name}  ${detail}`;
    if (state === 'routed') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (mappings !== null) {
      console.warn(`  mapped: ${mappings.credential_list} credential list(s), ` +
                   `${mappings.ip_acl} IP ACL(s)`);
    }
    console.warn(`  repair: POST ${BASE}/Accounts/${account}/SIP/Domains/${d.sid}` +
                 '/Auth/Calls/CredentialListMappings.json CredentialListSid=CLxxx ' +
                 '(or the IpAccessControlListMappings equivalent)');
  }

  console.log(`${domains.length} SIP domain(s), ${bad} unable to accept traffic`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on missing credentials and set a non-zero exit
// code that fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three things are worth pinning here. A domain declaring both modes must not be reported as unrecognised, because the comma is the easiest thing in this note to get wrong. A domain audited without the mapping fetch must not be reported as unmapped. And a domain where one of two declared modes has nothing mapped must come back as its own state, because that is the case that presents as an intermittent fault and gets misdiagnosed for days.",
"test_py_file": "test_twilio_sip_domain_auth_audit.py",
"test_py": '''from twilio_sip_domain_auth_audit import auth_modes, verdict

ROUTED = {"auth_type": "CREDENTIAL_LIST",
          "voice_url": "https://app.example.com/voice",
          "voice_fallback_url": "https://app.example.com/fallback"}


def test_empty_auth_type_is_inert():
    state, detail = verdict({"auth_type": "",
                             "voice_url": "https://app.example.com/voice"})
    assert state == "inert"
    assert "cannot receive any traffic" in detail


def test_missing_auth_type_reads_the_same_as_an_empty_one():
    assert verdict({"voice_url": "https://app.example.com/voice"})[0] == "inert"
    assert verdict({"auth_type": None})[0] == "inert"


def test_both_modes_comma_separated_are_parsed_as_two():
    # The reason auth_type is split rather than compared as a string.
    assert auth_modes({"auth_type": "ip_acl, CREDENTIAL_LIST"}) == \\
        ["IP_ACL", "CREDENTIAL_LIST"]


def test_declared_but_nothing_mapped_is_auth_unmapped():
    state, _ = verdict(ROUTED, {"credential_list": 0, "ip_acl": 0})
    assert state == "auth-unmapped"


def test_not_checking_mappings_is_not_the_same_as_nothing_mapped():
    assert verdict(ROUTED)[0] == "routed"


def test_one_of_two_modes_unmapped_is_the_intermittent_case():
    domain = dict(ROUTED, auth_type="IP_ACL,CREDENTIAL_LIST")
    state, detail = verdict(domain, {"credential_list": 1, "ip_acl": 0})
    assert state == "partial-auth"
    assert "IP_ACL" in detail


def test_authenticated_domain_with_no_voice_url_is_no_handler():
    domain = dict(ROUTED, voice_url="")
    assert verdict(domain, {"credential_list": 1, "ip_acl": 0})[0] == "no-handler"


def test_missing_fallback_is_reported_after_the_bigger_failures():
    domain = dict(ROUTED, voice_fallback_url="")
    state, detail = verdict(domain, {"credential_list": 1, "ip_acl": 0})
    assert state == "no-fallback"
    assert "non-2xx" in detail
''',
"test_js_file": "twilio-sip-domain-auth-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { authModes, verdict } from './twilio-sip-domain-auth-audit.mjs';

const ROUTED = {
  auth_type: 'CREDENTIAL_LIST',
  voice_url: 'https://app.example.com/voice',
  voice_fallback_url: 'https://app.example.com/fallback',
};

test('empty auth_type is inert', () => {
  const [state, detail] = verdict({ auth_type: '', voice_url: 'https://app.example.com/voice' });
  assert.equal(state, 'inert');
  assert.match(detail, /cannot receive any traffic/);
});

test('missing auth_type reads the same as an empty one', () => {
  assert.equal(verdict({ voice_url: 'https://app.example.com/voice' })[0], 'inert');
  assert.equal(verdict({ auth_type: null })[0], 'inert');
});

test('both modes comma separated are parsed as two', () => {
  assert.deepEqual(authModes({ auth_type: 'ip_acl, CREDENTIAL_LIST' }),
                   ['IP_ACL', 'CREDENTIAL_LIST']);
});

test('declared but nothing mapped is auth-unmapped', () => {
  assert.equal(verdict(ROUTED, { credential_list: 0, ip_acl: 0 })[0], 'auth-unmapped');
});

test('not checking mappings is not the same as nothing mapped', () => {
  assert.equal(verdict(ROUTED)[0], 'routed');
});

test('one of two modes unmapped is the intermittent case', () => {
  const domain = { ...ROUTED, auth_type: 'IP_ACL,CREDENTIAL_LIST' };
  const [state, detail] = verdict(domain, { credential_list: 1, ip_acl: 0 });
  assert.equal(state, 'partial-auth');
  assert.match(detail, /IP_ACL/);
});

test('authenticated domain with no voice_url is no-handler', () => {
  const domain = { ...ROUTED, voice_url: '' };
  assert.equal(verdict(domain, { credential_list: 1, ip_acl: 0 })[0], 'no-handler');
});

test('missing fallback is reported after the bigger failures', () => {
  const domain = { ...ROUTED, voice_fallback_url: '' };
  const [state, detail] = verdict(domain, { credential_list: 1, ip_acl: 0 });
  assert.equal(state, 'no-fallback');
  assert.match(detail, /non-2xx/);
});
''',
"faq": [
 ("Why is there no error in the Debugger for a rejected SIP call?",
  "Because the rejection happens at authentication, which is upstream of everything the Debugger reports on. Twilio never fetched a TwiML URL, never executed a document and never contacted your application, so there is no request, no response and no 11xxx or 12xxx code. The evidence lives on the SIP side, with whoever runs the PBX."),
 ("Is setting auth_type enough on its own?",
  "No, and that is the second failure in this note. auth_type describes which modes the domain will accept; it does not create or attach a credential list or an IP ACL. A domain can name a mode and have nothing mapped to it, which is why the script fetches both mapping subresources rather than trusting the field."),
 ("What does partial-auth actually look like in production?",
  "Some callers work and some do not, consistently, split by how they authenticate. The softphones with SIP credentials get through; the PBX that Twilio was supposed to recognise by source IP does not. It is reported as an intermittent problem because the reporter cannot see the pattern, and it stays open until somebody counts the mappings."),
 ("Should the script check voice_url and voice_fallback_url too?",
  "They are found by the same GET and they drop calls, so yes. They are ordered after the authentication states because a domain that refuses every INVITE has a handler problem you will never observe. Fix the authentication and the handler findings become the next thing that matters."),
 ("Can the script map the credential list it says is missing?",
  "It will not. Mapping a credential list decides who is allowed to send calls into your account, which is an access-control change and not something a read-only auditor should be making. It prints the exact POST, with the domain SID, for a human to run."),
],
"related": [
 ("/twilio/trunk-missing-disaster-recovery-url/", "A trunk with no disaster recovery URL"),
 ("/twilio/dial-invalid-caller-id-13214/", "Dial rejected with 13214 on a passed-through caller ID"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still pointing at the demo TwiML"),
],
"citations": [CITE_SIP_DOMAIN, CITE_SENDING_SIP, CITE_CL_MAPPING, CITE_KEYS],
},

{
"slug": "dial-invalid-caller-id-13214",
"title": "Dial rejected with 13214 on a passed-through caller ID",
"description": "A Dial with no explicit callerId forwards whatever the inbound leg carried. When a carrier delivers a malformed From, the outbound leg is rejected as 13214.",
"h1": "Dial rejected with 13214 on a passed-through caller ID",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 13214", "dial invalid callerid value",
             "twilio callerid passthrough", "twilio forwarding caller id e164",
             "outgoing caller id verification twilio"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Call forwarding works. It has worked all week. Then a handful of calls fail, and they fail without a pattern anyone can see &mdash; not one number, not one hour, not one destination. What they have in common is invisible from the outside: the inbound leg arrived carrying a caller ID the terminating carrier will not accept, your <code>&lt;Dial&gt;</code> passed it through unchanged, and Twilio logged <code>13214 Dial: Invalid callerId value</code> against a call nobody was watching.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts</code> at <strong>both</strong> <code>LogLevel=error</code> and <code>LogLevel=warning</code>, because several of the 132xx Dial attribute errors are logged as warnings and an error-only sweep reports a clean account. Keep the alerts whose <code>error_code</code> is <code>13214</code>.</p>
<p>Take each alert's <code>resource_sid</code> and read <code>GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json</code>. When <code>direction</code> is <code>inbound</code> and <code>from</code> is not valid E.164, you are looking at pass-through: <code>&lt;Dial&gt;</code> with no <code>callerId</code> hands the inbound <code>From</code> straight to the outbound leg. When <code>from</code> is well formed, compare it against <code>GET /2010-04-01/Accounts/{AccountSid}/OutgoingCallerIds.json</code> and the account's own numbers instead.</p>""",
"problem": """<p>The intermittency is the whole difficulty. Most inbound calls carry a clean E.164 <code>From</code>, so forwarding works, so the code that does it looks correct. The calls that fail are the ones where some upstream carrier delivered something else: a national-format number with no country code, a number with spaces in it, a literal <code>anonymous</code>, a SIP URI. That garbage is not yours and you cannot predict it, but <code>&lt;Dial&gt;</code> without an explicit <code>callerId</code> will faithfully forward it to a terminating provider that rejects it.</p>
<p>And it is logged somewhere nobody reads. The failure is on the outbound child leg of an inbound call, so the parent call often shows as completed. The alert exists, but if your monitoring queries the Alerts API at <code>LogLevel=error</code> only, some of the 132xx family never appear at all. The result is a failure mode that has both a specific error code and no visibility, which is the worst of both.</p>""",
"why": """<p><strong>Pass-through is the default and it reads as correct.</strong> Forwarding a call while preserving the original caller's number is exactly what most people want, and omitting <code>callerId</code> is how you ask for it. Nothing in the TwiML suggests you have taken a dependency on the formatting habits of every carrier that might route a call to you.</p>
<p><strong>Twilio only presents caller IDs it can vouch for.</strong> The <code>callerId</code> on a <code>&lt;Dial&gt;</code> has to be a number on the account or a verified outgoing caller ID. A passed-through <code>From</code> from an arbitrary inbound caller is neither, so even a perfectly formatted number can be refused for a reason that has nothing to do with formatting.</p>
<p><strong>Some of the 132xx family are warnings.</strong> The Alerts API separates <code>error</code> from <code>warning</code>, and a dashboard or script built around the error level will show nothing while these accumulate. This is the single most common reason a team believes they have no Dial problems.</p>
<p><strong>The parent call looks fine.</strong> The inbound leg connects, executes TwiML and ends normally. The rejected leg is a child call, and unless you are joining alerts to calls, nothing puts the two together for you.</p>""",
"steps": [
 {"h": "Sweep the Alerts API at both log levels",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=1000</code>, then the same request with <code>LogLevel=warning</code>, following <code>meta.next_page_url</code> &mdash; on this API the next page is an absolute URL, not the relative <code>next_page_uri</code> the 2010-04-01 API uses. De-duplicate on <code>sid</code>. Alerts are retained 30 days, so a longer window is the same window with a misleading label.</p>"""},
 {"h": "Filter to 13214, reading error_code as an integer",
  "body": """<p>The Monitor API returns <code>error_code</code> as a string, unlike the Messages list. Compare it as a number, or compare both as strings consistently, but do not mix the two &mdash; a filter that silently matches nothing is indistinguishable from a healthy account.</p>"""},
 {"h": "Resolve each alert to its call",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json</code> using the alert's <code>resource_sid</code>. Cache by SID: one bad forwarding rule produces many alerts against a small number of calls, and re-fetching the same call fifty times is fifty requests you did not need.</p>"""},
 {"h": "Classify the caller ID, then check it is one you may present",
  "body": """<p>Not valid E.164 on an <code>inbound</code> call is pass-through, and the fix is in your TwiML. Valid E.164 that is not one of the account's numbers and not in <code>GET /2010-04-01/Accounts/{AccountSid}/OutgoingCallerIds.json</code> is a different problem with the same error code, and the fix is a verification.</p>"""},
 {"h": "Set an explicit callerId and validate the pass-through",
  "body": """<p>Put a real number on every <code>&lt;Dial callerId="+1..."&gt;</code>. If you must preserve the original caller, validate the inbound <code>From</code> against E.164 in your webhook first and substitute one of your own numbers when it fails. Then re-run this sweep over the following week: the count going to zero is the only confirmation that matters, because you cannot reproduce this on demand.</p>"""},
],
"verify": """<p>Re-run the sweep over a window that starts after the deploy. The 13214 count should be zero.</p>
<pre><code class="language-bash">python3 twilio_dial_caller_id_audit.py --days 7
# 0 alert(s) with error_code 13214 in the last 7 day(s)</code></pre>""",
"code_intro": "Two paginated sweeps of the Alerts API, one per log level, then one cached GET per distinct call and one listing of the account's usable caller IDs. Every request is a GET; an API Key with read access is enough. Two pure functions carry the diagnosis: one classifies a caller ID string on its own terms, and one decides what a 13214 on a given call actually means. Both are the kind of rule that is easy to write approximately and worth writing exactly.",
"py_file": "twilio_dial_caller_id_audit.py",
"py": '''"""Report Twilio 13214 alerts and say why each caller ID was rejected.

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
log = logging.getLogger("twilio_dial_caller_id_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

DIAL_CALLER_ID = 13214

# ITU E.164 allows at most 15 digits after the plus. The lower bound is a
# judgement: nothing routable is shorter than a country code plus a few digits,
# and being generous here is better than flagging a valid short number.
E164_MAX = 15
E164_MIN = 7

WITHHELD = {"anonymous", "unavailable", "restricted", "unknown", "private",
            "unknown caller", "not available"}


def caller_id_state(value):
    """Classify a caller ID string on its own, with no account context.

    The states are the shapes carriers actually deliver on an inbound From,
    each of which fails differently: nothing at all, a SIP URI, a withheld
    marker, a national-format number, and a digit string outside E.164.
    """
    v = str(value or "").strip()
    if not v:
        return "absent"
    low = v.lower()
    if low.startswith("sip:") or low.startswith("sips:") or "@" in v:
        return "sip-uri"
    if low.startswith("client:"):
        return "client"
    if low in WITHHELD:
        return "withheld"
    if not v.startswith("+"):
        return "not-e164"
    digits = v[1:]
    if not digits.isdigit():
        return "not-e164"
    if len(digits) < E164_MIN or len(digits) > E164_MAX:
        return "out-of-range"
    return "e164"


def verdict(call, verified=()):
    """Explain one 13214 given the call it was raised against.

    verified is every caller ID this account may present: its own phone numbers
    plus its verified OutgoingCallerIds. Pure, so both the string rules and the
    account rule can be tested without a network.

    Returns (state, detail).
    """
    frm = str(call.get("from") or "").strip()
    shape = caller_id_state(frm)
    direction = str(call.get("direction") or "").strip().lower()

    if shape != "e164":
        if direction == "inbound":
            return ("passthrough",
                    "the inbound leg arrived with from=%s (%s) and a <Dial> "
                    "with no callerId passed it straight to the outbound leg, "
                    "which the terminating carrier refused."
                    % (frm or "<empty>", shape))
        return ("malformed",
                "callerId %s is %s, so it was rejected before the call was "
                "placed." % (frm or "<empty>", shape))

    if frm not in set(verified):
        return ("unverified",
                "%s is well formed but is not a number on this account and is "
                "not a verified outgoing caller ID, so Twilio will not present "
                "it." % frm)

    return ("presentable",
            "%s is a caller ID this account may present, so the 13214 came from "
            "something else on the <Dial>: check the callerId attribute for "
            "whitespace, and check the TwiML that generated it." % frm)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, since, limit, log_level):
    """Page the Monitor alerts at one log level. next_page_url is absolute here."""
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
    """Both log levels, de-duplicated on sid.

    Several of the 132xx Dial attribute errors are logged at warning rather than
    error. A sweep that reads only the error level reports a clean account while
    the calls keep failing, which is the reason this function exists at all.
    """
    seen = {}
    for level in levels:
        for a in list_alerts(session, since, limit, level):
            seen.setdefault(a.get("sid"), a)
    return list(seen.values())


def page_2010(session, url, key):
    params = {"PageSize": 1000}
    out = []
    while url:
        body = get(session, url, **params)
        out.extend(body.get(key, []))
        nxt = body.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out


def presentable_caller_ids(session, account):
    """Every caller ID this account may present: its numbers plus verified ones."""
    numbers = page_2010(session, "%s/Accounts/%s/IncomingPhoneNumbers.json"
                        % (BASE, account), "incoming_phone_numbers")
    verified = page_2010(session, "%s/Accounts/%s/OutgoingCallerIds.json"
                         % (BASE, account), "outgoing_caller_ids")
    out = {str(n.get("phone_number") or "").strip() for n in numbers}
    out |= {str(v.get("phone_number") or "").strip() for v in verified}
    out.discard("")
    return out


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
            if str(a.get("error_code") or "").strip() == str(DIAL_CALLER_ID)]
    if not hits:
        log.info("0 alert(s) with error_code %d in the last %d day(s)",
                 DIAL_CALLER_ID, days)
        return 0

    verified = presentable_caller_ids(session, account)
    calls = {}
    counts = {}
    for a in hits:
        sid = a.get("resource_sid") or ""
        if not sid.startswith("CA"):
            log.warning("13214 alert %s has no call sid to resolve", a.get("sid"))
            continue
        if sid not in calls:
            calls[sid] = get(session, "%s/Accounts/%s/Calls/%s.json"
                             % (BASE, account, sid))
        state, detail = verdict(calls[sid], verified)
        counts[state] = counts.get(state, 0) + 1
        log.warning("%-12s %s  %s", state, sid, detail)

    log.warning("%d alert(s) with error_code %d across %d call(s): %s",
                len(hits), DIAL_CALLER_ID, len(calls),
                ", ".join("%s=%d" % kv for kv in sorted(counts.items())))
    log.warning("  repair: set an explicit callerId on every <Dial>, using one "
                "of this account's numbers, and validate the inbound From "
                "against E.164 before forwarding it")
    log.warning("  verified caller IDs: GET %s/Accounts/%s/OutgoingCallerIds.json",
                BASE, account)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-dial-caller-id-audit.mjs",
"js": '''/**
 * Report Twilio 13214 alerts and say why each caller ID was rejected.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

const DIAL_CALLER_ID = 13214;

// ITU E.164 allows at most 15 digits after the plus. The lower bound is a
// judgement: being generous beats flagging a valid short number.
const E164_MAX = 15;
const E164_MIN = 7;

const WITHHELD = new Set(['anonymous', 'unavailable', 'restricted', 'unknown',
                          'private', 'unknown caller', 'not available']);

/**
 * Classify a caller ID string on its own, with no account context. The states
 * are the shapes carriers actually deliver on an inbound From.
 */
export function callerIdState(value) {
  const v = String(value ?? '').trim();
  if (!v) return 'absent';
  const low = v.toLowerCase();
  if (low.startsWith('sip:') || low.startsWith('sips:') || v.includes('@')) return 'sip-uri';
  if (low.startsWith('client:')) return 'client';
  if (WITHHELD.has(low)) return 'withheld';
  if (!v.startsWith('+')) return 'not-e164';
  const digits = v.slice(1);
  if (!/^[0-9]+$/.test(digits)) return 'not-e164';
  if (digits.length < E164_MIN || digits.length > E164_MAX) return 'out-of-range';
  return 'e164';
}

/**
 * Explain one 13214 given the call it was raised against. `verified` is every
 * caller ID this account may present: its own numbers plus its verified
 * OutgoingCallerIds. Pure. Returns [state, detail].
 */
export function verdict(call, verified = []) {
  const frm = String(call.from ?? '').trim();
  const shape = callerIdState(frm);
  const direction = String(call.direction ?? '').trim().toLowerCase();

  if (shape !== 'e164') {
    if (direction === 'inbound') {
      return ['passthrough',
        `the inbound leg arrived with from=${frm || '<empty>'} (${shape}) and a ` +
        '<Dial> with no callerId passed it straight to the outbound leg, which ' +
        'the terminating carrier refused.'];
    }
    return ['malformed',
      `callerId ${frm || '<empty>'} is ${shape}, so it was rejected before the ` +
      'call was placed.'];
  }

  if (!new Set(verified).has(frm)) {
    return ['unverified',
      `${frm} is well formed but is not a number on this account and is not a ` +
      'verified outgoing caller ID, so Twilio will not present it.'];
  }

  return ['presentable',
    `${frm} is a caller ID this account may present, so the 13214 came from ` +
    'something else on the <Dial>: check the callerId attribute for whitespace, ' +
    'and check the TwiML that generated it.'];
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

/**
 * Both log levels, de-duplicated on sid. Several of the 132xx Dial attribute
 * errors are logged at warning rather than error, so an error-only sweep
 * reports a clean account while the calls keep failing.
 */
export async function sweepAlerts(auth, since, limit, levels) {
  const seen = new Map();
  for (const level of levels) {
    for (const a of await listAlerts(auth, since, limit, level)) {
      if (!seen.has(a.sid)) seen.set(a.sid, a);
    }
  }
  return [...seen.values()];
}

async function page2010(auth, url, key) {
  let params = { PageSize: 1000 };
  const out = [];
  while (url) {
    const body = await get(auth, url, params);
    out.push(...(body[key] ?? []));
    url = body.next_page_uri ? HOST + body.next_page_uri : null;
    params = {};
  }
  return out;
}

async function presentableCallerIds(auth, account) {
  const numbers = await page2010(
    auth, `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`, 'incoming_phone_numbers');
  const verified = await page2010(
    auth, `${BASE}/Accounts/${account}/OutgoingCallerIds.json`, 'outgoing_caller_ids');
  const out = new Set();
  for (const n of [...numbers, ...verified]) {
    const v = String(n.phone_number ?? '').trim();
    if (v) out.add(v);
  }
  return out;
}

function arg(name, fallback) {
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
  const days = Math.min(arg('--days', 7), 30);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const levels = process.argv.includes('--errors-only') ? ['error'] : ['error', 'warning'];

  const alerts = await sweepAlerts(auth, since, 10000, levels);
  const hits = alerts.filter((a) => String(a.error_code ?? '').trim() === String(DIAL_CALLER_ID));
  if (hits.length === 0) {
    console.log(`0 alert(s) with error_code ${DIAL_CALLER_ID} in the last ${days} day(s)`);
    return;
  }

  const verified = await presentableCallerIds(auth, account);
  const calls = new Map();
  const counts = new Map();
  for (const a of hits) {
    const sid = a.resource_sid ?? '';
    if (!sid.startsWith('CA')) {
      console.warn(`13214 alert ${a.sid} has no call sid to resolve`);
      continue;
    }
    if (!calls.has(sid)) {
      calls.set(sid, await get(auth, `${BASE}/Accounts/${account}/Calls/${sid}.json`));
    }
    const [state, detail] = verdict(calls.get(sid), verified);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    console.warn(`${state.padEnd(12)} ${sid}  ${detail}`);
  }

  const summary = [...counts.entries()].sort().map(([k, v]) => `${k}=${v}`).join(', ');
  console.warn(`${hits.length} alert(s) with error_code ${DIAL_CALLER_ID} across ` +
               `${calls.size} call(s): ${summary}`);
  console.warn('  repair: set an explicit callerId on every <Dial>, using one of ' +
               'this account\\'s numbers, and validate the inbound From against ' +
               'E.164 before forwarding it');
  console.warn(`  verified caller IDs: GET ${BASE}/Accounts/${account}/OutgoingCallerIds.json`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail on the missing credentials.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The caller ID rules are worth pinning one shape at a time, because each of them is something a real carrier has actually delivered on an inbound leg: a national-format number, a number with spaces, a literal <code>anonymous</code>, a SIP URI, sixteen digits. The <code>verdict</code> cases then pin the part that is easy to get backwards &mdash; that a perfectly formatted number can still be a 13214, because Twilio will only present a caller ID the account owns or has verified.",
"test_py_file": "test_twilio_dial_caller_id_audit.py",
"test_py": '''from twilio_dial_caller_id_audit import caller_id_state, verdict

OWNED = {"+15005550006"}


def test_plain_e164_is_accepted():
    assert caller_id_state("+15005550006") == "e164"


def test_national_format_has_no_country_code():
    assert caller_id_state("5005550006") == "not-e164"


def test_spaces_and_punctuation_are_not_e164():
    assert caller_id_state("+1 500 555-0006") == "not-e164"


def test_withheld_markers_are_their_own_state():
    assert caller_id_state("anonymous") == "withheld"
    assert caller_id_state("Restricted") == "withheld"


def test_sip_uri_and_client_identity_are_distinguished():
    assert caller_id_state("sip:alice@example.com") == "sip-uri"
    assert caller_id_state("client:alice") == "client"


def test_sixteen_digits_is_outside_e164():
    assert caller_id_state("+1234567890123456") == "out-of-range"


def test_empty_is_absent():
    assert caller_id_state("") == "absent"
    assert caller_id_state(None) == "absent"


def test_bad_from_on_an_inbound_call_is_passthrough():
    state, detail = verdict({"from": "5005550006", "direction": "inbound"}, OWNED)
    assert state == "passthrough"
    assert "no callerId" in detail


def test_bad_from_on_an_outbound_call_is_not_passthrough():
    state, _ = verdict({"from": "anonymous", "direction": "outbound-api"}, OWNED)
    assert state == "malformed"


def test_well_formed_but_unowned_number_is_still_a_13214():
    # The case that reads as a false positive and is not: valid E.164 is not
    # the same as a caller ID this account is allowed to present.
    state, detail = verdict({"from": "+15005550999", "direction": "inbound"}, OWNED)
    assert state == "unverified"
    assert "verified outgoing caller ID" in detail


def test_owned_number_points_the_investigation_elsewhere():
    state, _ = verdict({"from": "+15005550006", "direction": "inbound"}, OWNED)
    assert state == "presentable"
''',
"test_js_file": "twilio-dial-caller-id-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { callerIdState, verdict } from './twilio-dial-caller-id-audit.mjs';

const OWNED = ['+15005550006'];

test('plain e164 is accepted', () => {
  assert.equal(callerIdState('+15005550006'), 'e164');
});

test('national format has no country code', () => {
  assert.equal(callerIdState('5005550006'), 'not-e164');
});

test('spaces and punctuation are not e164', () => {
  assert.equal(callerIdState('+1 500 555-0006'), 'not-e164');
});

test('withheld markers are their own state', () => {
  assert.equal(callerIdState('anonymous'), 'withheld');
  assert.equal(callerIdState('Restricted'), 'withheld');
});

test('sip uri and client identity are distinguished', () => {
  assert.equal(callerIdState('sip:alice@example.com'), 'sip-uri');
  assert.equal(callerIdState('client:alice'), 'client');
});

test('sixteen digits is outside e164', () => {
  assert.equal(callerIdState('+1234567890123456'), 'out-of-range');
});

test('empty is absent', () => {
  assert.equal(callerIdState(''), 'absent');
  assert.equal(callerIdState(null), 'absent');
});

test('bad from on an inbound call is passthrough', () => {
  const [state, detail] = verdict({ from: '5005550006', direction: 'inbound' }, OWNED);
  assert.equal(state, 'passthrough');
  assert.match(detail, /no callerId/);
});

test('bad from on an outbound call is not passthrough', () => {
  assert.equal(verdict({ from: 'anonymous', direction: 'outbound-api' }, OWNED)[0],
               'malformed');
});

test('well formed but unowned number is still a 13214', () => {
  const [state, detail] = verdict({ from: '+15005550999', direction: 'inbound' }, OWNED);
  assert.equal(state, 'unverified');
  assert.match(detail, /verified outgoing caller ID/);
});

test('owned number points the investigation elsewhere', () => {
  assert.equal(verdict({ from: '+15005550006', direction: 'inbound' }, OWNED)[0],
               'presentable');
});
''',
"faq": [
 ("Why does the script sweep the warning level as well as error?",
  "Because several of the 132xx Dial attribute errors are logged at LogLevel=warning rather than error. A sweep filtered to the error level returns nothing and reads as a clean account while the calls keep failing. Both levels are swept and the results de-duplicated on the alert sid, which costs one extra paginated read."),
 ("Is a valid E.164 number ever rejected as 13214?",
  "Yes, and it is the case people call a false positive. The callerId on a Dial has to be a number on the account or a verified outgoing caller ID; anything else is refused however well formatted it is. That is why the script builds the set from IncomingPhoneNumbers and OutgoingCallerIds before judging anything."),
 ("Why look at the parent call rather than the child leg?",
  "Because the parent is where the evidence is. The alert's resource_sid resolves to the call whose TwiML ran the Dial, and that call's from is the value that was passed through. Its direction tells you whether pass-through was even possible, which is what separates a TwiML bug from an unverified number."),
 ("How far back can this look?",
  "Thirty days, because that is how long Twilio retains alerts, and at most 10,000 alerts per request. The script caps the window at 30 days rather than accepting a larger number and quietly returning the same data under a misleading label."),
 ("What is the actual fix in the TwiML?",
  "Set callerId explicitly on Dial, to one of your own numbers. If you need to preserve the original caller's number, validate the inbound From against E.164 in your webhook and fall back to your own number when it fails, which is the same rule this script uses to classify."),
],
"related": [
 ("/twilio/outbound-call-failure-rate-spike/", "Outbound calls quietly failing more often"),
 ("/twilio/sip-domain-no-auth-type/", "A SIP Domain with no auth_type accepts nothing"),
 ("/twilio/status-callback-webhook-failing-11200/", "A status callback failing with 11200"),
],
"citations": [CITE_13214, CITE_CALL, CITE_ALERT, CITE_CALLER_IDS],
},

{
"slug": "outbound-call-failure-rate-spike",
"title": "A rising share of outbound calls end in status failed",
"description": "No single error code explains it. The Calls resource is the only place a failure rate rather than an event is visible, and only if you fetch the denominator.",
"h1": "a rising share of outbound calls end in status failed",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio call status failed", "twilio outbound call failure rate",
             "twilio calls not going through", "outbound-dial failed twilio",
             "twilio geo permissions blocked calls"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nobody can point at an error. Support says calls are not going through; the Debugger has its usual scattering of alerts and none of them is new; the code has not changed. What has changed is a ratio: the share of outbound calls ending in <code>failed</code> rather than <code>completed</code>. A ratio is not an event, so nothing raised it, and nothing will &mdash; you have to go and compute it.",
"short_answer": """<p>Count both sides over the same window. <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?Status=failed&amp;StartTime&gt;=YYYY-MM-DD&amp;PageSize=1000</code> gives you the numerator; the same request with <code>Status=completed</code> gives you the denominator. A count of failures without a denominator tells you nothing, because it rises with traffic.</p>
<p>Then bucket the failures by <code>direction</code> (<code>outbound-api</code> versus <code>outbound-dial</code>) and by the leading digits of <code>to</code>. <code>failed</code> means the call could not be completed as dialled &mdash; a bad destination, a carrier rejection, a geo-permission block, an unreachable SIP leg &mdash; and which bucket it concentrates in is what tells the four apart. Cross-reference <code>GET https://monitor.twilio.com/v1/Alerts</code> at <em>both</em> <code>LogLevel=error</code> and <code>LogLevel=warning</code>, because Twilio raises a Debugger alert for only some of these and some of those are warnings.</p>""",
"problem": """<p>Every other note in this section starts from an error code and works outwards. This one has no error code to start from, and that is the point: <code>failed</code> is a bucket, not a diagnosis. It collects a number that does not exist, a country your account is not permitted to call, a carrier that declined the caller ID, and a SIP endpoint that did not answer, and it gives all four the same word.</p>
<p>Which is why the rate matters more than the count. A hundred failures in a week is normal at some volumes and an outage at others, and no alert threshold on the raw count survives a change in traffic. And because Twilio raises a Debugger alert for only some of these causes, the Calls resource is the authoritative denominator: it is the only place where the calls that <em>worked</em> are counted alongside the ones that did not.</p>""",
"why": """<p><strong>A rate has to be computed, not observed.</strong> The API will give you a list of failed calls all day. It will not tell you what fraction of the traffic that is, because the answer depends on a second query you have to remember to make.</p>
<p><strong>The Calls list has no error-code filter.</strong> You can filter by <code>Status</code>, <code>To</code>, <code>From</code> and time, and that is all. Localising the cause means paging the results and bucketing them client-side, which is exactly the work that does not get done in a console session.</p>
<p><strong>The buckets separate causes that look identical.</strong> Failures concentrated on one country prefix are geo permissions or a normalisation bug. Failures spread across every prefix but only on <code>outbound-dial</code> are a forwarding or caller ID problem. Failures on <code>outbound-api</code> only are your own dialling code. Same status, three different investigations.</p>
<p><strong>Alerts under-report, and some of it is at warning level.</strong> Cross-referencing the Debugger is worth doing, but only with both log levels swept: the CPS and Dial attribute alerts that would explain a chunk of these are logged as warnings, and an error-level query will show you a quiet Debugger next to a failing service.</p>""",
"steps": [
 {"h": "Fetch the numerator and the denominator over the same window",
  "body": """<p>Two paginated reads of <code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json</code>, one with <code>Status=failed</code> and one with <code>Status=completed</code>, both with the same <code>StartTime&gt;=</code>. Follow <code>next_page_uri</code>, which on this API is a path rather than an absolute URL. Anything else is a count, and a count moves with traffic.</p>"""},
 {"h": "Decide honestly what is in the denominator",
  "body": """<p>Two <code>Status</code>-filtered sweeps do not fetch <code>busy</code> or <code>no-answer</code>, so those read as zero and the failure share is computed against completed calls alone. That is a defensible denominator, but only if you know that is what it is. One unfiltered sweep over the window gives you the true outcome mix at the cost of a lot more paging, and the script makes that a flag rather than a hidden default.</p>"""},
 {"h": "Bucket by direction and destination prefix",
  "body": """<p><code>outbound-api</code> is a call your code originated; <code>outbound-dial</code> is a leg created by TwiML. Bucket by that and by the first few digits of <code>to</code>, keeping <code>sip:</code> and <code>client:</code> destinations in their own buckets rather than mangling them into digits. Prefix length is a trade-off: too short and every North American destination lands in one bucket, too long and each bucket has three calls in it.</p>"""},
 {"h": "Only judge buckets with enough calls in them",
  "body": """<p>Three failures out of four calls is a 75% failure rate and means nothing. A floor below which a bucket is reported as low-volume rather than elevated is the difference between a report you act on and one you learn to ignore.</p>"""},
 {"h": "Take the top bucket to the per-call detail",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}/Events.json</code> for a call from the worst bucket gives you the signalling detail that the Calls list flattens into one word. Repair depends on what you find there: geo permissions, E.164 normalisation, or caller ID reputation. That is a decision, which is why this script prints and does not act.</p>"""},
],
"verify": """<p>Re-run with the same window and prefix length after the change. The elevated buckets should drop back to <code>ok</code>.</p>
<pre><code class="language-bash">python3 twilio_call_failure_rate_audit.py --days 7
# 1284 outbound call(s), 41 failed (3.2%), 0 elevated bucket(s)</code></pre>""",
"code_intro": "Two paginated GETs for the two halves of the ratio, an optional third sweep of the Alerts API at both log levels, and no writes anywhere. The three pure functions are the note: how a destination becomes a bucket, how calls become counts, and how a count becomes a verdict. Keeping the volume floor and the threshold as arguments to the classifier rather than constants inside the loop is what lets the tests pin the boundary cases, which are the only cases where a rate check is ever wrong.",
"py_file": "twilio_call_failure_rate_audit.py",
"py": '''"""Report the outbound call failure rate, bucketed by direction and destination.

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
log = logging.getLogger("twilio_call_failure_rate_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

# Statuses that are an outcome. queued, ringing and in-progress are calls that
# have not finished yet: counting them would move the rate purely by when the
# script happened to run.
OUTCOMES = ("completed", "failed", "busy", "no-answer", "canceled")


def dial_prefix(to, digits=3):
    """Bucket a destination by its leading digits.

    SIP URIs and client identities get their own buckets rather than being
    stripped down to whatever digits they happen to contain, because a failure
    rate on sip: destinations is a completely different investigation from one
    on a country prefix.
    """
    v = str(to or "").strip()
    if not v:
        return "unknown"
    low = v.lower()
    if low.startswith("sip:") or low.startswith("sips:"):
        return "sip"
    if low.startswith("client:"):
        return "client"
    d = "".join(c for c in v if c.isdigit())
    if not d:
        return "unknown"
    return "+" + d[:digits]


def summarise(calls, digits=3):
    """Group outbound calls into (direction, prefix) buckets of outcomes.

    Pure, and deliberately tolerant: an unexpected status is skipped rather than
    counted as a failure, because a status this script does not know about is
    not evidence of anything.
    """
    buckets = {}
    for c in calls:
        status = str(c.get("status") or "").strip().lower()
        if status not in OUTCOMES:
            continue
        direction = str(c.get("direction") or "unknown").strip().lower()
        if not direction.startswith("outbound"):
            continue
        key = (direction, dial_prefix(c.get("to"), digits))
        b = buckets.setdefault(key, {"total": 0, "completed": 0, "failed": 0,
                                     "busy": 0, "no_answer": 0, "canceled": 0})
        b["total"] += 1
        b[status.replace("-", "_")] += 1
    return buckets


def verdict(bucket, floor=20, threshold=0.10):
    """Judge one bucket. Pure, and the thresholds are arguments so the boundary
    cases can be tested rather than argued about.

    Returns (state, detail).
    """
    total = bucket.get("total", 0)
    failed = bucket.get("failed", 0)
    share = (failed / total) if total else 0.0
    pct = "%.1f%%" % (share * 100)

    if total < floor:
        return ("low-volume",
                "%d call(s) is too few to read a rate from: %d failed, which is "
                "%s of nothing much." % (total, failed, pct))
    if failed == total:
        return ("total-failure",
                "every one of %d call(s) failed. This is not a rate, it is a "
                "destination or a permission that is off." % total)
    if share >= threshold:
        return ("elevated",
                "%d of %d call(s) failed (%s), against a threshold of %.0f%%. "
                "busy=%d no-answer=%d."
                % (failed, total, pct, threshold * 100,
                   bucket.get("busy", 0), bucket.get("no_answer", 0)))
    return ("ok", "%d of %d call(s) failed (%s)" % (failed, total, pct))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_calls(session, account, since, limit, status=None):
    """Page the Calls list. next_page_uri here is a path, not an absolute URL.

    There is no ErrorCode filter on this resource, and StartTime>= is the only
    way to bound the window, so everything else is done client-side.
    """
    url = "%s/Accounts/%s/Calls.json" % (BASE, account)
    params = {"StartTime>=": since, "PageSize": 1000}
    if status:
        params["Status"] = status
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("calls", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def alert_codes(session, since, limit, levels):
    """Error codes seen in the window, counted, across both log levels.

    Sweeping error alone is the mistake worth avoiding here: some of the codes
    that explain a voice failure rate, including several 132xx Dial attribute
    errors, are logged at warning.
    """
    seen = {}
    for level in levels:
        url = MONITOR + "/Alerts"
        params = {"LogLevel": level, "StartDate": since, "PageSize": 1000}
        got = 0
        while url and got < limit:
            page = get(session, url, **params)
            for a in page.get("alerts", []):
                seen.setdefault(a.get("sid"), str(a.get("error_code") or "?"))
                got += 1
            url = (page.get("meta") or {}).get("next_page_url")
            params = {}
    counts = {}
    for code in seen.values():
        counts[code] = counts.get(code, 0) + 1
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7, help="window size in days")
    ap.add_argument("--prefix-digits", type=int, default=3,
                    help="how many leading digits of `to` make a bucket")
    ap.add_argument("--floor", type=int, default=20,
                    help="minimum calls before a bucket's rate is judged")
    ap.add_argument("--threshold", type=float, default=0.10,
                    help="failure share at which a bucket is elevated")
    ap.add_argument("--max-calls", type=int, default=20000,
                    help="stop after this many calls per sweep")
    ap.add_argument("--all-statuses", action="store_true",
                    help="one unfiltered sweep, so busy and no-answer are in "
                         "the denominator too")
    ap.add_argument("--with-alerts", action="store_true",
                    help="also count Debugger alerts in the window, at both "
                         "the error and warning log levels")
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

    if args.all_statuses:
        calls = list_calls(session, account, since, args.max_calls)
    else:
        calls = (list_calls(session, account, since, args.max_calls, "failed")
                 + list_calls(session, account, since, args.max_calls, "completed"))
        log.info("busy and no-answer are not in this denominator: "
                 "re-run with --all-statuses for the full outcome mix")

    buckets = summarise(calls, args.prefix_digits)
    if not buckets:
        log.info("no outbound calls in the last %d day(s)", args.days)
        return 0

    total = sum(b["total"] for b in buckets.values())
    failed = sum(b["failed"] for b in buckets.values())
    elevated = 0
    for key in sorted(buckets, key=lambda k: -buckets[k]["failed"]):
        direction, prefix = key
        state, detail = verdict(buckets[key], args.floor, args.threshold)
        line = "%-14s %-14s %-8s %s" % (state, direction, prefix, detail)
        if state in ("elevated", "total-failure"):
            elevated += 1
            log.warning(line)
        else:
            log.info(line)

    if args.with_alerts:
        counts = alert_codes(session, since, 10000, ["error", "warning"])
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
        log.info("alerts in window (error and warning): %s",
                 ", ".join("%s=%d" % kv for kv in top) or "none")

    share = (failed / total * 100) if total else 0.0
    log.info("%d outbound call(s), %d failed (%.1f%%), %d elevated bucket(s)",
             total, failed, share, elevated)
    if elevated:
        log.warning("  repair: pull the signalling detail for a call in the worst "
                    "bucket with GET %s/Accounts/%s/Calls/{CallSid}/Events.json, "
                    "then fix the cause it points at: geo permissions, E.164 "
                    "normalisation, or caller ID reputation", BASE, account)
    return 1 if elevated else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-call-failure-rate-audit.mjs",
"js": '''/**
 * Report the outbound call failure rate, bucketed by direction and destination.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

// Statuses that are an outcome. queued, ringing and in-progress have not
// finished, and counting them moves the rate by when the script ran.
const OUTCOMES = new Set(['completed', 'failed', 'busy', 'no-answer', 'canceled']);

/**
 * Bucket a destination by its leading digits. SIP URIs and client identities
 * get their own buckets rather than being stripped to whatever digits they
 * contain.
 */
export function dialPrefix(to, digits = 3) {
  const v = String(to ?? '').trim();
  if (!v) return 'unknown';
  const low = v.toLowerCase();
  if (low.startsWith('sip:') || low.startsWith('sips:')) return 'sip';
  if (low.startsWith('client:')) return 'client';
  const d = v.replace(/[^0-9]/g, '');
  if (!d) return 'unknown';
  return `+${d.slice(0, digits)}`;
}

/**
 * Group outbound calls into direction/prefix buckets of outcomes. Pure, and
 * deliberately tolerant: an unexpected status is skipped rather than counted as
 * a failure. Returns a Map keyed by `${direction}|${prefix}`.
 */
export function summarise(calls, digits = 3) {
  const buckets = new Map();
  for (const c of calls) {
    const status = String(c.status ?? '').trim().toLowerCase();
    if (!OUTCOMES.has(status)) continue;
    const direction = String(c.direction ?? 'unknown').trim().toLowerCase();
    if (!direction.startsWith('outbound')) continue;
    const key = `${direction}|${dialPrefix(c.to, digits)}`;
    if (!buckets.has(key)) {
      buckets.set(key, { total: 0, completed: 0, failed: 0, busy: 0,
                         no_answer: 0, canceled: 0 });
    }
    const b = buckets.get(key);
    b.total += 1;
    b[status.replace('-', '_')] += 1;
  }
  return buckets;
}

/**
 * Judge one bucket. Pure, and the thresholds are arguments so the boundary
 * cases can be tested. Returns [state, detail].
 */
export function verdict(bucket, floor = 20, threshold = 0.10) {
  const total = bucket.total ?? 0;
  const failed = bucket.failed ?? 0;
  const share = total ? failed / total : 0;
  const pct = `${(share * 100).toFixed(1)}%`;

  if (total < floor) {
    return ['low-volume',
      `${total} call(s) is too few to read a rate from: ${failed} failed, ` +
      `which is ${pct} of nothing much.`];
  }
  if (failed === total) {
    return ['total-failure',
      `every one of ${total} call(s) failed. This is not a rate, it is a ` +
      'destination or a permission that is off.'];
  }
  if (share >= threshold) {
    return ['elevated',
      `${failed} of ${total} call(s) failed (${pct}), against a threshold of ` +
      `${(threshold * 100).toFixed(0)}%. busy=${bucket.busy ?? 0} ` +
      `no-answer=${bucket.no_answer ?? 0}.`];
  }
  return ['ok', `${failed} of ${total} call(s) failed (${pct})`];
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

/** Page the Calls list. next_page_uri here is a path, not an absolute URL. */
export async function listCalls(auth, account, since, limit, status = null) {
  let url = `${BASE}/Accounts/${account}/Calls.json`;
  let params = { 'StartTime>=': since, PageSize: 1000 };
  if (status) params.Status = status;
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.calls ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Error codes in the window, across both log levels, de-duplicated on sid. */
export async function alertCodes(auth, since, limit, levels) {
  const seen = new Map();
  for (const level of levels) {
    let url = `${MONITOR}/Alerts`;
    let params = { LogLevel: level, StartDate: since, PageSize: 1000 };
    while (url && seen.size < limit) {
      const page = await get(auth, url, params);
      for (const a of page.alerts ?? []) {
        if (!seen.has(a.sid)) seen.set(a.sid, String(a.error_code ?? '?'));
      }
      url = page.meta?.next_page_url ?? null;
      params = {};
    }
  }
  const counts = new Map();
  for (const code of seen.values()) counts.set(code, (counts.get(code) ?? 0) + 1);
  return counts;
}

function arg(name, fallback) {
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
  const days = arg('--days', 7);
  const digits = arg('--prefix-digits', 3);
  const floor = arg('--floor', 20);
  const threshold = arg('--threshold', 0.10);
  const maxCalls = arg('--max-calls', 20000);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  let calls;
  if (process.argv.includes('--all-statuses')) {
    calls = await listCalls(auth, account, since, maxCalls);
  } else {
    calls = [...await listCalls(auth, account, since, maxCalls, 'failed'),
             ...await listCalls(auth, account, since, maxCalls, 'completed')];
    console.log('busy and no-answer are not in this denominator: ' +
                're-run with --all-statuses for the full outcome mix');
  }

  const buckets = summarise(calls, digits);
  if (buckets.size === 0) {
    console.log(`no outbound calls in the last ${days} day(s)`);
    return;
  }

  let total = 0;
  let failed = 0;
  let elevated = 0;
  const keys = [...buckets.keys()].sort((a, b) => buckets.get(b).failed - buckets.get(a).failed);
  for (const k of keys) {
    const b = buckets.get(k);
    total += b.total;
    failed += b.failed;
    const [direction, prefix] = k.split('|');
    const [state, detail] = verdict(b, floor, threshold);
    const line = `${state.padEnd(14)} ${direction.padEnd(14)} ${prefix.padEnd(8)} ${detail}`;
    if (state === 'elevated' || state === 'total-failure') { elevated += 1; console.warn(line); }
    else console.log(line);
  }

  if (process.argv.includes('--with-alerts')) {
    const counts = await alertCodes(auth, since, 10000, ['error', 'warning']);
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    console.log(`alerts in window (error and warning): ${
      top.map(([c, n]) => `${c}=${n}`).join(', ') || 'none'}`);
  }

  const share = total ? (failed / total) * 100 : 0;
  console.log(`${total} outbound call(s), ${failed} failed (${share.toFixed(1)}%), ` +
              `${elevated} elevated bucket(s)`);
  if (elevated) {
    console.warn('  repair: pull the signalling detail for a call in the worst bucket ' +
                 `with GET ${BASE}/Accounts/${account}/Calls/{CallSid}/Events.json, then ` +
                 'fix the cause it points at: geo permissions, E.164 normalisation, ' +
                 'or caller ID reputation');
  }
  process.exitCode = elevated ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail on the missing credentials.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Rate checks are wrong at the edges or not at all, so the tests are almost entirely edges: the bucket that is one call below the floor, the bucket exactly on the threshold, the bucket where everything failed. The bucketing tests pin the two decisions that quietly corrupt a report &mdash; that a call still ringing is not an outcome, and that a <code>sip:</code> destination is not a phone number with unusual punctuation.",
"test_py_file": "test_twilio_call_failure_rate_audit.py",
"test_py": '''from twilio_call_failure_rate_audit import dial_prefix, summarise, verdict


def calls(n, status, to="+15005550006", direction="outbound-api"):
    return [{"status": status, "to": to, "direction": direction} for _ in range(n)]


def test_prefix_uses_leading_digits_only():
    assert dial_prefix("+15005550006") == "+150"
    assert dial_prefix("+44 20 7946 0000", digits=2) == "+44"


def test_sip_and_client_destinations_are_their_own_buckets():
    assert dial_prefix("sip:pbx@example.com") == "sip"
    assert dial_prefix("client:alice") == "client"
    assert dial_prefix("") == "unknown"


def test_calls_still_in_flight_are_not_an_outcome():
    # Counting ringing calls would move the rate with the clock rather than
    # with anything that happened.
    assert summarise(calls(5, "ringing")) == {}


def test_inbound_calls_are_not_in_the_outbound_rate():
    assert summarise(calls(5, "failed", direction="inbound")) == {}


def test_buckets_split_on_direction_and_prefix():
    rows = (calls(3, "failed") + calls(2, "completed")
            + calls(4, "failed", direction="outbound-dial"))
    buckets = summarise(rows)
    assert set(buckets) == {("outbound-api", "+150"), ("outbound-dial", "+150")}
    assert buckets[("outbound-api", "+150")]["total"] == 5
    assert buckets[("outbound-dial", "+150")]["failed"] == 4


def test_a_small_bucket_is_never_elevated():
    state, detail = verdict({"total": 4, "failed": 3}, floor=20)
    assert state == "low-volume"
    assert "too few" in detail


def test_exactly_on_the_threshold_is_elevated():
    state, _ = verdict({"total": 100, "failed": 10}, floor=20, threshold=0.10)
    assert state == "elevated"


def test_just_below_the_threshold_is_ok():
    assert verdict({"total": 100, "failed": 9}, floor=20, threshold=0.10)[0] == "ok"


def test_everything_failing_is_not_reported_as_a_rate():
    state, detail = verdict({"total": 40, "failed": 40}, floor=20)
    assert state == "total-failure"
    assert "permission" in detail


def test_a_bucket_with_no_calls_does_not_divide_by_zero():
    assert verdict({"total": 0, "failed": 0})[0] == "low-volume"
''',
"test_js_file": "twilio-call-failure-rate-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dialPrefix, summarise, verdict } from './twilio-call-failure-rate-audit.mjs';

function calls(n, status, to = '+15005550006', direction = 'outbound-api') {
  return Array.from({ length: n }, () => ({ status, to, direction }));
}

test('prefix uses leading digits only', () => {
  assert.equal(dialPrefix('+15005550006'), '+150');
  assert.equal(dialPrefix('+44 20 7946 0000', 2), '+44');
});

test('sip and client destinations are their own buckets', () => {
  assert.equal(dialPrefix('sip:pbx@example.com'), 'sip');
  assert.equal(dialPrefix('client:alice'), 'client');
  assert.equal(dialPrefix(''), 'unknown');
});

test('calls still in flight are not an outcome', () => {
  assert.equal(summarise(calls(5, 'ringing')).size, 0);
});

test('inbound calls are not in the outbound rate', () => {
  assert.equal(summarise(calls(5, 'failed', '+15005550006', 'inbound')).size, 0);
});

test('buckets split on direction and prefix', () => {
  const rows = [...calls(3, 'failed'), ...calls(2, 'completed'),
                ...calls(4, 'failed', '+15005550006', 'outbound-dial')];
  const buckets = summarise(rows);
  assert.deepEqual([...buckets.keys()].sort(),
                   ['outbound-api|+150', 'outbound-dial|+150']);
  assert.equal(buckets.get('outbound-api|+150').total, 5);
  assert.equal(buckets.get('outbound-dial|+150').failed, 4);
});

test('a small bucket is never elevated', () => {
  const [state, detail] = verdict({ total: 4, failed: 3 }, 20);
  assert.equal(state, 'low-volume');
  assert.match(detail, /too few/);
});

test('exactly on the threshold is elevated', () => {
  assert.equal(verdict({ total: 100, failed: 10 }, 20, 0.10)[0], 'elevated');
});

test('just below the threshold is ok', () => {
  assert.equal(verdict({ total: 100, failed: 9 }, 20, 0.10)[0], 'ok');
});

test('everything failing is not reported as a rate', () => {
  const [state, detail] = verdict({ total: 40, failed: 40 }, 20);
  assert.equal(state, 'total-failure');
  assert.match(detail, /permission/);
});

test('a bucket with no calls does not divide by zero', () => {
  assert.equal(verdict({ total: 0, failed: 0 })[0], 'low-volume');
});
''',
"faq": [
 ("What does status failed actually mean?",
  "That the call could not be completed as dialled. It covers a destination that does not exist, a carrier rejection, a geo-permission block and an unreachable SIP leg, all under one word. It is distinct from busy and no-answer, which are calls that reached the destination and were not answered."),
 ("Why does the script fetch completed calls at all?",
  "Because a numerator without a denominator is not a rate. A count of failures rises with traffic, so any threshold set on it either fires every time you have a good week or never fires at all. Fetching both sides over the same window is the only way to make the number comparable to last week's."),
 ("Why are busy and no-answer missing from the default run?",
  "Because the default does two Status-filtered sweeps, which is cheap, and neither of them fetches those. The failure share is then computed against completed calls alone, which is defensible as long as you know it. --all-statuses does one unfiltered sweep and gives you the true outcome mix at the cost of a great deal more paging."),
 ("Why sweep the Debugger at the warning level too?",
  "Because Twilio raises an alert for only some of these failures and some of those alerts are warnings rather than errors, including several 132xx Dial attribute errors and the 32012 CPS alerts. Cross-referencing at LogLevel=error alone shows a quiet Debugger next to a failing service, which is worse than not looking."),
 ("How long a window should this run over?",
  "Long enough that the smallest bucket you care about clears the volume floor, and short enough that a change is still visible rather than averaged away. A week is a reasonable default for most accounts. The Alerts cross-reference is capped at 30 days regardless, because that is Twilio's retention."),
],
"related": [
 ("/twilio/dial-invalid-caller-id-13214/", "Dial rejected with 13214 on a passed-through caller ID"),
 ("/twilio/trunk-missing-disaster-recovery-url/", "A trunk with no disaster recovery URL"),
 ("/twilio/webhook-connection-timeout-11205/", "A webhook that times out with 11205"),
],
"citations": [CITE_CALL, CITE_ALERT, CITE_TWIML_DIAL, CITE_KEYS],
},

]
