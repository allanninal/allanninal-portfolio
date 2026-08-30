#!/usr/bin/env python3
"""/slack/ field notes, batch Q - the writing.

Four notes about messages that will not do what you asked, written so that no
two of them are the same note. Two of them look like one problem from the
outside and are not, so they are deliberately separated by what the script
reads.

The first is a message that is not there: chat.update takes a channel and a ts
and both must match exactly, so the interesting reading is conversations.history
around that ts, and the interesting cause is that Slack timestamps are strings
and a JSON parser turns them into floats.

The second is a message that is there and is not yours: the interesting reading
is auth.test beside the authorship fields on the message, and the answer is a
sentence about which identity wrote it rather than about whether it exists.

The third is not about a message at all. It is about a viewer: an ephemeral is
rendered into one person's view of one channel, so if that person cannot see the
channel there is nowhere to draw it, and the send can still come back ok.

The fourth is about a number. post_at is Unix seconds in the future and within
120 days, and every way of getting it wrong is arithmetic.

Read only throughout. Nothing in this batch posts, edits, deletes or schedules
anything, and that is a stronger promise here than elsewhere in the section
because all four notes are about write calls. Listing the scheduled queue is a
read; cancelling anything in it is not, and is printed rather than run.
"""

CITE_CHAT_UPDATE = ("chat.update method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.update")
CITE_CHAT_DELETE = ("chat.delete method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.delete")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_RETRIEVING = ("Retrieving messages - Slack Docs",
                   "https://docs.slack.dev/messaging/retrieving-messages")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_POSTMESSAGE = ("chat.postMessage method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_EPHEMERAL = ("chat.postEphemeral method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/chat.postEphemeral")
CITE_CONV_MEMBERS = ("conversations.members method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.members")
CITE_USERS_CONVERSATIONS = ("users.conversations method reference - Slack Docs",
                            "https://docs.slack.dev/reference/methods/users.conversations")
CITE_USERS_INFO = ("users.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_CONV_OPEN = ("conversations.open method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.open")
CITE_SCHEDULE = ("chat.scheduleMessage method reference - Slack Docs",
                 "https://docs.slack.dev/reference/methods/chat.scheduleMessage")
CITE_SCHEDULED_LIST = ("chat.scheduledMessages.list method reference - Slack Docs",
                       "https://docs.slack.dev/reference/methods/chat.scheduledMessages.list")
CITE_INTERACTIVITY = ("Handling user interaction - Slack Docs",
                      "https://docs.slack.dev/interactivity/handling-user-interaction")
CITE_WEBHOOKS = ("Sending messages using incoming webhooks - Slack Docs",
                 "https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks")
CITE_TOKENS = ("Token types - Slack Docs", "https://docs.slack.dev/authentication/tokens")
CITE_WEB_API = ("Web API - Slack Docs", "https://docs.slack.dev/apis/web-api/")

GUIDES = []

GUIDES.append({
"slug": "chat-update-message-not-found",
"title": "message_not_found: the ts no longer resolves to a message",
"description": "chat.update needs an exact channel and ts pair. Find the stored ts values that no longer resolve, including the ones a JSON parser turned into a float.",
"h1": "message_not_found: the ts no longer resolves to a message",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack message_not_found chat.update",
             "slack chat.update message_not_found",
             "slack ts precision lost float",
             "slack timestamp string not number",
             "slack chat.delete message_not_found"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:history, or no token at all in shape-only mode",
"lead": "The bot posts a status message and then edits it every thirty seconds as the deploy progresses. It has done this for months. This afternoon the first edit comes back <code>{\"ok\": false, \"error\": \"message_not_found\"}</code> and every edit after it does the same, so the message in the channel is frozen at <em>starting</em> forever.</p><p>Nothing about the token changed, the bot is still in the channel, and the message is visibly right there on screen. <code>chat.update</code> identifies a message by the pair <code>(channel, ts)</code>, both have to match exactly, and one of the two no longer does.",
"short_answer": """<p><code>message_not_found</code> from <code>chat.update</code> or <code>chat.delete</code> means the pair you handed Slack does not name a message. There are only four ways that happens, and they want four different repairs: the message was deleted, the <code>channel</code> is not the channel the message is in, the message came from an incoming webhook so there was never a usable <code>ts</code> to store, or the <code>ts</code> itself has been damaged in storage.</p>
<p>That last one is the one worth owning. <strong>A Slack <code>ts</code> is a string</strong>. It looks like a number, so at some point it passes through a JSON parser, a database column, a message queue or a JavaScript <code>Number</code> and comes out as a float. <code>1755000000.000200</code> becomes <code>1755000000.0002</code>, the trailing zeros are gone, and that value will never match anything again. The message is still there. The key is not.</p>
<p>All four are decidable with a read. Ask <code>conversations.history</code> for the single-message window <code>latest=&lt;ts&gt;&amp;oldest=&lt;ts&gt;&amp;inclusive=true</code>: one message back means the pair is fine, none back means it is not. Then widen the window by a second and look at the neighbours, because the neighbour whose <code>ts</code> re-pads to yours is the proof that this was a float and not a deletion.</p>""",
"problem": """<p>What makes this expensive is that all four causes produce the same five words, and the first thing everyone does is the wrong thing: they open Slack, see the message sitting in the channel, and conclude that Slack is lying. So the investigation starts from the assumption that the API is broken, which is the one hypothesis that is never true.</p>
<p>The float story is worth walking through slowly, because it is the one that survives code review. The bot posts, gets back <code>{"ok": true, "ts": "1755000000.000200"}</code>, and stores it. If the storage layer is a JSON column, a Redis value round-tripped through <code>JSON.parse</code>, a Kafka payload, or an ORM field typed as numeric, the string is now a double. Doubles have no memory of trailing zeros. It comes back as <code>1755000000.0002</code>, which formats as <code>"1755000000.0002"</code>, which is not the key of any message in any workspace. Everything about the code looks right. The value looks right. It is off by four characters nobody can see.</p>
<p>The wrong-channel case is quieter and more embarrassing. A <code>ts</code> is only unique within a channel, so a <code>ts</code> captured in <code>#deploys</code> and used against <code>#deploys-staging</code> resolves to nothing, and there is no error that says so. Apps that thread replies across channels, or that store a <code>ts</code> without the channel beside it and reconstruct the channel from configuration later, hit this the first time somebody renames or splits a channel.</p>
<p>The webhook case is a design dead end rather than a bug. An incoming webhook returns the literal body <code>ok</code> and no JSON, so there is no <code>ts</code> at all. Code that posts through a webhook and later wants to edit is not one field away from working; it is on the wrong API. There is nothing to store and nothing to update.</p>
<p>And the ordinary case, someone deleted the message, is real and is usually the least likely of the four. It deserves a fallback in the send path rather than an investigation, which is why the script separates it from the other three instead of grouping everything under <em>gone</em>.</p>""",
"why": """<p><strong>The pair is the identity, so half of it going wrong is invisible.</strong> Slack never tells you which half. A wrong channel and a wrong ts produce byte-identical errors, and the only way to tell them apart is to read the channel and see what is actually in it.</p>
<p><strong>A ts must be a string at every layer, not just in your code.</strong> The variable in the function that calls <code>chat.update</code> is almost always fine. The damage happens in the layer nobody thinks of as a layer: the JSON column, the queue payload, the cache, the test fixture. The script checks the shape of stored values because that is where the mistake lives.</p>
<p><strong>The re-padded neighbour is the proof.</strong> Reporting <em>this ts does not resolve</em> is not enough to change anyone's mind. Reporting <em>this ts does not resolve, and the message at <code>1755000000.000200</code> two rows away is the one you meant</em> ends the argument in one line, which is why the script widens the window after a miss instead of stopping at the first read.</p>
<p><strong>Re-padding is a repair for exactly one failure mode and the script refuses to over-claim it.</strong> Adding trailing zeros back is safe when trailing zeros are what was lost. If the fraction is longer than six digits, or the seconds part is the wrong length, something else happened, and the script says it cannot decide rather than inventing a value that would silently edit the wrong message.</p>
<p><strong>Deleted is a runtime condition, not an incident.</strong> People delete messages. An app that edits a long-lived message needs a fallback that posts a fresh one and re-captures the <code>ts</code>, and the script separates <em>deleted</em> from the three genuine bugs so that this one row does not get fixed by adding a retry to all four.</p>
<p><strong>The authorship question is a different note.</strong> If the message resolves and Slack still refuses the edit, the error is <code>cant_update_message</code>, not <code>message_not_found</code>, and it is about which identity wrote it. This script deliberately stops at existence.</p>""",
"steps": [
 {"h": "Check the shape of every stored ts before you call anything",
  "body": """<p>Run with <code>--pairs state.json --shape-only</code> and no token. <code>ts_fault</code> reads each stored value and reports <code>not-a-string</code> for a JSON number, <code>unpadded</code> for a fraction shorter than six digits, and <code>no-fraction</code> for an integer. Most of the time this ends the investigation before a single API call is made.</p>"""},
 {"h": "Ask for the one-message window",
  "body": """<p><code>window_params</code> builds the <code>conversations.history</code> query that asks about exactly one message: <code>latest</code> and <code>oldest</code> both set to the <code>ts</code>, <code>inclusive=true</code>, <code>limit=1</code>. One message back with a matching <code>ts</code> means <code>chat.update</code> would have worked and your problem is elsewhere.</p>"""},
 {"h": "Widen the window when the exact read comes back empty",
  "body": """<p>The second read asks for the second either side. <code>resolution</code> then sorts the answer: an exact hit is <code>found</code>, a neighbour whose <code>ts</code> re-pads to yours is <code>precision-loss</code> and names the real value, an empty window is <code>absent</code>, and a window full of other people's messages is <code>neighbours-only</code>, which is what a <code>ts</code> from a different channel looks like.</p>"""},
 {"h": "Read absent and neighbours-only as different findings",
  "body": """<p><code>absent</code> means nothing at all exists around that moment in this channel, which is consistent with a deletion. <code>neighbours-only</code> means the channel was busy at that instant and none of it was yours, which is consistent with the <code>ts</code> having been captured somewhere else. Collapsing the two into <em>gone</em> loses the only distinction that changes what you do.</p>"""},
 {"h": "Take the repair the script prints rather than the one it implies",
  "body": """<p>For <code>precision-loss</code> the printed repair is a storage change, not a data fix: make the column text, stop parsing the value, and re-capture. Patching the one broken row leaves the parser that broke it in place, and the next message posted with a trailing zero breaks the same way.</p>"""},
 {"h": "Check whether the message could ever have had a ts",
  "body": """<p>If the code path that posted it was an incoming webhook, stop here. A webhook answers with the three characters <code>ok</code> and no timestamp, so there is no valid pair to store and no update path to fix. Moving that path to <code>chat.postMessage</code> is the change, and no amount of storage hygiene substitutes for it.</p>"""},
],
"verify": """<p>Run it against the state your app stores. The finding you want is a named <code>ts</code> and a named cause, not a count.</p>
<pre><code class="language-bash">python3 slack_update_message_not_found.py --pairs deploy-state.json
# pairs      4 pair(s) read from deploy-state.json
# shape      unpadded       C024BE91L ts=1755000000.0002  the fraction has 4 digits and
#                           Slack always sends 6; trailing zeros are what a float drops
# resolve    precision-loss C024BE91L ts=1755000000.0002  the message is at
#                           1755000000.000200, two rows from where you looked
# shape      no-fraction    C07J4K2QT ts=1755000398  an integer, so the fraction is gone
# resolve    absent         C07J4K2QT ts=1755000398  nothing exists around that second
# resolve    found          C024BE91L ts=1755000411.418500
# verdict    3 of 4 pair(s) would fail chat.update
#   repair: store ts as text at every layer, not only in the calling function
#   repair: store the channel id beside it; a ts is unique per channel, not per workspace</code></pre>""",
"code_intro": "Four pure functions and two reads. <code>ts_fault</code> is the whole shape argument in one table and needs no network. <code>repad</code> is the repair, and it is written to refuse rather than to guess, because a re-padded value that is wrong would edit somebody else's message. <code>same_ts</code> exists so the comparison is done in one place rather than three. <code>resolution</code> turns a history window into the four causes, and the two that look alike are the two it keeps apart.",
"py_file": "slack_update_message_not_found.py",
"py": '''"""Find the (channel, ts) pairs your app can no longer update.

Read only. Nothing here posts, edits, deletes or schedules a message: the
question is whether the message chat.update would aim at still resolves, and
conversations.history answers that with a read. It also checks the shape of the
ts values you have stored, because the most common reason a ts stops matching
is not that the message went away, it is that a JSON parser somewhere turned
the string into a float and the trailing zeros went with it.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_update_message_not_found")

API = "https://slack.com/api/"

# Slack sends ten digits, a dot, and exactly six digits. Anything else has been
# through something that reformatted it.
TS_SHAPE = re.compile(r"^(\\d{10,})\\.(\\d+)$")
FRACTION_DIGITS = 6


def ts_fault(value):
    """Is this stored ts still the exact string Slack handed you? Pure.

    Returns (verdict, detail). usable is the only verdict that means the value
    can be sent as it stands. Everything else is a value that will produce
    message_not_found no matter what the channel is or whether the message is
    still there.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return ("missing", "no ts stored. An incoming webhook answers with the literal "
                           "text ok and no timestamp, so a webhook post has no ts to "
                           "keep and no update path at all")
    if isinstance(value, bool):
        return ("not-a-string", "a boolean, which is what a truthiness check stored "
                                "instead of the value")
    if isinstance(value, float):
        return ("not-a-string", "a float. Slack sends a ts as a string, and a double "
                                "cannot hold %r without dropping trailing zeros; "
                                "the value in your store is already damaged"
                % value)
    if isinstance(value, int):
        return ("not-a-string", "an integer, so the fractional part is gone entirely. "
                                "A ts is a string and the six digits after the dot are "
                                "part of the key")
    text = str(value).strip()
    if re.search(r"\\d[eE][+-]?\\d", text):
        return ("scientific", "%s is in exponent notation, which is what a float "
                              "formatter does to a value it decided was large. Nothing "
                              "will match this" % text)
    m = TS_SHAPE.match(text)
    if not m:
        return ("not-a-timestamp", "%s is not shaped like a Slack ts. Slack sends ten "
                                   "digits, a dot and six digits" % text[:40])
    fraction = m.group(2)
    if len(fraction) < FRACTION_DIGITS:
        return ("unpadded", "the fraction has %d digit(s) and Slack always sends %d. "
                            "Trailing zeros are exactly what a float round trip drops, "
                            "so this value was a number at some point"
                % (len(fraction), FRACTION_DIGITS))
    if len(fraction) > FRACTION_DIGITS:
        return ("over-precise", "the fraction has %d digits and Slack sends %d. "
                                "Something appended precision that was never there"
                % (len(fraction), FRACTION_DIGITS))
    return ("usable", "%s is the shape Slack sends" % text)


def repad(value):
    """Normalise a ts back to the string form, or return "" rather than guess. Pure.

    Re-padding is a repair for exactly one failure: a float dropped trailing
    zeros. That is recoverable because zeros carry no information. A fraction
    that is longer than six digits and does not end in zeros was damaged some
    other way, and inventing a value there would aim chat.update at a message
    that is not the one you meant, so this refuses.
    """
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, float):
        text = "%.6f" % value
    elif isinstance(value, int):
        text = "%d.%s" % (value, "0" * FRACTION_DIGITS)
    else:
        text = str(value).strip()
    m = TS_SHAPE.match(text)
    if not m:
        return ""
    seconds, fraction = m.group(1), m.group(2)
    if len(fraction) < FRACTION_DIGITS:
        return "%s.%s" % (seconds, fraction.ljust(FRACTION_DIGITS, "0"))
    if len(fraction) > FRACTION_DIGITS:
        head, tail = fraction[:FRACTION_DIGITS], fraction[FRACTION_DIGITS:]
        return "%s.%s" % (seconds, head) if set(tail) == {"0"} else ""
    return "%s.%s" % (seconds, fraction)


def same_ts(a, b):
    """Do these two values name the same message? Pure.

    Kept in one place because the comparison is the whole bug: a == b on the
    raw values is what every caller writes and what silently answers no.
    """
    left, right = repad(a), repad(b)
    return bool(left) and left == right


def window_params(channel, ts, spread=0.0, limit=1):
    """The conversations.history query that asks about one message. Pure.

    With spread=0 this is the exact probe: latest and oldest both the ts, and
    inclusive, so a single message comes back or nothing does. With a spread it
    widens to the neighbours, which is the read that tells a deletion apart
    from a ts that lost its trailing zeros.
    """
    anchor = repad(ts) or str(ts)
    if not spread:
        return {"channel": str(channel), "latest": anchor, "oldest": anchor,
                "inclusive": "true", "limit": "1"}
    try:
        centre = float(anchor)
    except (TypeError, ValueError):
        centre = 0.0
    return {"channel": str(channel),
            "latest": "%.6f" % (centre + spread),
            "oldest": "%.6f" % (max(0.0, centre - spread)),
            "inclusive": "true", "limit": str(limit)}


def resolution(ts, window):
    """What did the history window say about this ts? Pure.

    Returns (verdict, detail, matched). The two verdicts worth separating are
    absent and neighbours-only: an empty window is consistent with the message
    having been deleted, while a window full of other messages means the
    channel was busy at that instant and none of it was yours, which is what a
    ts captured in a different channel looks like from here.
    """
    stored = str(ts)
    rows = [str((m or {}).get("ts") or "") for m in window or []]
    if stored in rows:
        return ("found", "%s resolves; chat.update would have worked on this pair"
                % stored, stored)
    for candidate in rows:
        if same_ts(stored, candidate):
            return ("precision-loss",
                    "the message is at %s and you stored %s. Those are the same six "
                    "digits with the trailing zeros dropped, which is a float round "
                    "trip and not a deletion" % (candidate, stored), candidate)
    if not rows:
        return ("absent", "nothing at all exists around that second in this channel. "
                          "That is consistent with the message having been deleted",
                "")
    return ("neighbours-only",
            "%d other message(s) sit around that second and none of them is yours. A ts "
            "is unique within one channel, so a ts captured somewhere else looks exactly "
            "like this" % len(rows), "")


def load_pairs(path):
    """Read the (channel, ts) pairs the app stores. Deliberately forgiving."""
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, dict):
        raw = raw.get("pairs") or raw.get("messages") or []
    out = []
    for row in raw or []:
        if isinstance(row, dict):
            out.append((row.get("channel") or row.get("channel_id") or "",
                        row.get("ts") if "ts" in row else row.get("message_ts")))
        elif isinstance(row, (list, tuple)) and len(row) == 2:
            out.append((row[0], row[1]))
    return out


def report_shape(channel, ts, verdict, detail):
    bad = verdict != "usable"
    (log.warning if bad else log.info)("shape      %-14s %s ts=%s  %s", verdict,
                                       channel or "?", ts, detail)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pairs", default="",
                    help="a JSON file of {channel, ts} records your app stores")
    ap.add_argument("--channel", default="", help="one channel, used with --ts")
    ap.add_argument("--ts", action="append", default=[],
                    help="a stored ts to check in --channel; repeatable")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--shape-only", action="store_true",
                    help="check the stored values and make no API call at all")
    ap.add_argument("--spread", type=float, default=1.0,
                    help="seconds either side to search after an exact miss")
    ap.add_argument("--limit", type=int, default=20,
                    help="neighbours to read in the widened window")
    args = ap.parse_args()

    pairs = load_pairs(args.pairs) if args.pairs else [
        (args.channel, t) for t in args.ts]
    if not pairs:
        log.error("pass --pairs FILE, or --channel with one or more --ts")
        return 2
    if args.pairs:
        log.info("pairs      %d pair(s) read from %s", len(pairs), args.pairs)

    broken = 0
    unusable = set()
    for channel, ts in pairs:
        verdict, detail = ts_fault(ts)
        if report_shape(channel, ts, verdict, detail):
            broken += 1
            if verdict in ("missing", "not-a-timestamp", "scientific"):
                unusable.add((str(channel), str(ts)))

    if args.shape_only:
        if broken:
            log.warning("  repair: store ts as text at every layer, not only in the "
                        "function that calls chat.update")
            return 1
        log.info("verdict    clean          every stored ts is the shape Slack sends")
        return 0

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s, or pass --shape-only to check the stored values with no token",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    failures = 0
    for channel, ts in pairs:
        if not channel or (str(channel), str(ts)) in unusable:
            continue
        exact = s.get(API + "conversations.history", timeout=30,
                      params=window_params(channel, ts)).json()
        if exact.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, exact.get("error"))
            continue
        window = exact.get("messages") or []
        verdict, detail, _ = resolution(ts, window)
        if verdict != "found":
            wide = s.get(API + "conversations.history", timeout=30,
                         params=window_params(channel, ts, args.spread,
                                              args.limit)).json()
            if wide.get("ok") is True:
                verdict, detail, _ = resolution(ts, wide.get("messages") or [])
        if verdict == "found":
            log.info("resolve    %-14s %s ts=%s", verdict, channel, ts)
            continue
        failures += 1
        log.warning("resolve    %-14s %s ts=%s  %s", verdict, channel, ts, detail)

    if failures or broken:
        log.warning("verdict    %d pair(s) would fail chat.update", failures or broken)
        log.warning("  repair: store ts as text at every layer, not only in the "
                    "function that calls chat.update")
        log.warning("  repair: store the channel id beside it; a ts is unique per "
                    "channel, not per workspace")
        log.warning("  repair: tolerate a genuine deletion by posting a fresh message "
                    "and re-capturing the ts it returns")
        return 1
    log.info("verdict    clean          every pair still resolves to a message")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-update-message-not-found.mjs",
"js": '''/**
 * Find the (channel, ts) pairs your app can no longer update.
 *
 * Read only. Nothing here posts, edits, deletes or schedules a message: the
 * question is whether the message chat.update would aim at still resolves, and
 * conversations.history answers that with a read. It also checks the shape of
 * the stored ts values, which matters more in this runtime than in any other:
 * JSON.parse turns "1755000000.000200" into the number 1755000000.0002 and
 * there is no warning anywhere.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Slack sends ten digits, a dot, and exactly six digits. Anything else has
// been through something that reformatted it.
const TS_SHAPE = /^(\\d{10,})\\.(\\d+)$/;
const FRACTION_DIGITS = 6;

/**
 * Is this stored ts still the exact string Slack handed you? Pure.
 * Returns [verdict, detail]; usable is the only one that can be sent as it is.
 */
export function tsFault(value) {
  if (value === null || value === undefined
      || (typeof value === 'string' && !value.trim())) {
    return ['missing', 'no ts stored. An incoming webhook answers with the literal '
      + 'text ok and no timestamp, so a webhook post has no ts to keep and no '
      + 'update path at all'];
  }
  if (typeof value === 'boolean') {
    return ['not-a-string', 'a boolean, which is what a truthiness check stored '
      + 'instead of the value'];
  }
  if (typeof value === 'number') {
    return ['not-a-string', `a JSON number. JSON.parse reads "1755000000.000200" as `
      + `${value} and the trailing zeros are gone; the value in your store is `
      + 'already damaged'];
  }
  const text = String(value).trim();
  if (/\\d[eE][+-]?\\d/.test(text)) {
    return ['scientific', `${text} is in exponent notation, which is what a number `
      + 'formatter does to a value it decided was large. Nothing will match this'];
  }
  const m = TS_SHAPE.exec(text);
  if (!m) {
    return ['not-a-timestamp', `${text.slice(0, 40)} is not shaped like a Slack ts. `
      + 'Slack sends ten digits, a dot and six digits'];
  }
  const fraction = m[2];
  if (fraction.length < FRACTION_DIGITS) {
    return ['unpadded', `the fraction has ${fraction.length} digit(s) and Slack always `
      + `sends ${FRACTION_DIGITS}. Trailing zeros are exactly what a float round trip `
      + 'drops, so this value was a number at some point'];
  }
  if (fraction.length > FRACTION_DIGITS) {
    return ['over-precise', `the fraction has ${fraction.length} digits and Slack sends `
      + `${FRACTION_DIGITS}. Something appended precision that was never there`];
  }
  return ['usable', `${text} is the shape Slack sends`];
}

/**
 * Normalise a ts back to the string form, or return '' rather than guess. Pure.
 *
 * Re-padding repairs exactly one failure: a float dropped trailing zeros, and
 * zeros carry no information. Anything else would aim chat.update at a message
 * that is not the one you meant, so this refuses instead.
 */
export function repad(value) {
  if (value === null || value === undefined || typeof value === 'boolean') return '';
  let text;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return '';
    text = value.toFixed(FRACTION_DIGITS);
  } else {
    text = String(value).trim();
  }
  const m = TS_SHAPE.exec(text);
  if (!m) return '';
  const [, seconds, fraction] = m;
  if (fraction.length < FRACTION_DIGITS) {
    return `${seconds}.${fraction.padEnd(FRACTION_DIGITS, '0')}`;
  }
  if (fraction.length > FRACTION_DIGITS) {
    const tail = fraction.slice(FRACTION_DIGITS);
    return /^0+$/.test(tail) ? `${seconds}.${fraction.slice(0, FRACTION_DIGITS)}` : '';
  }
  return `${seconds}.${fraction}`;
}

/** Do these two values name the same message? Pure. */
export function sameTs(a, b) {
  const left = repad(a);
  const right = repad(b);
  return Boolean(left) && left === right;
}

/**
 * The conversations.history query that asks about one message. Pure.
 * With spread 0 it is the exact probe; with a spread it reaches the neighbours.
 */
export function windowParams(channel, ts, spread = 0, limit = 1) {
  const anchor = repad(ts) || String(ts);
  if (!spread) {
    return { channel: String(channel), latest: anchor, oldest: anchor,
      inclusive: 'true', limit: '1' };
  }
  const centre = Number.isFinite(Number(anchor)) ? Number(anchor) : 0;
  return {
    channel: String(channel),
    latest: (centre + spread).toFixed(6),
    oldest: Math.max(0, centre - spread).toFixed(6),
    inclusive: 'true',
    limit: String(limit),
  };
}

/**
 * What did the history window say about this ts? Pure.
 * Returns [verdict, detail, matched].
 */
export function resolution(ts, window) {
  const stored = String(ts);
  const rows = (window ?? []).map((m) => String((m ?? {}).ts ?? ''));
  if (rows.includes(stored)) {
    return ['found', `${stored} resolves; chat.update would have worked on this pair`,
      stored];
  }
  for (const candidate of rows) {
    if (sameTs(stored, candidate)) {
      return ['precision-loss', `the message is at ${candidate} and you stored `
        + `${stored}. Those are the same six digits with the trailing zeros dropped, `
        + 'which is a float round trip and not a deletion', candidate];
    }
  }
  if (!rows.length) {
    return ['absent', 'nothing at all exists around that second in this channel. That '
      + 'is consistent with the message having been deleted', ''];
  }
  return ['neighbours-only', `${rows.length} other message(s) sit around that second `
    + 'and none of them is yours. A ts is unique within one channel, so a ts captured '
    + 'somewhere else looks exactly like this', ''];
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

function loadPairs(raw) {
  let rows = raw;
  if (rows && !Array.isArray(rows) && typeof rows === 'object') {
    rows = rows.pairs ?? rows.messages ?? [];
  }
  const out = [];
  for (const row of rows ?? []) {
    if (Array.isArray(row) && row.length === 2) out.push([row[0], row[1]]);
    else if (row && typeof row === 'object') {
      out.push([row.channel ?? row.channel_id ?? '',
        'ts' in row ? row.ts : row.message_ts]);
    }
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const pairsFile = arg(args, '--pairs', '');
  const channel = arg(args, '--channel', '');
  const shapeOnly = args.includes('--shape-only');
  const spread = Number(arg(args, '--spread', '1'));
  const limit = arg(args, '--limit', '20');

  const pairs = pairsFile
    ? loadPairs(JSON.parse(await readFile(pairsFile, 'utf8')))
    : argAll(args, '--ts').map((t) => [channel, t]);
  if (!pairs.length) {
    console.error('pass --pairs FILE, or --channel with one or more --ts');
    process.exitCode = 2;
    return;
  }
  if (pairsFile) console.log(`pairs      ${pairs.length} pair(s) read from ${pairsFile}`);

  let broken = 0;
  const unusable = new Set();
  for (const [ch, ts] of pairs) {
    const [verdict, detail] = tsFault(ts);
    const line = `shape      ${verdict.padEnd(14)} ${ch || '?'} ts=${ts}  ${detail}`;
    if (verdict === 'usable') console.log(line);
    else {
      console.warn(line);
      broken += 1;
      if (['missing', 'not-a-timestamp', 'scientific'].includes(verdict)) {
        unusable.add(`${ch}\\u0000${ts}`);
      }
    }
  }

  if (shapeOnly) {
    if (broken) {
      console.warn('  repair: store ts as text at every layer, not only in the function '
        + 'that calls chat.update');
      process.exitCode = 1;
    } else {
      console.log('verdict    clean          every stored ts is the shape Slack sends');
    }
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}, or pass --shape-only to check the stored values `
      + 'with no token');
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const read = async (params) => {
    const qs = new URLSearchParams(params).toString();
    return (await fetch(`${API}conversations.history?${qs}`, { headers })).json();
  };

  let failures = 0;
  for (const [ch, ts] of pairs) {
    if (!ch || unusable.has(`${ch}\\u0000${ts}`)) continue;
    const exact = await read(windowParams(ch, ts));
    if (exact.ok !== true) {
      console.warn(`history    unavailable    ${ch}: ${exact.error}`);
      continue;
    }
    let [verdict, detail] = resolution(ts, exact.messages ?? []);
    if (verdict !== 'found') {
      const wide = await read(windowParams(ch, ts, spread, limit));
      if (wide.ok === true) [verdict, detail] = resolution(ts, wide.messages ?? []);
    }
    if (verdict === 'found') {
      console.log(`resolve    ${verdict.padEnd(14)} ${ch} ts=${ts}`);
      continue;
    }
    failures += 1;
    console.warn(`resolve    ${verdict.padEnd(14)} ${ch} ts=${ts}  ${detail}`);
  }

  if (failures || broken) {
    console.warn(`verdict    ${failures || broken} pair(s) would fail chat.update`);
    console.warn('  repair: store ts as text at every layer, not only in the function '
      + 'that calls chat.update');
    console.warn('  repair: store the channel id beside it; a ts is unique per channel, '
      + 'not per workspace');
    console.warn('  repair: tolerate a genuine deletion by posting a fresh message and '
      + 're-capturing the ts it returns');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          every pair still resolves to a message');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions that earn their place are about refusing to guess. <code>repad</code> must recover a value that only lost zeros and must return nothing at all when the damage could have been something else, because a confident wrong answer here edits a stranger's message. <code>resolution</code> must call an empty window <code>absent</code> and a busy one <code>neighbours-only</code>, since those two are the deletion and the wrong-channel case and they are the only pair in this script that a reader could reasonably conflate. And the float tests use the literal values a real round trip produces rather than made-up ones.",
"test_py_file": "test_slack_update_message_not_found.py",
"test_py": '''from slack_update_message_not_found import (repad, resolution, same_ts, ts_fault,
                                            window_params)


def msg(ts):
    return {"ts": ts, "text": "x"}


def test_the_shape_slack_sends_is_the_only_usable_verdict():
    verdict, detail = ts_fault("1755000000.000200")
    assert verdict == "usable"
    assert "1755000000.000200" in detail


def test_a_float_is_named_as_damaged_rather_than_as_a_type_complaint():
    verdict, detail = ts_fault(1755000000.0002)
    assert verdict == "not-a-string"
    assert "trailing zeros" in detail


def test_an_integer_ts_has_lost_the_whole_fraction():
    verdict, detail = ts_fault(1755000398)
    assert verdict == "not-a-string"
    assert "fractional part is gone" in detail


def test_a_string_that_lost_its_trailing_zeros_is_unpadded():
    verdict, detail = ts_fault("1755000000.0002")
    assert verdict == "unpadded"
    assert "4 digit(s)" in detail


def test_a_fraction_longer_than_six_is_over_precise():
    assert ts_fault("1755000000.00020012")[0] == "over-precise"


def test_an_integer_string_with_no_dot_is_not_a_timestamp():
    assert ts_fault("1755000398")[0] == "not-a-timestamp"
    assert ts_fault("hello")[0] == "not-a-timestamp"


def test_exponent_notation_is_its_own_verdict():
    assert ts_fault("1.7550000000002e9")[0] == "scientific"


def test_a_missing_ts_names_the_webhook_dead_end():
    for value in (None, "", "   "):
        verdict, detail = ts_fault(value)
        assert verdict == "missing"
        assert "webhook" in detail


def test_a_boolean_is_not_quietly_stringified():
    assert ts_fault(True)[0] == "not-a-string"


def test_repad_restores_only_the_zeros_a_float_drops():
    assert repad("1755000000.0002") == "1755000000.000200"
    assert repad(1755000000.0002) == "1755000000.000200"
    assert repad(1755000398) == "1755000398.000000"
    assert repad("1755000000.000200") == "1755000000.000200"


def test_repad_refuses_when_the_damage_could_have_been_anything_else():
    assert repad("1755000000.00020012") == ""
    assert repad("not a ts") == ""
    assert repad(None) == ""
    assert repad(True) == ""


def test_repad_trims_a_tail_that_is_only_zeros():
    assert repad("1755000000.0002000") == "1755000000.000200"


def test_same_ts_sees_through_the_round_trip_that_equality_misses():
    assert "1755000000.0002" != "1755000000.000200"
    assert same_ts("1755000000.0002", "1755000000.000200") is True
    assert same_ts(1755000000.0002, "1755000000.000200") is True
    assert same_ts("1755000000.000200", "1755000000.000201") is False
    assert same_ts("", "1755000000.000200") is False


def test_the_exact_probe_asks_for_one_message_at_that_instant():
    params = window_params("C1", "1755000000.0002")
    assert params["latest"] == params["oldest"] == "1755000000.000200"
    assert params["inclusive"] == "true"
    assert params["limit"] == "1"


def test_the_widened_probe_reaches_the_neighbours():
    params = window_params("C1", "1755000000.000200", spread=1.0, limit=20)
    assert params["oldest"] == "1754999999.000200"
    assert params["latest"] == "1755000001.000200"
    assert params["limit"] == "20"


def test_an_exact_hit_is_found():
    verdict, detail, matched = resolution("1755000000.000200",
                                          [msg("1755000000.000200")])
    assert verdict == "found"
    assert matched == "1755000000.000200"


def test_a_neighbour_that_repads_to_yours_is_the_proof_it_was_a_float():
    verdict, detail, matched = resolution(
        "1755000000.0002",
        [msg("1755000000.111111"), msg("1755000000.000200")])
    assert verdict == "precision-loss"
    assert matched == "1755000000.000200"
    assert "not a deletion" in detail


def test_an_empty_window_is_absent_and_reads_as_a_deletion():
    verdict, detail, _ = resolution("1755000000.000200", [])
    assert verdict == "absent"
    assert "deleted" in detail


def test_a_busy_window_with_nothing_of_yours_is_the_wrong_channel_shape():
    verdict, detail, _ = resolution("1755000000.000200",
                                    [msg("1755000000.111111"), msg("1755000000.222222")])
    assert verdict == "neighbours-only"
    assert "unique within one channel" in detail


def test_absent_and_neighbours_only_are_never_collapsed():
    assert resolution("1755000000.000200", [])[0] \\
        != resolution("1755000000.000200", [msg("1755000000.999999")])[0]
''',
"test_js_file": "slack-update-message-not-found.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  repad, resolution, sameTs, tsFault, windowParams,
} from './slack-update-message-not-found.mjs';

const msg = (ts) => ({ ts, text: 'x' });

test('the shape Slack sends is the only usable verdict', () => {
  const [verdict, detail] = tsFault('1755000000.000200');
  assert.equal(verdict, 'usable');
  assert.match(detail, /1755000000\\.000200/);
});

test('JSON.parse really does destroy the value this note is about', () => {
  assert.equal(JSON.parse('{"ts": 1755000000.000200}').ts, 1755000000.0002);
  assert.notEqual(String(JSON.parse('{"ts": 1755000000.000200}').ts),
    '1755000000.000200');
});

test('a JSON number is named as damaged rather than as a type complaint', () => {
  const [verdict, detail] = tsFault(1755000000.0002);
  assert.equal(verdict, 'not-a-string');
  assert.match(detail, /trailing zeros are gone/);
});

test('a string that lost its trailing zeros is unpadded', () => {
  const [verdict, detail] = tsFault('1755000000.0002');
  assert.equal(verdict, 'unpadded');
  assert.match(detail, /4 digit\\(s\\)/);
});

test('a fraction longer than six is over precise', () => {
  assert.equal(tsFault('1755000000.00020012')[0], 'over-precise');
});

test('an integer string with no dot is not a timestamp', () => {
  assert.equal(tsFault('1755000398')[0], 'not-a-timestamp');
  assert.equal(tsFault('hello')[0], 'not-a-timestamp');
});

test('exponent notation is its own verdict', () => {
  assert.equal(tsFault('1.7550000000002e9')[0], 'scientific');
});

test('a missing ts names the webhook dead end', () => {
  for (const value of [null, undefined, '', '   ']) {
    const [verdict, detail] = tsFault(value);
    assert.equal(verdict, 'missing');
    assert.match(detail, /webhook/);
  }
});

test('a boolean is not quietly stringified', () => {
  assert.equal(tsFault(true)[0], 'not-a-string');
});

test('repad restores only the zeros a float drops', () => {
  assert.equal(repad('1755000000.0002'), '1755000000.000200');
  assert.equal(repad(1755000000.0002), '1755000000.000200');
  assert.equal(repad(1755000398), '1755000398.000000');
  assert.equal(repad('1755000000.000200'), '1755000000.000200');
});

test('repad refuses when the damage could have been anything else', () => {
  assert.equal(repad('1755000000.00020012'), '');
  assert.equal(repad('not a ts'), '');
  assert.equal(repad(null), '');
  assert.equal(repad(true), '');
  assert.equal(repad(Number.NaN), '');
});

test('repad trims a tail that is only zeros', () => {
  assert.equal(repad('1755000000.0002000'), '1755000000.000200');
});

test('sameTs sees through the round trip that equality misses', () => {
  assert.notEqual('1755000000.0002', '1755000000.000200');
  assert.equal(sameTs('1755000000.0002', '1755000000.000200'), true);
  assert.equal(sameTs(1755000000.0002, '1755000000.000200'), true);
  assert.equal(sameTs('1755000000.000200', '1755000000.000201'), false);
  assert.equal(sameTs('', '1755000000.000200'), false);
});

test('the exact probe asks for one message at that instant', () => {
  const params = windowParams('C1', '1755000000.0002');
  assert.equal(params.latest, '1755000000.000200');
  assert.equal(params.oldest, '1755000000.000200');
  assert.equal(params.inclusive, 'true');
  assert.equal(params.limit, '1');
});

test('the widened probe reaches the neighbours', () => {
  const params = windowParams('C1', '1755000000.000200', 1, 20);
  assert.equal(params.oldest, '1754999999.000200');
  assert.equal(params.latest, '1755000001.000200');
  assert.equal(params.limit, '20');
});

test('an exact hit is found', () => {
  const [verdict, , matched] = resolution('1755000000.000200',
    [msg('1755000000.000200')]);
  assert.equal(verdict, 'found');
  assert.equal(matched, '1755000000.000200');
});

test('a neighbour that repads to yours is the proof it was a float', () => {
  const [verdict, detail, matched] = resolution('1755000000.0002',
    [msg('1755000000.111111'), msg('1755000000.000200')]);
  assert.equal(verdict, 'precision-loss');
  assert.equal(matched, '1755000000.000200');
  assert.match(detail, /not a deletion/);
});

test('an empty window is absent and reads as a deletion', () => {
  const [verdict, detail] = resolution('1755000000.000200', []);
  assert.equal(verdict, 'absent');
  assert.match(detail, /deleted/);
});

test('a busy window with nothing of yours is the wrong channel shape', () => {
  const [verdict, detail] = resolution('1755000000.000200',
    [msg('1755000000.111111'), msg('1755000000.222222')]);
  assert.equal(verdict, 'neighbours-only');
  assert.match(detail, /unique within one channel/);
});

test('absent and neighbours-only are never collapsed', () => {
  assert.notEqual(resolution('1755000000.000200', [])[0],
    resolution('1755000000.000200', [msg('1755000000.999999')])[0]);
});
''',
"faq": [
 ("The message is right there in the channel. How can it not be found?",
  "Because Slack is not looking for the message, it is looking for the pair. chat.update takes a channel and a ts and matches both exactly. If either one is wrong the message you can see is not the message you asked about, and message_not_found is the honest answer. The most common wrong half is the ts, and the most common reason it is wrong is that it stopped being a string somewhere in your storage."),
 ("Why does the ts have to be a string when it looks exactly like a number?",
  "Because it is a key, not a quantity. Nothing ever adds one ts to another. The moment it becomes a double it loses trailing zeros, so 1755000000.000200 comes back as 1755000000.0002, and a value that differs from the key by four invisible characters matches nothing. Slack sends it as a string for this reason, and every layer of your stack has to keep it that way, not just the variable in the calling function."),
 ("Can I just re-pad the ts back to six digits and retry?",
  "For the specific case where trailing zeros were dropped, yes, and this script does exactly that to find the message and prove the cause. As a fix, no. The re-pad works because zeros carry no information, and the moment the damage is anything else the repaired value points at a different message, which is a far worse outcome than an error. Fix the storage and re-capture the ts."),
 ("We post through an incoming webhook and cannot update anything. Is this the same problem?",
  "It is a different problem with the same error. A webhook responds with the plain text ok and no JSON, so there was never a ts to store. There is no field to fix and no scope to add; the message is unaddressable by design. If you need to edit it later, that path has to move to chat.postMessage with a bot token."),
 ("The message resolves fine and Slack still will not update it. Now what?",
  "Then the error will not be message_not_found. If the pair resolves and the edit is refused, the answer is cant_update_message, which is about which identity authored the message rather than whether it exists. That is a separate check and a separate note, and this script deliberately stops at existence so the two do not get confused."),
],
"related": [
 ("/slack/cant-update-or-delete-message/", "when the message resolves and is still not yours"),
 ("/slack/channel-name-instead-of-id/", "the other half of the pair, wrong in a different way"),
 ("/slack/http-200-ok-false/", "why the refusal arrived looking like a success"),
],
"citations": [CITE_CHAT_UPDATE, CITE_CONV_HISTORY, CITE_RETRIEVING, CITE_CHAT_DELETE],
})

GUIDES.append({
"slug": "cant-update-or-delete-message",
"title": "cant_update_message: that message is not yours to edit",
"description": "A message can only be changed by the identity that wrote it. Match every message you edit against your token's bot_id and user_id before the call, not after.",
"h1": "cant_update_message: that message is not yours to edit",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack cant_update_message", "slack cant_delete_message",
             "slack bot cannot edit user message",
             "slack chat.update wrong token type",
             "slack delete another user's message"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot or user token with channels:history",
"lead": "The message exists. You just read it back from <code>conversations.history</code>, the <code>ts</code> is exactly right, the channel is right, and <code>chat.update</code> answers <code>{\"ok\": false, \"error\": \"cant_update_message\"}</code>. This is not <code>message_not_found</code>. Slack found it. Slack will not let you touch it.</p><p>Editing and deleting are the two Slack methods where the token has to be the <em>author</em> and not merely authorised. A scope does not help, a reinstall does not help, and admin rights on the workspace mostly do not help either. The message belongs to whoever wrote it, and the only question worth asking is who that was.",
"short_answer": """<p>A message can be modified only by the identity that authored it. A bot token can change messages carrying that bot's <code>bot_id</code>. A user token can change messages carrying that user's <code>user_id</code>. They do not overlap in either direction: <strong>a bot token cannot edit a message posted with a user token, and a user token cannot edit a message posted by your own bot</strong>, even when that user is the person who installed the app.</p>
<p>Everything else follows from that. A message from another app carries a different <code>bot_id</code> and is unreachable. A message from an incoming webhook or a legacy custom integration carries a <code>bot_id</code> with no <code>app_id</code> beside it and is unreachable by any token at all. A human's message can never be edited by anyone but that human, and deleting one needs a <strong>user</strong> token belonging to an admin with <code>chat:write</code>, subject to workspace policy on top.</p>
<p>The check is a comparison and it is cheap: read <code>auth.test</code> once for your <code>bot_id</code>, your <code>user_id</code> and which class of token you are actually holding, then read the messages you intend to change and compare the authorship fields. The interesting output is not a boolean but a reason, because <em>a different app wrote this</em> and <em>you are holding the wrong kind of token</em> want completely different fixes.</p>""",
"problem": """<p>The confusing shape of this bug is that the code is usually right and the credential is usually wrong. A team writes an approval flow: a bot posts a message with a button, the button is clicked, and the handler edits the message to say <em>approved by Dana</em>. It works in development. In production the same handler runs under a user token, because that is the token the OAuth flow happened to store, and every edit comes back <code>cant_update_message</code>. Nothing in the payload changed. The author did.</p>
<p>The reverse direction catches teams who added a user-token feature later. A message posted with <code>chat.postMessage</code> on a user token appears in the channel as that person, with their name and their avatar. It is their message. The bot that runs the rest of the app is a different identity with a different <code>bot_id</code>, and it cannot edit that message any more than it could edit yours. Apps that post <em>as the user</em> for one feature and clean up with the bot for another discover this at the cleanup step.</p>
<p>Then there is the identity that looks like yours and is not. Posting with <code>username</code> and <code>icon_emoji</code> overrides changes what a message looks like and not who wrote it: those messages are still your bot's and still editable, which surprises people in the pleasant direction. An incoming webhook is the opposite surprise. It posts under an identity that renders like an app, carries a <code>bot_id</code>, and has no <code>app_id</code> beside it, and there is no token in the world that can edit it. It also returns the literal text <code>ok</code> rather than a <code>ts</code>, so the update path was never viable to begin with.</p>
<p>Deletion is stricter still and worth separating. <code>chat.delete</code> on your own bot's message is fine. <code>chat.delete</code> on a human's message requires a user token from someone with the right to do it, and workspace settings can remove that right entirely. A support tool that deletes messages containing an access key on a bot token will fail on every message it was built to clean up, because the messages it is cleaning up are all written by people.</p>
<p>All of this is visible before you call anything. The authorship fields are right there in <code>conversations.history</code>, and <code>auth.test</code> tells you which identity you hold. The only reason this is ever discovered at runtime is that nobody compares the two.</p>""",
"why": """<p><strong>Authorship is not a permission, so no scope fixes it.</strong> This is the part that costs the most time. The instinct on any Slack error is to add a scope and reinstall, and here that changes nothing at all: <code>chat:write</code> lets you write as yourself, and there is no scope that lets you write as somebody else. The script says which identity wrote the message so the conversation skips the reinstall entirely.</p>
<p><strong>auth.test tells you which class of token you are holding, and you should not assume you know.</strong> A bot token's <code>auth.test</code> comes back with a <code>bot_id</code>; a user token's does not. Apps that store both and pick one by variable name get this wrong regularly, and the symptom is a method that works for months and then does not after a config change nobody connected to it.</p>
<p><strong>The two directions of the mismatch are one verdict, because the fix is the same shape.</strong> Bot token against a user's message and user token against the bot's message are both <em>wrong token class</em>, and the repair in both is to make the identity that wrote it be the identity that changes it. Splitting them into two findings implies two different fixes and there is only one.</p>
<p><strong>A webhook message has no update path at all, and that is a design finding rather than a bug.</strong> The script names it separately from <em>another app wrote this</em>, because <em>another app</em> can sometimes be solved by asking that team, and a webhook cannot be solved by anyone. Moving the send to <code>chat.postMessage</code> is the whole answer.</p>
<p><strong>The interaction path is the exception that rescues most real cases.</strong> A button click hands you a <code>response_url</code>, and posting to it with <code>replace_original</code> replaces the original message regardless of which token posted it. That window is <strong>thirty minutes and five uses</strong>, which is why the script gives you a function that answers whether the window is still open rather than leaving it as a footnote.</p>
<p><strong>Deleting somebody else's message is a policy question, not an API question.</strong> The method exists, the credential is a user token belonging to an admin, and the workspace can still say no. The script reports <em>human, and this needs an admin user token</em> rather than pretending a code change will do it.</p>""",
"steps": [
 {"h": "Find out which token you are actually holding",
  "body": """<p><code>auth.test</code> first, every time. <code>token_class</code> reads the response and returns <code>bot</code> or <code>user</code>: a bot token's answer carries a <code>bot_id</code> and a user token's does not. This one line settles half the cases before any message is examined.</p>"""},
 {"h": "Read the authorship fields rather than the rendered name",
  "body": """<p><code>authorship</code> looks at <code>bot_id</code>, <code>app_id</code> and <code>user</code> together. The displayed name and avatar are decoration and can be overridden per message; the three id fields are the identity, and they are what Slack compares when you try to change something.</p>"""},
 {"h": "Compare, and read the verdict as a reason rather than a boolean",
  "body": """<p><code>mutability</code> returns one of <code>yours</code>, <code>wrong-token-class</code>, <code>other-app</code>, <code>webhook-or-legacy</code>, <code>human</code>, <code>another-user</code> or <code>unknown-author</code>. Only the first is editable, and the other six each want a different next move.</p>"""},
 {"h": "Take wrong-token-class seriously before you take anything else seriously",
  "body": """<p>It is the only verdict where your own code posted the message and your own code cannot change it. It means the two halves of your app are running as two identities, which is usually an accident of which token got read from the environment, and it is the cheapest of the six to fix.</p>"""},
 {"h": "Check whether the interaction window is still open",
  "body": """<p>If the edit is in response to a button, <code>response_url_plan</code> answers whether <code>replace_original</code> is still available: thirty minutes from the interaction, five uses. That path ignores authorship entirely, which makes it the right answer for most approval and acknowledgement flows and the wrong answer for a status message you update for an hour.</p>"""},
 {"h": "Stop at human rather than looking for a clever way through",
  "body": """<p>There is no bot-token route to deleting a person's message, and no scope that adds one. The script prints the requirement, which is an admin's user token with <code>chat:write</code> and a workspace that permits it, and leaves the decision with you rather than suggesting a workaround that does not exist.</p>"""},
],
"verify": """<p>Point it at the channel your app edits in. The line you want is a named identity, not a count of failures.</p>
<pre><code class="language-bash">python3 slack_cant_update_message.py --channel C024BE91L
# identity   user           U04HZ9K1M holds a user token; auth.test returned no bot_id
# authors    47 message(s) read in C024BE91L
# mutable    yours          12  posted by U04HZ9K1M with this same user token
# blocked    wrong-token-class 21  authored by B01J9Q7XA, which is your own bot. A user
#                               token cannot edit a message a bot wrote, and no scope
#                               changes that
# blocked    human          9   written by people; chat.update can never touch these and
#                               chat.delete needs an admin user token with chat:write
# blocked    webhook-or-legacy 5  a bot_id with no app_id beside it, so no token can edit
#                               it and no ts was ever returned to store
#   repair: use the identity that posted the message to change it, or replace it through
#           the interaction response_url within thirty minutes and five uses</code></pre>""",
"code_intro": "Four pure functions and one read. <code>token_class</code> is the line nobody writes and everybody needs. <code>authorship</code> deliberately ignores <code>username</code> and <code>icons</code>, because those are the fields that make a message look like it belongs to somebody it does not. <code>mutability</code> is the comparison, and it returns a reason rather than a boolean so that the two verdicts you can fix are never buried among the four you cannot. <code>response_url_plan</code> is the escape hatch, with its clock.",
"py_file": "slack_cant_update_message.py",
"py": '''"""Say which messages your token is allowed to change, and why not.

Read only. Nothing here edits or removes a message: the whole point is that
editing and removing are the two Slack methods where the token has to be the
author, and that is decidable in advance from conversations.history plus one
auth.test. The script compares the identities and prints the repair.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_cant_update_message")

API = "https://slack.com/api/"

# Slack's documented window on an interaction response_url: half an hour, and
# five uses. Both are ceilings, and hitting either one closes the only path
# that ignores authorship.
RESPONSE_URL_SECONDS = 1800
RESPONSE_URL_USES = 5


def token_class(auth):
    """Which kind of token is this, really? Pure.

    auth is the auth.test body. A bot token's answer carries a bot_id and a
    user token's does not, which is the only reliable discriminator; the
    prefix on the token string is not, because apps store both and read the
    wrong one by variable name.
    """
    if not isinstance(auth, dict) or auth.get("ok") is not True:
        return ("unknown", "auth.test did not answer ok, so the identity behind this "
                           "token is unknown and nothing below can be decided")
    if auth.get("bot_id"):
        return ("bot", "%s holds a bot token; auth.test returned bot_id %s"
                % (auth.get("user_id") or "?", auth.get("bot_id")))
    if auth.get("user_id"):
        return ("user", "%s holds a user token; auth.test returned no bot_id"
                % auth.get("user_id"))
    return ("unknown", "auth.test answered ok with no user_id, which should not happen")


def authorship(message):
    """Who wrote this message? Pure.

    Returns (kind, ident). Deliberately ignores username, icons and any display
    name: those are per-message decoration and can be set to anything, while
    bot_id, app_id and user are the identity Slack compares against your token.
    """
    if not isinstance(message, dict):
        return ("unknown", "")
    bot_id = str(message.get("bot_id") or "")
    app_id = str(message.get("app_id") or "")
    user = str(message.get("user") or "")
    if bot_id and app_id:
        return ("app", bot_id)
    if bot_id:
        return ("bot-no-app", bot_id)
    if user:
        return ("human", user)
    return ("unknown", "")


def mutability(message, identity):
    """Can this token change this message, and if not, why not? Pure.

    identity is {"bot_id", "user_id", "token"} where token is bot or user.
    Returns (verdict, detail). Only yours is changeable. The other verdicts are
    kept apart because they want different repairs: wrong-token-class is a
    credential your app already has, other-app is somebody else's problem, and
    human is a policy question with no code answer at all.
    """
    ident = identity or {}
    holder = str(ident.get("token") or "unknown")
    our_bot = str(ident.get("bot_id") or "")
    our_user = str(ident.get("user_id") or "")
    kind, author = authorship(message)

    if kind == "unknown":
        return ("unknown-author", "no bot_id, app_id or user on this message, so there "
                                  "is no identity to compare and no safe assumption")

    if kind in ("app", "bot-no-app"):
        if our_bot and author == our_bot:
            if holder == "bot":
                return ("yours", "authored by %s, which is this token's own bot. A "
                                 "username or icon_emoji override changes how it looks "
                                 "and not who wrote it, so those are editable too"
                        % author)
            return ("wrong-token-class",
                    "authored by %s, which is your own bot. A user token cannot edit a "
                    "message a bot wrote, even when that user installed the app, and no "
                    "scope changes that" % author)
        if kind == "bot-no-app":
            return ("webhook-or-legacy",
                    "a bot_id (%s) with no app_id beside it, which is what an incoming "
                    "webhook or a legacy custom integration produces. No token can edit "
                    "it, and a webhook answers with the text ok rather than a ts, so "
                    "there was never a pair to store" % author)
        return ("other-app", "authored by %s, a different app. Authorship is not a "
                             "permission, so there is no scope and no reinstall that "
                             "makes this editable by you" % author)

    if holder == "user" and our_user and author == our_user:
        return ("yours", "posted by %s with this same user token" % author)
    if holder == "user":
        return ("another-user", "written by %s, a different person. chat.update can "
                                "never touch it, and chat.delete needs an admin user "
                                "token with chat:write and a workspace that allows it"
                % author)
    return ("human", "written by %s, a person. A bot token can never edit this, and "
                     "deleting it needs an admin user token with chat:write rather than "
                     "any bot scope" % author)


def response_url_plan(age_seconds, uses=0, max_age=RESPONSE_URL_SECONDS,
                      max_uses=RESPONSE_URL_USES):
    """Is the interaction escape hatch still open? Pure.

    A response_url from a button click replaces the original message regardless
    of which token posted it, which is the one path that ignores authorship
    entirely. It is also the one path with a clock on it, and code that treats
    it as permanent fails silently the first time somebody clicks a button on
    yesterday's message.
    """
    if age_seconds is None:
        return ("no-interaction", "this edit is not in response to an interaction, so "
                                  "there is no response_url and authorship is the only "
                                  "rule that applies")
    try:
        age = float(age_seconds)
    except (TypeError, ValueError):
        return ("no-interaction", "no usable interaction age, so treat authorship as "
                                  "the only rule")
    used = int(uses or 0)
    if used >= max_uses:
        return ("exhausted", "%d of the %d permitted uses are gone; the url is spent "
                             "even though the clock has not run out" % (used, max_uses))
    if age > max_age:
        return ("expired", "%.0f seconds since the interaction and the window is %d. "
                           "Replacing the original is no longer possible and authorship "
                           "is back to being the only rule" % (age, max_age))
    return ("usable", "%.0f seconds in, %d of %d uses spent: replace_original still "
                      "works here and ignores which token posted the message"
            % (age, used, max_uses))


def summarise(messages, identity):
    """Group a channel's messages by what this token could do to them."""
    counts = {}
    for m in messages or []:
        verdict, detail = mutability(m, identity)
        row = counts.setdefault(verdict, {"count": 0, "detail": detail})
        row["count"] += 1
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel your app edits messages in; repeatable")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the token to test")
    ap.add_argument("--limit", type=int, default=200, help="messages read per channel")
    ap.add_argument("--interaction-age", type=float, default=None,
                    help="seconds since the button click, to test the response_url path")
    ap.add_argument("--interaction-uses", type=int, default=0,
                    help="how many times that response_url has already been used")
    args = ap.parse_args()

    if not args.channel:
        log.error("pass at least one --channel")
        return 2
    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to the token whose edits are failing", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    auth = s.get(API + "auth.test", timeout=30).json()
    holder, detail = token_class(auth)
    if holder == "unknown":
        log.error("identity   unknown        %s", detail)
        return 2
    log.info("identity   %-14s %s", holder, detail)
    identity = {"bot_id": auth.get("bot_id") or "", "user_id": auth.get("user_id") or "",
                "token": holder}

    if args.interaction_age is not None:
        verdict, why = response_url_plan(args.interaction_age, args.interaction_uses)
        (log.info if verdict == "usable" else log.warning)(
            "response   %-14s %s", verdict, why)

    blocked = 0
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        messages = body.get("messages") or []
        log.info("authors    %d message(s) read in %s", len(messages), channel)
        for verdict, row in sorted(summarise(messages, identity).items()):
            if verdict == "yours":
                log.info("mutable    %-18s %d  %s", verdict, row["count"], row["detail"])
            else:
                blocked += row["count"]
                log.warning("blocked    %-18s %d  %s", verdict, row["count"],
                            row["detail"])

    if blocked:
        log.warning("  repair: use the identity that posted the message to change it; "
                    "authorship is not a permission and no scope grants it")
        log.warning("  repair: for an edit in response to a button, replace the original "
                    "through the interaction response_url, within thirty minutes and "
                    "five uses")
        log.warning("  repair: to remove somebody else's message you need an admin user "
                    "token with chat:write, and the workspace can still refuse")
        return 1
    log.info("verdict    clean          every message read is one this token authored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-cant-update-message.mjs",
"js": '''/**
 * Say which messages your token is allowed to change, and why not.
 *
 * Read only. Nothing here edits or removes a message: the whole point is that
 * editing and removing are the two Slack methods where the token has to be the
 * author, and that is decidable in advance from conversations.history plus one
 * auth.test. The script compares the identities and prints the repair.
 */

const API = 'https://slack.com/api/';

// Slack's documented window on an interaction response_url: half an hour, and
// five uses. Hitting either closes the only path that ignores authorship.
const RESPONSE_URL_SECONDS = 1800;
const RESPONSE_URL_USES = 5;

/**
 * Which kind of token is this, really? Pure.
 * A bot token's auth.test carries a bot_id and a user token's does not.
 */
export function tokenClass(auth) {
  if (!auth || typeof auth !== 'object' || auth.ok !== true) {
    return ['unknown', 'auth.test did not answer ok, so the identity behind this token '
      + 'is unknown and nothing below can be decided'];
  }
  if (auth.bot_id) {
    return ['bot', `${auth.user_id ?? '?'} holds a bot token; auth.test returned bot_id `
      + `${auth.bot_id}`];
  }
  if (auth.user_id) {
    return ['user', `${auth.user_id} holds a user token; auth.test returned no bot_id`];
  }
  return ['unknown', 'auth.test answered ok with no user_id, which should not happen'];
}

/**
 * Who wrote this message? Pure. Returns [kind, ident].
 * Ignores username and icons on purpose: those are per-message decoration.
 */
export function authorship(message) {
  if (!message || typeof message !== 'object') return ['unknown', ''];
  const botId = String(message.bot_id ?? '');
  const appId = String(message.app_id ?? '');
  const user = String(message.user ?? '');
  if (botId && appId) return ['app', botId];
  if (botId) return ['bot-no-app', botId];
  if (user) return ['human', user];
  return ['unknown', ''];
}

/**
 * Can this token change this message, and if not, why not? Pure.
 * identity is { bot_id, user_id, token } where token is bot or user.
 */
export function mutability(message, identity) {
  const ident = identity ?? {};
  const holder = String(ident.token ?? 'unknown');
  const ourBot = String(ident.bot_id ?? '');
  const ourUser = String(ident.user_id ?? '');
  const [kind, author] = authorship(message);

  if (kind === 'unknown') {
    return ['unknown-author', 'no bot_id, app_id or user on this message, so there is '
      + 'no identity to compare and no safe assumption'];
  }

  if (kind === 'app' || kind === 'bot-no-app') {
    if (ourBot && author === ourBot) {
      if (holder === 'bot') {
        return ['yours', `authored by ${author}, which is this token's own bot. A `
          + 'username or icon_emoji override changes how it looks and not who wrote '
          + 'it, so those are editable too'];
      }
      return ['wrong-token-class', `authored by ${author}, which is your own bot. A `
        + 'user token cannot edit a message a bot wrote, even when that user installed '
        + 'the app, and no scope changes that'];
    }
    if (kind === 'bot-no-app') {
      return ['webhook-or-legacy', `a bot_id (${author}) with no app_id beside it, `
        + 'which is what an incoming webhook or a legacy custom integration produces. '
        + 'No token can edit it, and a webhook answers with the text ok rather than a '
        + 'ts, so there was never a pair to store'];
    }
    return ['other-app', `authored by ${author}, a different app. Authorship is not a `
      + 'permission, so there is no scope and no reinstall that makes this editable '
      + 'by you'];
  }

  if (holder === 'user' && ourUser && author === ourUser) {
    return ['yours', `posted by ${author} with this same user token`];
  }
  if (holder === 'user') {
    return ['another-user', `written by ${author}, a different person. chat.update can `
      + 'never touch it, and chat.delete needs an admin user token with chat:write and '
      + 'a workspace that allows it'];
  }
  return ['human', `written by ${author}, a person. A bot token can never edit this, `
    + 'and deleting it needs an admin user token with chat:write rather than any bot '
    + 'scope'];
}

/**
 * Is the interaction escape hatch still open? Pure.
 * A response_url replaces the original regardless of which token posted it,
 * and it is the one path with a clock on it.
 */
export function responseUrlPlan(ageSeconds, uses = 0, maxAge = RESPONSE_URL_SECONDS,
  maxUses = RESPONSE_URL_USES) {
  if (ageSeconds === null || ageSeconds === undefined
      || !Number.isFinite(Number(ageSeconds))) {
    return ['no-interaction', 'this edit is not in response to an interaction, so there '
      + 'is no response_url and authorship is the only rule that applies'];
  }
  const age = Number(ageSeconds);
  const used = Number(uses ?? 0) || 0;
  if (used >= maxUses) {
    return ['exhausted', `${used} of the ${maxUses} permitted uses are gone; the url is `
      + 'spent even though the clock has not run out'];
  }
  if (age > maxAge) {
    return ['expired', `${age.toFixed(0)} seconds since the interaction and the window `
      + `is ${maxAge}. Replacing the original is no longer possible and authorship is `
      + 'back to being the only rule'];
  }
  return ['usable', `${age.toFixed(0)} seconds in, ${used} of ${maxUses} uses spent: `
    + 'replace_original still works here and ignores which token posted the message'];
}

/** Group a channel's messages by what this token could do to them. */
export function summarise(messages, identity) {
  const counts = new Map();
  for (const m of messages ?? []) {
    const [verdict, detail] = mutability(m, identity);
    if (!counts.has(verdict)) counts.set(verdict, { count: 0, detail });
    counts.get(verdict).count += 1;
  }
  return counts;
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
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error('pass at least one --channel');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to the token whose edits are failing`);
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const headers = { Authorization: `Bearer ${token}` };

  const auth = await (await fetch(`${API}auth.test`, { headers })).json();
  const [holder, detail] = tokenClass(auth);
  if (holder === 'unknown') {
    console.error(`identity   unknown        ${detail}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${holder.padEnd(14)} ${detail}`);
  const identity = { bot_id: auth.bot_id ?? '', user_id: auth.user_id ?? '',
    token: holder };

  const age = arg(args, '--interaction-age', null);
  if (age !== null) {
    const [verdict, why] = responseUrlPlan(Number(age),
      Number(arg(args, '--interaction-uses', '0')));
    const line = `response   ${verdict.padEnd(14)} ${why}`;
    if (verdict === 'usable') console.log(line); else console.warn(line);
  }

  let blocked = 0;
  for (const channel of channels) {
    const qs = new URLSearchParams({ channel, limit: String(limit) }).toString();
    const body = await (await fetch(`${API}conversations.history?${qs}`, { headers }))
      .json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    const messages = body.messages ?? [];
    console.log(`authors    ${messages.length} message(s) read in ${channel}`);
    for (const [verdict, row] of [...summarise(messages, identity)].sort()) {
      if (verdict === 'yours') {
        console.log(`mutable    ${verdict.padEnd(18)} ${row.count}  ${row.detail}`);
      } else {
        blocked += row.count;
        console.warn(`blocked    ${verdict.padEnd(18)} ${row.count}  ${row.detail}`);
      }
    }
  }

  if (blocked) {
    console.warn('  repair: use the identity that posted the message to change it; '
      + 'authorship is not a permission and no scope grants it');
    console.warn('  repair: for an edit in response to a button, replace the original '
      + 'through the interaction response_url, within thirty minutes and five uses');
    console.warn('  repair: to remove somebody else\\'s message you need an admin user '
      + 'token with chat:write, and the workspace can still refuse');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          every message read is one this token authored');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are mostly about the two directions of the same mistake, because that symmetry is the note. A bot token facing a message a user wrote and a user token facing a message the bot wrote must both come back <code>wrong-token-class</code>, since the repair is the same in both. A <code>username</code> override must not move a message out of <code>yours</code>, because the display name is the field most likely to make somebody believe the wrong thing. And <code>response_url_plan</code> must go <code>exhausted</code> on the fifth use even at one second old, since the two limits are independent and code that only watches the clock is wrong about half the time.",
"test_py_file": "test_slack_cant_update_message.py",
"test_py": '''from slack_cant_update_message import (authorship, mutability, response_url_plan,
                                       summarise, token_class)

BOT = {"bot_id": "B01J9Q7XA", "user_id": "U0BOTUSER", "token": "bot"}
USER = {"bot_id": "", "user_id": "U04HZ9K1M", "token": "user"}


def test_a_bot_token_is_recognised_by_its_bot_id():
    verdict, detail = token_class({"ok": True, "user_id": "U0BOTUSER",
                                   "bot_id": "B01J9Q7XA"})
    assert verdict == "bot"
    assert "B01J9Q7XA" in detail


def test_a_user_token_is_the_absence_of_a_bot_id():
    verdict, detail = token_class({"ok": True, "user_id": "U04HZ9K1M"})
    assert verdict == "user"
    assert "no bot_id" in detail


def test_a_failed_auth_test_is_never_guessed_at():
    assert token_class({"ok": False, "error": "invalid_auth"})[0] == "unknown"
    assert token_class(None)[0] == "unknown"


def test_authorship_reads_ids_and_not_the_displayed_name():
    assert authorship({"bot_id": "B1", "app_id": "A1", "username": "Totally Dana"}) \\
        == ("app", "B1")
    assert authorship({"bot_id": "B1"}) == ("bot-no-app", "B1")
    assert authorship({"user": "U9"}) == ("human", "U9")
    assert authorship({}) == ("unknown", "")
    assert authorship("not a message") == ("unknown", "")


def test_a_bot_token_can_change_its_own_bot_message():
    verdict, detail = mutability({"bot_id": "B01J9Q7XA", "app_id": "A1"}, BOT)
    assert verdict == "yours"
    assert "own bot" in detail


def test_a_username_override_does_not_change_who_wrote_it():
    message = {"bot_id": "B01J9Q7XA", "app_id": "A1", "subtype": "bot_message",
               "username": "Deploy Bot", "icons": {"emoji": ":rocket:"}}
    verdict, detail = mutability(message, BOT)
    assert verdict == "yours"
    assert "icon_emoji" in detail


def test_a_user_token_cannot_edit_your_own_bots_message():
    verdict, detail = mutability({"bot_id": "B01J9Q7XA", "app_id": "A1"},
                                 dict(USER, bot_id="B01J9Q7XA"))
    assert verdict == "wrong-token-class"
    assert "installed the app" in detail


def test_a_bot_token_cannot_edit_a_message_a_person_wrote():
    verdict, detail = mutability({"user": "U04HZ9K1M"}, BOT)
    assert verdict == "human"
    assert "admin user token" in detail


def test_a_user_token_owns_only_that_users_messages():
    assert mutability({"user": "U04HZ9K1M"}, USER)[0] == "yours"
    verdict, detail = mutability({"user": "U7SOMEONE"}, USER)
    assert verdict == "another-user"
    assert "chat.delete needs an admin" in detail


def test_another_apps_message_is_named_as_a_different_app():
    verdict, detail = mutability({"bot_id": "B99OTHER", "app_id": "A99"}, BOT)
    assert verdict == "other-app"
    assert "not a permission" in detail


def test_a_bot_id_with_no_app_id_is_the_webhook_dead_end():
    verdict, detail = mutability({"bot_id": "B77HOOK", "subtype": "bot_message"}, BOT)
    assert verdict == "webhook-or-legacy"
    assert "never a pair to store" in detail


def test_a_message_with_no_author_fields_is_not_assumed_editable():
    assert mutability({"text": "hi"}, BOT)[0] == "unknown-author"


def test_the_two_directions_of_the_mismatch_share_one_verdict():
    as_user = mutability({"bot_id": "B01J9Q7XA", "app_id": "A1"},
                         dict(USER, bot_id="B01J9Q7XA"))[0]
    assert as_user == "wrong-token-class"


def test_the_response_url_window_is_open_inside_thirty_minutes():
    verdict, detail = response_url_plan(120, 1)
    assert verdict == "usable"
    assert "replace_original" in detail


def test_the_response_url_expires_on_the_clock():
    verdict, detail = response_url_plan(1801, 0)
    assert verdict == "expired"
    assert "1800" in detail


def test_the_response_url_expires_on_uses_independently_of_the_clock():
    verdict, detail = response_url_plan(1, 5)
    assert verdict == "exhausted"
    assert "clock has not run out" in detail


def test_an_edit_with_no_interaction_behind_it_says_so():
    assert response_url_plan(None)[0] == "no-interaction"
    assert response_url_plan("soon")[0] == "no-interaction"


def test_summarise_counts_by_reason_rather_than_by_pass_or_fail():
    messages = [{"bot_id": "B01J9Q7XA", "app_id": "A1"},
                {"bot_id": "B01J9Q7XA", "app_id": "A1"},
                {"user": "U04HZ9K1M"},
                {"bot_id": "B99OTHER", "app_id": "A99"}]
    counts = summarise(messages, BOT)
    assert counts["yours"]["count"] == 2
    assert counts["human"]["count"] == 1
    assert counts["other-app"]["count"] == 1


def test_an_empty_channel_produces_no_findings():
    assert summarise([], BOT) == {}
''',
"test_js_file": "slack-cant-update-message.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  authorship, mutability, responseUrlPlan, summarise, tokenClass,
} from './slack-cant-update-message.mjs';

const BOT = { bot_id: 'B01J9Q7XA', user_id: 'U0BOTUSER', token: 'bot' };
const USER = { bot_id: '', user_id: 'U04HZ9K1M', token: 'user' };

test('a bot token is recognised by its bot_id', () => {
  const [verdict, detail] = tokenClass({ ok: true, user_id: 'U0BOTUSER',
    bot_id: 'B01J9Q7XA' });
  assert.equal(verdict, 'bot');
  assert.match(detail, /B01J9Q7XA/);
});

test('a user token is the absence of a bot_id', () => {
  const [verdict, detail] = tokenClass({ ok: true, user_id: 'U04HZ9K1M' });
  assert.equal(verdict, 'user');
  assert.match(detail, /no bot_id/);
});

test('a failed auth.test is never guessed at', () => {
  assert.equal(tokenClass({ ok: false, error: 'invalid_auth' })[0], 'unknown');
  assert.equal(tokenClass(null)[0], 'unknown');
});

test('authorship reads ids and not the displayed name', () => {
  assert.deepEqual(authorship({ bot_id: 'B1', app_id: 'A1', username: 'Totally Dana' }),
    ['app', 'B1']);
  assert.deepEqual(authorship({ bot_id: 'B1' }), ['bot-no-app', 'B1']);
  assert.deepEqual(authorship({ user: 'U9' }), ['human', 'U9']);
  assert.deepEqual(authorship({}), ['unknown', '']);
  assert.deepEqual(authorship('not a message'), ['unknown', '']);
});

test('a bot token can change its own bot message', () => {
  const [verdict, detail] = mutability({ bot_id: 'B01J9Q7XA', app_id: 'A1' }, BOT);
  assert.equal(verdict, 'yours');
  assert.match(detail, /own bot/);
});

test('a username override does not change who wrote it', () => {
  const message = { bot_id: 'B01J9Q7XA', app_id: 'A1', subtype: 'bot_message',
    username: 'Deploy Bot', icons: { emoji: ':rocket:' } };
  const [verdict, detail] = mutability(message, BOT);
  assert.equal(verdict, 'yours');
  assert.match(detail, /icon_emoji/);
});

test('a user token cannot edit your own bot message', () => {
  const [verdict, detail] = mutability({ bot_id: 'B01J9Q7XA', app_id: 'A1' },
    { ...USER, bot_id: 'B01J9Q7XA' });
  assert.equal(verdict, 'wrong-token-class');
  assert.match(detail, /installed the app/);
});

test('a bot token cannot edit a message a person wrote', () => {
  const [verdict, detail] = mutability({ user: 'U04HZ9K1M' }, BOT);
  assert.equal(verdict, 'human');
  assert.match(detail, /admin user token/);
});

test('a user token owns only that user messages', () => {
  assert.equal(mutability({ user: 'U04HZ9K1M' }, USER)[0], 'yours');
  const [verdict, detail] = mutability({ user: 'U7SOMEONE' }, USER);
  assert.equal(verdict, 'another-user');
  assert.match(detail, /chat\\.delete needs an admin/);
});

test('another app message is named as a different app', () => {
  const [verdict, detail] = mutability({ bot_id: 'B99OTHER', app_id: 'A99' }, BOT);
  assert.equal(verdict, 'other-app');
  assert.match(detail, /not a permission/);
});

test('a bot_id with no app_id is the webhook dead end', () => {
  const [verdict, detail] = mutability({ bot_id: 'B77HOOK', subtype: 'bot_message' },
    BOT);
  assert.equal(verdict, 'webhook-or-legacy');
  assert.match(detail, /never a pair to store/);
});

test('a message with no author fields is not assumed editable', () => {
  assert.equal(mutability({ text: 'hi' }, BOT)[0], 'unknown-author');
});

test('the response_url window is open inside thirty minutes', () => {
  const [verdict, detail] = responseUrlPlan(120, 1);
  assert.equal(verdict, 'usable');
  assert.match(detail, /replace_original/);
});

test('the response_url expires on the clock', () => {
  const [verdict, detail] = responseUrlPlan(1801, 0);
  assert.equal(verdict, 'expired');
  assert.match(detail, /1800/);
});

test('the response_url expires on uses independently of the clock', () => {
  const [verdict, detail] = responseUrlPlan(1, 5);
  assert.equal(verdict, 'exhausted');
  assert.match(detail, /clock has not run out/);
});

test('an edit with no interaction behind it says so', () => {
  assert.equal(responseUrlPlan(null)[0], 'no-interaction');
  assert.equal(responseUrlPlan(undefined)[0], 'no-interaction');
  assert.equal(responseUrlPlan('soon')[0], 'no-interaction');
});

test('summarise counts by reason rather than by pass or fail', () => {
  const messages = [{ bot_id: 'B01J9Q7XA', app_id: 'A1' },
    { bot_id: 'B01J9Q7XA', app_id: 'A1' },
    { user: 'U04HZ9K1M' },
    { bot_id: 'B99OTHER', app_id: 'A99' }];
  const counts = summarise(messages, BOT);
  assert.equal(counts.get('yours').count, 2);
  assert.equal(counts.get('human').count, 1);
  assert.equal(counts.get('other-app').count, 1);
});

test('an empty channel produces no findings', () => {
  assert.equal(summarise([], BOT).size, 0);
});
''',
"faq": [
 ("Which scope do I need so my bot can edit this message?",
  "There is not one. chat:write lets a token write as itself, and Slack has no scope that lets one identity edit another identity's message. This is the single most useful thing to know about this error, because the reflex on any Slack failure is to add a scope and reinstall, and here that costs an hour and changes nothing. The fix is always about which identity is making the call."),
 ("We post as the user for one feature and as the bot for the rest. Why does cleanup fail?",
  "Because those are two authors. A message posted on a user token belongs to that person and renders with their name; the bot is a separate identity with its own bot_id and cannot edit it. This is the wrong-token-class verdict in both directions, and the usual fix is to make the identity that posts a given message also be the identity that later changes it."),
 ("Does posting with username or icon_emoji change who owns the message?",
  "No, and that is the good news in this note. Those overrides change the rendering only. The message still carries your bot's bot_id, so your bot token can still edit and delete it. If a message looks like it was posted by something else and your token can change it anyway, this is why."),
 ("How do I delete a message a person posted, for example one containing a secret?",
  "With a user token belonging to someone allowed to delete other people's messages, holding chat:write, and only if the workspace's settings permit it. There is no bot-token path. If you are building a secret-scrubbing tool, plan on a user token from an admin from the start, because every message such a tool is meant to remove will be written by a human."),
 ("The message came from an incoming webhook. Can I edit it with the right token?",
  "No token can. A webhook message has no app-level identity that chat.update will accept, and the webhook itself answered your post with the plain text ok rather than a ts, so there was never a valid pair to store. If you need to edit later, the send has to move to chat.postMessage with a bot token; there is no smaller change that works."),
],
"related": [
 ("/slack/chat-update-message-not-found/", "when the pair does not resolve at all"),
 ("/slack/bot-vs-user-scope-mixup/", "the other note about holding the wrong one of two tokens"),
 ("/slack/not-allowed-token-type/", "a method that refuses the class of token outright"),
],
"citations": [CITE_CHAT_UPDATE, CITE_CHAT_DELETE, CITE_AUTH_TEST, CITE_INTERACTIVITY],
})

GUIDES.append({
"slug": "ephemeral-user-not-in-channel",
"title": "user_not_in_channel: an ephemeral nobody ever sees",
"description": "chat.postEphemeral renders into one person's view of one channel. Check the recipient can see the channel before you send, and fall back to a DM.",
"h1": "user_not_in_channel: an ephemeral nobody ever sees",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack chat.postEphemeral user_not_in_channel",
             "slack ephemeral message not showing",
             "slack postEphemeral ok true not visible",
             "slack ephemeral message disappeared",
             "slack ephemeral vs direct message"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with users:read plus channels:read and groups:read",
"lead": "A user runs the slash command, the handler answers with <code>chat.postEphemeral</code>, and the API says <code>{\"ok\": true, \"message_ts\": \"1755000000.000200\"}</code>. There is a timestamp. There is no error. The user says nothing happened.</p><p>They are both right. An ephemeral message is not a message stored in a channel, it is a rendering drawn into <em>one person's view</em> of <em>one channel</em>. If that person is not in the channel there is no view to draw into, so the drawing goes nowhere. Sometimes Slack tells you, with <code>user_not_in_channel</code>. Sometimes it takes the call, hands back a timestamp, and shows nobody anything.",
"short_answer": """<p><code>chat.postEphemeral</code> needs both a <code>channel</code> and a <code>user</code>, and the user has to be able to see that channel. When they cannot, you get <code>user_not_in_channel</code>, or in some situations an <code>ok: true</code> response with a <code>message_ts</code> that renders for nobody. The timestamp is not a receipt; there is no message behind it.</p>
<p>This is a property of the primitive rather than a bug. Ephemeral messages are not persisted anywhere: they do not appear in <code>conversations.history</code>, they cannot be edited after the session, they cannot be deleted, and they vanish when the client reloads. They exist to say <em>got it, working on that</em> and nothing more.</p>
<p>So there are two checks and they are different. The delivery check is a read: <code>conversations.members</code> or <code>users.conversations</code> for membership, and <code>users.info</code> to confirm the recipient is a real, active human rather than a deactivated account or another app. The design check is about the content: an ephemeral that carries a button, a file, or anything the reader might want to come back to is using the wrong primitive, and the tell is that a read-only audit finds no trace of it anywhere.</p>""",
"problem": """<p>The reason this survives testing is that developers are members of every channel they test in. You install the app, you join <code>#support</code>, you run the command, the ephemeral appears, and the feature ships. The first real user is someone the app is reaching out to rather than someone who came to it: a reviewer named in a ticket, an on-call engineer picked from a rota, the author of a pull request. None of them are necessarily in the channel, and for them the feature simply does not exist.</p>
<p>The silence is what makes it expensive. There is no error in the log for the <code>ok: true</code> case, nothing in <code>conversations.history</code> to inspect afterwards, and nothing the user can screenshot. The bug report is <em>the bot ignored me</em>, which sends everyone to look at the handler, the event subscription, and the token, none of which are involved. The one place the answer lives is a membership list nobody thought to read, because the app is the thing posting and the app is in the channel.</p>
<p>Private channels sharpen it. A user who is not a member of a private channel cannot see it at all, so an ephemeral aimed at them is doubly impossible, and if your token lacks <code>groups:read</code> you cannot even enumerate the membership to find out. Single-channel guests are the same story with a policy on top: they are confined to the channels they were invited to, and there is no move that puts them somewhere else so you can show them a transient string.</p>
<p>Then there are the recipients who are not people. A deactivated account still resolves in <code>users.info</code>, still has a name, and still looks like a valid <code>user</code> argument, so a rota built from a stale list keeps aiming ephemerals at somebody who left in March. Bot users and app users are worse, because they have no client rendering anything at all, and the call can come back clean.</p>
<p>The last failure is the one nobody calls a failure. An app answers a slash command with an ephemeral that contains an approval button and a link to the run. The user is in the channel, everything works, and then they reload Slack and it is gone, with nothing in the channel history and no way to get it back. That is not a delivery problem; it is a durable payload sent down a transient channel, and it is the most common misuse of the primitive.</p>""",
"why": """<p><strong>The recipient's membership is the question, not the app's.</strong> This is the distinction that makes this note separate from every other channel note in this section. Whether <em>your bot</em> is in the channel is a different check with a different error, and this script deliberately does not read <code>is_member</code> so the two findings never blur together.</p>
<p><strong>An ok with a message_ts is not evidence of delivery.</strong> Ephemerals are the one place in the Slack API where a timestamp comes back for something that was never stored. Code that logs the <code>message_ts</code> and calls it delivered is logging a number that refers to nothing, and no later read will ever find it.</p>
<p><strong>The membership read has to be paginated, and a partial answer is worse than none.</strong> <code>conversations.members</code> pages at 100 by default, so a script that reads one page of a 400-person channel decides three hundred people are not members. The script follows the cursor and reports <code>membership-unknown</code> rather than <code>not-member</code> when it could not finish, because a confident wrong answer here reroutes real messages into DMs.</p>
<p><strong>The right fallback is a DM, not an invitation.</strong> Adding somebody to a channel so they can see a transient acknowledgement is a permanent change made for a message that lasts seconds, and it is visible to everyone else in the channel. <code>conversations.open</code> followed by <code>chat.postMessage</code> is the fallback, and the script prints that rather than suggesting a join.</p>
<p><strong>Deactivated and bot recipients are skips, not retries.</strong> Both will fail forever, so a queue that retries them burns rate limit against your whole app on a message that can never arrive. The script separates them from <code>not-member</code>, which is the only verdict where a fallback is worth building.</p>
<p><strong>Content that outlives the session is the real bug in half of these.</strong> An ephemeral carrying a button cannot be updated once the session ends and leaves the click with nothing to replace. The script judges the payload as well as the recipient, because fixing the delivery of a message that should never have been ephemeral only makes the next problem harder to see.</p>""",
"steps": [
 {"h": "Check the recipient before you check anything else",
  "body": """<p><code>users.info</code> answers three questions in one call: does this account exist, is it <code>deleted</code>, and is it a bot or app user. <code>recipient_verdict</code> puts those ahead of membership on purpose, because a deactivated account is not a routing problem and no fallback will rescue it.</p>"""},
 {"h": "Read the membership all the way to the end of the cursor",
  "body": """<p><code>member_lookup</code> takes the pages of a <code>conversations.members</code> read and folds them into one set, and it refuses to answer if any page failed. A half-read membership list produces false <code>not-member</code> verdicts, which is how a working feature starts sending everybody a DM instead.</p>"""},
 {"h": "Take membership-unknown as a finding rather than a shrug",
  "body": """<p>If your token cannot enumerate the channel, that is usually a missing <code>groups:read</code> on a private conversation. The script says so rather than guessing, and the repair is a scope rather than a change to your send path.</p>"""},
 {"h": "Turn each verdict into the one action it deserves",
  "body": """<p><code>fallback_plan</code> maps the six verdicts onto four actions: send it, open a DM, skip permanently, or resolve the recipient first. The important pairing is <code>not-member</code> to <code>open-dm</code> and <code>deactivated</code> to <code>skip</code>, because retrying the second one is how a queue eats its own rate limit.</p>"""},
 {"h": "Judge the payload, not only the address",
  "body": """<p><code>ephemeral_fitness</code> reads the blocks with no token at all. A payload with an <code>actions</code> or <code>input</code> block comes back <code>interactive</code>, one carrying a file or several screens of content comes back <code>durable</code>, and only a short acknowledgement comes back <code>transient-ack</code>. The first two are using the wrong primitive.</p>"""},
 {"h": "Expect the audit to find nothing in history, and read that as the point",
  "body": """<p>Ephemerals never appear in <code>conversations.history</code>. If your team is trying to reconstruct what a user was shown and cannot find it anywhere, that absence is not a gap in your logging. It is the primitive behaving as documented, and it is the argument for moving anything that matters into a real message.</p>"""},
],
"verify": """<p>Run it over the pairs your app actually sends to. Every line should name a person and an action.</p>
<pre><code class="language-bash">python3 slack_ephemeral_recipient.py --pair U7REVIEWR:C024BE91L --pair U0LEFTFEB:C024BE91L
# members    C024BE91L: 214 member(s) read across 3 page(s)
# recipient  not-member     U7REVIEWR in C024BE91L  the ephemeral has no view to render
#                           into; Slack answers user_not_in_channel, or takes the call
#                           and shows nobody anything
#   action:  open-dm        conversations.open then chat.postMessage; do not add someone
#                           to a channel so they can see a message that lasts seconds
# recipient  deactivated    U0LEFTFEB in C024BE91L  users.info says deleted, so this can
#                           never arrive and retrying it spends your rate limit
#   action:  skip           remove the account from the rota rather than the queue
# fitness    interactive    the payload carries an actions block: an ephemeral cannot be
#                           updated after the session and the click has nothing to replace</code></pre>""",
"code_intro": "Four pure functions and two reads. <code>member_lookup</code> exists because pagination is the difference between a membership list and a wrong answer, and it returns <code>None</code> rather than a short set when a page failed. <code>recipient_verdict</code> orders its checks so that a permanent condition is never reported as a routing one. <code>fallback_plan</code> is the whole point of the note in one table. <code>ephemeral_fitness</code> needs no network and judges the payload rather than the address.",
"py_file": "slack_ephemeral_recipient.py",
"py": '''"""Say whether each ephemeral recipient could see the message at all.

Read only. Nothing here posts an ephemeral, a DM or anything else: the answer
is in users.info and the channel membership, both of which are reads, and
sending a test ephemeral to find out would show a real person a real message
they did not ask for.

Deliberately does not read is_member on the channel. Whether the app itself is
in the channel is a different failure with a different error, and mixing the two
produces an audit where nobody can tell whose membership is missing.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_ephemeral_recipient")

API = "https://slack.com/api/"

# Blocks that need the reader to come back to them. An ephemeral cannot be
# updated once the session ends and is not in history, so a click on one of
# these arrives with nothing left to replace.
RETURNING_BLOCKS = {"actions", "input"}
# Blocks whose content a reader is likely to want later, which an ephemeral
# cannot give them.
KEEPING_BLOCKS = {"file", "image", "video"}
ACK_CHARS = 280


def member_lookup(pages):
    """Fold paginated conversations.members answers into one set. Pure.

    Returns None rather than a short set when any page failed or was missing,
    because a half-read membership list turns members into not-member, and the
    fallback that follows sends real people a DM they should not have had.
    """
    found = set()
    for page in pages or []:
        if not isinstance(page, dict) or page.get("ok") is not True:
            return None
        members = page.get("members")
        if not isinstance(members, list):
            return None
        found.update(str(m) for m in members)
    return found if pages else None


def recipient_verdict(user_info, member):
    """Could this person see an ephemeral in this channel? Pure.

    member is True, False, or None for could-not-tell. The permanent
    conditions are checked before membership on purpose: a deactivated account
    is not a routing problem, and reporting it as one invites a fallback that
    will also never arrive.
    """
    info = user_info if isinstance(user_info, dict) else {}
    if not info or not info.get("id"):
        return ("unknown-user", "users.info returned nothing for this id, so there is "
                                "no recipient to reason about. A stale rota or a "
                                "hand-typed id lands here")
    who = str(info.get("id"))
    if info.get("deleted"):
        return ("deactivated", "%s is deactivated. users.info still returns a name and "
                               "a profile, so a stale rota keeps aiming at them; the "
                               "message can never arrive and retrying spends rate limit"
                % who)
    if info.get("is_bot") or info.get("is_app_user"):
        return ("bot-recipient", "%s is a bot or app user, which has no client and "
                                 "renders nothing. An ephemeral to it is a call that "
                                 "cannot fail and cannot be seen" % who)
    if member is None:
        return ("membership-unknown", "the membership of this channel could not be read "
                                      "in full. On a private channel that is usually a "
                                      "missing groups:read, and guessing here would "
                                      "reroute a working message into a DM")
    if not member:
        detail = ("%s is not in this channel, so the ephemeral has no view to render "
                  "into. Slack answers user_not_in_channel, or takes the call and shows "
                  "nobody anything" % who)
        if info.get("is_ultra_restricted"):
            detail += (". They are a single-channel guest, so they cannot be added to "
                       "another channel either")
        return ("not-member", detail)
    return ("member", "%s is in this channel and an ephemeral will render for them"
            % who)


def fallback_plan(verdict):
    """The one action each verdict deserves. Pure.

    The pairing that matters is not-member to open-dm and deactivated to skip.
    Retrying a permanent condition is how a queue spends a whole app's rate
    limit on messages that can never arrive.
    """
    table = {
        "member": ("send-ephemeral", "the recipient can see the channel; an ephemeral "
                                     "is fine for a transient acknowledgement"),
        "not-member": ("open-dm", "conversations.open then chat.postMessage; do not add "
                                  "somebody to a channel so they can see a message that "
                                  "lasts seconds and is visible to nobody else"),
        "deactivated": ("skip", "remove the account from the rota rather than from the "
                                "queue; no fallback reaches a deactivated user"),
        "bot-recipient": ("skip", "nothing renders for an app. If this is an "
                                  "integration talking to another integration, it needs "
                                  "an event or a real message, not an ephemeral"),
        "unknown-user": ("resolve-first", "resolve the id before sending anything. "
                                          "users.lookupByEmail or a fresh users.list is "
                                          "the fix, not a retry"),
        "membership-unknown": ("resolve-first", "add the scope that lets the token read "
                                                "this channel's membership; this is a "
                                                "credential change, not a send-path one"),
    }
    return table.get(verdict, ("resolve-first", "no rule for %s, so decide it by hand "
                                                "rather than defaulting to send"
                               % verdict))


def ephemeral_fitness(text, blocks=None):
    """Is this payload one an ephemeral can carry? Pure.

    Ephemerals are not stored: not in conversations.history, not updatable
    after the session, not deletable, and gone on a client reload. That makes
    them right for an acknowledgement and wrong for anything the reader might
    need twice.
    """
    body = str(text or "").strip()
    rows = blocks if isinstance(blocks, list) else []
    types = {str((b or {}).get("type") or "") for b in rows if isinstance(b, dict)}
    if not body and not rows:
        return ("empty", "no text and no blocks, so there is nothing to render and "
                         "nothing to diagnose")
    returning = sorted(types & RETURNING_BLOCKS)
    if returning:
        return ("interactive", "carries %s. An ephemeral cannot be updated once the "
                               "session ends and is not in history, so the click arrives "
                               "with nothing left to replace and the reader cannot get "
                               "back to it" % ", ".join(returning))
    keeping = sorted(types & KEEPING_BLOCKS)
    if keeping:
        return ("durable", "carries %s, which the reader will want again. An ephemeral "
                           "is gone at the next client reload and leaves no trace in "
                           "history" % ", ".join(keeping))
    if len(body) > ACK_CHARS or len(rows) > 3:
        return ("durable", "%d characters across %d block(s) is more than an "
                           "acknowledgement, and none of it survives a reload"
                % (len(body), len(rows)))
    return ("transient-ack", "short enough to be an acknowledgement, which is what an "
                             "ephemeral is for")


def parse_pair(text):
    """user:channel, in either order of the two id prefixes."""
    parts = str(text or "").split(":", 1)
    if len(parts) != 2:
        return ("", "")
    a, b = parts[0].strip(), parts[1].strip()
    return (b, a) if a.upper().startswith("C") or a.upper().startswith("G") else (a, b)


def read_members(session, channel, page_size=200):
    """Follow the cursor to the end, or give up honestly."""
    pages, cursor = [], ""
    while True:
        params = {"channel": channel, "limit": str(page_size)}
        if cursor:
            params["cursor"] = cursor
        page = session.get(API + "conversations.members", timeout=30,
                           params=params).json()
        pages.append(page)
        if page.get("ok") is not True:
            return pages
        cursor = ((page.get("response_metadata") or {}).get("next_cursor") or "").strip()
        if not cursor:
            return pages


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pair", action="append", default=[],
                    help="a user:channel pair your app sends ephemerals to; repeatable")
    ap.add_argument("--payload", default="",
                    help="a JSON file holding an ephemeral message, checked with no token")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    findings = 0
    if args.payload:
        raw = json.loads(open(args.payload, encoding="utf-8").read())
        verdict, detail = ephemeral_fitness(raw.get("text"), raw.get("blocks"))
        (log.info if verdict == "transient-ack" else log.warning)(
            "fitness    %-14s %s", verdict, detail)
        if verdict in ("interactive", "durable"):
            findings += 1

    if not args.pair:
        if args.payload:
            return 1 if findings else 0
        log.error("pass at least one --pair USER:CHANNEL, or --payload FILE")
        return 2

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s, or pass --payload alone to judge a message with no token",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    members_by_channel, users = {}, {}
    for pair in args.pair:
        user, channel = parse_pair(pair)
        if not user or not channel:
            log.warning("pair       unusable       %s is not USER:CHANNEL", pair)
            continue
        if channel not in members_by_channel:
            pages = read_members(s, channel)
            members_by_channel[channel] = member_lookup(pages)
            found = members_by_channel[channel]
            if found is None:
                log.warning("members    unavailable    %s: %s", channel,
                            pages[-1].get("error") if pages else "no answer")
            else:
                log.info("members    %s: %d member(s) read across %d page(s)", channel,
                         len(found), len(pages))
        if user not in users:
            body = s.get(API + "users.info", timeout=30, params={"user": user}).json()
            users[user] = (body.get("user") or {}) if body.get("ok") is True else {}

        known = members_by_channel[channel]
        member = None if known is None else (user in known)
        verdict, detail = recipient_verdict(users[user], member)
        action, why = fallback_plan(verdict)
        if verdict == "member":
            log.info("recipient  %-14s %s in %s  %s", verdict, user, channel, detail)
            continue
        findings += 1
        log.warning("recipient  %-14s %s in %s  %s", verdict, user, channel, detail)
        log.warning("  action:  %-14s %s", action, why)

    if findings:
        log.warning("  repair: check membership before the send and fall back to a DM; "
                    "an ok with a message_ts is not evidence anybody saw anything")
        log.warning("  repair: keep ephemerals for transient acknowledgements and put "
                    "anything the reader needs twice in a DM or a real message")
        return 1
    log.info("verdict    clean          every recipient can see the channel they are "
             "being drawn into")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-ephemeral-recipient.mjs",
"js": '''/**
 * Say whether each ephemeral recipient could see the message at all.
 *
 * Read only. Nothing here sends an ephemeral, a DM or anything else: the
 * answer is in users.info and the channel membership, both reads, and sending
 * a test ephemeral to find out would show a real person a real message they
 * did not ask for.
 *
 * Deliberately does not read is_member on the channel. Whether the app itself
 * is in the channel is a different failure with a different error.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Blocks that need the reader to come back to them. An ephemeral cannot be
// updated once the session ends and is not in history.
const RETURNING_BLOCKS = new Set(['actions', 'input']);
const KEEPING_BLOCKS = new Set(['file', 'image', 'video']);
const ACK_CHARS = 280;

/**
 * Fold paginated conversations.members answers into one set. Pure.
 * Returns null rather than a short set when any page failed.
 */
export function memberLookup(pages) {
  if (!Array.isArray(pages) || !pages.length) return null;
  const found = new Set();
  for (const page of pages) {
    if (!page || typeof page !== 'object' || page.ok !== true) return null;
    if (!Array.isArray(page.members)) return null;
    for (const m of page.members) found.add(String(m));
  }
  return found;
}

/**
 * Could this person see an ephemeral in this channel? Pure.
 * member is true, false, or null for could-not-tell.
 */
export function recipientVerdict(userInfo, member) {
  const info = (userInfo && typeof userInfo === 'object') ? userInfo : {};
  if (!info.id) {
    return ['unknown-user', 'users.info returned nothing for this id, so there is no '
      + 'recipient to reason about. A stale rota or a hand-typed id lands here'];
  }
  const who = String(info.id);
  if (info.deleted) {
    return ['deactivated', `${who} is deactivated. users.info still returns a name and `
      + 'a profile, so a stale rota keeps aiming at them; the message can never arrive '
      + 'and retrying spends rate limit'];
  }
  if (info.is_bot || info.is_app_user) {
    return ['bot-recipient', `${who} is a bot or app user, which has no client and `
      + 'renders nothing. An ephemeral to it is a call that cannot fail and cannot '
      + 'be seen'];
  }
  if (member === null || member === undefined) {
    return ['membership-unknown', 'the membership of this channel could not be read in '
      + 'full. On a private channel that is usually a missing groups:read, and guessing '
      + 'here would reroute a working message into a DM'];
  }
  if (!member) {
    let detail = `${who} is not in this channel, so the ephemeral has no view to render `
      + 'into. Slack answers user_not_in_channel, or takes the call and shows nobody '
      + 'anything';
    if (info.is_ultra_restricted) {
      detail += '. They are a single-channel guest, so they cannot be added to another '
        + 'channel either';
    }
    return ['not-member', detail];
  }
  return ['member', `${who} is in this channel and an ephemeral will render for them`];
}

/** The one action each verdict deserves. Pure. */
export function fallbackPlan(verdict) {
  const table = {
    member: ['send-ephemeral', 'the recipient can see the channel; an ephemeral is fine '
      + 'for a transient acknowledgement'],
    'not-member': ['open-dm', 'conversations.open then chat.postMessage; do not add '
      + 'somebody to a channel so they can see a message that lasts seconds and is '
      + 'visible to nobody else'],
    deactivated: ['skip', 'remove the account from the rota rather than from the queue; '
      + 'no fallback reaches a deactivated user'],
    'bot-recipient': ['skip', 'nothing renders for an app. If this is an integration '
      + 'talking to another integration, it needs an event or a real message, not an '
      + 'ephemeral'],
    'unknown-user': ['resolve-first', 'resolve the id before sending anything. '
      + 'users.lookupByEmail or a fresh users.list is the fix, not a retry'],
    'membership-unknown': ['resolve-first', 'add the scope that lets the token read this '
      + "channel's membership; this is a credential change, not a send-path one"],
  };
  return table[verdict] ?? ['resolve-first', `no rule for ${verdict}, so decide it by `
    + 'hand rather than defaulting to send'];
}

/** Is this payload one an ephemeral can carry? Pure. */
export function ephemeralFitness(text, blocks = null) {
  const body = String(text ?? '').trim();
  const rows = Array.isArray(blocks) ? blocks : [];
  const types = new Set(rows.filter((b) => b && typeof b === 'object')
    .map((b) => String(b.type ?? '')));
  if (!body && !rows.length) {
    return ['empty', 'no text and no blocks, so there is nothing to render and nothing '
      + 'to diagnose'];
  }
  const returning = [...types].filter((t) => RETURNING_BLOCKS.has(t)).sort();
  if (returning.length) {
    return ['interactive', `carries ${returning.join(', ')}. An ephemeral cannot be `
      + 'updated once the session ends and is not in history, so the click arrives with '
      + 'nothing left to replace and the reader cannot get back to it'];
  }
  const keeping = [...types].filter((t) => KEEPING_BLOCKS.has(t)).sort();
  if (keeping.length) {
    return ['durable', `carries ${keeping.join(', ')}, which the reader will want again. `
      + 'An ephemeral is gone at the next client reload and leaves no trace in history'];
  }
  if (body.length > ACK_CHARS || rows.length > 3) {
    return ['durable', `${body.length} characters across ${rows.length} block(s) is more `
      + 'than an acknowledgement, and none of it survives a reload'];
  }
  return ['transient-ack', 'short enough to be an acknowledgement, which is what an '
    + 'ephemeral is for'];
}

/** user:channel, in either order of the two id prefixes. Pure. */
export function parsePair(text) {
  const parts = String(text ?? '').split(':');
  if (parts.length !== 2) return ['', ''];
  const a = parts[0].trim();
  const b = parts[1].trim();
  return (a.toUpperCase().startsWith('C') || a.toUpperCase().startsWith('G'))
    ? [b, a] : [a, b];
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

async function readMembers(headers, channel, pageSize = 200) {
  const pages = [];
  let cursor = '';
  for (;;) {
    const params = { channel, limit: String(pageSize) };
    if (cursor) params.cursor = cursor;
    const qs = new URLSearchParams(params).toString();
    const page = await (await fetch(`${API}conversations.members?${qs}`, { headers }))
      .json();
    pages.push(page);
    if (page.ok !== true) return pages;
    cursor = String((page.response_metadata ?? {}).next_cursor ?? '').trim();
    if (!cursor) return pages;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const payload = arg(args, '--payload', '');
  const pairs = argAll(args, '--pair');
  let findings = 0;

  if (payload) {
    const raw = JSON.parse(await readFile(payload, 'utf8'));
    const [verdict, detail] = ephemeralFitness(raw.text, raw.blocks);
    const line = `fitness    ${verdict.padEnd(14)} ${detail}`;
    if (verdict === 'transient-ack') console.log(line); else console.warn(line);
    if (verdict === 'interactive' || verdict === 'durable') findings += 1;
  }

  if (!pairs.length) {
    if (payload) { if (findings) process.exitCode = 1; return; }
    console.error('pass at least one --pair USER:CHANNEL, or --payload FILE');
    process.exitCode = 2;
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}, or pass --payload alone to judge a message with `
      + 'no token');
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const membersByChannel = new Map();
  const users = new Map();
  for (const pair of pairs) {
    const [user, channel] = parsePair(pair);
    if (!user || !channel) {
      console.warn(`pair       unusable       ${pair} is not USER:CHANNEL`);
      continue;
    }
    if (!membersByChannel.has(channel)) {
      const pages = await readMembers(headers, channel);
      const found = memberLookup(pages);
      membersByChannel.set(channel, found);
      if (found === null) {
        console.warn(`members    unavailable    ${channel}: `
          + `${pages.length ? pages[pages.length - 1].error : 'no answer'}`);
      } else {
        console.log(`members    ${channel}: ${found.size} member(s) read across `
          + `${pages.length} page(s)`);
      }
    }
    if (!users.has(user)) {
      const qs = new URLSearchParams({ user }).toString();
      const body = await (await fetch(`${API}users.info?${qs}`, { headers })).json();
      users.set(user, body.ok === true ? (body.user ?? {}) : {});
    }

    const known = membersByChannel.get(channel);
    const member = known === null ? null : known.has(user);
    const [verdict, detail] = recipientVerdict(users.get(user), member);
    const [action, why] = fallbackPlan(verdict);
    if (verdict === 'member') {
      console.log(`recipient  ${verdict.padEnd(14)} ${user} in ${channel}  ${detail}`);
      continue;
    }
    findings += 1;
    console.warn(`recipient  ${verdict.padEnd(14)} ${user} in ${channel}  ${detail}`);
    console.warn(`  action:  ${action.padEnd(14)} ${why}`);
  }

  if (findings) {
    console.warn('  repair: check membership before the send and fall back to a DM; an '
      + 'ok with a message_ts is not evidence anybody saw anything');
    console.warn('  repair: keep ephemerals for transient acknowledgements and put '
      + 'anything the reader needs twice in a DM or a real message');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          every recipient can see the channel they are '
      + 'being drawn into');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions guard the two mistakes that would make this script actively harmful. A membership read that lost a page must come back <code>membership-unknown</code> and never <code>not-member</code>, because the second one reroutes a working message into somebody's DMs on the strength of an answer the script did not have. And a permanent condition must win over a routing one: a deactivated account that is also not in the channel has to report as <code>deactivated</code> with the action <code>skip</code>, since a fallback DM to a deleted user is a retry loop with a nice name.",
"test_py_file": "test_slack_ephemeral_recipient.py",
"test_py": '''from slack_ephemeral_recipient import (ephemeral_fitness, fallback_plan, member_lookup,
                                       parse_pair, recipient_verdict)

ACTIVE = {"id": "U7REVIEWR", "name": "dana", "deleted": False, "is_bot": False}


def page(members, cursor=""):
    return {"ok": True, "members": members,
            "response_metadata": {"next_cursor": cursor}}


def test_pages_fold_into_one_membership_set():
    found = member_lookup([page(["U1", "U2"], "c"), page(["U3"])])
    assert found == {"U1", "U2", "U3"}


def test_a_failed_page_gives_up_rather_than_returning_a_short_set():
    assert member_lookup([page(["U1"], "c"), {"ok": False, "error": "ratelimited"}]) \\
        is None
    assert member_lookup([{"ok": True}]) is None
    assert member_lookup([]) is None
    assert member_lookup(None) is None


def test_a_member_can_be_shown_an_ephemeral():
    verdict, detail = recipient_verdict(ACTIVE, True)
    assert verdict == "member"
    assert fallback_plan(verdict)[0] == "send-ephemeral"


def test_a_non_member_has_no_view_to_render_into():
    verdict, detail = recipient_verdict(ACTIVE, False)
    assert verdict == "not-member"
    assert "user_not_in_channel" in detail
    assert fallback_plan(verdict)[0] == "open-dm"


def test_the_fallback_is_a_dm_and_never_an_invitation():
    action, why = fallback_plan("not-member")
    assert action == "open-dm"
    assert "conversations.open" in why
    assert "do not add" in why


def test_a_deactivated_recipient_beats_the_membership_question():
    verdict, detail = recipient_verdict({"id": "U0LEFTFEB", "deleted": True}, False)
    assert verdict == "deactivated"
    assert fallback_plan(verdict)[0] == "skip"
    assert "rate limit" in detail


def test_a_bot_recipient_renders_nothing_and_is_skipped():
    verdict, _ = recipient_verdict({"id": "U0BOT", "is_bot": True}, True)
    assert verdict == "bot-recipient"
    assert fallback_plan(verdict)[0] == "skip"
    assert recipient_verdict({"id": "U0APP", "is_app_user": True}, True)[0] \\
        == "bot-recipient"


def test_an_unreadable_membership_is_never_reported_as_not_member():
    verdict, detail = recipient_verdict(ACTIVE, None)
    assert verdict == "membership-unknown"
    assert "groups:read" in detail
    assert fallback_plan(verdict)[0] == "resolve-first"


def test_an_unresolvable_user_is_resolved_before_anything_is_sent():
    assert recipient_verdict({}, True)[0] == "unknown-user"
    assert recipient_verdict(None, True)[0] == "unknown-user"
    assert fallback_plan("unknown-user")[0] == "resolve-first"


def test_a_single_channel_guest_is_told_why_the_dm_is_the_only_route():
    guest = dict(ACTIVE, is_ultra_restricted=True)
    verdict, detail = recipient_verdict(guest, False)
    assert verdict == "not-member"
    assert "single-channel guest" in detail


def test_an_unknown_verdict_never_defaults_to_sending():
    assert fallback_plan("something-new")[0] == "resolve-first"


def test_a_short_acknowledgement_is_what_an_ephemeral_is_for():
    verdict, detail = ephemeral_fitness("Got it, working on that now")
    assert verdict == "transient-ack"
    assert "acknowledgement" in detail


def test_a_payload_with_a_button_is_using_the_wrong_primitive():
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Approve?"}},
              {"type": "actions", "elements": [{"type": "button"}]}]
    verdict, detail = ephemeral_fitness("Approve?", blocks)
    assert verdict == "interactive"
    assert "nothing left to replace" in detail


def test_an_input_block_counts_the_same_way_a_button_does():
    assert ephemeral_fitness("x", [{"type": "input"}])[0] == "interactive"


def test_content_the_reader_will_want_again_is_durable():
    assert ephemeral_fitness("here", [{"type": "file"}])[0] == "durable"
    assert ephemeral_fitness("x" * 400)[0] == "durable"
    assert ephemeral_fitness("x", [{"type": "divider"}] * 4)[0] == "durable"


def test_an_empty_payload_is_named_rather_than_passed():
    assert ephemeral_fitness("", None)[0] == "empty"
    assert ephemeral_fitness(None, [])[0] == "empty"


def test_a_pair_parses_in_either_order():
    assert parse_pair("U7REVIEWR:C024BE91L") == ("U7REVIEWR", "C024BE91L")
    assert parse_pair("C024BE91L:U7REVIEWR") == ("U7REVIEWR", "C024BE91L")
    assert parse_pair("G01PRIVATE:U7REVIEWR") == ("U7REVIEWR", "G01PRIVATE")
    assert parse_pair("nonsense") == ("", "")
''',
"test_js_file": "slack-ephemeral-recipient.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ephemeralFitness, fallbackPlan, memberLookup, parsePair, recipientVerdict,
} from './slack-ephemeral-recipient.mjs';

const ACTIVE = { id: 'U7REVIEWR', name: 'dana', deleted: false, is_bot: false };

const page = (members, cursor = '') => ({ ok: true, members,
  response_metadata: { next_cursor: cursor } });

test('pages fold into one membership set', () => {
  const found = memberLookup([page(['U1', 'U2'], 'c'), page(['U3'])]);
  assert.deepEqual([...found].sort(), ['U1', 'U2', 'U3']);
});

test('a failed page gives up rather than returning a short set', () => {
  assert.equal(memberLookup([page(['U1'], 'c'), { ok: false, error: 'ratelimited' }]),
    null);
  assert.equal(memberLookup([{ ok: true }]), null);
  assert.equal(memberLookup([]), null);
  assert.equal(memberLookup(null), null);
});

test('a member can be shown an ephemeral', () => {
  assert.equal(recipientVerdict(ACTIVE, true)[0], 'member');
  assert.equal(fallbackPlan('member')[0], 'send-ephemeral');
});

test('a non member has no view to render into', () => {
  const [verdict, detail] = recipientVerdict(ACTIVE, false);
  assert.equal(verdict, 'not-member');
  assert.match(detail, /user_not_in_channel/);
  assert.equal(fallbackPlan(verdict)[0], 'open-dm');
});

test('the fallback is a DM and never an invitation', () => {
  const [action, why] = fallbackPlan('not-member');
  assert.equal(action, 'open-dm');
  assert.match(why, /conversations\\.open/);
  assert.match(why, /do not add/);
});

test('a deactivated recipient beats the membership question', () => {
  const [verdict, detail] = recipientVerdict({ id: 'U0LEFTFEB', deleted: true }, false);
  assert.equal(verdict, 'deactivated');
  assert.equal(fallbackPlan(verdict)[0], 'skip');
  assert.match(detail, /rate limit/);
});

test('a bot recipient renders nothing and is skipped', () => {
  assert.equal(recipientVerdict({ id: 'U0BOT', is_bot: true }, true)[0], 'bot-recipient');
  assert.equal(recipientVerdict({ id: 'U0APP', is_app_user: true }, true)[0],
    'bot-recipient');
  assert.equal(fallbackPlan('bot-recipient')[0], 'skip');
});

test('an unreadable membership is never reported as not-member', () => {
  const [verdict, detail] = recipientVerdict(ACTIVE, null);
  assert.equal(verdict, 'membership-unknown');
  assert.match(detail, /groups:read/);
  assert.equal(fallbackPlan(verdict)[0], 'resolve-first');
});

test('an unresolvable user is resolved before anything is sent', () => {
  assert.equal(recipientVerdict({}, true)[0], 'unknown-user');
  assert.equal(recipientVerdict(null, true)[0], 'unknown-user');
  assert.equal(fallbackPlan('unknown-user')[0], 'resolve-first');
});

test('a single channel guest is told why the DM is the only route', () => {
  const guest = { ...ACTIVE, is_ultra_restricted: true };
  const [verdict, detail] = recipientVerdict(guest, false);
  assert.equal(verdict, 'not-member');
  assert.match(detail, /single-channel guest/);
});

test('an unknown verdict never defaults to sending', () => {
  assert.equal(fallbackPlan('something-new')[0], 'resolve-first');
});

test('a short acknowledgement is what an ephemeral is for', () => {
  const [verdict, detail] = ephemeralFitness('Got it, working on that now');
  assert.equal(verdict, 'transient-ack');
  assert.match(detail, /acknowledgement/);
});

test('a payload with a button is using the wrong primitive', () => {
  const blocks = [{ type: 'section', text: { type: 'mrkdwn', text: 'Approve?' } },
    { type: 'actions', elements: [{ type: 'button' }] }];
  const [verdict, detail] = ephemeralFitness('Approve?', blocks);
  assert.equal(verdict, 'interactive');
  assert.match(detail, /nothing left to replace/);
});

test('an input block counts the same way a button does', () => {
  assert.equal(ephemeralFitness('x', [{ type: 'input' }])[0], 'interactive');
});

test('content the reader will want again is durable', () => {
  assert.equal(ephemeralFitness('here', [{ type: 'file' }])[0], 'durable');
  assert.equal(ephemeralFitness('x'.repeat(400))[0], 'durable');
  assert.equal(ephemeralFitness('x', Array.from({ length: 4 },
    () => ({ type: 'divider' })))[0], 'durable');
});

test('an empty payload is named rather than passed', () => {
  assert.equal(ephemeralFitness('', null)[0], 'empty');
  assert.equal(ephemeralFitness(null, [])[0], 'empty');
});

test('a pair parses in either order', () => {
  assert.deepEqual(parsePair('U7REVIEWR:C024BE91L'), ['U7REVIEWR', 'C024BE91L']);
  assert.deepEqual(parsePair('C024BE91L:U7REVIEWR'), ['U7REVIEWR', 'C024BE91L']);
  assert.deepEqual(parsePair('G01PRIVATE:U7REVIEWR'), ['U7REVIEWR', 'G01PRIVATE']);
  assert.deepEqual(parsePair('nonsense'), ['', '']);
});
''',
"faq": [
 ("chat.postEphemeral returned ok with a message_ts. How can the user have seen nothing?",
  "Because an ephemeral is not stored, so that timestamp does not refer to a message anywhere. It identifies a rendering that was attempted in one person's view of one channel. If they had no view of that channel, the attempt had nowhere to land. This is the one place in the Slack API where a timestamp comes back for something that will never exist, and code that logs it as a delivery receipt is logging a number about nothing."),
 ("Should I just add the user to the channel before sending?",
  "Almost never. Joining a channel is permanent, visible to everyone already in it, and changes what that person sees from then on, all so they can be shown a string that lasts a few seconds. Open a DM instead. The one time an invitation is right is when membership is the actual goal and the ephemeral was only how you noticed it was missing."),
 ("Why can I not find the ephemeral in conversations.history afterwards?",
  "Because it was never written there. Ephemerals are absent from history by design, along with search, exports and the mobile notification path. If a team is trying to reconstruct what a user was shown, that absence is not a hole in your logging; it is the strongest argument available for moving the content into a real message."),
 ("Can I update or delete an ephemeral after I send it?",
  "Not after the session. There is no chat.update path for one, and once the client reloads it is gone whether you wanted it gone or not. This is why a payload carrying a button is the shape this note flags hardest: the click arrives, your handler wants to replace the message with a result, and the message it would replace no longer exists in any form."),
 ("Is this the same as the bot not being in the channel?",
  "No, and keeping them apart is most of the value here. That one is about the app's own membership, produces not_in_channel, and is fixed by having the bot join. This one is about the recipient's membership, produces user_not_in_channel or a silent nothing, and is fixed in the send path by falling back to a DM. Both can be true at once, which is exactly why the script only reports one of them."),
],
"related": [
 ("/slack/bot-not-in-channel/", "the same word about the other party's membership"),
 ("/slack/dm-never-opened/", "the fallback this note recommends, and how it fails"),
 ("/slack/private-channel-invisible/", "why the membership read came back empty"),
],
"citations": [CITE_EPHEMERAL, CITE_CONV_MEMBERS, CITE_USERS_INFO, CITE_CONV_OPEN],
})

GUIDES.append({
"slug": "scheduled-message-in-past",
"title": "time_in_past: the scheduled send is behind the clock",
"description": "post_at is Unix seconds, in the future, and within 120 days. Audit the queue for millisecond values, timezone offsets and sends with no margin at all.",
"h1": "time_in_past: the scheduled send is behind the clock",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack chat.scheduleMessage time_in_past",
             "slack scheduled message invalid_time",
             "slack time_too_far 120 days",
             "slack post_at milliseconds seconds",
             "slack scheduledMessages.list audit"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a token in the chat:write family to list the queue, or no token at all to check a computed value",
"lead": "The digest is scheduled for nine in the morning. Most days it goes out. Some days the scheduler logs <code>{\"ok\": false, \"error\": \"time_in_past\"}</code> and there is no digest, and nobody notices until somebody asks where Tuesday went.</p><p>Nothing is intermittent about the code. <code>post_at</code> is a Unix timestamp in <strong>seconds</strong>, it must still be in the future when Slack processes the call, and it must be inside 120 days. Every way of getting it wrong is arithmetic: milliseconds where seconds were wanted, a local wall clock treated as UTC, or a target so close to now that the queue eats the difference before the request lands.",
"short_answer": """<p><code>chat.scheduleMessage</code> takes <code>post_at</code> as whole Unix <strong>seconds</strong>. Slack refuses it with <code>time_in_past</code> if that moment has already passed by the time the request is processed, with <code>invalid_time</code> if the value is not a usable timestamp, and with <code>time_too_far</code> if it is more than <strong>120 days</strong> ahead.</p>
<p>Four causes cover almost all of it. <code>Date.now()</code> returns <em>milliseconds</em>, so passing it directly produces a date tens of thousands of years out, and dividing it carelessly produces one in the past. Timezone arithmetic that builds a local wall-clock value and hands it over as if it were UTC is off by a whole number of hours, which is why this fails for some of your users and not others. Scheduling <em>now plus a few seconds</em> loses to queueing latency. And a rota that computes dates a year ahead sails past the 120-day horizon without anything local complaining.</p>
<p>The queue itself is readable. <code>chat.scheduledMessages.list</code> returns every pending send with its <code>id</code>, <code>channel_id</code>, <code>post_at</code> and <code>date_created</code>, which is enough to find the values that will never fire and the ones that only fired because they got lucky. Listing is a read; cancelling anything you find is a write, and this script prints that rather than doing it.</p>""",
"problem": """<p>The reason this is filed as flaky rather than as broken is that most of these bugs only fail near a boundary. A job that schedules <em>five minutes from now</em> succeeds every time the queue is warm and fails on the mornings the worker cold-starts, because Slack evaluates <code>post_at</code> when it processes the request rather than when you computed it. Nothing in the code distinguishes the good days from the bad ones, so it gets a retry wrapped around it and the retry recomputes the same too-close value.</p>
<p>The unit bug is the loudest and the easiest to miss in review. <code>Date.now()</code> is milliseconds and <code>time.time()</code> is float seconds, and the two get mixed anywhere a timestamp crosses a language boundary. Passing milliseconds gives a moment roughly fifty thousand years from now, which Slack rejects as too far. The half-fix is worse: someone divides by a thousand somewhere else in the chain, the value gets divided twice, and now it is 1970 plus a few hundred thousand seconds, which is firmly in the past. Same variable, two opposite errors, both reported as a scheduling failure.</p>
<p>Timezones fail with a signature you can actually recognise. Code that builds nine in the morning as a local datetime and then takes its epoch as if it were UTC is wrong by exactly the offset, so the value is off by a whole number of hours: one or two for most of Europe, five to eight across the Americas, and thirty or forty five minutes for India, Nepal and the Chatham Islands. Every one of those is a clean multiple, which is what tells it apart from a value that is merely stale.</p>
<p>The horizon catches the opposite kind of code: careful, correct, and planning further ahead than the API allows. A quarterly reminder scheduled at the start of the year is beyond 120 days for three quarters of its entries, and the failures arrive as a batch of <code>time_too_far</code> that looks like an outage.</p>
<p>What all four share is that the number is wrong before the call is made, so all four are checkable without making the call. That is the entire argument for reading the queue rather than watching the error log: the error log tells you a send failed, and the queue tells you which of the pending ones is going to.</p>""",
"why": """<p><strong>The value is evaluated when Slack processes the request, not when you build it.</strong> This is why a margin matters and why <em>now plus five seconds</em> is not a schedule, it is a race. The script reports a value inside the margin as a finding even though it has not failed yet, because it is going to.</p>
<p><strong>Milliseconds are recognisable by digit count and nothing else needs to be inferred.</strong> A ten-digit value is seconds and a thirteen-digit one is milliseconds. That single comparison catches the most common cause outright and does not need a token, a network call, or any knowledge of what you intended.</p>
<p><strong>A whole number of hours is a timezone bug, and anything else is not.</strong> This is the finding that saves the most time, because a value that is off by exactly five hours has a completely different cause from one that is off by four minutes. Reporting only <em>the time is wrong</em> loses the one detail that names the bug.</p>
<p><strong>A value under a billion is a duration, not a timestamp.</strong> Passing <code>300</code> for <em>five minutes from now</em> is not an edge case, it is what happens when a delay and a deadline share a variable name. Slack reads it as 1970 plus five minutes, and the error is <code>time_in_past</code> for a value nobody thought of as a time at all.</p>
<p><strong>The 120-day horizon is a design constraint rather than a bug.</strong> If your calendar reaches further than that, the answer is a durable store and a job that schedules as the horizon rolls forward, not a retry. The script names <code>too-far</code> separately so that this conclusion is reachable from the output.</p>
<p><strong>Listing is a read and cancelling is not.</strong> <code>chat.scheduledMessages.list</code> answers every question this note asks. Removing a bad entry from the queue changes your workspace, so the script prints the <code>id</code> and the method and leaves the decision with you, which is the same promise every other script in this section makes.</p>""",
"steps": [
 {"h": "Check the computed value before you check the queue",
  "body": """<p><code>--post-at 1755000000</code> needs no token at all. <code>post_at_verdict</code> compares the number against the clock and against the shape a Unix second has, and returns <code>milliseconds</code>, <code>duration-not-timestamp</code>, <code>message-ts</code>, <code>in-past</code>, <code>too-soon</code>, <code>too-far</code> or <code>plausible</code>.</p>"""},
 {"h": "Give the script what you meant, and let it name the timezone",
  "body": """<p><code>--intended 2026-09-01T09:00:00+00:00</code> turns the check into a comparison. <code>offset_smell</code> reports <code>whole-hour-offset</code> when the difference is a clean number of hours, which is a timezone conversion and not a rounding error, and <code>half-hour-offset</code> for the zones that are not on the hour.</p>"""},
 {"h": "Read the whole queue, following the cursor",
  "body": """<p><code>chat.scheduledMessages.list</code> pages. <code>queue_report</code> folds the pages into counts by verdict and names the nearest pending send, so the output answers <em>what is going to break</em> rather than <em>what broke</em>.</p>"""},
 {"h": "Treat the gap between date_created and post_at as its own signal",
  "body": """<p><code>creation_margin</code> looks at how long the scheduler gave itself. An entry created eight seconds before it is due did not fail, and the next one like it will. That is a different finding from <code>too-soon</code>, which is about the clock now, and the two are reported separately.</p>"""},
 {"h": "Separate too-far from every other finding",
  "body": """<p>Everything else on this list is a bug in the arithmetic. <code>too-far</code> is arithmetic that is entirely correct against an API that will not take it, and the repair is a job that schedules as the horizon rolls forward rather than a fix to the calculation.</p>"""},
 {"h": "Cancel the bad entries yourself",
  "body": """<p>The script prints each unusable entry's <code>id</code> and the method that removes it. It does not call it. A scheduled message is a pending change to your workspace, and this section's scripts do not make changes to your workspace even when the change is a deletion you asked for.</p>"""},
],
"verify": """<p>Run it against the pending queue. Every line names an entry, a cause and whether it can still fire.</p>
<pre><code class="language-bash">python3 slack_scheduled_in_past.py --queue
# queue      6 pending send(s) read across 1 page(s)
# entry      milliseconds   Q1298ABCD C024BE91L post_at=1756713600000  thirteen digits is
#                           Date.now(); Slack reads seconds and refuses this as too far
# entry      too-soon       Q1298ABCE C024BE91L post_at=1756713612  12s from now, and
#                           Slack evaluates post_at when it processes the call
# entry      too-far        Q1298ABCF C07J4K2QT post_at=1790000000  386 days out and the
#                           horizon is 120
# margin     tight-window   Q1298ABCE created 9s before it is due; the next one like this
#                           loses the race
# entry      plausible      Q1298ABCG C024BE91L post_at=1756800000
# verdict    3 of 6 pending send(s) will not fire
#   repair: compute post_at as whole seconds and assert post_at > now + 60 before sending
#   repair: do the arithmetic in UTC and convert only for display</code></pre>""",
"code_intro": "Four pure functions and one paginated read. <code>post_at_verdict</code> is the whole unit argument in one table and runs against a value you type on the command line. <code>offset_smell</code> is the function that earns the note, because a difference of exactly five hours and a difference of four minutes are two unrelated bugs and only one of them is about timezones. <code>creation_margin</code> reads the gap the scheduler gave itself, which is the leading indicator. <code>queue_report</code> folds the pages into an answer.",
"py_file": "slack_scheduled_in_past.py",
"py": '''"""Audit the pending scheduled sends for values that will never fire.

Read only. chat.scheduledMessages.list is a read and is the only method this
script calls; scheduling a message and cancelling one are both writes and
neither is here. When an entry is unusable the script prints its id and the
method that removes it, and leaves the call to you.
"""
import argparse
import datetime as dt
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_scheduled_in_past")

API = "https://slack.com/api/"

# Slack takes a schedule up to 120 days out and no further.
HORIZON_SECONDS = 120 * 86400
# Below this the value is not an absolute time at all: 1e9 seconds is 2001, and
# anything smaller is a duration somebody handed over as a deadline.
SMALLEST_PLAUSIBLE = 1_000_000_000
# Ten digits is seconds, thirteen is milliseconds, sixteen is microseconds.
MILLISECONDS = 1_000_000_000_000
MICROSECONDS = 1_000_000_000_000_000
DEFAULT_MARGIN = 60


def post_at_verdict(post_at, now, margin=DEFAULT_MARGIN, horizon=HORIZON_SECONDS):
    """Will Slack accept this post_at, and if not, which mistake was it? Pure.

    Returns (verdict, detail). The unit verdicts come before the clock verdicts
    because a value in milliseconds is not early or late, it is the wrong kind
    of number, and reporting it as too-far sends somebody to look at a horizon
    that has nothing to do with it.
    """
    if post_at is None or post_at == "":
        return ("missing", "no post_at. chat.scheduleMessage has no default and will "
                           "not treat an absent value as send now")
    try:
        value = float(post_at)
    except (TypeError, ValueError):
        return ("not-a-number", "%r is not a number. An ISO 8601 string is the usual "
                                "cause; post_at is Unix seconds, not a formatted date"
                % (post_at,))
    if value != int(value):
        return ("message-ts", "%s has a fractional part, which is the shape of a message "
                              "ts rather than of a post_at. post_at is whole seconds"
                % post_at)
    value = int(value)
    if value >= MICROSECONDS:
        return ("microseconds", "%d digits. This is microseconds, which is what a "
                                "database timestamp column hands back on some drivers"
                % len(str(abs(value))))
    if value >= MILLISECONDS:
        return ("milliseconds", "%d digits, so this is milliseconds. Date.now() returns "
                                "milliseconds and Slack reads seconds, which puts this "
                                "roughly fifty thousand years out and gets it refused "
                                "as too far" % len(str(abs(value))))
    if value < SMALLEST_PLAUSIBLE:
        return ("duration-not-timestamp",
                "%d is not an absolute time. Slack reads it as 1970 plus %d seconds, "
                "which is what happens when a delay and a deadline share a variable name"
                % (value, value))
    delta = value - int(now)
    if delta <= 0:
        return ("in-past", "%d seconds behind the clock already. Slack evaluates post_at "
                           "when it processes the request, so a value computed a while "
                           "ago can be fine at build time and late on arrival"
                % abs(delta))
    if delta <= margin:
        return ("too-soon", "%ds from now, inside the %ds margin. Queueing latency, a "
                            "retry, or a cold worker will push this past the target "
                            "before Slack sees it" % (delta, margin))
    if delta > horizon:
        return ("too-far", "%d days out and the horizon is %d. The arithmetic is right "
                           "and the API will not take it, so this wants a job that "
                           "schedules as the horizon rolls forward"
                % (delta // 86400, horizon // 86400))
    return ("plausible", "%d days, %d hours out and inside every limit"
            % (delta // 86400, (delta % 86400) // 3600))


def offset_smell(post_at, intended_epoch, tolerance=90):
    """Is the difference a timezone conversion or something else? Pure.

    A value that is wrong by exactly five hours and a value that is wrong by
    four minutes have unrelated causes, and only the first one is about
    timezones. Reporting the size of the error without its shape loses the one
    detail that names the bug.
    """
    try:
        diff = int(float(post_at)) - int(float(intended_epoch))
    except (TypeError, ValueError):
        return ("uncomparable", "one of these is not a number, so there is nothing to "
                                "compare")
    size = abs(diff)
    direction = "ahead of" if diff > 0 else "behind"
    if size <= tolerance:
        return ("aligned", "within %ds of the moment you meant" % size)
    hours = round(size / 3600.0)
    if 1 <= hours <= 14 and abs(size - hours * 3600) <= tolerance:
        return ("whole-hour-offset",
                "exactly %d hour(s) %s the moment you meant. A clean multiple of an "
                "hour is a timezone conversion, not a rounding error: a local wall "
                "clock was handed over as if it were UTC" % (hours, direction))
    remainder = size % 3600
    if abs(remainder - 1800) <= tolerance or abs(remainder - 2700) <= tolerance:
        return ("half-hour-offset",
                "%ds %s the moment you meant, which lands on a 30 or 45 minute "
                "boundary. India, Nepal and the Chatham Islands are not on the hour, "
                "and this is what their users see" % (size, direction))
    return ("drifted", "%ds %s the moment you meant, and not a clean timezone offset. "
                       "This is a stale value or a clock problem rather than a "
                       "conversion" % (size, direction))


def creation_margin(post_at, date_created, margin=DEFAULT_MARGIN):
    """How much room did the scheduler give itself? Pure.

    Different from too-soon, which is about the clock now. This is about the
    gap the code chose, and it is the leading indicator: an entry created eight
    seconds before it was due did not fail, and the next one like it will.
    """
    if date_created in (None, "") or post_at in (None, ""):
        return ("unknown", "no date_created on this entry, so the gap the scheduler "
                           "gave itself cannot be read")
    try:
        gap = int(float(post_at)) - int(float(date_created))
    except (TypeError, ValueError):
        return ("unknown", "date_created or post_at is not a number")
    if gap <= 0:
        return ("created-after", "scheduled for %ds before it was created, which is a "
                                 "sign computation and not a scheduling one" % abs(gap))
    if gap < margin:
        return ("tight-window", "created %ds before it is due, inside the %ds margin. "
                                "This one got through and the next one like it loses "
                                "the race" % (gap, margin))
    return ("comfortable", "created %ds before it is due" % gap)


def queue_report(entries, now, margin=DEFAULT_MARGIN, horizon=HORIZON_SECONDS):
    """Fold the pending queue into counts and rows. Pure."""
    rows, counts = [], {}
    nearest = None
    for entry in entries or []:
        item = entry if isinstance(entry, dict) else {}
        post_at = item.get("post_at")
        verdict, detail = post_at_verdict(post_at, now, margin, horizon)
        gap_verdict, gap_detail = creation_margin(post_at, item.get("date_created"),
                                                  margin)
        counts[verdict] = counts.get(verdict, 0) + 1
        rows.append({"id": str(item.get("id") or "?"),
                     "channel": str(item.get("channel_id") or "?"),
                     "post_at": post_at, "verdict": verdict, "detail": detail,
                     "margin": gap_verdict, "margin_detail": gap_detail})
        try:
            seconds = int(float(post_at))
        except (TypeError, ValueError):
            seconds = None
        if seconds is not None and seconds > int(now):
            if nearest is None or seconds < nearest[1]:
                nearest = (str(item.get("id") or "?"), seconds)
    unusable = sum(n for verdict, n in counts.items() if verdict != "plausible")
    return {"total": len(rows), "unusable": unusable, "by_verdict": counts,
            "nearest": nearest, "rows": rows}


def read_queue(session, page_size=100):
    """Follow the cursor. Listing is a read; cancelling is not, and is not here."""
    pages, cursor = [], ""
    while True:
        params = {"limit": str(page_size)}
        if cursor:
            params["cursor"] = cursor
        page = session.get(API + "chat.scheduledMessages.list", timeout=30,
                           params=params).json()
        pages.append(page)
        if page.get("ok") is not True:
            return pages
        cursor = ((page.get("response_metadata") or {}).get("next_cursor") or "").strip()
        if not cursor:
            return pages


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--post-at", action="append", default=[],
                    help="a computed post_at to check with no token at all; repeatable")
    ap.add_argument("--intended", default="",
                    help="the moment you meant, ISO 8601, to name a timezone offset")
    ap.add_argument("--queue", action="store_true",
                    help="read the pending scheduled sends and audit every one")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the token")
    ap.add_argument("--margin", type=int, default=DEFAULT_MARGIN,
                    help="seconds of room a send should leave itself")
    args = ap.parse_args()

    now = time.time()
    findings = 0

    intended = None
    if args.intended:
        try:
            intended = dt.datetime.fromisoformat(args.intended).timestamp()
        except ValueError:
            log.warning("intended   unusable       %s is not ISO 8601", args.intended)

    for raw in args.post_at:
        verdict, detail = post_at_verdict(raw, now, args.margin)
        (log.info if verdict == "plausible" else log.warning)(
            "value      %-22s post_at=%s  %s", verdict, raw, detail)
        if verdict != "plausible":
            findings += 1
        if intended is not None:
            smell, why = offset_smell(raw, intended)
            (log.info if smell == "aligned" else log.warning)(
                "offset     %-22s %s", smell, why)
            if smell != "aligned":
                findings += 1

    if not args.queue:
        if args.post_at:
            return 1 if findings else 0
        log.error("pass --post-at VALUE to check a number, or --queue to read the queue")
        return 2

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s, or use --post-at alone to check a value with no token",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    pages = read_queue(s)
    if pages and pages[-1].get("ok") is not True:
        log.error("queue      unavailable    %s. Listing the queue needs a token in the "
                  "chat:write family, which is a write scope used here only to read",
                  pages[-1].get("error"))
        return 2

    entries = [e for page in pages for e in (page.get("scheduled_messages") or [])]
    log.info("queue      %d pending send(s) read across %d page(s)", len(entries),
             len(pages))
    report = queue_report(entries, now, args.margin)
    for row in report["rows"]:
        (log.info if row["verdict"] == "plausible" else log.warning)(
            "entry      %-22s %s %s post_at=%s  %s", row["verdict"], row["id"],
            row["channel"], row["post_at"], row["detail"])
        if row["margin"] in ("tight-window", "created-after"):
            log.warning("margin     %-22s %s %s", row["margin"], row["id"],
                        row["margin_detail"])
    if report["nearest"]:
        log.info("nearest    %s fires next", report["nearest"][0])

    findings += report["unusable"]
    if findings:
        log.warning("verdict    %d of %d pending send(s) will not fire",
                    report["unusable"], report["total"])
        log.warning("  repair: compute post_at as whole seconds and assert "
                    "post_at > now + %d before sending", args.margin)
        log.warning("  repair: do the arithmetic in UTC and convert only for display; a "
                    "clean multiple of an hour is always a conversion")
        log.warning("  repair: for anything beyond 120 days, keep the schedule in your "
                    "own store and enqueue as the horizon rolls forward")
        log.warning("  repair: remove the entries named above yourself with "
                    "chat.deleteScheduledMessage; this script does not write")
        return 1
    log.info("verdict    clean          every pending send is inside every limit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-scheduled-in-past.mjs",
"js": '''/**
 * Audit the pending scheduled sends for values that will never fire.
 *
 * Read only. chat.scheduledMessages.list is a read and is the only method this
 * script calls; scheduling a message and cancelling one are both writes and
 * neither is here. When an entry is unusable the script prints its id and the
 * method that removes it, and leaves the call to you.
 */

const API = 'https://slack.com/api/';

// Slack takes a schedule up to 120 days out and no further.
const HORIZON_SECONDS = 120 * 86400;
// Below this the value is not an absolute time at all: 1e9 seconds is 2001.
const SMALLEST_PLAUSIBLE = 1_000_000_000;
const MILLISECONDS = 1_000_000_000_000;
const MICROSECONDS = 1_000_000_000_000_000;
const DEFAULT_MARGIN = 60;

/**
 * Will Slack accept this post_at, and if not, which mistake was it? Pure.
 * The unit verdicts come before the clock verdicts on purpose.
 */
export function postAtVerdict(postAt, now, margin = DEFAULT_MARGIN,
  horizon = HORIZON_SECONDS) {
  if (postAt === null || postAt === undefined || postAt === '') {
    return ['missing', 'no post_at. chat.scheduleMessage has no default and will not '
      + 'treat an absent value as send now'];
  }
  const value = Number(postAt);
  if (!Number.isFinite(value)) {
    return ['not-a-number', `${postAt} is not a number. An ISO 8601 string is the usual `
      + 'cause; post_at is Unix seconds, not a formatted date'];
  }
  if (!Number.isInteger(value)) {
    return ['message-ts', `${postAt} has a fractional part, which is the shape of a `
      + 'message ts rather than of a post_at. post_at is whole seconds'];
  }
  const digits = String(Math.abs(value)).length;
  if (value >= MICROSECONDS) {
    return ['microseconds', `${digits} digits. This is microseconds, which is what a `
      + 'database timestamp column hands back on some drivers'];
  }
  if (value >= MILLISECONDS) {
    return ['milliseconds', `${digits} digits, so this is milliseconds. Date.now() `
      + 'returns milliseconds and Slack reads seconds, which puts this roughly fifty '
      + 'thousand years out and gets it refused as too far'];
  }
  if (value < SMALLEST_PLAUSIBLE) {
    return ['duration-not-timestamp', `${value} is not an absolute time. Slack reads it `
      + `as 1970 plus ${value} seconds, which is what happens when a delay and a `
      + 'deadline share a variable name'];
  }
  const delta = value - Math.trunc(now);
  if (delta <= 0) {
    return ['in-past', `${Math.abs(delta)} seconds behind the clock already. Slack `
      + 'evaluates post_at when it processes the request, so a value computed a while '
      + 'ago can be fine at build time and late on arrival'];
  }
  if (delta <= margin) {
    return ['too-soon', `${delta}s from now, inside the ${margin}s margin. Queueing `
      + 'latency, a retry, or a cold worker will push this past the target before '
      + 'Slack sees it'];
  }
  if (delta > horizon) {
    return ['too-far', `${Math.floor(delta / 86400)} days out and the horizon is `
      + `${Math.floor(horizon / 86400)}. The arithmetic is right and the API will not `
      + 'take it, so this wants a job that schedules as the horizon rolls forward'];
  }
  return ['plausible', `${Math.floor(delta / 86400)} days, `
    + `${Math.floor((delta % 86400) / 3600)} hours out and inside every limit`];
}

/**
 * Is the difference a timezone conversion or something else? Pure.
 * A clean multiple of an hour is a conversion; four minutes is not.
 */
export function offsetSmell(postAt, intendedEpoch, tolerance = 90) {
  const a = Number(postAt);
  const b = Number(intendedEpoch);
  if (!Number.isFinite(a) || !Number.isFinite(b)) {
    return ['uncomparable', 'one of these is not a number, so there is nothing to '
      + 'compare'];
  }
  const diff = Math.trunc(a) - Math.trunc(b);
  const size = Math.abs(diff);
  const direction = diff > 0 ? 'ahead of' : 'behind';
  if (size <= tolerance) return ['aligned', `within ${size}s of the moment you meant`];
  const hours = Math.round(size / 3600);
  if (hours >= 1 && hours <= 14 && Math.abs(size - hours * 3600) <= tolerance) {
    return ['whole-hour-offset', `exactly ${hours} hour(s) ${direction} the moment you `
      + 'meant. A clean multiple of an hour is a timezone conversion, not a rounding '
      + 'error: a local wall clock was handed over as if it were UTC'];
  }
  const remainder = size % 3600;
  if (Math.abs(remainder - 1800) <= tolerance || Math.abs(remainder - 2700) <= tolerance) {
    return ['half-hour-offset', `${size}s ${direction} the moment you meant, which lands `
      + 'on a 30 or 45 minute boundary. India, Nepal and the Chatham Islands are not on '
      + 'the hour, and this is what their users see'];
  }
  return ['drifted', `${size}s ${direction} the moment you meant, and not a clean `
    + 'timezone offset. This is a stale value or a clock problem rather than a '
    + 'conversion'];
}

/** How much room did the scheduler give itself? Pure. */
export function creationMargin(postAt, dateCreated, margin = DEFAULT_MARGIN) {
  if (dateCreated === null || dateCreated === undefined || dateCreated === ''
      || postAt === null || postAt === undefined || postAt === '') {
    return ['unknown', 'no date_created on this entry, so the gap the scheduler gave '
      + 'itself cannot be read'];
  }
  const a = Number(postAt);
  const b = Number(dateCreated);
  if (!Number.isFinite(a) || !Number.isFinite(b)) {
    return ['unknown', 'date_created or post_at is not a number'];
  }
  const gap = Math.trunc(a) - Math.trunc(b);
  if (gap <= 0) {
    return ['created-after', `scheduled for ${Math.abs(gap)}s before it was created, `
      + 'which is a sign computation and not a scheduling one'];
  }
  if (gap < margin) {
    return ['tight-window', `created ${gap}s before it is due, inside the ${margin}s `
      + 'margin. This one got through and the next one like it loses the race'];
  }
  return ['comfortable', `created ${gap}s before it is due`];
}

/** Fold the pending queue into counts and rows. Pure. */
export function queueReport(entries, now, margin = DEFAULT_MARGIN,
  horizon = HORIZON_SECONDS) {
  const rows = [];
  const counts = new Map();
  let nearest = null;
  for (const entry of entries ?? []) {
    const item = (entry && typeof entry === 'object') ? entry : {};
    const postAt = item.post_at;
    const [verdict, detail] = postAtVerdict(postAt, now, margin, horizon);
    const [marginVerdict, marginDetail] = creationMargin(postAt, item.date_created,
      margin);
    counts.set(verdict, (counts.get(verdict) ?? 0) + 1);
    rows.push({ id: String(item.id ?? '?'), channel: String(item.channel_id ?? '?'),
      postAt, verdict, detail, margin: marginVerdict, marginDetail });
    const seconds = Number(postAt);
    if (Number.isFinite(seconds) && seconds > Math.trunc(now)
        && (nearest === null || seconds < nearest[1])) {
      nearest = [String(item.id ?? '?'), Math.trunc(seconds)];
    }
  }
  let unusable = 0;
  for (const [verdict, n] of counts) if (verdict !== 'plausible') unusable += n;
  return { total: rows.length, unusable, byVerdict: counts, nearest, rows };
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

async function readQueue(headers, pageSize = 100) {
  const pages = [];
  let cursor = '';
  for (;;) {
    const params = { limit: String(pageSize) };
    if (cursor) params.cursor = cursor;
    const qs = new URLSearchParams(params).toString();
    const page = await (await fetch(`${API}chat.scheduledMessages.list?${qs}`,
      { headers })).json();
    pages.push(page);
    if (page.ok !== true) return pages;
    cursor = String((page.response_metadata ?? {}).next_cursor ?? '').trim();
    if (!cursor) return pages;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const now = Date.now() / 1000;
  const margin = Number(arg(args, '--margin', String(DEFAULT_MARGIN)));
  const values = argAll(args, '--post-at');
  const wantQueue = args.includes('--queue');
  let findings = 0;

  let intended = null;
  const intendedText = arg(args, '--intended', '');
  if (intendedText) {
    const parsed = Date.parse(intendedText);
    if (Number.isNaN(parsed)) {
      console.warn(`intended   unusable       ${intendedText} is not ISO 8601`);
    } else {
      intended = parsed / 1000;
    }
  }

  for (const raw of values) {
    const [verdict, detail] = postAtVerdict(raw, now, margin);
    const line = `value      ${verdict.padEnd(22)} post_at=${raw}  ${detail}`;
    if (verdict === 'plausible') console.log(line);
    else { console.warn(line); findings += 1; }
    if (intended !== null) {
      const [smell, why] = offsetSmell(raw, intended);
      const offsetLine = `offset     ${smell.padEnd(22)} ${why}`;
      if (smell === 'aligned') console.log(offsetLine);
      else { console.warn(offsetLine); findings += 1; }
    }
  }

  if (!wantQueue) {
    if (values.length) { if (findings) process.exitCode = 1; return; }
    console.error('pass --post-at VALUE to check a number, or --queue to read the queue');
    process.exitCode = 2;
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}, or use --post-at alone to check a value with `
      + 'no token');
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const pages = await readQueue(headers);
  if (pages.length && pages[pages.length - 1].ok !== true) {
    console.error(`queue      unavailable    ${pages[pages.length - 1].error}. Listing `
      + 'the queue needs a token in the chat:write family, which is a write scope used '
      + 'here only to read');
    process.exitCode = 2;
    return;
  }

  const entries = pages.flatMap((p) => p.scheduled_messages ?? []);
  console.log(`queue      ${entries.length} pending send(s) read across `
    + `${pages.length} page(s)`);
  const report = queueReport(entries, now, margin);
  for (const row of report.rows) {
    const line = `entry      ${row.verdict.padEnd(22)} ${row.id} ${row.channel} `
      + `post_at=${row.postAt}  ${row.detail}`;
    if (row.verdict === 'plausible') console.log(line); else console.warn(line);
    if (row.margin === 'tight-window' || row.margin === 'created-after') {
      console.warn(`margin     ${row.margin.padEnd(22)} ${row.id} ${row.marginDetail}`);
    }
  }
  if (report.nearest) console.log(`nearest    ${report.nearest[0]} fires next`);

  findings += report.unusable;
  if (findings) {
    console.warn(`verdict    ${report.unusable} of ${report.total} pending send(s) `
      + 'will not fire');
    console.warn('  repair: compute post_at as whole seconds and assert post_at > now + '
      + `${margin} before sending`);
    console.warn('  repair: do the arithmetic in UTC and convert only for display; a '
      + 'clean multiple of an hour is always a conversion');
    console.warn('  repair: for anything beyond 120 days, keep the schedule in your own '
      + 'store and enqueue as the horizon rolls forward');
    console.warn('  repair: remove the entries named above yourself with '
      + 'chat.deleteScheduledMessage; this script does not write');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          every pending send is inside every limit');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin a fixed <code>now</code>, because a scheduling audit whose assertions depend on the clock is a test that fails on a slow morning. The ones that matter are the ordering: a value in milliseconds must report as <code>milliseconds</code> and never as <code>too-far</code>, even though it is also very far, since the horizon is not the bug. And <code>offset_smell</code> has to split a clean five hours from an untidy four minutes, because those are two different investigations and the numbers are the only way to tell them apart.",
"test_py_file": "test_slack_scheduled_in_past.py",
"test_py": '''from slack_scheduled_in_past import (creation_margin, offset_smell, post_at_verdict,
                                     queue_report)

# Fixed so the assertions do not depend on the clock: 2025-08-12T12:00:00Z.
NOW = 1755000000


def test_a_sensible_future_value_is_plausible():
    verdict, detail = post_at_verdict(NOW + 86400, NOW)
    assert verdict == "plausible"
    assert "1 days" in detail


def test_milliseconds_are_named_by_their_digit_count():
    verdict, detail = post_at_verdict(NOW * 1000, NOW)
    assert verdict == "milliseconds"
    assert "13 digits" in detail
    assert "Date.now()" in detail


def test_milliseconds_beat_too_far_because_the_horizon_is_not_the_bug():
    assert post_at_verdict(NOW * 1000, NOW)[0] != "too-far"


def test_microseconds_have_their_own_verdict():
    assert post_at_verdict(NOW * 1000000, NOW)[0] == "microseconds"


def test_a_delay_passed_as_a_deadline_is_caught():
    verdict, detail = post_at_verdict(300, NOW)
    assert verdict == "duration-not-timestamp"
    assert "1970 plus 300 seconds" in detail


def test_a_value_already_behind_the_clock_is_in_past():
    verdict, detail = post_at_verdict(NOW - 5, NOW)
    assert verdict == "in-past"
    assert "when it processes the request" in detail
    assert post_at_verdict(NOW, NOW)[0] == "in-past"


def test_a_send_with_no_room_is_a_finding_before_it_fails():
    verdict, detail = post_at_verdict(NOW + 12, NOW)
    assert verdict == "too-soon"
    assert "cold worker" in detail


def test_the_margin_boundary_is_inclusive_and_the_next_second_is_fine():
    assert post_at_verdict(NOW + 60, NOW)[0] == "too-soon"
    assert post_at_verdict(NOW + 61, NOW)[0] == "plausible"


def test_past_the_horizon_is_separated_from_every_arithmetic_bug():
    verdict, detail = post_at_verdict(NOW + 121 * 86400, NOW)
    assert verdict == "too-far"
    assert "horizon rolls forward" in detail
    assert post_at_verdict(NOW + 119 * 86400, NOW)[0] == "plausible"


def test_a_message_ts_handed_over_as_a_post_at_is_recognised():
    verdict, detail = post_at_verdict("1755000000.000200", NOW)
    assert verdict == "message-ts"
    assert "whole seconds" in detail


def test_a_formatted_date_is_not_a_post_at():
    assert post_at_verdict("2026-09-01T09:00:00Z", NOW)[0] == "not-a-number"
    assert post_at_verdict(None, NOW)[0] == "missing"
    assert post_at_verdict("", NOW)[0] == "missing"


def test_a_clean_multiple_of_an_hour_is_named_as_a_timezone_bug():
    verdict, detail = offset_smell(NOW + 5 * 3600, NOW)
    assert verdict == "whole-hour-offset"
    assert "exactly 5 hour(s) ahead of" in detail
    assert "as if it were UTC" in detail


def test_the_offset_is_reported_in_both_directions():
    assert "behind" in offset_smell(NOW - 3600, NOW)[1]


def test_the_zones_that_are_not_on_the_hour_are_still_timezone_bugs():
    assert offset_smell(NOW + 5 * 3600 + 1800, NOW)[0] == "half-hour-offset"
    assert offset_smell(NOW + 5 * 3600 + 2700, NOW)[0] == "half-hour-offset"


def test_an_untidy_difference_is_not_blamed_on_timezones():
    verdict, detail = offset_smell(NOW + 240, NOW)
    assert verdict == "drifted"
    assert "not a clean timezone offset" in detail


def test_a_value_that_matches_what_you_meant_is_aligned():
    assert offset_smell(NOW + 10, NOW)[0] == "aligned"
    assert offset_smell("nine o'clock", NOW)[0] == "uncomparable"


def test_the_gap_the_scheduler_gave_itself_is_its_own_signal():
    verdict, detail = creation_margin(NOW + 9, NOW)
    assert verdict == "tight-window"
    assert "loses the race" in detail
    assert creation_margin(NOW + 3600, NOW)[0] == "comfortable"


def test_an_entry_due_before_it_was_created_is_a_sign_error():
    assert creation_margin(NOW - 10, NOW)[0] == "created-after"
    assert creation_margin(NOW + 60, None)[0] == "unknown"


def test_the_queue_report_counts_by_cause_and_names_the_next_to_fire():
    entries = [
        {"id": "Q1", "channel_id": "C1", "post_at": NOW * 1000, "date_created": NOW},
        {"id": "Q2", "channel_id": "C1", "post_at": NOW + 12, "date_created": NOW + 3},
        {"id": "Q3", "channel_id": "C2", "post_at": NOW + 86400, "date_created": NOW},
        {"id": "Q4", "channel_id": "C2", "post_at": NOW + 200 * 86400,
         "date_created": NOW},
    ]
    report = queue_report(entries, NOW)
    assert report["total"] == 4
    assert report["unusable"] == 3
    assert report["by_verdict"]["plausible"] == 1
    assert report["nearest"] == ("Q2", NOW + 12)
    assert report["rows"][1]["margin"] == "tight-window"


def test_an_empty_queue_is_not_a_finding():
    report = queue_report([], NOW)
    assert report["total"] == 0
    assert report["unusable"] == 0
    assert report["nearest"] is None
''',
"test_js_file": "slack-scheduled-in-past.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  creationMargin, offsetSmell, postAtVerdict, queueReport,
} from './slack-scheduled-in-past.mjs';

// Fixed so the assertions do not depend on the clock: 2025-08-12T12:00:00Z.
const NOW = 1755000000;

test('a sensible future value is plausible', () => {
  const [verdict, detail] = postAtVerdict(NOW + 86400, NOW);
  assert.equal(verdict, 'plausible');
  assert.match(detail, /1 days/);
});

test('milliseconds are named by their digit count', () => {
  const [verdict, detail] = postAtVerdict(NOW * 1000, NOW);
  assert.equal(verdict, 'milliseconds');
  assert.match(detail, /13 digits/);
  assert.match(detail, /Date\\.now\\(\\)/);
});

test('milliseconds beat too-far because the horizon is not the bug', () => {
  assert.notEqual(postAtVerdict(NOW * 1000, NOW)[0], 'too-far');
});

test('microseconds have their own verdict', () => {
  assert.equal(postAtVerdict(NOW * 1000000, NOW)[0], 'microseconds');
});

test('a delay passed as a deadline is caught', () => {
  const [verdict, detail] = postAtVerdict(300, NOW);
  assert.equal(verdict, 'duration-not-timestamp');
  assert.match(detail, /1970 plus 300 seconds/);
});

test('a value already behind the clock is in-past', () => {
  const [verdict, detail] = postAtVerdict(NOW - 5, NOW);
  assert.equal(verdict, 'in-past');
  assert.match(detail, /when it processes the request/);
  assert.equal(postAtVerdict(NOW, NOW)[0], 'in-past');
});

test('a send with no room is a finding before it fails', () => {
  const [verdict, detail] = postAtVerdict(NOW + 12, NOW);
  assert.equal(verdict, 'too-soon');
  assert.match(detail, /cold worker/);
});

test('the margin boundary is inclusive and the next second is fine', () => {
  assert.equal(postAtVerdict(NOW + 60, NOW)[0], 'too-soon');
  assert.equal(postAtVerdict(NOW + 61, NOW)[0], 'plausible');
});

test('past the horizon is separated from every arithmetic bug', () => {
  const [verdict, detail] = postAtVerdict(NOW + 121 * 86400, NOW);
  assert.equal(verdict, 'too-far');
  assert.match(detail, /horizon rolls forward/);
  assert.equal(postAtVerdict(NOW + 119 * 86400, NOW)[0], 'plausible');
});

test('a message ts handed over as a post_at is recognised', () => {
  const [verdict, detail] = postAtVerdict('1755000000.000200', NOW);
  assert.equal(verdict, 'message-ts');
  assert.match(detail, /whole seconds/);
});

test('a formatted date is not a post_at', () => {
  assert.equal(postAtVerdict('2026-09-01T09:00:00Z', NOW)[0], 'not-a-number');
  assert.equal(postAtVerdict(null, NOW)[0], 'missing');
  assert.equal(postAtVerdict('', NOW)[0], 'missing');
});

test('a clean multiple of an hour is named as a timezone bug', () => {
  const [verdict, detail] = offsetSmell(NOW + 5 * 3600, NOW);
  assert.equal(verdict, 'whole-hour-offset');
  assert.match(detail, /exactly 5 hour\\(s\\) ahead of/);
  assert.match(detail, /as if it were UTC/);
});

test('the offset is reported in both directions', () => {
  assert.match(offsetSmell(NOW - 3600, NOW)[1], /behind/);
});

test('the zones that are not on the hour are still timezone bugs', () => {
  assert.equal(offsetSmell(NOW + 5 * 3600 + 1800, NOW)[0], 'half-hour-offset');
  assert.equal(offsetSmell(NOW + 5 * 3600 + 2700, NOW)[0], 'half-hour-offset');
});

test('an untidy difference is not blamed on timezones', () => {
  const [verdict, detail] = offsetSmell(NOW + 240, NOW);
  assert.equal(verdict, 'drifted');
  assert.match(detail, /not a clean timezone offset/);
});

test('a value that matches what you meant is aligned', () => {
  assert.equal(offsetSmell(NOW + 10, NOW)[0], 'aligned');
  assert.equal(offsetSmell("nine o'clock", NOW)[0], 'uncomparable');
});

test('the gap the scheduler gave itself is its own signal', () => {
  const [verdict, detail] = creationMargin(NOW + 9, NOW);
  assert.equal(verdict, 'tight-window');
  assert.match(detail, /loses the race/);
  assert.equal(creationMargin(NOW + 3600, NOW)[0], 'comfortable');
});

test('an entry due before it was created is a sign error', () => {
  assert.equal(creationMargin(NOW - 10, NOW)[0], 'created-after');
  assert.equal(creationMargin(NOW + 60, null)[0], 'unknown');
});

test('the queue report counts by cause and names the next to fire', () => {
  const entries = [
    { id: 'Q1', channel_id: 'C1', post_at: NOW * 1000, date_created: NOW },
    { id: 'Q2', channel_id: 'C1', post_at: NOW + 12, date_created: NOW + 3 },
    { id: 'Q3', channel_id: 'C2', post_at: NOW + 86400, date_created: NOW },
    { id: 'Q4', channel_id: 'C2', post_at: NOW + 200 * 86400, date_created: NOW },
  ];
  const report = queueReport(entries, NOW);
  assert.equal(report.total, 4);
  assert.equal(report.unusable, 3);
  assert.equal(report.byVerdict.get('plausible'), 1);
  assert.deepEqual(report.nearest, ['Q2', NOW + 12]);
  assert.equal(report.rows[1].margin, 'tight-window');
});

test('an empty queue is not a finding', () => {
  const report = queueReport([], NOW);
  assert.equal(report.total, 0);
  assert.equal(report.unusable, 0);
  assert.equal(report.nearest, null);
});
''',
"faq": [
 ("It works most of the time. Why would post_at be in the past only sometimes?",
  "Because Slack checks the value when it processes the request, not when you computed it. Anything that adds delay between those two moments (a queue, a retry, a cold start, a slow DNS lookup) eats into whatever margin you left. A target five seconds out is not a schedule, it is a race you win most mornings. Assert at least a minute of room, and for anything nearer than that, post immediately instead."),
 ("How do I tell a units bug from a timezone bug from a stale value?",
  "By the size and shape of the error. Milliseconds show up as thirteen digits and a date tens of thousands of years out. A timezone conversion is off by a clean multiple of an hour, or by thirty or forty five minutes in a handful of zones. Anything else, a few minutes or a few days, is a stale value or a clock problem. The three want three different fixes, which is why the script never reports a bare wrong."),
 ("Why is there a 120-day limit, and what do I do about a yearly reminder?",
  "It is a documented ceiling on the API rather than something you can raise. Keep the schedule in your own store, and run a job that enqueues into Slack as the horizon rolls forward, for example every night scheduling everything now due inside the next 120 days. That also gives you somewhere to cancel and reschedule from, which the Slack queue on its own does not."),
 ("Can this script cancel the bad entries it finds?",
  "No, and that is deliberate. Listing the queue is a read; removing an entry changes your workspace. The script prints each unusable entry's id and names chat.deleteScheduledMessage so you can run it yourself. Every script in this section holds a token that could write and none of them does."),
 ("Does a scheduled message reserve anything, or count against a limit?",
  "It sits in a per-app, per-channel queue that you can enumerate with chat.scheduledMessages.list, and it fires as an ordinary message at the appointed second. Once it has fired it is a normal message with a ts and an author, which means the rules about who can edit it apply from that moment on, and it is no longer visible in the scheduled list at all."),
],
"related": [
 ("/slack/chat-update-message-not-found/", "the other note where a number in your store was the bug"),
 ("/slack/cant-update-or-delete-message/", "what happens after it fires and you want it back"),
 ("/slack/http-200-ok-false/", "why time_in_past arrived with a 200 on it"),
],
"citations": [CITE_SCHEDULE, CITE_SCHEDULED_LIST, CITE_POSTMESSAGE, CITE_WEB_API],
})

