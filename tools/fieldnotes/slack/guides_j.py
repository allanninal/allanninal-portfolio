#!/usr/bin/env python3
"""/slack/ field notes, batch J — the writing.

Four notes about rate limits, which is the batch most at risk of being one note
written four times. So each one probes a different surface and none of them is
allowed to end on "add backoff".

The first is about what happens *after* the refusal: Slack tells you how long to
wait, in a header, and hand-rolled clients throw it away. The second is not
about a tier at all — chat.postMessage is roughly one message per second per
channel, and the evidence is arithmetic on the timestamps of messages your app
already sent. The third is a budget problem you can settle offline: a method
whose documented tier is 1 sitting inside a loop that runs every thirty seconds.
The fourth is about the key the quota is stored under, which is (method,
workspace, app) and not (method, workspace, app, process), so eight replicas
that each behave perfectly still starve each other.

Read-only throughout, and with one extra rule this batch needs and the others do
not: none of these scripts drives traffic into a 429 to prove a limit exists.
Deliberately exhausting a window is a denial of service against the workspace
you were asked to audit. The findings come from headers Slack returned anyway,
from documented tiers, from timestamps already in the channel, and from records
the caller supplies.
"""

CITE_RATE_LIMITS = ("Rate limits — Slack Docs",
                    "https://docs.slack.dev/apis/web-api/rate-limits")
CITE_WEB_API = ("Using the Web API — Slack Docs",
                "https://docs.slack.dev/apis/web-api/")
CITE_RATE_CLARITY = ("Rate limits: added clarity — Slack Docs",
                     "https://docs.slack.dev/changelog/2025/06/03/rate-limits-clarity/")
CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_POSTMESSAGE = ("chat.postMessage method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_CHAT_UPDATE = ("chat.update method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.update")
CITE_CONV_HISTORY = ("conversations.history method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_CONV_LIST = ("conversations.list method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.list")
CITE_USERS_LIST = ("users.list method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.list")
CITE_EVENTS = ("Events API — Slack Docs",
               "https://docs.slack.dev/apis/events-api/")

GUIDES = [

{
"slug": "ratelimited-retry-after-ignored",
"title": "ratelimited: the Retry-After header nobody read",
"description": "Slack says exactly how long to wait and hand-rolled clients discard it. Parse Retry-After defensively, then replay your own retry log offline.",
"h1": "ratelimited: the Retry-After header nobody read",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack ratelimited error", "slack retry-after header",
             "slack 429 rate limit backoff", "slack api exponential backoff",
             "slack rate limit retry"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the replay half reads a log you already have",
"lead": "The backfill runs beautifully for ninety seconds and then produces a wall of the same line. <code>ratelimited</code>. Sometimes a real <code>HTTP 429</code>, sometimes an <code>HTTP 200</code> whose body says <code>ok: false</code>. The client sees a failure, does what it does with failures, and tries again immediately, which is the one response guaranteed to make it last longer.</p><p>Slack answered that question before you asked it. The wait is in a header, in seconds, on the response you already have.",
"short_answer": """<p>Slack rate-limits per method, per workspace, per app, on a rolling one-minute window. When the window is spent it answers with <code>Retry-After</code>, in whole seconds, and the correct behaviour is to sleep for that long and try once more. The two things that go wrong are equally common: clients that never look at the header, and clients that look at it and crash when it is not there.</p>
<p>The script below has two halves. It makes a handful of ordinary read calls and prints the status, the body error and the <code>Retry-After</code> value exactly as Slack sent them, so you can see which shape your workspace produces. Then it replays a log you already have &mdash; the refusals your own client recorded, with the wait it actually took &mdash; and says for each one whether the header was honoured, undercut, or replaced with a fixed sleep that had nothing to do with the answer.</p>
<p>It does not provoke a limit to demonstrate one. Exhausting a window on purpose is a denial of service against the workspace you were asked to audit.</p>""",
"problem": """<p>A rate limit is the one API failure that carries its own remedy. Slack computed the window, knows when it reopens, and puts the number of seconds in a response header. Every other error in this section makes you go and find out what to do. This one does not, which is exactly why it is so consistently mishandled: the information arrives somewhere a generic HTTP client is not looking.</p>
<p>What that client sees is a failure, so it applies whatever failure policy it has. Retry immediately, and the next call spends a request out of a window that has not reopened, which on some surfaces extends the penalty. Retry with exponential backoff seeded at one second, and the first four attempts are wasted before the wait is long enough to matter. Retry with a flat sixty-second sleep, and a limit that wanted three seconds costs you a minute, every time, forever. All three of those are written by careful people. None of them read the number.</p>
<p>Then there is the shape problem. Slack sometimes returns a genuine <code>429</code> and sometimes returns <code>HTTP 200</code> with <code>{"ok": false, "error": "ratelimited"}</code>, and a client that switches on the status code catches one of those and treats the other as data. <code>Retry-After</code> is present on both shapes, and is occasionally absent, empty, or something the parser did not expect. Code written as <code>int(response.headers["Retry-After"])</code> is one missing header away from a <code>KeyError</code> inside the error path, which is the worst place in any program to put an unhandled exception: the process dies during the incident rather than during the test.</p>""",
"why": """<p><strong>The header is a schedule, not a hint.</strong> It is not a suggestion computed from a heuristic on your side; it is Slack reporting when the window it maintains reopens. Any backoff you invent is a guess at a number you were told.</p>
<p><strong>Absent is not zero, and absent is not sixty.</strong> When the header is missing the honest move is a documented default &mdash; thirty seconds is a reasonable one &mdash; recorded as a default rather than as an answer. The failure mode to avoid is a parser that treats a missing header as permission to retry now.</p>
<p><strong>Both response shapes are the same event.</strong> A true <code>429</code> and an <code>HTTP 200</code> carrying <code>error: "ratelimited"</code> mean the identical thing and want the identical handling. Any code path that treats one as transport and the other as business logic will handle them differently, and will be right about at most one.</p>
<p><strong>Retrying early is worse than not retrying.</strong> A request that arrives inside a closed window is still a request. Undercutting the header converts a wait into a longer wait, which is why a job that "retries aggressively" finishes after a job that sleeps politely.</p>
<p><strong>The strongest repair is to stop writing the client.</strong> Both official SDKs already do this correctly &mdash; <code>@slack/web-api</code> through its retry configuration, <code>slack_sdk</code> through its built-in retry handlers. A hand-rolled transport layer is the thing under audit here far more often than the rate limit is.</p>""",
"steps": [
 {"h": "Capture three things on every response, not one",
  "body": """<p>Status, <code>body.error</code>, and the <code>Retry-After</code> header, logged together. Most clients keep the first or the second and never the third, which makes the whole question unanswerable after the fact. This is a one-line change in a transport wrapper and it is the change that makes everything below possible.</p>"""},
 {"h": "Look at what your own workspace actually returns",
  "body": """<p>The sweep makes a small number of ordinary read calls, one per method, and prints the shape of each response. Under normal conditions nothing is throttled and the sweep is boring, which is the point: it proves the capture path works before an incident needs it.</p>"""},
 {"h": "Parse the header defensively and label the result",
  "body": """<p>Present and numeric is an answer. Missing, empty, non-numeric, negative, zero or implausibly large are five different situations and none of them is an answer. The parser returns a number in every case and says which case it was, so a log line can distinguish "Slack asked for 3 seconds" from "we defaulted to 30 because nothing was returned".</p>"""},
 {"h": "Replay the refusals you already logged",
  "body": """<p>Feed the script the records your client wrote: the method, the status, the body, the headers, and how long it waited before trying again. It is completely offline, and it is where the finding lives. Nothing has to be reproduced, and nothing has to be provoked.</p>"""},
 {"h": "Treat undercutting and oversleeping as separate bugs",
  "body": """<p>Retrying inside the window is a correctness bug that lengthens the outage. Sleeping four times longer than asked is a throughput bug that makes the job look rate-limited when it is mostly idle. They have different causes and the report keeps them apart.</p>"""},
 {"h": "Delete the backoff and adopt the SDK's",
  "body": """<p>Once the log shows which of the two you have, the repair is usually subtraction rather than addition. The official clients implement this correctly, including the missing-header case, and a hand-written transport layer that gets it wrong is a liability that will be rediscovered by the next person on call.</p>"""},
],
"verify": """<p>Re-run the replay against a log captured after the change. Every throttled record should come back honoured, and the sweep should show the header being captured even on the calls that succeed.</p>
<pre><code class="language-bash">python3 slack_retry_after_audit.py --record retries.json
# sweep    conversations.list   ok               no Retry-After returned, nothing to honour
# sweep    users.list           ok               no Retry-After returned, nothing to honour
# replay   conversations.history  honoured       Slack asked for 12s, the client waited 12.4s
# replay   users.list             honoured       Slack asked for 30s, the client waited 30.1s
# 2 sweep call(s), 2 replayed refusal(s), 0 mishandled</code></pre>""",
"code_intro": "Three pure functions and one GET helper. <code>retry_after_seconds</code> is the whole note in miniature: it always returns a number and always says where the number came from, so a default is never mistaken for an answer. <code>classify_response</code> collapses the two shapes Slack uses into one state. <code>replay_verdict</code> is entirely offline and reads a log you already have, which is how this script audits rate-limit handling without generating a single rate limit.",
"py_file": "slack_retry_after_audit.py",
"py": '''"""Audit what this app does with a Slack rate-limit refusal.

Read only, and it never provokes one. Two halves. A small sweep of read methods
records the status, the body error and the Retry-After header exactly as Slack
returned them, so you can see the shape your workspace produces. Then an offline
replay of refusals your own client already logged says, for each, whether the
header was honoured, undercut, or replaced by a sleep unrelated to the answer.

Deliberately exhausting a window to demonstrate that windows exist is a denial
of service against the workspace being audited, so this does not do that.
"""
import argparse
import json
import logging
import math
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_retry_after_audit")

API = "https://slack.com/api/"

# What to sleep when Slack did not tell us. Documented rather than clever: the
# number matters far less than the fact that it is recorded as a default and not
# reported as though Slack had asked for it.
DEFAULT_WAIT = 30.0

# A Retry-After longer than this is almost certainly a parsing accident rather
# than an instruction, so it is clamped and flagged instead of obeyed.
CEILING = 600.0

# Waiting less than this fraction of the window is retrying early. Waiting more
# than this multiple of it is a fixed sleep wearing a backoff costume.
EARLY = 0.95
BLIND = 4.0

# Read methods safe to call once each, with the smallest page they will accept.
# One call per method: the sweep is here to prove the capture path works, not to
# find the edge of the window.
SWEEP = (
    ("conversations.list", {"limit": 1, "exclude_archived": "true"}),
    ("users.list", {"limit": 1}),
)


def retry_after_seconds(headers):
    """Read Retry-After defensively. Pure. Returns (seconds, source, detail).

    Always returns a usable number, and always says where that number came from,
    because the difference between "Slack asked for 3 seconds" and "nothing came
    back so we picked 30" is the difference between a schedule and a guess. The
    common one-liner, int(headers["Retry-After"]), raises inside the error path
    when the header is absent, which kills the process during the incident.
    """
    raw = None
    for key, value in (headers or {}).items():
        if str(key).strip().lower() == "retry-after":
            raw = value
            break

    if raw is None:
        return (DEFAULT_WAIT, "absent",
                "no Retry-After came back. Slack usually sends one and sometimes "
                "does not, so this is a default and is reported as one.")

    text = str(raw).strip()
    if not text:
        return (DEFAULT_WAIT, "empty",
                "Retry-After was present and empty, which is indistinguishable "
                "from absent for every purpose except a parser that assumes a "
                "value is there because a key is.")

    try:
        seconds = float(text)
    except ValueError:
        return (DEFAULT_WAIT, "unparseable",
                "Retry-After was %r, which is not a number of seconds. A date "
                "form is legal HTTP and is not what Slack sends; anything that "
                "parses it as an integer without guarding gets an exception "
                "inside the retry path." % text)

    if not math.isfinite(seconds):
        return (DEFAULT_WAIT, "unparseable",
                "Retry-After was %r, which parsed to a non-finite number." % text)
    if seconds < 0:
        return (DEFAULT_WAIT, "negative",
                "Retry-After was negative. Treated as no answer rather than as "
                "permission to retry immediately.")
    if seconds == 0:
        return (1.0, "zero",
                "Retry-After was zero. Retrying instantly on a window that just "
                "closed spends a request inside it, so this waits one second.")
    if seconds > CEILING:
        return (CEILING, "clamped",
                "Retry-After was %.0f seconds, past the %.0f second ceiling this "
                "audit trusts. Clamped, and worth reading the raw response."
                % (seconds, CEILING))

    return (seconds, "header",
            "Slack asked for %.0f second(s) and that is the whole schedule."
            % seconds)


def classify_response(status, body, headers=None):
    """Name what Slack actually returned. Pure. Returns (state, detail).

    A true 429 and an HTTP 200 whose body carries error: "ratelimited" are the
    same event and want the same handling. Code that switches on the status code
    catches one of them and treats the other as data.
    """
    body = body if isinstance(body, dict) else {}
    error = str(body.get("error") or "").strip()
    try:
        code = int(status or 0)
    except (TypeError, ValueError):
        code = 0

    if code == 429:
        return ("throttled-429",
                "a real HTTP 429. The rarer of the two shapes, and the only one "
                "a generic HTTP client notices without being told to.")
    if body.get("ok") is True:
        return ("ok", "the call succeeded, so nothing here is being throttled.")
    if error == "ratelimited":
        return ("throttled-200",
                "HTTP %d with ok: false and error ratelimited. The same event as "
                "a 429, arriving on the success path." % code)
    if error:
        return ("refused",
                "%s is a refusal and it is not a rate limit. Backing off will "
                "not change it." % error)
    return ("unreadable",
            "HTTP %d with no ok field and no error. Log the body verbatim; "
            "something between you and Slack rewrote the response." % code)


def replay_verdict(record):
    """Judge one refusal the client already logged. Pure and offline.

    record: {"method", "status", "body", "headers", "waited"}. `waited` is the
    seconds the client actually slept before its next attempt, or None if it did
    not record one.
    """
    record = record or {}
    method = str(record.get("method") or "?")
    state, detail = classify_response(record.get("status"),
                                      record.get("body"),
                                      record.get("headers"))
    if state in ("ok", "refused", "unreadable"):
        return ("not-a-refusal", state,
                "%s: %s Nothing about backoff is decided here." % (method, detail))

    seconds, source, why = retry_after_seconds(record.get("headers"))
    waited = record.get("waited")
    if waited is None:
        return ("no-wait-recorded", state,
                "%s was throttled and the client logged no wait at all. Either it "
                "retried without pausing, or it raised inside the error path and "
                "never got as far as retrying. %s" % (method, why))

    try:
        waited = float(waited)
    except (TypeError, ValueError):
        return ("no-wait-recorded", state,
                "%s recorded a wait of %r, which is not a duration." % (method, waited))

    if waited < seconds * EARLY:
        return ("retried-early", state,
                "%s waited %.1fs against a window of %.0fs. The retry lands inside "
                "a window that has not reopened, which spends a request and makes "
                "the outage longer than doing nothing. %s" % (method, waited, seconds, why))
    if waited > seconds * BLIND:
        return ("slept-blind", state,
                "%s waited %.1fs against a window of %.0fs. That is a fixed sleep "
                "rather than an answer, and it turns a short throttle into a long "
                "one on every occurrence. %s" % (method, waited, seconds, why))
    return ("honoured", state,
            "%s waited %.1fs against a window of %.0fs. %s"
            % (method, waited, seconds, why))


def probe(session, method, params):
    """One read call. GET only, and exactly one: no retry, no second attempt."""
    res = session.get(API + method, params=params, timeout=30)
    try:
        body = res.json()
    except ValueError:
        body = {}
    return (res.status_code, body, dict(res.headers))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--record", default="",
                    help="JSON file of refusals the client already logged")
    ap.add_argument("--no-sweep", action="store_true",
                    help="skip the live half and replay the log only")
    args = ap.parse_args()

    mishandled = 0
    sweeps = 0

    if not args.no_sweep:
        token = os.environ.get(args.token_env)
        if not token:
            log.error("set %s, or pass --no-sweep to replay a log offline",
                      args.token_env)
            return 2
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})

        identity = s.get(API + "auth.test", timeout=30).json()
        if identity.get("ok") is not True:
            log.error("auth.test answered ok: false, error=%s", identity.get("error"))
            return 2
        log.info("identity  %s in %s", identity.get("user_id"), identity.get("team"))

        for method, params in SWEEP:
            status, body, headers = probe(s, method, params)
            state, detail = classify_response(status, body, headers)
            seconds, source, why = retry_after_seconds(headers)
            sweeps += 1
            if state.startswith("throttled"):
                mishandled += 1
                log.warning("sweep    %-22s %-16s %s", method, state, detail)
                log.warning("  window: %.0fs from the %s. One ordinary read was "
                            "enough to be throttled, so the app's real traffic is "
                            "well past this method's tier", seconds, source)
            elif source == "header":
                log.info("sweep    %-22s %-16s %s", method, state, why)
            else:
                log.info("sweep    %-22s %-16s no Retry-After returned, nothing "
                         "to honour", method, state)

    replayed = 0
    if args.record:
        records = json.loads(open(args.record, encoding="utf-8").read())
        for record in records:
            verdict, state, detail = replay_verdict(record)
            replayed += 1
            if verdict in ("honoured", "not-a-refusal"):
                log.info("replay   %-16s %s", verdict, detail)
                continue
            mishandled += 1
            log.warning("replay   %-16s %s", verdict, detail)
            if verdict == "retried-early":
                log.warning("  repair: sleep for the header before the next attempt, "
                            "not for a number your backoff invented")
            elif verdict == "slept-blind":
                log.warning("  repair: read Retry-After instead of the constant; "
                            "the constant is why this job looks slow while idle")
            else:
                log.warning("  repair: guard the header read. A missing Retry-After "
                            "must produce a documented default, never an exception "
                            "inside the error path")

    log.info("%d sweep call(s), %d replayed refusal(s), %d mishandled",
             sweeps, replayed, mishandled)
    return 1 if mishandled else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-retry-after-audit.mjs",
"js": '''/**
 * Audit what this app does with a Slack rate-limit refusal.
 *
 * Read only, and it never provokes one. A small sweep of read methods records
 * the status, the body error and the Retry-After header exactly as Slack
 * returned them. Then an offline replay of refusals the client already logged
 * says whether the header was honoured, undercut, or replaced by a fixed sleep.
 *
 * Deliberately exhausting a window to prove windows exist is a denial of
 * service against the workspace being audited, so this does not do that.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Documented rather than clever. The number matters far less than the fact that
// it is recorded as a default and not reported as though Slack had asked for it.
const DEFAULT_WAIT = 30;
const CEILING = 600;
const EARLY = 0.95;
const BLIND = 4.0;

const SWEEP = [
  ['conversations.list', { limit: '1', exclude_archived: 'true' }],
  ['users.list', { limit: '1' }],
];

/**
 * Read Retry-After defensively. Pure. Returns [seconds, source, detail].
 * Always returns a usable number and always says where it came from.
 */
export function retryAfterSeconds(headers) {
  let raw = null;
  for (const [key, value] of Object.entries(headers ?? {})) {
    if (String(key).trim().toLowerCase() === 'retry-after') { raw = value; break; }
  }

  if (raw === null || raw === undefined) {
    return [DEFAULT_WAIT, 'absent',
      'no Retry-After came back. Slack usually sends one and sometimes does ' +
      'not, so this is a default and is reported as one.'];
  }

  const text = String(raw).trim();
  if (!text) {
    return [DEFAULT_WAIT, 'empty',
      'Retry-After was present and empty, which is indistinguishable from ' +
      'absent for every purpose except a parser that assumes a value is there ' +
      'because a key is.'];
  }

  // Number('') is 0 and Number('12abc') is NaN, so the emptiness check above has
  // to come first or an empty header silently becomes an instant retry.
  const seconds = Number(text);
  if (!Number.isFinite(seconds)) {
    return [DEFAULT_WAIT, 'unparseable',
      `Retry-After was ${JSON.stringify(text)}, which is not a number of ` +
      'seconds. A date form is legal HTTP and is not what Slack sends; ' +
      'anything that parses it without guarding throws inside the retry path.'];
  }
  if (seconds < 0) {
    return [DEFAULT_WAIT, 'negative',
      'Retry-After was negative. Treated as no answer rather than as ' +
      'permission to retry immediately.'];
  }
  if (seconds === 0) {
    return [1, 'zero',
      'Retry-After was zero. Retrying instantly on a window that just closed ' +
      'spends a request inside it, so this waits one second.'];
  }
  if (seconds > CEILING) {
    return [CEILING, 'clamped',
      `Retry-After was ${seconds.toFixed(0)} seconds, past the ${CEILING} ` +
      'second ceiling this audit trusts. Clamped, and worth reading the raw ' +
      'response.'];
  }

  return [seconds, 'header',
    `Slack asked for ${seconds.toFixed(0)} second(s) and that is the whole schedule.`];
}

/**
 * Name what Slack actually returned. Pure. Returns [state, detail].
 * A true 429 and an HTTP 200 carrying error: "ratelimited" are the same event.
 */
export function classifyResponse(status, body, headers = null) {
  const doc = (body && typeof body === 'object') ? body : {};
  const error = String(doc.error ?? '').trim();
  const code = Number.isFinite(Number(status)) ? Number(status) : 0;

  if (code === 429) {
    return ['throttled-429',
      'a real HTTP 429. The rarer of the two shapes, and the only one a ' +
      'generic HTTP client notices without being told to.'];
  }
  if (doc.ok === true) {
    return ['ok', 'the call succeeded, so nothing here is being throttled.'];
  }
  if (error === 'ratelimited') {
    return ['throttled-200',
      `HTTP ${code} with ok: false and error ratelimited. The same event as a ` +
      '429, arriving on the success path.'];
  }
  if (error) {
    return ['refused',
      `${error} is a refusal and it is not a rate limit. Backing off will not ` +
      'change it.'];
  }
  return ['unreadable',
    `HTTP ${code} with no ok field and no error. Log the body verbatim; ` +
    'something between you and Slack rewrote the response.'];
}

/**
 * Judge one refusal the client already logged. Pure and offline.
 * record: { method, status, body, headers, waited }.
 */
export function replayVerdict(record) {
  const doc = record ?? {};
  const method = String(doc.method ?? '?');
  const [state, detail] = classifyResponse(doc.status, doc.body, doc.headers);
  if (state === 'ok' || state === 'refused' || state === 'unreadable') {
    return ['not-a-refusal', state,
      `${method}: ${detail} Nothing about backoff is decided here.`];
  }

  const [seconds, , why] = retryAfterSeconds(doc.headers);
  if (doc.waited === null || doc.waited === undefined) {
    return ['no-wait-recorded', state,
      `${method} was throttled and the client logged no wait at all. Either it ` +
      'retried without pausing, or it threw inside the error path and never ' +
      `got as far as retrying. ${why}`];
  }

  const waited = Number(doc.waited);
  if (!Number.isFinite(waited)) {
    return ['no-wait-recorded', state,
      `${method} recorded a wait of ${JSON.stringify(doc.waited)}, which is ` +
      'not a duration.'];
  }

  if (waited < seconds * EARLY) {
    return ['retried-early', state,
      `${method} waited ${waited.toFixed(1)}s against a window of ` +
      `${seconds.toFixed(0)}s. The retry lands inside a window that has not ` +
      'reopened, which spends a request and makes the outage longer than doing ' +
      `nothing. ${why}`];
  }
  if (waited > seconds * BLIND) {
    return ['slept-blind', state,
      `${method} waited ${waited.toFixed(1)}s against a window of ` +
      `${seconds.toFixed(0)}s. That is a fixed sleep rather than an answer, and ` +
      `it turns a short throttle into a long one on every occurrence. ${why}`];
  }
  return ['honoured', state,
    `${method} waited ${waited.toFixed(1)}s against a window of ` +
    `${seconds.toFixed(0)}s. ${why}`];
}

/** One read call. GET only, and exactly one: no retry, no second attempt. */
async function probe(token, method, params) {
  const qs = new URLSearchParams(params);
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  let body = {};
  try { body = await res.json(); } catch { body = {}; }
  return [res.status, body, Object.fromEntries(res.headers.entries())];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const recordFile = arg(args, '--record', '');
  const noSweep = args.includes('--no-sweep');

  let mishandled = 0;
  let sweeps = 0;

  if (!noSweep) {
    const token = process.env[tokenEnv];
    if (!token) {
      console.error(`set ${tokenEnv}, or pass --no-sweep to replay a log offline`);
      process.exitCode = 2;
      return;
    }

    const [, identity] = await probe(token, 'auth.test', {});
    if (identity.ok !== true) {
      console.error(`auth.test answered ok: false, error=${identity.error}`);
      process.exitCode = 2;
      return;
    }
    console.log(`identity  ${identity.user_id} in ${identity.team}`);

    for (const [method, params] of SWEEP) {
      const [status, body, headers] = await probe(token, method, params);
      const [state, detail] = classifyResponse(status, body, headers);
      const [seconds, source, why] = retryAfterSeconds(headers);
      sweeps += 1;
      if (state.startsWith('throttled')) {
        mishandled += 1;
        console.warn(`sweep    ${method.padEnd(22)} ${state.padEnd(16)} ${detail}`);
        console.warn(`  window: ${seconds.toFixed(0)}s from the ${source}. One ` +
          'ordinary read was enough to be throttled, so the app\\'s real traffic ' +
          'is well past this method\\'s tier');
      } else if (source === 'header') {
        console.log(`sweep    ${method.padEnd(22)} ${state.padEnd(16)} ${why}`);
      } else {
        console.log(`sweep    ${method.padEnd(22)} ${state.padEnd(16)} no ` +
          'Retry-After returned, nothing to honour');
      }
    }
  }

  let replayed = 0;
  if (recordFile) {
    const records = JSON.parse(await readFile(recordFile, 'utf8'));
    for (const record of records) {
      const [verdict, , detail] = replayVerdict(record);
      replayed += 1;
      if (verdict === 'honoured' || verdict === 'not-a-refusal') {
        console.log(`replay   ${verdict.padEnd(16)} ${detail}`);
        continue;
      }
      mishandled += 1;
      console.warn(`replay   ${verdict.padEnd(16)} ${detail}`);
      if (verdict === 'retried-early') {
        console.warn('  repair: sleep for the header before the next attempt, not ' +
          'for a number your backoff invented');
      } else if (verdict === 'slept-blind') {
        console.warn('  repair: read Retry-After instead of the constant; the ' +
          'constant is why this job looks slow while idle');
      } else {
        console.warn('  repair: guard the header read. A missing Retry-After must ' +
          'produce a documented default, never an exception inside the error path');
      }
    }
  }

  console.log(`${sweeps} sweep call(s), ${replayed} replayed refusal(s), ` +
    `${mishandled} mishandled`);
  process.exitCode = mishandled ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are headers rather than workspaces, because the header is the whole subject. Six of the tests pin cases that are not a number of seconds &mdash; absent, empty, an HTTP date, negative, zero, implausibly large &mdash; and every one of them returns a usable wait with a label saying it was a default. Two pin that a real <code>429</code> and an <code>HTTP 200</code> carrying <code>ratelimited</code> reach the same state. The replay tests pin the three ways a client gets it wrong and the one way it does not.",
"test_py_file": "test_slack_retry_after_audit.py",
"test_py": '''from slack_retry_after_audit import (classify_response, replay_verdict,
                                       retry_after_seconds)

THROTTLED = {"ok": False, "error": "ratelimited"}


def test_a_numeric_header_is_the_schedule():
    seconds, source, detail = retry_after_seconds({"Retry-After": "12"})
    assert seconds == 12.0
    assert source == "header"
    assert "12" in detail


def test_the_header_name_is_matched_without_regard_to_case():
    assert retry_after_seconds({"retry-after": "7"})[0] == 7.0
    assert retry_after_seconds({"RETRY-AFTER": "7"})[0] == 7.0
    assert retry_after_seconds({" Retry-After ": "7"})[0] == 7.0


def test_an_absent_header_returns_a_default_that_says_it_is_a_default():
    seconds, source, _ = retry_after_seconds({})
    assert seconds == 30.0
    assert source == "absent"
    assert retry_after_seconds(None)[1] == "absent"


def test_an_empty_header_is_not_permission_to_retry_now():
    seconds, source, _ = retry_after_seconds({"Retry-After": "  "})
    assert seconds == 30.0
    assert source == "empty"


def test_an_http_date_is_reported_rather_than_crashed_on():
    seconds, source, _ = retry_after_seconds({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
    assert seconds == 30.0
    assert source == "unparseable"


def test_zero_waits_a_second_and_negative_falls_back():
    assert retry_after_seconds({"Retry-After": "0"}) [:2] == (1.0, "zero")
    assert retry_after_seconds({"Retry-After": "-5"})[:2] == (30.0, "negative")


def test_an_implausible_window_is_clamped_rather_than_obeyed():
    seconds, source, _ = retry_after_seconds({"Retry-After": "86400"})
    assert seconds == 600.0
    assert source == "clamped"


def test_both_shapes_of_the_same_event_reach_a_throttled_state():
    assert classify_response(429, {}, {})[0] == "throttled-429"
    assert classify_response(200, THROTTLED, {})[0] == "throttled-200"


def test_a_refusal_that_is_not_a_rate_limit_is_not_dressed_up_as_one():
    state, detail = classify_response(200, {"ok": False, "error": "not_in_channel"})
    assert state == "refused"
    assert "not a rate limit" in detail
    assert classify_response(200, {"ok": True})[0] == "ok"
    assert classify_response(502, {})[0] == "unreadable"


def test_honouring_the_header_is_the_only_clean_verdict():
    verdict, state, _ = replay_verdict({"method": "users.list", "status": 429,
                                        "body": {}, "headers": {"Retry-After": "30"},
                                        "waited": 30.2})
    assert verdict == "honoured"
    assert state == "throttled-429"


def test_retrying_inside_the_window_is_its_own_finding():
    verdict, _, detail = replay_verdict({"method": "conversations.history",
                                         "status": 200, "body": THROTTLED,
                                         "headers": {"Retry-After": "60"},
                                         "waited": 1.0})
    assert verdict == "retried-early"
    assert "has not reopened" in detail


def test_a_fixed_sleep_is_a_different_finding_from_an_early_retry():
    verdict, _, _ = replay_verdict({"method": "users.list", "status": 429,
                                    "body": {}, "headers": {"Retry-After": "3"},
                                    "waited": 60.0})
    assert verdict == "slept-blind"


def test_a_missing_wait_reads_as_a_client_that_never_got_that_far():
    verdict, _, _ = replay_verdict({"method": "users.list", "status": 429,
                                    "body": {}, "headers": {}, "waited": None})
    assert verdict == "no-wait-recorded"
    assert replay_verdict({"method": "u", "status": 429, "body": {},
                           "headers": {}, "waited": "soon"})[0] == "no-wait-recorded"


def test_a_successful_call_in_the_log_is_left_alone():
    verdict, _, _ = replay_verdict({"method": "auth.test", "status": 200,
                                    "body": {"ok": True}, "headers": {}, "waited": 0})
    assert verdict == "not-a-refusal"
''',
"test_js_file": "slack-retry-after-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classifyResponse, replayVerdict, retryAfterSeconds }
  from './slack-retry-after-audit.mjs';

const THROTTLED = { ok: false, error: 'ratelimited' };

test('a numeric header is the schedule', () => {
  const [seconds, source, detail] = retryAfterSeconds({ 'Retry-After': '12' });
  assert.equal(seconds, 12);
  assert.equal(source, 'header');
  assert.match(detail, /12/);
});

test('the header name is matched without regard to case', () => {
  assert.equal(retryAfterSeconds({ 'retry-after': '7' })[0], 7);
  assert.equal(retryAfterSeconds({ 'RETRY-AFTER': '7' })[0], 7);
  assert.equal(retryAfterSeconds({ ' Retry-After ': '7' })[0], 7);
});

test('an absent header returns a default that says it is a default', () => {
  const [seconds, source] = retryAfterSeconds({});
  assert.equal(seconds, 30);
  assert.equal(source, 'absent');
  assert.equal(retryAfterSeconds(null)[1], 'absent');
});

test('an empty header is not permission to retry now', () => {
  const [seconds, source] = retryAfterSeconds({ 'Retry-After': '  ' });
  assert.equal(seconds, 30);
  assert.equal(source, 'empty');
});

test('an http date is reported rather than thrown on', () => {
  const [seconds, source] =
    retryAfterSeconds({ 'Retry-After': 'Wed, 21 Oct 2026 07:28:00 GMT' });
  assert.equal(seconds, 30);
  assert.equal(source, 'unparseable');
});

test('zero waits a second and negative falls back', () => {
  assert.deepEqual(retryAfterSeconds({ 'Retry-After': '0' }).slice(0, 2), [1, 'zero']);
  assert.deepEqual(retryAfterSeconds({ 'Retry-After': '-5' }).slice(0, 2),
    [30, 'negative']);
});

test('an implausible window is clamped rather than obeyed', () => {
  const [seconds, source] = retryAfterSeconds({ 'Retry-After': '86400' });
  assert.equal(seconds, 600);
  assert.equal(source, 'clamped');
});

test('both shapes of the same event reach a throttled state', () => {
  assert.equal(classifyResponse(429, {}, {})[0], 'throttled-429');
  assert.equal(classifyResponse(200, THROTTLED, {})[0], 'throttled-200');
});

test('a refusal that is not a rate limit is not dressed up as one', () => {
  const [state, detail] = classifyResponse(200, { ok: false, error: 'not_in_channel' });
  assert.equal(state, 'refused');
  assert.match(detail, /not a rate limit/);
  assert.equal(classifyResponse(200, { ok: true })[0], 'ok');
  assert.equal(classifyResponse(502, {})[0], 'unreadable');
});

test('honouring the header is the only clean verdict', () => {
  const [verdict, state] = replayVerdict({
    method: 'users.list', status: 429, body: {},
    headers: { 'Retry-After': '30' }, waited: 30.2,
  });
  assert.equal(verdict, 'honoured');
  assert.equal(state, 'throttled-429');
});

test('retrying inside the window is its own finding', () => {
  const [verdict, , detail] = replayVerdict({
    method: 'conversations.history', status: 200, body: THROTTLED,
    headers: { 'Retry-After': '60' }, waited: 1,
  });
  assert.equal(verdict, 'retried-early');
  assert.match(detail, /has not reopened/);
});

test('a fixed sleep is a different finding from an early retry', () => {
  const [verdict] = replayVerdict({
    method: 'users.list', status: 429, body: {},
    headers: { 'Retry-After': '3' }, waited: 60,
  });
  assert.equal(verdict, 'slept-blind');
});

test('a missing wait reads as a client that never got that far', () => {
  assert.equal(replayVerdict({
    method: 'users.list', status: 429, body: {}, headers: {}, waited: null,
  })[0], 'no-wait-recorded');
  assert.equal(replayVerdict({
    method: 'u', status: 429, body: {}, headers: {}, waited: 'soon',
  })[0], 'no-wait-recorded');
});

test('a successful call in the log is left alone', () => {
  assert.equal(replayVerdict({
    method: 'auth.test', status: 200, body: { ok: true }, headers: {}, waited: 0,
  })[0], 'not-a-refusal');
});
''',
"faq": [
 ("Is Retry-After always present on a Slack rate-limit response?",
  "Usually, not always. Slack documents it and sends it on both the 429 and the HTTP 200 shape, but a client has to survive its absence: an empty value, a proxy that stripped it, or a response that never carried one. The rule this script encodes is that a missing header produces a documented default recorded as a default, never an exception and never an instant retry."),
 ("Should I use exponential backoff as well?",
  "Only as the fallback when there is no header. Exponential backoff is a guess at a number that has been given to you, and its usual failure is being too impatient for the first few attempts and too patient afterwards. Sleep for Retry-After, cap the number of attempts, and add a small amount of jitter so several processes do not all wake at once."),
 ("Why does the same event sometimes arrive as 429 and sometimes as HTTP 200?",
  "Slack answers almost everything with HTTP 200 and puts the failure in the body, and rate limiting is one of the few places it sometimes uses a real status code instead. Both shapes mean the identical thing. The practical consequence is that a client which only checks response.ok, or only checks status == 429, is handling half of them."),
 ("Can the script prove my backoff works by forcing a rate limit?",
  "It could, and it will not. Exhausting a window on purpose spends a real workspace's quota on a demonstration, and every other app in that workspace using the same method shares the consequence. The header is present on responses Slack already returns, and the log of past refusals is more evidence than a provoked one would be."),
 ("We use the official SDK. Is there anything left to check?",
  "The retry behaviour, yes: both official clients handle this correctly, and both let you configure it away. Check that the retry policy is actually enabled rather than set to none, and check any place your code calls fetch or requests directly instead of going through the client, because that is where the hand-rolled path usually survives."),
],
"related": [
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
 ("/slack/non-marketplace-history-clamp/", "when the throttle is the steady state"),
 ("/slack/parallel-workers-share-quota/", "who else is spending the same window"),
],
"citations": [CITE_RATE_LIMITS, CITE_RATE_CLARITY, CITE_WEB_API, CITE_AUTH_TEST],
},

{
"slug": "postmessage-one-per-second",
"title": "chat.postMessage is one per second, per channel",
"description": "Not a tier. chat.postMessage is roughly one message a second in one channel, so read the ts values of what you already sent and measure your own cadence.",
"h1": "chat.postMessage is one per second, per channel",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["chat.postMessage rate limit", "slack one message per second",
             "slack special tier rate limit", "slack bot message throttled",
             "slack chat.update streaming rate limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+; measuring the cadence needs channels:history",
"lead": "A fan-out job posts two hundred alerts. Around sixty land. The rest come back <code>ratelimited</code>, and the tier table does not explain it, because the number in the tier table is per minute and this failure happens in the first minute.</p><p><code>chat.postMessage</code> is not on a tier. It is on Slack's Special tier, which for this method means roughly one message per second in one channel, and the limit follows the channel rather than the method.",
"short_answer": """<p>The four numbered tiers &mdash; 1+, 20+, 50+ and 100+ requests a minute &mdash; do not apply to <code>chat.postMessage</code>. It sits on Special, at approximately <strong>one message per second per channel</strong>, with short bursts tolerated and a separate workspace-wide ceiling above that. <code>chat.update</code> lives in the same envelope, which is why streaming an assistant's reply token by token into a Slack message does not work at the rate people expect.</p>
<p>Because the limit is per channel, the two obvious remedies point in opposite directions. Parallelising the sender across channels helps. Parallelising it within one channel does nothing at all, and the limiter has to be keyed on the channel or it is not measuring the thing being limited.</p>
<p>A read-only script cannot post, so it measures the sender rather than the limit: read the recent history of a channel, keep the messages your own app wrote, and do arithmetic on their <code>ts</code> values. Three messages inside one second is not a prediction of throttling. It is a recording of it, from a send path that was lucky.</p>""",
"problem": """<p>Everything about this limit is shaped to be found late. It is not in the tier table, so a developer who reads the rate-limit page carefully still comes away with the wrong number. It tolerates bursts, so the first sixty messages of a fan-out succeed and the failure looks like it started partway through rather than being present from the start. And it is per channel, so a load test that posts to eight channels at once passes, and production, which posts to one, does not.</p>
<p>The streaming case is worse because it looks like a completely different problem. An assistant generates a reply and the natural implementation edits one message repeatedly as tokens arrive. <code>chat.update</code> is in the same one-per-second envelope, so the update loop throttles after a second or two, the reply stutters, and the bug gets filed against the model latency or the socket rather than against a posting limit nobody knew applied to edits.</p>
<p>The reason this note is a read-only detection at all is that the honest test would be to post and see. That is the one experiment this section will not run: sending two hundred messages into a real channel to confirm that sending two hundred messages into a real channel is a bad idea is not a diagnostic, it is the incident. The timestamps of what your app already sent contain the same information, and they are free.</p>""",
"why": """<p><strong>The limit is per channel, so the fix is a per-channel key.</strong> A global token bucket in front of the sender is the usual first attempt, and it throttles the whole app to protect one channel while doing nothing to stop a burst into that channel from two processes. The bucket has to be keyed on the channel ID.</p>
<p><strong>Bursts are tolerated, which hides the steady state.</strong> Slack allows short bursts above one per second, so a small test always passes. The number that matters is the sustained rate, and the only way to see it is over a run long enough for the burst allowance to be spent.</p>
<p><strong>A message is not the unit anybody actually needs.</strong> Most fan-outs send N messages because N things happened, not because N messages were required. One message carrying up to fifty blocks delivers the same information in one request, reads better in the channel, and does not race anything. The block ceiling is a much larger budget than the one-per-second one.</p>
<p><strong><code>chat.update</code> is in the envelope too.</strong> Anything that treats editing as cheaper than posting is wrong here. Streaming works when the update cadence is fixed at one or two seconds and the text is coarser, and does not work at token granularity, at any level of cleverness.</p>
<p><strong>The timestamps are evidence, not a model.</strong> <code>ts</code> is a Unix time with microseconds, assigned by Slack. Two of your app's messages 0.2 seconds apart is not a simulation of a burst; it is a burst that already happened and was allowed through on the burst allowance. That is what makes this detectable without sending anything.</p>""",
"steps": [
 {"h": "Get the app's own identity before reading anybody's history",
  "body": """<p>One <code>auth.test</code> returns the bot user ID and the <code>bot_id</code>. Without it the history is just messages; with it, some of them are yours. If you also know the app ID, pass it: history items carry <code>app_id</code> and a <code>bot_profile</code>, and matching on it catches messages sent by other tokens of the same app.</p>"""},
 {"h": "Read one page of history, on purpose",
  "body": """<p>One <code>conversations.history</code> call per channel. This is a question about the recent shape of your sending, not about the archive, so there is no cursor to follow and no reason to page. If the page is mostly other people's messages, the sample of your own is small, and the script says so instead of ruling on four timestamps.</p>"""},
 {"h": "Keep only the messages this app wrote",
  "body": """<p>Match on <code>bot_id</code> first, then <code>app_id</code>, then the <code>bot_profile</code> block, then the bot's own user ID. Everything else in the channel is somebody else's cadence and including it turns a busy channel into a finding.</p>"""},
 {"h": "Measure the peak second, not the average",
  "body": """<p>An average rate over a hundred messages hides the burst completely: an app that sends five messages in one second and nothing for an hour averages almost nothing. Slide a one second window across your timestamps and keep the maximum. That number is the one the limit compares against.</p>"""},
 {"h": "Cost the batch before proposing it",
  "body": """<p>The script converts the finding into the repair with arithmetic the reader can check: two hundred alerts at one per second is over three minutes of queue, and the same alerts at two blocks each collapse into eight messages and seven seconds. That is a bigger change than a limiter and it is usually less work.</p>"""},
 {"h": "Key the limiter on the channel and queue rather than drop",
  "body": """<p>One token bucket per channel ID, refilling at one per second, with the sender blocking rather than discarding. Parallelise across channels if throughput matters. For streaming edits, update on a fixed one to two second cadence and accept the coarser granularity, because there is no configuration that makes per-token editing work.</p>"""},
],
"verify": """<p>Re-run after the batching change. The peak second should fall to one, and the app's messages should be fewer and larger.</p>
<pre><code class="language-bash">python3 slack_send_cadence.py C0ALERTS99
# identity  U0APPBOT11 bot B0APPBOT99 in acme
# C0ALERTS99  sample   9 message(s) from this app in the last 200
# C0ALERTS99  paced    peak of 1 message(s) in any one second window
# batching    200 alert(s) at 2 block(s) each fit in 8 message(s), 7s instead of 199s
# 1 channel(s) checked, 0 sending faster than one per second</code></pre>""",
"code_intro": "Four pure functions and two GET methods. <code>app_messages</code> is a positive filter rather than a subtype blocklist: it keeps what this app wrote and ignores everything else, so a busy channel cannot be mistaken for a busy sender. <code>peak_per_second</code> slides a one second window instead of averaging, because the average is the number that hides this. <code>batch_plan</code> exists so the repair arrives as arithmetic rather than as advice.",
"py_file": "slack_send_cadence.py",
"py": '''"""Measure how fast this app has been posting into one Slack channel.

Read only. chat.postMessage is on Slack's Special tier at roughly one message
per second per channel, and the honest way to test that would be to send two
hundred messages, which is the incident rather than the diagnostic. So this
reads one page of history instead, keeps the messages this app already wrote,
and does arithmetic on their ts values. A burst in the record is a burst that
happened and was allowed through on the burst allowance.
"""
import argparse
import logging
import math
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_send_cadence")

API = "https://slack.com/api/"

# The documented envelope for chat.postMessage and chat.update: about one
# message per second in one channel, bursts tolerated above it.
WINDOW = 1.0

# Fewer of this app's messages than this on the page and the sample is too thin
# to rule on. Saying so is more useful than a verdict drawn from three points.
MIN_SAMPLE = 5

# Block Kit's per-message ceiling. The budget that is not scarce here.
BLOCK_CEILING = 50


def parse_ts(value):
    """A Slack ts as a float, or None. Pure.

    ts is a Unix time with microseconds, delivered as a string, and it is also
    a message's identity, so it turns up in configuration and in stored thread
    anchors where it may have been mangled. Anything that is not a positive
    number is dropped rather than defaulted to now.
    """
    try:
        seconds = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(seconds) or seconds <= 0:
        return None
    return seconds


def app_messages(messages, identity):
    """The messages on this page that this app wrote. Pure.

    A positive filter, not a subtype blocklist. Everything else in the channel
    is somebody else's cadence, and counting it turns a busy channel into a
    finding about a sender that posted twice all week.

    Returns [(ts, matched_on), ...] in the order Slack returned them.
    """
    bot_id = str((identity or {}).get("bot_id") or "").strip()
    app_id = str((identity or {}).get("app_id") or "").strip()
    user_id = str((identity or {}).get("user_id") or "").strip()

    out = []
    for message in messages or []:
        matched = ""
        profile = message.get("bot_profile") or {}
        if bot_id and str(message.get("bot_id") or "") == bot_id:
            matched = "bot_id"
        elif app_id and str(message.get("app_id") or "") == app_id:
            matched = "app_id"
        elif app_id and str(profile.get("app_id") or "") == app_id:
            matched = "bot_profile"
        elif user_id and str(message.get("user") or "") == user_id:
            matched = "user_id"
        if not matched:
            continue
        stamp = parse_ts(message.get("ts"))
        if stamp is not None:
            out.append((stamp, matched))
    return out


def peak_per_second(stamps, window=WINDOW):
    """The most messages this sender put into any one window. Pure.

    An average hides this completely: five messages in one second and silence
    for an hour averages to nothing at all, and the limit compares against the
    peak. Sliding window, so a burst spanning a second boundary still counts.
    """
    ordered = sorted(s for s in stamps if s is not None)
    best, start = 0, 0
    for end in range(len(ordered)):
        while ordered[end] - ordered[start] >= window:
            start += 1
        best = max(best, end - start + 1)
    return best


def cadence_verdict(stamps, window=WINDOW, min_sample=MIN_SAMPLE):
    """Rule on one channel's send cadence. Pure. Returns (verdict, peak, detail)."""
    ordered = sorted(s for s in stamps if s is not None)
    if len(ordered) < min_sample:
        return ("no-sample", len(ordered),
                "only %d message(s) from this app on the page. That is too few to "
                "say anything about cadence, and a verdict drawn from it would be "
                "noise wearing a label." % len(ordered))

    peak = peak_per_second(ordered, window)
    span = ordered[-1] - ordered[0]
    if peak >= 3:
        return ("will-throttle", peak,
                "%d message(s) inside one second. This sender is already past the "
                "one per second envelope and is being carried by the burst "
                "allowance; a longer run in the same channel will be refused."
                % peak)
    if peak == 2:
        return ("at-the-edge", peak,
                "two messages inside one second, over a span of %.0fs. That is the "
                "top of the envelope. It survives today and will not survive a "
                "fan-out twice this size." % span)
    return ("paced", peak,
            "peak of %d message(s) in any one second window over %.0fs. Nothing "
            "here is racing the limit." % (peak, span))


def batch_plan(alerts, blocks_per_alert=2, ceiling=BLOCK_CEILING):
    """What N separate alerts cost, and what they cost batched. Pure.

    Returns (messages, seconds_now, seconds_batched). The block ceiling is a far
    larger budget than the one per second one, which is the whole argument: most
    fan-outs send N messages because N things happened, not because N messages
    were needed.
    """
    alerts = max(0, int(alerts))
    per_message = max(1, int(ceiling) // max(1, int(blocks_per_alert)))
    messages = -(-alerts // per_message) if alerts else 0
    return (messages, float(max(0, alerts - 1)), float(max(0, messages - 1)))


def identify(session):
    """The app's own identity. GET only."""
    body = session.get(API + "auth.test", timeout=30).json()
    if body.get("ok") is not True:
        raise SystemExit("auth.test answered 200 with ok: false, error=%s"
                         % body.get("error"))
    return body


def one_page(session, channel, limit):
    """One page of history. GET only, and one page on purpose: this is a
    question about the recent shape of the sending, not about the archive."""
    body = session.get(API + "conversations.history",
                       params={"channel": channel, "limit": limit},
                       timeout=30).json()
    if body.get("ok") is not True:
        log.error("%s conversations.history answered ok: false, error=%s",
                  channel, body.get("error"))
        return []
    return body.get("messages") or []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("channels", nargs="+", help="channel IDs this app posts into")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--app-id", default="",
                    help="the app ID, if you know it; catches messages sent by "
                         "other tokens of the same app")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages to read per channel, one page only")
    ap.add_argument("--alerts", type=int, default=0,
                    help="size of a fan-out to cost against the batching plan")
    ap.add_argument("--blocks-per-alert", type=int, default=2,
                    help="blocks one alert occupies when batched")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history is what the measurement needs)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    identity = identify(s)
    if args.app_id:
        identity = dict(identity, app_id=args.app_id)
    log.info("identity  %s bot %s in %s", identity.get("user_id"),
             identity.get("bot_id"), identity.get("team"))
    if not args.app_id:
        log.info("no --app-id given, so messages sent by other tokens of this app "
                 "will not be matched and the sample may be smaller than the truth")

    hot = 0
    for channel in args.channels:
        page = one_page(s, channel, args.limit)
        mine = app_messages(page, identity)
        log.info("%-12s sample   %d message(s) from this app in the last %d",
                 channel, len(mine), len(page))

        verdict, peak, detail = cadence_verdict([ts for ts, _ in mine])
        if verdict in ("paced", "no-sample"):
            log.info("%-12s %-14s %s", channel, verdict, detail)
            continue

        hot += 1
        log.warning("%-12s %-14s %s", channel, verdict, detail)
        log.warning("  repair: one token bucket per channel ID at one per second, "
                    "and the sender queues rather than drops")
        log.warning("  repair: parallelise across channels if throughput matters. "
                    "Parallelising inside this one changes nothing, because the "
                    "limit follows the channel")
        log.warning("  note: chat.update shares this envelope, so editing one "
                    "message per token is refused for the same reason")

    if args.alerts:
        messages, before, after = batch_plan(args.alerts, args.blocks_per_alert)
        log.info("batching  %d alert(s) at %d block(s) each fit in %d message(s), "
                 "%.0fs instead of %.0fs", args.alerts, args.blocks_per_alert,
                 messages, after, before)

    log.info("%d channel(s) checked, %d sending faster than one per second",
             len(args.channels), hot)
    return 1 if hot else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-send-cadence.mjs",
"js": '''/**
 * Measure how fast this app has been posting into one Slack channel.
 *
 * Read only. chat.postMessage is on Slack's Special tier at roughly one message
 * per second per channel, and the honest way to test that would be to send two
 * hundred messages, which is the incident rather than the diagnostic. So this
 * reads one page of history instead, keeps the messages this app already wrote,
 * and does arithmetic on their ts values.
 */

const API = 'https://slack.com/api/';

const WINDOW = 1.0;
const MIN_SAMPLE = 5;
const BLOCK_CEILING = 50;

/**
 * A Slack ts as a number, or null. Pure.
 * Anything that is not a positive finite number is dropped rather than
 * defaulted to now.
 */
export function parseTs(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const seconds = Number(text);
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  return seconds;
}

/**
 * The messages on this page that this app wrote. Pure.
 * A positive filter, not a subtype blocklist: everything else in the channel is
 * somebody else's cadence. Returns [[ts, matchedOn], ...].
 */
export function appMessages(messages, identity) {
  const botId = String(identity?.bot_id ?? '').trim();
  const appId = String(identity?.app_id ?? '').trim();
  const userId = String(identity?.user_id ?? '').trim();

  const out = [];
  for (const message of messages ?? []) {
    const profile = message.bot_profile ?? {};
    let matched = '';
    if (botId && String(message.bot_id ?? '') === botId) matched = 'bot_id';
    else if (appId && String(message.app_id ?? '') === appId) matched = 'app_id';
    else if (appId && String(profile.app_id ?? '') === appId) matched = 'bot_profile';
    else if (userId && String(message.user ?? '') === userId) matched = 'user_id';
    if (!matched) continue;
    const stamp = parseTs(message.ts);
    if (stamp !== null) out.push([stamp, matched]);
  }
  return out;
}

/**
 * The most messages this sender put into any one window. Pure.
 * An average hides this completely, and the limit compares against the peak.
 */
export function peakPerSecond(stamps, window = WINDOW) {
  const ordered = stamps.filter((s) => s !== null && s !== undefined)
    .slice().sort((a, b) => a - b);
  let best = 0;
  let start = 0;
  for (let end = 0; end < ordered.length; end += 1) {
    while (ordered[end] - ordered[start] >= window) start += 1;
    best = Math.max(best, end - start + 1);
  }
  return best;
}

/** Rule on one channel's send cadence. Pure. Returns [verdict, peak, detail]. */
export function cadenceVerdict(stamps, window = WINDOW, minSample = MIN_SAMPLE) {
  const ordered = stamps.filter((s) => s !== null && s !== undefined)
    .slice().sort((a, b) => a - b);
  if (ordered.length < minSample) {
    return ['no-sample', ordered.length,
      `only ${ordered.length} message(s) from this app on the page. That is too ` +
      'few to say anything about cadence, and a verdict drawn from it would be ' +
      'noise wearing a label.'];
  }

  const peak = peakPerSecond(ordered, window);
  const span = ordered[ordered.length - 1] - ordered[0];
  if (peak >= 3) {
    return ['will-throttle', peak,
      `${peak} message(s) inside one second. This sender is already past the one ` +
      'per second envelope and is being carried by the burst allowance; a longer ' +
      'run in the same channel will be refused.'];
  }
  if (peak === 2) {
    return ['at-the-edge', peak,
      `two messages inside one second, over a span of ${span.toFixed(0)}s. That ` +
      'is the top of the envelope. It survives today and will not survive a ' +
      'fan-out twice this size.'];
  }
  return ['paced', peak,
    `peak of ${peak} message(s) in any one second window over ${span.toFixed(0)}s. ` +
    'Nothing here is racing the limit.'];
}

/**
 * What N separate alerts cost, and what they cost batched. Pure.
 * Returns [messages, secondsNow, secondsBatched].
 */
export function batchPlan(alerts, blocksPerAlert = 2, ceiling = BLOCK_CEILING) {
  const count = Math.max(0, Math.trunc(Number(alerts) || 0));
  const perMessage = Math.max(1, Math.trunc(ceiling / Math.max(1, blocksPerAlert)));
  const messages = count ? Math.ceil(count / perMessage) : 0;
  return [messages, Math.max(0, count - 1), Math.max(0, messages - 1)];
}

async function call(token, method, params) {
  const qs = new URLSearchParams(params);
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

/** One page of history. GET only, and one page on purpose. */
async function onePage(token, channel, limit) {
  const body = await call(token, 'conversations.history',
    { channel, limit: String(limit) });
  if (body.ok !== true) {
    console.error(`${channel} conversations.history answered ok: false, ` +
      `error=${body.error}`);
    return [];
  }
  return body.messages ?? [];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function positionals(args) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i].startsWith('--')) { i += 1; continue; }
    out.push(args[i]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const channels = positionals(args);
  if (channels.length === 0) {
    console.error('usage: <channel id>... [--token-env SLACK_BOT_TOKEN] ' +
      '[--app-id A0...] [--limit 200] [--alerts 200] [--blocks-per-alert 2]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history is what the measurement needs)`);
    process.exitCode = 2;
    return;
  }

  const appId = arg(args, '--app-id', '');
  const limit = Number(arg(args, '--limit', 200));
  const alerts = Number(arg(args, '--alerts', 0));
  const blocksPerAlert = Number(arg(args, '--blocks-per-alert', 2));

  const auth = await call(token, 'auth.test', {});
  if (auth.ok !== true) {
    console.error(`auth.test answered 200 with ok: false, error=${auth.error}`);
    process.exitCode = 2;
    return;
  }
  const identity = appId ? { ...auth, app_id: appId } : auth;
  console.log(`identity  ${identity.user_id} bot ${identity.bot_id} in ${identity.team}`);
  if (!appId) {
    console.log('no --app-id given, so messages sent by other tokens of this app ' +
      'will not be matched and the sample may be smaller than the truth');
  }

  let hot = 0;
  for (const channel of channels) {
    const page = await onePage(token, channel, limit);
    const mine = appMessages(page, identity);
    console.log(`${channel.padEnd(12)} sample   ${mine.length} message(s) from ` +
      `this app in the last ${page.length}`);

    const [verdict, , detail] = cadenceVerdict(mine.map(([ts]) => ts));
    if (verdict === 'paced' || verdict === 'no-sample') {
      console.log(`${channel.padEnd(12)} ${verdict.padEnd(14)} ${detail}`);
      continue;
    }

    hot += 1;
    console.warn(`${channel.padEnd(12)} ${verdict.padEnd(14)} ${detail}`);
    console.warn('  repair: one token bucket per channel ID at one per second, and ' +
      'the sender queues rather than drops');
    console.warn('  repair: parallelise across channels if throughput matters. ' +
      'Parallelising inside this one changes nothing, because the limit follows ' +
      'the channel');
    console.warn('  note: chat.update shares this envelope, so editing one message ' +
      'per token is refused for the same reason');
  }

  if (alerts) {
    const [messages, before, after] = batchPlan(alerts, blocksPerAlert);
    console.log(`batching  ${alerts} alert(s) at ${blocksPerAlert} block(s) each ` +
      `fit in ${messages} message(s), ${after}s instead of ${before}s`);
  }

  console.log(`${channels.length} channel(s) checked, ${hot} sending faster than ` +
    'one per second');
  process.exitCode = hot ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixture is one page of history with three senders in it: this app, a colleague, and another app entirely. The tests pin that only the first is counted, that a <code>bot_profile</code> match catches a message sent by a second token of the same app, and that <code>peak_per_second</code> finds a burst that straddles a second boundary &mdash; the case a naive grouping by whole second misses. The batching arithmetic is pinned to an exact number so the repair in the report can be checked rather than believed.",
"test_py_file": "test_slack_send_cadence.py",
"test_py": '''from slack_send_cadence import (app_messages, batch_plan, cadence_verdict,
                                  parse_ts, peak_per_second)

ME = {"user_id": "U0APPBOT11", "bot_id": "B0APPBOT99", "app_id": "A0APPBOT77"}

PAGE = [
    {"ts": "1770000000.000100", "bot_id": "B0APPBOT99", "text": "alert 1"},
    {"ts": "1770000000.400100", "bot_id": "B0APPBOT99", "text": "alert 2"},
    {"ts": "1770000000.800100", "bot_id": "B0APPBOT99", "text": "alert 3"},
    {"ts": "1770000004.000100", "user": "U0HUMAN123", "text": "what happened"},
    {"ts": "1770000004.100100", "bot_id": "B0OTHERBOT", "text": "unrelated bot"},
]


def test_a_ts_is_a_float_and_nonsense_is_dropped():
    assert parse_ts("1770000000.000100") == 1770000000.0001
    assert parse_ts(" 1770000000.5 ") == 1770000000.5
    assert parse_ts("") is None
    assert parse_ts(None) is None
    assert parse_ts("p1770000000.000100") is None
    assert parse_ts("-1") is None


def test_only_this_apps_messages_are_counted():
    mine = app_messages(PAGE, ME)
    assert [how for _, how in mine] == ["bot_id", "bot_id", "bot_id"]


def test_a_second_token_of_the_same_app_is_matched_through_bot_profile():
    page = PAGE + [{"ts": "1770000009.000100", "bot_id": "B0SECOND11",
                    "bot_profile": {"app_id": "A0APPBOT77"}}]
    assert app_messages(page, ME)[-1][1] == "bot_profile"


def test_without_an_app_id_the_second_token_is_invisible():
    page = PAGE + [{"ts": "1770000009.000100", "bot_id": "B0SECOND11",
                    "bot_profile": {"app_id": "A0APPBOT77"}}]
    identity = {"user_id": "U0APPBOT11", "bot_id": "B0APPBOT99"}
    assert len(app_messages(page, identity)) == 3


def test_a_burst_straddling_a_second_boundary_is_still_a_burst():
    # Grouping by whole second would file these as one and two.
    stamps = [1770000000.9, 1770000001.1, 1770000001.4]
    assert peak_per_second(stamps) == 3


def test_an_idle_sender_peaks_at_one():
    assert peak_per_second([1770000000.0, 1770000060.0, 1770000120.0]) == 1
    assert peak_per_second([]) == 0


def test_three_in_a_second_is_the_headline_verdict():
    stamps = [1770000000.0, 1770000000.3, 1770000000.6, 1770000000.9, 1770000010.0]
    verdict, peak, detail = cadence_verdict(stamps)
    assert verdict == "will-throttle"
    assert peak == 4
    assert "burst allowance" in detail


def test_two_in_a_second_is_the_edge_rather_than_a_failure():
    stamps = [1770000000.0, 1770000000.5, 1770000030.0, 1770000060.0, 1770000090.0]
    verdict, peak, _ = cadence_verdict(stamps)
    assert verdict == "at-the-edge"
    assert peak == 2


def test_a_paced_sender_is_cleared():
    stamps = [1770000000.0 + i * 5 for i in range(8)]
    assert cadence_verdict(stamps)[0] == "paced"


def test_a_thin_sample_produces_no_verdict_at_all():
    verdict, count, detail = cadence_verdict([1770000000.0, 1770000000.1])
    assert verdict == "no-sample"
    assert count == 2
    assert "too few" in detail


def test_batching_turns_two_hundred_alerts_into_eight_messages():
    messages, before, after = batch_plan(200, 2)
    assert messages == 8
    assert before == 199.0
    assert after == 7.0


def test_batching_degrades_sensibly_at_the_edges():
    assert batch_plan(0) == (0, 0.0, 0.0)
    assert batch_plan(1)[0] == 1
    # A fat alert that eats the whole block budget cannot be batched at all.
    assert batch_plan(9, 50) == (9, 8.0, 8.0)
''',
"test_js_file": "slack-send-cadence.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { appMessages, batchPlan, cadenceVerdict, parseTs, peakPerSecond }
  from './slack-send-cadence.mjs';

const ME = { user_id: 'U0APPBOT11', bot_id: 'B0APPBOT99', app_id: 'A0APPBOT77' };

const PAGE = [
  { ts: '1770000000.000100', bot_id: 'B0APPBOT99', text: 'alert 1' },
  { ts: '1770000000.400100', bot_id: 'B0APPBOT99', text: 'alert 2' },
  { ts: '1770000000.800100', bot_id: 'B0APPBOT99', text: 'alert 3' },
  { ts: '1770000004.000100', user: 'U0HUMAN123', text: 'what happened' },
  { ts: '1770000004.100100', bot_id: 'B0OTHERBOT', text: 'unrelated bot' },
];

test('a ts is a number and nonsense is dropped', () => {
  assert.equal(parseTs('1770000000.000100'), 1770000000.0001);
  assert.equal(parseTs(' 1770000000.5 '), 1770000000.5);
  assert.equal(parseTs(''), null);
  assert.equal(parseTs(null), null);
  assert.equal(parseTs('p1770000000.000100'), null);
  assert.equal(parseTs('-1'), null);
});

test('only this apps messages are counted', () => {
  assert.deepEqual(appMessages(PAGE, ME).map(([, how]) => how),
    ['bot_id', 'bot_id', 'bot_id']);
});

test('a second token of the same app is matched through bot_profile', () => {
  const page = [...PAGE, {
    ts: '1770000009.000100', bot_id: 'B0SECOND11',
    bot_profile: { app_id: 'A0APPBOT77' },
  }];
  assert.equal(appMessages(page, ME).at(-1)[1], 'bot_profile');
});

test('without an app id the second token is invisible', () => {
  const page = [...PAGE, {
    ts: '1770000009.000100', bot_id: 'B0SECOND11',
    bot_profile: { app_id: 'A0APPBOT77' },
  }];
  assert.equal(appMessages(page, { user_id: 'U0APPBOT11', bot_id: 'B0APPBOT99' }).length, 3);
});

test('a burst straddling a second boundary is still a burst', () => {
  assert.equal(peakPerSecond([1770000000.9, 1770000001.1, 1770000001.4]), 3);
});

test('an idle sender peaks at one', () => {
  assert.equal(peakPerSecond([1770000000, 1770000060, 1770000120]), 1);
  assert.equal(peakPerSecond([]), 0);
});

test('three in a second is the headline verdict', () => {
  const stamps = [1770000000, 1770000000.3, 1770000000.6, 1770000000.9, 1770000010];
  const [verdict, peak, detail] = cadenceVerdict(stamps);
  assert.equal(verdict, 'will-throttle');
  assert.equal(peak, 4);
  assert.match(detail, /burst allowance/);
});

test('two in a second is the edge rather than a failure', () => {
  const stamps = [1770000000, 1770000000.5, 1770000030, 1770000060, 1770000090];
  const [verdict, peak] = cadenceVerdict(stamps);
  assert.equal(verdict, 'at-the-edge');
  assert.equal(peak, 2);
});

test('a paced sender is cleared', () => {
  const stamps = Array.from({ length: 8 }, (_, i) => 1770000000 + i * 5);
  assert.equal(cadenceVerdict(stamps)[0], 'paced');
});

test('a thin sample produces no verdict at all', () => {
  const [verdict, count, detail] = cadenceVerdict([1770000000, 1770000000.1]);
  assert.equal(verdict, 'no-sample');
  assert.equal(count, 2);
  assert.match(detail, /too few/);
});

test('batching turns two hundred alerts into eight messages', () => {
  assert.deepEqual(batchPlan(200, 2), [8, 199, 7]);
});

test('batching degrades sensibly at the edges', () => {
  assert.deepEqual(batchPlan(0), [0, 0, 0]);
  assert.equal(batchPlan(1)[0], 1);
  assert.deepEqual(batchPlan(9, 50), [9, 8, 8]);
});
''',
"faq": [
 ("Is chat.postMessage on Tier 3 or Tier 4?",
  "Neither. It is on the Special tier, which is where Slack puts methods whose limit does not fit the four-number table. For chat.postMessage that limit is approximately one message per second in one channel, with short bursts tolerated and a separate workspace-wide ceiling above it. Reading a tier number off the general rate-limit page and applying it here is the most common way to get this wrong."),
 ("Does adding more workers make the fan-out faster?",
  "Not into one channel. The limit follows the channel, so eight workers posting into #alerts share the same one-per-second envelope and simply spend their time backing off. Across eight different channels they genuinely parallelise. That asymmetry is why the limiter has to be keyed on the channel ID rather than on the process or the method."),
 ("Can I stream an assistant reply token by token with chat.update?",
  "No, and no configuration changes that. chat.update sits in the same envelope as chat.postMessage, so an update per token throttles within a second or two. What works is a fixed cadence of one to two seconds, buffering the tokens in between, and accepting that the reply appears in chunks rather than letters."),
 ("Why measure timestamps instead of just posting a test burst?",
  "Because a test burst into a real channel is the failure it is meant to detect, delivered to real people, and because deliberately spending a workspace's quota affects every other app using the same method. The ts values of the messages your app already sent record exactly the same cadence, and the burst they show already happened."),
 ("The script says no-sample. What now?",
  "Point it at a channel your app actually posts into, and raise --limit. Below five of your own messages on the page there is nothing to measure, and the script refuses rather than ruling on three points. If the app posts rarely everywhere, this is not your problem: a sender that posts twice an hour cannot exceed one per second."),
],
"related": [
 ("/slack/ratelimited-retry-after-ignored/", "what to do with the refusal when it comes"),
 ("/slack/duplicate-messages-no-dedupe/", "the same message posted three times"),
 ("/slack/bot-not-in-channel/", "not_in_channel: the bot was never invited"),
],
"citations": [CITE_POSTMESSAGE, CITE_CHAT_UPDATE, CITE_RATE_LIMITS, CITE_CONV_HISTORY],
},

{
"slug": "tier1-method-hammered",
"title": "A Tier 1 method polled as if it were cheap",
"description": "One call throttles while everything else is fine. Slack's tiers are per method, so check the interval against the documented tier before you add backoff.",
"h1": "A Tier 1 method polled as if it were cheap",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack tier 1 rate limit", "slack method rate limit tiers",
             "slack api polling rate limit", "slack tier 2 20 per minute",
             "slack rate limit per method"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the audit reads a schedule you write down",
"lead": "One call throttles. Not the app &mdash; one method, over and over, while everything around it is perfectly healthy. Adding backoff makes the loop slower and does not make it work, because the loop is asking for more than the method has ever been allowed to give.</p><p>Slack's limits are per method. There are four tiers and the bottom one allows about one request a minute, which is a number nobody discovers by reading and everybody discovers by polling.",
"short_answer": """<p>Slack assigns each Web API method to a tier: Tier 1 at 1+ request per minute, Tier 2 at 20+, Tier 3 at 50+, Tier 4 at 100+, plus a Special tier for methods whose limit does not fit that shape. Tier 1 is where the expensive, rarely-needed operations live, and it has almost no burst allowance. A cron that runs every thirty seconds against a Tier 1 method is asking for double its entire budget, forever.</p>
<p>The finding is arithmetic and it does not need the API: sixty divided by your polling interval, against the tier printed on the method's reference page. The script below carries a small seeded table of tiers it is confident about, takes the ones it does not know from a schedule you write down, and refuses to guess for the rest. For each offender it prints the substitute &mdash; the event to subscribe to, or the cache with the long TTL &mdash; because a method on Tier 1 is Slack saying this is not something you poll.</p>
<p>The one thing it will not do is find the tier by calling until something breaks.</p>""",
"problem": """<p>The tier is documented, on the method's own reference page, in a line most people never read because they arrived at the page looking for the parameters. So the tier gets discovered at runtime instead, and it gets discovered in the most confusing possible way: as a partial failure. Because limits are per method, a Tier 1 method inside an otherwise well-behaved app produces one endpoint that throttles constantly while every other call in the same process succeeds. That does not look like a rate limit. It looks like a broken endpoint.</p>
<p>The response is usually backoff, and backoff is the wrong shape of fix. Backoff makes a temporary overshoot recover; it does not make a permanent one go away. A loop that wants 2 requests a minute from a budget of 1 will spend half its life sleeping no matter how elegantly the sleeping is arranged, and the job's real throughput is fixed at the tier whatever the client does.</p>
<p>What makes it worse is that the polling interval is almost never a considered decision. It is thirty seconds because thirty seconds felt responsive, or because the scheduler's smallest useful unit is a minute and somebody halved it. Nobody chose it against a budget, because nobody knew there was one. So the audit is not really about rate limits at all: it is about writing down every interval in the system next to the number it is spending, which is a thing most integrations have never had on one page.</p>""",
"why": """<p><strong>The tier is a design statement, not a speed bump.</strong> Slack put a method on Tier 1 because it is expensive to compute across a workspace. The tier is telling you the method was never intended to be the data path for anything that refreshes. Backing off politely still misses the point.</p>
<p><strong>Per-method limits produce partial failures, which mislead.</strong> Everything else works, so the investigation starts at the endpoint and not at the app's traffic. The first useful question is not "why is this call failing" but "what tier is this call on, and how often do we make it".</p>
<p><strong>The arithmetic is offline and the API cannot improve on it.</strong> Sixty over the interval, against the documented tier. There is no method that reports your remaining budget &mdash; rate-limit posture is inferred from headers on live calls and never queried &mdash; so calling more is not a way to learn more.</p>
<p><strong>A tier this audit does not know is reported as unknown.</strong> The seeded table is small on purpose and the tiers do change. An unknown method gets a link to the reference page and a request for the number, rather than a plausible guess that would be quoted back in a design review a year from now.</p>
<p><strong>The repair is a different architecture, and it is usually smaller than it sounds.</strong> Most Tier 1 and Tier 2 polling exists to notice a change. Slack emits an event for nearly every change worth noticing, and a cached answer refreshed by an event is both cheaper and fresher than a poll. The substitution table in the script is the actual deliverable.</p>""",
"steps": [
 {"h": "Write the schedule down before you look at any code",
  "body": """<p>Every place the app calls Slack on a timer: the method, the interval, and how many calls one run makes. Cron entries, scheduler jobs, the loop in the worker, the health check. This is the artifact most integrations have never produced, and half the findings appear while writing it.</p>"""},
 {"h": "Put the documented tier next to each method",
  "body": """<p>The tier is on the method's reference page. The script seeds the ones it is confident about and takes the rest from your schedule file. Where it does not know, it says so and asks for the number rather than inventing one.</p>"""},
 {"h": "Do the division",
  "body": """<p>Sixty divided by the interval, times the calls per run, against the tier's floor. A method on Tier 1 polled every thirty seconds is at two hundred percent of its budget. A method on Tier 4 polled every second is at sixty percent of its. The same interval is fine in one place and impossible in the other, which is the whole reason the tier has to be in the table.</p>"""},
 {"h": "Do not probe to find out",
  "body": """<p>The script will call a method once, if you ask it to and if the method is on its allowlist of reads, purely to confirm the token can reach it. It will not call a method it cannot prove is a read, and it will never loop. Finding a limit by exhausting it spends a real workspace's window on a demonstration, and every other app on that method shares the bill.</p>"""},
 {"h": "Replace the worst offender with an event",
  "body": """<p>Each entry in the table comes with its substitute. Polling <code>users.list</code> to notice a profile change is what <code>user_change</code> exists for. Polling <code>conversations.list</code> to notice a new channel is <code>channel_created</code>. The poll becomes a cold-start backfill and a nightly reconciliation, which together cost less in a day than the loop cost in a minute.</p>"""},
 {"h": "Keep the schedule file in the repository",
  "body": """<p>It is a small JSON file and it is the only place the system's total demand on Slack is written down. Re-run the audit in CI when it changes, and a new poll added at a plausible-looking interval fails the build instead of failing at three in the morning.</p>"""},
],
"verify": """<p>Re-run after the interval changes and the substitutions land. Every line should be within budget, and the tiers the audit does not know should have been filled in.</p>
<pre><code class="language-bash">python3 slack_method_tier_budget.py --schedule slack_schedule.json
# identity   U0APPBOT11 in acme
# conversations.list     within-budget   2.0/min against a tier 2 floor of 20/min
# users.list             within-budget   0.5/min against a tier 2 floor of 20/min
# conversations.members  within-budget   12.0/min against a tier 4 floor of 100/min
# 3 entry(s) checked, 0 over budget, 0 with an unknown tier</code></pre>""",
"code_intro": "Three pure functions, one small table and one GET method. <code>tier_of</code> is deliberately incomplete and says so: it returns a source alongside the tier, and <code>unknown</code> is a first-class answer rather than a fallback to something plausible. <code>budget_verdict</code> is the division. <code>substitute</code> is the part worth keeping &mdash; the event or the cache that replaces each poll &mdash; because on Tier 1 the repair is never a shorter sleep.",
"py_file": "slack_method_tier_budget.py",
"py": '''"""Check a Slack app's polling schedule against the documented method tiers.

Read only, and almost entirely offline. Slack limits per method, per workspace,
per app; the tier is printed on each method's reference page; and the finding is
sixty divided by your polling interval against that number. No read method
reports remaining budget, so calling more is not a way to learn more, and this
audit will not find a limit by exhausting one.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_method_tier_budget")

API = "https://slack.com/api/"

DOCS = "https://docs.slack.dev/apis/web-api/rate-limits"

# The documented floor for each tier, in requests per minute. Slack writes them
# as "1+", "20+", "50+", "100+": the floor is what you may design against, and
# the plus is headroom you are not entitled to.
TIER_FLOOR = {1: 1, 2: 20, 3: 50, 4: 100}

# Seeded from the method reference pages, and deliberately not exhaustive. Tiers
# move, new methods arrive, and a table that guesses is worse than a table that
# admits its edges: an invented number here would be quoted back in a design
# review a year from now with this file as the source.
KNOWN_TIERS = {
    "conversations.list": 2,
    "conversations.history": 3,
    "conversations.replies": 3,
    "conversations.info": 3,
    "conversations.members": 4,
    "users.list": 2,
    "users.info": 4,
    "users.conversations": 3,
    "users.lookupByEmail": 3,
    "team.info": 3,
}

# Methods whose limit does not fit the four-number table at all. Naming them
# matters because a reader who cannot find one in the tier list assumes the list
# is incomplete rather than that the method is elsewhere.
SPECIAL = {
    "chat.postMessage": "roughly one message per second per channel, with a "
                        "separate workspace-wide ceiling",
    "chat.update": "the same envelope as chat.postMessage, which is why editing "
                   "one message per token does not stream",
}

# What replaces the poll. This is the actual deliverable: a method on a low tier
# is Slack saying the answer is not something you ask for repeatedly.
SUBSTITUTES = {
    "users.list": "subscribe to user_change and keep your own directory; a full "
                  "users.list becomes a cold-start backfill and a nightly "
                  "reconciliation",
    "users.info": "cache per user with a long TTL and invalidate on user_change "
                  "rather than re-reading on every mention",
    "conversations.list": "subscribe to channel_created, channel_rename and "
                          "channel_archive; the inventory changes a few times a "
                          "week and you are asking twice a minute",
    "conversations.members": "subscribe to member_joined_channel and "
                             "member_left_channel and maintain the roster",
    "conversations.history": "subscribe to message.channels and message.groups; "
                             "history then becomes a rare backfill instead of the "
                             "primary data path",
    "team.info": "call it once at boot. A workspace name and icon change about "
                 "never, and nothing downstream needs them fresher than a deploy",
}

# The audit will probe a method only if it is on this list, and only once. A
# schedule file is written by a human and can name anything; calling an arbitrary
# method name because it appeared in a config file is how a read-only tool stops
# being one.
ALLOWED_PROBE = {
    "conversations.list": {"limit": 1, "exclude_archived": "true"},
    "users.list": {"limit": 1},
    "team.info": {},
}

RANK = {"polled-tier-1": 0, "over-budget": 1, "at-the-edge": 2,
        "tier-unknown": 3, "special-tier": 4, "no-interval": 5,
        "within-budget": 6}


def tier_of(method, table=None):
    """The documented tier for a method. Pure. Returns (tier, source).

    source is one of table, special, unknown-admin, unknown, no-method. Only
    "table" carries a number, and that is the point: unknown is an answer here,
    not a fallback to something plausible.
    """
    name = str(method or "").strip()
    table = KNOWN_TIERS if table is None else table
    if not name:
        return (None, "no-method")
    if name in SPECIAL:
        return (None, "special")
    if name in table:
        return (table[name], "table")
    if name.split(".")[0] == "admin":
        return (None, "unknown-admin")
    return (None, "unknown")


def budget_verdict(entry, table=None):
    """One scheduled call against its tier. Pure. Returns (verdict, rate, detail).

    entry: {"method", "interval_seconds", "calls_per_run"?, "tier"?}. A tier in
    the entry wins, because it came from the reference page and this table did
    not.
    """
    entry = entry or {}
    method = str(entry.get("method") or "").strip() or "?"
    try:
        interval = float(entry.get("interval_seconds") or 0)
    except (TypeError, ValueError):
        interval = 0.0
    try:
        per_run = max(1, int(entry.get("calls_per_run") or 1))
    except (TypeError, ValueError):
        per_run = 1

    if interval <= 0:
        return ("no-interval", 0.0,
                "%s has no polling interval, so there is nothing to divide. If it "
                "is called once at boot that is the answer this audit wants to "
                "hear; write it down as such." % method)

    rate = 60.0 / interval * per_run
    tier = entry.get("tier")
    if tier is None:
        tier, source = tier_of(method, table)
    else:
        source = "supplied"
    try:
        tier = int(tier) if tier is not None else None
    except (TypeError, ValueError):
        tier = None

    if tier not in TIER_FLOOR:
        if source == "special":
            return ("special-tier", rate,
                    "%s is on the Special tier: %s. The four-number table does "
                    "not apply and %.1f calls a minute is the wrong unit for it."
                    % (method, SPECIAL.get(method, "a limit of its own"), rate))
        hint = ("the admin family is where the expensive workspace-wide "
                "operations live and is the likeliest place to meet Tier 1"
                if source == "unknown-admin" else
                "this audit does not carry a tier for it")
        return ("tier-unknown", rate,
                "%s is polled at %.1f call(s) a minute and %s. Read the tier off "
                "the method's reference page and put it in the schedule; see %s."
                % (method, rate, hint, DOCS))

    floor = TIER_FLOOR[tier]
    share = rate / floor
    if tier == 1 and rate > floor:
        return ("polled-tier-1", rate,
                "%s is on Tier 1, which is about %d request a minute, and this "
                "schedule asks for %.1f. That is %.0f%% of the entire budget for "
                "the method. Tier 1 is Slack saying this is not something you "
                "poll, and no backoff makes a permanent overshoot temporary."
                % (method, floor, rate, share * 100))
    if share > 1.0:
        return ("over-budget", rate,
                "%s is on Tier %d, a floor of %d a minute, and this schedule asks "
                "for %.1f. Every run past the floor is refused, so the job's real "
                "throughput is %d a minute however the client sleeps."
                % (method, tier, floor, rate, floor))
    if share > 0.8:
        return ("at-the-edge", rate,
                "%s is at %.1f a minute against a Tier %d floor of %d. It works "
                "today and it shares the window with everything else in this app "
                "that calls the same method." % (method, rate, tier, floor))
    return ("within-budget", rate,
            "%.1f/min against a tier %d floor of %d/min" % (rate, tier, floor))


def substitute(method):
    """What to do instead of polling this. Pure. Returns text or None."""
    return SUBSTITUTES.get(str(method or "").strip())


def probe_once(session, method):
    """One call, to confirm the token can reach the method. GET only.

    Refuses anything not on the allowlist. A schedule file is written by a human
    and can name any method at all; calling whatever appeared in a config file
    is how a read-only tool quietly stops being one.
    """
    params = ALLOWED_PROBE.get(method)
    if params is None:
        return (None, "not probed: %s is not on this audit's list of methods it "
                      "can prove are reads" % method)
    body = session.get(API + method, params=params, timeout=30).json()
    if body.get("ok") is True:
        return (True, "reachable, one call spent")
    return (False, "answered ok: false, error=%s" % body.get("error"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--schedule", required=True,
                    help="JSON list of {method, interval_seconds, calls_per_run?, tier?}")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--probe", action="store_true",
                    help="make one call per allowlisted method to confirm reachability")
    args = ap.parse_args()

    entries = json.loads(open(args.schedule, encoding="utf-8").read())

    session = None
    if args.probe:
        token = os.environ.get(args.token_env)
        if not token:
            log.error("set %s, or drop --probe: the arithmetic is offline",
                      args.token_env)
            return 2
        session = requests.Session()
        session.headers.update({"Authorization": "Bearer " + token})
        identity = session.get(API + "auth.test", timeout=30).json()
        if identity.get("ok") is not True:
            log.error("auth.test answered ok: false, error=%s", identity.get("error"))
            return 2
        log.info("identity   %s in %s", identity.get("user_id"), identity.get("team"))

    judged = [(budget_verdict(e), e) for e in entries]
    judged.sort(key=lambda pair: RANK.get(pair[0][0], 9))

    over = unknown = 0
    for (verdict, rate, detail), entry in judged:
        method = str(entry.get("method") or "?")
        if verdict == "within-budget":
            log.info("%-22s %-15s %s", method, verdict, detail)
            continue
        if verdict == "tier-unknown":
            unknown += 1
            log.warning("%-22s %-15s %s", method, verdict, detail)
        elif verdict in ("no-interval", "special-tier"):
            log.info("%-22s %-15s %s", method, verdict, detail)
        else:
            over += 1
            log.warning("%-22s %-15s %s", method, verdict, detail)
            instead = substitute(method)
            if instead:
                log.warning("  repair: %s", instead)
            else:
                log.warning("  repair: move it out of the loop. Call it once at "
                            "boot, cache the answer with a long TTL, and refresh "
                            "it from an event rather than from a timer")

        if args.probe and session is not None:
            ok, note = probe_once(session, method)
            log.info("  probe: %s", note if ok is not False else "unreachable, " + note)

    log.info("%d entry(s) checked, %d over budget, %d with an unknown tier",
             len(entries), over, unknown)
    return 1 if (over or unknown) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-method-tier-budget.mjs",
"js": '''/**
 * Check a Slack app's polling schedule against the documented method tiers.
 *
 * Read only, and almost entirely offline. Slack limits per method, per
 * workspace, per app; the tier is printed on each method's reference page; and
 * the finding is sixty divided by your polling interval against that number. No
 * read method reports remaining budget, so calling more is not a way to learn
 * more, and this audit will not find a limit by exhausting one.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';
const DOCS = 'https://docs.slack.dev/apis/web-api/rate-limits';

// Slack writes the tiers as "1+", "20+", "50+", "100+": the floor is what you
// may design against, and the plus is headroom you are not entitled to.
const TIER_FLOOR = new Map([[1, 1], [2, 20], [3, 50], [4, 100]]);

// Seeded from the method reference pages, and deliberately not exhaustive. An
// invented number here would be quoted back in a design review a year from now
// with this file as the source.
const KNOWN_TIERS = new Map([
  ['conversations.list', 2],
  ['conversations.history', 3],
  ['conversations.replies', 3],
  ['conversations.info', 3],
  ['conversations.members', 4],
  ['users.list', 2],
  ['users.info', 4],
  ['users.conversations', 3],
  ['users.lookupByEmail', 3],
  ['team.info', 3],
]);

const SPECIAL = new Map([
  ['chat.postMessage', 'roughly one message per second per channel, with a ' +
    'separate workspace-wide ceiling'],
  ['chat.update', 'the same envelope as chat.postMessage, which is why editing ' +
    'one message per token does not stream'],
]);

// What replaces the poll. This is the actual deliverable.
const SUBSTITUTES = new Map([
  ['users.list', 'subscribe to user_change and keep your own directory; a full ' +
    'users.list becomes a cold-start backfill and a nightly reconciliation'],
  ['users.info', 'cache per user with a long TTL and invalidate on user_change ' +
    'rather than re-reading on every mention'],
  ['conversations.list', 'subscribe to channel_created, channel_rename and ' +
    'channel_archive; the inventory changes a few times a week and you are ' +
    'asking twice a minute'],
  ['conversations.members', 'subscribe to member_joined_channel and ' +
    'member_left_channel and maintain the roster'],
  ['conversations.history', 'subscribe to message.channels and message.groups; ' +
    'history then becomes a rare backfill instead of the primary data path'],
  ['team.info', 'call it once at boot. A workspace name and icon change about ' +
    'never, and nothing downstream needs them fresher than a deploy'],
]);

// The audit will probe a method only if it is on this list, and only once.
const ALLOWED_PROBE = new Map([
  ['conversations.list', { limit: '1', exclude_archived: 'true' }],
  ['users.list', { limit: '1' }],
  ['team.info', {}],
]);

const RANK = new Map([
  ['polled-tier-1', 0], ['over-budget', 1], ['at-the-edge', 2],
  ['tier-unknown', 3], ['special-tier', 4], ['no-interval', 5],
  ['within-budget', 6],
]);

/**
 * The documented tier for a method. Pure. Returns [tier, source].
 * Only "table" carries a number: unknown is an answer here, not a fallback to
 * something plausible.
 */
export function tierOf(method, table = KNOWN_TIERS) {
  const name = String(method ?? '').trim();
  if (!name) return [null, 'no-method'];
  if (SPECIAL.has(name)) return [null, 'special'];
  if (table.has(name)) return [table.get(name), 'table'];
  if (name.split('.')[0] === 'admin') return [null, 'unknown-admin'];
  return [null, 'unknown'];
}

/**
 * One scheduled call against its tier. Pure. Returns [verdict, rate, detail].
 * A tier in the entry wins, because it came from the reference page.
 */
export function budgetVerdict(entry, table = KNOWN_TIERS) {
  const doc = entry ?? {};
  const method = String(doc.method ?? '').trim() || '?';
  const interval = Number(doc.interval_seconds ?? 0);
  const perRun = Math.max(1, Math.trunc(Number(doc.calls_per_run ?? 1) || 1));

  if (!Number.isFinite(interval) || interval <= 0) {
    return ['no-interval', 0,
      `${method} has no polling interval, so there is nothing to divide. If it ` +
      'is called once at boot that is the answer this audit wants to hear; ' +
      'write it down as such.'];
  }

  const rate = (60 / interval) * perRun;
  let tier = doc.tier ?? null;
  let source = 'supplied';
  if (tier === null || tier === undefined) [tier, source] = tierOf(method, table);
  tier = Number.isFinite(Number(tier)) ? Math.trunc(Number(tier)) : null;

  if (!TIER_FLOOR.has(tier)) {
    if (source === 'special') {
      const note = SPECIAL.get(method) ?? 'a limit of its own';
      return ['special-tier', rate,
        `${method} is on the Special tier: ${note}. The four-number table does ` +
        `not apply and ${rate.toFixed(1)} calls a minute is the wrong unit for it.`];
    }
    const hint = source === 'unknown-admin'
      ? 'the admin family is where the expensive workspace-wide operations live ' +
        'and is the likeliest place to meet Tier 1'
      : 'this audit does not carry a tier for it';
    return ['tier-unknown', rate,
      `${method} is polled at ${rate.toFixed(1)} call(s) a minute and ${hint}. ` +
      `Read the tier off the method's reference page and put it in the ` +
      `schedule; see ${DOCS}.`];
  }

  const floor = TIER_FLOOR.get(tier);
  const share = rate / floor;
  if (tier === 1 && rate > floor) {
    return ['polled-tier-1', rate,
      `${method} is on Tier 1, which is about ${floor} request a minute, and ` +
      `this schedule asks for ${rate.toFixed(1)}. That is ` +
      `${(share * 100).toFixed(0)}% of the entire budget for the method. Tier 1 ` +
      'is Slack saying this is not something you poll, and no backoff makes a ' +
      'permanent overshoot temporary.'];
  }
  if (share > 1.0) {
    return ['over-budget', rate,
      `${method} is on Tier ${tier}, a floor of ${floor} a minute, and this ` +
      `schedule asks for ${rate.toFixed(1)}. Every run past the floor is ` +
      `refused, so the job's real throughput is ${floor} a minute however the ` +
      'client sleeps.'];
  }
  if (share > 0.8) {
    return ['at-the-edge', rate,
      `${method} is at ${rate.toFixed(1)} a minute against a Tier ${tier} floor ` +
      `of ${floor}. It works today and it shares the window with everything else ` +
      'in this app that calls the same method.'];
  }
  return ['within-budget', rate,
    `${rate.toFixed(1)}/min against a tier ${tier} floor of ${floor}/min`];
}

/** What to do instead of polling this. Pure. Returns text or null. */
export function substitute(method) {
  return SUBSTITUTES.get(String(method ?? '').trim()) ?? null;
}

/** One call, to confirm the token can reach the method. GET only. */
async function probeOnce(token, method) {
  const params = ALLOWED_PROBE.get(method);
  if (params === undefined) {
    return [null, `not probed: ${method} is not on this audit's list of methods ` +
      'it can prove are reads'];
  }
  const qs = new URLSearchParams(params);
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok === true) return [true, 'reachable, one call spent'];
  return [false, `answered ok: false, error=${body.error}`];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const schedule = arg(args, '--schedule', '');
  if (!schedule) {
    console.error('usage: --schedule slack_schedule.json [--probe] ' +
      '[--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const entries = JSON.parse(await readFile(schedule, 'utf8'));

  let token = null;
  if (args.includes('--probe')) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    token = process.env[tokenEnv];
    if (!token) {
      console.error(`set ${tokenEnv}, or drop --probe: the arithmetic is offline`);
      process.exitCode = 2;
      return;
    }
    const res = await fetch(`${API}auth.test`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const identity = await res.json();
    if (identity.ok !== true) {
      console.error(`auth.test answered ok: false, error=${identity.error}`);
      process.exitCode = 2;
      return;
    }
    console.log(`identity   ${identity.user_id} in ${identity.team}`);
  }

  const judged = entries.map((e) => [budgetVerdict(e), e]);
  judged.sort((a, b) => (RANK.get(a[0][0]) ?? 9) - (RANK.get(b[0][0]) ?? 9));

  let over = 0;
  let unknown = 0;
  for (const [[verdict, , detail], entry] of judged) {
    const method = String(entry.method ?? '?');
    if (verdict === 'within-budget') {
      console.log(`${method.padEnd(22)} ${verdict.padEnd(15)} ${detail}`);
      continue;
    }
    if (verdict === 'tier-unknown') {
      unknown += 1;
      console.warn(`${method.padEnd(22)} ${verdict.padEnd(15)} ${detail}`);
    } else if (verdict === 'no-interval' || verdict === 'special-tier') {
      console.log(`${method.padEnd(22)} ${verdict.padEnd(15)} ${detail}`);
    } else {
      over += 1;
      console.warn(`${method.padEnd(22)} ${verdict.padEnd(15)} ${detail}`);
      const instead = substitute(method);
      console.warn(instead
        ? `  repair: ${instead}`
        : '  repair: move it out of the loop. Call it once at boot, cache the ' +
          'answer with a long TTL, and refresh it from an event rather than ' +
          'from a timer');
    }

    if (token) {
      const [ok, note] = await probeOnce(token, method);
      console.log(`  probe: ${ok === false ? `unreachable, ${note}` : note}`);
    }
  }

  console.log(`${entries.length} entry(s) checked, ${over} over budget, ` +
    `${unknown} with an unknown tier`);
  process.exitCode = (over || unknown) ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing schedule.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are schedule entries, not API responses, because the finding is arithmetic and the arithmetic is the thing worth pinning. The important tests are the ones about not knowing: an unfamiliar method returns <code>tier-unknown</code> with a pointer to the reference page rather than a plausible number, an <code>admin.*</code> method says which neighbourhood it is in without claiming a tier, and a tier supplied in the schedule overrides the seeded table because it came from the documentation and the table did not.",
"test_py_file": "test_slack_method_tier_budget.py",
"test_py": '''from slack_method_tier_budget import budget_verdict, substitute, tier_of


def test_the_seeded_table_answers_for_the_methods_it_carries():
    assert tier_of("conversations.list") == (2, "table")
    assert tier_of("conversations.members") == (4, "table")
    assert tier_of("users.info") == (4, "table")


def test_an_unfamiliar_method_is_unknown_rather_than_guessed():
    assert tier_of("dnd.info") == (None, "unknown")
    assert tier_of("") == (None, "no-method")
    assert tier_of(None) == (None, "no-method")


def test_the_admin_family_is_named_without_claiming_a_number():
    tier, source = tier_of("admin.teams.list")
    assert tier is None
    assert source == "unknown-admin"


def test_the_special_tier_is_a_separate_answer_from_not_knowing():
    assert tier_of("chat.postMessage") == (None, "special")
    verdict, _, detail = budget_verdict({"method": "chat.postMessage",
                                         "interval_seconds": 1})
    assert verdict == "special-tier"
    assert "per channel" in detail


def test_a_tier_1_method_in_a_loop_is_the_headline_finding():
    verdict, rate, detail = budget_verdict({"method": "admin.teams.list",
                                            "interval_seconds": 30, "tier": 1})
    assert verdict == "polled-tier-1"
    assert rate == 2.0
    assert "200%" in detail
    assert "no backoff" in detail


def test_a_supplied_tier_beats_the_seeded_table():
    # The schedule says the tier moved; the reference page is the source and
    # this table is not.
    verdict, _, _ = budget_verdict({"method": "conversations.list",
                                    "interval_seconds": 30, "tier": 1})
    assert verdict == "polled-tier-1"


def test_the_same_interval_is_fine_on_a_higher_tier():
    verdict, rate, _ = budget_verdict({"method": "conversations.members",
                                       "interval_seconds": 1})
    assert verdict == "within-budget"
    assert rate == 60.0


def test_calls_per_run_multiplies_the_rate():
    verdict, rate, _ = budget_verdict({"method": "users.list",
                                       "interval_seconds": 60, "calls_per_run": 40})
    assert rate == 40.0
    assert verdict == "over-budget"


def test_the_floor_itself_is_the_edge_and_not_yet_over():
    verdict, rate, _ = budget_verdict({"method": "users.list",
                                       "interval_seconds": 3})
    assert rate == 20.0
    assert verdict == "at-the-edge"
    verdict, rate, _ = budget_verdict({"method": "users.list",
                                       "interval_seconds": 2.5})
    assert rate == 24.0
    assert verdict == "over-budget"


def test_an_unknown_tier_asks_for_the_number_instead_of_inventing_one():
    verdict, _, detail = budget_verdict({"method": "dnd.info",
                                         "interval_seconds": 10})
    assert verdict == "tier-unknown"
    assert "reference page" in detail
    assert "docs.slack.dev" in detail


def test_no_interval_is_a_good_answer_not_a_missing_one():
    verdict, rate, detail = budget_verdict({"method": "team.info"})
    assert verdict == "no-interval"
    assert rate == 0.0
    assert "once at boot" in detail
    assert budget_verdict({"method": "team.info",
                           "interval_seconds": "soon"})[0] == "no-interval"


def test_every_poll_worth_flagging_has_something_to_replace_it_with():
    assert "user_change" in substitute("users.list")
    assert "channel_created" in substitute("conversations.list")
    assert "member_joined_channel" in substitute("conversations.members")
    assert substitute("dnd.info") is None
''',
"test_js_file": "slack-method-tier-budget.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { budgetVerdict, substitute, tierOf }
  from './slack-method-tier-budget.mjs';

test('the seeded table answers for the methods it carries', () => {
  assert.deepEqual(tierOf('conversations.list'), [2, 'table']);
  assert.deepEqual(tierOf('conversations.members'), [4, 'table']);
  assert.deepEqual(tierOf('users.info'), [4, 'table']);
});

test('an unfamiliar method is unknown rather than guessed', () => {
  assert.deepEqual(tierOf('dnd.info'), [null, 'unknown']);
  assert.deepEqual(tierOf(''), [null, 'no-method']);
  assert.deepEqual(tierOf(null), [null, 'no-method']);
});

test('the admin family is named without claiming a number', () => {
  const [tier, source] = tierOf('admin.teams.list');
  assert.equal(tier, null);
  assert.equal(source, 'unknown-admin');
});

test('the special tier is a separate answer from not knowing', () => {
  assert.deepEqual(tierOf('chat.postMessage'), [null, 'special']);
  const [verdict, , detail] = budgetVerdict({
    method: 'chat.postMessage', interval_seconds: 1,
  });
  assert.equal(verdict, 'special-tier');
  assert.match(detail, /per channel/);
});

test('a tier 1 method in a loop is the headline finding', () => {
  const [verdict, rate, detail] = budgetVerdict({
    method: 'admin.teams.list', interval_seconds: 30, tier: 1,
  });
  assert.equal(verdict, 'polled-tier-1');
  assert.equal(rate, 2);
  assert.match(detail, /200%/);
  assert.match(detail, /no backoff/);
});

test('a supplied tier beats the seeded table', () => {
  assert.equal(budgetVerdict({
    method: 'conversations.list', interval_seconds: 30, tier: 1,
  })[0], 'polled-tier-1');
});

test('the same interval is fine on a higher tier', () => {
  const [verdict, rate] = budgetVerdict({
    method: 'conversations.members', interval_seconds: 1,
  });
  assert.equal(verdict, 'within-budget');
  assert.equal(rate, 60);
});

test('calls per run multiplies the rate', () => {
  const [verdict, rate] = budgetVerdict({
    method: 'users.list', interval_seconds: 60, calls_per_run: 40,
  });
  assert.equal(rate, 40);
  assert.equal(verdict, 'over-budget');
});

test('the floor itself is the edge and not yet over', () => {
  const [edge, rate] = budgetVerdict({ method: 'users.list', interval_seconds: 3 });
  assert.equal(rate, 20);
  assert.equal(edge, 'at-the-edge');
  const [over, faster] = budgetVerdict({ method: 'users.list', interval_seconds: 2.5 });
  assert.equal(faster, 24);
  assert.equal(over, 'over-budget');
});

test('an unknown tier asks for the number instead of inventing one', () => {
  const [verdict, , detail] = budgetVerdict({ method: 'dnd.info', interval_seconds: 10 });
  assert.equal(verdict, 'tier-unknown');
  assert.match(detail, /reference page/);
  assert.match(detail, /docs\\.slack\\.dev/);
});

test('no interval is a good answer not a missing one', () => {
  const [verdict, rate, detail] = budgetVerdict({ method: 'team.info' });
  assert.equal(verdict, 'no-interval');
  assert.equal(rate, 0);
  assert.match(detail, /once at boot/);
  assert.equal(budgetVerdict({ method: 'team.info', interval_seconds: 'soon' })[0],
    'no-interval');
});

test('every poll worth flagging has something to replace it with', () => {
  assert.match(substitute('users.list'), /user_change/);
  assert.match(substitute('conversations.list'), /channel_created/);
  assert.match(substitute('conversations.members'), /member_joined_channel/);
  assert.equal(substitute('dnd.info'), null);
});
''',
"faq": [
 ("How do I find out which tier a method is on?",
  "The method's own reference page states it, in a line near the top: Tier 3: 50+ per minute, and so on. There is no API that returns it and no header that reports your remaining budget. The script seeds a small table for the methods it is confident about and asks you to fill in the rest from the documentation rather than guessing, because tiers do change."),
 ("Is a tier the exact number of calls I get?",
  "It is the floor. Slack writes them as 1+, 20+, 50+ and 100+ per minute, and allows short bursts above the floor. Design against the floor: the plus is headroom you are not entitled to and cannot measure. If your schedule only works because of the burst allowance, it will start failing the first time the app has a busy minute for any other reason."),
 ("Will exponential backoff fix a Tier 1 method in a loop?",
  "No. Backoff recovers from a temporary overshoot. A loop that wants two requests a minute out of a budget of one is overshooting permanently, so the job's throughput is fixed at the tier no matter how the client sleeps. The polite backoff simply makes the failure quieter, which is worse, because it stops anyone from noticing the design problem."),
 ("Why does the script not just call each method to see what happens?",
  "Because the only way to learn a limit by calling is to exhaust it, and exhausting a window spends a real workspace's quota on a demonstration that every other app on the same method pays for. With --probe it makes exactly one call per method, only for methods it can prove are reads, and never in a loop. The tier is documented; the arithmetic is offline."),
 ("The audit says tier-unknown for most of our methods. Is that useful?",
  "It is the useful state. It names precisely which reference pages somebody has to open, and it turns an unbounded question into a short list. The alternative is a table full of plausible numbers that nobody checked, which is exactly how an audit becomes the source of the wrong answer it was written to prevent."),
],
"related": [
 ("/slack/non-marketplace-history-clamp/", "when a tier changes underneath you"),
 ("/slack/ratelimited-retry-after-ignored/", "the refusal, once the budget is spent"),
 ("/slack/pagination-not-followed/", "next_cursor ignored, so one page is all you see"),
],
"citations": [CITE_RATE_LIMITS, CITE_WEB_API, CITE_EVENTS, CITE_USERS_LIST],
},

{
"slug": "parallel-workers-share-quota",
"title": "One quota bucket, eight workers that think they are alone",
"description": "Scaling to eight workers made the job slower. Slack's quota is keyed on method, workspace and app, so replicas share one bucket and resynchronise.",
"h1": "One quota bucket, eight workers that think they are alone",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack rate limit shared quota", "slack api concurrency rate limit",
             "slack workers ratelimited", "slack thundering herd retry",
             "slack rate limit per app per workspace"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the strongest evidence is an auth.test from each replica",
"lead": "The backfill was slow, so it was given eight workers. It got slower. Each worker has its own client, its own connection pool and its own carefully written backoff, and each of them spends most of its life asleep.</p><p>Nothing in that list is wrong. The mistake is upstream of all of it: the quota is not stored per process. Eight workers is not eight budgets. It is one budget, divided eight ways, by eight things that do not know the other seven exist.",
"short_answer": """<p>Slack's rate limit is keyed on <strong>method, workspace and app</strong>. Not on process, host, container, connection or client instance. Ten replicas of the same deployment holding the same token draw from exactly one bucket, so adding concurrency to a rate-limited API is negative work: total throughput does not move, and per-request latency gets worse because every worker now spends time in backoff it did not spend before.</p>
<p>Then the second-order failure. Each replica gets the same <code>Retry-After</code>, because it is the same window. Each sleeps exactly that long. Each wakes at the same instant and retries together, so the bucket is emptied in the first few milliseconds of every window and the herd re-forms on the next refusal. Backoff without jitter does not spread load; it synchronises it.</p>
<p>The script below establishes the shared identity from <code>auth.test</code> bodies collected from each replica, does the fan-out arithmetic against the tier, and infers unseen callers from a paced sample: being throttled at a rate well below the documented floor means somebody else is spending your window.</p>""",
"problem": """<p>Every intuition you have about scaling a worker pool is correct except for the one that matters here. More workers usually means more throughput because the bottleneck is local: CPU, a connection, a disk. When the bottleneck is a quota held by somebody else's server and keyed on your app rather than on your process, the pool size is a divisor and not a multiplier. Eight workers each achieving one-eighth of the rate is the good case; the realistic case is worse, because the coordination overhead is paid in wall-clock sleeps.</p>
<p>The synchronisation is what makes it pathological rather than merely futile. Slack hands every refused caller the same number of seconds, because the window is a property of the window and not of the caller. Eight replicas that each implement the documented behaviour perfectly will therefore sleep for identical durations and wake within milliseconds of each other. The first two calls of the new window succeed and the other six are refused, all at once, and receive an identical <code>Retry-After</code> again. The pool converges on a lockstep that nobody designed and nobody can see from inside any single process.</p>
<p>And the diagnosis is genuinely hard from one process, because every log you have is a log of one replica behaving reasonably. It made twelve calls a minute against a method whose floor is twenty and it was throttled, which reads as a Slack problem. It is not: it is the other four replicas, or the cron on the analytics box that nobody remembers, or the staging deployment still pointed at the production token.</p>""",
"why": """<p><strong>The key does not contain your process.</strong> This is the whole note. Method, workspace, app. Two tokens of the same app in the same workspace share. Two replicas of the same container share. A laptop running the script during the incident shares. Only a genuinely different app, or a different workspace, gets its own bucket.</p>
<p><strong>Being throttled below the floor is evidence about somebody else.</strong> If you make twelve calls a minute against a method with a floor of twenty and are refused, at least eight calls a minute came from somewhere that is not you. That subtraction is the most useful thing a single process can compute, and it is the only way to find the caller nobody remembers deploying.</p>
<p><strong>Identical backoff is worse than random backoff.</strong> Correct, documented, uniform backoff produces a thundering herd, because uniformity is exactly what you do not want when the wake-up time is shared. Jitter is not a refinement here; without it the pool cannot de-synchronise, ever.</p>
<p><strong>Per-replica limiting cannot work in principle.</strong> A token bucket inside each process can only enforce a rate it can observe, and it cannot observe the other seven. The limiter has to live somewhere all callers meet: a shared store, or a single sender service that everything else queues into.</p>
<p><strong>Parallelising across channels is a different question and a real answer.</strong> <code>chat.postMessage</code> is limited per channel, so N channels genuinely means N envelopes. That is the one axis on which concurrency buys throughput, and it is worth separating from the axis on which it does not.</p>""",
"steps": [
 {"h": "Collect an auth.test from every process that holds a token",
  "body": """<p>Every replica, every cron, every notebook, staging included. Save the response bodies with a label. Two of them carrying the same <code>team_id</code> and the same <code>bot_id</code> are the same app in the same workspace, which is the quota key, which means they are one caller as far as Slack is concerned however many hosts they run on.</p>"""},
 {"h": "Add up the rates you believe each one makes",
  "body": """<p>Calls per minute per replica, times the replica count, summed. Against the documented floor for that method. This arithmetic usually ends the investigation on its own, because nobody has ever written the total down and the total is often several times the budget.</p>"""},
 {"h": "Take a paced sample and see whether it is refused",
  "body": """<p>The script makes a small number of read calls, deliberately spaced well under the tier, and reports whether any came back throttled. It refuses to go below a spacing floor. If a rate that low is refused, the bucket was already empty when the script arrived, and that is a measurement of everybody else.</p>"""},
 {"h": "Subtract to find the callers you did not know about",
  "body": """<p>The floor minus your observed rate is the traffic that has to be coming from somewhere else. Expressed as a multiple of your own rate it is a headcount: roughly how many more processes like this one are on the same method. That number is what you take to the team to ask whose job it is.</p>"""},
 {"h": "Measure the herd, not just the rate",
  "body": """<p>Replica count, the <code>Retry-After</code> they all received, and the jitter fraction in your backoff. With no jitter the retry window has zero width and every replica lands in the same millisecond. The script computes how many arrive in the first hundred milliseconds, which is the number that decides whether the next window is also wasted.</p>"""},
 {"h": "Move the limiter out of the process",
  "body": """<p>One shared token bucket, in Redis or in a single sender service, so the app respects the tier regardless of how many copies of it are running. Add jitter to every backoff. Then, if throughput still matters, parallelise along the axis that actually has more than one bucket: across channels for posting, or across workspaces, never across workers on one method.</p>"""},
],
"verify": """<p>Re-run after the shared limiter is in front of the sender. The sample should come back clean and the fan-out arithmetic should sit under the floor.</p>
<pre><code class="language-bash">python3 slack_shared_quota_audit.py --identities replicas.json --tier-floor 20
# identity   U0APPBOT11 bot B0APPBOT99 in acme
# bucket     separate-buckets  2 group(s), no two callers share a workspace and app
# fanout     headroom          8.0/min across 4 caller(s) against a floor of 20/min
# sample     5 call(s) at 5.0s spacing, 0 throttled
# competitors  nothing was throttled, so nothing is implied about other callers
# herd       de-synchronised   retries spread over 15.0s, about 1 in the first 100ms
# 0 finding(s)</code></pre>""",
"code_intro": "Five pure functions and one paced GET loop. <code>same_bucket</code> is the one that ends arguments: it groups <code>auth.test</code> bodies by the key Slack actually uses, and two replicas that land in one group are one caller no matter what the deployment diagram says. <code>implied_competitors</code> is the subtraction that finds the process nobody remembers. <code>herd_window</code> is about time rather than rate, because a pool can be under budget and still waste every window by arriving in it together.",
"py_file": "slack_shared_quota_audit.py",
"py": '''"""Find out how many callers are sharing one Slack rate-limit bucket.

Read only. Slack keys its quota on method, workspace and app, so replicas of one
deployment share a single budget and adding workers to a throttled job makes it
slower. This groups auth.test bodies by that key, adds up the fan-out against the
documented tier floor, takes a deliberately slow sample to see whether the bucket
is already empty, and measures how tightly the pool's retries synchronise.

The sample is paced well below the tier and refuses to go faster. Nothing here
tries to exhaust a window: that would be a denial of service against the
workspace under audit, and against everybody else's app in it.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_shared_quota_audit")

API = "https://slack.com/api/"

# The sample will not go faster than this, whatever the flags say. An audit that
# can be pointed at a production workspace has to be incapable of becoming the
# incident it was sent to diagnose.
MIN_SPACING = 3.0

# Retries landing inside this window of each other are one wave rather than a
# spread. A hundred milliseconds is generous to the client and still small
# against any Retry-After Slack returns.
BURST = 0.1


def same_bucket(identities):
    """Group callers by the key Slack's quota actually uses. Pure.

    identities: [(label, auth_test_body), ...].

    The documented key is (method, workspace, app). team_id is the workspace and
    bot_id is the closest thing a read-only caller has to the app's identity in
    it: two different tokens of the same app in the same workspace return the
    same bot_id. A user token has no bot_id, so it falls back to user_id, which
    is a weaker key and is labelled as such in the output.
    """
    groups = {}
    for label, body in identities or []:
        body = body if isinstance(body, dict) else {}
        team = str(body.get("team_id") or "").strip() or "unknown-team"
        actor = str(body.get("bot_id") or "").strip()
        if not actor:
            actor = str(body.get("user_id") or "").strip() or "unknown-app"
        groups.setdefault("%s/%s" % (team, actor), []).append(str(label))
    return groups


def bucket_verdict(groups):
    """Say whether anything is sharing. Pure. Returns (verdict, detail)."""
    if not groups:
        return ("nothing-supplied",
                "no identities were given, so the sharing question is unanswered. "
                "One auth.test per process, saved with a label, is the whole "
                "input and it is the evidence that ends the argument.")
    shared = {key: labels for key, labels in groups.items() if len(labels) > 1}
    if not shared:
        return ("separate-buckets",
                "%d group(s), no two callers share a workspace and app"
                % len(groups))
    biggest = max(shared.items(), key=lambda pair: len(pair[1]))
    return ("one-bucket",
            "%d caller(s) share the key %s: %s. Slack sees one app in one "
            "workspace, so they hold one budget between them however many hosts "
            "they run on." % (len(biggest[1]), biggest[0], ", ".join(biggest[1])))


def aggregate_rate(workers):
    """Total calls per minute against one method. Pure.

    workers: [{"label", "calls_per_minute", "replicas"?}]. Nobody has usually
    written this total down, and the total is the finding.
    """
    total = 0.0
    for worker in workers or []:
        try:
            rate = float((worker or {}).get("calls_per_minute") or 0)
        except (TypeError, ValueError):
            rate = 0.0
        try:
            replicas = max(1, int((worker or {}).get("replicas") or 1))
        except (TypeError, ValueError):
            replicas = 1
        total += max(0.0, rate) * replicas
    return total


def fanout_verdict(total_rate, tier_floor):
    """The pool's demand against the method's floor. Pure.

    Returns (verdict, share, detail).
    """
    floor = max(1.0, float(tier_floor or 1))
    share = float(total_rate) / floor
    if share > 1.0:
        return ("saturated", share,
                "%.1f/min across the pool against a floor of %.0f/min. The pool is "
                "asking for %.1f times the budget, so its real throughput is the "
                "floor and the extra workers buy queueing rather than work."
                % (total_rate, floor, share))
    if share > 0.8:
        return ("at-the-edge", share,
                "%.1f/min across the pool against a floor of %.0f/min. One more "
                "replica, or one retry storm, puts it over."
                % (total_rate, floor))
    return ("headroom", share,
            "%.1f/min against a floor of %.0f/min" % (total_rate, floor))


def implied_competitors(observed_rate, tier_floor, throttled):
    """Callers you cannot see, inferred by subtraction. Pure.

    Returns (others, detail). others is a multiple of your own rate, or None
    when nothing can be inferred. This is the most useful thing one process can
    compute about the rest of them.
    """
    floor = max(0.0, float(tier_floor or 0))
    observed = max(0.0, float(observed_rate or 0))
    if not throttled:
        return (None,
                "nothing was throttled, so nothing is implied about other callers. "
                "A clean sample is not proof the bucket is yours alone; it is "
                "proof it was not empty in the seconds you looked.")
    if observed <= 0:
        return (None, "throttled at an observed rate of zero, which means the "
                      "sample never got a call away. Nothing to subtract from.")
    if observed >= floor:
        return (None,
                "throttled at %.1f/min against a floor of %.0f/min, which you "
                "reached on your own. This sample says nothing about anybody else."
                % (observed, floor))
    hidden = floor - observed
    others = hidden / observed
    return (others,
            "throttled at %.1f/min against a floor of %.0f/min, so at least "
            "%.1f call(s) a minute on this method came from somewhere other than "
            "this process. That is roughly %.1f more caller(s) at your rate, and "
            "finding them is the job." % (observed, floor, hidden, others))


def herd_window(replicas, retry_after, jitter_fraction=0.0):
    """How tightly the pool's retries land together. Pure.

    Returns (width, first_wave, verdict, detail). Slack hands every refused
    caller the same Retry-After because the window belongs to the window and not
    to the caller, so uniform backoff is exactly the wrong shape: it guarantees
    the pool wakes in lockstep.
    """
    try:
        replicas = max(1, int(replicas))
    except (TypeError, ValueError):
        replicas = 1
    try:
        retry_after = max(0.0, float(retry_after))
    except (TypeError, ValueError):
        retry_after = 0.0
    try:
        jitter = min(1.0, max(0.0, float(jitter_fraction)))
    except (TypeError, ValueError):
        jitter = 0.0

    width = retry_after * jitter
    if width <= 0:
        return (0.0, replicas, "thundering-herd",
                "no jitter, so the retry window has zero width and all %d "
                "replica(s) wake in the same millisecond. The first calls of the "
                "new window are spent instantly and the rest are refused "
                "together, which re-forms the herd on the next Retry-After."
                % replicas)
    first = max(1, int(round(replicas * min(1.0, BURST / width))))
    verdict = "thundering-herd" if first >= 2 else "de-synchronised"
    return (width, first, verdict,
            "retries spread over %.1fs, about %d in the first %.0fms"
            % (width, first, BURST * 1000))


def paced_sample(session, method, params, samples, spacing):
    """A deliberately slow read loop. GET only.

    Spacing is floored: this audit will not add meaningful load to the bucket it
    is measuring, and it will not chase a 429 to prove one exists.
    """
    spacing = max(MIN_SPACING, float(spacing))
    throttled = 0
    started = time.monotonic()
    made = 0
    for i in range(max(1, int(samples))):
        if i:
            time.sleep(spacing)
        res = session.get(API + method, params=params, timeout=30)
        made += 1
        try:
            body = res.json()
        except ValueError:
            body = {}
        if res.status_code == 429 or body.get("error") == "ratelimited":
            throttled += 1
    elapsed = max(1e-6, time.monotonic() - started)
    return (made, throttled, made / elapsed * 60.0, spacing)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--identities", default="",
                    help="JSON list of [label, auth.test body] from each process")
    ap.add_argument("--workers", default="",
                    help="JSON list of {label, calls_per_minute, replicas}")
    ap.add_argument("--tier-floor", type=float, default=20.0,
                    help="documented requests per minute for the method under audit")
    ap.add_argument("--method", default="conversations.list",
                    help="read method to sample")
    ap.add_argument("--samples", type=int, default=5, help="calls in the sample")
    ap.add_argument("--spacing", type=float, default=5.0,
                    help="seconds between sample calls, floored at 3")
    ap.add_argument("--replicas", type=int, default=1,
                    help="how many copies of this process run")
    ap.add_argument("--retry-after", type=float, default=30.0,
                    help="the Retry-After they all received")
    ap.add_argument("--jitter", type=float, default=0.0,
                    help="jitter as a fraction of the wait, 0 for none")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--no-sample", action="store_true",
                    help="skip the live half and do the arithmetic only")
    args = ap.parse_args()

    findings = 0

    identities = []
    if args.identities:
        identities = json.loads(open(args.identities, encoding="utf-8").read())
    groups = same_bucket(identities)
    verdict, detail = bucket_verdict(groups)
    if verdict == "one-bucket":
        findings += 1
        log.warning("bucket     %-17s %s", verdict, detail)
        log.warning("  repair: one shared token bucket in front of Slack, in Redis "
                    "or in a single sender service. A limiter inside each process "
                    "can only enforce a rate it can see")
    else:
        log.info("bucket     %-17s %s", verdict, detail)

    if args.workers:
        workers = json.loads(open(args.workers, encoding="utf-8").read())
        total = aggregate_rate(workers)
        fan, share, fan_detail = fanout_verdict(total, args.tier_floor)
        if fan == "headroom":
            log.info("fanout     %-17s %.1f/min across %d caller(s) against a floor "
                     "of %.0f/min", fan, total, len(workers), args.tier_floor)
        else:
            findings += 1
            log.warning("fanout     %-17s %s", fan, fan_detail)
            log.warning("  repair: concurrency is a divisor here, not a multiplier. "
                        "Parallelise across channels or workspaces, which have more "
                        "than one bucket, rather than across workers on one method")

    if not args.no_sample:
        token = os.environ.get(args.token_env)
        if not token:
            log.error("set %s, or pass --no-sample", args.token_env)
            return 2
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        identity = s.get(API + "auth.test", timeout=30).json()
        if identity.get("ok") is not True:
            log.error("auth.test answered ok: false, error=%s", identity.get("error"))
            return 2
        log.info("identity   %s bot %s in %s", identity.get("user_id"),
                 identity.get("bot_id"), identity.get("team"))

        made, throttled, rate, spacing = paced_sample(
            s, args.method, {"limit": 1, "exclude_archived": "true"},
            args.samples, args.spacing)
        log.info("sample     %d call(s) at %.1fs spacing, %d throttled",
                 made, spacing, throttled)
        others, why = implied_competitors(rate, args.tier_floor, throttled > 0)
        if others is None:
            log.info("competitors  %s", why)
        else:
            findings += 1
            log.warning("competitors  %s", why)

    width, first, herd, herd_detail = herd_window(args.replicas, args.retry_after,
                                                  args.jitter)
    if herd == "thundering-herd" and args.replicas > 1:
        findings += 1
        log.warning("herd       %-17s %s", herd, herd_detail)
        log.warning("  repair: add jitter to every backoff. Uniform, correct, "
                    "documented backoff synchronises the pool, because Slack gives "
                    "every caller the same number")
    else:
        log.info("herd       %-17s %s", herd, herd_detail)

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-shared-quota-audit.mjs",
"js": '''/**
 * Find out how many callers are sharing one Slack rate-limit bucket.
 *
 * Read only. Slack keys its quota on method, workspace and app, so replicas of
 * one deployment share a single budget and adding workers to a throttled job
 * makes it slower. This groups auth.test bodies by that key, adds up the fan-out
 * against the documented tier floor, takes a deliberately slow sample to see
 * whether the bucket is already empty, and measures how tightly the pool's
 * retries synchronise.
 *
 * The sample is paced well below the tier and refuses to go faster.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// The sample will not go faster than this, whatever the flags say.
const MIN_SPACING = 3.0;

// Retries landing inside this window of each other are one wave, not a spread.
const BURST = 0.1;

/**
 * Group callers by the key Slack's quota actually uses. Pure.
 * identities: [[label, authTestBody], ...].
 */
export function sameBucket(identities) {
  const groups = new Map();
  for (const [label, body] of identities ?? []) {
    const doc = (body && typeof body === 'object') ? body : {};
    const team = String(doc.team_id ?? '').trim() || 'unknown-team';
    let actor = String(doc.bot_id ?? '').trim();
    if (!actor) actor = String(doc.user_id ?? '').trim() || 'unknown-app';
    const key = `${team}/${actor}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(String(label));
  }
  return groups;
}

/** Say whether anything is sharing. Pure. Returns [verdict, detail]. */
export function bucketVerdict(groups) {
  if (!groups || groups.size === 0) {
    return ['nothing-supplied',
      'no identities were given, so the sharing question is unanswered. One ' +
      'auth.test per process, saved with a label, is the whole input and it is ' +
      'the evidence that ends the argument.'];
  }
  const shared = [...groups.entries()].filter(([, labels]) => labels.length > 1);
  if (shared.length === 0) {
    return ['separate-buckets',
      `${groups.size} group(s), no two callers share a workspace and app`];
  }
  const biggest = shared.reduce((a, b) => (b[1].length > a[1].length ? b : a));
  return ['one-bucket',
    `${biggest[1].length} caller(s) share the key ${biggest[0]}: ` +
    `${biggest[1].join(', ')}. Slack sees one app in one workspace, so they ` +
    'hold one budget between them however many hosts they run on.'];
}

/** Total calls per minute against one method. Pure. */
export function aggregateRate(workers) {
  let total = 0;
  for (const worker of workers ?? []) {
    const rate = Number(worker?.calls_per_minute ?? 0);
    const replicas = Math.max(1, Math.trunc(Number(worker?.replicas ?? 1) || 1));
    total += Math.max(0, Number.isFinite(rate) ? rate : 0) * replicas;
  }
  return total;
}

/** The pool's demand against the method's floor. Pure. Returns [verdict, share, detail]. */
export function fanoutVerdict(totalRate, tierFloor) {
  const floor = Math.max(1, Number(tierFloor) || 1);
  const share = Number(totalRate) / floor;
  if (share > 1.0) {
    return ['saturated', share,
      `${totalRate.toFixed(1)}/min across the pool against a floor of ` +
      `${floor.toFixed(0)}/min. The pool is asking for ${share.toFixed(1)} times ` +
      'the budget, so its real throughput is the floor and the extra workers buy ' +
      'queueing rather than work.'];
  }
  if (share > 0.8) {
    return ['at-the-edge', share,
      `${totalRate.toFixed(1)}/min across the pool against a floor of ` +
      `${floor.toFixed(0)}/min. One more replica, or one retry storm, puts it over.`];
  }
  return ['headroom', share,
    `${totalRate.toFixed(1)}/min against a floor of ${floor.toFixed(0)}/min`];
}

/**
 * Callers you cannot see, inferred by subtraction. Pure.
 * Returns [others, detail]; others is a multiple of your own rate, or null.
 */
export function impliedCompetitors(observedRate, tierFloor, throttled) {
  const floor = Math.max(0, Number(tierFloor) || 0);
  const observed = Math.max(0, Number(observedRate) || 0);
  if (!throttled) {
    return [null,
      'nothing was throttled, so nothing is implied about other callers. A clean ' +
      'sample is not proof the bucket is yours alone; it is proof it was not ' +
      'empty in the seconds you looked.'];
  }
  if (observed <= 0) {
    return [null, 'throttled at an observed rate of zero, which means the sample ' +
      'never got a call away. Nothing to subtract from.'];
  }
  if (observed >= floor) {
    return [null,
      `throttled at ${observed.toFixed(1)}/min against a floor of ` +
      `${floor.toFixed(0)}/min, which you reached on your own. This sample says ` +
      'nothing about anybody else.'];
  }
  const hidden = floor - observed;
  const others = hidden / observed;
  return [others,
    `throttled at ${observed.toFixed(1)}/min against a floor of ` +
    `${floor.toFixed(0)}/min, so at least ${hidden.toFixed(1)} call(s) a minute ` +
    'on this method came from somewhere other than this process. That is roughly ' +
    `${others.toFixed(1)} more caller(s) at your rate, and finding them is the job.`];
}

/**
 * How tightly the pool's retries land together. Pure.
 * Returns [width, firstWave, verdict, detail].
 */
export function herdWindow(replicas, retryAfter, jitterFraction = 0) {
  const count = Math.max(1, Math.trunc(Number(replicas) || 1));
  const wait = Math.max(0, Number(retryAfter) || 0);
  const jitter = Math.min(1, Math.max(0, Number(jitterFraction) || 0));

  const width = wait * jitter;
  if (width <= 0) {
    return [0, count, 'thundering-herd',
      `no jitter, so the retry window has zero width and all ${count} replica(s) ` +
      'wake in the same millisecond. The first calls of the new window are spent ' +
      'instantly and the rest are refused together, which re-forms the herd on ' +
      'the next Retry-After.'];
  }
  const first = Math.max(1, Math.round(count * Math.min(1, BURST / width)));
  const verdict = first >= 2 ? 'thundering-herd' : 'de-synchronised';
  return [width, first, verdict,
    `retries spread over ${width.toFixed(1)}s, about ${first} in the first ` +
    `${(BURST * 1000).toFixed(0)}ms`];
}

const sleep = (ms) => new Promise((resolve) => { setTimeout(resolve, ms); });

/** A deliberately slow read loop. GET only, and spacing is floored. */
async function pacedSample(token, method, params, samples, spacing) {
  const gap = Math.max(MIN_SPACING, Number(spacing) || MIN_SPACING);
  const qs = new URLSearchParams(params);
  let throttled = 0;
  let made = 0;
  const started = Date.now();
  for (let i = 0; i < Math.max(1, Math.trunc(samples)); i += 1) {
    if (i) await sleep(gap * 1000);
    const res = await fetch(`${API}${method}?${qs}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    made += 1;
    let body = {};
    try { body = await res.json(); } catch { body = {}; }
    if (res.status === 429 || body.error === 'ratelimited') throttled += 1;
  }
  const elapsed = Math.max(1e-6, (Date.now() - started) / 1000);
  return [made, throttled, (made / elapsed) * 60, gap];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const tierFloor = Number(arg(args, '--tier-floor', 20));
  let findings = 0;

  const identitiesFile = arg(args, '--identities', '');
  const identities = identitiesFile
    ? JSON.parse(await readFile(identitiesFile, 'utf8')) : [];
  const groups = sameBucket(identities);
  const [verdict, detail] = bucketVerdict(groups);
  if (verdict === 'one-bucket') {
    findings += 1;
    console.warn(`bucket     ${verdict.padEnd(17)} ${detail}`);
    console.warn('  repair: one shared token bucket in front of Slack, in Redis or ' +
      'in a single sender service. A limiter inside each process can only enforce ' +
      'a rate it can see');
  } else {
    console.log(`bucket     ${verdict.padEnd(17)} ${detail}`);
  }

  const workersFile = arg(args, '--workers', '');
  if (workersFile) {
    const workers = JSON.parse(await readFile(workersFile, 'utf8'));
    const total = aggregateRate(workers);
    const [fan, , fanDetail] = fanoutVerdict(total, tierFloor);
    if (fan === 'headroom') {
      console.log(`fanout     ${fan.padEnd(17)} ${total.toFixed(1)}/min across ` +
        `${workers.length} caller(s) against a floor of ${tierFloor}/min`);
    } else {
      findings += 1;
      console.warn(`fanout     ${fan.padEnd(17)} ${fanDetail}`);
      console.warn('  repair: concurrency is a divisor here, not a multiplier. ' +
        'Parallelise across channels or workspaces, which have more than one ' +
        'bucket, rather than across workers on one method');
    }
  }

  if (!args.includes('--no-sample')) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    const token = process.env[tokenEnv];
    if (!token) {
      console.error(`set ${tokenEnv}, or pass --no-sample`);
      process.exitCode = 2;
      return;
    }
    const res = await fetch(`${API}auth.test`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const identity = await res.json();
    if (identity.ok !== true) {
      console.error(`auth.test answered ok: false, error=${identity.error}`);
      process.exitCode = 2;
      return;
    }
    console.log(`identity   ${identity.user_id} bot ${identity.bot_id} in ` +
      `${identity.team}`);

    const [made, throttled, rate, gap] = await pacedSample(
      token, arg(args, '--method', 'conversations.list'),
      { limit: '1', exclude_archived: 'true' },
      Number(arg(args, '--samples', 5)), Number(arg(args, '--spacing', 5)));
    console.log(`sample     ${made} call(s) at ${gap.toFixed(1)}s spacing, ` +
      `${throttled} throttled`);
    const [others, why] = impliedCompetitors(rate, tierFloor, throttled > 0);
    if (others === null) {
      console.log(`competitors  ${why}`);
    } else {
      findings += 1;
      console.warn(`competitors  ${why}`);
    }
  }

  const replicas = Number(arg(args, '--replicas', 1));
  const [, , herd, herdDetail] = herdWindow(replicas,
    Number(arg(args, '--retry-after', 30)), Number(arg(args, '--jitter', 0)));
  if (herd === 'thundering-herd' && replicas > 1) {
    findings += 1;
    console.warn(`herd       ${herd.padEnd(17)} ${herdDetail}`);
    console.warn('  repair: add jitter to every backoff. Uniform, correct, ' +
      'documented backoff synchronises the pool, because Slack gives every ' +
      'caller the same number');
  } else {
    console.log(`herd       ${herd.padEnd(17)} ${herdDetail}`);
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixture that matters is four <code>auth.test</code> bodies: two replicas of the same deployment, a cron box holding a second token of the same app, and a staging install in another workspace. The tests pin that the first three land in one group and the fourth does not, which is the whole claim. The rest pin the arithmetic: subtraction only produces a headcount when the sample was actually throttled below the floor, and uniform backoff is reported as a herd rather than as correct behaviour.",
"test_py_file": "test_slack_shared_quota_audit.py",
"test_py": '''from slack_shared_quota_audit import (aggregate_rate, bucket_verdict,
                                        fanout_verdict, herd_window,
                                        implied_competitors, same_bucket)

# One app, one workspace, three processes. The third holds a different token of
# the same app, which is the case people are most confident is separate.
WORKER_A = {"ok": True, "team_id": "T0ACME1234", "bot_id": "B0APPBOT99",
            "user_id": "U0APPBOT11"}
WORKER_B = {"ok": True, "team_id": "T0ACME1234", "bot_id": "B0APPBOT99",
            "user_id": "U0APPBOT11"}
CRON_BOX = {"ok": True, "team_id": "T0ACME1234", "bot_id": "B0APPBOT99",
            "user_id": "U0APPBOT11"}
STAGING = {"ok": True, "team_id": "T0STAGE999", "bot_id": "B0APPBOT99",
           "user_id": "U0APPBOT11"}


def test_replicas_of_one_deployment_land_in_one_group():
    groups = same_bucket([("worker-a", WORKER_A), ("worker-b", WORKER_B),
                          ("cron", CRON_BOX)])
    assert list(groups) == ["T0ACME1234/B0APPBOT99"]
    assert groups["T0ACME1234/B0APPBOT99"] == ["worker-a", "worker-b", "cron"]


def test_a_different_workspace_is_a_different_bucket():
    groups = same_bucket([("prod", WORKER_A), ("staging", STAGING)])
    assert len(groups) == 2


def test_sharing_is_the_finding_and_is_named_with_its_members():
    groups = same_bucket([("worker-a", WORKER_A), ("worker-b", WORKER_B),
                          ("staging", STAGING)])
    verdict, detail = bucket_verdict(groups)
    assert verdict == "one-bucket"
    assert "worker-a, worker-b" in detail
    assert "staging" not in detail


def test_no_sharing_and_no_input_are_different_answers():
    assert bucket_verdict(same_bucket([("prod", WORKER_A)]))[0] == "separate-buckets"
    assert bucket_verdict({})[0] == "nothing-supplied"


def test_a_user_token_without_a_bot_id_still_gets_a_key():
    groups = same_bucket([("script", {"team_id": "T0ACME1234", "user_id": "U0HUMAN1"})])
    assert list(groups) == ["T0ACME1234/U0HUMAN1"]
    assert list(same_bucket([("mystery", {})])) == ["unknown-team/unknown-app"]


def test_replicas_multiply_the_rate_they_were_given():
    workers = [{"label": "worker", "calls_per_minute": 5, "replicas": 8},
               {"label": "cron", "calls_per_minute": 2}]
    assert aggregate_rate(workers) == 42.0
    assert aggregate_rate([]) == 0.0
    assert aggregate_rate([{"calls_per_minute": "many"}]) == 0.0


def test_the_pool_is_saturated_when_the_total_passes_the_floor():
    verdict, share, detail = fanout_verdict(42.0, 20)
    assert verdict == "saturated"
    assert round(share, 1) == 2.1
    assert "divisor" not in detail
    assert "queueing rather than work" in detail


def test_the_edge_and_the_headroom_are_separate_verdicts():
    assert fanout_verdict(18.0, 20)[0] == "at-the-edge"
    assert fanout_verdict(8.0, 20)[0] == "headroom"


def test_throttling_below_the_floor_implies_callers_you_cannot_see():
    others, detail = implied_competitors(12.0, 20, True)
    assert round(others, 2) == 0.67
    assert "8.0 call(s) a minute" in detail


def test_a_clean_sample_implies_nothing_at_all():
    others, detail = implied_competitors(12.0, 20, False)
    assert others is None
    assert "not proof the bucket is yours alone" in detail


def test_reaching_the_floor_yourself_is_not_evidence_of_anybody_else():
    others, _ = implied_competitors(25.0, 20, True)
    assert others is None
    assert implied_competitors(0.0, 20, True)[0] is None


def test_uniform_backoff_is_reported_as_a_herd():
    width, first, verdict, detail = herd_window(8, 30, 0.0)
    assert width == 0.0
    assert first == 8
    assert verdict == "thundering-herd"
    assert "same millisecond" in detail


def test_jitter_spreads_the_pool_across_the_window():
    width, first, verdict, _ = herd_window(8, 30, 0.5)
    assert width == 15.0
    assert first == 1
    assert verdict == "de-synchronised"


def test_a_single_replica_cannot_form_a_herd_worth_reporting():
    assert herd_window(1, 30, 0.0)[1] == 1
    assert herd_window("eight", "soon", "none")[2] == "thundering-herd"
''',
"test_js_file": "slack-shared-quota-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { aggregateRate, bucketVerdict, fanoutVerdict, herdWindow,
  impliedCompetitors, sameBucket } from './slack-shared-quota-audit.mjs';

// One app, one workspace, three processes. The third holds a different token of
// the same app, which is the case people are most confident is separate.
const WORKER_A = { ok: true, team_id: 'T0ACME1234', bot_id: 'B0APPBOT99',
  user_id: 'U0APPBOT11' };
const WORKER_B = { ...WORKER_A };
const CRON_BOX = { ...WORKER_A };
const STAGING = { ok: true, team_id: 'T0STAGE999', bot_id: 'B0APPBOT99',
  user_id: 'U0APPBOT11' };

test('replicas of one deployment land in one group', () => {
  const groups = sameBucket([['worker-a', WORKER_A], ['worker-b', WORKER_B],
    ['cron', CRON_BOX]]);
  assert.deepEqual([...groups.keys()], ['T0ACME1234/B0APPBOT99']);
  assert.deepEqual(groups.get('T0ACME1234/B0APPBOT99'),
    ['worker-a', 'worker-b', 'cron']);
});

test('a different workspace is a different bucket', () => {
  assert.equal(sameBucket([['prod', WORKER_A], ['staging', STAGING]]).size, 2);
});

test('sharing is the finding and is named with its members', () => {
  const groups = sameBucket([['worker-a', WORKER_A], ['worker-b', WORKER_B],
    ['staging', STAGING]]);
  const [verdict, detail] = bucketVerdict(groups);
  assert.equal(verdict, 'one-bucket');
  assert.match(detail, /worker-a, worker-b/);
  assert.ok(!detail.includes('staging'));
});

test('no sharing and no input are different answers', () => {
  assert.equal(bucketVerdict(sameBucket([['prod', WORKER_A]]))[0], 'separate-buckets');
  assert.equal(bucketVerdict(new Map())[0], 'nothing-supplied');
});

test('a user token without a bot id still gets a key', () => {
  const groups = sameBucket([['script', { team_id: 'T0ACME1234', user_id: 'U0HUMAN1' }]]);
  assert.deepEqual([...groups.keys()], ['T0ACME1234/U0HUMAN1']);
  assert.deepEqual([...sameBucket([['mystery', {}]]).keys()],
    ['unknown-team/unknown-app']);
});

test('replicas multiply the rate they were given', () => {
  const workers = [{ label: 'worker', calls_per_minute: 5, replicas: 8 },
    { label: 'cron', calls_per_minute: 2 }];
  assert.equal(aggregateRate(workers), 42);
  assert.equal(aggregateRate([]), 0);
  assert.equal(aggregateRate([{ calls_per_minute: 'many' }]), 0);
});

test('the pool is saturated when the total passes the floor', () => {
  const [verdict, share, detail] = fanoutVerdict(42, 20);
  assert.equal(verdict, 'saturated');
  assert.equal(Number(share.toFixed(1)), 2.1);
  assert.match(detail, /queueing rather than work/);
});

test('the edge and the headroom are separate verdicts', () => {
  assert.equal(fanoutVerdict(18, 20)[0], 'at-the-edge');
  assert.equal(fanoutVerdict(8, 20)[0], 'headroom');
});

test('throttling below the floor implies callers you cannot see', () => {
  const [others, detail] = impliedCompetitors(12, 20, true);
  assert.equal(Number(others.toFixed(2)), 0.67);
  assert.match(detail, /8\\.0 call\\(s\\) a minute/);
});

test('a clean sample implies nothing at all', () => {
  const [others, detail] = impliedCompetitors(12, 20, false);
  assert.equal(others, null);
  assert.match(detail, /not proof the bucket is yours alone/);
});

test('reaching the floor yourself is not evidence of anybody else', () => {
  assert.equal(impliedCompetitors(25, 20, true)[0], null);
  assert.equal(impliedCompetitors(0, 20, true)[0], null);
});

test('uniform backoff is reported as a herd', () => {
  const [width, first, verdict, detail] = herdWindow(8, 30, 0);
  assert.equal(width, 0);
  assert.equal(first, 8);
  assert.equal(verdict, 'thundering-herd');
  assert.match(detail, /same millisecond/);
});

test('jitter spreads the pool across the window', () => {
  const [width, first, verdict] = herdWindow(8, 30, 0.5);
  assert.equal(width, 15);
  assert.equal(first, 1);
  assert.equal(verdict, 'de-synchronised');
});

test('a single replica cannot form a herd worth reporting', () => {
  assert.equal(herdWindow(1, 30, 0)[1], 1);
  assert.equal(herdWindow('eight', 'soon', 'none')[2], 'thundering-herd');
});
''',
"faq": [
 ("Does giving each worker its own token split the quota?",
  "No. Slack keys the limit on the app and the workspace, not on the token, so two tokens belonging to the same app in the same workspace draw on one bucket. That is the case people are most confident is separate, and it is the reason the audit groups on team_id and bot_id rather than on the credential."),
 ("How do I find the caller nobody remembers deploying?",
  "By subtraction. Take a paced sample well under the documented floor; if it is refused anyway, the difference between the floor and your own rate is traffic from somewhere else. Expressed as a multiple of your rate it is roughly a headcount, and it is usually a staging deployment still pointed at production, an analytics cron, or a laptop."),
 ("Is exponential backoff enough if every worker implements it correctly?",
  "Correctly is the problem. Slack hands every refused caller the same Retry-After, so identical, correct backoff makes the pool wake in lockstep and empty the new window in its first milliseconds. Jitter is not a refinement here; without it the workers cannot de-synchronise, and the herd re-forms on every refusal."),
 ("Where should the shared limiter live?",
  "Somewhere all callers meet: a token bucket in Redis, or a single sender service everything else queues into. The rule is that the limiter has to see every call the app makes, which no in-process limiter can. A sender service is usually the smaller change, because it also gives you one place to add batching and one place to log."),
 ("Is there any axis where more concurrency does help?",
  "Yes, where there is genuinely more than one bucket. chat.postMessage is limited per channel, so posting into N channels means N envelopes and parallelism is real. Separate workspaces are separate buckets too. Across workers hitting the same method in the same workspace there is exactly one, and adding workers divides it."),
],
"related": [
 ("/slack/tier1-method-hammered/", "the budget one process is spending"),
 ("/slack/ratelimited-retry-after-ignored/", "the header every replica reads the same way"),
 ("/slack/enterprise-id-not-stored/", "installs keyed on team_id alone collide"),
],
"citations": [CITE_RATE_LIMITS, CITE_AUTH_TEST, CITE_CONV_LIST, CITE_WEB_API],
},

]
