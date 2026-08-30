#!/usr/bin/env python3
"""/slack/ field notes, batch B — the writing.

Four problems whose evidence is already sitting in the workspace. Three of them
read `conversations.history` and one reads `files.list`, and in every case the
finding is a grouping the API will not do for you: identical messages collapsed
by content, runs of self-authored messages measured in order, files sorted by
which visibility flag is set, a page counted against the size that was asked for.

Read-only throughout. These scripts hold a bot token that can post into your
workspace, so none of them writes: they report what is wrong and print the
repair. The last note has no API repair at all, and says so.
"""

CITE_HISTORY = ("conversations.history method — Slack API",
                "https://docs.slack.dev/reference/methods/conversations.history")
CITE_POSTMESSAGE = ("chat.postMessage method — Slack API",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_UPDATE = ("chat.update method — Slack API",
               "https://docs.slack.dev/reference/methods/chat.update")
CITE_EVENTS = ("The Events API — Slack docs", "https://docs.slack.dev/apis/events-api/")
CITE_MESSAGE_EVENT = ("The message event — Slack API",
                      "https://docs.slack.dev/reference/events/message")
CITE_APP_MENTION = ("The app_mention event — Slack API",
                    "https://docs.slack.dev/reference/events/app_mention")
CITE_AUTH_TEST = ("auth.test method — Slack API",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_FILES_LIST = ("files.list method — Slack API",
                   "https://docs.slack.dev/reference/methods/files.list")
CITE_FILES_PUBLIC = ("files.sharedPublicURL method — Slack API",
                     "https://docs.slack.dev/reference/methods/files.sharedPublicURL")
CITE_FILES_REVOKE = ("files.revokePublicURL method — Slack API",
                     "https://docs.slack.dev/reference/methods/files.revokePublicURL")
CITE_FILES_INFO = ("files.info method — Slack API",
                   "https://docs.slack.dev/reference/methods/files.info")
CITE_CLAMP = ("Rate limit changes for non-Marketplace apps — Slack changelog",
              "https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps/")
CITE_CLAMP_CLARITY = ("More clarity on the rate limit changes — Slack changelog",
                      "https://docs.slack.dev/changelog/2025/06/03/rate-limits-clarity/")
CITE_RATE_LIMITS = ("Rate limits — Slack API",
                    "https://docs.slack.dev/apis/web-api/rate-limits")

GUIDES = [

{
"slug": "duplicate-messages-no-dedupe",
"title": "The same message posted three times, and the ts says why",
"description": "Slack has no idempotency key, so every duplicate is a real second call. The gap between the copies names the cause: a double subscription or a retry.",
"h1": "the same message posted three times, and the ts says why",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack duplicate messages", "slack bot posts twice",
             "chat.postMessage idempotency", "slack event retry duplicate",
             "slack deduplicate event_id"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The alert channel has the same incident in it four times. Every one of those messages is a real, successful <code>chat.postMessage</code> call that returned <code>ok: true</code> and a distinct <code>ts</code>, so nothing failed and nothing will appear in your error tracker. The duplicates are not a display bug &mdash; they are four separate decisions your system made to send, and the record of all four is sitting in <code>conversations.history</code> waiting to be read.",
"short_answer": """<p>Page <code>conversations.history?channel=C...&amp;limit=200</code> for each channel the app posts to, keep the messages whose <code>bot_id</code> matches <code>auth.test</code>, group them by a hash of <code>text</code> plus <code>blocks</code>, and report every group with more than one member.</p>
<p>Then read the gaps between the copies, because the spacing is the diagnosis. Under a second apart means two delivery paths handled the same event. Roughly 60 or 300 seconds apart means Slack retried an unacknowledged event and your handler was not idempotent on <code>event_id</code>. Hours apart means two scheduler runs overlapped.</p>""",
"problem": """<p>Slack will not help you here. <code>chat.postMessage</code> has no <code>Idempotency-Key</code> header and no client-supplied token that the platform will honour to collapse repeats. Unlike a payments API, where sending the same key twice is defined to be safe, every call to Slack creates a new message unconditionally. Any at-least-once mechanism anywhere upstream of the send &mdash; event retries, queue redelivery, cron overlap, two replicas of the same worker &mdash; lands in the channel as visible duplication.</p>
<p>The damage is not really the clutter. It is that duplicated messages usually mean duplicated <em>side effects</em>: the page was sent twice, the ticket was opened twice, the refund path ran twice. The channel is just the only place the double-execution is visible, which makes it the cheapest place to detect it. Everything else about the failure is inside your process and unobservable.</p>""",
"why": """<p><strong>There is no idempotency key to reach for.</strong> The method reference lists no such parameter, and no header is honoured. Deduplication has to happen in your code, before the call, or it does not happen.</p>
<p><strong>Slack retries events on a schedule you can recognise.</strong> If your Request URL does not answer <code>200</code> within three seconds, Slack redelivers the same event with an incremented <code>X-Slack-Retry-Num</code> and a <code>X-Slack-Retry-Reason</code> of <code>http_timeout</code>. The redeliveries are spaced roughly a minute and then five minutes out. A handler that does the work first and acknowledges afterwards will complete the work every time it is asked.</p>
<p><strong>Two subscriptions to the same message look nothing like a retry.</strong> An app subscribed to both <code>app_mention</code> and <code>message.channels</code> receives two events for one mention, delivered simultaneously. Socket Mode running locally while an HTTP Request URL is still configured does the same thing. Those copies land sub-second apart, and no amount of <code>event_id</code> deduplication fixes them, because the two events have different ids.</p>
<p><strong>The spacing is the only free discriminator.</strong> From the outside, all three causes produce identical text in the same channel. The <code>ts</code> values are the one piece of evidence that separates them, and they are already stored.</p>""",
"steps": [
 {"h": "Establish who the app is",
  "body": """<p><code>auth.test</code> returns <code>bot_id</code> and <code>user_id</code> for the token you are holding. Everything downstream filters on those, because the interesting duplication is your own; two humans posting the same sentence is not a finding.</p>"""},
 {"h": "Read history for the channels the app posts to",
  "body": """<p><code>users.conversations?limit=200</code> gives the channels the bot is a member of, and <code>conversations.history?channel=C...&amp;limit=200</code> gives the messages. Follow <code>response_metadata.next_cursor</code> if you want more than a page. If a page comes back with exactly 15 messages, stop and read the note on the <a href="/slack/non-marketplace-history-clamp/">non-Marketplace history clamp</a> first &mdash; your sample is smaller than you think.</p>"""},
 {"h": "Group on content, not on text alone",
  "body": """<p>Block Kit messages routinely carry an identical <code>text</code> fallback (“New alert”) while the blocks differ completely. Hashing <code>text</code> on its own merges unrelated alerts into one enormous fake duplicate group. Hash the serialized <code>blocks</code> alongside it, and leave <code>ts</code> out, since that is the field guaranteed to differ.</p>"""},
 {"h": "Read the gaps and name the cause",
  "body": """<p>Sub-second: two delivery paths. About 60 or 300 seconds: Slack retried and you processed it twice. Half an hour or more: a scheduler ran twice. Anything else stays unclassified rather than being forced into a bucket &mdash; a wrong diagnosis costs more than an honest “duplicated, cause unclear”.</p>"""},
 {"h": "Fix at the cause the spacing named",
  "body": """<p>For retries, store <code>event.event_id</code> in a short-TTL set and return early on a hit; acknowledge inside three seconds and do the work asynchronously. For double delivery, drop one subscription or turn off one transport. For scheduler overlap, take a lock. For status that changes, post once and call <code>chat.update</code> on the same <code>ts</code> instead of posting again.</p>"""},
],
"verify": """<p>Re-run over the same channels after the guard is in place. Every group should report <code>unique</code>.</p>
<pre><code class="language-bash">python3 slack_duplicate_messages.py --limit 200
# 6 channel(s), 412 app-authored message(s), 0 duplicate group(s)</code></pre>""",
"code_intro": "Two GET methods and nothing else &mdash; <code>auth.test</code>, <code>users.conversations</code> and <code>conversations.history</code>, which need only <code>channels:read</code> and <code>channels:history</code>. Both judgement calls are pure functions: the fingerprint that decides when two messages are the same message, and the classifier that turns a list of timestamps into a named cause. Neither touches the network, so both are tested directly.",
"py_file": "slack_duplicate_messages.py",
"py": '''"""Find app-authored Slack messages that were posted more than once.

Read only. Three GET methods and no writes: a bot token with channels:read and
channels:history is enough, and is what you should give it. The repair is
printed, never performed, because this token can post into your workspace.
"""
import argparse
import hashlib
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_duplicate_messages")

API = "https://slack.com/api"

# Slack redelivers an event that was not acknowledged in three seconds, once at
# roughly a minute and again at roughly five. Those two numbers are the
# fingerprint of a handler that is not idempotent on event_id.
RETRY_GAPS = (60.0, 300.0)

# Two runs of the same cron job land far enough apart that nothing else explains
# them. Half an hour is deliberately conservative.
RERUN_GAP = 1800.0


def fingerprint(message):
    """Content hash for one message. Pure, so grouping is testable offline.

    Text alone is not enough. A Block Kit message usually carries a short
    fallback in `text` that is identical across every alert the app sends, so
    hashing that field on its own merges unrelated messages into one enormous
    false duplicate group. The serialized blocks go into the hash too. `ts` is
    deliberately excluded: it is the one field guaranteed to differ between two
    copies of the same message.
    """
    payload = json.dumps([message.get("text") or "", message.get("blocks") or []],
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def near(gap, target, tolerance):
    """True when `gap` is within `tolerance` (a fraction) of `target`."""
    return abs(gap - target) <= target * tolerance


def classify(timestamps, *, tolerance=0.25):
    """Name the cause of one duplicate group from the spacing of its copies.

    Pure, so the thresholds are visible and testable rather than buried in a
    request loop. `timestamps` are Slack `ts` values, as strings or floats.

    Returns (state, detail). The states are the causes, because the repairs are
    different for each: a retry needs an event_id check, a double delivery needs
    a subscription removed, an overlapping cron needs a lock. A group whose
    spacing matches none of them is reported as unclassified rather than pushed
    into the nearest bucket.
    """
    ts = sorted(float(t) for t in timestamps)
    n = len(ts)
    if n < 2:
        return ("unique", "one message, nothing to explain")

    gaps = [b - a for a, b in zip(ts, ts[1:])]
    span = ts[-1] - ts[0]

    if max(gaps) < 1.0:
        return ("double-delivery",
                "%d copies inside %.2fs. Sub-second spacing is two delivery "
                "paths handling one event, not a retry: app_mention and "
                "message.channels both subscribed, or Socket Mode running "
                "alongside a live Request URL." % (n, span))

    if all(any(near(g, r, tolerance) for r in RETRY_GAPS) for g in gaps):
        return ("retry-duplicate",
                "%d copies spaced %s. That is Slack's retry schedule: the "
                "handler did not acknowledge inside three seconds and did the "
                "work again on redelivery."
                % (n, ", ".join("%.0fs" % g for g in gaps)))

    if min(gaps) >= RERUN_GAP:
        return ("rerun",
                "%d copies over %.1f hour(s). Too far apart for a retry: two "
                "scheduler runs, a redeployed worker replaying a queue, or a "
                "backfill run twice." % (n, span / 3600.0))

    return ("duplicated",
            "%d copies over %.1fs, spacing matches no known cause. Worth reading "
            "by hand before you change anything." % (n, span))


def call(session, method, **params):
    """One Web API read. Slack answers almost every failure with HTTP 200 and
    puts the error in the body, so the body is what gets asserted on."""
    r = session.get("%s/%s" % (API, method), params=params, timeout=30)
    r.raise_for_status()
    body = r.json()
    if not body.get("ok"):
        raise SystemExit("%s: %s (needed=%s provided=%s)"
                         % (method, body.get("error"), body.get("needed"),
                            body.get("provided")))
    return body


def channels(session, explicit):
    if explicit:
        return [{"id": c, "name": c} for c in explicit]
    out, cursor = [], ""
    while True:
        body = call(session, "users.conversations", limit=200,
                    types="public_channel,private_channel", cursor=cursor)
        out.extend(body.get("channels", []))
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return out


def history(session, channel_id, limit):
    out, cursor = [], ""
    while len(out) < limit:
        body = call(session, "conversations.history", channel=channel_id,
                    limit=min(200, limit - len(out)), cursor=cursor)
        out.extend(body.get("messages", []))
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channel", action="append", default=[],
                    help="channel id to read; repeatable. Default: every channel "
                         "the bot is a member of")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages to read per channel")
    ap.add_argument("--tolerance", type=float, default=0.25,
                    help="how far a gap may sit from 60s or 300s and still count "
                         "as a Slack retry")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (a bot token with channels:read and "
                  "channels:history is enough)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    me = call(session, "auth.test")
    bot_id, user_id = me.get("bot_id"), me.get("user_id")
    log.info("authenticated as %s (bot_id=%s) in %s",
             me.get("user"), bot_id, me.get("team"))

    targets = channels(session, args.channel)
    if not targets:
        log.info("the bot is not a member of any conversation")
        return 0

    findings = authored = 0
    for ch in targets:
        messages = history(session, ch["id"], args.limit)
        mine = [m for m in messages
                if (bot_id and m.get("bot_id") == bot_id)
                or (user_id and m.get("user") == user_id)]
        authored += len(mine)

        groups = {}
        for m in mine:
            groups.setdefault(fingerprint(m), []).append(m)

        for key, group in sorted(groups.items()):
            state, detail = classify([m["ts"] for m in group],
                                     tolerance=args.tolerance)
            if state == "unique":
                continue
            findings += 1
            log.warning("%-16s #%s  %s", state, ch.get("name", ch["id"]), detail)
            log.warning("  first ts %s  fingerprint %s", group[0]["ts"], key)
            log.warning("  text: %.90s", (group[0].get("text") or "").replace("\\n", " "))
            if state == "retry-duplicate":
                log.warning("  repair: acknowledge the event inside 3s and do the "
                            "work after; key on event.event_id in a short-TTL set "
                            "and return early on a repeat.")
            elif state == "double-delivery":
                log.warning("  repair: one delivery path per app. Drop either "
                            "app_mention or message.channels, and do not leave a "
                            "Request URL configured while Socket Mode is on.")
            elif state == "rerun":
                log.warning("  repair: take a per-job lock so overlapping runs "
                            "cannot both send, or post once and chat.update the "
                            "same ts as the state changes.")

    log.info("%d channel(s), %d app-authored message(s), %d duplicate group(s)",
             len(targets), authored, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-duplicate-messages.mjs",
"js": '''/**
 * Find app-authored Slack messages that were posted more than once.
 *
 * Read only. Three GET methods and no writes: a bot token with channels:read
 * and channels:history is enough. The repair is printed, never performed.
 */
import { createHash } from 'node:crypto';

const API = 'https://slack.com/api';

// Slack redelivers an event that was not acknowledged in three seconds, once at
// roughly a minute and again at roughly five.
const RETRY_GAPS = [60, 300];

// Two runs of the same cron job land far enough apart that nothing else
// explains them. Half an hour is deliberately conservative.
const RERUN_GAP = 1800;

/**
 * Content hash for one message. Pure, so grouping is testable offline.
 *
 * Text alone is not enough: a Block Kit message usually carries a fallback in
 * `text` that is identical across every alert, so hashing that field on its own
 * merges unrelated messages into one false duplicate group. `ts` is excluded on
 * purpose, being the field guaranteed to differ between copies.
 */
export function fingerprint(message) {
  const payload = JSON.stringify([message.text ?? '', message.blocks ?? []]);
  return createHash('sha256').update(payload).digest('hex').slice(0, 16);
}

function near(gap, target, tolerance) {
  return Math.abs(gap - target) <= target * tolerance;
}

/**
 * Name the cause of one duplicate group from the spacing of its copies.
 *
 * Pure, so the thresholds are visible and testable. Returns [state, detail];
 * a group matching no known spacing is reported as unclassified rather than
 * pushed into the nearest bucket.
 */
export function classify(timestamps, { tolerance = 0.25 } = {}) {
  const ts = timestamps.map(Number).sort((a, b) => a - b);
  const n = ts.length;
  if (n < 2) return ['unique', 'one message, nothing to explain'];

  const gaps = ts.slice(1).map((t, i) => t - ts[i]);
  const span = ts[n - 1] - ts[0];

  if (Math.max(...gaps) < 1) {
    return ['double-delivery',
      `${n} copies inside ${span.toFixed(2)}s. Sub-second spacing is two ` +
      'delivery paths handling one event, not a retry: app_mention and ' +
      'message.channels both subscribed, or Socket Mode running alongside a ' +
      'live Request URL.'];
  }

  if (gaps.every((g) => RETRY_GAPS.some((r) => near(g, r, tolerance)))) {
    return ['retry-duplicate',
      `${n} copies spaced ${gaps.map((g) => `${g.toFixed(0)}s`).join(', ')}. ` +
      "That is Slack's retry schedule: the handler did not acknowledge inside " +
      'three seconds and did the work again on redelivery.'];
  }

  if (Math.min(...gaps) >= RERUN_GAP) {
    return ['rerun',
      `${n} copies over ${(span / 3600).toFixed(1)} hour(s). Too far apart for ` +
      'a retry: two scheduler runs, a redeployed worker replaying a queue, or ' +
      'a backfill run twice.'];
  }

  return ['duplicated',
    `${n} copies over ${span.toFixed(1)}s, spacing matches no known cause. ` +
    'Worth reading by hand before you change anything.'];
}

async function call(token, method, params = {}) {
  const url = new URL(`${API}/${method}`);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(`${res.status} from ${method}`);
  const body = await res.json();
  // Slack answers almost every failure with HTTP 200 and puts the error in the
  // body, so the body is what gets asserted on.
  if (!body.ok) {
    throw new Error(`${method}: ${body.error} (needed=${body.needed} ` +
                    `provided=${body.provided})`);
  }
  return body;
}

async function channels(token, explicit) {
  if (explicit.length) return explicit.map((id) => ({ id, name: id }));
  const out = [];
  let cursor = '';
  for (;;) {
    const body = await call(token, 'users.conversations',
      { limit: 200, types: 'public_channel,private_channel', cursor });
    out.push(...(body.channels ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return out;
  }
}

async function history(token, channel, limit) {
  const out = [];
  let cursor = '';
  while (out.length < limit) {
    const body = await call(token, 'conversations.history',
      { channel, limit: Math.min(200, limit - out.length), cursor });
    out.push(...(body.messages ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) break;
  }
  return out.slice(0, limit);
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (channels:read and channels:history)');
    process.exitCode = 2;
    return;
  }

  const explicit = process.argv.slice(2).filter((a) => !a.startsWith('-'));
  const limit = 200;

  const me = await call(token, 'auth.test');
  console.log(`authenticated as ${me.user} (bot_id=${me.bot_id}) in ${me.team}`);

  const targets = await channels(token, explicit);
  if (targets.length === 0) {
    console.log('the bot is not a member of any conversation');
    return;
  }

  let findings = 0;
  let authored = 0;
  for (const ch of targets) {
    const messages = await history(token, ch.id, limit);
    const mine = messages.filter((m) =>
      (me.bot_id && m.bot_id === me.bot_id) || (me.user_id && m.user === me.user_id));
    authored += mine.length;

    const groups = new Map();
    for (const m of mine) {
      const key = fingerprint(m);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(m);
    }

    for (const [key, group] of [...groups].sort()) {
      const [state, detail] = classify(group.map((m) => m.ts));
      if (state === 'unique') continue;
      findings += 1;
      console.warn(`${state.padEnd(16)} #${ch.name ?? ch.id}  ${detail}`);
      console.warn(`  first ts ${group[0].ts}  fingerprint ${key}`);
      if (state === 'retry-duplicate') {
        console.warn('  repair: acknowledge the event inside 3s and do the work ' +
                     'after; key on event.event_id in a short-TTL set.');
      } else if (state === 'double-delivery') {
        console.warn('  repair: one delivery path per app. Drop either ' +
                     'app_mention or message.channels, and do not leave a ' +
                     'Request URL configured while Socket Mode is on.');
      } else if (state === 'rerun') {
        console.warn('  repair: take a per-job lock, or post once and ' +
                     'chat.update the same ts as the state changes.');
      }
    }
  }

  console.log(`${targets.length} channel(s), ${authored} app-authored ` +
              `message(s), ${findings} duplicate group(s)`);
  process.exitCode = findings ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and
// without the guard main() would run there too, fail on the missing token, and
// set a non-zero exit code that fails the whole test file even as every test
// passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the two boundaries that matter. One is the fingerprint: two Block Kit messages sharing a fallback <code>text</code> must not be reported as duplicates of each other, or the whole run is noise. The other is the mixed group &mdash; copies spaced neither sub-second nor on the retry schedule &mdash; which must stay unclassified rather than being handed a confident wrong cause.",
"test_py_file": "test_slack_duplicate_messages.py",
"test_py": '''from slack_duplicate_messages import classify, fingerprint


def test_one_message_is_never_a_duplicate():
    state, detail = classify(["1712345678.000100"])
    assert state == "unique"
    assert "nothing to explain" in detail


def test_sub_second_copies_are_a_double_delivery():
    state, detail = classify(["1712345678.000100", "1712345678.400200"])
    assert state == "double-delivery"
    assert "app_mention" in detail


def test_sixty_and_three_hundred_second_gaps_are_slack_retries():
    state, detail = classify(["1000.0", "1061.0", "1358.0"])
    assert state == "retry-duplicate"
    assert "three seconds" in detail


def test_hours_apart_is_a_rerun_not_a_retry():
    state, _ = classify(["0.0", "7200.0"])
    assert state == "rerun"


def test_mixed_spacing_is_not_given_a_confident_cause():
    # Sub-second to the second copy, eight seconds to the third: none of the
    # three known causes produces this, so the script must say so.
    state, detail = classify(["1000.0", "1000.2", "1008.0"])
    assert state == "duplicated"
    assert "matches no known cause" in detail


def test_identical_fallback_text_with_different_blocks_is_not_a_duplicate():
    a = {"text": "New alert", "blocks": [{"type": "section", "text": "disk full"}]}
    b = {"text": "New alert", "blocks": [{"type": "section", "text": "cert expiring"}]}
    assert fingerprint(a) != fingerprint(b)


def test_the_same_content_at_different_timestamps_shares_a_fingerprint():
    a = {"text": "deploy finished", "ts": "1712345678.000100"}
    b = {"text": "deploy finished", "ts": "1712345738.000200"}
    assert fingerprint(a) == fingerprint(b)
''',
"test_js_file": "slack-duplicate-messages.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, fingerprint } from './slack-duplicate-messages.mjs';

test('one message is never a duplicate', () => {
  const [state, detail] = classify(['1712345678.000100']);
  assert.equal(state, 'unique');
  assert.match(detail, /nothing to explain/);
});

test('sub-second copies are a double delivery', () => {
  const [state, detail] = classify(['1712345678.000100', '1712345678.400200']);
  assert.equal(state, 'double-delivery');
  assert.match(detail, /app_mention/);
});

test('sixty and three hundred second gaps are Slack retries', () => {
  const [state, detail] = classify(['1000.0', '1061.0', '1358.0']);
  assert.equal(state, 'retry-duplicate');
  assert.match(detail, /three seconds/);
});

test('hours apart is a rerun, not a retry', () => {
  assert.equal(classify(['0.0', '7200.0'])[0], 'rerun');
});

test('mixed spacing is not given a confident cause', () => {
  const [state, detail] = classify(['1000.0', '1000.2', '1008.0']);
  assert.equal(state, 'duplicated');
  assert.match(detail, /matches no known cause/);
});

test('identical fallback text with different blocks is not a duplicate', () => {
  const a = { text: 'New alert', blocks: [{ type: 'section', text: 'disk full' }] };
  const b = { text: 'New alert', blocks: [{ type: 'section', text: 'cert expiring' }] };
  assert.notEqual(fingerprint(a), fingerprint(b));
});

test('the same content at different timestamps shares a fingerprint', () => {
  assert.equal(
    fingerprint({ text: 'deploy finished', ts: '1712345678.000100' }),
    fingerprint({ text: 'deploy finished', ts: '1712345738.000200' }),
  );
});
''',
"faq": [
 ("Does chat.postMessage support an idempotency key?",
  "No. There is no Idempotency-Key header and no client-supplied token that Slack will honour, so every call creates a new message. Deduplication has to happen in your code before the call. This is the single most important difference between Slack's API and the payments APIs people are used to reasoning about."),
 ("How do I tell a retry duplicate from a double subscription?",
  "By the gap between the copies. Slack redelivers an unacknowledged event at roughly 60 seconds and again at roughly 300, so copies on that spacing are retries. Two subscriptions delivering the same message arrive together, sub-second apart. The repairs are completely different, which is why the script refuses to guess when the spacing matches neither."),
 ("Why hash the blocks instead of just the text?",
  "Because a Block Kit message usually carries a short generic fallback in text, identical across every alert the app sends. Grouping on text alone collapses hundreds of unrelated messages into one group and reports the whole channel as duplicated. Hashing the serialized blocks alongside the text keeps genuinely different messages apart."),
 ("Can the script delete the duplicates it finds?",
  "No, and it should not. It holds a token that can write to your workspace, so it only reads. Deleting message history is a decision with its own consequences, and the duplicates are evidence until you have found the cause."),
 ("My handler is idempotent on event_id and I still see duplicates.",
  "Then the copies are not retries of one event. Check the spacing: if they are sub-second, you have two events, with two different event_ids, for one message. That happens when app_mention and message.channels are both subscribed, or when Socket Mode is running while an HTTP Request URL is still configured on the same app."),
],
"related": [
 ("/slack/bot-message-echo-loop/", "A bot that answers its own messages"),
 ("/slack/non-marketplace-history-clamp/", "History clamped to 15 objects per call"),
 ("/slack/http-200-ok-false/", "Every failure arrives as HTTP 200"),
],
"citations": [CITE_POSTMESSAGE, CITE_HISTORY, CITE_EVENTS, CITE_UPDATE],
},


{
"slug": "bot-message-echo-loop",
"title": "The bot answers its own messages in an endless loop",
"description": "message.channels delivers your own posts back to you. Without a bot_id guard the handler replies to its own reply, and history shows the run.",
"h1": "the bot answers its own messages in an endless loop",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack bot infinite loop", "slack bot replies to itself",
             "message.channels bot_id", "slack echo loop",
             "bolt app.message bot messages"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A channel fills with hundreds of identical bot messages in a few seconds. Slack starts rate-limiting the app, which slows the flood without stopping it, and in the end somebody removes the bot from the channel to make it stop. The cause is one line that was never written: the handler subscribed to <code>message.channels</code>, which delivers <em>every</em> message in the channel, including the one the app posted a moment ago.",
"short_answer": """<p>Call <code>auth.test</code> for your <code>bot_id</code>, then read <code>conversations.history?channel=C...&amp;limit=200</code> and walk the messages in timestamp order looking for <strong>runs of consecutive messages authored by you</strong> with no human message in between. One or two in a row is normal. Twenty in a row, sub-second apart, is the loop.</p>
<p>The guard is in the handler, not in Slack: ignore any event carrying <code>bot_id</code>, any event whose <code>subtype</code> is <code>bot_message</code>, and any event whose <code>user</code> is your own bot user id. Or subscribe to <code>app_mention</code> instead, which never fires on your own posts.</p>""",
"problem": """<p>This is the classic first-week Slack bug, and it is unusual in being both catastrophic and completely unambiguous once you look for it. There is no interpretation required: either there is a run of thirty self-authored messages in the channel or there is not.</p>
<p>What makes it worse than it looks is that rate limiting does not save you. Slack throttles <code>chat.postMessage</code> to roughly one message per second per channel, so the loop keeps running, one message a second, indefinitely. It will still be going tomorrow. Meanwhile every one of those posts is another event delivered to your handler, so the app's own inbound queue grows at the same rate, and any downstream side effect the handler performs happens once per iteration.</p>""",
"why": """<p><strong><code>message.channels</code> is not filtered for you.</strong> The subscription means “every message in every public channel this app is in”, and your own messages are messages. Slack marks them &mdash; app-authored posts carry <code>bot_id</code> and <code>app_id</code>, and legacy senders also carry <code>subtype: "bot_message"</code> &mdash; but a handler that branches on <code>event.text</code> alone never looks at any of that.</p>
<p><strong>Bolt's two entry points behave differently.</strong> <code>app.message()</code> in Bolt already skips messages with a <code>bot_message</code> subtype, which is exactly enough to make developers believe they are protected. It does not skip a modern app-authored message that carries <code>bot_id</code> without that subtype. <code>app.event('app_mention')</code> never fires on your own messages at all, which is why the mention path is the safe one.</p>
<p><strong>A slow loop looks like a feature.</strong> If the handler adds a delay, or the reply is only sent under some condition, the run is spaced out over minutes and reads as a chatty integration rather than a bug. Length alone is not the signal; length combined with spacing is.</p>
<p><strong>Another app's bot messages are not yours.</strong> Filtering on “any message with a <code>bot_id</code>” finds every integration in the channel and reports a busy alerts channel as a loop. The comparison has to be against your own <code>bot_id</code> from <code>auth.test</code>.</p>""",
"steps": [
 {"h": "Get your own identity first",
  "body": """<p><code>auth.test</code> returns both <code>bot_id</code> and <code>user_id</code>. You need both: history items from a modern app carry <code>bot_id</code>, while messages posted with a user token carry only <code>user</code>. Matching on either one, and on nothing else, is what keeps other apps out of the result.</p>"""},
 {"h": "Read history in timestamp order",
  "body": """<p><code>conversations.history</code> returns newest first. Sort ascending before you look for runs, because a run is a property of the order the messages were posted in, and reading the array as it arrives measures the loop backwards.</p>"""},
 {"h": "Measure runs, not counts",
  "body": """<p>A bot that posted 180 of the last 200 messages in an alerts channel is doing its job. A bot that posted 30 <em>consecutively</em>, with no human message anywhere in the run, is talking to itself. Track the longest run per channel and the gaps inside it.</p>"""},
 {"h": "Separate a loop from a batch",
  "body": """<p>A digest job that posts twelve messages in a row at startup is not a loop; a run whose internal gaps are all under a couple of seconds is. Report the slow long run as its own state so that the fast one keeps its meaning &mdash; a check that cries wolf on the nightly digest gets switched off within a week.</p>"""},
 {"h": "Add the guard, then prefer app_mention",
  "body": """<p>In the handler, return early when <code>event.bot_id</code> is present, when <code>event.subtype === "bot_message"</code>, or when <code>event.user</code> equals your bot user id. Better still, subscribe to <code>app_mention</code> for anything conversational: it only fires when a human addresses the app, so the loop is structurally impossible.</p>"""},
],
"verify": """<p>Re-run after the guard ships. The longest self-authored run in every channel should collapse to one or two.</p>
<pre><code class="language-bash">python3 slack_echo_loop_audit.py --limit 200
# 6 channel(s) checked, longest self-authored run 2, 0 loop(s)</code></pre>""",
"code_intro": "Two GET methods, <code>auth.test</code> and <code>conversations.history</code>, plus <code>users.conversations</code> to find the channels &mdash; <code>channels:read</code> and <code>channels:history</code> cover all three. The two pure functions are the ones that decide the answer: whether a given message is ours, which is the same rule the repair puts in the handler, and whether a run of ours is a loop or a batch.",
"py_file": "slack_echo_loop_audit.py",
"py": '''"""Find Slack channels where the app is replying to its own messages.

Read only. Three GET methods and no writes: a bot token with channels:read and
channels:history is enough. The repair is printed, never performed, because this
token can post into the same channels it is reading.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_echo_loop_audit")

API = "https://slack.com/api"


def is_self(message, identity):
    """True when this message was authored by the app we authenticated as.

    Pure, and deliberately narrow. Matching on "has a bot_id" would flag every
    other integration in the channel and report a busy alerts channel as a loop,
    so the comparison is against our own ids from auth.test. Both are checked
    because a modern app-authored message carries bot_id while a message posted
    with a user token carries only `user`.

    This is the same predicate the repair puts in the event handler.
    """
    bot_id = identity.get("bot_id")
    user_id = identity.get("user_id")
    if bot_id and message.get("bot_id") == bot_id:
        return True
    if user_id and message.get("user") == user_id:
        return True
    return False


def verdict(messages, identity, *, min_run=4, burst=2.0):
    """Classify one channel by its longest run of self-authored messages.

    Pure, so the thresholds are visible and testable rather than buried in a
    request loop. `messages` are history items in any order; they are sorted by
    ts here because a run is a property of posting order.

    Returns (state, detail). Length alone is not the signal: a digest job posting
    a dozen messages in a row is not a loop, so a long run whose internal gaps
    are wider than `burst` seconds gets its own state rather than being reported
    as one.
    """
    ordered = sorted(messages, key=lambda m: float(m.get("ts") or 0))

    best, best_gaps = [], []
    run, gaps = [], []
    for m in ordered:
        if is_self(m, identity):
            if run:
                gaps.append(float(m.get("ts") or 0) - float(run[-1].get("ts") or 0))
            run.append(m)
        else:
            if len(run) > len(best):
                best, best_gaps = run, gaps
            run, gaps = [], []
    if len(run) > len(best):
        best, best_gaps = run, gaps

    n = len(best)
    if n <= 1:
        return ("quiet",
                "longest self-authored run is %d. Every reply is answering "
                "somebody else." % n)

    widest = max(best_gaps) if best_gaps else 0.0

    if n < min_run:
        return ("short-run",
                "%d in a row, %.1fs apart at widest. A threaded reply or a "
                "two-part message, not a loop." % (n, widest))

    if widest >= burst:
        return ("batch",
                "%d in a row but %.1fs apart at widest. That is a poster, not a "
                "loop: a digest or a backlog being drained. Worth confirming it "
                "is deliberate." % (n, widest))

    return ("echo-loop",
            "%d consecutive self-authored messages, none more than %.2fs apart, "
            "with no human message in the run. The handler is hearing itself."
            % (n, widest))


def call(session, method, **params):
    """One Web API read. Slack answers almost every failure with HTTP 200 and
    puts the error in the body, so the body is what gets asserted on."""
    r = session.get("%s/%s" % (API, method), params=params, timeout=30)
    r.raise_for_status()
    body = r.json()
    if not body.get("ok"):
        raise SystemExit("%s: %s (needed=%s provided=%s)"
                         % (method, body.get("error"), body.get("needed"),
                            body.get("provided")))
    return body


def channels(session, explicit):
    if explicit:
        return [{"id": c, "name": c} for c in explicit]
    out, cursor = [], ""
    while True:
        body = call(session, "users.conversations", limit=200,
                    types="public_channel,private_channel", cursor=cursor)
        out.extend(body.get("channels", []))
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return out


def history(session, channel_id, limit):
    body = call(session, "conversations.history", channel=channel_id,
                limit=min(200, limit))
    return body.get("messages", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channel", action="append", default=[],
                    help="channel id to read; repeatable. Default: every channel "
                         "the bot is a member of")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages to read per channel")
    ap.add_argument("--min-run", type=int, default=4,
                    help="runs shorter than this are never reported as a loop")
    ap.add_argument("--burst", type=float, default=2.0,
                    help="seconds; a run spaced wider than this is a batch")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (a bot token with channels:read and "
                  "channels:history is enough)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    me = call(session, "auth.test")
    identity = {"bot_id": me.get("bot_id"), "user_id": me.get("user_id")}
    log.info("authenticated as %s (bot_id=%s) in %s",
             me.get("user"), identity["bot_id"], me.get("team"))

    targets = channels(session, args.channel)
    if not targets:
        log.info("the bot is not a member of any conversation")
        return 0

    loops = longest = 0
    for ch in targets:
        messages = history(session, ch["id"], args.limit)
        state, detail = verdict(messages, identity,
                                min_run=args.min_run, burst=args.burst)
        name = ch.get("name", ch["id"])
        if state in ("quiet", "short-run"):
            log.info("%-10s #%s  %s", state, name, detail)
            continue
        if state == "batch":
            log.info("%-10s #%s  %s", state, name, detail)
            continue
        loops += 1
        log.warning("%-10s #%s  %s", state, name, detail)
        log.warning("  repair: in the handler, return early when event.bot_id is "
                    "set, when event.subtype is bot_message, or when event.user "
                    "== %s.", identity["user_id"])
        log.warning("  better: subscribe to app_mention instead of "
                    "message.channels so your own posts never reach the handler.")

    log.info("%d channel(s) checked, %d loop(s)", len(targets), loops)
    return 1 if loops else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-echo-loop-audit.mjs",
"js": '''/**
 * Find Slack channels where the app is replying to its own messages.
 *
 * Read only. Three GET methods and no writes: a bot token with channels:read
 * and channels:history is enough. The repair is printed, never performed.
 */
const API = 'https://slack.com/api';

/**
 * True when this message was authored by the app we authenticated as.
 *
 * Pure, and deliberately narrow: matching on "has a bot_id" would flag every
 * other integration in the channel. Both ids are checked because a modern
 * app-authored message carries bot_id while one posted with a user token
 * carries only `user`. This is the same predicate the repair puts in the
 * event handler.
 */
export function isSelf(message, identity) {
  if (identity.bot_id && message.bot_id === identity.bot_id) return true;
  if (identity.user_id && message.user === identity.user_id) return true;
  return false;
}

/**
 * Classify one channel by its longest run of self-authored messages.
 *
 * Pure, so the thresholds are visible and testable. Length alone is not the
 * signal: a digest job posting a dozen messages in a row is not a loop, so a
 * long run with wide internal gaps gets its own state.
 */
export function verdict(messages, identity, { minRun = 4, burst = 2.0 } = {}) {
  const ordered = [...messages].sort((a, b) => Number(a.ts ?? 0) - Number(b.ts ?? 0));

  let best = [];
  let bestGaps = [];
  let run = [];
  let gaps = [];
  for (const m of ordered) {
    if (isSelf(m, identity)) {
      if (run.length) gaps.push(Number(m.ts ?? 0) - Number(run[run.length - 1].ts ?? 0));
      run.push(m);
    } else {
      if (run.length > best.length) { best = run; bestGaps = gaps; }
      run = [];
      gaps = [];
    }
  }
  if (run.length > best.length) { best = run; bestGaps = gaps; }

  const n = best.length;
  if (n <= 1) {
    return ['quiet',
      `longest self-authored run is ${n}. Every reply is answering somebody else.`];
  }

  const widest = bestGaps.length ? Math.max(...bestGaps) : 0;

  if (n < minRun) {
    return ['short-run',
      `${n} in a row, ${widest.toFixed(1)}s apart at widest. A threaded reply ` +
      'or a two-part message, not a loop.'];
  }

  if (widest >= burst) {
    return ['batch',
      `${n} in a row but ${widest.toFixed(1)}s apart at widest. That is a ` +
      'poster, not a loop: a digest or a backlog being drained. Worth ' +
      'confirming it is deliberate.'];
  }

  return ['echo-loop',
    `${n} consecutive self-authored messages, none more than ` +
    `${widest.toFixed(2)}s apart, with no human message in the run. The ` +
    'handler is hearing itself.'];
}

async function call(token, method, params = {}) {
  const url = new URL(`${API}/${method}`);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(`${res.status} from ${method}`);
  const body = await res.json();
  // Slack answers almost every failure with HTTP 200 and puts the error in the
  // body, so the body is what gets asserted on.
  if (!body.ok) {
    throw new Error(`${method}: ${body.error} (needed=${body.needed} ` +
                    `provided=${body.provided})`);
  }
  return body;
}

async function channels(token, explicit) {
  if (explicit.length) return explicit.map((id) => ({ id, name: id }));
  const out = [];
  let cursor = '';
  for (;;) {
    const body = await call(token, 'users.conversations',
      { limit: 200, types: 'public_channel,private_channel', cursor });
    out.push(...(body.channels ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return out;
  }
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (channels:read and channels:history)');
    process.exitCode = 2;
    return;
  }

  const explicit = process.argv.slice(2).filter((a) => !a.startsWith('-'));

  const me = await call(token, 'auth.test');
  const identity = { bot_id: me.bot_id, user_id: me.user_id };
  console.log(`authenticated as ${me.user} (bot_id=${me.bot_id}) in ${me.team}`);

  const targets = await channels(token, explicit);
  if (targets.length === 0) {
    console.log('the bot is not a member of any conversation');
    return;
  }

  let loops = 0;
  for (const ch of targets) {
    const body = await call(token, 'conversations.history',
      { channel: ch.id, limit: 200 });
    const [state, detail] = verdict(body.messages ?? [], identity);
    const name = ch.name ?? ch.id;
    if (state !== 'echo-loop') {
      console.log(`${state.padEnd(10)} #${name}  ${detail}`);
      continue;
    }
    loops += 1;
    console.warn(`${state.padEnd(10)} #${name}  ${detail}`);
    console.warn('  repair: in the handler, return early when event.bot_id is ' +
                 `set, when event.subtype is bot_message, or when event.user == ${identity.user_id}.`);
    console.warn('  better: subscribe to app_mention instead of ' +
                 'message.channels so your own posts never reach the handler.');
  }

  console.log(`${targets.length} channel(s) checked, ${loops} loop(s)`);
  process.exitCode = loops ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and
// without the guard main() would run there too, fail on the missing token, and
// set a non-zero exit code that fails the whole test file even as every test
// passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two tests that keep this check usable are the negatives. Another app's <code>bot_id</code> must not count as ours, or every alerts channel in the workspace is a loop; and a long run posted slowly must come back as <code>batch</code>, or the nightly digest gets reported every night until somebody deletes the cron entry for the audit.",
"test_py_file": "test_slack_echo_loop_audit.py",
"test_py": '''from slack_echo_loop_audit import is_self, verdict

ME = {"bot_id": "B111", "user_id": "U111"}


def msg(ts, *, bot=None, user=None):
    m = {"ts": str(ts)}
    if bot:
        m["bot_id"] = bot
    if user:
        m["user"] = user
    return m


def test_another_apps_bot_message_is_not_ours():
    assert is_self(msg(1, bot="B999"), ME) is False


def test_our_bot_id_and_our_user_id_both_count():
    assert is_self(msg(1, bot="B111"), ME) is True
    assert is_self(msg(2, user="U111"), ME) is True


def test_replies_interleaved_with_humans_are_quiet():
    messages = [msg(1, user="U777"), msg(2, bot="B111"),
                msg(3, user="U777"), msg(4, bot="B111")]
    state, _ = verdict(messages, ME)
    assert state == "quiet"


def test_a_fast_unbroken_run_is_the_loop():
    messages = [msg(1000 + i * 0.3, bot="B111") for i in range(12)]
    state, detail = verdict(messages, ME)
    assert state == "echo-loop"
    assert "12" in detail


def test_a_slow_long_run_is_a_batch_not_a_loop():
    # A digest posting one message every five seconds. Reporting this is how
    # the check gets switched off.
    messages = [msg(1000 + i * 5.0, bot="B111") for i in range(12)]
    state, _ = verdict(messages, ME)
    assert state == "batch"


def test_history_arriving_newest_first_is_still_measured_correctly():
    newest_first = [msg(1000 + i * 0.3, bot="B111") for i in range(9)][::-1]
    assert verdict(newest_first, ME)[0] == "echo-loop"


def test_two_in_a_row_is_a_short_run():
    messages = [msg(1, user="U777"), msg(2, bot="B111"), msg(2.4, bot="B111")]
    state, _ = verdict(messages, ME)
    assert state == "short-run"
''',
"test_js_file": "slack-echo-loop-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isSelf, verdict } from './slack-echo-loop-audit.mjs';

const ME = { bot_id: 'B111', user_id: 'U111' };

const msg = (ts, { bot, user } = {}) => {
  const m = { ts: String(ts) };
  if (bot) m.bot_id = bot;
  if (user) m.user = user;
  return m;
};

test('another app bot message is not ours', () => {
  assert.equal(isSelf(msg(1, { bot: 'B999' }), ME), false);
});

test('our bot id and our user id both count', () => {
  assert.equal(isSelf(msg(1, { bot: 'B111' }), ME), true);
  assert.equal(isSelf(msg(2, { user: 'U111' }), ME), true);
});

test('replies interleaved with humans are quiet', () => {
  const messages = [msg(1, { user: 'U777' }), msg(2, { bot: 'B111' }),
    msg(3, { user: 'U777' }), msg(4, { bot: 'B111' })];
  assert.equal(verdict(messages, ME)[0], 'quiet');
});

test('a fast unbroken run is the loop', () => {
  const messages = Array.from({ length: 12 }, (_, i) => msg(1000 + i * 0.3, { bot: 'B111' }));
  const [state, detail] = verdict(messages, ME);
  assert.equal(state, 'echo-loop');
  assert.match(detail, /12/);
});

test('a slow long run is a batch, not a loop', () => {
  const messages = Array.from({ length: 12 }, (_, i) => msg(1000 + i * 5, { bot: 'B111' }));
  assert.equal(verdict(messages, ME)[0], 'batch');
});

test('history arriving newest first is still measured correctly', () => {
  const messages = Array.from({ length: 9 }, (_, i) => msg(1000 + i * 0.3, { bot: 'B111' })).reverse();
  assert.equal(verdict(messages, ME)[0], 'echo-loop');
});

test('two in a row is a short run', () => {
  const messages = [msg(1, { user: 'U777' }), msg(2, { bot: 'B111' }), msg(2.4, { bot: 'B111' })];
  assert.equal(verdict(messages, ME)[0], 'short-run');
});
''',
"faq": [
 ("Why does my bot receive its own messages at all?",
  "Because message.channels means every message posted in a channel the app is in, and your app's posts are messages in that channel. Slack marks them with bot_id and app_id so you can filter, but it does not filter for you. There is no subscription setting that excludes your own posts."),
 ("Doesn't Bolt already protect me from this?",
  "Partly, which is the trap. Bolt's app.message() skips messages whose subtype is bot_message, so a legacy-shaped post is filtered. A modern app-authored message can carry bot_id without that subtype and still reach your handler. app.event('app_mention') is the one that never fires on your own posts."),
 ("Rate limiting will stop the loop, won't it?",
  "No. chat.postMessage is throttled to roughly one message per second per channel, so the loop slows to one message a second and keeps going. It does not terminate on its own; somebody has to deploy the guard or remove the bot from the channel."),
 ("How does the script tell a loop from a bot that just posts a lot?",
  "It measures runs of consecutive self-authored messages with no human message in between, and then the gaps inside the longest run. Twelve in a row five seconds apart is a digest and gets reported as a batch. Twelve in a row a third of a second apart is a handler answering itself."),
 ("Can it check threads too?",
  "The same shape works on conversations.replies for a thread_ts, and threaded echo loops do happen when a handler replies in-thread to any message in the thread. The channel-level check finds the expensive case first, because a loop in the main channel is the one that pages everybody."),
],
"related": [
 ("/slack/duplicate-messages-no-dedupe/", "The same message posted three times"),
 ("/slack/bot-not-in-channel/", "not_in_channel: the bot was never invited"),
 ("/slack/http-200-ok-false/", "Every failure arrives as HTTP 200"),
],
"citations": [CITE_MESSAGE_EVENT, CITE_APP_MENTION, CITE_HISTORY, CITE_AUTH_TEST],
},


{
"slug": "public-file-links-exposed",
"title": "Files made public with a link that works without a Slack login",
"description": "files.list reports public_url_shared per file. Where it is true the permalink_public opens for anyone on the internet, with no login and no expiry.",
"h1": "files made public with a link that works without a Slack login",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack public file link", "files.sharedPublicURL",
             "slack permalink_public", "slack file exposed publicly",
             "revoke slack public file url"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing errored, and nothing is going to. Somewhere in the app's history a developer needed an image URL that Block Kit could actually fetch, called <code>files.sharedPublicURL</code>, and it worked. Every file that call has been made against since &mdash; customer exports, database dumps, screenshots with a token still on screen &mdash; is readable by anyone holding the link, with no Slack account, no workspace membership and no expiry. The flag is on each file, and <code>files.list</code> will hand you all of them.",
"short_answer": """<p>Page <code>files.list?count=200&amp;types=all</code> with <code>files:read</code> and report every file where <code>public_url_shared</code> is <code>true</code>. That field means one thing only: a <code>permalink_public</code> exists and serves the file to unauthenticated requests.</p>
<p>Do not confuse it with <code>is_public</code>, which merely means the file is shared into a public <em>channel</em> and still requires a Slack login. Reporting those as exposures buries the real finding. The repair is <code>files.revokePublicURL</code>, which needs <code>files:write</code> &mdash; this script prints the call rather than making it.</p>""",
"problem": """<p>This is a data-exposure finding, not a bug report, and it deserves to be read that way. A public Slack file URL is an unauthenticated, unexpiring, unlogged capability. It is not covered by channel permissions, it survives the file being unshared from every channel, it survives the message that carried it being deleted, and it does not stop working when the person who created it leaves the company. There is no access log to check afterwards to find out whether anyone used it.</p>
<p>It also has essentially no false positives. Unlike most audit findings, there is nothing to interpret: either <code>public_url_shared</code> is true, in which case a URL exists that a stranger can fetch, or it is false. The only judgement in the whole check is deciding which of those files should not have been public, and that is a question for a human with context, which is exactly why the script reports and does not revoke.</p>""",
"why": """<p><strong>Block Kit forced somebody's hand.</strong> An <code>image_url</code> in a Block Kit block has to be fetchable by Slack's own image proxy without credentials, and <code>url_private</code> is not. The documented workaround people find is <code>files.sharedPublicURL</code>, and it is a single call that makes the image render immediately. Nobody comes back to it.</p>
<p><strong>The flag is permanent until explicitly revoked.</strong> There is no TTL on <code>permalink_public</code>. The only way it stops working is <code>files.revokePublicURL</code>, or the file being deleted. Retention policies will eventually delete old files, which means the exposure quietly ends years later for reasons unrelated to anyone noticing it.</p>
<p><strong>The URL is guessable enough to matter.</strong> A public Slack file link is a long path, not a signed URL with a secret, and it is routinely pasted into tickets, wikis, emails and third-party tools that index what they are given. Treat it as published, not as obscure.</p>
<p><strong>Two flags look alike and mean completely different things.</strong> <code>is_public</code> is about channel visibility inside the workspace. <code>public_url_shared</code> is about the internet. A check that conflates them reports every screenshot ever posted in <code>#general</code> and gets ignored.</p>""",
"steps": [
 {"h": "Page files.list rather than reading the first page",
  "body": """<p><code>files.list?count=200&amp;types=all</code> returns a <code>paging</code> object with <code>pages</code>. The default page size is small and the exposures are usually old, so a first-page-only read is the version of this check that reports zero findings on a workspace that has hundreds.</p>"""},
 {"h": "Split the two visibility flags",
  "body": """<p>Keep <code>public_url_shared</code> and <code>is_public</code> in separate buckets. The first is the finding. The second is normal workspace behaviour and belongs in the run as context, not as an alert.</p>"""},
 {"h": "Surface the files nobody can see from inside Slack",
  "body": """<p>A file with <code>public_url_shared: true</code> whose <code>channels</code>, <code>groups</code> and <code>ims</code> arrays are all empty is the worst case in the list: it is unreachable through the Slack UI, so no member will ever stumble on it and report it, while the public URL keeps serving. Report it separately.</p>"""},
 {"h": "Confirm one link empirically",
  "body": """<p>Fetch one <code>permalink_public</code> with no <code>Authorization</code> header at all. A <code>200</code> carrying the real bytes is proof; a redirect to a Slack sign-in page means the link is already dead. One confirmation is enough to establish that the flag means what the docs say it means in your workspace.</p>"""},
 {"h": "Revoke, then remove the reason it was needed",
  "body": """<p><code>files.revokePublicURL?file=F...</code> per file, which needs <code>files:write</code> and is why this script prints the list instead of acting on it. Then fix the cause: host Block Kit images on your own infrastructure, or upload the file to Slack and reference it in the message so channel permissions apply. Ask an admin to disable public file sharing workspace-wide if the app has no legitimate need for it.</p>"""},
],
"verify": """<p>Re-run after the revocations. The exposed count should be zero, and the files that are merely in public channels should still be listed as such.</p>
<pre><code class="language-bash">python3 slack_public_files_audit.py --max-files 5000
# 3184 file(s), 0 exposed, 0 exposed and unreachable in Slack</code></pre>""",
"code_intro": "One paginated GET against <code>files.list</code>, with <code>files:read</code> and nothing else &mdash; the revocation needs <code>files:write</code>, which this script deliberately does not use. The pure function is the per-file verdict, and it earns its place by keeping <code>is_public</code> and <code>public_url_shared</code> apart: the whole value of this check is that it reports only the files a stranger can actually fetch.",
"py_file": "slack_public_files_audit.py",
"py": '''"""Report Slack files that are readable without a Slack login.

Read only. One paginated GET and no writes: a bot token with files:read is
enough, and the revocation that repairs this needs files:write, which this
script deliberately does not use. The repair is printed for a human to run.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_public_files_audit")

API = "https://slack.com/api"


def verdict(f):
    """Classify one file by which visibility flag is set. Pure, so the rule can
    be tested without a network.

    The distinction this function exists to protect: `is_public` means the file
    is shared into a public channel and a Slack login is still required, while
    `public_url_shared` means a permalink_public exists that serves the bytes to
    anyone on the internet. Only the second is a data exposure. Conflating them
    reports every screenshot ever posted in #general and buries the finding.

    Returns (state, detail).
    """
    if f.get("is_external"):
        return ("external",
                "hosted outside Slack, so Slack's flags do not govern who can "
                "read it. Check the origin instead.")

    public_link = bool(f.get("public_url_shared"))
    shared = bool(f.get("channels") or f.get("groups") or f.get("ims"))

    if public_link and not shared:
        return ("exposed-orphan",
                "public URL live and the file is in no channel, group or DM. "
                "Nobody inside Slack can see it to report it, and the link "
                "still serves.")

    if public_link:
        return ("exposed",
                "public URL live. Readable by anyone holding the link: no "
                "login, no expiry, no access log.")

    if f.get("is_public"):
        return ("workspace-visible",
                "shared into a public channel. Visible to members, still gated "
                "behind a Slack login. Not an exposure.")

    return ("private", "no public URL, not in a public channel")


def human_size(n):
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.0f%s" % (n, unit)
        n /= 1024


def call(session, method, **params):
    """One Web API read. Slack answers almost every failure with HTTP 200 and
    puts the error in the body, so the body is what gets asserted on."""
    r = session.get("%s/%s" % (API, method), params=params, timeout=30)
    r.raise_for_status()
    body = r.json()
    if not body.get("ok"):
        raise SystemExit("%s: %s (needed=%s provided=%s)"
                         % (method, body.get("error"), body.get("needed"),
                            body.get("provided")))
    return body


def list_files(session, limit):
    """Page files.list. This resource uses page numbers rather than cursors, and
    a first-page-only read is how this check reports zero findings on a
    workspace with hundreds: the exposures are usually old."""
    out, page = [], 1
    while len(out) < limit:
        body = call(session, "files.list", count=200, page=page, types="all")
        out.extend(body.get("files", []))
        pages = int((body.get("paging") or {}).get("pages") or 1)
        if page >= pages:
            break
        page += 1
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-files", type=int, default=5000,
                    help="stop paging after this many files")
    ap.add_argument("--show-workspace-visible", action="store_true",
                    help="also list files that are in public channels but still "
                         "require a Slack login")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (a bot token with files:read is enough)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    me = call(session, "auth.test")
    log.info("authenticated as %s in %s", me.get("user"), me.get("team"))

    files = list_files(session, args.max_files)
    if not files:
        log.info("no files visible to this token")
        return 0

    exposed = orphaned = 0
    # Newest and largest first: a recent export is a more urgent conversation
    # than a four-year-old screenshot.
    for f in sorted(files, key=lambda x: (int(x.get("created") or 0),
                                          int(x.get("size") or 0)), reverse=True):
        state, detail = verdict(f)
        if state == "private":
            continue
        if state == "workspace-visible" and not args.show_workspace_visible:
            continue

        created = dt.datetime.utcfromtimestamp(int(f.get("created") or 0)).date()
        line = "%-17s %s  %s  %s  %s" % (state, f.get("id"), created,
                                         human_size(f.get("size")),
                                         (f.get("name") or "")[:48])
        if state in ("exposed", "exposed-orphan"):
            exposed += 1
            orphaned += 1 if state == "exposed-orphan" else 0
            log.warning(line)
            log.warning("  %s", detail)
            log.warning("  public link: %s", f.get("permalink_public"))
            log.warning("  repair: files.revokePublicURL?file=%s (needs "
                        "files:write, which this script does not hold)",
                        f.get("id"))
        else:
            log.info("%s  %s", line, detail)

    log.info("%d file(s), %d exposed, %d exposed and unreachable in Slack",
             len(files), exposed, orphaned)
    if exposed:
        log.warning("stop minting public URLs for Block Kit images: host them "
                    "yourself, or reference the uploaded file so channel "
                    "permissions apply. An admin can disable public file "
                    "sharing workspace-wide.")
    return 1 if exposed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-public-files-audit.mjs",
"js": '''/**
 * Report Slack files that are readable without a Slack login.
 *
 * Read only. One paginated GET and no writes: a bot token with files:read is
 * enough, and the revocation that repairs this needs files:write, which this
 * script deliberately does not use. The repair is printed for a human to run.
 */
const API = 'https://slack.com/api';

/**
 * Classify one file by which visibility flag is set. Pure, so the rule can be
 * tested without a network.
 *
 * The distinction this function exists to protect: `is_public` means the file
 * is shared into a public channel and a Slack login is still required, while
 * `public_url_shared` means a permalink_public exists that serves the bytes to
 * anyone on the internet. Only the second is a data exposure.
 */
export function verdict(f) {
  if (f.is_external) {
    return ['external',
      "hosted outside Slack, so Slack's flags do not govern who can read it. " +
      'Check the origin instead.'];
  }

  const publicLink = Boolean(f.public_url_shared);
  const shared = Boolean((f.channels ?? []).length || (f.groups ?? []).length ||
                         (f.ims ?? []).length);

  if (publicLink && !shared) {
    return ['exposed-orphan',
      'public URL live and the file is in no channel, group or DM. Nobody ' +
      'inside Slack can see it to report it, and the link still serves.'];
  }

  if (publicLink) {
    return ['exposed',
      'public URL live. Readable by anyone holding the link: no login, no ' +
      'expiry, no access log.'];
  }

  if (f.is_public) {
    return ['workspace-visible',
      'shared into a public channel. Visible to members, still gated behind a ' +
      'Slack login. Not an exposure.'];
  }

  return ['private', 'no public URL, not in a public channel'];
}

export function humanSize(bytes) {
  let n = Number(bytes ?? 0);
  for (const unit of ['B', 'KB', 'MB', 'GB']) {
    if (n < 1024 || unit === 'GB') return `${n.toFixed(0)}${unit}`;
    n /= 1024;
  }
  return `${n}B`;
}

async function call(token, method, params = {}) {
  const url = new URL(`${API}/${method}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(`${res.status} from ${method}`);
  const body = await res.json();
  // Slack answers almost every failure with HTTP 200 and puts the error in the
  // body, so the body is what gets asserted on.
  if (!body.ok) {
    throw new Error(`${method}: ${body.error} (needed=${body.needed} ` +
                    `provided=${body.provided})`);
  }
  return body;
}

async function listFiles(token, limit) {
  const out = [];
  let page = 1;
  while (out.length < limit) {
    const body = await call(token, 'files.list',
      { count: 200, page, types: 'all' });
    out.push(...(body.files ?? []));
    const pages = Number(body.paging?.pages ?? 1);
    if (page >= pages) break;
    page += 1;
  }
  return out.slice(0, limit);
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (a bot token with files:read is enough)');
    process.exitCode = 2;
    return;
  }

  const me = await call(token, 'auth.test');
  console.log(`authenticated as ${me.user} in ${me.team}`);

  const files = await listFiles(token, 5000);
  if (files.length === 0) {
    console.log('no files visible to this token');
    return;
  }

  let exposed = 0;
  let orphaned = 0;
  const ordered = [...files].sort((a, b) =>
    Number(b.created ?? 0) - Number(a.created ?? 0));

  for (const f of ordered) {
    const [state, detail] = verdict(f);
    if (state !== 'exposed' && state !== 'exposed-orphan') continue;
    exposed += 1;
    if (state === 'exposed-orphan') orphaned += 1;
    const created = new Date(Number(f.created ?? 0) * 1000).toISOString().slice(0, 10);
    console.warn(`${state.padEnd(17)} ${f.id}  ${created}  ` +
                 `${humanSize(f.size)}  ${(f.name ?? '').slice(0, 48)}`);
    console.warn(`  ${detail}`);
    console.warn(`  public link: ${f.permalink_public}`);
    console.warn(`  repair: files.revokePublicURL?file=${f.id} (needs ` +
                 'files:write, which this script does not hold)');
  }

  console.log(`${files.length} file(s), ${exposed} exposed, ${orphaned} ` +
              'exposed and unreachable in Slack');
  if (exposed) {
    console.warn('stop minting public URLs for Block Kit images: host them ' +
                 'yourself, or reference the uploaded file so channel ' +
                 'permissions apply.');
  }
  process.exitCode = exposed ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and
// without the guard main() would run there too, fail on the missing token, and
// set a non-zero exit code that fails the whole test file even as every test
// passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is the third one: a file with <code>is_public</code> set and <code>public_url_shared</code> unset must come back as <code>workspace-visible</code>, never as an exposure. Every screenshot ever posted in a public channel has that shape, and a check that reports them all is a check nobody reads twice.",
"test_py_file": "test_slack_public_files_audit.py",
"test_py": '''from slack_public_files_audit import verdict


def test_a_public_url_is_an_exposure():
    state, detail = verdict({"public_url_shared": True, "channels": ["C1"]})
    assert state == "exposed"
    assert "no login" in detail


def test_a_public_url_on_a_file_in_no_channel_is_worse():
    state, detail = verdict({"public_url_shared": True,
                             "channels": [], "groups": [], "ims": []})
    assert state == "exposed-orphan"
    assert "no channel" in detail


def test_is_public_alone_is_not_an_exposure():
    # A screenshot in #general. Slack login still required.
    state, detail = verdict({"is_public": True, "channels": ["C1"]})
    assert state == "workspace-visible"
    assert "Not an exposure" in detail


def test_a_private_file_is_private():
    assert verdict({"channels": ["C1"]})[0] == "private"


def test_an_external_file_is_not_judged_by_slack_flags():
    state, _ = verdict({"is_external": True, "public_url_shared": True})
    assert state == "external"


def test_a_file_with_no_flags_at_all_is_private():
    assert verdict({})[0] == "private"
''',
"test_js_file": "slack-public-files-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, humanSize } from './slack-public-files-audit.mjs';

test('a public URL is an exposure', () => {
  const [state, detail] = verdict({ public_url_shared: true, channels: ['C1'] });
  assert.equal(state, 'exposed');
  assert.match(detail, /no login/);
});

test('a public URL on a file in no channel is worse', () => {
  const [state, detail] = verdict({
    public_url_shared: true, channels: [], groups: [], ims: [],
  });
  assert.equal(state, 'exposed-orphan');
  assert.match(detail, /no channel/);
});

test('is_public alone is not an exposure', () => {
  const [state, detail] = verdict({ is_public: true, channels: ['C1'] });
  assert.equal(state, 'workspace-visible');
  assert.match(detail, /Not an exposure/);
});

test('a private file is private', () => {
  assert.equal(verdict({ channels: ['C1'] })[0], 'private');
});

test('an external file is not judged by Slack flags', () => {
  assert.equal(verdict({ is_external: true, public_url_shared: true })[0], 'external');
});

test('a file with no flags at all is private', () => {
  assert.equal(verdict({})[0], 'private');
});

test('sizes are rendered in the nearest unit', () => {
  assert.equal(humanSize(2048), '2KB');
});
''',
"faq": [
 ("What is the difference between is_public and public_url_shared?",
  "is_public means the file is shared into a public channel: any member of the workspace can open it, and a Slack login is required. public_url_shared means files.sharedPublicURL was called on it and a permalink_public exists that serves the bytes to anyone on the internet with no account at all. Only the second is a data exposure."),
 ("Does the public link expire, or stop working when the message is deleted?",
  "Neither. There is no TTL, and the link is not tied to any message or channel. It survives the file being unshared everywhere, the message being deleted, and the person who created it leaving the company. Only files.revokePublicURL or the file being deleted stops it."),
 ("Can I see who has downloaded a public file?",
  "No. There is no access log for permalink_public on any plan. That is why the finding is treated as an exposure rather than as a risk to assess: you cannot establish that nobody used the link, only that the link works."),
 ("Why doesn't the script revoke the links itself?",
  "Because it holds a token for your workspace and this section's scripts never write, and because revoking is a judgement call the script cannot make. Some public URLs are load-bearing for a page that embeds them. It prints the exact files.revokePublicURL call per file so you can review the list and run it."),
 ("How did this happen if nobody meant to make files public?",
  "Almost always Block Kit. An image_url in a block has to be fetchable without credentials and url_private is not, so files.sharedPublicURL is the first thing that works. Once it is in the upload path it applies to every file the app uploads from then on."),
],
"related": [
 ("/slack/pagination-not-followed/", "next_cursor is ignored, so you see one page"),
 ("/slack/http-200-ok-false/", "Every failure arrives as HTTP 200"),
 ("/slack/non-marketplace-history-clamp/", "History clamped to 15 objects per call"),
],
"citations": [CITE_FILES_PUBLIC, CITE_FILES_REVOKE, CITE_FILES_LIST, CITE_FILES_INFO],
},


{
"slug": "non-marketplace-history-clamp",
"title": "conversations.history clamped to 15 objects and 1 per minute",
"description": "Ask for 200 messages and get 15. Slack clamps conversations.history for apps that are not on the Marketplace, and there is no setting to change.",
"h1": "conversations.history clamped to 15 objects and 1 per minute",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack conversations.history rate limit",
             "slack non-marketplace app rate limits", "slack 15 messages limit",
             "slack history 1 request per minute", "slack may 2025 rate limits"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A backfill that used to take an hour now takes weeks, and nothing in your code changed. <code>conversations.history</code> still returns <code>ok: true</code>, still returns a valid page, still gives you a cursor &mdash; it just returns 15 messages when you asked for 200, and refuses the second call inside the same minute. This is Slack's May 2025 rate-limit change for apps that are not approved for the Marketplace, and it is working exactly as designed.",
"short_answer": """<p>Call <code>conversations.history?channel=C...&amp;limit=200</code> once. If <code>messages.length</code> comes back as exactly <strong>15</strong> and <code>response_metadata.next_cursor</code> is a non-empty string, the clamp is on. Confirm by calling again inside the same minute: a clamped app gets <code>ok: false</code> with <code>error: "ratelimited"</code> and a <code>Retry-After</code> of about 60.</p>
<p><strong>This note is detect-only.</strong> There is no setting, header or parameter that lifts the clamp. The real options are Marketplace approval, reclassifying the app as internal, or moving off history polling and onto the Events API.</p>""",
"problem": """<p>On 29 May 2025 Slack changed the rate limits on <code>conversations.history</code> and <code>conversations.replies</code> for commercially distributed apps that are not approved for the Slack Marketplace. Those apps get <strong>1 request per minute</strong>, and a maximum and default <code>limit</code> of <strong>15 objects</strong> per request, down from Tier 3 &mdash; 50+ requests a minute with <code>limit</code> up to 1000. It took effect immediately for newly created unlisted apps and for net-new installations of existing ones, and rolled across existing installations between 2 September 2025 and 3 March 2026. Internal, customer-built apps are excluded.</p>
<p>The change is a factor of roughly 3,000 in throughput, and it arrives without a single error. <code>ok</code> stays <code>true</code>, the response shape is unchanged, pagination still works. An archiver that reads a busy channel simply falls behind, forever, and the only symptom anyone sees is a dashboard that is a bit more out of date every week.</p>""",
"why": """<p><strong>A clamped page is indistinguishable from a small page.</strong> Slack does not return <code>invalid_limit</code> when you ask for 200 and it will only give you 15; it silently returns 15. The only thing separating “the clamp is on” from “the channel only has 15 messages” is whether a <code>next_cursor</code> came back with it.</p>
<p><strong>The 1-per-minute part is easy to misread as a transient throttle.</strong> A <code>ratelimited</code> error with <code>Retry-After: 60</code> looks like ordinary backpressure, and a client with retry logic absorbs it silently. It is not transient; it is the steady state for this app on this method.</p>
<p><strong>It is per method family, not global.</strong> <code>conversations.list</code> and <code>users.list</code> are untouched, so a health check that exercises those comes back clean. Contrasting a history call against a list call is what proves the problem is the clamp and not a workspace-wide throttle or a shared quota between your own workers.</p>
<p><strong>Nothing in the app can fix it.</strong> This is the unusual case where detection is the entire deliverable. Every real remedy is a change to what the app <em>is</em> &mdash; a Marketplace listing, an internal-app reclassification, or an architecture that does not poll history &mdash; and pretending otherwise wastes a day looking for a setting that was never there.</p>""",
"steps": [
 {"h": "Ask for more than the cap, deliberately",
  "body": """<p>The probe only works if the request is larger than the clamp. Call <code>conversations.history?channel=C...&amp;limit=200</code>. If your code already asks for 15, or for the default, you cannot tell the difference and the script says so rather than guessing.</p>"""},
 {"h": "Count the page and read the cursor together",
  "body": """<p>Exactly 15 messages plus a non-empty <code>response_metadata.next_cursor</code> is the clamp: Slack has more to give and is giving you 15. Exactly 15 with no cursor means the channel has 15 messages left and proves nothing. Pick a busy channel, and if the result is inconclusive, pick a busier one.</p>"""},
 {"h": "Confirm with a second call in the same minute",
  "body": """<p>Immediately repeat the call. A clamped app gets <code>ok: false</code>, <code>error: "ratelimited"</code>, and a <code>Retry-After</code> header near 60. An unclamped app on Tier 3 answers normally. Read <code>Retry-After</code> from the headers on both a real <code>429</code> and a <code>200</code> body, because Slack uses both shapes.</p>"""},
 {"h": "Contrast against a method that was not changed",
  "body": """<p><code>conversations.list?limit=200</code> should still return up to 200. If that is clamped too, you are looking at something else entirely &mdash; an IP allow list, a workspace-wide throttle, or your own workers sharing one per-method quota &mdash; and the history clamp is not your problem.</p>"""},
 {"h": "Choose one of the three real remedies",
  "body": """<p>Submit the app to the Slack Marketplace and get it approved, which restores Tier 3. Or, if it only ever runs inside one organisation, reclassify it as an internal customer-built app, which is exempt. Or redesign away from polling: subscribe to <code>message.channels</code> and <code>message.groups</code>, maintain your own store, and let history become a rare backfill. While you decide, drop any hardcoded <code>limit=1000</code> to 15 so the pagination logic stops assuming pages it will not get.</p>"""},
],
"verify": """<p>Re-run the probe after the app's status changes. A healthy app returns a full page and answers the second call.</p>
<pre><code class="language-bash">python3 slack_history_clamp_probe.py --channel C0123456789
# unclamped   C0123456789  asked for 200, got 200. Tier 3 limits intact.</code></pre>""",
"code_intro": "Three GET calls, all reads: <code>auth.test</code>, one <code>conversations.history</code> probe repeated once inside the minute, and a <code>conversations.list</code> control. Scopes are <code>channels:read</code> and <code>channels:history</code>. The pure function takes the numbers the probe collected &mdash; requested, returned, cursor, whether the second call was refused &mdash; and names the state, including the two states that mean “this probe cannot tell you”.",
"py_file": "slack_history_clamp_probe.py",
"py": '''"""Detect Slack's non-Marketplace clamp on conversations.history.

Read only, and detect-only: there is no setting that lifts this clamp, so the
script reports what it found and prints the three real remedies. A bot token
with channels:read and channels:history is enough.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_history_clamp_probe")

API = "https://slack.com/api"

# The documented ceiling for a non-Marketplace app on conversations.history and
# conversations.replies since 29 May 2025: 15 objects, one request per minute.
CAP = 15


def verdict(probe, *, cap=CAP):
    """Name the state of one history probe. Pure, so the rule is testable
    offline.

    `probe` carries what the two calls observed:
        requested          the limit that was asked for
        returned           how many messages came back
        next_cursor        response_metadata.next_cursor, or ""
        second_call_error  body.error from an immediate repeat call, or ""

    Returns (state, detail). Two of the states exist to say the probe cannot
    tell: asking for 15 or fewer proves nothing, and a page of exactly 15 with
    no cursor is a channel that ran out of messages, not a clamp. Reporting
    either as clamped sends somebody to the Marketplace over a quiet channel.
    """
    requested = int(probe.get("requested") or 0)
    returned = int(probe.get("returned") or 0)
    cursor = str(probe.get("next_cursor") or "").strip()
    throttled = str(probe.get("second_call_error") or "").strip() == "ratelimited"

    if requested <= cap:
        return ("not-probed",
                "asked for %d, which is at or below the %d-object cap. Ask for "
                "more than %d or the answer means nothing."
                % (requested, cap, cap))

    if returned > cap:
        return ("unclamped",
                "asked for %d, got %d. Tier 3 limits intact."
                % (requested, returned))

    if returned == cap and cursor and throttled:
        return ("clamped-confirmed",
                "asked for %d, got exactly %d with more pages waiting, and the "
                "second call inside the minute was refused with ratelimited. "
                "That is the non-Marketplace clamp." % (requested, cap))

    if returned == cap and cursor:
        return ("clamped",
                "asked for %d, got exactly %d and a cursor, so Slack has more "
                "and is handing over %d. The second call was not refused; "
                "repeat the probe to confirm the 1-per-minute half."
                % (requested, cap, cap))

    if returned == cap:
        return ("inconclusive",
                "got exactly %d with no cursor. A clamped page and a channel "
                "with %d messages left look identical here. Probe a busier "
                "channel." % (cap, cap))

    if cursor:
        return ("short-page",
                "got %d of %d with a cursor still set. Fewer than the clamp "
                "would give, so this is not it: look at the channel, the "
                "oldest/latest window, or a shared quota."
                % (returned, requested))

    return ("small-channel",
            "got %d of %d and no cursor. The channel simply has that many "
            "messages; nothing is clamped." % (returned, requested))


def call(session, method, **params):
    """One Web API read. Returns (body, retry_after). Unlike the other scripts
    in this section, a ratelimited answer here is the finding rather than an
    error, so it is returned instead of raised. Slack sends it both as a real
    429 with a Retry-After header and as a 200 carrying ok false, so both are
    handled."""
    r = session.get("%s/%s" % (API, method), params=params, timeout=30)
    retry_after = r.headers.get("Retry-After")
    if r.status_code == 429:
        return ({"ok": False, "error": "ratelimited"}, retry_after)
    r.raise_for_status()
    body = r.json()
    if not body.get("ok") and body.get("error") != "ratelimited":
        raise SystemExit("%s: %s (needed=%s provided=%s)"
                         % (method, body.get("error"), body.get("needed"),
                            body.get("provided")))
    return (body, retry_after)


def pick_channel(session):
    body, _ = call(session, "users.conversations", limit=200,
                   types="public_channel")
    channels = body.get("channels") or []
    if not channels:
        return None
    # The busiest channel available is the one least likely to give an
    # inconclusive answer, and message count is the closest proxy on hand.
    channels.sort(key=lambda c: int(c.get("num_members") or 0), reverse=True)
    return channels[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channel", help="channel id to probe. Default: the "
                                      "largest channel the bot is a member of")
    ap.add_argument("--limit", type=int, default=200,
                    help="page size to ask for; must exceed 15 to mean anything")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (channels:read and channels:history)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    me, _ = call(session, "auth.test")
    log.info("authenticated as %s in %s", me.get("user"), me.get("team"))

    channel = args.channel
    if not channel:
        picked = pick_channel(session)
        if not picked:
            log.error("no channels available; pass --channel")
            return 2
        channel = picked["id"]
        log.info("probing #%s (%s)", picked.get("name"), channel)

    first, _ = call(session, "conversations.history", channel=channel,
                    limit=args.limit)
    if not first.get("ok"):
        log.error("first call was already ratelimited; wait a minute and retry")
        return 2

    second, retry_after = call(session, "conversations.history",
                               channel=channel, limit=args.limit)

    state, detail = verdict({
        "requested": args.limit,
        "returned": len(first.get("messages") or []),
        "next_cursor": (first.get("response_metadata") or {}).get("next_cursor"),
        "second_call_error": second.get("error"),
    })

    log.info("%-18s %s  %s", state, channel, detail)
    if retry_after:
        log.info("  Retry-After on the second call: %s", retry_after)

    control, _ = call(session, "conversations.list", limit=200,
                      exclude_archived="true")
    n = len(control.get("channels") or [])
    log.info("  control: conversations.list?limit=200 returned %d", n)
    if n <= CAP and state.startswith("clamped"):
        log.warning("  the control is short too, so this may be a wider "
                    "throttle rather than the history clamp alone")

    if state.startswith("clamped"):
        log.warning("  no setting lifts this. The three real remedies:")
        log.warning("   1. get the app approved for the Slack Marketplace, "
                    "which restores Tier 3")
        log.warning("   2. if it runs inside one organisation only, reclassify "
                    "it as an internal customer-built app, which is exempt")
        log.warning("   3. stop polling history: subscribe to message.channels "
                    "and message.groups, keep your own store, and let history "
                    "become a rare backfill")
        log.warning("  meanwhile drop any hardcoded limit=1000 to %d so "
                    "pagination stops assuming pages it will not get", CAP)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-history-clamp-probe.mjs",
"js": '''/**
 * Detect Slack's non-Marketplace clamp on conversations.history.
 *
 * Read only, and detect-only: there is no setting that lifts this clamp, so the
 * script reports what it found and prints the three real remedies. A bot token
 * with channels:read and channels:history is enough.
 */
const API = 'https://slack.com/api';

// The documented ceiling for a non-Marketplace app on conversations.history and
// conversations.replies since 29 May 2025: 15 objects, one request per minute.
export const CAP = 15;

/**
 * Name the state of one history probe. Pure, so the rule is testable offline.
 *
 * Two of the states exist to say the probe cannot tell: asking for 15 or fewer
 * proves nothing, and a page of exactly 15 with no cursor is a channel that ran
 * out of messages rather than a clamp. Reporting either as clamped sends
 * somebody to the Marketplace over a quiet channel.
 */
export function verdict(probe, { cap = CAP } = {}) {
  const requested = Number(probe.requested ?? 0);
  const returned = Number(probe.returned ?? 0);
  const cursor = String(probe.next_cursor ?? '').trim();
  const throttled = String(probe.second_call_error ?? '').trim() === 'ratelimited';

  if (requested <= cap) {
    return ['not-probed',
      `asked for ${requested}, which is at or below the ${cap}-object cap. ` +
      `Ask for more than ${cap} or the answer means nothing.`];
  }

  if (returned > cap) {
    return ['unclamped', `asked for ${requested}, got ${returned}. Tier 3 limits intact.`];
  }

  if (returned === cap && cursor && throttled) {
    return ['clamped-confirmed',
      `asked for ${requested}, got exactly ${cap} with more pages waiting, and ` +
      'the second call inside the minute was refused with ratelimited. That is ' +
      'the non-Marketplace clamp.'];
  }

  if (returned === cap && cursor) {
    return ['clamped',
      `asked for ${requested}, got exactly ${cap} and a cursor, so Slack has ` +
      `more and is handing over ${cap}. The second call was not refused; ` +
      'repeat the probe to confirm the 1-per-minute half.'];
  }

  if (returned === cap) {
    return ['inconclusive',
      `got exactly ${cap} with no cursor. A clamped page and a channel with ` +
      `${cap} messages left look identical here. Probe a busier channel.`];
  }

  if (cursor) {
    return ['short-page',
      `got ${returned} of ${requested} with a cursor still set. Fewer than the ` +
      'clamp would give, so this is not it: look at the channel, the ' +
      'oldest/latest window, or a shared quota.'];
  }

  return ['small-channel',
    `got ${returned} of ${requested} and no cursor. The channel simply has ` +
    'that many messages; nothing is clamped.'];
}

/**
 * One Web API read. Returns { body, retryAfter }. A ratelimited answer is the
 * finding here rather than an error, so it is returned instead of thrown, and
 * Slack sends it both as a real 429 and as a 200 carrying ok false.
 */
async function call(token, method, params = {}) {
  const url = new URL(`${API}/${method}`);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const retryAfter = res.headers.get('retry-after');
  if (res.status === 429) return { body: { ok: false, error: 'ratelimited' }, retryAfter };
  if (!res.ok) throw new Error(`${res.status} from ${method}`);
  const body = await res.json();
  if (!body.ok && body.error !== 'ratelimited') {
    throw new Error(`${method}: ${body.error} (needed=${body.needed} ` +
                    `provided=${body.provided})`);
  }
  return { body, retryAfter };
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (channels:read and channels:history)');
    process.exitCode = 2;
    return;
  }

  const limit = 200;
  const { body: me } = await call(token, 'auth.test');
  console.log(`authenticated as ${me.user} in ${me.team}`);

  let channel = process.argv.slice(2).find((a) => !a.startsWith('-'));
  if (!channel) {
    const { body } = await call(token, 'users.conversations',
      { limit: 200, types: 'public_channel' });
    const channels = [...(body.channels ?? [])]
      .sort((a, b) => Number(b.num_members ?? 0) - Number(a.num_members ?? 0));
    if (channels.length === 0) {
      console.error('no channels available; pass a channel id');
      process.exitCode = 2;
      return;
    }
    channel = channels[0].id;
    console.log(`probing #${channels[0].name} (${channel})`);
  }

  const { body: first } = await call(token, 'conversations.history', { channel, limit });
  if (!first.ok) {
    console.error('first call was already ratelimited; wait a minute and retry');
    process.exitCode = 2;
    return;
  }

  const { body: second, retryAfter } = await call(token, 'conversations.history',
    { channel, limit });

  const [state, detail] = verdict({
    requested: limit,
    returned: (first.messages ?? []).length,
    next_cursor: first.response_metadata?.next_cursor,
    second_call_error: second.error,
  });

  console.log(`${state.padEnd(18)} ${channel}  ${detail}`);
  if (retryAfter) console.log(`  Retry-After on the second call: ${retryAfter}`);

  const { body: control } = await call(token, 'conversations.list',
    { limit: 200, exclude_archived: 'true' });
  console.log(`  control: conversations.list?limit=200 returned ` +
              `${(control.channels ?? []).length}`);

  if (state.startsWith('clamped')) {
    console.warn('  no setting lifts this. The three real remedies:');
    console.warn('   1. get the app approved for the Slack Marketplace, which ' +
                 'restores Tier 3');
    console.warn('   2. if it runs inside one organisation only, reclassify it ' +
                 'as an internal customer-built app, which is exempt');
    console.warn('   3. stop polling history: subscribe to message.channels and ' +
                 'message.groups, keep your own store, and let history become a ' +
                 'rare backfill');
    console.warn(`  meanwhile drop any hardcoded limit=1000 to ${CAP} so ` +
                 'pagination stops assuming pages it will not get');
    process.exitCode = 1;
  }
}

// Only run when invoked directly. The test file imports this module, and
// without the guard main() would run there too, fail on the missing token, and
// set a non-zero exit code that fails the whole test file even as every test
// passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Most of these tests are about refusing to answer. A page of exactly 15 with no cursor, and a probe that asked for 15 in the first place, both have to come back as “cannot tell” &mdash; because the cost of a false positive here is somebody spending a week on a Marketplace submission for a quiet channel.",
"test_py_file": "test_slack_history_clamp_probe.py",
"test_py": '''from slack_history_clamp_probe import verdict


def test_a_full_page_is_unclamped():
    state, detail = verdict({"requested": 200, "returned": 200,
                             "next_cursor": "dXNlcjpV"})
    assert state == "unclamped"
    assert "Tier 3" in detail


def test_exactly_fifteen_with_a_cursor_is_the_clamp():
    state, _ = verdict({"requested": 200, "returned": 15,
                        "next_cursor": "dXNlcjpV"})
    assert state == "clamped"


def test_a_refused_second_call_confirms_it():
    state, detail = verdict({"requested": 200, "returned": 15,
                             "next_cursor": "dXNlcjpV",
                             "second_call_error": "ratelimited"})
    assert state == "clamped-confirmed"
    assert "ratelimited" in detail


def test_exactly_fifteen_with_no_cursor_is_not_a_finding():
    # A channel that has fifteen messages left looks identical to a clamped
    # page. Calling this clamped is the expensive mistake.
    state, detail = verdict({"requested": 200, "returned": 15, "next_cursor": ""})
    assert state == "inconclusive"
    assert "busier channel" in detail


def test_asking_for_fifteen_proves_nothing():
    state, _ = verdict({"requested": 15, "returned": 15, "next_cursor": "abc"})
    assert state == "not-probed"


def test_a_short_quiet_channel_is_not_clamped():
    state, _ = verdict({"requested": 200, "returned": 4, "next_cursor": ""})
    assert state == "small-channel"


def test_fewer_than_the_cap_with_a_cursor_is_something_else():
    state, _ = verdict({"requested": 200, "returned": 9, "next_cursor": "abc"})
    assert state == "short-page"
''',
"test_js_file": "slack-history-clamp-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './slack-history-clamp-probe.mjs';

test('a full page is unclamped', () => {
  const [state, detail] = verdict({
    requested: 200, returned: 200, next_cursor: 'dXNlcjpV',
  });
  assert.equal(state, 'unclamped');
  assert.match(detail, /Tier 3/);
});

test('exactly fifteen with a cursor is the clamp', () => {
  assert.equal(
    verdict({ requested: 200, returned: 15, next_cursor: 'dXNlcjpV' })[0],
    'clamped',
  );
});

test('a refused second call confirms it', () => {
  const [state, detail] = verdict({
    requested: 200, returned: 15, next_cursor: 'dXNlcjpV',
    second_call_error: 'ratelimited',
  });
  assert.equal(state, 'clamped-confirmed');
  assert.match(detail, /ratelimited/);
});

test('exactly fifteen with no cursor is not a finding', () => {
  const [state, detail] = verdict({ requested: 200, returned: 15, next_cursor: '' });
  assert.equal(state, 'inconclusive');
  assert.match(detail, /busier channel/);
});

test('asking for fifteen proves nothing', () => {
  assert.equal(
    verdict({ requested: 15, returned: 15, next_cursor: 'abc' })[0],
    'not-probed',
  );
});

test('a short quiet channel is not clamped', () => {
  assert.equal(
    verdict({ requested: 200, returned: 4, next_cursor: '' })[0],
    'small-channel',
  );
});

test('fewer than the cap with a cursor is something else', () => {
  assert.equal(
    verdict({ requested: 200, returned: 9, next_cursor: 'abc' })[0],
    'short-page',
  );
});
''',
"faq": [
 ("Which apps are affected by the clamp?",
  "Commercially distributed apps that are not approved for the Slack Marketplace, on conversations.history and conversations.replies. Internal customer-built apps are excluded. It applied immediately to newly created unlisted apps and to net-new installations of existing ones, and rolled across existing installations between 2 September 2025 and 3 March 2026."),
 ("Is there a header or parameter that turns it off?",
  "No. There is no setting, no allow list you can request, and no plan tier that changes it. That is why this note is detect-only: the script tells you the clamp is on and prints the three real remedies, which are Marketplace approval, internal-app reclassification, or an architecture that does not poll history."),
 ("Why does the script call the same endpoint twice on purpose?",
  "Because the clamp has two halves and the page size only shows you one. The second call inside the same minute is what proves the 1-request-per-minute half: a clamped app is refused with ratelimited and a Retry-After near 60, and a Tier 3 app answers normally."),
 ("My probe returned 15 messages and the script said inconclusive.",
  "Then no cursor came back, which means Slack had nothing more to give: the channel really does have fifteen messages left. A clamped page always has a next_cursor, because the clamp truncates a page Slack could have filled. Probe a busier channel."),
 ("What does the Events API buy me here?",
  "It inverts the data flow. Instead of asking Slack for history on a schedule and being metered, you subscribe to message.channels and message.groups and write each message into your own store as it happens. History then becomes a rare backfill rather than the primary data path, and one request per minute stops mattering."),
],
"related": [
 ("/slack/pagination-not-followed/", "next_cursor is ignored, so you see one page"),
 ("/slack/duplicate-messages-no-dedupe/", "The same message posted three times"),
 ("/slack/http-200-ok-false/", "Every failure arrives as HTTP 200"),
],
"citations": [CITE_CLAMP, CITE_CLAMP_CLARITY, CITE_RATE_LIMITS, CITE_HISTORY],
},

]
