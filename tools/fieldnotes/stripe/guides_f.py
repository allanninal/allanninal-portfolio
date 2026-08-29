#!/usr/bin/env python3
"""/stripe/ field notes, batch F — the writing.

Same constraint as every other batch in this section: each note is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

Disputes and customer identity, which is where the read-only rule earns most of
its keep: the repair for a dispute is irreversible and submits exactly once, and
the repair for a duplicate customer deletes a record that a subscription may be
pointing at.
"""

CITE_DISPUTE_OBJ = ("The dispute object — Stripe API reference",
                    "https://docs.stripe.com/api/disputes/object")
CITE_DISPUTE_LIST = ("List all disputes — Stripe API reference",
                     "https://docs.stripe.com/api/disputes/list")
CITE_RESPONDING = ("Respond to disputes — Stripe Docs",
                   "https://docs.stripe.com/disputes/responding")
CITE_DISPUTES = ("Disputes and fraud — Stripe Docs",
                 "https://docs.stripe.com/disputes")
CITE_MEASURING = ("Measuring disputes — Stripe Docs",
                  "https://docs.stripe.com/disputes/measuring")
CITE_SESSION_OBJ = ("The Checkout Session object — Stripe API reference",
                    "https://docs.stripe.com/api/checkout/sessions/object")
CITE_SESSION_LIST = ("List all Checkout Sessions — Stripe API reference",
                     "https://docs.stripe.com/api/checkout/sessions/list")
CITE_METADATA = ("Metadata — Stripe API reference",
                 "https://docs.stripe.com/api/metadata")
CITE_PAYMENT_LINKS = ("Payment Links — Stripe Docs",
                      "https://docs.stripe.com/payment-links")
CITE_CUSTOMER_OBJ = ("The customer object — Stripe API reference",
                     "https://docs.stripe.com/api/customers/object")
CITE_CUSTOMER_LIST = ("List all customers — Stripe API reference",
                      "https://docs.stripe.com/api/customers/list")
CITE_CUSTOMER_SEARCH = ("Search customers — Stripe API reference",
                        "https://docs.stripe.com/api/customers/search")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

GUIDES = [

{
"slug": "dispute-deadline-72h-no-evidence",
"title": "Disputes are hours from due_by with no evidence attached",
"description": "Nothing chases a dispute deadline. Read evidence_details.due_by against now and find the ones about to be lost by default rather than on merit.",
"h1": "disputes are hours from due_by with no evidence attached",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe dispute deadline", "evidence_details due_by",
             "stripe dispute needs_response", "stripe chargeback deadline",
             "stripe dispute past_due"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A customer disputed a charge three weeks ago. The notification went to the shared billing inbox, where it sat under invoices. The dispute closed yesterday as lost, the funds went back, the dispute fee did not come back, and the delivery confirmation that would have answered it was in a support ticket the whole time.",
"short_answer": """<p>Page <code>GET /v1/disputes</code> and read <code>evidence_details</code> on everything whose <code>status</code> is <code>needs_response</code>. Three fields decide the outcome: <code>due_by</code> is the deadline, <code>has_evidence</code> says whether anything has been staged, and <code>submission_count</code> says whether it was ever actually sent.</p>
<p>Alert when <code>due_by - now</code> is under 72 hours and <code>submission_count</code> is still <code>0</code>. If <code>past_due</code> is already <code>true</code> while the status is <code>needs_response</code>, that dispute is over: miss the deadline and you lose automatically, and the disputed funds cannot be retrieved.</p>""",
"problem": """<p>The dispute itself is not the failure. Disputes are a cost of taking cards, and a fair number of them are genuinely indefensible. The failure is the ones you would have won, closed without anyone opening them, because the deadline arrived before the notification was read.</p>
<p>What makes it hard to see is that the outcome looks identical either way. A dispute lost on the evidence and a dispute lost because nobody replied both appear in the Dashboard as <code>lost</code>, both take the funds back, and both keep the fee. There is no line item anywhere that says "this one was forfeited", so the first honest measurement of the problem is usually a script, and the first symptom is a chargeback rate creeping toward the threshold where the card networks start taking an interest.</p>""",
"why": """<p><strong>The clock is short and it is not yours.</strong> The response window is roughly 7 to 21 days depending on the card network, and it starts when the network files the dispute rather than when you read about it. A week of that can be gone before the email is opened, and none of it is negotiable afterwards.</p>
<p><strong>Nothing pushes a reminder as it approaches.</strong> <code>due_by</code> is right there on the object, but Stripe does not escalate as it nears. The notification arrives once, at the start, usually to whatever address the account was created with. If that is a shared inbox that four people half-watch, the dispute is now everyone's job and therefore nobody's.</p>
<p><strong>Evidence submits exactly once.</strong> You cannot send a partial response now and add the tracking number tomorrow. That makes the correct behaviour "assemble everything, then submit", which is also the behaviour most likely to stall for a week waiting on a colleague, so a dispute can sit at <code>has_evidence: true</code> and <code>submission_count: 0</code> right through its deadline. Staged is not submitted, and only <code>submission_count</code> can tell you which one you are looking at.</p>
<p><strong>The window is measured in hours near the end, not days.</strong> A weekly check on a 10-day deadline can hand you a dispute with four hours left, on a Saturday. This is a daily check or it is decoration.</p>""",
"steps": [
 {"h": "List disputes and keep only the ones still open",
  "body": """<p><code>GET /v1/disputes?limit=100</code>, paginated. The statuses that still need something from you are <code>needs_response</code> and <code>warning_needs_response</code>; <code>under_review</code> means the evidence is already in, and <code>won</code>, <code>lost</code> and <code>warning_closed</code> are finished.</p>"""},
 {"h": "Turn due_by into hours, not days",
  "body": """<p><code>due_by</code> is a unix timestamp. Subtract now and divide by 3600. Days are the wrong unit at the end of the window: "2 days left" and "38 hours left, and one of them is a weekend" are the same number and very different tickets.</p>"""},
 {"h": "Separate staged evidence from submitted evidence",
  "body": """<p><code>has_evidence</code> goes <code>true</code> as soon as a single field is saved, which is why it reads as reassuring and is not. <code>submission_count</code> is the field that says the response actually went to the network. A dispute with evidence staged and a submission count of zero is the most expensive state on this list, because somebody already did the work.</p>"""},
 {"h": "Check enhanced eligibility before assembling anything",
  "body": """<p><code>enhanced_eligibility_types</code> containing <code>visa_compelling_evidence_3</code> means Stripe can pre-populate most of the response from prior transactions with the same customer. That turns a two-hour evidence hunt into a review, so it is worth reading before anyone starts collecting screenshots.</p>"""},
 {"h": "Decide deliberately, including the decision not to fight",
  "body": """<p>Some disputes are not worth answering, and accepting one with <code>POST /v1/disputes/{id}/close</code> is a legitimate outcome. What this check is for is making that a decision somebody took rather than a deadline that passed.</p>"""},
 {"h": "Run it daily and route it to a person",
  "body": """<p>One paginated GET. Anything that fires into a channel a human reads every morning converts a class of losses that are invisible in the numbers into a queue with a length.</p>"""},
],
"verify": """<p>Re-run the script after the responses go in. Everything answered moves to <code>under_review</code>, and nothing should be inside the 72-hour window unanswered.</p>
<pre><code class="language-bash">python3 stripe_dispute_deadlines.py
# 14 dispute(s) read, 0 needing a response now</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/disputes</code> and nothing else &mdash; a restricted key with read access to Disputes is enough, and is what you should give it. The classification is a pure function because the whole check is deadline arithmetic, and an off-by-one on the boundary is a check that tells you about a dispute after it closed.",
"py_file": "stripe_dispute_deadlines.py",
"py": '''"""Report Stripe disputes whose response deadline is about to pass.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Disputes. The response is printed, never submitted, because this script
holds a credential to a live payments account and dispute evidence can be sent
exactly once.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_dispute_deadlines")

API = "https://api.stripe.com/v1"

CRITICAL_HOURS = 72.0

# Still waiting on you.
OPEN = ("needs_response", "warning_needs_response")
# Answered; the network has it.
IN_REVIEW = ("under_review", "warning_under_review")
# Finished either way.
SETTLED = ("won", "lost", "warning_closed")


def verdict(dispute, now, critical_hours=CRITICAL_HOURS):
    """Classify one dispute. Pure, so the deadline arithmetic can be tested.

    `now` is a unix timestamp. Returns (state, detail).

    The states that matter are `critical` (deadline close, nothing sent) and
    `staged` (deadline close, evidence written but submission_count still 0),
    which is the same loss with the work already paid for.
    """
    status = dispute.get("status")
    ed = dispute.get("evidence_details") or {}

    if status in IN_REVIEW:
        return ("submitted", "evidence is in and the network is reviewing it")
    if status in SETTLED:
        return ("closed", "closed as %s; there is nothing left to send" % status)
    if status not in OPEN:
        return ("unknown", "unrecognised status %r" % (status,))

    due_by = ed.get("due_by")
    staged = bool(ed.get("has_evidence"))
    sent = ed.get("submission_count") or 0

    if ed.get("past_due") or (due_by is not None and due_by <= now):
        return ("forfeited",
                "past due_by while still needing a response. The funds and the "
                "dispute fee are gone, and no evidence will be accepted now.")
    if due_by is None:
        return ("unknown", "open, but with no due_by to measure against")

    hours = (due_by - now) / 3600.0
    if hours <= critical_hours:
        if staged and not sent:
            return ("staged",
                    "%.1f hour(s) left. Evidence is staged but submission_count "
                    "is 0, so none of it has reached the network." % hours)
        return ("critical", "%.1f hour(s) left and nothing attached." % hours)
    if staged and not sent:
        return ("open",
                "%.1f day(s) left; evidence staged, not submitted" % (hours / 24.0))
    return ("open", "%.1f day(s) left to assemble evidence" % (hours / 24.0))


def money(dispute):
    """Amount at risk, in minor units.

    Deliberately not divided by 100: that is wrong for zero-decimal currencies
    like JPY, and a report that quietly reads 100x low on one currency is worse
    than one that makes you read the currency code.
    """
    return "%s %s" % (dispute.get("amount"), (dispute.get("currency") or "?").upper())


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def disputes(session, limit):
    """Yield disputes, newest first, up to `limit`."""
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
    seen = urgent = 0
    for d in disputes(s, args.max_disputes):
        seen += 1
        state, detail = verdict(d, now, args.hours)
        if state in ("submitted", "closed", "open"):
            log.info("%-10s %s  %s", state, d.get("id", "?"), detail)
            continue

        urgent += 1
        log.warning("%-10s %s  %s  %s", state, d.get("id", "?"), money(d), detail)
        if state == "unknown":
            continue
        if state == "forfeited":
            log.warning("  nothing to run: the window is closed. Count it with the "
                        "other forfeits and fix the sweep, not this dispute.")
            continue
        log.warning("  repair: POST %s/disputes/%s "
                    "-d 'evidence[product_description]=...' "
                    "-d 'evidence[shipping_tracking_number]=...' "
                    "-d 'evidence[customer_communication]=<file_id>'",
                    API, d["id"])
        log.warning("  evidence submits once, so assemble it all first. "
                    "To concede on purpose: POST %s/disputes/%s/close", API, d["id"])
        if "visa_compelling_evidence_3" in (d.get("enhanced_eligibility_types") or []):
            log.warning("  eligible for Visa Compelling Evidence 3.0: Stripe "
                        "pre-populates most of this from prior transactions")

    log.info("%d dispute(s) read, %d needing a response now", seen, urgent)
    return 1 if urgent else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-dispute-deadlines.mjs",
"js": '''/**
 * Report Stripe disputes whose response deadline is about to pass.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Disputes. The response is printed, never submitted, because
 * dispute evidence can be sent exactly once.
 */
const API = 'https://api.stripe.com/v1';

export const CRITICAL_HOURS = 72;

const OPEN = ['needs_response', 'warning_needs_response'];
const IN_REVIEW = ['under_review', 'warning_under_review'];
const SETTLED = ['won', 'lost', 'warning_closed'];

/**
 * Classify one dispute. Pure, so the deadline arithmetic can be tested.
 * `now` is a unix timestamp in seconds.
 */
export function verdict(dispute, now, criticalHours = CRITICAL_HOURS) {
  const status = dispute.status;
  const ed = dispute.evidence_details ?? {};

  if (IN_REVIEW.includes(status)) {
    return ['submitted', 'evidence is in and the network is reviewing it'];
  }
  if (SETTLED.includes(status)) {
    return ['closed', `closed as ${status}; there is nothing left to send`];
  }
  if (!OPEN.includes(status)) {
    return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
  }

  const dueBy = ed.due_by;
  const staged = Boolean(ed.has_evidence);
  const sent = ed.submission_count ?? 0;

  if (ed.past_due || (dueBy !== undefined && dueBy !== null && dueBy <= now)) {
    return ['forfeited',
      'past due_by while still needing a response. The funds and the dispute ' +
      'fee are gone, and no evidence will be accepted now.'];
  }
  if (dueBy === undefined || dueBy === null) {
    return ['unknown', 'open, but with no due_by to measure against'];
  }

  const hours = (dueBy - now) / 3600;
  if (hours <= criticalHours) {
    if (staged && !sent) {
      return ['staged',
        `${hours.toFixed(1)} hour(s) left. Evidence is staged but ` +
        'submission_count is 0, so none of it has reached the network.'];
    }
    return ['critical', `${hours.toFixed(1)} hour(s) left and nothing attached.`];
  }
  if (staged && !sent) {
    return ['open', `${(hours / 24).toFixed(1)} day(s) left; evidence staged, not submitted`];
  }
  return ['open', `${(hours / 24).toFixed(1)} day(s) left to assemble evidence`];
}

/**
 * Amount at risk, in minor units. Not divided by 100, which is wrong for
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
  let seen = 0;
  let urgent = 0;

  for await (const d of disputes(key)) {
    seen += 1;
    const [state, detail] = verdict(d, now);
    if (state === 'submitted' || state === 'closed' || state === 'open') {
      console.log(`${state.padEnd(10)} ${d.id ?? '?'}  ${detail}`);
      continue;
    }

    urgent += 1;
    console.warn(`${state.padEnd(10)} ${d.id ?? '?'}  ${money(d)}  ${detail}`);
    if (state === 'unknown') continue;
    if (state === 'forfeited') {
      console.warn('  nothing to run: the window is closed. Count it with the ' +
                   'other forfeits and fix the sweep, not this dispute.');
      continue;
    }
    console.warn(`  repair: POST ${API}/disputes/${d.id} ` +
                 `-d 'evidence[product_description]=...' ` +
                 `-d 'evidence[shipping_tracking_number]=...' ` +
                 `-d 'evidence[customer_communication]=<file_id>'`);
    console.warn('  evidence submits once, so assemble it all first. ' +
                 `To concede on purpose: POST ${API}/disputes/${d.id}/close`);
    if ((d.enhanced_eligibility_types ?? []).includes('visa_compelling_evidence_3')) {
      console.warn('  eligible for Visa Compelling Evidence 3.0: Stripe ' +
                   'pre-populates most of this from prior transactions');
    }
  }

  console.log(`${seen} dispute(s) read, ${urgent} needing a response now`);
  process.exitCode = urgent ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. The first is the exact boundary, because a check that flips at 71 hours instead of 72 loses a day of the three you have left. The second is a dispute with evidence staged and <code>submission_count</code> still zero: it looks answered on every field except the one that counts, and treating it as answered is how the work gets done and thrown away.",
"test_py_file": "test_stripe_dispute_deadlines.py",
"test_py": '''from stripe_dispute_deadlines import verdict

NOW = 1_700_000_000


def open_dispute(hours_left, **evidence):
    ev = {"due_by": NOW + int(hours_left * 3600)}
    ev.update(evidence)
    return {"id": "du_1", "status": "needs_response", "evidence_details": ev}


def test_deadline_inside_the_window_with_nothing_attached_is_critical():
    state, detail = verdict(open_dispute(6), NOW)
    assert state == "critical"
    assert "6.0" in detail


def test_seventy_two_hours_is_the_boundary_and_it_is_inclusive():
    # 72 must already fire. Waiting for 71 spends a third of what is left.
    assert verdict(open_dispute(72), NOW)[0] == "critical"
    assert verdict(open_dispute(72.1), NOW)[0] == "open"


def test_staged_evidence_that_was_never_submitted_is_its_own_state():
    state, detail = verdict(
        open_dispute(10, has_evidence=True, submission_count=0), NOW)
    assert state == "staged"
    assert "submission_count" in detail


def test_past_due_while_still_needing_a_response_is_forfeited():
    d = open_dispute(-1, past_due=True)
    state, detail = verdict(d, NOW)
    assert state == "forfeited"
    assert "fee" in detail


def test_under_review_is_answered_and_a_missing_due_by_is_not_silently_open():
    assert verdict({"status": "under_review"}, NOW)[0] == "submitted"
    assert verdict({"status": "needs_response", "evidence_details": {}}, NOW)[0] == "unknown"
    assert verdict({"status": "sleeping"}, NOW)[0] == "unknown"
''',
"test_js_file": "stripe-dispute-deadlines.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-dispute-deadlines.mjs';

const NOW = 1_700_000_000;

function openDispute(hoursLeft, evidence = {}) {
  return {
    id: 'du_1',
    status: 'needs_response',
    evidence_details: { due_by: NOW + Math.round(hoursLeft * 3600), ...evidence },
  };
}

test('deadline inside the window with nothing attached is critical', () => {
  const [state, detail] = verdict(openDispute(6), NOW);
  assert.equal(state, 'critical');
  assert.match(detail, /6\\.0 hour/);
});

test('seventy two hours is the boundary and it is inclusive', () => {
  assert.equal(verdict(openDispute(72), NOW)[0], 'critical');
  assert.equal(verdict(openDispute(72.1), NOW)[0], 'open');
});

test('staged evidence that was never submitted is its own state', () => {
  const [state, detail] = verdict(
    openDispute(10, { has_evidence: true, submission_count: 0 }), NOW);
  assert.equal(state, 'staged');
  assert.match(detail, /submission_count/);
});

test('past due while still needing a response is forfeited', () => {
  const [state, detail] = verdict(openDispute(-1, { past_due: true }), NOW);
  assert.equal(state, 'forfeited');
  assert.match(detail, /fee/);
});

test('answered and unreadable disputes are not treated as open', () => {
  assert.equal(verdict({ status: 'under_review' }, NOW)[0], 'submitted');
  assert.equal(
    verdict({ status: 'needs_response', evidence_details: {} }, NOW)[0], 'unknown');
  assert.equal(verdict({ status: 'sleeping' }, NOW)[0], 'unknown');
});
''',
"faq": [
 ("How long do I actually have to respond to a Stripe dispute?",
  "Roughly 7 to 21 days, set by the card network rather than by Stripe, which is why the only trustworthy number is evidence_details.due_by on the dispute itself. The clock starts when the network files the dispute, not when the notification reaches you, so some of the window is usually gone before anyone reads about it."),
 ("What happens if the deadline passes with no response?",
  "You lose automatically. The disputed funds are not retrievable and the dispute fee is not returned. The outcome is recorded as lost, indistinguishable in the Dashboard from a dispute you fought and lost on the evidence."),
 ("Does has_evidence being true mean the response was sent?",
  "No, and this is the trap the script exists for. has_evidence goes true as soon as any evidence field is saved. submission_count is the field that says the response reached the network. Staged evidence with a submission count of zero still forfeits at the deadline."),
 ("Can I submit evidence twice to add something I forgot?",
  "No. Evidence submits once per dispute, which is why the correct workflow is to assemble everything before sending. It is also why this script prints the submission instead of performing it: an automated partial submission would spend your only attempt."),
 ("What is enhanced_eligibility_types for?",
  "It tells you when a dispute qualifies for a network programme such as Visa Compelling Evidence 3.0, where Stripe can pre-populate the response from prior transactions with the same customer. Reading it first tells you whether you are assembling evidence or reviewing evidence Stripe already has."),
],
"related": [
 ("/stripe/disputes-lost-without-response/", "Disputes closed as lost were never actually contested"),
 ("/stripe/radar-blocked-payments-ignored/", "Radar blocks payments and nobody reads the block reasons"),
 ("/stripe/refunds-failed-or-stuck/", "Refunds sit failed or requires_action and nobody notices"),
],
"citations": [CITE_DISPUTE_OBJ, CITE_RESPONDING, CITE_DISPUTE_LIST, CITE_KEYS],
},

{
"slug": "disputes-lost-without-response",
"title": "Disputes closed as lost were never actually contested",
"description": "A wall of lost disputes hides two different failures. A lost dispute with submission_count 0 was forfeited by the deadline, not decided against you.",
"h1": "disputes closed as lost were never actually contested",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe disputes lost", "evidence_details submission_count",
             "stripe dispute win rate", "stripe chargeback loss rate",
             "stripe disputes not contested"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody finally asks what the dispute win rate is. The Dashboard says most of them are lost, and the conclusion in the room is that disputes are unwinnable and not worth the effort. Nobody in the room can say how many of those losses were ever answered, and until someone can, that conclusion is unsupported.",
"short_answer": """<p>Page <code>GET /v1/disputes?created[gte]=&lt;now-365d&gt;</code> and split the losses in two. A dispute with <code>status</code> of <code>lost</code> and <code>evidence_details.submission_count</code> of <code>0</code> was never contested; it was forfeited when the deadline passed. Anything above zero was actually judged.</p>
<p>Report two numbers, not one: the share of losses that were forfeits, and the loss rate over contested disputes only. The first is recoverable process loss, the second is your real win rate. A forfeit share above roughly <strong>30%</strong> means there is no dispute workflow, only a dispute list.</p>""",
"problem": """<p>The Dashboard shows outcomes. It does not show effort, so a dispute lost after a careful evidence package and a dispute lost because nobody opened the email look exactly alike in the headline number. That single number then gets used to make a decision &mdash; usually "disputes are not worth fighting" &mdash; which quietly guarantees the number stays where it is.</p>
<p>The cost compounds in a second place. Chargeback rate is measured by the networks, and sustained high rates put an account into a monitoring programme with fees and remediation plans attached. Forfeited disputes count toward that just as decided ones do, so a process gap becomes an account-standing problem without ever appearing as one.</p>""",
"why": """<p><strong>Forfeits and defeats are the same status.</strong> <code>lost</code> is <code>lost</code>. Nothing in the object separates the two except <code>submission_count</code>, and nothing in the interface puts that field next to the outcome, so the distinction only exists if somebody goes looking for it.</p>
<p><strong>The denominator is wrong in the obvious calculation.</strong> Dividing losses by all disputes mixes the ones you fought with the ones you skipped, and produces a win rate that is not a measure of anything you do. The number that answers "is fighting worth it" is losses over contested disputes only, and it is frequently far better than the headline suggests.</p>
<p><strong>The mechanism is invisible in aggregate but obvious per dispute.</strong> Each individual forfeit has a story &mdash; the person who handled disputes left, the deadline landed over a holiday, the notification went to an inbox nobody owns &mdash; and each one sounds like a one-off. Counted together over a year they form a rate, and rates get fixed where anecdotes do not.</p>
<p><strong>Nobody measures what they believe is unwinnable.</strong> The belief and the absence of measurement hold each other up. Breaking that loop needs exactly one number that anybody can reproduce, which is what this script prints.</p>""",
"steps": [
 {"h": "Pull a year of disputes, not a month",
  "body": """<p><code>GET /v1/disputes?created[gte]=&lt;unix&gt;&amp;limit=100</code>, paginated. Disputes are low-volume for most accounts, so a short window gives you a ratio built on four data points. A year is usually enough to be worth arguing about.</p>"""},
 {"h": "Count three things and only three",
  "body": """<p>Disputes closed as <code>won</code>, disputes closed as <code>lost</code>, and the subset of the lost ones with <code>submission_count</code> of zero. Anything still open belongs to the deadline sweep, not to this measurement, and including it drags the ratio around for no reason.</p>"""},
 {"h": "Report the forfeit share",
  "body": """<p>Forfeits divided by losses. This is the number that is recoverable by process alone, with no change to the evidence you collect or the products you sell. Zero is achievable; most first measurements are not close to it.</p>"""},
 {"h": "Report the contested loss rate separately",
  "body": """<p>Contested losses over contested losses plus wins. This is what your evidence is actually worth. If it is good, the forfeit share is money left on the table. If it is poor as well, the fix is in what you collect at payment time rather than in who reads the inbox.</p>"""},
 {"h": "Close the loop with a daily deadline sweep",
  "body": """<p>This note measures the damage; it does not stop it. The sweep on <code>evidence_details.due_by</code> is what changes the number, and re-running this check a quarter later is what proves it did.</p>"""},
 {"h": "Pre-populate the evidence at payment time",
  "body": """<p>Customer IP, email, shipping address and product description passed on every payment make a response something you assemble in minutes rather than a research project, and they are what network programmes such as Visa Compelling Evidence 3.0 are assessed against.</p>"""},
],
"verify": """<p>Re-run the check a quarter after the deadline sweep is in place. The forfeit share should be falling toward zero, and the contested loss rate should barely move, because it was always measuring something else.</p>
<pre><code class="language-bash">python3 stripe_dispute_forfeits.py --days 90
# contested   6 loss(es), all of them answered; the 11 contested dispute(s) lost 55% of the time</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/disputes</code> with a <code>created[gte]</code> filter, and no writes at all. The arithmetic is a pure function taking three integers, which keeps the two ratios &mdash; the forfeit share and the contested loss rate &mdash; visible and testable instead of buried in a counting loop where a wrong denominator would never be noticed.",
"py_file": "stripe_dispute_forfeits.py",
"py": '''"""Measure how many lost Stripe disputes were forfeited rather than decided.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Disputes. The repair is a process change, printed for a human, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_dispute_forfeits")

API = "https://api.stripe.com/v1"

# Above this share of losses, the dispute process is not merely leaky.
FORFEIT_ALARM = 0.30


def verdict(lost, forfeited, won):
    """Classify a window of closed disputes. Pure, so both ratios can be tested.

    `forfeited` is the subset of `lost` that closed with submission_count 0,
    meaning the deadline passed rather than the evidence failing.
    Returns (state, detail).
    """
    if lost + won == 0:
        return ("no_disputes", "no dispute closed as won or lost in this window")
    if forfeited > lost:
        return ("unknown",
                "%d forfeit(s) against %d loss(es); the counts disagree"
                % (forfeited, lost))
    if lost == 0:
        return ("clean", "%d dispute(s) closed, none lost" % won)

    contested_lost = lost - forfeited
    denom = contested_lost + won
    if denom:
        rate = ("the %d contested dispute(s) lost %.0f%% of the time"
                % (denom, 100.0 * contested_lost / denom))
    else:
        rate = "nothing was contested, so there is no real loss rate to quote"

    if forfeited == 0:
        return ("contested", "%d loss(es), every one answered; %s" % (lost, rate))

    share = 100.0 * forfeited / lost
    body = ("%d of %d loss(es) (%.0f%%) closed with submission_count 0; %s"
            % (forfeited, lost, share, rate))
    if forfeited / float(lost) >= FORFEIT_ALARM:
        return ("absent", body + ". At this share there is no dispute workflow, "
                                 "only a dispute list.")
    return ("leaking", body + ". Each of those was recoverable process loss.")


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def tally(session, since, limit):
    """Count won, lost and forfeited disputes created since `since`.

    Open disputes are ignored on purpose: they belong to the deadline sweep, and
    counting them here moves the ratio for reasons that have nothing to do with
    how the closed ones went.
    """
    lost = forfeited = won = seen = 0
    params = {"limit": 100, "created[gte]": int(since)}
    while True:
        page = get(session, "/disputes", params)
        data = page.get("data", [])
        for d in data:
            seen += 1
            status = d.get("status")
            if status == "won":
                won += 1
            elif status == "lost":
                lost += 1
                ed = d.get("evidence_details") or {}
                if not (ed.get("submission_count") or 0):
                    forfeited += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return lost, forfeited, won


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=365,
                    help="how far back to count closed disputes")
    ap.add_argument("--max-disputes", type=int, default=5000,
                    help="stop paginating after this many disputes")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = time.time() - args.days * 86400
    lost, forfeited, won = tally(s, since, args.max_disputes)
    state, detail = verdict(lost, forfeited, won)

    line = "%-12s %s" % (state, detail)
    if state in ("no_disputes", "clean", "contested"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  repair: sweep evidence_details.due_by daily and route each "
                "dispute to a named human before it is 72 hours out")
    log.warning("  and pass customer IP, email, shipping address and product "
                "description on every payment, so a response is a review "
                "rather than a research project")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-dispute-forfeits.mjs",
"js": '''/**
 * Measure how many lost Stripe disputes were forfeited rather than decided.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Disputes. The repair is a process change, printed for a human.
 */
const API = 'https://api.stripe.com/v1';

// Above this share of losses, the dispute process is not merely leaky.
export const FORFEIT_ALARM = 0.30;

/**
 * Classify a window of closed disputes. Pure, so both ratios can be tested.
 * `forfeited` is the subset of `lost` that closed with submission_count 0.
 */
export function verdict(lost, forfeited, won) {
  if (lost + won === 0) {
    return ['no_disputes', 'no dispute closed as won or lost in this window'];
  }
  if (forfeited > lost) {
    return ['unknown',
      `${forfeited} forfeit(s) against ${lost} loss(es); the counts disagree`];
  }
  if (lost === 0) return ['clean', `${won} dispute(s) closed, none lost`];

  const contestedLost = lost - forfeited;
  const denom = contestedLost + won;
  const rate = denom
    ? `the ${denom} contested dispute(s) lost ` +
      `${(100 * contestedLost / denom).toFixed(0)}% of the time`
    : 'nothing was contested, so there is no real loss rate to quote';

  if (forfeited === 0) {
    return ['contested', `${lost} loss(es), every one answered; ${rate}`];
  }

  const share = (100 * forfeited / lost).toFixed(0);
  const body = `${forfeited} of ${lost} loss(es) (${share}%) closed with ` +
               `submission_count 0; ${rate}`;
  if (forfeited / lost >= FORFEIT_ALARM) {
    return ['absent', body +
      '. At this share there is no dispute workflow, only a dispute list.'];
  }
  return ['leaking', body + '. Each of those was recoverable process loss.'];
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

export async function tally(key, since, limit = 5000) {
  let lost = 0, forfeited = 0, won = 0, seen = 0;
  const params = { limit: 100, 'created[gte]': Math.floor(since) };
  for (;;) {
    const page = await get(key, '/disputes', params);
    const data = page.data ?? [];
    for (const d of data) {
      seen += 1;
      if (d.status === 'won') won += 1;
      else if (d.status === 'lost') {
        lost += 1;
        if (!((d.evidence_details ?? {}).submission_count ?? 0)) forfeited += 1;
      }
    }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { lost, forfeited, won };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.argv[2] ?? 365);
  const since = Date.now() / 1000 - days * 86400;
  const { lost, forfeited, won } = await tally(key, since);
  const [state, detail] = verdict(lost, forfeited, won);

  const line = `${state.padEnd(12)} ${detail}`;
  if (state === 'no_disputes' || state === 'clean' || state === 'contested') {
    console.log(line);
    return;
  }

  console.warn(line);
  console.warn('  repair: sweep evidence_details.due_by daily and route each ' +
               'dispute to a named human before it is 72 hours out');
  console.warn('  and pass customer IP, email, shipping address and product ' +
               'description on every payment, so a response is a review ' +
               'rather than a research project');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are about denominators. A forfeit counted into the contested loss rate makes the evidence look worse than it is, an account with no disputes at all must not report a division by zero as a perfect record, and 30% has to fire at exactly 30% rather than just above it.",
"test_py_file": "test_stripe_dispute_forfeits.py",
"test_py": '''from stripe_dispute_forfeits import verdict


def test_no_closed_disputes_is_not_a_perfect_record():
    state, _ = verdict(0, 0, 0)
    assert state == "no_disputes"


def test_losses_that_were_all_answered_report_the_real_loss_rate():
    # 4 losses, none forfeited, 6 wins: 4 of 10 contested disputes lost.
    state, detail = verdict(4, 0, 6)
    assert state == "contested"
    assert "40%" in detail


def test_forfeits_are_excluded_from_the_contested_loss_rate():
    # 10 losses, 2 forfeited, 8 wins: the contested rate is 8 of 16, not 10 of 18.
    state, detail = verdict(10, 2, 8)
    assert state == "leaking"
    assert "16 contested" in detail
    assert "50%" in detail


def test_thirty_percent_forfeits_is_the_alarm_and_it_is_inclusive():
    assert verdict(100, 29, 0)[0] == "leaking"
    state, detail = verdict(10, 3, 0)
    assert state == "absent"
    assert "no dispute workflow" in detail


def test_every_loss_forfeited_has_no_loss_rate_to_quote():
    state, detail = verdict(5, 5, 0)
    assert state == "absent"
    assert "nothing was contested" in detail
    assert verdict(1, 2, 0)[0] == "unknown"
''',
"test_js_file": "stripe-dispute-forfeits.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-dispute-forfeits.mjs';

test('no closed disputes is not a perfect record', () => {
  assert.equal(verdict(0, 0, 0)[0], 'no_disputes');
});

test('losses that were all answered report the real loss rate', () => {
  const [state, detail] = verdict(4, 0, 6);
  assert.equal(state, 'contested');
  assert.match(detail, /40% of the time/);
});

test('forfeits are excluded from the contested loss rate', () => {
  const [state, detail] = verdict(10, 2, 8);
  assert.equal(state, 'leaking');
  assert.match(detail, /16 contested/);
  assert.match(detail, /50% of the time/);
});

test('thirty percent forfeits is the alarm and it is inclusive', () => {
  assert.equal(verdict(100, 29, 0)[0], 'leaking');
  const [state, detail] = verdict(10, 3, 0);
  assert.equal(state, 'absent');
  assert.match(detail, /no dispute workflow/);
});

test('every loss forfeited has no loss rate to quote', () => {
  const [state, detail] = verdict(5, 5, 0);
  assert.equal(state, 'absent');
  assert.match(detail, /nothing was contested/);
  assert.equal(verdict(1, 2, 0)[0], 'unknown');
});
''',
"faq": [
 ("How do I tell a forfeited dispute from one I lost on the evidence?",
  "evidence_details.submission_count on the dispute object. A dispute with status lost and a submission count of zero was never answered; the deadline simply passed. Anything above zero was judged on what you sent."),
 ("What is a normal forfeit share?",
  "Zero is the target, because a forfeit is a process failure rather than a business outcome. Anything above zero is recoverable, and above roughly 30% the honest description is that disputes are not being worked at all, whatever the calendar says."),
 ("Why report the contested loss rate separately?",
  "Because it is the only number that measures your evidence. Mixing forfeits into the denominator makes a good evidence package look like a poor one and supports the conclusion that fighting disputes is pointless, which then produces more forfeits."),
 ("Do forfeited disputes still count toward my chargeback rate?",
  "Yes. The networks count the dispute, not your effort. Sustained high rates lead to monitoring programmes with fees and remediation requirements attached, so a process gap in the inbox becomes an account-standing problem."),
 ("Can this script fix the disputes it finds?",
  "No, and by then nothing can: a closed dispute is closed. It measures a window that has already passed so the process change can be justified and, later, shown to have worked. The check that prevents the next one is the daily sweep on evidence_details.due_by."),
],
"related": [
 ("/stripe/dispute-deadline-72h-no-evidence/", "Disputes are hours from due_by with no evidence attached"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
 ("/stripe/radar-blocked-payments-ignored/", "Radar blocks payments and nobody reads the block reasons"),
],
"citations": [CITE_DISPUTE_OBJ, CITE_RESPONDING, CITE_MEASURING, CITE_DISPUTE_LIST],
},

{
"slug": "checkout-sessions-unreconcilable",
"title": "Checkout Sessions carry no ID that maps back to your order",
"description": "A payment lands and nothing on it points at your database. client_reference_id and metadata both default to empty, and nothing warns you.",
"h1": "Checkout Sessions carry no ID that maps back to your order",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe client_reference_id", "checkout session metadata",
             "stripe reconcile orders", "stripe checkout order id",
             "payment link metadata"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Support is reconciling payments by matching an email address and an amount against the order table by hand. It works, mostly, until two people buy the same thing on the same day. Then a dispute arrives on one of those charges and nobody can say with confidence which order it was, which is a bad position to answer a dispute from.",
"short_answer": """<p>Page <code>GET /v1/checkout/sessions?created[gte]=&lt;now-30d&gt;</code> and count the sessions where <code>client_reference_id</code> is <code>null</code> and <code>metadata</code> carries none of your own keys. Those two fields are the only places on a Session that hold an identifier of yours, and both default to empty.</p>
<p>The subset that matters most is sessions with <code>payment_status</code> of <code>paid</code> and neither field set: money taken that points at nothing. Fix it at creation with <code>client_reference_id</code> and <code>metadata[order_id]</code>; for Payment Links, set metadata on the link, which copies onto every Session it creates.</p>""",
"problem": """<p>Everything works while volume is low, because email plus amount plus a date is very nearly unique when there are eleven orders a day. The reconciliation is manual, but nobody calls it a problem: it is five minutes in the morning.</p>
<p>It stops working in three places at once. Refunds go to the wrong order when two customers share a name. Fulfilment webhooks arrive with nothing to look up, so the handler either guesses or drops the event. And a dispute has to be answered with the product description, the delivery address and the customer's own messages, all of which live in your database behind an order id that the payment does not carry. The evidence exists; the join does not.</p>""",
"why": """<p><strong>Both fields default to empty and neither is required.</strong> A Checkout Session created without them is completely valid, completes normally, and takes the money. There is no warning at creation, no field marked missing in the Dashboard, and nothing in the test-mode flow that behaves differently.</p>
<p><strong>The identifier you do have points the wrong way.</strong> You get back a <code>cs_</code> id and later a <code>pi_</code> id, and it is tempting to store those on the order and call it done. That resolves Stripe to order, but the incoming direction &mdash; a webhook, a dispute, a support enquiry that starts with a charge &mdash; still has nothing to go on unless the object itself carries your id.</p>
<p><strong>Payment Links look like they have no place to put one.</strong> A link is created once in the Dashboard and reused, so there is no per-order code path to add a reference in. Metadata set on the link is copied onto every Session it creates, which is the piece people miss, and the reason link-driven checkouts are usually the worst offenders on the report.</p>
<p><strong>It is only fixable going forward.</strong> Metadata can be added to a Session after the fact, but nobody is going to backfill six months of them by hand, and the identifier you would backfill from is the same email-and-amount guess that made this a problem. Every day the check does not run is another day of unreconcilable payments.</p>""",
"steps": [
 {"h": "Count the last 30 days of sessions",
  "body": """<p><code>GET /v1/checkout/sessions?created[gte]=&lt;unix&gt;&amp;limit=100</code>, paginated. A month is enough to see the shape and short enough that the count means something about the code that runs today rather than the code from last year.</p>"""},
 {"h": "Decide which keys count as an identifier",
  "body": """<p>Pass the metadata keys your own system actually reads &mdash; usually <code>order_id</code>, sometimes <code>user_id</code> as well. A session with unrelated metadata such as a UTM source is not reconcilable, and a check that treats any non-empty metadata as sufficient will report a clean bill of health on an account that cannot answer a single dispute.</p>"""},
 {"h": "Separate paid sessions from abandoned ones",
  "body": """<p>An expired session with no reference is untidy. A <code>paid</code> session with no reference is money you cannot attribute. Report them separately or the urgent number drowns in the harmless one, since most sessions in any window are abandoned.</p>"""},
 {"h": "Set both fields at creation, not one",
  "body": """<p><code>client_reference_id</code> is the field Stripe surfaces in the Dashboard and in exports; <code>metadata</code> is the one that survives into your own tooling and can carry more than one key. Setting both costs nothing and each covers the other's gap.</p>"""},
 {"h": "Fix Payment Links on the link, once",
  "body": """<p>Set <code>metadata</code> on the Payment Link itself. Every Session created from it inherits that metadata, so a link that says which campaign or product it is at least narrows a payment to a cohort even when there is no per-order id to give.</p>"""},
 {"h": "Run it weekly and watch the paid count",
  "body": """<p>The number to hold at zero is paid-and-unlinked. If it moves off zero, a new code path started creating Sessions without a reference, and it is much cheaper to find that in the week it shipped.</p>"""},
],
"verify": """<p>Re-run after the change and check the paid sessions specifically. The unlinked count over recent sessions should fall to zero as the old ones age out of the window.</p>
<pre><code class="language-bash">python3 stripe_checkout_reconciliation.py --days 7
# 128 session(s): 128 linked, 0 partial, 0 unlinked, 0 orphaned</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/checkout/sessions</code>, no writes. The classifier is pure and takes the expected metadata keys as an argument, because the interesting distinction &mdash; metadata that exists but carries none of <em>your</em> keys &mdash; is exactly the one a hardcoded truthiness check on <code>metadata</code> would get wrong.",
"py_file": "stripe_checkout_reconciliation.py",
"py": '''"""Report Stripe Checkout Sessions that carry no identifier of your own.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Checkout Sessions. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_checkout_reconciliation")

API = "https://api.stripe.com/v1"

DEFAULT_KEYS = ("order_id",)


def verdict(session, expected_keys=DEFAULT_KEYS):
    """Classify one Checkout Session. Pure, so the rules can be tested offline.

    `expected_keys` are the metadata keys your own system reads. Metadata that
    exists but holds none of them is not reconcilable, however full it looks.
    Returns (state, detail).
    """
    ref = str(session.get("client_reference_id") or "").strip()
    meta = session.get("metadata") or {}
    present = [k for k in expected_keys if str(meta.get(k) or "").strip()]

    if ref:
        return ("linked", "client_reference_id=%s" % ref)
    if expected_keys and len(present) == len(expected_keys):
        return ("linked", "metadata carries %s" % ", ".join(present))
    if present:
        missing = [k for k in expected_keys if k not in present]
        return ("partial",
                "metadata has %s but is missing %s"
                % (", ".join(present), ", ".join(missing)))
    if session.get("payment_status") == "paid":
        return ("orphaned",
                "paid, with no client_reference_id and none of %s in metadata: "
                "money that points at nothing" % ", ".join(expected_keys))
    return ("unlinked",
            "no identifier of yours, but payment_status is %r so nothing has "
            "been taken yet" % (session.get("payment_status"),))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def sessions(http, since, limit):
    """Yield Checkout Sessions created since `since`, newest first."""
    seen = 0
    params = {"limit": 100, "created[gte]": int(since)}
    while True:
        page = get(http, "/checkout/sessions", params)
        data = page.get("data", [])
        for s in data:
            yield s
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read sessions")
    ap.add_argument("--keys", default=",".join(DEFAULT_KEYS),
                    help="comma-separated metadata keys your system reads")
    ap.add_argument("--max-sessions", type=int, default=5000,
                    help="stop paginating after this many sessions")
    ap.add_argument("--show", type=int, default=10,
                    help="how many orphaned session ids to print")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    expected = tuple(k.strip() for k in args.keys.split(",") if k.strip())
    http = requests.Session()
    http.headers.update({"Authorization": "Bearer " + key})

    counts = {"linked": 0, "partial": 0, "unlinked": 0, "orphaned": 0}
    worst = []
    total = 0
    for s in sessions(http, time.time() - args.days * 86400, args.max_sessions):
        total += 1
        state, detail = verdict(s, expected)
        counts[state] = counts.get(state, 0) + 1
        if state == "orphaned" and len(worst) < args.show:
            worst.append((s.get("id", "?"), detail))

    log.info("%d session(s): %d linked, %d partial, %d unlinked, %d orphaned",
             total, counts["linked"], counts["partial"], counts["unlinked"],
             counts["orphaned"])
    for sid, detail in worst:
        log.warning("orphaned  %s  %s", sid, detail)

    if counts["orphaned"] or counts["partial"]:
        log.warning("  repair: POST %s/checkout/sessions "
                    "-d client_reference_id=<your_order_id> "
                    "-d 'metadata[order_id]=<your_order_id>'", API)
        log.warning("  for Payment Links, set metadata on the link itself: it is "
                    "copied onto every Session the link creates")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-checkout-reconciliation.mjs",
"js": '''/**
 * Report Stripe Checkout Sessions that carry no identifier of your own.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Checkout Sessions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const DEFAULT_KEYS = ['order_id'];

/**
 * Classify one Checkout Session. Pure, so the rules can be tested offline.
 * `expectedKeys` are the metadata keys your own system reads.
 */
export function verdict(session, expectedKeys = DEFAULT_KEYS) {
  const ref = String(session.client_reference_id ?? '').trim();
  const meta = session.metadata ?? {};
  const present = expectedKeys.filter((k) => String(meta[k] ?? '').trim());

  if (ref) return ['linked', `client_reference_id=${ref}`];
  if (expectedKeys.length && present.length === expectedKeys.length) {
    return ['linked', `metadata carries ${present.join(', ')}`];
  }
  if (present.length) {
    const missing = expectedKeys.filter((k) => !present.includes(k));
    return ['partial',
      `metadata has ${present.join(', ')} but is missing ${missing.join(', ')}`];
  }
  if (session.payment_status === 'paid') {
    return ['orphaned',
      `paid, with no client_reference_id and none of ${expectedKeys.join(', ')} ` +
      'in metadata: money that points at nothing'];
  }
  return ['unlinked',
    'no identifier of yours, but payment_status is ' +
    `${JSON.stringify(session.payment_status)} so nothing has been taken yet`];
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

export async function* sessions(key, since, limit = 5000) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': Math.floor(since) };
  for (;;) {
    const page = await get(key, '/checkout/sessions', params);
    const data = page.data ?? [];
    for (const s of data) { yield s; seen += 1; }
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

  const days = Number(process.argv[2] ?? 30);
  const expected = (process.argv[3] ?? DEFAULT_KEYS.join(','))
    .split(',').map((k) => k.trim()).filter(Boolean);

  const counts = { linked: 0, partial: 0, unlinked: 0, orphaned: 0 };
  const worst = [];
  let total = 0;

  for await (const s of sessions(key, Date.now() / 1000 - days * 86400)) {
    total += 1;
    const [state, detail] = verdict(s, expected);
    counts[state] = (counts[state] ?? 0) + 1;
    if (state === 'orphaned' && worst.length < 10) worst.push([s.id ?? '?', detail]);
  }

  console.log(`${total} session(s): ${counts.linked} linked, ${counts.partial} ` +
              `partial, ${counts.unlinked} unlinked, ${counts.orphaned} orphaned`);
  for (const [id, detail] of worst) console.warn(`orphaned  ${id}  ${detail}`);

  if (counts.orphaned || counts.partial) {
    console.warn(`  repair: POST ${API}/checkout/sessions ` +
                 `-d client_reference_id=<your_order_id> ` +
                 `-d 'metadata[order_id]=<your_order_id>'`);
    console.warn('  for Payment Links, set metadata on the link itself: it is ' +
                 'copied onto every Session the link creates');
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
"test_intro": "The case that decides whether this check is worth running is a session with plenty of metadata, none of it yours. A truthiness test on <code>metadata</code> calls that linked and reports zero problems on an account that cannot attribute a single payment, so it gets its own test alongside the empty-string reference that looks set and is not.",
"test_py_file": "test_stripe_checkout_reconciliation.py",
"test_py": '''from stripe_checkout_reconciliation import verdict


def test_client_reference_id_is_enough_on_its_own():
    state, detail = verdict({"client_reference_id": "ord_918", "payment_status": "paid"})
    assert state == "linked"
    assert "ord_918" in detail


def test_metadata_full_of_someone_elses_keys_is_not_linked():
    # A truthiness check on metadata would call this linked and report nothing.
    state, _ = verdict({"metadata": {"utm_source": "newsletter"},
                        "payment_status": "paid"})
    assert state == "orphaned"


def test_paid_and_unidentified_is_worse_than_abandoned():
    assert verdict({"payment_status": "paid"})[0] == "orphaned"
    assert verdict({"payment_status": "unpaid"})[0] == "unlinked"


def test_some_expected_keys_but_not_all_is_partial():
    state, detail = verdict({"metadata": {"order_id": "42"}, "payment_status": "paid"},
                            ("order_id", "user_id"))
    assert state == "partial"
    assert "user_id" in detail


def test_empty_and_whitespace_references_do_not_count_as_set():
    assert verdict({"client_reference_id": "", "payment_status": "paid"})[0] == "orphaned"
    assert verdict({"client_reference_id": "   ", "payment_status": "paid"})[0] == "orphaned"
    assert verdict({"metadata": {"order_id": " "}, "payment_status": "paid"})[0] == "orphaned"
''',
"test_js_file": "stripe-checkout-reconciliation.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-checkout-reconciliation.mjs';

test('client_reference_id is enough on its own', () => {
  const [state, detail] = verdict(
    { client_reference_id: 'ord_918', payment_status: 'paid' });
  assert.equal(state, 'linked');
  assert.match(detail, /ord_918/);
});

test('metadata full of someone elses keys is not linked', () => {
  const [state] = verdict(
    { metadata: { utm_source: 'newsletter' }, payment_status: 'paid' });
  assert.equal(state, 'orphaned');
});

test('paid and unidentified is worse than abandoned', () => {
  assert.equal(verdict({ payment_status: 'paid' })[0], 'orphaned');
  assert.equal(verdict({ payment_status: 'unpaid' })[0], 'unlinked');
});

test('some expected keys but not all is partial', () => {
  const [state, detail] = verdict(
    { metadata: { order_id: '42' }, payment_status: 'paid' },
    ['order_id', 'user_id']);
  assert.equal(state, 'partial');
  assert.match(detail, /user_id/);
});

test('empty and whitespace references do not count as set', () => {
  assert.equal(
    verdict({ client_reference_id: '', payment_status: 'paid' })[0], 'orphaned');
  assert.equal(
    verdict({ client_reference_id: '   ', payment_status: 'paid' })[0], 'orphaned');
  assert.equal(
    verdict({ metadata: { order_id: ' ' }, payment_status: 'paid' })[0], 'orphaned');
});
''',
"faq": [
 ("What is client_reference_id actually for?",
  "It is a free-text field on a Checkout Session for your own identifier, surfaced in the Dashboard and in exports. Stripe never interprets it. Put your order id in it at creation and the payment carries a pointer back to your database from that moment on."),
 ("Should I use client_reference_id or metadata?",
  "Both. client_reference_id is a single value that shows up in the Dashboard where support will look for it. Metadata holds several keys and is what your own webhook handlers read. They cost nothing to set together and each covers a case the other misses."),
 ("How do I attach an order id to a Payment Link?",
  "Set metadata on the Payment Link itself; it is copied onto every Checkout Session the link creates. A static link cannot carry a per-order id, so use it to identify the product or campaign, and create Sessions in code when you need true per-order attribution."),
 ("Can I add metadata to a Session after it completes?",
  "You can update the Session's metadata afterwards, but you have to already know which order it was, and if you knew that you would not have needed the field. Treat this as fixable going forward only, and reconcile the historical window by hand once."),
 ("Why does this matter more for disputes than for reporting?",
  "Because dispute evidence has a deadline. Reporting can wait while somebody matches emails to amounts; a dispute response needs the product description, the delivery address and the customer's messages assembled within days, and all of that lives behind an order id the charge does not carry."),
],
"related": [
 ("/stripe/duplicate-customers-same-email/", "Duplicate customers share an email and split billing"),
 ("/stripe/dispute-deadline-72h-no-evidence/", "Disputes are hours from due_by with no evidence attached"),
 ("/stripe/abandoned-requires-action-intents/", "3DS handoff breaks and requires_action intents pile up"),
],
"citations": [CITE_SESSION_OBJ, CITE_SESSION_LIST, CITE_METADATA, CITE_PAYMENT_LINKS],
},

{
"slug": "duplicate-customers-same-email",
"title": "Duplicate customers share an email and split billing",
"description": "Stripe does not enforce email uniqueness on Customers. One person ends up with three records, and their card, subscription and invoices sit on different ones.",
"h1": "duplicate customers share an email and split billing",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe duplicate customers", "stripe customer same email",
             "stripe customer email uniqueness", "stripe merge customers",
             "stripe customers list email"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A customer writes in to say they were charged twice this month. Support finds their subscription, checks it, and it billed once. The second charge is on a different Customer record with the same email address, created the day they resubscribed, and it has its own card, its own subscription and its own renewal date.",
"short_answer": """<p>Page <code>GET /v1/customers?limit=100</code>, lowercase every <code>email</code>, group, and flag any address with more than one record. Stripe does not enforce uniqueness on customer email, by design, so any code path that creates a Customer without looking one up first mints a new <code>cus_</code> every time.</p>
<p>Then find out which duplicates hold anything: <code>GET /v1/payment_methods?customer=&lt;id&gt;&amp;type=card</code> and <code>GET /v1/subscriptions?customer=&lt;id&gt;</code>. Empty duplicates are untidy. Two records with live subscriptions on one email address are two bills.</p>""",
"problem": """<p>The obvious cost is support time: three records, and the card is on one, the subscription on another, the invoices split across both. Every enquiry starts with a hunt, and any answer given from the wrong record is wrong in a way nobody notices for a month.</p>
<p>The expensive cost is billing. Two Customer records each with an active subscription renew independently. Cancelling one leaves the other charging, which is the shape of the "I cancelled and you kept billing me" complaint that ends in a dispute. Analytics inherits the same fault line: churn, lifetime value and active-customer counts all count the records rather than the people, so the numbers are wrong in a direction that flatters.</p>""",
"why": """<p><strong>Stripe deliberately does not enforce uniqueness.</strong> The email on a Customer is a label, not a key. This is one of the oldest complaints in the ecosystem and the answer has always been the same: uniqueness is yours to enforce, because Stripe has no way to know whether two records with one address are one person or a shared family inbox.</p>
<p><strong>Every path that creates a customer is a path that can duplicate one.</strong> A second checkout by a returning customer, a retried webhook that creates before it checks, a re-signup after a cancellation, a Checkout configuration that always creates a customer. Each is reasonable on its own and none of them look like a bug in review.</p>
<p><strong>Lookup by email is stricter than people expect.</strong> The <code>email</code> filter on the customer list is an exact, case-sensitive match. A user who typed a capital on signup and lowercase next time has two records and a lookup that finds neither from the other, which is why the grouping here normalises before comparing.</p>
<p><strong>The duplicate is created at the worst moment.</strong> It happens at checkout, when a card is being saved and a subscription started, so the new empty record does not stay empty. By the time anyone notices, both records hold something worth keeping and merging them is careful manual work rather than a delete.</p>""",
"steps": [
 {"h": "List every customer and normalise the address",
  "body": """<p><code>GET /v1/customers?limit=100</code>, paginated to the end. Lowercase and trim before grouping. Customers with no email are a different problem and belong in their own bucket rather than in one enormous group keyed on nothing.</p>"""},
 {"h": "Find out which duplicates hold value",
  "body": """<p>For each record in a duplicate group, <code>GET /v1/payment_methods?customer=&lt;id&gt;&amp;type=card</code> and <code>GET /v1/subscriptions?customer=&lt;id&gt;</code>. This is the difference between a report you can act on and a list of 400 email addresses. A group where only one record holds anything is a tidy-up; a group where two hold subscriptions is a billing incident.</p>"""},
 {"h": "Confirm a specific case before touching it",
  "body": """<p><code>GET /v1/customers?email=&lt;address&gt;</code> matches exactly and is case-sensitive, so run it against each casing you actually found. <code>GET /v1/customers/search</code> handles substring matching when you need it, at the cost of an index that lags writes by up to a minute.</p>"""},
 {"h": "Stop making new ones first",
  "body": """<p>Look up before you create: <code>GET /v1/customers?email=&lt;address&gt;&amp;limit=1</code>, and reuse the id if there is one. Store the <code>cus_</code> id on your own user row and treat that as the single source of truth, so the lookup is a fallback rather than the mechanism. In Checkout, pass an existing <code>customer</code> instead of relying on customer creation.</p>"""},
 {"h": "Merge deliberately, subscriptions last",
  "body": """<p>Attach the payment methods to the keeper, move or re-create the subscriptions, then delete the empty record. Deleting a customer cancels its subscriptions, so a delete performed in the wrong order is a cancellation you did not intend &mdash; which is exactly why this script prints the steps instead of running them.</p>"""},
 {"h": "Re-run it monthly",
  "body": """<p>New duplicates mean a new code path. The count going up after a release is a much better signal than a support ticket six weeks later.</p>"""},
],
"verify": """<p>Re-run after the lookup-before-create change ships. The count of email addresses with more than one record should stop growing, and the dangerous subset should be empty once the merges are done.</p>
<pre><code class="language-bash">python3 stripe_duplicate_customers.py
# 1,204 customer(s), 0 address(es) with more than one record</code></pre>""",
"code_intro": "One paginated GET over customers, plus two small GETs per duplicated record to find out which of them actually hold a card or a subscription. Nothing writes. Both pure functions are exported and tested: the normalisation, because case is the whole reason the duplicates hide from an exact-match lookup, and the classification, because three records with one real customer among them and three records with two of them billing want very different responses.",
"py_file": "stripe_duplicate_customers.py",
"py": '''"""Report Stripe Customers that share an email address.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Customers, Subscriptions and PaymentMethods. The merge is printed,
never performed, because deleting a customer cancels its subscriptions and this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_duplicate_customers")

API = "https://api.stripe.com/v1"


def normalise(email):
    """Lowercase and trim an address for grouping. Pure.

    Stripe's own email filter is exact and case-sensitive, so a user who
    capitalised once and did not the next time has two records that no exact
    lookup will ever put beside each other. Grouping has to normalise even
    though the confirming API call cannot.
    """
    if not email:
        return None
    return str(email).strip().lower() or None


def verdict(records):
    """Classify one group of customers sharing an address. Pure.

    Each record is {"id": str, "has_card": bool, "has_subscription": bool},
    filled in by the caller. Returns (state, detail).
    """
    n = len(records)
    if n <= 1:
        return ("unique", "one customer for this address")

    subs = [r for r in records if r.get("has_subscription")]
    holders = [r for r in records
               if r.get("has_card") or r.get("has_subscription")]

    if len(subs) > 1:
        return ("split_billing",
                "%d records, %d with a subscription. They renew independently, "
                "so cancelling one leaves the other charging." % (n, len(subs)))
    if len(holders) > 1:
        return ("split_methods",
                "%d records, %d holding a card or a subscription. Support will "
                "answer from whichever one they find first." % (n, len(holders)))
    if holders:
        return ("shells",
                "%d records, one holding everything. The other %d are empty."
                % (n, n - 1))
    return ("empty",
            "%d records, none holding a card or a subscription. Untidy, not "
            "urgent." % n)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def group_by_email(session, limit):
    """Return {normalised email: [customer ids]} plus the number read."""
    groups = {}
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/customers", params)
        data = page.get("data", [])
        for c in data:
            seen += 1
            key = normalise(c.get("email"))
            if key is None:
                continue  # no email is a different problem
            groups.setdefault(key, []).append(c["id"])
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return groups, seen


def enrich(session, customer_id):
    """One record for verdict(), costing two small GETs."""
    cards = get(session, "/payment_methods",
                {"customer": customer_id, "type": "card", "limit": 1})
    subs = get(session, "/subscriptions",
               {"customer": customer_id, "status": "all", "limit": 1})
    return {"id": customer_id,
            "has_card": bool(cards.get("data")),
            "has_subscription": bool(subs.get("data"))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-customers", type=int, default=10000,
                    help="stop paginating after this many customers")
    ap.add_argument("--max-groups", type=int, default=50,
                    help="how many duplicate groups to enrich and report")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    groups, seen = group_by_email(s, args.max_customers)
    dupes = {e: ids for e, ids in groups.items() if len(ids) > 1}
    log.info("%d customer(s), %d address(es) with more than one record",
             seen, len(dupes))
    if not dupes:
        return 0

    # Worst first: the ones with the most records are the ones support is
    # already losing time to.
    ordered = sorted(dupes.items(), key=lambda kv: -len(kv[1]))[:args.max_groups]
    bad = 0
    for email, ids in ordered:
        records = [enrich(s, cid) for cid in ids]
        state, detail = verdict(records)
        log.warning("%-14s %s  %s", state, email, detail)
        log.warning("  records: %s", ", ".join(r["id"] for r in records))
        if state in ("split_billing", "split_methods"):
            bad += 1
            keeper = records[0]["id"]
            log.warning("  merge: POST %s/payment_methods/<pm>/attach "
                        "-d customer=%s, move the subscriptions, then "
                        "DELETE %s/customers/<dupe>", API, keeper, API)
            log.warning("  deleting a customer cancels its subscriptions, so "
                        "empty the record before you delete it")
    log.warning("  prevent: GET %s/customers?email=<address>&limit=1 before "
                "creating, and store the cus_ id on your own user row", API)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-duplicate-customers.mjs",
"js": '''/**
 * Report Stripe Customers that share an email address.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Customers, Subscriptions and PaymentMethods. The merge is printed,
 * never performed, because deleting a customer cancels its subscriptions.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Lowercase and trim an address for grouping. Pure.
 *
 * Stripe's own email filter is exact and case-sensitive, so grouping has to
 * normalise even though the confirming API call cannot.
 */
export function normalise(email) {
  if (!email) return null;
  return String(email).trim().toLowerCase() || null;
}

/**
 * Classify one group of customers sharing an address. Pure.
 * Each record is { id, has_card, has_subscription }, filled in by the caller.
 */
export function verdict(records) {
  const n = records.length;
  if (n <= 1) return ['unique', 'one customer for this address'];

  const subs = records.filter((r) => r.has_subscription);
  const holders = records.filter((r) => r.has_card || r.has_subscription);

  if (subs.length > 1) {
    return ['split_billing',
      `${n} records, ${subs.length} with a subscription. They renew ` +
      'independently, so cancelling one leaves the other charging.'];
  }
  if (holders.length > 1) {
    return ['split_methods',
      `${n} records, ${holders.length} holding a card or a subscription. ` +
      'Support will answer from whichever one they find first.'];
  }
  if (holders.length) {
    return ['shells',
      `${n} records, one holding everything. The other ${n - 1} are empty.`];
  }
  return ['empty',
    `${n} records, none holding a card or a subscription. Untidy, not urgent.`];
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

export async function groupByEmail(key, limit = 10000) {
  const groups = new Map();
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/customers', params);
    const data = page.data ?? [];
    for (const c of data) {
      seen += 1;
      const email = normalise(c.email);
      if (email === null) continue; // no email is a different problem
      groups.set(email, [...(groups.get(email) ?? []), c.id]);
    }
    if (data.length === 0 || !page.has_more || seen >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { groups, seen };
}

async function enrich(key, customerId) {
  const cards = await get(key, '/payment_methods',
    { customer: customerId, type: 'card', limit: 1 });
  const subs = await get(key, '/subscriptions',
    { customer: customerId, status: 'all', limit: 1 });
  return {
    id: customerId,
    has_card: Boolean((cards.data ?? []).length),
    has_subscription: Boolean((subs.data ?? []).length),
  };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const maxGroups = Number(process.argv[2] ?? 50);
  const { groups, seen } = await groupByEmail(key);
  const dupes = [...groups.entries()].filter(([, ids]) => ids.length > 1);

  console.log(`${seen} customer(s), ${dupes.length} address(es) with more than one record`);
  if (dupes.length === 0) return;

  // Worst first: the ones with the most records are the ones support is
  // already losing time to.
  dupes.sort((a, b) => b[1].length - a[1].length);
  let bad = 0;
  for (const [email, ids] of dupes.slice(0, maxGroups)) {
    const records = [];
    for (const id of ids) records.push(await enrich(key, id));
    const [state, detail] = verdict(records);
    console.warn(`${state.padEnd(14)} ${email}  ${detail}`);
    console.warn(`  records: ${records.map((r) => r.id).join(', ')}`);
    if (state === 'split_billing' || state === 'split_methods') {
      bad += 1;
      console.warn(`  merge: POST ${API}/payment_methods/<pm>/attach ` +
                   `-d customer=${records[0].id}, move the subscriptions, then ` +
                   `DELETE ${API}/customers/<dupe>`);
      console.warn('  deleting a customer cancels its subscriptions, so empty ' +
                   'the record before you delete it');
    }
  }
  console.warn(`  prevent: GET ${API}/customers?email=<address>&limit=1 before ` +
               'creating, and store the cus_ id on your own user row');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth pinning. Normalisation has to fold case, because a capital letter on signup is the most common way a duplicate hides from an exact-match lookup. And a group with two live subscriptions has to sort above a group with two saved cards, because one of those is a support annoyance and the other is billing the same person twice.",
"test_py_file": "test_stripe_duplicate_customers.py",
"test_py": '''from stripe_duplicate_customers import normalise, verdict


def rec(cid, card=False, sub=False):
    return {"id": cid, "has_card": card, "has_subscription": sub}


def test_normalisation_folds_case_and_whitespace():
    assert normalise("  Ada@Example.COM ") == "ada@example.com"
    assert normalise("") is None
    assert normalise(None) is None


def test_a_single_record_is_not_a_duplicate():
    assert verdict([rec("cus_1", card=True)])[0] == "unique"


def test_two_live_subscriptions_is_the_billing_case():
    state, detail = verdict([rec("cus_1", sub=True), rec("cus_2", sub=True)])
    assert state == "split_billing"
    assert "cancelling one" in detail


def test_two_records_holding_cards_is_a_support_problem_not_a_billing_one():
    state, _ = verdict([rec("cus_1", card=True), rec("cus_2", card=True)])
    assert state == "split_methods"


def test_duplicates_holding_nothing_are_ranked_below_ones_that_do():
    assert verdict([rec("cus_1", card=True), rec("cus_2")])[0] == "shells"
    assert verdict([rec("cus_1"), rec("cus_2"), rec("cus_3")])[0] == "empty"
''',
"test_js_file": "stripe-duplicate-customers.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalise, verdict } from './stripe-duplicate-customers.mjs';

const rec = (id, card = false, sub = false) =>
  ({ id, has_card: card, has_subscription: sub });

test('normalisation folds case and whitespace', () => {
  assert.equal(normalise('  Ada@Example.COM '), 'ada@example.com');
  assert.equal(normalise(''), null);
  assert.equal(normalise(null), null);
});

test('a single record is not a duplicate', () => {
  assert.equal(verdict([rec('cus_1', true)])[0], 'unique');
});

test('two live subscriptions is the billing case', () => {
  const [state, detail] = verdict([rec('cus_1', false, true), rec('cus_2', false, true)]);
  assert.equal(state, 'split_billing');
  assert.match(detail, /cancelling one/);
});

test('two records holding cards is a support problem not a billing one', () => {
  assert.equal(verdict([rec('cus_1', true), rec('cus_2', true)])[0], 'split_methods');
});

test('duplicates holding nothing are ranked below ones that do', () => {
  assert.equal(verdict([rec('cus_1', true), rec('cus_2')])[0], 'shells');
  assert.equal(verdict([rec('cus_1'), rec('cus_2'), rec('cus_3')])[0], 'empty');
});
''',
"faq": [
 ("Why does Stripe allow two customers with the same email?",
  "Because email is a label on the Customer object, not a key. Stripe cannot know whether two records on one address are one person or two people sharing an inbox, so uniqueness is left to you. It has been asked about for over a decade and the answer has not changed."),
 ("How do I look up a customer by email?",
  "GET /v1/customers?email=<address> filters on an exact, case-sensitive match. GET /v1/customers/search with a query handles substring matching, at the cost of a search index that can lag a write by up to a minute. Neither will fold case for you, which is why duplicates that differ only in capitalisation stay invisible."),
 ("What is the safe order to merge duplicates in?",
  "Attach the payment methods to the record you are keeping, move or re-create the subscriptions, confirm the loser holds nothing, and only then delete it. Deleting a customer cancels its subscriptions immediately, so a delete in the wrong order is an unintended cancellation."),
 ("Can I stop Checkout creating a new customer every time?",
  "Yes. Pass an existing customer id to the Checkout Session rather than relying on customer creation. Look the customer up by email first, and store the cus_ id on your own user row so the next checkout does not need the lookup at all."),
 ("Is this worth fixing if the duplicates are empty?",
  "It is worth preventing, not urgently worth merging. Empty duplicates only cost search time. The reason to act is that the code path creating them will eventually create one at checkout, where a card and a subscription land on the new record, and that one is a billing problem rather than an untidy list."),
],
"related": [
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access forever"),
],
"citations": [CITE_CUSTOMER_LIST, CITE_CUSTOMER_OBJ, CITE_CUSTOMER_SEARCH, CITE_KEYS],
},

]
