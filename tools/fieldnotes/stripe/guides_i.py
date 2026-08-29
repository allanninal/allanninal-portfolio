#!/usr/bin/env python3
"""/stripe/ field notes, batch I — the writing.

Checkout, Payment Links and the Billing Portal. Same constraint as the rest of
the section: every note here is a problem a script can find with a RESTRICTED,
READ-ONLY Stripe key. None of these scripts writes. They read, they say exactly
what is wrong, and they print the repair for a human to run against a live
payments account.
"""

CITE_SESSION_OBJ = ("The Checkout Session object — Stripe API reference",
                    "https://docs.stripe.com/api/checkout/sessions/object")
CITE_SESSION_LIST = ("List all Checkout Sessions — Stripe API reference",
                     "https://docs.stripe.com/api/checkout/sessions/list")
CITE_SESSION_CREATE = ("Create a Checkout Session — Stripe API reference",
                       "https://docs.stripe.com/api/checkout/sessions/create")
CITE_SESSION_RETRIEVE = ("Retrieve a Checkout Session — Stripe API reference",
                         "https://docs.stripe.com/api/checkout/sessions/retrieve")
CITE_ABANDONED = ("Recover abandoned carts — Stripe Docs",
                  "https://docs.stripe.com/payments/checkout/abandoned-carts")
CITE_FULFILMENT = ("Fulfill orders after checkout — Stripe Docs",
                   "https://docs.stripe.com/checkout/fulfillment")
CITE_ACH = ("ACH Direct Debit payments — Stripe Docs",
            "https://docs.stripe.com/payments/ach-direct-debit")
CITE_EVENT_TYPES = ("Types of events — Stripe API reference",
                    "https://docs.stripe.com/api/events/types")
CITE_LINK_OBJ = ("The Payment Link object — Stripe API reference",
                 "https://docs.stripe.com/api/payment-link/object")
CITE_LINK_CREATE = ("Create a payment link — Stripe API reference",
                    "https://docs.stripe.com/api/payment-link/create")
CITE_LINK_UPDATE = ("Update a payment link — Stripe API reference",
                    "https://docs.stripe.com/api/payment-link/update")
CITE_LINKS = ("Payment Links — Stripe Docs", "https://docs.stripe.com/payment-links")
CITE_PORTAL_SESSION_CREATE = ("Create a portal session — Stripe API reference",
                              "https://docs.stripe.com/api/customer_portal/sessions/create")
CITE_PORTAL_CONFIG_OBJ = ("The portal configuration object — Stripe API reference",
                          "https://docs.stripe.com/api/customer_portal/configurations/object")
CITE_PORTAL_CONFIG_LIST = ("List portal configurations — Stripe API reference",
                           "https://docs.stripe.com/api/customer_portal/configurations/list")
CITE_PORTAL_ACTIVATE = ("Set up the customer portal — Stripe Docs",
                        "https://docs.stripe.com/customer-management/activate-no-code-customer-portal")

GUIDES = [

{
"slug": "checkout-expired-session-share",
"title": "Most Checkout Sessions expire unpaid and nobody is told",
"description": "Session creation is healthy, revenue is flat, and the only signal is a checkout.session.expired event a full day later that nobody subscribes to.",
"h1": "most Checkout Sessions expire unpaid and nobody is told",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe checkout session expired", "checkout.session.expired",
             "stripe abandoned cart rate", "stripe checkout expires_at",
             "stripe checkout abandonment"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Sessions are being created at a healthy rate and the revenue line is flat. There is no error, no failed payment, no declined card &mdash; the sessions simply stop existing. Stripe does emit an event when one lapses, exactly 24 hours after it was created, and almost nobody is subscribed to it.",
"short_answer": """<p>Page <code>GET /v1/checkout/sessions?created[gte]=&lt;now-30d&gt;</code> and tally <code>status</code>. The number you want is <code>count(status == "expired") / count(all)</code>. Past <strong>0.5</strong> more than half of everything you create is being discarded; past <strong>0.25</strong> it is worth a look. Separately, count sessions where <code>status == "open"</code> and <code>expires_at</code> is already in the past &mdash; those have lapsed and have not been marked yet.</p>
<p>The repair is two things. Set <code>expires_at</code> at creation (minimum 30 minutes, maximum 24 hours) so a lapse surfaces in hours instead of a day, and subscribe an event destination to <code>checkout.session.expired</code> so the lapse is recorded somewhere you look.</p>""",
"problem": """<p>The shape of this is what makes it survive. Every individual session that expires looks like a customer who changed their mind, which is a normal thing that happens. There is no threshold at which Stripe tells you the aggregate has moved, because Stripe has no idea what your normal is. So the abandonment rate can drift from a third to two thirds over a quarter and the only visible symptom is that revenue is not growing the way session volume says it should.</p>
<p>Then there is the timing. A Checkout Session with no explicit <code>expires_at</code> lives for 24 hours. That means the event that marks it abandoned fires a full day after the customer left, long after they have gone somewhere else. Even teams that do handle <code>checkout.session.expired</code> are reacting to yesterday's decision, and teams that never subscribed to it &mdash; which is most of them, because the event is not on the list anybody starts with &mdash; have no record of the lapse at all.</p>""",
"why": """<p><strong>Nothing errors, so nothing pages.</strong> An expired session is a successful outcome as far as the API is concerned. The object is created, it is served, it reaches its <code>expires_at</code>, it moves to <code>expired</code>. Every step returned 200. There is no failed state anywhere in the sequence for an alert to hang off.</p>
<p><strong>The default window is a day, and a day is much longer than a decision.</strong> A customer who abandons a cart abandons it in the first few minutes. The remaining 23 hours and 55 minutes are pure lag between the event and your knowledge of it, and during that time the session sits in <code>open</code> where a naive count reads it as still in progress.</p>
<p><strong>The event nobody subscribes to.</strong> Integrations start from <code>checkout.session.completed</code> because that is the one that makes money appear. <code>checkout.session.expired</code> has no immediate consequence, so it never makes it onto the endpoint, and the abandonment metric that would have existed for free is simply never collected.</p>
<p><strong>The dashboard number is not the same number.</strong> Stripe's conversion reporting is built around sessions that were shown to a customer. A session created by a bot, a health check, or a page that renders a Checkout button and never redirects still counts in your API tally. That gap is fine as long as you know it exists, and it is the reason to measure the trend rather than agonise over the absolute value.</p>""",
"steps": [
 {"h": "Tally status across a fixed window",
  "body": """<p>Paginate <code>GET /v1/checkout/sessions?created[gte]=&lt;unix&gt;&amp;limit=100</code> and count <code>open</code>, <code>complete</code> and <code>expired</code>. Use the same window every time. The share only means something as a series, and changing the window changes the number more than any fix will.</p>"""},
 {"h": "Count the sessions that lapsed but are still marked open",
  "body": """<p>A session with <code>status == "open"</code> and <code>expires_at</code> in the past is already gone; the status just has not caught up. Counting these separately stops you from reporting an abandonment rate that is quietly optimistic by a day's worth of traffic.</p>"""},
 {"h": "Shorten expires_at at creation",
  "body": """<p><code>expires_at</code> accepts anything from 30 minutes to 24 hours after creation. Two hours is a reasonable default for a cart: long enough for someone to fetch their wallet, short enough that the expiry event arrives while a recovery email still makes sense.</p>"""},
 {"h": "Subscribe to checkout.session.expired",
  "body": """<p>Add it to the event destination alongside <code>checkout.session.completed</code>. Write the lapse to your own store with the session id and <code>customer_details.email</code>. That single row is what turns this from a quarterly spreadsheet exercise into a number on a dashboard.</p>"""},
 {"h": "Re-measure after the window changes, not before",
  "body": """<p>Shortening <code>expires_at</code> moves sessions out of <code>open</code> and into <code>expired</code> faster, so the measured share goes <em>up</em> the week you deploy it. That is the metric getting more honest, not the funnel getting worse. Compare against the window after it settles.</p>"""},
],
"verify": """<p>Re-run the script over the same window. The share should be reported with no lapsed-but-open sessions left behind it.</p>
<pre><code class="language-bash">python3 stripe_checkout_abandonment.py --days 30
# normal      118 of 640 session(s) expired unpaid (18.4%).</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/checkout/sessions</code> and nothing else &mdash; a restricted key with read access to Checkout Sessions is enough, and is what you should give it. The classification is a pure function of three integers, because the interesting part of this check is where the thresholds sit and that is exactly the part a network call would make untestable.",
"py_file": "stripe_checkout_abandonment.py",
"py": '''"""Report the share of Stripe Checkout Sessions that expire unpaid.

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
log = logging.getLogger("stripe_checkout_abandonment")

API = "https://api.stripe.com/v1"

HIGH_SHARE = 0.5    # more than half of everything created is thrown away
WATCH_SHARE = 0.25  # worth looking at before it becomes the first number


def verdict(total, expired, lapsed_open=0):
    """Classify one window of Checkout Sessions. Pure, so the thresholds are testable.

    `total` is every session created in the window, `expired` the ones Stripe has
    already marked expired, and `lapsed_open` the ones still marked open whose
    expires_at is in the past. Returns (state, detail).
    """
    if not total:
        return ("no-data", "no Checkout Sessions were created in the window")
    share = expired / float(total)
    pct = 100.0 * share
    if share >= HIGH_SHARE:
        return ("abandoned",
                "%d of %d session(s) expired unpaid (%.1f%%). More than half of "
                "everything created is being discarded." % (expired, total, pct))
    if lapsed_open:
        return ("lapsed",
                "%d open session(s) are already past expires_at and have not been "
                "marked yet; %.1f%% expired so far." % (lapsed_open, pct))
    if share >= WATCH_SHARE:
        return ("elevated",
                "%d of %d session(s) expired unpaid (%.1f%%). Shorten the window "
                "so the lapse is visible in hours." % (expired, total, pct))
    return ("normal",
            "%d of %d session(s) expired unpaid (%.1f%%)." % (expired, total, pct))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def scan(session, since, cap):
    """Tally status across every session created since `since`.

    Stripe returns newest first; the order does not matter for a tally, but the
    pagination does, because a single page of 100 on a busy account is a sample
    rather than a rate.
    """
    counts = {"open": 0, "complete": 0, "expired": 0}
    total = 0
    lapsed = 0
    now = int(time.time())
    params = {"created[gte]": since, "limit": 100}
    while True:
        page = get(session, "/checkout/sessions", params)
        data = page.get("data", [])
        for cs in data:
            total += 1
            state = cs.get("status") or "unknown"
            counts[state] = counts.get(state, 0) + 1
            expires = cs.get("expires_at")
            if state == "open" and expires is not None and expires < now:
                lapsed += 1
        if not data or not page.get("has_more") or total >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return total, counts, lapsed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="window to measure, in days (keep it fixed between runs)")
    ap.add_argument("--max-sessions", type=int, default=5000,
                    help="stop paginating after this many sessions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    total, counts, lapsed = scan(s, since, args.max_sessions)
    state, detail = verdict(total, counts.get("expired", 0), lapsed)

    log.info("%-11s %s", state, detail)
    log.info("  open %d  complete %d  expired %d  (last %d days)",
             counts.get("open", 0), counts.get("complete", 0),
             counts.get("expired", 0), args.days)
    if state in ("normal", "no-data"):
        return 0

    log.warning("  repair: create sessions with a shorter window so a lapse shows "
                "up in hours rather than a day:")
    log.warning("  POST %s/checkout/sessions -d expires_at=<now+7200>   "
                "(min 30 minutes, max 24 hours)", API)
    log.warning("  and subscribe an event destination to checkout.session.expired "
                "so each lapse is recorded")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-checkout-abandonment.mjs",
"js": '''/**
 * Report the share of Stripe Checkout Sessions that expire unpaid.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Checkout Sessions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const HIGH_SHARE = 0.5;   // more than half of everything created is discarded
export const WATCH_SHARE = 0.25; // worth looking at before it becomes the first number

/**
 * Classify one window of Checkout Sessions. Pure, so the thresholds are testable.
 * `lapsedOpen` counts sessions still marked open whose expires_at has passed.
 */
export function verdict(total, expired, lapsedOpen = 0) {
  if (!total) return ['no-data', 'no Checkout Sessions were created in the window'];
  const share = expired / total;
  const pct = (100 * share).toFixed(1);
  if (share >= HIGH_SHARE) {
    return ['abandoned',
      `${expired} of ${total} session(s) expired unpaid (${pct}%). More than half ` +
      'of everything created is being discarded.'];
  }
  if (lapsedOpen) {
    return ['lapsed',
      `${lapsedOpen} open session(s) are already past expires_at and have not been ` +
      `marked yet; ${pct}% expired so far.`];
  }
  if (share >= WATCH_SHARE) {
    return ['elevated',
      `${expired} of ${total} session(s) expired unpaid (${pct}%). Shorten the ` +
      'window so the lapse is visible in hours.'];
  }
  return ['normal', `${expired} of ${total} session(s) expired unpaid (${pct}%).`];
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

export async function scan(key, since, cap = 5000) {
  const counts = { open: 0, complete: 0, expired: 0 };
  let total = 0;
  let lapsed = 0;
  const now = Math.floor(Date.now() / 1000);
  const params = { 'created[gte]': since, limit: 100 };
  for (;;) {
    const page = await get(key, '/checkout/sessions', params);
    const data = page.data ?? [];
    for (const cs of data) {
      total += 1;
      const state = cs.status ?? 'unknown';
      counts[state] = (counts[state] ?? 0) + 1;
      if (state === 'open' && cs.expires_at != null && cs.expires_at < now) lapsed += 1;
    }
    if (data.length === 0 || !page.has_more || total >= cap) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { total, counts, lapsed };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.argv[2] ?? 30);
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  const { total, counts, lapsed } = await scan(key, since);
  const [state, detail] = verdict(total, counts.expired ?? 0, lapsed);

  console.log(`${state.padEnd(11)} ${detail}`);
  console.log(`  open ${counts.open ?? 0}  complete ${counts.complete ?? 0}  ` +
              `expired ${counts.expired ?? 0}  (last ${days} days)`);
  if (state === 'normal' || state === 'no-data') return;

  console.warn('  repair: create sessions with a shorter window so a lapse shows ' +
               'up in hours rather than a day:');
  console.warn(`  POST ${API}/checkout/sessions -d expires_at=<now+7200>   ` +
               '(min 30 minutes, max 24 hours)');
  console.warn('  and subscribe an event destination to checkout.session.expired ' +
               'so each lapse is recorded');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these tests exist because of an accounting mistake that is easy to make and impossible to see afterwards. An account with no sessions at all is not a perfect conversion rate, and sessions that have lapsed but are still marked <code>open</code> have to be counted somewhere, or the reported share is optimistic by a day of traffic every single run.",
"test_py_file": "test_stripe_checkout_abandonment.py",
"test_py": '''from stripe_checkout_abandonment import verdict


def test_no_sessions_is_not_a_perfect_score():
    # An empty window divided into zero expired sessions is 0% abandonment, which
    # would report "normal" on an account that has simply stopped taking payments.
    state, _ = verdict(0, 0)
    assert state == "no-data"


def test_half_expired_is_the_boundary():
    assert verdict(100, 49)[0] == "elevated"
    assert verdict(100, 50)[0] == "abandoned"


def test_a_quarter_expired_is_only_elevated():
    assert verdict(100, 24)[0] == "normal"
    assert verdict(100, 25)[0] == "elevated"


def test_lapsed_open_sessions_are_reported_even_when_the_share_is_low():
    state, detail = verdict(100, 4, 3)
    assert state == "lapsed"
    assert "3 open session(s)" in detail


def test_a_healthy_account_still_reports_the_percentage():
    state, detail = verdict(640, 118)
    assert state == "normal"
    assert "18.4%" in detail
''',
"test_js_file": "stripe-checkout-abandonment.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-checkout-abandonment.mjs';

test('no sessions is not a perfect score', () => {
  assert.equal(verdict(0, 0)[0], 'no-data');
});

test('half expired is the boundary', () => {
  assert.equal(verdict(100, 49)[0], 'elevated');
  assert.equal(verdict(100, 50)[0], 'abandoned');
});

test('a quarter expired is only elevated', () => {
  assert.equal(verdict(100, 24)[0], 'normal');
  assert.equal(verdict(100, 25)[0], 'elevated');
});

test('lapsed open sessions are reported even when the share is low', () => {
  const [state, detail] = verdict(100, 4, 3);
  assert.equal(state, 'lapsed');
  assert.match(detail, /3 open session\\(s\\)/);
});

test('a healthy account still reports the percentage', () => {
  const [state, detail] = verdict(640, 118);
  assert.equal(state, 'normal');
  assert.match(detail, /18\\.4%/);
});
''',
"faq": [
 ("What is the default lifetime of a Checkout Session?",
  "24 hours from creation. You can set expires_at explicitly to anything between 30 minutes and 24 hours after creation, but you cannot extend it past a day. Once it passes, status moves to expired and checkout.session.expired fires."),
 ("Is a high expired share always a problem?",
  "No, and that is why the script reports a number rather than a pass or fail. Sessions created by crawlers, health checks, or a page that renders a Checkout button before the customer commits all inflate the denominator. Watch the trend against a fixed window; a share that moves is worth investigating, a share that sits still is your baseline."),
 ("Why do sessions sit in open long after the customer left?",
  "Because status only changes at expires_at. A customer who closed the tab two minutes in leaves a session that reads open for the rest of the day. Counting open sessions whose expires_at has already passed is the only way to see them before Stripe relabels them."),
 ("Does shortening expires_at lose me sales?",
  "Rarely, and the ones it loses are recoverable. Anyone who returns to a dead link gets Stripe's expired-session page, so give them a route back: enable recovery at creation and email the recovery URL. Two hours covers essentially everyone who was going to complete, and the shorter window is what makes the recovery email arrive while the cart is still in mind."),
 ("Can I re-open an expired Checkout Session?",
  "No. Expiry is terminal; the session cannot be revived and its URL stops working. You create a new session, which is exactly what Checkout's built-in recovery does under the covers, linking the new one back to the old through recovered_from."),
],
"related": [
 ("/stripe/checkout-complete-payment-unpaid/", "A complete session whose payment_status is still unpaid"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
 ("/stripe/payment-link-inactive-still-published/", "A deactivated Payment Link is still linked from your site"),
],
"citations": [CITE_SESSION_OBJ, CITE_SESSION_LIST, CITE_ABANDONED, CITE_SESSION_CREATE],
},

{
"slug": "payment-link-inactive-still-published",
"title": "A deactivated Payment Link is still linked from your site",
"description": "Customers click buy and land on Stripe's deactivation page. Conversion for that product goes to zero and nothing errors server-side.",
"h1": "a deactivated Payment Link is still linked from your site",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payment link deactivated", "payment link active false",
             "stripe payment link not working", "stripe inactive_message",
             "stripe payment link dead"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody deactivated a Payment Link in the Dashboard six weeks ago, for a good reason. The URL is still in a landing page, a scheduled email and a PDF invoice template, and every customer who clicks it lands on a Stripe page explaining that the link is no longer active. Your server never hears about any of it.",
"short_answer": """<p>Page <code>GET /v1/payment_links?limit=100</code> and collect every <code>url</code> where <code>active == false</code>. Diff that set against the URLs your site, emails and documents actually reference. Anything in both lists is a buy button that goes nowhere.</p>
<p>To sort the urgent ones from the merely untidy, ask whether the dead link is still receiving traffic: <code>GET /v1/checkout/sessions?payment_link={plink_id}&amp;limit=100</code> and look at recent <code>created</code> timestamps. A dead link with sessions last week is losing sales now. A dead link nobody has touched in a year is housekeeping.</p>""",
"problem": """<p>The failure is entirely one-sided. Stripe knows the link is inactive; your site does not, and there is no mechanism by which it ever could. The <code>url</code> keeps resolving forever &mdash; that is deliberate, so that old links do not become 404s &mdash; and what changes is only what Stripe serves at the other end. From your side nothing happened. No request hit your servers, no error was logged, no exception was raised. The customer simply stopped.</p>
<p>What makes this expensive rather than annoying is where Payment Link URLs end up. They are designed to be pasted: into a landing page, a newsletter, an invoice PDF, a QR code on a printed flyer, a social bio. Deactivating the link takes one click in the Dashboard and no part of that click reaches any of those places. Six weeks later somebody notices that one product has sold nothing since March.</p>""",
"why": """<p><strong>Deactivation is reversible, so it feels safe.</strong> <code>active</code> is a flag you can flip back, which is precisely why people flip it in the first place: to pause a product, to stop a promotion, to take something down while a price is corrected. The intent is temporary. The published URL does not know that, and the intent to re-enable it is exactly the kind of thing that gets forgotten.</p>
<p><strong>The link keeps working, for a definition of working.</strong> Requesting the URL returns 200 with a real Stripe page. Every uptime check, link checker and crawler you own will report it as fine, because by every mechanical measure it is fine. The only thing wrong is the content, and no automated check you have is reading it.</p>
<p><strong>There is no reverse index from a link to where you published it.</strong> Stripe can tell you a link is inactive. It has no idea that the URL is in a MailChimp template and on page four of a PDF. Only you can hold that list, and almost nobody does, so the diff that would catch this has to be run deliberately.</p>
<p><strong><code>inactive_message</code> is the clue that it was on purpose.</strong> When somebody sets a custom message shown to customers who hit a deactivated link, they knew people were still arriving. That is a link that was consciously retired and consciously left published &mdash; and worth checking that the message actually forwards people somewhere useful, rather than telling them nothing.</p>""",
"steps": [
 {"h": "List every Payment Link, not just the inactive ones",
  "body": """<p>Paginate <code>GET /v1/payment_links?limit=100</code>. You can pass <code>active=false</code> to isolate the dead ones, but the full list is more useful: it is also the inventory you will diff your site against, and it tells you which live link a dead product should be repointed at.</p>"""},
 {"h": "Check each dead link for recent sessions",
  "body": """<p><code>GET /v1/checkout/sessions?payment_link={plink_id}&amp;limit=100</code> returns the sessions that link created. Recent timestamps on an inactive link mean customers are still arriving and being turned away. This is the number that turns the finding into a priority.</p>"""},
 {"h": "Grep your own content for the URLs",
  "body": """<p>The Stripe half of the diff is easy; the other half is your repository, your CMS export and your email templates. Search for <code>buy.stripe.com</code> across all of them. Whatever the script cannot see is where the dead links actually live.</p>"""},
 {"h": "Decide per link: republish or reactivate",
  "body": """<p>If the product is still sold, point the published URL at a live link. If the link was paused by mistake, <code>POST /v1/payment_links/{plink_id} -d active=true</code> brings it straight back with the same URL, which is the one repair that fixes every publication at once.</p>"""},
 {"h": "Set inactive_message on anything you leave dead",
  "body": """<p>For links you intend to retire, give the deactivation page something useful to say &mdash; where the product moved to, or who to contact. It does not recover the sale automatically, but it converts a dead end into a redirect a human can follow.</p>"""},
],
"verify": """<p>Re-run the script. Every inactive link should either be reactivated or reporting no recent traffic.</p>
<pre><code class="language-bash">python3 stripe_inactive_payment_links.py
# live        plink_1MoBy5  https://buy.stripe.com/...  12 session(s) in the window
# dormant     plink_1KqAa2  inactive and nothing has reached it in 90 days</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Payment Links and Checkout Sessions is enough. The classification is pure and takes the <code>active</code> flag, the recent session count and <code>inactive_message</code>, so the difference between a link that is quietly losing sales and one that is merely stale is decided by visible rules rather than inside a request loop.",
"py_file": "stripe_inactive_payment_links.py",
"py": '''"""Report Stripe Payment Links that are deactivated but still receiving traffic.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access to
Payment Links and Checkout Sessions. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_inactive_payment_links")

API = "https://api.stripe.com/v1"


def verdict(active, recent_sessions, inactive_message=None):
    """Classify one Payment Link. Pure, so the rules can be tested without a network.

    `active` is the link's flag, `recent_sessions` the number of Checkout Sessions
    it created inside the window, and `inactive_message` the custom text shown on
    the deactivation page. Returns (state, detail).
    """
    if active is None:
        return ("unknown",
                "the link has no active flag; treat it as published until you know "
                "otherwise (%d recent session(s))" % recent_sessions)
    if active:
        return ("live", "%d session(s) in the window" % recent_sessions)
    if recent_sessions:
        if inactive_message:
            return ("dead-signposted",
                    "inactive, %d recent session(s), and customers at least see: %r"
                    % (recent_sessions, inactive_message))
        return ("dead-in-use",
                "inactive but still reached %d time(s) in the window: every one of "
                "those landed on Stripe's deactivation page" % recent_sessions)
    return ("dormant", "inactive and nothing has reached it in the window")


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def payment_links(session, cap):
    """Every Payment Link on the account, active and not."""
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/payment_links", params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def recent_session_count(session, link_id, since):
    """Sessions this link created since `since`.

    Only the count matters, but the pagination still has to happen: a busy link
    can fill a page with sessions from a single afternoon.
    """
    count = 0
    params = {"payment_link": link_id, "limit": 100}
    while True:
        page = get(session, "/checkout/sessions", params)
        data = page.get("data", [])
        for cs in data:
            if (cs.get("created") or 0) >= since:
                count += 1
        if not data or not page.get("has_more"):
            break
        if (data[-1].get("created") or 0) < since:
            break
        params["starting_after"] = data[-1]["id"]
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back a session still counts as recent traffic")
    ap.add_argument("--max-links", type=int, default=500,
                    help="stop paginating after this many Payment Links")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    bad = 0
    for link in payment_links(s, args.max_links):
        count = recent_session_count(s, link["id"], since)
        state, detail = verdict(link.get("active"), count, link.get("inactive_message"))
        line = "%-15s %-20s %s" % (state, link["id"], detail)
        if state in ("live", "dormant"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  published at: %s", link.get("url") or "<no url>")
        log.warning("  repair: repoint the published URL at a live link, or bring "
                    "this one back:")
        log.warning("  POST %s/payment_links/%s -d active=true", API, link["id"])
        if not link.get("inactive_message"):
            log.warning("  if it stays dead, give the deactivation page a "
                        "forwarding instruction with -d inactive_message=\\"...\\"")

    log.info("%d inactive link(s) still taking traffic", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-inactive-payment-links.mjs",
"js": '''/**
 * Report Stripe Payment Links that are deactivated but still receiving traffic.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read access
 * to Payment Links and Checkout Sessions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one Payment Link. Pure, so the rules can be tested without a network.
 * `active` may be null, which is not the same as false.
 */
export function verdict(active, recentSessions, inactiveMessage = null) {
  if (active === null || active === undefined) {
    return ['unknown',
      'the link has no active flag; treat it as published until you know ' +
      `otherwise (${recentSessions} recent session(s))`];
  }
  if (active) return ['live', `${recentSessions} session(s) in the window`];
  if (recentSessions) {
    if (inactiveMessage) {
      return ['dead-signposted',
        `inactive, ${recentSessions} recent session(s), and customers at least ` +
        `see: '${inactiveMessage}'`];
    }
    return ['dead-in-use',
      `inactive but still reached ${recentSessions} time(s) in the window: every ` +
      "one of those landed on Stripe's deactivation page"];
  }
  return ['dormant', 'inactive and nothing has reached it in the window'];
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

export async function paymentLinks(key, cap = 500) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/payment_links', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= cap) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

export async function recentSessionCount(key, linkId, since) {
  let count = 0;
  const params = { payment_link: linkId, limit: 100 };
  for (;;) {
    const page = await get(key, '/checkout/sessions', params);
    const data = page.data ?? [];
    for (const cs of data) if ((cs.created ?? 0) >= since) count += 1;
    if (data.length === 0 || !page.has_more) break;
    if ((data[data.length - 1].created ?? 0) < since) break;
    params.starting_after = data[data.length - 1].id;
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

  const days = Number(process.argv[2] ?? 90);
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  let bad = 0;
  for (const link of await paymentLinks(key)) {
    const count = await recentSessionCount(key, link.id, since);
    const [state, detail] = verdict(link.active, count, link.inactive_message);
    const line = `${state.padEnd(15)} ${link.id.padEnd(20)} ${detail}`;
    if (state === 'live' || state === 'dormant') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  published at: ${link.url ?? '<no url>'}`);
    console.warn('  repair: repoint the published URL at a live link, or bring ' +
                 'this one back:');
    console.warn(`  POST ${API}/payment_links/${link.id} -d active=true`);
    if (!link.inactive_message) {
      console.warn('  if it stays dead, give the deactivation page a forwarding ' +
                   'instruction with -d inactive_message="..."');
    }
  }

  console.log(`${bad} inactive link(s) still taking traffic`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The last test is the one that matters most and looks the most pedantic. <code>active</code> is a boolean, but a truncated response, an expanded field or a stubbed fixture can hand you <code>None</code> instead, and a plain <code>if not active</code> would then report every link on the account as dead. A missing flag is a thing you do not know, not a thing you know is false.",
"test_py_file": "test_stripe_inactive_payment_links.py",
"test_py": '''from stripe_inactive_payment_links import verdict


def test_an_active_link_is_live():
    assert verdict(True, 12)[0] == "live"


def test_a_dead_link_with_recent_traffic_is_the_expensive_case():
    state, detail = verdict(False, 9)
    assert state == "dead-in-use"
    assert "9 time(s)" in detail


def test_an_inactive_message_softens_it_but_does_not_clear_it():
    state, detail = verdict(False, 9, "We moved to the new plan page")
    assert state == "dead-signposted"
    assert "new plan page" in detail


def test_a_dead_link_nobody_visits_is_only_housekeeping():
    assert verdict(False, 0)[0] == "dormant"


def test_a_missing_active_flag_is_not_read_as_deactivated():
    # `if not active` would call this dead and print a repair for a link that is
    # working perfectly. Absent is not false.
    assert verdict(None, 3)[0] == "unknown"
''',
"test_js_file": "stripe-inactive-payment-links.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-inactive-payment-links.mjs';

test('an active link is live', () => {
  assert.equal(verdict(true, 12)[0], 'live');
});

test('a dead link with recent traffic is the expensive case', () => {
  const [state, detail] = verdict(false, 9);
  assert.equal(state, 'dead-in-use');
  assert.match(detail, /9 time\\(s\\)/);
});

test('an inactive message softens it but does not clear it', () => {
  const [state, detail] = verdict(false, 9, 'We moved to the new plan page');
  assert.equal(state, 'dead-signposted');
  assert.match(detail, /new plan page/);
});

test('a dead link nobody visits is only housekeeping', () => {
  assert.equal(verdict(false, 0)[0], 'dormant');
});

test('a missing active flag is not read as deactivated', () => {
  assert.equal(verdict(null, 3)[0], 'unknown');
  assert.equal(verdict(undefined, 3)[0], 'unknown');
});
''',
"faq": [
 ("What does a customer see when they open a deactivated Payment Link?",
  "A Stripe-hosted page telling them the link is no longer active. It returns a normal 200 response, so every link checker and uptime monitor you own will call it healthy. If inactive_message is set, your text is shown there instead of the generic wording."),
 ("Can I delete a Payment Link instead of deactivating it?",
  "No. Payment Links cannot be deleted through the API; active is the only lever, and it can be flipped either way. That is convenient when you paused something by mistake and awkward when you wanted the URL to stop resolving, because it never will."),
 ("Does deactivating a link cancel the subscriptions it created?",
  "No. The link is only the door. Subscriptions, invoices and payments it produced carry on exactly as before; deactivation stops new Checkout Sessions being created and nothing else."),
 ("How do I find where a link is published?",
  "Stripe cannot tell you. Grep your repository, CMS export and email templates for buy.stripe.com, then diff that list against the URLs the script prints. Keeping a link-to-page mapping in your own system is the only durable fix, and it takes one column."),
 ("Why check for recent sessions on a link that is already dead?",
  "Because it separates a lost sale from a tidy-up. Sessions created against an inactive link are people who found the URL, clicked it and were turned away. Zero recent sessions means the link is simply stale, and stale links can wait for the next cleanup."),
],
"related": [
 ("/stripe/checkout-expired-session-share/", "Most Checkout Sessions expire unpaid and nobody is told"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
 ("/stripe/billing-portal-no-configuration/", "No Billing Portal configuration, so portal sessions 400"),
],
"citations": [CITE_LINK_OBJ, CITE_LINK_UPDATE, CITE_LINK_CREATE, CITE_LINKS],
},

{
"slug": "billing-portal-no-configuration",
"title": "No Billing Portal configuration, so portal sessions 400",
"description": "Manage subscription 500s in production. Test mode and live mode are configured separately, so the portal works right up until the first live click.",
"h1": "no Billing Portal configuration, so portal sessions 400",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe billing portal no configuration",
             "no configuration provided default configuration",
             "billing_portal sessions 400", "stripe customer portal error",
             "stripe portal configuration live mode"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Manage subscription button worked all through development. On the day it goes live it throws a 500, and the log underneath it reads <em>No configuration provided and your default configuration has not been created</em>. Nothing about the deploy changed the portal code, because the thing that is missing was never in the code.",
"short_answer": """<p>Run <code>GET /v1/billing_portal/configurations?limit=100</code> <strong>with the live key</strong>. The failure condition is an empty <code>data</code> array, or no element with <code>is_default == true</code> and <code>active == true</code>. A test-mode key that returns configurations proves nothing whatsoever about live.</p>
<p>Cross-check the exposure with <code>GET /v1/subscriptions?status=active&amp;limit=100</code>. Active subscribers plus zero configurations means every portal click on the site is currently returning 400 to your server and a 500 to the customer.</p>""",
"problem": """<p>This one is unusual in that the error message is genuinely good. Stripe tells you exactly what is wrong and exactly how to fix it. The problem is where the message ends up: inside a 400 from the API, caught by your generic error handler, turned into a 500, and shown to the customer as "something went wrong". Nobody reads the Stripe text until somebody goes looking in the logs, which happens after the support ticket, which happens after the customer has already tried three times.</p>
<p>And it will not have shown up before then. The portal integration is a handful of lines &mdash; create a session for a customer, redirect to <code>session.url</code> &mdash; and it works perfectly in test mode, because somebody clicked through the portal settings screen at some point while building it. That click saved a test-mode default configuration. Live mode has its own, and it does not exist.</p>""",
"why": """<p><strong>The default configuration is created by a Dashboard save, not by an API call.</strong> Every other part of a Stripe integration comes into existence because your code created it. This one comes into existence because a human opened a settings page and pressed a button. There is no line in your repository that would remind you, and no deploy step that would carry it across.</p>
<p><strong>Test and live are separate accounts for this purpose.</strong> Configurations do not sync between modes, exactly like webhook endpoints and API keys. The mental model of "I set that up already" is true and refers to the wrong mode.</p>
<p><strong>Omitting <code>configuration</code> is the documented, ordinary way to call the API.</strong> <code>POST /v1/billing_portal/sessions</code> with just a customer id is the example in every tutorial, and it falls back to the account default. That fallback is invisible until the thing it falls back to is missing, at which point the call fails on a parameter your code never mentioned.</p>
<p><strong>Nothing degrades &mdash; it is all or nothing.</strong> There is no partial portal. Either a usable default exists and every customer can manage their subscription, or it does not and every single click fails. That makes it a total outage of a feature, and total outages of secondary features are exactly what monitoring misses.</p>""",
"steps": [
 {"h": "List configurations with the live key specifically",
  "body": """<p><code>GET /v1/billing_portal/configurations?limit=100</code>. Run it with the key the production server actually uses. Running it with a test key is the same mistake that caused the incident, made a second time while investigating it.</p>"""},
 {"h": "Look for a default that is also active",
  "body": """<p>Both flags matter. <code>is_default</code> decides whether a session created without a <code>configuration</code> parameter can find it; <code>active</code> decides whether it can be used at all. A configuration that is default but inactive satisfies a naive check and still fails every call.</p>"""},
 {"h": "Measure who is affected",
  "body": """<p><code>GET /v1/subscriptions?status=active&amp;limit=100</code>. Every active subscriber is somebody who can press the button. That count is the difference between "fix before the next release" and "fix now", and it belongs in the incident note.</p>"""},
 {"h": "Create the default, once",
  "body": """<p>Save the portal settings at <code>dashboard.stripe.com/settings/billing/portal</code> for live mode and the <code>/test/</code> equivalent for test. Or create one through the API and pass its id explicitly as <code>configuration=bpc_...</code> on every session, which has the advantage of being visible in your repository.</p>"""},
 {"h": "Log the Stripe error message, not a generic one",
  "body": """<p>Stripe's message named the problem precisely. Whatever swallowed it will swallow the next one too. Surface <code>error.message</code> from the Stripe response into your logs and this class of failure stops costing an afternoon each time.</p>"""},
],
"verify": """<p>Re-run the script against the live key. A default configuration that is active is all this check wants to see.</p>
<pre><code class="language-bash">python3 stripe_portal_configuration.py
# configured  default configuration bpc_1MrTdC is active; portal sessions resolve</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to the Customer Portal and to Subscriptions is enough. The classifier takes the list of configurations and the number of active subscriptions, because the same missing configuration is a ticket on an account with no subscribers and a live outage on one with four hundred.",
"py_file": "stripe_portal_configuration.py",
"py": '''"""Report a missing or unusable Stripe Billing Portal configuration.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access to
the Customer Portal and Subscriptions. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_portal_configuration")

API = "https://api.stripe.com/v1"

PORTAL_SETTINGS = "https://dashboard.stripe.com/settings/billing/portal"


def verdict(configurations, active_subscriptions=0):
    """Classify the account's portal configuration. Pure, so it is testable offline.

    `configurations` is the list from /v1/billing_portal/configurations and
    `active_subscriptions` the number of customers who can press the button.
    Returns (state, detail).
    """
    configs = list(configurations or [])
    usable = [c for c in configs if c.get("is_default") and c.get("active")]
    if usable:
        return ("configured",
                "default configuration %s is active; portal sessions resolve"
                % usable[0].get("id", "<no id>"))
    if not configs:
        if active_subscriptions:
            return ("erroring",
                    "no portal configuration exists and %d active subscription(s) "
                    "can reach the portal: every session create is failing with 400 "
                    "right now" % active_subscriptions)
        return ("missing",
                "no portal configuration exists. The first session created without "
                "an explicit configuration will fail with 400.")
    active = [c for c in configs if c.get("active")]
    if active:
        return ("explicit-only",
                "%d active configuration(s) but none is the default (%s). A session "
                "created without configuration=... fails with 400."
                % (len(active), ", ".join(c.get("id", "?") for c in active[:3])))
    return ("inactive-default",
            "%d configuration(s) exist and none of them is active, so none can be "
            "used to open the portal" % len(configs))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def configurations(session):
    """Every portal configuration on the account, in whichever mode the key is for."""
    out = []
    params = {"limit": 100}
    while True:
        page = get(session, "/billing_portal/configurations", params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more"):
            break
        params["starting_after"] = data[-1]["id"]
    return out


def active_subscription_count(session, cap):
    count = 0
    params = {"status": "active", "limit": 100}
    while True:
        page = get(session, "/subscriptions", params)
        data = page.get("data", [])
        count += len(data)
        if not data or not page.get("has_more") or count >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-subscriptions", type=int, default=2000,
                    help="stop counting active subscriptions after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2
    if key.startswith("sk_test") or key.startswith("rk_test"):
        log.warning("this is a test-mode key: a result here says nothing about live, "
                    "which is where this failure happens")

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    configs = configurations(s)
    subs = active_subscription_count(s, args.max_subscriptions)
    state, detail = verdict(configs, subs)

    line = "%-16s %s" % (state, detail)
    if state == "configured":
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  %d active subscription(s) can reach the portal", subs)
    log.warning("  repair: save the portal settings once, in this mode, at %s",
                PORTAL_SETTINGS)
    log.warning("  or create one over the API and pass its id explicitly:")
    log.warning("  POST %s/billing_portal/configurations -d "
                "\\"features[invoice_history][enabled]=true\\" ...", API)
    log.warning("  then POST %s/billing_portal/sessions -d customer=cus_... "
                "-d configuration=bpc_...", API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-portal-configuration.mjs",
"js": '''/**
 * Report a missing or unusable Stripe Billing Portal configuration.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read access
 * to the Customer Portal and Subscriptions. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const PORTAL_SETTINGS = 'https://dashboard.stripe.com/settings/billing/portal';

/**
 * Classify the account's portal configuration. Pure, so it is testable offline.
 * A default that is not active satisfies a naive check and still fails every call.
 */
export function verdict(configurations, activeSubscriptions = 0) {
  const configs = configurations ?? [];
  const usable = configs.filter((c) => c.is_default && c.active);
  if (usable.length) {
    return ['configured',
      `default configuration ${usable[0].id ?? '<no id>'} is active; portal ` +
      'sessions resolve'];
  }
  if (configs.length === 0) {
    if (activeSubscriptions) {
      return ['erroring',
        `no portal configuration exists and ${activeSubscriptions} active ` +
        'subscription(s) can reach the portal: every session create is failing ' +
        'with 400 right now'];
    }
    return ['missing',
      'no portal configuration exists. The first session created without an ' +
      'explicit configuration will fail with 400.'];
  }
  const active = configs.filter((c) => c.active);
  if (active.length) {
    return ['explicit-only',
      `${active.length} active configuration(s) but none is the default ` +
      `(${active.slice(0, 3).map((c) => c.id ?? '?').join(', ')}). A session ` +
      'created without configuration=... fails with 400.'];
  }
  return ['inactive-default',
    `${configs.length} configuration(s) exist and none of them is active, so ` +
    'none can be used to open the portal'];
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

export async function configurations(key) {
  const out = [];
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/billing_portal/configurations', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

export async function activeSubscriptionCount(key, cap = 2000) {
  let count = 0;
  const params = { status: 'active', limit: 100 };
  for (;;) {
    const page = await get(key, '/subscriptions', params);
    const data = page.data ?? [];
    count += data.length;
    if (data.length === 0 || !page.has_more || count >= cap) break;
    params.starting_after = data[data.length - 1].id;
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
  if (key.startsWith('sk_test') || key.startsWith('rk_test')) {
    console.warn('this is a test-mode key: a result here says nothing about live, ' +
                 'which is where this failure happens');
  }

  const configs = await configurations(key);
  const subs = await activeSubscriptionCount(key);
  const [state, detail] = verdict(configs, subs);

  const line = `${state.padEnd(16)} ${detail}`;
  if (state === 'configured') { console.log(line); return; }

  console.warn(line);
  console.warn(`  ${subs} active subscription(s) can reach the portal`);
  console.warn(`  repair: save the portal settings once, in this mode, at ${PORTAL_SETTINGS}`);
  console.warn('  or create one over the API and pass its id explicitly:');
  console.warn(`  POST ${API}/billing_portal/configurations -d ` +
               '"features[invoice_history][enabled]=true" ...');
  console.warn(`  then POST ${API}/billing_portal/sessions -d customer=cus_... ` +
               '-d configuration=bpc_...');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two tests worth reading are the ones about configurations that exist and still do not work. A default flag with <code>active</code> false, and a set of perfectly good configurations none of which is the default, both look like success to a check that only counts array length &mdash; and both return the same 400 to the customer as having nothing at all.",
"test_py_file": "test_stripe_portal_configuration.py",
"test_py": '''from stripe_portal_configuration import verdict

DEFAULT = {"id": "bpc_1", "is_default": True, "active": True}
EXPLICIT = {"id": "bpc_2", "is_default": False, "active": True}


def test_an_active_default_is_all_that_is_needed():
    state, detail = verdict([DEFAULT], 400)
    assert state == "configured"
    assert "bpc_1" in detail


def test_no_configuration_with_live_subscribers_is_an_outage():
    state, detail = verdict([], 400)
    assert state == "erroring"
    assert "400" in detail


def test_no_configuration_and_no_subscribers_is_only_waiting_to_break():
    assert verdict([], 0)[0] == "missing"


def test_an_explicit_only_setup_still_fails_without_the_id():
    # Counting the array would call this configured. Sessions created without a
    # configuration parameter still have no default to fall back to.
    state, detail = verdict([EXPLICIT], 400)
    assert state == "explicit-only"
    assert "bpc_2" in detail


def test_an_inactive_default_does_not_count():
    inactive = {"id": "bpc_3", "is_default": True, "active": False}
    assert verdict([inactive], 5)[0] == "inactive-default"
''',
"test_js_file": "stripe-portal-configuration.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-portal-configuration.mjs';

const DEFAULT = { id: 'bpc_1', is_default: true, active: true };
const EXPLICIT = { id: 'bpc_2', is_default: false, active: true };

test('an active default is all that is needed', () => {
  const [state, detail] = verdict([DEFAULT], 400);
  assert.equal(state, 'configured');
  assert.match(detail, /bpc_1/);
});

test('no configuration with live subscribers is an outage', () => {
  const [state, detail] = verdict([], 400);
  assert.equal(state, 'erroring');
  assert.match(detail, /400/);
});

test('no configuration and no subscribers is only waiting to break', () => {
  assert.equal(verdict([], 0)[0], 'missing');
});

test('an explicit only setup still fails without the id', () => {
  const [state, detail] = verdict([EXPLICIT], 400);
  assert.equal(state, 'explicit-only');
  assert.match(detail, /bpc_2/);
});

test('an inactive default does not count', () => {
  const inactive = { id: 'bpc_3', is_default: true, active: false };
  assert.equal(verdict([inactive], 5)[0], 'inactive-default');
});
''',
"faq": [
 ("What exactly does the error say?",
  "No configuration provided and your default configuration has not been created. Provide a configuration or create your default by saving your customer portal settings. It is a 400 from POST /v1/billing_portal/sessions, and it is usually invisible because a generic handler turns it into a 500 before anyone reads it."),
 ("Why did it work in test mode?",
  "Because somebody saved the portal settings in test mode while building the feature, and that save is what creates the default configuration. Configurations do not cross modes, exactly like webhook endpoints and keys. Live mode has never had the settings screen saved."),
 ("Can I create the default configuration through the API?",
  "You can create configurations through the API, and you can mark one as the default. Many teams prefer to skip the default entirely and pass configuration=bpc_... explicitly on every session, because then the dependency is visible in the repository instead of living in somebody's browser history."),
 ("Does a configuration need to be active as well as default?",
  "Yes, and this is the trap. active can be set to false to retire a configuration, and an inactive one cannot be used to open the portal even if it is still flagged as the default. A check that only looks at is_default reports success on an account where every click fails."),
 ("How many configurations should an account have?",
  "One is enough for most. More than one is useful when different customer segments should see different features, in which case you pass the right configuration id per session. What you should not have is several configurations and no default, plus code that never passes an id."),
],
"related": [
 ("/stripe/subscription-without-payment-method/", "An active subscription has no payment method attached"),
 ("/stripe/past-due-subscriptions-accumulating/", "past_due subscriptions accumulate unnoticed"),
 ("/stripe/payment-link-inactive-still-published/", "A deactivated Payment Link is still linked from your site"),
],
"citations": [CITE_PORTAL_SESSION_CREATE, CITE_PORTAL_CONFIG_OBJ,
              CITE_PORTAL_CONFIG_LIST, CITE_PORTAL_ACTIVATE],
},

{
"slug": "checkout-complete-payment-unpaid",
"title": "Session status is complete but payment_status is still unpaid",
"description": "Fulfilment fires on checkout.session.completed and the money arrives days later, or not at all. status and payment_status are independent fields.",
"h1": "session status is complete but payment_status is still unpaid",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["checkout.session.completed unpaid", "stripe payment_status unpaid",
             "checkout session complete not paid",
             "checkout.session.async_payment_failed",
             "stripe delayed payment methods fulfilment"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The handler listens for <code>checkout.session.completed</code>, marks the order paid and ships it. Most of the time that is correct. For ACH, SEPA and every other delayed payment method it is a guess, and a few days later some of those guesses come back as <code>checkout.session.async_payment_failed</code> with the goods already gone.",
"short_answer": """<p><code>status</code> and <code>payment_status</code> are two different fields and <code>status: "complete"</code> explicitly allows payment to still be in progress. Page <code>GET /v1/checkout/sessions?status=complete&amp;created[gte]=&lt;now-90d&gt;</code> and flag every session where <code>payment_status == "unpaid"</code>.</p>
<p>To see which way each one went, expand the intent: <code>GET /v1/checkout/sessions/{cs_id}?expand[]=payment_intent</code>. <code>payment_intent.status == "processing"</code> is money in flight; <code>requires_payment_method</code> or <code>canceled</code> means it already failed and the fulfilment needs reversing. The fix in the code is one condition: gate fulfilment on <code>payment_status != "unpaid"</code>.</p>""",
"problem": """<p>The bug is invisible on a card-only account, which is where the code was written and tested. Cards authorise synchronously, so by the time <code>checkout.session.completed</code> arrives the money really is there and <code>payment_status</code> really is <code>paid</code>. Fulfilling on the event is correct a hundred times out of a hundred, so the shortcut is never punished and becomes the pattern everyone copies.</p>
<p>Then somebody enables ACH Direct Debit, or SEPA, or Boleto for a new market, in a Dashboard setting that does not touch your code at all. Now some sessions complete with <code>payment_status: "unpaid"</code> and settle days later. Most of them settle fine. The ones that do not arrive as <code>checkout.session.async_payment_failed</code>, an event the handler has no branch for, for orders that shipped last Tuesday.</p>""",
"why": """<p><strong>The field names encourage the mistake.</strong> "Complete" sounds terminal in a way that "the customer finished the form, and payment may still be processing" does not. Stripe's own reference says as much in the object docs, but the reading that survives is the one the word suggests.</p>
<p><strong>The event fires at the same moment either way.</strong> <code>checkout.session.completed</code> arrives when the customer finishes checkout, not when the money settles. There is nothing different about the delivery, the timing or the payload shape to distinguish a card payment from an ACH debit &mdash; only one field inside it.</p>
<p><strong>Enabling a payment method is a configuration change, not a deploy.</strong> Somebody in finance turns on bank debits to cut card fees. No pull request, no review, no test. The first delayed payment is also the first time your fulfilment logic is wrong, and nobody involved connected the two.</p>
<p><strong>The failure lands days after the fulfilment, on a different event.</strong> <code>checkout.session.async_payment_failed</code> is a separate event type that has to be subscribed to and handled. If it is not on the endpoint, the failure is a line in the Stripe Dashboard that nobody is reading, and the loss shows up eventually as an unexplained gap between orders and revenue.</p>""",
"steps": [
 {"h": "Find complete sessions that were never paid",
  "body": """<p>Paginate <code>GET /v1/checkout/sessions?status=complete&amp;created[gte]=&lt;unix&gt;&amp;limit=100</code> and flag <code>payment_status == "unpaid"</code>. Ninety days is a sensible window: long enough to include settled and failed async payments, short enough to stay one job.</p>"""},
 {"h": "Expand the PaymentIntent to see which way it went",
  "body": """<p><code>GET /v1/checkout/sessions/{cs_id}?expand[]=payment_intent</code>. <code>processing</code> means it is still in flight and there is nothing to do but wait. <code>requires_payment_method</code> or <code>canceled</code> means the payment failed after the session completed, and anything you fulfilled against it needs unwinding.</p>"""},
 {"h": "Check which delayed methods are enabled at all",
  "body": """<p><code>payment_method_types</code> on the sessions tells you which methods are actually in play. <code>us_bank_account</code>, <code>sepa_debit</code>, <code>boleto</code>, <code>konbini</code> and <code>oxxo</code> all settle asynchronously. Seeing any of them on a live session is enough to know this failure mode applies to you today.</p>"""},
 {"h": "Gate fulfilment on payment_status, not on the event",
  "body": """<p>One condition in the handler: fulfil only when <code>payment_status != "unpaid"</code>. That covers <code>paid</code> and <code>no_payment_required</code>, which is Stripe's own reference implementation and the whole fix on the happy path.</p>"""},
 {"h": "Subscribe to both async events and give each a branch",
  "body": """<p>Add <code>checkout.session.async_payment_succeeded</code> and <code>checkout.session.async_payment_failed</code> to the event destination alongside <code>completed</code>. Succeeded is where a delayed order actually gets fulfilled; failed is where it gets cancelled, and without it the failure has nowhere to land.</p>"""},
],
"verify": """<p>Re-run the script over the same window. Any remaining unpaid sessions should be genuinely in flight rather than already failed.</p>
<pre><code class="language-bash">python3 stripe_unpaid_complete_sessions.py --days 90
# processing  cs_test_a1B2  complete but unpaid, and the PaymentIntent is still processing.
# 0 session(s) fulfilled against a payment that has already failed</code></pre>""",
"code_intro": "One paginated GET plus one expanded retrieve per flagged session, and no writes &mdash; a restricted key with read access to Checkout Sessions and PaymentIntents is enough. The classifier is pure and takes four fields off the session, because the distinction that matters here &mdash; still in flight versus already failed &mdash; is a rule about field values and deserves to be tested as one.",
"py_file": "stripe_unpaid_complete_sessions.py",
"py": '''"""Report Stripe Checkout Sessions that are complete but were never paid.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Checkout Sessions and PaymentIntents. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_unpaid_complete_sessions")

API = "https://api.stripe.com/v1"

# Payment methods that settle after the session completes rather than during it.
DELAYED = ("us_bank_account", "sepa_debit", "boleto", "konbini", "oxxo")

# PaymentIntent states that mean the async payment is already lost.
DEAD_INTENT = ("requires_payment_method", "canceled")


def verdict(status, payment_status, intent_status=None, methods=None):
    """Classify one Checkout Session. Pure, so the rules can be tested offline.

    Takes the session's `status` and `payment_status`, the expanded
    `payment_intent.status` where one was fetched, and `payment_method_types`.
    Returns (state, detail).
    """
    if status != "complete":
        return ("skipped",
                "status is %r; this check only looks at complete sessions" % status)
    if payment_status == "no_payment_required":
        return ("free", "nothing to collect on this session")
    if payment_status == "paid":
        return ("paid", "payment_status is paid; fulfilment is safe")

    delayed = sorted(m for m in (methods or []) if m in DELAYED)
    note = (" Delayed method(s) on the session: %s." % ", ".join(delayed)) if delayed else ""
    if intent_status == "processing":
        return ("processing",
                "complete but unpaid, and the PaymentIntent is still processing. "
                "Wait for checkout.session.async_payment_succeeded before "
                "fulfilling." + note)
    if intent_status in DEAD_INTENT:
        return ("failed",
                "complete but unpaid, and the PaymentIntent is %s: the payment "
                "failed after the session completed. Anything fulfilled against "
                "it has to be unwound." % intent_status + note)
    return ("unpaid",
            "complete but payment_status is unpaid, and the PaymentIntent state is "
            "%s. Do not treat completed as paid." % (intent_status or "unknown") + note)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def complete_sessions(session, since, cap):
    """Every session Stripe considers complete in the window."""
    out = []
    params = {"status": "complete", "created[gte]": since, "limit": 100}
    while True:
        page = get(session, "/checkout/sessions", params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= cap:
            break
        params["starting_after"] = data[-1]["id"]
    return out


def intent_status(session, cs_id):
    """Expand the PaymentIntent for one session, so a failure can be told from a wait."""
    cs = get(session, "/checkout/sessions/" + cs_id, {"expand[]": "payment_intent"})
    intent = cs.get("payment_intent")
    if isinstance(intent, dict):
        return intent.get("status")
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="how far back to look for complete sessions")
    ap.add_argument("--max-sessions", type=int, default=5000,
                    help="stop paginating after this many sessions")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    failed = 0
    waiting = 0
    for cs in complete_sessions(s, since, args.max_sessions):
        if cs.get("payment_status") != "unpaid":
            continue
        pi = intent_status(s, cs["id"])
        state, detail = verdict(cs.get("status"), cs.get("payment_status"), pi,
                                cs.get("payment_method_types"))
        log.warning("%-11s %-28s %s", state, cs["id"], detail)
        if state == "failed":
            failed += 1
        else:
            waiting += 1

    log.info("%d session(s) fulfilled against a payment that has already failed, "
             "%d still in flight", failed, waiting)
    if failed or waiting:
        log.warning("  repair: gate fulfilment on payment_status != \\"unpaid\\", not "
                    "on the completed event alone")
        log.warning("  and subscribe the event destination to "
                    "checkout.session.async_payment_succeeded and "
                    "checkout.session.async_payment_failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-unpaid-complete-sessions.mjs",
"js": '''/**
 * Report Stripe Checkout Sessions that are complete but were never paid.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access to
 * Checkout Sessions and PaymentIntents. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Payment methods that settle after the session completes rather than during it.
export const DELAYED = ['us_bank_account', 'sepa_debit', 'boleto', 'konbini', 'oxxo'];

// PaymentIntent states that mean the async payment is already lost.
const DEAD_INTENT = ['requires_payment_method', 'canceled'];

/**
 * Classify one Checkout Session. Pure, so the rules can be tested offline.
 * status and payment_status are independent: complete does not mean paid.
 */
export function verdict(status, paymentStatus, intentStatus = null, methods = null) {
  if (status !== 'complete') {
    return ['skipped',
      `status is '${status}'; this check only looks at complete sessions`];
  }
  if (paymentStatus === 'no_payment_required') {
    return ['free', 'nothing to collect on this session'];
  }
  if (paymentStatus === 'paid') {
    return ['paid', 'payment_status is paid; fulfilment is safe'];
  }

  const delayed = (methods ?? []).filter((m) => DELAYED.includes(m)).sort();
  const note = delayed.length
    ? ` Delayed method(s) on the session: ${delayed.join(', ')}.`
    : '';
  if (intentStatus === 'processing') {
    return ['processing',
      'complete but unpaid, and the PaymentIntent is still processing. Wait for ' +
      'checkout.session.async_payment_succeeded before fulfilling.' + note];
  }
  if (DEAD_INTENT.includes(intentStatus)) {
    return ['failed',
      `complete but unpaid, and the PaymentIntent is ${intentStatus}: the payment ` +
      'failed after the session completed. Anything fulfilled against it has to ' +
      'be unwound.' + note];
  }
  return ['unpaid',
    'complete but payment_status is unpaid, and the PaymentIntent state is ' +
    `${intentStatus ?? 'unknown'}. Do not treat completed as paid.` + note];
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

export async function completeSessions(key, since, cap = 5000) {
  const out = [];
  const params = { status: 'complete', 'created[gte]': since, limit: 100 };
  for (;;) {
    const page = await get(key, '/checkout/sessions', params);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= cap) break;
    params.starting_after = data[data.length - 1].id;
  }
  return out;
}

export async function intentStatus(key, csId) {
  const cs = await get(key, `/checkout/sessions/${csId}`, { 'expand[]': 'payment_intent' });
  const intent = cs.payment_intent;
  return intent && typeof intent === 'object' ? intent.status : null;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.argv[2] ?? 90);
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  let failed = 0;
  let waiting = 0;
  for (const cs of await completeSessions(key, since)) {
    if (cs.payment_status !== 'unpaid') continue;
    const pi = await intentStatus(key, cs.id);
    const [state, detail] = verdict(cs.status, cs.payment_status, pi,
      cs.payment_method_types);
    console.warn(`${state.padEnd(11)} ${cs.id.padEnd(28)} ${detail}`);
    if (state === 'failed') failed += 1; else waiting += 1;
  }

  console.log(`${failed} session(s) fulfilled against a payment that has already ` +
              `failed, ${waiting} still in flight`);
  if (failed || waiting) {
    console.warn('  repair: gate fulfilment on payment_status != "unpaid", not on ' +
                 'the completed event alone');
    console.warn('  and subscribe the event destination to ' +
                 'checkout.session.async_payment_succeeded and ' +
                 'checkout.session.async_payment_failed');
  }
  process.exitCode = failed ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The distinction these tests protect is the one the whole check exists for: <em>unpaid and still processing</em> is a normal ACH payment doing exactly what it is supposed to, and <em>unpaid with a dead PaymentIntent</em> is stock that has already left the warehouse. Collapsing them into one alert makes the check unusable within a week, because the first kind vastly outnumbers the second.",
"test_py_file": "test_stripe_unpaid_complete_sessions.py",
"test_py": '''from stripe_unpaid_complete_sessions import verdict


def test_a_paid_session_is_safe_to_fulfil():
    assert verdict("complete", "paid")[0] == "paid"


def test_an_open_session_is_not_this_checks_business():
    assert verdict("open", "unpaid")[0] == "skipped"


def test_unpaid_while_the_intent_processes_is_money_in_flight():
    state, detail = verdict("complete", "unpaid", "processing", ["us_bank_account"])
    assert state == "processing"
    assert "us_bank_account" in detail


def test_a_dead_intent_means_fulfilment_has_to_be_unwound():
    # Same status, same payment_status as the test above. Only the intent differs,
    # and it is the difference between waiting and having lost the goods.
    state, detail = verdict("complete", "unpaid", "requires_payment_method")
    assert state == "failed"
    assert "unwound" in detail


def test_no_payment_required_is_not_unpaid():
    assert verdict("complete", "no_payment_required")[0] == "free"
''',
"test_js_file": "stripe-unpaid-complete-sessions.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-unpaid-complete-sessions.mjs';

test('a paid session is safe to fulfil', () => {
  assert.equal(verdict('complete', 'paid')[0], 'paid');
});

test('an open session is not this check\\'s business', () => {
  assert.equal(verdict('open', 'unpaid')[0], 'skipped');
});

test('unpaid while the intent processes is money in flight', () => {
  const [state, detail] = verdict('complete', 'unpaid', 'processing', ['us_bank_account']);
  assert.equal(state, 'processing');
  assert.match(detail, /us_bank_account/);
});

test('a dead intent means fulfilment has to be unwound', () => {
  const [state, detail] = verdict('complete', 'unpaid', 'requires_payment_method');
  assert.equal(state, 'failed');
  assert.match(detail, /unwound/);
});

test('no payment required is not unpaid', () => {
  assert.equal(verdict('complete', 'no_payment_required')[0], 'free');
});
''',
"faq": [
 ("Does checkout.session.completed mean the payment succeeded?",
  "No. It means the customer finished the Checkout flow. status: complete explicitly allows payment to still be in progress, which is why payment_status exists as a separate field. For cards the two line up; for delayed methods they do not."),
 ("Which payment methods settle asynchronously?",
  "ACH Direct Debit (us_bank_account), SEPA Direct Debit, Boleto, Konbini and OXXO are the common ones. They complete the session immediately and settle days later, so payment_status stays unpaid in between and resolves through the async events."),
 ("What is the actual code fix?",
  "One condition: fulfil only when payment_status is not unpaid. That admits paid and no_payment_required and excludes everything still in flight. It is what Stripe's own fulfilment reference does, and it is correct for card payments too, so there is no reason to special-case anything."),
 ("What happens if an async payment fails after I shipped?",
  "Stripe sends checkout.session.async_payment_failed and the PaymentIntent lands on requires_payment_method or canceled. Nothing reverses automatically. You need a branch on that event that cancels the order and, if it has already shipped, raises it for a human. Without the subscription, the failure is only visible in the Dashboard."),
 ("Should I fulfil on the session or on the PaymentIntent?",
  "Either works if you check the right field, but the session is usually simpler because it carries your client_reference_id and metadata. Handle completed and async_payment_succeeded on the same code path, gate both on payment_status, and make the path idempotent on the session id so the two events cannot double-fulfil."),
],
"related": [
 ("/stripe/checkout-expired-session-share/", "Most Checkout Sessions expire unpaid and nobody is told"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions carry no ID that maps back to your order"),
 ("/stripe/refunds-failed-or-stuck/", "Refunds that failed or are stuck pending"),
],
"citations": [CITE_FULFILMENT, CITE_SESSION_OBJ, CITE_SESSION_RETRIEVE, CITE_ACH],
},

]
