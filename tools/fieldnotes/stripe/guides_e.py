#!/usr/bin/env python3
"""/stripe/ field notes — batch E: Connect and payouts.

Four problems that share one shape: a connected account, or the bank account
behind it, stopped working, and the platform found out from the seller rather
than from its own monitoring. Every script here is read only. They hold a
credential to a live payments account, so none of them writes: they read, they
say exactly what is wrong, and they print the repair for a human to run.
"""

CITE_ACCOUNT_OBJECT = ("The Account object — Stripe API reference",
                       "https://docs.stripe.com/api/accounts/object")
CITE_ACCOUNT_LIST = ("List all connected accounts — Stripe API reference",
                     "https://docs.stripe.com/api/accounts/list")
CITE_VERIFICATION = ("Handling verification with the API — Stripe Docs",
                     "https://docs.stripe.com/connect/handling-api-verification")
CITE_CAPABILITIES = ("Account capabilities — Stripe Docs",
                     "https://docs.stripe.com/connect/account-capabilities")
CITE_CAPABILITY_OBJECT = ("The Capability object — Stripe API reference",
                          "https://docs.stripe.com/api/capabilities/object")
CITE_HOSTED_ONBOARDING = ("Hosted onboarding — Stripe Docs",
                          "https://docs.stripe.com/connect/hosted-onboarding")
CITE_REQUIRED_INFO = ("Required verification information — Stripe Docs",
                      "https://docs.stripe.com/connect/required-verification-information")
CITE_PAYOUT_OBJECT = ("The Payout object — Stripe API reference",
                      "https://docs.stripe.com/api/payouts/object")
CITE_PAYOUT_LIST = ("List all payouts — Stripe API reference",
                    "https://docs.stripe.com/api/payouts/list")
CITE_PAYOUTS = ("Payouts — Stripe Docs", "https://docs.stripe.com/payouts")
CITE_EXTERNAL_ACCOUNT = ("The bank account object — Stripe API reference",
                         "https://docs.stripe.com/api/external_account_bank_accounts/object")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

GUIDES = [

{
"slug": "connected-accounts-charges-disabled",
"title": "A connected account sits with charges_enabled false",
"description": "A seller's checkout stops working and the platform dashboard looks fine, because the account that broke is not the one you are looking at.",
"h1": "a connected account sits with charges_enabled false",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe charges_enabled false", "connect account disabled",
             "stripe disabled_reason", "connected account not accepting payments",
             "stripe account.updated"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A seller emails support to say their checkout has been broken for two weeks. Nobody on the platform side saw anything: no alert, no failed job, no error in the logs. The platform's own Stripe account is healthy, payments are flowing, the graphs are flat and normal. The account that stopped working is one of four hundred, and the only field that would have told you is one nobody was reading.",
"short_answer": """<p>Paginate <code>GET /v1/accounts?limit=100</code> and flag every account where <code>charges_enabled</code> is <code>false</code>. Then read <code>requirements.disabled_reason</code> on the same object, because that single string decides whether this is your problem or Stripe's.</p>
<p><code>requirements.past_due</code> and <code>requirements.pending_verification</code> mean fields are outstanding and an onboarding link fixes it. Anything in the <code>rejected.*</code> family, plus <code>listed</code> and <code>under_review</code>, cannot be cleared through the API at all &mdash; those are resolved from the Dashboard's Connected accounts page or not at all.</p>""",
"problem": """<p>The platform never sees this. That is the whole difficulty. Your application talks to your own Stripe account, your own account is fine, and a connected account that has had its card payments switched off produces no signal on your side unless you go and ask about it. There is no failing request in your logs because your code is not making requests for that seller; the seller's customers are, and they are seeing an error page on a checkout you do not own.</p>
<p>By the time it reaches you it arrives as a support ticket with two weeks of lost revenue attached, and the seller reasonably believes the platform broke their store. You then have to work out which of several hundred accounts are in the same state, which is when it becomes clear that nobody has ever run that query.</p>""",
"why": """<p><strong>Nothing pushes the state change to you.</strong> <code>charges_enabled</code> flips the moment a capability the account depends on goes inactive, and the only notification is the <code>account.updated</code> event. If the platform has no endpoint scoped to connected accounts &mdash; which is the default, since a normal endpoint only receives the platform's own events &mdash; that transition happens in silence.</p>
<p><strong>The account looks finished.</strong> <code>details_submitted</code> is <code>true</code>. The seller completed onboarding months ago and has been taking payments ever since. Nothing about the object says "unfinished", so a check written around onboarding completion passes cleanly while the account is dead.</p>
<p><strong>The reason matters more than the flag.</strong> Two accounts can both read <code>charges_enabled: false</code> and need completely different work: one needs an email with an onboarding link, the other needs a human to open the Dashboard because Stripe has rejected it and the API has no way to argue. A monitor that reports only the boolean generates a list that cannot be acted on without opening every account by hand.</p>
<p><strong>Capabilities and the top-level flag are not the same thing.</strong> <code>charges_enabled</code> is a summary. <code>capabilities.card_payments</code> is the specific thing that broke, and Stripe couples <code>card_payments</code> and <code>transfers</code> so that either one being inactive disables both. Chasing the summary flag without reading the capability leaves you fixing requirements that belong to a capability you were not looking at.</p>""",
"steps": [
 {"h": "List every connected account and read three fields, not one",
  "body": """<p><code>charges_enabled</code>, <code>details_submitted</code> and <code>requirements.disabled_reason</code>. The first says something is wrong, the second says whether onboarding ever finished, the third says who can fix it. Paginate with <code>starting_after</code>; a platform with four hundred sellers does not fit in one page and the broken ones are not usefully clustered.</p>"""},
 {"h": "Separate never-started from stopped-working",
  "body": """<p><code>details_submitted: false</code> with <code>charges_enabled: false</code> is an account that never opened for business. It is a sales problem, not an incident. Mixing those into the same alert as accounts that were live yesterday is how the alert gets ignored, because the never-started ones are always the majority.</p>"""},
 {"h": "Split the disabled reasons by who can act",
  "body": """<p><code>requirements.past_due</code>, <code>requirements.pending_verification</code> and <code>action_required.requested_capabilities</code> are yours: collect fields, send a link, wait. <code>rejected.fraud</code>, <code>rejected.listed</code>, <code>rejected.terms_of_service</code>, <code>rejected.other</code>, <code>listed</code> and <code>under_review</code> are not. Sending an onboarding link to a rejected account produces a completed form and no change in status.</p>"""},
 {"h": "Read the specific capability before collecting anything",
  "body": """<p><code>GET /v1/accounts/{id}/capabilities</code> gives the per-capability requirement sets. Union <code>requirements.currently_due</code> across all of them rather than the one you happen to use, because of the <code>card_payments</code>/<code>transfers</code> coupling: satisfying one capability's list while the other stays inactive leaves both disabled and looks like the fix did not work.</p>"""},
 {"h": "Print the repair, then subscribe so it never gets this far again",
  "body": """<p>The repair is an account link for the fixable cases and a Dashboard visit for the rest. The permanent fix is an endpoint with <code>connect: true</code> subscribed to <code>account.updated</code>, so the next flip arrives as an event on the day it happens rather than as a ticket a fortnight later.</p>"""},
],
"verify": """<p>Re-run the script. Every live seller should classify as <code>live</code>, and anything left should be an account that has genuinely never onboarded.</p>
<pre><code class="language-bash">python3 stripe_connect_charges_disabled.py
# 412 account(s): 0 blocked, 0 rejected, 6 never onboarded</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/accounts</code> and nothing else &mdash; a restricted key with read access to Connected accounts is enough, and is what you should give it. The classification is a pure function of one account object, because the whole value of this check is the distinction between an account you can fix with an email and one that needs a human in the Dashboard, and that distinction is a list of strings that is easy to get subtly wrong.",
"py_file": "stripe_connect_charges_disabled.py",
"py": '''"""Report connected accounts that cannot take payments, and say who can fix each.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_connect_charges_disabled")

API = "https://api.stripe.com/v1"

# Reasons the API cannot clear. An onboarding link sent to one of these produces a
# completed form and no change in status, which reads as a broken link to the
# seller and as a fixed account to whoever sent it.
DASHBOARD_ONLY = ("listed", "under_review", "rejected")

# Stripe is holding the account while it checks something. There is no field to
# collect and nothing for anyone to do.
WAITING = ("requirements.pending_verification",)


def classify(account):
    """Sort one connected account. Pure, so the reason table can be tested.

    Takes an /v1/accounts object. Returns (state, detail). The states exist to
    split the work by who can do it: `blocked` is an email, `rejected` is a human
    in the Dashboard, `waiting` is nobody.
    """
    reqs = account.get("requirements") or {}
    reason = reqs.get("disabled_reason")
    due = [f for f in (reqs.get("currently_due") or []) if f]

    if account.get("charges_enabled"):
        return ("live", "charges_enabled, nothing to chase")

    if not account.get("details_submitted"):
        return ("never-onboarded",
                "details_submitted is false: this account never opened, so it has "
                "not broken. Do not page anyone about it.")

    if reason and (reason in DASHBOARD_ONLY or reason.split(".", 1)[0] == "rejected"):
        return ("rejected",
                "disabled_reason %s: the API cannot clear this. It is resolved from "
                "the Dashboard Connected accounts page, or not at all." % reason)

    if reason in WAITING:
        return ("waiting",
                "disabled_reason %s: Stripe is verifying what it already has. "
                "Collecting more fields does not speed it up." % reason)

    if due:
        return ("blocked",
                "%s, %d field(s) currently due: %s"
                % (reason or "no disabled_reason", len(due), ", ".join(due[:4])))

    if reason:
        return ("blocked",
                "%s with nothing in currently_due: read the per-capability "
                "requirements before collecting anything." % reason)

    return ("unknown",
            "charges_enabled is false with no disabled_reason and no currently_due")


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
    ap.add_argument("--quiet-never-onboarded", action="store_true",
                    help="do not list accounts that never finished onboarding")
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
        state, detail = classify(acct)
        counts[state] = counts.get(state, 0) + 1
        if state == "live":
            continue
        if state == "never-onboarded" and args.quiet_never_onboarded:
            continue
        log.warning("%s  %-16s %s", acct.get("id", "acct_?"), state, detail)

    blocked = counts.get("blocked", 0)
    rejected = counts.get("rejected", 0)
    unknown = counts.get("unknown", 0)

    log.info("%d account(s): %d blocked, %d rejected, %d never onboarded",
             scanned, blocked, rejected, counts.get("never-onboarded", 0))

    if blocked:
        log.warning("  repair: read the union of currently_due across every "
                    "capability first:")
        log.warning("  GET %s/accounts/{id}/capabilities", API)
        log.warning("  repair: create an account link for the seller, "
                    "type=account_onboarding, collection_options[fields]=currently_due")
    if rejected:
        log.warning("  repair: Dashboard, Connected accounts, open the account. "
                    "No API call clears a rejected.* or under_review reason.")
    if blocked or rejected or unknown:
        log.warning("  check: an endpoint with connect=true subscribed to "
                    "account.updated turns this into an event instead of a ticket")
    return 1 if (blocked or rejected or unknown) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-connect-charges-disabled.mjs",
"js": '''/**
 * Report connected accounts that cannot take payments, and say who can fix each.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Reasons the API cannot clear. An onboarding link sent to one of these produces
// a completed form and no change in status.
const DASHBOARD_ONLY = ['listed', 'under_review', 'rejected'];

// Stripe is holding the account while it checks something. Nothing to collect.
const WAITING = ['requirements.pending_verification'];

/**
 * Sort one connected account. Pure, so the reason table can be tested.
 * Returns [state, detail]. The states split the work by who can do it.
 */
export function classify(account) {
  const reqs = account.requirements ?? {};
  const reason = reqs.disabled_reason ?? null;
  const due = (reqs.currently_due ?? []).filter(Boolean);

  if (account.charges_enabled) return ['live', 'charges_enabled, nothing to chase'];

  if (!account.details_submitted) {
    return ['never-onboarded',
      'details_submitted is false: this account never opened, so it has not ' +
      'broken. Do not page anyone about it.'];
  }

  if (reason && (DASHBOARD_ONLY.includes(reason) || reason.split('.')[0] === 'rejected')) {
    return ['rejected',
      `disabled_reason ${reason}: the API cannot clear this. It is resolved from ` +
      'the Dashboard Connected accounts page, or not at all.'];
  }

  if (reason && WAITING.includes(reason)) {
    return ['waiting',
      `disabled_reason ${reason}: Stripe is verifying what it already has. ` +
      'Collecting more fields does not speed it up.'];
  }

  if (due.length) {
    return ['blocked',
      `${reason ?? 'no disabled_reason'}, ${due.length} field(s) currently due: ` +
      due.slice(0, 4).join(', ')];
  }

  if (reason) {
    return ['blocked',
      `${reason} with nothing in currently_due: read the per-capability ` +
      'requirements before collecting anything.'];
  }

  return ['unknown',
    'charges_enabled is false with no disabled_reason and no currently_due'];
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

  const counts = new Map();
  let scanned = 0;

  for await (const acct of accounts(key)) {
    scanned += 1;
    const [state, detail] = classify(acct);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'live') continue;
    console.warn(`${acct.id ?? 'acct_?'}  ${state.padEnd(16)} ${detail}`);
  }

  const blocked = counts.get('blocked') ?? 0;
  const rejected = counts.get('rejected') ?? 0;
  const unknown = counts.get('unknown') ?? 0;

  console.log(`${scanned} account(s): ${blocked} blocked, ${rejected} rejected, ` +
              `${counts.get('never-onboarded') ?? 0} never onboarded`);

  if (blocked) {
    console.warn('  repair: read the union of currently_due across every capability first:');
    console.warn(`  GET ${API}/accounts/{id}/capabilities`);
    console.warn('  repair: create an account link for the seller, ' +
                 'type=account_onboarding, collection_options[fields]=currently_due');
  }
  if (rejected) {
    console.warn('  repair: Dashboard, Connected accounts, open the account. ' +
                 'No API call clears a rejected.* or under_review reason.');
  }
  if (blocked || rejected || unknown) {
    console.warn('  check: an endpoint with connect=true subscribed to ' +
                 'account.updated turns this into an event instead of a ticket');
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
"test_intro": "The tests are about the reason table, because that is the part with real consequences. Classifying a rejected account as fixable sends a seller an onboarding link that cannot work, and classifying an account that never onboarded as an incident is how a monitor with four hundred accounts behind it gets muted in its first week.",
"test_py_file": "test_stripe_connect_charges_disabled.py",
"test_py": '''from stripe_connect_charges_disabled import classify


def test_enabled_account_is_live():
    state, _ = classify({"charges_enabled": True, "details_submitted": True})
    assert state == "live"


def test_never_onboarded_is_not_an_incident():
    state, detail = classify({"charges_enabled": False, "details_submitted": False})
    assert state == "never-onboarded"
    assert "never opened" in detail


def test_every_rejected_reason_is_dashboard_only():
    # rejected.* is an open family; matching the prefix rather than a fixed list
    # is the difference between a correct answer and one that ages badly.
    for reason in ("rejected.fraud", "rejected.listed", "rejected.terms_of_service",
                   "rejected.other", "listed", "under_review"):
        state, detail = classify({
            "charges_enabled": False, "details_submitted": True,
            "requirements": {"disabled_reason": reason,
                             "currently_due": ["company.tax_id"]},
        })
        assert state == "rejected", reason
        assert "cannot clear" in detail


def test_past_due_is_blocked_and_names_the_fields():
    state, detail = classify({
        "charges_enabled": False, "details_submitted": True,
        "requirements": {"disabled_reason": "requirements.past_due",
                         "currently_due": ["company.tax_id", "business_profile.url"]},
    })
    assert state == "blocked"
    assert "company.tax_id" in detail


def test_pending_verification_asks_nobody_for_anything():
    state, detail = classify({
        "charges_enabled": False, "details_submitted": True,
        "requirements": {"disabled_reason": "requirements.pending_verification",
                         "currently_due": []},
    })
    assert state == "waiting"
    assert "does not speed it up" in detail


def test_disabled_with_no_explanation_is_not_reported_as_healthy():
    state, _ = classify({"charges_enabled": False, "details_submitted": True,
                         "requirements": {}})
    assert state == "unknown"
''',
"test_js_file": "stripe-connect-charges-disabled.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-connect-charges-disabled.mjs';

test('enabled account is live', () => {
  assert.equal(classify({ charges_enabled: true, details_submitted: true })[0], 'live');
});

test('never onboarded is not an incident', () => {
  const [state, detail] = classify({ charges_enabled: false, details_submitted: false });
  assert.equal(state, 'never-onboarded');
  assert.match(detail, /never opened/);
});

test('every rejected reason is dashboard only', () => {
  // rejected.* is an open family; matching the prefix rather than a fixed list is
  // the difference between a correct answer and one that ages badly.
  for (const reason of ['rejected.fraud', 'rejected.listed', 'rejected.terms_of_service',
    'rejected.other', 'listed', 'under_review']) {
    const [state, detail] = classify({
      charges_enabled: false,
      details_submitted: true,
      requirements: { disabled_reason: reason, currently_due: ['company.tax_id'] },
    });
    assert.equal(state, 'rejected', reason);
    assert.match(detail, /cannot clear/);
  }
});

test('past due is blocked and names the fields', () => {
  const [state, detail] = classify({
    charges_enabled: false,
    details_submitted: true,
    requirements: {
      disabled_reason: 'requirements.past_due',
      currently_due: ['company.tax_id', 'business_profile.url'],
    },
  });
  assert.equal(state, 'blocked');
  assert.match(detail, /company\\.tax_id/);
});

test('pending verification asks nobody for anything', () => {
  const [state, detail] = classify({
    charges_enabled: false,
    details_submitted: true,
    requirements: {
      disabled_reason: 'requirements.pending_verification',
      currently_due: [],
    },
  });
  assert.equal(state, 'waiting');
  assert.match(detail, /does not speed it up/);
});

test('disabled with no explanation is not reported as healthy', () => {
  assert.equal(
    classify({ charges_enabled: false, details_submitted: true, requirements: {} })[0],
    'unknown');
});
''',
"faq": [
 ("What actually sets charges_enabled to false?",
  "A capability the account depends on going inactive. That happens when verification fields go unmet past their deadline, when Stripe opens a risk review, when Stripe rejects the account, or when the platform itself pauses it. The flag is a summary of capability state, not an independent switch, which is why the specific capability and its requirements are where the repair lives."),
 ("Why did nobody get an alert?",
  "Because a plain webhook endpoint only receives events for your own account. Events about connected accounts need an endpoint created with connect set to true, subscribed to account.updated. Platforms that never created one see nothing when a seller's account changes state, and there is no error to indicate the events were missed."),
 ("Can I fix a rejected account through the API?",
  "No. Every reason in the rejected family, plus listed and under_review, is resolved from the Dashboard's Connected accounts page or through Stripe support. Updating the account object or sending a fresh onboarding link changes nothing, and the seller will complete the form and come back asking why it did not work."),
 ("Should I check capabilities or charges_enabled?",
  "Both, in that order of authority. charges_enabled tells you an account is broken; capabilities.card_payments and its requirements tell you what to collect. Stripe couples card_payments and transfers so that either being inactive disables both, so union the currently_due lists across all capabilities rather than trusting the one you use."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Connected accounts is enough, and it is what this script should be given. It reads a list of accounts and prints a classification; it cannot onboard, update, or reject anything."),
],
"related": [
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/no-external-account-attached/", "A connected account has no external account to pay out to"),
 ("/stripe/missing-payout-failed/", "payout.failed is unsubscribed so broken bank details go unseen"),
],
"citations": [CITE_ACCOUNT_OBJECT, CITE_VERIFICATION, CITE_CAPABILITIES, CITE_ACCOUNT_LIST],
},

{
"slug": "requirements-past-due-disables-account",
"title": "requirements.past_due has already disabled the payouts",
"description": "A monitor that counts currently_due cannot tell a warning from a broken account, because past_due is a subset of the list it is counting.",
"h1": "requirements.past_due has already disabled the payouts",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe requirements past_due", "payouts_enabled false",
             "stripe currently_due deadline", "connect current_deadline",
             "stripe requirements disabled_reason"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "There is a monitor. It runs daily, it reads every connected account, and it alerts when <code>requirements.currently_due</code> is not empty. It has been green for a month. A seller's payouts stopped eleven days ago and the monitor never said a word about it, because the field that would have told it apart from routine housekeeping is a different array on the same object.",
"short_answer": """<p>Read <code>requirements.past_due</code>, not just <code>requirements.currently_due</code>. <code>past_due</code> is a strict subset of <code>currently_due</code>, so an account whose payouts Stripe has already disabled looks identical to one with paperwork outstanding if you only measure the length of the larger array.</p>
<p>The three states that matter are separate fields: <code>past_due</code> non-empty means already broken, <code>currently_due</code> with a near <code>requirements.current_deadline</code> means about to break on a known date, and <code>eventually_due</code> alone means nothing is wrong yet. Confirm the first with <code>disabled_reason == "requirements.past_due"</code> and <code>payouts_enabled == false</code>.</p>""",
"problem": """<p>The insidious part is that the monitor is not broken. It fires correctly, on a real field, with a sensible threshold. It just cannot distinguish the two situations that share that field, and the difference between them is a seller who needs a reminder email and a seller whose money has stopped moving.</p>
<p>What that produces in practice is alert fatigue that arrives in the worst possible order. Most accounts have something in <code>currently_due</code> most of the time, so the alert is noisy, so the team raises the threshold or mutes it, and the one account per month that is genuinely disabled comes in on the same channel as the eighty that are merely untidy. The signal was always there; it was averaged away.</p>""",
"why": """<p><strong>The arrays nest, and the nesting is not obvious.</strong> <code>eventually_due</code> contains <code>currently_due</code> contains <code>past_due</code>. A field moves inward over time as deadlines pass. Because every <code>past_due</code> field is also in <code>currently_due</code>, a check on the outer array is technically triggered by the inner state and therefore feels like it covers it. It does not: it just cannot say which one it saw.</p>
<p><strong>The deadline is invisible until it is not.</strong> <code>current_deadline</code> is the earliest deadline across every requested capability plus any risk requirements you cannot see. It is set the moment a volume threshold is crossed, which is a good thing happening to the seller, and it gives a real window. A boolean check discards that window entirely and turns a scheduled piece of work into a surprise.</p>
<p><strong>Cohorts break together.</strong> Deadlines are usually driven by processing thresholds, and sellers who onboarded in the same month cross them in the same month. The failure mode is not one account; it is fourteen accounts on a Tuesday, all with the same missing tax ID field, all of which could have been collected weeks earlier from the same list.</p>
<p><strong>Nothing in your own code fails.</strong> Payouts are automatic. When Stripe disables them, no request of yours errors, because you were not making one. The balance simply stops moving, and a balance that stops moving looks exactly like a quiet week until someone counts the days.</p>""",
"steps": [
 {"h": "Measure past_due separately from currently_due",
  "body": """<p>These are two different alerts with two different response times. <code>past_due</code> is an incident: capabilities that depend on those fields are already off. <code>currently_due</code> without <code>past_due</code> is a task. Reporting them on one line, with one count, guarantees the incident is read as a task.</p>"""},
 {"h": "Sort the rest by current_deadline ascending",
  "body": """<p>The accounts closest to their deadline are the ones worth an email today. An ordered list with days remaining next to each account is actionable in a way that an unordered set of account ids is not, and it lets you collect a whole cohort in one pass before any of them break.</p>"""},
 {"h": "Confirm the damage with payouts_enabled and disabled_reason",
  "body": """<p><code>requirements.past_due</code> being non-empty and <code>disabled_reason</code> reading <code>requirements.past_due</code> should agree with <code>payouts_enabled: false</code>. When they disagree, believe the requirement arrays: the capability that was disabled may not be the one driving the top-level flag.</p>"""},
 {"h": "Get the per-capability breakdown before you collect anything",
  "body": """<p><code>GET /v1/accounts/{id}/capabilities</code> returns <code>requirements.past_due</code> per capability. This matters when only one capability is affected, since the account-level arrays flatten several capabilities together and you can end up chasing a field that is blocking a capability the seller does not use.</p>"""},
 {"h": "Collect eventually_due, not currently_due",
  "body": """<p>An onboarding link with <code>collection_options[fields]=currently_due</code> clears today's problem and leaves the account to re-enter this state at the next threshold. Asking for <code>eventually_due</code> collects everything Stripe will ever want in one session, which is one email to the seller instead of three.</p>"""},
],
"verify": """<p>Re-run the script. No account should be in <code>past-due</code>, and anything left should carry a deadline far enough out to be scheduled rather than chased.</p>
<pre><code class="language-bash">python3 stripe_requirements_past_due.py
# 412 account(s): 0 past due, 3 with a deadline inside 14 days</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/accounts</code> &mdash; a restricted key with read access to Connected accounts covers it. The classifier takes the requirements object and the current time and returns one of five states, because the entire point of this check is that <em>already broken</em>, <em>breaks on a date</em> and <em>nothing wrong yet</em> are three different answers that a length check on one array collapses into one.",
"py_file": "stripe_requirements_past_due.py",
"py": '''"""Separate connected accounts that are already disabled from ones merely due.

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
log = logging.getLogger("stripe_requirements_past_due")

API = "https://api.stripe.com/v1"

# A deadline further out than this is a scheduled task; inside it, an email today.
NEAR_DEADLINE_DAYS = 14


def classify(requirements, now, near_days=NEAR_DEADLINE_DAYS):
    """Sort one account's requirements object. Pure, so the nesting can be tested.

    eventually_due contains currently_due contains past_due, so the arrays are
    read innermost first. Returns (state, detail).
    """
    reqs = requirements or {}
    past = [f for f in (reqs.get("past_due") or []) if f]
    current = [f for f in (reqs.get("currently_due") or []) if f]
    pending = [f for f in (reqs.get("pending_verification") or []) if f]
    eventual = [f for f in (reqs.get("eventually_due") or []) if f]
    deadline = reqs.get("current_deadline")

    if past:
        return ("past-due",
                "%d field(s) past the deadline, so the capabilities that need them "
                "are already off: %s" % (len(past), ", ".join(past[:4])))

    if current:
        if isinstance(deadline, (int, float)):
            days = (deadline - now) / 86400.0
            if days < 0:
                return ("overdue",
                        "current_deadline passed %.1f days ago with %d field(s) "
                        "still due: expect past_due next" % (-days, len(current)))
            if days <= near_days:
                return ("deadline",
                        "%d field(s) due and current_deadline is %.1f days away: %s"
                        % (len(current), days, ", ".join(current[:4])))
            return ("due",
                    "%d field(s) due, %.1f days of deadline left"
                    % (len(current), days))
        return ("due",
                "%d field(s) currently due with no deadline set yet"
                % len(current))

    if pending:
        return ("pending",
                "%d field(s) submitted and under verification: nothing to collect"
                % len(pending))

    if eventual:
        return ("eventual",
                "%d field(s) eventually due, none of them urgent" % len(eventual))

    return ("clear", "no outstanding requirements")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
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
    ap.add_argument("--near-days", type=int, default=NEAR_DEADLINE_DAYS,
                    help="treat a deadline inside this many days as urgent")
    ap.add_argument("--max-accounts", type=int, default=5000,
                    help="stop paginating after this many accounts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    counts = {}
    urgent = []
    scanned = 0

    for acct in accounts(s, args.max_accounts):
        scanned += 1
        state, detail = classify(acct.get("requirements"), now, args.near_days)
        counts[state] = counts.get(state, 0) + 1
        if state in ("past-due", "overdue", "deadline"):
            deadline = (acct.get("requirements") or {}).get("current_deadline") or 0
            urgent.append((deadline, acct.get("id", "acct_?"), state, detail,
                           acct.get("payouts_enabled")))

    # Soonest deadline first: this list is a work queue, not a report.
    for deadline, acct_id, state, detail, payouts in sorted(urgent):
        log.warning("%s  %-9s payouts_enabled=%s  %s",
                    acct_id, state, payouts, detail)

    log.info("%d account(s): %d past due, %d with a deadline inside %d days",
             scanned, counts.get("past-due", 0) + counts.get("overdue", 0),
             counts.get("deadline", 0), args.near_days)

    if counts.get("past-due") or counts.get("overdue"):
        log.warning("  repair: per-capability detail first, since the account level "
                    "arrays flatten several capabilities together:")
        log.warning("  GET %s/accounts/{id}/capabilities", API)
        log.warning("  repair: update the account with every string listed in "
                    "requirements.past_due, or send an onboarding account link")
    if counts.get("deadline") or counts.get("due"):
        log.warning("  repair: collect eventually_due rather than currently_due so "
                    "the account does not re-enter this state at the next threshold")
    return 1 if (counts.get("past-due") or counts.get("overdue")
                 or counts.get("deadline")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-requirements-past-due.mjs",
"js": '''/**
 * Separate connected accounts that are already disabled from ones merely due.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// A deadline further out than this is a scheduled task; inside it, an email today.
export const NEAR_DEADLINE_DAYS = 14;

/**
 * Sort one account's requirements object. Pure, so the nesting can be tested.
 * eventually_due contains currently_due contains past_due, so the arrays are read
 * innermost first. Returns [state, detail].
 */
export function classify(requirements, now, nearDays = NEAR_DEADLINE_DAYS) {
  const reqs = requirements ?? {};
  const past = (reqs.past_due ?? []).filter(Boolean);
  const current = (reqs.currently_due ?? []).filter(Boolean);
  const pending = (reqs.pending_verification ?? []).filter(Boolean);
  const eventual = (reqs.eventually_due ?? []).filter(Boolean);
  const deadline = reqs.current_deadline;

  if (past.length) {
    return ['past-due',
      `${past.length} field(s) past the deadline, so the capabilities that need ` +
      `them are already off: ${past.slice(0, 4).join(', ')}`];
  }

  if (current.length) {
    if (typeof deadline === 'number') {
      const days = (deadline - now) / 86400;
      if (days < 0) {
        return ['overdue',
          `current_deadline passed ${(-days).toFixed(1)} days ago with ` +
          `${current.length} field(s) still due: expect past_due next`];
      }
      if (days <= nearDays) {
        return ['deadline',
          `${current.length} field(s) due and current_deadline is ` +
          `${days.toFixed(1)} days away: ${current.slice(0, 4).join(', ')}`];
      }
      return ['due',
        `${current.length} field(s) due, ${days.toFixed(1)} days of deadline left`];
    }
    return ['due', `${current.length} field(s) currently due with no deadline set yet`];
  }

  if (pending.length) {
    return ['pending',
      `${pending.length} field(s) submitted and under verification: nothing to collect`];
  }

  if (eventual.length) {
    return ['eventual', `${eventual.length} field(s) eventually due, none of them urgent`];
  }

  return ['clear', 'no outstanding requirements'];
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

  const nearDays = Number(process.env.NEAR_DAYS ?? NEAR_DEADLINE_DAYS);
  const now = Math.floor(Date.now() / 1000);
  const counts = new Map();
  const urgent = [];
  let scanned = 0;

  for await (const acct of accounts(key)) {
    scanned += 1;
    const [state, detail] = classify(acct.requirements, now, nearDays);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (['past-due', 'overdue', 'deadline'].includes(state)) {
      urgent.push([acct.requirements?.current_deadline ?? 0, acct.id ?? 'acct_?',
        state, detail, acct.payouts_enabled]);
    }
  }

  // Soonest deadline first: this list is a work queue, not a report.
  for (const [, id, state, detail, payouts] of urgent.sort((a, b) => a[0] - b[0])) {
    console.warn(`${id}  ${state.padEnd(9)} payouts_enabled=${payouts}  ${detail}`);
  }

  const broken = (counts.get('past-due') ?? 0) + (counts.get('overdue') ?? 0);
  const soon = counts.get('deadline') ?? 0;
  console.log(`${scanned} account(s): ${broken} past due, ${soon} with a deadline ` +
              `inside ${nearDays} days`);

  if (broken) {
    console.warn('  repair: per-capability detail first, since the account level ' +
                 'arrays flatten several capabilities together:');
    console.warn(`  GET ${API}/accounts/{id}/capabilities`);
    console.warn('  repair: update the account with every string listed in ' +
                 'requirements.past_due, or send an onboarding account link');
  }
  if (soon || counts.get('due')) {
    console.warn('  repair: collect eventually_due rather than currently_due so the ' +
                 'account does not re-enter this state at the next threshold');
  }
  if (broken || soon) process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the one this whole guide exists for: an account with a field in <code>past_due</code> also has that field in <code>currently_due</code>, and a classifier that reads the outer array first reports it as a task. The rest pin the deadline arithmetic, including the case where the deadline has passed but Stripe has not moved the fields yet.",
"test_py_file": "test_stripe_requirements_past_due.py",
"test_py": '''from stripe_requirements_past_due import classify

NOW = 1800000000
DAY = 86400


def test_past_due_wins_over_the_array_that_contains_it():
    # past_due is a strict subset of currently_due. Reading the outer array first
    # is exactly the bug this check exists to avoid.
    state, detail = classify({
        "past_due": ["company.tax_id"],
        "currently_due": ["company.tax_id", "business_profile.url"],
        "current_deadline": NOW - 3 * DAY,
    }, NOW)
    assert state == "past-due"
    assert "company.tax_id" in detail


def test_near_deadline_is_separated_from_a_distant_one():
    reqs = {"currently_due": ["company.tax_id"], "current_deadline": NOW + 20 * DAY}
    assert classify(reqs, NOW)[0] == "due"
    reqs["current_deadline"] = NOW + 13 * DAY
    assert classify(reqs, NOW)[0] == "deadline"


def test_fourteen_days_is_inside_the_window():
    reqs = {"currently_due": ["x"], "current_deadline": NOW + 14 * DAY}
    assert classify(reqs, NOW)[0] == "deadline"


def test_passed_deadline_without_past_due_is_still_reported():
    # Stripe moves the fields on its own schedule, so there is a gap where the
    # deadline is behind you and past_due is still empty.
    state, detail = classify(
        {"currently_due": ["x"], "current_deadline": NOW - 2 * DAY}, NOW)
    assert state == "overdue"
    assert "expect past_due next" in detail


def test_pending_verification_is_not_work_for_anyone():
    state, _ = classify({"pending_verification": ["individual.id_number"]}, NOW)
    assert state == "pending"


def test_eventually_due_alone_is_not_urgent_and_empty_is_clear():
    assert classify({"eventually_due": ["company.tax_id"]}, NOW)[0] == "eventual"
    assert classify({}, NOW)[0] == "clear"
    assert classify(None, NOW)[0] == "clear"
''',
"test_js_file": "stripe-requirements-past-due.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-requirements-past-due.mjs';

const NOW = 1800000000;
const DAY = 86400;

test('past due wins over the array that contains it', () => {
  // past_due is a strict subset of currently_due. Reading the outer array first
  // is exactly the bug this check exists to avoid.
  const [state, detail] = classify({
    past_due: ['company.tax_id'],
    currently_due: ['company.tax_id', 'business_profile.url'],
    current_deadline: NOW - 3 * DAY,
  }, NOW);
  assert.equal(state, 'past-due');
  assert.match(detail, /company\\.tax_id/);
});

test('near deadline is separated from a distant one', () => {
  const reqs = { currently_due: ['company.tax_id'], current_deadline: NOW + 20 * DAY };
  assert.equal(classify(reqs, NOW)[0], 'due');
  reqs.current_deadline = NOW + 13 * DAY;
  assert.equal(classify(reqs, NOW)[0], 'deadline');
});

test('fourteen days is inside the window', () => {
  assert.equal(
    classify({ currently_due: ['x'], current_deadline: NOW + 14 * DAY }, NOW)[0],
    'deadline');
});

test('passed deadline without past due is still reported', () => {
  // Stripe moves the fields on its own schedule, so there is a gap where the
  // deadline is behind you and past_due is still empty.
  const [state, detail] = classify(
    { currently_due: ['x'], current_deadline: NOW - 2 * DAY }, NOW);
  assert.equal(state, 'overdue');
  assert.match(detail, /expect past_due next/);
});

test('pending verification is not work for anyone', () => {
  assert.equal(classify({ pending_verification: ['individual.id_number'] }, NOW)[0],
    'pending');
});

test('eventually due alone is not urgent and empty is clear', () => {
  assert.equal(classify({ eventually_due: ['company.tax_id'] }, NOW)[0], 'eventual');
  assert.equal(classify({}, NOW)[0], 'clear');
  assert.equal(classify(null, NOW)[0], 'clear');
});
''',
"faq": [
 ("What is the difference between past_due and currently_due?",
  "currently_due is everything Stripe needs from the account now. past_due is the part of that list whose deadline has already passed, which is why Stripe has disabled the capabilities depending on it. Every past_due field also appears in currently_due, so the two are not alternatives: past_due is the subset that means the account is already broken."),
 ("Where does current_deadline come from?",
  "It is the earliest deadline across every requested capability, including risk requirements you cannot see in the object. Stripe sets it when a threshold is crossed, usually a processing volume one, which means it tends to appear because the seller is doing well. It is a window, and the only way to use it is to sort by it."),
 ("Why does payouts_enabled sometimes stay true with fields past due?",
  "Because requirements are per capability. A field past due on a capability the account does not rely on for payouts disables that capability without touching payouts. This is why the per-capability call matters: the account-level arrays flatten several capabilities together and cannot tell you which one is affected."),
 ("Should I collect currently_due or eventually_due?",
  "eventually_due, in almost every case. Collecting currently_due clears today's block and leaves the account to hit the same wall at the next threshold, which means another email, another link, and another chance for the seller to ignore it. eventually_due asks for everything once."),
 ("Does this need write access?",
  "No. Read access to Connected accounts covers both the list and the per-capability detail. The script sorts accounts into a work queue and prints what to submit; the submission itself is a write, and it belongs in a tool with a much narrower blast radius than a monitor that runs unattended."),
],
"related": [
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
 ("/stripe/no-external-account-attached/", "A connected account has no external account to pay out to"),
 ("/stripe/payouts-failing-bank-rejection/", "Payouts fail with account_closed and nobody is watching"),
],
"citations": [CITE_VERIFICATION, CITE_ACCOUNT_OBJECT, CITE_REQUIRED_INFO, CITE_CAPABILITY_OBJECT],
},

{
"slug": "payouts-failing-bank-rejection",
"title": "Payouts fail with account_closed and nobody is watching",
"description": "Money leaves your Stripe balance, comes back days later, and the recipient was never paid. The failure_code says which fix applies, if anything reads it.",
"h1": "payouts fail with account_closed and nobody is watching",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payout failed", "payout failure_code account_closed",
             "stripe payout debit_not_authorized", "payout reversed to balance",
             "stripe failed payouts monitoring"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The ledger says the payout was paid. The recipient says no money arrived. Both are true: the payout reached <code>paid</code>, the bank rejected the credit four days later, Stripe moved it to <code>failed</code> and returned the funds to your balance. Nothing in your system recorded the second half of that story, because nothing was reading the object after it went green.",
"short_answer": """<p>Query <code>GET /v1/payouts?status=failed&amp;limit=100&amp;created[gte]=&lt;90 days ago&gt;</code> on the platform, and again per connected account with the <code>Stripe-Account</code> header. Group the results by <code>failure_code</code>, because that enum is what decides the repair.</p>
<p><code>account_closed</code>, <code>no_account</code> and the <code>invalid_account_number</code> family need new bank details on the destination. <code>debit_not_authorized</code> and <code>incorrect_account_type</code> need the account holder to talk to their bank. <code>insufficient_funds</code> needs a top-up, not a bank change. Retrying without reading the code repeats whichever of these you happened to hit.</p>""",
"problem": """<p>A payout that reads <code>paid</code> is not finished. The status reflects Stripe having sent the credit, and the receiving bank can reject it for up to five business days afterwards, at which point the payout flips to <code>failed</code> and the money is returned to your Stripe balance along with a <code>failure_balance_transaction</code>.</p>
<p>Two things go wrong at once when nobody is watching this. The recipient is unpaid and does not know why, so your support queue gets a message that sounds like an accusation of theft. And your reconciliation is now off in a way that is hard to spot: the original payout debited the balance, the reversal credited it back, and a report that sums payouts without accounting for reversals shows money going out that never left.</p>""",
"why": """<p><strong>The terminal-looking state is not terminal.</strong> <code>pending</code> to <code>in_transit</code> to <code>paid</code> looks like a completed lifecycle, and every instinct says to stop reading an object once it reaches the state you were waiting for. The <code>paid</code> to <code>failed</code> transition arrives days later, on the bank's schedule, with nothing to prompt a re-read.</p>
<p><strong>The failure codes need different people.</strong> They look like one category &mdash; "the payout failed" &mdash; and they are at least four. A closed account needs new details from the seller. <code>debit_not_authorized</code> needs the seller to authorise debits with their own bank, and no amount of re-entering the same account number will fix it. <code>insufficient_funds</code> is about your balance, not theirs. Treating them alike produces a support script that is wrong three times out of four.</p>
<p><strong>The first failure stops the rest.</strong> A payout failure sets the external account's <code>status</code> to <code>errored</code>, and Stripe stops sending scheduled payouts to that destination. So the count of failed payouts goes up once and then stays flat, which reads like a resolved blip. It is the opposite: the number stopped growing because nothing is being attempted any more.</p>
<p><strong>The event exists and is usually unsubscribed.</strong> <code>payout.failed</code> is a real event that would have told you on the day. Platforms that never subscribed to it find out from the recipient, which is always later and always more expensive.</p>""",
"steps": [
 {"h": "Query failed payouts over a window wide enough to catch the pattern",
  "body": """<p>Ninety days. A shorter window can show one failure and hide the fact that it is the same destination failing every cycle. Run it on the platform account and then once per connected account with the <code>Stripe-Account</code> header, since a platform's own payouts and its sellers' payouts are separate lists.</p>"""},
 {"h": "Group by failure_code before looking at anything else",
  "body": """<p>The distribution is the diagnosis. Twenty failures across twenty codes is bad luck; twenty failures all reading <code>debit_not_authorized</code> is an onboarding flow that never told sellers to authorise debits. Read <code>failure_message</code> for the human sentence, but branch on the code.</p>"""},
 {"h": "Confirm the money came back",
  "body": """<p><code>failure_balance_transaction</code> is non-null on a failed payout and points at the balance transaction that returned the funds. If your reconciliation does not know about that object, every failed payout is a double count: once out, once back, neither matched.</p>"""},
 {"h": "Check whether the destination is now frozen",
  "body": """<p>Read the external account's <code>status</code>. <code>errored</code> means scheduled payouts to it have stopped, which explains why the failures are not accumulating and why the balance is. Attaching fresh details is what clears it; editing the numbers on the existing object generally does not.</p>"""},
 {"h": "Subscribe to payout.failed so the next one arrives as an event",
  "body": """<p>Check <code>GET /v1/webhook_endpoints</code> for <code>payout.failed</code> in <code>enabled_events</code>. A daily script is a good backstop and a bad primary: it turns a five-day-old failure into a four-day-old one, where the event would have told you the same day.</p>"""},
],
"verify": """<p>Re-run the script after fresh details are attached and the next payout cycle has run. The failed count over the window should stop growing, and the destination should no longer report a frozen status.</p>
<pre><code class="language-bash">python3 stripe_failed_payouts.py --days 90
# 0 failed payout(s) in the last 90 days</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/payouts</code>, optionally repeated per connected account &mdash; a restricted key with read access to Payouts is enough. The classifier maps <code>failure_code</code> to the person who can act, because the enum has more than a dozen members and the useful question is not which code it is but whether this needs the seller, their bank, or your balance.",
"py_file": "stripe_failed_payouts.py",
"py": '''"""Group failed Stripe payouts by failure_code and say what each one needs.

Read only. One paginated GET per account and no writes: give this a RESTRICTED
key with read access to Payouts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_failed_payouts")

API = "https://api.stripe.com/v1"

# The destination is wrong or gone. Nothing but new bank details fixes these.
NEW_DETAILS = (
    "account_closed", "no_account", "invalid_account_number",
    "invalid_account_number_length", "incorrect_account_holder_name",
    "incorrect_account_holder_address", "incorrect_account_holder_tax_id",
    "unsupported_card",
)
# The account exists but its holder has to authorise something with their bank.
BANK_AUTHORISATION = (
    "debit_not_authorized", "incorrect_account_type", "declined",
    "bank_account_restricted", "account_frozen",
)
# Your balance, not their bank.
FUNDING = ("insufficient_funds",)
# Transient. Worth one retry before anyone is contacted.
TRANSIENT = ("could_not_process", "bank_ownership_changed")
# A configuration mismatch on the destination rather than a bad number.
CONFIGURATION = ("invalid_currency", "unsupported_currency")


def classify(payout):
    """Sort one payout by what its failure needs. Pure, so the table is testable.

    Takes a /v1/payouts object. Returns (state, detail). The states name the
    person who can act, which is the only grouping that changes what you do next.
    """
    status = payout.get("status")
    if status in ("paid", "in_transit", "pending"):
        return ("open", "status %s: not a failure, and not final either" % status)
    if status == "canceled":
        return ("canceled", "cancelled before it left, nothing was rejected")
    if status != "failed":
        return ("unknown", "unrecognised status %r" % (status,))

    code = payout.get("failure_code") or "unknown"
    message = payout.get("failure_message") or "no failure_message"
    returned = payout.get("failure_balance_transaction") is not None
    tail = "" if returned else " (no failure_balance_transaction: check the balance)"

    if code in NEW_DETAILS:
        return ("new-details",
                "%s: the destination is gone or wrong. Attach a fresh external "
                "account; re-entering the same number fails identically.%s"
                % (code, tail))
    if code in BANK_AUTHORISATION:
        return ("bank-authorisation",
                "%s: the account exists, its holder has to settle this with their "
                "bank. New details will not help.%s" % (code, tail))
    if code in FUNDING:
        return ("funding",
                "%s: your balance could not cover it. This is your side, not "
                "theirs.%s" % (code, tail))
    if code in TRANSIENT:
        return ("transient",
                "%s: worth one retry before anyone is contacted.%s" % (code, tail))
    if code in CONFIGURATION:
        return ("configuration",
                "%s: the destination cannot receive this currency.%s" % (code, tail))
    return ("unclassified",
            "failure_code %s: %s%s" % (code, message, tail))


def get(session, path, account=None, **params):
    headers = {"Stripe-Account": account} if account else None
    r = session.get(API + path, params=params, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def failed_payouts(session, since, cap, account=None):
    """Yield failed payouts created since `since`, paginating to the cap."""
    seen = 0
    params = {"limit": 100, "status": "failed", "created[gte]": since}
    while True:
        page = get(session, "/payouts", account=account, **params)
        data = page.get("data", [])
        for po in data:
            yield po
            seen += 1
            if seen >= cap:
                return
        if not data or not page.get("has_more"):
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to look (default 90)")
    ap.add_argument("--account", action="append", default=[],
                    help="also scan this connected account; repeatable")
    ap.add_argument("--max-payouts", type=int, default=2000,
                    help="stop paginating after this many failed payouts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    counts = {}
    by_code = {}
    returned_minor = 0
    total = 0

    for account in [None] + list(args.account):
        for po in failed_payouts(s, since, args.max_payouts, account):
            total += 1
            state, detail = classify(po)
            counts[state] = counts.get(state, 0) + 1
            code = po.get("failure_code") or "unknown"
            by_code[code] = by_code.get(code, 0) + 1
            returned_minor += int(po.get("amount") or 0)
            log.warning("%s  %-18s dest=%s  %s", po.get("id", "po_?"), state,
                        po.get("destination") or "?", detail)

    log.info("%d failed payout(s) in the last %d days", total, args.days)
    for code, n in sorted(by_code.items(), key=lambda kv: -kv[1]):
        log.warning("  %-34s %d", code, n)

    if total:
        log.warning("  %d in minor units came back to the balance: reconcile against "
                    "failure_balance_transaction or it is counted twice", returned_minor)
    if counts.get("new-details"):
        log.warning("  repair: attach a new external account and make it the default "
                    "for the currency. Editing the existing one rarely clears it.")
    if counts.get("bank-authorisation"):
        log.warning("  repair: the account holder authorises credits and debits with "
                    "their own bank. No API call substitutes for that.")
    if counts.get("funding"):
        log.warning("  repair: fund the balance before the next payout cycle")
    if total:
        log.warning("  check: the destination status is probably errored, which stops "
                    "scheduled payouts and is why the failures are not accumulating:")
        log.warning("  GET %s/accounts/{id}/external_accounts", API)
        log.warning("  check: payout.failed in enabled_events, or this stays a "
                    "five day old surprise:")
        log.warning("  GET %s/webhook_endpoints", API)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-failed-payouts.mjs",
"js": '''/**
 * Group failed Stripe payouts by failure_code and say what each one needs.
 *
 * Read only. One paginated GET per account and no writes: give this a RESTRICTED
 * key with read access to Payouts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// The destination is wrong or gone. Nothing but new bank details fixes these.
const NEW_DETAILS = [
  'account_closed', 'no_account', 'invalid_account_number',
  'invalid_account_number_length', 'incorrect_account_holder_name',
  'incorrect_account_holder_address', 'incorrect_account_holder_tax_id',
  'unsupported_card',
];
// The account exists but its holder has to authorise something with their bank.
const BANK_AUTHORISATION = [
  'debit_not_authorized', 'incorrect_account_type', 'declined',
  'bank_account_restricted', 'account_frozen',
];
// Your balance, not their bank.
const FUNDING = ['insufficient_funds'];
// Transient. Worth one retry before anyone is contacted.
const TRANSIENT = ['could_not_process', 'bank_ownership_changed'];
// A configuration mismatch on the destination rather than a bad number.
const CONFIGURATION = ['invalid_currency', 'unsupported_currency'];

/**
 * Sort one payout by what its failure needs. Pure, so the table is testable.
 * The states name the person who can act, which is the only grouping that
 * changes what you do next. Returns [state, detail].
 */
export function classify(payout) {
  const status = payout.status;
  if (['paid', 'in_transit', 'pending'].includes(status)) {
    return ['open', `status ${status}: not a failure, and not final either`];
  }
  if (status === 'canceled') {
    return ['canceled', 'cancelled before it left, nothing was rejected'];
  }
  if (status !== 'failed') {
    return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
  }

  const code = payout.failure_code ?? 'unknown';
  const message = payout.failure_message ?? 'no failure_message';
  const returned = payout.failure_balance_transaction != null;
  const tail = returned ? '' : ' (no failure_balance_transaction: check the balance)';

  if (NEW_DETAILS.includes(code)) {
    return ['new-details',
      `${code}: the destination is gone or wrong. Attach a fresh external ` +
      `account; re-entering the same number fails identically.${tail}`];
  }
  if (BANK_AUTHORISATION.includes(code)) {
    return ['bank-authorisation',
      `${code}: the account exists, its holder has to settle this with their ` +
      `bank. New details will not help.${tail}`];
  }
  if (FUNDING.includes(code)) {
    return ['funding',
      `${code}: your balance could not cover it. This is your side, not theirs.${tail}`];
  }
  if (TRANSIENT.includes(code)) {
    return ['transient', `${code}: worth one retry before anyone is contacted.${tail}`];
  }
  if (CONFIGURATION.includes(code)) {
    return ['configuration',
      `${code}: the destination cannot receive this currency.${tail}`];
  }
  return ['unclassified', `failure_code ${code}: ${message}${tail}`];
}

async function get(key, path, { account = null, ...params } = {}) {
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

export async function* failedPayouts(key, since, cap = 2000, account = null) {
  let seen = 0;
  const params = { account, limit: 100, status: 'failed', 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/payouts', params);
    const data = page.data ?? [];
    for (const po of data) {
      yield po;
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

  const days = Number(process.env.DAYS ?? 90);
  const extra = (process.env.ACCOUNTS ?? '').split(',').filter(Boolean);
  const since = Math.floor(Date.now() / 1000) - days * 86400;

  const counts = new Map();
  const byCode = new Map();
  let returnedMinor = 0;
  let total = 0;

  for (const account of [null, ...extra]) {
    for await (const po of failedPayouts(key, since, 2000, account)) {
      total += 1;
      const [state, detail] = classify(po);
      counts.set(state, (counts.get(state) ?? 0) + 1);
      const code = po.failure_code ?? 'unknown';
      byCode.set(code, (byCode.get(code) ?? 0) + 1);
      returnedMinor += po.amount ?? 0;
      console.warn(`${po.id ?? 'po_?'}  ${state.padEnd(18)} ` +
                   `dest=${po.destination ?? '?'}  ${detail}`);
    }
  }

  console.log(`${total} failed payout(s) in the last ${days} days`);
  for (const [code, n] of [...byCode].sort((a, b) => b[1] - a[1])) {
    console.warn(`  ${code.padEnd(34)} ${n}`);
  }

  if (total) {
    console.warn(`  ${returnedMinor} in minor units came back to the balance: ` +
                 'reconcile against failure_balance_transaction or it is counted twice');
  }
  if (counts.get('new-details')) {
    console.warn('  repair: attach a new external account and make it the default ' +
                 'for the currency. Editing the existing one rarely clears it.');
  }
  if (counts.get('bank-authorisation')) {
    console.warn('  repair: the account holder authorises credits and debits with ' +
                 'their own bank. No API call substitutes for that.');
  }
  if (counts.get('funding')) {
    console.warn('  repair: fund the balance before the next payout cycle');
  }
  if (total) {
    console.warn('  check: the destination status is probably errored, which stops ' +
                 'scheduled payouts and is why the failures are not accumulating:');
    console.warn(`  GET ${API}/accounts/{id}/external_accounts`);
    console.warn('  check: payout.failed in enabled_events, or this stays a five ' +
                 'day old surprise:');
    console.warn(`  GET ${API}/webhook_endpoints`);
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
"test_intro": "The tests exist to keep two pairs apart. <code>account_closed</code> and <code>debit_not_authorized</code> both mean an unpaid recipient and need opposite actions, and a <code>paid</code> payout must never classify as final, because the whole failure mode here is a status that changes after everyone stopped looking.",
"test_py_file": "test_stripe_failed_payouts.py",
"test_py": '''from stripe_failed_payouts import classify


def test_paid_is_not_treated_as_final():
    # The paid to failed transition happens up to five business days later. A
    # classifier that calls paid "done" is the bug this guide is about.
    state, detail = classify({"status": "paid"})
    assert state == "open"
    assert "not final" in detail


def test_closed_account_needs_new_details():
    state, detail = classify({
        "status": "failed", "failure_code": "account_closed",
        "failure_balance_transaction": "txn_1",
    })
    assert state == "new-details"
    assert "fails identically" in detail


def test_debit_not_authorized_is_not_a_bank_details_problem():
    # The number is right. Attaching a new external account changes nothing, and
    # asking the seller for it wastes a round trip while they stay unpaid.
    state, detail = classify({
        "status": "failed", "failure_code": "debit_not_authorized",
        "failure_balance_transaction": "txn_2",
    })
    assert state == "bank-authorisation"
    assert "New details will not help" in detail


def test_insufficient_funds_is_your_side():
    state, detail = classify({
        "status": "failed", "failure_code": "insufficient_funds",
        "failure_balance_transaction": "txn_3",
    })
    assert state == "funding"
    assert "your side" in detail


def test_missing_reversal_is_called_out():
    _, detail = classify({"status": "failed", "failure_code": "account_closed"})
    assert "no failure_balance_transaction" in detail


def test_unknown_code_is_reported_rather_than_swallowed():
    state, detail = classify({
        "status": "failed", "failure_code": "brand_new_code",
        "failure_message": "Something Stripe added later",
    })
    assert state == "unclassified"
    assert "brand_new_code" in detail
    assert classify({"status": "in_flight"})[0] == "unknown"
''',
"test_js_file": "stripe-failed-payouts.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-failed-payouts.mjs';

test('paid is not treated as final', () => {
  // The paid to failed transition happens up to five business days later. A
  // classifier that calls paid "done" is the bug this guide is about.
  const [state, detail] = classify({ status: 'paid' });
  assert.equal(state, 'open');
  assert.match(detail, /not final/);
});

test('closed account needs new details', () => {
  const [state, detail] = classify({
    status: 'failed',
    failure_code: 'account_closed',
    failure_balance_transaction: 'txn_1',
  });
  assert.equal(state, 'new-details');
  assert.match(detail, /fails identically/);
});

test('debit not authorized is not a bank details problem', () => {
  // The number is right. Attaching a new external account changes nothing.
  const [state, detail] = classify({
    status: 'failed',
    failure_code: 'debit_not_authorized',
    failure_balance_transaction: 'txn_2',
  });
  assert.equal(state, 'bank-authorisation');
  assert.match(detail, /New details will not help/);
});

test('insufficient funds is your side', () => {
  const [state, detail] = classify({
    status: 'failed',
    failure_code: 'insufficient_funds',
    failure_balance_transaction: 'txn_3',
  });
  assert.equal(state, 'funding');
  assert.match(detail, /your side/);
});

test('missing reversal is called out', () => {
  const [, detail] = classify({ status: 'failed', failure_code: 'account_closed' });
  assert.match(detail, /no failure_balance_transaction/);
});

test('unknown code is reported rather than swallowed', () => {
  const [state, detail] = classify({
    status: 'failed',
    failure_code: 'brand_new_code',
    failure_message: 'Something Stripe added later',
  });
  assert.equal(state, 'unclassified');
  assert.match(detail, /brand_new_code/);
  assert.equal(classify({ status: 'in_flight' })[0], 'unknown');
});
''',
"faq": [
 ("How can a payout go from paid to failed?",
  "paid means Stripe sent the credit, not that the receiving bank accepted it. Banks can reject a credit for several business days afterwards, and when that happens Stripe moves the payout to failed and returns the funds to your balance. It is the normal behaviour of the banking rails, not a Stripe anomaly, and it is why a payout should be read again rather than filed once it turns green."),
 ("Where does the money go when a payout fails?",
  "Back to your Stripe balance, recorded as the balance transaction referenced by failure_balance_transaction on the payout. Reconciliation that sums payouts without subtracting these reversals reports money leaving that never left, which is usually noticed weeks later as an unexplained surplus."),
 ("Why did the failures stop appearing after the first one?",
  "Because the destination is frozen. A failed payout sets the external account's status to errored and Stripe stops sending scheduled payouts there. The flat failure count is not recovery, it is the absence of attempts, and the giveaway is a balance that keeps climbing next to it."),
 ("What is the difference between account_closed and debit_not_authorized?",
  "account_closed means the destination no longer exists, so the fix is fresh bank details. debit_not_authorized means the account exists and its holder has not authorised the bank to accept this kind of movement, so the fix is a conversation between the holder and their bank. Sending new details for the second one produces the same failure with a different account number on it."),
 ("Is a daily script enough, or do I need the webhook?",
  "Both, with the event first. payout.failed tells you on the day; a daily read of GET /v1/payouts?status=failed catches anything the endpoint missed while it was disabled or misconfigured. Running only the script means every failure is discovered up to a day late, on top of the days the bank already took."),
],
"related": [
 ("/stripe/missing-payout-failed/", "payout.failed is unsubscribed so broken bank details go unseen"),
 ("/stripe/no-external-account-attached/", "A connected account has no external account to pay out to"),
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
],
"citations": [CITE_PAYOUT_OBJECT, CITE_PAYOUT_LIST, CITE_EXTERNAL_ACCOUNT, CITE_PAYOUTS],
},

{
"slug": "no-external-account-attached",
"title": "A connected account has no external account to pay out to",
"description": "A seller's balance climbs for months with no failed payouts, because no payout was ever attempted. There is nowhere for the money to go.",
"h1": "a connected account has no external account to pay out to",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe external_account missing", "connect no bank account",
             "stripe payouts never run", "external_account_collection disabled",
             "default_for_currency stripe"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A seller has been taking payments for five months. Their Stripe balance is a five-figure number and it has only ever gone up. There are no failed payouts to investigate, no errors in any log, and no alert anywhere, for the simple reason that nothing has ever been attempted: the account has no bank account attached, so automatic payouts have nowhere to send the money.",
"short_answer": """<p>For each connected account call <code>GET /v1/accounts/{id}/external_accounts?limit=100</code> and check two things: whether <code>data</code> is empty at all, and whether any entry has <code>default_for_currency: true</code> for the account's <code>default_currency</code>. Both cases stop payouts, and the second one is the harder to spot because the account visibly has a bank account attached.</p>
<p>Corroborate against the account object: <code>requirements.currently_due</code> containing the literal string <code>external_account</code> confirms Stripe agrees it is missing. Note that <code>details_submitted</code> can be <code>true</code> throughout &mdash; onboarding completed, it just never collected this.</p>""",
"problem": """<p>Every monitoring instinct is built around things failing. This fails by never happening. There is no payout object to inspect, no <code>failure_code</code> to group by, no <code>payout.failed</code> event to subscribe to. The absence is the symptom, and absences do not raise alerts unless something is specifically counting them.</p>
<p>What makes it survive for months is that the seller's side looks completely healthy. Payments succeed, the Dashboard shows a growing balance, and the platform's own reporting shows the seller as one of the good ones. The discovery event is a seller asking where their money is, at which point the balance is large enough that the conversation is uncomfortable and the delay is measured in months rather than days.</p>""",
"why": """<p><strong>Onboarding can legitimately be told to skip it.</strong> <code>external_account_collection</code> gets disabled when a platform intends to collect bank details through its own interface. That is a supported configuration. The failure is the second half never being built, or being built and quietly failing, at which point accounts finish onboarding with <code>details_submitted: true</code> and no destination.</p>
<p><strong>A missing default is not the same as a missing account.</strong> An account can have a bank account attached and still not pay out, if none is marked <code>default_for_currency</code> for the currency the balance is in. This is common when a seller's balance ends up in a currency their attached account does not serve, and it looks completely fine in any check that only counts rows.</p>
<p><strong>Requirements say so, quietly.</strong> <code>external_account</code> appears in <code>currently_due</code>, but it sits in the same array as a dozen other verification fields, and a platform that treats requirements as one undifferentiated to-do list never notices that this particular string means the money cannot move at all.</p>
<p><strong>Nothing else in the system disagrees.</strong> Charges work, capabilities are active, the account is not disabled. Every health check the platform runs passes, because the account genuinely is healthy in every respect except the one nobody is measuring.</p>""",
"steps": [
 {"h": "List the external accounts for every connected account",
  "body": """<p>One GET per account. Zero rows is the obvious case and the fastest to confirm. Do it for every account rather than for the ones that complained, because by construction the affected sellers do not know anything is wrong yet.</p>"""},
 {"h": "Check the default for the account's own default_currency",
  "body": """<p>Read <code>default_currency</code> from the account object, then look for an external account with a matching <code>currency</code> and <code>default_for_currency: true</code>. An account with three attached destinations and no default for the currency the balance is actually in pays out exactly as often as one with none.</p>"""},
 {"h": "Cross-check requirements.currently_due for the literal string",
  "body": """<p><code>external_account</code> in <code>currently_due</code> is Stripe's own confirmation. When the list is empty and there is still no destination, the platform disabled collection during onboarding and Stripe is not going to ask for it on your behalf.</p>"""},
 {"h": "Look at the balance next to the finding",
  "body": """<p>An account with no destination and a zero balance is a configuration bug to fix this week. The same account with months of accumulated funds is a conversation with a seller that gets worse every day it waits. The API call is the same; the priority is not, and only one of the two belongs at the top of the queue.</p>"""},
 {"h": "Decide who collects the details, then make that path exist",
  "body": """<p>Either re-enable external account collection so Stripe's onboarding asks, or send an account link of type <code>account_update</code> and let the seller add it there. What must not happen is the current state, where onboarding believes the platform will collect it and the platform believes onboarding did.</p>"""},
],
"verify": """<p>Re-run the script. Every account should report a default destination for its own currency, and the next payout cycle should produce actual payout objects for accounts that previously had none.</p>
<pre><code class="language-bash">python3 stripe_missing_external_account.py
# 412 account(s): 0 with no destination, 0 with no default for their currency</code></pre>""",
"code_intro": "Two GETs per account and no writes &mdash; a restricted key with read access to Connected accounts is enough. The classifier takes the list of external accounts, the account's default currency and its <code>currently_due</code> array, because <em>no destination at all</em> and <em>a destination that cannot receive this currency</em> produce the same silence and need different repairs.",
"py_file": "stripe_missing_external_account.py",
"py": '''"""Find connected accounts whose balance cannot move because nothing is attached.

Read only. Two GETs per account and no writes: give this a RESTRICTED key with
read access to Connected accounts. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_missing_external_account")

API = "https://api.stripe.com/v1"

# A destination in one of these states is attached but cannot be paid to. It is a
# different problem from having none, and it needs fresh details rather than a
# form the seller has already filled in.
UNUSABLE = ("errored", "verification_failed",
            "tokenized_account_number_deactivated")


def classify(external_accounts, default_currency, currently_due=()):
    """Decide whether this account can be paid out. Pure, so it can be tested.

    `external_accounts` is the `data` array from /v1/accounts/{id}/external_accounts.
    Returns (state, detail).
    """
    rows = list(external_accounts or [])
    due = [f for f in (currently_due or []) if f]
    asked = "external_account" in due
    currency = (default_currency or "").lower()

    if not rows:
        if asked:
            return ("none",
                    "no external account, and external_account is in currently_due: "
                    "Stripe is asking and nobody is collecting it")
        return ("none-unrequested",
                "no external account and Stripe is not asking for one: external "
                "account collection was turned off during onboarding")

    unusable = [r for r in rows if r.get("status") in UNUSABLE]
    matching = [r for r in rows
                if (r.get("currency") or "").lower() == currency]
    default = [r for r in matching if r.get("default_for_currency")]

    if default:
        bad = [r for r in default if r.get("status") in UNUSABLE]
        if bad:
            return ("unusable",
                    "the default destination for %s has status %s: scheduled payouts "
                    "to it have stopped" % (currency or "?", bad[0].get("status")))
        return ("attached",
                "%d destination(s), default set for %s" % (len(rows), currency or "?"))

    if matching:
        return ("no-default",
                "%d destination(s) in %s but none marked default_for_currency: "
                "payouts have nowhere to go" % (len(matching), currency or "?"))

    if unusable:
        return ("unusable",
                "%d destination(s), all in a failed state (%s)"
                % (len(rows), unusable[0].get("status")))

    return ("wrong-currency",
            "%d destination(s), none of them in %s, so the balance cannot be paid out"
            % (len(rows), currency or "the account default currency"))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def accounts(session, cap):
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
    ap.add_argument("--max-accounts", type=int, default=1000,
                    help="stop after this many accounts; each one costs a GET")
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
        acct_id = acct.get("id", "acct_?")
        reqs = acct.get("requirements") or {}
        page = get(s, "/accounts/%s/external_accounts" % acct_id, limit=100)
        state, detail = classify(page.get("data"), acct.get("default_currency"),
                                 reqs.get("currently_due"))
        counts[state] = counts.get(state, 0) + 1
        if state == "attached":
            continue
        log.warning("%s  %-17s payouts_enabled=%s  %s",
                    acct_id, state, acct.get("payouts_enabled"), detail)

    missing = counts.get("none", 0) + counts.get("none-unrequested", 0)
    no_default = counts.get("no-default", 0) + counts.get("wrong-currency", 0)

    log.info("%d account(s): %d with no destination, %d with no default for their "
             "currency", scanned, missing, no_default)

    if counts.get("none"):
        log.warning("  repair: send the seller an account link of type account_update "
                    "so they attach a bank account themselves")
    if counts.get("none-unrequested"):
        log.warning("  repair: Dashboard, Settings, Connect, Payouts: re-enable "
                    "external account collection, or finish the flow that was going "
                    "to collect it in your own interface")
    if no_default:
        log.warning("  repair: mark one destination default_for_currency for the "
                    "account default_currency, or attach one in that currency")
    if counts.get("unusable"):
        log.warning("  repair: attach fresh details. Editing the numbers on an "
                    "errored destination does not clear the status.")
    if missing or no_default or counts.get("unusable"):
        log.warning("  check: the balance on these accounts says how old this is:")
        log.warning("  GET %s/balance  with the Stripe-Account header", API)
    return 1 if (missing or no_default or counts.get("unusable")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-missing-external-account.mjs",
"js": '''/**
 * Find connected accounts whose balance cannot move because nothing is attached.
 *
 * Read only. Two GETs per account and no writes: give this a RESTRICTED key with
 * read access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// A destination in one of these states is attached but cannot be paid to. It is a
// different problem from having none, and it needs fresh details rather than a
// form the seller has already filled in.
const UNUSABLE = ['errored', 'verification_failed',
  'tokenized_account_number_deactivated'];

/**
 * Decide whether this account can be paid out. Pure, so it can be tested.
 * `externalAccounts` is the data array from /v1/accounts/{id}/external_accounts.
 * Returns [state, detail].
 */
export function classify(externalAccounts, defaultCurrency, currentlyDue = []) {
  const rows = externalAccounts ?? [];
  const due = (currentlyDue ?? []).filter(Boolean);
  const asked = due.includes('external_account');
  const currency = (defaultCurrency ?? '').toLowerCase();

  if (rows.length === 0) {
    if (asked) {
      return ['none',
        'no external account, and external_account is in currently_due: Stripe is ' +
        'asking and nobody is collecting it'];
    }
    return ['none-unrequested',
      'no external account and Stripe is not asking for one: external account ' +
      'collection was turned off during onboarding'];
  }

  const unusable = rows.filter((r) => UNUSABLE.includes(r.status));
  const matching = rows.filter((r) => (r.currency ?? '').toLowerCase() === currency);
  const def = matching.filter((r) => r.default_for_currency);

  if (def.length) {
    const bad = def.filter((r) => UNUSABLE.includes(r.status));
    if (bad.length) {
      return ['unusable',
        `the default destination for ${currency || '?'} has status ${bad[0].status}: ` +
        'scheduled payouts to it have stopped'];
    }
    return ['attached', `${rows.length} destination(s), default set for ${currency || '?'}`];
  }

  if (matching.length) {
    return ['no-default',
      `${matching.length} destination(s) in ${currency || '?'} but none marked ` +
      'default_for_currency: payouts have nowhere to go'];
  }

  if (unusable.length) {
    return ['unusable',
      `${rows.length} destination(s), all in a failed state (${unusable[0].status})`];
  }

  return ['wrong-currency',
    `${rows.length} destination(s), none of them in ` +
    `${currency || 'the account default currency'}, so the balance cannot be paid out`];
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

export async function* accounts(key, cap = 1000) {
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

  const counts = new Map();
  let scanned = 0;

  for await (const acct of accounts(key)) {
    scanned += 1;
    const id = acct.id ?? 'acct_?';
    const page = await get(key, `/accounts/${id}/external_accounts`, { limit: 100 });
    const [state, detail] = classify(page.data, acct.default_currency,
      acct.requirements?.currently_due);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'attached') continue;
    console.warn(`${id}  ${state.padEnd(17)} ` +
                 `payouts_enabled=${acct.payouts_enabled}  ${detail}`);
  }

  const missing = (counts.get('none') ?? 0) + (counts.get('none-unrequested') ?? 0);
  const noDefault = (counts.get('no-default') ?? 0) + (counts.get('wrong-currency') ?? 0);

  console.log(`${scanned} account(s): ${missing} with no destination, ${noDefault} ` +
              'with no default for their currency');

  if (counts.get('none')) {
    console.warn('  repair: send the seller an account link of type account_update ' +
                 'so they attach a bank account themselves');
  }
  if (counts.get('none-unrequested')) {
    console.warn('  repair: Dashboard, Settings, Connect, Payouts: re-enable external ' +
                 'account collection, or finish the flow that was going to collect it ' +
                 'in your own interface');
  }
  if (noDefault) {
    console.warn('  repair: mark one destination default_for_currency for the account ' +
                 'default_currency, or attach one in that currency');
  }
  if (counts.get('unusable')) {
    console.warn('  repair: attach fresh details. Editing the numbers on an errored ' +
                 'destination does not clear the status.');
  }
  if (missing || noDefault || counts.get('unusable')) {
    console.warn('  check: the balance on these accounts says how old this is:');
    console.warn(`  GET ${API}/balance  with the Stripe-Account header`);
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
"test_intro": "Two of these tests describe accounts that visibly have a bank account attached and still cannot be paid: one where nothing is marked default for the currency, one where every destination is in a currency the balance is not in. A row count alone passes both, which is why the classifier takes the currency rather than just the array.",
"test_py_file": "test_stripe_missing_external_account.py",
"test_py": '''from stripe_missing_external_account import classify


def test_a_default_destination_is_the_healthy_case():
    state, detail = classify(
        [{"currency": "usd", "default_for_currency": True, "status": "verified"}],
        "usd")
    assert state == "attached"
    assert "default set for usd" in detail


def test_nothing_attached_separates_asked_from_never_asked():
    # Stripe asking and nobody collecting is a broken handoff. Stripe not asking
    # means the platform turned collection off and never built the other half.
    state, _ = classify([], "usd", ["external_account", "company.tax_id"])
    assert state == "none"
    assert classify([], "usd", ["company.tax_id"])[0] == "none-unrequested"


def test_attached_but_no_default_still_cannot_pay_out():
    state, detail = classify(
        [{"currency": "usd", "default_for_currency": False, "status": "verified"}],
        "usd")
    assert state == "no-default"
    assert "nowhere to go" in detail


def test_a_destination_in_the_wrong_currency_is_not_a_destination():
    state, detail = classify(
        [{"currency": "eur", "default_for_currency": True, "status": "verified"}],
        "usd")
    assert state == "wrong-currency"
    assert "usd" in detail


def test_case_does_not_decide_the_answer():
    # Stripe returns lowercase currencies, but an account object copied through a
    # cache or a spreadsheet may not.
    assert classify(
        [{"currency": "USD", "default_for_currency": True, "status": "verified"}],
        "USD")[0] == "attached"


def test_an_errored_default_is_reported_as_frozen_not_healthy():
    state, detail = classify(
        [{"currency": "usd", "default_for_currency": True, "status": "errored"}],
        "usd")
    assert state == "unusable"
    assert "have stopped" in detail
''',
"test_js_file": "stripe-missing-external-account.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-missing-external-account.mjs';

test('a default destination is the healthy case', () => {
  const [state, detail] = classify(
    [{ currency: 'usd', default_for_currency: true, status: 'verified' }], 'usd');
  assert.equal(state, 'attached');
  assert.match(detail, /default set for usd/);
});

test('nothing attached separates asked from never asked', () => {
  // Stripe asking and nobody collecting is a broken handoff. Stripe not asking
  // means the platform turned collection off and never built the other half.
  assert.equal(classify([], 'usd', ['external_account', 'company.tax_id'])[0], 'none');
  assert.equal(classify([], 'usd', ['company.tax_id'])[0], 'none-unrequested');
});

test('attached but no default still cannot pay out', () => {
  const [state, detail] = classify(
    [{ currency: 'usd', default_for_currency: false, status: 'verified' }], 'usd');
  assert.equal(state, 'no-default');
  assert.match(detail, /nowhere to go/);
});

test('a destination in the wrong currency is not a destination', () => {
  const [state, detail] = classify(
    [{ currency: 'eur', default_for_currency: true, status: 'verified' }], 'usd');
  assert.equal(state, 'wrong-currency');
  assert.match(detail, /usd/);
});

test('case does not decide the answer', () => {
  // Stripe returns lowercase currencies, but an account object copied through a
  // cache or a spreadsheet may not.
  assert.equal(classify(
    [{ currency: 'USD', default_for_currency: true, status: 'verified' }], 'USD')[0],
  'attached');
});

test('an errored default is reported as frozen not healthy', () => {
  const [state, detail] = classify(
    [{ currency: 'usd', default_for_currency: true, status: 'errored' }], 'usd');
  assert.equal(state, 'unusable');
  assert.match(detail, /have stopped/);
});
''',
"faq": [
 ("How can an account finish onboarding with no bank account?",
  "Because external account collection can be turned off on the platform, which is the supported way to say the platform will gather bank details itself. Stripe then stops asking, the account reaches details_submitted true, and the only thing standing between the seller and their money is a flow on your side that may never have been finished."),
 ("Why are there no failed payouts to look at?",
  "Because none were attempted. Automatic payouts need a destination; with none, Stripe does not create a payout object at all. Everything downstream that watches for failures is watching a list that stays empty, which is indistinguishable from everything working."),
 ("What does default_for_currency actually control?",
  "Which destination receives payouts for a given currency. An account can hold several external accounts, and only the one flagged default for the balance's currency gets used. A seller with a bank account attached in the wrong currency, or with none flagged, is in exactly the same position as a seller with none at all."),
 ("How do I know how long this has been going on?",
  "Read the account's balance with the Stripe-Account header. The size of the available balance is a direct proxy for how many payout cycles have been skipped, and it is the number that decides whether this is a quiet bug fix or a call with a seller."),
 ("Can this script attach the bank account for me?",
  "No, deliberately. Attaching an external account moves where money goes, which is the single most dangerous write in a payments integration, and it is not something an unattended monitor holding a long-lived key should be able to do. The script names the accounts and prints the two ways to collect the details."),
],
"related": [
 ("/stripe/payouts-failing-bank-rejection/", "Payouts fail with account_closed and nobody is watching"),
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/missing-payout-failed/", "payout.failed is unsubscribed so broken bank details go unseen"),
],
"citations": [CITE_EXTERNAL_ACCOUNT, CITE_HOSTED_ONBOARDING, CITE_ACCOUNT_OBJECT, CITE_KEYS],
},

]
