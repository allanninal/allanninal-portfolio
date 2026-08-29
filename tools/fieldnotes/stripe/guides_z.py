#!/usr/bin/env python3
"""/stripe/ field notes, batch Z — the writing.

Same constraint as every other batch in this section: each note is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

Four notes about the two fields that decide whether an invoice can be collected
and whether the tax on it is right: the due date that gives the past-due
machinery something to fire against, and the customer location and tax ID that
Stripe Tax needs before it will calculate anything. Every repair here either
sends a bill, amends a legal record, or changes what a customer owes, which is
exactly why the script prints it instead of doing it.
"""

CITE_INVOICE_OBJ = ("The invoice object — Stripe API reference",
                    "https://docs.stripe.com/api/invoices/object")
CITE_INVOICE_LIST = ("List all invoices — Stripe API reference",
                     "https://docs.stripe.com/api/invoices/list")
CITE_SUB_OBJ = ("The subscription object — Stripe API reference",
                "https://docs.stripe.com/api/subscriptions/object")
CITE_SUB_LIST = ("List all subscriptions — Stripe API reference",
                 "https://docs.stripe.com/api/subscriptions/list")
CITE_COLLECTION = ("Collection method — Stripe Docs",
                   "https://docs.stripe.com/billing/collection-method")
CITE_WORKFLOW = ("Invoice workflow transitions — Stripe Docs",
                 "https://docs.stripe.com/invoicing/integration/workflow-transitions")
CITE_TAX_INVOICING = ("Stripe Tax and invoicing — Stripe Docs",
                      "https://docs.stripe.com/tax/invoicing")
CITE_TAX_LOCATIONS = ("Determining customer locations — Stripe Docs",
                      "https://docs.stripe.com/tax/customer-locations")
CITE_CUSTOMER_OBJ = ("The customer object — Stripe API reference",
                     "https://docs.stripe.com/api/customers/object")
CITE_TAX_IDS = ("Customer tax IDs — Stripe Docs",
                "https://docs.stripe.com/billing/customer/tax-ids")
CITE_TAX_ID_OBJ = ("The tax ID object — Stripe API reference",
                   "https://docs.stripe.com/api/tax_ids/object")
CITE_ZERO_TAX = ("Why is my tax zero? — Stripe Docs",
                 "https://docs.stripe.com/tax/zero-tax")

GUIDES = [

{
"slug": "send-invoice-without-days-until-due",
"title": "Invoiced subscriptions with no days_until_due never age",
"description": "days_until_due is what puts a due_date on a send_invoice bill. Leave it null and the invoice can never be overdue, so no reminder ever fires.",
"h1": "invoiced subscriptions with no days_until_due never age",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe days_until_due null", "stripe invoice no due date",
             "stripe send_invoice subscription", "stripe invoice reminders not sending",
             "stripe collection_method send_invoice"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The finance team asks for an aged receivables report and the answer comes back empty, which everyone reads as good news. It is not: these invoices are not current, they are undateable. <code>days_until_due</code> was never set on the subscriptions that generate them, so Stripe writes each invoice with <code>due_date</code> null, and an invoice with no due date cannot be overdue, cannot trigger a reminder, and cannot age into any bucket at all.",
"short_answer": """<p>List <code>GET /v1/subscriptions?collection_method=send_invoice&amp;status=all</code> and flag every row where <code>days_until_due</code> is null. That field is the only thing that populates <code>due_date</code> on the invoices a <code>send_invoice</code> subscription generates; there is no account-level default that fills it in later.</p>
<p>Corroborate on the invoices themselves with <code>GET /v1/invoices?collection_method=send_invoice&amp;status=open</code> and count the rows whose <code>due_date</code> is null. Those are already issued and already unanchored: the reminder schedule and the 30, 60 and 90 day subscription actions all measure from a due date these invoices do not have.</p>""",
"problem": """<p><code>collection_method=send_invoice</code> is the right choice for customers who pay through an accounts-payable process rather than a card on file. Stripe finalizes the invoice, emails it, and waits. Everything after that &mdash; the reminder emails, the past-due subscription action, any aging report you or Stripe builds &mdash; is arithmetic on <code>due_date</code>.</p>
<p>When <code>days_until_due</code> is null, <code>due_date</code> is null, and that arithmetic has no operand. The invoice does not become overdue at 30 days or at 300. It stays <code>open</code>, indefinitely, in the same bucket as one issued this morning. The customer, for their part, received a bill with no payment terms printed on it, which their accounts-payable system will happily park at the bottom of a queue that is sorted by due date.</p>
<p>The result is receivable that is invisible from both ends. You cannot see it aging because Stripe has nothing to age it against, and they are not chasing it because nothing told them when it was owed.</p>""",
"why": """<p><strong>The field is optional and has no default.</strong> <code>days_until_due</code> is only meaningful for <code>send_invoice</code>, it is rejected for <code>charge_automatically</code>, and it is simply absent unless the create call passes it. A subscription created by an integration written for card customers and later switched to invoicing almost always has it null, because the code path that sets it never existed.</p>
<p><strong>Nothing complains.</strong> Creating a <code>send_invoice</code> subscription with no <code>days_until_due</code> is a valid call that returns 200. Finalizing its invoices is valid. Emailing them is valid. The only artefact is a null in a field nobody reads, on an object nobody opens once it is working.</p>
<p><strong>Turning on reminders does not fix it retroactively, or prospectively.</strong> Reminder emails are scheduled relative to the due date, so enabling them in the Dashboard changes nothing for a subscription that will keep producing undated invoices. Two separate repairs are needed and teams usually only do the visible one.</p>
<p><strong>Zero is a legitimate value and looks like absence.</strong> <code>days_until_due=0</code> means due on receipt, which is a real term some businesses use. Any check written as "if not days_until_due" folds that into the missing case and reports a correctly configured subscription as broken, which is how these checks lose their audience.</p>
<p><strong>Terms longer than the billing period compound quietly.</strong> Net 45 on a monthly subscription means invoice two is issued and emailed before invoice one is due. The customer is permanently at least one invoice behind, and every report of "overdue" undercounts by a whole cycle.</p>""",
"steps": [
 {"h": "Page every send_invoice subscription, in every status",
  "body": """<p>Use <code>status=all</code> rather than <code>active</code>. A subscription that is <code>past_due</code> or <code>unpaid</code> is exactly the one you want to see here, and the default filter hides it. <code>collection_method=send_invoice</code> is a server-side filter, so this stays one cheap paginated read.</p>"""},
 {"h": "Distinguish null from zero before you count anything",
  "body": """<p>Null means no due date will ever be written. Zero means due on receipt. They are different configurations with different repairs, and a truthiness check cannot tell them apart. Compare against null explicitly.</p>"""},
 {"h": "Read the billing interval off the subscription item",
  "body": """<p><code>items.data[0].price.recurring.interval</code> and <code>interval_count</code> give the length of the billing period. Terms at or beyond that length mean the next invoice arrives before the current one is due, which is a real finding even when <code>days_until_due</code> is set.</p>"""},
 {"h": "Count the invoices that are already undated",
  "body": """<p><code>GET /v1/invoices?collection_method=send_invoice&amp;status=open</code>, then filter client side for <code>due_date</code> null. This is the damage already done, as opposed to the damage the configuration will keep doing. It is also the number that gets a ticket prioritised.</p>"""},
 {"h": "Set the terms on the subscription, then switch on reminders",
  "body": """<p><code>days_until_due</code> is updatable on an existing subscription and takes effect on the next invoice. The reminder schedule is a Dashboard setting under Billing then Invoices, and it is worth doing in that order: reminders on a subscription that still writes null due dates change nothing.</p>"""},
 {"h": "Deal with the already-issued invoices separately",
  "body": """<p>An invoice that is already finalized has its <code>due_date</code> baked in, so fixing the subscription does not reach back. Those need a resend, a manual due date, or an honest write-off, and that is a decision per invoice rather than a loop.</p>"""},
],
"verify": """<p>Re-run the script. Every <code>send_invoice</code> subscription should report terms, and the count of open invoices with a null due date should stop growing.</p>
<pre><code class="language-bash">python3 stripe_days_until_due.py
# clear       0 of 34 send_invoice subscription(s) without terms</code></pre>""",
"code_intro": "Two paginated GETs and nothing else &mdash; a restricted key with read access to Subscriptions and Invoices is enough, and is what you should give it. The classifier is pure and takes the collection method, the terms, the billing interval in days and the count of already-undated invoices, because the difference between <em>null</em> and <em>0</em> is the whole point of the note and it deserves a test rather than a comment.",
"py_file": "stripe_days_until_due.py",
"py": '''"""Report Stripe send_invoice subscriptions that write invoices with no due date.

Read only. Two paginated GETs and no writes: give this a RESTRICTED key with read
access to Subscriptions and Invoices. The repair is printed, never performed,
because changing payment terms changes what a customer owes and when.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_days_until_due")

API = "https://api.stripe.com/v1"

# Roughly how many days each recurring interval is worth. Used only to compare
# payment terms against the billing period, so month lengths do not matter.
INTERVAL_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


def verdict(collection_method, days_until_due, interval_days, undated_open_invoices):
    """Classify one subscription. Pure, so the rules can be tested without a network.

    `days_until_due` is the raw field: None when absent, and 0 is a real value
    meaning due on receipt. `interval_days` is the billing period in days, or
    None if it could not be read. `undated_open_invoices` is how many open
    invoices this subscription already has with a null due_date.

    Returns (state, detail).
    """
    if collection_method != "send_invoice":
        return ("automatic",
                "collection_method is %r: Stripe charges the payment method on "
                "file, so days_until_due does not apply" % (collection_method,))
    if days_until_due is None:
        if undated_open_invoices:
            return ("undated",
                    "days_until_due is null and %d open invoice(s) already have "
                    "due_date null: nothing can mark them overdue"
                    % undated_open_invoices)
        return ("unanchored",
                "days_until_due is null, so every invoice this subscription "
                "writes will have due_date null and can never age")
    if days_until_due == 0:
        return ("on-receipt",
                "net 0, due on receipt: a real term, not a missing one")
    if interval_days and days_until_due >= interval_days:
        return ("overlapping",
                "net %d on a %d day billing period: the next invoice is issued "
                "before this one is due" % (days_until_due, interval_days))
    return ("dated",
            "net %d; due_date is set and the past due machinery has something "
            "to measure from" % days_until_due)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def page_all(session, path, limit, **params):
    """Page a list endpoint until it runs out or the cap is reached."""
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


def interval_days(sub):
    """Billing period length in days, or None when the price cannot be read."""
    items = (sub.get("items") or {}).get("data") or []
    if not items:
        return None
    recurring = (items[0].get("price") or {}).get("recurring") or {}
    unit = INTERVAL_DAYS.get(recurring.get("interval"))
    if not unit:
        return None
    return unit * (recurring.get("interval_count") or 1)


def undated_open_invoices(session, limit):
    """Count open send_invoice invoices with a null due_date, per subscription.

    The list endpoint has no server-side filter for due_date, so the comparison
    is client side over invoices Stripe has already narrowed by status and
    collection method.
    """
    counts = {}
    for inv in page_all(session, "/invoices", limit,
                        status="open", collection_method="send_invoice"):
        if inv.get("due_date") is None:
            sub = inv.get("subscription")
            if isinstance(sub, dict):
                sub = sub.get("id")
            counts[sub] = counts.get(sub, 0) + 1
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=20,
                    help="how many individual subscriptions to print")
    ap.add_argument("--max-rows", type=int, default=2000,
                    help="stop paginating each list after this many objects")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    undated = undated_open_invoices(s, args.max_rows)
    subs = page_all(s, "/subscriptions", args.max_rows,
                    collection_method="send_invoice", status="all")
    if not subs:
        log.info("no send_invoice subscriptions for this key's mode")
        return 0

    rows = []
    for sub in subs:
        state, detail = verdict(sub.get("collection_method"),
                                sub.get("days_until_due"),
                                interval_days(sub),
                                undated.get(sub.get("id"), 0))
        rows.append((sub.get("id", "<no id>"), state, detail))

    bad = [r for r in rows if r[1] in ("undated", "unanchored", "overlapping")]
    if not bad:
        log.info("%-11s 0 of %d send_invoice subscription(s) without terms",
                 "clear", len(rows))
        return 0

    log.warning("%-11s %d of %d send_invoice subscription(s) need terms",
                "unterm", len(bad), len(rows))
    for sub_id, state, detail in bad[:args.top]:
        log.warning("  %-11s %s  %s", state, sub_id, detail)
        log.warning("      repair: POST %s/subscriptions/%s  days_until_due=30",
                    API, sub_id)
    if len(bad) > args.top:
        log.warning("  ... and %d more", len(bad) - args.top)
    log.warning("  then Dashboard > Settings > Billing > Invoices: enable the "
                "reminder emails and set the past due subscription action")
    log.warning("  invoices already finalized keep their null due_date; those "
                "need a resend or a write off, one at a time")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-days-until-due.mjs",
"js": '''/**
 * Report Stripe send_invoice subscriptions that write invoices with no due date.
 *
 * Read only. Two paginated GETs and no writes: give this a RESTRICTED key with
 * read access to Subscriptions and Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Roughly how many days each recurring interval is worth. Used only to compare
// payment terms against the billing period, so month lengths do not matter.
export const INTERVAL_DAYS = { day: 1, week: 7, month: 30, year: 365 };

/**
 * Classify one subscription. Pure, so the rules can be tested without a network.
 * `daysUntilDue` is the raw field: null when absent, and 0 is a real value.
 */
export function verdict(collectionMethod, daysUntilDue, intervalDays, undatedOpenInvoices) {
  if (collectionMethod !== 'send_invoice') {
    return ['automatic',
      `collection_method is ${JSON.stringify(collectionMethod)}: Stripe charges ` +
      'the payment method on file, so days_until_due does not apply'];
  }
  if (daysUntilDue === null || daysUntilDue === undefined) {
    if (undatedOpenInvoices) {
      return ['undated',
        `days_until_due is null and ${undatedOpenInvoices} open invoice(s) already ` +
        'have due_date null: nothing can mark them overdue'];
    }
    return ['unanchored',
      'days_until_due is null, so every invoice this subscription writes will ' +
      'have due_date null and can never age'];
  }
  if (daysUntilDue === 0) {
    return ['on-receipt', 'net 0, due on receipt: a real term, not a missing one'];
  }
  if (intervalDays && daysUntilDue >= intervalDays) {
    return ['overlapping',
      `net ${daysUntilDue} on a ${intervalDays} day billing period: the next ` +
      'invoice is issued before this one is due'];
  }
  return ['dated',
    `net ${daysUntilDue}; due_date is set and the past due machinery has ` +
    'something to measure from'];
}

/** Billing period length in days, or null when the price cannot be read. */
export function intervalDays(sub) {
  const items = sub.items?.data ?? [];
  if (items.length === 0) return null;
  const recurring = items[0].price?.recurring ?? {};
  const unit = INTERVAL_DAYS[recurring.interval];
  if (!unit) return null;
  return unit * (recurring.interval_count ?? 1);
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

async function pageAll(key, path, limit, params = {}) {
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

  const maxRows = Number(process.argv[2] ?? 2000);

  const undated = new Map();
  for (const inv of await pageAll(key, '/invoices', maxRows,
    { status: 'open', collection_method: 'send_invoice' })) {
    if (inv.due_date === null || inv.due_date === undefined) {
      const sub = typeof inv.subscription === 'object' && inv.subscription !== null
        ? inv.subscription.id : inv.subscription;
      undated.set(sub, (undated.get(sub) ?? 0) + 1);
    }
  }

  const subs = await pageAll(key, '/subscriptions', maxRows,
    { collection_method: 'send_invoice', status: 'all' });
  if (subs.length === 0) {
    console.log("no send_invoice subscriptions for this key's mode");
    return;
  }

  const rows = subs.map((sub) => ({
    id: sub.id ?? '<no id>',
    v: verdict(sub.collection_method, sub.days_until_due, intervalDays(sub),
      undated.get(sub.id) ?? 0),
  }));

  const bad = rows.filter((r) => ['undated', 'unanchored', 'overlapping'].includes(r.v[0]));
  if (bad.length === 0) {
    console.log(`${'clear'.padEnd(11)} 0 of ${rows.length} send_invoice subscription(s) without terms`);
    return;
  }

  console.warn(`${'unterm'.padEnd(11)} ${bad.length} of ${rows.length} send_invoice subscription(s) need terms`);
  for (const r of bad.slice(0, 20)) {
    console.warn(`  ${r.v[0].padEnd(11)} ${r.id}  ${r.v[1]}`);
    console.warn(`      repair: POST ${API}/subscriptions/${r.id}  days_until_due=30`);
  }
  if (bad.length > 20) console.warn(`  ... and ${bad.length - 20} more`);
  console.warn('  then Dashboard > Settings > Billing > Invoices: enable the ' +
               'reminder emails and set the past due subscription action');
  console.warn('  invoices already finalized keep their null due_date; those ' +
               'need a resend or a write off, one at a time');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that earns its place is the one for <code>days_until_due=0</code>. Written the obvious way, the null check is a truthiness check, zero falls through it, and a subscription with due-on-receipt terms is reported as having no terms at all. That single false positive is enough for someone to decide the report is noise and stop reading it, which costs more than the bug did.",
"test_py_file": "test_stripe_days_until_due.py",
"test_py": '''from stripe_days_until_due import verdict


def test_charge_automatically_is_not_a_finding():
    # days_until_due is rejected for charge_automatically, so a null there is
    # correct rather than missing.
    state, detail = verdict("charge_automatically", None, 30, 0)
    assert state == "automatic"
    assert "does not apply" in detail


def test_null_terms_with_no_invoices_yet_is_unanchored():
    state, detail = verdict("send_invoice", None, 30, 0)
    assert state == "unanchored"
    assert "can never age" in detail


def test_null_terms_with_undated_invoices_names_the_damage():
    state, detail = verdict("send_invoice", None, 30, 7)
    assert state == "undated"
    assert "7" in detail


def test_zero_days_is_a_real_term_not_a_missing_one():
    # The whole reason the null check is explicit: `if not days_until_due`
    # would report due-on-receipt as unconfigured.
    state, _ = verdict("send_invoice", 0, 30, 0)
    assert state == "on-receipt"


def test_terms_at_or_past_the_billing_period_overlap():
    assert verdict("send_invoice", 30, 30, 0)[0] == "overlapping"
    assert verdict("send_invoice", 29, 30, 0)[0] == "dated"


def test_an_unreadable_interval_does_not_invent_an_overlap():
    assert verdict("send_invoice", 45, None, 0)[0] == "dated"
''',
"test_js_file": "stripe-days-until-due.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, intervalDays } from './stripe-days-until-due.mjs';

test('charge_automatically is not a finding', () => {
  const [state, detail] = verdict('charge_automatically', null, 30, 0);
  assert.equal(state, 'automatic');
  assert.match(detail, /does not apply/);
});

test('null terms with no invoices yet is unanchored', () => {
  const [state, detail] = verdict('send_invoice', null, 30, 0);
  assert.equal(state, 'unanchored');
  assert.match(detail, /can never age/);
});

test('null terms with undated invoices names the damage', () => {
  const [state, detail] = verdict('send_invoice', null, 30, 7);
  assert.equal(state, 'undated');
  assert.match(detail, /7/);
});

test('zero days is a real term, not a missing one', () => {
  assert.equal(verdict('send_invoice', 0, 30, 0)[0], 'on-receipt');
});

test('terms at or past the billing period overlap', () => {
  assert.equal(verdict('send_invoice', 30, 30, 0)[0], 'overlapping');
  assert.equal(verdict('send_invoice', 29, 30, 0)[0], 'dated');
});

test('an unreadable interval does not invent an overlap', () => {
  assert.equal(verdict('send_invoice', 45, null, 0)[0], 'dated');
});

test('the billing period is read off the first subscription item', () => {
  const sub = { items: { data: [{ price: { recurring: { interval: 'month', interval_count: 3 } } }] } };
  assert.equal(intervalDays(sub), 90);
  assert.equal(intervalDays({ items: { data: [] } }), null);
});
''',
"faq": [
 ("Can I set a default due date for all invoices instead?",
  "Not as a field that back-fills days_until_due. The due date on a subscription invoice comes from the subscription's days_until_due, so a subscription created without it keeps writing invoices with due_date null until that subscription is updated. Setting it once per subscription is the repair; setting it on every create path is the fix."),
 ("Why does days_until_due not work on my card subscriptions?",
  "Because there is nothing to wait for. Under collection_method=charge_automatically Stripe attempts the payment method on file as soon as the invoice finalizes, so there is no period during which the invoice is merely owed. The field is only accepted for send_invoice."),
 ("Will enabling reminder emails fix the invoices already out there?",
  "No. Reminders are scheduled relative to due_date, and these invoices do not have one. Enabling reminders helps every invoice issued after the subscription is fixed, and does nothing at all for the ones already finalized."),
 ("Can I add a due date to an invoice that is already finalized?",
  "due_date is set at finalization and is not something you can revise afterwards on a finalized invoice. In practice the options are to resend it with a stated deadline outside Stripe, to void and reissue, or to mark it uncollectible if it is old enough that chasing it is theatre."),
 ("Is days_until_due=0 a mistake?",
  "No, it means due on receipt, and plenty of businesses bill that way. It is worth pinning in a test because the natural way to check for a missing value in either language treats zero as missing, and a checker that cries wolf on correctly configured subscriptions gets ignored within a week."),
],
"related": [
 ("/stripe/open-invoices-past-due-date/", "Open invoices are weeks past due_date and nobody chases"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions keep their access forever"),
 ("/stripe/dunning-retries-exhausted/", "Dunning ran out of retries and no attempt is scheduled"),
],
"citations": [CITE_COLLECTION, CITE_SUB_OBJ, CITE_INVOICE_OBJ, CITE_SUB_LIST],
},

{
"slug": "draft-invoices-blocked-by-tax-location",
"title": "Draft invoices blocked on customer_tax_location_invalid",
"description": "Stripe Tax will not finalize an invoice for a customer whose location it cannot resolve. The invoice stays draft, the subscription stays active, nothing errors.",
"h1": "draft invoices blocked on customer_tax_location_invalid",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["customer_tax_location_invalid", "stripe invoice stuck draft tax",
             "stripe tax location invalid", "last_finalization_error",
             "finalization_requires_location_inputs"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A handful of customers have not been billed since Stripe Tax was switched on, and their subscriptions all read <code>active</code>. Their renewal invoices were created on schedule, priced correctly, and then refused at the last step: Stripe Tax cannot work out where the customer is, so it will not finalize the invoice, and an unfinalized invoice is never sent and never charged.",
"short_answer": """<p>List <code>GET /v1/invoices?status=draft</code> and read <code>last_finalization_error.code</code>. The value <code>customer_tax_location_invalid</code> means finalization was attempted and rejected because Stripe Tax could not resolve the customer's location: a country is needed outside the US, a five digit ZIP inside it, and a province or postal code in Canada.</p>
<p>Two nearby fields carry the same root cause at different stages. <code>automatic_tax.status</code> of <code>requires_location_inputs</code> means the calculation itself cannot run. <code>automatic_tax.disabled_reason</code> of <code>finalization_requires_location_inputs</code> means Stripe gave up and switched automatic tax off so the invoice could go out &mdash; which it then does, with no tax on it and no error anywhere.</p>
<p>Confirm the cause per customer with <code>GET /v1/customers/{cus}?expand[]=tax</code> and look for <code>tax.automatic_tax</code> of <code>unrecognized_location</code>.</p>""",
"problem": """<p>This is the failure mode that looks most like everything working. The subscription is <code>active</code>, so the customer keeps their access and appears in every retention metric. The invoice exists, so the line items and amounts are all there to look at. Nothing is <code>past_due</code>, because an invoice that never finalized was never owed.</p>
<p>What is missing is the finalization, and with it the invoice number, the PDF, the hosted page, the email and any possibility of collection. The customer is being served for free and does not know it. You are not chasing them, because from the billing system's point of view they were never billed.</p>
<p>It concentrates, too. The customers affected are the ones whose addresses were captured badly, which usually means one signup path, one import, or one country. So it is rarely a stray invoice; it is a cohort, and the cohort keeps generating a new stuck draft every renewal.</p>""",
"why": """<p><strong>Stripe Tax needs a location before it will calculate, and finalization needs a calculation.</strong> With <code>automatic_tax[enabled]=true</code> the tax amount is part of the invoice total, so the invoice cannot become immutable until that number exists. No resolvable address means no number, which means no finalization. That ordering is the whole mechanism.</p>
<p><strong>The address requirement is not one rule.</strong> Outside the US a country is generally enough. In the US it is a five digit postal code, because rates vary below state level. In Canada a province or postal code is needed. An address that satisfies your shipping validator can still fail all three.</p>
<p><strong>The error lives on the invoice, not in your logs.</strong> <code>last_finalization_error</code> is a field on the invoice object. Nothing raises, nothing pages, and the <code>invoice.finalization_failed</code> event only helps if you subscribed to it, which most integrations did not because it did not exist as a concern until Stripe Tax was enabled.</p>
<p><strong>The fallback is worse than the block, and quieter.</strong> Stripe can disable automatic tax on the invoice rather than leaving it stuck, recording <code>finalization_requires_location_inputs</code> in <code>disabled_reason</code>. The invoice then finalizes and gets paid with zero tax on it. That is a collected invoice with a wrong total and a liability you now owe out of your own margin, and it produces no stuck draft for anyone to notice.</p>
<p><strong>Fixing the invoice does not fix the customer.</strong> Finalizing this month's draft with tax disabled clears the symptom and leaves the address broken, so next month produces another one. The repair belongs on the customer record.</p>""",
"steps": [
 {"h": "Page all draft invoices and read last_finalization_error",
  "body": """<p>Do not filter by age here. Unlike a stranded draft, a tax-blocked one is a finding from the first attempt: the finalization already happened and already failed, so waiting adds nothing but more of them.</p>"""},
 {"h": "Separate the blocked from the merely stranded",
  "body": """<p>A draft with <code>auto_advance</code> false was never going to finalize and is a different note with a different repair. A draft with <code>auto_advance</code> true and a finalization error tried and was refused. Reporting them together produces a list nobody can action.</p>"""},
 {"h": "Look for the disabled_reason as hard as for the error",
  "body": """<p><code>finalization_requires_location_inputs</code> on <code>automatic_tax.disabled_reason</code> is the same broken address with the opposite outcome: the invoice finalizes untaxed instead of sticking. It costs real money and leaves no stuck draft behind, so a check that only looks at drafts with errors will never see it.</p>"""},
 {"h": "Roll the findings up by customer",
  "body": """<p>The unit of repair is the customer address, not the invoice. One customer with six months of blocked renewals is one fix and six finalizations; six customers with one each is six fixes. The report should say which of those you have.</p>"""},
 {"h": "Confirm on the customer before changing anything",
  "body": """<p><code>GET /v1/customers/{cus}?expand[]=tax</code> returns <code>tax.automatic_tax</code> and <code>tax.location</code>. <code>unrecognized_location</code> confirms the diagnosis and <code>tax.location</code> shows what Stripe did manage to infer, which is usually an IP-derived country that disagrees with the address on file.</p>"""},
 {"h": "Fix the address, then finalize, in that order",
  "body": """<p>Update the customer with a full <code>address</code> and validate it, then finalize the drafts. Doing it the other way round either fails again or finalizes untaxed. If an address genuinely cannot be obtained, disabling automatic tax on that one invoice before finalizing is a deliberate choice with a cost, not a workaround.</p>"""},
 {"h": "Close the intake that produced the bad addresses",
  "body": """<p>Checkout can be told to require a billing address, and the billing portal can be configured to let customers update their own. Without one of those, the cohort refills.</p>"""},
],
"verify": """<p>Re-run the script after the customer records are fixed and the drafts finalized. No draft should carry a tax finalization error, and no invoice should report tax disabled for want of a location.</p>
<pre><code class="language-bash">python3 stripe_tax_blocked_drafts.py
# clear       0 of 118 draft invoice(s) blocked on tax location</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/invoices</code> filtered to drafts &mdash; a restricted key with read access to Invoices is enough. The classifier takes the four fields that distinguish the outcomes, and their order matters: the finalization error is read before the disabled reason, the disabled reason before the calculation status, and <code>auto_advance</code> last, so a draft that is both stranded and tax-blocked is reported as the thing you can actually fix.",
"py_file": "stripe_tax_blocked_drafts.py",
"py": '''"""Report Stripe draft invoices that cannot finalize because Stripe Tax cannot
locate the customer.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Invoices. The repair is printed, never performed, because finalizing an
invoice sends a real bill and disabling tax on one changes what is owed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_tax_blocked_drafts")

API = "https://api.stripe.com/v1"

TAX_LOCATION_ERROR = "customer_tax_location_invalid"
TAX_DISABLED_FOR_LOCATION = "finalization_requires_location_inputs"

# States that mean a human has to touch the customer record or the invoice.
ACTIONABLE = ("tax-location", "tax-dropped", "needs-address", "tax-failed")


def verdict(error_code, tax_status, disabled_reason, auto_advance):
    """Classify one draft invoice. Pure, so the rules can be tested without a network.

    `error_code` is last_finalization_error.code, `tax_status` is
    automatic_tax.status, `disabled_reason` is automatic_tax.disabled_reason.
    Any of them may be None. Returns (state, detail).
    """
    if error_code == TAX_LOCATION_ERROR:
        return ("tax-location",
                "finalization was attempted and refused: Stripe Tax cannot "
                "resolve this customer's location")
    if disabled_reason == TAX_DISABLED_FOR_LOCATION:
        return ("tax-dropped",
                "Stripe switched automatic tax off so this invoice can finalize; "
                "it will be billed and paid with no tax on it")
    if tax_status == "requires_location_inputs":
        return ("needs-address",
                "the tax calculation cannot run for want of a location; no "
                "finalization attempt has failed yet, but one will")
    if tax_status == "failed":
        return ("tax-failed",
                "the calculation failed on Stripe's side; retry the finalization "
                "before editing the customer")
    if error_code:
        return ("other-error",
                "finalization is failing for a reason that is not tax: %s"
                % (error_code,))
    if not auto_advance:
        return ("not-advancing",
                "auto_advance is false: this draft is outside the collection "
                "workflow rather than blocked by tax")
    return ("clear", "no tax finalization problem recorded on this draft")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def drafts(session, limit):
    """Page every draft invoice. Newest first, as Stripe sends them."""
    out = []
    params = {"status": "draft", "limit": 100}
    while True:
        page = get(session, "/invoices", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def classify(inv):
    """Pull the four fields off an invoice and hand them to verdict()."""
    err = inv.get("last_finalization_error") or {}
    tax = inv.get("automatic_tax") or {}
    return verdict(err.get("code"), tax.get("status"), tax.get("disabled_reason"),
                   bool(inv.get("auto_advance")))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=20,
                    help="how many customers to print")
    ap.add_argument("--max-invoices", type=int, default=2000,
                    help="stop paginating after this many drafts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    seen = 0
    by_customer = {}
    for inv in drafts(s, args.max_invoices):
        seen += 1
        state, detail = classify(inv)
        if state not in ACTIONABLE:
            continue
        cus = inv.get("customer")
        if isinstance(cus, dict):
            cus = cus.get("id")
        entry = by_customer.setdefault(cus or "<no customer>",
                                       {"n": 0, "amount": 0, "state": state,
                                        "detail": detail, "first": inv.get("id")})
        entry["n"] += 1
        entry["amount"] += inv.get("amount_due") or 0

    if not by_customer:
        log.info("%-13s 0 of %d draft invoice(s) blocked on tax location",
                 "clear", seen)
        return 0

    at_stake = sum(e["amount"] for e in by_customer.values())
    log.warning("%-13s %d customer(s), %d draft(s), %d in minor units uncollected",
                "tax-blocked", len(by_customer),
                sum(e["n"] for e in by_customer.values()), at_stake)

    ranked = sorted(by_customer.items(), key=lambda kv: -kv[1]["amount"])
    for cus, e in ranked[:args.top]:
        log.warning("  %-13s %s  %d draft(s)  %d  %s",
                    e["state"], cus, e["n"], e["amount"], e["detail"])
        log.warning("      GET %s/customers/%s?expand[]=tax   read "
                    "tax.automatic_tax and tax.location", API, cus)
        log.warning("      repair: POST %s/customers/%s  address[country]=..  "
                    "address[postal_code]=..  tax[validate_location]=immediately",
                    API, cus)
        log.warning("      then: POST %s/invoices/%s/finalize", API, e["first"])
    if len(ranked) > args.top:
        log.warning("  ... and %d more customer(s)", len(ranked) - args.top)
    log.warning("  fix the customer before the invoice; finalizing first either "
                "fails again or bills with no tax on it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-tax-blocked-drafts.mjs",
"js": '''/**
 * Report Stripe draft invoices that cannot finalize because Stripe Tax cannot
 * locate the customer.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const TAX_LOCATION_ERROR = 'customer_tax_location_invalid';
export const TAX_DISABLED_FOR_LOCATION = 'finalization_requires_location_inputs';

// States that mean a human has to touch the customer record or the invoice.
export const ACTIONABLE = ['tax-location', 'tax-dropped', 'needs-address', 'tax-failed'];

/**
 * Classify one draft invoice. Pure, so the rules can be tested without a network.
 * Any of the first three arguments may be null or undefined.
 */
export function verdict(errorCode, taxStatus, disabledReason, autoAdvance) {
  if (errorCode === TAX_LOCATION_ERROR) {
    return ['tax-location',
      'finalization was attempted and refused: Stripe Tax cannot resolve this ' +
      "customer's location"];
  }
  if (disabledReason === TAX_DISABLED_FOR_LOCATION) {
    return ['tax-dropped',
      'Stripe switched automatic tax off so this invoice can finalize; it will ' +
      'be billed and paid with no tax on it'];
  }
  if (taxStatus === 'requires_location_inputs') {
    return ['needs-address',
      'the tax calculation cannot run for want of a location; no finalization ' +
      'attempt has failed yet, but one will'];
  }
  if (taxStatus === 'failed') {
    return ['tax-failed',
      "the calculation failed on Stripe's side; retry the finalization before " +
      'editing the customer'];
  }
  if (errorCode) {
    return ['other-error',
      `finalization is failing for a reason that is not tax: ${errorCode}`];
  }
  if (!autoAdvance) {
    return ['not-advancing',
      'auto_advance is false: this draft is outside the collection workflow ' +
      'rather than blocked by tax'];
  }
  return ['clear', 'no tax finalization problem recorded on this draft'];
}

/** Pull the four fields off an invoice and hand them to verdict(). */
export function classify(inv) {
  const err = inv.last_finalization_error ?? {};
  const tax = inv.automatic_tax ?? {};
  return verdict(err.code, tax.status, tax.disabled_reason, Boolean(inv.auto_advance));
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

export async function drafts(key, limit = 2000) {
  const out = [];
  const params = { status: 'draft', limit: 100 };
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

  let seen = 0;
  const byCustomer = new Map();
  for (const inv of await drafts(key)) {
    seen += 1;
    const [state, detail] = classify(inv);
    if (!ACTIONABLE.includes(state)) continue;
    const cus = (typeof inv.customer === 'object' && inv.customer !== null
      ? inv.customer.id : inv.customer) ?? '<no customer>';
    const entry = byCustomer.get(cus)
      ?? { n: 0, amount: 0, state, detail, first: inv.id };
    entry.n += 1;
    entry.amount += inv.amount_due ?? 0;
    byCustomer.set(cus, entry);
  }

  if (byCustomer.size === 0) {
    console.log(`${'clear'.padEnd(13)} 0 of ${seen} draft invoice(s) blocked on tax location`);
    return;
  }

  const entries = [...byCustomer.entries()].sort((a, b) => b[1].amount - a[1].amount);
  const drafted = entries.reduce((a, [, e]) => a + e.n, 0);
  const atStake = entries.reduce((a, [, e]) => a + e.amount, 0);
  console.warn(`${'tax-blocked'.padEnd(13)} ${entries.length} customer(s), ${drafted} draft(s), ${atStake} in minor units uncollected`);

  for (const [cus, e] of entries.slice(0, 20)) {
    console.warn(`  ${e.state.padEnd(13)} ${cus}  ${e.n} draft(s)  ${e.amount}  ${e.detail}`);
    console.warn(`      GET ${API}/customers/${cus}?expand[]=tax   read tax.automatic_tax and tax.location`);
    console.warn(`      repair: POST ${API}/customers/${cus}  address[country]=..  address[postal_code]=..  tax[validate_location]=immediately`);
    console.warn(`      then: POST ${API}/invoices/${e.first}/finalize`);
  }
  if (entries.length > 20) console.warn(`  ... and ${entries.length - 20} more customer(s)`);
  console.warn('  fix the customer before the invoice; finalizing first either ' +
               'fails again or bills with no tax on it');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "These tests pin an order rather than a set of outcomes. A blocked draft usually carries several of these fields at once, and reading <code>auto_advance</code> too early turns a fixable address into a note about a stranded invoice, while reading <code>disabled_reason</code> too late hides the case where Stripe already billed the customer with no tax on it.",
"test_py_file": "test_stripe_tax_blocked_drafts.py",
"test_py": '''from stripe_tax_blocked_drafts import verdict


def test_the_finalization_error_is_the_headline():
    state, detail = verdict("customer_tax_location_invalid",
                            "requires_location_inputs", None, True)
    assert state == "tax-location"
    assert "cannot resolve" in detail


def test_tax_dropped_is_reported_even_though_the_invoice_will_finalize():
    # No error and no stuck draft: Stripe disabled tax so the bill could go out.
    # It is the expensive case and the one nothing else surfaces.
    state, detail = verdict(None, "requires_location_inputs",
                            "finalization_requires_location_inputs", True)
    assert state == "tax-dropped"
    assert "no tax on it" in detail


def test_requires_location_inputs_alone_is_a_warning_not_an_error():
    state, _ = verdict(None, "requires_location_inputs", None, True)
    assert state == "needs-address"


def test_a_stripe_side_failure_is_not_the_customers_address():
    state, detail = verdict(None, "failed", None, True)
    assert state == "tax-failed"
    assert "retry the finalization" in detail


def test_a_non_tax_finalization_error_is_kept_separate():
    state, detail = verdict("invoice_payment_intent_requires_action", None, None, True)
    assert state == "other-error"
    assert "not tax" in detail


def test_auto_advance_is_read_last():
    # Both true at once: the tax problem is the one a human can act on, so a
    # stranded draft with a tax error must not be filed as merely stranded.
    assert verdict("customer_tax_location_invalid", None, None, False)[0] == "tax-location"
    assert verdict(None, None, None, False)[0] == "not-advancing"


def test_a_healthy_draft_is_clear():
    assert verdict(None, "complete", None, True)[0] == "clear"
''',
"test_js_file": "stripe-tax-blocked-drafts.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, classify } from './stripe-tax-blocked-drafts.mjs';

test('the finalization error is the headline', () => {
  const [state, detail] = verdict('customer_tax_location_invalid',
    'requires_location_inputs', null, true);
  assert.equal(state, 'tax-location');
  assert.match(detail, /cannot resolve/);
});

test('tax dropped is reported even though the invoice will finalize', () => {
  const [state, detail] = verdict(null, 'requires_location_inputs',
    'finalization_requires_location_inputs', true);
  assert.equal(state, 'tax-dropped');
  assert.match(detail, /no tax on it/);
});

test('requires_location_inputs alone is a warning, not an error', () => {
  assert.equal(verdict(null, 'requires_location_inputs', null, true)[0], 'needs-address');
});

test('a Stripe side failure is not the customer address', () => {
  const [state, detail] = verdict(null, 'failed', null, true);
  assert.equal(state, 'tax-failed');
  assert.match(detail, /retry the finalization/);
});

test('a non tax finalization error is kept separate', () => {
  const [state, detail] = verdict('invoice_payment_intent_requires_action', null, null, true);
  assert.equal(state, 'other-error');
  assert.match(detail, /not tax/);
});

test('auto_advance is read last', () => {
  assert.equal(verdict('customer_tax_location_invalid', null, null, false)[0], 'tax-location');
  assert.equal(verdict(null, null, null, false)[0], 'not-advancing');
});

test('classify reads the nested invoice fields', () => {
  const inv = {
    last_finalization_error: { code: 'customer_tax_location_invalid' },
    automatic_tax: { status: 'requires_location_inputs' },
    auto_advance: true,
  };
  assert.equal(classify(inv)[0], 'tax-location');
  assert.equal(classify({ auto_advance: true, automatic_tax: { status: 'complete' } })[0], 'clear');
});
''',
"faq": [
 ("What address does Stripe Tax actually need?",
  "Enough to identify a taxing jurisdiction. Outside the US a country is generally sufficient. Inside the US it needs a five digit postal code, because rates vary below state level. Canada needs a province or a postal code. An address good enough to ship to can still be too vague to tax against."),
 ("Why is the subscription still active if the invoice never finalized?",
  "Because subscription status tracks payment, and there was never a payment to fail. An unfinalized invoice is not owed, so nothing moves the subscription to past_due or unpaid. Access continues and every retention dashboard counts the customer as healthy."),
 ("Is it safe to just disable automatic tax on the stuck invoice?",
  "It unsticks it, and it bills the customer with no tax on them. If you had an obligation in their jurisdiction you now owe it out of your own margin, and the invoice is a legal record you cannot amend afterwards. It is a defensible choice for a customer whose address is genuinely unobtainable, and a bad default."),
 ("Stripe disabled tax on some invoices by itself. Is that the same problem?",
  "The same cause with the opposite symptom. automatic_tax.disabled_reason of finalization_requires_location_inputs means Stripe chose to let the invoice through untaxed rather than leave it stuck. There is no draft to find and no error to read, which is exactly why the script looks for the field rather than for stuck invoices."),
 ("How do I stop new customers arriving without an address?",
  "Require a billing address in Checkout rather than treating it as optional, and allow address updates in the billing portal so customers can correct their own. Validating the location when the customer is created turns a silent finalization failure months later into an error at signup, where somebody is still paying attention."),
],
"related": [
 ("/stripe/draft-invoices-never-finalized/", "Draft invoices sit for months and never finalize"),
 ("/stripe/automatic-tax-requires-location-inputs/", "automatic_tax reports requires_location_inputs"),
 ("/stripe/customers-missing-address/", "Customers with no address at all"),
],
"citations": [CITE_TAX_INVOICING, CITE_TAX_LOCATIONS, CITE_INVOICE_OBJ, CITE_WORKFLOW],
},

{
"slug": "automatic-tax-requires-location-inputs",
"title": "automatic_tax reports requires_location_inputs on live bills",
"description": "Stripe Tax is on and most invoices are fine, but a slice of them report requires_location_inputs or failed and have already been billed untaxed.",
"h1": "automatic_tax reports requires_location_inputs on live bills",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["automatic_tax requires_location_inputs", "stripe automatic_tax status failed",
             "stripe tax not calculated", "automatic_tax disabled_reason",
             "stripe tax unrecognized_location"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Stripe Tax is enabled, the integration passes <code>automatic_tax[enabled]=true</code> everywhere, and the totals look right on every invoice anyone has opened. They have been opening the wrong ones. A slice of the customers &mdash; the ones whose addresses were never captured properly &mdash; have been billed and paid with no tax calculated, and the invoices carrying that fact are already finalized and immutable.",
"short_answer": """<p>Page <code>GET /v1/invoices?created[gte]=&lt;90 days ago&gt;</code> across every status and read <code>automatic_tax</code> on each. <code>status</code> of <code>requires_location_inputs</code> means the location details on the customer are not valid or not sufficient, so no tax was calculated. <code>status</code> of <code>failed</code> is a Stripe-side calculation error and behaves differently: it is worth retrying before you touch anything.</p>
<p>Read <code>disabled_reason</code> first, though. <code>finalization_requires_location_inputs</code> and <code>finalization_system_error</code> mean automatic tax was switched off at finalization so the invoice could go out, which it did &mdash; billed, paid, and untaxed. Those are the ones that already cost money.</p>
<p>Group by customer and confirm with <code>GET /v1/customers/{cus}?expand[]=tax</code>: <code>tax.automatic_tax</code> of <code>unrecognized_location</code> names the customers whose next invoice will do the same thing.</p>""",
"problem": """<p>Tax that is simply off across the board is a loud problem: every invoice is wrong and somebody notices within a quarter. This is the quiet version. Most invoices calculate correctly, the integration is right, and the Dashboard shows Stripe Tax as active. A minority of customers are silently exempted from the whole mechanism because Stripe cannot tell where they are.</p>
<p>The damage is asymmetric. Where the invoice stuck in draft you can still fix it. Where it finalized without tax, you cannot: finalization freezes the tax lines, the tax IDs and the exemption status onto the document permanently. The invoice was paid, the customer's obligation was discharged at the amount printed on it, and the tax you should have collected is now yours to pay out of margin. Every cycle adds more of them.</p>
<p>It also does not show up as a percentage anyone tracks. Total tax collected goes up month on month because the business is growing. The share of invoices where tax was never calculated is the number that matters, and nothing computes it for you.</p>""",
"why": """<p><strong><code>automatic_tax.status</code> reports the last calculation, not the configuration.</strong> <code>enabled: true</code> with <code>status: requires_location_inputs</code> is a perfectly consistent pair: you asked for tax, Stripe tried, and the customer's location was not good enough to produce one. Any check that reads <code>enabled</code> alone concludes everything is fine.</p>
<p><strong>The customers this happens to arrive in batches.</strong> A Checkout configuration that does not require a billing address, an API integration that creates customers with an email and nothing else, a migration from another billing system that dropped the address column. Each of those produces a cohort, and the cohort is invisible until you count by customer rather than by invoice.</p>
<p><strong><code>failed</code> and <code>requires_location_inputs</code> want opposite responses.</strong> <code>failed</code> is Stripe's side: a retry of the finalization may well succeed and editing the customer record achieves nothing. <code>requires_location_inputs</code> is your data: retrying is guaranteed to fail again until the address is fixed. Treating them as one bucket wastes the effort on whichever half you guessed wrong.</p>
<p><strong>The disabled reason outranks the status.</strong> When Stripe turns automatic tax off at finalization it records why in <code>disabled_reason</code>, and the invoice proceeds. That is worse than a blocked draft and produces no stuck object, so it has to be checked before the status or it gets filed as the milder problem.</p>
<p><strong>A complete calculation of zero is a different note entirely.</strong> <code>status: complete</code> with no tax on the invoice usually means you have no registration in that country, which is a registration problem rather than a location one. Mixing the two produces a report where the two halves need different departments.</p>""",
"steps": [
 {"h": "Read invoices across every status, not just drafts",
  "body": """<p>The expensive cases are finalized and paid. Filtering to drafts finds only the ones that stuck, which is the half you can still fix and the smaller half of the bill.</p>"""},
 {"h": "Bound the window with created[gte]",
  "body": """<p>Ninety days is enough to cover three monthly cycles and to show whether the rate is rising. Going back further makes the report a history lesson: nothing before the current period can be repaired, only credited.</p>"""},
 {"h": "Check disabled_reason before status",
  "body": """<p>An invoice Stripe disabled tax on has already billed. One that merely reports <code>requires_location_inputs</code> may still be a draft. Read the more expensive field first so the ranking of the report matches the ranking of the damage.</p>"""},
 {"h": "Split failed from requires_location_inputs",
  "body": """<p>They are two findings with two different owners. One is a retry, the other is a data fix on the customer. The script should never print them under the same heading.</p>"""},
 {"h": "Roll up by customer and count the repeats",
  "body": """<p>A customer with one affected invoice may have been fixed since. A customer with four consecutive ones is still broken and will produce a fifth. The repeat count is what turns this from a list of invoices into a list of addresses to collect.</p>"""},
 {"h": "Confirm on the customer object",
  "body": """<p><code>GET /v1/customers/{cus}?expand[]=tax</code> gives <code>tax.automatic_tax</code> and <code>tax.location</code>. <code>unrecognized_location</code> is the confirmation; <code>tax.location</code> shows what Stripe inferred and from what source, which is usually where the disagreement is.</p>"""},
 {"h": "Decide what to do about the invoices already out",
  "body": """<p>A finalized invoice cannot be amended. The honest options are a credit note and a reissue, or absorbing the tax. Both are decisions with a number attached, which is why the script totals the affected amounts rather than just counting rows.</p>"""},
],
"verify": """<p>Re-run over the same window once the customer addresses are collected. The share of invoices with a non-complete tax status should fall to zero, and no invoice should report tax disabled for want of a location.</p>
<pre><code class="language-bash">python3 stripe_tax_location_status.py --days 90
# clear       0 of 1,204 invoice(s) with an incomplete tax calculation</code></pre>""",
"code_intro": "One paginated GET over a bounded window &mdash; a restricted key with read access to Invoices is enough, and Customers too if you want the confirmation step. The classifier takes the calculation status, the disabled reason and whether the invoice is finalized, because those three decide whether the answer is a retry, an address to collect, or a credit note.",
"py_file": "stripe_tax_location_status.py",
"py": '''"""Report Stripe invoices where the automatic tax calculation never completed.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Invoices. The repair is printed, never performed, because amending tax
on a customer changes what they owe and a credit note is a legal record.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_tax_location_status")

API = "https://api.stripe.com/v1"

# An invoice past draft has its tax lines frozen; nothing can be recalculated on
# it, only credited.
FINALIZED = ("open", "paid", "uncollectible", "void")

# States where money has already moved with the wrong tax on it.
BILLED = ("billed-untaxed", "billed-unpriced", "frozen")


def verdict(tax_status, disabled_reason, finalized):
    """Classify one invoice's tax calculation. Pure, so it is testable offline.

    `tax_status` is automatic_tax.status, `disabled_reason` is
    automatic_tax.disabled_reason, both possibly None. `finalized` says whether
    the invoice has left draft, which is the point after which the tax on it
    cannot be changed. Returns (state, detail).
    """
    if disabled_reason == "finalization_requires_location_inputs":
        return ("billed-untaxed",
                "automatic tax was switched off at finalization for want of a "
                "location: this invoice went out with no tax and no error")
    if disabled_reason == "finalization_system_error":
        return ("billed-unpriced",
                "Stripe could not calculate at finalization and disabled tax to "
                "let the invoice through")
    if tax_status == "requires_location_inputs":
        if finalized:
            return ("frozen",
                    "the location was not resolvable and the invoice is already "
                    "finalized: the tax on it can no longer be changed")
        return ("blocked",
                "the calculation cannot run for want of a location; still a "
                "draft, so fixing the customer is enough")
    if tax_status == "failed":
        return ("failed",
                "the calculation failed on Stripe's side; retry before assuming "
                "the customer record is wrong")
    if tax_status == "complete":
        return ("complete",
                "the calculation ran; zero tax here is a registration question, "
                "not a location one")
    return ("unknown", "unrecognised automatic_tax.status %r" % (tax_status,))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def invoices_since(session, days, limit):
    """Page invoices created within the window, every status."""
    cutoff = int(time.time() - days * 86400)
    out = []
    params = {"limit": 100, "created[gte]": cutoff}
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
    ap.add_argument("--days", type=float, default=90,
                    help="how far back to read invoices")
    ap.add_argument("--top", type=int, default=20,
                    help="how many customers to print")
    ap.add_argument("--max-invoices", type=int, default=5000,
                    help="stop paginating after this many invoices")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    seen = 0
    by_customer = {}
    for inv in invoices_since(s, args.days, args.max_invoices):
        seen += 1
        tax = inv.get("automatic_tax") or {}
        if not tax.get("enabled"):
            continue
        state, detail = verdict(tax.get("status"), tax.get("disabled_reason"),
                                inv.get("status") in FINALIZED)
        if state in ("complete", "unknown"):
            continue
        cus = inv.get("customer")
        if isinstance(cus, dict):
            cus = cus.get("id")
        entry = by_customer.setdefault(cus or "<no customer>",
                                       {"n": 0, "amount": 0, "billed": 0,
                                        "state": state, "detail": detail})
        entry["n"] += 1
        entry["amount"] += inv.get("total") or 0
        if state in BILLED:
            entry["billed"] += 1

    if not by_customer:
        log.info("%-15s 0 of %d invoice(s) with an incomplete tax calculation",
                 "clear", seen)
        return 0

    affected = sum(e["n"] for e in by_customer.values())
    log.warning("%-15s %d customer(s), %d of %d invoice(s), %d in minor units billed",
                "tax-incomplete", len(by_customer), affected, seen,
                sum(e["amount"] for e in by_customer.values()))

    ranked = sorted(by_customer.items(), key=lambda kv: (-kv[1]["billed"], -kv[1]["n"]))
    for cus, e in ranked[:args.top]:
        log.warning("  %-15s %s  %d invoice(s), %d already billed  %s",
                    e["state"], cus, e["n"], e["billed"], e["detail"])
        log.warning("      GET %s/customers/%s?expand[]=tax   expect "
                    "tax.automatic_tax = unrecognized_location", API, cus)
        if e["state"] != "failed":
            log.warning("      repair: POST %s/customers/%s  address[country]=..  "
                        "address[postal_code]=..  tax[validate_location]=immediately",
                        API, cus)
    if len(ranked) > args.top:
        log.warning("  ... and %d more customer(s)", len(ranked) - args.top)
    log.warning("  invoices already finalized keep the tax they were finalized "
                "with; a credit note and a reissue is the only correction")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-tax-location-status.mjs",
"js": '''/**
 * Report Stripe invoices where the automatic tax calculation never completed.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// An invoice past draft has its tax lines frozen; nothing can be recalculated on
// it, only credited.
export const FINALIZED = ['open', 'paid', 'uncollectible', 'void'];

// States where money has already moved with the wrong tax on it.
export const BILLED = ['billed-untaxed', 'billed-unpriced', 'frozen'];

/**
 * Classify one invoice's tax calculation. Pure, so it is testable offline.
 * `finalized` says whether the invoice has left draft.
 */
export function verdict(taxStatus, disabledReason, finalized) {
  if (disabledReason === 'finalization_requires_location_inputs') {
    return ['billed-untaxed',
      'automatic tax was switched off at finalization for want of a location: ' +
      'this invoice went out with no tax and no error'];
  }
  if (disabledReason === 'finalization_system_error') {
    return ['billed-unpriced',
      'Stripe could not calculate at finalization and disabled tax to let the ' +
      'invoice through'];
  }
  if (taxStatus === 'requires_location_inputs') {
    if (finalized) {
      return ['frozen',
        'the location was not resolvable and the invoice is already finalized: ' +
        'the tax on it can no longer be changed'];
    }
    return ['blocked',
      'the calculation cannot run for want of a location; still a draft, so ' +
      'fixing the customer is enough'];
  }
  if (taxStatus === 'failed') {
    return ['failed',
      "the calculation failed on Stripe's side; retry before assuming the " +
      'customer record is wrong'];
  }
  if (taxStatus === 'complete') {
    return ['complete',
      'the calculation ran; zero tax here is a registration question, not a ' +
      'location one'];
  }
  return ['unknown', `unrecognised automatic_tax.status ${JSON.stringify(taxStatus)}`];
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

export async function invoicesSince(key, days = 90, limit = 5000) {
  const cutoff = Math.floor(Date.now() / 1000 - days * 86400);
  const out = [];
  const params = { limit: 100, 'created[gte]': cutoff };
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

  const days = Number(process.argv[2] ?? 90);
  let seen = 0;
  const byCustomer = new Map();

  for (const inv of await invoicesSince(key, days)) {
    seen += 1;
    const tax = inv.automatic_tax ?? {};
    if (!tax.enabled) continue;
    const [state, detail] = verdict(tax.status, tax.disabled_reason,
      FINALIZED.includes(inv.status));
    if (state === 'complete' || state === 'unknown') continue;
    const cus = (typeof inv.customer === 'object' && inv.customer !== null
      ? inv.customer.id : inv.customer) ?? '<no customer>';
    const entry = byCustomer.get(cus) ?? { n: 0, amount: 0, billed: 0, state, detail };
    entry.n += 1;
    entry.amount += inv.total ?? 0;
    if (BILLED.includes(state)) entry.billed += 1;
    byCustomer.set(cus, entry);
  }

  if (byCustomer.size === 0) {
    console.log(`${'clear'.padEnd(15)} 0 of ${seen} invoice(s) with an incomplete tax calculation`);
    return;
  }

  const entries = [...byCustomer.entries()]
    .sort((a, b) => (b[1].billed - a[1].billed) || (b[1].n - a[1].n));
  const affected = entries.reduce((a, [, e]) => a + e.n, 0);
  const total = entries.reduce((a, [, e]) => a + e.amount, 0);
  console.warn(`${'tax-incomplete'.padEnd(15)} ${entries.length} customer(s), ${affected} of ${seen} invoice(s), ${total} in minor units billed`);

  for (const [cus, e] of entries.slice(0, 20)) {
    console.warn(`  ${e.state.padEnd(15)} ${cus}  ${e.n} invoice(s), ${e.billed} already billed  ${e.detail}`);
    console.warn(`      GET ${API}/customers/${cus}?expand[]=tax   expect tax.automatic_tax = unrecognized_location`);
    if (e.state !== 'failed') {
      console.warn(`      repair: POST ${API}/customers/${cus}  address[country]=..  address[postal_code]=..  tax[validate_location]=immediately`);
    }
  }
  if (entries.length > 20) console.warn(`  ... and ${entries.length - 20} more customer(s)`);
  console.warn('  invoices already finalized keep the tax they were finalized ' +
               'with; a credit note and a reissue is the only correction');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth freezing here. The disabled reason is read before the status, so an invoice Stripe already billed untaxed cannot be filed as a pending problem. And <code>requires_location_inputs</code> splits on whether the invoice is finalized, because that is the line between a customer to fix and a credit note to write.",
"test_py_file": "test_stripe_tax_location_status.py",
"test_py": '''from stripe_tax_location_status import verdict


def test_disabled_reason_outranks_the_status():
    # Both are set on the same invoice. The disabled reason means the bill went
    # out untaxed, which is the more expensive fact and must win.
    state, detail = verdict("requires_location_inputs",
                            "finalization_requires_location_inputs", True)
    assert state == "billed-untaxed"
    assert "no tax and no error" in detail


def test_a_system_error_disable_is_its_own_state():
    state, _ = verdict(None, "finalization_system_error", True)
    assert state == "billed-unpriced"


def test_requires_location_inputs_splits_on_finalization():
    # Still a draft: fixing the customer is the whole repair.
    assert verdict("requires_location_inputs", None, False)[0] == "blocked"
    # Already finalized: the tax on the document is immutable.
    state, detail = verdict("requires_location_inputs", None, True)
    assert state == "frozen"
    assert "no longer be changed" in detail


def test_failed_is_stripe_side_and_wants_a_retry():
    state, detail = verdict("failed", None, True)
    assert state == "failed"
    assert "retry" in detail


def test_complete_is_not_a_location_problem():
    state, detail = verdict("complete", None, True)
    assert state == "complete"
    assert "registration" in detail


def test_an_unrecognised_status_is_not_silently_complete():
    assert verdict(None, None, True)[0] == "unknown"
    assert verdict("pending", None, True)[0] == "unknown"
''',
"test_js_file": "stripe-tax-location-status.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-tax-location-status.mjs';

test('disabled reason outranks the status', () => {
  const [state, detail] = verdict('requires_location_inputs',
    'finalization_requires_location_inputs', true);
  assert.equal(state, 'billed-untaxed');
  assert.match(detail, /no tax and no error/);
});

test('a system error disable is its own state', () => {
  assert.equal(verdict(null, 'finalization_system_error', true)[0], 'billed-unpriced');
});

test('requires_location_inputs splits on finalization', () => {
  assert.equal(verdict('requires_location_inputs', null, false)[0], 'blocked');
  const [state, detail] = verdict('requires_location_inputs', null, true);
  assert.equal(state, 'frozen');
  assert.match(detail, /no longer be changed/);
});

test('failed is Stripe side and wants a retry', () => {
  const [state, detail] = verdict('failed', null, true);
  assert.equal(state, 'failed');
  assert.match(detail, /retry/);
});

test('complete is not a location problem', () => {
  const [state, detail] = verdict('complete', null, true);
  assert.equal(state, 'complete');
  assert.match(detail, /registration/);
});

test('an unrecognised status is not silently complete', () => {
  assert.equal(verdict(null, null, true)[0], 'unknown');
  assert.equal(verdict('pending', null, true)[0], 'unknown');
});
''',
"faq": [
 ("automatic_tax.enabled is true. Why is there no tax on the invoice?",
  "Because enabled describes what you asked for and status describes what happened. requires_location_inputs means Stripe tried to calculate, could not identify a taxing jurisdiction from the customer's details, and produced nothing. The two fields are consistent; only one of them tells you whether tax was actually applied."),
 ("What is the difference between failed and requires_location_inputs?",
  "Ownership. failed is an error on Stripe's side and a retry of the finalization is a reasonable first move. requires_location_inputs is a statement about your data: the customer has no resolvable location, and retrying will produce exactly the same result until an address is added."),
 ("Can I recalculate tax on an invoice that has already been finalized?",
  "No. Finalization freezes the tax lines, the customer tax IDs and the exemption status onto the invoice, because it is the document the customer and both tax authorities work from. Correcting it means issuing a credit note and reissuing, or absorbing the difference."),
 ("Why check disabled_reason before status?",
  "Because it identifies the invoices that were billed rather than blocked. When Stripe disables automatic tax at finalization the invoice proceeds normally and gets paid, so there is no stuck draft and no error for anyone to trip over. Reading status first files those under the milder finding."),
 ("Every invoice says complete and there is still no tax. Is this the same bug?",
  "No, and that is why complete is its own state here. A completed calculation of zero usually means you hold no registration in the buyer's country, so Stripe correctly calculated that it should collect nothing. That is a registrations problem with a different repair."),
],
"related": [
 ("/stripe/draft-invoices-blocked-by-tax-location/", "Draft invoices blocked on customer_tax_location_invalid"),
 ("/stripe/no-tax-registrations-while-selling-abroad/", "No tax registrations while invoicing many countries"),
 ("/stripe/customers-missing-address/", "Customers with no address at all"),
],
"citations": [CITE_INVOICE_OBJ, CITE_TAX_LOCATIONS, CITE_TAX_INVOICING, CITE_CUSTOMER_OBJ],
},

{
"slug": "missing-customer-tax-ids-b2b-eu",
"title": "EU business invoices with no VAT number miss reverse charge",
"description": "Stripe applies reverse charge from the tax ID on the invoice. With no ID, a business buyer is treated as a consumer and charged local VAT it should not pay.",
"h1": "EU business invoices with no VAT number miss reverse charge",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe customer_tax_ids empty", "stripe reverse charge not applied",
             "stripe eu_vat tax id", "stripe b2b vat invoice",
             "stripe tax id verification unverified"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A German customer's finance team refuses the invoice. It has their company name on it, it has VAT added to it, and it has no VAT number and no reverse-charge notice anywhere on the document &mdash; so as far as their accounts payable is concerned it is a consumer receipt, and they cannot reclaim anything against it. Stripe did nothing wrong: with no tax ID on the customer, a business buyer is a consumer.",
"short_answer": """<p>Page <code>GET /v1/invoices?status=paid&amp;created[gte]=&lt;180 days ago&gt;</code> and flag the rows where <code>customer_tax_ids</code> is empty, <code>customer_address.country</code> is an EU member state, <code>customer_tax_exempt</code> is <code>none</code>, and tax was actually charged. That combination is a business being billed as a consumer.</p>
<p>Then check the ones that do have an ID: <code>GET /v1/customers/{cus}/tax_ids</code> and read <code>verification.status</code>. An <code>unverified</code> or <code>unavailable</code> <code>eu_vat</code> is a number VIES did not confirm, which is not a number you want to be defending in an audit.</p>
<p>Both are urgent for the same reason: finalization freezes <code>customer_tax_ids</code> and <code>customer_tax_exempt</code> onto the invoice permanently. Adding the VAT number tomorrow does nothing for the documents already sent.</p>""",
"problem": """<p>Cross-border B2B inside the EU normally moves the VAT obligation to the buyer. The seller invoices without VAT, states that the reverse charge applies, and the buyer accounts for it themselves. Stripe Tax will do this automatically, but it decides based on the tax ID attached to the customer and the jurisdictions involved. No tax ID, no business buyer, no reverse charge.</p>
<p>So the invoice goes out with local VAT on it. The buyer has been charged something like nineteen or twenty-one per cent that they did not owe, on a document that cannot support a reclaim because it names no VAT number. Their options are to eat it or to come back to you, and the ones who understand the rules come back.</p>
<p>The part that makes this expensive rather than annoying is timing. The tax IDs and the exemption status on an invoice are captured at finalization and never change afterwards. A customer who sends you their VAT number in month seven has six months of invoices that are permanently wrong, and each one needs a credit note and a reissue to correct.</p>""",
"why": """<p><strong>The tax ID is what identifies a business, and it is optional everywhere.</strong> Checkout does not collect tax IDs unless you switch it on. The billing portal does not let customers add one unless you allow that field. The API accepts a customer with an address and no tax ID without complaint. Every default in the product produces a consumer.</p>
<p><strong>Nothing about the invoice looks wrong from your side.</strong> The tax calculated, the status is <code>complete</code>, the payment succeeded and the revenue is higher than it would have been with the reverse charge applied. There is no error, no failed calculation and no unusual field; the only signal is an empty array on a document that should not have one.</p>
<p><strong>An unverified number is worse than an obvious gap.</strong> A tax ID whose <code>verification.status</code> is <code>unverified</code> was submitted and not confirmed by VIES, and one that is <code>unavailable</code> could not be checked at all. Both look like coverage in a list of customers with tax IDs, and neither is something you would want to rely on if the treatment of those invoices is ever questioned.</p>
<p><strong>Zero tax with no ID is a different finding and gets conflated with this one.</strong> If an EU invoice carries no tax and no tax ID, reverse charge is not what happened: it is far more likely you hold no registration in that country and Stripe correctly calculated nothing. Same-looking invoice, entirely different repair.</p>
<p><strong>Nobody checks, because the customers who care tell you.</strong> The ones who complain get fixed one at a time through support. The ones who do not complain quietly keep paying VAT they do not owe, and they are the majority, which is exactly why the count only appears when something goes looking for it.</p>""",
"steps": [
 {"h": "Bound the window and read paid invoices",
  "body": """<p>A hundred and eighty days covers two VAT quarters in most member states, which is the horizon over which a correction is still a routine credit note rather than a filing amendment. Paid invoices are the ones where money moved.</p>"""},
 {"h": "Filter to EU destinations using the invoice's own address",
  "body": """<p>Use <code>customer_address.country</code> from the invoice, not the customer's current address. The invoice records where the customer was when it was finalized, and that is the address the tax treatment was based on.</p>"""},
 {"h": "Read customer_tax_exempt before the ID list",
  "body": """<p><code>reverse</code> means the reverse charge was applied and the invoice is correct. <code>exempt</code> means no VAT was due for another reason. Only <code>none</code> is the case where a missing ID actually cost the customer money, and checking it first keeps correctly handled invoices out of the report.</p>"""},
 {"h": "Separate the taxed from the untaxed",
  "body": """<p>An EU invoice with no ID and VAT on it is a business charged as a consumer. An EU invoice with no ID and no VAT is almost certainly a missing registration. Both are findings; they belong on different lists and go to different people.</p>"""},
 {"h": "Check verification on the IDs that do exist",
  "body": """<p><code>GET /v1/customers/{cus}/tax_ids</code> and read <code>verification.status</code> per ID. <code>verified</code> is the only reassuring value. <code>pending</code> is fine for something added minutes ago and suspicious on something added last year.</p>"""},
 {"h": "Collect the numbers at the point of sale, not afterwards",
  "body": """<p>Enable tax ID collection in Checkout and allow the tax ID field in the billing portal. Both are configuration rather than code, and both stop the problem at the only moment when the invoice has not been written yet.</p>"""},
 {"h": "Correct the invoices already sent, deliberately",
  "body": """<p>Finalized invoices cannot be edited, so correcting one means a credit note and a reissue. Total the exposure before deciding how far back to go; for small amounts the honest answer is often to fix it going forward and tell the customer why.</p>"""},
],
"verify": """<p>Re-run after tax ID collection is switched on. New EU business invoices should carry either a verified tax ID or a <code>reverse</code> exemption, and the count of taxed invoices with no ID should stop growing.</p>
<pre><code class="language-bash">python3 stripe_eu_vat_ids.py --days 180
# clear       0 of 412 EU invoice(s) billed to a business as a consumer</code></pre>""",
"code_intro": "One paginated GET over invoices, plus one small GET per flagged customer for the verification status &mdash; a restricted key with read access to Invoices and Customers is enough. The classifier is pure and takes the four fields the invoice already carries plus the verification status, because the difference between <em>charged VAT it did not owe</em> and <em>zero tax for want of a registration</em> is the difference between a credit note and a different note entirely.",
"py_file": "stripe_eu_vat_ids.py",
"py": '''"""Report EU business invoices billed with VAT because no tax ID was on file.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Invoices and Customers. The repair is printed, never performed, because
a credit note is a legal record and reissuing an invoice rebills a customer.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_eu_vat_ids")

API = "https://api.stripe.com/v1"

# The 27 member states. Reverse charge is an intra-EU mechanism, so a country
# outside this set is a different question with a different answer.
EU = frozenset("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL "
               "PT RO SK SI ES SE".split())

# Verification results that are not a confirmation. `pending` is normal for a few
# minutes and a problem after a few months.
UNCONFIRMED = ("unverified", "unavailable", "pending")


def verdict(country, invoice_tax_ids, tax_exempt, tax_amount, verification):
    """Classify one paid invoice. Pure, so the rules can be tested without a network.

    `invoice_tax_ids` is the invoice's customer_tax_ids array, frozen at
    finalization. `tax_exempt` is customer_tax_exempt. `tax_amount` is the tax
    actually charged in minor units. `verification` is the status of the
    customer's tax ID, or None when there is not one. Returns (state, detail).
    """
    if country not in EU:
        return ("out-of-scope",
                "%s is outside the EU: the reverse charge does not apply here"
                % (country or "no country on the invoice",))
    if tax_exempt == "reverse":
        return ("reverse-charge",
                "billed under the reverse charge; the buyer accounts for the VAT")
    if tax_exempt == "exempt":
        return ("exempt",
                "recorded as exempt, so no VAT was due and none was charged")
    if not invoice_tax_ids:
        if tax_amount:
            return ("charged-vat",
                    "no customer_tax_ids on the invoice and %d in tax charged: a "
                    "business was billed as a consumer" % tax_amount)
        return ("no-id-no-vat",
                "no tax ID and no VAT either; that is a registration question "
                "rather than a reverse charge one")
    if verification in UNCONFIRMED:
        return ("unverified",
                "a tax ID is on the invoice but its verification status is %r: "
                "not a number to rely on" % (verification,))
    return ("ok", "a verified tax ID is recorded on the invoice")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def paid_invoices(session, days, limit):
    """Page paid invoices created within the window."""
    cutoff = int(time.time() - days * 86400)
    out = []
    params = {"status": "paid", "limit": 100, "created[gte]": cutoff}
    while True:
        page = get(session, "/invoices", **params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def verification_status(session, customer_id, cache):
    """Weakest verification status across a customer's tax IDs, or None."""
    if customer_id in cache:
        return cache[customer_id]
    status = None
    try:
        ids = get(session, "/customers/%s/tax_ids" % customer_id,
                  limit=10).get("data", [])
    except requests.HTTPError:
        ids = []
    for tid in ids:
        s = (tid.get("verification") or {}).get("status")
        if s in UNCONFIRMED:
            status = s
            break
        status = status or s
    cache[customer_id] = status
    return status


def tax_charged(inv):
    """Total tax on the invoice in minor units, across every tax line."""
    return sum(t.get("amount") or 0 for t in (inv.get("total_taxes") or []))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=float, default=180,
                    help="how far back to read paid invoices")
    ap.add_argument("--top", type=int, default=20,
                    help="how many invoices to print")
    ap.add_argument("--max-invoices", type=int, default=5000,
                    help="stop paginating after this many invoices")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    cache = {}
    eu_seen = 0
    findings = []
    for inv in paid_invoices(s, args.days, args.max_invoices):
        country = ((inv.get("customer_address") or {}).get("country") or "")
        if country not in EU:
            continue
        eu_seen += 1
        cus = inv.get("customer")
        if isinstance(cus, dict):
            cus = cus.get("id")
        ids = inv.get("customer_tax_ids") or []
        verification = verification_status(s, cus, cache) if ids and cus else None
        state, detail = verdict(country, ids, inv.get("customer_tax_exempt"),
                                tax_charged(inv), verification)
        if state in ("charged-vat", "unverified", "no-id-no-vat"):
            findings.append((state, inv.get("id", "<no id>"), cus, country,
                             tax_charged(inv), detail))

    if not findings:
        log.info("%-13s 0 of %d EU invoice(s) billed to a business as a consumer",
                 "clear", eu_seen)
        return 0

    charged = [f for f in findings if f[0] == "charged-vat"]
    log.warning("%-13s %d of %d EU invoice(s) flagged, %d charged VAT with no "
                "tax ID, %d in minor units", "no-tax-id", len(findings), eu_seen,
                len(charged), sum(f[4] for f in charged))

    findings.sort(key=lambda f: -f[4])
    for state, inv_id, cus, country, tax, detail in findings[:args.top]:
        log.warning("  %-13s %s  %s  %s  %d  %s",
                    state, inv_id, cus, country, tax, detail)
        if state == "charged-vat":
            log.warning("      repair: POST %s/tax_ids  type=eu_vat  "
                        "value=%s123456789  owner[type]=customer  owner[customer]=%s",
                        API, country, cus)
            log.warning("      the invoice itself is frozen: correct it with a "
                        "credit note and a reissue, not an edit")
    if len(findings) > args.top:
        log.warning("  ... and %d more", len(findings) - args.top)
    log.warning("  then switch on tax ID collection in Checkout and allow the "
                "tax_id field in the billing portal, or the list refills")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-eu-vat-ids.mjs",
"js": '''/**
 * Report EU business invoices billed with VAT because no tax ID was on file.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Invoices and Customers. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// The 27 member states. Reverse charge is an intra-EU mechanism, so a country
// outside this set is a different question with a different answer.
export const EU = new Set(('AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT ' +
  'LU MT NL PL PT RO SK SI ES SE').split(' '));

// Verification results that are not a confirmation. `pending` is normal for a
// few minutes and a problem after a few months.
export const UNCONFIRMED = ['unverified', 'unavailable', 'pending'];

/**
 * Classify one paid invoice. Pure, so the rules can be tested without a network.
 * `invoiceTaxIds` is the invoice's customer_tax_ids array, frozen at finalization.
 */
export function verdict(country, invoiceTaxIds, taxExempt, taxAmount, verification) {
  if (!EU.has(country)) {
    return ['out-of-scope',
      `${country || 'no country on the invoice'} is outside the EU: the reverse ` +
      'charge does not apply here'];
  }
  if (taxExempt === 'reverse') {
    return ['reverse-charge',
      'billed under the reverse charge; the buyer accounts for the VAT'];
  }
  if (taxExempt === 'exempt') {
    return ['exempt', 'recorded as exempt, so no VAT was due and none was charged'];
  }
  if (!invoiceTaxIds || invoiceTaxIds.length === 0) {
    if (taxAmount) {
      return ['charged-vat',
        `no customer_tax_ids on the invoice and ${taxAmount} in tax charged: a ` +
        'business was billed as a consumer'];
    }
    return ['no-id-no-vat',
      'no tax ID and no VAT either; that is a registration question rather than ' +
      'a reverse charge one'];
  }
  if (UNCONFIRMED.includes(verification)) {
    return ['unverified',
      `a tax ID is on the invoice but its verification status is ` +
      `${JSON.stringify(verification)}: not a number to rely on`];
  }
  return ['ok', 'a verified tax ID is recorded on the invoice'];
}

/** Total tax on the invoice in minor units, across every tax line. */
export function taxCharged(inv) {
  return (inv.total_taxes ?? []).reduce((a, t) => a + (t.amount ?? 0), 0);
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

export async function paidInvoices(key, days = 180, limit = 5000) {
  const cutoff = Math.floor(Date.now() / 1000 - days * 86400);
  const out = [];
  const params = { status: 'paid', limit: 100, 'created[gte]': cutoff };
  for (;;) {
    const page = await get(key, '/invoices', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

async function verificationStatus(key, customerId, cache) {
  if (cache.has(customerId)) return cache.get(customerId);
  let status = null;
  try {
    const { data = [] } = await get(key, `/customers/${customerId}/tax_ids`, { limit: 10 });
    for (const tid of data) {
      const s = tid.verification?.status;
      if (UNCONFIRMED.includes(s)) { status = s; break; }
      status = status ?? s ?? null;
    }
  } catch {
    status = null;
  }
  cache.set(customerId, status);
  return status;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.argv[2] ?? 180);
  const cache = new Map();
  let euSeen = 0;
  const findings = [];

  for (const inv of await paidInvoices(key, days)) {
    const country = inv.customer_address?.country ?? '';
    if (!EU.has(country)) continue;
    euSeen += 1;
    const cus = (typeof inv.customer === 'object' && inv.customer !== null
      ? inv.customer.id : inv.customer) ?? null;
    const ids = inv.customer_tax_ids ?? [];
    const verification = ids.length && cus
      ? await verificationStatus(key, cus, cache) : null;
    const tax = taxCharged(inv);
    const [state, detail] = verdict(country, ids, inv.customer_tax_exempt, tax, verification);
    if (['charged-vat', 'unverified', 'no-id-no-vat'].includes(state)) {
      findings.push({ state, id: inv.id ?? '<no id>', cus, country, tax, detail });
    }
  }

  if (findings.length === 0) {
    console.log(`${'clear'.padEnd(13)} 0 of ${euSeen} EU invoice(s) billed to a business as a consumer`);
    return;
  }

  const charged = findings.filter((f) => f.state === 'charged-vat');
  const chargedTax = charged.reduce((a, f) => a + f.tax, 0);
  console.warn(`${'no-tax-id'.padEnd(13)} ${findings.length} of ${euSeen} EU invoice(s) flagged, ${charged.length} charged VAT with no tax ID, ${chargedTax} in minor units`);

  findings.sort((a, b) => b.tax - a.tax);
  for (const f of findings.slice(0, 20)) {
    console.warn(`  ${f.state.padEnd(13)} ${f.id}  ${f.cus}  ${f.country}  ${f.tax}  ${f.detail}`);
    if (f.state === 'charged-vat') {
      console.warn(`      repair: POST ${API}/tax_ids  type=eu_vat  value=${f.country}123456789  owner[type]=customer  owner[customer]=${f.cus}`);
      console.warn('      the invoice itself is frozen: correct it with a credit note and a reissue, not an edit');
    }
  }
  if (findings.length > 20) console.warn(`  ... and ${findings.length - 20} more`);
  console.warn('  then switch on tax ID collection in Checkout and allow the ' +
               'tax_id field in the billing portal, or the list refills');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that has to be separated is an EU invoice with no tax ID and no tax on it. It looks identical to the expensive one in every field a quick check would read, and it is not the same finding at all: nobody was overcharged, and the reason there is no VAT is almost certainly that you hold no registration in that country. Merging the two produces a report where most of the rows are somebody else's problem.",
"test_py_file": "test_stripe_eu_vat_ids.py",
"test_py": '''from stripe_eu_vat_ids import verdict


def test_outside_the_eu_is_not_a_reverse_charge_question():
    state, _ = verdict("US", [], "none", 800, None)
    assert state == "out-of-scope"
    assert verdict("", [], "none", 800, None)[0] == "out-of-scope"


def test_an_eu_business_with_no_id_and_vat_charged_is_the_finding():
    state, detail = verdict("DE", [], "none", 1900, None)
    assert state == "charged-vat"
    assert "1900" in detail


def test_no_id_and_no_vat_is_a_registration_question():
    # Same empty tax ID list, no money lost by the customer, different owner.
    state, detail = verdict("FR", [], "none", 0, None)
    assert state == "no-id-no-vat"
    assert "registration" in detail


def test_reverse_charge_is_checked_before_the_id_list():
    # customer_tax_exempt can carry the treatment even where the invoice's
    # frozen tax ID array reads empty.
    assert verdict("NL", [], "reverse", 0, None)[0] == "reverse-charge"
    assert verdict("NL", [], "exempt", 0, None)[0] == "exempt"


def test_an_unconfirmed_id_is_not_coverage():
    for status in ("unverified", "unavailable", "pending"):
        state, detail = verdict("IT", [{"type": "eu_vat"}], "none", 0, status)
        assert state == "unverified"
        assert status in detail


def test_a_verified_id_is_the_only_clean_result():
    assert verdict("ES", [{"type": "eu_vat"}], "none", 0, "verified")[0] == "ok"
''',
"test_js_file": "stripe-eu-vat-ids.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, taxCharged } from './stripe-eu-vat-ids.mjs';

test('outside the EU is not a reverse charge question', () => {
  assert.equal(verdict('US', [], 'none', 800, null)[0], 'out-of-scope');
  assert.equal(verdict('', [], 'none', 800, null)[0], 'out-of-scope');
});

test('an EU business with no ID and VAT charged is the finding', () => {
  const [state, detail] = verdict('DE', [], 'none', 1900, null);
  assert.equal(state, 'charged-vat');
  assert.match(detail, /1900/);
});

test('no ID and no VAT is a registration question', () => {
  const [state, detail] = verdict('FR', [], 'none', 0, null);
  assert.equal(state, 'no-id-no-vat');
  assert.match(detail, /registration/);
});

test('reverse charge is checked before the ID list', () => {
  assert.equal(verdict('NL', [], 'reverse', 0, null)[0], 'reverse-charge');
  assert.equal(verdict('NL', [], 'exempt', 0, null)[0], 'exempt');
});

test('an unconfirmed ID is not coverage', () => {
  for (const status of ['unverified', 'unavailable', 'pending']) {
    const [state, detail] = verdict('IT', [{ type: 'eu_vat' }], 'none', 0, status);
    assert.equal(state, 'unverified');
    assert.match(detail, new RegExp(status));
  }
});

test('a verified ID is the only clean result', () => {
  assert.equal(verdict('ES', [{ type: 'eu_vat' }], 'none', 0, 'verified')[0], 'ok');
});

test('tax is summed across every tax line on the invoice', () => {
  assert.equal(taxCharged({ total_taxes: [{ amount: 190 }, { amount: 10 }] }), 200);
  assert.equal(taxCharged({}), 0);
});
''',
"faq": [
 ("Why did Stripe charge VAT to a business customer?",
  "Because nothing on the customer said it was a business. Stripe Tax applies the reverse charge based on a tax ID being present and the jurisdictions involved; with an empty tax ID list the sale is treated as B2C and local VAT is added. The company name on the address makes no difference to the calculation."),
 ("Can I add the VAT number to an invoice that already went out?",
  "No. customer_tax_ids and customer_tax_exempt are copied onto the invoice at finalization and are fixed there, because the invoice is the document both parties file against. Attaching the tax ID to the customer fixes every future invoice and none of the past ones; correcting an old one means a credit note and a reissue."),
 ("What does an unverified tax ID mean?",
  "That the number was submitted and VIES did not confirm it. unavailable means the check could not be performed at all, and pending means it is still in flight, which is unremarkable for a minute and worth investigating after a month. Only verified is a confirmation, and it is the only status worth counting as coverage."),
 ("Some EU invoices have no tax ID and no VAT. Is that the same problem?",
  "No, and the script keeps them apart. Zero VAT with no tax ID usually means you hold no active tax registration in that country, so Stripe calculated correctly and collected nothing. Nobody was overcharged, and the repair is a registration rather than a tax ID."),
 ("How do I stop collecting business customers without their VAT number?",
  "Enable tax ID collection in Checkout so it is asked for at the point of sale, and allow the tax_id field in the billing portal so a customer who forgot can add it themselves. Both are configuration. Anything that relies on a support conversation will catch only the customers who already knew they were being overcharged."),
],
"related": [
 ("/stripe/no-tax-registrations-while-selling-abroad/", "No tax registrations while invoicing many countries"),
 ("/stripe/automatic-tax-requires-location-inputs/", "automatic_tax reports requires_location_inputs"),
 ("/stripe/prices-with-tax-behavior-unspecified/", "Prices left at tax_behavior unspecified break tax math"),
],
"citations": [CITE_TAX_IDS, CITE_TAX_ID_OBJ, CITE_INVOICE_LIST, CITE_ZERO_TAX],
},

]
