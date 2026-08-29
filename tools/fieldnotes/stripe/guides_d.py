#!/usr/bin/env python3
"""/stripe/ field notes — batch D: payments and intents.

Four problems that all live in the same place: an object Stripe created for you
that never reached a terminal state, and nothing in your application noticed.
Every script here is read only. They hold a credential to a live payments
account, so none of them writes: they read, they say exactly what is wrong, and
they print the repair for a human to run.
"""

CITE_PI_LIFECYCLE = ("The PaymentIntent lifecycle — Stripe Docs",
                     "https://docs.stripe.com/payments/paymentintents/lifecycle")
CITE_PI_OBJECT = ("The PaymentIntent object — Stripe API reference",
                  "https://docs.stripe.com/api/payment_intents/object")
CITE_PI_LIST = ("List PaymentIntents — Stripe API reference",
                "https://docs.stripe.com/api/payment_intents/list")
CITE_3DS = ("3D Secure authentication — Stripe Docs",
            "https://docs.stripe.com/payments/3d-secure")
CITE_CHARGE_OBJECT = ("The Charge object — Stripe API reference",
                      "https://docs.stripe.com/api/charges/object")
CITE_DECLINES = ("Declines — Stripe Docs", "https://docs.stripe.com/declines")
CITE_RADAR_RULES = ("Radar rules — Stripe Docs", "https://docs.stripe.com/radar/rules")
CITE_RADAR_REVIEWS = ("Reviewing payments — Stripe Docs",
                      "https://docs.stripe.com/radar/reviews")
CITE_REFUND_OBJECT = ("The Refund object — Stripe API reference",
                      "https://docs.stripe.com/api/refunds/object")
CITE_REFUNDS = ("Refunds — Stripe Docs", "https://docs.stripe.com/refunds")
CITE_KEYS = ("API keys — Stripe Docs", "https://docs.stripe.com/keys")

GUIDES = [

{
"slug": "abandoned-requires-action-intents",
"title": "3DS handoff breaks and requires_action intents pile up",
"description": "PaymentIntents freeze at requires_action when the client never finishes the authentication handoff. No error is raised and no money moves.",
"h1": "3DS handoff breaks and requires_action intents pile up",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe requires_action stuck", "stripe 3ds not completing",
             "payment intent requires_action", "stripe next_action redirect",
             "stripe sca abandoned payments"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Card volume from Europe and India reads lower than your traffic says it should. Nothing fails. There are no declines to look at, no errors in the logs, and no support tickets, because from the customer's side the page simply did nothing. The intents stopped at <code>requires_action</code> and stayed there.",
"short_answer": """<p>Paginate <code>GET /v1/payment_intents</code> and count the ones whose <code>status</code> is <code>"requires_action"</code> with a <code>created</code> timestamp older than 24 hours. An intent in that state is waiting on the customer's bank, and 24 hours is far longer than any real authentication takes.</p>
<p>Bucket the results by <code>next_action.type</code>. <code>use_stripe_sdk</code> failing points at the client never calling <code>confirmPayment</code>; <code>redirect_to_url</code> failing points at a <code>return_url</code> that does not resolve, or a redirect blocked inside an iframe or an in-app webview.</p>""",
"problem": """<p>An intent at <code>requires_action</code> is not a failure and Stripe does not treat it as one. The authorization was never attempted, so there is no decline code, no <code>last_payment_error</code>, and no <code>payment_intent.payment_failed</code> event to subscribe to. The object just sits in a non-terminal state with a <code>next_action</code> nobody ever acted on.</p>
<p>That makes it invisible to every dashboard you already look at. Conversion reports built on succeeded payments show a dip with no cause attached. Fraud reports show nothing, because Radar never saw a charge. The only place the failure is written down is the intent itself, and nothing in a normal integration reads intents that did not succeed.</p>""",
"why": """<p><strong>The client never handles the returned status.</strong> A server-confirmed flow returns an intent that needs <code>stripe.handleNextAction({clientSecret})</code>. Code that checks only for <code>succeeded</code> and otherwise shows a spinner leaves the customer looking at a page that will never change.</p>
<p><strong>The <code>return_url</code> does not exist.</strong> The bank's redirect flow sends the customer back to a URL you supplied at confirm time. If that route was renamed, or points at a staging host, or returns a page that does not re-retrieve the intent by <code>client_secret</code>, the customer lands on something broken after authenticating successfully. The money is one API round trip away and never gets collected.</p>
<p><strong>The redirect is blocked by the frame it runs in.</strong> Issuer authentication pages set <code>X-Frame-Options</code>. Launching 3DS inside a cross-origin iframe, or inside an in-app browser that refuses third-party redirects, produces a blank frame rather than an error. This is why the problem tends to look regional: SCA applies to European cards, and RBI mandates step-up authentication in India, so those are the cards that reach the step at all.</p>
<p><strong>Nothing expires loudly.</strong> The intent stays valid, so there is no cleanup job that trips over it and no alert that fires. It accumulates.</p>""",
"steps": [
 {"h": "Count the intents currently frozen at the authentication step",
  "body": """<p>Anything at <code>requires_action</code> for more than 24 hours is not a customer who is still deciding. Run this over a 30-day window so you can see whether the pile started on a particular day, which is usually a deploy.</p>"""},
 {"h": "Bucket them by next_action.type",
  "body": """<p>The distribution is the diagnosis. If everything failing is <code>redirect_to_url</code>, the problem is the return trip. If it is <code>use_stripe_sdk</code>, the client never called into the SDK at all. A mix of both usually means one shared code path in front of the two.</p>"""},
 {"h": "Look for intents with no next_action at all",
  "body": """<p><code>requires_action</code> with an empty <code>next_action</code> is a different bug: the intent is waiting for something the client was never told to do. Nothing on the customer's side can complete it, so these are dead on arrival rather than abandoned.</p>"""},
 {"h": "Open the return_url yourself",
  "body": """<p>Take the <code>return_url</code> from a recent confirm and request it directly. It should be a real page on the live host that reads <code>payment_intent_client_secret</code> from the query string and re-retrieves the intent. A 404, a redirect to a login wall, or a page that ignores the parameter each produce exactly the symptom above.</p>"""},
 {"h": "Cross-check the charges for authentication_required",
  "body": """<p><code>GET /v1/charges</code> with <code>outcome.reason</code> of <code>authentication_required</code> is the related off-session failure: a saved card that needed a step-up when nobody was present to give one. It is a different fix, but the same root cause of assuming authentication never happens.</p>"""},
],
"verify": """<p>Re-run the script after the client change ships. The abandoned count should stop growing; existing ones do not clear themselves, so compare against a fresh window rather than the total.</p>
<pre><code class="language-bash">python3 stripe_requires_action.py --days 2
# scanned 214 intent(s): 0 abandoned, 3 in-flight, 0 with no next_action</code></pre>""",
"code_intro": "The script makes one paginated GET against PaymentIntents and no writes &mdash; a restricted key with read access to PaymentIntents is enough, and is what you should give it. The clock is passed into the classifier rather than read inside it, so the ageing rule is testable at a pinned timestamp instead of being true only on the day you wrote the test.",
"py_file": "stripe_requires_action.py",
"py": '''"""Report Stripe PaymentIntents abandoned at the authentication step.

Read only. One paginated GET, no writes: give this a RESTRICTED key with read
access to PaymentIntents. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_requires_action")

API = "https://api.stripe.com/v1"
STALE_SECONDS = 24 * 3600


def classify(intent, now, stale_after=STALE_SECONDS):
    """Classify one PaymentIntent. Pure, so the rules can be tested without a network.

    Returns (state, detail). `now` is a unix timestamp passed in rather than read
    here, so the ageing rule can be tested against a pinned clock.
    """
    status = intent.get("status")
    if status != "requires_action":
        return ("other", "status %r, not waiting on authentication" % (status,))
    created = intent.get("created")
    if not isinstance(created, int):
        return ("unknown", "no created timestamp, so the intent cannot be aged")
    action = (intent.get("next_action") or {}).get("type")
    if not action:
        return ("no-next-action",
                "requires_action with an empty next_action: the client was never "
                "told what to do, so nothing can finish this")
    hours = int((now - created) // 3600)
    if now - created < stale_after:
        return ("in-flight",
                "%s, %dh old, still inside the window a customer plausibly needs"
                % (action, hours))
    return ("abandoned",
            "%s, %dh old: the customer left the authentication step and never came back"
            % (action, hours))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def payment_intents(session, since, cap):
    """Yield PaymentIntents created since `since`, newest first, up to `cap`."""
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/payment_intents", **params)
        data = page.get("data", [])
        for pi in data:
            yield pi
            seen += 1
            if seen >= cap:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to scan (default 30)")
    ap.add_argument("--stale-hours", type=int, default=24,
                    help="age at which requires_action counts as abandoned")
    ap.add_argument("--max-intents", type=int, default=5000,
                    help="stop paginating after this many intents")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    since = now - args.days * 86400
    stale_after = args.stale_hours * 3600

    counts = {}
    by_action = {}
    examples = []
    scanned = 0

    for pi in payment_intents(s, since, args.max_intents):
        scanned += 1
        state, detail = classify(pi, now, stale_after)
        counts[state] = counts.get(state, 0) + 1
        if state in ("abandoned", "no-next-action"):
            action = (pi.get("next_action") or {}).get("type") or "none"
            by_action[action] = by_action.get(action, 0) + 1
            if len(examples) < 10:
                examples.append((pi["id"], detail))

    abandoned = counts.get("abandoned", 0)
    in_flight = counts.get("in-flight", 0)
    headless = counts.get("no-next-action", 0)

    for pid, detail in examples:
        log.warning("%s  %s", pid, detail)

    log.info("scanned %d intent(s): %d abandoned, %d in-flight, %d with no next_action",
             scanned, abandoned, in_flight, headless)

    if by_action:
        for action, n in sorted(by_action.items(), key=lambda kv: -kv[1]):
            log.warning("  %-24s %d", action, n)

    waiting = abandoned + in_flight
    if waiting:
        # Not the true abandonment rate: Stripe does not report which succeeded
        # intents passed through requires_action on their way, so the honest
        # denominator here is the intents sitting at the step right now.
        log.info("  %.0f%% of the intents at the authentication step are stalled",
                 100.0 * abandoned / waiting)

    if abandoned or headless:
        log.warning("  repair: handle the returned status on the client, e.g. "
                    "await stripe.confirmPayment({elements, confirmParams: {return_url}})")
        log.warning("  repair: for server-confirmed flows call "
                    "stripe.handleNextAction({clientSecret}) with the returned secret")
        log.warning("  check: request the return_url directly and confirm it "
                    "re-retrieves the intent by client_secret")
        log.warning("  check: stop launching 3DS inside a cross-origin iframe")
        log.warning("  to close out the dead ones: POST %s/payment_intents/{id}/cancel "
                    "-d cancellation_reason=abandoned", API)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-requires-action.mjs",
"js": '''/**
 * Report Stripe PaymentIntents abandoned at the authentication step.
 *
 * Read only. One paginated GET, no writes: give this a RESTRICTED key with read
 * access to PaymentIntents. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const STALE_SECONDS = 24 * 3600;

/**
 * Classify one PaymentIntent. Pure, so the rules can be tested without a network.
 * `now` is a unix timestamp passed in, so the ageing rule can be tested at a
 * pinned clock rather than only on the day the test was written.
 */
export function classify(intent, now, staleAfter = STALE_SECONDS) {
  const status = intent.status;
  if (status !== 'requires_action') {
    return ['other', `status ${JSON.stringify(status)}, not waiting on authentication`];
  }
  const created = intent.created;
  if (!Number.isInteger(created)) {
    return ['unknown', 'no created timestamp, so the intent cannot be aged'];
  }
  const action = intent.next_action?.type;
  if (!action) {
    return ['no-next-action',
      'requires_action with an empty next_action: the client was never told ' +
      'what to do, so nothing can finish this'];
  }
  const hours = Math.floor((now - created) / 3600);
  if (now - created < staleAfter) {
    return ['in-flight',
      `${action}, ${hours}h old, still inside the window a customer plausibly needs`];
  }
  return ['abandoned',
    `${action}, ${hours}h old: the customer left the authentication step and never came back`];
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

export async function* paymentIntents(key, since, cap) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/payment_intents', params);
    const data = page.data ?? [];
    for (const pi of data) {
      yield pi;
      seen += 1;
      if (seen >= cap) return;
    }
    if (!page.has_more || data.length === 0) return;
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

  const days = Number(process.env.DAYS ?? 30);
  const staleAfter = Number(process.env.STALE_HOURS ?? 24) * 3600;
  const now = Math.floor(Date.now() / 1000);
  const since = now - days * 86400;

  const counts = new Map();
  const byAction = new Map();
  const examples = [];
  let scanned = 0;

  for await (const pi of paymentIntents(key, since, 5000)) {
    scanned += 1;
    const [state, detail] = classify(pi, now, staleAfter);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'abandoned' || state === 'no-next-action') {
      const action = pi.next_action?.type ?? 'none';
      byAction.set(action, (byAction.get(action) ?? 0) + 1);
      if (examples.length < 10) examples.push([pi.id, detail]);
    }
  }

  const abandoned = counts.get('abandoned') ?? 0;
  const inFlight = counts.get('in-flight') ?? 0;
  const headless = counts.get('no-next-action') ?? 0;

  for (const [id, detail] of examples) console.warn(`${id}  ${detail}`);

  console.log(`scanned ${scanned} intent(s): ${abandoned} abandoned, ` +
              `${inFlight} in-flight, ${headless} with no next_action`);

  for (const [action, n] of [...byAction].sort((a, b) => b[1] - a[1])) {
    console.warn(`  ${action.padEnd(24)} ${n}`);
  }

  const waiting = abandoned + inFlight;
  if (waiting) {
    // Not the true abandonment rate: Stripe does not report which succeeded
    // intents passed through requires_action, so the honest denominator is the
    // intents sitting at the step right now.
    const pct = Math.round((100 * abandoned) / waiting);
    console.log(`  ${pct}% of the intents at the authentication step are stalled`);
  }

  if (abandoned || headless) {
    console.warn('  repair: handle the returned status on the client, e.g. ' +
                 'await stripe.confirmPayment({elements, confirmParams: {return_url}})');
    console.warn('  repair: for server-confirmed flows call ' +
                 'stripe.handleNextAction({clientSecret}) with the returned secret');
    console.warn('  check: request the return_url directly and confirm it ' +
                 're-retrieves the intent by client_secret');
    console.warn('  check: stop launching 3DS inside a cross-origin iframe');
    console.warn(`  to close out the dead ones: POST ${API}/payment_intents/{id}/cancel ` +
                 '-d cancellation_reason=abandoned');
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
"test_intro": "Two cases carry the note. An intent one hour into <code>requires_action</code> is a customer reading a bank prompt, and calling that broken would bury the real signal under normal traffic. An intent at <code>requires_action</code> with an empty <code>next_action</code> is not abandoned at all &mdash; nobody could have completed it &mdash; and folding it into the abandoned count sends you to look at the wrong layer.",
"test_py_file": "test_stripe_requires_action.py",
"test_py": '''from stripe_requires_action import classify

NOW = 1_800_000_000


def pi(status="requires_action", age_h=48, action="redirect_to_url"):
    out = {"status": status, "created": NOW - age_h * 3600}
    if action is not None:
        out["next_action"] = {"type": action}
    return out


def test_old_requires_action_is_abandoned():
    state, detail = classify(pi(age_h=48), NOW)
    assert state == "abandoned"
    assert "redirect_to_url" in detail


def test_recent_requires_action_is_not_abandoned():
    # A customer reading a bank prompt is not a broken integration.
    state, _ = classify(pi(age_h=1), NOW)
    assert state == "in-flight"


def test_empty_next_action_is_its_own_state():
    # Nobody could have completed this one, so it is a different bug.
    state, detail = classify(pi(age_h=48, action=None), NOW)
    assert state == "no-next-action"
    assert "never" in detail


def test_other_statuses_are_left_alone():
    assert classify(pi(status="succeeded"), NOW)[0] == "other"


def test_missing_created_is_not_silently_healthy():
    assert classify({"status": "requires_action"}, NOW)[0] == "unknown"
''',
"test_js_file": "stripe-requires-action.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-requires-action.mjs';

const NOW = 1800000000;

function pi({ status = 'requires_action', ageH = 48, action = 'redirect_to_url' } = {}) {
  const out = { status, created: NOW - ageH * 3600 };
  if (action !== null) out.next_action = { type: action };
  return out;
}

test('old requires_action is abandoned', () => {
  const [state, detail] = classify(pi({ ageH: 48 }), NOW);
  assert.equal(state, 'abandoned');
  assert.match(detail, /redirect_to_url/);
});

test('recent requires_action is not abandoned', () => {
  assert.equal(classify(pi({ ageH: 1 }), NOW)[0], 'in-flight');
});

test('empty next_action is its own state', () => {
  const [state, detail] = classify(pi({ ageH: 48, action: null }), NOW);
  assert.equal(state, 'no-next-action');
  assert.match(detail, /never/);
});

test('other statuses are left alone', () => {
  assert.equal(classify(pi({ status: 'succeeded' }), NOW)[0], 'other');
});

test('missing created is not silently healthy', () => {
  assert.equal(classify({ status: 'requires_action' }, NOW)[0], 'unknown');
});
''',
"faq": [
 ("How long should a PaymentIntent stay in requires_action?",
  "Minutes. The customer is being shown a bank prompt or redirected to an issuer page, and either finishes or gives up within one session. Twenty-four hours is a deliberately generous threshold that no genuine authentication reaches, so anything past it is a customer who was never able to complete the step."),
 ("Why does this only affect European and Indian cards?",
  "Because those are the cards that reach the authentication step at all. SCA applies to card payments in the European Economic Area and the UK, and the Reserve Bank of India mandates step-up authentication. A broken 3DS handoff is invisible on US traffic that mostly frictionlessly authorizes, which is why the regional split in your conversion numbers is the first clue."),
 ("Is requires_action with no next_action the same problem?",
  "No. An intent waiting for action with nothing populated in next_action cannot be completed by the customer at all, because the client was never given anything to do. It usually means the confirm call did not go through the path that populates it. Treat it as a separate bug from an abandoned redirect."),
 ("Can I just cancel the stuck intents and move on?",
  "You can, with cancellation_reason set to abandoned, and it will tidy your reporting. It does not recover the payment and it does not stop the next one from stalling. Fix the client handoff first, then clear the backlog, or you will be clearing it again next month."),
 ("Does this script need a live secret key?",
  "No. A restricted key with read access to PaymentIntents covers every call it makes. It never confirms, cancels, or captures anything, so if the key leaks the worst case is that somebody learns the shape of your payment volume."),
],
"related": [
 ("/woocommerce/orders-stuck-requires-action-3ds/", "Orders stuck at requires_action after 3DS"),
 ("/stripe/stale-requires-payment-method-intents/", "Intents sitting in requires_payment_method for weeks"),
 ("/woocommerce/declined-card-order-stuck-pending/", "Declined card leaves the order stuck pending"),
],
"citations": [CITE_PI_LIFECYCLE, CITE_3DS, CITE_PI_OBJECT, CITE_KEYS],
},

{
"slug": "stale-requires-payment-method-intents",
"title": "PaymentIntents sit in requires_payment_method for weeks",
"description": "Intents created on page load and never confirmed pile up forever. Checkout starts look healthy while payment volume quietly does not match them.",
"h1": "paymentIntents sit in requires_payment_method for weeks",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe requires_payment_method stuck",
             "stripe incomplete payments", "payment intent never confirmed",
             "stripe abandoned payment intents", "requires_confirmation stuck"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Payments page shows a long tail of incomplete payments that never resolve into anything. Checkout starts and successful payments have drifted apart by a factor nobody can explain, and the gap grows every week. Most of those intents were never going to succeed: they were created before the customer had done anything, and nothing ever went back to them.",
"short_answer": """<p>Paginate <code>GET /v1/payment_intents</code> and count the ones older than seven days still sitting at <code>requires_payment_method</code> or <code>requires_confirmation</code>. Anything over roughly 30% of the intents in that window means the integration is creating intents it does not intend to confirm.</p>
<p>Split the stale ones on whether <code>last_payment_error</code> is <code>null</code>. Null means no payment was ever attempted, which is a page-load creation problem. Populated means the customer tried and was declined, and nothing offered them a retry.</p>""",
"problem": """<p><code>requires_payment_method</code> is the state a PaymentIntent is born in, and the state it returns to after every failed confirmation. Those two facts make it the single least informative status on the object: a brand new intent and a twice-declined one look identical unless you read <code>last_payment_error</code> as well.</p>
<p>Because it is also a perfectly valid resting state, nothing anywhere complains. Stripe does not expire these, does not emit an event about them, and does not surface them outside the incomplete filter on the Payments page. They accumulate for as long as the integration has existed, and the first person to notice is usually whoever is trying to reconcile checkout analytics against payment volume and cannot make the numbers meet.</p>""",
"why": """<p><strong>The intent is created on page load instead of at confirm time.</strong> This is the common one, and it used to be the documented pattern. Every visitor who reaches the payment step gets an intent whether or not they ever type a card number, so the stale pile grows in proportion to traffic rather than to failures.</p>
<p><strong>Nothing retries after a decline.</strong> A declined confirmation puts the intent back at <code>requires_payment_method</code> with the reason in <code>last_payment_error</code>. If the UI shows a generic failure and starts over with a fresh intent, the old one stays behind forever and the customer never sees the actual message from their bank.</p>
<p><strong>Manual confirmation that never happens.</strong> With <code>confirmation_method: manual</code> the intent lands at <code>requires_confirmation</code> and waits for a server-side confirm call. A background job that crashes, or a queue that drops the message, leaves the intent one API call short of completion with nothing to indicate it.</p>
<p><strong>Nobody cancels anything.</strong> Cancellation is a deliberate write, and most integrations have no code path that performs it. The default behaviour of the whole system is to keep every dead intent indefinitely.</p>""",
"steps": [
 {"h": "Scan intents older than seven days",
  "body": """<p>Seven days is well past any real checkout session, including the ones where somebody genuinely came back the next morning. Anything still unconfirmed at that age is not going to be.</p>"""},
 {"h": "Split never-attempted from declined",
  "body": """<p>The <code>last_payment_error</code> field decides which of the two problems you have, and they have entirely different fixes. Do not read the totals before reading the split; a large never-attempted bucket and a large declined bucket look the same in a headline count and lead you to opposite conclusions.</p>"""},
 {"h": "Read the decline codes on the declined bucket",
  "body": """<p><code>last_payment_error.code</code> and <code>decline_code</code> tell you whether these are genuine issuer declines, a card that expired, or something your own configuration caused. A pile of one specific code is a configuration problem wearing a decline's clothes.</p>"""},
 {"h": "Count requires_confirmation separately",
  "body": """<p>These are not customer behaviour at all. Every one of them is a server-side confirm call that your code owed Stripe and never made, so the count is a direct measure of a broken job rather than of checkout friction.</p>"""},
 {"h": "Move intent creation behind the pay button",
  "body": """<p>Creating the intent when the customer submits, rather than when the page renders, removes the never-attempted bucket entirely. For the declined bucket, reuse the same intent for the retry and show <code>last_payment_error.message</code> instead of a generic failure.</p>"""},
],
"verify": """<p>Re-run the script against a window that begins after the change shipped. The stale share in the new window should drop toward zero even while the historical backlog is untouched.</p>
<pre><code class="language-bash">python3 stripe_stale_intents.py --days 14
# 312 intent(s) older than 7d: 4 stale (1%) - 0 never-attempted, 4 declined, 0 unconfirmed</code></pre>""",
"code_intro": "One paginated GET against PaymentIntents, no writes &mdash; a restricted key with read access to PaymentIntents is all it needs. The classifier is pure and takes the clock as an argument, because the interesting behaviour is entirely about which bucket a given object falls into, and that should be readable without tracing a request loop.",
"py_file": "stripe_stale_intents.py",
"py": '''"""Report Stripe PaymentIntents that were created and never confirmed.

Read only. One paginated GET, no writes: give this a RESTRICTED key with read
access to PaymentIntents. The repair is printed, never performed, because this
script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_stale_intents")

API = "https://api.stripe.com/v1"
STALE_SECONDS = 7 * 86400
OPEN_STATUSES = ("requires_payment_method", "requires_confirmation")


def classify(intent, now, stale_after=STALE_SECONDS):
    """Classify one PaymentIntent. Pure, so the rules can be tested without a network.

    Returns (state, detail). The split that matters is `last_payment_error`:
    null means nothing was ever attempted, populated means the customer tried and
    was declined. The two look identical in a status count and need opposite fixes.
    """
    status = intent.get("status")
    if status not in OPEN_STATUSES:
        return ("other", "status %r, not an open intent" % (status,))
    created = intent.get("created")
    if not isinstance(created, int):
        return ("unknown", "no created timestamp, so the intent cannot be aged")
    days = int((now - created) // 86400)
    if now - created < stale_after:
        return ("recent", "%s, %dd old, still plausibly live" % (status, days))
    if status == "requires_confirmation":
        return ("unconfirmed",
                "%dd old: confirmation_method is manual and the server never "
                "called confirm" % days)
    err = intent.get("last_payment_error") or {}
    if err:
        reason = err.get("decline_code") or err.get("code") or "no code given"
        return ("declined",
                "%dd old: last attempt was declined (%s) and nothing offered a retry"
                % (days, reason))
    return ("never-attempted",
            "%dd old: created but no payment method was ever attached" % days)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def payment_intents(session, since, until, cap):
    """Yield PaymentIntents created in [since, until), up to `cap` of them."""
    seen = 0
    params = {"limit": 100, "created[gte]": since, "created[lt]": until}
    while True:
        page = get(session, "/payment_intents", **params)
        data = page.get("data", [])
        for pi in data:
            yield pi
            seen += 1
            if seen >= cap:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to scan (default 30)")
    ap.add_argument("--stale-days", type=int, default=7,
                    help="age at which an open intent counts as stale")
    ap.add_argument("--max-intents", type=int, default=5000,
                    help="stop paginating after this many intents")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    stale_after = args.stale_days * 86400
    since = now - args.days * 86400
    until = now - stale_after  # only intents old enough to have a verdict

    counts = {}
    codes = {}
    examples = []
    scanned = 0

    for pi in payment_intents(s, since, until, args.max_intents):
        scanned += 1
        state, detail = classify(pi, now, stale_after)
        counts[state] = counts.get(state, 0) + 1
        if state == "declined":
            err = pi.get("last_payment_error") or {}
            code = err.get("decline_code") or err.get("code") or "unknown"
            codes[code] = codes.get(code, 0) + 1
        if state in ("never-attempted", "declined", "unconfirmed") and len(examples) < 10:
            examples.append((pi["id"], detail))

    never = counts.get("never-attempted", 0)
    declined = counts.get("declined", 0)
    unconfirmed = counts.get("unconfirmed", 0)
    stale = never + declined + unconfirmed

    for pid, detail in examples:
        log.warning("%s  %s", pid, detail)

    share = (100.0 * stale / scanned) if scanned else 0.0
    log.info("%d intent(s) older than %dd: %d stale (%.0f%%) - "
             "%d never-attempted, %d declined, %d unconfirmed",
             scanned, args.stale_days, stale, share, never, declined, unconfirmed)

    for code, n in sorted(codes.items(), key=lambda kv: -kv[1]):
        log.warning("  decline %-28s %d", code, n)

    if share > 30:
        log.warning("  over 30%% of intents in this window never went anywhere")
    if never:
        log.warning("  repair: create the PaymentIntent when the customer submits, "
                    "not when the payment page renders")
    if declined:
        log.warning("  repair: retry on the same intent and show "
                    "last_payment_error.message rather than a generic failure")
    if unconfirmed:
        log.warning("  repair: find the job that owes Stripe "
                    "POST %s/payment_intents/{id}/confirm and fix it", API)
    if stale:
        log.warning("  to clear the backlog: POST %s/payment_intents/{id}/cancel "
                    "-d cancellation_reason=abandoned", API)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-stale-intents.mjs",
"js": '''/**
 * Report Stripe PaymentIntents that were created and never confirmed.
 *
 * Read only. One paginated GET, no writes: give this a RESTRICTED key with read
 * access to PaymentIntents. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const STALE_SECONDS = 7 * 86400;
const OPEN_STATUSES = ['requires_payment_method', 'requires_confirmation'];

/**
 * Classify one PaymentIntent. Pure, so the rules can be tested without a network.
 * The split that matters is last_payment_error: null means nothing was ever
 * attempted, populated means the customer tried and was declined. The two look
 * identical in a status count and need opposite fixes.
 */
export function classify(intent, now, staleAfter = STALE_SECONDS) {
  const status = intent.status;
  if (!OPEN_STATUSES.includes(status)) {
    return ['other', `status ${JSON.stringify(status)}, not an open intent`];
  }
  const created = intent.created;
  if (!Number.isInteger(created)) {
    return ['unknown', 'no created timestamp, so the intent cannot be aged'];
  }
  const days = Math.floor((now - created) / 86400);
  if (now - created < staleAfter) {
    return ['recent', `${status}, ${days}d old, still plausibly live`];
  }
  if (status === 'requires_confirmation') {
    return ['unconfirmed',
      `${days}d old: confirmation_method is manual and the server never called confirm`];
  }
  const err = intent.last_payment_error;
  if (err) {
    const reason = err.decline_code ?? err.code ?? 'no code given';
    return ['declined',
      `${days}d old: last attempt was declined (${reason}) and nothing offered a retry`];
  }
  return ['never-attempted',
    `${days}d old: created but no payment method was ever attached`];
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

export async function* paymentIntents(key, since, until, cap) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since, 'created[lt]': until };
  for (;;) {
    const page = await get(key, '/payment_intents', params);
    const data = page.data ?? [];
    for (const pi of data) {
      yield pi;
      seen += 1;
      if (seen >= cap) return;
    }
    if (!page.has_more || data.length === 0) return;
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

  const days = Number(process.env.DAYS ?? 30);
  const staleDays = Number(process.env.STALE_DAYS ?? 7);
  const staleAfter = staleDays * 86400;
  const now = Math.floor(Date.now() / 1000);
  const since = now - days * 86400;
  const until = now - staleAfter; // only intents old enough to have a verdict

  const counts = new Map();
  const codes = new Map();
  const examples = [];
  let scanned = 0;

  for await (const pi of paymentIntents(key, since, until, 5000)) {
    scanned += 1;
    const [state, detail] = classify(pi, now, staleAfter);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (state === 'declined') {
      const err = pi.last_payment_error ?? {};
      const code = err.decline_code ?? err.code ?? 'unknown';
      codes.set(code, (codes.get(code) ?? 0) + 1);
    }
    if (['never-attempted', 'declined', 'unconfirmed'].includes(state) && examples.length < 10) {
      examples.push([pi.id, detail]);
    }
  }

  const never = counts.get('never-attempted') ?? 0;
  const declined = counts.get('declined') ?? 0;
  const unconfirmed = counts.get('unconfirmed') ?? 0;
  const stale = never + declined + unconfirmed;

  for (const [id, detail] of examples) console.warn(`${id}  ${detail}`);

  const share = scanned ? Math.round((100 * stale) / scanned) : 0;
  console.log(`${scanned} intent(s) older than ${staleDays}d: ${stale} stale (${share}%) - ` +
              `${never} never-attempted, ${declined} declined, ${unconfirmed} unconfirmed`);

  for (const [code, n] of [...codes].sort((a, b) => b[1] - a[1])) {
    console.warn(`  decline ${code.padEnd(28)} ${n}`);
  }

  if (share > 30) console.warn('  over 30% of intents in this window never went anywhere');
  if (never) {
    console.warn('  repair: create the PaymentIntent when the customer submits, ' +
                 'not when the payment page renders');
  }
  if (declined) {
    console.warn('  repair: retry on the same intent and show ' +
                 'last_payment_error.message rather than a generic failure');
  }
  if (unconfirmed) {
    console.warn(`  repair: find the job that owes Stripe POST ${API}` +
                 '/payment_intents/{id}/confirm and fix it');
  }
  if (stale) {
    console.warn(`  to clear the backlog: POST ${API}/payment_intents/{id}/cancel ` +
                 '-d cancellation_reason=abandoned');
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
"test_intro": "The classifier exists to keep two buckets apart that Stripe reports with the same status. A stale intent with no <code>last_payment_error</code> is a page-load creation bug; a stale intent with one is a missing retry. The tests pin that split, and pin that <code>requires_confirmation</code> is never folded in with either of them, because it is your server's omission rather than the customer's.",
"test_py_file": "test_stripe_stale_intents.py",
"test_py": '''from stripe_stale_intents import classify

NOW = 1_800_000_000
DAY = 86400


def pi(status="requires_payment_method", age_d=30, err=None):
    out = {"status": status, "created": NOW - age_d * DAY}
    if err is not None:
        out["last_payment_error"] = err
    return out


def test_old_intent_with_no_error_was_never_attempted():
    state, detail = classify(pi(age_d=30), NOW)
    assert state == "never-attempted"
    assert "no payment method" in detail


def test_old_intent_with_an_error_is_a_missing_retry():
    # Same status, opposite fix: this customer tried and was turned down.
    state, detail = classify(pi(age_d=30, err={"decline_code": "insufficient_funds"}), NOW)
    assert state == "declined"
    assert "insufficient_funds" in detail


def test_requires_confirmation_is_the_servers_omission():
    state, detail = classify(pi(status="requires_confirmation", age_d=30), NOW)
    assert state == "unconfirmed"
    assert "confirm" in detail


def test_a_two_day_old_intent_is_still_live():
    assert classify(pi(age_d=2), NOW)[0] == "recent"


def test_succeeded_intents_are_not_counted():
    assert classify(pi(status="succeeded"), NOW)[0] == "other"
''',
"test_js_file": "stripe-stale-intents.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-stale-intents.mjs';

const NOW = 1800000000;
const DAY = 86400;

function pi({ status = 'requires_payment_method', ageD = 30, err = null } = {}) {
  const out = { status, created: NOW - ageD * DAY };
  if (err !== null) out.last_payment_error = err;
  return out;
}

test('old intent with no error was never attempted', () => {
  const [state, detail] = classify(pi({ ageD: 30 }), NOW);
  assert.equal(state, 'never-attempted');
  assert.match(detail, /no payment method/);
});

test('old intent with an error is a missing retry', () => {
  const [state, detail] = classify(
    pi({ ageD: 30, err: { decline_code: 'insufficient_funds' } }), NOW);
  assert.equal(state, 'declined');
  assert.match(detail, /insufficient_funds/);
});

test('requires_confirmation is the server omission', () => {
  const [state, detail] = classify(pi({ status: 'requires_confirmation', ageD: 30 }), NOW);
  assert.equal(state, 'unconfirmed');
  assert.match(detail, /confirm/);
});

test('a two day old intent is still live', () => {
  assert.equal(classify(pi({ ageD: 2 }), NOW)[0], 'recent');
});

test('succeeded intents are not counted', () => {
  assert.equal(classify(pi({ status: 'succeeded' }), NOW)[0], 'other');
});
''',
"faq": [
 ("Is it wrong to create a PaymentIntent on page load?",
  "It is not wrong, but it costs you a permanent record for every visitor who never pays, and it makes your incomplete-payment count a measure of traffic rather than of failure. Creating the intent when the customer submits keeps the object count proportional to actual attempts, which is what makes the remaining stale ones worth investigating."),
 ("Do stale intents cost money or hold funds?",
  "No. An intent at requires_payment_method has never touched a card, so nothing is authorized and nothing is held. The cost is entirely in reporting: they distort conversion figures and they bury the small number of intents that represent a real broken flow."),
 ("What is the difference between requires_payment_method and requires_confirmation?",
  "The first means no usable payment method is attached, which is where every intent starts and where it returns after a decline. The second only appears when confirmation_method is manual: a payment method is attached and Stripe is waiting for your server to call confirm. One is about the customer, the other is about your code."),
 ("Should I cancel old intents automatically?",
  "Cancelling is safe for genuinely dead intents and sets cancellation_reason so the history stays readable. Do it as a deliberate, rate-limited job over a fixed age threshold rather than as a side effect of the check, and fix the creation pattern first so the job has less to do each week."),
 ("Why does this script only look at intents older than the stale threshold?",
  "Because a younger intent has no verdict yet, and including it would drag the stale percentage down by however much traffic you had today. Bounding the scan at now minus seven days makes the ratio a property of the integration instead of a property of the hour you ran it."),
],
"related": [
 ("/stripe/abandoned-requires-action-intents/", "requires_action intents pile up at the 3DS step"),
 ("/woocommerce/cancel-abandoned-payment-intents/", "Cancel abandoned payment intents"),
 ("/woocommerce/declined-card-order-stuck-pending/", "Declined card leaves the order stuck pending"),
],
"citations": [CITE_PI_LIFECYCLE, CITE_PI_OBJECT, CITE_PI_LIST, CITE_KEYS],
},

{
"slug": "radar-blocked-payments-ignored",
"title": "Radar blocks payments and nobody reads the block reasons",
"description": "Blocked charges never reach the issuer, so they leave no decline code. A rule written years ago can quietly eat good revenue for months.",
"h1": "radar blocks payments and nobody reads the block reasons",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe radar blocked charges", "outcome type blocked",
             "stripe rule blocking payments", "highest_risk_level",
             "stripe not_sent_to_network"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Support keeps hearing the same sentence: my card works everywhere else. The charge shows as failed with a message that says nothing, the customer's bank has no record of the attempt at all, and nobody on your side can say why. The payment never left Stripe.",
"short_answer": """<p>Paginate <code>GET /v1/charges</code> and filter on <code>outcome.type == "blocked"</code>. Those charges carry <code>outcome.network_status</code> of <code>not_sent_to_network</code>, which is the literal statement that the issuer never saw them.</p>
<p>Group by <code>outcome.reason</code>. <code>rule</code> means one of your own Radar rules fired and is the reason you should look at first; <code>highest_risk_level</code> is Radar's built-in threshold; <code>low_probability_of_authorization</code> is Adaptive Acceptance declining to spend a network fee on a charge it expects to fail, and is not fraud at all.</p>""",
"problem": """<p>A blocked charge is not a decline, and the difference is the whole problem. A decline came back from the issuer with a code you can read, argue with, and retry against. A block happened before authorization, so there is no issuer response, no decline code, and nothing the customer's bank can tell them when they call to ask.</p>
<p>What the customer sees is a generic failure. What your logs show is a failed charge. What your fraud reporting shows, if it counts blocked charges as fraud attempts, is a healthy-looking prevention rate. The one field that says what actually happened is <code>outcome.reason</code>, and almost no integration reads it, because reading it requires knowing the object has an <code>outcome</code> at all.</p>""",
"why": """<p><strong>Custom rules outlive the pattern they were written for.</strong> Somebody blocked a country during a fraud wave in 2021, or a BIN range, or every charge over a threshold. The wave passed; the rule did not. It keeps firing against ordinary customers and there is nothing that expires it or reports on it.</p>
<p><strong>The block threshold is a business decision made once.</strong> <code>highest_risk_level</code> blocks are Radar's default, and they are usually right. But the boundary between blocking and reviewing is a choice, and an account that never configured a review queue is blocking payments it could have looked at instead.</p>
<p><strong>Adaptive Acceptance blocks look identical and are not the same thing.</strong> <code>low_probability_of_authorization</code> means Stripe predicted the issuer would decline and skipped the attempt to avoid the fee. Counting those as fraud inflates your block rate and sends you to change rules that were never involved.</p>
<p><strong>Nothing sums the cost.</strong> The individual charge is a line in a list. The total value of what a single rule blocked last month is a number nobody has ever calculated, and it is usually the number that ends the argument.</p>""",
"steps": [
 {"h": "Pull the last 30 days of charges and filter on outcome.type",
  "body": """<p>Only <code>blocked</code> matters here. <code>issuer_declined</code> is a different investigation and mixing the two makes both harder, because one has a decline code to work with and the other never will.</p>"""},
 {"h": "Group by outcome.reason and sum the amounts",
  "body": """<p>Counts tell you what is firing; summed <code>amount</code> tells you what it costs. A rule that blocks a hundred small charges and a rule that blocks four large ones are different problems and the count alone hides that.</p>"""},
 {"h": "Read outcome.seller_message on a sample",
  "body": """<p>This is Stripe's own human-readable sentence about why the charge was stopped, written for you rather than for the customer. It is the fastest way to tell a rule you wrote from a threshold Stripe applied.</p>"""},
 {"h": "Separate Adaptive Acceptance out of the total",
  "body": """<p><code>low_probability_of_authorization</code> is working as intended: the charge was very likely to be declined and Stripe saved you the network fee. Leave it alone, and take it out of the fraud numbers, or every review of those numbers starts with the same wrong assumption.</p>"""},
 {"h": "Narrow the rule rather than deleting it",
  "body": """<p>In the Dashboard, Radar then Rules, find the rule that <code>outcome.reason</code> pointed at. Scoping it to an amount band or a specific BIN usually keeps whatever protection it still provides while returning the traffic it should never have touched. For <code>highest_risk_level</code>, add a review threshold before you move the block threshold.</p>"""},
],
"verify": """<p>Re-run the script over a window that starts after the rule change. The reason you narrowed should either disappear or drop to a share you can justify.</p>
<pre><code class="language-bash">python3 stripe_radar_blocks.py --days 7
# 1,204 charge(s): 9 blocked (0.7%) - rule 0, risk 6, adaptive 3</code></pre>""",
"code_intro": "One paginated GET against Charges, no writes &mdash; a restricted key with read access to Charges is enough. The classifier is pure and takes a single charge, because the only judgement in the whole script is which of the four kinds of block a charge represents, and that judgement is worth reading on its own.",
"py_file": "stripe_radar_blocks.py",
"py": '''"""Report Stripe charges that Radar blocked before authorization.

Read only. One paginated GET, no writes: give this a RESTRICTED key with read
access to Charges. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_radar_blocks")

API = "https://api.stripe.com/v1"


def classify(charge):
    """Classify one charge. Pure, so the rules can be tested without a network.

    Returns (state, detail). A blocked charge never reached the issuer, so it has
    no decline code; `outcome.reason` is the only account of what happened.
    """
    outcome = charge.get("outcome") or {}
    if outcome.get("type") != "blocked":
        return ("not-blocked", "outcome.type %r" % (outcome.get("type"),))
    reason = outcome.get("reason") or "unknown"
    seller = outcome.get("seller_message") or "no seller_message"
    if reason == "rule":
        return ("rule",
                "a Radar rule you wrote stopped this before authorization: %s" % seller)
    if reason in ("highest_risk_level", "elevated_risk_level"):
        return ("risk",
                "Radar's own %s threshold, not a rule of yours: %s" % (reason, seller))
    if reason == "low_probability_of_authorization":
        return ("adaptive",
                "Adaptive Acceptance skipped an attempt it expected to fail. "
                "Not fraud; exclude it from fraud metrics.")
    return ("blocked-other", "blocked for %r: %s" % (reason, seller))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def charges(session, since, cap):
    """Yield charges created since `since`, newest first, up to `cap`."""
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/charges", **params)
        data = page.get("data", [])
        for ch in data:
            yield ch
            seen += 1
            if seen >= cap:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to scan (default 30)")
    ap.add_argument("--max-charges", type=int, default=5000,
                    help="stop paginating after this many charges")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    since = int(time.time()) - args.days * 86400
    counts = {}
    by_reason = {}
    examples = []
    scanned = 0

    for ch in charges(s, since, args.max_charges):
        scanned += 1
        state, detail = classify(ch)
        if state == "not-blocked":
            continue
        counts[state] = counts.get(state, 0) + 1
        reason = (ch.get("outcome") or {}).get("reason") or "unknown"
        n, amount = by_reason.get(reason, (0, 0))
        by_reason[reason] = (n + 1, amount + int(ch.get("amount") or 0))
        if len(examples) < 10:
            examples.append((ch["id"], detail))

    for cid, detail in examples:
        log.warning("%s  %s", cid, detail)

    blocked = sum(counts.values())
    share = (100.0 * blocked / scanned) if scanned else 0.0
    log.info("%d charge(s): %d blocked (%.1f%%) - rule %d, risk %d, adaptive %d",
             scanned, blocked, share, counts.get("rule", 0),
             counts.get("risk", 0), counts.get("adaptive", 0))

    for reason, (n, amount) in sorted(by_reason.items(), key=lambda kv: -kv[1][0]):
        log.warning("  %-32s %4d charge(s), %d in minor units", reason, n, amount)

    if share > 2:
        log.warning("  blocked charges are over 2%% of volume, which is high enough "
                    "to be costing real revenue")
    if counts.get("rule"):
        log.warning("  repair: Dashboard > Radar > Rules, find the rule named in "
                    "outcome.seller_message and narrow its scope or disable it")
    if counts.get("risk"):
        log.warning("  repair: add a review rule before moving the block threshold, "
                    "so risky payments queue rather than vanish")
    if counts.get("adaptive"):
        log.warning("  note: low_probability_of_authorization is Adaptive Acceptance "
                    "working; exclude it from fraud metrics rather than 'fixing' it")
    return 1 if (counts.get("rule") or counts.get("risk")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-radar-blocks.mjs",
"js": '''/**
 * Report Stripe charges that Radar blocked before authorization.
 *
 * Read only. One paginated GET, no writes: give this a RESTRICTED key with read
 * access to Charges. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one charge. Pure, so the rules can be tested without a network.
 * A blocked charge never reached the issuer, so it has no decline code;
 * outcome.reason is the only account of what happened.
 */
export function classify(charge) {
  const outcome = charge.outcome ?? {};
  if (outcome.type !== 'blocked') {
    return ['not-blocked', `outcome.type ${JSON.stringify(outcome.type)}`];
  }
  const reason = outcome.reason ?? 'unknown';
  const seller = outcome.seller_message ?? 'no seller_message';
  if (reason === 'rule') {
    return ['rule', `a Radar rule you wrote stopped this before authorization: ${seller}`];
  }
  if (reason === 'highest_risk_level' || reason === 'elevated_risk_level') {
    return ['risk', `Radar's own ${reason} threshold, not a rule of yours: ${seller}`];
  }
  if (reason === 'low_probability_of_authorization') {
    return ['adaptive',
      'Adaptive Acceptance skipped an attempt it expected to fail. ' +
      'Not fraud; exclude it from fraud metrics.'];
  }
  return ['blocked-other', `blocked for ${JSON.stringify(reason)}: ${seller}`];
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

export async function* charges(key, since, cap) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/charges', params);
    const data = page.data ?? [];
    for (const ch of data) {
      yield ch;
      seen += 1;
      if (seen >= cap) return;
    }
    if (!page.has_more || data.length === 0) return;
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

  const days = Number(process.env.DAYS ?? 30);
  const since = Math.floor(Date.now() / 1000) - days * 86400;

  const counts = new Map();
  const byReason = new Map();
  const examples = [];
  let scanned = 0;

  for await (const ch of charges(key, since, 5000)) {
    scanned += 1;
    const [state, detail] = classify(ch);
    if (state === 'not-blocked') continue;
    counts.set(state, (counts.get(state) ?? 0) + 1);
    const reason = ch.outcome?.reason ?? 'unknown';
    const [n, amount] = byReason.get(reason) ?? [0, 0];
    byReason.set(reason, [n + 1, amount + (ch.amount ?? 0)]);
    if (examples.length < 10) examples.push([ch.id, detail]);
  }

  for (const [id, detail] of examples) console.warn(`${id}  ${detail}`);

  const blocked = [...counts.values()].reduce((a, b) => a + b, 0);
  const share = scanned ? (100 * blocked) / scanned : 0;
  console.log(`${scanned} charge(s): ${blocked} blocked (${share.toFixed(1)}%) - ` +
              `rule ${counts.get('rule') ?? 0}, risk ${counts.get('risk') ?? 0}, ` +
              `adaptive ${counts.get('adaptive') ?? 0}`);

  for (const [reason, [n, amount]] of [...byReason].sort((a, b) => b[1][0] - a[1][0])) {
    console.warn(`  ${reason.padEnd(32)} ${String(n).padStart(4)} charge(s), ` +
                 `${amount} in minor units`);
  }

  if (share > 2) {
    console.warn('  blocked charges are over 2% of volume, which is high enough ' +
                 'to be costing real revenue');
  }
  if (counts.get('rule')) {
    console.warn('  repair: Dashboard > Radar > Rules, find the rule named in ' +
                 'outcome.seller_message and narrow its scope or disable it');
  }
  if (counts.get('risk')) {
    console.warn('  repair: add a review rule before moving the block threshold, ' +
                 'so risky payments queue rather than vanish');
  }
  if (counts.get('adaptive')) {
    console.warn('  note: low_probability_of_authorization is Adaptive Acceptance ' +
                 "working; exclude it from fraud metrics rather than 'fixing' it");
  }
  process.exitCode = (counts.get('rule') || counts.get('risk')) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case the tests exist for is <code>low_probability_of_authorization</code>. It sits in the same field, with the same <code>outcome.type</code>, as a rule that is eating your revenue, and it is the one block you should not touch. Anything that lumps it in with the others produces a block rate that looks alarming and points at rules that had nothing to do with it.",
"test_py_file": "test_stripe_radar_blocks.py",
"test_py": '''from stripe_radar_blocks import classify


def charge(reason, type_="blocked", seller="Stopped"):
    return {"outcome": {"type": type_, "reason": reason, "seller_message": seller,
                        "network_status": "not_sent_to_network"}}


def test_custom_rule_is_named_as_yours():
    state, detail = classify(charge("rule", seller="Blocked by your rule"))
    assert state == "rule"
    assert "rule you wrote" in detail


def test_radar_threshold_is_not_confused_with_a_custom_rule():
    state, detail = classify(charge("highest_risk_level"))
    assert state == "risk"
    assert "not a rule of yours" in detail


def test_adaptive_acceptance_is_not_fraud():
    # The whole point of the note: this one is working correctly.
    state, detail = classify(charge("low_probability_of_authorization"))
    assert state == "adaptive"
    assert "Not fraud" in detail


def test_issuer_declines_are_a_different_investigation():
    assert classify(charge(None, type_="issuer_declined"))[0] == "not-blocked"


def test_missing_outcome_is_not_counted_as_blocked():
    assert classify({})[0] == "not-blocked"
''',
"test_js_file": "stripe-radar-blocks.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-radar-blocks.mjs';

function charge(reason, type = 'blocked', seller = 'Stopped') {
  return { outcome: { type, reason, seller_message: seller,
                      network_status: 'not_sent_to_network' } };
}

test('custom rule is named as yours', () => {
  const [state, detail] = classify(charge('rule', 'blocked', 'Blocked by your rule'));
  assert.equal(state, 'rule');
  assert.match(detail, /rule you wrote/);
});

test('radar threshold is not confused with a custom rule', () => {
  const [state, detail] = classify(charge('highest_risk_level'));
  assert.equal(state, 'risk');
  assert.match(detail, /not a rule of yours/);
});

test('adaptive acceptance is not fraud', () => {
  const [state, detail] = classify(charge('low_probability_of_authorization'));
  assert.equal(state, 'adaptive');
  assert.match(detail, /Not fraud/);
});

test('issuer declines are a different investigation', () => {
  assert.equal(classify(charge(null, 'issuer_declined'))[0], 'not-blocked');
});

test('missing outcome is not counted as blocked', () => {
  assert.equal(classify({})[0], 'not-blocked');
});
''',
"faq": [
 ("What is the difference between a blocked charge and a declined one?",
  "A blocked charge was stopped by Radar before Stripe sent it to the card network, so outcome.network_status reads not_sent_to_network and there is no issuer decline code anywhere on the object. A declined charge reached the issuer and came back with a reason. Only the second one is something the customer's bank can explain."),
 ("How high is a normal block rate?",
  "It depends entirely on the business, but blocked charges above roughly 2% of volume are worth an afternoon of investigation, and a single outcome.reason accounting for the majority of them is worth one regardless of the rate. The number that settles the question is the summed amount, not the count."),
 ("Should I turn off the rule the script points at?",
  "Narrow it before you delete it. A rule that blocks a whole country during a fraud wave may still be doing something useful against a narrower slice, and scoping it to an amount band or a BIN range usually returns most of the good traffic while keeping that. Deleting outright is a decision to make deliberately, not as a first move."),
 ("What do I do about low_probability_of_authorization?",
  "Nothing. That is Adaptive Acceptance predicting the issuer would decline and skipping the attempt so you do not pay a network fee for a failure. The correct action is to stop counting those charges as fraud prevention, because they distort every block-rate number you look at afterwards."),
 ("Can a restricted key read outcome data?",
  "Yes. outcome is part of the Charge object, so read access to Charges is all this script needs. It never creates, refunds, or updates anything, and it cannot change a Radar rule even if you wanted it to, which is the point."),
],
"related": [
 ("/shopify/high-risk-orders-unactioned/", "High-risk orders nobody actions"),
 ("/woocommerce/declined-card-order-stuck-pending/", "Declined card leaves the order stuck pending"),
 ("/stripe/abandoned-requires-action-intents/", "requires_action intents pile up at the 3DS step"),
],
"citations": [CITE_DECLINES, CITE_CHARGE_OBJECT, CITE_RADAR_RULES, CITE_RADAR_REVIEWS],
},

{
"slug": "refunds-failed-or-stuck",
"title": "Refunds sit failed or requires_action and nobody notices",
"description": "A refund is not final when created. It can fail days later, and if nothing listens the money leaves your balance and reaches no one.",
"h1": "refunds sit failed or requires_action and nobody notices",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe refund failed", "refund status requires_action",
             "expired_or_canceled_card refund", "stripe refund pending",
             "charge.refund.updated"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Support issued the refund, the ticket was closed, and the money left your Stripe balance. Weeks later the same customer opens a dispute for the same transaction, because it never arrived. You now pay the amount twice and the dispute fee on top, and the only record of what went wrong was a status change on an object nobody was watching.",
"short_answer": """<p>Paginate <code>GET /v1/refunds</code> over the last 180 days and flag every refund whose <code>status</code> is <code>"failed"</code> or <code>"requires_action"</code>, grouped by <code>failure_reason</code>. Also flag anything still <code>pending</code> after ten days and read its <code>pending_reason</code>.</p>
<p>Sum <code>amount</code> across the failed ones. That total is money that was debited from your balance and reached nobody, and it is the number that gets this prioritised.</p>""",
"problem": """<p>Creating a Refund returns a <code>200</code> and an object, and most refund code stops reading there. But the object is not terminal at creation. It moves through <code>pending</code>, and it can land on <code>failed</code> or <code>requires_action</code> days later, when the original request is long out of scope and nothing is left holding a reference to it.</p>
<p>The failure is worse than a refund that never happened, because your side is confident it did. The support ticket is closed, the order shows as refunded, the ledger shows the debit. The customer, holding no money, does the only thing left and disputes the charge &mdash; which costs you the amount again plus a fee, and lands as a dispute rather than as the refund failure it actually is.</p>""",
"why": """<p><strong>The card is gone.</strong> <code>expired_or_canceled_card</code> and <code>lost_or_stolen_card</code> are the common failure reasons, and both mean the card that paid you no longer exists. Retrying the same refund will fail the same way every time, so this is not a retry problem; it needs an out-of-band payment.</p>
<p><strong>Nothing subscribes to the update.</strong> The status change is announced as <code>charge.refund.updated</code>. Integrations that only handle <code>charge.refunded</code>, or that handle no refund events at all, get the optimistic first answer and never the correction.</p>
<p><strong>Some refunds need the customer to act.</strong> <code>requires_action</code> means Stripe has instructions for the recipient, in <code>refund.next_action</code>, that somebody has to pass on. Nobody passes on a link they never knew existed.</p>
<p><strong>The ledger double-counts.</strong> A failed refund is re-credited to your balance through <code>failure_balance_transaction</code>. Reconciliation that reads only the original debit shows money leaving that came back, which makes the discrepancy look like a rounding problem rather than a customer who is owed money.</p>""",
"steps": [
 {"h": "Scan 180 days of refunds and read the status",
  "body": """<p>A long window matters here because the loss is discovered late, usually by a dispute. Refunds that failed months ago are still unresolved customer obligations even though nothing in your system says so.</p>"""},
 {"h": "Group the failures by failure_reason",
  "body": """<p><code>expired_or_canceled_card</code> and <code>lost_or_stolen_card</code> need a different payment path. <code>insufficient_funds</code> and <code>declined</code> can sometimes be retried. <code>charge_for_pending_refund_disputed</code> means the customer already escalated and the dispute is now the live thread.</p>"""},
 {"h": "Flag pending refunds older than ten days",
  "body": """<p>Most refunds settle in five to ten business days. Past that, <code>pending_reason</code> says whether it is genuinely still processing, waiting on funds in your balance, or blocked because the original charge has not settled.</p>"""},
 {"h": "Sum the amounts",
  "body": """<p>The count understates this badly. One failed refund on a large order is a bigger liability than twenty small ones, and the summed figure is what tells you whether this is a backlog to work through or a single call to make this afternoon.</p>"""},
 {"h": "Subscribe to charge.refund.updated and treat failed as a ticket",
  "body": """<p>This is the actual fix. A failed refund is an open customer obligation, not a log line, and it should create work in whatever system your support team lives in. For <code>requires_action</code>, follow <code>next_action</code> and send the customer the instructions.</p>"""},
],
"verify": """<p>Re-run the script after the webhook handler ships. Failed refunds will still appear &mdash; they are historical &mdash; but each one should now correspond to an open ticket rather than to nothing.</p>
<pre><code class="language-bash">python3 stripe_refund_health.py --days 180
# 486 refund(s): 0 failed, 0 needing action, 2 stalled pending</code></pre>""",
"code_intro": "One paginated GET against Refunds and no writes &mdash; a restricted key with read access to Refunds is enough. The classifier takes the clock as an argument so the ten-day pending rule is testable, and it keeps <code>failed</code> and <code>requires_action</code> in separate states because one of them is money you still owe and the other is a message you still owe.",
"py_file": "stripe_refund_health.py",
"py": '''"""Report Stripe refunds that failed, stalled, or are waiting on the customer.

Read only. One paginated GET, no writes: give this a RESTRICTED key with read
access to Refunds. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_refund_health")

API = "https://api.stripe.com/v1"
PENDING_SECONDS = 10 * 86400

# Reasons where retrying the same card is pointless: the card is gone.
DEAD_CARD = ("expired_or_canceled_card", "lost_or_stolen_card")


def classify(refund, now, pending_after=PENDING_SECONDS):
    """Classify one refund. Pure, so the rules can be tested without a network.

    Returns (state, detail). `failed` and `requires_action` stay apart on purpose:
    the first is money you still owe the customer, the second is an instruction
    you still owe them.
    """
    status = refund.get("status")
    if status == "failed":
        reason = refund.get("failure_reason") or "unknown"
        if reason in DEAD_CARD:
            return ("failed",
                    "%s: the card no longer exists, so a retry fails the same way. "
                    "Refund out of band." % reason)
        return ("failed",
                "%s: the money left your balance and reached nobody" % reason)
    if status == "requires_action":
        return ("needs-action",
                "the customer has to follow refund.next_action before this completes")
    if status == "pending":
        created = refund.get("created")
        if not isinstance(created, int):
            return ("unknown", "pending with no created timestamp, so it cannot be aged")
        days = int((now - created) // 86400)
        if now - created < pending_after:
            return ("pending", "%dd old, inside the normal settlement window" % days)
        return ("stalled",
                "%dd old and still pending (%s)"
                % (days, refund.get("pending_reason") or "no pending_reason"))
    if status in ("succeeded", "canceled"):
        return ("settled", "status %r" % (status,))
    return ("unknown", "unrecognised status %r" % (status,))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def refunds(session, since, cap):
    """Yield refunds created since `since`, newest first, up to `cap`."""
    seen = 0
    params = {"limit": 100, "created[gte]": since}
    while True:
        page = get(session, "/refunds", **params)
        data = page.get("data", [])
        for rf in data:
            yield rf
            seen += 1
            if seen >= cap:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=180,
                    help="how far back to scan (default 180)")
    ap.add_argument("--pending-days", type=int, default=10,
                    help="age at which a pending refund counts as stalled")
    ap.add_argument("--max-refunds", type=int, default=5000,
                    help="stop paginating after this many refunds")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    since = now - args.days * 86400
    pending_after = args.pending_days * 86400

    counts = {}
    by_reason = {}
    lost = 0
    scanned = 0

    for rf in refunds(s, since, args.max_refunds):
        scanned += 1
        state, detail = classify(rf, now, pending_after)
        counts[state] = counts.get(state, 0) + 1
        if state in ("failed", "needs-action", "stalled"):
            log.warning("%s  charge=%s  %s", rf["id"], rf.get("charge") or "?", detail)
        if state == "failed":
            lost += int(rf.get("amount") or 0)
            reason = rf.get("failure_reason") or "unknown"
            by_reason[reason] = by_reason.get(reason, 0) + 1

    failed = counts.get("failed", 0)
    needs = counts.get("needs-action", 0)
    stalled = counts.get("stalled", 0)

    log.info("%d refund(s): %d failed, %d needing action, %d stalled pending",
             scanned, failed, needs, stalled)

    for reason, n in sorted(by_reason.items(), key=lambda kv: -kv[1]):
        log.warning("  %-34s %d", reason, n)

    if failed:
        log.warning("  %d in minor units left your balance and reached nobody", lost)
        log.warning("  repair: subscribe to charge.refund.updated and open a support "
                    "ticket for every status == failed")
        log.warning("  repair: for a dead card, pay the customer out of band; "
                    "retrying the same refund fails identically")
        log.warning("  check: reconcile against failure_balance_transaction so the "
                    "re-credit is not read as a second refund")
    if needs:
        log.warning("  repair: read GET %s/refunds/{id} and send the customer the "
                    "link in next_action", API)
    if stalled:
        log.warning("  check: pending_reason says whether this is settlement, your "
                    "balance, or an unsettled original charge")
    return 1 if (failed or needs or stalled) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-refund-health.mjs",
"js": '''/**
 * Report Stripe refunds that failed, stalled, or are waiting on the customer.
 *
 * Read only. One paginated GET, no writes: give this a RESTRICTED key with read
 * access to Refunds. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const PENDING_SECONDS = 10 * 86400;

// Reasons where retrying the same card is pointless: the card is gone.
const DEAD_CARD = ['expired_or_canceled_card', 'lost_or_stolen_card'];

/**
 * Classify one refund. Pure, so the rules can be tested without a network.
 * `failed` and `requires_action` stay apart on purpose: the first is money you
 * still owe the customer, the second is an instruction you still owe them.
 */
export function classify(refund, now, pendingAfter = PENDING_SECONDS) {
  const status = refund.status;
  if (status === 'failed') {
    const reason = refund.failure_reason ?? 'unknown';
    if (DEAD_CARD.includes(reason)) {
      return ['failed',
        `${reason}: the card no longer exists, so a retry fails the same way. ` +
        'Refund out of band.'];
    }
    return ['failed', `${reason}: the money left your balance and reached nobody`];
  }
  if (status === 'requires_action') {
    return ['needs-action',
      'the customer has to follow refund.next_action before this completes'];
  }
  if (status === 'pending') {
    const created = refund.created;
    if (!Number.isInteger(created)) {
      return ['unknown', 'pending with no created timestamp, so it cannot be aged'];
    }
    const days = Math.floor((now - created) / 86400);
    if (now - created < pendingAfter) {
      return ['pending', `${days}d old, inside the normal settlement window`];
    }
    return ['stalled',
      `${days}d old and still pending (${refund.pending_reason ?? 'no pending_reason'})`];
  }
  if (status === 'succeeded' || status === 'canceled') {
    return ['settled', `status ${JSON.stringify(status)}`];
  }
  return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
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

export async function* refunds(key, since, cap) {
  let seen = 0;
  const params = { limit: 100, 'created[gte]': since };
  for (;;) {
    const page = await get(key, '/refunds', params);
    const data = page.data ?? [];
    for (const rf of data) {
      yield rf;
      seen += 1;
      if (seen >= cap) return;
    }
    if (!page.has_more || data.length === 0) return;
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

  const days = Number(process.env.DAYS ?? 180);
  const pendingAfter = Number(process.env.PENDING_DAYS ?? 10) * 86400;
  const now = Math.floor(Date.now() / 1000);
  const since = now - days * 86400;

  const counts = new Map();
  const byReason = new Map();
  let lost = 0;
  let scanned = 0;

  for await (const rf of refunds(key, since, 5000)) {
    scanned += 1;
    const [state, detail] = classify(rf, now, pendingAfter);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    if (['failed', 'needs-action', 'stalled'].includes(state)) {
      console.warn(`${rf.id}  charge=${rf.charge ?? '?'}  ${detail}`);
    }
    if (state === 'failed') {
      lost += rf.amount ?? 0;
      const reason = rf.failure_reason ?? 'unknown';
      byReason.set(reason, (byReason.get(reason) ?? 0) + 1);
    }
  }

  const failed = counts.get('failed') ?? 0;
  const needs = counts.get('needs-action') ?? 0;
  const stalled = counts.get('stalled') ?? 0;

  console.log(`${scanned} refund(s): ${failed} failed, ${needs} needing action, ` +
              `${stalled} stalled pending`);

  for (const [reason, n] of [...byReason].sort((a, b) => b[1] - a[1])) {
    console.warn(`  ${reason.padEnd(34)} ${n}`);
  }

  if (failed) {
    console.warn(`  ${lost} in minor units left your balance and reached nobody`);
    console.warn('  repair: subscribe to charge.refund.updated and open a support ' +
                 'ticket for every status == failed');
    console.warn('  repair: for a dead card, pay the customer out of band; ' +
                 'retrying the same refund fails identically');
    console.warn('  check: reconcile against failure_balance_transaction so the ' +
                 're-credit is not read as a second refund');
  }
  if (needs) {
    console.warn(`  repair: read GET ${API}/refunds/{id} and send the customer the ` +
                 'link in next_action');
  }
  if (stalled) {
    console.warn('  check: pending_reason says whether this is settlement, your ' +
                 'balance, or an unsettled original charge');
  }
  process.exitCode = (failed || needs || stalled) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests hold three lines in place. A dead card has to be reported as unretryable, because a retry loop against it is the failure mode that turns one unhappy customer into a monthly job that never converges. A pending refund inside the settlement window is normal and must not be alarmed on. And an unrecognised status has to surface as unknown rather than fall through to settled, since a status Stripe adds later would otherwise be silently treated as money delivered.",
"test_py_file": "test_stripe_refund_health.py",
"test_py": '''from stripe_refund_health import classify

NOW = 1_800_000_000
DAY = 86400


def test_dead_card_is_reported_as_unretryable():
    state, detail = classify(
        {"status": "failed", "failure_reason": "expired_or_canceled_card"}, NOW)
    assert state == "failed"
    assert "out of band" in detail


def test_other_failures_say_the_money_reached_nobody():
    state, detail = classify(
        {"status": "failed", "failure_reason": "insufficient_funds"}, NOW)
    assert state == "failed"
    assert "reached nobody" in detail


def test_requires_action_is_not_a_failure():
    state, detail = classify({"status": "requires_action"}, NOW)
    assert state == "needs-action"
    assert "next_action" in detail


def test_pending_inside_the_window_is_normal():
    assert classify({"status": "pending", "created": NOW - 3 * DAY}, NOW)[0] == "pending"


def test_long_pending_is_stalled_and_unknown_status_is_not_settled():
    stalled, detail = classify(
        {"status": "pending", "created": NOW - 30 * DAY,
         "pending_reason": "charge_pending"}, NOW)
    assert stalled == "stalled"
    assert "charge_pending" in detail
    # A status Stripe adds later must not be read as money delivered.
    assert classify({"status": "reversed"}, NOW)[0] == "unknown"
''',
"test_js_file": "stripe-refund-health.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-refund-health.mjs';

const NOW = 1800000000;
const DAY = 86400;

test('dead card is reported as unretryable', () => {
  const [state, detail] = classify(
    { status: 'failed', failure_reason: 'expired_or_canceled_card' }, NOW);
  assert.equal(state, 'failed');
  assert.match(detail, /out of band/);
});

test('other failures say the money reached nobody', () => {
  const [state, detail] = classify(
    { status: 'failed', failure_reason: 'insufficient_funds' }, NOW);
  assert.equal(state, 'failed');
  assert.match(detail, /reached nobody/);
});

test('requires_action is not a failure', () => {
  const [state, detail] = classify({ status: 'requires_action' }, NOW);
  assert.equal(state, 'needs-action');
  assert.match(detail, /next_action/);
});

test('pending inside the window is normal', () => {
  assert.equal(classify({ status: 'pending', created: NOW - 3 * DAY }, NOW)[0], 'pending');
});

test('long pending is stalled and unknown status is not settled', () => {
  const [state, detail] = classify(
    { status: 'pending', created: NOW - 30 * DAY, pending_reason: 'charge_pending' }, NOW);
  assert.equal(state, 'stalled');
  assert.match(detail, /charge_pending/);
  // A status Stripe adds later must not be read as money delivered.
  assert.equal(classify({ status: 'reversed' }, NOW)[0], 'unknown');
});
''',
"faq": [
 ("Is a refund final once the API returns success?",
  "No. Creating a refund returns an object in pending or succeeded, and a pending refund can still land on failed or requires_action days later. The only way to know the outcome is to read the refund again or to handle the charge.refund.updated event."),
 ("What does expired_or_canceled_card mean for the customer?",
  "It means the card that paid you has been closed or replaced since the charge, so there is no destination for the money. Stripe re-credits the amount to your balance and the customer is still owed it. Retrying the same refund produces the same failure, so the resolution has to be a bank transfer, a credit, or a payment to a card they still hold."),
 ("How long should a pending refund take?",
  "Usually five to ten business days depending on the card network and the issuing bank. Past ten days, read pending_reason: processing means it is genuinely in flight, insufficient_funds means your Stripe balance could not cover it, and charge_pending means the original charge has not settled yet."),
 ("Why does a failed refund lead to a dispute?",
  "Because from the customer's side nothing distinguishes a failed refund from a refund you never issued. They were told the money was coming, it did not arrive, and the only lever they have left is their bank. You then pay the amount again plus the dispute fee, for a refund you already tried to make."),
 ("Does this need more than a read-only key?",
  "No. Read access to Refunds covers every call. The script never creates or cancels a refund, which matters more here than anywhere else in this section: a bug in a script that can issue refunds is a bug that moves money out of your account."),
],
"related": [
 ("/shopify/refund-exists-but-the-money-never-moved/", "A refund exists but the money never moved"),
 ("/woocommerce/stripe-dashboard-refund-not-synced/", "Dashboard refund never syncs back to the order"),
 ("/bigcommerce/gateway-refund-not-reflected-on-the-order/", "Gateway refund not reflected on the order"),
],
"citations": [CITE_REFUND_OBJECT, CITE_REFUNDS, CITE_CHARGE_OBJECT, CITE_KEYS],
},

]
