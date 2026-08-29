#!/usr/bin/env python3
"""/stripe/ field notes, batch P — the four subscription states that stop
collecting money without ever looking broken.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

These four sit next to the subscription notes already published and deliberately
do not restate them. `past-due-subscriptions-accumulating` and
`dunning-retries-exhausted` cover the period while Stripe is still trying to
collect. This batch starts after that: `unpaid` is where dunning ends and Stripe
stops attempting payment altogether; `paused` is the status a trial ends into
when no card was ever attached; `pause_collection` is a completely separate
field that suppresses billing while the status stays `active`; and
`cancel_at_period_end` is churn that is already committed and still reads as
active in every report.
"""

CHIPS = ["Read-only key", "Python and Node.js", "Tests included"]

CITE_SUB_OBJ = ("The subscription object — Stripe API reference",
                "https://docs.stripe.com/api/subscriptions/object")
CITE_SUB_LIST = ("List subscriptions — Stripe API reference",
                 "https://docs.stripe.com/api/subscriptions/list")
CITE_SUB_OVERVIEW = ("How subscriptions work — Stripe Docs",
                     "https://docs.stripe.com/billing/subscriptions/overview")
CITE_COLLECTION = ("Collection methods — Stripe Docs",
                   "https://docs.stripe.com/billing/collection-method")
CITE_INVOICE_OBJ = ("The invoice object — Stripe API reference",
                    "https://docs.stripe.com/api/invoices/object")
CITE_TRIALS = ("Subscription trials — Stripe Docs",
               "https://docs.stripe.com/billing/subscriptions/trials")
CITE_PAUSE = ("Pause payment collection — Stripe Docs",
              "https://docs.stripe.com/billing/subscriptions/pause-payment")
CITE_PORTAL_CONFIG = ("The portal configuration object — Stripe API reference",
                      "https://docs.stripe.com/api/customer_portal/configurations/object")
CITE_RETRIES = ("Smart Retries — Stripe Docs",
                "https://docs.stripe.com/billing/revenue-recovery/smart-retries")

GUIDES = [

{
"slug": "unpaid-subscriptions-still-provisioned",
"title": "unpaid subscriptions keep access and stop billing entirely",
"description": "unpaid is where dunning ends. Stripe still creates invoices but closes them without attempting payment, so the balance owed grows and nothing collects it.",
"h1": "unpaid subscriptions keep access and stop billing entirely",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe unpaid subscription", "stripe subscription status unpaid",
             "unpaid subscription still active", "stripe draft invoices not sent",
             "revoke access unpaid subscription"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A handful of customers are still logged in and still using everything, and the last money any of them sent you was months ago. Their subscriptions are not canceled and they are not <code>past_due</code> either. They are <code>unpaid</code>, which is the state Stripe parks a subscription in when it has finished trying and been told not to cancel.",
"short_answer": """<p>Read <code>GET /v1/subscriptions?status=unpaid&amp;limit=100</code>. Every row is a customer whose dunning is over. Then, per subscription, <code>GET /v1/invoices?subscription={sub_id}&amp;status=draft&amp;limit=100</code>: a stack of drafts is Stripe still generating the invoice each period and immediately closing it, because on an <code>unpaid</code> subscription payment is not attempted.</p>
<p>Two fixes, and you need both. Gate provisioning on <code>status</code> being <code>active</code> or <code>trialing</code>, so <code>unpaid</code> revokes access. And change the end-of-retries behaviour under <strong>Billing, Revenue recovery, Retries</strong> to cancel instead, so nothing else lands here.</p>""",
"problem": """<p><code>unpaid</code> is a terminal state that looks like a live one. The subscription object is still there, the items are still there, <code>ended_at</code> is null, and every report built on "not canceled" counts it as a subscriber. Meanwhile Stripe has stopped collecting: the docs are explicit that once a subscription is <code>unpaid</code>, subsequent invoices are created but immediately closed and payments are not attempted.</p>
<p>So the meter keeps running on your side and the till is switched off on Stripe's. The customer accrues an invoice every period that nobody will ever send, ever finalise, or ever charge. Nothing errors, because nothing is being tried.</p>
<p>It is also the one dunning outcome that produces no further events. A subscription that cancels fires <code>customer.subscription.deleted</code> and your revocation code runs. A subscription that goes <code>unpaid</code> fires <code>customer.subscription.updated</code> once, months ago, and then goes quiet forever.</p>""",
"why": """<p><strong>Somebody chose "mark unpaid" instead of "cancel".</strong> The end-of-retries action is a Dashboard setting with three options: cancel, mark unpaid, or leave past due. "Mark unpaid" sounds like the cautious one, the choice that keeps the record around in case the customer comes back. It is cautious about the record and reckless about the access.</p>
<p><strong>The entitlement check was written against the statuses that existed in the demo.</strong> <code>active</code>, <code>trialing</code>, <code>canceled</code>. <code>unpaid</code> is reachable only after a full dunning cycle has run out, so it never appears in testing, and a check written as <code>status != "canceled"</code> passes it straight through.</p>
<p><strong>The draft invoices hide the size of it.</strong> Draft invoices do not appear in revenue reports, do not appear in accounts receivable, and do not appear in the customer's invoice history in the portal. The amount owed is real and it is completely absent from every screen anyone looks at.</p>
<p><strong>It is not the same failure as <code>past_due</code>.</strong> A <code>past_due</code> subscription is one Stripe is still working on, with a scheduled retry you can read. An <code>unpaid</code> one has no next attempt because attempts have stopped being a thing that happens. Detecting one does not detect the other, and the <a href="/stripe/past-due-subscriptions-accumulating/">past-due note</a> covers the earlier half.</p>""",
"steps": [
 {"h": "List the unpaid subscriptions",
  "body": """<p><code>GET /v1/subscriptions?status=unpaid&amp;limit=100</code>. Do it in both modes. Any result at all is a finding: <code>unpaid</code> is not a state a healthy account passes through, it is a state a subscription is left in.</p>"""},
 {"h": "Count the drafts behind each one",
  "body": """<p><code>GET /v1/invoices?subscription={sub_id}&amp;status=draft&amp;limit=100</code>. Read <code>auto_advance</code> on each: <code>false</code> is Stripe telling you this invoice will never finalise on its own. Sum <code>amount_due</code> across them and you have the number that is missing from your AR.</p>"""},
 {"h": "Fix the entitlement check first",
  "body": """<p>This is the part that is costing you money right now. Gate on <code>status in ("active", "trialing")</code>. Every other status, including <code>unpaid</code>, <code>past_due</code> and <code>paused</code>, is a customer who should not be served.</p>"""},
 {"h": "Decide what to do with the balance owed",
  "body": """<p>For a customer worth chasing, restart collection on the stranded drafts: <code>POST /v1/invoices/{inv}</code> with <code>auto_advance=true</code>, or <code>POST /v1/invoices/{inv}/send</code> to mail the hosted invoice. For one that is gone, cancel the subscription so it stops generating invoices nobody will ever look at.</p>"""},
 {"h": "Change the end-of-dunning action",
  "body": """<p>Dashboard, then <strong>Billing, Revenue recovery, Retries</strong>. Set the final action to cancel the subscription. That makes <code>customer.subscription.deleted</code> fire, which is the event your revocation code is already listening for.</p>"""},
],
"verify": """<p>Re-run the script. The unpaid query should come back empty, and the count of stranded drafts with it.</p>
<pre><code class="language-bash">python3 stripe_unpaid_subscriptions.py
# 0 unpaid subscription(s), 0 stranded draft invoice(s)</code></pre>""",
"code_intro": "Two GETs per subscription and no writes &mdash; the subscription list, then the draft invoices behind each row. A restricted key with read access to Subscriptions and Invoices covers it. The classifier is pure and takes the subscription plus its drafts, because the distinction that matters is not whether drafts exist but whether <code>auto_advance</code> is off on them: that flag is the difference between invoices somebody has already restarted and invoices Stripe closed the moment it made them.",
"py_file": "stripe_unpaid_subscriptions.py",
"py": '''"""Report unpaid subscriptions and the draft invoices stranded behind them.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Subscriptions and Invoices. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_unpaid_subscriptions")

API = "https://api.stripe.com/v1"


def verdict(sub, drafts):
    """Classify one subscription and the draft invoices behind it.

    `drafts` is this subscription's invoices already filtered to status draft.
    Pure, so the rules are visible and testable without a network.
    Returns (state, detail).
    """
    status = sub.get("status")
    if status != "unpaid":
        return ("not-unpaid",
                "status is %r, which is a different problem than this one"
                % (status,))

    # auto_advance false is Stripe saying this invoice will never finalise by
    # itself. On an unpaid subscription that is every invoice it generates.
    closed = [d for d in drafts if not d.get("auto_advance")]
    if closed:
        owed = sum(d.get("amount_due") or 0 for d in closed)
        return ("stranded",
                "%d draft invoice(s) worth %d (minor units) were created and "
                "closed without a payment attempt" % (len(closed), owed))
    if drafts:
        return ("collecting",
                "%d draft invoice(s) still carry auto_advance, so somebody has "
                "already restarted collection here" % len(drafts))
    return ("silent",
            "no invoices since dunning ended. Billing stopped at the last "
            "past_due invoice and access is whatever your app still grants.")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Walk a Stripe list endpoint, stopping at `limit` objects."""
    out = []
    params = dict(params, limit=100)
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=500,
                    help="stop after this many unpaid subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    subs = page_all(s, "/subscriptions", args.max_subscriptions, status="unpaid")
    if not subs:
        log.info("0 unpaid subscription(s), 0 stranded draft invoice(s)")
        return 0

    stranded = 0
    for sub in subs:
        drafts = page_all(s, "/invoices", 100, subscription=sub["id"], status="draft")
        state, detail = verdict(sub, drafts)
        log.warning("%-11s %s  %s", state, sub["id"], detail)
        if state == "stranded":
            stranded += len(drafts)
            log.warning("  repair: for each draft, POST %s/invoices/{inv} "
                        "-d auto_advance=true (or /send to mail it)", API)
        log.warning("  repair: gate provisioning on status in (active, trialing); "
                    "unpaid must revoke")
        log.warning("  repair: Billing, Revenue recovery, Retries: set the final "
                    "action to cancel instead of mark unpaid")

    log.info("%d unpaid subscription(s), %d stranded draft invoice(s)",
             len(subs), stranded)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-unpaid-subscriptions.mjs",
"js": '''/**
 * Report unpaid subscriptions and the draft invoices stranded behind them.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access
 * to Subscriptions and Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one subscription and the draft invoices behind it. Pure, so the
 * rules are visible and testable without a network.
 */
export function verdict(sub, drafts) {
  const status = sub.status;
  if (status !== 'unpaid') {
    return ['not-unpaid',
      `status is ${JSON.stringify(status)}, which is a different problem than this one`];
  }

  // auto_advance false is Stripe saying this invoice will never finalise by
  // itself. On an unpaid subscription that is every invoice it generates.
  const closed = (drafts ?? []).filter((d) => !d.auto_advance);
  if (closed.length > 0) {
    const owed = closed.reduce((t, d) => t + (d.amount_due ?? 0), 0);
    return ['stranded',
      `${closed.length} draft invoice(s) worth ${owed} (minor units) were ` +
      'created and closed without a payment attempt'];
  }
  if ((drafts ?? []).length > 0) {
    return ['collecting',
      `${drafts.length} draft invoice(s) still carry auto_advance, so somebody ` +
      'has already restarted collection here'];
  }
  return ['silent',
    'no invoices since dunning ended. Billing stopped at the last past_due ' +
    'invoice and access is whatever your app still grants.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function pageAll(key, path, limit, params = {}) {
  const out = [];
  const q = { ...params, limit: 100 };
  for (;;) {
    const page = await get(key, path, q);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) break;
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

  const subs = await pageAll(key, '/subscriptions', 500, { status: 'unpaid' });
  if (subs.length === 0) {
    console.log('0 unpaid subscription(s), 0 stranded draft invoice(s)');
    return;
  }

  let stranded = 0;
  for (const sub of subs) {
    const drafts = await pageAll(key, '/invoices', 100,
      { subscription: sub.id, status: 'draft' });
    const [state, detail] = verdict(sub, drafts);
    console.warn(`${state.padEnd(11)} ${sub.id}  ${detail}`);
    if (state === 'stranded') {
      stranded += drafts.length;
      console.warn(`  repair: for each draft, POST ${API}/invoices/{inv} ` +
                   '-d auto_advance=true (or /send to mail it)');
    }
    console.warn('  repair: gate provisioning on status in (active, trialing); ' +
                 'unpaid must revoke');
    console.warn('  repair: Billing, Revenue recovery, Retries: set the final ' +
                 'action to cancel instead of mark unpaid');
  }

  console.log(`${subs.length} unpaid subscription(s), ${stranded} stranded ` +
              'draft invoice(s)');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning is a draft invoice with no <code>auto_advance</code> key at all. Absent is not the same as <code>true</code>, and treating it as such would report a subscription somebody is actively collecting on when in fact Stripe closed the invoice on creation. The tests also keep <code>stranded</code> and <code>silent</code> apart, because one has a balance to chase and the other only has access to revoke.",
"test_py_file": "test_stripe_unpaid_subscriptions.py",
"test_py": '''from stripe_unpaid_subscriptions import verdict

UNPAID = {"id": "sub_1", "status": "unpaid"}


def test_unpaid_with_closed_drafts_reports_the_balance_owed():
    state, detail = verdict(UNPAID, [{"auto_advance": False, "amount_due": 2500},
                                     {"auto_advance": False, "amount_due": 2500}])
    assert state == "stranded"
    assert "5000" in detail


def test_missing_auto_advance_counts_as_closed():
    # Absent is not true. A draft Stripe closed on creation carries no flag at
    # all, and reading that as collecting hides the whole finding.
    state, _ = verdict(UNPAID, [{"amount_due": 900}])
    assert state == "stranded"


def test_drafts_with_auto_advance_mean_somebody_restarted_collection():
    state, _ = verdict(UNPAID, [{"auto_advance": True, "amount_due": 900}])
    assert state == "collecting"


def test_unpaid_with_no_invoices_is_its_own_finding():
    # Nothing to chase, but the access is still granted.
    state, detail = verdict(UNPAID, [])
    assert state == "silent"
    assert "past_due" in detail


def test_a_past_due_subscription_is_not_this_problem():
    state, _ = verdict({"id": "sub_2", "status": "past_due"}, [])
    assert state == "not-unpaid"
''',
"test_js_file": "stripe-unpaid-subscriptions.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-unpaid-subscriptions.mjs';

const UNPAID = { id: 'sub_1', status: 'unpaid' };

test('unpaid with closed drafts reports the balance owed', () => {
  const [state, detail] = verdict(UNPAID, [
    { auto_advance: false, amount_due: 2500 },
    { auto_advance: false, amount_due: 2500 },
  ]);
  assert.equal(state, 'stranded');
  assert.match(detail, /5000/);
});

test('missing auto_advance counts as closed', () => {
  // Absent is not true. A draft Stripe closed on creation has no flag at all.
  assert.equal(verdict(UNPAID, [{ amount_due: 900 }])[0], 'stranded');
});

test('drafts with auto_advance mean somebody restarted collection', () => {
  assert.equal(verdict(UNPAID, [{ auto_advance: true, amount_due: 900 }])[0],
    'collecting');
});

test('unpaid with no invoices is its own finding', () => {
  const [state, detail] = verdict(UNPAID, []);
  assert.equal(state, 'silent');
  assert.match(detail, /past_due/);
});

test('a past_due subscription is not this problem', () => {
  assert.equal(verdict({ id: 'sub_2', status: 'past_due' }, [])[0], 'not-unpaid');
});
''',
"faq": [
 ("What does the unpaid subscription status actually mean in Stripe?",
  "It is one of the three things Stripe can do when dunning finishes: cancel, leave past due, or mark unpaid. On an unpaid subscription Stripe keeps generating an invoice each billing period, but those invoices are created and immediately closed and no payment is attempted. The subscription is alive as a record and dead as a source of revenue."),
 ("Does an unpaid subscription still count as active in my app?",
  "It does if your entitlement check asks whether the status is canceled. It is not canceled, so the answer is yes and the customer keeps everything. Gate on status being active or trialing instead; that one change turns unpaid, past_due and paused into revocations without needing to enumerate them."),
 ("Can I collect the money from the draft invoices?",
  "Yes, one at a time. POST /v1/invoices/{id} with auto_advance=true restarts Stripe's collection on a draft, and POST /v1/invoices/{id}/send mails the hosted invoice link. Neither happens on its own while the subscription stays unpaid, which is exactly why the drafts piled up."),
 ("How is this different from past_due?",
  "past_due means Stripe is still trying: there is an attempt_count and usually a next_payment_attempt you can read. unpaid means it has stopped trying, permanently, and no further attempt will ever be scheduled. A check that finds one will not find the other."),
 ("Which webhook tells me a subscription went unpaid?",
  "customer.subscription.updated, once, with the status change in the payload. There is no dedicated event and nothing fires afterwards, so if that one update was missed the subscription simply goes quiet. This is the main practical argument for setting the end-of-retries action to cancel, which fires customer.subscription.deleted instead."),
],
"related": [
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access forever"),
 ("/stripe/dunning-retries-exhausted/", "Dunning ran out of retries and no attempt is scheduled"),
 ("/stripe/open-invoices-past-due-date/", "Open invoices past their due date"),
],
"citations": [CITE_SUB_OBJ, CITE_COLLECTION, CITE_SUB_OVERVIEW, CITE_INVOICE_OBJ],
},

{
"slug": "paused-subscriptions-never-resumed",
"title": "paused subscriptions never resume and never invoice again",
"description": "A trial that ends with no card can park the subscription in paused. Stripe stops creating invoices and there is no timeout: it waits for a resume nobody makes.",
"h1": "paused subscriptions never resume and never invoice again",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe paused subscription", "subscription status paused",
             "stripe resume paused subscription", "trial end pause behaviour",
             "paused subscriptions not billing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody set trials to pause instead of dunning when no card was attached, which was the right call. Nobody built the other half. Two years of trials that ended without a card are sitting in <code>paused</code>, generating nothing, appearing in no past-due report, and waiting for a resume that is not coming.",
"short_answer": """<p>Read <code>GET /v1/subscriptions?status=paused&amp;limit=100</code>. There is no timeout on this status and no automatic exit from it, so every row is inventory that has been sitting still since the day its trial ended.</p>
<p>Sort them by two things. Whether a payment method has since appeared &mdash; those need only the resume call. And age against one billing interval, computed from <code>items.data[0].price.recurring</code>; anything older than that is not a pause, it is churn that was never recorded as churn.</p>""",
"problem": """<p><code>paused</code> is the narrowest status Stripe has. There is exactly one way in: a trial ends, the subscription has no payment method, and <code>trial_settings.end_behavior.missing_payment_method</code> is set to <code>pause</code>. Stripe then stops creating invoices entirely and holds the subscription there indefinitely.</p>
<p>That is the correct behaviour and it is much better than the default, which is to cut an invoice that instantly fails. The problem is that it is a state with no clock. Nothing expires it, nothing escalates it, and nothing fires from it after the initial <code>customer.subscription.paused</code>. It is a queue with no consumer.</p>
<p>And it hides from the two reports people actually read. It is not in the past-due list, because nothing is due. It is not in the churn number, because nothing was canceled. A cohort of customers who wanted the product enough to start a trial simply stops existing, in a status that nobody has a dashboard for.</p>""",
"why": """<p><strong>Configuring the pause is one line and handling it is a project.</strong> Setting <code>missing_payment_method=pause</code> takes a minute. Reacting to it means an event handler, a win-back sequence, a billing-portal link, and someone to own the list. The first half ships and the second half becomes a ticket.</p>
<p><strong>Resuming is not a single flag.</strong> Attaching a card does not un-pause anything. The subscription has to be updated with a valid <code>default_payment_method</code> and <code>pause_collection</code> cleared, and doing so can generate an invoice that must be paid before the status actually leaves <code>paused</code>. So a customer who added a card through the portal months ago can still be sitting in the list &mdash; and that is the most recoverable row in it.</p>
<p><strong>It is confused with the field of a similar name.</strong> <code>pause_collection</code> is a completely different mechanism that leaves the status <code>active</code>; the <a href="/stripe/pause-collection-left-on-indefinitely/">note on that one</a> is separate for exactly this reason. Searching your code for "pause" finds one and not the other.</p>
<p><strong>The age is invisible without doing arithmetic.</strong> The object carries <code>trial_end</code> and <code>start_date</code>, not a "paused for" number. Until someone bucket-sorts by the billing interval, a subscription paused last week and one paused in 2024 look identical in a list.</p>""",
"steps": [
 {"h": "List everything in paused",
  "body": """<p><code>GET /v1/subscriptions?status=paused&amp;limit=100</code>, expanding <code>data.customer</code> so you can see whether a payment method has turned up since. Page it all &mdash; the interesting rows are the oldest ones and Stripe returns newest first.</p>"""},
 {"h": "Separate the ones that only need the resume call",
  "body": """<p>Check <code>default_payment_method</code>, <code>default_source</code>, and the customer's <code>invoice_settings.default_payment_method</code>. If any is set, this customer gave you a card and is still being served nothing. That is the top of the list, not the bottom.</p>"""},
 {"h": "Age the rest against one billing interval",
  "body": """<p>Read the interval from <code>items.data[0].price.recurring.interval</code> and <code>interval_count</code>. Paused for less than one interval is a win-back you can still run. Paused for longer is dead inventory, and pretending otherwise inflates whatever you are calling your subscriber count.</p>"""},
 {"h": "Resume the recoverable ones",
  "body": """<p><code>POST /v1/subscriptions/{sub}</code> with <code>pause_collection=</code> (empty) and a valid <code>default_payment_method</code>. Expect an invoice to be generated; the status does not leave <code>paused</code> until it is paid.</p>"""},
 {"h": "Give the status an owner",
  "body": """<p>Handle <code>customer.subscription.paused</code>: revoke access and start the win-back sequence with a billing-portal link in it. Once something consumes the queue, this note stops applying to you.</p>"""},
],
"verify": """<p>Re-run the script. Nothing should be older than one billing interval, and nothing should be paused with a usable payment method already on file.</p>
<pre><code class="language-bash">python3 stripe_paused_subscriptions.py
# 0 paused subscription(s): 0 resumable, 0 stale</code></pre>""",
"code_intro": "One GET with the customer expanded, and no writes. A restricted key with read access to Subscriptions and Customers is enough. The classifier is pure and takes the subscription and the current time, because both facts it sorts on &mdash; whether a payment method exists anywhere, and how the age compares to this subscription's own billing interval &mdash; are computed from the object rather than assumed.",
"py_file": "stripe_paused_subscriptions.py",
"py": '''"""Report paused subscriptions, sorted by whether they can still be resumed.

Read only. One GET, no writes: give this a RESTRICTED key with read access to
Subscriptions and Customers. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_paused_subscriptions")

API = "https://api.stripe.com/v1"
DAY = 86400
INTERVALS = {"day": DAY, "week": 7 * DAY, "month": 30 * DAY, "year": 365 * DAY}


def interval_seconds(sub):
    """Length of one billing interval, from the first item's recurring price.

    Falls back to 30 days when the price is not expanded or the interval is one
    we do not recognise: a paused subscription with an unknown interval is still
    worth ageing, and guessing monthly is the conservative guess.
    """
    items = (sub.get("items") or {}).get("data") or []
    if not items:
        return 30 * DAY
    price = items[0].get("price") or items[0].get("plan") or {}
    recurring = price.get("recurring") or price
    unit = INTERVALS.get(recurring.get("interval"))
    if not unit:
        return 30 * DAY
    return unit * (recurring.get("interval_count") or 1)


def has_payment_method(sub):
    """True when Stripe has something to charge the moment this is resumed.

    Same four places Stripe itself looks, in the same order.
    """
    customer = sub.get("customer")
    if not isinstance(customer, dict):
        customer = {}
    return bool(sub.get("default_payment_method")
                or sub.get("default_source")
                or (customer.get("invoice_settings") or {}).get("default_payment_method")
                or customer.get("default_source"))


def verdict(sub, now):
    """Classify one paused subscription. Pure, so the rules can be tested.

    Returns (state, detail).
    """
    if sub.get("status") != "paused":
        return ("not-paused",
                "status is %r; paused is only reachable from a trial that ended "
                "with no payment method" % (sub.get("status"),))
    if has_payment_method(sub):
        return ("resumable",
                "a payment method is already on file. The only thing keeping this "
                "paused is the resume nobody performed.")
    days = int((now - (sub.get("trial_end") or sub.get("start_date") or now)) // DAY)
    if now - (sub.get("trial_end") or sub.get("start_date") or now) > interval_seconds(sub):
        return ("stale",
                "paused %d day(s), longer than one billing interval. This is "
                "churn that was never recorded as churn." % days)
    return ("recent",
            "paused %d day(s), inside one billing interval. The win-back window "
            "is still open." % days)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def paused_subscriptions(session, limit):
    """Page every paused subscription, customer expanded so cards are visible."""
    out = []
    params = {"status": "paused", "limit": 100, "expand[]": "data.customer"}
    while True:
        page = get(session, "/subscriptions", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=1000,
                    help="stop after this many paused subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    subs = paused_subscriptions(s, args.max_subscriptions)
    now = int(time.time())
    counts = {}
    for sub in subs:
        state, detail = verdict(sub, now)
        counts[state] = counts.get(state, 0) + 1
        log.warning("%-10s %s  %s", state, sub["id"], detail)
        if state == "resumable":
            log.warning("  repair: POST %s/subscriptions/%s -d pause_collection= "
                        "-d default_payment_method={pm}", API, sub["id"])
        elif state == "stale":
            log.warning("  repair: count it as churn, or send a billing portal "
                        "link before you do")

    log.info("%d paused subscription(s): %d resumable, %d stale",
             len(subs), counts.get("resumable", 0), counts.get("stale", 0))
    if subs:
        log.info("handle customer.subscription.paused so this list has an owner")
    return 1 if subs else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-paused-subscriptions.mjs",
"js": '''/**
 * Report paused subscriptions, sorted by whether they can still be resumed.
 *
 * Read only. One GET, no writes: give this a RESTRICTED key with read access to
 * Subscriptions and Customers. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;
const INTERVALS = { day: DAY, week: 7 * DAY, month: 30 * DAY, year: 365 * DAY };

/**
 * Length of one billing interval, from the first item's recurring price.
 * Falls back to 30 days when the price is not expanded.
 */
export function intervalSeconds(sub) {
  const items = sub.items?.data ?? [];
  if (items.length === 0) return 30 * DAY;
  const price = items[0].price ?? items[0].plan ?? {};
  const recurring = price.recurring ?? price;
  const unit = INTERVALS[recurring.interval];
  if (!unit) return 30 * DAY;
  return unit * (recurring.interval_count ?? 1);
}

/** True when Stripe has something to charge the moment this is resumed. */
export function hasPaymentMethod(sub) {
  const customer = typeof sub.customer === 'object' && sub.customer !== null
    ? sub.customer : {};
  return Boolean(sub.default_payment_method
    || sub.default_source
    || customer.invoice_settings?.default_payment_method
    || customer.default_source);
}

/** Classify one paused subscription. Pure, so the rules can be tested. */
export function verdict(sub, now) {
  if (sub.status !== 'paused') {
    return ['not-paused',
      `status is ${JSON.stringify(sub.status)}; paused is only reachable from a ` +
      'trial that ended with no payment method'];
  }
  if (hasPaymentMethod(sub)) {
    return ['resumable',
      'a payment method is already on file. The only thing keeping this paused ' +
      'is the resume nobody performed.'];
  }
  const since = sub.trial_end ?? sub.start_date ?? now;
  const age = now - since;
  const days = Math.floor(age / DAY);
  if (age > intervalSeconds(sub)) {
    return ['stale',
      `paused ${days} day(s), longer than one billing interval. This is churn ` +
      'that was never recorded as churn.'];
  }
  return ['recent',
    `paused ${days} day(s), inside one billing interval. The win-back window is ` +
    'still open.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function pausedSubscriptions(key, limit = 1000) {
  const out = [];
  const params = { status: 'paused', limit: 100, 'expand[]': 'data.customer' };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) break;
    params.starting_after = data[data.length - 1].id;
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

  const subs = await pausedSubscriptions(key);
  const now = Math.floor(Date.now() / 1000);
  const counts = new Map();
  for (const sub of subs) {
    const [state, detail] = verdict(sub, now);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    console.warn(`${state.padEnd(10)} ${sub.id}  ${detail}`);
    if (state === 'resumable') {
      console.warn(`  repair: POST ${API}/subscriptions/${sub.id} ` +
                   '-d pause_collection= -d default_payment_method={pm}');
    } else if (state === 'stale') {
      console.warn('  repair: count it as churn, or send a billing portal link ' +
                   'before you do');
    }
  }

  console.log(`${subs.length} paused subscription(s): ` +
              `${counts.get('resumable') ?? 0} resumable, ` +
              `${counts.get('stale') ?? 0} stale`);
  if (subs.length > 0) {
    console.log('handle customer.subscription.paused so this list has an owner');
  }
  process.exitCode = subs.length > 0 ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things the tests hold in place. A subscription with a card on file is <code>resumable</code> however old it is, because age is a priority signal and a usable payment method is a certainty; sorting it by age first would bury the easiest recovery in the list. And the interval comes from the subscription's own price, so a yearly plan paused for two months is <code>recent</code> while a monthly one paused for the same two months is <code>stale</code>.",
"test_py_file": "test_stripe_paused_subscriptions.py",
"test_py": '''from stripe_paused_subscriptions import verdict

NOW = 1_800_000_000
DAY = 86400


def paused(days_ago, interval="month", count=1, **extra):
    body = {
        "id": "sub_1",
        "status": "paused",
        "trial_end": NOW - days_ago * DAY,
        "items": {"data": [{"price": {"recurring": {"interval": interval,
                                                    "interval_count": count}}}]},
    }
    body.update(extra)
    return body


def test_a_card_on_file_beats_age():
    state, _ = verdict(paused(400, default_payment_method="pm_1"), NOW)
    assert state == "resumable"


def test_a_customer_default_counts_as_a_card():
    customer = {"invoice_settings": {"default_payment_method": "pm_2"}}
    state, _ = verdict(paused(400, customer=customer), NOW)
    assert state == "resumable"


def test_past_one_billing_interval_is_dead_inventory():
    state, detail = verdict(paused(90), NOW)
    assert state == "stale"
    assert "90 day(s)" in detail


def test_the_interval_comes_from_this_subscriptions_own_price():
    # Two months is stale on a monthly plan and recent on a yearly one.
    assert verdict(paused(60, interval="year"), NOW)[0] == "recent"
    assert verdict(paused(60, interval="month"), NOW)[0] == "stale"


def test_only_paused_is_this_problem():
    state, _ = verdict(paused(90, status="active"), NOW)
    assert state == "not-paused"
''',
"test_js_file": "stripe-paused-subscriptions.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-paused-subscriptions.mjs';

const NOW = 1800000000;
const DAY = 86400;

function sub(daysAgo, { interval = 'month', count = 1, ...extra } = {}) {
  return {
    id: 'sub_1',
    status: 'paused',
    trial_end: NOW - daysAgo * DAY,
    items: { data: [{ price: { recurring: { interval, interval_count: count } } }] },
    ...extra,
  };
}

test('a card on file beats age', () => {
  assert.equal(verdict(sub(400, { default_payment_method: 'pm_1' }), NOW)[0],
    'resumable');
});

test('a customer default counts as a card', () => {
  const customer = { invoice_settings: { default_payment_method: 'pm_2' } };
  assert.equal(verdict(sub(400, { customer }), NOW)[0], 'resumable');
});

test('past one billing interval is dead inventory', () => {
  const [state, detail] = verdict(sub(90), NOW);
  assert.equal(state, 'stale');
  assert.match(detail, /90 day/);
});

test('the interval comes from this subscription own price', () => {
  // Two months is stale on a monthly plan and recent on a yearly one.
  assert.equal(verdict(sub(60, { interval: 'year' }), NOW)[0], 'recent');
  assert.equal(verdict(sub(60, { interval: 'month' }), NOW)[0], 'stale');
});

test('only paused is this problem', () => {
  assert.equal(verdict(sub(90, { status: 'active' }), NOW)[0], 'not-paused');
});
''',
"faq": [
 ("How does a Stripe subscription end up in the paused status?",
  "One way only: a trial ends, the subscription has no payment method, and trial_settings.end_behavior.missing_payment_method is set to pause. Stripe then stops creating invoices and holds the subscription there. The other two settings for that field, create_invoice and cancel, produce dunning and a cancellation instead."),
 ("Does a paused subscription resume by itself?",
  "No. There is no timeout and no automatic exit. It stays paused until something updates it with a valid default payment method and clears pause_collection, and even then the status only changes once the invoice that update generates has been paid."),
 ("Is paused the same as setting pause_collection?",
  "No, and the confusion is the reason both get missed. pause_collection is a field you set on any subscription and it leaves the status untouched, usually active. The paused status is reachable only from a trial ending without a card. A check for one finds nothing about the other."),
 ("Should a paused subscription keep its product access?",
  "No. Nothing is being invoiced, so nothing is being paid for. Handle customer.subscription.paused by revoking access, and gate your entitlement check on status being active or trialing rather than on it not being canceled."),
 ("Can I find these with a read-only key?",
  "Yes. Read access to Subscriptions lists them and read access to Customers lets you expand data.customer to see whether a card turned up since. Neither permission can move money or change a subscription."),
],
"related": [
 ("/stripe/trial-ends-without-payment-method/", "Trials ending in days with no card on file"),
 ("/stripe/pause-collection-left-on-indefinitely/", "pause_collection with no resumes_at silently bills nothing"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
],
"citations": [CITE_SUB_OVERVIEW, CITE_TRIALS, CITE_SUB_OBJ, CITE_PAUSE],
},

{
"slug": "pause-collection-left-on-indefinitely",
"title": "pause_collection with no resumes_at silently bills nothing",
"description": "A support grace period sets pause_collection and never sets resumes_at. The subscription still reads active, and no money has arrived from it since.",
"h1": "pause_collection with no resumes_at silently bills nothing",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe pause_collection", "stripe pause payment collection",
             "subscription active but not billing", "pause_collection resumes_at",
             "stripe keep_as_draft invoices"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One customer had a bad month, support paused their billing for a while, and everybody moved on. That was in February. The subscription still reads <code>active</code> in every report you have, it still shows up in the subscriber count, and it has not produced a single invoice since.",
"short_answer": """<p>Read <code>GET /v1/subscriptions?status=active&amp;limit=100</code> and flag any row where <code>pause_collection</code> is not null and <code>pause_collection.resumes_at</code> is null. The status is deliberately unchanged by this field, so nothing else in your reporting will ever surface it.</p>
<p>Then read <code>pause_collection.behavior</code>, because it decides whether the missed periods are recoverable. <code>keep_as_draft</code> leaves invoices you can still finalise. <code>void</code> and <code>mark_uncollectible</code> throw each one away as it is created.</p>""",
"problem": """<p>The Stripe docs are explicit that pausing collection does not change the subscription's status. That is the whole design: the customer keeps their access, the subscription keeps its schedule, and only the collection is suspended. It is exactly what you want for a two-week grace period.</p>
<p>It is also why nothing catches it when the two weeks never end. <code>status</code> is <code>active</code>, so it is in the active-subscriber count. Nothing is <code>past_due</code>, so it is in no dunning report. No payment failed, so no failure event fired. The only visible symptom is an absence: money that should be arriving and is not, spread thinly enough across one customer at a time to look like nothing.</p>
<p><code>resumes_at</code> is optional, and omitting it means "until a human says otherwise". A support agent handling a refund request has no reason to think about a date three months out, and the API does not ask them to.</p>""",
"why": """<p><strong>The grace period is granted by whoever is on shift and owned by nobody.</strong> The pause is a response to a conversation. There is no ticket for un-pausing it, because un-pausing was never an action anyone planned to take &mdash; it was assumed to be the default that time would restore.</p>
<p><strong>The behaviour decides how much you lose, and it is chosen once and forgotten.</strong> With <code>keep_as_draft</code>, every skipped period leaves a draft invoice you can still finalise with <code>auto_advance=true</code>, so the money is merely delayed. With <code>void</code> or <code>mark_uncollectible</code>, Stripe disposes of each invoice as it is created and those periods are gone. Same pause, same duration, entirely different bill at the end.</p>
<p><strong>It is invisible in the Dashboard list too.</strong> The subscriptions list shows the status column, and the status is <code>active</code>. You have to open the individual subscription to see the paused banner, which means you have to already suspect the subscription you are opening.</p>
<p><strong>A <code>resumes_at</code> in the past is a different bug.</strong> When the date is set, Stripe resumes on it. A pause still in place with a resume date behind it means something is holding it there, and it deserves a look rather than being lumped in with the indefinite ones.</p>""",
"steps": [
 {"h": "Page the active subscriptions and read one field",
  "body": """<p><code>GET /v1/subscriptions?status=active&amp;limit=100</code>. <code>pause_collection</code> is on the subscription object, so no expansion is needed. Page all of them: these are single customers scattered through a list, not a cluster.</p>"""},
 {"h": "Split on resumes_at",
  "body": """<p>Null is the finding. A future timestamp is a pause with an end and needs nothing from you. A timestamp in the past with the pause still applied is its own oddity and worth surfacing separately rather than counting as healthy.</p>"""},
 {"h": "Read the behavior to know what is recoverable",
  "body": """<p><code>keep_as_draft</code> means the invoices exist and are collectable. <code>void</code> and <code>mark_uncollectible</code> mean they were disposed of on creation. Confirm with <code>GET /v1/invoices?subscription={sub}&amp;status=draft</code>, or <code>status=void</code> if the behavior says so.</p>"""},
 {"h": "Resume collection",
  "body": """<p><code>POST /v1/subscriptions/{sub}</code> with <code>pause_collection=</code> and an empty value clears it. Then, for each stranded draft, <code>POST /v1/invoices/{inv}</code> with <code>auto_advance=true</code> so Stripe starts collecting on it again.</p>"""},
 {"h": "Make resumes_at mandatory in whatever tool support uses",
  "body": """<p>Always send <code>pause_collection[resumes_at]</code> with a real timestamp. A pause that expires on its own is a grace period; a pause without one is a decision to stop billing a customer that nobody has written down anywhere.</p>"""},
],
"verify": """<p>Re-run the script. Any remaining pauses should carry a future <code>resumes_at</code>.</p>
<pre><code class="language-bash">python3 stripe_pause_collection.py
# 412 active subscription(s), 0 paused indefinitely, 2 scheduled to resume</code></pre>""",
"code_intro": "One GET over the active subscriptions and no writes at all &mdash; a restricted key with read access to Subscriptions is the whole requirement. The classifier is pure and takes the subscription and the current time, so the four outcomes it separates are readable side by side: no pause, a pause with an end, a pause whose end has already gone by, and the indefinite one, split by whether its behaviour leaves anything to collect.",
"py_file": "stripe_pause_collection.py",
"py": '''"""Report subscriptions left with pause_collection and no resumes_at.

Read only. One GET, no writes: give this a RESTRICTED key with read access to
Subscriptions. The repair is printed, never performed, because this script holds
a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_pause_collection")

API = "https://api.stripe.com/v1"
DAY = 86400

# Behaviours that dispose of the invoice as it is created. keep_as_draft, the
# remaining one, leaves something you can still finalise.
DISCARDING = ("void", "mark_uncollectible")


def verdict(sub, now):
    """Classify one subscription's pause_collection. Pure, so it can be tested.

    Note this never reads `status`: pause_collection leaves the status alone,
    which is exactly why the field needs a check of its own.
    Returns (state, detail).
    """
    pause = sub.get("pause_collection")
    if not pause:
        return ("collecting", "no pause on this subscription")

    behavior = pause.get("behavior") or "keep_as_draft"
    resumes = pause.get("resumes_at")

    if resumes is None:
        if behavior in DISCARDING:
            return ("unrecoverable",
                    "paused with no resumes_at and behavior %s: every invoice for "
                    "a paused period is disposed of as it is created" % behavior)
        return ("indefinite",
                "paused with no resumes_at and behavior %s: invoices accumulate "
                "as drafts that nothing will finalise" % behavior)

    if resumes <= now:
        return ("overdue",
                "resumes_at passed %d day(s) ago and collection is still paused"
                % ((now - resumes) // DAY))
    return ("scheduled",
            "resumes in %d day(s); this pause has an end" % ((resumes - now) // DAY))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def active_subscriptions(session, limit):
    out = []
    params = {"status": "active", "limit": 100}
    while True:
        page = get(session, "/subscriptions", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=5000,
                    help="stop after this many active subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    subs = active_subscriptions(s, args.max_subscriptions)
    now = int(time.time())
    counts = {}
    for sub in subs:
        state, detail = verdict(sub, now)
        counts[state] = counts.get(state, 0) + 1
        if state in ("collecting", "scheduled"):
            continue
        log.warning("%-13s %s  %s", state, sub["id"], detail)
        log.warning("  repair: POST %s/subscriptions/%s -d pause_collection=",
                    API, sub["id"])
        if state == "indefinite":
            log.warning("  then per draft: POST %s/invoices/{inv} "
                        "-d auto_advance=true", API)

    indefinite = counts.get("indefinite", 0) + counts.get("unrecoverable", 0)
    log.info("%d active subscription(s), %d paused indefinitely, %d scheduled "
             "to resume", len(subs), indefinite, counts.get("scheduled", 0))
    if counts.get("overdue"):
        log.info("%d still paused past their own resumes_at", counts["overdue"])
    return 1 if indefinite or counts.get("overdue") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-pause-collection.mjs",
"js": '''/**
 * Report subscriptions left with pause_collection and no resumes_at.
 *
 * Read only. One GET, no writes: give this a RESTRICTED key with read access to
 * Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;

// Behaviours that dispose of the invoice as it is created. keep_as_draft, the
// remaining one, leaves something you can still finalise.
const DISCARDING = new Set(['void', 'mark_uncollectible']);

/**
 * Classify one subscription's pause_collection. Pure, so it can be tested.
 * Never reads `status`: pause_collection leaves the status alone, which is
 * exactly why the field needs a check of its own.
 */
export function verdict(sub, now) {
  const pause = sub.pause_collection;
  if (!pause) return ['collecting', 'no pause on this subscription'];

  const behavior = pause.behavior ?? 'keep_as_draft';
  const resumes = pause.resumes_at ?? null;

  if (resumes === null) {
    if (DISCARDING.has(behavior)) {
      return ['unrecoverable',
        `paused with no resumes_at and behavior ${behavior}: every invoice for ` +
        'a paused period is disposed of as it is created'];
    }
    return ['indefinite',
      `paused with no resumes_at and behavior ${behavior}: invoices accumulate ` +
      'as drafts that nothing will finalise'];
  }

  if (resumes <= now) {
    return ['overdue',
      `resumes_at passed ${Math.floor((now - resumes) / DAY)} day(s) ago and ` +
      'collection is still paused'];
  }
  return ['scheduled',
    `resumes in ${Math.floor((resumes - now) / DAY)} day(s); this pause has an end`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function activeSubscriptions(key, limit = 5000) {
  const out = [];
  const params = { status: 'active', limit: 100 };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) break;
    params.starting_after = data[data.length - 1].id;
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

  const subs = await activeSubscriptions(key);
  const now = Math.floor(Date.now() / 1000);
  const counts = new Map();
  for (const sub of subs) {
    const [state, detail] = verdict(sub, now);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'collecting' || state === 'scheduled') continue;
    console.warn(`${state.padEnd(13)} ${sub.id}  ${detail}`);
    console.warn(`  repair: POST ${API}/subscriptions/${sub.id} -d pause_collection=`);
    if (state === 'indefinite') {
      console.warn(`  then per draft: POST ${API}/invoices/{inv} -d auto_advance=true`);
    }
  }

  const indefinite = (counts.get('indefinite') ?? 0) + (counts.get('unrecoverable') ?? 0);
  console.log(`${subs.length} active subscription(s), ${indefinite} paused ` +
              `indefinitely, ${counts.get('scheduled') ?? 0} scheduled to resume`);
  if (counts.get('overdue')) {
    console.log(`${counts.get('overdue')} still paused past their own resumes_at`);
  }
  process.exitCode = (indefinite || counts.get('overdue')) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The split that earns its own state is <code>behavior</code>. Two subscriptions paused on the same day for the same length of time produce a recoverable pile of drafts under <code>keep_as_draft</code> and nothing at all under <code>void</code>, so collapsing them into one finding would tell you to go and collect invoices that no longer exist. The tests also cover the omitted <code>behavior</code>, which is <code>keep_as_draft</code> rather than a reason to skip the row.",
"test_py_file": "test_stripe_pause_collection.py",
"test_py": '''from stripe_pause_collection import verdict

NOW = 1_800_000_000
DAY = 86400


def test_no_pause_is_collecting():
    assert verdict({"id": "sub_1"}, NOW)[0] == "collecting"
    assert verdict({"id": "sub_1", "pause_collection": None}, NOW)[0] == "collecting"


def test_indefinite_keep_as_draft_leaves_something_to_collect():
    state, detail = verdict(
        {"pause_collection": {"behavior": "keep_as_draft", "resumes_at": None}}, NOW)
    assert state == "indefinite"
    assert "drafts" in detail


def test_indefinite_void_throws_the_invoices_away():
    # Same pause, same duration, nothing left to finalise at the end of it.
    state, _ = verdict(
        {"pause_collection": {"behavior": "void", "resumes_at": None}}, NOW)
    assert state == "unrecoverable"


def test_a_future_resumes_at_is_a_pause_with_an_end():
    state, _ = verdict(
        {"pause_collection": {"behavior": "void", "resumes_at": NOW + 14 * DAY}}, NOW)
    assert state == "scheduled"


def test_a_past_resumes_at_still_paused_is_its_own_oddity():
    state, detail = verdict(
        {"pause_collection": {"behavior": "keep_as_draft",
                              "resumes_at": NOW - 30 * DAY}}, NOW)
    assert state == "overdue"
    assert "30 day(s)" in detail
''',
"test_js_file": "stripe-pause-collection.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-pause-collection.mjs';

const NOW = 1800000000;
const DAY = 86400;

test('no pause is collecting', () => {
  assert.equal(verdict({ id: 'sub_1' }, NOW)[0], 'collecting');
  assert.equal(verdict({ id: 'sub_1', pause_collection: null }, NOW)[0], 'collecting');
});

test('indefinite keep_as_draft leaves something to collect', () => {
  const [state, detail] = verdict(
    { pause_collection: { behavior: 'keep_as_draft', resumes_at: null } }, NOW);
  assert.equal(state, 'indefinite');
  assert.match(detail, /drafts/);
});

test('indefinite void throws the invoices away', () => {
  // Same pause, same duration, nothing left to finalise at the end of it.
  assert.equal(
    verdict({ pause_collection: { behavior: 'void', resumes_at: null } }, NOW)[0],
    'unrecoverable');
});

test('a future resumes_at is a pause with an end', () => {
  assert.equal(
    verdict({ pause_collection: { behavior: 'void', resumes_at: NOW + 14 * DAY } },
      NOW)[0],
    'scheduled');
});

test('a past resumes_at still paused is its own oddity', () => {
  const [state, detail] = verdict(
    { pause_collection: { behavior: 'keep_as_draft', resumes_at: NOW - 30 * DAY } },
    NOW);
  assert.equal(state, 'overdue');
  assert.match(detail, /30 day/);
});
''',
"faq": [
 ("Does pause_collection change the subscription status?",
  "No. The docs are explicit that the status is unchanged, which is the point of the feature and also why it goes unnoticed. A paused subscription usually still reads active, so it stays in the subscriber count and appears in no dunning or past-due report."),
 ("What happens to invoices while collection is paused?",
  "It depends on pause_collection.behavior. keep_as_draft leaves a draft invoice for each period, which you can still finalise later. void and mark_uncollectible dispose of each invoice as it is created, so those periods cannot be billed afterwards."),
 ("How do I resume collection?",
  "POST /v1/subscriptions/{id} with pause_collection set to an empty value clears it. If the behavior was keep_as_draft, the accumulated drafts stay drafts until you send each one auto_advance=true, so resuming the subscription alone does not collect the backlog."),
 ("Why should resumes_at always be set?",
  "Because it turns a pause into a grace period. With a timestamp, Stripe resumes collection on that date without anyone remembering to. Without one, the pause lasts until a human notices, and the only signal that a human should notice is money quietly not arriving."),
 ("What does it mean if resumes_at is in the past and collection is still paused?",
  "Something re-applied the pause or the update never took. It is not the same finding as an indefinite pause, so the script reports it separately rather than counting it as healthy just because a date is present."),
],
"related": [
 ("/stripe/paused-subscriptions-never-resumed/", "paused subscriptions never resume and never invoice again"),
 ("/stripe/draft-invoices-never-finalized/", "Draft invoices that never finalized"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access forever"),
],
"citations": [CITE_PAUSE, CITE_SUB_OBJ, CITE_INVOICE_OBJ, CITE_SUB_OVERVIEW],
},

{
"slug": "cancel-at-period-end-churn-backlog",
"title": "Active subscriptions already committed to cancel at period end",
"description": "cancel_at_period_end leaves the status active until the renewal date, so committed churn is invisible to every dashboard built on subscription status.",
"h1": "active subscriptions already committed to cancel at period end",
"category": "Stripe",
"pill": "Diagnostic",
"chips": CHIPS,
"keywords": ["stripe cancel_at_period_end", "pending churn stripe",
             "subscription scheduled to cancel", "stripe churn not showing",
             "cancel at period end report"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "MRR is flat, the active-subscriber count is flat, and nothing in the billing data looks wrong. A month from now a fifth of it disappears in a week. The cancellations already happened; they just have not taken effect yet, and no report you have distinguishes a subscription that will renew from one that will not.",
"short_answer": """<p>Page <code>GET /v1/subscriptions?status=active&amp;limit=100</code> and count the rows where <code>cancel_at_period_end</code> is <code>true</code> or <code>cancel_at</code> is set. Divide by the total and you have a pending-churn rate, which is a number nobody has because the status column does not carry it.</p>
<p>Then bucket by <code>items.data[0].current_period_end</code> to find the cliff, and read <code>cancellation_details.feedback</code> for why. Do not use <code>canceled_at</code> for the date: it records when the flag was set, not when service ends.</p>""",
"problem": """<p><code>cancel_at_period_end=true</code> is a scheduled deletion that leaves everything else alone. The status stays <code>active</code> until the period boundary, the invoice for the current period is already paid, and the customer keeps full access. Every property a dashboard queries on says this is a healthy subscription right up until the day it is gone.</p>
<p>So the churn is fully committed and entirely unrecorded. The decision was made when the customer clicked cancel; the number moves weeks later. In the gap, the growth chart is describing a company that no longer exists.</p>
<p>The date arithmetic makes it worse. <code>canceled_at</code> is populated the moment the flag is set, which reads like a cancellation date and is not one. An analysis that groups by <code>canceled_at</code> puts the churn in the wrong month in one direction and an analysis that ignores the flag entirely puts it in the wrong month in the other.</p>""",
"why": """<p><strong>The billing portal makes cancelling easy and makes it invisible.</strong> A customer cancels in the portal, the subscription is flagged, and unless something is listening for the flag flipping on <code>customer.subscription.updated</code>, the only record is a boolean on an object nobody re-reads.</p>
<p><strong>Everything downstream is keyed on status.</strong> Entitlement checks, seat counts, revenue reports, the sales team's account list. All of them ask what the status is, all of them get <code>active</code>, and all of them are correct about today and wrong about next month.</p>
<p><strong>The reason for the cancellation is captured only if it was configured.</strong> <code>cancellation_details.feedback</code> and <code>comment</code> are populated by the billing portal when <code>subscription_cancel.cancellation_reason</code> is enabled in the portal configuration. If it was never turned on, the backlog tells you how much you are losing and nothing at all about why.</p>
<p><strong>It is reversible until it is not.</strong> Setting <code>cancel_at_period_end=false</code> before the boundary restores the subscription completely, with no new signup and no re-entry of card details. After the boundary the subscription is <code>canceled</code> and the customer has to start again. The window is the whole opportunity, and it closes on a date the flag does not advertise.</p>""",
"steps": [
 {"h": "Count the flag across every active subscription",
  "body": """<p>Page the whole list. <code>cancel_at_period_end</code> is on the subscription object, and <code>cancel_at</code> catches the ones scheduled for a specific date rather than a period boundary. Both are pending churn.</p>"""},
 {"h": "Express it as a rate, not a count",
  "body": """<p>Scheduled divided by total active. A count means nothing without the denominator; a rate is comparable week to week and is the version of this number that belongs on a dashboard.</p>"""},
 {"h": "Find the nearest cliff",
  "body": """<p>Bucket by <code>items.data[0].current_period_end</code>, falling back to <code>cancel_at</code>. Fifty cancellations spread over a year is attrition. Fifty landing in the same week is an incident, usually a price change or an outage, and it needs an answer before that week.</p>"""},
 {"h": "Read the reasons if you have them",
  "body": """<p><code>cancellation_details.feedback</code> takes values like <code>too_expensive</code>, <code>missing_features</code> and <code>switched_service</code>. If every row is null, enable <code>subscription_cancel.cancellation_reason</code> on the portal configuration so the next cohort tells you something.</p>"""},
 {"h": "Reverse the ones worth reversing, and watch the flag from now on",
  "body": """<p><code>POST /v1/subscriptions/{sub}</code> with <code>cancel_at_period_end=false</code> reinstates a subscription with no re-signup. Structurally, trigger a save offer from <code>customer.subscription.updated</code> when the flag flips, on the day it flips, rather than finding it in a quarterly review.</p>"""},
],
"verify": """<p>Re-run the script. The pending-churn rate is the number you want on a dashboard, and the nearest cliff is the one you want on a calendar.</p>
<pre><code class="language-bash">python3 stripe_pending_churn.py
# backlog   7 of 412 active subscriptions (1.7%) are scheduled to cancel</code></pre>""",
"code_intro": "One paged GET over the active subscriptions and no writes; read access to Subscriptions is all the key needs. The classifier is pure and takes three numbers &mdash; how many are scheduled, how many are active in total, and how many days until the soonest one ends &mdash; because a low rate with a cliff next week and a high rate spread over a year are different findings and the count alone cannot tell them apart.",
"py_file": "stripe_pending_churn.py",
"py": '''"""Report active subscriptions already scheduled to cancel, as a rate and a date.

Read only. One GET, no writes: give this a RESTRICTED key with read access to
Subscriptions. The repair is printed, never performed, because this script holds
a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_pending_churn")

API = "https://api.stripe.com/v1"
DAY = 86400

ELEVATED_RATE = 0.10   # scheduled / active above this is a trend, not attrition
CLIFF_DAYS = 7         # a cancellation this close needs an answer this week


def scheduled_end(sub):
    """When service actually ends, or None if it is not scheduled to.

    Deliberately not `canceled_at`: that is populated when the flag is set, not
    when the subscription stops, and grouping by it dates the churn wrongly.
    """
    if sub.get("cancel_at"):
        return sub["cancel_at"]
    if not sub.get("cancel_at_period_end"):
        return None
    items = (sub.get("items") or {}).get("data") or []
    if items and items[0].get("current_period_end"):
        return items[0]["current_period_end"]
    return sub.get("current_period_end")


def verdict(scheduled, active_total, soonest_days):
    """Classify a pending-churn backlog. Pure, so the rules can be tested.

    `soonest_days` is days until the nearest scheduled end, or None if nothing
    is scheduled. Returns (state, detail).
    """
    if not active_total:
        return ("empty", "no active subscriptions in this account and mode")
    if not scheduled:
        return ("clear", "%d active subscription(s), none scheduled to cancel"
                % active_total)

    rate = scheduled / active_total
    summary = ("%d of %d active subscription(s) (%.1f%%) are scheduled to cancel"
               % (scheduled, active_total, rate * 100))

    if soonest_days is not None and soonest_days <= CLIFF_DAYS:
        return ("imminent",
                "%s, the first in %d day(s)" % (summary, soonest_days))
    if rate >= ELEVATED_RATE:
        return ("elevated",
                "%s. Above %d%% this is a trend with a cause, not attrition."
                % (summary, int(ELEVATED_RATE * 100)))
    return ("backlog", summary)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def active_subscriptions(session, limit):
    out = []
    params = {"status": "active", "limit": 100}
    while True:
        page = get(session, "/subscriptions", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=5000,
                    help="stop after this many active subscriptions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    subs = active_subscriptions(s, args.max_subscriptions)
    now = int(time.time())

    ends = []
    reasons = {}
    for sub in subs:
        end = scheduled_end(sub)
        if end is None:
            continue
        ends.append(end)
        why = (sub.get("cancellation_details") or {}).get("feedback") or "not captured"
        reasons[why] = reasons.get(why, 0) + 1

    soonest = int((min(ends) - now) // DAY) if ends else None
    state, detail = verdict(len(ends), len(subs), soonest)

    if state in ("clear", "empty"):
        log.info("%-9s %s", state, detail)
        return 0

    log.warning("%-9s %s", state, detail)
    log.warning("  reasons: %s",
                ", ".join("%s x%d" % (k, v) for k, v in sorted(reasons.items())))
    if reasons.get("not captured"):
        log.warning("  repair: enable subscription_cancel.cancellation_reason on the "
                    "billing portal configuration so reasons are recorded")
    log.warning("  repair: per salvageable subscription, POST %s/subscriptions/{sub} "
                "-d cancel_at_period_end=false", API)
    log.warning("  repair: trigger the save offer from customer.subscription.updated "
                "on the day the flag flips")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-pending-churn.mjs",
"js": '''/**
 * Report active subscriptions already scheduled to cancel, as a rate and a date.
 *
 * Read only. One GET, no writes: give this a RESTRICTED key with read access to
 * Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;

const ELEVATED_RATE = 0.10;  // scheduled / active above this is a trend
const CLIFF_DAYS = 7;        // a cancellation this close needs an answer this week

/**
 * When service actually ends, or null if it is not scheduled to.
 * Deliberately not `canceled_at`: that is populated when the flag is set.
 */
export function scheduledEnd(sub) {
  if (sub.cancel_at) return sub.cancel_at;
  if (!sub.cancel_at_period_end) return null;
  const items = sub.items?.data ?? [];
  if (items.length > 0 && items[0].current_period_end) {
    return items[0].current_period_end;
  }
  return sub.current_period_end ?? null;
}

/** Classify a pending-churn backlog. Pure, so the rules can be tested. */
export function verdict(scheduled, activeTotal, soonestDays) {
  if (!activeTotal) return ['empty', 'no active subscriptions in this account and mode'];
  if (!scheduled) {
    return ['clear', `${activeTotal} active subscription(s), none scheduled to cancel`];
  }

  const rate = scheduled / activeTotal;
  const summary = `${scheduled} of ${activeTotal} active subscription(s) ` +
    `(${(rate * 100).toFixed(1)}%) are scheduled to cancel`;

  if (soonestDays !== null && soonestDays !== undefined && soonestDays <= CLIFF_DAYS) {
    return ['imminent', `${summary}, the first in ${soonestDays} day(s)`];
  }
  if (rate >= ELEVATED_RATE) {
    return ['elevated',
      `${summary}. Above ${Math.round(ELEVATED_RATE * 100)}% this is a trend ` +
      'with a cause, not attrition.'];
  }
  return ['backlog', summary];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error(`403 from Stripe: the restricted key lacks read access to ${path}`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function activeSubscriptions(key, limit = 5000) {
  const out = [];
  const params = { status: 'active', limit: 100 };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) break;
    params.starting_after = data[data.length - 1].id;
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

  const subs = await activeSubscriptions(key);
  const now = Math.floor(Date.now() / 1000);

  const ends = [];
  const reasons = new Map();
  for (const sub of subs) {
    const end = scheduledEnd(sub);
    if (end === null) continue;
    ends.push(end);
    const why = sub.cancellation_details?.feedback ?? 'not captured';
    reasons.set(why, (reasons.get(why) ?? 0) + 1);
  }

  const soonest = ends.length > 0
    ? Math.floor((Math.min(...ends) - now) / DAY) : null;
  const [state, detail] = verdict(ends.length, subs.length, soonest);

  if (state === 'clear' || state === 'empty') {
    console.log(`${state.padEnd(9)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(9)} ${detail}`);
  const listed = [...reasons.entries()].sort().map(([k, v]) => `${k} x${v}`).join(', ');
  console.warn(`  reasons: ${listed}`);
  if (reasons.get('not captured')) {
    console.warn('  repair: enable subscription_cancel.cancellation_reason on the ' +
                 'billing portal configuration so reasons are recorded');
  }
  console.warn(`  repair: per salvageable subscription, POST ${API}/subscriptions/{sub} ` +
               '-d cancel_at_period_end=false');
  console.warn('  repair: trigger the save offer from customer.subscription.updated ' +
               'on the day the flag flips');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The ordering is the thing under test. A single cancellation landing in three days is a more urgent finding than fifty spread across the next year, so the date has to be checked before the rate; reverse the two and the one subscription you could still have saved is reported as a rounding error. The rest pins the empty account, which is not a clean bill of health, and the rate boundary itself.",
"test_py_file": "test_stripe_pending_churn.py",
"test_py": '''from stripe_pending_churn import scheduled_end, verdict


def test_an_imminent_cliff_outranks_a_low_rate():
    # One cancellation in three days beats sixty spread over a year.
    state, detail = verdict(1, 400, 3)
    assert state == "imminent"
    assert "3 day(s)" in detail


def test_a_high_rate_far_out_is_a_trend():
    state, _ = verdict(60, 400, 200)
    assert state == "elevated"


def test_a_handful_far_out_is_just_a_backlog():
    state, detail = verdict(8, 400, 200)
    assert state == "backlog"
    assert "2.0%" in detail


def test_no_active_subscriptions_is_not_a_clean_bill_of_health():
    state, _ = verdict(0, 0, None)
    assert state == "empty"


def test_the_end_date_comes_from_the_item_not_from_canceled_at():
    sub = {"cancel_at_period_end": True, "canceled_at": 1,
           "items": {"data": [{"current_period_end": 999}]}}
    assert scheduled_end(sub) == 999
    assert scheduled_end({"cancel_at_period_end": False, "canceled_at": 1}) is None
''',
"test_js_file": "stripe-pending-churn.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scheduledEnd, verdict } from './stripe-pending-churn.mjs';

test('an imminent cliff outranks a low rate', () => {
  // One cancellation in three days beats fifty spread over a year.
  const [state, detail] = verdict(1, 400, 3);
  assert.equal(state, 'imminent');
  assert.match(detail, /3 day/);
});

test('a high rate far out is a trend', () => {
  assert.equal(verdict(60, 400, 200)[0], 'elevated');
});

test('a handful far out is just a backlog', () => {
  const [state, detail] = verdict(8, 400, 200);
  assert.equal(state, 'backlog');
  assert.match(detail, /2.0%/);
});

test('no active subscriptions is not a clean bill of health', () => {
  assert.equal(verdict(0, 0, null)[0], 'empty');
});

test('the end date comes from the item not from canceled_at', () => {
  const sub = {
    cancel_at_period_end: true,
    canceled_at: 1,
    items: { data: [{ current_period_end: 999 }] },
  };
  assert.equal(scheduledEnd(sub), 999);
  assert.equal(scheduledEnd({ cancel_at_period_end: false, canceled_at: 1 }), null);
});
''',
"faq": [
 ("Why do subscriptions scheduled to cancel still show as active?",
  "Because cancel_at_period_end is a schedule, not a state change. The customer has paid for the current period and keeps access until it ends, so Stripe leaves the status as active until the boundary. The status becomes canceled only when service actually stops."),
 ("Can I undo cancel_at_period_end?",
  "Yes, at any point before the period ends: POST /v1/subscriptions/{id} with cancel_at_period_end=false restores it completely, with no new signup and no card re-entry. Once the boundary passes the subscription is canceled and the customer has to subscribe again."),
 ("Is canceled_at the date the subscription ends?",
  "No, and this trips up a lot of churn analysis. canceled_at is when the cancellation was requested, which is when the flag was set. The end of service is cancel_at, or the current period end on the subscription item. Grouping by canceled_at dates the churn to the wrong month."),
 ("Why is cancellation_details.feedback null on all my subscriptions?",
  "It is populated by the billing portal, and only when subscription_cancel.cancellation_reason is enabled on the portal configuration. Cancellations made through the API or the Dashboard without a reason leave it null. Turn it on and the next cohort explains itself."),
 ("What counts as a high pending-churn rate?",
  "There is no universal figure, which is why the rate matters more than the threshold: track it weekly and watch it move. As a starting point, a script that flags anything at or above ten percent of active subscriptions, or any cancellation landing within a week, catches both the trend and the cliff."),
],
"related": [
 ("/stripe/missing-subscription-deleted/", "customer.subscription.deleted is missing so access never ends"),
 ("/stripe/billing-portal-no-configuration/", "The billing portal has no configuration"),
 ("/stripe/unpaid-subscriptions-still-provisioned/", "unpaid subscriptions keep access and stop billing entirely"),
],
"citations": [CITE_SUB_OBJ, CITE_SUB_LIST, CITE_PORTAL_CONFIG, CITE_RETRIES],
},

]
