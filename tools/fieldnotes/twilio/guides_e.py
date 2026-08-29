#!/usr/bin/env python3
"""/twilio/ field notes, batch E — the writing.

Four failures in the plumbing between a number, a Messaging Service and your
application. Two of them return an error code on every send (21704, 21606) and
two of them return nothing at all: a number whose webhook edits have been ignored
for months, and a service that has never once told you a message failed.

Read-only throughout, like the rest of the section: an API Key with read access,
never the account auth token, every request a GET, and the repair printed for a
human to run rather than performed by a script holding a credential that can
send messages and spend money.
"""

CITE_PN = ("IncomingPhoneNumber resource — Twilio Docs",
           "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_APPS = ("Application resource — Twilio Docs",
             "https://www.twilio.com/docs/usage/api/applications")
CITE_WEBHOOKS = ("Webhooks (HTTP callbacks) — Twilio Docs",
                 "https://www.twilio.com/docs/usage/webhooks")
CITE_TWIML_VOICE = ("TwiML for Programmable Voice — Twilio Docs",
                    "https://www.twilio.com/docs/voice/twiml")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_SERVICE_PN = ("Messaging Service PhoneNumber resource — Twilio Docs",
                   "https://www.twilio.com/docs/messaging/api/phonenumber-resource")
CITE_ALPHA = ("Messaging Service AlphaSender resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/alphasender-resource")
CITE_SERVICES_GUIDE = ("Messaging Services — Twilio Docs",
                       "https://www.twilio.com/docs/messaging/services")
CITE_21704 = ("Error 21704: the Messaging Service contains no phone numbers — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21704")
CITE_21703 = ("Error 21703: no phone number available to send — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21703")
CITE_21606 = ("Error 21606: 'From' is not a valid message-capable number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21606")
CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_STATUS = ("Outbound message status in status callbacks — Twilio Docs",
               "https://www.twilio.com/docs/messaging/guides/outbound-message-status-in-status-callbacks")
CITE_SINK = ("Event Streams Sink resource — Twilio Docs",
             "https://www.twilio.com/docs/events/event-streams/sink-resource")
CITE_SUB = ("Event Streams Subscription resource — Twilio Docs",
            "https://www.twilio.com/docs/events/event-streams/subscription-resource")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "number-conflicting-url-and-application-sid",
"title": "A number with an Application SID ignores its own voice_url",
"description": "When voice_application_sid is set it wins outright and voice_url is ignored, so every edit to the number changes nothing and calls keep hitting an old app.",
"h1": "a number with an Application SID ignores its own voice_url",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio voice_application_sid", "twilio voice_url ignored",
             "twilio application sid precedence", "twilio twiml app not updating",
             "twilio number webhook has no effect"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You changed <code>voice_url</code> on the number this morning. You changed it again in the console an hour later and watched the page save. Calls keep arriving at an endpoint you retired last spring. Nothing is broken and nothing is cached &mdash; <code>voice_application_sid</code> is set on that number, and while it is, the field you keep editing is not read at all.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code> and flag any number where <code>voice_application_sid</code> is non-empty <em>and</em> <code>voice_url</code> is also non-empty and different. Resolve what actually answers with <code>GET /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json</code> &mdash; <code>voice_url</code>, <code>voice_fallback_url</code> and <code>status_callback</code> all live there once an app is attached.</p>
<p>Flag a second shape while you are in there: an Application whose <code>voice_url</code> is empty. A number pointed at it routes calls nowhere, and the number's own URL cannot rescue it. The same precedence applies to <code>sms_application_sid</code> over <code>sms_url</code>.</p>""",
"problem": """<p>This is a configuration bug that presents as a caching bug. The edit succeeds, the API returns the new value, the console shows it, and behaviour does not change. So the next hypothesis is propagation delay, then a stale deploy, then DNS, and an afternoon disappears into a system that is doing exactly what it was told by a field nobody looked at.</p>
<p>Applications get attached by accident more often than by design. The Voice quickstarts create a TwiML App, client SDK setups require one, and a number bought during a spike gets pointed at whatever app was in the dropdown. Two years later the app is the effective handler for eleven numbers, its URL points at a host that no longer exists, and every number still carries a tidy-looking <code>voice_url</code> that has not served a call since it was set.</p>""",
"why": """<p><strong>Precedence is silent and absolute.</strong> When <code>voice_application_sid</code> is populated, Twilio requests the Application's URLs and ignores the number's entirely &mdash; not as a fallback, not as a merge. There is no warning on the write that sets a URL which will never be read, because the API has no opinion about which field you meant.</p>
<p><strong>The ignored field stays visible everywhere.</strong> The API returns it, the console renders it in an editable box, and infrastructure code keeps setting it. Every surface a developer checks says the number points at the new endpoint, so the conclusion is that Twilio is wrong rather than that the value is inert.</p>
<p><strong>One app fronts many numbers.</strong> That is the point of an Application, and it is why the repair has two shapes with very different blast radii. Editing the app moves every number attached to it; detaching the app moves one. Choosing without listing the other numbers on that SID is how a fix for one number takes out ten.</p>
<p><strong>An empty app URL is a dead end, not an error.</strong> An Application with no <code>voice_url</code> gives Twilio nowhere to go for a call the number was configured to receive, and the number's own URL is still ignored. Nothing in the numbers list reveals it; the finding only exists once the Application resource has been read.</p>""",
"steps": [
 {"h": "List every number and read both channels",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, following <code>next_page_uri</code>. Voice and SMS carry independent pairs of fields, and a number is routinely clean on one and shadowed on the other.</p>"""},
 {"h": "Fetch each referenced Application exactly once",
  "body": """<p>Collect the distinct values of <code>voice_application_sid</code> and <code>sms_application_sid</code>, then <code>GET /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json</code> per SID and cache the result. A busy account points dozens of numbers at a handful of apps, so this is a few requests rather than one per number.</p>"""},
 {"h": "Compare the two URLs instead of checking that one is set",
  "body": """<p>A number whose <code>voice_url</code> matches the app's <code>voice_url</code> is harmless noise: both point at the same place and no traffic goes anywhere surprising. The finding is a number whose own URL <em>differs</em> from the one that actually answers, because that gap is exactly the wrong mental model somebody is currently debugging.</p>"""},
 {"h": "Flag applications with no URL at all",
  "body": """<p>An empty <code>voice_url</code> on the Application routes calls nowhere while the number looks fully configured. Read <code>voice_fallback_url</code> and <code>status_callback</code> from the same resource while you have it: those moved to the app too, and an audit that reads them off the number reports the wrong answer.</p>"""},
 {"h": "Pick the repair by blast radius, then re-run",
  "body": """<p>Two options. Update the app &mdash; <code>POST /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json</code> with <code>VoiceUrl</code> &mdash; which moves every number attached to it. Or detach it, <code>POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json</code> with an empty <code>VoiceApplicationSid</code>, so the number's own <code>voice_url</code> starts being read. List the other numbers on that SID before choosing.</p>"""},
],
"verify": """<p>Re-run the script. Every number should report <code>direct</code> or <code>app-routed</code>, and no number should be carrying a URL that nothing reads.</p>
<pre><code class="language-bash">python3 twilio_number_app_precedence_audit.py
# 14 number(s), 0 with a shadowed handler</code></pre>""",
"code_intro": "One paginated GET over the numbers, one GET per distinct Application SID, cached &mdash; an API Key with read access covers all of it. The precedence rule is the entire pure function, because the whole failure is a mental model, and a mental model belongs somewhere you can read it next to its tests.",
"py_file": "twilio_number_app_precedence_audit.py",
"py": '''"""Report Twilio numbers whose webhook URLs are shadowed by an Application SID.

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
log = logging.getLogger("twilio_number_app_precedence_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# (channel, url field, application sid field). The Application resource happens
# to name its URLs identically, which is what lets one comparison serve both.
CHANNELS = (
    ("voice", "voice_url", "voice_application_sid"),
    ("sms", "sms_url", "sms_application_sid"),
)


def verdict(number, apps=None):
    """Classify one IncomingPhoneNumber against the apps it references.

    Pure, so the precedence rule is testable without a network. `apps` maps an
    Application SID to that Application resource. When a channel carries an
    application sid, the Application is the effective handler and the number's
    own url is never requested.

    Returns (state, detail).
    """
    apps = apps or {}
    unresolved, dead, shadowed, routed, direct = [], [], [], [], []

    for channel, url_field, app_field in CHANNELS:
        app_sid = str(number.get(app_field) or "").strip()
        own = str(number.get(url_field) or "").strip()

        if not app_sid:
            if own:
                direct.append("%s serves %s" % (channel, own))
            continue

        app = apps.get(app_sid)
        if app is None:
            unresolved.append("%s (%s)" % (channel, app_sid))
            continue

        live = str(app.get(url_field) or "").strip()
        if not live:
            dead.append("%s: app %s has no %s" % (channel, app_sid, url_field))
            continue
        if own and own != live:
            shadowed.append("%s: %s on the number is ignored, app %s serves %s"
                            % (channel, own, app_sid, live))
            continue
        routed.append("%s via app %s" % (channel, app_sid))

    if unresolved:
        return ("unresolved",
                "an application sid is set but that application was not read: %s"
                % ", ".join(unresolved))
    if dead:
        return ("routes-nowhere",
                "%s. The number's own url cannot rescue this: the app wins while "
                "it is attached." % "; ".join(dead))
    if shadowed:
        return ("shadowed",
                "%s. Editing the number changes nothing." % "; ".join(shadowed))
    if routed:
        return ("app-routed", "handled by its application: " + ", ".join(routed))
    if direct:
        return ("direct", "no application sid, so the number's own url is read: "
                + ", ".join(direct))
    return ("idle", "no voice or sms handler and no application sid")


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
    """Fetch each referenced Application once and cache it by SID."""
    sids = set()
    for n in numbers:
        for _channel, _url_field, app_field in CHANNELS:
            sid = str(n.get(app_field) or "").strip()
            if sid:
                sids.add(sid)
    return {sid: get(session, "%s/Accounts/%s/Applications/%s.json"
                     % (BASE, account, sid))
            for sid in sorted(sids)}


def sharing(numbers, app_sid):
    """Every number attached to one app. Pure, and the reason it exists is that
    editing an app moves all of them at once."""
    out = []
    for n in numbers:
        for _channel, _url_field, app_field in CHANNELS:
            if str(n.get(app_field) or "").strip() == app_sid:
                out.append(n.get("phone_number") or n.get("sid"))
                break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000,
                    help="stop paging after this many numbers")
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
        line = "%-14s %s  %s" % (state, n.get("phone_number", "?"), detail)
        if state in ("direct", "app-routed", "idle"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for _channel, _url_field, app_field in CHANNELS:
            sid = str(n.get(app_field) or "").strip()
            if not sid:
                continue
            peers = sharing(numbers, sid)
            log.warning("  app %s also fronts %d number(s): %s",
                        sid, len(peers), ", ".join(str(p) for p in peers[:5]))
        log.warning("  repair: either update the app, POST %s/Accounts/%s/"
                    "Applications/{AppSid}.json VoiceUrl=https://.../voice, which "
                    "moves every number above; or detach it, POST %s/Accounts/%s/"
                    "IncomingPhoneNumbers/%s.json VoiceApplicationSid= (empty), "
                    "so the number's own voice_url is read again.",
                    BASE, account, BASE, account, n.get("sid"))

    log.info("%d number(s), %d with a shadowed handler", len(numbers), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-number-app-precedence-audit.mjs",
"js": '''/**
 * Report Twilio numbers whose webhook URLs are shadowed by an Application SID.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// [channel, url field, application sid field]. The Application resource names
// its URLs identically, which is what lets one comparison serve both.
const CHANNELS = [
  ['voice', 'voice_url', 'voice_application_sid'],
  ['sms', 'sms_url', 'sms_application_sid'],
];

/**
 * Classify one IncomingPhoneNumber against the apps it references. Pure, so the
 * precedence rule is testable without a network. `apps` maps an Application SID
 * to that Application: when a channel carries one, the Application is the
 * effective handler and the number's own url is never requested.
 * Returns [state, detail].
 */
export function verdict(number, apps = {}) {
  const unresolved = [];
  const dead = [];
  const shadowed = [];
  const routed = [];
  const direct = [];

  for (const [channel, urlField, appField] of CHANNELS) {
    const appSid = String(number[appField] ?? '').trim();
    const own = String(number[urlField] ?? '').trim();

    if (!appSid) {
      if (own) direct.push(`${channel} serves ${own}`);
      continue;
    }

    const app = apps[appSid];
    if (app === undefined) { unresolved.push(`${channel} (${appSid})`); continue; }

    const live = String(app[urlField] ?? '').trim();
    if (!live) { dead.push(`${channel}: app ${appSid} has no ${urlField}`); continue; }
    if (own && own !== live) {
      shadowed.push(`${channel}: ${own} on the number is ignored, app ${appSid} serves ${live}`);
      continue;
    }
    routed.push(`${channel} via app ${appSid}`);
  }

  if (unresolved.length) {
    return ['unresolved',
      `an application sid is set but that application was not read: ${unresolved.join(', ')}`];
  }
  if (dead.length) {
    return ['routes-nowhere',
      `${dead.join('; ')}. The number's own url cannot rescue this: the app wins ` +
      'while it is attached.'];
  }
  if (shadowed.length) {
    return ['shadowed', `${shadowed.join('; ')}. Editing the number changes nothing.`];
  }
  if (routed.length) return ['app-routed', `handled by its application: ${routed.join(', ')}`];
  if (direct.length) {
    return ['direct', `no application sid, so the number's own url is read: ${direct.join(', ')}`];
  }
  return ['idle', 'no voice or sms handler and no application sid'];
}

/** Every number attached to one app. Pure: editing an app moves all of them. */
export function sharing(numbers, appSid) {
  const out = [];
  for (const n of numbers) {
    for (const [, , appField] of CHANNELS) {
      if (String(n[appField] ?? '').trim() === appSid) {
        out.push(n.phone_number ?? n.sid);
        break;
      }
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
    for (const [, , appField] of CHANNELS) {
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
    const line = `${state.padEnd(14)} ${n.phone_number ?? '?'}  ${detail}`;
    if (state === 'direct' || state === 'app-routed' || state === 'idle') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    for (const [, , appField] of CHANNELS) {
      const sid = String(n[appField] ?? '').trim();
      if (!sid) continue;
      const peers = sharing(numbers, sid);
      console.warn(`  app ${sid} also fronts ${peers.length} number(s): ` +
                   `${peers.slice(0, 5).join(', ')}`);
    }
    console.warn(`  repair: either update the app, POST ${BASE}/Accounts/${account}` +
                 '/Applications/{AppSid}.json VoiceUrl=https://.../voice, which moves ' +
                 `every number above; or detach it, POST ${BASE}/Accounts/${account}` +
                 `/IncomingPhoneNumbers/${n.sid}.json VoiceApplicationSid= (empty), ` +
                 "so the number's own voice_url is read again.");
  }

  console.log(`${numbers.length} number(s), ${bad} with a shadowed handler`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three rules carry the note. A number whose own URL matches the app's is <em>not</em> a finding, because nothing surprising happens there and a report full of those gets ignored. A number whose URL differs is the finding, even though both fields look set and healthy. And an Application with no URL is worse than a shadowed one, so it gets its own state rather than being folded into the same bucket.",
"test_py_file": "test_twilio_number_app_precedence_audit.py",
"test_py": '''from twilio_number_app_precedence_audit import sharing, verdict

APP = "AP11111111111111111111111111111111"
OTHER = "AP22222222222222222222222222222222"


def test_a_different_url_on_the_number_is_shadowed():
    # The whole note: this number looks configured and the field is inert.
    state, detail = verdict(
        {"voice_application_sid": APP, "voice_url": "https://new.example.com/voice"},
        {APP: {"voice_url": "https://retired.example.com/voice"}})
    assert state == "shadowed"
    assert "retired.example.com" in detail
    assert "Editing the number changes nothing" in detail


def test_the_same_url_on_both_is_not_a_finding():
    state, _ = verdict(
        {"voice_application_sid": APP, "voice_url": "https://app.example.com/voice"},
        {APP: {"voice_url": "https://app.example.com/voice"}})
    assert state == "app-routed"


def test_an_application_with_no_url_routes_nowhere():
    state, detail = verdict(
        {"voice_application_sid": APP, "voice_url": "https://app.example.com/voice"},
        {APP: {"voice_url": ""}})
    assert state == "routes-nowhere"
    assert "has no voice_url" in detail


def test_sms_precedence_is_checked_independently():
    state, detail = verdict(
        {"voice_url": "https://app.example.com/voice",
         "sms_application_sid": APP, "sms_url": "https://new.example.com/sms"},
        {APP: {"sms_url": "https://retired.example.com/sms"}})
    assert state == "shadowed"
    assert "sms:" in detail


def test_no_application_sid_means_the_number_is_read():
    state, detail = verdict({"voice_url": "https://app.example.com/voice"})
    assert state == "direct"
    assert "app.example.com" in detail


def test_an_unread_application_is_never_guessed_at():
    state, _ = verdict({"voice_application_sid": APP}, {})
    assert state == "unresolved"


def test_a_number_with_nothing_configured_is_idle():
    assert verdict({"voice_url": "", "sms_url": None})[0] == "idle"


def test_sharing_lists_every_number_on_one_app_once():
    numbers = [
        {"phone_number": "+15550001111", "voice_application_sid": APP,
         "sms_application_sid": APP},
        {"phone_number": "+15550002222", "sms_application_sid": APP},
        {"phone_number": "+15550003333", "voice_application_sid": OTHER},
    ]
    assert sharing(numbers, APP) == ["+15550001111", "+15550002222"]
    assert sharing(numbers, OTHER) == ["+15550003333"]
''',
"test_js_file": "twilio-number-app-precedence-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sharing, verdict } from './twilio-number-app-precedence-audit.mjs';

const APP = 'AP11111111111111111111111111111111';
const OTHER = 'AP22222222222222222222222222222222';

test('a different url on the number is shadowed', () => {
  const [state, detail] = verdict(
    { voice_application_sid: APP, voice_url: 'https://new.example.com/voice' },
    { [APP]: { voice_url: 'https://retired.example.com/voice' } });
  assert.equal(state, 'shadowed');
  assert.match(detail, /retired\\.example\\.com/);
  assert.match(detail, /Editing the number changes nothing/);
});

test('the same url on both is not a finding', () => {
  const [state] = verdict(
    { voice_application_sid: APP, voice_url: 'https://app.example.com/voice' },
    { [APP]: { voice_url: 'https://app.example.com/voice' } });
  assert.equal(state, 'app-routed');
});

test('an application with no url routes nowhere', () => {
  const [state, detail] = verdict(
    { voice_application_sid: APP, voice_url: 'https://app.example.com/voice' },
    { [APP]: { voice_url: '' } });
  assert.equal(state, 'routes-nowhere');
  assert.match(detail, /has no voice_url/);
});

test('sms precedence is checked independently', () => {
  const [state, detail] = verdict(
    { voice_url: 'https://app.example.com/voice',
      sms_application_sid: APP, sms_url: 'https://new.example.com/sms' },
    { [APP]: { sms_url: 'https://retired.example.com/sms' } });
  assert.equal(state, 'shadowed');
  assert.match(detail, /sms:/);
});

test('no application sid means the number is read', () => {
  const [state, detail] = verdict({ voice_url: 'https://app.example.com/voice' });
  assert.equal(state, 'direct');
  assert.match(detail, /app\\.example\\.com/);
});

test('an unread application is never guessed at', () => {
  assert.equal(verdict({ voice_application_sid: APP }, {})[0], 'unresolved');
});

test('a number with nothing configured is idle', () => {
  assert.equal(verdict({ voice_url: '', sms_url: null })[0], 'idle');
});

test('sharing lists every number on one app once', () => {
  const numbers = [
    { phone_number: '+15550001111', voice_application_sid: APP, sms_application_sid: APP },
    { phone_number: '+15550002222', sms_application_sid: APP },
    { phone_number: '+15550003333', voice_application_sid: OTHER },
  ];
  assert.deepEqual(sharing(numbers, APP), ['+15550001111', '+15550002222']);
  assert.deepEqual(sharing(numbers, OTHER), ['+15550003333']);
});
''',
"faq": [
 ("Which one wins, voice_url or voice_application_sid?",
  "The Application SID, outright. While voice_application_sid is populated Twilio requests the Application's voice_url, voice_fallback_url and status_callback, and the number's own copies of those fields are never read. The same holds for sms_application_sid over sms_url."),
 ("Then why does the console still let me edit voice_url?",
  "Because the field is still a real, writable property of the number; it just is not consulted while an app is attached. That is the trap: the write succeeds, the read shows your value, and behaviour is governed by a different resource entirely."),
 ("Should I fix the Application or detach it?",
  "Depends how many numbers share the app. Updating the app moves all of them at once, which is right when the app is the intended routing layer and wrong when one number needs to diverge. Detaching restores that single number to its own voice_url and leaves the others alone, which is why the script prints the peer list first."),
 ("What happens if the Application has no voice_url?",
  "Calls to any number attached to it have nowhere to go, and the number's own URL does not step in. This is the state worth fixing first, because it is a live outage rather than a stale endpoint, and it is invisible until you fetch the Application resource itself."),
 ("Does the script change anything?",
  "No. It issues GETs against IncomingPhoneNumbers and Applications and prints both repair options with the SIDs filled in. Everything in this section runs on an API Key with read access, so it cannot rewrite a number even if the key leaked."),
],
"related": [
 ("/twilio/phone-number-missing-fallback-url/", "Numbers whose live handler has no fallback"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still points at the demo TwiML"),
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS disappears into a blank sms_url"),
],
"citations": [CITE_APPS, CITE_PN, CITE_WEBHOOKS, CITE_TWIML_VOICE],
},


{
"slug": "messaging-service-empty-sender-pool",
"title": "An empty sender pool fails every send with error 21704",
"description": "The Messaging Service exists and looks configured, but no sender was ever added, so Twilio has no From to pick and rejects before any carrier hop.",
"h1": "an empty sender pool fails every send with error 21704",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 21704", "messaging service contains no phone numbers",
             "twilio sender pool empty", "twilio messagingservicesid 21704",
             "twilio messaging service no senders"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Messaging Service was created by a setup script in March. It has a friendly name, a SID your application has been passing on every send since, an inbound webhook, a status callback &mdash; and nothing in the sender pool. Every <code>Messages.create</code> against it comes back <code>21704</code>, &ldquo;The Messaging Service contains no phone numbers&rdquo;, before a carrier is ever involved.",
"short_answer": """<p>Per service, read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> and flag an empty <code>phone_numbers[]</code>. Then read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/AlphaSenders</code> and check <code>alpha_senders[]</code>. Both empty guarantees <code>21704</code> on every send that passes that <code>MessagingServiceSid</code>.</p>
<p>Read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/ShortCodes</code> too before you call a pool empty. A service whose only sender is a short code has no phone numbers and no alpha senders and still sends perfectly well, and a report that flags it teaches everyone to ignore the report.</p>""",
"problem": """<p>An empty pool is the failure mode of automation. Nobody creates a Messaging Service by hand and forgets to add a number &mdash; the console walks you through the sender pool on the way in. Terraform, a bootstrap script or a copied setup notebook creates the service in one call and adds senders in another, and when the second call is missing, skipped in a dry run, or applied against the wrong account, you get a service that exists, reports healthy, and cannot send.</p>
<p>The same shape appears at the other end of a service's life. The last number in the pool is released during a cleanup, or moved to a new service during a migration, and the old SID is still hard-coded in one job nobody remembered. That job has been returning <code>21704</code> nightly ever since, and because the failure is at request time it never becomes a Message row, never appears in the Messages list, and never shows up on the bill.</p>""",
"why": """<p><strong>The service looks complete without a single sender.</strong> Every other field is set: friendly name, inbound request URL, validity period, use-case flags. Nothing in the Service resource itself says the pool is empty, because the pool is a subresource you have to ask for separately.</p>
<p><strong>The rejection happens before a Message exists.</strong> <code>21704</code> is returned to the API caller synchronously; no Message resource is created, so paging <code>Messages.json</code> will never find it. If your send path swallows exceptions, or logs them at a level nobody reads, the traffic simply stops and no Twilio-side artifact records that it ever tried.</p>
<p><strong>Sender types live in three different lists.</strong> Long codes and toll-free numbers are under <code>/PhoneNumbers</code>, alphanumeric sender IDs under <code>/AlphaSenders</code>, short codes under <code>/ShortCodes</code>. A check that reads one of the three reports false findings on the accounts most likely to be doing something deliberate.</p>
<p><strong>Not empty is not the same as usable.</strong> A pool holding only an alphanumeric sender ID cannot send to the United States or Canada and cannot receive a reply, so a US destination fails sender selection with <code>21703</code> rather than <code>21704</code>. Different code, different note, same afternoon lost if the audit lumps them together.</p>""",
"steps": [
 {"h": "List the services before you list the senders",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services?PageSize=100</code>, following <code>meta.next_page_url</code>. Accounts accumulate services faster than anyone expects &mdash; one per environment, one per experiment &mdash; and the empty one is rarely the one you would have thought to check.</p>"""},
 {"h": "Read all three sender subresources",
  "body": """<p><code>/PhoneNumbers</code>, <code>/AlphaSenders</code> and <code>/ShortCodes</code> under each service. Three GETs per service is cheap, and it is the difference between a report you act on and a report that cries wolf about the one service deliberately fronted by a short code.</p>"""},
 {"h": "Keep unread and empty as different states",
  "body": """<p>A request that failed, was skipped, or came back without the list key is <em>not</em> an empty pool. Treat a missing list as unknown and say so; an audit that reports "empty" because a page of results never arrived will have somebody adding senders to a service that already has them.</p>"""},
 {"h": "Separate 21704 from 21703",
  "body": """<p>Nothing at all in any list means every send is rejected outright. Senders that exist but cannot reach the destination &mdash; alphanumeric only, or no US long code for a US recipient &mdash; is sender selection failing, which is <code>21703</code> and a different repair. The classifier should name which one it found.</p>"""},
 {"h": "Add the senders, then keep the check on a schedule",
  "body": """<p><code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> with <code>PhoneNumberSid=PN…</code> for each owned number, or Console &rarr; Messaging &rarr; Services &rarr; Sender Pool &rarr; Add Senders. The default cap is 400 numbers per service. Re-run afterwards, and keep running it: the next environment somebody bootstraps will land the same way.</p>"""},
],
"verify": """<p>Re-run after adding senders. Every service should report <code>ready</code>, and the count of pool problems should be zero.</p>
<pre><code class="language-bash">python3 twilio_sender_pool_audit.py
# 6 service(s), 0 that cannot send</code></pre>""",
"code_intro": "One GET to list the services and three per service for the sender lists &mdash; an API Key with read access is the whole credential. The pure part is deliberately fussy about one distinction: a list that came back empty and a list that was never read are different facts, and collapsing them is how an audit sends somebody to fix a service that was fine.",
"py_file": "twilio_sender_pool_audit.py",
"py": '''"""Report Twilio Messaging Services whose sender pool cannot send.

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
log = logging.getLogger("twilio_sender_pool_audit")

MESSAGING = "https://messaging.twilio.com/v1"

# (subresource path, the key its list response uses)
SENDER_LISTS = (
    ("PhoneNumbers", "phone_numbers"),
    ("AlphaSenders", "alpha_senders"),
    ("ShortCodes", "short_codes"),
)


def sender_count(payload, key):
    """How many senders a list response holds, or None when it was not read.

    Pure. The None is the point: a request that failed or was skipped must not
    be reported as an empty pool, because the repair for the two is opposite.
    """
    if not isinstance(payload, dict):
        return None
    items = payload.get(key)
    if items is None:
        return None
    return len(items)


def verdict(pool):
    """Classify one service's sender pool. Pure, so the 21704 rule and the
    21703 rule are readable side by side.

    `pool` maps a sender kind to a count or to None for "not read".

    Returns (state, detail).
    """
    numbers = pool.get("phone_numbers")
    alpha = pool.get("alpha_senders")
    short = pool.get("short_codes")

    if numbers is None:
        return ("unread", "the phone number pool was not read, so nothing here is "
                          "a finding yet")
    if numbers == 0 and (alpha is None or short is None):
        return ("unread", "no phone numbers, but the alpha sender or short code "
                          "list was not read. Do not call a pool empty until all "
                          "three lists are in hand.")

    total = numbers + alpha + short
    if total == 0:
        return ("empty",
                "no phone numbers, no alpha senders, no short codes. Every send "
                "that passes this MessagingServiceSid is rejected with 21704 at "
                "request time, before any carrier hop and before a Message row "
                "exists to find later.")
    if numbers == 0 and short == 0:
        return ("alpha-only",
                "%d alphanumeric sender(s) and nothing else. Not 21704, but "
                "alphanumeric senders are one way and are not supported for US "
                "or Canadian destinations, so those sends fail selection with "
                "21703 instead." % alpha)
    if numbers == 0:
        return ("short-code-only",
                "%d short code(s) and no long codes. It sends, but there is no "
                "long code to fall back to and no coverage outside the short "
                "code's own country." % short)
    return ("ready", "%d number(s), %d alpha sender(s), %d short code(s)"
            % (numbers, alpha, short))


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
    """One GET per sender kind. Anything that does not come back stays None so
    the classifier can say 'unread' rather than 'empty'."""
    pool = {}
    for path, key in SENDER_LISTS:
        payload = get(session, "%s/Services/%s/%s" % (MESSAGING, service_sid, path),
                      PageSize=100)
        pool[key] = sender_count(payload, key)
    return pool


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-services", type=int, default=200,
                    help="stop paging after this many Messaging Services")
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

    services = list_services(session, args.max_services)
    if not services:
        log.info("no Messaging Services on this account")
        return 0

    bad = 0
    for svc in services:
        sid = svc.get("sid")
        state, detail = verdict(read_pool(session, sid))
        line = "%-16s %s (%s)  %s" % (state, sid, svc.get("friendly_name", "?"), detail)
        if state == "ready":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: add a sender with POST %s/Services/%s/PhoneNumbers "
                    "PhoneNumberSid=PN..., or Console > Messaging > Services > "
                    "Sender Pool > Add Senders. The default cap is 400 numbers "
                    "per service.", MESSAGING, sid)

    log.info("%d service(s), %d that cannot send", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sender-pool-audit.mjs",
"js": '''/**
 * Report Twilio Messaging Services whose sender pool cannot send.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MESSAGING = 'https://messaging.twilio.com/v1';

// [subresource path, the key its list response uses]
const SENDER_LISTS = [
  ['PhoneNumbers', 'phone_numbers'],
  ['AlphaSenders', 'alpha_senders'],
  ['ShortCodes', 'short_codes'],
];

/**
 * How many senders a list response holds, or null when it was not read. Pure.
 * The null is the point: a request that failed or was skipped must not be
 * reported as an empty pool, because the repair for the two is opposite.
 */
export function senderCount(payload, key) {
  if (payload === null || typeof payload !== 'object') return null;
  const items = payload[key];
  if (items === null || items === undefined) return null;
  return items.length;
}

/**
 * Classify one service's sender pool. Pure, so the 21704 rule and the 21703
 * rule are readable side by side. `pool` maps a sender kind to a count or to
 * null for "not read". Returns [state, detail].
 */
export function verdict(pool) {
  const numbers = pool.phone_numbers ?? null;
  const alpha = pool.alpha_senders ?? null;
  const short = pool.short_codes ?? null;

  if (numbers === null) {
    return ['unread', 'the phone number pool was not read, so nothing here is a finding yet'];
  }
  if (numbers === 0 && (alpha === null || short === null)) {
    return ['unread',
      'no phone numbers, but the alpha sender or short code list was not read. ' +
      'Do not call a pool empty until all three lists are in hand.'];
  }

  if (numbers + alpha + short === 0) {
    return ['empty',
      'no phone numbers, no alpha senders, no short codes. Every send that passes ' +
      'this MessagingServiceSid is rejected with 21704 at request time, before any ' +
      'carrier hop and before a Message row exists to find later.'];
  }
  if (numbers === 0 && short === 0) {
    return ['alpha-only',
      `${alpha} alphanumeric sender(s) and nothing else. Not 21704, but alphanumeric ` +
      'senders are one way and are not supported for US or Canadian destinations, ' +
      'so those sends fail selection with 21703 instead.'];
  }
  if (numbers === 0) {
    return ['short-code-only',
      `${short} short code(s) and no long codes. It sends, but there is no long code ` +
      "to fall back to and no coverage outside the short code's own country."];
  }
  return ['ready',
    `${numbers} number(s), ${alpha} alpha sender(s), ${short} short code(s)`];
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
  for (const [path, key] of SENDER_LISTS) {
    const payload = await get(auth, `${MESSAGING}/Services/${serviceSid}/${path}`,
                              { PageSize: 100 });
    pool[key] = senderCount(payload, key);
  }
  return pool;
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

  const services = await listServices(auth);
  if (services.length === 0) {
    console.log('no Messaging Services on this account');
    return;
  }

  let bad = 0;
  for (const svc of services) {
    const [state, detail] = verdict(await readPool(auth, svc.sid));
    const line = `${state.padEnd(16)} ${svc.sid} (${svc.friendly_name ?? '?'})  ${detail}`;
    if (state === 'ready') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: add a sender with POST ${MESSAGING}/Services/${svc.sid}` +
                 '/PhoneNumbers PhoneNumberSid=PN..., or Console > Messaging > ' +
                 'Services > Sender Pool > Add Senders. The default cap is 400 ' +
                 'numbers per service.');
  }

  console.log(`${services.length} service(s), ${bad} that cannot send`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the two ways this audit could lie. A list that was never read must not be reported as an empty pool, so an unread short code list on a service with no numbers is <code>unread</code> and not <code>empty</code>. And a pool with senders in it that still cannot reach the destination is a different error code, so alphanumeric-only gets its own state rather than being quietly counted as fine.",
"test_py_file": "test_twilio_sender_pool_audit.py",
"test_py": '''from twilio_sender_pool_audit import sender_count, verdict


def full(numbers=0, alpha=0, short=0):
    return {"phone_numbers": numbers, "alpha_senders": alpha, "short_codes": short}


def test_sender_count_separates_empty_from_unread():
    assert sender_count({"phone_numbers": []}, "phone_numbers") == 0
    assert sender_count({"phone_numbers": [{"sid": "PN1"}]}, "phone_numbers") == 1
    assert sender_count({}, "phone_numbers") is None
    assert sender_count(None, "phone_numbers") is None


def test_nothing_in_any_list_is_21704():
    state, detail = verdict(full())
    assert state == "empty"
    assert "21704" in detail


def test_an_unread_list_is_not_an_empty_pool():
    # The false positive worth preventing: somebody adds senders to a service
    # that already had them because one GET was skipped.
    state, detail = verdict({"phone_numbers": 0, "alpha_senders": 0,
                             "short_codes": None})
    assert state == "unread"
    assert "not read" in detail
    assert verdict({"phone_numbers": None})[0] == "unread"


def test_alpha_senders_only_is_21703_not_21704():
    state, detail = verdict(full(alpha=2))
    assert state == "alpha-only"
    assert "21703" in detail
    assert "21704" not in detail.replace("Not 21704", "")


def test_a_short_code_only_pool_still_sends():
    state, detail = verdict(full(short=1))
    assert state == "short-code-only"
    assert "1 short code(s)" in detail


def test_one_number_is_enough_to_be_ready():
    state, detail = verdict(full(numbers=1))
    assert state == "ready"
    assert "1 number(s)" in detail


def test_numbers_win_over_the_other_lists():
    assert verdict(full(numbers=3, alpha=1, short=1))[0] == "ready"
''',
"test_js_file": "twilio-sender-pool-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { senderCount, verdict } from './twilio-sender-pool-audit.mjs';

const full = (numbers = 0, alpha = 0, short = 0) => ({
  phone_numbers: numbers, alpha_senders: alpha, short_codes: short,
});

test('sender count separates empty from unread', () => {
  assert.equal(senderCount({ phone_numbers: [] }, 'phone_numbers'), 0);
  assert.equal(senderCount({ phone_numbers: [{ sid: 'PN1' }] }, 'phone_numbers'), 1);
  assert.equal(senderCount({}, 'phone_numbers'), null);
  assert.equal(senderCount(null, 'phone_numbers'), null);
});

test('nothing in any list is 21704', () => {
  const [state, detail] = verdict(full());
  assert.equal(state, 'empty');
  assert.match(detail, /21704/);
});

test('an unread list is not an empty pool', () => {
  const [state, detail] = verdict({
    phone_numbers: 0, alpha_senders: 0, short_codes: null,
  });
  assert.equal(state, 'unread');
  assert.match(detail, /not read/);
  assert.equal(verdict({ phone_numbers: null })[0], 'unread');
});

test('alpha senders only is 21703, not 21704', () => {
  const [state, detail] = verdict(full(0, 2, 0));
  assert.equal(state, 'alpha-only');
  assert.match(detail, /21703/);
});

test('a short code only pool still sends', () => {
  const [state, detail] = verdict(full(0, 0, 1));
  assert.equal(state, 'short-code-only');
  assert.match(detail, /1 short code\\(s\\)/);
});

test('one number is enough to be ready', () => {
  const [state, detail] = verdict(full(1));
  assert.equal(state, 'ready');
  assert.match(detail, /1 number\\(s\\)/);
});

test('numbers win over the other lists', () => {
  assert.equal(verdict(full(3, 1, 1))[0], 'ready');
});
''',
"faq": [
 ("What exactly does 21704 mean?",
  "That the Messaging Service you passed as MessagingServiceSid has no sender Twilio can select. It is returned synchronously to the API caller, so no Message resource is created and nothing about the attempt appears in the Messages list afterwards."),
 ("Why does the Console show the service as configured?",
  "Because everything on the Service resource itself is configured. The sender pool is a separate subresource, so a service can carry a friendly name, an inbound URL, a status callback and a validity period while holding no senders at all."),
 ("Do alphanumeric sender IDs count as senders?",
  "They stop you getting 21704, and they are not a substitute for a number. Alphanumeric senders are one-way and are not supported for US or Canadian destinations, so those sends fail sender selection with 21703 instead. The script reports that as its own state for exactly that reason."),
 ("Why read the short code list as well?",
  "To avoid a false positive. A service whose only sender is a short code has an empty phone_numbers[] and an empty alpha_senders[] and sends perfectly well. Flagging it once is enough to teach a team to ignore the whole report."),
 ("How many numbers can a sender pool hold?",
  "400 by default. That is a cap on the pool, not a target: adding numbers to dodge throughput limits is what carriers read as snowshoeing, and toll-free numbers in particular belong one per service."),
],
"related": [
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
 ("/twilio/messaging-service-no-status-callback/", "A service that never reports a delivery failure"),
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS disappears into a blank sms_url"),
],
"citations": [CITE_21704, CITE_SERVICE_PN, CITE_ALPHA, CITE_SERVICES_GUIDE],
},


{
"slug": "from-number-not-sms-capable",
"title": "A voice-only From number fails every SMS with error 21606",
"description": "21606 says the From is not a message-capable Twilio number for this account. Usually it is voice-only, on another subaccount, or not in E.164 format.",
"h1": "a voice-only From number fails every SMS with error 21606",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 21606", "from number not sms capable",
             "twilio 21606 fix", "twilio number capabilities sms",
             "not a valid message-capable twilio number"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The number works. People call it, the IVR answers, it has been on the account for two years. Then a new notification job starts sending from it and every single message is rejected with <code>21606</code>: <em>'From' number is not a valid message-capable Twilio number for this account</em>. Both halves of that sentence are load-bearing, and only one of them is about SMS.",
"short_answer": """<p>Look the sender up directly: <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PhoneNumber={E164}</code>. Read <code>capabilities.sms</code>, <code>capabilities.mms</code>, <code>capabilities.voice</code> and <code>account_sid</code> on whatever comes back.</p>
<p>Three separate findings share the one error code. <code>capabilities.sms == false</code> is a voice-only number. An empty result set means the number is not on this account at all. An <code>account_sid</code> that differs from the SID you authenticate with means it belongs to another subaccount. A <code>From</code> that is not in E.164 fails before any of that is even checked.</p>""",
"problem": """<p><code>21606</code> reads like a capability error and is thrown for at least four unrelated causes, which is why it survives a whole debugging session. The number in front of you demonstrably works &mdash; you can dial it &mdash; so the error looks wrong, and the natural next step is to retry, or to blame the client library, rather than to ask which of the four things happened.</p>
<p>Toll-free numbers bought for an IVR are the classic case: voice-capable, not message-capable, and indistinguishable from a working SMS sender in every internal document. The subaccount case is worse, because the number is genuinely message-capable and genuinely yours; it just is not owned by the account whose credentials the job is holding, and no amount of reading the number's capabilities will explain that.</p>""",
"why": """<p><strong>Capabilities are per number and are not uniform.</strong> Voice, SMS, MMS and fax are independent flags. Many non-US numbers cannot do SMS at all, plenty of toll-free numbers are sold voice-only, and nothing about the number's appearance tells you which. The flags are on the resource; they are just never read until something breaks.</p>
<p><strong>The error says "for this account", and means it.</strong> A number on a sibling subaccount is not usable as a <code>From</code> by the parent's credentials or by another subaccount's. This is the cause that wastes the most time, because every capability on the number is correct and the fix has nothing to do with capabilities.</p>
<p><strong>Format is checked before ownership.</strong> A <code>From</code> passed as <code>(555) 010-1234</code> or <code>07700900123</code> is rejected with the same code as a number you do not own. Sending <code>From</code> in E.164 is the cheapest of the four fixes and the easiest to overlook, because the value came out of a database column that looks fine to a human.</p>
<p><strong>Porting and hosting have a gap.</strong> A number mid-port, or an SMS-hosted number still being provisioned, exists in your plans and not yet in <code>IncomingPhoneNumbers</code>. The lookup returns nothing, the send fails, and the answer is to wait rather than to change anything.</p>""",
"steps": [
 {"h": "Normalise the sender before you ask Twilio about it",
  "body": """<p>E.164 means a leading <code>+</code>, a country code, no spaces, no punctuation. Check it in your own code first: a malformed <code>From</code> produces the same <code>21606</code> as a number you do not own, and telling those apart after the fact costs far more than a regex.</p>"""},
 {"h": "Look the number up by value, not by paging the list",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PhoneNumber={E164}</code>. The filter takes the exact number, so this is one request per sender rather than a walk of the whole inventory, and it works the same on an account with four numbers and one with four hundred.</p>"""},
 {"h": "Treat an empty result as its own finding",
  "body": """<p>No match means the number is not on this account: a typo, a number on a different subaccount, a port or host still provisioning, or a production number being used with test credentials. None of those are capability problems, and reporting them as one sends people to look at the wrong field.</p>"""},
 {"h": "Compare account_sid with the account you authenticated as",
  "body": """<p>Where a record does come back, <code>account_sid</code> must equal the <code>AccountSid</code> in the request path. Subaccount sprawl makes this common and it is invisible in the console, where you are usually already looking at the subaccount that owns the number.</p>"""},
 {"h": "Read capabilities.mms too if you send media",
  "body": """<p><code>capabilities.sms</code> true and <code>capabilities.mms</code> false is a number that sends text and rejects anything with a <code>MediaUrl</code>. It is worth flagging separately rather than discovering it on the first campaign that includes an image. The repair is a replacement number: <code>GET …/AvailablePhoneNumbers/US/Local.json?SmsEnabled=true</code>, then buy it.</p>"""},
],
"verify": """<p>Re-run with the senders your application actually uses. Every one should report <code>ok</code>.</p>
<pre><code class="language-bash">python3 twilio_from_number_capability_audit.py +15550001111 +15550002222
# 2 sender(s), 0 that cannot send SMS</code></pre>""",
"code_intro": "One GET per sender, filtered by the exact number &mdash; an API Key with read access covers it. The classifier takes the E.164 check, the ownership check and the capability check in that order, because that is the order Twilio applies them and because a report that says &ldquo;voice only&rdquo; about a number on another subaccount is worse than no report at all.",
"py_file": "twilio_from_number_capability_audit.py",
"py": '''"""Explain 21606 for a set of Twilio From numbers before they are used.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_from_number_capability_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

E164 = re.compile(r"^\\+[1-9]\\d{6,14}$")


def is_e164(value):
    """A leading plus, a country code, digits only. Pure.

    Twilio rejects a national-format From with the same 21606 it uses for a
    number you do not own, so this has to be a separate answer rather than a
    guess made after the lookup comes back empty.
    """
    return bool(E164.match(str(value or "").strip()))


def verdict(sender, matches, account, need_mms=False):
    """Say why one From number would be rejected with 21606, or that it is fine.

    Pure, so the four unrelated causes behind one error code are testable
    without a network. `matches` is whatever IncomingPhoneNumbers returned when
    filtered by this exact number; `account` is the AccountSid the credentials
    authenticate as.

    Returns (state, detail).
    """
    if not is_e164(sender):
        return ("not-e164",
                "%r is not E.164. Send From as +<country><number> with no spaces "
                "or punctuation; this is rejected with 21606 before ownership or "
                "capabilities are looked at." % sender)

    matches = list(matches or [])
    if not matches:
        return ("not-on-account",
                "no IncomingPhoneNumber on account %s matches. A typo, a number "
                "owned by another subaccount, a port or SMS-hosted number still "
                "provisioning, or production digits used with test credentials."
                % account)

    number = matches[0]
    owner = str(number.get("account_sid") or "").strip()
    if owner and account and owner != account:
        return ("wrong-account",
                "owned by %s, but these credentials authenticate as %s. The "
                "number is message capable and still cannot be used as a From "
                "here: 21606 says 'for this account' and means it."
                % (owner, account))

    caps = number.get("capabilities")
    if not isinstance(caps, dict):
        return ("unresolved",
                "the record carried no capabilities object, so nothing can be "
                "said about SMS without re-reading it")

    if not caps.get("sms"):
        return ("voice-only",
                "capabilities.sms is false%s. Every SMS from this number is "
                "rejected with 21606; no setting turns messaging on, the repair "
                "is an SMS capable replacement number."
                % (" (voice is true)" if caps.get("voice") else ""))

    if need_mms and not caps.get("mms"):
        return ("no-mms",
                "SMS works and capabilities.mms is false, so any send carrying a "
                "MediaUrl fails. Add an MMS capable US or Canadian long code.")

    return ("ok", "sms%s, owned by this account"
            % (" and mms" if caps.get("mms") else " only"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def lookup(session, account, sender):
    """One request per sender, filtered by the exact number, so this costs the
    same on an account with four numbers and one with four hundred."""
    page = get(session, "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account),
               PhoneNumber=sender, PageSize=20)
    return page.get("incoming_phone_numbers", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("senders", nargs="+", help="the From numbers your app sends with")
    ap.add_argument("--mms", action="store_true",
                    help="also require MMS, for senders that carry MediaUrl")
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

    bad = 0
    for sender in args.senders:
        matches = lookup(session, account, sender) if is_e164(sender) else []
        state, detail = verdict(sender, matches, account, args.mms)
        line = "%-16s %s  %s" % (state, sender, detail)
        if state == "ok":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: find an SMS capable replacement with GET %s/Accounts/"
                    "%s/AvailablePhoneNumbers/US/Local.json?SmsEnabled=true and buy "
                    "it, or send From the subaccount that owns the number. Always "
                    "pass From in E.164.", BASE, account)

    log.info("%d sender(s), %d that cannot send SMS", len(args.senders), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-from-number-capability-audit.mjs",
"js": '''/**
 * Explain 21606 for a set of Twilio From numbers before they are used.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const E164 = /^\\+[1-9]\\d{6,14}$/;

/**
 * A leading plus, a country code, digits only. Pure. Twilio rejects a
 * national-format From with the same 21606 it uses for a number you do not own,
 * so this has to be a separate answer rather than a guess made afterwards.
 */
export function isE164(value) {
  return E164.test(String(value ?? '').trim());
}

/**
 * Say why one From number would be rejected with 21606, or that it is fine.
 * Pure, so the four unrelated causes behind one error code are testable without
 * a network. `matches` is whatever IncomingPhoneNumbers returned when filtered
 * by this exact number; `account` is the AccountSid the credentials
 * authenticate as. Returns [state, detail].
 */
export function verdict(sender, matches, account, needMms = false) {
  if (!isE164(sender)) {
    return ['not-e164',
      `${JSON.stringify(sender)} is not E.164. Send From as +<country><number> with ` +
      'no spaces or punctuation; this is rejected with 21606 before ownership or ' +
      'capabilities are looked at.'];
  }

  const found = [...(matches ?? [])];
  if (found.length === 0) {
    return ['not-on-account',
      `no IncomingPhoneNumber on account ${account} matches. A typo, a number owned ` +
      'by another subaccount, a port or SMS-hosted number still provisioning, or ' +
      'production digits used with test credentials.'];
  }

  const number = found[0];
  const owner = String(number.account_sid ?? '').trim();
  if (owner && account && owner !== account) {
    return ['wrong-account',
      `owned by ${owner}, but these credentials authenticate as ${account}. The ` +
      'number is message capable and still cannot be used as a From here: 21606 ' +
      "says 'for this account' and means it."];
  }

  const caps = number.capabilities;
  if (caps === null || typeof caps !== 'object') {
    return ['unresolved',
      'the record carried no capabilities object, so nothing can be said about SMS ' +
      'without re-reading it'];
  }

  if (!caps.sms) {
    return ['voice-only',
      `capabilities.sms is false${caps.voice ? ' (voice is true)' : ''}. Every SMS ` +
      'from this number is rejected with 21606; no setting turns messaging on, the ' +
      'repair is an SMS capable replacement number.'];
  }

  if (needMms && !caps.mms) {
    return ['no-mms',
      'SMS works and capabilities.mms is false, so any send carrying a MediaUrl ' +
      'fails. Add an MMS capable US or Canadian long code.'];
  }

  return ['ok', `sms${caps.mms ? ' and mms' : ' only'}, owned by this account`];
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

export async function lookup(auth, account, sender) {
  const page = await get(auth, `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`,
                         { PhoneNumber: sender, PageSize: 20 });
  return page.incoming_phone_numbers ?? [];
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

  const needMms = process.argv.includes('--mms');
  const senders = process.argv.slice(2).filter((a) => !a.startsWith('--'));
  if (senders.length === 0) {
    console.error('usage: node twilio-from-number-capability-audit.mjs +1555... [--mms]');
    process.exitCode = 2;
    return;
  }

  let bad = 0;
  for (const sender of senders) {
    const matches = isE164(sender) ? await lookup(auth, account, sender) : [];
    const [state, detail] = verdict(sender, matches, account, needMms);
    const line = `${state.padEnd(16)} ${sender}  ${detail}`;
    if (state === 'ok') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: find an SMS capable replacement with GET ${BASE}/Accounts/` +
                 `${account}/AvailablePhoneNumbers/US/Local.json?SmsEnabled=true and ` +
                 'buy it, or send From the subaccount that owns the number. Always ' +
                 'pass From in E.164.');
  }

  console.log(`${senders.length} sender(s), ${bad} that cannot send SMS`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "One error code, four causes, and the tests exist to keep them apart. A number on a sibling subaccount must not be reported as voice-only, because its capabilities are perfect and the repair is somewhere else entirely. A national-format <code>From</code> must be caught before the lookup, since an empty result would otherwise be blamed on ownership. And MMS is only a finding when the caller says they send media.",
"test_py_file": "test_twilio_from_number_capability_audit.py",
"test_py": '''from twilio_from_number_capability_audit import is_e164, verdict

ACCOUNT = "AC11111111111111111111111111111111"
SUB = "AC22222222222222222222222222222222"


def number(sms=True, mms=True, voice=True, account=ACCOUNT):
    return {"phone_number": "+15550001111", "account_sid": account,
            "capabilities": {"sms": sms, "mms": mms, "voice": voice}}


def test_e164_is_checked_the_way_twilio_checks_it():
    assert is_e164("+15550001111")
    assert not is_e164("(555) 010-1234")
    assert not is_e164("15550001111")
    assert not is_e164("+0123456789")
    assert not is_e164(None)


def test_national_format_is_named_rather_than_blamed_on_ownership():
    state, detail = verdict("(555) 010-1234", [], ACCOUNT)
    assert state == "not-e164"
    assert "21606" in detail


def test_a_voice_only_number_is_the_capability_case():
    state, detail = verdict("+15550001111", [number(sms=False, mms=False)], ACCOUNT)
    assert state == "voice-only"
    assert "capabilities.sms is false" in detail
    assert "voice is true" in detail


def test_a_number_on_another_subaccount_is_not_a_capability_problem():
    # Perfect capabilities, still 21606. Reporting this as voice-only sends
    # somebody to buy a number they already own.
    state, detail = verdict("+15550001111", [number(account=SUB)], ACCOUNT)
    assert state == "wrong-account"
    assert SUB in detail and ACCOUNT in detail


def test_no_match_at_all_is_its_own_finding():
    state, detail = verdict("+15550001111", [], ACCOUNT)
    assert state == "not-on-account"
    assert "provisioning" in detail


def test_mms_is_only_a_finding_when_media_is_sent():
    assert verdict("+15550001111", [number(mms=False)], ACCOUNT)[0] == "ok"
    state, _ = verdict("+15550001111", [number(mms=False)], ACCOUNT, need_mms=True)
    assert state == "no-mms"


def test_a_record_without_capabilities_is_not_guessed_at():
    state, _ = verdict("+15550001111", [{"account_sid": ACCOUNT}], ACCOUNT)
    assert state == "unresolved"


def test_a_healthy_sender_says_what_it_can_do():
    state, detail = verdict("+15550001111", [number()], ACCOUNT)
    assert state == "ok"
    assert "sms and mms" in detail
''',
"test_js_file": "twilio-from-number-capability-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isE164, verdict } from './twilio-from-number-capability-audit.mjs';

const ACCOUNT = 'AC11111111111111111111111111111111';
const SUB = 'AC22222222222222222222222222222222';

const number = ({ sms = true, mms = true, voice = true, account = ACCOUNT } = {}) => ({
  phone_number: '+15550001111', account_sid: account,
  capabilities: { sms, mms, voice },
});

test('e164 is checked the way Twilio checks it', () => {
  assert.ok(isE164('+15550001111'));
  assert.ok(!isE164('(555) 010-1234'));
  assert.ok(!isE164('15550001111'));
  assert.ok(!isE164('+0123456789'));
  assert.ok(!isE164(null));
});

test('national format is named rather than blamed on ownership', () => {
  const [state, detail] = verdict('(555) 010-1234', [], ACCOUNT);
  assert.equal(state, 'not-e164');
  assert.match(detail, /21606/);
});

test('a voice only number is the capability case', () => {
  const [state, detail] = verdict('+15550001111', [number({ sms: false, mms: false })], ACCOUNT);
  assert.equal(state, 'voice-only');
  assert.match(detail, /capabilities\\.sms is false/);
  assert.match(detail, /voice is true/);
});

test('a number on another subaccount is not a capability problem', () => {
  const [state, detail] = verdict('+15550001111', [number({ account: SUB })], ACCOUNT);
  assert.equal(state, 'wrong-account');
  assert.match(detail, new RegExp(SUB));
  assert.match(detail, new RegExp(ACCOUNT));
});

test('no match at all is its own finding', () => {
  const [state, detail] = verdict('+15550001111', [], ACCOUNT);
  assert.equal(state, 'not-on-account');
  assert.match(detail, /provisioning/);
});

test('mms is only a finding when media is sent', () => {
  assert.equal(verdict('+15550001111', [number({ mms: false })], ACCOUNT)[0], 'ok');
  assert.equal(
    verdict('+15550001111', [number({ mms: false })], ACCOUNT, true)[0], 'no-mms');
});

test('a record without capabilities is not guessed at', () => {
  assert.equal(
    verdict('+15550001111', [{ account_sid: ACCOUNT }], ACCOUNT)[0], 'unresolved');
});

test('a healthy sender says what it can do', () => {
  const [state, detail] = verdict('+15550001111', [number()], ACCOUNT);
  assert.equal(state, 'ok');
  assert.match(detail, /sms and mms/);
});
''',
"faq": [
 ("The number works for voice. Why is SMS rejected?",
  "Because capabilities are per channel. capabilities.voice true with capabilities.sms false is an ordinary, supported configuration, common on toll-free numbers bought for an IVR and on many non-US numbers. There is no setting that adds messaging to a number that was not sold with it."),
 ("Can I enable SMS on a number that does not have it?",
  "No. The capability is a property of the number as provisioned by the carrier, not an account setting. The repair is to buy a replacement filtered on SmsEnabled=true, or to use a number that already has the capability."),
 ("Why does a number I definitely own still return 21606?",
  "Most often it is owned by a different subaccount than the credentials sending the message. Compare account_sid on the number with the AccountSid you authenticate as. Same organisation, same console, different account as far as the API is concerned."),
 ("Does the From format really matter?",
  "Yes, and it is checked before ownership. A national-format From is rejected with the same 21606 as a number you do not own, which is why the script checks the format itself before it asks Twilio anything."),
 ("What if the number is mid-port or SMS-hosted?",
  "Then it will not appear in IncomingPhoneNumbers yet and the lookup returns nothing. That reads as not-on-account, and the repair is to wait for provisioning rather than to change any configuration."),
],
"related": [
 ("/twilio/messaging-service-empty-sender-pool/", "A Messaging Service with no senders at all"),
 ("/twilio/landline-destination-30006/", "SMS to landlines that can never receive it"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_21606, CITE_PN, CITE_MSG, CITE_KEYS],
},


{
"slug": "messaging-service-no-status-callback",
"title": "No status callback means delivery failures never reach you",
"description": "Messages.create returns queued and your database records a success. Terminal status and error_code arrive only by status callback or Event Streams.",
"h1": "no status callback means delivery failures never reach you",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio status callback missing", "twilio delivery status webhook",
             "twilio message status not updating", "twilio event streams sink",
             "twilio messaging service status_callback"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Your dashboard says every message sent. Support says customers never got them. Both are true: <code>Messages.create</code> returned <code>queued</code>, your code wrote <em>sent</em>, and the <code>undelivered</code> that arrived ninety seconds later went to a status callback that was never configured. The <code>21610</code>s, the <code>30007</code>s and the <code>30034</code>s exist, in Twilio's logs, where nothing you own is looking.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Services</code> and flag any service where <code>status_callback</code> is null &mdash; and note <code>fallback_url</code> while you are there. Then read <code>GET https://events.twilio.com/v1/Sinks</code> and flag an empty list or any sink whose <code>status</code> is not <code>active</code>.</p>
<p>A sink on its own proves nothing: pair it with <code>GET https://events.twilio.com/v1/Subscriptions</code>, and the subscription's <code>SubscribedEvents</code>, to confirm something is actually subscribed to <code>com.twilio.messaging.message.*</code>. No status callback and no active messaging subscription means zero delivery observability, whatever the dashboard says.</p>""",
"problem": """<p>The synchronous response to a send is an acceptance, not a delivery. <code>queued</code> and <code>accepted</code> mean Twilio has the message; everything that determines whether a human saw it happens afterwards, asynchronously, and is reported only to a callback URL or an Event Streams sink. An application that records the create response as its final state has built a database of intentions and labelled it delivery.</p>
<p>The consequence is not just a wrong dashboard. Opt-outs (<code>21610</code>) never reach your suppression list, so you keep messaging people who asked you to stop. Filtered traffic (<code>30007</code>) never triggers a content review. Unregistered-sender rejections (<code>30034</code>) look identical to success. The list rots quietly, month after month, and the first honest signal is a support ticket or a compliance complaint.</p>""",
"why": """<p><strong>There is no polling substitute worth running.</strong> The Messages list has no <code>Status</code> filter and no <code>ErrorCode</code> filter, so reconstructing delivery after the fact means paging every message in the window and filtering client-side. That is a fine audit and a terrible pipeline; the callback exists precisely so you do not have to do it continuously.</p>
<p><strong>Nothing is configured by default.</strong> A Messaging Service is created with <code>status_callback</code> null. A per-message <code>StatusCallback</code> parameter overrides it, which is why a service can look uninstrumented while one code path is fine &mdash; and why the other nine are not.</p>
<p><strong>An Event Streams sink is only half the wiring.</strong> A sink can exist, be pointed at a webhook or a Kinesis stream, and be subscribed to nothing but voice events. Or it can be subscribed correctly and sit in a status that is not <code>active</code>, which is a silent outage with a green-looking configuration. Both need the subscription and the sink read together.</p>
<p><strong>The failure is invisible from the send side forever.</strong> Every other problem in this section eventually shows up as an error somewhere. This one removes the reporting channel itself, so the longer it runs the more confident everyone becomes in numbers that have never once been checked against reality.</p>""",
"steps": [
 {"h": "List the services and read status_callback",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services?PageSize=100</code>. Null <code>status_callback</code> is the finding. Note <code>fallback_url</code> at the same time: a service with neither has no second chance when the primary webhook is down.</p>"""},
 {"h": "Read the sinks and their status",
  "body": """<p><code>GET https://events.twilio.com/v1/Sinks</code>. An empty list means Event Streams is not an answer here. A sink whose <code>status</code> is not <code>active</code> is worse than none, because somebody believes it is working; read the status rather than the existence.</p>"""},
 {"h": "Confirm something is subscribed to message events",
  "body": """<p><code>GET https://events.twilio.com/v1/Subscriptions</code>, then the <code>SubscribedEvents</code> under each, and keep only subscriptions carrying a <code>com.twilio.messaging.message.*</code> type. A subscription full of voice or Verify events is not delivery observability, and it is the easiest thing in the world to mistake for it.</p>"""},
 {"h": "Join the subscription to its sink before deciding",
  "body": """<p>The pairing is what matters: a messaging subscription whose <code>sink_sid</code> resolves to an <code>active</code> sink. Either half alone is a service that is still blind. Judge the pair, and name which half is missing so the repair is obvious.</p>"""},
 {"h": "Set the callback, then handle what it sends you",
  "body": """<p><code>POST https://messaging.twilio.com/v1/Services/{ServiceSid}</code> with <code>StatusCallback</code> and <code>FallbackUrl</code>. Then do the part that actually pays: validate <code>X-Twilio-Signature</code> on receipt, persist <code>MessageStatus</code> and <code>ErrorCode</code> against your own record, and suppress the recipient on <code>21610</code>. A callback whose handler drops the payload is the same outage with more traffic.</p>"""},
],
"verify": """<p>Re-run after configuring the callback. Every service should report <code>callback</code> or <code>streamed</code>.</p>
<pre><code class="language-bash">python3 twilio_delivery_observability_audit.py
# 6 service(s), 0 with no delivery signal</code></pre>""",
"code_intro": "Three read-only surfaces &mdash; Messaging Services, Event Streams sinks, and subscriptions with their subscribed event types &mdash; and an API Key with read access for all of them. The pure part joins a subscription to its sink and then judges one service, because the mistake this note exists to prevent is calling an account instrumented on the strength of a sink that is subscribed to something else.",
"py_file": "twilio_delivery_observability_audit.py",
"py": '''"""Report Twilio Messaging Services with no delivery signal at all.

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
log = logging.getLogger("twilio_delivery_observability_audit")

MESSAGING = "https://messaging.twilio.com/v1"
EVENTS = "https://events.twilio.com/v1"

MESSAGE_EVENT = "com.twilio.messaging.message."


def message_streams(sinks, subscriptions):
    """Pair every subscription carrying a message event with the sink it feeds.

    Pure. `subscriptions` entries are the Subscription resource plus a "types"
    list, which is the SubscribedEvents subresource fetched alongside it. A sink
    that exists proves nothing on its own: it can be subscribed to voice events,
    or be subscribed correctly and sit in a status that is not active.

    Returns {"live": [sink sid, ...], "broken": [(sink sid, status), ...]}.
    """
    by_sid = {}
    for sink in sinks or []:
        by_sid[str(sink.get("sid") or "")] = sink

    live, broken = [], []
    for sub in subscriptions or []:
        types = [str(t.get("type") or "") for t in (sub.get("types") or [])]
        if not any(t.startswith(MESSAGE_EVENT) for t in types):
            continue
        sink_sid = str(sub.get("sink_sid") or "")
        sink = by_sid.get(sink_sid)
        status = str((sink or {}).get("status") or "missing").lower()
        if status == "active":
            live.append(sink_sid)
        else:
            broken.append((sink_sid or "?", status))
    return {"live": live, "broken": broken}


def verdict(service, streams=None):
    """Classify one Messaging Service's delivery observability. Pure.

    Returns (state, detail).
    """
    streams = streams or {"live": [], "broken": []}
    callback = str(service.get("status_callback") or "").strip()
    fallback = str(service.get("fallback_url") or "").strip()
    no_fallback = "" if fallback else " No fallback_url either."

    if callback:
        return ("callback", "status_callback posts terminal status and error_code "
                            "to %s.%s" % (callback, no_fallback))
    if streams["live"]:
        return ("streamed",
                "no status_callback, but Event Streams carries message events to "
                "active sink(s) %s.%s" % (", ".join(streams["live"]), no_fallback))
    if streams["broken"]:
        return ("sink-failed",
                "no status_callback, and the only message subscription feeds a "
                "sink that is not active: %s. Believed working, delivering "
                "nothing.%s"
                % (", ".join("%s (%s)" % pair for pair in streams["broken"]),
                   no_fallback))
    return ("blind",
            "no status_callback and no active subscription to "
            "com.twilio.messaging.message.*. Every delivery failure, opt-out and "
            "filtering code exists only in Twilio's logs.%s" % no_fallback)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, url, key, limit):
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def load_subscriptions(session, limit):
    """Each subscription plus the event types it is actually subscribed to. The
    types live in a subresource, so the sink alone never answers the question."""
    subs = paged(session, "%s/Subscriptions" % EVENTS, "subscriptions", limit)
    for sub in subs:
        sub["types"] = paged(session, "%s/Subscriptions/%s/SubscribedEvents"
                             % (EVENTS, sub.get("sid")), "types", 200)
    return subs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-services", type=int, default=200,
                    help="stop paging after this many Messaging Services")
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

    services = paged(session, "%s/Services" % MESSAGING, "services", args.max_services)
    if not services:
        log.info("no Messaging Services on this account")
        return 0

    sinks = paged(session, "%s/Sinks" % EVENTS, "sinks", 200)
    streams = message_streams(sinks, load_subscriptions(session, 200))

    bad = 0
    for svc in services:
        state, detail = verdict(svc, streams)
        line = "%-12s %s (%s)  %s" % (state, svc.get("sid"),
                                      svc.get("friendly_name", "?"), detail)
        if state in ("callback", "streamed"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: POST %s/Services/%s StatusCallback=https://.../twilio/"
                    "status FallbackUrl=https://.../twilio/fallback, then validate "
                    "X-Twilio-Signature, persist MessageStatus and ErrorCode, and "
                    "suppress the recipient on 21610.", MESSAGING, svc.get("sid"))

    log.info("%d service(s), %d with no delivery signal", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-delivery-observability-audit.mjs",
"js": '''/**
 * Report Twilio Messaging Services with no delivery signal at all.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MESSAGING = 'https://messaging.twilio.com/v1';
const EVENTS = 'https://events.twilio.com/v1';

const MESSAGE_EVENT = 'com.twilio.messaging.message.';

/**
 * Pair every subscription carrying a message event with the sink it feeds.
 * Pure. `subscriptions` entries are the Subscription resource plus a `types`
 * list, which is the SubscribedEvents subresource fetched alongside it. A sink
 * that exists proves nothing on its own: it can be subscribed to voice events,
 * or be subscribed correctly and sit in a status that is not active.
 * Returns { live: [sinkSid], broken: [[sinkSid, status]] }.
 */
export function messageStreams(sinks, subscriptions) {
  const bySid = new Map();
  for (const sink of sinks ?? []) bySid.set(String(sink.sid ?? ''), sink);

  const live = [];
  const broken = [];
  for (const sub of subscriptions ?? []) {
    const types = (sub.types ?? []).map((t) => String(t.type ?? ''));
    if (!types.some((t) => t.startsWith(MESSAGE_EVENT))) continue;
    const sinkSid = String(sub.sink_sid ?? '');
    const sink = bySid.get(sinkSid);
    const status = String(sink?.status ?? 'missing').toLowerCase();
    if (status === 'active') live.push(sinkSid);
    else broken.push([sinkSid || '?', status]);
  }
  return { live, broken };
}

/**
 * Classify one Messaging Service's delivery observability. Pure.
 * Returns [state, detail].
 */
export function verdict(service, streams = { live: [], broken: [] }) {
  const callback = String(service.status_callback ?? '').trim();
  const fallback = String(service.fallback_url ?? '').trim();
  const noFallback = fallback ? '' : ' No fallback_url either.';

  if (callback) {
    return ['callback',
      `status_callback posts terminal status and error_code to ${callback}.${noFallback}`];
  }
  if (streams.live.length) {
    return ['streamed',
      'no status_callback, but Event Streams carries message events to active ' +
      `sink(s) ${streams.live.join(', ')}.${noFallback}`];
  }
  if (streams.broken.length) {
    const named = streams.broken.map(([sid, status]) => `${sid} (${status})`).join(', ');
    return ['sink-failed',
      'no status_callback, and the only message subscription feeds a sink that is ' +
      `not active: ${named}. Believed working, delivering nothing.${noFallback}`];
  }
  return ['blind',
    'no status_callback and no active subscription to com.twilio.messaging.message.*. ' +
    `Every delivery failure, opt-out and filtering code exists only in Twilio's logs.${noFallback}`];
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

export async function paged(auth, url, key, limit = 200) {
  let next = url;
  let params = { PageSize: 100 };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

async function loadSubscriptions(auth, limit = 200) {
  const subs = await paged(auth, `${EVENTS}/Subscriptions`, 'subscriptions', limit);
  for (const sub of subs) {
    sub.types = await paged(auth, `${EVENTS}/Subscriptions/${sub.sid}/SubscribedEvents`,
                            'types', 200);
  }
  return subs;
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

  const services = await paged(auth, `${MESSAGING}/Services`, 'services');
  if (services.length === 0) {
    console.log('no Messaging Services on this account');
    return;
  }

  const sinks = await paged(auth, `${EVENTS}/Sinks`, 'sinks');
  const streams = messageStreams(sinks, await loadSubscriptions(auth));

  let bad = 0;
  for (const svc of services) {
    const [state, detail] = verdict(svc, streams);
    const line = `${state.padEnd(12)} ${svc.sid} (${svc.friendly_name ?? '?'})  ${detail}`;
    if (state === 'callback' || state === 'streamed') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: POST ${MESSAGING}/Services/${svc.sid} StatusCallback=` +
                 'https://.../twilio/status FallbackUrl=https://.../twilio/fallback, ' +
                 'then validate X-Twilio-Signature, persist MessageStatus and ' +
                 'ErrorCode, and suppress the recipient on 21610.');
  }

  console.log(`${services.length} service(s), ${bad} with no delivery signal`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test here is about not being fooled by a configuration that looks instrumented. A sink subscribed to voice events does not count. A correctly subscribed sink whose status is not <code>active</code> counts for less than nothing, because somebody believes in it. And a per-service <code>status_callback</code> settles the question on its own, whatever Event Streams is doing.",
"test_py_file": "test_twilio_delivery_observability_audit.py",
"test_py": '''from twilio_delivery_observability_audit import message_streams, verdict

SINK = "DG11111111111111111111111111111111"


def sink(status="active", sid=SINK):
    return {"sid": sid, "status": status, "sink_type": "webhook"}


def sub(types, sink_sid=SINK):
    return {"sid": "DF1", "sink_sid": sink_sid,
            "types": [{"type": t} for t in types]}


def test_a_messaging_subscription_on_an_active_sink_is_live():
    streams = message_streams(
        [sink()], [sub(["com.twilio.messaging.message.delivered",
                        "com.twilio.messaging.message.failed"])])
    assert streams == {"live": [SINK], "broken": []}


def test_voice_events_are_not_delivery_observability():
    streams = message_streams([sink()], [sub(["com.twilio.voice.insights.call-summary"])])
    assert streams == {"live": [], "broken": []}


def test_a_sink_that_is_not_active_is_broken_not_live():
    streams = message_streams(
        [sink(status="failed")], [sub(["com.twilio.messaging.message.delivered"])])
    assert streams["live"] == []
    assert streams["broken"] == [(SINK, "failed")]


def test_a_subscription_pointing_at_no_sink_at_all_is_broken():
    streams = message_streams([], [sub(["com.twilio.messaging.message.sent"])])
    assert streams["broken"] == [(SINK, "missing")]


def test_a_service_with_no_callback_and_no_stream_is_blind():
    state, detail = verdict({"sid": "MG1", "status_callback": None,
                             "fallback_url": None})
    assert state == "blind"
    assert "com.twilio.messaging.message." in detail
    assert "No fallback_url either." in detail


def test_the_status_callback_settles_it():
    state, detail = verdict({"status_callback": "https://app.example.com/twilio/status",
                             "fallback_url": "https://app.example.com/twilio/fallback"})
    assert state == "callback"
    assert "No fallback_url" not in detail


def test_event_streams_counts_when_the_sink_is_active():
    state, _ = verdict({"status_callback": ""}, {"live": [SINK], "broken": []})
    assert state == "streamed"


def test_a_failed_sink_is_worse_than_nothing_and_says_so():
    state, detail = verdict({"status_callback": ""},
                            {"live": [], "broken": [(SINK, "failed")]})
    assert state == "sink-failed"
    assert "Believed working" in detail
''',
"test_js_file": "twilio-delivery-observability-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { messageStreams, verdict } from './twilio-delivery-observability-audit.mjs';

const SINK = 'DG11111111111111111111111111111111';

const sink = (status = 'active', sid = SINK) => ({ sid, status, sink_type: 'webhook' });
const sub = (types, sinkSid = SINK) => ({
  sid: 'DF1', sink_sid: sinkSid, types: types.map((t) => ({ type: t })),
});

test('a messaging subscription on an active sink is live', () => {
  const streams = messageStreams([sink()], [sub([
    'com.twilio.messaging.message.delivered',
    'com.twilio.messaging.message.failed',
  ])]);
  assert.deepEqual(streams, { live: [SINK], broken: [] });
});

test('voice events are not delivery observability', () => {
  const streams = messageStreams([sink()], [sub(['com.twilio.voice.insights.call-summary'])]);
  assert.deepEqual(streams, { live: [], broken: [] });
});

test('a sink that is not active is broken, not live', () => {
  const streams = messageStreams([sink('failed')],
                                 [sub(['com.twilio.messaging.message.delivered'])]);
  assert.deepEqual(streams.live, []);
  assert.deepEqual(streams.broken, [[SINK, 'failed']]);
});

test('a subscription pointing at no sink at all is broken', () => {
  const streams = messageStreams([], [sub(['com.twilio.messaging.message.sent'])]);
  assert.deepEqual(streams.broken, [[SINK, 'missing']]);
});

test('a service with no callback and no stream is blind', () => {
  const [state, detail] = verdict({ sid: 'MG1', status_callback: null, fallback_url: null });
  assert.equal(state, 'blind');
  assert.match(detail, /com\\.twilio\\.messaging\\.message\\./);
  assert.match(detail, /No fallback_url either\\./);
});

test('the status callback settles it', () => {
  const [state, detail] = verdict({
    status_callback: 'https://app.example.com/twilio/status',
    fallback_url: 'https://app.example.com/twilio/fallback',
  });
  assert.equal(state, 'callback');
  assert.ok(!/No fallback_url/.test(detail));
});

test('event streams counts when the sink is active', () => {
  const [state] = verdict({ status_callback: '' }, { live: [SINK], broken: [] });
  assert.equal(state, 'streamed');
});

test('a failed sink is worse than nothing and says so', () => {
  const [state, detail] = verdict({ status_callback: '' },
                                  { live: [], broken: [[SINK, 'failed']] });
  assert.equal(state, 'sink-failed');
  assert.match(detail, /Believed working/);
});
''',
"faq": [
 ("Is queued or accepted not a success?",
  "It is a success at accepting the message, and says nothing about delivery. The terminal status, sent, delivered, undelivered or failed, plus any error_code, arrives asynchronously and is reported only to a status callback or an Event Streams sink."),
 ("Can I poll the Messages list instead?",
  "As an audit, yes; as a pipeline, no. Messages.json has no Status filter and no ErrorCode filter, so continuous polling means paging every message in the window and filtering client-side. That is the exact cost the callback exists to remove."),
 ("What is the difference between the service callback and the per-message one?",
  "The StatusCallback parameter on Messages.create overrides the service-level status_callback for that message. That is why a service can look uninstrumented while one well-written code path is fine, and it is worth checking both before concluding anything."),
 ("Does an Event Streams sink replace the callback?",
  "It can, when the sink status is active and a subscription actually carries com.twilio.messaging.message.* events. A sink subscribed to something else, or sitting in a non-active status, is worse than nothing, because the team believes delivery is being recorded."),
 ("What has to happen in the handler for this to be worth setting?",
  "Validate X-Twilio-Signature, persist MessageStatus and ErrorCode against your own record, and act on the codes: suppress on 21610, review content on 30007, check registration on 30034. A callback whose handler drops the payload is the same blindness with more inbound traffic."),
],
"related": [
 ("/twilio/messages-stuck-queued-or-accepted/", "Messages that never leave queued or accepted"),
 ("/twilio/carrier-filtered-messages-30007/", "Carrier filtering that drops SMS silently"),
 ("/twilio/opted-out-recipients-21610/", "Sends to recipients who already texted STOP"),
],
"citations": [CITE_SERVICE, CITE_STATUS, CITE_SINK, CITE_SUB],
},

]
