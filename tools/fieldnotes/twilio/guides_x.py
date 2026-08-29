#!/usr/bin/env python3
"""/twilio/ field notes, batch X — the writing.

Five failures in the space between a phone number, a sender pool and the clock.
Two of them return an error code on every affected send (21703, 14107), one gets
the whole pool blocked by a carrier rather than by Twilio (30032), and two return
nothing at all: a number that sends outside every Messaging Service, and a ten
hour delivery deadline that turns a passcode into an apology.

Read-only throughout, like the rest of the section: an API Key with read access,
never the account auth token, every request a GET, and the repair printed for a
human to run rather than performed by a script holding a credential that can send
messages and spend money.
"""

CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_SERVICE_PN = ("Messaging Service PhoneNumber resource — Twilio Docs",
                   "https://www.twilio.com/docs/messaging/api/phonenumber-resource")
CITE_SHORTCODE = ("Messaging Service ShortCode resource — Twilio Docs",
                  "https://www.twilio.com/docs/messaging/api/short-code-resource")
CITE_ALPHA = ("Messaging Service AlphaSender resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/alphasender-resource")
CITE_SERVICES_GUIDE = ("Messaging Services — Twilio Docs",
                       "https://www.twilio.com/docs/messaging/services")
CITE_SERVICES_TUT = ("Send messages with a Messaging Service — Twilio Docs",
                     "https://www.twilio.com/docs/messaging/tutorials/send-messages-with-messaging-services")
CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_LOOKUP = ("Lookup v2 API — Twilio Docs", "https://www.twilio.com/docs/lookup/v2-api")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_MSG_TWIML = ("TwiML for Programmable Messaging — Twilio Docs",
                  "https://www.twilio.com/docs/messaging/twiml")
CITE_SCALING = ("Scaling, queueing and message latency — Twilio Docs",
                "https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_21703 = ("Error 21703: no phone number available to send — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21703")
CITE_21704 = ("Error 21704: the Messaging Service contains no phone numbers — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21704")
CITE_30032 = ("Error 30032: toll-free number has not been verified — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30032")
CITE_30036 = ("Error 30036: validity period expired — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30036")
CITE_14107 = ("Error 14107: SMS send rate limit exceeded — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/14107")

GUIDES = [

{
"slug": "number-not-in-messaging-service",
"title": "An SMS number that belongs to no Messaging Service",
"description": "No error code, just unpooled sending: no sticky sender, no geomatch, no long code failover, and A2P registration that attaches through a pool.",
"h1": "an SMS number that belongs to no Messaging Service",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio number not in messaging service", "twilio sender pool missing number",
             "twilio sticky sender not working", "twilio geomatch messaging service",
             "twilio unpooled phone number"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing is failing. The number sends, the number receives, the console is green, and it has been like that for a year. It is also in no Messaging Service at all, which means every feature that lives on a service &mdash; sticky sender, geomatch, long code failover, and the A2P registration that attaches through a pool &mdash; has never applied to a single message it sent.",
"short_answer": """<p>Take a set difference. <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code> gives every number you own; keep the ones where <code>capabilities.sms</code> is true. <code>GET https://messaging.twilio.com/v1/Services?PageSize=1000</code> and then <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers?PageSize=1000</code> per service gives every number that is in a pool. What is in the first set and not the second is sending outside every Messaging Service you have.</p>
<p>There is no error code for this, so sort the findings by whether they matter yet: <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?From={E164}&amp;PageSize=1</code> separates a number that is quietly sending unpooled traffic today from one that is merely waiting to.</p>""",
"problem": """<p>This is the one note in the section where nothing is broken. Sends succeed, replies arrive, the API returns <code>201</code>, and if you only ever look for errors you will never look at this number again. What has happened instead is that a whole layer of the product was skipped: the Messaging Service is where Twilio implements sender selection, and a number outside every service is a bare <code>From</code> with no selection logic behind it.</p>
<p>The cost arrives later and indirectly. Deliverability drops because the traffic is coming from an unpooled long code rather than a registered sender. A conversation started from one number gets answered from another, because there is no sticky sender to keep it consistent. An international recipient gets a foreign long code because nothing is matching sender to destination. None of that produces a ticket that says &ldquo;this number is not in a Messaging Service&rdquo;; it produces slow, unattributable erosion, and a support thread about how customers say the texts feel like spam.</p>""",
"why": """<p><strong>The features are on the service, not on the number.</strong> Sticky sender, geomatch and long code failover are implemented by sender selection, and sender selection only runs when a send names a <code>MessagingServiceSid</code>. A number with a bare <code>sms_url</code> and no service association bypasses all of it, and the number's own resource has no field that admits this.</p>
<p><strong>Nothing in the number's own view mentions services.</strong> <code>IncomingPhoneNumbers</code> returns capabilities, URLs and SIDs. Pool membership lives on the other side of the relationship, in a subresource of each Messaging Service, so the only way to see the absence is to build both lists and subtract. Absence is the hardest thing to notice in an API that returns objects.</p>
<p><strong>Numbers get bought outside the flow that adds them.</strong> Somebody needed a second number for a test, or a regional line, or a port completed and the number arrived on the account with nothing attached. Buying a number succeeds. Adding it to a pool is a separate call that no failure will ever remind you to make.</p>
<p><strong>It is not the same finding as an unregistered 10DLC number.</strong> A US long code outside a pool also misses its A2P campaign and starts returning <code>30034</code>, which is a live outage with its own note. This one is wider and quieter: it includes your non-US numbers and your toll-free lines, none of which produce <code>30034</code>, and all of which are sending without the service layer.</p>""",
"steps": [
 {"h": "List the numbers, then narrow to the ones a pool would help",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, following <code>next_page_uri</code>. Keep entries whose <code>capabilities.sms</code> is true. A voice-only number is not a finding here, and reporting it teaches people to skim the report.</p>"""},
 {"h": "Build the pooled set from every service, not the one you remember",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code> paging on <code>meta.next_page_url</code>, then <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> for each. Accounts accumulate services &mdash; one per environment, one per tenant, one from a migration &mdash; and a number in the forgotten one is pooled, not unpooled.</p>"""},
 {"h": "Key the join on the SID, not the phone number string",
  "body": """<p>Both sides carry <code>sid</code> starting <code>PN</code>, and both carry <code>phone_number</code> in E.164. Join on the SID: it is stable, and it does not lose to a formatting difference the way a string comparison eventually does.</p>"""},
 {"h": "Ask whether the unpooled number is actually sending",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?From={E164}&amp;PageSize=1</code> with a <code>DateSent&gt;=</code> bound. One row is enough. A number sending today with no service behind it is worth an afternoon; a number that has sent nothing in ninety days is either about to be used or about to be released, and both of those are calm decisions.</p>"""},
 {"h": "Add it to the service that matches its traffic, then send through the service",
  "body": """<p>The repair is <code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> with <code>PhoneNumberSid=PN...</code>; the default cap is 400 numbers per service. Adding the number is only half of it, though: sender selection runs when the send names a <code>MessagingServiceSid</code>, so code that keeps passing a bare <code>From</code> gets no more of the service than it did yesterday.</p>"""},
],
"verify": """<p>Re-run the script. Every SMS-capable number should report <code>pooled</code>, and the unpooled count should be zero.</p>
<pre><code class="language-bash">python3 twilio_unpooled_number_audit.py --check-traffic
# 22 SMS capable number(s), 0 outside every Messaging Service</code></pre>""",
"code_intro": "One paginated GET over the numbers, one over the services, one per service for its pool, and with <code>--check-traffic</code> one more per unpooled number &mdash; an API Key with read access covers all of it. The classifier is pure and takes the number, the service holding it (or <code>None</code>) and its traffic count, because the difference between a finding worth acting on today and one worth scheduling is exactly those three inputs.",
"py_file": "twilio_unpooled_number_audit.py",
"py": '''"""Report SMS-capable Twilio numbers that are in no Messaging Service.

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
log = logging.getLogger("twilio_unpooled_number_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

# What a number outside every service does not get. All four are implemented by
# sender selection, which only runs when a send names a MessagingServiceSid.
LOST = ("no sticky sender, no geomatch, no long code failover, and the A2P "
        "campaign attaches through a pool this number is not in")


def verdict(number, service=None, traffic=None):
    """Classify one owned number against the Messaging Service holding it.

    `number` is an IncomingPhoneNumber. `service` is the Messaging Service whose
    pool contains it, or None when no pool does. `traffic` is how many outbound
    messages were seen from it in the window, or None when traffic was not
    checked at all: not checked and none found are different facts, and merging
    them makes an idle number look like an urgent one.

    Pure, so the scope rule and the priority rule can be tested without a
    network. Returns (state, detail).
    """
    caps = number.get("capabilities") or {}
    if not caps.get("sms"):
        return ("out-of-scope",
                "capabilities.sms is false, so a sender pool has nothing to "
                "offer it. Voice only numbers are somebody else's report.")

    if service:
        label = service.get("friendly_name") or service.get("sid") or "a service"
        return ("pooled", "in the sender pool of %s" % label)

    if traffic is None:
        return ("unpooled",
                "SMS capable and in no Messaging Service: %s." % LOST)
    if traffic > 0:
        return ("unpooled-sending",
                "sending today with no Messaging Service behind it, at least "
                "%d message(s) in the window: %s." % (traffic, LOST))
    return ("unpooled-idle",
            "SMS capable, in no Messaging Service, and nothing sent in the "
            "window. Pool it before somebody uses it, or release it.")


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


def list_services(session, limit):
    """Page Messaging Services. This API pages on meta.next_page_url, which is
    absolute, unlike the 2010-04-01 API next door."""
    url = "%s/Services" % MESSAGING
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("services", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def pooled_by_sid(session, services):
    """Map every pooled PN sid to the service holding it.

    Keyed on the sid rather than the E.164 string: both sides return the sid,
    and a sid does not lose to a formatting difference.
    """
    owner = {}
    for svc in services:
        url = "%s/Services/%s/PhoneNumbers" % (MESSAGING, svc.get("sid"))
        params = {"PageSize": 100}
        while url:
            page = get(session, url, **params)
            for entry in page.get("phone_numbers", []):
                owner[entry.get("sid")] = svc
            url = (page.get("meta") or {}).get("next_page_url")
            params = {}
    return owner


def outbound_count(session, account, e164, days):
    """One row is enough to know the number is in use. PageSize=1 keeps this to
    a single small response per flagged number."""
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    page = get(session, "%s/Accounts/%s/Messages.json" % (BASE, account),
               **{"From": e164, "DateSent>": since, "PageSize": 1})
    return len(page.get("messages", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000,
                    help="stop paging after this many numbers")
    ap.add_argument("--max-services", type=int, default=200,
                    help="stop paging after this many Messaging Services")
    ap.add_argument("--check-traffic", action="store_true",
                    help="one extra GET per unpooled number to see if it sends")
    ap.add_argument("--days", type=int, default=90,
                    help="traffic window in days for --check-traffic")
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
    services = list_services(session, args.max_services)
    owner = pooled_by_sid(session, services)
    log.info("%d number(s) on the account, %d Messaging Service(s), %d pooled sender(s)",
             len(numbers), len(services), len(owner))

    considered = bad = 0
    for n in numbers:
        service = owner.get(n.get("sid"))
        traffic = None
        if service is None and args.check_traffic and (n.get("capabilities") or {}).get("sms"):
            traffic = outbound_count(session, account, n.get("phone_number"), args.days)
        state, detail = verdict(n, service, traffic)
        if state == "out-of-scope":
            continue
        considered += 1
        line = "%-16s %s  %s" % (state, n.get("phone_number", "?"), detail)
        if state == "pooled":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: POST %s/Services/{ServiceSid}/PhoneNumbers "
                    "PhoneNumberSid=%s, then send with MessagingServiceSid "
                    "instead of a bare From so sender selection actually runs.",
                    MESSAGING, n.get("sid"))

    log.info("%d SMS capable number(s), %d outside every Messaging Service",
             considered, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-unpooled-number-audit.mjs",
"js": '''/**
 * Report SMS-capable Twilio numbers that are in no Messaging Service.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

// What a number outside every service does not get. All four are implemented by
// sender selection, which only runs when a send names a MessagingServiceSid.
const LOST = 'no sticky sender, no geomatch, no long code failover, and the A2P ' +
             'campaign attaches through a pool this number is not in';

/**
 * Classify one owned number against the Messaging Service holding it. `service`
 * is the service whose pool contains it or null; `traffic` is how many outbound
 * messages were seen in the window, or null when traffic was not checked. Not
 * checked and none found are different facts. Pure. Returns [state, detail].
 */
export function verdict(number, service = null, traffic = null) {
  const caps = number.capabilities ?? {};
  if (!caps.sms) {
    return ['out-of-scope',
      'capabilities.sms is false, so a sender pool has nothing to offer it. ' +
      "Voice only numbers are somebody else's report."];
  }

  if (service) {
    const label = service.friendly_name ?? service.sid ?? 'a service';
    return ['pooled', `in the sender pool of ${label}`];
  }

  if (traffic === null || traffic === undefined) {
    return ['unpooled', `SMS capable and in no Messaging Service: ${LOST}.`];
  }
  if (traffic > 0) {
    return ['unpooled-sending',
      'sending today with no Messaging Service behind it, at least ' +
      `${traffic} message(s) in the window: ${LOST}.`];
  }
  return ['unpooled-idle',
    'SMS capable, in no Messaging Service, and nothing sent in the window. ' +
    'Pool it before somebody uses it, or release it.'];
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

export async function listServices(auth, limit = 200) {
  let url = `${MESSAGING}/Services`;
  let params = { PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.services ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Map every pooled PN sid to the service holding it. Keyed on the sid. */
async function pooledBySid(auth, services) {
  const owner = new Map();
  for (const svc of services) {
    let url = `${MESSAGING}/Services/${svc.sid}/PhoneNumbers`;
    let params = { PageSize: 100 };
    while (url) {
      const page = await get(auth, url, params);
      for (const entry of page.phone_numbers ?? []) owner.set(entry.sid, svc);
      url = page.meta?.next_page_url ?? null;
      params = {};
    }
  }
  return owner;
}

async function outboundCount(auth, account, e164, days) {
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const page = await get(auth, `${BASE}/Accounts/${account}/Messages.json`,
                         { From: e164, 'DateSent>': since, PageSize: 1 });
  return (page.messages ?? []).length;
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
  const checkTraffic = process.argv.includes('--check-traffic');
  const days = flagValue('--days', 90);

  const numbers = await listNumbers(auth, account);
  const services = await listServices(auth);
  const owner = await pooledBySid(auth, services);
  console.log(`${numbers.length} number(s) on the account, ${services.length} ` +
              `Messaging Service(s), ${owner.size} pooled sender(s)`);

  let considered = 0;
  let bad = 0;
  for (const n of numbers) {
    const service = owner.get(n.sid) ?? null;
    let traffic = null;
    if (!service && checkTraffic && (n.capabilities ?? {}).sms) {
      traffic = await outboundCount(auth, account, n.phone_number, days);
    }
    const [state, detail] = verdict(n, service, traffic);
    if (state === 'out-of-scope') continue;
    considered += 1;
    const line = `${state.padEnd(16)} ${n.phone_number ?? '?'}  ${detail}`;
    if (state === 'pooled') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: POST ${MESSAGING}/Services/{ServiceSid}/PhoneNumbers ` +
                 `PhoneNumberSid=${n.sid}, then send with MessagingServiceSid ` +
                 'instead of a bare From so sender selection actually runs.');
  }

  console.log(`${considered} SMS capable number(s), ${bad} outside every Messaging Service`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two rules carry the note and both are about not crying wolf. A voice-only number is out of scope entirely, because a sender pool cannot help it and a report that lists it gets skimmed. And <code>traffic=None</code> has to stay distinct from <code>traffic=0</code>: one means nobody looked, the other means nobody is sending, and only the second is safe to leave until next quarter.",
"test_py_file": "test_twilio_unpooled_number_audit.py",
"test_py": '''from twilio_unpooled_number_audit import verdict

SMS = {"phone_number": "+15550001111", "sid": "PN1", "capabilities": {"sms": True, "voice": True}}
VOICE_ONLY = {"phone_number": "+15550002222", "sid": "PN2", "capabilities": {"sms": False, "voice": True}}
SERVICE = {"sid": "MG1", "friendly_name": "transactional"}


def test_a_number_in_a_pool_is_not_a_finding():
    state, detail = verdict(SMS, SERVICE)
    assert state == "pooled"
    assert "transactional" in detail


def test_an_unpooled_number_names_what_it_is_missing():
    state, detail = verdict(SMS)
    assert state == "unpooled"
    assert "sticky sender" in detail
    assert "geomatch" in detail


def test_a_voice_only_number_is_out_of_scope():
    # A sender pool cannot help it, and listing it trains people to skim.
    state, detail = verdict(VOICE_ONLY)
    assert state == "out-of-scope"
    assert "capabilities.sms is false" in detail


def test_unchecked_traffic_is_not_the_same_as_no_traffic():
    assert verdict(SMS, None, None)[0] == "unpooled"
    assert verdict(SMS, None, 0)[0] == "unpooled-idle"


def test_an_unpooled_number_that_is_sending_is_the_urgent_one():
    state, detail = verdict(SMS, None, 4)
    assert state == "unpooled-sending"
    assert "at least 4 message(s)" in detail


def test_pool_membership_beats_traffic():
    # Being in a pool settles it; the traffic count is only there to rank the
    # numbers that are not.
    assert verdict(SMS, SERVICE, 500)[0] == "pooled"


def test_a_service_with_no_friendly_name_falls_back_to_its_sid():
    _state, detail = verdict(SMS, {"sid": "MG9"})
    assert "MG9" in detail


def test_missing_capabilities_object_is_treated_as_not_sms():
    assert verdict({"phone_number": "+15550003333", "sid": "PN3"})[0] == "out-of-scope"
''',
"test_js_file": "twilio-unpooled-number-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './twilio-unpooled-number-audit.mjs';

const SMS = { phone_number: '+15550001111', sid: 'PN1', capabilities: { sms: true, voice: true } };
const VOICE_ONLY = { phone_number: '+15550002222', sid: 'PN2', capabilities: { sms: false, voice: true } };
const SERVICE = { sid: 'MG1', friendly_name: 'transactional' };

test('a number in a pool is not a finding', () => {
  const [state, detail] = verdict(SMS, SERVICE);
  assert.equal(state, 'pooled');
  assert.match(detail, /transactional/);
});

test('an unpooled number names what it is missing', () => {
  const [state, detail] = verdict(SMS);
  assert.equal(state, 'unpooled');
  assert.match(detail, /sticky sender/);
  assert.match(detail, /geomatch/);
});

test('a voice only number is out of scope', () => {
  const [state, detail] = verdict(VOICE_ONLY);
  assert.equal(state, 'out-of-scope');
  assert.match(detail, /capabilities\\.sms is false/);
});

test('unchecked traffic is not the same as no traffic', () => {
  assert.equal(verdict(SMS, null, null)[0], 'unpooled');
  assert.equal(verdict(SMS, null, 0)[0], 'unpooled-idle');
});

test('an unpooled number that is sending is the urgent one', () => {
  const [state, detail] = verdict(SMS, null, 4);
  assert.equal(state, 'unpooled-sending');
  assert.match(detail, /at least 4 message\\(s\\)/);
});

test('pool membership beats traffic', () => {
  assert.equal(verdict(SMS, SERVICE, 500)[0], 'pooled');
});

test('a service with no friendly name falls back to its sid', () => {
  const [, detail] = verdict(SMS, { sid: 'MG9' });
  assert.match(detail, /MG9/);
});

test('missing capabilities object is treated as not sms', () => {
  assert.equal(verdict({ phone_number: '+15550003333', sid: 'PN3' })[0], 'out-of-scope');
});
''',
"faq": [
 ("Nothing is failing. Is this actually a problem?",
  "Nothing is failing today. What you are losing is the layer that decides which sender to use: sticky sender keeping one conversation on one number, geomatch picking a local sender, long code failover, and the A2P campaign that attaches through a pool. Unpooled traffic works and is filtered more, which shows up as deliverability rather than as an error."),
 ("How is this different from a 10DLC number missing from the campaign pool?",
  "Scope and urgency. That note is about US long codes returning 30034 right now because A2P registration attaches through the pool. This one covers every SMS-capable number you own, including non-US numbers and toll-free lines that will never produce a 30034 and are still outside sender selection."),
 ("Does adding the number to a service fix it on its own?",
  "Only half. Sender selection runs when the send names a MessagingServiceSid; code that keeps passing a bare From gets the same behaviour it had before the number joined the pool. The script prints both halves of the repair for that reason."),
 ("Which service should an unpooled number go into?",
  "The one whose traffic it is already carrying, which is why the script offers to count outbound messages per number. A number sending passcodes belongs with the passcode service and its shorter validity period; a number sending campaigns belongs with the campaign one."),
 ("Can a number sit in more than one Messaging Service?",
  "The script does not assume it cannot: it maps pooled SIDs to the service that claimed them and reports the number as pooled once any service holds it. If your account has grown several services over the years, run the audit after each migration, because a number that moved services is the same set difference as a number that never joined one."),
],
"related": [
 ("/twilio/number-missing-from-campaign-sender-pool/", "A 10DLC number outside the pool 30034s"),
 ("/twilio/messaging-service-empty-sender-pool/", "An empty sender pool and 21704 on every send"),
 ("/twilio/idle-phone-numbers-billed/", "Numbers with no traffic that still bill monthly"),
],
"citations": [CITE_SERVICE_PN, CITE_PN, CITE_SERVICES_GUIDE, CITE_KEYS],
},


{
"slug": "no-sender-matching-destination",
"title": "Error 21703: the pool has senders but none reach the To",
"description": "Sender selection needs a pool member matching the destination country and message type. A pool with no US number fails every US send with 21703.",
"h1": "error 21703: the pool has senders but none reach the To",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 21703", "no phone number available to send",
             "twilio messaging service sender selection", "twilio 21703 mms",
             "twilio pool wrong country"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Messaging Service has senders in it. Sends to the UK go out all day. Every send to a US number comes back <code>21703</code>, &ldquo;The Messaging Service does not have a phone number available to send a message&rdquo;, which sounds like the pool is empty and is not what it means. The pool is fine. It has nothing in it that can reach <em>that</em> destination.",
"short_answer": """<p>Read the pool as three lists: <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> (each entry carries <code>country_code</code> and a <code>capabilities</code> list of <code>SMS</code>, <code>MMS</code>, <code>voice</code>), plus <code>/ShortCodes</code> and <code>/AlphaSenders</code>. Then resolve the destination's country with <code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}</code> and check the pool against it.</p>
<p>Two shapes produce <code>21703</code>. Nothing in the pool matches the destination country &mdash; and for US or Canadian destinations an alphanumeric sender ID does not count, because it cannot deliver there. Or the country is covered but the message carries <code>MediaUrl</code> and no matching sender lists <code>MMS</code>.</p>""",
"problem": """<p><code>21703</code> is read as &ldquo;empty pool&rdquo; by almost everyone who meets it, because the message says the service does not have a phone number available. It does have phone numbers. Sender selection ran, looked for one that supports this destination and this message type, and found none, which is a different sentence with a different repair. The service that fails is often the one that has been working for a year, right up to the first customer in a new country.</p>
<p>It also fails per destination rather than per service, so nothing about it is reproducible from the outside. Half the traffic goes out. The half that does not is defined by a property of the recipient, not of your code, so the bug report says &ldquo;messages to the US are broken&rdquo; and the service dashboard says the service is healthy. Both are accurate.</p>
<p>The MMS variant is worse, because the same recipient works and fails depending on whether the message has an attachment. A pool with SMS-only US long codes sends the text version of a notification perfectly and rejects the one with a receipt image, and the difference lives in a capabilities list nobody has read.</p>""",
"why": """<p><strong>Sender selection matches on country and on message type together.</strong> A pool member has to support the destination and the thing you are sending. A US destination needs a US or Canadian long code, toll-free number or short code; a message with <code>MediaUrl</code> needs a sender that lists <code>MMS</code>. Satisfying one and not the other still returns <code>21703</code>.</p>
<p><strong>Alphanumeric sender IDs cannot reach the US or Canada.</strong> They are legitimate senders, they appear in the pool, and they make a service look populated. For a US destination they are not a candidate at all, which is exactly how a service with three alpha senders and no US number produces this error while looking well configured.</p>
<p><strong>The failure is at request time, so there is often no Message row.</strong> <code>21703</code> is returned synchronously and no Message resource is created, which means paging <code>Messages.json</code> will not find it. The read-only evidence lives in <code>GET https://monitor.twilio.com/v1/Alerts</code> instead, and the audit itself has to be predictive: read the pool, name the destinations you care about, and check coverage before anyone sends.</p>
<p><strong>Capabilities are spelled differently on either side of the join.</strong> The pool entry carries a list like <code>["SMS", "MMS"]</code>; the account's <code>IncomingPhoneNumbers</code> carries an object with lowercase keys. Comparing them naively is how an MMS-capable pool gets reported as having no MMS sender.</p>
<p><strong>A brand new sender can behave like a missing one.</strong> A number added minutes ago may still be pending on the carrier side, so the pool looks correct and selection still fails. That is a different note and a different action, which is to wait.</p>""",
"steps": [
 {"h": "Read all three sender lists for the service",
  "body": """<p><code>/PhoneNumbers</code>, <code>/ShortCodes</code> and <code>/AlphaSenders</code> under <code>https://messaging.twilio.com/v1/Services/{ServiceSid}</code>. A pool whose only sender is a short code has an empty <code>phone_numbers[]</code> and sends perfectly well, so reading one list and concluding from it produces a confident wrong answer.</p>"""},
 {"h": "Resolve the destination country rather than guessing from the prefix",
  "body": """<p><code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}</code> returns <code>country_code</code>. Prefix arithmetic works until it meets the North American numbering plan, where <code>+1</code> covers the US, Canada and a list of Caribbean countries that do not share sender rules.</p>"""},
 {"h": "Treat US and Canadian destinations by their own rule",
  "body": """<p>For a <code>US</code> or <code>CA</code> destination the pool needs a US or Canadian phone number or short code. Alphanumeric sender IDs cannot deliver there, so a pool of alpha senders is uncovered no matter how many it holds.</p>"""},
 {"h": "Check the message type as well as the country",
  "body": """<p>If the traffic carries <code>MediaUrl</code>, the matching sender has to list <code>MMS</code>. Compare capabilities case-insensitively: the pool spells them <code>SMS</code> and <code>MMS</code>, the account API spells the same facts as lowercase keys on an object.</p>"""},
 {"h": "Confirm the live failures in Alerts, not in the Messages list",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=...</code> and filter for <code>error_code</code> <code>21703</code> yourself; the Messages list has no error filter and, for a request-time rejection, usually has no row at all. Alerts are retained thirty days, which bounds every trend you can draw from them.</p>"""},
 {"h": "Add a sender that matches, then re-check the destinations you actually serve",
  "body": """<p><code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> with the <code>PhoneNumberSid</code> of a number in the destination country carrying the capability you need. For US MMS that means an MMS-capable US long code specifically. Re-run the audit with the country list your product actually sells into.</p>"""},
],
"verify": """<p>Re-run the script with the destinations you care about. Every service and destination pair should report <code>covered</code>.</p>
<pre><code class="language-bash">python3 twilio_sender_coverage_audit.py --to +12025550123 --to +447700900123 --media
# 2 service(s) x 2 destination(s), 0 uncovered</code></pre>""",
"code_intro": "One GET per sender list, one Lookup per destination, and nothing else &mdash; an API Key with read access is the whole credential. The coverage rule is pure and takes a pool and one destination, because the interesting content of this note is a matching rule with two dimensions, and a rule with two dimensions is worth reading next to the cases that pin it.",
"py_file": "twilio_sender_coverage_audit.py",
"py": '''"""Report Messaging Services whose sender pool cannot reach a destination.

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
log = logging.getLogger("twilio_sender_coverage_audit")

MESSAGING = "https://messaging.twilio.com/v1"
LOOKUPS = "https://lookups.twilio.com/v2"

# Alphanumeric sender IDs are not candidates for these destinations, so a pool
# holding nothing else is uncovered however full it looks.
ALPHA_EXCLUDED = ("US", "CA")


def has_capability(entry, name):
    """Case-insensitive capability test that survives both spellings.

    The Messaging Service pool returns a list like ["SMS", "MMS", "voice"]. The
    account API returns an object with lowercase keys for the same facts.
    Comparing raw strings across the two is how an MMS-capable pool gets
    reported as having no MMS sender.
    """
    caps = entry.get("capabilities") or []
    if isinstance(caps, dict):
        return bool(caps.get(name.lower()))
    return name.lower() in [str(c).lower() for c in caps]


def coverage(pool, destination):
    """Decide whether one sender pool can reach one destination.

    `pool` is {"phone_numbers": [...], "short_codes": [...], "alpha_senders": [...]}
    as returned by the three subresources. `destination` is
    {"country_code": "US", "needs_mms": bool}.

    Pure, so the matching rule can be tested without a network.
    Returns (state, detail).
    """
    country = str(destination.get("country_code") or "").upper()
    needs_mms = bool(destination.get("needs_mms"))
    numbers = pool.get("phone_numbers") or []
    codes = pool.get("short_codes") or []
    alphas = pool.get("alpha_senders") or []

    if not (numbers or codes or alphas):
        return ("no-senders",
                "the pool holds no senders at all, which is 21704 on every send "
                "rather than 21703 on this destination.")
    if not country:
        return ("unresolved",
                "the destination country was not resolved, so coverage cannot "
                "be decided. Read country_code from Lookup v2 first.")

    local = [n for n in numbers
             if str(n.get("country_code") or "").upper() == country]
    local_codes = [c for c in codes
                   if str(c.get("country_code") or "").upper() == country]

    if not (local or local_codes):
        if country in ALPHA_EXCLUDED:
            return ("unreachable",
                    "no %s number or short code in the pool. The %d alphanumeric "
                    "sender(s) do not count: they cannot deliver to %s."
                    % (country, len(alphas), country))
        if alphas:
            return ("alpha-only",
                    "no %s number in the pool, only %d alphanumeric sender(s). "
                    "They are one way and are not accepted everywhere, so this "
                    "is deliverable in some countries and 21703 in others."
                    % (country, len(alphas)))
        return ("no-local-sender",
                "no %s sender in the pool. Selection may still pick a foreign "
                "long code, and this is the shape that returns 21703 when it "
                "does not." % country)

    if needs_mms and not any(has_capability(n, "MMS") for n in local):
        return ("no-mms",
                "%d %s sender(s) in the pool and not one of them lists MMS, so "
                "any message carrying MediaUrl is 21703 while the text only "
                "version of it sends." % (len(local), country))

    kinds = []
    if local:
        kinds.append("%d number(s)" % len(local))
    if local_codes:
        kinds.append("%d short code(s)" % len(local_codes))
    return ("covered", "%s in %s%s"
            % (", ".join(kinds), country, ", MMS capable" if needs_mms else ""))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_services(session, limit):
    url = "%s/Services" % MESSAGING
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("services", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def read_pool(session, service_sid):
    """All three sender lists. Reading one and concluding from it is how a
    short code only service gets reported as broken."""
    pool = {}
    for path, key in (("PhoneNumbers", "phone_numbers"),
                      ("ShortCodes", "short_codes"),
                      ("AlphaSenders", "alpha_senders")):
        page = get(session, "%s/Services/%s/%s" % (MESSAGING, service_sid, path),
                   PageSize=100)
        pool[key] = page.get(key, [])
    return pool


def resolve(session, e164):
    """Destination country from Lookup v2. Prefix arithmetic breaks on +1,
    which covers the US, Canada and several Caribbean countries."""
    page = get(session, "%s/PhoneNumbers/%s" % (LOOKUPS, e164))
    return str(page.get("country_code") or "").upper()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--to", action="append", default=[],
                    help="destination in E.164, repeatable")
    ap.add_argument("--media", action="store_true",
                    help="the traffic carries MediaUrl, so a sender must do MMS")
    ap.add_argument("--service", action="append", default=[],
                    help="limit to these Messaging Service SIDs")
    args = ap.parse_args()

    if not args.to:
        log.error("give at least one destination with --to +15551234567")
        return 2

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    destinations = []
    for e164 in args.to:
        country = resolve(session, e164)
        destinations.append({"phone_number": e164, "country_code": country,
                             "needs_mms": args.media})
        log.info("destination %s resolves to %s", e164, country or "?")

    services = list_services(session, 200)
    if args.service:
        services = [s for s in services if s.get("sid") in set(args.service)]

    bad = 0
    for svc in services:
        pool = read_pool(session, svc.get("sid"))
        for dest in destinations:
            state, detail = coverage(pool, dest)
            line = "%-16s %s -> %s  %s" % (state, svc.get("sid"),
                                           dest["phone_number"], detail)
            if state == "covered":
                log.info(line)
                continue
            bad += 1
            log.warning(line)
            log.warning("  repair: POST %s/Services/%s/PhoneNumbers "
                        "PhoneNumberSid=PN... for a %s number%s",
                        MESSAGING, svc.get("sid"), dest["country_code"] or "?",
                        " that is MMS capable" if dest["needs_mms"] else "")

    log.info("%d service(s) x %d destination(s), %d uncovered",
             len(services), len(destinations), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sender-coverage-audit.mjs",
"js": '''/**
 * Report Messaging Services whose sender pool cannot reach a destination.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MESSAGING = 'https://messaging.twilio.com/v1';
const LOOKUPS = 'https://lookups.twilio.com/v2';

// Alphanumeric sender IDs are not candidates for these destinations, so a pool
// holding nothing else is uncovered however full it looks.
const ALPHA_EXCLUDED = ['US', 'CA'];

/**
 * Case-insensitive capability test that survives both spellings: the pool
 * returns a list like ['SMS', 'MMS'], the account API returns an object with
 * lowercase keys for the same facts.
 */
export function hasCapability(entry, name) {
  const caps = entry.capabilities ?? [];
  if (!Array.isArray(caps)) return Boolean(caps[name.toLowerCase()]);
  return caps.map((c) => String(c).toLowerCase()).includes(name.toLowerCase());
}

/**
 * Decide whether one sender pool can reach one destination. Pure, so the
 * matching rule can be tested without a network. Returns [state, detail].
 */
export function coverage(pool, destination) {
  const country = String(destination.country_code ?? '').toUpperCase();
  const needsMms = Boolean(destination.needs_mms);
  const numbers = pool.phone_numbers ?? [];
  const codes = pool.short_codes ?? [];
  const alphas = pool.alpha_senders ?? [];

  if (!numbers.length && !codes.length && !alphas.length) {
    return ['no-senders',
      'the pool holds no senders at all, which is 21704 on every send rather ' +
      'than 21703 on this destination.'];
  }
  if (!country) {
    return ['unresolved',
      'the destination country was not resolved, so coverage cannot be ' +
      'decided. Read country_code from Lookup v2 first.'];
  }

  const local = numbers.filter(
    (n) => String(n.country_code ?? '').toUpperCase() === country);
  const localCodes = codes.filter(
    (c) => String(c.country_code ?? '').toUpperCase() === country);

  if (!local.length && !localCodes.length) {
    if (ALPHA_EXCLUDED.includes(country)) {
      return ['unreachable',
        `no ${country} number or short code in the pool. The ${alphas.length} ` +
        `alphanumeric sender(s) do not count: they cannot deliver to ${country}.`];
    }
    if (alphas.length) {
      return ['alpha-only',
        `no ${country} number in the pool, only ${alphas.length} alphanumeric ` +
        'sender(s). They are one way and are not accepted everywhere, so this ' +
        'is deliverable in some countries and 21703 in others.'];
    }
    return ['no-local-sender',
      `no ${country} sender in the pool. Selection may still pick a foreign ` +
      'long code, and this is the shape that returns 21703 when it does not.'];
  }

  if (needsMms && !local.some((n) => hasCapability(n, 'MMS'))) {
    return ['no-mms',
      `${local.length} ${country} sender(s) in the pool and not one of them ` +
      'lists MMS, so any message carrying MediaUrl is 21703 while the text ' +
      'only version of it sends.'];
  }

  const kinds = [];
  if (local.length) kinds.push(`${local.length} number(s)`);
  if (localCodes.length) kinds.push(`${localCodes.length} short code(s)`);
  return ['covered',
    `${kinds.join(', ')} in ${country}${needsMms ? ', MMS capable' : ''}`];
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

export async function listServices(auth, limit = 200) {
  let url = `${MESSAGING}/Services`;
  let params = { PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.services ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

async function readPool(auth, serviceSid) {
  const pool = {};
  for (const [path, key] of [['PhoneNumbers', 'phone_numbers'],
                             ['ShortCodes', 'short_codes'],
                             ['AlphaSenders', 'alpha_senders']]) {
    const page = await get(auth, `${MESSAGING}/Services/${serviceSid}/${path}`,
                           { PageSize: 100 });
    pool[key] = page[key] ?? [];
  }
  return pool;
}

async function resolve(auth, e164) {
  const page = await get(auth, `${LOOKUPS}/PhoneNumbers/${e164}`);
  return String(page.country_code ?? '').toUpperCase();
}

function repeatedFlag(name) {
  const out = [];
  process.argv.forEach((a, i) => { if (a === name) out.push(process.argv[i + 1]); });
  return out.filter(Boolean);
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  const tos = repeatedFlag('--to');
  if (!tos.length) {
    console.error('give at least one destination with --to +15551234567');
    process.exitCode = 2;
    return;
  }
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);
  const needsMms = process.argv.includes('--media');
  const only = new Set(repeatedFlag('--service'));

  const destinations = [];
  for (const e164 of tos) {
    const country = await resolve(auth, e164);
    destinations.push({ phone_number: e164, country_code: country, needs_mms: needsMms });
    console.log(`destination ${e164} resolves to ${country || '?'}`);
  }

  let services = await listServices(auth);
  if (only.size) services = services.filter((s) => only.has(s.sid));

  let bad = 0;
  for (const svc of services) {
    const pool = await readPool(auth, svc.sid);
    for (const dest of destinations) {
      const [state, detail] = coverage(pool, dest);
      const line = `${state.padEnd(16)} ${svc.sid} -> ${dest.phone_number}  ${detail}`;
      if (state === 'covered') { console.log(line); continue; }
      bad += 1;
      console.warn(line);
      console.warn(`  repair: POST ${MESSAGING}/Services/${svc.sid}/PhoneNumbers ` +
                   `PhoneNumberSid=PN... for a ${dest.country_code || '?'} number` +
                   `${dest.needs_mms ? ' that is MMS capable' : ''}`);
    }
  }

  console.log(`${services.length} service(s) x ${destinations.length} ` +
              `destination(s), ${bad} uncovered`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones where the pool looks full. Three alphanumeric senders and a US destination is uncovered, not covered, because alpha senders cannot deliver to the US or Canada. A US long code without <code>MMS</code> covers the text and fails the picture. And an empty pool is deliberately its own state, because that is <code>21704</code> and a different note.",
"test_py_file": "test_twilio_sender_coverage_audit.py",
"test_py": '''from twilio_sender_coverage_audit import coverage, has_capability

US_SMS = {"phone_number": "+12025550100", "country_code": "US", "capabilities": ["SMS"]}
US_MMS = {"phone_number": "+12025550101", "country_code": "US", "capabilities": ["SMS", "MMS"]}
GB_SMS = {"phone_number": "+447700900100", "country_code": "GB", "capabilities": ["SMS"]}
ALPHA = {"sid": "AS1", "alpha_sender": "ACME"}

US = {"country_code": "US", "needs_mms": False}
US_MEDIA = {"country_code": "US", "needs_mms": True}
GB = {"country_code": "GB", "needs_mms": False}


def test_a_us_number_covers_a_us_destination():
    state, detail = coverage({"phone_numbers": [US_SMS]}, US)
    assert state == "covered"
    assert "US" in detail


def test_alpha_senders_do_not_cover_the_us():
    # The whole note: the pool is populated and the destination is unreachable.
    state, detail = coverage({"alpha_senders": [ALPHA, ALPHA, ALPHA]}, US)
    assert state == "unreachable"
    assert "cannot deliver to US" in detail


def test_a_uk_only_pool_cannot_reach_the_us():
    assert coverage({"phone_numbers": [GB_SMS]}, US)[0] == "unreachable"


def test_media_needs_an_mms_capable_sender_in_that_country():
    state, detail = coverage({"phone_numbers": [US_SMS]}, US_MEDIA)
    assert state == "no-mms"
    assert "MediaUrl" in detail
    assert coverage({"phone_numbers": [US_SMS, US_MMS]}, US_MEDIA)[0] == "covered"


def test_an_empty_pool_is_21704_and_says_so():
    state, detail = coverage({}, US)
    assert state == "no-senders"
    assert "21704" in detail


def test_a_short_code_in_the_destination_country_counts():
    pool = {"short_codes": [{"short_code": "12345", "country_code": "US"}]}
    assert coverage(pool, US)[0] == "covered"


def test_a_non_north_american_gap_is_not_reported_as_unreachable():
    # Selection may still pick a foreign long code, so this is a softer state.
    assert coverage({"phone_numbers": [US_SMS]}, GB)[0] == "no-local-sender"
    assert coverage({"phone_numbers": [US_SMS], "alpha_senders": [ALPHA]}, GB)[0] == "alpha-only"


def test_an_unresolved_country_is_never_guessed_at():
    assert coverage({"phone_numbers": [US_SMS]}, {"country_code": ""})[0] == "unresolved"


def test_capabilities_match_across_both_spellings():
    assert has_capability({"capabilities": ["SMS", "MMS"]}, "mms")
    assert has_capability({"capabilities": {"sms": True, "mms": True}}, "MMS")
    assert not has_capability({"capabilities": ["SMS"]}, "MMS")
''',
"test_js_file": "twilio-sender-coverage-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { coverage, hasCapability } from './twilio-sender-coverage-audit.mjs';

const US_SMS = { phone_number: '+12025550100', country_code: 'US', capabilities: ['SMS'] };
const US_MMS = { phone_number: '+12025550101', country_code: 'US', capabilities: ['SMS', 'MMS'] };
const GB_SMS = { phone_number: '+447700900100', country_code: 'GB', capabilities: ['SMS'] };
const ALPHA = { sid: 'AS1', alpha_sender: 'ACME' };

const US = { country_code: 'US', needs_mms: false };
const US_MEDIA = { country_code: 'US', needs_mms: true };
const GB = { country_code: 'GB', needs_mms: false };

test('a us number covers a us destination', () => {
  const [state, detail] = coverage({ phone_numbers: [US_SMS] }, US);
  assert.equal(state, 'covered');
  assert.match(detail, /US/);
});

test('alpha senders do not cover the us', () => {
  const [state, detail] = coverage({ alpha_senders: [ALPHA, ALPHA, ALPHA] }, US);
  assert.equal(state, 'unreachable');
  assert.match(detail, /cannot deliver to US/);
});

test('a uk only pool cannot reach the us', () => {
  assert.equal(coverage({ phone_numbers: [GB_SMS] }, US)[0], 'unreachable');
});

test('media needs an mms capable sender in that country', () => {
  const [state, detail] = coverage({ phone_numbers: [US_SMS] }, US_MEDIA);
  assert.equal(state, 'no-mms');
  assert.match(detail, /MediaUrl/);
  assert.equal(coverage({ phone_numbers: [US_SMS, US_MMS] }, US_MEDIA)[0], 'covered');
});

test('an empty pool is 21704 and says so', () => {
  const [state, detail] = coverage({}, US);
  assert.equal(state, 'no-senders');
  assert.match(detail, /21704/);
});

test('a short code in the destination country counts', () => {
  const pool = { short_codes: [{ short_code: '12345', country_code: 'US' }] };
  assert.equal(coverage(pool, US)[0], 'covered');
});

test('a non north american gap is not reported as unreachable', () => {
  assert.equal(coverage({ phone_numbers: [US_SMS] }, GB)[0], 'no-local-sender');
  assert.equal(
    coverage({ phone_numbers: [US_SMS], alpha_senders: [ALPHA] }, GB)[0], 'alpha-only');
});

test('an unresolved country is never guessed at', () => {
  assert.equal(coverage({ phone_numbers: [US_SMS] }, { country_code: '' })[0], 'unresolved');
});

test('capabilities match across both spellings', () => {
  assert.ok(hasCapability({ capabilities: ['SMS', 'MMS'] }, 'mms'));
  assert.ok(hasCapability({ capabilities: { sms: true, mms: true } }, 'MMS'));
  assert.ok(!hasCapability({ capabilities: ['SMS'] }, 'MMS'));
});
''',
"faq": [
 ("What is the difference between 21703 and 21704?",
  "21704 means the pool has no senders at all, so every send through that service fails. 21703 means the pool has senders and none of them can serve this particular destination and message type, so the same service sends fine to other countries. Different code, different repair, and the script keeps an empty pool as its own state for that reason."),
 ("Why do alphanumeric sender IDs not count for a US destination?",
  "They cannot deliver to the US or Canada, so sender selection never considers one for those destinations. That is what makes this failure so convincing: the pool is populated, the console shows senders, and for a US recipient there is nothing eligible in it."),
 ("Why is a message with an image rejected when the same text sends?",
  "MMS is a per-sender capability. If no sender in the destination country lists MMS, a send carrying MediaUrl has no eligible sender and returns 21703 while the text-only version of the same message goes out normally."),
 ("Why can I not find the 21703s in the Messages list?",
  "Because the rejection happens at request time, before a Message resource is created, and the Messages list has no error code filter in any case. The read-only evidence is in the Alerts API, filtered client-side on error_code, and alerts are retained for thirty days."),
 ("I added the right number and it still fails. What now?",
  "A sender added minutes ago can still be pending on the carrier side, which looks identical to a missing sender from the outside. Check when it was added before changing anything else; if the pool matches the destination and the country rule, waiting is the correct action."),
],
"related": [
 ("/twilio/messaging-service-empty-sender-pool/", "An empty pool and 21704 on every send"),
 ("/twilio/from-number-not-sms-capable/", "A voice-only From and 21606"),
 ("/twilio/shortcode-cross-border-sender-mismatch/", "Short codes that do not cross borders"),
],
"citations": [CITE_21703, CITE_SERVICE_PN, CITE_LOOKUP, CITE_21704],
},


{
"slug": "multiple-tollfree-in-one-pool",
"title": "Two toll-free numbers in one sender pool get both blocked",
"description": "Carriers read several toll-free senders in one Messaging Service as snowshoeing and block them. Twilio's guidance is one toll-free number per service.",
"h1": "two toll-free numbers in one sender pool get both blocked",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio multiple toll-free numbers messaging service",
             "twilio toll-free snowshoeing", "twilio error 30032 pool",
             "one toll-free per messaging service", "twilio toll-free blocked"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Two toll-free numbers were put in one Messaging Service so the send would go faster. Both were verified. For a few weeks it did go faster. Then toll-free traffic through that service started failing with <code>30032</code> &mdash; across the whole pool, including the number that had been verified and sending since last year.",
"short_answer": """<p>Read each pool with <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers?PageSize=1000</code> and count the entries whose <code>phone_number</code> is a North American toll-free number: the <code>+1</code> area codes <code>800</code>, <code>833</code>, <code>844</code>, <code>855</code>, <code>866</code>, <code>877</code> and <code>888</code>. More than one in a single service is the finding.</p>
<p>Twilio's guidance is one toll-free number per Messaging Service. Carriers treat several toll-free senders sharing a service as snowshoeing &mdash; volume spread across senders to dodge filtering &mdash; and block the numbers, which is why the damage lands on the whole pool rather than on the number you added last.</p>""",
"problem": """<p>The change that causes this looks like a capacity fix and is applied by someone being sensible. Toll-free throughput is finite, a second verified toll-free number is sitting on the account, and adding it to the same service is one API call. Nothing warns you. The pool accepts it, sends start alternating between the two senders, and the service does exactly what a sender pool is advertised to do.</p>
<p>The judgement that follows is not Twilio's, which is the part that makes it hard to debug. Carriers look at one messaging service pushing volume through multiple toll-free senders and see the standard shape of a spam operation spreading traffic to stay under per-sender thresholds. The response is to block, and the block is not scoped to the new number. The number that had been running clean for a year goes down with it, so the timeline in your head &mdash; &ldquo;we added a number and the old one broke&rdquo; &mdash; reads as unrelated events.</p>
<p>Then the reflex fix makes it worse. The numbers look unverified, so somebody re-submits verification, waits, and re-submits again, while the pool is still shaped the way that caused the block. Nothing in the verification record explains that the problem is how many toll-free senders share the service.</p>""",
"why": """<p><strong>The rule is about the pool, not about any one number.</strong> Each toll-free number can be individually verified and completely legitimate. What the carrier reacts to is the arrangement: several toll-free senders behind a single service, taking turns. No property of any single number describes that, which is why no per-number check finds it.</p>
<p><strong>Adding a sender is a success.</strong> The API returns a created sender, the console lists it, and there is no warning at the moment the second toll-free number joins. The consequence arrives days or weeks later from a third party, with a delay long enough that nobody connects the two.</p>
<p><strong>30032 says the number is unverified, which is not what you are looking at.</strong> The same code covers a genuinely unverified toll-free number, and that is a different note with a different fix. Reading the code literally sends you to the verification record, where everything is in order, rather than to the pool.</p>
<p><strong>The blast radius is the service.</strong> A block that lands on the pool takes out the sender your production traffic has used for a year, not just the one that was added. That asymmetry is why this is worth auditing before the second number goes in rather than after.</p>
<p><strong>Nothing puts the numbers back together for you.</strong> The repair is to split them across services, one toll-free number each, which also means the traffic that was pointed at one service has to be split. That is a change to your application, not just to a pool, and it is easier to plan before a carrier forces the schedule.</p>""",
"steps": [
 {"h": "List the services, then read each sender pool",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code>, paging on <code>meta.next_page_url</code>, then <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> per service. The finding is a property of one pool, so the count has to be per service and never per account.</p>"""},
 {"h": "Identify toll-free numbers by the numbering plan, not by a substring",
  "body": """<p>Strip everything that is not a digit, require eleven digits starting with <code>1</code>, and match the area code against <code>800</code>, <code>833</code>, <code>844</code>, <code>855</code>, <code>866</code>, <code>877</code>, <code>888</code>. A naive <code>startswith("+1800")</code> check misses the other six, and a bare <code>"800" in number</code> check matches a UK freephone number and a subscriber number that happens to contain 800.</p>"""},
 {"h": "Count long codes in the same pool as context, not as a finding",
  "body": """<p>A pool with one toll-free number and a set of long codes is a normal, working arrangement; it is worth printing the shape so the reader can see what they have, but the thing being flagged is strictly more than one toll-free sender in one service.</p>"""},
 {"h": "Corroborate with the 30032s, grouped by sender",
  "body": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and count <code>error_code</code> <code>30032</code> per <code>from</code> yourself: the Messages list has no error filter, so the filtering is client side. Failures on both toll-free numbers in a shared pool is the signature; failures on one number only usually means that number really is unverified.</p>"""},
 {"h": "Split them, one toll-free number per service",
  "body": """<p>The repair is <code>DELETE https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers/{PNSid}</code> for the extras and a service of its own for each toll-free number, with the sending code updated to name the right <code>MessagingServiceSid</code> for each stream of traffic. Then leave the audit on a schedule, because the next capacity problem invites exactly the same fix.</p>"""},
],
"verify": """<p>Re-run the script. Every service should hold at most one toll-free sender.</p>
<pre><code class="language-bash">python3 twilio_tollfree_pool_audit.py
# 6 service(s), 0 holding more than one toll-free sender</code></pre>""",
"code_intro": "One GET for the services, one per service for its pool, and with <code>--check-errors</code> one paginated pass over the Messages list &mdash; all of it on an API Key with read access. Two pure functions carry the note: what counts as a North American toll-free number, and what counts as too many of them in one pool. The first is where the false positives would come from, so it is the one with the most tests.",
"py_file": "twilio_tollfree_pool_audit.py",
"py": '''"""Report Messaging Services holding more than one toll-free sender.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import collections
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_tollfree_pool_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

# North American toll-free area codes. Matching the numbering plan rather than a
# prefix string keeps a UK freephone number and a subscriber number containing
# 800 out of the report.
TOLL_FREE_AREA_CODES = frozenset({"800", "833", "844", "855", "866", "877", "888"})

TOLL_FREE_ERROR = "30032"


def is_toll_free(phone_number):
    """True for a North American toll-free number in any formatting.

    Pure. Eleven digits beginning with the country code 1, and an area code from
    the toll-free set: that is the rule, and it is deliberately not a substring
    test on the E.164 string.
    """
    digits = "".join(c for c in str(phone_number or "") if c.isdigit())
    if len(digits) != 11 or not digits.startswith("1"):
        return False
    return digits[1:4] in TOLL_FREE_AREA_CODES


def verdict(entries):
    """Classify one sender pool by how many toll-free numbers share it.

    `entries` is the pool's phone_numbers list. Pure, so the rule is testable
    without a network. Returns (state, detail).
    """
    entries = entries or []
    if not entries:
        return ("empty", "no phone numbers in this pool at all, which is 21704 "
                         "on every send and a different note.")

    toll_free = [str(e.get("phone_number") or "")
                 for e in entries if is_toll_free(e.get("phone_number"))]
    others = len(entries) - len(toll_free)

    if not toll_free:
        return ("no-toll-free",
                "%d sender(s), none of them toll-free." % len(entries))
    if len(toll_free) == 1:
        return ("single-toll-free",
                "one toll-free sender (%s) alongside %d other sender(s), which "
                "is the shape Twilio's guidance asks for."
                % (toll_free[0], others))
    return ("multiple-toll-free",
            "%d toll-free senders share this pool: %s. Carriers read that as "
            "snowshoeing and block the numbers, including ones verified long "
            "before the extras were added."
            % (len(toll_free), ", ".join(toll_free)))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_services(session, limit):
    url = "%s/Services" % MESSAGING
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("services", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def read_pool(session, service_sid):
    url = "%s/Services/%s/PhoneNumbers" % (MESSAGING, service_sid)
    params = {"PageSize": 100}
    out = []
    while url:
        page = get(session, url, **params)
        out.extend(page.get("phone_numbers", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out


def count_blocks(session, account, days, max_messages):
    """Count 30032 per sender. The Messages list has no error code filter and no
    status filter, so the window is paged and filtered here."""
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"DateSent>": since, "PageSize": 1000}
    seen = 0
    tally = collections.Counter()
    while url and seen < max_messages:
        page = get(session, url, **params)
        rows = page.get("messages", [])
        seen += len(rows)
        for m in rows:
            if str(m.get("error_code") or "") == TOLL_FREE_ERROR:
                tally[m.get("from")] += 1
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return tally


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-services", type=int, default=200,
                    help="stop paging after this many Messaging Services")
    ap.add_argument("--check-errors", action="store_true",
                    help="page the Messages list and count 30032 per sender")
    ap.add_argument("--days", type=int, default=7,
                    help="window in days for --check-errors")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging the Messages list after this many rows")
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

    blocks = count_blocks(session, account, args.days, args.max_messages) if args.check_errors else {}

    services = list_services(session, args.max_services)
    bad = 0
    for svc in services:
        entries = read_pool(session, svc.get("sid"))
        state, detail = verdict(entries)
        label = svc.get("friendly_name") or svc.get("sid")
        line = "%-19s %s  %s" % (state, label, detail)
        if state != "multiple-toll-free":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for e in entries:
            number = e.get("phone_number")
            if is_toll_free(number) and blocks.get(number):
                log.warning("  %s has %d message(s) failing %s in the last %d day(s)",
                            number, blocks[number], TOLL_FREE_ERROR, args.days)
        log.warning("  repair: give each toll-free number its own Messaging "
                    "Service, then DELETE %s/Services/%s/PhoneNumbers/{PNSid} "
                    "for the extras and point each traffic stream at the right "
                    "MessagingServiceSid.", MESSAGING, svc.get("sid"))

    log.info("%d service(s), %d holding more than one toll-free sender",
             len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-tollfree-pool-audit.mjs",
"js": '''/**
 * Report Messaging Services holding more than one toll-free sender.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

// North American toll-free area codes. Matching the numbering plan rather than a
// prefix string keeps a UK freephone number and a subscriber number containing
// 800 out of the report.
const TOLL_FREE_AREA_CODES = new Set(['800', '833', '844', '855', '866', '877', '888']);

const TOLL_FREE_ERROR = '30032';

/**
 * True for a North American toll-free number in any formatting. Pure: eleven
 * digits beginning with country code 1, and an area code from the toll-free set.
 */
export function isTollFree(phoneNumber) {
  const digits = String(phoneNumber ?? '').replace(/\\D/g, '');
  if (digits.length !== 11 || !digits.startsWith('1')) return false;
  return TOLL_FREE_AREA_CODES.has(digits.slice(1, 4));
}

/**
 * Classify one sender pool by how many toll-free numbers share it. Pure, so the
 * rule is testable without a network. Returns [state, detail].
 */
export function verdict(entries) {
  const pool = entries ?? [];
  if (!pool.length) {
    return ['empty',
      'no phone numbers in this pool at all, which is 21704 on every send and ' +
      'a different note.'];
  }

  const tollFree = pool.filter((e) => isTollFree(e.phone_number))
                       .map((e) => String(e.phone_number ?? ''));
  const others = pool.length - tollFree.length;

  if (!tollFree.length) {
    return ['no-toll-free', `${pool.length} sender(s), none of them toll-free.`];
  }
  if (tollFree.length === 1) {
    return ['single-toll-free',
      `one toll-free sender (${tollFree[0]}) alongside ${others} other ` +
      "sender(s), which is the shape Twilio's guidance asks for."];
  }
  return ['multiple-toll-free',
    `${tollFree.length} toll-free senders share this pool: ${tollFree.join(', ')}. ` +
    'Carriers read that as snowshoeing and block the numbers, including ones ' +
    'verified long before the extras were added.'];
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

export async function listServices(auth, limit = 200) {
  let url = `${MESSAGING}/Services`;
  let params = { PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.services ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

async function readPool(auth, serviceSid) {
  let url = `${MESSAGING}/Services/${serviceSid}/PhoneNumbers`;
  let params = { PageSize: 100 };
  const out = [];
  while (url) {
    const page = await get(auth, url, params);
    out.push(...(page.phone_numbers ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out;
}

/** Count 30032 per sender. The Messages list has no error code filter. */
async function countBlocks(auth, account, days, maxMessages) {
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  let url = `${BASE}/Accounts/${account}/Messages.json`;
  let params = { 'DateSent>': since, PageSize: 1000 };
  const tally = new Map();
  let seen = 0;
  while (url && seen < maxMessages) {
    const page = await get(auth, url, params);
    const rows = page.messages ?? [];
    seen += rows.length;
    for (const m of rows) {
      if (String(m.error_code ?? '') === TOLL_FREE_ERROR) {
        tally.set(m.from, (tally.get(m.from) ?? 0) + 1);
      }
    }
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return tally;
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
  const days = flagValue('--days', 7);
  const blocks = process.argv.includes('--check-errors')
    ? await countBlocks(auth, account, days, flagValue('--max-messages', 20000))
    : new Map();

  const services = await listServices(auth);
  let bad = 0;
  for (const svc of services) {
    const entries = await readPool(auth, svc.sid);
    const [state, detail] = verdict(entries);
    const label = svc.friendly_name ?? svc.sid;
    const line = `${state.padEnd(19)} ${label}  ${detail}`;
    if (state !== 'multiple-toll-free') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    for (const e of entries) {
      if (isTollFree(e.phone_number) && blocks.get(e.phone_number)) {
        console.warn(`  ${e.phone_number} has ${blocks.get(e.phone_number)} ` +
                     `message(s) failing ${TOLL_FREE_ERROR} in the last ${days} day(s)`);
      }
    }
    console.warn('  repair: give each toll-free number its own Messaging Service, ' +
                 `then DELETE ${MESSAGING}/Services/${svc.sid}/PhoneNumbers/{PNSid} ` +
                 'for the extras and point each traffic stream at the right ' +
                 'MessagingServiceSid.');
  }

  console.log(`${services.length} service(s), ${bad} holding more than one toll-free sender`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Everything that could go wrong here is a misidentified number, so that is where the tests are. All seven toll-free area codes have to match, a UK freephone number starting <code>+44 800</code> must not, and neither must a subscriber number that merely contains <code>800</code>. After that the pool rule is small: one toll-free sender is the recommended shape, two is the finding, and a pool of long codes is not this note's business.",
"test_py_file": "test_twilio_tollfree_pool_audit.py",
"test_py": '''from twilio_tollfree_pool_audit import is_toll_free, verdict


def pn(number):
    return {"phone_number": number, "sid": "PN" + number[-4:]}


def test_every_toll_free_area_code_is_recognised():
    for area in ("800", "833", "844", "855", "866", "877", "888"):
        assert is_toll_free("+1" + area + "5550123"), area


def test_a_uk_freephone_number_is_not_north_american_toll_free():
    # +44 800 is freephone in the UK and nothing to do with this rule.
    assert not is_toll_free("+448001234567")


def test_a_subscriber_number_containing_800_is_not_toll_free():
    assert not is_toll_free("+12028005550")
    assert not is_toll_free("+15558675309")


def test_formatting_does_not_change_the_answer():
    assert is_toll_free("+1 (833) 555-0123")
    assert is_toll_free("18335550123")


def test_one_toll_free_number_is_the_recommended_shape():
    state, detail = verdict([pn("+18005550123"), pn("+12025550100")])
    assert state == "single-toll-free"
    assert "+18005550123" in detail


def test_two_toll_free_numbers_in_one_pool_is_the_finding():
    state, detail = verdict([pn("+18005550123"), pn("+18445550199")])
    assert state == "multiple-toll-free"
    assert "snowshoeing" in detail
    assert "+18445550199" in detail


def test_a_pool_of_long_codes_is_not_this_note():
    assert verdict([pn("+12025550100"), pn("+12025550101")])[0] == "no-toll-free"


def test_an_empty_pool_points_at_the_other_note():
    state, detail = verdict([])
    assert state == "empty"
    assert "21704" in detail
''',
"test_js_file": "twilio-tollfree-pool-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isTollFree, verdict } from './twilio-tollfree-pool-audit.mjs';

const pn = (number) => ({ phone_number: number, sid: `PN${number.slice(-4)}` });

test('every toll free area code is recognised', () => {
  for (const area of ['800', '833', '844', '855', '866', '877', '888']) {
    assert.ok(isTollFree(`+1${area}5550123`), area);
  }
});

test('a uk freephone number is not north american toll free', () => {
  assert.ok(!isTollFree('+448001234567'));
});

test('a subscriber number containing 800 is not toll free', () => {
  assert.ok(!isTollFree('+12028005550'));
  assert.ok(!isTollFree('+15558675309'));
});

test('formatting does not change the answer', () => {
  assert.ok(isTollFree('+1 (833) 555-0123'));
  assert.ok(isTollFree('18335550123'));
});

test('one toll free number is the recommended shape', () => {
  const [state, detail] = verdict([pn('+18005550123'), pn('+12025550100')]);
  assert.equal(state, 'single-toll-free');
  assert.match(detail, /\\+18005550123/);
});

test('two toll free numbers in one pool is the finding', () => {
  const [state, detail] = verdict([pn('+18005550123'), pn('+18445550199')]);
  assert.equal(state, 'multiple-toll-free');
  assert.match(detail, /snowshoeing/);
  assert.match(detail, /\\+18445550199/);
});

test('a pool of long codes is not this note', () => {
  assert.equal(verdict([pn('+12025550100'), pn('+12025550101')])[0], 'no-toll-free');
});

test('an empty pool points at the other note', () => {
  const [state, detail] = verdict([]);
  assert.equal(state, 'empty');
  assert.match(detail, /21704/);
});
''',
"faq": [
 ("Both numbers are verified. Why are they being blocked?",
  "Verification is per number and this rule is about the pool. Carriers look at one Messaging Service pushing volume through several toll-free senders and read it as snowshoeing, which is spreading traffic across senders to stay under filtering thresholds. The senders being individually legitimate does not change the shape they make together."),
 ("Why did the number that was already working go down too?",
  "Because the block lands on the arrangement rather than on the newest sender. That is what makes the timeline confusing: the number you added is fine on paper and the one you have relied on for a year stops delivering."),
 ("How is this different from a toll-free number that was never verified?",
  "Same error code, different cause. An unverified number fails on its own, from its first US or Canadian send, and the fix is to submit the verification. This one fails after the fact, across a pool of numbers whose verification records are all in order, and the fix is to split the pool."),
 ("Can I keep two toll-free numbers if I only send from one?",
  "The recommendation is one toll-free number per Messaging Service, and the sender pool exists precisely so that Twilio can select between the numbers in it. If a second toll-free number is in the pool it is a candidate, whatever your application intends. Park the spare outside the service."),
 ("Does the script remove the extra number?",
  "No. It prints the DELETE for the extra pool member and leaves it to you, because taking a sender out of a live pool moves traffic onto whatever remains. Everything in this section runs on an API Key with read access and cannot write even if the key leaked."),
],
"related": [
 ("/twilio/tollfree-number-not-verified/", "An unverified toll-free number blocked in the US"),
 ("/twilio/tollfree-verification-rejected/", "A toll-free verification rejected with a reason"),
 ("/twilio/no-sender-matching-destination/", "A pool with no sender for the destination"),
],
"citations": [CITE_SERVICES_GUIDE, CITE_SERVICE_PN, CITE_30032, CITE_SERVICES_TUT],
},


{
"slug": "messaging-service-validity-period-too-long",
"title": "A ten hour validity period delivers passcodes nobody wants",
"description": "validity_period defaults to 36,000 seconds, so a queued passcode can wait ten hours and then arrive, after the user gave up and requested three more.",
"h1": "a ten hour validity period delivers passcodes nobody wants",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio validity_period 36000", "twilio messaging service validity period",
             "twilio otp arrives late", "twilio message queue latency",
             "twilio validity period default"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nobody complains that the passcode failed. They complain that it arrived: at 4pm, for a login attempt made at six in the morning, after they gave up and requested three more. The Messaging Service is carrying the default <code>validity_period</code> of 36,000 seconds, so a message stuck behind a backlog is entitled to wait ten hours before Twilio gives up on it.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}</code> and look at <code>validity_period</code>. The default is <code>36000</code> seconds &mdash; ten hours &mdash; and on a service carrying passcodes or alerts that is a delivery deadline nobody chose.</p>
<p>The setting alone is not evidence, so measure the queue: page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, bucket by <code>messaging_service_sid</code>, and compare <code>date_created</code> with <code>date_sent</code> on each row. Messages that waited minutes on a ten hour ceiling are the ones that will wait hours during the next backlog.</p>""",
"problem": """<p><code>ValidityPeriod</code> is the answer to a question nobody asks at setup time: how long is this message still worth sending? The default answers it with ten hours, which is a reasonable ceiling for a marketing campaign and an absurd one for a login code. Because the default is generous, nothing ever fails, and because nothing fails, nothing ever prompts the question.</p>
<p>What the ceiling actually buys you is a very late delivery instead of an early honest failure. A passcode that arrives after ten hours is worse than one that never arrives: the user has already requested three more, each of which cost you a segment and a fraud-score datapoint, and the one that finally lands may still be accepted by your verification logic, which is its own problem. The support ticket says the codes are unreliable, and every message in it was delivered successfully.</p>
<p>It is also the exact opposite of the failure next door. A validity period set too short kills messages in the queue and reports <code>30036</code>, which is loud and easy to find. Too long is silent by construction, so the two settings have to be reasoned about together: the right number is not the maximum and it is not the minimum, it is the length of time the message is still useful.</p>""",
"why": """<p><strong>The deadline is measured from acceptance, not from transmission.</strong> The clock starts when Twilio accepts the message, so everything spent queued behind other traffic counts against it. Ten hours of allowance means ten hours of waiting is permitted, and a long code clearing about one message per second reaches that during any serious campaign.</p>
<p><strong>The default is not neutral.</strong> A Messaging Service is created with <code>validity_period</code> at 36,000 seconds. Nobody sets it, so nobody reviews it, and it applies to every message the service carries, including the ones with a five minute shelf life.</p>
<p><strong>A late delivery is recorded as a success.</strong> The status callback says <code>delivered</code>, the Message row says <code>delivered</code>, and your dashboard counts it as one. The only trace of the wait is the gap between <code>date_created</code> and <code>date_sent</code>, and nothing in the API draws attention to it.</p>
<p><strong>Traffic type is not a field.</strong> There is no property on a Messaging Service that says &ldquo;this one carries passcodes&rdquo;. The API cannot tell whether ten hours is negligent or correct, which is why the script asks you to declare it per service rather than guessing from a friendly name and reporting confidently on a guess.</p>
<p><strong>Shortening it without widening the pool converts one problem into the other.</strong> Dropping the ceiling to five minutes on a service whose queue is genuinely ten hours deep does not deliver anything faster; it turns late deliveries into <code>30036</code> expiries. The deadline and the throughput have to move together.</p>""",
"steps": [
 {"h": "Read validity_period on every service",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code>, paging on <code>meta.next_page_url</code>. Note the value per service; <code>36000</code> is the untouched default and the starting point for every finding here.</p>"""},
 {"h": "Measure the queue instead of trusting the setting",
  "body": """<p>Page the Messages list over a window and compute <code>date_sent</code> minus <code>date_created</code> per row. Both are RFC 2822 timestamps, so parse them properly rather than slicing the string: a ten character slice reads identically for every message ever sent and turns every backlog into a flat line.</p>"""},
 {"h": "Bucket by messaging_service_sid, not by sender",
  "body": """<p><code>validity_period</code> is a property of the service, so the latency has to be attributed the same way. A message row carries <code>messaging_service_sid</code> when it was sent through one; rows without it were sent with a bare <code>From</code> and are not governed by any service setting.</p>"""},
 {"h": "Declare which services are time critical",
  "body": """<p>Ten hours is correct for marketing and wrong for passcodes, and no field distinguishes them. Pass the SIDs explicitly &mdash; <code>--time-critical MG...</code> for the passcode and alert services, <code>--bulk MG...</code> for the campaign ones &mdash; so the report says what it knows rather than inferring intent from a friendly name.</p>"""},
 {"h": "Set a deadline that matches the message, then widen the pool",
  "body": """<p><code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}</code> with <code>ValidityPeriod=300</code> for time-critical traffic keeps 36,000 for the campaigns that deserve it. If the measured queue is already deeper than the new ceiling, add senders at the same time, or you have simply chosen to fail fast instead of late.</p>"""},
],
"verify": """<p>Re-run the script with the same declarations. Every time-critical service should report <code>capped</code>, and no service should show late deliveries under a ten hour ceiling.</p>
<pre><code class="language-bash">python3 twilio_validity_ceiling_audit.py --time-critical MG0123 --bulk MG9876
# 4 service(s), 0 with a ten hour ceiling over time critical traffic</code></pre>""",
"code_intro": "One paginated GET over the services, one over the Messages list, and an API Key with read access for both. Two pure functions: one turns a Message row into the seconds it waited, the other weighs the ceiling against what the queue actually did. The second takes an explicit declaration of whether the traffic is time critical, because the API has no field for that and a guess dressed as a finding is worse than a question.",
"py_file": "twilio_validity_ceiling_audit.py",
"py": '''"""Report Messaging Services whose validity period is far longer than the
traffic they carry can use.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import collections
import datetime as dt
import email.utils
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_validity_ceiling_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MESSAGING = "https://messaging.twilio.com/v1"

# The value a Messaging Service is created with: ten hours.
DEFAULT_VALIDITY = 36000


def queue_seconds(message):
    """How long a message waited between being accepted and being sent.

    Both timestamps are RFC 2822, so they are parsed rather than sliced: a fixed
    length slice of that format reads the same for every message ever sent, and
    a backlog measured that way looks like no backlog at all.

    Pure. Returns None when either timestamp is missing or unparseable, because
    "not measured" and "waited nothing" are different facts.
    """
    def parse(value):
        if not value:
            return None
        try:
            return email.utils.parsedate_to_datetime(str(value))
        except (TypeError, ValueError):
            return None

    created, sent = parse(message.get("date_created")), parse(message.get("date_sent"))
    if created is None or sent is None:
        return None
    return (sent - created).total_seconds()


def verdict(service, latency=None, time_critical=None):
    """Weigh a service's validity period against what its queue actually did.

    `latency` is {"sampled": n, "late": k, "worst": seconds} or None when the
    Messages window produced no rows for this service. `time_critical` is True,
    False or None: the API has no field for what a service carries, so this is
    declared rather than guessed.

    Pure, so the ranking can be tested without a network.
    Returns (state, detail).
    """
    raw = service.get("validity_period")
    if raw is None:
        return ("unknown", "validity_period was not read, so nothing can be said "
                           "about the deadline this service enforces.")
    period = int(raw)
    late = (latency or {}).get("late") or 0
    worst = int((latency or {}).get("worst") or 0)

    if period < DEFAULT_VALIDITY:
        return ("capped",
                "validity_period is %ds rather than the %ds default. The failure "
                "at this end is 30036, messages expiring in the queue, so keep "
                "it above the wait you actually measure."
                % (period, DEFAULT_VALIDITY))

    if time_critical is False:
        return ("bulk",
                "the ten hour default, on traffic declared not time critical. "
                "That is what the default is for.")

    if late:
        return ("too-long",
                "%d of %d sampled message(s) waited past the threshold, worst "
                "%ds, under a %ds ceiling. A passcode behind that queue is "
                "delivered rather than dropped, hours after it was any use."
                % (late, (latency or {}).get("sampled") or 0, worst, period))

    if time_critical:
        return ("latent",
                "declared time critical and still carrying the ten hour default. "
                "Nothing is arriving late in this window, and nothing stops it "
                "during the next backlog either.")

    return ("undeclared",
            "the ten hour default, and this script cannot tell what the service "
            "carries. Declare it with --time-critical or --bulk.")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_services(session, limit):
    url = "%s/Services" % MESSAGING
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("services", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def sample_latency(session, account, days, threshold, max_messages):
    """Queue wait per Messaging Service, from the Messages list.

    The list has no status filter and no error code filter, so the window is
    paged and everything is computed here. Rows with no messaging_service_sid
    were sent with a bare From and are governed by no service setting.
    """
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"DateSent>": since, "PageSize": 1000}
    stats = collections.defaultdict(lambda: {"sampled": 0, "late": 0, "worst": 0})
    seen = 0
    while url and seen < max_messages:
        page = get(session, url, **params)
        rows = page.get("messages", [])
        seen += len(rows)
        for m in rows:
            sid = m.get("messaging_service_sid")
            waited = queue_seconds(m)
            if not sid or waited is None:
                continue
            s = stats[sid]
            s["sampled"] += 1
            s["worst"] = max(s["worst"], waited)
            if waited > threshold:
                s["late"] += 1
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--time-critical", action="append", default=[],
                    help="Messaging Service SID carrying passcodes or alerts")
    ap.add_argument("--bulk", action="append", default=[],
                    help="Messaging Service SID carrying campaign traffic")
    ap.add_argument("--days", type=int, default=7, help="latency window in days")
    ap.add_argument("--late-after", type=int, default=120,
                    help="seconds of queue wait that counts as late")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging the Messages list after this many rows")
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

    declared = {sid: True for sid in args.time_critical}
    declared.update({sid: False for sid in args.bulk})

    services = list_services(session, 200)
    stats = sample_latency(session, account, args.days, args.late_after,
                           args.max_messages)

    bad = 0
    for svc in services:
        sid = svc.get("sid")
        state, detail = verdict(svc, stats.get(sid), declared.get(sid))
        label = svc.get("friendly_name") or sid
        line = "%-12s %s  %s" % (state, label, detail)
        if state in ("capped", "bulk"):
            log.info(line)
            continue
        if state in ("unknown", "undeclared"):
            log.warning(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: POST %s/Services/%s ValidityPeriod=300 for time "
                    "critical traffic, and add senders if the measured wait is "
                    "already longer than the new ceiling, or you have chosen to "
                    "fail fast rather than late.", MESSAGING, sid)

    log.info("%d service(s), %d with a ten hour ceiling over time critical traffic",
             len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-validity-ceiling-audit.mjs",
"js": '''/**
 * Report Messaging Services whose validity period is far longer than the traffic
 * they carry can use.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MESSAGING = 'https://messaging.twilio.com/v1';

// The value a Messaging Service is created with: ten hours.
const DEFAULT_VALIDITY = 36000;

/**
 * How long a message waited between being accepted and being sent. Both
 * timestamps are RFC 2822, which Date.parse handles; null when either is
 * missing or unparseable, because "not measured" and "waited nothing" are
 * different facts. Pure.
 */
export function queueSeconds(message) {
  const created = Date.parse(message.date_created ?? '');
  const sent = Date.parse(message.date_sent ?? '');
  if (Number.isNaN(created) || Number.isNaN(sent)) return null;
  return (sent - created) / 1000;
}

/**
 * Weigh a service's validity period against what its queue actually did.
 * `latency` is {sampled, late, worst} or null; `timeCritical` is true, false or
 * null, because the API has no field for what a service carries. Pure.
 * Returns [state, detail].
 */
export function verdict(service, latency = null, timeCritical = null) {
  const raw = service.validity_period;
  if (raw === null || raw === undefined) {
    return ['unknown',
      'validity_period was not read, so nothing can be said about the deadline ' +
      'this service enforces.'];
  }
  const period = Number(raw);
  const late = latency?.late ?? 0;
  const worst = Math.round(latency?.worst ?? 0);

  if (period < DEFAULT_VALIDITY) {
    return ['capped',
      `validity_period is ${period}s rather than the ${DEFAULT_VALIDITY}s ` +
      'default. The failure at this end is 30036, messages expiring in the ' +
      'queue, so keep it above the wait you actually measure.'];
  }

  if (timeCritical === false) {
    return ['bulk',
      'the ten hour default, on traffic declared not time critical. That is ' +
      'what the default is for.'];
  }

  if (late) {
    return ['too-long',
      `${late} of ${latency?.sampled ?? 0} sampled message(s) waited past the ` +
      `threshold, worst ${worst}s, under a ${period}s ceiling. A passcode ` +
      'behind that queue is delivered rather than dropped, hours after it was ' +
      'any use.'];
  }

  if (timeCritical) {
    return ['latent',
      'declared time critical and still carrying the ten hour default. Nothing ' +
      'is arriving late in this window, and nothing stops it during the next ' +
      'backlog either.'];
  }

  return ['undeclared',
    'the ten hour default, and this script cannot tell what the service ' +
    'carries. Declare it with --time-critical or --bulk.'];
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

export async function listServices(auth, limit = 200) {
  let url = `${MESSAGING}/Services`;
  let params = { PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.services ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Queue wait per Messaging Service. Rows with no service sid used a bare From. */
async function sampleLatency(auth, account, days, threshold, maxMessages) {
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  let url = `${BASE}/Accounts/${account}/Messages.json`;
  let params = { 'DateSent>': since, PageSize: 1000 };
  const stats = new Map();
  let seen = 0;
  while (url && seen < maxMessages) {
    const page = await get(auth, url, params);
    const rows = page.messages ?? [];
    seen += rows.length;
    for (const m of rows) {
      const sid = m.messaging_service_sid;
      const waited = queueSeconds(m);
      if (!sid || waited === null) continue;
      const s = stats.get(sid) ?? { sampled: 0, late: 0, worst: 0 };
      s.sampled += 1;
      s.worst = Math.max(s.worst, waited);
      if (waited > threshold) s.late += 1;
      stats.set(sid, s);
    }
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return stats;
}

function repeatedFlag(name) {
  const out = [];
  process.argv.forEach((a, i) => { if (a === name) out.push(process.argv[i + 1]); });
  return out.filter(Boolean);
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
  const declared = new Map();
  for (const sid of repeatedFlag('--time-critical')) declared.set(sid, true);
  for (const sid of repeatedFlag('--bulk')) declared.set(sid, false);

  const services = await listServices(auth);
  const stats = await sampleLatency(auth, account, flagValue('--days', 7),
                                    flagValue('--late-after', 120),
                                    flagValue('--max-messages', 20000));

  let bad = 0;
  for (const svc of services) {
    const [state, detail] = verdict(svc, stats.get(svc.sid) ?? null,
                                    declared.has(svc.sid) ? declared.get(svc.sid) : null);
    const line = `${state.padEnd(12)} ${svc.friendly_name ?? svc.sid}  ${detail}`;
    if (state === 'capped' || state === 'bulk') { console.log(line); continue; }
    if (state === 'unknown' || state === 'undeclared') { console.warn(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: POST ${MESSAGING}/Services/${svc.sid} ValidityPeriod=300 ` +
                 'for time critical traffic, and add senders if the measured wait ' +
                 'is already longer than the new ceiling, or you have chosen to ' +
                 'fail fast rather than late.');
  }

  console.log(`${services.length} service(s), ${bad} with a ten hour ceiling ` +
              'over time critical traffic');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The measurement is the fragile part, so it gets pinned first: an RFC 2822 pair four minutes apart has to come out as 240 seconds, and a message that was never sent has to come out as <code>None</code> rather than zero. After that the ranking: measured late deliveries outrank every declaration, a service declared bulk is never a finding at the default, and an undeclared service says so instead of guessing from its name.",
"test_py_file": "test_twilio_validity_ceiling_audit.py",
"test_py": '''from twilio_validity_ceiling_audit import queue_seconds, verdict

DEFAULT = {"sid": "MG1", "friendly_name": "notifications", "validity_period": 36000}
TIGHT = {"sid": "MG2", "friendly_name": "passcodes", "validity_period": 300}


def test_queue_wait_is_parsed_from_rfc_2822_not_sliced():
    waited = queue_seconds({"date_created": "Mon, 24 Aug 2026 09:00:00 +0000",
                            "date_sent": "Mon, 24 Aug 2026 09:04:00 +0000"})
    assert waited == 240


def test_a_message_that_was_never_sent_measures_nothing():
    # None rather than 0: not measured and waited nothing are different facts.
    assert queue_seconds({"date_created": "Mon, 24 Aug 2026 09:00:00 +0000"}) is None
    assert queue_seconds({"date_created": "nonsense", "date_sent": "also nonsense"}) is None


def test_measured_late_deliveries_under_the_default_are_the_finding():
    state, detail = verdict(DEFAULT, {"sampled": 400, "late": 37, "worst": 5400}, True)
    assert state == "too-long"
    assert "5400s" in detail


def test_late_deliveries_outrank_a_missing_declaration():
    assert verdict(DEFAULT, {"sampled": 10, "late": 1, "worst": 900})[0] == "too-long"


def test_the_default_is_correct_for_traffic_declared_bulk():
    state, _ = verdict(DEFAULT, {"sampled": 900, "late": 90, "worst": 7200}, False)
    assert state == "bulk"


def test_time_critical_traffic_at_the_default_is_latent_even_with_a_clean_window():
    state, detail = verdict(DEFAULT, {"sampled": 500, "late": 0, "worst": 12}, True)
    assert state == "latent"
    assert "next backlog" in detail


def test_an_undeclared_service_asks_rather_than_guesses():
    assert verdict(DEFAULT, {"sampled": 500, "late": 0, "worst": 9})[0] == "undeclared"


def test_a_shorter_ceiling_points_at_the_other_failure():
    state, detail = verdict(TIGHT, {"sampled": 500, "late": 0, "worst": 9}, True)
    assert state == "capped"
    assert "30036" in detail


def test_an_unread_validity_period_is_never_guessed_at():
    assert verdict({"sid": "MG3"}, None, True)[0] == "unknown"
''',
"test_js_file": "twilio-validity-ceiling-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { queueSeconds, verdict } from './twilio-validity-ceiling-audit.mjs';

const DEFAULT = { sid: 'MG1', friendly_name: 'notifications', validity_period: 36000 };
const TIGHT = { sid: 'MG2', friendly_name: 'passcodes', validity_period: 300 };

test('queue wait is parsed from rfc 2822 not sliced', () => {
  assert.equal(queueSeconds({ date_created: 'Mon, 24 Aug 2026 09:00:00 +0000',
                              date_sent: 'Mon, 24 Aug 2026 09:04:00 +0000' }), 240);
});

test('a message that was never sent measures nothing', () => {
  assert.equal(queueSeconds({ date_created: 'Mon, 24 Aug 2026 09:00:00 +0000' }), null);
  assert.equal(queueSeconds({ date_created: 'nonsense', date_sent: 'also nonsense' }), null);
});

test('measured late deliveries under the default are the finding', () => {
  const [state, detail] = verdict(DEFAULT, { sampled: 400, late: 37, worst: 5400 }, true);
  assert.equal(state, 'too-long');
  assert.match(detail, /5400s/);
});

test('late deliveries outrank a missing declaration', () => {
  assert.equal(verdict(DEFAULT, { sampled: 10, late: 1, worst: 900 })[0], 'too-long');
});

test('the default is correct for traffic declared bulk', () => {
  assert.equal(verdict(DEFAULT, { sampled: 900, late: 90, worst: 7200 }, false)[0], 'bulk');
});

test('time critical traffic at the default is latent even with a clean window', () => {
  const [state, detail] = verdict(DEFAULT, { sampled: 500, late: 0, worst: 12 }, true);
  assert.equal(state, 'latent');
  assert.match(detail, /next backlog/);
});

test('an undeclared service asks rather than guesses', () => {
  assert.equal(verdict(DEFAULT, { sampled: 500, late: 0, worst: 9 })[0], 'undeclared');
});

test('a shorter ceiling points at the other failure', () => {
  const [state, detail] = verdict(TIGHT, { sampled: 500, late: 0, worst: 9 }, true);
  assert.equal(state, 'capped');
  assert.match(detail, /30036/);
});

test('an unread validity period is never guessed at', () => {
  assert.equal(verdict({ sid: 'MG3' }, null, true)[0], 'unknown');
});
''',
"faq": [
 ("What does validity_period actually control?",
  "How long Twilio will keep trying to send a message before giving up on it, measured from the moment the message is accepted rather than from the moment a sender is free. The service default is 36,000 seconds, which is ten hours of permitted waiting for every message the service carries."),
 ("If nothing is failing, what is the harm in leaving it?",
  "The harm is a delivery you did not want. A passcode that arrives ten hours late is recorded as delivered, counts as a success on every dashboard, and reaches a user who requested three more codes and has forgotten the whole thing. Failing fast would at least have told you."),
 ("How does this relate to the 30036 errors in the other note?",
  "They are the two ends of the same dial. Too short and messages expire in the queue with 30036, which is loud. Too long and they arrive uselessly late, which is silent. Neither extreme is the answer: the ceiling should be roughly how long the message stays useful, and the queue should be short enough to meet it."),
 ("Why does the script make me declare which services are time critical?",
  "Because nothing in the API says what a service carries. A ten hour ceiling on a marketing service is correct and on a passcode service is negligent, and the two look identical over the API. Guessing from a friendly name would produce a confident report built on a naming convention."),
 ("Should I just lower the validity period everywhere?",
  "Not on its own. If the measured queue is deeper than the new ceiling, lowering it converts late deliveries into expiries and delivers less than before. Lower the ceiling and add senders together, then re-measure the wait rather than assuming it moved."),
],
"related": [
 ("/twilio/validity-period-expired-30036/", "Messages expiring in the queue with 30036"),
 ("/twilio/messaging-queue-overflow-30001/", "Queue overflow when sends outrun throughput"),
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never reach a final state"),
],
"citations": [CITE_SERVICE, CITE_SCALING, CITE_30036, CITE_MSG],
},


{
"slug": "sms-reply-loop-rate-limit-14107",
"title": "Error 14107: an auto-reply loop trips the SMS rate limit",
"description": "Twilio caps outbound at 30 messages between the same two numbers in 30 seconds. The limit is the symptom; a handler answering its own answer is the bug.",
"h1": "error 14107: an auto-reply loop trips the SMS rate limit",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 14107", "sms send rate limit exceeded",
             "twilio message loop", "twilio auto reply loop",
             "twilio two numbers texting each other"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Two of your own numbers found each other. One auto-replies to everything it receives, the other does too, and for about half a minute they had the fastest conversation in the account's history. Then <code>14107</code> stopped it: <em>SMS send rate limit exceeded</em>. The rate limit is not the problem. It is the seatbelt, and it did its job.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> and filter for <code>error_code</code> <code>14107</code> client-side. Twilio caps outbound at 30 messages between the same two numbers in 30 seconds, as a guard against exactly this, so a <code>14107</code> means a pair of numbers hit that ceiling.</p>
<p>Then prove it is a loop rather than a burst. The alert's <code>resource_sid</code> gives you a Message SID; <code>GET /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}.json</code> gives you the pair, and two queries &mdash; <code>?To=A&amp;From=B</code> and <code>?To=B&amp;From=A</code> &mdash; give you both halves of the conversation. Dense, alternating, repeated bodies is a loop. Dense and one-directional is a send loop, which is a different repair.</p>""",
"problem": """<p>Every ingredient of this is something a reasonable person built on purpose. An inbound handler that always replies is good manners. A <code>&lt;Redirect&gt;</code> that sends the flow back to a menu is how menus work. A test number that echoes what it receives is a useful test number. The loop is what happens when two of those meet, and no single piece of it looks wrong when you read it.</p>
<p>It also gets found in the worst possible way. Nothing complains during the seconds when the loop is running at full speed, because every one of those messages sends successfully and is billed. The first sign is <code>14107</code>, which appears once the pair is already thirty messages deep, and which reads as a throughput problem: somebody's first instinct is to ask Twilio to raise the limit. Raising it would have bought a longer loop.</p>
<p>The other shape is quieter and worse. A loop that trades messages just under the ceiling never trips anything at all. It looks like an unusually chatty customer, it bills every segment, and it can run for days, which is why the audit checks the density below the limit as well as the failures above it.</p>""",
"why": """<p><strong>The limit is between a pair of numbers, not per account.</strong> Thirty messages in thirty seconds between the same two numbers is the ceiling, and it exists specifically to stop messaging loops. That scoping is why account-level throughput dashboards show nothing: the account is not busy, one pair of numbers is.</p>
<p><strong>Auto-replies do not know they are talking to a robot.</strong> An inbound handler answers whatever arrives. If what arrives is another handler's answer, the conversation is self-sustaining, and neither side has any way to notice. Two Twilio numbers in the same account are the classic pairing, usually because a test harness pointed one at the other.</p>
<p><strong>Request-time rejections often leave no Message row.</strong> A send refused with <code>14107</code> can be a rejection at the API rather than an undelivered message, so paging the Messages list looking for the error code finds nothing. The Alerts API is the read-only path to those, filtered client-side, and alerts are retained thirty days.</p>
<p><strong>The Messages list has no &ldquo;between these two numbers&rdquo; filter.</strong> It filters on <code>To</code> and on <code>From</code> independently, so a conversation has to be assembled from two queries and merged. Query one direction only and every loop looks like a one-sided flood, which points at the wrong repair.</p>
<p><strong>The error code names the ceiling, not the cause.</strong> <code>14107</code> is the same code whether the cause is a reply loop, a retry storm from your own sender, or a genuine burst to one recipient. The three need different fixes, and only the direction pattern in the message history tells them apart.</p>""",
"steps": [
 {"h": "Sweep Alerts for the code, filtering client-side",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=...</code> and keep the entries whose <code>error_code</code> is <code>14107</code>. There is no error code filter on the request, alerts are capped per request and retained thirty days, so treat the sweep as a sample of a window rather than as a complete history.</p>"""},
 {"h": "Resolve each alert to the pair of numbers involved",
  "body": """<p>The alert's <code>resource_sid</code> is usually a Message SID. <code>GET /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}.json</code> gives <code>to</code> and <code>from</code>. Where the alert points at something else, the single-alert fetch <code>GET https://monitor.twilio.com/v1/Alerts/{AlertSid}</code> carries the request variables that the list response leaves out.</p>"""},
 {"h": "Assemble the conversation from both directions",
  "body": """<p>Two queries per pair: <code>Messages.json?To=A&amp;From=B</code> and <code>?To=B&amp;From=A</code>, both bounded with <code>DateSent&gt;=</code>. Merge them and sort by time. The list cannot express &ldquo;between these two numbers&rdquo;, and half a conversation is exactly the half that makes a loop look like a flood.</p>"""},
 {"h": "Measure density in a sliding window, not per minute",
  "body": """<p>Count the largest number of messages falling inside any thirty second span rather than bucketing by clock minute. A loop that starts at 12:00:45 puts fifteen messages in one bucket and fifteen in the next, and a per-minute count reports it as ordinary traffic.</p>"""},
 {"h": "Separate a reply loop from a one-way burst",
  "body": """<p>Both directions present, with repeated bodies, is the auto-reply loop; the repair is in the inbound handler. All one direction is a send loop or a retry storm in your own code; the repair is in the sender. Twilio's <code>direction</code> field distinguishes <code>outbound-reply</code>, generated by TwiML answering an inbound message, from <code>outbound-api</code>, which your code asked for.</p>"""},
 {"h": "Fix the handler, then audit the TwiML that made it possible",
  "body": """<p>Add loop detection to the inbound handler &mdash; dedupe on the peer plus the body inside a short window, and refuse to reply to your own numbers &mdash; then walk every <code>&lt;Message&gt;</code> <code>action</code> URL and every <code>&lt;Redirect&gt;</code> target for cycles. The rate limit is the safety net; the handler is the thing that should have stopped.</p>"""},
],
"verify": """<p>Re-run the script over the same window. No pair should classify as a loop, and the echo count should be zero.</p>
<pre><code class="language-bash">python3 twilio_reply_loop_audit.py --days 3
# 2 pair(s) examined from 41 alert(s), 0 looping</code></pre>""",
"code_intro": "Alerts for the sample, one message fetch per alert to name the pair, then two paginated queries per pair &mdash; all GETs on an API Key with read access. The two pure functions are the whole diagnosis: the sliding window that measures density honestly, and the classifier that decides whether what you are looking at is a conversation eating itself or your own sender misbehaving.",
"py_file": "twilio_reply_loop_audit.py",
"py": '''"""Report pairs of numbers whose traffic is an SMS reply loop.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import collections
import datetime as dt
import email.utils
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_reply_loop_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MONITOR = "https://monitor.twilio.com/v1"

# Twilio's guard against messaging loops: 30 messages between the same two
# numbers in 30 seconds. The limit is the symptom, the loop is the bug.
LOOP_WINDOW = 30
LOOP_LIMIT = 30
ECHO_REPEATS = 4

RATE_LIMIT_ERROR = "14107"


def to_epoch(value):
    """RFC 2822 timestamp to epoch seconds, or None. Parsed rather than sliced:
    a fixed length slice of that format reads the same for every message."""
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(str(value)).timestamp()
    except (TypeError, ValueError):
        return None


def densest_window(stamps, window=LOOP_WINDOW):
    """Largest number of timestamps falling inside any `window` second span.

    Pure. A sliding window rather than clock buckets, because a loop starting at
    12:00:45 splits evenly across two minute buckets and disappears.
    """
    xs = sorted(s for s in stamps if s is not None)
    best = start = 0
    for i, t in enumerate(xs):
        while t - xs[start] > window:
            start += 1
        best = max(best, i - start + 1)
    return best


def classify_pair(messages, window=LOOP_WINDOW, limit=LOOP_LIMIT,
                  echo_repeats=ECHO_REPEATS):
    """Classify the traffic between one pair of numbers.

    `messages` is both directions merged: dicts with `direction`, `body` and
    `at`, the last being epoch seconds. Pure, so the density rule and the
    direction rule can be tested without a network. Returns (state, detail).
    """
    messages = messages or []
    if not messages:
        return ("quiet", "no messages between this pair in the window.")

    peak = densest_window([m.get("at") for m in messages], window)
    directions = [str(m.get("direction") or "") for m in messages]
    inbound = any(d.startswith("inbound") for d in directions)
    outbound = any(d.startswith("outbound") for d in directions)
    auto = any(d == "outbound-reply" for d in directions)
    bodies = collections.Counter(str(m.get("body") or "").strip()
                                 for m in messages if str(m.get("body") or "").strip())
    repeats = max(bodies.values()) if bodies else 0

    handwriting = (" Some of these are direction outbound-reply, which means "
                   "TwiML generated them in answer to an inbound message: that "
                   "is the loop's own handwriting." if auto else "")

    if peak >= limit and inbound and outbound:
        return ("reply-loop",
                "%d messages inside %d seconds, in both directions, with one "
                "body repeated %d times. That is the ceiling 14107 enforces, "
                "and the repair is in the inbound handler.%s"
                % (peak, window, repeats, handwriting))

    if peak >= limit:
        return ("one-way-burst",
                "%d messages inside %d seconds and all in one direction: a send "
                "loop or a retry storm in your own code, not a reply loop. Same "
                "error code, different repair." % (peak, window))

    if inbound and outbound and repeats >= echo_repeats:
        return ("echo",
                "one body repeated %d times in both directions, peaking at %d "
                "messages inside %d seconds. Under the limit, so nothing has "
                "failed and nothing will stop it either.%s"
                % (repeats, peak, window, handwriting))

    return ("normal",
            "%d message(s), peaking at %d inside %d seconds." % (len(messages), peak, window))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def rate_limit_alerts(session, days, max_alerts):
    """Alerts carrying 14107. There is no error code filter on the request, so
    the sweep is filtered here; alerts are retained 30 days."""
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    url = "%s/Alerts" % MONITOR
    params = {"LogLevel": "error", "StartDate": since, "PageSize": 100}
    out = []
    while url and len(out) < max_alerts:
        page = get(session, url, **params)
        for alert in page.get("alerts", []):
            if str(alert.get("error_code") or "") == RATE_LIMIT_ERROR:
                out.append(alert)
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:max_alerts]


def pair_from_alert(session, account, alert):
    """The two numbers behind one alert, via its Message resource.

    The list response does not carry request variables; only the single-alert
    fetch does. Resolving through the message SID keeps this to one small GET.
    """
    sid = str(alert.get("resource_sid") or "")
    if not sid.startswith(("SM", "MM")):
        return None
    msg = get(session, "%s/Accounts/%s/Messages/%s.json" % (BASE, account, sid))
    a, b = msg.get("from"), msg.get("to")
    return (a, b) if a and b else None


def conversation(session, account, a, b, days, max_messages):
    """Both halves of a conversation, merged and sorted.

    The Messages list filters To and From independently and cannot express
    "between these two numbers", so this is two queries. Half a conversation is
    exactly the half that makes a loop look like a flood.
    """
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    rows = []
    for sender, recipient in ((a, b), (b, a)):
        url = "%s/Accounts/%s/Messages.json" % (BASE, account)
        params = {"From": sender, "To": recipient, "DateSent>": since, "PageSize": 1000}
        while url and len(rows) < max_messages:
            page = get(session, url, **params)
            for m in page.get("messages", []):
                rows.append({"direction": m.get("direction"), "body": m.get("body"),
                             "at": to_epoch(m.get("date_created") or m.get("date_sent"))})
            nxt = page.get("next_page_uri")
            url, params = (HOST + nxt) if nxt else None, {}
    rows.sort(key=lambda m: m["at"] or 0)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=3,
                    help="window in days; alerts are retained 30")
    ap.add_argument("--max-alerts", type=int, default=200,
                    help="stop after this many 14107 alerts")
    ap.add_argument("--max-messages", type=int, default=4000,
                    help="stop paging a pair's history after this many rows")
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

    alerts = rate_limit_alerts(session, args.days, args.max_alerts)
    if not alerts:
        log.info("no %s alerts in the last %d day(s)", RATE_LIMIT_ERROR, args.days)
        return 0

    pairs = set()
    for alert in alerts:
        pair = pair_from_alert(session, account, alert)
        if pair:
            pairs.add(tuple(sorted(pair)))
        else:
            log.warning("alert %s does not point at a message; fetch %s/Alerts/%s "
                        "for its request variables", alert.get("sid"), MONITOR,
                        alert.get("sid"))

    bad = 0
    for a, b in sorted(pairs):
        rows = conversation(session, account, a, b, args.days, args.max_messages)
        state, detail = classify_pair(rows)
        line = "%-14s %s <-> %s  %s" % (state, a, b, detail)
        if state in ("normal", "quiet"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: dedupe on peer plus body inside a short window in "
                    "the inbound handler, refuse to reply to your own numbers, "
                    "and audit every <Message> action URL and <Redirect> target "
                    "for cycles. Raising the rate limit buys a longer loop.")

    log.info("%d pair(s) examined from %d alert(s), %d looping",
             len(pairs), len(alerts), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-reply-loop-audit.mjs",
"js": '''/**
 * Report pairs of numbers whose traffic is an SMS reply loop.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MONITOR = 'https://monitor.twilio.com/v1';

// Twilio's guard against messaging loops: 30 messages between the same two
// numbers in 30 seconds. The limit is the symptom, the loop is the bug.
const LOOP_WINDOW = 30;
const LOOP_LIMIT = 30;
const ECHO_REPEATS = 4;

const RATE_LIMIT_ERROR = '14107';

/** RFC 2822 timestamp to epoch seconds, or null. */
export function toEpoch(value) {
  const ms = Date.parse(value ?? '');
  return Number.isNaN(ms) ? null : ms / 1000;
}

/**
 * Largest number of timestamps falling inside any `window` second span. Pure. A
 * sliding window rather than clock buckets, because a loop starting at 12:00:45
 * splits evenly across two minute buckets and disappears.
 */
export function densestWindow(stamps, window = LOOP_WINDOW) {
  const xs = stamps.filter((s) => s !== null && s !== undefined).sort((p, q) => p - q);
  let best = 0;
  let start = 0;
  for (let i = 0; i < xs.length; i += 1) {
    while (xs[i] - xs[start] > window) start += 1;
    best = Math.max(best, i - start + 1);
  }
  return best;
}

/**
 * Classify the traffic between one pair of numbers. `messages` is both
 * directions merged, each with direction, body and `at` in epoch seconds. Pure.
 * Returns [state, detail].
 */
export function classifyPair(messages, window = LOOP_WINDOW, limit = LOOP_LIMIT,
                             echoRepeats = ECHO_REPEATS) {
  const rows = messages ?? [];
  if (!rows.length) return ['quiet', 'no messages between this pair in the window.'];

  const peak = densestWindow(rows.map((m) => m.at), window);
  const directions = rows.map((m) => String(m.direction ?? ''));
  const inbound = directions.some((d) => d.startsWith('inbound'));
  const outbound = directions.some((d) => d.startsWith('outbound'));
  const auto = directions.some((d) => d === 'outbound-reply');

  const bodies = new Map();
  for (const m of rows) {
    const body = String(m.body ?? '').trim();
    if (body) bodies.set(body, (bodies.get(body) ?? 0) + 1);
  }
  const repeats = bodies.size ? Math.max(...bodies.values()) : 0;

  const handwriting = auto
    ? ' Some of these are direction outbound-reply, which means TwiML generated ' +
      "them in answer to an inbound message: that is the loop's own handwriting."
    : '';

  if (peak >= limit && inbound && outbound) {
    return ['reply-loop',
      `${peak} messages inside ${window} seconds, in both directions, with one ` +
      `body repeated ${repeats} times. That is the ceiling 14107 enforces, and ` +
      `the repair is in the inbound handler.${handwriting}`];
  }

  if (peak >= limit) {
    return ['one-way-burst',
      `${peak} messages inside ${window} seconds and all in one direction: a ` +
      'send loop or a retry storm in your own code, not a reply loop. Same ' +
      'error code, different repair.'];
  }

  if (inbound && outbound && repeats >= echoRepeats) {
    return ['echo',
      `one body repeated ${repeats} times in both directions, peaking at ${peak} ` +
      `messages inside ${window} seconds. Under the limit, so nothing has ` +
      `failed and nothing will stop it either.${handwriting}`];
  }

  return ['normal',
    `${rows.length} message(s), peaking at ${peak} inside ${window} seconds.`];
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

async function rateLimitAlerts(auth, days, maxAlerts) {
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  let url = `${MONITOR}/Alerts`;
  let params = { LogLevel: 'error', StartDate: since, PageSize: 100 };
  const out = [];
  while (url && out.length < maxAlerts) {
    const page = await get(auth, url, params);
    for (const alert of page.alerts ?? []) {
      if (String(alert.error_code ?? '') === RATE_LIMIT_ERROR) out.push(alert);
    }
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, maxAlerts);
}

async function pairFromAlert(auth, account, alert) {
  const sid = String(alert.resource_sid ?? '');
  if (!sid.startsWith('SM') && !sid.startsWith('MM')) return null;
  const msg = await get(auth, `${BASE}/Accounts/${account}/Messages/${sid}.json`);
  return msg.from && msg.to ? [msg.from, msg.to] : null;
}

/** Both halves of a conversation. The list filters To and From independently. */
async function conversation(auth, account, a, b, days, maxMessages) {
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const rows = [];
  for (const [sender, recipient] of [[a, b], [b, a]]) {
    let url = `${BASE}/Accounts/${account}/Messages.json`;
    let params = { From: sender, To: recipient, 'DateSent>': since, PageSize: 1000 };
    while (url && rows.length < maxMessages) {
      const page = await get(auth, url, params);
      for (const m of page.messages ?? []) {
        rows.push({ direction: m.direction, body: m.body,
                    at: toEpoch(m.date_created ?? m.date_sent) });
      }
      url = page.next_page_uri ? HOST + page.next_page_uri : null;
      params = {};
    }
  }
  rows.sort((p, q) => (p.at ?? 0) - (q.at ?? 0));
  return rows;
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
  const days = flagValue('--days', 3);

  const alerts = await rateLimitAlerts(auth, days, flagValue('--max-alerts', 200));
  if (!alerts.length) {
    console.log(`no ${RATE_LIMIT_ERROR} alerts in the last ${days} day(s)`);
    return;
  }

  const pairs = new Set();
  for (const alert of alerts) {
    const pair = await pairFromAlert(auth, account, alert);
    if (pair) pairs.add([...pair].sort().join('|'));
    else {
      console.warn(`alert ${alert.sid} does not point at a message; fetch ` +
                   `${MONITOR}/Alerts/${alert.sid} for its request variables`);
    }
  }

  let bad = 0;
  for (const joined of [...pairs].sort()) {
    const [a, b] = joined.split('|');
    const rows = await conversation(auth, account, a, b, days,
                                    flagValue('--max-messages', 4000));
    const [state, detail] = classifyPair(rows);
    const line = `${state.padEnd(14)} ${a} <-> ${b}  ${detail}`;
    if (state === 'normal' || state === 'quiet') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn('  repair: dedupe on peer plus body inside a short window in the ' +
                 'inbound handler, refuse to reply to your own numbers, and audit ' +
                 'every <Message> action URL and <Redirect> target for cycles. ' +
                 'Raising the rate limit buys a longer loop.');
  }

  console.log(`${pairs.size} pair(s) examined from ${alerts.length} alert(s), ${bad} looping`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The window test is the one that matters most: thirty messages straddling a minute boundary have to count as thirty, because a per-minute bucket would report fifteen and fifteen and call it quiet. After that the direction rule, which decides where the repair goes &mdash; both directions is a handler answering itself, one direction is your own sender misbehaving &mdash; and the echo case, a loop running just under the ceiling that never trips anything at all.",
"test_py_file": "test_twilio_reply_loop_audit.py",
"test_py": '''from twilio_reply_loop_audit import classify_pair, densest_window


def pair_traffic(count, start=0.0, step=0.8, alternating=True, body="Thanks!"):
    """A dense exchange between two numbers, one message every `step` seconds."""
    rows = []
    for i in range(count):
        direction = ("inbound" if i % 2 else "outbound-reply") if alternating else "outbound-api"
        rows.append({"direction": direction, "body": body, "at": start + i * step})
    return rows


def test_a_window_straddling_a_minute_boundary_is_still_one_burst():
    # 30 messages from 12:00:45 to 12:01:15. Clock buckets would see 15 and 15.
    stamps = [45.0 + i for i in range(30)]
    assert densest_window(stamps, 30) == 30


def test_sparse_traffic_has_a_low_peak():
    assert densest_window([0, 60, 120, 180], 30) == 1


def test_an_alternating_burst_at_the_ceiling_is_a_reply_loop():
    state, detail = classify_pair(pair_traffic(34))
    assert state == "reply-loop"
    assert "both directions" in detail
    assert "outbound-reply" in detail


def test_a_one_directional_burst_is_not_a_reply_loop():
    state, detail = classify_pair(pair_traffic(34, alternating=False))
    assert state == "one-way-burst"
    assert "retry storm" in detail


def test_a_loop_running_under_the_limit_is_still_reported():
    # Nothing has failed, nothing will stop it, and it bills every segment.
    state, detail = classify_pair(pair_traffic(8, step=3.0))
    assert state == "echo"
    assert "Under the limit" in detail


def test_ordinary_conversation_is_left_alone():
    rows = [{"direction": "inbound", "body": "hi", "at": 0.0},
            {"direction": "outbound-reply", "body": "hello", "at": 40.0},
            {"direction": "inbound", "body": "thanks", "at": 200.0}]
    assert classify_pair(rows)[0] == "normal"


def test_an_empty_history_is_its_own_state():
    assert classify_pair([])[0] == "quiet"


def test_missing_timestamps_do_not_crash_the_window():
    rows = [{"direction": "inbound", "body": "hi", "at": None},
            {"direction": "outbound-reply", "body": "hi", "at": 1.0}]
    assert classify_pair(rows)[0] == "normal"
''',
"test_js_file": "twilio-reply-loop-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classifyPair, densestWindow } from './twilio-reply-loop-audit.mjs';

/** A dense exchange between two numbers, one message every `step` seconds. */
function pairTraffic(count, { start = 0, step = 0.8, alternating = true,
                              body = 'Thanks!' } = {}) {
  const rows = [];
  for (let i = 0; i < count; i += 1) {
    const direction = alternating
      ? (i % 2 ? 'inbound' : 'outbound-reply')
      : 'outbound-api';
    rows.push({ direction, body, at: start + i * step });
  }
  return rows;
}

test('a window straddling a minute boundary is still one burst', () => {
  const stamps = Array.from({ length: 30 }, (_, i) => 45 + i);
  assert.equal(densestWindow(stamps, 30), 30);
});

test('sparse traffic has a low peak', () => {
  assert.equal(densestWindow([0, 60, 120, 180], 30), 1);
});

test('an alternating burst at the ceiling is a reply loop', () => {
  const [state, detail] = classifyPair(pairTraffic(34));
  assert.equal(state, 'reply-loop');
  assert.match(detail, /both directions/);
  assert.match(detail, /outbound-reply/);
});

test('a one directional burst is not a reply loop', () => {
  const [state, detail] = classifyPair(pairTraffic(34, { alternating: false }));
  assert.equal(state, 'one-way-burst');
  assert.match(detail, /retry storm/);
});

test('a loop running under the limit is still reported', () => {
  const [state, detail] = classifyPair(pairTraffic(8, { step: 3 }));
  assert.equal(state, 'echo');
  assert.match(detail, /Under the limit/);
});

test('ordinary conversation is left alone', () => {
  const rows = [{ direction: 'inbound', body: 'hi', at: 0 },
                { direction: 'outbound-reply', body: 'hello', at: 40 },
                { direction: 'inbound', body: 'thanks', at: 200 }];
  assert.equal(classifyPair(rows)[0], 'normal');
});

test('an empty history is its own state', () => {
  assert.equal(classifyPair([])[0], 'quiet');
});

test('missing timestamps do not crash the window', () => {
  const rows = [{ direction: 'inbound', body: 'hi', at: null },
                { direction: 'outbound-reply', body: 'hi', at: 1 }];
  assert.equal(classifyPair(rows)[0], 'normal');
});
''',
"faq": [
 ("What exactly is the limit behind 14107?",
  "Thirty messages between the same two numbers in thirty seconds. It is a guard against messaging loops rather than a throughput quota, which is why it is scoped to a pair and why account-level dashboards show nothing while it is being hit."),
 ("Can the limit be raised?",
  "That is the wrong request, and it is the first one everybody makes. The limit is what stopped a conversation that had no other way to end; raising it buys a longer loop and a larger bill. The thing to change is the handler that answers its own answers."),
 ("How do two Twilio numbers end up texting each other?",
  "Usually a test. One number is pointed at a handler that always replies, another is used to poke it, and both end up in the same account with auto-replies enabled. A <Redirect> cycle inside one flow does the same thing with a single number and a single peer."),
 ("Why not just search the Messages list for 14107?",
  "Because a request-time rejection frequently leaves no Message row at all, and the Messages list has no error code filter in any case. The Alerts API holds those, filtered client-side, with thirty days of retention and a cap per request, so treat the sweep as a sample of a window."),
 ("Why does the script query the messages twice per pair?",
  "The Messages list filters To and From independently and cannot express traffic between two numbers, so each direction is its own query. With only one of them, a loop looks like a one-sided flood and the repair gets pointed at the sender instead of at the handler."),
],
"related": [
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS disappearing into a blank sms_url"),
 ("/twilio/messaging-queue-overflow-30001/", "Sends outrunning throughput and overflowing"),
 ("/twilio/a2p-throughput-exceeded-30022/", "Bursts past the campaign's throughput"),
],
"citations": [CITE_14107, CITE_ALERTS, CITE_MSG_TWIML, CITE_MSG],
},

]
