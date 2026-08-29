#!/usr/bin/env python3
"""/stripe/ field notes, batch G — the writing.

Same constraint as every other batch in this section: each note is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

Invoices and tax, where the read-only rule matters for a different reason than
usual: the repairs here move money or create a legal record. Finalizing an
invoice sends a bill to a customer, deleting a draft destroys it, and marking one
uncollectible writes off revenue. None of those should happen because a
classifier had an off-by-one in it.
"""

CITE_INVOICE_OBJ = ("The invoice object — Stripe API reference",
                    "https://docs.stripe.com/api/invoices/object")
CITE_INVOICE_LIST = ("List all invoices — Stripe API reference",
                     "https://docs.stripe.com/api/invoices/list")
CITE_WORKFLOW = ("Invoice workflow transitions — Stripe Docs",
                 "https://docs.stripe.com/invoicing/integration/workflow-transitions")
CITE_PAUSE = ("Pause payment collection — Stripe Docs",
              "https://docs.stripe.com/billing/subscriptions/pause-payment")
CITE_COLLECTION = ("Collection method — Stripe Docs",
                   "https://docs.stripe.com/billing/collection-method")
CITE_INVOICE_SEND = ("Send an invoice for manual payment — Stripe API reference",
                     "https://docs.stripe.com/api/invoices/send")
CITE_SMART_RETRIES = ("Smart Retries — Stripe Docs",
                      "https://docs.stripe.com/billing/revenue-recovery/smart-retries")
CITE_RECOVERY = ("Revenue recovery — Stripe Docs",
                 "https://docs.stripe.com/billing/revenue-recovery")
CITE_INVOICE_PAY = ("Pay an invoice — Stripe API reference",
                    "https://docs.stripe.com/api/invoices/pay")
CITE_TAX_INVOICING = ("Stripe Tax and invoicing — Stripe Docs",
                      "https://docs.stripe.com/tax/invoicing")
CITE_TAX_SETUP = ("Set up Stripe Tax — Stripe Docs",
                  "https://docs.stripe.com/tax/set-up")
CITE_SUB_LIST = ("List all subscriptions — Stripe API reference",
                 "https://docs.stripe.com/api/subscriptions/list")

GUIDES = [

{
"slug": "draft-invoices-never-finalized",
"title": "Draft invoices sit for months and never finalize",
"description": "A draft invoice has no number, no PDF and no hosted page, and Stripe will not collect on it. Read auto_advance and automatically_finalizes_at.",
"h1": "draft invoices sit for months and never finalize",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe draft invoice", "stripe auto_advance false",
             "automatically_finalizes_at null", "stripe invoice never finalized",
             "stripe finalize invoice"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody asks why the March figure is lower than the March that was forecast, and nobody can answer it from the Dashboard, because the money is not missing and it is not late. It is sitting in invoices that were built, itemised, priced correctly, and then never sent: no number, no PDF, no hosted page, no email. Stripe cannot collect on an invoice that has not been finalized, and these have been drafts since March.",
"short_answer": """<p>List <code>GET /v1/invoices?status=draft&amp;created[lt]=&lt;unix now-30d&gt;</code> and read three fields on every row. <code>auto_advance</code> says whether Stripe will ever finalize the invoice on its own. <code>automatically_finalizes_at</code> says when that is scheduled to happen. <code>amount_due</code> says what it is worth.</p>
<p>An old draft with <code>auto_advance: false</code> is not late, it is stranded: nothing inside Stripe will ever move it, and no amount of waiting changes that. One with <code>auto_advance: true</code> and <code>automatically_finalizes_at: null</code> has lost its schedule. One whose <code>automatically_finalizes_at</code> is already in the past is being blocked at finalization, and <code>last_finalization_error</code> will say by what.</p>""",
"problem": """<p>A draft invoice is a document, not a bill. It has no invoice number, no PDF, no <code>hosted_invoice_url</code> to send anyone, and Stripe explicitly will not attempt payment on it. From the customer's side nothing happened at all: they were never asked for the money, so they are not late paying it and no dunning, reminder or subscription state change will ever be triggered on their account.</p>
<p>This makes it the quietest revenue leak in a billing integration. Every other failure in this section leaves a trace somebody eventually trips over &mdash; a failed charge, a past_due subscription, an angry customer. A stranded draft produces no event, no email, no error and no support ticket. It shows up as a number in a report being smaller than it should be, which is exactly the class of problem that gets attributed to churn or seasonality for two quarters before anyone opens the invoice list and sorts by status.</p>""",
"why": """<p><strong>Automatic finalization is not a timer, it is a consequence.</strong> Stripe finalizes a draft roughly an hour after your endpoint acknowledges <code>invoice.created</code>, and defers for up to 72 hours while deliveries are failing. That is a deliberate courtesy &mdash; it gives you a window to add line items before the invoice becomes immutable &mdash; but it couples finalization to webhook health. A broken endpoint does not just cost you events; for three days it also holds up the billing.</p>
<p><strong><code>auto_advance: false</code> arrives without anyone choosing it.</strong> It is the default under <code>payment_behavior=default_incomplete</code>, it is what <code>pause_collection[behavior]=keep_as_draft</code> produces, and it is what subscriptions that went <code>unpaid</code> leave behind. Each of those is a reasonable state at the moment it is created. The failure is that none of them expire: a subscription paused in January is still generating drafts nobody will ever finalize in June.</p>
<p><strong>The list endpoint does not sort by what matters.</strong> Drafts come back newest first, and the newest drafts are the healthy ones an hour away from finalizing normally. The stranded ones are at the far end of the pagination, which is why a manual look at the Dashboard usually concludes everything is fine.</p>
<p><strong>Deleting is as valid a repair as finalizing, and nobody wants to decide.</strong> Half of these drafts should be billed and half should never have existed. Because the two look identical in a list, the whole pile gets left alone. <code>amount_due</code> and the age are what separate them, and both are in the API.</p>""",
"steps": [
 {"h": "List drafts older than 30 days, not all drafts",
  "body": """<p>Use <code>created[lt]</code> with a unix timestamp 30 days back. Everything younger is either finalizing normally or inside the 72-hour deferral window, and including it buries the real findings under noise. The cutoff is an argument on the script for a reason: a monthly biller may want 45 days, a daily one 7.</p>"""},
 {"h": "Read auto_advance before anything else",
  "body": """<p><code>false</code> means the invoice has opted out of Stripe's collection workflow entirely. No schedule exists for it and none will be created. This is the state to count first, because it is the only one where waiting is definitively not a strategy.</p>"""},
 {"h": "Treat a past automatically_finalizes_at as an error report",
  "body": """<p>If the scheduled time has passed and the invoice is still a draft, finalization was attempted and failed. <code>last_finalization_error</code> carries the reason, and the most common one on an account with Stripe Tax enabled is <code>customer_tax_location_invalid</code>: a customer with no resolvable address. That is a different repair from finalizing, and doing it in the wrong order just fails again.</p>"""},
 {"h": "Total amount_due before writing the ticket",
  "body": """<p>"Forty stranded drafts" gets triaged into next quarter. "Forty stranded drafts worth 61,400 in minor units" gets done this week. The sum is one addition over data you already fetched, and it is the only line of the report anyone outside the team will read.</p>"""},
 {"h": "Split the pile into collect and delete",
  "body": """<p><code>POST /v1/invoices/{id}/finalize</code> for the ones you intend to bill, or set <code>auto_advance=true</code> to hand the invoice back to Stripe's workflow. For the ones that should never have existed, drafts are the only invoices Stripe lets you delete. Do the deletions in a separate pass from the finalizations, because a finalized invoice cannot be taken back.</p>"""},
 {"h": "Check webhook health at the same time",
  "body": """<p>If drafts are piling up account-wide rather than for one paused subscription, look at the endpoints before the invoices. Three days of failing deliveries produce three days of drafts that look stranded and are merely deferred.</p>"""},
],
"verify": """<p>Re-run the script after the pass. What is left should be recent drafts with a finalization scheduled, and nothing older than the cutoff.</p>
<pre><code class="language-bash">python3 stripe_draft_invoices.py --older-than 30
# clear       0 draft invoice(s) older than 30 days</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/invoices</code> and nothing else &mdash; a restricted key with read access to Invoices is enough, and is what you should give it. The classifier is pure and takes four scalars, because the difference between <em>stranded</em>, <em>unscheduled</em> and <em>blocked</em> decides whether the repair is a finalize call, a field update, or a fix to the customer record, and getting that wrong wastes a day.",
"py_file": "stripe_draft_invoices.py",
"py": '''"""Report Stripe draft invoices that will never finalize on their own.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Invoices. The repair is printed, never performed, because finalizing an
invoice sends a bill to a customer and deleting one destroys it.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_draft_invoices")

API = "https://api.stripe.com/v1"

# Stripe finalizes about an hour after invoice.created is acknowledged, and
# defers up to 72 hours while endpoints are failing. Anything still a draft well
# past that is not waiting for the workflow, it is outside it.
STALE_DAYS = 30


def verdict(age_days, auto_advance, finalizes_in_days, amount_due):
    """Classify one draft invoice. Pure, so the rules can be tested without a network.

    `age_days` is how long the invoice has been a draft. `finalizes_in_days` is
    the time until `automatically_finalizes_at`, negative if that moment has
    already passed, and None when the field is null. Returns (state, detail).
    """
    if age_days < STALE_DAYS:
        return ("fresh",
                "draft for %.1f day(s); still inside the window where Stripe "
                "finalizes on its own" % age_days)
    if not amount_due:
        return ("empty",
                "draft for %.0f day(s) with amount_due 0: clutter rather than "
                "money, and safe to delete" % age_days)
    if not auto_advance:
        return ("stranded",
                "auto_advance is false after %.0f day(s): no finalization is "
                "scheduled and none will be" % age_days)
    if finalizes_in_days is None:
        return ("unscheduled",
                "auto_advance is true after %.0f day(s) but "
                "automatically_finalizes_at is null: nothing is queued" % age_days)
    if finalizes_in_days < 0:
        return ("blocked",
                "the scheduled finalization passed %.1f day(s) ago and this is "
                "still a draft: read last_finalization_error"
                % -finalizes_in_days)
    return ("scheduled",
            "finalizes in %.1f day(s); leave it alone" % finalizes_in_days)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def drafts(session, older_than_days, limit):
    """Page draft invoices created before the cutoff. Newest first, as Stripe sends them."""
    cutoff = int(time.time() - older_than_days * 86400)
    out = []
    params = {"status": "draft", "limit": 100, "created[lt]": cutoff}
    while True:
        page = get(session, "/invoices", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--older-than", type=float, default=STALE_DAYS,
                    help="only look at drafts created this many days ago or more")
    ap.add_argument("--top", type=int, default=20,
                    help="how many individual invoices to print")
    ap.add_argument("--max-invoices", type=int, default=2000,
                    help="stop paginating after this many drafts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    rows = []
    for inv in drafts(s, args.older_than, args.max_invoices):
        created = inv.get("created") or now
        finalizes_at = inv.get("automatically_finalizes_at")
        rows.append((
            inv.get("id", "<no id>"),
            verdict((now - created) / 86400.0,
                    bool(inv.get("auto_advance")),
                    None if finalizes_at is None else (finalizes_at - now) / 86400.0,
                    inv.get("amount_due") or 0),
            inv.get("amount_due") or 0,
            (inv.get("currency") or "").upper(),
        ))

    stuck = [r for r in rows
             if r[1][0] in ("stranded", "unscheduled", "blocked")]
    if not stuck:
        log.info("%-11s 0 draft invoice(s) older than %g days",
                 "clear", args.older_than)
        return 0

    at_stake = sum(r[2] for r in stuck)
    log.warning("%-11s %d stuck draft(s) worth %d in minor units",
                "stuck", len(stuck), at_stake)
    for inv_id, (state, detail), amount, currency in stuck[:args.top]:
        log.warning("  %-11s %s  %d %s  %s", state, inv_id, amount, currency, detail)
        if state == "blocked":
            log.warning("      GET %s/invoices/%s  and read last_finalization_error",
                        API, inv_id)
        else:
            log.warning("      POST %s/invoices/%s/finalize   to bill it", API, inv_id)
            log.warning("      POST %s/invoices/%s  auto_advance=true   to hand it "
                        "back to Stripe", API, inv_id)
    if len(stuck) > args.top:
        log.warning("  ... and %d more", len(stuck) - args.top)
    log.warning("  drafts you never intended to bill are the one kind of invoice "
                "Stripe lets you remove; do that in a separate pass")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-draft-invoices.mjs",
"js": '''/**
 * Report Stripe draft invoices that will never finalize on their own.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Stripe finalizes about an hour after invoice.created is acknowledged, and
// defers up to 72 hours while endpoints are failing. Anything still a draft well
// past that is not waiting for the workflow, it is outside it.
export const STALE_DAYS = 30;

/**
 * Classify one draft invoice. Pure, so the rules can be tested without a network.
 * `finalizesInDays` is negative when that moment has passed, null when the field is.
 */
export function verdict(ageDays, autoAdvance, finalizesInDays, amountDue) {
  if (ageDays < STALE_DAYS) {
    return ['fresh',
      `draft for ${ageDays.toFixed(1)} day(s); still inside the window where ` +
      'Stripe finalizes on its own'];
  }
  if (!amountDue) {
    return ['empty',
      `draft for ${ageDays.toFixed(0)} day(s) with amount_due 0: clutter rather ` +
      'than money, and safe to delete'];
  }
  if (!autoAdvance) {
    return ['stranded',
      `auto_advance is false after ${ageDays.toFixed(0)} day(s): no finalization ` +
      'is scheduled and none will be'];
  }
  if (finalizesInDays === null || finalizesInDays === undefined) {
    return ['unscheduled',
      `auto_advance is true after ${ageDays.toFixed(0)} day(s) but ` +
      'automatically_finalizes_at is null: nothing is queued'];
  }
  if (finalizesInDays < 0) {
    return ['blocked',
      `the scheduled finalization passed ${(-finalizesInDays).toFixed(1)} day(s) ` +
      'ago and this is still a draft: read last_finalization_error'];
  }
  return ['scheduled',
    `finalizes in ${finalizesInDays.toFixed(1)} day(s); leave it alone`];
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

export async function drafts(key, olderThanDays = STALE_DAYS, limit = 2000) {
  const cutoff = Math.floor(Date.now() / 1000 - olderThanDays * 86400);
  const out = [];
  const params = { status: 'draft', limit: 100, 'created[lt]': cutoff };
  for (;;) {
    const page = await get(key, '/invoices', params);
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

  const olderThan = Number(process.argv[2] ?? STALE_DAYS);
  const now = Date.now() / 1000;
  const rows = (await drafts(key, olderThan)).map((inv) => {
    const created = inv.created ?? now;
    const at = inv.automatically_finalizes_at;
    return {
      id: inv.id ?? '<no id>',
      amount: inv.amount_due ?? 0,
      currency: (inv.currency ?? '').toUpperCase(),
      state: verdict((now - created) / 86400,
        Boolean(inv.auto_advance),
        at === null || at === undefined ? null : (at - now) / 86400,
        inv.amount_due ?? 0),
    };
  });

  const stuck = rows.filter((r) => ['stranded', 'unscheduled', 'blocked'].includes(r.state[0]));
  if (stuck.length === 0) {
    console.log(`${'clear'.padEnd(11)} 0 draft invoice(s) older than ${olderThan} days`);
    return;
  }

  const atStake = stuck.reduce((a, r) => a + r.amount, 0);
  console.warn(`${'stuck'.padEnd(11)} ${stuck.length} stuck draft(s) worth ${atStake} in minor units`);
  for (const r of stuck.slice(0, 20)) {
    const [state, detail] = r.state;
    console.warn(`  ${state.padEnd(11)} ${r.id}  ${r.amount} ${r.currency}  ${detail}`);
    if (state === 'blocked') {
      console.warn(`      GET ${API}/invoices/${r.id}  and read last_finalization_error`);
    } else {
      console.warn(`      POST ${API}/invoices/${r.id}/finalize   to bill it`);
      console.warn(`      POST ${API}/invoices/${r.id}  auto_advance=true   to hand it back to Stripe`);
    }
  }
  if (stuck.length > 20) console.warn(`  ... and ${stuck.length - 20} more`);
  console.warn('  drafts you never intended to bill are the one kind of invoice ' +
               'Stripe lets you remove; do that in a separate pass');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests fix the order of the rules, which is the part that actually decides what a human does next. A zero-value draft is checked before <code>auto_advance</code>, because there is no point routing an empty invoice to someone to finalize; a past <code>automatically_finalizes_at</code> is checked last, because it means something tried and failed rather than never started.",
"test_py_file": "test_stripe_draft_invoices.py",
"test_py": '''from stripe_draft_invoices import verdict


def test_recent_drafts_are_not_a_finding():
    # Everything under the cutoff is either finalizing normally or inside the
    # 72-hour deferral window. Reporting those buries the real ones.
    assert verdict(29.9, False, None, 5000)[0] == "fresh"
    assert verdict(30.0, False, None, 5000)[0] == "stranded"


def test_auto_advance_false_is_stranded_not_late():
    state, detail = verdict(90.0, False, None, 12000)
    assert state == "stranded"
    assert "none will be" in detail


def test_zero_amount_is_clutter_before_it_is_stranded():
    # Checked ahead of auto_advance on purpose: nobody should be asked to
    # finalize an invoice worth nothing.
    assert verdict(90.0, False, None, 0)[0] == "empty"


def test_auto_advance_true_with_no_schedule_is_unscheduled():
    state, _ = verdict(45.0, True, None, 8000)
    assert state == "unscheduled"


def test_a_past_finalization_time_means_it_failed():
    state, detail = verdict(45.0, True, -3.0, 8000)
    assert state == "blocked"
    assert "last_finalization_error" in detail


def test_a_future_finalization_time_is_left_alone():
    assert verdict(45.0, True, 0.5, 8000)[0] == "scheduled"
''',
"test_js_file": "stripe-draft-invoices.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-draft-invoices.mjs';

test('recent drafts are not a finding', () => {
  assert.equal(verdict(29.9, false, null, 5000)[0], 'fresh');
  assert.equal(verdict(30.0, false, null, 5000)[0], 'stranded');
});

test('auto_advance false is stranded, not late', () => {
  const [state, detail] = verdict(90.0, false, null, 12000);
  assert.equal(state, 'stranded');
  assert.match(detail, /none will be/);
});

test('zero amount is clutter before it is stranded', () => {
  assert.equal(verdict(90.0, false, null, 0)[0], 'empty');
});

test('auto_advance true with no schedule is unscheduled', () => {
  assert.equal(verdict(45.0, true, null, 8000)[0], 'unscheduled');
});

test('a past finalization time means it failed', () => {
  const [state, detail] = verdict(45.0, true, -3.0, 8000);
  assert.equal(state, 'blocked');
  assert.match(detail, /last_finalization_error/);
});

test('a future finalization time is left alone', () => {
  assert.equal(verdict(45.0, true, 0.5, 8000)[0], 'scheduled');
});
''',
"faq": [
 ("Can a draft invoice be paid?",
  "No. Stripe will not attempt payment on an invoice that has not been finalized, and there is no hosted page or PDF for a customer to pay from because those are created at finalization along with the invoice number. A draft is a document, not a bill."),
 ("Why is auto_advance false when I never set it?",
  "Several ordinary paths set it for you. payment_behavior=default_incomplete leaves the first invoice with auto_advance false, pause_collection[behavior]=keep_as_draft produces drafts by design, and subscriptions that reached unpaid stop advancing their invoices. None of those states expires on its own, so the drafts keep accumulating after the reason for them has gone."),
 ("Does a broken webhook endpoint really delay billing?",
  "For up to 72 hours, yes. Stripe waits for successful delivery of invoice.created before finalizing, so that you can add line items first, and gives up waiting after three days. If drafts are piling up across the whole account rather than on one subscription, check endpoint health before you touch the invoices."),
 ("Should I finalize these or delete them?",
  "Both, in separate passes. Drafts are the only invoices Stripe permits deleting, which makes deletion the honest way to clear ones that should never have existed. Finalizing is irreversible and sends a real bill, so do that pass with a list you have actually read, not with a loop over the script's output."),
 ("Why filter on created[lt] rather than reading every draft?",
  "Because a healthy account always has recent drafts in flight, and they outnumber the stuck ones. Stripe returns newest first, so without the cutoff the findings you want are at the end of the pagination, underneath every invoice that is about to finalize normally."),
],
"related": [
 ("/stripe/open-invoices-past-due-date/", "Open invoices are weeks past due_date and nobody chases"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access forever"),
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
],
"citations": [CITE_WORKFLOW, CITE_INVOICE_OBJ, CITE_INVOICE_LIST, CITE_PAUSE],
},

{
"slug": "open-invoices-past-due-date",
"title": "Open invoices are weeks past due_date and nobody chases",
"description": "send_invoice bills do not auto-charge. Reminders are an opt-in Dashboard setting, so an overdue invoice can sit at open indefinitely with no follow-up.",
"h1": "open invoices are weeks past due_date and nobody chases",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe invoice past due", "stripe due_date overdue",
             "stripe send_invoice not paid", "stripe invoice reminders",
             "stripe accounts receivable"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Invoiced customers pay when they are asked twice. The integration asks once: Stripe emails the invoice on finalization and then waits, because that is what <code>collection_method=send_invoice</code> means. Nobody enabled the reminder emails, so an invoice that went out in April is still sitting at <code>open</code> in July, and the customer's subscription never noticed.",
"short_answer": """<p>List <code>GET /v1/invoices?status=open&amp;collection_method=send_invoice</code> and filter client side on <code>due_date</code>, because the list endpoint has no server-side filter for it. Anything with <code>due_date</code> in the past and <code>amount_remaining</code> above zero is receivable that nothing is chasing.</p>
<p>Rank by days overdue and by <code>amount_remaining</code>, and use <code>status_transitions.finalized_at</code> for the true age. Past 60 days you are outside the window Stripe's own reminder emails cover, so no automated follow-up will ever be sent for that invoice no matter what you switch on today.</p>""",
"problem": """<p><code>send_invoice</code> is the correct collection method for customers who pay from an accounts-payable process rather than a saved card, and it behaves exactly as documented: Stripe finalizes the invoice, emails it, and stops. There is no charge attempt, no retry schedule and no dunning, because there is nothing on file to charge.</p>
<p>The gap is that most teams read "Stripe handles billing" as covering collection too. It does for <code>charge_automatically</code>. For <code>send_invoice</code> the follow-up is a Dashboard setting nobody turned on, and the result is an accounts receivable ledger that exists only inside Stripe, that nobody exports, and that ages quietly while the customer keeps their service. The first honest measurement usually happens during a funding round or an audit, at which point some of it is a year old and effectively uncollectible.</p>""",
"why": """<p><strong>Nothing changes state when an invoice goes past due.</strong> An overdue invoice stays <code>open</code>. Stripe has no <code>overdue</code> status, so no event fires, no filter in the Dashboard highlights it, and any dashboard you built on invoice status shows it in exactly the same bucket as one issued this morning.</p>
<p><strong>The list endpoint cannot filter on <code>due_date</code>.</strong> You can filter by status, by collection method, by customer and by <code>created</code>, but not by the field that defines overdue. That single omission is why this check is nearly always written as "we will look in the Dashboard sometimes" instead of as a cron job: the obvious one-line API call does not exist, and the two-line version with a client-side filter never gets written.</p>
<p><strong>The subscription does not react either.</strong> The 30, 60 and 90 day past-due actions are opt-in settings. Left at their defaults, an unpaid <code>send_invoice</code> subscription keeps renewing and keeps generating new invoices on top of the unpaid one, so the customer accumulates debt while continuing to receive the service.</p>
<p><strong>Reminders have a window, and it closes.</strong> Stripe's built-in reminders run from shortly before the due date to about 60 days after it. An invoice already 120 days overdue is past all of them: enabling reminders today does nothing for it, and it needs either a manual resend or an honest write-off.</p>""",
"steps": [
 {"h": "Page open invoices for the send_invoice collection method only",
  "body": """<p>Automatically charged invoices sitting open are a different problem with a different repair &mdash; that is dunning, and it is the next note. Filtering here keeps the two apart, so the report you hand someone is one kind of work.</p>"""},
 {"h": "Filter due_date client side and compute the age in days",
  "body": """<p>There is no server-side option, so fetch and compare. Also count the invoices where <code>due_date</code> is null: those can never be overdue by definition, which means no reminder will ever fire for them either. That is usually a <code>days_until_due</code> that was never set on the subscription.</p>"""},
 {"h": "Sort by amount_remaining, not by age",
  "body": """<p>Use <code>amount_remaining</code> rather than <code>total</code>, because partial payments are common on invoiced accounts and the balance is what you are chasing. The oldest invoice is rarely the one worth the phone call.</p>"""},
 {"h": "Turn on the reminders before working the backlog",
  "body": """<p>Settings, then Billing, then Invoices in the Dashboard: enable the reminder emails and set the past-due subscription action. Do this first, so the backlog you are about to clear is the last one that accumulates for this reason.</p>"""},
 {"h": "Re-send what is still collectible, write off what is not",
  "body": """<p><code>POST /v1/invoices/{id}/send</code> re-sends the invoice email. For the ones nobody is going to pay, marking them uncollectible is not an admission of failure; it is what keeps the receivable figure meaningful. Leaving them open forever is the option that costs you an accurate number.</p>"""},
],
"verify": """<p>Re-run the script. Anything still listed should be inside its terms rather than past them.</p>
<pre><code class="language-bash">python3 stripe_overdue_invoices.py
# clear       0 open invoice(s) past due_date</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/invoices</code> with the status and collection method fixed, then a client-side filter because Stripe does not offer a server-side one for <code>due_date</code>. The classifier is pure and takes two scalars, so the boundaries that decide whether an invoice is chaseable, stale or past every reminder Stripe would ever send are visible rules rather than a comparison buried in a loop.",
"py_file": "stripe_overdue_invoices.py",
"py": '''"""Report open Stripe invoices that are past their due_date with nothing chasing them.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Invoices. The repair is printed, never performed, because re-sending an
invoice emails a customer and marking one uncollectible writes off revenue.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_overdue_invoices")

API = "https://api.stripe.com/v1"

ACTION_DAYS = 30      # earliest past-due subscription action Stripe offers
REMINDER_END_DAYS = 60  # past this, no built-in reminder will ever be sent


def verdict(days_overdue, amount_remaining):
    """Classify one open invoice. Pure, so the boundaries can be tested without a network.

    `days_overdue` is negative while the invoice is still within terms and None
    when it has no due_date at all. Returns (state, detail).
    """
    if not amount_remaining or amount_remaining <= 0:
        return ("nothing_due", "open with amount_remaining 0: no money outstanding")
    if days_overdue is None:
        return ("undated",
                "open with no due_date: it can never be overdue, so no reminder "
                "will ever fire for it")
    if days_overdue < 0:
        return ("current", "due in %.1f day(s)" % -days_overdue)
    if days_overdue < ACTION_DAYS:
        return ("overdue",
                "%.0f day(s) past due; still inside the reminder window" % days_overdue)
    if days_overdue < REMINDER_END_DAYS:
        return ("stale",
                "%.0f day(s) past due; past the point where a subscription action "
                "would have fired had one been configured" % days_overdue)
    return ("abandoned",
            "%.0f day(s) past due; beyond every built-in reminder, so nothing "
            "automated will chase this one again" % days_overdue)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def open_invoices(session, limit):
    """Page open, manually collected invoices.

    There is no server-side filter for due_date on this endpoint, so the whole set
    comes back and the comparison happens here.
    """
    out = []
    params = {"status": "open", "collection_method": "send_invoice", "limit": 100}
    while True:
        page = get(session, "/invoices", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=20,
                    help="how many individual invoices to print")
    ap.add_argument("--max-invoices", type=int, default=2000,
                    help="stop paginating after this many open invoices")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    rows = []
    for inv in open_invoices(s, args.max_invoices):
        due = inv.get("due_date")
        remaining = inv.get("amount_remaining") or 0
        rows.append((
            inv.get("id", "<no id>"),
            verdict(None if due is None else (now - due) / 86400.0, remaining),
            remaining,
            (inv.get("currency") or "").upper(),
        ))

    late = [r for r in rows if r[1][0] in ("overdue", "stale", "abandoned", "undated")]
    if not late:
        log.info("%-12s 0 open invoice(s) past due_date", "clear")
        return 0

    # Biggest balance first: the oldest invoice is rarely the one worth a call.
    late.sort(key=lambda r: r[2], reverse=True)
    outstanding = sum(r[2] for r in late)
    log.warning("%-12s %d unchased invoice(s) worth %d in minor units",
                "receivable", len(late), outstanding)
    for inv_id, (state, detail), amount, currency in late[:args.top]:
        log.warning("  %-12s %s  %d %s  %s", state, inv_id, amount, currency, detail)
    if len(late) > args.top:
        log.warning("  ... and %d more", len(late) - args.top)
    log.warning("  turn the follow-up on first: Dashboard, Settings, Billing, "
                "Invoices, then enable reminder emails and the past-due "
                "subscription action")
    log.warning("  then per invoice: POST %s/invoices/<id>/send to re-send, or "
                "mark_uncollectible on the ones nobody will pay", API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-overdue-invoices.mjs",
"js": '''/**
 * Report open Stripe invoices past their due_date with nothing chasing them.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const ACTION_DAYS = 30;             // earliest past-due subscription action
export const REMINDER_END_DAYS = 60; // past this, no built-in reminder is sent

/**
 * Classify one open invoice. Pure, so the boundaries can be tested without a network.
 * `daysOverdue` is negative within terms and null when there is no due_date.
 */
export function verdict(daysOverdue, amountRemaining) {
  if (!amountRemaining || amountRemaining <= 0) {
    return ['nothing_due', 'open with amount_remaining 0: no money outstanding'];
  }
  if (daysOverdue === null || daysOverdue === undefined) {
    return ['undated',
      'open with no due_date: it can never be overdue, so no reminder will ever fire for it'];
  }
  if (daysOverdue < 0) {
    return ['current', `due in ${(-daysOverdue).toFixed(1)} day(s)`];
  }
  if (daysOverdue < ACTION_DAYS) {
    return ['overdue',
      `${daysOverdue.toFixed(0)} day(s) past due; still inside the reminder window`];
  }
  if (daysOverdue < REMINDER_END_DAYS) {
    return ['stale',
      `${daysOverdue.toFixed(0)} day(s) past due; past the point where a ` +
      'subscription action would have fired had one been configured'];
  }
  return ['abandoned',
    `${daysOverdue.toFixed(0)} day(s) past due; beyond every built-in reminder, ` +
    'so nothing automated will chase this one again'];
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

export async function openInvoices(key, limit = 2000) {
  const out = [];
  const params = { status: 'open', collection_method: 'send_invoice', limit: 100 };
  for (;;) {
    const page = await get(key, '/invoices', params);
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

  const now = Date.now() / 1000;
  const rows = (await openInvoices(key)).map((inv) => {
    const remaining = inv.amount_remaining ?? 0;
    const due = inv.due_date;
    return {
      id: inv.id ?? '<no id>',
      amount: remaining,
      currency: (inv.currency ?? '').toUpperCase(),
      state: verdict(due === null || due === undefined ? null : (now - due) / 86400, remaining),
    };
  });

  const late = rows.filter((r) => ['overdue', 'stale', 'abandoned', 'undated'].includes(r.state[0]));
  if (late.length === 0) {
    console.log(`${'clear'.padEnd(12)} 0 open invoice(s) past due_date`);
    return;
  }

  // Biggest balance first: the oldest invoice is rarely the one worth a call.
  late.sort((a, b) => b.amount - a.amount);
  const outstanding = late.reduce((a, r) => a + r.amount, 0);
  console.warn(`${'receivable'.padEnd(12)} ${late.length} unchased invoice(s) worth ${outstanding} in minor units`);
  for (const r of late.slice(0, 20)) {
    const [state, detail] = r.state;
    console.warn(`  ${state.padEnd(12)} ${r.id}  ${r.amount} ${r.currency}  ${detail}`);
  }
  if (late.length > 20) console.warn(`  ... and ${late.length - 20} more`);
  console.warn('  turn the follow-up on first: Dashboard, Settings, Billing, ' +
               'Invoices, then enable reminder emails and the past-due subscription action');
  console.warn(`  then per invoice: POST ${API}/invoices/<id>/send to re-send, or ` +
               'mark_uncollectible on the ones nobody will pay');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these tests are about the day the state changes and two are about invoices that look fine and are not. An invoice with no <code>due_date</code> is the interesting case: it is not overdue, it can never become overdue, and treating it as healthy is how a receivable disappears from the report entirely.",
"test_py_file": "test_stripe_overdue_invoices.py",
"test_py": '''from stripe_overdue_invoices import verdict


def test_within_terms_is_current():
    state, detail = verdict(-4.0, 25000)
    assert state == "current"
    assert "4.0" in detail


def test_the_due_date_itself_is_already_overdue():
    assert verdict(-0.1, 25000)[0] == "current"
    assert verdict(0.0, 25000)[0] == "overdue"


def test_thirty_and_sixty_days_are_the_two_boundaries():
    assert verdict(29.9, 25000)[0] == "overdue"
    assert verdict(30.0, 25000)[0] == "stale"
    assert verdict(59.9, 25000)[0] == "stale"
    state, detail = verdict(60.0, 25000)
    assert state == "abandoned"
    assert "nothing automated will chase" in detail


def test_no_due_date_is_reported_rather_than_ignored():
    # It can never be overdue, which means no reminder will ever fire. Silence
    # here is how an invoice leaves the receivable report for good.
    state, _ = verdict(None, 25000)
    assert state == "undated"


def test_a_zero_balance_is_not_receivable():
    assert verdict(120.0, 0)[0] == "nothing_due"
''',
"test_js_file": "stripe-overdue-invoices.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-overdue-invoices.mjs';

test('within terms is current', () => {
  const [state, detail] = verdict(-4.0, 25000);
  assert.equal(state, 'current');
  assert.match(detail, /4.0/);
});

test('the due date itself is already overdue', () => {
  assert.equal(verdict(-0.1, 25000)[0], 'current');
  assert.equal(verdict(0.0, 25000)[0], 'overdue');
});

test('thirty and sixty days are the two boundaries', () => {
  assert.equal(verdict(29.9, 25000)[0], 'overdue');
  assert.equal(verdict(30.0, 25000)[0], 'stale');
  assert.equal(verdict(59.9, 25000)[0], 'stale');
  const [state, detail] = verdict(60.0, 25000);
  assert.equal(state, 'abandoned');
  assert.match(detail, /nothing automated will chase/);
});

test('no due date is reported rather than ignored', () => {
  assert.equal(verdict(null, 25000)[0], 'undated');
});

test('a zero balance is not receivable', () => {
  assert.equal(verdict(120.0, 0)[0], 'nothing_due');
});
''',
"faq": [
 ("Why does Stripe not charge a send_invoice invoice automatically?",
  "Because there is nothing to charge. collection_method=send_invoice means the customer pays on their own terms, usually by bank transfer or card through the hosted invoice page, and no payment method is assumed to be on file. Stripe emails the invoice at finalization and then waits, which is the documented behaviour rather than a failure."),
 ("Is there an overdue status I can filter on?",
  "No. An overdue invoice keeps the status open, and the list endpoint has no due_date filter either. That combination is the whole reason this needs a script: you fetch open invoices for the collection method and compare due_date yourself."),
 ("What does marking an invoice uncollectible actually do?",
  "It closes the invoice as bad debt without pretending it was paid, so your revenue and receivable figures stay honest. It does not refund anything and it does not delete the record. Leaving unrecoverable invoices open indefinitely is the option that quietly inflates the receivable number."),
 ("Will enabling reminders help the invoices that are already 200 days late?",
  "No. Stripe's reminder schedule runs from shortly before the due date to roughly 60 days after it, so an invoice past that window is outside every automated follow-up. Enable the reminders for everything that comes after, and work the old backlog by hand or write it off."),
 ("What about open invoices on charge_automatically?",
  "Different problem entirely. Those have a payment method and a retry schedule, so the question is whether dunning is still running or has already given up. That is the next note in this section, and mixing the two in one report gets both of them ignored."),
],
"related": [
 ("/stripe/dunning-retries-exhausted/", "Dunning ran out of retries and no attempt is scheduled"),
 ("/stripe/draft-invoices-never-finalized/", "Draft invoices sit for months and never finalize"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access forever"),
],
"citations": [CITE_COLLECTION, CITE_INVOICE_LIST, CITE_INVOICE_OBJ, CITE_INVOICE_SEND],
},

{
"slug": "dunning-retries-exhausted",
"title": "Dunning ran out of retries and no attempt is scheduled",
"description": "After the last Smart Retry, next_payment_attempt goes null and Stripe stops. High attempt_count with nothing scheduled is a customer nobody will ever bill.",
"h1": "dunning ran out of retries and no attempt is scheduled",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe dunning", "next_payment_attempt null",
             "stripe attempt_count", "stripe smart retries",
             "stripe failed invoice retries"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A card expired in May. Stripe retried it eight times over two weeks, each attempt failed, and then it stopped, which is exactly what it is supposed to do. Nothing announced the end of that sequence. The invoice is still <code>open</code>, the customer still has access, and the last human to look at the account was the one who set up the subscription.",
"short_answer": """<p>List <code>GET /v1/invoices?status=open&amp;collection_method=charge_automatically</code> and read two fields together. <code>attempt_count</code> is how many times Stripe has tried; <code>next_payment_attempt</code> is when it will try again, and <code>null</code> means never.</p>
<p>A high <code>attempt_count</code> with <code>next_payment_attempt: null</code> and <code>amount_remaining</code> above zero is a finished dunning sequence: Stripe has given up and no further attempt exists anywhere. A high count with an attempt still scheduled is the other signature, the hard decline, where retries are queued but only execute once a new payment method appears.</p>""",
"problem": """<p>Dunning is the one part of billing that is genuinely automatic, so it gets trusted completely. The retries run, most of them succeed eventually, and the recovered revenue shows up without anyone doing anything. That is a real feature and it works.</p>
<p>What is missing is the ending. When the last retry fails, Stripe stops attempting and sets <code>next_payment_attempt</code> to null. There is no separate "we gave up" state on the invoice: the status is still <code>open</code>, identical to an invoice issued twenty minutes ago that is about to be paid. Unless the end-of-dunning subscription action was configured, the subscription does not change either, so the customer keeps their access, keeps renewing, and accumulates further unpaid invoices behind the first one. Six months later, someone finds an account with nine open invoices and no way to tell when the relationship actually ended.</p>""",
"why": """<p><strong>The end of dunning is an absence, not an event.</strong> Every failed attempt produces an <code>invoice.payment_failed</code> event, including the last one, and the last one looks exactly like the others. The only thing that distinguishes it is that no further attempt gets scheduled, and there is no event for a thing that did not happen.</p>
<p><strong><code>attempt_count</code> alone is misleading.</strong> On a hard decline &mdash; <code>lost_card</code>, <code>stolen_card</code>, <code>transaction_not_allowed</code>, <code>authentication_required</code> &mdash; Stripe still increments the count and still schedules attempts, but those attempts do not really execute against the dead card; they wait for a new payment method. A count of nine with a future attempt means the customer needs an email, not that the system is still trying. The pair of fields distinguishes the two; either one on its own does not.</p>
<p><strong>A low count with nothing scheduled is a configuration problem, not a customer problem.</strong> If dunning stopped after one or two attempts, either Smart Retries is off, or an end-of-dunning action already ran. Both are worth knowing, and both look like the exhausted case if you only check <code>next_payment_attempt</code>.</p>
<p><strong>Access is decoupled from payment by default.</strong> The action Stripe takes when dunning ends &mdash; cancel, mark unpaid, leave alone &mdash; is a Dashboard setting, and the default leaves the subscription running. That is a sensible default for a business that wants to keep customers through a payment problem, and a costly one for a business that forgot the setting exists.</p>""",
"steps": [
 {"h": "Page open invoices for charge_automatically only",
  "body": """<p>Manually collected invoices have no retry schedule at all, so including them fills the report with rows where <code>next_payment_attempt</code> is legitimately null. Those are a receivable problem with a different repair, covered separately.</p>"""},
 {"h": "Read attempt_count and next_payment_attempt as a pair",
  "body": """<p>Four states come out of two fields, and they need four different responses. Retries still running: wait. Retries exhausted: the relationship needs a decision. Retries scheduled but the count is high: email the customer for a new card. Nothing ever attempted: look at the integration, not the customer.</p>"""},
 {"h": "Check that Smart Retries is actually on",
  "body": """<p>A pile of invoices that stopped after one or two attempts is a settings problem, not a customer-quality problem. Dashboard, then Billing, then Revenue recovery, then Retries: the default schedule is eight attempts over two weeks, and it recovers materially more than a fixed schedule does.</p>"""},
 {"h": "Set the end-of-dunning action while you are there",
  "body": """<p>Decide now what should happen when retries run out: cancel the subscription, mark it unpaid, or leave it. Any of the three is defensible. Not choosing means the default runs, and the default is the one that keeps giving away the product.</p>"""},
 {"h": "Work the exhausted list by value",
  "body": """<p>For the ones worth recovering, collect a new card, set it as the subscription's <code>default_payment_method</code>, and then pay the invoice. Doing it in the other order pays the invoice with the same failing card. For the rest, mark them uncollectible so the receivable figure means something.</p>"""},
],
"verify": """<p>Re-run the script. Every remaining open invoice should have an attempt scheduled, or a count low enough that dunning is genuinely still in progress.</p>
<pre><code class="language-bash">python3 stripe_dunning_exhausted.py
# clear           0 invoice(s) with dunning stopped</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/invoices</code> and no writes &mdash; a restricted key with read access to Invoices is enough. The classifier is pure and takes the two fields plus the balance, because the whole value of this check is in telling <em>exhausted</em> apart from <em>stalled</em>: one needs a decision about the customer, the other needs an email asking for a card, and they are indistinguishable in the Dashboard.",
"py_file": "stripe_dunning_exhausted.py",
"py": '''"""Report Stripe invoices where dunning has stopped and no attempt is scheduled.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Invoices. The repair is printed, never performed, because paying an
invoice moves money and marking one uncollectible writes off revenue.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_dunning_exhausted")

API = "https://api.stripe.com/v1"

# The default Smart Retries schedule is eight attempts over two weeks. Four is a
# deliberately conservative floor: past it, a sequence that has stopped has
# stopped for a reason rather than by coincidence.
EXHAUSTED_ATTEMPTS = 4


def verdict(attempt_count, next_attempt_in_days, amount_remaining):
    """Classify one automatically collected invoice. Pure, so the rules can be tested.

    `next_attempt_in_days` is the time until `next_payment_attempt`, and None when
    that field is null, which is Stripe saying it will not try again. Returns
    (state, detail).
    """
    if not amount_remaining or amount_remaining <= 0:
        return ("nothing_due", "open with amount_remaining 0: no money outstanding")
    if next_attempt_in_days is None:
        if attempt_count >= EXHAUSTED_ATTEMPTS:
            return ("exhausted",
                    "%d attempt(s) and next_payment_attempt is null: dunning is "
                    "over and nothing will collect this" % attempt_count)
        if attempt_count:
            return ("stopped_early",
                    "only %d attempt(s) and nothing scheduled: Smart Retries is "
                    "off, or an end-of-dunning action already ran" % attempt_count)
        return ("never_attempted",
                "0 attempts and nothing scheduled: this invoice was never charged "
                "at all, which is an integration problem rather than a decline")
    if attempt_count >= EXHAUSTED_ATTEMPTS:
        return ("stalled",
                "%d attempt(s) with another in %.1f day(s): on a hard decline the "
                "count keeps rising but nothing collects until a new payment "
                "method is attached" % (attempt_count, next_attempt_in_days))
    return ("retrying",
            "%d attempt(s), next in %.1f day(s): dunning is still running"
            % (attempt_count, next_attempt_in_days))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def open_invoices(session, limit):
    """Page open invoices that Stripe is supposed to be charging by itself."""
    out = []
    params = {"status": "open", "collection_method": "charge_automatically",
              "limit": 100}
    while True:
        page = get(session, "/invoices", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=20,
                    help="how many individual invoices to print")
    ap.add_argument("--max-invoices", type=int, default=2000,
                    help="stop paginating after this many open invoices")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    rows = []
    for inv in open_invoices(s, args.max_invoices):
        nxt = inv.get("next_payment_attempt")
        remaining = inv.get("amount_remaining") or 0
        rows.append((
            inv.get("id", "<no id>"),
            inv.get("subscription") or "<no subscription>",
            verdict(inv.get("attempt_count") or 0,
                    None if nxt is None else (nxt - now) / 86400.0,
                    remaining),
            remaining,
            (inv.get("currency") or "").upper(),
        ))

    stopped = [r for r in rows if r[2][0] in
               ("exhausted", "stopped_early", "never_attempted", "stalled")]
    if not stopped:
        log.info("%-15s 0 invoice(s) with dunning stopped", "clear")
        return 0

    stopped.sort(key=lambda r: r[3], reverse=True)
    lost = sum(r[3] for r in stopped)
    log.warning("%-15s %d invoice(s) nothing is collecting, worth %d in minor units",
                "stopped", len(stopped), lost)
    for inv_id, sub, (state, detail), amount, currency in stopped[:args.top]:
        log.warning("  %-15s %s  %d %s  %s", state, inv_id, amount, currency, detail)
        if state in ("exhausted", "stalled"):
            log.warning("      collect a card, then set it on the subscription "
                        "before paying: POST %s/subscriptions/%s "
                        "default_payment_method=<pm>", API, sub)
            log.warning("      then POST %s/invoices/%s/pay", API, inv_id)
    if len(stopped) > args.top:
        log.warning("  ... and %d more", len(stopped) - args.top)
    log.warning("  check the schedule itself: Dashboard, Billing, Revenue "
                "recovery, Retries, and set an end-of-dunning action")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-dunning-exhausted.mjs",
"js": '''/**
 * Report Stripe invoices where dunning has stopped and no attempt is scheduled.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// The default Smart Retries schedule is eight attempts over two weeks. Four is a
// deliberately conservative floor: past it, a sequence that has stopped has
// stopped for a reason rather than by coincidence.
export const EXHAUSTED_ATTEMPTS = 4;

/**
 * Classify one automatically collected invoice. Pure, so the rules can be tested.
 * `nextAttemptInDays` is null when next_payment_attempt is null, which is Stripe
 * saying it will not try again.
 */
export function verdict(attemptCount, nextAttemptInDays, amountRemaining) {
  if (!amountRemaining || amountRemaining <= 0) {
    return ['nothing_due', 'open with amount_remaining 0: no money outstanding'];
  }
  if (nextAttemptInDays === null || nextAttemptInDays === undefined) {
    if (attemptCount >= EXHAUSTED_ATTEMPTS) {
      return ['exhausted',
        `${attemptCount} attempt(s) and next_payment_attempt is null: dunning is ` +
        'over and nothing will collect this'];
    }
    if (attemptCount) {
      return ['stopped_early',
        `only ${attemptCount} attempt(s) and nothing scheduled: Smart Retries is ` +
        'off, or an end-of-dunning action already ran'];
    }
    return ['never_attempted',
      '0 attempts and nothing scheduled: this invoice was never charged at all, ' +
      'which is an integration problem rather than a decline'];
  }
  if (attemptCount >= EXHAUSTED_ATTEMPTS) {
    return ['stalled',
      `${attemptCount} attempt(s) with another in ${nextAttemptInDays.toFixed(1)} ` +
      'day(s): on a hard decline the count keeps rising but nothing collects ' +
      'until a new payment method is attached'];
  }
  return ['retrying',
    `${attemptCount} attempt(s), next in ${nextAttemptInDays.toFixed(1)} day(s): ` +
    'dunning is still running'];
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

export async function openInvoices(key, limit = 2000) {
  const out = [];
  const params = { status: 'open', collection_method: 'charge_automatically', limit: 100 };
  for (;;) {
    const page = await get(key, '/invoices', params);
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

  const now = Date.now() / 1000;
  const rows = (await openInvoices(key)).map((inv) => {
    const nxt = inv.next_payment_attempt;
    const remaining = inv.amount_remaining ?? 0;
    return {
      id: inv.id ?? '<no id>',
      sub: inv.subscription ?? '<no subscription>',
      amount: remaining,
      currency: (inv.currency ?? '').toUpperCase(),
      state: verdict(inv.attempt_count ?? 0,
        nxt === null || nxt === undefined ? null : (nxt - now) / 86400,
        remaining),
    };
  });

  const stopped = rows.filter((r) => ['exhausted', 'stopped_early', 'never_attempted', 'stalled']
    .includes(r.state[0]));
  if (stopped.length === 0) {
    console.log(`${'clear'.padEnd(15)} 0 invoice(s) with dunning stopped`);
    return;
  }

  stopped.sort((a, b) => b.amount - a.amount);
  const lost = stopped.reduce((a, r) => a + r.amount, 0);
  console.warn(`${'stopped'.padEnd(15)} ${stopped.length} invoice(s) nothing is collecting, worth ${lost} in minor units`);
  for (const r of stopped.slice(0, 20)) {
    const [state, detail] = r.state;
    console.warn(`  ${state.padEnd(15)} ${r.id}  ${r.amount} ${r.currency}  ${detail}`);
    if (state === 'exhausted' || state === 'stalled') {
      console.warn('      collect a card, then set it on the subscription before ' +
                   `paying: POST ${API}/subscriptions/${r.sub} default_payment_method=<pm>`);
      console.warn(`      then POST ${API}/invoices/${r.id}/pay`);
    }
  }
  if (stopped.length > 20) console.warn(`  ... and ${stopped.length - 20} more`);
  console.warn('  check the schedule itself: Dashboard, Billing, Revenue recovery, ' +
               'Retries, and set an end-of-dunning action');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test here is about the pair of fields rather than either one, because that is where the check earns its keep. The same <code>attempt_count</code> of nine means &ldquo;Stripe has given up&rdquo; with a null next attempt and &ldquo;the customer needs to send a new card&rdquo; with a scheduled one, and those go to different people.",
"test_py_file": "test_stripe_dunning_exhausted.py",
"test_py": '''from stripe_dunning_exhausted import verdict


def test_dunning_still_running_is_not_a_finding():
    state, detail = verdict(2, 1.5, 9900)
    assert state == "retrying"
    assert "still running" in detail


def test_high_count_with_nothing_scheduled_is_exhausted():
    state, detail = verdict(8, None, 9900)
    assert state == "exhausted"
    assert "next_payment_attempt is null" in detail


def test_high_count_with_an_attempt_scheduled_is_a_hard_decline():
    # Same count, opposite meaning: retries are queued but only execute once a
    # new payment method appears, so this one needs an email, not a decision.
    assert verdict(8, 2.0, 9900)[0] == "stalled"
    assert verdict(3, None, 9900)[0] == "stopped_early"
    assert verdict(4, None, 9900)[0] == "exhausted"


def test_never_attempted_is_an_integration_problem():
    state, detail = verdict(0, None, 9900)
    assert state == "never_attempted"
    assert "integration problem" in detail


def test_a_settled_balance_is_not_dunning():
    assert verdict(8, None, 0)[0] == "nothing_due"
''',
"test_js_file": "stripe-dunning-exhausted.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-dunning-exhausted.mjs';

test('dunning still running is not a finding', () => {
  const [state, detail] = verdict(2, 1.5, 9900);
  assert.equal(state, 'retrying');
  assert.match(detail, /still running/);
});

test('high count with nothing scheduled is exhausted', () => {
  const [state, detail] = verdict(8, null, 9900);
  assert.equal(state, 'exhausted');
  assert.match(detail, /next_payment_attempt is null/);
});

test('high count with an attempt scheduled is a hard decline', () => {
  assert.equal(verdict(8, 2.0, 9900)[0], 'stalled');
  assert.equal(verdict(3, null, 9900)[0], 'stopped_early');
  assert.equal(verdict(4, null, 9900)[0], 'exhausted');
});

test('never attempted is an integration problem', () => {
  const [state, detail] = verdict(0, null, 9900);
  assert.equal(state, 'never_attempted');
  assert.match(detail, /integration problem/);
});

test('a settled balance is not dunning', () => {
  assert.equal(verdict(8, null, 0)[0], 'nothing_due');
});
''',
"faq": [
 ("How many times does Stripe retry a failed invoice?",
  "The Smart Retries default is eight attempts spread over two weeks, timed by a model rather than a fixed interval. You can switch to a fixed schedule or turn retries off entirely, which is why a pile of invoices that stopped after one or two attempts is worth checking against the settings before blaming the cards."),
 ("What exactly does next_payment_attempt: null mean?",
  "That Stripe has no further attempt planned for that invoice. On an open, automatically collected invoice with a balance, it means the retry sequence is finished. It is the only signal that dunning ended, because the invoice status stays open and the final failure event looks like every earlier one."),
 ("Why would attempt_count be high while an attempt is still scheduled?",
  "Hard declines. On lost_card, stolen_card, transaction_not_allowed or authentication_required, retrying the same card cannot succeed, so the attempts wait for a new payment method to be attached. The count keeps rising and the schedule stays populated, which reads as a working system and is actually a stalled one."),
 ("Does the subscription get cancelled when retries run out?",
  "Only if you configured it to. The end-of-dunning action is a Dashboard setting with options to cancel, mark the subscription unpaid, or do nothing, and doing nothing is the default. That is why unpaid customers keep their access and keep generating new invoices behind the unpaid one."),
 ("Why set the payment method on the subscription before paying the invoice?",
  "Because paying it without doing that charges whatever failed last time. Attach the new payment method, set it as the subscription's default so future renewals use it too, and then pay the invoice. In the other order you get one more decline and an unchanged renewal."),
],
"related": [
 ("/stripe/open-invoices-past-due-date/", "Open invoices are weeks past due_date and nobody chases"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access forever"),
 ("/stripe/subscription-without-payment-method/", "Active subscriptions with nothing to charge on renewal"),
],
"citations": [CITE_SMART_RETRIES, CITE_RECOVERY, CITE_INVOICE_OBJ, CITE_INVOICE_PAY],
},

{
"slug": "automatic-tax-disabled-everywhere",
"title": "automatic_tax is off on every invoice while selling abroad",
"description": "automatic_tax.enabled defaults to false, and enabling Stripe Tax in the Dashboard does not touch subscriptions your API create call already made.",
"h1": "automatic_tax is off on every invoice while selling abroad",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe automatic_tax enabled", "stripe tax not calculated",
             "stripe vat missing invoice", "automatic_tax false subscription",
             "stripe tax subscriptions"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Stripe Tax was switched on eighteen months ago, the registrations were filed, and everyone moved on. The invoices going to Germany, France and the UK still carry no VAT, because enabling Tax in the Dashboard did nothing to the subscriptions the API had already created. Nothing errors. The totals are simply wrong, and the liability compounds every month.",
"short_answer": """<p>Count how many active subscriptions have tax off: <code>GET /v1/subscriptions?status=active</code> and read <code>automatic_tax.enabled</code> on each, or let Stripe filter with <code>automatic_tax[enabled]=false</code>. Then take the countries you are actually invoicing from <code>GET /v1/invoices?status=paid</code> and <code>customer_address.country</code> on the untaxed ones.</p>
<p>Tax off plus a single domestic country may well be correct. Tax off plus invoices to the EU, the UK, Australia or Canada is the combination that compounds, because those are jurisdictions where a remote seller acquires an obligation and the invoices you already sent cannot be reissued with tax on them.</p>""",
"problem": """<p>Every other failure in this section makes something visibly stop. This one makes everything keep working with the wrong number on it. The subscription bills, the card is charged, the invoice is delivered, the customer pays, and the tax line is absent because Stripe was never asked to compute one.</p>
<p>The cost is that it is retroactive. A webhook outage is bounded by the outage. Missing tax is bounded by however long the integration has been running, and the money was never collected from the customer, so the liability comes out of margin that has already been recognised, spent and reported. By the time an audit or a diligence process finds it, the exposure is the whole trading history in that jurisdiction rather than the current month.</p>""",
"why": """<p><strong>The field defaults to <code>false</code>, and defaults do not announce themselves.</strong> <code>automatic_tax.enabled</code> is off unless the create call passes it. Nothing in the API response is missing, nothing is flagged, and the invoice looks complete because a total with no tax on it is still a valid total.</p>
<p><strong>Enabling Stripe Tax in the Dashboard is not retroactive and not universal.</strong> It affects invoices created through the Dashboard. Subscriptions your code created keep whatever they were created with, forever, because <code>automatic_tax</code> lives on the subscription and not on the account. The team that turned Tax on genuinely believes it is on.</p>
<p><strong>Nobody is watching the field they would need to watch.</strong> The failure has no owner: engineering sees payments succeeding, finance sees revenue arriving, and the person who would notice a missing VAT line is looking at a spreadsheet exported from a system that also has no tax column.</p>
<p><strong>Enabling it is necessary and not sufficient.</strong> With <code>automatic_tax[enabled]=true</code> but no active registration for a jurisdiction, Stripe calculates zero and the invoices look exactly as wrong as before. And with tax on but an unresolvable customer address the calculation reports <code>requires_location_inputs</code>, which can hold the invoice in draft instead. Turning it on is the first step of three, not the whole repair.</p>""",
"steps": [
 {"h": "Count active subscriptions with automatic_tax off, against the total",
  "body": """<p>The ratio is the diagnosis. All of them means it was never set on any create path. Some of them means the code was fixed at some point and the older subscriptions were never backfilled &mdash; which is the more dangerous version, because the recent invoices in the Dashboard all look right.</p>"""},
 {"h": "Take the countries from paid invoices, not from customer records",
  "body": """<p><code>customer_address.country</code> on the invoice is where the invoice was actually billed to. A customer's current address can be edited after the fact; the invoice keeps what was used. Collect the distinct set across untaxed paid invoices and you have the exposure map.</p>"""},
 {"h": "Treat a missing country as its own finding",
  "body": """<p>If <code>customer_address</code> is null across the board, you are not selling tax free &mdash; you are unable to determine tax at all, and enabling Stripe Tax will produce <code>requires_location_inputs</code> rather than a tax line. Collecting the address is the prerequisite, not an afterthought.</p>"""},
 {"h": "Register before you enable",
  "body": """<p>Stripe calculates tax only where you have an active registration. Turning <code>automatic_tax</code> on without registrations produces zero tax and a false sense that the problem is solved. Get the registrations in place, then enable, then verify one real invoice has a tax line.</p>"""},
 {"h": "Fix every create path, then backfill",
  "body": """<p><code>automatic_tax[enabled]=true</code> belongs on subscription creation and on Checkout Session creation, and both need doing or the next signup reintroduces the problem. Only then backfill the existing subscriptions, so the two sets meet in the middle instead of chasing each other.</p>"""},
 {"h": "Take the historical exposure to an accountant, not to a script",
  "body": """<p>This script tells you which jurisdictions and how many subscriptions. What to do about invoices already issued is a question about voluntary disclosure and local rules, and it is not one an API can answer.</p>"""},
],
"verify": """<p>Re-run the script after the backfill. Every active subscription should have tax enabled, whatever the countries look like.</p>
<pre><code class="language-bash">python3 stripe_automatic_tax_off.py
# on          automatic_tax is enabled on all 412 active subscription(s)</code></pre>""",
"code_intro": "Two paginated GETs and no writes &mdash; a restricted key with read access to Subscriptions and Invoices is enough. The classifier is pure and takes the two counts plus the country list, because the same missing field is a note for the backlog on a single-country account and a compounding liability on one selling into the EU, and only the countries tell the two apart.",
"py_file": "stripe_automatic_tax_off.py",
"py": '''"""Report Stripe subscriptions billing without automatic_tax while invoicing abroad.

Read only. Two paginated GETs and no writes: give this a RESTRICTED key with read
access to Subscriptions and Invoices. The repair is printed, never performed.

This is a configuration check, not tax advice. It tells you where you are
invoicing with tax calculation switched off; whether that is a liability is a
question for an accountant.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_automatic_tax_off")

API = "https://api.stripe.com/v1"

# Jurisdictions where a remote seller most commonly acquires a collection
# obligation. Deliberately not exhaustive: the point is to raise the question for
# the obvious cases, not to decide the answer.
REGISTRATION_COUNTRIES = frozenset("""
AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE
GB NO CH AU NZ CA JP SG AE ZA IN
""".split())


def verdict(off_count, total_count, countries):
    """Classify the account. Pure, so the rules can be tested without a network.

    `off_count` is active subscriptions with automatic_tax.enabled false,
    `total_count` is all active subscriptions, and `countries` is the distinct set
    of customer_address.country values seen on untaxed paid invoices. Returns
    (state, detail).
    """
    if not total_count:
        return ("empty", "no active subscriptions to check")
    if not off_count:
        return ("on", "automatic_tax is enabled on all %d active subscription(s)"
                % total_count)
    seen = sorted({(c or "").upper() for c in (countries or []) if c})
    if not seen:
        return ("unknown",
                "%d of %d active subscription(s) have automatic_tax off, and no "
                "untaxed invoice carries customer_address.country: the exposure "
                "cannot be judged, and Stripe could not compute tax either"
                % (off_count, total_count))
    exposed = [c for c in seen if c in REGISTRATION_COUNTRIES]
    if exposed:
        where = ", ".join(exposed)
        if off_count >= total_count:
            return ("exposed",
                    "automatic_tax is off on all %d active subscription(s), and "
                    "untaxed invoices went to %s" % (total_count, where))
        return ("partial",
                "%d of %d active subscription(s) have automatic_tax off: the "
                "create path was fixed and the older ones never backfilled. "
                "Untaxed invoices went to %s" % (off_count, total_count, where))
    if len(seen) > 1:
        return ("multi_country",
                "%d of %d off, and untaxed invoices span %d countries (%s)"
                % (off_count, total_count, len(seen), ", ".join(seen)))
    return ("domestic",
            "%d of %d off, but every untaxed invoice is billed to %s. Check that "
            "against your registrations rather than assuming it is wrong"
            % (off_count, total_count, seen[0]))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
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
    ap.add_argument("--max-subscriptions", type=int, default=2000,
                    help="stop paginating active subscriptions after this many")
    ap.add_argument("--max-invoices", type=int, default=1000,
                    help="how many recent paid invoices to sample for countries")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    subs = page_all(s, "/subscriptions", args.max_subscriptions, status="active")
    total = len(subs)
    off = [x for x in subs if not (x.get("automatic_tax") or {}).get("enabled")]

    countries = []
    for inv in page_all(s, "/invoices", args.max_invoices, status="paid"):
        if (inv.get("automatic_tax") or {}).get("enabled"):
            continue
        addr = inv.get("customer_address") or {}
        if addr.get("country"):
            countries.append(addr["country"])

    state, detail = verdict(len(off), total, countries)
    line = "%-13s %s" % (state, detail)
    if state in ("on", "empty"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  register first: Stripe calculates zero where you have no active "
                "registration, which looks identical to tax being off")
    log.warning("  then set it on every create path: POST %s/subscriptions and "
                "POST %s/checkout/sessions both take automatic_tax[enabled]=true",
                API, API)
    log.warning("  then backfill: POST %s/subscriptions/<sub> "
                "automatic_tax[enabled]=true", API)
    for sub in off[:10]:
        log.warning("      %s", sub.get("id", "<no id>"))
    if len(off) > 10:
        log.warning("      ... and %d more", len(off) - 10)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-automatic-tax-off.mjs",
"js": '''/**
 * Report Stripe subscriptions billing without automatic_tax while invoicing abroad.
 *
 * Read only. Two paginated GETs and no writes: give this a RESTRICTED key with
 * read access to Subscriptions and Invoices. The repair is printed, never performed.
 *
 * This is a configuration check, not tax advice.
 */
const API = 'https://api.stripe.com/v1';

// Jurisdictions where a remote seller most commonly acquires a collection
// obligation. Deliberately not exhaustive: the point is to raise the question for
// the obvious cases, not to decide the answer.
export const REGISTRATION_COUNTRIES = new Set([
  'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU',
  'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES',
  'SE', 'GB', 'NO', 'CH', 'AU', 'NZ', 'CA', 'JP', 'SG', 'AE', 'ZA', 'IN',
]);

/**
 * Classify the account. Pure, so the rules can be tested without a network.
 * `countries` is the distinct set of customer_address.country values seen on
 * untaxed paid invoices.
 */
export function verdict(offCount, totalCount, countries) {
  if (!totalCount) return ['empty', 'no active subscriptions to check'];
  if (!offCount) {
    return ['on', `automatic_tax is enabled on all ${totalCount} active subscription(s)`];
  }
  const seen = [...new Set((countries ?? []).filter(Boolean).map((c) => c.toUpperCase()))].sort();
  if (seen.length === 0) {
    return ['unknown',
      `${offCount} of ${totalCount} active subscription(s) have automatic_tax off, ` +
      'and no untaxed invoice carries customer_address.country: the exposure ' +
      'cannot be judged, and Stripe could not compute tax either'];
  }
  const exposed = seen.filter((c) => REGISTRATION_COUNTRIES.has(c));
  if (exposed.length) {
    const where = exposed.join(', ');
    if (offCount >= totalCount) {
      return ['exposed',
        `automatic_tax is off on all ${totalCount} active subscription(s), and ` +
        `untaxed invoices went to ${where}`];
    }
    return ['partial',
      `${offCount} of ${totalCount} active subscription(s) have automatic_tax off: ` +
      'the create path was fixed and the older ones never backfilled. ' +
      `Untaxed invoices went to ${where}`];
  }
  if (seen.length > 1) {
    return ['multi_country',
      `${offCount} of ${totalCount} off, and untaxed invoices span ${seen.length} ` +
      `countries (${seen.join(', ')})`];
  }
  return ['domestic',
    `${offCount} of ${totalCount} off, but every untaxed invoice is billed to ` +
    `${seen[0]}. Check that against your registrations rather than assuming it is wrong`];
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

  const subs = await pageAll(key, '/subscriptions', 2000, { status: 'active' });
  const off = subs.filter((x) => !(x.automatic_tax?.enabled));

  const countries = [];
  for (const inv of await pageAll(key, '/invoices', 1000, { status: 'paid' })) {
    if (inv.automatic_tax?.enabled) continue;
    const country = inv.customer_address?.country;
    if (country) countries.push(country);
  }

  const [state, detail] = verdict(off.length, subs.length, countries);
  const line = `${state.padEnd(13)} ${detail}`;
  if (state === 'on' || state === 'empty') { console.log(line); return; }

  console.warn(line);
  console.warn('  register first: Stripe calculates zero where you have no active ' +
               'registration, which looks identical to tax being off');
  console.warn(`  then set it on every create path: POST ${API}/subscriptions and ` +
               `POST ${API}/checkout/sessions both take automatic_tax[enabled]=true`);
  console.warn(`  then backfill: POST ${API}/subscriptions/<sub> automatic_tax[enabled]=true`);
  for (const sub of off.slice(0, 10)) console.warn(`      ${sub.id ?? '<no id>'}`);
  if (off.length > 10) console.warn(`      ... and ${off.length - 10} more`);
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests hold the line between reporting a fact and giving tax advice. Tax off in one domestic market gets a state that says check your registrations; tax off with invoices to Germany gets one that says this compounds. The third case is the one people forget: tax off and no address anywhere, where the answer is that nothing can be judged yet.",
"test_py_file": "test_stripe_automatic_tax_off.py",
"test_py": '''from stripe_automatic_tax_off import verdict


def test_all_enabled_is_clear():
    state, detail = verdict(0, 412, [])
    assert state == "on"
    assert "412" in detail


def test_off_everywhere_with_eu_invoices_is_the_loud_case():
    state, detail = verdict(300, 300, ["DE", "FR", "de"])
    assert state == "exposed"
    assert "DE, FR" in detail


def test_a_fixed_create_path_with_no_backfill_reads_as_partial():
    # The dangerous version: new invoices look right in the Dashboard while the
    # older subscriptions keep billing untaxed.
    state, detail = verdict(40, 300, ["GB"])
    assert state == "partial"
    assert "never backfilled" in detail


def test_one_domestic_country_is_a_question_not_a_verdict():
    state, detail = verdict(50, 50, ["US"])
    assert state == "domestic"
    assert "registrations" in detail


def test_no_country_anywhere_cannot_be_judged():
    state, detail = verdict(50, 50, [None, ""])
    assert state == "unknown"
    assert "cannot be judged" in detail
''',
"test_js_file": "stripe-automatic-tax-off.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-automatic-tax-off.mjs';

test('all enabled is clear', () => {
  const [state, detail] = verdict(0, 412, []);
  assert.equal(state, 'on');
  assert.match(detail, /412/);
});

test('off everywhere with EU invoices is the loud case', () => {
  const [state, detail] = verdict(300, 300, ['DE', 'FR', 'de']);
  assert.equal(state, 'exposed');
  assert.match(detail, /DE, FR/);
});

test('a fixed create path with no backfill reads as partial', () => {
  const [state, detail] = verdict(40, 300, ['GB']);
  assert.equal(state, 'partial');
  assert.match(detail, /never backfilled/);
});

test('one domestic country is a question, not a verdict', () => {
  const [state, detail] = verdict(50, 50, ['US']);
  assert.equal(state, 'domestic');
  assert.match(detail, /registrations/);
});

test('no country anywhere cannot be judged', () => {
  const [state, detail] = verdict(50, 50, [null, '']);
  assert.equal(state, 'unknown');
  assert.match(detail, /cannot be judged/);
});
''',
"faq": [
 ("Does enabling Stripe Tax in the Dashboard fix existing subscriptions?",
  "No. automatic_tax lives on the subscription and on the invoice, not on the account. Turning Tax on in the Dashboard affects what the Dashboard creates from then on; a subscription your API created with the field unset keeps billing untaxed until something updates that subscription."),
 ("I enabled automatic_tax and the tax is still zero. Why?",
  "Almost always a missing registration. Stripe calculates tax only for jurisdictions where you have an active registration recorded, so with the flag on and no registration the result is a correctly computed zero. The other cause is an unresolvable customer address, which shows up as automatic_tax.status of requires_location_inputs."),
 ("Why read the country off the invoice rather than the customer?",
  "Because the invoice records the address that was actually used at the time. A customer record can be corrected later, which quietly rewrites the history you are trying to measure. customer_address on a paid invoice is what you billed."),
 ("Can I turn this on for everyone with one API call?",
  "No, it is per subscription, and doing it in a loop is a write against a live billing account that changes what your customers are charged next cycle. Fix the create paths first so nothing new is added to the pile, then work through the existing subscriptions deliberately, in batches you can check."),
 ("Is a missing tax line something I can just fix going forward?",
  "Going forward, yes. What to do about invoices already issued without tax is a question about local rules and voluntary disclosure, and it belongs with an accountant. The script's job is to tell you which jurisdictions are involved and how many subscriptions are affected, which is the information that conversation needs."),
],
"related": [
 ("/stripe/draft-invoices-never-finalized/", "Draft invoices sit for months and never finalize"),
 ("/stripe/open-invoices-past-due-date/", "Open invoices are weeks past due_date and nobody chases"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
],
"citations": [CITE_TAX_INVOICING, CITE_TAX_SETUP, CITE_SUB_LIST, CITE_INVOICE_OBJ],
},

]
