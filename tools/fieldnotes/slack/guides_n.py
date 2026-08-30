#!/usr/bin/env python3
"""/slack/ field notes, batch N - the writing.

Three notes about transports and the things that arrive on them. One is about
an app that asked for the same sentence twice and got it: two event types,
two handlers, one human being. One is about an address that was correct on the
afternoon it was typed in and has been pointing at a closed laptop ever since,
which is a different failure from a URL that never verified at all. And one is
about an app still riding a transport Slack retired, working perfectly, one
reinstall away from an error no scope can clear.

Read only throughout, and unusually strict about it. Two of these scripts read
an app manifest, which is a read of the configuration rather than a change to
it. None of them sends a single byte to the reader's own Request URL, because
a detector that pokes a production endpoint to see what happens is a detector
that has started participating in the incident. And none of them calls
rtm.connect, which mints a session and is therefore a write in every sense
this section means.
"""

CITE_EVENTS = ("The Events API - Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_EVENT_TYPES = ("Events reference - Slack Docs",
                    "https://docs.slack.dev/reference/events/")
CITE_APP_MENTION = ("app_mention event reference - Slack Docs",
                    "https://docs.slack.dev/reference/events/app_mention")
CITE_MESSAGE_EVENT = ("message event reference - Slack Docs",
                      "https://docs.slack.dev/reference/events/message")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_MANIFEST = ("apps.manifest.export method reference - Slack Docs",
                 "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_MANIFESTS = ("App manifests - Slack Docs", "https://docs.slack.dev/app-manifests/")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_SOCKET_MODE = ("Using Socket Mode - Slack Docs",
                    "https://docs.slack.dev/apis/events-api/using-socket-mode")
CITE_RTM = ("Legacy RTM API - Slack Docs", "https://docs.slack.dev/legacy/legacy-rtm-api")
CITE_SCOPES = ("Scopes - Slack Docs", "https://docs.slack.dev/reference/scopes/")
CITE_INTERACTIVITY = ("Handling user interaction - Slack Docs",
                      "https://docs.slack.dev/interactivity/handling-user-interaction")
CITE_SLASH = ("Implementing slash commands - Slack Docs",
              "https://docs.slack.dev/interactivity/implementing-slash-commands")
CITE_SECURITY = ("Security best practices - Slack Docs",
                 "https://docs.slack.dev/authentication/best-practices-for-security")

GUIDES = []

GUIDES.append({
"slug": "app-mention-vs-message-double-fire",
"title": "One mention, two events: app_mention and message both fire",
"description": "Subscribe to app_mention and message.channels and one @bot line arrives twice. The overlap is in the subscription list, and the reply spacing proves it.",
"h1": "One mention, two events: app_mention and message both fire",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack bot replies twice", "app_mention and message both fire",
             "slack app_mention duplicate", "bolt app.message and app.event duplicate",
             "slack bot responds twice to mention"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody types <code>@deploybot status</code> and the bot answers, and then answers again, with the identical text, so fast that the two replies land in the same visual block in the client. It happens every time, for everyone, in every channel. It is not flaky and it is not load: it is exactly two, always.</p><p>That reliability is the clue. Retries are irregular and spaced in minutes. This is two events, delivered once each, arriving at your process inside the same tick, because a mention in a channel your app is in is two separate events and the app asked for both of them.",
"short_answer": """<p>When someone writes <code>@bot hello</code> in a channel your app belongs to, Slack sends <strong>two events</strong>: <code>app_mention</code>, because the text mentions your app, and <code>message.channels</code>, because a message was posted in a channel you subscribe to. They are separate deliveries with separate <code>event_id</code> values and separate types. An app with a replying handler on each replies twice, and no amount of idempotency on <code>event_id</code> will collapse them, because they are genuinely two different events.</p>
<p>So the finding lives in the subscription list, not in the message history. The script reads <code>settings.event_subscriptions.bot_events</code> and asks which human actions land on more than one subscribed event; the mention rows are the ones that produce a deterministic pair. Then it reads a page of channel history as corroboration and measures the gap between consecutive replies, because the spacing is what separates this note from its neighbours: <strong>under a second is two subscriptions, sixty or three hundred seconds is a retry</strong>.</p>""",
"problem": """<p>The first hour goes into the wrong place, and it goes there for a good reason. Two identical messages look like a delivery problem, and Slack has a famous delivery problem: it retries anything you do not acknowledge in three seconds. So the team adds an idempotency store keyed on <code>event_id</code>, deploys it, and the bot still answers twice. That is the moment the bug becomes interesting, because the fix that always works has just failed.</p>
<p>It failed because there is nothing to deduplicate. The two deliveries are not two copies of one event, they are one copy each of two events, with different ids, different types and different payload shapes. A dedupe key that is doing its job perfectly will pass both of them through, and it should.</p>
<p>The way in is almost always incremental and almost always sensible in isolation. The app starts with <code>app_mention</code> because it answers when addressed. Later somebody wants it to notice links, or keywords, or a message in a support channel, so they add <code>message.channels</code> and a second handler. Both handlers are correct. The overlap between them is not written down anywhere, is invisible on the configuration screen, which lists the two events on adjacent lines with no hint that one human sentence satisfies both, and appears in production the first time somebody says the bot's name.</p>""",
"why": """<p><strong>These are two events, not one event twice.</strong> That single sentence is the whole note. <code>app_mention</code> and <code>message.channels</code> arrive with distinct <code>event_id</code> values, so every deduplication strategy built for retries passes them both, correctly. If your dedupe store is working and the duplicates continue, this is where to look.</p>
<p><strong>The spacing is the discriminator and it is not subtle.</strong> Two deliveries caused by one utterance are handled in the same tick and land milliseconds apart. Slack's retries land at roughly sixty and three hundred seconds. There is no overlap between those regimes, so one subtraction on two <code>ts</code> values tells you which note you are reading.</p>
<p><strong>The overlap is a property of the configuration, so it is knowable before anybody complains.</strong> You do not need a reproduction. Two lines in <code>bot_events</code> are enough to say that a mention in a public channel will be delivered twice, permanently, to any handler pair that does not coordinate.</p>
<p><strong>The guard belongs in the message handler, not in the mention handler.</strong> <code>app_mention</code> is the narrower, better-typed event and it is the one to keep for directed commands. The general <code>message</code> handler is the one that needs to learn to step aside when the text contains your bot user id, because it is the one that was never meant to answer commands in the first place.</p>
<p><strong>Removing a subscription is not always available, which is why the script models a guard.</strong> Plenty of apps need <code>message.channels</code> for a real feature. In that case the pair stays subscribed forever and the only correct repair is code that knows about the overlap, so the script reports a declared guard as a resolved state rather than pretending the subscription must go.</p>""",
"steps": [
 {"h": "Read the subscription list, or supply it",
  "body": """<p>With an app configuration token, <code>apps.manifest.export</code> returns <code>settings.event_subscriptions.bot_events</code>. Without one, pass <code>--subscribed</code> once per event; the list is short and it is on the screen in front of you. This is the set the finding is computed from.</p>"""},
 {"h": "Ask which human action lands on two subscribed events",
  "body": """<p><code>overlap</code> walks a small table of triggers: a mention in a public channel is <code>app_mention</code> plus <code>message.channels</code>, in a private channel <code>message.groups</code>, in a group DM <code>message.mpim</code>. Any row where both are subscribed is a deterministic double delivery.</p>"""},
 {"h": "Declare the guards you already have",
  "body": """<p>If your <code>message</code> handler already skips text containing your bot user id, say so with <code>--guarded message.channels</code>. The row comes back <code>guarded</code> rather than as a finding. A subscription you legitimately need is not a bug, and a report that calls it one gets ignored.</p>"""},
 {"h": "Corroborate from one page of history",
  "body": """<p>Pass <code>--channel</code> and the script reads <code>conversations.history</code>, finds human messages that mention the bot, and looks at the run of bot replies immediately after each one. Two replies to one mention is the symptom made visible, in the workspace, with timestamps.</p>"""},
 {"h": "Subtract the two timestamps and let the gap decide",
  "body": """<p><code>gap_state</code> sorts a pair into <code>simultaneous</code> under a second, <code>retry-shaped</code> in the sixty and three hundred second windows, and <code>unattributed</code> otherwise. Only the first is this note, and the other two are handed to the notes that own them by name.</p>"""},
 {"h": "Print the guard, not just the diagnosis",
  "body": """<p>The repair is one condition in one handler: ignore any <code>message</code> event whose text contains <code>&lt;@</code> plus your bot user id, and let <code>app_mention</code> own directed commands. The script prints it with your actual user id substituted in, so it can be pasted.</p>"""},
],
"verify": """<p>After the guard ships, mention the bot once and re-run against the same channel. The subscription overlap is still there, because it is allowed to be; what should be gone is the pair.</p>
<pre><code class="language-bash">python3 slack_event_overlap_audit.py --subscribed app_mention \\
    --subscribed message.channels --guarded message.channels --channel C01ABCDE9
# identity   U0APPBOT11 in acme, bot_id B01ABCDE9
# public channel        guarded        both events are subscribed and the message.channels
#                                      handler declares that it skips messages addressed to the bot
# history    C01ABCDE9  4 mention(s), 0 pair(s)
# verdict    clear          no mention in this workspace is being delivered twice</code></pre>""",
"code_intro": "Three pure functions and two ordinary reads. <code>overlap</code> is the finding: it takes the subscribed events and returns the human actions that land on two of them, which is knowable without a single duplicate ever being posted. <code>gap_state</code> is the discriminator, and it is deliberately the shortest function in the file because the whole argument is one subtraction. <code>mention_twins</code> walks a page of history and only attributes a pair to this note when a mention preceded it, so an echo loop is not filed here by mistake.",
"py_file": "slack_event_overlap_audit.py",
"py": '''"""Find the subscription overlap that delivers one mention as two events.

Read only. One auth.test for the bot's own identifiers, one optional
apps.manifest.export on an app configuration token for the subscribed events,
and one page of conversations.history per channel you name. Nothing is posted,
edited or unsubscribed: the overlap is a property of the subscription list, and
this prints the guard you would add.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_event_overlap_audit")

API = "https://slack.com/api/"

# One human action, and every event Slack sends because of it. These are not two
# names for one delivery: app_mention and message.channels are separate events
# with separate ids, arriving at the same process inside the same tick. An app
# subscribed to both has two handlers for one sentence.
MENTION_TRIGGERS = {
    "public channel": ("app_mention", "message.channels"),
    "private channel": ("app_mention", "message.groups"),
    "group DM": ("app_mention", "message.mpim"),
}

RANK = {"double-fire": 0, "guarded": 1, "single-path": 2, "not-subscribed": 3}

# Slack retries a delivery it believes failed at roughly 60 and 300 seconds. A
# pair spaced like that is one event delivered twice, which is a different note.
# A pair spaced under a second is two events delivered once each, which is this
# one. There is no overlap between the two regimes, which is what makes a single
# subtraction sufficient.
RETRY_WINDOWS = ((55.0, 70.0), (285.0, 320.0))

SIMULTANEOUS = 1.0


def overlap(subscribed, guarded=None):
    """Which human action is delivered twice. Pure.

    Returns rows of (where, events, state, detail), worst first. The states are
    deliberately four rather than two: a pair that is subscribed and guarded is
    a resolved overlap and not a finding, because plenty of apps need
    message.channels for a real feature and will keep it forever.
    """
    subs = {str(e).strip() for e in subscribed or [] if str(e).strip()}
    guards = {str(e).strip() for e in guarded or [] if str(e).strip()}
    rows = []
    for where in sorted(MENTION_TRIGGERS):
        mention, msg = MENTION_TRIGGERS[where]
        both = mention in subs and msg in subs
        if both and (msg in guards or mention in guards):
            rows.append((where, (mention, msg), "guarded",
                         "both events are subscribed and the %s handler declares "
                         "that it skips messages addressed to the bot" % msg))
        elif both:
            rows.append((where, (mention, msg), "double-fire",
                         "%s and %s are both subscribed, so one mention in a %s is "
                         "two deliveries with two event ids and two handler runs"
                         % (mention, msg, where)))
        elif mention in subs or msg in subs:
            only = mention if mention in subs else msg
            rows.append((where, (mention, msg), "single-path",
                         "only %s is subscribed, so a mention in a %s reaches the "
                         "app once" % (only, where)))
        else:
            rows.append((where, (mention, msg), "not-subscribed",
                         "neither %s nor %s is subscribed, so nothing arrives from "
                         "a %s at all" % (mention, msg, where)))
    return sorted(rows, key=lambda r: (RANK.get(r[2], 9), r[0]))


def gap_state(delta):
    """What the spacing between two consecutive replies means. Pure.

    The shortest function here and the one carrying the argument. Two events
    caused by one utterance are handled in the same tick. A retry is a minute
    or five minutes later. Nothing lands in between, so the subtraction decides
    which note you are reading.
    """
    try:
        d = abs(float(delta))
    except (TypeError, ValueError):
        return ("unattributed", "the two timestamps could not be read as numbers")
    if d < SIMULTANEOUS:
        return ("simultaneous",
                "%.3fs apart, which is two events for one message handled in the "
                "same tick" % d)
    for lo, hi in RETRY_WINDOWS:
        if lo <= d <= hi:
            return ("retry-shaped",
                    "%.1fs apart, which is Slack's retry schedule and not a second "
                    "subscription" % d)
    return ("unattributed",
            "%.1fs apart, which matches neither a double subscription nor a retry" % d)


def mention_twins(messages, bot_id, bot_user_id):
    """Reply pairs in one page of history, and what put them there. Pure.

    messages: as conversations.history returns them, newest first. Returns rows
    of (trigger_ts, delta, state, detail).

    A run of consecutive replies is only attributed to this note when the human
    message in front of it actually mentions the bot. Two replies with no
    mention before them is an echo loop or two workers, and filing those here
    would send somebody to edit a subscription list that is not the problem.
    """
    ordered = sorted([m for m in messages or [] if isinstance(m, dict)],
                     key=lambda m: float(m.get("ts") or 0))
    handle = "<@%s>" % bot_user_id if bot_user_id else ""

    def mine(m):
        return bool(bot_id) and m.get("bot_id") == bot_id

    rows, i = [], 0
    while i < len(ordered):
        trigger = ordered[i]
        if mine(trigger):
            i += 1
            continue
        run, j = [], i + 1
        while j < len(ordered) and mine(ordered[j]):
            run.append(ordered[j])
            j += 1
        if len(run) >= 2:
            delta = float(run[1].get("ts") or 0) - float(run[0].get("ts") or 0)
            addressed = bool(handle) and handle in str(trigger.get("text") or "")
            if addressed:
                state, detail = gap_state(delta)
            else:
                state = "unattributed"
                detail = ("the message before this pair does not mention the bot, "
                          "so the pair belongs to the echo loop or the duplicate "
                          "message note rather than to this one")
            rows.append((trigger.get("ts"), delta, state, detail))
        i = j if j > i else i + 1
    return rows


def verdict(overlap_rows, twin_rows, subscriptions_known=True):
    """Combine the configuration finding with the behavioural one. Pure."""
    doubled = [r for r in overlap_rows or [] if r[2] == "double-fire"]
    twins = [r for r in twin_rows or [] if r[2] == "simultaneous"]
    retries = [r for r in twin_rows or [] if r[2] == "retry-shaped"]
    if doubled and twins:
        return ("confirmed",
                "%d subscription overlap(s) and %d reply pair(s) under a second "
                "apart. The configuration explains the behaviour"
                % (len(doubled), len(twins)))
    if doubled:
        return ("configured",
                "%d subscription overlap(s). Nothing has to have gone wrong yet: "
                "a mention in one of these conversations is two deliveries whether "
                "or not anyone has complained" % len(doubled))
    if twins and not subscriptions_known:
        return ("observed",
                "%d reply pair(s) under a second apart, with no subscription list "
                "read. Export the manifest, or pass --subscribed, to name the cause"
                % len(twins))
    if twins:
        return ("elsewhere",
                "%d reply pair(s) under a second apart, and no overlap in the "
                "subscription list. Two processes running the same handler will "
                "also produce this" % len(twins))
    if retries:
        return ("retries",
                "%d pair(s) spaced like Slack's retry schedule, which is a "
                "dedupe question rather than a subscription one" % len(retries))
    return ("clear", "no mention in this workspace is being delivered twice")


def get(session, method, params, label):
    """One GET, asserting on the body rather than the status line."""
    r = session.get(API + method, params=params or {}, timeout=30)
    body = r.json()
    if body.get("ok") is not True:
        log.warning("%-10s %-14s %s", label, "unavailable", body.get("error"))
        return None
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app ID, for the manifest read")
    ap.add_argument("--subscribed", action="append", default=[],
                    help="a subscribed event type, when no manifest is available")
    ap.add_argument("--guarded", action="append", default=[],
                    help="an event whose handler already skips messages that "
                         "mention the bot; repeatable")
    ap.add_argument("--channel", action="append", default=[],
                    help="channel ID to read one page of history from; repeatable")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s; channels:history and the identity read are enough",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = get(s, "auth.test", {}, "auth.test")
    if not who:
        return 2
    bot_id, user_id = who.get("bot_id"), who.get("user_id")
    log.info("identity   %s in %s, bot_id %s", user_id, who.get("team"), bot_id)

    subscribed, known = list(args.subscribed), bool(args.subscribed)
    config_token = os.environ.get(args.config_token_env)
    if config_token and args.app_id:
        c = requests.Session()
        c.headers.update({"Authorization": "Bearer " + config_token})
        body = get(c, "apps.manifest.export", {"app_id": args.app_id}, "manifest")
        if body:
            subs = (((body or {}).get("manifest") or {}).get("settings")
                    or {}).get("event_subscriptions") or {}
            subscribed = list(subs.get("bot_events") or [])
            known = True
    if not known:
        log.info("manifest   skipped        no subscription list was read; pass "
                 "--subscribed for each event on the configuration screen")

    rows = overlap(subscribed, args.guarded)
    for where, events, state, detail in rows:
        line = "%-21s %-14s %s" % (where, state, detail)
        if state == "double-fire":
            log.warning(line)
        else:
            log.info(line)

    twins = []
    for channel in args.channel:
        body = get(s, "conversations.history", {"channel": channel, "limit": 200},
                   channel)
        if not body:
            continue
        found = mention_twins(body.get("messages") or [], bot_id, user_id)
        twins.extend(found)
        log.info("history    %-10s %d pair(s) after a mention", channel, len(found))
        for ts, _delta, state, detail in found:
            log.info("  %-19s %-14s %s", ts, state, detail)

    state, detail = verdict(rows, twins, known)
    if state in ("confirmed", "configured", "observed"):
        log.warning("verdict    %-14s %s", state, detail)
        log.warning("  repair: keep app_mention for directed commands and guard the "
                    "message handler; ignore any message event whose text contains "
                    "<@%s>", user_id)
        log.warning("  repair: if the message subscription exists for a real "
                    "feature, keep it and add the guard rather than unsubscribing")
        log.warning("  repair: do not reach for a dedupe store; these are two event "
                    "ids and an idempotency key will pass both, correctly")
        return 1
    log.info("verdict    %-14s %s", state, detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-event-overlap-audit.mjs",
"js": '''/**
 * Find the subscription overlap that delivers one mention as two events.
 *
 * Read only. One auth.test for the bot's own identifiers, one optional
 * apps.manifest.export on an app configuration token for the subscribed events,
 * and one page of conversations.history per channel you name. Nothing is
 * posted, edited or unsubscribed: the overlap is a property of the subscription
 * list, and this prints the guard you would add.
 */

const API = 'https://slack.com/api/';

// One human action, and every event Slack sends because of it. These are not
// two names for one delivery: app_mention and message.channels are separate
// events with separate ids, arriving inside the same tick.
const MENTION_TRIGGERS = new Map([
  ['group DM', ['app_mention', 'message.mpim']],
  ['private channel', ['app_mention', 'message.groups']],
  ['public channel', ['app_mention', 'message.channels']],
]);

const RANK = { 'double-fire': 0, guarded: 1, 'single-path': 2, 'not-subscribed': 3 };

// Slack retries at roughly 60 and 300 seconds. A pair spaced like that is one
// event delivered twice; a pair under a second apart is two events delivered
// once each. The regimes do not overlap.
const RETRY_WINDOWS = [[55, 70], [285, 320]];
const SIMULTANEOUS = 1.0;

/**
 * Which human action is delivered twice. Pure.
 * Four states rather than two: a subscribed pair with a declared guard is a
 * resolved overlap, not a finding, because plenty of apps need
 * message.channels for a real feature and will keep it forever.
 */
export function overlap(subscribed, guarded = []) {
  const subs = new Set((subscribed ?? []).map((e) => String(e).trim()).filter(Boolean));
  const guards = new Set((guarded ?? []).map((e) => String(e).trim()).filter(Boolean));
  const rows = [];
  for (const where of [...MENTION_TRIGGERS.keys()].sort()) {
    const [mention, msg] = MENTION_TRIGGERS.get(where);
    const both = subs.has(mention) && subs.has(msg);
    if (both && (guards.has(msg) || guards.has(mention))) {
      rows.push([where, [mention, msg], 'guarded',
        `both events are subscribed and the ${msg} handler declares that it skips ` +
        'messages addressed to the bot']);
    } else if (both) {
      rows.push([where, [mention, msg], 'double-fire',
        `${mention} and ${msg} are both subscribed, so one mention in a ${where} is ` +
        'two deliveries with two event ids and two handler runs']);
    } else if (subs.has(mention) || subs.has(msg)) {
      const only = subs.has(mention) ? mention : msg;
      rows.push([where, [mention, msg], 'single-path',
        `only ${only} is subscribed, so a mention in a ${where} reaches the app once`]);
    } else {
      rows.push([where, [mention, msg], 'not-subscribed',
        `neither ${mention} nor ${msg} is subscribed, so nothing arrives from a ` +
        `${where} at all`]);
    }
  }
  return rows.sort((a, b) => (RANK[a[2]] ?? 9) - (RANK[b[2]] ?? 9)
    || a[0].localeCompare(b[0]));
}

/**
 * What the spacing between two consecutive replies means. Pure.
 * The shortest function here and the one carrying the argument.
 */
export function gapState(delta) {
  // Number(null) is 0 and Number('') is 0, either of which would sail through a
  // finiteness check and be reported as a sub-second gap. Reject the absent
  // value before the arithmetic rather than after it.
  const d = (delta === null || delta === undefined || delta === '')
    ? NaN : Math.abs(Number(delta));
  if (!Number.isFinite(d)) {
    return ['unattributed', 'the two timestamps could not be read as numbers'];
  }
  if (d < SIMULTANEOUS) {
    return ['simultaneous',
      `${d.toFixed(3)}s apart, which is two events for one message handled in the ` +
      'same tick'];
  }
  for (const [lo, hi] of RETRY_WINDOWS) {
    if (d >= lo && d <= hi) {
      return ['retry-shaped',
        `${d.toFixed(1)}s apart, which is Slack's retry schedule and not a second ` +
        'subscription'];
    }
  }
  return ['unattributed',
    `${d.toFixed(1)}s apart, which matches neither a double subscription nor a retry`];
}

/**
 * Reply pairs in one page of history, and what put them there. Pure.
 * A run of replies is only attributed to this note when the human message in
 * front of it actually mentions the bot; two replies with no mention before
 * them is an echo loop or two workers.
 */
export function mentionTwins(messages, botId, botUserId) {
  const ordered = (messages ?? [])
    .filter((m) => m && typeof m === 'object')
    .slice()
    .sort((a, b) => Number(a.ts ?? 0) - Number(b.ts ?? 0));
  const handle = botUserId ? `<@${botUserId}>` : '';
  const mine = (m) => Boolean(botId) && m.bot_id === botId;

  const rows = [];
  let i = 0;
  while (i < ordered.length) {
    const trigger = ordered[i];
    if (mine(trigger)) { i += 1; continue; }
    const run = [];
    let j = i + 1;
    while (j < ordered.length && mine(ordered[j])) { run.push(ordered[j]); j += 1; }
    if (run.length >= 2) {
      const delta = Number(run[1].ts ?? 0) - Number(run[0].ts ?? 0);
      const addressed = Boolean(handle) && String(trigger.text ?? '').includes(handle);
      const [state, detail] = addressed ? gapState(delta) : ['unattributed',
        'the message before this pair does not mention the bot, so the pair belongs ' +
        'to the echo loop or the duplicate message note rather than to this one'];
      rows.push([trigger.ts, delta, state, detail]);
    }
    i = j > i ? j : i + 1;
  }
  return rows;
}

/** Combine the configuration finding with the behavioural one. Pure. */
export function verdict(overlapRows, twinRows, subscriptionsKnown = true) {
  const doubled = (overlapRows ?? []).filter((r) => r[2] === 'double-fire');
  const twins = (twinRows ?? []).filter((r) => r[2] === 'simultaneous');
  const retries = (twinRows ?? []).filter((r) => r[2] === 'retry-shaped');
  if (doubled.length && twins.length) {
    return ['confirmed',
      `${doubled.length} subscription overlap(s) and ${twins.length} reply pair(s) ` +
      'under a second apart. The configuration explains the behaviour'];
  }
  if (doubled.length) {
    return ['configured',
      `${doubled.length} subscription overlap(s). Nothing has to have gone wrong ` +
      'yet: a mention in one of these conversations is two deliveries whether or ' +
      'not anyone has complained'];
  }
  if (twins.length && !subscriptionsKnown) {
    return ['observed',
      `${twins.length} reply pair(s) under a second apart, with no subscription ` +
      'list read. Export the manifest, or pass --subscribed, to name the cause'];
  }
  if (twins.length) {
    return ['elsewhere',
      `${twins.length} reply pair(s) under a second apart, and no overlap in the ` +
      'subscription list. Two processes running the same handler will also produce ' +
      'this'];
  }
  if (retries.length) {
    return ['retries',
      `${retries.length} pair(s) spaced like Slack's retry schedule, which is a ` +
      'dedupe question rather than a subscription one'];
  }
  return ['clear', 'no mention in this workspace is being delivered twice'];
}

async function get(token, method, params, label) {
  const qs = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) {
    console.warn(`${label.padEnd(10)} ${'unavailable'.padEnd(14)} ${body.error}`);
    return null;
  }
  return body;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}; channels:history and the identity read are enough`);
    process.exitCode = 2;
    return;
  }
  const configTokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');
  const guarded = argAll(args, '--guarded');
  const channels = argAll(args, '--channel');

  const who = await get(token, 'auth.test', {}, 'auth.test');
  if (!who) { process.exitCode = 2; return; }
  const botId = who.bot_id;
  const userId = who.user_id;
  console.log(`identity   ${userId} in ${who.team}, bot_id ${botId}`);

  let subscribed = argAll(args, '--subscribed');
  let known = subscribed.length > 0;
  const configToken = process.env[configTokenEnv];
  if (configToken && appId) {
    const body = await get(configToken, 'apps.manifest.export', { app_id: appId },
      'manifest');
    if (body) {
      subscribed = body?.manifest?.settings?.event_subscriptions?.bot_events ?? [];
      known = true;
    }
  }
  if (!known) {
    console.log('manifest   skipped        no subscription list was read; pass ' +
      '--subscribed for each event on the configuration screen');
  }

  const rows = overlap(subscribed, guarded);
  for (const [where, , state, detail] of rows) {
    const line = `${where.padEnd(21)} ${state.padEnd(14)} ${detail}`;
    if (state === 'double-fire') console.warn(line); else console.log(line);
  }

  const twins = [];
  for (const channel of channels) {
    // eslint-disable-next-line no-await-in-loop
    const body = await get(token, 'conversations.history',
      { channel, limit: '200' }, channel);
    if (!body) continue;
    const found = mentionTwins(body.messages ?? [], botId, userId);
    twins.push(...found);
    console.log(`history    ${channel.padEnd(10)} ${found.length} pair(s) after a ` +
      'mention');
    for (const [ts, , state, detail] of found) {
      console.log(`  ${String(ts).padEnd(19)} ${state.padEnd(14)} ${detail}`);
    }
  }

  const [state, detail] = verdict(rows, twins, known);
  if (state === 'confirmed' || state === 'configured' || state === 'observed') {
    console.warn(`verdict    ${state.padEnd(14)} ${detail}`);
    console.warn('  repair: keep app_mention for directed commands and guard the ' +
      `message handler; ignore any message event whose text contains <@${userId}>`);
    console.warn('  repair: if the message subscription exists for a real feature, ' +
      'keep it and add the guard rather than unsubscribing');
    console.warn('  repair: do not reach for a dedupe store; these are two event ' +
      'ids and an idempotency key will pass both, correctly');
    process.exitCode = 1;
  } else {
    console.log(`verdict    ${state.padEnd(14)} ${detail}`);
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are about the three ways this note could be wrong. A guard has to close the finding, or an app that legitimately needs <code>message.channels</code> gets told to break a feature. A pair sixty seconds apart has to come back <code>retry-shaped</code> and be handed to the note that owns retries, because that is the boundary this whole script exists to draw. And a pair with no mention in front of it must not be attributed here at all, since a bot answering itself is a loop and not an overlap.",
"test_py_file": "test_slack_event_overlap_audit.py",
"test_py": '''from slack_event_overlap_audit import gap_state, mention_twins, overlap, verdict


def rows_by_where(rows):
    return {r[0]: r for r in rows}


def test_both_events_subscribed_is_the_finding():
    row = rows_by_where(overlap(["app_mention", "message.channels"]))["public channel"]
    assert row[2] == "double-fire"
    assert "two deliveries" in row[3]


def test_one_event_alone_arrives_once():
    row = rows_by_where(overlap(["app_mention"]))["public channel"]
    assert row[2] == "single-path"
    row = rows_by_where(overlap(["message.channels"]))["public channel"]
    assert row[2] == "single-path"


def test_a_declared_guard_closes_the_finding():
    rows = rows_by_where(overlap(["app_mention", "message.channels"],
                                 ["message.channels"]))
    assert rows["public channel"][2] == "guarded"


def test_a_guard_on_one_channel_type_does_not_cover_another():
    rows = rows_by_where(overlap(
        ["app_mention", "message.channels", "message.groups"], ["message.channels"]))
    assert rows["public channel"][2] == "guarded"
    assert rows["private channel"][2] == "double-fire"


def test_private_channels_and_group_dms_have_their_own_message_event():
    rows = rows_by_where(overlap(["app_mention", "message.mpim"]))
    assert rows["group DM"][2] == "double-fire"
    assert rows["public channel"][2] == "single-path"


def test_nothing_subscribed_is_not_a_finding():
    assert rows_by_where(overlap([]))["public channel"][2] == "not-subscribed"
    assert overlap(None)[0][2] == "not-subscribed"


def test_findings_sort_above_resolved_rows():
    rows = overlap(["app_mention", "message.channels", "message.groups"],
                   ["message.channels"])
    assert rows[0][2] == "double-fire"


def test_a_sub_second_gap_is_two_events_for_one_message():
    state, detail = gap_state(0.12)
    assert state == "simultaneous"
    assert "same tick" in detail


def test_a_sixty_second_gap_belongs_to_the_retry_note():
    assert gap_state(60.4)[0] == "retry-shaped"
    assert gap_state(300.0)[0] == "retry-shaped"
    assert "retry schedule" in gap_state(60.4)[1]


def test_a_gap_matching_neither_regime_is_not_attributed():
    assert gap_state(9.0)[0] == "unattributed"
    assert gap_state(None)[0] == "unattributed"
    assert gap_state("later")[0] == "unattributed"


def test_two_replies_to_a_mention_are_the_symptom():
    msgs = [
        {"ts": "1000.000000", "user": "U9", "text": "hey <@U0BOT> status"},
        {"ts": "1000.400000", "bot_id": "B1", "text": "ok"},
        {"ts": "1000.480000", "bot_id": "B1", "text": "ok"},
    ]
    rows = mention_twins(msgs, "B1", "U0BOT")
    assert len(rows) == 1
    assert rows[0][2] == "simultaneous"


def test_history_arriving_newest_first_is_ordered_before_it_is_read():
    msgs = [
        {"ts": "1000.480000", "bot_id": "B1", "text": "ok"},
        {"ts": "1000.400000", "bot_id": "B1", "text": "ok"},
        {"ts": "1000.000000", "user": "U9", "text": "hey <@U0BOT> status"},
    ]
    assert mention_twins(msgs, "B1", "U0BOT")[0][2] == "simultaneous"


def test_a_pair_with_no_mention_in_front_of_it_is_not_this_note():
    msgs = [
        {"ts": "1000.000000", "user": "U9", "text": "morning everyone"},
        {"ts": "1000.400000", "bot_id": "B1", "text": "ok"},
        {"ts": "1000.480000", "bot_id": "B1", "text": "ok"},
    ]
    rows = mention_twins(msgs, "B1", "U0BOT")
    assert rows[0][2] == "unattributed"
    assert "echo loop" in rows[0][3]


def test_a_single_reply_to_a_mention_is_not_a_pair():
    msgs = [
        {"ts": "1000.000000", "user": "U9", "text": "<@U0BOT> status"},
        {"ts": "1000.400000", "bot_id": "B1", "text": "ok"},
    ]
    assert mention_twins(msgs, "B1", "U0BOT") == []


def test_replies_from_another_bot_are_not_counted_as_ours():
    msgs = [
        {"ts": "1000.000000", "user": "U9", "text": "<@U0BOT> status"},
        {"ts": "1000.400000", "bot_id": "B2", "text": "ok"},
        {"ts": "1000.480000", "bot_id": "B2", "text": "ok"},
    ]
    assert mention_twins(msgs, "B1", "U0BOT") == []


def test_a_retry_shaped_pair_after_a_mention_is_named_as_such():
    msgs = [
        {"ts": "1000.000000", "user": "U9", "text": "<@U0BOT> status"},
        {"ts": "1000.400000", "bot_id": "B1", "text": "ok"},
        {"ts": "1060.500000", "bot_id": "B1", "text": "ok"},
    ]
    assert mention_twins(msgs, "B1", "U0BOT")[0][2] == "retry-shaped"


def test_the_configuration_alone_is_enough_to_report():
    rows = overlap(["app_mention", "message.channels"])
    state, detail = verdict(rows, [])
    assert state == "configured"
    assert "whether or not anyone has complained" in detail


def test_configuration_plus_observed_pairs_is_confirmed():
    rows = overlap(["app_mention", "message.channels"])
    twins = [("1000.0", 0.08, "simultaneous", "")]
    assert verdict(rows, twins)[0] == "confirmed"


def test_pairs_without_a_subscription_list_ask_for_the_manifest():
    twins = [("1000.0", 0.08, "simultaneous", "")]
    assert verdict(overlap([]), twins, subscriptions_known=False)[0] == "observed"


def test_pairs_with_a_clean_subscription_list_point_somewhere_else():
    twins = [("1000.0", 0.08, "simultaneous", "")]
    state, detail = verdict(overlap(["app_mention"]), twins)
    assert state == "elsewhere"
    assert "Two processes" in detail


def test_retry_shaped_pairs_alone_are_handed_to_the_dedupe_note():
    twins = [("1000.0", 60.1, "retry-shaped", "")]
    assert verdict(overlap(["app_mention"]), twins)[0] == "retries"


def test_no_overlap_and_no_pairs_is_clear():
    assert verdict(overlap(["app_mention"]), [])[0] == "clear"
''',
"test_js_file": "slack-event-overlap-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  gapState, mentionTwins, overlap, verdict,
} from './slack-event-overlap-audit.mjs';

const byWhere = (rows) => Object.fromEntries(rows.map((r) => [r[0], r]));

test('both events subscribed is the finding', () => {
  const row = byWhere(overlap(['app_mention', 'message.channels']))['public channel'];
  assert.equal(row[2], 'double-fire');
  assert.match(row[3], /two deliveries/);
});

test('one event alone arrives once', () => {
  assert.equal(byWhere(overlap(['app_mention']))['public channel'][2], 'single-path');
  assert.equal(byWhere(overlap(['message.channels']))['public channel'][2],
    'single-path');
});

test('a declared guard closes the finding', () => {
  const rows = byWhere(overlap(['app_mention', 'message.channels'],
    ['message.channels']));
  assert.equal(rows['public channel'][2], 'guarded');
});

test('a guard on one channel type does not cover another', () => {
  const rows = byWhere(overlap(
    ['app_mention', 'message.channels', 'message.groups'], ['message.channels']));
  assert.equal(rows['public channel'][2], 'guarded');
  assert.equal(rows['private channel'][2], 'double-fire');
});

test('private channels and group dms have their own message event', () => {
  const rows = byWhere(overlap(['app_mention', 'message.mpim']));
  assert.equal(rows['group DM'][2], 'double-fire');
  assert.equal(rows['public channel'][2], 'single-path');
});

test('nothing subscribed is not a finding', () => {
  assert.equal(byWhere(overlap([]))['public channel'][2], 'not-subscribed');
  assert.equal(overlap(null)[0][2], 'not-subscribed');
});

test('findings sort above resolved rows', () => {
  const rows = overlap(['app_mention', 'message.channels', 'message.groups'],
    ['message.channels']);
  assert.equal(rows[0][2], 'double-fire');
});

test('a sub second gap is two events for one message', () => {
  const [state, detail] = gapState(0.12);
  assert.equal(state, 'simultaneous');
  assert.match(detail, /same tick/);
});

test('a sixty second gap belongs to the retry note', () => {
  assert.equal(gapState(60.4)[0], 'retry-shaped');
  assert.equal(gapState(300)[0], 'retry-shaped');
  assert.match(gapState(60.4)[1], /retry schedule/);
});

test('a gap matching neither regime is not attributed', () => {
  assert.equal(gapState(9)[0], 'unattributed');
  assert.equal(gapState(null)[0], 'unattributed');
  assert.equal(gapState('later')[0], 'unattributed');
});

test('two replies to a mention are the symptom', () => {
  const msgs = [
    { ts: '1000.000000', user: 'U9', text: 'hey <@U0BOT> status' },
    { ts: '1000.400000', bot_id: 'B1', text: 'ok' },
    { ts: '1000.480000', bot_id: 'B1', text: 'ok' },
  ];
  const rows = mentionTwins(msgs, 'B1', 'U0BOT');
  assert.equal(rows.length, 1);
  assert.equal(rows[0][2], 'simultaneous');
});

test('history arriving newest first is ordered before it is read', () => {
  const msgs = [
    { ts: '1000.480000', bot_id: 'B1', text: 'ok' },
    { ts: '1000.400000', bot_id: 'B1', text: 'ok' },
    { ts: '1000.000000', user: 'U9', text: 'hey <@U0BOT> status' },
  ];
  assert.equal(mentionTwins(msgs, 'B1', 'U0BOT')[0][2], 'simultaneous');
});

test('a pair with no mention in front of it is not this note', () => {
  const msgs = [
    { ts: '1000.000000', user: 'U9', text: 'morning everyone' },
    { ts: '1000.400000', bot_id: 'B1', text: 'ok' },
    { ts: '1000.480000', bot_id: 'B1', text: 'ok' },
  ];
  const rows = mentionTwins(msgs, 'B1', 'U0BOT');
  assert.equal(rows[0][2], 'unattributed');
  assert.match(rows[0][3], /echo loop/);
});

test('a single reply to a mention is not a pair', () => {
  const msgs = [
    { ts: '1000.000000', user: 'U9', text: '<@U0BOT> status' },
    { ts: '1000.400000', bot_id: 'B1', text: 'ok' },
  ];
  assert.deepEqual(mentionTwins(msgs, 'B1', 'U0BOT'), []);
});

test('replies from another bot are not counted as ours', () => {
  const msgs = [
    { ts: '1000.000000', user: 'U9', text: '<@U0BOT> status' },
    { ts: '1000.400000', bot_id: 'B2', text: 'ok' },
    { ts: '1000.480000', bot_id: 'B2', text: 'ok' },
  ];
  assert.deepEqual(mentionTwins(msgs, 'B1', 'U0BOT'), []);
});

test('a retry shaped pair after a mention is named as such', () => {
  const msgs = [
    { ts: '1000.000000', user: 'U9', text: '<@U0BOT> status' },
    { ts: '1000.400000', bot_id: 'B1', text: 'ok' },
    { ts: '1060.500000', bot_id: 'B1', text: 'ok' },
  ];
  assert.equal(mentionTwins(msgs, 'B1', 'U0BOT')[0][2], 'retry-shaped');
});

test('the configuration alone is enough to report', () => {
  const [state, detail] = verdict(overlap(['app_mention', 'message.channels']), []);
  assert.equal(state, 'configured');
  assert.match(detail, /whether or not anyone has complained/);
});

test('configuration plus observed pairs is confirmed', () => {
  const twins = [['1000.0', 0.08, 'simultaneous', '']];
  assert.equal(verdict(overlap(['app_mention', 'message.channels']), twins)[0],
    'confirmed');
});

test('pairs without a subscription list ask for the manifest', () => {
  const twins = [['1000.0', 0.08, 'simultaneous', '']];
  assert.equal(verdict(overlap([]), twins, false)[0], 'observed');
});

test('pairs with a clean subscription list point somewhere else', () => {
  const twins = [['1000.0', 0.08, 'simultaneous', '']];
  const [state, detail] = verdict(overlap(['app_mention']), twins);
  assert.equal(state, 'elsewhere');
  assert.match(detail, /Two processes/);
});

test('retry shaped pairs alone are handed to the dedupe note', () => {
  const twins = [['1000.0', 60.1, 'retry-shaped', '']];
  assert.equal(verdict(overlap(['app_mention']), twins)[0], 'retries');
});

test('no overlap and no pairs is clear', () => {
  assert.equal(verdict(overlap(['app_mention']), [])[0], 'clear');
});
''',
"faq": [
 ("I added a dedupe store keyed on event_id and it still replies twice. Why?",
  "Because your dedupe store is working correctly and there is nothing here for it to catch. app_mention and message.channels are two different events with two different event_id values, so an idempotency key sees two distinct events and passes both, which is exactly what you want it to do when two distinct events arrive. Deduplication defends against one event being delivered more than once. This is two events being delivered once each."),
 ("How do I tell this apart from a retry without reading any configuration?",
  "Subtract the two timestamps. A double subscription is handled in the same tick and the copies land milliseconds apart, typically under half a second. Slack's retry schedule is roughly sixty seconds and then five minutes, so retried copies land a minute or more apart. Nothing lands in between, which is why one subtraction is enough to pick the note you should be reading."),
 ("Should I just unsubscribe from message.channels?",
  "Only if nothing needs it. Many apps subscribe to messages for a genuine feature, such as noticing links or keywords, and in that case the pair stays subscribed forever and the overlap is permanent. The correct repair then is a guard in the message handler: skip any message whose text contains your bot user id, and let app_mention own everything addressed to you. The script reports a declared guard as resolved rather than insisting the subscription go."),
 ("Why guard the message handler rather than the app_mention one?",
  "Because app_mention is the narrower event and the better one to keep for directed commands. It carries the mention semantics, it never fires on your own posts, and it is what the feature was written against. The general message handler is the one that was never meant to answer commands, so it is the one that should learn to step aside."),
 ("What about a one-to-one DM with the bot? Does that double up too?",
  "It does not need a mention to reach you, which changes the shape of the problem. In a DM the app already receives message.im for everything said to it, so a guard written as &ldquo;ignore anything that mentions me&rdquo; can silence the DM path entirely if the same handler serves both. Guard on the pairing rather than on the mention alone: skip a message event only in the conversation types where app_mention would also have fired."),
],
"related": [
 ("/slack/duplicate-messages-no-dedupe/", "counting the copies once they are in the channel"),
 ("/slack/duplicate-processing-on-retry/", "the other twin, arriving sixty seconds later"),
 ("/slack/bot-message-echo-loop/", "when the second message is your own and you answer it"),
],
"citations": [CITE_APP_MENTION, CITE_MESSAGE_EVENT, CITE_EVENTS, CITE_CONV_HISTORY],
})

GUIDES.append({
"slug": "http-or-dead-tunnel-request-url",
"title": "The Request URL verified once, on a laptop that is now closed",
"description": "A URL that passed the handshake on somebody's ngrok tunnel still reads as configured. Classify the host from the manifest, without sending it any traffic.",
"h1": "The Request URL verified once, on a laptop that is now closed",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack request url ngrok expired", "slack events not received production",
             "slack request url http not allowed", "slack app dev tunnel request url",
             "slack request url points to localhost"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The app configuration page has a green tick next to the Request URL. Somebody checked, twice. Event subscriptions are on, the scopes are right, the bot is in the channel, and nothing has arrived for four months.</p><p>Read the URL rather than the tick. It says <code>https://a1b2c3d4.ngrok.io/slack/events</code>, and it verified perfectly on the afternoon it was pasted in, from a laptop that has since been closed, reimaged and handed to somebody else. The tick records that the handshake succeeded once. It is not a claim about now.",
"short_answer": """<p>A Request URL that verified is not a Request URL that works. Verification is a single exchange at configuration time; delivery is every day afterwards, to whatever that hostname resolves to today. Development tunnels satisfy Slack's requirements perfectly while they are running, so a URL pasted in during development verifies, gets forgotten, and leaves a production app whose configuration <em>looks</em> correct and whose events go nowhere.</p>
<p>The whole finding is in the string. The script exports the manifest, walks <strong>every</strong> surface that carries a URL &mdash; events, interactivity, message menu options, and each slash command &mdash; and classifies each host: not <code>https</code>, a known tunnel domain, an unroutable name or private address, a bare IP literal, or production-shaped. Then it lets Socket Mode downgrade the entire report, because an app on Socket Mode does not use these URLs at all. <strong>Nothing is sent to your endpoint.</strong> A detector that dials a production Request URL to see what answers has started participating in the incident it was asked to describe.</p>""",
"problem": """<p>The thing that makes this expensive is that every screen you would think to check is green. The URL is present. It is <code>https</code>, usually. It was verified, and Slack remembers that it was. Event subscriptions are enabled and list the events you expect. There is no error state anywhere in the configuration, because from Slack's point of view nothing is wrong with the configuration: the URL is well formed and it passed its handshake.</p>
<p>And the app is often not new. It ran, in development, on the machine where the tunnel lived, and everybody who saw it saw it work. What shipped was the code, and the code was fine. What did not ship was the URL, because the URL is not in the repository and is not in the deployment and is not in the review. It is in a web form that one person filled in six months ago.</p>
<p>The variants all end the same way. A tunnel host that no longer resolves. A <code>http://</code> URL that a colleague swears used to work and could never have verified. A hostname that resolves only inside the VPC, so it is reachable from every machine anybody tries it from and from nothing Slack owns. A certificate that expired last Tuesday. In each case the app is not broken and not misconfigured in any way an error message can express: it is pointed at an address that no longer answers.</p>""",
"why": """<p><strong>Verification is a moment and delivery is a habit.</strong> Slack checks the URL once, when you save it, and then trusts it. There is no periodic revalidation, so the green tick is a fact about an afternoon in March and says nothing about today. Treating it as a health indicator is the mistake at the centre of this note.</p>
<p><strong>A tunnel is indistinguishable from production while it is up.</strong> That is what makes it dangerous rather than obviously wrong. It presents a valid publicly trusted certificate, it answers the challenge, it delivers events, and every check anybody performs during development passes. The failure is deferred to the moment the process is killed, which is a moment nobody logs.</p>
<p><strong>Slack has no notion of environments, so there is exactly one URL per app.</strong> There is no staging slot, no per-branch override, no environment variable. Whatever is in that field is what production uses. That single fact is why the repair is two apps rather than a better URL, and it is worth saying out loud because teams keep looking for the environment switch.</p>
<p><strong>This is not the handshake failing.</strong> A URL that never verified is a different note with a different repair: you replay the exchange and find the redirect, the auth wall or the framework that swallowed the body. Here the exchange succeeded and the address went stale afterwards. Same field, opposite fault, and the diagnostic that solves one is useless for the other.</p>
<p><strong>The detector must not send anything to the endpoint, and that is a design decision rather than a limitation.</strong> Your Request URL is a production endpoint that answers Slack. A script that dials it adds an unsigned request to whatever is already going wrong, may trip an alert, and proves less than the string does: a host that answers a bare GET can still be the wrong deployment. The classification and the records you already hold are both stronger evidence and free of side effects.</p>""",
"steps": [
 {"h": "Export the manifest, or read one from a file",
  "body": """<p>An app configuration token and <code>apps.manifest.export</code> return the whole configuration. If you do not have one, download the manifest from the app page and pass <code>--manifest app.json</code>; the check is entirely offline from that point, which also makes it something you can run in CI against a manifest in the repository.</p>"""},
 {"h": "Walk every surface, not just the events one",
  "body": """<p><code>surfaces</code> yields the event subscriptions URL, the interactivity URL, the message menu options URL and one row per slash command. These drift independently. The commonest half-repair in this whole area is fixing the events URL and leaving three slash commands pointed at a tunnel.</p>"""},
 {"h": "Classify each host from the string alone",
  "body": """<p><code>url_verdict</code> returns <code>not-https</code>, <code>ephemeral-tunnel</code>, <code>unroutable</code>, <code>bare-ip</code> or <code>production-shaped</code>. It sends nothing. <code>production-shaped</code> deliberately does not mean healthy; it means this script has no complaint about the address, which is a much smaller claim.</p>"""},
 {"h": "Let Socket Mode downgrade the whole report",
  "body": """<p>If <code>settings.socket_mode_enabled</code> is true, none of these URLs is used for delivery: events, interactions and commands all arrive over the socket. The rows become <code>dormant</code>, still worth cleaning up before somebody turns Socket Mode off, but not the cause of today's silence.</p>"""},
 {"h": "Bring the records you already have",
  "body": """<p>Two numbers from your own side settle it. <code>--last-delivery</code> is when your endpoint last logged a request from Slack, and <code>--retry-reason</code> is the <code>X-Slack-Retry-Reason</code> value on the last one it saw. <code>connection_failed</code> or <code>ssl_error</code> against a tunnel host is as conclusive as this gets.</p>"""},
 {"h": "Print the repair, including the part about two apps",
  "body": """<p>Point every surface at the production hostname and re-verify. Then keep development in a separate Slack app with its own manifest, because there is no environment switch and the alternative is that somebody pastes a tunnel URL into the production app again next quarter.</p>"""},
],
"verify": """<p>After the URLs are repointed and re-verified, re-run against the exported manifest. Every surface should read <code>production-shaped</code>, and the last delivery should be minutes old rather than months.</p>
<pre><code class="language-bash">python3 slack_request_url_origin.py --manifest app.json --last-delivery 2026-08-31 \\
    --retry-reason none
# manifest   4 surface(s), socket mode off
# event subscriptions   production-shaped  hooks.acme.example is a routable public hostname
# interactivity         production-shaped  hooks.acme.example is a routable public hostname
# slash /deploy         production-shaped  hooks.acme.example is a routable public hostname
# records    delivering     a delivery was seen 0.0 day(s) ago
# verdict    clear          no configured URL points somewhere Slack cannot reach</code></pre>""",
"code_intro": "Two pure functions and a manifest. <code>url_verdict</code> is the whole detector and it never opens a socket: it takes one string and returns which of six things that string is, which is more than a request to the endpoint would tell you and costs your production system nothing. <code>surfaces</code> exists because the events URL is the one everybody remembers and the slash commands are the ones that get left behind. <code>record_verdict</code> reads the two facts your own logs already hold, and <code>verdict</code> is where a suspicious hostname and a silent endpoint become one sentence.",
"py_file": "slack_request_url_origin.py",
"py": '''"""Classify every Request URL an app has configured, without dialling any of them.

Read only, and deliberately more than that: this sends nothing at all to your
own endpoint. One optional apps.manifest.export on an app configuration token,
or a manifest file you exported yourself, and everything after that is string
work. A detector that dials a production Request URL to see what answers has
started participating in the incident it was asked to describe.
"""
import argparse
import datetime
import json
import logging
import os
import sys
import urllib.parse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_request_url_origin")

API = "https://slack.com/api/"

# Hosts handed out by development tunnels. Every one of these satisfies Slack
# completely while the tunnel is running, which is exactly why a URL pointing at
# one verifies, is forgotten, and then quietly stops existing.
TUNNEL_SUFFIXES = (
    ".ngrok.io", ".ngrok-free.app", ".ngrok.app", ".ngrok.dev",
    ".loca.lt", ".trycloudflare.com", ".serveo.net", ".localhost.run",
    ".lhr.life", ".telebit.io", ".pinggy.link", ".tunnelmole.net",
    ".devtunnels.ms", ".ngrok-free.dev",
)

# Names that resolve to something only you can see.
UNROUTABLE_NAMES = ("localhost", "localhost.localdomain")
UNROUTABLE_SUFFIXES = (".local", ".internal", ".localdomain", ".localhost",
                       ".test", ".invalid", ".home.arpa")

# What Slack puts in X-Slack-Retry-Reason, and what each one means about the
# far end. These come out of your own access logs; none of them is produced by
# anything this script does.
RETRY_REASONS = {
    "connection_failed": "the connection could not be established at all, which "
                         "is what a closed tunnel looks like from Slack's side",
    "ssl_error": "the certificate could not be validated, which is what an "
                 "expired or self-signed certificate looks like",
    "http_timeout": "the connection was accepted and nothing answered within "
                    "three seconds",
    "http_error": "the endpoint answered with a status Slack does not accept",
}

RANK = {"not-https": 0, "unroutable": 1, "ephemeral-tunnel": 2, "bare-ip": 3,
        "unparseable": 4, "no-url": 5, "production-shaped": 6}

FINDINGS = ("not-https", "unroutable", "ephemeral-tunnel", "bare-ip", "unparseable")


def _as_ip(host):
    """Parse an IP literal without a regex. Pure. -> (version, octets, text) or None"""
    text = host.replace("[", "").replace("]", "")
    parts = text.split(".")
    if len(parts) == 4 and all(p.isdigit() and 0 < len(p) < 4 for p in parts):
        nums = [int(p) for p in parts]
        if all(n <= 255 for n in nums):
            return (4, nums, text)
    if ":" in text:
        return (6, [], text)
    return None


def _unroutable_ip(ip):
    """Whether an IP literal is one Slack could never reach. Pure.

    The ranges are written out rather than taken from the standard library so
    that this file and its Node counterpart give the same answer. They do not
    otherwise: Python's private-address table has grown to include the
    documentation ranges, and a reader comparing the two outputs on the same URL
    deserves one verdict rather than an argument.
    """
    version, nums, text = ip
    if version == 6:
        h = text.lower()
        return (h in ("::1", "::") or h.startswith("fc") or h.startswith("fd")
                or h.startswith("fe8") or h.startswith("fe9")
                or h.startswith("fea") or h.startswith("feb"))
    a, b = nums[0], nums[1]
    return (a in (0, 10, 127) or (a == 192 and b == 168)
            or (a == 169 and b == 254) or (a == 172 and 16 <= b <= 31))


def url_verdict(url):
    """Classify one configured URL from its text alone. Pure. -> (state, detail)

    Six states, and production-shaped is the weakest of them on purpose: it
    means this script has no complaint about the address, not that anything is
    listening on it. The stronger claim would need a request, and making that
    request is the one thing this script will not do.
    """
    raw = str(url or "").strip()
    if not raw:
        return ("no-url", "no URL is configured for this surface")
    try:
        parsed = urllib.parse.urlsplit(raw)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return ("unparseable", "%s could not be parsed as a URL" % raw)
    if not parsed.scheme or not host:
        return ("unparseable", "%s is not a complete URL" % raw)

    if parsed.scheme.lower() != "https":
        return ("not-https",
                "the scheme is %s. Slack requires https with a publicly trusted "
                "certificate, so this URL cannot have verified in this form"
                % parsed.scheme.lower())
    for suffix in TUNNEL_SUFFIXES:
        if host.endswith(suffix):
            return ("ephemeral-tunnel",
                    "%s is a development tunnel host. It was reachable while the "
                    "tunnel was running, which is how it verified, and it stopped "
                    "existing when that process was killed" % host)
    ip = _as_ip(host)
    if ip is not None:
        if _unroutable_ip(ip):
            return ("unroutable",
                    "%s is not an address Slack can reach from the public "
                    "internet" % host)
        return ("bare-ip",
                "%s is a literal address rather than a name. Slack validates the "
                "certificate for what it dials, and certificates issued to bare "
                "addresses are rare enough to be worth confirming" % host)
    if host in UNROUTABLE_NAMES or host.endswith(UNROUTABLE_SUFFIXES):
        return ("unroutable",
                "%s resolves inside a network Slack is not on" % host)
    return ("production-shaped",
            "%s is a routable public hostname. That is not the same as reachable, "
            "and nothing was sent to it to find out" % host)


def surfaces(manifest):
    """Every place a manifest carries a URL. Pure. -> rows of (surface, url)

    The events URL is the one everybody remembers. Slash commands are the ones
    left behind, because there are several of them and they are on a different
    screen, and a half-repair that fixes events and forgets three commands is
    the commonest outcome in this whole area.
    """
    m = manifest if isinstance(manifest, dict) else {}
    settings = m.get("settings") or {}
    features = m.get("features") or {}
    rows = [
        ("event subscriptions",
         (settings.get("event_subscriptions") or {}).get("request_url")),
        ("interactivity", (settings.get("interactivity") or {}).get("request_url")),
        ("message menu options",
         (settings.get("interactivity") or {}).get("message_menu_options_url")),
    ]
    for cmd in features.get("slash_commands") or []:
        if not isinstance(cmd, dict):
            continue
        rows.append(("slash %s" % (cmd.get("command") or "?"), cmd.get("url")))
    return [(name, url) for name, url in rows if url is not None]


def audit(manifest):
    """Classify every surface, and mark the rows Socket Mode makes moot. Pure.

    Returns rows of (surface, url, state, detail, live), worst first. When
    Socket Mode is on, events, interactions and commands all arrive over the
    socket and none of these URLs is used, so a tunnel host left in the field is
    a tidiness problem rather than the cause of today's silence.
    """
    m = manifest if isinstance(manifest, dict) else {}
    socket = bool((m.get("settings") or {}).get("socket_mode_enabled"))
    rows = []
    for name, url in surfaces(m):
        state, detail = url_verdict(url)
        if socket and state in FINDINGS:
            detail += (". Socket Mode is on, so this URL is not used for delivery "
                       "and this is a cleanup rather than an outage")
        rows.append((name, url, state, detail, not socket))
    return sorted(rows, key=lambda r: (RANK.get(r[2], 9), r[0]))


def record_verdict(days_silent, retry_reason=None):
    """What your own records already say about the far end. Pure.

    Both inputs come from your side of the connection: when your endpoint last
    logged a request from Slack, and the X-Slack-Retry-Reason on the last one it
    saw. Neither requires sending anything to the URL.
    """
    reason = str(retry_reason or "").strip().lower()
    if reason and reason not in ("none", "-"):
        if reason in RETRY_REASONS:
            return ("reason-recorded", "%s: %s" % (reason, RETRY_REASONS[reason]))
        return ("unknown-reason",
                "%s is not a retry reason this script knows; read it against the "
                "Events API documentation rather than assuming it is benign" % reason)
    if days_silent is None:
        return ("no-records",
                "no delivery record was supplied, so the classification above "
                "stands on the URL alone")
    try:
        days = float(days_silent)
    except (TypeError, ValueError):
        return ("no-records", "the last delivery date could not be read")
    if days >= 1.0:
        return ("silent",
                "nothing has been delivered for %.1f day(s)" % days)
    return ("delivering", "a delivery was seen %.1f day(s) ago" % days)


def verdict(rows, record_state):
    """Turn a suspicious address and a silent endpoint into one sentence. Pure."""
    live = [r for r in rows or [] if r[4] and r[2] in FINDINGS]
    dormant = [r for r in rows or [] if not r[4] and r[2] in FINDINGS]
    corroborated = record_state in ("silent", "reason-recorded")
    if live and corroborated:
        return ("dead-endpoint",
                "%d surface(s) point somewhere Slack cannot reach, and your own "
                "records agree that nothing is arriving" % len(live))
    if live:
        return ("suspect-origin",
                "%d surface(s) point at an address that cannot serve production. "
                "Pass --last-delivery to turn this into a closed case" % len(live))
    if dormant:
        return ("dormant",
                "%d surface(s) carry an address that could not serve production, "
                "but Socket Mode is on and none of them is used for delivery"
                % len(dormant))
    if corroborated:
        return ("elsewhere",
                "every configured URL is production-shaped and nothing is arriving "
                "anyway. The endpoint, the handshake or a disabled subscription is "
                "the next place to look")
    return ("clear", "no configured URL points somewhere Slack cannot reach")


def get(session, method, params, label):
    """One GET, asserting on the body rather than the status line."""
    r = session.get(API + method, params=params or {}, timeout=30)
    body = r.json()
    if body.get("ok") is not True:
        log.warning("%-10s %-14s %s", label, "unavailable", body.get("error"))
        return None
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="",
                    help="path to a manifest exported from the app page")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app ID, for the manifest read")
    ap.add_argument("--last-delivery", default="",
                    help="YYYY-MM-DD your endpoint last logged a request from Slack")
    ap.add_argument("--retry-reason", default="",
                    help="the X-Slack-Retry-Reason on the last delivery you saw")
    args = ap.parse_args()

    manifest = None
    if args.manifest:
        manifest = json.loads(open(args.manifest, encoding="utf-8").read())
        manifest = manifest.get("manifest", manifest)
    else:
        token = os.environ.get(args.config_token_env)
        if not token or not args.app_id:
            log.error("supply --manifest, or set %s and pass --app-id; a bot token "
                      "cannot read app configuration", args.config_token_env)
            return 2
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        body = get(s, "apps.manifest.export", {"app_id": args.app_id}, "manifest")
        if not body:
            return 2
        manifest = body.get("manifest") or {}

    rows = audit(manifest)
    socket = bool((manifest.get("settings") or {}).get("socket_mode_enabled"))
    log.info("manifest   %d surface(s), socket mode %s", len(rows),
             "on" if socket else "off")
    for name, url, state, detail, live in rows:
        line = "%-21s %-18s %s" % (name, state if live else "dormant", detail)
        if state in FINDINGS and live:
            log.warning(line)
        else:
            log.info(line)
        log.info("  %-19s %s", "", url)

    days = None
    if args.last_delivery:
        seen = datetime.datetime.strptime(args.last_delivery, "%Y-%m-%d").date()
        days = (datetime.date.today() - seen).days
    rstate, rdetail = record_verdict(days, args.retry_reason)
    log.info("records    %-14s %s", rstate, rdetail)

    state, detail = verdict(rows, rstate)
    if state in ("dead-endpoint", "suspect-origin"):
        log.warning("verdict    %-14s %s", state, detail)
        log.warning("  repair: point every surface above at the production hostname "
                    "and re-verify; the tick records one exchange, not a health check")
        log.warning("  repair: keep development in a separate Slack app with its own "
                    "manifest. Slack has no environments, so two apps is the only "
                    "clean separation")
        log.warning("  repair: put certificate expiry on the same monitor that "
                    "watches the endpoint, because an expired certificate reads as "
                    "ssl_error and nothing else")
        return 1
    log.info("verdict    %-14s %s", state, detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-request-url-origin.mjs",
"js": '''/**
 * Classify every Request URL an app has configured, without dialling any of them.
 *
 * Read only, and deliberately more than that: this sends nothing at all to your
 * own endpoint. One optional apps.manifest.export on an app configuration
 * token, or a manifest file you exported yourself, and everything after that is
 * string work.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Hosts handed out by development tunnels. Every one satisfies Slack completely
// while the tunnel is running, which is why a URL pointing at one verifies, is
// forgotten, and then quietly stops existing.
const TUNNEL_SUFFIXES = [
  '.ngrok.io', '.ngrok-free.app', '.ngrok.app', '.ngrok.dev',
  '.loca.lt', '.trycloudflare.com', '.serveo.net', '.localhost.run',
  '.lhr.life', '.telebit.io', '.pinggy.link', '.tunnelmole.net',
  '.devtunnels.ms', '.ngrok-free.dev',
];

const UNROUTABLE_NAMES = ['localhost', 'localhost.localdomain'];
const UNROUTABLE_SUFFIXES = ['.local', '.internal', '.localdomain', '.localhost',
  '.test', '.invalid', '.home.arpa'];

const RETRY_REASONS = new Map([
  ['connection_failed', 'the connection could not be established at all, which is ' +
    "what a closed tunnel looks like from Slack's side"],
  ['ssl_error', 'the certificate could not be validated, which is what an expired ' +
    'or self-signed certificate looks like'],
  ['http_timeout', 'the connection was accepted and nothing answered within three ' +
    'seconds'],
  ['http_error', 'the endpoint answered with a status Slack does not accept'],
]);

const RANK = {
  'not-https': 0, unroutable: 1, 'ephemeral-tunnel': 2, 'bare-ip': 3,
  unparseable: 4, 'no-url': 5, 'production-shaped': 6,
};

const FINDINGS = ['not-https', 'unroutable', 'ephemeral-tunnel', 'bare-ip',
  'unparseable'];

/** Parse an IP literal without a regex. Pure. -> {v, nums} or null */
function asIp(host) {
  const h = host.split('[').join('').split(']').join('');
  const parts = h.split('.');
  const digits = (p) => p.length > 0 && p.length < 4
    && [...p].every((c) => c >= '0' && c <= '9');
  if (parts.length === 4 && parts.every(digits)) {
    const nums = parts.map(Number);
    if (nums.every((n) => n <= 255)) return { v: 4, nums, host: h };
  }
  if (h.includes(':')) return { v: 6, nums: [], host: h };
  return null;
}

/** Whether an IP literal is one Slack could never reach. Pure. */
function unroutableIp(ip) {
  if (ip.v === 6) {
    const h = ip.host.toLowerCase();
    return h === '::1' || h === '::' || h.startsWith('fc') || h.startsWith('fd')
      || h.startsWith('fe8') || h.startsWith('fe9') || h.startsWith('fea')
      || h.startsWith('feb');
  }
  const [a, b] = ip.nums;
  return a === 10 || a === 127 || a === 0
    || (a === 192 && b === 168) || (a === 169 && b === 254)
    || (a === 172 && b >= 16 && b <= 31);
}

/**
 * Classify one configured URL from its text alone. Pure. -> [state, detail]
 * production-shaped is the weakest state on purpose: it means this script has
 * no complaint about the address, not that anything is listening on it.
 */
export function urlVerdict(url) {
  const raw = String(url ?? '').trim();
  if (!raw) return ['no-url', 'no URL is configured for this surface'];
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    return ['unparseable', `${raw} could not be parsed as a URL`];
  }
  const host = (parsed.hostname ?? '').toLowerCase();
  if (!host) return ['unparseable', `${raw} is not a complete URL`];

  const scheme = parsed.protocol.replace(':', '').toLowerCase();
  if (scheme !== 'https') {
    return ['not-https',
      `the scheme is ${scheme}. Slack requires https with a publicly trusted ` +
      'certificate, so this URL cannot have verified in this form'];
  }
  if (TUNNEL_SUFFIXES.some((s) => host.endsWith(s))) {
    return ['ephemeral-tunnel',
      `${host} is a development tunnel host. It was reachable while the tunnel ` +
      'was running, which is how it verified, and it stopped existing when that ' +
      'process was killed'];
  }
  const ip = asIp(host);
  if (ip) {
    if (unroutableIp(ip)) {
      return ['unroutable',
        `${host} is not an address Slack can reach from the public internet`];
    }
    return ['bare-ip',
      `${host} is a literal address rather than a name. Slack validates the ` +
      'certificate for what it dials, and certificates issued to bare addresses ' +
      'are rare enough to be worth confirming'];
  }
  if (UNROUTABLE_NAMES.includes(host)
      || UNROUTABLE_SUFFIXES.some((s) => host.endsWith(s))) {
    return ['unroutable', `${host} resolves inside a network Slack is not on`];
  }
  return ['production-shaped',
    `${host} is a routable public hostname. That is not the same as reachable, ` +
    'and nothing was sent to it to find out'];
}

/**
 * Every place a manifest carries a URL. Pure. -> rows of [surface, url]
 * Slash commands are the ones left behind, because there are several of them
 * and they are on a different screen.
 */
export function surfaces(manifest) {
  const m = (manifest && typeof manifest === 'object') ? manifest : {};
  const settings = m.settings ?? {};
  const features = m.features ?? {};
  const rows = [
    ['event subscriptions', settings.event_subscriptions?.request_url],
    ['interactivity', settings.interactivity?.request_url],
    ['message menu options', settings.interactivity?.message_menu_options_url],
  ];
  for (const cmd of features.slash_commands ?? []) {
    if (!cmd || typeof cmd !== 'object') continue;
    rows.push([`slash ${cmd.command ?? '?'}`, cmd.url]);
  }
  return rows.filter(([, url]) => url !== undefined && url !== null);
}

/**
 * Classify every surface, and mark the rows Socket Mode makes moot. Pure.
 * Returns rows of [surface, url, state, detail, live], worst first.
 */
export function audit(manifest) {
  const m = (manifest && typeof manifest === 'object') ? manifest : {};
  const socket = Boolean(m.settings?.socket_mode_enabled);
  const rows = surfaces(m).map(([name, url]) => {
    const [state, base] = urlVerdict(url);
    const detail = (socket && FINDINGS.includes(state))
      ? `${base}. Socket Mode is on, so this URL is not used for delivery and ` +
        'this is a cleanup rather than an outage'
      : base;
    return [name, url, state, detail, !socket];
  });
  return rows.sort((a, b) => (RANK[a[2]] ?? 9) - (RANK[b[2]] ?? 9)
    || a[0].localeCompare(b[0]));
}

/** What your own records already say about the far end. Pure. */
export function recordVerdict(daysSilent, retryReason = null) {
  const reason = String(retryReason ?? '').trim().toLowerCase();
  if (reason && reason !== 'none' && reason !== '-') {
    if (RETRY_REASONS.has(reason)) {
      return ['reason-recorded', `${reason}: ${RETRY_REASONS.get(reason)}`];
    }
    return ['unknown-reason',
      `${reason} is not a retry reason this script knows; read it against the ` +
      'Events API documentation rather than assuming it is benign'];
  }
  if (daysSilent === null || daysSilent === undefined || daysSilent === '') {
    return ['no-records',
      'no delivery record was supplied, so the classification above stands on ' +
      'the URL alone'];
  }
  const days = Number(daysSilent);
  if (!Number.isFinite(days)) {
    return ['no-records', 'the last delivery date could not be read'];
  }
  if (days >= 1) {
    return ['silent', `nothing has been delivered for ${days.toFixed(1)} day(s)`];
  }
  return ['delivering', `a delivery was seen ${days.toFixed(1)} day(s) ago`];
}

/** Turn a suspicious address and a silent endpoint into one sentence. Pure. */
export function verdict(rows, recordState) {
  const live = (rows ?? []).filter((r) => r[4] && FINDINGS.includes(r[2]));
  const dormant = (rows ?? []).filter((r) => !r[4] && FINDINGS.includes(r[2]));
  const corroborated = recordState === 'silent' || recordState === 'reason-recorded';
  if (live.length && corroborated) {
    return ['dead-endpoint',
      `${live.length} surface(s) point somewhere Slack cannot reach, and your own ` +
      'records agree that nothing is arriving'];
  }
  if (live.length) {
    return ['suspect-origin',
      `${live.length} surface(s) point at an address that cannot serve ` +
      'production. Pass --last-delivery to turn this into a closed case'];
  }
  if (dormant.length) {
    return ['dormant',
      `${dormant.length} surface(s) carry an address that could not serve ` +
      'production, but Socket Mode is on and none of them is used for delivery'];
  }
  if (corroborated) {
    return ['elsewhere',
      'every configured URL is production-shaped and nothing is arriving anyway. ' +
      'The endpoint, the handshake or a disabled subscription is the next place ' +
      'to look'];
  }
  return ['clear', 'no configured URL points somewhere Slack cannot reach'];
}

async function get(token, method, params, label) {
  const qs = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) {
    console.warn(`${label.padEnd(10)} ${'unavailable'.padEnd(14)} ${body.error}`);
    return null;
  }
  return body;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const manifestPath = arg(args, '--manifest', '');
  const configTokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');

  let manifest = null;
  if (manifestPath) {
    const parsed = JSON.parse(await readFile(manifestPath, 'utf8'));
    manifest = parsed.manifest ?? parsed;
  } else {
    const token = process.env[configTokenEnv];
    if (!token || !appId) {
      console.error(`supply --manifest, or set ${configTokenEnv} and pass --app-id; ` +
        'a bot token cannot read app configuration');
      process.exitCode = 2;
      return;
    }
    const body = await get(token, 'apps.manifest.export', { app_id: appId },
      'manifest');
    if (!body) { process.exitCode = 2; return; }
    manifest = body.manifest ?? {};
  }

  const rows = audit(manifest);
  const socket = Boolean(manifest.settings?.socket_mode_enabled);
  console.log(`manifest   ${rows.length} surface(s), socket mode ` +
    `${socket ? 'on' : 'off'}`);
  for (const [name, url, state, detail, live] of rows) {
    const line = `${name.padEnd(21)} ${(live ? state : 'dormant').padEnd(18)} ${detail}`;
    if (FINDINGS.includes(state) && live) console.warn(line); else console.log(line);
    console.log(`  ${''.padEnd(19)} ${url}`);
  }

  const lastDelivery = arg(args, '--last-delivery', '');
  let days = null;
  if (lastDelivery) {
    days = (Date.now() - Date.parse(`${lastDelivery}T00:00:00Z`)) / 86400000;
  }
  const [rstate, rdetail] = recordVerdict(days, arg(args, '--retry-reason', ''));
  console.log(`records    ${rstate.padEnd(14)} ${rdetail}`);

  const [state, detail] = verdict(rows, rstate);
  if (state === 'dead-endpoint' || state === 'suspect-origin') {
    console.warn(`verdict    ${state.padEnd(14)} ${detail}`);
    console.warn('  repair: point every surface above at the production hostname ' +
      'and re-verify; the tick records one exchange, not a health check');
    console.warn('  repair: keep development in a separate Slack app with its own ' +
      'manifest. Slack has no environments, so two apps is the only clean ' +
      'separation');
    console.warn('  repair: put certificate expiry on the same monitor that watches ' +
      'the endpoint, because an expired certificate reads as ssl_error and ' +
      'nothing else');
    process.exitCode = 1;
  } else {
    console.log(`verdict    ${state.padEnd(14)} ${detail}`);
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing manifest.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions are mostly about not overclaiming. A public hostname has to come back <code>production-shaped</code> and nothing stronger, because the script did not dial it and must not imply that it did. Socket Mode has to demote every finding to <code>dormant</code>, since an app on a socket is not using these fields at all and reporting an outage there would be a fabrication. And a slash command URL has to be classified alongside the events URL, because the half-repair that fixes one and forgets the others is the failure mode this note exists to prevent twice.",
"test_py_file": "test_slack_request_url_origin.py",
"test_py": '''from slack_request_url_origin import audit, record_verdict, surfaces, url_verdict, verdict


def manifest(events=None, socket=False, commands=None, interactivity=None):
    return {
        "settings": {
            "event_subscriptions": {"request_url": events} if events else {},
            "interactivity": interactivity or {},
            "socket_mode_enabled": socket,
        },
        "features": {"slash_commands": commands or []},
    }


def test_a_tunnel_host_is_the_finding():
    state, detail = url_verdict("https://a1b2c3d4.ngrok.io/slack/events")
    assert state == "ephemeral-tunnel"
    assert "stopped existing" in detail


def test_every_tunnel_vendor_in_the_table_is_recognised():
    for host in ("x.ngrok-free.app", "y.loca.lt", "z.trycloudflare.com",
                 "q.serveo.net", "r.devtunnels.ms"):
        assert url_verdict("https://%s/slack/events" % host)[0] == "ephemeral-tunnel"


def test_plain_http_could_never_have_verified():
    state, detail = url_verdict("http://hooks.acme.example/slack/events")
    assert state == "not-https"
    assert "cannot have verified" in detail


def test_localhost_and_private_addresses_are_unroutable():
    assert url_verdict("https://localhost:3000/slack/events")[0] == "unroutable"
    assert url_verdict("https://api.internal/slack/events")[0] == "unroutable"
    assert url_verdict("https://10.0.4.12/slack/events")[0] == "unroutable"
    assert url_verdict("https://192.168.1.9/slack/events")[0] == "unroutable"
    assert url_verdict("https://172.16.0.1/slack/events")[0] == "unroutable"
    assert url_verdict("https://127.0.0.1/slack/events")[0] == "unroutable"


def test_a_public_ip_literal_is_flagged_for_its_certificate_not_its_routing():
    state, detail = url_verdict("https://203.0.113.44/slack/events")
    assert state == "bare-ip"
    assert "certificate" in detail


def test_a_public_hostname_is_never_called_healthy():
    state, detail = url_verdict("https://hooks.acme.example/slack/events")
    assert state == "production-shaped"
    assert "not the same as reachable" in detail
    assert "nothing was sent to it" in detail


def test_an_empty_or_broken_url_is_said_so_rather_than_guessed():
    assert url_verdict("")[0] == "no-url"
    assert url_verdict(None)[0] == "no-url"
    assert url_verdict("not a url at all")[0] == "unparseable"


def test_slash_commands_are_surfaces_too():
    m = manifest(events="https://hooks.acme.example/e",
                 commands=[{"command": "/deploy",
                            "url": "https://a1.ngrok.io/cmd"}])
    names = [n for n, _ in surfaces(m)]
    assert "event subscriptions" in names
    assert "slash /deploy" in names


def test_the_forgotten_slash_command_outranks_the_healthy_events_url():
    m = manifest(events="https://hooks.acme.example/e",
                 commands=[{"command": "/deploy", "url": "https://a1.ngrok.io/cmd"}])
    rows = audit(m)
    assert rows[0][0] == "slash /deploy"
    assert rows[0][2] == "ephemeral-tunnel"


def test_interactivity_and_menu_urls_are_read_as_well():
    m = manifest(interactivity={"request_url": "https://a1.ngrok.io/i",
                                "message_menu_options_url": "http://x.example/m"})
    states = {n: s for n, _, s, _, _ in audit(m)}
    assert states["interactivity"] == "ephemeral-tunnel"
    assert states["message menu options"] == "not-https"


def test_socket_mode_demotes_every_finding_to_dormant():
    m = manifest(events="https://a1.ngrok.io/slack/events", socket=True)
    rows = audit(m)
    assert rows[0][2] == "ephemeral-tunnel"
    assert rows[0][4] is False
    assert "cleanup rather than an outage" in rows[0][3]
    assert verdict(rows, "no-records")[0] == "dormant"


def test_a_retry_reason_is_translated_rather_than_echoed():
    state, detail = record_verdict(None, "connection_failed")
    assert state == "reason-recorded"
    assert "closed tunnel" in detail
    assert record_verdict(None, "ssl_error")[0] == "reason-recorded"


def test_an_unknown_retry_reason_is_not_waved_through():
    state, detail = record_verdict(None, "something_new")
    assert state == "unknown-reason"
    assert "rather than assuming it is benign" in detail


def test_silence_is_measured_in_days_and_none_means_no_records():
    assert record_verdict(120)[0] == "silent"
    assert record_verdict(0.0)[0] == "delivering"
    assert record_verdict(None)[0] == "no-records"
    assert record_verdict("yesterday")[0] == "no-records"


def test_a_dead_tunnel_plus_a_silent_endpoint_closes_the_case():
    rows = audit(manifest(events="https://a1.ngrok.io/slack/events"))
    assert verdict(rows, "silent")[0] == "dead-endpoint"
    assert verdict(rows, "reason-recorded")[0] == "dead-endpoint"


def test_a_suspect_url_alone_asks_for_the_records():
    rows = audit(manifest(events="https://a1.ngrok.io/slack/events"))
    state, detail = verdict(rows, "no-records")
    assert state == "suspect-origin"
    assert "--last-delivery" in detail


def test_a_clean_url_and_a_silent_endpoint_is_somebody_else_s_note():
    rows = audit(manifest(events="https://hooks.acme.example/slack/events"))
    state, detail = verdict(rows, "silent")
    assert state == "elsewhere"
    assert "handshake" in detail


def test_a_clean_url_and_live_delivery_is_clear():
    rows = audit(manifest(events="https://hooks.acme.example/slack/events"))
    assert verdict(rows, "delivering")[0] == "clear"
''',
"test_js_file": "slack-request-url-origin.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  audit, recordVerdict, surfaces, urlVerdict, verdict,
} from './slack-request-url-origin.mjs';

const manifest = ({
  events = null, socket = false, commands = [], interactivity = {},
} = {}) => ({
  settings: {
    event_subscriptions: events ? { request_url: events } : {},
    interactivity,
    socket_mode_enabled: socket,
  },
  features: { slash_commands: commands },
});

test('a tunnel host is the finding', () => {
  const [state, detail] = urlVerdict('https://a1b2c3d4.ngrok.io/slack/events');
  assert.equal(state, 'ephemeral-tunnel');
  assert.match(detail, /stopped existing/);
});

test('every tunnel vendor in the table is recognised', () => {
  for (const host of ['x.ngrok-free.app', 'y.loca.lt', 'z.trycloudflare.com',
    'q.serveo.net', 'r.devtunnels.ms']) {
    assert.equal(urlVerdict(`https://${host}/slack/events`)[0], 'ephemeral-tunnel');
  }
});

test('plain http could never have verified', () => {
  const [state, detail] = urlVerdict('http://hooks.acme.example/slack/events');
  assert.equal(state, 'not-https');
  assert.match(detail, /cannot have verified/);
});

test('localhost and private addresses are unroutable', () => {
  for (const url of ['https://localhost:3000/slack/events',
    'https://api.internal/slack/events', 'https://10.0.4.12/slack/events',
    'https://192.168.1.9/slack/events', 'https://172.16.0.1/slack/events',
    'https://127.0.0.1/slack/events']) {
    assert.equal(urlVerdict(url)[0], 'unroutable', url);
  }
});

test('a public ip literal is flagged for its certificate not its routing', () => {
  const [state, detail] = urlVerdict('https://203.0.113.44/slack/events');
  assert.equal(state, 'bare-ip');
  assert.match(detail, /certificate/);
});

test('a public hostname is never called healthy', () => {
  const [state, detail] = urlVerdict('https://hooks.acme.example/slack/events');
  assert.equal(state, 'production-shaped');
  assert.match(detail, /not the same as reachable/);
  assert.match(detail, /nothing was sent to it/);
});

test('an empty or broken url is said so rather than guessed', () => {
  assert.equal(urlVerdict('')[0], 'no-url');
  assert.equal(urlVerdict(null)[0], 'no-url');
  assert.equal(urlVerdict('not a url at all')[0], 'unparseable');
});

test('slash commands are surfaces too', () => {
  const m = manifest({
    events: 'https://hooks.acme.example/e',
    commands: [{ command: '/deploy', url: 'https://a1.ngrok.io/cmd' }],
  });
  const names = surfaces(m).map(([n]) => n);
  assert.ok(names.includes('event subscriptions'));
  assert.ok(names.includes('slash /deploy'));
});

test('the forgotten slash command outranks the healthy events url', () => {
  const m = manifest({
    events: 'https://hooks.acme.example/e',
    commands: [{ command: '/deploy', url: 'https://a1.ngrok.io/cmd' }],
  });
  const rows = audit(m);
  assert.equal(rows[0][0], 'slash /deploy');
  assert.equal(rows[0][2], 'ephemeral-tunnel');
});

test('interactivity and menu urls are read as well', () => {
  const m = manifest({
    interactivity: {
      request_url: 'https://a1.ngrok.io/i',
      message_menu_options_url: 'http://x.example/m',
    },
  });
  const states = Object.fromEntries(audit(m).map(([n, , s]) => [n, s]));
  assert.equal(states.interactivity, 'ephemeral-tunnel');
  assert.equal(states['message menu options'], 'not-https');
});

test('socket mode demotes every finding to dormant', () => {
  const rows = audit(manifest({
    events: 'https://a1.ngrok.io/slack/events', socket: true,
  }));
  assert.equal(rows[0][2], 'ephemeral-tunnel');
  assert.equal(rows[0][4], false);
  assert.match(rows[0][3], /cleanup rather than an outage/);
  assert.equal(verdict(rows, 'no-records')[0], 'dormant');
});

test('a retry reason is translated rather than echoed', () => {
  const [state, detail] = recordVerdict(null, 'connection_failed');
  assert.equal(state, 'reason-recorded');
  assert.match(detail, /closed tunnel/);
  assert.equal(recordVerdict(null, 'ssl_error')[0], 'reason-recorded');
});

test('an unknown retry reason is not waved through', () => {
  const [state, detail] = recordVerdict(null, 'something_new');
  assert.equal(state, 'unknown-reason');
  assert.match(detail, /rather than assuming it is benign/);
});

test('silence is measured in days and none means no records', () => {
  assert.equal(recordVerdict(120)[0], 'silent');
  assert.equal(recordVerdict(0)[0], 'delivering');
  assert.equal(recordVerdict(null)[0], 'no-records');
  assert.equal(recordVerdict('yesterday')[0], 'no-records');
});

test('a dead tunnel plus a silent endpoint closes the case', () => {
  const rows = audit(manifest({ events: 'https://a1.ngrok.io/slack/events' }));
  assert.equal(verdict(rows, 'silent')[0], 'dead-endpoint');
  assert.equal(verdict(rows, 'reason-recorded')[0], 'dead-endpoint');
});

test('a suspect url alone asks for the records', () => {
  const rows = audit(manifest({ events: 'https://a1.ngrok.io/slack/events' }));
  const [state, detail] = verdict(rows, 'no-records');
  assert.equal(state, 'suspect-origin');
  assert.match(detail, /--last-delivery/);
});

test('a clean url and a silent endpoint is somebody elses note', () => {
  const rows = audit(manifest({ events: 'https://hooks.acme.example/slack/events' }));
  const [state, detail] = verdict(rows, 'silent');
  assert.equal(state, 'elsewhere');
  assert.match(detail, /handshake/);
});

test('a clean url and live delivery is clear', () => {
  const rows = audit(manifest({ events: 'https://hooks.acme.example/slack/events' }));
  assert.equal(verdict(rows, 'delivering')[0], 'clear');
});
''',
"faq": [
 ("The URL is verified and has a green tick. Does that not mean it works?",
  "It means the handshake succeeded on the day it was saved. Slack does not revalidate a Request URL on a schedule, so the tick is a record of one exchange rather than a health check. A URL that verified on a development tunnel keeps its tick forever, including for the four months after the tunnel stopped existing."),
 ("Why will this script not just make a request to my endpoint and tell me?",
  "Because your Request URL is a production endpoint and a detector should not add traffic to an incident it was asked to describe. An unsigned request could trip an alert or a rate limiter, and it proves less than you would think: a host that answers a bare GET can still be the wrong deployment, and one that refuses it can be perfectly healthy behind a signature check. The hostname and your own access log are better evidence and cost nothing."),
 ("How do I run development and production without swapping this field?",
  "Two Slack apps. Slack has no notion of environments, no staging slot and no per-branch override, so the only clean separation is a second app with its own manifest carrying the tunnel URL while the production app carries the production hostname. Any workflow that involves editing the production app's URL to debug something will eventually leave it edited."),
 ("Everything says production-shaped and events still are not arriving. Now what?",
  "Then the address is not the problem and the script says so rather than inventing one. Three things sit behind it: the endpoint never passed the handshake at all, which is a separate note about the challenge exchange; Slack disabled your event subscriptions after sustained failures, which is another; or the events you expect were never subscribed or never scoped. The clear verdict is meant to move you along."),
 ("What is ssl_error and why does it appear months after everything was fine?",
  "It is the retry reason Slack records when it cannot validate your certificate, and the usual cause is expiry rather than misconfiguration. The certificate was valid when the URL verified and stopped being valid at renewal time, so delivery fails without a single line of your configuration changing. Put certificate expiry on the same monitor that watches the endpoint."),
],
"related": [
 ("/slack/request-url-unverified/", "the handshake this URL already passed, once"),
 ("/slack/event-subscriptions-auto-disabled/", "where an endpoint that stops answering ends up"),
 ("/slack/config-token-expired/", "the credential that reads the manifest, and its twelve hours"),
],
"citations": [CITE_EVENTS, CITE_MANIFEST, CITE_INTERACTIVITY, CITE_SECURITY],
})

GUIDES.append({
"slug": "rtm-legacy-still-used",
"title": "Still on RTM: the retired transport and the next reinstall",
"description": "rtm.connect needs the classic client scope no modern app can request. Read the grant vocabulary and the replacement configuration, never the socket.",
"h1": "Still on RTM: the retired transport and the next reinstall",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack rtm.connect missing_scope", "slack rtm api deprecated",
             "rtm.connect needed client scope", "migrate slack rtm to socket mode",
             "slack legacy rtm still working"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The bot has been up for four years. It connects with <code>rtm.connect</code>, holds a websocket open, and has never once been the thing that broke. Nobody has touched it, which is the highest compliment this industry pays a service.</p><p>Then somebody adds a scope, or recreates the app after a workspace migration, and <code>rtm.connect</code> answers <code>missing_scope</code> with <code>needed: client</code>. There is no screen on which <code>client</code> can be granted to an app created after 2020. The transport did not break. It was withdrawn years ago, and this app has been living on a grandfather clause it never knew it had.",
"short_answer": """<p>The Real Time Messaging API predates granular permissions and needs the classic <code>client</code> scope. Apps created before the 2020 migration hold coarse scopes like <code>client</code>, <code>bot</code> and <code>read</code> and can still use it. Apps created since hold namespaced scopes like <code>channels:history</code>, cannot request <code>client</code> at all, and get <code>missing_scope</code> the first time they try. Socket Mode is the supported replacement.</p>
<p>So the audit crosses three things a read-only token can establish: the <strong>vocabulary of the grant</strong>, from the <code>X-OAuth-Scopes</code> header; <strong>what the client opens</strong>, which you declare with <code>--calls</code>; and <strong>what is configured to take over</strong>, from <code>settings.socket_mode_enabled</code> and the subscribed events. The interesting state is not "RTM is deprecated" but <code>cliff</code>: code that opens an RTM session against a grant that can never authorise one. <strong>The script never calls <code>rtm.connect</code></strong>, because that method mints a session, and a section that promises read-only scripts does not get to open connections to prove a point.</p>""",
"problem": """<p>Nothing here fails gradually. RTM does not warn, does not deprecate at runtime, does not add a header telling you to move. It works exactly as well on the last day as on the first. The whole of the risk sits behind an event that is not a code change and is usually not even a deploy: somebody adds a scope, or an admin reinstalls the app, or a workspace is migrated into a Grid org and the app is recreated on the other side.</p>
<p>At that moment the grant is reissued under the current model, in the current vocabulary, and the current vocabulary has no <code>client</code> in it. <code>rtm.connect</code> starts answering <code>missing_scope</code>, and the team does what the error asks: they go to the app configuration to add the scope it named. It is not there. It cannot be added. That is the moment the four-year-old service becomes an unplanned migration, usually in the middle of whatever the reinstall was actually for.</p>
<p>The rewrite is also bigger than swapping a client library, and this is the part that gets underestimated. RTM delivered everything the token could see, implicitly, as a stream. Socket Mode and the Events API deliver only what you have subscribed to, event by event. So an app that moves the transport and not the subscriptions connects successfully, reports healthy, and receives nothing, which looks like a broken socket and is actually an empty <code>bot_events</code> list.</p>""",
"why": """<p><strong>Working is not the same as supported, and only one of them is observable.</strong> There is no runtime signal that separates a transport Slack maintains from one it merely has not switched off. That is why this note is an audit rather than an incident: the finding has to be produced from configuration before the reinstall, because after the reinstall it produces itself.</p>
<p><strong>The scope vocabulary dates the app precisely.</strong> A bare word like <code>client</code> or <code>bot</code> in <code>X-OAuth-Scopes</code> is a pre-2020 grant; namespaced scopes are the current model. The two do not mix, and the presence or absence of <code>client</code> tells you whether RTM is available to this token without any need to try it.</p>
<p><strong>The cliff is the finding, not the deprecation.</strong> An old app on an old grant running RTM is stable. An app whose code opens RTM against a granular grant is already broken or one reinstall from it, and those two are different rows in a report. Collapsing them into "you use a deprecated API" wastes the reader's attention on the stable case.</p>
<p><strong>RTM was implicit and its replacements are not.</strong> This is the single most expensive difference and it is invisible in a diff of the connection code. Socket Mode with an empty subscription list connects, stays connected, and delivers nothing, so the migration looks finished and the app is silent. The script reports that state by name rather than calling Socket Mode configured.</p>
<p><strong>A probe here would be a write.</strong> Calling <code>rtm.connect</code> to see what it says opens a session against your workspace. It is the kind of thing that reads as harmless and is exactly the behaviour this section promises not to have, so the answer is derived from the grant instead. The scope header is not weaker evidence than the error string; it is the same fact, read earlier.</p>""",
"steps": [
 {"h": "Read the grant vocabulary from the header",
  "body": """<p>One <code>auth.test</code> and Slack returns <code>X-OAuth-Scopes</code> with the token's complete current grant. <code>grant_era</code> sorts it: a bare <code>client</code>, <code>bot</code> or <code>read</code> is the classic model, anything namespaced is the current one. That single distinction decides whether RTM is available at all.</p>"""},
 {"h": "Declare what your client actually opens",
  "body": """<p>Pass <code>--calls rtm.connect</code>, or <code>--calls apps.connections.open</code>, or both, for the methods your code calls. No API can tell you this and pretending otherwise would be the wrong kind of confidence; it is one grep in your own repository and it is the input the rest of the audit turns on.</p>"""},
 {"h": "Find out what is configured to take over",
  "body": """<p><code>replacement</code> reads <code>settings.socket_mode_enabled</code> and the subscribed events from the manifest. Socket Mode with events is a destination. The Events API with events is a destination. Neither, and there is nothing for RTM to hand over to when the day comes.</p>"""},
 {"h": "Cross the three and let the cliff surface",
  "body": """<p><code>transport_state</code> is the whole report in one function. The state to act on is <code>cliff</code>: code that opens RTM against a granular grant, which cannot work and cannot be made to work by any change to the app configuration. Everything else is planning.</p>"""},
 {"h": "Watch for the socket that carries nothing",
  "body": """<p><code>half-migrated</code> is Socket Mode enabled with an empty <code>bot_events</code> list. The connection opens, the health check is green, and no event ever arrives, because RTM streamed everything implicitly and its replacements deliver only what you subscribed to.</p>"""},
 {"h": "Print the migration, not just the deprecation",
  "body": """<p>Enable Socket Mode, mint an app-level token with <code>connections:write</code>, subscribe to the events the RTM stream was carrying implicitly, then swap the client. The script prints them in that order because reversing the last two is how an app arrives silent.</p>"""},
],
"verify": """<p>After the cut-over, re-run with the new client declared. The grant should read <code>granular</code>, the replacement should name Socket Mode with a non-empty subscription list, and the transport should be <code>clear</code>.</p>
<pre><code class="language-bash">python3 slack_rtm_migration_audit.py --app-id A01ABCDE9 --calls apps.connections.open
# identity   U0APPBOT11 in acme
# grant      granular       every scope is namespaced, so rtm.connect is not available
# client     socket         the code opens a Socket Mode connection
# replace    socket-mode    Socket Mode is on and 4 event(s) are subscribed
# verdict    clear          the app is on socket-mode with a granular grant</code></pre>""",
"code_intro": "Four pure functions and one read. <code>grant_era</code> dates the app from the shape of its scope names, which is the only fact here that does not need you to know anything about your own code. <code>client_intent</code> is the one input the API cannot supply, so it is declared rather than guessed. <code>replacement</code> is where the expensive detail lives, because Socket Mode with no subscriptions is not a destination. <code>transport_state</code> crosses all three, and <code>cliff</code> is the row worth waking somebody for.",
"py_file": "slack_rtm_migration_audit.py",
"py": '''"""Decide whether a Slack app is still riding RTM, and what happens if it is.

Read only, and specifically without opening anything. This never calls
rtm.connect: that method mints a session, and a section whose scripts promise
never to change your workspace does not get to open a connection to prove a
point. The same fact is available earlier, in the X-OAuth-Scopes header, which
says whether this token could authorise an RTM session at all.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_rtm_migration_audit")

API = "https://slack.com/api/"

# The classic vocabulary. A pre-2020 app holds bare words like these; RTM needs
# client, and no app created since the granular migration can request it.
CLASSIC_SCOPES = {"client", "bot", "read", "post", "identify", "admin"}

# Bare words that survived the migration and therefore date nothing.
NEUTRAL_SCOPES = {"commands", "incoming-webhook"}

RTM_METHODS = {"rtm.connect", "rtm.start"}
SOCKET_METHODS = {"apps.connections.open"}

# States that should fail the run. legacy-grant-idle and no-transport are real
# observations and neither is breaking anything today.
FAILING = ("cliff", "retired-transport", "dual-transport", "half-migrated",
           "mixed-grant")


def grant_era(scopes):
    """Which permission model this token was issued under. Pure. -> (state, detail)

    The vocabulary dates the app exactly, with no call to make and nothing to
    open. A bare word is the old model; a colon is the new one.
    """
    have = {str(s).strip() for s in scopes or [] if str(s).strip()}
    if not have:
        return ("unknown",
                "no scopes were read, so the permission model of this token is "
                "unknown and every conclusion below would be a guess")
    classic = sorted(have & CLASSIC_SCOPES)
    granular = sorted(s for s in have if ":" in s)
    if classic and granular:
        return ("mixed",
                "the grant holds classic scopes (%s) and namespaced ones at the "
                "same time. The two vocabularies are not supposed to coexist, so "
                "read this twice before acting on it" % ", ".join(classic))
    if classic:
        return ("rtm-capable",
                "the grant holds %s, which is the pre-2020 vocabulary. RTM is "
                "available to this token and to no token issued today"
                % ", ".join(classic))
    if granular:
        return ("granular",
                "every scope is namespaced, so this is a modern app. rtm.connect "
                "answers missing_scope with needed: client, and there is no screen "
                "on which client can be granted")
    named = ", ".join(sorted(have & NEUTRAL_SCOPES)) or "unrecognised scopes"
    return ("unknown",
            "the grant holds only %s, which survived the migration and says "
            "nothing about which model this app was created under" % named)


def client_intent(calls):
    """What the client code opens, as declared by the caller. Pure.

    No API reports which methods your code calls, and inferring it from workspace
    state would be a guess dressed as a finding. One grep in your own repository
    is the honest input.
    """
    named = {str(c).strip().lower() for c in calls or [] if str(c).strip()}
    rtm = bool(named & RTM_METHODS)
    socket = bool(named & SOCKET_METHODS)
    if rtm and socket:
        return ("both",
                "the code opens an RTM session and a Socket Mode connection")
    if rtm:
        return ("rtm", "the code opens an RTM session")
    if socket:
        return ("socket", "the code opens a Socket Mode connection")
    if named:
        return ("http",
                "none of the methods named opens a persistent connection, so "
                "events reach this app over HTTP if they reach it at all")
    return ("unknown",
            "no client methods were named. Pass --calls rtm.connect or --calls "
            "apps.connections.open for what your code actually opens")


def replacement(socket_enabled, subscribed):
    """What is configured to take over from RTM. Pure. -> (state, detail)

    RTM delivered everything the token could see, implicitly, as a stream. Both
    replacements are subscription based, so an empty event list is not a
    destination: it is a connection that will open and carry nothing.
    """
    if socket_enabled is None and subscribed is None:
        return ("unknown",
                "no manifest was read, so what is configured to receive events is "
                "unknown")
    events = [str(e).strip() for e in subscribed or [] if str(e).strip()]
    if socket_enabled and events:
        return ("socket-mode",
                "Socket Mode is on and %d event(s) are subscribed" % len(events))
    if socket_enabled:
        return ("socket-unsubscribed",
                "Socket Mode is on and no events are subscribed. The socket will "
                "connect and carry nothing, because RTM streamed everything "
                "implicitly and Socket Mode does not")
    if events:
        return ("http-events",
                "%d event(s) are subscribed for delivery over HTTP" % len(events))
    return ("none",
            "neither Socket Mode nor any event subscription is configured, so "
            "there is nothing for RTM to hand over to")


def transport_state(era, intent, repl):
    """Cross the grant, the client and the configuration. Pure. -> (state, detail)

    The state worth acting on is cliff. An old app on an old grant running RTM is
    stable and has been for years; an app whose code opens RTM against a granular
    grant is already broken or one reinstall away, and reporting those two at the
    same volume wastes the only attention this report will get.
    """
    if era == "unknown" or intent == "unknown":
        return ("unknown",
                "the grant or the client is unknown, so no transport conclusion "
                "is available")
    if era == "mixed":
        return ("mixed-grant",
                "classic and granular scopes on one token. Establish which app "
                "this token belongs to before reading anything else here")
    if intent == "rtm" and era == "granular":
        return ("cliff",
                "the code opens an RTM session and the token holds only granular "
                "scopes. rtm.connect answers missing_scope with needed: client, "
                "and no reinstall can grant client to a modern app")
    if intent == "both":
        return ("dual-transport",
                "the code opens RTM and a socket at once. Both carry the same "
                "events, so everything subscribed is handled twice for as long as "
                "the cut-over lasts")
    if repl == "socket-unsubscribed":
        return ("half-migrated",
                "the transport moved and the subscriptions did not. The socket "
                "connects, the health check passes, and no event arrives")
    if intent == "rtm" and repl in ("none", "unknown"):
        return ("retired-transport",
                "the app runs on RTM with nothing configured to take over. It "
                "works today on a grandfather clause and stops on the day the app "
                "is recreated or its scopes change")
    if intent == "rtm":
        return ("migration-ready",
                "the app still opens RTM and %s is already configured. What is "
                "left is the client, not the configuration" % repl)
    if era == "rtm-capable":
        return ("legacy-grant-idle",
                "the token still holds classic scopes and nothing here opens an "
                "RTM session. That is a grant to tidy rather than a transport to "
                "migrate")
    if repl == "none":
        return ("no-transport",
                "nothing opens a connection and nothing is subscribed, so no "
                "event reaches this app by any route")
    return ("clear",
            "the app is on %s with a granular grant, which is where RTM was "
            "going" % repl)


def get(session, method, params, label):
    """One GET, asserting on the body rather than the status line."""
    r = session.get(API + method, params=params or {}, timeout=30)
    body = r.json()
    if body.get("ok") is not True:
        log.warning("%-10s %-14s %s", label, "unavailable", body.get("error"))
        return None, r.headers.get("X-OAuth-Scopes", "")
    return body, r.headers.get("X-OAuth-Scopes", "")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app ID, for the manifest read")
    ap.add_argument("--calls", action="append", default=[],
                    help="a method your client code calls, such as rtm.connect or "
                         "apps.connections.open; repeatable")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s; any read scope works, the header is what matters",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who, header = get(s, "auth.test", {}, "auth.test")
    if not who:
        return 2
    scopes = {p.strip() for p in str(header or "").split(",") if p.strip()}
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    era, era_detail = grant_era(scopes)
    log.info("grant      %-14s %s", era, era_detail)
    intent, intent_detail = client_intent(args.calls)
    log.info("client     %-14s %s", intent, intent_detail)

    socket_enabled, subscribed = None, None
    config_token = os.environ.get(args.config_token_env)
    if config_token and args.app_id:
        c = requests.Session()
        c.headers.update({"Authorization": "Bearer " + config_token})
        body, _ = get(c, "apps.manifest.export", {"app_id": args.app_id}, "manifest")
        if body:
            settings = ((body or {}).get("manifest") or {}).get("settings") or {}
            socket_enabled = bool(settings.get("socket_mode_enabled"))
            subscribed = list(
                (settings.get("event_subscriptions") or {}).get("bot_events") or [])
    repl, repl_detail = replacement(socket_enabled, subscribed)
    log.info("replace    %-14s %s", repl, repl_detail)

    state, detail = transport_state(era, intent, repl)
    if state in FAILING:
        log.warning("verdict    %-14s %s", state, detail)
        log.warning("  repair: enable Socket Mode and mint an app-level token with "
                    "connections:write on the Basic Information page")
        log.warning("  repair: subscribe to the events the RTM stream was carrying "
                    "implicitly, before you swap the client. Reversing those two is "
                    "how an app arrives connected and silent")
        log.warning("  repair: then move the client to SocketModeClient, or to the "
                    "Events API with a public Request URL if you would rather not "
                    "hold a connection open")
        return 1
    log.info("verdict    %-14s %s", state, detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-rtm-migration-audit.mjs",
"js": '''/**
 * Decide whether a Slack app is still riding RTM, and what happens if it is.
 *
 * Read only, and specifically without opening anything. This never calls
 * rtm.connect: that method mints a session, and a section whose scripts promise
 * never to change your workspace does not get to open a connection to prove a
 * point. The same fact is available earlier, in the X-OAuth-Scopes header.
 */

const API = 'https://slack.com/api/';

// The classic vocabulary. A pre-2020 app holds bare words like these; RTM needs
// client, and no app created since the granular migration can request it.
const CLASSIC_SCOPES = new Set(['client', 'bot', 'read', 'post', 'identify',
  'admin']);

// Bare words that survived the migration and therefore date nothing.
const NEUTRAL_SCOPES = new Set(['commands', 'incoming-webhook']);

const RTM_METHODS = new Set(['rtm.connect', 'rtm.start']);
const SOCKET_METHODS = new Set(['apps.connections.open']);

const FAILING = ['cliff', 'retired-transport', 'dual-transport', 'half-migrated',
  'mixed-grant'];

/**
 * Which permission model this token was issued under. Pure.
 * A bare word is the old model; a colon is the new one.
 */
export function grantEra(scopes) {
  const have = new Set([...(scopes ?? [])].map((s) => String(s).trim())
    .filter(Boolean));
  if (!have.size) {
    return ['unknown',
      'no scopes were read, so the permission model of this token is unknown and ' +
      'every conclusion below would be a guess'];
  }
  const classic = [...have].filter((s) => CLASSIC_SCOPES.has(s)).sort();
  const granular = [...have].filter((s) => s.includes(':')).sort();
  if (classic.length && granular.length) {
    return ['mixed',
      `the grant holds classic scopes (${classic.join(', ')}) and namespaced ones ` +
      'at the same time. The two vocabularies are not supposed to coexist, so read ' +
      'this twice before acting on it'];
  }
  if (classic.length) {
    return ['rtm-capable',
      `the grant holds ${classic.join(', ')}, which is the pre-2020 vocabulary. ` +
      'RTM is available to this token and to no token issued today'];
  }
  if (granular.length) {
    return ['granular',
      'every scope is namespaced, so this is a modern app. rtm.connect answers ' +
      'missing_scope with needed: client, and there is no screen on which client ' +
      'can be granted'];
  }
  const neutral = [...have].filter((s) => NEUTRAL_SCOPES.has(s)).sort();
  return ['unknown',
    `the grant holds only ${neutral.join(', ') || 'unrecognised scopes'}, which ` +
    'survived the migration and says nothing about which model this app was ' +
    'created under'];
}

/**
 * What the client code opens, as declared by the caller. Pure.
 * No API reports which methods your code calls, and inferring it from workspace
 * state would be a guess dressed as a finding.
 */
export function clientIntent(calls) {
  const named = new Set((calls ?? []).map((c) => String(c).trim().toLowerCase())
    .filter(Boolean));
  const rtm = [...named].some((m) => RTM_METHODS.has(m));
  const socket = [...named].some((m) => SOCKET_METHODS.has(m));
  if (rtm && socket) {
    return ['both', 'the code opens an RTM session and a Socket Mode connection'];
  }
  if (rtm) return ['rtm', 'the code opens an RTM session'];
  if (socket) return ['socket', 'the code opens a Socket Mode connection'];
  if (named.size) {
    return ['http',
      'none of the methods named opens a persistent connection, so events reach ' +
      'this app over HTTP if they reach it at all'];
  }
  return ['unknown',
    'no client methods were named. Pass --calls rtm.connect or --calls ' +
    'apps.connections.open for what your code actually opens'];
}

/**
 * What is configured to take over from RTM. Pure.
 * RTM delivered everything the token could see, implicitly. Both replacements
 * are subscription based, so an empty event list is not a destination.
 */
export function replacement(socketEnabled, subscribed) {
  if ((socketEnabled === null || socketEnabled === undefined)
      && (subscribed === null || subscribed === undefined)) {
    return ['unknown',
      'no manifest was read, so what is configured to receive events is unknown'];
  }
  const events = (subscribed ?? []).map((e) => String(e).trim()).filter(Boolean);
  if (socketEnabled && events.length) {
    return ['socket-mode',
      `Socket Mode is on and ${events.length} event(s) are subscribed`];
  }
  if (socketEnabled) {
    return ['socket-unsubscribed',
      'Socket Mode is on and no events are subscribed. The socket will connect ' +
      'and carry nothing, because RTM streamed everything implicitly and Socket ' +
      'Mode does not'];
  }
  if (events.length) {
    return ['http-events',
      `${events.length} event(s) are subscribed for delivery over HTTP`];
  }
  return ['none',
    'neither Socket Mode nor any event subscription is configured, so there is ' +
    'nothing for RTM to hand over to'];
}

/**
 * Cross the grant, the client and the configuration. Pure.
 * The state worth acting on is cliff: an old app on an old grant running RTM is
 * stable, and an app whose code opens RTM against a granular grant is not.
 */
export function transportState(era, intent, repl) {
  if (era === 'unknown' || intent === 'unknown') {
    return ['unknown',
      'the grant or the client is unknown, so no transport conclusion is available'];
  }
  if (era === 'mixed') {
    return ['mixed-grant',
      'classic and granular scopes on one token. Establish which app this token ' +
      'belongs to before reading anything else here'];
  }
  if (intent === 'rtm' && era === 'granular') {
    return ['cliff',
      'the code opens an RTM session and the token holds only granular scopes. ' +
      'rtm.connect answers missing_scope with needed: client, and no reinstall can ' +
      'grant client to a modern app'];
  }
  if (intent === 'both') {
    return ['dual-transport',
      'the code opens RTM and a socket at once. Both carry the same events, so ' +
      'everything subscribed is handled twice for as long as the cut-over lasts'];
  }
  if (repl === 'socket-unsubscribed') {
    return ['half-migrated',
      'the transport moved and the subscriptions did not. The socket connects, ' +
      'the health check passes, and no event arrives'];
  }
  if (intent === 'rtm' && (repl === 'none' || repl === 'unknown')) {
    return ['retired-transport',
      'the app runs on RTM with nothing configured to take over. It works today ' +
      'on a grandfather clause and stops on the day the app is recreated or its ' +
      'scopes change'];
  }
  if (intent === 'rtm') {
    return ['migration-ready',
      `the app still opens RTM and ${repl} is already configured. What is left is ` +
      'the client, not the configuration'];
  }
  if (era === 'rtm-capable') {
    return ['legacy-grant-idle',
      'the token still holds classic scopes and nothing here opens an RTM session. ' +
      'That is a grant to tidy rather than a transport to migrate'];
  }
  if (repl === 'none') {
    return ['no-transport',
      'nothing opens a connection and nothing is subscribed, so no event reaches ' +
      'this app by any route'];
  }
  return ['clear',
    `the app is on ${repl} with a granular grant, which is where RTM was going`];
}

async function get(token, method, params, label) {
  const qs = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) {
    console.warn(`${label.padEnd(10)} ${'unavailable'.padEnd(14)} ${body.error}`);
    return [null, res.headers.get('x-oauth-scopes') ?? ''];
  }
  return [body, res.headers.get('x-oauth-scopes') ?? ''];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}; any read scope works, the header is what matters`);
    process.exitCode = 2;
    return;
  }
  const configTokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');

  const [who, header] = await get(token, 'auth.test', {}, 'auth.test');
  if (!who) { process.exitCode = 2; return; }
  const scopes = String(header ?? '').split(',').map((p) => p.trim()).filter(Boolean);
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const [era, eraDetail] = grantEra(scopes);
  console.log(`grant      ${era.padEnd(14)} ${eraDetail}`);
  const [intent, intentDetail] = clientIntent(argAll(args, '--calls'));
  console.log(`client     ${intent.padEnd(14)} ${intentDetail}`);

  let socketEnabled = null;
  let subscribed = null;
  const configToken = process.env[configTokenEnv];
  if (configToken && appId) {
    const [body] = await get(configToken, 'apps.manifest.export', { app_id: appId },
      'manifest');
    if (body) {
      const settings = body?.manifest?.settings ?? {};
      socketEnabled = Boolean(settings.socket_mode_enabled);
      subscribed = settings.event_subscriptions?.bot_events ?? [];
    }
  }
  const [repl, replDetail] = replacement(socketEnabled, subscribed);
  console.log(`replace    ${repl.padEnd(14)} ${replDetail}`);

  const [state, detail] = transportState(era, intent, repl);
  if (FAILING.includes(state)) {
    console.warn(`verdict    ${state.padEnd(14)} ${detail}`);
    console.warn('  repair: enable Socket Mode and mint an app-level token with ' +
      'connections:write on the Basic Information page');
    console.warn('  repair: subscribe to the events the RTM stream was carrying ' +
      'implicitly, before you swap the client. Reversing those two is how an app ' +
      'arrives connected and silent');
    console.warn('  repair: then move the client to SocketModeClient, or to the ' +
      'Events API with a public Request URL if you would rather not hold a ' +
      'connection open');
    process.exitCode = 1;
  } else {
    console.log(`verdict    ${state.padEnd(14)} ${detail}`);
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests defend the two distinctions this note is built on. A classic app quietly running RTM has to come back as stable, and a modern app whose code calls <code>rtm.connect</code> has to come back as <code>cliff</code>, because treating those two the same is what turns a useful audit into a deprecation notice nobody reads. And Socket Mode with an empty subscription list has to be <code>half-migrated</code> rather than migrated, since that is the state where every dashboard is green and nothing arrives.",
"test_py_file": "test_slack_rtm_migration_audit.py",
"test_py": '''from slack_rtm_migration_audit import (client_intent, grant_era, replacement,
                                       transport_state)


def test_a_bare_client_scope_dates_the_app_to_the_classic_model():
    state, detail = grant_era(["client", "bot"])
    assert state == "rtm-capable"
    assert "pre-2020" in detail


def test_namespaced_scopes_are_the_modern_model_and_cannot_reach_rtm():
    state, detail = grant_era(["channels:history", "chat:write"])
    assert state == "granular"
    assert "needed: client" in detail


def test_both_vocabularies_at_once_is_reported_rather_than_resolved():
    state, detail = grant_era(["client", "channels:history"])
    assert state == "mixed"
    assert "read this twice" in detail


def test_scopes_that_survived_the_migration_date_nothing():
    assert grant_era(["commands", "incoming-webhook"])[0] == "unknown"
    assert grant_era([])[0] == "unknown"


def test_the_client_is_declared_and_never_inferred():
    assert client_intent(["rtm.connect"])[0] == "rtm"
    assert client_intent(["rtm.start"])[0] == "rtm"
    assert client_intent(["apps.connections.open"])[0] == "socket"
    assert client_intent(["rtm.connect", "apps.connections.open"])[0] == "both"
    assert client_intent(["chat.postMessage"])[0] == "http"
    assert client_intent([])[0] == "unknown"


def test_socket_mode_with_subscriptions_is_a_destination():
    state, detail = replacement(True, ["app_mention", "message.channels"])
    assert state == "socket-mode"
    assert "2 event(s)" in detail


def test_socket_mode_with_no_subscriptions_is_not_a_destination():
    state, detail = replacement(True, [])
    assert state == "socket-unsubscribed"
    assert "connect and carry nothing" in detail


def test_subscriptions_without_socket_mode_are_the_http_route():
    assert replacement(False, ["app_mention"])[0] == "http-events"


def test_neither_leaves_rtm_with_nowhere_to_go():
    assert replacement(False, [])[0] == "none"
    assert replacement(None, None)[0] == "unknown"


def test_rtm_code_on_a_granular_grant_is_the_cliff():
    state, detail = transport_state("granular", "rtm", "socket-mode")
    assert state == "cliff"
    assert "no reinstall can grant client" in detail


def test_a_classic_app_on_rtm_with_no_replacement_is_a_plan_not_an_outage():
    state, detail = transport_state("rtm-capable", "rtm", "none")
    assert state == "retired-transport"
    assert "grandfather clause" in detail


def test_a_classic_app_on_rtm_with_socket_mode_ready_is_a_client_swap():
    assert transport_state("rtm-capable", "rtm", "socket-mode")[0] == "migration-ready"


def test_two_transports_at_once_deliver_everything_twice():
    state, detail = transport_state("rtm-capable", "both", "socket-mode")
    assert state == "dual-transport"
    assert "handled twice" in detail


def test_a_socket_with_no_subscriptions_beats_the_other_readings():
    assert transport_state("granular", "socket", "socket-unsubscribed")[0] == \\
        "half-migrated"


def test_a_classic_grant_with_no_rtm_client_is_the_scope_note_next_door():
    state, detail = transport_state("rtm-capable", "http", "http-events")
    assert state == "legacy-grant-idle"
    assert "grant to tidy" in detail


def test_nothing_connecting_and_nothing_subscribed_receives_nothing():
    assert transport_state("granular", "http", "none")[0] == "no-transport"


def test_a_migrated_app_is_clear():
    state, detail = transport_state("granular", "socket", "socket-mode")
    assert state == "clear"
    assert "where RTM was going" in detail


def test_an_undeclared_client_produces_no_conclusion():
    assert transport_state("granular", "unknown", "socket-mode")[0] == "unknown"
    assert transport_state("unknown", "rtm", "none")[0] == "unknown"


def test_a_mixed_grant_is_settled_before_anything_else_is_read():
    assert transport_state("mixed", "rtm", "none")[0] == "mixed-grant"
''',
"test_js_file": "slack-rtm-migration-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  clientIntent, grantEra, replacement, transportState,
} from './slack-rtm-migration-audit.mjs';

test('a bare client scope dates the app to the classic model', () => {
  const [state, detail] = grantEra(['client', 'bot']);
  assert.equal(state, 'rtm-capable');
  assert.match(detail, /pre-2020/);
});

test('namespaced scopes are the modern model and cannot reach rtm', () => {
  const [state, detail] = grantEra(['channels:history', 'chat:write']);
  assert.equal(state, 'granular');
  assert.match(detail, /needed: client/);
});

test('both vocabularies at once is reported rather than resolved', () => {
  const [state, detail] = grantEra(['client', 'channels:history']);
  assert.equal(state, 'mixed');
  assert.match(detail, /read this twice/);
});

test('scopes that survived the migration date nothing', () => {
  assert.equal(grantEra(['commands', 'incoming-webhook'])[0], 'unknown');
  assert.equal(grantEra([])[0], 'unknown');
});

test('the client is declared and never inferred', () => {
  assert.equal(clientIntent(['rtm.connect'])[0], 'rtm');
  assert.equal(clientIntent(['rtm.start'])[0], 'rtm');
  assert.equal(clientIntent(['apps.connections.open'])[0], 'socket');
  assert.equal(clientIntent(['rtm.connect', 'apps.connections.open'])[0], 'both');
  assert.equal(clientIntent(['chat.postMessage'])[0], 'http');
  assert.equal(clientIntent([])[0], 'unknown');
});

test('socket mode with subscriptions is a destination', () => {
  const [state, detail] = replacement(true, ['app_mention', 'message.channels']);
  assert.equal(state, 'socket-mode');
  assert.match(detail, /2 event\\(s\\)/);
});

test('socket mode with no subscriptions is not a destination', () => {
  const [state, detail] = replacement(true, []);
  assert.equal(state, 'socket-unsubscribed');
  assert.match(detail, /connect and carry nothing/);
});

test('subscriptions without socket mode are the http route', () => {
  assert.equal(replacement(false, ['app_mention'])[0], 'http-events');
});

test('neither leaves rtm with nowhere to go', () => {
  assert.equal(replacement(false, [])[0], 'none');
  assert.equal(replacement(null, null)[0], 'unknown');
});

test('rtm code on a granular grant is the cliff', () => {
  const [state, detail] = transportState('granular', 'rtm', 'socket-mode');
  assert.equal(state, 'cliff');
  assert.match(detail, /no reinstall can grant client/);
});

test('a classic app on rtm with no replacement is a plan not an outage', () => {
  const [state, detail] = transportState('rtm-capable', 'rtm', 'none');
  assert.equal(state, 'retired-transport');
  assert.match(detail, /grandfather clause/);
});

test('a classic app on rtm with socket mode ready is a client swap', () => {
  assert.equal(transportState('rtm-capable', 'rtm', 'socket-mode')[0],
    'migration-ready');
});

test('two transports at once deliver everything twice', () => {
  const [state, detail] = transportState('rtm-capable', 'both', 'socket-mode');
  assert.equal(state, 'dual-transport');
  assert.match(detail, /handled twice/);
});

test('a socket with no subscriptions beats the other readings', () => {
  assert.equal(transportState('granular', 'socket', 'socket-unsubscribed')[0],
    'half-migrated');
});

test('a classic grant with no rtm client is the scope note next door', () => {
  const [state, detail] = transportState('rtm-capable', 'http', 'http-events');
  assert.equal(state, 'legacy-grant-idle');
  assert.match(detail, /grant to tidy/);
});

test('nothing connecting and nothing subscribed receives nothing', () => {
  assert.equal(transportState('granular', 'http', 'none')[0], 'no-transport');
});

test('a migrated app is clear', () => {
  const [state, detail] = transportState('granular', 'socket', 'socket-mode');
  assert.equal(state, 'clear');
  assert.match(detail, /where RTM was going/);
});

test('an undeclared client produces no conclusion', () => {
  assert.equal(transportState('granular', 'unknown', 'socket-mode')[0], 'unknown');
  assert.equal(transportState('unknown', 'rtm', 'none')[0], 'unknown');
});

test('a mixed grant is settled before anything else is read', () => {
  assert.equal(transportState('mixed', 'rtm', 'none')[0], 'mixed-grant');
});
''',
"faq": [
 ("RTM still works for us. Is this actually urgent?",
  "For a classic app on a classic grant, no, and the script says so by returning retired-transport rather than an error. It works and will keep working until something reissues the grant. What makes it worth scheduling is that the trigger is not a code change: adding a scope, reinstalling, or recreating the app after a workspace migration all reissue it, and at that point the migration happens on somebody else's timetable rather than yours."),
 ("Why can I not just add the client scope the error asks for?",
  "Because client belongs to the pre-2020 permission model and the app configuration screens for a modern app do not offer it. Slack kept RTM working for apps that already held those coarse scopes rather than making it grantable again. If your grant is namespaced, the error naming client is telling you which era the method belongs to, not which checkbox to tick."),
 ("Is Socket Mode just RTM with a new name?",
  "No, and the difference is the part that costs time. RTM delivered everything the token could see as a single implicit stream. Socket Mode delivers only the events you have subscribed to, in the Events API payload shape, over a connection you obtain with an app-level token holding connections:write. The transport is similar; the delivery model, the payloads and the setup are not."),
 ("The socket connects and nothing arrives. What did we miss?",
  "The subscriptions, almost certainly. That is the half-migrated state: Socket Mode is enabled, the client connects, every health check is green, and bot_events is empty, so there is nothing for the socket to carry. RTM never made you list events, so a team migrating the transport has no reason to think a list is missing. Subscribe first, then swap the client."),
 ("Why does this script not just call rtm.connect and read the error?",
  "Because rtm.connect mints a session. It is a small write rather than a large one, but it is still the script changing something on your account to answer a question, and every script in this section promises not to. The scope header carries the same fact earlier: a token with no client scope could not have opened that session, so there is nothing the call would add except a connection nobody asked for."),
],
"related": [
 ("/slack/classic-app-coarse-scopes/", "the scope vocabulary that makes RTM possible at all"),
 ("/slack/app-level-token-missing-connections-write/", "the credential the replacement needs"),
 ("/slack/no-event-subscriptions/", "what RTM delivered implicitly and its replacements do not"),
],
"citations": [CITE_RTM, CITE_SOCKET_MODE, CITE_SCOPES, CITE_MANIFEST],
})
