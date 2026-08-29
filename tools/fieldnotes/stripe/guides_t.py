#!/usr/bin/env python3
"""/stripe/ field notes, batch T — the writing.

Checkout and Payment Links again, but the four failures that happen *after* the
customer has finished: the Session that kept nobody, the lapse nobody can mail,
the return leg with no destination, and the link whose flow ends on Stripe's own
page. Same constraint as the rest of the section: every note here is a problem a
script can find with a RESTRICTED, READ-ONLY Stripe key. None of these scripts
writes. They read, they say exactly what is wrong, and they print the repair for
a human to run against a live payments account.
"""

CITE_SESSION_OBJ = ("The Checkout Session object — Stripe API reference",
                    "https://docs.stripe.com/api/checkout/sessions/object")
CITE_SESSION_CREATE = ("Create a Checkout Session — Stripe API reference",
                       "https://docs.stripe.com/api/checkout/sessions/create")
CITE_CUSTOMER_OBJ = ("The Customer object — Stripe API reference",
                     "https://docs.stripe.com/api/customers/object")
CITE_ABANDONED = ("Recover abandoned carts — Stripe Docs",
                  "https://docs.stripe.com/payments/checkout/abandoned-carts")
CITE_EVENT_TYPES = ("Types of events — Stripe API reference",
                    "https://docs.stripe.com/api/events/types")
CITE_FULFILMENT = ("Fulfill orders after checkout — Stripe Docs",
                   "https://docs.stripe.com/checkout/fulfillment")
CITE_EMBEDDED = ("Embedded Checkout quickstart — Stripe Docs",
                 "https://docs.stripe.com/checkout/embedded/quickstart")
CITE_LINK_OBJ = ("The Payment Link object — Stripe API reference",
                 "https://docs.stripe.com/api/payment-link/object")
CITE_LINK_CREATE = ("Create a payment link — Stripe API reference",
                    "https://docs.stripe.com/api/payment-link/create")
CITE_LINK_UPDATE = ("Update a payment link — Stripe API reference",
                    "https://docs.stripe.com/api/payment-link/update")
CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")

GUIDES = [

{
"slug": "checkout-guest-customer-null",
"title": "Guest checkouts finish with customer null and can't be linked",
"description": "customer_creation defaults to if_required, so payment-mode Sessions complete with customer null and the email stays a string on the Session.",
"h1": "guest checkouts finish with customer null and can't be linked",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe checkout customer null", "stripe customer_creation always",
             "stripe guest checkout customer", "checkout session customer_details email",
             "stripe repeat customer not linked"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody writes in asking for a copy of a receipt from March. You search the Dashboard for their email address and find four separate payments, no Customer record, no purchase history, and nothing you can open the Billing Portal against. Every one of those four checkouts completed perfectly. None of them left behind anything that ties the four together.",
"short_answer": """<p>Page <code>GET /v1/checkout/sessions?status=complete&amp;created[gte]=&lt;now-90d&gt;</code> and count the sessions where <code>mode == "payment"</code> and <code>customer</code> is <code>null</code>. That is the default outcome, not a bug: <code>customer_creation</code> defaults to <code>if_required</code>, and Stripe only <em>requires</em> a Customer in <code>subscription</code> mode and in <code>payment</code> mode with post-purchase invoices enabled.</p>
<p>Group those guests by <code>customer_details.email</code>. Any address appearing more than once is a repeat buyer your account meets as a stranger every time. Fix it at creation with <code>customer_creation=always</code>, or by passing an existing <code>customer=cus_...</code>; on a Payment Link, set <code>customer_creation</code> on the link itself.</p>""",
"problem": """<p>Guest checkout is usually a deliberate decision, and a good one: fewer fields, no account, a higher completion rate. The cost lands nowhere near the checkout. It lands afterwards, in every question that starts with "this customer".</p>
<p>You cannot show a purchase history, because there is no object to hang one on. You cannot open the Billing Portal, because a portal session is created against a Customer id and you do not have one. Lifetime value, refund history and repeat-purchase rate are all unqueryable from Stripe, because the only thing linking the payments is an email address sitting as a plain string on each Session. Support ends up doing by hand what the API was supposed to do, and does it with an amount, a date and a guess.</p>""",
"why": """<p><strong>The default is named as if it described your business, and it describes Stripe's mechanics.</strong> <code>if_required</code> reads like "we will make one if it is needed". What it actually means is "if the Session cannot function without one" &mdash; a subscription, or a payment-mode session with post-purchase invoices. Needing a Customer to answer a support email is not part of that test, so the answer is always no.</p>
<p><strong>Nothing about the checkout looks different.</strong> The Session completes, the payment succeeds, and Stripe emails a receipt to the address in <code>customer_details.email</code>. A receipt going out feels like proof that a customer exists somewhere. It is not: that field is a string, not a reference.</p>
<p><strong>The email looks like a Customer and behaves like a label.</strong> It has no id, so no <code>GET /v1/customers</code> lookup finds it, no portal session can be created from it, and nothing prevents the same human from having three spellings of it across three purchases. It is a hint, not a join.</p>
<p><strong>It is only really fixable going forward.</strong> You can create Customers from the addresses you have, but the Sessions that already completed keep <code>customer: null</code>, and the merge you would do is exactly the email-matching guess that made this a problem. Every week the flag stays on the default is another week of payments that will never link to anyone.</p>""",
"steps": [
 {"h": "Page the completed sessions for a window you believe in",
  "body": """<p><code>GET /v1/checkout/sessions?status=complete&amp;created[gte]=&lt;unix&gt;&amp;limit=100</code>, paginated. Ninety days is long enough for repeat buyers to actually repeat, which is the number that makes the argument, and short enough that it describes the code running today.</p>"""},
 {"h": "Split by mode before you count anything",
  "body": """<p>Subscription-mode sessions always have a Customer, because Stripe cannot run a subscription without one. Mixing them into the denominator makes the guest ratio look better on accounts that sell both, which are the accounts where this matters most.</p>"""},
 {"h": "Group the guests by customer_details.email",
  "body": """<p>One address, several completed sessions, no Customer on any of them. That is the finding worth putting in front of someone: not "we create guest checkouts" but "142 people bought from us more than once this quarter and we recognised none of them".</p>"""},
 {"h": "Treat a guest with no email at all as its own case",
  "body": """<p>A guest session you can still match on an address is recoverable by hand later. One with neither a Customer nor an email is not recoverable by any means at all, and a check that folds it in with the rest hides the only truly permanent loss on the report.</p>"""},
 {"h": "Set customer_creation at creation, or pass the customer you already know",
  "body": """<p><code>customer_creation=always</code> makes Stripe create the Customer. If the buyer is signed in and you already hold a <code>cus_</code> id, pass <code>customer</code> instead &mdash; that links the payment to the record you have rather than making a second one beside it.</p>"""},
 {"h": "Fix Payment Links on the link, once",
  "body": """<p>A link has no per-purchase code path to set anything in, so the setting lives on the link and every Session it creates inherits it. Links are usually the worst offenders on the report for exactly that reason: nobody has ever written a line of code near them.</p>"""},
 {"h": "Re-run monthly and watch the repeat count",
  "body": """<p>The guest count falls slowly as old sessions age out of the window. The number that should move immediately is repeat guests, because after the change a returning buyer is matched to the Customer created on their first visit.</p>"""},
],
"verify": """<p>Re-run after the change. New completed sessions should report <code>linked</code>, and the repeat-guest count should fall as the old window ages out.</p>
<pre><code class="language-bash">python3 stripe_checkout_guests.py --days 30
# 214 session(s): 214 linked, 0 guest, 0 repeat-guest, 0 anonymous</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/checkout/sessions</code> and no writes. The classifier is pure and takes the number of sessions in the window sharing this one's email, because the difference between a genuine one-off guest and a repeat buyer you fail to recognise every time is the entire argument for changing the flag, and it is not visible on a single Session.",
"py_file": "stripe_checkout_guests.py",
"py": '''"""Report Stripe Checkout Sessions that completed without a Customer.

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
log = logging.getLogger("stripe_checkout_guests")

API = "https://api.stripe.com/v1"


def verdict(session, email_seen=1):
    """Classify one completed Checkout Session. Pure, so the rules can be tested
    offline.

    `email_seen` is how many sessions in the window share this session's
    customer_details.email. A single Session cannot tell you whether its buyer
    has been here before, and that is the fact the whole report turns on.
    Returns (state, detail).
    """
    if session.get("customer"):
        return ("linked", "customer=%s" % (session["customer"],))

    mode = session.get("mode")
    if mode != "payment":
        return ("unknown",
                "mode %r completed with no Customer, which Stripe normally "
                "requires here" % (mode,))

    creation = session.get("customer_creation")
    if creation == "always":
        return ("unknown",
                "customer_creation=always but no Customer is attached; check the "
                "session really completed")

    email = str((session.get("customer_details") or {}).get("email") or "").strip()
    if not email:
        return ("anonymous",
                "no Customer and no customer_details.email: nothing at all to "
                "match this payment to later")
    if email_seen > 1:
        return ("repeat-guest",
                "%s completed %d sessions in this window and was a new stranger "
                "every time" % (email, email_seen))
    return ("guest",
            "customer_creation=%r, so Stripe made no Customer; %s exists only as "
            "a string on the Session" % (creation, email))


def email_of(session):
    """The address a guest session could later be matched on, normalised."""
    return str((session.get("customer_details") or {}).get("email") or "").strip().lower()


def email_counts(sessions):
    """Count how many sessions share each address. Pure, and used before any
    session is classified, because the count is an argument to the classifier."""
    counts = {}
    for s in sessions:
        addr = email_of(s)
        if addr:
            counts[addr] = counts.get(addr, 0) + 1
    return counts


def get(http, path, params=None):
    r = http.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def completed_sessions(http, since, limit):
    """Yield completed Checkout Sessions created since `since`, newest first."""
    seen = 0
    params = {"limit": 100, "status": "complete", "created[gte]": int(since)}
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
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to read completed sessions")
    ap.add_argument("--max-sessions", type=int, default=5000,
                    help="stop paginating after this many sessions")
    ap.add_argument("--show", type=int, default=10,
                    help="how many repeat guests to print")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    http = requests.Session()
    http.headers.update({"Authorization": "Bearer " + key})

    since = time.time() - args.days * 86400
    sessions = list(completed_sessions(http, since, args.max_sessions))
    if not sessions:
        log.info("no completed Checkout Sessions in the last %d days", args.days)
        return 0

    counts = email_counts(sessions)
    tally = {"linked": 0, "guest": 0, "repeat-guest": 0, "anonymous": 0, "unknown": 0}
    repeats = []
    for s in sessions:
        state, detail = verdict(s, counts.get(email_of(s), 1))
        tally[state] = tally.get(state, 0) + 1
        if state == "repeat-guest" and len(repeats) < args.show:
            repeats.append((s.get("id", "?"), detail))

    log.info("%d session(s): %d linked, %d guest, %d repeat-guest, %d anonymous",
             len(sessions), tally["linked"], tally["guest"],
             tally["repeat-guest"], tally["anonymous"])
    for sid, detail in repeats:
        log.warning("repeat-guest  %s  %s", sid, detail)
    if tally["unknown"]:
        log.warning("%d session(s) in an unexpected state; read them by hand",
                    tally["unknown"])

    unlinked = tally["guest"] + tally["repeat-guest"] + tally["anonymous"]
    if unlinked:
        log.warning("  repair: POST %s/checkout/sessions -d customer_creation=always",
                    API)
        log.warning("          or pass the id you already hold: -d customer=cus_XXX")
        log.warning("  for a Payment Link, set it on the link: POST "
                    "%s/payment_links/plink_XXX -d customer_creation=always", API)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-checkout-guests.mjs",
"js": '''/**
 * Report Stripe Checkout Sessions that completed without a Customer.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Checkout Sessions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one completed Checkout Session. Pure, so the rules can be tested
 * offline. `emailSeen` is how many sessions in the window share this session's
 * customer_details.email.
 */
export function verdict(session, emailSeen = 1) {
  if (session.customer) return ['linked', `customer=${session.customer}`];

  const mode = session.mode;
  if (mode !== 'payment') {
    return ['unknown',
      `mode ${JSON.stringify(mode)} completed with no Customer, which Stripe ` +
      'normally requires here'];
  }

  const creation = session.customer_creation;
  if (creation === 'always') {
    return ['unknown',
      'customer_creation=always but no Customer is attached; check the session ' +
      'really completed'];
  }

  const email = String(session.customer_details?.email ?? '').trim();
  if (!email) {
    return ['anonymous',
      'no Customer and no customer_details.email: nothing at all to match this ' +
      'payment to later'];
  }
  if (emailSeen > 1) {
    return ['repeat-guest',
      `${email} completed ${emailSeen} sessions in this window and was a new ` +
      'stranger every time'];
  }
  return ['guest',
    `customer_creation=${JSON.stringify(creation)}, so Stripe made no Customer; ` +
    `${email} exists only as a string on the Session`];
}

/** The address a guest session could later be matched on, normalised. */
export function emailOf(session) {
  return String(session.customer_details?.email ?? '').trim().toLowerCase();
}

/** Count how many sessions share each address. Pure. */
export function emailCounts(sessions) {
  const counts = new Map();
  for (const s of sessions) {
    const addr = emailOf(s);
    if (addr) counts.set(addr, (counts.get(addr) ?? 0) + 1);
  }
  return counts;
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

export async function* completedSessions(key, since, limit = 5000) {
  let seen = 0;
  const params = { limit: 100, status: 'complete', 'created[gte]': Math.floor(since) };
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

  const days = Number(process.argv[2] ?? 90);
  const sessions = [];
  for await (const s of completedSessions(key, Date.now() / 1000 - days * 86400)) {
    sessions.push(s);
  }
  if (sessions.length === 0) {
    console.log(`no completed Checkout Sessions in the last ${days} days`);
    return;
  }

  const counts = emailCounts(sessions);
  const tally = { linked: 0, guest: 0, 'repeat-guest': 0, anonymous: 0, unknown: 0 };
  const repeats = [];
  for (const s of sessions) {
    const [state, detail] = verdict(s, counts.get(emailOf(s)) ?? 1);
    tally[state] = (tally[state] ?? 0) + 1;
    if (state === 'repeat-guest' && repeats.length < 10) {
      repeats.push([s.id ?? '?', detail]);
    }
  }

  console.log(`${sessions.length} session(s): ${tally.linked} linked, ` +
              `${tally.guest} guest, ${tally['repeat-guest']} repeat-guest, ` +
              `${tally.anonymous} anonymous`);
  for (const [id, detail] of repeats) console.warn(`repeat-guest  ${id}  ${detail}`);
  if (tally.unknown) {
    console.warn(`${tally.unknown} session(s) in an unexpected state; read them by hand`);
  }

  if (tally.guest + tally['repeat-guest'] + tally.anonymous) {
    console.warn(`  repair: POST ${API}/checkout/sessions -d customer_creation=always`);
    console.warn('          or pass the id you already hold: -d customer=cus_XXX');
    console.warn('  for a Payment Link, set it on the link: POST ' +
                 `${API}/payment_links/plink_XXX -d customer_creation=always`);
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
"test_intro": "The case worth pinning is the repeat guest. A per-session check cannot see it &mdash; every one of those sessions is individually unremarkable &mdash; and it is the only state on the report that says the flag is costing you something today rather than in theory. The session with no email at all gets its own test for the opposite reason: it is rare, permanent, and easy to fold in with the recoverable ones by accident.",
"test_py_file": "test_stripe_checkout_guests.py",
"test_py": '''from stripe_checkout_guests import email_counts, verdict


def make(email=None, **kw):
    s = {"mode": "payment", "customer_creation": "if_required"}
    if email is not None:
        s["customer_details"] = {"email": email}
    s.update(kw)
    return s


def test_a_session_with_a_customer_is_linked():
    state, detail = verdict(make("a@example.com", customer="cus_9"))
    assert state == "linked"
    assert "cus_9" in detail


def test_the_default_flag_produces_a_guest():
    state, detail = verdict(make("a@example.com"))
    assert state == "guest"
    assert "if_required" in detail


def test_the_same_address_twice_is_a_repeat_guest():
    # The point of the note: no single session shows this, only the window does.
    sessions = [make("buyer@example.com"), make("BUYER@example.com")]
    counts = email_counts(sessions)
    state, detail = verdict(sessions[0], counts["buyer@example.com"])
    assert state == "repeat-guest"
    assert "2" in detail


def test_a_guest_with_no_email_is_not_merely_a_guest():
    assert verdict(make())[0] == "anonymous"
    assert verdict(make("   "))[0] == "anonymous"


def test_subscription_mode_and_always_are_not_silently_guests():
    assert verdict(make("a@example.com", mode="subscription"))[0] == "unknown"
    assert verdict(make("a@example.com", customer_creation="always"))[0] == "unknown"
''',
"test_js_file": "stripe-checkout-guests.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emailCounts, verdict } from './stripe-checkout-guests.mjs';

const make = (email, extra = {}) => ({
  mode: 'payment',
  customer_creation: 'if_required',
  ...(email === undefined ? {} : { customer_details: { email } }),
  ...extra,
});

test('a session with a customer is linked', () => {
  const [state, detail] = verdict(make('a@example.com', { customer: 'cus_9' }));
  assert.equal(state, 'linked');
  assert.match(detail, /cus_9/);
});

test('the default flag produces a guest', () => {
  const [state, detail] = verdict(make('a@example.com'));
  assert.equal(state, 'guest');
  assert.match(detail, /if_required/);
});

test('the same address twice is a repeat guest', () => {
  const sessions = [make('buyer@example.com'), make('BUYER@example.com')];
  const counts = emailCounts(sessions);
  const [state, detail] = verdict(sessions[0], counts.get('buyer@example.com'));
  assert.equal(state, 'repeat-guest');
  assert.match(detail, /2/);
});

test('a guest with no email is not merely a guest', () => {
  assert.equal(verdict(make())[0], 'anonymous');
  assert.equal(verdict(make('   '))[0], 'anonymous');
});

test('subscription mode and always are not silently guests', () => {
  assert.equal(verdict(make('a@example.com', { mode: 'subscription' }))[0], 'unknown');
  assert.equal(
    verdict(make('a@example.com', { customer_creation: 'always' }))[0], 'unknown');
});
''',
"faq": [
 ("Stripe emailed a receipt, so surely there is a customer somewhere?",
  "No. The receipt goes to customer_details.email, which is a string recorded on the Checkout Session. It has no id, it is not an object, and nothing in /v1/customers will return it. A receipt proves an address was collected, not that a Customer was created."),
 ("What does customer_creation=if_required actually require?",
  "Stripe's own mechanics, not your business needs. A Customer is required in subscription mode, and in payment mode when post-purchase invoices are enabled. Everything else completes with customer null, which is why the default silently produces guests on a plain one-off purchase."),
 ("Why can't I open the Billing Portal for these buyers?",
  "A portal session is created against a Customer id. A guest checkout never produced one, so there is nothing to pass. Creating a Customer now does not retroactively attach the payments that already happened, which is why the flag matters more than the backfill."),
 ("Can I backfill Customers for the guest checkouts I already have?",
  "You can create Customers from the addresses you collected, but the completed Sessions keep customer null and the join you would make is the same email match support is already doing by hand. Treat it as fixable going forward, and reconcile the historical window once, deliberately."),
 ("How do I set this on a Payment Link?",
  "Set customer_creation on the link itself with POST /v1/payment_links/{plink_id} -d customer_creation=always. Every Checkout Session the link creates inherits it, which is the only place to fix it because a link has no per-purchase code path of its own."),
],
"related": [
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
 ("/stripe/duplicate-customers-same-email/", "Duplicate customers share an email and split billing"),
 ("/stripe/billing-portal-no-configuration/", "The Billing Portal has no configuration and will not open"),
],
"citations": [CITE_SESSION_OBJ, CITE_SESSION_CREATE, CITE_LINK_CREATE, CITE_CUSTOMER_OBJ],
},

{
"slug": "checkout-recovery-never-enabled",
"title": "Expired Checkout Sessions are never recovered by email",
"description": "Recovery is opt-in per session. Without after_expiration[recovery], the expired event carries no recovery URL, so there is nothing to send anyone.",
"h1": "expired Checkout Sessions are never recovered by email",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe abandoned cart recovery", "after_expiration recovery enabled",
             "checkout.session.expired recovery url", "stripe recovered_from",
             "stripe checkout recovery email"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody asks why there is no abandoned-cart email. The answer is not that nobody built one. It is that there is nothing to send: Checkout will mint a recovery link for every session that lapses, but only for sessions created with recovery switched on, and switching it on afterwards does nothing at all.",
"short_answer": """<p>Page <code>GET /v1/checkout/sessions?status=expired&amp;created[gte]=&lt;now-60d&gt;</code> and count the sessions where <code>after_expiration</code> is <code>null</code> or <code>after_expiration.recovery.enabled</code> is <code>false</code>. Those lapsed with no recovery URL and no way to mint one now.</p>
<p>Then page the completed sessions in the same window and count <code>recovered_from</code>. A non-trivial expired population with zero <code>recovered_from</code> means no cart has ever been recovered, whatever the configuration says. Fix it at creation with <code>after_expiration[recovery][enabled]=true</code> and <code>consent_collection[promotions]=auto</code>, then mail <code>after_expiration.recovery.url</code> when you handle <code>checkout.session.expired</code>.</p>""",
"problem": """<p>Abandoned carts get written off wholesale, and the reason given is usually that recovery emails are a project. They are not: Checkout builds the link, keeps it alive for 30 days, and tells you which recovered session came from which original. The project is one parameter and one event handler.</p>
<p>What makes this worth checking rather than assuming is that the config is per session, set at creation, and invisible everywhere else. A team can decide to do recovery, write the email, wire the handler, deploy it, and discover that every incoming <code>checkout.session.expired</code> payload has <code>after_expiration.recovery.url</code> of <code>null</code>, because the sessions were created by a code path nobody changed.</p>""",
"why": """<p><strong>Recovery is opt-in on the session, not on the account.</strong> There is no Dashboard switch that turns it on everywhere. It is a parameter passed at <code>POST /v1/checkout/sessions</code>, which means it is as easy to miss as any other optional field, and it can be present on the sessions one service creates and absent on the ones another creates.</p>
<p><strong>The recovery URL does not exist until the session lapses, and cannot be added after.</strong> It appears on the expired session only if recovery was enabled at creation. An expired session without it is finished: there is no endpoint that mints a recovery link retroactively, and no amount of fixing the flag today helps the sessions that lapsed yesterday.</p>
<p><strong>The link has its own expiry, and it is not the session's.</strong> <code>after_expiration.recovery.expires_at</code> is 30 days from the lapse. A batch job that mails weekly, or a queue that stalls, can hold perfectly valid recovery links until they are dead, and the send will look like it worked.</p>
<p><strong>Consent is a separate field from recovery, and it is the one that stops you.</strong> <code>consent_collection.promotions</code> controls whether the customer is even asked; <code>consent.promotions</code> records what they answered. Recovery enabled without consent collection produces a working URL for an address you have no permission to market to, which is a worse position than having nothing, because it looks like a green light.</p>""",
"steps": [
 {"h": "Page the expired sessions over 60 days",
  "body": """<p><code>GET /v1/checkout/sessions?status=expired&amp;created[gte]=&lt;unix&gt;&amp;limit=100</code>. Sixty days is deliberate: it is twice the life of a recovery URL, so the report shows both the links you could still use and the ones that quietly went past their own expiry.</p>"""},
 {"h": "Classify each lapse rather than counting them",
  "body": """<p>Four outcomes matter and they need different work. No recovery configured is a code change. A lapsed URL is a scheduling problem. A live URL with no consent is a legal one. A live URL with consent is a send you have not made.</p>"""},
 {"h": "Ask whether a single recovery has ever landed",
  "body": """<p>A session created from a recovery URL carries <code>recovered_from</code> pointing at the original. Count them across completed sessions in the window. That count is the only end-to-end proof the loop closes; configuration says what should happen, <code>recovered_from</code> says what did.</p>"""},
 {"h": "Turn recovery and consent on together",
  "body": """<p>Enabling recovery without collecting consent gets you links you cannot use. Set both at creation and the expired payload arrives with a URL and a recorded answer, so the handler has everything it needs to decide whether to send.</p>"""},
 {"h": "Handle checkout.session.expired and read the URL from the payload",
  "body": """<p>The event is the trigger and the payload already carries <code>after_expiration.recovery.url</code> and <code>customer_details.email</code>. There is no second lookup to do. If nothing is subscribed to the event, subscribe it first &mdash; the sessions lapse whether or not anybody is listening.</p>"""},
 {"h": "Check expires_at before every send, not at queue time",
  "body": """<p>Thirty days is generous until a mail job runs weekly and retries twice. Comparing <code>after_expiration.recovery.expires_at</code> to the clock at send time costs nothing and stops you mailing dead links, which convert at zero and look like recovery not working.</p>"""},
],
"verify": """<p>Re-run after the change. New lapses should report <code>recoverable</code>, and the <code>recovered_from</code> count should stop being zero.</p>
<pre><code class="language-bash">python3 stripe_checkout_recovery.py --days 30
# 96 expired: 0 no-recovery, 0 lapsed, 0 no-consent, 96 recoverable
# 12 completed session(s) carry recovered_from</code></pre>""",
"code_intro": "Two paginated GETs and no writes: expired sessions to classify, completed sessions to count <code>recovered_from</code>. The classifier is pure and takes the current time as an argument rather than reading the clock, because the whole point of the <code>lapsed</code> state is a boundary, and a boundary you cannot pin in a test is a boundary you find out about in production.",
"py_file": "stripe_checkout_recovery.py",
"py": '''"""Report expired Stripe Checkout Sessions that can never be recovered by email.

Read only. Two paginated GETs and no writes: give this a RESTRICTED key with read
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
log = logging.getLogger("stripe_checkout_recovery")

API = "https://api.stripe.com/v1"


def verdict(session, now):
    """Classify one expired Checkout Session. Pure, so the rules can be tested
    offline.

    `now` is unix seconds, passed in rather than read, so the recovery URL's own
    expiry boundary can be pinned in a test.
    Returns (state, detail).
    """
    recovery = (session.get("after_expiration") or {}).get("recovery") or {}
    if not recovery.get("enabled"):
        return ("no-recovery",
                "after_expiration[recovery][enabled] was not set at creation, so "
                "this lapse has no recovery url and never will")

    url = str(recovery.get("url") or "").strip()
    if not url:
        return ("unknown",
                "recovery is enabled but no url is present on an expired session")

    expires_at = recovery.get("expires_at")
    if expires_at is not None and expires_at <= now:
        return ("lapsed",
                "the recovery url expired %.1f day(s) ago; mailing it now sends "
                "the customer to a dead link" % ((now - expires_at) / 86400.0))

    left = ((expires_at - now) / 86400.0) if expires_at is not None else float("nan")
    consent = (session.get("consent") or {}).get("promotions")
    if consent != "opt_in":
        return ("no-consent",
                "the recovery url is live for %.1f more day(s), but "
                "consent.promotions is %r: there is no recorded permission to "
                "mail this address" % (left, consent))

    return ("recoverable",
            "the recovery url is live for %.1f more day(s) and the customer "
            "opted in" % (left,))


def get(http, path, params=None):
    r = http.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def sessions_with_status(http, status, since, limit):
    """Yield Checkout Sessions with `status` created since `since`, newest first."""
    seen = 0
    params = {"limit": 100, "status": status, "created[gte]": int(since)}
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
    ap.add_argument("--days", type=int, default=60,
                    help="how far back to read sessions")
    ap.add_argument("--max-sessions", type=int, default=5000,
                    help="stop paginating after this many sessions per status")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    http = requests.Session()
    http.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    since = now - args.days * 86400

    tally = {"no-recovery": 0, "lapsed": 0, "no-consent": 0,
             "recoverable": 0, "unknown": 0}
    expired = 0
    for s in sessions_with_status(http, "expired", since, args.max_sessions):
        expired += 1
        state, _ = verdict(s, now)
        tally[state] = tally.get(state, 0) + 1

    recovered = 0
    completed = 0
    for s in sessions_with_status(http, "complete", since, args.max_sessions):
        completed += 1
        if s.get("recovered_from"):
            recovered += 1

    log.info("%d expired: %d no-recovery, %d lapsed, %d no-consent, %d recoverable",
             expired, tally["no-recovery"], tally["lapsed"], tally["no-consent"],
             tally["recoverable"])
    log.info("%d completed session(s), %d carrying recovered_from",
             completed, recovered)

    if tally["no-recovery"]:
        log.warning("  repair: POST %s/checkout/sessions "
                    "-d 'after_expiration[recovery][enabled]=true' "
                    "-d 'consent_collection[promotions]=auto'", API)
    if tally["no-consent"]:
        log.warning("  recovery urls exist but consent.promotions is not opt_in; "
                    "add -d 'consent_collection[promotions]=auto' at creation")
    if tally["lapsed"]:
        log.warning("  recovery urls went past after_expiration.recovery.expires_at "
                    "before anything sent them; check expires_at at send time")
    if expired and not recovered:
        log.warning("  no completed session carries recovered_from: nothing has "
                    "ever come back through a recovery url")
        log.warning("  subscribe checkout.session.expired and mail "
                    "after_expiration.recovery.url to customer_details.email")

    return 1 if (tally["no-recovery"] or tally["lapsed"] or tally["no-consent"]) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-checkout-recovery.mjs",
"js": '''/**
 * Report expired Stripe Checkout Sessions that can never be recovered by email.
 *
 * Read only. Two paginated GETs and no writes: give this a RESTRICTED key with
 * read access to Checkout Sessions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one expired Checkout Session. Pure, so the rules can be tested
 * offline. `now` is unix seconds, passed in rather than read, so the recovery
 * URL's own expiry boundary can be pinned in a test.
 */
export function verdict(session, now) {
  const recovery = session.after_expiration?.recovery ?? {};
  if (!recovery.enabled) {
    return ['no-recovery',
      'after_expiration[recovery][enabled] was not set at creation, so this ' +
      'lapse has no recovery url and never will'];
  }

  const url = String(recovery.url ?? '').trim();
  if (!url) {
    return ['unknown',
      'recovery is enabled but no url is present on an expired session'];
  }

  const expiresAt = recovery.expires_at;
  if (expiresAt != null && expiresAt <= now) {
    const ago = ((now - expiresAt) / 86400).toFixed(1);
    return ['lapsed',
      `the recovery url expired ${ago} day(s) ago; mailing it now sends the ` +
      'customer to a dead link'];
  }

  const left = expiresAt == null ? NaN : ((expiresAt - now) / 86400);
  const consent = session.consent?.promotions;
  if (consent !== 'opt_in') {
    return ['no-consent',
      `the recovery url is live for ${left.toFixed(1)} more day(s), but ` +
      `consent.promotions is ${JSON.stringify(consent)}: there is no recorded ` +
      'permission to mail this address'];
  }

  return ['recoverable',
    `the recovery url is live for ${left.toFixed(1)} more day(s) and the ` +
    'customer opted in'];
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

export async function* sessionsWithStatus(key, status, since, limit = 5000) {
  let seen = 0;
  const params = { limit: 100, status, 'created[gte]': Math.floor(since) };
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

  const days = Number(process.argv[2] ?? 60);
  const now = Date.now() / 1000;
  const since = now - days * 86400;

  const tally = { 'no-recovery': 0, lapsed: 0, 'no-consent': 0, recoverable: 0, unknown: 0 };
  let expired = 0;
  for await (const s of sessionsWithStatus(key, 'expired', since)) {
    expired += 1;
    const [state] = verdict(s, now);
    tally[state] = (tally[state] ?? 0) + 1;
  }

  let completed = 0;
  let recovered = 0;
  for await (const s of sessionsWithStatus(key, 'complete', since)) {
    completed += 1;
    if (s.recovered_from) recovered += 1;
  }

  console.log(`${expired} expired: ${tally['no-recovery']} no-recovery, ` +
              `${tally.lapsed} lapsed, ${tally['no-consent']} no-consent, ` +
              `${tally.recoverable} recoverable`);
  console.log(`${completed} completed session(s), ${recovered} carrying recovered_from`);

  if (tally['no-recovery']) {
    console.warn(`  repair: POST ${API}/checkout/sessions ` +
                 `-d 'after_expiration[recovery][enabled]=true' ` +
                 `-d 'consent_collection[promotions]=auto'`);
  }
  if (tally['no-consent']) {
    console.warn('  recovery urls exist but consent.promotions is not opt_in; ' +
                 "add -d 'consent_collection[promotions]=auto' at creation");
  }
  if (tally.lapsed) {
    console.warn('  recovery urls went past after_expiration.recovery.expires_at ' +
                 'before anything sent them; check expires_at at send time');
  }
  if (expired && !recovered) {
    console.warn('  no completed session carries recovered_from: nothing has ever ' +
                 'come back through a recovery url');
    console.warn('  subscribe checkout.session.expired and mail ' +
                 'after_expiration.recovery.url to customer_details.email');
  }

  process.exitCode =
    (tally['no-recovery'] || tally.lapsed || tally['no-consent']) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. A recovery URL that is live but has no recorded consent looks like success from every angle except the only one that matters, and a URL that went past its own 30-day expiry while sitting in a mail queue is indistinguishable from a working one unless something compares it to the clock. Both are pinned here, with the boundary passed in rather than read.",
"test_py_file": "test_stripe_checkout_recovery.py",
"test_py": '''from stripe_checkout_recovery import verdict

NOW = 1_700_000_000
DAY = 86400


def expired_session(**recovery):
    """An expired Session with recovery enabled unless told otherwise."""
    base = {"enabled": True, "url": "https://checkout.stripe.com/c/pay/cs_test_x",
            "expires_at": NOW + 10 * DAY}
    base.update(recovery)
    return {"after_expiration": {"recovery": base},
            "consent": {"promotions": "opt_in"}}


def test_recovery_never_enabled_is_the_default_finding():
    state, detail = verdict({}, NOW)
    assert state == "no-recovery"
    assert "never will" in detail


def test_live_url_with_consent_is_recoverable():
    state, detail = verdict(expired_session(), NOW)
    assert state == "recoverable"
    assert "10.0" in detail


def test_a_url_past_its_own_expiry_is_not_recoverable():
    # 30 days from the lapse, not from the session: a weekly mail job can miss it.
    state, detail = verdict(expired_session(expires_at=NOW - 2 * DAY), NOW)
    assert state == "lapsed"
    assert "2.0" in detail


def test_a_live_url_without_consent_is_its_own_state():
    session = expired_session()
    session["consent"] = {"promotions": None}
    state, detail = verdict(session, NOW)
    assert state == "no-consent"
    assert "permission" in detail


def test_enabled_but_urlless_is_not_silently_recoverable():
    assert verdict(expired_session(url=None), NOW)[0] == "unknown"
    assert verdict(expired_session(url="  "), NOW)[0] == "unknown"
''',
"test_js_file": "stripe-checkout-recovery.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-checkout-recovery.mjs';

const NOW = 1_700_000_000;
const DAY = 86400;

const expiredSession = (recovery = {}) => ({
  after_expiration: {
    recovery: {
      enabled: true,
      url: 'https://checkout.stripe.com/c/pay/cs_test_x',
      expires_at: NOW + 10 * DAY,
      ...recovery,
    },
  },
  consent: { promotions: 'opt_in' },
});

test('recovery never enabled is the default finding', () => {
  const [state, detail] = verdict({}, NOW);
  assert.equal(state, 'no-recovery');
  assert.match(detail, /never will/);
});

test('live url with consent is recoverable', () => {
  const [state, detail] = verdict(expiredSession(), NOW);
  assert.equal(state, 'recoverable');
  assert.match(detail, /10\\.0/);
});

test('a url past its own expiry is not recoverable', () => {
  const [state, detail] = verdict(expiredSession({ expires_at: NOW - 2 * DAY }), NOW);
  assert.equal(state, 'lapsed');
  assert.match(detail, /2\\.0/);
});

test('a live url without consent is its own state', () => {
  const session = expiredSession();
  session.consent = { promotions: null };
  const [state, detail] = verdict(session, NOW);
  assert.equal(state, 'no-consent');
  assert.match(detail, /permission/);
});

test('enabled but urlless is not silently recoverable', () => {
  assert.equal(verdict(expiredSession({ url: null }), NOW)[0], 'unknown');
  assert.equal(verdict(expiredSession({ url: '  ' }), NOW)[0], 'unknown');
});
''',
"faq": [
 ("Can I turn recovery on for sessions that have already expired?",
  "No. It is a parameter at session creation, and the recovery URL is minted at the lapse only if it was set. There is no endpoint that adds one afterwards, so every session that lapsed without it is permanently unrecoverable. Changing the flag today only helps sessions created from today."),
 ("How long is a recovery URL valid?",
  "Thirty days from the lapse, in after_expiration.recovery.expires_at. That is generous until a mail job runs weekly, stalls, and retries: compare expires_at to the clock at send time rather than at queue time, or you will mail links that are already dead."),
 ("Do I need consent to send the recovery email?",
  "You need a recorded answer before you rely on one. consent_collection[promotions]=auto shows the customer the box, and consent.promotions records what they chose. Gate the send on opt_in and you have both the permission and the evidence of it; your own legal obligations are a separate question from the API."),
 ("How can I tell whether a recovery actually worked?",
  "A Checkout Session created from a recovery URL carries recovered_from, pointing at the session it replaced. Counting those across completed sessions is the only end-to-end proof: the configuration tells you what should happen, recovered_from tells you what did."),
 ("Would shortening expires_at improve recovery?",
  "It brings the whole loop forward, which usually helps: a session that lapses in two hours can be recovered while the customer still remembers the cart, rather than a day later. See the note on expired session share for what that window costs you at the default of 24 hours."),
],
"related": [
 ("/stripe/checkout-expired-session-share/", "Most Checkout Sessions expire unpaid and nobody is told"),
 ("/stripe/checkout-guest-customer-null/", "Guest checkouts finish with customer null and can't be linked"),
 ("/stripe/customers-missing-email/", "Customers with no email address on file"),
],
"citations": [CITE_ABANDONED, CITE_SESSION_OBJ, CITE_SESSION_CREATE, CITE_EVENT_TYPES],
},

{
"slug": "checkout-embedded-no-return-url",
"title": "Embedded Checkout never redirects and return_url is null",
"description": "A customer authenticates at their bank and comes back to nowhere. And redirect_on_completion never quietly removes iDEAL from the form entirely.",
"h1": "embedded Checkout never redirects and return_url is null",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe embedded checkout return_url", "redirect_on_completion never",
             "stripe ui_mode embedded", "CHECKOUT_SESSION_ID success_url",
             "stripe ideal not showing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The form is embedded in your own page, which is the whole point of it. Then a customer pays with iDEAL: they are sent to their bank, they authenticate, and they come back to nowhere, because <code>return_url</code> is null and the return leg has no destination. To them the payment failed. To Stripe it did not.",
"short_answer": """<p>Page <code>GET /v1/checkout/sessions?created[gte]=&lt;now-30d&gt;</code> and check three things. Sessions with <code>ui_mode</code> of <code>embedded_page</code> or <code>elements</code> and <code>return_url</code> of <code>null</code> have no return leg. Sessions with <code>redirect_on_completion == "never"</code> whose <code>payment_method_types</code> include a redirect method &mdash; <code>ideal</code>, <code>bancontact</code>, <code>p24</code>, <code>sofort</code>, <code>eps</code>, <code>giropay</code>, <code>blik</code> &mdash; are not offering those methods at all, because <code>never</code> disables them. And hosted sessions whose <code>success_url</code> has no <code>{CHECKOUT_SESSION_ID}</code> placeholder land on a page that cannot tell which session it is.</p>
<p>The repair is at creation: <code>ui_mode=embedded_page</code> with a real <code>return_url</code> and <code>redirect_on_completion=if_required</code>.</p>""",
"problem": """<p>Both halves of this produce the same support ticket &mdash; "it didn't work" &mdash; and neither produces an error anywhere you are looking. Nothing throws. Your server is not in the flow. Stripe's side is behaving exactly as configured.</p>
<p>The volume hides it too. Card payments are unaffected, so the great majority of checkouts on most accounts are fine and the metric barely moves. What moves is a slice: the customers in the Netherlands, or Belgium, or Poland, or the subset of card holders whose issuer throws a full 3DS challenge that leaves the page. Those people either fail or vanish, and they fail consistently, which looks like a market that does not convert rather than a bug.</p>""",
"why": """<p><strong><code>return_url</code> and <code>success_url</code> are different fields for different journeys.</strong> <code>success_url</code> is where the hosted page sends a customer when checkout finishes. <code>return_url</code> is where a customer comes back to after authenticating somewhere else entirely &mdash; their bank, their wallet, a 3DS challenge page. Embedded Checkout needs the second one, and reading the first as covering it is the usual mistake.</p>
<p><strong>The obvious fix for an embedded form makes it worse.</strong> "It is embedded, so it should not redirect" leads straight to <code>redirect_on_completion=never</code>, and <code>never</code> does not merely stop the completion redirect: it disables redirect-based payment methods outright. They stay listed in <code>payment_method_types</code> and simply are not offered, so your configuration and the customer's actual choices disagree with nothing to reconcile them.</p>
<p><strong>Nobody tests the leg that leaves the browser.</strong> Test-mode card payments complete without ever leaving your page, so the return leg is never exercised in development. The first real exercise is a live customer at a real bank, and the evidence of the failure is on their screen, not in your logs.</p>
<p><strong>The hosted-mode version of this is quieter still.</strong> A <code>success_url</code> without <code>{CHECKOUT_SESSION_ID}</code> works: the customer lands on a thank-you page. It just cannot say which purchase it is thanking them for, so anything that page was meant to show, or trigger, has nothing to look up.</p>""",
"steps": [
 {"h": "Read the last 30 days of sessions and split them by ui_mode",
  "body": """<p>Embedded and hosted sessions fail differently and are checked differently. Splitting first also tells you something useful on its own: which integration is actually creating sessions, which is often not the one people describe.</p>"""},
 {"h": "Check return_url on every embedded session",
  "body": """<p>A null or empty <code>return_url</code> means any payment method that leaves the page has nowhere to come back to. This is the whole finding for embedded integrations, and it is one field.</p>"""},
 {"h": "Compare redirect_on_completion against payment_method_types",
  "body": """<p><code>never</code> alongside <code>ideal</code>, <code>bancontact</code>, <code>p24</code>, <code>sofort</code>, <code>eps</code>, <code>giropay</code> or <code>blik</code> is a contradiction the API will not complain about. Those methods are configured and not being offered, so the loss shows up as low conversion in one region rather than as an error.</p>"""},
 {"h": "Check hosted sessions for the session id placeholder",
  "body": """<p><code>success_url</code> should contain the literal <code>{CHECKOUT_SESSION_ID}</code>. Stripe substitutes the real id at redirect time, and without it your landing page has no handle on the session it is confirming.</p>"""},
 {"h": "Fix it at creation",
  "body": """<p>Pass a real <code>return_url</code> carrying the placeholder, and use <code>redirect_on_completion=if_required</code> so the redirect happens only when the payment method demands it. That keeps the embedded experience for cards and keeps the redirect methods working.</p>"""},
 {"h": "Do not fulfil from the page the customer lands on",
  "body": """<p>The return page tells the customer something happened; it is not a reliable trigger, because the customer can close the tab before it loads. Fulfilment belongs on <code>checkout.session.completed</code>, which fires with or without a browser.</p>"""},
],
"verify": """<p>Re-run after the change. Embedded sessions should report <code>ok</code>, and no session should report <code>blocked</code>.</p>
<pre><code class="language-bash">python3 stripe_checkout_return_urls.py --days 7
# 340 session(s): 340 ok, 0 stranded, 0 blocked, 0 unjoinable</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/checkout/sessions</code>, no writes. The classifier is pure and holds the redirect-method list as data, because the interesting finding &mdash; a session configured with iDEAL that will never show iDEAL &mdash; is a comparison between two fields that are individually valid and only wrong together.",
"py_file": "stripe_checkout_return_urls.py",
"py": '''"""Report Stripe Checkout Sessions whose return leg has no destination.

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
log = logging.getLogger("stripe_checkout_return_urls")

API = "https://api.stripe.com/v1"

# Methods that take the customer off your page to authenticate. redirect_on_completion
# of "never" disables these outright rather than merely skipping a redirect.
REDIRECT_METHODS = ("ideal", "bancontact", "p24", "sofort", "eps", "giropay", "blik")

# Stripe has spelled the ui_mode values differently across API versions, so accept
# both rather than reporting a pinned older version as unknown.
EMBEDDED_MODES = ("embedded_page", "embedded", "elements")
HOSTED_MODES = ("hosted_page", "hosted")

PLACEHOLDER = "{CHECKOUT_SESSION_ID}"


def verdict(session):
    """Classify one Checkout Session. Pure, so the rules can be tested offline.

    Returns (state, detail).
    """
    ui = session.get("ui_mode") or HOSTED_MODES[0]
    methods = [m for m in (session.get("payment_method_types") or [])
               if m in REDIRECT_METHODS]

    if ui in EMBEDDED_MODES:
        if session.get("redirect_on_completion") == "never" and methods:
            return ("blocked",
                    "redirect_on_completion=never disables redirect-based methods, "
                    "so %s are configured but never offered" % ", ".join(methods))
        if not str(session.get("return_url") or "").strip():
            return ("stranded",
                    "ui_mode=%s with no return_url: a customer who authenticates "
                    "off-site comes back to nowhere" % (ui,))
        return ("ok", "ui_mode=%s with a return_url" % (ui,))

    if ui in HOSTED_MODES:
        success = str(session.get("success_url") or "")
        if PLACEHOLDER not in success:
            return ("unjoinable",
                    "success_url is %s: no %s placeholder, so the landing page "
                    "cannot tell which session it is confirming"
                    % (success or "empty", PLACEHOLDER))
        return ("ok", "hosted, and success_url carries the session id")

    return ("unknown", "unrecognised ui_mode %r" % (ui,))


def get(http, path, params=None):
    r = http.get(API + path, params=params or {}, timeout=30)
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
    ap.add_argument("--max-sessions", type=int, default=5000,
                    help="stop paginating after this many sessions")
    ap.add_argument("--show", type=int, default=10,
                    help="how many failing session ids to print")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    http = requests.Session()
    http.headers.update({"Authorization": "Bearer " + key})

    tally = {"ok": 0, "stranded": 0, "blocked": 0, "unjoinable": 0, "unknown": 0}
    examples = []
    total = 0
    for s in sessions(http, time.time() - args.days * 86400, args.max_sessions):
        total += 1
        state, detail = verdict(s)
        tally[state] = tally.get(state, 0) + 1
        if state != "ok" and len(examples) < args.show:
            examples.append((state, s.get("id", "?"), detail))

    log.info("%d session(s): %d ok, %d stranded, %d blocked, %d unjoinable",
             total, tally["ok"], tally["stranded"], tally["blocked"],
             tally["unjoinable"])
    for state, sid, detail in examples:
        log.warning("%-10s %s  %s", state, sid, detail)

    if tally["stranded"] or tally["blocked"]:
        log.warning("  repair: POST %s/checkout/sessions -d ui_mode=embedded_page "
                    "-d return_url='https://example.com/after-checkout"
                    "?session_id=%s' -d redirect_on_completion=if_required",
                    API, PLACEHOLDER)
    if tally["unjoinable"]:
        log.warning("  repair: POST %s/checkout/sessions "
                    "-d success_url='https://example.com/thanks?session_id=%s'",
                    API, PLACEHOLDER)

    return 1 if total - tally["ok"] else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-checkout-return-urls.mjs",
"js": '''/**
 * Report Stripe Checkout Sessions whose return leg has no destination.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Checkout Sessions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Methods that take the customer off your page to authenticate.
// redirect_on_completion of "never" disables these outright.
export const REDIRECT_METHODS =
  ['ideal', 'bancontact', 'p24', 'sofort', 'eps', 'giropay', 'blik'];

// Stripe has spelled the ui_mode values differently across API versions, so
// accept both rather than reporting a pinned older version as unknown.
const EMBEDDED_MODES = ['embedded_page', 'embedded', 'elements'];
const HOSTED_MODES = ['hosted_page', 'hosted'];

export const PLACEHOLDER = '{CHECKOUT_SESSION_ID}';

/** Classify one Checkout Session. Pure, so the rules can be tested offline. */
export function verdict(session) {
  const ui = session.ui_mode ?? HOSTED_MODES[0];
  const methods = (session.payment_method_types ?? [])
    .filter((m) => REDIRECT_METHODS.includes(m));

  if (EMBEDDED_MODES.includes(ui)) {
    if (session.redirect_on_completion === 'never' && methods.length) {
      return ['blocked',
        'redirect_on_completion=never disables redirect-based methods, so ' +
        `${methods.join(', ')} are configured but never offered`];
    }
    if (!String(session.return_url ?? '').trim()) {
      return ['stranded',
        `ui_mode=${ui} with no return_url: a customer who authenticates ` +
        'off-site comes back to nowhere'];
    }
    return ['ok', `ui_mode=${ui} with a return_url`];
  }

  if (HOSTED_MODES.includes(ui)) {
    const success = String(session.success_url ?? '');
    if (!success.includes(PLACEHOLDER)) {
      return ['unjoinable',
        `success_url is ${success || 'empty'}: no ${PLACEHOLDER} placeholder, ` +
        'so the landing page cannot tell which session it is confirming'];
    }
    return ['ok', 'hosted, and success_url carries the session id'];
  }

  return ['unknown', `unrecognised ui_mode ${JSON.stringify(ui)}`];
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
  const tally = { ok: 0, stranded: 0, blocked: 0, unjoinable: 0, unknown: 0 };
  const examples = [];
  let total = 0;

  for await (const s of sessions(key, Date.now() / 1000 - days * 86400)) {
    total += 1;
    const [state, detail] = verdict(s);
    tally[state] = (tally[state] ?? 0) + 1;
    if (state !== 'ok' && examples.length < 10) {
      examples.push([state, s.id ?? '?', detail]);
    }
  }

  console.log(`${total} session(s): ${tally.ok} ok, ${tally.stranded} stranded, ` +
              `${tally.blocked} blocked, ${tally.unjoinable} unjoinable`);
  for (const [state, id, detail] of examples) {
    console.warn(`${state.padEnd(10)} ${id}  ${detail}`);
  }

  if (tally.stranded || tally.blocked) {
    console.warn(`  repair: POST ${API}/checkout/sessions -d ui_mode=embedded_page ` +
                 `-d return_url='https://example.com/after-checkout` +
                 `?session_id=${PLACEHOLDER}' -d redirect_on_completion=if_required`);
  }
  if (tally.unjoinable) {
    console.warn(`  repair: POST ${API}/checkout/sessions ` +
                 `-d success_url='https://example.com/thanks?session_id=${PLACEHOLDER}'`);
  }

  process.exitCode = total - tally.ok ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that earns its place is the blocked one: an embedded session with a perfectly good <code>return_url</code>, iDEAL in <code>payment_method_types</code>, and <code>redirect_on_completion</code> of <code>never</code>. Every field is individually valid and the combination silently removes a payment method from the form, so a checker that stops at <code>return_url</code> reports it as fine.",
"test_py_file": "test_stripe_checkout_return_urls.py",
"test_py": '''from stripe_checkout_return_urls import verdict

RETURN = "https://example.com/after-checkout?session_id={CHECKOUT_SESSION_ID}"


def test_embedded_with_a_return_url_is_ok():
    state, _ = verdict({"ui_mode": "embedded_page", "return_url": RETURN,
                        "redirect_on_completion": "if_required"})
    assert state == "ok"


def test_embedded_without_a_return_url_is_stranded():
    state, detail = verdict({"ui_mode": "embedded_page", "return_url": None})
    assert state == "stranded"
    assert "nowhere" in detail
    assert verdict({"ui_mode": "embedded_page", "return_url": "  "})[0] == "stranded"


def test_never_plus_a_redirect_method_beats_a_valid_return_url():
    # Every field here is individually fine; together they remove iDEAL entirely.
    state, detail = verdict({"ui_mode": "embedded_page", "return_url": RETURN,
                             "redirect_on_completion": "never",
                             "payment_method_types": ["card", "ideal"]})
    assert state == "blocked"
    assert "ideal" in detail


def test_hosted_success_url_without_the_placeholder_is_unjoinable():
    state, detail = verdict({"ui_mode": "hosted_page",
                             "success_url": "https://example.com/thanks"})
    assert state == "unjoinable"
    assert "CHECKOUT_SESSION_ID" in detail
    assert verdict({"success_url": "https://example.com/thanks"})[0] == "unjoinable"


def test_an_unrecognised_ui_mode_is_not_silently_ok():
    assert verdict({"ui_mode": "kiosk"})[0] == "unknown"
''',
"test_js_file": "stripe-checkout-return-urls.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-checkout-return-urls.mjs';

const RETURN = 'https://example.com/after-checkout?session_id={CHECKOUT_SESSION_ID}';

test('embedded with a return_url is ok', () => {
  const [state] = verdict({ ui_mode: 'embedded_page', return_url: RETURN,
    redirect_on_completion: 'if_required' });
  assert.equal(state, 'ok');
});

test('embedded without a return_url is stranded', () => {
  const [state, detail] = verdict({ ui_mode: 'embedded_page', return_url: null });
  assert.equal(state, 'stranded');
  assert.match(detail, /nowhere/);
  assert.equal(
    verdict({ ui_mode: 'embedded_page', return_url: '  ' })[0], 'stranded');
});

test('never plus a redirect method beats a valid return_url', () => {
  const [state, detail] = verdict({ ui_mode: 'embedded_page', return_url: RETURN,
    redirect_on_completion: 'never', payment_method_types: ['card', 'ideal'] });
  assert.equal(state, 'blocked');
  assert.match(detail, /ideal/);
});

test('hosted success_url without the placeholder is unjoinable', () => {
  const [state, detail] = verdict({ ui_mode: 'hosted_page',
    success_url: 'https://example.com/thanks' });
  assert.equal(state, 'unjoinable');
  assert.match(detail, /CHECKOUT_SESSION_ID/);
  assert.equal(
    verdict({ success_url: 'https://example.com/thanks' })[0], 'unjoinable');
});

test('an unrecognised ui_mode is not silently ok', () => {
  assert.equal(verdict({ ui_mode: 'kiosk' })[0], 'unknown');
});
''',
"faq": [
 ("What is the difference between return_url and success_url?",
  "success_url is where the hosted Checkout page sends the customer once checkout finishes. return_url is where the customer comes back to after authenticating somewhere else: their bank for iDEAL or Bancontact, or a 3DS challenge page. Embedded Checkout uses return_url, and a success_url does not stand in for it."),
 ("Why did iDEAL stop appearing in my embedded form?",
  "Almost certainly redirect_on_completion=never. It does not only suppress the completion redirect; it disables redirect-based payment methods altogether. They stay listed in payment_method_types and are simply never offered, which is why nothing errors and the only symptom is a region that stopped converting."),
 ("Should return_url carry the session id?",
  "Yes. Add ?session_id={CHECKOUT_SESSION_ID} and Stripe substitutes the real id, so the page the customer lands on can retrieve the session and show them what they bought. Without it the page knows something finished but not what."),
 ("Is redirect_on_completion=if_required safe to use?",
  "That is the setting to want. The customer stays on your page for methods that do not need to leave it, and is redirected only for the ones that do, which keeps the embedded experience without silently removing payment methods from it."),
 ("Can I fulfil the order on the return page?",
  "Not as the only trigger. The customer can close the tab, lose signal, or be dropped by their bank's redirect, and none of that stops the payment succeeding. Fulfil on checkout.session.completed and use the return page to tell the customer what happened."),
],
"related": [
 ("/stripe/checkout-complete-payment-unpaid/", "Session status is complete but payment_status is still unpaid"),
 ("/stripe/payment-link-hosted-confirmation-no-fulfilment/", "Payment Link ends on Stripe's page, so fulfilment never fires"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
],
"citations": [CITE_SESSION_OBJ, CITE_SESSION_CREATE, CITE_EMBEDDED, CITE_FULFILMENT],
},

{
"slug": "payment-link-hosted-confirmation-no-fulfilment",
"title": "Payment Link ends on Stripe's page, so fulfilment never fires",
"description": "after_completion defaults to hosted_confirmation, so the buyer never reaches your server. With no checkout.session.completed webhook, nothing fulfils.",
"h1": "Payment Link ends on Stripe's page, so fulfilment never fires",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payment link fulfilment", "after_completion hosted_confirmation",
             "payment link redirect CHECKOUT_SESSION_ID",
             "checkout.session.completed not received", "stripe payment link webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The link works. The money arrives. The customer sees a Stripe page thanking them, closes the tab, and waits for a licence key that no code was ever asked to send. Nothing failed anywhere: the flow simply ends on Stripe's side and never comes back to yours.",
"short_answer": """<p>Page <code>GET /v1/payment_links?limit=100</code> and flag every link whose <code>after_completion.type</code> is <code>hosted_confirmation</code> &mdash; the default. Then read <code>GET /v1/webhook_endpoints?limit=100</code> and ask whether any endpoint with <code>status == "enabled"</code> lists <code>checkout.session.completed</code> in <code>enabled_events</code> (a <code>*</code> entry counts).</p>
<p>A hosted-confirmation link on an account with no such endpoint fulfils nothing at all, and nothing anywhere reports it. The repair is both halves: <code>after_completion[type]=redirect</code> with a URL carrying <code>{CHECKOUT_SESSION_ID}</code>, and a subscription to <code>checkout.session.completed</code> regardless, because Stripe is explicit that you cannot rely on the landing page alone.</p>""",
"problem": """<p>Payment Links exist so that you can take money without writing code, and they are extremely good at that. The trouble starts when a link created for something that needed no fulfilment &mdash; a donation, a deposit, an invoice somebody pays by hand &mdash; is copied for something that does. The link looks the same. The Dashboard looks the same. Nothing about the object says that a human now has to be sent a licence key.</p>
<p>Then the two halves of the repair live in different places, owned by different people. The <code>after_completion</code> setting is on the link, edited by whoever made it, usually in the Dashboard. The webhook endpoint is in a developer's settings, on a different screen, in a different week. Each side can look correct on its own while the account as a whole provisions nothing.</p>""",
"why": """<p><strong>The default is right for the original use and wrong for the new one.</strong> <code>hosted_confirmation</code> ends the flow on Stripe's own confirmation page. For a donation that is the correct and complete behaviour. For anything that has to be provisioned, it means the buyer's browser never touches your domain, so there is no page of yours that could have started the work.</p>
<p><strong>Redirecting is necessary but not sufficient.</strong> Switching to <code>redirect</code> gives you a page to run something on, and that page is not guaranteed to load: the customer can close the tab, lose signal, or simply not wait. Stripe says this in its own fulfilment guide. The webhook is the only trigger that does not depend on a browser still being open.</p>
<p><strong>A redirect without the placeholder is a page that knows nothing.</strong> <code>{CHECKOUT_SESSION_ID}</code> is substituted at redirect time. Without it the landing page can tell that somebody bought something and cannot tell what, for whom, or against which of your records.</p>
<p><strong>Nothing about the link tells you whether a webhook exists.</strong> The two facts live in different objects and no view in the Dashboard joins them. That join is exactly what a script can do in two GETs, and it is the difference between a link that is merely configured oddly and an account that silently provisions nothing.</p>""",
"steps": [
 {"h": "List every Payment Link and read after_completion.type",
  "body": """<p><code>GET /v1/payment_links?limit=100</code>, paginated. Missing or <code>hosted_confirmation</code> both mean the flow ends on Stripe's page; the field defaults, so a link created in the Dashboard without touching the After payment tab is in this state.</p>"""},
 {"h": "Ask the account whether the event is subscribed at all",
  "body": """<p><code>GET /v1/webhook_endpoints?limit=100</code>. You want an endpoint with <code>status</code> of <code>enabled</code> whose <code>enabled_events</code> contains <code>checkout.session.completed</code> or <code>*</code>. A disabled endpoint does not count, and neither does one in the other mode.</p>"""},
 {"h": "Check the redirect URL on the links that do redirect",
  "body": """<p>A redirect to a URL with no <code>{CHECKOUT_SESSION_ID}</code> is a thank-you page with no handle on the purchase. It is a smaller problem than no redirect at all, and it is the one that makes people believe fulfilment is wired up when it is not.</p>"""},
 {"h": "Confirm the link is actually in use before you rank it",
  "body": """<p><code>GET /v1/checkout/sessions?payment_link={plink_id}&amp;limit=100</code> and look at the recent <code>created</code> timestamps and <code>payment_status</code>. A misconfigured link nobody has used since last year is housekeeping; one taking payments this week is an incident.</p>"""},
 {"h": "Fix the link and the endpoint, not one of them",
  "body": """<p>Point <code>after_completion</code> at a redirect carrying the placeholder so the customer lands somewhere of yours, and subscribe <code>checkout.session.completed</code> so fulfilment happens whether or not they do. The redirect is the receipt; the webhook is the work.</p>"""},
 {"h": "Subscribe the async events too",
  "body": """<p>If the link accepts a delayed payment method, <code>checkout.session.completed</code> can arrive before the money does. Add <code>checkout.session.async_payment_succeeded</code> and <code>checkout.session.async_payment_failed</code> and gate the provisioning on <code>payment_status</code>.</p>"""},
],
"verify": """<p>Re-run after the change. Every link should be <code>covered</code>, meaning it redirects with the session id and the account has an enabled endpoint listening for the event.</p>
<pre><code class="language-bash">python3 stripe_payment_link_fulfilment.py
# 7 link(s): 7 covered, 0 webhook-only, 0 landing-only, 0 blind-redirect, 0 unfulfilled</code></pre>""",
"code_intro": "Two GETs and no writes: the links, and the account's webhook endpoints. There are two pure functions rather than one, because whether the account listens for <code>checkout.session.completed</code> is a fact about the whole account and the classifier has to be told it &mdash; the same link configuration is a mild untidiness on an account with a webhook and a total fulfilment failure on one without.",
"py_file": "stripe_payment_link_fulfilment.py",
"py": '''"""Report Stripe Payment Links whose completed payments fulfil nothing.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access to
Payment Links and Webhook Endpoints. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_payment_link_fulfilment")

API = "https://api.stripe.com/v1"

COMPLETED_EVENT = "checkout.session.completed"
PLACEHOLDER = "{CHECKOUT_SESSION_ID}"


def listens_for_completion(endpoints):
    """True when some enabled endpoint would receive checkout.session.completed.

    Pure. A disabled endpoint receives nothing, and a wildcard subscription does
    receive this event even though it receives a great deal else besides.
    """
    for ep in endpoints or []:
        if ep.get("status") != "enabled":
            continue
        events = ep.get("enabled_events") or []
        if COMPLETED_EVENT in events or "*" in events:
            return True
    return False


def verdict(link, webhook_covered):
    """Classify one Payment Link. Pure, so the rules can be tested offline.

    `webhook_covered` is the account-wide fact from listens_for_completion(): the
    same link configuration means different things with and without it.
    Returns (state, detail).
    """
    after = link.get("after_completion") or {}
    kind = after.get("type") or "hosted_confirmation"

    if kind == "redirect":
        url = str((after.get("redirect") or {}).get("url") or "")
        if PLACEHOLDER not in url:
            return ("blind-redirect",
                    "redirects to %s with no %s, so the landing page cannot tell "
                    "which purchase it is confirming"
                    % (url or "an empty url", PLACEHOLDER))
        if not webhook_covered:
            return ("landing-only",
                    "the redirect is the only fulfilment trigger, and it fires "
                    "only if the customer's browser reaches your page")
        return ("covered", "redirects with the session id, and the event is subscribed")

    if kind == "hosted_confirmation":
        if webhook_covered:
            return ("webhook-only",
                    "the flow ends on Stripe's page, so fulfilment runs from "
                    "%s alone; the buyer never lands anywhere of yours"
                    % COMPLETED_EVENT)
        return ("unfulfilled",
                "the flow ends on Stripe's page and no enabled endpoint listens "
                "for %s: nothing fulfils these payments at all" % COMPLETED_EVENT)

    return ("unknown", "unrecognised after_completion.type %r" % (kind,))


def get(http, path, params=None):
    r = http.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def all_pages(http, path, limit):
    """Yield every object from a paginated list endpoint."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(http, path, params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
        if not data or not page.get("has_more") or seen >= limit:
            break
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-links", type=int, default=1000,
                    help="stop paginating after this many payment links")
    ap.add_argument("--show", type=int, default=20,
                    help="how many failing links to print")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    http = requests.Session()
    http.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(http, "/webhook_endpoints", {"limit": 100}).get("data", [])
    covered = listens_for_completion(endpoints)
    if not covered:
        log.warning("no enabled webhook endpoint listens for %s in this key's mode",
                    COMPLETED_EVENT)

    tally = {"covered": 0, "webhook-only": 0, "landing-only": 0,
             "blind-redirect": 0, "unfulfilled": 0, "unknown": 0}
    examples = []
    links = 0
    for link in all_pages(http, "/payment_links", args.max_links):
        links += 1
        state, detail = verdict(link, covered)
        tally[state] = tally.get(state, 0) + 1
        if state in ("unfulfilled", "landing-only", "blind-redirect") \\
                and len(examples) < args.show:
            examples.append((state, link.get("id", "?"), detail))

    log.info("%d link(s): %d covered, %d webhook-only, %d landing-only, "
             "%d blind-redirect, %d unfulfilled",
             links, tally["covered"], tally["webhook-only"], tally["landing-only"],
             tally["blind-redirect"], tally["unfulfilled"])
    for state, lid, detail in examples:
        log.warning("%-14s %s  %s", state, lid, detail)

    if tally["unfulfilled"] or tally["blind-redirect"]:
        log.warning("  repair: POST %s/payment_links/plink_XXX "
                    "-d 'after_completion[type]=redirect' "
                    "-d 'after_completion[redirect][url]="
                    "https://example.com/after-checkout?session_id=%s'",
                    API, PLACEHOLDER)
    if not covered:
        log.warning("  and subscribe an enabled endpoint to %s plus "
                    "checkout.session.async_payment_succeeded", COMPLETED_EVENT)
        log.warning("  check which links are actually in use: GET "
                    "%s/checkout/sessions?payment_link=plink_XXX", API)

    return 1 if (tally["unfulfilled"] or tally["landing-only"]
                 or tally["blind-redirect"]) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-payment-link-fulfilment.mjs",
"js": '''/**
 * Report Stripe Payment Links whose completed payments fulfil nothing.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read access
 * to Payment Links and Webhook Endpoints. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const COMPLETED_EVENT = 'checkout.session.completed';
export const PLACEHOLDER = '{CHECKOUT_SESSION_ID}';

/**
 * True when some enabled endpoint would receive checkout.session.completed.
 * Pure. A disabled endpoint receives nothing, and a wildcard subscription does
 * receive this event even though it receives a great deal else besides.
 */
export function listensForCompletion(endpoints) {
  for (const ep of endpoints ?? []) {
    if (ep.status !== 'enabled') continue;
    const events = ep.enabled_events ?? [];
    if (events.includes(COMPLETED_EVENT) || events.includes('*')) return true;
  }
  return false;
}

/**
 * Classify one Payment Link. Pure, so the rules can be tested offline.
 * `webhookCovered` is the account-wide fact from listensForCompletion().
 */
export function verdict(link, webhookCovered) {
  const after = link.after_completion ?? {};
  const kind = after.type ?? 'hosted_confirmation';

  if (kind === 'redirect') {
    const url = String(after.redirect?.url ?? '');
    if (!url.includes(PLACEHOLDER)) {
      return ['blind-redirect',
        `redirects to ${url || 'an empty url'} with no ${PLACEHOLDER}, so the ` +
        'landing page cannot tell which purchase it is confirming'];
    }
    if (!webhookCovered) {
      return ['landing-only',
        'the redirect is the only fulfilment trigger, and it fires only if the ' +
        "customer's browser reaches your page"];
    }
    return ['covered', 'redirects with the session id, and the event is subscribed'];
  }

  if (kind === 'hosted_confirmation') {
    if (webhookCovered) {
      return ['webhook-only',
        `the flow ends on Stripe's page, so fulfilment runs from ` +
        `${COMPLETED_EVENT} alone; the buyer never lands anywhere of yours`];
    }
    return ['unfulfilled',
      `the flow ends on Stripe's page and no enabled endpoint listens for ` +
      `${COMPLETED_EVENT}: nothing fulfils these payments at all`];
  }

  return ['unknown', `unrecognised after_completion.type ${JSON.stringify(kind)}`];
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

export async function* allPages(key, path, limit = 1000) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const obj of data) { yield obj; seen += 1; }
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

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  const covered = listensForCompletion(endpoints);
  if (!covered) {
    console.warn(`no enabled webhook endpoint listens for ${COMPLETED_EVENT} ` +
                 "in this key's mode");
  }

  const tally = { covered: 0, 'webhook-only': 0, 'landing-only': 0,
    'blind-redirect': 0, unfulfilled: 0, unknown: 0 };
  const examples = [];
  let links = 0;

  for await (const link of allPages(key, '/payment_links')) {
    links += 1;
    const [state, detail] = verdict(link, covered);
    tally[state] = (tally[state] ?? 0) + 1;
    if (['unfulfilled', 'landing-only', 'blind-redirect'].includes(state)
        && examples.length < 20) {
      examples.push([state, link.id ?? '?', detail]);
    }
  }

  console.log(`${links} link(s): ${tally.covered} covered, ` +
              `${tally['webhook-only']} webhook-only, ${tally['landing-only']} ` +
              `landing-only, ${tally['blind-redirect']} blind-redirect, ` +
              `${tally.unfulfilled} unfulfilled`);
  for (const [state, id, detail] of examples) {
    console.warn(`${state.padEnd(14)} ${id}  ${detail}`);
  }

  if (tally.unfulfilled || tally['blind-redirect']) {
    console.warn(`  repair: POST ${API}/payment_links/plink_XXX ` +
                 `-d 'after_completion[type]=redirect' ` +
                 `-d 'after_completion[redirect][url]=` +
                 `https://example.com/after-checkout?session_id=${PLACEHOLDER}'`);
  }
  if (!covered) {
    console.warn(`  and subscribe an enabled endpoint to ${COMPLETED_EVENT} plus ` +
                 'checkout.session.async_payment_succeeded');
    console.warn('  check which links are actually in use: GET ' +
                 `${API}/checkout/sessions?payment_link=plink_XXX`);
  }

  process.exitCode =
    (tally.unfulfilled || tally['landing-only'] || tally['blind-redirect']) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The pair that matters is the same link read twice, once on an account that subscribes <code>checkout.session.completed</code> and once on one that does not. The link object is identical in both; only the account-wide fact changes, and it is the difference between an odd configuration and a product nobody is shipping. The wildcard endpoint gets its own test because a <code>*</code> subscription does cover this event, however much else it drags in.",
"test_py_file": "test_stripe_payment_link_fulfilment.py",
"test_py": '''from stripe_payment_link_fulfilment import listens_for_completion, verdict

REDIRECT = {"type": "redirect",
            "redirect": {"url": "https://example.com/after"
                                "?session_id={CHECKOUT_SESSION_ID}"}}


def test_hosted_confirmation_without_a_webhook_fulfils_nothing():
    state, detail = verdict({"after_completion": {"type": "hosted_confirmation"}},
                            False)
    assert state == "unfulfilled"
    assert "nothing fulfils" in detail


def test_the_same_link_with_a_webhook_is_only_untidy():
    # Identical link object; only the account-wide fact changed.
    state, _ = verdict({"after_completion": {"type": "hosted_confirmation"}}, True)
    assert state == "webhook-only"


def test_a_missing_after_completion_is_treated_as_the_default():
    assert verdict({}, False)[0] == "unfulfilled"


def test_a_redirect_without_the_placeholder_is_blind():
    state, detail = verdict(
        {"after_completion": {"type": "redirect",
                              "redirect": {"url": "https://example.com/thanks"}}},
        True)
    assert state == "blind-redirect"
    assert "CHECKOUT_SESSION_ID" in detail


def test_a_good_redirect_still_needs_the_event_subscribed():
    assert verdict({"after_completion": REDIRECT}, True)[0] == "covered"
    assert verdict({"after_completion": REDIRECT}, False)[0] == "landing-only"


def test_only_enabled_endpoints_count_and_a_wildcard_does():
    assert listens_for_completion(
        [{"status": "enabled", "enabled_events": ["*"]}]) is True
    assert listens_for_completion(
        [{"status": "disabled",
          "enabled_events": ["checkout.session.completed"]}]) is False
    assert listens_for_completion([]) is False
''',
"test_js_file": "stripe-payment-link-fulfilment.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { listensForCompletion, verdict } from './stripe-payment-link-fulfilment.mjs';

const REDIRECT = {
  type: 'redirect',
  redirect: { url: 'https://example.com/after?session_id={CHECKOUT_SESSION_ID}' },
};

test('hosted_confirmation without a webhook fulfils nothing', () => {
  const [state, detail] = verdict(
    { after_completion: { type: 'hosted_confirmation' } }, false);
  assert.equal(state, 'unfulfilled');
  assert.match(detail, /nothing fulfils/);
});

test('the same link with a webhook is only untidy', () => {
  const [state] = verdict(
    { after_completion: { type: 'hosted_confirmation' } }, true);
  assert.equal(state, 'webhook-only');
});

test('a missing after_completion is treated as the default', () => {
  assert.equal(verdict({}, false)[0], 'unfulfilled');
});

test('a redirect without the placeholder is blind', () => {
  const [state, detail] = verdict({ after_completion: {
    type: 'redirect', redirect: { url: 'https://example.com/thanks' } } }, true);
  assert.equal(state, 'blind-redirect');
  assert.match(detail, /CHECKOUT_SESSION_ID/);
});

test('a good redirect still needs the event subscribed', () => {
  assert.equal(verdict({ after_completion: REDIRECT }, true)[0], 'covered');
  assert.equal(verdict({ after_completion: REDIRECT }, false)[0], 'landing-only');
});

test('only enabled endpoints count and a wildcard does', () => {
  assert.equal(
    listensForCompletion([{ status: 'enabled', enabled_events: ['*'] }]), true);
  assert.equal(listensForCompletion([{ status: 'disabled',
    enabled_events: ['checkout.session.completed'] }]), false);
  assert.equal(listensForCompletion([]), false);
});
''',
"faq": [
 ("Where is this setting in the Dashboard?",
  "On the Payment Link, under the After payment tab: the choice between showing Stripe's confirmation page and the Don't show confirmation page option, which is the redirect. In the API it is after_completion.type, and it defaults to hosted_confirmation on every link created without touching it."),
 ("Is hosted_confirmation always wrong?",
  "No. For a donation, a deposit or anything with nothing to provision it is exactly right, and it is also fine when a webhook does the fulfilment and the buyer never needed to land on your site. It is wrong only when the landing page was supposed to be the trigger, which is the case people assume."),
 ("Can I fulfil the order from the redirect page instead of a webhook?",
  "Not as the only trigger. Stripe's fulfilment guide says as much: the customer can close the tab before your page loads, and the payment still succeeded. Use the redirect for the receipt the customer sees, and checkout.session.completed for the work."),
 ("What does {CHECKOUT_SESSION_ID} give me on the landing page?",
  "The id to retrieve the Checkout Session with, which carries the line items, the customer details and whatever client_reference_id or metadata you set. Without it the page knows a purchase happened and nothing else about it."),
 ("Which events should the endpoint subscribe to?",
  "checkout.session.completed for the ordinary case, plus checkout.session.async_payment_succeeded and checkout.session.async_payment_failed if the link accepts a delayed method such as ACH or SEPA, where completed arrives before the money does."),
],
"related": [
 ("/stripe/payment-link-inactive-still-published/", "A deactivated Payment Link is still linked from your site"),
 ("/stripe/checkout-complete-payment-unpaid/", "Session status is complete but payment_status is still unpaid"),
 ("/stripe/checkout-embedded-no-return-url/", "Embedded Checkout never redirects and return_url is null"),
],
"citations": [CITE_FULFILMENT, CITE_LINK_OBJ, CITE_LINK_UPDATE, CITE_WEBHOOK_OBJ],
},

]
