#!/usr/bin/env python3
"""/twilio/ field notes, batch A — the writing.

Every note here is a problem a script can find with a READ-ONLY Twilio
credential: an API Key with read access, never the account auth token. That
constraint is the whole design. These scripts hold a credential to an account
that can send messages and spend money, so none of them writes. They read, they
say exactly what is wrong, and they print the repair for a human to run.
"""

CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_APPS = ("Application resource — Twilio Docs",
             "https://www.twilio.com/docs/usage/api/applications")
CITE_11200 = ("Error 11200: HTTP retrieval failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/11200")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_SERVICE_PN = ("Messaging Service PhoneNumber resource — Twilio Docs",
                   "https://www.twilio.com/docs/messaging/api/phonenumber-resource")
CITE_USA2P = ("UsAppToPerson resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/usapptoperson-resource")
CITE_30034 = ("Error 30034: message from an unregistered number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30034")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_TWIML_VOICE = ("TwiML for Programmable Voice — Twilio Docs",
                    "https://www.twilio.com/docs/voice/twiml")
CITE_WEBHOOKS = ("Webhooks (HTTP callbacks) — Twilio Docs",
                 "https://www.twilio.com/docs/usage/webhooks")

GUIDES = [

{
"slug": "phone-number-still-on-demo-twiml",
"title": "A phone number still points at Twilio's demo TwiML",
"description": "Callers hear the Twilio demo greeting instead of your app. The webhook answers 200, every call is marked completed, and error monitoring never sees it.",
"h1": "a phone number still points at Twilio's demo TwiML",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio demo twiml", "demo.twilio.com voice.xml",
             "twilio number wrong webhook", "twilio voice_url default",
             "unedited twiml bin"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The number rings. It answers. It plays a cheerful message about Twilio and hangs up. Nothing appears in the Debugger, nothing appears in your logs, and every call in the console is marked <code>completed</code> &mdash; because the webhook Twilio fetched answered perfectly. It just was not yours.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> and flag any number whose <code>voice_url</code> or <code>sms_url</code> still points at <code>demo.twilio.com</code>, or at an unedited TwiML Bin on <code>handler.twilio.com/twiml/</code>, or which has no handler and no application SID at all.</p>
<p>Newly purchased numbers arrive with <code>voice_url</code> set to <code>https://demo.twilio.com/docs/voice.xml</code>. That URL is healthy and returns valid TwiML, which is precisely why no error-based monitoring will ever mention it.</p>""",
"problem": """<p>Every other misconfiguration in this section announces itself with an error code. This one does not, and that is the entire difficulty. Twilio requested a URL, got a <code>200</code>, got well-formed TwiML, and executed it exactly as instructed. From the platform's point of view the call was a success. From the Alerts API's point of view nothing happened worth logging. From your application's point of view nothing happened at all, because your application was never contacted.</p>
<p>So it survives. It survives the deploy, the launch checklist, the monitoring review, and it is usually discovered by a customer or a salesperson dialling the number on the website footer. By then the number has been live for weeks and nobody can say how many callers heard the demo greeting, because there is no record of a failure to count.</p>""",
"why": """<p><strong>The demo URL is the factory default, not a mistake anyone made.</strong> Buying a number through the API or the console provisions it with Twilio's demo TwiML so that the number does something rather than erroring. Wiring it to your own application is a separate step, and it is the step that gets skipped when a number is bought in a hurry to test something.</p>
<p><strong>TwiML Bins fail the same way, more convincingly.</strong> A Bin created during a quickstart is a real, permanent URL on <code>handler.twilio.com</code>. It answers, it is not a demo URL, and it looks configured in the console. If the application was supposed to take over and never did, a Bin is the leftover that hides it.</p>
<p><strong>The console shows configuration, not intent.</strong> Both fields are populated with valid HTTPS URLs. There is nothing red, nothing empty, nothing that reads as wrong &mdash; you have to already know what the URL <em>should</em> be to see that it isn't.</p>
<p><strong>Numbers outlive the projects that bought them.</strong> An account with forty numbers accumulated over three years has no one person who knows what each is for. The audit has to be mechanical, because memory is not going to cover it.</p>""",
"steps": [
 {"h": "List every number and read both handler fields",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, following <code>next_page_uri</code> to the end. Read <code>voice_url</code>, <code>sms_url</code>, <code>voice_application_sid</code> and <code>sms_application_sid</code> on each. A number can be misrouted on one channel and correct on the other.</p>"""},
 {"h": "Match on host and path, not on the whole string",
  "body": """<p>The demo URL appears as <code>http://</code> and <code>https://</code>, with and without a trailing query string, and sometimes with the <code>.xml</code> swapped for a different demo document. Comparing full strings misses all of those; comparing the host catches every variant.</p>"""},
 {"h": "Treat an empty number as the same finding",
  "body": """<p>A number with no <code>voice_url</code>, no <code>sms_url</code> and no application SID is bought, billed monthly and answers nothing. It belongs in the same report as the demo ones because it has the same cause: provisioned and never wired up.</p>"""},
 {"h": "Check whether anyone is actually dialling it",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Calls.json?To={E164}&amp;PageSize=1</code> answers the only question that sets priority. A demo-TwiML number with traffic is an incident; one with none is a tidying job, and possibly a number to release.</p>"""},
 {"h": "Point it at your application, then re-run",
  "body": """<p><code>POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json</code> with <code>VoiceUrl</code> and <code>VoiceMethod</code>. Run the audit again afterwards; it is one paginated GET and it is worth having on a schedule, because the next number someone buys will arrive on the demo URL too.</p>"""},
],
"verify": """<p>Re-run the script. Every number should report <code>configured</code>, and the demo count should be zero.</p>
<pre><code class="language-bash">python3 twilio_demo_twiml_audit.py
# 12 number(s), 0 on demo or placeholder TwiML</code></pre>""",
"code_intro": "The script does one paginated GET over the numbers and, with <code>--check-traffic</code>, one extra GET per flagged number &mdash; an API Key with read access is enough, and is what you should give it. The classification is a pure function, because the interesting part is the URL matching rules, and those deserve to be visible and testable rather than buried in a request loop.",
"py_file": "twilio_demo_twiml_audit.py",
"py": '''"""Report Twilio phone numbers still answering with demo or placeholder TwiML.

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
log = logging.getLogger("twilio_demo_twiml_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

DEMO_HOST = "demo.twilio.com"
BIN_PREFIX = "handler.twilio.com/twiml/"


def host_and_path(url):
    """Reduce a URL to lowercase host plus path.

    The demo endpoint turns up as http and https, with and without a query
    string, and pointing at several different demo documents. Matching the whole
    string misses most of those; matching host and path catches all of them.
    """
    u = str(url or "").strip()
    for scheme in ("https://", "http://"):
        if u.lower().startswith(scheme):
            u = u[len(scheme):]
            break
    u = u.split("?", 1)[0].split("#", 1)[0]
    head = u.split("/", 1)[0]
    if "@" in head:
        u = u.split("@", 1)[1]
    return u.lower()


def verdict(number):
    """Classify one IncomingPhoneNumber. Pure, so the rules can be tested
    without a network.

    Returns (state, detail).
    """
    handlers = [("voice", number.get("voice_url")), ("sms", number.get("sms_url"))]

    demo = [c for c, u in handlers if host_and_path(u).startswith(DEMO_HOST)]
    if demo:
        return ("demo",
                "%s handler is Twilio's demo TwiML. It answers 200 with valid "
                "TwiML, so nothing is logged and every call reads as completed."
                % "/".join(demo))

    bins = [c for c, u in handlers if host_and_path(u).startswith(BIN_PREFIX)]
    if bins:
        return ("twiml-bin",
                "%s handler is a TwiML Bin. Bins are legitimate, but one left "
                "over from a quickstart fails exactly like the demo URL."
                % "/".join(bins))

    routed = [c for c, u in handlers if str(u or "").strip()]
    if str(number.get("voice_application_sid") or "").strip():
        routed.append("voice app")
    if str(number.get("sms_application_sid") or "").strip():
        routed.append("sms app")
    if not routed:
        return ("unrouted",
                "no voice_url, no sms_url and no application sid: the number is "
                "bought, billed monthly and answers nothing.")

    return ("configured", "handled by " + ", ".join(routed))


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


def has_traffic(session, account, e164):
    """One call record is enough to know the number is in use."""
    page = get(session, "%s/Accounts/%s/Calls.json" % (BASE, account),
               To=e164, PageSize=1)
    return bool(page.get("calls"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000,
                    help="stop after this many numbers")
    ap.add_argument("--check-traffic", action="store_true",
                    help="one extra GET per flagged number to see if it is dialled")
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

    bad = 0
    for n in numbers:
        state, detail = verdict(n)
        line = "%-11s %s  %s" % (state, n.get("phone_number", "?"), detail)
        if state == "configured":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if args.check_traffic and has_traffic(session, account, n.get("phone_number")):
            log.warning("  this number has inbound calls: fix it before the rest")
        log.warning("  repair: POST %s/Accounts/%s/IncomingPhoneNumbers/%s.json "
                    "VoiceUrl=https://your-app.example.com/voice VoiceMethod=POST",
                    BASE, account, n.get("sid"))

    log.info("%d number(s), %d on demo or placeholder TwiML", len(numbers), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-demo-twiml-audit.mjs",
"js": '''/**
 * Report Twilio phone numbers still answering with demo or placeholder TwiML.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const DEMO_HOST = 'demo.twilio.com';
const BIN_PREFIX = 'handler.twilio.com/twiml/';

/**
 * Reduce a URL to lowercase host plus path, so http/https, query strings and
 * different demo documents all match the same rule.
 */
export function hostAndPath(url) {
  let u = String(url ?? '').trim();
  for (const scheme of ['https://', 'http://']) {
    if (u.toLowerCase().startsWith(scheme)) { u = u.slice(scheme.length); break; }
  }
  u = u.split('?')[0].split('#')[0];
  if (u.split('/')[0].includes('@')) u = u.slice(u.indexOf('@') + 1);
  return u.toLowerCase();
}

/**
 * Classify one IncomingPhoneNumber. Pure, so the rules can be tested without a
 * network. Returns [state, detail].
 */
export function verdict(number) {
  const handlers = [['voice', number.voice_url], ['sms', number.sms_url]];

  const demo = handlers.filter(([, u]) => hostAndPath(u).startsWith(DEMO_HOST));
  if (demo.length) {
    return ['demo',
      `${demo.map(([c]) => c).join('/')} handler is Twilio's demo TwiML. It ` +
      'answers 200 with valid TwiML, so nothing is logged and every call reads ' +
      'as completed.'];
  }

  const bins = handlers.filter(([, u]) => hostAndPath(u).startsWith(BIN_PREFIX));
  if (bins.length) {
    return ['twiml-bin',
      `${bins.map(([c]) => c).join('/')} handler is a TwiML Bin. Bins are ` +
      'legitimate, but one left over from a quickstart fails exactly like the ' +
      'demo URL.'];
  }

  const routed = handlers.filter(([, u]) => String(u ?? '').trim()).map(([c]) => c);
  if (String(number.voice_application_sid ?? '').trim()) routed.push('voice app');
  if (String(number.sms_application_sid ?? '').trim()) routed.push('sms app');
  if (routed.length === 0) {
    return ['unrouted',
      'no voice_url, no sms_url and no application sid: the number is bought, ' +
      'billed monthly and answers nothing.'];
  }

  return ['configured', `handled by ${routed.join(', ')}`];
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

  const numbers = await listNumbers(auth, account);
  if (numbers.length === 0) {
    console.log('no phone numbers on this account');
    return;
  }

  let bad = 0;
  for (const n of numbers) {
    const [state, detail] = verdict(n);
    const line = `${state.padEnd(11)} ${n.phone_number ?? '?'}  ${detail}`;
    if (state === 'configured') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (checkTraffic) {
      const calls = await get(auth, `${BASE}/Accounts/${account}/Calls.json`,
                              { To: n.phone_number, PageSize: 1 });
      if ((calls.calls ?? []).length) {
        console.warn('  this number has inbound calls: fix it before the rest');
      }
    }
    console.warn(`  repair: POST ${BASE}/Accounts/${account}/IncomingPhoneNumbers/` +
                 `${n.sid}.json VoiceUrl=https://your-app.example.com/voice ` +
                 'VoiceMethod=POST');
  }

  console.log(`${numbers.length} number(s), ${bad} on demo or placeholder TwiML`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones a string comparison gets wrong: the demo URL over plain <code>http</code>, the demo URL with a query string, and a number whose voice handler is fine while its SMS handler is not. The last one matters because a per-number verdict that only ever looks at <code>voice_url</code> reports an SMS black hole as healthy.",
"test_py_file": "test_twilio_demo_twiml_audit.py",
"test_py": '''from twilio_demo_twiml_audit import host_and_path, verdict


def test_default_demo_voice_url_is_flagged():
    state, detail = verdict({"voice_url": "https://demo.twilio.com/docs/voice.xml"})
    assert state == "demo"
    assert "completed" in detail


def test_demo_url_over_http_and_with_a_query_string_is_still_demo():
    # The reason matching is on host and path rather than the whole string.
    state, _ = verdict({"voice_url": "http://demo.twilio.com/docs/voice.xml?x=1"})
    assert state == "demo"


def test_demo_on_the_sms_handler_is_found_when_voice_is_fine():
    state, detail = verdict({"voice_url": "https://app.example.com/voice",
                             "sms_url": "https://demo.twilio.com/welcome/sms/reply"})
    assert state == "demo"
    assert "sms" in detail


def test_unedited_twiml_bin_is_its_own_state():
    state, _ = verdict({"voice_url": "https://handler.twilio.com/twiml/EH0123456789"})
    assert state == "twiml-bin"


def test_number_with_no_handler_at_all_is_unrouted():
    state, detail = verdict({"voice_url": "", "sms_url": None})
    assert state == "unrouted"
    assert "billed" in detail


def test_application_sid_counts_as_routed():
    state, _ = verdict({"voice_application_sid": "AP0123456789"})
    assert state == "configured"


def test_host_and_path_drops_scheme_credentials_and_query():
    assert host_and_path("https://user@Demo.Twilio.com/docs/voice.xml?a=b") == \\
        "demo.twilio.com/docs/voice.xml"
''',
"test_js_file": "twilio-demo-twiml-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { hostAndPath, verdict } from './twilio-demo-twiml-audit.mjs';

test('default demo voice url is flagged', () => {
  const [state, detail] = verdict({ voice_url: 'https://demo.twilio.com/docs/voice.xml' });
  assert.equal(state, 'demo');
  assert.match(detail, /completed/);
});

test('demo url over http and with a query string is still demo', () => {
  assert.equal(verdict({ voice_url: 'http://demo.twilio.com/docs/voice.xml?x=1' })[0], 'demo');
});

test('demo on the sms handler is found when voice is fine', () => {
  const [state, detail] = verdict({
    voice_url: 'https://app.example.com/voice',
    sms_url: 'https://demo.twilio.com/welcome/sms/reply',
  });
  assert.equal(state, 'demo');
  assert.match(detail, /sms/);
});

test('unedited twiml bin is its own state', () => {
  assert.equal(
    verdict({ voice_url: 'https://handler.twilio.com/twiml/EH0123456789' })[0],
    'twiml-bin');
});

test('number with no handler at all is unrouted', () => {
  const [state, detail] = verdict({ voice_url: '', sms_url: null });
  assert.equal(state, 'unrouted');
  assert.match(detail, /billed/);
});

test('application sid counts as routed', () => {
  assert.equal(verdict({ voice_application_sid: 'AP0123456789' })[0], 'configured');
});

test('hostAndPath drops scheme, credentials and query', () => {
  assert.equal(hostAndPath('https://user@Demo.Twilio.com/docs/voice.xml?a=b'),
               'demo.twilio.com/docs/voice.xml');
});
''',
"faq": [
 ("Why is there no error code for this?",
  "Because nothing failed. Twilio fetched a URL, received 200 with well-formed TwiML, and executed it. The demo endpoint is a healthy web server, so there is no 11200, no Debugger alert and no failed call to count. Error-based monitoring cannot see this class of problem at all."),
 ("Where does the demo URL come from if nobody set it?",
  "Twilio provisions newly purchased numbers with voice_url pointing at https://demo.twilio.com/docs/voice.xml so the number does something rather than erroring. Pointing it at your own application is a separate step, and it is the one that gets skipped."),
 ("Is a TwiML Bin a real problem, or a false positive?",
  "It depends on intent, which is why it gets its own state rather than being folded into the demo one. A Bin serving a deliberate static greeting is fine. A Bin created during a quickstart, on a number your application was supposed to answer, is the same failure wearing a different URL."),
 ("Should a number with no webhook at all be in this report?",
  "Yes. Same cause, same fix, and it is billed every month for answering nothing. Keeping it in the same run is how you find out that three of the forty numbers on the account have never been wired to anything."),
 ("Can the script fix the numbers it finds?",
  "It will not. Rewriting a live number's voice_url from a cron job is how a working phone line goes down at 3am. It prints the exact POST, with the resource SID and the field, for a human to run and watch."),
],
"related": [
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS disappears into a blank sms_url"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_PN, CITE_TWIML_VOICE, CITE_WEBHOOKS, CITE_KEYS],
},

{
"slug": "inbound-webhook-black-hole",
"title": "Inbound SMS disappears into a number with no sms_url",
"description": "The Messaging Service has an inbound URL and it is being ignored. Deferring to the sender's webhook means a blank sms_url on the number drops every reply.",
"h1": "inbound SMS disappears into a number with no sms_url",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio inbound sms not received", "use_inbound_webhook_on_number",
             "inbound_request_url ignored", "twilio stop replies missing",
             "messaging service inbound webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Outbound works perfectly. Replies do not arrive. There is no 4xx, no entry in the Debugger, no request in your access log &mdash; the inbound message is accepted by Twilio, matched to a number, and then delivered to nowhere. The STOP replies vanish the same way, which is the part that eventually costs money.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}</code> and look at <code>use_inbound_webhook_on_number</code>. When it is <code>true</code>, the <em>number's</em> <code>sms_url</code> wins and the service's <code>inbound_request_url</code> is ignored entirely &mdash; so any pool number with a blank <code>sms_url</code> silently drops inbound traffic.</p>
<p>The inverse black-holes the whole pool at once: <code>use_inbound_webhook_on_number</code> <code>false</code> with <code>inbound_request_url</code> unset. Join the pool from <code>GET /v1/Services/{ServiceSid}/PhoneNumbers</code> to <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> to see which numbers actually have a handler.</p>""",
"problem": """<p>Inbound messages that go nowhere produce no evidence anywhere. Twilio has no failing HTTP request to log, because it never made one. Your server has no request to trace, because none arrived. The message itself exists &mdash; it is in the Messages list, <code>direction</code> of <code>inbound</code>, looking entirely normal &mdash; but the webhook that was supposed to hand it to your application was never called.</p>
<p>The bill for this is not the missed conversations. It is the STOP replies. An opt-out that never reaches your database means you keep sending to someone who asked you to stop; Twilio still honours the opt-out and rejects the sends with <code>21610</code>, so you find out eventually, but by then you have a compliance problem with a start date rather than a bug.</p>""",
"why": """<p><strong>The setting inverts which URL wins, and it is on by default.</strong> "Defer to sender's webhook" reads like a fallback and is not one. When <code>use_inbound_webhook_on_number</code> is <code>true</code>, the number's <code>sms_url</code> is the handler and the service's <code>inbound_request_url</code> is dead configuration &mdash; still there, still visible in the API and console, doing nothing.</p>
<p><strong>Configuring the service feels like configuring the numbers.</strong> That is the whole appeal of a Messaging Service: one place for pool, opt-out, callbacks. Setting <code>inbound_request_url</code> there is the natural act, it succeeds, and the value is displayed back to you. Nothing indicates it is being overridden per number.</p>
<p><strong>It breaks per number, not per service.</strong> The numbers that were bought and wired individually work. The ones added later, or moved in from another service, carry a blank <code>sms_url</code> and drop everything. So inbound "works" in testing, on whichever number the tester happened to use.</p>
<p><strong>The two fields live in different APIs.</strong> The service is on <code>messaging.twilio.com/v1</code>; <code>sms_url</code> is on the 2010-04-01 account API; the pool listing gives you SIDs but not handler URLs. No single response shows the failure, so you have to join three of them before it is even visible.</p>""",
"steps": [
 {"h": "Read the routing mode on every service",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code>, then per service read <code>use_inbound_webhook_on_number</code>, <code>inbound_request_url</code> and <code>fallback_url</code>. Those three fields determine which of the two failure modes you are looking for.</p>"""},
 {"h": "Catch the whole-pool case first",
  "body": """<p><code>use_inbound_webhook_on_number</code> <code>false</code> with an empty <code>inbound_request_url</code> drops inbound for every number in the pool at once. It is one comparison, it is the more damaging of the two, and it needs no join to detect.</p>"""},
 {"h": "Join the pool to the numbers",
  "body": """<p><code>GET /v1/Services/{ServiceSid}/PhoneNumbers</code> returns <code>PN</code> SIDs and E.164 numbers but not handler URLs. Build a map from <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> keyed on <code>sid</code> and look each pool member up in it. A pool member that is not in the map belongs to a subaccount; report it as unresolved rather than as broken.</p>"""},
 {"h": "Flag blank sms_url, then blank sms_fallback_url",
  "body": """<p>A blank <code>sms_url</code> while the service defers to the number is the black hole. A populated <code>sms_url</code> with a blank <code>sms_fallback_url</code> is the lesser finding: inbound works until your endpoint returns non-2xx, and then that message is lost too.</p>"""},
 {"h": "Pick one place to route inbound, and make it true everywhere",
  "body": """<p>Either centralise &mdash; <code>POST /v1/Services/{ServiceSid}</code> with <code>UseInboundWebhookOnNumber=false</code> and <code>InboundRequestUrl</code> &mdash; or set <code>SmsUrl</code> on every number in the pool. Half-and-half is what produced this. Re-run the audit after adding a number to the pool, because that is when it recurs.</p>"""},
],
"verify": """<p>Re-run the script. Every service should report <code>routed</code> or <code>centralised</code>, and no number should appear as a black hole.</p>
<pre><code class="language-bash">python3 twilio_inbound_route_audit.py
# 3 service(s), 0 dropping inbound messages</code></pre>""",
"code_intro": "Three GETs and a join: the services, each service's pool, and the account's numbers &mdash; all read with an API Key that has read access and nothing more. The routing rule is a pure function taking the service and its resolved pool, because which URL actually wins is the entire content of this note and it should be readable in one screen.",
"py_file": "twilio_inbound_route_audit.py",
"py": '''"""Report Messaging Services whose inbound messages are routed nowhere.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_inbound_route_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"


def verdict(service, pool):
    """Decide where a Messaging Service's inbound messages actually land.

    `service` is the Messaging Service resource. `pool` is its sender pool with
    each number already joined to its IncomingPhoneNumber record, so every entry
    carries `phone_number`, `sms_url` and `sms_fallback_url`.

    Pure, so the precedence rule can be tested without a network. Returns
    (state, detail).
    """
    defers = bool(service.get("use_inbound_webhook_on_number"))
    inbound = str(service.get("inbound_request_url") or "").strip()

    if not defers:
        if not inbound:
            return ("service-black-hole",
                    "use_inbound_webhook_on_number is false and "
                    "inbound_request_url is empty: inbound to all %d pool "
                    "number(s) is dropped." % len(pool))
        return ("centralised",
                "all inbound goes to the service URL; the numbers' sms_url "
                "values are ignored.")

    if not pool:
        return ("empty-pool",
                "defers to the sender's webhook, but the pool has no numbers.")

    blank = [n.get("phone_number", "?") for n in pool
             if not str(n.get("sms_url") or "").strip()]
    if blank:
        detail = ("%d of %d pool number(s) have a blank sms_url and the service "
                  "defers to the number, so inbound to %s is dropped."
                  % (len(blank), len(pool), ", ".join(blank[:5])))
        if inbound:
            detail += " inbound_request_url is set but ignored."
        return ("number-black-hole", detail)

    no_fallback = [n.get("phone_number", "?") for n in pool
                   if not str(n.get("sms_fallback_url") or "").strip()]
    if no_fallback:
        return ("no-fallback",
                "every number has an sms_url, but %d have no sms_fallback_url: "
                "one non-2xx and that message is gone." % len(no_fallback))

    return ("routed", "all %d pool number(s) have their own sms_url" % len(pool))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def list_numbers(session, account, limit=1000):
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
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

    services = list_v1(session, MSG + "/Services", "services", args.max_services)
    if not services:
        log.info("no Messaging Services on this account")
        return 0

    by_sid = {n.get("sid"): n for n in list_numbers(session, account)}

    bad = 0
    for svc in services:
        members = list_v1(session, "%s/Services/%s/PhoneNumbers" % (MSG, svc["sid"]),
                          "phone_numbers")
        pool, unresolved = [], []
        for m in members:
            record = by_sid.get(m.get("sid"))
            (pool if record else unresolved).append(record or m)

        state, detail = verdict(svc, pool)
        line = "%-18s %s  %s" % (state, svc.get("friendly_name", svc["sid"]), detail)
        if unresolved:
            log.info("%s: %d pool number(s) live in another account, not read",
                     svc["sid"], len(unresolved))
        if state in ("routed", "centralised"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "service-black-hole":
            log.warning("  repair: POST %s/Services/%s "
                        "InboundRequestUrl=https://your-app.example.com/twilio/inbound",
                        MSG, svc["sid"])
        elif state == "number-black-hole":
            log.warning("  repair: set SmsUrl on each number, or POST %s/Services/%s "
                        "UseInboundWebhookOnNumber=false with an InboundRequestUrl",
                        MSG, svc["sid"])

    log.info("%d service(s), %d dropping inbound messages", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-inbound-route-audit.mjs",
"js": '''/**
 * Report Messaging Services whose inbound messages are routed nowhere.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';

/**
 * Decide where a Messaging Service's inbound messages actually land.
 *
 * `service` is the Messaging Service resource; `pool` is its sender pool with
 * each number already joined to its IncomingPhoneNumber record. Pure, so the
 * precedence rule can be tested without a network. Returns [state, detail].
 */
export function verdict(service, pool) {
  const defers = Boolean(service.use_inbound_webhook_on_number);
  const inbound = String(service.inbound_request_url ?? '').trim();

  if (!defers) {
    if (!inbound) {
      return ['service-black-hole',
        'use_inbound_webhook_on_number is false and inbound_request_url is ' +
        `empty: inbound to all ${pool.length} pool number(s) is dropped.`];
    }
    return ['centralised',
      "all inbound goes to the service URL; the numbers' sms_url values are ignored."];
  }

  if (pool.length === 0) {
    return ['empty-pool', "defers to the sender's webhook, but the pool has no numbers."];
  }

  const blank = pool.filter((n) => !String(n.sms_url ?? '').trim())
                    .map((n) => n.phone_number ?? '?');
  if (blank.length) {
    return ['number-black-hole',
      `${blank.length} of ${pool.length} pool number(s) have a blank sms_url ` +
      `and the service defers to the number, so inbound to ${blank.slice(0, 5).join(', ')} ` +
      `is dropped.${inbound ? ' inbound_request_url is set but ignored.' : ''}`];
  }

  const noFallback = pool.filter((n) => !String(n.sms_fallback_url ?? '').trim());
  if (noFallback.length) {
    return ['no-fallback',
      `every number has an sms_url, but ${noFallback.length} have no ` +
      'sms_fallback_url: one non-2xx and that message is gone.'];
  }

  return ['routed', `all ${pool.length} pool number(s) have their own sms_url`];
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

export async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
  }
  return out.slice(0, limit);
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

  const services = await listV1(auth, `${MSG}/Services`, 'services');
  if (services.length === 0) {
    console.log('no Messaging Services on this account');
    return;
  }

  const bySid = new Map((await listNumbers(auth, account)).map((n) => [n.sid, n]));

  let bad = 0;
  for (const svc of services) {
    const members = await listV1(auth, `${MSG}/Services/${svc.sid}/PhoneNumbers`,
                                 'phone_numbers');
    const pool = [];
    let unresolved = 0;
    for (const m of members) {
      const record = bySid.get(m.sid);
      if (record) pool.push(record); else unresolved += 1;
    }

    const [state, detail] = verdict(svc, pool);
    const line = `${state.padEnd(18)} ${svc.friendly_name ?? svc.sid}  ${detail}`;
    if (unresolved) {
      console.log(`${svc.sid}: ${unresolved} pool number(s) live in another account, not read`);
    }
    if (state === 'routed' || state === 'centralised') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'service-black-hole') {
      console.warn(`  repair: POST ${MSG}/Services/${svc.sid} ` +
                   'InboundRequestUrl=https://your-app.example.com/twilio/inbound');
    } else if (state === 'number-black-hole') {
      console.warn(`  repair: set SmsUrl on each number, or POST ${MSG}/Services/` +
                   `${svc.sid} UseInboundWebhookOnNumber=false with an InboundRequestUrl`);
    }
  }

  console.log(`${services.length} service(s), ${bad} dropping inbound messages`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters is the one where the service has a perfectly good <code>inbound_request_url</code> and the pool number does not have an <code>sms_url</code>. Everything about that service reads as configured; it is the precedence rule that makes it a black hole, so the classifier has to report it as broken while the field is populated.",
"test_py_file": "test_twilio_inbound_route_audit.py",
"test_py": '''from twilio_inbound_route_audit import verdict

SERVICE_URL = "https://app.example.com/twilio/inbound"
NUMBER_URL = "https://app.example.com/sms"


def test_service_url_is_ignored_when_the_service_defers_to_the_number():
    # The point of the note: inbound_request_url is set and it does not matter.
    state, detail = verdict(
        {"use_inbound_webhook_on_number": True, "inbound_request_url": SERVICE_URL},
        [{"phone_number": "+15550001111", "sms_url": ""}])
    assert state == "number-black-hole"
    assert "ignored" in detail


def test_false_with_no_inbound_url_drops_the_whole_pool():
    state, detail = verdict(
        {"use_inbound_webhook_on_number": False, "inbound_request_url": None},
        [{"phone_number": "+15550001111", "sms_url": NUMBER_URL}])
    assert state == "service-black-hole"
    assert "all 1 pool number(s)" in detail


def test_centralised_routing_is_healthy_even_with_blank_number_urls():
    state, _ = verdict(
        {"use_inbound_webhook_on_number": False, "inbound_request_url": SERVICE_URL},
        [{"phone_number": "+15550001111", "sms_url": ""}])
    assert state == "centralised"


def test_one_bad_number_among_good_ones_is_still_reported():
    state, detail = verdict(
        {"use_inbound_webhook_on_number": True, "inbound_request_url": ""},
        [{"phone_number": "+15550001111", "sms_url": NUMBER_URL,
          "sms_fallback_url": NUMBER_URL},
         {"phone_number": "+15550002222", "sms_url": None}])
    assert state == "number-black-hole"
    assert "+15550002222" in detail


def test_missing_fallback_is_the_lesser_finding_not_the_black_hole():
    state, _ = verdict(
        {"use_inbound_webhook_on_number": True},
        [{"phone_number": "+15550001111", "sms_url": NUMBER_URL,
          "sms_fallback_url": ""}])
    assert state == "no-fallback"


def test_fully_wired_pool_is_routed():
    state, _ = verdict(
        {"use_inbound_webhook_on_number": True},
        [{"phone_number": "+15550001111", "sms_url": NUMBER_URL,
          "sms_fallback_url": NUMBER_URL}])
    assert state == "routed"


def test_empty_pool_is_not_reported_as_routed():
    state, _ = verdict({"use_inbound_webhook_on_number": True}, [])
    assert state == "empty-pool"
''',
"test_js_file": "twilio-inbound-route-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './twilio-inbound-route-audit.mjs';

const SERVICE_URL = 'https://app.example.com/twilio/inbound';
const NUMBER_URL = 'https://app.example.com/sms';

test('service url is ignored when the service defers to the number', () => {
  const [state, detail] = verdict(
    { use_inbound_webhook_on_number: true, inbound_request_url: SERVICE_URL },
    [{ phone_number: '+15550001111', sms_url: '' }]);
  assert.equal(state, 'number-black-hole');
  assert.match(detail, /ignored/);
});

test('false with no inbound url drops the whole pool', () => {
  const [state, detail] = verdict(
    { use_inbound_webhook_on_number: false, inbound_request_url: null },
    [{ phone_number: '+15550001111', sms_url: NUMBER_URL }]);
  assert.equal(state, 'service-black-hole');
  assert.match(detail, /all 1 pool number\\(s\\)/);
});

test('centralised routing is healthy even with blank number urls', () => {
  const [state] = verdict(
    { use_inbound_webhook_on_number: false, inbound_request_url: SERVICE_URL },
    [{ phone_number: '+15550001111', sms_url: '' }]);
  assert.equal(state, 'centralised');
});

test('one bad number among good ones is still reported', () => {
  const [state, detail] = verdict(
    { use_inbound_webhook_on_number: true, inbound_request_url: '' },
    [{ phone_number: '+15550001111', sms_url: NUMBER_URL, sms_fallback_url: NUMBER_URL },
     { phone_number: '+15550002222', sms_url: null }]);
  assert.equal(state, 'number-black-hole');
  assert.match(detail, /\\+15550002222/);
});

test('missing fallback is the lesser finding, not the black hole', () => {
  const [state] = verdict(
    { use_inbound_webhook_on_number: true },
    [{ phone_number: '+15550001111', sms_url: NUMBER_URL, sms_fallback_url: '' }]);
  assert.equal(state, 'no-fallback');
});

test('fully wired pool is routed', () => {
  const [state] = verdict(
    { use_inbound_webhook_on_number: true },
    [{ phone_number: '+15550001111', sms_url: NUMBER_URL, sms_fallback_url: NUMBER_URL }]);
  assert.equal(state, 'routed');
});

test('empty pool is not reported as routed', () => {
  assert.equal(verdict({ use_inbound_webhook_on_number: true }, [])[0], 'empty-pool');
});
''',
"faq": [
 ("What does use_inbound_webhook_on_number actually change?",
  "Which URL Twilio calls for an inbound message. True means the number's sms_url handles it and the service's inbound_request_url is ignored. False means the service's URL handles everything in the pool and the numbers' own sms_url values are ignored. It is a switch between two routes, not a fallback chain."),
 ("Why is there nothing in the Debugger?",
  "Because no HTTP request failed. With no handler URL there is nothing for Twilio to call, so there is no 11200 and no alert. The inbound message still appears in the Messages list with direction inbound, which is the only trace that it existed at all."),
 ("How does this end up as a compliance problem?",
  "STOP replies are inbound messages. If they never reach your application, your database never records the opt-out and your sends keep going. Twilio blocks them with 21610 so the recipient is protected, but your own records show consent you no longer have."),
 ("Should I centralise on the service or configure each number?",
  "Either works; mixing them is what produces this. Centralising is one field for the whole pool and one place to change when the endpoint moves, which is why it survives a number being added later. Per-number routing is right when different numbers genuinely belong to different applications."),
 ("Why does the script join three API responses instead of one?",
  "Because no single response contains the failure. The routing mode is on the Messaging Service, the pool membership is a subresource of it, and sms_url lives on the number in the 2010-04-01 account API. The bug is only visible where the three meet."),
],
"related": [
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still points at the demo TwiML"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_SERVICE, CITE_SERVICE_PN, CITE_PN, CITE_WEBHOOKS],
},

{
"slug": "messaging-service-not-a2p-registered",
"title": "A Messaging Service with no A2P campaign fails US sends",
"description": "us_app_to_person_registered is false, so every US 10DLC send returns 30034. The service accepts numbers and API calls happily; only the message fails.",
"h1": "a Messaging Service with no A2P campaign fails US sends",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30034", "us_app_to_person_registered",
             "a2p 10dlc not registered", "messaging service campaign missing",
             "twilio unregistered number"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Staging was cloned from production last quarter and it has worked ever since &mdash; until the new tenant went live and every US message came back <code>30034</code>. The brand is approved. The campaign is verified. Neither of them is attached to <em>this</em> Messaging Service, because A2P registration is per service and nobody registers the second one.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Services</code> and flag every service where <code>us_app_to_person_registered</code> is <code>false</code>. That single boolean is the fastest account-wide way to find unregistered services.</p>
<p>Confirm each with <code>GET /v1/Services/{ServiceSid}/Compliance/Usa2p</code>, which returns an empty list when no campaign is attached. Then count the US long codes in <code>GET /v1/Services/{ServiceSid}/PhoneNumbers</code> &mdash; an unregistered service with US senders is failing right now; one with none is a ticket for before launch.</p>""",
"problem": """<p>Nothing about an unregistered Messaging Service looks unregistered. You can create it, name it, add numbers to it, set its callbacks, and call the API against it, and every one of those operations succeeds. The service is a perfectly valid object. It is only at the moment a US message is handed to a carrier that the missing campaign matters, and by then you are looking at a delivery failure rather than a configuration error.</p>
<p>What makes it expensive is the shape of the failure: <code>30034</code> comes back per message, at send time, in production. A service created for staging, or for a new tenant, or as part of a migration, carries no warning that it is not the registered one. The team sees the brand approved in the console, concludes registration is done, and ships.</p>""",
"why": """<p><strong>Registration attaches to the service, not to the account.</strong> One approved brand can sit behind many Messaging Services, and each one needs its own campaign. "We are registered" is true of the account and false of the service that is actually sending.</p>
<p><strong>Cloning a service does not clone its campaign.</strong> Copying the settings that show in the console &mdash; pool, opt-out, callbacks &mdash; produces something that looks identical and is missing the one attribute you cannot see there.</p>
<p><strong>The failure is per message, not at configuration time.</strong> Adding a US long code to an unregistered service returns 201. Twilio will not stop you assembling a service that cannot send; the carrier rejects the traffic later.</p>
<p><strong>A registered flag is not a healthy campaign.</strong> <code>us_app_to_person_registered</code> can be <code>true</code> while the campaign underneath is <code>IN_PROGRESS</code>, <code>FAILED</code> or <code>SUSPENDED</code>. Reading only the boolean turns a suspended campaign into a green tick, so the campaign status has to be read as well.</p>""",
"steps": [
 {"h": "Sweep every service for the boolean",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services</code> and read <code>us_app_to_person_registered</code> on each. This is one paginated GET for the whole account and it is the check to put on a schedule, because the failure arrives with a service somebody created last week.</p>"""},
 {"h": "Confirm with the campaign subresource",
  "body": """<p><code>GET /v1/Services/{ServiceSid}/Compliance/Usa2p</code> returns the campaign objects under <code>compliance</code>. An empty list confirms the boolean. A non-empty list with <code>us_app_to_person_registered</code> false, or the reverse, is a disagreement worth reporting rather than resolving in favour of whichever you read first.</p>"""},
 {"h": "Read campaign_status, not just presence",
  "body": """<p>A campaign exists in several states that are not <code>VERIFIED</code>. <code>IN_PROGRESS</code> means it is not live yet, <code>FAILED</code> means it never will be without changes, and <code>SUSPENDED</code> usually means the brand above it is suspended. All three send exactly like an unregistered service.</p>"""},
 {"h": "Count the US senders to decide urgency",
  "body": """<p><code>GET /v1/Services/{ServiceSid}/PhoneNumbers</code> and count <code>+1</code> numbers that are not toll-free. Unregistered with US senders is a live outage; unregistered with none has not bitten yet and can be fixed before it does.</p>"""},
 {"h": "Register the service, then re-run",
  "body": """<p><code>POST /v1/Services/{ServiceSid}/Compliance/Usa2p</code> with <code>BrandRegistrationSid</code>, <code>Description</code>, <code>MessageFlow</code>, <code>MessageSamples</code>, <code>UsAppToPersonUsecase</code>, <code>HasEmbeddedLinks</code> and <code>HasEmbeddedPhone</code>. Carrier provisioning of the individual numbers takes up to a day afterwards, so re-run the audit tomorrow rather than treating the POST as the finish line.</p>"""},
],
"verify": """<p>Re-run the script. Every service with US senders should report <code>registered</code>, with a campaign in <code>VERIFIED</code>.</p>
<pre><code class="language-bash">python3 twilio_a2p_registration_audit.py
# 4 service(s), 0 unable to send to US numbers</code></pre>""",
"code_intro": "One paginated GET for the services and two per service for its campaign and its pool &mdash; all reads, with an API Key that has read access and nothing more. The classifier takes the service, the campaign list and the US sender count together, because the same missing campaign is a ticket on an empty service and an outage on one that is sending.",
"py_file": "twilio_a2p_registration_audit.py",
"py": '''"""Report Messaging Services that cannot send to US numbers under A2P 10DLC.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The registration is printed, never
performed, because this script holds a credential to an account that can send
messages and spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_a2p_registration_audit")

MSG = "https://messaging.twilio.com/v1"

TOLL_FREE = ("800", "833", "844", "855", "866", "877", "888")


def us_long_codes(pool):
    """Count the senders 10DLC registration actually governs.

    Pure. Toll-free numbers are verified separately and short codes are not
    10DLC at all, so counting every +1 in the pool overstates the exposure.
    """
    out = []
    for n in pool:
        number = str(n.get("phone_number") or "")
        if not number.startswith("+1") or len(number) != 12:
            continue
        if number[2:5] in TOLL_FREE:
            continue
        out.append(number)
    return out


def verdict(service, campaigns, us_senders):
    """Classify one Messaging Service's A2P standing. Pure, so the states can be
    tested without a network.

    `campaigns` is the list from Compliance/Usa2p; `us_senders` is the count of
    US long codes in its pool. Returns (state, detail).
    """
    registered = bool(service.get("us_app_to_person_registered"))
    campaign = campaigns[0] if campaigns else None

    if campaign is None:
        if registered:
            return ("inconsistent",
                    "us_app_to_person_registered is true but Compliance/Usa2p "
                    "returned no campaign. Trust the subresource, not the flag.")
        if us_senders:
            return ("blocked",
                    "no A2P campaign and %d US long code(s) in the pool: every "
                    "US send through this service returns 30034." % us_senders)
        return ("unregistered",
                "no A2P campaign. No US long codes in the pool yet, so nothing "
                "is failing; register before one is added.")

    status = str(campaign.get("campaign_status") or "").upper()
    if status == "VERIFIED":
        if not registered:
            return ("inconsistent",
                    "campaign is VERIFIED but us_app_to_person_registered is "
                    "false. Trust the subresource, not the flag.")
        return ("registered", "campaign %s is VERIFIED" % campaign.get("sid", "?"))

    return ("campaign-%s" % (status.lower() or "unknown"),
            "a campaign exists but its status is %s, which sends exactly like "
            "no campaign at all (%d US long code(s) affected)."
            % (status or "unset", us_senders))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
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

    services = list_v1(session, MSG + "/Services", "services", args.max_services)
    if not services:
        log.info("no Messaging Services on this account")
        return 0

    bad = 0
    for svc in services:
        sid = svc["sid"]
        campaigns = list_v1(session, "%s/Services/%s/Compliance/Usa2p" % (MSG, sid),
                            "compliance")
        pool = list_v1(session, "%s/Services/%s/PhoneNumbers" % (MSG, sid),
                       "phone_numbers")
        state, detail = verdict(svc, campaigns, len(us_long_codes(pool)))

        line = "%-22s %s  %s" % (state, svc.get("friendly_name", sid), detail)
        if state == "registered":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("blocked", "unregistered"):
            log.warning("  repair: POST %s/Services/%s/Compliance/Usa2p with "
                        "BrandRegistrationSid, Description, MessageFlow, "
                        "MessageSamples, UsAppToPersonUsecase, HasEmbeddedLinks, "
                        "HasEmbeddedPhone", MSG, sid)

    log.info("%d service(s), %d unable to send to US numbers", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-registration-audit.mjs",
"js": '''/**
 * Report Messaging Services that cannot send to US numbers under A2P 10DLC.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The registration is printed, never
 * performed.
 */
const MSG = 'https://messaging.twilio.com/v1';

const TOLL_FREE = ['800', '833', '844', '855', '866', '877', '888'];

/**
 * Count the senders 10DLC registration actually governs. Pure: toll-free
 * numbers are verified separately and short codes are not 10DLC at all.
 */
export function usLongCodes(pool) {
  return pool
    .map((n) => String(n.phone_number ?? ''))
    .filter((n) => n.startsWith('+1') && n.length === 12 && !TOLL_FREE.includes(n.slice(2, 5)));
}

/**
 * Classify one Messaging Service's A2P standing. Pure, so the states can be
 * tested without a network. Returns [state, detail].
 */
export function verdict(service, campaigns, usSenders) {
  const registered = Boolean(service.us_app_to_person_registered);
  const campaign = campaigns && campaigns.length ? campaigns[0] : null;

  if (campaign === null) {
    if (registered) {
      return ['inconsistent',
        'us_app_to_person_registered is true but Compliance/Usa2p returned no ' +
        'campaign. Trust the subresource, not the flag.'];
    }
    if (usSenders) {
      return ['blocked',
        `no A2P campaign and ${usSenders} US long code(s) in the pool: every US ` +
        'send through this service returns 30034.'];
    }
    return ['unregistered',
      'no A2P campaign. No US long codes in the pool yet, so nothing is ' +
      'failing; register before one is added.'];
  }

  const status = String(campaign.campaign_status ?? '').toUpperCase();
  if (status === 'VERIFIED') {
    if (!registered) {
      return ['inconsistent',
        'campaign is VERIFIED but us_app_to_person_registered is false. Trust ' +
        'the subresource, not the flag.'];
    }
    return ['registered', `campaign ${campaign.sid ?? '?'} is VERIFIED`];
  }

  return [`campaign-${status.toLowerCase() || 'unknown'}`,
    `a campaign exists but its status is ${status || 'unset'}, which sends ` +
    `exactly like no campaign at all (${usSenders} US long code(s) affected).`];
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

export async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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

  const services = await listV1(auth, `${MSG}/Services`, 'services');
  if (services.length === 0) {
    console.log('no Messaging Services on this account');
    return;
  }

  let bad = 0;
  for (const svc of services) {
    const campaigns = await listV1(auth, `${MSG}/Services/${svc.sid}/Compliance/Usa2p`,
                                   'compliance');
    const pool = await listV1(auth, `${MSG}/Services/${svc.sid}/PhoneNumbers`,
                              'phone_numbers');
    const [state, detail] = verdict(svc, campaigns, usLongCodes(pool).length);

    const line = `${state.padEnd(22)} ${svc.friendly_name ?? svc.sid}  ${detail}`;
    if (state === 'registered') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'blocked' || state === 'unregistered') {
      console.warn(`  repair: POST ${MSG}/Services/${svc.sid}/Compliance/Usa2p with ` +
                   'BrandRegistrationSid, Description, MessageFlow, MessageSamples, ' +
                   'UsAppToPersonUsecase, HasEmbeddedLinks, HasEmbeddedPhone');
    }
  }

  console.log(`${services.length} service(s), ${bad} unable to send to US numbers`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. A campaign that exists but is not <code>VERIFIED</code> has to be as loud as no campaign at all, because it sends identically. And an unregistered service with no US senders has to stay separate from one with senders: same missing campaign, but only one of them is currently losing messages.",
"test_py_file": "test_twilio_a2p_registration_audit.py",
"test_py": '''from twilio_a2p_registration_audit import us_long_codes, verdict

REGISTERED = {"us_app_to_person_registered": True}
UNREGISTERED = {"us_app_to_person_registered": False}
VERIFIED = [{"sid": "QE0123456789", "campaign_status": "VERIFIED"}]


def test_unregistered_with_us_senders_is_an_outage():
    state, detail = verdict(UNREGISTERED, [], 3)
    assert state == "blocked"
    assert "30034" in detail


def test_unregistered_with_no_us_senders_is_not_the_same_finding():
    # Same missing campaign, but nothing is failing yet. Keeping these apart is
    # what makes the report worth reading on a big account.
    state, _ = verdict(UNREGISTERED, [], 0)
    assert state == "unregistered"


def test_verified_campaign_and_flag_agree():
    state, detail = verdict(REGISTERED, VERIFIED, 3)
    assert state == "registered"
    assert "QE0123456789" in detail


def test_campaign_in_progress_sends_like_no_campaign():
    state, detail = verdict(REGISTERED, [{"campaign_status": "IN_PROGRESS"}], 2)
    assert state == "campaign-in_progress"
    assert "no campaign at all" in detail


def test_suspended_campaign_is_not_reported_as_registered():
    state, _ = verdict(REGISTERED, [{"campaign_status": "SUSPENDED"}], 1)
    assert state == "campaign-suspended"


def test_flag_disagreeing_with_the_subresource_is_reported():
    state, _ = verdict(REGISTERED, [], 1)
    assert state == "inconsistent"


def test_toll_free_and_short_codes_are_not_10dlc_senders():
    pool = [{"phone_number": "+15550001111"}, {"phone_number": "+18885551234"},
            {"phone_number": "+447700900123"}, {"phone_number": "12345"}]
    assert us_long_codes(pool) == ["+15550001111"]
''',
"test_js_file": "twilio-a2p-registration-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { usLongCodes, verdict } from './twilio-a2p-registration-audit.mjs';

const REGISTERED = { us_app_to_person_registered: true };
const UNREGISTERED = { us_app_to_person_registered: false };
const VERIFIED = [{ sid: 'QE0123456789', campaign_status: 'VERIFIED' }];

test('unregistered with us senders is an outage', () => {
  const [state, detail] = verdict(UNREGISTERED, [], 3);
  assert.equal(state, 'blocked');
  assert.match(detail, /30034/);
});

test('unregistered with no us senders is not the same finding', () => {
  assert.equal(verdict(UNREGISTERED, [], 0)[0], 'unregistered');
});

test('verified campaign and flag agree', () => {
  const [state, detail] = verdict(REGISTERED, VERIFIED, 3);
  assert.equal(state, 'registered');
  assert.match(detail, /QE0123456789/);
});

test('campaign in progress sends like no campaign', () => {
  const [state, detail] = verdict(REGISTERED, [{ campaign_status: 'IN_PROGRESS' }], 2);
  assert.equal(state, 'campaign-in_progress');
  assert.match(detail, /no campaign at all/);
});

test('suspended campaign is not reported as registered', () => {
  assert.equal(verdict(REGISTERED, [{ campaign_status: 'SUSPENDED' }], 1)[0],
               'campaign-suspended');
});

test('flag disagreeing with the subresource is reported', () => {
  assert.equal(verdict(REGISTERED, [], 1)[0], 'inconsistent');
});

test('toll free and short codes are not 10dlc senders', () => {
  const pool = [{ phone_number: '+15550001111' }, { phone_number: '+18885551234' },
                { phone_number: '+447700900123' }, { phone_number: '12345' }];
  assert.deepEqual(usLongCodes(pool), ['+15550001111']);
});
''',
"faq": [
 ("Our brand is approved. Why is this service still failing?",
  "Because A2P registration attaches to the Messaging Service, not to the account or the brand. One approved brand can sit behind several services, and each needs its own campaign. A service created for staging or a new tenant starts with none."),
 ("What exactly does 30034 mean?",
  "The message was sent from a US long code that carriers do not recognise as belonging to a registered campaign. It is a carrier-side rejection at send time, so it appears per message rather than as a configuration error you could have caught earlier."),
 ("Is us_app_to_person_registered enough on its own?",
  "It is enough to find the unregistered services quickly, which is why the sweep starts there. It is not enough to declare one healthy: the flag can be true while the campaign underneath is IN_PROGRESS, FAILED or SUSPENDED, all of which send exactly like no campaign."),
 ("Does sending with an explicit From number avoid this?",
  "No, it makes it worse. A bare From bypasses the Messaging Service entirely, so the number sends outside any registered campaign and gets the same 30034 with nothing to inspect. Send with MessagingServiceSid."),
 ("How long after registering can we send?",
  "The campaign has to reach VERIFIED, and then the individual numbers are provisioned with the carriers, which can take up to a day and shows as 30035 or 30024 in the meantime. Re-run the audit the next day rather than treating the POST as the finish line."),
],
"related": [
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS disappears into a blank sms_url"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still points at the demo TwiML"),
 ("/twilio/phone-number-missing-fallback-url/", "A number with no fallback URL drops the call"),
],
"citations": [CITE_USA2P, CITE_SERVICE, CITE_30034, CITE_SERVICE_PN],
},

{
"slug": "phone-number-missing-fallback-url",
"title": "A number with no fallback URL drops the call when yours 500s",
"description": "Twilio calls the fallback URL only when the primary handler errors. With none configured, one 11200 during a deploy is a lost customer call.",
"h1": "a number with no fallback URL drops the call when yours 500s",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio voice_fallback_url", "twilio sms_fallback_url",
             "twilio 11200 dropped call", "twilio fallback webhook",
             "twilio number fallback missing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Your webhook was down for ninety seconds during a deploy. Twilio requested it, got a 502, logged an <code>11200</code> and hung up on whoever was calling. There was a mitigation for exactly this, it costs one field on the number, and it is empty on every number you own.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code> and flag any number where <code>voice_url</code> is set but <code>voice_fallback_url</code> is empty &mdash; and the same for <code>sms_url</code> and <code>sms_fallback_url</code>.</p>
<p>Where <code>voice_application_sid</code> is populated it takes precedence and the number's own URLs are ignored, so the effective fallback lives on the app: read it from <code>GET /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json</code>. A check that skips that resolution reports the wrong answer on exactly the numbers most likely to be misconfigured.</p>""",
"problem": """<p>A missing fallback URL is invisible until the day it isn't. The number works, the handler answers, calls connect, and the field sits empty because nobody was ever asked to fill it in. Then a deploy takes ninety seconds, or a database connection pool exhausts, or a certificate expires, and Twilio has nowhere to go: it logs <code>11200</code> and terminates the interaction.</p>
<p>The cost lands entirely on the customer side of the line. Your monitoring sees an application outage of about a minute and calls it minor. What actually happened is that every caller in that minute heard silence or a fast busy and formed an opinion about your company, and no retry, alert or queue exists to recover them. Inbound calls are not messages: there is nothing to redeliver.</p>""",
"why": """<p><strong>The field is optional and empty by default.</strong> Nothing in the purchase flow, the API or the console requires it. A number with a primary handler looks fully configured, and the fallback is the field you only learn about after the first outage.</p>
<p><strong>Fallback is the one mitigation that works while your app is broken.</strong> Retries do not exist for inbound voice; the caller is on the line now. A static TwiML Bin that says "we are having trouble, please hold or call back" is a different experience from dead air, and it does not depend on the system that just failed.</p>
<p><strong>Application SIDs move the field somewhere else.</strong> When <code>voice_application_sid</code> is set it wins outright and <code>voice_url</code> is ignored, including its fallback. Teams then "fix" the fallback on the number, see no change in behaviour, and conclude fallbacks do not work.</p>
<p><strong>The gap spreads one number at a time.</strong> Numbers are bought individually, often in a hurry, and the console does not copy settings from an existing number. So an account ends up with two numbers that have fallbacks and eleven that do not, and no pattern to the difference.</p>""",
"steps": [
 {"h": "List every number and both channels",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, paging on <code>next_page_uri</code>. Voice and SMS are separate pairs of fields; a number can be protected on one and exposed on the other.</p>"""},
 {"h": "Resolve the Application SID before you judge the number",
  "body": """<p>If <code>voice_application_sid</code> or <code>sms_application_sid</code> is set, that resource is the effective handler. Fetch <code>GET /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json</code> once per SID, cache it, and read <code>voice_url</code> and <code>voice_fallback_url</code> from there instead.</p>"""},
 {"h": "Only flag channels that are actually in use",
  "body": """<p>A number with no primary handler on a channel has a different problem, and it belongs in a different report. The finding here is narrow on purpose: a live handler with no fallback behind it.</p>"""},
 {"h": "Point the fallback at something that cannot share your outage",
  "body": """<p>A fallback URL on the same host, behind the same load balancer, served by the same process is not a fallback. A TwiML Bin on <code>handler.twilio.com</code>, or a small static endpoint on separate infrastructure, is what makes the field worth setting.</p>"""},
 {"h": "Set it, then re-run",
  "body": """<p><code>POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json</code> with <code>VoiceFallbackUrl</code> and <code>VoiceFallbackMethod</code>, or the same on the Application. Then keep the audit on a schedule: the next number somebody buys will arrive without a fallback too.</p>"""},
],
"verify": """<p>Re-run the script. Every number with a live handler should report <code>covered</code>.</p>
<pre><code class="language-bash">python3 twilio_fallback_audit.py
# 12 number(s), 0 with an unprotected handler</code></pre>""",
"code_intro": "One paginated GET over the numbers, plus one GET per distinct Application SID, cached &mdash; an API Key with read access is enough. The precedence rule is in the pure function together with the fallback check, because reading the fallback off the number when an Application SID is set is the exact mistake this note exists to prevent.",
"py_file": "twilio_fallback_audit.py",
"py": '''"""Report Twilio numbers whose live handlers have no fallback URL.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_fallback_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

CHANNELS = (
    ("voice", "voice_url", "voice_fallback_url", "voice_application_sid"),
    ("sms", "sms_url", "sms_fallback_url", "sms_application_sid"),
)


def verdict(number, apps=None):
    """Classify one IncomingPhoneNumber. Pure, so the precedence rule can be
    tested without a network.

    `apps` maps an Application SID to that Application resource. When a channel
    has an application sid, the application is the effective handler and the
    number's own url and fallback are ignored entirely.

    Returns (state, detail).
    """
    apps = apps or {}
    exposed, covered, unresolved = [], [], []

    for channel, url_field, fb_field, app_field in CHANNELS:
        app_sid = str(number.get(app_field) or "").strip()
        if app_sid:
            source = apps.get(app_sid)
            if source is None:
                unresolved.append("%s (%s)" % (channel, app_sid))
                continue
            where = "app %s" % app_sid
        else:
            source, where = number, "the number"
        primary = str(source.get(url_field) or "").strip()
        fallback = str(source.get(fb_field) or "").strip()
        if not primary:
            continue
        (covered if fallback else exposed).append("%s on %s" % (channel, where))

    if unresolved:
        return ("unresolved",
                "an application sid is set but the application was not read: %s"
                % ", ".join(unresolved))
    if exposed:
        return ("exposed",
                "%s has a live handler and no fallback: one non-2xx and the "
                "interaction is dropped." % "; ".join(exposed))
    if covered:
        return ("covered", "fallback set for " + ", ".join(covered))
    return ("idle", "no voice or sms handler configured, so nothing to fall back from")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_numbers(session, account, limit):
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def load_apps(session, account, numbers):
    """Fetch each referenced Application once. A busy account points many numbers
    at the same app, so this is a handful of GETs rather than one per number."""
    sids = set()
    for n in numbers:
        for _c, _u, _f, app_field in CHANNELS:
            sid = str(n.get(app_field) or "").strip()
            if sid:
                sids.add(sid)
    apps = {}
    for sid in sorted(sids):
        apps[sid] = get(session, "%s/Accounts/%s/Applications/%s.json"
                        % (BASE, account, sid))
    return apps


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000)
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
    apps = load_apps(session, account, numbers)

    bad = 0
    for n in numbers:
        state, detail = verdict(n, apps)
        line = "%-10s %s  %s" % (state, n.get("phone_number", "?"), detail)
        if state in ("covered", "idle"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: POST %s/Accounts/%s/IncomingPhoneNumbers/%s.json "
                    "VoiceFallbackUrl=https://handler.twilio.com/twiml/EHxxx "
                    "VoiceFallbackMethod=POST", BASE, account, n.get("sid"))

    log.info("%d number(s), %d with an unprotected handler", len(numbers), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-fallback-audit.mjs",
"js": '''/**
 * Report Twilio numbers whose live handlers have no fallback URL.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const CHANNELS = [
  ['voice', 'voice_url', 'voice_fallback_url', 'voice_application_sid'],
  ['sms', 'sms_url', 'sms_fallback_url', 'sms_application_sid'],
];

/**
 * Classify one IncomingPhoneNumber. Pure, so the precedence rule can be tested
 * without a network. `apps` maps an Application SID to that Application: when a
 * channel has one, it is the effective handler and the number's own url and
 * fallback are ignored entirely. Returns [state, detail].
 */
export function verdict(number, apps = {}) {
  const exposed = [];
  const covered = [];
  const unresolved = [];

  for (const [channel, urlField, fbField, appField] of CHANNELS) {
    const appSid = String(number[appField] ?? '').trim();
    let source = number;
    let where = 'the number';
    if (appSid) {
      source = apps[appSid];
      if (source === undefined) { unresolved.push(`${channel} (${appSid})`); continue; }
      where = `app ${appSid}`;
    }
    const primary = String(source[urlField] ?? '').trim();
    const fallback = String(source[fbField] ?? '').trim();
    if (!primary) continue;
    (fallback ? covered : exposed).push(`${channel} on ${where}`);
  }

  if (unresolved.length) {
    return ['unresolved',
      `an application sid is set but the application was not read: ${unresolved.join(', ')}`];
  }
  if (exposed.length) {
    return ['exposed',
      `${exposed.join('; ')} has a live handler and no fallback: one non-2xx ` +
      'and the interaction is dropped.'];
  }
  if (covered.length) return ['covered', `fallback set for ${covered.join(', ')}`];
  return ['idle', 'no voice or sms handler configured, so nothing to fall back from'];
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

async function loadApps(auth, account, numbers) {
  const sids = new Set();
  for (const n of numbers) {
    for (const [, , , appField] of CHANNELS) {
      const sid = String(n[appField] ?? '').trim();
      if (sid) sids.add(sid);
    }
  }
  const apps = {};
  for (const sid of [...sids].sort()) {
    apps[sid] = await get(auth, `${BASE}/Accounts/${account}/Applications/${sid}.json`);
  }
  return apps;
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

  const numbers = await listNumbers(auth, account);
  if (numbers.length === 0) {
    console.log('no phone numbers on this account');
    return;
  }
  const apps = await loadApps(auth, account, numbers);

  let bad = 0;
  for (const n of numbers) {
    const [state, detail] = verdict(n, apps);
    const line = `${state.padEnd(10)} ${n.phone_number ?? '?'}  ${detail}`;
    if (state === 'covered' || state === 'idle') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: POST ${BASE}/Accounts/${account}/IncomingPhoneNumbers/` +
                 `${n.sid}.json VoiceFallbackUrl=https://handler.twilio.com/twiml/EHxxx ` +
                 'VoiceFallbackMethod=POST');
  }

  console.log(`${numbers.length} number(s), ${bad} with an unprotected handler`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that has to be right is the number with an Application SID: a fallback set on the number itself is ignored, so a classifier that reads the number's fields reports it as protected when it is not. The mirror case matters too &mdash; the fallback on the app counts, even though the number's own field is empty.",
"test_py_file": "test_twilio_fallback_audit.py",
"test_py": '''from twilio_fallback_audit import verdict

APP = "AP0123456789"


def test_live_voice_handler_with_no_fallback_is_exposed():
    state, detail = verdict({"voice_url": "https://app.example.com/voice"})
    assert state == "exposed"
    assert "dropped" in detail


def test_fallback_on_the_number_is_covered():
    state, _ = verdict({"voice_url": "https://app.example.com/voice",
                        "voice_fallback_url": "https://handler.twilio.com/twiml/EH1"})
    assert state == "covered"


def test_application_sid_wins_so_a_fallback_on_the_number_does_not_count():
    # The mistake this note exists to prevent: the number looks protected and is not.
    state, detail = verdict(
        {"voice_application_sid": APP,
         "voice_url": "https://app.example.com/voice",
         "voice_fallback_url": "https://handler.twilio.com/twiml/EH1"},
        {APP: {"voice_url": "https://app.example.com/voice"}})
    assert state == "exposed"
    assert APP in detail


def test_fallback_on_the_application_counts():
    state, _ = verdict(
        {"voice_application_sid": APP},
        {APP: {"voice_url": "https://app.example.com/voice",
               "voice_fallback_url": "https://handler.twilio.com/twiml/EH1"}})
    assert state == "covered"


def test_sms_is_checked_when_voice_is_fine():
    state, detail = verdict({"voice_url": "https://app.example.com/voice",
                             "voice_fallback_url": "https://handler.twilio.com/twiml/EH1",
                             "sms_url": "https://app.example.com/sms"})
    assert state == "exposed"
    assert "sms" in detail


def test_number_with_no_handler_is_idle_not_exposed():
    state, _ = verdict({"voice_url": "", "sms_url": None})
    assert state == "idle"


def test_unread_application_is_not_guessed_at():
    state, _ = verdict({"voice_application_sid": APP}, {})
    assert state == "unresolved"
''',
"test_js_file": "twilio-fallback-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './twilio-fallback-audit.mjs';

const APP = 'AP0123456789';

test('live voice handler with no fallback is exposed', () => {
  const [state, detail] = verdict({ voice_url: 'https://app.example.com/voice' });
  assert.equal(state, 'exposed');
  assert.match(detail, /dropped/);
});

test('fallback on the number is covered', () => {
  const [state] = verdict({
    voice_url: 'https://app.example.com/voice',
    voice_fallback_url: 'https://handler.twilio.com/twiml/EH1',
  });
  assert.equal(state, 'covered');
});

test('application sid wins, so a fallback on the number does not count', () => {
  const [state, detail] = verdict(
    { voice_application_sid: APP,
      voice_url: 'https://app.example.com/voice',
      voice_fallback_url: 'https://handler.twilio.com/twiml/EH1' },
    { [APP]: { voice_url: 'https://app.example.com/voice' } });
  assert.equal(state, 'exposed');
  assert.match(detail, new RegExp(APP));
});

test('fallback on the application counts', () => {
  const [state] = verdict(
    { voice_application_sid: APP },
    { [APP]: { voice_url: 'https://app.example.com/voice',
               voice_fallback_url: 'https://handler.twilio.com/twiml/EH1' } });
  assert.equal(state, 'covered');
});

test('sms is checked when voice is fine', () => {
  const [state, detail] = verdict({
    voice_url: 'https://app.example.com/voice',
    voice_fallback_url: 'https://handler.twilio.com/twiml/EH1',
    sms_url: 'https://app.example.com/sms',
  });
  assert.equal(state, 'exposed');
  assert.match(detail, /sms/);
});

test('number with no handler is idle, not exposed', () => {
  assert.equal(verdict({ voice_url: '', sms_url: null })[0], 'idle');
});

test('unread application is not guessed at', () => {
  assert.equal(verdict({ voice_application_sid: APP }, {})[0], 'unresolved');
});
''',
"faq": [
 ("When does Twilio actually call the fallback URL?",
  "Only when the primary handler fails: a non-2xx response, a connection or TLS error, a timeout, or TwiML that will not parse. A handler that answers 200 with unhelpful TwiML is a success as far as Twilio is concerned, and the fallback is never reached."),
 ("What should the fallback URL point at?",
  "Something that cannot fail for the same reason your app just did. A TwiML Bin on handler.twilio.com is the usual answer: it is static, hosted by Twilio, and says something human while you fix the real handler. A URL on the same host behind the same load balancer is not a fallback."),
 ("Why does setting the fallback on the number change nothing?",
  "Because an Application SID is set on that channel. When voice_application_sid is populated it takes precedence outright and every URL on the number, fallback included, is ignored. Set the fallback on the Application, or detach the Application so the number's own fields apply."),
 ("Does a missing fallback affect SMS as badly as voice?",
  "It is less severe, because inbound SMS can be reconstructed from the Messages list afterwards and a caller cannot. It still loses the automatic reply and any STOP handling that depended on the webhook, so it belongs in the same audit with a lower priority."),
 ("Is a fallback a substitute for fixing the handler?",
  "No. It converts a dropped call into a degraded one, which is worth having and is not the same as working. The 11200 in the Debugger is still the thing to chase; the fallback just means the customer is not the one who pays for it."),
],
"related": [
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still points at the demo TwiML"),
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS disappears into a blank sms_url"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_PN, CITE_APPS, CITE_11200, CITE_WEBHOOKS],
},

]
