#!/usr/bin/env python3
"""/twilio/ field notes, batch U — the writing.

Four identity and paperwork failures, all of which block traffic without ever
touching the traffic. A regulatory bundle refused by a human reviewer; a bundle
refused by the machine evaluation before a human ever sees it; a Trust Hub
Customer Profile whose rejection is felt in two other products and blamed on
neither; and a toll-free verification whose rejection is either a field to
correct or a business Twilio will not carry, with nothing in the status telling
you which.

Each keys on a different object and a different question, so they are worth
reading as four notes rather than one: status on the Bundle, the per-requirement
breakdown under Evaluations, the downstream join for the Customer Profile, and
the coded reason plus the edit window for toll-free.

Read-only throughout. GET requests only, and every repair is printed for a human
to run rather than performed, because resubmitting any of these starts a review
you want somebody watching.
"""

CITE_BUNDLES = ("Bundle resource — Twilio Docs",
                "https://www.twilio.com/docs/phone-numbers/regulatory/api/bundles")
CITE_REGULATORY = ("Regulatory compliance for phone numbers — Twilio Docs",
                   "https://www.twilio.com/docs/phone-numbers/regulatory")
CITE_REG_API = ("Regulatory Compliance API — Twilio Docs",
                "https://www.twilio.com/docs/phone-numbers/regulatory/api")
CITE_EVALUATIONS = ("Evaluation resource — Twilio Docs",
                    "https://www.twilio.com/docs/phone-numbers/regulatory/api/evaluations")
CITE_SUPPORTING = ("Supporting Document resource — Twilio Docs",
                   "https://www.twilio.com/docs/phone-numbers/regulatory/api/supporting-documents")
CITE_PROFILES = ("Customer Profiles (Trust Hub REST API) — Twilio Docs",
                 "https://www.twilio.com/docs/trust-hub/trusthub-rest-api/customer-profiles")
CITE_BRAND = ("Brand Registration resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/brand-registration-resource")
CITE_TFV = ("Toll-Free Verification resource — Twilio Docs",
            "https://www.twilio.com/docs/messaging/api/tollfree-verification-resource")
CITE_30469 = ("Error 30469: illegal substances or articles — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30469")
CITE_30032 = ("Error 30032: toll-free number has not been verified — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30032")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "regulatory-bundle-rejected",
"title": "A rejected regulatory bundle blocks every number purchase",
"description": "The bundle failed review, not the clock. Until somebody reads its item assignments and resubmits it, no number can be bought in that country.",
"h1": "a rejected regulatory bundle blocks every number purchase",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio bundle twilio-rejected", "regulatory bundle rejected",
             "twilio number purchase fails regulated country",
             "regulatorycompliance bundles api", "twilio bundle item assignments"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A number that was available yesterday cannot be bought today, and the API is saying something about regulatory requirements rather than about the number. Nothing changed in your code. Somebody on Twilio's regulatory team opened the bundle that proves who you are to that country's regulator, read the documents attached to it, and refused them. That happened days ago, in a resource nobody on your team has a reason to open.",
"short_answer": """<p>Read <code>GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles?Status=twilio-rejected</code> and treat every result as a country you cannot buy numbers in. Each carries <code>sid</code>, <code>friendly_name</code>, <code>regulation_sid</code>, <code>status</code>, <code>valid_until</code> and <code>email</code>, and the list filters on <code>IsoCountry</code>, <code>NumberType</code> and <code>EndUserType</code>.</p>
<p>Then <code>GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles/{BundleSid}/ItemAssignments</code> for the <code>object_sid</code> of each End-User and Supporting Document attached to it. Those SIDs are what the repair replaces; the bundle itself holds no document, only assignments.</p>
<p>This is a review that failed, not an approval that lapsed. If the bundle reads <code>twilio-approved</code> with a date approaching, that is <a href="/twilio/regulatory-bundle-expiring/">a bundle counting down to expiry</a> and a different note.</p>""",
"problem": """<p>The bundle is the object a regulated country's rules are satisfied against: a container of End-User and Supporting Document assignments matched to a Regulation for one ISO country and one number type. It is entirely out of band from the numbers it protects. Nothing in the phone-number API mentions it, no message or call carries its state, and the account works normally in every other country. So a rejection sits there being true and being invisible.</p>
<p>What makes it expensive is when it is discovered. The natural moment is a purchase, which means the discovery happens inside whatever you were trying to launch, in a country where you have already promised somebody a local number. The rejection itself may be a photograph that was cropped, an address that does not match the utility bill, or a document class the regulation does not accept, and none of that is in the failure you are looking at. It is in a resource you have to go and read, along with, on a mature account, several other bundles in the same state that nobody has looked at either.</p>""",
"why": """<p><strong>Nothing announces a rejection unless you asked it to.</strong> A bundle carries an <code>email</code> and a <code>status_callback</code>. If both are empty, the state change is delivered to nobody. Bundles are usually created in the console during a hurried onboarding, and neither field is one anybody fills in while trying to get a number bought.</p>
<p><strong>The reviewer is a person, and the objection is about documents.</strong> Illegible scans, an expired passport, a lease where a utility bill was required, a director's address where the company's registered address was required. These are not states a schema can express, which is why the bundle only carries <code>twilio-rejected</code> and the detail lives in the assignments and the email nobody received.</p>
<p><strong>A draft looks exactly like a rejection from the outside.</strong> Both are bundles that cannot buy numbers. But a draft was never submitted, so nothing was reviewed and nothing failed &mdash; somebody started it, got interrupted, and it has been sitting at <code>draft</code> ever since. It needs a submission, not a correction, and a report that lumps the two together sends people looking for a rejection reason that does not exist.</p>
<p><strong>Existing numbers are exposed, not just new ones.</strong> A rejected bundle does not only block purchases. The numbers already provisioned against that regulation are non-compliant while it stands, which is a reclamation risk rather than an immediate outage, and it is the reason this is worth finding before the next purchase rather than during it.</p>
<p><strong>The bundle is per country and per number type.</strong> An account selling into six countries has at least six of these, often more once mobile and national numbers are counted separately. Checking the one you are about to use is how five others stay rejected for a year.</p>""",
"steps": [
 {"h": "List by status across the whole estate, not by the country you need today",
  "body": """<p><code>GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles?Status=twilio-rejected</code>. Add <code>SortBy=date-updated</code> to put the most recent decisions first. The point of a status filter is that it costs the same to ask about every country as about one, and the answer for the other countries is the part nobody has.</p>"""},
 {"h": "Page the v2 way",
  "body": """<p>Results arrive under <code>results</code> and the next page is an absolute URL in <code>meta.next_page_url</code>. Code carried over from the <code>2010-04-01</code> account API looks for <code>next_page_uri</code> and a host to prefix it with, finds neither, and silently stops after the first page.</p>"""},
 {"h": "Separate rejected from draft from in review",
  "body": """<p>Three different states, three different actions: correct and resubmit, submit for the first time, or wait. Only the first has a reason to go and find. Fold them together and the report reads as a pile of failures with no next step, which is a report people stop opening.</p>"""},
 {"h": "Read the item assignments to name what has to be replaced",
  "body": """<p><code>GET /v2/RegulatoryCompliance/Bundles/{BundleSid}/ItemAssignments</code> lists an <code>object_sid</code> per assignment &mdash; the End-User (<code>IT&hellip;</code>) and Supporting Document (<code>RD&hellip;</code>) objects the reviewer actually looked at. Printing those SIDs turns "this bundle was rejected" into a repair somebody can start without opening the console.</p>"""},
 {"h": "Check email and status_callback while you are in the response",
  "body": """<p>Both empty means the next transition on this bundle will also be found by an audit rather than told to anyone. It is not the cause of the rejection and it is the reason the rejection is weeks old.</p>"""},
 {"h": "Replace the object, resubmit, then re-run",
  "body": """<p><code>POST /v2/RegulatoryCompliance/SupportingDocuments</code> with the corrected document, assign it with <code>POST /v2/RegulatoryCompliance/Bundles/{BundleSid}/ItemAssignments</code>, then <code>POST /v2/RegulatoryCompliance/Bundles/{BundleSid}</code> with <code>Status=pending-review</code>. Before resubmitting, it is worth reading <a href="/twilio/bundle-evaluation-noncompliant/">the machine evaluation</a>, which will tell you for free whether the new set of documents can pass at all.</p>"""},
],
"verify": """<p>Re-run the script with <code>--all</code>. Every bundle should read <code>approved</code> or <code>in-review</code>, and the rejected count should be zero.</p>
<pre><code class="language-bash">python3 twilio_bundle_rejection_audit.py --all
# 7 bundle(s), 0 rejected, 0 never submitted</code></pre>""",
"code_intro": "One paginated GET over the bundles, plus &mdash; with <code>--items</code> &mdash; one extra GET per finding to name the objects the reviewer refused. The classification is a pure function of <code>status</code> alone, which is the honest shape: the bundle resource genuinely does not carry the reason, and pretending otherwise would mean inventing detail the API never returned.",
"py_file": "twilio_bundle_rejection_audit.py",
"py": '''"""Report regulatory Bundles that failed review and cannot buy numbers.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because resubmitting a bundle starts a regulatory review you want a human
watching, and because this script holds a credential to an account that can send
messages and spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_bundle_rejection_audit")

NUMBERS = "https://numbers.twilio.com/v2"

REJECTED = "twilio-rejected"
APPROVED = "twilio-approved"
DRAFT = "draft"
REVIEWING = ("pending-review", "in-review")


def verdict(bundle):
    """Classify one Bundle on status. Pure, so the states can be tested without a
    network and without a rejected bundle to hand.

    Status is all the bundle carries. There is no rejection reason on this
    resource, no error array and no free-text note: the objection lives with the
    reviewer and with the End-User and Supporting Document objects assigned to
    the bundle. A classifier that promised more than status would be inventing
    it.

    Returns (state, detail).
    """
    status = str(bundle.get("status") or "").strip().lower()

    if status == REJECTED:
        return ("rejected",
                "twilio-rejected: a reviewer read the assigned documents and "
                "refused them. No number can be bought against this regulation, "
                "and numbers already on it are non-compliant meanwhile.")

    if status == DRAFT:
        return ("draft",
                "still a draft: created, perhaps filled in, never submitted. "
                "Nothing was reviewed, so there is no rejection reason to go "
                "looking for. It needs submitting, not correcting.")

    if status in REVIEWING:
        return ("in-review",
                "%s: submitted and waiting on a human. Purchases in this country "
                "keep failing until it is approved, so this is a queue position "
                "rather than a green light." % status)

    if status == APPROVED:
        return ("approved",
                "twilio-approved: usable for purchase today. Whether it stays "
                "that way is a question about valid_until, which is a different "
                "check from this one.")

    return ("unknown",
            "status is %s, which this script does not classify. Read it rather "
            "than assuming it is healthy." % (status or "unset"))


def notification_gap(bundle):
    """The reason a rejection is weeks old when it is found, or None.

    A bundle transitions on Twilio's schedule, not yours. With no email and no
    status_callback the transition is delivered to nobody, which is how a
    rejection that happened in March is discovered by a purchase in June.
    """
    if str(bundle.get("email") or "").strip():
        return None
    if str(bundle.get("status_callback") or "").strip():
        return None
    return ("no email and no status_callback on this bundle: its state changes "
            "are announced to nobody, which is why this one is being found by an "
            "audit rather than by a message.")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v2(session, url, limit, **params):
    """Page a numbers v2 collection.

    Rows arrive under `results` and the next page as an absolute URL in
    `meta.next_page_url`, unlike the 2010-04-01 API's `next_page_uri` path.
    """
    params = dict(params, PageSize=50)
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("results", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def assigned_objects(session, bundle_sid):
    """The End-User and Supporting Document SIDs a reviewer actually looked at."""
    url = "%s/RegulatoryCompliance/Bundles/%s/ItemAssignments" % (NUMBERS, bundle_sid)
    return [a.get("object_sid") for a in list_v2(session, url, 100)
            if a.get("object_sid")]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true",
                    help="classify every bundle rather than only rejected ones")
    ap.add_argument("--items", action="store_true",
                    help="one extra GET per finding to name the assigned objects")
    ap.add_argument("--max-bundles", type=int, default=500,
                    help="stop after this many bundles")
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

    query = {"SortBy": "date-updated", "SortDirection": "DESC"}
    if not args.all:
        query["Status"] = REJECTED
    bundles = list_v2(session, "%s/RegulatoryCompliance/Bundles" % NUMBERS,
                      args.max_bundles, **query)
    if not bundles:
        log.info("no regulatory bundles matched")
        return 0

    rejected = drafts = 0
    for bundle in bundles:
        state, detail = verdict(bundle)
        label = "%s/%s" % (bundle.get("iso_country") or "??",
                           bundle.get("number_type") or "?")
        sid = bundle.get("sid", "?")
        log_line = "%-10s %s  %s  %s" % (state, sid, label, detail)
        if state in ("approved", "in-review"):
            log.info(log_line)
            continue
        if state == DRAFT:
            drafts += 1
        else:
            rejected += 1
        log.warning(log_line)

        note = notification_gap(bundle)
        if note:
            log.warning("  %s", note)

        if state == "rejected":
            if args.items:
                objects = assigned_objects(session, sid)
                log.warning("  assigned objects: %s",
                            ", ".join(objects) or "none assigned")
            log.warning("  repair: replace the refused End-User or Supporting "
                        "Document, assign it via %s/RegulatoryCompliance/Bundles/"
                        "%s/ItemAssignments, then send the bundle back with "
                        "Status=pending-review", NUMBERS, sid)
        elif state == DRAFT:
            log.warning("  repair: finish the assignments, then move %s/"
                        "RegulatoryCompliance/Bundles/%s to Status=pending-review",
                        NUMBERS, sid)

    log.info("%d bundle(s), %d rejected, %d never submitted",
             len(bundles), rejected, drafts)
    return 1 if (rejected or drafts) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-bundle-rejection-audit.mjs",
"js": '''/**
 * Report regulatory Bundles that failed review and cannot buy numbers.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed, because resubmitting a bundle starts a regulatory review you want a
 * human watching.
 */
const NUMBERS = 'https://numbers.twilio.com/v2';

const REJECTED = 'twilio-rejected';
const APPROVED = 'twilio-approved';
const DRAFT = 'draft';
const REVIEWING = ['pending-review', 'in-review'];

/**
 * Classify one Bundle on status. Pure, so the states can be tested without a
 * network and without a rejected bundle to hand.
 *
 * Status is all the bundle carries. There is no rejection reason on this
 * resource: the objection lives with the reviewer and with the End-User and
 * Supporting Document objects assigned to the bundle.
 *
 * Returns [state, detail].
 */
export function verdict(bundle) {
  const status = String(bundle.status ?? '').trim().toLowerCase();

  if (status === REJECTED) {
    return ['rejected',
      'twilio-rejected: a reviewer read the assigned documents and refused ' +
      'them. No number can be bought against this regulation, and numbers ' +
      'already on it are non-compliant meanwhile.'];
  }

  if (status === DRAFT) {
    return ['draft',
      'still a draft: created, perhaps filled in, never submitted. Nothing was ' +
      'reviewed, so there is no rejection reason to go looking for. It needs ' +
      'submitting, not correcting.'];
  }

  if (REVIEWING.includes(status)) {
    return ['in-review',
      `${status}: submitted and waiting on a human. Purchases in this country ` +
      'keep failing until it is approved, so this is a queue position rather ' +
      'than a green light.'];
  }

  if (status === APPROVED) {
    return ['approved',
      'twilio-approved: usable for purchase today. Whether it stays that way is ' +
      'a question about valid_until, which is a different check from this one.'];
  }

  return ['unknown',
    `status is ${status || 'unset'}, which this script does not classify. Read ` +
    'it rather than assuming it is healthy.'];
}

/** The reason a rejection is weeks old when it is found, or null. */
export function notificationGap(bundle) {
  if (String(bundle.email ?? '').trim()) return null;
  if (String(bundle.status_callback ?? '').trim()) return null;
  return 'no email and no status_callback on this bundle: its state changes are ' +
         'announced to nobody, which is why this one is being found by an audit ' +
         'rather than by a message.';
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

/**
 * Page a numbers v2 collection: rows under `results`, next page as an absolute
 * URL in `meta.next_page_url`.
 */
export async function listV2(auth, url, limit = 500, query = {}) {
  let params = { ...query, PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.results ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

async function assignedObjects(auth, bundleSid) {
  const url = `${NUMBERS}/RegulatoryCompliance/Bundles/${bundleSid}/ItemAssignments`;
  const rows = await listV2(auth, url, 100);
  return rows.map((a) => a.object_sid).filter(Boolean);
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
  const all = process.argv.includes('--all');
  const withItems = process.argv.includes('--items');

  const query = { SortBy: 'date-updated', SortDirection: 'DESC' };
  if (!all) query.Status = REJECTED;
  const bundles = await listV2(auth, `${NUMBERS}/RegulatoryCompliance/Bundles`,
                               500, query);
  if (bundles.length === 0) {
    console.log('no regulatory bundles matched');
    return;
  }

  let rejected = 0;
  let drafts = 0;
  for (const bundle of bundles) {
    const [state, detail] = verdict(bundle);
    const label = `${bundle.iso_country ?? '??'}/${bundle.number_type ?? '?'}`;
    const sid = bundle.sid ?? '?';
    const line = `${state.padEnd(10)} ${sid}  ${label}  ${detail}`;
    if (state === 'approved' || state === 'in-review') { console.log(line); continue; }
    if (state === DRAFT) drafts += 1; else rejected += 1;
    console.warn(line);

    const note = notificationGap(bundle);
    if (note) console.warn(`  ${note}`);

    if (state === 'rejected') {
      if (withItems) {
        const objects = await assignedObjects(auth, sid);
        console.warn(`  assigned objects: ${objects.join(', ') || 'none assigned'}`);
      }
      console.warn('  repair: replace the refused End-User or Supporting Document, ' +
                   `assign it via ${NUMBERS}/RegulatoryCompliance/Bundles/${sid}/` +
                   'ItemAssignments, then send the bundle back with ' +
                   'Status=pending-review');
    } else if (state === DRAFT) {
      console.warn('  repair: finish the assignments, then move ' +
                   `${NUMBERS}/RegulatoryCompliance/Bundles/${sid} to ` +
                   'Status=pending-review');
    }
  }

  console.log(`${bundles.length} bundle(s), ${rejected} rejected, ` +
              `${drafts} never submitted`);
  process.exitCode = (rejected || drafts) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Four states that look alike from a dashboard and mean four different things to whoever picks up the ticket. The cases worth pinning are <code>draft</code> staying separate from <code>rejected</code> &mdash; one needs a correction, the other needs a submission &mdash; and a status the script has never seen reporting as <code>unknown</code> rather than falling through to healthy, which is the failure mode of every classifier written as an if/else with a cheerful default.",
"test_py_file": "test_twilio_bundle_rejection_audit.py",
"test_py": '''from twilio_bundle_rejection_audit import notification_gap, verdict


def make(**kw):
    bundle = {"sid": "BU00000000000000000000000000000001",
              "friendly_name": "DE local business",
              "iso_country": "DE",
              "number_type": "local",
              "status": "twilio-rejected",
              "email": "compliance@example.com",
              "status_callback": "https://ops.example.com/bundle"}
    bundle.update(kw)
    return bundle


def test_a_rejected_bundle_names_the_purchase_it_blocks():
    state, detail = verdict(make())
    assert state == "rejected"
    assert "No number can be bought" in detail


def test_draft_is_not_folded_into_rejected():
    state, detail = verdict(make(status="draft"))
    assert state == "draft"
    assert "never submitted" in detail
    assert "submitting, not correcting" in detail


def test_both_review_states_read_as_waiting():
    assert verdict(make(status="pending-review"))[0] == "in-review"
    assert verdict(make(status="in-review"))[0] == "in-review"


def test_approved_defers_the_expiry_question_rather_than_answering_it():
    state, detail = verdict(make(status="twilio-approved"))
    assert state == "approved"
    assert "valid_until" in detail


def test_a_status_the_script_has_never_seen_is_not_healthy():
    state, detail = verdict(make(status="provisionally-approved"))
    assert state == "unknown"
    assert "provisionally-approved" in detail
    state, _ = verdict(make(status=None))
    assert state == "unknown"


def test_valid_until_is_deliberately_not_consulted():
    # A rejected bundle with a date years away is still rejected. The date is
    # the subject of a different check, and reading it here would soften a
    # finding that is not soft.
    state, _ = verdict(make(valid_until="2030-01-01T00:00:00Z"))
    assert state == "rejected"


def test_notification_gap_needs_both_channels_empty():
    assert notification_gap(make()) is None
    assert notification_gap(make(status_callback="")) is None
    assert notification_gap(make(email="")) is None
    assert notification_gap(make(email="", status_callback="")) is not None
    assert notification_gap(make(email="  ", status_callback=None)) is not None
''',
"test_js_file": "twilio-bundle-rejection-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { notificationGap, verdict } from './twilio-bundle-rejection-audit.mjs';

const make = (over = {}) => ({
  sid: 'BU00000000000000000000000000000001',
  friendly_name: 'DE local business',
  iso_country: 'DE',
  number_type: 'local',
  status: 'twilio-rejected',
  email: 'compliance@example.com',
  status_callback: 'https://ops.example.com/bundle',
  ...over,
});

test('a rejected bundle names the purchase it blocks', () => {
  const [state, detail] = verdict(make());
  assert.equal(state, 'rejected');
  assert.match(detail, /No number can be bought/);
});

test('draft is not folded into rejected', () => {
  const [state, detail] = verdict(make({ status: 'draft' }));
  assert.equal(state, 'draft');
  assert.match(detail, /never submitted/);
  assert.match(detail, /submitting, not correcting/);
});

test('both review states read as waiting', () => {
  assert.equal(verdict(make({ status: 'pending-review' }))[0], 'in-review');
  assert.equal(verdict(make({ status: 'in-review' }))[0], 'in-review');
});

test('approved defers the expiry question rather than answering it', () => {
  const [state, detail] = verdict(make({ status: 'twilio-approved' }));
  assert.equal(state, 'approved');
  assert.match(detail, /valid_until/);
});

test('a status the script has never seen is not healthy', () => {
  const [state, detail] = verdict(make({ status: 'provisionally-approved' }));
  assert.equal(state, 'unknown');
  assert.match(detail, /provisionally-approved/);
  assert.equal(verdict(make({ status: null }))[0], 'unknown');
});

test('valid_until is deliberately not consulted', () => {
  assert.equal(verdict(make({ valid_until: '2030-01-01T00:00:00Z' }))[0], 'rejected');
});

test('notificationGap needs both channels empty', () => {
  assert.equal(notificationGap(make()), null);
  assert.equal(notificationGap(make({ status_callback: '' })), null);
  assert.equal(notificationGap(make({ email: '' })), null);
  assert.notEqual(notificationGap(make({ email: '', status_callback: '' })), null);
  assert.notEqual(notificationGap(make({ email: '  ', status_callback: null })), null);
});
''',
"faq": [
 ("Why does the bundle not carry a rejection reason?",
  "Because the objection is about documents rather than about fields. A reviewer looked at a scan and decided it was illegible, or that a lease is not a utility bill, or that the address on it is not the address on the End-User. None of that has a schema. The bundle carries the decision, the assignments carry the objects the decision was about, and the prose goes to the email address on the bundle, which is usually empty."),
 ("How do I find out which document was the problem?",
  "Read the item assignments for the object SIDs, then fetch each End-User and Supporting Document and compare them against the regulation's requirements. If the email on the bundle was set, the reason was sent there. If it was not, Twilio Support can retrieve it, and setting the email before you resubmit means you will not need to ask twice."),
 ("Is a draft bundle really worth reporting?",
  "Yes, and separately. It blocks purchases exactly like a rejection, but there is nothing to correct: somebody created it, got as far as attaching one document, and stopped. On accounts with more than a handful of countries this is more common than rejection, and the fix is minutes rather than a document-gathering exercise."),
 ("What happens to the numbers I already own under a rejected bundle?",
  "They keep working, and they are non-compliant with the regulation that permitted them, which puts them at risk of reclamation. There is no published grace period to plan around. Treat a rejected bundle with live numbers as urgent even though nothing has broken yet, because when it does break the number is gone rather than degraded."),
 ("Can the script resubmit the bundle for me?",
  "No, and this is one of the places where that restraint matters most. A resubmission enters a queue with a human at the end of it, and resubmitting the same documents produces the same rejection while consuming review time. The script prints the sequence, including the assignment step people miss, for somebody to run once the document is genuinely different."),
],
"related": [
 ("/twilio/regulatory-bundle-expiring/", "An approved bundle counting down to expiry"),
 ("/twilio/bundle-evaluation-noncompliant/", "The evaluation that names the failing field"),
 ("/twilio/trusthub-customer-profile-rejected/", "A rejected Trust Hub Customer Profile"),
],
"citations": [CITE_BUNDLES, CITE_REG_API, CITE_REGULATORY, CITE_KEYS],
},

{
"slug": "bundle-evaluation-noncompliant",
"title": "A bundle is noncompliant on a field only Evaluations names",
"description": "The bundle will not submit and the status says nothing useful. The per-requirement breakdown naming the exact failing field is in a subresource.",
"h1": "a bundle is noncompliant on a field only Evaluations names",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio bundle evaluations", "regulatorycompliance evaluations noncompliant",
             "twilio bundle wont submit", "bundle results invalid object_field",
             "twilio regulation requirements"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The bundle has every document somebody could think of attached to it, and it still will not go anywhere. The status reads <code>draft</code>. Submitting bounces. Nothing says why, and the natural response is to attach another document and try again. Twilio already knows the answer: a machine evaluated the bundle against the regulation, found one attribute wrong, and wrote it down in a subresource that most teams never call.",
"short_answer": """<p>Read <code>GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles/{BundleSid}/Evaluations</code>. Each evaluation has a <code>status</code> of <code>compliant</code> or <code>noncompliant</code> and a <code>results</code> array, one entry per requirement, carrying <code>requirement_friendly_name</code>, <code>requirement_name</code>, <code>object_type</code>, <code>passed</code>, <code>failure_reason</code> and <code>error_code</code>.</p>
<p>The field name is one level deeper. Inside a failed result, <code>invalid</code> lists the specific attributes with <code>friendly_name</code>, <code>object_field</code> and their own <code>failure_reason</code>. That <code>object_field</code> is the thing to correct on the referenced End-User or Supporting Document.</p>
<p>An evaluation is a record of one run, not live status. Compare its <code>date_created</code> against the bundle's <code>date_updated</code> before believing it.</p>""",
"problem": """<p>A bundle is checked twice: once by a machine against the regulation's declared requirements, and once by a person once it reaches review. The machine check is the cheap one, it is exhaustive, and it names the failing attribute exactly. It also runs into a subresource rather than onto the bundle, so the bundle keeps saying <code>draft</code> and the answer sits one GET away, unread.</p>
<p>What people do instead is guess. Another document goes on, another submission bounces, and after a few rounds the bundle carries five supporting documents where the regulation asked for two, none of which addresses the actual problem &mdash; a business registration number in the wrong format, an address whose country does not match the regulation's ISO country, a document of a class the regulation does not list. Every one of those is already written down, in English, with the field name attached.</p>""",
"why": """<p><strong>The coarse status is on the bundle and the detail is not.</strong> <code>draft</code> and <code>twilio-rejected</code> are the only things the Bundles resource says. There is no errors array, no summary, no count of failed requirements. Anyone monitoring the bundle sees a state and no reason, which trains people to treat the evaluation as unavailable rather than as unfetched.</p>
<p><strong>The useful field is nested two levels down.</strong> <code>results[]</code> is per requirement; <code>results[].invalid[]</code> is per attribute. Code that stops at the requirement level reports "Business Identity failed" and leaves somebody to work out which of nine attributes that means. The <code>object_field</code> in the inner array is the whole point of the resource.</p>
<p><strong>A failed requirement can carry no invalid entries at all.</strong> When the objection is that a required document is missing rather than wrong, there is no attribute to name, and the reason lives at the result level. A reader that only walks the inner array shows an empty report for the most basic failure there is.</p>
<p><strong>An evaluation is a snapshot with a timestamp.</strong> It records what was true when it ran. Edit the End-User afterwards and the evaluation does not change: a <code>compliant</code> record older than the bundle's <code>date_updated</code> is evidence about a state the bundle is no longer in, and it is exactly the record somebody quotes when asking why an approved-looking bundle was refused.</p>
<p><strong>Creating an evaluation is a write, so a read-only audit reads the last one.</strong> That is a real limitation and worth stating plainly: this script tells you what the most recent run found and when it ran. Getting a fresh answer is a POST, and it belongs with the human doing the repair.</p>""",
"steps": [
 {"h": "Pick the bundles worth evaluating",
  "body": """<p>Anything at <code>draft</code> or <code>twilio-rejected</code>. An approved bundle has already passed both checks, and a bundle in review is somebody else's turn. Filtering first keeps the run to one GET per bundle that could plausibly be wrong.</p>"""},
 {"h": "Fetch the evaluations and take the latest by date",
  "body": """<p><code>GET /v2/RegulatoryCompliance/Bundles/{BundleSid}/Evaluations</code> returns every run this bundle has had, and there can be a dozen. Choose by <code>date_created</code> rather than by position: relying on the API's ordering means the report changes meaning if that ordering ever does.</p>"""},
 {"h": "Walk results[], then invalid[] inside each failure",
  "body": """<p>Skip entries where <code>passed</code> is true. For the rest, read <code>requirement_friendly_name</code> and <code>object_type</code> for context, then each <code>invalid[].object_field</code> and its <code>failure_reason</code> for the correction. When <code>invalid</code> is empty, fall back to the result's own <code>failure_reason</code> and <code>error_code</code> &mdash; that is the missing-document case, and it must not vanish from the report.</p>"""},
 {"h": "Compare the evaluation's date against the bundle's",
  "body": """<p>If <code>date_created</code> on the evaluation is older than <code>date_updated</code> on the bundle, the bundle has been edited since and the verdict describes a previous version of it. Report that alongside the findings rather than instead of them: the failing fields are still the best available list, and their status is now unknown.</p>"""},
 {"h": "Read the regulation to see what was being asked for",
  "body": """<p><code>GET /v2/RegulatoryCompliance/Regulations/{RegulationSid}</code> lists the requirements the evaluation is checking against, which is how you tell a wrong value from an object type that should never have been attached in the first place.</p>"""},
 {"h": "Correct the named field, reassign, evaluate again, then submit",
  "body": """<p>Fix the <code>object_field</code> on the End-User or Supporting Document, reassign it if the object changed, then <code>POST /v2/RegulatoryCompliance/Bundles/{BundleSid}/Evaluations</code> for a fresh verdict. Only once that returns <code>compliant</code> is it worth moving the bundle to <code>pending-review</code>, where <a href="/twilio/regulatory-bundle-rejected/">a human reviewer</a> takes over.</p>"""},
],
"verify": """<p>Re-run the script. Every bundle should report <code>compliant</code>, with no failed fields listed and no staleness note.</p>
<pre><code class="language-bash">python3 twilio_bundle_evaluation_audit.py
# 3 bundle(s) checked, 0 noncompliant, 0 never evaluated</code></pre>""",
"code_intro": "One GET to list the bundles and one per bundle for its evaluations. Three pure functions carry the meaning: which evaluation counts when there are several, how a nested evaluation flattens into a list of fields somebody can act on, and whether the run predates the bundle's last edit &mdash; the last of which is the difference between a verdict and a historical note.",
"py_file": "twilio_bundle_evaluation_audit.py",
"py": '''"""Report the exact fields that make a regulatory Bundle noncompliant.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Creating a fresh evaluation is a write, so
this reads the most recent one and prints what it found; the repair is printed
for a human to run.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_bundle_evaluation_audit")

NUMBERS = "https://numbers.twilio.com/v2"

CHECKABLE = ("draft", "twilio-rejected")


def parse_date(value):
    """Parse an ISO 8601 timestamp from the numbers v2 API into aware UTC.

    fromisoformat on Python 3.9 rejects a trailing Z, and comparing a naive
    datetime against an aware one raises, so both are normalised here rather
    than at every call site.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def latest_evaluation(evaluations):
    """The most recent run by date_created, or None.

    Chosen by date rather than by position in the response. A bundle can carry a
    dozen evaluations, and trusting the API's ordering means the report changes
    meaning if that ordering ever changes.
    """
    dated = [(parse_date(e.get("date_created")), e) for e in evaluations or []]
    dated = [(d, e) for d, e in dated if d is not None]
    if not dated:
        return (evaluations or [None])[0]
    return max(dated, key=lambda pair: pair[0])[1]


def failures(evaluation):
    """Flatten one Evaluation into the attributes that did not pass. Pure, so
    the nesting can be tested without a network.

    Two levels matter. results[] is per requirement; results[].invalid[] is per
    attribute, and object_field in there is the only thing that names what to
    correct. A failed requirement with an empty invalid[] is the missing-document
    case: there is no attribute to blame, and dropping it would hide the most
    basic failure the evaluation reports.

    Returns a list of (requirement, object_type, field, reason).
    """
    out = []
    for result in (evaluation or {}).get("results") or []:
        if result.get("passed"):
            continue
        requirement = (result.get("requirement_friendly_name")
                       or result.get("requirement_name")
                       or "unnamed requirement")
        object_type = result.get("object_type") or "unknown object type"
        invalid = result.get("invalid") or []
        if not invalid:
            reason = (result.get("failure_reason")
                      or ("error %s" % result["error_code"]
                          if result.get("error_code") is not None else None)
                      or "no reason given at requirement level")
            out.append((requirement, object_type, "(no field named)", str(reason)))
            continue
        for field in invalid:
            name = (field.get("object_field") or field.get("friendly_name")
                    or "(unnamed field)")
            out.append((requirement, object_type, name,
                        str(field.get("failure_reason") or "no reason given")))
    return out


def verdict(evaluation):
    """Classify the most recent evaluation of one bundle. Pure.

    Returns (state, detail).
    """
    if not evaluation:
        return ("never-evaluated",
                "no evaluation has ever been run on this bundle. The check is "
                "free and exhaustive, and nothing has asked for it.")

    status = str(evaluation.get("status") or "").strip().lower()
    bad = failures(evaluation)

    if status == "compliant":
        return ("compliant",
                "the run passed every requirement in the regulation. That is a "
                "statement about the moment it ran, not a live status.")

    if status == "noncompliant":
        return ("noncompliant",
                "%d attribute(s) failed. The names below are the fields to "
                "correct on the assigned End-User or Supporting Document."
                % len(bad))

    return ("unknown",
            "evaluation status is %s, which this script does not classify. %d "
            "attribute(s) are marked failed regardless."
            % (status or "unset", len(bad)))


def staleness(evaluation, bundle):
    """Whether the evaluation predates the bundle's last edit, or None.

    An evaluation is a snapshot. Edit an End-User afterwards and the record does
    not move, so a compliant run older than date_updated is evidence about a
    version of the bundle that no longer exists.
    """
    if not evaluation:
        return None
    ran = parse_date(evaluation.get("date_created"))
    edited = parse_date(bundle.get("date_updated"))
    if ran is None or edited is None or ran >= edited:
        return None
    return ("this evaluation ran %s, before the bundle was last updated at %s: "
            "it describes an earlier version of the bundle and only a fresh run "
            "can say what is true now."
            % (ran.isoformat(), edited.isoformat()))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v2(session, url, limit, **params):
    """Page a numbers v2 collection: rows under `results`, next page absolute in
    `meta.next_page_url`."""
    params = dict(params, PageSize=50)
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("results", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true",
                    help="check every bundle rather than only draft and rejected ones")
    ap.add_argument("--max-bundles", type=int, default=200,
                    help="stop after this many bundles")
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

    bundles = list_v2(session, "%s/RegulatoryCompliance/Bundles" % NUMBERS,
                      args.max_bundles)
    if not args.all:
        bundles = [b for b in bundles
                   if str(b.get("status") or "").strip().lower() in CHECKABLE]
    if not bundles:
        log.info("no bundles in a state worth evaluating")
        return 0

    noncompliant = unevaluated = 0
    for bundle in bundles:
        sid = bundle.get("sid", "?")
        runs = list_v2(session, "%s/RegulatoryCompliance/Bundles/%s/Evaluations"
                       % (NUMBERS, sid), 100)
        evaluation = latest_evaluation(runs)
        state, detail = verdict(evaluation)
        label = "%s/%s" % (bundle.get("iso_country") or "??",
                           bundle.get("number_type") or "?")
        line = "%-15s %s  %s  %s" % (state, sid, label, detail)

        if state == "compliant":
            log.info(line)
            note = staleness(evaluation, bundle)
            if note:
                log.warning("  %s", note)
            continue

        if state == "never-evaluated":
            unevaluated += 1
        else:
            noncompliant += 1
        log.warning(line)

        for requirement, object_type, field, reason in failures(evaluation):
            log.warning("  %s [%s] %s: %s", requirement, object_type, field, reason)
        note = staleness(evaluation, bundle)
        if note:
            log.warning("  %s", note)
        log.warning("  repair: correct the named object_field on the assigned "
                    "End-User or Supporting Document, reassign it, then ask for a "
                    "fresh evaluation at %s/RegulatoryCompliance/Bundles/%s/"
                    "Evaluations before submitting", NUMBERS, sid)

    log.info("%d bundle(s) checked, %d noncompliant, %d never evaluated",
             len(bundles), noncompliant, unevaluated)
    return 1 if (noncompliant or unevaluated) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-bundle-evaluation-audit.mjs",
"js": '''/**
 * Report the exact fields that make a regulatory Bundle noncompliant.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. Creating a fresh evaluation is a
 * write, so this reads the most recent one and prints what it found.
 */
const NUMBERS = 'https://numbers.twilio.com/v2';

const CHECKABLE = ['draft', 'twilio-rejected'];

/** Parse an ISO 8601 timestamp from the numbers v2 API. */
export function parseDate(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : new Date(ms);
}

/**
 * The most recent run by date_created, or null. Chosen by date rather than by
 * position, so the report does not change meaning if the API's ordering does.
 */
export function latestEvaluation(evaluations) {
  const dated = (evaluations ?? [])
    .map((e) => [parseDate(e.date_created), e])
    .filter(([d]) => d !== null);
  if (dated.length === 0) return (evaluations ?? [])[0] ?? null;
  return dated.reduce((best, cur) => (cur[0] > best[0] ? cur : best))[1];
}

/**
 * Flatten one Evaluation into the attributes that did not pass. Pure, so the
 * nesting can be tested without a network.
 *
 * results[] is per requirement; results[].invalid[] is per attribute, and
 * object_field in there names what to correct. A failed requirement with an
 * empty invalid[] is the missing-document case and must still be reported.
 *
 * Returns an array of [requirement, objectType, field, reason].
 */
export function failures(evaluation) {
  const out = [];
  for (const result of evaluation?.results ?? []) {
    if (result.passed) continue;
    const requirement = result.requirement_friendly_name
      ?? result.requirement_name ?? 'unnamed requirement';
    const objectType = result.object_type ?? 'unknown object type';
    const invalid = result.invalid ?? [];
    if (invalid.length === 0) {
      const reason = result.failure_reason
        ?? (result.error_code != null ? `error ${result.error_code}` : null)
        ?? 'no reason given at requirement level';
      out.push([requirement, objectType, '(no field named)', String(reason)]);
      continue;
    }
    for (const field of invalid) {
      const name = field.object_field ?? field.friendly_name ?? '(unnamed field)';
      out.push([requirement, objectType, name,
                String(field.failure_reason ?? 'no reason given')]);
    }
  }
  return out;
}

/** Classify the most recent evaluation of one bundle. Returns [state, detail]. */
export function verdict(evaluation) {
  if (!evaluation) {
    return ['never-evaluated',
      'no evaluation has ever been run on this bundle. The check is free and ' +
      'exhaustive, and nothing has asked for it.'];
  }

  const status = String(evaluation.status ?? '').trim().toLowerCase();
  const bad = failures(evaluation);

  if (status === 'compliant') {
    return ['compliant',
      'the run passed every requirement in the regulation. That is a statement ' +
      'about the moment it ran, not a live status.'];
  }

  if (status === 'noncompliant') {
    return ['noncompliant',
      `${bad.length} attribute(s) failed. The names below are the fields to ` +
      'correct on the assigned End-User or Supporting Document.'];
  }

  return ['unknown',
    `evaluation status is ${status || 'unset'}, which this script does not ` +
    `classify. ${bad.length} attribute(s) are marked failed regardless.`];
}

/** Whether the evaluation predates the bundle's last edit, or null. */
export function staleness(evaluation, bundle) {
  if (!evaluation) return null;
  const ran = parseDate(evaluation.date_created);
  const edited = parseDate(bundle.date_updated);
  if (ran === null || edited === null || ran >= edited) return null;
  return `this evaluation ran ${ran.toISOString()}, before the bundle was last ` +
         `updated at ${edited.toISOString()}: it describes an earlier version of ` +
         'the bundle and only a fresh run can say what is true now.';
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

export async function listV2(auth, url, limit = 200) {
  let params = { PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.results ?? []));
    url = page.meta?.next_page_url ?? null;
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
  const all = process.argv.includes('--all');

  let bundles = await listV2(auth, `${NUMBERS}/RegulatoryCompliance/Bundles`, 200);
  if (!all) {
    bundles = bundles.filter(
      (b) => CHECKABLE.includes(String(b.status ?? '').trim().toLowerCase()));
  }
  if (bundles.length === 0) {
    console.log('no bundles in a state worth evaluating');
    return;
  }

  let noncompliant = 0;
  let unevaluated = 0;
  for (const bundle of bundles) {
    const sid = bundle.sid ?? '?';
    const runs = await listV2(
      auth, `${NUMBERS}/RegulatoryCompliance/Bundles/${sid}/Evaluations`, 100);
    const evaluation = latestEvaluation(runs);
    const [state, detail] = verdict(evaluation);
    const label = `${bundle.iso_country ?? '??'}/${bundle.number_type ?? '?'}`;
    const line = `${state.padEnd(15)} ${sid}  ${label}  ${detail}`;

    if (state === 'compliant') {
      console.log(line);
      const fresh = staleness(evaluation, bundle);
      if (fresh) console.warn(`  ${fresh}`);
      continue;
    }

    if (state === 'never-evaluated') unevaluated += 1; else noncompliant += 1;
    console.warn(line);

    for (const [requirement, objectType, field, reason] of failures(evaluation)) {
      console.warn(`  ${requirement} [${objectType}] ${field}: ${reason}`);
    }
    const note = staleness(evaluation, bundle);
    if (note) console.warn(`  ${note}`);
    console.warn('  repair: correct the named object_field on the assigned ' +
                 'End-User or Supporting Document, reassign it, then ask for a ' +
                 `fresh evaluation at ${NUMBERS}/RegulatoryCompliance/Bundles/` +
                 `${sid}/Evaluations before submitting`);
  }

  console.log(`${bundles.length} bundle(s) checked, ${noncompliant} noncompliant, ` +
              `${unevaluated} never evaluated`);
  process.exitCode = (noncompliant || unevaluated) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The nesting is the thing worth pinning, in both directions: a failed requirement with attributes must produce one row per attribute, and a failed requirement with none must still produce a row rather than disappearing. Alongside those, the case that decides whether a report is trustworthy at all &mdash; a <code>compliant</code> evaluation dated before the bundle's last edit, which is not evidence about the bundle as it stands now.",
"test_py_file": "test_twilio_bundle_evaluation_audit.py",
"test_py": '''from twilio_bundle_evaluation_audit import (failures, latest_evaluation,
                                              parse_date, staleness, verdict)

BUNDLE = {"sid": "BU00000000000000000000000000000002",
          "iso_country": "FR",
          "number_type": "national",
          "status": "draft",
          "date_updated": "2026-08-20T10:00:00Z"}

NONCOMPLIANT = {
    "sid": "EL00000000000000000000000000000001",
    "status": "noncompliant",
    "date_created": "2026-08-25T09:00:00Z",
    "results": [
        {"requirement_friendly_name": "Business Name",
         "requirement_name": "business_name_info",
         "object_type": "business",
         "passed": True,
         "invalid": []},
        {"requirement_friendly_name": "Business Identity",
         "requirement_name": "business_identity_info",
         "object_type": "business",
         "passed": False,
         "failure_reason": "one or more attributes are invalid",
         "invalid": [
             {"friendly_name": "Business Registration Number",
              "object_field": "business_registration_number",
              "failure_reason": "value does not match the expected format"},
             {"friendly_name": "Business Address Country",
              "object_field": "iso_country",
              "failure_reason": "address country does not match the regulation"},
         ]},
    ],
}


def test_failed_attributes_are_listed_one_per_field():
    rows = failures(NONCOMPLIANT)
    assert len(rows) == 2
    assert [r[2] for r in rows] == ["business_registration_number", "iso_country"]
    assert rows[0][0] == "Business Identity"
    assert "expected format" in rows[0][3]


def test_a_passing_requirement_is_not_reported():
    assert all(r[0] != "Business Name" for r in failures(NONCOMPLIANT))


def test_a_failure_with_no_invalid_entries_still_produces_a_row():
    # The missing-document case: nothing to name, and the most basic failure
    # there is. A reader that only walks invalid[] shows an empty report.
    evaluation = {"status": "noncompliant",
                  "results": [{"requirement_friendly_name": "Address",
                               "object_type": "supporting_document",
                               "passed": False,
                               "error_code": 22215,
                               "invalid": []}]}
    rows = failures(evaluation)
    assert len(rows) == 1
    assert rows[0][2] == "(no field named)"
    assert "22215" in rows[0][3]


def test_verdict_counts_the_attributes_rather_than_the_requirements():
    state, detail = verdict(NONCOMPLIANT)
    assert state == "noncompliant"
    assert "2 attribute(s)" in detail


def test_a_bundle_with_no_evaluation_is_its_own_state():
    state, detail = verdict(None)
    assert state == "never-evaluated"
    assert "free and exhaustive" in detail


def test_the_latest_run_is_chosen_by_date_not_by_position():
    old = {"sid": "EL1", "date_created": "2026-01-01T00:00:00Z"}
    new = {"sid": "EL2", "date_created": "2026-08-25T09:00:00Z"}
    assert latest_evaluation([new, old])["sid"] == "EL2"
    assert latest_evaluation([old, new])["sid"] == "EL2"
    assert latest_evaluation([]) is None


def test_a_compliant_run_older_than_the_last_edit_is_flagged_as_stale():
    compliant = {"status": "compliant", "date_created": "2026-08-01T00:00:00Z"}
    note = staleness(compliant, BUNDLE)
    assert note is not None
    assert "earlier version" in note
    fresh = {"status": "compliant", "date_created": "2026-08-25T09:00:00Z"}
    assert staleness(fresh, BUNDLE) is None


def test_dates_parse_with_a_trailing_z():
    assert parse_date("2026-08-25T09:00:00Z").hour == 9
    assert parse_date("") is None
    assert parse_date("not a date") is None
''',
"test_js_file": "twilio-bundle-evaluation-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  failures, latestEvaluation, parseDate, staleness, verdict,
} from './twilio-bundle-evaluation-audit.mjs';

const BUNDLE = {
  sid: 'BU00000000000000000000000000000002',
  iso_country: 'FR',
  number_type: 'national',
  status: 'draft',
  date_updated: '2026-08-20T10:00:00Z',
};

const NONCOMPLIANT = {
  sid: 'EL00000000000000000000000000000001',
  status: 'noncompliant',
  date_created: '2026-08-25T09:00:00Z',
  results: [
    {
      requirement_friendly_name: 'Business Name',
      requirement_name: 'business_name_info',
      object_type: 'business',
      passed: true,
      invalid: [],
    },
    {
      requirement_friendly_name: 'Business Identity',
      requirement_name: 'business_identity_info',
      object_type: 'business',
      passed: false,
      failure_reason: 'one or more attributes are invalid',
      invalid: [
        {
          friendly_name: 'Business Registration Number',
          object_field: 'business_registration_number',
          failure_reason: 'value does not match the expected format',
        },
        {
          friendly_name: 'Business Address Country',
          object_field: 'iso_country',
          failure_reason: 'address country does not match the regulation',
        },
      ],
    },
  ],
};

test('failed attributes are listed one per field', () => {
  const rows = failures(NONCOMPLIANT);
  assert.equal(rows.length, 2);
  assert.deepEqual(rows.map((r) => r[2]),
                   ['business_registration_number', 'iso_country']);
  assert.equal(rows[0][0], 'Business Identity');
  assert.match(rows[0][3], /expected format/);
});

test('a passing requirement is not reported', () => {
  assert.ok(failures(NONCOMPLIANT).every((r) => r[0] !== 'Business Name'));
});

test('a failure with no invalid entries still produces a row', () => {
  const evaluation = {
    status: 'noncompliant',
    results: [{
      requirement_friendly_name: 'Address',
      object_type: 'supporting_document',
      passed: false,
      error_code: 22215,
      invalid: [],
    }],
  };
  const rows = failures(evaluation);
  assert.equal(rows.length, 1);
  assert.equal(rows[0][2], '(no field named)');
  assert.match(rows[0][3], /22215/);
});

test('verdict counts the attributes rather than the requirements', () => {
  const [state, detail] = verdict(NONCOMPLIANT);
  assert.equal(state, 'noncompliant');
  assert.match(detail, /2 attribute\\(s\\)/);
});

test('a bundle with no evaluation is its own state', () => {
  const [state, detail] = verdict(null);
  assert.equal(state, 'never-evaluated');
  assert.match(detail, /free and exhaustive/);
});

test('the latest run is chosen by date not by position', () => {
  const old = { sid: 'EL1', date_created: '2026-01-01T00:00:00Z' };
  const fresh = { sid: 'EL2', date_created: '2026-08-25T09:00:00Z' };
  assert.equal(latestEvaluation([fresh, old]).sid, 'EL2');
  assert.equal(latestEvaluation([old, fresh]).sid, 'EL2');
  assert.equal(latestEvaluation([]), null);
});

test('a compliant run older than the last edit is flagged as stale', () => {
  const note = staleness(
    { status: 'compliant', date_created: '2026-08-01T00:00:00Z' }, BUNDLE);
  assert.notEqual(note, null);
  assert.match(note, /earlier version/);
  assert.equal(
    staleness({ status: 'compliant', date_created: '2026-08-25T09:00:00Z' }, BUNDLE),
    null);
});

test('dates parse with a trailing z', () => {
  assert.equal(parseDate('2026-08-25T09:00:00Z').getUTCHours(), 9);
  assert.equal(parseDate(''), null);
  assert.equal(parseDate('not a date'), null);
});
''',
"faq": [
 ("What is the difference between the evaluation and the review?",
  "The evaluation is a machine check against the regulation's declared requirements: it is free, instant, exhaustive about field-level problems, and it names the attribute. The review is a person deciding whether the documents are genuine, legible and consistent. Passing the evaluation is necessary and not sufficient, which is why a compliant bundle can still come back rejected."),
 ("Why can this script not just run a fresh evaluation?",
  "Because creating one is a POST, and this section's scripts hold a read-only credential on purpose. The limitation is real and it is worth stating in the output: what you get is the most recent verdict and its timestamp. When that timestamp is older than the bundle's last edit, the script says so rather than presenting a stale verdict as current."),
 ("The report says a requirement failed but names no field. What does that mean?",
  "That the objection is not about a value. A required document type is missing entirely, or no object of the required type is assigned, so there is no attribute to point at and the reason sits at the requirement level. It is the most common first failure on a new bundle and it is the one a naive reader drops on the floor."),
 ("Where do I actually make the change?",
  "Not on the bundle. The object_field belongs to the End-User or Supporting Document that the bundle assigns, so the edit happens on that object, and if you create a replacement rather than editing in place you also have to assign the new one. That second step is the one people miss, and it produces an identical evaluation on the next run."),
 ("Should I evaluate approved bundles too?",
  "There is little point routinely, and --all is there for the day you want it. An approved bundle has passed both checks against the regulation as it stood. If a regulation changes, the signal you will get is a rejection or an expiry rather than a spontaneous evaluation, so watch those instead."),
],
"related": [
 ("/twilio/regulatory-bundle-rejected/", "The bundle a human reviewer refused"),
 ("/twilio/regulatory-bundle-expiring/", "An approved bundle counting down to expiry"),
 ("/twilio/trusthub-customer-profile-rejected/", "A rejected Trust Hub Customer Profile"),
],
"citations": [CITE_EVALUATIONS, CITE_BUNDLES, CITE_SUPPORTING, CITE_KEYS],
},

{
"slug": "trusthub-customer-profile-rejected",
"title": "One rejected Trust Hub profile fails brands and toll-free",
"description": "A brand rejection and a toll-free rejection that make no sense together usually share one cause: the Customer Profile both of them hang off.",
"h1": "one rejected Trust Hub profile fails brands and toll-free",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio trust hub customer profile rejected",
             "customer_profile_bundle_sid", "twilio trusthub api",
             "a2p brand and tollfree both failing", "twilio secondary profile"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Two people are debugging two problems. One is on the A2P brand, which came back with a code about business identity. The other is on a toll-free verification, rejected for reasons about the business name. They are not related in any dashboard, they are being worked in separate tickets, and they are the same failure: the Trust Hub Customer Profile both of them were built from was rejected, and every product that hangs off it is failing in its own vocabulary.",
"short_answer": """<p>Read <code>GET https://trusthub.twilio.com/v1/CustomerProfiles</code> and check <code>status</code> against <code>draft</code>, <code>pending-review</code>, <code>in-review</code>, <code>twilio-rejected</code> and <code>twilio-approved</code>, alongside <code>errors</code>, <code>valid_until</code> and <code>policy_sid</code>.</p>
<p>Then join downstream. A2P brands name their profile in <code>customer_profile_bundle_sid</code> on <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code>; toll-free verifications name it in <code>customer_profile_sid</code> on <code>GET https://messaging.twilio.com/v1/Tollfree/Verifications</code>. That join is the report: it turns "a profile is rejected" into the list of things that cannot be submitted until it is fixed.</p>
<p><code>GET /v1/CustomerProfiles/{Sid}/Evaluations</code> and <code>/EntityAssignments</code> give the per-requirement breakdown and the objects behind it. <code>GET https://trusthub.twilio.com/v1/TrustProducts</code> has the same shape for Voice Integrity and SHAKEN/STIR.</p>""",
"problem": """<p>Trust Hub is the identity layer that several unrelated-looking Twilio products share. The Customer Profile holds the business: legal name, address, registration identifier, the authorised representative. An A2P brand is not built from data you send to the brand endpoint; it is built from the profile named in <code>customer_profile_bundle_sid</code>. A toll-free verification references the same object. So does Voice Integrity, and SHAKEN/STIR.</p>
<p>When the profile is rejected, none of those products says "the profile is rejected". Each one fails in its own error vocabulary, on its own resource, with its own docs page, and the two engineers looking at them have no reason to suspect a common cause. The result is two investigations, two sets of resubmissions against products that cannot possibly pass, and the shared object sitting one API call away with the actual reason on it.</p>""",
"why": """<p><strong>The dependency points the wrong way for debugging.</strong> The brand knows the profile's SID; the profile knows nothing about the brand. So the natural direction of investigation, starting at the thing that failed, leads away from the cause. You have to already know Trust Hub exists to look up.</p>
<p><strong>Two products spell the same reference differently.</strong> Brands say <code>customer_profile_bundle_sid</code>. Toll-free verifications say <code>customer_profile_sid</code>. The value is the same <code>BU&hellip;</code> SID and any join written for one product silently matches nothing on the other.</p>
<p><strong>Draft is as blocking as rejected, and much quieter.</strong> A profile someone created during onboarding and never submitted has never been reviewed, so it has no errors and no rejection. Downstream submissions against it still fail. A check that keys on <code>twilio-rejected</code> reports the whole account healthy.</p>
<p><strong>Profiles expire.</strong> <code>valid_until</code> is on the profile the same way it is on a regulatory bundle. An approved profile past that date stops being an approved profile, and the products that inherited its approval start failing without anything downstream having changed.</p>
<p><strong>Accounts collect profiles.</strong> A primary profile for the account, secondary profiles for ISVs and their customers, one per tenant. Which one a given brand was built from is a field, not a guess, and on an account with thirty of them the field is the only way to know which rejection matters.</p>""",
"steps": [
 {"h": "List the profiles and read status, errors and valid_until together",
  "body": """<p><code>GET https://trusthub.twilio.com/v1/CustomerProfiles</code>. Rows are under <code>results</code> and the next page is absolute in <code>meta.next_page_url</code>. Read all three fields at once: an approved profile past <code>valid_until</code> and a rejected profile are the same outage wearing different statuses.</p>"""},
 {"h": "Read errors on the profile, not on the products downstream",
  "body": """<p><code>errors</code> on the profile is where the objection was actually recorded. The brand's <code>errors[]</code> and the verification's <code>rejection_reasons[]</code> are consequences, phrased in each product's own terms, and chasing them is what turns one problem into three.</p>"""},
 {"h": "Join the brands and toll-free verifications back to the profile",
  "body": """<p>Brands from <code>GET /v1/a2p/BrandRegistrations</code> (items under <code>data</code>) matched on <code>customer_profile_bundle_sid</code>; verifications from <code>GET /v1/Tollfree/Verifications</code> (items under <code>verifications</code>) matched on <code>customer_profile_sid</code>. Print the blast radius next to the profile so the report says what stops rather than what is wrong.</p>"""},
 {"h": "Treat draft as a finding of its own",
  "body": """<p>A profile that was never submitted blocks the same products as one that was refused. It has no errors to read and no review to wait for, which makes it invisible to anything looking for a rejection and cheap to fix once it is named.</p>"""},
 {"h": "Get the per-requirement detail from Evaluations",
  "body": """<p><code>GET /v1/CustomerProfiles/{Sid}/Evaluations</code> returns the same shape as <a href="/twilio/bundle-evaluation-noncompliant/">the regulatory bundle evaluation</a>: results per requirement, with the failing attributes named inside. <code>/EntityAssignments</code> lists the End-User and Supporting Document objects to correct.</p>"""},
 {"h": "Fix the profile, wait for approval, then re-trigger downstream",
  "body": """<p>Correct the assigned objects, then <code>POST https://trusthub.twilio.com/v1/CustomerProfiles/{Sid}</code> with <code>Status=pending-review</code>. Resubmit the brand or the toll-free verification only after the profile is approved &mdash; a resubmission against a rejected profile fails identically and, for <a href="/twilio/a2p-brand-tax-id-legal-name-mismatch/">brands</a>, consumes one of a small number of free attempts.</p>"""},
],
"verify": """<p>Re-run the script. Every profile should read <code>approved</code>, and every brand and verification listed under it should have somewhere to go.</p>
<pre><code class="language-bash">python3 twilio_customer_profile_audit.py
# 4 profile(s), 0 blocking 0 downstream object(s)</code></pre>""",
"code_intro": "Three paginated GETs &mdash; the profiles from Trust Hub, the brands and the toll-free verifications from messaging v1 &mdash; and then the join that makes the report worth reading. Both interesting parts are pure: the verdict on a profile, including the expiry case that an approved status hides, and the dependency list that has to match two differently spelled fields holding the same SID.",
"py_file": "twilio_customer_profile_audit.py",
"py": '''"""Report Trust Hub Customer Profiles that block A2P brands and toll-free.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because resubmitting a profile starts a review and re-triggering a brand
consumes one of a small number of free attempts.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_customer_profile_audit")

TRUSTHUB = "https://trusthub.twilio.com/v1"
MSG = "https://messaging.twilio.com/v1"

APPROVED = "twilio-approved"
REJECTED = "twilio-rejected"
DRAFT = "draft"
REVIEWING = ("pending-review", "in-review")


def parse_date(value):
    """Parse an ISO 8601 timestamp into aware UTC.

    fromisoformat on Python 3.9 rejects a trailing Z, and comparing naive to
    aware raises, so both are normalised here rather than at every call site.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def error_lines(profile):
    """Readable lines from the profile's errors, whatever shape they arrive in.

    Entries are objects with a code and a description, but a bare string turns up
    too, and str() on a dict in a report is worse than useless.
    """
    out = []
    for err in profile.get("errors") or []:
        if isinstance(err, dict):
            code = err.get("code") or err.get("error_code") or "no code"
            text = (err.get("description") or err.get("message")
                    or "no description")
            out.append("%s: %s" % (code, text))
        else:
            out.append(str(err))
    return out


def verdict(profile, now):
    """Classify one Customer Profile. Pure, so the states can be tested offline.

    An approved profile past valid_until is the case worth having its own state:
    the status still reads approved, and everything built on it has stopped
    inheriting an approval that no longer exists.

    Returns (state, detail).
    """
    status = str(profile.get("status") or "").strip().lower()
    valid_until = parse_date(profile.get("valid_until"))

    if status == REJECTED:
        return ("rejected",
                "twilio-rejected: every product built on this profile fails "
                "downstream in its own vocabulary. The reason is in errors on "
                "this object, not on the brand or the verification.")

    if status == DRAFT:
        return ("draft",
                "still a draft: never submitted, so never reviewed and never "
                "rejected. It blocks the same downstream products, and it has no "
                "errors to read because nothing has looked at it.")

    if status in REVIEWING:
        return ("in-review",
                "%s: submitted and waiting. Downstream submissions made now will "
                "fail, so this is a reason to hold them rather than to retry "
                "them." % status)

    if status == APPROVED:
        if valid_until is not None and valid_until <= now:
            return ("expired",
                    "status still reads twilio-approved but valid_until passed "
                    "on %s: the approval that downstream products inherited is "
                    "gone." % valid_until.date().isoformat())
        return ("approved", "twilio-approved and in date.")

    return ("unknown",
            "status is %s, which this script does not classify. Read it rather "
            "than assuming it is healthy." % (status or "unset"))


def dependents(profile_sid, brands, verifications):
    """Name what stops working while this profile is not approved. Pure.

    The two products spell the same reference differently: brands use
    customer_profile_bundle_sid, toll-free verifications use
    customer_profile_sid. A join written for one matches nothing on the other,
    which is how half the blast radius goes unreported.
    """
    sid = str(profile_sid or "").strip()
    if not sid:
        return []
    out = []
    for brand in brands or []:
        if str(brand.get("customer_profile_bundle_sid") or "").strip() == sid:
            out.append("brand %s (%s)" % (brand.get("sid", "?"),
                                          brand.get("status") or "no status"))
    for record in verifications or []:
        if str(record.get("customer_profile_sid") or "").strip() == sid:
            out.append("toll-free verification %s (%s)"
                       % (record.get("sid", "?"),
                          record.get("status") or "no status"))
    return out


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=500):
    """Page a v1 collection. The items key differs per resource: Trust Hub uses
    `results`, BrandRegistrations uses `data`, toll-free uses `verifications`.
    meta.next_page_url is absolute in all three."""
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
    ap.add_argument("--all", action="store_true",
                    help="list approved profiles too, with their dependants")
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

    profiles = list_v1(session, TRUSTHUB + "/CustomerProfiles", "results")
    if not profiles:
        log.info("no Trust Hub customer profiles on this account")
        return 0

    brands = list_v1(session, MSG + "/a2p/BrandRegistrations", "data")
    verifications = list_v1(session, MSG + "/Tollfree/Verifications", "verifications")

    bad = blocked = 0
    for profile in profiles:
        sid = profile.get("sid", "?")
        state, detail = verdict(profile, now)
        downstream = dependents(sid, brands, verifications)
        line = "%-10s %s  %s  %s" % (state, sid,
                                     profile.get("friendly_name") or "no name",
                                     detail)
        if state == "approved" and not args.all:
            log.info(line)
            continue
        if state == "approved":
            log.info(line)
            for item in downstream:
                log.info("  built on this profile: %s", item)
            continue

        bad += 1
        blocked += len(downstream)
        log.warning(line)
        for text in error_lines(profile):
            log.warning("  error %s", text)
        for item in downstream:
            log.warning("  blocked: %s", item)
        if not downstream:
            log.warning("  nothing downstream references this profile yet, which "
                        "makes it a ticket rather than an outage")
        log.warning("  repair: correct the objects at %s/CustomerProfiles/%s/"
                    "EntityAssignments, send the profile back with "
                    "Status=pending-review, and re-trigger the brand or "
                    "verification only once it is approved", TRUSTHUB, sid)

    log.info("%d profile(s), %d blocking %d downstream object(s)",
             len(profiles), bad, blocked)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-customer-profile-audit.mjs",
"js": '''/**
 * Report Trust Hub Customer Profiles that block A2P brands and toll-free.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed, because resubmitting a profile starts a review and re-triggering a
 * brand consumes one of a small number of free attempts.
 */
const TRUSTHUB = 'https://trusthub.twilio.com/v1';
const MSG = 'https://messaging.twilio.com/v1';

const APPROVED = 'twilio-approved';
const REJECTED = 'twilio-rejected';
const DRAFT = 'draft';
const REVIEWING = ['pending-review', 'in-review'];

/** Parse an ISO 8601 timestamp. */
export function parseDate(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : new Date(ms);
}

/**
 * Readable lines from the profile's errors, whatever shape they arrive in.
 * Entries are objects with a code and a description, but a bare string turns up
 * too, and stringifying an object in a report is worse than useless.
 */
export function errorLines(profile) {
  const out = [];
  for (const err of profile.errors ?? []) {
    if (err && typeof err === 'object') {
      const code = err.code ?? err.error_code ?? 'no code';
      const text = err.description ?? err.message ?? 'no description';
      out.push(`${code}: ${text}`);
    } else {
      out.push(String(err));
    }
  }
  return out;
}

/**
 * Classify one Customer Profile. Pure, so the states can be tested offline.
 *
 * An approved profile past valid_until is the case worth its own state: the
 * status still reads approved, and everything built on it has stopped
 * inheriting an approval that no longer exists.
 *
 * Returns [state, detail].
 */
export function verdict(profile, now) {
  const status = String(profile.status ?? '').trim().toLowerCase();
  const validUntil = parseDate(profile.valid_until);

  if (status === REJECTED) {
    return ['rejected',
      'twilio-rejected: every product built on this profile fails downstream in ' +
      'its own vocabulary. The reason is in errors on this object, not on the ' +
      'brand or the verification.'];
  }

  if (status === DRAFT) {
    return ['draft',
      'still a draft: never submitted, so never reviewed and never rejected. It ' +
      'blocks the same downstream products, and it has no errors to read ' +
      'because nothing has looked at it.'];
  }

  if (REVIEWING.includes(status)) {
    return ['in-review',
      `${status}: submitted and waiting. Downstream submissions made now will ` +
      'fail, so this is a reason to hold them rather than to retry them.'];
  }

  if (status === APPROVED) {
    if (validUntil !== null && validUntil <= now) {
      return ['expired',
        'status still reads twilio-approved but valid_until passed on ' +
        `${validUntil.toISOString().slice(0, 10)}: the approval that downstream ` +
        'products inherited is gone.'];
    }
    return ['approved', 'twilio-approved and in date.'];
  }

  return ['unknown',
    `status is ${status || 'unset'}, which this script does not classify. Read ` +
    'it rather than assuming it is healthy.'];
}

/**
 * Name what stops working while this profile is not approved. Pure.
 *
 * The two products spell the same reference differently: brands use
 * customer_profile_bundle_sid, toll-free verifications use customer_profile_sid.
 * A join written for one matches nothing on the other.
 */
export function dependents(profileSid, brands, verifications) {
  const sid = String(profileSid ?? '').trim();
  if (!sid) return [];
  const out = [];
  for (const brand of brands ?? []) {
    if (String(brand.customer_profile_bundle_sid ?? '').trim() === sid) {
      out.push(`brand ${brand.sid ?? '?'} (${brand.status ?? 'no status'})`);
    }
  }
  for (const record of verifications ?? []) {
    if (String(record.customer_profile_sid ?? '').trim() === sid) {
      out.push(`toll-free verification ${record.sid ?? '?'} ` +
               `(${record.status ?? 'no status'})`);
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

/**
 * Page a v1 collection. The items key differs per resource: Trust Hub uses
 * `results`, BrandRegistrations uses `data`, toll-free uses `verifications`.
 */
export async function listV1(auth, url, key, limit = 500) {
  let params = { PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page[key] ?? []));
    url = page.meta?.next_page_url ?? null;
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
  const all = process.argv.includes('--all');
  const now = new Date();

  const profiles = await listV1(auth, `${TRUSTHUB}/CustomerProfiles`, 'results');
  if (profiles.length === 0) {
    console.log('no Trust Hub customer profiles on this account');
    return;
  }

  const brands = await listV1(auth, `${MSG}/a2p/BrandRegistrations`, 'data');
  const verifications = await listV1(auth, `${MSG}/Tollfree/Verifications`,
                                     'verifications');

  let bad = 0;
  let blocked = 0;
  for (const profile of profiles) {
    const sid = profile.sid ?? '?';
    const [state, detail] = verdict(profile, now);
    const downstream = dependents(sid, brands, verifications);
    const line = `${state.padEnd(10)} ${sid}  ` +
                 `${profile.friendly_name ?? 'no name'}  ${detail}`;
    if (state === 'approved') {
      console.log(line);
      if (all) for (const item of downstream) {
        console.log(`  built on this profile: ${item}`);
      }
      continue;
    }

    bad += 1;
    blocked += downstream.length;
    console.warn(line);
    for (const text of errorLines(profile)) console.warn(`  error ${text}`);
    for (const item of downstream) console.warn(`  blocked: ${item}`);
    if (downstream.length === 0) {
      console.warn('  nothing downstream references this profile yet, which ' +
                   'makes it a ticket rather than an outage');
    }
    console.warn(`  repair: correct the objects at ${TRUSTHUB}/CustomerProfiles/` +
                 `${sid}/EntityAssignments, send the profile back with ` +
                 'Status=pending-review, and re-trigger the brand or verification ' +
                 'only once it is approved');
  }

  console.log(`${profiles.length} profile(s), ${bad} blocking ` +
              `${blocked} downstream object(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The join is the part that is easy to get half right, so it is pinned hardest: a brand referencing the profile through <code>customer_profile_bundle_sid</code> and a toll-free verification referencing the same profile through <code>customer_profile_sid</code> must both appear, and an object pointing at a different profile must not. The other case worth fixing in a test is the approved profile whose <code>valid_until</code> has passed, which a status check alone reports as healthy.",
"test_py_file": "test_twilio_customer_profile_audit.py",
"test_py": '''import datetime

from twilio_customer_profile_audit import (dependents, error_lines, verdict)

NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)

PROFILE_SID = "BU00000000000000000000000000000003"

BRANDS = [
    {"sid": "BN00000000000000000000000000000001",
     "status": "FAILED",
     "customer_profile_bundle_sid": PROFILE_SID},
    {"sid": "BN00000000000000000000000000000002",
     "status": "APPROVED",
     "customer_profile_bundle_sid": "BU99999999999999999999999999999999"},
]

VERIFICATIONS = [
    {"sid": "HH00000000000000000000000000000001",
     "status": "TWILIO_REJECTED",
     "customer_profile_sid": PROFILE_SID},
    {"sid": "HH00000000000000000000000000000002",
     "status": "TWILIO_APPROVED",
     "customer_profile_sid": "BU99999999999999999999999999999999"},
]


def make(**kw):
    profile = {"sid": PROFILE_SID,
               "friendly_name": "Example Ltd primary",
               "status": "twilio-rejected",
               "valid_until": None,
               "policy_sid": "RN00000000000000000000000000000001",
               "errors": []}
    profile.update(kw)
    return profile


def test_a_rejected_profile_points_at_itself_rather_than_downstream():
    state, detail = verdict(make(), NOW)
    assert state == "rejected"
    assert "not on the brand" in detail


def test_draft_blocks_the_same_products_and_has_no_errors_to_read():
    state, detail = verdict(make(status="draft"), NOW)
    assert state == "draft"
    assert "never submitted" in detail


def test_review_states_are_a_reason_to_hold_not_to_retry():
    state, detail = verdict(make(status="in-review"), NOW)
    assert state == "in-review"
    assert "hold them" in detail
    assert verdict(make(status="pending-review"), NOW)[0] == "in-review"


def test_an_approved_profile_past_valid_until_is_not_approved():
    state, detail = verdict(
        make(status="twilio-approved", valid_until="2026-07-01T00:00:00Z"), NOW)
    assert state == "expired"
    assert "2026-07-01" in detail


def test_an_approved_profile_in_date_is_the_only_healthy_state():
    state, _ = verdict(
        make(status="twilio-approved", valid_until="2027-07-01T00:00:00Z"), NOW)
    assert state == "approved"
    state, _ = verdict(make(status="twilio-approved", valid_until=None), NOW)
    assert state == "approved"


def test_dependents_match_both_spellings_of_the_same_reference():
    found = dependents(PROFILE_SID, BRANDS, VERIFICATIONS)
    assert len(found) == 2
    assert "brand BN00000000000000000000000000000001 (FAILED)" in found
    assert any(f.startswith("toll-free verification HH00") for f in found)


def test_objects_on_another_profile_are_not_claimed():
    assert dependents("BU00000000000000000000000000000009",
                      BRANDS, VERIFICATIONS) == []
    assert dependents("", BRANDS, VERIFICATIONS) == []
    assert dependents(PROFILE_SID, None, None) == []


def test_errors_render_whether_they_are_objects_or_strings():
    lines = error_lines(make(errors=[{"code": 21212,
                                      "description": "business name mismatch"},
                                     "legacy string entry"]))
    assert lines[0] == "21212: business name mismatch"
    assert lines[1] == "legacy string entry"
    assert error_lines(make()) == []
''',
"test_js_file": "twilio-customer-profile-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dependents, errorLines, verdict } from './twilio-customer-profile-audit.mjs';

const NOW = new Date('2026-08-30T00:00:00Z');
const PROFILE_SID = 'BU00000000000000000000000000000003';

const BRANDS = [
  { sid: 'BN00000000000000000000000000000001', status: 'FAILED',
    customer_profile_bundle_sid: PROFILE_SID },
  { sid: 'BN00000000000000000000000000000002', status: 'APPROVED',
    customer_profile_bundle_sid: 'BU99999999999999999999999999999999' },
];

const VERIFICATIONS = [
  { sid: 'HH00000000000000000000000000000001', status: 'TWILIO_REJECTED',
    customer_profile_sid: PROFILE_SID },
  { sid: 'HH00000000000000000000000000000002', status: 'TWILIO_APPROVED',
    customer_profile_sid: 'BU99999999999999999999999999999999' },
];

const make = (over = {}) => ({
  sid: PROFILE_SID,
  friendly_name: 'Example Ltd primary',
  status: 'twilio-rejected',
  valid_until: null,
  policy_sid: 'RN00000000000000000000000000000001',
  errors: [],
  ...over,
});

test('a rejected profile points at itself rather than downstream', () => {
  const [state, detail] = verdict(make(), NOW);
  assert.equal(state, 'rejected');
  assert.match(detail, /not on the brand/);
});

test('draft blocks the same products and has no errors to read', () => {
  const [state, detail] = verdict(make({ status: 'draft' }), NOW);
  assert.equal(state, 'draft');
  assert.match(detail, /never submitted/);
});

test('review states are a reason to hold not to retry', () => {
  const [state, detail] = verdict(make({ status: 'in-review' }), NOW);
  assert.equal(state, 'in-review');
  assert.match(detail, /hold them/);
  assert.equal(verdict(make({ status: 'pending-review' }), NOW)[0], 'in-review');
});

test('an approved profile past valid_until is not approved', () => {
  const [state, detail] = verdict(
    make({ status: 'twilio-approved', valid_until: '2026-07-01T00:00:00Z' }), NOW);
  assert.equal(state, 'expired');
  assert.match(detail, /2026-07-01/);
});

test('an approved profile in date is the only healthy state', () => {
  assert.equal(verdict(
    make({ status: 'twilio-approved', valid_until: '2027-07-01T00:00:00Z' }),
    NOW)[0], 'approved');
  assert.equal(verdict(
    make({ status: 'twilio-approved', valid_until: null }), NOW)[0], 'approved');
});

test('dependents match both spellings of the same reference', () => {
  const found = dependents(PROFILE_SID, BRANDS, VERIFICATIONS);
  assert.equal(found.length, 2);
  assert.ok(found.includes('brand BN00000000000000000000000000000001 (FAILED)'));
  assert.ok(found.some((f) => f.startsWith('toll-free verification HH00')));
});

test('objects on another profile are not claimed', () => {
  assert.deepEqual(
    dependents('BU00000000000000000000000000000009', BRANDS, VERIFICATIONS), []);
  assert.deepEqual(dependents('', BRANDS, VERIFICATIONS), []);
  assert.deepEqual(dependents(PROFILE_SID, null, null), []);
});

test('errors render whether they are objects or strings', () => {
  const lines = errorLines(make({
    errors: [{ code: 21212, description: 'business name mismatch' },
             'legacy string entry'] }));
  assert.equal(lines[0], '21212: business name mismatch');
  assert.equal(lines[1], 'legacy string entry');
  assert.deepEqual(errorLines(make()), []);
});
''',
"faq": [
 ("How do I know which Customer Profile a brand was built from?",
  "It is on the brand: customer_profile_bundle_sid names the BU… SID. On an account with one profile the question does not come up; on an ISV account with a profile per tenant it is the only reliable way to tell which rejection is the one blocking this brand, and guessing by friendly name is how the wrong profile gets edited."),
 ("Why do two products spell the same reference differently?",
  "Because they were built at different times against the same underlying object. Brands say customer_profile_bundle_sid, toll-free verifications say customer_profile_sid, and both hold a BU… SID pointing at the same Customer Profile. It costs one extra line to match both and it is the difference between reporting half the blast radius and all of it."),
 ("The profile is approved but the brand still failed. What now?",
  "Then the profile was not the cause and the brand's own errors[] are worth reading properly. That is the point of checking the shared object first: it either explains several failures at once or it rules itself out in one call, and both outcomes are cheaper than two parallel investigations."),
 ("What is a secondary Customer Profile?",
  "The pattern ISVs use: a primary profile for their own business and a secondary profile per customer, each carrying that customer's identity and each able to be rejected on its own. The script does not need to know which is which, because the join answers the question that matters, which is what stops working if this particular profile is not approved."),
 ("Can I resubmit the brand while the profile is in review?",
  "You can, and it will fail the same way. A brand is assembled from the profile at submission time, so submitting against a profile that has not been approved reproduces the rejection and, for Standard brands, spends one of a small number of free attempts. Wait for the profile, then resubmit once."),
],
"related": [
 ("/twilio/a2p-brand-tax-id-legal-name-mismatch/", "A brand rejected on 30799 for an EIN mismatch"),
 ("/twilio/tollfree-verification-rejected/", "A toll-free verification rejected with a code"),
 ("/twilio/a2p-brand-registration-failed/", "A brand registration that came back FAILED"),
],
"citations": [CITE_PROFILES, CITE_BRAND, CITE_TFV, CITE_KEYS],
},

{
"slug": "tollfree-verification-rejected",
"title": "A rejected toll-free verification is fixable or it is not",
"description": "TWILIO_REJECTED carries a coded reason and an edit window. Correcting the named fields works for some codes and can never work for others.",
"h1": "a rejected toll-free verification is fixable or it is not",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio tollfree verification rejected", "TWILIO_REJECTED tollfree",
             "twilio 30469", "tollfree rejection_reasons edit_allowed",
             "toll-free verification edit window"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The verification was filed, it came back <code>TWILIO_REJECTED</code>, somebody read the prose, changed a sentence in the use-case summary and resubmitted. It was rejected again. The reason is a code, the code says the business category is one Twilio will not carry on US and Canadian SMS routes at all, and no edit to the summary was ever going to change that. Meanwhile the window in which cheap edits were possible has been spent on them.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Tollfree/Verifications?Status=TWILIO_REJECTED</code>. Each record carries <code>rejection_reason</code> as prose, <code>rejection_reasons</code> as coded entries, an <code>error_code</code>, and the two fields that decide what to do next: <code>edit_allowed</code> and <code>edit_expiration</code>.</p>
<p>Split the rejections in two. A coded reason such as <code>30469</code> &mdash; illegal substances or articles, which covers cannabis, CBD, kratom, vape and fireworks &mdash; is structural: the category is not carried on these routes regardless of local legality, and no edit fixes it. Everything else is a field problem, and <code>edit_allowed</code> with <code>edit_expiration</code> says whether the in-place correction is still available or a fresh submission is required.</p>
<p>An unverified or pending number is <a href="/twilio/tollfree-number-not-verified/">a different note</a>. This one is about the record that came back with a reason on it.</p>""",
"problem": """<p>Toll-free verification is a review of a business, not a check of a form. Twilio looks at the identity, the use case, the sample content, the public website, the opt-in flow and the privacy policy behind it. When it comes back rejected, the natural reading is that something was written badly, and the natural response is to write it better and try again.</p>
<p>That works for one kind of rejection and cannot work for the other. Some rejections are about evidence: the opt-in is not documented, the summary does not describe what the messages actually say, the website does not mention SMS at all. Those are edits. Others are about what the business is. A prohibited category is prohibited on US and Canadian SMS routes as a matter of carrier policy, not as a matter of how convincingly you described it, and it stays prohibited in states where the underlying product is entirely legal. Resubmitting into that is a loop, and each pass through it burns days of a limited edit window and, eventually, the cheap correction path entirely.</p>""",
"why": """<p><strong>The prose and the code say different things.</strong> <code>rejection_reason</code> is written for a human and reads like feedback on a document. The code in <code>rejection_reasons[]</code> or <code>error_code</code> is the machine-readable classification, and it is the one that says whether this is a category decision or a content one. Reading only the prose is what produces the resubmission loop.</p>
<p><strong>The record holds a clock, and nothing counts it down for you.</strong> <code>edit_allowed</code> plus <code>edit_expiration</code> is the difference between correcting the fields on the existing submission and filing a new one from the back of the review queue. The status stays <code>TWILIO_REJECTED</code> either way, so nothing changes appearance when the window closes.</p>
<p><strong>Legal locally is not the same as carriable.</strong> This surprises people every time. US carriers apply their own content policy to A2P traffic, and cannabis, CBD, kratom, vape and fireworks sit outside it nationally. A dispensary operating lawfully under state law reads its rejection as a mistake, appeals, and gets the same answer.</p>
<p><strong>The submission that was judged is still readable.</strong> <code>use_case_categories</code>, <code>use_case_summary</code>, <code>opt_in_type</code> and <code>business_website</code> are on the record. When the summary is one line and the website field is empty, you can see what the reviewer had to work with, and that is usually a better explanation of a vague rejection than the prose is.</p>
<p><strong>Every day in this state is a day of blocked traffic.</strong> Rejected means unverified, and unverified toll-free traffic to US and Canadian mobiles is blocked outright with <code>30032</code>, while you are still billed for the attempts. The clock on the edit window is running at the same time as the outage.</p>""",
"steps": [
 {"h": "List the rejected records rather than reading them one at a time",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Tollfree/Verifications?Status=TWILIO_REJECTED</code>. Items come back under <code>verifications</code> and the next page is absolute in <code>meta.next_page_url</code>. An account with several toll-free numbers usually has more than one of these, and they will not all be the same kind.</p>"""},
 {"h": "Collect the codes from both places they hide",
  "body": """<p><code>rejection_reasons[]</code> holds the coded entries and the record also carries a top-level <code>error_code</code>. Different records populate different ones. Collect both, deduplicate, and compare as strings before comparing as numbers &mdash; codes arrive as integers in some responses and strings in others.</p>"""},
 {"h": "Decide structural or fixable before reading a word of the prose",
  "body": """<p>A prohibited-category code such as <code>30469</code> means the answer will not change. Say so in the report, name the code, and move the conversation to whether this use case belongs on SMS at all rather than to how it was worded. Everything else is a field problem.</p>"""},
 {"h": "Read the edit window against the clock",
  "body": """<p><code>edit_allowed</code> true with <code>edit_expiration</code> in the future is the cheap path: correct the named fields on the existing record. Past the expiration, or with <code>edit_allowed</code> false, it is a new submission and a new place in the queue. Report the days remaining, because the difference between those two paths is measured in weeks of blocked traffic.</p>"""},
 {"h": "Look at what was actually submitted",
  "body": """<p>An empty <code>business_website</code>, a <code>use_case_summary</code> of a dozen characters, or no <code>use_case_categories</code> at all explain a vague rejection better than the prose does. These are the gaps to close before spending the edit window, not after.</p>"""},
 {"h": "Correct in place, or file fresh, then re-run",
  "body": """<p>Within the window, <code>POST https://messaging.twilio.com/v1/Tollfree/Verifications/{Sid}</code> with the corrected fields. Outside it, <code>POST https://messaging.twilio.com/v1/Tollfree/Verifications</code> as a new submission with <code>BusinessName</code>, <code>BusinessWebsite</code>, <code>NotificationEmail</code>, <code>UseCaseCategories</code>, <code>UseCaseSummary</code>, <code>ProductionMessageSample</code>, <code>OptInType</code>, <code>OptInImageUrls</code>, <code>MessageVolume</code> and <code>TollfreePhoneNumberSid</code>. For a prohibited category, neither: move the use case off SMS.</p>"""},
],
"verify": """<p>Re-run the script. No record should remain at <code>TWILIO_REJECTED</code>, and the structural count should be zero or accounted for.</p>
<pre><code class="language-bash">python3 twilio_tollfree_rejection_audit.py --horizon-days 2
# 2 rejected record(s), 0 structural, 0 with the edit window closing</code></pre>""",
"code_intro": "One paginated GET, filtered by status, and three pure functions doing the thinking: where the codes hide, whether a code means the answer can change, and what the submission looked like to the person who read it. The prohibited-code set is deliberately short &mdash; it holds the code this note documents rather than a guess at the rest, because a classifier that mislabels a fixable rejection as hopeless costs more than one that says it does not know.",
"py_file": "twilio_tollfree_rejection_audit.py",
"py": '''"""Sort rejected toll-free verifications into fixable and structural.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The correction is printed, never performed,
because a resubmission consumes the edit window and enters a review queue.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_tollfree_rejection_audit")

MSG = "https://messaging.twilio.com/v1"

REJECTED = "TWILIO_REJECTED"

# Codes where the answer cannot change by editing the submission. 30469 is
# illegal substances or articles: cannabis, CBD, kratom, vape, fireworks. US
# carriers apply this nationally, so lawful under state law is not the question.
#
# Deliberately short. Guessing at codes would mean telling somebody their
# fixable rejection is hopeless, which is a worse mistake than printing the
# reason and letting them read it.
STRUCTURAL_CODES = {30469}

# A summary shorter than this cannot describe a use case, whatever it says.
MIN_SUMMARY = 40


def parse_date(value):
    """Parse an ISO 8601 timestamp into aware UTC.

    fromisoformat on Python 3.9 rejects a trailing Z, and comparing naive to
    aware raises rather than quietly returning the wrong answer.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def reason_codes(verification):
    """Every coded reason on the record, in order, deduplicated. Pure.

    Codes live in two places and not every record populates both: entries in
    rejection_reasons[] carry their own code, and the record carries a top-level
    error_code. They arrive as integers in some responses and strings in others,
    so everything is normalised to a string here and compared as one.
    """
    codes = []
    for reason in verification.get("rejection_reasons") or []:
        if not isinstance(reason, dict):
            continue
        for field in ("code", "error_code"):
            if reason.get(field) is not None:
                codes.append(str(reason[field]).strip())
                break
    if verification.get("error_code") is not None:
        codes.append(str(verification["error_code"]).strip())

    seen = set()
    out = []
    for code in codes:
        if code and code not in seen:
            seen.add(code)
            out.append(code)
    return out


def is_structural(codes):
    """Whether any code means an edit cannot help. Pure."""
    for code in codes:
        try:
            if int(code) in STRUCTURAL_CODES:
                return True
        except (TypeError, ValueError):
            continue
    return False


def submission_gaps(verification):
    """What the reviewer had to work with, where it was thin. Pure.

    A vague rejection is usually explained better by the submission than by the
    prose. These are the things to fix before spending the edit window.
    """
    gaps = []
    if not str(verification.get("business_website") or "").strip():
        gaps.append("business_website is empty: the reviewer had no site on "
                    "which to find the messaging programme or the privacy policy")
    summary = str(verification.get("use_case_summary") or "").strip()
    if len(summary) < MIN_SUMMARY:
        gaps.append("use_case_summary is %d character(s): too short to describe "
                    "what the messages say or who asked for them" % len(summary))
    if not (verification.get("use_case_categories") or []):
        gaps.append("use_case_categories is empty: nothing declares what this "
                    "traffic is for")
    if not str(verification.get("opt_in_type") or "").strip():
        gaps.append("opt_in_type is unset: no consent mechanism was declared")
    return gaps


def verdict(verification, now, horizon_days=2):
    """Classify one rejected verification. Pure, so the branches can be tested
    without a rejection and without waiting for a window to close.

    Returns (state, detail).
    """
    status = str(verification.get("status") or "").strip().upper()
    if status != REJECTED:
        return ("not-rejected",
                "status is %s: this record is not a rejection, so there is "
                "nothing here to correct." % (status or "unset"))

    codes = reason_codes(verification)
    listed = ", ".join(codes) or "no code given"

    if is_structural(codes):
        return ("structural",
                "rejected on %s: the business category is not carried on US and "
                "CA SMS routes regardless of local legality. Editing the "
                "submission cannot change this answer." % listed)

    expires = parse_date(verification.get("edit_expiration"))
    days = None if expires is None else (expires - now).days

    if verification.get("edit_allowed") and (days is None or days >= 0):
        window = ("an unstated date" if days is None
                  else "%d day(s) from now" % days)
        if days is not None and days <= horizon_days:
            return ("edit-closing",
                    "rejected on %s. edit_allowed is true but the window closes "
                    "%s: correct the named fields on this record now or lose the "
                    "cheap path." % (listed, window))
        return ("editable",
                "rejected on %s. edit_allowed is true until %s, so the named "
                "fields can be corrected in place." % (listed, window))

    if verification.get("edit_allowed") and days is not None and days < 0:
        return ("resubmit",
                "rejected on %s. edit_allowed still reads true but "
                "edit_expiration passed %d day(s) ago: treat this as a fresh "
                "submission." % (listed, -days))

    return ("resubmit",
            "rejected on %s and edit_allowed is false: the in-place correction "
            "is gone and a new submission goes to the back of the review "
            "queue." % listed)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_verifications(session, status=REJECTED, limit=500):
    """Page the toll-free verifications. Items under `verifications`, and
    meta.next_page_url is absolute."""
    url = MSG + "/Tollfree/Verifications"
    params = {"PageSize": 50}
    if status:
        params["Status"] = status
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("verifications", []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--horizon-days", type=int, default=2,
                    help="how near an edit_expiration counts as closing")
    ap.add_argument("--all", action="store_true",
                    help="read every verification rather than only rejections")
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

    records = list_verifications(session, None if args.all else REJECTED)
    if not records:
        log.info("no rejected toll-free verifications on this account")
        return 0

    structural = closing = found = 0
    for record in records:
        state, detail = verdict(record, now, args.horizon_days)
        sid = record.get("sid", "?")
        line = "%-13s %s  %s" % (state, sid, detail)
        if state == "not-rejected":
            log.info(line)
            continue

        found += 1
        if state == "structural":
            structural += 1
        elif state == "edit-closing":
            closing += 1
        log.warning(line)

        for gap in submission_gaps(record):
            log.warning("  %s", gap)
        prose = str(record.get("rejection_reason") or "").strip()
        if prose:
            log.warning("  reviewer note: %s", prose)

        if state == "structural":
            log.warning("  repair: none through this resource. Move the use case "
                        "off US and CA SMS, or carry it on a channel that "
                        "permits the category.")
        elif state in ("editable", "edit-closing"):
            log.warning("  repair: send the corrected fields to %s/Tollfree/"
                        "Verifications/%s before edit_expiration", MSG, sid)
        else:
            log.warning("  repair: file a fresh submission at %s/Tollfree/"
                        "Verifications with BusinessName, BusinessWebsite, "
                        "NotificationEmail, UseCaseCategories, UseCaseSummary, "
                        "ProductionMessageSample, OptInType, OptInImageUrls, "
                        "MessageVolume and TollfreePhoneNumberSid", MSG)

    log.info("%d rejected record(s), %d structural, %d with the edit window "
             "closing", found, structural, closing)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-tollfree-rejection-audit.mjs",
"js": '''/**
 * Sort rejected toll-free verifications into fixable and structural.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The correction is printed, never
 * performed, because a resubmission consumes the edit window and enters a
 * review queue.
 */
const MSG = 'https://messaging.twilio.com/v1';

const REJECTED = 'TWILIO_REJECTED';

// Codes where the answer cannot change by editing the submission. 30469 is
// illegal substances or articles: cannabis, CBD, kratom, vape, fireworks. US
// carriers apply this nationally, so lawful under state law is not the question.
//
// Deliberately short. Guessing at codes would mean telling somebody their
// fixable rejection is hopeless, which is the worse mistake.
const STRUCTURAL_CODES = new Set([30469]);

// A summary shorter than this cannot describe a use case, whatever it says.
const MIN_SUMMARY = 40;

/** Parse an ISO 8601 timestamp. */
export function parseDate(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : new Date(ms);
}

/**
 * Every coded reason on the record, in order, deduplicated. Pure.
 *
 * Codes live in two places and not every record populates both: entries in
 * rejection_reasons[] carry their own code, and the record carries a top-level
 * error_code. They arrive as integers in some responses and strings in others.
 */
export function reasonCodes(verification) {
  const codes = [];
  for (const reason of verification.rejection_reasons ?? []) {
    if (!reason || typeof reason !== 'object') continue;
    for (const field of ['code', 'error_code']) {
      if (reason[field] != null) { codes.push(String(reason[field]).trim()); break; }
    }
  }
  if (verification.error_code != null) {
    codes.push(String(verification.error_code).trim());
  }
  return [...new Set(codes.filter(Boolean))];
}

/** Whether any code means an edit cannot help. Pure. */
export function isStructural(codes) {
  return codes.some((code) => {
    const n = Number.parseInt(code, 10);
    return Number.isInteger(n) && STRUCTURAL_CODES.has(n);
  });
}

/**
 * What the reviewer had to work with, where it was thin. Pure. A vague
 * rejection is usually explained better by the submission than by the prose.
 */
export function submissionGaps(verification) {
  const gaps = [];
  if (!String(verification.business_website ?? '').trim()) {
    gaps.push('business_website is empty: the reviewer had no site on which to ' +
              'find the messaging programme or the privacy policy');
  }
  const summary = String(verification.use_case_summary ?? '').trim();
  if (summary.length < MIN_SUMMARY) {
    gaps.push(`use_case_summary is ${summary.length} character(s): too short to ` +
              'describe what the messages say or who asked for them');
  }
  if ((verification.use_case_categories ?? []).length === 0) {
    gaps.push('use_case_categories is empty: nothing declares what this traffic ' +
              'is for');
  }
  if (!String(verification.opt_in_type ?? '').trim()) {
    gaps.push('opt_in_type is unset: no consent mechanism was declared');
  }
  return gaps;
}

/**
 * Classify one rejected verification. Pure, so the branches can be tested
 * without a rejection and without waiting for a window to close.
 *
 * Returns [state, detail].
 */
export function verdict(verification, now, horizonDays = 2) {
  const status = String(verification.status ?? '').trim().toUpperCase();
  if (status !== REJECTED) {
    return ['not-rejected',
      `status is ${status || 'unset'}: this record is not a rejection, so there ` +
      'is nothing here to correct.'];
  }

  const codes = reasonCodes(verification);
  const listed = codes.join(', ') || 'no code given';

  if (isStructural(codes)) {
    return ['structural',
      `rejected on ${listed}: the business category is not carried on US and CA ` +
      'SMS routes regardless of local legality. Editing the submission cannot ' +
      'change this answer.'];
  }

  const expires = parseDate(verification.edit_expiration);
  const days = expires === null
    ? null
    : Math.floor((expires.getTime() - now.getTime()) / 86400000);

  if (verification.edit_allowed && (days === null || days >= 0)) {
    const window = days === null ? 'an unstated date' : `${days} day(s) from now`;
    if (days !== null && days <= horizonDays) {
      return ['edit-closing',
        `rejected on ${listed}. edit_allowed is true but the window closes ` +
        `${window}: correct the named fields on this record now or lose the ` +
        'cheap path.'];
    }
    return ['editable',
      `rejected on ${listed}. edit_allowed is true until ${window}, so the named ` +
      'fields can be corrected in place.'];
  }

  if (verification.edit_allowed && days !== null && days < 0) {
    return ['resubmit',
      `rejected on ${listed}. edit_allowed still reads true but edit_expiration ` +
      `passed ${-days} day(s) ago: treat this as a fresh submission.`];
  }

  return ['resubmit',
    `rejected on ${listed} and edit_allowed is false: the in-place correction is ` +
    'gone and a new submission goes to the back of the review queue.'];
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

/** Page the toll-free verifications: items under `verifications`. */
export async function listVerifications(auth, status = REJECTED, limit = 500) {
  let url = `${MSG}/Tollfree/Verifications`;
  let params = status ? { PageSize: 50, Status: status } : { PageSize: 50 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.verifications ?? []));
    url = page.meta?.next_page_url ?? null;
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
  const flag = process.argv.indexOf('--horizon-days');
  const horizonDays = flag === -1 ? 2 : Number.parseInt(process.argv[flag + 1], 10);
  const now = new Date();

  const records = await listVerifications(
    auth, process.argv.includes('--all') ? null : REJECTED);
  if (records.length === 0) {
    console.log('no rejected toll-free verifications on this account');
    return;
  }

  let structural = 0;
  let closing = 0;
  let found = 0;
  for (const record of records) {
    const [state, detail] = verdict(record, now, horizonDays);
    const sid = record.sid ?? '?';
    const line = `${state.padEnd(13)} ${sid}  ${detail}`;
    if (state === 'not-rejected') { console.log(line); continue; }

    found += 1;
    if (state === 'structural') structural += 1;
    else if (state === 'edit-closing') closing += 1;
    console.warn(line);

    for (const gap of submissionGaps(record)) console.warn(`  ${gap}`);
    const prose = String(record.rejection_reason ?? '').trim();
    if (prose) console.warn(`  reviewer note: ${prose}`);

    if (state === 'structural') {
      console.warn('  repair: none through this resource. Move the use case off ' +
                   'US and CA SMS, or carry it on a channel that permits the ' +
                   'category.');
    } else if (state === 'editable' || state === 'edit-closing') {
      console.warn(`  repair: send the corrected fields to ${MSG}/Tollfree/` +
                   `Verifications/${sid} before edit_expiration`);
    } else {
      console.warn(`  repair: file a fresh submission at ${MSG}/Tollfree/` +
                   'Verifications with BusinessName, BusinessWebsite, ' +
                   'NotificationEmail, UseCaseCategories, UseCaseSummary, ' +
                   'ProductionMessageSample, OptInType, OptInImageUrls, ' +
                   'MessageVolume and TollfreePhoneNumberSid');
    }
  }

  console.log(`${found} rejected record(s), ${structural} structural, ` +
              `${closing} with the edit window closing`);
  process.exitCode = found ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case the whole note turns on is the first one pinned: a structural code on a record whose <code>edit_allowed</code> is true must not be reported as editable, because that is precisely the report that sends somebody back into the resubmission loop. After that, the clock: an <code>edit_expiration</code> in the past has to override an <code>edit_allowed</code> that still reads true, and a code that arrives as a string has to classify the same as one that arrives as an integer.",
"test_py_file": "test_twilio_tollfree_rejection_audit.py",
"test_py": '''import datetime

from twilio_tollfree_rejection_audit import (is_structural, reason_codes,
                                             submission_gaps, verdict)

NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)


def make(**kw):
    record = {"sid": "HH00000000000000000000000000000001",
              "status": "TWILIO_REJECTED",
              "rejection_reason": "opt-in evidence was not found on the website",
              "rejection_reasons": [{"code": 30452,
                                     "description": "opt-in not documented"}],
              "error_code": None,
              "edit_allowed": True,
              "edit_expiration": "2026-09-05T00:00:00Z",
              "business_website": "https://example.com",
              "use_case_categories": ["TWO_FACTOR_AUTHENTICATION"],
              "use_case_summary": "One-time passcodes sent to customers who ask "
                                  "for them at sign-in.",
              "opt_in_type": "WEB_FORM"}
    record.update(kw)
    return record


def test_a_prohibited_category_beats_an_open_edit_window():
    # The case the whole script exists for. edit_allowed is true, so a naive
    # reader sends somebody off to reword a summary that was never the problem.
    state, detail = verdict(make(rejection_reasons=[{"code": 30469}]), NOW)
    assert state == "structural"
    assert "regardless of local legality" in detail
    assert "30469" in detail


def test_codes_classify_the_same_as_integers_or_strings():
    assert is_structural(["30469"]) is True
    assert is_structural([30469]) is True
    assert is_structural(["30452"]) is False
    assert is_structural(["not a code", None]) is False


def test_codes_are_collected_from_the_array_and_the_top_level():
    codes = reason_codes(make(rejection_reasons=[{"code": 30452},
                                                 {"error_code": "30453"}],
                              error_code=30452))
    assert codes == ["30452", "30453"]
    assert reason_codes(make(rejection_reasons=[], error_code=None)) == []


def test_an_open_window_is_the_cheap_path():
    state, detail = verdict(make(), NOW)
    assert state == "editable"
    assert "6 day(s) from now" in detail


def test_a_window_about_to_close_is_its_own_state():
    state, detail = verdict(make(edit_expiration="2026-08-31T00:00:00Z"), NOW)
    assert state == "edit-closing"
    assert "lose the cheap path" in detail


def test_an_expired_window_overrides_edit_allowed():
    state, detail = verdict(make(edit_expiration="2026-08-20T00:00:00Z"), NOW)
    assert state == "resubmit"
    assert "10 day(s) ago" in detail


def test_edit_allowed_false_is_a_fresh_submission():
    state, detail = verdict(make(edit_allowed=False), NOW)
    assert state == "resubmit"
    assert "back of the review queue" in detail


def test_a_record_that_is_not_a_rejection_is_left_alone():
    state, _ = verdict(make(status="TWILIO_APPROVED"), NOW)
    assert state == "not-rejected"


def test_gaps_name_what_the_reviewer_had_to_work_with():
    assert submission_gaps(make()) == []
    gaps = submission_gaps(make(business_website="", use_case_summary="OTPs",
                                use_case_categories=[], opt_in_type=""))
    assert len(gaps) == 4
    assert any("business_website" in g for g in gaps)
    assert any("4 character(s)" in g for g in gaps)
''',
"test_js_file": "twilio-tollfree-rejection-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  isStructural, reasonCodes, submissionGaps, verdict,
} from './twilio-tollfree-rejection-audit.mjs';

const NOW = new Date('2026-08-30T00:00:00Z');

const make = (over = {}) => ({
  sid: 'HH00000000000000000000000000000001',
  status: 'TWILIO_REJECTED',
  rejection_reason: 'opt-in evidence was not found on the website',
  rejection_reasons: [{ code: 30452, description: 'opt-in not documented' }],
  error_code: null,
  edit_allowed: true,
  edit_expiration: '2026-09-05T00:00:00Z',
  business_website: 'https://example.com',
  use_case_categories: ['TWO_FACTOR_AUTHENTICATION'],
  use_case_summary: 'One-time passcodes sent to customers who ask for them at sign-in.',
  opt_in_type: 'WEB_FORM',
  ...over,
});

test('a prohibited category beats an open edit window', () => {
  const [state, detail] = verdict(make({ rejection_reasons: [{ code: 30469 }] }), NOW);
  assert.equal(state, 'structural');
  assert.match(detail, /regardless of local legality/);
  assert.match(detail, /30469/);
});

test('codes classify the same as integers or strings', () => {
  assert.equal(isStructural(['30469']), true);
  assert.equal(isStructural([30469]), true);
  assert.equal(isStructural(['30452']), false);
  assert.equal(isStructural(['not a code', null]), false);
});

test('codes are collected from the array and the top level', () => {
  const codes = reasonCodes(make({
    rejection_reasons: [{ code: 30452 }, { error_code: '30453' }],
    error_code: 30452 }));
  assert.deepEqual(codes, ['30452', '30453']);
  assert.deepEqual(reasonCodes(make({ rejection_reasons: [], error_code: null })), []);
});

test('an open window is the cheap path', () => {
  const [state, detail] = verdict(make(), NOW);
  assert.equal(state, 'editable');
  assert.match(detail, /6 day\\(s\\) from now/);
});

test('a window about to close is its own state', () => {
  const [state, detail] = verdict(make({ edit_expiration: '2026-08-31T00:00:00Z' }), NOW);
  assert.equal(state, 'edit-closing');
  assert.match(detail, /lose the cheap path/);
});

test('an expired window overrides edit_allowed', () => {
  const [state, detail] = verdict(make({ edit_expiration: '2026-08-20T00:00:00Z' }), NOW);
  assert.equal(state, 'resubmit');
  assert.match(detail, /10 day\\(s\\) ago/);
});

test('edit_allowed false is a fresh submission', () => {
  const [state, detail] = verdict(make({ edit_allowed: false }), NOW);
  assert.equal(state, 'resubmit');
  assert.match(detail, /back of the review queue/);
});

test('a record that is not a rejection is left alone', () => {
  assert.equal(verdict(make({ status: 'TWILIO_APPROVED' }), NOW)[0], 'not-rejected');
});

test('gaps name what the reviewer had to work with', () => {
  assert.deepEqual(submissionGaps(make()), []);
  const gaps = submissionGaps(make({
    business_website: '', use_case_summary: 'OTPs',
    use_case_categories: [], opt_in_type: '' }));
  assert.equal(gaps.length, 4);
  assert.ok(gaps.some((g) => g.includes('business_website')));
  assert.ok(gaps.some((g) => g.includes('4 character(s)')));
});
''',
"faq": [
 ("How do I tell a structural rejection from a fixable one?",
  "By the code, not the prose. A prohibited-category code such as 30469 says the business is outside what US carriers will carry on A2P SMS, and no version of the submission passes. Anything else is about evidence: the opt-in flow, the summary, the sample content, the website. The prose reads the same in both cases, which is why the loop happens."),
 ("Our product is legal in our state. Why is this a rejection at all?",
  "Because the decision is a carrier content policy applied nationally, not a legal judgement about your jurisdiction. Cannabis, CBD, kratom, vape and fireworks sit outside it whatever the local law says. Appealing tends to produce the same answer, and the time it takes is time the toll-free traffic stays blocked."),
 ("What exactly does the edit window change?",
  "Whether you correct the record you have or file a new one. Inside the window, a POST to the existing verification SID with corrected fields keeps your place. Outside it, you file fresh and go to the back of the review queue, which on toll-free is measured in weeks. Nothing about the record's appearance changes when the window closes, so it has to be read."),
 ("The rejection prose is vague. Where else can I look?",
  "At what was submitted. use_case_summary, use_case_categories, opt_in_type and business_website are all on the record, and an empty website field or a twelve-character summary explains a vague rejection better than the note does. The script prints those gaps before the prose for that reason."),
 ("Can the script correct the record for me?",
  "No. Every path out of a rejection is a submission into a human review queue, with a limited window and a real cost to getting it wrong twice. The script tells you which path applies, how long you have, and what was thin about the last attempt; a person writes the correction."),
],
"related": [
 ("/twilio/tollfree-number-not-verified/", "A toll-free number blocked for want of verification"),
 ("/twilio/trusthub-customer-profile-rejected/", "The Customer Profile behind the verification"),
 ("/twilio/a2p-campaign-vetting-failed/", "A 10DLC campaign that failed vetting"),
],
"citations": [CITE_TFV, CITE_30469, CITE_30032, CITE_KEYS],
},

]
