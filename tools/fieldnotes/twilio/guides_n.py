#!/usr/bin/env python3
"""/twilio/ field notes, batch N — the four other things an A2P brand does.

Batch C covered the brand that says FAILED and explains itself in errors[].
These four are the states either side of that: the brand that never answers at
all, the brand that answered and was later taken away, the one specific code
behind most Standard brand rejections, and the brand that is APPROVED and still
throttled. Every check is a GET with an API Key that has read access, and every
repair is printed rather than run, because these scripts hold a credential to an
account that can send messages and spend money.
"""

CITE_BRAND = ("BrandRegistration resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/brand-registration-resource")
CITE_VETTING = ("BrandVetting resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/brand-vetting-resource")
CITE_USA2P = ("UsAppToPerson resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/usapptoperson-resource")
CITE_PROFILES = ("Customer Profile resource — Twilio Docs",
                 "https://www.twilio.com/docs/trust-hub/trusthub-rest-api/customer-profile-resource")
CITE_30034 = ("Error 30034: message from an unregistered number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30034")
CITE_30033 = ("Error 30033: US A2P 10DLC campaign suspended — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30033")
CITE_30799 = ("Error 30799: unable to verify brand registration details — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30799")
CITE_FIX_BRANDS = (
    "Troubleshooting and rectifying A2P Standard and LVS brands — Twilio Docs",
    "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-and-rectifying-a2p-standardlvs-brands")
CITE_A2P = ("A2P 10DLC overview — Twilio Docs",
            "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "a2p-brand-stuck-pending-review",
"title": "An A2P brand parked at PENDING for weeks with no callback",
"description": "The brand never failed and never approved. status is PENDING or IN_REVIEW, tcr_id is null, and the status callback that was supposed to tell you was missed.",
"h1": "an A2P brand parked at PENDING for weeks with no callback",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio brand pending review", "brandregistration in_review stuck",
             "twilio tcr_id null", "a2p brand not approved",
             "10dlc brand taking weeks"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "There is no error to find. <code>errors[]</code> is empty, nothing is red in the console, and every US send still comes back <code>30034</code>. The brand was submitted five weeks ago, the status callback fired into a service that had not been deployed yet, and since then <code>status</code> has read <code>PENDING</code> with nobody looking at it.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code> and flag any item where <code>status</code> is <code>PENDING</code> or <code>IN_REVIEW</code> and <code>date_created</code> is more than about seven days old. Confirm with <code>tcr_id</code>, which stays <code>null</code> until The Campaign Registry accepts the brand, and with <code>brand_score</code>, which is <code>null</code> for the same reason.</p>
<p>The two waiting states are not the same waiting. <code>PENDING</code> means automated registry validation has not finished, which normally takes minutes; past a week it is stuck and worth a support ticket quoting the <code>BN…</code> SID. <code>IN_REVIEW</code> means a human is doing third-party vetting and there is nothing for you to do but wait.</p>""",
"problem": """<p>Every other A2P failure hands you something to read. A rejected brand has <code>errors[]</code>. A rejected campaign has a code and a <code>fields</code> array. This one has an empty object and a timestamp, which means the only evidence that anything is wrong is arithmetic: the difference between <code>date_created</code> and today.</p>
<p>That is exactly the kind of evidence a monitoring setup built around callbacks cannot produce. The integration registered the brand, wired a <code>status_callback</code>, and treated the absence of a callback as the absence of news. A callback delivered to a URL that returned 502, or to a service that was deployed the following week, is indistinguishable from a brand still being reviewed. So the brand sits, no campaign can attach to it, no number can be registered under a campaign that does not exist, and the launch date passes with the team debugging the send path.</p>""",
"why": """<p><strong>The waiting state has no failure signal by design.</strong> <code>PENDING</code> is the correct, healthy state for the first few minutes of a brand's life. There is no field that says "this has been pending too long", because how long is too long is a judgement about your launch, not about the resource. The script has to supply the threshold; the API will never volunteer it.</p>
<p><strong>Callbacks are the only notification and they are at-most-once in practice.</strong> A brand transition fires <code>status_callback</code> once. If your endpoint is down, mid-deploy, or behind a signature check that rejects it, the transition is still real and you simply do not hear about it. Polling one list endpoint removes the entire dependency.</p>
<p><strong>The send-side error says nothing about which layer is stuck.</strong> Traffic fails with <code>30034</code>, which reads the same for a brand awaiting review, a brand that was rejected, a campaign that never finished vetting and a number outside the sender pool. Four different waits, one code.</p>
<p><strong>The obvious workaround makes it worse.</strong> The instinct after two silent weeks is to register the brand again, which produces two brands on one EIN and gets the duplicate rejected with <code>30898</code>. Reporting the duplicates alongside the stall is what stops that, and duplicates are visible from the same list response.</p>""",
"steps": [
 {"h": "Page the brand list and keep date_created",
  "body": """<p><code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code>. This resource returns its items under <code>data</code> rather than a resource-named key, and <code>meta.next_page_url</code> is absolute. <code>date_created</code> is the timestamp everything here is measured against, so read it on every item rather than only on the ones that look interesting.</p>"""},
 {"h": "Separate PENDING from IN_REVIEW before you time either of them",
  "body": """<p><code>PENDING</code> is automated registry validation and usually resolves in minutes. <code>IN_REVIEW</code> is manual third-party vetting and legitimately takes days. Reporting them under one heading produces a list where the actionable rows and the rows you must not touch look identical.</p>"""},
 {"h": "Corroborate the status with tcr_id and brand_score",
  "body": """<p>Both are <code>null</code> while a brand is unapproved. A brand that says <code>PENDING</code> and carries a <code>tcr_id</code> is a disagreement between two fields on one object, and a script that reports it rather than resolving it is more useful than one that quietly trusts whichever field it happened to read first.</p>"""},
 {"h": "Flag brands sharing a Customer Profile bundle",
  "body": """<p><code>customer_profile_bundle_sid</code> appears on every brand. Two brands pointing at one bundle is the duplicate-registration mistake made visible in the same response that shows the stall, and it is worth reporting before somebody makes a third.</p>"""},
 {"h": "Open a ticket for PENDING, and only wait on IN_REVIEW",
  "body": """<p>There is no API repair for either. Past roughly seven days at <code>PENDING</code>, raise a Twilio Support ticket quoting the <code>BN…</code> SID. At <code>IN_REVIEW</code>, no customer action is required and resubmitting or re-registering only adds a duplicate to the queue.</p>"""},
],
"verify": """<p>Re-run the script. Nothing should be waiting past your threshold, and no two brands should share one Customer Profile bundle.</p>
<pre><code class="language-bash">python3 twilio_a2p_brand_stall_audit.py --stall-days 7
# 3 brand(s), 0 stalled in review</code></pre>""",
"code_intro": "One paginated GET and some arithmetic &mdash; an API Key with read access is all it needs. The classifier takes the brand and the current time as arguments rather than reading the clock itself, which is what makes \"this has been PENDING for nine days\" a testable statement instead of a thing that only happens on the day you run it.",
"py_file": "twilio_a2p_brand_stall_audit.py",
"py": '''"""Report A2P 10DLC brands that have been waiting for review too long.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_a2p_brand_stall_audit")

MSG = "https://messaging.twilio.com/v1"

# The two waiting states mean different things and want different responses, so
# they are never collapsed into one bucket anywhere in this script.
AUTOMATED = "PENDING"      # registry validation, normally minutes
MANUAL = "IN_REVIEW"       # third party vetting, legitimately days
SETTLED = ("APPROVED", "FAILED", "SUSPENDED")
DELETING = ("DELETION_PENDING", "DELETION_FAILED")


def parsed_time(value):
    """Parse a Twilio ISO 8601 timestamp into an aware datetime. Pure.

    Returns None when the field is absent or will not parse, because a brand
    with an unreadable date is a finding of its own rather than a brand that is
    zero days old.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def age_days(brand, now):
    """How many days ago the brand was created, or None. Pure."""
    when = parsed_time(brand.get("date_created"))
    if when is None:
        return None
    return (now - when).total_seconds() / 86400.0


def duplicate_bundles(brands):
    """Customer Profile bundles carrying more than one brand, sorted. Pure.

    Registering a second brand because the first went quiet is the usual
    response to a stall, and it is the one that gets rejected with 30898. The
    same list response that shows the stall shows the duplicate, so report both
    together or the reader will make the mistake this note exists to prevent.
    """
    counts = {}
    for brand in brands:
        bundle = str(brand.get("customer_profile_bundle_sid") or "").strip()
        if bundle:
            counts[bundle] = counts.get(bundle, 0) + 1
    return sorted(b for b, n in counts.items() if n > 1)


def verdict(brand, now, stall_days=7):
    """Classify one BrandRegistration against the clock. Pure, so a nine day
    stall is testable on any day of the year.

    Returns (state, detail).
    """
    status = str(brand.get("status") or "").upper()
    tcr = str(brand.get("tcr_id") or "").strip()
    age = age_days(brand, now)

    if status in SETTLED:
        return ("settled",
                "status is %s: this brand has a verdict, not a wait." % status)
    if status in DELETING:
        return ("deleting",
                "status is %s: on its way out, not waiting for review." % status)
    if status not in (AUTOMATED, MANUAL):
        return ("unknown-status",
                "status is %s, which this script does not recognise."
                % (status or "unset"))

    if tcr:
        return ("waiting-with-tcr-id",
                "status is %s but tcr_id is %s, which only an accepted brand "
                "should have. Two fields on one object disagree; report it "
                "rather than picking a side." % (status, tcr))

    if age is None:
        return ("undated",
                "status is %s and date_created is missing or unparseable, so "
                "there is no way to tell a fresh submission from a stall."
                % status)

    if age <= stall_days:
        if status == AUTOMATED:
            return ("pending",
                    "PENDING for %.1f day(s). Registry validation normally "
                    "finishes in minutes; this is still inside the window." % age)
        return ("in-review",
                "IN_REVIEW for %.1f day(s). A human is vetting it and no "
                "customer action is required." % age)

    if status == AUTOMATED:
        return ("pending-stalled",
                "PENDING for %.1f day(s), past the %d day threshold. Automated "
                "validation does not take this long; nothing here will change "
                "on its own." % (age, stall_days))
    return ("in-review-long",
            "IN_REVIEW for %.1f day(s). Still the correct state, still nothing "
            "to submit, but long enough to plan around rather than wait on."
            % age)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_brands(session, limit=500):
    """Page the brand list.

    This resource returns its items under `data`, not under a resource-named key
    like the rest of messaging v1. meta.next_page_url is absolute.
    """
    url = MSG + "/a2p/BrandRegistrations"
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get("data", []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stall-days", type=float, default=7.0,
                    help="how long a brand may wait before it is reported")
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

    brands = list_brands(session, args.max_brands)
    if not brands:
        log.info("no A2P brand registrations on this account")
        return 0

    now = datetime.now(timezone.utc)
    stalled = 0
    for brand in brands:
        state, detail = verdict(brand, now, args.stall_days)
        sid = brand.get("sid", "?")
        line = "%-19s %s  %s" % (state, sid, detail)
        if state in ("pending", "in-review", "settled", "deleting"):
            log.info(line)
            continue
        stalled += 1
        log.warning(line)
        if state == "pending-stalled":
            log.warning("  repair: none by API. Open a Twilio Support ticket "
                        "quoting brand %s. Do not register a second brand on the "
                        "same EIN, which is rejected with 30898", sid)
        elif state == "in-review-long":
            log.warning("  repair: none, and none wanted. Gate the launch on "
                        "status APPROVED and send US traffic over a verified "
                        "toll-free number until then")

    for bundle in duplicate_bundles(brands):
        stalled += 1
        log.warning("duplicate-bundle    %s  more than one brand points at this "
                    "Customer Profile. Duplicates on one EIN are rejected with "
                    "30898; keep the oldest and delete the rest", bundle)

    log.info("%d brand(s), %d stalled in review", len(brands), stalled)
    return 1 if stalled else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-brand-stall-audit.mjs",
"js": '''/**
 * Report A2P 10DLC brands that have been waiting for review too long.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MSG = 'https://messaging.twilio.com/v1';

// The two waiting states mean different things and want different responses.
const AUTOMATED = 'PENDING';   // registry validation, normally minutes
const MANUAL = 'IN_REVIEW';    // third party vetting, legitimately days
const SETTLED = ['APPROVED', 'FAILED', 'SUSPENDED'];
const DELETING = ['DELETION_PENDING', 'DELETION_FAILED'];

/**
 * Parse a Twilio ISO 8601 timestamp to epoch milliseconds, or null. Pure.
 * A brand with an unreadable date is a finding, not a brand zero days old.
 */
export function parsedTime(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : ms;
}

/** How many days ago the brand was created, or null. Pure. */
export function ageDays(brand, nowMs) {
  const when = parsedTime(brand.date_created);
  return when === null ? null : (nowMs - when) / 86400000;
}

/**
 * Customer Profile bundles carrying more than one brand, sorted. Pure.
 * Registering a second brand because the first went quiet is the usual response
 * to a stall, and it is the one rejected with 30898.
 */
export function duplicateBundles(brands) {
  const counts = new Map();
  for (const brand of brands) {
    const bundle = String(brand.customer_profile_bundle_sid ?? '').trim();
    if (bundle) counts.set(bundle, (counts.get(bundle) ?? 0) + 1);
  }
  return [...counts.entries()].filter(([, n]) => n > 1)
    .map(([b]) => b).sort();
}

/**
 * Classify one BrandRegistration against the clock. Pure, so a nine day stall
 * is testable on any day of the year. Returns [state, detail].
 */
export function verdict(brand, nowMs, stallDays = 7) {
  const status = String(brand.status ?? '').toUpperCase();
  const tcr = String(brand.tcr_id ?? '').trim();
  const age = ageDays(brand, nowMs);

  if (SETTLED.includes(status)) {
    return ['settled', `status is ${status}: this brand has a verdict, not a wait.`];
  }
  if (DELETING.includes(status)) {
    return ['deleting',
      `status is ${status}: on its way out, not waiting for review.`];
  }
  if (status !== AUTOMATED && status !== MANUAL) {
    return ['unknown-status',
      `status is ${status || 'unset'}, which this script does not recognise.`];
  }

  if (tcr) {
    return ['waiting-with-tcr-id',
      `status is ${status} but tcr_id is ${tcr}, which only an accepted brand ` +
      'should have. Two fields on one object disagree; report it rather than ' +
      'picking a side.'];
  }

  if (age === null) {
    return ['undated',
      `status is ${status} and date_created is missing or unparseable, so there ` +
      'is no way to tell a fresh submission from a stall.'];
  }

  if (age <= stallDays) {
    if (status === AUTOMATED) {
      return ['pending',
        `PENDING for ${age.toFixed(1)} day(s). Registry validation normally ` +
        'finishes in minutes; this is still inside the window.'];
    }
    return ['in-review',
      `IN_REVIEW for ${age.toFixed(1)} day(s). A human is vetting it and no ` +
      'customer action is required.'];
  }

  if (status === AUTOMATED) {
    return ['pending-stalled',
      `PENDING for ${age.toFixed(1)} day(s), past the ${stallDays} day ` +
      'threshold. Automated validation does not take this long; nothing here ' +
      'will change on its own.'];
  }
  return ['in-review-long',
    `IN_REVIEW for ${age.toFixed(1)} day(s). Still the correct state, still ` +
    'nothing to submit, but long enough to plan around rather than wait on.'];
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

/** Page the brand list. This resource returns items under `data`. */
export async function listBrands(auth, limit = 500) {
  let url = `${MSG}/a2p/BrandRegistrations`;
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, { PageSize: 50 });
    out.push(...(page.data ?? []));
    url = page.meta?.next_page_url ?? null;
  }
  return out.slice(0, limit);
}

async function main() {
  const stallDays = Number(process.env.STALL_DAYS ?? 7);
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

  const brands = await listBrands(auth);
  if (brands.length === 0) {
    console.log('no A2P brand registrations on this account');
    return;
  }

  const now = Date.now();
  let stalled = 0;
  for (const brand of brands) {
    const [state, detail] = verdict(brand, now, stallDays);
    const sid = brand.sid ?? '?';
    const line = `${state.padEnd(19)} ${sid}  ${detail}`;
    if (['pending', 'in-review', 'settled', 'deleting'].includes(state)) {
      console.log(line);
      continue;
    }
    stalled += 1;
    console.warn(line);
    if (state === 'pending-stalled') {
      console.warn(`  repair: none by API. Open a Twilio Support ticket quoting ` +
                   `brand ${sid}. Do not register a second brand on the same ` +
                   'EIN, which is rejected with 30898');
    } else if (state === 'in-review-long') {
      console.warn('  repair: none, and none wanted. Gate the launch on status ' +
                   'APPROVED and send US traffic over a verified toll-free ' +
                   'number until then');
    }
  }

  for (const bundle of duplicateBundles(brands)) {
    stalled += 1;
    console.warn(`duplicate-bundle    ${bundle}  more than one brand points at ` +
                 'this Customer Profile. Duplicates on one EIN are rejected with ' +
                 '30898; keep the oldest and delete the rest');
  }

  console.log(`${brands.length} brand(s), ${stalled} stalled in review`);
  process.exitCode = stalled ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones where a clock is involved: the same brand is fine on day two and a support ticket on day nine, and the classifier has to say so without reading the system clock. The other two are the brand whose <code>date_created</code> will not parse, which must not silently become zero days old, and <code>IN_REVIEW</code> past the threshold, which is reported but is still not something to act on.",
"test_py_file": "test_twilio_a2p_brand_stall_audit.py",
"test_py": '''from datetime import datetime, timezone

from twilio_a2p_brand_stall_audit import (age_days, duplicate_bundles,
                                          parsed_time, verdict)

NOW = datetime(2026, 3, 10, tzinfo=timezone.utc)


def brand(**kw):
    base = {"sid": "BN0123456789", "status": "PENDING",
            "date_created": "2026-03-09T12:00:00Z", "tcr_id": None}
    base.update(kw)
    return base


def test_pending_inside_the_window_is_not_a_finding():
    state, _ = verdict(brand(), NOW)
    assert state == "pending"


def test_the_same_brand_is_a_finding_nine_days_later():
    # Nothing about the object changes. Only the clock does, which is why the
    # classifier takes now as an argument instead of reading it.
    state, detail = verdict(brand(date_created="2026-03-01T00:00:00Z"), NOW)
    assert state == "pending-stalled"
    assert "9.0 day(s)" in detail


def test_in_review_past_the_threshold_is_reported_but_kept_separate():
    state, detail = verdict(
        brand(status="IN_REVIEW", date_created="2026-02-01T00:00:00Z"), NOW)
    assert state == "in-review-long"
    assert "nothing to submit" in detail


def test_an_unparseable_date_is_not_treated_as_zero_days_old():
    assert age_days(brand(date_created="last tuesday"), NOW) is None
    assert verdict(brand(date_created=""), NOW)[0] == "undated"


def test_a_naive_timestamp_is_read_as_utc():
    when = parsed_time("2026-03-09T12:00:00")
    assert when == datetime(2026, 3, 9, 12, tzinfo=timezone.utc)


def test_waiting_with_a_tcr_id_is_a_disagreement_not_a_wait():
    state, detail = verdict(brand(tcr_id="BXXXXXXX"), NOW)
    assert state == "waiting-with-tcr-id"
    assert "picking a side" in detail


def test_a_settled_brand_belongs_to_a_different_report():
    assert verdict(brand(status="FAILED"), NOW)[0] == "settled"
    assert verdict(brand(status="APPROVED"), NOW)[0] == "settled"


def test_two_brands_on_one_customer_profile_are_reported():
    brands = [brand(sid="BN1", customer_profile_bundle_sid="BU1"),
              brand(sid="BN2", customer_profile_bundle_sid="BU1"),
              brand(sid="BN3", customer_profile_bundle_sid="BU2")]
    assert duplicate_bundles(brands) == ["BU1"]


def test_brands_with_no_bundle_are_not_counted_as_duplicates_of_each_other():
    assert duplicate_bundles([brand(sid="BN1"), brand(sid="BN2")]) == []
''',
"test_js_file": "twilio-a2p-brand-stall-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageDays, duplicateBundles, parsedTime, verdict }
  from './twilio-a2p-brand-stall-audit.mjs';

const NOW = Date.parse('2026-03-10T00:00:00Z');

function brand(over = {}) {
  return { sid: 'BN0123456789', status: 'PENDING',
           date_created: '2026-03-09T12:00:00Z', tcr_id: null, ...over };
}

test('pending inside the window is not a finding', () => {
  assert.equal(verdict(brand(), NOW)[0], 'pending');
});

test('the same brand is a finding nine days later', () => {
  const [state, detail] = verdict(brand({ date_created: '2026-03-01T00:00:00Z' }),
                                  NOW);
  assert.equal(state, 'pending-stalled');
  assert.match(detail, /9\\.0 day\\(s\\)/);
});

test('in review past the threshold is reported but kept separate', () => {
  const [state, detail] = verdict(
    brand({ status: 'IN_REVIEW', date_created: '2026-02-01T00:00:00Z' }), NOW);
  assert.equal(state, 'in-review-long');
  assert.match(detail, /nothing to submit/);
});

test('an unparseable date is not treated as zero days old', () => {
  assert.equal(ageDays(brand({ date_created: 'last tuesday' }), NOW), null);
  assert.equal(verdict(brand({ date_created: '' }), NOW)[0], 'undated');
});

test('a valid timestamp parses to epoch milliseconds', () => {
  assert.equal(parsedTime('2026-03-09T12:00:00Z'),
               Date.parse('2026-03-09T12:00:00Z'));
});

test('waiting with a tcr_id is a disagreement, not a wait', () => {
  const [state, detail] = verdict(brand({ tcr_id: 'BXXXXXXX' }), NOW);
  assert.equal(state, 'waiting-with-tcr-id');
  assert.match(detail, /picking a side/);
});

test('a settled brand belongs to a different report', () => {
  assert.equal(verdict(brand({ status: 'FAILED' }), NOW)[0], 'settled');
  assert.equal(verdict(brand({ status: 'APPROVED' }), NOW)[0], 'settled');
});

test('two brands on one customer profile are reported', () => {
  assert.deepEqual(duplicateBundles([
    brand({ sid: 'BN1', customer_profile_bundle_sid: 'BU1' }),
    brand({ sid: 'BN2', customer_profile_bundle_sid: 'BU1' }),
    brand({ sid: 'BN3', customer_profile_bundle_sid: 'BU2' }),
  ]), ['BU1']);
});

test('brands with no bundle are not duplicates of each other', () => {
  assert.deepEqual(duplicateBundles([brand({ sid: 'BN1' }), brand({ sid: 'BN2' })]),
                   []);
});
''',
"faq": [
 ("How long is too long for a brand to sit at PENDING?",
  "PENDING is automated registry validation and normally completes in minutes. Twilio's own guidance treats more than seven days as abnormal, which is why the script defaults there and takes --stall-days so you can tighten it. IN_REVIEW is different: it is manual vetting and days are ordinary."),
 ("Is there any API call that speeds this up?",
  "No. There is no resubmit that helps a brand which has not been reviewed yet, and no field you can set to escalate. For PENDING past a week the only route is a Twilio Support ticket quoting the BN SID; for IN_REVIEW there is genuinely nothing to do."),
 ("Why does tcr_id matter if status already says PENDING?",
  "Because it is a second opinion from a different system. tcr_id is assigned by The Campaign Registry when it accepts the brand, and brand_score is populated later still. Both null alongside PENDING is a consistent story. A tcr_id present alongside PENDING is not, and that is worth surfacing rather than smoothing over."),
 ("Should I register a second brand while the first is stuck?",
  "No. Two brands on the same EIN get the duplicate rejected with 30898, and you now have two registrations to unpick instead of one stall to chase. The script reports brands sharing a Customer Profile bundle for exactly this reason."),
 ("We wired a status callback. Why poll at all?",
  "A brand transition fires the callback once. If the endpoint was down, mid-deploy, or rejecting the request behind a signature check, the transition still happened and you did not hear about it. A missed callback and an ongoing review look identical from your side; one GET tells them apart."),
],
"related": [
 ("/twilio/a2p-brand-registration-failed/", "A brand at FAILED explains itself in errors[]"),
 ("/twilio/a2p-campaign-stuck-in-progress/", "A campaign parked at IN_PROGRESS is not live"),
 ("/twilio/a2p-brand-missing-secondary-vetting/", "An approved brand with no trust score"),
],
"citations": [CITE_BRAND, CITE_FIX_BRANDS, CITE_30034, CITE_A2P],
},

{
"slug": "a2p-brand-suspended",
"title": "A SUSPENDED brand suspends every campaign underneath it",
"description": "Traffic that worked yesterday returns 30033 and the campaign reads SUSPENDED. The cause is one level up: the brand was suspended and the cascade is silent.",
"h1": "a SUSPENDED brand suspends every campaign underneath it",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio brand suspended", "30033 campaign suspended",
             "twilio 21731 21729", "a2p brand suspension cascade",
             "10dlc campaign suspended brand"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing was deployed. Nothing was edited. Yesterday's traffic delivered and today every US message comes back <code>30033</code> with <code>campaign_status</code> reading <code>SUSPENDED</code>. Editing the campaign returns <code>21729</code>, editing the brand returns <code>21731</code>, and the reason both refuse is that the suspension is not on the campaign at all.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code> and look for <code>status == \"SUSPENDED\"</code>. Then, for each Messaging Service, read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> and join on <code>brand_registration_sid</code>. A campaign whose <code>campaign_status</code> is <code>SUSPENDED</code> under a brand that is also <code>SUSPENDED</code> is a cascade, and the campaign is not the thing to fix.</p>
<p>The join is the whole check. Reading either resource alone gives you a suspended object with no way to tell whether it is the cause or the consequence, and those two readings lead to completely different weeks of work.</p>""",
"problem": """<p>The symptom arrives at the campaign level and the cause lives at the brand level, so the natural first move is the wrong one. A team sees <code>SUSPENDED</code> on the campaign, reads the campaign's <code>errors[]</code>, finds nothing new, and starts rewriting the description and the message samples. Every one of those edits is refused with <code>21729</code>, which is a permissions-shaped error rather than a diagnostic one, and none of them would have helped anyway.</p>
<p>Meanwhile the suspension is doing something the campaign view cannot show: it applies to every campaign attached to that brand. An account running one brand with four Messaging Services loses all four at once, and each one presents as its own outage. Without the join, four separate investigations start in parallel on four separate services for one cause.</p>""",
"why": """<p><strong>The error code is emitted per message, at the campaign.</strong> <code>30033</code> is documented as campaign suspended, so the code itself points down rather than up. Nothing in the message record mentions a brand, and the brand SID is not in the send path at all.</p>
<p><strong>Both write paths refuse, with different codes.</strong> <code>21731</code> on the brand and <code>21729</code> on the campaign. Two different numbers for one underlying condition reads like two unrelated problems, and neither says the word suspension.</p>
<p><strong>The cascade is not always visible in the same instant.</strong> The brand can read <code>SUSPENDED</code> while campaigns beneath it still read <code>VERIFIED</code>, because the campaign resource has not caught up. Sends fail regardless. A script that only looks for suspended campaigns misses the window where the brand is the only field telling the truth.</p>
<p><strong>Suspension is a compliance decision, not a fault.</strong> Campaign-to-traffic mismatch, complaint rate, prohibited content. There is no field to set and no resubmit that clears it, so the only useful output is an accurate statement of which layer was suspended and which campaigns it took with it.</p>""",
"steps": [
 {"h": "List the brands and note every SUSPENDED sid",
  "body": """<p><code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code>, items under <code>data</code>. Keep the <code>BN…</code> SIDs of anything at <code>SUSPENDED</code>; those are the keys the campaigns will be joined on.</p>"""},
 {"h": "Read every service's campaign, not only the ones that are failing",
  "body": """<p><code>GET /v1/Services/{ServiceSid}/Compliance/Usa2p</code> per Messaging Service. A brand suspension reaches services that nobody has reported yet, and finding them in the same pass is the difference between one incident and four.</p>"""},
 {"h": "Join on brand_registration_sid",
  "body": """<p>Each campaign object names the brand it was registered under. That field is the only link between the code your sends return and the object that actually changed state, and it is why this check reads both resources rather than one.</p>"""},
 {"h": "Report the direction, not just the status",
  "body": """<p>A suspended campaign under a healthy brand is a campaign-level suspension and belongs with the campaign notes. A suspended campaign under a suspended brand is a cascade. A suspended brand with campaigns still reading <code>VERIFIED</code> is the same cascade, seen before the campaign resource updated. Three findings, three different next steps.</p>"""},
 {"h": "Take the brand to Support, and leave the campaigns alone",
  "body": """<p>There is no API repair. Resolve the brand suspension with Twilio Support first; campaigns stay suspended until the brand clears, so editing or recreating them achieves nothing. Moving the same traffic onto a new brand or a new campaign is the response that risks the account itself.</p>"""},
],
"verify": """<p>Re-run the script. No brand should be <code>SUSPENDED</code>, and no campaign should be suspended under one.</p>
<pre><code class="language-bash">python3 twilio_a2p_brand_suspension_audit.py
# 2 brand(s), 6 campaign(s), 0 suspended</code></pre>""",
"code_intro": "Two reads and a join: the brand list once, then the campaign subresource per Messaging Service. The classifier is pure and takes a brand plus the campaigns already attributed to it, so the interesting part &mdash; which layer was suspended, and therefore which way the causation runs &mdash; is decided in a function with no network in it.",
"py_file": "twilio_a2p_brand_suspension_audit.py",
"py": '''"""Report A2P brand suspensions and the campaigns they take down with them.

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
log = logging.getLogger("twilio_a2p_brand_suspension_audit")

MSG = "https://messaging.twilio.com/v1"

SUSPENDED = "SUSPENDED"


def attached(campaigns, brand_sid):
    """The campaigns registered under one brand. Pure.

    brand_registration_sid on the campaign is the only link between the 30033
    your sends return and the object that actually changed state.
    """
    want = str(brand_sid or "").strip()
    if not want:
        return []
    return [c for c in campaigns
            if str(c.get("brand_registration_sid") or "").strip() == want]


def campaign_statuses(campaigns):
    """Upper-cased campaign_status for each campaign, in order. Pure."""
    return [str(c.get("campaign_status") or "").upper() for c in campaigns]


def verdict(brand, campaigns):
    """Classify one brand together with the campaigns attributed to it. Pure.

    The states differ by the direction of causation, not by which fields say
    SUSPENDED, because that direction is the only thing that changes what
    anybody should do next.

    Returns (state, detail).
    """
    status = str(brand.get("status") or "").upper()
    statuses = campaign_statuses(campaigns)
    hit = sum(1 for s in statuses if s == SUSPENDED)

    if status == SUSPENDED:
        if not campaigns:
            return ("brand-suspended-no-campaign",
                    "brand is SUSPENDED with no campaign attached. Nothing is "
                    "sending, and nothing can be registered under it.")
        if hit == len(statuses):
            return ("cascade",
                    "brand is SUSPENDED and all %d campaign(s) under it are "
                    "SUSPENDED too. Every US send on them returns 30033, and "
                    "the campaign is not the thing that changed." % len(statuses))
        if hit:
            return ("cascade-partial",
                    "brand is SUSPENDED; %d of %d campaign(s) already read "
                    "SUSPENDED. The rest are on the same brand and will follow."
                    % (hit, len(statuses)))
        return ("cascade-not-yet-visible",
                "brand is SUSPENDED while all %d campaign(s) still read %s. "
                "Sends fail regardless: the brand is the field telling the "
                "truth here." % (len(statuses), ", ".join(sorted(set(statuses)))))

    if hit:
        return ("campaign-suspended-only",
                "%d campaign(s) SUSPENDED under a brand that is %s. This one is "
                "campaign level, so the campaign's errors[] is where the reason "
                "is." % (hit, status or "unset"))

    if status == "APPROVED":
        return ("clean",
                "brand is APPROVED and none of its %d campaign(s) are suspended."
                % len(statuses))

    return ("brand-not-usable",
            "brand status is %s, which is not a suspension. Nothing here is "
            "being taken down; it never came up." % (status or "unset"))


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

    brands = list_v1(session, MSG + "/a2p/BrandRegistrations", "data",
                     args.max_brands)
    if not brands:
        log.info("no A2P brand registrations on this account")
        return 0

    # Every campaign on the account, tagged with the service it came from, so a
    # brand suspension is reported against the services it actually reaches.
    services = list_v1(session, MSG + "/Services", "services", args.max_services)
    campaigns = []
    for svc in services:
        for c in list_v1(session,
                         "%s/Services/%s/Compliance/Usa2p" % (MSG, svc["sid"]),
                         "compliance"):
            c = dict(c)
            c["_service"] = svc.get("friendly_name") or svc["sid"]
            campaigns.append(c)

    bad = 0
    for brand in brands:
        sid = brand.get("sid", "?")
        mine = attached(campaigns, sid)
        state, detail = verdict(brand, mine)
        line = "%-24s %s  %s" % (state, sid, detail)
        if state in ("clean", "brand-not-usable"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for c in mine:
            log.warning("  %s on %s (%s)", c.get("campaign_status", "?"),
                        c.get("_service", "?"), c.get("sid", "QE..."))
        if state.startswith("cascade") or state == "brand-suspended-no-campaign":
            log.warning("  repair: none by API. Take brand %s to Twilio Support; "
                        "campaigns stay suspended until the brand clears. Do not "
                        "move the traffic to a new brand or campaign", sid)
        elif state == "campaign-suspended-only":
            log.warning("  repair: read errors[] on the campaign; the brand above "
                        "it is not the cause")

    log.info("%d brand(s), %d campaign(s), %d suspended",
             len(brands), len(campaigns), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-brand-suspension-audit.mjs",
"js": '''/**
 * Report A2P brand suspensions and the campaigns they take down with them.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MSG = 'https://messaging.twilio.com/v1';

const SUSPENDED = 'SUSPENDED';

/**
 * The campaigns registered under one brand. Pure. brand_registration_sid is the
 * only link between the 30033 your sends return and the object that changed.
 */
export function attached(campaigns, brandSid) {
  const want = String(brandSid ?? '').trim();
  if (!want) return [];
  return campaigns.filter(
    (c) => String(c.brand_registration_sid ?? '').trim() === want);
}

/** Upper-cased campaign_status for each campaign, in order. Pure. */
export function campaignStatuses(campaigns) {
  return campaigns.map((c) => String(c.campaign_status ?? '').toUpperCase());
}

/**
 * Classify one brand together with the campaigns attributed to it. Pure. The
 * states differ by the direction of causation, not by which fields say
 * SUSPENDED. Returns [state, detail].
 */
export function verdict(brand, campaigns) {
  const status = String(brand.status ?? '').toUpperCase();
  const statuses = campaignStatuses(campaigns);
  const hit = statuses.filter((s) => s === SUSPENDED).length;

  if (status === SUSPENDED) {
    if (campaigns.length === 0) {
      return ['brand-suspended-no-campaign',
        'brand is SUSPENDED with no campaign attached. Nothing is sending, and ' +
        'nothing can be registered under it.'];
    }
    if (hit === statuses.length) {
      return ['cascade',
        `brand is SUSPENDED and all ${statuses.length} campaign(s) under it are ` +
        'SUSPENDED too. Every US send on them returns 30033, and the campaign ' +
        'is not the thing that changed.'];
    }
    if (hit) {
      return ['cascade-partial',
        `brand is SUSPENDED; ${hit} of ${statuses.length} campaign(s) already ` +
        'read SUSPENDED. The rest are on the same brand and will follow.'];
    }
    const seen = [...new Set(statuses)].sort().join(', ');
    return ['cascade-not-yet-visible',
      `brand is SUSPENDED while all ${statuses.length} campaign(s) still read ` +
      `${seen}. Sends fail regardless: the brand is the field telling the ` +
      'truth here.'];
  }

  if (hit) {
    return ['campaign-suspended-only',
      `${hit} campaign(s) SUSPENDED under a brand that is ${status || 'unset'}. ` +
      "This one is campaign level, so the campaign's errors[] is where the " +
      'reason is.'];
  }

  if (status === 'APPROVED') {
    return ['clean',
      `brand is APPROVED and none of its ${statuses.length} campaign(s) are ` +
      'suspended.'];
  }

  return ['brand-not-usable',
    `brand status is ${status || 'unset'}, which is not a suspension. Nothing ` +
    'here is being taken down; it never came up.'];
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

  const brands = await listV1(auth, `${MSG}/a2p/BrandRegistrations`, 'data');
  if (brands.length === 0) {
    console.log('no A2P brand registrations on this account');
    return;
  }

  const services = await listV1(auth, `${MSG}/Services`, 'services');
  const campaigns = [];
  for (const svc of services) {
    const found = await listV1(
      auth, `${MSG}/Services/${svc.sid}/Compliance/Usa2p`, 'compliance');
    for (const c of found) {
      campaigns.push({ ...c, _service: svc.friendly_name ?? svc.sid });
    }
  }

  let bad = 0;
  for (const brand of brands) {
    const sid = brand.sid ?? '?';
    const mine = attached(campaigns, sid);
    const [state, detail] = verdict(brand, mine);
    const line = `${state.padEnd(24)} ${sid}  ${detail}`;
    if (state === 'clean' || state === 'brand-not-usable') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    for (const c of mine) {
      console.warn(`  ${c.campaign_status ?? '?'} on ${c._service ?? '?'} ` +
                   `(${c.sid ?? 'QE...'})`);
    }
    if (state.startsWith('cascade') || state === 'brand-suspended-no-campaign') {
      console.warn(`  repair: none by API. Take brand ${sid} to Twilio Support; ` +
                   'campaigns stay suspended until the brand clears. Do not move ' +
                   'the traffic to a new brand or campaign');
    } else if (state === 'campaign-suspended-only') {
      console.warn('  repair: read errors[] on the campaign; the brand above it ' +
                   'is not the cause');
    }
  }

  console.log(`${brands.length} brand(s), ${campaigns.length} campaign(s), ` +
              `${bad} suspended`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every case here is about direction. The same word on two resources means a cascade one way round and a campaign problem the other, and the case worth being most careful with is the brand that is already <code>SUSPENDED</code> while its campaigns still read <code>VERIFIED</code> &mdash; sends are failing, and a check that only looks for suspended campaigns reports the account as healthy.",
"test_py_file": "test_twilio_a2p_brand_suspension_audit.py",
"test_py": '''from twilio_a2p_brand_suspension_audit import attached, verdict

BRAND = {"sid": "BN0123456789", "status": "SUSPENDED"}
OK_BRAND = {"sid": "BN0123456789", "status": "APPROVED"}


def campaign(status, brand_sid="BN0123456789", sid="QE1"):
    return {"sid": sid, "campaign_status": status,
            "brand_registration_sid": brand_sid}


def test_suspended_brand_over_suspended_campaigns_is_a_cascade():
    state, detail = verdict(BRAND, [campaign("SUSPENDED")])
    assert state == "cascade"
    assert "30033" in detail


def test_suspended_brand_with_verified_campaigns_is_still_the_brands_fault():
    # The campaign resource has not caught up. Sends fail anyway, and a check
    # that only looks for suspended campaigns calls this account healthy.
    state, detail = verdict(BRAND, [campaign("VERIFIED")])
    assert state == "cascade-not-yet-visible"
    assert "telling the truth" in detail


def test_a_partly_updated_cascade_says_how_many():
    state, detail = verdict(BRAND, [campaign("SUSPENDED", sid="QE1"),
                                    campaign("VERIFIED", sid="QE2")])
    assert state == "cascade-partial"
    assert "1 of 2" in detail


def test_suspended_campaign_under_a_healthy_brand_is_campaign_level():
    state, detail = verdict(OK_BRAND, [campaign("SUSPENDED")])
    assert state == "campaign-suspended-only"
    assert "errors[]" in detail


def test_a_suspended_brand_with_nothing_attached_is_still_reported():
    assert verdict(BRAND, [])[0] == "brand-suspended-no-campaign"


def test_an_approved_brand_with_verified_campaigns_is_clean():
    assert verdict(OK_BRAND, [campaign("VERIFIED")])[0] == "clean"


def test_a_failed_brand_is_not_a_suspension():
    state, detail = verdict({"sid": "BN1", "status": "FAILED"}, [])
    assert state == "brand-not-usable"
    assert "never came up" in detail


def test_campaigns_are_attributed_by_brand_registration_sid():
    pool = [campaign("SUSPENDED", "BN1", "QE1"), campaign("VERIFIED", "BN2", "QE2")]
    assert [c["sid"] for c in attached(pool, "BN1")] == ["QE1"]


def test_a_blank_brand_sid_attributes_nothing():
    assert attached([campaign("SUSPENDED", "", "QE1")], "") == []
''',
"test_js_file": "twilio-a2p-brand-suspension-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attached, verdict }
  from './twilio-a2p-brand-suspension-audit.mjs';

const BRAND = { sid: 'BN0123456789', status: 'SUSPENDED' };
const OK_BRAND = { sid: 'BN0123456789', status: 'APPROVED' };

function campaign(status, brandSid = 'BN0123456789', sid = 'QE1') {
  return { sid, campaign_status: status, brand_registration_sid: brandSid };
}

test('suspended brand over suspended campaigns is a cascade', () => {
  const [state, detail] = verdict(BRAND, [campaign('SUSPENDED')]);
  assert.equal(state, 'cascade');
  assert.match(detail, /30033/);
});

test('suspended brand with verified campaigns is still the brand', () => {
  const [state, detail] = verdict(BRAND, [campaign('VERIFIED')]);
  assert.equal(state, 'cascade-not-yet-visible');
  assert.match(detail, /telling the truth/);
});

test('a partly updated cascade says how many', () => {
  const [state, detail] = verdict(BRAND, [campaign('SUSPENDED', 'BN0123456789', 'QE1'),
                                          campaign('VERIFIED', 'BN0123456789', 'QE2')]);
  assert.equal(state, 'cascade-partial');
  assert.match(detail, /1 of 2/);
});

test('suspended campaign under a healthy brand is campaign level', () => {
  const [state, detail] = verdict(OK_BRAND, [campaign('SUSPENDED')]);
  assert.equal(state, 'campaign-suspended-only');
  assert.match(detail, /errors\\[\\]/);
});

test('a suspended brand with nothing attached is still reported', () => {
  assert.equal(verdict(BRAND, [])[0], 'brand-suspended-no-campaign');
});

test('an approved brand with verified campaigns is clean', () => {
  assert.equal(verdict(OK_BRAND, [campaign('VERIFIED')])[0], 'clean');
});

test('a failed brand is not a suspension', () => {
  const [state, detail] = verdict({ sid: 'BN1', status: 'FAILED' }, []);
  assert.equal(state, 'brand-not-usable');
  assert.match(detail, /never came up/);
});

test('campaigns are attributed by brand_registration_sid', () => {
  const pool = [campaign('SUSPENDED', 'BN1', 'QE1'),
                campaign('VERIFIED', 'BN2', 'QE2')];
  assert.deepEqual(attached(pool, 'BN1').map((c) => c.sid), ['QE1']);
});

test('a blank brand sid attributes nothing', () => {
  assert.deepEqual(attached([campaign('SUSPENDED', '', 'QE1')], ''), []);
});
''',
"faq": [
 ("How do I tell a brand suspension from a campaign suspension?",
  "By joining them. The campaign object carries brand_registration_sid; look up that BN SID in the brand list. Campaign SUSPENDED under brand SUSPENDED is a cascade and the brand is the cause. Campaign SUSPENDED under an APPROVED brand is campaign level, and that campaign's errors[] holds the reason."),
 ("Why do my edits fail with 21731 and 21729?",
  "Because a suspended object is frozen. 21731 refuses an update to a suspended brand and 21729 refuses one to a suspended campaign. They are two codes for the same underlying condition, and neither of them says the word suspension, which is why they read like unrelated permission problems."),
 ("Can I move the traffic to a new brand or campaign while this is resolved?",
  "No. Re-registering the same traffic under a fresh brand to route around a suspension is treated as evasion and puts the whole account at risk. The suspension is a compliance decision about the traffic, and the traffic has not changed by moving it."),
 ("The brand says SUSPENDED but the campaign still says VERIFIED. Which is right?",
  "Both, briefly. The brand transitioned and the campaign resource has not caught up. Sends fail either way, so treat the brand as the truth. This is the exact window in which a check written only against campaign_status reports a healthy account during an outage."),
 ("Does a brand suspension affect toll-free or short code traffic?",
  "No. A2P 10DLC brands and campaigns govern US long code traffic, so toll-free and short code senders keep working. That is the usual stopgap while the suspension is being resolved, provided the toll-free number is itself verified."),
],
"related": [
 ("/twilio/a2p-campaign-vetting-failed/", "A campaign is FAILED and errors[] names the field"),
 ("/twilio/a2p-brand-registration-failed/", "A brand at FAILED blocks every campaign"),
 ("/twilio/tollfree-number-not-verified/", "An unverified toll-free number blocks US SMS"),
],
"citations": [CITE_BRAND, CITE_USA2P, CITE_30033, CITE_FIX_BRANDS],
},

{
"slug": "a2p-brand-tax-id-legal-name-mismatch",
"title": "Brand failed 30799: the EIN does not match the legal name",
"description": "The commonest Standard brand rejection. TCR checks the EIN against public tax records and needs an exact match, so a DBA or an old address fails it.",
"h1": "brand failed 30799: the EIN does not match the legal name",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30799", "brand registration ein mismatch",
             "business_registration_identifier twilio",
             "a2p legal name mismatch", "trust hub customer profile ein"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The company has traded under one name since 2019 and everybody, including the people who filled in the registration, calls it that. The IRS calls it something else, ending in <code>, Inc.</code>, and The Campaign Registry only reads the IRS. That single disagreement is <code>30799</code>, and it is the reason behind most Standard brand rejections.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}</code> and look in <code>errors[]</code> for <code>30799</code>. Each entry carries <code>code</code>, <code>description</code>, <code>fields</code> and <code>url</code>; <code>fields</code> names the attributes the registry objected to.</p>
<p>The edit does not happen on the brand. The brand is assembled from the Trust Hub Customer Profile named in <code>customer_profile_bundle_sid</code>, so read that bundle's business End-User with <code>GET https://trusthub.twilio.com/v1/CustomerProfiles/{BundleSid}/EntityAssignments</code>, correct the legal name, address and <code>business_registration_identifier</code> there to match the IRS or CRA record exactly, and only then resubmit the brand.</p>""",
"problem": """<p><code>30799</code> is the least specific-sounding of the brand codes &mdash; "unable to verify registration details" &mdash; and it is the most specific in practice. The registry is doing one thing: taking the tax identifier you supplied and looking it up against public records, then requiring that the legal name and address on that record match what you sent. It is a string comparison against a government database, and it does not know about trading names.</p>
<p>So the rejection lands on a brand that everybody involved believes is correct, and the natural response is to resubmit it. There are three free resubmissions before <code>21724</code> starts refusing them, and a resubmission of the same Customer Profile produces the same lookup and the same answer. The information that would have stopped that round trip is the <code>fields</code> array, which names whether the objection was to the identifier, the name or the address.</p>""",
"why": """<p><strong>The name people use is not the name on the record.</strong> A DBA, a shortened form, a dropped <code>LLC</code> or <code>Inc.</code>, a merged entity still trading under the acquired brand: all of them are the real company and none of them is what the IRS has on file. The registry compares against the file.</p>
<p><strong>The identifier is often the wrong kind of number.</strong> A sole trader supplying an SSN where an EIN is required, a Canadian company supplying a provincial number rather than the federal BN, a public company whose ticker cannot be verified. Each fails as an identity mismatch, and none of them looks wrong on inspection.</p>
<p><strong>Government and nonprofit brands fail the same way for a different reason.</strong> A nonprofit with the wrong 501(c) subsection code, or an entity registered with the wrong <code>company_type</code>, produces the same code from the same lookup. The fix is still a Customer Profile edit, just on a different attribute.</p>
<p><strong>The object you edit is not the object that failed.</strong> The error is on the brand; the data is on the Trust Hub Customer Profile bundle. Editing anything on the brand itself changes nothing, which makes the first attempt at a fix feel like the API is ignoring you.</p>""",
"steps": [
 {"h": "Fetch the brand and read errors[] for 30799",
  "body": """<p><code>GET /v1/a2p/BrandRegistrations/{BrandSid}</code>. Note that the brand resource spells the key <code>code</code> where the campaign resource spells it <code>error_code</code>; read both or you will report every rejection as unrecognised. Ignore <code>failure_reason</code> and <code>brand_feedback</code>, which are deprecated.</p>"""},
 {"h": "Take the objection from fields, not from the description",
  "body": """<p><code>fields</code> is a list of the attributes that triggered the code. It is the difference between re-checking three things and re-checking one. When it is absent, fall back to the identity triple &mdash; legal company name, registered address and <code>business_registration_identifier</code> &mdash; because those are what the lookup compares.</p>"""},
 {"h": "Follow customer_profile_bundle_sid to the data that actually failed",
  "body": """<p><code>GET https://trusthub.twilio.com/v1/CustomerProfiles/{BundleSid}/EntityAssignments</code> lists the End-User and supporting document objects attached to the profile. The business End-User holds the name, address and registration identifier that were submitted, and it is the object somebody has to edit.</p>"""},
 {"h": "Separate 30799 from the other reasons a brand can fail",
  "body": """<p>A brand can be <code>FAILED</code> for reasons that have nothing to do with identity, and those want a different page and a different fix. Reporting "failed" for both wastes the reader's time on the wrong bundle; reporting the code and the named fields does not.</p>"""},
 {"h": "Correct the profile, then resubmit once",
  "body": """<p>Console &rarr; Trust Hub &rarr; Customer Profiles, edit the business End-User so legal name, address and identifier match the IRS or CRA record character for character, then resubmit the brand. Three resubmissions are free and a fourth returns <code>21724</code>, so spend them on a change you have verified rather than on a guess.</p>"""},
],
"verify": """<p>Re-run the script. No brand should be carrying <code>30799</code>, and every approved brand should have an identity status above self-declared.</p>
<pre><code class="language-bash">python3 twilio_a2p_brand_identity_audit.py
# 2 brand(s), 0 with an identity mismatch</code></pre>""",
"code_intro": "One paginated GET over the brands, and the Customer Profile bundle SID printed rather than followed &mdash; the repair is a human editing a business record, and no script should be doing that on a schedule. The classifier is pure and singles out <code>30799</code>, because a report that says only \"failed\" sends the reader to re-check the whole profile when the API already named the field.",
"py_file": "twilio_a2p_brand_identity_audit.py",
"py": '''"""Report A2P brands rejected because the tax ID and legal name disagree.

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
log = logging.getLogger("twilio_a2p_brand_identity_audit")

MSG = "https://messaging.twilio.com/v1"
TRUSTHUB = "https://trusthub.twilio.com/v1"

MISMATCH = "30799"

# What the registry actually compares when it resolves a tax identifier against
# public records. Used only when errors[] names no fields, so the report still
# says where to look instead of saying "failed".
IDENTITY_TRIPLE = ("legal company name", "registered business address",
                   "business_registration_identifier")

# An APPROVED brand can still be carrying an identity that was never checked
# against anything external, which is a weaker position than it looks.
WEAK_IDENTITY = ("SELF_DECLARED", "UNVERIFIED")


def error_code(err):
    """Read the code off one errors[] entry, as a string.

    The brand resource spells the key code and the campaign resource spells it
    error_code. Reading both costs one loop and removes a whole class of silent
    misreport.
    """
    for k in ("error_code", "code"):
        v = err.get(k)
        if v not in (None, ""):
            return str(v)
    return ""


def edit_targets(errors):
    """What to correct on the Customer Profile, from the 30799 entries. Pure.

    Prefers what the API named in `fields`, because that is one thing to check
    rather than three. Falls back to the identity triple only when the entry
    named nothing, so the report is never reduced to the word "failed".
    """
    named = []
    saw_mismatch = False
    for err in errors:
        if error_code(err) != MISMATCH:
            continue
        saw_mismatch = True
        for f in (err.get("fields") or []):
            text = str(f).strip()
            if text and text not in named:
                named.append(text)
    if named:
        return named
    return list(IDENTITY_TRIPLE) if saw_mismatch else []


def verdict(brand):
    """Classify one BrandRegistration by what it says about identity. Pure.

    Returns (state, detail).
    """
    status = str(brand.get("status") or "").upper()
    errors = brand.get("errors") or []
    codes = [error_code(e) for e in errors]
    identity = str(brand.get("identity_status") or "").upper()

    if MISMATCH in codes:
        targets = ", ".join(edit_targets(errors))
        return ("identity-mismatch",
                "%s: the registry could not match the submitted identity against "
                "public records. Correct %s on the Customer Profile, not on the "
                "brand." % (MISMATCH, targets))

    if status == "FAILED":
        other = ", ".join(c for c in codes if c) or "no code"
        return ("failed-elsewhere",
                "FAILED on %s, which is not an identity mismatch. The Customer "
                "Profile business details are not the thing to re-check."
                % other)

    if status == "SUSPENDED":
        return ("suspended",
                "brand is SUSPENDED, which is a compliance decision rather than "
                "an identity check. Nothing here is fixed by editing the "
                "profile.")

    if status in ("PENDING", "IN_REVIEW"):
        return ("in-review",
                "brand is %s: the identity lookup has not returned a verdict "
                "yet." % status)

    if status == "APPROVED":
        if identity in WEAK_IDENTITY:
            return ("approved-unverified-identity",
                    "APPROVED with identity_status %s, so the business identity "
                    "was taken as declared rather than matched to a record. A "
                    "later re-vet can still turn up %s." % (identity, MISMATCH))
        return ("approved",
                "APPROVED with identity_status %s" % (identity or "unset"))

    return ("unknown-status",
            "status is %s, which this script does not recognise."
            % (status or "unset"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_brands(session, limit=500):
    """Page the brand list. Items come back under `data` on this resource."""
    url = MSG + "/a2p/BrandRegistrations"
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get("data", []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
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

    brands = list_brands(session, args.max_brands)
    if not brands:
        log.info("no A2P brand registrations on this account")
        return 0

    bad = 0
    for brand in brands:
        state, detail = verdict(brand)
        sid = brand.get("sid", "?")
        line = "%-28s %s  %s" % (state, sid, detail)
        if state in ("approved", "in-review"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for err in brand.get("errors") or []:
            if err.get("url"):
                log.warning("  %s -> %s", error_code(err) or "?", err["url"])
        if state == "identity-mismatch":
            bundle = brand.get("customer_profile_bundle_sid", "BU...")
            log.warning("  read: GET %s/CustomerProfiles/%s/EntityAssignments to "
                        "find the business End-User holding those fields",
                        TRUSTHUB, bundle)
            log.warning("  repair: edit that End-User in Trust Hub so the legal "
                        "name, address and registration identifier match the "
                        "IRS or CRA record exactly, then resubmit brand %s. "
                        "Three resubmissions are free; a fourth returns 21724",
                        sid)

    log.info("%d brand(s), %d with an identity mismatch", len(brands), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-brand-identity-audit.mjs",
"js": '''/**
 * Report A2P brands rejected because the tax ID and legal name disagree.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MSG = 'https://messaging.twilio.com/v1';
const TRUSTHUB = 'https://trusthub.twilio.com/v1';

const MISMATCH = '30799';

// What the registry compares when it resolves a tax identifier against public
// records. Used only when errors[] names no fields.
const IDENTITY_TRIPLE = ['legal company name', 'registered business address',
                         'business_registration_identifier'];

const WEAK_IDENTITY = ['SELF_DECLARED', 'UNVERIFIED'];

/**
 * Read the code off one errors[] entry, as a string. The brand resource spells
 * the key code and the campaign resource spells it error_code.
 */
export function errorCode(err) {
  for (const k of ['error_code', 'code']) {
    const v = err[k];
    if (v !== undefined && v !== null && v !== '') return String(v);
  }
  return '';
}

/**
 * What to correct on the Customer Profile, from the 30799 entries. Pure.
 * Prefers what the API named in `fields`; falls back to the identity triple
 * only when the entry named nothing.
 */
export function editTargets(errors) {
  const named = [];
  let sawMismatch = false;
  for (const err of errors) {
    if (errorCode(err) !== MISMATCH) continue;
    sawMismatch = true;
    for (const f of err.fields ?? []) {
      const text = String(f).trim();
      if (text && !named.includes(text)) named.push(text);
    }
  }
  if (named.length) return named;
  return sawMismatch ? [...IDENTITY_TRIPLE] : [];
}

/**
 * Classify one BrandRegistration by what it says about identity. Pure.
 * Returns [state, detail].
 */
export function verdict(brand) {
  const status = String(brand.status ?? '').toUpperCase();
  const errors = brand.errors ?? [];
  const codes = errors.map(errorCode);
  const identity = String(brand.identity_status ?? '').toUpperCase();

  if (codes.includes(MISMATCH)) {
    const targets = editTargets(errors).join(', ');
    return ['identity-mismatch',
      `${MISMATCH}: the registry could not match the submitted identity against ` +
      `public records. Correct ${targets} on the Customer Profile, not on the ` +
      'brand.'];
  }

  if (status === 'FAILED') {
    const other = codes.filter(Boolean).join(', ') || 'no code';
    return ['failed-elsewhere',
      `FAILED on ${other}, which is not an identity mismatch. The Customer ` +
      'Profile business details are not the thing to re-check.'];
  }

  if (status === 'SUSPENDED') {
    return ['suspended',
      'brand is SUSPENDED, which is a compliance decision rather than an ' +
      'identity check. Nothing here is fixed by editing the profile.'];
  }

  if (status === 'PENDING' || status === 'IN_REVIEW') {
    return ['in-review',
      `brand is ${status}: the identity lookup has not returned a verdict yet.`];
  }

  if (status === 'APPROVED') {
    if (WEAK_IDENTITY.includes(identity)) {
      return ['approved-unverified-identity',
        `APPROVED with identity_status ${identity}, so the business identity was ` +
        `taken as declared rather than matched to a record. A later re-vet can ` +
        `still turn up ${MISMATCH}.`];
    }
    return ['approved', `APPROVED with identity_status ${identity || 'unset'}`];
  }

  return ['unknown-status',
    `status is ${status || 'unset'}, which this script does not recognise.`];
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

/** Page the brand list. Items come back under `data` on this resource. */
export async function listBrands(auth, limit = 500) {
  let url = `${MSG}/a2p/BrandRegistrations`;
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, { PageSize: 50 });
    out.push(...(page.data ?? []));
    url = page.meta?.next_page_url ?? null;
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

  const brands = await listBrands(auth);
  if (brands.length === 0) {
    console.log('no A2P brand registrations on this account');
    return;
  }

  let bad = 0;
  for (const brand of brands) {
    const [state, detail] = verdict(brand);
    const sid = brand.sid ?? '?';
    const line = `${state.padEnd(28)} ${sid}  ${detail}`;
    if (state === 'approved' || state === 'in-review') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    for (const err of brand.errors ?? []) {
      if (err.url) console.warn(`  ${errorCode(err) || '?'} -> ${err.url}`);
    }
    if (state === 'identity-mismatch') {
      const bundle = brand.customer_profile_bundle_sid ?? 'BU...';
      console.warn(`  read: GET ${TRUSTHUB}/CustomerProfiles/${bundle}/` +
                   'EntityAssignments to find the business End-User holding ' +
                   'those fields');
      console.warn('  repair: edit that End-User in Trust Hub so the legal name, ' +
                   'address and registration identifier match the IRS or CRA ' +
                   `record exactly, then resubmit brand ${sid}. Three ` +
                   'resubmissions are free; a fourth returns 21724');
    }
  }

  console.log(`${brands.length} brand(s), ${bad} with an identity mismatch`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are easy to get wrong here and both are pinned below. The brand resource spells the key <code>code</code> where the campaign resource spells it <code>error_code</code>, so a classifier reading one of them reports <code>30799</code> as unrecognised. And a <code>FAILED</code> brand carrying some other code must not be reported as an identity mismatch, because that sends somebody to re-check a Customer Profile that was never the problem.",
"test_py_file": "test_twilio_a2p_brand_identity_audit.py",
"test_py": '''from twilio_a2p_brand_identity_audit import edit_targets, error_code, verdict

FAILED = {"sid": "BN0123456789", "status": "FAILED"}


def test_30799_is_reported_as_an_identity_mismatch():
    state, detail = verdict(dict(FAILED, errors=[{"code": "30799"}]))
    assert state == "identity-mismatch"
    assert "Customer Profile" in detail


def test_the_brand_resource_spells_the_key_code_not_error_code():
    # The campaign resource says error_code. A classifier that reads only one of
    # them reports every brand rejection as unrecognised.
    assert error_code({"code": 30799}) == "30799"
    assert error_code({"error_code": 30799}) == "30799"


def test_named_fields_win_over_the_identity_triple():
    errors = [{"code": "30799", "fields": ["business_registration_identifier"]}]
    assert edit_targets(errors) == ["business_registration_identifier"]


def test_a_30799_with_no_fields_still_says_where_to_look():
    assert edit_targets([{"code": "30799"}]) == [
        "legal company name", "registered business address",
        "business_registration_identifier"]


def test_other_codes_contribute_no_edit_targets():
    assert edit_targets([{"code": "30898"}]) == []


def test_a_brand_failed_on_another_code_is_not_an_identity_mismatch():
    state, detail = verdict(dict(FAILED, errors=[{"code": "30898"}]))
    assert state == "failed-elsewhere"
    assert "30898" in detail


def test_approved_but_self_declared_is_reported():
    state, detail = verdict({"sid": "BN1", "status": "APPROVED",
                             "identity_status": "SELF_DECLARED"})
    assert state == "approved-unverified-identity"
    assert "30799" in detail


def test_a_vetted_brand_is_clean():
    state, _ = verdict({"sid": "BN1", "status": "APPROVED",
                        "identity_status": "VETTED_VERIFIED"})
    assert state == "approved"


def test_suspension_is_not_an_identity_problem():
    state, detail = verdict({"sid": "BN1", "status": "SUSPENDED"})
    assert state == "suspended"
    assert "compliance decision" in detail
''',
"test_js_file": "twilio-a2p-brand-identity-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { editTargets, errorCode, verdict }
  from './twilio-a2p-brand-identity-audit.mjs';

const FAILED = { sid: 'BN0123456789', status: 'FAILED' };

test('30799 is reported as an identity mismatch', () => {
  const [state, detail] = verdict({ ...FAILED, errors: [{ code: '30799' }] });
  assert.equal(state, 'identity-mismatch');
  assert.match(detail, /Customer Profile/);
});

test('the brand resource spells the key code, not error_code', () => {
  assert.equal(errorCode({ code: 30799 }), '30799');
  assert.equal(errorCode({ error_code: 30799 }), '30799');
});

test('named fields win over the identity triple', () => {
  assert.deepEqual(
    editTargets([{ code: '30799', fields: ['business_registration_identifier'] }]),
    ['business_registration_identifier']);
});

test('a 30799 with no fields still says where to look', () => {
  assert.deepEqual(editTargets([{ code: '30799' }]),
    ['legal company name', 'registered business address',
     'business_registration_identifier']);
});

test('other codes contribute no edit targets', () => {
  assert.deepEqual(editTargets([{ code: '30898' }]), []);
});

test('a brand failed on another code is not an identity mismatch', () => {
  const [state, detail] = verdict({ ...FAILED, errors: [{ code: '30898' }] });
  assert.equal(state, 'failed-elsewhere');
  assert.match(detail, /30898/);
});

test('approved but self declared is reported', () => {
  const [state, detail] = verdict({ sid: 'BN1', status: 'APPROVED',
                                    identity_status: 'SELF_DECLARED' });
  assert.equal(state, 'approved-unverified-identity');
  assert.match(detail, /30799/);
});

test('a vetted brand is clean', () => {
  assert.equal(verdict({ sid: 'BN1', status: 'APPROVED',
                         identity_status: 'VETTED_VERIFIED' })[0], 'approved');
});

test('suspension is not an identity problem', () => {
  const [state, detail] = verdict({ sid: 'BN1', status: 'SUSPENDED' });
  assert.equal(state, 'suspended');
  assert.match(detail, /compliance decision/);
});
''',
"faq": [
 ("What does 30799 actually mean?",
  "That the registry could not verify the business identity you submitted. In practice it took the tax identifier, looked it up against public records, and found the legal name or address on that record did not match what was sent. It is a lookup failure, not a formatting error, so the value can be perfectly valid and still fail."),
 ("Which name does the registry want?",
  "The legal name exactly as it appears on the IRS or CRA record for that identifier, including the entity suffix. A DBA, a trading name, a shortened form or the name of an acquired company that is still on the signage will all fail, however well known they are."),
 ("Can I fix this on the brand resource?",
  "No, and this is the part that wastes the most time. The brand is built from the Trust Hub Customer Profile bundle named in customer_profile_bundle_sid. The business End-User inside that bundle holds the name, address and registration identifier, and that is the object to edit before resubmitting the brand."),
 ("How many times can I resubmit?",
  "Three, free. The fourth returns 21724. So a resubmission is worth spending only on a change you have actually verified against the tax record, not on a plausible-looking retype of the same details."),
 ("Do nonprofits and government entities fail differently?",
  "They fail with the same code from the same lookup, but the attribute is usually different: a wrong 501(c) subsection code, or an entity submitted under the wrong company type. The fix is still a Customer Profile edit, so read the fields array rather than assuming it is the EIN."),
],
"related": [
 ("/twilio/a2p-brand-registration-failed/", "A brand at FAILED blocks every campaign"),
 ("/twilio/a2p-brand-stuck-pending-review/", "A brand parked at PENDING with no callback"),
 ("/twilio/a2p-campaign-vetting-failed/", "A campaign is FAILED and errors[] names the field"),
],
"citations": [CITE_30799, CITE_FIX_BRANDS, CITE_BRAND, CITE_PROFILES],
},

{
"slug": "a2p-brand-missing-secondary-vetting",
"title": "An approved brand with no trust score is throttled to the floor",
"description": "The brand is APPROVED, campaigns are still rejected for AT&T and throughput sits at the lowest tier. brand_score is null because secondary vetting never ran.",
"h1": "an approved brand with no trust score is throttled to the floor",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio brand_score null", "a2p secondary vetting",
             "skip_automatic_sec_vet", "10dlc trust score throughput",
             "brand not qualified for at&t"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Registration is finished. <code>status</code> reads <code>APPROVED</code>, the campaign is <code>VERIFIED</code>, numbers are registered, and messages queue up behind a throughput ceiling that nobody set. Sometimes a campaign is refused outright with \"brand not qualified to run Campaign for AT&amp;T\". The field that explains all of it is <code>brand_score</code>, and it is <code>null</code>.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}</code> and flag any brand where <code>status</code> is <code>APPROVED</code> and <code>brand_score</code> is <code>null</code>. Read <code>brand_type</code>, <code>identity_status</code> and <code>skip_automatic_sec_vet</code> alongside it, then <code>GET /v1/a2p/BrandRegistrations/{BrandSid}/Vettings</code> for <code>vetting_status</code>, <code>vetting_class</code> and <code>vetting_provider</code>.</p>
<p>Only Standard brands are scored. A <code>SOLE_PROPRIETOR</code> or <code>LOW_VOLUME_STANDARD</code> brand has no score by definition and its throughput is fixed by use case, so a null score there is not a finding &mdash; reporting it as one buries the Standard brand that genuinely lost its vetting.</p>""",
"problem": """<p>This is the only A2P problem in this section where everything reads as successful. There is no error code on the brand, no rejected campaign to look at, no failed send to trace. The registration completed, and the consequence is a number that is absent rather than wrong: messages per second toward AT&amp;T, T-Mobile and Verizon scale with the trust score, and a brand without one is treated as the least trusted thing on the network.</p>
<p>What that looks like from the application is a queue. Sends are accepted, they sit, and they arrive late under load, which reads as a Twilio performance problem rather than a registration one. The other face of it is blunter: a campaign submission refused with a message about the brand not qualifying for AT&amp;T, which sends the team to edit campaign copy for a rejection that has nothing to do with the campaign.</p>""",
"why": """<p><strong>Approval and scoring are two separate outcomes.</strong> The brand can pass registration and never acquire a score. <code>status</code> answers "is this brand real"; <code>brand_score</code> answers "how much throughput will carriers give it", and the second question has no bearing on the first.</p>
<p><strong>A flag set once at creation stays set.</strong> If <code>skip_automatic_sec_vet</code> was true when the brand was submitted &mdash; often to avoid the vetting fee during a proof of concept &mdash; the automatic vetting never ran, and nothing later in the lifecycle goes back and runs it.</p>
<p><strong>Vetting can fail on its own, quietly.</strong> The <code>Vettings</code> subresource is a separate object with its own <code>vetting_status</code>. A record sitting at <code>FAILED</code> or <code>PENDING</code> explains a null score, and it lives one GET away from the brand rather than on it.</p>
<p><strong>Null is a legitimate value for most brand types.</strong> Sole Proprietor and Low-Volume Standard brands are never scored. A check that flags every null score produces a report where the real finding is one row among many, which is the same as not having found it.</p>""",
"steps": [
 {"h": "Filter to APPROVED before anything else",
  "body": """<p>A brand that is <code>PENDING</code>, <code>FAILED</code> or <code>SUSPENDED</code> has a null score for an obvious reason and belongs in a different report. This check is specifically about the brand that finished registration successfully and is still throttled.</p>"""},
 {"h": "Read brand_type and stop there when it is not Standard",
  "body": """<p><code>SOLE_PROPRIETOR</code> and <code>LOW_VOLUME_STANDARD</code> brands do not receive a secondary vetting score at all; their throughput is set by the use case. Reporting them alongside the Standard brand that lost its vetting is how the real finding gets lost.</p>"""},
 {"h": "Test brand_score for null, not for falsiness",
  "body": """<p>The score runs from 0 to 100 and <code>0</code> is a real, meaningful score &mdash; a very low trust rating, not a missing one. A truthiness check treats them as the same thing and reports a scored brand as unvetted, which is the opposite of the truth.</p>"""},
 {"h": "Fetch the Vettings subresource for the reason",
  "body": """<p><code>GET /v1/a2p/BrandRegistrations/{BrandSid}/Vettings</code> returns the vetting records with <code>vetting_status</code> of <code>PENDING</code>, <code>SUCCESS</code> or <code>FAILED</code>, plus <code>vetting_class</code> and <code>vetting_provider</code>. No records at all, a failed record and a record still pending are three different situations with three different responses.</p>"""},
 {"h": "Request vetting, and treat a SUCCESS with no score as a disagreement",
  "body": """<p>The repair is a vetting request against the brand with <code>VettingProvider=aegis</code>, or <code>campaign-verify</code> plus a <code>VettingId</code> for political brands. If a record already reads <code>SUCCESS</code> and the score is still null, do not request another one &mdash; report the disagreement, because a second request costs the fee again for a vetting that already happened.</p>"""},
],
"verify": """<p>Re-run the script. Every approved Standard brand should carry a <code>brand_score</code>, and no vetting record should be sitting at <code>FAILED</code>.</p>
<pre><code class="language-bash">python3 twilio_a2p_brand_vetting_audit.py
# 3 brand(s), 0 approved without a trust score</code></pre>""",
"code_intro": "One paginated GET over the brands and one per approved Standard brand for its vetting records &mdash; the subresource is only worth fetching once the brand type says a score was ever expected. The classifier is pure and takes both, because the distinction that matters is between a score of zero, a score that is missing, and a brand type that was never going to have one.",
"py_file": "twilio_a2p_brand_vetting_audit.py",
"py": '''"""Report approved A2P brands that carry no trust score, and say why.

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
log = logging.getLogger("twilio_a2p_brand_vetting_audit")

MSG = "https://messaging.twilio.com/v1"

# Only Standard brands receive a secondary vetting score. Sole Proprietor and
# Low-Volume Standard throughput is fixed by use case, so a null score on those
# is the documented behaviour rather than a finding.
SCORED_TYPE = "STANDARD"
UNSCORED_TYPES = ("SOLE_PROPRIETOR", "LOW_VOLUME_STANDARD")

# Precedence when a brand has several vetting records: an in-flight retry says
# more about what to do next than the failure it is retrying.
VETTING_ORDER = ("SUCCESS", "PENDING", "FAILED")


def vetting_state(vettings):
    """The one vetting_status that decides what to do next. Pure.

    Returns success, pending, failed or none. A brand can accumulate several
    records, and reporting the newest is less useful than reporting the one that
    changes the recommendation.
    """
    seen = {str(v.get("vetting_status") or "").upper() for v in vettings or []}
    for status in VETTING_ORDER:
        if status in seen:
            return status.lower()
    return "none"


def verdict(brand, vettings=()):
    """Classify one approved brand by whether it has a usable trust score. Pure.

    Returns (state, detail).
    """
    status = str(brand.get("status") or "").upper()
    if status != "APPROVED":
        return ("not-approved",
                "status is %s: a brand that has not been approved has no score "
                "for a reason that has nothing to do with vetting."
                % (status or "unset"))

    brand_type = str(brand.get("brand_type") or "").upper()
    score = brand.get("brand_score")

    # 0 is a real score, and the lowest one. A truthiness check here reports a
    # scored brand as unvetted, which is exactly backwards.
    if score is not None:
        return ("scored",
                "brand_score is %s; carrier throughput scales with it." % score)

    if brand_type in UNSCORED_TYPES:
        return ("not-eligible",
                "%s brands are never scored and their throughput is fixed by "
                "use case, so a null brand_score here is expected." % brand_type)
    if brand_type != SCORED_TYPE:
        return ("unknown-brand-type",
                "brand_type is %s, which this script cannot say is eligible for "
                "a score." % (brand_type or "unset"))

    state = vetting_state(vettings)
    if state == "success":
        return ("vetted-without-score",
                "a vetting record reads SUCCESS and brand_score is still null. "
                "Two objects disagree; do not pay for a second vetting on the "
                "strength of one of them.")
    if state == "pending":
        return ("vetting-pending",
                "secondary vetting is PENDING. The score arrives when it "
                "resolves; throughput stays at the floor until then.")
    if state == "failed":
        return ("vetting-failed",
                "secondary vetting FAILED, so the brand is APPROVED and "
                "untrusted at the same time. Carriers treat it as low trust.")

    if brand.get("skip_automatic_sec_vet"):
        return ("vetting-skipped",
                "skip_automatic_sec_vet was set at creation, so automatic "
                "vetting never ran and nothing later runs it.")
    return ("unvetted",
            "APPROVED Standard brand with no score and no vetting record. "
            "Throughput toward AT&T, T-Mobile and Verizon sits at the lowest "
            "tier, and campaigns can be refused as unqualified.")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=500):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
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

    brands = list_v1(session, MSG + "/a2p/BrandRegistrations", "data",
                     args.max_brands)
    if not brands:
        log.info("no A2P brand registrations on this account")
        return 0

    bad = 0
    for brand in brands:
        sid = brand.get("sid", "?")
        vettings = []
        # Only worth a request once the brand type says a score was expected.
        if (str(brand.get("status") or "").upper() == "APPROVED"
                and str(brand.get("brand_type") or "").upper() == SCORED_TYPE
                and brand.get("brand_score") is None):
            vettings = list_v1(session,
                               "%s/a2p/BrandRegistrations/%s/Vettings" % (MSG, sid),
                               "data")
        state, detail = verdict(brand, vettings)
        line = "%-21s %s  %s" % (state, sid, detail)
        if state in ("scored", "not-eligible", "not-approved"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for v in vettings:
            log.warning("  %s vetting %s from %s",
                        v.get("vetting_status", "?"), v.get("vetting_class", "?"),
                        v.get("vetting_provider", "?"))
        if state in ("unvetted", "vetting-skipped", "vetting-failed"):
            log.warning("  repair: request secondary vetting on brand %s with "
                        "VettingProvider=aegis, or campaign-verify plus a "
                        "VettingId for a political brand. Console -> Messaging -> "
                        "Regulatory Compliance -> Brand -> Request secondary "
                        "vetting", sid)
        elif state == "vetted-without-score":
            log.warning("  repair: none yet. Re-read the brand before requesting "
                        "anything; a second vetting is charged again")

    log.info("%d brand(s), %d approved without a trust score", len(brands), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-brand-vetting-audit.mjs",
"js": '''/**
 * Report approved A2P brands that carry no trust score, and say why.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MSG = 'https://messaging.twilio.com/v1';

// Only Standard brands receive a secondary vetting score. Sole Proprietor and
// Low-Volume Standard throughput is fixed by use case.
const SCORED_TYPE = 'STANDARD';
const UNSCORED_TYPES = ['SOLE_PROPRIETOR', 'LOW_VOLUME_STANDARD'];

// Precedence when a brand has several vetting records: an in-flight retry says
// more about what to do next than the failure it is retrying.
const VETTING_ORDER = ['SUCCESS', 'PENDING', 'FAILED'];

/**
 * The one vetting_status that decides what to do next. Pure. Returns success,
 * pending, failed or none.
 */
export function vettingState(vettings) {
  const seen = new Set((vettings ?? []).map(
    (v) => String(v.vetting_status ?? '').toUpperCase()));
  for (const status of VETTING_ORDER) {
    if (seen.has(status)) return status.toLowerCase();
  }
  return 'none';
}

/**
 * Classify one approved brand by whether it has a usable trust score. Pure.
 * Returns [state, detail].
 */
export function verdict(brand, vettings = []) {
  const status = String(brand.status ?? '').toUpperCase();
  if (status !== 'APPROVED') {
    return ['not-approved',
      `status is ${status || 'unset'}: a brand that has not been approved has ` +
      'no score for a reason that has nothing to do with vetting.'];
  }

  const brandType = String(brand.brand_type ?? '').toUpperCase();
  const score = brand.brand_score ?? null;

  // 0 is a real score, and the lowest one. A truthiness check here reports a
  // scored brand as unvetted, which is exactly backwards.
  if (score !== null) {
    return ['scored',
      `brand_score is ${score}; carrier throughput scales with it.`];
  }

  if (UNSCORED_TYPES.includes(brandType)) {
    return ['not-eligible',
      `${brandType} brands are never scored and their throughput is fixed by ` +
      'use case, so a null brand_score here is expected.'];
  }
  if (brandType !== SCORED_TYPE) {
    return ['unknown-brand-type',
      `brand_type is ${brandType || 'unset'}, which this script cannot say is ` +
      'eligible for a score.'];
  }

  const state = vettingState(vettings);
  if (state === 'success') {
    return ['vetted-without-score',
      'a vetting record reads SUCCESS and brand_score is still null. Two ' +
      'objects disagree; do not pay for a second vetting on the strength of ' +
      'one of them.'];
  }
  if (state === 'pending') {
    return ['vetting-pending',
      'secondary vetting is PENDING. The score arrives when it resolves; ' +
      'throughput stays at the floor until then.'];
  }
  if (state === 'failed') {
    return ['vetting-failed',
      'secondary vetting FAILED, so the brand is APPROVED and untrusted at the ' +
      'same time. Carriers treat it as low trust.'];
  }

  if (brand.skip_automatic_sec_vet) {
    return ['vetting-skipped',
      'skip_automatic_sec_vet was set at creation, so automatic vetting never ' +
      'ran and nothing later runs it.'];
  }
  return ['unvetted',
    'APPROVED Standard brand with no score and no vetting record. Throughput ' +
    'toward AT&T, T-Mobile and Verizon sits at the lowest tier, and campaigns ' +
    'can be refused as unqualified.'];
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

export async function listV1(auth, url, key, limit = 500) {
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

  const brands = await listV1(auth, `${MSG}/a2p/BrandRegistrations`, 'data');
  if (brands.length === 0) {
    console.log('no A2P brand registrations on this account');
    return;
  }

  let bad = 0;
  for (const brand of brands) {
    const sid = brand.sid ?? '?';
    let vettings = [];
    // Only worth a request once the brand type says a score was expected.
    if (String(brand.status ?? '').toUpperCase() === 'APPROVED'
        && String(brand.brand_type ?? '').toUpperCase() === SCORED_TYPE
        && (brand.brand_score ?? null) === null) {
      vettings = await listV1(
        auth, `${MSG}/a2p/BrandRegistrations/${sid}/Vettings`, 'data');
    }
    const [state, detail] = verdict(brand, vettings);
    const line = `${state.padEnd(21)} ${sid}  ${detail}`;
    if (['scored', 'not-eligible', 'not-approved'].includes(state)) {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    for (const v of vettings) {
      console.warn(`  ${v.vetting_status ?? '?'} vetting ` +
                   `${v.vetting_class ?? '?'} from ${v.vetting_provider ?? '?'}`);
    }
    if (['unvetted', 'vetting-skipped', 'vetting-failed'].includes(state)) {
      console.warn(`  repair: request secondary vetting on brand ${sid} with ` +
                   'VettingProvider=aegis, or campaign-verify plus a VettingId ' +
                   'for a political brand. Console -> Messaging -> Regulatory ' +
                   'Compliance -> Brand -> Request secondary vetting');
    } else if (state === 'vetted-without-score') {
      console.warn('  repair: none yet. Re-read the brand before requesting ' +
                   'anything; a second vetting is charged again');
    }
  }

  console.log(`${brands.length} brand(s), ${bad} approved without a trust score`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that earns its place is <code>brand_score</code> of <code>0</code>. It is a real score, the lowest one on a scale that starts there, and any check written as <code>if not score</code> reports that brand as never vetted &mdash; sending somebody to pay for a vetting that already ran and already answered. The rest pin the brand types that are correctly scoreless, so they never crowd the report.",
"test_py_file": "test_twilio_a2p_brand_vetting_audit.py",
"test_py": '''from twilio_a2p_brand_vetting_audit import verdict, vetting_state

STANDARD = {"sid": "BN0123456789", "status": "APPROVED", "brand_type": "STANDARD",
            "brand_score": None}


def test_an_approved_standard_brand_with_no_vetting_is_the_finding():
    state, detail = verdict(STANDARD)
    assert state == "unvetted"
    assert "lowest tier" in detail


def test_a_score_of_zero_is_a_score():
    # 0 is the bottom of a 0 to 100 scale, not a missing value. A truthiness
    # check reports this brand as unvetted and buys a second vetting for it.
    state, detail = verdict(dict(STANDARD, brand_score=0))
    assert state == "scored"
    assert "0" in detail


def test_sole_proprietor_brands_are_never_scored():
    state, _ = verdict(dict(STANDARD, brand_type="SOLE_PROPRIETOR"))
    assert state == "not-eligible"


def test_low_volume_standard_is_not_reported_either():
    assert verdict(dict(STANDARD,
                        brand_type="LOW_VOLUME_STANDARD"))[0] == "not-eligible"


def test_the_skip_flag_is_named_when_nothing_was_ever_vetted():
    state, detail = verdict(dict(STANDARD, skip_automatic_sec_vet=True))
    assert state == "vetting-skipped"
    assert "skip_automatic_sec_vet" in detail


def test_a_failed_vetting_record_explains_the_null_score():
    state, _ = verdict(STANDARD, [{"vetting_status": "FAILED"}])
    assert state == "vetting-failed"


def test_a_pending_retry_outranks_the_failure_it_retries():
    assert vetting_state([{"vetting_status": "FAILED"},
                          {"vetting_status": "PENDING"}]) == "pending"


def test_success_with_no_score_is_reported_as_a_disagreement():
    state, detail = verdict(STANDARD, [{"vetting_status": "SUCCESS"}])
    assert state == "vetted-without-score"
    assert "disagree" in detail


def test_an_unapproved_brand_is_a_different_report():
    assert verdict(dict(STANDARD, status="PENDING"))[0] == "not-approved"
''',
"test_js_file": "twilio-a2p-brand-vetting-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, vettingState }
  from './twilio-a2p-brand-vetting-audit.mjs';

const STANDARD = { sid: 'BN0123456789', status: 'APPROVED',
                   brand_type: 'STANDARD', brand_score: null };

test('an approved standard brand with no vetting is the finding', () => {
  const [state, detail] = verdict(STANDARD);
  assert.equal(state, 'unvetted');
  assert.match(detail, /lowest tier/);
});

test('a score of zero is a score', () => {
  const [state, detail] = verdict({ ...STANDARD, brand_score: 0 });
  assert.equal(state, 'scored');
  assert.match(detail, /0/);
});

test('sole proprietor brands are never scored', () => {
  assert.equal(verdict({ ...STANDARD, brand_type: 'SOLE_PROPRIETOR' })[0],
               'not-eligible');
});

test('low volume standard is not reported either', () => {
  assert.equal(verdict({ ...STANDARD, brand_type: 'LOW_VOLUME_STANDARD' })[0],
               'not-eligible');
});

test('the skip flag is named when nothing was ever vetted', () => {
  const [state, detail] = verdict({ ...STANDARD, skip_automatic_sec_vet: true });
  assert.equal(state, 'vetting-skipped');
  assert.match(detail, /skip_automatic_sec_vet/);
});

test('a failed vetting record explains the null score', () => {
  assert.equal(verdict(STANDARD, [{ vetting_status: 'FAILED' }])[0],
               'vetting-failed');
});

test('a pending retry outranks the failure it retries', () => {
  assert.equal(vettingState([{ vetting_status: 'FAILED' },
                             { vetting_status: 'PENDING' }]), 'pending');
});

test('success with no score is reported as a disagreement', () => {
  const [state, detail] = verdict(STANDARD, [{ vetting_status: 'SUCCESS' }]);
  assert.equal(state, 'vetted-without-score');
  assert.match(detail, /disagree/);
});

test('an unapproved brand is a different report', () => {
  assert.equal(verdict({ ...STANDARD, status: 'PENDING' })[0], 'not-approved');
});
''',
"faq": [
 ("What is a brand score and what does it change?",
  "It is an external secondary vetting score from 0 to 100, produced by a third-party provider such as Aegis. Messages per second toward AT&T, T-Mobile and Verizon scale with it, so a brand without one is given the lowest throughput tier and some campaign types are refused outright."),
 ("My brand is APPROVED. Why is there no score?",
  "Because approval and scoring are separate outcomes. Approval says the business is real; the score says how much the carriers will let it send. Either skip_automatic_sec_vet was set when the brand was created, or a vetting record exists and did not succeed. The Vettings subresource distinguishes the two."),
 ("Do Sole Proprietor brands need vetting?",
  "No. Sole Proprietor and Low-Volume Standard brands are not scored at all and their throughput is fixed by use case, so a null brand_score on those is the documented behaviour. Requesting vetting for them spends the fee for nothing."),
 ("Is brand_score of 0 the same as no score?",
  "No, and confusing them is the expensive mistake here. Zero is the bottom of the scale and a real answer from a vetting that ran. Null means no vetting produced an answer. A check written as a truthiness test reports the first as the second and sends somebody to buy a vetting they already have."),
 ("Can I request vetting more than once?",
  "You can, and each request is charged. That is why a SUCCESS vetting record alongside a null brand_score is reported as a disagreement to investigate rather than as a reason to request another one: the vetting already happened and paying twice will not change the field."),
],
"related": [
 ("/twilio/a2p-brand-registration-failed/", "A brand at FAILED blocks every campaign"),
 ("/twilio/a2p-brand-suspended/", "A SUSPENDED brand suspends every campaign under it"),
 ("/twilio/a2p-campaign-stuck-in-progress/", "A campaign parked at IN_PROGRESS is not live"),
],
"citations": [CITE_VETTING, CITE_BRAND, CITE_FIX_BRANDS, CITE_A2P],
},

]
