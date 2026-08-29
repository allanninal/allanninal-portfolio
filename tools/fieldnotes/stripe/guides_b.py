#!/usr/bin/env python3
"""/stripe/ field notes, batch B — the writing.

Same constraint as guides.py: every note here is a problem a script can find
with a RESTRICTED, READ-ONLY Stripe key. None of these scripts writes. They
read, they say exactly what is wrong, and they print the repair for a human to
run against a live payments account.
"""

CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")
CITE_UNDELIVERED = ("Process undelivered events — Stripe Docs",
                    "https://docs.stripe.com/webhooks/process-undelivered-events")
CITE_EVENTS_LIST = ("List all events — Stripe API reference",
                    "https://docs.stripe.com/api/events/list")
CITE_EVENT_OBJ = ("The event object — Stripe API reference",
                  "https://docs.stripe.com/api/events/object")
CITE_EVENT_TYPES = ("Types of events — Stripe API reference",
                    "https://docs.stripe.com/api/events/types")
CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")
CITE_WEBHOOK_UPDATE = ("Update a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/update")
CITE_WEBHOOK_CREATE = ("Create a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/create")
CITE_VERSIONING = ("Webhook versioning — Stripe Docs",
                   "https://docs.stripe.com/webhooks/versioning")
CITE_CONNECT_WEBHOOKS = ("Connect webhooks — Stripe Docs",
                         "https://docs.stripe.com/connect/webhooks")
CITE_PAYOUT_OBJ = ("The payout object — Stripe API reference",
                   "https://docs.stripe.com/api/payouts/object")

GUIDES = [

{
"slug": "undelivered-events-nearing-retention",
"title": "Undelivered events are aging out of the 30-day window",
"description": "An outage found three weeks late. The fix takes minutes; the replay is the problem, because the oldest missed events are about to leave the API.",
"h1": "undelivered events are aging out of the 30-day window",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe event retention", "stripe replay missed events",
             "stripe events 30 days", "delivery_success false",
             "stripe undelivered events"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The handler is fixed. The endpoint is enabled again. Now someone has to replay three weeks of missed events, and a quiet arithmetic problem is waiting: Stripe keeps events for 30 days, the oldest ones are on day 26, and the backfill script has not been written yet.",
"short_answer": """<p>Page <code>GET /v1/events?delivery_success=false</code> and take <code>min(created)</code> across every page. Compare it to now. Past <strong>20 days</strong> you are inside the margin where a backfill still has to be scheduled rather than discussed; past <strong>29 days</strong> those events leave the API tomorrow and are not recoverable from Stripe at all.</p>
<p>Replay oldest first, not newest first. Anything already past 30 days has to be reconciled from <code>GET /v1/charges</code> and <code>GET /v1/invoices</code> instead, which carry no retention limit.</p>""",
"problem": """<p>The failure that produces this is usually already fixed by the time it matters. Somebody found the disabled endpoint, corrected the signing secret, re-enabled it, and deliveries resumed. Everyone relaxes. The missed events are still sitting in <code>/v1/events</code> marked undelivered, and nobody has looked at how old the oldest one is.</p>
<p>What makes it expensive is that the loss is silent and partial. You do not wake up to an empty backfill; you wake up to one that is missing its first four days, which is exactly the period nobody has records for, because the whole point is that those events never reached your system. The order table ends up with a hole whose edges you cannot even measure.</p>""",
"why": """<p><strong>There are four different windows and people remember the wrong one.</strong> Automatic retries stop after three days. The Dashboard's Resend button works for 15 days. The CLI can resend for 30. The API lists events for 30. Someone who remembers "Stripe retries for three days" concludes at day four that everything is already lost and does not try. Someone who remembers "30 days" assumes the Dashboard button will still be there on day 20. Neither is right, and only the API window governs a scripted replay.</p>
<p><strong>The clock runs from <code>created</code>, not from when you found out.</strong> An event created on the 1st is gone on the 31st whether the outage was noticed on the 5th or the 28th. Discovery does not buy time; it only tells you how much is left.</p>
<p><strong>The natural way to page events is the wrong way round.</strong> Stripe returns newest first, so a replay written the obvious way processes the events that are safest for a couple of hours before it reaches the ones about to expire. If it dies partway through &mdash; rate limits, a bad record, a deploy &mdash; the events it lost are the ones it could least afford to lose.</p>""",
"steps": [
 {"h": "Find the oldest undelivered event, not just the count",
  "body": """<p>The count tells you how much work the replay is. The oldest <code>created</code> timestamp tells you whether you have time to do it properly. Paginate all the way to the end: Stripe returns newest first, so the number you need is on the last page.</p>"""},
 {"h": "Turn the timestamp into days remaining",
  "body": """<p>Subtract from 30. That is the whole calculation, and it is the number to put in the ticket. "1,400 undelivered events, oldest expires in 4 days" gets scheduled; "we have some webhook backlog" does not.</p>"""},
 {"h": "Replay oldest first",
  "body": """<p>Walk the list in reverse chronological order and process from the tail. Use <code>ending_before</code> with an event id to page backwards through the window. Your handler has to be idempotent on <code>event.id</code>, since Stripe already delivers at least once and a replay makes duplicates certain rather than merely likely.</p>"""},
 {"h": "Reconcile anything past 30 days from the source objects",
  "body": """<p>Events expire; the objects they described do not. <code>GET /v1/charges?created[gte]=...</code> and <code>GET /v1/invoices?created[gte]=...</code> will still return everything from the lost period. You lose the ordering and the state transitions, but you can rebuild what exists now, which is usually what the order table actually needs.</p>"""},
 {"h": "Run the check daily",
  "body": """<p>A weekly check on a 30-day window can hand you a report that is already six days stale. Daily is one paginated GET and turns this from a deadline into a number that goes up and down.</p>"""},
],
"verify": """<p>Re-run the script after the replay. The undelivered count should be zero, and with nothing undelivered there is no oldest event to age out.</p>
<pre><code class="language-bash">python3 stripe_event_retention.py
# clear     0 undelivered event(s) in the retained window</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/events</code> and nothing else &mdash; a restricted key with read access to Events is enough, and is what you should give it. The age arithmetic is a pure function, because off-by-one-day errors in a retention check are the kind that only show up on the day they cost you something.",
"py_file": "stripe_event_retention.py",
"py": '''"""Report undelivered Stripe events approaching the 30-day retention cliff.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Events. The replay is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_event_retention")

API = "https://api.stripe.com/v1"

RETENTION_DAYS = 30   # events leave /v1/events entirely at this age
CRITICAL_DAYS = 29    # gone tomorrow
WARN_DAYS = 20        # still replayable, but schedule it now


def verdict(oldest_age_days, count):
    """Classify the backlog. Pure, so the boundaries can be tested without a network.

    `oldest_age_days` is the age of the oldest undelivered event in days, or None
    when nothing is undelivered. Returns (state, detail).
    """
    if not count:
        return ("clear", "0 undelivered event(s) in the retained window")
    if oldest_age_days is None:
        return ("unknown",
                "%d undelivered event(s) but no usable created timestamp" % count)
    left = RETENTION_DAYS - oldest_age_days
    if oldest_age_days >= CRITICAL_DAYS:
        return ("expiring",
                "%d event(s); the oldest is %.1f days old and leaves the API in "
                "under a day. Replay oldest first, now." % (count, oldest_age_days))
    if oldest_age_days >= WARN_DAYS:
        return ("aging",
                "%d event(s); the oldest expires in %.1f days. Schedule the replay "
                "rather than discussing it." % (count, left))
    return ("replayable",
            "%d event(s); the oldest expires in %.1f days. There is room to replay "
            "carefully." % (count, left))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def undelivered(session, limit):
    """Return (count, oldest_created, oldest_event_id) for undelivered events.

    Stripe returns events newest first, so the oldest one is on the last page and
    the pagination cannot be short-circuited if the age is to be trusted.
    """
    count = 0
    oldest = None
    oldest_id = None
    params = {"delivery_success": "false", "limit": 100}
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        for ev in data:
            count += 1
            created = ev.get("created")
            if created is not None and (oldest is None or created < oldest):
                oldest, oldest_id = created, ev.get("id")
        if not data or not page.get("has_more") or count >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return count, oldest, oldest_id


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=5000,
                    help="stop paginating after this many undelivered events")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    count, oldest, oldest_id = undelivered(s, args.max_events)
    age = None if oldest is None else (time.time() - oldest) / 86400.0
    state, detail = verdict(age, count)

    line = "%-11s %s" % (state, detail)
    if state == "clear":
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  replay oldest first, walking backwards from the tail:")
    log.warning("  GET %s/events?delivery_success=false&ending_before=%s",
                API, oldest_id or "<evt_id>")
    if state == "expiring":
        log.warning("  anything already past %d days: reconcile from the objects "
                    "instead, which have no retention limit:", RETENTION_DAYS)
        log.warning("  GET %s/charges?created[gte]=<unix>   "
                    "GET %s/invoices?created[gte]=<unix>", API, API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-event-retention.mjs",
"js": '''/**
 * Report undelivered Stripe events approaching the 30-day retention cliff.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Events. The replay is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

export const RETENTION_DAYS = 30; // events leave /v1/events entirely at this age
const CRITICAL_DAYS = 29;         // gone tomorrow
const WARN_DAYS = 20;             // still replayable, but schedule it now

/**
 * Classify the backlog. Pure, so the boundaries can be tested without a network.
 * `oldestAgeDays` is null when nothing is undelivered.
 */
export function verdict(oldestAgeDays, count) {
  if (!count) return ['clear', '0 undelivered event(s) in the retained window'];
  if (oldestAgeDays === null || oldestAgeDays === undefined) {
    return ['unknown', `${count} undelivered event(s) but no usable created timestamp`];
  }
  const left = RETENTION_DAYS - oldestAgeDays;
  if (oldestAgeDays >= CRITICAL_DAYS) {
    return ['expiring',
      `${count} event(s); the oldest is ${oldestAgeDays.toFixed(1)} days old and ` +
      'leaves the API in under a day. Replay oldest first, now.'];
  }
  if (oldestAgeDays >= WARN_DAYS) {
    return ['aging',
      `${count} event(s); the oldest expires in ${left.toFixed(1)} days. ` +
      'Schedule the replay rather than discussing it.'];
  }
  return ['replayable',
    `${count} event(s); the oldest expires in ${left.toFixed(1)} days. ` +
    'There is room to replay carefully.'];
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

export async function undelivered(key, limit = 5000) {
  let count = 0;
  let oldest = null;
  let oldestId = null;
  const params = { delivery_success: 'false', limit: 100 };
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    for (const ev of data) {
      count += 1;
      if (ev.created !== undefined && (oldest === null || ev.created < oldest)) {
        oldest = ev.created;
        oldestId = ev.id;
      }
    }
    if (data.length === 0 || !page.has_more || count >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { count, oldest, oldestId };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { count, oldest, oldestId } = await undelivered(key);
  const age = oldest === null ? null : (Date.now() / 1000 - oldest) / 86400;
  const [state, detail] = verdict(age, count);

  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'clear') { console.log(line); return; }

  console.warn(line);
  console.warn('  replay oldest first, walking backwards from the tail:');
  console.warn(`  GET ${API}/events?delivery_success=false&ending_before=${oldestId ?? '<evt_id>'}`);
  if (state === 'expiring') {
    console.warn(`  anything already past ${RETENTION_DAYS} days: reconcile from the ` +
                 'objects instead, which have no retention limit:');
    console.warn(`  GET ${API}/charges?created[gte]=<unix>   GET ${API}/invoices?created[gte]=<unix>`);
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
"test_intro": "The tests are almost entirely about boundaries, because that is where this check earns its keep. Day 20 and day 29 are the two numbers that decide whether a backlog gets scheduled or gets lost, and a check that reports <em>aging</em> one day late is a check that reports nothing.",
"test_py_file": "test_stripe_event_retention.py",
"test_py": '''from stripe_event_retention import verdict


def test_nothing_undelivered_is_clear():
    state, _ = verdict(None, 0)
    assert state == "clear"


def test_fresh_backlog_is_replayable():
    state, detail = verdict(3.0, 40)
    assert state == "replayable"
    assert "27.0" in detail


def test_twenty_days_is_the_warning_boundary():
    # Exactly 20 must already warn. A check that flips on day 21 has spent a
    # third of what is left before it says anything.
    assert verdict(19.9, 5)[0] == "replayable"
    assert verdict(20.0, 5)[0] == "aging"


def test_twenty_nine_days_is_the_last_call():
    assert verdict(28.9, 5)[0] == "aging"
    state, detail = verdict(29.0, 5)
    assert state == "expiring"
    assert "under a day" in detail


def test_count_without_a_timestamp_is_not_silently_clear():
    state, _ = verdict(None, 12)
    assert state == "unknown"
''',
"test_js_file": "stripe-event-retention.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-event-retention.mjs';

test('nothing undelivered is clear', () => {
  assert.equal(verdict(null, 0)[0], 'clear');
});

test('fresh backlog is replayable', () => {
  const [state, detail] = verdict(3.0, 40);
  assert.equal(state, 'replayable');
  assert.match(detail, /27\\.0/);
});

test('twenty days is the warning boundary', () => {
  assert.equal(verdict(19.9, 5)[0], 'replayable');
  assert.equal(verdict(20.0, 5)[0], 'aging');
});

test('twenty nine days is the last call', () => {
  assert.equal(verdict(28.9, 5)[0], 'aging');
  const [state, detail] = verdict(29.0, 5);
  assert.equal(state, 'expiring');
  assert.match(detail, /under a day/);
});

test('count without a timestamp is not silently clear', () => {
  assert.equal(verdict(null, 12)[0], 'unknown');
});
''',
"faq": [
 ("How long does Stripe keep events?",
  "30 days through GET /v1/events. That is the window a scripted replay works in. It is not the same as the three days of automatic retries, nor the 15 days the Dashboard's Resend button covers, and confusing the three is the usual reason a recoverable backlog is written off."),
 ("What happens to events older than 30 days?",
  "They are gone from the API. Nothing you can do with a Stripe key brings them back. The objects they described still exist, so reconcile from GET /v1/charges and GET /v1/invoices over the same period instead and rebuild the current state rather than the sequence of transitions."),
 ("Why replay oldest first when Stripe returns newest first?",
  "Because the oldest events are the ones with a deadline. If a replay is interrupted halfway, processing newest-first means the part it did not reach is the part closest to expiry. Page to the end and work backwards with ending_before."),
 ("Is delivery_success=false the same as pending_webhooks > 0?",
  "Close, not identical. pending_webhooks counts destinations that have not yet returned a 2xx, so it can be nonzero for an event that is merely mid-retry. delivery_success=false is the filter to size a backfill; pending_webhooks is the field to watch for a handler that is currently struggling."),
 ("Does this need a live secret key?",
  "No. A restricted key with read access to Events is enough, and it is what this script should be given. It cannot move money if it leaks."),
],
"related": [
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
 ("/stripe/duplicate-endpoints-same-url/", "Two endpoints share one URL, so every event is handled twice"),
 ("/woocommerce/replay-missed-stripe-webhook-events/", "Replay missed Stripe webhook events"),
],
"citations": [CITE_EVENTS_LIST, CITE_UNDELIVERED, CITE_EVENT_OBJ, CITE_WEBHOOKS],
},

{
"slug": "wildcard-enabled-events",
"title": "An endpoint subscribes to every event and floods the handler",
"description": "The webhook route receives dozens of types it has no branch for, and times out at month-end. enabled_events is a wildcard, not a list.",
"h1": "an endpoint subscribes to every event and floods the handler",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe enabled_events wildcard", "stripe webhook all events",
             "stripe webhook timeout", "stripe webhook too many events",
             "enabled_events star"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The webhook route is slow, and it is slow at the worst possible time: the end of the month, when renewals run. It handles four event types. It is being sent everything Stripe generates, and the other ninety-odd types still cost a request, a signature verification, and a database round trip before the handler decides it does not care.",
"short_answer": """<p>Read <code>GET /v1/webhook_endpoints</code> and look at <code>enabled_events</code>. A literal <code>"*"</code> subscribes the endpoint to every event type. An array longer than about forty is the same thing written out by hand, usually by somebody who ticked most of the boxes in the Dashboard.</p>
<p>Then tally what actually fires with <code>GET /v1/events</code> over the retained window and compare. The gap between what you are subscribed to and what your handler branches on is the traffic you are paying for and discarding.</p>""",
"problem": """<p>Nothing is broken here, which is why it survives so long. Every event verifies, the handler returns 200, and the endpoint stays enabled. The symptom is a latency graph with a spike at the end of each month, and the cause looks like your own code because the requests really are arriving at your route.</p>
<p>It becomes a real failure when the volume is enough to push a handler past Stripe's timeout on some requests. Those get retried, which adds load, which causes more timeouts. The events that fail are not the noisy ones you do not care about; they are whichever ones happened to be in flight, which will eventually include a payment.</p>""",
"why": """<p><strong>The wildcard is the path of least resistance when setting an endpoint up.</strong> You do not yet know which events you need, <code>"*"</code> means you never have to come back, and it works immediately. The intention to narrow it later is genuine and almost never acted on, because nothing ever complains.</p>
<p><strong>The cost is invisible until volume arrives.</strong> On a test account with four payments a day, a wildcard endpoint and a precise one are indistinguishable. The difference only appears once billing has a renewal cohort, and by then the endpoint has been configured that way for two years and nobody remembers choosing it.</p>
<p><strong>Every event still costs full price before it is discarded.</strong> The handler cannot know an event is irrelevant until it has received the body, verified the signature against the raw bytes, and parsed the JSON. A <code>switch</code> with no matching branch is the cheapest part of the whole operation; the expensive work has already happened.</p>
<p><strong>Stripe says not to do it.</strong> The docs recommend subscribing only to what you handle, precisely because listening for extra events puts undue strain on your server. The wildcard also enrols you automatically in event types that did not exist when you configured it.</p>""",
"steps": [
 {"h": "Read enabled_events on every endpoint, in both modes",
  "body": """<p>Look for the literal <code>"*"</code> first. Then look at length: an array of sixty specific types is a wildcard that somebody typed out, and it has the same problem.</p>"""},
 {"h": "Tally the types that actually fire",
  "body": """<p>Paginate <code>GET /v1/events</code> across the retained window and count distinct <code>type</code> values. This is the real traffic profile of the account, and it is usually a much shorter list than people expect &mdash; and a very differently weighted one.</p>"""},
 {"h": "Derive the subscription list from your code, not from the tally",
  "body": """<p>The events you should subscribe to are the ones your handler has a branch for. Read that <code>switch</code> or dispatch table and write the list from it. The API tally tells you the volume you are shedding; the code tells you what to keep.</p>"""},
 {"h": "Narrow the endpoint, do not delete and recreate it",
  "body": """<p><code>POST /v1/webhook_endpoints/{id}</code> with an explicit <code>enabled_events[]</code> list. Updating preserves the signing secret; deleting and recreating gives you a new one and a deploy you did not plan.</p>"""},
 {"h": "Re-run the tally afterwards",
  "body": """<p>Confirm that nothing your handler branches on has dropped out of the subscription. This is the one way narrowing can hurt you, and it is easy to check.</p>"""},
],
"verify": """<p>Re-run the script. Every endpoint should report a focused subscription with no unused types left in it.</p>
<pre><code class="language-bash">python3 stripe_wildcard_events.py
# focused   https://example.com/stripe/webhook  6 type(s), all seen firing</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Webhook Endpoints and Events is enough. The classification is pure and takes the subscription list plus the set of types actually observed, so the difference between a wildcard, a hand-typed wildcard and an honestly wide subscription is decided by visible rules rather than inside a request loop.",
"py_file": "stripe_wildcard_events.py",
"py": '''"""Report Stripe webhook endpoints subscribed to far more events than they handle.

Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints and Events. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_wildcard_events")

API = "https://api.stripe.com/v1"

# Above this an explicit list is a wildcard somebody typed out by hand.
WIDE = 40


def verdict(enabled_events, fired_types):
    """Classify one endpoint's subscription. Pure, so the rules can be tested.

    `enabled_events` is the endpoint's array; `fired_types` is the set of event
    types actually seen in the retained window. Returns (state, detail).
    """
    events = list(enabled_events or [])
    if not events:
        return ("empty", "no enabled_events at all: this endpoint receives nothing")
    if "*" in events:
        return ("wildcard",
                "subscribed to every event type. %d distinct type(s) fired in the "
                "retained window, and all of them are being delivered."
                % len(set(fired_types or [])))
    if len(events) > WIDE:
        return ("overbroad",
                "%d explicit types subscribed. That is a wildcard written out by "
                "hand and carries the same load." % len(events))
    unused = sorted(e for e in set(events) if e not in set(fired_types or []))
    if unused:
        return ("padded",
                "%d of %d subscribed type(s) never fired in the retained window: %s"
                % (len(unused), len(set(events)), ", ".join(unused[:5])))
    return ("focused", "%d type(s), all seen firing" % len(set(events)))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def fired_types(session, limit):
    """Distinct event types seen in the retained window, with counts."""
    counts = {}
    total = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        for ev in data:
            total += 1
            t = ev.get("type")
            counts[t] = counts.get(t, 0) + 1
        if not data or not page.get("has_more") or total >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=2000,
                    help="stop sampling event types after this many events")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    if not endpoints:
        log.info("no webhook endpoints configured for this key's mode")
        return 0

    counts = fired_types(s, args.max_events)
    log.info("sampled %d event(s) across %d distinct type(s)",
             sum(counts.values()), len(counts))

    bad = 0
    for ep in endpoints:
        state, detail = verdict(ep.get("enabled_events"), counts.keys())
        line = "%-10s %s  %s" % (state, ep.get("url", "?"), detail)
        if state == "focused":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("wildcard", "overbroad", "padded"):
            top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
            log.warning("  busiest types seen: %s",
                        ", ".join("%s x%d" % (t, n) for t, n in top))
            log.warning("  repair: POST %s/webhook_endpoints/%s "
                        "-d enabled_events[]=<type> ... (one per branch in your handler)",
                        API, ep["id"])

    log.info("%d endpoint(s), %d needing attention", len(endpoints), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-wildcard-events.mjs",
"js": '''/**
 * Report Stripe webhook endpoints subscribed to far more events than they handle.
 *
 * Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
 * Webhook Endpoints and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Above this an explicit list is a wildcard somebody typed out by hand.
const WIDE = 40;

/**
 * Classify one endpoint's subscription. Pure, so the rules can be tested.
 * `firedTypes` is the set of event types actually seen in the retained window.
 */
export function verdict(enabledEvents, firedTypes) {
  const events = [...(enabledEvents ?? [])];
  const fired = new Set(firedTypes ?? []);
  if (events.length === 0) {
    return ['empty', 'no enabled_events at all: this endpoint receives nothing'];
  }
  if (events.includes('*')) {
    return ['wildcard',
      `subscribed to every event type. ${fired.size} distinct type(s) fired in ` +
      'the retained window, and all of them are being delivered.'];
  }
  if (events.length > WIDE) {
    return ['overbroad',
      `${events.length} explicit types subscribed. That is a wildcard written ` +
      'out by hand and carries the same load.'];
  }
  const distinct = new Set(events);
  const unused = [...distinct].filter((e) => !fired.has(e)).sort();
  if (unused.length > 0) {
    return ['padded',
      `${unused.length} of ${distinct.size} subscribed type(s) never fired in ` +
      `the retained window: ${unused.slice(0, 5).join(', ')}`];
  }
  return ['focused', `${distinct.size} type(s), all seen firing`];
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

export async function firedTypes(key, limit = 2000) {
  const counts = new Map();
  let total = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    for (const ev of data) {
      total += 1;
      counts.set(ev.type, (counts.get(ev.type) ?? 0) + 1);
    }
    if (data.length === 0 || !page.has_more || total >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return counts;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  if (endpoints.length === 0) {
    console.log("no webhook endpoints configured for this key's mode");
    return;
  }

  const counts = await firedTypes(key);
  const sampled = [...counts.values()].reduce((a, b) => a + b, 0);
  console.log(`sampled ${sampled} event(s) across ${counts.size} distinct type(s)`);

  let bad = 0;
  for (const ep of endpoints) {
    const [state, detail] = verdict(ep.enabled_events, counts.keys());
    const line = `${state.padEnd(10)} ${ep.url ?? '?'}  ${detail}`;
    if (state === 'focused') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    console.warn(`  busiest types seen: ${top.map(([t, n]) => `${t} x${n}`).join(', ')}`);
    console.warn(`  repair: POST ${API}/webhook_endpoints/${ep.id} ` +
                 '-d enabled_events[]=<type> ... (one per branch in your handler)');
  }

  console.log(`${endpoints.length} endpoint(s), ${bad} needing attention`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that matters is the hand-typed wildcard. A list of sixty named types passes any check that only looks for <code>\"*\"</code>, and delivers exactly the same load. The other one worth pinning is an empty <code>enabled_events</code>, which is not a tidy subscription &mdash; it is an endpoint that receives nothing.",
"test_py_file": "test_stripe_wildcard_events.py",
"test_py": '''from stripe_wildcard_events import verdict

FIRED = ["payment_intent.succeeded", "charge.refunded", "invoice.paid"]


def test_literal_star_is_a_wildcard():
    state, detail = verdict(["*"], FIRED)
    assert state == "wildcard"
    assert "3" in detail


def test_a_long_explicit_list_is_a_wildcard_typed_out():
    # The case a naive check misses: no star anywhere, same load.
    state, _ = verdict(["evt.%d" % i for i in range(60)], FIRED)
    assert state == "overbroad"


def test_subscribed_types_that_never_fire_are_reported():
    state, detail = verdict(["payment_intent.succeeded", "issuing_card.created"],
                            FIRED)
    assert state == "padded"
    assert "issuing_card.created" in detail


def test_a_list_matching_real_traffic_is_focused():
    state, _ = verdict(FIRED, FIRED)
    assert state == "focused"


def test_empty_enabled_events_is_not_focused():
    state, _ = verdict([], FIRED)
    assert state == "empty"
''',
"test_js_file": "stripe-wildcard-events.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-wildcard-events.mjs';

const FIRED = ['payment_intent.succeeded', 'charge.refunded', 'invoice.paid'];

test('literal star is a wildcard', () => {
  const [state, detail] = verdict(['*'], FIRED);
  assert.equal(state, 'wildcard');
  assert.match(detail, /3 distinct/);
});

test('a long explicit list is a wildcard typed out', () => {
  const many = Array.from({ length: 60 }, (_, i) => `evt.${i}`);
  assert.equal(verdict(many, FIRED)[0], 'overbroad');
});

test('subscribed types that never fire are reported', () => {
  const [state, detail] = verdict(
    ['payment_intent.succeeded', 'issuing_card.created'], FIRED);
  assert.equal(state, 'padded');
  assert.match(detail, /issuing_card\\.created/);
});

test('a list matching real traffic is focused', () => {
  assert.equal(verdict(FIRED, FIRED)[0], 'focused');
});

test('empty enabled_events is not focused', () => {
  assert.equal(verdict([], FIRED)[0], 'empty');
});
''',
"faq": [
 ("Is enabled_events: [\"*\"] actually harmful?",
  "It is not incorrect, but Stripe recommends against it because listening for extra events puts undue strain on your server. Every delivery costs a request, a signature verification against the raw body, and a parse before your handler can decide it does not care. At renewal peaks that is the difference between a fast route and a timing-out one."),
 ("Does the wildcard include every event type there is?",
  "Every type except the ones that require explicit selection. It also enrols the endpoint in types Stripe adds later, which is occasionally what people want and more often a surprise."),
 ("How do I know which types to subscribe to instead?",
  "From your handler's dispatch, not from a traffic tally. The tally tells you what volume you are shedding; the code tells you what you must keep. Anything your handler has no branch for is load you are paying to discard."),
 ("Will narrowing enabled_events change my signing secret?",
  "No, as long as you update the endpoint rather than deleting and recreating it. POST /v1/webhook_endpoints/{id} preserves the secret. A delete-and-recreate gives you a new one and an unplanned deploy."),
 ("Why flag lists longer than forty types?",
  "Because a subscription that large is a wildcard somebody clicked their way to in the Dashboard. It carries the same load as a star and passes any check that only greps for one."),
],
"related": [
 ("/stripe/missing-payout-failed/", "payout.failed is unsubscribed so failures go unseen"),
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
 ("/bigcommerce/webhook-domain-blocklisted-low-success-ratio/", "A webhook domain blocklisted for a low success ratio"),
],
"citations": [CITE_WEBHOOKS, CITE_WEBHOOK_OBJ, CITE_WEBHOOK_UPDATE, CITE_EVENT_TYPES],
},

{
"slug": "duplicate-endpoints-same-url",
"title": "Two endpoints share one URL, so every event is handled twice",
"description": "Duplicate orders and double fulfilment emails, not reproducible locally. Two enabled endpoints point at the same URL and both signatures verify.",
"h1": "two endpoints share one URL, so every event is handled twice",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe duplicate webhook", "stripe webhook fires twice",
             "duplicate webhook endpoints", "stripe double fulfilment",
             "stripe webhook idempotency"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Two order rows for one payment. Two fulfilment emails. A customer credited twice. The handler reads correctly, it passes its tests, and it does not misbehave locally &mdash; because locally there is one endpoint, and in production there are two pointing at the same URL.",
"short_answer": """<p>Read <code>GET /v1/webhook_endpoints</code>, normalise each <code>url</code> by stripping the query string and any trailing slash, and group. Any normalised URL with more than one <code>enabled</code> endpoint at the same <code>livemode</code> is delivering every subscribed event to your handler once per endpoint.</p>
<p>Both deliveries verify, because each endpoint has its own signing secret and your handler checks against whichever one it holds &mdash; or against both. Corroborate with <code>GET /v1/events</code>: <code>pending_webhooks</code> counting up to the endpoint total rather than one.</p>""",
"problem": """<p>The distinguishing feature is that nothing looks wrong in the code. A duplicate delivery is not a bug in the handler; it is the handler working correctly, twice. Every trace shows a valid signed request with a real event, and every log line is one you would expect. Reviewers looking for a race condition or a retry loop find neither.</p>
<p>It is also not reproducible in development, where there is one endpoint, one secret and one delivery. That combination &mdash; visible in production, invisible everywhere else, no error anywhere &mdash; is what turns a five-minute configuration check into a week of instrumenting the wrong layer.</p>""",
"why": """<p><strong>Stripe's own upgrade procedure creates the second one.</strong> To move a webhook to a new API version you create a second endpoint on the same URL, usually with a query parameter to tell them apart, run both, then retire the old one. The creation step is memorable and the retirement step is a follow-up ticket. If it does not get done, both endpoints stay enabled and both keep delivering.</p>
<p><strong>The query parameter hides the duplicate from a visual scan.</strong> <code>/stripe/webhook?v=2025-09-30</code> and <code>/stripe/webhook</code> are different rows in the Dashboard and the same route in your application. Grouping only works after the URLs are normalised, which is why this check strips the query string before comparing.</p>
<p><strong>Separate secrets mean the second delivery cannot fail verification.</strong> Each endpoint signs with its own secret, so there is no signature mismatch to raise the alarm. If your handler accepts either secret, both deliveries sail through; if it only knows one, half your traffic starts 400-ing instead, which is a different and equally confusing problem.</p>
<p><strong>Idempotency is the actual fix, and duplication is only the trigger for it.</strong> Stripe guarantees at-least-once delivery. Even with exactly one endpoint you will eventually get the same event twice, so a handler that breaks on repeats was going to break regardless; the duplicate endpoint just made it happen every single time.</p>""",
"steps": [
 {"h": "Group endpoints by normalised URL and mode",
  "body": """<p>Strip the query string and any trailing slash, lowercase the host, then group by <code>(livemode, url)</code>. Keeping the mode in the key matters: a test and a live endpoint on the same URL are not duplicates of each other and should not be reported as such.</p>"""},
 {"h": "Count only the enabled ones",
  "body": """<p>A disabled sibling is residue, not a duplicate &mdash; worth mentioning, not worth paging anyone about. Two or more <code>enabled</code> endpoints on one normalised URL is the finding.</p>"""},
 {"h": "Corroborate against the events",
  "body": """<p><code>GET /v1/events?limit=20</code> and read <code>pending_webhooks</code> on a fresh event. A value matching the number of endpoints subscribed to that type, rather than one, confirms Stripe really is fanning out rather than something in your infrastructure replaying.</p>"""},
 {"h": "Pick the canonical endpoint and disable the other",
  "body": """<p>Keep whichever has the API version and <code>enabled_events</code> you actually want. <code>POST /v1/webhook_endpoints/{id}</code> with <code>disabled=true</code> on the other, or delete it once you are sure. Disabling first is reversible; deletion is not.</p>"""},
 {"h": "Make the handler idempotent anyway",
  "body": """<p>Persist processed <code>event.id</code> values and short-circuit repeats. This is the fix that survives the next duplicate endpoint, the next retry storm, and the at-least-once guarantee that was always going to send you a repeat eventually.</p>"""},
],
"verify": """<p>Re-run the script. Every normalised URL should hold exactly one enabled endpoint per mode.</p>
<pre><code class="language-bash">python3 stripe_duplicate_endpoints.py
# unique    live https://example.com/stripe/webhook  1 enabled endpoint</code></pre>""",
"code_intro": "One GET against <code>/v1/webhook_endpoints</code>, one optional GET against <code>/v1/events</code> to corroborate, and no writes. Two pure functions carry the logic: the URL normaliser, because the whole finding depends on <code>?v=2025-09-30</code> not counting as a different destination, and the group classifier that separates a live duplicate from a disabled leftover.",
"py_file": "stripe_duplicate_endpoints.py",
"py": '''"""Report Stripe webhook endpoints that share a URL and deliver every event twice.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints and Events. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_duplicate_endpoints")

API = "https://api.stripe.com/v1"


def normalise(url):
    """Reduce a webhook URL to the destination it actually is. Pure.

    Stripe's own API-version upgrade procedure tells you to create the second
    endpoint with a query parameter, so the query string is exactly what makes a
    duplicate look distinct. Strip it, strip a trailing slash, lowercase the host.
    """
    parts = urlsplit((url or "").strip())
    host = (parts.hostname or "").lower()
    if parts.port:
        host = "%s:%d" % (host, parts.port)
    path = parts.path.rstrip("/")
    return "%s://%s%s" % ((parts.scheme or "").lower(), host, path)


def verdict(group):
    """Classify one group of endpoints sharing a normalised URL and mode. Pure.

    Returns (state, detail).
    """
    if not group:
        return ("unique", "no endpoints")
    enabled = [e for e in group if e.get("status") == "enabled"]
    if len(enabled) > 1:
        return ("duplicate",
                "%d enabled endpoints on one URL: every subscribed event is "
                "delivered %d times and both signatures verify."
                % (len(enabled), len(enabled)))
    if len(group) > 1:
        return ("residue",
                "%d endpoint(s) on this URL, %d enabled. The disabled ones are "
                "leftovers, not duplicates." % (len(group), len(enabled)))
    return ("unique", "%d enabled endpoint" % len(enabled))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def group_endpoints(endpoints):
    """Group by (livemode, normalised url). Pure, given the endpoint list."""
    groups = {}
    for ep in endpoints:
        key = (bool(ep.get("livemode")), normalise(ep.get("url")))
        groups.setdefault(key, []).append(ep)
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corroborate", action="store_true",
                    help="also read recent events and report pending_webhooks")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    if not endpoints:
        log.info("no webhook endpoints configured for this key's mode")
        return 0

    bad = 0
    for (livemode, url), group in sorted(group_endpoints(endpoints).items()):
        state, detail = verdict(group)
        mode = "live" if livemode else "test"
        line = "%-10s %s %s  %s" % (state, mode, url, detail)
        if state == "unique":
            log.info(line)
            continue
        if state == "residue":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for ep in group:
            log.warning("    %s  %s  version=%s  %d event type(s)",
                        ep["id"], ep.get("status"),
                        ep.get("api_version") or "account default",
                        len(ep.get("enabled_events") or []))
        keep = group[0]["id"]
        for ep in group[1:]:
            log.warning("  repair: keep %s, then "
                        "POST %s/webhook_endpoints/%s -d disabled=true",
                        keep, API, ep["id"])
        log.warning("  then make the handler idempotent on event.id, which is "
                    "required regardless: Stripe delivers at least once.")

    if args.corroborate:
        recent = get(s, "/events", limit=20).get("data", [])
        pending = [e.get("pending_webhooks", 0) for e in recent]
        if pending:
            log.info("recent events: pending_webhooks max=%d (1 per subscribed "
                     "destination while in flight)", max(pending))

    log.info("%d endpoint(s), %d duplicated URL group(s)", len(endpoints), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-duplicate-endpoints.mjs",
"js": '''/**
 * Report Stripe webhook endpoints that share a URL and deliver every event twice.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access to
 * Webhook Endpoints and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Reduce a webhook URL to the destination it actually is. Pure.
 *
 * Stripe's own API-version upgrade procedure tells you to create the second
 * endpoint with a query parameter, so the query string is exactly what makes a
 * duplicate look distinct. Strip it, strip a trailing slash, lowercase the host.
 */
export function normalise(url) {
  let parsed;
  try {
    parsed = new URL(String(url ?? '').trim());
  } catch {
    return String(url ?? '').trim();
  }
  const path = parsed.pathname.replace(/\\/+$/, '');
  return `${parsed.protocol.replace(':', '').toLowerCase()}://${parsed.host.toLowerCase()}${path}`;
}

/**
 * Classify one group of endpoints sharing a normalised URL and mode. Pure.
 */
export function verdict(group) {
  const items = group ?? [];
  if (items.length === 0) return ['unique', 'no endpoints'];
  const enabled = items.filter((e) => e.status === 'enabled');
  if (enabled.length > 1) {
    return ['duplicate',
      `${enabled.length} enabled endpoints on one URL: every subscribed event is ` +
      `delivered ${enabled.length} times and both signatures verify.`];
  }
  if (items.length > 1) {
    return ['residue',
      `${items.length} endpoint(s) on this URL, ${enabled.length} enabled. ` +
      'The disabled ones are leftovers, not duplicates.'];
  }
  return ['unique', `${enabled.length} enabled endpoint`];
}

export function groupEndpoints(endpoints) {
  const groups = new Map();
  for (const ep of endpoints) {
    const key = `${ep.livemode ? 'live' : 'test'} ${normalise(ep.url)}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(ep);
  }
  return groups;
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

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  if (endpoints.length === 0) {
    console.log("no webhook endpoints configured for this key's mode");
    return;
  }

  let bad = 0;
  for (const [label, group] of [...groupEndpoints(endpoints).entries()].sort()) {
    const [state, detail] = verdict(group);
    const line = `${state.padEnd(10)} ${label}  ${detail}`;
    if (state !== 'duplicate') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    for (const ep of group) {
      console.warn(`    ${ep.id}  ${ep.status}  version=` +
                   `${ep.api_version ?? 'account default'}  ` +
                   `${(ep.enabled_events ?? []).length} event type(s)`);
    }
    const keep = group[0].id;
    for (const ep of group.slice(1)) {
      console.warn(`  repair: keep ${keep}, then ` +
                   `POST ${API}/webhook_endpoints/${ep.id} -d disabled=true`);
    }
    console.warn('  then make the handler idempotent on event.id, which is ' +
                 'required regardless: Stripe delivers at least once.');
  }

  console.log(`${endpoints.length} endpoint(s), ${bad} duplicated URL group(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The normaliser carries the finding, so it is tested harder than the classifier: <code>?v=2025-09-30</code> is precisely the difference Stripe's upgrade guide tells you to introduce, and a check that treats it as a different destination reports nothing. The classifier's own edge is one enabled endpoint beside a disabled one, which is untidy rather than broken.",
"test_py_file": "test_stripe_duplicate_endpoints.py",
"test_py": '''from stripe_duplicate_endpoints import normalise, verdict


def test_query_string_does_not_make_a_new_destination():
    # Stripe's version-upgrade guide tells you to add exactly this parameter.
    a = normalise("https://example.com/stripe/webhook?v=2025-09-30")
    b = normalise("https://example.com/stripe/webhook")
    assert a == b


def test_trailing_slash_and_host_case_are_ignored():
    a = normalise("https://Example.COM/stripe/webhook/")
    b = normalise("https://example.com/stripe/webhook")
    assert a == b


def test_different_paths_stay_different():
    assert normalise("https://example.com/a") != normalise("https://example.com/b")


def test_two_enabled_endpoints_on_one_url_is_the_finding():
    state, detail = verdict([{"status": "enabled"}, {"status": "enabled"}])
    assert state == "duplicate"
    assert "2 times" in detail


def test_one_enabled_beside_a_disabled_one_is_only_residue():
    state, _ = verdict([{"status": "enabled"}, {"status": "disabled"}])
    assert state == "residue"


def test_a_single_endpoint_is_unique():
    assert verdict([{"status": "enabled"}])[0] == "unique"
''',
"test_js_file": "stripe-duplicate-endpoints.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalise, verdict } from './stripe-duplicate-endpoints.mjs';

test('query string does not make a new destination', () => {
  // Stripe's version-upgrade guide tells you to add exactly this parameter.
  assert.equal(
    normalise('https://example.com/stripe/webhook?v=2025-09-30'),
    normalise('https://example.com/stripe/webhook'));
});

test('trailing slash and host case are ignored', () => {
  assert.equal(
    normalise('https://Example.COM/stripe/webhook/'),
    normalise('https://example.com/stripe/webhook'));
});

test('different paths stay different', () => {
  assert.notEqual(normalise('https://example.com/a'),
                  normalise('https://example.com/b'));
});

test('two enabled endpoints on one url is the finding', () => {
  const [state, detail] = verdict([{ status: 'enabled' }, { status: 'enabled' }]);
  assert.equal(state, 'duplicate');
  assert.match(detail, /2 times/);
});

test('one enabled beside a disabled one is only residue', () => {
  assert.equal(verdict([{ status: 'enabled' }, { status: 'disabled' }])[0], 'residue');
});

test('a single endpoint is unique', () => {
  assert.equal(verdict([{ status: 'enabled' }])[0], 'unique');
});
''',
"faq": [
 ("Why does the second delivery pass signature verification?",
  "Because each endpoint has its own signing secret and signs its own delivery. There is no mismatch to catch. If your handler is configured with both secrets, or tries each in turn, both deliveries verify perfectly and neither looks unusual."),
 ("How did a second endpoint on the same URL get created?",
  "Most often during an API-version upgrade. Stripe's documented procedure is to create a second endpoint on the same URL pinned to the new version, run both, and retire the old one. The retirement is a separate step and is frequently skipped."),
 ("Should I delete the extra endpoint or disable it?",
  "Disable first. POST /v1/webhook_endpoints/{id} with disabled=true is reversible, so if you picked the wrong one you find out without having lost the object and its configuration. Delete later, once deliveries look right."),
 ("If I fix the duplicate, do I still need idempotency?",
  "Yes. Stripe guarantees at-least-once delivery, so repeats happen with a single endpoint too, particularly around retries. Key your side effects on event.id and the duplicate endpoint becomes a performance issue rather than a data-integrity one."),
 ("Can this be detected without a live secret key?",
  "Yes. A restricted key with read access to Webhook Endpoints lists the URLs, statuses and modes, which is everything the grouping needs. Read access to Events adds the pending_webhooks corroboration."),
],
"related": [
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
 ("/stripe/undelivered-events-nearing-retention/", "Undelivered events are aging out of the 30-day window"),
 ("/woocommerce/duplicate-webhook-events/", "Duplicate webhook events run the handler twice"),
],
"citations": [CITE_VERSIONING, CITE_WEBHOOK_OBJ, CITE_EVENT_OBJ, CITE_WEBHOOKS],
},

{
"slug": "missing-payout-failed",
"title": "payout.failed is unsubscribed so failures go unseen for days",
"description": "Money stops arriving in the bank account and nothing alerts. payout.paid is subscribed, payout.failed is not, and the external account is disabled.",
"h1": "payout.failed is unsubscribed so failures go unseen for days",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe payout failed webhook", "payout.failed not received",
             "stripe payouts stopped", "stripe external account disabled",
             "connect payout failure"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Money stopped arriving in the bank account. Nothing alerted, nothing errored, and the balance in Stripe kept climbing. On a Connect platform it is worse: the sellers notice before the platform does, and they notice by not being paid.",
"short_answer": """<p>Union the <code>enabled_events</code> arrays across every endpoint from <code>GET /v1/webhook_endpoints</code> and check whether <code>payout.failed</code> is in it. Treat a <code>"*"</code> subscription as covering everything.</p>
<p>Then establish whether it matters yet: <code>GET /v1/payouts?limit=100</code> for any <code>status</code> of <code>"failed"</code>, or <code>GET /v1/events?types[]=payout.failed</code> for a non-empty result. An unsubscribed event that has already fired is not a gap in coverage &mdash; it is an incident you have not been told about.</p>""",
"problem": """<p>Payout failure is one of the few Stripe states that is genuinely invisible from the inside of your application. There is no failed request, no rejected charge, no customer complaint. Payments keep succeeding and the Stripe balance keeps growing, which reads as a good week rather than a stuck one. The signal is entirely negative: an amount that should have shown up in a bank account and did not.</p>
<p>The knock-on is what makes it urgent rather than annoying. When a payout fails, the external account it was going to is disabled, and no further payouts &mdash; automatic or manual &mdash; can be processed until it is updated. So one failure does not delay one transfer; it stops all of them, quietly, until someone goes and fixes the bank details.</p>""",
"why": """<p><strong>People subscribe to the success and not the failure.</strong> <code>payout.paid</code> is the event you reach for when you are building reconciliation, because it is the one that carries the money you want to match against. <code>payout.failed</code> arrives separately and later, and it is easy to leave off a list that was written while thinking about the happy path.</p>
<p><strong>Failure is rare enough to never have been exercised.</strong> Bank details are entered once and work for years. The subscription gap has no symptom until the day the account is closed, the sort code changes, or a bank rejects the transfer &mdash; which is precisely the day you need the alert you did not configure.</p>
<p><strong>On Connect it fails on the wrong side of the boundary.</strong> Connected accounts' payout events reach a Connect-scoped destination, not the account-scoped one, so a platform can have <code>payout.failed</code> subscribed and still see nothing for its sellers. The companion signal there is <code>account.external_account.updated</code>, which tells you a seller has repaired their details.</p>
<p><strong>The failure reason is in the event and nowhere convenient.</strong> <code>failure_code</code> distinguishes an <code>account_closed</code> that needs the seller to act from a <code>could_not_process</code> that may simply need a retry. Without the event you get neither the alert nor the reason.</p>""",
"steps": [
 {"h": "Union enabled_events across every endpoint",
  "body": """<p>Coverage is a property of the account, not of any one endpoint. It is entirely normal for the payout events to live on a different endpoint from the payment ones. Treat a <code>"*"</code> subscription as covering everything &mdash; it does, though it brings its own problems.</p>"""},
 {"h": "Check whether payouts have already failed",
  "body": """<p><code>GET /v1/payouts?limit=100</code> and look for <code>status</code> of <code>"failed"</code>. This is the difference between a gap to close this quarter and an incident that is live right now with an external account disabled behind it.</p>"""},
 {"h": "Read the failure code before assuming it is the bank",
  "body": """<p><code>failure_code</code> and <code>failure_balance_transaction</code> are on the payout object. <code>account_closed</code>, <code>invalid_account_number</code> and <code>debit_not_authorized</code> need different people to do different things, and only one of them is fixed by trying again.</p>"""},
 {"h": "Subscribe to the failure alongside the success",
  "body": """<p><code>POST /v1/webhook_endpoints/{id}</code> with <code>enabled_events[]=payout.failed</code> and <code>enabled_events[]=payout.paid</code>. Keeping them together is the point: a reconciliation process that only ever hears about successes cannot tell a quiet week from a broken one.</p>"""},
 {"h": "On Connect, add the connected-account destination too",
  "body": """<p>A Connect-scoped endpoint with <code>payout.failed</code> and <code>account.external_account.updated</code>. Without it the platform is blind to exactly the failures its sellers will call about.</p>"""},
],
"verify": """<p>Re-run the script. The union should contain <code>payout.failed</code> and the state should be covered.</p>
<pre><code class="language-bash">python3 stripe_payout_events.py
# covered   payout.failed is subscribed on at least one endpoint</code></pre>""",
"code_intro": "Three GETs and no writes &mdash; endpoints, payouts, and optionally the events themselves. A restricted key with read access to Webhook Endpoints, Payouts and Events covers it. The classifier takes the subscription union and the count of failures already seen, because those two facts together are what separate a gap in coverage from an outage in progress.",
"py_file": "stripe_payout_events.py",
"py": '''"""Report whether payout.failed is subscribed, and whether payouts already failed.

Read only. GETs only, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints, Payouts and Events. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_payout_events")

API = "https://api.stripe.com/v1"

TARGET = "payout.failed"
COMPANION = "payout.paid"


def verdict(subscribed, failed_payouts):
    """Classify payout-failure coverage. Pure, so the rules can be tested.

    `subscribed` is the union of enabled_events across every endpoint;
    `failed_payouts` is how many payouts are already in status failed.
    Returns (state, detail).
    """
    events = set(subscribed or [])
    if "*" in events:
        return ("wildcard",
                "a wildcard subscription covers %s, but it also delivers every "
                "other event type to the same handler." % TARGET)
    if TARGET in events:
        if COMPANION not in events:
            return ("partial",
                    "%s is subscribed but %s is not. Reconciliation cannot tell a "
                    "quiet week from a broken one." % (TARGET, COMPANION))
        return ("covered", "%s is subscribed on at least one endpoint" % TARGET)
    if failed_payouts:
        return ("blind",
                "%d payout(s) already failed and nothing subscribes to %s. The "
                "external account is disabled until the details are updated."
                % (failed_payouts, TARGET))
    return ("unsubscribed",
            "nothing subscribes to %s. No failures in the window yet, so this is "
            "a gap rather than an incident." % TARGET)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key lacks read access to "
                         + path)
    r.raise_for_status()
    return r.json()


def subscribed_events(endpoints):
    """Union of enabled_events across endpoints. Pure, given the endpoint list."""
    union = set()
    for ep in endpoints:
        union.update(ep.get("enabled_events") or [])
    return union


def failed_payouts(session, limit):
    """Count payouts currently in status failed, and collect their failure codes."""
    codes = {}
    count = 0
    params = {"limit": 100, "status": "failed"}
    while True:
        page = get(session, "/payouts", **params)
        data = page.get("data", [])
        for p in data:
            count += 1
            code = p.get("failure_code") or "unknown"
            codes[code] = codes.get(code, 0) + 1
        if not data or not page.get("has_more") or count >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return count, codes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-payouts", type=int, default=500,
                    help="stop counting failed payouts after this many")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    union = subscribed_events(endpoints)
    count, codes = failed_payouts(s, args.max_payouts)

    state, detail = verdict(union, count)
    line = "%-13s %s" % (state, detail)
    if state == "covered":
        log.info(line)
        return 0

    log.warning(line)
    if codes:
        log.warning("  failure codes seen: %s",
                    ", ".join("%s x%d" % (c, n) for c, n in sorted(codes.items())))
    if state in ("blind", "unsubscribed", "partial"):
        target = endpoints[0]["id"] if endpoints else "<we_id>"
        log.warning("  repair: POST %s/webhook_endpoints/%s "
                    "-d enabled_events[]=%s -d enabled_events[]=%s",
                    API, target, TARGET, COMPANION)
        log.warning("  on Connect, add a connected-accounts destination carrying "
                    "%s and account.external_account.updated", TARGET)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-payout-events.mjs",
"js": '''/**
 * Report whether payout.failed is subscribed, and whether payouts already failed.
 *
 * Read only. GETs only, no writes: give this a RESTRICTED key with read access to
 * Webhook Endpoints, Payouts and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const TARGET = 'payout.failed';
const COMPANION = 'payout.paid';

/**
 * Classify payout-failure coverage. Pure, so the rules can be tested.
 * `subscribed` is the union of enabled_events across every endpoint.
 */
export function verdict(subscribed, failedPayouts) {
  const events = new Set(subscribed ?? []);
  if (events.has('*')) {
    return ['wildcard',
      `a wildcard subscription covers ${TARGET}, but it also delivers every ` +
      'other event type to the same handler.'];
  }
  if (events.has(TARGET)) {
    if (!events.has(COMPANION)) {
      return ['partial',
        `${TARGET} is subscribed but ${COMPANION} is not. Reconciliation cannot ` +
        'tell a quiet week from a broken one.'];
    }
    return ['covered', `${TARGET} is subscribed on at least one endpoint`];
  }
  if (failedPayouts) {
    return ['blind',
      `${failedPayouts} payout(s) already failed and nothing subscribes to ` +
      `${TARGET}. The external account is disabled until the details are updated.`];
  }
  return ['unsubscribed',
    `nothing subscribes to ${TARGET}. No failures in the window yet, so this is ` +
    'a gap rather than an incident.'];
}

export function subscribedEvents(endpoints) {
  const union = new Set();
  for (const ep of endpoints ?? []) {
    for (const e of ep.enabled_events ?? []) union.add(e);
  }
  return union;
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

export async function failedPayouts(key, limit = 500) {
  const codes = new Map();
  let count = 0;
  const params = { limit: 100, status: 'failed' };
  for (;;) {
    const page = await get(key, '/payouts', params);
    const data = page.data ?? [];
    for (const p of data) {
      count += 1;
      const code = p.failure_code ?? 'unknown';
      codes.set(code, (codes.get(code) ?? 0) + 1);
    }
    if (data.length === 0 || !page.has_more || count >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return { count, codes };
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  const union = subscribedEvents(endpoints);
  const { count, codes } = await failedPayouts(key);

  const [state, detail] = verdict(union, count);
  const line = `${state.padEnd(13)} ${detail}`;
  if (state === 'covered') { console.log(line); return; }

  console.warn(line);
  if (codes.size > 0) {
    const seen = [...codes.entries()].sort().map(([c, n]) => `${c} x${n}`).join(', ');
    console.warn(`  failure codes seen: ${seen}`);
  }
  const target = endpoints.length > 0 ? endpoints[0].id : '<we_id>';
  console.warn(`  repair: POST ${API}/webhook_endpoints/${target} ` +
               `-d enabled_events[]=${TARGET} -d enabled_events[]=${COMPANION}`);
  console.warn('  on Connect, add a connected-accounts destination carrying ' +
               `${TARGET} and account.external_account.updated`);
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two distinctions are worth pinning down. A missing subscription with failures already recorded is not the same finding as a missing subscription on an account that has never had one &mdash; the first is an incident, the second is a task. And a wildcard technically covers <code>payout.failed</code>, so the check must not report it as broken while still saying what it is.",
"test_py_file": "test_stripe_payout_events.py",
"test_py": '''from stripe_payout_events import verdict

BOTH = ["payout.paid", "payout.failed", "payment_intent.succeeded"]


def test_both_payout_events_subscribed_is_covered():
    state, _ = verdict(BOTH, 0)
    assert state == "covered"


def test_missing_subscription_with_failures_is_an_incident():
    state, detail = verdict(["payout.paid"], 3)
    assert state == "blind"
    assert "3 payout(s)" in detail


def test_missing_subscription_with_no_failures_is_only_a_gap():
    # Same configuration, different urgency. Collapsing these two loses the
    # distinction between a ticket and a page.
    state, _ = verdict(["payout.paid"], 0)
    assert state == "unsubscribed"


def test_failure_without_the_success_is_flagged_as_partial():
    state, _ = verdict(["payout.failed"], 0)
    assert state == "partial"


def test_a_wildcard_covers_it_but_is_named_as_such():
    state, detail = verdict(["*"], 0)
    assert state == "wildcard"
    assert "every" in detail
''',
"test_js_file": "stripe-payout-events.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-payout-events.mjs';

const BOTH = ['payout.paid', 'payout.failed', 'payment_intent.succeeded'];

test('both payout events subscribed is covered', () => {
  assert.equal(verdict(BOTH, 0)[0], 'covered');
});

test('missing subscription with failures is an incident', () => {
  const [state, detail] = verdict(['payout.paid'], 3);
  assert.equal(state, 'blind');
  assert.match(detail, /3 payout\\(s\\)/);
});

test('missing subscription with no failures is only a gap', () => {
  // Same configuration, different urgency.
  assert.equal(verdict(['payout.paid'], 0)[0], 'unsubscribed');
});

test('failure without the success is flagged as partial', () => {
  assert.equal(verdict(['payout.failed'], 0)[0], 'partial');
});

test('a wildcard covers it but is named as such', () => {
  const [state, detail] = verdict(['*'], 0);
  assert.equal(state, 'wildcard');
  assert.match(detail, /every/);
});
''',
"faq": [
 ("What happens when a Stripe payout fails?",
  "The payout moves to status failed and the external account it was going to is disabled. No further payouts, automatic or manual, can be processed to that account until the details are updated. One failure therefore stops the whole payout schedule rather than delaying a single transfer."),
 ("Why is payout.paid usually subscribed and payout.failed not?",
  "Because payout.paid is the event people reach for when building reconciliation: it carries the money to match against. The failure event arrives separately and later, and gets left off a list written while thinking about the happy path."),
 ("I subscribe to payout.failed but see nothing for my connected accounts.",
  "Connected accounts' events only reach a Connect-scoped destination. An account-scoped endpoint never sees them whatever its enabled_events says. Add a connected-accounts destination carrying payout.failed and account.external_account.updated."),
 ("Which failure codes need action from me rather than a retry?",
  "account_closed, invalid_account_number and debit_not_authorized all need someone to change the bank details or the authorisation; retrying is pointless. Codes like could_not_process may clear on their own. Read failure_code on the payout object rather than assuming."),
 ("Can I check this with a read-only key?",
  "Yes. Read access to Webhook Endpoints gives you the subscription union and read access to Payouts confirms whether anything has already failed. Neither can move money."),
],
"related": [
 ("/stripe/wildcard-enabled-events/", "An endpoint subscribes to every event and floods the handler"),
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
 ("/woocommerce/match-payouts-to-orders/", "Match payouts to orders"),
],
"citations": [CITE_CONNECT_WEBHOOKS, CITE_PAYOUT_OBJ, CITE_WEBHOOK_CREATE, CITE_WEBHOOKS],
},

]
