#!/usr/bin/env python3
"""/stripe/ field notes, batch Y — the writing.

Same constraint as every other batch in this section: each note is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

Four notes about the part of disputes that happens before a dispute: the inquiry
you can still answer, the ratio the card networks are watching, the early fraud
warning you can still refund, and the authentication you did not ask for. Every
repair in this batch is either irreversible (a refund, a one-shot evidence
submission) or a Dashboard rule change that reprices every payment on the
account, which is exactly why none of it is automated here.
"""

CITE_DISPUTE_OBJ = ("The dispute object — Stripe API reference",
                    "https://docs.stripe.com/api/disputes/object")
CITE_DISPUTE_LIST = ("List all disputes — Stripe API reference",
                     "https://docs.stripe.com/api/disputes/list")
CITE_RESPONDING = ("Respond to disputes — Stripe Docs",
                   "https://docs.stripe.com/disputes/responding")
CITE_MONITORING = ("Dispute monitoring programs — Stripe Docs",
                   "https://docs.stripe.com/disputes/monitoring-programs")
CITE_MEASURING = ("Measuring disputes — Stripe Docs",
                  "https://docs.stripe.com/disputes/measuring")
CITE_EFW_OBJ = ("The early fraud warning object — Stripe API reference",
                "https://docs.stripe.com/api/radar/early_fraud_warnings/object")
CITE_PREVENTION = ("Dispute prevention best practices — Stripe Docs",
                   "https://docs.stripe.com/disputes/prevention/best-practices")
CITE_RADAR_RULES = ("Radar rules — Stripe Docs", "https://docs.stripe.com/radar/rules")
CITE_CHARGE_OBJ = ("The charge object — Stripe API reference",
                   "https://docs.stripe.com/api/charges/object")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

GUIDES = [

{
"slug": "inquiry-needs-response-ignored",
"title": "Inquiries sit unanswered and escalate into chargebacks",
"description": "Dispute sweeps filter on needs_response and never see the warning_ family. An inquiry answered in time never becomes a chargeback at all.",
"h1": "inquiries sit unanswered and escalate into chargebacks",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe warning_needs_response", "stripe inquiry vs chargeback",
             "stripe retrieval request", "stripe pre-dispute inquiry",
             "stripe dispute escalation"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Chargebacks appear to arrive from nowhere. Somebody pulls the history for one of them and finds it was visible in the API eleven days earlier, as an inquiry, with a deadline and a place to put evidence. Nothing was wrong with the alerting: the sweep looked for disputes whose status was <code>needs_response</code>, and at that point the status was <code>warning_needs_response</code>.",
"short_answer": """<p>Page <code>GET /v1/disputes</code> and read the <code>warning_</code> statuses, not just the bare ones. A dispute with <code>status</code> of <code>warning_needs_response</code> is a pre-dispute inquiry: the issuer is asking, no funds have moved, and it is not counted by any card-network monitoring programme yet.</p>
<p>Flag every one where <code>evidence_details.has_evidence</code> is <code>false</code>, sorted by <code>evidence_details.due_by</code>. Answering at this stage prevents the escalation entirely, which saves the funds, the dispute fee, and the entry in the ratio the networks watch. Accepting an inquiry does not resolve it &mdash; only evidence does.</p>""",
"problem": """<p>Stripe models the inquiry and the chargeback as the same object with different statuses. That is accurate to how the networks work and it is a trap for the obvious integration, because the natural filter &mdash; <code>status == "needs_response"</code> &mdash; is exact-match and silently excludes the entire <code>warning_</code> family. The alerting is not broken, it is scoped to the half of the lifecycle where you have already lost the cheap option.</p>
<p>What that costs is specific. An inquiry answered in time closes without escalating, so it never becomes a chargeback, never takes the funds, never attracts the dispute fee, and never enters the count that puts an account into a monitoring programme. The same dispute answered a week later, after escalation, does all four even if you win it. The window between those two outcomes is days long and is visible in the API for the whole of it.</p>""",
"why": """<p><strong>The status string looks like a different kind of object.</strong> <code>warning_needs_response</code> reads like a warning about something rather than a thing that needs a response. Integrations that branch on a list of statuses tend to have been written against the four everyone knows, and the <code>warning_</code> family gets added later, if ever.</p>
<p><strong>The webhook has the same shape.</strong> <code>charge.dispute.created</code> fires for inquiries too, and the handler that routes on <code>data.object.status</code> will fall through to its default branch. So the event arrived, was processed successfully, and was dropped on purpose by code nobody remembers writing.</p>
<p><strong>Nothing has moved yet, so nothing looks urgent.</strong> There is no balance transaction, no fee, no missing money. The only thing that exists is a deadline, and deadlines that are not attached to a visible loss do not get worked.</p>
<p><strong>Accepting is not an option here, and people assume it is.</strong> With a chargeback you can deliberately concede and close it. An inquiry has no such door: doing nothing is not conceding, it is waiting for the issuer to escalate on your behalf. Only submitted evidence ends it in your favour.</p>
<p><strong>A snapshot cannot prove which chargebacks began as inquiries.</strong> The status advances in place, so once it escalates the object no longer says it was ever a <code>warning_</code>. The only honest way to measure the leak is to record the status you saw at <code>charge.dispute.created</code> and compare later, which is why this script reports the current split rather than inventing a history it cannot read.</p>""",
"steps": [
 {"h": "Page the disputes list without a status filter",
  "body": """<p><code>GET /v1/disputes?limit=100</code>, paginated. Do not filter server-side on status; pull them all and split locally. The moment the filter lives in the query string, the next person to widen the set of statuses you care about has to remember it is there.</p>"""},
 {"h": "Split the list on the escalation line, not on urgency",
  "body": """<p>Three statuses are inquiries: <code>warning_needs_response</code>, <code>warning_under_review</code>, <code>warning_closed</code>. Four are chargebacks: <code>needs_response</code>, <code>under_review</code>, <code>won</code>, <code>lost</code>. That line is the whole note &mdash; everything to the left is cheap to fix and everything to the right is already counted against you.</p>"""},
 {"h": "Sort the open inquiries by due_by",
  "body": """<p><code>evidence_details.due_by</code> is a unix timestamp and it is the only ordering that matters. An inquiry with two days left and one with fifteen are the same row in a dashboard sorted by creation date, and very different tickets.</p>"""},
 {"h": "Read submission_count, not has_evidence",
  "body": """<p><code>has_evidence</code> flips to <code>true</code> the moment one field is saved, so a half-written response reads as handled. <code>submission_count</code> is what says the response actually went to the issuer. Staged and unsent is the most expensive state in the list, because the work was already done.</p>"""},
 {"h": "Report the inquiry-to-chargeback mix as a number",
  "body": """<p>Count the two families over the same window. A healthy account has more inquiries than chargebacks, because inquiries are the earlier stage of the same funnel. An account with almost no inquiries and plenty of chargebacks is either genuinely unlucky with its issuer mix or, much more often, not looking at the earlier stage at all.</p>"""},
 {"h": "Fix the webhook filter while you are here",
  "body": """<p>The sweep is a safety net; the event is the mechanism. Alert on <code>charge.dispute.created</code> where <code>data.object.status</code> <em>starts with</em> <code>warning_</code> as well as on the bare statuses, and the sweep should stop finding anything.</p>"""},
],
"verify": """<p>Re-run after the inquiries are answered. Everything answered moves to <code>warning_under_review</code>, and the unanswered count should be zero.</p>
<pre><code class="language-bash">python3 stripe_dispute_inquiries.py
# 31 dispute(s) read: 12 inquiry, 19 chargeback, 0 inquiry needing a response</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/disputes</code> and nothing else &mdash; a restricted key with read access to Disputes is enough, and is what you should give it. The status split is a pure function on its own, separate from the deadline classification, because the bug this note is about is a status list that was too short and that is the piece worth being able to read at a glance.",
"py_file": "stripe_dispute_inquiries.py",
"py": '''"""Report Stripe pre-dispute inquiries that nobody has answered.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Disputes. The response is printed, never submitted, because this script
holds a credential to a live payments account and dispute evidence can be sent
exactly once per dispute.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_dispute_inquiries")

API = "https://api.stripe.com/v1"

CRITICAL_HOURS = 72.0

# The inquiry side of the escalation line. No funds have moved and none of these
# are counted by a card network monitoring programme yet.
INQUIRY_OPEN = ("warning_needs_response",)
INQUIRY_ANSWERED = ("warning_under_review",)
INQUIRY_CLOSED = ("warning_closed",)

# The chargeback side. Funds are withdrawn, the dispute fee is charged, and the
# dispute counts toward the ratio whether it is later won or lost.
CHARGEBACK = ("needs_response", "under_review", "won", "lost")


def family(status):
    """Which side of the escalation line a dispute status sits on. Pure.

    This exists as its own function because the bug is almost always here: an
    integration matching only the four bare statuses drops every inquiry on the
    floor, and a list that is too short is invisible in a longer function.
    """
    if status in INQUIRY_OPEN + INQUIRY_ANSWERED + INQUIRY_CLOSED:
        return "inquiry"
    if status in CHARGEBACK:
        return "chargeback"
    return "unknown"


def classify(dispute, now, critical_hours=CRITICAL_HOURS):
    """Classify one dispute. Pure, so the deadline arithmetic can be tested.

    `now` is a unix timestamp. Returns (state, detail).

    The state that costs money is `unanswered`, and its worst variant is
    `staged`: evidence written and never sent, which forfeits the inquiry with
    the work already paid for.
    """
    status = dispute.get("status")
    side = family(status)

    if side == "unknown":
        return ("unknown", "unrecognised status %r" % (status,))
    if side == "chargeback":
        return ("escalated",
                "already a chargeback (%s). The funds and the dispute fee are "
                "gone and it counts toward the network ratio either way." % status)
    if status in INQUIRY_CLOSED:
        return ("closed", "inquiry closed without escalating")
    if status in INQUIRY_ANSWERED:
        return ("answered", "evidence is in and the issuer is reviewing it")

    ed = dispute.get("evidence_details") or {}
    due_by = ed.get("due_by")
    staged = bool(ed.get("has_evidence"))
    sent = ed.get("submission_count") or 0

    if sent:
        return ("answered", "%d submission(s) already sent" % sent)
    if staged:
        return ("staged",
                "evidence is staged but submission_count is 0. Nothing has "
                "reached the issuer, and doing nothing is not the same as "
                "accepting: only evidence closes an inquiry.")
    if due_by is None:
        return ("unanswered", "open inquiry with no due_by to measure against")

    hours = (due_by - now) / 3600.0
    if hours <= 0:
        return ("lapsing",
                "past due_by while unanswered. Expect this to escalate into a "
                "formal chargeback, with the fee and the ratio entry attached.")
    if hours <= critical_hours:
        return ("critical", "%.1f hour(s) left and nothing attached." % hours)
    return ("unanswered", "%.1f day(s) left to answer before escalation" % (hours / 24.0))


def money(dispute):
    """Amount at stake, in minor units.

    Not divided by 100, which is wrong for zero-decimal currencies such as JPY.
    A report that reads 100x low on one currency is worse than one that makes
    you read the currency code.
    """
    return "%s %s" % (dispute.get("amount"), (dispute.get("currency") or "?").upper())


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def disputes(session, limit):
    """Yield disputes, newest first, up to `limit`.

    Deliberately unfiltered. A server-side status filter is how the inquiries
    got missed in the first place.
    """
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/disputes", params)
        data = page.get("data", [])
        for d in data:
            yield d
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=float, default=CRITICAL_HOURS,
                    help="how close to due_by counts as critical")
    ap.add_argument("--max-disputes", type=int, default=1000,
                    help="stop paginating after this many disputes")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    counts = {"inquiry": 0, "chargeback": 0, "unknown": 0}
    open_inquiries = 0

    # Newest first, so collect and sort by deadline before printing: the order
    # the API returns them in is not the order you should work them in.
    rows = []
    for d in disputes(s, args.max_disputes):
        counts[family(d.get("status"))] += 1
        state, detail = classify(d, now, args.hours)
        if state in ("unanswered", "critical", "staged", "lapsing"):
            open_inquiries += 1
            rows.append(((d.get("evidence_details") or {}).get("due_by") or 0,
                         d, state, detail))

    for _due, d, state, detail in sorted(rows, key=lambda r: r[0]):
        log.warning("%-10s %s  %s  %s", state, d.get("id", "?"), money(d), detail)
        log.warning("  repair: POST %s/disputes/%s "
                    "-d 'evidence[uncategorized_text]=...' "
                    "-d 'evidence[product_description]=...' "
                    "-d 'evidence[shipping_tracking_number]=...'",
                    API, d["id"])
        log.warning("  evidence submits once per dispute, so assemble it all first")

    total = sum(counts.values())
    log.info("%d dispute(s) read: %d inquiry, %d chargeback, %d inquiry needing "
             "a response", total, counts["inquiry"], counts["chargeback"],
             open_inquiries)
    if counts["inquiry"] and counts["chargeback"] > counts["inquiry"]:
        log.info("more chargebacks than inquiries in this window: check that "
                 "charge.dispute.created is routed on statuses starting warning_")
    return 1 if open_inquiries else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-dispute-inquiries.mjs",
"js": '''/**
 * Report Stripe pre-dispute inquiries that nobody has answered.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Disputes. The response is printed, never submitted, because
 * dispute evidence can be sent exactly once per dispute.
 */
const API = 'https://api.stripe.com/v1';

export const CRITICAL_HOURS = 72;

const INQUIRY_OPEN = ['warning_needs_response'];
const INQUIRY_ANSWERED = ['warning_under_review'];
const INQUIRY_CLOSED = ['warning_closed'];
const CHARGEBACK = ['needs_response', 'under_review', 'won', 'lost'];

/**
 * Which side of the escalation line a dispute status sits on. Pure.
 */
export function family(status) {
  if (INQUIRY_OPEN.includes(status) || INQUIRY_ANSWERED.includes(status)
      || INQUIRY_CLOSED.includes(status)) {
    return 'inquiry';
  }
  if (CHARGEBACK.includes(status)) return 'chargeback';
  return 'unknown';
}

/**
 * Classify one dispute. Pure, so the deadline arithmetic can be tested.
 * `now` is a unix timestamp in seconds.
 */
export function classify(dispute, now, criticalHours = CRITICAL_HOURS) {
  const status = dispute.status;
  const side = family(status);

  if (side === 'unknown') {
    return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
  }
  if (side === 'chargeback') {
    return ['escalated',
      `already a chargeback (${status}). The funds and the dispute fee are gone ` +
      'and it counts toward the network ratio either way.'];
  }
  if (INQUIRY_CLOSED.includes(status)) {
    return ['closed', 'inquiry closed without escalating'];
  }
  if (INQUIRY_ANSWERED.includes(status)) {
    return ['answered', 'evidence is in and the issuer is reviewing it'];
  }

  const ed = dispute.evidence_details ?? {};
  const dueBy = ed.due_by;
  const staged = Boolean(ed.has_evidence);
  const sent = ed.submission_count ?? 0;

  if (sent) return ['answered', `${sent} submission(s) already sent`];
  if (staged) {
    return ['staged',
      'evidence is staged but submission_count is 0. Nothing has reached the ' +
      'issuer, and doing nothing is not the same as accepting: only evidence ' +
      'closes an inquiry.'];
  }
  if (dueBy === undefined || dueBy === null) {
    return ['unanswered', 'open inquiry with no due_by to measure against'];
  }

  const hours = (dueBy - now) / 3600;
  if (hours <= 0) {
    return ['lapsing',
      'past due_by while unanswered. Expect this to escalate into a formal ' +
      'chargeback, with the fee and the ratio entry attached.'];
  }
  if (hours <= criticalHours) {
    return ['critical', `${hours.toFixed(1)} hour(s) left and nothing attached.`];
  }
  return ['unanswered',
    `${(hours / 24).toFixed(1)} day(s) left to answer before escalation`];
}

/**
 * Amount at stake, in minor units. Not divided by 100, which is wrong for
 * zero-decimal currencies such as JPY.
 */
export function money(dispute) {
  return `${dispute.amount} ${(dispute.currency ?? '?').toUpperCase()}`;
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function* disputes(key, limit = 1000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/disputes', params);
    const data = page.data ?? [];
    for (const d of data) { yield d; seen += 1; }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const now = Date.now() / 1000;
  const counts = { inquiry: 0, chargeback: 0, unknown: 0 };
  const rows = [];

  for await (const d of disputes(key)) {
    counts[family(d.status)] += 1;
    const [state, detail] = classify(d, now);
    if (['unanswered', 'critical', 'staged', 'lapsing'].includes(state)) {
      rows.push([(d.evidence_details ?? {}).due_by ?? 0, d, state, detail]);
    }
  }

  rows.sort((a, b) => a[0] - b[0]);
  for (const [, d, state, detail] of rows) {
    console.warn(`${state.padEnd(10)} ${d.id ?? '?'}  ${money(d)}  ${detail}`);
    console.warn(`  repair: POST ${API}/disputes/${d.id} ` +
                 `-d 'evidence[uncategorized_text]=...' ` +
                 `-d 'evidence[product_description]=...' ` +
                 `-d 'evidence[shipping_tracking_number]=...'`);
    console.warn('  evidence submits once per dispute, so assemble it all first');
  }

  const total = counts.inquiry + counts.chargeback + counts.unknown;
  console.log(`${total} dispute(s) read: ${counts.inquiry} inquiry, ` +
              `${counts.chargeback} chargeback, ${rows.length} inquiry needing a response`);
  if (counts.inquiry && counts.chargeback > counts.inquiry) {
    console.log('more chargebacks than inquiries in this window: check that ' +
                'charge.dispute.created is routed on statuses starting warning_');
  }
  process.exitCode = rows.length ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. The first is that <code>lost</code> and <code>won</code> are on the chargeback side of the line, because the tempting shortcut &mdash; treat anything that is not <code>needs_response</code> as handled &mdash; puts them somewhere else and takes the inquiries with them. The second is staged evidence with a submission count of zero, which reads as answered on every field except the one the issuer sees.",
"test_py_file": "test_stripe_dispute_inquiries.py",
"test_py": '''from stripe_dispute_inquiries import classify, family

NOW = 1_700_000_000


def inquiry(hours_left, **evidence):
    ev = {"due_by": NOW + int(hours_left * 3600)}
    ev.update(evidence)
    return {"id": "du_1", "status": "warning_needs_response",
            "evidence_details": ev}


def test_the_warning_family_is_the_inquiry_side_of_the_line():
    assert family("warning_needs_response") == "inquiry"
    assert family("warning_under_review") == "inquiry"
    assert family("warning_closed") == "inquiry"


def test_settled_chargebacks_stay_on_the_chargeback_side():
    # The shortcut this guards against: "anything not needs_response is done".
    assert family("won") == "chargeback"
    assert family("lost") == "chargeback"
    assert family("needs_response") == "chargeback"
    assert family("sleeping") == "unknown"


def test_an_open_inquiry_with_nothing_attached_reports_days_left():
    state, detail = classify(inquiry(240), NOW)
    assert state == "unanswered"
    assert "10.0 day" in detail


def test_seventy_two_hours_is_the_boundary_and_it_is_inclusive():
    assert classify(inquiry(72), NOW)[0] == "critical"
    assert classify(inquiry(72.1), NOW)[0] == "unanswered"


def test_staged_evidence_that_was_never_submitted_is_its_own_state():
    state, detail = classify(
        inquiry(240, has_evidence=True, submission_count=0), NOW)
    assert state == "staged"
    assert "submission_count" in detail
    # And an inquiry that really was answered is not confused with it.
    assert classify(inquiry(240, has_evidence=True, submission_count=1), NOW)[0] == "answered"


def test_an_escalated_dispute_is_not_reported_as_an_open_inquiry():
    state, detail = classify({"status": "needs_response"}, NOW)
    assert state == "escalated"
    assert "fee" in detail
    assert classify(inquiry(-1), NOW)[0] == "lapsing"
''',
"test_js_file": "stripe-dispute-inquiries.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, family } from './stripe-dispute-inquiries.mjs';

const NOW = 1_700_000_000;

function inquiry(hoursLeft, evidence = {}) {
  return {
    id: 'du_1',
    status: 'warning_needs_response',
    evidence_details: { due_by: NOW + Math.round(hoursLeft * 3600), ...evidence },
  };
}

test('the warning family is the inquiry side of the line', () => {
  assert.equal(family('warning_needs_response'), 'inquiry');
  assert.equal(family('warning_under_review'), 'inquiry');
  assert.equal(family('warning_closed'), 'inquiry');
});

test('settled chargebacks stay on the chargeback side', () => {
  assert.equal(family('won'), 'chargeback');
  assert.equal(family('lost'), 'chargeback');
  assert.equal(family('needs_response'), 'chargeback');
  assert.equal(family('sleeping'), 'unknown');
});

test('an open inquiry with nothing attached reports days left', () => {
  const [state, detail] = classify(inquiry(240), NOW);
  assert.equal(state, 'unanswered');
  assert.match(detail, /10\\.0 day/);
});

test('seventy two hours is the boundary and it is inclusive', () => {
  assert.equal(classify(inquiry(72), NOW)[0], 'critical');
  assert.equal(classify(inquiry(72.1), NOW)[0], 'unanswered');
});

test('staged evidence that was never submitted is its own state', () => {
  const [state, detail] = classify(
    inquiry(240, { has_evidence: true, submission_count: 0 }), NOW);
  assert.equal(state, 'staged');
  assert.match(detail, /submission_count/);
  assert.equal(
    classify(inquiry(240, { has_evidence: true, submission_count: 1 }), NOW)[0],
    'answered');
});

test('an escalated dispute is not reported as an open inquiry', () => {
  const [state, detail] = classify({ status: 'needs_response' }, NOW);
  assert.equal(state, 'escalated');
  assert.match(detail, /fee/);
  assert.equal(classify(inquiry(-1), NOW)[0], 'lapsing');
});
''',
"faq": [
 ("What is the difference between a Stripe inquiry and a chargeback?",
  "An inquiry, exposed as a status starting with warning_, is the issuer asking about a transaction before filing anything. No funds have moved, no dispute fee is charged, and it is not counted by the card networks' monitoring programmes. A chargeback is the formal filing: the funds are withdrawn immediately, the fee applies, and it counts toward your ratio whether you later win it or lose it."),
 ("Why does my dispute alerting miss inquiries?",
  "Because it almost certainly matches status exactly against needs_response. Stripe uses the same dispute object for both stages and distinguishes them by a warning_ prefix, so an exact-match filter excludes the whole inquiry family without producing any error. The same happens in webhook handlers that switch on data.object.status."),
 ("Can I just accept an inquiry to make it go away?",
  "No. There is no equivalent of closing a dispute at the inquiry stage; doing nothing simply lets the issuer escalate. Submitting evidence is the only action that resolves an inquiry in your favour, which is why an unanswered inquiry is a decision nobody made rather than a decision to concede."),
 ("Does answering an inquiry guarantee it will not escalate?",
  "No, but it is the only lever you have, and it is a cheap one. The issuer can still file a chargeback afterwards. What answering removes is the case where it escalated purely because nothing came back, which is the population this script is built to find."),
 ("Can I measure how many of my chargebacks started as inquiries?",
  "Not from a snapshot. The status advances in place on the same object, so once it escalates there is no field saying it was ever an inquiry. To measure it properly, record data.object.status when charge.dispute.created fires and compare against the final status later. The script reports the current inquiry-to-chargeback mix instead, which is a proxy rather than a proof."),
],
"related": [
 ("/stripe/dispute-deadline-72h-no-evidence/", "Disputes are hours from due_by with no evidence attached"),
 ("/stripe/disputes-lost-without-response/", "Disputes closed as lost were never actually contested"),
 ("/stripe/dispute-rate-above-threshold/", "Dispute activity is above the 0.75% excessive threshold"),
],
"citations": [CITE_RESPONDING, CITE_DISPUTE_OBJ, CITE_MONITORING, CITE_KEYS],
},

{
"slug": "dispute-rate-above-threshold",
"title": "Dispute activity is above the 0.75% excessive threshold",
"description": "No single dispute looks alarming, but the ratio does. Count disputes and early fraud warnings against successful charges before a network does it for you.",
"h1": "dispute activity is above the 0.75% excessive threshold",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe dispute rate", "chargeback rate threshold",
             "visa vamp ratio", "mastercard excessive chargeback program",
             "stripe dispute monitoring program"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nobody in the company can say what the dispute rate is. Individually the disputes look ordinary and each one gets handled on its own terms, so the trend never gets discussed. The first hard signal is an email from Stripe naming a card network monitoring programme, a fine, and a remediation plan with a deadline on it.",
"short_answer": """<p>Count two things over a rolling calendar month and divide. Numerator: disputes from <code>GET /v1/disputes?created[gte]=...&amp;created[lt]=...</code>. Denominator: charges from <code>GET /v1/charges</code> over the same window where <code>status</code> is <code>succeeded</code> and <code>captured</code> is <code>true</code>.</p>
<p>Industry practice treats activity above <strong>0.75%</strong> as excessive. Visa's VAMP flags a merchant as non-compliant at <strong>0.5%</strong> and counts early fraud warnings in the same numerator, so add <code>GET /v1/radar/early_fraud_warnings</code> to it. Both programmes have a count floor &mdash; VAMP needs at least 5 countable events, Mastercard's ECM starts at 100 disputes &mdash; so a small account with a scary-looking ratio is not yet in scope.</p>""",
"problem": """<p>Every other note in this section is about an object you can point at. This one is about a quotient, and quotients have no owner. The disputes are handled by support, the charges are counted by finance, and the ratio between them is the thing the card networks act on and nobody computes.</p>
<p>It also moves for reasons that have nothing to do with fraud. A month with a promotion doubles the denominator and the rate improves without anything getting better. A month where marketing pauses spend halves the denominator and the rate deteriorates without anything getting worse. Because the number is only ever looked at after bad news arrives, this ordinary volatility gets read as a trend, and the wrong lever gets pulled.</p>
<p>And the consequence is not proportionate. Crossing a threshold is not a slightly worse month; it is a programme with monthly fines, a remediation plan, and in the worst case the loss of card acceptance. The gap between "fine" and "in a programme" is a few tenths of a percent that nothing in the Dashboard puts in front of you.</p>""",
"why": """<p><strong>The denominator is not obvious.</strong> Total charges includes failed and blocked attempts, which makes the rate look better than the one the networks compute. Total volume in currency units is a different number again. The comparable figure is a count of successful captured charges over the same calendar month as the numerator, and getting that wrong by a plausible-looking definition moves the answer by more than the entire margin between compliant and not.</p>
<p><strong>Early fraud warnings count too, for Visa.</strong> VAMP's ratio adds EFWs to disputes in the numerator, so an account that refunds every actionable EFW diligently &mdash; the right thing to do, and the subject of its own note &mdash; still carries every one of them in this ratio. Refunding avoids the second count as a chargeback; it does not remove the first.</p>
<p><strong>Won disputes still count.</strong> The ratio is about how much dispute activity your traffic generates, not how much of it you deserved. A month of successfully defended disputes reads to the networks exactly like a month of lost ones.</p>
<p><strong>The thresholds are not one number.</strong> Stripe's guidance names 0.75% as excessive. VAMP is non-compliant at 0.5% and excessive at 1.5%, with a higher band in some regions. Mastercard's ECM starts at 100 disputes and 1.5%. A single hard-coded limit will either cry wolf or arrive late, so the script reports where you sit against all of them and applies the count floors.</p>
<p><strong>A truncated denominator is worse than no answer.</strong> Charge pagination on a busy account is thousands of pages. Stopping early and dividing anyway produces a confidently wrong number that reads high, which is why the script refuses to report a ratio it could not count in full.</p>""",
"steps": [
 {"h": "Fix the window before you count anything",
  "body": """<p>Use a calendar month, and use the same <code>created[gte]</code> and <code>created[lt]</code> bounds for all three lists. A rolling 30 days and a calendar month give different answers, and the programmes are assessed monthly.</p>"""},
 {"h": "Count disputes over that window",
  "body": """<p><code>GET /v1/disputes?created[gte]=&lt;start&gt;&amp;created[lt]=&lt;end&gt;&amp;limit=100</code>, paginated. Every status counts, including <code>won</code> and the <code>warning_</code> family is the one thing that does not &mdash; unescalated inquiries are not counted by the programmes.</p>"""},
 {"h": "Count successful captured charges over the same window",
  "body": """<p>The denominator is <code>status == "succeeded"</code> and <code>captured == true</code>. Not attempts, not authorisations, not volume. This is the expensive half of the job on a busy account, so page it properly and fail loudly if you hit your own cap.</p>"""},
 {"h": "Add early fraud warnings for the VAMP ratio",
  "body": """<p><code>GET /v1/radar/early_fraud_warnings</code> over the same bounds. Report both ratios: disputes alone, which is what Stripe's 0.75% guidance is about, and disputes plus EFWs, which is what Visa measures.</p>"""},
 {"h": "Apply the count floors before you panic",
  "body": """<p>Four disputes on two hundred charges is 2% and is not a programme risk, because VAMP needs at least five countable events and ECM needs a hundred disputes. Report it as a signal, not as a breach. Conflating the two is how a small account spends a week rebuilding its checkout over noise.</p>"""},
 {"h": "Run it monthly, and keep the history",
  "body": """<p>One number in isolation says almost nothing. Twelve of them say whether you are drifting toward a threshold, which is the only version of this that is actionable while it is still cheap to act.</p>"""},
],
"verify": """<p>Re-run for the previous month. The ratios should be under 0.5% and the state should read <code>clear</code>.</p>
<pre><code class="language-bash">python3 stripe_dispute_rate.py --month 2026-07
# clear  disputes 9 / charges 4,812 = 0.187%  (with EFW: 0.249%)</code></pre>""",
"code_intro": "Three paginated GETs and no writes &mdash; a restricted key with read access to Disputes, Charges and Early Fraud Warnings is enough. The arithmetic is a pure function taking three integers, because everything difficult about this check is in what you decide to count, and that decision should be readable in one place instead of tangled through a pagination loop.",
"py_file": "stripe_dispute_rate.py",
"py": '''"""Measure the Stripe dispute rate against the card network thresholds.

Read only. Three paginated GETs and no writes: give this a RESTRICTED key with
read access to Disputes, Charges and Early Fraud Warnings. There is no API
toggle to repair this, so nothing here could write even if it wanted to; the
remediation is printed instead.
"""
import argparse
import calendar
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_dispute_rate")

API = "https://api.stripe.com/v1"

# Visa VAMP flags a merchant as non-compliant here.
WARN_RATE = 0.005
# Industry practice, and Stripe's own guidance, treats this as excessive.
EXCESSIVE_RATE = 0.0075
# Visa VAMP excessive, and Mastercard ECM once its own count floor is met.
PROGRAM_RATE = 0.015

# Below these counts the programmes do not apply, whatever the ratio says.
VAMP_FLOOR = 5      # disputes plus early fraud warnings
ECM_FLOOR = 100     # disputes alone


def rates(disputes, efws, charges):
    """Return (dispute_rate, vamp_rate). Pure.

    Both are None when there were no successful charges. A month with disputes
    and no charges is a data problem, not an infinite rate, and printing
    infinity would bury the real message.
    """
    if not charges:
        return (None, None)
    return (disputes / charges, (disputes + efws) / charges)


def assess(disputes, efws, charges,
           warn=WARN_RATE, excessive=EXCESSIVE_RATE, program=PROGRAM_RATE):
    """Classify a month of dispute activity. Pure. Returns (state, detail).

    The ratio and the count floors are separate tests on purpose: a high ratio
    on a handful of events is a signal worth reading, but it is not a breach,
    and reporting it as one wastes the credibility of the check.
    """
    dispute_rate, vamp_rate = rates(disputes, efws, charges)
    if dispute_rate is None:
        return ("no_volume",
                "no successful captured charges in the window; there is nothing "
                "to divide by")

    events = disputes + efws
    pct = "disputes %.3f%%, with EFW %.3f%%" % (dispute_rate * 100, vamp_rate * 100)

    if vamp_rate < warn:
        return ("clear", "%s, both under the %.2f%% VAMP line" % (pct, warn * 100))

    if events < VAMP_FLOOR and disputes < ECM_FLOOR:
        return ("below_floor",
                "%s, but only %d countable event(s). VAMP needs %d and ECM needs "
                "%d disputes, so no programme applies yet."
                % (pct, events, VAMP_FLOOR, ECM_FLOOR))

    if dispute_rate >= program or vamp_rate >= program:
        return ("program",
                "%s. At or above %.2f%% this is VAMP excessive territory, and "
                "Mastercard ECM once you pass %d disputes in a month."
                % (pct, program * 100, ECM_FLOOR))
    if dispute_rate >= excessive or vamp_rate >= excessive:
        return ("excessive",
                "%s. Above the %.2f%% the industry treats as excessive; expect "
                "monitoring before it reaches %.2f%%."
                % (pct, excessive * 100, program * 100))
    return ("watch",
            "%s. At or above the %.2f%% VAMP non-compliant line and below the "
            "%.2f%% excessive line: the month to act in."
            % (pct, warn * 100, excessive * 100))


def month_bounds(month):
    """Unix bounds for a YYYY-MM string, or the previous calendar month."""
    if month:
        year, mon = (int(p) for p in month.split("-"))
    else:
        today = dt.date.today()
        year, mon = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    start = dt.datetime(year, mon, 1, tzinfo=dt.timezone.utc)
    last = calendar.monthrange(year, mon)[1]
    end = dt.datetime(year, mon, last, 23, 59, 59, tzinfo=dt.timezone.utc)
    return int(start.timestamp()), int(end.timestamp()) + 1, "%04d-%02d" % (year, mon)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def count(session, path, start, end, cap, keep=None):
    """Count objects in a created range. Returns (count, truncated).

    `truncated` is the whole point of the return being a tuple: a denominator
    that stopped early makes the ratio read high, and a confidently wrong ratio
    is worse than refusing to print one.
    """
    total = 0
    scanned = 0
    params = {"limit": 100, "created[gte]": start, "created[lt]": end}
    while True:
        page = get(session, path, params)
        data = page.get("data", [])
        for obj in data:
            scanned += 1
            if keep is None or keep(obj):
                total += 1
        if not data or not page.get("has_more"):
            return total, False
        if scanned >= cap:
            return total, True
        params["starting_after"] = data[-1]["id"]


def succeeded_and_captured(charge):
    return charge.get("status") == "succeeded" and charge.get("captured") is True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--month", help="YYYY-MM; defaults to the previous calendar month")
    ap.add_argument("--max-charges", type=int, default=50000,
                    help="refuse to report a ratio if the denominator needs more than this")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    start, end, label = month_bounds(args.month)
    log.info("counting %s", label)

    disputes, _ = count(s, "/disputes", start, end, cap=100000)
    efws, _ = count(s, "/radar/early_fraud_warnings", start, end, cap=100000)
    charges, truncated = count(s, "/charges", start, end,
                               cap=args.max_charges, keep=succeeded_and_captured)

    if truncated:
        log.error("stopped after %d charges, so the denominator is short and the "
                  "ratio would read high. Raise --max-charges or narrow the window.",
                  args.max_charges)
        return 2

    state, detail = assess(disputes, efws, charges)
    line = "%-12s %d dispute(s), %d EFW(s), %d successful charge(s): %s" % (
        state, disputes, efws, charges, detail)
    if state in ("clear", "no_volume"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  there is no API repair for a ratio: reduce the numerator.")
    log.warning("  block highest risk in Radar, request 3DS on elevated risk,")
    log.warning("  refund actionable early fraud warnings before they escalate,")
    log.warning("  set a recognisable statement descriptor, and make cancelling self-serve.")
    log.warning("  remediation guidance: https://docs.stripe.com/disputes/monitoring-programs")
    return 1 if state != "below_floor" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-dispute-rate.mjs",
"js": '''/**
 * Measure the Stripe dispute rate against the card network thresholds.
 *
 * Read only. Three paginated GETs and no writes: give this a RESTRICTED key
 * with read access to Disputes, Charges and Early Fraud Warnings. There is no
 * API toggle to repair this; the remediation is printed instead.
 */
const API = 'https://api.stripe.com/v1';

export const WARN_RATE = 0.005;      // Visa VAMP non-compliant
export const EXCESSIVE_RATE = 0.0075; // industry and Stripe guidance
export const PROGRAM_RATE = 0.015;   // VAMP excessive, Mastercard ECM

export const VAMP_FLOOR = 5;   // disputes plus early fraud warnings
export const ECM_FLOOR = 100;  // disputes alone

/**
 * Return [disputeRate, vampRate], or [null, null] with no charges. Pure.
 */
export function rates(disputes, efws, charges) {
  if (!charges) return [null, null];
  return [disputes / charges, (disputes + efws) / charges];
}

/**
 * Classify a month of dispute activity. Pure. Returns [state, detail].
 */
export function assess(disputes, efws, charges,
                       warn = WARN_RATE, excessive = EXCESSIVE_RATE,
                       program = PROGRAM_RATE) {
  const [disputeRate, vampRate] = rates(disputes, efws, charges);
  if (disputeRate === null) {
    return ['no_volume',
      'no successful captured charges in the window; there is nothing to divide by'];
  }

  const events = disputes + efws;
  const pct = `disputes ${(disputeRate * 100).toFixed(3)}%, ` +
              `with EFW ${(vampRate * 100).toFixed(3)}%`;

  if (vampRate < warn) {
    return ['clear', `${pct}, both under the ${(warn * 100).toFixed(2)}% VAMP line`];
  }
  if (events < VAMP_FLOOR && disputes < ECM_FLOOR) {
    return ['below_floor',
      `${pct}, but only ${events} countable event(s). VAMP needs ${VAMP_FLOOR} ` +
      `and ECM needs ${ECM_FLOOR} disputes, so no programme applies yet.`];
  }
  if (disputeRate >= program || vampRate >= program) {
    return ['program',
      `${pct}. At or above ${(program * 100).toFixed(2)}% this is VAMP excessive ` +
      `territory, and Mastercard ECM once you pass ${ECM_FLOOR} disputes in a month.`];
  }
  if (disputeRate >= excessive || vampRate >= excessive) {
    return ['excessive',
      `${pct}. Above the ${(excessive * 100).toFixed(2)}% the industry treats as ` +
      `excessive; expect monitoring before it reaches ${(program * 100).toFixed(2)}%.`];
  }
  return ['watch',
    `${pct}. At or above the ${(warn * 100).toFixed(2)}% VAMP non-compliant line ` +
    `and below the ${(excessive * 100).toFixed(2)}% excessive line: the month to act in.`];
}

/** Unix bounds for a YYYY-MM string, or the previous calendar month. */
export function monthBounds(month) {
  let year;
  let mon;
  if (month) {
    [year, mon] = month.split('-').map(Number);
  } else {
    const now = new Date();
    year = now.getUTCMonth() > 0 ? now.getUTCFullYear() : now.getUTCFullYear() - 1;
    mon = now.getUTCMonth() > 0 ? now.getUTCMonth() : 12;
  }
  const start = Date.UTC(year, mon - 1, 1) / 1000;
  const end = Date.UTC(mon === 12 ? year + 1 : year, mon === 12 ? 0 : mon, 1) / 1000;
  return [start, end, `${String(year).padStart(4, '0')}-${String(mon).padStart(2, '0')}`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function countObjects(key, path, start, end, cap, keep) {
  let total = 0;
  let scanned = 0;
  const params = { limit: 100, 'created[gte]': start, 'created[lt]': end };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const obj of data) {
      scanned += 1;
      if (!keep || keep(obj)) total += 1;
    }
    if (data.length === 0 || !page.has_more) return [total, false];
    if (scanned >= cap) return [total, true];
    params.starting_after = data[data.length - 1].id;
  }
}

export function succeededAndCaptured(charge) {
  return charge.status === 'succeeded' && charge.captured === true;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const monthArg = process.argv.includes('--month')
    ? process.argv[process.argv.indexOf('--month') + 1] : undefined;
  const maxCharges = process.argv.includes('--max-charges')
    ? Number(process.argv[process.argv.indexOf('--max-charges') + 1]) : 50000;

  const [start, end, label] = monthBounds(monthArg);
  console.log(`counting ${label}`);

  const [disputes] = await countObjects(key, '/disputes', start, end, 100000);
  const [efws] = await countObjects(key, '/radar/early_fraud_warnings', start, end, 100000);
  const [charges, truncated] = await countObjects(
    key, '/charges', start, end, maxCharges, succeededAndCaptured);

  if (truncated) {
    console.error(`stopped after ${maxCharges} charges, so the denominator is ` +
                  'short and the ratio would read high. Raise --max-charges or ' +
                  'narrow the window.');
    process.exitCode = 2;
    return;
  }

  const [state, detail] = assess(disputes, efws, charges);
  const line = `${state.padEnd(12)} ${disputes} dispute(s), ${efws} EFW(s), ` +
               `${charges} successful charge(s): ${detail}`;
  if (state === 'clear' || state === 'no_volume') {
    console.log(line);
    return;
  }

  console.warn(line);
  console.warn('  there is no API repair for a ratio: reduce the numerator.');
  console.warn('  block highest risk in Radar, request 3DS on elevated risk,');
  console.warn('  refund actionable early fraud warnings before they escalate,');
  console.warn('  set a recognisable statement descriptor, and make cancelling self-serve.');
  console.warn('  remediation guidance: https://docs.stripe.com/disputes/monitoring-programs');
  process.exitCode = state === 'below_floor' ? 0 : 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases that matter here are the ones where the ratio and the reality disagree. A tiny account can post 1.5% on three events and be in no programme at all, and an account with a perfectly respectable dispute rate can be non-compliant on Visa's ratio purely because of early fraud warnings it already refunded. Both are pinned, along with the boundary, because a check that fires at 0.51% instead of 0.5% costs you the month you needed.",
"test_py_file": "test_stripe_dispute_rate.py",
"test_py": '''from stripe_dispute_rate import assess, rates


def test_no_successful_charges_is_not_an_infinite_rate():
    assert rates(3, 0, 0) == (None, None)
    state, detail = assess(3, 0, 0)
    assert state == "no_volume"
    assert "divide" in detail


def test_the_half_percent_vamp_line_is_inclusive():
    # 10 / 2000 is exactly 0.5%, which is already non-compliant.
    assert assess(10, 0, 2000)[0] == "watch"
    assert assess(9, 0, 2000)[0] == "clear"


def test_early_fraud_warnings_count_toward_the_visa_ratio():
    # 0.2% on disputes alone, 0.6% once EFWs join the numerator.
    dispute_rate, vamp_rate = rates(4, 8, 2000)
    assert dispute_rate < 0.005 < vamp_rate
    state, detail = assess(4, 8, 2000)
    assert state == "watch"
    assert "EFW" in detail


def test_a_high_ratio_under_the_count_floor_is_not_a_breach():
    # 3 countable events is below VAMP's floor of 5 and ECM's of 100,
    # so 1.5% here is a signal and not a programme risk.
    state, detail = assess(2, 1, 200)
    assert state == "below_floor"
    assert "VAMP needs 5" in detail


def test_the_bands_above_the_line_are_distinct():
    assert assess(16, 0, 2000)[0] == "excessive"   # 0.8%
    assert assess(40, 0, 2000)[0] == "program"     # 2.0%
    assert assess(11, 0, 2000)[0] == "watch"       # 0.55%
''',
"test_js_file": "stripe-dispute-rate.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assess, rates } from './stripe-dispute-rate.mjs';

test('no successful charges is not an infinite rate', () => {
  assert.deepEqual(rates(3, 0, 0), [null, null]);
  const [state, detail] = assess(3, 0, 0);
  assert.equal(state, 'no_volume');
  assert.match(detail, /divide/);
});

test('the half percent vamp line is inclusive', () => {
  assert.equal(assess(10, 0, 2000)[0], 'watch');
  assert.equal(assess(9, 0, 2000)[0], 'clear');
});

test('early fraud warnings count toward the visa ratio', () => {
  const [disputeRate, vampRate] = rates(4, 8, 2000);
  assert.ok(disputeRate < 0.005);
  assert.ok(vampRate > 0.005);
  const [state, detail] = assess(4, 8, 2000);
  assert.equal(state, 'watch');
  assert.match(detail, /EFW/);
});

test('a high ratio under the count floor is not a breach', () => {
  const [state, detail] = assess(2, 1, 200);
  assert.equal(state, 'below_floor');
  assert.match(detail, /VAMP needs 5/);
});

test('the bands above the line are distinct', () => {
  assert.equal(assess(16, 0, 2000)[0], 'excessive');
  assert.equal(assess(40, 0, 2000)[0], 'program');
  assert.equal(assess(11, 0, 2000)[0], 'watch');
});
''',
"faq": [
 ("What dispute rate is too high for Stripe?",
  "Industry practice, and Stripe's own guidance, treats dispute activity above 0.75% as excessive. The card networks set their own lines: Visa's VAMP marks a merchant non-compliant at 0.5% and excessive at 1.5%, and Mastercard's ECM begins at 100 disputes and a 1.5% rate. A sharp spike can also attract attention below any of those numbers."),
 ("What exactly goes in the denominator?",
  "A count of successful, captured charges over the same calendar month as the numerator. Not attempts, because failed and Radar-blocked charges never reached the network. Not currency volume, because the ratio is counted per transaction. Getting this wrong in either direction moves the answer by more than the whole margin between compliant and not."),
 ("Do disputes I won still count against me?",
  "Yes. The ratio measures how much dispute activity your traffic generates, not how much of it was justified. A month of successfully defended disputes looks identical to the networks as a month of lost ones, which is why winning disputes is not a strategy for staying out of a monitoring programme."),
 ("Why are early fraud warnings in the numerator?",
  "Because Visa counts them there. VAMP's ratio combines disputes and EFWs, so refunding an actionable EFW prevents it being counted a second time as a chargeback but does not remove the first count. That is a good reason to refund them promptly and a bad reason to expect the ratio to drop immediately."),
 ("There is no API call to fix this, so what does the script give me?",
  "A number, monthly, that somebody owns. The repairs are all indirect: block highest-risk payments in Radar, request 3D Secure on elevated risk, refund actionable early fraud warnings, use a statement descriptor customers recognise, and let people cancel without emailing you. The script tells you whether those are working before a network tells you they were not."),
],
"related": [
 ("/stripe/efw-actionable-not-refunded/", "Actionable early fraud warnings were never refunded"),
 ("/stripe/no-3ds-on-elevated-risk/", "Elevated-risk card charges are captured with no 3DS"),
 ("/stripe/highest-risk-charges-succeeded/", "Highest-risk charges are succeeding instead of being blocked"),
],
"citations": [CITE_MEASURING, CITE_MONITORING, CITE_DISPUTE_LIST, CITE_KEYS],
},

{
"slug": "efw-actionable-not-refunded",
"title": "Actionable early fraud warnings were never refunded",
"description": "The issuer has told you a charge is fraud and the money is still yours to give back. Join actionable EFWs to their charges and find the ones untouched.",
"h1": "actionable early fraud warnings were never refunded",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe early fraud warning", "radar early_fraud_warnings actionable",
             "stripe efw refund", "stripe fraud warning not refunded",
             "radar.early_fraud_warning.created"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A batch of fraud disputes lands in the same week, all on charges from a month earlier. Each of those charges already carried an early fraud warning at the time, sitting in the API with <code>actionable</code> set to <code>true</code>, which is Stripe saying in as many words that you could still refund it. Nobody was subscribed to the event and nobody swept for it, so the window opened and closed unobserved.",
"short_answer": """<p>Page <code>GET /v1/radar/early_fraud_warnings?created[gte]=&lt;now-90d&gt;</code> and keep the ones where <code>actionable</code> is <code>true</code>. For each, read the charge it names with <code>GET /v1/charges/{id}</code> and flag it when <code>disputed</code> is <code>false</code>, <code>refunded</code> is <code>false</code> and <code>amount_refunded</code> is <code>0</code>.</p>
<p>An EFW is actionable exactly while it has not received a dispute and has not been fully refunded. That is the only window in which a voluntary refund costs you the goods and nothing else: after it closes the same transaction arrives as a fraud dispute, with the funds withdrawn, the dispute fee charged, and an entry in the ratio the card networks watch.</p>""",
"problem": """<p>An early fraud warning is the issuer telling you, ahead of any dispute, that the cardholder has reported this transaction as fraud. It is the rarest thing in payments: advance notice with an action attached. The action is a refund, and the cost of taking it is losing a sale you were going to lose anyway.</p>
<p>The reason it gets missed is that nothing about it is loud. No money moves when an EFW arrives. There is no queue in the Dashboard that fills up, no failing job, no customer writing in. The object appears, the <code>actionable</code> flag is <code>true</code> for a while, and then the same transaction reappears weeks later as a dispute where it looks like an ordinary chargeback with no history.</p>
<p>The second cost is the one that is hard to argue back. Both the warning and the resulting chargeback are counted by Visa's VAMP ratio, so ignoring the warning does not save you one entry &mdash; it buys you a second one, plus the fee, plus the loss of whatever you shipped in the meantime.</p>""",
"why": """<p><strong>The flag means something narrower than it sounds.</strong> <code>actionable</code> is <code>true</code> while the warning has received no dispute and has not been fully refunded. It is not a judgement about how convincing the fraud claim is; it is a statement about whether the door is still open. Reading it as a severity score is why the low-value ones get skipped and then escalate anyway.</p>
<p><strong>A partial refund does not close the door.</strong> Refunding shipping, or the difference after a restocking fee, leaves the charge partly funded and the warning still actionable. Any check that treats a non-zero <code>amount_refunded</code> as handled will report the account clean while the disputes are still coming.</p>
<p><strong>The join is two calls, and the second one is the one that gets dropped.</strong> The EFW object carries a <code>charge</code> id, not the charge's refund state. Everything you need to decide lives on the charge, so a script that reports the warnings without fetching them tells you what you already knew.</p>
<p><strong>Nobody subscribed to the event.</strong> <code>radar.early_fraud_warning.created</code> is not in anyone's default enabled_events list, so the notice that was designed to be pushed to you sits waiting to be pulled.</p>
<p><strong>The pattern in fraud_type is the part that changes what you do.</strong> One <code>made_with_stolen_card</code> is a bad customer. Fifteen in three days is an attack in progress, and the response to that is a Radar rule, not fifteen refunds.</p>""",
"steps": [
 {"h": "List warnings over a window wide enough to include the escalations",
  "body": """<p><code>GET /v1/radar/early_fraud_warnings?created[gte]=&lt;unix&gt;&amp;limit=100</code>, paginated. Ninety days is a reasonable default: long enough that you can see which of the older warnings became disputes, which is the number that tells you whether the process is working.</p>"""},
 {"h": "Trust the actionable flag rather than recomputing it",
  "body": """<p>Stripe maintains <code>actionable</code> against the dispute and refund state for you. Filter on it first and you cut the number of charge lookups to the population that still has a door open.</p>"""},
 {"h": "Fetch the charge, because the decision lives there",
  "body": """<p><code>GET /v1/charges/{efw.charge}</code>. Three fields decide it: <code>disputed</code>, <code>refunded</code> and <code>amount_refunded</code>. Compare <code>amount_refunded</code> against <code>amount</code> rather than against zero, so a partial refund is reported as the unfinished thing it is.</p>"""},
 {"h": "Sort by age, then by amount",
  "body": """<p>Age first, because the window is what you are racing. Amount second, because if you can only work half the list today it should be the expensive half. Sorting by amount alone is how a two-week-old warning outlives its window while somebody handles a fresh one worth more.</p>"""},
 {"h": "Group by fraud_type before you start refunding",
  "body": """<p>A cluster of <code>made_with_stolen_card</code> or <code>unauthorized_use_of_card</code> in a short window is a campaign against your checkout. Refunding each one individually treats the symptom and leaves the source running for another week.</p>"""},
 {"h": "Subscribe to the event so the sweep finds nothing",
  "body": """<p>Add <code>radar.early_fraud_warning.created</code> to a webhook endpoint and route it to a person. A daily sweep is a good backstop and a poor primary: the window is measured in days, and half of it is gone by the time a nightly job runs.</p>"""},
],
"verify": """<p>Re-run after the refunds go through. Everything refunded in full drops out of the actionable set, and the flagged count should be zero.</p>
<pre><code class="language-bash">python3 stripe_efw_actionable.py --days 90
# 41 warning(s) read, 0 actionable and unrefunded</code></pre>""",
"code_intro": "A paginated GET over the warnings and one GET per actionable warning &mdash; a restricted key with read access to Early Fraud Warnings and Charges is enough. The classification is a pure function taking the warning and its charge together, because the whole judgement is the join between them, and the partial-refund case is the one that quietly breaks when it is written inline.",
"py_file": "stripe_efw_actionable.py",
"py": '''"""Report Stripe early fraud warnings that can still be refunded.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Early Fraud Warnings and Charges. The refund is printed, never issued, because
this script holds a credential to a live payments account and a refund cannot be
undone.
"""
import argparse
import collections
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_efw_actionable")

API = "https://api.stripe.com/v1"


def classify(efw, charge, now):
    """Classify one warning against its charge. Pure. Returns (state, detail).

    `charge` is the charge object the warning names, or None if it could not be
    read. The state that costs money is `actionable`: the issuer has reported
    fraud, no dispute has been filed yet, and the money is still yours to give
    back.
    """
    if not efw.get("actionable", False):
        return ("not_actionable",
                "Stripe no longer counts this as actionable: it has already "
                "been disputed or fully refunded")
    if charge is None:
        return ("unknown", "the charge named by this warning could not be read")

    if charge.get("disputed"):
        return ("escalated",
                "the warning became a dispute. The refund window is closed, the "
                "dispute fee applies, and it now counts twice toward the ratio.")

    amount = charge.get("amount") or 0
    refunded = charge.get("amount_refunded") or 0
    if charge.get("refunded") or (amount and refunded >= amount):
        return ("refunded", "fully refunded before it could escalate")
    if refunded:
        return ("partial",
                "%d of %d refunded. A partial refund does not close the window: "
                "the warning is still actionable and can still become a dispute."
                % (refunded, amount))

    created = efw.get("created")
    if created is None:
        return ("actionable", "unrefunded, with no created timestamp to age it by")
    days = (now - created) / 86400.0
    return ("actionable",
            "%.1f day(s) old, %d %s unrefunded, no dispute filed yet"
            % (days, amount, (charge.get("currency") or "?").upper()))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def warnings(session, since, limit):
    """Yield early fraud warnings created since `since`, newest first."""
    seen = 0
    params = {"limit": 100, "created[gte]": int(since)}
    while True:
        page = get(session, "/radar/early_fraud_warnings", params)
        data = (page or {}).get("data", [])
        for w in data:
            yield w
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def charge_id(efw):
    """The warning carries `charge` as an id, or expanded as an object."""
    ch = efw.get("charge")
    return ch.get("id") if isinstance(ch, dict) else ch


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to read warnings")
    ap.add_argument("--max-warnings", type=int, default=1000,
                    help="stop paginating after this many warnings")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    since = now - args.days * 86400
    types = collections.Counter()
    rows = []
    seen = 0

    for w in warnings(s, since, args.max_warnings):
        seen += 1
        types[w.get("fraud_type") or "unknown"] += 1
        cid = charge_id(w)
        # Only actionable warnings are worth a second request; Stripe has
        # already done the dispute and refund bookkeeping behind that flag.
        charge = get(s, "/charges/" + cid) if (w.get("actionable") and cid) else None
        state, detail = classify(w, charge, now)
        if state in ("actionable", "partial", "unknown"):
            rows.append((w.get("created") or 0, w, cid, state, detail))

    # Oldest first: the window is the thing being raced, and a fresh warning
    # worth more can wait a day where a two week old one cannot.
    for _created, w, cid, state, detail in sorted(rows, key=lambda r: r[0]):
        log.warning("%-12s %s  charge=%s  %s  %s",
                    state, w.get("id", "?"), cid, w.get("fraud_type", "?"), detail)
        if state == "unknown":
            continue
        log.warning("  repair: POST %s/refunds -d charge=%s -d reason=fraudulent",
                    API, cid)
        log.warning("  or Dashboard, the payment, Refund as fraud, which also adds "
                    "the card fingerprint and email to your block lists")

    log.info("%d warning(s) read, %d actionable and unrefunded", seen, len(rows))
    if types:
        log.info("by fraud_type: %s",
                 ", ".join("%s=%d" % (k, v) for k, v in types.most_common()))
        top, count = types.most_common(1)[0]
        if seen and count >= 10 and count / seen > 0.5:
            log.warning("%d of %d warnings are %s: that is a campaign, and a Radar "
                        "rule will do more than %d refunds", count, seen, top, count)
    log.info("subscribe to radar.early_fraud_warning.created so this sweep is a "
             "backstop rather than the only notice you get")
    return 1 if rows else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-efw-actionable.mjs",
"js": '''/**
 * Report Stripe early fraud warnings that can still be refunded.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to Early Fraud Warnings and Charges. The refund is printed, never issued,
 * because a refund cannot be undone.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one warning against its charge. Pure. Returns [state, detail].
 * `charge` is the charge the warning names, or null if it could not be read.
 */
export function classify(efw, charge, now) {
  if (!efw.actionable) {
    return ['not_actionable',
      'Stripe no longer counts this as actionable: it has already been ' +
      'disputed or fully refunded'];
  }
  if (charge === null || charge === undefined) {
    return ['unknown', 'the charge named by this warning could not be read'];
  }

  if (charge.disputed) {
    return ['escalated',
      'the warning became a dispute. The refund window is closed, the dispute ' +
      'fee applies, and it now counts twice toward the ratio.'];
  }

  const amount = charge.amount ?? 0;
  const refunded = charge.amount_refunded ?? 0;
  if (charge.refunded || (amount && refunded >= amount)) {
    return ['refunded', 'fully refunded before it could escalate'];
  }
  if (refunded) {
    return ['partial',
      `${refunded} of ${amount} refunded. A partial refund does not close the ` +
      'window: the warning is still actionable and can still become a dispute.'];
  }

  const created = efw.created;
  if (created === undefined || created === null) {
    return ['actionable', 'unrefunded, with no created timestamp to age it by'];
  }
  const days = (now - created) / 86400;
  return ['actionable',
    `${days.toFixed(1)} day(s) old, ${amount} ` +
    `${(charge.currency ?? '?').toUpperCase()} unrefunded, no dispute filed yet`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function* warnings(key, since, limit = 1000) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': Math.floor(since) };
  for (;;) {
    const page = await get(key, '/radar/early_fraud_warnings', params);
    const data = page?.data ?? [];
    for (const w of data) { yield w; seen += 1; }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
}

/** The warning carries `charge` as an id, or expanded as an object. */
export function chargeId(efw) {
  const ch = efw.charge;
  return ch && typeof ch === 'object' ? ch.id : ch;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = process.argv.includes('--days')
    ? Number(process.argv[process.argv.indexOf('--days') + 1]) : 90;

  const now = Date.now() / 1000;
  const since = now - days * 86400;
  const types = new Map();
  const rows = [];
  let seen = 0;

  for await (const w of warnings(key, since)) {
    seen += 1;
    const t = w.fraud_type ?? 'unknown';
    types.set(t, (types.get(t) ?? 0) + 1);
    const cid = chargeId(w);
    const charge = w.actionable && cid ? await get(key, `/charges/${cid}`) : null;
    const [state, detail] = classify(w, charge, now);
    if (['actionable', 'partial', 'unknown'].includes(state)) {
      rows.push([w.created ?? 0, w, cid, state, detail]);
    }
  }

  rows.sort((a, b) => a[0] - b[0]);
  for (const [, w, cid, state, detail] of rows) {
    console.warn(`${state.padEnd(12)} ${w.id ?? '?'}  charge=${cid}  ` +
                 `${w.fraud_type ?? '?'}  ${detail}`);
    if (state === 'unknown') continue;
    console.warn(`  repair: POST ${API}/refunds -d charge=${cid} -d reason=fraudulent`);
    console.warn('  or Dashboard, the payment, Refund as fraud, which also adds ' +
                 'the card fingerprint and email to your block lists');
  }

  console.log(`${seen} warning(s) read, ${rows.length} actionable and unrefunded`);
  const ranked = [...types.entries()].sort((a, b) => b[1] - a[1]);
  if (ranked.length) {
    console.log('by fraud_type: ' + ranked.map(([k, v]) => `${k}=${v}`).join(', '));
    const [top, count] = ranked[0];
    if (seen && count >= 10 && count / seen > 0.5) {
      console.warn(`${count} of ${seen} warnings are ${top}: that is a campaign, ` +
                   `and a Radar rule will do more than ${count} refunds`);
    }
  }
  console.log('subscribe to radar.early_fraud_warning.created so this sweep is a ' +
              'backstop rather than the only notice you get');
  process.exitCode = rows.length ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning above all the others is the partial refund. It is the one a hurried implementation gets wrong &mdash; a non-zero <code>amount_refunded</code> reads as handled &mdash; and getting it wrong means the report says the account is clean while the disputes it was meant to prevent are already on their way.",
"test_py_file": "test_stripe_efw_actionable.py",
"test_py": '''from stripe_efw_actionable import classify

NOW = 1_700_000_000


def warning(**kw):
    w = {"id": "issfr_1", "actionable": True, "charge": "ch_1",
         "fraud_type": "made_with_stolen_card", "created": NOW - 3 * 86400}
    w.update(kw)
    return w


def charge(**kw):
    c = {"id": "ch_1", "amount": 4500, "currency": "usd", "amount_refunded": 0,
         "refunded": False, "disputed": False}
    c.update(kw)
    return c


def test_an_untouched_actionable_warning_is_flagged_with_its_age():
    state, detail = classify(warning(), charge(), NOW)
    assert state == "actionable"
    assert "3.0 day" in detail


def test_a_partial_refund_does_not_close_the_window():
    # The trap: amount_refunded is non-zero, so a naive check calls this done.
    state, detail = classify(warning(), charge(amount_refunded=500), NOW)
    assert state == "partial"
    assert "still actionable" in detail


def test_a_full_refund_is_the_outcome_this_check_exists_for():
    assert classify(warning(), charge(refunded=True, amount_refunded=4500), NOW)[0] == "refunded"
    # Refunded to the last minor unit without the boolean set is the same thing.
    assert classify(warning(), charge(amount_refunded=4500), NOW)[0] == "refunded"


def test_a_disputed_charge_is_past_the_window_not_pending_in_it():
    state, detail = classify(warning(), charge(disputed=True), NOW)
    assert state == "escalated"
    assert "fee" in detail


def test_the_actionable_flag_and_an_unreadable_charge_are_both_respected():
    assert classify(warning(actionable=False), charge(), NOW)[0] == "not_actionable"
    assert classify(warning(), None, NOW)[0] == "unknown"
''',
"test_js_file": "stripe-efw-actionable.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-efw-actionable.mjs';

const NOW = 1_700_000_000;

const warning = (kw = {}) => ({
  id: 'issfr_1',
  actionable: true,
  charge: 'ch_1',
  fraud_type: 'made_with_stolen_card',
  created: NOW - 3 * 86400,
  ...kw,
});

const charge = (kw = {}) => ({
  id: 'ch_1',
  amount: 4500,
  currency: 'usd',
  amount_refunded: 0,
  refunded: false,
  disputed: false,
  ...kw,
});

test('an untouched actionable warning is flagged with its age', () => {
  const [state, detail] = classify(warning(), charge(), NOW);
  assert.equal(state, 'actionable');
  assert.match(detail, /3\\.0 day/);
});

test('a partial refund does not close the window', () => {
  const [state, detail] = classify(warning(), charge({ amount_refunded: 500 }), NOW);
  assert.equal(state, 'partial');
  assert.match(detail, /still actionable/);
});

test('a full refund is the outcome this check exists for', () => {
  assert.equal(
    classify(warning(), charge({ refunded: true, amount_refunded: 4500 }), NOW)[0],
    'refunded');
  assert.equal(
    classify(warning(), charge({ amount_refunded: 4500 }), NOW)[0], 'refunded');
});

test('a disputed charge is past the window not pending in it', () => {
  const [state, detail] = classify(warning(), charge({ disputed: true }), NOW);
  assert.equal(state, 'escalated');
  assert.match(detail, /fee/);
});

test('the actionable flag and an unreadable charge are both respected', () => {
  assert.equal(classify(warning({ actionable: false }), charge(), NOW)[0],
               'not_actionable');
  assert.equal(classify(warning(), null, NOW)[0], 'unknown');
});
''',
"faq": [
 ("What does actionable mean on an early fraud warning?",
  "It means the warning has not yet received a dispute and the charge has not been fully refunded, so a voluntary refund is still possible. It is not a confidence score about the fraud claim. Once a dispute is filed or the charge is refunded in full, the flag goes false because there is nothing left to do."),
 ("Does refunding an early fraud warning remove it from my dispute rate?",
  "No, and this is worth being clear about. Visa's VAMP ratio counts early fraud warnings alongside disputes, so the warning is counted whether or not you refund. What refunding avoids is the second count: the chargeback that the warning would otherwise become, plus its fee and the goods you would ship in the meantime."),
 ("Is a partial refund enough?",
  "No. The warning stays actionable until the charge is refunded in full, and it can still become a dispute. A refund of shipping, or of the amount after a restocking fee, leaves you with all of the original exposure and a false sense that the item was handled."),
 ("How quickly do warnings turn into disputes?",
  "There is no published guarantee, which is exactly why a nightly sweep is a backstop rather than a process. Subscribe to radar.early_fraud_warning.created and route it somewhere a person looks; the sweep is there to catch what the subscription missed while it was misconfigured."),
 ("Should I refund every actionable warning automatically?",
  "That is a business decision, and it is the reason this script prints the refund instead of issuing it. Automating refunds from a script holding a live key means one bad filter refunds a day of legitimate revenue, irreversibly. Read the fraud_type breakdown first: a cluster is an attack that wants a Radar rule, not a queue of individual refunds."),
],
"related": [
 ("/stripe/dispute-rate-above-threshold/", "Dispute activity is above the 0.75% excessive threshold"),
 ("/stripe/highest-risk-charges-succeeded/", "Highest-risk charges are succeeding instead of being blocked"),
 ("/stripe/radar-reviews-open-stale/", "Radar reviews sit open for days while funds stay at risk"),
],
"citations": [CITE_EFW_OBJ, CITE_PREVENTION, CITE_MEASURING, CITE_KEYS],
},

{
"slug": "no-3ds-on-elevated-risk",
"title": "Elevated-risk card charges are captured with no 3DS",
"description": "Radar scored the payment risky and let it through unauthenticated. With three_d_secure null there is no liability shift, so every fraud dispute is yours.",
"h1": "elevated-risk card charges are captured with no 3DS",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe 3d secure liability shift", "three_d_secure null",
             "radar request 3d secure rule", "stripe elevated risk 3ds",
             "stripe sca liability shift"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Fraud disputes on card-not-present payments are being lost one after another, and each response comes back the same way. Somebody checks whether the liability shift applies and finds that none of the disputed charges went through 3D Secure at all: <code>payment_method_details.card.three_d_secure</code> is <code>null</code> on every one, including the ones Radar had already scored as elevated risk.",
"short_answer": """<p>Page <code>GET /v1/charges?created[gte]=&lt;now-90d&gt;</code> and flag anything where <code>payment_method_details.type</code> is <code>card</code>, <code>status</code> is <code>succeeded</code>, <code>outcome.risk_level</code> is <code>elevated</code> or <code>highest</code>, and <code>payment_method_details.card.three_d_secure</code> is <code>null</code>.</p>
<p>Stripe triggers 3D Secure automatically for regulatory reasons and for issuer soft declines &mdash; not because Radar thought a payment was risky. Without an explicit <em>Request 3D Secure</em> rule, the payments most likely to be disputed are exactly the ones with no authentication behind them, and no liability shift to invoke when the dispute arrives. Report the account-wide 3DS share while you are there: Mastercard's fraud monitoring penalises merchants sitting at or below 10%.</p>""",
"problem": """<p>3D Secure is usually discussed as a conversion cost, and the conclusion people reach is a reasonable-sounding one: do not force it, let Stripe apply it where the regulator requires it, keep the checkout smooth. That is a defensible position for the bulk of traffic and a bad one for the tail, because the tail is where the disputes come from.</p>
<p>What makes the gap invisible is that the two mechanisms look like one. Stripe does trigger 3DS on its own &mdash; for SCA in the regions that mandate it, and when an issuer soft-declines and asks for authentication &mdash; so authenticated payments do appear in the account without anyone configuring anything. It is easy to look at those and conclude the protection is on. It is on for a population defined by regulation and by issuer behaviour, which has no overlap with the population Radar has flagged.</p>
<p>The bill arrives at dispute time. A fraud dispute on an unauthenticated card payment is yours to fight and usually yours to lose. The same dispute on a 3DS-authenticated payment is, for most fraud reason codes, the issuer's problem instead. That difference does not show up until the disputes do, by which point the charges are ninety days old and nothing about them can be changed.</p>""",
"why": """<p><strong>Risk scoring and authentication are separate systems.</strong> Radar produces <code>outcome.risk_level</code>. 3DS is triggered by regulation, by the issuer, or by a rule you wrote. Nothing joins them by default, so a payment can be scored <code>highest</code>, be allowed through, and never be authenticated, all consistently with how both systems are meant to work.</p>
<p><strong>The field is null, not false.</strong> <code>payment_method_details.card.three_d_secure</code> simply is not present when no authentication happened. Code that reads <code>three_d_secure.result</code> without checking the parent gets an exception rather than an answer, and the usual fix is a null guard that swallows the case entirely.</p>
<p><strong>Attempted is not authenticated.</strong> A <code>result</code> of <code>attempt_acknowledged</code> means the flow ran and the issuer did not complete it. It reads as success in a list of charges that have a 3DS object at all, and it is not the same protection as <code>authenticated</code>. Counting anything non-null as covered overstates the share.</p>
<p><strong>A rule that requests 3DS is not the same as one that requires it.</strong> Requesting authentication on a card whose issuer will not perform it produces no authentication and a payment that proceeds anyway. Stripe's own guidance pairs the request rule with a block rule so those cards do not simply fall through, and the pairing is the part that gets skipped.</p>
<p><strong>The share is a monitored number too.</strong> Mastercard's fraud monitoring penalises merchants whose 3DS share sits at or below 10% of Mastercard volume, with a much higher bar in regulated countries. So the coverage figure is not only an internal health metric; it is one somebody else is also computing.</p>""",
"steps": [
 {"h": "Pull ninety days of charges",
  "body": """<p><code>GET /v1/charges?created[gte]=&lt;unix&gt;&amp;limit=100</code>, paginated. Ninety days is long enough to be a rate rather than a week's weather, and short enough that the answer still describes the rules currently in force.</p>"""},
 {"h": "Keep card payments and successful ones only",
  "body": """<p><code>payment_method_details.type == "card"</code>, because wallets and bank debits authenticate differently or not at all and would drag the share around meaninglessly. <code>status == "succeeded"</code>, because a blocked or failed charge cannot be disputed and does not belong in either side of the ratio.</p>"""},
 {"h": "Read the parent before the result",
  "body": """<p>Check that <code>card.three_d_secure</code> exists at all. Null is the finding; it is the literal statement that no authentication took place. Only once it exists is <code>result</code> worth reading.</p>"""},
 {"h": "Cross the null against outcome.risk_level",
  "body": """<p>A normal-risk charge with no 3DS is ordinary. An <code>elevated</code> or <code>highest</code> charge with no 3DS is the finding: Radar identified it, the payment went through unauthenticated, and the liability for a fraud dispute is entirely yours.</p>"""},
 {"h": "Separate authenticated from attempted",
  "body": """<p>Group the charges that do have a 3DS object by <code>result</code>. <code>authenticated</code> is the one that carries the shift. Anything else &mdash; <code>attempt_acknowledged</code>, a processing error &mdash; that was captured on an elevated-risk charge is worth listing separately, because it looks covered and is not.</p>"""},
 {"h": "Report the account-wide share as its own line",
  "body": """<p>Authenticated charges over all card charges. Below 10% is where Mastercard's programme starts taking an interest, which makes it a number to know before somebody else tells you what it is.</p>"""},
],
"verify": """<p>Add the Radar rules, wait for a day of traffic, and re-run. The unprotected count over the last 24 hours should be zero and the share should be climbing.</p>
<pre><code class="language-bash">python3 stripe_3ds_coverage.py --days 1
# 612 card charge(s): 0 elevated-risk unprotected, 3DS share 14.2%</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/charges</code> and nothing else &mdash; a restricted key with read access to Charges is enough. The per-charge classification and the coverage share are two pure functions rather than one, because they answer different questions: one names charges you can still learn from, the other is a rate somebody outside your company is also measuring.",
"py_file": "stripe_3ds_coverage.py",
"py": '''"""Report Stripe card charges captured at elevated risk without 3D Secure.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Charges. The Radar rules that repair this are printed, never applied,
because a rule change reprices every payment on the account and this script holds
a credential to a live one.
"""
import argparse
import collections
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_3ds_coverage")

API = "https://api.stripe.com/v1"

# Radar levels where an unauthenticated capture is a finding rather than normal.
ELEVATED = ("elevated", "highest")

# The only result that carries the liability shift.
AUTHENTICATED = "authenticated"

# Mastercard's fraud monitoring penalises merchants at or below this share.
SHARE_FLOOR = 0.10


def classify(charge):
    """Classify one charge. Pure. Returns (state, detail).

    `unprotected` is the finding: Radar scored the payment elevated or higher,
    it was captured, and no authentication happened, so a fraud dispute on it
    has no liability shift to invoke.
    """
    pmd = charge.get("payment_method_details") or {}
    if pmd.get("type") != "card":
        return ("not_card",
                "%s, which authenticates differently or not at all"
                % (pmd.get("type") or "no payment method details",))
    if charge.get("status") != "succeeded":
        return ("not_settled",
                "status is %r, so it cannot be disputed" % (charge.get("status"),))

    risk = (charge.get("outcome") or {}).get("risk_level")
    tds = (pmd.get("card") or {}).get("three_d_secure")

    if tds is None:
        if risk in ELEVATED:
            return ("unprotected",
                    "risk_level %s captured with three_d_secure null. Radar "
                    "flagged it, nothing authenticated it, and the fraud "
                    "liability is yours." % risk)
        return ("no_3ds",
                "risk_level %s, no authentication. Ordinary, but it counts "
                "against the account 3DS share." % (risk or "unknown",))

    result = tds.get("result")
    if result == AUTHENTICATED:
        return ("protected",
                "authenticated; liability for most fraud disputes sits with the issuer")
    if risk in ELEVATED:
        return ("attempted",
                "three_d_secure.result is %r on a %s risk charge. The flow ran "
                "and the issuer did not complete it, so this looks covered and "
                "is not." % (result, risk))
    return ("attempted",
            "three_d_secure.result is %r, which is not an authentication" % (result,))


def coverage(authenticated, card_charges, floor=SHARE_FLOOR):
    """Account-wide 3DS share. Pure. Returns (state, detail).

    Only `authenticated` counts in the numerator: an acknowledged attempt is
    not an authentication, and counting it overstates the share against the
    number the card networks compute.
    """
    if not card_charges:
        return ("no_volume", "no card charges in the window")
    share = authenticated / card_charges
    if share <= floor:
        return ("low",
                "%.1f%% of card charges authenticated, at or below the %.0f%% "
                "where Mastercard fraud monitoring applies"
                % (share * 100, floor * 100))
    return ("ok", "%.1f%% of card charges authenticated" % (share * 100))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def charges(session, since, limit):
    """Yield charges created since `since`, newest first."""
    seen = 0
    params = {"limit": 100, "created[gte]": int(since)}
    while True:
        page = get(session, "/charges", params)
        data = page.get("data", [])
        for c in data:
            yield c
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


REQUEST_RULE = ("Request 3D Secure if :risk_level: != 'normal' "
                "and :amount_in_usd: > 25")
BLOCK_RULE = ("Block if not :is_3d_secure: and :risk_level: != 'normal' "
              "and not :is_off_session: and :digital_wallet: != 'apple_pay' "
              "and not (:digital_wallet: = 'android_pay' and :has_cryptogram:)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90, help="how far back to read charges")
    ap.add_argument("--max-charges", type=int, default=5000,
                    help="stop paginating after this many charges")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = time.time() - args.days * 86400
    states = collections.Counter()
    card_charges = 0
    authenticated = 0
    findings = []

    for c in charges(s, since, args.max_charges):
        state, detail = classify(c)
        states[state] += 1
        if state == "not_card":
            continue
        if state != "not_settled":
            card_charges += 1
        if state == "protected":
            authenticated += 1
        if state in ("unprotected", "attempted"):
            findings.append((c, state, detail))

    for c, state, detail in findings:
        log.warning("%-12s %s  %s %s  %s", state, c.get("id", "?"),
                    c.get("amount"), (c.get("currency") or "?").upper(), detail)

    share_state, share_detail = coverage(authenticated, card_charges)
    log.info("%d card charge(s): %d unprotected, %d attempted, %d authenticated",
             card_charges, states["unprotected"], states["attempted"], authenticated)
    if share_state == "low":
        log.warning("3DS share: %s", share_detail)
    else:
        log.info("3DS share: %s", share_detail)

    if findings or share_state == "low":
        log.warning("  repair, in Dashboard, Radar, Rules, add both together:")
        log.warning("    %s", REQUEST_RULE)
        log.warning("    %s", BLOCK_RULE)
        log.warning("  the request rule alone lets cards whose issuer will not "
                    "authenticate proceed unauthenticated anyway")
        log.warning("  note that early fraud warnings still arrive on authenticated "
                    "payments and still count toward the Visa VAMP ratio")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-3ds-coverage.mjs",
"js": '''/**
 * Report Stripe card charges captured at elevated risk without 3D Secure.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Charges. The Radar rules that repair this are printed, never
 * applied, because a rule change reprices every payment on the account.
 */
const API = 'https://api.stripe.com/v1';

const ELEVATED = ['elevated', 'highest'];
const AUTHENTICATED = 'authenticated';
export const SHARE_FLOOR = 0.10;

/**
 * Classify one charge. Pure. Returns [state, detail].
 */
export function classify(charge) {
  const pmd = charge.payment_method_details ?? {};
  if (pmd.type !== 'card') {
    return ['not_card',
      `${pmd.type ?? 'no payment method details'}, which authenticates ` +
      'differently or not at all'];
  }
  if (charge.status !== 'succeeded') {
    return ['not_settled',
      `status is ${JSON.stringify(charge.status)}, so it cannot be disputed`];
  }

  const risk = (charge.outcome ?? {}).risk_level;
  const tds = (pmd.card ?? {}).three_d_secure;

  if (tds === null || tds === undefined) {
    if (ELEVATED.includes(risk)) {
      return ['unprotected',
        `risk_level ${risk} captured with three_d_secure null. Radar flagged ` +
        'it, nothing authenticated it, and the fraud liability is yours.'];
    }
    return ['no_3ds',
      `risk_level ${risk ?? 'unknown'}, no authentication. Ordinary, but it ` +
      'counts against the account 3DS share.'];
  }

  const result = tds.result;
  if (result === AUTHENTICATED) {
    return ['protected',
      'authenticated; liability for most fraud disputes sits with the issuer'];
  }
  if (ELEVATED.includes(risk)) {
    return ['attempted',
      `three_d_secure.result is ${JSON.stringify(result)} on a ${risk} risk ` +
      'charge. The flow ran and the issuer did not complete it, so this looks ' +
      'covered and is not.'];
  }
  return ['attempted',
    `three_d_secure.result is ${JSON.stringify(result)}, which is not an authentication`];
}

/**
 * Account-wide 3DS share. Pure. Returns [state, detail]. Only authenticated
 * charges count in the numerator; an acknowledged attempt is not an
 * authentication.
 */
export function coverage(authenticated, cardCharges, floor = SHARE_FLOOR) {
  if (!cardCharges) return ['no_volume', 'no card charges in the window'];
  const share = authenticated / cardCharges;
  if (share <= floor) {
    return ['low',
      `${(share * 100).toFixed(1)}% of card charges authenticated, at or below ` +
      `the ${(floor * 100).toFixed(0)}% where Mastercard fraud monitoring applies`];
  }
  return ['ok', `${(share * 100).toFixed(1)}% of card charges authenticated`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function* charges(key, since, limit = 5000) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': Math.floor(since) };
  for (;;) {
    const page = await get(key, '/charges', params);
    const data = page.data ?? [];
    for (const c of data) { yield c; seen += 1; }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
}

const REQUEST_RULE =
  "Request 3D Secure if :risk_level: != 'normal' and :amount_in_usd: > 25";
const BLOCK_RULE =
  "Block if not :is_3d_secure: and :risk_level: != 'normal' and not " +
  ":is_off_session: and :digital_wallet: != 'apple_pay' and not " +
  "(:digital_wallet: = 'android_pay' and :has_cryptogram:)";

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = process.argv.includes('--days')
    ? Number(process.argv[process.argv.indexOf('--days') + 1]) : 90;
  const since = Date.now() / 1000 - days * 86400;

  const states = new Map();
  let cardCharges = 0;
  let authenticated = 0;
  const findings = [];

  for await (const c of charges(key, since)) {
    const [state, detail] = classify(c);
    states.set(state, (states.get(state) ?? 0) + 1);
    if (state === 'not_card') continue;
    if (state !== 'not_settled') cardCharges += 1;
    if (state === 'protected') authenticated += 1;
    if (state === 'unprotected' || state === 'attempted') {
      findings.push([c, state, detail]);
    }
  }

  for (const [c, state, detail] of findings) {
    console.warn(`${state.padEnd(12)} ${c.id ?? '?'}  ${c.amount} ` +
                 `${(c.currency ?? '?').toUpperCase()}  ${detail}`);
  }

  const [shareState, shareDetail] = coverage(authenticated, cardCharges);
  console.log(`${cardCharges} card charge(s): ${states.get('unprotected') ?? 0} ` +
              `unprotected, ${states.get('attempted') ?? 0} attempted, ` +
              `${authenticated} authenticated`);
  if (shareState === 'low') console.warn(`3DS share: ${shareDetail}`);
  else console.log(`3DS share: ${shareDetail}`);

  if (findings.length || shareState === 'low') {
    console.warn('  repair, in Dashboard, Radar, Rules, add both together:');
    console.warn(`    ${REQUEST_RULE}`);
    console.warn(`    ${BLOCK_RULE}`);
    console.warn('  the request rule alone lets cards whose issuer will not ' +
                 'authenticate proceed unauthenticated anyway');
    console.warn('  note that early fraud warnings still arrive on authenticated ' +
                 'payments and still count toward the Visa VAMP ratio');
    process.exitCode = 1;
  }
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three things are pinned. That a missing <code>three_d_secure</code> is only a finding when Radar had already flagged the charge, so the report does not drown in ordinary traffic. That <code>attempt_acknowledged</code> is not <code>authenticated</code>, which is the distinction that decides who pays for the dispute. And that the coverage floor is inclusive, because 10% exactly is already inside the monitoring band.",
"test_py_file": "test_stripe_3ds_coverage.py",
"test_py": '''from stripe_3ds_coverage import classify, coverage


def card_charge(risk="normal", three_d_secure=None, status="succeeded"):
    card = {"brand": "visa"}
    if three_d_secure is not None:
        card["three_d_secure"] = three_d_secure
    return {
        "id": "ch_1", "status": status, "amount": 9900, "currency": "usd",
        "outcome": {"risk_level": risk},
        "payment_method_details": {"type": "card", "card": card},
    }


def test_elevated_risk_with_no_authentication_is_the_finding():
    state, detail = classify(card_charge(risk="elevated"))
    assert state == "unprotected"
    assert "liability" in detail


def test_normal_risk_with_no_authentication_is_not_a_finding():
    # Ordinary traffic. Flagging it would bury the elevated-risk charges.
    state, detail = classify(card_charge(risk="normal"))
    assert state == "no_3ds"
    assert "share" in detail


def test_an_acknowledged_attempt_is_not_an_authentication():
    state, detail = classify(card_charge(
        risk="highest", three_d_secure={"result": "attempt_acknowledged"}))
    assert state == "attempted"
    assert "not" in detail
    assert classify(card_charge(
        risk="highest", three_d_secure={"result": "authenticated"}))[0] == "protected"


def test_non_card_and_unsettled_charges_are_out_of_scope():
    assert classify({"payment_method_details": {"type": "us_bank_account"}})[0] == "not_card"
    assert classify(card_charge(risk="highest", status="failed"))[0] == "not_settled"


def test_the_ten_percent_coverage_floor_is_inclusive():
    assert coverage(10, 100)[0] == "low"
    assert coverage(11, 100)[0] == "ok"
    assert coverage(0, 0)[0] == "no_volume"
''',
"test_js_file": "stripe-3ds-coverage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, coverage } from './stripe-3ds-coverage.mjs';

function cardCharge(risk = 'normal', threeDSecure = null, status = 'succeeded') {
  const card = { brand: 'visa' };
  if (threeDSecure !== null) card.three_d_secure = threeDSecure;
  return {
    id: 'ch_1',
    status,
    amount: 9900,
    currency: 'usd',
    outcome: { risk_level: risk },
    payment_method_details: { type: 'card', card },
  };
}

test('elevated risk with no authentication is the finding', () => {
  const [state, detail] = classify(cardCharge('elevated'));
  assert.equal(state, 'unprotected');
  assert.match(detail, /liability/);
});

test('normal risk with no authentication is not a finding', () => {
  const [state, detail] = classify(cardCharge('normal'));
  assert.equal(state, 'no_3ds');
  assert.match(detail, /share/);
});

test('an acknowledged attempt is not an authentication', () => {
  const [state, detail] = classify(
    cardCharge('highest', { result: 'attempt_acknowledged' }));
  assert.equal(state, 'attempted');
  assert.match(detail, /not/);
  assert.equal(
    classify(cardCharge('highest', { result: 'authenticated' }))[0], 'protected');
});

test('non card and unsettled charges are out of scope', () => {
  assert.equal(
    classify({ payment_method_details: { type: 'us_bank_account' } })[0], 'not_card');
  assert.equal(classify(cardCharge('highest', null, 'failed'))[0], 'not_settled');
});

test('the ten percent coverage floor is inclusive', () => {
  assert.equal(coverage(10, 100)[0], 'low');
  assert.equal(coverage(11, 100)[0], 'ok');
  assert.equal(coverage(0, 0)[0], 'no_volume');
});
''',
"faq": [
 ("Does Stripe apply 3D Secure automatically?",
  "Only for regulatory reasons, such as Strong Customer Authentication in the regions that mandate it, and when an issuer soft-declines and asks for authentication. Radar's risk score does not trigger it. So an account can have plenty of authenticated payments and still have none on the charges Radar flagged."),
 ("What does three_d_secure being null actually mean?",
  "That no authentication took place on that payment. The object is absent rather than present-and-false, which is why code reading three_d_secure.result directly throws instead of reporting, and why the null case tends to be swallowed by whatever guard was added to stop the exception."),
 ("Is attempt_acknowledged good enough for the liability shift?",
  "No. It records that the authentication flow ran and the issuer did not complete it. Treating any non-null three_d_secure object as covered inflates your protection figure and your reported 3DS share, and neither the card networks nor a dispute response will agree with the number."),
 ("Why pair the request rule with a block rule?",
  "Because requesting authentication does not guarantee getting it. If the issuer will not authenticate, the payment proceeds unauthenticated and you are back where you started. Stripe's recommended companion block rule stops those, with carve-outs for wallets that already carry their own cryptogram."),
 ("Will 3D Secure stop early fraud warnings?",
  "No. Early fraud warnings still arrive on authenticated payments and still count toward Visa's VAMP ratio. What authentication changes is who carries the loss when a fraud dispute is filed, which is a different problem from how many fraud signals your traffic generates."),
],
"related": [
 ("/stripe/highest-risk-charges-succeeded/", "Highest-risk charges are succeeding instead of being blocked"),
 ("/stripe/avs-cvc-fail-captured/", "Charges captured after AVS and CVC verification failed"),
 ("/stripe/dispute-rate-above-threshold/", "Dispute activity is above the 0.75% excessive threshold"),
],
"citations": [CITE_RADAR_RULES, CITE_CHARGE_OBJ, CITE_PREVENTION, CITE_KEYS],
},

]
