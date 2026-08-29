#!/usr/bin/env python3
"""/stripe/ field notes, batch O — Connect capabilities, payout schedules,
abandoned onboarding and unread verification errors.

Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.

These four sit next to the four Connect notes already published and deliberately
do not restate them. `connected-accounts-charges-disabled` reads one boolean on
the Account; this batch reads the capability underneath it, the schedule that
decides whether money ever leaves, the cohort that never finished onboarding at
all, and the error codes explaining why a submitted document was rejected.
"""

CITE_CAPABILITIES = ("Account capabilities — Stripe Docs",
                     "https://docs.stripe.com/connect/account-capabilities")
CITE_CAPABILITY_OBJ = ("The capability object — Stripe API reference",
                       "https://docs.stripe.com/api/capabilities/object")
CITE_ACCOUNT_OBJ = ("The account object — Stripe API reference",
                    "https://docs.stripe.com/api/accounts/object")
CITE_VERIFICATION = ("Handling verification with the API — Stripe Docs",
                     "https://docs.stripe.com/connect/handling-api-verification")
CITE_PAYOUTS = ("Payouts — Stripe Docs",
                "https://docs.stripe.com/payouts")
CITE_PAYOUT_SCHEDULE = ("Manage payout schedule — Stripe Docs",
                        "https://docs.stripe.com/connect/manage-payout-schedule")
CITE_BALANCE_OBJ = ("The balance object — Stripe API reference",
                    "https://docs.stripe.com/api/balance/balance_object")
CITE_HOSTED_ONBOARDING = ("Hosted onboarding — Stripe Docs",
                          "https://docs.stripe.com/connect/hosted-onboarding")
CITE_ACCOUNT_LINK_OBJ = ("The account link object — Stripe API reference",
                         "https://docs.stripe.com/api/account_links/object")
CITE_PERSON_OBJ = ("The person object — Stripe API reference",
                   "https://docs.stripe.com/api/persons/object")

GUIDES = [

{
"slug": "transfers-capability-inactive",
"title": "transfers capability is inactive so every transfer 400s",
"description": "Transfers fail for one seller while every other account works. charges_enabled is true; the capability that moves the money is a different field.",
"h1": "the transfers capability is inactive so every transfer 400s",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe transfers capability inactive", "stripe capability status",
             "stripe connect transfer 400", "capabilities.transfers",
             "stripe request capability"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One seller's payouts never arrive. Their checkout works, the charges land on the platform, the account object says <code>charges_enabled: true</code>, and the seller's own balance stays at zero. Every attempt to move the money returns a 400 that names a capability nobody on the team has ever read a value from.",
"short_answer": """<p>Paginate <code>GET /v1/accounts?limit=100</code> and read <code>capabilities.transfers</code>. It has four possible states and only one of them lets funds move: <code>active</code>. <code>pending</code> means Stripe is verifying, <code>inactive</code> means a requirement is unmet, and a <strong>missing key</strong> means the capability was never requested at all, which is the case no boolean on the account will ever show you.</p>
<p>The list response gives you the status and nothing else. For the reason, read the capability itself: <code>GET /v1/accounts/{id}/capabilities/transfers</code> returns <code>requirements.currently_due</code>, <code>requirements.pending_verification</code> and <code>requirements.disabled_reason</code> scoped to that one capability rather than to the account.</p>""",
"problem": """<p>The confusing part is that the account looks healthy. <code>charges_enabled</code> is true, so a monitor built around it stays green. Payments succeed, because taking a payment on the platform and moving funds to a connected account are two separate permissions and only the first one is working. The seller sees orders arrive and no money follow.</p>
<p>The error itself is not much help either. It comes back on the call that moves funds, at the moment somebody tries, which is usually a background job rather than a request anybody is watching. So the failure surfaces as a stuck queue or a retry loop somewhere in your own infrastructure, several steps removed from the account that caused it.</p>""",
"why": """<p><strong>A capability is not the same permission as the account boolean.</strong> <code>charges_enabled</code> tells you the account can accept payments. Moving funds <em>to</em> that account requires the <code>transfers</code> capability to be <code>active</code>, verified against its own requirement set. The two can and do disagree, and a check that reads only the account object cannot see the disagreement.</p>
<p><strong>The unrequested case has no field of its own.</strong> When a capability was never requested, Stripe does not report it as <code>inactive</code> &mdash; the key is simply absent from the <code>capabilities</code> hash. Code written as <code>if account.capabilities.transfers != 'active'</code> catches it; code written as <code>if status == 'inactive'</code> does not, and this is the state that lasts for years because nothing anywhere ever complains about it.</p>
<p><strong>Capabilities can go back down.</strong> An account that has been transferring for months drops to <code>inactive</code> when new requirements go unmet past their deadline. It is not a one-time onboarding gate you clear and forget; it is a live status that needs the same daily read as any other.</p>
<p><strong>The requirements you need are not the ones on the account.</strong> Stripe documents an explicit coupling between <code>card_payments</code> and <code>transfers</code>: where an account has both, one of them sitting at <code>inactive</code> disables the pair. That is why a team can satisfy every field the account object lists and watch <code>transfers</code> stay stubbornly inactive. Read <code>GET /v1/accounts/{id}/capabilities</code> and take the union.</p>""",
"steps": [
 {"h": "Read capabilities.transfers, not charges_enabled",
  "body": """<p>Compare against the string <code>active</code> rather than testing for <code>inactive</code>. The four outcomes are active, pending, inactive and absent, and absent is a real state with a different repair from all the others.</p>"""},
 {"h": "Fetch the capability object for anything that is not active",
  "body": """<p><code>GET /v1/accounts/{id}/capabilities/transfers</code> is one extra GET per unhealthy account and it is the only place the reason lives. <code>requirements.currently_due</code> lists the fields for <em>this</em> capability; <code>requirements.disabled_reason</code> says whether a field is even the problem.</p>"""},
 {"h": "Split pending from inactive before telling anyone to do something",
  "body": """<p><code>pending</code> means Stripe is verifying what it already has. There is nothing to collect and no link to send, and sending one anyway produces a completed form with no status change, which reads to the seller as a broken product.</p>"""},
 {"h": "Take the union across every capability, not just this one",
  "body": """<p>Because <code>card_payments</code> and <code>transfers</code> disable each other, the field blocking transfers may be listed under a capability you never use. <code>GET /v1/accounts/{id}/capabilities</code> returns all of them; collect the union of their <code>currently_due</code> in one pass rather than fixing one capability at a time.</p>"""},
 {"h": "Request the capability for accounts that never had it",
  "body": """<p>An absent <code>transfers</code> key is not a verification problem, so no amount of onboarding will fix it. The capability has to be requested for the account first, and only then does Stripe start asking for whatever it needs to make it active.</p>"""},
],
"verify": """<p>Re-run the script. Every account you expect to pay out should report <code>active</code>, and the summary line should show no blocked or unrequested accounts left.</p>
<pre><code class="language-bash">python3 stripe_transfers_capability.py
# 412 account(s): 412 active, 0 blocked, 0 unrequested, 0 held</code></pre>""",
"code_intro": "One paginated GET over the accounts, then one small GET per account that is not already active &mdash; a restricted key with read access to Connected accounts covers both. The classifier is pure and takes the capability object, so the difference between <em>never requested</em>, <em>being verified</em> and <em>waiting on a field</em> is decided by rules you can read rather than inside a request loop.",
"py_file": "stripe_transfers_capability.py",
"py": '''"""Report connected accounts whose transfers capability is not active.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_transfers_capability")

API = "https://api.stripe.com/v1"

# Reasons no amount of field collection will clear. An onboarding link sent to an
# account in one of these states produces a completed form and no status change.
DASHBOARD_ONLY = ("listed", "under_review", "rejected")


def classify(capability):
    """Sort the transfers capability of one account. Pure, so the states can be
    tested without a network.

    `capability` is the object from GET /v1/accounts/{id}/capabilities/transfers,
    or None when the account's `capabilities` hash has no `transfers` key at all.
    That absence is its own state: the capability was never requested, so no
    requirement is outstanding and none ever will be.

    Returns (state, detail).
    """
    if capability is None:
        return ("unrequested",
                "no transfers capability on the account: it was never requested, "
                "so Stripe is not asking for anything and funds will never move")

    status = capability.get("status")
    reqs = capability.get("requirements") or {}
    due = [f for f in (reqs.get("currently_due") or []) if f]
    verifying = [f for f in (reqs.get("pending_verification") or []) if f]
    reason = reqs.get("disabled_reason")

    if status == "active":
        return ("active", "transfers are active")

    if status == "unrequested":
        return ("unrequested",
                "status unrequested: request the capability before collecting "
                "anything, because nothing is outstanding yet")

    if status == "pending":
        return ("verifying",
                "status pending: Stripe is checking what it already has%s. "
                "Collecting more fields does not speed it up"
                % (", %d field(s) in pending_verification" % len(verifying)
                   if verifying else ""))

    if status == "inactive":
        if due:
            return ("blocked",
                    "status inactive, %d field(s) currently due on this "
                    "capability: %s" % (len(due), ", ".join(due[:4])))
        if verifying:
            return ("verifying",
                    "status inactive with %d field(s) in pending_verification: "
                    "submitted and being checked, nothing to collect"
                    % len(verifying))
        if reason and (reason in DASHBOARD_ONLY
                       or reason.split(".", 1)[0] == "rejected"):
            return ("held",
                    "status inactive, disabled_reason %s: no API call clears "
                    "this one" % reason)
        if reason:
            return ("blocked",
                    "status inactive, disabled_reason %s with nothing currently "
                    "due: read every capability before collecting" % reason)
        return ("unknown",
                "status inactive with no currently_due and no disabled_reason")

    return ("unknown", "unrecognised capability status: %s" % status)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
    """Yield connected accounts, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            yield acct
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    ap.add_argument("--quiet-unrequested", action="store_true",
                    help="do not list accounts that never requested the capability")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    counts = {}
    scanned = 0
    for acct in accounts(s, args.max_accounts):
        scanned += 1
        caps = acct.get("capabilities") or {}

        # The list response carries the status and nothing else. Only fetch the
        # capability object where the status is not already active, because that
        # object is the only place the reason lives.
        capability = None
        if caps.get("transfers") == "active":
            counts["active"] = counts.get("active", 0) + 1
            continue
        if "transfers" in caps:
            capability = get(s, "/accounts/%s/capabilities/transfers"
                             % acct.get("id", ""))

        state, detail = classify(capability)
        counts[state] = counts.get(state, 0) + 1
        if state == "unrequested" and args.quiet_unrequested:
            continue
        log.warning("%s  %-12s %s", acct.get("id", "acct_?"), state, detail)

    blocked = counts.get("blocked", 0)
    held = counts.get("held", 0)
    unrequested = counts.get("unrequested", 0)
    unknown = counts.get("unknown", 0)

    log.info("%d account(s): %d active, %d blocked, %d unrequested, %d held",
             scanned, counts.get("active", 0), blocked, unrequested, held)

    if unrequested:
        log.warning("  repair: request the capability first, then onboard for "
                    "whatever it asks for once Stripe starts asking:")
        log.warning("  POST %s/accounts/{id}/capabilities/transfers  requested=true",
                    API)
    if blocked:
        log.warning("  repair: read every capability and collect the union of "
                    "currently_due, since card_payments and transfers disable "
                    "each other:")
        log.warning("  GET %s/accounts/{id}/capabilities", API)
        log.warning("  then POST %s/accounts/{id} with those fields, or an "
                    "account link with type=account_onboarding", API)
    if held:
        log.warning("  repair: Dashboard, Connected accounts. No field collection "
                    "clears a rejected.* or under_review reason.")
    return 1 if (blocked or held or unrequested or unknown) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-transfers-capability.mjs",
"js": '''/**
 * Report connected accounts whose transfers capability is not active.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Reasons no amount of field collection will clear.
const DASHBOARD_ONLY = ['listed', 'under_review', 'rejected'];

/**
 * Sort the transfers capability of one account. Pure, so the states can be
 * tested without a network. `capability` is null when the account's capabilities
 * hash has no transfers key at all, which means it was never requested.
 * Returns [state, detail].
 */
export function classify(capability) {
  if (capability === null || capability === undefined) {
    return ['unrequested',
      'no transfers capability on the account: it was never requested, so ' +
      'Stripe is not asking for anything and funds will never move'];
  }

  const status = capability.status;
  const reqs = capability.requirements ?? {};
  const due = (reqs.currently_due ?? []).filter(Boolean);
  const verifying = (reqs.pending_verification ?? []).filter(Boolean);
  const reason = reqs.disabled_reason ?? null;

  if (status === 'active') return ['active', 'transfers are active'];

  if (status === 'unrequested') {
    return ['unrequested',
      'status unrequested: request the capability before collecting anything, ' +
      'because nothing is outstanding yet'];
  }

  if (status === 'pending') {
    const extra = verifying.length
      ? `, ${verifying.length} field(s) in pending_verification` : '';
    return ['verifying',
      `status pending: Stripe is checking what it already has${extra}. ` +
      'Collecting more fields does not speed it up'];
  }

  if (status === 'inactive') {
    if (due.length) {
      return ['blocked',
        `status inactive, ${due.length} field(s) currently due on this ` +
        `capability: ${due.slice(0, 4).join(', ')}`];
    }
    if (verifying.length) {
      return ['verifying',
        `status inactive with ${verifying.length} field(s) in ` +
        'pending_verification: submitted and being checked, nothing to collect'];
    }
    if (reason && (DASHBOARD_ONLY.includes(reason) || reason.split('.')[0] === 'rejected')) {
      return ['held',
        `status inactive, disabled_reason ${reason}: no API call clears this one`];
    }
    if (reason) {
      return ['blocked',
        `status inactive, disabled_reason ${reason} with nothing currently due: ` +
        'read every capability before collecting'];
    }
    return ['unknown', 'status inactive with no currently_due and no disabled_reason'];
  }

  return ['unknown', `unrecognised capability status: ${status}`];
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

export async function* accounts(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/accounts', params);
    const data = page.data ?? [];
    for (const acct of data) {
      yield acct;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
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

  const counts = {};
  let scanned = 0;
  for await (const acct of accounts(key)) {
    scanned += 1;
    const caps = acct.capabilities ?? {};

    if (caps.transfers === 'active') {
      counts.active = (counts.active ?? 0) + 1;
      continue;
    }

    // Only fetch the capability object where the status is not already active:
    // it is the only place the reason lives.
    let capability = null;
    if ('transfers' in caps) {
      capability = await get(key, `/accounts/${acct.id}/capabilities/transfers`);
    }

    const [state, detail] = classify(capability);
    counts[state] = (counts[state] ?? 0) + 1;
    console.warn(`${acct.id ?? 'acct_?'}  ${state.padEnd(12)} ${detail}`);
  }

  const blocked = counts.blocked ?? 0;
  const held = counts.held ?? 0;
  const unrequested = counts.unrequested ?? 0;
  const unknown = counts.unknown ?? 0;

  console.log(`${scanned} account(s): ${counts.active ?? 0} active, ${blocked} ` +
              `blocked, ${unrequested} unrequested, ${held} held`);

  if (unrequested) {
    console.warn('  repair: request the capability first, then onboard for ' +
                 'whatever it asks for once Stripe starts asking:');
    console.warn(`  POST ${API}/accounts/{id}/capabilities/transfers  requested=true`);
  }
  if (blocked) {
    console.warn('  repair: read every capability and collect the union of ' +
                 'currently_due, since card_payments and transfers disable each other:');
    console.warn(`  GET ${API}/accounts/{id}/capabilities`);
  }
  if (held) {
    console.warn('  repair: Dashboard, Connected accounts. No field collection ' +
                 'clears a rejected.* or under_review reason.');
  }
  if (blocked || held || unrequested || unknown) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are mostly about the four statuses being kept apart, because every one of them has a different repair and three of them are easy to collapse into a single <em>broken</em> bucket. The absent capability is the case worth writing a test for: it is the one that produces no error anywhere and lasts longest.",
"test_py_file": "test_stripe_transfers_capability.py",
"test_py": '''from stripe_transfers_capability import classify


def test_absent_capability_is_unrequested_not_inactive():
    # No transfers key on the account at all. Nothing is outstanding, so no
    # onboarding link will ever help; the capability has to be requested.
    state, detail = classify(None)
    assert state == "unrequested"
    assert "never requested" in detail


def test_active_is_the_only_healthy_status():
    assert classify({"status": "active"})[0] == "active"


def test_pending_is_not_something_to_chase():
    state, detail = classify({
        "status": "pending",
        "requirements": {"pending_verification": ["individual.verification.document"]},
    })
    assert state == "verifying"
    assert "does not speed it up" in detail


def test_inactive_with_fields_names_them():
    state, detail = classify({
        "status": "inactive",
        "requirements": {"currently_due": ["company.tax_id", "business_profile.url"]},
    })
    assert state == "blocked"
    assert "company.tax_id" in detail


def test_rejected_reason_is_not_a_field_to_collect():
    state, detail = classify({
        "status": "inactive",
        "requirements": {"currently_due": [], "disabled_reason": "rejected.fraud"},
    })
    assert state == "held"
    assert "rejected.fraud" in detail
''',
"test_js_file": "stripe-transfers-capability.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-transfers-capability.mjs';

test('absent capability is unrequested, not inactive', () => {
  const [state, detail] = classify(null);
  assert.equal(state, 'unrequested');
  assert.match(detail, /never requested/);
});

test('active is the only healthy status', () => {
  assert.equal(classify({ status: 'active' })[0], 'active');
});

test('pending is not something to chase', () => {
  const [state, detail] = classify({
    status: 'pending',
    requirements: { pending_verification: ['individual.verification.document'] },
  });
  assert.equal(state, 'verifying');
  assert.match(detail, /does not speed it up/);
});

test('inactive with fields names them', () => {
  const [state, detail] = classify({
    status: 'inactive',
    requirements: { currently_due: ['company.tax_id', 'business_profile.url'] },
  });
  assert.equal(state, 'blocked');
  assert.match(detail, /company\\.tax_id/);
});

test('a rejected reason is not a field to collect', () => {
  const [state, detail] = classify({
    status: 'inactive',
    requirements: { currently_due: [], disabled_reason: 'rejected.fraud' },
  });
  assert.equal(state, 'held');
  assert.match(detail, /rejected\\.fraud/);
});
''',
"faq": [
 ("Why does the account say charges_enabled true if transfers fail?",
  "They are different permissions. charges_enabled says the account can accept payments; the transfers capability says funds can be moved to it. Each has its own requirement set and its own verification, so an account can take payments all day while nothing can be paid out to it."),
 ("What does an absent transfers key mean?",
  "It was never requested. Stripe omits unrequested capabilities from the capabilities hash rather than listing them as inactive, so there is no status to read and no requirement outstanding. Request the capability, and only then does Stripe start asking for what it needs."),
 ("I fixed everything in currently_due and transfers is still inactive. Why?",
  "Read every capability, not just this one. Where an account has both card_payments and transfers, either one sitting at inactive disables the pair, so the field blocking your transfers can be listed under a capability you never use. GET /v1/accounts/{id}/capabilities and satisfy the union."),
 ("Is pending the same as inactive?",
  "No, and it is worth keeping apart. Pending means Stripe is verifying what it already holds: there is nothing to collect and no link to send. Sending one anyway gives the seller a form that changes nothing, which reads as a broken product rather than as patience."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Connected accounts is enough for both the account list and the capability objects, and it is what this script should be given. It cannot move money if it leaks."),
],
"related": [
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/payout-schedule-left-on-manual/", "A payout schedule left on manual strands the balance"),
],
"citations": [CITE_CAPABILITIES, CITE_CAPABILITY_OBJ, CITE_ACCOUNT_OBJ, CITE_VERIFICATION],
},

{
"slug": "payout-schedule-left-on-manual",
"title": "A payout schedule left on manual strands the balance",
"description": "A seller's balance climbs with a valid bank account and no requirements outstanding, because manual means Stripe never initiates the payout. Your code must.",
"h1": "a payout schedule left on manual strands the balance",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payout schedule manual", "stripe manual payouts connect",
             "settings.payouts.schedule.interval", "stripe delay_days",
             "stripe balance not paid out"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A seller opens a ticket asking where four months of money went. Everything you check says the account is fine: payouts are enabled, no requirements are outstanding, a verified bank account is attached and set as the default. There are no failed payouts to investigate because there are no payouts at all, and the reason is a single string in a settings hash nobody has read since the platform was built.",
"short_answer": """<p>Paginate <code>GET /v1/accounts?limit=100</code> and read <code>settings.payouts.schedule.interval</code>. Where it is <code>manual</code> and <code>payouts_enabled</code> is <code>true</code>, Stripe will never initiate a payout for that account. It is not a fault state, which is exactly why nothing reports it.</p>
<p>Confirm that money is actually stuck rather than merely unscheduled: with <code>Stripe-Account: acct_x</code>, <code>GET /v1/balance</code> for a positive <code>available[].amount</code>, and <code>GET /v1/payouts?limit=1</code> for the most recent payout. A positive balance and no payout in the last 30 days is stranded money; a positive balance with a payout last week means a job exists and is running.</p>
<p>While you are there, read <code>settings.payouts.schedule.delay_days</code>. An inflated value produces the same "no payouts" complaint from a schedule that is working exactly as configured.</p>""",
"problem": """<p>Every health check on this account passes. That is the whole problem. Manual is a legitimate setting, deliberately available, and Stripe has no opinion about whether you meant it, so an account left on it looks identical to one where a nightly job is quietly doing its work. The absence of that job is not something the API can see.</p>
<p>It typically starts as a decision. Somebody set the platform default to manual during a hold-funds phase, or turned it on for one seller during a dispute, and the corresponding <em>create the payouts ourselves</em> work item was either never written or was written for a different cohort. New accounts inherit the platform default, so the population of affected sellers grows quietly with signups.</p>
<p>The damage compounds. Every week the stranded amount grows, and the eventual fix is not a small one: switching to an automatic schedule releases a large balance at once, which is exactly the kind of movement that draws a risk review.</p>""",
"why": """<p><strong>Manual is a setting, not a failure.</strong> There is no <code>disabled_reason</code>, no requirement, no event, and nothing in the Dashboard turns red. The only signal is an absence &mdash; payouts that were never created &mdash; and absences do not raise alerts unless something is deliberately looking for them.</p>
<p><strong>It is inherited, so it spreads without a decision being made twice.</strong> The platform-level default applies to accounts created after it was set. One choice made during a beta becomes the configuration of every seller who has signed up since.</p>
<p><strong>The obvious monitor watches the wrong list.</strong> Checking <code>GET /v1/payouts?status=failed</code> finds nothing here, forever, because nothing was ever attempted. The same blind spot makes an account with no external account attached look healthy, and the two conditions produce an identical symptom from opposite causes: one has nowhere to send money, this one has no instruction to send it.</p>
<p><strong>A large <code>delay_days</code> looks the same from outside.</strong> A schedule with an inflated delay is working correctly and still produces a seller who says they have not been paid. It is worth flagging next to manual precisely because the complaint is identical and the fix is not.</p>""",
"steps": [
 {"h": "Read the schedule on every connected account",
  "body": """<p><code>settings.payouts.schedule.interval</code> is one of <code>manual</code>, <code>daily</code>, <code>weekly</code> or <code>monthly</code>. Flag <code>manual</code> where <code>payouts_enabled</code> is true, because that combination means Stripe is willing to pay out and is simply never asked to.</p>"""},
 {"h": "Separate manual-and-empty from manual-and-stranded",
  "body": """<p>A manual schedule on an account with a zero balance is a configuration question. A manual schedule on an account holding money is a support ticket. Read <code>GET /v1/balance</code> with the <code>Stripe-Account</code> header to tell them apart before anyone gets paged.</p>"""},
 {"h": "Check whether a payout job exists at all",
  "body": """<p><code>GET /v1/payouts?limit=1</code> against the account answers the question the settings cannot: is something out there creating payouts? A recent one means your job is running and manual is intentional. None at all, or one from months ago, means the job was never written.</p>"""},
 {"h": "Flag an inflated delay_days alongside it",
  "body": """<p>Anything well above the country minimum is worth listing. It is not broken, but it explains the same complaint, and knowing which of the two you are looking at saves an afternoon.</p>"""},
 {"h": "Decide deliberately, then release carefully",
  "body": """<p>Either switch the interval to an automatic one or commit to writing the job. If you switch, expect the accumulated balance to go out in the first payout: tell the seller, and expect Stripe to look at a movement that size on an account with no payout history.</p>"""},
],
"verify": """<p>Re-run the script. Accounts on a manual schedule should either hold no balance or show a recent payout, and no account should appear as stranded.</p>
<pre><code class="language-bash">python3 stripe_manual_payout_schedule.py
# 412 account(s): 0 stranded, 6 manual, 2 slow</code></pre>""",
"code_intro": "One paginated GET over the accounts, then two small GETs per manual account using the <code>Stripe-Account</code> header &mdash; a restricted key with read access to Connected accounts, Balance and Payouts covers all three. The classifier is pure and takes the account plus the two facts read per account, so the line between a deliberate manual schedule and stranded money is a rule you can read rather than a judgement made mid-loop.",
"py_file": "stripe_manual_payout_schedule.py",
"py": '''"""Report connected accounts whose payout schedule leaves money stranded.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Connected accounts, Balance and Payouts. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_manual_payout_schedule")

API = "https://api.stripe.com/v1"

STALE_DAYS = 30      # a manual account with money and no payout this recently
SLOW_DELAY_DAYS = 14  # well above any country minimum


def classify(account, available, last_payout_age_days):
    """Sort one connected account by its payout schedule. Pure, so the boundary
    between a deliberate manual schedule and stranded money can be tested.

    `available` is the summed available balance for that account in minor units,
    or None when it was not read. `last_payout_age_days` is the age of the most
    recent payout in days, or None when the account has never had one.

    Returns (state, detail).
    """
    schedule = (((account.get("settings") or {}).get("payouts") or {})
                .get("schedule") or {})
    interval = schedule.get("interval")
    delay = schedule.get("delay_days")
    held = available or 0

    if not account.get("payouts_enabled"):
        return ("disabled",
                "payouts_enabled is false: the schedule is not what is stopping "
                "the money, so fix the requirements first")

    if interval == "manual":
        if held <= 0:
            return ("manual",
                    "manual schedule with nothing available: intentional or not, "
                    "no money is stuck right now")
        if last_payout_age_days is None:
            return ("stranded",
                    "manual schedule, %d available and no payout has ever been "
                    "created: nothing is going to move it" % held)
        if last_payout_age_days >= STALE_DAYS:
            return ("stranded",
                    "manual schedule, %d available and the last payout was %.0f "
                    "days ago: whatever creates them has stopped"
                    % (held, last_payout_age_days))
        return ("manual",
                "manual schedule, %d available and a payout %.0f days ago: a job "
                "is running" % (held, last_payout_age_days))

    if interval is None:
        return ("unknown",
                "no settings.payouts.schedule.interval on the account object")

    if isinstance(delay, int) and delay > SLOW_DELAY_DAYS:
        return ("slow",
                "%s schedule with delay_days=%d: working as configured, and far "
                "enough out to produce the same complaint" % (interval, delay))

    return ("scheduled", "%s schedule, delay_days=%s" % (interval, delay))


def get(session, path, account=None, **params):
    """GET one path. `account` sets the Stripe-Account header for per-account reads."""
    headers = {"Stripe-Account": account} if account else None
    r = session.get(API + path, params=params, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
    """Yield connected accounts, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            yield acct
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def stranded_facts(session, account_id):
    """Read the two facts that separate a deliberate manual schedule from a stuck one."""
    balance = get(session, "/balance", account=account_id)
    available = sum(b.get("amount", 0) for b in (balance.get("available") or []))
    payouts = get(session, "/payouts", account=account_id, limit=1)
    data = payouts.get("data") or []
    age = None
    if data and data[0].get("created"):
        age = (time.time() - data[0]["created"]) / 86400.0
    return available, age


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    ap.add_argument("--stale-days", type=float, default=STALE_DAYS,
                    help="a manual account with no payout this recently is stranded")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    counts = {}
    scanned = 0
    for acct in accounts(s, args.max_accounts):
        scanned += 1
        schedule = (((acct.get("settings") or {}).get("payouts") or {})
                    .get("schedule") or {})

        # Only spend the two extra GETs where the schedule says nobody is going
        # to create a payout on its own.
        available, age = (None, None)
        if schedule.get("interval") == "manual" and acct.get("payouts_enabled"):
            available, age = stranded_facts(s, acct.get("id", ""))

        state, detail = classify(acct, available, age)
        counts[state] = counts.get(state, 0) + 1
        if state in ("scheduled",):
            continue
        log.warning("%s  %-10s %s", acct.get("id", "acct_?"), state, detail)

    stranded = counts.get("stranded", 0)
    slow = counts.get("slow", 0)

    log.info("%d account(s): %d stranded, %d manual, %d slow",
             scanned, stranded, counts.get("manual", 0), slow)

    if stranded:
        log.warning("  repair, one of two, and pick deliberately:")
        log.warning("  POST %s/accounts/{id}  "
                    "settings[payouts][schedule][interval]=daily", API)
        log.warning("  or keep manual and write the job that creates "
                    "POST %s/payouts against each account", API)
        log.warning("  note: the first automatic payout releases the whole "
                    "accumulated balance at once. Warn the seller.")
    if slow:
        log.warning("  repair: lower settings[payouts][schedule][delay_days] to "
                    "the country minimum if it was inflated by accident")
    return 1 if stranded else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-manual-payout-schedule.mjs",
"js": '''/**
 * Report connected accounts whose payout schedule leaves money stranded.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Connected accounts, Balance and Payouts. The repair is printed,
 * never performed.
 */
const API = 'https://api.stripe.com/v1';

export const STALE_DAYS = 30;      // manual, holding money, no payout this recently
const SLOW_DELAY_DAYS = 14;        // well above any country minimum

/**
 * Sort one connected account by its payout schedule. Pure, so the boundary
 * between a deliberate manual schedule and stranded money can be tested.
 * `available` is the summed available balance in minor units, or null.
 * `lastPayoutAgeDays` is null when the account has never had a payout.
 * Returns [state, detail].
 */
export function classify(account, available, lastPayoutAgeDays) {
  const schedule = account.settings?.payouts?.schedule ?? {};
  const interval = schedule.interval ?? null;
  const delay = schedule.delay_days;
  const held = available ?? 0;

  if (!account.payouts_enabled) {
    return ['disabled',
      'payouts_enabled is false: the schedule is not what is stopping the ' +
      'money, so fix the requirements first'];
  }

  if (interval === 'manual') {
    if (held <= 0) {
      return ['manual',
        'manual schedule with nothing available: intentional or not, no money ' +
        'is stuck right now'];
    }
    if (lastPayoutAgeDays === null || lastPayoutAgeDays === undefined) {
      return ['stranded',
        `manual schedule, ${held} available and no payout has ever been ` +
        'created: nothing is going to move it'];
    }
    if (lastPayoutAgeDays >= STALE_DAYS) {
      return ['stranded',
        `manual schedule, ${held} available and the last payout was ` +
        `${lastPayoutAgeDays.toFixed(0)} days ago: whatever creates them has stopped`];
    }
    return ['manual',
      `manual schedule, ${held} available and a payout ` +
      `${lastPayoutAgeDays.toFixed(0)} days ago: a job is running`];
  }

  if (interval === null) {
    return ['unknown', 'no settings.payouts.schedule.interval on the account object'];
  }

  if (Number.isInteger(delay) && delay > SLOW_DELAY_DAYS) {
    return ['slow',
      `${interval} schedule with delay_days=${delay}: working as configured, ` +
      'and far enough out to produce the same complaint'];
  }

  return ['scheduled', `${interval} schedule, delay_days=${delay}`];
}

async function get(key, path, { account = null, params = {} } = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const headers = { Authorization: `Bearer ${key}` };
  if (account) headers['Stripe-Account'] = account;
  const res = await fetch(url, { headers });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function* accounts(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/accounts', { params });
    const data = page.data ?? [];
    for (const acct of data) {
      yield acct;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
    params.starting_after = data[data.length - 1].id;
  }
}

async function strandedFacts(key, accountId) {
  const balance = await get(key, '/balance', { account: accountId });
  const available = (balance.available ?? []).reduce((n, b) => n + (b.amount ?? 0), 0);
  const payouts = await get(key, '/payouts', { account: accountId, params: { limit: 1 } });
  const data = payouts.data ?? [];
  const age = data.length && data[0].created
    ? (Date.now() / 1000 - data[0].created) / 86400 : null;
  return { available, age };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const counts = {};
  let scanned = 0;
  for await (const acct of accounts(key)) {
    scanned += 1;
    const schedule = acct.settings?.payouts?.schedule ?? {};

    let available = null;
    let age = null;
    if (schedule.interval === 'manual' && acct.payouts_enabled) {
      ({ available, age } = await strandedFacts(key, acct.id));
    }

    const [state, detail] = classify(acct, available, age);
    counts[state] = (counts[state] ?? 0) + 1;
    if (state === 'scheduled') continue;
    console.warn(`${acct.id ?? 'acct_?'}  ${state.padEnd(10)} ${detail}`);
  }

  const stranded = counts.stranded ?? 0;
  console.log(`${scanned} account(s): ${stranded} stranded, ` +
              `${counts.manual ?? 0} manual, ${counts.slow ?? 0} slow`);

  if (stranded) {
    console.warn('  repair, one of two, and pick deliberately:');
    console.warn(`  POST ${API}/accounts/{id}  settings[payouts][schedule][interval]=daily`);
    console.warn(`  or keep manual and write the job that creates POST ${API}/payouts`);
    console.warn('  note: the first automatic payout releases the whole ' +
                 'accumulated balance at once. Warn the seller.');
  }
  if (counts.slow) {
    console.warn('  repair: lower settings[payouts][schedule][delay_days] to the ' +
                 'country minimum if it was inflated by accident');
  }
  if (stranded) process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the test file does
// not run main(), fail on the missing key and fail the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are about not crying wolf. Manual is a legitimate setting, so the check is only useful if it can tell an account where somebody chose manual and wrote the job from one where somebody chose manual and did not. That distinction is two facts &mdash; a balance and the age of the last payout &mdash; and every boundary between them is here.",
"test_py_file": "test_stripe_manual_payout_schedule.py",
"test_py": '''from stripe_manual_payout_schedule import classify


def manual(payouts_enabled=True, delay=2):
    return {"payouts_enabled": payouts_enabled,
            "settings": {"payouts": {"schedule": {"interval": "manual",
                                                  "delay_days": delay}}}}


def test_manual_with_money_and_no_payout_ever_is_stranded():
    state, detail = classify(manual(), 480000, None)
    assert state == "stranded"
    assert "no payout has ever been created" in detail


def test_manual_with_money_and_a_recent_payout_is_a_running_job():
    # Somebody chose manual and wrote the job. Do not page anyone.
    state, _ = classify(manual(), 480000, 3.0)
    assert state == "manual"


def test_thirty_days_is_the_boundary():
    assert classify(manual(), 100, 29.9)[0] == "manual"
    assert classify(manual(), 100, 30.0)[0] == "stranded"


def test_manual_with_an_empty_balance_is_not_an_incident():
    assert classify(manual(), 0, None)[0] == "manual"


def test_payouts_disabled_is_a_different_problem():
    state, detail = classify(manual(payouts_enabled=False), 90000, None)
    assert state == "disabled"
    assert "requirements first" in detail


def test_inflated_delay_days_is_flagged_separately():
    acct = {"payouts_enabled": True,
            "settings": {"payouts": {"schedule": {"interval": "weekly",
                                                  "delay_days": 30}}}}
    state, detail = classify(acct, None, None)
    assert state == "slow"
    assert "delay_days=30" in detail


def test_an_ordinary_daily_schedule_is_quiet():
    acct = {"payouts_enabled": True,
            "settings": {"payouts": {"schedule": {"interval": "daily",
                                                  "delay_days": 2}}}}
    assert classify(acct, None, None)[0] == "scheduled"
''',
"test_js_file": "stripe-manual-payout-schedule.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-manual-payout-schedule.mjs';

const manual = (payoutsEnabled = true, delay = 2) => ({
  payouts_enabled: payoutsEnabled,
  settings: { payouts: { schedule: { interval: 'manual', delay_days: delay } } },
});

test('manual with money and no payout ever is stranded', () => {
  const [state, detail] = classify(manual(), 480000, null);
  assert.equal(state, 'stranded');
  assert.match(detail, /no payout has ever been created/);
});

test('manual with money and a recent payout is a running job', () => {
  assert.equal(classify(manual(), 480000, 3.0)[0], 'manual');
});

test('thirty days is the boundary', () => {
  assert.equal(classify(manual(), 100, 29.9)[0], 'manual');
  assert.equal(classify(manual(), 100, 30.0)[0], 'stranded');
});

test('manual with an empty balance is not an incident', () => {
  assert.equal(classify(manual(), 0, null)[0], 'manual');
});

test('payouts disabled is a different problem', () => {
  const [state, detail] = classify(manual(false), 90000, null);
  assert.equal(state, 'disabled');
  assert.match(detail, /requirements first/);
});

test('inflated delay_days is flagged separately', () => {
  const acct = {
    payouts_enabled: true,
    settings: { payouts: { schedule: { interval: 'weekly', delay_days: 30 } } },
  };
  const [state, detail] = classify(acct, null, null);
  assert.equal(state, 'slow');
  assert.match(detail, /delay_days=30/);
});

test('an ordinary daily schedule is quiet', () => {
  const acct = {
    payouts_enabled: true,
    settings: { payouts: { schedule: { interval: 'daily', delay_days: 2 } } },
  };
  assert.equal(classify(acct, null, null)[0], 'scheduled');
});
''',
"faq": [
 ("What does a manual payout schedule actually do?",
  "It stops Stripe from initiating payouts for that account. The balance still accrues and payouts are still permitted; they just have to be created by your code. If nothing creates them, nothing happens, and no error is raised because nothing was attempted."),
 ("Why did every new seller end up on manual?",
  "It is inherited. A platform-level payout schedule applies to accounts created after it is set, so one decision made during a hold-funds phase quietly becomes the configuration of every account that signs up afterwards."),
 ("How is this different from an account with no bank account attached?",
  "The symptom is identical and the cause is the opposite. With no external account there is nowhere to send the money; with a manual schedule there is a destination and no instruction. Reading settings.payouts.schedule.interval next to the external accounts list tells you which one you have."),
 ("What happens when I switch a stranded account to daily?",
  "The accumulated balance goes out, subject to the delay_days on the schedule. On an account with months of history and no payouts that can be a large single movement, so warn the seller first and expect it to attract a look from Stripe."),
 ("Should I flag a large delay_days as a problem?",
  "Flag it, do not alarm about it. A long delay is a working schedule and produces the same seller complaint, so it belongs in the same report. The fix is different: lower it toward the country minimum if it was inflated by accident, or explain it if it was not."),
],
"related": [
 ("/stripe/no-external-account-attached/", "A connected account has no external account to pay out to"),
 ("/stripe/payouts-failing-bank-rejection/", "Payouts fail with account_closed and nobody is watching"),
 ("/stripe/transfers-capability-inactive/", "The transfers capability is inactive so every transfer 400s"),
],
"citations": [CITE_PAYOUTS, CITE_PAYOUT_SCHEDULE, CITE_ACCOUNT_OBJ, CITE_BALANCE_OBJ],
},

{
"slug": "onboarding-abandoned-details-not-submitted",
"title": "Accounts stall at details_submitted false after link expiry",
"description": "A long tail of accounts that never opened. The onboarding link expires within minutes and is strictly single use, and nothing minted a new one.",
"h1": "accounts stall at details_submitted false after link expiry",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe details_submitted false", "stripe account link expired",
             "stripe onboarding abandoned", "account_links refresh_url",
             "stripe connect onboarding stuck"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Your database has four hundred <code>acct_</code> rows and two hundred and ninety of them have never done anything at all. Support has a handful of tickets that all say some version of the same thing: the Stripe page said something went wrong, or the emailed link did nothing when they clicked it. Nobody connected the tickets to the rows, because the rows do not look like failures. They look like people who changed their minds.",
"short_answer": """<p>Paginate <code>GET /v1/accounts?limit=100</code> and flag every account where <code>details_submitted</code> is <code>false</code> and <code>created</code> is more than about a week old. That combination is not a seller who is thinking it over; it is a seller whose onboarding session ended before it finished.</p>
<p>Then segment by <code>requirements.currently_due</code>. A long list means the form was never worked through at all; a short one means somebody got most of the way and lost the session near the end. The second group converts on a fresh link and the first group usually needs a different conversation.</p>
<p>The mechanism is the AccountLink itself: the <code>url</code> expires within minutes and is <strong>single use</strong>. A refresh, a back button, or a chat client fetching a preview of the link consumes it.</p>""",
"problem": """<p>These accounts are invisible precisely because they are not broken. Nothing is disabled, no requirement is past due, no capability is inactive, and no event fires. A monitor built around <code>charges_enabled</code> correctly ignores them &mdash; an account that never opened has not stopped working &mdash; so the cohort accumulates underneath every other check you have.</p>
<p>Meanwhile the seller's experience is worse than a plain error. They clicked a link and got a page saying something went wrong, with nothing to retry. Most of them do not open a ticket; they just do not come back, and the row sits in your database looking like a lead who went cold rather than a product failure you can fix.</p>""",
"why": """<p><strong>The link is single use and short lived.</strong> An AccountLink <code>url</code> is valid for a few minutes and can be used once. Refreshing the page, pressing back, or opening it a second time on a different device consumes it. The user did nothing wrong and there is nothing on the page telling them what happened.</p>
<p><strong>Sending it through a message consumes it before the human sees it.</strong> Email and chat clients fetch links to build previews and to scan them for safety. That fetch is a use. This is why the docs say to hand the link to an already authenticated user inside your own app rather than emailing or texting it &mdash; a link that arrives in an inbox may already be spent by the time it is clicked.</p>
<p><strong><code>refresh_url</code> is the part everyone stubs out.</strong> Stripe sends the user to <code>refresh_url</code> exactly when the link is no longer usable, and its whole job is to mint a new one and redirect. Implemented as a static "something went wrong" page &mdash; the natural placeholder &mdash; it converts a recoverable expiry into a dead end, and the account is left at <code>details_submitted: false</code> forever.</p>
<p><strong>Nobody re-onboards the cohort.</strong> Even after the handler is fixed, the accounts that stalled before the fix stay stalled. They need a deliberate pass with fresh links, and that pass never happens unless someone can produce the list.</p>""",
"steps": [
 {"h": "List the accounts that never submitted, with an age",
  "body": """<p><code>details_submitted == false</code> on its own includes everyone who signed up in the last hour. Pair it with <code>created</code> and a threshold of about seven days, so the report is people who are not coming back on their own rather than people mid-signup.</p>"""},
 {"h": "Split never-started from nearly-finished",
  "body": """<p>Use the length of <code>requirements.currently_due</code>. It is a triage heuristic, not a status: a short list means most of the form was completed and the session died near the end, which is the group most worth a fresh link and a personal email.</p>"""},
 {"h": "Look at what your refresh_url actually serves",
  "body": """<p>This is the fix. It has to call the account link endpoint again with the same parameters and 302 to the new <code>url</code>. If it renders an error page, every expiry in your funnel becomes a permanently lost account.</p>"""},
 {"h": "Stop sending links through messaging",
  "body": """<p>Generate the link on a request from an authenticated user and redirect them straight to it. If you need an out-of-band nudge, email a link to <em>your</em> app, which authenticates them and then mints a fresh AccountLink server-side.</p>"""},
 {"h": "Re-onboard the backlog once, deliberately",
  "body": """<p>The list this script prints is the work queue. Fixing the handler helps everyone who arrives from now on; the stalled cohort needs someone to walk them back in.</p>"""},
],
"verify": """<p>Re-run the script after the refresh handler ships and the backlog has been contacted. Accounts under the age threshold are expected; the aged cohort should shrink toward zero.</p>
<pre><code class="language-bash">python3 stripe_onboarding_stalled.py
# 412 account(s): 3 in flight, 0 abandoned</code></pre>""",
"code_intro": "One paginated GET and nothing else &mdash; a restricted key with read access to Connected accounts is enough. The classifier is pure and takes the account plus its age in days, so the seven-day threshold and the never-started split are testable rules rather than an inline comparison against the clock.",
"py_file": "stripe_onboarding_stalled.py",
"py": '''"""Report connected accounts that never finished onboarding.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_onboarding_stalled")

API = "https://api.stripe.com/v1"

STALE_DAYS = 7   # below this, the seller may simply still be signing up
NEARLY_DONE = 3  # few enough fields left that the session probably died near the end


def classify(account, age_days, stale_days=STALE_DAYS):
    """Sort one connected account by how far its onboarding got. Pure, so the age
    threshold and the never-started split can be tested without a clock.

    `age_days` is the account's age in days, or None when `created` is missing.
    The length of currently_due is a triage heuristic and nothing more: Stripe
    does not publish a "how far through the form" field, and a short list is the
    closest honest proxy for a session that ended near the end.

    Returns (state, detail).
    """
    reqs = account.get("requirements") or {}
    due = [f for f in (reqs.get("currently_due") or []) if f]

    if account.get("details_submitted"):
        return ("submitted", "details_submitted is true: onboarding completed")

    if age_days is None:
        return ("unknown", "details_submitted is false and there is no created "
                           "timestamp to age it against")

    if age_days < stale_days:
        return ("in-flight",
                "%.1f days old and not submitted: may still be signing up, so do "
                "not chase it yet" % age_days)

    if not due:
        return ("unknown",
                "%.0f days old, not submitted, and nothing is currently due: no "
                "capability has been requested, so Stripe is not asking for "
                "anything" % age_days)

    if len(due) <= NEARLY_DONE:
        return ("abandoned-late",
                "%.0f days old with %d field(s) left (%s): got most of the way, "
                "then the session ended. Worth a fresh link and an email"
                % (age_days, len(due), ", ".join(due[:3])))

    return ("abandoned-cold",
            "%.0f days old with %d field(s) still due: the form was never worked "
            "through" % (age_days, len(due)))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
    """Yield connected accounts, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            yield acct
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    ap.add_argument("--stale-days", type=float, default=STALE_DAYS,
                    help="an unsubmitted account older than this is abandoned")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    counts = {}
    scanned = 0
    for acct in accounts(s, args.max_accounts):
        scanned += 1
        created = acct.get("created")
        age = None if created is None else (now - created) / 86400.0
        state, detail = classify(acct, age, args.stale_days)
        counts[state] = counts.get(state, 0) + 1
        if state in ("submitted", "in-flight"):
            continue
        log.warning("%s  %-15s %s", acct.get("id", "acct_?"), state, detail)

    late = counts.get("abandoned-late", 0)
    cold = counts.get("abandoned-cold", 0)

    log.info("%d account(s): %d in flight, %d abandoned",
             scanned, counts.get("in-flight", 0), late + cold)

    if late or cold:
        log.warning("  repair, in this order:")
        log.warning("  1. make refresh_url mint a new link and 302 to it. Stripe "
                    "sends the user there precisely when the old one is spent:")
        log.warning("  POST %s/account_links  account, refresh_url, return_url, "
                    "type=account_onboarding", API)
        log.warning("  2. never email or SMS the returned url. It is single use, "
                    "and a client fetching a preview of it uses it.")
        log.warning("  3. re-onboard the %d account(s) above with fresh links, "
                    "starting with the %d that nearly finished.", late + cold, late)
    return 1 if (late or cold) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-onboarding-stalled.mjs",
"js": '''/**
 * Report connected accounts that never finished onboarding.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const STALE_DAYS = 7;  // below this, the seller may still be signing up
const NEARLY_DONE = 3;        // few enough left that the session died near the end

/**
 * Sort one connected account by how far its onboarding got. Pure, so the age
 * threshold and the never-started split can be tested without a clock.
 * `ageDays` is null when the account has no created timestamp.
 * Returns [state, detail].
 */
export function classify(account, ageDays, staleDays = STALE_DAYS) {
  const reqs = account.requirements ?? {};
  const due = (reqs.currently_due ?? []).filter(Boolean);

  if (account.details_submitted) {
    return ['submitted', 'details_submitted is true: onboarding completed'];
  }

  if (ageDays === null || ageDays === undefined) {
    return ['unknown',
      'details_submitted is false and there is no created timestamp to age it against'];
  }

  if (ageDays < staleDays) {
    return ['in-flight',
      `${ageDays.toFixed(1)} days old and not submitted: may still be signing ` +
      'up, so do not chase it yet'];
  }

  if (!due.length) {
    return ['unknown',
      `${ageDays.toFixed(0)} days old, not submitted, and nothing is currently ` +
      'due: no capability has been requested, so Stripe is not asking for anything'];
  }

  if (due.length <= NEARLY_DONE) {
    return ['abandoned-late',
      `${ageDays.toFixed(0)} days old with ${due.length} field(s) left ` +
      `(${due.slice(0, 3).join(', ')}): got most of the way, then the session ` +
      'ended. Worth a fresh link and an email'];
  }

  return ['abandoned-cold',
    `${ageDays.toFixed(0)} days old with ${due.length} field(s) still due: the ` +
    'form was never worked through'];
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

export async function* accounts(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/accounts', params);
    const data = page.data ?? [];
    for (const acct of data) {
      yield acct;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
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
  const counts = {};
  let scanned = 0;
  for await (const acct of accounts(key)) {
    scanned += 1;
    const age = acct.created === undefined || acct.created === null
      ? null : (now - acct.created) / 86400;
    const [state, detail] = classify(acct, age);
    counts[state] = (counts[state] ?? 0) + 1;
    if (state === 'submitted' || state === 'in-flight') continue;
    console.warn(`${acct.id ?? 'acct_?'}  ${state.padEnd(15)} ${detail}`);
  }

  const late = counts['abandoned-late'] ?? 0;
  const cold = counts['abandoned-cold'] ?? 0;

  console.log(`${scanned} account(s): ${counts['in-flight'] ?? 0} in flight, ` +
              `${late + cold} abandoned`);

  if (late || cold) {
    console.warn('  repair, in this order:');
    console.warn('  1. make refresh_url mint a new link and 302 to it. Stripe ' +
                 'sends the user there precisely when the old one is spent:');
    console.warn(`  POST ${API}/account_links  account, refresh_url, return_url, ` +
                 'type=account_onboarding');
    console.warn('  2. never email or SMS the returned url. It is single use, and ' +
                 'a client fetching a preview of it uses it.');
    console.warn(`  3. re-onboard the ${late + cold} account(s) above with fresh ` +
                 `links, starting with the ${late} that nearly finished.`);
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the test file does
// not run main(), fail on the missing key and fail the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The threshold is the whole check, so the threshold is what the tests pin. A day-old unsubmitted account is a normal signup and reporting it trains everyone to ignore the report; a forty-day-old one with two fields left is a person who tried and lost the session. The tests also cover the odd case where nothing is due at all, because that one is a different bug wearing the same symptom.",
"test_py_file": "test_stripe_onboarding_stalled.py",
"test_py": '''from stripe_onboarding_stalled import classify


def acct(submitted=False, due=("individual.dob.day", "individual.address.line1",
                               "business_profile.url", "external_account")):
    return {"details_submitted": submitted,
            "requirements": {"currently_due": list(due)}}


def test_a_submitted_account_is_finished():
    assert classify(acct(submitted=True), 400.0)[0] == "submitted"


def test_a_fresh_signup_is_not_chased():
    state, detail = classify(acct(), 1.5)
    assert state == "in-flight"
    assert "do not chase it yet" in detail


def test_seven_days_is_the_boundary():
    assert classify(acct(), 6.9)[0] == "in-flight"
    assert classify(acct(), 7.0)[0] == "abandoned-cold"


def test_a_short_remaining_list_means_they_nearly_finished():
    state, detail = classify(acct(due=("external_account",)), 40.0)
    assert state == "abandoned-late"
    assert "external_account" in detail


def test_unsubmitted_with_nothing_due_is_a_different_bug():
    # No capability requested, so Stripe is not asking for anything and no
    # onboarding link will collect anything either.
    state, detail = classify(acct(due=()), 40.0)
    assert state == "unknown"
    assert "no capability has been requested" in detail
''',
"test_js_file": "stripe-onboarding-stalled.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-onboarding-stalled.mjs';

const acct = (submitted = false, due = [
  'individual.dob.day', 'individual.address.line1',
  'business_profile.url', 'external_account',
]) => ({ details_submitted: submitted, requirements: { currently_due: due } });

test('a submitted account is finished', () => {
  assert.equal(classify(acct(true), 400.0)[0], 'submitted');
});

test('a fresh signup is not chased', () => {
  const [state, detail] = classify(acct(), 1.5);
  assert.equal(state, 'in-flight');
  assert.match(detail, /do not chase it yet/);
});

test('seven days is the boundary', () => {
  assert.equal(classify(acct(), 6.9)[0], 'in-flight');
  assert.equal(classify(acct(), 7.0)[0], 'abandoned-cold');
});

test('a short remaining list means they nearly finished', () => {
  const [state, detail] = classify(acct(false, ['external_account']), 40.0);
  assert.equal(state, 'abandoned-late');
  assert.match(detail, /external_account/);
});

test('unsubmitted with nothing due is a different bug', () => {
  const [state, detail] = classify(acct(false, []), 40.0);
  assert.equal(state, 'unknown');
  assert.match(detail, /no capability has been requested/);
});
''',
"faq": [
 ("How long is an account link valid?",
  "A few minutes, and it can be used once. That is short by design: the url authenticates the session, so a link that lived for a day would be a credential sitting in an inbox. The consequence is that anything which delays or duplicates the click breaks it."),
 ("Why did the link stop working before the user clicked it?",
  "Something fetched it first. Email and chat clients request links to build previews and to scan them, and that request consumes the single use. This is why the link should be handed to an already authenticated user inside your own app rather than sent as a message."),
 ("What should refresh_url do?",
  "Create a new account link with the same parameters and redirect to it. Stripe sends the user there exactly when the old link is no longer usable, so it is the recovery path, not an error page. Serving a static message there turns every expiry into a lost account."),
 ("Why not just alert on charges_enabled instead?",
  "Because these accounts have not broken. An account that never opened correctly reports charges_enabled false with no disabled_reason, and any monitor worth having filters it out to avoid paging on signups. This cohort needs its own list, keyed on details_submitted and age."),
 ("What does an unsubmitted account with nothing currently due mean?",
  "That no capability has been requested for it, so Stripe has nothing to ask for. An onboarding link will collect nothing because there is nothing outstanding. Request the capabilities the account needs first, then send a link."),
],
"related": [
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
 ("/stripe/verification-errors-unread/", "requirements.errors explains the rejected document"),
 ("/stripe/no-external-account-attached/", "A connected account has no external account to pay out to"),
],
"citations": [CITE_HOSTED_ONBOARDING, CITE_ACCOUNT_LINK_OBJ, CITE_ACCOUNT_OBJ, CITE_VERIFICATION],
},

{
"slug": "verification-errors-unread",
"title": "requirements.errors explains the rejected document",
"description": "A user uploads their passport four times and your UI says pending. The code saying why the last one was rejected is already on the account object.",
"h1": "requirements.errors explains the rejected document",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe requirements.errors", "verification_document_failed_greyscale",
             "stripe verification failed connect", "verification_failed_keyed_identity",
             "stripe identity document rejected"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A seller has uploaded the same photo of their passport four times over two weeks. Your onboarding UI has said <em>verification pending</em> every time, because that is the only string it knows. Stripe has been returning the specific reason since the first attempt: the scan is greyscale. Nobody has ever read the field it is in, so the seller keeps sending the file that cannot pass.",
"short_answer": """<p>Read <code>requirements.errors</code> on the account. It is an array of <code>{code, reason, requirement}</code> objects saying exactly why a submitted piece of information was rejected &mdash; <code>verification_document_failed_greyscale</code>, <code>verification_document_not_readable</code>, <code>verification_document_expired</code>, <code>verification_document_missing_back</code>, <code>verification_failed_keyed_identity</code>, <code>invalid_street_address</code>, <code>invalid_tax_id_format</code>, and the <code>invalid_url_website_*</code> family.</p>
<p>Look in all four places it appears, because the account-level array is not the whole story: <code>future_requirements.errors</code> on the account, <code>requirements.errors</code> on each object under <code>GET /v1/accounts/{id}/persons</code>, and again on each entry from <code>GET /v1/accounts/{id}/capabilities</code>.</p>
<p>Then map each code to an instruction a human can act on, and make sure the re-submission is a <strong>different file</strong>. Re-uploading the identical document fails automatically, which is what turns this into a loop rather than a delay.</p>""",
"problem": """<p>The account is not disabled and no requirement has gone past due, so every check you have says this account is progressing normally. It is progressing nowhere. The field is in <code>currently_due</code>, the seller keeps submitting it, and Stripe keeps rejecting it for a reason that is sitting in the API response your onboarding page already fetched and discarded.</p>
<p>What makes it a loop rather than a delay is the duplicate rule: submitting the same file again fails on its own, without a fresh review. So the seller's most natural response &mdash; try again &mdash; is guaranteed to fail, and each cycle costs a day or two and some more goodwill. Support sees "verification is slow" tickets and has nothing to tell them, because support is reading the same generic status the seller is.</p>""",
"why": """<p><strong>The error is on the object, not in an exception.</strong> Nothing throws. Your integration submitted the document successfully, got a 200, and the rejection arrives later as an entry in an array on the account. Code written around request failures never looks at it.</p>
<p><strong>"Pending" is the default thing to render.</strong> A field in <code>currently_due</code> with no message is naturally displayed as awaiting review, and that display is correct right up until it is catastrophically wrong. There is no signal to change it unless <code>requirements.errors</code> is read.</p>
<p><strong>The codes have specific, different remedies.</strong> <code>verification_document_failed_greyscale</code> needs a colour scan of the same passport. <code>verification_failed_keyed_identity</code> needs the <em>typed</em> name or date of birth corrected, not a new file at all. <code>invalid_url_website_incomplete</code> needs a change to the website, then the URL flipped to another value and back to force re-verification. Showing one generic "please try again" for the set guarantees most people do the wrong thing.</p>
<p><strong>Errors hide one level down.</strong> On a company account, KYC lives on Person objects and the account-level array can be empty while a director's is not. Reading only the account is how a team concludes there is no error to show while the seller is staring at a rejection.</p>""",
"steps": [
 {"h": "Read requirements.errors, in all four places",
  "body": """<p>Account <code>requirements.errors</code>, account <code>future_requirements.errors</code>, every Person's <code>requirements.errors</code>, and every capability's. An empty array at the top means nothing about the ones underneath.</p>"""},
 {"h": "Map every code to one specific instruction",
  "body": """<p>Not a category, an instruction. "The scan was in black and white, we need it in colour" is actionable; "document verification failed" produces another identical upload. Keep the mapping in code so an unrecognised code is visible rather than swallowed.</p>"""},
 {"h": "Surface the reason string as well as your own copy",
  "body": """<p><code>reason</code> is human readable and written to be shown. Your mapped instruction tells the seller what to do; the reason tells them what happened, and having both cuts the support conversation to nothing.</p>"""},
 {"h": "Force a genuinely different submission",
  "body": """<p>The same file re-uploaded fails automatically. If the code is a document one, the UI has to make it clear that a new capture is required: colour, in focus, uncropped, under the size limits, and not a PDF where an image is required.</p>"""},
 {"h": "Handle keyed identity and website errors as field edits",
  "body": """<p>These two are the common ones that no document will ever fix. Keyed identity means the typed fields disagree with the document; the website family means <code>business_profile[url]</code> is unreachable, incomplete, or missing the business details Stripe looks for.</p>"""},
],
"verify": """<p>Re-run the script. Every account should report clear, and any code the script cannot map should show up as unmapped rather than disappearing.</p>
<pre><code class="language-bash">python3 stripe_verification_errors.py
# 412 account(s): 0 with errors, 0 unmapped codes</code></pre>""",
"code_intro": "One paginated GET, plus two small GETs per account when <code>--persons</code> is set &mdash; a restricted key with read access to Connected accounts is enough. The mapping from code to instruction is a pure function over the errors array, which is the part worth testing: an unrecognised code has to come out as <em>unmapped</em> rather than being quietly treated as clear, because Stripe adds codes and this table will go stale.",
"py_file": "stripe_verification_errors.py",
"py": '''"""Report unread requirements.errors on connected accounts, with the fix for each.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_verification_errors")

API = "https://api.stripe.com/v1"

# A new file is required. The same one re-uploaded fails automatically, so the
# instruction has to say what is different about the next capture.
DOCUMENT_CODES = {
    "verification_document_failed_greyscale":
        "the upload was greyscale: a colour scan or photo of the same document",
    "verification_document_not_readable":
        "the image could not be read: re-capture it in focus and uncropped",
    "verification_document_expired":
        "the document is out of date: a current one, not a better scan",
    "verification_document_missing_back":
        "only one side was submitted: the back of the same document",
    "verification_document_failed_other":
        "rejected without a specific cause: a different capture, colour, under "
        "the size limits, and an image rather than a PDF for identity documents",
}

# A new file will never fix these. The typed fields are what disagree.
IDENTITY_CODES = {
    "verification_failed_keyed_identity":
        "the typed name or date of birth does not match the document: correct "
        "the fields, not the file",
}

# Ordinary field edits on the account or person.
FIELD_CODES = {
    "information_missing":
        "a required field was left out: read the requirement and supply it",
    "verification_missing_owners":
        "beneficial owners are missing: add the Person objects for them",
    "invalid_street_address":
        "the address could not be validated: check it against the postal service "
        "format for the country",
    "invalid_tax_id_format":
        "the tax id is not in the format for that country",
}

# The whole invalid_url_website_* family. Matched by prefix because it is long
# and Stripe keeps adding to it.
WEBSITE_PREFIX = "invalid_url_website"

GROUPS = (("document", DOCUMENT_CODES),
          ("identity", IDENTITY_CODES),
          ("field", FIELD_CODES))


def classify(errors):
    """Turn a requirements.errors array into one state and one instruction.

    Pure, so the code table can be tested without a network. Groups are checked
    in order of how blocking they are: a rejected document stops verification
    dead, a keyed identity mismatch is a field edit, a website error is often the
    last thing left. An unrecognised code returns `unmapped` rather than `clear`,
    because Stripe adds codes and a table that silently swallows new ones is
    worse than no table.

    Returns (state, detail).
    """
    items = [e for e in (errors or []) if isinstance(e, dict) and e.get("code")]
    if not items:
        return ("clear", "requirements.errors is empty")

    for state, table in GROUPS:
        for e in items:
            if e["code"] in table:
                return (state, "%s on %s: %s"
                        % (e["code"], e.get("requirement") or "an unnamed requirement",
                           table[e["code"]]))

    for e in items:
        if str(e["code"]).startswith(WEBSITE_PREFIX):
            return ("website",
                    "%s on %s: fix the site itself, then set business_profile[url] "
                    "to another value and back to force re-verification"
                    % (e["code"], e.get("requirement") or "business_profile.url"))

    e = items[0]
    return ("unmapped", "%s on %s: %s"
            % (e["code"], e.get("requirement") or "an unnamed requirement",
               e.get("reason") or "no reason string returned"))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
    """Yield connected accounts, paginating until Stripe stops or the cap is hit."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/accounts", **params)
        data = page.get("data", [])
        for acct in data:
            yield acct
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def error_sources(session, account, deep):
    """Yield (where, errors) for every place a verification error can hide."""
    reqs = account.get("requirements") or {}
    future = account.get("future_requirements") or {}
    yield ("account", reqs.get("errors") or [])
    yield ("future", future.get("errors") or [])
    if not deep:
        return
    acct_id = account.get("id", "")
    persons = get(session, "/accounts/%s/persons" % acct_id, limit=100)
    for p in persons.get("data") or []:
        preqs = p.get("requirements") or {}
        yield ("person %s" % p.get("id", "person_?"), preqs.get("errors") or [])
    caps = get(session, "/accounts/%s/capabilities" % acct_id)
    for c in caps.get("data") or []:
        creqs = c.get("requirements") or {}
        yield ("capability %s" % c.get("id", "?"), creqs.get("errors") or [])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    ap.add_argument("--persons", action="store_true",
                    help="also read persons and capabilities, two extra GETs each")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    with_errors = 0
    unmapped = 0
    scanned = 0
    for acct in accounts(s, args.max_accounts):
        scanned += 1
        hits = 0
        for where, errors in error_sources(s, acct, args.persons):
            state, detail = classify(errors)
            if state == "clear":
                continue
            hits += 1
            if state == "unmapped":
                unmapped += 1
            log.warning("%s  %-9s %-12s %s",
                        acct.get("id", "acct_?"), state, where, detail)
        if hits:
            with_errors += 1

    log.info("%d account(s): %d with errors, %d unmapped code(s)",
             scanned, with_errors, unmapped)

    if with_errors:
        log.warning("  repair: show the mapped instruction and the reason string "
                    "in your onboarding UI, then require a genuinely different "
                    "submission. The same file re-uploaded fails on its own.")
        log.warning("  documents: upload to https://files.stripe.com/v1/files with "
                    "purpose=identity_document, then attach the file id to the "
                    "person's verification[document][front]")
        log.warning("  fields: POST %s/accounts/{id} with the corrected values", API)
    if unmapped:
        log.warning("  add the unmapped code(s) above to the table in this script. "
                    "Stripe adds codes; a stale table shows a seller nothing.")
    if not args.persons:
        log.info("  re-run with --persons: on a company account the account-level "
                 "array is often empty while a director's is not")
    return 1 if with_errors else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-verification-errors.mjs",
"js": '''/**
 * Report unread requirements.errors on connected accounts, with the fix for each.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// A new file is required. The same one re-uploaded fails automatically.
const DOCUMENT_CODES = {
  verification_document_failed_greyscale:
    'the upload was greyscale: a colour scan or photo of the same document',
  verification_document_not_readable:
    'the image could not be read: re-capture it in focus and uncropped',
  verification_document_expired:
    'the document is out of date: a current one, not a better scan',
  verification_document_missing_back:
    'only one side was submitted: the back of the same document',
  verification_document_failed_other:
    'rejected without a specific cause: a different capture, colour, under the ' +
    'size limits, and an image rather than a PDF for identity documents',
};

// A new file will never fix this. The typed fields are what disagree.
const IDENTITY_CODES = {
  verification_failed_keyed_identity:
    'the typed name or date of birth does not match the document: correct the ' +
    'fields, not the file',
};

// Ordinary field edits on the account or person.
const FIELD_CODES = {
  information_missing:
    'a required field was left out: read the requirement and supply it',
  verification_missing_owners:
    'beneficial owners are missing: add the Person objects for them',
  invalid_street_address:
    'the address could not be validated: check it against the postal service ' +
    'format for the country',
  invalid_tax_id_format:
    'the tax id is not in the format for that country',
};

// The whole invalid_url_website_* family, matched by prefix.
const WEBSITE_PREFIX = 'invalid_url_website';

const GROUPS = [
  ['document', DOCUMENT_CODES],
  ['identity', IDENTITY_CODES],
  ['field', FIELD_CODES],
];

/**
 * Turn a requirements.errors array into one state and one instruction. Pure, so
 * the code table can be tested without a network. An unrecognised code returns
 * `unmapped` rather than `clear`: Stripe adds codes, and a table that silently
 * swallows new ones is worse than no table.
 * Returns [state, detail].
 */
export function classify(errors) {
  const items = (errors ?? []).filter((e) => e && typeof e === 'object' && e.code);
  if (!items.length) return ['clear', 'requirements.errors is empty'];

  for (const [state, table] of GROUPS) {
    for (const e of items) {
      if (e.code in table) {
        return [state,
          `${e.code} on ${e.requirement || 'an unnamed requirement'}: ${table[e.code]}`];
      }
    }
  }

  for (const e of items) {
    if (String(e.code).startsWith(WEBSITE_PREFIX)) {
      return ['website',
        `${e.code} on ${e.requirement || 'business_profile.url'}: fix the site ` +
        'itself, then set business_profile[url] to another value and back to ' +
        'force re-verification'];
    }
  }

  const e = items[0];
  return ['unmapped',
    `${e.code} on ${e.requirement || 'an unnamed requirement'}: ` +
    `${e.reason || 'no reason string returned'}`];
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

export async function* accounts(key, cap = 5000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/accounts', params);
    const data = page.data ?? [];
    for (const acct of data) {
      yield acct;
      seen += 1;
      if (seen >= cap) return;
    }
    if (data.length === 0 || !page.has_more) return;
    params.starting_after = data[data.length - 1].id;
  }
}

async function errorSources(key, account, deep) {
  const out = [
    ['account', account.requirements?.errors ?? []],
    ['future', account.future_requirements?.errors ?? []],
  ];
  if (!deep) return out;
  const persons = await get(key, `/accounts/${account.id}/persons`, { limit: 100 });
  for (const p of persons.data ?? []) {
    out.push([`person ${p.id ?? 'person_?'}`, p.requirements?.errors ?? []]);
  }
  const caps = await get(key, `/accounts/${account.id}/capabilities`);
  for (const c of caps.data ?? []) {
    out.push([`capability ${c.id ?? '?'}`, c.requirements?.errors ?? []]);
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
  const deep = process.argv.includes('--persons');

  let withErrors = 0;
  let unmapped = 0;
  let scanned = 0;
  for await (const acct of accounts(key)) {
    scanned += 1;
    let hits = 0;
    for (const [where, errors] of await errorSources(key, acct, deep)) {
      const [state, detail] = classify(errors);
      if (state === 'clear') continue;
      hits += 1;
      if (state === 'unmapped') unmapped += 1;
      console.warn(`${acct.id ?? 'acct_?'}  ${state.padEnd(9)} ${where.padEnd(12)} ${detail}`);
    }
    if (hits) withErrors += 1;
  }

  console.log(`${scanned} account(s): ${withErrors} with errors, ` +
              `${unmapped} unmapped code(s)`);

  if (withErrors) {
    console.warn('  repair: show the mapped instruction and the reason string in ' +
                 'your onboarding UI, then require a genuinely different ' +
                 'submission. The same file re-uploaded fails on its own.');
    console.warn('  documents: upload to https://files.stripe.com/v1/files with ' +
                 "purpose=identity_document, then attach the file id to the " +
                 "person's verification[document][front]");
    console.warn(`  fields: POST ${API}/accounts/{id} with the corrected values`);
    process.exitCode = 1;
  }
  if (unmapped) {
    console.warn('  add the unmapped code(s) above to the table in this script. ' +
                 'Stripe adds codes; a stale table shows a seller nothing.');
  }
}

// Only run when invoked directly, so importing this module in the test file does
// not run main(), fail on the missing key and fail the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The table is the product here, so the tests check that each family produces the instruction that actually resolves it &mdash; and, more importantly, that a code the table has never seen comes out as <em>unmapped</em>. Stripe adds error codes; a lookup that returns a cheerful <em>clear</em> for anything it does not recognise would put this note's exact bug back into the script written to find it.",
"test_py_file": "test_stripe_verification_errors.py",
"test_py": '''from stripe_verification_errors import classify


def test_no_errors_is_clear():
    assert classify([])[0] == "clear"
    assert classify(None)[0] == "clear"


def test_greyscale_asks_for_colour_not_for_patience():
    state, detail = classify([{
        "code": "verification_document_failed_greyscale",
        "reason": "The document could not be verified because it is greyscale.",
        "requirement": "individual.verification.document",
    }])
    assert state == "document"
    assert "colour" in detail


def test_keyed_identity_is_a_field_edit_not_a_new_file():
    state, detail = classify([{"code": "verification_failed_keyed_identity",
                               "requirement": "individual.first_name"}])
    assert state == "identity"
    assert "not the file" in detail


def test_a_field_code_names_its_requirement():
    state, detail = classify([{"code": "invalid_tax_id_format",
                               "requirement": "company.tax_id"}])
    assert state == "field"
    assert "company.tax_id" in detail


def test_the_website_family_is_matched_by_prefix():
    # Stripe keeps adding to invalid_url_website_*, so this must not be a list.
    state, detail = classify([{"code": "invalid_url_website_incomplete_cancellation_policy",
                               "requirement": "business_profile.url"}])
    assert state == "website"
    assert "force re-verification" in detail


def test_an_unknown_code_is_unmapped_and_keeps_its_reason():
    state, detail = classify([{"code": "verification_something_brand_new",
                               "reason": "A reason only Stripe knows yet.",
                               "requirement": "individual.id_number"}])
    assert state == "unmapped"
    assert "A reason only Stripe knows yet." in detail


def test_a_blocking_document_error_wins_over_a_website_one():
    state, _ = classify([
        {"code": "invalid_url_website_other", "requirement": "business_profile.url"},
        {"code": "verification_document_expired",
         "requirement": "individual.verification.document"},
    ])
    assert state == "document"
''',
"test_js_file": "stripe-verification-errors.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-verification-errors.mjs';

test('no errors is clear', () => {
  assert.equal(classify([])[0], 'clear');
  assert.equal(classify(null)[0], 'clear');
});

test('greyscale asks for colour, not for patience', () => {
  const [state, detail] = classify([{
    code: 'verification_document_failed_greyscale',
    reason: 'The document could not be verified because it is greyscale.',
    requirement: 'individual.verification.document',
  }]);
  assert.equal(state, 'document');
  assert.match(detail, /colour/);
});

test('keyed identity is a field edit, not a new file', () => {
  const [state, detail] = classify([{
    code: 'verification_failed_keyed_identity',
    requirement: 'individual.first_name',
  }]);
  assert.equal(state, 'identity');
  assert.match(detail, /not the file/);
});

test('a field code names its requirement', () => {
  const [state, detail] = classify([{
    code: 'invalid_tax_id_format', requirement: 'company.tax_id',
  }]);
  assert.equal(state, 'field');
  assert.match(detail, /company\\.tax_id/);
});

test('the website family is matched by prefix', () => {
  const [state, detail] = classify([{
    code: 'invalid_url_website_incomplete_cancellation_policy',
    requirement: 'business_profile.url',
  }]);
  assert.equal(state, 'website');
  assert.match(detail, /force re-verification/);
});

test('an unknown code is unmapped and keeps its reason', () => {
  const [state, detail] = classify([{
    code: 'verification_something_brand_new',
    reason: 'A reason only Stripe knows yet.',
    requirement: 'individual.id_number',
  }]);
  assert.equal(state, 'unmapped');
  assert.match(detail, /A reason only Stripe knows yet\\./);
});

test('a blocking document error wins over a website one', () => {
  const [state] = classify([
    { code: 'invalid_url_website_other', requirement: 'business_profile.url' },
    { code: 'verification_document_expired', requirement: 'individual.verification.document' },
  ]);
  assert.equal(state, 'document');
});
''',
"faq": [
 ("Where does requirements.errors appear?",
  "In four places, and they do not agree with each other. On the account's requirements hash, on its future_requirements hash, on every Person object under GET /v1/accounts/{id}/persons, and on every entry from GET /v1/accounts/{id}/capabilities. On a company account the account-level array is frequently empty while a director's is not."),
 ("Why does re-uploading the same document keep failing?",
  "Because a duplicate submission fails on its own. Stripe will not re-review a file it has already rejected, so the seller's instinctive response guarantees another failure. The instruction has to make clear what must be different about the next capture: colour, in focus, current, both sides where required."),
 ("What is verification_failed_keyed_identity?",
  "The name or date of birth typed into the form does not match the document that was uploaded. No new photo fixes it. Correct the fields on the account or the person, which is why mapping the code to an instruction matters more here than anywhere else in the table."),
 ("How do I fix an invalid_url_website_* error?",
  "Fix the website first: reachable, describing the business, and carrying whatever the specific code names, such as a returns or cancellation policy. Then set business_profile[url] to a different value and back, because otherwise nothing has changed on the object and Stripe has no reason to look again."),
 ("Should I show the reason string to the seller?",
  "Show both. The reason string is human readable and written to be displayed, and your mapped instruction says what to do about it. Together they end the ticket; either one alone tends to produce another identical upload."),
],
"related": [
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/onboarding-abandoned-details-not-submitted/", "Accounts stall at details_submitted false after link expiry"),
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
],
"citations": [CITE_VERIFICATION, CITE_ACCOUNT_OBJ, CITE_PERSON_OBJ, CITE_CAPABILITY_OBJ],
},

]
