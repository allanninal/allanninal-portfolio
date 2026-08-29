#!/usr/bin/env python3
"""/stripe/ field notes, batch N — the writing.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair
for a human to run against a live payments account.

This batch is about the fraud controls that are configured but not working:
a review queue nobody empties, a block rule an allow rule silently overrides,
verification results that are collected and then ignored, and a statement
descriptor that never reaches the card networks at all.
"""

CITE_REVIEW_OBJ = ("The review object — Stripe API reference",
                   "https://docs.stripe.com/api/radar/reviews/object")
CITE_RADAR_REVIEWS = ("Reviews — Stripe Docs", "https://docs.stripe.com/radar/reviews")
CITE_RADAR_RULES = ("Rules — Stripe Docs", "https://docs.stripe.com/radar/rules")
CITE_CHARGE_OBJ = ("The charge object — Stripe API reference",
                   "https://docs.stripe.com/api/charges/object")
CITE_DECLINES = ("Declines — Stripe Docs", "https://docs.stripe.com/declines")
CITE_HOLD = ("Place a hold on a payment method — Stripe Docs",
             "https://docs.stripe.com/payments/place-a-hold-on-a-payment-method")
CITE_EFW = ("The early fraud warning object — Stripe API reference",
            "https://docs.stripe.com/api/radar/early_fraud_warnings/object")
CITE_ACCOUNT_OBJ = ("The account object — Stripe API reference",
                    "https://docs.stripe.com/api/accounts/object")
CITE_PREVENTION = ("Preventing disputes and fraud — Stripe Docs",
                   "https://docs.stripe.com/disputes/prevention/best-practices")
CITE_MONITORING = ("Dispute monitoring programs — Stripe Docs",
                   "https://docs.stripe.com/disputes/monitoring-programs")

GUIDES = [

{
"slug": "radar-reviews-open-stale",
"title": "Radar reviews sit open for days while funds stay at risk",
"description": "The review queue grows and nobody works it. Flagged payments ship anyway, and any uncaptured authorization is released at seven days.",
"h1": "radar reviews sit open for days while funds stay at risk",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe radar review queue", "stripe review open true",
             "stripe radar reviews stale", "closed_reason approved",
             "stripe review opened_reason"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody added a review rule, which was the right instinct. The queue it feeds has forty-one items in it, the oldest is from three weeks ago, and nobody has opened the page since the week it was set up. Every one of those payments was already taken, and the ones that were not have quietly stopped being collectable.",
"short_answer": """<p>Paginate <code>GET /v1/reviews</code> and look at <code>open</code>. Anything with <code>open == true</code> is a payment Stripe is waiting on you to judge. Take the age from <code>created</code>: past <strong>3 days</strong> the queue is not being worked, and past <strong>7 days</strong> any charge that was authorized but not captured has had its hold released and cannot be captured at all.</p>
<p>Then audit the rule that fills the queue. Over 90 days, divide the reviews closed with <code>closed_reason == "approved"</code> by all the closed ones. A ratio near 1.0 means the rule is flagging traffic you always accept, and the queue is pure cost.</p>""",
"problem": """<p>An unworked review queue is worse than no review rule, and that is the part people get wrong. With no rule the payment goes through and you take the fraud risk knowingly. With a rule and no one working it, the payment <em>also</em> goes through &mdash; a review does not hold anything back on a normal automatic-capture integration &mdash; and you have added a queue that generates guilt rather than decisions.</p>
<p>On separate authorization and capture it is materially worse. There the review really is blocking, because you were going to capture manually and now nobody has. Seven days later the authorization is released by the issuer. The order was picked, packed, possibly shipped, and the charge you were relying on no longer exists to capture.</p>""",
"why": """<p><strong>The queue lives somewhere nobody has a reason to visit.</strong> Payments show up in reporting, disputes arrive by email, failed payouts eventually make somebody call. A review sits on a Dashboard page that has no notification attached to it unless you subscribed to <code>review.opened</code>, and almost nobody did.</p>
<p><strong>The rule that fills it was written to be safe, which means broad.</strong> Stripe's own example of a rule to narrow is <code>if :card_funding: = 'prepaid'</code>, tightened to <code>if :is_disposable_email: and :card_funding: = 'prepaid'</code>. The broad version flags a large, mostly legitimate slice of traffic. Every one of those needs a human, and every one of them gets approved, until the humans stop coming.</p>
<p><strong>Approving everything looks like diligence and is indistinguishable from doing nothing.</strong> If the last two hundred reviews were all approved, the rule has never once changed an outcome. That is a measurable fact sitting in <code>closed_reason</code>, and it is the number that tells you to delete the rule rather than staff the queue.</p>
<p><strong>The seven-day capture deadline is invisible from the queue itself.</strong> The review object does not say the authorization has lapsed. You have to read <code>captured</code> on the charge behind it, and by then it is a fact rather than a warning.</p>""",
"steps": [
 {"h": "Page the reviews and split on open",
  "body": """<p><code>GET /v1/reviews</code> returns closed reviews too, which is useful: the closed ones are the evidence about the rule and the open ones are the work. Filter client-side on <code>open</code> rather than assuming a filter parameter exists.</p>"""},
 {"h": "Age every open review from created",
  "body": """<p>Three days is when a queue stops being a queue and becomes a backlog; Stripe's own guidance is to work reviews as soon as possible. Seven days is not a judgement call, it is the point at which an uncaptured authorization is gone.</p>"""},
 {"h": "Read captured on the charge behind each open review",
  "body": """<p>This is the field that separates "we still owe someone a decision" from "we can no longer act on this at all". <code>GET /v1/charges/{id}</code> for the id in <code>review.charge</code>. Cache it; several reviews can point at the same charge after a retry.</p>"""},
 {"h": "Group the open ones by opened_reason",
  "body": """<p><code>rule</code> means one of your Radar rules put it there and the rule is a candidate for narrowing. <code>manual</code> means a person did, which is a different conversation. A queue that is 90% <code>rule</code> has a configuration problem, not a staffing problem.</p>"""},
 {"h": "Compute the approval rate before you decide to staff the queue",
  "body": """<p>Over 90 days, <code>closed_reason == "approved"</code> against every closed review. Near 1.0 and the honest fix is to delete or narrow the rule in Dashboard, Radar, then Rules. Below that, the rule is earning its place and the queue needs an owner and an alert on <code>review.opened</code>.</p>"""},
],
"verify": """<p>Re-run after the queue is worked. Nothing open past three days, and the approval rate should have a verdict you are willing to defend.</p>
<pre><code class="language-bash">python3 stripe_radar_review_queue.py
# 0 open review(s) past 3 days
# earning   41% approved: the rule is catching real fraud</code></pre>""",
"code_intro": "Two read endpoints and no writes &mdash; a restricted key with read access to Reviews and Charges is enough. Two pure functions carry the judgement: one ages a single open review against the two deadlines that matter, and one turns ninety days of <code>closed_reason</code> values into a verdict on the rule itself.",
"py_file": "stripe_radar_review_queue.py",
"py": '''"""Report Stripe Radar reviews left open while the funds behind them are at risk.

Read only. Paginated GETs and nothing else: give this a RESTRICTED key with read
access to Reviews and Charges. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_radar_review_queue")

API = "https://api.stripe.com/v1"

STALE_DAYS = 3     # past this the queue is a backlog, not a queue
LAPSE_DAYS = 7     # an uncaptured authorization is released at this age
MIN_CLOSED = 20    # below this the approval rate is noise
OVERBROAD = 0.95   # approvals at or above this: the rule never changes an outcome
WIDE = 0.80


def verdict(age_days, captured):
    """Classify one open review. Pure, so both deadlines can be tested offline.

    `captured` is the `captured` flag of the review's charge, or None when the
    charge could not be read. Returns (state, detail).
    """
    if age_days < STALE_DAYS:
        return ("open",
                "open for %.1f day(s), still inside the window Stripe asks you to "
                "work" % age_days)
    if captured is False and age_days >= LAPSE_DAYS:
        return ("lapsed",
                "open for %.1f day(s) on an uncaptured authorization: the hold was "
                "released at %d days and approving it now captures nothing"
                % (age_days, LAPSE_DAYS))
    if captured is False:
        return ("expiring",
                "open for %.1f day(s) on an uncaptured authorization, released in "
                "%.1f day(s)" % (age_days, LAPSE_DAYS - age_days))
    if age_days >= LAPSE_DAYS:
        return ("critical",
                "open for %.1f day(s) on a captured charge: the money is with you "
                "and the dispute window is already running" % age_days)
    return ("stale", "open for %.1f day(s) on a captured charge" % age_days)


def rule_health(approved, closed):
    """Judge the review rule from how its reviews were closed. Pure.

    `approved` counts closed_reason == "approved"; `closed` counts every review
    with any closed_reason. Returns (state, detail).
    """
    if closed < MIN_CLOSED:
        return ("insufficient",
                "%d closed review(s) is too few to judge the rule" % closed)
    rate = approved / float(closed)
    if rate >= OVERBROAD:
        return ("overbroad",
                "%.0f%% of closed reviews were approved: the rule flags traffic you "
                "always accept and has never changed an outcome" % (rate * 100))
    if rate >= WIDE:
        return ("wide",
                "%.0f%% approved: add a second predicate before staffing this queue"
                % (rate * 100))
    return ("earning", "%.0f%% approved: the rule is catching real fraud"
            % (rate * 100))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page(session, path, cap, **params):
    """Collect up to `cap` objects from a list endpoint."""
    out = []
    params = dict(params)
    params["limit"] = 100
    while True:
        p = get(session, path, **params)
        data = p.get("data", [])
        out.extend(data)
        if not data or not p.get("has_more") or len(out) >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def captured_flag(session, charge_id, cache):
    """Read `captured` off the charge behind a review. None when unreadable."""
    if not charge_id:
        return None
    if charge_id not in cache:
        try:
            cache[charge_id] = get(session, "/charges/" + charge_id).get("captured")
        except requests.HTTPError:
            cache[charge_id] = None
    return cache[charge_id]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="window for the approval-rate audit")
    ap.add_argument("--max-reviews", type=int, default=2000,
                    help="stop paginating after this many reviews")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    since = now - args.days * 86400
    reviews = page(s, "/reviews", args.max_reviews)

    cache = {}
    approved = closed = flagged = 0
    by_reason = {}
    for rev in reviews:
        created = rev.get("created", now)
        if created >= since and rev.get("closed_reason"):
            closed += 1
            if rev["closed_reason"] == "approved":
                approved += 1
        if not rev.get("open"):
            continue
        reason = rev.get("opened_reason") or "unknown"
        by_reason[reason] = by_reason.get(reason, 0) + 1
        age = (now - created) / 86400.0
        state, detail = verdict(age, captured_flag(s, rev.get("charge"), cache))
        if state == "open":
            log.info("%-9s %s  %s", state, rev.get("id"), detail)
            continue
        flagged += 1
        log.warning("%-9s %s  %s", state, rev.get("id"), detail)
        log.warning("    opened by %s, charge %s", reason, rev.get("charge"))

    for reason, n in sorted(by_reason.items()):
        log.info("%d open review(s) opened by %s", n, reason)
    health, detail = rule_health(approved, closed)
    log.info("%-12s %s", health, detail)

    if not flagged and health not in ("overbroad", "wide"):
        log.info("0 open review(s) past %d days", STALE_DAYS)
        return 0

    if flagged:
        log.warning("  work the queue: Dashboard, Radar, Reviews, then Approve, "
                    "Refund, or Refund and report fraud on each one")
        log.warning("  alert instead of polling: subscribe an endpoint to "
                    "review.opened")
    if health in ("overbroad", "wide"):
        log.warning("  narrow the rule in Dashboard, Radar, Rules: add a second "
                    "predicate, for example is_disposable_email alongside the "
                    "card_funding test, or delete the rule outright")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-radar-review-queue.mjs",
"js": '''/**
 * Report Stripe Radar reviews left open while the funds behind them are at risk.
 *
 * Read only. Paginated GETs and nothing else: give this a RESTRICTED key with
 * read access to Reviews and Charges. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const STALE_DAYS = 3;  // past this the queue is a backlog, not a queue
export const LAPSE_DAYS = 7;  // an uncaptured authorization is released at this age
const MIN_CLOSED = 20;
const OVERBROAD = 0.95;
const WIDE = 0.8;

/**
 * Classify one open review. Pure, so both deadlines can be tested offline.
 * `captured` is the charge's captured flag, or null when it could not be read.
 */
export function verdict(ageDays, captured) {
  if (ageDays < STALE_DAYS) {
    return ['open',
      `open for ${ageDays.toFixed(1)} day(s), still inside the window Stripe asks you to work`];
  }
  if (captured === false && ageDays >= LAPSE_DAYS) {
    return ['lapsed',
      `open for ${ageDays.toFixed(1)} day(s) on an uncaptured authorization: the hold ` +
      `was released at ${LAPSE_DAYS} days and approving it now captures nothing`];
  }
  if (captured === false) {
    return ['expiring',
      `open for ${ageDays.toFixed(1)} day(s) on an uncaptured authorization, released ` +
      `in ${(LAPSE_DAYS - ageDays).toFixed(1)} day(s)`];
  }
  if (ageDays >= LAPSE_DAYS) {
    return ['critical',
      `open for ${ageDays.toFixed(1)} day(s) on a captured charge: the money is with ` +
      'you and the dispute window is already running'];
  }
  return ['stale', `open for ${ageDays.toFixed(1)} day(s) on a captured charge`];
}

/** Judge the review rule from how its reviews were closed. Pure. */
export function ruleHealth(approved, closed) {
  if (closed < MIN_CLOSED) {
    return ['insufficient', `${closed} closed review(s) is too few to judge the rule`];
  }
  const rate = approved / closed;
  const pct = Math.round(rate * 100);
  if (rate >= OVERBROAD) {
    return ['overbroad',
      `${pct}% of closed reviews were approved: the rule flags traffic you always ` +
      'accept and has never changed an outcome'];
  }
  if (rate >= WIDE) {
    return ['wide', `${pct}% approved: add a second predicate before staffing this queue`];
  }
  return ['earning', `${pct}% approved: the rule is catching real fraud`];
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

async function page(key, path, cap, params = {}) {
  const out = [];
  const q = { ...params, limit: 100 };
  for (;;) {
    const p = await get(key, path, q);
    const data = p.data ?? [];
    out.push(...data);
    if (data.length === 0 || !p.has_more || out.length >= cap) break;
    q.starting_after = data[data.length - 1].id;
  }
  return out;
}

async function capturedFlag(key, chargeId, cache) {
  if (!chargeId) return null;
  if (!(chargeId in cache)) {
    try {
      cache[chargeId] = (await get(key, `/charges/${chargeId}`)).captured ?? null;
    } catch {
      cache[chargeId] = null;
    }
  }
  return cache[chargeId];
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 90);
  const now = Date.now() / 1000;
  const since = now - days * 86400;
  const reviews = await page(key, '/reviews', 2000);

  const cache = {};
  const byReason = {};
  let approved = 0;
  let closed = 0;
  let flagged = 0;

  for (const rev of reviews) {
    const created = rev.created ?? now;
    if (created >= since && rev.closed_reason) {
      closed += 1;
      if (rev.closed_reason === 'approved') approved += 1;
    }
    if (!rev.open) continue;
    const reason = rev.opened_reason ?? 'unknown';
    byReason[reason] = (byReason[reason] ?? 0) + 1;
    const age = (now - created) / 86400;
    const [state, detail] = verdict(age, await capturedFlag(key, rev.charge, cache));
    if (state === 'open') {
      console.log(`${state.padEnd(9)} ${rev.id}  ${detail}`);
      continue;
    }
    flagged += 1;
    console.warn(`${state.padEnd(9)} ${rev.id}  ${detail}`);
    console.warn(`    opened by ${reason}, charge ${rev.charge}`);
  }

  for (const [reason, n] of Object.entries(byReason).sort()) {
    console.log(`${n} open review(s) opened by ${reason}`);
  }
  const [health, detail] = ruleHealth(approved, closed);
  console.log(`${health.padEnd(12)} ${detail}`);

  if (!flagged && health !== 'overbroad' && health !== 'wide') {
    console.log(`0 open review(s) past ${STALE_DAYS} days`);
    return;
  }
  if (flagged) {
    console.warn('  work the queue: Dashboard, Radar, Reviews, then Approve, Refund, ' +
                 'or Refund and report fraud on each one');
    console.warn('  alert instead of polling: subscribe an endpoint to review.opened');
  }
  if (health === 'overbroad' || health === 'wide') {
    console.warn('  narrow the rule in Dashboard, Radar, Rules: add a second predicate, ' +
                 'for example is_disposable_email alongside the card_funding test, or ' +
                 'delete the rule outright');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are about the two deadlines and the one ratio. Day three is where a queue becomes a backlog and day seven is where an uncaptured authorization stops existing, so a classifier that is a day out on either turns a warning into a post-mortem. The approval-rate tests exist because 95% and 80% are the numbers that decide whether the answer is to hire someone or to delete a rule.",
"test_py_file": "test_stripe_radar_review_queue.py",
"test_py": '''from stripe_radar_review_queue import rule_health, verdict


def test_fresh_review_is_just_open():
    state, detail = verdict(1.0, True)
    assert state == "open"
    assert "still inside the window" in detail


def test_three_days_is_the_stale_boundary():
    # Exactly three must already flag. A check that waits until day four has
    # spent nearly half the capture window before saying anything.
    assert verdict(2.9, True)[0] == "open"
    assert verdict(3.0, True)[0] == "stale"


def test_uncaptured_hold_expires_at_seven_days():
    state, detail = verdict(6.9, False)
    assert state == "expiring"
    assert "0.1 day(s)" in detail
    assert verdict(7.0, False)[0] == "lapsed"


def test_captured_charge_past_seven_days_is_critical():
    state, detail = verdict(9.0, True)
    assert state == "critical"
    assert "dispute window" in detail


def test_approval_rate_needs_a_sample_before_it_judges_the_rule():
    assert rule_health(19, 19)[0] == "insufficient"
    assert rule_health(20, 20)[0] == "overbroad"
    assert rule_health(16, 20)[0] == "wide"
    assert rule_health(8, 20)[0] == "earning"
''',
"test_js_file": "stripe-radar-review-queue.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ruleHealth, verdict } from './stripe-radar-review-queue.mjs';

test('fresh review is just open', () => {
  const [state, detail] = verdict(1.0, true);
  assert.equal(state, 'open');
  assert.ok(detail.includes('still inside the window'));
});

test('three days is the stale boundary', () => {
  assert.equal(verdict(2.9, true)[0], 'open');
  assert.equal(verdict(3.0, true)[0], 'stale');
});

test('uncaptured hold expires at seven days', () => {
  const [state, detail] = verdict(6.9, false);
  assert.equal(state, 'expiring');
  assert.ok(detail.includes('0.1 day(s)'));
  assert.equal(verdict(7.0, false)[0], 'lapsed');
});

test('captured charge past seven days is critical', () => {
  const [state, detail] = verdict(9.0, true);
  assert.equal(state, 'critical');
  assert.ok(detail.includes('dispute window'));
});

test('approval rate needs a sample before it judges the rule', () => {
  assert.equal(ruleHealth(19, 19)[0], 'insufficient');
  assert.equal(ruleHealth(20, 20)[0], 'overbroad');
  assert.equal(ruleHealth(16, 20)[0], 'wide');
  assert.equal(ruleHealth(8, 20)[0], 'earning');
});
''',
"faq": [
 ("Does a review hold the payment while it is open?",
  "Not on a normal automatic-capture integration. The charge has already been made and the goods can already ship; open just means Stripe is waiting for your judgement so it can learn from it and so you can refund quickly if the answer is fraud. On separate authorization and capture it genuinely blocks, because the capture is the thing you have not done."),
 ("What actually happens at seven days?",
  "An uncaptured authorization is released. That is a card network limit, not a Stripe setting, and after it passes there is nothing to capture. The review can still be closed, but closing it recovers no money. This is why the script reads captured on the charge rather than judging the review by its age alone."),
 ("Can I filter GET /v1/reviews to only the open ones?",
  "Filter client-side on the open field. Pulling everything is what makes the second half of this check possible anyway: the closed reviews and their closed_reason values are the only evidence you have about whether the rule filling the queue is worth keeping."),
 ("An approval rate near 100% means the rule works, surely?",
  "It means the rule has never changed an outcome. Every payment it flagged, you accepted. That is a rule generating work and latency and buying nothing. Narrow it with a second predicate so it flags a smaller, genuinely ambiguous slice, or delete it and take the risk knowingly."),
 ("How do I stop polling for this?",
  "Subscribe an endpoint to review.opened and route it somewhere a person reads. The script is still worth running daily, because a notification tells you a review arrived and only the queue tells you one is about to lapse."),
],
"related": [
 ("/stripe/radar-blocked-payments-ignored/", "Radar blocks payments and nobody reads the block reasons"),
 ("/stripe/highest-risk-charges-succeeded/", "Highest-risk charges succeed instead of being blocked"),
 ("/stripe/abandoned-requires-action-intents/", "requires_action intents pile up at the 3DS step"),
],
"citations": [CITE_REVIEW_OBJ, CITE_RADAR_REVIEWS, CITE_RADAR_RULES, CITE_HOLD],
},

{
"slug": "highest-risk-charges-succeeded",
"title": "Highest-risk charges succeed instead of being blocked",
"description": "An allow rule overrides Stripe's own defaults. The built-in highest-risk block rule looks enabled and quietly does nothing at all.",
"h1": "highest-risk charges succeed instead of being blocked",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe radar allow rule override", "outcome risk_level highest",
             "stripe highest risk charge succeeded", "stripe allow rule risk_level",
             "stripe radar default rules"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Radar page says the highest-risk block rule is on. It has been on since the account was created, nobody has touched it, and it is doing nothing. Somewhere below it is an allow rule that somebody added to stop blocking a partner's traffic, and an allow rule wins against everything, including Stripe's own defaults.",
"short_answer": """<p>Paginate <code>GET /v1/charges</code> and flag anything where <code>outcome.risk_level == "highest"</code> and <code>status == "succeeded"</code> and <code>captured == true</code>. Those charges should not exist on an account with the default block rule working.</p>
<p>Read <code>outcome.rule</code> on each one. A populated rule with <code>action == "allow"</code> names the override and its <code>predicate</code> tells you what somebody widened. Then confirm the leak is real by matching those charge ids against <code>GET /v1/radar/early_fraud_warnings</code> and <code>GET /v1/disputes</code>.</p>""",
"problem": """<p>This is the failure mode of a control that reports its own state honestly and still lies to you. The block rule is enabled. The Dashboard shows it as enabled. Nothing anywhere says "overridden". The only place the truth appears is on the individual charges, in a field most integrations never read, and only after the payment has already gone through.</p>
<p>The allow rule usually starts reasonable. A partner in one country kept getting blocked, so somebody wrote <code>if :ip_country: = 'GB'</code> and the complaints stopped. What that rule actually says is: for every payment from that country, ignore every other rule, including the one Stripe wrote to stop the worst 0.1% of traffic. It is a hole with a country-sized edge, and it was opened deliberately for a good reason.</p>""",
"why": """<p><strong>Allow beats block, by design, everywhere.</strong> Stripe is explicit that allow rules override the Stripe default rules along with any other custom rules matching the same criteria. That is the correct semantics for an allow list &mdash; an exception has to be able to win &mdash; but it means the precedence is invisible in a list of rules that reads top to bottom like a policy document.</p>
<p><strong>An allow rule is written to solve a support ticket, not to set a fraud policy.</strong> The person writing it is trying to make one legitimate customer's payment work. The predicate is as wide as it needs to be to cover that customer and no wider in the author's mind, and it is usually a country, a BIN, or an email domain, all of which are trivial for an attacker to match.</p>
<p><strong>Nothing reports on it.</strong> There is no view that says how many highest-risk payments an allow rule let through last month. That number has to be computed from the charges, and until somebody computes it the rule looks like a small, targeted exception.</p>
<p><strong>The evidence arrives late and somewhere else.</strong> The consequence is early fraud warnings and fraudulent disputes weeks later, attributed to fraud in general rather than to one predicate. Matching those back to the flagged charges is the step that turns an argument about risk appetite into an argument about a specific line of configuration.</p>""",
"steps": [
 {"h": "Pull 90 days of charges and filter on outcome.risk_level",
  "body": """<p>Ninety days is deliberate: early fraud warnings and disputes lag the payment by weeks, and a 30-day window shows you the leak without any of the damage. Only <code>highest</code> matters here. <code>elevated</code> is a different note and a different rule.</p>"""},
 {"h": "Separate the ones that never captured",
  "body": """<p>A highest-risk charge with <code>captured == false</code> is a hold you can still cancel, and that is a different instruction to a human than one where the money already moved. It is also on a clock, so it goes at the top of the output.</p>"""},
 {"h": "Read outcome.rule to name the override",
  "body": """<p><code>action == "allow"</code> with a predicate is the answer written out. If <code>outcome.rule</code> is empty on a captured highest-risk charge, the built-in block rule itself is disabled, which is a different repair and a shorter conversation.</p>"""},
 {"h": "Watch for not_assessed",
  "body": """<p>If <code>outcome.risk_level</code> is <code>not_assessed</code> across a lot of charges, Radar never scored them, because no Radar session was collected from the client. No rule of any kind can fire on a charge Radar did not score, so fix that before tuning anything.</p>"""},
 {"h": "Quantify with early fraud warnings and disputes, then guard the allow rule",
  "body": """<p>Match the flagged charge ids against <code>GET /v1/radar/early_fraud_warnings</code> and <code>GET /v1/disputes</code>. A materially higher incidence than your baseline is the proof. The repair is Stripe's own recommendation: add <code>and :risk_level: != 'highest'</code> to every allow rule, so an exception can still let a partner through without also disarming the default.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the guard was added. Highest-risk charges should stop succeeding, and the ones that do should be named by a rule you recognise.</p>
<pre><code class="language-bash">python3 stripe_highest_risk_succeeded.py --days 30
# 2,918 charge(s): 0 highest-risk captured, 4 stopped</code></pre>""",
"code_intro": "One paginated GET over Charges plus two small lookups for the fraud evidence, and no writes &mdash; read access to Charges, Disputes and Radar is enough. The classifier is pure and takes the four fields that decide the verdict, because the difference between an allow rule winning, a default rule being switched off, and Radar never scoring the charge at all is the whole point of the check.",
"py_file": "stripe_highest_risk_succeeded.py",
"py": '''"""Report Stripe charges Radar scored as highest risk that succeeded anyway.

Read only. Paginated GETs and nothing else: give this a RESTRICTED key with read
access to Charges, Disputes and Radar. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_highest_risk_succeeded")

API = "https://api.stripe.com/v1"

LEAKING = ("allowed", "leaked", "uncaptured")


def verdict(risk_level, status, captured, rule):
    """Classify one charge. Pure, so the precedence rules can be tested offline.

    `rule` is the charge's outcome.rule: None, a rule id string, or the expanded
    object carrying `action` and `predicate`. Returns (state, detail).
    """
    if risk_level in (None, "not_assessed"):
        return ("not_assessed",
                "Radar never scored this charge: no Radar session reached the API")
    if risk_level != "highest":
        return ("baseline", "risk_level %s, outside the scope of this check" % risk_level)
    if status != "succeeded":
        return ("stopped", "highest risk and status %s: the block held" % status)
    if not captured:
        return ("uncaptured",
                "highest risk, authorized but not captured: cancel the payment "
                "intent before the hold is captured or expires")
    action = rule.get("action") if isinstance(rule, dict) else None
    if action == "allow":
        predicate = rule.get("predicate") or rule.get("id") or "unnamed"
        return ("allowed",
                "highest risk and captured because an allow rule matched first: %s"
                % predicate)
    return ("leaked",
            "highest risk and captured with no rule named: the built-in highest "
            "risk block rule is not in force on this account")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page(session, path, cap, **params):
    out = []
    params = dict(params)
    params["limit"] = 100
    while True:
        p = get(session, path, **params)
        data = p.get("data", [])
        out.extend(data)
        if not data or not p.get("has_more") or len(out) >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def fraud_charge_ids(session, cap):
    """Charge ids carrying an early fraud warning or a dispute."""
    ids = set()
    for efw in page(session, "/radar/early_fraud_warnings", cap):
        if efw.get("charge"):
            ids.add(efw["charge"] if isinstance(efw["charge"], str)
                    else efw["charge"].get("id"))
    for dispute in page(session, "/disputes", cap):
        if dispute.get("charge"):
            ids.add(dispute["charge"] if isinstance(dispute["charge"], str)
                    else dispute["charge"].get("id"))
    return {i for i in ids if i}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to read charges")
    ap.add_argument("--max-charges", type=int, default=5000,
                    help="stop paginating after this many charges")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time() - args.days * 86400)
    charges = page(s, "/charges", args.max_charges, **{"created[gte]": since})

    leaking = []
    counts = {}
    for ch in charges:
        outcome = ch.get("outcome") or {}
        state, detail = verdict(outcome.get("risk_level"), ch.get("status"),
                                ch.get("captured"), outcome.get("rule"))
        counts[state] = counts.get(state, 0) + 1
        if state in LEAKING:
            leaking.append((ch, state, detail))

    log.info("%d charge(s): %d highest-risk captured, %d stopped",
             len(charges), counts.get("allowed", 0) + counts.get("leaked", 0),
             counts.get("stopped", 0))
    if counts.get("not_assessed"):
        log.warning("%d charge(s) were never scored by Radar. Mount Stripe.js on the "
                    "payment page, or pass radar_options[session] on server-side "
                    "confirms, before tuning any rule.",
                    counts["not_assessed"])

    if not leaking:
        return 1 if counts.get("not_assessed") else 0

    fraud = fraud_charge_ids(s, 1000)
    hits = 0
    for ch, state, detail in leaking:
        marker = ""
        if ch.get("id") in fraud:
            hits += 1
            marker = "  [early fraud warning or dispute on this charge]"
        log.warning("%-12s %s %s%s", state, ch.get("id"), detail, marker)

    log.warning("  %d of %d leaked charge(s) already carry fraud evidence",
                hits, len(leaking))
    log.warning("  guard every allow rule in Dashboard, Radar, Rules by appending "
                "and :risk_level: != 'highest' to its predicate")
    log.warning("  then confirm the built-in rule if :risk_level: = 'highest' is "
                "still enabled")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-highest-risk-succeeded.mjs",
"js": '''/**
 * Report Stripe charges Radar scored as highest risk that succeeded anyway.
 *
 * Read only. Paginated GETs and nothing else: give this a RESTRICTED key with
 * read access to Charges, Disputes and Radar. The repair is printed, never run.
 */
const API = 'https://api.stripe.com/v1';

const LEAKING = new Set(['allowed', 'leaked', 'uncaptured']);

/**
 * Classify one charge. Pure, so the precedence rules can be tested offline.
 * `rule` is outcome.rule: null, a rule id, or the expanded rule object.
 */
export function verdict(riskLevel, status, captured, rule) {
  if (riskLevel === null || riskLevel === undefined || riskLevel === 'not_assessed') {
    return ['not_assessed',
      'Radar never scored this charge: no Radar session reached the API'];
  }
  if (riskLevel !== 'highest') {
    return ['baseline', `risk_level ${riskLevel}, outside the scope of this check`];
  }
  if (status !== 'succeeded') {
    return ['stopped', `highest risk and status ${status}: the block held`];
  }
  if (!captured) {
    return ['uncaptured',
      'highest risk, authorized but not captured: cancel the payment intent ' +
      'before the hold is captured or expires'];
  }
  const action = rule && typeof rule === 'object' ? rule.action : null;
  if (action === 'allow') {
    const predicate = (rule.predicate ?? rule.id) || 'unnamed';
    return ['allowed',
      `highest risk and captured because an allow rule matched first: ${predicate}`];
  }
  return ['leaked',
    'highest risk and captured with no rule named: the built-in highest risk ' +
    'block rule is not in force on this account'];
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

async function page(key, path, cap, params = {}) {
  const out = [];
  const q = { ...params, limit: 100 };
  for (;;) {
    const p = await get(key, path, q);
    const data = p.data ?? [];
    out.push(...data);
    if (data.length === 0 || !p.has_more || out.length >= cap) break;
    q.starting_after = data[data.length - 1].id;
  }
  return out;
}

async function fraudChargeIds(key, cap) {
  const ids = new Set();
  const idOf = (c) => (typeof c === 'string' ? c : c?.id);
  for (const efw of await page(key, '/radar/early_fraud_warnings', cap)) {
    if (efw.charge) ids.add(idOf(efw.charge));
  }
  for (const dispute of await page(key, '/disputes', cap)) {
    if (dispute.charge) ids.add(idOf(dispute.charge));
  }
  ids.delete(undefined);
  return ids;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 90);
  const since = Math.floor(Date.now() / 1000 - days * 86400);
  const charges = await page(key, '/charges', 5000, { 'created[gte]': since });

  const leaking = [];
  const counts = {};
  for (const ch of charges) {
    const outcome = ch.outcome ?? {};
    const [state, detail] = verdict(outcome.risk_level, ch.status, ch.captured,
                                    outcome.rule);
    counts[state] = (counts[state] ?? 0) + 1;
    if (LEAKING.has(state)) leaking.push([ch, state, detail]);
  }

  const captured = (counts.allowed ?? 0) + (counts.leaked ?? 0);
  console.log(`${charges.length} charge(s): ${captured} highest-risk captured, ` +
              `${counts.stopped ?? 0} stopped`);
  if (counts.not_assessed) {
    console.warn(`${counts.not_assessed} charge(s) were never scored by Radar. Mount ` +
                 'Stripe.js on the payment page, or pass radar_options[session] on ' +
                 'server-side confirms, before tuning any rule.');
  }

  if (leaking.length === 0) {
    if (counts.not_assessed) process.exitCode = 1;
    return;
  }

  const fraud = await fraudChargeIds(key, 1000);
  let hits = 0;
  for (const [ch, state, detail] of leaking) {
    let marker = '';
    if (fraud.has(ch.id)) {
      hits += 1;
      marker = '  [early fraud warning or dispute on this charge]';
    }
    console.warn(`${state.padEnd(12)} ${ch.id} ${detail}${marker}`);
  }

  console.warn(`  ${hits} of ${leaking.length} leaked charge(s) already carry fraud evidence`);
  console.warn("  guard every allow rule in Dashboard, Radar, Rules by appending " +
               "and :risk_level: != 'highest' to its predicate");
  console.warn("  then confirm the built-in rule if :risk_level: = 'highest' is still enabled");
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test here is about telling apart four situations that look identical in a charge list: a block that worked, an allow rule that overrode it, a default rule that is simply switched off, and a charge Radar never scored. Those four have four different repairs, and getting them confused sends somebody to edit a rule that was never involved.",
"test_py_file": "test_stripe_highest_risk_succeeded.py",
"test_py": '''from stripe_highest_risk_succeeded import verdict


def test_normal_risk_is_out_of_scope():
    assert verdict("normal", "succeeded", True, None)[0] == "baseline"


def test_unscored_charges_are_called_out_before_anything_else():
    # A charge Radar never scored cannot be blocked by any rule, so tuning
    # rules on an account full of these is wasted work.
    assert verdict("not_assessed", "succeeded", True, None)[0] == "not_assessed"
    assert verdict(None, "succeeded", True, None)[0] == "not_assessed"


def test_highest_risk_that_did_not_succeed_is_the_block_working():
    state, detail = verdict("highest", "failed", False, None)
    assert state == "stopped"
    assert "the block held" in detail


def test_an_allow_rule_is_named_when_it_overrode_the_default():
    rule = {"id": "rule_123", "action": "allow", "predicate": ":ip_country: = 'GB'"}
    state, detail = verdict("highest", "succeeded", True, rule)
    assert state == "allowed"
    assert ":ip_country: = 'GB'" in detail


def test_captured_with_no_rule_means_the_default_is_off():
    assert verdict("highest", "succeeded", True, None)[0] == "leaked"
    # A rule id string with no action is not evidence of an allow rule.
    assert verdict("highest", "succeeded", True, "rule_123")[0] == "leaked"
    # Still holdable, so it is a different instruction to a human.
    assert verdict("highest", "succeeded", False, None)[0] == "uncaptured"
''',
"test_js_file": "stripe-highest-risk-succeeded.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-highest-risk-succeeded.mjs';

test('normal risk is out of scope', () => {
  assert.equal(verdict('normal', 'succeeded', true, null)[0], 'baseline');
});

test('unscored charges are called out before anything else', () => {
  assert.equal(verdict('not_assessed', 'succeeded', true, null)[0], 'not_assessed');
  assert.equal(verdict(null, 'succeeded', true, null)[0], 'not_assessed');
});

test('highest risk that did not succeed is the block working', () => {
  const [state, detail] = verdict('highest', 'failed', false, null);
  assert.equal(state, 'stopped');
  assert.ok(detail.includes('the block held'));
});

test('an allow rule is named when it overrode the default', () => {
  const rule = { id: 'rule_123', action: 'allow', predicate: ":ip_country: = 'GB'" };
  const [state, detail] = verdict('highest', 'succeeded', true, rule);
  assert.equal(state, 'allowed');
  assert.ok(detail.includes(":ip_country: = 'GB'"));
});

test('captured with no rule means the default is off', () => {
  assert.equal(verdict('highest', 'succeeded', true, null)[0], 'leaked');
  assert.equal(verdict('highest', 'succeeded', true, 'rule_123')[0], 'leaked');
  assert.equal(verdict('highest', 'succeeded', false, null)[0], 'uncaptured');
});
''',
"faq": [
 ("Why does an allow rule beat Stripe's own block rule?",
  "Because that is what an allow list is for. Stripe states that allow rules override the Stripe default rules along with any other custom rules matching the same criteria, so an exception can always win. The problem is not the precedence, it is that the precedence is invisible when you read the rules as a list."),
 ("Is outcome.rule always populated on a blocked or allowed charge?",
  "It is populated when one of your own rules decided the outcome. A block from Stripe's own model shows outcome.reason of highest_risk_level with no custom rule behind it. On a captured highest-risk charge an empty outcome.rule therefore points at the built-in block rule being disabled rather than overridden."),
 ("What does risk_level not_assessed mean?",
  "Radar never scored the charge, almost always because no Radar session was created on the client. Mount Stripe.js on the payment page, or pass radar_options[session] explicitly on server-side confirms. No rule can fire on a charge that was never scored, so fix this before tuning thresholds."),
 ("How do I keep the exception and close the hole?",
  "Append and :risk_level: != 'highest' to the allow rule's predicate. That is Stripe's own recommended guard. The partner whose payments kept failing still gets through, and the worst slice of traffic still meets the default block."),
 ("Why cross-reference early fraud warnings as well as disputes?",
  "An early fraud warning arrives from the network before the cardholder files anything, so it shows up weeks earlier than the dispute and often on payments that are never disputed at all. Using both gives you the leak's real cost while the dispute data is still incomplete."),
],
"related": [
 ("/stripe/radar-blocked-payments-ignored/", "Radar blocks payments and nobody reads the block reasons"),
 ("/stripe/radar-reviews-open-stale/", "Radar reviews sit open while funds stay at risk"),
 ("/shopify/high-risk-orders-unactioned/", "High-risk orders nobody actions"),
],
"citations": [CITE_RADAR_RULES, CITE_CHARGE_OBJ, CITE_DECLINES, CITE_EFW],
},

{
"slug": "avs-cvc-fail-captured",
"title": "Charges captured after AVS and CVC verification failed",
"description": "The issuer approved a payment whose postal code and security code did not match. Stripe records the failure and, by default, does nothing with it.",
"h1": "charges captured after AVS and CVC verification failed",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe avs failure", "stripe cvc_check fail",
             "address_postal_code_check fail", "decline_on avs_failure",
             "stripe verification failed captured"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The dispute says the cardholder never made the purchase, and when you open the charge to build a case you find the billing postal code did not match the issuer's records and the security code was wrong. Stripe recorded both facts at the time. Nothing was configured to act on them, so the payment was captured and the goods shipped.",
"short_answer": """<p>Start at the account: <code>GET /v1/account</code> and read <code>settings.card_payments.decline_on.avs_failure</code> and <code>.cvc_failure</code>. Both default to <code>false</code>, which means Stripe records a failed check and captures the payment anyway.</p>
<p>Then paginate <code>GET /v1/charges</code> and look at <code>payment_method_details.card.checks</code>. Flag any captured, succeeded charge where <code>cvc_check</code>, <code>address_postal_code_check</code> or <code>address_line1_check</code> is <code>"fail"</code>. Count the ones where all three are <code>null</code> separately: that is data you never collected, which is the deeper problem.</p>""",
"problem": """<p>An issuer can approve a payment that fails CVC or AVS. It weighs a great many other signals and the mismatch is only one of them, so an approval is not a statement that the details were correct. Stripe faithfully records what the issuer said about each check and, unless you told it otherwise, treats the approval as the answer.</p>
<p>What that costs you shows up at dispute time. A fraudulent-charge dispute is defended with evidence that the real cardholder made the purchase, and the strongest evidence available is that the billing details matched. When the record shows they demonstrably did not, there is no case to make. Stripe's own guidance on this is blunt: if verification fails, consider rejecting the payment, because it might indicate fraud.</p>""",
"why": """<p><strong>The defaults are off, and off is invisible.</strong> <code>decline_on.avs_failure</code> and <code>decline_on.cvc_failure</code> are both <code>false</code> on a new account. Nothing prompts you during onboarding, nothing warns you later, and the checks still appear on every charge, which makes it look like something is consuming them.</p>
<p><strong>Turning them on bluntly breaks wallets.</strong> Apple Pay and Google Pay often do not supply a postal code or a CVC at all, so a hard decline on failure can also reject payments that were never going to have the data. That is why Stripe ships risk-scored variants of both rules, and why the blunt account settings are a worse first move than the Radar rules.</p>
<p><strong>A null check is not a passing check.</strong> The two are easy to conflate in a query and they mean opposite things. <code>null</code> across all three fields means nothing was ever collected: the payment form never asked for a postal code, so there was no AVS request to fail. That is a form problem, and no rule will fix it.</p>
<p><strong>The failure is only expensive in aggregate.</strong> One captured payment with a failed AVS check is not evidence of anything. A steady few percent of them, disproportionately represented among your disputes, is a control you never switched on, and only counting shows you which one it is.</p>""",
"steps": [
 {"h": "Read the account settings first",
  "body": """<p><code>GET /v1/account</code>, then <code>settings.card_payments.decline_on</code>. This one object tells you whether anything at all is acting on verification failures, and it costs a single request. If both flags are <code>false</code>, everything you find in the charges was inevitable.</p>"""},
 {"h": "Page 90 days of charges and read the checks object",
  "body": """<p><code>payment_method_details.card.checks</code> carries three fields: <code>cvc_check</code>, <code>address_postal_code_check</code> and <code>address_line1_check</code>. The values you care about are <code>"fail"</code>, and separately <code>null</code>.</p>"""},
 {"h": "Flag failures that were captured, and hold the ones that were not",
  "body": """<p>A failed check on a charge with <code>captured == false</code> is still a decision you can make. A failed check on a captured charge is a refund decision, and one you should probably make quickly rather than after a dispute makes it for you.</p>"""},
 {"h": "Count uncollected checks as their own category",
  "body": """<p>All three fields <code>null</code> on a card charge means the data never reached the issuer. Force collection at the source: set <code>billing_address_collection</code> to <code>required</code> on Checkout Sessions, or collect the postal code in the Payment Element. Until you do, an AVS rule has nothing to evaluate.</p>"""},
 {"h": "Enable the risk-scored Radar rules rather than the blunt account flags",
  "body": """<p>In Dashboard, Radar, then Rules, switch on the built-ins for postal code verification failing based on risk score, and CVC verification failing based on risk score. The scoring is what stops them rejecting wallet payments that never supplied the data in the first place.</p>"""},
],
"verify": """<p>Re-run over a window that starts after the rules were enabled. Captured failures should go to zero, and the uncollected count should fall as the form change reaches customers.</p>
<pre><code class="language-bash">python3 stripe_avs_cvc_checks.py --days 30
# decline_on: avs=True cvc=True
# 1,860 card charge(s): 0 captured on a failed check, 31 never collected</code></pre>""",
"code_intro": "One account read and one paginated GET over Charges, no writes &mdash; read access to Account and Charges is enough. The classifier is pure and takes the checks object, the capture flag and the account's <code>decline_on</code> settings together, because whether a captured failure is a surprise or a configured choice depends on all three.",
"py_file": "stripe_avs_cvc_checks.py",
"py": '''"""Report Stripe charges captured after an AVS or CVC check came back failed.

Read only. One account read and one paginated GET: give this a RESTRICTED key
with read access to Account and Charges. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_avs_cvc_checks")

API = "https://api.stripe.com/v1"

CHECK_FIELDS = ("cvc_check", "address_postal_code_check", "address_line1_check")
INCONCLUSIVE = (None, "unavailable", "unchecked")


def _covered(field, decline_on):
    """True when the account is configured to decline on this check failing."""
    settings = decline_on or {}
    if field == "cvc_check":
        return bool(settings.get("cvc_failure"))
    return bool(settings.get("avs_failure"))


def verdict(checks, captured, decline_on):
    """Classify one charge's verification result. Pure, so it tests offline.

    `checks` is payment_method_details.card.checks, or None when the charge was
    not a card payment. `decline_on` is settings.card_payments.decline_on from
    the account. Returns (state, detail).
    """
    if checks is None:
        return ("not_card", "no card checks on this charge")
    values = {f: checks.get(f) for f in CHECK_FIELDS}
    if all(v is None for v in values.values()):
        return ("uncollected",
                "no AVS or CVC result at all: the details were never collected, so "
                "there was nothing for the issuer to verify")
    failed = sorted(f for f, v in values.items() if v == "fail")
    if failed and captured:
        uncovered = [f for f in failed if not _covered(f, decline_on)]
        if uncovered:
            return ("captured_on_fail",
                    "%s failed and the charge was captured: decline_on is not set "
                    "for %s" % (", ".join(failed), ", ".join(uncovered)))
        return ("captured_despite_setting",
                "%s failed and the charge was captured even though decline_on "
                "covers it: check the Radar rules are enabled" % ", ".join(failed))
    if failed:
        return ("held",
                "%s failed and the charge is not captured: this is still a decision "
                "you can make" % ", ".join(failed))
    if any(values[f] in INCONCLUSIVE for f in CHECK_FIELDS):
        missing = sorted(f for f in CHECK_FIELDS if values[f] in INCONCLUSIVE)
        return ("unverified", "no usable result for %s" % ", ".join(missing))
    return ("verified", "every collected check passed")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page(session, path, cap, **params):
    out = []
    params = dict(params)
    params["limit"] = 100
    while True:
        p = get(session, path, **params)
        data = p.get("data", [])
        out.extend(data)
        if not data or not p.get("has_more") or len(out) >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def card_checks(charge):
    """payment_method_details.card.checks, or None when this is not a card."""
    details = charge.get("payment_method_details") or {}
    if details.get("type") != "card":
        return None
    return (details.get("card") or {}).get("checks")


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

    account = get(s, "/account")
    settings = account.get("settings") or {}
    decline_on = (settings.get("card_payments") or {}).get("decline_on") or {}
    log.info("decline_on: avs=%s cvc=%s",
             bool(decline_on.get("avs_failure")), bool(decline_on.get("cvc_failure")))

    since = int(time.time() - args.days * 86400)
    charges = page(s, "/charges", args.max_charges, **{"created[gte]": since})

    counts = {}
    flagged = []
    cards = 0
    for ch in charges:
        checks = card_checks(ch)
        if checks is None and (ch.get("payment_method_details") or {}).get("type") != "card":
            continue
        cards += 1
        state, detail = verdict(checks, ch.get("captured"), decline_on)
        counts[state] = counts.get(state, 0) + 1
        if state in ("captured_on_fail", "captured_despite_setting", "held"):
            flagged.append((ch, state, detail))

    log.info("%d card charge(s): %d captured on a failed check, %d never collected",
             cards,
             counts.get("captured_on_fail", 0) + counts.get("captured_despite_setting", 0),
             counts.get("uncollected", 0))

    for ch, state, detail in flagged:
        log.warning("%-24s %s %s", state, ch.get("id"), detail)

    if not flagged and not counts.get("uncollected"):
        return 0

    if flagged:
        log.warning("  enable the risk-scored built-ins in Dashboard, Radar, Rules: "
                    "postal code verification fails based on risk score, and CVC "
                    "verification fails based on risk score")
    if counts.get("uncollected"):
        log.warning("  %d charge(s) had no checks at all. Collect the details: set "
                    "billing_address_collection to required on Checkout Sessions, or "
                    "collect the postal code in the Payment Element.",
                    counts["uncollected"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-avs-cvc-checks.mjs",
"js": '''/**
 * Report Stripe charges captured after an AVS or CVC check came back failed.
 *
 * Read only. One account read and one paginated GET: give this a RESTRICTED key
 * with read access to Account and Charges. The repair is printed, never run.
 */
const API = 'https://api.stripe.com/v1';

export const CHECK_FIELDS = ['cvc_check', 'address_postal_code_check',
                             'address_line1_check'];
const INCONCLUSIVE = new Set([null, undefined, 'unavailable', 'unchecked']);

/** True when the account is configured to decline on this check failing. */
function covered(field, declineOn) {
  const s = declineOn ?? {};
  return field === 'cvc_check' ? Boolean(s.cvc_failure) : Boolean(s.avs_failure);
}

/**
 * Classify one charge's verification result. Pure, so it tests offline.
 * `checks` is payment_method_details.card.checks, or null for a non-card charge.
 */
export function verdict(checks, captured, declineOn) {
  if (checks === null || checks === undefined) {
    return ['not_card', 'no card checks on this charge'];
  }
  const values = Object.fromEntries(CHECK_FIELDS.map((f) => [f, checks[f] ?? null]));
  if (CHECK_FIELDS.every((f) => values[f] === null)) {
    return ['uncollected',
      'no AVS or CVC result at all: the details were never collected, so there ' +
      'was nothing for the issuer to verify'];
  }
  const failed = CHECK_FIELDS.filter((f) => values[f] === 'fail').sort();
  if (failed.length && captured) {
    const uncovered = failed.filter((f) => !covered(f, declineOn));
    if (uncovered.length) {
      return ['captured_on_fail',
        `${failed.join(', ')} failed and the charge was captured: decline_on is ` +
        `not set for ${uncovered.join(', ')}`];
    }
    return ['captured_despite_setting',
      `${failed.join(', ')} failed and the charge was captured even though ` +
      'decline_on covers it: check the Radar rules are enabled'];
  }
  if (failed.length) {
    return ['held',
      `${failed.join(', ')} failed and the charge is not captured: this is still ` +
      'a decision you can make'];
  }
  const missing = CHECK_FIELDS.filter((f) => INCONCLUSIVE.has(values[f])).sort();
  if (missing.length) {
    return ['unverified', `no usable result for ${missing.join(', ')}`];
  }
  return ['verified', 'every collected check passed'];
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

async function page(key, path, cap, params = {}) {
  const out = [];
  const q = { ...params, limit: 100 };
  for (;;) {
    const p = await get(key, path, q);
    const data = p.data ?? [];
    out.push(...data);
    if (data.length === 0 || !p.has_more || out.length >= cap) break;
    q.starting_after = data[data.length - 1].id;
  }
  return out;
}

function cardChecks(charge) {
  const details = charge.payment_method_details ?? {};
  if (details.type !== 'card') return undefined;
  return (details.card ?? {}).checks ?? null;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const account = await get(key, '/account');
  const declineOn = account.settings?.card_payments?.decline_on ?? {};
  console.log(`decline_on: avs=${Boolean(declineOn.avs_failure)} ` +
              `cvc=${Boolean(declineOn.cvc_failure)}`);

  const days = Number(process.env.DAYS ?? 90);
  const since = Math.floor(Date.now() / 1000 - days * 86400);
  const charges = await page(key, '/charges', 5000, { 'created[gte]': since });

  const counts = {};
  const flagged = [];
  let cards = 0;
  for (const ch of charges) {
    const checks = cardChecks(ch);
    if (checks === undefined) continue;
    cards += 1;
    const [state, detail] = verdict(checks, ch.captured, declineOn);
    counts[state] = (counts[state] ?? 0) + 1;
    if (state === 'captured_on_fail' || state === 'captured_despite_setting' ||
        state === 'held') {
      flagged.push([ch, state, detail]);
    }
  }

  const bad = (counts.captured_on_fail ?? 0) + (counts.captured_despite_setting ?? 0);
  console.log(`${cards} card charge(s): ${bad} captured on a failed check, ` +
              `${counts.uncollected ?? 0} never collected`);

  for (const [ch, state, detail] of flagged) {
    console.warn(`${state.padEnd(24)} ${ch.id} ${detail}`);
  }

  if (flagged.length === 0 && !counts.uncollected) return;

  if (flagged.length) {
    console.warn('  enable the risk-scored built-ins in Dashboard, Radar, Rules: ' +
                 'postal code verification fails based on risk score, and CVC ' +
                 'verification fails based on risk score');
  }
  if (counts.uncollected) {
    console.warn(`  ${counts.uncollected} charge(s) had no checks at all. Collect the ` +
                 'details: set billing_address_collection to required on Checkout ' +
                 'Sessions, or collect the postal code in the Payment Element.');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests exist mostly to keep <code>null</code> and <code>\"fail\"</code> apart. Those two values sit in the same field, mean opposite things, and have completely different repairs: one is a Radar rule you never enabled, the other is a checkout form that never asked for a postal code. A classifier that folds them together produces a report that sends you to the wrong page.",
"test_py_file": "test_stripe_avs_cvc_checks.py",
"test_py": '''from stripe_avs_cvc_checks import verdict

OFF = {"avs_failure": False, "cvc_failure": False}
ON = {"avs_failure": True, "cvc_failure": True}


def test_non_card_charges_are_out_of_scope():
    assert verdict(None, True, OFF)[0] == "not_card"


def test_all_null_checks_means_nothing_was_ever_collected():
    # Not the same as passing. There was no AVS request to fail, so no rule
    # would have helped: the checkout form is the thing to fix.
    state, detail = verdict({}, True, OFF)
    assert state == "uncollected"
    assert "never collected" in detail


def test_a_failed_check_on_a_captured_charge_names_the_missing_setting():
    checks = {"cvc_check": "pass", "address_postal_code_check": "fail",
              "address_line1_check": "pass"}
    state, detail = verdict(checks, True, OFF)
    assert state == "captured_on_fail"
    assert "address_postal_code_check" in detail


def test_a_failure_the_account_declines_on_is_a_different_problem():
    checks = {"cvc_check": "fail", "address_postal_code_check": "pass",
              "address_line1_check": "pass"}
    assert verdict(checks, True, ON)[0] == "captured_despite_setting"
    # Uncaptured is still a live decision, whatever the settings say.
    assert verdict(checks, False, OFF)[0] == "held"


def test_passing_and_inconclusive_checks_are_told_apart():
    passed = {"cvc_check": "pass", "address_postal_code_check": "pass",
              "address_line1_check": "pass"}
    assert verdict(passed, True, OFF)[0] == "verified"
    partial = dict(passed, address_line1_check="unavailable")
    assert verdict(partial, True, OFF)[0] == "unverified"
''',
"test_js_file": "stripe-avs-cvc-checks.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-avs-cvc-checks.mjs';

const OFF = { avs_failure: false, cvc_failure: false };
const ON = { avs_failure: true, cvc_failure: true };

test('non card charges are out of scope', () => {
  assert.equal(verdict(null, true, OFF)[0], 'not_card');
});

test('all null checks means nothing was ever collected', () => {
  const [state, detail] = verdict({}, true, OFF);
  assert.equal(state, 'uncollected');
  assert.ok(detail.includes('never collected'));
});

test('a failed check on a captured charge names the missing setting', () => {
  const checks = { cvc_check: 'pass', address_postal_code_check: 'fail',
                   address_line1_check: 'pass' };
  const [state, detail] = verdict(checks, true, OFF);
  assert.equal(state, 'captured_on_fail');
  assert.ok(detail.includes('address_postal_code_check'));
});

test('a failure the account declines on is a different problem', () => {
  const checks = { cvc_check: 'fail', address_postal_code_check: 'pass',
                   address_line1_check: 'pass' };
  assert.equal(verdict(checks, true, ON)[0], 'captured_despite_setting');
  assert.equal(verdict(checks, false, OFF)[0], 'held');
});

test('passing and inconclusive checks are told apart', () => {
  const passed = { cvc_check: 'pass', address_postal_code_check: 'pass',
                   address_line1_check: 'pass' };
  assert.equal(verdict(passed, true, OFF)[0], 'verified');
  assert.equal(verdict({ ...passed, address_line1_check: 'unavailable' }, true, OFF)[0],
               'unverified');
});
''',
"faq": [
 ("If the issuer approved it, why is a failed AVS check my problem?",
  "The issuer weighs many signals and can approve despite a mismatch; the approval is a lending decision, not a statement that the billing details were correct. The liability for a fraudulent card-not-present payment stays with you, and at dispute time the mismatch is the record you have to argue against."),
 ("Should I just set decline_on.avs_failure and cvc_failure to true?",
  "Those flags decline bluntly, on any failure, including wallet payments that never supplied a postal code or a CVC to begin with. Stripe's risk-scored Radar rules do the same job while taking the rest of the signal into account, which is why they are the better first move."),
 ("What is the difference between a null check and a failed one?",
  "A failure means the issuer compared the value you sent and it did not match. A null means you never sent one, so nothing was compared. The first is a rule you have not enabled; the second is a checkout form that does not ask for the data. Fixing the rule does nothing about the nulls."),
 ("How do I start collecting postal codes?",
  "On Checkout, set billing_address_collection to required when you create the session. On a custom flow, collect the postal code in the Payment Element so it is sent with the confirmation. Either way the AVS result appears on subsequent charges and the null count falls."),
 ("Does this script need write access to fix anything?",
  "No, and it deliberately cannot. It reads the account settings and the charges, prints which rules to enable and which charges to look at, and leaves every decision about refunding a captured payment to you."),
],
"related": [
 ("/stripe/highest-risk-charges-succeeded/", "Highest-risk charges succeed instead of being blocked"),
 ("/stripe/dispute-deadline-72h-no-evidence/", "A dispute deadline is 72 hours out with no evidence attached"),
 ("/stripe/missing-statement-descriptor/", "No statement descriptor, so customers dispute what they see"),
],
"citations": [CITE_ACCOUNT_OBJ, CITE_RADAR_RULES, CITE_PREVENTION, CITE_CHARGE_OBJ],
},

{
"slug": "missing-statement-descriptor",
"title": "No statement descriptor, so customers dispute what they see",
"description": "A trickle of unrecognized and duplicate disputes from real customers. The line on their statement does not carry your name, and never did.",
"h1": "no statement descriptor, so customers dispute what they see",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe statement descriptor", "calculated_statement_descriptor",
             "statement_descriptor_prefix", "unrecognized dispute stripe",
             "stripe descriptor visa vamp"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every month a handful of disputes arrive with the reason unrecognized or duplicate, from customers who bought the thing, kept the thing, and are perfectly happy with it. They looked at a bank statement, saw a line that meant nothing to them, and did the sensible thing. You pay the dispute fee for each one.",
"short_answer": """<p><code>GET /v1/account</code> and check <code>settings.card_payments.statement_descriptor_prefix</code> and <code>settings.payments.statement_descriptor</code>. If either is empty, what reaches the card networks is a generic default rather than your brand.</p>
<p>Then paginate <code>GET /v1/charges</code> and read <code>calculated_statement_descriptor</code>. More than one distinct value across a recent sample is worse than a bad one, because Visa identifies monitored accounts by the static component of the descriptor and a fragmented prefix splits your volume across phantom merchants.</p>""",
"problem": """<p>These are not fraud disputes and they are not unhappy customers. They are people who cannot map a line on a statement to a purchase they remember making, which is exactly the situation the <code>unrecognized</code> and <code>duplicate</code> reason codes exist for. Each one costs the disputed amount plus the fee, and each one counts toward the ratios the card networks watch.</p>
<p>The fragmentation problem is quieter and worse. Visa identifies a monitored account by the static part of the statement descriptor. If different payment flows in your integration produce different descriptors, your dispute ratio is computed against fragments of your volume rather than all of it. A small number of disputes measured against a small slice of payments can breach a threshold that your real, whole-account ratio is nowhere near.</p>""",
"why": """<p><strong>Nothing in the payment flow surfaces the descriptor.</strong> You never see it. It appears on a document the bank sends the customer, weeks later, in an abbreviated form, next to thirty other lines. The only people who read it are the ones about to dispute the charge.</p>
<p><strong>The default looks like a value.</strong> An account with no prefix set still produces a <code>calculated_statement_descriptor</code> on every charge, so the field is populated and a script that only checks for null finds nothing wrong. What it contains is a generic default, not your business name.</p>
<p><strong>The rules are strict enough that a first attempt often fails and is abandoned.</strong> Five to twenty-two characters, at least five letters, and none of the four characters Stripe rejects. Somebody tries their full legal entity name, gets an error, and leaves the field empty intending to come back.</p>
<p><strong>Different flows produce different descriptors without anyone deciding to.</strong> A Checkout Session, a Payment Link, a subscription invoice and a hand-rolled PaymentIntent can each end up with a different suffix or prefix depending on what was passed at creation. Nobody sees them side by side, so nobody notices they disagree.</p>""",
"steps": [
 {"h": "Read the account descriptor settings",
  "body": """<p>One request. <code>settings.card_payments.statement_descriptor_prefix</code> is the static part that appears on card payments; <code>settings.payments.statement_descriptor</code> is the account-level default. Empty on either is the first finding and the cheapest fix.</p>"""},
 {"h": "Sample calculated_statement_descriptor across recent charges",
  "body": """<p>This is the field that says what was actually sent, rather than what you configured. Collect the distinct values over 30 days. One value is the goal; several is fragmentation; blank is the worst case.</p>"""},
 {"h": "Check the value against the format rules",
  "body": """<p>Five to twenty-two characters, at least five letters, and none of the four characters Stripe disallows. A descriptor that is technically present but is an acronym nobody recognises fails the only test that matters, which is whether your customer can read it.</p>"""},
 {"h": "Quantify with the dispute reasons",
  "body": """<p><code>GET /v1/disputes</code> over 180 days and count the share with <code>reason</code> of <code>unrecognized</code>, <code>general</code> or <code>duplicate</code>. That share is what a clear descriptor is worth, and it is the number that gets the settings page opened.</p>"""},
 {"h": "Set the prefix once, then add a per-payment suffix",
  "body": """<p>Dashboard, Settings, Business, then public business information. Use the website domain or the business name customers know. Keep that prefix identical everywhere so Visa aggregates your volume as one account, and put the order number in <code>statement_descriptor_suffix</code> at payment creation so the customer can match the line to a specific purchase.</p>"""},
],
"verify": """<p>Re-run after the prefix is set. One distinct descriptor across the sample, and it should read as your business rather than as an abbreviation.</p>
<pre><code class="language-bash">python3 stripe_statement_descriptor.py --days 30
# consistent  EXAMPLE STORE across 1,204 charge(s)
# 0.4% of disputes cite unrecognized, general or duplicate</code></pre>""",
"code_intro": "One account read, one paginated GET over Charges and one over Disputes, no writes &mdash; read access to those three is enough. The classifier is pure and takes the configured prefix plus the descriptors actually observed, because the interesting failure is not a missing setting but a setting that disagrees with itself across payment flows.",
"py_file": "stripe_statement_descriptor.py",
"py": '''"""Report Stripe accounts whose statement descriptor is missing or inconsistent.

Read only. Three paginated GETs and no writes: give this a RESTRICTED key with
read access to Account, Charges and Disputes. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_statement_descriptor")

API = "https://api.stripe.com/v1"

MIN_LEN = 5
MAX_LEN = 22
MIN_LETTERS = 5
BANNED = ("<", ">", "'", '"')

# Reason codes a customer gives when the line on the statement meant nothing.
UNRECOGNISED = ("unrecognized", "general", "duplicate")


def verdict(prefix, descriptors):
    """Classify the account's descriptor. Pure, so the format rules test offline.

    `prefix` is the configured static prefix; `descriptors` is every
    calculated_statement_descriptor observed on recent charges. Returns
    (state, detail).
    """
    seen = sorted({(d or "").strip() for d in (descriptors or [])} - {""})
    if not (prefix or "").strip():
        return ("unset",
                "no statement descriptor prefix on the account; %d distinct "
                "descriptor(s) observed on charges" % len(seen))
    if descriptors and not seen:
        return ("blank",
                "a prefix is configured but every charge carried an empty "
                "descriptor: nothing identifying you reaches the networks")
    if len(seen) > 1:
        return ("fragmented",
                "%d distinct descriptors in use (%s): Visa identifies a monitored "
                "account by the static component, so your volume is being split"
                % (len(seen), ", ".join(seen[:3])))
    text = seen[0] if seen else prefix.strip()
    letters = sum(1 for c in text if c.isalpha())
    if len(text) < MIN_LEN or len(text) > MAX_LEN:
        return ("malformed",
                "%r is %d characters; Stripe requires %d to %d"
                % (text, len(text), MIN_LEN, MAX_LEN))
    if letters < MIN_LETTERS:
        return ("malformed",
                "%r has %d letter(s); Stripe requires at least %d"
                % (text, letters, MIN_LETTERS))
    if any(c in text for c in BANNED):
        return ("malformed",
                "%r contains a character Stripe disallows in a descriptor" % text)
    return ("consistent", "%s across the sampled charges" % text)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page(session, path, cap, **params):
    out = []
    params = dict(params)
    params["limit"] = 100
    while True:
        p = get(session, path, **params)
        data = p.get("data", [])
        out.extend(data)
        if not data or not p.get("has_more") or len(out) >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to sample charges")
    ap.add_argument("--dispute-days", type=int, default=180,
                    help="how far back to read disputes")
    ap.add_argument("--max-charges", type=int, default=5000,
                    help="stop paginating after this many charges")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    account = get(s, "/account")
    settings = account.get("settings") or {}
    prefix = ((settings.get("card_payments") or {}).get("statement_descriptor_prefix")
              or (settings.get("payments") or {}).get("statement_descriptor"))

    now = time.time()
    charges = page(s, "/charges", args.max_charges,
                   **{"created[gte]": int(now - args.days * 86400)})
    descriptors = [c.get("calculated_statement_descriptor") for c in charges]
    no_suffix = sum(1 for c in charges if not c.get("statement_descriptor_suffix"))

    state, detail = verdict(prefix, descriptors)
    log.info("%-11s %s (%d charge(s) sampled)", state, detail, len(charges))

    disputes = page(s, "/disputes", 1000,
                    **{"created[gte]": int(now - args.dispute_days * 86400)})
    if disputes:
        blind = sum(1 for d in disputes if d.get("reason") in UNRECOGNISED)
        log.info("%.1f%% of disputes cite unrecognized, general or duplicate (%d of %d)",
                 100.0 * blind / len(disputes), blind, len(disputes))

    if state == "consistent" and not no_suffix:
        return 0

    if state != "consistent":
        log.warning("  set the prefix in Dashboard, Settings, Business, public "
                    "business information: %d to %d characters, at least %d letters, "
                    "and none of %s", MIN_LEN, MAX_LEN, MIN_LETTERS, " ".join(BANNED))
        log.warning("  use the website domain or the business name customers know, "
                    "and keep it identical across every payment flow")
    if no_suffix:
        log.warning("  %d of %d charge(s) carried no statement_descriptor_suffix. Set "
                    "one at payment creation so the line names the order.",
                    no_suffix, len(charges))
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-statement-descriptor.mjs",
"js": '''/**
 * Report Stripe accounts whose statement descriptor is missing or inconsistent.
 *
 * Read only. Three paginated GETs and no writes: give this a RESTRICTED key with
 * read access to Account, Charges and Disputes. The repair is printed, never run.
 */
const API = 'https://api.stripe.com/v1';

export const MIN_LEN = 5;
export const MAX_LEN = 22;
const MIN_LETTERS = 5;
const BANNED = ['<', '>', "'", '"'];
const UNRECOGNISED = new Set(['unrecognized', 'general', 'duplicate']);

/**
 * Classify the account's descriptor. Pure, so the format rules test offline.
 * `descriptors` is every calculated_statement_descriptor seen on recent charges.
 */
export function verdict(prefix, descriptors) {
  const seen = [...new Set((descriptors ?? [])
    .map((d) => (d ?? '').trim())
    .filter((d) => d !== ''))].sort();

  if (!(prefix ?? '').trim()) {
    return ['unset',
      `no statement descriptor prefix on the account; ${seen.length} distinct ` +
      'descriptor(s) observed on charges'];
  }
  if (descriptors && descriptors.length && seen.length === 0) {
    return ['blank',
      'a prefix is configured but every charge carried an empty descriptor: ' +
      'nothing identifying you reaches the networks'];
  }
  if (seen.length > 1) {
    return ['fragmented',
      `${seen.length} distinct descriptors in use (${seen.slice(0, 3).join(', ')}): ` +
      'Visa identifies a monitored account by the static component, so your ' +
      'volume is being split'];
  }
  const text = seen.length ? seen[0] : prefix.trim();
  const letters = [...text].filter((c) => /[a-z]/i.test(c)).length;
  if (text.length < MIN_LEN || text.length > MAX_LEN) {
    return ['malformed',
      `"${text}" is ${text.length} characters; Stripe requires ${MIN_LEN} to ${MAX_LEN}`];
  }
  if (letters < MIN_LETTERS) {
    return ['malformed',
      `"${text}" has ${letters} letter(s); Stripe requires at least ${MIN_LETTERS}`];
  }
  if (BANNED.some((c) => text.includes(c))) {
    return ['malformed',
      `"${text}" contains a character Stripe disallows in a descriptor`];
  }
  return ['consistent', `${text} across the sampled charges`];
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

async function page(key, path, cap, params = {}) {
  const out = [];
  const q = { ...params, limit: 100 };
  for (;;) {
    const p = await get(key, path, q);
    const data = p.data ?? [];
    out.push(...data);
    if (data.length === 0 || !p.has_more || out.length >= cap) break;
    q.starting_after = data[data.length - 1].id;
  }
  return out;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const account = await get(key, '/account');
  const settings = account.settings ?? {};
  const prefix = settings.card_payments?.statement_descriptor_prefix
    ?? settings.payments?.statement_descriptor;

  const days = Number(process.env.DAYS ?? 30);
  const disputeDays = Number(process.env.DISPUTE_DAYS ?? 180);
  const now = Date.now() / 1000;
  const charges = await page(key, '/charges', 5000,
    { 'created[gte]': Math.floor(now - days * 86400) });
  const descriptors = charges.map((c) => c.calculated_statement_descriptor);
  const noSuffix = charges.filter((c) => !c.statement_descriptor_suffix).length;

  const [state, detail] = verdict(prefix, descriptors);
  console.log(`${state.padEnd(11)} ${detail} (${charges.length} charge(s) sampled)`);

  const disputes = await page(key, '/disputes', 1000,
    { 'created[gte]': Math.floor(now - disputeDays * 86400) });
  if (disputes.length) {
    const blind = disputes.filter((d) => UNRECOGNISED.has(d.reason)).length;
    console.log(`${(100 * blind / disputes.length).toFixed(1)}% of disputes cite ` +
                `unrecognized, general or duplicate (${blind} of ${disputes.length})`);
  }

  if (state === 'consistent' && !noSuffix) return;

  if (state !== 'consistent') {
    console.warn('  set the prefix in Dashboard, Settings, Business, public business ' +
                 `information: ${MIN_LEN} to ${MAX_LEN} characters, at least ` +
                 `${MIN_LETTERS} letters, and none of ${BANNED.join(' ')}`);
    console.warn('  use the website domain or the business name customers know, and ' +
                 'keep it identical across every payment flow');
  }
  if (noSuffix) {
    console.warn(`  ${noSuffix} of ${charges.length} charge(s) carried no ` +
                 'statement_descriptor_suffix. Set one at payment creation so the ' +
                 'line names the order.');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The interesting case is not the empty setting, which anybody would catch. It is two payment flows producing two different descriptors while both of them look perfectly reasonable on their own, because that is the state that quietly splits your dispute ratio across accounts Visa thinks are separate. The format rules are tested at their boundaries for the ordinary reason: a check that accepts a four-character descriptor is telling you something Stripe will reject.",
"test_py_file": "test_stripe_statement_descriptor.py",
"test_py": '''from stripe_statement_descriptor import verdict


def test_no_prefix_is_the_first_finding():
    state, detail = verdict(None, ["EXAMPLE STORE"])
    assert state == "unset"
    assert "1 distinct" in detail
    assert verdict("   ", [])[0] == "unset"


def test_two_flows_with_two_descriptors_is_fragmentation():
    state, detail = verdict("EXAMPLE", ["EXAMPLE STORE", "EXAMPLE SUBS", "EXAMPLE STORE"])
    assert state == "fragmented"
    assert "2 distinct" in detail


def test_a_configured_prefix_with_empty_descriptors_is_worse_than_missing():
    assert verdict("EXAMPLE", ["", "  ", None])[0] == "blank"


def test_the_format_rules_are_checked_at_their_boundaries():
    assert verdict("EXAMPLE", ["ABCD"])[0] == "malformed"          # 4 chars
    assert verdict("EXAMPLE", ["ABCDE"])[0] == "consistent"        # 5 is the floor
    assert verdict("EXAMPLE", ["A" * 23])[0] == "malformed"        # 23 chars
    assert verdict("EXAMPLE", ["AB 12"])[0] == "malformed"         # only 2 letters


def test_a_disallowed_character_is_rejected():
    state, detail = verdict("EXAMPLE", ["EXAMPLE<STORE"])
    assert state == "malformed"
    assert "disallows" in detail
''',
"test_js_file": "stripe-statement-descriptor.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-statement-descriptor.mjs';

test('no prefix is the first finding', () => {
  const [state, detail] = verdict(null, ['EXAMPLE STORE']);
  assert.equal(state, 'unset');
  assert.ok(detail.includes('1 distinct'));
  assert.equal(verdict('   ', [])[0], 'unset');
});

test('two flows with two descriptors is fragmentation', () => {
  const [state, detail] = verdict('EXAMPLE',
    ['EXAMPLE STORE', 'EXAMPLE SUBS', 'EXAMPLE STORE']);
  assert.equal(state, 'fragmented');
  assert.ok(detail.includes('2 distinct'));
});

test('a configured prefix with empty descriptors is worse than missing', () => {
  assert.equal(verdict('EXAMPLE', ['', '  ', null])[0], 'blank');
});

test('the format rules are checked at their boundaries', () => {
  assert.equal(verdict('EXAMPLE', ['ABCD'])[0], 'malformed');
  assert.equal(verdict('EXAMPLE', ['ABCDE'])[0], 'consistent');
  assert.equal(verdict('EXAMPLE', ['A'.repeat(23)])[0], 'malformed');
  assert.equal(verdict('EXAMPLE', ['AB 12'])[0], 'malformed');
});

test('a disallowed character is rejected', () => {
  const [state, detail] = verdict('EXAMPLE', ['EXAMPLE<STORE']);
  assert.equal(state, 'malformed');
  assert.ok(detail.includes('disallows'));
});
''',
"faq": [
 ("What actually appears on the customer's statement?",
  "The calculated_statement_descriptor on the charge, which combines the account's static prefix with any per-payment suffix. It is the only field that tells you what was sent; the account settings tell you what you configured, and those two can disagree once different payment flows pass their own values."),
 ("Why does one inconsistent descriptor matter so much?",
  "Visa identifies a monitored account by the static component of the descriptor. Two descriptors means your payments are counted as two merchants, so a handful of disputes is measured against half your volume instead of all of it, and a ratio you are comfortably under can be breached on a fragment."),
 ("What are the format rules?",
  "Five to twenty-two characters, at least five letters, and none of the four characters Stripe disallows. Beyond the rules, the useful test is whether a customer who bought from you last month would recognise it on a bank statement without thinking about it."),
 ("Is the suffix worth setting per payment?",
  "Yes, when there is anything to name. An order number in statement_descriptor_suffix turns an unrecognized dispute into a support email, because the customer can search their inbox for the number they are looking at. It goes on the PaymentIntent at creation."),
 ("Will fixing the descriptor change disputes already open?",
  "No. Descriptors are recorded at payment time and existing disputes carry the old one. The change affects payments made afterwards, which is why the reason-code share is worth recording before you make it and again 90 days later."),
],
"related": [
 ("/stripe/disputes-lost-without-response/", "Disputes are lost by default when nobody responds"),
 ("/stripe/missing-dispute-and-fraud-events/", "No endpoint subscribes to dispute or fraud events"),
 ("/stripe/avs-cvc-fail-captured/", "Charges captured after AVS and CVC verification failed"),
],
"citations": [CITE_PREVENTION, CITE_CHARGE_OBJ, CITE_MONITORING, CITE_ACCOUNT_OBJ],
},

]
