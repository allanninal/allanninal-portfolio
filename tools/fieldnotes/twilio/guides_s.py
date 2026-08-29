#!/usr/bin/env python3
"""/twilio/ field notes, batch S — the writing.

Four Verify settings that nobody revisits once the integration works. A code
length picked in the first week because it was quicker to read off a phone
during QA, a five-check budget spent by a keystroke handler, a resend button
with no cooldown, and a warning line that has been off since the account was
created. None of them break anything on the day they are set, which is exactly
why they are all still like that.

Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run. Verify spends money on every
attempt, which is precisely why a credential pointed at it should not be able to
start one.
"""

CITE_VSERVICE = ("Verify Service resource — Twilio Docs",
                 "https://www.twilio.com/docs/verify/api/service")
CITE_VERIFICATION = ("Verification resource — Twilio Docs",
                     "https://www.twilio.com/docs/verify/api/verification")
CITE_TEMPLATES = ("Verify Templates — Twilio Docs",
                  "https://www.twilio.com/docs/verify/api/templates")
CITE_RATELIMITS = ("Verify Service Rate Limits — Twilio Docs",
                   "https://www.twilio.com/docs/verify/api/service-rate-limits")
CITE_60202 = ("Error 60202: max verification check attempts reached — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/60202")
CITE_60203 = ("Error 60203: max send attempts reached — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/60203")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "verify-code-length-too-short",
"title": "A Verify Service issuing four-digit codes to production",
"description": "Four digits is ten thousand codes and each verification allows five checks. No error code will ever mention it, and nobody has looked at the field since.",
"h1": "a Verify Service issuing four-digit codes to production",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio verify code length", "verify code_length 4",
             "twilio custom_code_enabled", "otp brute force keyspace",
             "twilio verify service settings"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing is failing. Codes arrive, users type them in, verifications approve, and conversion rate is flat and healthy. The only thing to notice is one integer in the Service resource, set during the first week of the integration when a four-digit code was faster to read off a phone during QA &mdash; and that has been the length of every code you have sent since.",
"short_answer": """<p>Read <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}</code> and flag any Service whose <code>code_length</code> is below <code>6</code>. Read <code>custom_code_enabled</code> in the same response: <code>true</code> in production means your own application supplies the code and Twilio's randomness is not involved at all.</p>
<p>Four digits is 10000 possible codes. Each verification allows five checks before <code>60202</code>, and the budget is scoped to the verification, so starting a fresh one resets it. That is roughly 1000 starts for even odds against a single code. Six digits multiplies both numbers by a hundred.</p>""",
"problem": """<p>This is not a bug and it never becomes one. There is no error, no failed request, no degraded metric, nothing that fires. The Service does exactly what it was configured to do on the day somebody typed a <code>4</code> into a form, and it will keep doing it forever, because the only symptom is a number that has to be reasoned about rather than observed.</p>
<p>The arithmetic only becomes dangerous in combination with an endpoint that will start verifications on demand, which is the ordinary shape of a signup or login form. Five guesses per verification is a real ceiling; five guesses per verification, and anyone can create verifications, is not a ceiling at all. That second half is <a href="/twilio/verify-no-rate-limits/">a Verify Service with zero rate limits</a>, and the two findings are worth reading together &mdash; each one is survivable and the pair is not.</p>
<p>When it does get exercised, the evidence looks like ordinary user friction. A grinding attack produces a stream of verifications that each end in <code>max_attempts_reached</code>, which is indistinguishable from people mistyping codes unless somebody is already counting the rate. Twilio's own protections notice repetition against one destination; an attacker working against one account's phone number is not repeating anything else.</p>""",
"why": """<p><strong>The length was a product decision, made once, under time pressure.</strong> Shorter codes are easier to read aloud, easier to type on a small keyboard, and produce fewer support calls about typos. Every one of those arguments is true, none of them is wrong, and all of them were made before anyone in the room had run the keyspace numbers. Nothing about the decision decays, so nothing ever prompts a second look.</p>
<p><strong>The five-check budget is scoped to the verification, not to the phone number.</strong> That is the mechanism that makes a short code cheap to attack. Burning all five checks kills one verification and nothing else; the next <code>POST</code> to start a verification hands over five more. The defence is per-object and the attack is per-request, so the attack simply buys more objects.</p>
<p><strong><code>custom_code_enabled</code> turns the length field into decoration.</strong> With it on, your application supplies the code and Twilio delivers whatever it is given. <code>code_length</code> still sits in the response looking authoritative while describing nothing. It gets switched on for a test harness that needs deterministic codes, and switching it back off is a step in nobody's checklist.</p>
<p><strong>The ten-minute lifetime caps rate, not total attempts.</strong> A code expiring limits how many guesses fit inside one window, but the attacker is not confined to one window. They start another verification. The TTL is the reason an attack takes hours instead of minutes; it is not the reason it fails.</p>
<p><strong>Nothing in your own logs records the exposure.</strong> A short code produces no distinct error, no alert, and no line in the Debugger. The field is readable in one <code>GET</code> and invisible in every dashboard, which is why an audit that reads it deliberately is the only thing that finds it.</p>""",
"steps": [
 {"h": "List the Services and read the two fields that matter",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services</code> for the inventory, then read <code>code_length</code> and <code>custom_code_enabled</code> off each Service in the same response. Accounts collect Services &mdash; one per brand, one per environment, one from a proof of concept &mdash; and the short one is rarely the one you were looking at.</p>"""},
 {"h": "Do the arithmetic instead of eyeballing the integer",
  "body": """<p><code>4</code> and <code>6</code> look like neighbouring numbers and are not. Ten thousand codes against a million; a thousand verification starts for even odds against a hundred thousand. Printing the keyspace and the start count next to the length is what turns the field from a preference into a finding somebody will act on.</p>"""},
 {"h": "Treat custom_code_enabled as outranking the length",
  "body": """<p>If <code>custom_code_enabled</code> is <code>true</code>, stop reading <code>code_length</code>: it no longer describes what gets sent. Whatever your code generates is the code, including the sequential integers a test fixture was handing out when somebody enabled the flag.</p>"""},
 {"h": "Find out whether the length is load-bearing elsewhere",
  "body": """<p>Raising it breaks a fixed-width four-box input, an SMS template that says "your 4 digit code", a voice prompt that reads digits in pairs, and any test fixture that hard-codes a value. This is the step that actually takes the time, and skipping it is how a code-length change becomes an outage on the login screen.</p>"""},
 {"h": "Raise it, then pair it with a rate limit",
  "body": """<p><code>POST https://verify.twilio.com/v2/Services/{ServiceSid}</code> with <code>CodeLength=6</code> and <code>CustomCodeEnabled=false</code>. Existing verifications keep the length they were created with, so the change is not retroactive and does not invalidate codes already in flight. Then add a Service Rate Limit, because the check budget resets on every start and the length alone is only half the control.</p>"""},
],
"verify": """<p>Re-run the script. Every Service should report <code>ok</code>, and the count below the bar should be zero.</p>
<pre><code class="language-bash">python3 twilio_verify_code_length_audit.py
# 3 service(s), 0 issuing codes below 6 digits</code></pre>""",
"code_intro": "One paginated GET over the Verify Services and nothing else &mdash; give it an API Key with read access. The classifier is pure and does the arithmetic in the output, because a report that says <code>code_length is 4</code> gets filed and a report that says <code>10000 codes, about 1000 starts for even odds</code> gets fixed.",
"py_file": "twilio_verify_code_length_audit.py",
"py": '''"""Report Verify Services issuing codes short enough to grind through.

The five-check budget that protects a code is scoped to the verification, so an
attacker who can start verifications resets it at will. That makes the keyspace,
not the check limit, the number that decides how much work an attack is.

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
log = logging.getLogger("twilio_verify_code_length_audit")

VERIFY = "https://verify.twilio.com/v2"

# Fixed by the platform: the fifth failed check on a verification returns 60202
# and that verification is dead for the rest of its lifetime. Starting a new one
# hands the caller five more, which is the whole reason length matters.
CHECKS_PER_VERIFICATION = 5

# Twilio accepts 4 through 10.
MIN_LENGTH_ALLOWED = 4
MAX_LENGTH_ALLOWED = 10

MIN_SAFE_LENGTH = 6


def keyspace(code_length):
    """Number of codes a length can produce, or None if the value is unusable.

    Anything outside the range Twilio issues is not a length to reason about,
    and reporting it as safe would be worse than reporting it as unknown.
    """
    try:
        n = int(code_length)
    except (TypeError, ValueError):
        return None
    if n < MIN_LENGTH_ALLOWED or n > MAX_LENGTH_ALLOWED:
        return None
    return 10 ** n


def starts_for_even_odds(space, checks=CHECKS_PER_VERIFICATION):
    """Fresh verifications needed for a 50/50 chance of hitting one code.

    Half the space on average, five guesses per verification, because the check
    budget belongs to the verification and starting another one resets it.
    """
    if not space or checks <= 0:
        return None
    return int(round(space / (2.0 * checks)))


def verdict(service, min_length=MIN_SAFE_LENGTH):
    """Classify one Verify Service by how guessable the codes it issues are.

    Pure, so the arithmetic can be tested without a network. Returns
    (state, detail).
    """
    length = service.get("code_length")
    space = keyspace(length)

    if service.get("custom_code_enabled"):
        return ("custom-code",
                "custom_code_enabled is true: the codes come from your own "
                "application, so code_length (%s) describes nothing that is "
                "actually sent and Twilio generates none of it." % (length,))

    if space is None:
        return ("unreadable",
                "code_length is %r, which is not a length Twilio issues (%d to "
                "%d). Report it as unknown rather than as safe."
                % (length, MIN_LENGTH_ALLOWED, MAX_LENGTH_ALLOWED))

    n = int(length)
    detail = ("%d digits: %d codes, %d checks per verification, about %d fresh "
              "starts for even odds against one code."
              % (n, space, CHECKS_PER_VERIFICATION, starts_for_even_odds(space)))

    if n < min_length - 1:
        return ("short", detail + " Nothing caps the number of starts but you.")
    if n < min_length:
        return ("thin", detail + " An afternoon of scripted starts, not a week.")
    return ("ok", detail)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page(session, url, field, **params):
    """Walk a Verify v2 list. Paging lives in meta.next_page_url."""
    out = []
    while url:
        body = get(session, url, **params)
        out.extend(body.get(field, []))
        url, params = (body.get("meta") or {}).get("next_page_url"), {}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", action="append", default=[],
                    help="Verify Service SID; repeatable. Default: every service")
    ap.add_argument("--min-length", type=int, default=MIN_SAFE_LENGTH,
                    help="shortest code length to accept without comment")
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

    if args.service:
        services = [get(session, "%s/Services/%s" % (VERIFY, s))
                    for s in args.service]
    else:
        services = page(session, VERIFY + "/Services", "services", PageSize=50)
    if not services:
        log.info("no Verify services on this account")
        return 0

    bad = 0
    for svc in services:
        sid = svc.get("sid", "?")
        state, detail = verdict(svc, args.min_length)
        line = "%-11s %s (%s)  %s" % (state, svc.get("friendly_name", "?"), sid, detail)
        if state == "ok":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: POST %s/Services/%s with CodeLength=%d and "
                    "CustomCodeEnabled=false", VERIFY, sid, max(args.min_length, 6))
        log.warning("  then add a Service Rate Limit: the check budget resets on "
                    "every new verification, so length alone is half a control")

    log.info("%d service(s), %d issuing codes below %d digits",
             len(services), bad, args.min_length)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-code-length-audit.mjs",
"js": '''/**
 * Report Verify Services issuing codes short enough to grind through.
 *
 * The five-check budget that protects a code is scoped to the verification, so
 * an attacker who can start verifications resets it at will. That makes the
 * keyspace, not the check limit, the number that decides how much work an
 * attack is.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';

// Fixed by the platform: the fifth failed check returns 60202 and that
// verification is dead. Starting a new one hands the caller five more.
export const CHECKS_PER_VERIFICATION = 5;

// Twilio accepts 4 through 10.
const MIN_LENGTH_ALLOWED = 4;
const MAX_LENGTH_ALLOWED = 10;

export const MIN_SAFE_LENGTH = 6;

/**
 * Number of codes a length can produce, or null if the value is unusable.
 * Anything outside the range Twilio issues is reported as unknown, never safe.
 */
export function keyspace(codeLength) {
  // Number(null) is 0 rather than NaN, so a missing field has to be rejected
  // before the arithmetic instead of after it.
  if (codeLength === null || codeLength === undefined || codeLength === '') return null;
  const n = Number(codeLength);
  if (!Number.isInteger(n)) return null;
  if (n < MIN_LENGTH_ALLOWED || n > MAX_LENGTH_ALLOWED) return null;
  return 10 ** n;
}

/**
 * Fresh verifications needed for a 50/50 chance of hitting one code: half the
 * space on average, five guesses per verification.
 */
export function startsForEvenOdds(space, checks = CHECKS_PER_VERIFICATION) {
  if (!space || checks <= 0) return null;
  return Math.round(space / (2 * checks));
}

/**
 * Classify one Verify Service by how guessable the codes it issues are. Pure,
 * so the arithmetic can be tested without a network. Returns [state, detail].
 */
export function verdict(service, minLength = MIN_SAFE_LENGTH) {
  const length = service.code_length;
  const space = keyspace(length);

  if (service.custom_code_enabled) {
    return ['custom-code',
      `custom_code_enabled is true: the codes come from your own application, ` +
      `so code_length (${length}) describes nothing that is actually sent and ` +
      'Twilio generates none of it.'];
  }

  if (space === null) {
    return ['unreadable',
      `code_length is ${JSON.stringify(length)}, which is not a length Twilio ` +
      `issues (${MIN_LENGTH_ALLOWED} to ${MAX_LENGTH_ALLOWED}). Report it as ` +
      'unknown rather than as safe.'];
  }

  const n = Number(length);
  const detail = `${n} digits: ${space} codes, ${CHECKS_PER_VERIFICATION} ` +
    `checks per verification, about ${startsForEvenOdds(space)} fresh starts ` +
    'for even odds against one code.';

  if (n < minLength - 1) {
    return ['short', `${detail} Nothing caps the number of starts but you.`];
  }
  if (n < minLength) {
    return ['thin', `${detail} An afternoon of scripted starts, not a week.`];
  }
  return ['ok', detail];
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

/** Walk a Verify v2 list. Paging lives in meta.next_page_url. */
async function page(auth, url, field, params = {}) {
  const out = [];
  let next = url;
  let p = params;
  while (next) {
    const body = await get(auth, next, p);
    out.push(...(body[field] ?? []));
    next = body.meta?.next_page_url ?? null;
    p = {};
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

  const services = await page(auth, `${VERIFY}/Services`, 'services', { PageSize: 50 });
  if (services.length === 0) {
    console.log('no Verify services on this account');
    return;
  }

  let bad = 0;
  for (const svc of services) {
    const [state, detail] = verdict(svc);
    const line = `${state.padEnd(11)} ${svc.friendly_name ?? '?'} (${svc.sid})  ${detail}`;
    if (state === 'ok') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: POST ${VERIFY}/Services/${svc.sid} with CodeLength=6 ` +
                 'and CustomCodeEnabled=false');
    console.warn('  then add a Service Rate Limit: the check budget resets on ' +
                 'every new verification, so length alone is half a control');
  }

  console.log(`${services.length} service(s), ${bad} issuing codes below ` +
              `${MIN_SAFE_LENGTH} digits`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the boundary and the two states that a naive length check gets wrong: five digits, which is below the bar without being the headline; a Service with <code>custom_code_enabled</code>, where the length field is honest-looking and meaningless; and a length outside the range Twilio issues, which has to come back as unknown rather than as passing.",
"test_py_file": "test_twilio_verify_code_length_audit.py",
"test_py": '''from twilio_verify_code_length_audit import (keyspace, starts_for_even_odds,
                                              verdict)


def test_four_digits_is_ten_thousand_codes():
    state, detail = verdict({"code_length": 4})
    assert state == "short"
    assert "10000 codes" in detail
    assert "1000 fresh starts" in detail


def test_five_digits_is_below_the_bar_without_being_the_headline():
    state, detail = verdict({"code_length": 5})
    assert state == "thin"
    assert "100000 codes" in detail


def test_six_digits_passes():
    state, detail = verdict({"code_length": 6})
    assert state == "ok"
    assert "1000000 codes" in detail


def test_custom_code_outranks_a_perfectly_good_length():
    # The field still reads 6. It describes nothing that gets sent.
    state, detail = verdict({"code_length": 6, "custom_code_enabled": True})
    assert state == "custom-code"
    assert "your own application" in detail


def test_a_length_twilio_cannot_issue_is_unknown_not_safe():
    assert verdict({"code_length": 12})[0] == "unreadable"
    assert verdict({})[0] == "unreadable"
    assert verdict({"code_length": "six"})[0] == "unreadable"


def test_even_odds_spends_five_guesses_per_start():
    assert starts_for_even_odds(10000) == 1000
    assert starts_for_even_odds(1000000) == 100000
    assert starts_for_even_odds(None) is None


def test_keyspace_covers_the_range_and_rejects_the_rest():
    assert keyspace(4) == 10000
    assert keyspace(10) == 10 ** 10
    assert keyspace(3) is None
    assert keyspace(None) is None
''',
"test_js_file": "twilio-verify-code-length-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keyspace, startsForEvenOdds, verdict } from './twilio-verify-code-length-audit.mjs';

test('four digits is ten thousand codes', () => {
  const [state, detail] = verdict({ code_length: 4 });
  assert.equal(state, 'short');
  assert.match(detail, /10000 codes/);
  assert.match(detail, /1000 fresh starts/);
});

test('five digits is below the bar without being the headline', () => {
  const [state, detail] = verdict({ code_length: 5 });
  assert.equal(state, 'thin');
  assert.match(detail, /100000 codes/);
});

test('six digits passes', () => {
  const [state, detail] = verdict({ code_length: 6 });
  assert.equal(state, 'ok');
  assert.match(detail, /1000000 codes/);
});

test('custom code outranks a perfectly good length', () => {
  const [state, detail] = verdict({ code_length: 6, custom_code_enabled: true });
  assert.equal(state, 'custom-code');
  assert.match(detail, /your own application/);
});

test('a length twilio cannot issue is unknown not safe', () => {
  assert.equal(verdict({ code_length: 12 })[0], 'unreadable');
  assert.equal(verdict({})[0], 'unreadable');
  assert.equal(verdict({ code_length: 'six' })[0], 'unreadable');
});

test('even odds spends five guesses per start', () => {
  assert.equal(startsForEvenOdds(10000), 1000);
  assert.equal(startsForEvenOdds(1000000), 100000);
  assert.equal(startsForEvenOdds(null), null);
});

test('keyspace covers the range and rejects the rest', () => {
  assert.equal(keyspace(4), 10000);
  assert.equal(keyspace(10), 10 ** 10);
  assert.equal(keyspace(3), null);
  assert.equal(keyspace(null), null);
});
''',
"faq": [
 ("Is four digits actually exploitable, or is this theatre?",
  "It is exploitable exactly when your start endpoint is. Five checks per verification is a real ceiling if the attacker gets one verification. It is not a ceiling at all if they can create ten thousand. That is why the fix is two changes, not one: raise the length and add a Service Rate Limit keyed on something you control."),
 ("Does raising code_length invalidate codes already in flight?",
  "No. A verification carries the length it was created with, so codes already sent keep working until they expire. The change applies to verifications started after it. That makes this one of the few Verify settings you can move during business hours."),
 ("Why does custom_code_enabled get its own state?",
  "Because it makes the length field a lie rather than a low number, and the two need different fixes. With custom codes on, the report has to send you to your own generator: whatever it produces is the code, including the sequential integers a test fixture was handing out when somebody switched the flag on."),
 ("Six digits or more?",
  "Six is the point where the keyspace stops being the weak link and your rate limits become the binding control. Longer codes buy less than the next limit does, and they cost you in typos and support volume. Spend the effort on the start endpoint instead."),
 ("Will Twilio's own protections not stop a brute force?",
  "They stop repetition against one destination number, which is the pattern of an impatient user or a retry loop. An attacker grinding one victim's code is not repeating a destination faster than a real person would; they are starting ordinary-looking verifications for a number that is genuinely theirs to target."),
],
"related": [
 ("/twilio/verify-no-rate-limits/", "A Verify Service with zero rate limits configured"),
 ("/twilio/verify-max-check-attempts/", "A verification that burned all five checks"),
 ("/twilio/verify-do-not-share-warning-off/", "OTP codes sent without the do-not-share warning"),
],
"citations": [CITE_VSERVICE, CITE_60202, CITE_VERIFICATION, CITE_KEYS],
},

{
"slug": "verify-max-check-attempts",
"title": "60202: a verification that burned all five check attempts",
"description": "The code is right and the check still fails. A handler that fires on every keystroke spends the five-attempt budget before the user has finished typing.",
"h1": "60202: a verification that burned all five check attempts",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 60202", "max check attempts reached",
             "twilio verify max_attempts_reached", "verify check 429",
             "twilio verify stuck user"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The support ticket says the code does not work. It does work; the user is holding the right one. Somewhere between the keypad and your server the five checks that verification was allowed have already been spent, the verification has moved to <code>max_attempts_reached</code>, and every further attempt returns <code>60202</code> until it expires. The screen offers a Verify button that can no longer do anything.",
"short_answer": """<p>Read <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VerificationSid}</code> and look at <code>status</code>. <code>max_attempts_reached</code> means the five-check budget is gone and the verification is dead for the remainder of its ten-minute lifetime, regardless of what the user types next.</p>
<p>A <code>404</code> from that same call is not an error: Verify soft-deletes a verification once it is approved, canceled or expired, so a missing resource means it already resolved. Count the <code>max_attempts_reached</code> rate against the verifications you inspected &mdash; a handful is users mistyping, a few percent is a client firing checks it was never asked to fire.</p>""",
"problem": """<p>Five is a generous budget for a person and no budget at all for a loop. A person types six digits, glances at the message again, corrects one, and submits twice. A form that calls the check endpoint on every <code>input</code> event submits five times before the user has finished the code, and each of those is a genuine failed check against a partial string. By the time the last digit lands the verification is already dead, and the failure the user sees is the only correct code they will ever type.</p>
<p>What makes it hard to see from the outside is that the <code>60202</code> lands on the request that <em>should</em> have succeeded. The four failures before it are invisible to the user, and in your logs they look like ordinary wrong-code attempts. So the bug reports say the code is wrong when the code was right, and reproducing it needs someone to type at the speed a real user types rather than pasting the value in.</p>
<p>The other producer is a double-firing handler: a form that submits on both <code>click</code> and <code>submit</code>, a React effect without a dependency array, a retry wrapper that repeats a check after a slow response even though the first one arrived. Those spend the budget two at a time, which turns a user with one typo into a user who is locked out.</p>""",
"why": """<p><strong>The budget belongs to the verification, and the user cannot see it.</strong> There is no counter in the response and nothing in the UI that says two of five. The state moves from <code>pending</code> to <code>max_attempts_reached</code> in one step, with no warning at four, so the first evidence anyone gets is the error that ends the session.</p>
<p><strong>The error is a 429, which invites exactly the wrong reaction.</strong> Client code that sees <code>429</code> backs off and retries, because that is what <code>429</code> usually means. Here it means stop: the budget is not going to refill, and every retry is another logged failure against a verification that is already finished. Retrying a <code>60202</code> is a loop that can only produce more <code>60202</code>.</p>
<p><strong>The dead verification looks alive from the outside.</strong> Nothing expires visibly and nothing changes on the page. The input still accepts digits, the button still posts, and the only route out is to start a new verification &mdash; which is a thing the UI usually does not offer, because the resend button was designed for a code that failed to arrive rather than for one that arrived and then died.</p>
<p><strong>A 404 on the lookup means resolved, not missing.</strong> Verify soft-deletes a verification when it is approved, canceled or expired. An audit that treats <code>404</code> as an error will report the healthy majority as broken and bury the finding. Reading the absence correctly is most of what makes this script trustworthy.</p>
<p><strong>The rate is the diagnosis, not the individual record.</strong> One <code>max_attempts_reached</code> is a person having a bad morning. Two percent of all verifications ending that way is a client bug with a deploy date, and only counting tells you which of the two you have.</p>""",
"steps": [
 {"h": "Collect candidate verifications from the attempts list",
  "body": """<p>There is no list endpoint for verifications, so start from what there is: <code>GET https://verify.twilio.com/v2/Attempts?VerifyServiceSid={VA...}&amp;DateCreatedAfter={ISO8601}</code>. Every attempt carries a <code>verification_sid</code>; the distinct set of those is the population to inspect.</p>"""},
 {"h": "Fetch each verification and read status",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VerificationSid}</code>. <code>max_attempts_reached</code> is the finding. <code>pending</code> is still live. Anything else is the resource on its way out.</p>"""},
 {"h": "Treat 404 as resolved rather than as an error",
  "body": """<p>Verify soft-deletes a verification once it is approved, canceled or expired, so the lookup returns <code>404</code> for the ones that went fine. Fold those into a <code>resolved</code> bucket. A script that raises on <code>404</code> reports a healthy account as an outage.</p>"""},
 {"h": "Split the burned ones by whether the clock has run out",
  "body": """<p>Compare <code>date_created</code> against the ten-minute lifetime. Inside the window there is a person sitting in front of a broken screen right now, which is a page. Outside it, the record is evidence of a rate and nothing more. Same status, two different responses.</p>"""},
 {"h": "Fix the client, then give the user a way out",
  "body": """<p>Debounce the check and submit only on a complete code. Treat <code>60202</code> as terminal rather than retryable, and replace the Verify button with "send a new code". Server-side, a stuck verification can be closed with <code>POST https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VerificationSid}</code> and <code>Status=canceled</code>, then a fresh one started.</p>"""},
],
"verify": """<p>Re-run the script over the same window. The burned count should fall to the background rate of genuine typos, and nothing should be burned inside its lifetime.</p>
<pre><code class="language-bash">python3 twilio_verify_check_attempts_audit.py --hours 24
# 412 verification(s) inspected, 3 burned (0.7%), 0 still inside their lifetime</code></pre>""",
"code_intro": "One GET for the services, one paginated GET of the attempts to find which verifications existed, and one GET per verification &mdash; all read-only, so an API Key with read access is enough. The classifier is pure and takes the HTTP status alongside the body, because <code>404</code> is a verdict here rather than a failure and that decision deserves a test rather than a comment.",
"py_file": "twilio_verify_check_attempts_audit.py",
"py": '''"""Report Verify verifications that spent all five checks and died.

A verification allows five checks. A handler that fires on every keystroke, or
a form that submits twice, spends them before the user finishes typing, and the
verification moves to max_attempts_reached for the rest of its lifetime.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_verify_check_attempts_audit")

VERIFY = "https://verify.twilio.com/v2"

# Fixed by the platform: five checks per verification, and the verification lives
# ten minutes. Both numbers are the reason a burned one cannot be recovered.
MAX_CHECKS = 5
TTL_SECONDS = 600


def parse_time(value):
    """Parse a Verify timestamp into an aware datetime, or None.

    fromisoformat did not accept a trailing Z until 3.11 and every timestamp
    Verify returns has one, so the swap has to happen here rather than in the
    caller.
    """
    s = str(value or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def age_seconds(value, now):
    dt = parse_time(value)
    return None if dt is None else (now - dt).total_seconds()


def verdict(http_status, verification, now, ttl_seconds=TTL_SECONDS):
    """Classify one verification lookup.

    `http_status` matters as much as the body: Verify soft-deletes a verification
    once it is approved, canceled or expired, so a 404 means it resolved rather
    than that anything went wrong. Pure, so that rule can be tested without a
    network. Returns (state, detail).
    """
    if http_status == 404:
        return ("resolved",
                "404: the verification is soft deleted, which Verify does once "
                "it is approved, canceled or expired. Nothing is stuck.")

    body = verification or {}
    status = str(body.get("status") or "").strip().lower()

    if status == "max_attempts_reached":
        age = age_seconds(body.get("date_created"), now)
        if age is None:
            return ("burned",
                    "all %d checks spent. date_created is unreadable, so "
                    "whether the lifetime has run out cannot be told from here."
                    % MAX_CHECKS)
        remaining = ttl_seconds - age
        if remaining > 0:
            return ("burned-live",
                    "all %d checks spent %ds ago. Every further check returns "
                    "60202 for another %ds, and someone is looking at that "
                    "screen now." % (MAX_CHECKS, int(age), int(remaining)))
        return ("burned-cold",
                "all %d checks spent %ds ago, past the %ds lifetime. Nobody is "
                "stuck on it; it counts towards the rate."
                % (MAX_CHECKS, int(age), ttl_seconds))

    if status == "pending":
        return ("pending", "open, checks still available")
    if status in ("approved", "canceled"):
        return (status, "closed as " + status)
    return ("unknown", "status %r is not one this script recognises"
            % (body.get("status"),))


def fetch(session, url, **params):
    """GET returning (status_code, body). 404 is data here, not an error."""
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    if r.status_code == 404:
        return (404, {})
    r.raise_for_status()
    return (r.status_code, r.json())


def get(session, url, **params):
    status, body = fetch(session, url, **params)
    if status == 404:
        raise SystemExit("404 from %s: check the SID" % url)
    return body


def page(session, url, field, **params):
    """Walk a Verify v2 list. Paging lives in meta.next_page_url."""
    out = []
    while url:
        body = get(session, url, **params)
        out.extend(body.get(field, []))
        url, params = (body.get("meta") or {}).get("next_page_url"), {}
    return out


def verification_sids(session, service_sid, since, limit):
    """Distinct verification SIDs seen in the attempts list for a window.

    There is no list endpoint for verifications, so the attempts are the only
    read-only way to find out which ones existed. Order is preserved so the
    limit takes the oldest in the window rather than an arbitrary slice.
    """
    seen, out = set(), []
    for attempt in page(session, VERIFY + "/Attempts", "attempts",
                        VerifyServiceSid=service_sid, DateCreatedAfter=since,
                        PageSize=100):
        sid = attempt.get("verification_sid")
        if sid and sid not in seen:
            seen.add(sid)
            out.append(sid)
            if len(out) >= limit:
                break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", action="append", default=[],
                    help="Verify Service SID; repeatable. Default: every service")
    ap.add_argument("--hours", type=int, default=24,
                    help="how far back to look for verifications")
    ap.add_argument("--max-verifications", type=int, default=500,
                    help="stop after this many per service")
    ap.add_argument("--burn-rate", type=float, default=2.0,
                    help="percent burned above which this is a client bug")
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

    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=args.hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.service:
        services = [{"sid": s, "friendly_name": s} for s in args.service]
    else:
        services = page(session, VERIFY + "/Services", "services", PageSize=50)
    if not services:
        log.info("no Verify services on this account")
        return 0

    inspected = burned = live = 0
    for svc in services:
        sid = svc.get("sid")
        for ve in verification_sids(session, sid, since, args.max_verifications):
            status, body = fetch(
                session, "%s/Services/%s/Verifications/%s" % (VERIFY, sid, ve))
            state, detail = verdict(status, body, now)
            inspected += 1
            if not state.startswith("burned"):
                continue
            burned += 1
            log.warning("%-12s %s  %s", state, ve, detail)
            if state == "burned-live":
                live += 1
                log.warning("  repair now: POST %s/Services/%s/Verifications/%s "
                            "with Status=canceled, then start a fresh "
                            "verification for that user", VERIFY, sid, ve)

    if not inspected:
        log.info("no verifications in the last %d hour(s)", args.hours)
        return 0

    rate = 100.0 * burned / inspected
    log.info("%d verification(s) inspected, %d burned (%.1f%%), %d still inside "
             "their lifetime", inspected, burned, rate, live)
    if rate > args.burn_rate:
        log.warning("above %.1f%%: debounce the check call and submit only on a "
                    "complete code. 60202 is terminal, not retryable.",
                    args.burn_rate)
        return 1
    return 1 if live else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-check-attempts-audit.mjs",
"js": '''/**
 * Report Verify verifications that spent all five checks and died.
 *
 * A verification allows five checks. A handler that fires on every keystroke,
 * or a form that submits twice, spends them before the user finishes typing,
 * and the verification moves to max_attempts_reached for the rest of its
 * lifetime.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';

// Fixed by the platform: five checks per verification, ten minute lifetime.
export const MAX_CHECKS = 5;
export const TTL_SECONDS = 600;

/** Parse a Verify timestamp into epoch milliseconds, or null. */
export function parseTime(value) {
  const s = String(value ?? '').trim();
  if (!s) return null;
  const ms = Date.parse(s);
  return Number.isFinite(ms) ? ms : null;
}

export function ageSeconds(value, nowMs) {
  const ms = parseTime(value);
  return ms === null ? null : (nowMs - ms) / 1000;
}

/**
 * Classify one verification lookup. `httpStatus` matters as much as the body:
 * Verify soft-deletes a verification once it is approved, canceled or expired,
 * so a 404 means it resolved rather than that anything went wrong. Pure, so
 * that rule can be tested without a network. Returns [state, detail].
 */
export function verdict(httpStatus, verification, nowMs, ttlSeconds = TTL_SECONDS) {
  if (httpStatus === 404) {
    return ['resolved',
      '404: the verification is soft deleted, which Verify does once it is ' +
      'approved, canceled or expired. Nothing is stuck.'];
  }

  const body = verification ?? {};
  const status = String(body.status ?? '').trim().toLowerCase();

  if (status === 'max_attempts_reached') {
    const age = ageSeconds(body.date_created, nowMs);
    if (age === null) {
      return ['burned',
        `all ${MAX_CHECKS} checks spent. date_created is unreadable, so ` +
        'whether the lifetime has run out cannot be told from here.'];
    }
    const remaining = ttlSeconds - age;
    if (remaining > 0) {
      return ['burned-live',
        `all ${MAX_CHECKS} checks spent ${Math.trunc(age)}s ago. Every further ` +
        `check returns 60202 for another ${Math.trunc(remaining)}s, and ` +
        'someone is looking at that screen now.'];
    }
    return ['burned-cold',
      `all ${MAX_CHECKS} checks spent ${Math.trunc(age)}s ago, past the ` +
      `${ttlSeconds}s lifetime. Nobody is stuck on it; it counts towards the rate.`];
  }

  if (status === 'pending') return ['pending', 'open, checks still available'];
  if (status === 'approved' || status === 'canceled') {
    return [status, `closed as ${status}`];
  }
  return ['unknown',
    `status ${JSON.stringify(body.status)} is not one this script recognises`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

/** GET returning [status, body]. 404 is data here, not an error. */
async function fetchJson(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (res.status === 404) return [404, {}];
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return [res.status, await res.json()];
}

async function get(auth, url, params = {}) {
  const [status, body] = await fetchJson(auth, url, params);
  if (status === 404) throw new Error(`404 from ${url}: check the SID`);
  return body;
}

/** Walk a Verify v2 list. Paging lives in meta.next_page_url. */
async function page(auth, url, field, params = {}) {
  const out = [];
  let next = url;
  let p = params;
  while (next) {
    const body = await get(auth, next, p);
    out.push(...(body[field] ?? []));
    next = body.meta?.next_page_url ?? null;
    p = {};
  }
  return out;
}

/** Distinct verification SIDs seen in the attempts list for a window. */
export async function verificationSids(auth, serviceSid, since, limit) {
  const seen = new Set();
  const attempts = await page(auth, `${VERIFY}/Attempts`, 'attempts', {
    VerifyServiceSid: serviceSid, DateCreatedAfter: since, PageSize: 100,
  });
  for (const attempt of attempts) {
    if (attempt.verification_sid) seen.add(attempt.verification_sid);
    if (seen.size >= limit) break;
  }
  return [...seen];
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

  const hoursArg = process.argv.indexOf('--hours');
  const hours = hoursArg === -1 ? 24 : Number(process.argv[hoursArg + 1]) || 24;
  const nowMs = Date.now();
  const since = `${new Date(nowMs - hours * 3600 * 1000).toISOString().slice(0, 19)}Z`;

  const services = await page(auth, `${VERIFY}/Services`, 'services', { PageSize: 50 });
  if (services.length === 0) {
    console.log('no Verify services on this account');
    return;
  }

  let inspected = 0;
  let burned = 0;
  let live = 0;
  for (const svc of services) {
    for (const ve of await verificationSids(auth, svc.sid, since, 500)) {
      const [status, body] = await fetchJson(
        auth, `${VERIFY}/Services/${svc.sid}/Verifications/${ve}`);
      const [state, detail] = verdict(status, body, nowMs);
      inspected += 1;
      if (!state.startsWith('burned')) continue;
      burned += 1;
      console.warn(`${state.padEnd(12)} ${ve}  ${detail}`);
      if (state === 'burned-live') {
        live += 1;
        console.warn(`  repair now: POST ${VERIFY}/Services/${svc.sid}/` +
                     `Verifications/${ve} with Status=canceled, then start a ` +
                     'fresh verification for that user');
      }
    }
  }

  if (inspected === 0) {
    console.log(`no verifications in the last ${hours} hour(s)`);
    return;
  }

  const rate = (100 * burned) / inspected;
  console.log(`${inspected} verification(s) inspected, ${burned} burned ` +
              `(${rate.toFixed(1)}%), ${live} still inside their lifetime`);
  if (rate > 2) {
    console.warn('above 2.0%: debounce the check call and submit only on a ' +
                 'complete code. 60202 is terminal, not retryable.');
  }
  process.exitCode = rate > 2 || live ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two decisions carry this script and both are easy to get quietly wrong: a <code>404</code> has to read as resolved rather than as a failure, and a burned verification inside its ten-minute lifetime has to be separated from one outside it, because the first is a person waiting and the second is a statistic. The clock is passed in rather than read from the system, so the tests pin real elapsed times instead of sleeping.",
"test_py_file": "test_twilio_verify_check_attempts_audit.py",
"test_py": '''from datetime import datetime, timedelta, timezone

from twilio_verify_check_attempts_audit import age_seconds, parse_time, verdict

NOW = datetime(2026, 3, 4, 12, 0, 0, tzinfo=timezone.utc)


def iso(seconds_ago):
    return (NOW - timedelta(seconds=seconds_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_404_is_resolved_not_an_error():
    state, detail = verdict(404, None, NOW)
    assert state == "resolved"
    assert "soft deleted" in detail


def test_burned_inside_the_lifetime_is_someone_waiting_now():
    state, detail = verdict(200, {"status": "max_attempts_reached",
                                  "date_created": iso(120)}, NOW)
    assert state == "burned-live"
    assert "another 480s" in detail


def test_burned_after_the_lifetime_is_only_a_statistic():
    state, detail = verdict(200, {"status": "max_attempts_reached",
                                  "date_created": iso(3600)}, NOW)
    assert state == "burned-cold"
    assert "Nobody is stuck" in detail


def test_burned_with_an_unreadable_clock_is_still_burned():
    state, detail = verdict(200, {"status": "max_attempts_reached",
                                  "date_created": "not a date"}, NOW)
    assert state == "burned"
    assert "unreadable" in detail


def test_pending_and_approved_are_left_alone():
    assert verdict(200, {"status": "pending"}, NOW)[0] == "pending"
    assert verdict(200, {"status": "approved"}, NOW)[0] == "approved"


def test_an_unrecognised_status_is_reported_rather_than_assumed_healthy():
    state, detail = verdict(200, {"status": "expired"}, NOW)
    assert state == "unknown"
    assert "expired" in detail


def test_timestamps_with_a_trailing_z_parse_on_3_9():
    assert parse_time("2026-03-04T11:58:00Z") is not None
    assert parse_time("") is None
    assert age_seconds(iso(60), NOW) == 60
''',
"test_js_file": "twilio-verify-check-attempts-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageSeconds, parseTime, verdict } from './twilio-verify-check-attempts-audit.mjs';

const NOW = Date.parse('2026-03-04T12:00:00Z');
const iso = (secondsAgo) =>
  `${new Date(NOW - secondsAgo * 1000).toISOString().slice(0, 19)}Z`;

test('404 is resolved not an error', () => {
  const [state, detail] = verdict(404, null, NOW);
  assert.equal(state, 'resolved');
  assert.match(detail, /soft deleted/);
});

test('burned inside the lifetime is someone waiting now', () => {
  const [state, detail] = verdict(
    200, { status: 'max_attempts_reached', date_created: iso(120) }, NOW);
  assert.equal(state, 'burned-live');
  assert.match(detail, /another 480s/);
});

test('burned after the lifetime is only a statistic', () => {
  const [state, detail] = verdict(
    200, { status: 'max_attempts_reached', date_created: iso(3600) }, NOW);
  assert.equal(state, 'burned-cold');
  assert.match(detail, /Nobody is stuck/);
});

test('burned with an unreadable clock is still burned', () => {
  const [state, detail] = verdict(
    200, { status: 'max_attempts_reached', date_created: 'not a date' }, NOW);
  assert.equal(state, 'burned');
  assert.match(detail, /unreadable/);
});

test('pending and approved are left alone', () => {
  assert.equal(verdict(200, { status: 'pending' }, NOW)[0], 'pending');
  assert.equal(verdict(200, { status: 'approved' }, NOW)[0], 'approved');
});

test('an unrecognised status is reported rather than assumed healthy', () => {
  const [state, detail] = verdict(200, { status: 'expired' }, NOW);
  assert.equal(state, 'unknown');
  assert.match(detail, /expired/);
});

test('timestamps parse and age is measured in seconds', () => {
  assert.notEqual(parseTime('2026-03-04T11:58:00Z'), null);
  assert.equal(parseTime(''), null);
  assert.equal(ageSeconds(iso(60), NOW), 60);
});
''',
"faq": [
 ("Can I reset the check counter on a verification?",
  "No. The five checks belong to that verification and nothing refills them. The only way forward is a new verification, which is why the fix on the client is to replace the Verify button with a request-a-new-code button once 60202 comes back rather than letting the user keep pressing."),
 ("Why does the lookup 404 for most of my verifications?",
  "Because they worked. Verify soft-deletes a verification once it is approved, canceled or expired, so a 404 is the ordinary end state and not a missing record. An audit that treats it as an error will flag a healthy account, which is why the script counts 404 as resolved."),
 ("60202 is a 429. Should the client back off and retry?",
  "No, and this is the trap. A 429 usually means slow down and try again, but this one means the budget is gone for good. A generic retry wrapper turns one exhausted verification into a stream of identical failures against a resource that can no longer approve anything."),
 ("How do I tell a client bug from users mistyping?",
  "By the rate. A percent or less spread evenly across the day is people. Several percent, or a step change that starts on a deploy date, is a handler firing checks the user did not ask for. That is why the script reports the rate rather than a list of records."),
 ("Should the server cancel stuck verifications automatically?",
  "It can, but that is a write against a live authentication flow and this script will not do it. Canceling is the right repair when a human decides it is; running it on a schedule means a background job racing a user who is still typing."),
],
"related": [
 ("/twilio/verify-max-send-attempts/", "A resend button with no cooldown burns five sends"),
 ("/twilio/verify-code-length-too-short/", "A Verify Service issuing four-digit codes"),
 ("/twilio/verify-conversion-rate-collapse/", "Verify conversion collapsing in one country"),
],
"citations": [CITE_60202, CITE_VERIFICATION, CITE_VSERVICE, CITE_KEYS],
},

{
"slug": "verify-max-send-attempts",
"title": "60203: a resend button with no cooldown burns five sends",
"description": "Verify allows five sends per verification. A resend with no cooldown, or a retry that treats slow SMS as failure, drains them in seconds and bills each one.",
"h1": "60203: a resend button with no cooldown burns five sends",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 60203", "max send attempts reached",
             "twilio verify send_code_attempts", "verify resend cooldown",
             "twilio verify duplicate sends"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "SMS took eleven seconds to arrive, so the user pressed Resend. Then again. Then once more, because the first three had not landed yet either &mdash; they had, all four of them, in a burst, several seconds after the fourth press. Now <code>60203</code> comes back, the button does nothing, and you have paid for four messages to deliver one code.",
"short_answer": """<p>Read <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VerificationSid}</code> and look at <code>send_code_attempts</code>. It is an array of <code>{channel, time, attempt_sid}</code>, one entry per send. Five entries means the budget is gone and the next resend returns <code>60203</code>; four while <code>status</code> is still <code>pending</code> means one tap away.</p>
<p>The count is the symptom. The spacing is the diagnosis: take the smallest gap between consecutive <code>time</code> values, and anything under about thirty seconds is not a person deciding the message has not arrived. It is a button with no cooldown, or a retry wrapper treating a slow send as a failed one.</p>""",
"problem": """<p>Every send in that burst succeeded. Twilio accepted each one, a carrier delivered each one, and each one is on the invoice. The only failure in the whole sequence is the fifth press, and by then the money is spent and the user is locked out of the flow they were trying to complete. This is the rare Verify problem where the error at the end is the cheapest part of the incident.</p>
<p>The reason it survives is that a resend button is trivially correct in testing. One tester, one tap, one code, works. It only misbehaves under the condition that produces real resends &mdash; SMS latency of five to twenty seconds, which no local test reproduces and no staging environment has. The behaviour that breaks is impatience, and impatience is not in the test plan.</p>
<p>The second producer is worse because nobody pressed anything: a server-side retry around the start call. Verify accepts the request, the response is slow, the HTTP client times out at three seconds, the wrapper retries, and Verify sends a second code for the same verification. Three retries and the budget is nearly gone before the first message has even been delivered.</p>""",
"why": """<p><strong>The send budget and the check budget are different limits with similar names.</strong> Five sends before <code>60203</code>, five checks before <code>60202</code>. They live on the same verification, they run down independently, and confusing them sends you looking at the wrong half of the client. The send count is visible in <code>send_code_attempts</code>; the check count is not exposed at all.</p>
<p><strong>The budget clears on a successful check, not on time.</strong> That inverts the intuition. A user who never enters a code carries the exhausted budget for the whole ten-minute lifetime, which is exactly the user who is pressing Resend. The people who trip this are the people it takes longest to release.</p>
<p><strong>The spacing separates a person from a loop, and only the spacing does.</strong> Four sends is four sends whether they arrived over two minutes or over four seconds. The first is a user in a bad coverage area, which is a product problem. The second is code firing on its own, which is a bug with a line number. The count alone cannot tell you which you have.</p>
<p><strong>Every attempt is billed at international OTP rates.</strong> A resend loop is not just a broken screen, it is a multiplier on the most expensive message you send. Two sends per verification across a signup funnel is the entire cost of the funnel, twice, for no additional verified users.</p>
<p><strong>The channel column hides a second cost.</strong> An escalation from <code>sms</code> to <code>call</code> is a legitimate design, and it still spends from the same five. A flow that auto-escalates after two failed SMS deliveries has a smaller budget than its author thinks, and reads as normal in every dashboard.</p>""",
"steps": [
 {"h": "Pick the verifications to look at",
  "body": """<p><code>GET https://verify.twilio.com/v2/Attempts?VerifyServiceSid={VA...}&amp;DateCreatedAfter={ISO8601}</code> lists sends, and each carries a <code>verification_sid</code>. A verification SID appearing several times in that list is already a candidate before you fetch anything.</p>"""},
 {"h": "Read send_code_attempts on each verification",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VerificationSid}</code>. The array holds one entry per send with its <code>channel</code> and <code>time</code>. Five entries is the exhausted state; four with <code>status</code> still <code>pending</code> is the one that is about to become a support ticket.</p>"""},
 {"h": "Measure the smallest gap between consecutive sends",
  "body": """<p>This is the step that turns a count into a diagnosis. Sort the <code>time</code> values, take consecutive differences, keep the minimum. Under about thirty seconds nobody has had time to check an inbox and decide the message is missing, so something other than a person issued that send.</p>"""},
 {"h": "Divide total sends by verifications to get the billing number",
  "body": """<p>One send per verification is the design. Anything above about 1.2 across a real window is a cost line, and it is the number to take to whoever owns the signup screen &mdash; more persuasive than any individual record, and it comes out of the same data.</p>"""},
 {"h": "Put a cooldown on the button and a guard on the retry",
  "body": """<p>Thirty to sixty seconds of disabled button with a visible countdown, and hard-stop the control at three presses. Make the start call non-retryable on timeout, because a slow response from Verify usually means the message is already on its way. A stuck verification can be closed with <code>POST https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VerificationSid}</code> and <code>Status=canceled</code>.</p>"""},
],
"verify": """<p>Re-run over the same window. Sends per verification should sit near one, and no verification should show a gap under the cooldown.</p>
<pre><code class="language-bash">python3 twilio_verify_send_attempts_audit.py --hours 24
# 412 verification(s), 431 send(s), 1.05 per verification, 0 under the cooldown</code></pre>""",
"code_intro": "Attempts to find the verifications, then one GET each to read <code>send_code_attempts</code> &mdash; read-only, so an API Key with read access is all it needs. The classifier is pure and takes the verification as the API returns it, because the interesting work is arithmetic on a list of timestamps and that is far easier to trust with tests around it than with a screenshot of a log.",
"py_file": "twilio_verify_send_attempts_audit.py",
"py": '''"""Report Verify verifications that burned their send budget on resends.

Five sends per verification, then 60203. A resend button with no cooldown, or a
retry wrapper treating a slow start call as a failed one, spends them in seconds
and bills every message.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_verify_send_attempts_audit")

VERIFY = "https://verify.twilio.com/v2"

# Fixed by the platform: the sixth send returns 60203, and the budget clears on a
# successful check rather than on a timer.
MAX_SENDS = 5

# Below this, nobody has had time to look at an inbox and decide the message is
# missing, so a person did not issue that send.
COOLDOWN_SECONDS = 30


def parse_time(value):
    """Parse a Verify timestamp into an aware datetime, or None.

    fromisoformat did not accept a trailing Z until 3.11 and every timestamp
    Verify returns has one.
    """
    s = str(value or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def gaps_seconds(send_code_attempts):
    """Seconds between consecutive sends, oldest first.

    Entries with an unreadable time drop out rather than poisoning the list: a
    verification with three good timestamps and one bad one still has two gaps
    worth reading.
    """
    times = sorted(t for t in (parse_time(a.get("time"))
                               for a in (send_code_attempts or []))
                   if t is not None)
    return [(times[i + 1] - times[i]).total_seconds() for i in range(len(times) - 1)]


def verdict(verification, cooldown=COOLDOWN_SECONDS, max_sends=MAX_SENDS):
    """Classify one verification by how its send budget was spent.

    Pure, so the spacing arithmetic can be tested without a network. Returns
    (state, detail).
    """
    sends = verification.get("send_code_attempts") or []
    status = str(verification.get("status") or "").strip().lower()
    n = len(sends)
    gaps = gaps_seconds(sends)
    fastest = min(gaps) if gaps else None

    channels = ", ".join(str(a.get("channel") or "?") for a in sends) or "none"
    tail = " %d send(s): %s." % (n, channels)
    if fastest is not None:
        tail += " Fastest gap %ds." % int(fastest)

    if n >= max_sends:
        return ("burned",
                "the %d send budget is spent, so the next resend returns 60203. "
                "It clears on a successful check, not on a timer, and the user "
                "pressing resend is the one who has not checked." % max_sends
                + tail)

    if n >= max_sends - 1 and status == "pending":
        return ("one-left",
                "one send from 60203 while the verification is still open."
                + tail)

    if fastest is not None and fastest < cooldown:
        return ("no-cooldown",
                "two sends %ds apart, inside the %ds a person needs to check an "
                "inbox and decide nothing arrived: something resent on its own."
                % (int(fastest), cooldown) + tail)

    if n <= 1:
        return ("ok", "one send, which is the design." if n else "no sends recorded.")

    return ("ok", "resends are spaced like a person pressing a button." + tail)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def page(session, url, field, **params):
    """Walk a Verify v2 list. Paging lives in meta.next_page_url."""
    out = []
    while url:
        body = get(session, url, **params) or {}
        out.extend(body.get(field, []))
        url, params = (body.get("meta") or {}).get("next_page_url"), {}
    return out


def verification_sids(session, service_sid, since, limit):
    """Distinct verification SIDs seen in the attempts list for a window.

    There is no list endpoint for verifications; the attempts list is the only
    read-only way to learn which ones existed.
    """
    seen, out = set(), []
    for attempt in page(session, VERIFY + "/Attempts", "attempts",
                        VerifyServiceSid=service_sid, DateCreatedAfter=since,
                        PageSize=100):
        sid = attempt.get("verification_sid")
        if sid and sid not in seen:
            seen.add(sid)
            out.append(sid)
            if len(out) >= limit:
                break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", action="append", default=[],
                    help="Verify Service SID; repeatable. Default: every service")
    ap.add_argument("--hours", type=int, default=24,
                    help="how far back to look for verifications")
    ap.add_argument("--max-verifications", type=int, default=500,
                    help="stop after this many per service")
    ap.add_argument("--cooldown", type=float, default=COOLDOWN_SECONDS,
                    help="seconds below which a gap is not a human resend")
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

    since = (datetime.now(timezone.utc) - timedelta(hours=args.hours)
             ).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.service:
        services = [{"sid": s, "friendly_name": s} for s in args.service]
    else:
        services = page(session, VERIFY + "/Services", "services", PageSize=50)
    if not services:
        log.info("no Verify services on this account")
        return 0

    inspected = total_sends = bad = 0
    for svc in services:
        sid = svc.get("sid")
        for ve in verification_sids(session, sid, since, args.max_verifications):
            body = get(session, "%s/Services/%s/Verifications/%s"
                       % (VERIFY, sid, ve))
            if body is None:
                # Soft deleted once approved, canceled or expired. The send
                # budget of a verification that resolved is not a finding.
                continue
            inspected += 1
            total_sends += len(body.get("send_code_attempts") or [])
            state, detail = verdict(body, args.cooldown)
            if state == "ok":
                continue
            bad += 1
            log.warning("%-12s %s  %s", state, ve, detail)
            if state in ("burned", "one-left"):
                log.warning("  repair: POST %s/Services/%s/Verifications/%s with "
                            "Status=canceled, then start a fresh verification",
                            VERIFY, sid, ve)
            log.warning("  and put a %ds cooldown on the resend control, with a "
                        "hard stop at three presses", int(args.cooldown))

    if not inspected:
        log.info("no verifications in the last %d hour(s)", args.hours)
        return 0

    per = float(total_sends) / inspected
    log.info("%d verification(s), %d send(s), %.2f per verification, %d over the "
             "budget or under the cooldown", inspected, total_sends, per, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-send-attempts-audit.mjs",
"js": '''/**
 * Report Verify verifications that burned their send budget on resends.
 *
 * Five sends per verification, then 60203. A resend button with no cooldown, or
 * a retry wrapper treating a slow start call as a failed one, spends them in
 * seconds and bills every message.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';

// Fixed by the platform: the sixth send returns 60203, and the budget clears on
// a successful check rather than on a timer.
export const MAX_SENDS = 5;

// Below this, nobody has had time to look at an inbox and decide the message is
// missing, so a person did not issue that send.
export const COOLDOWN_SECONDS = 30;

/** Parse a Verify timestamp into epoch milliseconds, or null. */
export function parseTime(value) {
  const s = String(value ?? '').trim();
  if (!s) return null;
  const ms = Date.parse(s);
  return Number.isFinite(ms) ? ms : null;
}

/**
 * Seconds between consecutive sends, oldest first. Entries with an unreadable
 * time drop out rather than poisoning the list.
 */
export function gapsSeconds(sendCodeAttempts) {
  const times = (sendCodeAttempts ?? [])
    .map((a) => parseTime(a.time))
    .filter((t) => t !== null)
    .sort((a, b) => a - b);
  const out = [];
  for (let i = 0; i + 1 < times.length; i += 1) {
    out.push((times[i + 1] - times[i]) / 1000);
  }
  return out;
}

/**
 * Classify one verification by how its send budget was spent. Pure, so the
 * spacing arithmetic can be tested without a network. Returns [state, detail].
 */
export function verdict(verification, cooldown = COOLDOWN_SECONDS,
                        maxSends = MAX_SENDS) {
  const sends = verification.send_code_attempts ?? [];
  const status = String(verification.status ?? '').trim().toLowerCase();
  const n = sends.length;
  const gaps = gapsSeconds(sends);
  const fastest = gaps.length ? Math.min(...gaps) : null;

  const channels = sends.map((a) => String(a.channel ?? '?')).join(', ') || 'none';
  let tail = ` ${n} send(s): ${channels}.`;
  if (fastest !== null) tail += ` Fastest gap ${Math.trunc(fastest)}s.`;

  if (n >= maxSends) {
    return ['burned',
      `the ${maxSends} send budget is spent, so the next resend returns 60203. ` +
      'It clears on a successful check, not on a timer, and the user pressing ' +
      `resend is the one who has not checked.${tail}`];
  }

  if (n >= maxSends - 1 && status === 'pending') {
    return ['one-left',
      `one send from 60203 while the verification is still open.${tail}`];
  }

  if (fastest !== null && fastest < cooldown) {
    return ['no-cooldown',
      `two sends ${Math.trunc(fastest)}s apart, inside the ${cooldown}s a ` +
      'person needs to check an inbox and decide nothing arrived: something ' +
      `resent on its own.${tail}`];
  }

  if (n <= 1) {
    return ['ok', n ? 'one send, which is the design.' : 'no sends recorded.'];
  }

  return ['ok', `resends are spaced like a person pressing a button.${tail}`];
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
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

/** Walk a Verify v2 list. Paging lives in meta.next_page_url. */
async function page(auth, url, field, params = {}) {
  const out = [];
  let next = url;
  let p = params;
  while (next) {
    const body = (await get(auth, next, p)) ?? {};
    out.push(...(body[field] ?? []));
    next = body.meta?.next_page_url ?? null;
    p = {};
  }
  return out;
}

/** Distinct verification SIDs seen in the attempts list for a window. */
export async function verificationSids(auth, serviceSid, since, limit) {
  const seen = new Set();
  const attempts = await page(auth, `${VERIFY}/Attempts`, 'attempts', {
    VerifyServiceSid: serviceSid, DateCreatedAfter: since, PageSize: 100,
  });
  for (const attempt of attempts) {
    if (attempt.verification_sid) seen.add(attempt.verification_sid);
    if (seen.size >= limit) break;
  }
  return [...seen];
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

  const hoursArg = process.argv.indexOf('--hours');
  const hours = hoursArg === -1 ? 24 : Number(process.argv[hoursArg + 1]) || 24;
  const since = `${new Date(Date.now() - hours * 3600 * 1000)
    .toISOString().slice(0, 19)}Z`;

  const services = await page(auth, `${VERIFY}/Services`, 'services', { PageSize: 50 });
  if (services.length === 0) {
    console.log('no Verify services on this account');
    return;
  }

  let inspected = 0;
  let totalSends = 0;
  let bad = 0;
  for (const svc of services) {
    for (const ve of await verificationSids(auth, svc.sid, since, 500)) {
      const body = await get(auth, `${VERIFY}/Services/${svc.sid}/Verifications/${ve}`);
      // Soft deleted once approved, canceled or expired. The send budget of a
      // verification that resolved is not a finding.
      if (body === null) continue;
      inspected += 1;
      totalSends += (body.send_code_attempts ?? []).length;
      const [state, detail] = verdict(body);
      if (state === 'ok') continue;
      bad += 1;
      console.warn(`${state.padEnd(12)} ${ve}  ${detail}`);
      if (state === 'burned' || state === 'one-left') {
        console.warn(`  repair: POST ${VERIFY}/Services/${svc.sid}/Verifications/` +
                     `${ve} with Status=canceled, then start a fresh verification`);
      }
      console.warn(`  and put a ${COOLDOWN_SECONDS}s cooldown on the resend ` +
                   'control, with a hard stop at three presses');
    }
  }

  if (inspected === 0) {
    console.log(`no verifications in the last ${hours} hour(s)`);
    return;
  }

  const per = totalSends / inspected;
  console.log(`${inspected} verification(s), ${totalSends} send(s), ` +
              `${per.toFixed(2)} per verification, ${bad} over the budget or ` +
              'under the cooldown');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The count is the easy half. The tests that earn their place are the spacing ones: three sends four seconds apart has to come back as a machine even though the budget is not spent, and three sends two minutes apart has to come back clean even though it is the same count. The last test pins that a broken timestamp costs you one gap rather than the whole verification.",
"test_py_file": "test_twilio_verify_send_attempts_audit.py",
"test_py": '''from twilio_verify_send_attempts_audit import gaps_seconds, verdict


def at(second, channel="sms"):
    return {"channel": channel,
            "time": "2026-03-04T12:%02d:%02dZ" % divmod(second, 60)}


def test_five_sends_is_the_exhausted_budget():
    state, detail = verdict({"send_code_attempts": [at(s * 40) for s in range(5)],
                             "status": "pending"})
    assert state == "burned"
    assert "60203" in detail


def test_four_sends_while_pending_is_one_tap_away():
    state, detail = verdict({"send_code_attempts": [at(s * 40) for s in range(4)],
                             "status": "pending"})
    assert state == "one-left"
    assert "still open" in detail


def test_three_sends_seconds_apart_is_a_machine_not_a_person():
    state, detail = verdict({"send_code_attempts": [at(0), at(4), at(9)],
                             "status": "pending"})
    assert state == "no-cooldown"
    assert "Fastest gap 4s" in detail


def test_the_same_count_spaced_like_a_human_is_fine():
    state, _ = verdict({"send_code_attempts": [at(0), at(45), at(95)],
                        "status": "pending"})
    assert state == "ok"


def test_a_channel_escalation_still_spends_from_the_same_budget():
    state, detail = verdict({"send_code_attempts": [at(0), at(60, "call")],
                             "status": "pending"})
    assert state == "ok"
    assert "sms, call" in detail


def test_one_send_is_the_design():
    assert verdict({"send_code_attempts": [at(0)], "status": "pending"})[0] == "ok"
    assert verdict({"status": "pending"})[0] == "ok"


def test_an_unreadable_timestamp_costs_one_gap_not_the_verification():
    sends = [at(0), {"channel": "sms", "time": "whenever"}, at(4)]
    assert gaps_seconds(sends) == [4.0]
    assert verdict({"send_code_attempts": sends, "status": "pending"})[0] == "no-cooldown"
''',
"test_js_file": "twilio-verify-send-attempts-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { gapsSeconds, verdict } from './twilio-verify-send-attempts-audit.mjs';

const BASE = Date.parse('2026-03-04T12:00:00Z');
const at = (second, channel = 'sms') => ({
  channel,
  time: `${new Date(BASE + second * 1000).toISOString().slice(0, 19)}Z`,
});

test('five sends is the exhausted budget', () => {
  const sends = [0, 40, 80, 120, 160].map((s) => at(s));
  const [state, detail] = verdict({ send_code_attempts: sends, status: 'pending' });
  assert.equal(state, 'burned');
  assert.match(detail, /60203/);
});

test('four sends while pending is one tap away', () => {
  const sends = [at(0), at(40), at(80), at(120)];
  const [state, detail] = verdict({ send_code_attempts: sends, status: 'pending' });
  assert.equal(state, 'one-left');
  assert.match(detail, /still open/);
});

test('three sends seconds apart is a machine not a person', () => {
  const [state, detail] = verdict({
    send_code_attempts: [at(0), at(4), at(9)], status: 'pending' });
  assert.equal(state, 'no-cooldown');
  assert.match(detail, /Fastest gap 4s/);
});

test('the same count spaced like a human is fine', () => {
  const [state] = verdict({
    send_code_attempts: [at(0), at(45), at(95)], status: 'pending' });
  assert.equal(state, 'ok');
});

test('a channel escalation still spends from the same budget', () => {
  const [state, detail] = verdict({
    send_code_attempts: [at(0), at(60, 'call')], status: 'pending' });
  assert.equal(state, 'ok');
  assert.match(detail, /sms, call/);
});

test('one send is the design', () => {
  assert.equal(verdict({ send_code_attempts: [at(0)], status: 'pending' })[0], 'ok');
  assert.equal(verdict({ status: 'pending' })[0], 'ok');
});

test('an unreadable timestamp costs one gap not the verification', () => {
  const sends = [at(0), { channel: 'sms', time: 'whenever' }, at(4)];
  assert.deepEqual(gapsSeconds(sends), [4]);
  assert.equal(
    verdict({ send_code_attempts: sends, status: 'pending' })[0], 'no-cooldown');
});
''',
"faq": [
 ("How is 60203 different from 60202?",
  "60203 is the send budget: five codes issued for one verification. 60202 is the check budget: five guesses at the code. They sit on the same verification and run down independently, and mixing them up sends you to the wrong half of the client, because the send count is visible in the API and the check count is not."),
 ("Does waiting clear the send budget?",
  "No. It clears on a successful check, or when the verification expires and you start a new one. Waiting is exactly what the user who tripped it will not do, which is why the flow needs a path to a fresh verification rather than a longer spinner."),
 ("Why judge the spacing rather than just the count?",
  "Because four sends over three minutes is a person in bad coverage and four sends over six seconds is code. The count is identical and the fix is completely different: one is a product decision about escalation, the other is a line in a handler that should not be there."),
 ("Is a channel escalation from SMS to voice a problem?",
  "No, it is a good design, but it spends from the same five. A flow that escalates automatically after two SMS attempts has three sends left before 60203, not five, and the report names the channels so that arithmetic is visible rather than assumed."),
 ("Can the script cancel the stuck verifications it finds?",
  "It will not. Canceling is a write against a live authentication attempt, and this script holds a credential to an account that can spend money. It prints the exact call, with the Service SID and the verification SID, for a human to run."),
],
"related": [
 ("/twilio/verify-max-check-attempts/", "A verification that burned all five checks"),
 ("/twilio/verify-no-rate-limits/", "A Verify Service with zero rate limits configured"),
 ("/twilio/verify-sms-to-landline/", "Verify sending SMS to a line that cannot receive it"),
],
"citations": [CITE_60203, CITE_VERIFICATION, CITE_VSERVICE, CITE_KEYS],
},

{
"slug": "verify-do-not-share-warning-off",
"title": "OTP codes sent without the do-not-share warning line",
"description": "do_not_share_warning_enabled is off by default, so the SMS is a bare code. A custom default template can drop the line even when the flag is on.",
"h1": "OTP codes sent without the do-not-share warning line",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["do_not_share_warning_enabled", "twilio verify otp warning",
             "twilio verify dtmf_input_required", "otp phishing warning sms",
             "verify default_template_sid"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody phoned your customer, said they were from your support team, told them there was a suspicious login and that a code was on its way to confirm it was really them. The code arrived, on time, from your number, saying nothing except what the code was. The customer read it out. Nothing in that message gave them a reason not to.",
"short_answer": """<p>Read <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}</code> and flag <code>do_not_share_warning_enabled == false</code>. That flag appends a security warning to the SMS verification body, and it is off by default, so every Service created without it sends codes with no caution line.</p>
<p>Then read <code>default_template_sid</code> in the same response. The flag appends to Twilio's default body; a custom default template carries whatever text it was approved with, and the warning may not be in it. Cross-reference <code>GET https://verify.twilio.com/v2/Templates</code>. For voice, <code>dtmf_input_required == false</code> means a voicemail box that answers the call gets read the code.</p>""",
"problem": """<p>The attack this defends against does not touch your infrastructure at all. Nothing is compromised, no credential leaks, no request is malformed. Somebody talks a customer into reading out a number, and the number works, because it is a valid code delivered to the right handset at the right moment. Every log line for that session says the verification succeeded, which it did.</p>
<p>The single line of text is a small defence and it is a real one, because it arrives at the exact moment of the decision. The caller is on the phone saying they are from your support team; the message in the customer's hand says nobody from your support team will ever ask for this. That contradiction, delivered in the same second, is most of what stops the call.</p>
<p>It is missing for the most ordinary reason there is: it defaults to off, and turning it on was never a task on anybody's list. The Service was created through the API during the integration, with the fields the quickstart used, and the fields the quickstart did not mention have been at their defaults ever since.</p>""",
"why": """<p><strong>The flag is off by default, so nobody chose the current state.</strong> A Service created through the API gets whatever the create call did not set, and no quickstart sets this. There is no migration, no deprecation notice, and no console warning; the setting simply stays where it was born, which for most accounts is off.</p>
<p><strong>The warning is appended to Twilio's default body, not to yours.</strong> Set <code>default_template_sid</code> to a custom template and the body is now whatever that template says. The flag can be <code>true</code> in the API while the message going out has no warning in it, which is the one state a boolean check reports as safe and is not.</p>
<p><strong>Nobody reads their own OTP messages.</strong> The team receives the code in a test, types it in, and confirms the flow works. Reading the sentence around the digits is not part of confirming the flow works, so a body with no caution line passes every test anyone runs against it.</p>
<p><strong>The voice channel has its own version of the same gap.</strong> <code>dtmf_input_required</code> makes the call wait for a keypress before reading the code. With it off, a voicemail box answers, hears the code, and stores it as an audio recording in a mailbox protected by a four-digit PIN. It is off by default too.</p>
<p><strong>Templates are a per-account resource and services are not.</strong> The template list lives at the account level while the reference lives on each Service, so the two have to be joined to say anything. A Service pointing at a template your key cannot see is a real state, and the honest answer there is unresolved rather than either verdict.</p>""",
"steps": [
 {"h": "Read the flag on every Service",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services</code> and read <code>do_not_share_warning_enabled</code>. False is the headline finding and it is one boolean. Do it across every Service, because the one created most recently is usually the one somebody configured properly and the old one is still carrying production.</p>"""},
 {"h": "Join the default template before trusting a true",
  "body": """<p><code>GET https://verify.twilio.com/v2/Templates</code> once, keyed by <code>sid</code>. If a Service sets <code>default_template_sid</code>, the flag is not the whole story: the body is the template's, and the warning line is in it or it is not. Report that as needing a human read rather than as passing.</p>"""},
 {"h": "Handle a template you cannot resolve as unknown",
  "body": """<p>A <code>default_template_sid</code> that is not in the list the key can read is not evidence of anything. Give it its own state. Reporting it as covered hides a real gap; reporting it as broken sends somebody to look at a template that is probably fine.</p>"""},
 {"h": "Check the voice channel separately, and only if you use it",
  "body": """<p><code>dtmf_input_required</code> matters when you send <code>Channel=call</code>. One paginated <code>GET https://verify.twilio.com/v2/Attempts?VerifyServiceSid={VA...}&amp;DateCreatedAfter={ISO8601}</code> tells you whether any attempt used the call channel, which is the difference between a finding and a footnote.</p>"""},
 {"h": "Turn both on, then read the message on a real handset",
  "body": """<p><code>POST https://verify.twilio.com/v2/Services/{ServiceSid}</code> with <code>DoNotShareWarningEnabled=true</code> and <code>DtmfInputRequired=true</code>. If a custom template is in play, resubmit it with the warning line included and wait for approval. Then send yourself one and read it, because that is the check the flag cannot do for you.</p>"""},
],
"verify": """<p>Re-run the script. Every Service should report <code>warned</code>, with no custom template left unread.</p>
<pre><code class="language-bash">python3 twilio_verify_warning_audit.py --check-voice
# 3 service(s), 0 sending codes without a warning</code></pre>""",
"code_intro": "One GET for the Services, one for the account's Templates, and with <code>--check-voice</code> one paginated GET of the attempts per Service to find out whether the voice channel is in use at all &mdash; read-only throughout. The classifier is pure and takes the templates as a map, because the interesting rule is that a <code>true</code> flag plus a custom template is not a pass, and that is the sentence the whole note exists to make testable.",
"py_file": "twilio_verify_warning_audit.py",
"py": '''"""Report Verify Services sending OTP codes with no do-not-share warning.

do_not_share_warning_enabled appends a security warning to the SMS body and is
off by default. It appends to Twilio's default body, so a Service with a custom
default template can have the flag on and still send a bare code.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_verify_warning_audit")

VERIFY = "https://verify.twilio.com/v2"


def verdict(service, templates_by_sid, voice_in_use=None):
    """Classify one Verify Service by whether its codes carry a warning.

    `templates_by_sid` is the account's Templates keyed on sid. `voice_in_use` is
    True, False, or None when it was not checked -- the three cases produce three
    different answers about dtmf_input_required, and collapsing them into a
    boolean is how an audit starts inventing findings.

    Pure, so the rule that a true flag plus a custom template is not a pass can
    be tested without a network. Returns (state, detail).
    """
    warned = bool(service.get("do_not_share_warning_enabled"))
    dtmf = bool(service.get("dtmf_input_required"))
    template_sid = str(service.get("default_template_sid") or "").strip()

    voice_note = ""
    if not dtmf and voice_in_use is True:
        voice_note = (" dtmf_input_required is false and this service sends voice "
                      "verifications: a voicemail box answering the call is read "
                      "the code and keeps it.")
    elif not dtmf and voice_in_use is None:
        voice_note = (" dtmf_input_required is false; if you ever send "
                      "Channel=call, a voicemail box can capture the code.")

    if not warned:
        return ("no-warning",
                "do_not_share_warning_enabled is false: the SMS body is the code "
                "and nothing else, with no line saying that nobody legitimate "
                "will ask for it." + voice_note)

    if template_sid:
        template = templates_by_sid.get(template_sid)
        if template is None:
            return ("unresolved-template",
                    "the flag is true, but default_template_sid %s is not in the "
                    "Templates this key can read, and the body comes from the "
                    "template. Unknown, not covered." % template_sid + voice_note)
        return ("custom-template",
                "the flag is true, but the Service sends a custom default "
                "template (%s, %s) and the flag appends to Twilio's default body. "
                "Read the translations before calling this covered."
                % (template_sid, template.get("friendly_name") or "unnamed")
                + voice_note)

    if not dtmf and voice_in_use is True:
        return ("voice-exposed",
                "the SMS body carries the warning, but" + voice_note)

    return ("warned",
            "do_not_share_warning_enabled is true and the built-in default "
            "template is in use." + voice_note)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page(session, url, field, **params):
    """Walk a Verify v2 list. Paging lives in meta.next_page_url."""
    out = []
    while url:
        body = get(session, url, **params)
        out.extend(body.get(field, []))
        url, params = (body.get("meta") or {}).get("next_page_url"), {}
    return out


def voice_used(session, service_sid, since):
    """True when any attempt in the window used the call channel."""
    for attempt in page(session, VERIFY + "/Attempts", "attempts",
                        VerifyServiceSid=service_sid, DateCreatedAfter=since,
                        PageSize=100):
        if str(attempt.get("channel") or "").lower() == "call":
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-voice", action="store_true",
                    help="one paginated GET per service to see if voice is used")
    ap.add_argument("--hours", type=int, default=168,
                    help="window for the voice channel check")
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

    services = page(session, VERIFY + "/Services", "services", PageSize=50)
    if not services:
        log.info("no Verify services on this account")
        return 0

    templates = {t.get("sid"): t
                 for t in page(session, VERIFY + "/Templates", "templates",
                               PageSize=50)}
    since = (datetime.now(timezone.utc) - timedelta(hours=args.hours)
             ).strftime("%Y-%m-%dT%H:%M:%SZ")

    bad = 0
    for svc in services:
        sid = svc.get("sid")
        voice = voice_used(session, sid, since) if args.check_voice else None
        state, detail = verdict(svc, templates, voice)
        line = "%-19s %s (%s)  %s" % (state, svc.get("friendly_name", "?"),
                                      sid, detail)
        if state == "warned":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: POST %s/Services/%s with "
                    "DoNotShareWarningEnabled=true and DtmfInputRequired=true",
                    VERIFY, sid)
        if state in ("custom-template", "unresolved-template"):
            log.warning("  and read the template body: the flag appends to "
                        "Twilio's default, not to yours")

    log.info("%d service(s), %d sending codes without a warning",
             len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-warning-audit.mjs",
"js": '''/**
 * Report Verify Services sending OTP codes with no do-not-share warning.
 *
 * do_not_share_warning_enabled appends a security warning to the SMS body and
 * is off by default. It appends to the default body, so a Service with a custom
 * default template can have the flag on and still send a bare code.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';

/**
 * Classify one Verify Service by whether its codes carry a warning.
 *
 * `templatesBySid` is the account Templates keyed on sid. `voiceInUse` is true,
 * false, or null when it was not checked: the three cases produce three
 * different answers about dtmf_input_required, and collapsing them into a
 * boolean is how an audit starts inventing findings.
 *
 * Pure, so the rule that a true flag plus a custom template is not a pass can
 * be tested without a network. Returns [state, detail].
 */
export function verdict(service, templatesBySid, voiceInUse = null) {
  const warned = Boolean(service.do_not_share_warning_enabled);
  const dtmf = Boolean(service.dtmf_input_required);
  const templateSid = String(service.default_template_sid ?? '').trim();

  let voiceNote = '';
  if (!dtmf && voiceInUse === true) {
    voiceNote = ' dtmf_input_required is false and this service sends voice ' +
      'verifications: a voicemail box answering the call is read the code and ' +
      'keeps it.';
  } else if (!dtmf && voiceInUse === null) {
    voiceNote = ' dtmf_input_required is false; if you ever send Channel=call, ' +
      'a voicemail box can capture the code.';
  }

  if (!warned) {
    return ['no-warning',
      'do_not_share_warning_enabled is false: the SMS body is the code and ' +
      'nothing else, with no line saying that nobody legitimate will ask for ' +
      `it.${voiceNote}`];
  }

  if (templateSid) {
    const template = templatesBySid.get
      ? templatesBySid.get(templateSid)
      : templatesBySid[templateSid];
    if (template === undefined || template === null) {
      return ['unresolved-template',
        `the flag is true, but default_template_sid ${templateSid} is not in ` +
        'the Templates this key can read, and the body comes from the ' +
        `template. Unknown, not covered.${voiceNote}`];
    }
    return ['custom-template',
      'the flag is true, but the Service sends a custom default template ' +
      `(${templateSid}, ${template.friendly_name || 'unnamed'}) and the flag ` +
      'appends to the default body. Read the translations before calling this ' +
      `covered.${voiceNote}`];
  }

  if (!dtmf && voiceInUse === true) {
    return ['voice-exposed', `the SMS body carries the warning, but${voiceNote}`];
  }

  return ['warned',
    'do_not_share_warning_enabled is true and the built-in default template is ' +
    `in use.${voiceNote}`];
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

/** Walk a Verify v2 list. Paging lives in meta.next_page_url. */
async function page(auth, url, field, params = {}) {
  const out = [];
  let next = url;
  let p = params;
  while (next) {
    const body = await get(auth, next, p);
    out.push(...(body[field] ?? []));
    next = body.meta?.next_page_url ?? null;
    p = {};
  }
  return out;
}

/** True when any attempt in the window used the call channel. */
export async function voiceUsed(auth, serviceSid, since) {
  const attempts = await page(auth, `${VERIFY}/Attempts`, 'attempts', {
    VerifyServiceSid: serviceSid, DateCreatedAfter: since, PageSize: 100,
  });
  return attempts.some((a) => String(a.channel ?? '').toLowerCase() === 'call');
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
  const checkVoice = process.argv.includes('--check-voice');

  const services = await page(auth, `${VERIFY}/Services`, 'services', { PageSize: 50 });
  if (services.length === 0) {
    console.log('no Verify services on this account');
    return;
  }

  const templates = new Map();
  for (const t of await page(auth, `${VERIFY}/Templates`, 'templates', { PageSize: 50 })) {
    templates.set(t.sid, t);
  }
  const since = `${new Date(Date.now() - 168 * 3600 * 1000)
    .toISOString().slice(0, 19)}Z`;

  let bad = 0;
  for (const svc of services) {
    const voice = checkVoice ? await voiceUsed(auth, svc.sid, since) : null;
    const [state, detail] = verdict(svc, templates, voice);
    const line = `${state.padEnd(19)} ${svc.friendly_name ?? '?'} (${svc.sid})  ${detail}`;
    if (state === 'warned') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: POST ${VERIFY}/Services/${svc.sid} with ` +
                 'DoNotShareWarningEnabled=true and DtmfInputRequired=true');
    if (state === 'custom-template' || state === 'unresolved-template') {
      console.warn('  and read the template body: the flag appends to the ' +
                   'built-in default, not to yours');
    }
  }

  console.log(`${services.length} service(s), ${bad} sending codes without a warning`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "One boolean would make this a three-line script, and the tests are here to stop it being one. A <code>true</code> flag with a custom default template must not come back as a pass; a template SID the key cannot resolve must come back as unknown rather than as either verdict; and <code>dtmf_input_required</code> must only become a finding when the voice channel is actually in use, because the value of an audit is that its warnings are all real.",
"test_py_file": "test_twilio_verify_warning_audit.py",
"test_py": '''from twilio_verify_warning_audit import verdict

TEMPLATES = {"HJ0123456789": {"sid": "HJ0123456789", "friendly_name": "signup v3"}}


def test_the_flag_off_is_the_headline_finding():
    state, detail = verdict({"do_not_share_warning_enabled": False,
                             "dtmf_input_required": True}, {})
    assert state == "no-warning"
    assert "nothing else" in detail


def test_a_custom_template_is_not_a_pass_even_with_the_flag_on():
    state, detail = verdict({"do_not_share_warning_enabled": True,
                             "dtmf_input_required": True,
                             "default_template_sid": "HJ0123456789"}, TEMPLATES)
    assert state == "custom-template"
    assert "signup v3" in detail


def test_a_template_the_key_cannot_read_is_unknown_not_broken():
    state, detail = verdict({"do_not_share_warning_enabled": True,
                             "dtmf_input_required": True,
                             "default_template_sid": "HJ9999999999"}, TEMPLATES)
    assert state == "unresolved-template"
    assert "Unknown, not covered" in detail


def test_the_default_template_with_the_flag_on_passes():
    state, _ = verdict({"do_not_share_warning_enabled": True,
                        "dtmf_input_required": True}, TEMPLATES)
    assert state == "warned"


def test_dtmf_is_only_a_finding_when_voice_is_actually_used():
    exposed, detail = verdict({"do_not_share_warning_enabled": True,
                               "dtmf_input_required": False}, {}, voice_in_use=True)
    assert exposed == "voice-exposed"
    assert "voicemail box" in detail
    assert verdict({"do_not_share_warning_enabled": True,
                    "dtmf_input_required": False}, {}, voice_in_use=False)[0] == "warned"


def test_an_unchecked_voice_channel_is_a_note_not_a_verdict():
    state, detail = verdict({"do_not_share_warning_enabled": True,
                             "dtmf_input_required": False}, {})
    assert state == "warned"
    assert "if you ever send" in detail


def test_a_missing_flag_reads_as_off():
    assert verdict({}, {})[0] == "no-warning"
''',
"test_js_file": "twilio-verify-warning-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './twilio-verify-warning-audit.mjs';

const TEMPLATES = new Map([
  ['HJ0123456789', { sid: 'HJ0123456789', friendly_name: 'signup v3' }],
]);

test('the flag off is the headline finding', () => {
  const [state, detail] = verdict(
    { do_not_share_warning_enabled: false, dtmf_input_required: true }, new Map());
  assert.equal(state, 'no-warning');
  assert.match(detail, /nothing else/);
});

test('a custom template is not a pass even with the flag on', () => {
  const [state, detail] = verdict({
    do_not_share_warning_enabled: true,
    dtmf_input_required: true,
    default_template_sid: 'HJ0123456789',
  }, TEMPLATES);
  assert.equal(state, 'custom-template');
  assert.match(detail, /signup v3/);
});

test('a template the key cannot read is unknown not broken', () => {
  const [state, detail] = verdict({
    do_not_share_warning_enabled: true,
    dtmf_input_required: true,
    default_template_sid: 'HJ9999999999',
  }, TEMPLATES);
  assert.equal(state, 'unresolved-template');
  assert.match(detail, /Unknown, not covered/);
});

test('the default template with the flag on passes', () => {
  const [state] = verdict(
    { do_not_share_warning_enabled: true, dtmf_input_required: true }, TEMPLATES);
  assert.equal(state, 'warned');
});

test('dtmf is only a finding when voice is actually used', () => {
  const [state, detail] = verdict(
    { do_not_share_warning_enabled: true, dtmf_input_required: false },
    new Map(), true);
  assert.equal(state, 'voice-exposed');
  assert.match(detail, /voicemail box/);
  assert.equal(verdict(
    { do_not_share_warning_enabled: true, dtmf_input_required: false },
    new Map(), false)[0], 'warned');
});

test('an unchecked voice channel is a note not a verdict', () => {
  const [state, detail] = verdict(
    { do_not_share_warning_enabled: true, dtmf_input_required: false }, new Map());
  assert.equal(state, 'warned');
  assert.match(detail, /if you ever send/);
});

test('a missing flag reads as off', () => {
  assert.equal(verdict({}, new Map())[0], 'no-warning');
});
''',
"faq": [
 ("Does one line of text really stop anything?",
  "It stops the specific attack it is aimed at, which is a person on the phone asking for the code. The warning arrives in the same second as the request and contradicts it directly. It does nothing against a compromised handset or an intercepted message, and it was never meant to."),
 ("The flag is true. Why is my Service still flagged?",
  "Because you have a custom default_template_sid. The flag appends the warning to the built-in body; a custom template sends whatever text it was approved with. The flag and the body are two different things, and only reading the template settles it."),
 ("What if the script cannot see the template?",
  "It reports unresolved rather than guessing. A template SID that is not in the list your key can read is missing information, not evidence. Calling it covered would hide a gap and calling it broken would send somebody to review a template that is probably correct."),
 ("What does dtmf_input_required have to do with this?",
  "It is the same problem on the voice channel. Without it, the call reads the code out to whatever answers, including a voicemail box, which then stores it as a recording behind a PIN. The script only raises it when the attempts show the call channel actually in use."),
 ("Can I write my own warning wording?",
  "Yes, through a template, and that is the state this script asks you to read rather than trust. Custom wording is often better than the default because it can name your brand. It is only a problem when the customisation quietly dropped the caution line on its way through review."),
],
"related": [
 ("/twilio/verify-code-length-too-short/", "A Verify Service issuing four-digit codes"),
 ("/twilio/verify-sms-to-landline/", "Verify sending SMS to a line that cannot receive it"),
 ("/twilio/verify-conversion-rate-collapse/", "Verify conversion collapsing in one country"),
],
"citations": [CITE_VSERVICE, CITE_TEMPLATES, CITE_VERIFICATION, CITE_KEYS],
},

]
