#!/usr/bin/env python3
"""/twilio/ field notes, batch Z — the writing.

Five late entries in the A2P and toll-free enumeration, each one a clock or a
ceiling rather than a rejection. Nothing here throws at submit time: a passcode
window closes, a pool holds one number more than the brand allows, a carrier
counts segments somewhere you cannot see, an edit window lapses, a certificate
expires. All of them are readable with an API Key that has read access, and none
of the scripts writes.
"""

CITE_BRAND = ("Brand Registration resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/brand-registration-resource")
CITE_SOLE_PROP = ("Sole Proprietor A2P registration through the API — Twilio Docs",
                  "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/"
                  "onboarding-isv-api-sole-prop-new")
CITE_USA2P = ("UsAppToPerson resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/usapptoperson-resource")
CITE_30034 = ("Error 30034: message from an unregistered number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30034")
CITE_FIX_NUMBERS = ("Troubleshooting A2P phone number registration — Twilio Docs",
                    "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/"
                    "troubleshooting-a2p-brands/"
                    "troubleshooting-a2p-phone-number-registration-issues")
CITE_MSPN = ("Messaging Service PhoneNumber resource — Twilio Docs",
             "https://www.twilio.com/docs/messaging/api/phonenumber-resource")
CITE_30023 = ("Error 30023: daily message cap reached — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30023")
CITE_MSG = ("Message resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_TFV = ("Toll-Free Verification resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/tollfree-verification-resource")
CITE_30032 = ("Error 30032: toll-free number has not been verified — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30032")
CITE_TF_VERIFY = ("Toll-free message verification — Twilio Docs",
                  "https://www.twilio.com/docs/messaging/compliance/"
                  "toll-free-message-verification")
CITE_LINKS = ("Link Shortening onboarding guide — Twilio Docs",
              "https://www.twilio.com/docs/messaging/features/link-shortening/"
              "onboarding-guide")
CITE_30120 = ("Error 30120: link shortening delivery failure — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30120")
CITE_30131 = ("Error 30131: link shortening domain warning — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30131")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "sole-prop-otp-never-accepted",
"title": "A Sole Proprietor brand blocked by an OTP nobody answered",
"description": "The brand never rises to VERIFIED because the owner never replied to the SMS passcode. The reply window is 24 hours and nothing tells you it closed.",
"h1": "a Sole Proprietor brand blocked by an OTP nobody answered",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio sole proprietor brand otp", "sole prop identity_status unverified",
             "brand_registration_otps", "sole proprietor 10dlc verification failed",
             "twilio sole prop 30034"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The registration went in. Somewhere a phone buzzed with a passcode and a message about a business the owner had half forgotten agreeing to. They did not reply, or they replied on Thursday to a code that expired on Wednesday. <code>identity_status</code> is still <code>SELF_DECLARED</code>, the campaign underneath cannot register, and every US message is coming back <code>30034</code> for a reason nobody in your building can see.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code>, keep the rows where <code>brand_type</code> is <code>SOLE_PROPRIETOR</code>, and flag any whose <code>identity_status</code> is below <code>VERIFIED</code> while <code>date_created</code> is more than 24 hours old. That combination is a passcode that was sent and never answered.</p>
<p><code>identity_status</code> runs <code>SELF_DECLARED</code>, <code>UNVERIFIED</code>, <code>VERIFIED</code>, <code>VETTED_VERIFIED</code>. Only the last two mean the handset replied. <code>links.brand_registration_otps</code> on the same resource tells you the passcode subresource exists at all.</p>""",
"problem": """<p>A Sole Proprietor registration puts a step in the middle of your onboarding that you cannot perform and cannot observe: a text goes to the owner's personal mobile and they have to reply to it, from that handset, within 24 hours. Your onboarding flow has no callback for "the customer ignored a text message". The brand does not fail. It simply stops being about you.</p>
<p>What makes it expensive is that the brand's own <code>status</code> can read <code>APPROVED</code> while <code>identity_status</code> sits at <code>SELF_DECLARED</code>. Somebody checks the field they know about, sees the word approved, and enables US sending. The campaign underneath never reaches a state where numbers register, and the whole account returns <code>30034</code> on a brand that looks fine in the console list view.</p>""",
"why": """<p><strong>The 24 hour window is not surfaced anywhere you would look.</strong> There is no <code>otp_expires_at</code> to read and no alert when it lapses. The only observable is the pair of fields: an <code>identity_status</code> that has not moved and a <code>date_created</code> that keeps getting older. Aging the brand is the whole detection.</p>
<p><strong>The handset has a lifetime quota you did not know about.</strong> A mobile can back at most three A2P brand registrations across the whole registry, including registrations made through other vendors entirely. A support-desk habit of putting the agency owner's mobile on every client brand burns that quota silently, and the fourth registration cannot be rescued by re-sending anything.</p>
<p><strong>CPaaS numbers are rejected without saying so.</strong> The registered mobile has to be a real US or Canadian handset. A Twilio number, or any other virtual number the customer happened to have handy, will not carry the passcode, and the failure looks identical to a customer who ignored the text.</p>
<p><strong>Nobody owns the step.</strong> Your side submitted it, so your side thinks it is done. The customer received a text from a shortcode about compliance, so they think it is spam. The registration sits between two parties who both believe it belongs to the other one, which is exactly the shape of a problem that needs a scheduled read rather than a memory.</p>""",
"steps": [
 {"h": "List the brands and keep only the Sole Proprietor ones",
  "body": """<p><code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code>, following <code>meta.next_page_url</code>. Filter on <code>brand_type == "SOLE_PROPRIETOR"</code>. Standard and Low-Volume Standard brands prove identity through the customer profile and never send a passcode, so including them only produces noise.</p>"""},
 {"h": "Read identity_status, not status",
  "body": """<p><code>status</code> describes the registration; <code>identity_status</code> describes whether the human answered. They move independently, and an <code>APPROVED</code> brand with <code>identity_status</code> of <code>SELF_DECLARED</code> is the case that ships to production. Treat only <code>VERIFIED</code> and <code>VETTED_VERIFIED</code> as answered.</p>"""},
 {"h": "Age the brand against the 24 hour reply window",
  "body": """<p><code>date_created</code> arrives as ISO 8601 with a trailing <code>Z</code>, which <code>datetime.fromisoformat</code> would not accept before Python 3.11. Under 24 hours old with an unverified identity is a passcode in flight and not yet a finding. Past 24 hours it has expired unanswered.</p>"""},
 {"h": "Confirm a passcode was ever raised",
  "body": """<p><code>links.brand_registration_otps</code> is the subresource for the passcodes on this brand. Its absence on an unverified Sole Proprietor brand means the registration is not simply waiting on a reply, so re-sending is not the first thing to do; look at how the brand was submitted.</p>"""},
 {"h": "Print the re-send, and the case where re-sending cannot help",
  "body": """<p>The repair is <code>POST /v1/a2p/BrandRegistrations/{BrandSid}/SmsOtp</code> to raise a fresh passcode, then a human asking the owner to reply from that handset within 24 hours. If the mobile has already backed three registrations anywhere in the registry, or is not a real US or Canadian handset, no re-send will land and the profile has to be refiled with a different number.</p>"""},
],
"verify": """<p>Re-run the script. Every Sole Proprietor brand should report <code>verified</code>, and nothing should be sitting past the reply window.</p>
<pre><code class="language-bash">python3 twilio_sole_prop_otp_audit.py
# 12 brand(s), 3 sole proprietor, 0 waiting on a passcode</code></pre>""",
"code_intro": "One paginated GET over the brand registrations and nothing else. The clock stays out of the classifier: <code>verdict()</code> takes an age in hours, so the boundary at 24 and the states either side of it are ordinary tests rather than something that needs time frozen. An API Key with read access is enough; the passcode re-send is printed, never sent.",
"py_file": "twilio_sole_prop_otp_audit.py",
"py": '''"""Find Sole Proprietor A2P brands whose SMS passcode was never answered.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Re-sending a passcode costs a customer a
text message and restarts a 24 hour clock, so this script prints that repair
and leaves the decision to send it with a person.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_sole_prop_otp_audit")

MSG = "https://messaging.twilio.com/v1"

SOLE = "SOLE_PROPRIETOR"

# identity_status runs SELF_DECLARED, UNVERIFIED, VERIFIED, VETTED_VERIFIED.
# Only the last two mean the registered handset replied to the passcode.
ANSWERED = ("VERIFIED", "VETTED_VERIFIED")


def parse_time(value):
    """Parse a messaging v1 timestamp. Pure.

    These come back as ISO 8601 with a trailing Z, which
    datetime.fromisoformat did not accept before Python 3.11.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(text)
    except ValueError:
        return None


def age_hours(date_created, now):
    """Age of a brand in hours, or None when the timestamp is unreadable."""
    created = parse_time(date_created)
    if created is None or now is None:
        return None
    return (now - created).total_seconds() / 3600.0


def verdict(brand, age, window_hours=24.0):
    """Classify one brand registration against the passcode reply window.

    `age` is the brand's age in hours, or None. Taking it as an argument keeps
    the clock out of the classifier, so the boundary at the window and both
    sides of it are testable without freezing time. Returns (state, detail).
    """
    if not brand:
        return ("no-brand", "no brand registration to read.")

    brand_type = str(brand.get("brand_type") or "").upper()
    if brand_type != SOLE:
        return ("not-sole-prop",
                "brand_type is %s: identity here is proved by the customer "
                "profile, and no passcode is ever sent."
                % (brand_type or "unset"))

    status = str(brand.get("status") or "").upper()
    identity = str(brand.get("identity_status") or "").upper()

    if status == "FAILED":
        return ("brand-failed",
                "the brand itself is FAILED. A fresh passcode changes nothing "
                "until the registration is refiled, so read the failure first.")

    if identity in ANSWERED:
        return ("verified",
                "identity_status is %s: the handset replied and identity is "
                "settled." % identity)

    if not identity:
        return ("identity-unknown",
                "identity_status is not set on this brand, so nothing can be "
                "concluded about the passcode from this response.")

    links = brand.get("links") or {}
    if not links.get("brand_registration_otps"):
        return ("no-otp-subresource",
                "identity_status is %s and links.brand_registration_otps is "
                "absent, so no passcode has been raised on this brand at all. "
                "This is a submission problem, not an unanswered text."
                % identity)

    if age is None:
        return ("age-unknown",
                "identity_status is %s and date_created could not be read, so "
                "this cannot be aged against the reply window." % identity)

    if age >= window_hours:
        return ("otp-lapsed",
                "identity_status is still %s, %.0f hours after the brand was "
                "created. The %.0f hour reply window has closed and the "
                "passcode expired unanswered. status reads %s, which is not "
                "the field that unblocks sending."
                % (identity, age, window_hours, status or "unset"))

    return ("otp-outstanding",
            "identity_status is %s, %.0f hours in. The owner has about %.0f "
            "hours left to reply from the registered handset."
            % (identity, age, window_hours - age))


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
    ap.add_argument("--window-hours", type=float, default=24.0,
                    help="how long the owner has to reply to the passcode")
    ap.add_argument("--max-brands", type=int, default=500)
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
    now = datetime.datetime.now(datetime.timezone.utc)

    brands = list_v1(session, MSG + "/a2p/BrandRegistrations", "data",
                     args.max_brands)
    if not brands:
        log.info("no A2P brand registrations on this account")
        return 0

    sole = 0
    bad = 0
    for brand in brands:
        age = age_hours(brand.get("date_created"), now)
        state, detail = verdict(brand, age, args.window_hours)
        if state == "not-sole-prop":
            continue
        sole += 1
        name = brand.get("brand_sid") or brand.get("sid") or "brand"
        line = "%-20s %s  %s" % (state, name, detail)
        if state in ("verified", "otp-outstanding"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("otp-lapsed", "age-unknown"):
            log.warning("  repair: raise a fresh passcode at %s/a2p/"
                        "BrandRegistrations/%s/SmsOtp, then have the owner "
                        "reply from the registered handset within %.0f hours",
                        MSG, name, args.window_hours)
            log.warning("  repair: if that mobile already backs three A2P brand "
                        "registrations anywhere in the registry, or is not a "
                        "real US or Canadian handset, refile the profile with a "
                        "different number instead")
        elif state == "no-otp-subresource":
            log.warning("  repair: check how this brand was submitted before "
                        "sending anything; there is no passcode to re-send")

    log.info("%d brand(s), %d sole proprietor, %d waiting on a passcode",
             len(brands), sole, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sole-prop-otp-audit.mjs",
"js": '''/**
 * Find Sole Proprietor A2P brands whose SMS passcode was never answered.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The passcode re-send is printed,
 * never performed.
 */
const MSG = 'https://messaging.twilio.com/v1';

const SOLE = 'SOLE_PROPRIETOR';

// identity_status runs SELF_DECLARED, UNVERIFIED, VERIFIED, VETTED_VERIFIED.
// Only the last two mean the registered handset replied.
const ANSWERED = ['VERIFIED', 'VETTED_VERIFIED'];

/** Parse a messaging v1 ISO 8601 timestamp. Pure. Returns a Date or null. */
export function parseTime(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const t = Date.parse(text);
  return Number.isNaN(t) ? null : new Date(t);
}

/** Age of a brand in hours, or null when the timestamp is unreadable. */
export function ageHours(dateCreated, now) {
  const created = parseTime(dateCreated);
  if (created === null || !now) return null;
  return (now.getTime() - created.getTime()) / 3600000;
}

/**
 * Classify one brand registration against the passcode reply window. `age` is
 * in hours, or null; taking it as an argument keeps the clock out of the
 * classifier. Pure. Returns [state, detail].
 */
export function verdict(brand, age, windowHours = 24.0) {
  if (!brand) return ['no-brand', 'no brand registration to read.'];

  const brandType = String(brand.brand_type ?? '').toUpperCase();
  if (brandType !== SOLE) {
    return ['not-sole-prop',
      `brand_type is ${brandType || 'unset'}: identity here is proved by the ` +
      'customer profile, and no passcode is ever sent.'];
  }

  const status = String(brand.status ?? '').toUpperCase();
  const identity = String(brand.identity_status ?? '').toUpperCase();

  if (status === 'FAILED') {
    return ['brand-failed',
      'the brand itself is FAILED. A fresh passcode changes nothing until the ' +
      'registration is refiled, so read the failure first.'];
  }

  if (ANSWERED.includes(identity)) {
    return ['verified',
      `identity_status is ${identity}: the handset replied and identity is settled.`];
  }

  if (!identity) {
    return ['identity-unknown',
      'identity_status is not set on this brand, so nothing can be concluded ' +
      'about the passcode from this response.'];
  }

  const links = brand.links ?? {};
  if (!links.brand_registration_otps) {
    return ['no-otp-subresource',
      `identity_status is ${identity} and links.brand_registration_otps is ` +
      'absent, so no passcode has been raised on this brand at all. This is a ' +
      'submission problem, not an unanswered text.'];
  }

  if (age === null) {
    return ['age-unknown',
      `identity_status is ${identity} and date_created could not be read, so ` +
      'this cannot be aged against the reply window.'];
  }

  if (age >= windowHours) {
    return ['otp-lapsed',
      `identity_status is still ${identity}, ${age.toFixed(0)} hours after the ` +
      `brand was created. The ${windowHours.toFixed(0)} hour reply window has ` +
      'closed and the passcode expired unanswered. status reads ' +
      `${status || 'unset'}, which is not the field that unblocks sending.`];
  }

  return ['otp-outstanding',
    `identity_status is ${identity}, ${age.toFixed(0)} hours in. The owner has ` +
    `about ${(windowHours - age).toFixed(0)} hours left to reply from the ` +
    'registered handset.'];
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
  const flag = process.argv.indexOf('--window-hours');
  const windowHours = flag >= 0 ? Number(process.argv[flag + 1]) : 24.0;
  const now = new Date();

  const brands = await listV1(auth, `${MSG}/a2p/BrandRegistrations`, 'data');
  if (brands.length === 0) {
    console.log('no A2P brand registrations on this account');
    return;
  }

  let sole = 0;
  let bad = 0;
  for (const brand of brands) {
    const age = ageHours(brand.date_created, now);
    const [state, detail] = verdict(brand, age, windowHours);
    if (state === 'not-sole-prop') continue;
    sole += 1;
    const name = brand.brand_sid ?? brand.sid ?? 'brand';
    const line = `${state.padEnd(20)} ${name}  ${detail}`;
    if (state === 'verified' || state === 'otp-outstanding') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (state === 'otp-lapsed' || state === 'age-unknown') {
      console.warn(`  repair: raise a fresh passcode at ${MSG}/a2p/` +
                   `BrandRegistrations/${name}/SmsOtp, then have the owner reply ` +
                   `from the registered handset within ${windowHours} hours`);
      console.warn('  repair: if that mobile already backs three A2P brand ' +
                   'registrations anywhere in the registry, or is not a real US ' +
                   'or Canadian handset, refile the profile with a different number');
    } else if (state === 'no-otp-subresource') {
      console.warn('  repair: check how this brand was submitted before sending ' +
                   'anything; there is no passcode to re-send');
    }
  }

  console.log(`${brands.length} brand(s), ${sole} sole proprietor, ${bad} waiting ` +
              'on a passcode');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The age is an argument, so the window boundary is an ordinary assertion rather than a mocked clock. The two tests that earn their place are the ones that catch a wrong reading of the resource: a brand whose <code>status</code> is <code>APPROVED</code> while its identity never verified, which is the state that ships to production, and an unverified brand with no passcode subresource, which needs a different conversation entirely.",
"test_py_file": "test_twilio_sole_prop_otp_audit.py",
"test_py": '''import datetime

from twilio_sole_prop_otp_audit import age_hours, verdict

OTPS = {"brand_registration_otps": "https://messaging.twilio.com/v1/a2p/"
                                   "BrandRegistrations/BN01/SmsOtp"}
WAITING = {"brand_type": "SOLE_PROPRIETOR", "status": "PENDING",
           "identity_status": "SELF_DECLARED", "links": OTPS}
NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)


def test_inside_the_window_the_passcode_is_still_in_flight():
    state, detail = verdict(WAITING, 6.0)
    assert state == "otp-outstanding"
    assert "18 hours left" in detail


def test_past_the_window_the_passcode_has_expired_unanswered():
    state, detail = verdict(WAITING, 40.0)
    assert state == "otp-lapsed"
    assert "reply window has closed" in detail


def test_approved_status_does_not_rescue_an_unverified_identity():
    # This is the state that reaches production: somebody reads status, sees
    # APPROVED, and enables US sending on a brand that cannot register numbers.
    state, detail = verdict(dict(WAITING, status="APPROVED"), 72.0)
    assert state == "otp-lapsed"
    assert "status reads APPROVED" in detail


def test_vetted_verified_counts_as_answered():
    assert verdict(dict(WAITING, identity_status="VETTED_VERIFIED"), 500.0)[0] == "verified"


def test_missing_otp_subresource_is_not_an_unanswered_text():
    brand = dict(WAITING, links={})
    state, detail = verdict(brand, 200.0)
    assert state == "no-otp-subresource"
    assert "submission problem" in detail


def test_a_failed_brand_is_read_before_the_passcode():
    assert verdict(dict(WAITING, status="FAILED"), 200.0)[0] == "brand-failed"


def test_standard_brands_are_left_alone():
    state, detail = verdict({"brand_type": "STANDARD", "identity_status": "UNVERIFIED"}, 999.0)
    assert state == "not-sole-prop"
    assert "no passcode is ever sent" in detail


def test_an_unreadable_date_is_reported_rather_than_guessed():
    assert verdict(WAITING, None)[0] == "age-unknown"
    assert age_hours("not a date", NOW) is None
    assert round(age_hours("2026-08-29T00:00:00Z", NOW)) == 24
''',
"test_js_file": "twilio-sole-prop-otp-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageHours, verdict } from './twilio-sole-prop-otp-audit.mjs';

const OTPS = {
  brand_registration_otps:
    'https://messaging.twilio.com/v1/a2p/BrandRegistrations/BN01/SmsOtp',
};
const WAITING = {
  brand_type: 'SOLE_PROPRIETOR',
  status: 'PENDING',
  identity_status: 'SELF_DECLARED',
  links: OTPS,
};
const NOW = new Date('2026-08-30T00:00:00Z');

test('inside the window the passcode is still in flight', () => {
  const [state, detail] = verdict(WAITING, 6.0);
  assert.equal(state, 'otp-outstanding');
  assert.match(detail, /18 hours left/);
});

test('past the window the passcode has expired unanswered', () => {
  const [state, detail] = verdict(WAITING, 40.0);
  assert.equal(state, 'otp-lapsed');
  assert.match(detail, /reply window has closed/);
});

test('approved status does not rescue an unverified identity', () => {
  const [state, detail] = verdict({ ...WAITING, status: 'APPROVED' }, 72.0);
  assert.equal(state, 'otp-lapsed');
  assert.match(detail, /status reads APPROVED/);
});

test('vetted verified counts as answered', () => {
  assert.equal(verdict({ ...WAITING, identity_status: 'VETTED_VERIFIED' }, 500.0)[0],
               'verified');
});

test('missing otp subresource is not an unanswered text', () => {
  const [state, detail] = verdict({ ...WAITING, links: {} }, 200.0);
  assert.equal(state, 'no-otp-subresource');
  assert.match(detail, /submission problem/);
});

test('a failed brand is read before the passcode', () => {
  assert.equal(verdict({ ...WAITING, status: 'FAILED' }, 200.0)[0], 'brand-failed');
});

test('standard brands are left alone', () => {
  const [state, detail] = verdict(
    { brand_type: 'STANDARD', identity_status: 'UNVERIFIED' }, 999.0);
  assert.equal(state, 'not-sole-prop');
  assert.match(detail, /no passcode is ever sent/);
});

test('an unreadable date is reported rather than guessed', () => {
  assert.equal(verdict(WAITING, null)[0], 'age-unknown');
  assert.equal(ageHours('not a date', NOW), null);
  assert.equal(Math.round(ageHours('2026-08-29T00:00:00Z', NOW)), 24);
});
''',
"faq": [
 ("Can I re-send the passcode from the API?",
  "Yes, with a POST to the SmsOtp subresource on the brand, which raises a fresh code and restarts the 24 hour window. This script will not do it for you: it costs the customer a text message and puts a clock on their day, so the decision belongs to a person who can tell them it is coming."),
 ("Why does the brand say APPROVED while identity_status says SELF_DECLARED?",
  "They describe different things. status is about the registration record, identity_status is about whether the registered handset replied. A Sole Proprietor brand needs the second one to reach VERIFIED before the campaign under it can register numbers, so reading only status will tell you a blocked account is fine."),
 ("What is the three registration limit on the mobile number?",
  "A single mobile can back at most three A2P brand registrations across the whole registry, including ones filed through other vendors. Agencies hit it by reusing one owner's mobile across client brands. Once it is exhausted no re-send will land, and the profile has to be refiled with a different handset."),
 ("Can the customer use a Twilio number to receive the passcode?",
  "No. The registered mobile has to be a real US or Canadian handset, not a CPaaS or virtual number. When somebody enters one, the passcode never arrives and the brand looks exactly like a customer who ignored the text, which is why the number is worth checking before assuming the human is at fault."),
 ("Is this the same problem as a brand stuck at PENDING?",
  "No. A brand parked at PENDING is waiting on the registry, and there is nothing for anyone to do but wait. This one is waiting on a person, has a 24 hour deadline, and has a repair. Both look like a quiet brand from the console, which is why the identity fields are worth reading separately."),
],
"related": [
 ("/twilio/a2p-brand-stuck-pending-review/", "A brand parked at PENDING with no callback"),
 ("/twilio/sole-prop-extra-numbers-unregistered/", "A Sole Prop pool with more than one number"),
 ("/twilio/a2p-brand-registration-failed/", "An A2P brand stuck at FAILED blocks every campaign"),
],
"citations": [CITE_SOLE_PROP, CITE_BRAND, CITE_30034, CITE_KEYS],
},

{
"slug": "sole-prop-extra-numbers-unregistered",
"title": "Extra numbers on a Sole Prop campaign never leave UNREGISTERED",
"description": "A Sole Proprietor brand allows one campaign holding one number. Adding more never errors: the extras stay UNREGISTERED and 30034 arrives at random.",
"h1": "extra numbers on a Sole Prop campaign never leave UNREGISTERED",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["sole proprietor one number limit", "twilio sole prop 30034 intermittent",
             "10dlc sole proprietor sender pool", "twilio a2p unregistered number",
             "messaging service sender pool sole prop"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Roughly a third of the messages get through. The rest come back <code>30034</code>. Retrying works, sometimes, and which send succeeds changes every time, so the first theory is a flaky carrier and the second is a Twilio incident. It is neither. The Messaging Service is picking a sender per message from a pool of three, and on a Sole Proprietor brand only one of those three was ever registered.",
"short_answer": """<p>For each Messaging Service read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> and take <code>brand_registration_sid</code>. Read that brand at <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}</code>. If <code>brand_type</code> is <code>SOLE_PROPRIETOR</code>, then <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code> and flag any pool holding more than one number.</p>
<p>A Sole Proprietor brand permits exactly one campaign, and that campaign exactly one 10DLC number. Adding a second to the pool returns success; it simply never registers.</p>""",
"problem": """<p>The add succeeded. That is the whole trap. Attaching a number to a Messaging Service is an ordinary call that returns an ordinary created resource, and nothing in the response mentions that the brand behind this service is capped at one sender. So the pool has three numbers in it, the console lists three numbers, and by every visible measure the service is configured the way somebody intended.</p>
<p>Then the sends start failing at a rate nobody can pin down. A Messaging Service selects the <code>from</code> per message, so the same recipient succeeds on one attempt and <code>30034</code>s on the next. That intermittency is what sends teams chasing carrier filtering, rate limits and retry logic, none of which is involved. Two of the three numbers are sitting at A2P status <code>UNREGISTERED</code>, permanently, and no amount of waiting will move them.</p>""",
"why": """<p><strong>Intermittent is the signature.</strong> A number missing from any pool fails consistently for one <code>from</code>: send from that number, it always fails. This fails randomly across the same recipients, because the failure is decided at selection time. If your <code>30034</code>s correlate with a single sender you have the other problem; if they scatter, you have this one.</p>
<p><strong>The limit is a property of the brand, not of the service.</strong> Nothing on the Messaging Service says one number. You have to follow the campaign to <code>brand_registration_sid</code>, read <code>brand_type</code> there, and only then does the pool size mean anything. A script that stops at the campaign sees a perfectly healthy <code>VERIFIED</code> record.</p>
<p><strong>Sole Proprietor cannot be widened.</strong> There is no upgrade path that keeps this brand and adds capacity. More senders means a Standard or Low-Volume Standard brand, with a customer profile and a different registration. Teams lose weeks assuming the cap is a quota to be raised rather than a shape of registration to be replaced.</p>
<p><strong>Which number is the registered one is not obvious.</strong> Removing the wrong two takes the working sender out of the pool and turns an intermittent failure into a total one. The order numbers were added is not a reliable guide, so the repair has to be checked against the A2P registration status of each number before anything is detached.</p>""",
"steps": [
 {"h": "Read the campaign to find the brand behind the service",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> returns the campaign under <code>compliance</code>. Take <code>brand_registration_sid</code> from it. A service with no campaign at all is a different finding and is covered separately.</p>"""},
 {"h": "Read brand_type on that brand",
  "body": """<p><code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}</code> and look at <code>brand_type</code>. Only <code>SOLE_PROPRIETOR</code> carries the one number limit. Cache this per brand: several services can share one, and there is no reason to fetch it twice.</p>"""},
 {"h": "Count the pool",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers</code>, following the pages. On a Sole Proprietor brand a length greater than one is the finding, and the count of extras is the number of senders that will never register.</p>"""},
 {"h": "Separate an empty pool from an overfilled one",
  "body": """<p>Zero numbers on a Sole Proprietor service fails every send consistently rather than intermittently, and the repair is to add one rather than remove several. Same brand, same limit, opposite mistake, so it belongs in the report as its own state.</p>"""},
 {"h": "Print the removals, and say which one to keep",
  "body": """<p>The repair is to detach every number except the intended sender, leaving one. Do not guess which to keep from the order of the list: confirm the registered sender before detaching anything, or the fix converts intermittent failures into total ones. If the account genuinely needs more senders, the repair is a Standard or Low-Volume Standard brand, because Sole Proprietor cannot be widened.</p>"""},
],
"verify": """<p>Re-run the script. Every Sole Proprietor service should report one number in the pool.</p>
<pre><code class="language-bash">python3 twilio_sole_prop_pool_audit.py
# 6 service(s), 2 on a sole proprietor brand, 0 overfilled</code></pre>""",
"code_intro": "Three reads per service, and the brand cached across them. The classifier takes the brand, the pool size and the campaign status as plain values rather than fetching anything, so every combination that matters &mdash; overfilled, empty, exactly one but not yet verified, and the case where the brand could not be read at all &mdash; is a test that runs offline.",
"py_file": "twilio_sole_prop_pool_audit.py",
"py": '''"""Find Sole Proprietor Messaging Services holding more than one sender.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Detaching the wrong number here would take
the one registered sender out of the pool, so the removals are printed and a
person decides which number stays.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_sole_prop_pool_audit")

MSG = "https://messaging.twilio.com/v1"

SOLE = "SOLE_PROPRIETOR"

# A Sole Proprietor brand permits one campaign, and that campaign one 10DLC
# number. The limit lives on the brand, not on the Messaging Service.
SOLE_PROP_SENDER_LIMIT = 1


def verdict(brand, pool_size, campaign_status=None, limit=SOLE_PROP_SENDER_LIMIT):
    """Classify one Messaging Service against its brand's sender limit.

    `brand` is the brand registration dict or None, `pool_size` the number of
    phone numbers in the service's pool or None. Nothing is fetched here, so
    every state below is testable offline. Returns (state, detail).
    """
    if brand is None:
        return ("brand-unread",
                "the campaign names a brand_registration_sid that could not be "
                "read, so the one sender limit cannot be applied to this pool.")

    brand_type = str(brand.get("brand_type") or "").upper()
    if brand_type != SOLE:
        return ("not-sole-prop",
                "brand_type is %s: the pool size is not capped by the brand."
                % (brand_type or "unset"))

    if pool_size is None:
        return ("pool-unread",
                "sole proprietor brand and the sender pool could not be read.")

    status = str(campaign_status or "").upper()

    if pool_size == 0:
        return ("empty-pool",
                "sole proprietor brand with nothing in the sender pool. Every "
                "US send fails consistently rather than intermittently, and "
                "the repair is to add the one number rather than remove any.")

    if pool_size > limit:
        extras = pool_size - limit
        return ("overfilled",
                "%d numbers in the pool on a sole proprietor brand, which "
                "permits %d. %d of them will sit at A2P status UNREGISTERED "
                "permanently, and the service picks a sender per message, so "
                "30034 arrives at random rather than for one from."
                % (pool_size, limit, extras))

    if status and status != "VERIFIED":
        return ("single-not-verified",
                "one number, which is the limit, but campaign_status is %s so "
                "it is not registered yet. This is the review clock, not the "
                "sender limit." % status)

    return ("registered",
            "one number in the pool, which is what a sole proprietor brand "
            "supports.")


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


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        if page is None:
            break
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def read_brand(session, cache, brand_sid):
    """Read a brand once per run. Several services can share one brand."""
    if not brand_sid:
        return None
    if brand_sid not in cache:
        cache[brand_sid] = get(session, "%s/a2p/BrandRegistrations/%s"
                               % (MSG, brand_sid))
    return cache[brand_sid]


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
    brands = {}

    services = list_v1(session, MSG + "/Services", "services", args.max_services)
    if not services:
        log.info("no Messaging Services on this account")
        return 0

    sole = 0
    bad = 0
    for svc in services:
        campaigns = list_v1(session, "%s/Services/%s/Compliance/Usa2p"
                            % (MSG, svc["sid"]), "compliance")
        campaign = campaigns[0] if campaigns else None
        if campaign is None:
            continue
        brand = read_brand(session, brands, campaign.get("brand_registration_sid"))
        numbers = list_v1(session, "%s/Services/%s/PhoneNumbers" % (MSG, svc["sid"]),
                          "phone_numbers")
        state, detail = verdict(brand, len(numbers),
                                campaign.get("campaign_status"))
        if state == "not-sole-prop":
            continue
        sole += 1
        name = svc.get("friendly_name") or svc["sid"]
        line = "%-20s %s  %s" % (state, name, detail)
        if state == "registered":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "overfilled":
            for num in numbers:
                log.warning("    in pool: %s  %s", num.get("phone_number", "?"),
                            num.get("sid", ""))
            log.warning("  repair: detach every number above except the one that "
                        "is actually registered, at %s/Services/%s/PhoneNumbers/"
                        "{PhoneNumberSid}. Confirm which one is registered "
                        "first: removing the wrong two turns an intermittent "
                        "failure into a total one", MSG, svc["sid"])
            log.warning("  repair: if this account genuinely needs more senders, "
                        "register a Standard or Low-Volume Standard brand. Sole "
                        "Proprietor cannot be widened")
        elif state == "empty-pool":
            log.warning("  repair: attach the intended sender to %s, then wait "
                        "for its A2P registration to complete", svc["sid"])

    log.info("%d service(s), %d on a sole proprietor brand, %d overfilled",
             len(services), sole, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sole-prop-pool-audit.mjs",
"js": '''/**
 * Find Sole Proprietor Messaging Services holding more than one sender.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The removals are printed, because
 * detaching the wrong number takes the one registered sender out of the pool.
 */
const MSG = 'https://messaging.twilio.com/v1';

const SOLE = 'SOLE_PROPRIETOR';

// A Sole Proprietor brand permits one campaign, and that campaign one 10DLC
// number. The limit lives on the brand, not on the Messaging Service.
export const SOLE_PROP_SENDER_LIMIT = 1;

/**
 * Classify one Messaging Service against its brand's sender limit. Nothing is
 * fetched here. Pure. Returns [state, detail].
 */
export function verdict(brand, poolSize, campaignStatus = null,
                        limit = SOLE_PROP_SENDER_LIMIT) {
  if (brand === null || brand === undefined) {
    return ['brand-unread',
      'the campaign names a brand_registration_sid that could not be read, so ' +
      'the one sender limit cannot be applied to this pool.'];
  }

  const brandType = String(brand.brand_type ?? '').toUpperCase();
  if (brandType !== SOLE) {
    return ['not-sole-prop',
      `brand_type is ${brandType || 'unset'}: the pool size is not capped by the brand.`];
  }

  if (poolSize === null || poolSize === undefined) {
    return ['pool-unread',
      'sole proprietor brand and the sender pool could not be read.'];
  }

  const status = String(campaignStatus ?? '').toUpperCase();

  if (poolSize === 0) {
    return ['empty-pool',
      'sole proprietor brand with nothing in the sender pool. Every US send ' +
      'fails consistently rather than intermittently, and the repair is to add ' +
      'the one number rather than remove any.'];
  }

  if (poolSize > limit) {
    const extras = poolSize - limit;
    return ['overfilled',
      `${poolSize} numbers in the pool on a sole proprietor brand, which ` +
      `permits ${limit}. ${extras} of them will sit at A2P status UNREGISTERED ` +
      'permanently, and the service picks a sender per message, so 30034 ' +
      'arrives at random rather than for one from.'];
  }

  if (status && status !== 'VERIFIED') {
    return ['single-not-verified',
      `one number, which is the limit, but campaign_status is ${status} so it ` +
      'is not registered yet. This is the review clock, not the sender limit.'];
  }

  return ['registered',
    'one number in the pool, which is what a sole proprietor brand supports.'];
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

export async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    if (page === null) break;
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
  }
  return out.slice(0, limit);
}

async function readBrand(auth, cache, brandSid) {
  if (!brandSid) return null;
  if (!(brandSid in cache)) {
    cache[brandSid] = await get(auth, `${MSG}/a2p/BrandRegistrations/${brandSid}`);
  }
  return cache[brandSid];
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
  const brands = {};

  const services = await listV1(auth, `${MSG}/Services`, 'services');
  if (services.length === 0) {
    console.log('no Messaging Services on this account');
    return;
  }

  let sole = 0;
  let bad = 0;
  for (const svc of services) {
    const campaigns = await listV1(auth, `${MSG}/Services/${svc.sid}/Compliance/Usa2p`,
                                   'compliance');
    const campaign = campaigns[0] ?? null;
    if (campaign === null) continue;
    const brand = await readBrand(auth, brands, campaign.brand_registration_sid);
    const numbers = await listV1(auth, `${MSG}/Services/${svc.sid}/PhoneNumbers`,
                                 'phone_numbers');
    const [state, detail] = verdict(brand, numbers.length, campaign.campaign_status);
    if (state === 'not-sole-prop') continue;
    sole += 1;
    const name = svc.friendly_name ?? svc.sid;
    const line = `${state.padEnd(20)} ${name}  ${detail}`;
    if (state === 'registered') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'overfilled') {
      for (const num of numbers) {
        console.warn(`    in pool: ${num.phone_number ?? '?'}  ${num.sid ?? ''}`);
      }
      console.warn('  repair: detach every number above except the one that is ' +
                   `actually registered, at ${MSG}/Services/${svc.sid}/` +
                   'PhoneNumbers/{PhoneNumberSid}. Confirm which one is ' +
                   'registered first: removing the wrong two turns an ' +
                   'intermittent failure into a total one');
      console.warn('  repair: if this account genuinely needs more senders, ' +
                   'register a Standard or Low-Volume Standard brand. Sole ' +
                   'Proprietor cannot be widened');
    } else if (state === 'empty-pool') {
      console.warn(`  repair: attach the intended sender to ${svc.sid}, then ` +
                   'wait for its A2P registration to complete');
    }
  }

  console.log(`${services.length} service(s), ${sole} on a sole proprietor brand, ` +
              `${bad} overfilled`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The classifier never fetches, so the pool size is just a number and the brand is a dict. That makes the four states worth being sure about into four short assertions: too many numbers, none at all, exactly one on a campaign that has not been approved yet, and a brand that could not be read, which must not be silently treated as compliant.",
"test_py_file": "test_twilio_sole_prop_pool_audit.py",
"test_py": '''from twilio_sole_prop_pool_audit import verdict

SOLE_PROP = {"brand_type": "SOLE_PROPRIETOR", "status": "APPROVED"}
STANDARD = {"brand_type": "STANDARD", "status": "APPROVED"}


def test_three_numbers_leaves_two_permanently_unregistered():
    state, detail = verdict(SOLE_PROP, 3, "VERIFIED")
    assert state == "overfilled"
    assert "2 of them" in detail
    assert "at random" in detail


def test_one_number_on_a_verified_campaign_is_the_supported_shape():
    assert verdict(SOLE_PROP, 1, "VERIFIED")[0] == "registered"


def test_an_empty_pool_is_the_opposite_mistake():
    state, detail = verdict(SOLE_PROP, 0, "VERIFIED")
    assert state == "empty-pool"
    assert "consistently" in detail


def test_one_number_on_an_unapproved_campaign_is_the_review_clock():
    state, detail = verdict(SOLE_PROP, 1, "IN_PROGRESS")
    assert state == "single-not-verified"
    assert "not the sender limit" in detail


def test_a_standard_brand_is_not_capped_by_pool_size():
    state, _ = verdict(STANDARD, 12, "VERIFIED")
    assert state == "not-sole-prop"


def test_an_unread_brand_is_never_reported_as_compliant():
    # Following brand_registration_sid can fail. Guessing SOLE_PROPRIETOR would
    # invent findings; guessing STANDARD would hide them.
    assert verdict(None, 4, "VERIFIED")[0] == "brand-unread"


def test_an_unread_pool_is_reported_as_such():
    assert verdict(SOLE_PROP, None, "VERIFIED")[0] == "pool-unread"


def test_an_unset_brand_type_is_not_assumed_to_be_sole_prop():
    state, detail = verdict({"status": "APPROVED"}, 5)
    assert state == "not-sole-prop"
    assert "unset" in detail
''',
"test_js_file": "twilio-sole-prop-pool-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './twilio-sole-prop-pool-audit.mjs';

const SOLE_PROP = { brand_type: 'SOLE_PROPRIETOR', status: 'APPROVED' };
const STANDARD = { brand_type: 'STANDARD', status: 'APPROVED' };

test('three numbers leaves two permanently unregistered', () => {
  const [state, detail] = verdict(SOLE_PROP, 3, 'VERIFIED');
  assert.equal(state, 'overfilled');
  assert.match(detail, /2 of them/);
  assert.match(detail, /at random/);
});

test('one number on a verified campaign is the supported shape', () => {
  assert.equal(verdict(SOLE_PROP, 1, 'VERIFIED')[0], 'registered');
});

test('an empty pool is the opposite mistake', () => {
  const [state, detail] = verdict(SOLE_PROP, 0, 'VERIFIED');
  assert.equal(state, 'empty-pool');
  assert.match(detail, /consistently/);
});

test('one number on an unapproved campaign is the review clock', () => {
  const [state, detail] = verdict(SOLE_PROP, 1, 'IN_PROGRESS');
  assert.equal(state, 'single-not-verified');
  assert.match(detail, /not the sender limit/);
});

test('a standard brand is not capped by pool size', () => {
  assert.equal(verdict(STANDARD, 12, 'VERIFIED')[0], 'not-sole-prop');
});

test('an unread brand is never reported as compliant', () => {
  assert.equal(verdict(null, 4, 'VERIFIED')[0], 'brand-unread');
});

test('an unread pool is reported as such', () => {
  assert.equal(verdict(SOLE_PROP, null, 'VERIFIED')[0], 'pool-unread');
});

test('an unset brand type is not assumed to be sole prop', () => {
  const [state, detail] = verdict({ status: 'APPROVED' }, 5);
  assert.equal(state, 'not-sole-prop');
  assert.match(detail, /unset/);
});
''',
"faq": [
 ("How do I tell this apart from a number that is not in any pool?",
  "By whether the failures follow a sender. A number outside every pool fails every time you send from it and never fails for the others. This one fails at random across the same recipients, because the Messaging Service chooses the from per message and only one number in the pool is registered."),
 ("Can I raise the one number limit on a Sole Proprietor brand?",
  "No. It is not a quota, it is the shape of the registration: one brand, one campaign, one number. More senders means registering a Standard or Low-Volume Standard brand instead, which needs a customer profile and goes through its own review."),
 ("Which number in the pool is the registered one?",
  "Check the A2P registration status of each number rather than assuming it is the first or oldest. Detaching the wrong two removes the only working sender, and the failure goes from intermittent to complete while the report still says the pool was fixed."),
 ("Does adding the extra numbers cost anything?",
  "They are billed as phone numbers like any others, and they will carry non-US traffic and voice normally. What they will not do is send US A2P messages, so the cost is a monthly line item plus a share of your sends failing."),
 ("Why does the API let me add them at all?",
  "The sender pool is a Messaging Service feature and the limit belongs to the brand behind the campaign. The two are separate resources, and the add is validated against the service rather than against the registration, so nothing on that call is in a position to refuse."),
],
"related": [
 ("/twilio/number-missing-from-campaign-sender-pool/", "A 10DLC number outside the pool is never registered"),
 ("/twilio/sole-prop-otp-never-accepted/", "A Sole Prop brand blocked by an unanswered passcode"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_FIX_NUMBERS, CITE_30034, CITE_MSPN, CITE_BRAND],
},

{
"slug": "tmobile-brand-daily-segment-cap",
"title": "T-Mobile caps daily segments per brand, not per campaign",
"description": "Sends stop mid-afternoon with 30023 and resume at midnight Pacific. The ceiling belongs to the brand and every campaign under it shares one pool.",
"h1": "T-Mobile caps daily segments per brand, not per campaign",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30023 daily message cap", "t-mobile daily segment limit 10dlc",
             "brand daily cap a2p", "t-mobile special business review",
             "twilio num_segments daily"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The morning batch is fine. The afternoon batch is fine. Somewhere around four o'clock deliveries to T-Mobile handsets stop, and by six every one of them is failing, while Verizon and AT&T carry on as if nothing happened. Tomorrow morning it works again. Nothing in your code changed, nothing in the Messaging Service changed, and the number that ran out is one you have never seen: a daily segment allowance held by T-Mobile against your brand.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}</code> for <code>brand_type</code>, <code>brand_score</code> and <code>russell_3000</code>, which is what the tier is derived from. Read <code>rate_limits</code> on <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> for the per-carrier limits Twilio can see. Then page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=today</code> and sum <code>num_segments</code>.</p>
<p>Segments, not messages: a 480 character body is four of them. And a Sole Proprietor brand is capped at 1,000 segments a day across every campaign it owns.</p>""",
"problem": """<p>Nothing rejects the send. Twilio accepts the message, the carrier accepts the handoff, and then T-Mobile counts it against an allowance that lives in T-Mobile's systems and belongs to your brand rather than to a campaign, a number or a Messaging Service. Cross the line and messages come back <code>30023</code>, or simply undelivered. The counter resets at midnight US Pacific, which is why the failure has a time of day and a clean edge either side of it.</p>
<p>The part that makes it hard to diagnose from the inside is that the cap is shared. Every campaign under one brand draws from the same pool, so a marketing blast on one campaign exhausts the allowance for the transactional campaign next to it. Whoever gets paged is looking at a service that did not change, sending traffic that did not grow, failing because of volume they do not own.</p>""",
"why": """<p><strong>Segments are the unit, and your body length decides how many you spend.</strong> A single message can be one segment or eight, and a body that grew by ten characters in a copy edit can quietly turn every send into two. Counting messages against a segment ceiling will tell you that you are at half your limit on the day you exhaust it.</p>
<p><strong>The ceiling is not fully visible from the API.</strong> Sole Proprietor is 1,000 segments a day. A Russell 3000 company defaults to 200,000. Everything in between is assigned by T-Mobile from your trust tier and is not published as a field you can read, so the honest script derives what it can, reports <code>rate_limits</code> verbatim, and asks you to supply the rest rather than inventing it.</p>
<p><strong>Your own segment count is an upper bound, not the number being capped.</strong> The Messages list does not tell you which carrier a destination belongs to, so you cannot isolate the T-Mobile share of the day's traffic from it. Total segments sent today is a ceiling on your T-Mobile burn, which is enough for an early warning and not enough for a precise one, and a script that pretends otherwise will be wrong in both directions.</p>
<p><strong>An observed 30023 outranks any estimate.</strong> One message today carrying <code>error_code</code> <code>30023</code> is direct evidence the allowance ran out, and it should be reported ahead of whatever the arithmetic says, because the arithmetic is working from a bound.</p>""",
"steps": [
 {"h": "Find the brand behind the campaign and read its tier fields",
  "body": """<p>The campaign at <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> gives <code>brand_registration_sid</code>. On the brand, <code>brand_type</code>, <code>brand_score</code> and <code>russell_3000</code> are the inputs to the tier. Note that the brand, not the service, is what the cap is attached to, so several services can be sharing one number.</p>"""},
 {"h": "Read rate_limits, and print it rather than parsing it",
  "body": """<p><code>rate_limits</code> on the campaign carries the per-carrier limits Twilio has been told about. Its exact shape varies by carrier and by what the registry returned, so the script reports it as it found it and derives the ceiling from the brand fields, instead of hard-coding a path into a structure that may not be there.</p>"""},
 {"h": "Sum today's segments, not today's messages",
  "body": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and add up <code>num_segments</code>, which arrives as a string. Use the US Pacific day, since that is the boundary the counter resets on and it is not the same day your servers think it is.</p>"""},
 {"h": "Count the 30023s in the same pass",
  "body": """<p>There is no <code>ErrorCode</code> filter on the Messages list, so the error codes come out of the same paging run, filtered client-side. Any message today with <code>error_code</code> <code>30023</code> means the cap was reached, and that observation should be reported ahead of any estimate.</p>"""},
 {"h": "Print the two repairs that exist, and the one that does not",
  "body": """<p>The cap cannot be raised by API. Either the brand moves up a tier &mdash; Sole Proprietor to Standard, then secondary vetting to lift the score &mdash; or you request a T-Mobile Special Business Review through Twilio Support. Until one of those lands, the only lever is operational: spread the day's volume and shorten bodies so each message costs fewer segments.</p>"""},
],
"verify": """<p>Re-run the script after the day's batch. The burn should sit under the ceiling and no message should carry <code>30023</code>.</p>
<pre><code class="language-bash">python3 twilio_tmobile_daily_cap_report.py --ceiling 1000
# 1 brand(s), 640 segment(s) today, 0 capped</code></pre>""",
"code_intro": "Two pure functions carry the judgement. <code>brand_ceiling()</code> derives what the brand fields alone can support and returns <code>None</code> rather than guessing when they cannot; <code>verdict()</code> takes the ceiling, the day's segments and the count of observed <code>30023</code>s as plain numbers. Neither reads a clock or a network, so the ordering that matters &mdash; evidence before arithmetic &mdash; is a test.",
"py_file": "twilio_tmobile_daily_cap_report.py",
"py": '''"""Measure today's segment burn against T-Mobile's daily cap on your brand.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Nothing here can raise the cap; the script
exists so the ceiling is a number somebody knows before the afternoon batch
runs into it.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_tmobile_daily_cap_report")

API = "https://api.twilio.com/2010-04-01"
MSG = "https://messaging.twilio.com/v1"

DAILY_CAP_ERROR = 30023

# Published tier defaults. Everything between these two is assigned by T-Mobile
# from the trust tier and is not exposed as a field, so it has to be supplied.
SOLE_PROP_DAILY_SEGMENTS = 1000
RUSSELL_3000_DAILY_SEGMENTS = 200000


def brand_ceiling(brand):
    """Derive the daily segment ceiling from a brand registration. Pure.

    Returns (ceiling, source). ceiling is None when the brand fields do not
    determine it, which is the common case: the tier comes from T-Mobile and
    there is no field to read it from.
    """
    if not brand:
        return (None, "no brand registration to read")

    brand_type = str(brand.get("brand_type") or "").upper()
    if brand_type == "SOLE_PROPRIETOR":
        return (SOLE_PROP_DAILY_SEGMENTS, "sole proprietor brands are capped at "
                "1,000 segments a day")

    if brand.get("russell_3000"):
        return (RUSSELL_3000_DAILY_SEGMENTS,
                "russell_3000 is true, which defaults to 200,000 segments a day")

    score = brand.get("brand_score")
    return (None,
            "brand_type is %s with brand_score %s: the tier is assigned by "
            "T-Mobile and is not exposed as a field, so pass --ceiling with the "
            "value from your tier"
            % (brand_type or "unset", "unset" if score is None else score))


def summarise(messages):
    """Total segments and capped-message count for a day of messages. Pure.

    num_segments arrives as a string. There is no ErrorCode filter on the
    Messages list, so 30023 is counted here rather than asked for.
    """
    segments = 0
    capped = 0
    for m in messages or []:
        try:
            segments += int(m.get("num_segments") or 0)
        except (TypeError, ValueError):
            pass
        try:
            code = int(m.get("error_code") or 0)
        except (TypeError, ValueError):
            code = 0
        if code == DAILY_CAP_ERROR:
            capped += 1
    return (segments, capped)


def verdict(ceiling, segments, capped, warn_ratio=0.8):
    """Classify one brand's position against the daily cap. Pure.

    An observed 30023 outranks the arithmetic, because the segment total is an
    upper bound: the Messages list does not say which carrier a destination
    belongs to, so the T-Mobile share of it cannot be isolated.
    Returns (state, detail).
    """
    if capped:
        return ("cap-hit",
                "%d message(s) today came back %d. The daily allowance ran out; "
                "it resets at midnight US Pacific." % (capped, DAILY_CAP_ERROR))

    if segments is None:
        return ("burn-unknown",
                "today's messages could not be read, so the burn is unknown.")

    if ceiling is None:
        return ("ceiling-unknown",
                "%d segment(s) sent today and no ceiling could be derived from "
                "the brand. Supply the tier value to turn this into a warning."
                % segments)

    if segments >= ceiling:
        return ("over-estimate",
                "%d segment(s) today against a ceiling of %d. That total is "
                "every carrier, so it is an upper bound on the T-Mobile share, "
                "but it is past the line and nothing has failed yet only "
                "because not all of it went to T-Mobile."
                % (segments, ceiling))

    if segments >= ceiling * warn_ratio:
        return ("near-cap",
                "%d segment(s) today, %.0f%% of the %d ceiling. Spread the rest "
                "of the day's volume." % (segments, 100.0 * segments / ceiling,
                                          ceiling))

    return ("under-cap",
            "%d segment(s) today against a ceiling of %d." % (segments, ceiling))


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


def list_messages(session, account, since, limit=20000):
    """Page the Messages list. next_page_uri is a path, not an absolute URL."""
    out = []
    page = get(session, "%s/Accounts/%s/Messages.json" % (API, account),
               PageSize=1000, **{"DateSent>": since})
    while page:
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        if not nxt or len(out) >= limit:
            break
        page = get(session, "https://api.twilio.com" + nxt)
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ceiling", type=int, default=None,
                    help="daily segment ceiling for your T-Mobile tier, when "
                         "the brand fields do not determine it")
    ap.add_argument("--warn-ratio", type=float, default=0.8)
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

    # The counter resets at midnight US Pacific, which is not your servers' day.
    pacific = datetime.timezone(datetime.timedelta(hours=-7))
    today = datetime.datetime.now(pacific).date().isoformat()

    messages = list_messages(session, account, today)
    segments, capped = summarise(messages)

    services = list_v1(session, MSG + "/Services", "services", args.max_services)
    brands = {}
    for svc in services:
        campaigns = list_v1(session, "%s/Services/%s/Compliance/Usa2p"
                            % (MSG, svc["sid"]), "compliance")
        for campaign in campaigns:
            brand_sid = campaign.get("brand_registration_sid")
            if not brand_sid or brand_sid in brands:
                continue
            brands[brand_sid] = get(session, "%s/a2p/BrandRegistrations/%s"
                                    % (MSG, brand_sid))
            limits = campaign.get("rate_limits")
            if limits:
                log.info("rate_limits on %s: %s", svc["sid"], limits)

    if not brands:
        log.info("no A2P brands reachable from the Messaging Services on this account")
        return 0

    bad = 0
    for brand_sid, brand in brands.items():
        derived, source = brand_ceiling(brand)
        ceiling = args.ceiling if args.ceiling is not None else derived
        state, detail = verdict(ceiling, segments, capped, args.warn_ratio)
        line = "%-16s %s  %s" % (state, brand_sid, detail)
        if state == "under-cap":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  ceiling: %s", source if args.ceiling is None
                    else "supplied on the command line")
        if state in ("cap-hit", "over-estimate", "near-cap"):
            log.warning("  repair: the cap cannot be raised by API. Move the "
                        "brand up a tier (Sole Proprietor to Standard, then "
                        "secondary vetting to lift brand_score), or request a "
                        "T-Mobile Special Business Review through Twilio Support")
            log.warning("  repair: until then, spread the day's volume and "
                        "shorten bodies, since the cap counts segments and a "
                        "160 character overflow doubles the cost of every send")

    log.info("%d brand(s), %d segment(s) today, %d capped",
             len(brands), segments, capped)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-tmobile-daily-cap-report.mjs",
"js": '''/**
 * Measure today's segment burn against T-Mobile's daily cap on your brand.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. Nothing here can raise the cap.
 */
const API = 'https://api.twilio.com/2010-04-01';
const MSG = 'https://messaging.twilio.com/v1';

export const DAILY_CAP_ERROR = 30023;

// Published tier defaults. Everything between these two is assigned by T-Mobile
// from the trust tier and is not exposed as a field, so it has to be supplied.
const SOLE_PROP_DAILY_SEGMENTS = 1000;
const RUSSELL_3000_DAILY_SEGMENTS = 200000;

/**
 * Derive the daily segment ceiling from a brand registration. Pure.
 * Returns [ceiling, source]; ceiling is null when the fields do not determine it.
 */
export function brandCeiling(brand) {
  if (!brand) return [null, 'no brand registration to read'];

  const brandType = String(brand.brand_type ?? '').toUpperCase();
  if (brandType === 'SOLE_PROPRIETOR') {
    return [SOLE_PROP_DAILY_SEGMENTS,
      'sole proprietor brands are capped at 1,000 segments a day'];
  }

  if (brand.russell_3000) {
    return [RUSSELL_3000_DAILY_SEGMENTS,
      'russell_3000 is true, which defaults to 200,000 segments a day'];
  }

  const score = brand.brand_score;
  return [null,
    `brand_type is ${brandType || 'unset'} with brand_score ` +
    `${score === null || score === undefined ? 'unset' : score}: the tier is ` +
    'assigned by T-Mobile and is not exposed as a field, so pass --ceiling with ' +
    'the value from your tier'];
}

/**
 * Total segments and capped-message count for a day of messages. Pure.
 * num_segments arrives as a string, and there is no ErrorCode filter on the list.
 */
export function summarise(messages) {
  let segments = 0;
  let capped = 0;
  for (const m of messages ?? []) {
    const n = Number.parseInt(m.num_segments ?? 0, 10);
    if (Number.isFinite(n)) segments += n;
    const code = Number.parseInt(m.error_code ?? 0, 10);
    if (code === DAILY_CAP_ERROR) capped += 1;
  }
  return [segments, capped];
}

/**
 * Classify one brand's position against the daily cap. Pure.
 * An observed 30023 outranks the arithmetic, because the segment total is an
 * upper bound: the Messages list does not say which carrier a destination is on.
 * Returns [state, detail].
 */
export function verdict(ceiling, segments, capped, warnRatio = 0.8) {
  if (capped) {
    return ['cap-hit',
      `${capped} message(s) today came back ${DAILY_CAP_ERROR}. The daily ` +
      'allowance ran out; it resets at midnight US Pacific.'];
  }

  if (segments === null || segments === undefined) {
    return ['burn-unknown', "today's messages could not be read, so the burn is unknown."];
  }

  if (ceiling === null || ceiling === undefined) {
    return ['ceiling-unknown',
      `${segments} segment(s) sent today and no ceiling could be derived from ` +
      'the brand. Supply the tier value to turn this into a warning.'];
  }

  if (segments >= ceiling) {
    return ['over-estimate',
      `${segments} segment(s) today against a ceiling of ${ceiling}. That total ` +
      'is every carrier, so it is an upper bound on the T-Mobile share, but it ' +
      'is past the line and nothing has failed yet only because not all of it ' +
      'went to T-Mobile.'];
  }

  if (segments >= ceiling * warnRatio) {
    return ['near-cap',
      `${segments} segment(s) today, ${(100 * segments / ceiling).toFixed(0)}% of ` +
      `the ${ceiling} ceiling. Spread the rest of the day's volume.`];
  }

  return ['under-cap', `${segments} segment(s) today against a ceiling of ${ceiling}.`];
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

async function listMessages(auth, account, since, limit = 20000) {
  const out = [];
  let page = await get(auth, `${API}/Accounts/${account}/Messages.json`,
                       { PageSize: 1000, 'DateSent>': since });
  while (page) {
    out.push(...(page.messages ?? []));
    const nxt = page.next_page_uri;
    if (!nxt || out.length >= limit) break;
    page = await get(auth, `https://api.twilio.com${nxt}`);
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
  const flag = process.argv.indexOf('--ceiling');
  const supplied = flag >= 0 ? Number(process.argv[flag + 1]) : null;

  // The counter resets at midnight US Pacific, which is not your servers' day.
  const pacific = new Date(Date.now() - 7 * 3600000);
  const today = pacific.toISOString().slice(0, 10);

  const messages = await listMessages(auth, account, today);
  const [segments, capped] = summarise(messages);

  const services = await listV1(auth, `${MSG}/Services`, 'services');
  const brands = {};
  for (const svc of services) {
    const campaigns = await listV1(auth, `${MSG}/Services/${svc.sid}/Compliance/Usa2p`,
                                   'compliance');
    for (const campaign of campaigns) {
      const brandSid = campaign.brand_registration_sid;
      if (!brandSid || brandSid in brands) continue;
      brands[brandSid] = await get(auth, `${MSG}/a2p/BrandRegistrations/${brandSid}`);
      if (campaign.rate_limits) {
        console.log(`rate_limits on ${svc.sid}:`, campaign.rate_limits);
      }
    }
  }

  const sids = Object.keys(brands);
  if (sids.length === 0) {
    console.log('no A2P brands reachable from the Messaging Services on this account');
    return;
  }

  let bad = 0;
  for (const brandSid of sids) {
    const [derived, source] = brandCeiling(brands[brandSid]);
    const ceiling = supplied === null ? derived : supplied;
    const [state, detail] = verdict(ceiling, segments, capped);
    const line = `${state.padEnd(16)} ${brandSid}  ${detail}`;
    if (state === 'under-cap') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  ceiling: ${supplied === null ? source : 'supplied on the command line'}`);
    if (state === 'cap-hit' || state === 'over-estimate' || state === 'near-cap') {
      console.warn('  repair: the cap cannot be raised by API. Move the brand up ' +
                   'a tier (Sole Proprietor to Standard, then secondary vetting ' +
                   'to lift brand_score), or request a T-Mobile Special Business ' +
                   'Review through Twilio Support');
      console.warn("  repair: until then, spread the day's volume and shorten " +
                   'bodies, since the cap counts segments and a 160 character ' +
                   'overflow doubles the cost of every send');
    }
  }

  console.log(`${sids.length} brand(s), ${segments} segment(s) today, ${capped} capped`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth pinning down and neither needs a network. First that <code>summarise()</code> adds segments rather than counting messages, since <code>num_segments</code> arrives as a string and a four segment message spends four. Second that an observed <code>30023</code> is reported ahead of the estimate: the segment total covers every carrier, so the arithmetic is a bound and the error code is evidence.",
"test_py_file": "test_twilio_tmobile_daily_cap_report.py",
"test_py": '''from twilio_tmobile_daily_cap_report import brand_ceiling, summarise, verdict

SOLE_PROP = {"brand_type": "SOLE_PROPRIETOR", "brand_score": None}
RUSSELL = {"brand_type": "STANDARD", "russell_3000": True}
STANDARD = {"brand_type": "STANDARD", "brand_score": 62, "russell_3000": False}


def test_segments_are_summed_not_messages_counted():
    # Four messages, ten segments. Counting rows would report 40% of a 25 cap.
    messages = [{"num_segments": "4"}, {"num_segments": "1"},
                {"num_segments": "3"}, {"num_segments": "2"}]
    assert summarise(messages) == (10, 0)


def test_unreadable_segment_counts_do_not_abort_the_sum():
    assert summarise([{"num_segments": "2"}, {"num_segments": None},
                      {"num_segments": "x"}]) == (2, 0)


def test_30023_is_counted_client_side():
    messages = [{"num_segments": "1", "error_code": 30023},
                {"num_segments": "1", "error_code": "30023"},
                {"num_segments": "1", "error_code": 30007}]
    assert summarise(messages) == (3, 2)


def test_an_observed_cap_hit_outranks_the_estimate():
    # The segment total is an upper bound across all carriers. A 30023 is not.
    state, detail = verdict(200000, 12, capped=3)
    assert state == "cap-hit"
    assert "midnight US Pacific" in detail


def test_sole_proprietor_ceiling_is_derived_from_the_brand():
    ceiling, source = brand_ceiling(SOLE_PROP)
    assert ceiling == 1000
    assert "1,000 segments" in source


def test_russell_3000_defaults_to_two_hundred_thousand():
    assert brand_ceiling(RUSSELL)[0] == 200000


def test_an_ordinary_standard_brand_has_no_readable_ceiling():
    ceiling, source = brand_ceiling(STANDARD)
    assert ceiling is None
    assert "--ceiling" in source


def test_the_warning_band_sits_below_the_line():
    assert verdict(1000, 850, 0)[0] == "near-cap"
    assert verdict(1000, 400, 0)[0] == "under-cap"
    assert verdict(1000, 1200, 0)[0] == "over-estimate"
    assert verdict(None, 400, 0)[0] == "ceiling-unknown"
''',
"test_js_file": "twilio-tmobile-daily-cap-report.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { brandCeiling, summarise, verdict } from './twilio-tmobile-daily-cap-report.mjs';

const SOLE_PROP = { brand_type: 'SOLE_PROPRIETOR', brand_score: null };
const RUSSELL = { brand_type: 'STANDARD', russell_3000: true };
const STANDARD = { brand_type: 'STANDARD', brand_score: 62, russell_3000: false };

test('segments are summed, not messages counted', () => {
  const messages = [{ num_segments: '4' }, { num_segments: '1' },
                    { num_segments: '3' }, { num_segments: '2' }];
  assert.deepEqual(summarise(messages), [10, 0]);
});

test('unreadable segment counts do not abort the sum', () => {
  assert.deepEqual(summarise([{ num_segments: '2' }, { num_segments: null },
                              { num_segments: 'x' }]), [2, 0]);
});

test('30023 is counted client side', () => {
  const messages = [{ num_segments: '1', error_code: 30023 },
                    { num_segments: '1', error_code: '30023' },
                    { num_segments: '1', error_code: 30007 }];
  assert.deepEqual(summarise(messages), [3, 2]);
});

test('an observed cap hit outranks the estimate', () => {
  const [state, detail] = verdict(200000, 12, 3);
  assert.equal(state, 'cap-hit');
  assert.match(detail, /midnight US Pacific/);
});

test('sole proprietor ceiling is derived from the brand', () => {
  const [ceiling, source] = brandCeiling(SOLE_PROP);
  assert.equal(ceiling, 1000);
  assert.match(source, /1,000 segments/);
});

test('russell 3000 defaults to two hundred thousand', () => {
  assert.equal(brandCeiling(RUSSELL)[0], 200000);
});

test('an ordinary standard brand has no readable ceiling', () => {
  const [ceiling, source] = brandCeiling(STANDARD);
  assert.equal(ceiling, null);
  assert.match(source, /--ceiling/);
});

test('the warning band sits below the line', () => {
  assert.equal(verdict(1000, 850, 0)[0], 'near-cap');
  assert.equal(verdict(1000, 400, 0)[0], 'under-cap');
  assert.equal(verdict(1000, 1200, 0)[0], 'over-estimate');
  assert.equal(verdict(null, 400, 0)[0], 'ceiling-unknown');
});
''',
"faq": [
 ("Is this the same as the throughput limit that produces 30022?",
  "No. 30022 is messages per second: you sent too fast, and the same message succeeds a moment later. This is a total for the calendar day, held by T-Mobile against the brand, and once it is gone nothing succeeds until midnight Pacific no matter how slowly you send."),
 ("Why does the script say the segment total is an upper bound?",
  "Because the Messages list does not tell you which carrier a destination is on, so the T-Mobile share of the day's traffic cannot be separated from the rest. Total segments is therefore a ceiling on what was counted against the cap, which makes it a fair early warning and a poor precise measure."),
 ("Can I raise the cap?",
  "Not through the API. The paths are moving the brand up a tier, which for a Sole Proprietor means registering as Standard, and lifting brand_score through secondary vetting; or asking Twilio Support to file a T-Mobile Special Business Review. Both take time, so the operational lever is spreading volume."),
 ("Does the cap apply per campaign or per Messaging Service?",
  "Neither. It is enforced at the brand, so every campaign registered under one brand draws from the same daily allowance, including campaigns running on other platforms under the same registration. That is why a marketing send can exhaust the allowance for a transactional one."),
 ("Why does shortening the message body help?",
  "The cap counts segments. A GSM-7 body over 160 characters becomes two segments, and one that slips into UCS-2 through a smart quote or an emoji drops to 70 characters per segment. Trimming a template can halve what each send costs against the allowance."),
],
"related": [
 ("/twilio/a2p-throughput-exceeded-30022/", "30022 when sends outrun the assigned throughput"),
 ("/twilio/ucs2-segment-inflation/", "One character turns every message into three segments"),
 ("/twilio/a2p-brand-missing-secondary-vetting/", "An approved brand with no score is on the lowest tier"),
],
"citations": [CITE_30023, CITE_BRAND, CITE_USA2P, CITE_MSG],
},

{
"slug": "tollfree-edit-window-expiring",
"title": "A rejected toll-free record's edit window closes on a clock",
"description": "edit_allowed is true and edit_expiration is days out. Miss it and the in-place correction is gone: only a fresh submission, at the back of the queue.",
"h1": "a rejected toll-free record's edit window closes on a clock",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio edit_expiration tollfree", "toll-free verification edit window",
             "edit_allowed twilio", "tollfree rejected resubmit deadline",
             "twilio tollfree verification expired edit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The rejection came in ten days ago. Somebody read it, agreed the opt-in wording needed work, put it on the board, and the board is long. Nothing has broken since: the number was already blocked, the status has read <code>TWILIO_REJECTED</code> the whole time, and it will read that tomorrow too. What changes tomorrow is <code>edit_expiration</code>, and after it passes the correction that would have taken twenty minutes becomes a fresh submission at the back of a queue measured in weeks.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Tollfree/Verifications?Status=TWILIO_REJECTED</code> and, on each record, the two fields that are about time rather than about the rejection: <code>edit_allowed</code> and <code>edit_expiration</code>. Flag anything where <code>edit_allowed</code> is <code>true</code> and <code>edit_expiration</code> falls inside your alerting horizon.</p>
<p>Nothing here is about <em>why</em> it was rejected. This is a deadline check, and it should run on a schedule whether or not anyone has read the rejection yet.</p>""",
"problem": """<p>Every other toll-free finding announces itself by failing. This one has already failed: the number was blocked the moment the verification was rejected, and it stays blocked either way. So there is no new symptom to notice, no error rate that ticks up, and no moment where the situation gets worse in a way monitoring would see. It just gets more expensive to fix.</p>
<p>The console does not nag. The status does not change when the window closes &mdash; it reads <code>TWILIO_REJECTED</code> before and after &mdash; and <code>edit_allowed</code> is a field you have to go looking for. The whole loss is invisible: one day a correction is possible, the next it is not, and the only difference is a timestamp nobody was watching.</p>""",
"why": """<p><strong>The deadline is on a different clock from the work.</strong> Whoever owns the rejection is scheduling it against sprint capacity. The window is running against wall time from the moment of rejection, including the weekend and the week the owner was on leave. Those two clocks never meet unless something reads the field.</p>
<p><strong>It is a separate question from whether the rejection is fixable.</strong> Some rejection reasons can be corrected in place and some can never be, and that judgement takes a person reading <code>rejection_reasons</code>. The window closes at the same rate regardless. Keeping the two checks apart means the deadline still gets flagged while the reason is still being argued about.</p>
<p><strong>Missing it costs the queue, not the fee.</strong> An in-place correction goes back for review on the existing record. A fresh submission starts over, and toll-free review times are measured in weeks. On a number that is already blocked, that is weeks of a customer-facing sender staying dark for a wording change.</p>
<p><strong>The field and the clock can disagree.</strong> A record can read <code>edit_allowed: true</code> with an <code>edit_expiration</code> already in the past. Trusting the boolean there produces a confident report that the correction is available, followed by a rejected edit and a lost afternoon. Report the disagreement rather than picking a side.</p>""",
"steps": [
 {"h": "List the rejected verifications",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Tollfree/Verifications?Status=TWILIO_REJECTED</code>, following <code>meta.next_page_url</code>. The status filter is server side here, which is a change from the Messages list where error codes have to be filtered client side.</p>"""},
 {"h": "Read edit_allowed and edit_expiration, and nothing else",
  "body": """<p>Deliberately narrow. <code>rejection_reason</code>, <code>rejection_reasons</code> and <code>error_code</code> decide whether a correction can work, and that is a separate note and a separate conversation. This check is only about how long that conversation has left.</p>"""},
 {"h": "Distinguish absent from false",
  "body": """<p><code>edit_allowed</code> being <code>false</code> means the in-place path was never offered and a fresh submission is the only route. The field being absent from the response means something different: you have not learned that, and reporting it as closed would send somebody down the expensive path unnecessarily.</p>"""},
 {"h": "Treat an expiration in the past as authoritative",
  "body": """<p>When <code>edit_allowed</code> still reads <code>true</code> but <code>edit_expiration</code> has passed, report the disagreement and expect the edit to be refused. The timestamp is the thing the platform is enforcing; the boolean is a summary that can lag it.</p>"""},
 {"h": "Print the correction and the deadline together",
  "body": """<p>The repair is <code>POST https://messaging.twilio.com/v1/Tollfree/Verifications/{Sid}</code> with the corrected fields, before <code>edit_expiration</code>. In the console it is Phone Numbers, Manage, Active numbers, Regulatory Information, then edit and resubmit. Print the deadline next to the instruction so whoever reads the alert knows what it costs to defer it.</p>"""},
],
"verify": """<p>Re-run the script. Nothing should be inside the horizon with an open window.</p>
<pre><code class="language-bash">python3 twilio_tollfree_edit_window.py --horizon-hours 72
# 4 rejected verification(s), 0 closing inside 72 hours</code></pre>""",
"code_intro": "One paginated GET with a server-side status filter, and a classifier that takes the hours remaining as a number. That keeps the interesting cases testable without freezing a clock: inside the horizon, already past it while the boolean still says otherwise, never offered at all, and absent from the response, which is not the same as offered and declined.",
"py_file": "twilio_tollfree_edit_window.py",
"py": '''"""Flag rejected toll-free verifications whose edit window is about to close.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The correction itself needs a human who has
read the rejection reasons; this script only makes sure they still can.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_tollfree_edit_window")

MSG = "https://messaging.twilio.com/v1"

REJECTED = "TWILIO_REJECTED"


def parse_time(value):
    """Parse a messaging v1 timestamp. Pure.

    These come back as ISO 8601 with a trailing Z, which
    datetime.fromisoformat did not accept before Python 3.11.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(text)
    except ValueError:
        return None


def hours_left(edit_expiration, now):
    """Hours until the edit window closes. Negative once it has passed."""
    expires = parse_time(edit_expiration)
    if expires is None or now is None:
        return None
    return (expires - now).total_seconds() / 3600.0


def verdict(record, hours, horizon_hours=72.0):
    """Classify one rejected toll-free verification against its edit window.

    `hours` is the time remaining, or None. Taking it as an argument keeps the
    clock out of the classifier. Nothing here reads the rejection reasons: what
    can be corrected is a separate question from how long there is to do it.
    Returns (state, detail).
    """
    if not record:
        return ("no-record", "no verification to read.")

    status = str(record.get("status") or "").upper()
    if status != REJECTED:
        return ("not-rejected",
                "status is %s: there is no edit window on a record that has "
                "not been rejected." % (status or "unset"))

    allowed = record.get("edit_allowed")
    if allowed is None:
        return ("edit-allowed-unset",
                "rejected, and edit_allowed is absent from the response. That "
                "is not the same as false: nothing has been learned about the "
                "window, so do not file a fresh submission on this alone.")

    if not allowed:
        return ("no-edit-window",
                "rejected with edit_allowed false. The in-place correction was "
                "never on offer here, so a fresh submission is the only path "
                "and there is no deadline to race.")

    if hours is None:
        return ("expiration-unreadable",
                "rejected with edit_allowed true, and edit_expiration could "
                "not be parsed. Treat the window as closing and correct now.")

    if hours <= 0:
        return ("window-lapsed",
                "edit_expiration passed %.0f hours ago while edit_allowed "
                "still reads true. The timestamp is what the platform "
                "enforces, so expect the correction to be refused and plan on "
                "a fresh submission." % abs(hours))

    if hours <= horizon_hours:
        return ("closing",
                "%.0f hours left on the edit window. After that the in-place "
                "correction is gone and the only route is a fresh submission, "
                "back of the review queue." % hours)

    return ("open",
            "%.0f hours left on the edit window, outside the %.0f hour horizon."
            % (hours, horizon_hours))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=1000, **params):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--horizon-hours", type=float, default=72.0,
                    help="how close to the deadline counts as a finding")
    ap.add_argument("--max-records", type=int, default=500)
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
    now = datetime.datetime.now(datetime.timezone.utc)

    records = list_v1(session, MSG + "/Tollfree/Verifications",
                      "verifications", args.max_records, Status=REJECTED)
    if not records:
        log.info("no rejected toll-free verifications on this account")
        return 0

    bad = 0
    for rec in records:
        hours = hours_left(rec.get("edit_expiration"), now)
        state, detail = verdict(rec, hours, args.horizon_hours)
        name = rec.get("tollfree_phone_number_sid") or rec.get("sid") or "record"
        line = "%-22s %s  %s" % (state, name, detail)
        if state in ("open", "no-edit-window"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("closing", "expiration-unreadable"):
            log.warning("  repair: correct the named fields on %s/Tollfree/"
                        "Verifications/%s before %s, then resubmit. Console: "
                        "Phone Numbers, Manage, Active numbers, Regulatory "
                        "Information, edit and resubmit", MSG,
                        rec.get("sid", "{Sid}"),
                        rec.get("edit_expiration", "the expiration"))
        elif state == "window-lapsed":
            log.warning("  repair: file a fresh verification for this number "
                        "and expect the full review time; the in-place edit is "
                        "no longer available")

    log.info("%d rejected verification(s), %d closing inside %.0f hours",
             len(records), bad, args.horizon_hours)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-tollfree-edit-window.mjs",
"js": '''/**
 * Flag rejected toll-free verifications whose edit window is about to close.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The correction needs a human who
 * has read the rejection reasons; this only makes sure they still can.
 */
const MSG = 'https://messaging.twilio.com/v1';

const REJECTED = 'TWILIO_REJECTED';

/** Parse a messaging v1 ISO 8601 timestamp. Pure. Returns a Date or null. */
export function parseTime(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const t = Date.parse(text);
  return Number.isNaN(t) ? null : new Date(t);
}

/** Hours until the edit window closes. Negative once it has passed. */
export function hoursLeft(editExpiration, now) {
  const expires = parseTime(editExpiration);
  if (expires === null || !now) return null;
  return (expires.getTime() - now.getTime()) / 3600000;
}

/**
 * Classify one rejected toll-free verification against its edit window. `hours`
 * is the time remaining, or null; taking it as an argument keeps the clock out
 * of the classifier. Nothing here reads the rejection reasons. Pure.
 * Returns [state, detail].
 */
export function verdict(record, hours, horizonHours = 72.0) {
  if (!record) return ['no-record', 'no verification to read.'];

  const status = String(record.status ?? '').toUpperCase();
  if (status !== REJECTED) {
    return ['not-rejected',
      `status is ${status || 'unset'}: there is no edit window on a record ` +
      'that has not been rejected.'];
  }

  const allowed = record.edit_allowed;
  if (allowed === null || allowed === undefined) {
    return ['edit-allowed-unset',
      'rejected, and edit_allowed is absent from the response. That is not the ' +
      'same as false: nothing has been learned about the window, so do not ' +
      'file a fresh submission on this alone.'];
  }

  if (!allowed) {
    return ['no-edit-window',
      'rejected with edit_allowed false. The in-place correction was never on ' +
      'offer here, so a fresh submission is the only path and there is no ' +
      'deadline to race.'];
  }

  if (hours === null || hours === undefined) {
    return ['expiration-unreadable',
      'rejected with edit_allowed true, and edit_expiration could not be ' +
      'parsed. Treat the window as closing and correct now.'];
  }

  if (hours <= 0) {
    return ['window-lapsed',
      `edit_expiration passed ${Math.abs(hours).toFixed(0)} hours ago while ` +
      'edit_allowed still reads true. The timestamp is what the platform ' +
      'enforces, so expect the correction to be refused and plan on a fresh ' +
      'submission.'];
  }

  if (hours <= horizonHours) {
    return ['closing',
      `${hours.toFixed(0)} hours left on the edit window. After that the ` +
      'in-place correction is gone and the only route is a fresh submission, ' +
      'back of the review queue.'];
  }

  return ['open',
    `${hours.toFixed(0)} hours left on the edit window, outside the ` +
    `${horizonHours.toFixed(0)} hour horizon.`];
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
  let first = params;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50, ...first });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    first = {};
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
  const flag = process.argv.indexOf('--horizon-hours');
  const horizon = flag >= 0 ? Number(process.argv[flag + 1]) : 72.0;
  const now = new Date();

  const records = await listV1(auth, `${MSG}/Tollfree/Verifications`,
                               'verifications', 500, { Status: REJECTED });
  if (records.length === 0) {
    console.log('no rejected toll-free verifications on this account');
    return;
  }

  let bad = 0;
  for (const rec of records) {
    const hours = hoursLeft(rec.edit_expiration, now);
    const [state, detail] = verdict(rec, hours, horizon);
    const name = rec.tollfree_phone_number_sid ?? rec.sid ?? 'record';
    const line = `${state.padEnd(22)} ${name}  ${detail}`;
    if (state === 'open' || state === 'no-edit-window') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'closing' || state === 'expiration-unreadable') {
      console.warn(`  repair: correct the named fields on ${MSG}/Tollfree/` +
                   `Verifications/${rec.sid ?? '{Sid}'} before ` +
                   `${rec.edit_expiration ?? 'the expiration'}, then resubmit. ` +
                   'Console: Phone Numbers, Manage, Active numbers, Regulatory ' +
                   'Information, edit and resubmit');
    } else if (state === 'window-lapsed') {
      console.warn('  repair: file a fresh verification for this number and ' +
                   'expect the full review time; the in-place edit is no longer ' +
                   'available');
    }
  }

  console.log(`${records.length} rejected verification(s), ${bad} closing inside ` +
              `${horizon} hours`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Hours remaining is an argument, so the horizon boundary is one assertion and the lapsed case is another. The three that matter beyond the arithmetic are the ones where a careless reading costs real time: <code>edit_allowed</code> true over an expiration already in the past, <code>edit_allowed</code> false which has no deadline at all, and <code>edit_allowed</code> absent, which is not the same as false.",
"test_py_file": "test_twilio_tollfree_edit_window.py",
"test_py": '''import datetime

from twilio_tollfree_edit_window import hours_left, verdict

OPEN = {"sid": "HH01", "status": "TWILIO_REJECTED", "edit_allowed": True,
        "edit_expiration": "2026-09-02T00:00:00Z"}
NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)


def test_inside_the_horizon_is_the_finding():
    state, detail = verdict(OPEN, 40.0, horizon_hours=72.0)
    assert state == "closing"
    assert "back of the review queue" in detail


def test_outside_the_horizon_is_not_a_finding_yet():
    assert verdict(OPEN, 200.0, horizon_hours=72.0)[0] == "open"


def test_the_timestamp_wins_over_the_boolean():
    # edit_allowed can still read true after the expiration has passed.
    state, detail = verdict(OPEN, -12.0)
    assert state == "window-lapsed"
    assert "expect the correction to be refused" in detail


def test_edit_allowed_false_has_no_deadline_to_race():
    state, detail = verdict(dict(OPEN, edit_allowed=False), 40.0)
    assert state == "no-edit-window"
    assert "fresh submission is the only path" in detail


def test_an_absent_edit_allowed_is_not_read_as_false():
    rec = {"sid": "HH02", "status": "TWILIO_REJECTED"}
    state, detail = verdict(rec, 40.0)
    assert state == "edit-allowed-unset"
    assert "not the same as false" in detail


def test_an_unparseable_expiration_is_treated_as_urgent():
    state, _ = verdict(dict(OPEN, edit_expiration="soon"), None)
    assert state == "expiration-unreadable"


def test_records_that_were_not_rejected_are_skipped():
    state, _ = verdict({"status": "TWILIO_APPROVED", "edit_allowed": True}, 5.0)
    assert state == "not-rejected"


def test_hours_left_reads_the_trailing_z_timestamp():
    assert round(hours_left("2026-08-31T00:00:00Z", NOW)) == 24
    assert round(hours_left("2026-08-29T00:00:00Z", NOW)) == -24
    assert hours_left("not a date", NOW) is None
''',
"test_js_file": "twilio-tollfree-edit-window.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { hoursLeft, verdict } from './twilio-tollfree-edit-window.mjs';

const OPEN = {
  sid: 'HH01',
  status: 'TWILIO_REJECTED',
  edit_allowed: true,
  edit_expiration: '2026-09-02T00:00:00Z',
};
const NOW = new Date('2026-08-30T00:00:00Z');

test('inside the horizon is the finding', () => {
  const [state, detail] = verdict(OPEN, 40.0, 72.0);
  assert.equal(state, 'closing');
  assert.match(detail, /back of the review queue/);
});

test('outside the horizon is not a finding yet', () => {
  assert.equal(verdict(OPEN, 200.0, 72.0)[0], 'open');
});

test('the timestamp wins over the boolean', () => {
  const [state, detail] = verdict(OPEN, -12.0);
  assert.equal(state, 'window-lapsed');
  assert.match(detail, /expect the correction to be refused/);
});

test('edit_allowed false has no deadline to race', () => {
  const [state, detail] = verdict({ ...OPEN, edit_allowed: false }, 40.0);
  assert.equal(state, 'no-edit-window');
  assert.match(detail, /fresh submission is the only path/);
});

test('an absent edit_allowed is not read as false', () => {
  const [state, detail] = verdict({ sid: 'HH02', status: 'TWILIO_REJECTED' }, 40.0);
  assert.equal(state, 'edit-allowed-unset');
  assert.match(detail, /not the same as false/);
});

test('an unparseable expiration is treated as urgent', () => {
  assert.equal(verdict({ ...OPEN, edit_expiration: 'soon' }, null)[0],
               'expiration-unreadable');
});

test('records that were not rejected are skipped', () => {
  assert.equal(verdict({ status: 'TWILIO_APPROVED', edit_allowed: true }, 5.0)[0],
               'not-rejected');
});

test('hoursLeft reads the trailing z timestamp', () => {
  assert.equal(Math.round(hoursLeft('2026-08-31T00:00:00Z', NOW)), 24);
  assert.equal(Math.round(hoursLeft('2026-08-29T00:00:00Z', NOW)), -24);
  assert.equal(hoursLeft('not a date', NOW), null);
});
''',
"faq": [
 ("How is this different from reading the rejection itself?",
  "Reading the rejection tells you whether a correction can work at all, which needs a person looking at rejection_reasons and the use case. This tells you how long that person has. They are separate checks because the deadline keeps running while the reason is still being discussed."),
 ("What happens if the window closes?",
  "The record stays rejected and the number stays blocked. What you lose is the cheap path: instead of correcting fields on the existing verification, you file a new one and wait out the full toll-free review, which is measured in weeks rather than days."),
 ("Can edit_allowed be true after edit_expiration has passed?",
  "It can, and that is worth reporting as a disagreement rather than trusting either field alone. The timestamp is what the platform enforces. Reading only the boolean produces a report saying the correction is available, followed by an edit that is refused."),
 ("Should the script correct the record for me?",
  "No. Resubmitting a compliance record puts it back into review with whatever content the script had, and a wrong automatic edit burns the window it was supposed to protect. The alert names the resource, the fields and the deadline, and a person makes the change."),
 ("How often should this run?",
  "Daily is enough for a window measured in days, with the horizon set to whatever notice your team actually needs. Running it hourly does not help: the useful output is a reminder with enough lead time for someone to schedule the work, not a countdown."),
],
"related": [
 ("/twilio/tollfree-verification-rejected/", "A rejected toll-free verification is fixable or it is not"),
 ("/twilio/tollfree-number-not-verified/", "An unverified toll-free number is blocked outright"),
 ("/twilio/regulatory-bundle-expiring/", "An approved bundle counting down to expiry"),
],
"citations": [CITE_TFV, CITE_30032, CITE_TF_VERIFY, CITE_KEYS],
},

{
"slug": "link-shortening-cert-expiring",
"title": "A link shortening certificate expires and short links break",
"description": "A bring-your-own certificate on a link-shortening domain has a fixed date_expires and is not renewed for you. 30131 warns, then 30120 breaks the sends.",
"h1": "a link shortening certificate expires and short links break",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio link shortening certificate expired", "30131 link shortening",
             "twilio 30120 error", "link shortening domain date_expires",
             "twilio branded link tls"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The short domain in your messages is yours: <code>go.example.com</code>, in your brand, with a certificate somebody uploaded eighteen months ago and a calendar reminder that went to an address that no longer exists. Twilio does not renew it for you. When it expires, every shortened link in every message stops resolving, and the messages themselves start coming back <code>30120</code> while the click-through report goes flat.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/LinkShortening/Domains/{DomainSid}/Certificate</code> and flag any domain whose <code>date_expires</code> falls inside your renewal window, or whose <code>cert_in_validation</code> carries a <code>status</code> that is not validated.</p>
<p>Corroborate with <code>GET https://monitor.twilio.com/v1/Alerts</code>, keeping <code>error_code</code> in <code>30120</code>, <code>30129</code> and <code>30131</code>. The warning arrives before the failure does, which is the whole reason to read both.</p>""",
"problem": """<p>A branded short domain is a certificate you own, sitting in Twilio's infrastructure, doing TLS termination for links your customers click. It is a piece of PKI that lives outside every certificate renewal process your team has, because it is not on your load balancer, not in your certificate manager, and not on any host your monitoring can reach.</p>
<p>So it expires the way certificates expire when nobody owns them: silently, on a date chosen a year or two ago. The first symptom is a <code>30131</code> warning in the Debugger, which is logged at warning level and therefore missed by anything sweeping only errors. Then links start failing TLS in customers' browsers, and messages start returning <code>30120</code> or <code>30129</code>. By the time it is an incident, the fix is uploading a certificate, and the person who has it left.</p>""",
"why": """<p><strong>Twilio does not renew a certificate you brought.</strong> A domain on Twilio-managed certificates renews itself and never appears in this report. A bring-your-own certificate has a fixed <code>date_expires</code> and stays exactly as uploaded until somebody replaces it. Which mode a domain is in is the first thing worth knowing, and it is not obvious from the outside.</p>
<p><strong>The failure is on the click, not on the send.</strong> The message goes out with a link that no longer resolves, so the damage lands on a customer's phone rather than in your error rate, and it lands for every message already delivered as well as every new one. There is no retry that fixes a link somebody clicks tomorrow.</p>
<p><strong>The warning is at warning level.</strong> <code>30131</code> shows up before the hard failures, and a sweep of <code>LogLevel=error</code> alone will not see it. That is the free lead time on this problem, and it is routinely thrown away by monitoring that only looks at errors.</p>
<p><strong>A replacement in validation is not a replacement.</strong> Somebody uploading a new certificate does not end the problem; <code>cert_in_validation</code> has to reach a validated state. A live certificate three days from expiry with a replacement still validating is the combination worth paging on, and reading either field alone misses it.</p>""",
"steps": [
 {"h": "Read the certificate on each link-shortening domain",
  "body": """<p><code>GET https://messaging.twilio.com/v1/LinkShortening/Domains/{DomainSid}/Certificate</code>. There is no account-wide list of link-shortening domains being used here, so the domain SIDs are given to the script as arguments; take them from Console, Messaging, Link Shortening. Two or three of them is the usual number, and they change rarely enough to live in config.</p>"""},
 {"h": "Treat an empty response as a question, not a pass",
  "body": """<p>No certificate on the domain is what a Twilio-managed domain looks like from this endpoint: nothing to renew and nothing to watch. It is also what a misidentified SID looks like. The script reports it as unknown rather than clean, because a false all-clear on this is worse than a false alarm.</p>"""},
 {"h": "Measure date_expires against a real renewal window",
  "body": """<p>Thirty days is the usual window and it is a deliberate choice: it has to cover finding whoever holds the private key, issuing a replacement, uploading it, and the validation that follows. A seven day window on a certificate that takes a week to reissue is a window that does not exist.</p>"""},
 {"h": "Read cert_in_validation alongside the expiry",
  "body": """<p><code>cert_in_validation</code> describes a replacement that has been uploaded but not accepted. Combine it with the expiry rather than reporting either alone: a certificate expiring inside the window <em>with</em> a replacement still validating is the state that reads as handled and is not.</p>"""},
 {"h": "Corroborate against the alerts, at both log levels",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts</code> for <code>error_code</code> <code>30120</code>, <code>30129</code> and <code>30131</code>. Sweep <code>warning</code> as well as <code>error</code>, since <code>30131</code> is the early one. Alerts are retained for thirty days, so this corroborates a current problem and will not reconstruct one from last quarter.</p>"""},
],
"verify": """<p>Re-run the script. Every domain should report <code>current</code>, with no alerts in the corroborating sweep.</p>
<pre><code class="language-bash">python3 twilio_link_domain_cert_audit.py --domain-sid LD0123 --window-days 30
# 1 domain(s), 0 needing a certificate</code></pre>""",
"code_intro": "One read per domain SID plus one alerts sweep, and a classifier that takes days remaining as a number. The combination worth being careful about is the one the eye skips: a live certificate inside the renewal window while a replacement is still validating, which reads as handled from either field alone and is a separate state here.",
"py_file": "twilio_link_domain_cert_audit.py",
"py": '''"""Watch the certificate on a Twilio link-shortening domain for expiry.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Uploading a certificate is a change to how
your customers' links terminate TLS, so the replacement is printed and a person
performs it.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_link_domain_cert_audit")

MSG = "https://messaging.twilio.com/v1"
MONITOR = "https://monitor.twilio.com/v1"

# 30131 is the early warning and is logged at warning level; 30120 and 30129 are
# the hard failures. Sweeping only LogLevel=error throws the lead time away.
LINK_ERRORS = (30120, 30129, 30131)


def parse_time(value):
    """Parse a messaging v1 timestamp. Pure.

    These come back as ISO 8601 with a trailing Z, which
    datetime.fromisoformat did not accept before Python 3.11.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(text)
    except ValueError:
        return None


def days_left(date_expires, now):
    """Days until the certificate expires. Negative once it has passed."""
    expires = parse_time(date_expires)
    if expires is None or now is None:
        return None
    return (expires - now).total_seconds() / 86400.0


def validation_pending(cert):
    """True when a replacement has been uploaded and is not validated yet. Pure."""
    pending = (cert or {}).get("cert_in_validation")
    if not pending:
        return False
    return str(pending.get("status") or "").lower() != "validated"


def verdict(cert, days, window_days=30):
    """Classify one link-shortening domain certificate. Pure.

    `days` is the time remaining, or None. Taking it as an argument keeps the
    clock out of the classifier. Returns (state, detail).
    """
    if not cert:
        return ("no-certificate",
                "no certificate on this domain. That is what a Twilio-managed "
                "domain looks like from here, and also what a wrong domain sid "
                "looks like. Confirm which before treating it as clean.")

    pending = validation_pending(cert)

    if days is None:
        return ("expiry-unreadable",
                "a certificate is present and date_expires could not be read, "
                "so nothing can be said about when it lapses.")

    if days <= 0:
        return ("expired",
                "date_expires passed %.0f days ago. Shortened links are "
                "failing TLS in the browser and sends are returning 30120 or "
                "30129." % abs(days))

    if days <= window_days and pending:
        return ("expiring-replacement-validating",
                "%.0f days left, and cert_in_validation is not validated. A "
                "replacement has been uploaded but it is not live yet, so the "
                "clock is still running on the old one." % days)

    if days <= window_days:
        return ("expiring",
                "%.0f days left, inside the %d day renewal window. 30131 will "
                "appear first, at warning level." % (days, window_days))

    if pending:
        return ("validation-pending",
                "the live certificate has %.0f days left, but a replacement in "
                "cert_in_validation is not validated. Worth finishing rather "
                "than leaving half done." % days)

    return ("current", "%.0f days left on the certificate." % days)


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


def link_alerts(session, since, levels=("error", "warning"), limit=2000):
    """Alerts carrying a link-shortening error code, at both log levels.

    Alerts are retained 30 days, which bounds what this can corroborate.
    """
    found = []
    for level in levels:
        page = get(session, MONITOR + "/Alerts", LogLevel=level,
                   StartDate=since, PageSize=100)
        while page:
            for alert in page.get("alerts", []):
                try:
                    code = int(alert.get("error_code") or 0)
                except (TypeError, ValueError):
                    continue
                if code in LINK_ERRORS:
                    found.append(alert)
            nxt = (page.get("meta") or {}).get("next_page_url")
            if not nxt or len(found) >= limit:
                break
            page = get(session, nxt)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain-sid", action="append", default=[],
                    help="link-shortening domain sid; repeatable. From Console, "
                         "Messaging, Link Shortening")
    ap.add_argument("--window-days", type=int, default=30,
                    help="renewal window: long enough to find the key holder, "
                         "reissue, upload and validate")
    ap.add_argument("--alert-days", type=int, default=7)
    args = ap.parse_args()

    if not args.domain_sid:
        log.error("pass at least one --domain-sid; there is no account-wide "
                  "list of link-shortening domains read here")
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
    now = datetime.datetime.now(datetime.timezone.utc)
    since = (now - datetime.timedelta(days=args.alert_days)).date().isoformat()

    alerts = link_alerts(session, since)
    if alerts:
        codes = sorted({str(a.get("error_code")) for a in alerts})
        log.warning("%d link-shortening alert(s) in the last %d days, codes %s",
                    len(alerts), args.alert_days, ", ".join(codes))

    bad = 0
    for sid in args.domain_sid:
        cert = get(session, "%s/LinkShortening/Domains/%s/Certificate" % (MSG, sid))
        days = days_left((cert or {}).get("date_expires"), now)
        state, detail = verdict(cert, days, args.window_days)
        line = "%-32s %s  %s" % (state, sid, detail)
        if state == "current":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("expired", "expiring", "expiring-replacement-validating",
                     "expiry-unreadable"):
            log.warning("  repair: upload a fresh TlsCert to %s/LinkShortening/"
                        "Domains/%s/Certificate, or move the domain to "
                        "Twilio-managed certificates in Console, Messaging, "
                        "Link Shortening, which removes this clock entirely",
                        MSG, sid)
        elif state == "validation-pending":
            log.warning("  repair: finish validating the replacement on %s "
                        "rather than leaving two certificates half swapped", sid)

    log.info("%d domain(s), %d needing a certificate", len(args.domain_sid), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-link-domain-cert-audit.mjs",
"js": '''/**
 * Watch the certificate on a Twilio link-shortening domain for expiry.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The replacement is printed.
 */
const MSG = 'https://messaging.twilio.com/v1';
const MONITOR = 'https://monitor.twilio.com/v1';

// 30131 is the early warning and is logged at warning level; 30120 and 30129
// are the hard failures. Sweeping only LogLevel=error throws the lead time away.
export const LINK_ERRORS = [30120, 30129, 30131];

/** Parse a messaging v1 ISO 8601 timestamp. Pure. Returns a Date or null. */
export function parseTime(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const t = Date.parse(text);
  return Number.isNaN(t) ? null : new Date(t);
}

/** Days until the certificate expires. Negative once it has passed. */
export function daysLeft(dateExpires, now) {
  const expires = parseTime(dateExpires);
  if (expires === null || !now) return null;
  return (expires.getTime() - now.getTime()) / 86400000;
}

/** True when a replacement has been uploaded and is not validated yet. Pure. */
export function validationPending(cert) {
  const pending = (cert ?? {}).cert_in_validation;
  if (!pending) return false;
  return String(pending.status ?? '').toLowerCase() !== 'validated';
}

/**
 * Classify one link-shortening domain certificate. `days` is the time
 * remaining, or null; taking it as an argument keeps the clock out of the
 * classifier. Pure. Returns [state, detail].
 */
export function verdict(cert, days, windowDays = 30) {
  if (!cert) {
    return ['no-certificate',
      'no certificate on this domain. That is what a Twilio-managed domain ' +
      'looks like from here, and also what a wrong domain sid looks like. ' +
      'Confirm which before treating it as clean.'];
  }

  const pending = validationPending(cert);

  if (days === null || days === undefined) {
    return ['expiry-unreadable',
      'a certificate is present and date_expires could not be read, so nothing ' +
      'can be said about when it lapses.'];
  }

  if (days <= 0) {
    return ['expired',
      `date_expires passed ${Math.abs(days).toFixed(0)} days ago. Shortened ` +
      'links are failing TLS in the browser and sends are returning 30120 or 30129.'];
  }

  if (days <= windowDays && pending) {
    return ['expiring-replacement-validating',
      `${days.toFixed(0)} days left, and cert_in_validation is not validated. A ` +
      'replacement has been uploaded but it is not live yet, so the clock is ' +
      'still running on the old one.'];
  }

  if (days <= windowDays) {
    return ['expiring',
      `${days.toFixed(0)} days left, inside the ${windowDays} day renewal ` +
      'window. 30131 will appear first, at warning level.'];
  }

  if (pending) {
    return ['validation-pending',
      `the live certificate has ${days.toFixed(0)} days left, but a replacement ` +
      'in cert_in_validation is not validated. Worth finishing rather than ' +
      'leaving half done.'];
  }

  return ['current', `${days.toFixed(0)} days left on the certificate.`];
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

async function linkAlerts(auth, since, levels = ['error', 'warning'], limit = 2000) {
  const found = [];
  for (const level of levels) {
    let page = await get(auth, `${MONITOR}/Alerts`,
                         { LogLevel: level, StartDate: since, PageSize: 100 });
    while (page) {
      for (const alert of page.alerts ?? []) {
        const code = Number.parseInt(alert.error_code ?? 0, 10);
        if (LINK_ERRORS.includes(code)) found.push(alert);
      }
      const nxt = page.meta?.next_page_url;
      if (!nxt || found.length >= limit) break;
      page = await get(auth, nxt);
    }
  }
  return found;
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;

  const sids = [];
  for (let i = 0; i < process.argv.length - 1; i += 1) {
    if (process.argv[i] === '--domain-sid') sids.push(process.argv[i + 1]);
  }
  if (sids.length === 0) {
    console.error('pass at least one --domain-sid; there is no account-wide list ' +
                  'of link-shortening domains read here');
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
  const flag = process.argv.indexOf('--window-days');
  const windowDays = flag >= 0 ? Number(process.argv[flag + 1]) : 30;
  const now = new Date();
  const since = new Date(now.getTime() - 7 * 86400000).toISOString().slice(0, 10);

  const alerts = await linkAlerts(auth, since);
  if (alerts.length) {
    const codes = [...new Set(alerts.map((a) => String(a.error_code)))].sort();
    console.warn(`${alerts.length} link-shortening alert(s) in the last 7 days, ` +
                 `codes ${codes.join(', ')}`);
  }

  let bad = 0;
  for (const sid of sids) {
    const cert = await get(auth, `${MSG}/LinkShortening/Domains/${sid}/Certificate`);
    const days = daysLeft((cert ?? {}).date_expires, now);
    const [state, detail] = verdict(cert, days, windowDays);
    const line = `${state.padEnd(32)} ${sid}  ${detail}`;
    if (state === 'current') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'expired' || state === 'expiring' ||
        state === 'expiring-replacement-validating' || state === 'expiry-unreadable') {
      console.warn(`  repair: upload a fresh TlsCert to ${MSG}/LinkShortening/` +
                   `Domains/${sid}/Certificate, or move the domain to ` +
                   'Twilio-managed certificates in Console, Messaging, Link ' +
                   'Shortening, which removes this clock entirely');
    } else if (state === 'validation-pending') {
      console.warn(`  repair: finish validating the replacement on ${sid} rather ` +
                   'than leaving two certificates half swapped');
    }
  }

  console.log(`${sids.length} domain(s), ${bad} needing a certificate`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Days remaining is an argument, so the window boundary and the expired case are plain assertions. The pair worth writing down are the ones that look the same and are not: a certificate inside the renewal window with a replacement still validating, which must not read as handled, and a healthy certificate with a stalled replacement, which is untidy rather than urgent.",
"test_py_file": "test_twilio_link_domain_cert_audit.py",
"test_py": '''import datetime

from twilio_link_domain_cert_audit import days_left, validation_pending, verdict

CERT = {"date_expires": "2026-10-01T00:00:00Z"}
VALIDATING = dict(CERT, cert_in_validation={"status": "pending"})
VALIDATED = dict(CERT, cert_in_validation={"status": "validated"})
NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)


def test_inside_the_renewal_window_is_the_finding():
    state, detail = verdict(CERT, 12.0, window_days=30)
    assert state == "expiring"
    assert "30131" in detail


def test_outside_the_window_is_current():
    assert verdict(CERT, 120.0, window_days=30)[0] == "current"


def test_an_expired_certificate_names_both_failure_codes():
    state, detail = verdict(CERT, -3.0)
    assert state == "expired"
    assert "30120" in detail and "30129" in detail


def test_a_replacement_in_validation_does_not_stop_the_clock():
    # This is the state that reads as handled in a status meeting and is not.
    state, detail = verdict(VALIDATING, 4.0, window_days=30)
    assert state == "expiring-replacement-validating"
    assert "not live yet" in detail


def test_a_stalled_replacement_on_a_healthy_certificate_is_untidy_not_urgent():
    assert verdict(VALIDATING, 200.0)[0] == "validation-pending"


def test_a_validated_replacement_is_not_reported():
    assert verdict(VALIDATED, 200.0)[0] == "current"
    assert validation_pending(VALIDATED) is False


def test_no_certificate_is_reported_as_unknown_rather_than_clean():
    state, detail = verdict(None, None)
    assert state == "no-certificate"
    assert "wrong domain sid" in detail


def test_days_left_reads_the_trailing_z_timestamp():
    assert round(days_left("2026-09-06T00:00:00Z", NOW)) == 7
    assert round(days_left("2026-08-23T00:00:00Z", NOW)) == -7
    assert days_left("not a date", NOW) is None
''',
"test_js_file": "twilio-link-domain-cert-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { daysLeft, validationPending, verdict } from './twilio-link-domain-cert-audit.mjs';

const CERT = { date_expires: '2026-10-01T00:00:00Z' };
const VALIDATING = { ...CERT, cert_in_validation: { status: 'pending' } };
const VALIDATED = { ...CERT, cert_in_validation: { status: 'validated' } };
const NOW = new Date('2026-08-30T00:00:00Z');

test('inside the renewal window is the finding', () => {
  const [state, detail] = verdict(CERT, 12.0, 30);
  assert.equal(state, 'expiring');
  assert.match(detail, /30131/);
});

test('outside the window is current', () => {
  assert.equal(verdict(CERT, 120.0, 30)[0], 'current');
});

test('an expired certificate names both failure codes', () => {
  const [state, detail] = verdict(CERT, -3.0);
  assert.equal(state, 'expired');
  assert.match(detail, /30120/);
  assert.match(detail, /30129/);
});

test('a replacement in validation does not stop the clock', () => {
  const [state, detail] = verdict(VALIDATING, 4.0, 30);
  assert.equal(state, 'expiring-replacement-validating');
  assert.match(detail, /not live yet/);
});

test('a stalled replacement on a healthy certificate is untidy, not urgent', () => {
  assert.equal(verdict(VALIDATING, 200.0)[0], 'validation-pending');
});

test('a validated replacement is not reported', () => {
  assert.equal(verdict(VALIDATED, 200.0)[0], 'current');
  assert.equal(validationPending(VALIDATED), false);
});

test('no certificate is reported as unknown rather than clean', () => {
  const [state, detail] = verdict(null, null);
  assert.equal(state, 'no-certificate');
  assert.match(detail, /wrong domain sid/);
});

test('daysLeft reads the trailing z timestamp', () => {
  assert.equal(Math.round(daysLeft('2026-09-06T00:00:00Z', NOW)), 7);
  assert.equal(Math.round(daysLeft('2026-08-23T00:00:00Z', NOW)), -7);
  assert.equal(daysLeft('not a date', NOW), null);
});
''',
"faq": [
 ("Why does the script need me to pass the domain SIDs?",
  "Because it reads the certificate subresource of a specific domain rather than enumerating your link-shortening domains. Most accounts have one or two and they change rarely, so putting them in the job's config is honest and avoids the script guessing at an inventory it cannot see."),
 ("What if the domain uses Twilio-managed certificates?",
  "Then there is no bring-your-own certificate to expire and nothing here applies: renewal is handled for you. The script reports an empty certificate response as unknown rather than clean, because a mistyped domain SID looks identical and a false all-clear on this costs more than a false alarm."),
 ("Is 30131 an error or a warning?",
  "It is logged at warning level, which is exactly why it gets missed. Anything sweeping the Alerts API with LogLevel=error alone will see the hard failures, 30120 and 30129, and none of the notice that came first. Sweep both levels or give up the lead time."),
 ("What actually breaks when the certificate expires?",
  "The link in the message. Recipients get a TLS failure in their browser on every shortened link, including links in messages you sent weeks ago, and new sends start returning 30120 or 30129. Click-through goes to zero before anything in your own logs looks wrong."),
 ("How long should the renewal window be?",
  "Long enough to cover the slowest step, which is usually finding whoever holds the private key rather than the issuance. Thirty days is a reasonable default. A seven day window on a certificate that needs a week to reissue and validate leaves no room at all."),
],
"related": [
 ("/twilio/webhook-tls-certificate-expired-11236/", "An expired webhook certificate fails every request"),
 ("/twilio/regulatory-bundle-expiring/", "An approved bundle counting down to expiry"),
 ("/twilio/no-error-log-subscription/", "Alerts nobody is subscribed to"),
],
"citations": [CITE_LINKS, CITE_30120, CITE_30131, CITE_ALERTS],
},

]
