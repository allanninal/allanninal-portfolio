#!/usr/bin/env python3
"""/stripe/ field notes, batch M — the writing.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair
for a human to run against a live payments account.

This batch is about the arithmetic on an invoice rather than its delivery:
usage that was never metered, one-off charges that never reached a document,
and the two tax settings that let a calculation succeed at zero.
"""

CITE_METER_OBJ = ("The meter object — Stripe API reference",
                  "https://docs.stripe.com/api/billing/meter/object")
CITE_METER_SUMMARIES = ("List meter event summaries — Stripe API reference",
                        "https://docs.stripe.com/api/billing/meter-event_summary/list")
CITE_USAGE_BASED = ("Usage-based billing — Stripe Docs",
                    "https://docs.stripe.com/billing/subscriptions/usage-based")
CITE_SUB_OBJ = ("The subscription object — Stripe API reference",
                "https://docs.stripe.com/api/subscriptions/object")
CITE_INVOICEITEM_LIST = ("List all invoice items — Stripe API reference",
                         "https://docs.stripe.com/api/invoiceitems/list")
CITE_INVOICEITEM_OBJ = ("The invoice item object — Stripe API reference",
                        "https://docs.stripe.com/api/invoiceitems/object")
CITE_PRORATIONS = ("Prorations — Stripe Docs",
                   "https://docs.stripe.com/billing/subscriptions/prorations")
CITE_INVOICE_OBJ = ("The invoice object — Stripe API reference",
                    "https://docs.stripe.com/api/invoices/object")
CITE_REGISTRATIONS = ("List tax registrations — Stripe API reference",
                      "https://docs.stripe.com/api/tax/registrations/all")
CITE_ZERO_TAX = ("Zero tax amounts — Stripe Docs", "https://docs.stripe.com/tax/zero-tax")
CITE_TAX_MONITORING = ("Monitor your tax obligations — Stripe Docs",
                       "https://docs.stripe.com/tax/monitoring")
CITE_PRICE_OBJ = ("The price object — Stripe API reference",
                  "https://docs.stripe.com/api/prices/object")
CITE_PRODUCT_OBJ = ("The product object — Stripe API reference",
                    "https://docs.stripe.com/api/products/object")
CITE_TAX_INVOICING = ("Stripe Tax and invoicing — Stripe Docs",
                      "https://docs.stripe.com/tax/invoicing")

GUIDES = [

{
"slug": "metered-items-with-no-usage-reported",
"title": "Metered subscription items with no usage reported",
"description": "Usage-based subscriptions invoice for zero every cycle. The meter aggregated nothing, because the emitter's event name never matched the meter.",
"h1": "metered subscription items with no usage reported",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe metered usage zero", "billing meter no events",
             "stripe meter event_name mismatch", "usage based billing invoice 0",
             "stripe meter event summaries empty"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The invoice goes out with the usage line at zero. The customer has been hammering the API all month and your own dashboards say so, but Stripe has no record of a single unit. The subscription is active, the price is metered, nothing has errored anywhere, and the invoice has already finalized, which is the point past which usage cannot be added to it.",
"short_answer": """<p>For every active subscription item whose <code>price.recurring.usage_type</code> is <code>metered</code>, read the meter it points at and ask what that meter aggregated for that customer this period: <code>GET /v1/billing/meters/{meter}/event_summaries?customer={cus}&amp;start_time=...&amp;end_time=...</code>.</p>
<p>No rows at all means the events never matched the meter's <code>event_name</code> or its <code>customer_mapping.event_payload_key</code>, so Stripe dropped them on arrival. Rows that all aggregate to <code>0</code> mean the events landed but the value key did not match <code>value_settings.event_payload_key</code>. The two look identical on the invoice and have different repairs.</p>""",
"problem": """<p>The way this is normally found is a customer asking why their bill is so low, which is a conversation nobody wants to have in either direction. Everything upstream of the meter looks healthy: the emitter is running, its logs show events being posted, the HTTP responses are 2xx, the subscription is active and renewing. The gap is entirely inside Stripe, between accepting an event and counting it.</p>
<p>What makes it expensive rather than merely wrong is the finalization boundary. Meter events belong to a period; once that period's invoice finalizes, backfilling into it is not possible. Every cycle that passes undetected is a cycle of revenue that has to be recovered as a separate charge and explained to the customer, or written off. A check that runs mid-period is worth several times one that runs monthly, because mid-period there is still something to do about it.</p>""",
"why": """<p><strong>A meter drops what it does not recognise, and dropping is not an error.</strong> Meter events are matched by <code>event_name</code>. An emitter sending <code>api_requests</code> to a meter named <code>api_request</code> is posting valid, accepted events into nothing. There is no failed request and no alert to fire, because from the API's point of view nothing went wrong.</p>
<p><strong>The customer is resolved by a payload key, not by the request.</strong> The meter's <code>customer_mapping.event_payload_key</code> names the field inside <code>payload</code> that holds the customer id, and it defaults to <code>stripe_customer_id</code>. An emitter that sends <code>customer_id</code> instead produces events that exist but attach to nobody, so the summaries for the actual customer stay empty while a count somewhere else looks reassuringly non-zero.</p>
<p><strong>The value is a second, separate key.</strong> <code>value_settings.event_payload_key</code> defaults to <code>value</code>. Send <code>units</code> and the events arrive, attach to the right customer, and aggregate to zero. This is the version of the bug that survives longest, because the meter clearly is receiving traffic.</p>
<p><strong>Reconciliation happens at invoice time and nowhere else.</strong> Billing Meters do not push a "your usage is suspiciously zero" signal. The first moment the mismatch becomes visible in Stripe is the invoice, which is also the last moment you could have done anything cheap about it.</p>""",
"steps": [
 {"h": "Find the metered items and the meter each one points at",
  "body": """<p><code>GET /v1/subscriptions?status=active&amp;limit=100&amp;expand[]=data.items.data.price</code>. An item is metered when <code>price.recurring.usage_type</code> is <code>metered</code>, and <code>price.recurring.meter</code> holds the id of the meter that bills it. Prices created before Billing Meters have no <code>meter</code> field, and those have to be matched against <code>GET /v1/billing/meters?status=active</code> by hand.</p>"""},
 {"h": "Ask the meter what it aggregated for that customer, this period",
  "body": """<p><code>GET /v1/billing/meters/{meter}/event_summaries?customer={cus}&amp;start_time=...&amp;end_time=...</code>. The period bounds live on the subscription item as <code>current_period_start</code> and <code>current_period_end</code> on recent API versions, and on the subscription itself on older ones, so read the item first and fall back. Floor both timestamps to the hour; the endpoint expects bounds aligned to the meter's grouping window and rejects them otherwise.</p>"""},
 {"h": "Separate no rows from zero-valued rows",
  "body": """<p>Empty <code>data</code> means nothing ever matched this meter for this customer: suspect <code>event_name</code> first, then <code>customer_mapping.event_payload_key</code>. Rows present with every <code>aggregated_value</code> at <code>0</code> means the matching worked and the value did not: that is <code>value_settings.event_payload_key</code>. Reporting these as one finding wastes the afternoon.</p>"""},
 {"h": "Give a fresh period the benefit of the doubt",
  "body": """<p>A period that opened an hour ago legitimately has no usage on a product billed daily. Suppress anything inside a few hours of <code>current_period_start</code>, and say so in the output rather than silently, so nobody concludes the check is broken when it reports nothing on the first of the month.</p>"""},
 {"h": "Count the cycles already billed at zero",
  "body": """<p><code>GET /v1/invoices?subscription={sub}&amp;status=paid&amp;limit=10</code> and look for lines at <code>amount = 0</code>. That count is the difference between "fix the emitter" and "fix the emitter and decide what to do about four months of unbilled usage", and it is the number the finance conversation actually needs.</p>"""},
 {"h": "Compare the emitter's payload with the meter, field by field",
  "body": """<p><code>GET /v1/billing/meters/{id}</code> returns the three fields that have to match: <code>event_name</code>, <code>customer_mapping.event_payload_key</code>, <code>value_settings.event_payload_key</code>. Put them next to one real payload from your emitter. The mismatch is always visible in that comparison, and almost never visible in the emitter's own logs.</p>"""},
],
"verify": """<p>Re-run the script mid-period once the emitter is corrected. Every metered item should report usage against its meter.</p>
<pre><code class="language-bash">python3 stripe_metered_usage.py
# reporting  sub_123 / si_abc  meter mtr_9: 41,208 unit(s) so far this period</code></pre>""",
"code_intro": "Three GETs and no writes &mdash; a restricted key with read access to Subscriptions, Billing Meters and Invoices is enough, and is what you should give it. The classifier is pure and takes the aggregated total, the number of summary rows, how far into the period we are, and how many closed invoices already billed zero, because those four facts are what separate a quiet Tuesday morning from four months of lost revenue.",
"py_file": "stripe_metered_usage.py",
"py": '''"""Report metered subscription items that no usage has been recorded against.

Read only. Three GETs, no writes: give this a RESTRICTED key with read access to
Subscriptions, Billing Meters and Invoices. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_metered_usage")

API = "https://api.stripe.com/v1"

# A period that opened minutes ago has no usage yet on almost any product, and
# reporting that as a fault trains people to ignore the check on the 1st.
GRACE_HOURS = 6


def verdict(aggregated_value, summary_rows, hours_into_period, zero_billed_cycles):
    """Classify one metered subscription item. Pure, so the rules can be tested.

    `aggregated_value` is the sum of aggregated_value across the meter's event
    summaries for this customer and period, `summary_rows` how many rows came
    back, `hours_into_period` how far into the current period we are, and
    `zero_billed_cycles` how many already-paid invoices carry a zero line.
    Returns (state, detail).
    """
    if aggregated_value:
        return ("reporting",
                "%s unit(s) so far this period" % format(aggregated_value, ",g"))
    if hours_into_period < GRACE_HOURS:
        return ("early",
                "the period is %.1fh old; too early to call zero a fault"
                % hours_into_period)

    if summary_rows:
        cause = ("%d summary row(s) and every one aggregates to 0: the events "
                 "arrive and carry no value. Check value_settings."
                 "event_payload_key against the payload." % summary_rows)
        state = "zero-valued"
    else:
        cause = ("no meter event summaries at all for this customer: the events "
                 "never matched. Check event_name first, then customer_mapping."
                 "event_payload_key.")
        state = "silent"

    if zero_billed_cycles:
        return ("billed-zero",
                "%d closed invoice(s) already billed a zero line. %s"
                % (zero_billed_cycles, cause))
    return (state, cause)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def paginate(session, path, **params):
    params = dict(params, limit=params.get("limit", 100))
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for row in data:
            yield row
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def period_bounds(sub, item):
    """Current period for an item.

    current_period_start and current_period_end moved from the subscription onto
    each subscription item, because items on one subscription can now bill on
    different cycles. Read the item, fall back to the subscription, so this works
    either side of that change.
    """
    start = item.get("current_period_start") or sub.get("current_period_start")
    end = item.get("current_period_end") or sub.get("current_period_end")
    return start, end


def usage(session, meter_id, customer, start, end):
    """Return (rows, total) from the meter's event summaries for one customer.

    Both bounds are floored to the hour: the summaries endpoint expects timestamps
    aligned to the meter's grouping window and returns an error for anything else.
    """
    hour = 3600
    params = {"customer": customer,
              "start_time": (start // hour) * hour,
              "end_time": (end // hour) * hour,
              "limit": 100}
    rows, total = 0, 0
    page = get(session, "/billing/meters/%s/event_summaries" % meter_id, **params)
    for row in page.get("data", []):
        rows += 1
        total += row.get("aggregated_value") or 0
    return rows, total


def zero_billed(session, subscription_id, look_back):
    """Count already-paid invoices for this subscription carrying a zero line.

    Matching a line back to a specific price is version dependent, so this counts
    invoices with any zero-amount line instead. It is a corroborating number, not
    the diagnosis.
    """
    count = 0
    for inv in paginate(session, "/invoices", subscription=subscription_id,
                        status="paid", limit=look_back):
        if any((line.get("amount") or 0) == 0
               for line in (inv.get("lines") or {}).get("data", [])):
            count += 1
        if count >= look_back:
            break
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--invoice-look-back", type=int, default=6,
                    help="paid invoices per subscription to check for zero lines")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    findings = 0
    checked = 0

    for sub in paginate(s, "/subscriptions", status="active",
                        **{"expand[]": "data.items.data.price"}):
        for item in (sub.get("items") or {}).get("data", []):
            price = item.get("price") or {}
            recurring = price.get("recurring") or {}
            if recurring.get("usage_type") != "metered":
                continue
            meter_id = recurring.get("meter")
            if not meter_id:
                log.warning("legacy    %s / %s  metered price %s has no meter; "
                            "match it against GET %s/billing/meters by hand",
                            sub["id"], item["id"], price.get("id"), API)
                continue

            checked += 1
            start, end = period_bounds(sub, item)
            if not start:
                continue
            rows, total = usage(s, meter_id, sub["customer"], start, end or now)
            hours = max(0.0, (now - start) / 3600.0)
            zeros = zero_billed(s, sub["id"], args.invoice_look_back) if not total else 0
            state, detail = verdict(total, rows, hours, zeros)

            line = "%-11s %s / %s  meter %s: %s" % (state, sub["id"], item["id"],
                                                    meter_id, detail)
            if state in ("reporting", "early"):
                log.info(line)
                continue

            findings += 1
            log.warning(line)
            log.warning("  compare the emitter payload with the meter definition:")
            log.warning("  GET %s/billing/meters/%s", API, meter_id)
            log.warning("  then backfill this period before its invoice finalizes; "
                        "usage cannot be added to a finalized invoice")

    log.info("checked %d metered item(s), %d not reporting", checked, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-metered-usage.mjs",
"js": '''/**
 * Report metered subscription items that no usage has been recorded against.
 *
 * Read only. Three GETs, no writes: give this a RESTRICTED key with read access
 * to Subscriptions, Billing Meters and Invoices. The repair is printed, never
 * performed, because this script holds a credential to a live payments account.
 */
const API = 'https://api.stripe.com/v1';

// A period that opened minutes ago has no usage yet on almost any product, and
// reporting that as a fault trains people to ignore the check on the 1st.
export const GRACE_HOURS = 6;

/**
 * Classify one metered subscription item. Pure, so the rules can be tested.
 * Returns [state, detail].
 */
export function verdict(aggregatedValue, summaryRows, hoursIntoPeriod, zeroBilledCycles) {
  if (aggregatedValue) {
    return ['reporting', `${aggregatedValue.toLocaleString('en-US')} unit(s) so far this period`];
  }
  if (hoursIntoPeriod < GRACE_HOURS) {
    return ['early',
      `the period is ${hoursIntoPeriod.toFixed(1)}h old; too early to call zero a fault`];
  }

  let cause;
  let state;
  if (summaryRows) {
    cause = `${summaryRows} summary row(s) and every one aggregates to 0: the events ` +
            'arrive and carry no value. Check value_settings.event_payload_key ' +
            'against the payload.';
    state = 'zero-valued';
  } else {
    cause = 'no meter event summaries at all for this customer: the events never ' +
            'matched. Check event_name first, then customer_mapping.event_payload_key.';
    state = 'silent';
  }

  if (zeroBilledCycles) {
    return ['billed-zero',
      `${zeroBilledCycles} closed invoice(s) already billed a zero line. ${cause}`];
  }
  return [state, cause];
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

async function* paginate(key, path, params = {}) {
  const p = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const row of data) yield row;
    if (data.length === 0 || !page.has_more) return;
    p.starting_after = data[data.length - 1].id;
  }
}

/**
 * Current period for an item. These fields moved from the subscription onto each
 * item, because items on one subscription can now bill on different cycles.
 */
export function periodBounds(sub, item) {
  return [item.current_period_start ?? sub.current_period_start,
          item.current_period_end ?? sub.current_period_end];
}

async function usage(key, meterId, customer, start, end) {
  const hour = 3600;
  const page = await get(key, `/billing/meters/${meterId}/event_summaries`, {
    customer,
    start_time: Math.floor(start / hour) * hour,
    end_time: Math.floor(end / hour) * hour,
    limit: 100,
  });
  let rows = 0;
  let total = 0;
  for (const row of page.data ?? []) {
    rows += 1;
    total += row.aggregated_value ?? 0;
  }
  return { rows, total };
}

async function zeroBilled(key, subscriptionId, lookBack) {
  let count = 0;
  for await (const inv of paginate(key, '/invoices',
    { subscription: subscriptionId, status: 'paid', limit: lookBack })) {
    if ((inv.lines?.data ?? []).some((line) => (line.amount ?? 0) === 0)) count += 1;
    if (count >= lookBack) break;
  }
  return count;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const lookBack = 6;
  const now = Math.floor(Date.now() / 1000);
  let findings = 0;
  let checked = 0;

  for await (const sub of paginate(key, '/subscriptions',
    { status: 'active', 'expand[]': 'data.items.data.price' })) {
    for (const item of sub.items?.data ?? []) {
      const recurring = item.price?.recurring ?? {};
      if (recurring.usage_type !== 'metered') continue;
      const meterId = recurring.meter;
      if (!meterId) {
        console.warn(`legacy      ${sub.id} / ${item.id}  metered price ` +
          `${item.price?.id} has no meter; match it against GET ${API}/billing/meters by hand`);
        continue;
      }

      checked += 1;
      const [start, end] = periodBounds(sub, item);
      if (!start) continue;
      const { rows, total } = await usage(key, meterId, sub.customer, start, end ?? now);
      const hours = Math.max(0, (now - start) / 3600);
      const zeros = total ? 0 : await zeroBilled(key, sub.id, lookBack);
      const [state, detail] = verdict(total, rows, hours, zeros);

      const line = `${state.padEnd(11)} ${sub.id} / ${item.id}  meter ${meterId}: ${detail}`;
      if (state === 'reporting' || state === 'early') { console.log(line); continue; }

      findings += 1;
      console.warn(line);
      console.warn('  compare the emitter payload with the meter definition:');
      console.warn(`  GET ${API}/billing/meters/${meterId}`);
      console.warn('  then backfill this period before its invoice finalizes; ' +
                   'usage cannot be added to a finalized invoice');
    }
  }

  console.log(`checked ${checked} metered item(s), ${findings} not reporting`);
  if (findings) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are about the distinction the invoice cannot show you: nothing arrived versus everything arrived empty. They also pin the grace window, because a check that cries wolf every time a billing period rolls over is a check that gets muted before it ever finds anything.",
"test_py_file": "test_stripe_metered_usage.py",
"test_py": '''from stripe_metered_usage import verdict


def test_usage_present_is_reporting():
    state, detail = verdict(41208, 12, 300.0, 0)
    assert state == "reporting"
    assert "41,208" in detail


def test_a_fresh_period_is_not_a_fault():
    # Zero usage two hours into a period is normal on almost any product.
    assert verdict(0, 0, 2.0, 0)[0] == "early"
    assert verdict(0, 0, 6.0, 0)[0] == "silent"


def test_no_summaries_points_at_the_event_name():
    state, detail = verdict(0, 0, 240.0, 0)
    assert state == "silent"
    assert "event_name" in detail


def test_rows_that_aggregate_to_zero_point_at_the_value_key():
    # The events matched the meter and the customer. Only the value did not.
    state, detail = verdict(0, 9, 240.0, 0)
    assert state == "zero-valued"
    assert "value_settings.event_payload_key" in detail


def test_already_billed_cycles_escalate_and_keep_the_cause():
    state, detail = verdict(0, 9, 240.0, 4)
    assert state == "billed-zero"
    assert "4 closed invoice(s)" in detail
    assert "value_settings.event_payload_key" in detail
''',
"test_js_file": "stripe-metered-usage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, periodBounds } from './stripe-metered-usage.mjs';

test('usage present is reporting', () => {
  const [state, detail] = verdict(41208, 12, 300, 0);
  assert.equal(state, 'reporting');
  assert.ok(detail.includes('41,208'));
});

test('a fresh period is not a fault', () => {
  assert.equal(verdict(0, 0, 2, 0)[0], 'early');
  assert.equal(verdict(0, 0, 6, 0)[0], 'silent');
});

test('no summaries points at the event name', () => {
  const [state, detail] = verdict(0, 0, 240, 0);
  assert.equal(state, 'silent');
  assert.ok(detail.includes('event_name'));
});

test('rows that aggregate to zero point at the value key', () => {
  const [state, detail] = verdict(0, 9, 240, 0);
  assert.equal(state, 'zero-valued');
  assert.ok(detail.includes('value_settings.event_payload_key'));
});

test('already billed cycles escalate and keep the cause', () => {
  const [state, detail] = verdict(0, 9, 240, 4);
  assert.equal(state, 'billed-zero');
  assert.ok(detail.includes('4 closed invoice(s)'));
  assert.ok(detail.includes('value_settings.event_payload_key'));
});

test('the item period wins over the subscription period', () => {
  const bounds = periodBounds({ current_period_start: 1, current_period_end: 2 },
                              { current_period_start: 10, current_period_end: 20 });
  assert.deepEqual(bounds, [10, 20]);
});
''',
"faq": [
 ("Why is the invoice zero when my emitter is clearly sending events?",
  "Because a meter silently ignores anything it does not recognise. Events whose event_name does not match the meter are accepted and dropped, and events whose payload does not carry the customer under customer_mapping.event_payload_key attach to nobody. Neither produces an error, so the emitter's logs look perfect."),
 ("What is the difference between no summary rows and rows that are all zero?",
  "No rows means the event never matched the meter or the customer, so look at event_name and customer_mapping.event_payload_key. Rows at zero means matching worked and the value did not, so look at value_settings.event_payload_key. The invoice looks the same either way, which is why the check reports them as different states."),
 ("Can I backfill usage after the invoice has finalized?",
  "No. Meter events belong to a period, and once that period's invoice is finalized it cannot absorb more usage. Recovering the revenue means a separate charge and a conversation with the customer, so run this check mid-period rather than after the invoice."),
 ("Where do I find the meter for a metered price?",
  "price.recurring.meter on an expanded price. Prices created before Billing Meters have no meter field at all; the script reports those separately, because they have to be matched against GET /v1/billing/meters by hand rather than guessed at."),
 ("Why does the script skip periods that just started?",
  "Because zero usage six hours into a monthly period is normal, and a check that alerts every time a billing cycle rolls over gets muted long before it catches a real mismatch. The grace window is one constant at the top of the file."),
],
"related": [
 ("/stripe/draft-invoices-never-finalized/", "Draft invoices that never finalized"),
 ("/stripe/orphaned-pending-invoice-items/", "Pending invoice items that never reach an invoice"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions piling up unnoticed"),
],
"citations": [CITE_METER_OBJ, CITE_METER_SUMMARIES, CITE_USAGE_BASED, CITE_SUB_OBJ],
},

{
"slug": "orphaned-pending-invoice-items",
"title": "Pending invoice items that never reach an invoice",
"description": "One-off charges and prorations created months ago that no invoice ever swept up. The revenue exists in Stripe and has never been billed.",
"h1": "pending invoice items that never reach an invoice",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe pending invoice items", "invoiceitem invoice null",
             "stripe one off charge never billed", "pending=true invoiceitems",
             "stripe proration never invoiced"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody added a setup fee in March. It is still there, sitting in the account with <code>invoice: null</code>, waiting for the next invoice to sweep it up. That customer cancelled in April, so there will never be a next invoice, and the fee has been quietly not-billed for five months while showing up in nobody's report of anything.",
"short_answer": """<p><code>GET /v1/invoiceitems?pending=true&amp;limit=100</code> lists every invoice item that has not been attached to an invoice yet. Bucket by <code>customer</code>, take the age of the oldest item from <code>date</code>, and sum <code>amount</code> for the exposure.</p>
<p>Then ask the deciding question per customer: <code>GET /v1/subscriptions?customer={cus}&amp;status=active&amp;limit=1</code>. An item on a customer with a live subscription is waiting for the next cycle. An item on a customer with no live subscription is waiting for an invoice that will never be created, and no amount of time fixes it.</p>""",
"problem": """<p>A pending invoice item is not an error state, which is exactly why it accumulates. It is the normal, documented way to attach a one-off charge to somebody's next invoice: create it, do not name an invoice, and Stripe sweeps it up next time it bills that customer. The mechanism only works if there is a next time.</p>
<p>The failure is therefore invisible from both ends. Stripe is behaving correctly and holding the item exactly as instructed. Your application already treated the charge as done, because the create call returned 200 five months ago. Nothing reconciles the two, so the money is neither collected nor written off nor reported: it is simply parked, and the only way anyone finds out is by looking.</p>""",
"why": """<p><strong>Cancellation stops invoice generation, and the items do not go with it.</strong> Cancelling a subscription ends future invoices for that customer. Anything pending at that moment stays pending forever. This is the single largest source of orphans, and it is worst on exactly the accounts where somebody added a manual adjustment during the cancellation conversation.</p>
<p><strong><code>proration_behavior=none</code> is a decision to bill later that nobody records.</strong> Upgrades and downgrades made with <code>create_prorations</code> leave the proration as a pending item, correctly, to be picked up next cycle. Used on a subscription that is about to end, or combined with a plan change that resets the cycle, the proration outlives the thing that was going to bill it.</p>
<p><strong>Nothing ages a pending item.</strong> There is no expiry, no status transition, no event. An item created two years ago and an item created this morning are the same object in the same state, and the API sorts by creation date rather than by anything resembling urgency.</p>
<p><strong>Annual cycles make the benign case look identical.</strong> On a yearly subscription, an item sitting pending for eleven months is completely healthy. On a monthly one, the same age means two cycles have already passed without picking it up, which means it is not going to be picked up at all. Age alone cannot tell them apart, which is why the subscription check matters.</p>""",
"steps": [
 {"h": "List pending items and bucket them by customer",
  "body": """<p><code>GET /v1/invoiceitems?pending=true&amp;limit=100</code>, paginated. Per customer, keep the count, the sum of <code>amount</code>, and the <code>date</code> of the oldest item. The per-customer view matters because the repair is per customer: one invoice sweeps up everything pending for that customer at once.</p>"""},
 {"h": "Ask whether an invoice is still coming",
  "body": """<p><code>GET /v1/subscriptions?customer={cus}&amp;status=active&amp;limit=1</code>. A non-empty result means something will bill this customer again and the item has a route to an invoice. An empty result is the finding: no scheduled invoice exists, so the item is orphaned regardless of how new it is.</p>"""},
 {"h": "Use age only to sort the customers who still have a subscription",
  "body": """<p>Past a monthly cycle plus slack, a pending item on a live subscription has already survived a billing run, which usually means the cycle is annual or the subscription was created after the item. Both are worth a look; neither is the same emergency as an orphan.</p>"""},
 {"h": "Sum the exposure in minor units and report it",
  "body": """<p>The number that gets this scheduled is currency and cents: "EUR 41,900 across 23 customers, oldest item 412 days". Group by <code>currency</code> rather than adding across currencies, which is the mistake that gets the whole report distrusted.</p>"""},
 {"h": "Sweep, or delete, per customer",
  "body": """<p>For items still owed: create an invoice for that customer with <code>collection_method=charge_automatically</code> and <code>auto_advance=true</code>, then finalize it. Everything pending for that customer is pulled onto it. For items no longer owed, delete them: <code>DELETE /v1/invoiceitems/{id}</code> works while the item is still unattached, which is the only period during which it can be cleanly removed.</p>"""},
 {"h": "Stop the next one",
  "body": """<p>Set <code>pending_invoice_item_interval</code> on subscriptions that regularly accrue one-off charges, so Stripe raises an invoice on its own schedule instead of waiting for the next renewal. Where a change should bill immediately, use <code>proration_behavior=always_invoice</code> rather than <code>create_prorations</code>.</p>"""},
],
"verify": """<p>Re-run the script after the sweep. Every remaining pending item should belong to a customer with a live subscription and be younger than a cycle.</p>
<pre><code class="language-bash">python3 stripe_pending_invoice_items.py
# waiting     cus_123  2 item(s), 4,500 minor unit(s), oldest 6d, next invoice due</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Invoices and Subscriptions is enough, and is what you should give it. The classifier is pure and takes the age of the oldest item, whether the customer still has an active subscription, and how many items are stacked up, because age on its own cannot tell an annual cycle apart from an item that has been abandoned.",
"py_file": "stripe_pending_invoice_items.py",
"py": '''"""Report Stripe invoice items left pending with no invoice coming to collect them.

Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
Invoices and Subscriptions. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_pending_invoice_items")

API = "https://api.stripe.com/v1"

FRESH_DAYS = 1     # created today; a manual invoice may be seconds behind it
SWEEP_DAYS = 35    # a monthly cycle plus slack: one invoice should have run
STALE_DAYS = 60    # two cycles missed, or an annual plan worth confirming


def verdict(age_days, has_active_subscription, item_count):
    """Classify one customer's pending invoice items. Pure, so it can be tested.

    `age_days` is the age of that customer's oldest pending item, and
    `has_active_subscription` whether any invoice is still scheduled for them at
    all. Returns (state, detail).
    """
    stack = "%d pending item(s), oldest %.0fd" % (item_count, age_days)
    if not has_active_subscription:
        if age_days < FRESH_DAYS:
            return ("fresh",
                    "%s, no active subscription. Probably an invoice being built "
                    "right now; check again tomorrow." % stack)
        return ("orphaned",
                "%s, and no active subscription to raise an invoice. Nothing will "
                "ever sweep these up." % stack)
    if age_days < SWEEP_DAYS:
        return ("waiting", "%s, next invoice still due" % stack)
    if age_days < STALE_DAYS:
        return ("aging",
                "%s, past a monthly cycle. Fine on an annual plan, a miss on a "
                "monthly one." % stack)
    return ("stalled",
            "%s, past two monthly cycles with a live subscription. Confirm the "
            "billing interval before assuming this is benign." % stack)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def paginate(session, path, **params):
    params = dict(params, limit=params.get("limit", 100))
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for row in data:
            yield row
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def bucket_by_customer(items):
    """Group pending items per customer, keeping the oldest date and the totals.

    Amounts are kept per currency. Summing across currencies produces a number
    that is wrong in a way nobody can see, which is how a report gets distrusted.
    """
    buckets = {}
    for it in items:
        cus = it.get("customer")
        if not cus:
            continue
        b = buckets.setdefault(cus, {"count": 0, "oldest": None, "amounts": {}})
        b["count"] += 1
        date = it.get("date") or it.get("created")
        if date is not None and (b["oldest"] is None or date < b["oldest"]):
            b["oldest"] = date
        cur = (it.get("currency") or "???").upper()
        b["amounts"][cur] = b["amounts"].get(cur, 0) + (it.get("amount") or 0)
    return buckets


def has_active_subscription(session, customer):
    page = get(session, "/subscriptions", customer=customer, status="active", limit=1)
    return bool(page.get("data"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-items", type=int, default=5000,
                    help="stop paginating after this many pending invoice items")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    items = []
    for it in paginate(s, "/invoiceitems", pending="true"):
        items.append(it)
        if len(items) >= args.max_items:
            break

    buckets = bucket_by_customer(items)
    now = time.time()
    findings = 0
    exposure = {}

    for cus, b in sorted(buckets.items(), key=lambda kv: kv[1]["oldest"] or 0):
        age = 0.0 if b["oldest"] is None else (now - b["oldest"]) / 86400.0
        live = has_active_subscription(s, cus)
        state, detail = verdict(age, live, b["count"])
        money = ", ".join("%s %d" % (c, v) for c, v in sorted(b["amounts"].items()))

        line = "%-11s %s  %s  [%s minor unit(s)]" % (state, cus, detail, money)
        if state in ("waiting", "fresh"):
            log.info(line)
            continue

        findings += 1
        for c, v in b["amounts"].items():
            exposure[c] = exposure.get(c, 0) + v
        log.warning(line)
        if state == "orphaned":
            log.warning("  raise one invoice for this customer to sweep every "
                        "pending item onto it, then finalize it; or delete the "
                        "items that are no longer owed while they are unattached")
        else:
            log.warning("  confirm the billing interval: GET %s/subscriptions"
                        "?customer=%s&status=active", API, cus)

    log.info("%d customer(s) with pending items, %d needing a decision", len(buckets),
             findings)
    for c, v in sorted(exposure.items()):
        log.info("  unbilled exposure: %s %d minor unit(s)", c, v)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-pending-invoice-items.mjs",
"js": '''/**
 * Report Stripe invoice items left pending with no invoice coming to collect them.
 *
 * Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
 * Invoices and Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const FRESH_DAYS = 1;  // created today; a manual invoice may be seconds behind
export const SWEEP_DAYS = 35; // a monthly cycle plus slack: one invoice should have run
export const STALE_DAYS = 60; // two cycles missed, or an annual plan worth confirming

/**
 * Classify one customer's pending invoice items. Pure, so it can be tested.
 * Returns [state, detail].
 */
export function verdict(ageDays, hasActiveSubscription, itemCount) {
  const stack = `${itemCount} pending item(s), oldest ${Math.round(ageDays)}d`;
  if (!hasActiveSubscription) {
    if (ageDays < FRESH_DAYS) {
      return ['fresh',
        `${stack}, no active subscription. Probably an invoice being built right ` +
        'now; check again tomorrow.'];
    }
    return ['orphaned',
      `${stack}, and no active subscription to raise an invoice. Nothing will ever ` +
      'sweep these up.'];
  }
  if (ageDays < SWEEP_DAYS) return ['waiting', `${stack}, next invoice still due`];
  if (ageDays < STALE_DAYS) {
    return ['aging',
      `${stack}, past a monthly cycle. Fine on an annual plan, a miss on a monthly one.`];
  }
  return ['stalled',
    `${stack}, past two monthly cycles with a live subscription. Confirm the ` +
    'billing interval before assuming this is benign.'];
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

async function* paginate(key, path, params = {}) {
  const p = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const row of data) yield row;
    if (data.length === 0 || !page.has_more) return;
    p.starting_after = data[data.length - 1].id;
  }
}

/**
 * Group pending items per customer, keeping the oldest date and the totals.
 * Amounts stay per currency: summing across currencies is wrong invisibly.
 */
export function bucketByCustomer(items) {
  const buckets = new Map();
  for (const it of items) {
    if (!it.customer) continue;
    if (!buckets.has(it.customer)) {
      buckets.set(it.customer, { count: 0, oldest: null, amounts: {} });
    }
    const b = buckets.get(it.customer);
    b.count += 1;
    const date = it.date ?? it.created;
    if (date !== undefined && date !== null && (b.oldest === null || date < b.oldest)) {
      b.oldest = date;
    }
    const cur = (it.currency ?? '???').toUpperCase();
    b.amounts[cur] = (b.amounts[cur] ?? 0) + (it.amount ?? 0);
  }
  return buckets;
}

async function hasActiveSubscription(key, customer) {
  const page = await get(key, '/subscriptions',
    { customer, status: 'active', limit: 1 });
  return (page.data ?? []).length > 0;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const maxItems = 5000;
  const items = [];
  for await (const it of paginate(key, '/invoiceitems', { pending: 'true' })) {
    items.push(it);
    if (items.length >= maxItems) break;
  }

  const buckets = bucketByCustomer(items);
  const now = Date.now() / 1000;
  let findings = 0;
  const exposure = {};

  const ordered = [...buckets.entries()].sort((a, b) => (a[1].oldest ?? 0) - (b[1].oldest ?? 0));
  for (const [cus, b] of ordered) {
    const age = b.oldest === null ? 0 : (now - b.oldest) / 86400;
    const live = await hasActiveSubscription(key, cus);
    const [state, detail] = verdict(age, live, b.count);
    const money = Object.entries(b.amounts).sort()
      .map(([c, v]) => `${c} ${v}`).join(', ');

    const line = `${state.padEnd(11)} ${cus}  ${detail}  [${money} minor unit(s)]`;
    if (state === 'waiting' || state === 'fresh') { console.log(line); continue; }

    findings += 1;
    for (const [c, v] of Object.entries(b.amounts)) exposure[c] = (exposure[c] ?? 0) + v;
    console.warn(line);
    if (state === 'orphaned') {
      console.warn('  raise one invoice for this customer to sweep every pending ' +
        'item onto it, then finalize it; or delete the items that are no longer ' +
        'owed while they are unattached');
    } else {
      console.warn(`  confirm the billing interval: GET ${API}/subscriptions` +
        `?customer=${cus}&status=active`);
    }
  }

  console.log(`${buckets.size} customer(s) with pending items, ${findings} needing a decision`);
  for (const [c, v] of Object.entries(exposure).sort()) {
    console.log(`  unbilled exposure: ${c} ${v} minor unit(s)`);
  }
  if (findings) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests hold the one rule that matters: no active subscription means orphaned at any age, because there is no future invoice for the item to wait for. The rest pin the two day boundaries and the currency bucketing, since an exposure figure that silently adds euros to yen is worse than no figure at all.",
"test_py_file": "test_stripe_pending_invoice_items.py",
"test_py": '''from stripe_pending_invoice_items import bucket_by_customer, verdict


def test_a_live_subscription_means_the_item_is_merely_waiting():
    state, detail = verdict(6.0, True, 2)
    assert state == "waiting"
    assert "2 pending item(s)" in detail


def test_no_subscription_is_orphaned_at_any_age():
    # This is the whole point: age is irrelevant once nothing will ever bill.
    assert verdict(3.0, False, 1)[0] == "orphaned"
    assert verdict(400.0, False, 1)[0] == "orphaned"


def test_an_item_created_today_gets_the_benefit_of_the_doubt():
    assert verdict(0.5, False, 1)[0] == "fresh"
    assert verdict(1.0, False, 1)[0] == "orphaned"


def test_the_cycle_boundaries_separate_aging_from_stalled():
    assert verdict(34.9, True, 1)[0] == "waiting"
    assert verdict(35.0, True, 1)[0] == "aging"
    assert verdict(59.9, True, 1)[0] == "aging"
    assert verdict(60.0, True, 1)[0] == "stalled"


def test_bucketing_keeps_currencies_apart_and_the_oldest_date():
    items = [
        {"customer": "cus_1", "date": 500, "amount": 1000, "currency": "eur"},
        {"customer": "cus_1", "date": 100, "amount": 250, "currency": "eur"},
        {"customer": "cus_1", "date": 900, "amount": 700, "currency": "usd"},
        {"customer": None, "date": 100, "amount": 999, "currency": "eur"},
    ]
    b = bucket_by_customer(items)["cus_1"]
    assert b["count"] == 3
    assert b["oldest"] == 100
    assert b["amounts"] == {"EUR": 1250, "USD": 700}
''',
"test_js_file": "stripe-pending-invoice-items.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, bucketByCustomer } from './stripe-pending-invoice-items.mjs';

test('a live subscription means the item is merely waiting', () => {
  const [state, detail] = verdict(6, true, 2);
  assert.equal(state, 'waiting');
  assert.ok(detail.includes('2 pending item(s)'));
});

test('no subscription is orphaned at any age', () => {
  assert.equal(verdict(3, false, 1)[0], 'orphaned');
  assert.equal(verdict(400, false, 1)[0], 'orphaned');
});

test('an item created today gets the benefit of the doubt', () => {
  assert.equal(verdict(0.5, false, 1)[0], 'fresh');
  assert.equal(verdict(1, false, 1)[0], 'orphaned');
});

test('the cycle boundaries separate aging from stalled', () => {
  assert.equal(verdict(34.9, true, 1)[0], 'waiting');
  assert.equal(verdict(35, true, 1)[0], 'aging');
  assert.equal(verdict(59.9, true, 1)[0], 'aging');
  assert.equal(verdict(60, true, 1)[0], 'stalled');
});

test('bucketing keeps currencies apart and the oldest date', () => {
  const items = [
    { customer: 'cus_1', date: 500, amount: 1000, currency: 'eur' },
    { customer: 'cus_1', date: 100, amount: 250, currency: 'eur' },
    { customer: 'cus_1', date: 900, amount: 700, currency: 'usd' },
    { customer: null, date: 100, amount: 999, currency: 'eur' },
  ];
  const b = bucketByCustomer(items).get('cus_1');
  assert.equal(b.count, 3);
  assert.equal(b.oldest, 100);
  assert.deepEqual(b.amounts, { EUR: 1250, USD: 700 });
});
''',
"faq": [
 ("What exactly is a pending invoice item?",
  "An invoice item whose invoice field is null. It has been created and it belongs to a customer, but no invoice has claimed it yet. Stripe sweeps every pending item for a customer onto the next invoice it raises for them, which is a useful mechanism right up until no next invoice exists."),
 ("Why does a cancelled subscription orphan the items rather than billing them?",
  "Cancelling ends future invoice generation for that customer. Stripe does not raise a final invoice to clear pending items, and the items carry no expiry, so they stay in the same state indefinitely. Nothing is broken from Stripe's side, which is why nothing reports it."),
 ("Is an old pending item always a problem?",
  "No, and that is why the script checks for an active subscription rather than trusting age. On an annual plan an item can sit pending for eleven months and be collected exactly as intended. Age sorts the list; the presence of a live subscription decides the verdict."),
 ("Can I still delete a pending invoice item?",
  "Yes, while it is unattached. DELETE /v1/invoiceitems/{id} works on items with invoice: null. Once an item is on a finalized invoice it is part of a financial document and has to be handled with a credit note instead, so unattached is the cheap window."),
 ("How do I stop this happening again?",
  "Set pending_invoice_item_interval on subscriptions that regularly accrue one-off charges, so Stripe raises its own invoice on a schedule rather than waiting for a renewal. For changes that should bill straight away use proration_behavior=always_invoice instead of create_prorations."),
],
"related": [
 ("/stripe/draft-invoices-never-finalized/", "Draft invoices that never finalized"),
 ("/stripe/open-invoices-past-due-date/", "open invoices past their due date"),
 ("/stripe/metered-items-with-no-usage-reported/", "Metered items with no usage reported"),
],
"citations": [CITE_INVOICEITEM_LIST, CITE_INVOICEITEM_OBJ, CITE_PRORATIONS, CITE_SUB_OBJ],
},

{
"slug": "no-tax-registrations-while-selling-abroad",
"title": "No tax registrations while invoicing many countries",
"description": "Stripe Tax is on, calculation succeeds, every invoice shows zero tax. Without a registration in the buyer's country there is nothing to calculate.",
"h1": "no tax registrations while invoicing many countries",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe tax registrations", "stripe tax zero not_collecting",
             "stripe tax nexus threshold", "taxability_reason not_collecting",
             "stripe tax no vat charged"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Stripe Tax is enabled. <code>automatic_tax.status</code> reads <code>complete</code> on every invoice. The tax line is zero on all of them, including the ones going to Germany and the UK, and the reason given is <code>not_collecting</code>. Nothing is failing. Stripe calculated the tax correctly, and the correct answer given the registrations on file is nothing.",
"short_answer": """<p>Compare two lists. <code>GET /v1/tax/registrations?status=active&amp;limit=100</code> gives the countries where Stripe is allowed to collect for you. <code>GET /v1/invoices?status=paid&amp;created[gte]=&lt;a year ago&gt;</code> gives, through <code>customer_address.country</code>, the countries you have actually been billing.</p>
<p>Every country in the second list and not the first is untaxed revenue accruing towards a threshold you are not tracking. Also check <code>status=expired</code>: a registration with <code>expires_at</code> in the past stops collection on that date and reports the same reassuring <code>complete</code> afterwards.</p>""",
"problem": """<p>This is the tax failure that survives review, because every signal an engineer would look at is green. Stripe Tax is switched on. The API says the calculation completed. There is no error code, no stuck invoice, no unusual status. The one field that says what happened, <code>taxability_reason</code> on the line, says <code>not_collecting</code>, and that reads as a normal condition rather than a warning.</p>
<p>The exposure builds in the wrong direction too. The problem is not that a customer was undercharged; it is that you owe the tax anyway once the threshold is crossed, out of margin you already recognised as revenue. A year of German sales with no VAT is not a year of missing line items, it is a liability plus interest that arrives as a surprise, and the invoices cannot be reissued retroactively without going back to every customer.</p>""",
"why": """<p><strong>A registration is what authorises collection, not the Tax toggle.</strong> Enabling Stripe Tax turns on calculation. Calculation consults your registrations, finds none for the buyer's jurisdiction, and returns zero. That zero is a successful calculation, which is why the status field cannot help you and the amount has to be read instead.</p>
<p><strong>Thresholds accrue silently and in the background.</strong> Economic nexus rules mean the obligation starts when you cross a revenue or transaction level in a jurisdiction, whether or not anybody registered. Stripe's monitoring emails only fire above a revenue floor and only in live mode, so a business under that floor gets no warning at all while it approaches one.</p>
<p><strong>Registrations expire, and expiry is not an error.</strong> A registration can carry an <code>expires_at</code>. Past that date it stops authorising collection, and every invoice afterwards behaves exactly like one for a country you never registered in. Nothing changes in the API responses except the amount.</p>
<p><strong>The billed-country list lives in the invoices, not in your head.</strong> Teams reliably know their top three markets and reliably miss the long tail: two customers in Norway, one in Australia, a handful in Canada. Those are the rows that show up in a diligence review, and the only honest way to enumerate them is to read the paid invoices.</p>""",
"steps": [
 {"h": "Collect the countries you are registered in",
  "body": """<p><code>GET /v1/tax/registrations?status=active&amp;limit=100</code> and take <code>country</code> from each. In the US, registration is per state: read <code>country_options.us.state</code> as well, because a single US registration authorises collection in one state and not in the other forty-nine.</p>"""},
 {"h": "Collect the countries you have actually billed",
  "body": """<p><code>GET /v1/invoices?status=paid&amp;limit=100&amp;created[gte]=</code> a year back, paginated, tallying distinct <code>customer_address.country</code> along with the count and the total per country. Paid invoices, not all invoices: drafts and voids describe intentions rather than revenue.</p>"""},
 {"h": "Subtract, and rank what is left by revenue",
  "body": """<p>Every billed country absent from the registration set is a finding. Rank by revenue rather than by invoice count, because the jurisdiction that matters first is the one closest to its threshold, and thresholds are almost always monetary.</p>"""},
 {"h": "Check for expired registrations separately",
  "body": """<p><code>GET /v1/tax/registrations?status=expired</code>. A country you used to be registered in is a different and more urgent finding than one you never registered in: it means collection stopped on a specific date, which is the date you can hand to an accountant.</p>"""},
 {"h": "Register, then record the registration in Stripe",
  "body": """<p>The registration itself happens with the tax authority. Recording it in Stripe with <code>POST /v1/tax/registrations</code> and a country plus the country options for that regime is what makes calculation start returning a number. Both steps are required and only the second one is visible from the API, which is why this check only ever sees the second.</p>"""},
 {"h": "Turn threshold monitoring on rather than reading this monthly",
  "body": """<p>Stripe tracks nexus thresholds in the Dashboard under Tax, and can email you as you approach them. Set the notification preferences once. This script tells you where you stand today; the monitoring tells you before the next one arrives.</p>"""},
],
"verify": """<p>Re-run the script after the registrations are recorded. Every country you bill should be either registered or explicitly below its threshold and known about.</p>
<pre><code class="language-bash">python3 stripe_tax_registrations.py
# covered     DE  registered, 214 paid invoice(s) in the last year</code></pre>""",
"code_intro": "Three GETs and no writes &mdash; a restricted key with read access to Tax and Invoices is enough, and is what you should give it. The classifier is pure and takes one country plus the registered and expired sets and the revenue billed there, because an expired registration and one that never existed produce identical invoices and need different phone calls.",
"py_file": "stripe_tax_registrations.py",
"py": '''"""Report countries you invoice into with no active Stripe Tax registration.

Read only. Three GETs, no writes: give this a RESTRICTED key with read access to
Tax and Invoices. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_tax_registrations")

API = "https://api.stripe.com/v1"

# Roughly where Stripe's own threshold monitoring starts emailing, in minor units
# of the invoice currency. Currencies are not converted: this is a triage rank,
# not an accounting figure, and it is deliberately a constant you can move.
WATCH_MINOR = 1000000


def verdict(country, registered, expired, revenue_minor, invoice_count):
    """Classify one billed country. Pure, so the rules can be tested offline.

    `registered` and `expired` are sets of country codes from
    /v1/tax/registrations. Returns (state, detail).
    """
    where = "%d paid invoice(s), %d minor unit(s) billed" % (invoice_count,
                                                             revenue_minor)
    if country in registered:
        return ("covered", "registered, %s" % where)
    if country in expired:
        return ("lapsed",
                "a registration existed and has expired, so collection stopped on "
                "a known date. %s since." % where)
    if revenue_minor >= WATCH_MINOR:
        return ("exposed",
                "no registration and %s. This is the size at which a threshold is "
                "the likely explanation for the letter." % where)
    return ("unregistered", "no registration, %s" % where)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def paginate(session, path, **params):
    params = dict(params, limit=params.get("limit", 100))
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for row in data:
            yield row
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def registration_countries(session, status):
    """Country codes with a registration in the given status.

    US registrations are per state, so a US row is recorded as US-CA rather than
    US: one state registration does not authorise collection in the other 49.
    """
    out = set()
    for reg in paginate(session, "/tax/registrations", status=status):
        country = (reg.get("country") or "").upper()
        if not country:
            continue
        state = ((reg.get("country_options") or {}).get("us") or {}).get("state")
        out.add("%s-%s" % (country, state.upper()) if country == "US" and state
                else country)
    return out


def billed_countries(session, since):
    """Tally paid invoices by the customer's country. Returns {code: (count, minor)}."""
    tally = {}
    for inv in paginate(session, "/invoices", status="paid",
                        **{"created[gte]": since}):
        addr = inv.get("customer_address") or {}
        country = (addr.get("country") or "").upper()
        if not country:
            continue
        key = country
        if country == "US" and addr.get("state"):
            key = "US-%s" % addr["state"].upper()
        count, amount = tally.get(key, (0, 0))
        tally[key] = (count + 1, amount + (inv.get("amount_paid") or 0))
    return tally


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=365,
                    help="how far back to read paid invoices")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    registered = registration_countries(s, "active")
    expired = registration_countries(s, "expired")
    since = int(time.time()) - args.days * 86400
    tally = billed_countries(s, since)

    if not tally:
        log.info("no paid invoices with a customer country in the last %d days",
                 args.days)
        return 0

    findings = 0
    for country, (count, amount) in sorted(tally.items(), key=lambda kv: -kv[1][1]):
        state, detail = verdict(country, registered, expired, amount, count)
        line = "%-12s %-6s %s" % (state, country, detail)
        if state == "covered":
            log.info(line)
            continue
        findings += 1
        log.warning(line)

    if findings:
        log.warning("register with each authority, then record it so calculation "
                    "starts returning a number rather than a correct zero")
        log.warning("  GET %s/tax/registrations?status=active   "
                    "(the list this check compares against)", API)
        log.warning("  Dashboard: Tax > Locations shows threshold progress per "
                    "jurisdiction, which this API cannot")
    log.info("%d billed country/state(s), %d without an active registration",
             len(tally), findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-tax-registrations.mjs",
"js": '''/**
 * Report countries you invoice into with no active Stripe Tax registration.
 *
 * Read only. Three GETs, no writes: give this a RESTRICTED key with read access
 * to Tax and Invoices. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Roughly where Stripe's own threshold monitoring starts emailing, in minor units
// of the invoice currency. Currencies are not converted: this is a triage rank,
// not an accounting figure.
export const WATCH_MINOR = 1000000;

/**
 * Classify one billed country. Pure, so the rules can be tested offline.
 * `registered` and `expired` are Sets of country codes. Returns [state, detail].
 */
export function verdict(country, registered, expired, revenueMinor, invoiceCount) {
  const where = `${invoiceCount} paid invoice(s), ${revenueMinor} minor unit(s) billed`;
  if (registered.has(country)) return ['covered', `registered, ${where}`];
  if (expired.has(country)) {
    return ['lapsed',
      'a registration existed and has expired, so collection stopped on a known ' +
      `date. ${where} since.`];
  }
  if (revenueMinor >= WATCH_MINOR) {
    return ['exposed',
      `no registration and ${where}. This is the size at which a threshold is the ` +
      'likely explanation for the letter.'];
  }
  return ['unregistered', `no registration, ${where}`];
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

async function* paginate(key, path, params = {}) {
  const p = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const row of data) yield row;
    if (data.length === 0 || !page.has_more) return;
    p.starting_after = data[data.length - 1].id;
  }
}

/**
 * Country codes with a registration in the given status. US registrations are per
 * state, so a US row is recorded as US-CA: one state does not cover the other 49.
 */
export async function registrationCountries(key, status) {
  const out = new Set();
  for await (const reg of paginate(key, '/tax/registrations', { status })) {
    const country = (reg.country ?? '').toUpperCase();
    if (!country) continue;
    const state = reg.country_options?.us?.state;
    out.add(country === 'US' && state ? `US-${state.toUpperCase()}` : country);
  }
  return out;
}

/** Tally paid invoices by the customer's country. Returns a Map of code to totals. */
export async function billedCountries(key, since) {
  const tally = new Map();
  for await (const inv of paginate(key, '/invoices',
    { status: 'paid', 'created[gte]': since })) {
    const addr = inv.customer_address ?? {};
    const country = (addr.country ?? '').toUpperCase();
    if (!country) continue;
    const k = country === 'US' && addr.state
      ? `US-${addr.state.toUpperCase()}` : country;
    const prev = tally.get(k) ?? { count: 0, amount: 0 };
    tally.set(k, { count: prev.count + 1, amount: prev.amount + (inv.amount_paid ?? 0) });
  }
  return tally;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = 365;
  const registered = await registrationCountries(key, 'active');
  const expired = await registrationCountries(key, 'expired');
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  const tally = await billedCountries(key, since);

  if (tally.size === 0) {
    console.log(`no paid invoices with a customer country in the last ${days} days`);
    return;
  }

  let findings = 0;
  const ordered = [...tally.entries()].sort((a, b) => b[1].amount - a[1].amount);
  for (const [country, { count, amount }] of ordered) {
    const [state, detail] = verdict(country, registered, expired, amount, count);
    const line = `${state.padEnd(12)} ${country.padEnd(6)} ${detail}`;
    if (state === 'covered') { console.log(line); continue; }
    findings += 1;
    console.warn(line);
  }

  if (findings) {
    console.warn('register with each authority, then record it so calculation ' +
      'starts returning a number rather than a correct zero');
    console.warn(`  GET ${API}/tax/registrations?status=active   ` +
      '(the list this check compares against)');
    console.warn('  Dashboard: Tax > Locations shows threshold progress per ' +
      'jurisdiction, which this API cannot');
  }
  console.log(`${tally.size} billed country/state(s), ${findings} without an active registration`);
  if (findings) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests fix the three distinctions this check exists to make: registered against not, never-registered against expired, and small against large enough that a threshold is the likely explanation. The US case gets its own test, because a registration in one state covering the whole country is the assumption that costs the most.",
"test_py_file": "test_stripe_tax_registrations.py",
"test_py": '''from stripe_tax_registrations import verdict


REGISTERED = {"DE", "GB", "US-CA"}
EXPIRED = {"FR"}


def test_a_registered_country_is_covered():
    state, detail = verdict("DE", REGISTERED, EXPIRED, 4200000, 214)
    assert state == "covered"
    assert "214 paid invoice(s)" in detail


def test_an_expired_registration_is_its_own_finding():
    # Identical invoices to the never-registered case, different phone call.
    state, detail = verdict("FR", REGISTERED, EXPIRED, 50000, 9)
    assert state == "lapsed"
    assert "expired" in detail


def test_small_revenue_in_a_new_country_is_still_reported():
    assert verdict("NO", REGISTERED, EXPIRED, 12000, 3)[0] == "unregistered"


def test_large_revenue_escalates_to_exposed():
    assert verdict("AU", REGISTERED, EXPIRED, 999999, 40)[0] == "unregistered"
    assert verdict("AU", REGISTERED, EXPIRED, 1000000, 40)[0] == "exposed"


def test_one_us_state_does_not_cover_another():
    assert verdict("US-CA", REGISTERED, EXPIRED, 800000, 60)[0] == "covered"
    assert verdict("US-NY", REGISTERED, EXPIRED, 800000, 60)[0] == "unregistered"
''',
"test_js_file": "stripe-tax-registrations.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-tax-registrations.mjs';

const REGISTERED = new Set(['DE', 'GB', 'US-CA']);
const EXPIRED = new Set(['FR']);

test('a registered country is covered', () => {
  const [state, detail] = verdict('DE', REGISTERED, EXPIRED, 4200000, 214);
  assert.equal(state, 'covered');
  assert.ok(detail.includes('214 paid invoice(s)'));
});

test('an expired registration is its own finding', () => {
  const [state, detail] = verdict('FR', REGISTERED, EXPIRED, 50000, 9);
  assert.equal(state, 'lapsed');
  assert.ok(detail.includes('expired'));
});

test('small revenue in a new country is still reported', () => {
  assert.equal(verdict('NO', REGISTERED, EXPIRED, 12000, 3)[0], 'unregistered');
});

test('large revenue escalates to exposed', () => {
  assert.equal(verdict('AU', REGISTERED, EXPIRED, 999999, 40)[0], 'unregistered');
  assert.equal(verdict('AU', REGISTERED, EXPIRED, 1000000, 40)[0], 'exposed');
});

test('one US state does not cover another', () => {
  assert.equal(verdict('US-CA', REGISTERED, EXPIRED, 800000, 60)[0], 'covered');
  assert.equal(verdict('US-NY', REGISTERED, EXPIRED, 800000, 60)[0], 'unregistered');
});
''',
"faq": [
 ("Stripe Tax is enabled and the status says complete. Why is the tax zero?",
  "Because calculation consults your registrations and you have none in that jurisdiction. Zero is the correct answer to the question Stripe was asked, so the status is complete and no error appears. The line's taxability_reason says not_collecting, which is the only field that distinguishes this from a genuinely tax-free sale."),
 ("Does enabling Stripe Tax create registrations for me?",
  "No. Registration happens with the tax authority in each jurisdiction. Recording it in Stripe afterwards is what lets calculation return a number. Only the second half is visible through the API, which is why this check can tell you what Stripe knows and not whether you are actually registered somewhere."),
 ("Why compare against paid invoices rather than customers?",
  "Because a customer record with an address may never have bought anything, and a country with revenue is the one that accrues towards a threshold. Paid invoices, read through customer_address.country, are the closest thing the API has to a list of the jurisdictions you actually sell into."),
 ("Why does the script treat US states separately?",
  "Because US registration is per state and country_options.us.state names which one. Treating a California registration as covering the country is the mistake this check is most useful for catching, so a US row is tracked as US-CA rather than US."),
 ("What about registrations that have expired?",
  "They are reported as their own state. An expired registration means collection stopped on a specific date and everything invoiced since then behaves like an unregistered country. Knowing the date is what makes the cleanup finite, so it is worth separating from countries you never registered in."),
],
"related": [
 ("/stripe/automatic-tax-disabled-everywhere/", "automatic_tax disabled while selling abroad"),
 ("/stripe/prices-with-tax-behavior-unspecified/", "Prices left at tax_behavior unspecified"),
 ("/stripe/draft-invoices-never-finalized/", "Draft invoices that never finalized"),
],
"citations": [CITE_REGISTRATIONS, CITE_ZERO_TAX, CITE_TAX_MONITORING, CITE_INVOICE_OBJ],
},

{
"slug": "prices-with-tax-behavior-unspecified",
"title": "Prices left at tax_behavior unspecified break tax math",
"description": "Stripe cannot tell whether the amount already includes tax, so the tax is wrong or the line cannot be added to an automatic tax invoice at all.",
"h1": "prices left at tax_behavior unspecified break tax math",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe tax_behavior unspecified", "stripe price inclusive exclusive",
             "automatic tax invoice price error", "stripe tax_code missing",
             "stripe price tax behavior immutable"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody turns on automatic tax and the first invoice refuses to take a line item. The price is fine, the product is fine, the amount is right, and Stripe will not compute tax on it, because <code>tax_behavior</code> is <code>unspecified</code> and it genuinely does not know whether the 20 EUR on that price already has VAT in it or not.",
"short_answer": """<p><code>GET /v1/prices?active=true&amp;limit=100</code> and flag every price whose <code>tax_behavior</code> is <code>unspecified</code>. That is the default, so on an account that never set one it will be all of them.</p>
<p>Then find out which of those are live: <code>GET /v1/subscriptions?price={price}&amp;status=active&amp;limit=100</code>. A dormant price is a five-minute fix; a price with four hundred subscriptions on it is a migration, because <code>tax_behavior</code> can be set once while it is <code>unspecified</code> and never changed after that.</p>""",
"problem": """<p><code>unspecified</code> is not a placeholder for "no tax". It is Stripe recording that nobody has said which side of the amount the tax sits on, and that is not a question the tax engine can guess its way around. Twenty euros inclusive of 20% VAT and twenty euros plus 20% VAT are different prices, different revenue and different invoices, and the difference is exactly the amount somebody is arguing about later.</p>
<p>The consequence lands in two different places at two different times. Adding an item with <code>tax_behavior=unspecified</code> to an invoice with automatic tax fails outright, which at least happens loudly. Everything else is quiet: charges that compute tax against the wrong base, or against no base, on prices that have been billing happily for two years. The loud failure is the lucky one.</p>""",
"why": """<p><strong>The default is the unsafe value, and nothing warns about it.</strong> A price created without <code>tax_behavior</code> gets <code>unspecified</code>. Nothing in the create call fails, nothing in the Dashboard flags it, and the price bills correctly for as long as nobody is calculating tax on it. The field only becomes load-bearing later, when automatic tax is switched on by somebody else.</p>
<p><strong>The setting is effectively one-way.</strong> <code>tax_behavior</code> can be set while it is still <code>unspecified</code>, and once it is <code>inclusive</code> or <code>exclusive</code> it cannot be changed again. That is a deliberate protection &mdash; flipping it silently reprices everything on it &mdash; but it also means the fix has to be right first time, and that a price you would rather not touch has to be replaced instead of edited.</p>
<p><strong>Live prices cannot be repriced under a subscription.</strong> Replacing the price on an active subscription is a real migration with proration decisions attached. So the number of active subscriptions is not a detail: it is the difference between a config change and a change-managed piece of work, and it is why this check counts them.</p>
<p><strong>A missing product <code>tax_code</code> hides behind the same symptom.</strong> Tax behavior says how to apply tax; the product's tax code says which rate applies. A price with correct behavior on a product with no tax code falls back to your account default, which is right for some catalogues and quietly wrong for anything mixing digital services, physical goods or training.</p>""",
"steps": [
 {"h": "List active prices and read tax_behavior",
  "body": """<p><code>GET /v1/prices?active=true&amp;limit=100</code>, paginated. Archived prices do not matter unless a subscription still points at one, which is rare and worth checking separately if it does happen.</p>"""},
 {"h": "Count active subscriptions per flagged price",
  "body": """<p><code>GET /v1/subscriptions?price={price}&amp;status=active&amp;limit=100</code>. This is the number that decides the repair path, so do it per price rather than sampling. Zero means the price can be corrected in place; anything else means a migration.</p>"""},
 {"h": "Find out whether automatic tax is actually in use",
  "body": """<p><code>GET /v1/subscriptions?automatic_tax[enabled]=true&amp;limit=1</code>. If anything comes back, unspecified prices are not a latent risk but an active one: those line items cannot be added to an automatic tax invoice at all.</p>"""},
 {"h": "Check the products for a tax code while you are there",
  "body": """<p><code>GET /v1/products?active=true&amp;limit=100</code> and look for <code>tax_code</code> at <code>null</code>. It is the same conversation with the same person and it is the other half of getting the rate right, so it belongs in the same report.</p>"""},
 {"h": "Set the default before creating anything new",
  "body": """<p>Stripe's tax settings carry a default tax behavior that new prices inherit. Setting it is what stops the list growing again while you work through the existing one, and it is a Dashboard setting rather than a deploy.</p>"""},
 {"h": "Fix dormant prices in place, migrate the live ones",
  "body": """<p>A price with no active subscriptions can have <code>tax_behavior</code> set directly, once. For a live price, create a replacement with the same product, amount, currency and interval plus an explicit <code>tax_behavior</code>, move subscriptions onto it with an explicit proration decision, then archive the old one so nothing new lands on it.</p>"""},
],
"verify": """<p>Re-run the script. Every active price should carry an explicit behavior, and every product a tax code.</p>
<pre><code class="language-bash">python3 stripe_price_tax_behavior.py
# ready       price_123  exclusive, product tax code txcd_10000000</code></pre>""",
"code_intro": "Four GETs and no writes &mdash; a restricted key with read access to Products, Prices and Subscriptions is enough, and is what you should give it. The classifier is pure and takes the behavior, the number of active subscriptions, the product's tax code and whether automatic tax is in use anywhere, because those four together decide whether this is a Dashboard change this afternoon or a priced migration.",
"py_file": "stripe_price_tax_behavior.py",
"py": '''"""Report Stripe prices left at tax_behavior unspecified, ranked by how live they are.

Read only. Four GETs, no writes: give this a RESTRICTED key with read access to
Products, Prices and Subscriptions. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_price_tax_behavior")

API = "https://api.stripe.com/v1"


def verdict(tax_behavior, active_subscriptions, product_tax_code, automatic_tax_in_use):
    """Classify one active price. Pure, so the rules can be tested offline.

    `tax_behavior` is the raw field, `active_subscriptions` how many live
    subscriptions bill this price, `product_tax_code` the parent product's
    tax_code or None, and `automatic_tax_in_use` whether any subscription on the
    account has automatic tax on. Returns (state, detail).
    """
    if tax_behavior == "unspecified":
        if automatic_tax_in_use:
            return ("blocking",
                    "unspecified while automatic tax is in use on this account: "
                    "line items on this price cannot be added to an automatic tax "
                    "invoice. %d active subscription(s)." % active_subscriptions)
        if active_subscriptions:
            return ("live",
                    "unspecified with %d active subscription(s). Setting it means "
                    "a replacement price and a migration, not an edit."
                    % active_subscriptions)
        return ("dormant",
                "unspecified with no active subscriptions. Set it now, while it is "
                "still settable and nothing is billing on it.")
    if not product_tax_code:
        return ("no-tax-code",
                "%s, but the product carries no tax_code, so the rate falls back to "
                "the account default." % tax_behavior)
    return ("ready", "%s, product tax code %s" % (tax_behavior, product_tax_code))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def paginate(session, path, **params):
    params = dict(params, limit=params.get("limit", 100))
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for row in data:
            yield row
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def product_tax_codes(session):
    """Map product id to tax_code. The tax code can be a string id or an object."""
    codes = {}
    for prod in paginate(session, "/products", active="true"):
        code = prod.get("tax_code")
        if isinstance(code, dict):
            code = code.get("id")
        codes[prod["id"]] = code
    return codes


def active_subscription_count(session, price_id, cap):
    """Count active subscriptions billing one price, stopping at `cap`.

    The exact number stops mattering above a handful: any non-zero count means a
    replacement price and a migration rather than an edit.
    """
    count = 0
    for _sub in paginate(session, "/subscriptions", price=price_id, status="active"):
        count += 1
        if count >= cap:
            break
    return count


def automatic_tax_in_use(session):
    page = get(session, "/subscriptions", limit=1,
               **{"automatic_tax[enabled]": "true"})
    return bool(page.get("data"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subscription-cap", type=int, default=200,
                    help="stop counting subscriptions per price at this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    codes = product_tax_codes(s)
    auto_tax = automatic_tax_in_use(s)
    if auto_tax:
        log.info("automatic tax is enabled on at least one subscription, so an "
                 "unspecified price is an active fault rather than a latent one")

    findings = 0
    total = 0
    for price in paginate(s, "/prices", active="true"):
        total += 1
        behavior = price.get("tax_behavior")
        product = price.get("product")
        if isinstance(product, dict):
            product = product.get("id")
        subs = (active_subscription_count(s, price["id"], args.subscription_cap)
                if behavior == "unspecified" else 0)
        state, detail = verdict(behavior, subs, codes.get(product), auto_tax)

        line = "%-12s %s  %s" % (state, price["id"], detail)
        if state == "ready":
            log.info(line)
            continue

        findings += 1
        log.warning(line)
        if state == "dormant":
            log.warning("  set tax_behavior on this price while it is still "
                        "unspecified; the value is permanent once set")
        elif state in ("live", "blocking"):
            log.warning("  create a replacement price on product %s with the same "
                        "amount, currency and interval plus an explicit "
                        "tax_behavior, migrate the subscriptions with an explicit "
                        "proration decision, then archive %s",
                        product, price["id"])
        else:
            log.warning("  set a tax_code on product %s so the rate stops falling "
                        "back to the account default", product)

    log.info("%d active price(s), %d needing attention", total, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-price-tax-behavior.mjs",
"js": '''/**
 * Report Stripe prices left at tax_behavior unspecified, ranked by how live they are.
 *
 * Read only. Four GETs, no writes: give this a RESTRICTED key with read access to
 * Products, Prices and Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one active price. Pure, so the rules can be tested offline.
 * Returns [state, detail].
 */
export function verdict(taxBehavior, activeSubscriptions, productTaxCode, automaticTaxInUse) {
  if (taxBehavior === 'unspecified') {
    if (automaticTaxInUse) {
      return ['blocking',
        'unspecified while automatic tax is in use on this account: line items on ' +
        'this price cannot be added to an automatic tax invoice. ' +
        `${activeSubscriptions} active subscription(s).`];
    }
    if (activeSubscriptions) {
      return ['live',
        `unspecified with ${activeSubscriptions} active subscription(s). Setting it ` +
        'means a replacement price and a migration, not an edit.'];
    }
    return ['dormant',
      'unspecified with no active subscriptions. Set it now, while it is still ' +
      'settable and nothing is billing on it.'];
  }
  if (!productTaxCode) {
    return ['no-tax-code',
      `${taxBehavior}, but the product carries no tax_code, so the rate falls back ` +
      'to the account default.'];
  }
  return ['ready', `${taxBehavior}, product tax code ${productTaxCode}`];
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

async function* paginate(key, path, params = {}) {
  const p = { limit: 100, ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    for (const row of data) yield row;
    if (data.length === 0 || !page.has_more) return;
    p.starting_after = data[data.length - 1].id;
  }
}

/** Map product id to tax_code. The tax code can be a string id or an object. */
export async function productTaxCodes(key) {
  const codes = new Map();
  for await (const prod of paginate(key, '/products', { active: 'true' })) {
    const code = prod.tax_code;
    codes.set(prod.id, typeof code === 'object' && code !== null ? code.id : code);
  }
  return codes;
}

async function activeSubscriptionCount(key, priceId, cap) {
  let count = 0;
  for await (const _sub of paginate(key, '/subscriptions',
    { price: priceId, status: 'active' })) {
    count += 1;
    if (count >= cap) break;
  }
  return count;
}

async function automaticTaxInUse(key) {
  const page = await get(key, '/subscriptions',
    { limit: 1, 'automatic_tax[enabled]': 'true' });
  return (page.data ?? []).length > 0;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const cap = 200;
  const codes = await productTaxCodes(key);
  const autoTax = await automaticTaxInUse(key);
  if (autoTax) {
    console.log('automatic tax is enabled on at least one subscription, so an ' +
      'unspecified price is an active fault rather than a latent one');
  }

  let findings = 0;
  let total = 0;
  for await (const price of paginate(key, '/prices', { active: 'true' })) {
    total += 1;
    const behavior = price.tax_behavior;
    const product = typeof price.product === 'object' && price.product !== null
      ? price.product.id : price.product;
    const subs = behavior === 'unspecified'
      ? await activeSubscriptionCount(key, price.id, cap) : 0;
    const [state, detail] = verdict(behavior, subs, codes.get(product), autoTax);

    const line = `${state.padEnd(12)} ${price.id}  ${detail}`;
    if (state === 'ready') { console.log(line); continue; }

    findings += 1;
    console.warn(line);
    if (state === 'dormant') {
      console.warn('  set tax_behavior on this price while it is still unspecified; ' +
        'the value is permanent once set');
    } else if (state === 'live' || state === 'blocking') {
      console.warn(`  create a replacement price on product ${product} with the same ` +
        'amount, currency and interval plus an explicit tax_behavior, migrate the ' +
        `subscriptions with an explicit proration decision, then archive ${price.id}`);
    } else {
      console.warn(`  set a tax_code on product ${product} so the rate stops falling ` +
        'back to the account default');
    }
  }

  console.log(`${total} active price(s), ${findings} needing attention`);
  if (findings) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the escalation, because the same <code>unspecified</code> value means three different amounts of work depending on what else is true. They also cover the price whose behavior is correct and whose product has no tax code, which is the finding people skip past on the way to the interesting ones.",
"test_py_file": "test_stripe_price_tax_behavior.py",
"test_py": '''from stripe_price_tax_behavior import verdict


def test_an_explicit_behavior_with_a_tax_code_is_ready():
    state, detail = verdict("exclusive", 0, "txcd_10000000", True)
    assert state == "ready"
    assert "txcd_10000000" in detail


def test_a_dormant_unspecified_price_can_be_fixed_in_place():
    state, detail = verdict("unspecified", 0, "txcd_10000000", False)
    assert state == "dormant"
    assert "still settable" in detail


def test_subscriptions_turn_the_fix_into_a_migration():
    state, detail = verdict("unspecified", 412, "txcd_10000000", False)
    assert state == "live"
    assert "412 active subscription(s)" in detail


def test_automatic_tax_makes_it_an_active_fault():
    # The same field, the same value, but now line items are rejected outright.
    state, detail = verdict("unspecified", 0, "txcd_10000000", True)
    assert state == "blocking"
    assert "cannot be added" in detail


def test_a_correct_behavior_on_a_product_with_no_tax_code_is_still_flagged():
    state, detail = verdict("inclusive", 0, None, False)
    assert state == "no-tax-code"
    assert "account default" in detail
''',
"test_js_file": "stripe-price-tax-behavior.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-price-tax-behavior.mjs';

test('an explicit behavior with a tax code is ready', () => {
  const [state, detail] = verdict('exclusive', 0, 'txcd_10000000', true);
  assert.equal(state, 'ready');
  assert.ok(detail.includes('txcd_10000000'));
});

test('a dormant unspecified price can be fixed in place', () => {
  const [state, detail] = verdict('unspecified', 0, 'txcd_10000000', false);
  assert.equal(state, 'dormant');
  assert.ok(detail.includes('still settable'));
});

test('subscriptions turn the fix into a migration', () => {
  const [state, detail] = verdict('unspecified', 412, 'txcd_10000000', false);
  assert.equal(state, 'live');
  assert.ok(detail.includes('412 active subscription(s)'));
});

test('automatic tax makes it an active fault', () => {
  const [state, detail] = verdict('unspecified', 0, 'txcd_10000000', true);
  assert.equal(state, 'blocking');
  assert.ok(detail.includes('cannot be added'));
});

test('a correct behavior on a product with no tax code is still flagged', () => {
  const [state, detail] = verdict('inclusive', 0, null, false);
  assert.equal(state, 'no-tax-code');
  assert.ok(detail.includes('account default'));
});
''',
"faq": [
 ("What does tax_behavior=unspecified actually mean?",
  "That nobody has told Stripe whether the price already contains tax. It is the default on every price created without the field. Inclusive means the tax is inside the amount, exclusive means it is added on top, and unspecified means the tax engine has no basis to compute either."),
 ("Why can I not just change tax_behavior on the price?",
  "You can, once, while it is still unspecified. After it is inclusive or exclusive it is fixed, because changing it would silently reprice everything billing on it. That is why the check counts active subscriptions: it decides whether you are editing a price or replacing one."),
 ("What breaks if I leave it alone?",
  "Line items on an unspecified price cannot be added to an invoice with automatic tax, so that fails loudly. Everything short of that is quiet: tax computed against the wrong base, or not computed at all, on prices that otherwise bill perfectly."),
 ("Why does the script also look at product tax codes?",
  "Because behavior and tax code are the two halves of getting the number right. Behavior says how tax relates to the amount; the tax code says which rate applies. A product with no tax_code falls back to your account default, which is fine for a single-category catalogue and wrong the moment it mixes digital services with anything else."),
 ("How do I stop new prices arriving unspecified?",
  "Set the default tax behavior in Stripe's tax settings so new prices inherit it. Doing that first is what keeps the list from growing while you migrate the prices already on it."),
],
"related": [
 ("/stripe/no-tax-registrations-while-selling-abroad/", "No tax registrations while invoicing abroad"),
 ("/stripe/automatic-tax-disabled-everywhere/", "automatic_tax disabled while selling abroad"),
 ("/stripe/orphaned-pending-invoice-items/", "Pending invoice items that never reach an invoice"),
],
"citations": [CITE_PRICE_OBJ, CITE_INVOICE_OBJ, CITE_TAX_INVOICING, CITE_PRODUCT_OBJ],
},

]
