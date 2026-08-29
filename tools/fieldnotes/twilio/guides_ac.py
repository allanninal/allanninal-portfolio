#!/usr/bin/env python3
"""/twilio/ field notes, batch AC — the last five, and the writing.

The same constraint as every other batch: each note is a problem a script can
find with a READ-ONLY Twilio credential, an API Key with read access rather than
the account auth token. These scripts hold a credential to an account that can
send messages and spend money, so none of them writes. They read, they say what
is wrong, and they print the repair for a human to run.

Two of the five are deliberately narrow siblings of notes that already exist.
The 11200 here is the inbound TwiML fetch, not the status callback: a lost
receipt and a dropped call are the same error code and different incidents. The
12200 here is TwiML that parses and then fails the schema, logged at warning
rather than error, which is why an error-only sweep has never seen one.
"""

CITE_VERIFY_SERVICE = ("Verify Service resource — Twilio Docs",
                       "https://www.twilio.com/docs/verify/api/service")
CITE_60205 = ("Error 60205: SMS is not supported by landline phone number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/60205")
CITE_LTI = ("Lookup Line Type Intelligence — Twilio Docs",
            "https://www.twilio.com/docs/lookup/v2-api/line-type-intelligence")
CITE_LOOKUP = ("Lookup v2 API — Twilio Docs", "https://www.twilio.com/docs/lookup/v2-api")
CITE_21211 = ("Error 21211: invalid 'To' phone number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21211")
CITE_60600 = ("Error 60600: unprovisioned or out of coverage — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/60600")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_11200 = ("Error 11200: HTTP retrieval failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11200")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_WEBHOOKS = ("Webhooks (HTTP callbacks) — Twilio Docs",
                 "https://www.twilio.com/docs/usage/webhooks")
CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_12200 = ("Error 12200: schema validation warning — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/12200")
CITE_12100 = ("Error 12100: document parse failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/12100")
CITE_TWIML_VOICE = ("TwiML for Programmable Voice — Twilio Docs",
                    "https://www.twilio.com/docs/voice/twiml")
CITE_63040 = ("Error 63040: WhatsApp template rejected — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/63040")
CITE_63016 = ("Error 63016: freeform message outside the 24 hour window — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/63016")
CITE_WA_TEMPLATES = ("WhatsApp message template approval statuses — Twilio Docs",
                     "https://www.twilio.com/docs/whatsapp/tutorial/"
                     "message-template-approvals-statuses")
CITE_CONTENT = ("Content API resources — Twilio Docs",
                "https://www.twilio.com/docs/content/content-api-resources")

GUIDES = [

{
"slug": "verify-lookup-disabled",
"title": "Verify runs with lookup_enabled false, so landlines are billed",
"description": "skip_sms_to_landlines needs lookup_enabled and it is off by default. Verify sends into landlines at full price and 60205 never reaches your logs.",
"h1": "Verify runs with lookup_enabled false, so landlines are billed",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio lookup_enabled false", "skip_sms_to_landlines not working",
             "verify service lookup disabled", "twilio verify landline billing",
             "verify service settings audit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody switched on <em>skip SMS to landlines</em> months ago, the setting is still there in the console, and Verify has been sending SMS into landlines the entire time. The guard needs a Lookup on each verification start to know what a landline is, and Lookup is off &mdash; so the switch is set, saved, displayed back to you, and doing nothing at all.",
"short_answer": """<p>Read <code>GET https://verify.twilio.com/v2/Services</code> and, per service, <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}</code>. The finding is <code>lookup_enabled == false</code>, and the sharp version of it is <code>skip_sms_to_landlines</code> <code>true</code> while <code>lookup_enabled</code> is <code>false</code> &mdash; a guard that cannot run.</p>
<p><code>lookup_enabled</code> is off when a service is created. With it off Verify never classifies the destination line type, so it sends the SMS, bills the attempt at the full verification price, and logs no <code>60205</code> for you to find later. The attempt simply stays <code>pending</code> until it expires.</p>""",
"problem": """<p>This one costs money quietly rather than breaking anything loudly. A verification started against a landline is a verification Twilio accepted, priced and attempted. It comes back <code>pending</code>, it expires, and the user tries again on a different number or gives up. There is no failed send in the Messages list, no <code>60205</code> in the Debugger, and no alert &mdash; because from the platform's side nothing failed. Verify was asked to send an SMS and it sent one.</p>
<p>What makes it durable is that the visible setting is the wrong one. <code>skip_sms_to_landlines</code> is the switch with the obvious name, it is the one people turn on, and turning it on succeeds. The dependency runs the other way: the skip is implemented <em>by</em> the Lookup that <code>lookup_enabled</code> authorises. Set one without the other and you have bought a guard with nothing behind it, which is worse than having no guard, because now the question looks answered.</p>""",
"why": """<p><strong>The default is off, and it is off per service.</strong> Every Verify Service you create arrives with <code>lookup_enabled</code> <code>false</code>. An account that has three services &mdash; production, staging, and the one made for a partner integration &mdash; has three separate copies of this setting and no reason for them to agree.</p>
<p><strong>The two fields do not validate each other.</strong> Setting <code>SkipSmsToLandlines=true</code> on a service whose <code>lookup_enabled</code> is <code>false</code> returns 200 and stores the value. Nothing warns you, and reading the service back shows exactly what you set. The inconsistency is only visible if you know that one field is a prerequisite of the other.</p>
<p><strong>The failure produces no error code.</strong> <code>60205</code> is what you get when Verify <em>knows</em> the destination is a landline and refuses. With Lookup off it never knows, so the code that would have named this problem for you is precisely the code that cannot be emitted.</p>
<p><strong>A 4% shortfall reads as user behaviour.</strong> Conversion rates never hit 100%, so a permanent slice of unconverted attempts is easy to file under mistyped numbers and abandoned signups. It stays filed there until somebody asks which numbers those attempts went to.</p>""",
"steps": [
 {"h": "List every Verify Service, not just the one you think is live",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services</code>, following <code>meta.next_page_url</code>. Services accumulate: one per environment, one per brand, one left over from an integration test. Each carries its own <code>lookup_enabled</code>, and the one that is misconfigured is rarely the one you would have checked by hand.</p>"""},
 {"h": "Read the two settings as a pair, never singly",
  "body": """<p><code>lookup_enabled</code> and <code>skip_sms_to_landlines</code> have four combinations and three of them are wrong in different ways. Reporting on either field alone gives you a green tick for the combination that is actively costing you money.</p>"""},
 {"h": "Name the no-op configuration explicitly",
  "body": """<p><code>skip_sms_to_landlines</code> <code>true</code> with <code>lookup_enabled</code> <code>false</code> deserves its own line in the report and its own wording. Anyone reading a list of services where this one says <em>lookup off</em> will assume the landline guard was never configured; the point is that it was, and it is not running.</p>"""},
 {"h": "Weigh it by traffic before you weigh it by badness",
  "body": """<p><code>GET https://verify.twilio.com/v2/Attempts?DateCreatedAfter={ISO8601}</code> returns attempts across the account with a <code>service_sid</code> on each. Counting per service turns a list of five misconfigured services into one that is billing you daily and four that are dormant.</p>"""},
 {"h": "Turn on Lookup first, then the skip, then re-run",
  "body": """<p><code>POST https://verify.twilio.com/v2/Services/{ServiceSid}</code> with <code>LookupEnabled=true</code> and <code>SkipSmsToLandlines=true</code>. Enabling Lookup adds a per-verification cost of its own, which is the honest trade and worth stating in the ticket: you pay for a Lookup on every start instead of paying for an SMS that could never arrive.</p>"""},
],
"verify": """<p>Re-run the script. Every service that sends SMS should report <code>guarded</code>, and no service should report <code>no-op-guard</code>.</p>
<pre><code class="language-bash">python3 twilio_verify_lookup_audit.py --check-traffic
# 3 service(s), 0 sending SMS without a line type check</code></pre>""",
"code_intro": "One paginated GET for the services and, with <code>--check-traffic</code>, one more for recent attempts &mdash; an API Key with read access is enough and is what you should give it. The classifier is pure and takes both booleans together, because the whole content of this note is that reading either one alone gives you the wrong answer.",
"py_file": "twilio_verify_lookup_audit.py",
"py": '''"""Report Verify Services that send SMS without a line type check.

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
log = logging.getLogger("twilio_verify_lookup_audit")

VERIFY = "https://verify.twilio.com/v2"


def attempts_for(attempts, service_sid):
    """Count verification attempts belonging to one service.

    Pure. The Attempts list is account-wide, so the per-service number that sets
    urgency has to be produced here rather than asked for.
    """
    return sum(1 for a in attempts if a.get("service_sid") == service_sid)


def verdict(service, attempts=None):
    """Classify one Verify Service's landline protection. Pure, so the rule can
    be tested without a network.

    `attempts` is the count of recent verification attempts on this service, or
    None when traffic was not checked. Returns (state, detail).
    """
    lookup = bool(service.get("lookup_enabled"))
    skip = bool(service.get("skip_sms_to_landlines"))

    if lookup and skip:
        return ("guarded",
                "lookup_enabled and skip_sms_to_landlines are both true: the "
                "line type is checked and landlines are not sent to.")

    if lookup and not skip:
        return ("lookup-only",
                "lookup_enabled is true but skip_sms_to_landlines is false: you "
                "pay for a Lookup on every start and still send SMS to "
                "landlines.")

    if skip:
        return ("no-op-guard",
                "skip_sms_to_landlines is true while lookup_enabled is false. "
                "The skip is implemented by that Lookup, so it never runs: this "
                "service is configured to protect landlines and does not.")

    busy = "" if attempts is None else " %d attempt(s) in the window." % attempts
    if attempts:
        return ("unguarded",
                "lookup_enabled is false, so every attempt is sent blind and "
                "billed in full; 60205 is never logged because the line type is "
                "never read." + busy)

    return ("unguarded-idle",
            "lookup_enabled is false. No attempts seen in the window, so this "
            "is a setting to fix before the service is used rather than a bill "
            "to stop." + busy)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v2(session, url, key, limit=1000, **params):
    """Page a verify.twilio.com list. meta.next_page_url is absolute."""
    out = []
    params.setdefault("PageSize", 50)
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url, params = (page.get("meta") or {}).get("next_page_url"), {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="window for the attempt count")
    ap.add_argument("--check-traffic", action="store_true",
                    help="one extra paginated GET to weigh each service by use")
    ap.add_argument("--max-services", type=int, default=200)
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

    services = list_v2(session, VERIFY + "/Services", "services", args.max_services)
    if not services:
        log.info("no Verify Services on this account")
        return 0

    attempts = None
    if args.check_traffic:
        since = (dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        attempts = list_v2(session, VERIFY + "/Attempts", "attempts", 5000,
                           DateCreatedAfter=since)

    bad = 0
    for svc in services:
        seen = None if attempts is None else attempts_for(attempts, svc.get("sid"))
        state, detail = verdict(svc, seen)
        line = "%-15s %s  %s" % (state, svc.get("friendly_name", svc.get("sid")), detail)
        if state == "guarded":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: POST %s/Services/%s LookupEnabled=true "
                    "SkipSmsToLandlines=true", VERIFY, svc.get("sid"))

    log.info("%d service(s), %d sending SMS without a line type check",
             len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-lookup-audit.mjs",
"js": '''/**
 * Report Verify Services that send SMS without a line type check.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';

/**
 * Count verification attempts belonging to one service. Pure: the Attempts list
 * is account-wide, so the per-service number has to be produced here.
 */
export function attemptsFor(attempts, serviceSid) {
  return attempts.filter((a) => a.service_sid === serviceSid).length;
}

/**
 * Classify one Verify Service's landline protection. Pure, so the rule can be
 * tested without a network. `attempts` is null when traffic was not checked.
 * Returns [state, detail].
 */
export function verdict(service, attempts = null) {
  const lookup = Boolean(service.lookup_enabled);
  const skip = Boolean(service.skip_sms_to_landlines);

  if (lookup && skip) {
    return ['guarded',
      'lookup_enabled and skip_sms_to_landlines are both true: the line type ' +
      'is checked and landlines are not sent to.'];
  }

  if (lookup && !skip) {
    return ['lookup-only',
      'lookup_enabled is true but skip_sms_to_landlines is false: you pay for ' +
      'a Lookup on every start and still send SMS to landlines.'];
  }

  if (skip) {
    return ['no-op-guard',
      'skip_sms_to_landlines is true while lookup_enabled is false. The skip ' +
      'is implemented by that Lookup, so it never runs: this service is ' +
      'configured to protect landlines and does not.'];
  }

  const busy = attempts === null ? '' : ` ${attempts} attempt(s) in the window.`;
  if (attempts) {
    return ['unguarded',
      'lookup_enabled is false, so every attempt is sent blind and billed in ' +
      'full; 60205 is never logged because the line type is never read.' + busy];
  }

  return ['unguarded-idle',
    'lookup_enabled is false. No attempts seen in the window, so this is a ' +
    'setting to fix before the service is used rather than a bill to stop.' + busy];
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

export async function listV2(auth, url, key, limit = 1000, params = {}) {
  const out = [];
  let next = url;
  let query = { PageSize: 50, ...params };
  while (next && out.length < limit) {
    const page = await get(auth, next, query);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    query = {};
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
  const days = Number(process.env.DAYS ?? 7);
  const checkTraffic = process.argv.includes('--check-traffic');

  const services = await listV2(auth, `${VERIFY}/Services`, 'services');
  if (services.length === 0) {
    console.log('no Verify Services on this account');
    return;
  }

  let attempts = null;
  if (checkTraffic) {
    const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 19) + 'Z';
    attempts = await listV2(auth, `${VERIFY}/Attempts`, 'attempts', 5000,
                            { DateCreatedAfter: since });
  }

  let bad = 0;
  for (const svc of services) {
    const seen = attempts === null ? null : attemptsFor(attempts, svc.sid);
    const [state, detail] = verdict(svc, seen);
    const line = `${state.padEnd(15)} ${svc.friendly_name ?? svc.sid}  ${detail}`;
    if (state === 'guarded') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: POST ${VERIFY}/Services/${svc.sid} ` +
                 'LookupEnabled=true SkipSmsToLandlines=true');
  }

  console.log(`${services.length} service(s), ${bad} sending SMS without a line type check`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case the whole note exists for is the third one: <code>skip_sms_to_landlines</code> <code>true</code>, <code>lookup_enabled</code> <code>false</code>. A classifier that checks the skip flag and stops reports that service as protected, which is the same conclusion the console invites you to draw. The other combination worth pinning is lookup on with the skip off, because it is not free &mdash; you are paying for a Lookup whose answer is then ignored.",
"test_py_file": "test_twilio_verify_lookup_audit.py",
"test_py": '''from twilio_verify_lookup_audit import attempts_for, verdict


def test_both_settings_on_is_the_only_guarded_state():
    state, detail = verdict({"lookup_enabled": True, "skip_sms_to_landlines": True})
    assert state == "guarded"
    assert "line type is checked" in detail


def test_skip_without_lookup_is_a_guard_that_never_runs():
    # The reason this note exists: the visible setting is on and inert.
    state, detail = verdict({"lookup_enabled": False, "skip_sms_to_landlines": True})
    assert state == "no-op-guard"
    assert "never runs" in detail


def test_lookup_without_skip_still_sends_to_landlines():
    state, detail = verdict({"lookup_enabled": True, "skip_sms_to_landlines": False})
    assert state == "lookup-only"
    assert "pay for a Lookup" in detail


def test_both_off_with_traffic_is_the_billing_finding():
    state, detail = verdict({"lookup_enabled": False}, 412)
    assert state == "unguarded"
    assert "412 attempt(s)" in detail
    assert "60205" in detail


def test_both_off_with_no_traffic_is_separated_from_the_live_one():
    state, detail = verdict({"lookup_enabled": False, "skip_sms_to_landlines": False}, 0)
    assert state == "unguarded-idle"
    assert "before the service is used" in detail


def test_missing_fields_are_read_as_the_defaults_they_are():
    # A service resource with neither field set is a new service: both are off.
    assert verdict({})[0] == "unguarded-idle"


def test_attempts_are_counted_per_service_from_an_account_wide_list():
    attempts = [{"service_sid": "VA1"}, {"service_sid": "VA2"}, {"service_sid": "VA1"}]
    assert attempts_for(attempts, "VA1") == 2
    assert attempts_for(attempts, "VA3") == 0
''',
"test_js_file": "twilio-verify-lookup-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attemptsFor, verdict } from './twilio-verify-lookup-audit.mjs';

test('both settings on is the only guarded state', () => {
  const [state, detail] = verdict({ lookup_enabled: true, skip_sms_to_landlines: true });
  assert.equal(state, 'guarded');
  assert.match(detail, /line type is checked/);
});

test('skip without lookup is a guard that never runs', () => {
  const [state, detail] = verdict({ lookup_enabled: false, skip_sms_to_landlines: true });
  assert.equal(state, 'no-op-guard');
  assert.match(detail, /never runs/);
});

test('lookup without skip still sends to landlines', () => {
  const [state, detail] = verdict({ lookup_enabled: true, skip_sms_to_landlines: false });
  assert.equal(state, 'lookup-only');
  assert.match(detail, /pay for a Lookup/);
});

test('both off with traffic is the billing finding', () => {
  const [state, detail] = verdict({ lookup_enabled: false }, 412);
  assert.equal(state, 'unguarded');
  assert.match(detail, /412 attempt\\(s\\)/);
  assert.match(detail, /60205/);
});

test('both off with no traffic is separated from the live one', () => {
  const [state, detail] = verdict({ lookup_enabled: false, skip_sms_to_landlines: false }, 0);
  assert.equal(state, 'unguarded-idle');
  assert.match(detail, /before the service is used/);
});

test('missing fields are read as the defaults they are', () => {
  assert.equal(verdict({})[0], 'unguarded-idle');
});

test('attempts are counted per service from an account wide list', () => {
  const attempts = [{ service_sid: 'VA1' }, { service_sid: 'VA2' }, { service_sid: 'VA1' }];
  assert.equal(attemptsFor(attempts, 'VA1'), 2);
  assert.equal(attemptsFor(attempts, 'VA3'), 0);
});
''',
"faq": [
 ("Why does skip_sms_to_landlines need lookup_enabled?",
  "Because the skip is implemented by the Lookup. Verify has no idea what kind of line a destination is until it performs a Lookup on the verification start, and lookup_enabled is the field that authorises that call. With it false there is no line type to compare against, so there is nothing for the skip to act on."),
 ("Shouldn't Twilio reject the inconsistent combination?",
  "It does not. POSTing SkipSmsToLandlines=true to a service with lookup_enabled false returns 200 and stores the value, and reading the service back shows exactly what you set. That is why an audit that reads both fields together is the only way to see it."),
 ("Why is there no 60205 in the logs?",
  "60205 is Verify refusing to send because it knows the destination is a landline. Knowing requires the Lookup. With Lookup off Verify never forms that opinion, so the one error code that would have named this problem is the code that cannot be emitted."),
 ("Does turning on Lookup cost more?",
  "Yes, and it is worth saying so in the ticket rather than discovering it on the invoice. You pay for a Lookup on every verification start instead of paying for an SMS that could never be delivered, plus the support cost of the users who never got a code."),
 ("Why does the script count attempts per service?",
  "Because the Attempts list is account-wide and the decision is per service. Five services with lookup off are not five equal problems: one of them is billing you today and the other four are dormant settings to correct before anything is routed through them."),
],
"related": [
 ("/twilio/verify-sms-to-landline/", "Verify sending SMS to a landline: 60205, or silence"),
 ("/twilio/landline-destination-30006/", "Sending SMS to landlines that can never receive it"),
 ("/twilio/verify-conversion-rate-collapse/", "Verify conversion collapsing in one country"),
],
"citations": [CITE_VERIFY_SERVICE, CITE_60205, CITE_LTI, CITE_KEYS],
},


{
"slug": "lookup-invalid-or-uncovered-number",
"title": "An invalid or uncovered number: 21211 on send, 60600 on Lookup",
"description": "Twilio does no fuzzy parsing. A national-format number stored years ago fails with 21211, and a range no carrier was ever assigned comes back 60600.",
"h1": "an invalid or uncovered number: 21211 on send, 60600 on Lookup",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 21211", "twilio 60600", "lookup validation_errors",
             "e164 normalisation twilio", "twilio invalid to phone number"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The contact table has been filling up since before anyone thought about E.164. Some rows are <code>(555) 010-9999</code>, some are <code>07700 900123</code>, some are fine. Twilio does not guess: a number that is not strictly E.164 comes back <code>21211</code> at send time, one send at a time, forever, and each of those failures is a customer who was supposed to hear from you.",
"short_answer": """<p><code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}</code> returns <code>valid</code> as a boolean and <code>validation_errors[]</code> naming why: <code>TOO_SHORT</code>, <code>TOO_LONG</code>, <code>INVALID_BUT_POSSIBLE</code>, <code>INVALID_COUNTRY_CODE</code>, <code>INVALID_LENGTH</code>, <code>NOT_A_NUMBER</code>. It also returns the normalised <code>phone_number</code>, <code>country_code</code> and <code>calling_country_code</code>.</p>
<p>Two other outcomes are not <code>valid == false</code>. A number Lookup has no record of returns HTTP 404. A number that is well formed but sits in a range with no carrier behind it produces <code>60600</code>, unprovisioned or out of coverage. And a number that <em>is</em> valid can still be stored in a form your code will send verbatim, which is why the normalised <code>phone_number</code> is worth comparing against what you have.</p>""",
"problem": """<p>Bad numbers do not fail in a batch you can look at. They fail one at a time, months apart, inside whatever job happened to be sending, and each failure is a single <code>21211</code> against a single row. Nothing aggregates them, because a request that is rejected at validation frequently never creates a Message record at all &mdash; there is no row in <code>Messages.json</code> with a status of <code>failed</code>, just an API call that returned 400 and an exception your worker swallowed or retried.</p>
<p>So the shape of the problem is invisible. You cannot answer "how many of our contacts are unsendable" from the Twilio console, because Twilio has never been asked about the ones you have not tried yet. The only way to know is to ask about all of them at once, before the sending code does it for you one row at a time.</p>""",
"why": """<p><strong>Twilio requires strict E.164 and does no fuzzy parsing.</strong> There is no country hint, no default region, no stripping of punctuation on your behalf. <code>+1</code> and fifteen digits maximum, or <code>21211</code>. That strictness is correct &mdash; guessing a country for an ambiguous string is how a message goes to the wrong continent &mdash; but it means every legacy format in your database is a failure waiting for its turn.</p>
<p><strong>Valid and reachable are different questions.</strong> <code>valid</code> is a statement about the shape of the number against the numbering plan of its country. <code>60600</code> is a statement about whether any carrier has that number. A well-formed number in an unallocated range passes the first test and fails the second, and only the second one costs you a delivery.</p>
<p><strong>A number can be valid and still stored wrong.</strong> <code>+1 555 010 9999</code> with spaces, or a leading <code>00</code> instead of <code>+</code>, may well resolve. What you send is what you have in the row, so the normalised <code>phone_number</code> Lookup returns is the value that belongs in the database, not the one you happen to have.</p>
<p><strong>The obvious failures do not need an API call.</strong> A string with letters in it, or no <code>+</code>, or twenty digits, is unsendable before Twilio is involved. Checking the shape locally first means the paid Lookup is spent on the numbers where the answer is genuinely unknown.</p>""",
"steps": [
 {"h": "Decide what the input set is, and make it the whole set",
  "body": """<p>The useful run is over your stored contacts, not over what you have already sent. Feed the script a file of one number per line. Where that is not to hand, the fallback is the distinct <code>to</code> values from <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;={date}</code>, which at least covers the numbers in active use.</p>"""},
 {"h": "Screen the shape locally before spending a Lookup",
  "body": """<p>No leading <code>+</code>, characters that are not digits, fewer than eight digits or more than fifteen: all decided without a request. These are the rows that were exported from a system that never stored E.164, and they are usually the bulk of the finding.</p>"""},
 {"h": "Look up the rest and read validation_errors, not just valid",
  "body": """<p><code>valid == false</code> tells you it will fail; <code>validation_errors[]</code> tells you what to do about it. <code>TOO_SHORT</code> on a set of numbers sharing a country code is a truncation bug in an import. <code>INVALID_COUNTRY_CODE</code> across a batch is usually a national number with a <code>+</code> bolted on the front.</p>"""},
 {"h": "Separate malformed from unallocated",
  "body": """<p>HTTP 404 means Lookup has no record of the number. <code>60600</code> means it is a plausible number that is unprovisioned or out of coverage. Neither is a formatting mistake, so neither is fixed by re-parsing the string &mdash; those rows are dead and should be quarantined rather than corrected.</p>"""},
 {"h": "Write back the normalised form and quarantine the rest",
  "body": """<p>For every row where Lookup returned <code>valid</code> with a <code>phone_number</code> different from what you hold, store Twilio's version. For the invalid ones, mark the row rather than deleting it: a human needs to see the original string to know whether it is recoverable. Then validate at the input layer, so the set stops growing.</p>"""},
],
"verify": """<p>Re-run the script over the same input. Every number should report <code>ok</code>, and the invalid count should be zero.</p>
<pre><code class="language-bash">python3 twilio_lookup_validity_audit.py --file contacts.txt
# 1284 number(s), 0 unsendable</code></pre>""",
"code_intro": "One Lookup GET per number that survives the local shape check, plus one paginated GET over recent messages when no file is given. The classifier is pure and takes the HTTP status alongside the body, because three of the six outcomes here are not distinguishable from the JSON alone: a 404, a <code>60600</code> and a <code>valid</code> false are three different rows in the report and three different repairs.",
"py_file": "twilio_lookup_validity_audit.py",
"py": '''"""Report stored phone numbers that Twilio cannot send to.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Nothing is written back to your database and
nothing is changed on the account; the corrections are printed for you to apply.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_lookup_validity_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
LOOKUPS = "https://lookups.twilio.com/v2/PhoneNumbers"

VALIDATION = {
    "TOO_SHORT": "too few digits for the country code it starts with",
    "TOO_LONG": "too many digits for the country code it starts with",
    "INVALID_BUT_POSSIBLE": "the right length, but not a range that country has allocated",
    "INVALID_COUNTRY_CODE": "the leading digits are not a country calling code",
    "INVALID_LENGTH": "the wrong length for any range in that country",
    "NOT_A_NUMBER": "not parseable as a phone number at all",
}


def shape(raw):
    """Judge a stored string against E.164 without spending a Lookup.

    Pure. Returns a reason when the number cannot possibly be sent to, or None
    when the answer needs Twilio. These are the rows exported from a system that
    never stored E.164, and they are usually most of the finding.
    """
    s = str(raw or "").strip()
    if not s:
        return "empty"
    if not s.startswith("+"):
        return ("no leading +, so this is national format or a + stripped by an "
                "export; Twilio does no fuzzy parsing and will return 21211")
    digits = s[1:]
    if not digits.isdigit():
        return ("non-digit characters after the +: spaces, dashes or brackets "
                "survived the import")
    if len(digits) < 8:
        return "%d digits: shorter than any E.164 number" % len(digits)
    if len(digits) > 15:
        return "%d digits: E.164 allows at most 15" % len(digits)
    return None


def explain(errors):
    """Turn validation_errors[] into something a person can act on. Pure."""
    named = [VALIDATION.get(e, str(e)) for e in (errors or [])]
    return "; ".join(named) if named else "no reason given"


def classify(raw, status, body):
    """Classify one number from the Lookup response. Pure, so every outcome can
    be tested without a network.

    `status` is the HTTP status and `body` the parsed JSON, because three of the
    outcomes are not distinguishable from the JSON alone. Returns (state, detail).
    """
    local = shape(raw)
    if local:
        return ("not-e164", local)

    body = body or {}
    if status == 404:
        return ("not-found",
                "Lookup has no record of this number: it is not a formatting "
                "mistake, so re-parsing the string will not recover it")
    if status >= 400:
        code = body.get("code")
        if code == 60600:
            return ("uncovered",
                    "60600 unprovisioned or out of coverage: a plausible number "
                    "that no carrier has behind it")
        return ("lookup-error",
                "HTTP %s from Lookup, code %s: retry before treating the row as "
                "bad" % (status, code))

    if body.get("valid") is False:
        return ("invalid",
                "valid is false: %s" % explain(body.get("validation_errors")))

    normalised = str(body.get("phone_number") or "").strip()
    if normalised and normalised != str(raw).strip():
        return ("renormalise",
                "valid, but stored as %s where Twilio normalises it to %s; you "
                "send what is in the row" % (str(raw).strip(), normalised))

    return ("ok", "valid and stored in the form Twilio returns")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def lookup(session, e164):
    """One Lookup. Returns (status, body); 4xx bodies carry the error code."""
    r = session.get("%s/%s" % (LOOKUPS, e164), timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: the API key needs read access to Lookup"
                         % r.status_code)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


def recent_destinations(session, account, since, limit):
    """Distinct `to` values from recent messages, for when no file is given."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 100, "DateSent>": since}
    seen, out = set(), []
    while url and len(out) < limit:
        page = get(session, url, **params)
        for m in page.get("messages", []):
            to = str(m.get("to") or "").strip()
            if to and to not in seen:
                seen.add(to)
                out.append(to)
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", help="one phone number per line")
    ap.add_argument("--days", type=int, default=30,
                    help="window for the message fallback when no file is given")
    ap.add_argument("--max-numbers", type=int, default=500)
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

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            numbers = [ln.strip() for ln in fh if ln.strip()][:args.max_numbers]
    else:
        since = (dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=args.days)).strftime("%Y-%m-%d")
        log.info("no --file given: falling back to distinct destinations from the "
                 "last %d days of messages", args.days)
        numbers = recent_destinations(session, account, since, args.max_numbers)

    if not numbers:
        log.info("no numbers to check")
        return 0

    bad = 0
    for raw in numbers:
        if shape(raw):
            state, detail = classify(raw, 0, None)
        else:
            status, body = lookup(session, raw)
            state, detail = classify(raw, status, body)
        line = "%-13s %s  %s" % (state, raw, detail)
        if state == "ok":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "renormalise":
            log.warning("  repair: store Twilio's normalised phone_number on this row")
        elif state in ("not-found", "uncovered"):
            log.warning("  repair: quarantine this row; it is unreachable, not misformatted")
        elif state != "lookup-error":
            log.warning("  repair: correct the stored string to E.164, then "
                        "validate with Lookup at the input layer")

    log.info("%d number(s), %d unsendable", len(numbers), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-lookup-validity-audit.mjs",
"js": '''/**
 * Report stored phone numbers that Twilio cannot send to.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. Nothing is written back to your
 * database and nothing is changed on the account.
 */
import { readFileSync } from 'node:fs';

const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const LOOKUPS = 'https://lookups.twilio.com/v2/PhoneNumbers';

const VALIDATION = {
  TOO_SHORT: 'too few digits for the country code it starts with',
  TOO_LONG: 'too many digits for the country code it starts with',
  INVALID_BUT_POSSIBLE: 'the right length, but not a range that country has allocated',
  INVALID_COUNTRY_CODE: 'the leading digits are not a country calling code',
  INVALID_LENGTH: 'the wrong length for any range in that country',
  NOT_A_NUMBER: 'not parseable as a phone number at all',
};

/**
 * Judge a stored string against E.164 without spending a Lookup. Pure. Returns
 * a reason, or null when the answer needs Twilio.
 */
export function shape(raw) {
  const s = String(raw ?? '').trim();
  if (!s) return 'empty';
  if (!s.startsWith('+')) {
    return 'no leading +, so this is national format or a + stripped by an ' +
           'export; Twilio does no fuzzy parsing and will return 21211';
  }
  const digits = s.slice(1);
  if (!/^[0-9]+$/.test(digits)) {
    return 'non-digit characters after the +: spaces, dashes or brackets survived the import';
  }
  if (digits.length < 8) return `${digits.length} digits: shorter than any E.164 number`;
  if (digits.length > 15) return `${digits.length} digits: E.164 allows at most 15`;
  return null;
}

/** Turn validation_errors[] into something a person can act on. Pure. */
export function explain(errors) {
  const named = (errors ?? []).map((e) => VALIDATION[e] ?? String(e));
  return named.length ? named.join('; ') : 'no reason given';
}

/**
 * Classify one number from the Lookup response. Pure, so every outcome can be
 * tested without a network. Returns [state, detail].
 */
export function classify(raw, status, body) {
  const local = shape(raw);
  if (local) return ['not-e164', local];

  const b = body ?? {};
  if (status === 404) {
    return ['not-found',
      'Lookup has no record of this number: it is not a formatting mistake, ' +
      'so re-parsing the string will not recover it'];
  }
  if (status >= 400) {
    if (b.code === 60600) {
      return ['uncovered',
        '60600 unprovisioned or out of coverage: a plausible number that no ' +
        'carrier has behind it'];
    }
    return ['lookup-error',
      `HTTP ${status} from Lookup, code ${b.code}: retry before treating the row as bad`];
  }

  if (b.valid === false) {
    return ['invalid', `valid is false: ${explain(b.validation_errors)}`];
  }

  const normalised = String(b.phone_number ?? '').trim();
  if (normalised && normalised !== String(raw).trim()) {
    return ['renormalise',
      `valid, but stored as ${String(raw).trim()} where Twilio normalises it ` +
      `to ${normalised}; you send what is in the row`];
  }

  return ['ok', 'valid and stored in the form Twilio returns'];
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

export async function lookup(auth, e164) {
  const res = await fetch(`${LOOKUPS}/${encodeURIComponent(e164)}`,
                          { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: the API key needs read access to Lookup`);
  }
  try {
    return [res.status, await res.json()];
  } catch {
    return [res.status, {}];
  }
}

export async function recentDestinations(auth, account, since, limit) {
  let url = `${BASE}/Accounts/${account}/Messages.json`;
  let params = { PageSize: 100, 'DateSent>': since };
  const seen = new Set();
  while (url && seen.size < limit) {
    const page = await get(auth, url, params);
    for (const m of page.messages ?? []) {
      const to = String(m.to ?? '').trim();
      if (to) seen.add(to);
    }
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return [...seen].slice(0, limit);
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
  const fileArg = process.argv.indexOf('--file');
  const days = Number(process.env.DAYS ?? 30);
  const max = 500;

  let numbers;
  if (fileArg !== -1 && process.argv[fileArg + 1]) {
    numbers = readFileSync(process.argv[fileArg + 1], 'utf8')
      .split('\\n').map((l) => l.trim()).filter(Boolean).slice(0, max);
  } else {
    const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
    console.log(`no --file given: falling back to distinct destinations from the ` +
                `last ${days} days of messages`);
    numbers = await recentDestinations(auth, account, since, max);
  }

  if (numbers.length === 0) {
    console.log('no numbers to check');
    return;
  }

  let bad = 0;
  for (const raw of numbers) {
    let state; let detail;
    if (shape(raw)) {
      [state, detail] = classify(raw, 0, null);
    } else {
      const [status, body] = await lookup(auth, raw);
      [state, detail] = classify(raw, status, body);
    }
    const line = `${state.padEnd(13)} ${raw}  ${detail}`;
    if (state === 'ok') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'renormalise') {
      console.warn("  repair: store Twilio's normalised phone_number on this row");
    } else if (state === 'not-found' || state === 'uncovered') {
      console.warn('  repair: quarantine this row; it is unreachable, not misformatted');
    } else if (state !== 'lookup-error') {
      console.warn('  repair: correct the stored string to E.164, then validate ' +
                   'with Lookup at the input layer');
    }
  }

  console.log(`${numbers.length} number(s), ${bad} unsendable`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that decides whether the report is useful is the valid number stored in the wrong form. It is not an error, Lookup returns 200 and <code>valid</code> true, and the send will still fail if your code passes the row through verbatim. The other one worth pinning is the 404: a number Lookup has never heard of is a different repair from a number that was typed wrong, and folding them together sends someone off to fix a string that was never the problem.",
"test_py_file": "test_twilio_lookup_validity_audit.py",
"test_py": '''from twilio_lookup_validity_audit import classify, explain, shape

VALID = {"valid": True, "phone_number": "+15550109999", "country_code": "US"}


def test_national_format_is_caught_without_a_lookup():
    state, detail = classify("(555) 010-9999", 0, None)
    assert state == "not-e164"
    assert "21211" in detail


def test_punctuation_after_the_plus_is_still_not_e164():
    assert shape("+1 555 010 9999") is not None
    assert classify("+1 555 010 9999", 0, None)[0] == "not-e164"


def test_valid_false_reports_the_validation_error_in_words():
    state, detail = classify("+15550109", 200,
                             {"valid": False, "validation_errors": ["TOO_SHORT"]})
    assert state == "invalid"
    assert "too few digits" in detail


def test_a_valid_number_stored_in_another_form_is_its_own_finding():
    # 200, valid true, and the send still fails: you send what is in the row.
    assert classify("+1-555-010-9999", 200, VALID)[0] == "not-e164"
    assert classify("+15550109999 ", 200, VALID)[0] == "ok"


def test_normalised_difference_is_reported_rather_than_passed():
    state, detail = classify("+15550109998", 200, VALID)
    assert state == "renormalise"
    assert "+15550109999" in detail


def test_404_and_60600_are_different_rows():
    assert classify("+15550109999", 404, {"code": 20404})[0] == "not-found"
    assert classify("+15550109999", 400, {"code": 60600})[0] == "uncovered"
    assert classify("+15550109999", 429, {"code": 20429})[0] == "lookup-error"


def test_unknown_validation_codes_survive_the_translation():
    assert explain(["SOMETHING_NEW"]) == "SOMETHING_NEW"
    assert explain([]) == "no reason given"
''',
"test_js_file": "twilio-lookup-validity-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, explain, shape } from './twilio-lookup-validity-audit.mjs';

const VALID = { valid: true, phone_number: '+15550109999', country_code: 'US' };

test('national format is caught without a lookup', () => {
  const [state, detail] = classify('(555) 010-9999', 0, null);
  assert.equal(state, 'not-e164');
  assert.match(detail, /21211/);
});

test('punctuation after the plus is still not e164', () => {
  assert.notEqual(shape('+1 555 010 9999'), null);
  assert.equal(classify('+1 555 010 9999', 0, null)[0], 'not-e164');
});

test('valid false reports the validation error in words', () => {
  const [state, detail] = classify('+15550109', 200,
    { valid: false, validation_errors: ['TOO_SHORT'] });
  assert.equal(state, 'invalid');
  assert.match(detail, /too few digits/);
});

test('a valid number stored in another form is its own finding', () => {
  assert.equal(classify('+1-555-010-9999', 200, VALID)[0], 'not-e164');
  assert.equal(classify('+15550109999 ', 200, VALID)[0], 'ok');
});

test('normalised difference is reported rather than passed', () => {
  const [state, detail] = classify('+15550109998', 200, VALID);
  assert.equal(state, 'renormalise');
  assert.match(detail, /\\+15550109999/);
});

test('404 and 60600 are different rows', () => {
  assert.equal(classify('+15550109999', 404, { code: 20404 })[0], 'not-found');
  assert.equal(classify('+15550109999', 400, { code: 60600 })[0], 'uncovered');
  assert.equal(classify('+15550109999', 429, { code: 20429 })[0], 'lookup-error');
});

test('unknown validation codes survive the translation', () => {
  assert.equal(explain(['SOMETHING_NEW']), 'SOMETHING_NEW');
  assert.equal(explain([]), 'no reason given');
});
''',
"faq": [
 ("Why does Twilio not just parse the number for me?",
  "Because it would have to guess a country, and guessing wrong sends the message to a real person on another continent. E.164 is unambiguous by construction: the country calling code is part of the number. The strictness is the feature; the cost is that every legacy format in your database is a failure waiting for its turn."),
 ("What is the difference between valid false and 60600?",
  "valid is a statement about shape: does this string fit the numbering plan of the country its leading digits name. 60600 is a statement about reality: is there a carrier behind it. A well-formed number in a range nobody was ever assigned passes the first and fails the second, and only the second costs you a delivery."),
 ("Why check the shape locally when Lookup would tell me?",
  "Because Lookup is a paid request and a string with letters in it does not need one. Screening locally spends the requests on the numbers where the answer is genuinely unknown, which matters when the input is a contact table rather than a handful of rows."),
 ("A number came back valid and the send still failed. Why?",
  "Most often because what you sent is not what Lookup was asked about. Lookup normalises the number in its response; if your row holds a different string with the same meaning, that is the string your code sends. Comparing the returned phone_number against the stored value is the check that catches it."),
 ("Should the script write the corrected numbers back?",
  "No, and not only because this section never writes. A bulk update over a contact table from a script holding a messaging credential is the wrong shape of change: the invalid rows need a person to look at the original string and decide whether it is recoverable at all."),
],
"related": [
 ("/twilio/verify-lookup-disabled/", "Verify running with lookup_enabled false"),
 ("/twilio/unknown-destination-handset-30005/", "A destination that no longer exists on the carrier"),
 ("/twilio/deactivated-number-recycling/", "Recycled numbers send OTPs to the wrong person"),
],
"citations": [CITE_LOOKUP, CITE_21211, CITE_60600, CITE_KEYS],
},

{
"slug": "webhook-http-retrieval-failure-11200",
"title": "11200 on the TwiML fetch: the call fails, not just a receipt",
"description": "Anything outside 2xx is a retrieval failure. On an inbound handler that is a dropped call or a lost message, not a delivery receipt that went missing.",
"h1": "11200 on the TwiML fetch: the call fails, not just a receipt",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 11200 voice_url", "twiml retrieval failure",
             "twilio webhook 15 second timeout", "application error has occurred twilio",
             "twilio inbound webhook 500"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Debugger shows a wall of <code>11200</code> and everyone agrees it is the same known issue with the delivery receipts. It is not. Some of these are on <code>voice_url</code>, and an <code>11200</code> there is not a receipt that went missing &mdash; it is a caller who heard <em>an application error has occurred</em> and then a dial tone.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> for <code>error_code == 11200</code> and group by <code>request_url</code>. Then decide, per URL, which handler it is: <code>voice_url</code> and <code>sms_url</code> from <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code>, <code>inbound_request_url</code> from <code>GET https://messaging.twilio.com/v1/Services</code>.</p>
<p>An <code>11200</code> on one of those is a TwiML retrieval failure: the request that was supposed to tell Twilio what to do never produced an answer, so there is nothing to execute. An <code>11200</code> on a <code>status_callback</code> is <a href="/twilio/status-callback-webhook-failing-11200/">the other failure with the same code</a>, and it costs you a receipt rather than a call. The consequence turns on which URL it was, so the URL is the first thing to establish.</p>""",
"problem": """<p><code>11200</code> is one code covering every way an HTTP response can be unusable. A <code>404</code> from a route that moved, a <code>401</code> from auth middleware that started challenging Twilio, a <code>500</code> from a crash, a handler that took sixteen seconds, a URL that resolves to a private address: all of them arrive as <code>11200 HTTP retrieval failure</code> and all of them look identical in a list view. The alert does not say what happened, only that nothing usable came back.</p>
<p>Because the code is shared, the incident gets triaged by whoever saw it first, and the status-callback version is the common one. So the voice and inbound alerts get folded into the same ticket and inherit its urgency, which is low, because a missing receipt can be backfilled from <code>Messages.json</code> tomorrow. A dropped call cannot be backfilled from anything. The caller is gone, and Twilio has no retry for inbound: the fallback URL is the only second chance, and if it is unset there is no second chance at all.</p>""",
"why": """<p><strong>One code, two consequences, and the alert does not distinguish them.</strong> The Alerts list gives you <code>error_code</code>, <code>request_url</code> and a timestamp. Whether that URL is a TwiML handler or a receipt endpoint is knowledge that lives on the phone number and the Messaging Service, in a different API, so an alert-only view cannot tell you which incident you are in.</p>
<p><strong>Twilio's window is fifteen seconds, and it is not your window.</strong> A handler that queries a database, calls a partner API and then renders TwiML can sit comfortably inside your own SLO and still exceed Twilio's. When it does, the response is discarded and logged as a retrieval failure &mdash; your access log shows a 200, which is exactly the evidence that makes people conclude Twilio is wrong.</p>
<p><strong>Auth middleware is a common cause and an invisible one.</strong> Twilio's request carries no session and no bearer token. A blanket authentication rule added to a route prefix will start returning <code>401</code> or <code>403</code> to Twilio while every human user continues to work, and the deploy that did it will look unrelated.</p>
<p><strong>Without a fallback the failure is total.</strong> With <code>voice_fallback_url</code> set, an <code>11200</code> on the primary is a degraded call: the caller gets whatever the fallback says. With it unset, Twilio plays its own error message and hangs up. Same alert, same code, and the difference between the two is a field on the number that the alert does not mention.</p>""",
"steps": [
 {"h": "Sweep 11200 over a bounded window and group by URL",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate={ISO8601}</code>, keeping <code>error_code == 11200</code>. Alerts are retained for thirty days and a request returns at most ten thousand, so the window is a real constraint rather than a nicety. Group on host plus path with the query string dropped, or one handler will appear as forty distinct endpoints.</p>"""},
 {"h": "Attribute each URL to a handler before you judge it",
  "body": """<p>Build the index from <code>IncomingPhoneNumbers.json</code> and <code>messaging.twilio.com/v1/Services</code>: <code>voice_url</code>, <code>sms_url</code>, <code>inbound_request_url</code> are the TwiML paths; <code>voice_fallback_url</code>, <code>sms_fallback_url</code> and <code>fallback_url</code> are the safety nets; <code>status_callback</code> is the receipt path. A URL that matches nothing is usually a TwiML App or a Studio flow, and is worth reporting as unattributed rather than dropping.</p>"""},
 {"h": "Read whether the failing handler has a fallback",
  "body": """<p>This is what sets severity, and it comes off the same number record you already fetched. A primary handler failing with no fallback configured is a dropped call. A primary failing with a fallback is a degraded one. A <em>fallback</em> failing is its own state and the worst of the three, because there is nothing behind it.</p>"""},
 {"h": "Fetch one alert by SID to see what your server actually returned",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{AlertSid}</code> populates <code>response_body</code>, <code>response_headers</code> and <code>request_headers</code>. None of them appear in the list response, so this second fetch is the only way to tell a <code>404</code> from a timeout from an HTML login page served where TwiML was expected. One sample per endpoint is enough.</p>"""},
 {"h": "Answer inside the window, then set a fallback, then re-run",
  "body": """<p>Acknowledge immediately and do the slow work asynchronously; return TwiML in well under fifteen seconds. Then <code>POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json</code> with <code>VoiceFallbackUrl</code>, so the next occurrence is a degraded call rather than a dropped one. Re-run over a fresh window afterwards; the old alerts do not disappear.</p>"""},
],
"verify": """<p>Re-run the script over a window that starts after the fix. No endpoint should report <code>no-safety-net</code> or <code>fallback-failing</code>.</p>
<pre><code class="language-bash">python3 twilio_twiml_retrieval_audit.py --days 1
# 4 endpoint(s) with 11200, 0 on a TwiML handler with no fallback</code></pre>""",
"code_intro": "One paginated GET over the alerts, one over the numbers and one over the Messaging Services, plus one optional fetch per endpoint for the sample &mdash; all reads, with an API Key that has read access and nothing more. The attribution and the verdict are both pure functions, because the whole argument of this note is that the same alert means two different things depending on a field that is not in it.",
"py_file": "twilio_twiml_retrieval_audit.py",
"py": '''"""Report 11200 retrieval failures on the TwiML handlers, not the receipts.

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
log = logging.getLogger("twilio_twiml_retrieval_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"
MONITOR = "https://monitor.twilio.com/v1"

PRIMARY = {"voice", "sms", "inbound"}


def code_of(alert):
    """error_code arrives as a string on some alerts and an int on others."""
    try:
        return int(alert.get("error_code"))
    except (TypeError, ValueError):
        return None


def endpoint(url):
    """Reduce a URL to lowercase host plus path.

    Pure. Twilio appends nothing, but applications routinely carry a per-call
    query string, and grouping on the raw URL turns one broken handler into
    forty endpoints that each look survivable.
    """
    u = str(url or "").strip()
    for scheme in ("https://", "http://"):
        if u.lower().startswith(scheme):
            u = u[len(scheme):]
            break
    u = u.split("?", 1)[0].split("#", 1)[0]
    if "@" in u.split("/", 1)[0]:
        u = u.split("@", 1)[1]
    return u.rstrip("/").lower()


def handler_index(numbers, services):
    """Map every configured URL to the roles it plays and what it protects.

    Pure. The alert says which URL failed; only this index says whether that URL
    is a TwiML handler, a fallback or a delivery receipt, and whether the thing
    it serves has a fallback behind it.
    """
    idx = {}

    def add(url, role, exposed=None):
        e = endpoint(url)
        if not e:
            return
        entry = idx.setdefault(e, {"roles": set(), "exposed": []})
        entry["roles"].add(role)
        if exposed:
            entry["exposed"].append(exposed)

    for n in numbers:
        label = n.get("phone_number") or n.get("sid") or "?"
        voice_fb = str(n.get("voice_fallback_url") or "").strip()
        sms_fb = str(n.get("sms_fallback_url") or "").strip()
        add(n.get("voice_url"), "voice", None if voice_fb else label + " voice")
        add(n.get("sms_url"), "sms", None if sms_fb else label + " sms")
        add(voice_fb, "fallback")
        add(sms_fb, "fallback")
        add(n.get("status_callback"), "status-callback")
        add(n.get("sms_status_callback"), "status-callback")

    for s in services:
        label = s.get("friendly_name") or s.get("sid") or "?"
        fb = str(s.get("fallback_url") or "").strip()
        add(s.get("inbound_request_url"), "inbound", None if fb else label + " inbound")
        add(fb, "fallback")
        add(s.get("status_callback"), "status-callback")

    return idx


def verdict(row, min_alerts=3):
    """Classify one failing endpoint. Pure, so the severity rule can be tested
    without a network.

    `row` carries the normalised endpoint, the alert count, the roles it plays
    and the handlers it serves that have no fallback. Returns (state, detail).
    """
    roles = set(row.get("roles") or ())
    exposed = list(row.get("exposed") or ())
    n = int(row.get("count") or 0)

    if roles and roles <= {"status-callback"}:
        return ("status-callback",
                "%d failure(s) on a delivery receipt URL. That loses the receipt, "
                "not the call, and it is a different note with a different "
                "repair." % n)

    if not roles:
        return ("unattributed",
                "%d failure(s) on a URL that no number and no Messaging Service "
                "currently points at: a TwiML App, a Studio flow, or a handler "
                "that has since been reconfigured." % n)

    primary = roles & PRIMARY
    if not primary:
        return ("fallback-failing",
                "%d failure(s) on a fallback URL. The fallback is the last thing "
                "between a broken handler and a dropped call, and it is the "
                "thing returning non-2xx." % n)

    where = "/".join(sorted(primary))
    if exposed:
        return ("no-safety-net",
                "%d failure(s) on the %s handler for %s, which has no fallback "
                "URL. Twilio has nothing to execute, so it plays its own error "
                "message and hangs up, or drops the inbound message."
                % (n, where, ", ".join(exposed[:3])))

    if n < min_alerts:
        return ("intermittent",
                "%d failure(s) on the %s handler, and a fallback answered. Under "
                "the %d threshold: noise, until the rate changes."
                % (n, where, min_alerts))

    return ("degraded",
            "%d failure(s) on the %s handler. A fallback answered, so callers "
            "were served something, but not your application." % (n, where))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=10000, **params):
    """Page a v1 list. meta.next_page_url is absolute."""
    out = []
    params.setdefault("PageSize", 100)
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url, params = (page.get("meta") or {}).get("next_page_url"), {}
    return out[:limit]


def list_numbers(session, account, limit=2000):
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def fetch_alert(session, sid):
    """response_body and response_headers exist only on the single-alert fetch."""
    return get(session, "%s/Alerts/%s" % (MONITOR, sid))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=3, help="alert window, max 30")
    ap.add_argument("--min-alerts", type=int, default=3,
                    help="below this a fallback-covered endpoint is noise")
    ap.add_argument("--sample", action="store_true",
                    help="one extra GET per endpoint to see the response Twilio got")
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

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=min(args.days, 30))).strftime("%Y-%m-%dT%H:%M:%SZ")
    alerts = [a for a in list_v1(session, MONITOR + "/Alerts", "alerts",
                                 LogLevel="error", StartDate=since)
              if code_of(a) == 11200]
    if not alerts:
        log.info("no 11200 alerts in the last %d day(s)", args.days)
        return 0

    idx = handler_index(list_numbers(session, account),
                        list_v1(session, MSG + "/Services", "services", 1000))

    rows = {}
    for a in alerts:
        e = endpoint(a.get("request_url"))
        row = rows.setdefault(e, {"endpoint": e, "count": 0, "sid": a.get("sid"),
                                  "roles": set(), "exposed": []})
        row["count"] += 1
        known = idx.get(e)
        if known:
            row["roles"] = known["roles"]
            row["exposed"] = known["exposed"]

    bad = 0
    for row in sorted(rows.values(), key=lambda r: -r["count"]):
        state, detail = verdict(row, args.min_alerts)
        line = "%-16s %s  %s" % (state, row["endpoint"], detail)
        if state in ("intermittent", "status-callback"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if args.sample and row["sid"]:
            full = fetch_alert(session, row["sid"])
            log.warning("  %s returned: %s", full.get("request_method") or "GET",
                        str(full.get("response_body") or "")[:200] or "no body")
        log.warning("  repair: return TwiML with a 2xx inside 15 seconds, then "
                    "POST %s/Accounts/%s/IncomingPhoneNumbers/{PNSid}.json "
                    "VoiceFallbackUrl=https://your-app.example.com/fallback",
                    BASE, account)

    log.info("%d endpoint(s) with 11200, %d on a TwiML handler with no fallback",
             len(rows), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-twiml-retrieval-audit.mjs",
"js": '''/**
 * Report 11200 retrieval failures on the TwiML handlers, not the receipts.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';
const MONITOR = 'https://monitor.twilio.com/v1';

const PRIMARY = ['voice', 'sms', 'inbound'];

/** error_code arrives as a string on some alerts and a number on others. */
export function codeOf(alert) {
  const n = Number(alert?.error_code);
  return Number.isFinite(n) ? n : null;
}

/**
 * Reduce a URL to lowercase host plus path. Pure: applications carry a per-call
 * query string, and grouping on the raw URL turns one broken handler into forty
 * endpoints that each look survivable.
 */
export function endpoint(url) {
  let u = String(url ?? '').trim();
  for (const scheme of ['https://', 'http://']) {
    if (u.toLowerCase().startsWith(scheme)) { u = u.slice(scheme.length); break; }
  }
  u = u.split('?')[0].split('#')[0];
  if (u.split('/')[0].includes('@')) u = u.slice(u.indexOf('@') + 1);
  return u.replace(/\\/+$/, '').toLowerCase();
}

/**
 * Map every configured URL to the roles it plays and what it protects. Pure:
 * the alert says which URL failed, and only this index says whether that URL is
 * a TwiML handler, a fallback or a delivery receipt.
 */
export function handlerIndex(numbers, services) {
  const idx = new Map();

  const add = (url, role, exposed = null) => {
    const e = endpoint(url);
    if (!e) return;
    const entry = idx.get(e) ?? { roles: new Set(), exposed: [] };
    entry.roles.add(role);
    if (exposed) entry.exposed.push(exposed);
    idx.set(e, entry);
  };

  for (const n of numbers) {
    const label = n.phone_number ?? n.sid ?? '?';
    const voiceFb = String(n.voice_fallback_url ?? '').trim();
    const smsFb = String(n.sms_fallback_url ?? '').trim();
    add(n.voice_url, 'voice', voiceFb ? null : `${label} voice`);
    add(n.sms_url, 'sms', smsFb ? null : `${label} sms`);
    add(voiceFb, 'fallback');
    add(smsFb, 'fallback');
    add(n.status_callback, 'status-callback');
    add(n.sms_status_callback, 'status-callback');
  }

  for (const s of services) {
    const label = s.friendly_name ?? s.sid ?? '?';
    const fb = String(s.fallback_url ?? '').trim();
    add(s.inbound_request_url, 'inbound', fb ? null : `${label} inbound`);
    add(fb, 'fallback');
    add(s.status_callback, 'status-callback');
  }

  return idx;
}

/**
 * Classify one failing endpoint. Pure, so the severity rule can be tested
 * without a network. Returns [state, detail].
 */
export function verdict(row, minAlerts = 3) {
  const roles = new Set(row.roles ?? []);
  const exposed = [...(row.exposed ?? [])];
  const n = Number(row.count ?? 0);

  if (roles.size && [...roles].every((r) => r === 'status-callback')) {
    return ['status-callback',
      `${n} failure(s) on a delivery receipt URL. That loses the receipt, not ` +
      'the call, and it is a different note with a different repair.'];
  }

  if (roles.size === 0) {
    return ['unattributed',
      `${n} failure(s) on a URL that no number and no Messaging Service ` +
      'currently points at: a TwiML App, a Studio flow, or a handler that has ' +
      'since been reconfigured.'];
  }

  const primary = PRIMARY.filter((r) => roles.has(r));
  if (primary.length === 0) {
    return ['fallback-failing',
      `${n} failure(s) on a fallback URL. The fallback is the last thing ` +
      'between a broken handler and a dropped call, and it is the thing ' +
      'returning non-2xx.'];
  }

  const where = [...primary].sort().join('/');
  if (exposed.length) {
    return ['no-safety-net',
      `${n} failure(s) on the ${where} handler for ${exposed.slice(0, 3).join(', ')}, ` +
      'which has no fallback URL. Twilio has nothing to execute, so it plays ' +
      'its own error message and hangs up, or drops the inbound message.'];
  }

  if (n < minAlerts) {
    return ['intermittent',
      `${n} failure(s) on the ${where} handler, and a fallback answered. Under ` +
      `the ${minAlerts} threshold: noise, until the rate changes.`];
  }

  return ['degraded',
    `${n} failure(s) on the ${where} handler. A fallback answered, so callers ` +
    'were served something, but not your application.'];
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

export async function listV1(auth, url, key, limit = 10000, params = {}) {
  const out = [];
  let next = url;
  let query = { PageSize: 100, ...params };
  while (next && out.length < limit) {
    const page = await get(auth, next, query);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    query = {};
  }
  return out.slice(0, limit);
}

export async function listNumbers(auth, account, limit = 2000) {
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
  const days = Math.min(Number(process.env.DAYS ?? 3), 30);
  const minAlerts = Number(process.env.MIN_ALERTS ?? 3);
  const sample = process.argv.includes('--sample');

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 19) + 'Z';
  const alerts = (await listV1(auth, `${MONITOR}/Alerts`, 'alerts', 10000,
                               { LogLevel: 'error', StartDate: since }))
    .filter((a) => codeOf(a) === 11200);
  if (alerts.length === 0) {
    console.log(`no 11200 alerts in the last ${days} day(s)`);
    return;
  }

  const idx = handlerIndex(await listNumbers(auth, account),
                           await listV1(auth, `${MSG}/Services`, 'services', 1000));

  const rows = new Map();
  for (const a of alerts) {
    const e = endpoint(a.request_url);
    const row = rows.get(e) ??
      { endpoint: e, count: 0, sid: a.sid, roles: new Set(), exposed: [] };
    row.count += 1;
    const known = idx.get(e);
    if (known) { row.roles = known.roles; row.exposed = known.exposed; }
    rows.set(e, row);
  }

  let bad = 0;
  for (const row of [...rows.values()].sort((a, b) => b.count - a.count)) {
    const [state, detail] = verdict(row, minAlerts);
    const line = `${state.padEnd(16)} ${row.endpoint}  ${detail}`;
    if (state === 'intermittent' || state === 'status-callback') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (sample && row.sid) {
      const full = await get(auth, `${MONITOR}/Alerts/${row.sid}`);
      console.warn(`  ${full.request_method ?? 'GET'} returned: ` +
                   `${String(full.response_body ?? '').slice(0, 200) || 'no body'}`);
    }
    console.warn('  repair: return TwiML with a 2xx inside 15 seconds, then ' +
                 `POST ${BASE}/Accounts/${account}/IncomingPhoneNumbers/{PNSid}.json ` +
                 'VoiceFallbackUrl=https://your-app.example.com/fallback');
  }

  console.log(`${rows.size} endpoint(s) with 11200, ${bad} on a TwiML handler with no fallback`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. The first is an endpoint that is only ever a status callback: it has to come back as somebody else's incident, or this report reproduces exactly the triage mistake it exists to prevent. The second is a fallback URL that is itself failing &mdash; that endpoint plays no primary role, so a classifier keyed on <em>is this a TwiML handler</em> would file it as unattributed and lose the most urgent finding in the run.",
"test_py_file": "test_twilio_twiml_retrieval_audit.py",
"test_py": '''from twilio_twiml_retrieval_audit import endpoint, handler_index, verdict

APP = "https://app.example.com/voice"
FALLBACK = "https://app.example.com/fallback"
RECEIPT = "https://app.example.com/status"


def index_for(numbers, services=()):
    return handler_index(numbers, list(services))


def test_a_status_callback_url_is_handed_to_the_other_note():
    state, detail = verdict({"count": 40, "roles": {"status-callback"}})
    assert state == "status-callback"
    assert "not the call" in detail


def test_primary_handler_with_no_fallback_is_the_dropped_call():
    idx = index_for([{"phone_number": "+15550001111", "voice_url": APP}])
    row = dict(idx[endpoint(APP)], count=5)
    state, detail = verdict(row)
    assert state == "no-safety-net"
    assert "+15550001111 voice" in detail


def test_the_same_handler_with_a_fallback_is_only_degraded():
    idx = index_for([{"phone_number": "+15550001111", "voice_url": APP,
                      "voice_fallback_url": FALLBACK}])
    state, _ = verdict(dict(idx[endpoint(APP)], count=5))
    assert state == "degraded"


def test_a_failing_fallback_is_its_own_state_not_unattributed():
    idx = index_for([{"phone_number": "+15550001111", "voice_url": APP,
                      "voice_fallback_url": FALLBACK}])
    state, detail = verdict(dict(idx[endpoint(FALLBACK)], count=2))
    assert state == "fallback-failing"
    assert "last thing" in detail


def test_an_unknown_url_is_reported_rather_than_dropped():
    state, detail = verdict({"count": 9, "roles": set()})
    assert state == "unattributed"
    assert "Studio" in detail


def test_a_few_failures_behind_a_fallback_are_under_the_threshold():
    idx = index_for([{"phone_number": "+15550001111", "sms_url": APP,
                      "sms_fallback_url": FALLBACK}])
    state, _ = verdict(dict(idx[endpoint(APP)], count=2), min_alerts=3)
    assert state == "intermittent"


def test_query_strings_do_not_split_one_handler_into_many():
    assert endpoint("https://App.Example.com/voice?CallSid=CA1") == \\
        endpoint("http://app.example.com/voice/")


def test_a_service_inbound_url_counts_as_a_twiml_handler():
    idx = index_for([], [{"friendly_name": "prod", "inbound_request_url": APP,
                          "status_callback": RECEIPT}])
    state, _ = verdict(dict(idx[endpoint(APP)], count=7))
    assert state == "no-safety-net"
    assert verdict(dict(idx[endpoint(RECEIPT)], count=7))[0] == "status-callback"
''',
"test_js_file": "twilio-twiml-retrieval-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { endpoint, handlerIndex, verdict } from './twilio-twiml-retrieval-audit.mjs';

const APP = 'https://app.example.com/voice';
const FALLBACK = 'https://app.example.com/fallback';
const RECEIPT = 'https://app.example.com/status';

const row = (idx, url, count, extra = {}) => ({ ...idx.get(endpoint(url)), count, ...extra });

test('a status callback url is handed to the other note', () => {
  const [state, detail] = verdict({ count: 40, roles: new Set(['status-callback']) });
  assert.equal(state, 'status-callback');
  assert.match(detail, /not the call/);
});

test('primary handler with no fallback is the dropped call', () => {
  const idx = handlerIndex([{ phone_number: '+15550001111', voice_url: APP }], []);
  const [state, detail] = verdict(row(idx, APP, 5));
  assert.equal(state, 'no-safety-net');
  assert.match(detail, /\\+15550001111 voice/);
});

test('the same handler with a fallback is only degraded', () => {
  const idx = handlerIndex([{ phone_number: '+15550001111', voice_url: APP,
                              voice_fallback_url: FALLBACK }], []);
  assert.equal(verdict(row(idx, APP, 5))[0], 'degraded');
});

test('a failing fallback is its own state, not unattributed', () => {
  const idx = handlerIndex([{ phone_number: '+15550001111', voice_url: APP,
                              voice_fallback_url: FALLBACK }], []);
  assert.equal(verdict(row(idx, FALLBACK, 2))[0], 'fallback-failing');
});

test('an unknown url is reported rather than dropped', () => {
  const [state, detail] = verdict({ count: 9, roles: new Set() });
  assert.equal(state, 'unattributed');
  assert.match(detail, /Studio/);
});

test('a few failures behind a fallback are under the threshold', () => {
  const idx = handlerIndex([{ phone_number: '+15550001111', sms_url: APP,
                              sms_fallback_url: FALLBACK }], []);
  assert.equal(verdict(row(idx, APP, 2), 3)[0], 'intermittent');
});

test('query strings do not split one handler into many', () => {
  assert.equal(endpoint('https://App.Example.com/voice?CallSid=CA1'),
               endpoint('http://app.example.com/voice/'));
});

test('a service inbound url counts as a twiml handler', () => {
  const idx = handlerIndex([], [{ friendly_name: 'prod', inbound_request_url: APP,
                                  status_callback: RECEIPT }]);
  assert.equal(verdict(row(idx, APP, 7))[0], 'no-safety-net');
  assert.equal(verdict(row(idx, RECEIPT, 7))[0], 'status-callback');
});
''',
"faq": [
 ("How is this different from 11200 on a status callback?",
  "Same code, different endpoint, different loss. A status callback carries a delivery receipt, and when it fails you can rebuild the state from Messages.json afterwards. A TwiML handler carries the instructions for what to do with a live call or an inbound message; when it fails there is nothing to execute and nothing to reconstruct later."),
 ("My server logged a 200. Why does Twilio say retrieval failure?",
  "Almost always the fifteen-second window. Twilio gives you ten seconds to establish the connection and fifteen for the whole response; a handler that eventually returns 200 after sixteen seconds has already had its response discarded. Your log records the reply you sent, not whether anyone was still waiting for it."),
 ("Why do the alerts suddenly appear after an unrelated deploy?",
  "Auth middleware is the usual answer. Twilio's request carries no session cookie and no bearer token, so a blanket rule applied to a route prefix starts returning 401 or 403 to Twilio while every browser user is unaffected. The change looks unrelated because for humans it is."),
 ("Why fetch a second time for one alert?",
  "response_body, response_headers and request_headers are populated only on GET /v1/Alerts/{AlertSid}, never in the list response. Without that fetch you cannot tell a 404 from a timeout from an HTML login page, and those are three different repairs. One sample per endpoint is enough to decide."),
 ("Is a fallback URL a fix?",
  "No, it is a floor. It converts a dropped call into a degraded one, which is worth having, but the caller still is not talking to your application. Fix the handler; set the fallback so the next failure costs less than this one did."),
],
"related": [
 ("/twilio/status-callback-webhook-failing-11200/", "The same code on the delivery receipt path"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
 ("/twilio/webhook-connection-timeout-11205/", "Twilio cannot open a connection to your webhook"),
],
"citations": [CITE_11200, CITE_ALERTS, CITE_WEBHOOKS, CITE_PN],
},

{
"slug": "twiml-schema-validation-warning-12200",
"title": "12200: TwiML that parses, fails the schema, and is skipped",
"description": "The document is well formed, so 12100 never fires. The verb is miscased, the schema rejects it, and Twilio logs the whole thing at warning.",
"h1": "12200: TwiML that parses, fails the schema, and is skipped",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 12200", "schema validation warning twilio",
             "twiml case sensitive", "numDigits not working",
             "twilio alerts loglevel warning"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The <code>&lt;Gather&gt;</code> collects one digit instead of four and nobody can find an error, because there isn't one. <code>numdigits</code> was written in lower case, the schema rejected the attribute, and Twilio logged a <code>12200</code> at <em>warning</em>. Every dashboard, alert rule and sweep in the building filters on errors.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=warning&amp;StartDate=YYYY-MM-DD</code> for <code>error_code == 12200</code>. The <code>LogLevel=warning</code> filter is the whole trick: these alerts do not exist in an error-only query, which is why an account can carry them for months.</p>
<p>The document parsed, so this is not <a href="/twilio/twiml-document-parse-failure-12100/">12100</a>. It is valid XML that is not valid TwiML: <code>&lt;say&gt;</code> for <code>&lt;Say&gt;</code>, <code>numdigits</code> for <code>numDigits</code>, a verb the vocabulary does not contain, or a verb nested where the schema disallows it. Fetch a sample with <code>GET https://monitor.twilio.com/v1/Alerts/{AlertSid}</code> and read <code>response_body</code> &mdash; the bytes are the diagnosis.</p>""",
"problem": """<p>Everything about this failure argues that it is not one. The call connects. The webhook returns 200. The XML is well formed. Twilio parses it, walks it, discards the part it cannot validate, and carries on with the rest of the document. The call completes. The only trace is a single alert, filed at <code>warning</code>, in a stream that almost nobody reads at that level.</p>
<p>The behaviour it produces is worse than an outright failure, because it is partial. A miscased <code>&lt;Say&gt;</code> means silence where a prompt should be, and the call proceeds to the next verb as though the caller had heard it. A miscased <code>numDigits</code> means <code>&lt;Gather&gt;</code> falls back to its default and posts after the first keypress, so your handler receives a one-digit extension and reports an invalid entry. The bug that gets filed is <em>customers cannot enter their account number</em>, and it will be investigated in your application code, where nothing is wrong.</p>""",
"why": """<p><strong>It is logged at warning, and warning is not in anybody's query.</strong> Alerting, dashboards and the ad-hoc scripts everyone writes all default to <code>LogLevel=error</code>, because that is where failures live. 12200 is one of a small set that does not &mdash; 32012 and several of the 132xx Dial attribute errors behave the same way &mdash; and each of them is invisible to every sweep you already have.</p>
<p><strong>TwiML is case-sensitive and closed-vocabulary, and XML is neither.</strong> An XML parser is perfectly happy with <code>&lt;say&gt;</code>; it is a well-formed element with a name. Only the TwiML schema knows that the name has to be <code>Say</code>. So the document passes the check that produces a loud error and fails the one that produces a quiet warning.</p>
<p><strong>Templating engines lower-case things.</strong> Hand-written TwiML rarely gets this wrong twice. TwiML assembled by string interpolation, or emitted by a helper that normalises tag names, or copied out of a blog post that was rendered through a markdown pipeline, gets it wrong systematically and in one place.</p>
<p><strong>SSML inside <code>&lt;Say&gt;</code> is lower-case on purpose.</strong> <code>&lt;break&gt;</code>, <code>&lt;prosody&gt;</code> and <code>&lt;say-as&gt;</code> are correct exactly as written. Any check that flags lower-case tags has to exclude the contents of <code>&lt;Say&gt;</code>, or it will report a correct document as broken and be switched off within a day.</p>""",
"steps": [
 {"h": "Sweep the warning level, and put it in the standing query",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=warning&amp;StartDate={ISO8601}</code>, filtering to <code>error_code == 12200</code>. If you take one thing from this note, make it that your alert sweep runs at both levels. The window is bounded by the thirty-day retention regardless.</p>"""},
 {"h": "Group by endpoint before fetching anything",
  "body": """<p>A miscased verb is emitted by one code path and fires on every call through it, so a thousand alerts are one bug. Group on host plus path with the query string dropped, and the report goes from a wall of alerts to a list of two or three handlers.</p>"""},
 {"h": "Fetch one alert per endpoint and read response_body",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts/{AlertSid}</code> is the only place <code>response_body</code> is populated. <code>alert_text</code> carries the line and column, which is useful, but the document itself is what tells you whether the problem is a verb, an attribute or a nesting rule.</p>"""},
 {"h": "Scan the document against the vocabulary, and exempt Say",
  "body": """<p>Compare each element name against the TwiML verbs case-sensitively: a name that differs only in case is a casing bug with an obvious fix, and a name that is not in the vocabulary at all is something else entirely. Do the same for the camelCase attributes. Strip the children of <code>&lt;Say&gt;</code> first &mdash; SSML lives there and is meant to be lower-case.</p>"""},
 {"h": "Fix the emission point and re-run over a fresh window",
  "body": """<p>The repair is in whatever renders the TwiML, not in Twilio. Correct the casing at the source, deploy, and sweep again from a start date after the deploy: the old alerts stay in the thirty-day window and will otherwise look like the fix did not take.</p>"""},
],
"verify": """<p>Sweep again with a start date after the deploy. The 12200 count should be zero.</p>
<pre><code class="language-bash">python3 twilio_twiml_schema_audit.py --days 1 --sample
# 0 endpoint(s) emitting 12200 in the last 1 day(s)</code></pre>""",
"code_intro": "One paginated GET at <code>LogLevel=warning</code>, then one fetch per endpoint for a sample document &mdash; reads only, with an API Key that has read access. The scanner is pure and works on the bytes Twilio received: it is not a schema validator, it is a check for the two mistakes that produce almost every 12200, with the contents of <code>&lt;Say&gt;</code> deliberately exempted.",
"py_file": "twilio_twiml_schema_audit.py",
"py": '''"""Report TwiML that parses and then fails the schema: error 12200.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is in your own template, and it
is printed rather than performed.
"""
import argparse
import datetime as dt
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_twiml_schema_audit")

MONITOR = "https://monitor.twilio.com/v1"

VERBS = {
    "Response", "Say", "Play", "Gather", "Record", "Dial", "Sms", "Message",
    "Body", "Media", "Redirect", "Hangup", "Reject", "Pause", "Enqueue", "Leave",
    "Queue", "Conference", "Number", "Client", "Sip", "Task", "Refer", "Pay",
    "Prompt", "Parameter", "Connect", "Stream", "Start", "Stop", "Siprec",
    "VirtualAgent", "Identity", "Room", "Application",
}
VERB_BY_LOWER = {v.lower(): v for v in VERBS}

# Only the camelCase attributes: those are where the casing mistakes happen, and
# limiting the list to them keeps the scanner from inventing findings about
# attributes it simply has not heard of.
ATTRS = [
    "numDigits", "finishOnKey", "speechTimeout", "speechModel", "actionOnEmptyResult",
    "partialResultCallback", "partialResultCallbackMethod", "callerId", "timeLimit",
    "hangupOnStar", "answerOnBridge", "ringTone", "recordingStatusCallback",
    "recordingStatusCallbackMethod", "recordingStatusCallbackEvent", "maxLength",
    "playBeep", "transcribeCallback", "statusCallback", "statusCallbackEvent",
    "statusCallbackMethod", "waitUrl", "waitMethod", "startConferenceOnEnter",
    "endConferenceOnExit", "maxParticipants", "sendDigits", "machineDetection",
    "referUrl", "maxSpeechTime", "profanityFilter", "playTone", "recordingTrack",
]
ATTR_BY_LOWER = {a.lower(): a for a in ATTRS}

TAG = re.compile(r"<\\s*(/?)\\s*([A-Za-z_][A-Za-z0-9_.-]*)([^<>]*?)/?>", re.S)
ATTR_NAME = re.compile(r"([A-Za-z_][A-Za-z0-9_.:-]*)\\s*=")
SAY_BLOCK = re.compile(r"(<\\s*[Ss][Aa][Yy]\\b[^<>]*>)(.*?)(<\\s*/\\s*[Ss][Aa][Yy]\\s*>)", re.S)


def code_of(alert):
    """error_code arrives as a string on some alerts and an int on others."""
    try:
        return int(alert.get("error_code"))
    except (TypeError, ValueError):
        return None


def strip_say_children(xml):
    """Drop what is inside <Say>, keeping the tags themselves.

    Pure. SSML is lower-case by design: <break>, <prosody> and <say-as> are
    correct exactly as written, and a scanner that flags them reports a healthy
    document as broken. The Say tags stay so their own casing is still checked.
    """
    return SAY_BLOCK.sub(lambda m: m.group(1) + m.group(3), str(xml or ""))


def scan(xml):
    """Find the schema mistakes in a TwiML document. Pure, so the vocabulary
    rules can be tested without a network.

    Returns a list of (kind, found, suggestion). This is not a validator: it is
    a check for the two mistakes that produce almost every 12200.
    """
    body = strip_say_children(xml)
    findings, seen, root_checked = [], set(), False

    def note(kind, found, suggestion):
        keyps = (kind, found)
        if keyps in seen:
            return
        seen.add(keyps)
        findings.append((kind, found, suggestion))

    for match in TAG.finditer(body):
        closing, name, rest = match.group(1), match.group(2), match.group(3) or ""

        if not root_checked and not closing:
            root_checked = True
            if name != "Response":
                if name.lower() == "response":
                    note("verb-casing", name, "Response")
                else:
                    note("root", name, "Response")
                continue

        if name not in VERBS:
            canonical = VERB_BY_LOWER.get(name.lower())
            if canonical:
                note("verb-casing", name, canonical)
            else:
                note("unknown-verb", name, None)
            continue

        if closing:
            continue
        for attr in ATTR_NAME.findall(rest):
            if attr in ATTR_BY_LOWER.values():
                continue
            canonical = ATTR_BY_LOWER.get(attr.lower())
            if canonical:
                note("attribute-casing", attr, canonical)

    return findings


def verdict(findings, count=1):
    """Turn the scan into one line for the report. Pure. Returns (state, detail)."""
    by_kind = {}
    for kind, found, suggestion in findings:
        by_kind.setdefault(kind, []).append((found, suggestion))

    def named(kind):
        return ", ".join("%s should be %s" % (f, s) if s else f
                         for f, s in by_kind[kind][:4])

    if "verb-casing" in by_kind:
        return ("verb-casing",
                "%d alert(s): %s. TwiML is case-sensitive, so the verb is "
                "skipped and the call continues past it." % (count, named("verb-casing")))
    if "attribute-casing" in by_kind:
        return ("attribute-casing",
                "%d alert(s): %s. The attribute is dropped and the verb runs on "
                "its default." % (count, named("attribute-casing")))
    if "root" in by_kind:
        return ("bad-root",
                "%d alert(s): the document root is %s. Every TwiML document has "
                "to be <Response>." % (count, named("root")))
    if "unknown-verb" in by_kind:
        return ("unknown-verb",
                "%d alert(s): %s is not in the TwiML vocabulary at all, so it is "
                "not a casing slip." % (count, named("unknown-verb")))
    return ("unexplained",
            "%d alert(s) and the scanner found no casing or vocabulary mistake: "
            "read alert_text for the line and column, and check the nesting."
            % count)


def endpoint(url):
    """Host plus path, lowercased. One bad template fires on every call through
    it, and grouping on the raw URL hides that."""
    u = str(url or "").strip()
    for scheme in ("https://", "http://"):
        if u.lower().startswith(scheme):
            u = u[len(scheme):]
            break
    return u.split("?", 1)[0].split("#", 1)[0].rstrip("/").lower()


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_alerts(session, since, limit=10000, log_level="warning"):
    url = MONITOR + "/Alerts"
    params = {"PageSize": 100, "LogLevel": log_level, "StartDate": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("alerts", []))
        url, params = (page.get("meta") or {}).get("next_page_url"), {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7, help="alert window, max 30")
    ap.add_argument("--sample", action="store_true",
                    help="one extra GET per endpoint to read the actual document")
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

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=min(args.days, 30))).strftime("%Y-%m-%dT%H:%M:%SZ")
    # LogLevel=warning is the point of this script: 12200 never appears in an
    # error-only sweep, which is why accounts carry it for months.
    alerts = [a for a in list_alerts(session, since) if code_of(a) == 12200]
    if not alerts:
        log.info("0 endpoint(s) emitting 12200 in the last %d day(s)", args.days)
        return 0

    rows = {}
    for a in alerts:
        e = endpoint(a.get("request_url"))
        row = rows.setdefault(e, {"count": 0, "sid": a.get("sid"),
                                  "text": a.get("alert_text") or ""})
        row["count"] += 1

    bad = 0
    for e, row in sorted(rows.items(), key=lambda kv: -kv[1]["count"]):
        findings = []
        if args.sample and row["sid"]:
            full = get(session, "%s/Alerts/%s" % (MONITOR, row["sid"]))
            findings = scan(full.get("response_body"))
        state, detail = verdict(findings, row["count"])
        bad += 1
        log.warning("%-18s %s  %s", state, e or "unknown endpoint", detail)
        if not args.sample:
            log.warning("  re-run with --sample to read the document Twilio received")
        log.warning("  repair: correct the casing in the template that renders "
                    "this document; alert_text gives the line and column: %s",
                    row["text"][:160])

    log.info("%d endpoint(s) emitting 12200 in the last %d day(s)", bad, args.days)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-twiml-schema-audit.mjs",
"js": '''/**
 * Report TwiML that parses and then fails the schema: error 12200.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is in your own
 * template, and it is printed rather than performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';

const VERBS = new Set([
  'Response', 'Say', 'Play', 'Gather', 'Record', 'Dial', 'Sms', 'Message',
  'Body', 'Media', 'Redirect', 'Hangup', 'Reject', 'Pause', 'Enqueue', 'Leave',
  'Queue', 'Conference', 'Number', 'Client', 'Sip', 'Task', 'Refer', 'Pay',
  'Prompt', 'Parameter', 'Connect', 'Stream', 'Start', 'Stop', 'Siprec',
  'VirtualAgent', 'Identity', 'Room', 'Application',
]);
const VERB_BY_LOWER = new Map([...VERBS].map((v) => [v.toLowerCase(), v]));

// Only the camelCase attributes: those are where the casing mistakes happen,
// and limiting the list to them keeps the scanner from inventing findings about
// attributes it simply has not heard of.
const ATTRS = [
  'numDigits', 'finishOnKey', 'speechTimeout', 'speechModel', 'actionOnEmptyResult',
  'partialResultCallback', 'partialResultCallbackMethod', 'callerId', 'timeLimit',
  'hangupOnStar', 'answerOnBridge', 'ringTone', 'recordingStatusCallback',
  'recordingStatusCallbackMethod', 'recordingStatusCallbackEvent', 'maxLength',
  'playBeep', 'transcribeCallback', 'statusCallback', 'statusCallbackEvent',
  'statusCallbackMethod', 'waitUrl', 'waitMethod', 'startConferenceOnEnter',
  'endConferenceOnExit', 'maxParticipants', 'sendDigits', 'machineDetection',
  'referUrl', 'maxSpeechTime', 'profanityFilter', 'playTone', 'recordingTrack',
];
const ATTR_BY_LOWER = new Map(ATTRS.map((a) => [a.toLowerCase(), a]));
const ATTR_SET = new Set(ATTRS);

const TAG = /<\\s*(\\/?)\\s*([A-Za-z_][A-Za-z0-9_.-]*)([^<>]*?)\\/?>/gs;
const ATTR_NAME = /([A-Za-z_][A-Za-z0-9_.:-]*)\\s*=/g;
const SAY_BLOCK = /(<\\s*[Ss][Aa][Yy]\\b[^<>]*>)([\\s\\S]*?)(<\\s*\\/\\s*[Ss][Aa][Yy]\\s*>)/g;

/** error_code arrives as a string on some alerts and a number on others. */
export function codeOf(alert) {
  const n = Number(alert?.error_code);
  return Number.isFinite(n) ? n : null;
}

/**
 * Drop what is inside <Say>, keeping the tags themselves. Pure. SSML is
 * lower-case by design, and a scanner that flags it reports a healthy document
 * as broken. The Say tags stay so their own casing is still checked.
 */
export function stripSayChildren(xml) {
  return String(xml ?? '').replace(SAY_BLOCK, (m, open, inner, close) => open + close);
}

/**
 * Find the schema mistakes in a TwiML document. Pure, so the vocabulary rules
 * can be tested without a network. Returns [kind, found, suggestion] triples.
 * This is not a validator: it is a check for the two mistakes that produce
 * almost every 12200.
 */
export function scan(xml) {
  const body = stripSayChildren(xml);
  const findings = [];
  const seen = new Set();
  let rootChecked = false;

  const note = (kind, found, suggestion) => {
    const k = `${kind}\\u0000${found}`;
    if (seen.has(k)) return;
    seen.add(k);
    findings.push([kind, found, suggestion]);
  };

  for (const match of body.matchAll(TAG)) {
    const closing = match[1];
    const name = match[2];
    const rest = match[3] ?? '';

    if (!rootChecked && !closing) {
      rootChecked = true;
      if (name !== 'Response') {
        if (name.toLowerCase() === 'response') note('verb-casing', name, 'Response');
        else note('root', name, 'Response');
        continue;
      }
    }

    if (!VERBS.has(name)) {
      const canonical = VERB_BY_LOWER.get(name.toLowerCase());
      if (canonical) note('verb-casing', name, canonical);
      else note('unknown-verb', name, null);
      continue;
    }

    if (closing) continue;
    for (const attr of rest.matchAll(ATTR_NAME)) {
      const found = attr[1];
      if (ATTR_SET.has(found)) continue;
      const canonical = ATTR_BY_LOWER.get(found.toLowerCase());
      if (canonical) note('attribute-casing', found, canonical);
    }
  }

  return findings;
}

/** Turn the scan into one line for the report. Pure. Returns [state, detail]. */
export function verdict(findings, count = 1) {
  const byKind = new Map();
  for (const [kind, found, suggestion] of findings) {
    if (!byKind.has(kind)) byKind.set(kind, []);
    byKind.get(kind).push([found, suggestion]);
  }
  const named = (kind) => byKind.get(kind).slice(0, 4)
    .map(([f, s]) => (s ? `${f} should be ${s}` : f)).join(', ');

  if (byKind.has('verb-casing')) {
    return ['verb-casing',
      `${count} alert(s): ${named('verb-casing')}. TwiML is case-sensitive, so ` +
      'the verb is skipped and the call continues past it.'];
  }
  if (byKind.has('attribute-casing')) {
    return ['attribute-casing',
      `${count} alert(s): ${named('attribute-casing')}. The attribute is ` +
      'dropped and the verb runs on its default.'];
  }
  if (byKind.has('root')) {
    return ['bad-root',
      `${count} alert(s): the document root is ${named('root')}. Every TwiML ` +
      'document has to be <Response>.'];
  }
  if (byKind.has('unknown-verb')) {
    return ['unknown-verb',
      `${count} alert(s): ${named('unknown-verb')} is not in the TwiML ` +
      'vocabulary at all, so it is not a casing slip.'];
  }
  return ['unexplained',
    `${count} alert(s) and the scanner found no casing or vocabulary mistake: ` +
    'read alert_text for the line and column, and check the nesting.'];
}

/** Host plus path, lowercased: one bad template fires on every call through it. */
export function endpoint(url) {
  let u = String(url ?? '').trim();
  for (const scheme of ['https://', 'http://']) {
    if (u.toLowerCase().startsWith(scheme)) { u = u.slice(scheme.length); break; }
  }
  return u.split('?')[0].split('#')[0].replace(/\\/+$/, '').toLowerCase();
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

export async function listAlerts(auth, since, limit = 10000, logLevel = 'warning') {
  const out = [];
  let next = `${MONITOR}/Alerts`;
  let query = { PageSize: 100, LogLevel: logLevel, StartDate: since };
  while (next && out.length < limit) {
    const page = await get(auth, next, query);
    out.push(...(page.alerts ?? []));
    next = page.meta?.next_page_url ?? null;
    query = {};
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
  const days = Math.min(Number(process.env.DAYS ?? 7), 30);
  const sample = process.argv.includes('--sample');

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 19) + 'Z';
  // LogLevel=warning is the point of this script: 12200 never appears in an
  // error-only sweep, which is why accounts carry it for months.
  const alerts = (await listAlerts(auth, since)).filter((a) => codeOf(a) === 12200);
  if (alerts.length === 0) {
    console.log(`0 endpoint(s) emitting 12200 in the last ${days} day(s)`);
    return;
  }

  const rows = new Map();
  for (const a of alerts) {
    const e = endpoint(a.request_url);
    const row = rows.get(e) ?? { count: 0, sid: a.sid, text: a.alert_text ?? '' };
    row.count += 1;
    rows.set(e, row);
  }

  let bad = 0;
  for (const [e, row] of [...rows.entries()].sort((a, b) => b[1].count - a[1].count)) {
    let findings = [];
    if (sample && row.sid) {
      const full = await get(auth, `${MONITOR}/Alerts/${row.sid}`);
      findings = scan(full.response_body);
    }
    const [state, detail] = verdict(findings, row.count);
    bad += 1;
    console.warn(`${state.padEnd(18)} ${e || 'unknown endpoint'}  ${detail}`);
    if (!sample) console.warn('  re-run with --sample to read the document Twilio received');
    console.warn('  repair: correct the casing in the template that renders this ' +
                 `document; alert_text gives the line and column: ${row.text.slice(0, 160)}`);
  }

  console.log(`${bad} endpoint(s) emitting 12200 in the last ${days} day(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that keeps the scanner usable is the SSML one. A <code>&lt;break&gt;</code> tag inside <code>&lt;Say&gt;</code> is correct TwiML and a naive lower-case check reports it as a bug; one false positive on a healthy document and nobody runs the script again. The other case worth pinning is the difference between a verb that is miscased and a verb that does not exist, because those are two different conversations with whoever wrote the template.",
"test_py_file": "test_twilio_twiml_schema_audit.py",
"test_py": '''from twilio_twiml_schema_audit import scan, strip_say_children, verdict

GOOD = """<?xml version="1.0" encoding="UTF-8"?>
<Response><Gather numDigits="4" action="/entered"><Say>Enter your code</Say></Gather></Response>"""


def test_a_correct_document_produces_nothing():
    assert scan(GOOD) == []
    assert verdict(scan(GOOD), 0)[0] == "unexplained"


def test_ssml_inside_say_is_not_a_casing_error():
    # The false positive that would get this script switched off.
    doc = '<Response><Say>One<break time="500ms"/>two<say-as>3</say-as></Say></Response>'
    assert scan(doc) == []


def test_a_lowercase_say_is_still_caught_even_though_say_is_exempt():
    doc = "<Response><say>hello<break/></say></Response>"
    findings = scan(doc)
    assert ("verb-casing", "say", "Say") in findings
    assert not any(f[1] == "break" for f in findings)


def test_a_miscased_attribute_names_the_camelcase_form():
    doc = '<Response><Gather numdigits="4"/></Response>'
    state, detail = verdict(scan(doc), 12)
    assert state == "attribute-casing"
    assert "numdigits should be numDigits" in detail
    assert "12 alert(s)" in detail


def test_an_unknown_verb_is_not_reported_as_a_casing_slip():
    state, detail = verdict(scan("<Response><Speak>hi</Speak></Response>"))
    assert state == "unknown-verb"
    assert "not in the TwiML vocabulary" in detail


def test_a_root_that_is_not_response_is_its_own_state():
    state, detail = verdict(scan("<Twiml><Say>hi</Say></Twiml>"))
    assert state == "bad-root"
    assert "<Response>" in detail


def test_a_lowercase_root_is_a_casing_finding_not_a_bad_root():
    assert ("verb-casing", "response", "Response") in scan("<response><Say>hi</Say></response>")


def test_strip_say_children_keeps_the_tags_it_removes_the_contents_of():
    out = strip_say_children("<Response><Say voice=\\"alice\\"><break/></Say></Response>")
    assert "break" not in out
    assert "<Say voice=" in out and "</Say>" in out
''',
"test_js_file": "twilio-twiml-schema-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scan, stripSayChildren, verdict } from './twilio-twiml-schema-audit.mjs';

const GOOD = `<?xml version="1.0" encoding="UTF-8"?>
<Response><Gather numDigits="4" action="/entered"><Say>Enter your code</Say></Gather></Response>`;

test('a correct document produces nothing', () => {
  assert.deepEqual(scan(GOOD), []);
  assert.equal(verdict(scan(GOOD), 0)[0], 'unexplained');
});

test('ssml inside say is not a casing error', () => {
  const doc = '<Response><Say>One<break time="500ms"/>two<say-as>3</say-as></Say></Response>';
  assert.deepEqual(scan(doc), []);
});

test('a lowercase say is still caught even though say is exempt', () => {
  const findings = scan('<Response><say>hello<break/></say></Response>');
  assert.ok(findings.some(([k, f, s]) => k === 'verb-casing' && f === 'say' && s === 'Say'));
  assert.ok(!findings.some(([, f]) => f === 'break'));
});

test('a miscased attribute names the camelCase form', () => {
  const [state, detail] = verdict(scan('<Response><Gather numdigits="4"/></Response>'), 12);
  assert.equal(state, 'attribute-casing');
  assert.match(detail, /numdigits should be numDigits/);
  assert.match(detail, /12 alert\\(s\\)/);
});

test('an unknown verb is not reported as a casing slip', () => {
  const [state, detail] = verdict(scan('<Response><Speak>hi</Speak></Response>'));
  assert.equal(state, 'unknown-verb');
  assert.match(detail, /not in the TwiML vocabulary/);
});

test('a root that is not Response is its own state', () => {
  const [state, detail] = verdict(scan('<Twiml><Say>hi</Say></Twiml>'));
  assert.equal(state, 'bad-root');
  assert.match(detail, /<Response>/);
});

test('a lowercase root is a casing finding, not a bad root', () => {
  const findings = scan('<response><Say>hi</Say></response>');
  assert.ok(findings.some(([k, f, s]) => k === 'verb-casing' && f === 'response' && s === 'Response'));
});

test('stripSayChildren keeps the tags it removes the contents of', () => {
  const out = stripSayChildren('<Response><Say voice="alice"><break/></Say></Response>');
  assert.ok(!out.includes('break'));
  assert.ok(out.includes('<Say voice=') && out.includes('</Say>'));
});
''',
"faq": [
 ("Why does an error-only sweep never show 12200?",
  "Because Twilio files it at LogLevel=warning. The Alerts API filters on that field, and every dashboard and alert rule anyone writes defaults to error, since that is where failures live. 12200 is in a small group that does not follow that rule, along with 32012 and several of the 132xx Dial attribute errors."),
 ("How is 12200 different from 12100?",
  "12100 is an XML parser refusing the document: a stray character before the declaration, an unclosed tag, a bare ampersand. 12200 is a document that parsed cleanly and then failed the TwiML schema. One is malformed bytes, the other is well-formed XML that is not TwiML, and only the first stops the call outright."),
 ("What actually happens on the call when this fires?",
  "The offending part is skipped and the rest of the document executes. A miscased Say is silence where a prompt should have been; a miscased numDigits leaves Gather on its default, so it submits after one keypress. The call completes, which is why the bug gets filed against your application instead."),
 ("Why exempt the contents of Say from the scan?",
  "Because SSML is deliberately lower-case. break, prosody, say-as, phoneme and the rest are correct exactly as written and only appear inside Say. A scanner that flags them reports healthy documents as broken, and a check with false positives on correct code stops being run."),
 ("Can the script fix the TwiML?",
  "There is nothing on the Twilio side to fix. The document comes from your own handler, so the repair is a change in the template or the code that builds the string. The script tells you which endpoint, which name and what it should have been."),
],
"related": [
 ("/twilio/twiml-document-parse-failure-12100/", "TwiML that is not well-formed XML fails with 12100"),
 ("/twilio/webhook-invalid-content-type-12300/", "The wrong Content-Type on a TwiML response"),
 ("/twilio/twiml-response-body-too-large-11750/", "A TwiML response over the size limit"),
],
"citations": [CITE_12200, CITE_TWIML_VOICE, CITE_ALERTS, CITE_12100],
},

{
"slug": "whatsapp-content-template-rejected",
"title": "A rejected WhatsApp content template blocks every send",
"description": "whatsapp.status is rejected and 63040 comes back on every send. Outside the 24 hour window an approved template is the only thing that will deliver.",
"h1": "a rejected WhatsApp content template blocks every send",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 63040", "whatsapp template rejected",
             "content api approval requests", "twilio 63016 24 hour window",
             "whatsapp template paused 63041"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The template was approved in March and the notifications have gone out every day since. This morning they stopped. Nobody changed the code, nobody changed the template, and <code>whatsapp.status</code> now reads <code>paused</code> &mdash; Meta paused it on user feedback, and every send that uses it comes back <code>63041</code> until it comes back on its own.",
"short_answer": """<p>List your templates with <code>GET https://content.twilio.com/v1/Content</code>, then read each one's approval with <code>GET https://content.twilio.com/v1/Content/{ContentSid}/ApprovalRequests</code>. The field is <code>whatsapp.status</code>, and <code>rejected</code> comes with a <code>whatsapp.rejection_reason</code> that says what Meta objected to.</p>
<p>Four statuses are not sendable and each has its own error code: rejected is <code>63040</code>, paused is <code>63041</code>, disabled is <code>63042</code>, and a template that was never submitted leaves you sending freeform text, which is <code>63016</code> the moment you are outside the 24-hour customer-service window. Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error</code> for those four codes to see which of them your account is hitting now.</p>""",
"problem": """<p>Template state is not yours. Meta reviews every template, and it keeps reviewing them after approval: a template that has been fine for months can be paused because enough recipients blocked or reported the messages it was used for. Nothing in your account changes, nothing in your deploy pipeline changes, and the sends simply start failing. The state that decides whether your notifications go out lives behind two APIs and is edited by a third party.</p>
<p>What makes this worse than an ordinary outage is the fallback everyone reaches for. When a templated send fails, the instinct is to send the message as plain text instead. That works in testing, because whoever is testing has just messaged the sandbox and is inside the 24-hour window where freeform text is allowed. In production the recipients have not messaged you in days, so the fallback fails too, with <code>63016</code>, and now you have two failure codes and one broken feature.</p>""",
"why": """<p><strong>Approval is a third party's decision and it is revocable.</strong> <code>approved</code> is the state today, not a property of the template. Paused and disabled are both reached without you doing anything, on feedback from the people receiving your messages, and neither arrives as a notification you have subscribed to.</p>
<p><strong>The four codes look like one problem and are four.</strong> <code>63040</code> needs a rewrite and a resubmission. <code>63041</code> lifts by itself if the feedback stops. <code>63042</code> is terminal for that template. <code>63016</code> is not about the template at all &mdash; it is about the window. Treating them as "WhatsApp is broken" gets you the wrong repair three times out of four.</p>
<p><strong>Rejection reasons are specific and are not in the error.</strong> The alert tells you the send failed. <code>whatsapp.rejection_reason</code> on the approval request tells you it was the placeholder at the start of the body, or the category you picked, or copy that reads as promotional in a utility template. That string is the entire content of the fix and it is only on the Content API.</p>
<p><strong>The 24-hour window is invisible from your side.</strong> Nothing in your code knows when a given recipient last messaged you unless you track it. So the freeform fallback that worked during development is a coin toss in production, and it fails for exactly the recipients who most need the notification: the quiet ones.</p>""",
"steps": [
 {"h": "Enumerate the templates rather than the ones you remember",
  "body": """<p><code>GET https://content.twilio.com/v1/Content</code>, following <code>meta.next_page_url</code>. Templates accumulate the way Messaging Services do: one per language, one per campaign, several from experiments. The one that broke this morning is not necessarily the one you would have checked.</p>"""},
 {"h": "Read the approval per template, not the template body",
  "body": """<p><code>GET https://content.twilio.com/v1/Content/{ContentSid}/ApprovalRequests</code> returns the <code>whatsapp</code> block with <code>status</code>, <code>name</code>, <code>category</code> and <code>rejection_reason</code>. A template with no approval request at all answers a different question: it was never submitted, so it has never been usable outside the 24-hour window.</p>"""},
 {"h": "Sweep the four error codes for what is failing right now",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate={ISO8601}</code>, counting <code>63016</code>, <code>63040</code>, <code>63041</code> and <code>63042</code>. The alerts do not carry a ContentSid, so this is account-level context rather than per-template attribution &mdash; useful for ranking, not for blaming a specific template.</p>"""},
 {"h": "Separate the template problem from the window problem",
  "body": """<p><code>63016</code> alongside an approved template means something in your code is sending freeform text where it should be sending the template. That is a code fix, not a resubmission, and it will not be helped by anything you do to the template.</p>"""},
 {"h": "Resubmit, then wait for approved before sending again",
  "body": """<p>Fix the body and <code>POST https://content.twilio.com/v1/Content/{ContentSid}/ApprovalRequests/whatsapp</code> with <code>Name</code> and <code>Category</code>. Re-run this script until <code>whatsapp.status</code> reads <code>approved</code>; sending against a template still in review fails exactly as it did before, and each failed send is more negative signal.</p>"""},
],
"verify": """<p>Re-run the script. Every template you send from should report <code>approved</code>, and the 63040 family count should be zero.</p>
<pre><code class="language-bash">python3 twilio_whatsapp_template_audit.py
# 9 template(s), 0 not usable</code></pre>""",
"code_intro": "One paginated GET for the templates, one per template for its approval, and one over the alerts for the error codes &mdash; reads only, with an API Key that has read access. The classifier is pure and takes the alert counts alongside the approval, because an approved template plus a pile of <code>63016</code> is a bug in your sending code and looks nothing like a rejected one.",
"py_file": "twilio_whatsapp_template_audit.py",
"py": '''"""Report WhatsApp content templates that cannot currently be sent.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The resubmission is printed, never
performed, because this script holds a credential to an account that can send
messages and spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_whatsapp_template_audit")

CONTENT = "https://content.twilio.com/v1"
MONITOR = "https://monitor.twilio.com/v1"

WA_CODES = {
    63016: "freeform message sent outside the 24 hour customer service window",
    63040: "template rejected",
    63041: "template paused",
    63042: "template disabled",
}
BLOCKING = (63040, 63041, 63042)


def code_of(alert):
    """error_code arrives as a string on some alerts and an int on others."""
    try:
        return int(alert.get("error_code"))
    except (TypeError, ValueError):
        return None


def whatsapp_status(approval):
    """Pull status and rejection_reason out of an approval request. Pure.

    An absent approval is not an error: it means nobody ever submitted this
    template, which is a different finding from one that was refused.
    """
    wa = ((approval or {}).get("whatsapp") or {})
    status = str(wa.get("status") or "unsubmitted").strip().lower()
    return status, str(wa.get("rejection_reason") or "").strip()


def explain_code(code):
    """What one of the four WhatsApp codes actually means. Pure."""
    return WA_CODES.get(code, "unrecognised WhatsApp error code")


def verdict(content, approval, code_hits=None):
    """Classify one Content template. Pure, so every status can be tested
    without a network.

    `code_hits` maps WhatsApp error codes to counts seen in the alert window.
    Alerts do not carry a ContentSid, so those counts are account-level context
    and the classifier says so rather than pretending to attribute them.
    Returns (state, detail).
    """
    hits = code_hits or {}
    status, reason = whatsapp_status(approval)

    blocked = sum(hits.get(c, 0) for c in BLOCKING)
    context = ""
    if blocked:
        context = (" Alerts logged %d blocked-template error(s) on this account "
                   "in the window; they carry no ContentSid, so treat that as "
                   "context rather than attribution." % blocked)

    if status == "rejected":
        return ("rejected",
                "whatsapp.status is rejected: %s. Every send using this template "
                "returns 63040 until it is rewritten, resubmitted and approved.%s"
                % (reason or "no rejection_reason given", context))

    if status == "paused":
        return ("paused",
                "whatsapp.status is paused, so sends return 63041. Meta pauses a "
                "template on negative feedback; it lifts on its own if the "
                "feedback stops, and does not if it does not.%s" % context)

    if status == "disabled":
        return ("disabled",
                "whatsapp.status is disabled, so sends return 63042. This is "
                "terminal for this template: build a new one rather than waiting."
                "%s" % context)

    if status == "pending":
        return ("pending",
                "submitted and not yet reviewed. It is not usable outside the 24 "
                "hour window yet, and sending against it now just adds failures.")

    if status == "unsubmitted":
        return ("unsubmitted",
                "no WhatsApp approval request exists for this template, so it "
                "has never been sendable outside the 24 hour window. Anything "
                "falling back to freeform text there returns 63016.")

    if status == "approved":
        freeform = hits.get(63016, 0)
        if freeform:
            return ("approved-but-freeform",
                    "approved, but the account logged %d 63016 in the window: "
                    "something is sending plain text outside the 24 hour window "
                    "instead of this template. That is a code fix, not a "
                    "resubmission." % freeform)
        return ("approved", "approved and sendable.")

    return ("unknown-status",
            "whatsapp.status is %s, which this script does not recognise: read "
            "the approval request before acting." % (status or "empty"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=1000, **params):
    """Page a v1 list. meta.next_page_url is absolute."""
    out = []
    params.setdefault("PageSize", 100)
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url, params = (page.get("meta") or {}).get("next_page_url"), {}
    return out[:limit]


def approval_for(session, content_sid):
    """A template with no approval request answers 404, and that is a finding
    rather than an error."""
    r = session.get("%s/Content/%s/ApprovalRequests" % (CONTENT, content_sid),
                    timeout=30)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: the API key needs read access to Content"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7, help="alert window, max 30")
    ap.add_argument("--max-templates", type=int, default=500)
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

    contents = list_v1(session, CONTENT + "/Content", "contents", args.max_templates)
    if not contents:
        log.info("no Content templates on this account")
        return 0

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=min(args.days, 30))).strftime("%Y-%m-%dT%H:%M:%SZ")
    hits = {}
    for a in list_v1(session, MONITOR + "/Alerts", "alerts", 10000,
                     LogLevel="error", StartDate=since):
        c = code_of(a)
        if c in WA_CODES:
            hits[c] = hits.get(c, 0) + 1
    for c, n in sorted(hits.items()):
        log.info("%d alert(s) of %d: %s", n, c, explain_code(c))

    bad = 0
    for content in contents:
        state, detail = verdict(content, approval_for(session, content.get("sid")), hits)
        line = "%-21s %s  %s" % (state, content.get("friendly_name",
                                                    content.get("sid")), detail)
        if state == "approved":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("rejected", "disabled", "unsubmitted"):
            log.warning("  repair: fix the body, then POST %s/Content/%s/"
                        "ApprovalRequests/whatsapp with Name and Category, and "
                        "wait for approved before sending", CONTENT,
                        content.get("sid"))

    log.info("%d template(s), %d not usable", len(contents), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-whatsapp-template-audit.mjs",
"js": '''/**
 * Report WhatsApp content templates that cannot currently be sent.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The resubmission is printed, never
 * performed.
 */
const CONTENT = 'https://content.twilio.com/v1';
const MONITOR = 'https://monitor.twilio.com/v1';

const WA_CODES = new Map([
  [63016, 'freeform message sent outside the 24 hour customer service window'],
  [63040, 'template rejected'],
  [63041, 'template paused'],
  [63042, 'template disabled'],
]);
const BLOCKING = [63040, 63041, 63042];

/** error_code arrives as a string on some alerts and a number on others. */
export function codeOf(alert) {
  const n = Number(alert?.error_code);
  return Number.isFinite(n) ? n : null;
}

/**
 * Pull status and rejection_reason out of an approval request. Pure. An absent
 * approval is not an error: it means nobody ever submitted this template.
 */
export function whatsappStatus(approval) {
  const wa = approval?.whatsapp ?? {};
  const status = String(wa.status ?? 'unsubmitted').trim().toLowerCase();
  return [status, String(wa.rejection_reason ?? '').trim()];
}

/** What one of the four WhatsApp codes actually means. Pure. */
export function explainCode(code) {
  return WA_CODES.get(code) ?? 'unrecognised WhatsApp error code';
}

/**
 * Classify one Content template. Pure, so every status can be tested without a
 * network. `codeHits` maps WhatsApp error codes to counts seen in the alert
 * window; alerts carry no ContentSid, so the classifier reports those as
 * context rather than attribution. Returns [state, detail].
 */
export function verdict(content, approval, codeHits = null) {
  const hits = codeHits ?? {};
  const [status, reason] = whatsappStatus(approval);

  const blocked = BLOCKING.reduce((n, c) => n + (hits[c] ?? 0), 0);
  const context = blocked
    ? ` Alerts logged ${blocked} blocked-template error(s) on this account in ` +
      'the window; they carry no ContentSid, so treat that as context rather ' +
      'than attribution.'
    : '';

  if (status === 'rejected') {
    return ['rejected',
      `whatsapp.status is rejected: ${reason || 'no rejection_reason given'}. ` +
      'Every send using this template returns 63040 until it is rewritten, ' +
      `resubmitted and approved.${context}`];
  }

  if (status === 'paused') {
    return ['paused',
      'whatsapp.status is paused, so sends return 63041. Meta pauses a template ' +
      'on negative feedback; it lifts on its own if the feedback stops, and ' +
      `does not if it does not.${context}`];
  }

  if (status === 'disabled') {
    return ['disabled',
      'whatsapp.status is disabled, so sends return 63042. This is terminal for ' +
      `this template: build a new one rather than waiting.${context}`];
  }

  if (status === 'pending') {
    return ['pending',
      'submitted and not yet reviewed. It is not usable outside the 24 hour ' +
      'window yet, and sending against it now just adds failures.'];
  }

  if (status === 'unsubmitted') {
    return ['unsubmitted',
      'no WhatsApp approval request exists for this template, so it has never ' +
      'been sendable outside the 24 hour window. Anything falling back to ' +
      'freeform text there returns 63016.'];
  }

  if (status === 'approved') {
    const freeform = hits[63016] ?? 0;
    if (freeform) {
      return ['approved-but-freeform',
        `approved, but the account logged ${freeform} 63016 in the window: ` +
        'something is sending plain text outside the 24 hour window instead of ' +
        'this template. That is a code fix, not a resubmission.'];
    }
    return ['approved', 'approved and sendable.'];
  }

  return ['unknown-status',
    `whatsapp.status is ${status || 'empty'}, which this script does not ` +
    'recognise: read the approval request before acting.'];
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

export async function listV1(auth, url, key, limit = 1000, params = {}) {
  const out = [];
  let next = url;
  let query = { PageSize: 100, ...params };
  while (next && out.length < limit) {
    const page = await get(auth, next, query);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    query = {};
  }
  return out.slice(0, limit);
}

export async function approvalFor(auth, contentSid) {
  const res = await fetch(`${CONTENT}/Content/${contentSid}/ApprovalRequests`,
                          { headers: { Authorization: auth } });
  if (res.status === 404) return null;
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: the API key needs read access to Content`);
  }
  if (!res.ok) throw new Error(`${res.status} reading approvals for ${contentSid}`);
  return res.json();
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
  const days = Math.min(Number(process.env.DAYS ?? 7), 30);

  const contents = await listV1(auth, `${CONTENT}/Content`, 'contents', 500);
  if (contents.length === 0) {
    console.log('no Content templates on this account');
    return;
  }

  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 19) + 'Z';
  const hits = {};
  for (const a of await listV1(auth, `${MONITOR}/Alerts`, 'alerts', 10000,
                               { LogLevel: 'error', StartDate: since })) {
    const c = codeOf(a);
    if (WA_CODES.has(c)) hits[c] = (hits[c] ?? 0) + 1;
  }
  for (const [c, n] of Object.entries(hits).sort()) {
    console.log(`${n} alert(s) of ${c}: ${explainCode(Number(c))}`);
  }

  let bad = 0;
  for (const content of contents) {
    const [state, detail] = verdict(content, await approvalFor(auth, content.sid), hits);
    const line = `${state.padEnd(21)} ${content.friendly_name ?? content.sid}  ${detail}`;
    if (state === 'approved') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'rejected' || state === 'disabled' || state === 'unsubmitted') {
      console.warn(`  repair: fix the body, then POST ${CONTENT}/Content/${content.sid}` +
                   '/ApprovalRequests/whatsapp with Name and Category, and wait ' +
                   'for approved before sending');
    }
  }

  console.log(`${contents.length} template(s), ${bad} not usable`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two cases that carry the note are the ones that look like each other and are not. A missing approval request is a template nobody ever submitted, which is not the same as one that was refused, and the classifier has to say so rather than defaulting to rejected. And an approved template on an account logging <code>63016</code> is a bug in your sending code &mdash; resubmitting the template would be a week spent on the wrong thing.",
"test_py_file": "test_twilio_whatsapp_template_audit.py",
"test_py": '''from twilio_whatsapp_template_audit import explain_code, verdict, whatsapp_status

TPL = {"sid": "HX0123456789", "friendly_name": "order_shipped_en"}


def approval(status, reason=""):
    return {"whatsapp": {"type": "whatsapp", "status": status,
                         "rejection_reason": reason}}


def test_rejected_carries_the_reason_meta_gave():
    state, detail = verdict(TPL, approval("rejected", "variable at start of body"))
    assert state == "rejected"
    assert "variable at start of body" in detail
    assert "63040" in detail


def test_paused_and_disabled_are_different_repairs():
    paused, pdetail = verdict(TPL, approval("paused"))
    disabled, ddetail = verdict(TPL, approval("disabled"))
    assert (paused, disabled) == ("paused", "disabled")
    assert "lifts on its own" in pdetail
    assert "terminal" in ddetail


def test_no_approval_request_is_unsubmitted_not_rejected():
    # 404 from ApprovalRequests: nobody ever submitted it.
    state, detail = verdict(TPL, None)
    assert state == "unsubmitted"
    assert "63016" in detail


def test_an_approved_template_on_an_account_logging_63016_is_a_code_bug():
    state, detail = verdict(TPL, approval("approved"), {63016: 84})
    assert state == "approved-but-freeform"
    assert "code fix, not a resubmission" in detail


def test_a_clean_approved_template_is_the_only_healthy_state():
    assert verdict(TPL, approval("approved"))[0] == "approved"
    assert verdict(TPL, approval("APPROVED"))[0] == "approved"


def test_blocking_counts_are_labelled_as_context_not_attribution():
    state, detail = verdict(TPL, approval("rejected"), {63040: 3, 63041: 2})
    assert state == "rejected"
    assert "5 blocked-template error(s)" in detail
    assert "context rather than attribution" in detail


def test_status_and_codes_are_read_defensively():
    assert whatsapp_status({}) == ("unsubmitted", "")
    assert whatsapp_status({"whatsapp": {"status": "Pending"}})[0] == "pending"
    assert verdict(TPL, {"whatsapp": {"status": "in_appeal"}})[0] == "unknown-status"
    assert explain_code(63042) == "template disabled"
    assert "unrecognised" in explain_code(12345)
''',
"test_js_file": "twilio-whatsapp-template-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { explainCode, verdict, whatsappStatus } from './twilio-whatsapp-template-audit.mjs';

const TPL = { sid: 'HX0123456789', friendly_name: 'order_shipped_en' };
const approval = (status, reason = '') =>
  ({ whatsapp: { type: 'whatsapp', status, rejection_reason: reason } });

test('rejected carries the reason Meta gave', () => {
  const [state, detail] = verdict(TPL, approval('rejected', 'variable at start of body'));
  assert.equal(state, 'rejected');
  assert.match(detail, /variable at start of body/);
  assert.match(detail, /63040/);
});

test('paused and disabled are different repairs', () => {
  const [paused, pdetail] = verdict(TPL, approval('paused'));
  const [disabled, ddetail] = verdict(TPL, approval('disabled'));
  assert.deepEqual([paused, disabled], ['paused', 'disabled']);
  assert.match(pdetail, /lifts on its own/);
  assert.match(ddetail, /terminal/);
});

test('no approval request is unsubmitted, not rejected', () => {
  const [state, detail] = verdict(TPL, null);
  assert.equal(state, 'unsubmitted');
  assert.match(detail, /63016/);
});

test('an approved template on an account logging 63016 is a code bug', () => {
  const [state, detail] = verdict(TPL, approval('approved'), { 63016: 84 });
  assert.equal(state, 'approved-but-freeform');
  assert.match(detail, /code fix, not a resubmission/);
});

test('a clean approved template is the only healthy state', () => {
  assert.equal(verdict(TPL, approval('approved'))[0], 'approved');
  assert.equal(verdict(TPL, approval('APPROVED'))[0], 'approved');
});

test('blocking counts are labelled as context, not attribution', () => {
  const [state, detail] = verdict(TPL, approval('rejected'), { 63040: 3, 63041: 2 });
  assert.equal(state, 'rejected');
  assert.match(detail, /5 blocked-template error\\(s\\)/);
  assert.match(detail, /context rather than attribution/);
});

test('status and codes are read defensively', () => {
  assert.deepEqual(whatsappStatus({}), ['unsubmitted', '']);
  assert.equal(whatsappStatus({ whatsapp: { status: 'Pending' } })[0], 'pending');
  assert.equal(verdict(TPL, { whatsapp: { status: 'in_appeal' } })[0], 'unknown-status');
  assert.equal(explainCode(63042), 'template disabled');
  assert.match(explainCode(12345), /unrecognised/);
});
''',
"faq": [
 ("The template was approved for months. Why did it stop working?",
  "Meta keeps reviewing after approval. Enough recipients blocking or reporting messages sent with a template moves it to paused, and a paused template that keeps collecting negative feedback becomes disabled. Nothing in your account changed; the state that decides delivery is edited by a third party."),
 ("Is paused the same as rejected?",
  "No, and the repair is different. Rejected means Meta refused the content and it needs a rewrite and a resubmission. Paused means an approved template is temporarily blocked on feedback and can lift by itself. Disabled is the end of that road and is terminal for that template."),
 ("Why do plain-text fallbacks fail in production and work in testing?",
  "The 24-hour customer service window. Whoever is testing has just messaged the sandbox, so freeform text is allowed. Real recipients have not messaged you in days, so the same code returns 63016. It fails hardest for the quiet recipients, who are the ones the notification was for."),
 ("Why can the script not tell me which template caused a 63040?",
  "The Monitor alert does not carry a ContentSid. Counting the codes tells you how much the account is losing to blocked templates right now, and the Content API tells you which templates are in a blocked state; joining those two into a claim about causation would be a guess, so the script reports them side by side and says which is which."),
 ("Should the script resubmit a rejected template?",
  "No. Resubmitting an unchanged template gets it rejected again and each rejection is more signal against you. The rejection_reason tells you what to change, a person changes it, and then the POST is one command. The script prints that command."),
],
"related": [
 ("/twilio/carrier-filtered-messages-30007/", "Carrier or Twilio silently filtering your SMS"),
 ("/twilio/messaging-service-no-status-callback/", "A Messaging Service with no status callback"),
 ("/twilio/no-error-log-subscription/", "Nobody subscribed to the error log"),
],
"citations": [CITE_63040, CITE_WA_TEMPLATES, CITE_63016, CITE_CONTENT],
},

]
