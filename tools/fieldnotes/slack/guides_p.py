#!/usr/bin/env python3
"""/slack/ field notes, batch P - the writing.

Four notes in two pairs. The first pair is about a message that has nothing in
it, or has too much of the wrong kind of thing in it, and both are refusals:
the legacy attachments array has its own ceiling, on its own surface, with its
own error, and a message that renders to nothing at all is refused before it is
ever delivered. Neither is the batch before this one, which was about payloads
that Slack accepted.

The second pair is about where a reply goes. One is a parent that has stopped
being able to host a reply, which Slack says out loud. The other is a parent
that is perfectly healthy and is not a root, which Slack says nothing at all
about: it reparents the reply, returns ok, and leaves you with a conversation
that reads as though everybody is answering the wrong question.

Read only throughout. Two of these four run with no token at all against a
payload file, and the two threading scripts read one thread each. None of them
sends a message, which matters more here than usual: three of the four faults
in this batch can only be reproduced by posting into a real channel, and two of
them leave the evidence behind afterwards.
"""

CITE_POSTMESSAGE = ("chat.postMessage method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_CONV_REPLIES = ("conversations.replies method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.replies")
CITE_RETRIEVING = ("Retrieving messages - Slack Docs",
                   "https://docs.slack.dev/messaging/retrieving-messages")
CITE_FORMATTING = ("Formatting message text - Slack Docs",
                   "https://docs.slack.dev/messaging/formatting-message-text")
CITE_BLOCKS = ("Blocks reference - Slack Docs",
               "https://docs.slack.dev/reference/block-kit/blocks")
CITE_BLOCK_KIT = ("Block Kit - Slack Docs", "https://docs.slack.dev/block-kit/")
CITE_WEB_API = ("Web API - Slack Docs", "https://docs.slack.dev/apis/web-api/")

GUIDES = []


GUIDES.append({
"slug": "too-many-attachments",
"title": "too_many_attachments: the legacy array has its own ceiling",
"description": "Attachments are a second surface with a second ceiling: 100, not 50. Measure it, and price the migration before it lands you on the tighter one.",
"h1": "too_many_attachments: the legacy array has its own ceiling",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": [
    "slack too_many_attachments",
    "slack attachment_payload_limit_exceeded",
    "slack 100 attachment limit chat.postMessage",
    "slack attachments deprecated migrate to blocks",
    "slack mrkdwn_in attachment formatting not working",
],
"deps": "Python 3.9+ with requests, or Node.js 18+; no token at all if you measure a payload file",
"lead": "The alert integration has posted one coloured bar per failing check for four years. This afternoon a dependency went down, 140 checks failed at once, and the alert came back <code>{\"ok\": false, \"error\": \"too_many_attachments\"}</code>. Nothing was deployed. The message that would have explained the outage is the one the outage suppressed.</p><p>The obvious answer is to move off attachments, because Slack has described them as legacy for years. That answer is right and it is also a trap: the surface everybody migrates to has a ceiling of 50, and you were refused at 100.",
"short_answer": """<p>A message takes at most <strong>100 attachments</strong>. Past that, <code>chat.postMessage</code> answers <code>too_many_attachments</code>, and a serialized attachment payload that is large enough answers <code>attachment_payload_limit_exceeded</code> at a lower count. There is a parallel ceiling of <strong>10</strong> on <code>contact_cards</code>.</p>
<p>This is a different ceiling on a different surface from the 50-block limit, and the two coexist in one message. An audit that measures <code>blocks</code> reports nothing at all about the message that was just refused, which is why an integration built out of attachments can fail a limit check and pass a limit audit on the same payload.</p>
<p>Attachments still exist because they still do one thing Block Kit does not: the coloured bar down the left edge. Every monitoring tool that emits red for critical and yellow for warning emits attachments, and there is no Block Kit equivalent to move that to. So this script measures the ceilings, and then prices the migration honestly - which usually means <strong>one attachment becomes more than one block</strong>, against a ceiling half the size.</p>""",
"problem": """<p>The count is the least of it. Attachments are legacy in the specific sense that they are frozen: they are still delivered, still rendered, and no longer developed, so everything about them is slightly out of step with the rest of the API. Formatting inside an attachment is opt-in through <code>mrkdwn_in</code>, and a field not named there renders its own asterisks, which is why so many bot messages in so many workspaces show <code>*Critical*</code> with the punctuation visible. Nobody files that as a bug. It just looks slightly broken forever.</p>
<p>The migration advice is also given without a number attached, and the number is what decides whether the advice works. An attachment with a title, a body and eight fields is not one block. It is a section for the body, a section for each group of ten fields, sometimes a context row for the footer, and a divider if you want to keep the visual separation the coloured bar was providing. Sixty attachments do not become sixty blocks; they become something like a hundred and twenty, against a ceiling of fifty. A team that rewrites the generator over an afternoon discovers this at the end of the afternoon.</p>
<p>And the failure fires on the same schedule as every other capacity failure: on the busiest day, in the message that mattered most, with an error string nobody in the room has seen before. The generator maps a list to attachments, one per item, and the list is a list of things that went wrong. It is longest exactly when somebody is waiting for it.</p>
<p>Underneath all of it, the attachment payload has a size ceiling that Slack does not publish as a number. A hundred short bars are fine and forty long ones are not, and the error is a different string, which makes the two failures look like unrelated incidents when they are the same generator hitting two edges of the same box.</p>""",
"why": """<p><strong>This is a second ceiling, not a second reading of the first one.</strong> Blocks cap at 50 and attachments cap at 100, in the same message, on the same call. A script that measures one and reports on the other is worse than no script, because it returns a clean verdict on a payload that was refused ten minutes ago.</p>
<p><strong>The migration cost has to be computed, or the advice is wrong half the time.</strong> Telling somebody to move to blocks without saying how many blocks their content becomes is telling them to swap a ceiling of 100 for a ceiling of 50 and hope. The arithmetic is not hard and it changes the plan, so the script does it.</p>
<p><strong>Two of the smells are reasons to keep an attachment.</strong> The coloured bar has no replacement, and content already expressed as blocks inside an attachment is already migrated. A report that lists those as faults is a report that gets read once and ignored, so they are printed as findings without being printed as problems.</p>
<p><strong><code>mrkdwn_in</code> is opt-in, and nothing tells you when you forgot.</strong> The message posts, the formatting does not happen, and the asterisks are right there in the channel. This is the only fault in the note with no error string and no ceiling, and it is the one most likely to already be true of your workspace.</p>
<p><strong>The byte ceiling is not published, so the script reports the measurement.</strong> It prints the serialized size, names the line it compared against, and says plainly that the line is a default rather than a documented figure. A verdict built on a guessed threshold is worth less than the number it was computed from.</p>
<p><strong>Nothing is sent.</strong> Finding an attachment ceiling by walking into it means posting a hundred coloured bars into a channel, twice, because the first attempt is how you learn the count and the second is how you learn the size. With <code>--payload</code> this holds no token at all.</p>""",
"steps": [
 {"h": "Measure the payload you were about to send",
  "body": """<p>Write the failing message to a file and run the script with <code>--payload</code>. No token, no network, nothing posted. <code>budget_report</code> returns the count, the serialized size, the <code>contact_cards</code> count and which ceiling each one is against.</p>"""},
 {"h": "Read the byte line as a measurement, not a verdict",
  "body": """<p>Slack does not publish the size behind <code>attachment_payload_limit_exceeded</code>, so <code>--payload-bytes</code> sets the line and the report always prints the number it measured. Adjust the line to whatever your workspace actually refuses; the measurement is the part that transfers.</p>"""},
 {"h": "Price the migration before you plan it",
  "body": """<p><code>migration_cost</code> converts the same content into the blocks it would need: a section per body, one per ten fields, a divider between items to keep the separation the coloured bar gave you. If that number is over 50, moving to blocks makes the problem worse and the real repair is capping the list.</p>"""},
 {"h": "Sort the attachments by what they are actually doing",
  "body": """<p><code>legacy_smells</code> names it per attachment. A coloured bar has no Block Kit equivalent and is a reason to stay. Text only maps to a section and costs nothing. Legacy <code>actions</code> are a retired interactive style. These are three different decisions, not one migration.</p>"""},
 {"h": "Fix the formatting you did not know was broken",
  "body": """<p>Any attachment whose <code>text</code>, <code>pretext</code> or field values contain mrkdwn without naming that field in <code>mrkdwn_in</code> is rendering its own punctuation right now. This has nothing to do with the ceiling and it is usually the finding people act on first.</p>"""},
 {"h": "Run the same measurement over what you have already posted",
  "body": """<p>With a token and <code>--channel</code>, the script reads <code>conversations.history</code> and measures the attachments Slack stored for your app's own messages. The distribution is the useful part: a fleet whose tail sits at 80 is one bad afternoon from the ceiling.</p>"""},
],
"verify": """<p>Cap the generator, run the same fixture again, and the verdict should move without anything being sent.</p>
<pre><code class="language-bash">python3 slack_attachment_budget.py --payload failing-alert.json
# payload    failing-alert.json
# budget     reject     payload  140 attachment(s), 0 contact_card(s), 6441 bytes
# reason     too_many_attachments   140 attachments, and the ceiling is 100
# migration  140 attachment(s) become about 279 block(s); the block ceiling is 50, so a
#            straight migration lands over it
# legacy     colour-bar           color '#e01e5a' is the one thing an attachment does
#                                 that Block Kit has no equivalent for; a reason to keep it
# legacy     mrkdwn-not-enabled   text contains mrkdwn and mrkdwn_in does not list 'text',
#                                 so the asterisks and link syntax render literally</code></pre>""",
"code_intro": "Four pure functions and no network in the path that matters. <code>attachment_size</code> serializes the array the way the API counts it. <code>legacy_smells</code> names what one attachment is doing rather than whether it is wrong, because two of the answers are reasons to keep it. <code>migration_cost</code> is the one that earns the note: it turns \"just move to blocks\" into a block count you can hold against a ceiling of fifty before you spend an afternoon on it. <code>budget_report</code> holds one message against every ceiling at once and prints the numbers beside the verdict.",
"py_file": "slack_attachment_budget.py",
"py": '''"""Measure the legacy attachments array against the ceilings that are its own.

Read only. With --payload it holds no token and calls no Slack method at all;
with --channel it reads conversations.history and measures the attachments
Slack stored for messages your app already posted. Nothing is ever sent from
here: finding an attachment ceiling by walking into it puts a hundred coloured
bars in a real channel.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_attachment_budget")

API = "https://slack.com/api/"

# Published, and the one number in this script that is not a judgement call.
MAX_ATTACHMENTS = 100
# The parallel ceiling on the contact_cards field, which travels beside
# attachments and is counted separately.
MAX_CONTACT_CARDS = 10

# Slack does not publish the byte ceiling behind attachment_payload_limit_exceeded,
# so this is a deliberately conservative default rather than a documented number,
# and --payload-bytes exists because the figure that matters is the one your own
# workspace refuses at. The measurement is printed either way, so the report is
# useful even when the threshold is wrong.
DEFAULT_PAYLOAD_BYTES = 12000

# Belongs to the note next door, and is here only for the migration arithmetic:
# the point of that arithmetic is that moving off attachments lands you on this.
BLOCK_CEILING = 50
# A section holds at most ten fields, which is what an attachment fields grid
# turns into.
FIELDS_PER_SECTION = 10

# Formatting that only renders when the field is named in mrkdwn_in. Inside an
# attachment this is opt in, which is the single most surprising thing about
# the legacy surface and the reason so many attachments show their own asterisks.
MRKDWN = re.compile(r"\\*[^*\\n]+\\*|_[^_\\n]+_|~[^~\\n]+~|`[^`\\n]+`|<https?://[^>|]+\\|[^>]+>")

# Fields whose content mrkdwn_in can name.
MRKDWN_FIELDS = ("text", "pretext", "fields")


def attachment_size(attachments):
    """Serialized bytes of the attachments array, counted as the API counts it.

    Pure. Returns -1 for a structure that will not serialize at all, which is a
    different fault and belongs to whoever built it.
    """
    try:
        encoded = json.dumps(attachments, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        return -1
    return len(encoded.encode("utf-8"))


def legacy_smells(attachment):
    """Name what one attachment is doing that Block Kit does another way. Pure.

    Returns a list of (smell, detail). This is not a list of faults. Two of
    these are reasons to keep an attachment, and reporting them as problems is
    how a migration report gets ignored.
    """
    out = []
    if not isinstance(attachment, dict):
        return [("not-an-object", "an attachment must be an object; this is a %s"
                 % type(attachment).__name__)]

    declared = attachment.get("mrkdwn_in")
    declared = set(declared) if isinstance(declared, list) else set()
    for field in MRKDWN_FIELDS:
        value = attachment.get(field)
        if field == "fields":
            body = " ".join(str(f.get("value", "")) for f in value or []
                            if isinstance(f, dict))
        else:
            body = str(value or "")
        if body and MRKDWN.search(body) and field not in declared:
            out.append(("mrkdwn-not-enabled",
                        "%s contains mrkdwn and mrkdwn_in does not list %r, so the "
                        "asterisks and link syntax render literally" % (field, field)))

    if attachment.get("color"):
        out.append(("colour-bar",
                    "color %r is the one thing an attachment does that Block Kit has "
                    "no equivalent for; this is a reason to keep it"
                    % str(attachment["color"])[:16]))
    if isinstance(attachment.get("fields"), list) and attachment["fields"]:
        out.append(("fields-grid",
                    "%d field(s), which become section fields ten at a time"
                    % len(attachment["fields"])))
    if isinstance(attachment.get("blocks"), list) and attachment["blocks"]:
        out.append(("blocks-inside",
                    "%d block(s) already inside the attachment, so the content is "
                    "migrated and only the colour bar is still legacy"
                    % len(attachment["blocks"])))
    if isinstance(attachment.get("actions"), list) and attachment["actions"]:
        out.append(("legacy-actions",
                    "%d interactive action(s) in the retired attachment style rather "
                    "than a Block Kit actions block" % len(attachment["actions"])))
    if not out:
        out.append(("plain", "text only, so this maps to one section and nothing is "
                             "lost by moving it"))
    return out


def migration_cost(attachments, separator=True):
    """How many blocks the same content needs once it stops being attachments.

    Pure. The answer matters because it is usually larger than the attachment
    count, and the ceiling on the other side is 50 rather than 100. A fleet at
    70 attachments is not one refactor away from safety; it is one refactor away
    from a tighter ceiling.
    """
    items = attachments if isinstance(attachments, list) else []
    blocks = 0
    for a in items:
        if not isinstance(a, dict):
            continue
        inner = a.get("blocks")
        if isinstance(inner, list) and inner:
            blocks += len(inner)
            continue
        if str(a.get("pretext") or "").strip():
            blocks += 1
        if str(a.get("title") or "").strip() or str(a.get("text") or "").strip():
            blocks += 1
        fields = a.get("fields")
        if isinstance(fields, list) and fields:
            blocks += -(-len(fields) // FIELDS_PER_SECTION)
        if str(a.get("footer") or "").strip():
            blocks += 1
        if isinstance(a.get("actions"), list) and a["actions"]:
            blocks += 1
    if separator and len(items) > 1:
        blocks += len(items) - 1
    return {
        "attachments": len(items),
        "blocks_needed": blocks,
        "block_ceiling": BLOCK_CEILING,
        "over_block_ceiling": blocks > BLOCK_CEILING,
        "detail": ("%d attachment(s) become about %d block(s); the block ceiling is "
                   "%d, so %s" % (len(items), blocks, BLOCK_CEILING,
                                  "a straight migration lands over it"
                                  if blocks > BLOCK_CEILING
                                  else "a straight migration fits")),
    }


def budget_report(attachments, contact_cards=None, payload_bytes=DEFAULT_PAYLOAD_BYTES):
    """Hold one message's attachments against every ceiling at once. Pure.

    Returns a verdict of reject, at-risk or ok, plus the numbers, because the
    numbers are what somebody acts on and the verdict is only how they are
    sorted.
    """
    items = attachments if isinstance(attachments, list) else []
    cards = contact_cards if isinstance(contact_cards, list) else []
    size = attachment_size(items)
    reasons = []
    verdict = "ok"

    if len(items) > MAX_ATTACHMENTS:
        verdict = "reject"
        reasons.append(("too_many_attachments",
                        "%d attachments, and the ceiling is %d"
                        % (len(items), MAX_ATTACHMENTS)))
    if len(cards) > MAX_CONTACT_CARDS:
        verdict = "reject"
        reasons.append(("too_many_contact_cards",
                        "%d contact_cards, and the ceiling is %d"
                        % (len(cards), MAX_CONTACT_CARDS)))
    if size > payload_bytes:
        verdict = "reject"
        reasons.append(("attachment_payload_limit_exceeded",
                        "%d bytes serialized, past the %d byte line this run used; "
                        "Slack does not publish the real figure, so treat this as a "
                        "measurement rather than a certainty" % (size, payload_bytes)))

    if verdict == "ok":
        near_count = len(items) >= MAX_ATTACHMENTS * 0.8
        near_size = size >= payload_bytes * 0.8
        if near_count or near_size:
            verdict = "at-risk"
            reasons.append(("inside-the-last-fifth",
                            "%d of %d attachments and %d of %d bytes; this fails on a "
                            "busier day and nothing will have changed"
                            % (len(items), MAX_ATTACHMENTS, size, payload_bytes)))
    if not items and not cards:
        reasons.append(("no-attachments", "nothing legacy here"))
    return {
        "count": len(items),
        "contact_cards": len(cards),
        "bytes": size,
        "payload_bytes": payload_bytes,
        "verdict": verdict,
        "reasons": reasons,
    }


def _load_payload(path):
    body = json.loads(open(path, encoding="utf-8").read())
    if isinstance(body, list):
        return body, []
    if isinstance(body, dict):
        return body.get("attachments") or [], body.get("contact_cards") or []
    return [], []


def _report(label, attachments, cards, args):
    b = budget_report(attachments, cards, args.payload_bytes)
    line = ("%s  %d attachment(s), %d contact_card(s), %d bytes"
            % (label, b["count"], b["contact_cards"], b["bytes"]))
    (log.warning if b["verdict"] != "ok" else log.info)(
        "budget     %-10s %s", b["verdict"], line)
    for code, detail in b["reasons"]:
        if code == "no-attachments":
            continue
        (log.info if code == "inside-the-last-fifth" else log.warning)(
            "reason     %-34s %s", code, detail)
    if not attachments:
        return b["verdict"] != "ok"
    m = migration_cost(attachments)
    (log.warning if m["over_block_ceiling"] else log.info)(
        "migration  %s", m["detail"])
    seen = {}
    for a in attachments:
        for smell, detail in legacy_smells(a):
            seen.setdefault(smell, detail)
    for smell in sorted(seen):
        (log.info if smell in ("colour-bar", "plain", "blocks-inside")
         else log.warning)("legacy     %-20s %s", smell, seen[smell])
    return b["verdict"] != "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", help="a JSON file holding a message payload or a "
                                      "bare attachments array; needs no token")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel your app posts into; repeatable")
    ap.add_argument("--limit", type=int, default=200, help="messages read per channel")
    ap.add_argument("--payload-bytes", type=int, default=DEFAULT_PAYLOAD_BYTES,
                    help="serialized byte line to report against")
    args = ap.parse_args()

    if args.payload:
        attachments, cards = _load_payload(args.payload)
        log.info("payload    %s", args.payload)
        return 1 if _report("payload", attachments, cards, args) else 0

    if not args.channel:
        log.error("pass --payload FILE, or --channel with a token in %s", args.token_env)
        return 2
    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history is enough)", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    bot_id, bot_user = who.get("bot_id") or "", who.get("user_id") or ""
    log.info("identity   %s in %s", bot_user, who.get("team"))

    findings, using = 0, 0
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        for m in body.get("messages") or []:
            mine = ((bot_id and m.get("bot_id") == bot_id)
                    or (bot_user and m.get("user") == bot_user))
            if not mine:
                continue
            attachments = m.get("attachments")
            if not (isinstance(attachments, list) and attachments):
                continue
            using += 1
            if _report("%s ts=%s" % (channel, m.get("ts")), attachments,
                       m.get("contact_cards"), args):
                findings += 1

    if not using:
        log.info("verdict    clear          nothing of ours posts attachments here")
        return 0
    log.warning("using      %d of our messages still post attachments", using)
    log.warning("  repair: cap the attachment count in the generator and summarize the "
                "overflow, the same way you would cap any unbounded list")
    log.warning("  repair: keep attachments only for the coloured side bar, and put the "
                "content in blocks inside the attachment")
    log.warning("  repair: name every mrkdwn bearing field in mrkdwn_in, or the "
                "formatting renders as its own punctuation")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-attachment-budget.mjs",
"js": '''/**
 * Measure the legacy attachments array against the ceilings that are its own.
 *
 * Read only. With --payload it holds no token and calls no Slack method at
 * all; with --channel it reads conversations.history and measures the
 * attachments Slack stored for messages your app already posted. Nothing is
 * ever sent from here.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Published, and the one number here that is not a judgement call.
export const MAX_ATTACHMENTS = 100;
// The parallel ceiling on contact_cards, which is counted separately.
export const MAX_CONTACT_CARDS = 10;
// Not a documented figure. Slack does not publish the byte ceiling behind
// attachment_payload_limit_exceeded, so this is conservative and adjustable,
// and the measurement is printed either way.
export const DEFAULT_PAYLOAD_BYTES = 12000;
// Belongs to the note next door, and is here only for the migration
// arithmetic: the point of that arithmetic is that you land on this.
export const BLOCK_CEILING = 50;
const FIELDS_PER_SECTION = 10;

// Formatting that only renders when the field is named in mrkdwn_in.
const MRKDWN = /\\*[^*\\n]+\\*|_[^_\\n]+_|~[^~\\n]+~|`[^`\\n]+`|<https?:\\/\\/[^>|]+\\|[^>]+>/;
const MRKDWN_FIELDS = ['text', 'pretext', 'fields'];

/** Serialized bytes of the attachments array, counted as the API counts it. Pure. */
export function attachmentSize(attachments) {
  let encoded;
  try {
    encoded = JSON.stringify(attachments);
  } catch {
    return -1;
  }
  if (encoded === undefined) return -1;
  return Buffer.byteLength(encoded, 'utf8');
}

/**
 * Name what one attachment is doing that Block Kit does another way. Pure.
 * Not a list of faults: two of these are reasons to keep an attachment, and
 * reporting them as problems is how a migration report gets ignored.
 */
export function legacySmells(attachment) {
  const out = [];
  if (attachment === null || typeof attachment !== 'object' || Array.isArray(attachment)) {
    return [['not-an-object',
      `an attachment must be an object; this is a ${typeof attachment}`]];
  }
  const declared = new Set(Array.isArray(attachment.mrkdwn_in) ? attachment.mrkdwn_in : []);
  for (const field of MRKDWN_FIELDS) {
    let body;
    if (field === 'fields') {
      body = (attachment.fields ?? [])
        .filter((f) => f && typeof f === 'object')
        .map((f) => String(f.value ?? '')).join(' ');
    } else {
      body = String(attachment[field] ?? '');
    }
    if (body && MRKDWN.test(body) && !declared.has(field)) {
      out.push(['mrkdwn-not-enabled',
        `${field} contains mrkdwn and mrkdwn_in does not list "${field}", so the ` +
        'asterisks and link syntax render literally']);
    }
  }
  if (attachment.color) {
    out.push(['colour-bar',
      `color "${String(attachment.color).slice(0, 16)}" is the one thing an ` +
      'attachment does that Block Kit has no equivalent for; this is a reason to keep it']);
  }
  if (Array.isArray(attachment.fields) && attachment.fields.length) {
    out.push(['fields-grid',
      `${attachment.fields.length} field(s), which become section fields ten at a time`]);
  }
  if (Array.isArray(attachment.blocks) && attachment.blocks.length) {
    out.push(['blocks-inside',
      `${attachment.blocks.length} block(s) already inside the attachment, so the ` +
      'content is migrated and only the colour bar is still legacy']);
  }
  if (Array.isArray(attachment.actions) && attachment.actions.length) {
    out.push(['legacy-actions',
      `${attachment.actions.length} interactive action(s) in the retired attachment ` +
      'style rather than a Block Kit actions block']);
  }
  if (!out.length) {
    out.push(['plain',
      'text only, so this maps to one section and nothing is lost by moving it']);
  }
  return out;
}

/**
 * How many blocks the same content needs once it stops being attachments. Pure.
 * Usually more than the attachment count, against a ceiling of 50 rather than
 * 100, which is why a fleet at 70 attachments is not one refactor from safety.
 */
export function migrationCost(attachments, separator = true) {
  const items = Array.isArray(attachments) ? attachments : [];
  let blocks = 0;
  for (const a of items) {
    if (!a || typeof a !== 'object') continue;
    if (Array.isArray(a.blocks) && a.blocks.length) {
      blocks += a.blocks.length;
      continue;
    }
    if (String(a.pretext ?? '').trim()) blocks += 1;
    if (String(a.title ?? '').trim() || String(a.text ?? '').trim()) blocks += 1;
    if (Array.isArray(a.fields) && a.fields.length) {
      blocks += Math.ceil(a.fields.length / FIELDS_PER_SECTION);
    }
    if (String(a.footer ?? '').trim()) blocks += 1;
    if (Array.isArray(a.actions) && a.actions.length) blocks += 1;
  }
  if (separator && items.length > 1) blocks += items.length - 1;
  const over = blocks > BLOCK_CEILING;
  return {
    attachments: items.length,
    blocksNeeded: blocks,
    blockCeiling: BLOCK_CEILING,
    overBlockCeiling: over,
    detail: `${items.length} attachment(s) become about ${blocks} block(s); the block ` +
      `ceiling is ${BLOCK_CEILING}, so ${over ? 'a straight migration lands over it'
        : 'a straight migration fits'}`,
  };
}

/**
 * Hold one message's attachments against every ceiling at once. Pure.
 * Returns reject, at-risk or ok plus the numbers, because the numbers are what
 * somebody acts on and the verdict is only how they are sorted.
 */
export function budgetReport(attachments, contactCards = null,
  payloadBytes = DEFAULT_PAYLOAD_BYTES) {
  const items = Array.isArray(attachments) ? attachments : [];
  const cards = Array.isArray(contactCards) ? contactCards : [];
  const size = attachmentSize(items);
  const reasons = [];
  let verdict = 'ok';

  if (items.length > MAX_ATTACHMENTS) {
    verdict = 'reject';
    reasons.push(['too_many_attachments',
      `${items.length} attachments, and the ceiling is ${MAX_ATTACHMENTS}`]);
  }
  if (cards.length > MAX_CONTACT_CARDS) {
    verdict = 'reject';
    reasons.push(['too_many_contact_cards',
      `${cards.length} contact_cards, and the ceiling is ${MAX_CONTACT_CARDS}`]);
  }
  if (size > payloadBytes) {
    verdict = 'reject';
    reasons.push(['attachment_payload_limit_exceeded',
      `${size} bytes serialized, past the ${payloadBytes} byte line this run used; ` +
      'Slack does not publish the real figure, so treat this as a measurement rather ' +
      'than a certainty']);
  }
  if (verdict === 'ok'
      && (items.length >= MAX_ATTACHMENTS * 0.8 || size >= payloadBytes * 0.8)) {
    verdict = 'at-risk';
    reasons.push(['inside-the-last-fifth',
      `${items.length} of ${MAX_ATTACHMENTS} attachments and ${size} of ` +
      `${payloadBytes} bytes; this fails on a busier day and nothing will have changed`]);
  }
  if (!items.length && !cards.length) reasons.push(['no-attachments', 'nothing legacy here']);
  return {
    count: items.length,
    contactCards: cards.length,
    bytes: size,
    payloadBytes,
    verdict,
    reasons,
  };
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

function report(label, attachments, cards, payloadBytes) {
  const b = budgetReport(attachments, cards, payloadBytes);
  const line = `${label}  ${b.count} attachment(s), ${b.contactCards} contact_card(s), ` +
    `${b.bytes} bytes`;
  (b.verdict === 'ok' ? console.log : console.warn)(
    `budget     ${b.verdict.padEnd(10)} ${line}`);
  for (const [code, detail] of b.reasons) {
    if (code === 'no-attachments') continue;
    (code === 'inside-the-last-fifth' ? console.log : console.warn)(
      `reason     ${code.padEnd(34)} ${detail}`);
  }
  if (!attachments || !attachments.length) return b.verdict !== 'ok';
  const m = migrationCost(attachments);
  (m.overBlockCeiling ? console.warn : console.log)(`migration  ${m.detail}`);
  const seen = new Map();
  for (const a of attachments) {
    for (const [smell, detail] of legacySmells(a)) {
      if (!seen.has(smell)) seen.set(smell, detail);
    }
  }
  for (const smell of [...seen.keys()].sort()) {
    (['colour-bar', 'plain', 'blocks-inside'].includes(smell) ? console.log : console.warn)(
      `legacy     ${smell.padEnd(20)} ${seen.get(smell)}`);
  }
  return b.verdict !== 'ok';
}

async function main() {
  const args = process.argv.slice(2);
  const payloadBytes = Number(arg(args, '--payload-bytes', String(DEFAULT_PAYLOAD_BYTES)));
  const payload = arg(args, '--payload');

  if (payload) {
    const body = JSON.parse(await readFile(payload, 'utf8'));
    const attachments = Array.isArray(body) ? body : (body.attachments ?? []);
    const cards = Array.isArray(body) ? [] : (body.contact_cards ?? []);
    console.log(`payload    ${payload}`);
    if (report('payload', attachments, cards, payloadBytes)) process.exitCode = 1;
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error(`pass --payload FILE, or --channel with a token in ${tokenEnv}`);
    process.exitCode = 2;
    return;
  }
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history is enough)`);
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const botId = who.bot_id ?? '';
  const botUser = who.user_id ?? '';
  console.log(`identity   ${botUser} in ${who.team}`);

  let findings = 0;
  let using = 0;
  for (const channel of channels) {
    const url = `${API}conversations.history?channel=${encodeURIComponent(channel)}` +
      `&limit=${encodeURIComponent(limit)}`;
    const body = await (await fetch(url, { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    for (const m of body.messages ?? []) {
      const mine = (botId && m.bot_id === botId) || (botUser && m.user === botUser);
      if (!mine) continue;
      if (!Array.isArray(m.attachments) || !m.attachments.length) continue;
      using += 1;
      if (report(`${channel} ts=${m.ts}`, m.attachments, m.contact_cards, payloadBytes)) {
        findings += 1;
      }
    }
  }

  if (!using) {
    console.log('verdict    clear          nothing of ours posts attachments here');
    return;
  }
  console.warn(`using      ${using} of our messages still post attachments`);
  console.warn('  repair: cap the attachment count in the generator and summarize the ' +
    'overflow, the same way you would cap any unbounded list');
  console.warn('  repair: keep attachments only for the coloured side bar, and put the ' +
    'content in blocks inside the attachment');
  console.warn('  repair: name every mrkdwn bearing field in mrkdwn_in, or the ' +
    'formatting renders as its own punctuation');
  if (findings) process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertion the note rests on is that sixty attachments become more than sixty blocks, because that is the arithmetic that makes the obvious migration a worse position rather than a better one. The rest are about not crying wolf: a coloured bar has to come back as a reason to keep an attachment rather than as a fault, an attachment that already holds blocks has to cost what it holds rather than what it looks like, and a two-item payload has to be able to fail on bytes while passing on count, since that is the case a check on the length alone was written for and does not catch.",
"test_py_file": "test_slack_attachment_budget.py",
"test_js_file": "slack-attachment-budget.test.mjs",
"test_py": '''from slack_attachment_budget import (attachment_size, budget_report, legacy_smells,
                                     migration_cost)


def bar(i):
    return {"color": "#e01e5a", "text": "check %d failed" % i, "mrkdwn_in": ["text"]}


def test_a_hundred_attachments_pass_and_a_hundred_and_one_do_not():
    assert budget_report([bar(i) for i in range(100)])["verdict"] != "reject"
    b = budget_report([bar(i) for i in range(101)])
    assert b["verdict"] == "reject"
    assert b["reasons"][0][0] == "too_many_attachments"
    assert "101" in b["reasons"][0][1]


def test_the_contact_cards_ceiling_is_counted_separately():
    b = budget_report([bar(0)], [{"name": "n%d" % i} for i in range(11)])
    assert b["verdict"] == "reject"
    assert [c for c, _ in b["reasons"]] == ["too_many_contact_cards"]
    assert b["count"] == 1


def test_a_small_count_can_still_be_over_on_bytes():
    fat = [{"text": "x" * 4000}, {"text": "y" * 4000}]
    b = budget_report(fat, None, payload_bytes=5000)
    assert b["count"] == 2
    assert b["verdict"] == "reject"
    assert b["reasons"][0][0] == "attachment_payload_limit_exceeded"
    assert "not publish" in b["reasons"][0][1]


def test_the_byte_line_is_reported_as_the_line_this_run_used():
    b = budget_report([{"text": "x" * 100}], None, payload_bytes=9999)
    assert b["payload_bytes"] == 9999
    assert b["bytes"] > 100


def test_inside_the_last_fifth_is_a_warning_and_not_a_rejection():
    b = budget_report([bar(i) for i in range(85)])
    assert b["verdict"] == "at-risk"
    assert b["reasons"][0][0] == "inside-the-last-fifth"
    assert "busier day" in b["reasons"][0][1]


def test_a_message_with_no_attachments_is_not_a_finding():
    b = budget_report(None)
    assert b["verdict"] == "ok"
    assert b["count"] == 0
    assert b["reasons"] == [("no-attachments", "nothing legacy here")]


def test_attachment_size_counts_bytes_rather_than_characters():
    assert attachment_size([{"text": "abc"}]) == len('[{"text":"abc"}]')
    assert attachment_size([{"text": "é"}]) == len('[{"text":"x"}]') + 1
    assert attachment_size([{"bad": {1, 2}}]) == -1


def test_mrkdwn_without_mrkdwn_in_renders_its_own_punctuation():
    smells = dict(legacy_smells({"text": "*3 deploys* failed"}))
    assert "mrkdwn-not-enabled" in smells
    assert "render literally" in smells["mrkdwn-not-enabled"]
    assert "mrkdwn-not-enabled" not in dict(
        legacy_smells({"text": "*3 deploys* failed", "mrkdwn_in": ["text"]}))
    assert "mrkdwn-not-enabled" not in dict(legacy_smells({"text": "3 deploys failed"}))


def test_a_link_in_slack_syntax_counts_as_mrkdwn():
    smells = dict(legacy_smells({"pretext": "see <https://ci.example.com/1|build 1>"}))
    assert "mrkdwn-not-enabled" in smells
    assert "pretext" in smells["mrkdwn-not-enabled"]


def test_the_colour_bar_is_reported_as_a_reason_to_keep_it():
    smells = dict(legacy_smells({"color": "good", "text": "ok"}))
    assert "colour-bar" in smells
    assert "reason to keep it" in smells["colour-bar"]


def test_blocks_inside_an_attachment_are_already_migrated():
    smells = dict(legacy_smells({"color": "#36a64f", "blocks": [{"type": "divider"}]}))
    assert "blocks-inside" in smells
    assert "only the colour bar is still legacy" in smells["blocks-inside"]


def test_legacy_actions_are_named_separately_from_the_rest():
    smells = dict(legacy_smells({"actions": [{"type": "button", "text": "Retry"}]}))
    assert "legacy-actions" in smells
    assert "retired" in smells["legacy-actions"]


def test_a_plain_attachment_is_reported_as_costing_nothing_to_move():
    assert dict(legacy_smells({"text": "3 deploys failed"})).get("plain")
    assert legacy_smells("not a dict")[0][0] == "not-an-object"


def test_the_migration_lands_on_the_tighter_ceiling():
    m = migration_cost([bar(i) for i in range(60)])
    assert m["attachments"] == 60
    assert m["blocks_needed"] > 60
    assert m["over_block_ceiling"] is True
    assert "lands over it" in m["detail"]


def test_a_small_fleet_migrates_without_hitting_the_block_ceiling():
    m = migration_cost([bar(i) for i in range(4)])
    assert m["blocks_needed"] == 7
    assert m["over_block_ceiling"] is False
    assert "fits" in m["detail"]


def test_a_fields_grid_costs_one_section_per_ten_fields():
    a = {"text": "summary", "fields": [{"title": str(i), "value": str(i)}
                                       for i in range(25)]}
    assert migration_cost([a])["blocks_needed"] == 1 + 3


def test_an_attachment_that_already_holds_blocks_costs_what_it_holds():
    a = {"color": "danger", "text": "ignored", "blocks": [{"type": "divider"}] * 5}
    assert migration_cost([a])["blocks_needed"] == 5
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  attachmentSize, budgetReport, legacySmells, migrationCost,
} from './slack-attachment-budget.mjs';

const bar = (i) => ({ color: '#e01e5a', text: `check ${i} failed`, mrkdwn_in: ['text'] });
const many = (n) => Array.from({ length: n }, (_, i) => bar(i));
const smells = (a) => new Map(legacySmells(a));

test('a hundred attachments pass and a hundred and one do not', () => {
  assert.notEqual(budgetReport(many(100)).verdict, 'reject');
  const b = budgetReport(many(101));
  assert.equal(b.verdict, 'reject');
  assert.equal(b.reasons[0][0], 'too_many_attachments');
  assert.match(b.reasons[0][1], /101/);
});

test('the contact cards ceiling is counted separately', () => {
  const cards = Array.from({ length: 11 }, (_, i) => ({ name: `n${i}` }));
  const b = budgetReport([bar(0)], cards);
  assert.equal(b.verdict, 'reject');
  assert.deepEqual(b.reasons.map(([c]) => c), ['too_many_contact_cards']);
  assert.equal(b.count, 1);
});

test('a small count can still be over on bytes', () => {
  const fat = [{ text: 'x'.repeat(4000) }, { text: 'y'.repeat(4000) }];
  const b = budgetReport(fat, null, 5000);
  assert.equal(b.count, 2);
  assert.equal(b.verdict, 'reject');
  assert.equal(b.reasons[0][0], 'attachment_payload_limit_exceeded');
  assert.match(b.reasons[0][1], /not publish/);
});

test('the byte line is reported as the line this run used', () => {
  const b = budgetReport([{ text: 'x'.repeat(100) }], null, 9999);
  assert.equal(b.payloadBytes, 9999);
  assert.ok(b.bytes > 100);
});

test('inside the last fifth is a warning and not a rejection', () => {
  const b = budgetReport(many(85));
  assert.equal(b.verdict, 'at-risk');
  assert.equal(b.reasons[0][0], 'inside-the-last-fifth');
  assert.match(b.reasons[0][1], /busier day/);
});

test('a message with no attachments is not a finding', () => {
  const b = budgetReport(null);
  assert.equal(b.verdict, 'ok');
  assert.equal(b.count, 0);
  assert.deepEqual(b.reasons, [['no-attachments', 'nothing legacy here']]);
});

test('attachment size counts bytes rather than characters', () => {
  assert.equal(attachmentSize([{ text: 'abc' }]), '[{"text":"abc"}]'.length);
  assert.equal(attachmentSize([{ text: 'é' }]), '[{"text":"x"}]'.length + 1);
  const loop = [{}];
  loop[0].self = loop;
  assert.equal(attachmentSize(loop), -1);
});

test('mrkdwn without mrkdwn_in renders its own punctuation', () => {
  const found = smells({ text: '*3 deploys* failed' });
  assert.ok(found.has('mrkdwn-not-enabled'));
  assert.match(found.get('mrkdwn-not-enabled'), /render literally/);
  assert.ok(!smells({ text: '*3 deploys* failed', mrkdwn_in: ['text'] })
    .has('mrkdwn-not-enabled'));
  assert.ok(!smells({ text: '3 deploys failed' }).has('mrkdwn-not-enabled'));
});

test('a link in slack syntax counts as mrkdwn', () => {
  const found = smells({ pretext: 'see <https://ci.example.com/1|build 1>' });
  assert.ok(found.has('mrkdwn-not-enabled'));
  assert.match(found.get('mrkdwn-not-enabled'), /pretext/);
});

test('the colour bar is reported as a reason to keep it', () => {
  const found = smells({ color: 'good', text: 'ok' });
  assert.ok(found.has('colour-bar'));
  assert.match(found.get('colour-bar'), /reason to keep it/);
});

test('blocks inside an attachment are already migrated', () => {
  const found = smells({ color: '#36a64f', blocks: [{ type: 'divider' }] });
  assert.ok(found.has('blocks-inside'));
  assert.match(found.get('blocks-inside'), /only the colour bar is still legacy/);
});

test('legacy actions are named separately from the rest', () => {
  const found = smells({ actions: [{ type: 'button', text: 'Retry' }] });
  assert.ok(found.has('legacy-actions'));
  assert.match(found.get('legacy-actions'), /retired/);
});

test('a plain attachment is reported as costing nothing to move', () => {
  assert.ok(smells({ text: '3 deploys failed' }).has('plain'));
  assert.equal(legacySmells('not an object')[0][0], 'not-an-object');
});

test('the migration lands on the tighter ceiling', () => {
  const m = migrationCost(many(60));
  assert.equal(m.attachments, 60);
  assert.ok(m.blocksNeeded > 60);
  assert.equal(m.overBlockCeiling, true);
  assert.match(m.detail, /lands over it/);
});

test('a small fleet migrates without hitting the block ceiling', () => {
  const m = migrationCost(many(4));
  assert.equal(m.blocksNeeded, 7);
  assert.equal(m.overBlockCeiling, false);
  assert.match(m.detail, /fits/);
});

test('a fields grid costs one section per ten fields', () => {
  const fields = Array.from({ length: 25 }, (_, i) => ({ title: `${i}`, value: `${i}` }));
  assert.equal(migrationCost([{ text: 'summary', fields }]).blocksNeeded, 4);
});

test('an attachment that already holds blocks costs what it holds', () => {
  const a = { color: 'danger', text: 'ignored', blocks: Array(5).fill({ type: 'divider' }) };
  assert.equal(migrationCost([a]).blocksNeeded, 5);
});
''',
"faq": [
 ("Are attachments actually deprecated, or just old?",
  "Slack describes them as legacy and steers new work to Block Kit, and rendering of attachments is deprioritised in modern clients. They are not removed and are unlikely to be: an enormous amount of existing integration code emits them, and the coloured side bar has no Block Kit equivalent. Treat them as frozen rather than dying, which is why this note prices the migration instead of assuming it."),
 ("Why does my formatting inside an attachment not work?",
  "Because mrkdwn inside an attachment is opt-in. Slack only parses the fields you name in mrkdwn_in, so a bold marker in text renders as an asterisk unless you send mrkdwn_in with text in it. The script flags every attachment where a field contains mrkdwn syntax and is not named, which in most workspaces is the finding people fix first because it is visible in the channel right now."),
 ("Can I keep the coloured bar and still use Block Kit?",
  "Yes, and it is the usual answer. Put a blocks array inside the attachment: the content is then Block Kit and the attachment is doing nothing except carrying the colour. The script reports that as blocks-inside rather than as a fault, because it is the migrated state rather than a step short of it. The block ceiling still applies to what is inside."),
 ("Is the byte ceiling a real number I can code against?",
  "Not a published one. Slack returns attachment_payload_limit_exceeded without documenting the threshold, and the figure this script compares against is a conservative default rather than a documented limit. That is why the report always prints the measured size and names the line it used: the measurement is what transfers between workspaces, and the threshold is what you adjust once you have seen your own refusal."),
 ("Does the 50-block limit apply to my attachments too?",
  "The ceilings are separate and both are live in the same message. That is the whole reason this note exists beside the block one: a payload can be refused for attachments while sitting at four blocks, and an audit that only counts blocks reports a clean bill of health on it. Once you migrate, the block ceiling is the one that binds, and it is half the size."),
],
"related": [
 ("/slack/msg-blocks-too-long/", "the ceiling on the surface you would migrate to, and it is smaller"),
 ("/slack/blocks-without-text-fallback/", "the fallback string, one level down inside an attachment"),
 ("/slack/invalid-blocks/", "when the payload is refused for its shape rather than its size"),
],
"citations": [CITE_POSTMESSAGE, CITE_FORMATTING, CITE_BLOCKS, CITE_CONV_HISTORY],
})

GUIDES.append({
"slug": "no-text-empty-message",
"title": "no_text: the message that rendered to nothing",
"description": "A zero row query renders an empty string, the send is refused with no_text, and the only symptom is a report that did not arrive. Guard it before you send.",
"h1": "no_text: the message that rendered to nothing",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": [
    "slack no_text error",
    "slack chat.postMessage no_text",
    "slack empty message rejected",
    "slack bot posts nothing when no results",
    "slack message builder empty string",
],
"deps": "Python 3.9+ with requests, or Node.js 18+; no token at all if you check a payload file",
"lead": "The digest has run every morning for a year. This morning it returned <code>{\"ok\": false, \"error\": \"no_text\"}</code>, and the only thing different about this morning is that the query it runs returned zero rows.</p><p>The formatter joins those rows into a string. Zero rows join into an empty string. The empty string is passed to <code>chat.postMessage</code>, which requires the message to carry <em>something</em>, and refuses it. Nothing is delivered, and the symptom is a report that did not arrive, which is a symptom nobody notices until they go looking for a report they had stopped expecting.",
"short_answer": """<p><code>chat.postMessage</code> requires at least one of <code>text</code>, <code>blocks</code> or <code>attachments</code> to actually carry content. An empty <code>text</code> beside an empty <code>blocks: []</code> is refused with <code>no_text</code>, and nothing is delivered at all.</p>
<p>This is a rejection, not a degradation. The message never reaches the channel, never appears in history, and never notifies anybody, so unlike most message-quality problems there is no artefact left behind to inspect. The evidence is in your logs and in the absence of a post.</p>
<p>The path is almost always the same: a builder concatenates results, the result set is empty, and the "no results" case is the one nobody wrote a fixture for. So the script decides the question from the payload before the call, and separates it from the neighbouring case that <em>does</em> get through - a payload that is structurally present and holds no words, which Slack accepts and a reader sees as a heading over nothing.</p>""",
"problem": """<p>The reason this survives review is that the empty case is invisible in every environment where anybody looks. In development the query has fixtures in it. In staging somebody seeded data. In production it has rows on 364 days out of 365. The one day it does not is a Sunday of a long weekend, and the failure is a message that did not appear in a channel nobody is reading that day.</p>
<p>When it is noticed, it is noticed as a gap. "Did the digest run?" is not a bug report, and the answer is usually that the digest ran perfectly, computed correctly that there was nothing to report, and was refused when it tried to say so. The exit code is non-zero and the log line exists, but a cron job that fails one morning in three hundred is a cron job whose failures are filtered.</p>
<p>The repairs people reach for make it worse in an interesting way. Putting a space in the field silences the error, and now a blank message posts every quiet morning. Putting the word <code>update</code> in the field silences the error and posts the word <code>update</code>. Emitting a header block with nothing under it silences the error, because a header carries text, and posts a heading over nothing - a message that is delivered, occupies the channel, and says less than nothing. Each of these turns a loud failure into a quiet one, which is the wrong direction.</p>
<p>And underneath, the question nobody asks: should this message exist at all? A daily digest that posts "no results" every quiet day teaches its channel that most of its messages are noise, which is exactly how a channel stops being read before the day the digest has something important to say.</p>""",
"why": """<p><strong>A rejection and a degradation are two different notes and the script has to say which.</strong> Nothing delivered is a different afternoon from delivered and unreadable. The census returns <code>rejected</code>, <code>hollow</code> or <code>carries</code>, and only the first of those is <code>no_text</code>. Collapsing them into "empty" sends somebody looking for an error that, for the hollow case, was never raised.</p>
<p><strong>Structural presence is not content.</strong> <code>blocks: [{"type": "divider"}]</code> is a valid, accepted, delivered message that says nothing. So is a header with no body. The script walks the blocks for readable characters rather than checking whether the array is non-empty, because the empty-render bug frequently escapes by being structurally correct.</p>
<p><strong>Invisible characters are the standard workaround and have to be stripped first.</strong> A zero-width space in <code>text</code> makes <code>no_text</code> stop happening. It is present, it is non-empty, it passes every check anybody writes, and it makes the message worse. The census removes those characters before it decides anything.</p>
<p><strong>Skipping is a legitimate output, and usually the right one.</strong> The guard returns <code>skip</code> by default rather than a substitute string, because a channel that receives "nothing happened" every quiet morning stops reading the channel. Making the builder return <code>None</code> and the sender treat <code>None</code> as a no-op closes the whole class.</p>
<p><strong>Your own history holds the proof.</strong> A hollow post is the empty path having already run and got through by a hair. Finding three of them last month is evidence that the generator can emit nothing, which is a much stronger argument for a guard than an error string from one morning.</p>
<p><strong>Nothing is sent.</strong> Reproducing <code>no_text</code> by sending it means running the generator against a live workspace on the day it renders empty, and that is the same day it would post the empty message if the guard were wrong. With <code>--payload</code> the script holds no token.</p>""",
"steps": [
 {"h": "Take the census of the payload you were about to send",
  "body": """<p><code>content_census</code> asks which of <code>text</code>, <code>blocks</code> and <code>attachments</code> is carrying readable characters, and returns <code>rejected</code>, <code>hollow</code> or <code>carries</code> with the reason. Run it with <code>--payload</code> and no token.</p>"""},
 {"h": "Separate the refusal from the message that gets through empty",
  "body": """<p><code>rejected</code> means Slack answers <code>no_text</code> and delivers nothing. <code>hollow</code> means Slack accepts it and the reader gets a rule or a heading over nothing. These want different repairs and only one of them appears in your error log.</p>"""},
 {"h": "Strip the invisible characters before deciding anything",
  "body": """<p>A zero-width space, a word joiner and a byte order mark are all present and all silent. The census removes them first, which is why a payload that passes every presence check in your codebase can still come back <code>rejected</code> here.</p>"""},
 {"h": "Look for the heading with nothing under it",
  "body": """<p>A header block carries text, so it satisfies the API. It is also the exact shape of a zero-row render when the heading was appended before the loop that never ran. The census names that case specifically rather than calling it content.</p>"""},
 {"h": "Let the guard choose to say nothing",
  "body": """<p><code>guard_decision</code> returns <code>skip</code>, <code>substitute</code> or <code>send</code>. <code>skip</code> is the default because it is usually correct: nobody wants a daily ping that says nothing happened. <code>substitute</code> exists for the cases where the quiet day genuinely is the news.</p>"""},
 {"h": "Prove the empty path exists using your own history",
  "body": """<p>With a token and <code>--channel</code>, <code>hollow_history</code> counts the posts your app has already made that carry nothing a reader can read. Each one is the same code path, on a day it produced slightly more than nothing.</p>"""},
],
"verify": """<p>Add the guard, run the same empty fixture, and the script should report the skip rather than the rejection - without a call being made.</p>
<pre><code class="language-bash">python3 slack_empty_message.py --payload monday-digest.json
# census     rejected   no text field, no blocks and no attachments; chat.postMessage
#                       answers no_text and nothing is delivered
# guard      skip       nothing to say, so say nothing; the builder should return None
#                       and the sender should treat None as a no-op
#   repair: return None from the message builder when the body renders empty, and have
#           the sender treat None as a no-op</code></pre>""",
"code_intro": "Three pure functions and a recursive walk. <code>content_census</code> is the whole note: it asks which carrier holds readable characters and returns the three outcomes that need three different repairs. <code>guard_decision</code> is the repair expressed as a function, and its default is to send nothing at all, which is the answer people arrive at last and should have arrived at first. <code>hollow_history</code> finds the successful siblings of the failing send in your own channel, because an error from one morning argues less well than three posts that say nothing.",
"py_file": "slack_empty_message.py",
"py": '''"""Decide whether a message carries anything at all before you try to send it.

Read only. With --payload it holds no token and calls no Slack method; with
--channel it reads conversations.history and looks for the successful siblings
of the failing case, which are the posts your generator emitted on a day it had
almost nothing to say. Nothing is sent from here: reproducing no_text by sending
it is how you learn that the day the template renders empty is also the day it
renders empty into a customer channel.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_empty_message")

API = "https://slack.com/api/"

# Occupies the array, is accepted by the API, and shows the reader a rule.
WORDLESS = {"divider"}
# A label for content rather than content. A heading with nothing under it is
# the shape a zero row render takes when the heading was built before the loop,
# and it is the one empty message the API is perfectly happy with.
LABEL_ONLY = {"header"}

# Present, and not a message. The "no results" render arrives as one of these
# more often than as a bare empty string, because somebody put a character in
# the field to make the rejection stop.
INVISIBLE = "\\u200b\\u200c\\u200d\\u2060\\ufeff"

# Where a text object hides. Walked by key rather than by block shape so a new
# block type does not silently read as empty.
TEXT_KEYS = ("text", "value", "alt_text", "title")


def _clean(text):
    """Collapse to what is left after the invisible characters go. Pure."""
    if text is None:
        return ""
    out = str(text)
    for ch in INVISIBLE:
        out = out.replace(ch, " ")
    return re.sub(r"\\s+", " ", out).strip()


def _words(node):
    """Every readable character under a block or a list of them. Pure."""
    found = []

    def walk(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key in TEXT_KEYS and isinstance(value, str):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(item, list):
            for entry in item:
                walk(entry)

    walk(node)
    return _clean(" ".join(found))


def _body_words(blocks):
    """The words outside the headings and the rules. Pure.

    A heading is a label for a body. If the body is missing, the message reads
    as a title with nothing under it, which is exactly what a zero row render
    looks like when the heading was appended before the loop that never ran.
    """
    body = [b for b in (blocks or [])
            if isinstance(b, dict) and b.get("type") not in (LABEL_ONLY | WORDLESS)]
    return _words(body)


def content_census(text=None, blocks=None, attachments=None):
    """Say which of the three carriers is carrying something. Pure.

    Returns (verdict, carriers, detail). The three verdicts are outcomes rather
    than degrees of one thing:

      rejected  no carrier holds content, so chat.postMessage answers no_text
                and nothing is delivered at all
      hollow    a carrier is present and holds no body, so the send succeeds
                and the reader is shown a rule or a heading over nothing
      carries   there is something to read
    """
    body = _clean(text)
    block_list = blocks if isinstance(blocks, list) else []
    attach_list = attachments if isinstance(attachments, list) else []
    block_text = _words(block_list)
    attach_text = _clean(" ".join(
        " ".join(str(a.get(k) or "") for k in ("text", "pretext", "title", "fallback"))
        for a in attach_list if isinstance(a, dict)))

    carriers = []
    if body:
        carriers.append("text")
    if block_text:
        carriers.append("blocks")
    if attach_text:
        carriers.append("attachments")

    if not carriers:
        if not block_list and not attach_list:
            if text is None:
                got = "no text field"
            elif str(text) == "":
                got = "an empty text field"
            else:
                got = ("text of %d invisible or whitespace character(s)"
                       % len(str(text)))
            return ("rejected", [],
                    "%s, no blocks and no attachments; chat.postMessage answers "
                    "no_text and nothing is delivered" % got)
        present = ", ".join(x for x in
                            ("blocks[%d]" % len(block_list) if block_list else "",
                             "attachments[%d]" % len(attach_list) if attach_list else "")
                            if x)
        return ("hollow", [],
                "%s present and holding no words; the send succeeds and there is "
                "nothing to read" % present)

    if block_list and not _body_words(block_list):
        kinds = sorted({b.get("type") for b in block_list if isinstance(b, dict)})
        if set(kinds) <= LABEL_ONLY:
            return ("hollow", carriers,
                    "a heading and nothing under it, which is what a zero row render "
                    "looks like when the heading was built before the loop")
        return ("hollow", carriers,
                "%d block(s), all of them %s; the send succeeds and the reader is "
                "shown a rule" % (len(block_list), " and ".join(kinds)))

    return ("carries", carriers, "carried by %s" % ", ".join(carriers))


def guard_decision(rendered=None, blocks=None, window=None, announce_empty=False):
    """The three honest things to do with a body that came out empty. Pure.

    skip is the default and is usually right. A digest that posts "nothing
    happened" every quiet morning teaches a channel to ignore it, and that
    costs more than the message it was trying not to miss.
    """
    verdict, _carriers, _detail = content_census(rendered, blocks, None)
    if verdict == "carries":
        return ("send", "the body has content")
    if announce_empty:
        return ("substitute", "No results for %s" % (window or "the window"))
    return ("skip", "nothing to say, so say nothing; the builder should return None "
                    "and the sender should treat None as a no-op")


def hollow_history(messages, bot_id="", bot_user=""):
    """Find the successful siblings of the send that failed. Pure.

    A hollow post is proof, in your own channel, that the generator has a path
    that produces nothing. The no_text rejection is that same path on a day it
    produced slightly less, so this count is a prediction rather than a
    complaint about the posts it found.
    """
    authored, hollow = 0, 0
    rows = []
    for m in messages or []:
        mine = ((bot_id and m.get("bot_id") == bot_id)
                or (bot_user and m.get("user") == bot_user)
                or not (bot_id or bot_user))
        if not mine:
            continue
        authored += 1
        verdict, carriers, detail = content_census(
            m.get("text"), m.get("blocks"), m.get("attachments"))
        if verdict == "carries":
            continue
        hollow += 1
        rows.append({"ts": m.get("ts"), "verdict": verdict, "detail": detail,
                     "carriers": carriers})
    proof = ("%d of %d posts carry nothing a reader can read, so the generator has an "
             "empty path and no_text is that path on a quieter day" % (hollow, authored)
             ) if hollow else ("%d post(s), all of them carrying something" % authored)
    return {"authored": authored, "hollow": hollow, "rows": rows, "proof": proof}


def _load(path):
    body = json.loads(open(path, encoding="utf-8").read())
    return body if isinstance(body, dict) else {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", help="a JSON file holding the message payload you "
                                      "were about to send; needs no token")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel your app posts into; repeatable")
    ap.add_argument("--limit", type=int, default=200, help="messages read per channel")
    ap.add_argument("--announce-empty", action="store_true",
                    help="show the substitute string rather than the skip")
    ap.add_argument("--window", default="the last 24 hours",
                    help="label for the substitute string")
    args = ap.parse_args()

    if args.payload:
        payload = _load(args.payload)
        verdict, carriers, detail = content_census(
            payload.get("text"), payload.get("blocks"), payload.get("attachments"))
        (log.info if verdict == "carries" else log.warning)(
            "census     %-10s %s", verdict, detail)
        if verdict == "carries":
            log.info("carriers   %s", ", ".join(carriers))
            return 0
        action, message = guard_decision(payload.get("text"), payload.get("blocks"),
                                         args.window, args.announce_empty)
        log.warning("guard      %-10s %s", action, message)
        log.warning("  repair: return None from the message builder when the body "
                    "renders empty, and have the sender treat None as a no-op")
        log.warning("  repair: if the quiet day is worth reporting, substitute an "
                    "explicit string; never send an empty one")
        return 1

    if not args.channel:
        log.error("pass --payload FILE, or --channel with a token in %s", args.token_env)
        return 2
    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history is enough)", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    bot_id, bot_user = who.get("bot_id") or "", who.get("user_id") or ""
    log.info("identity   %s in %s", bot_user, who.get("team"))

    findings = 0
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        h = hollow_history(body.get("messages") or [], bot_id, bot_user)
        (log.warning if h["hollow"] else log.info)("history    %s: %s", channel,
                                                   h["proof"])
        for row in h["rows"][:10]:
            log.warning("empty      ts=%-18s %-9s %s", row["ts"], row["verdict"],
                        row["detail"])
        findings += h["hollow"]

    if findings:
        log.warning("  repair: guard the send. A builder that can render an empty body "
                    "should return None, and the sender should not call the API at all")
        log.warning("  repair: add the zero row case to the tests. It is the one case "
                    "nobody writes a fixture for, and the only one that fails")
        return 1
    log.info("verdict    clear          every post of ours carries something to read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-empty-message.mjs",
"js": '''/**
 * Decide whether a message carries anything at all before you try to send it.
 *
 * Read only. With --payload it holds no token and calls no Slack method; with
 * --channel it reads conversations.history and looks for the successful
 * siblings of the failing case. Nothing is sent from here: reproducing no_text
 * by sending it is how you learn that the day the template renders empty is
 * also the day it renders empty into a customer channel.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Occupies the array, is accepted by the API, and shows the reader a rule.
const WORDLESS = new Set(['divider']);
// A label for content rather than content. A heading with nothing under it is
// the shape a zero row render takes, and the one empty message the API likes.
const LABEL_ONLY = new Set(['header']);

// Present, and not a message. The "no results" render arrives as one of these
// more often than as a bare empty string.
const INVISIBLE = /[\\u200b\\u200c\\u200d\\u2060\\ufeff]/g;

// Where a text object hides. Walked by key rather than by block shape so a new
// block type does not silently read as empty.
const TEXT_KEYS = new Set(['text', 'value', 'alt_text', 'title']);

function clean(text) {
  if (text === null || text === undefined) return '';
  return String(text).replace(INVISIBLE, ' ').replace(/\\s+/g, ' ').trim();
}

/** Every readable character under a block or a list of them. Pure. */
function words(node) {
  const found = [];
  const walk = (item) => {
    if (Array.isArray(item)) {
      for (const entry of item) walk(entry);
    } else if (item && typeof item === 'object') {
      for (const [key, value] of Object.entries(item)) {
        if (TEXT_KEYS.has(key) && typeof value === 'string') found.push(value);
        else walk(value);
      }
    }
  };
  walk(node);
  return clean(found.join(' '));
}

/**
 * The words outside the headings and the rules. Pure.
 * A heading is a label for a body; with the body missing the message reads as
 * a title over nothing, which is what a zero row render looks like when the
 * heading was appended before the loop that never ran.
 */
function bodyWords(blocks) {
  const body = (blocks ?? []).filter(
    (b) => b && typeof b === 'object'
      && !LABEL_ONLY.has(b.type) && !WORDLESS.has(b.type));
  return words(body);
}

/**
 * Say which of the three carriers is carrying something. Pure.
 * Returns [verdict, carriers, detail]: rejected (no_text, nothing delivered),
 * hollow (delivered and unreadable) or carries.
 */
export function contentCensus(text = null, blocks = null, attachments = null) {
  const body = clean(text);
  const blockList = Array.isArray(blocks) ? blocks : [];
  const attachList = Array.isArray(attachments) ? attachments : [];
  const blockText = words(blockList);
  const attachText = clean(attachList
    .filter((a) => a && typeof a === 'object')
    .map((a) => ['text', 'pretext', 'title', 'fallback']
      .map((k) => String(a[k] ?? '')).join(' '))
    .join(' '));

  const carriers = [];
  if (body) carriers.push('text');
  if (blockText) carriers.push('blocks');
  if (attachText) carriers.push('attachments');

  if (!carriers.length) {
    if (!blockList.length && !attachList.length) {
      let got = 'no text field';
      if (text !== null && text !== undefined) {
        got = String(text) === ''
          ? 'an empty text field'
          : `text of ${String(text).length} invisible or whitespace character(s)`;
      }
      return ['rejected', [],
        `${got}, no blocks and no attachments; chat.postMessage answers no_text ` +
        'and nothing is delivered'];
    }
    const present = [
      blockList.length ? `blocks[${blockList.length}]` : '',
      attachList.length ? `attachments[${attachList.length}]` : '',
    ].filter(Boolean).join(', ');
    return ['hollow', [],
      `${present} present and holding no words; the send succeeds and there is ` +
      'nothing to read'];
  }

  if (blockList.length && !bodyWords(blockList)) {
    const kinds = [...new Set(blockList.filter((b) => b && typeof b === 'object')
      .map((b) => b.type))].sort();
    if (kinds.every((k) => LABEL_ONLY.has(k))) {
      return ['hollow', carriers,
        'a heading and nothing under it, which is what a zero row render looks ' +
        'like when the heading was built before the loop'];
    }
    return ['hollow', carriers,
      `${blockList.length} block(s), all of them ${kinds.join(' and ')}; the send ` +
      'succeeds and the reader is shown a rule'];
  }

  return ['carries', carriers, `carried by ${carriers.join(', ')}`];
}

/**
 * The three honest things to do with a body that came out empty. Pure.
 * skip is the default and is usually right: a digest that posts "nothing
 * happened" every quiet morning teaches a channel to ignore it.
 */
export function guardDecision(rendered = null, blocks = null, window = null,
  announceEmpty = false) {
  const [verdict] = contentCensus(rendered, blocks, null);
  if (verdict === 'carries') return ['send', 'the body has content'];
  if (announceEmpty) return ['substitute', `No results for ${window || 'the window'}`];
  return ['skip', 'nothing to say, so say nothing; the builder should return null '
    + 'and the sender should treat null as a no-op'];
}

/**
 * Find the successful siblings of the send that failed. Pure.
 * A hollow post is proof, in your own channel, that the generator has a path
 * that produces nothing; no_text is that path on a quieter day.
 */
export function hollowHistory(messages, botId = '', botUser = '') {
  let authored = 0;
  let hollow = 0;
  const rows = [];
  for (const m of messages ?? []) {
    const mine = (botId && m.bot_id === botId) || (botUser && m.user === botUser)
      || !(botId || botUser);
    if (!mine) continue;
    authored += 1;
    const [verdict, carriers, detail] = contentCensus(m.text, m.blocks, m.attachments);
    if (verdict === 'carries') continue;
    hollow += 1;
    rows.push({ ts: m.ts, verdict, detail, carriers });
  }
  const proof = hollow
    ? `${hollow} of ${authored} posts carry nothing a reader can read, so the `
      + 'generator has an empty path and no_text is that path on a quieter day'
    : `${authored} post(s), all of them carrying something`;
  return { authored, hollow, rows, proof };
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
  const payloadPath = arg(args, '--payload');
  const windowLabel = arg(args, '--window', 'the last 24 hours');
  const announce = args.includes('--announce-empty');

  if (payloadPath) {
    const payload = JSON.parse(await readFile(payloadPath, 'utf8'));
    const [verdict, carriers, detail] = contentCensus(
      payload.text, payload.blocks, payload.attachments);
    (verdict === 'carries' ? console.log : console.warn)(
      `census     ${verdict.padEnd(10)} ${detail}`);
    if (verdict === 'carries') {
      console.log(`carriers   ${carriers.join(', ')}`);
      return;
    }
    const [action, message] = guardDecision(
      payload.text, payload.blocks, windowLabel, announce);
    console.warn(`guard      ${action.padEnd(10)} ${message}`);
    console.warn('  repair: return null from the message builder when the body renders '
      + 'empty, and have the sender treat null as a no-op');
    console.warn('  repair: if the quiet day is worth reporting, substitute an explicit '
      + 'string; never send an empty one');
    process.exitCode = 1;
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error(`pass --payload FILE, or --channel with a token in ${tokenEnv}`);
    process.exitCode = 2;
    return;
  }
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history is enough)`);
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const botId = who.bot_id ?? '';
  const botUser = who.user_id ?? '';
  console.log(`identity   ${botUser} in ${who.team}`);

  let findings = 0;
  for (const channel of channels) {
    const url = `${API}conversations.history?channel=${encodeURIComponent(channel)}`
      + `&limit=${encodeURIComponent(limit)}`;
    const body = await (await fetch(url, { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    const h = hollowHistory(body.messages ?? [], botId, botUser);
    (h.hollow ? console.warn : console.log)(`history    ${channel}: ${h.proof}`);
    for (const row of h.rows.slice(0, 10)) {
      console.warn(`empty      ts=${String(row.ts).padEnd(18)} `
        + `${row.verdict.padEnd(9)} ${row.detail}`);
    }
    findings += h.hollow;
  }

  if (findings) {
    console.warn('  repair: guard the send. A builder that can render an empty body '
      + 'should return null, and the sender should not call the API at all');
    console.warn('  repair: add the zero row case to the tests. It is the one case '
      + 'nobody writes a fixture for, and the only one that fails');
    process.exitCode = 1;
    return;
  }
  console.log('verdict    clear          every post of ours carries something to read');
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertion that keeps this note distinct from its neighbour is that a heading over nothing comes back <code>hollow</code> while a payload with nothing anywhere comes back <code>rejected</code>: one is delivered and unreadable, the other never existed, and a checker that calls both of them empty has merged two different afternoons. The rest are about the workarounds. A zero-width space has to be stripped before the decision, an empty attachment object has to be hollow rather than a rejection, and a divider on its own has to be reported as a message that posts and says nothing rather than one that fails.",
"test_py_file": "test_slack_empty_message.py",
"test_js_file": "slack-empty-message.test.mjs",
"test_py": '''from slack_empty_message import content_census, guard_decision, hollow_history

SECTION = {"type": "section", "text": {"type": "mrkdwn", "text": "3 deploys failed"}}
HEADER = {"type": "header", "text": {"type": "plain_text", "text": "Nightly digest"}}
DIVIDER = {"type": "divider"}


def test_nothing_anywhere_is_the_rejection_this_note_is_about():
    verdict, carriers, detail = content_census(None, None, None)
    assert verdict == "rejected"
    assert carriers == []
    assert "no_text" in detail
    assert "nothing is delivered" in detail


def test_an_empty_string_beside_an_empty_blocks_array_is_still_rejected():
    verdict, _carriers, detail = content_census("", [], [])
    assert verdict == "rejected"
    assert detail.startswith("an empty text field")
    assert content_census("   ", [])[0] == "rejected"
    assert content_census(None)[2].startswith("no text field")


def test_a_field_holding_only_invisible_characters_is_reported_as_such():
    verdict, _carriers, detail = content_census("\\u200b\\ufeff")
    assert verdict == "rejected"
    assert "invisible or whitespace character(s)" in detail


def test_a_real_message_carries_and_names_its_carrier():
    verdict, carriers, detail = content_census("3 deploys failed", [SECTION])
    assert verdict == "carries"
    assert carriers == ["text", "blocks"]
    assert detail == "carried by text, blocks"
    assert content_census(None, [SECTION])[1] == ["blocks"]


def test_blocks_present_and_wordless_are_delivered_and_unreadable():
    verdict, carriers, detail = content_census(None, [DIVIDER, DIVIDER])
    assert verdict == "hollow"
    assert carriers == []
    assert "blocks[2]" in detail
    assert "the send succeeds" in detail


def test_a_heading_with_nothing_under_it_is_the_zero_row_render():
    verdict, carriers, detail = content_census("Nightly digest", [HEADER])
    assert verdict == "hollow"
    assert carriers == ["text", "blocks"]
    assert "heading and nothing under it" in detail


def test_a_heading_over_a_rule_is_hollow_and_named_by_its_types():
    verdict, _carriers, detail = content_census("Nightly digest", [HEADER, DIVIDER])
    assert verdict == "hollow"
    assert "divider and header" in detail


def test_a_heading_over_a_real_section_is_a_message():
    assert content_census("Nightly digest", [HEADER, SECTION])[0] == "carries"


def test_an_attachment_can_be_the_only_carrier():
    verdict, carriers, _detail = content_census(
        None, None, [{"fallback": "3 deploys failed"}])
    assert verdict == "carries"
    assert carriers == ["attachments"]


def test_an_empty_attachment_object_is_hollow_rather_than_rejected():
    verdict, _carriers, detail = content_census(None, None, [{}])
    assert verdict == "hollow"
    assert "attachments[1]" in detail


def test_the_guard_skips_by_default_because_silence_is_usually_right():
    action, message = guard_decision("", None)
    assert action == "skip"
    assert "no-op" in message
    assert guard_decision("   \\u200b  ")[0] == "skip"


def test_the_guard_substitutes_only_when_the_quiet_day_is_worth_saying():
    action, message = guard_decision("", None, "the last 24 hours", True)
    assert action == "substitute"
    assert message == "No results for the last 24 hours"
    assert guard_decision("", None, None, True)[1] == "No results for the window"


def test_the_guard_sends_a_body_that_has_something_in_it():
    action, message = guard_decision("3 deploys failed")
    assert action == "send"
    assert message == "the body has content"
    assert guard_decision(None, [SECTION])[0] == "send"


def test_history_counts_the_hollow_posts_as_proof_of_the_empty_path():
    messages = [
        {"ts": "1", "bot_id": "B1", "text": "3 deploys failed", "blocks": [SECTION]},
        {"ts": "2", "bot_id": "B1", "text": "Nightly digest", "blocks": [HEADER]},
        {"ts": "3", "bot_id": "B1", "blocks": [DIVIDER]},
        {"ts": "4", "user": "U9", "text": "a human"},
    ]
    h = hollow_history(messages, bot_id="B1")
    assert h["authored"] == 3
    assert h["hollow"] == 2
    assert [r["ts"] for r in h["rows"]] == ["2", "3"]
    assert "empty path" in h["proof"]


def test_history_with_nothing_hollow_says_so_without_a_finding():
    h = hollow_history([{"ts": "1", "bot_id": "B1", "text": "3 deploys failed"}],
                       bot_id="B1")
    assert h["hollow"] == 0
    assert h["rows"] == []
    assert "all of them carrying something" in h["proof"]


def test_an_empty_channel_is_not_a_finding():
    h = hollow_history([], bot_id="B1")
    assert h["authored"] == 0
    assert h["hollow"] == 0
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  contentCensus, guardDecision, hollowHistory,
} from './slack-empty-message.mjs';

const SECTION = { type: 'section', text: { type: 'mrkdwn', text: '3 deploys failed' } };
const HEADER = { type: 'header', text: { type: 'plain_text', text: 'Nightly digest' } };
const DIVIDER = { type: 'divider' };

test('nothing anywhere is the rejection this note is about', () => {
  const [verdict, carriers, detail] = contentCensus(null, null, null);
  assert.equal(verdict, 'rejected');
  assert.deepEqual(carriers, []);
  assert.match(detail, /no_text/);
  assert.match(detail, /nothing is delivered/);
});

test('an empty string beside an empty blocks array is still rejected', () => {
  const [verdict, , detail] = contentCensus('', [], []);
  assert.equal(verdict, 'rejected');
  assert.ok(detail.startsWith('an empty text field'));
  assert.equal(contentCensus('   ', [])[0], 'rejected');
  assert.ok(contentCensus(null)[2].startsWith('no text field'));
});

test('a field holding only invisible characters is reported as such', () => {
  const [verdict, , detail] = contentCensus('\\u200b\\ufeff');
  assert.equal(verdict, 'rejected');
  assert.match(detail, /invisible or whitespace character\\(s\\)/);
});

test('a real message carries and names its carrier', () => {
  const [verdict, carriers, detail] = contentCensus('3 deploys failed', [SECTION]);
  assert.equal(verdict, 'carries');
  assert.deepEqual(carriers, ['text', 'blocks']);
  assert.equal(detail, 'carried by text, blocks');
  assert.deepEqual(contentCensus(null, [SECTION])[1], ['blocks']);
});

test('blocks present and wordless are delivered and unreadable', () => {
  const [verdict, carriers, detail] = contentCensus(null, [DIVIDER, DIVIDER]);
  assert.equal(verdict, 'hollow');
  assert.deepEqual(carriers, []);
  assert.match(detail, /blocks\\[2\\]/);
  assert.match(detail, /the send succeeds/);
});

test('a heading with nothing under it is the zero row render', () => {
  const [verdict, carriers, detail] = contentCensus('Nightly digest', [HEADER]);
  assert.equal(verdict, 'hollow');
  assert.deepEqual(carriers, ['text', 'blocks']);
  assert.match(detail, /heading and nothing under it/);
});

test('a heading over a rule is hollow and named by its types', () => {
  const [verdict, , detail] = contentCensus('Nightly digest', [HEADER, DIVIDER]);
  assert.equal(verdict, 'hollow');
  assert.match(detail, /divider and header/);
});

test('a heading over a real section is a message', () => {
  assert.equal(contentCensus('Nightly digest', [HEADER, SECTION])[0], 'carries');
});

test('an attachment can be the only carrier', () => {
  const [verdict, carriers] = contentCensus(null, null, [{ fallback: '3 deploys failed' }]);
  assert.equal(verdict, 'carries');
  assert.deepEqual(carriers, ['attachments']);
});

test('an empty attachment object is hollow rather than rejected', () => {
  const [verdict, , detail] = contentCensus(null, null, [{}]);
  assert.equal(verdict, 'hollow');
  assert.match(detail, /attachments\\[1\\]/);
});

test('the guard skips by default because silence is usually right', () => {
  const [action, message] = guardDecision('', null);
  assert.equal(action, 'skip');
  assert.match(message, /no-op/);
  assert.equal(guardDecision('   \\u200b  ')[0], 'skip');
});

test('the guard substitutes only when the quiet day is worth saying', () => {
  const [action, message] = guardDecision('', null, 'the last 24 hours', true);
  assert.equal(action, 'substitute');
  assert.equal(message, 'No results for the last 24 hours');
  assert.equal(guardDecision('', null, null, true)[1], 'No results for the window');
});

test('the guard sends a body that has something in it', () => {
  const [action, message] = guardDecision('3 deploys failed');
  assert.equal(action, 'send');
  assert.equal(message, 'the body has content');
  assert.equal(guardDecision(null, [SECTION])[0], 'send');
});

test('history counts the hollow posts as proof of the empty path', () => {
  const messages = [
    { ts: '1', bot_id: 'B1', text: '3 deploys failed', blocks: [SECTION] },
    { ts: '2', bot_id: 'B1', text: 'Nightly digest', blocks: [HEADER] },
    { ts: '3', bot_id: 'B1', blocks: [DIVIDER] },
    { ts: '4', user: 'U9', text: 'a human' },
  ];
  const h = hollowHistory(messages, 'B1');
  assert.equal(h.authored, 3);
  assert.equal(h.hollow, 2);
  assert.deepEqual(h.rows.map((r) => r.ts), ['2', '3']);
  assert.match(h.proof, /empty path/);
});

test('history with nothing hollow says so without a finding', () => {
  const h = hollowHistory([{ ts: '1', bot_id: 'B1', text: '3 deploys failed' }], 'B1');
  assert.equal(h.hollow, 0);
  assert.deepEqual(h.rows, []);
  assert.match(h.proof, /all of them carrying something/);
});

test('an empty channel is not a finding', () => {
  const h = hollowHistory([], 'B1');
  assert.equal(h.authored, 0);
  assert.equal(h.hollow, 0);
});
''',
"faq": [
 ("Is no_text the same problem as sending blocks with no text field?",
  "No, and they are worth keeping apart. no_text is a rejection: nothing in the payload carries content, so nothing is delivered. Blocks without a text fallback is a success: the message is delivered and rendered correctly, and only the notification surfaces degrade. The first leaves an error and no message; the second leaves a message and no error. They have separate notes for that reason."),
 ("Can I just put a space in the text field to make the error stop?",
  "It does make the error stop, and that is the problem. A space or a zero-width space satisfies the API, so an empty digest now posts successfully and shows a reader nothing at all. The script strips those characters before it judges anything precisely because they are the standard workaround, and a payload that passes every presence check in your codebase can still come back rejected here."),
 ("Should the job post something on a quiet day, or nothing?",
  "Usually nothing. A channel that receives a daily message saying nothing happened learns that most messages from that app are noise, and stops reading it before the day something does happen. Skip the send, and let the absence be the signal. Substitute an explicit string only where the quiet day is genuinely news, such as a compliance check that has to record that it ran."),
 ("Why is a header block with nothing under it flagged?",
  "Because it is the shape a zero-row render takes when the heading was built before the loop. Slack accepts it, since a header carries text, so it never appears in your error log; a reader gets a title over nothing. It is the one empty message the API is perfectly happy with, and the only place it shows up is in the channel."),
 ("How can a message be empty and still be in my history?",
  "Because only the total absence of content is refused. A divider is a valid block, an empty attachment object is a valid attachment, and a header is a valid block that carries text, so all three post successfully. Those posts are the same code path as the failing one on a day it produced marginally more, which is why the script counts them: they are proof the empty path exists."),
],
"related": [
 ("/slack/blocks-without-text-fallback/", "the message that has content and still notifies as nothing"),
 ("/slack/http-200-ok-false/", "why the rejection arrives as a 200 and reads as a success"),
 ("/slack/duplicate-messages-no-dedupe/", "the other message quality problem your own history proves"),
],
"citations": [CITE_POSTMESSAGE, CITE_CONV_HISTORY, CITE_BLOCK_KIT, CITE_WEB_API],
})

GUIDES.append({
"slug": "cannot-reply-to-message",
"title": "cannot_reply_to_message: the parent stopped taking replies",
"description": "The thread_ts you stored weeks ago points at a message somebody deleted or locked. Read each stored parent once before you thread under it again.",
"h1": "cannot_reply_to_message: the parent stopped taking replies",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": [
    "slack cannot_reply_to_message",
    "slack thread_not_found",
    "slack restricted_action_thread_locked",
    "slack reply to deleted message tombstone",
    "slack stored thread_ts no longer works",
],
"deps": "Python 3.9+ with requests, or Node.js 18+; channels:history on the channels holding your stored parents",
"lead": "The deploy bot has threaded every status update under the same parent message for three weeks. This morning it returned <code>{\"ok\": false, \"error\": \"cannot_reply_to_message\"}</code> for every update, and the channel is fine, the bot is in it, and the token is valid.</p><p>Somebody deleted the parent yesterday while cleaning up. Slack left a tombstone in its place, which holds the position in the channel and cannot hold a reply. Nothing in your code changed; the thing your code was pointing at did.",
"short_answer": """<p><code>cannot_reply_to_message</code> means the specific message you passed as <code>thread_ts</code> cannot host a reply. The usual reasons are that it was deleted and Slack left a <code>tombstone</code> where it was, that an administrator locked the thread (which also surfaces as <code>restricted_action_thread_locked</code>), or that the message is one of the subtypes - joins and leaves among them - that never hosted threads.</p>
<p>This is about <strong>one message</strong>, not about the channel. A channel that forbids top-level posts or forbids threading entirely is a different problem with a different repair, and it applies to every message in the channel rather than to the one you stored.</p>
<p>The whole state is readable: <code>conversations.replies</code> with <code>limit=1</code> against the stored <code>thread_ts</code> answers with the parent, or with an error that names why it cannot. So the check is one read per stored parent, run before the reply rather than after the refusal - and no reply is ever sent, because a reply is a write and a script that tests whether a thread accepts replies by posting one has already posted one.</p>""",
"problem": """<p>The mechanism is that a <code>ts</code> is a reference to something you do not control. It goes into a config file, a database column or an environment variable, and from that moment it is a pointer to a message any member of the channel can delete, any administrator can lock, and any retention policy can remove. Nothing notifies you. The reference simply stops resolving, weeks after anybody touched the code that wrote it.</p>
<p>Deletion is the common one and it is the least obvious, because the message does not vanish from the channel. Slack leaves a tombstone: the position stays, the content is replaced, and to a reader scrolling past it is clearly "this message was deleted". To an integration, it is a <code>ts</code> that still exists, still returns from a read, and refuses every reply.</p>
<p>Locking is rarer and reads completely differently in the logs. An administrator locks a thread on a heated incident, and now every automated update to that incident is refused. The repair is not in your code and not in your reach: it needs a person with the permission to unlock it, or a new parent. Reporting that in the same bucket as a deleted message sends somebody to the wrong place.</p>
<p>And the whole class is silent until it fires. A parent that has worked for three weeks proves nothing about the fourth. The only thing that separates a healthy pointer from a broken one is a read, and the read is cheap: one call, one message, one answer.</p>""",
"why": """<p><strong>The state belongs to the parent, not to the channel.</strong> Everything this script reports is about one message: is it there, is it a tombstone, is it locked, is it a type that can host a thread. The channel's own threading rules are a separate question with a separate answer, and mixing them produces a report where nobody can tell which of the two to fix.</p>
<p><strong>A read answers the whole question, so nothing needs to be sent.</strong> <code>conversations.replies</code> with a limit of one returns the parent or the reason it cannot. Testing this by replying puts a message under somebody's incident thread, and if the parent turns out to be fine, it stays there.</p>
<p><strong>Gone, locked and unreadable want three different people.</strong> A missing parent needs the code to establish a new one. A locked thread needs an administrator. An error like <code>not_in_channel</code> or <code>missing_scope</code> is the channel refusing the read and says nothing about the parent at all, so it is reported as unknown rather than as broken.</p>
<p><strong>The subtype table is deliberately short.</strong> Slack adds message subtypes. A subtype this script does not recognise is reported as unknown and never counted as a fault, because an audit that fails the day somebody upgrades a client is an audit that gets switched off within a week.</p>
<p><strong>Age is the mechanism, so age is reported.</strong> Nothing about a parent changes when it is created and everything can change while it sits in a config file. A parent that has been the parent for forty days is not broken, and it is the shape of the thing that breaks, so the script says so without calling it a failure.</p>
<p><strong>A reply used as a parent is somebody else's note.</strong> If the stored <code>ts</code> turns out to be a reply, this script hands it over rather than absorbing it, because that fault has no error attached and a completely different repair.</p>""",
"steps": [
 {"h": "Collect the parents your app actually threads under",
  "body": """<p>Every <code>thread_ts</code> in a config file, a database column or an environment variable. Pass them as <code>--parent CHANNEL:THREAD_TS</code> or in a JSON file. This list is usually shorter than people expect and longer than the one person who remembers it.</p>"""},
 {"h": "Read each one once, with a limit of one",
  "body": """<p><code>conversations.replies?channel=...&amp;ts=...&amp;limit=1</code> is the whole check. It returns the parent message or an error naming why it cannot. No reply is sent, which matters when the parent turns out to be a live incident thread.</p>"""},
 {"h": "Read the tombstone as a deletion rather than a gap",
  "body": """<p>A deleted parent does not disappear. It comes back with <code>subtype: "tombstone"</code>, holding its position in the channel and unable to hold a reply. <code>parent_state</code> names it, because "the message is there and refuses replies" is otherwise a confusing sentence.</p>"""},
 {"h": "Keep a locked thread out of the broken bucket",
  "body": """<p><code>restricted_action_thread_locked</code> means an administrator closed the thread. The parent is healthy and the refusal is deliberate. This one needs a person rather than a retry, and putting it beside a deleted parent in the report loses that.</p>"""},
 {"h": "Report an unreadable channel as unknown, not as broken",
  "body": """<p><code>not_in_channel</code>, <code>missing_scope</code> and <code>channel_not_found</code> are the channel refusing the read. The parent's state is unknown, not bad. A checker that reports those as faults is one nobody trusts on private channels.</p>"""},
 {"h": "Give the stored parent a lifetime",
  "body": """<p><code>stale_root</code> reports how long each ts has been the parent. Nothing is wrong with an old parent and everything that goes wrong here goes wrong to old parents, so store one with an expiry and establish a new one rather than holding a pointer forever.</p>"""},
],
"verify": """<p>Establish a new parent, run the check again, and every row should come back usable before a single reply is attempted.</p>
<pre><code class="language-bash">python3 slack_thread_parent.py --parent C01ABCDE9:1735689600.000100
# identity   U0APPBOT11 in acme
# parent     tombstone        C01ABCDE9:17356...  the parent was deleted and Slack left a
#                             tombstone; a tombstone holds the position in the channel
#                             and cannot hold a reply
# age        aging            C01ABCDE9:17356... has been the parent for 21.4 day(s)
# roll call  1 parent(s): 0 usable, 1 broken, 0 unreadable
#   repair: read the parent with conversations.replies before you thread under it, and
#           post at the top level when the read fails</code></pre>""",
"code_intro": "Three pure functions and one read per parent. <code>parent_state</code> turns a single <code>conversations.replies</code> answer into what a reply would do, and its job is mostly restraint: an unrecognised subtype is unknown, an unreadable channel is unknown, and a reply used as a root is handed to the note next door. <code>stale_root</code> reports the age of the pointer, because age is the mechanism here rather than a symptom. <code>roll_call</code> sorts the results by who has to act on them, which is the ordering that decides whether anybody does.",
"py_file": "slack_thread_parent.py",
"py": '''"""Check every thread_ts your app still replies under before it replies again.

Read only. conversations.replies with limit 1 per stored parent, and nothing
else: a reply is a write, and a script that finds out whether a thread accepts
replies by posting one has already put a test message under somebody's incident.
The parent either answers as a usable root or it does not, and both answers come
back from a read.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_thread_parent")

API = "https://slack.com/api/"

# The parent is not there any more. Both spellings turn up depending on how the
# message went away, and they mean the same thing for a reply.
GONE = {"thread_not_found", "message_not_found"}
# The channel is refusing the read for a reason that has nothing to do with the
# parent, so the parent's state is unknown rather than bad. Reporting these as
# faults is how a checker starts crying wolf on private channels.
UNREADABLE = {"channel_not_found", "not_in_channel", "missing_scope",
              "not_allowed_token_type", "invalid_auth", "access_denied"}
# The thread exists and is closed to new replies by an administrator.
LOCKED = {"restricted_action_thread_locked"}

# Subtypes that cannot host a reply. Deliberately short: an unrecognised
# subtype is reported as unknown and never as a fault, because a checker that
# fails on a subtype Slack added last month is a checker that gets switched off.
NOT_THREADABLE = {"tombstone", "channel_join", "channel_leave", "group_join",
                  "group_leave"}

# A ts stored this long ago is a ts nobody has looked at. Days, and adjustable,
# because the right number is however long your parent is expected to live.
DEFAULT_TTL_DAYS = 7


def parent_state(error="", parent=None):
    """Turn one conversations.replies answer into what a reply would do. Pure.

    Returns (state, detail). The states are gone, locked, tombstone,
    not-threadable, not-a-root, unreadable, unknown-subtype and usable, and
    only the first four are this note's fault. not-a-root belongs to the note
    next door and is handed over rather than absorbed.
    """
    error = (error or "").strip()
    if error:
        if error in GONE:
            return ("gone", "conversations.replies answers %s: the parent is no longer "
                            "there, so cannot_reply_to_message is what a reply gets"
                            % error)
        if error in LOCKED:
            return ("locked", "the thread is locked by an administrator; replies are "
                              "refused for everyone, including your app")
        if error in UNREADABLE:
            return ("unreadable", "%s: the channel is refusing the read, so the "
                                  "parent's state is unknown rather than bad" % error)
        return ("unknown-error", "%s, which this table does not have a rule for; read "
                                 "it before treating the parent as broken" % error)

    if not isinstance(parent, dict) or not parent.get("ts"):
        return ("gone", "the reply list came back with no parent message in it")

    subtype = parent.get("subtype") or ""
    if subtype == "tombstone":
        return ("tombstone", "the parent was deleted and Slack left a tombstone; a "
                             "tombstone holds the position in the channel and cannot "
                             "hold a reply")
    if subtype in NOT_THREADABLE:
        return ("not-threadable", "the parent is a %s message, which is one of the "
                                  "types that cannot host a thread" % subtype)

    thread_ts = parent.get("thread_ts")
    if thread_ts and thread_ts != parent.get("ts"):
        return ("not-a-root", "this ts is a reply inside thread %s rather than a "
                              "thread root; Slack will accept the reply and move it, "
                              "which is a different problem" % thread_ts)
    if subtype:
        return ("unknown-subtype", "subtype %r is not in this table; the parent looks "
                                   "usable and the subtype is reported rather than "
                                   "judged" % subtype)
    return ("usable", "the parent is present, is a root, and can take a reply")


def stale_root(thread_ts, now=None, ttl_days=DEFAULT_TTL_DAYS):
    """How long the app has been threading under the same parent. Pure.

    Age is the mechanism rather than a symptom: nothing about a parent changes
    when it is created, and everything can change while it sits in a config
    file. Returns (state, age_days).
    """
    try:
        created = float(str(thread_ts).split(".")[0])
    except (TypeError, ValueError):
        return ("unparseable", -1.0)
    now = float(now if now is not None else time.time())
    exact = (now - created) / 86400.0
    # Rounded for the report and compared unrounded, so a parent one second in
    # the future is not rounded into the present.
    age = round(exact, 2)
    if exact < 0:
        return ("in-the-future", age)
    if exact >= ttl_days * 2:
        return ("stale", age)
    if exact >= ttl_days:
        return ("aging", age)
    return ("fresh", age)


def roll_call(results):
    """Sort a set of stored parents into what to do about each. Pure.

    The ordering matters: a parent that is gone needs a new parent, a locked
    one needs a person, and an unreadable one needs a scope. Reporting them as
    one number sends somebody to fix the wrong thing.
    """
    order = ["gone", "tombstone", "not-threadable", "locked", "not-a-root",
             "unknown-error", "unreadable", "unknown-subtype", "usable"]
    buckets = {}
    for r in results or []:
        buckets.setdefault(r.get("state", "unknown-error"), []).append(r)
    broken = sum(len(buckets.get(k, [])) for k in
                 ("gone", "tombstone", "not-threadable", "locked"))
    return {
        "total": sum(len(v) for v in buckets.values()),
        "broken": broken,
        "usable": len(buckets.get("usable", [])),
        "ambiguous": len(buckets.get("unreadable", [])),
        "order": [k for k in order if k in buckets],
        "buckets": buckets,
    }


def _stored(args):
    """The parents to check: from a file, or from repeated --parent flags."""
    out = []
    if args.parents:
        body = json.loads(open(args.parents, encoding="utf-8").read())
        for label, value in (body.items() if isinstance(body, dict)
                             else enumerate(body)):
            if isinstance(value, dict):
                out.append((str(label), value.get("channel"), value.get("thread_ts")))
            else:
                out.append((str(label), args.channel, str(value)))
    for pair in args.parent:
        channel, _, ts = pair.partition(":")
        out.append((pair, channel, ts))
    return [(label, c, t) for label, c, t in out if c and t]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--parent", action="append", default=[],
                    help="a stored parent as CHANNEL:THREAD_TS; repeatable")
    ap.add_argument("--parents", help="JSON file of stored parents")
    ap.add_argument("--channel", help="default channel for a bare ts in --parents")
    ap.add_argument("--ttl-days", type=int, default=DEFAULT_TTL_DAYS,
                    help="how long a stored parent is expected to stay usable")
    args = ap.parse_args()

    parents = _stored(args)
    if not parents:
        log.error("pass --parent CHANNEL:THREAD_TS or --parents FILE")
        return 2
    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history is enough)", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    results = []
    for label, channel, thread_ts in parents:
        body = s.get(API + "conversations.replies", timeout=30,
                     params={"channel": channel, "ts": thread_ts, "limit": "1"}).json()
        error = "" if body.get("ok") is True else (body.get("error") or "unknown")
        messages = body.get("messages") or []
        state, detail = parent_state(error, messages[0] if messages else None)
        age_state, age = stale_root(thread_ts, ttl_days=args.ttl_days)
        results.append({"label": label, "channel": channel, "ts": thread_ts,
                        "state": state, "detail": detail, "age": age,
                        "age_state": age_state})
        (log.info if state in ("usable", "unknown-subtype") else log.warning)(
            "parent     %-16s %-16s %s", state, label, detail)
        if age_state in ("aging", "stale"):
            log.warning("age        %-16s %s has been the parent for %.1f day(s)",
                        age_state, label, age)

    r = roll_call(results)
    log.info("roll call  %d parent(s): %d usable, %d broken, %d unreadable",
             r["total"], r["usable"], r["broken"], r["ambiguous"])
    if r["broken"]:
        log.warning("  repair: read the parent with conversations.replies before you "
                    "thread under it, and post at the top level when the read fails")
        log.warning("  repair: store the parent ts with a lifetime and establish a new "
                    "parent when the old one expires, rather than keeping one forever")
        log.warning("  repair: a locked thread needs a person rather than a retry; the "
                    "lock is an administrator decision and your app cannot lift it")
        return 1
    if r["ambiguous"]:
        log.warning("  note: %d parent(s) could not be read at all, which is a scope or "
                    "membership answer rather than a thread answer", r["ambiguous"])
    log.info("verdict    clear          every stored parent can still take a reply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-thread-parent.mjs",
"js": '''/**
 * Check every thread_ts your app still replies under before it replies again.
 *
 * Read only. conversations.replies with limit 1 per stored parent, and nothing
 * else: a reply is a write, and a script that finds out whether a thread
 * accepts replies by posting one has already put a test message under
 * somebody's incident.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// The parent is not there any more. Both spellings turn up depending on how
// the message went away, and they mean the same thing for a reply.
const GONE = new Set(['thread_not_found', 'message_not_found']);
// The channel is refusing the read for a reason that has nothing to do with
// the parent, so the parent's state is unknown rather than bad.
const UNREADABLE = new Set(['channel_not_found', 'not_in_channel', 'missing_scope',
  'not_allowed_token_type', 'invalid_auth', 'access_denied']);
// The thread exists and is closed to new replies by an administrator.
const LOCKED = new Set(['restricted_action_thread_locked']);

// Deliberately short: an unrecognised subtype is reported as unknown and never
// as a fault, because a checker that fails on a subtype Slack added last month
// is a checker that gets switched off.
const NOT_THREADABLE = new Set(['tombstone', 'channel_join', 'channel_leave',
  'group_join', 'group_leave']);

export const DEFAULT_TTL_DAYS = 7;

/**
 * Turn one conversations.replies answer into what a reply would do. Pure.
 * Returns [state, detail]. not-a-root belongs to the note next door and is
 * handed over rather than absorbed.
 */
export function parentState(error = '', parent = null) {
  const err = String(error ?? '').trim();
  if (err) {
    if (GONE.has(err)) {
      return ['gone', `conversations.replies answers ${err}: the parent is no longer `
        + 'there, so cannot_reply_to_message is what a reply gets'];
    }
    if (LOCKED.has(err)) {
      return ['locked', 'the thread is locked by an administrator; replies are refused '
        + 'for everyone, including your app'];
    }
    if (UNREADABLE.has(err)) {
      return ['unreadable', `${err}: the channel is refusing the read, so the parent's `
        + 'state is unknown rather than bad'];
    }
    return ['unknown-error', `${err}, which this table does not have a rule for; read `
      + 'it before treating the parent as broken'];
  }

  if (!parent || typeof parent !== 'object' || !parent.ts) {
    return ['gone', 'the reply list came back with no parent message in it'];
  }

  const subtype = parent.subtype ?? '';
  if (subtype === 'tombstone') {
    return ['tombstone', 'the parent was deleted and Slack left a tombstone; a '
      + 'tombstone holds the position in the channel and cannot hold a reply'];
  }
  if (NOT_THREADABLE.has(subtype)) {
    return ['not-threadable', `the parent is a ${subtype} message, which is one of the `
      + 'types that cannot host a thread'];
  }
  if (parent.thread_ts && parent.thread_ts !== parent.ts) {
    return ['not-a-root', `this ts is a reply inside thread ${parent.thread_ts} rather `
      + 'than a thread root; Slack will accept the reply and move it, which is a '
      + 'different problem'];
  }
  if (subtype) {
    return ['unknown-subtype', `subtype "${subtype}" is not in this table; the parent `
      + 'looks usable and the subtype is reported rather than judged'];
  }
  return ['usable', 'the parent is present, is a root, and can take a reply'];
}

/**
 * How long the app has been threading under the same parent. Pure.
 * Age is the mechanism rather than a symptom: nothing about a parent changes
 * when it is created, and everything can change while it sits in a config file.
 */
export function staleRoot(threadTs, now = null, ttlDays = DEFAULT_TTL_DAYS) {
  const created = Number(String(threadTs ?? '').split('.')[0]);
  if (!Number.isFinite(created) || String(threadTs ?? '').trim() === '') {
    return ['unparseable', -1];
  }
  const at = Number(now ?? Date.now() / 1000);
  const exact = (at - created) / 86400;
  // Rounded for the report and compared unrounded, so a parent one second in
  // the future is not rounded into the present.
  const age = Math.round(exact * 100) / 100;
  if (exact < 0) return ['in-the-future', age];
  if (exact >= ttlDays * 2) return ['stale', age];
  if (exact >= ttlDays) return ['aging', age];
  return ['fresh', age];
}

/**
 * Sort a set of stored parents into what to do about each. Pure.
 * A parent that is gone needs a new parent, a locked one needs a person, and
 * an unreadable one needs a scope; one number sends somebody to the wrong fix.
 */
export function rollCall(results) {
  const order = ['gone', 'tombstone', 'not-threadable', 'locked', 'not-a-root',
    'unknown-error', 'unreadable', 'unknown-subtype', 'usable'];
  const buckets = new Map();
  for (const r of results ?? []) {
    const key = r.state ?? 'unknown-error';
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(r);
  }
  const size = (k) => (buckets.get(k) ?? []).length;
  const broken = size('gone') + size('tombstone') + size('not-threadable')
    + size('locked');
  let total = 0;
  for (const v of buckets.values()) total += v.length;
  return {
    total,
    broken,
    usable: size('usable'),
    ambiguous: size('unreadable'),
    order: order.filter((k) => buckets.has(k)),
    buckets,
  };
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

async function stored(args) {
  const out = [];
  const file = arg(args, '--parents');
  const fallbackChannel = arg(args, '--channel');
  if (file) {
    const body = JSON.parse(await readFile(file, 'utf8'));
    const entries = Array.isArray(body) ? body.entries() : Object.entries(body);
    for (const [label, value] of entries) {
      if (value && typeof value === 'object') {
        out.push([String(label), value.channel, value.thread_ts]);
      } else {
        out.push([String(label), fallbackChannel, String(value)]);
      }
    }
  }
  for (const pair of argAll(args, '--parent')) {
    const i = pair.indexOf(':');
    out.push([pair, i === -1 ? '' : pair.slice(0, i), i === -1 ? '' : pair.slice(i + 1)]);
  }
  return out.filter(([, c, t]) => c && t);
}

async function main() {
  const args = process.argv.slice(2);
  const parents = await stored(args);
  if (!parents.length) {
    console.error('pass --parent CHANNEL:THREAD_TS or --parents FILE');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history is enough)`);
    process.exitCode = 2;
    return;
  }
  const ttlDays = Number(arg(args, '--ttl-days', String(DEFAULT_TTL_DAYS)));
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const results = [];
  for (const [label, channel, threadTs] of parents) {
    const url = `${API}conversations.replies?channel=${encodeURIComponent(channel)}`
      + `&ts=${encodeURIComponent(threadTs)}&limit=1`;
    const body = await (await fetch(url, { headers })).json();
    const error = body.ok === true ? '' : (body.error ?? 'unknown');
    const messages = body.messages ?? [];
    const [state, detail] = parentState(error, messages[0] ?? null);
    const [ageState, age] = staleRoot(threadTs, null, ttlDays);
    results.push({ label, channel, ts: threadTs, state, detail, age, ageState });
    (['usable', 'unknown-subtype'].includes(state) ? console.log : console.warn)(
      `parent     ${state.padEnd(16)} ${label.padEnd(16)} ${detail}`);
    if (['aging', 'stale'].includes(ageState)) {
      console.warn(`age        ${ageState.padEnd(16)} ${label} has been the parent for `
        + `${age.toFixed(1)} day(s)`);
    }
  }

  const r = rollCall(results);
  console.log(`roll call  ${r.total} parent(s): ${r.usable} usable, ${r.broken} broken, `
    + `${r.ambiguous} unreadable`);
  if (r.broken) {
    console.warn('  repair: read the parent with conversations.replies before you '
      + 'thread under it, and post at the top level when the read fails');
    console.warn('  repair: store the parent ts with a lifetime and establish a new '
      + 'parent when the old one expires, rather than keeping one forever');
    console.warn('  repair: a locked thread needs a person rather than a retry; the '
      + 'lock is an administrator decision and your app cannot lift it');
    process.exitCode = 1;
    return;
  }
  if (r.ambiguous) {
    console.warn(`  note: ${r.ambiguous} parent(s) could not be read at all, which is a `
      + 'scope or membership answer rather than a thread answer');
  }
  console.log('verdict    clear          every stored parent can still take a reply');
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions are mostly about what the script refuses to call a fault. An unrecognised subtype and an unrecognised error both have to come back reported rather than failed, because this table will be out of date the moment Slack adds something. A channel that refuses the read has to leave the parent unknown rather than broken, since that error is about the token and not about the thread. And a stored ts that turns out to be a reply has to be handed to the neighbouring note by name, because absorbing it would mean reporting a silent reparenting as a refusal that never happened.",
"test_py_file": "test_slack_thread_parent.py",
"test_js_file": "slack-thread-parent.test.mjs",
"test_py": '''from slack_thread_parent import parent_state, roll_call, stale_root

NOW = 1700000000.0
ROOT = {"ts": "1699999000.000100", "text": "deploy started"}


def test_a_present_root_can_take_a_reply():
    state, detail = parent_state("", ROOT)
    assert state == "usable"
    assert "can take a reply" in detail
    assert parent_state("", {"ts": "1.0", "thread_ts": "1.0"})[0] == "usable"


def test_a_parent_that_is_gone_is_reported_as_the_error_a_reply_would_get():
    for error in ("thread_not_found", "message_not_found"):
        state, detail = parent_state(error)
        assert state == "gone"
        assert "cannot_reply_to_message" in detail
        assert error in detail


def test_an_empty_reply_list_is_the_same_finding_as_a_missing_parent():
    state, detail = parent_state("", None)
    assert state == "gone"
    assert "no parent message in it" in detail
    assert parent_state("", {})[0] == "gone"


def test_a_deleted_parent_leaves_a_tombstone_that_cannot_hold_a_reply():
    state, detail = parent_state("", {"ts": "1.0", "subtype": "tombstone"})
    assert state == "tombstone"
    assert "deleted" in detail
    assert "cannot hold a reply" in detail


def test_a_join_message_is_one_of_the_types_that_cannot_host_a_thread():
    state, detail = parent_state("", {"ts": "1.0", "subtype": "channel_join"})
    assert state == "not-threadable"
    assert "channel_join" in detail
    assert parent_state("", {"ts": "1.0", "subtype": "group_leave"})[0] == "not-threadable"


def test_a_locked_thread_is_a_person_problem_rather_than_a_parent_problem():
    state, detail = parent_state("restricted_action_thread_locked")
    assert state == "locked"
    assert "administrator" in detail


def test_a_channel_that_refuses_the_read_leaves_the_parent_unknown():
    for error in ("channel_not_found", "not_in_channel", "missing_scope"):
        state, detail = parent_state(error)
        assert state == "unreadable"
        assert "unknown rather than bad" in detail


def test_a_reply_used_as_a_root_is_handed_to_the_note_next_door():
    state, detail = parent_state("", {"ts": "1699999500.0001",
                                      "thread_ts": "1699999000.0001"})
    assert state == "not-a-root"
    assert "1699999000.0001" in detail
    assert "different problem" in detail


def test_an_unrecognised_subtype_is_reported_and_not_failed():
    state, detail = parent_state("", {"ts": "1.0", "subtype": "some_new_subtype"})
    assert state == "unknown-subtype"
    assert "reported rather than judged" in detail


def test_an_unrecognised_error_is_reported_and_not_failed():
    state, detail = parent_state("something_new")
    assert state == "unknown-error"
    assert "does not have a rule for" in detail


def test_a_parent_stored_a_few_hours_ago_is_fresh():
    state, age = stale_root("1699999000.000100", NOW)
    assert state == "fresh"
    assert 0 <= age < 1


def test_a_parent_a_week_old_is_aging_and_a_fortnight_old_is_stale():
    assert stale_root("1699000000.000100", NOW)[0] == "aging"
    assert stale_root("1698000000.000100", NOW)[0] == "stale"
    assert stale_root("1699000000.000100", NOW, ttl_days=30)[0] == "fresh"


def test_a_ts_that_is_not_a_ts_is_unparseable_rather_than_old():
    assert stale_root("not-a-ts", NOW) == ("unparseable", -1.0)
    assert stale_root(None, NOW)[0] == "unparseable"
    assert stale_root("1700000001.0", NOW)[0] == "in-the-future"


def test_the_roll_call_separates_broken_from_merely_unreadable():
    r = roll_call([
        {"state": "usable"}, {"state": "usable"},
        {"state": "gone"}, {"state": "tombstone"}, {"state": "locked"},
        {"state": "unreadable"}, {"state": "not-a-root"},
    ])
    assert r["total"] == 7
    assert r["usable"] == 2
    assert r["broken"] == 3
    assert r["ambiguous"] == 1
    assert r["order"][0] == "gone"
    assert "usable" in r["order"]


def test_a_roll_call_over_healthy_parents_reports_nothing_broken():
    r = roll_call([{"state": "usable"}, {"state": "unknown-subtype"}])
    assert r["broken"] == 0
    assert r["ambiguous"] == 0
    assert r["total"] == 2


def test_an_empty_roll_call_is_not_a_finding():
    r = roll_call([])
    assert r == {"total": 0, "broken": 0, "usable": 0, "ambiguous": 0,
                 "order": [], "buckets": {}}
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parentState, rollCall, staleRoot } from './slack-thread-parent.mjs';

const NOW = 1700000000;
const ROOT = { ts: '1699999000.000100', text: 'deploy started' };

test('a present root can take a reply', () => {
  const [state, detail] = parentState('', ROOT);
  assert.equal(state, 'usable');
  assert.match(detail, /can take a reply/);
  assert.equal(parentState('', { ts: '1.0', thread_ts: '1.0' })[0], 'usable');
});

test('a parent that is gone is reported as the error a reply would get', () => {
  for (const error of ['thread_not_found', 'message_not_found']) {
    const [state, detail] = parentState(error);
    assert.equal(state, 'gone');
    assert.match(detail, /cannot_reply_to_message/);
    assert.ok(detail.includes(error));
  }
});

test('an empty reply list is the same finding as a missing parent', () => {
  const [state, detail] = parentState('', null);
  assert.equal(state, 'gone');
  assert.match(detail, /no parent message in it/);
  assert.equal(parentState('', {})[0], 'gone');
});

test('a deleted parent leaves a tombstone that cannot hold a reply', () => {
  const [state, detail] = parentState('', { ts: '1.0', subtype: 'tombstone' });
  assert.equal(state, 'tombstone');
  assert.match(detail, /deleted/);
  assert.match(detail, /cannot hold a reply/);
});

test('a join message is one of the types that cannot host a thread', () => {
  const [state, detail] = parentState('', { ts: '1.0', subtype: 'channel_join' });
  assert.equal(state, 'not-threadable');
  assert.match(detail, /channel_join/);
  assert.equal(parentState('', { ts: '1.0', subtype: 'group_leave' })[0],
    'not-threadable');
});

test('a locked thread is a person problem rather than a parent problem', () => {
  const [state, detail] = parentState('restricted_action_thread_locked');
  assert.equal(state, 'locked');
  assert.match(detail, /administrator/);
});

test('a channel that refuses the read leaves the parent unknown', () => {
  for (const error of ['channel_not_found', 'not_in_channel', 'missing_scope']) {
    const [state, detail] = parentState(error);
    assert.equal(state, 'unreadable');
    assert.match(detail, /unknown rather than bad/);
  }
});

test('a reply used as a root is handed to the note next door', () => {
  const [state, detail] = parentState('',
    { ts: '1699999500.0001', thread_ts: '1699999000.0001' });
  assert.equal(state, 'not-a-root');
  assert.match(detail, /1699999000\\.0001/);
  assert.match(detail, /different problem/);
});

test('an unrecognised subtype is reported and not failed', () => {
  const [state, detail] = parentState('', { ts: '1.0', subtype: 'some_new_subtype' });
  assert.equal(state, 'unknown-subtype');
  assert.match(detail, /reported rather than judged/);
});

test('an unrecognised error is reported and not failed', () => {
  const [state, detail] = parentState('something_new');
  assert.equal(state, 'unknown-error');
  assert.match(detail, /does not have a rule for/);
});

test('a parent stored a few hours ago is fresh', () => {
  const [state, age] = staleRoot('1699999000.000100', NOW);
  assert.equal(state, 'fresh');
  assert.ok(age >= 0 && age < 1);
});

test('a parent a week old is aging and a fortnight old is stale', () => {
  assert.equal(staleRoot('1699000000.000100', NOW)[0], 'aging');
  assert.equal(staleRoot('1698000000.000100', NOW)[0], 'stale');
  assert.equal(staleRoot('1699000000.000100', NOW, 30)[0], 'fresh');
});

test('a ts that is not a ts is unparseable rather than old', () => {
  assert.deepEqual(staleRoot('not-a-ts', NOW), ['unparseable', -1]);
  assert.equal(staleRoot(null, NOW)[0], 'unparseable');
  assert.equal(staleRoot('1700000001.0', NOW)[0], 'in-the-future');
});

test('the roll call separates broken from merely unreadable', () => {
  const r = rollCall([
    { state: 'usable' }, { state: 'usable' },
    { state: 'gone' }, { state: 'tombstone' }, { state: 'locked' },
    { state: 'unreadable' }, { state: 'not-a-root' },
  ]);
  assert.equal(r.total, 7);
  assert.equal(r.usable, 2);
  assert.equal(r.broken, 3);
  assert.equal(r.ambiguous, 1);
  assert.equal(r.order[0], 'gone');
  assert.ok(r.order.includes('usable'));
});

test('a roll call over healthy parents reports nothing broken', () => {
  const r = rollCall([{ state: 'usable' }, { state: 'unknown-subtype' }]);
  assert.equal(r.broken, 0);
  assert.equal(r.ambiguous, 0);
  assert.equal(r.total, 2);
});

test('an empty roll call is not a finding', () => {
  const r = rollCall([]);
  assert.equal(r.total, 0);
  assert.equal(r.broken, 0);
  assert.deepEqual(r.order, []);
  assert.equal(r.buckets.size, 0);
});
''',
"faq": [
 ("What is the difference between this and a channel that refuses threads?",
  "This note is about one message: the specific parent you stored has been deleted, locked, or was never a type that could host a thread. A channel that forbids top-level posts, or forbids threading entirely, is a policy that applies to every message in it and is refused with a different error. The repairs differ too: here you establish a new parent, there you change which posting mode you use for that channel."),
 ("Why does the parent still appear in the channel if it was deleted?",
  "Slack leaves a tombstone. The message keeps its position in the conversation and its content is replaced, so a reader sees that something was deleted and an integration sees a ts that still resolves. That is why the read is worth doing: the tombstone is the difference between a parent that is gone and one that looks present and refuses every reply."),
 ("Can my app unlock a locked thread and carry on?",
  "No. Locking is an administrator action and lifting it is an administrator action. The correct behaviour for an integration is to stop trying, report that the thread is locked, and post at the top level or under a new parent instead. The script keeps locked threads out of the same bucket as deleted parents precisely because the next step is a person rather than a retry."),
 ("How long should I hold on to a thread_ts?",
  "As long as the thing it represents is live, and no longer. A ts stored with an incident should expire with the incident; a ts stored for a daily thread should be replaced daily. The script reports the age of every stored parent because nothing about a parent changes when it is created and everything can change while it sits in a config file for six weeks."),
 ("The read came back missing_scope. Is my parent broken?",
  "Unknown, which is a genuinely different answer. missing_scope, not_in_channel and channel_not_found are the channel refusing the read, and a bot without groups:read cannot even distinguish a private channel that does not exist from one it is not allowed to see. The script reports these as unreadable rather than as faults, so the report does not blame a parent it never managed to look at."),
],
"related": [
 ("/slack/thread-ts-is-a-reply/", "a parent that works, and still puts the reply somewhere else"),
 ("/slack/thread-only-or-non-threadable/", "the channel's threading rules rather than this one parent's state"),
 ("/slack/archived-channel-target/", "the other stored identifier that stops working while you hold it"),
],
"citations": [CITE_CONV_REPLIES, CITE_POSTMESSAGE, CITE_RETRIEVING, CITE_WEB_API],
})

GUIDES.append({
"slug": "thread-ts-is-a-reply",
"title": "A reply ts used as thread_ts, so the thread flattens",
"description": "Slack does not refuse a reply's ts as a parent. It reparents your reply to the original root, answers ok, and the conversation quietly stops making sense.",
"h1": "A reply ts used as thread_ts, so the thread flattens",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": [
    "slack thread_ts vs ts",
    "slack thread replies flatten",
    "slack reply appears in wrong thread",
    "slack event thread_ts or ts",
    "slack thread_broadcast subtype",
],
"deps": "Python 3.9+ with requests, or Node.js 18+; channels:history on the channel holding the threads",
"lead": "The support bot replies to whoever mentioned it, in the thread where they mentioned it. Mostly it works. Sometimes an answer appears next to the question instead of under it, and the person who asked follows up under the answer, and the thread turns into two conversations interleaved.</p><p>Every call returned <code>ok: true</code>. There is no error to search for, nothing in the logs, and no failed request. The bug is that a <code>ts</code> captured from a reply was stored as a parent, and Slack accepted it by quietly moving the reply somewhere else.",
"short_answer": """<p>Slack threads are one level deep. If you pass the <code>ts</code> of a <strong>reply</strong> as <code>thread_ts</code>, Slack does not refuse it - it reparents your message to that reply's own root and returns <code>ok</code>. Your reply lands beside the message you were answering rather than under it, and nothing anywhere reports that a substitution happened.</p>
<p>The distinguishing field is already on every message you read. A thread root has no <code>thread_ts</code>, or a <code>thread_ts</code> equal to its own <code>ts</code>. A reply carries both and they differ. One comparison settles it.</p>
<p>The usual source is capturing <code>response.ts</code> from a send that was itself a reply, or capturing <code>event.ts</code> from a message event without checking whether that event was already inside a thread. The one-line repair is <code>event.thread_ts || event.ts</code>, which yields the root in both cases, and the script tests exactly that.</p>""",
"problem": """<p>What makes this expensive is that it is not a failure. There is no error code to search for, no non-2xx status, no log line, and no metric that moves. The API call succeeded, the message was delivered, and it is in the channel. Everything your monitoring can see says the feature works.</p>
<p>What people see instead is a conversation that has stopped making sense. An answer sits next to the question rather than under it. Somebody replies to the answer and their reply jumps to the top of the thread. A long incident thread grows a second, parallel thread beside it. Each of those reads as a Slack quirk rather than as a bug in an integration, so it gets mentioned and never filed.</p>
<p><code>reply_broadcast</code> makes it much more likely. A broadcast reply is pushed into the channel as well as the thread, so it looks exactly like a top-level message to anybody scrolling - and to any code that captures a <code>ts</code> from a message event. The next capture takes a reply's <code>ts</code>, stores it as a parent, and the flattening becomes permanent for as long as that value is stored.</p>
<p>And it survives review because the code is not obviously wrong. <code>store(response["ts"])</code> is correct when you posted the root and wrong when you posted a reply, and the two lines look identical. The variable is called <code>thread_ts</code> in both cases. Nothing at the call site distinguishes them.</p>""",
"why": """<p><strong>Silence is the whole problem, so the detector cannot look for an error.</strong> There is no <code>ok: false</code> to catch and no status code to check. The finding has to be computed from the message itself, which is why the central function classifies a <code>ts</code> rather than an outcome.</p>
<p><strong>Slack already gives you the answer for free.</strong> <code>conversations.replies</code> given a reply's <code>ts</code> returns the whole thread rooted at the real root, so the first message that comes back is where your reply would actually have landed. The detection is a read of the thread you were about to reply into.</p>
<p><strong>A broadcast is still a reply, however it looks in the channel.</strong> <code>subtype: "thread_broadcast"</code> is the single most likely thing to be captured as a parent by mistake, because it appears at the top level. The script names broadcasts separately rather than folding them into replies, since the reason they get captured is different.</p>
<p><strong>The repair is one line, and the one line is worth testing.</strong> <code>event.thread_ts || event.ts</code> yields the root for a top-level message and for a reply. That is a pure function over an event, so it has a test, and the test asserts the property that matters: the value it returns never needs to be reparented.</p>
<p><strong>A stored ts that is not in the thread is a different note.</strong> If the target cannot be found at all, that is a missing parent rather than a flattened one, and the script hands it over by name instead of guessing.</p>
<p><strong>Nothing is sent, and here that is not just a policy.</strong> Reproducing this by posting is uniquely useless: the send succeeds either way, so the only evidence is which thread the message turned up in, which means the experiment leaves a message in the wrong thread of a real conversation as its result.</p>""",
"steps": [
 {"h": "List every ts your app stores as a parent",
  "body": """<p>Config values, database columns, cached incident roots. Pass them as <code>--parent LABEL:THREAD_TS</code> with the channel they live in. The interesting ones are the values captured at runtime rather than the ones typed in by hand.</p>"""},
 {"h": "Let Slack tell you where the thread really starts",
  "body": """<p><code>conversations.replies</code> given any ts in a thread returns the whole thread, rooted at the real root. The first message that comes back is where a reply under your stored ts would actually land, which is the answer without a single message being sent.</p>"""},
 {"h": "Compare thread_ts against ts, and nothing else",
  "body": """<p><code>ts_role</code> is one comparison. No <code>thread_ts</code>, or <code>thread_ts</code> equal to <code>ts</code>, is a root. Both present and different is a reply. That field has been on every message you have ever read back.</p>"""},
 {"h": "Count broadcasts separately from ordinary replies",
  "body": """<p>A <code>thread_broadcast</code> reply appears in the channel and reads as top level, which is why it is the one most often captured as a parent. Same fault, different cause, so the report names it separately.</p>"""},
 {"h": "Compute where the reply would have gone",
  "body": """<p><code>resolve_root</code> returns the root Slack would substitute, and whether a substitution happens at all. That value is the finding: not "this is wrong" but "this reply lands under 1735689600.000100 instead".</p>"""},
 {"h": "Replace the capture, not the call sites",
  "body": """<p><code>capture_rule</code> is the repair as a function: <code>event.thread_ts or event.ts</code>. Put it where the ts is captured rather than fixing the places it is used, because the next call site will be written by somebody who has not read this note.</p>"""},
],
"verify": """<p>Change the capture, re-run the audit against the same stored values, and the verdict should move from <code>flattening</code> to <code>rooted</code> without anything being posted.</p>
<pre><code class="language-bash">python3 slack_thread_root.py --channel C01ABCDE9 --parent incident:1735689612.000400
# identity   U0APPBOT11 in acme
# thread     incident         root is 1735689600.000100 with 14 message(s) returned
# stored     incident         reply      the target is reply, so Slack silently reparents
#                             the reply to 1735689600.000100 and answers ok; the reply
#                             lands beside the message you were replying to
# verdict    flattening     1 of 1 stored parents are replies
#   repair: store the root. From an event, that is event.thread_ts or event.ts, which is
#           the root in both cases</code></pre>""",
"code_intro": "Four pure functions and one read per thread. <code>ts_role</code> is the comparison the whole note reduces to. <code>resolve_root</code> computes the silent outcome: where Slack will actually put the reply, and whether it moved it, which is the sentence that makes this a bug rather than a quirk. <code>capture_rule</code> is the repair written as a function so it can be tested rather than described. <code>audit_stored</code> holds a map of stored parents against the messages Slack returned and names which of them has been flattening a thread all along.",
"py_file": "slack_thread_root.py",
"py": '''"""Find out whether the ts you thread under is a root or a reply.

Read only, and read only is enough because Slack answers the question directly:
conversations.replies given the ts of a reply returns the whole thread, rooted
at the real root, so the first message that comes back is where your reply would
actually have landed. Nothing is posted from here. Reproducing this by sending
is unusually pointless anyway, since the send succeeds either way and the only
evidence is which thread it turned up in.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_thread_root")

API = "https://slack.com/api/"

# A reply that was also pushed into the channel. It is still a reply, and it is
# the one that most often gets captured as a parent, because it looks like a
# top level message in the channel where somebody found it.
BROADCAST = "thread_broadcast"


def ts_role(message):
    """Say whether one message is a thread root or a reply inside one. Pure.

    The distinguishing field is on the message itself and costs nothing to
    check: a root has no thread_ts, or a thread_ts equal to its own ts; a reply
    carries both, and they differ.
    """
    if not isinstance(message, dict) or not message.get("ts"):
        return ("unknown", "no message, so nothing can be said about the ts")
    ts = message.get("ts")
    thread_ts = message.get("thread_ts")
    if message.get("subtype") == BROADCAST:
        return ("broadcast", "a reply sent with reply_broadcast, so it appears in the "
                             "channel and is still a reply inside %s" % thread_ts)
    if not thread_ts or thread_ts == ts:
        if message.get("reply_count"):
            return ("root", "a thread root with %d repl(ies) already under it"
                    % message["reply_count"])
        return ("root", "a top level message and a valid thread root")
    return ("reply", "a reply inside thread %s; its own ts is %s and the two differ"
            % (thread_ts, ts))


def resolve_root(target):
    """Where a reply threaded under this ts would actually land. Pure.

    Slack does not refuse a reply's ts as a thread_ts. It reparents the reply
    to that reply's own root and returns ok, which is why this is the one
    threading fault with no error string attached to it.
    """
    role, detail = ts_role(target)
    if role == "unknown":
        return (None, False, "the target is not in this thread, which is a missing "
                             "parent rather than a flattened one")
    if role == "root":
        return (target.get("ts"), False, "the target is the root, so the reply lands "
                                         "where you meant it to")
    root = target.get("thread_ts")
    return (root, True, "the target is %s, so Slack silently reparents the reply to "
                        "%s and answers ok; the reply lands beside the message you "
                        "were replying to rather than under it" % (role, root))


def capture_rule(event):
    """The one line that captures a root from any message event. Pure.

    thread_ts or ts, in that order, which yields the root whether the event was
    a top level message or a reply. Storing response ts from a send is the
    mistake this replaces, because that ts is a root only when you posted the
    root.
    """
    if not isinstance(event, dict):
        return (None, "none")
    thread_ts = event.get("thread_ts")
    if thread_ts:
        return (thread_ts, "thread_ts")
    ts = event.get("ts")
    if ts:
        return (ts, "ts")
    return (None, "none")


def audit_stored(stored, index):
    """Check a map of stored parents against the messages Slack returned. Pure.

    stored: {label: ts}. index: {ts: message}, built from conversations.replies.
    A stored ts that resolves to a different root is a thread the app has been
    flattening, silently, for as long as that ts has been stored.
    """
    rows = []
    flattened = 0
    for label in sorted(stored or {}):
        ts = stored[label]
        target = (index or {}).get(ts)
        role, detail = ts_role(target)
        root, moved, why = resolve_root(target)
        if moved:
            flattened += 1
        rows.append({"label": label, "ts": ts, "role": role, "detail": detail,
                     "actual_root": root, "moved": moved, "why": why})
    return {
        "checked": len(rows),
        "flattened": flattened,
        "rows": rows,
        "verdict": "flattening" if flattened else "rooted",
    }


def _stored(args):
    out = {}
    if args.parents:
        body = json.loads(open(args.parents, encoding="utf-8").read())
        if isinstance(body, dict):
            for label, value in body.items():
                out[str(label)] = (value.get("thread_ts") if isinstance(value, dict)
                                   else str(value))
        else:
            for i, value in enumerate(body):
                out[str(i)] = str(value)
    for pair in args.parent:
        _, _, ts = pair.partition(":")
        out[pair] = ts
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", required=True,
                    help="the channel the stored parents live in")
    ap.add_argument("--parent", action="append", default=[],
                    help="a stored parent as LABEL:THREAD_TS; repeatable")
    ap.add_argument("--parents", help="JSON file of stored parents")
    ap.add_argument("--limit", type=int, default=200,
                    help="replies read per thread")
    args = ap.parse_args()

    stored = _stored(args)
    if not stored:
        log.error("pass --parent LABEL:THREAD_TS or --parents FILE")
        return 2
    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history is enough)", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    index, broadcasts = {}, 0
    for label in sorted(stored):
        ts = stored[label]
        body = s.get(API + "conversations.replies", timeout=30,
                     params={"channel": args.channel, "ts": ts,
                             "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("replies    unavailable    %s (%s): %s", label, ts,
                        body.get("error"))
            continue
        messages = body.get("messages") or []
        if messages:
            log.info("thread     %-16s root is %s with %d message(s) returned",
                     label, messages[0].get("ts"), len(messages))
        for m in messages:
            index[m.get("ts")] = m
            if m.get("subtype") == BROADCAST:
                broadcasts += 1

    a = audit_stored(stored, index)
    for row in a["rows"]:
        (log.warning if row["moved"] else log.info)(
            "stored     %-16s %-10s %s", row["label"], row["role"], row["why"])
    (log.warning if a["flattened"] else log.info)(
        "verdict    %-14s %d of %d stored parents are replies",
        a["verdict"], a["flattened"], a["checked"])
    if broadcasts:
        log.warning("broadcast  %d repl(ies) in these threads carry %s; each one was "
                    "pushed into the channel and is a candidate for being captured as "
                    "a parent by mistake", broadcasts, BROADCAST)

    if a["flattened"]:
        log.warning("  repair: store the root. From an event, that is "
                    "event.thread_ts or event.ts, which is the root in both cases")
        log.warning("  repair: from a send, keep the response ts only when you posted "
                    "the root; a reply's ts is not a parent")
        log.warning("  repair: set reply_broadcast deliberately and rarely. It puts the "
                    "reply in the channel, where the next person captures it as a root")
        return 1
    log.info("verdict    clear          every stored parent is a root")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-thread-root.mjs",
"js": '''/**
 * Find out whether the ts you thread under is a root or a reply.
 *
 * Read only, and read only is enough because Slack answers the question
 * directly: conversations.replies given the ts of a reply returns the whole
 * thread, rooted at the real root, so the first message that comes back is
 * where your reply would actually have landed. Nothing is posted from here.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// A reply that was also pushed into the channel. It is still a reply, and it
// is the one that most often gets captured as a parent, because it looks like
// a top level message in the channel where somebody found it.
const BROADCAST = 'thread_broadcast';

/**
 * Say whether one message is a thread root or a reply inside one. Pure.
 * A root has no thread_ts, or one equal to its own ts; a reply carries both,
 * and they differ.
 */
export function tsRole(message) {
  if (!message || typeof message !== 'object' || !message.ts) {
    return ['unknown', 'no message, so nothing can be said about the ts'];
  }
  const { ts } = message;
  const threadTs = message.thread_ts;
  if (message.subtype === BROADCAST) {
    return ['broadcast', 'a reply sent with reply_broadcast, so it appears in the '
      + `channel and is still a reply inside ${threadTs}`];
  }
  if (!threadTs || threadTs === ts) {
    if (message.reply_count) {
      return ['root', `a thread root with ${message.reply_count} repl(ies) already `
        + 'under it'];
    }
    return ['root', 'a top level message and a valid thread root'];
  }
  return ['reply', `a reply inside thread ${threadTs}; its own ts is ${ts} and the `
    + 'two differ'];
}

/**
 * Where a reply threaded under this ts would actually land. Pure.
 * Slack does not refuse a reply's ts as a thread_ts. It reparents the reply to
 * that reply's own root and returns ok, which is why this is the one threading
 * fault with no error string attached to it.
 */
export function resolveRoot(target) {
  const [role] = tsRole(target);
  if (role === 'unknown') {
    return [null, false, 'the target is not in this thread, which is a missing parent '
      + 'rather than a flattened one'];
  }
  if (role === 'root') {
    return [target.ts, false,
      'the target is the root, so the reply lands where you meant it to'];
  }
  const root = target.thread_ts;
  return [root, true, `the target is ${role}, so Slack silently reparents the reply `
    + `to ${root} and answers ok; the reply lands beside the message you were `
    + 'replying to rather than under it'];
}

/**
 * The one line that captures a root from any message event. Pure.
 * thread_ts or ts, in that order, which yields the root whether the event was
 * a top level message or a reply.
 */
export function captureRule(event) {
  if (!event || typeof event !== 'object') return [null, 'none'];
  if (event.thread_ts) return [event.thread_ts, 'thread_ts'];
  if (event.ts) return [event.ts, 'ts'];
  return [null, 'none'];
}

/**
 * Check a map of stored parents against the messages Slack returned. Pure.
 * stored: {label: ts}. index: {ts: message}. A stored ts that resolves to a
 * different root is a thread the app has been flattening, silently, for as
 * long as that ts has been stored.
 */
export function auditStored(stored, index) {
  const rows = [];
  let flattened = 0;
  for (const label of Object.keys(stored ?? {}).sort()) {
    const ts = stored[label];
    const target = (index ?? {})[ts];
    const [role, detail] = tsRole(target);
    const [root, moved, why] = resolveRoot(target);
    if (moved) flattened += 1;
    rows.push({ label, ts, role, detail, actualRoot: root, moved, why });
  }
  return {
    checked: rows.length,
    flattened,
    rows,
    verdict: flattened ? 'flattening' : 'rooted',
  };
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

async function storedParents(args) {
  const out = {};
  const file = arg(args, '--parents');
  if (file) {
    const body = JSON.parse(await readFile(file, 'utf8'));
    if (Array.isArray(body)) {
      body.forEach((value, i) => { out[String(i)] = String(value); });
    } else {
      for (const [label, value] of Object.entries(body)) {
        out[label] = (value && typeof value === 'object') ? value.thread_ts : String(value);
      }
    }
  }
  for (const pair of argAll(args, '--parent')) {
    const i = pair.indexOf(':');
    out[pair] = i === -1 ? '' : pair.slice(i + 1);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const channel = arg(args, '--channel');
  if (!channel) {
    console.error('pass --channel with the channel the stored parents live in');
    process.exitCode = 2;
    return;
  }
  const stored = await storedParents(args);
  if (!Object.keys(stored).length) {
    console.error('pass --parent LABEL:THREAD_TS or --parents FILE');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history is enough)`);
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const index = {};
  let broadcasts = 0;
  for (const label of Object.keys(stored).sort()) {
    const ts = stored[label];
    const url = `${API}conversations.replies?channel=${encodeURIComponent(channel)}`
      + `&ts=${encodeURIComponent(ts)}&limit=${encodeURIComponent(limit)}`;
    const body = await (await fetch(url, { headers })).json();
    if (body.ok !== true) {
      console.warn(`replies    unavailable    ${label} (${ts}): ${body.error}`);
      continue;
    }
    const messages = body.messages ?? [];
    if (messages.length) {
      console.log(`thread     ${label.padEnd(16)} root is ${messages[0].ts} with `
        + `${messages.length} message(s) returned`);
    }
    for (const m of messages) {
      index[m.ts] = m;
      if (m.subtype === BROADCAST) broadcasts += 1;
    }
  }

  const a = auditStored(stored, index);
  for (const row of a.rows) {
    (row.moved ? console.warn : console.log)(
      `stored     ${row.label.padEnd(16)} ${row.role.padEnd(10)} ${row.why}`);
  }
  (a.flattened ? console.warn : console.log)(
    `verdict    ${a.verdict.padEnd(14)} ${a.flattened} of ${a.checked} stored parents `
    + 'are replies');
  if (broadcasts) {
    console.warn(`broadcast  ${broadcasts} repl(ies) in these threads carry ${BROADCAST}; `
      + 'each one was pushed into the channel and is a candidate for being captured as '
      + 'a parent by mistake');
  }

  if (a.flattened) {
    console.warn('  repair: store the root. From an event, that is event.thread_ts or '
      + 'event.ts, which is the root in both cases');
    console.warn('  repair: from a send, keep the response ts only when you posted the '
      + "root; a reply's ts is not a parent");
    console.warn('  repair: set reply_broadcast deliberately and rarely. It puts the '
      + 'reply in the channel, where the next person captures it as a root');
    process.exitCode = 1;
    return;
  }
  console.log('verdict    clear          every stored parent is a root');
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that carries the note asserts that the capture rule's output never needs reparenting: take a reply event, apply <code>event.thread_ts or event.ts</code>, look the result up, and <code>resolve_root</code> must report no move. That is the repair proved as a property rather than restated as advice. The others hold the classifier honest in both directions: a broadcast has to come back as its own role rather than as a root, because looking top level is exactly how it gets captured, and a ts that is not in the thread at all has to be handed to the neighbouring note rather than counted as flattened.",
"test_py_file": "test_slack_thread_root.py",
"test_js_file": "slack-thread-root.test.mjs",
"test_py": '''from slack_thread_root import audit_stored, capture_rule, resolve_root, ts_role

ROOT = {"ts": "1700000000.0001", "text": "deploy started", "reply_count": 3}
REPLY = {"ts": "1700000100.0002", "thread_ts": "1700000000.0001", "text": "step 2"}
BCAST = {"ts": "1700000200.0003", "thread_ts": "1700000000.0001",
         "subtype": "thread_broadcast", "text": "still failing"}
INDEX = {m["ts"]: m for m in (ROOT, REPLY, BCAST)}


def test_a_root_is_a_message_whose_thread_ts_is_missing_or_its_own_ts():
    role, detail = ts_role(ROOT)
    assert role == "root"
    assert "3 repl(ies)" in detail
    assert ts_role({"ts": "1.0"})[0] == "root"
    assert ts_role({"ts": "1.0", "thread_ts": "1.0"})[0] == "root"


def test_a_reply_carries_both_fields_and_they_differ():
    role, detail = ts_role(REPLY)
    assert role == "reply"
    assert "1700000000.0001" in detail
    assert "the two differ" in detail


def test_a_broadcast_is_still_a_reply_however_it_looks_in_the_channel():
    role, detail = ts_role(BCAST)
    assert role == "broadcast"
    assert "still a reply" in detail


def test_a_missing_message_says_nothing_rather_than_guessing():
    assert ts_role(None)[0] == "unknown"
    assert ts_role({})[0] == "unknown"
    assert ts_role("1700000000.0001")[0] == "unknown"


def test_threading_under_a_root_lands_where_you_meant_it_to():
    root, moved, why = resolve_root(ROOT)
    assert root == "1700000000.0001"
    assert moved is False
    assert "where you meant it to" in why


def test_threading_under_a_reply_is_moved_and_nothing_is_returned_to_say_so():
    root, moved, why = resolve_root(REPLY)
    assert root == "1700000000.0001"
    assert moved is True
    assert "silently reparents" in why
    assert "answers ok" in why


def test_a_broadcast_reply_used_as_a_parent_is_moved_the_same_way():
    root, moved, why = resolve_root(BCAST)
    assert root == "1700000000.0001"
    assert moved is True
    assert "broadcast" in why


def test_a_target_that_is_not_in_the_thread_is_a_different_note():
    root, moved, why = resolve_root(None)
    assert root is None
    assert moved is False
    assert "missing parent" in why


def test_the_capture_rule_yields_the_root_for_a_reply_and_for_a_top_level_message():
    assert capture_rule(REPLY) == ("1700000000.0001", "thread_ts")
    assert capture_rule(ROOT) == ("1700000000.0001", "ts")
    assert capture_rule(BCAST)[0] == "1700000000.0001"


def test_the_capture_rule_holds_for_the_thing_it_was_written_to_prevent():
    stored, _source = capture_rule(REPLY)
    assert resolve_root(INDEX[stored])[1] is False


def test_the_capture_rule_refuses_to_invent_a_ts():
    assert capture_rule({}) == (None, "none")
    assert capture_rule(None) == (None, "none")


def test_the_audit_names_which_stored_parent_is_flattening_a_thread():
    a = audit_stored({"digest": ROOT["ts"], "incident": REPLY["ts"]}, INDEX)
    assert a["checked"] == 2
    assert a["flattened"] == 1
    assert a["verdict"] == "flattening"
    rows = {r["label"]: r for r in a["rows"]}
    assert rows["incident"]["moved"] is True
    assert rows["incident"]["actual_root"] == ROOT["ts"]
    assert rows["digest"]["moved"] is False


def test_the_audit_reports_rooted_when_every_stored_parent_is_a_root():
    a = audit_stored({"digest": ROOT["ts"]}, INDEX)
    assert a["flattened"] == 0
    assert a["verdict"] == "rooted"


def test_a_stored_ts_that_is_not_in_the_index_is_not_counted_as_flattened():
    a = audit_stored({"gone": "1699000000.0009"}, INDEX)
    assert a["flattened"] == 0
    assert a["rows"][0]["role"] == "unknown"
    assert a["rows"][0]["actual_root"] is None


def test_an_empty_audit_is_not_a_finding():
    a = audit_stored({}, INDEX)
    assert a["checked"] == 0
    assert a["verdict"] == "rooted"
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  auditStored, captureRule, resolveRoot, tsRole,
} from './slack-thread-root.mjs';

const ROOT = { ts: '1700000000.0001', text: 'deploy started', reply_count: 3 };
const REPLY = { ts: '1700000100.0002', thread_ts: '1700000000.0001', text: 'step 2' };
const BCAST = {
  ts: '1700000200.0003',
  thread_ts: '1700000000.0001',
  subtype: 'thread_broadcast',
  text: 'still failing',
};
const INDEX = Object.fromEntries([ROOT, REPLY, BCAST].map((m) => [m.ts, m]));

test('a root is a message whose thread_ts is missing or its own ts', () => {
  const [role, detail] = tsRole(ROOT);
  assert.equal(role, 'root');
  assert.match(detail, /3 repl\\(ies\\)/);
  assert.equal(tsRole({ ts: '1.0' })[0], 'root');
  assert.equal(tsRole({ ts: '1.0', thread_ts: '1.0' })[0], 'root');
});

test('a reply carries both fields and they differ', () => {
  const [role, detail] = tsRole(REPLY);
  assert.equal(role, 'reply');
  assert.match(detail, /1700000000\\.0001/);
  assert.match(detail, /two differ/);
});

test('a broadcast is still a reply however it looks in the channel', () => {
  const [role, detail] = tsRole(BCAST);
  assert.equal(role, 'broadcast');
  assert.match(detail, /still a reply/);
});

test('a missing message says nothing rather than guessing', () => {
  assert.equal(tsRole(null)[0], 'unknown');
  assert.equal(tsRole({})[0], 'unknown');
  assert.equal(tsRole('1700000000.0001')[0], 'unknown');
});

test('threading under a root lands where you meant it to', () => {
  const [root, moved, why] = resolveRoot(ROOT);
  assert.equal(root, '1700000000.0001');
  assert.equal(moved, false);
  assert.match(why, /where you meant it to/);
});

test('threading under a reply is moved and nothing is returned to say so', () => {
  const [root, moved, why] = resolveRoot(REPLY);
  assert.equal(root, '1700000000.0001');
  assert.equal(moved, true);
  assert.match(why, /silently reparents/);
  assert.match(why, /answers ok/);
});

test('a broadcast reply used as a parent is moved the same way', () => {
  const [root, moved, why] = resolveRoot(BCAST);
  assert.equal(root, '1700000000.0001');
  assert.equal(moved, true);
  assert.match(why, /broadcast/);
});

test('a target that is not in the thread is a different note', () => {
  const [root, moved, why] = resolveRoot(null);
  assert.equal(root, null);
  assert.equal(moved, false);
  assert.match(why, /missing parent/);
});

test('the capture rule yields the root for a reply and for a top level message', () => {
  assert.deepEqual(captureRule(REPLY), ['1700000000.0001', 'thread_ts']);
  assert.deepEqual(captureRule(ROOT), ['1700000000.0001', 'ts']);
  assert.equal(captureRule(BCAST)[0], '1700000000.0001');
});

test('the capture rule holds for the thing it was written to prevent', () => {
  const [stored] = captureRule(REPLY);
  assert.equal(resolveRoot(INDEX[stored])[1], false);
});

test('the capture rule refuses to invent a ts', () => {
  assert.deepEqual(captureRule({}), [null, 'none']);
  assert.deepEqual(captureRule(null), [null, 'none']);
});

test('the audit names which stored parent is flattening a thread', () => {
  const a = auditStored({ digest: ROOT.ts, incident: REPLY.ts }, INDEX);
  assert.equal(a.checked, 2);
  assert.equal(a.flattened, 1);
  assert.equal(a.verdict, 'flattening');
  const rows = Object.fromEntries(a.rows.map((r) => [r.label, r]));
  assert.equal(rows.incident.moved, true);
  assert.equal(rows.incident.actualRoot, ROOT.ts);
  assert.equal(rows.digest.moved, false);
});

test('the audit reports rooted when every stored parent is a root', () => {
  const a = auditStored({ digest: ROOT.ts }, INDEX);
  assert.equal(a.flattened, 0);
  assert.equal(a.verdict, 'rooted');
});

test('a stored ts that is not in the index is not counted as flattened', () => {
  const a = auditStored({ gone: '1699000000.0009' }, INDEX);
  assert.equal(a.flattened, 0);
  assert.equal(a.rows[0].role, 'unknown');
  assert.equal(a.rows[0].actualRoot, null);
});

test('an empty audit is not a finding', () => {
  const a = auditStored({}, INDEX);
  assert.equal(a.checked, 0);
  assert.equal(a.verdict, 'rooted');
});
''',
"faq": [
 ("Why does Slack not just return an error for this?",
  "Because from the API's point of view nothing invalid happened. Threads are one level deep, so a reply's ts identifies a thread perfectly well - it just identifies the thread that reply is already in. Slack resolves it to that thread's root and posts your message there. It is a valid interpretation of an ambiguous input, which is exactly why it is silent and exactly why it is expensive."),
 ("How do I tell a root from a reply without another API call?",
  "The message you already have says so. A root has no thread_ts, or a thread_ts equal to its own ts. A reply carries both and they differ. If you are handling an event, the same rule gives you the repair directly: event.thread_ts or event.ts yields the root in both cases, and that single expression removes the whole class."),
 ("Is reply_broadcast the cause, or just related?",
  "Related, and it makes the mistake much more likely. A broadcast reply is pushed into the channel as well as into the thread, so it looks like a top-level message to a person scrolling and to code capturing a ts from a message event. The reply itself is fine; the risk is that its ts gets stored as a parent afterwards. Use it deliberately and rarely."),
 ("Can I nest a reply under another reply if I really want to?",
  "No. Slack threads are one level deep and there is no way to ask for a second level. If you need to express a reply-to-a-reply relationship, do it in the message text by quoting or linking to the message you are answering. Passing the reply's ts as thread_ts does not create nesting; it silently moves your message to the root."),
 ("My reply went to the right thread but appeared in the channel too. Same bug?",
  "Different one, and worth checking deliberately. That is reply_broadcast being set, which pushes the reply into the channel on purpose. It is a legitimate feature that surprises people when it is on by default in a wrapper, and the script counts broadcasts separately for that reason - both because they surprise readers and because they are the messages most likely to be captured as a parent next."),
],
"related": [
 ("/slack/cannot-reply-to-message/", "the same stored ts, on the day it stops taking replies at all"),
 ("/slack/thread-only-or-non-threadable/", "which posting mode the channel allows in the first place"),
 ("/slack/message-subtypes-ignored/", "the other note about a field on the message that decides everything"),
],
"citations": [CITE_RETRIEVING, CITE_CONV_REPLIES, CITE_POSTMESSAGE, CITE_WEB_API],
})
