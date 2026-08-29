#!/usr/bin/env python3
"""/stripe/ field notes, batch X — the writing.

Four notes about the reporting surface and the hardware at the other end of it:
a report run that fails after the 200, a report run that succeeds and quietly
returns less than it was asked for, a Sigma schedule whose only failure signal is
an email that does not arrive, and a card reader that is offline while nothing at
all appears in the API to investigate.

Same constraint as every other batch here: each problem is findable with a
RESTRICTED, READ-ONLY Stripe key. None of these scripts writes. They read, they
say exactly what is wrong, and they print the repair for a human to run against a
live payments account.
"""

CITE_REPORT_RUN_OBJ = ("The report run object — Stripe API reference",
                       "https://docs.stripe.com/api/reporting/report_run/object")
CITE_REPORT_RUN_CREATE = ("Create a report run — Stripe API reference",
                          "https://docs.stripe.com/api/reporting/report_run/create")
CITE_REPORT_TYPE_OBJ = ("The report type object — Stripe API reference",
                        "https://docs.stripe.com/api/reporting/report_type/object")
CITE_REPORTS = ("Reports — Stripe Docs", "https://docs.stripe.com/reports")
CITE_SCHEDULE_QUERIES = ("Schedule queries — Stripe Docs",
                         "https://docs.stripe.com/stripe-data/schedule-queries")
CITE_SIGMA_RUN_OBJ = ("The scheduled query run object — Stripe API reference",
                      "https://docs.stripe.com/api/sigma/scheduled_queries/object")
CITE_TERMINAL_READER_OBJ = ("The reader object — Stripe API reference",
                            "https://docs.stripe.com/api/terminal/readers/object")
CITE_TERMINAL = ("Stripe Terminal — Stripe Docs", "https://docs.stripe.com/terminal")
CITE_EVENT_TYPES = ("Types of events — Stripe API reference",
                    "https://docs.stripe.com/api/events/types")
CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")

GUIDES = [

{
"slug": "report-run-failed-silently",
"title": "A report run fails after the 200 and the CSV never lands",
"description": "Creating a report run returns 200 with status pending. The failure happens later, and nothing subscribes to reporting.report_run.failed, so no file lands.",
"h1": "a report run fails after the 200 and the CSV never lands",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe report run failed", "reporting.report_run.failed",
             "stripe report run pending", "stripe reports api no file",
             "stripe finance export missing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Finance says the nightly export has been missing for a week. Your job logs say it succeeded every night, and they are not lying: creating a report run returned 200 and the job exited zero. The run failed twenty seconds later, in Stripe, where nobody was looking.",
"short_answer": """<p>Page <code>GET /v1/reporting/report_runs?limit=100&amp;created[gte]=&lt;30 days ago&gt;</code> and sort every run three ways. <code>status == "failed"</code> carries the reason in <code>error</code>. <code>status == "pending"</code> on a run created more than an hour ago is a failure that has not admitted it yet. And a day with no run at all is the worst case, because it means the job did not even reach Stripe.</p>
<p>Then check whether anyone would have been told: <code>GET /v1/webhook_endpoints?limit=100</code> and look for <code>reporting.report_run.failed</code> in <code>enabled_events</code>. Every clean run in the window is only reassuring if that subscription exists.</p>""",
"problem": """<p>The Reports API is asynchronous and the asynchrony is easy to miss. <code>POST /v1/reporting/report_runs</code> returns immediately with <code>status: "pending"</code> and no <code>result</code>. Stripe then does the work and moves the run to <code>succeeded</code>, where <code>result</code> holds a File you can download, or to <code>failed</code>, where <code>error</code> holds a sentence explaining why. A job that treats the 200 as the outcome has already declared victory before either of those happens.</p>
<p>So the failure mode is not an alert nobody read. It is an absence: no file in the bucket, no row in the warehouse, no error anywhere in your logs. Finance notices at month-end, which is between two and thirty days after the first missed night, and by then the question "which nights are we missing?" cannot be answered from your side at all.</p>
<p>What makes it worse is that the causes are boring and recurrent. An <code>interval_end</code> computed in local time drifts an hour twice a year. A report type gets a new version with different required parameters. An interval reaches past what Stripe has finalized. Each of these produces a perfectly clear <code>error</code> string on the run object, sitting in an API nobody is polling.</p>""",
"why": """<p><strong>The 200 is a receipt, not a result.</strong> It confirms Stripe accepted the request and created a run object. Everything that can actually go wrong &mdash; parameters, intervals, availability &mdash; is evaluated afterwards. Any integration whose success check is the HTTP status of the create call is checking the one thing that was never in doubt.</p>
<p><strong>Nobody writes the polling loop, because the first run worked.</strong> The Reports API is usually integrated by hand, once, against an interval that was definitely available, and it returns a file within seconds. The loop that waits for <code>status</code> to leave <code>pending</code> feels like ceremony until the first night it does not.</p>
<p><strong>A stuck <code>pending</code> looks like patience.</strong> A run that has been pending for six hours is not working on it. But a script written to poll "until it is not pending" with no deadline will wait forever, and one written to check once will record the pending state as fine. Both need the same number: an age past which pending means failed.</p>
<p><strong>The event exists and is almost never subscribed to.</strong> <code>reporting.report_run.failed</code> and <code>reporting.report_run.succeeded</code> are real event types. Endpoints are typically created for payment and subscription events by whoever built checkout, months before anyone built a finance export, and nobody goes back to add reporting events to the list.</p>""",
"steps": [
 {"h": "Read the runs, not your own job logs",
  "body": """<p><code>GET /v1/reporting/report_runs</code> over the last 30 days is the only record that reflects what Stripe actually did. Filter with <code>created[gte]</code> so the pagination stays bounded, and read <code>status</code>, <code>error</code>, <code>succeeded_at</code> and <code>parameters</code> on each one.</p>"""},
 {"h": "Treat a long pending as a failure",
  "body": """<p>Pick a deadline and apply it. An hour is generous for the standard report types. A run still pending past that is not going to finish, and reporting it as "running" is how a broken night gets counted as a good one.</p>"""},
 {"h": "Look for the days with no run at all",
  "body": """<p>This is the failure the run list cannot show you directly, because the evidence is an absence. Build the set of UTC dates you expected a run for, subtract the dates that have a <code>succeeded</code> run, and report what is left. A missing day means your scheduler never fired or never reached Stripe, which is a different bug from a run that failed.</p>"""},
 {"h": "Read the error string; it usually names the fix",
  "body": """<p>The <code>error</code> field is a sentence, not a code, and it generally names the parameter at fault. Fix that parameter and re-issue <code>POST /v1/reporting/report_runs</code>, then poll <code>GET /v1/reporting/report_runs/{frr_id}</code> until <code>status</code> leaves <code>pending</code> before you call the job done.</p>"""},
 {"h": "Subscribe to the failure event so next time is loud",
  "body": """<p>Add <code>reporting.report_run.failed</code> and <code>reporting.report_run.succeeded</code> to an endpoint's <code>enabled_events</code>. Polling catches today's problem; the subscription is what stops the next one from taking a week to surface. Verify it landed by reading <code>enabled_events</code> back.</p>"""},
],
"verify": """<p>Re-run the script after fixing the parameters and adding the subscription. Every expected day should carry a successful run, and the failure event should be subscribed.</p>
<pre><code class="language-bash">python3 stripe_report_runs.py --days 30
# clear       30 run(s), 0 failed, 0 stalled, no missing days, failures subscribed</code></pre>""",
"code_intro": "Two paginated GETs and no writes &mdash; a restricted key with read access to Reports and Webhook Endpoints is enough, and is what you should give it. Two pure functions do the judging: one classifies a single run, because the difference between <em>pending</em> and <em>stalled</em> is a number rather than a status, and one folds the run states, the missing days and the subscription into a single verdict.",
"py_file": "stripe_report_runs.py",
"py": '''"""Report Stripe report runs that failed, stalled in pending, or never happened.

Read only. Two paginated GETs and no writes: give this a RESTRICTED key with read
access to Reports and Webhook Endpoints. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import datetime as dt
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_report_runs")

API = "https://api.stripe.com/v1"

# A run still pending past this is not being worked on. The standard report types
# resolve in seconds; an hour is already several orders of magnitude of slack.
STALL_SECONDS = 3600

FAILURE_EVENT = "reporting.report_run.failed"


def run_state(status, age_seconds, error=None):
    """Classify one report run. Pure, so the pending deadline can be tested offline.

    `age_seconds` is how long ago the run was created. Returns (state, detail).
    """
    if status == "succeeded":
        return ("succeeded", "finished, result file available")
    if status == "failed":
        return ("failed", error or "failed with no error message on the run")
    if status == "pending":
        if age_seconds is not None and age_seconds >= STALL_SECONDS:
            return ("stalled",
                    "pending for %.1f hour(s); nothing is working on it, treat it "
                    "as failed" % (age_seconds / 3600.0))
        return ("running", "pending, still inside the %d second window"
                % STALL_SECONDS)
    return ("unknown", "unrecognised status %r" % (status,))


def verdict(states, missing_days, failure_subscribed):
    """Fold run states, schedule gaps and webhook coverage into one verdict. Pure.

    `states` is the list of per-run states, `missing_days` the expected UTC dates
    with no successful run, `failure_subscribed` whether any endpoint listens for
    reporting.report_run.failed.
    """
    failed = states.count("failed")
    stalled = states.count("stalled")
    if not states:
        return ("silent",
                "no report runs at all in the window; the export never reached "
                "Stripe, so there is nothing here to have failed")
    if failed or stalled:
        return ("failing",
                "%d run(s): %d failed, %d stalled in pending, %d expected day(s) "
                "with no successful run"
                % (len(states), failed, stalled, len(missing_days)))
    if missing_days:
        return ("gaps",
                "%d run(s), none failed, but %d expected day(s) have no successful "
                "run: %s" % (len(states), len(missing_days),
                             ", ".join(missing_days[:5])))
    if not failure_subscribed:
        return ("unwatched",
                "%d run(s), all successful, but nothing subscribes to %s, so the "
                "next failure is silent" % (len(states), FAILURE_EVENT))
    return ("clear",
            "%d run(s), 0 failed, 0 stalled, no missing days, failures subscribed"
            % len(states))


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key has no read access to "
                         "this resource")
    r.raise_for_status()
    return r.json()


def page_all(session, path, params, cap=2000):
    """Collect every page, oldest last: Stripe returns these lists newest first."""
    out = []
    params = dict(params)
    while True:
        page = get(session, path, params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= cap:
            return out
        params["starting_after"] = data[-1]["id"]


def expected_days(now, days):
    """UTC dates a nightly export should have covered, excluding today."""
    today = dt.datetime.utcfromtimestamp(now).date()
    return [(today - dt.timedelta(days=n)).isoformat() for n in range(1, days + 1)]


def failure_is_subscribed(endpoints):
    for ep in endpoints:
        if ep.get("status") == "disabled":
            continue
        events = ep.get("enabled_events") or []
        if FAILURE_EVENT in events or "*" in events:
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read report runs")
    ap.add_argument("--report-type",
                    help="only consider runs of this report type, e.g. balance.summary.1")
    ap.add_argument("--no-daily", action="store_true",
                    help="do not expect one successful run per day")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    runs = page_all(s, "/reporting/report_runs",
                    {"limit": 100, "created[gte]": int(now - args.days * 86400)})
    if args.report_type:
        runs = [r for r in runs if r.get("report_type") == args.report_type]

    states = []
    succeeded_days = set()
    for r in runs:
        created = r.get("created")
        age = None if created is None else now - created
        state, detail = run_state(r.get("status"), age, r.get("error"))
        states.append(state)
        if state == "succeeded" and r.get("succeeded_at"):
            succeeded_days.add(
                dt.datetime.utcfromtimestamp(r["succeeded_at"]).date().isoformat())
        if state in ("failed", "stalled", "unknown"):
            log.warning("  %-9s %s  %s  %s", state, r.get("id"),
                        r.get("report_type"), detail)

    missing = ([] if args.no_daily
               else [d for d in expected_days(now, args.days) if d not in succeeded_days])

    endpoints = page_all(s, "/webhook_endpoints", {"limit": 100})
    subscribed = failure_is_subscribed(endpoints)

    state, detail = verdict(states, missing, subscribed)
    line = "%-11s %s" % (state, detail)
    if state == "clear":
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  read the reason off the run, then re-issue it:")
    log.warning("  GET %s/reporting/report_runs/<frr_id>   (read .error, .parameters)", API)
    log.warning("  POST %s/reporting/report_runs with the corrected interval, then "
                "poll until status leaves pending", API)
    if not subscribed:
        log.warning("  and subscribe an endpoint so the next one is loud:")
        log.warning("  POST %s/webhook_endpoints/<we_id> "
                    "enabled_events[]=%s enabled_events[]=reporting.report_run.succeeded",
                    API, FAILURE_EVENT)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-report-runs.mjs",
"js": '''/**
 * Report Stripe report runs that failed, stalled in pending, or never happened.
 *
 * Read only. Two paginated GETs and no writes: give this a RESTRICTED key with
 * read access to Reports and Webhook Endpoints. The repair is printed, never
 * performed.
 */
const API = 'https://api.stripe.com/v1';

// A run still pending past this is not being worked on.
export const STALL_SECONDS = 3600;
export const FAILURE_EVENT = 'reporting.report_run.failed';

/**
 * Classify one report run. Pure, so the pending deadline can be tested offline.
 * `ageSeconds` is how long ago the run was created.
 */
export function runState(status, ageSeconds, error = null) {
  if (status === 'succeeded') return ['succeeded', 'finished, result file available'];
  if (status === 'failed') {
    return ['failed', error || 'failed with no error message on the run'];
  }
  if (status === 'pending') {
    if (ageSeconds !== null && ageSeconds !== undefined && ageSeconds >= STALL_SECONDS) {
      return ['stalled',
        `pending for ${(ageSeconds / 3600).toFixed(1)} hour(s); nothing is working ` +
        'on it, treat it as failed'];
    }
    return ['running', `pending, still inside the ${STALL_SECONDS} second window`];
  }
  return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
}

/** Fold run states, schedule gaps and webhook coverage into one verdict. Pure. */
export function verdict(states, missingDays, failureSubscribed) {
  const failed = states.filter((s) => s === 'failed').length;
  const stalled = states.filter((s) => s === 'stalled').length;
  if (states.length === 0) {
    return ['silent',
      'no report runs at all in the window; the export never reached Stripe, so ' +
      'there is nothing here to have failed'];
  }
  if (failed || stalled) {
    return ['failing',
      `${states.length} run(s): ${failed} failed, ${stalled} stalled in pending, ` +
      `${missingDays.length} expected day(s) with no successful run`];
  }
  if (missingDays.length) {
    return ['gaps',
      `${states.length} run(s), none failed, but ${missingDays.length} expected ` +
      `day(s) have no successful run: ${missingDays.slice(0, 5).join(', ')}`];
  }
  if (!failureSubscribed) {
    return ['unwatched',
      `${states.length} run(s), all successful, but nothing subscribes to ` +
      `${FAILURE_EVENT}, so the next failure is silent`];
  }
  return ['clear',
    `${states.length} run(s), 0 failed, 0 stalled, no missing days, failures subscribed`];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error('403 from Stripe: the restricted key has no read access here');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function pageAll(key, path, params, cap = 2000) {
  const out = [];
  const p = { ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= cap) return out;
    p.starting_after = data[data.length - 1].id;
  }
}

const utcDay = (unix) => new Date(unix * 1000).toISOString().slice(0, 10);

export function expectedDays(now, days) {
  const out = [];
  for (let n = 1; n <= days; n += 1) out.push(utcDay(now - n * 86400));
  return out;
}

export function failureIsSubscribed(endpoints) {
  return endpoints.some((ep) => ep.status !== 'disabled'
    && (ep.enabled_events ?? []).some((e) => e === FAILURE_EVENT || e === '*'));
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);
  const now = Date.now() / 1000;

  const runs = await pageAll(key, '/reporting/report_runs',
    { limit: 100, 'created[gte]': Math.floor(now - days * 86400) });

  const states = [];
  const succeededDays = new Set();
  for (const r of runs) {
    const age = r.created === undefined ? null : now - r.created;
    const [state, detail] = runState(r.status, age, r.error);
    states.push(state);
    if (state === 'succeeded' && r.succeeded_at) succeededDays.add(utcDay(r.succeeded_at));
    if (['failed', 'stalled', 'unknown'].includes(state)) {
      console.warn(`  ${state.padEnd(9)} ${r.id}  ${r.report_type}  ${detail}`);
    }
  }
  const missing = expectedDays(now, days).filter((d) => !succeededDays.has(d));

  const endpoints = await pageAll(key, '/webhook_endpoints', { limit: 100 });
  const subscribed = failureIsSubscribed(endpoints);

  const [state, detail] = verdict(states, missing, subscribed);
  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'clear') { console.log(line); return; }

  console.warn(line);
  console.warn('  read the reason off the run, then re-issue it:');
  console.warn(`  GET ${API}/reporting/report_runs/<frr_id>   (read .error, .parameters)`);
  console.warn(`  POST ${API}/reporting/report_runs with the corrected interval, then ` +
               'poll until status leaves pending');
  if (!subscribed) {
    console.warn('  and subscribe an endpoint so the next one is loud:');
    console.warn(`  POST ${API}/webhook_endpoints/<we_id> enabled_events[]=${FAILURE_EVENT}` +
                 ' enabled_events[]=reporting.report_run.succeeded');
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
"test_intro": "The tests are about the two judgements a human keeps getting wrong here: that <em>pending</em> is a state rather than a stopwatch, and that a window full of successful runs can still be a broken export if a night is missing from it. Both are decided by the pure functions, so both can be checked without a Stripe key.",
"test_py_file": "test_stripe_report_runs.py",
"test_py": '''from stripe_report_runs import run_state, verdict


def test_succeeded_run_is_not_flagged():
    state, _ = run_state("succeeded", 120.0)
    assert state == "succeeded"


def test_pending_becomes_stalled_at_the_hour():
    # 59 minutes is still legitimately running; 60 is a run nothing is working on.
    assert run_state("pending", 3599.0)[0] == "running"
    state, detail = run_state("pending", 3600.0)
    assert state == "stalled"
    assert "1.0 hour" in detail


def test_failed_run_without_an_error_string_still_says_something():
    state, detail = run_state("failed", 30.0, None)
    assert state == "failed"
    assert "no error message" in detail


def test_all_successful_but_a_missing_day_is_not_clear():
    state, detail = verdict(["succeeded"] * 29, ["2026-08-14"], True)
    assert state == "gaps"
    assert "2026-08-14" in detail


def test_no_runs_at_all_is_the_loudest_case():
    assert verdict([], [], True)[0] == "silent"
    # Clean runs still are not clear while nothing listens for the failure event.
    assert verdict(["succeeded"], [], False)[0] == "unwatched"
    assert verdict(["succeeded"], [], True)[0] == "clear"
''',
"test_js_file": "stripe-report-runs.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { runState, verdict } from './stripe-report-runs.mjs';

test('succeeded run is not flagged', () => {
  assert.equal(runState('succeeded', 120)[0], 'succeeded');
});

test('pending becomes stalled at the hour', () => {
  assert.equal(runState('pending', 3599)[0], 'running');
  const [state, detail] = runState('pending', 3600);
  assert.equal(state, 'stalled');
  assert.match(detail, /1\\.0 hour/);
});

test('failed run without an error string still says something', () => {
  const [state, detail] = runState('failed', 30, null);
  assert.equal(state, 'failed');
  assert.match(detail, /no error message/);
});

test('all successful but a missing day is not clear', () => {
  const [state, detail] = verdict(Array(29).fill('succeeded'), ['2026-08-14'], true);
  assert.equal(state, 'gaps');
  assert.match(detail, /2026-08-14/);
});

test('no runs at all is the loudest case', () => {
  assert.equal(verdict([], [], true)[0], 'silent');
  assert.equal(verdict(['succeeded'], [], false)[0], 'unwatched');
  assert.equal(verdict(['succeeded'], [], true)[0], 'clear');
});
''',
"faq": [
 ("Why did creating the report run return 200 if it failed?",
  "Because the 200 only says Stripe accepted the request and created a run object with status pending. The work happens afterwards. The run then moves to succeeded, with a result File, or to failed, with a sentence in error. Neither outcome is known at the moment the create call returns."),
 ("How long should I wait before calling a pending run dead?",
  "An hour is a safe default for the standard report types, which normally resolve in seconds. Whatever number you pick, pick one: a poll loop with no deadline waits forever, and a single check with no deadline records a stuck run as healthy."),
 ("What is the difference between a failed run and a missing day?",
  "A failed run means your job reached Stripe and Stripe could not produce the report, so error tells you which parameter was wrong. A missing day means no run object exists at all, so the scheduler did not fire or never got a request out. The second one cannot be diagnosed from Stripe's side, only detected."),
 ("Which events should I subscribe to?",
  "reporting.report_run.failed at minimum, and reporting.report_run.succeeded if you want to trigger the download rather than poll for it. Check what you already have with GET /v1/webhook_endpoints and read enabled_events; reporting events are usually absent because the endpoint was created for payments."),
 ("Does this script need a live secret key?",
  "No. A restricted key with read access to Reports and Webhook Endpoints is enough, and is what it should be given. It reads two lists and prints the repair, so if it leaks nobody can move money with it."),
],
"related": [
 ("/stripe/report-interval-past-data-available-end/", "A report run past data_available_end returns short data"),
 ("/stripe/payout-reconciliation-unavailable/", "Payout reconciliation reports are unavailable"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions cannot be reconciled to orders"),
],
"citations": [CITE_REPORT_RUN_OBJ, CITE_REPORT_RUN_CREATE, CITE_REPORTS, CITE_EVENT_TYPES],
},

{
"slug": "report-interval-past-data-available-end",
"title": "Report runs past data_available_end return short data",
"description": "Asking for an interval Stripe has not finalized does not error. The run succeeds with less data than you asked for, so the nightly export short-changes itself.",
"h1": "report runs past data_available_end return short data",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe data_available_end", "stripe report run truncated",
             "stripe report totals lower than dashboard",
             "stripe reporting interval_end", "stripe report type availability"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The month-end report succeeded. The totals are lower than the Dashboard by a few thousand, and re-running the identical report the next morning produces a larger number. Nothing errored either time, which is the part that makes this take a day to find: a report that is short does not look any different from a report that is complete.",
"short_answer": """<p>Read <code>GET /v1/reporting/report_types</code> and take <code>data_available_start</code> and <code>data_available_end</code> for the type you run. Then read your runs with <code>GET /v1/reporting/report_runs</code> and compare each one's <code>parameters.interval_end</code> against that <code>data_available_end</code>. Anything past it was answered with whatever Stripe had finalized at the time, and the run still says <code>succeeded</code>.</p>
<p>Also flag the availability window itself: a <code>data_available_end</code> more than about 36 hours old is Stripe's pipeline being late, not your job being wrong, and the correct response is to defer rather than to retry.</p>""",
"problem": """<p>Every report type carries a window of data Stripe has finalized, exposed as <code>data_available_start</code> and <code>data_available_end</code> on the report type object. That window lags real time, because the underlying daily snapshot has to be built: for the Sigma-backed types it is typically ready in the early afternoon UTC for the previous UTC day.</p>
<p>A job that asks for an <code>interval_end</code> beyond that point does not get an error explaining the situation. It gets a successful run containing the part Stripe could answer. The file arrives, the pipeline loads it, the dashboard renders, and the only symptom is that a number is smaller than it should be &mdash; in a report where numbers are supposed to be smaller some months.</p>
<p>The reason it is so persistent is that it is intermittent by construction. A job that runs at 02:00 UTC asking for "up to midnight" is racing a boundary that moves. Most days it loses by a little and nobody can tell. At month-end, when someone compares against the Dashboard, it loses visibly, and the natural next step &mdash; re-run it &mdash; produces a different, larger answer that makes the whole system look untrustworthy rather than late.</p>""",
"why": """<p><strong>Truncation is a success, not an error.</strong> This is the whole problem in one sentence. Every guard rail people build for the Reports API watches <code>status</code>, and <code>status</code> is <code>succeeded</code>. There is no field on the run that says "this is short", so the only way to know is to have checked the availability window before asking, or to check it afterwards against what you asked for.</p>
<p><strong>The window moves during the job.</strong> <code>data_available_end</code> advances as Stripe finalizes more data, so a check written as "fetch the type, then create the run" is correct, and one written as "create the run, then explain the result" is guesswork. Reading availability after the fact, as this script does, can only prove a run was short &mdash; never that it was complete &mdash; because the window has since moved forward.</p>
<p><strong>Timezones make it worse in a way that survives review.</strong> Report intervals are unix timestamps and the finalization boundary is a UTC day. A job computing "yesterday" in a local timezone asks for a window that is an hour or several past the UTC boundary, and it will do that correctly for years until the availability lag changes slightly.</p>
<p><strong>Report type versions are not interchangeable.</strong> <code>balance.summary.1</code> and <code>balance.summary.2</code> accept different parameters and emit different columns. A job that resolves the type by prefix, or that was written against whichever version was current, can start failing or silently changing shape. Pin the version you depend on and read its availability, not the family's.</p>""",
"steps": [
 {"h": "Read the availability window for the exact type you use",
  "body": """<p><code>GET /v1/reporting/report_types?limit=100</code> lists every type with its <code>data_available_start</code> and <code>data_available_end</code>. Match on the full id including the version suffix. This is the number your job should be gating on, and almost certainly is not.</p>"""},
 {"h": "Compare every recent run's interval against it",
  "body": """<p>For each run, read <code>parameters.interval_start</code> and <code>parameters.interval_end</code> and compare against the matching type. An <code>interval_end</code> past <code>data_available_end</code> means the run was answered with less than it asked for. Because availability only moves forward, anything this check flags today was definitely short when it ran.</p>"""},
 {"h": "Flag the runs sitting on the edge, not just the ones past it",
  "body": """<p>A run whose <code>interval_end</code> lands within an hour of <code>data_available_end</code> is a coin flip that happened to land right. It will be flagged as truncated on some other night. Treating the edge as a warning is what turns this from a recurring mystery into a scheduling fix.</p>"""},
 {"h": "Check whether the window itself has gone stale",
  "body": """<p>If <code>data_available_end</code> is more than about 36 hours behind now, the problem is upstream and no interval you choose will help. Defer the job and say so in the alert; retrying against an availability window that has not moved just produces more short reports.</p>"""},
 {"h": "Gate the job instead of scheduling it hopefully",
  "body": """<p>The repair is a read before the write: <code>GET /v1/reporting/report_types/{type_id}</code>, and only <code>POST /v1/reporting/report_runs</code> when <code>data_available_end &gt;= interval_end</code>. Otherwise wait and try later. This turns a silently short report into a late one, which is a problem finance can actually see.</p>"""},
],
"verify": """<p>Re-run the script. Every run in the window should sit fully inside the type's availability window, with room to spare rather than on the boundary.</p>
<pre><code class="language-bash">python3 stripe_report_interval.py --days 14
# clear       14 run(s) checked, all fully inside the available window</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Reports is enough. The comparison between a requested interval and an availability window is a pure function, which matters more here than usual: the whole failure is an off-by-a-few-hours that nothing in the API will complain about, so the boundary rules are the check, and they are tested directly.",
"py_file": "stripe_report_interval.py",
"py": '''"""Report Stripe report runs whose interval reached past the finalized data window.

Read only. Two GETs and no writes: give this a RESTRICTED key with read access to
Reports. The repair is printed, never performed, because this script holds a
credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_report_interval")

API = "https://api.stripe.com/v1"

# An interval_end landing this close to data_available_end is not safely covered:
# it is the same request that gets truncated on a night the pipeline runs late.
EDGE_HOURS = 1.0

# Past this, the availability window itself is the problem, not the interval.
STALE_HOURS = 36.0


def interval_state(interval_start, interval_end, available_start, available_end):
    """Compare one requested interval against a report type's availability window.

    Pure, so the boundary rules can be tested without a network. All four values
    are unix seconds; the availability values may be None on a type that has
    never produced data. Returns (state, detail).
    """
    if available_end is None or interval_end is None:
        return ("unknown",
                "no data_available_end or no interval_end to compare; the run "
                "cannot be judged either way")
    if interval_end > available_end:
        short = (interval_end - available_end) / 3600.0
        return ("truncated",
                "interval_end is %.1f hour(s) past data_available_end; the run "
                "succeeded and returned less than it asked for" % short)
    if (interval_start is not None and available_start is not None
            and interval_start < available_start):
        early = (available_start - interval_start) / 3600.0
        return ("before_window",
                "interval_start is %.1f hour(s) before data_available_start; the "
                "earliest part of the range does not exist" % early)
    margin = (available_end - interval_end) / 3600.0
    if margin < EDGE_HOURS:
        return ("at_edge",
                "interval_end is only %.2f hour(s) inside data_available_end; this "
                "run was a coin flip and will be short on a slower night" % margin)
    return ("covered",
            "fully inside the available window, with %.1f hour(s) to spare" % margin)


def freshness_state(available_end_age_hours):
    """Judge the availability window itself, independently of any run. Pure."""
    if available_end_age_hours is None:
        return ("unknown", "the report type reports no data_available_end")
    if available_end_age_hours >= STALE_HOURS:
        return ("stale",
                "data_available_end is %.1f hour(s) behind now; Stripe has not "
                "finalized recent data, so defer rather than retry"
                % available_end_age_hours)
    return ("fresh",
            "data_available_end is %.1f hour(s) behind now, which is normal lag"
            % available_end_age_hours)


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key has no read access to "
                         "this resource")
    r.raise_for_status()
    return r.json()


def page_all(session, path, params, cap=2000):
    out = []
    params = dict(params)
    while True:
        page = get(session, path, params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= cap:
            return out
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14,
                    help="how far back to read report runs")
    ap.add_argument("--report-type",
                    help="only check runs of this exact type id, version included")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    types = {t["id"]: t for t in page_all(s, "/reporting/report_types", {"limit": 100})}
    runs = page_all(s, "/reporting/report_runs",
                    {"limit": 100, "created[gte]": int(now - args.days * 86400)})
    if args.report_type:
        runs = [r for r in runs if r.get("report_type") == args.report_type]

    bad = 0
    stale_types = set()
    for r in runs:
        rt = types.get(r.get("report_type"), {})
        params = r.get("parameters") or {}
        state, detail = interval_state(params.get("interval_start"),
                                       params.get("interval_end"),
                                       rt.get("data_available_start"),
                                       rt.get("data_available_end"))
        if state in ("truncated", "before_window", "at_edge"):
            bad += 1
            log.warning("  %-13s %s  %s  %s", state, r.get("id"),
                        r.get("report_type"), detail)
        end = rt.get("data_available_end")
        age = None if end is None else (now - end) / 3600.0
        if freshness_state(age)[0] == "stale":
            stale_types.add(r.get("report_type"))

    for t in sorted(stale_types):
        end = types.get(t, {}).get("data_available_end")
        age = None if end is None else (now - end) / 3600.0
        log.warning("  %-13s %s  %s", "stale-window", t, freshness_state(age)[1])

    if not bad and not stale_types:
        log.info("%-11s %d run(s) checked, all fully inside the available window",
                 "clear", len(runs))
        return 0

    log.warning("%-11s %d of %d run(s) reached past what Stripe had finalized",
                "short", bad, len(runs))
    log.warning("  availability only moves forward, so anything flagged here was "
                "definitely short when it ran")
    log.warning("  gate the job on the type before creating the run:")
    log.warning("  GET %s/reporting/report_types/<type_id>   "
                "(create only while data_available_end >= interval_end)", API)
    log.warning("  and pin the version you depend on, e.g. balance.summary.1 rather "
                "than whichever is current")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-report-interval.mjs",
"js": '''/**
 * Report Stripe report runs whose interval reached past the finalized data window.
 *
 * Read only. Two GETs and no writes: give this a RESTRICTED key with read access
 * to Reports. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// An interval_end this close to data_available_end is not safely covered.
export const EDGE_HOURS = 1.0;
// Past this, the availability window itself is the problem.
export const STALE_HOURS = 36.0;

/**
 * Compare one requested interval against a report type's availability window.
 * Pure, so the boundary rules can be tested without a network.
 */
export function intervalState(intervalStart, intervalEnd, availableStart, availableEnd) {
  const missing = (v) => v === null || v === undefined;
  if (missing(availableEnd) || missing(intervalEnd)) {
    return ['unknown',
      'no data_available_end or no interval_end to compare; the run cannot be ' +
      'judged either way'];
  }
  if (intervalEnd > availableEnd) {
    const short = (intervalEnd - availableEnd) / 3600;
    return ['truncated',
      `interval_end is ${short.toFixed(1)} hour(s) past data_available_end; the ` +
      'run succeeded and returned less than it asked for'];
  }
  if (!missing(intervalStart) && !missing(availableStart) && intervalStart < availableStart) {
    const early = (availableStart - intervalStart) / 3600;
    return ['before_window',
      `interval_start is ${early.toFixed(1)} hour(s) before data_available_start; ` +
      'the earliest part of the range does not exist'];
  }
  const margin = (availableEnd - intervalEnd) / 3600;
  if (margin < EDGE_HOURS) {
    return ['at_edge',
      `interval_end is only ${margin.toFixed(2)} hour(s) inside data_available_end; ` +
      'this run was a coin flip and will be short on a slower night'];
  }
  return ['covered',
    `fully inside the available window, with ${margin.toFixed(1)} hour(s) to spare`];
}

/** Judge the availability window itself, independently of any run. Pure. */
export function freshnessState(availableEndAgeHours) {
  if (availableEndAgeHours === null || availableEndAgeHours === undefined) {
    return ['unknown', 'the report type reports no data_available_end'];
  }
  if (availableEndAgeHours >= STALE_HOURS) {
    return ['stale',
      `data_available_end is ${availableEndAgeHours.toFixed(1)} hour(s) behind now; ` +
      'Stripe has not finalized recent data, so defer rather than retry'];
  }
  return ['fresh',
    `data_available_end is ${availableEndAgeHours.toFixed(1)} hour(s) behind now, ` +
    'which is normal lag'];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error('403 from Stripe: the restricted key has no read access here');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function pageAll(key, path, params, cap = 2000) {
  const out = [];
  const p = { ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= cap) return out;
    p.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 14);
  const now = Date.now() / 1000;

  const types = new Map();
  for (const t of await pageAll(key, '/reporting/report_types', { limit: 100 })) {
    types.set(t.id, t);
  }
  const runs = await pageAll(key, '/reporting/report_runs',
    { limit: 100, 'created[gte]': Math.floor(now - days * 86400) });

  let bad = 0;
  const staleTypes = new Set();
  for (const r of runs) {
    const rt = types.get(r.report_type) ?? {};
    const params = r.parameters ?? {};
    const [state, detail] = intervalState(params.interval_start, params.interval_end,
      rt.data_available_start, rt.data_available_end);
    if (['truncated', 'before_window', 'at_edge'].includes(state)) {
      bad += 1;
      console.warn(`  ${state.padEnd(13)} ${r.id}  ${r.report_type}  ${detail}`);
    }
    const end = rt.data_available_end;
    const age = end === undefined || end === null ? null : (now - end) / 3600;
    if (freshnessState(age)[0] === 'stale') staleTypes.add(r.report_type);
  }

  for (const t of [...staleTypes].sort()) {
    const end = (types.get(t) ?? {}).data_available_end;
    const age = end === undefined || end === null ? null : (now - end) / 3600;
    console.warn(`  stale-window  ${t}  ${freshnessState(age)[1]}`);
  }

  if (!bad && staleTypes.size === 0) {
    console.log(`clear       ${runs.length} run(s) checked, all fully inside the ` +
                'available window');
    return;
  }

  console.warn(`short       ${bad} of ${runs.length} run(s) reached past what Stripe ` +
               'had finalized');
  console.warn('  availability only moves forward, so anything flagged here was ' +
               'definitely short when it ran');
  console.warn('  gate the job on the type before creating the run:');
  console.warn(`  GET ${API}/reporting/report_types/<type_id>   ` +
               '(create only while data_available_end >= interval_end)');
  console.warn('  and pin the version you depend on, e.g. balance.summary.1 rather ' +
               'than whichever is current');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail the suite on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Everything here is a boundary, because the failure is a boundary: one hour on the wrong side of <code>data_available_end</code> and a successful report is short. The tests pin the exact comparison, including the case that gets written wrong most often &mdash; an interval landing exactly on the edge, which is covered but is not safe.",
"test_py_file": "test_stripe_report_interval.py",
"test_py": '''from stripe_report_interval import freshness_state, interval_state

DAY = 86400
# A fixed availability window: data finalized up to this timestamp.
AVAIL_END = 1_756_000_000
AVAIL_START = AVAIL_END - 90 * DAY


def test_interval_inside_the_window_is_covered():
    state, detail = interval_state(AVAIL_END - 2 * DAY, AVAIL_END - DAY,
                                   AVAIL_START, AVAIL_END)
    assert state == "covered"
    assert "24.0 hour" in detail


def test_one_hour_past_availability_is_truncated_not_an_error():
    state, detail = interval_state(AVAIL_END - DAY, AVAIL_END + 3600,
                                   AVAIL_START, AVAIL_END)
    assert state == "truncated"
    assert "1.0 hour(s) past" in detail
    assert "succeeded" in detail


def test_landing_exactly_on_the_edge_is_a_warning_not_a_pass():
    # interval_end == data_available_end is not truncated, but it is the request
    # that gets truncated the night Stripe finalizes an hour later than usual.
    assert interval_state(AVAIL_START, AVAIL_END, AVAIL_START, AVAIL_END)[0] == "at_edge"
    assert interval_state(AVAIL_START, AVAIL_END - 1800,
                          AVAIL_START, AVAIL_END)[0] == "at_edge"
    # A full hour of margin is the boundary, and the boundary counts as covered.
    assert interval_state(AVAIL_START, AVAIL_END - 3600,
                          AVAIL_START, AVAIL_END)[0] == "covered"


def test_start_before_the_window_is_reported_separately():
    state, _ = interval_state(AVAIL_START - DAY, AVAIL_END - DAY,
                              AVAIL_START, AVAIL_END)
    assert state == "before_window"


def test_a_stale_window_is_stripes_problem_not_the_intervals():
    assert freshness_state(12.0)[0] == "fresh"
    assert freshness_state(35.9)[0] == "fresh"
    state, detail = freshness_state(36.0)
    assert state == "stale"
    assert "defer rather than retry" in detail
    assert freshness_state(None)[0] == "unknown"
''',
"test_js_file": "stripe-report-interval.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { freshnessState, intervalState } from './stripe-report-interval.mjs';

const DAY = 86400;
const AVAIL_END = 1756000000;
const AVAIL_START = AVAIL_END - 90 * DAY;

test('interval inside the window is covered', () => {
  const [state, detail] = intervalState(AVAIL_END - 2 * DAY, AVAIL_END - DAY,
    AVAIL_START, AVAIL_END);
  assert.equal(state, 'covered');
  assert.match(detail, /24\\.0 hour/);
});

test('one hour past availability is truncated, not an error', () => {
  const [state, detail] = intervalState(AVAIL_END - DAY, AVAIL_END + 3600,
    AVAIL_START, AVAIL_END);
  assert.equal(state, 'truncated');
  assert.match(detail, /1\\.0 hour\\(s\\) past/);
  assert.match(detail, /succeeded/);
});

test('landing exactly on the edge is a warning, not a pass', () => {
  assert.equal(intervalState(AVAIL_START, AVAIL_END, AVAIL_START, AVAIL_END)[0],
    'at_edge');
  assert.equal(intervalState(AVAIL_START, AVAIL_END - 1800, AVAIL_START, AVAIL_END)[0],
    'at_edge');
  // A full hour of margin is the boundary, and the boundary counts as covered.
  assert.equal(intervalState(AVAIL_START, AVAIL_END - 3600, AVAIL_START, AVAIL_END)[0],
    'covered');
});

test('start before the window is reported separately', () => {
  assert.equal(intervalState(AVAIL_START - DAY, AVAIL_END - DAY,
    AVAIL_START, AVAIL_END)[0], 'before_window');
});

test('a stale window is Stripe problem, not the interval', () => {
  assert.equal(freshnessState(12)[0], 'fresh');
  assert.equal(freshnessState(35.9)[0], 'fresh');
  const [state, detail] = freshnessState(36);
  assert.equal(state, 'stale');
  assert.match(detail, /defer rather than retry/);
  assert.equal(freshnessState(null)[0], 'unknown');
});
''',
"faq": [
 ("Why does Stripe not error when I ask for data it does not have?",
  "Because the request is legitimate: the report type has a window of finalized data and Stripe answers with the part of your interval that falls inside it. The run reaches status succeeded with a real file attached. There is no field on the run marking it as short, which is why this has to be checked against data_available_end rather than against the run."),
 ("How far behind real time is data_available_end?",
  "It lags, and the size of the lag depends on the report type and on the day. The daily snapshot behind the Sigma-backed types is typically ready in the early afternoon UTC for the previous UTC day. Do not hard-code a number: read data_available_end before creating the run and gate on it."),
 ("Can this script prove a report was complete?",
  "No, and it does not claim to. Availability only moves forward, so comparing a past run against today's window can only prove a run was short. Proving completeness requires reading data_available_end before the run, which is exactly what the repair asks you to start doing."),
 ("Why flag runs that land exactly on the boundary?",
  "Because they are the same job that gets truncated on a slower night. An interval_end within an hour of data_available_end succeeded by luck. Flagging the edge turns a report that is intermittently short into a scheduling change you make once."),
 ("Does the report type version matter?",
  "Yes. Versions such as balance.summary.1 and balance.summary.2 accept different parameters and emit different schemas, and each carries its own availability window. Pin the exact type id you depend on, and read the availability for that id rather than for the family."),
],
"related": [
 ("/stripe/report-run-failed-silently/", "A report run fails after the 200 and no CSV lands"),
 ("/stripe/sigma-scheduled-query-failing/", "Sigma scheduled query runs time out and email nothing"),
 ("/stripe/payout-reconciliation-unavailable/", "Payout reconciliation reports are unavailable"),
],
"citations": [CITE_REPORT_TYPE_OBJ, CITE_REPORT_RUN_OBJ, CITE_REPORTS,
              CITE_SCHEDULE_QUERIES],
},

{
"slug": "sigma-scheduled-query-failing",
"title": "Sigma scheduled query runs time out and email nothing",
"description": "The recurring Sigma email finance relies on stops arriving. Runs are ending in timed_out, and no email looks exactly like a quiet week.",
"h1": "sigma scheduled query runs time out and email nothing",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["sigma scheduled query timed_out", "stripe sigma query failing",
             "sigma.scheduled_query_run.created", "stripe sigma results expired",
             "result_available_until"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Finance asks where the Monday numbers went, and it turns out they have not arrived for six weeks. Nobody raised it earlier because the alert for this failure is an email that does not appear, and an email that does not appear looks exactly like a week where nothing happened.",
"short_answer": """<p>Page <code>GET /v1/sigma/scheduled_query_runs?limit=100</code> and flag every run whose <code>status</code> is not <code>completed</code>. The four terminal states are <code>completed</code>, <code>canceled</code>, <code>failed</code> and <code>timed_out</code>; the last is the one that arrives gradually, as a query that used to fit its execution budget stops fitting.</p>
<p>Then check two things the status alone will not tell you. Whether a run exists at all for each expected <code>data_load_time</code>, because a schedule that stopped producing runs looks identical to one that never failed. And whether <code>result_available_until</code> has already passed on runs whose CSV you still need, because results expire whether or not anyone downloaded them.</p>""",
"problem": """<p>A Sigma schedule delivers by email, and email is a channel with no failure signal. When the query completes, a message with a link arrives. When it times out, nothing arrives. There is no bounce, no error, no red mark anywhere the recipient looks, and the recipient is usually in finance rather than engineering, so the first few missing weeks get filed as "must have been quiet".</p>
<p>The timeout itself is a slow-motion failure. The query was written against a small table and fits comfortably. Volume grows month over month, the run time climbs, and one week it crosses the execution budget. From then on it fails every time, because nothing about the query has changed except the amount of data it now has to touch, and that only goes up.</p>
<p>Underneath that is a second, quieter loss. Even successful runs produce a file that expires at <code>result_available_until</code>. A pipeline that downloads results a few days late, or a person who comes back to an old email, finds the link dead. The run says <code>completed</code> and the data is gone, which is a confusing combination to debug from the Dashboard.</p>""",
"why": """<p><strong>The absence of an email is not an event.</strong> Everything else in a Stripe integration fails loudly enough to reach a log line. This one fails by not happening. Unless something is asserting that a run occurred, the failure has no representation anywhere in your systems.</p>
<p><strong>Timeouts arrive by growth, not by change.</strong> Nobody edited the query. That is why the investigation always starts in the wrong place: the schedule is unchanged, the SQL is unchanged, and the deploy history is clean. The variable that changed is the size of the tables the query scans, and it changes every day by a little.</p>
<p><strong>The terminal states are not all equally visible.</strong> <code>failed</code> usually carries a message in <code>error</code>. <code>timed_out</code> tells you the budget was exceeded but not which part of the query spent it. <code>canceled</code> is usually a human. Collapsing all three into "not completed" loses the distinction between "fix the SQL", "narrow the SQL", and "somebody stopped it on purpose".</p>
<p><strong>Results expire on a clock nobody watches.</strong> <code>result_available_until</code> is on every run object and is almost never read, because the workflow it was designed for &mdash; click the link in the email today &mdash; never encounters it. Any workflow that downloads on a schedule, or retries after a failure, will.</p>""",
"steps": [
 {"h": "List the runs and sort them by terminal state",
  "body": """<p><code>GET /v1/sigma/scheduled_query_runs?limit=100</code>, paginated. Read <code>status</code>, <code>error</code>, <code>data_load_time</code>, <code>title</code> and <code>result_available_until</code> on each. Report <code>timed_out</code>, <code>failed</code> and <code>canceled</code> separately, because they lead to three different repairs.</p>"""},
 {"h": "Assert that runs are still being produced",
  "body": """<p>Compare the newest run's <code>data_load_time</code> against the cadence you expect. If a weekly schedule's newest run is nineteen days old, the schedule has stopped producing runs entirely and no per-run status will ever show it. This is the check that catches the six-week silence.</p>"""},
 {"h": "Check whether the results you still need have expired",
  "body": """<p><code>result_available_until</code> in the past means the file is gone even though the run completed. If you are downloading results programmatically, this is the deadline your job is racing, and it is worth reporting separately from a failure.</p>"""},
 {"h": "Narrow the query rather than retrying it",
  "body": """<p>A timeout is a budget problem and re-running spends the same budget. In Dashboard &rarr; Data &rarr; Sigma, add a <code>created &gt;=</code> bound so the query scans a window rather than all history, drop the wide joins, and select fewer columns. Then re-save the schedule.</p>"""},
 {"h": "Stop depending on the email",
  "body": """<p>Subscribe an endpoint to <code>sigma.scheduled_query_run.created</code>, and on receipt download <code>data.object.file.url</code> through <code>GET https://files.stripe.com/v1/files/{FILE_ID}/contents</code> before <code>result_available_until</code>. A webhook that stops arriving is something your monitoring already knows how to notice; an email is not.</p>"""},
],
"verify": """<p>Re-run the script after narrowing the query and adding the subscription. Every run should be <code>completed</code>, the newest one should be inside the cadence, and the run event should be subscribed.</p>
<pre><code class="language-bash">python3 stripe_sigma_runs.py --cadence-hours 168
# clear       12 run(s), all completed, newest 6.2h old, results consumed by webhook</code></pre>""",
"code_intro": "One paginated GET for the runs and one for the endpoints, both reads &mdash; a restricted key with read access to Sigma and Webhook Endpoints is enough. Two pure functions carry the judgement: one classifies a single run, including the expiry that a status of <code>completed</code> hides, and one decides whether a schedule that has produced nothing recently is quiet or dead.",
"py_file": "stripe_sigma_runs.py",
"py": '''"""Report Sigma scheduled query runs that failed, timed out, or stopped happening.

Read only. Two paginated GETs and no writes: give this a RESTRICTED key with read
access to Sigma and Webhook Endpoints. The repair is printed, never performed,
because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_sigma_runs")

API = "https://api.stripe.com/v1"

RUN_EVENT = "sigma.scheduled_query_run.created"

# A schedule that has produced nothing for twice its cadence is not quiet, it has
# stopped. One missed run can be a blip; two in a row never is.
MISSED_CADENCES = 2.0


def run_state(status, error, seconds_until_expiry):
    """Classify one scheduled query run. Pure, so it can be tested offline.

    `seconds_until_expiry` is result_available_until minus now, or None when the
    run has no result. Returns (state, detail).
    """
    if status == "completed":
        if seconds_until_expiry is not None and seconds_until_expiry <= 0:
            return ("expired",
                    "completed, but the result expired %.1f hour(s) ago; the run "
                    "succeeded and the file is gone"
                    % (-seconds_until_expiry / 3600.0))
        return ("completed", "completed with a result still available")
    if status == "timed_out":
        return ("timed_out",
                "the query ran past its execution budget; it will keep doing that "
                "until it is narrowed, because the data only grows")
    if status == "failed":
        return ("failed", error or "failed with no error message on the run")
    if status == "canceled":
        return ("canceled", "canceled, which is usually a person rather than a fault")
    return ("unknown", "unrecognised status %r" % (status,))


def verdict(states, hours_since_newest, cadence_hours, run_event_subscribed):
    """Fold run states, schedule liveness and webhook coverage into one verdict.

    Pure. `hours_since_newest` is None when there are no runs at all.
    """
    broken = states.count("timed_out") + states.count("failed")
    expired = states.count("expired")
    if not states:
        return ("silent",
                "no scheduled query runs at all; either no schedule exists or it "
                "has never produced a run")
    if broken:
        return ("failing",
                "%d of %d run(s) ended in timed_out or failed; narrow the query "
                "rather than retrying it" % (broken, len(states)))
    if (hours_since_newest is not None
            and hours_since_newest > MISSED_CADENCES * cadence_hours):
        return ("missing",
                "no run for %.1f hour(s) against a cadence of %.0f hour(s); the "
                "schedule has stopped producing runs"
                % (hours_since_newest, cadence_hours))
    if expired:
        return ("expired_results",
                "%d completed run(s) whose result has already expired; the data is "
                "gone even though nothing failed" % expired)
    if not run_event_subscribed:
        return ("email_only",
                "%d run(s), all completed, but nothing subscribes to %s, so a run "
                "that stops happening has no signal at all" % (len(states), RUN_EVENT))
    return ("clear",
            "%d run(s), all completed, results consumed by webhook" % len(states))


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key has no read access to "
                         "Sigma, or Sigma is not enabled on this account")
    r.raise_for_status()
    return r.json()


def page_all(session, path, params, cap=2000):
    out = []
    params = dict(params)
    while True:
        page = get(session, path, params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= cap:
            return out
        params["starting_after"] = data[-1]["id"]


def run_event_is_subscribed(endpoints):
    for ep in endpoints:
        if ep.get("status") == "disabled":
            continue
        events = ep.get("enabled_events") or []
        if RUN_EVENT in events or "*" in events:
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cadence-hours", type=float, default=24.0,
                    help="how often you expect a run, in hours (168 for weekly)")
    ap.add_argument("--limit", type=int, default=200,
                    help="stop after this many runs")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    runs = page_all(s, "/sigma/scheduled_query_runs", {"limit": 100}, cap=args.limit)

    states = []
    newest = None
    for r in runs:
        until = r.get("result_available_until")
        left = None if until is None else until - now
        state, detail = run_state(r.get("status"), r.get("error"), left)
        states.append(state)
        loaded = r.get("data_load_time")
        if loaded is not None and (newest is None or loaded > newest):
            newest = loaded
        if state not in ("completed",):
            log.warning("  %-9s %s  %s  %s", state, r.get("id"),
                        r.get("title") or "<untitled>", detail)

    hours_since = None if newest is None else (now - newest) / 3600.0
    endpoints = page_all(s, "/webhook_endpoints", {"limit": 100})
    subscribed = run_event_is_subscribed(endpoints)

    state, detail = verdict(states, hours_since, args.cadence_hours, subscribed)
    line = "%-11s %s" % (state, detail)
    if state == "clear":
        log.info(line)
        return 0

    log.warning(line)
    if state in ("failing", "missing", "silent"):
        log.warning("  narrow the query in Dashboard > Data > Sigma: add a created >= "
                    "bound, drop wide joins, select fewer columns, then re-save it")
    if not subscribed:
        log.warning("  consume results programmatically instead of by email:")
        log.warning("  POST %s/webhook_endpoints/<we_id> enabled_events[]=%s",
                    API, RUN_EVENT)
        log.warning("  then GET https://files.stripe.com/v1/files/<file_id>/contents "
                    "before result_available_until")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-sigma-runs.mjs",
"js": '''/**
 * Report Sigma scheduled query runs that failed, timed out, or stopped happening.
 *
 * Read only. Two paginated GETs and no writes: give this a RESTRICTED key with
 * read access to Sigma and Webhook Endpoints. The repair is printed, never
 * performed.
 */
const API = 'https://api.stripe.com/v1';

export const RUN_EVENT = 'sigma.scheduled_query_run.created';

// A schedule that has produced nothing for twice its cadence has stopped.
export const MISSED_CADENCES = 2.0;

/**
 * Classify one scheduled query run. Pure, so it can be tested offline.
 * `secondsUntilExpiry` is result_available_until minus now, or null.
 */
export function runState(status, error, secondsUntilExpiry) {
  if (status === 'completed') {
    if (secondsUntilExpiry !== null && secondsUntilExpiry !== undefined
        && secondsUntilExpiry <= 0) {
      return ['expired',
        `completed, but the result expired ${(-secondsUntilExpiry / 3600).toFixed(1)} ` +
        'hour(s) ago; the run succeeded and the file is gone'];
    }
    return ['completed', 'completed with a result still available'];
  }
  if (status === 'timed_out') {
    return ['timed_out',
      'the query ran past its execution budget; it will keep doing that until it ' +
      'is narrowed, because the data only grows'];
  }
  if (status === 'failed') {
    return ['failed', error || 'failed with no error message on the run'];
  }
  if (status === 'canceled') {
    return ['canceled', 'canceled, which is usually a person rather than a fault'];
  }
  return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
}

/** Fold run states, schedule liveness and webhook coverage into one verdict. Pure. */
export function verdict(states, hoursSinceNewest, cadenceHours, runEventSubscribed) {
  const count = (s) => states.filter((x) => x === s).length;
  const broken = count('timed_out') + count('failed');
  const expired = count('expired');
  if (states.length === 0) {
    return ['silent',
      'no scheduled query runs at all; either no schedule exists or it has never ' +
      'produced a run'];
  }
  if (broken) {
    return ['failing',
      `${broken} of ${states.length} run(s) ended in timed_out or failed; narrow ` +
      'the query rather than retrying it'];
  }
  if (hoursSinceNewest !== null && hoursSinceNewest !== undefined
      && hoursSinceNewest > MISSED_CADENCES * cadenceHours) {
    return ['missing',
      `no run for ${hoursSinceNewest.toFixed(1)} hour(s) against a cadence of ` +
      `${cadenceHours.toFixed(0)} hour(s); the schedule has stopped producing runs`];
  }
  if (expired) {
    return ['expired_results',
      `${expired} completed run(s) whose result has already expired; the data is ` +
      'gone even though nothing failed'];
  }
  if (!runEventSubscribed) {
    return ['email_only',
      `${states.length} run(s), all completed, but nothing subscribes to ${RUN_EVENT}, ` +
      'so a run that stops happening has no signal at all'];
  }
  return ['clear',
    `${states.length} run(s), all completed, results consumed by webhook`];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error('403 from Stripe: no read access to Sigma, or Sigma is not enabled');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function pageAll(key, path, params, cap = 2000) {
  const out = [];
  const p = { ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= cap) return out;
    p.starting_after = data[data.length - 1].id;
  }
}

export function runEventIsSubscribed(endpoints) {
  return endpoints.some((ep) => ep.status !== 'disabled'
    && (ep.enabled_events ?? []).some((e) => e === RUN_EVENT || e === '*'));
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }
  const cadenceHours = Number(process.env.CADENCE_HOURS ?? 24);
  const now = Date.now() / 1000;

  const runs = await pageAll(key, '/sigma/scheduled_query_runs', { limit: 100 }, 200);

  const states = [];
  let newest = null;
  for (const r of runs) {
    const until = r.result_available_until;
    const left = until === undefined || until === null ? null : until - now;
    const [state, detail] = runState(r.status, r.error, left);
    states.push(state);
    if (r.data_load_time != null && (newest === null || r.data_load_time > newest)) {
      newest = r.data_load_time;
    }
    if (state !== 'completed') {
      console.warn(`  ${state.padEnd(9)} ${r.id}  ${r.title ?? '<untitled>'}  ${detail}`);
    }
  }

  const hoursSince = newest === null ? null : (now - newest) / 3600;
  const endpoints = await pageAll(key, '/webhook_endpoints', { limit: 100 });
  const subscribed = runEventIsSubscribed(endpoints);

  const [state, detail] = verdict(states, hoursSince, cadenceHours, subscribed);
  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'clear') { console.log(line); return; }

  console.warn(line);
  if (['failing', 'missing', 'silent'].includes(state)) {
    console.warn('  narrow the query in Dashboard > Data > Sigma: add a created >= ' +
                 'bound, drop wide joins, select fewer columns, then re-save it');
  }
  if (!subscribed) {
    console.warn('  consume results programmatically instead of by email:');
    console.warn(`  POST ${API}/webhook_endpoints/<we_id> enabled_events[]=${RUN_EVENT}`);
    console.warn('  then GET https://files.stripe.com/v1/files/<file_id>/contents ' +
                 'before result_available_until');
  }
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail the suite on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things need pinning here, and neither is visible from a single run's <code>status</code>. That a <code>completed</code> run can still have lost its data, and that a list of nothing but successes is a failure when the newest one is older than the cadence. The pure functions decide both, so the tests get at them without Sigma, a schedule, or a key.",
"test_py_file": "test_stripe_sigma_runs.py",
"test_py": '''from stripe_sigma_runs import run_state, verdict


def test_completed_run_with_a_live_result_is_fine():
    state, _ = run_state("completed", None, 3 * 86400.0)
    assert state == "completed"


def test_completed_but_expired_is_its_own_state():
    # status says completed and the data is gone. Collapsing this into "completed"
    # is how a pipeline reports success while downloading nothing.
    state, detail = run_state("completed", None, -7200.0)
    assert state == "expired"
    assert "2.0 hour(s) ago" in detail


def test_timed_out_is_distinguished_from_failed_and_canceled():
    assert run_state("timed_out", None, None)[0] == "timed_out"
    assert run_state("failed", "syntax error at or near FROM", None)[1].startswith("syntax")
    assert run_state("canceled", None, None)[0] == "canceled"


def test_all_completed_but_the_schedule_has_stopped():
    # Weekly cadence, newest run 19 days old: every run succeeded and the schedule
    # is dead. This is the six-week silence, caught by arithmetic rather than status.
    state, detail = verdict(["completed"] * 8, 456.0, 168.0, True)
    assert state == "missing"
    assert "stopped producing runs" in detail


def test_completed_runs_with_no_subscriber_are_not_clear():
    assert verdict(["completed"], 6.0, 24.0, False)[0] == "email_only"
    assert verdict(["completed"], 6.0, 24.0, True)[0] == "clear"
    assert verdict([], None, 24.0, True)[0] == "silent"
''',
"test_js_file": "stripe-sigma-runs.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { runState, verdict } from './stripe-sigma-runs.mjs';

test('completed run with a live result is fine', () => {
  assert.equal(runState('completed', null, 3 * 86400)[0], 'completed');
});

test('completed but expired is its own state', () => {
  const [state, detail] = runState('completed', null, -7200);
  assert.equal(state, 'expired');
  assert.match(detail, /2\\.0 hour\\(s\\) ago/);
});

test('timed out is distinguished from failed and canceled', () => {
  assert.equal(runState('timed_out', null, null)[0], 'timed_out');
  assert.match(runState('failed', 'syntax error at or near FROM', null)[1], /^syntax/);
  assert.equal(runState('canceled', null, null)[0], 'canceled');
});

test('all completed but the schedule has stopped', () => {
  const [state, detail] = verdict(Array(8).fill('completed'), 456, 168, true);
  assert.equal(state, 'missing');
  assert.match(detail, /stopped producing runs/);
});

test('completed runs with no subscriber are not clear', () => {
  assert.equal(verdict(['completed'], 6, 24, false)[0], 'email_only');
  assert.equal(verdict(['completed'], 6, 24, true)[0], 'clear');
  assert.equal(verdict([], null, 24, true)[0], 'silent');
});
''',
"faq": [
 ("What are the terminal states of a scheduled query run?",
  "completed, canceled, failed and timed_out. Only completed produces a result file. Treat the other three separately: failed usually carries a message in error, timed_out means the execution budget was exceeded, and canceled is normally a person who stopped it."),
 ("Why does a query that worked for a year start timing out?",
  "Because nothing about the query changed and everything about the data did. A query that scans all history gets slower every day. Once it crosses the execution budget it fails every run from then on, so re-running it is not a fix; bounding what it scans is."),
 ("A run says completed but the file link is dead. Why?",
  "result_available_until has passed. Results expire on their own clock regardless of whether anyone downloaded them, so a run can be a genuine success with nothing left to fetch. Any workflow that downloads on a schedule rather than on receipt has to treat that timestamp as a deadline."),
 ("How do I detect a schedule that just stopped?",
  "By arithmetic, not by status, because there are no failed runs to find. Take the newest run's data_load_time and compare it against the cadence you expect. Twice the cadence with no run is a schedule that has stopped, not a quiet week."),
 ("Should I keep using email delivery?",
  "Use it if people want it, but do not rely on it as the signal. Subscribe an endpoint to sigma.scheduled_query_run.created and download data.object.file.url from the files API on receipt. A webhook that stops arriving is something your monitoring can notice; a missing email is not."),
],
"related": [
 ("/stripe/report-run-failed-silently/", "A report run fails after the 200 and no CSV lands"),
 ("/stripe/report-interval-past-data-available-end/", "A report run past data_available_end returns short data"),
 ("/stripe/unsubscribed-event-types-firing/", "Events fire that no endpoint subscribes to"),
],
"citations": [CITE_SIGMA_RUN_OBJ, CITE_SCHEDULE_QUERIES, CITE_EVENT_TYPES, CITE_WEBHOOKS],
},

{
"slug": "terminal-readers-offline",
"title": "Terminal readers sit offline and take no payments",
"description": "A location's card volume drops to zero and there is nothing to investigate, because no PaymentIntent was ever created. The reader is offline or stale.",
"h1": "terminal readers sit offline and take no payments",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe terminal reader offline", "terminal last_seen_at",
             "stripe reader not accepting payments", "terminal reader status online",
             "stripe terminal firmware version"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A shop's card takings were zero all weekend. There is nothing in the Dashboard to look at: no declines, no failed PaymentIntents, no errors. That is the tell. A reader that is offline does not fail payments, it never starts them, so the evidence of the outage is an absence of records rather than a list of them.",
"short_answer": """<p>Page <code>GET /v1/terminal/readers?limit=100</code> and check two things independently. <code>status == "offline"</code> is the obvious one. <code>last_seen_at</code> is the honest one: a reader that has not checked in for six hours is not usable, whatever <code>status</code> currently claims.</p>
<p>Watch the units. <code>last_seen_at</code> is in <strong>milliseconds</strong>, unlike almost every other timestamp in the Stripe API, so the obvious subtraction against a seconds clock is wrong by a factor of 1000 and reports every reader as decades stale. Also read <code>action.status</code> and <code>action.failure_code</code> for readers stuck on a failed action, and group <code>device_sw_version</code> per <code>device_type</code> to catch firmware drift.</p>""",
"problem": """<p>Terminal is the one part of a Stripe integration where the failure is physical. A router reboots overnight, a cleaner unplugs a dock, a guest network drops its lease, and the reader stops talking to Stripe. It cannot accept a <code>process_payment_intent</code> action, so nothing gets as far as creating a PaymentIntent.</p>
<p>That is what makes it invisible to every dashboard you already have. Payment failure alerts fire on failed payments. Decline-rate alerts fire on declines. A dead reader produces neither, because it produces nothing at all: the customer is told the machine is not working, they pay cash or leave, and your metrics record a slow day.</p>
<p>Staff report it as "the machine isn't doing anything", which is accurate and unhelpful, and it usually reaches you a day or two after it started because a Saturday is allowed to be slow. By then the only way to establish when it began is <code>last_seen_at</code>.</p>""",
"why": """<p><strong><code>status</code> lags reality, so it is not a liveness check.</strong> Stripe's own guidance is not to use it for blocking flows. A reader that lost its network moments ago can still read as online; the field that actually moves is <code>last_seen_at</code>, and comparing it against now is the only check that does not have to trust a cached state.</p>
<p><strong><code>last_seen_at</code> is milliseconds, and everything around it is seconds.</strong> <code>created</code> is seconds. Event timestamps are seconds. This one is not. A check written by analogy divides or subtracts on the wrong scale and either flags every reader in the fleet or none of them, and both of those look like a broken script rather than a units bug.</p>
<p><strong>Nothing fails, so nothing alerts.</strong> This is worth stating plainly because it changes what you have to build. There is no error to catch, no webhook to subscribe to for "a reader stopped existing", and no failed object to count. The only way to know is to ask, on a schedule, and to compare a timestamp.</p>
<p><strong>Firmware drift accumulates in the same silence.</strong> Readers update during a configured window while powered and connected. One that is habitually unplugged at night never gets its window, so it falls behind the rest of the fleet, and the one reader running a version from eight months ago is usually also the one with the most mysterious faults.</p>""",
"steps": [
 {"h": "List every reader and read last_seen_at, not just status",
  "body": """<p><code>GET /v1/terminal/readers?limit=100</code>, optionally narrowed with <code>&amp;location={tml_id}</code>. Compute the age from <code>last_seen_at</code> in milliseconds against a millisecond clock. Report a reader that claims to be online but has not checked in for hours as its own state, because that is the case a status-only check gets wrong.</p>"""},
 {"h": "Sanity-check the units before trusting the number",
  "body": """<p>A <code>last_seen_at</code> that looks like a seconds timestamp is either a units bug in your own code or a value you should not act on. Refusing to classify it beats reporting a fleet that has been dead since 1973, which is how this check gets ignored the first time it fires.</p>"""},
 {"h": "Look for readers stuck on a failed action",
  "body": """<p><code>action.status == "failed"</code> with a <code>failure_code</code> is a reader that is reachable but wedged, which needs a different response from one that is unreachable. It is also the only case here where the API has an error message to show you.</p>"""},
 {"h": "Group firmware by device type",
  "body": """<p>Tally <code>device_sw_version</code> within each <code>device_type</code> and report the readers that are not on the version the rest of their kind are running. Leave those powered and connected through the configured update window rather than chasing the update by hand.</p>"""},
 {"h": "Power-cycle, then re-verify against the API",
  "body": """<p>Restart the reader, confirm the location's network allows Stripe's endpoints, then read <code>GET /v1/terminal/readers/{tmr_id}</code> and check for <code>status: "online"</code> <em>and</em> a fresh <code>last_seen_at</code>. Retire hardware that is genuinely dead with <code>DELETE /v1/terminal/readers/{tmr_id}</code> so it stops occupying the alert every morning.</p>"""},
],
"verify": """<p>Re-run the script after the reader is back on the network. Every reader should be online with a recent check-in, and on the same firmware as the rest of its device type.</p>
<pre><code class="language-bash">python3 stripe_terminal_readers.py --stale-hours 6
# clear       7 reader(s) online, newest check-in 0.1h, firmware consistent</code></pre>""",
"code_intro": "One paginated GET and no writes &mdash; a restricted key with read access to Terminal is enough, and is what you should give it. Two pure functions: one classifies a reader from its status, its check-in age and its last action, including a guard against the millisecond mistake that makes this check useless, and one finds the firmware outliers within each device type.",
"py_file": "stripe_terminal_readers.py",
"py": '''"""Report Stripe Terminal readers that are offline, stale, wedged or behind on firmware.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Terminal. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import collections
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_terminal_readers")

API = "https://api.stripe.com/v1"

# last_seen_at is in MILLISECONDS, unlike almost every other Stripe timestamp.
# Anything below this is a seconds value that has been passed in by mistake:
# 1e11 ms is 1973, and 1e11 seconds is the year 5138, so no real reading is
# ambiguous. Refusing to judge beats reporting a fleet as decades stale.
MS_FLOOR = 100_000_000_000

STALE_HOURS = 6.0


def reader_state(status, last_seen_at_ms, now_ms, action_status=None,
                 failure_code=None, stale_hours=STALE_HOURS):
    """Classify one Terminal reader. Pure, so the units guard can be tested offline.

    `last_seen_at_ms` and `now_ms` are both milliseconds. Returns (state, detail).
    """
    if last_seen_at_ms is not None and last_seen_at_ms < MS_FLOOR:
        return ("unknown",
                "last_seen_at is %d, which is a seconds timestamp; this reader "
                "cannot be judged until the units are right" % last_seen_at_ms)
    age_h = (None if last_seen_at_ms is None
             else (now_ms - last_seen_at_ms) / 3_600_000.0)
    if status == "offline":
        seen = "never seen" if age_h is None else "last seen %.1f hour(s) ago" % age_h
        return ("offline", "status offline, %s; it will not take a payment" % seen)
    if age_h is None:
        return ("unknown", "no last_seen_at, so liveness cannot be confirmed")
    if age_h >= stale_hours:
        return ("stale",
                "status %s but no check-in for %.1f hour(s); status lags reality, "
                "so treat this as unusable" % (status, age_h))
    if action_status == "failed":
        return ("action_failed",
                "reachable but wedged on a failed action: %s"
                % (failure_code or "no failure_code on the action"))
    if status == "online":
        return ("online", "checked in %.1f hour(s) ago" % age_h)
    return ("unknown", "unrecognised status %r" % (status,))


def firmware_outliers(readers):
    """Readers not on the version most of their own device_type is running. Pure.

    `readers` is a list of dicts with id, device_type and device_sw_version. A
    device type with a single reader has no majority and is skipped rather than
    reported as an outlier against itself.
    """
    by_type = collections.defaultdict(list)
    for r in readers:
        by_type[r.get("device_type")].append(r)
    out = []
    for device_type, group in sorted(by_type.items(), key=lambda kv: str(kv[0])):
        versions = collections.Counter(r.get("device_sw_version") for r in group
                                       if r.get("device_sw_version"))
        if len(group) < 2 or not versions:
            continue
        majority, _ = versions.most_common(1)[0]
        for r in group:
            v = r.get("device_sw_version")
            if v and v != majority:
                out.append((r.get("id"), device_type, v, majority))
    return out


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    if r.status_code == 403:
        raise SystemExit("403 from Stripe: the restricted key has no read access to "
                         "Terminal")
    r.raise_for_status()
    return r.json()


def page_all(session, path, params, cap=2000):
    out = []
    params = dict(params)
    while True:
        page = get(session, path, params)
        data = page.get("data", [])
        out.extend(data)
        if not data or not page.get("has_more") or len(out) >= cap:
            return out
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--location", help="only check readers at this location id")
    ap.add_argument("--stale-hours", type=float, default=STALE_HOURS,
                    help="check-in age past which a reader is unusable")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    params = {"limit": 100}
    if args.location:
        params["location"] = args.location
    readers = page_all(s, "/terminal/readers", params)

    now_ms = int(time.time() * 1000)
    bad = 0
    freshest = None
    for r in readers:
        action = r.get("action") or {}
        state, detail = reader_state(r.get("status"), r.get("last_seen_at"), now_ms,
                                     action.get("status"), action.get("failure_code"),
                                     args.stale_hours)
        seen = r.get("last_seen_at")
        if seen and seen >= MS_FLOOR and (freshest is None or seen > freshest):
            freshest = seen
        if state != "online":
            bad += 1
            log.warning("  %-13s %s  %s  %s", state, r.get("id"),
                        r.get("label") or r.get("device_type"), detail)

    drift = firmware_outliers(readers)
    for rid, device_type, version, majority in drift:
        log.warning("  %-13s %s  %s on %s, the rest of the fleet is on %s",
                    "firmware", rid, device_type, version, majority)

    if not bad and not drift:
        age = 0.0 if freshest is None else (now_ms - freshest) / 3_600_000.0
        log.info("%-11s %d reader(s) online, newest check-in %.1fh, firmware consistent",
                 "clear", len(readers), age)
        return 0

    log.warning("%-11s %d of %d reader(s) not usable, %d on odd firmware",
                "offline", bad, len(readers), len(drift))
    log.warning("  power-cycle the reader and confirm the location's network reaches "
                "Stripe, then re-check:")
    log.warning("  GET %s/terminal/readers/<tmr_id>   "
                "(want status online AND a fresh last_seen_at)", API)
    log.warning("  leave drifting readers powered and connected through their "
                "configured update window")
    log.warning("  retire dead hardware so it stops filling this report:")
    log.warning("  DELETE %s/terminal/readers/<tmr_id>", API)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-terminal-readers.mjs",
"js": '''/**
 * Report Stripe Terminal readers that are offline, stale, wedged or behind on firmware.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Terminal. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// last_seen_at is in MILLISECONDS, unlike almost every other Stripe timestamp.
// Anything below this is a seconds value passed in by mistake.
export const MS_FLOOR = 100000000000;

export const STALE_HOURS = 6.0;

/**
 * Classify one Terminal reader. Pure, so the units guard can be tested offline.
 * `lastSeenAtMs` and `nowMs` are both milliseconds.
 */
export function readerState(status, lastSeenAtMs, nowMs, actionStatus = null,
                            failureCode = null, staleHours = STALE_HOURS) {
  const missing = (v) => v === null || v === undefined;
  if (!missing(lastSeenAtMs) && lastSeenAtMs < MS_FLOOR) {
    return ['unknown',
      `last_seen_at is ${lastSeenAtMs}, which is a seconds timestamp; this reader ` +
      'cannot be judged until the units are right'];
  }
  const ageH = missing(lastSeenAtMs) ? null : (nowMs - lastSeenAtMs) / 3600000;
  if (status === 'offline') {
    const seen = ageH === null ? 'never seen' : `last seen ${ageH.toFixed(1)} hour(s) ago`;
    return ['offline', `status offline, ${seen}; it will not take a payment`];
  }
  if (ageH === null) {
    return ['unknown', 'no last_seen_at, so liveness cannot be confirmed'];
  }
  if (ageH >= staleHours) {
    return ['stale',
      `status ${status} but no check-in for ${ageH.toFixed(1)} hour(s); status lags ` +
      'reality, so treat this as unusable'];
  }
  if (actionStatus === 'failed') {
    return ['action_failed',
      `reachable but wedged on a failed action: ${failureCode || 'no failure_code on the action'}`];
  }
  if (status === 'online') return ['online', `checked in ${ageH.toFixed(1)} hour(s) ago`];
  return ['unknown', `unrecognised status ${JSON.stringify(status)}`];
}

/** Readers not on the version most of their own device_type is running. Pure. */
export function firmwareOutliers(readers) {
  const byType = new Map();
  for (const r of readers) {
    if (!byType.has(r.device_type)) byType.set(r.device_type, []);
    byType.get(r.device_type).push(r);
  }
  const out = [];
  for (const deviceType of [...byType.keys()].sort((a, b) => String(a).localeCompare(String(b)))) {
    const group = byType.get(deviceType);
    const counts = new Map();
    for (const r of group) {
      if (r.device_sw_version) {
        counts.set(r.device_sw_version, (counts.get(r.device_sw_version) ?? 0) + 1);
      }
    }
    if (group.length < 2 || counts.size === 0) continue;
    let majority = null;
    let best = -1;
    for (const [v, n] of counts) if (n > best) { majority = v; best = n; }
    for (const r of group) {
      if (r.device_sw_version && r.device_sw_version !== majority) {
        out.push([r.id, deviceType, r.device_sw_version, majority]);
      }
    }
  }
  return out;
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (res.status === 403) {
    throw new Error('403 from Stripe: the restricted key has no read access to Terminal');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function pageAll(key, path, params, cap = 2000) {
  const out = [];
  const p = { ...params };
  for (;;) {
    const page = await get(key, path, p);
    const data = page.data ?? [];
    out.push(...data);
    if (data.length === 0 || !page.has_more || out.length >= cap) return out;
    p.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }
  const staleHours = Number(process.env.STALE_HOURS ?? STALE_HOURS);
  const params = { limit: 100 };
  if (process.env.LOCATION) params.location = process.env.LOCATION;
  const readers = await pageAll(key, '/terminal/readers', params);

  const nowMs = Date.now();
  let bad = 0;
  let freshest = null;
  for (const r of readers) {
    const action = r.action ?? {};
    const [state, detail] = readerState(r.status, r.last_seen_at, nowMs,
      action.status, action.failure_code, staleHours);
    if (r.last_seen_at && r.last_seen_at >= MS_FLOOR
        && (freshest === null || r.last_seen_at > freshest)) {
      freshest = r.last_seen_at;
    }
    if (state !== 'online') {
      bad += 1;
      console.warn(`  ${state.padEnd(13)} ${r.id}  ${r.label ?? r.device_type}  ${detail}`);
    }
  }

  const drift = firmwareOutliers(readers);
  for (const [rid, deviceType, version, majority] of drift) {
    console.warn(`  firmware      ${rid}  ${deviceType} on ${version}, the rest of ` +
                 `the fleet is on ${majority}`);
  }

  if (!bad && drift.length === 0) {
    const age = freshest === null ? 0 : (nowMs - freshest) / 3600000;
    console.log(`clear       ${readers.length} reader(s) online, newest check-in ` +
                `${age.toFixed(1)}h, firmware consistent`);
    return;
  }

  console.warn(`offline     ${bad} of ${readers.length} reader(s) not usable, ` +
               `${drift.length} on odd firmware`);
  console.warn('  power-cycle the reader and confirm the location network reaches ' +
               'Stripe, then re-check:');
  console.warn(`  GET ${API}/terminal/readers/<tmr_id>   ` +
               '(want status online AND a fresh last_seen_at)');
  console.warn('  leave drifting readers powered and connected through their ' +
               'configured update window');
  console.warn('  retire dead hardware so it stops filling this report:');
  console.warn(`  DELETE ${API}/terminal/readers/<tmr_id>`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail the suite on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the one that matters most, and it is about units: a <code>last_seen_at</code> that arrived in seconds must not be quietly turned into a reader that has been missing for fifty years. After that it is the ordering &mdash; that a stale check-in outranks a cheerful <code>online</code> &mdash; and the firmware tally, which must not call a lone reader an outlier against itself.",
"test_py_file": "test_stripe_terminal_readers.py",
"test_py": '''from stripe_terminal_readers import firmware_outliers, reader_state

NOW_MS = 1_756_000_000_000
HOUR = 3_600_000


def test_a_seconds_timestamp_is_refused_not_believed():
    # 1756000000 is a perfectly good seconds timestamp and a nonsense millisecond
    # one. Reporting it as 50 years stale is how this check gets ignored.
    state, detail = reader_state("online", NOW_MS // 1000, NOW_MS)
    assert state == "unknown"
    assert "seconds timestamp" in detail


def test_recent_check_in_on_an_online_reader_is_fine():
    state, _ = reader_state("online", NOW_MS - HOUR, NOW_MS)
    assert state == "online"


def test_stale_beats_a_cheerful_status():
    # status lags reality, so six hours without a check-in is unusable even while
    # the reader still claims to be online.
    assert reader_state("online", NOW_MS - 5 * HOUR, NOW_MS)[0] == "online"
    state, detail = reader_state("online", NOW_MS - 6 * HOUR, NOW_MS)
    assert state == "stale"
    assert "status lags reality" in detail


def test_offline_and_wedged_are_different_problems():
    assert reader_state("offline", NOW_MS - HOUR, NOW_MS)[0] == "offline"
    state, detail = reader_state("online", NOW_MS - HOUR, NOW_MS,
                                 "failed", "reader_timeout")
    assert state == "action_failed"
    assert "reader_timeout" in detail


def test_firmware_outliers_need_a_majority_to_be_outliers_from():
    fleet = [
        {"id": "tmr_1", "device_type": "bbpos_wisepos_e", "device_sw_version": "2.24"},
        {"id": "tmr_2", "device_type": "bbpos_wisepos_e", "device_sw_version": "2.24"},
        {"id": "tmr_3", "device_type": "bbpos_wisepos_e", "device_sw_version": "2.11"},
        {"id": "tmr_4", "device_type": "stripe_s700", "device_sw_version": "1.4"},
    ]
    out = firmware_outliers(fleet)
    assert [row[0] for row in out] == ["tmr_3"]
    assert out[0][3] == "2.24"
''',
"test_js_file": "stripe-terminal-readers.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { firmwareOutliers, readerState } from './stripe-terminal-readers.mjs';

const NOW_MS = 1756000000000;
const HOUR = 3600000;

test('a seconds timestamp is refused, not believed', () => {
  const [state, detail] = readerState('online', Math.floor(NOW_MS / 1000), NOW_MS);
  assert.equal(state, 'unknown');
  assert.match(detail, /seconds timestamp/);
});

test('recent check-in on an online reader is fine', () => {
  assert.equal(readerState('online', NOW_MS - HOUR, NOW_MS)[0], 'online');
});

test('stale beats a cheerful status', () => {
  assert.equal(readerState('online', NOW_MS - 5 * HOUR, NOW_MS)[0], 'online');
  const [state, detail] = readerState('online', NOW_MS - 6 * HOUR, NOW_MS);
  assert.equal(state, 'stale');
  assert.match(detail, /status lags reality/);
});

test('offline and wedged are different problems', () => {
  assert.equal(readerState('offline', NOW_MS - HOUR, NOW_MS)[0], 'offline');
  const [state, detail] = readerState('online', NOW_MS - HOUR, NOW_MS,
    'failed', 'reader_timeout');
  assert.equal(state, 'action_failed');
  assert.match(detail, /reader_timeout/);
});

test('firmware outliers need a majority to be outliers from', () => {
  const fleet = [
    { id: 'tmr_1', device_type: 'bbpos_wisepos_e', device_sw_version: '2.24' },
    { id: 'tmr_2', device_type: 'bbpos_wisepos_e', device_sw_version: '2.24' },
    { id: 'tmr_3', device_type: 'bbpos_wisepos_e', device_sw_version: '2.11' },
    { id: 'tmr_4', device_type: 'stripe_s700', device_sw_version: '1.4' },
  ];
  const out = firmwareOutliers(fleet);
  assert.deepEqual(out.map((row) => row[0]), ['tmr_3']);
  assert.equal(out[0][3], '2.24');
});
''',
"faq": [
 ("Why is there nothing to investigate when a reader goes down?",
  "Because an offline reader never starts a payment. It cannot accept a process_payment_intent action, so no PaymentIntent is created, no charge fails and no decline is recorded. Every alert you have is watching for failed objects, and there are none. The outage is an absence of records."),
 ("Is status enough to tell whether a reader is usable?",
  "No, and Stripe says not to rely on it for blocking flows. It can lag the reader's real state. last_seen_at compared against now is the check that does not depend on a cached status, which is why this script treats a stale check-in as unusable even when status still says online."),
 ("Why is last_seen_at in milliseconds?",
  "It just is, unlike created and almost every other timestamp in the API, which are seconds. That inconsistency is the single most common bug in a check like this: a subtraction on the wrong scale either flags the whole fleet or none of it. The script refuses to classify a value that looks like seconds rather than guessing."),
 ("What does a failed action on a reader mean?",
  "The reader is reachable but wedged on the last thing it was asked to do; action.failure_code says which way. That is a different repair from an unreachable reader, because the network is fine and the device is answering, so start with the action rather than the router."),
 ("How do I stop firmware drifting?",
  "Readers update during their configured window while powered and connected, so the reader that is switched off overnight is the one that falls behind. Group device_sw_version within each device_type, find the ones that are not on the same version as their peers, and leave those powered through the window."),
],
"related": [
 ("/stripe/stale-requires-payment-method-intents/", "PaymentIntents left in requires_payment_method"),
 ("/stripe/missing-payment-failure-events/", "Payment failure events nobody subscribes to"),
 ("/stripe/report-run-failed-silently/", "A report run fails after the 200 and no CSV lands"),
],
"citations": [CITE_TERMINAL_READER_OBJ, CITE_TERMINAL, CITE_EVENT_TYPES],
},

]
