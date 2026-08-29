#!/usr/bin/env python3
"""/twilio/ field notes, batch Y — the writing.

Five findings that never produce an error code, because in every one of them the
platform is doing exactly what it was told: a number still serving the API
version it was bought with, two products the account still depends on after
Twilio stopped developing them, call recordings sitting in storage in the clear,
and an account with nothing subscribed to its own errors.

The three end-of-life notes share one thesis, and it is worth saying plainly:
nothing breaks on the day a product is deprecated. The announcement changes no
field, raises no code and fails no request. The only signal that a deprecation
concerns you is that you are still calling the thing, so each of these scripts
is built to answer two questions rather than one — is this account still
depending on it, and how much.

Read-only throughout. GET requests only, and every repair is printed for a human
to run rather than performed.
"""

CITE_PN_USAGE = ("IncomingPhoneNumber resource — Twilio Docs",
                 "https://www.twilio.com/docs/usage/api/incoming-phone-number")
CITE_API = ("Twilio REST API overview — Twilio Docs",
            "https://www.twilio.com/docs/usage/api")
CITE_MESSAGE = ("Message resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_CONVERSATIONS = ("Conversations API overview — Twilio Docs",
                      "https://www.twilio.com/docs/conversations")
CITE_CONV_SERVICE = ("Conversations Service resource — Twilio Docs",
                     "https://www.twilio.com/docs/conversations/api/service-resource")
CITE_CONV_RESOURCE = ("Conversation resource — Twilio Docs",
                      "https://www.twilio.com/docs/conversations/api/conversation-resource")
CITE_NOTIFY_SERVICE = ("Notify Service resource — Twilio Docs",
                       "https://www.twilio.com/docs/notify/api/service-resource")
CITE_VERIFY_PUSH = ("Verify Push — Twilio Docs", "https://www.twilio.com/docs/verify/push")
CITE_UNUSED = ("Manage unused resources — Twilio Docs",
               "https://www.twilio.com/docs/usage/manage-unused-resources")
CITE_ENCRYPTION = ("Voice recording encryption — Twilio Docs",
                   "https://www.twilio.com/docs/voice/tutorials/voice-recording-encryption")
CITE_RECORDING = ("Recording resource — Twilio Docs",
                  "https://www.twilio.com/docs/voice/api/recording")
CITE_ERROR_LOGS = ("Error log event types — Twilio Docs",
                   "https://www.twilio.com/docs/events/event-types/errors/error-logs")
CITE_DEBUGGING = ("Debugging your application — Twilio Docs",
                  "https://www.twilio.com/docs/usage/troubleshooting/debugging-your-application")
CITE_SUBSCRIPTION = ("Event Streams Subscription resource — Twilio Docs",
                     "https://www.twilio.com/docs/events/event-streams/subscription-resource")
CITE_SINK = ("Event Streams Sink resource — Twilio Docs",
             "https://www.twilio.com/docs/events/event-streams/sink-resource")

GUIDES = [

{
"slug": "pinned-old-api-version",
"title": "Numbers still pinned to the 2008-08-01 API version",
"description": "A number carries its own api_version, fixed when it was bought. A 2008 pin serves the old schema forever, without the fields the documentation promises.",
"h1": "numbers still pinned to the 2008-08-01 API version",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio api version 2008-08-01", "twilio api_version incomingphonenumber",
             "twilio error_code missing on message", "twilio account default api version",
             "twilio legacy api schema"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The delivery-failure dashboard has a bucket called <code>unknown</code> and it is a third of the chart. The code reads <code>error_code</code> off each message, the documentation says the field is there, and for messages from one particular number it is simply absent. That number was bought in 2014. It still carries <code>api_version</code> of <code>2008-08-01</code>, and the 2008 schema does not have that field.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json</code> and flag any entry whose <code>api_version</code> is not <code>2010-04-01</code>. Then read the account default from <code>GET /2010-04-01/Accounts/{AccountSid}.json</code>, because that field decides what the next number you buy arrives pinned to.</p>
<p>The pin is per number and set at purchase time. It does not expire, nothing migrates it, and Twilio will keep serving the version each number asks for indefinitely, which is why nothing has ever forced this to your attention.</p>""",
"problem": """<p>This is a version mismatch that presents as an empty field. Your code asks for <code>error_code</code>, gets nothing, and does the sensible thing with nothing: treats the message as having no error. The 2008 schema is not broken and Twilio is not failing to honour it &mdash; the number asked for that version, and that version does not carry that field. There is no <code>400</code>, no deprecation header, no line in the Debugger, and no difference visible in the console, which shows the same tidy row for a 2008 number as for a 2010 one.</p>
<p>What makes it expensive is the sampling. Most accounts have one or two legacy numbers among dozens, so every test passes, every integration works, and the gap only opens on the traffic that happens to use the old number. A team can spend a week on a reporting bug that is really one field on one resource, set eleven years ago by whoever clicked Buy.</p>""",
"why": """<p><strong>The pin belongs to the number, not to your client library.</strong> Your SDK talks to <code>/2010-04-01/</code> and gets modern responses; the webhook Twilio sends <em>for that number</em> is built from the number's own <code>api_version</code>. Those are two different decisions and only one of them is under your code's control.</p>
<p><strong>There is no end-of-life date to force the issue.</strong> Unlike a product being retired, the 2008 version is not scheduled to be switched off. Nothing counts down, nothing warns, and an account can carry a 2008 pin for another decade. Deprecation with a date eventually fixes itself; deprecation without one never does.</p>
<p><strong>The account default is a separate field with its own failure.</strong> Repairing every number and leaving the account default on the old version is a treadmill: the next number bought arrives pinned again, and the audit that passed last quarter fails next quarter for a reason nobody wrote down.</p>
<p><strong>Absence is the worst possible symptom.</strong> A wrong value gets noticed. A missing one is indistinguishable from a legitimately empty field, so it flows through validation, through the ORM, into a chart, and comes out the other side as a category of message that apparently had no error.</p>
<p><strong>Old numbers are the ones that matter most.</strong> The number pinned to 2008 is by definition the oldest one on the account, which usually means it is the main line, printed on things, carrying the most traffic. The finding is inversely correlated with how safe it is to ignore.</p>""",
"steps": [
 {"h": "Read the account default first",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code> and look at <code>api_version</code>. This is the value new numbers inherit. If it is <code>2008-08-01</code>, the per-number findings below are a symptom and this field is the cause, so fix them in that order.</p>"""},
 {"h": "List every number and read api_version on each",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, following <code>next_page_uri</code> to the end. The field sits alongside <code>voice_url</code> and <code>sms_url</code> on each row; there is no filter for it, so this is a full sweep and a client-side comparison.</p>"""},
 {"h": "Separate the pinned numbers that are wired up",
  "body": """<p>A 2008 pin only reaches your application through a webhook, so a pinned number with a <code>voice_url</code>, an <code>sms_url</code> or an application SID is actively serving the old schema, and one with none of those is not yet. Both need fixing; only one of them is sending you short webhooks today.</p>"""},
 {"h": "Do not treat an unexpected value as current",
  "body": """<p>Anything that is neither <code>2010-04-01</code> nor <code>2008-08-01</code> &mdash; including a blank field &mdash; should be reported as unread rather than folded into either bucket. A check that quietly treats unknown as fine is how the one number that matters gets skipped.</p>"""},
 {"h": "Repin the numbers, then the account, then re-run",
  "body": """<p><code>POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json</code> with <code>ApiVersion=2010-04-01</code> for each, and set the account default in Console &rarr; Account &rarr; API version. Re-run afterwards, and again after the next number purchase, because that is the moment this comes back.</p>"""},
],
"verify": """<p>Re-run the script. The account default and every number should report <code>current</code>.</p>
<pre><code class="language-bash">python3 twilio_api_version_audit.py
# current  account default is 2010-04-01
# 12 number(s), 0 pinned to an older API version</code></pre>""",
"code_intro": "One GET for the account and one paginated GET over the numbers, with an API Key that has read access and nothing more. Both classifiers are pure functions and both are exported, because the account default and the per-number pin are genuinely two findings with two repairs, and a script that reports only the second leaves you fixing the same thing every quarter.",
"py_file": "twilio_api_version_audit.py",
"py": '''"""Report Twilio phone numbers pinned to an older API version.

The pin is per number and set at purchase time. It does not expire and nothing
migrates it, so a number bought in 2014 is still served the 2008 schema today:
webhooks with fewer parameters, and resource fields the current documentation
promises simply absent.

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
log = logging.getLogger("twilio_api_version_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

CURRENT = "2010-04-01"
LEGACY = "2008-08-01"

ROUTING_FIELDS = ("voice_url", "sms_url", "voice_fallback_url", "sms_fallback_url",
                  "status_callback", "voice_application_sid", "sms_application_sid")


def is_routed(number):
    """True when something on this number would actually be fetched.

    The version pin only reaches your application through a webhook, so a pinned
    number with no handler on it is a different sentence from a pinned number
    that is answering calls today. Both are findings; only one is current.
    """
    return any(str(number.get(f) or "").strip() for f in ROUTING_FIELDS)


def verdict(number):
    """Classify one IncomingPhoneNumber by the API version it is pinned to.

    Pure, so the rules can be tested without a network. Returns (state, detail).
    """
    version = str(number.get("api_version") or "").strip()

    if not version:
        return ("unread",
                "no api_version on this resource: report it rather than assuming "
                "it is current, because an unknown quietly counted as fine is how "
                "the one number that matters gets skipped.")

    if version == CURRENT:
        return ("current", "on %s, the version the documentation describes." % CURRENT)

    if version == LEGACY:
        if is_routed(number):
            return ("legacy-live",
                    "pinned to %s and wired to a handler: every webhook Twilio "
                    "sends for this number is built from the %s schema, so "
                    "parameters the docs promise arrive absent rather than wrong."
                    % (LEGACY, LEGACY))
        return ("legacy-idle",
                "pinned to %s with no handler on it: nothing is receiving the old "
                "schema today, and something will on the day this number is used."
                % LEGACY)

    return ("unread",
            "api_version is %s, which is neither %s nor %s: read it before "
            "assuming anything about what the webhooks carry."
            % (version, CURRENT, LEGACY))


def account_verdict(account):
    """Classify the account's default API version. Pure.

    Separate from the per-number check because this field decides what the next
    number bought on this account arrives pinned to. Repairing the numbers and
    leaving this one is a treadmill: the audit passes this quarter and fails the
    next, for a reason nobody wrote down.

    Returns (state, detail).
    """
    version = str(account.get("api_version") or "").strip()
    if not version:
        return ("unread",
                "no api_version on the account resource: the default that new "
                "numbers inherit could not be read.")
    if version == CURRENT:
        return ("current", "account default is %s." % CURRENT)
    return ("legacy-default",
            "account default is %s: every number bought from here on arrives "
            "pinned to it, so repairing the numbers alone fixes nothing that "
            "stays fixed." % version)


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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000,
                    help="stop after this many numbers")
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

    state, detail = account_verdict(get(session, "%s/Accounts/%s.json" % (BASE, account)))
    bad = 0
    if state == "current":
        log.info("%-14s %s", state, detail)
    else:
        bad += 1
        log.warning("%-14s %s", state, detail)
        log.warning("  repair: Console > Account > API version, set it to %s", CURRENT)

    numbers = list_numbers(session, account, args.max_numbers)
    pinned = 0
    for n in numbers:
        state, detail = verdict(n)
        line = "%-14s %s  %s" % (state, n.get("phone_number", "?"), detail)
        if state == "current":
            log.info(line)
            continue
        pinned += 1
        log.warning(line)
        log.warning("  repair: POST %s/Accounts/%s/IncomingPhoneNumbers/%s.json "
                    "ApiVersion=%s", BASE, account, n.get("sid"), CURRENT)

    log.info("%d number(s), %d pinned to an older API version", len(numbers), pinned)
    return 1 if (pinned or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-api-version-audit.mjs",
"js": '''/**
 * Report Twilio phone numbers pinned to an older API version.
 *
 * The pin is per number and set at purchase time. It does not expire and nothing
 * migrates it, so a number bought in 2014 is still served the 2008 schema today.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const CURRENT = '2010-04-01';
const LEGACY = '2008-08-01';

const ROUTING_FIELDS = ['voice_url', 'sms_url', 'voice_fallback_url',
                        'sms_fallback_url', 'status_callback',
                        'voice_application_sid', 'sms_application_sid'];

/**
 * True when something on this number would actually be fetched. The version pin
 * only reaches your application through a webhook.
 */
export function isRouted(number) {
  return ROUTING_FIELDS.some((f) => String(number[f] ?? '').trim());
}

/**
 * Classify one IncomingPhoneNumber by the API version it is pinned to. Pure, so
 * the rules can be tested without a network. Returns [state, detail].
 */
export function verdict(number) {
  const version = String(number.api_version ?? '').trim();

  if (!version) {
    return ['unread',
      'no api_version on this resource: report it rather than assuming it is ' +
      'current, because an unknown quietly counted as fine is how the one ' +
      'number that matters gets skipped.'];
  }

  if (version === CURRENT) {
    return ['current', `on ${CURRENT}, the version the documentation describes.`];
  }

  if (version === LEGACY) {
    if (isRouted(number)) {
      return ['legacy-live',
        `pinned to ${LEGACY} and wired to a handler: every webhook Twilio sends ` +
        `for this number is built from the ${LEGACY} schema, so parameters the ` +
        'docs promise arrive absent rather than wrong.'];
    }
    return ['legacy-idle',
      `pinned to ${LEGACY} with no handler on it: nothing is receiving the old ` +
      'schema today, and something will on the day this number is used.'];
  }

  return ['unread',
    `api_version is ${version}, which is neither ${CURRENT} nor ${LEGACY}: read ` +
    'it before assuming anything about what the webhooks carry.'];
}

/**
 * Classify the account's default API version. Pure. This field decides what the
 * next number bought on this account arrives pinned to, so repairing the numbers
 * and leaving it is a treadmill. Returns [state, detail].
 */
export function accountVerdict(account) {
  const version = String(account.api_version ?? '').trim();
  if (!version) {
    return ['unread',
      'no api_version on the account resource: the default that new numbers ' +
      'inherit could not be read.'];
  }
  if (version === CURRENT) return ['current', `account default is ${CURRENT}.`];
  return ['legacy-default',
    `account default is ${version}: every number bought from here on arrives ` +
    'pinned to it, so repairing the numbers alone fixes nothing that stays fixed.'];
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

  let bad = 0;
  const [aState, aDetail] = accountVerdict(
    await get(auth, `${BASE}/Accounts/${account}.json`));
  if (aState === 'current') {
    console.log(`${aState.padEnd(14)} ${aDetail}`);
  } else {
    bad += 1;
    console.warn(`${aState.padEnd(14)} ${aDetail}`);
    console.warn(`  repair: Console > Account > API version, set it to ${CURRENT}`);
  }

  const numbers = await listNumbers(auth, account);
  let pinned = 0;
  for (const n of numbers) {
    const [state, detail] = verdict(n);
    const line = `${state.padEnd(14)} ${n.phone_number ?? '?'}  ${detail}`;
    if (state === 'current') { console.log(line); continue; }
    pinned += 1;
    console.warn(line);
    console.warn(`  repair: POST ${BASE}/Accounts/${account}/IncomingPhoneNumbers/` +
                 `${n.sid}.json ApiVersion=${CURRENT}`);
  }

  console.log(`${numbers.length} number(s), ${pinned} pinned to an older API version`);
  process.exitCode = (pinned || bad) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the two that a simpler check gets wrong. A legacy number with no handler is a real finding but not a live one, and reporting it with the same words as the main line wastes the reader's attention. An unexpected or missing <code>api_version</code> must not be quietly counted as current, because on an account with forty numbers the only one that gets skipped is the one nobody could parse.",
"test_py_file": "test_twilio_api_version_audit.py",
"test_py": '''from twilio_api_version_audit import account_verdict, is_routed, verdict


def make(**kw):
    number = {"sid": "PN01", "phone_number": "+15005550006",
              "api_version": "2010-04-01", "voice_url": "https://app.example.com/voice"}
    number.update(kw)
    return number


def test_a_number_on_the_current_version_is_current():
    state, detail = verdict(make())
    assert state == "current"
    assert "2010-04-01" in detail


def test_a_2008_pin_with_a_live_handler_is_serving_the_old_schema_now():
    state, detail = verdict(make(api_version="2008-08-01"))
    assert state == "legacy-live"
    assert "absent" in detail


def test_a_2008_pin_with_no_handler_is_a_separate_and_quieter_finding():
    state, detail = verdict(make(api_version="2008-08-01", voice_url=""))
    assert state == "legacy-idle"
    assert "day this number is used" in detail


def test_an_application_sid_alone_still_counts_as_routed():
    assert is_routed({"voice_application_sid": "AP0123456789"}) is True
    assert is_routed({"voice_url": "", "sms_url": None}) is False


def test_a_missing_api_version_is_reported_rather_than_assumed_current():
    state, detail = verdict(make(api_version=None))
    assert state == "unread"
    assert "assuming" in detail


def test_an_unexpected_version_is_never_folded_into_either_bucket():
    state, detail = verdict(make(api_version="2015-01-01"))
    assert state == "unread"
    assert "2015-01-01" in detail


def test_the_account_default_is_its_own_finding_with_its_own_repair():
    state, detail = account_verdict({"api_version": "2008-08-01"})
    assert state == "legacy-default"
    assert "bought from here on" in detail


def test_a_current_account_default_means_new_numbers_arrive_correct():
    assert account_verdict({"api_version": "2010-04-01"})[0] == "current"
    assert account_verdict({})[0] == "unread"
''',
"test_js_file": "twilio-api-version-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accountVerdict, isRouted, verdict } from './twilio-api-version-audit.mjs';

const make = (over = {}) => ({
  sid: 'PN01',
  phone_number: '+15005550006',
  api_version: '2010-04-01',
  voice_url: 'https://app.example.com/voice',
  ...over,
});

test('a number on the current version is current', () => {
  const [state, detail] = verdict(make());
  assert.equal(state, 'current');
  assert.match(detail, /2010-04-01/);
});

test('a 2008 pin with a live handler is serving the old schema now', () => {
  const [state, detail] = verdict(make({ api_version: '2008-08-01' }));
  assert.equal(state, 'legacy-live');
  assert.match(detail, /absent/);
});

test('a 2008 pin with no handler is a separate and quieter finding', () => {
  const [state, detail] = verdict(make({ api_version: '2008-08-01', voice_url: '' }));
  assert.equal(state, 'legacy-idle');
  assert.match(detail, /day this number is used/);
});

test('an application sid alone still counts as routed', () => {
  assert.equal(isRouted({ voice_application_sid: 'AP0123456789' }), true);
  assert.equal(isRouted({ voice_url: '', sms_url: null }), false);
});

test('a missing api_version is reported rather than assumed current', () => {
  const [state, detail] = verdict(make({ api_version: null }));
  assert.equal(state, 'unread');
  assert.match(detail, /assuming/);
});

test('an unexpected version is never folded into either bucket', () => {
  const [state, detail] = verdict(make({ api_version: '2015-01-01' }));
  assert.equal(state, 'unread');
  assert.match(detail, /2015-01-01/);
});

test('the account default is its own finding with its own repair', () => {
  const [state, detail] = accountVerdict({ api_version: '2008-08-01' });
  assert.equal(state, 'legacy-default');
  assert.match(detail, /bought from here on/);
});

test('a current account default means new numbers arrive correct', () => {
  assert.equal(accountVerdict({ api_version: '2010-04-01' })[0], 'current');
  assert.equal(accountVerdict({})[0], 'unread');
});
''',
"faq": [
 ("Is the 2008 API going to be switched off?",
  "There is no announced date, and that is precisely what makes this worth auditing. A retirement with a deadline eventually forces itself onto a roadmap. A version that is merely old gets served forever, so a 2008 pin will sit on an account until somebody goes looking for it, which is what this script is."),
 ("Does my client library not control the version?",
  "It controls the version of the REST calls you make, which is why your API responses look modern. It has nothing to do with the webhooks Twilio sends you: those are built from the api_version on the number that received the call or message. Two different decisions, and only one of them is in your code."),
 ("Why does the script care whether the number has a handler?",
  "Because it changes what you do this afternoon. A pinned number with a live voice_url is sending your application short webhooks right now, and that is a bug with current consequences. A pinned number with nothing on it is a landmine rather than an explosion, and it deserves a different sentence in the report."),
 ("Is repinning a number risky?",
  "It changes the parameter set your handler receives for that number, so it is a code question rather than a config question. Read what your handler actually uses first, deploy any missing tolerance, then repin one number and watch it. Doing all forty in a batch on a Friday is how a working line starts throwing 500s."),
 ("Why check the account default separately?",
  "Because it is the field that reintroduces the problem. Numbers inherit it at purchase, so an account still defaulting to the old version will hand you a fresh finding every time somebody buys a number. Fixing the numbers is the cleanup; fixing the default is the fix."),
],
"related": [
 ("/twilio/phone-number-still-on-demo-twiml/", "A number provisioned and never wired to your app"),
 ("/twilio/number-conflicting-url-and-application-sid/", "Which handler on a number actually wins"),
 ("/twilio/status-callback-webhook-failing-11200/", "Delivery state blind because the callback fails"),
],
"citations": [CITE_PN_USAGE, CITE_API, CITE_MESSAGE, CITE_KEYS],
},

{
"slug": "eol-programmable-chat-in-use",
"title": "Programmable Chat is still in use past its end of life",
"description": "Nothing breaks on a deprecation date, so the only signal is that you are still calling it. Count the Chat services, then find out what still depends on them.",
"h1": "Programmable Chat is still in use past its end of life",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio programmable chat end of life", "twilio chat to conversations migration",
             "chat.twilio.com v2 services", "twilio chat eol 2026", "twilio deprecated product audit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Chat SDK still works. Channels list, messages send, the integration tests are green, and the changelog entry announcing the end of life went to a billing address that forwards to a team alias nobody reads. Nothing failed on 1 June 2026 and nothing will fail on any particular morning after it. The account simply has three <code>IS</code> services on it that Twilio is no longer developing, and an iOS build from last year still talking to them.",
"short_answer": """<p>Read <code>GET https://chat.twilio.com/v2/Services</code>. A non-empty list is the whole detection: the account still holds Programmable Chat services, which Twilio superseded with Conversations and which reach end of life on 2026-06-01 for Flex.</p>
<p>Then read <code>GET https://conversations.twilio.com/v1/Services</code> in the same run. Chat services and no Conversations services means nothing has been moved. Both present means somebody started and these are the remainder, which is the state most likely to be recorded internally as done.</p>""",
"problem": """<p>A deprecation is an announcement, not a behaviour change. On the day it takes effect the API returns the same <code>200</code>, the SDK builds, the messages deliver, and every check you have keeps passing. There is no <code>deprecated</code> field on the resource, no <code>Sunset</code> header on the response, nothing in the Debugger, and no error code &mdash; because from the platform's point of view nothing has gone wrong yet. It has only stopped being maintained.</p>
<p>That leaves exactly one signal available to you: you are still calling it. Everything else about this problem, including when it eventually breaks and how badly, is unknowable from the API. So the check cannot be "has something failed" and has to be "is this account still depending on it, and how much" &mdash; because the answer to the second question is what decides whether the migration is a quarter of planning or a Tuesday afternoon.</p>""",
"why": """<p><strong>Nothing marks a resource as end-of-life.</strong> A Chat Service resource fetched today is byte-for-byte the shape it was three years ago. Deprecation lives in a changelog and a support email, both of which are outside the surface any monitoring you own can read.</p>
<p><strong>There is no automated migration, and there cannot be.</strong> Chat and Conversations have different models &mdash; channels against conversations, and Conversations reaches out over SMS and WhatsApp as well as chat. That is not a schema translation, it is a product decision per channel, which is why nobody can run it for you and why it is easy to defer.</p>
<p><strong><code>date_updated</code> is staleness, never traffic.</strong> It moves when somebody edits the service, not when a message goes through it. A service carrying your whole support queue and a service nobody has opened since 2021 are indistinguishable in the list response, so the script reports that field as an upper bound on staleness and refuses to call it usage.</p>
<p><strong>Half-migrated is the most dangerous state and the most reassuring one.</strong> An account with both Chat and Conversations services has a migration in its history, a ticket marked resolved, and some number of clients still pointed at the old product. Nobody re-opens a closed migration without a reason, and there will be no error to provide one.</p>
<p><strong>The real dependency is in clients you cannot see.</strong> The service resource is the account-side shadow of an SDK compiled into a mobile app that shipped to users who will not update it. The API tells you the service exists; only your own release history tells you who is still calling it.</p>""",
"steps": [
 {"h": "List the Chat services",
  "body": """<p><code>GET https://chat.twilio.com/v2/Services?PageSize=50</code>, following <code>meta.next_page_url</code>, which on this domain is an absolute URL rather than the path the 2010-04-01 API returns. An empty list ends the audit with the answer you want.</p>"""},
 {"h": "Read the Conversations services in the same run",
  "body": """<p><code>GET https://conversations.twilio.com/v1/Services</code>. This is what turns a count into a state: no Conversations services at all means the migration has not started, and both products present means it started and stopped somewhere in the middle.</p>"""},
 {"h": "Age the services, and be honest about what that measures",
  "body": """<p><code>date_updated</code> on these newer domains is ISO 8601 (<code>2024-03-11T09:12:00Z</code>), not the RFC 2822 the account API returns. It tells you when the service was last configured, which sorts an abandoned service from one somebody was recently touching, and tells you nothing whatsoever about message volume.</p>"""},
 {"h": "Count the days against the date",
  "body": """<p>Past the end-of-life date the finding is not "plan this" but "you are running unsupported", and the sentence in the report should say so. Before it, the number of days remaining is the only prioritisation signal available, because nothing else about this gets worse in a measurable way.</p>"""},
 {"h": "Find the clients, then migrate service by service",
  "body": """<p>Grep your own repositories for the Chat SDK and <code>chat.twilio.com</code>, and check which mobile releases still embed it &mdash; the API cannot see any of that. Then create the replacement with <code>POST https://conversations.twilio.com/v1/Services</code>, repoint one client, and only remove the Chat service once nothing is left on it.</p>"""},
],
"verify": """<p>Re-run once the last service is gone. The state should be <code>clear</code> and the exit code zero.</p>
<pre><code class="language-bash">python3 twilio_chat_eol_audit.py
# clear          no Programmable Chat services on this account.</code></pre>""",
"code_intro": "Two paginated GETs on two different Twilio domains, with an API Key that has read access and nothing more. The classifier takes both lists rather than one, because the finding is a relationship between them: the same three Chat services mean something different on an account that has never created a Conversations service than on one that has twelve. The countdown is a separate pure function so the arithmetic that decides the tone of the report is visible and testable.",
"py_file": "twilio_chat_eol_audit.py",
"py": '''"""Report Programmable Chat services still held by a Twilio account.

Nothing breaks on the day a product is deprecated, so there is no error to look
for. The only available signal is that the account is still calling it, and the
only useful question is how much still depends on it.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_chat_eol_audit")

CHAT = "https://chat.twilio.com/v2"
CONVERSATIONS = "https://conversations.twilio.com/v1"

# Programmable Chat in Flex reaches end of life on this date. After it the
# product may stop working as expected, and there is no automated migration.
EOL = datetime.date(2026, 6, 1)


def parse_when(value):
    """Parse a timestamp from one of Twilio's newer API domains.

    chat.twilio.com and conversations.twilio.com return ISO 8601 with a trailing
    Z. The 2010-04-01 account API returns RFC 2822 instead, so a parser written
    for one returns nothing at all when pointed at the other, and a report with
    no findings reads exactly like a clean account.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def deadline(today):
    """How far this account is from Chat's end of life. Pure.

    Past the date the finding is not "plan this", it is "you are running
    unsupported", and the report should use different words for the two.

    Returns (urgency, text).
    """
    days = (EOL - today).days
    if days < 0:
        return ("past", "%d day(s) past the %s end of life" % (-days, EOL.isoformat()))
    if days <= 90:
        return ("soon", "%d day(s) until the %s end of life" % (days, EOL.isoformat()))
    return ("ahead", "%d day(s) until the %s end of life" % (days, EOL.isoformat()))


def days_since_touched(services, today):
    """Days since the most recently updated service was last configured. Pure.

    date_updated moves when the service resource is edited and not when a
    message passes through it, so this is an upper bound on staleness and never
    a measure of traffic. It is here to sort a service somebody was recently
    working on from one nobody has opened in three years, and for nothing else.
    """
    seen = []
    for service in services or []:
        when = (parse_when(service.get("date_updated"))
                or parse_when(service.get("date_created")))
        if when:
            seen.append(when.date())
    return (today - max(seen)).days if seen else None


def verdict(chat_services, conversations_services):
    """Classify what the account still depends on. Pure, so the rules can be
    tested without a network.

    Takes both lists because the finding is the relationship between them: three
    Chat services mean one thing on an account with no Conversations services
    and another on an account with twelve.

    Returns (state, detail).
    """
    chat = list(chat_services or [])
    conversations = list(conversations_services or [])

    if not chat:
        return ("clear", "no Programmable Chat services on this account.")

    if not conversations:
        return ("not-started",
                "%d Chat service(s) and no Conversations services: nothing has "
                "been moved yet, and there is no automated migration to run "
                "because the two products do not have the same model."
                % len(chat))

    return ("in-progress",
            "%d Chat service(s) alongside %d Conversations service(s): the "
            "migration was started and these are what is left of it, which is "
            "the state most likely to be recorded internally as finished."
            % (len(chat), len(conversations)))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_all(session, url, key, limit=200):
    """Page a newer-domain list. meta.next_page_url is absolute here, unlike the
    next_page_uri path the 2010-04-01 API returns."""
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-services", type=int, default=200,
                    help="stop after this many services per product")
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

    chat = list_all(session, CHAT + "/Services", "services", args.max_services)
    conversations = list_all(session, CONVERSATIONS + "/Services", "services",
                             args.max_services)

    for service in chat:
        log.info("  %s %s updated=%s", service.get("sid", "?"),
                 service.get("friendly_name") or "(no name)",
                 service.get("date_updated") or "?")

    state, detail = verdict(chat, conversations)
    if state == "clear":
        log.info("%-14s %s", state, detail)
        return 0

    today = datetime.date.today()
    urgency, text = deadline(today)
    log.warning("%-14s %s", state, detail)
    log.warning("  %s (%s)", text, urgency)

    stale = days_since_touched(chat, today)
    if stale is not None:
        log.warning("  most recently configured %d day(s) ago: staleness, not "
                    "traffic. Nothing in this API reports message volume.", stale)

    log.warning("  repair: create the replacement with POST %s/Services, repoint "
                "one client at a time, then remove each Chat service once nothing "
                "is left on it", CONVERSATIONS)
    log.warning("  the clients are not visible from here: grep your repositories "
                "for chat.twilio.com and check which mobile releases embed the SDK")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-chat-eol-audit.mjs",
"js": '''/**
 * Report Programmable Chat services still held by a Twilio account.
 *
 * Nothing breaks on the day a product is deprecated, so there is no error to
 * look for. The only available signal is that the account is still calling it.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const CHAT = 'https://chat.twilio.com/v2';
const CONVERSATIONS = 'https://conversations.twilio.com/v1';

// Programmable Chat in Flex reaches end of life on this date.
const EOL = Date.UTC(2026, 5, 1);
const EOL_TEXT = '2026-06-01';
const DAY = 86400000;

/** Parse a timestamp from one of Twilio's newer domains: ISO 8601 with a Z. */
export function parseWhen(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : new Date(ms);
}

function utcDay(d) {
  return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
}

/**
 * How far this account is from Chat's end of life. Pure. Returns
 * [urgency, text].
 */
export function deadline(today) {
  const days = Math.round((EOL - utcDay(today)) / DAY);
  if (days < 0) return ['past', `${-days} day(s) past the ${EOL_TEXT} end of life`];
  if (days <= 90) return ['soon', `${days} day(s) until the ${EOL_TEXT} end of life`];
  return ['ahead', `${days} day(s) until the ${EOL_TEXT} end of life`];
}

/**
 * Days since the most recently updated service was last configured. Pure.
 * date_updated moves on a configuration edit and not on a message, so this is
 * an upper bound on staleness and never a measure of traffic.
 */
export function daysSinceTouched(services, today) {
  const seen = (services ?? [])
    .map((s) => parseWhen(s.date_updated) ?? parseWhen(s.date_created))
    .filter(Boolean)
    .map(utcDay);
  if (seen.length === 0) return null;
  return Math.round((utcDay(today) - Math.max(...seen)) / DAY);
}

/**
 * Classify what the account still depends on. Pure. Takes both lists because
 * the finding is the relationship between them. Returns [state, detail].
 */
export function verdict(chatServices, conversationsServices) {
  const chat = [...(chatServices ?? [])];
  const conversations = [...(conversationsServices ?? [])];

  if (chat.length === 0) {
    return ['clear', 'no Programmable Chat services on this account.'];
  }

  if (conversations.length === 0) {
    return ['not-started',
      `${chat.length} Chat service(s) and no Conversations services: nothing has ` +
      'been moved yet, and there is no automated migration to run because the ' +
      'two products do not have the same model.'];
  }

  return ['in-progress',
    `${chat.length} Chat service(s) alongside ${conversations.length} ` +
    'Conversations service(s): the migration was started and these are what is ' +
    'left of it, which is the state most likely to be recorded internally as ' +
    'finished.'];
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

export async function listAll(auth, url, key, limit = 200) {
  let next = url;
  let params = { PageSize: 50 };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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

  const chat = await listAll(auth, `${CHAT}/Services`, 'services');
  const conversations = await listAll(auth, `${CONVERSATIONS}/Services`, 'services');

  for (const s of chat) {
    console.log(`  ${s.sid ?? '?'} ${s.friendly_name || '(no name)'} ` +
                `updated=${s.date_updated ?? '?'}`);
  }

  const [state, detail] = verdict(chat, conversations);
  if (state === 'clear') {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }

  const today = new Date();
  const [urgency, text] = deadline(today);
  console.warn(`${state.padEnd(14)} ${detail}`);
  console.warn(`  ${text} (${urgency})`);

  const stale = daysSinceTouched(chat, today);
  if (stale !== null) {
    console.warn(`  most recently configured ${stale} day(s) ago: staleness, not ` +
                 'traffic. Nothing in this API reports message volume.');
  }

  console.warn(`  repair: create the replacement with POST ${CONVERSATIONS}/Services, ` +
               'repoint one client at a time, then remove each Chat service once ' +
               'nothing is left on it');
  console.warn('  the clients are not visible from here: grep your repositories ' +
               'for chat.twilio.com and check which mobile releases embed the SDK');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that matters most is the half-finished migration, because it is the one a count alone gets wrong: an account with Chat services and Conversations services has a closed ticket saying this was handled, and the report has to contradict that in words rather than in a number. The date arithmetic is pinned separately, with a date on each side of the deadline, so that the difference between a plan and an outage stays in the tests rather than in someone's head.",
"test_py_file": "test_twilio_chat_eol_audit.py",
"test_py": '''import datetime

from twilio_chat_eol_audit import days_since_touched, deadline, parse_when, verdict


def chat(**kw):
    service = {"sid": "IS01", "friendly_name": "support",
               "date_created": "2019-04-02T11:00:00Z",
               "date_updated": "2021-08-19T14:32:00Z"}
    service.update(kw)
    return service


def test_an_account_with_no_chat_services_is_clear():
    state, detail = verdict([], [{"sid": "IS90"}])
    assert state == "clear"
    assert "no Programmable Chat" in detail


def test_chat_services_and_no_conversations_means_nothing_has_moved():
    state, detail = verdict([chat()], [])
    assert state == "not-started"
    assert "no automated migration" in detail


def test_both_products_present_is_the_half_finished_migration():
    state, detail = verdict([chat()], [{"sid": "IS90"}, {"sid": "IS91"}])
    assert state == "in-progress"
    assert "recorded internally as finished" in detail


def test_after_the_date_the_account_is_running_unsupported():
    urgency, text = deadline(datetime.date(2026, 8, 30))
    assert urgency == "past"
    assert "90 day(s) past" in text


def test_inside_ninety_days_is_soon_and_beyond_it_is_ahead():
    assert deadline(datetime.date(2026, 5, 1))[0] == "soon"
    assert deadline(datetime.date(2025, 1, 1))[0] == "ahead"


def test_staleness_comes_from_the_most_recently_touched_service():
    services = [chat(date_updated="2021-08-19T14:32:00Z"),
                chat(date_updated="2026-08-20T09:00:00Z")]
    assert days_since_touched(services, datetime.date(2026, 8, 30)) == 10


def test_a_service_with_no_usable_timestamp_yields_no_staleness():
    assert days_since_touched([{"sid": "IS02"}], datetime.date(2026, 8, 30)) is None
    assert days_since_touched([], datetime.date(2026, 8, 30)) is None


def test_date_created_stands_in_when_date_updated_is_missing():
    service = {"sid": "IS03", "date_created": "2026-08-25T00:00:00Z"}
    assert days_since_touched([service], datetime.date(2026, 8, 30)) == 5


def test_parse_when_reads_iso_8601_and_refuses_anything_else():
    assert parse_when("2024-03-11T09:12:00Z") is not None
    assert parse_when("Tue, 18 Apr 2023 09:12:00 +0000") is None
    assert parse_when("") is None
''',
"test_js_file": "twilio-chat-eol-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  daysSinceTouched, deadline, parseWhen, verdict,
} from './twilio-chat-eol-audit.mjs';

const chat = (over = {}) => ({
  sid: 'IS01',
  friendly_name: 'support',
  date_created: '2019-04-02T11:00:00Z',
  date_updated: '2021-08-19T14:32:00Z',
  ...over,
});

const day = (y, m, d) => new Date(Date.UTC(y, m - 1, d));

test('an account with no chat services is clear', () => {
  const [state, detail] = verdict([], [{ sid: 'IS90' }]);
  assert.equal(state, 'clear');
  assert.match(detail, /no Programmable Chat/);
});

test('chat services and no conversations means nothing has moved', () => {
  const [state, detail] = verdict([chat()], []);
  assert.equal(state, 'not-started');
  assert.match(detail, /no automated migration/);
});

test('both products present is the half-finished migration', () => {
  const [state, detail] = verdict([chat()], [{ sid: 'IS90' }, { sid: 'IS91' }]);
  assert.equal(state, 'in-progress');
  assert.match(detail, /recorded internally as finished/);
});

test('after the date the account is running unsupported', () => {
  const [urgency, text] = deadline(day(2026, 8, 30));
  assert.equal(urgency, 'past');
  assert.match(text, /90 day\\(s\\) past/);
});

test('inside ninety days is soon and beyond it is ahead', () => {
  assert.equal(deadline(day(2026, 5, 1))[0], 'soon');
  assert.equal(deadline(day(2025, 1, 1))[0], 'ahead');
});

test('staleness comes from the most recently touched service', () => {
  const services = [chat({ date_updated: '2021-08-19T14:32:00Z' }),
                    chat({ date_updated: '2026-08-20T09:00:00Z' })];
  assert.equal(daysSinceTouched(services, day(2026, 8, 30)), 10);
});

test('a service with no usable timestamp yields no staleness', () => {
  assert.equal(daysSinceTouched([{ sid: 'IS02' }], day(2026, 8, 30)), null);
  assert.equal(daysSinceTouched([], day(2026, 8, 30)), null);
});

test('date_created stands in when date_updated is missing', () => {
  const service = { sid: 'IS03', date_created: '2026-08-25T00:00:00Z' };
  assert.equal(daysSinceTouched([service], day(2026, 8, 30)), 5);
});

test('parseWhen reads ISO 8601', () => {
  assert.notEqual(parseWhen('2024-03-11T09:12:00Z'), null);
  assert.equal(parseWhen(''), null);
  assert.equal(parseWhen('not a timestamp'), null);
});
''',
"faq": [
 ("The end-of-life date has passed and everything still works. Is this urgent?",
  "It is urgent in the sense that you no longer control the timing. Before the date, breakage is scheduled and you can plan around it; after it, the product is unmaintained and the change that finally breaks something arrives without notice and without an error code you can act on. Nothing about your Tuesday changes. What changed is that you have no warning left."),
 ("Why does the script look at Conversations services at all?",
  "Because it converts a count into a state. Chat services with no Conversations services anywhere means the migration has not begun, which is a big piece of work nobody has scoped. Both present means somebody did the work, stopped partway, and closed the ticket. Those two accounts need very different conversations and the Chat list alone cannot tell them apart."),
 ("Can I use date_updated to find the services nobody uses?",
  "No, and the script says so in its own output for that reason. The field moves when the service resource is edited and not when a message passes through it, so an untouched date proves nobody has changed the configuration and proves nothing at all about traffic. Treat it as an upper bound on staleness and get real usage from your own application logs."),
 ("Is there a migration tool?",
  "No, and the reason is structural rather than a gap in the tooling. Conversations models a conversation that can span SMS, WhatsApp and chat, where Chat models channels inside one product. Mapping one onto the other requires deciding what each channel becomes, which is a product decision per service. That is also why this note is about finding the dependency rather than about running a script that fixes it."),
 ("Deleting the Chat service would clear the finding. Should I?",
  "Only once nothing is calling it, which is exactly what the API cannot tell you. A mobile build from last year that still embeds the SDK will start failing the moment the service is gone, and those users will not have updated. Find the clients first from your own release history, move them, and let the empty service be the last thing you remove."),
],
"related": [
 ("/twilio/conversations-webhook-url-missing/", "The replacement product with no webhook wired up"),
 ("/twilio/eol-notify-service-in-use/", "The other dead product still sitting on the account"),
 ("/twilio/stale-or-orphaned-api-keys/", "Credentials nobody can account for either"),
],
"citations": [CITE_CONVERSATIONS, CITE_CONV_SERVICE, CITE_CONV_RESOURCE, CITE_KEYS],
},

{
"slug": "eol-notify-service-in-use",
"title": "Notify services still on the account after Notify's EOL",
"description": "Notify reached end of life and push stopped arriving, with no error anywhere. The services still exist in the API. The question is what is still bound to them.",
"h1": "Notify services still on the account after Notify's EOL",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio notify end of life", "twilio notify push not delivering",
             "notify.twilio.com v1 services", "twilio notify bindings",
             "twilio push migration fcm apns"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Push notifications stopped some time last winter. Nobody can put a date on it, because nothing recorded one. The Notify service is still in the API, the bindings are still listed, your code still gets a response it can parse, and the handset gets nothing. Twilio Notify reached end of life on 31 December 2025. The resource outlived the product by a comfortable margin, which is the only reason this is still in the codebase.",
"short_answer": """<p>Read <code>GET https://notify.twilio.com/v1/Services</code>. A non-empty list is the finding on its own: Notify reached end of life on 2025-12-31, and anything still here is unsupported.</p>
<p>Then read <code>GET https://notify.twilio.com/v1/Services/{ServiceSid}/Bindings</code> per service to answer the question that decides what you do about it. Bindings still registered means real devices are pointed at a product that no longer delivers to them. No bindings means this is a deletion to schedule rather than an outage to explain.</p>""",
"problem": """<p>This is the end-of-life failure in its completed form. Chat is a deadline; Notify is what the far side of one looks like. Delivery stopped, the REST surface did not, and the two facts are unrelated: the service resource still returns, still lists, still carries a friendly name, because retiring a product removes support and delivery and leaves the API shaped exactly as it was.</p>
<p>Push is the worst possible thing to lose quietly, because it is unobservable from your side even when it is working perfectly. There is no delivery receipt coming back from a handset, so a healthy push and a discarded one produce the same silence in your logs. The only monitoring most teams have for push is a user complaining, and users do not complain about a notification they never knew was coming. That is why this ran for months, and why the check has to be about registration rather than about failures: there are no failures to count.</p>""",
"why": """<p><strong>End of life removes the product, not the resource.</strong> Nothing is deleted from your account on the date, no field flips, and no request starts returning an error that names the reason. The list endpoint answers today exactly as it did in 2019, which is precisely how a dead dependency stays in a codebase.</p>
<p><strong>Nothing in the API says why the push stopped.</strong> There is no delivery status to poll and no error code attached to the silence. This is the documented symptom rather than a gap in your instrumentation, and it means no amount of log-searching on your side will ever produce the answer.</p>
<p><strong>Bindings are the only measure of dependence available.</strong> A binding is a device that registered itself for push through this service. Counting them is how "we still have a Notify service" becomes "eleven thousand installs are registered against something that does not deliver", which is the sentence that gets the work scheduled.</p>
<p><strong>The migration leaves Twilio entirely.</strong> Chat has a successor product one domain away. Notify does not: push goes back to FCM and APNs directly, or to Verify Push if what you were actually sending was authentication. There is no equivalent resource to create, so nobody can do this in an afternoon and everybody defers it.</p>
<p><strong>The devices will not come back on their own.</strong> Every binding was created by an app registering a token. Removing the service does not re-register anything, so the migration has to ship in a client release and then wait for installs to pick it up, which is the part that takes months rather than the part that takes an engineer.</p>""",
"steps": [
 {"h": "List the Notify services",
  "body": """<p><code>GET https://notify.twilio.com/v1/Services?PageSize=50</code>, following <code>meta.next_page_url</code>. On this domain that is an absolute URL, not the path <code>next_page_uri</code> returns on the 2010-04-01 API. An empty list is the answer you want and ends the run.</p>"""},
 {"h": "Count what is still bound to each service",
  "body": """<p><code>GET https://notify.twilio.com/v1/Services/{ServiceSid}/Bindings?PageSize=50</code>. One page is enough to separate the two cases that matter: something is registered, or nothing is. Treat the number as a floor rather than a total, and say so in the report, because a sampled page is not a count.</p>"""},
 {"h": "Do not wait for an error to confirm it",
  "body": """<p>There is no delivery status on this path and no error code for the silence. If you are looking for a failed request to prove the problem before acting, you will not find one, and the months you spend looking are months of notifications nobody receives.</p>"""},
 {"h": "Decide where push goes instead",
  "body": """<p>Straight to FCM and APNs is the general answer, since that is what Notify was wrapping. If what you were sending was really authentication rather than messaging, Verify Push is the closer replacement and keeps the challenge flow on Twilio. Either way this ships in a client release, so start it before the cleanup rather than after.</p>"""},
 {"h": "Delete the service last, once nothing is registered",
  "body": """<p><code>DELETE https://notify.twilio.com/v1/Services/{ServiceSid}</code> once traffic is off it. Last, not first: while a service is still there, its bindings tell you how far the client rollout has got, and deleting it throws away the only progress meter you have.</p>"""},
],
"verify": """<p>Re-run with bindings checked once the last service is removed. The state should be <code>clear</code>.</p>
<pre><code class="language-bash">python3 twilio_notify_eol_audit.py --check-bindings
# clear          no Notify services on this account.</code></pre>""",
"code_intro": "One paginated GET over the services and, with <code>--check-bindings</code>, one more per service &mdash; read access is all it needs. The classifier takes the services and a mapping of what was found bound to each, and it deliberately keeps <em>not checked</em> as its own state rather than defaulting it to zero: an account reported as abandoned because nobody passed a flag is worse than one reported as unknown.",
"py_file": "twilio_notify_eol_audit.py",
"py": '''"""Report Twilio Notify services still held after Notify's end of life.

Notify reached end of life on 2025-12-31. Nothing was deleted on the date and
nothing started returning an error, so the only signal that this account still
depends on it is that the services are still here and devices are still bound
to them.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_notify_eol_audit")

NOTIFY = "https://notify.twilio.com/v1"

# Twilio Notify reached end of life on this date. Remaining services are
# unsupported, and the resource still exists in the API long after delivery
# stopped.
EOL = datetime.date(2025, 12, 31)


def days_past_eol(today):
    """Days since Notify's end of life. Negative before it. Pure."""
    return (today - EOL).days


def binding_count(bindings, sid):
    """How many bindings were seen for one service. Pure, and forgiving.

    The value is whatever the caller counted on a sampled page, so it can arrive
    as an int, as a string, or missing entirely for a service that errored. None
    of those should raise in the middle of a report.
    """
    try:
        return max(0, int((bindings or {}).get(sid) or 0))
    except (TypeError, ValueError):
        return 0


def verdict(services, bindings=None):
    """Classify what this account still has bound to Notify. Pure, so the rules
    can be tested without a network.

    bindings is a mapping of service sid to how many bindings were seen, or None
    when the bindings were not read at all. Not-checked stays its own state
    rather than defaulting to zero: an account reported as abandoned because
    nobody passed a flag is worse than one reported as unknown.

    Returns (state, detail).
    """
    found = list(services or [])

    if not found:
        return ("clear", "no Notify services on this account.")

    if bindings is None:
        return ("unchecked",
                "%d Notify service(s) on an account, and Notify reached end of "
                "life on %s. The bindings were not read, so how much still "
                "depends on this is unknown." % (len(found), EOL.isoformat()))

    total = sum(binding_count(bindings, s.get("sid")) for s in found)
    if total:
        return ("registered",
                "%d Notify service(s) with at least %d binding(s) still "
                "registered: those are devices pointed at a product that no "
                "longer delivers, and every push aimed at them is discarded with "
                "nothing on either side to show for it." % (len(found), total))

    return ("abandoned",
            "%d Notify service(s) with nothing bound to them: this is a deletion "
            "to schedule rather than an outage to explain." % len(found))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_all(session, url, key, limit=200):
    """Page a newer-domain list. meta.next_page_url is absolute here, unlike the
    next_page_uri path the 2010-04-01 API returns."""
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def sample_bindings(session, services, sample):
    """One page of bindings per service. A floor, not a total, and the report
    says so rather than presenting a sampled page as a count."""
    seen = {}
    for service in services:
        sid = service.get("sid")
        page = get(session, "%s/Services/%s/Bindings" % (NOTIFY, sid), PageSize=sample)
        seen[sid] = len(page.get("bindings", []))
    return seen


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-bindings", action="store_true",
                    help="one extra GET per service to see what is still registered")
    ap.add_argument("--sample", type=int, default=50,
                    help="how many bindings to read per service")
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

    services = list_all(session, NOTIFY + "/Services", "services")
    bindings = sample_bindings(session, services, args.sample) if (
        services and args.check_bindings) else None

    for service in services:
        log.info("  %s %s bound=%s", service.get("sid", "?"),
                 service.get("friendly_name") or "(no name)",
                 binding_count(bindings, service.get("sid")) if bindings else "?")

    state, detail = verdict(services, bindings)
    if state == "clear":
        log.info("%-14s %s", state, detail)
        return 0

    log.warning("%-14s %s", state, detail)
    log.warning("  %d day(s) past end of life; nothing in this API reports why "
                "the push stopped, so there is no failure to wait for",
                days_past_eol(datetime.date.today()))
    log.warning("  repair: move push to FCM and APNs directly, or to Verify Push "
                "if what you were sending was authentication. That ships in a "
                "client release, so start it before the cleanup")
    log.warning("  then, once nothing is bound: DELETE %s/Services/{ServiceSid} "
                "for each one", NOTIFY)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-notify-eol-audit.mjs",
"js": '''/**
 * Report Twilio Notify services still held after Notify's end of life.
 *
 * Nothing was deleted on the date and nothing started returning an error, so the
 * only signal that this account still depends on Notify is that the services are
 * still here and devices are still bound to them.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const NOTIFY = 'https://notify.twilio.com/v1';

// Twilio Notify reached end of life on this date.
const EOL = Date.UTC(2025, 11, 31);
const EOL_TEXT = '2025-12-31';
const DAY = 86400000;

/** Days since Notify's end of life. Negative before it. Pure. */
export function daysPastEol(today) {
  const utc = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  return Math.round((utc - EOL) / DAY);
}

/**
 * How many bindings were seen for one service. Pure, and forgiving: the value
 * can arrive as a number, as a string, or missing for a service that errored.
 */
export function bindingCount(bindings, sid) {
  const raw = Number.parseInt((bindings ?? {})[sid] ?? 0, 10);
  return Number.isFinite(raw) ? Math.max(0, raw) : 0;
}

/**
 * Classify what this account still has bound to Notify. Pure.
 *
 * bindings is a mapping of service sid to how many bindings were seen, or null
 * when they were not read at all. Not-checked stays its own state rather than
 * defaulting to zero. Returns [state, detail].
 */
export function verdict(services, bindings = null) {
  const found = [...(services ?? [])];

  if (found.length === 0) return ['clear', 'no Notify services on this account.'];

  if (bindings === null || bindings === undefined) {
    return ['unchecked',
      `${found.length} Notify service(s) on an account, and Notify reached end of ` +
      `life on ${EOL_TEXT}. The bindings were not read, so how much still ` +
      'depends on this is unknown.'];
  }

  const total = found.reduce((n, s) => n + bindingCount(bindings, s.sid), 0);
  if (total) {
    return ['registered',
      `${found.length} Notify service(s) with at least ${total} binding(s) still ` +
      'registered: those are devices pointed at a product that no longer ' +
      'delivers, and every push aimed at them is discarded with nothing on ' +
      'either side to show for it.'];
  }

  return ['abandoned',
    `${found.length} Notify service(s) with nothing bound to them: this is a ` +
    'deletion to schedule rather than an outage to explain.'];
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

export async function listAll(auth, url, key, limit = 200) {
  let next = url;
  let params = { PageSize: 50 };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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
  const check = process.argv.includes('--check-bindings');

  const services = await listAll(auth, `${NOTIFY}/Services`, 'services');

  let bindings = null;
  if (services.length && check) {
    bindings = {};
    for (const s of services) {
      const page = await get(auth, `${NOTIFY}/Services/${s.sid}/Bindings`,
                             { PageSize: 50 });
      bindings[s.sid] = (page.bindings ?? []).length;
    }
  }

  for (const s of services) {
    console.log(`  ${s.sid ?? '?'} ${s.friendly_name || '(no name)'} ` +
                `bound=${bindings ? bindingCount(bindings, s.sid) : '?'}`);
  }

  const [state, detail] = verdict(services, bindings);
  if (state === 'clear') {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(14)} ${detail}`);
  console.warn(`  ${daysPastEol(new Date())} day(s) past end of life; nothing in ` +
               'this API reports why the push stopped, so there is no failure to ' +
               'wait for');
  console.warn('  repair: move push to FCM and APNs directly, or to Verify Push ' +
               'if what you were sending was authentication. That ships in a ' +
               'client release, so start it before the cleanup');
  console.warn(`  then, once nothing is bound: DELETE ${NOTIFY}/Services/{ServiceSid} ` +
               'for each one');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning hardest is the one where the bindings were never read. It is tempting to let a missing count fall through to zero and report the account as abandoned, and that produces a report saying the safe thing about an account with eleven thousand registered devices on it. Unknown has to survive as unknown all the way to the printed line, so it gets its own state and its own test.",
"test_py_file": "test_twilio_notify_eol_audit.py",
"test_py": '''import datetime

from twilio_notify_eol_audit import binding_count, days_past_eol, verdict


def service(sid="IS01", name="push"):
    return {"sid": sid, "friendly_name": name}


def test_an_account_with_no_notify_services_is_clear():
    state, detail = verdict([])
    assert state == "clear"
    assert "no Notify services" in detail


def test_services_with_unread_bindings_stay_unknown_rather_than_abandoned():
    state, detail = verdict([service()])
    assert state == "unchecked"
    assert "not read" in detail


def test_bindings_still_registered_is_the_finding_that_gets_scheduled():
    state, detail = verdict([service("IS01"), service("IS02")],
                            {"IS01": 11000, "IS02": 4})
    assert state == "registered"
    assert "at least 11004" in detail


def test_no_bindings_anywhere_is_cleanup_rather_than_an_outage():
    state, detail = verdict([service()], {"IS01": 0})
    assert state == "abandoned"
    assert "deletion to schedule" in detail


def test_a_service_missing_from_the_bindings_map_counts_as_zero():
    assert verdict([service("IS09")], {"IS01": 3})[0] == "abandoned"


def test_binding_count_takes_strings_and_refuses_to_raise_on_junk():
    assert binding_count({"IS01": "12"}, "IS01") == 12
    assert binding_count({"IS01": "many"}, "IS01") == 0
    assert binding_count({"IS01": -4}, "IS01") == 0
    assert binding_count(None, "IS01") == 0


def test_days_past_eol_counts_forward_from_the_end_of_life_date():
    assert days_past_eol(datetime.date(2026, 1, 31)) == 31
    assert days_past_eol(datetime.date(2025, 12, 1)) == -30
''',
"test_js_file": "twilio-notify-eol-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bindingCount, daysPastEol, verdict } from './twilio-notify-eol-audit.mjs';

const service = (sid = 'IS01', name = 'push') => ({ sid, friendly_name: name });
const day = (y, m, d) => new Date(Date.UTC(y, m - 1, d));

test('an account with no notify services is clear', () => {
  const [state, detail] = verdict([]);
  assert.equal(state, 'clear');
  assert.match(detail, /no Notify services/);
});

test('services with unread bindings stay unknown rather than abandoned', () => {
  const [state, detail] = verdict([service()]);
  assert.equal(state, 'unchecked');
  assert.match(detail, /not read/);
});

test('bindings still registered is the finding that gets scheduled', () => {
  const [state, detail] = verdict([service('IS01'), service('IS02')],
                                  { IS01: 11000, IS02: 4 });
  assert.equal(state, 'registered');
  assert.match(detail, /at least 11004/);
});

test('no bindings anywhere is cleanup rather than an outage', () => {
  const [state, detail] = verdict([service()], { IS01: 0 });
  assert.equal(state, 'abandoned');
  assert.match(detail, /deletion to schedule/);
});

test('a service missing from the bindings map counts as zero', () => {
  assert.equal(verdict([service('IS09')], { IS01: 3 })[0], 'abandoned');
});

test('bindingCount takes strings and refuses to throw on junk', () => {
  assert.equal(bindingCount({ IS01: '12' }, 'IS01'), 12);
  assert.equal(bindingCount({ IS01: 'many' }, 'IS01'), 0);
  assert.equal(bindingCount({ IS01: -4 }, 'IS01'), 0);
  assert.equal(bindingCount(null, 'IS01'), 0);
});

test('daysPastEol counts forward from the end of life date', () => {
  assert.equal(daysPastEol(day(2026, 1, 31)), 31);
  assert.equal(daysPastEol(day(2025, 12, 1)), -30);
});
''',
"faq": [
 ("Why is there nothing in the API explaining why push stopped?",
  "Because the product was retired rather than broken. There is no delivery status on this path and no error code attached to the silence, which is the documented symptom rather than a hole in your instrumentation. No amount of searching your own logs will produce a reason, so waiting for one is waiting for something that does not exist."),
 ("Can I keep using Notify if it still returns 200?",
  "The REST surface answering is not the same as notifications arriving, and this note exists because those two are easy to confuse. End of life removes support and delivery; it leaves the resource shaped as it was. An unsupported dependency that has already stopped doing its job is not a thing to keep using, it is a thing to remove once the clients have moved."),
 ("What replaces it?",
  "Nothing on Twilio, for the general case. Notify was a wrapper over FCM and APNs, so the migration is to call those directly with the tokens your app already collects. The exception is authentication: if the push you were sending was a login approval or a second factor, Verify Push is the closer replacement and keeps that flow on the platform."),
 ("Why count bindings instead of just deleting the services?",
  "Because the binding count is your only progress meter, and deleting the service throws it away. The migration ships in a client release and then waits on installs updating, which takes months. While the service is still there, the number of bindings tells you how far that rollout has actually got. Delete it once that number stops mattering."),
 ("The count came back as fifty for every service. Is that real?",
  "No, and the report says at least rather than exactly for that reason. One page of bindings is a sample sized by whatever you passed for the page size, so a service with fifty on the first page has fifty or more. The distinction the script cares about is between nothing and something, and a sampled page answers that honestly while a total would need every page."),
],
"related": [
 ("/twilio/eol-programmable-chat-in-use/", "The other dead product, still one deadline behind"),
 ("/twilio/idle-phone-numbers-billed/", "Resources kept long after they stopped being used"),
 ("/twilio/stale-or-orphaned-api-keys/", "Credentials that outlived whoever created them"),
],
"citations": [CITE_NOTIFY_SERVICE, CITE_VERIFY_PUSH, CITE_UNUSED, CITE_KEYS],
},

{
"slug": "recordings-not-encrypted",
"title": "Call recordings stored without encryption at rest",
"description": "Voice Recording Encryption is opt-in and not retroactive. Read encryption_details across the sample to learn when it was on and what is still in the clear.",
"h1": "call recordings stored without encryption at rest",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio voice recording encryption", "twilio encryption_details null",
             "twilio recordings pci", "twilio recording at rest encryption",
             "twilio recording public key"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The question arrives in a spreadsheet from an auditor and it is one line: are call recordings encrypted at rest. Nobody knows. Recording was switched on years ago by whoever built the support queue, the files play fine in the console, and the answer turns out to be a field that is either present or absent on each recording &mdash; absent on all four years of them, because Voice Recording Encryption is opt-in and nobody opted in.",
"short_answer": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Recordings.json</code> and read <code>encryption_details</code> on each row. It is absent when the recording was stored unencrypted, and present when it was not. That is the whole test: presence, not a value.</p>
<p>Read it across a date-ordered sample rather than on one recording. Enabling encryption is not retroactive, so the interesting answer is where in the timeline the field starts or stops appearing: everything on the unencrypted side of that boundary stays readable with account credentials for as long as you keep it.</p>""",
"problem": """<p>Unencrypted media is not an outage, a cost or a bug, so nothing in the system has any reason to mention it. The recordings record, store, download and play exactly as intended. The only thing wrong is who can read them, and Twilio has no opinion about that: with encryption off, the media is retrievable by anything holding account credentials, which includes a leaked Auth Token, a key on a laptop, and every integration you have ever handed credentials to.</p>
<p>The reason it surfaces during an audit rather than before one is that the answer is genuinely not knowable from the console at a glance. Nothing shows a padlock. You have to fetch a recording resource and notice a field that is not there, which is a strange thing to go looking for unless somebody has asked. And when somebody does ask, the honest answer is usually not yes or no but "since when", which is a question only a date-ordered sweep can answer.</p>""",
"why": """<p><strong>It is opt-in, and the default is off.</strong> Turning recording on is one switch and encrypting it is a different one, in a different place, that also requires you to generate a key pair and upload the public half. Nobody hits that path by accident, so an account that has never deliberately done it has none of it.</p>
<p><strong>Enabling it does not reach backwards.</strong> New recordings carry <code>encryption_details</code> from the moment the setting goes on; the ones already stored do not, and never will. So an account that fixed this last year still holds however many years of plaintext media, and a check that samples only recent recordings reports it as clean.</p>
<p><strong>Absence is the signal, which makes it easy to code past.</strong> The field is simply not there rather than set to a falsy value. Code that reads it defensively and moves on will never notice, and a check that compares it against something specific will fail to match anything at all.</p>
<p><strong>Turning it off is as quiet as never turning it on.</strong> If the setting is disabled, recordings from that moment stop carrying the field while everything older keeps it. That reads as normal in every direction except a date-ordered one, which is why the classifier sorts before it judges.</p>
<p><strong>This is a different problem from the storage bill.</strong> Recordings that accumulate forever are a <a href="/twilio/unreleased-recordings-storage/">cost with its own note</a>; these are the same files considered as a liability rather than a line item. The two findings overlap in the fix, though: deleting a recording you no longer need is the only way to un-hold plaintext that is already stored.</p>""",
"steps": [
 {"h": "Sample recordings across the whole range, not the recent ones",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Recordings.json?PageSize=1000</code>, following <code>next_page_uri</code>. Because enabling encryption is not retroactive, a sample of only the newest recordings answers a different question from the one the auditor asked.</p>"""},
 {"h": "Test for presence of encryption_details, not for a value",
  "body": """<p>The field is absent on an unencrypted recording. There is no flag set to false and nothing to compare against, so the check is truthiness and the report is a count of rows that have it against rows that do not.</p>"""},
 {"h": "Parse date_created as RFC 2822 before sorting",
  "body": """<p>This API returns <code>Tue, 18 Apr 2023 09:12:00 +0000</code>, not ISO 8601 &mdash; the newer Twilio domains differ. Python reads it with <code>email.utils.parsedate_to_datetime</code>; <code>datetime.fromisoformat</code> returns nothing, and a sweep that silently sorts nothing looks exactly like a clean account.</p>"""},
 {"h": "Find the boundary and say which side is which",
  "body": """<p>The newest unencrypted recording is the moment encryption was turned on, if the newer ones carry the field. If the newest recording is the unencrypted one and older ones are not, the setting was turned off instead, and everything since is in the clear. Those are opposite findings and only the ordering separates them.</p>"""},
 {"h": "Enable it, then decide what to do with the backlog",
  "body": """<p>Console &rarr; Voice &rarr; Settings &rarr; General, enable Voice Recording Encryption and upload a public key. Keep the private half somewhere you will still have it in three years, because without it the encrypted recordings are unrecoverable. Then deal with the plaintext backlog deliberately: it does not get encrypted, so the choice is keep it or delete it.</p>"""},
],
"verify": """<p>Re-run after enabling it and recording a new call. The newest rows should carry the field.</p>
<pre><code class="language-bash">python3 twilio_recording_encryption_audit.py
# encrypted      all 240 sampled recording(s) carry encryption details.</code></pre>""",
"code_intro": "One paginated GET over the recordings, with read access and nothing more. The classifier is pure and works on a date-ordered list rather than on a single recording, because every interesting answer here is about a boundary: encryption that started on a date and left everything before it in the clear, or encryption that stopped on one and left everything after it exposed. Those two look identical to a count and opposite to a sort.",
"py_file": "twilio_recording_encryption_audit.py",
"py": '''"""Report Twilio call recordings stored without encryption at rest.

Voice Recording Encryption is opt-in. With it off, encryption_details is simply
absent from the recording and the media is retrievable by anything holding
account credentials. Enabling it later is not retroactive, so the useful answer
is not yes or no but since when.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import email.utils
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_recording_encryption_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"


def is_encrypted(recording):
    """True when the recording carries encryption details.

    A presence test rather than a comparison: with encryption off the field is
    absent, not set to false, so there is nothing to compare it against and code
    that looks for a specific value matches nothing at all.
    """
    return bool(recording.get("encryption_details"))


def parse_when(value):
    """Parse date_created from the 2010-04-01 API.

    This API returns RFC 2822 (Tue, 18 Apr 2023 09:12:00 +0000). The newer
    Twilio domains return ISO 8601, so a parser written for one returns nothing
    for the other, and a sweep that silently sorts nothing reads exactly like a
    clean account.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None


def newest_first(recordings):
    """Sort a sample newest first, keeping undated rows at the end. Pure.

    The ordering is the analysis. A count of encrypted against unencrypted says
    nothing about which of the two opposite findings you have.
    """
    rows = list(recordings or [])
    dated = [(parse_when(r.get("date_created")), r) for r in rows]
    have = sorted([p for p in dated if p[0]], key=lambda p: p[0], reverse=True)
    return [r for _when, r in have] + [r for when, r in dated if not when]


def switch_point(recordings):
    """The date_created of the newest recording with no encryption details.

    On an account where encryption was turned on, that is the moment it happened:
    nothing after it is in the clear, and nothing before it will ever be
    encrypted, because the setting does not reach backwards.
    """
    for recording in newest_first(recordings):
        if not is_encrypted(recording):
            return recording.get("date_created")
    return None


def verdict(recordings):
    """Classify a date-ordered sample of recordings. Pure, so the rules can be
    tested without a network.

    Returns (state, detail).
    """
    rows = newest_first(recordings)
    if not rows:
        return ("none", "no recordings on this account: nothing stored, so "
                        "nothing stored in the clear.")

    plain = [r for r in rows if not is_encrypted(r)]

    if not plain:
        return ("encrypted",
                "all %d sampled recording(s) carry encryption details." % len(rows))

    if len(plain) == len(rows):
        return ("plaintext",
                "none of the %d sampled recording(s) carry encryption details: "
                "Voice Recording Encryption has never been on, and every one of "
                "these is readable by anything holding account credentials."
                % len(rows))

    if is_encrypted(rows[0]):
        return ("backlog",
                "the newest sampled recording is encrypted and %d older one(s) "
                "are not: enabling encryption does not reach backwards, so those "
                "stay in the clear for as long as you keep them." % len(plain))

    return ("regressed",
            "the newest sampled recording has no encryption details while %d "
            "older one(s) do: encryption was on and is not any more, so "
            "everything recorded since it stopped is in the clear."
            % (len(rows) - len(plain)))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_recordings(session, account, limit):
    """Page Recordings. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts/%s/Recordings.json" % (BASE, account)
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("recordings", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-recordings", type=int, default=2000,
                    help="stop after this many recordings")
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

    recordings = list_recordings(session, account, args.max_recordings)
    state, detail = verdict(recordings)
    if state in ("none", "encrypted"):
        log.info("%-14s %s", state, detail)
        return 0

    log.warning("%-14s %s", state, detail)

    boundary = switch_point(recordings)
    if boundary and state != "plaintext":
        log.warning("  newest unencrypted recording: %s", boundary)

    log.warning("  repair: Console > Voice > Settings > General, enable Voice "
                "Recording Encryption and upload a public key. Keep the private "
                "half: without it the encrypted recordings are unrecoverable")
    log.warning("  the recordings already stored in the clear are not re-encrypted "
                "when you enable it, so decide separately whether to keep them")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-recording-encryption-audit.mjs",
"js": '''/**
 * Report Twilio call recordings stored without encryption at rest.
 *
 * Voice Recording Encryption is opt-in. With it off, encryption_details is
 * simply absent and the media is retrievable by anything holding account
 * credentials. Enabling it later is not retroactive, so the useful answer is not
 * yes or no but since when.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

/**
 * True when the recording carries encryption details. A presence test rather
 * than a comparison: with encryption off the field is absent, not false.
 */
export function isEncrypted(recording) {
  return Boolean(recording.encryption_details);
}

/**
 * Parse date_created from the 2010-04-01 API, which returns RFC 2822 rather than
 * the ISO 8601 the newer Twilio domains use.
 */
export function parseWhen(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : ms;
}

/**
 * Sort a sample newest first, keeping undated rows at the end. Pure. The
 * ordering is the analysis: a count says nothing about which of the two
 * opposite findings you have.
 */
export function newestFirst(recordings) {
  const rows = [...(recordings ?? [])];
  const dated = rows.map((r) => [parseWhen(r.date_created), r]);
  const have = dated.filter(([w]) => w !== null).sort((a, b) => b[0] - a[0]);
  return [...have.map(([, r]) => r), ...dated.filter(([w]) => w === null).map(([, r]) => r)];
}

/**
 * The date_created of the newest recording with no encryption details: on an
 * account where encryption was turned on, the moment it happened.
 */
export function switchPoint(recordings) {
  for (const recording of newestFirst(recordings)) {
    if (!isEncrypted(recording)) return recording.date_created ?? null;
  }
  return null;
}

/**
 * Classify a date-ordered sample of recordings. Pure. Returns [state, detail].
 */
export function verdict(recordings) {
  const rows = newestFirst(recordings);
  if (rows.length === 0) {
    return ['none',
      'no recordings on this account: nothing stored, so nothing stored in the clear.'];
  }

  const plain = rows.filter((r) => !isEncrypted(r));

  if (plain.length === 0) {
    return ['encrypted',
      `all ${rows.length} sampled recording(s) carry encryption details.`];
  }

  if (plain.length === rows.length) {
    return ['plaintext',
      `none of the ${rows.length} sampled recording(s) carry encryption details: ` +
      'Voice Recording Encryption has never been on, and every one of these is ' +
      'readable by anything holding account credentials.'];
  }

  if (isEncrypted(rows[0])) {
    return ['backlog',
      `the newest sampled recording is encrypted and ${plain.length} older one(s) ` +
      'are not: enabling encryption does not reach backwards, so those stay in ' +
      'the clear for as long as you keep them.'];
  }

  return ['regressed',
    `the newest sampled recording has no encryption details while ` +
    `${rows.length - plain.length} older one(s) do: encryption was on and is not ` +
    'any more, so everything recorded since it stopped is in the clear.'];
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

export async function listRecordings(auth, account, limit = 2000) {
  let url = `${BASE}/Accounts/${account}/Recordings.json`;
  let params = { PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.recordings ?? []));
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

  const recordings = await listRecordings(auth, account);
  const [state, detail] = verdict(recordings);
  if (state === 'none' || state === 'encrypted') {
    console.log(`${state.padEnd(14)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(14)} ${detail}`);

  const boundary = switchPoint(recordings);
  if (boundary && state !== 'plaintext') {
    console.warn(`  newest unencrypted recording: ${boundary}`);
  }

  console.warn('  repair: Console > Voice > Settings > General, enable Voice ' +
               'Recording Encryption and upload a public key. Keep the private ' +
               'half: without it the encrypted recordings are unrecoverable');
  console.warn('  the recordings already stored in the clear are not re-encrypted ' +
               'when you enable it, so decide separately whether to keep them');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two cases that share a count and differ in every other respect are the ones to pin: encryption switched on last year, leaving an old backlog in the clear, and encryption switched off last month, leaving everything recent in the clear. Both are a mix of encrypted and unencrypted rows. Only the ordering says which, and only one of them is still getting worse.",
"test_py_file": "test_twilio_recording_encryption_audit.py",
"test_py": '''from twilio_recording_encryption_audit import (
    is_encrypted, newest_first, parse_when, switch_point, verdict)

DETAILS = {"type": "rsa-aes-cbc-gcm"}


def rec(day, encrypted=False, sid="RE01"):
    row = {"sid": sid, "date_created": "Tue, %02d Apr 2024 09:12:00 +0000" % day}
    if encrypted:
        row["encryption_details"] = DETAILS
    return row


def test_an_account_with_no_recordings_has_nothing_in_the_clear():
    state, detail = verdict([])
    assert state == "none"
    assert "nothing stored" in detail


def test_every_recording_encrypted_is_the_clean_answer():
    state, _ = verdict([rec(1, True), rec(2, True)])
    assert state == "encrypted"


def test_nothing_encrypted_anywhere_means_it_was_never_switched_on():
    state, detail = verdict([rec(1), rec(2)])
    assert state == "plaintext"
    assert "never been on" in detail


def test_newest_encrypted_and_older_not_is_a_backlog_that_stays():
    state, detail = verdict([rec(1), rec(2), rec(3, True)])
    assert state == "backlog"
    assert "2 older one(s)" in detail
    assert "does not reach backwards" in detail


def test_newest_unencrypted_while_older_ones_are_encrypted_is_a_regression():
    state, detail = verdict([rec(1, True), rec(2, True), rec(3)])
    assert state == "regressed"
    assert "was on and is not any more" in detail


def test_the_two_mixed_cases_are_told_apart_only_by_the_ordering():
    rows = [rec(1), rec(2), rec(3, True)]
    assert verdict(rows)[0] == "backlog"
    assert verdict(list(reversed(rows)))[0] == "backlog"


def test_the_switch_point_is_the_newest_recording_still_in_the_clear():
    assert switch_point([rec(1), rec(5), rec(9, True)]) == \\
        "Tue, 05 Apr 2024 09:12:00 +0000"
    assert switch_point([rec(1, True)]) is None


def test_presence_is_the_test_rather_than_a_value():
    assert is_encrypted({"encryption_details": DETAILS}) is True
    assert is_encrypted({"encryption_details": None}) is False
    assert is_encrypted({}) is False


def test_an_unparseable_date_sorts_last_instead_of_raising():
    rows = newest_first([{"sid": "RE99", "date_created": "whenever"}, rec(4)])
    assert [r["sid"] for r in rows] == ["RE01", "RE99"]


def test_parse_when_reads_rfc_2822():
    assert parse_when("Tue, 18 Apr 2023 09:12:00 +0000") is not None
    assert parse_when("") is None
    assert parse_when("not a date") is None
''',
"test_js_file": "twilio-recording-encryption-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  isEncrypted, newestFirst, parseWhen, switchPoint, verdict,
} from './twilio-recording-encryption-audit.mjs';

const DETAILS = { type: 'rsa-aes-cbc-gcm' };

const rec = (day, encrypted = false, sid = 'RE01') => {
  const row = {
    sid,
    date_created: `Tue, ${String(day).padStart(2, '0')} Apr 2024 09:12:00 +0000`,
  };
  if (encrypted) row.encryption_details = DETAILS;
  return row;
};

test('an account with no recordings has nothing in the clear', () => {
  const [state, detail] = verdict([]);
  assert.equal(state, 'none');
  assert.match(detail, /nothing stored/);
});

test('every recording encrypted is the clean answer', () => {
  assert.equal(verdict([rec(1, true), rec(2, true)])[0], 'encrypted');
});

test('nothing encrypted anywhere means it was never switched on', () => {
  const [state, detail] = verdict([rec(1), rec(2)]);
  assert.equal(state, 'plaintext');
  assert.match(detail, /never been on/);
});

test('newest encrypted and older not is a backlog that stays', () => {
  const [state, detail] = verdict([rec(1), rec(2), rec(3, true)]);
  assert.equal(state, 'backlog');
  assert.match(detail, /2 older one\\(s\\)/);
  assert.match(detail, /does not reach backwards/);
});

test('newest unencrypted while older ones are encrypted is a regression', () => {
  const [state, detail] = verdict([rec(1, true), rec(2, true), rec(3)]);
  assert.equal(state, 'regressed');
  assert.match(detail, /was on and is not any more/);
});

test('the two mixed cases are told apart only by the ordering', () => {
  const rows = [rec(1), rec(2), rec(3, true)];
  assert.equal(verdict(rows)[0], 'backlog');
  assert.equal(verdict([...rows].reverse())[0], 'backlog');
});

test('the switch point is the newest recording still in the clear', () => {
  assert.equal(switchPoint([rec(1), rec(5), rec(9, true)]),
               'Tue, 05 Apr 2024 09:12:00 +0000');
  assert.equal(switchPoint([rec(1, true)]), null);
});

test('presence is the test rather than a value', () => {
  assert.equal(isEncrypted({ encryption_details: DETAILS }), true);
  assert.equal(isEncrypted({ encryption_details: null }), false);
  assert.equal(isEncrypted({}), false);
});

test('an unparseable date sorts last instead of throwing', () => {
  const rows = newestFirst([{ sid: 'RE99', date_created: 'whenever' }, rec(4)]);
  assert.deepEqual(rows.map((r) => r.sid), ['RE01', 'RE99']);
});

test('parseWhen reads RFC 2822', () => {
  assert.notEqual(parseWhen('Tue, 18 Apr 2023 09:12:00 +0000'), null);
  assert.equal(parseWhen(''), null);
  assert.equal(parseWhen('not a date'), null);
});
''',
"faq": [
 ("Can I encrypt the recordings that are already stored?",
  "No. Enabling Voice Recording Encryption applies from the moment it is on, and everything recorded before that stays exactly as it is. That is why the script reports a boundary rather than a yes or no: the backlog is a separate decision, and the only ways to stop holding plaintext media are to delete it or to accept that you are holding it."),
 ("Is this the same problem as recordings piling up and billing forever?",
  "No, but they are the same files. Storage cost is about how many you keep and for how long, and has its own note. This is about who can read them while you keep them. They meet at the fix, though: deleting a recording is the only action that resolves both, which is why a retention policy usually ends up doing more for this finding than encryption does."),
 ("What actually protects the recordings without encryption?",
  "Account credentials, and nothing else. The media is retrievable by anything holding them, so the blast radius of a leaked Auth Token includes every call you have ever recorded. That is the sentence to bring to the review, and it is also the reason this section keeps insisting on read-scoped API keys instead."),
 ("What happens if we lose the private key?",
  "The recordings encrypted with the matching public key become unrecoverable, permanently. Twilio does not hold your private half, which is the entire point of the design. Treat the key as a production secret with the same backup and rotation story as anything else you cannot regenerate, and check that story exists before you enable the feature rather than after."),
 ("Why sample recordings across the whole range rather than the recent ones?",
  "Because the recent ones answer a question nobody asked. If encryption was enabled last year, the newest thousand recordings are all encrypted and the report reads clean while four years of plaintext sit underneath. The finding lives at the boundary, so the sweep has to reach far enough back to include it."),
],
"related": [
 ("/twilio/unreleased-recordings-storage/", "The same recordings considered as a bill"),
 ("/twilio/auth-token-used-instead-of-api-key/", "The credential that can fetch every one of them"),
 ("/twilio/stale-or-orphaned-api-keys/", "Who else still holds a way in"),
],
"citations": [CITE_ENCRYPTION, CITE_RECORDING, CITE_UNUSED, CITE_KEYS],
},

{
"slug": "no-error-log-subscription",
"title": "Nothing subscribes to error logs, so failures age out",
"description": "Debugger alerts are kept 30 days and pushed nowhere unless something subscribes. Read the Event Streams subscriptions and what each one actually carries.",
"h1": "nothing subscribes to error logs, so failures age out",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error logs event stream", "com.twilio.error-logs.error-log.logged",
             "twilio debugger webhook", "twilio alerts 30 day retention",
             "twilio event streams subscription errors"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The postmortem needs the hour before the incident, and the incident was seven weeks ago. That hour does not exist. It is not in the warehouse, not in the logging stack, not in a bucket somewhere: the Debugger holds its alerts for thirty days and pushes them nowhere unless something asks it to, and on this account nothing ever asked.",
"short_answer": """<p>Read <code>GET https://events.twilio.com/v1/Subscriptions</code>, then <code>GET https://events.twilio.com/v1/Subscriptions/{Sid}/SubscribedEvents</code> for each one, and look for a <code>type</code> beginning <code>com.twilio.error-logs</code>. Subscriptions that carry only message or call events are not coverage, however many of them there are.</p>
<p>Pair the survivors with <code>GET https://events.twilio.com/v1/Sinks</code> on <code>sink_sid</code>: a subscription feeding a sink that is not <code>active</code> is subscribed and not delivering. Note the blind spot in the same breath &mdash; the Debugger webhook is console-only and has no read API, so this check can prove coverage exists and cannot prove it does not.</p>""",
"problem": """<p>Twilio records what went wrong on your account and keeps it for thirty days. That retention is not a detail, it is the boundary of every diagnostic in this section: any check that reads the Alerts API can only see back that far, so a failure that started six weeks ago is not a hard question, it is an unanswerable one. The record existed, and then it stopped existing, and nothing anywhere noticed the transition.</p>
<p>Getting the data out is opt-in and there is exactly nothing on by default. No subscription, no Debugger webhook, no copy. That absence produces no symptom of its own &mdash; an account with nothing subscribed behaves identically to one with everything subscribed, right up until the day somebody needs last quarter's errors and finds out they were never kept. It is the same shape as having no backups: the cost is zero every day and then it is the whole thing at once.</p>""",
"why": """<p><strong>Nothing streams by default.</strong> Event Streams exists, error-log event types exist, and an account is created with no subscription to either. As with Usage Triggers, the absence is not a misconfiguration anyone made; it is what every account looks like until somebody deliberately sets one up.</p>
<p><strong>Having subscriptions is not having error coverage.</strong> A team that streams message and call events into a warehouse has a populated <code>Subscriptions</code> list, a working pipeline and a dashboard, and still keeps no errors at all. The list response cannot tell you the difference, because the types live on a subresource: you have to fetch <code>SubscribedEvents</code> per subscription to see what is actually being carried.</p>
<p><strong>Event types are versioned, so exact matching rots.</strong> Pinning the full <code>com.twilio.error-logs.error-log.logged</code> string works until the day it does not, and the failure is silent in the worst direction: the check reports no coverage, or worse, reports coverage missing on an account that has it. Matching the product prefix survives the version bump.</p>
<p><strong>Subscribed is not delivering.</strong> A subscription names a <code>sink_sid</code>, and a sink can be <code>failed</code>, <code>validating</code> or <code>initialized</code> instead of <code>active</code>. Errors subscribed into a dead sink leave you exactly as blind as errors nobody subscribed to, with more moving parts to reassure you. <a href="/twilio/event-streams-sink-failed/">That failure has its own note</a>; this check only needs to know the sink is not carrying anything.</p>
<p><strong>The other route out is invisible to the API.</strong> A Debugger webhook is configured in the console and there is no read endpoint for it. So a clean report from this script means no Event Streams subscription, not no coverage, and the script has to say that out loud rather than let a green line imply something it cannot see.</p>""",
"steps": [
 {"h": "List the subscriptions",
  "body": """<p><code>GET https://events.twilio.com/v1/Subscriptions?PageSize=50</code>, following <code>meta.next_page_url</code>. An empty list is the finding on its own and needs no further calls: nothing is being streamed anywhere, so the Debugger is the only copy of anything.</p>"""},
 {"h": "Fetch the types each one actually carries",
  "body": """<p><code>GET https://events.twilio.com/v1/Subscriptions/{Sid}/SubscribedEvents</code>, one call per subscription. This is the step that separates a busy pipeline from a useful one, and it cannot be skipped, because the subscription list gives you a description and a sink and no indication of what is on the wire.</p>"""},
 {"h": "Match the product prefix, not the whole type",
  "body": """<p>Compare against <code>com.twilio.error-logs</code> rather than the full <code>com.twilio.error-logs.error-log.logged</code>. The suffix carries the resource and the verb and can gain a variant; a prefix comparison keeps matching when it does and costs nothing today.</p>"""},
 {"h": "Resolve every sink_sid before calling it covered",
  "body": """<p><code>GET https://events.twilio.com/v1/Sinks</code> and look each <code>sink_sid</code> up by <code>sid</code>. Anything other than <code>active</code> means the pipe is not carrying, and a <code>sink_sid</code> that is not in the list at all should be reported as unresolved rather than assumed fine.</p>"""},
 {"h": "Subscribe errors somewhere durable, and check the console route too",
  "body": """<p>Create a sink, validate it, and <code>POST https://events.twilio.com/v1/Subscriptions</code> with an error-log type and that <code>SinkSid</code>. Or set a Debugger webhook under Console &rarr; Monitor &rarr; Debugger. Since the script cannot see the second one, confirm it by hand while you are in there.</p>"""},
],
"verify": """<p>Re-run once a subscription is attached to a validated sink.</p>
<pre><code class="language-bash">python3 twilio_error_log_subscription_audit.py
# covered        1 subscription(s) carrying error-log events into an active sink.</code></pre>""",
"code_intro": "One paginated GET over the subscriptions, one per subscription for its types, and one over the sinks &mdash; read access throughout. The classifier takes the three results as plain data rather than as responses, because the judgement is a join across all of them and the join is the thing worth testing: an account with six subscriptions and no error-log type is as blind as an account with none, and the report has to say that in those words.",
"py_file": "twilio_error_log_subscription_audit.py",
"py": '''"""Report a Twilio account with nothing subscribed to its own error logs.

Debugger alerts are retained for thirty days and pushed nowhere unless an Event
Streams subscription or a Debugger webhook exists. That retention window is the
boundary of every other diagnostic on the account, so this is the check about
the window itself.

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
log = logging.getLogger("twilio_error_log_subscription_audit")

EVENTS = "https://events.twilio.com/v1"

ERROR_LOG_PREFIX = "com.twilio.error-logs"
ACTIVE = "active"
RETENTION_DAYS = 30

# Printed, never sent. Kept as a literal so the repair line is the exact shape
# the API expects rather than a paraphrase of it.
REPAIR_TYPES = '{"type":"com.twilio.error-logs.error-log.logged"}'


def is_error_log_type(event_type):
    """True for any error-log event type. Pure.

    Matched on the product prefix rather than the full
    com.twilio.error-logs.error-log.logged string, because the suffix carries a
    resource and a verb and can gain a variant. A pinned full string stops
    matching on the day that happens, and reports an account that has coverage
    as an account that does not.
    """
    return str(event_type or "").strip().lower().startswith(ERROR_LOG_PREFIX)


def verdict(subscriptions, types_by_subscription, sink_status):
    """Classify what this account keeps of its own errors. Pure, so the join can
    be tested without a network.

    types_by_subscription maps a subscription sid to the event types it carries.
    sink_status maps a sink sid to its status. Both are plain data rather than
    responses, because the judgement here is the join across all three and that
    is the part worth pinning.

    Returns (state, detail).
    """
    subs = list(subscriptions or [])
    types = types_by_subscription or {}
    sinks = sink_status or {}

    if not subs:
        return ("none",
                "no Event Streams subscriptions on this account: nothing carries "
                "errors anywhere, so the Debugger is the only copy and it is kept "
                "for %d days." % RETENTION_DAYS)

    carrying = [s for s in subs
                if any(is_error_log_type(t) for t in types.get(s.get("sid"), []))]
    if not carrying:
        return ("no-error-logs",
                "%d subscription(s), none of them carrying a %s type: whatever "
                "else is being streamed, the errors are not, and they age out "
                "after %d days." % (len(subs), ERROR_LOG_PREFIX, RETENTION_DAYS))

    live = [s for s in carrying
            if str(sinks.get(s.get("sink_sid")) or "").strip().lower() == ACTIVE]
    if not live:
        states = sorted({str(sinks.get(s.get("sink_sid")) or "unresolved").strip().lower()
                         for s in carrying})
        return ("sink-not-active",
                "%d subscription(s) carry error logs and every sink behind them "
                "is %s rather than active: subscribed and not delivering is the "
                "same blind spot with more moving parts."
                % (len(carrying), ", ".join(states)))

    return ("covered",
            "%d subscription(s) carrying error-log events into an active sink."
            % len(live))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_all(session, url, key, limit=200):
    """Page a newer-domain list. meta.next_page_url is absolute here, unlike the
    next_page_uri path the 2010-04-01 API returns."""
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def subscribed_types(session, subscriptions):
    """One call per subscription. The types live on a subresource, so the list
    response cannot tell a busy pipeline from a useful one."""
    types = {}
    for subscription in subscriptions:
        sid = subscription.get("sid")
        events = list_all(session, "%s/Subscriptions/%s/SubscribedEvents" % (EVENTS, sid),
                          "types")
        types[sid] = [e.get("type") for e in events]
    return types


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=200,
                    help="stop after this many subscriptions")
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

    subscriptions = list_all(session, EVENTS + "/Subscriptions", "subscriptions",
                             args.max_subscriptions)
    types = subscribed_types(session, subscriptions) if subscriptions else {}
    sinks = {s.get("sid"): s.get("status")
             for s in list_all(session, EVENTS + "/Sinks", "sinks")}

    for subscription in subscriptions:
        sid = subscription.get("sid")
        log.info("  %s sink=%s status=%s types=%s", sid,
                 subscription.get("sink_sid", "?"),
                 sinks.get(subscription.get("sink_sid"), "unresolved"),
                 ", ".join(t for t in types.get(sid, []) if t) or "none")

    state, detail = verdict(subscriptions, types, sinks)
    if state == "covered":
        log.info("%-16s %s", state, detail)
        return 0

    log.warning("%-16s %s", state, detail)
    log.warning("  repair: create and validate a sink, then POST %s/Subscriptions "
                "Description=error-logs SinkSid={SinkSid} Types=%s",
                EVENTS, REPAIR_TYPES)
    log.warning("  or set a Debugger webhook: Console > Monitor > Debugger > Webhook")
    log.warning("  note: the Debugger webhook has no read API, so this check can "
                "prove coverage exists and cannot prove it does not")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-error-log-subscription-audit.mjs",
"js": '''/**
 * Report a Twilio account with nothing subscribed to its own error logs.
 *
 * Debugger alerts are retained for thirty days and pushed nowhere unless an
 * Event Streams subscription or a Debugger webhook exists. That window is the
 * boundary of every other diagnostic on the account.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const EVENTS = 'https://events.twilio.com/v1';

const ERROR_LOG_PREFIX = 'com.twilio.error-logs';
const ACTIVE = 'active';
const RETENTION_DAYS = 30;

// Printed, never sent. Kept as a literal so the repair line is the exact shape
// the API expects rather than a paraphrase of it.
const REPAIR_TYPES = '{"type":"com.twilio.error-logs.error-log.logged"}';

/**
 * True for any error-log event type. Pure. Matched on the product prefix rather
 * than the full type string, because the suffix carries a resource and a verb
 * and can gain a variant.
 */
export function isErrorLogType(eventType) {
  return String(eventType ?? '').trim().toLowerCase().startsWith(ERROR_LOG_PREFIX);
}

/**
 * Classify what this account keeps of its own errors. Pure, so the join can be
 * tested without a network. Returns [state, detail].
 */
export function verdict(subscriptions, typesBySubscription, sinkStatus) {
  const subs = [...(subscriptions ?? [])];
  const types = typesBySubscription ?? {};
  const sinks = sinkStatus ?? {};

  if (subs.length === 0) {
    return ['none',
      'no Event Streams subscriptions on this account: nothing carries errors ' +
      `anywhere, so the Debugger is the only copy and it is kept for ` +
      `${RETENTION_DAYS} days.`];
  }

  const carrying = subs.filter(
    (s) => (types[s.sid] ?? []).some(isErrorLogType));
  if (carrying.length === 0) {
    return ['no-error-logs',
      `${subs.length} subscription(s), none of them carrying a ` +
      `${ERROR_LOG_PREFIX} type: whatever else is being streamed, the errors ` +
      `are not, and they age out after ${RETENTION_DAYS} days.`];
  }

  const live = carrying.filter(
    (s) => String(sinks[s.sink_sid] ?? '').trim().toLowerCase() === ACTIVE);
  if (live.length === 0) {
    const states = [...new Set(carrying.map(
      (s) => String(sinks[s.sink_sid] ?? 'unresolved').trim().toLowerCase()))].sort();
    return ['sink-not-active',
      `${carrying.length} subscription(s) carry error logs and every sink behind ` +
      `them is ${states.join(', ')} rather than active: subscribed and not ` +
      'delivering is the same blind spot with more moving parts.'];
  }

  return ['covered',
    `${live.length} subscription(s) carrying error-log events into an active sink.`];
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

export async function listAll(auth, url, key, limit = 200) {
  let next = url;
  let params = { PageSize: 50 };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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

  const subscriptions = await listAll(auth, `${EVENTS}/Subscriptions`, 'subscriptions');

  const types = {};
  for (const s of subscriptions) {
    const events = await listAll(
      auth, `${EVENTS}/Subscriptions/${s.sid}/SubscribedEvents`, 'types');
    types[s.sid] = events.map((e) => e.type);
  }

  const sinks = Object.fromEntries(
    (await listAll(auth, `${EVENTS}/Sinks`, 'sinks')).map((s) => [s.sid, s.status]));

  for (const s of subscriptions) {
    const carried = (types[s.sid] ?? []).filter(Boolean).join(', ') || 'none';
    console.log(`  ${s.sid} sink=${s.sink_sid ?? '?'} ` +
                `status=${sinks[s.sink_sid] ?? 'unresolved'} types=${carried}`);
  }

  const [state, detail] = verdict(subscriptions, types, sinks);
  if (state === 'covered') {
    console.log(`${state.padEnd(16)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(16)} ${detail}`);
  console.warn(`  repair: create and validate a sink, then POST ${EVENTS}/Subscriptions ` +
               `Description=error-logs SinkSid={SinkSid} Types=${REPAIR_TYPES}`);
  console.warn('  or set a Debugger webhook: Console > Monitor > Debugger > Webhook');
  console.warn('  note: the Debugger webhook has no read API, so this check can ' +
               'prove coverage exists and cannot prove it does not');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The account worth writing a test for is the one with a working pipeline and no error coverage: six subscriptions, an active sink, a warehouse full of message events, and not one error kept past thirty days. It looks like the most instrumented account in the report and it is exactly as blind as the empty one. The other case pinned here is the unresolvable sink, because a <code>sink_sid</code> missing from the list must not fall through to covered.",
"test_py_file": "test_twilio_error_log_subscription_audit.py",
"test_py": '''from twilio_error_log_subscription_audit import is_error_log_type, verdict

ERRORS = "com.twilio.error-logs.error-log.logged"
MESSAGES = "com.twilio.messaging.message.delivered"


def sub(sid="DF01", sink="DG01"):
    return {"sid": sid, "sink_sid": sink, "description": "warehouse"}


def test_an_account_with_no_subscriptions_keeps_nothing_past_the_window():
    state, detail = verdict([], {}, {})
    assert state == "none"
    assert "30 days" in detail


def test_a_busy_pipeline_with_no_error_types_is_just_as_blind():
    state, detail = verdict([sub("DF01"), sub("DF02")],
                            {"DF01": [MESSAGES], "DF02": [MESSAGES]},
                            {"DG01": "active"})
    assert state == "no-error-logs"
    assert "whatever else is being streamed" in detail


def test_error_logs_into_an_active_sink_is_coverage():
    state, _ = verdict([sub()], {"DF01": [MESSAGES, ERRORS]}, {"DG01": "active"})
    assert state == "covered"


def test_error_logs_into_a_failed_sink_is_subscribed_and_not_delivering():
    state, detail = verdict([sub()], {"DF01": [ERRORS]}, {"DG01": "failed"})
    assert state == "sink-not-active"
    assert "failed" in detail


def test_a_sink_sid_that_is_not_in_the_list_is_unresolved_rather_than_fine():
    state, detail = verdict([sub(sink="DG99")], {"DF01": [ERRORS]}, {"DG01": "active"})
    assert state == "sink-not-active"
    assert "unresolved" in detail


def test_one_live_error_subscription_outweighs_the_dead_ones_beside_it():
    state, _ = verdict([sub("DF01", "DG_DEAD"), sub("DF02", "DG01")],
                       {"DF01": [ERRORS], "DF02": [ERRORS]},
                       {"DG01": "active", "DG_DEAD": "failed"})
    assert state == "covered"


def test_the_type_is_matched_on_the_product_prefix_not_the_whole_string():
    assert is_error_log_type(ERRORS) is True
    assert is_error_log_type("com.twilio.error-logs.error-log.logged.v2") is True
    assert is_error_log_type("COM.TWILIO.ERROR-LOGS.ERROR-LOG.LOGGED") is True
    assert is_error_log_type(MESSAGES) is False
    assert is_error_log_type(None) is False
''',
"test_js_file": "twilio-error-log-subscription-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isErrorLogType, verdict } from './twilio-error-log-subscription-audit.mjs';

const ERRORS = 'com.twilio.error-logs.error-log.logged';
const MESSAGES = 'com.twilio.messaging.message.delivered';

const sub = (sid = 'DF01', sink = 'DG01') => ({
  sid, sink_sid: sink, description: 'warehouse',
});

test('an account with no subscriptions keeps nothing past the window', () => {
  const [state, detail] = verdict([], {}, {});
  assert.equal(state, 'none');
  assert.match(detail, /30 days/);
});

test('a busy pipeline with no error types is just as blind', () => {
  const [state, detail] = verdict([sub('DF01'), sub('DF02')],
                                  { DF01: [MESSAGES], DF02: [MESSAGES] },
                                  { DG01: 'active' });
  assert.equal(state, 'no-error-logs');
  assert.match(detail, /whatever else is being streamed/);
});

test('error logs into an active sink is coverage', () => {
  assert.equal(
    verdict([sub()], { DF01: [MESSAGES, ERRORS] }, { DG01: 'active' })[0],
    'covered');
});

test('error logs into a failed sink is subscribed and not delivering', () => {
  const [state, detail] = verdict([sub()], { DF01: [ERRORS] }, { DG01: 'failed' });
  assert.equal(state, 'sink-not-active');
  assert.match(detail, /failed/);
});

test('a sink_sid that is not in the list is unresolved rather than fine', () => {
  const [state, detail] = verdict([sub('DF01', 'DG99')], { DF01: [ERRORS] },
                                  { DG01: 'active' });
  assert.equal(state, 'sink-not-active');
  assert.match(detail, /unresolved/);
});

test('one live error subscription outweighs the dead ones beside it', () => {
  const [state] = verdict([sub('DF01', 'DG_DEAD'), sub('DF02', 'DG01')],
                          { DF01: [ERRORS], DF02: [ERRORS] },
                          { DG01: 'active', DG_DEAD: 'failed' });
  assert.equal(state, 'covered');
});

test('the type is matched on the product prefix not the whole string', () => {
  assert.equal(isErrorLogType(ERRORS), true);
  assert.equal(isErrorLogType('com.twilio.error-logs.error-log.logged.v2'), true);
  assert.equal(isErrorLogType('COM.TWILIO.ERROR-LOGS.ERROR-LOG.LOGGED'), true);
  assert.equal(isErrorLogType(MESSAGES), false);
  assert.equal(isErrorLogType(null), false);
});
''',
"faq": [
 ("The Debugger shows my errors. Is that not enough?",
  "It is enough for thirty days and for one person looking at a screen. It is not enough for a postmortem written seven weeks later, for an alert that pages somebody, or for a query that counts how often something happened. Those all need the events somewhere you control, and getting them there is a subscription you have to create."),
 ("We already stream events into our warehouse. Are we covered?",
  "Only if one of those subscriptions carries an error-log type, which the subscription list will not tell you. Streaming message and call events is a different subscription with different types, and it is by far the most common way an account ends up with a real pipeline, a real dashboard and no errors in either. The subresource is the only place the answer lives."),
 ("Why match a prefix instead of the exact event type?",
  "Because the exact type carries a resource and a verb on the end and those can change. A check pinned to the full string keeps working until the day a variant appears, and then it reports an account with perfectly good coverage as having none. Matching com.twilio.error-logs costs nothing now and survives that."),
 ("The script says none. Does that definitely mean nothing is kept?",
  "No, and it says so in its own output. A Debugger webhook is configured in the console and has no read endpoint, so an account can be pushing every alert somewhere without leaving a trace this script can find. Treat a none as prove-it-by-hand rather than as a confirmed finding, and go look at the Debugger settings page."),
 ("What about the sink itself failing later?",
  "That is a different check and it has its own note, because it is a different question: this one asks whether anything is subscribed, that one asks whether the pipe is carrying. They overlap in one state, where an error-log subscription points at a sink that is not active, and the report names it separately so you know which of the two things to go and fix."),
],
"related": [
 ("/twilio/event-streams-sink-failed/", "The pipe that was carrying errors and stopped"),
 ("/twilio/no-usage-trigger-configured/", "The other alarm an account starts without"),
 ("/twilio/status-callback-webhook-failing-11200/", "Delivery state you are also not keeping"),
],
"citations": [CITE_ERROR_LOGS, CITE_DEBUGGING, CITE_SUBSCRIPTION, CITE_SINK],
},

]
